# app.py (Mise à jour)
import streamlit as st
import os
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
import random
import gspread # Nécessaire ici pour gspread.utils.rowcol_to_a1 dans la gestion des styles


# Importe les modules que nous avons créés
import config
import sheets_connector
import gemini_oracle
import utils

# --- Initialisation de st.session_state pour les paramètres de redirection et la directive ---
if 'generated_narrative_params' not in st.session_state:
    st.session_state.generated_narrative_params = None
if 'redirect_to_page' not in st.session_state:
    st.session_state.redirect_to_page = None
if 'last_directive_text' not in st.session_state:
    st.session_state.last_directive_text = ""
if 'current_universe_id_for_edit' not in st.session_state:
    st.session_state.current_universe_id_for_edit = None
if 'extracted_plot_for_universe' not in st.session_state:
    st.session_state.extracted_plot_for_universe = ""
if 'extracted_characters_for_universe' not in st.session_state:
    st.session_state.extracted_characters_for_universe = ""
if 'current_style_id_for_edit' not in st.session_state: # Initialisation de la variable de session pour l'édition de style
    st.session_state.current_style_id_for_edit = None
# Ajout pour la confirmation de suppression
if 'confirm_delete_id' not in st.session_state:
    st.session_state.confirm_delete_id = None
if 'confirm_delete_type' not in st.session_state:
    st.session_state.confirm_delete_type = None

# --- Gestion des redirections après initialisation de la session ---
if st.session_state.redirect_to_page:
    page_to_redirect_to = st.session_state.redirect_to_page
    st.session_state.redirect_to_page = None
    st.query_params["page"] = page_to_redirect_to.replace(" ", "%20")
    st.rerun()

# --- Fonctions de confirmation personnalisées (remplacement de alert/confirm) ---
# Ces fonctions manipulent st.session_state pour afficher/masquer un message de confirmation
def show_confirm_modal(item_id, item_type):
    st.session_state.confirm_delete_id = item_id
    st.session_state.confirm_delete_type = item_type
    st.rerun() # Trigger a rerun to show the modal

def hide_confirm_modal():
    st.session_state.confirm_delete_id = None
    st.session_state.confirm_delete_type = None
    st.rerun() # Trigger a rerun to hide the modal

def perform_delete(item_id, item_type):
    if item_type == "oeuvre":
        if sheets_connector.delete_row_by_id(config.WORKSHEET_NAME_OEUVRES, 'ID_Oeuvre', item_id):
            # Optional: delete local text file
            df_oeuvres = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES) # Reload to find URL
            oeuvre_row = df_oeuvres[df_oeuvres['ID_Oeuvre'] == item_id]
            if not oeuvre_row.empty and oeuvre_row.iloc[0].get('URL_Texte_Local'):
                local_text_path = os.path.join(os.path.dirname(__file__), oeuvre_row.iloc[0]['URL_Texte_Local'])
                if os.path.exists(local_text_path):
                    try:
                        os.remove(local_text_path)
                        st.success(f"Fichier local de l'œuvre {item_id} supprimé.")
                    except Exception as e:
                        st.error(f"Erreur lors de la suppression du fichier local de l'œuvre {item_id}: {e}")
            sheets_connector.load_data_from_sheet.clear()
            st.success(f"L'œuvre '{item_id}' a été supprimée avec succès.")
            hide_confirm_modal() # Hide modal and rerun
        else:
            st.error(f"Échec de la suppression de l'œuvre '{item_id}'.")
    elif item_type == "universe":
        if sheets_connector.delete_row_by_id(config.WORKSHEET_NAME_UNIVERS, 'ID_Univers', item_id):
            sheets_connector.load_data_from_sheet.clear()
            st.success(f"L'univers '{item_id}' a été supprimé avec succès.")
            hide_confirm_modal()
        else:
            st.error(f"Échec de la suppression de l'univers '{item_id}'.")
    elif item_type == "style":
        if sheets_connector.delete_row_by_id(config.WORKSHEET_NAME_STYLES, 'ID_Style', item_id):
            sheets_connector.load_data_from_sheet.clear()
            st.success(f"Le style '{item_id}' a été supprimé avec succès.")
            hide_confirm_modal()
        else:
            st.error(f"Échec de la suppression du style '{item_id}'.")
    else:
        st.error("Type d'élément à supprimer inconnu.")

# --- Affichage du modal de confirmation ---
if st.session_state.confirm_delete_id:
    st.warning(f"Êtes-vous sûr de vouloir supprimer l'élément '{st.session_state.confirm_delete_id}' de type '{st.session_state.confirm_delete_type}' ? Cette action est irréversible.")
    col_confirm_yes, col_confirm_no = st.columns(2)
    with col_confirm_yes:
        if st.button("Oui, Supprimer Définitivement", key="confirm_delete_yes_btn"):
            perform_delete(st.session_state.confirm_delete_id, st.session_state.confirm_delete_type)
    with col_confirm_no:
        if st.button("Non, Annuler", key="confirm_delete_no_btn"):
            hide_confirm_modal()


# --- Titre de l'application Streamlit ---
st.set_page_config(
    page_title="CARTEL DES PLAISIRS - QG Créateur",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("😈 Le Quartier Général du CARTEL DES PLAISIRS 😈")
st.markdown("---")

# --- Navigation ---
st.sidebar.title("Navigation")
current_page_from_query = st.query_params.get("page", ["Accueil"])[0].replace("%20", " ")

nav_options = [
    "Accueil",
    "Générateur de Texte (Standalone)",
    "Générateur de Suite",
    "Atelier de Production & Publication",
    "Générateur de Tendances Marché",
    "Générateur de Performances",
    "Veille Stratégique",
    "Portfolio & Performance",
    "Finances du Cartel",
    "Directive Stratégique de l'Oracle",
    "Gestion des Univers & Personnages",
    "Gestion des Styles d'Écriture"
]

if current_page_from_query in nav_options:
    page = st.sidebar.radio("Aller à :", nav_options, index=nav_options.index(current_page_from_query))
else:
    page = st.sidebar.radio("Aller à :", nav_options)


# --- Contenu des pages ---

if page == "Accueil":
    st.header("Bienvenue, Gardien !")
    st.write("Ce tableau de bord est le centre de commandement de votre micro-empire médiatique. Utilisez la barre latérale pour naviguer.")

    st.subheader("Vos Œuvres Actuelles (Directement de Google Sheets)")
    df_oeuvres = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)

    if not df_oeuvres.empty:
        st.write(f"**{len(df_oeuvres)}** œuvres enregistrées dans le Sanctuaire.")
        df_oeuvres['Serie_Info'] = df_oeuvres.apply(
            lambda row: f"Série: {row['ID_Parent_Serie']} (Tome {row['Numero_Tome']})" if row['ID_Parent_Serie'] and row['Numero_Tome'] and row['Numero_Tome'] > 0 else "Standalone", axis=1
        )
        st.dataframe(df_oeuvres[['ID_Oeuvre', 'Titre_Original', 'Statut_Publication', 'Date_Creation', 'Serie_Info']].head(10))
    else:
        st.info("Aucune œuvre dans l'onglet 'Oeuvres' ou problème de connexion.")


elif page == "Générateur de Texte (Standalone)":
    st.header("✨ Générateur de Texte (Standalone) : Invoquez l'Oracle")
    st.write("Utilisez les paramètres ci-dessous pour guider l'Oracle dans la création d'une nouvelle œuvre érotique indépendante. Le texte généré sera automatiquement sauvegardé dans votre Google Sheet ET localement sur votre machine.")
    st.info("💡 **Performance :** Les opérations de génération (texte, prompts, kit de lancement) peuvent prendre quelques secondes (jusqu'à 30-60 secondes pour les plus longs textes). Streamlit affichera un indicateur de chargement. Pour des applications de plus grande envergure avec des traitements très lourds en arrière-plan, il serait nécessaire d'intégrer un système de files d'attente (comme Celery avec Redis ou RabbitMQ) pour que l'interface utilisateur reste réactive. Cependant, pour une application locale comme celle-ci, l'approche actuelle est généralement suffisante et plus simple à maintenir.")


    default_theme = "cyberpunk"
    default_mood = "sensuel"
    default_protagonist_type = "humain"
    default_pov = "troisième personne"
    default_spiciness = "modéré"
    default_setting = "futuriste"
    default_tropes = ""
    default_plot_elements_standalone = ""
    default_character_details_standalone = ""
    default_style_description = ""

    df_univers = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_UNIVERS)
    universe_options = [''] + ([f"{row['ID_Univers']} - {row['Nom_Univers']}" for _, row in df_univers.iterrows()] if not df_univers.empty else [])
    selected_universe_str = st.selectbox("Lier à un Univers existant (Facultatif) :", universe_options, key="standalone_universe_select")

    selected_universe_data = {}
    if selected_universe_str:
        universe_id = selected_universe_str.split(' - ')[0]
        if not df_univers.empty and universe_id in df_univers['ID_Univers'].tolist():
            selected_universe_data = df_univers[df_univers['ID_Univers'] == universe_id].iloc[0].to_dict()
            default_theme = selected_universe_data.get('Nom_Univers', default_theme)
            default_setting = selected_universe_data.get('Description_Globale', default_setting).split('.')[0].strip() if selected_universe_data.get('Description_Globale') else default_setting
            default_plot_elements_standalone = selected_universe_data.get('Elements_Cles_Intrigue', '')
            default_character_details_standalone = selected_universe_data.get('Personnages_Cles', '')
            st.info(f"Les paramètres ont été pré-remplis avec les détails de l'univers '{selected_universe_data.get('Nom_Univers', 'Inconnu')}'.")
        else:
            st.warning(f"L'ID d'univers '{universe_id}' n'a pas été trouvé. Création d'une œuvre standalone sans lien d'univers.")


    df_styles = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_STYLES)
    style_options = [''] + ([f"{row['ID_Style']} - {row['Nom_Style']}" for _, row in df_styles.iterrows()] if not df_styles.empty else [])
    selected_style_str = st.selectbox("Choisir un Style d'Écriture (Facultatif) :", style_options, key="standalone_style_select")

    if selected_style_str:
        style_id = selected_style_str.split(' - ')[0]
        if not df_styles.empty and style_id in df_styles['ID_Style'].tolist():
            selected_style_data = df_styles[df_styles['ID_Style'] == style_id].iloc[0]
            default_style_description = selected_style_data.get('Description_Style', '')
            default_spiciness = selected_style_data.get('Niveau_Explicite_Defaut', default_spiciness)
            st.info(f"Les paramètres de style et de sensualité ont été pré-remplis avec le style '{selected_style_data.get('Nom_Style', 'Inconnu')}'.")
        else:
            st.warning(f"L'ID de style '{style_id}' n'a pas été trouvé. La génération se fera sans style spécifique.")


    if st.session_state.generated_narrative_params and st.session_state.generated_narrative_params.get("objective_text_generation"):
        params = st.session_state.generated_narrative_params
        default_theme = params.get("theme", default_theme)
        default_mood = params.get("mood", default_mood)
        default_protagonist_type = params.get("protagonist_type", default_protagonist_type)
        default_setting = params.get("setting", default_setting)
        default_spiciness = params.get("spiciness", default_spiciness)
        if params.get("tropes"):
            default_tropes = ", ".join(params["tropes"])
        st.info("Les paramètres du générateur ont été pré-remplis par la Directive Stratégique de l'Oracle.")
        st.session_state.generated_narrative_params = None


    with st.form("text_generation_form"):
        st.subheader("Paramètres de Génération :")
        col1, col2 = st.columns(2)
        with col1:
            theme_input = st.text_input("Thème principal (ex: 'cyberpunk', 'fantasy')", value=default_theme, key="gen_theme_input")
            mood_options = ["sensuel", "passionné", "mystérieux", "dark", "joyeux", "dramatique"]
            try:
                mood_index = mood_options.index(default_mood)
            except ValueError:
                mood_index = 0
            mood_input = st.selectbox("Ambiance / Ton :", mood_options, index=mood_index, key="gen_mood_input")

            protagonist_type_input = st.text_input("Type de protagoniste (ex: 'humain', 'cyborg', 'elfe')", value=default_protagonist_type, key="gen_protagonist_type_input")
        with col2:
            pov_options = ["première personne", "troisième personne"]
            try:
                pov_index = pov_options.index(default_pov)
            except ValueError:
                pov_index = 1
            pov_input = st.selectbox("Point de vue narratif :", pov_options, index=pov_index, key="gen_pov_input")

            spiciness_options = ["doux", "modéré", "explicite"]
            try:
                spiciness_index = spiciness_options.index(default_spiciness)
            except ValueError:
                spiciness_index = 1
            spiciness_input = st.selectbox("Niveau de sensualité :", spiciness_options, index=spiciness_index, key="gen_spiciness_input")

            setting_input = st.text_input("Cadre de l'histoire (ex: 'futuriste', 'médiéval')", value=default_setting, key="gen_setting_input")

        tropes_input = st.text_area("Tropes / Fétiches spécifiques (séparés par des virgules, facultatif) :", placeholder="ex: 'amour interdit, rivalité, pouvoirs magiques'", value=default_tropes, key="gen_tropes_input")
        plot_elements_input = st.text_area("Éléments clés de l'intrigue à inclure (issus de l'univers si lié) :", value=default_plot_elements_standalone, key="gen_plot_elements_input")
        character_details_input = st.text_area("Détails sur les personnages principaux (issus de l'univers si lié) :", value=default_character_details_standalone, key="gen_character_details_input")

        st.text_area("Description du Style d'Écriture sélectionné :", value=default_style_description, height=150, disabled=True, key="gen_style_description_display")

        length_words_input = st.slider("Longueur approximative (mots) :", min_value=200, max_value=20000, value=500, step=100, key="gen_length_words_input")
        num_variants_input = st.slider("Nombre de variantes à générer :", min_value=1, max_value=3, value=1, step=1, key="gen_num_variants_input")

        st.subheader("Métadonnées de l'Œuvre :")
        titre_original_input = st.text_input("Titre de travail de l'Œuvre :", value=f"Nouvelle Œuvre - {datetime.now().strftime('%Y-%m-%d %H:%M')}", key="gen_titre_original_input")
        description_courte_input_field = st.text_area("Courte description / Pitch (sera rempli par le résumé généré si vide) :", value="", key="gen_description_courte_input_field")

        submitted = st.form_submit_button("Générer & Sauvegarder l'Œuvre Standalone")

        if submitted:
            theme = st.session_state.gen_theme_input.strip() if st.session_state.gen_theme_input else "général"
            mood = st.session_state.gen_mood_input.strip() if st.session_state.gen_mood_input else "sensuel"
            protagonist_type = st.session_state.gen_protagonist_type_input.strip() if st.session_state.gen_protagonist_type_input else "humain"
            pov = st.session_state.gen_pov_input.strip() if st.session_state.gen_pov_input else "troisième personne"
            spiciness = st.session_state.gen_spiciness_input.strip() if st.session_state.gen_spiciness_input else "modéré"
            setting = st.session_state.gen_setting_input.strip() if st.session_state.gen_setting_input else "futuriste"

            tropes = [t.strip() for t in st.session_state.gen_tropes_input.split(',') if t.strip()] if st.session_state.gen_tropes_input else None
            plot_elements = [e.strip() for e in st.session_state.gen_plot_elements_input.split(',') if e.strip()] if st.session_state.gen_plot_elements_input else None
            character_details = [d.strip() for d in st.session_state.gen_character_details_input.split(',') if d.strip()] if st.session_state.gen_character_details_input else None

            length_words = st.session_state.gen_length_words_input
            num_variants = st.session_state.gen_num_variants_input
            titre_original = st.session_state.gen_titre_original_input.strip() if st.session_state.gen_titre_original_input else f"Nouvelle Œuvre - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            description_courte = st.session_state.gen_description_courte_input_field.strip()

            generated_data_list = []
            for i in range(num_variants):
                with st.spinner(f"L'Oracle est à l'œuvre... Génération de la variante {i+1}/{num_variants}..."):
                    generated_text = gemini_oracle.generate_erotic_text(
                        theme=theme,
                        mood=mood,
                        length_words=length_words,
                        protagonist_type=protagonist_type,
                        setting=setting,
                        pov=pov,
                        spiciness=spiciness,
                        tropes=tropes,
                        plot_elements=plot_elements,
                        character_details=character_details,
                        writing_style_description=default_style_description
                    )
                    image_prompts = gemini_oracle.generate_image_prompts(generated_text)
                    launch_kit = gemini_oracle.generate_launch_kit(generated_text)

                generated_data_list.append({
                    "text": generated_text,
                    "image_prompts": image_prompts,
                    "launch_kit": launch_kit,
                    "titre_original": f"{titre_original} - Var {i+1}" if num_variants > 1 else titre_original,
                    "description_courte_input": description_courte
                })

            for i, data in enumerate(generated_data_list):
                st.markdown(f"### Résultats de la Variante {i+1}")
                st.subheader("Texte Généré :")
                st.text_area(f"Contenu de l'œuvre (Variante {i+1})", value=data["text"], height=400, disabled=True, key=f"text_gen_{i}")

                st.subheader("Suggestions de l'Oracle :")
                st.write("##### Prompts d'Image :")
                for j, prompt in enumerate(data["image_prompts"]):
                    st.code(f"Prompt {j+1}:\n{prompt}")

                st.write("##### Kit de Lancement :")
                st.write(f"**Titres :** {', '.join(data['launch_kit']['titles'])}")
                st.markdown(f"**Résumé :** {data['launch_kit']['summary']}")
                st.write(f"**Tags :** {', '.join(data['launch_kit']['tags'])}")

                universe_id_to_save = selected_universe_data.get('ID_Univers', '')
                if sheets_connector.save_new_oeuvre_to_sheet(
                    data["text"], data["image_prompts"], data["launch_kit"],
                    titre_original=data["titre_original"],
                    description_courte=data["description_courte_input"],
                    id_parent_serie=universe_id_to_save,
                    numero_tome=1 if universe_id_to_save else ""
                ):
                    st.success(f"Variante {i+1} sauvegardée avec succès dans Google Sheets et localement !")

            sheets_connector.load_data_from_sheet.clear()


elif page == "Générateur de Suite":
    st.header("📚 Générateur de Suite : L'Oracle Conteur de Saga")
    st.write("Sélectionnez une œuvre existante pour laquelle l'Oracle va générer une suite. Les éléments clés (résumé, personnages, intrigue) seront automatiquement extraits de l'œuvre précédente pour assurer la continuité.")
    st.info("💡 **Performance :** Les opérations de génération (texte, prompts, kit de lancement) peuvent prendre quelques secondes (jusqu'à 30-60 secondes pour les plus longs textes). Streamlit affichera un indicateur de chargement. Pour des applications de plus grande envergure avec des traitements très lourds en arrière-plan, il serait nécessaire d'intégrer un système de files d'attente (comme Celery avec Redis ou RabbitMQ) pour que l'interface utilisateur reste réactive. Cependant, pour une application locale comme celle-ci, l'approche actuelle est généralement suffisante et plus simple à maintenir.")


    df_oeuvres = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)
    df_univers = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_UNIVERS)

    if df_oeuvres.empty:
        st.info("Aucune œuvre disponible pour générer une suite. Créez d'abord une œuvre standalone via 'Générateur de Texte (Standalone)'.")
    else:
        df_published_oeuvres = df_oeuvres[df_oeuvres['Statut_Publication'].isin(["Publié", "Prêt à Publier"])].copy()

        if df_published_oeuvres.empty:
            st.info("Aucune œuvre 'Publiée' ou 'Prête à Publier' pour générer une suite. Finalisez d'abord une œuvre.")
        else:
            df_published_oeuvres['Display_Name'] = df_published_oeuvres.apply(
                lambda row: f"{row['Titre_Original']} (ID: {row['ID_Oeuvre']})" if row['Titre_Original'] else f"ID: {row['ID_Oeuvre']}", axis=1
            )

            selected_previous_oeuvre_str = st.selectbox(
                "Sélectionnez l'œuvre précédente (Parent) pour laquelle générer une suite :",
                [''] + df_published_oeuvres['Display_Name'].tolist(),
                key="suite_parent_select"
            )

            selected_parent_oeuvre = {}
            if selected_previous_oeuvre_str:
                selected_parent_id = selected_previous_oeuvre_str.split('ID: ')[1].replace(')', '')
                if not df_published_oeuvres.empty and selected_parent_id in df_published_oeuvres['ID_Oeuvre'].tolist():
                    selected_parent_oeuvre = df_published_oeuvres[df_published_oeuvres['ID_Oeuvre'] == selected_parent_id].iloc[0].to_dict()
                    st.subheader(f"Génération de suite pour : {selected_parent_oeuvre.get('Titre_Original', 'Œuvre Inconnue')}")
                else:
                    st.warning(f"L'ID d'œuvre parente '{selected_parent_id}' n'a pas été trouvé. Veuillez sélectionner une œuvre valide.")

                default_plot_summary_suite = ""
                default_character_details_suite = ""
                default_sequel_directives = ""
                default_style_description_suite = ""

                if st.session_state.generated_narrative_params and st.session_state.generated_narrative_params.get("objective_text_generation_suite"):
                    params = st.session_state.generated_narrative_params
                    default_sequel_directives = params.get("sequel_directives", "")
                    st.info("Les paramètres du générateur de suite ont été pré-remplis par la Directive Stratégique de l'Oracle.")
                    st.session_state.generated_narrative_params = None

                parent_full_text = ""
                universe_plot_elements = ""
                universe_character_details = ""

                if selected_parent_oeuvre.get('ID_Parent_Serie') and not df_univers.empty:
                    parent_universe_id = selected_parent_oeuvre['ID_Parent_Serie']
                    universe_data = df_univers[df_univers['ID_Univers'] == parent_universe_id]
                    if not universe_data.empty:
                        universe_data = universe_data.iloc[0]
                        universe_plot_elements = universe_data.get('Elements_Cles_Intrigue', '')
                        universe_character_details = universe_data.get('Personnages_Cles', '')
                        st.info(f"Contexte pré-rempli avec la mémoire de l'univers '{universe_data.get('Nom_Univers', 'Inconnu')}'.")
                    else:
                        st.warning(f"L'univers parent '{parent_universe_id}' n'a pas été trouvé. Les données seront extraites du texte de l'œuvre.")


                if not universe_plot_elements or not universe_character_details:
                    if selected_parent_oeuvre.get('Texte_Genere'):
                        parent_full_text = selected_parent_oeuvre.get('Texte_Genere')
                    elif selected_parent_oeuvre.get('URL_Texte_Local'):
                        local_text_path_relative = selected_parent_oeuvre['URL_Texte_Local']
                        local_text_path = os.path.join(os.path.dirname(__file__), local_text_path_relative)
                        if os.path.exists(local_text_path):
                            with open(local_text_path, 'r', encoding='utf-8') as f:
                                parent_full_text = f.read()

                    if parent_full_text and parent_full_text.strip() != "":
                        with st.spinner("L'Oracle analyse le tome précédent pour un pré-remplissage intelligent (intrigue et personnages)..."):
                            if not universe_plot_elements:
                                auto_plot_summary_from_parent = gemini_oracle.summarize_plot(parent_full_text)
                            else:
                                auto_plot_summary_from_parent = universe_plot_elements

                            if not universe_character_details:
                                auto_character_details_from_parent = gemini_oracle.extract_character_details(parent_full_text)
                            else:
                                auto_character_details_from_parent = universe_character_details
                    else:
                        st.info("Le texte de l'œuvre parente est vide ou introuvable. Veuillez saisir manuellement le contexte.")
                        auto_plot_summary_from_parent = selected_parent_oeuvre.get('Resume_Suggere', selected_parent_oeuvre.get('Description_Courte', ''))
                        auto_character_details_from_parent = "Veuillez saisir les personnages du tome précédent."
                else:
                    auto_plot_summary_from_parent = universe_plot_elements
                    auto_character_details_from_parent = universe_character_details


                final_plot_summary_for_input = auto_plot_summary_from_parent
                final_character_details_for_input = auto_character_details_from_parent

                df_styles = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_STYLES)
                style_options_suite = [''] + ([f"{row['ID_Style']} - {row['Nom_Style']}" for _, row in df_styles.iterrows()] if not df_styles.empty else [])
                selected_style_suite_str = st.selectbox("Choisir un Style d'Écriture (Facultatif) :", style_options_suite, key="suite_style_select")

                selected_style_suite_data = {}
                default_style_description_suite = ""
                if selected_style_suite_str:
                    style_id_suite = selected_style_suite_str.split(' - ')[0]
                    if not df_styles.empty and style_id_suite in df_styles['ID_Style'].tolist():
                        selected_style_suite_data = df_styles[df_styles['ID_Style'] == style_id_suite].iloc[0].to_dict()
                        default_style_description_suite = selected_style_suite_data.get('Description_Style', '')
                        st.info(f"Le style d'écriture a été défini sur '{selected_style_suite_data.get('Nom_Style', 'Inconnu')}'.")
                    else:
                        st.warning(f"L'ID de style '{style_id_suite}' n'a pas été trouvé. La génération de suite se fera sans style spécifique.")

                next_tome_number = 2
                parent_tome_num = pd.to_numeric(selected_parent_oeuvre.get('Numero_Tome', 1), errors='coerce')
                if pd.notna(parent_tome_num) and parent_tome_num >= 1:
                    if selected_parent_oeuvre.get('ID_Parent_Serie'):
                        related_series_tomes = df_oeuvres[df_oeuvres['ID_Parent_Serie'] == selected_parent_oeuvre['ID_Parent_Serie']].copy()
                        related_series_tomes['Numero_Tome_Num'] = pd.to_numeric(related_series_tomes['Numero_Tome'], errors='coerce')
                        if not related_series_tomes.empty and related_series_tomes['Numero_Tome_Num'].notna().any():
                            max_tome_num = related_series_tomes['Numero_Tome_Num'].max()
                            if pd.notna(max_tome_num):
                                next_tome_number = int(max_tome_num) + 1
                            else:
                                next_tome_number = 2
                        else:
                            next_tome_number = int(parent_tome_num) + 1
                    else:
                        next_tome_number = int(parent_tome_num) + 1
                else:
                    st.warning("Numéro de tome du parent non valide. Le prochain tome sera défini par défaut à 2.")
                    next_tome_number = 2


                with st.form("suite_generation_form"):
                    st.subheader("Contexte Narratif de la Suite (Pré-rempli par l'Oracle)")
                    plot_input = st.text_area("Résumé de l'intrigue du tome précédent (modifiable) :", value=final_plot_summary_for_input, height=100, key="previous_plot_input")
                    characters_input = st.text_area("Détails clés sur les personnages du tome précédent (modifiable) :", value=final_character_details_for_input, height=100, key="previous_characters_input")

                    sequel_directives_input = st.text_area("Directives spécifiques pour ce nouveau tome (éléments à inclure, arcs narratifs) :", placeholder="Ex: 'Introduire un nouvel antagoniste, développer leur relation, un retournement de situation inattendu.'", value=default_sequel_directives, key="sequel_directives_input")

                    length_words_suite = st.slider("Longueur approximative de la suite (mots) :", min_value=200, max_value=20000, value=selected_parent_oeuvre.get('length_words_original', 500), step=100, key="length_words_suite")
                    num_variants_suite = st.slider("Nombre de variantes de la suite à générer :", min_value=1, max_value=3, value=1, step=1, key="num_variants_suite")

                    st.text_area("Description du Style d'Écriture sélectionné :", value=default_style_description_suite, height=100, disabled=True, key="suite_style_description_display")


                    st.subheader("Métadonnées de la Suite :")
                    titre_original_suite = st.text_input(f"Titre de travail de la Suite (Tome {next_tome_number}) :", value=f"{selected_parent_oeuvre.get('Titre_Original', 'Titre Inconnu')} - Tome {next_tome_number}", key="titre_original_suite")
                    description_courte_suite = st.text_area("Courte description / Pitch pour cette suite :", value="", key="description_courte_suite")

                    submitted_suite = st.form_submit_button("Générer & Sauvegarder la Suite")

                    if submitted_suite:
                        generated_data_list_suite = []
                        for i in range(num_variants_suite):
                            with st.spinner(f"L'Oracle est à l'œuvre... Génération de la variante {i+1}/{num_variants_suite} de la suite..."):
                                generated_text_suite = gemini_oracle.generate_erotic_text_suite(
                                    previous_text_summary=st.session_state.previous_plot_input,
                                    previous_characters_summary=st.session_state.previous_characters_input,
                                    previous_plot_summary=st.session_state.previous_plot_input,
                                    sequel_directives=st.session_state.sequel_directives_input,
                                    length_words=st.session_state.length_words_suite,
                                    writing_style_description=default_style_description_suite
                                )
                                image_prompts_suite = gemini_oracle.generate_image_prompts(generated_text_suite)
                                launch_kit_suite = gemini_oracle.generate_launch_kit(generated_text_suite)

                            generated_data_list_suite.append({
                                "text": generated_text_suite,
                                "image_prompts": image_prompts_suite,
                                "launch_kit": launch_kit_suite,
                                "titre_original": f"{st.session_state.titre_original_suite} - Var {i+1}" if num_variants_suite > 1 else st.session_state.titre_original_suite,
                                "description_courte_input": st.session_state.description_courte_suite
                            })

                        if selected_parent_oeuvre.get('ID_Parent_Serie') == "" or pd.isna(selected_parent_oeuvre.get('Numero_Tome')) or selected_parent_oeuvre.get('Numero_Tome') == 0:
                            parent_updates = {'ID_Parent_Serie': selected_parent_id, 'Numero_Tome': 1}
                            sheets_connector.update_oeuvre_in_sheet(selected_parent_id, parent_updates)
                            st.info(f"L'œuvre parente '{selected_parent_oeuvre.get('Titre_Original', 'Œuvre Inconnue')}' a été marquée comme Tome 1 de cette nouvelle série.")
                            sheets_connector.load_data_from_sheet.clear()


                        for i, data in enumerate(generated_data_list_suite):
                            st.markdown(f"### Résultats de la Suite - Variante {i+1}")
                            st.subheader("Texte Généré :")
                            st.text_area(f"Contenu de la suite (Variante {i+1})", value=data["text"], height=400, disabled=True, key=f"suite_text_gen_result_{i}")

                            st.subheader("Suggestions de l'Oracle :")
                            st.write("##### Prompts d'Image :")
                            for j, prompt in enumerate(data["image_prompts"]):
                                st.code(f"Prompt {j+1}:\n{prompt}")

                            st.write("##### Kit de Lancement :")
                            st.write(f"**Titres :** {', '.join(data['launch_kit']['titles'])}")
                            st.markdown(f"**Résumé :** {data['launch_kit']['summary']}")
                            st.write(f"**Tags :** {', '.join(data['launch_kit']['tags'])}")

                            if sheets_connector.save_new_oeuvre_to_sheet(
                                data["text"], data["image_prompts"], data["launch_kit"],
                                titre_original=data["titre_original"],
                                description_courte=data["description_courte_input"],
                                id_parent_serie=selected_parent_id,
                                numero_tome=next_tome_number
                            ):
                                st.success(f"Suite - Variante {i+1} sauvegardée avec succès dans Google Sheets et localement !")

                        sheets_connector.load_data_from_sheet.clear()


elif page == "Atelier de Production & Publication":
    st.header("✍️ Atelier de Production & Publication : Peaufinez vos chefs-d'œuvre")
    st.write("Sélectionnez une œuvre pour la peaufiner, gérer sa couverture, et définir sa stratégie de publication.")

    df_oeuvres = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)

    if not df_oeuvres.empty:
        st.subheader("Sélectionnez une Œuvre")
        df_oeuvres['Numero_Tome_Num'] = pd.to_numeric(df_oeuvres['Numero_Tome'], errors='coerce').fillna(0)
        df_oeuvres_sorted = df_oeuvres.sort_values(by=['ID_Parent_Serie', 'Numero_Tome_Num', 'Date_Creation'], ascending=[True, True, False])

        df_oeuvres_sorted['Display_Name_Full'] = df_oeuvres_sorted.apply(
            lambda row: f"{row['Titre_Original']} (Tome {int(row['Numero_Tome_Num'])})" if row['ID_Parent_Serie'] and pd.notna(row['Numero_Tome_Num']) and row['Numero_Tome_Num'] > 0 else row['Titre_Original'], axis=1
        )
        oeuvre_options = [''] + [f"{row['ID_Oeuvre']} - {row['Display_Name_Full']}" for index, row in df_oeuvres_sorted.iterrows()]

        selected_oeuvre_str = st.selectbox("Choisissez une œuvre :", oeuvre_options)

        selected_oeuvre = None
        if selected_oeuvre_str:
            selected_id = selected_oeuvre_str.split(' - ')[0]
            if selected_id in df_oeuvres_sorted['ID_Oeuvre'].tolist():
                selected_oeuvre = df_oeuvres_sorted[df_oeuvres_sorted['ID_Oeuvre'] == selected_id].iloc[0]
            else:
                st.error(f"L'ID d'œuvre '{selected_id}' n'a pas été trouvé. Veuillez recharger la page ou choisir une œuvre valide.")
                selected_oeuvre = None

            if selected_oeuvre is not None:
                st.subheader(f"Détails de l'Œuvre : {selected_oeuvre['Titre_Original']}")

                if selected_oeuvre.get('ID_Parent_Serie') and selected_oeuvre.get('Numero_Tome'):
                    st.info(f"Fait partie d'une série. Parent : {selected_oeuvre.get('ID_Parent_Serie')}, Tome : {selected_oeuvre.get('Numero_Tome')}")

                tab_verb, tab_visual, tab_publish, tab_edit, tab_delete = st.tabs(["Le Verbe", "Le Visuel (Couverture)", "La Publication", "Édition Manuelle", "Suppression"])

                with tab_verb:
                    st.subheader("Le Verbe (Texte de l'Œuvre)")
                    if 'Texte_Genere' in selected_oeuvre and pd.notna(selected_oeuvre['Texte_Genere']) and selected_oeuvre['Texte_Genere'].strip() != "":
                        text_content_display = selected_oeuvre['Texte_Genere']
                        st.text_area("Texte de l'œuvre (généré) :", value=text_content_display, height=400, disabled=True)
                        clean_title_for_filename_gen = utils.clean_filename_slug(selected_oeuvre['Titre_Original'])
                        st.download_button(
                            label="Télécharger le Texte Généré (depuis Google Sheets)",
                            data=text_content_display,
                            file_name=f"{selected_oeuvre['ID_Oeuvre']}_{clean_title_for_filename_gen}.txt",
                            mime="text/plain"
                        )
                    elif 'URL_Texte_Local' in selected_oeuvre and pd.notna(selected_oeuvre['URL_Texte_Local']) and selected_oeuvre['URL_Texte_Local'].strip() != "":
                        local_text_path = os.path.join(os.path.dirname(__file__), selected_oeuvre['URL_Texte_Local'])
                        if os.path.exists(local_text_path):
                            with open(local_text_path, 'r', encoding='utf-8') as f:
                                full_text = f.read()
                            st.text_area("Contenu complet depuis fichier local :", value=full_text, height=400, disabled=True)
                            clean_title_for_filename_local = utils.clean_filename_slug(selected_oeuvre['Titre_Original'])
                            st.download_button(
                                label="Télécharger le Texte Local",
                                data=full_text,
                                file_name=f"{selected_oeuvre['ID_Oeuvre']}_{clean_title_for_filename_local}_local.txt",
                                mime="text/plain"
                            )
                        else:
                            st.warning(f"Fichier texte local non trouvé à : {selected_oeuvre['URL_Texte_Local']}. Assurez-vous qu'il est dans le dossier 'assets/texts/'.")
                    elif 'Description_Courte' in selected_oeuvre and pd.notna(selected_oeuvre['Description_Courte']) and selected_oeuvre['Description_Courte'].strip() != "":
                        st.text_area("Description courte :", value=selected_oeuvre['Description_Courte'], height=150, disabled=True)
                    else:
                        st.info("Aucun texte ou description disponible pour cette œuvre.")


                with tab_visual:
                    st.subheader("Le Visuel (Gestion de Couverture)")
                    st.write("Ces prompts sont générés par l'Oracle (Gemini). Utilisez-les avec un **outil de génération d'images EXTERNE et GRATUIT** (ex: [Clipdrop.co/stable-diffusion](https://clipdrop.co/stable-diffusion), [Leonardo.ai](https://app.leonardo.ai), ou des démos sur [Hugging Face Spaces](https://huggingface.co/spaces)) pour créer votre couverture. Ensuite, importez l'image ici.")

                    st.markdown("##### Prompts d'Image Suggérés par l'Oracle (par Gemini) :")
                    generated_prompts = []
                    for i in range(1, 4):
                        col_name = f'Prompt_Image_{i}'
                        prompt_val = selected_oeuvre.get(col_name, '')
                        if pd.notna(prompt_val) and prompt_val.strip() != "":
                            generated_prompts.append(prompt_val)
                            st.code(f"Prompt {i}: {prompt_val}")
                        else:
                            st.info(f"Prompt d'image {i} non disponible.")

                    st.markdown("---")
                    st.subheader("Importer votre Couverture Finale")

                    default_custom_prompt_val = ""
                    if generated_prompts and selected_oeuvre.get('Prompt_Image_Genere') in generated_prompts:
                        default_custom_prompt_val = selected_oeuvre.get('Prompt_Image_Genere', '')
                    elif selected_oeuvre.get('Prompt_Image_Genere'):
                        default_custom_prompt_val = selected_oeuvre.get('Prompt_Image_Genere', '')
                    elif generated_prompts:
                        default_custom_prompt_val = generated_prompts[0]

                    selected_prompt_for_doc = st.selectbox("Prompt de l'Oracle utilisé pour la génération externe (si applicable) :",
                                                            [''] + generated_prompts,
                                                            index=generated_prompts.index(selected_oeuvre.get('Prompt_Image_Genere', '')) + 1 if selected_oeuvre.get('Prompt_Image_Genere') in generated_prompts else 0,
                                                            key="prompt_select_doc")
                    custom_prompt_for_doc = selected_prompt_for_doc if selected_prompt_for_doc else default_custom_prompt_val
                    custom_prompt_for_doc = st.text_area("Ou prompt personnalisé utilisé :", value=custom_prompt_for_doc, key="custom_prompt_doc")

                    uploaded_file = st.file_uploader("Chargez votre image de couverture finale ici (.jpg, .png, etc.) :", type=["jpg", "png", "jpeg", "webp"], key="cover_uploader")

                    image_path_input = st.text_input("Ou entrez le chemin local de l'image (ex: assets/covers/mon_image.jpg) :", value=selected_oeuvre.get('URL_Image_Couverture', ''), key="image_path_input")

                    final_image_path_to_save = image_path_input

                    if uploaded_file is not None:
                        save_folder = config.COVERS_FOLDER
                        file_extension = os.path.splitext(uploaded_file.name)[1]
                        filename_slug_cover = utils.clean_filename_slug(selected_oeuvre['Titre_Original'])
                        filename = f"{selected_oeuvre['ID_Oeuvre']}_cover_{filename_slug_cover}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_extension}"
                        local_image_path_full = os.path.join(save_folder, filename) # Full path for saving
                        final_image_path_to_save = os.path.join(os.path.basename(config.ASSETS_FOLDER), os.path.basename(config.COVERS_FOLDER), filename) # Relative path for sheets

                        try:
                            with open(local_image_path_full, "wb") as f:
                                f.write(uploaded_file.getbuffer())
                            st.success(f"Image chargée : {uploaded_file.name}. Sauvegardée localement : `{local_image_path_full}`")
                        except Exception as e:
                            st.error(f"Erreur lors de la sauvegarde du fichier local : {e}")
                            final_image_path_to_save = ""

                    if final_image_path_to_save:
                        display_image_path = final_image_path_to_save
                        if not os.path.isabs(display_image_path) and not display_image_path.startswith("http"):
                            display_image_path = os.path.join(os.path.dirname(__file__), display_image_path)

                        if os.path.exists(display_image_path):
                            st.image(display_image_path, caption="Aperçu de la Couverture (Locale)", width=300)
                        elif final_image_path_to_save.startswith("http"):
                            st.image(final_image_path_to_save, caption="Aperçu de la Couverture (URL Distante)", width=300)
                        else:
                            st.warning(f"Le chemin '{final_image_path_to_save}' ne pointe pas vers un fichier local existant ou une URL valide.")
                    else:
                        st.info("Aucune image de couverture définie.")

                    if st.button("Enregistrer la Couverture & Prompt dans Google Sheets", key="save_cover_btn"):
                        updates = {
                            'Prompt_Image_Genere': custom_prompt_for_doc,
                            'URL_Image_Couverture': final_image_path_to_save
                        }
                        if sheets_connector.update_oeuvre_in_sheet(selected_oeuvre['ID_Oeuvre'], updates):
                            sheets_connector.load_data_from_sheet.clear()
                            st.rerun()


                with tab_publish:
                    st.subheader("La Publication (Kit de Lancement Final)")
                    st.write("Définissez le kit de lancement final pour votre œuvre en vous basant sur les suggestions de l'Oracle.")

                    st.write("##### Titres Suggérés par l'Oracle :")
                    suggested_titles = []
                    for i in range(1, 4):
                        col_name = f'Titre_Suggere_{i}'
                        title_val = selected_oeuvre.get(col_name, '')
                        if pd.notna(title_val) and title_val.strip() != "":
                            suggested_titles.append(title_val)
                            st.write(f"- {title_val}")
                        else:
                            st.info(f"Titre suggéré {i} non disponible.")

                    st.write("##### Résumé Captivant Suggéré par l'Oracle :")
                    suggested_summary = selected_oeuvre.get('Resume_Suggere', '')
                    if pd.notna(suggested_summary) and suggested_summary.strip() != "":
                        st.markdown(suggested_summary)
                    else:
                        st.info("Résumé suggéré non disponible.")

                    st.write("##### Tags Optimisés Suggérés par l'Oracle :")
                    suggested_tags = selected_oeuvre.get('Tags_Suggérés', '')
                    if pd.notna(suggested_tags) and suggested_tags.strip() != "":
                        st.write(suggested_tags)
                    else:
                        st.info("Tags suggérés non disponibles.")

                    st.markdown("---")
                    st.subheader("Définir les Éléments de Publication Finaux")

                    default_final_title = selected_oeuvre.get('Titre_Optimise', '')
                    if not default_final_title and suggested_titles:
                        default_final_title = suggested_titles[0]
                    if not default_final_title and selected_oeuvre.get('Titre_Original'):
                        default_final_title = selected_oeuvre.get('Titre_Original')

                    final_title = st.text_input("Titre final de l'œuvre :", value=default_final_title)
                    final_summary = st.text_area("Résumé final (pour la publication) :", value=selected_oeuvre.get('Resume_Suggere', ''))
                    final_tags = st.text_input("Tags finaux (séparés par des virgules) :", value=selected_oeuvre.get('Tags_Suggérés', ''))
                    final_manual_tags = st.text_input("Tags Manuels additionnels :", value=selected_oeuvre.get('Tags_Manuels', ''))

                    platform_options = ["Patreon", "Kindle", "Sites de niche", "Autre", "Non publié"]
                    current_platforms = selected_oeuvre.get('Plateforme_Publication', '').split(',') if isinstance(selected_oeuvre.get('Plateforme_Publication'), str) and selected_oeuvre.get('Plateforme_Publication').strip() else []
                    default_selected_platforms = [p.strip() for p in current_platforms if p.strip() in platform_options]
                    if not default_selected_platforms and "Non publié" in platform_options:
                        default_selected_platforms = ["Non publié"]

                    final_platform = st.multiselect("Plateforme(s) de Publication :", platform_options, default=default_selected_platforms)

                    status_options = ["Brouillon", "Prêt à Publier", "Publié"]
                    default_status_index = status_options.index(selected_oeuvre.get('Statut_Publication', 'Brouillon')) if selected_oeuvre.get('Statut_Publication', 'Brouillon') in status_options else 0
                    final_status = st.selectbox("Statut de Publication :", status_options, index=default_status_index)
                    final_notes = st.text_area("Notes de l'éditeur :", value=selected_oeuvre.get('Notes_Editeur', ''))

                    if st.button("Enregistrer le Kit de Lancement Final", key="save_launch_kit_btn"):
                        updates = {
                            'Titre_Optimise': final_title,
                            'Resume_Suggere': final_summary,
                            'Tags_Suggérés': final_tags,
                            'Tags_Manuels': final_manual_tags,
                            'Plateforme_Publication': ", ".join(final_platform),
                            'Statut_Publication': final_status,
                            'Notes_Editeur': final_notes
                        }
                        if sheets_connector.update_oeuvre_in_sheet(selected_oeuvre['ID_Oeuvre'], updates):
                            sheets_connector.load_data_from_sheet.clear()
                            st.rerun()

                with tab_edit:
                    st.subheader("Édition Manuelle des Données")
                    st.write("⚠️ Utilisez cette section pour des modifications directes sur les données de l'œuvre. Soyez prudent. Notez que cette édition modifie la ligne dans le Google Sheet.")

                    editable_df = pd.DataFrame([selected_oeuvre.to_dict()])
                    edited_data = st.data_editor(editable_df, num_rows="fixed", hide_index=True)

                    if st.button("Appliquer les Modifications Manuelles", key="apply_manual_edit_btn"):
                        if edited_data is not None and not edited_data.empty:
                            row_to_update = edited_data.iloc[0]
                            updates = {col: row_to_update[col] if pd.notna(row_to_update[col]) else '' for col in edited_data.columns if col != 'ID_Oeuvre'}

                            if 'Numero_Tome' in updates:
                                try:
                                    updates['Numero_Tome'] = int(updates['Numero_Tome']) if str(updates['Numero_Tome']).strip() != '' else ''
                                except ValueError:
                                    updates['Numero_Tome'] = ''

                            if sheets_connector.update_oeuvre_in_sheet(selected_oeuvre['ID_Oeuvre'], updates):
                                sheets_connector.load_data_from_sheet.clear()
                                st.rerun()
                        else:
                            st.warning("Aucune modification à appliquer.")

                with tab_delete:
                    st.subheader("Supprimer l'Œuvre")
                    st.warning("ATTENTION : La suppression d'une œuvre est **irréversible**.")
                    if st.button(f"Supprimer l'Œuvre '{selected_oeuvre['Titre_Original']}'", key="delete_oeuvre_btn"):
                        show_confirm_modal(selected_oeuvre['ID_Oeuvre'], "oeuvre")

            else:
                st.info("Sélectionnez une œuvre valide ci-dessus pour accéder à l'atelier.")
        else:
            st.info("Sélectionnez une œuvre valide ci-dessus pour accéder à l'atelier.")
    else:
        st.info("Aucune œuvre disponible pour l'Atelier. Générez-en une via le 'Générateur de Texte' ou ajoutez-en manuellement dans Google Sheets.")


elif page == "Générateur de Tendances Marché":
    st.header("📈 Générateur de Tendances Marché : L'Oracle Prédit le Succès")
    st.write("Générez des données simulées pour la veille stratégique. Ces données rempliront l'onglet 'Tendances_Marche' de votre Google Sheet.")
    st.info("💡 **Performance :** L'opération de génération des tendances prend quelques secondes. Streamlit affichera un indicateur de chargement.")

    with st.form("generate_trends_form"):
        st.subheader("Paramètres de Simulation des Tendances :")
        num_entries = st.slider("Nombre d'entrées de tendance à générer :", min_value=1, max_value=10, value=3)
        start_date_obj = st.date_input("Date de début des tendances :", value=datetime.now() - timedelta(days=90))
        start_date_str = start_date_obj.strftime("%Y-%m-%d")

        overall_sentiment = st.selectbox("Sentiment général du marché :", ["En forte croissance", "En croissance modérée", "Stable", "En léger déclin", "En fort déclin"])
        dominant_genres_input = st.text_input("Genres dominants à prioriser (séparés par virgules) :", value="cyberpunk, fantasy érotique, romance historique")
        specific_kinks_input = st.text_input("Kinks/Thèmes spécifiques à inclure (séparés par virgules) :", value="bdsm, inceste, tabou, monstergirl")

        submitted_trends = st.form_submit_button("Générer & Sauvegarder les Tendances Marché")

        if submitted_trends:
            dominant_genres = [g.strip() for g in dominant_genres_input.split(',') if g.strip()]
            specific_kinks = [k.strip() for k in specific_kinks_input.split(',') if k.strip()]

            with st.spinner("L'Oracle génère les tendances du marché..."):
                generated_trends_data = gemini_oracle.generate_simulated_market_trends(
                    num_entries, start_date_str, overall_sentiment, dominant_genres, specific_kinks
                )

            if generated_trends_data:
                st.subheader("Tendances Générées :")
                st.dataframe(pd.DataFrame(generated_trends_data))

                if sheets_connector.append_rows_to_sheet(config.WORKSHEET_NAME_TENDANCES, generated_trends_data):
                    st.success("Tendances marché sauvegardées avec succès dans Google Sheets !")
                    sheets_connector.load_data_from_sheet.clear()
                else:
                    st.error("Échec de la sauvegarde des tendances marché dans Google Sheets.")
            else:
                st.warning("Aucune tendance marché générée. Veuillez ajuster les paramètres.")


elif page == "Générateur de Performances":
    st.header("📊 Générateur de Performances : L'Oracle Chiffre le Succès")
    st.write("Générez des données de performance mensuelle simulées pour vos œuvres. Ces données rempliront l'onglet 'Performance_Mensuelle' de votre Google Sheet.")
    st.info("💡 **Performance :** L'opération de génération des performances prend quelques secondes. Streamlit affichera un indicateur de chargement.")


    df_oeuvres = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)

    if df_oeuvres.empty:
        st.info("Aucune œuvre disponible pour générer des performances. Créez des œuvres d'abord.")
    else:
        oeuvre_ids_list = df_oeuvres['ID_Oeuvre'].tolist()
        oeuvre_titles_map = df_oeuvres.set_index('ID_Oeuvre')['Titre_Original'].to_dict()

        with st.form("generate_performance_form"):
            st.subheader("Paramètres de Simulation des Performances :")

            selected_oeuvres_for_perf_options = [f"{oid} - {oeuvre_titles_map.get(oid, 'Titre Inconnu')}" for oid in oeuvre_ids_list]
            selected_oeuvres_for_perf = st.multiselect(
                "Sélectionnez les œuvres pour lesquelles générer des performances :",
                options=selected_oeuvres_for_perf_options,
                default=selected_oeuvres_for_perf_options
            )
            selected_ids_for_perf = [s.split(' - ')[0] for s in selected_oeuvres_for_perf]

            num_months = st.slider("Nombre de mois à simuler :", min_value=1, max_value=12, value=3)
            start_month_year_obj = datetime.now().replace(day=1) - timedelta(days=90)
            start_month_year = st.date_input("Mois de début (performance) :", value=start_month_year_obj).strftime("%m-%Y")

            base_revenue_input = st.number_input("Revenu de base par mois et par œuvre (€) :", min_value=10.0, max_value=1000.0, value=50.0, step=10.0)
            growth_factor_input = st.slider("Facteur de croissance mensuelle (%) :", min_value=-5.0, max_value=10.0, value=2.0, step=0.5) / 100

            submitted_performance = st.form_submit_button("Générer & Sauvegarder les Performances")

            if submitted_performance:
                if not selected_ids_for_perf:
                    st.warning("Veuillez sélectionner au moins une œuvre pour générer des performances.")
                else:
                    with st.spinner("L'Oracle génère les données de performance..."):
                        generated_performance_data = gemini_oracle.generate_simulated_performance_data(
                            selected_ids_for_perf, num_months, start_month_year,
                            base_revenue=base_revenue_input, growth_factor=growth_factor_input
                        )

                    if generated_performance_data:
                        st.subheader("Performances Générées :")
                        st.dataframe(pd.DataFrame(generated_performance_data))

                        if sheets_connector.append_rows_to_sheet(config.WORKSHEET_NAME_PERFORMANCE, generated_performance_data):
                            st.success("Performances sauvegardées avec succès dans Google Sheets !")
                            sheets_connector.load_data_from_sheet.clear()
                        else:
                            st.error("Échec de la sauvegarde des performances dans Google Sheets.")
                    else:
                        st.warning("Aucune performance générée. Veuillez ajuster les paramètres.")


elif page == "Veille Stratégique":
    st.header("📊 Veille Stratégique : L'Oracle du Marché")
    st.write("Cette page affiche les tendances du marché, les mots-clés et les niches les plus populaires, basées sur vos données saisies ou générées.")

    df_tendances = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_TENDANCES)

    if not df_tendances.empty:
        st.subheader("Données Brutes des Tendances du Marché")
        st.dataframe(df_tendances)

        st.subheader("Tendances et Mots-clés Clés")

        if 'Popularite_Score' in df_tendances.columns and 'Niche_Identifiee' in df_tendances.columns and 'Competition_Niveau' in df_tendances.columns:
            df_tendances['Popularite_Score'] = pd.to_numeric(df_tendances['Popularite_Score'], errors='coerce').fillna(0)
            chart_niches = alt.Chart(df_tendances).mark_bar().encode(
                x=alt.X('Niche_Identifiee', sort='-y', title='Niche Identifiée'),
                y=alt.Y('Popularite_Score', title='Score de Popularité'),
                color=alt.Color('Competition_Niveau', title='Niveau de Compétition'),
                tooltip=['Niche_Identifiee', 'Popularite_Score', 'Competition_Niveau']
            ).properties(
                    title='Popularité des Niches par Niveau de Compétition'
            ).interactive()
            st.altair_chart(chart_niches, use_container_width=True)

            st.write("Top 3 des Niches par Popularité :")
            top_niches = df_tendances.sort_values(by='Popularite_Score', ascending=False).head(3)
            st.dataframe(top_niches[['Niche_Identifiee', 'Popularite_Score', 'Competition_Niveau']])

        if 'Mots_Cles_Associes' in df_tendances.columns:
            all_keywords = df_tendances['Mots_Cles_Associes'].dropna().str.split(', ').explode()
            if not all_keywords.empty:
                st.write("Mots-clés les plus fréquents :")
                keyword_counts = all_keywords.value_counts().reset_index()
                keyword_counts.columns = ['Keyword', 'Count']
                chart_keywords = alt.Chart(keyword_counts.head(10)).mark_bar().encode(
                    x=alt.X('Count', title='Fréquence'),
                    y=alt.Y('Keyword', sort='-x', title='Mot-clé'),
                    tooltip=['Keyword', 'Count']
                ).properties(
                    title='Top 10 des Mots-clés les Plus Fréquents'
                ).interactive()
                st.altair_chart(chart_keywords, use_container_width=True)
                st.dataframe(keyword_counts.head(10))
            else:
                st.info("Aucun mot-clé associé trouvé.")

        insights = []
        if 'Popularite_Score' in df_tendances.columns and 'Niche_Identifiee' in df_tendances.columns:
            top_niches_data = df_tendances.sort_values(by='Popularite_Score', ascending=False).head(1)
            if not top_niches_data.empty:
                insights.append(f"La niche la plus populaire est **{top_niches_data.iloc[0]['Niche_Identifiee']}** (Score: {top_niches_data.iloc[0]['Popularite_Score']}).")

        if 'Mots_Cles_Associes' in df_tendances.columns:
            all_keywords = df_tendances['Mots_Cles_Associes'].dropna().str.split(', ').explode()
            if not all_keywords.empty:
                trending_keywords = all_keywords.value_counts().head(3).index.tolist()
                insights.append(f"Les mots-clés en vogue sont : **{', '.join(trending_keywords)}**.")

        if insights:
            st.markdown(f"#### Conseil de l'Oracle :")
            for insight in insights:
                st.write(f"- {insight}")
        else:
            st.info("Pas assez de données pour générer des conseils de l'Oracle.")


    else:
        st.info("Pas de données à afficher pour la veille stratégique. Veuillez alimenter l'onglet 'Tendances_Marche' dans Google Sheets ou utiliser le 'Générateur de Tendances Marché'.")


elif page == "Portfolio & Performance":
    st.header("📈 Portfolio & Performance : Vos triomphes chiffrés")
    st.write("Suivez les performances de chaque œuvre et identifiez vos blockbusters, basés sur vos données saisies ou générées.")

    df_performance = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_PERFORMANCE)
    df_oeuvres = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)

    if not df_performance.empty:
        st.subheader("Performances Mensuelles Détaillées")

        df_performance_sorted = df_performance.sort_values(by=['Mois_Annee', 'ID_Oeuvre'], ascending=[True, True])
        st.dataframe(df_performance_sorted)

        if 'Revenus_Nets' in df_performance_sorted.columns:
            df_performance_sorted['Revenus_Nets'] = pd.to_numeric(df_performance_sorted['Revenus_Nets'], errors='coerce').fillna(0)
            total_revenus = df_performance_sorted['Revenus_Nets'].sum()
            st.metric(label="Revenus Nets Totaux Affichés", value=f"{total_revenus:,.2f} €")

            st.subheader("Graphique des Revenus Mensuels")
            if 'Mois_Annee' in df_performance_sorted.columns:
                df_performance_sorted['Mois_Annee'] = pd.to_datetime(df_performance_sorted['Mois_Annee'], errors='coerce')
                df_performance_agg = df_performance_sorted.dropna(subset=['Mois_Annee']).groupby('Mois_Annee')['Revenus_Nets'].sum().reset_index()
                chart_revenues = alt.Chart(df_performance_agg).mark_line(point=True).encode(
                    x=alt.X('Mois_Annee', title='Mois et Année', axis=alt.Axis(format="%b %Y")),
                    y=alt.Y('Revenus_Nets', title='Revenus Nets (€)'),
                    tooltip=[alt.Tooltip('Mois_Annee', format="%Y-%m"), 'Revenus_Nets']
                ).properties(
                    title='Revenus Nets Mensuels'
                ).interactive()
                st.altair_chart(chart_revenues, use_container_width=True)
            else:
                st.info("Colonne 'Mois_Annee' manquante ou invalide pour le graphique.")
        else:
            st.info("Colonne 'Revenus_Nets' manquante dans 'Performance_Mensuelle'.")

        if 'ID_Oeuvre' in df_performance_sorted.columns and 'Revenus_Nets' in df_performance_sorted.columns:
            st.subheader("Performance Cumulée par Œuvre")
            revenus_par_oeuvre = df_performance_sorted.groupby('ID_Oeuvre')['Revenus_Nets'].sum().sort_values(ascending=False).reset_index()

            if not df_oeuvres.empty:
                merged_df = pd.merge(revenus_par_oeuvre, df_oeuvres[['ID_Oeuvre', 'Titre_Original', 'Titre_Optimise']], on='ID_Oeuvre', how='left')
                merged_df['Titre_Display'] = merged_df['Titre_Optimise'].fillna(merged_df['Titre_Original']).fillna(merged_df['ID_Oeuvre'])
                st.dataframe(merged_df[['Titre_Display', 'Revenus_Nets']].rename(columns={'Revenus_Nets': 'Revenus Totaux'}).head(10))

                chart_top_oeuvres = alt.Chart(merged_df.head(10)).mark_bar().encode(
                    x=alt.X('Revenus_Nets', title='Revenus Totaux (€)'),
                    y=alt.Y('Titre_Display', sort='-x', title='Œuvre'),
                    tooltip=['Titre_Display', 'Revenus_Nets']
                ).properties(
                    title='Top 10 des Œuvres par Revenus'
                ).interactive()
                st.altair_chart(chart_top_oeuvres, use_container_width=True)

            else:
                st.warning("Impossible de lier les performances aux titres des œuvres (Onglet 'Oeuvres' vide ou introuvable).")
                st.dataframe(revenus_par_oeuvre)
        else:
            st.info("Colonnes 'ID_Oeuvre' ou 'Revenus_Nets' manquantes pour l'analyse par œuvre.")

    else:
        st.info("Pas de données de performance. Veuillez alimenter l'onglet 'Performance_Mensuelle' dans Google Sheets ou utiliser le 'Générateur de Performances'.")


elif page == "Finances du Cartel":
    st.header("💰 Finances du Cartel : Vue d'ensemble de votre empire")
    st.write("Visualisez vos revenus globaux et la croissance de votre micro-empire, basés sur vos données saisies ou générées.")

    df_performance = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_PERFORMANCE)

    if not df_performance.empty:
        if 'Revenus_Nets' in df_performance.columns:
            df_performance['Revenus_Nets'] = pd.to_numeric(df_performance['Revenus_Nets'], errors='coerce').fillna(0)
            total_revenus_globaux = df_performance['Revenus_Nets'].sum()
            st.metric(label="Revenus Nets Cumulés de toutes les œuvres", value=f"{total_revenus_globaux:,.2f} €")

            st.subheader("Croissance des Revenus Mensuels")
            if 'Mois_Annee' in df_performance.columns:
                df_performance['Mois_Annee'] = pd.to_datetime(df_performance['Mois_Annee'], errors='coerce')
                df_performance_agg = df_performance.dropna(subset=['Mois_Annee']).groupby('Mois_Annee')['Revenus_Nets'].sum().reset_index()
                chart_global_revenues = alt.Chart(df_performance_agg).mark_line(point=True).encode(
                    x=alt.X('Mois_Annee', title='Mois et Année', axis=alt.Axis(format="%b %Y")),
                    y=alt.Y('Revenus_Nets', title='Revenus Nets Mensuels (€)'),
                    tooltip=[alt.Tooltip('Mois_Annee', format="%Y-%m"), 'Revenus_Nets']
                ).properties(
                    title='Croissance des Revenus Nets Mensuels'
                ).interactive()
                st.altair_chart(chart_global_revenues, use_container_width=True)
            else:
                st.info("Colonne 'Mois_Annee' manquante ou invalide pour les tendances mensuelles.")

        else:
            st.info("Colonne 'Revenus_Nets' manquante dans 'Performance_Mensuelle'.")
    else:
        st.info("Pas de données financières à afficher. Veuillez alimenter l'onglet 'Performance_Mensuelle' dans Google Sheets ou utiliser le 'Générateur de Performances'.")

elif page == "Directive Stratégique de l'Oracle":
    st.header("🔮 Directive Stratégique de l'Oracle : Votre Plan d'Action")
    st.write("Demandez à l'Oracle de synthétiser les données du marché et de performance pour vous fournir une stratégie d'action.")
    st.info("💡 **Performance :** La génération de la directive peut prendre quelques secondes. Streamlit affichera un indicateur de chargement.")


    df_tendances = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_TENDANCES)
    df_performance = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_PERFORMANCE)
    df_oeuvres_for_strategy = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)

    with st.form("strategic_directive_form"):
        st.subheader("Votre Objectif Stratégique :")
        creative_goal = st.text_area(
            "Décrivez votre objectif principal pour le Cartel des Plaisirs (ex: 'Maximiser les revenus du prochain trimestre en explorant de nouvelles niches', 'Construire une marque forte autour de la fantasy érotique', 'Tester de nouveaux formats de contenu').",
            height=100
        )

        st.subheader("Données à Considérer :")
        col_data_options_1, col_data_options_2 = st.columns(2)
        with col_data_options_1:
            use_trends = st.checkbox("Inclure les données de Tendances Marché", value=True)
            if not df_tendances.empty:
                st.info(f"{len(df_tendances)} entrées de tendances disponibles.")
            else:
                st.warning("Aucune donnée de tendances marché disponible. Générez-en via 'Générateur de Tendances Marché'.")
        with col_data_options_2:
            use_performance = st.checkbox("Inclure les données de Performance (Revenus)", value=True)
            if not df_performance.empty:
                st.info(f"{len(df_performance)} entrées de performance disponibles.")
            else:
                st.warning("Aucune donnée de performance disponible. Générez-en via 'Générateur de Performances'.")

        submitted_directive = st.form_submit_button("Générer la Directive Stratégique")

    if submitted_directive:
        if not creative_goal.strip():
            st.warning("Veuillez définir votre objectif stratégique avant de générer une directive.")
        else:
            trends_data_for_oracle = df_tendances if use_trends else pd.DataFrame()

            performance_data_for_oracle = df_performance.copy() if use_performance else pd.DataFrame()
            if use_performance and not performance_data_for_oracle.empty and not df_oeuvres_for_strategy.empty:
                performance_data_for_oracle['Mois_Annee'] = pd.to_datetime(performance_data_for_oracle['Mois_Annee'], format='%m-%Y', errors='coerce')

                performance_data_for_oracle = pd.merge(
                    performance_data_for_oracle,
                    df_oeuvres_for_strategy[['ID_Oeuvre', 'Titre_Original', 'Titre_Optimise']],
                    on='ID_Oeuvre', how='left'
                )
                performance_data_for_oracle['Titre_Display'] = performance_data_for_oracle['Titre_Optimise'].fillna(performance_data_for_oracle['Titre_Original']).fillna(performance_data_for_oracle['ID_Oeuvre'])
                performance_data_for_oracle = performance_data_for_oracle[['ID_Oeuvre', 'Titre_Display', 'Mois_Annee', 'Revenus_Nets', 'Engagement_Score']]
            elif use_performance and (performance_data_for_oracle.empty or df_oeuvres_for_strategy.empty):
                st.info("Les données de performance ne pourront pas être liées aux titres des œuvres pour la directive (Données manquantes).")
            else:
                performance_data_for_oracle = pd.DataFrame()


            with st.spinner("L'Oracle analyse et formule votre directive stratégique..."):
                directive_generated = gemini_oracle.generate_strategic_directive(
                    creative_goal,
                    trends_data_for_oracle,
                    performance_data_for_oracle
                )
            st.session_state.last_directive_text = directive_generated

    if st.session_state.last_directive_text and st.session_state.last_directive_text.strip() != "":
        st.markdown("---")
        st.subheader("La Directive de l'Oracle :")
        st.markdown(st.session_state.last_directive_text)

        if st.button("Appliquer cette Stratégie à la Génération de Récits"):
            with st.spinner("L'Oracle extrait les paramètres narratifs de la directive..."):
                narrative_params = gemini_oracle.parse_strategic_directive_for_narrative_params(st.session_state.last_directive_text)

            if narrative_params:
                st.session_state.generated_narrative_params = narrative_params
                if narrative_params.get("objective_text_generation_suite", False):
                    st.session_state.redirect_to_page = "Générateur de Suite"
                else:
                    st.session_state.redirect_to_page = "Générateur de Texte (Standalone)"

                st.success(f"Paramètres extraits ! Redirection vers le '{st.session_state.redirect_to_page}' pour lancer la création.")
                st.rerun()
            else:
                st.warning("L'Oracle n'a pas pu extraire de paramètres narratifs clairs de la directive. Veuillez ajuster la directive ou saisir manuellement les paramètres.")

elif page == "Gestion des Univers & Personnages":
    st.header("🌌 Gestion des Univers & Personnages : La Mémoire de l'Oracle")
    st.write("Créez, visualisez et mettez à jour les détails de vos univers et personnages pour une cohérence narrative accrue.")

    df_univers = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_UNIVERS)

    st.subheader("Vos Univers Enregistrés")
    if not df_univers.empty:
        st.dataframe(df_univers[['ID_Univers', 'Nom_Univers', 'Description_Globale']].head(10))

        selected_universe_to_edit_str = st.selectbox(
            "Sélectionnez un univers à éditer :",
            [''] + [f"{row['ID_Univers']} - {row['Nom_Univers']}" for _, row in df_univers.iterrows()],
            key="edit_universe_select"
        )

        selected_universe_data_to_edit = {}
        if selected_universe_to_edit_str:
            universe_id_to_edit = selected_universe_to_edit_str.split(' - ')[0]
            if not df_univers.empty and universe_id_to_edit in df_univers['ID_Univers'].tolist():
                selected_universe_data_to_edit = df_univers[df_univers['ID_Univers'] == universe_id_to_edit].iloc[0].to_dict()
                st.session_state.current_universe_id_for_edit = universe_id_to_edit
            else:
                st.error(f"Erreur: L'univers avec l'ID '{universe_id_to_edit}' n'a pas été trouvé dans les données chargées. Veuillez sélectionner à nouveau ou créer un nouvel univers.")
                st.session_state.current_universe_id_for_edit = None
        else:
            st.session_state.current_universe_id_for_edit = None
    else:
        st.info("Aucun univers enregistré. Créez-en un nouveau ci-dessous.")
        selected_universe_to_edit_str = ""


    st.markdown("---")

    current_universe_details = {}
    if st.session_state.current_universe_id_for_edit:
        st.subheader(f"Éditer l'Univers : {selected_universe_data_to_edit.get('Nom_Univers', 'N/A')}")
        current_id_univers = st.session_state.current_universe_id_for_edit
        current_universe_details = selected_universe_data_to_edit
    else:
        st.subheader("Créer un Nouvel Univers")
        current_id_univers = f"UNI_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    st.subheader("Extraire les détails d'un texte existant (via l'Oracle)")
    df_oeuvres_for_extraction = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_OEUVRES)

    if not df_oeuvres_for_extraction.empty:
        oeuvre_for_extraction_options = [''] + [f"{row['ID_Oeuvre']} - {row['Titre_Original']}" for _, row in df_oeuvres_for_extraction.iterrows()]
        selected_oeuvre_for_extract_str = st.selectbox(
            "Sélectionnez une œuvre pour extraire les détails d'univers/personnages :",
            oeuvre_for_extraction_options, key="oeuvre_extract_select_outside_form_unique"
        )
        if selected_oeuvre_for_extract_str:
            oeuvre_id_to_extract = selected_oeuvre_for_extract_str.split(' - ')[0]
            if oeuvre_id_to_extract in df_oeuvres_for_extraction['ID_Oeuvre'].tolist():
                oeuvre_to_extract_data = df_oeuvres_for_extraction[df_oeuvres_for_extraction['ID_Oeuvre'] == oeuvre_id_to_extract].iloc[0]

                full_text_to_analyze = oeuvre_to_extract_data.get('Texte_Genere', '')
                if not full_text_to_analyze and oeuvre_to_extract_data.get('URL_Texte_Local'):
                    local_text_path = os.path.join(os.path.dirname(__file__), oeuvre_to_extract_data['URL_Texte_Local'])
                    if os.path.exists(local_text_path):
                        with open(local_text_path, 'r', encoding='utf-8') as f:
                            full_text_to_analyze = f.read()

                if full_text_to_analyze.strip():
                    if st.button("Extraire les Détails par l'Oracle (remplira les champs ci-dessous)", key="extract_details_button_outside_form_unique"):
                        with st.spinner("L'Oracle analyse le texte pour extraire les détails d'univers et de personnages..."):
                            extracted_plot = gemini_oracle.summarize_plot(full_text_to_analyze)
                            extracted_characters = gemini_oracle.extract_character_details(full_text_to_analyze)
                        st.session_state.extracted_plot_for_universe = extracted_plot
                        st.session_state.extracted_characters_for_universe = extracted_characters
                        st.info("Détails extraits ! Ils apparaîtront dans les champs ci-dessous. Cliquez sur 'Sauvegarder l'Univers' pour enregistrer.")
                        st.rerun()
                else:
                    st.warning("Texte de l'œuvre sélectionnée vide. Impossible d'extraire des détails.")
            else:
                st.warning(f"L'ID d'œuvre '{oeuvre_id_to_extract}' n'a pas été trouvé. Veuillez sélectionner une œuvre valide.")
        else:
            st.info("Sélectionnez une œuvre avec du texte pour extraire des détails.")
    else:
        st.info("Aucune œuvre disponible pour l'extraction de détails. Générez-en via le 'Générateur de Texte'.")

    st.markdown("---")

    with st.form("universe_edit_form", clear_on_submit=False):
        st.write(f"ID Univers : `{current_id_univers}`")

        default_plot_value = st.session_state.extracted_plot_for_universe if st.session_state.extracted_plot_for_universe else current_universe_details.get('Elements_Cles_Intrigue', '')
        default_chars_value = st.session_state.extracted_characters_for_universe if st.session_state.extracted_characters_for_universe else current_universe_details.get('Personnages_Cles', '')

        new_nom_univers = st.text_input("Nom de l'Univers :", value=current_universe_details.get('Nom_Univers', ''), key="uni_name")
        new_description_globale = st.text_area("Description Globale de l'Univers :", value=current_universe_details.get('Description_Globale', ''), height=150, key="uni_desc")
        new_elements_cles_intrigue = st.text_area("Éléments Clés de l'Intrigue/Historique de l'Univers :", value=default_plot_value, height=150, key="uni_plot")
        new_personnages_cles = st.text_area("Détails sur les Personnages Clés (Noms, Traits, Relations) :", value=default_chars_value, height=150, key="uni_chars")
        new_notes_internes = st.text_area("Notes Internes :", value=current_universe_details.get('Notes_Internes', ''), height=100, key="uni_notes")

        submitted_universe = st.form_submit_button("Sauvegarder l'Univers")

        if submitted_universe:
            st.session_state.extracted_plot_for_universe = ""
            st.session_state.extracted_characters_for_universe = ""

            updates = {
                'ID_Univers': current_id_univers,
                'Nom_Univers': st.session_state.uni_name,
                'Description_Globale': st.session_state.uni_desc,
                'Elements_Cles_Intrigue': st.session_state.uni_plot,
                'Personnages_Cles': st.session_state.uni_chars,
                'Notes_Internes': st.session_state.uni_notes
            }

            if st.session_state.current_universe_id_for_edit:
                if sheets_connector.update_row_by_id(config.WORKSHEET_NAME_UNIVERS, 'ID_Univers', current_id_univers, updates):
                    st.success(f"Univers '{st.session_state.uni_name}' mis à jour avec succès !")
                else:
                    st.error(f"Échec de la mise à jour de l'univers '{st.session_state.uni_name}'.")
            else:
                if sheets_connector.append_rows_to_sheet(config.WORKSHEET_NAME_UNIVERS, [updates]):
                    st.success(f"Nouvel univers '{st.session_state.uni_name}' créé avec succès !")

            st.session_state.current_universe_id_for_edit = None
            sheets_connector.load_data_from_sheet.clear()
            st.rerun()

    st.markdown("---")
    st.subheader("Supprimer un Univers Existant")
    if not df_univers.empty:
        delete_universe_options = [''] + [f"{row['ID_Univers']} - {row['Nom_Univers']}" for _, row in df_univers.iterrows()]
        selected_universe_to_delete_str = st.selectbox(
            "Sélectionnez un univers à supprimer :",
            delete_universe_options, key="delete_universe_select"
        )
        if selected_universe_to_delete_str:
            universe_id_to_delete = selected_universe_to_delete_str.split(' - ')[0]
            if st.button(f"Supprimer l'Univers '{universe_id_to_delete}'", key="delete_universe_btn"):
                show_confirm_modal(universe_id_to_delete, "universe")
    else:
        st.info("Aucun univers à supprimer.")

elif page == "Gestion des Styles d'Écriture":
    st.header("🎨 Gestion des Styles d'Écriture : La Voix de l'Oracle")
    st.write("Créez, visualisez et éditez les styles narratifs que l'Oracle pourra émuler dans vos récits.")

    df_styles = sheets_connector.load_data_from_sheet(config.WORKSHEET_NAME_STYLES)

    st.subheader("Vos Styles Enregistrés")
    if not df_styles.empty:
        st.dataframe(df_styles[['ID_Style', 'Nom_Style', 'Niveau_Explicite_Defaut', 'Description_Style']].head(10))

        selected_style_to_edit_str = st.selectbox(
            "Sélectionnez un style à éditer :",
            [''] + [f"{row['ID_Style']} - {row['Nom_Style']}" for _, row in df_styles.iterrows()],
            key="edit_style_select"
        )

        selected_style_data_to_edit = {}
        if selected_style_to_edit_str:
            style_id_to_edit = selected_style_to_edit_str.split(' - ')[0]
            if not df_styles.empty and style_id_to_edit in df_styles['ID_Style'].tolist():
                selected_style_data_to_edit = df_styles[df_styles['ID_Style'] == style_id_to_edit].iloc[0].to_dict()
                st.session_state.current_style_id_for_edit = style_id_to_edit
            else:
                st.error(f"Erreur: Le style avec l'ID '{style_id_to_edit}' n'a pas été trouvé dans les données chargées. Veuillez sélectionner à nouveau ou créer un nouveau style.")
                st.session_state.current_style_id_for_edit = None
        else:
            st.session_state.current_style_id_for_edit = None
    else:
        st.info("Aucun style enregistré. Créez-en un nouveau ci-dessous.")
        selected_style_to_edit_str = ""


    st.markdown("---")

    current_style_details = {}
    if st.session_state.current_style_id_for_edit:
        st.subheader(f"Éditer le Style : {selected_style_data_to_edit.get('Nom_Style', 'N/A')}")
        current_id_style = st.session_state.current_style_id_for_edit
        current_style_details = selected_style_data_to_edit
    else:
        st.subheader("Créer un Nouveau Style")
        current_id_style = f"STYLE_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    with st.form("style_edit_form", clear_on_submit=False):
        st.write(f"ID Style : `{current_id_style}`")

        new_nom_style = st.text_input("Nom du Style :", value=current_style_details.get('Nom_Style', ''), key="style_name")
        new_description_style = st.text_area("Description Détaillée du Style (pour l'IA) :", value=current_style_details.get('Description_Style', ''), height=200, key="style_desc")
        new_exemples_textuels = st.text_area("Exemples Textuels (facultatif) :", value=current_style_details.get('Exemples_Textuels', ''), height=100, key="style_examples")

        spiciness_options_for_style = ["", "doux", "modéré", "explicite"]
        default_spiciness_style = current_style_details.get('Niveau_Explicite_Defaut', '')
        try:
            spiciness_index_for_style = spiciness_options_for_style.index(default_spiciness_style)
        except ValueError:
            spiciness_index_for_style = 0
        new_niveau_explicite_defaut = st.selectbox("Niveau de Sensualité par Défaut :", spiciness_options_for_style, index=spiciness_index_for_style, key="style_spiciness_default")

        new_notes_internes = st.text_area("Notes Internes :", value=current_style_details.get('Notes_Internes', ''), height=100, key="style_notes")

        submitted_style = st.form_submit_button("Sauvegarder le Style")

        if submitted_style:
            updates = {
                'ID_Style': current_id_style,
                'Nom_Style': st.session_state.style_name,
                'Description_Style': st.session_state.style_desc,
                'Exemples_Textuels': st.session_state.style_examples,
                'Niveau_Explicite_Defaut': st.session_state.style_spiciness_default,
                'Notes_Internes': st.session_state.style_notes
            }

            if st.session_state.current_style_id_for_edit:
                if sheets_connector.update_row_by_id(config.WORKSHEET_NAME_STYLES, 'ID_Style', current_id_style, updates):
                    st.success(f"Style '{st.session_state.style_name}' mis à jour avec succès !")
                else:
                    st.error(f"Échec de la mise à jour du style '{st.session_state.style_name}'.")
            else:
                if sheets_connector.append_rows_to_sheet(config.WORKSHEET_NAME_STYLES, [updates]):
                    st.success(f"Nouveau style '{st.session_state.style_name}' créé avec succès !")

            st.session_state.current_style_id_for_edit = None
            sheets_connector.load_data_from_sheet.clear()
            st.rerun()

    st.markdown("---")
    st.subheader("Supprimer un Style Existant")
    if not df_styles.empty:
        delete_style_options = [''] + [f"{row['ID_Style']} - {row['Nom_Style']}" for _, row in df_styles.iterrows()]
        selected_style_to_delete_str = st.selectbox(
            "Sélectionnez un style à supprimer :",
            delete_style_options, key="delete_style_select"
        )
        if selected_style_to_delete_str:
            style_id_to_delete = selected_style_to_delete_str.split(' - ')[0]
            if st.button(f"Supprimer le Style '{style_id_to_delete}'", key="delete_style_btn"):
                show_confirm_modal(style_id_to_delete, "style")
    else:
        st.info("Aucun style à supprimer.")


st.markdown("---")
st.caption(f"© {datetime.now().year} CARTEL DES PLAISIRS - Propulsé par l'Oracle et la détermination du Gardien.")