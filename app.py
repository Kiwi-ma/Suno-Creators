# app.py

import streamlit as st
import os
import pandas as pd
from datetime import datetime
import base64

# Importation de nos modules personnalisés
from config import (
    SHEET_NAME, WORKSHEET_NAMES, ASSETS_DIR, AUDIO_CLIPS_DIR, SONG_COVERS_DIR, ALBUM_COVERS_DIR, GENERATED_TEXTS_DIR
)
import sheets_connector as sc
import gemini_oracle as go
import utils as ut

# --- Configuration Générale de l'Application Streamlit ---
st.set_page_config(
    page_title="L'ARCHITECTE Ω - Micro-Empire Musical IA",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Initialisation de st.session_state ---
# Un dictionnaire central pour gérer l'état de l'application
if 'app_initialized' not in st.session_state:
    st.session_state['app_initialized'] = True
    st.session_state['current_page'] = 'Accueil'
    st.session_state['user_id'] = 'Gardien' # Peut être étendu pour des profils utilisateur
    st.session_state['theme_mode'] = 'light' # Ou 'dark', si tu veux un toggle plus tard
    st.session_state['selected_morceau_id'] = None # Pour le lecteur audio et les détails du morceau

# --- Vérification et Création des Dossiers d'Assets ---
for directory in [ASSETS_DIR, AUDIO_CLIPS_DIR, SONG_COVERS_DIR, ALBUM_COVERS_DIR, GENERATED_TEXTS_DIR]:
    os.makedirs(directory, exist_ok=True)
    # st.sidebar.write(f"Dossier {directory} vérifié.") # Décommenter pour debug si besoin


# --- Fonctions Utilitaires d'Affichage (peut être déplacé dans utils.py à terme si elles grossissent) ---
def display_dataframe(df: pd.DataFrame, title: str = "", key: str = ""):
    """Affiche un DataFrame avec un titre et un key unique pour Streamlit."""
    if title:
        st.subheader(title)
    if not df.empty:
        st.dataframe(df, use_container_width=True, key=key)
    else:
        st.info("Aucune donnée à afficher pour le moment.")

def get_base64_image(image_path: str):
    """Encode une image en base64 pour l'intégration directe dans Streamlit (si besoin) ou CSS."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def set_background_image(image_path: str):
    """Définit une image de fond pour l'application Streamlit."""
    bin_img = get_base64_image(image_path)
    if bin_img:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{bin_img}");
                background-size: cover;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# Tu peux choisir une image de fond par défaut ici si tu en as une.
# Par exemple, une image générique de synthwave ou de paysage cosmique.
# set_background_image(os.path.join(ASSETS_DIR, "background_default.jpg")) # Décommenter et adapter

# --- Menu de Navigation Latéral ---
st.sidebar.title("ARCHITECTE Ω - Menu")

menu_options = {
    "Accueil": "🏠 Vue d'ensemble de l'empire.",
    "Création Musicale IA": {
        "Générateur de Contenu": "✍️ Paroles, Prompts Audio, Titres...",
        "Co-pilote Créatif": "💡 Idées en temps réel (Beta)",
        "Création Multimodale": "🎬 Audio, Visuel, Paroles (Synchronisé)"
    },
    "Gestion du Sanctuaire": {
        "Mes Morceaux": "🎶 Gérer les créations musicales",
        "Mes Albums": "💿 Gérer les collections",
        "Mes Artistes IA": "🤖 Gérer les identités IA",
        "Paroles Existantes": "📜 Consulter mes paroles manuelles"
    },
    "Analyse & Stratégie": {
        "Stats & Tendances Sim.": "📊 Analyser les performances virtuelles",
        "Directives Stratégiques": "🎯 Conseils de l'Oracle",
        "Potentiel Viral & Niches": "📈 Détecter les opportunités"
    },
    "Bibliothèques de l'Oracle": {
        "Styles Musicaux": "🎸 Explorer les genres",
        "Styles Lyriques": "📝 Définir les écritures",
        "Thèmes & Concepts": "🌌 Naviguer les idées",
        "Moods & Émotions": "❤️ Préciser les ressentis",
        "Instruments & Voix": "🎤 Palette sonore",
        "Structures de Chanson": "🏛️ Modèles de composition",
        "Règles de Génération": "⚖️ Contrôler l'IA"
    },
    "Outils & Projets": {
        "Projets en Cours": "🚧 Suivi de production",
        "Outils IA Référencés": "🛠️ Boîte à outils IA",
        "Timeline Événements": "🗓️ Planification des lancements"
    },
    "Historique de l'Oracle": "📚 Traces de nos interactions"
}

# Fonction pour afficher les options du menu
def display_menu(options_dict, parent_key=""):
    for key, value in options_dict.items():
        full_key = f"{parent_key}_{key}" if parent_key else key
        if isinstance(value, dict):
            with st.sidebar.expander(key):
                display_menu(value, full_key)
        else:
            if st.sidebar.button(f"{value} {key}", key=f"menu_button_{full_key}"):
                st.session_state['current_page'] = key

# Affichage dynamique du menu
display_menu(menu_options)

# --- Contenu principal de la page (sera rempli dans les prochaines sections) ---
st.title(f"Page : {st.session_state['current_page']}")

# Cette section est un placeholder. Le contenu réel sera ajouté après.
if st.session_state['current_page'] == 'Accueil':
    st.write("Bienvenue dans votre Quartier Général de Micro-Empire Numérique Musical IA. Utilisez le menu latéral pour naviguer.")
    st.info("Pensez à bien configurer vos dossiers d'assets et vos secrets dans `.streamlit/secrets.toml`!") 

# app.py - Suite du code

# --- Page : Générateur de Contenu (Création Musicale IA) ---
if st.session_state['current_page'] == 'Générateur de Contenu':
    st.header("✍️ Générateur de Contenu Musical par l'Oracle")
    st.write("Utilisez cette interface pour demander à l'Oracle de générer des paroles, des prompts audio, des titres, des descriptions marketing et des prompts visuels pour vos pochettes d'album.")

    content_type = st.radio(
        "Quel type de contenu souhaitez-vous générer ?",
        ["Paroles de Chanson", "Prompt Audio (pour SUNO)", "Idées de Titres", "Description Marketing", "Prompt Pochette d'Album"],
        key="content_type_radio"
    )

    st.markdown("---") # Séparateur visuel

    # --- Formulaire de Génération de Paroles ---
    if content_type == "Paroles de Chanson":
        st.subheader("Générer des Paroles de Chanson")
        with st.form("lyrics_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Genre Musical", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="lyrics_genre_musical")
                st.selectbox("Mood Principal", sc.get_all_moods()['ID_Mood'].tolist(), key="lyrics_mood_principal")
                st.selectbox("Thème Principal Lyrique", sc.get_all_themes()['ID_Theme'].tolist(), key="lyrics_theme_lyrique_principal")
                st.selectbox("Style Lyrique", sc.get_all_styles_lyriques()['ID_Style_Lyrique'].tolist(), key="lyrics_style_lyrique")
                st.text_input("Mots-clés de Génération (séparés par des virgules)", key="lyrics_mots_cles_generation")
            with col2:
                st.selectbox("Structure de Chanson", sc.get_all_structures_song()['ID_Structure'].tolist(), key="lyrics_structure_chanson")
                st.selectbox("Langue des Paroles", ["Français", "Anglais", "Espagnol"], key="lyrics_langue_paroles")
                st.selectbox("Niveau de Langage", ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], key="lyrics_niveau_langage_paroles")
                st.selectbox("Imagerie Texte", ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], key="lyrics_imagerie_texte")
               
                # --- Intégration de Modèles "Empathiques" (pour les Moods) ---
                if st.session_state.get('lyrics_mood_principal'):
                    if st.button("Affiner le Mood avec l'Oracle 🧠", key="refine_mood_button"):
                        with st.spinner("L'Oracle affine le mood..."):
                            mood_questions = go.refine_mood_with_questions(st.session_state.lyrics_mood_principal)
                            st.session_state['mood_refinement_questions'] = mood_questions
                    if 'mood_refinement_questions' in st.session_state and st.session_state.mood_refinement_questions:
                        st.info("Voici les questions de l'Oracle pour affiner votre mood :\n" + st.session_state.mood_refinement_questions)
                        st.text_area("Vos réponses / Affinement du mood (optionnel)", key="lyrics_mood_refinement_response")


            submit_lyrics_button = st.form_submit_button("Générer les Paroles")

            if submit_lyrics_button:
                with st.spinner("L'Oracle compose les paroles..."):
                    generated_lyrics = go.generate_song_lyrics(
                        genre_musical=st.session_state.lyrics_genre_musical,
                        mood_principal=st.session_state.lyrics_mood_principal,
                        theme_lyrique_principal=st.session_state.lyrics_theme_lyrique_principal,
                        style_lyrique=st.session_state.lyrics_style_lyrique,
                        mots_cles_generation=st.session_state.lyrics_mots_cles_generation,
                        structure_chanSONG=st.session_state.lyrics_structure_chanson,
                        langue_paroles=st.session_state.lyrics_langue_paroles,
                        niveau_langage_paroles=st.session_state.lyrics_niveau_langage_paroles,
                        imagerie_texte=st.session_state.lyrics_imagerie_texte
                    )
                    st.session_state['generated_lyrics'] = generated_lyrics
                    st.success("Paroles générées avec succès !")

        if 'generated_lyrics' in st.session_state and st.session_state.generated_lyrics:
            st.markdown("---")
            st.subheader("Paroles Générées")
            st.text_area("Copiez les paroles ici :", st.session_state.generated_lyrics, height=400, key="displayed_generated_lyrics")
           
            # Option de sauvegarde des paroles
            save_lyrics_option = st.radio(
                "Où souhaitez-vous sauvegarder ces paroles ?",
                ["Ne pas sauvegarder", "Dans un nouveau Morceau (Google Sheet)", "Dans un Morceau Existant (Google Sheet)", "Dans un fichier local"],
                key="save_lyrics_option"
            )

            if save_lyrics_option == "Dans un nouveau Morceau (Google Sheet)":
                with st.form("save_new_morceau_lyrics_form"):
                    st.info("Ces paroles seront ajoutées à un nouveau morceau dans l'onglet `MORCEAUX_GENERES`.")
                    # Pré-remplir certains champs avec les paramètres de génération
                    new_morceau_title = st.text_input("Titre du nouveau morceau", value=f"Nouveau Morceau - {st.session_state.lyrics_genre_musical}", key="new_morceau_lyrics_title")
                    new_morceau_artist_ia = st.selectbox("Artiste IA Associé", [""] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist(), key="new_morceau_lyrics_artist_ia")
                   
                    save_button = st.form_submit_button("Sauvegarder le nouveau Morceau")
                    if save_button:
                        morceau_data = {
                            'Titre_Morceau': new_morceau_title,
                            'Statut_Production': 'Paroles Générées',
                            'Prompt_Generation_Paroles': st.session_state.generated_lyrics,
                            'ID_Style_Musical_Principal': st.session_state.lyrics_genre_musical,
                            'ID_Style_Lyrique_Principal': st.session_state.lyrics_style_lyrique,
                            'Theme_Principal_Lyrique': st.session_state.lyrics_theme_lyrique_principal,
                            'Mots_Cles_Generation': st.session_state.lyrics_mots_cles_generation,
                            'Langue_Paroles': st.session_state.lyrics_langue_paroles,
                            'Niveau_Langage_Paroles': st.session_state.lyrics_niveau_langage_paroles,
                            'Imagerie_Texte': st.session_state.lyrics_imagerie_texte,
                            'Structure_Chanson_Specifique': st.session_state.lyrics_structure_chanson,
                            'ID_Artiste_IA': new_morceau_artist_ia,
                            'Ambiance_Sonore_Specifique': st.session_state.lyrics_mood_principal, # Ajout du mood
                            'Effets_Production_Domination': '', 'Type_Voix_Desiree': '', 'Style_Vocal_Desire': '', 'Caractere_Voix_Desire': '',
                            'Durée_Estimee': '', 'URL_Audio_Local': '', 'URL_Cover_Album': '', 'URL_Video_Clip_Associe': '', 'Mots_Cles_SEO': '', 'Description_Courte_Marketing': '',
                            'ID_Album_Associe': '' # Assurer que toutes les colonnes sont présentes
                        }
                        if sc.add_morceau_generes(morceau_data):
                            st.success(f"Paroles sauvegardées comme nouveau morceau '{new_morceau_title}' dans Google Sheet !")
                            del st.session_state['generated_lyrics'] # Nettoyer après sauvegarde
                        else:
                            st.error("Échec de la sauvegarde des paroles.")
           
            elif save_lyrics_option == "Dans un Morceau Existant (Google Sheet)":
                morceaux_df = sc.get_all_morceaux()
                if not morceaux_df.empty:
                    morceau_to_update_id = st.selectbox(
                        "Sélectionnez le morceau à mettre à jour",
                        morceaux_df['ID_Morceau'].tolist(),
                        format_func=lambda x: f"{x} - {morceaux_df[morceaux_df['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
                        key="update_existing_morceau_lyrics_id"
                    )
                    if st.button("Mettre à jour les Paroles du Morceau Existant"):
                        morceau_data_update = {
                            'Prompt_Generation_Paroles': st.session_state.generated_lyrics,
                            'Statut_Production': 'Paroles Générées'
                        }
                        if sc.update_morceau_generes(morceau_to_update_id, morceau_data_update):
                            st.success(f"Paroles mises à jour pour le morceau '{morceau_to_update_id}' dans Google Sheet !")
                            del st.session_state['generated_lyrics']
                        else:
                            st.error("Échec de la mise à jour des paroles.")
                else:
                    st.info("Aucun morceau existant dans votre Google Sheet.")

            elif save_lyrics_option == "Dans un fichier local":
                filename = st.text_input("Nom du fichier local (.txt)", value=f"paroles_{st.session_state.lyrics_genre_musical}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", key="local_lyrics_filename")
                if st.button("Sauvegarder les Paroles en local"):
                    file_path = os.path.join(GENERATED_TEXTS_DIR, filename)
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(st.session_state.generated_lyrics)
                        st.success(f"Paroles sauvegardées localement: {file_path}")
                        del st.session_state['generated_lyrics']
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde locale des paroles: {e}")

    st.markdown("---")

    # --- Formulaire de Génération de Prompt Audio ---
    if content_type == "Prompt Audio (pour SUNO)":
        st.subheader("Générer un Prompt Audio Détaillé (pour SUNO)")
        with st.form("audio_prompt_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.selectbox("Genre Musical", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="audio_genre_musical")
                st.selectbox("Mood Principal", sc.get_all_moods()['ID_Mood'].tolist(), key="audio_mood_principal")
                st.text_input("Durée Estimée (ex: 03:30)", key="audio_duree_estimee")
                st.text_input("Instrumentation Principale (ex: Piano, Violoncelle, Pads)", key="audio_instrumentation_principale")
            with col2:
                st.text_input("Ambiance Sonore Spécifique", key="audio_ambiance_sonore_specifique")
                st.text_input("Effets de Production Dominants (ex: Réverbération luxuriante)", key="audio_effets_production_dominants")
                st.selectbox("Type de Voix Désirée", ["N/A", "Chant Masculin", "Chant Féminin", "Spoken Word", "Chœur", "Voix Robotique"], key="audio_type_voix_desiree")
                st.text_input("Style Vocal Désiré (ex: Lyrique, Râpeux)", key="audio_style_vocal_desire")
                st.text_input("Caractère de la Voix (ex: Puissant, Doux)", key="audio_caractere_voix_desire")
                st.selectbox("Structure de Chanson", ["N/A"] + sc.get_all_structures_song()['ID_Structure'].tolist(), key="audio_structure_song")

            submit_audio_prompt_button = st.form_submit_button("Générer le Prompt Audio")

            if submit_audio_prompt_button:
                with st.spinner("L'Oracle génère le prompt audio..."):
                    generated_audio_prompt = go.generate_audio_prompt(
                        genre_musical=st.session_state.audio_genre_musical,
                        mood_principal=st.session_state.audio_mood_principal,
                        duree_estimee=st.session_state.audio_duree_estimee,
                        instrumentation_principale=st.session_state.audio_instrumentation_principale,
                        ambiance_sonore_specifique=st.session_state.audio_ambiance_sonore_specifique,
                        effets_production_dominants=st.session_state.audio_effets_production_dominants,
                        type_voix_desiree=st.session_state.audio_type_voix_desiree,
                        style_vocal_desire=st.session_state.audio_style_vocal_desire,
                        caractere_voix_desire=st.session_state.audio_caractere_voix_desire,
                        structure_song=st.session_state.audio_structure_song
                    )
                    st.session_state['generated_audio_prompt'] = generated_audio_prompt
                    st.success("Prompt Audio généré avec succès !")

        if 'generated_audio_prompt' in st.session_state and st.session_state.generated_audio_prompt:
            st.markdown("---")
            st.subheader("Prompt Audio Généré (pour SUNO ou autre)")
            st.text_area("Copiez ce prompt pour votre générateur audio :", st.session_state.generated_audio_prompt, height=200, key="displayed_generated_audio_prompt")

            # Option de sauvegarde du prompt audio pour un morceau existant
            morceaux_df = sc.get_all_morceaux()
            if not morceaux_df.empty:
                morceau_to_update_audio_id = st.selectbox(
                    "Liez ce prompt à un morceau existant (Google Sheet) :",
                    morceaux_df['ID_Morceau'].tolist(),
                    format_func=lambda x: f"{x} - {morceaux_df[morceaux_df['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
                    key="update_existing_morceau_audio_prompt_id"
                )
                if st.button("Mettre à jour le Prompt Audio du Morceau Existant"):
                    morceau_data_update = {
                        'Prompt_Generation_Audio': st.session_state.generated_audio_prompt,
                        'Statut_Production': 'Prompt Audio Généré'
                    }
                    if sc.update_morceau_generes(morceau_to_update_audio_id, morceau_data_update):
                        st.success(f"Prompt Audio mis à jour pour le morceau '{morceau_to_update_audio_id}' !")
                        del st.session_state['generated_audio_prompt']
                    else:
                        st.error("Échec de la mise à jour du prompt audio.")
            else:
                st.info("Aucun morceau existant pour lier le prompt audio.")

    st.markdown("---")

    # --- Formulaire de Génération d'Idées de Titres ---
    if content_type == "Idées de Titres":
        st.subheader("Générer des Idées de Titres de Chansons")
        with st.form("title_generator_form"):
            st.selectbox("Thème Principal", sc.get_all_themes()['ID_Theme'].tolist(), key="title_theme_principal")
            st.selectbox("Genre Musical", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="title_genre_musical")
            st.text_area("Extrait de paroles (optionnel, pour inspiration)", key="title_paroles_extrait")
            submit_title_button = st.form_submit_button("Générer les Titres")

            if submit_title_button:
                with st.spinner("L'Oracle brainstorme des titres..."):
                    generated_titles = go.generate_title_ideas(
                        theme_principal=st.session_state.title_theme_principal,
                        genre_musical=st.session_state.title_genre_musical,
                        paroles_extrait=st.session_state.title_paroles_extrait
                    )
                    st.session_state['generated_titles'] = generated_titles
                    st.success("Idées de titres générées avec succès !")
       
        if 'generated_titles' in st.session_state and st.session_state.generated_titles:
            st.markdown("---")
            st.subheader("Idées de Titres Générées")
            st.text_area("Copiez les titres ici :", st.session_state.generated_titles, height=250, key="displayed_generated_titles")

    st.markdown("---")

    # --- Formulaire de Génération de Description Marketing ---
    if content_type == "Description Marketing":
        st.subheader("Générer une Description Marketing")
        with st.form("marketing_copy_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Titre du Morceau/Album", key="marketing_titre_morceau")
                st.selectbox("Genre Musical", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="marketing_genre_musical")
            with col2:
                st.selectbox("Mood Principal", sc.get_all_moods()['ID_Mood'].tolist(), key="marketing_mood_principal")
                st.selectbox("Public Cible", sc.get_all_public_cible()['ID_Public'].tolist(), key="marketing_public_cible")
            st.text_input("Point Fort Principal (ex: 'son unique', 'message profond')", key="marketing_point_fort")
            submit_marketing_button = st.form_submit_button("Générer la Description Marketing")

            if submit_marketing_button:
                with st.spinner("L'Oracle rédige la description..."):
                    generated_marketing_copy = go.generate_marketing_copy(
                        titre_morceau=st.session_state.marketing_titre_morceau,
                        genre_musical=st.session_state.marketing_genre_musical,
                        mood_principal=st.session_state.marketing_mood_principal,
                        public_cible=st.session_state.marketing_public_cible,
                        point_fort_principal=st.session_state.marketing_point_fort
                    )
                    st.session_state['generated_marketing_copy'] = generated_marketing_copy
                    st.success("Description marketing générée avec succès !")
       
        if 'generated_marketing_copy' in st.session_state and st.session_state.generated_marketing_copy:
            st.markdown("---")
            st.subheader("Description Marketing Générée")
            st.text_area("Copiez la description ici :", st.session_state.generated_marketing_copy, height=150, key="displayed_generated_marketing_copy")

    st.markdown("---")

    # --- Formulaire de Génération de Prompt Pochette d'Album ---
    if content_type == "Prompt Pochette d'Album":
        st.subheader("Générer un Prompt pour Pochette d'Album (Midjourney/DALL-E)")
        with st.form("album_art_prompt_form"):
            st.text_input("Nom de l'Album", key="album_art_nom_album")
            st.selectbox("Genre Dominant de l'Album", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="album_art_genre_dominant")
            st.text_area("Description du Concept de l'Album", key="album_art_description_concept")
            st.selectbox("Mood Principal Visuel", sc.get_all_moods()['ID_Mood'].tolist(), key="album_art_mood_principal")
            st.text_input("Mots-clés Visuels Supplémentaires (ex: 'couleurs vives', 'style néon', 'minimaliste')", key="album_art_mots_cles_visuels")
            submit_album_art_button = st.form_submit_button("Générer le Prompt Visuel")

            if submit_album_art_button:
                with st.spinner("L'Oracle imagine la pochette..."):
                    generated_album_art_prompt = go.generate_album_art_prompt(
                        nom_album=st.session_state.album_art_nom_album,
                        genre_dominant_album=st.session_state.album_art_genre_dominant,
                        description_concept_album=st.session_state.album_art_description_concept,
                        mood_principal=st.session_state.album_art_mood_principal,
                        mots_cles_visuels_suppl=st.session_state.album_art_mots_cles_visuels
                    )
                    st.session_state['generated_album_art_prompt'] = generated_album_art_prompt
                    st.success("Prompt de pochette d'album généré avec succès !")
       
        if 'generated_album_art_prompt' in st.session_state and st.session_state.generated_album_art_prompt:
            st.markdown("---")
            st.subheader("Prompt de Pochette d'Album Généré")
            st.text_area("Copiez ce prompt pour votre générateur d'images :", st.session_state.generated_album_art_prompt, height=300, key="displayed_generated_album_art_prompt") 

# app.py - Suite du code

# --- Page : Co-pilote Créatif (Création Musicale IA) ---
if st.session_state['current_page'] == 'Co-pilote Créatif':
    st.header("💡 Co-pilote Créatif de l'Oracle (Beta)")
    st.write("Laissez l'Oracle vous accompagner en temps réel pour l'écriture de paroles, la composition harmonique ou rythmique.")
    st.info("Cette fonctionnalité est en version Beta. Les suggestions sont basées sur votre input et le contexte défini.")

    co_pilot_type = st.radio(
        "Quel type de suggestion souhaitez-vous ?",
        ["Suite Lyrique", "Ligne de Basse", "Prochain Accord"],
        key="co_pilot_type_radio"
    )

    st.markdown("---")

    # Contexte global pour le co-pilote
    st.subheader("Contexte du Morceau")
    col_ctx1, col_ctx2 = st.columns(2)
    with col_ctx1:
        st.selectbox("Genre Musical du morceau", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="copilot_genre_musical")
        st.selectbox("Mood du morceau", sc.get_all_moods()['ID_Mood'].tolist(), key="copilot_mood_principal")
    with col_ctx2:
        st.selectbox("Thème Principal du morceau", sc.get_all_themes()['ID_Theme'].tolist(), key="copilot_theme_principal")
        st.text_input("Mots-clés contextuels (ex: 'solitude urbaine', 'rythme entraînant')", key="copilot_context_keywords")
   
    # Construction du contexte pour l'IA
    full_context = f"Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}, Thème: {st.session_state.copilot_theme_principal}, Mots-clés: {st.session_state.copilot_context_keywords}"

    st.markdown("---")

    # --- Formulaire pour Suite Lyrique ---
    if co_pilot_type == "Suite Lyrique":
        st.subheader("Suggérer la Suite des Paroles")
        with st.form("copilot_lyrics_form"):
            st.text_area("Commencez à écrire vos paroles ici :", key="copilot_current_lyrics_input", height=100)
            submit_copilot_lyrics = st.form_submit_button("Suggérer la suite")

            if submit_copilot_lyrics:
                if st.session_state.copilot_current_lyrics_input:
                    with st.spinner("L'Oracle brainstorme la suite des paroles..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_lyrics_input,
                            context=full_context,
                            type_suggestion="suite_lyrique"
                        )
                        st.session_state['copilot_lyrics_suggestion'] = suggestion
                        st.success("Suggestion de paroles prête !")
                else:
                    st.warning("Veuillez entrer du texte pour obtenir une suggestion de suite.")

        if 'copilot_lyrics_suggestion' in st.session_state and st.session_state.copilot_lyrics_suggestion:
            st.markdown("---")
            st.subheader("Suggestion de Paroles")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_lyrics_suggestion, height=200)
            if st.button("Utiliser cette suggestion", key="use_lyrics_suggestion"):
                st.session_state.copilot_current_lyrics_input += "\n" + st.session_state.copilot_lyrics_suggestion
                st.experimental_rerun() # Recharger pour afficher la mise à jour


    # --- Formulaire pour Ligne de Basse ---
    elif co_pilot_type == "Ligne de Basse":
        st.subheader("Suggérer une Ligne de Basse")
        with st.form("copilot_bass_form"):
            st.text_input("Décrivez le groove ou la progression d'accords actuelle (ex: 'groove funk sur Am - G - C - F')", key="copilot_current_bass_input")
            submit_copilot_bass = st.form_submit_button("Suggérer une ligne de basse")

            if submit_copilot_bass:
                if st.session_state.copilot_current_bass_input:
                    with st.spinner("L'Oracle imagine la ligne de basse..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_bass_input,
                            context=full_context,
                            type_suggestion="ligne_basse"
                        )
                        st.session_state['copilot_bass_suggestion'] = suggestion
                        st.success("Suggestion de ligne de basse prête !")
                else:
                    st.warning("Veuillez décrire le contexte musical pour la ligne de basse.")

        if 'copilot_bass_suggestion' in st.session_state and st.session_state.copilot_bass_suggestion:
            st.markdown("---")
            st.subheader("Suggestion de Ligne de Basse")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_bass_suggestion, height=150)


    # --- Formulaire pour Prochain Accord ---
    elif co_pilot_type == "Prochain Accord":
        st.subheader("Suggérer le Prochain Accord")
        with st.form("copilot_chord_form"):
            st.text_input("Entrez l'accord actuel (ex: 'Cmaj7', 'Am')", key="copilot_current_chord_input")
            st.text_input("Tonalité du morceau (ex: 'C Majeur', 'A mineur')", key="copilot_tonalite_input")
            submit_copilot_chord = st.form_submit_button("Suggérer le prochain accord")

            if submit_copilot_chord:
                if st.session_state.copilot_current_chord_input and st.session_state.copilot_tonalite_input:
                    chord_context = f"Tonalité: {st.session_state.copilot_tonalite_input}, Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}"
                    with st.spinner("L'Oracle réfléchit aux harmonies..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_chord_input,
                            context=chord_context,
                            type_suggestion="prochain_accord"
                        )
                        st.session_state['copilot_chord_suggestion'] = suggestion
                        st.success("Suggestion d'accords prête !")
                else:
                    st.warning("Veuillez entrer l'accord actuel et la tonalité.")

        if 'copilot_chord_suggestion' in st.session_state and st.session_state.copilot_chord_suggestion:
            st.markdown("---")
            st.subheader("Suggestions de Prochains Accords")
            st.text_area("Voici les options du Co-pilote :", st.session_state.copilot_chord_suggestion, height=200) 

# app.py - Suite du code

# --- Page : Création Multimodale (Création Musicale IA) ---
if st.session_state['current_page'] == 'Création Multimodale':
    st.header("🎬 Création Multimodale Synchronisée")
    st.write("L'Oracle génère des prompts cohérents pour vos paroles, votre audio (pour SUNO) et vos visuels (pour Midjourney/DALL-E), assurant une harmonie parfaite de votre œuvre.")

    with st.form("multimodal_creation_form"):
        col_multi1, col_multi2 = st.columns(2)
        with col_multi1:
            st.selectbox("Thème Principal", sc.get_all_themes()['ID_Theme'].tolist(), key="multi_main_theme")
            st.selectbox("Genre Musical Général", sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="multi_main_genre")
        with col_multi2:
            st.selectbox("Mood Général", sc.get_all_moods()['ID_Mood'].tolist(), key="multi_main_mood")
            st.selectbox("Artiste IA Associé", sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist(), key="multi_artiste_ia_name")
       
        st.text_input("Longueur Estimée du Morceau (ex: '03:45')", key="multi_longueur_morceau")

        submit_multimodal_button = st.form_submit_button("Générer les Prompts Multimodaux")

        if submit_multimodal_button:
            with st.spinner("L'Oracle orchestre votre création multimodale..."):
                multimodal_prompts = go.generate_multimodal_content_prompts(
                    main_theme=st.session_state.multi_main_theme,
                    main_genre=st.session_state.multi_main_genre,
                    main_mood=st.session_state.multi_main_mood,
                    longueur_morceau=st.session_state.multi_longueur_morceau,
                    artiste_ia_name=st.session_state.multi_artiste_ia_name
                )
                st.session_state['multimodal_prompts'] = multimodal_prompts
                st.success("Prompts multimodaux générés avec succès !")

    if 'multimodal_prompts' in st.session_state and st.session_state.multimodal_prompts:
        st.markdown("---")
        st.subheader("Prompts Multimodaux Générés")
       
        st.write("### Prompt pour les Paroles de Chanson :")
        st.text_area("Copiez pour votre parolier ou pour affiner :", st.session_state.multimodal_prompts.get("paroles_prompt", ""), height=300, key="multi_lyrics_output")

        st.write("### Prompt pour la Génération Audio (pour SUNO) :")
        st.text_area("Copiez pour SUNO ou votre générateur audio :", st.session_state.multimodal_prompts.get("audio_suno_prompt", ""), height=200, key="multi_audio_output")

        st.write("### Prompt pour l'Image de Pochette (Midjourney/DALL-E) :")
        st.text_area("Copiez pour votre générateur d'images :", st.session_state.multimodal_prompts.get("image_prompt", ""), height=250, key="multi_image_output") 

# app.py - Suite du code

# --- Page : Mes Morceaux (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Mes Morceaux':
    st.header("🎶 Mes Morceaux Générés")
    st.write("Gérez et consultez toutes vos créations musicales, qu'elles soient entièrement générées par l'IA ou co-créées.")

    morceaux_df = sc.get_all_morceaux()
   
    tab1, tab2, tab3 = st.tabs(["Voir/Rechercher Morceaux", "Ajouter un Nouveau Morceau", "Mettre à Jour/Supprimer Morceau"])

    with tab1:
        st.subheader("Voir et Rechercher des Morceaux")
        if not morceaux_df.empty:
            # Recherche simple
            search_query = st.text_input("Rechercher par titre, genre ou mots-clés", key="search_morceaux")
            if search_query:
                filtered_df = morceaux_df[morceaux_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_df = morceaux_df

            # Affichage avec formatage
            display_dataframe(ut.format_dataframe_for_display(filtered_df), key="morceaux_display")
        else:
            st.info("Aucun morceau enregistré pour le moment.")

    with tab2:
        st.subheader("Ajouter un Nouveau Morceau")
        with st.form("add_morceau_form"):
            col_add1, col_add2 = st.columns(2)
            with col_add1:
                new_titre = st.text_input("Titre du Morceau", key="add_morceau_titre")
                new_statut = st.selectbox("Statut de Production", ["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"], key="add_morceau_statut")
                new_duree = st.text_input("Durée Estimée (ex: 03:45)", key="add_morceau_duree")
               
                st.selectbox("Style Musical Principal", [''] + sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="add_morceau_style_musical")
                st.selectbox("Mood Principal", [''] + sc.get_all_moods()['ID_Mood'].tolist(), key="add_morceau_mood_principal")
                st.selectbox("Thème Principal Lyrique", [''] + sc.get_all_themes()['ID_Theme'].tolist(), key="add_morceau_theme_lyrique")
                st.selectbox("Structure de Chanson", [''] + sc.get_all_structures_song()['ID_Structure'].tolist(), key="add_morceau_structure_chanson")
                st.text_area("Mots-clés de Génération (séparés par des virgules)", key="add_morceau_mots_cles_gen")
                st.selectbox("Langue des Paroles", [''] + ["Français", "Anglais", "Espagnol"], key="add_morceau_langue_paroles")
                st.selectbox("Niveau de Langage Paroles", [''] + ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], key="add_morceau_niveau_langage")
                st.selectbox("Imagerie Texte", [''] + ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], key="add_morceau_imagerie_texte")
           
            with col_add2:
                new_artiste_ia = st.selectbox("Artiste IA Associé", [''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist(), key="add_morceau_artiste_ia")
                new_album_associe = st.selectbox("Album Associé", [''] + sc.get_all_albums()['ID_Album'].tolist(), key="add_morceau_album_associe")
               
                st.text_area("Prompt Génération Audio (pour SUNO)", key="add_morceau_prompt_audio", height=150)
                st.text_area("Prompt Génération Paroles", key="add_morceau_prompt_paroles", height=150)
                st.text_input("Instrumentation Principale", key="add_morceau_instrumentation")
                st.text_input("Ambiance Sonore Spécifique", key="add_morceau_ambiance_sonore")
                st.text_input("Effets Production Dominants", key="add_morceau_effets_prod")
                st.selectbox("Type de Voix Désirée", [''] + sc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist(), key="add_morceau_type_voix")
                st.text_input("Style Vocal Désiré", key="add_morceau_style_vocal")
                st.text_input("Caractère Voix Désiré", key="add_morceau_caractere_voix")
                st.text_input("Mots-clés SEO", key="add_morceau_mots_cles_seo")
                st.text_area("Description Courte Marketing", key="add_morceau_desc_marketing", height=100)
               
                # --- Téléchargement de Fichiers ---
                st.markdown("##### Téléchargement de Fichiers Locaux")
                uploaded_audio_file = st.file_uploader("Uploader Fichier Audio (.mp3, .wav)", type=["mp3", "wav"], key="upload_audio_morceau")
                uploaded_cover_file = st.file_uploader("Uploader Image de Cover (.jpg, .png)", type=["jpg", "png"], key="upload_cover_morceau")

            submit_new_morceau = st.form_submit_button("Ajouter le Morceau")

            if submit_new_morceau:
                # Sauvegarder les fichiers uploadés
                audio_path = ut.save_uploaded_file(uploaded_audio_file, AUDIO_CLIPS_DIR)
                cover_path = ut.save_uploaded_file(uploaded_cover_file, SONG_COVERS_DIR)

                new_morceau_data = {
                    'Titre_Morceau': st.session_state.add_morceau_titre,
                    'Statut_Production': st.session_state.add_morceau_statut,
                    'Durée_Estimee': st.session_state.add_morceau_duree,
                    'ID_Album_Associe': st.session_state.add_morceau_album_associe,
                    'ID_Artiste_IA': st.session_state.add_morceau_artiste_ia,
                    'Prompt_Generation_Audio': st.session_state.add_morceau_prompt_audio,
                    'Prompt_Generation_Paroles': st.session_state.add_morceau_prompt_paroles,
                    'ID_Style_Musical_Principal': st.session_state.add_morceau_style_musical,
                    'ID_Style_Lyrique_Principal': st.session_state.add_morceau_theme_lyrique, # Utilise le champ theme pour le style lyrique principal
                    'Theme_Principal_Lyrique': st.session_state.add_morceau_theme_lyrique,
                    'Mots_Cles_Generation': st.session_state.add_morceau_mots_cles_gen,
                    'Langue_Paroles': st.session_state.add_morceau_langue_paroles,
                    'Niveau_Langage_Paroles': st.session_state.add_morceau_niveau_langage,
                    'Imagerie_Texte': st.session_state.add_morceau_imagerie_texte,
                    'Structure_Chanson_Specifique': st.session_state.add_morceau_structure_chanson,
                    'Instrumentation_Principale': st.session_state.add_morceau_instrumentation,
                    'Ambiance_Sonore_Specifique': st.session_state.add_morceau_ambiance_sonore,
                    'Effets_Production_Domination': st.session_state.add_morceau_effets_prod,
                    'Type_Voix_Desiree': st.session_state.add_morceau_type_voix,
                    'Style_Vocal_Desire': st.session_state.add_morceau_style_vocal,
                    'Caractere_Voix_Desire': st.session_state.add_morceau_caractere_voix,
                    'URL_Audio_Local': audio_path if audio_path else '',
                    'URL_Cover_Album': cover_path if cover_path else '',
                    'URL_Video_Clip_Associe': '', # Pas d'upload direct pour les vidéos ici
                    'Mots_Cles_SEO': st.session_state.add_morceau_mots_cles_seo,
                    'Description_Courte_Marketing': st.session_state.add_morceau_desc_marketing
                }
               
                if sc.add_morceau_generes(new_morceau_data):
                    st.success(f"Morceau '{new_titre}' ajouté avec succès à Google Sheet !")
                    st.experimental_rerun() # Rafraîchir pour voir les changements
                else:
                    st.error("Échec de l'ajout du morceau.")

    with tab3:
        st.subheader("Mettre à Jour ou Supprimer un Morceau")
        if not morceaux_df.empty:
            morceau_to_select = st.selectbox(
                "Sélectionnez le Morceau à modifier/supprimer",
                morceaux_df['ID_Morceau'].tolist(),
                format_func=lambda x: f"{x} - {morceaux_df[morceaux_df['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
                key="select_morceau_to_edit"
            )
           
            if morceau_to_select:
                selected_morceau = morceaux_df[morceaux_df['ID_Morceau'] == morceau_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_morceau['Titre_Morceau']}")

                with st.form("update_delete_morceau_form"):
                    col_upd1, col_upd2 = st.columns(2)
                    with col_upd1:
                        upd_titre = st.text_input("Titre du Morceau", value=selected_morceau['Titre_Morceau'], key="upd_morceau_titre")
                        upd_statut = st.selectbox("Statut de Production", ["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"], index=["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"].index(selected_morceau['Statut_Production']), key="upd_morceau_statut")
                        upd_duree = st.text_input("Durée Estimée (ex: 03:45)", value=selected_morceau['Durée_Estimee'], key="upd_morceau_duree")

                        upd_style_musical = st.selectbox("Style Musical Principal", [''] + sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), index=([''] + sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()).index(selected_morceau['ID_Style_Musical_Principal']) if selected_morceau['ID_Style_Musical_Principal'] in ([''] + sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()) else 0, key="upd_morceau_style_musical")
                        upd_mood_principal = st.selectbox("Mood Principal", [''] + sc.get_all_moods()['ID_Mood'].tolist(), index=([''] + sc.get_all_moods()['ID_Mood'].tolist()).index(selected_morceau['Ambiance_Sonore_Specifique']) if selected_morceau['Ambiance_Sonore_Specifique'] in ([''] + sc.get_all_moods()['ID_Mood'].tolist()) else 0, key="upd_morceau_mood_principal")
                        upd_theme_lyrique = st.selectbox("Thème Principal Lyrique", [''] + sc.get_all_themes()['ID_Theme'].tolist(), index=([''] + sc.get_all_themes()['ID_Theme'].tolist()).index(selected_morceau['Theme_Principal_Lyrique']) if selected_morceau['Theme_Principal_Lyrique'] in ([''] + sc.get_all_themes()['ID_Theme'].tolist()) else 0, key="upd_morceau_theme_lyrique")
                        upd_structure_chanson = st.selectbox("Structure de Chanson", [''] + sc.get_all_structures_song()['ID_Structure'].tolist(), index=([''] + sc.get_all_structures_song()['ID_Structure'].tolist()).index(selected_morceau['Structure_Chanson_Specifique']) if selected_morceau['Structure_Chanson_Specifique'] in ([''] + sc.get_all_structures_song()['ID_Structure'].tolist()) else 0, key="upd_morceau_structure_chanson")
                        upd_mots_cles_gen = st.text_area("Mots-clés de Génération (séparés par des virgules)", value=selected_morceau['Mots_Cles_Generation'], key="upd_morceau_mots_cles_gen")
                        upd_langue_paroles = st.selectbox("Langue des Paroles", [''] + ["Français", "Anglais", "Espagnol"], index=([''] + ["Français", "Anglais", "Espagnol"]).index(selected_morceau['Langue_Paroles']) if selected_morceau['Langue_Paroles'] in ([''] + ["Français", "Anglais", "Espagnol"]) else 0, key="upd_morceau_langue_paroles")
                        upd_niveau_langage = st.selectbox("Niveau de Langage Paroles", [''] + ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], index=([''] + ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"]).index(selected_morceau['Niveau_Langage_Paroles']) if selected_morceau['Niveau_Langage_Paroles'] in ([''] + ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"]) else 0, key="upd_morceau_niveau_langage")
                        upd_imagerie_texte = st.selectbox("Imagerie Texte", [''] + ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], index=([''] + ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"]).index(selected_morceau['Imagerie_Texte']) if selected_morceau['Imagerie_Texte'] in ([''] + ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"]) else 0, key="upd_morceau_imagerie_texte")
                   
                    with col_upd2:
                        upd_artiste_ia = st.selectbox("Artiste IA Associé", [''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist(), index=([''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()).index(selected_morceau['ID_Artiste_IA']) if selected_morceau['ID_Artiste_IA'] in ([''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()) else 0, key="upd_morceau_artiste_ia")
                        upd_album_associe = st.selectbox("Album Associé", [''] + sc.get_all_albums()['ID_Album'].tolist(), index=([''] + sc.get_all_albums()['ID_Album'].tolist()).index(selected_morceau['ID_Album_Associe']) if selected_morceau['ID_Album_Associe'] in ([''] + sc.get_all_albums()['ID_Album'].tolist()) else 0, key="upd_morceau_album_associe")
                       
                        upd_prompt_audio = st.text_area("Prompt Génération Audio (pour SUNO)", value=selected_morceau['Prompt_Generation_Audio'], height=150, key="upd_morceau_prompt_audio")
                        upd_prompt_paroles = st.text_area("Prompt Génération Paroles", value=selected_morceau['Prompt_Generation_Paroles'], height=150, key="upd_morceau_prompt_paroles")
                        upd_instrumentation = st.text_input("Instrumentation Principale", value=selected_morceau['Instrumentation_Principale'], key="upd_morceau_instrumentation")
                        upd_ambiance_sonore = st.text_input("Ambiance Sonore Spécifique", value=selected_morceau['Ambiance_Sonore_Specifique'], key="upd_morceau_ambiance_sonore")
                        upd_effets_prod = st.text_input("Effets Production Dominants", value=selected_morceau['Effets_Production_Domination'], key="upd_morceau_effets_prod")
                        upd_type_voix = st.selectbox("Type de Voix Désirée", [''] + sc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist(), index=([''] + sc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist()).index(selected_morceau['Type_Voix_Desiree']) if selected_morceau['Type_Voix_Desiree'] in ([''] + sc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist()) else 0, key="upd_morceau_type_voix")
                        upd_style_vocal = st.text_input("Style Vocal Désiré", value=selected_morceau['Style_Vocal_Desire'], key="upd_morceau_style_vocal")
                        upd_caractere_voix = st.text_input("Caractère Voix Désiré", value=selected_morceau['Caractere_Voix_Desire'], key="upd_morceau_caractere_voix")
                        upd_mots_cles_seo = st.text_input("Mots-clés SEO", value=selected_morceau['Mots_Cles_SEO'], key="upd_morceau_mots_cles_seo")
                        upd_desc_marketing = st.text_area("Description Courte Marketing", value=selected_morceau['Description_Courte_Marketing'], height=100, key="upd_morceau_desc_marketing")
                       
                        # Affichage des chemins de fichiers existants et upload pour mise à jour
                        st.markdown("##### Fichiers Locaux Existants")
                        if selected_morceau['URL_Audio_Local']:
                            st.text_input("Chemin Audio Local Actuel", value=selected_morceau['URL_Audio_Local'], disabled=True, key="current_audio_path")
                            st.audio(os.path.join(AUDIO_CLIPS_DIR, selected_morceau['URL_Audio_Local']), format="audio/mp3", start_time=0)
                        if selected_morceau['URL_Cover_Album']:
                            st.text_input("Chemin Cover Album Actuel", value=selected_morceau['URL_Cover_Album'], disabled=True, key="current_cover_path")
                            st.image(os.path.join(SONG_COVERS_DIR, selected_morceau['URL_Cover_Album']), width=150)

                        uploaded_audio_file_upd = st.file_uploader("Uploader Nouveau Fichier Audio (.mp3, .wav)", type=["mp3", "wav"], key="upload_audio_morceau_upd")
                        uploaded_cover_file_upd = st.file_uploader("Uploader Nouvelle Image de Cover (.jpg, .png)", type=["jpg", "png"], key="upload_cover_morceau_upd")


                    col_form_buttons = st.columns(2)
                    with col_form_buttons[0]:
                        submit_update_morceau = st.form_submit_button("Mettre à Jour le Morceau")
                    with col_form_buttons[1]:
                        submit_delete_morceau = st.form_submit_button("Supprimer le Morceau")

                    if submit_update_morceau:
                        audio_path_upd = selected_morceau['URL_Audio_Local']
                        if uploaded_audio_file_upd:
                            new_audio_path = ut.save_uploaded_file(uploaded_audio_file_upd, AUDIO_CLIPS_DIR)
                            if new_audio_path: audio_path_upd = new_audio_path

                        cover_path_upd = selected_morceau['URL_Cover_Album']
                        if uploaded_cover_file_upd:
                            new_cover_path = ut.save_uploaded_file(uploaded_cover_file_upd, SONG_COVERS_DIR)
                            if new_cover_path: cover_path_upd = new_cover_path

                        morceau_data_update = {
                            'Titre_Morceau': upd_titre,
                            'Statut_Production': upd_statut,
                            'Durée_Estimee': upd_duree,
                            'ID_Album_Associe': upd_album_associe,
                            'ID_Artiste_IA': upd_artiste_ia,
                            'Prompt_Generation_Audio': upd_prompt_audio,
                            'Prompt_Generation_Paroles': upd_prompt_paroles,
                            'ID_Style_Musical_Principal': upd_style_musical,
                            'ID_Style_Lyrique_Principal': upd_theme_lyrique, # S'assure que cette colonne est correcte
                            'Theme_Principal_Lyrique': upd_theme_lyrique,
                            'Mots_Cles_Generation': upd_mots_cles_gen,
                            'Langue_Paroles': upd_langue_paroles,
                            'Niveau_Langage_Paroles': upd_niveau_langage,
                            'Imagerie_Texte': upd_imagerie_texte,
                            'Structure_Chanson_Specifique': upd_structure_chanson,
                            'Instrumentation_Principale': upd_instrumentation,
                            'Ambiance_Sonore_Specifique': upd_ambiance_sonore,
                            'Effets_Production_Domination': upd_effets_prod,
                            'Type_Voix_Desiree': upd_type_voix,
                            'Style_Vocal_Desire': upd_style_vocal,
                            'Caractere_Voix_Desire': upd_caractere_voix,
                            'URL_Audio_Local': audio_path_upd,
                            'URL_Cover_Album': cover_path_upd,
                            'Mots_Cles_SEO': upd_mots_cles_seo,
                            'Description_Courte_Marketing': upd_desc_marketing
                        }
                        if sc.update_morceau_generes(morceau_to_select, morceau_data_update):
                            st.success(f"Morceau '{upd_titre}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du morceau.")
                   
                    if submit_delete_morceau:
                        if st.warning(f"Voulez-vous vraiment supprimer le morceau '{selected_morceau['Titre_Morceau']}' (ID: {morceau_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_morceau"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["MORCEAUX_GENERES"], 'ID_Morceau', morceau_to_select):
                                    st.success(f"Morceau '{morceau_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du morceau.")
        else:
            st.info("Aucun morceau à modifier ou supprimer pour le moment.") 

# app.py - Suite du code

# --- Page : Lecteur Audios (Expérience Musicale Interactive) ---
if st.session_state['current_page'] == 'Lecteur Audios':
    st.header("🎵 Lecteur Audios de l'Architecte Ω")
    st.write("Écoutez vos morceaux générés par l'IA, visualisez leurs paroles et marquez vos favoris. Une expérience immersive pour vos créations.")

    morceaux_df = sc.get_all_morceaux()
    paroles_existantes_df = sc.get_all_paroles_existantes()

    if not morceaux_df.empty:
        # Filtrage et sélection du morceau
        col_select_track, col_filter_track = st.columns([0.7, 0.3])
       
        with col_filter_track:
            st.subheader("Filtres")
            filter_genre = st.selectbox("Filtrer par Genre", ['Tous'] + morceaux_df['ID_Style_Musical_Principal'].unique().tolist(), key="player_filter_genre")
            filter_artist = st.selectbox("Filtrer par Artiste IA", ['Tous'] + morceaux_df['ID_Artiste_IA'].unique().tolist(), key="player_filter_artist")
            filter_status = st.selectbox("Filtrer par Statut", ['Tous'] + morceaux_df['Statut_Production'].unique().tolist(), key="player_filter_status")

        filtered_morceaux = morceaux_df.copy()
        if filter_genre != 'Tous':
            filtered_morceaux = filtered_morceaux[filtered_morceaux['ID_Style_Musical_Principal'] == filter_genre]
        if filter_artist != 'Tous':
            filtered_morceaux = filtered_morceaux[filtered_morceaux['ID_Artiste_IA'] == filter_artist]
        if filter_status != 'Tous':
            filtered_morceaux = filtered_morceaux[filtered_morceaux['Statut_Production'] == filter_status]

        with col_select_track:
            st.subheader("Sélection du Morceau")
            if not filtered_morceaux.empty:
                # Créer une liste de sélection formatée
                track_options = filtered_morceaux.apply(lambda row: f"{row['Titre_Morceau']} ({row['ID_Morceau']}) - {row['ID_Artiste_IA']}", axis=1).tolist()
                selected_track_display = st.selectbox("Choisissez un morceau à écouter", track_options, key="player_select_track")

                # Récupérer l'ID du morceau sélectionné à partir du texte affiché
                if selected_track_display:
                    selected_morceau_id = selected_track_display.split('(')[1].split(')')[0]
                    st.session_state['selected_morceau_id'] = selected_morceau_id
                    current_morceau = filtered_morceaux[filtered_morceaux['ID_Morceau'] == st.session_state.selected_morceau_id].iloc[0]
                else:
                    current_morceau = None
            else:
                st.info("Aucun morceau ne correspond à vos filtres.")
                current_morceau = None
                st.session_state['selected_morceau_id'] = None

        if current_morceau is not None:
            st.markdown("---")
            st.subheader(f"En cours de lecture : {current_morceau['Titre_Morceau']}")
           
            audio_file_path = os.path.join(AUDIO_CLIPS_DIR, current_morceau['URL_Audio_Local'])
            cover_image_path = os.path.join(SONG_COVERS_DIR, current_morceau['URL_Cover_Album'])

            col_player_info, col_player_audio = st.columns([0.3, 0.7])

            with col_player_info:
                if os.path.exists(cover_image_path) and current_morceau['URL_Cover_Album']:
                    st.image(cover_image_path, caption=current_morceau['Titre_Morceau'], use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/200?text=Pas+de+Cover", caption="Aucune image de cover", use_column_width=True)
               
                st.markdown(f"**Artiste IA :** {current_morceau['ID_Artiste_IA']}")
                st.markdown(f"**Genre :** {current_morceau['ID_Style_Musical_Principal']}")
                st.markdown(f"**Durée Estimée :** {current_morceau['Durée_Estimee']}")
                st.markdown(f"**Statut :** {current_morceau['Statut_Production']}")

                # --- Fonctionnalité "Favori" ---
                # Ajoutons une colonne "Favori" dans MORCEAUX_GENERES si elle n'existe pas
                # (Cela doit être géré dans EXPECTED_COLUMNS et le script de création de sheet)
                # Pour l'instant, on simule ou on l'ajouterait manuellement à la feuille
                # Option simple : simuler un bouton sans persistance avancée
                if 'Favori' not in morceaux_df.columns:
                     st.info("La fonctionnalité 'Favori' n'est pas encore persistante. Ajoutez une colonne 'Favori' (VRAI/FAUX) à 'MORCEAUX_GENERES'.")
                     is_favorite = st.button("❤️ Ajouter aux Favoris (non persistant)", key="add_to_favorite_button")
                else:
                    # Implémenter la logique de mise à jour pour la colonne 'Favori'
                    current_favorite_status = current_morceau.get('Favori', 'FAUX') # Assumer FAUX par défaut
                    is_favorite_bool = ut.parse_boolean_string(str(current_favorite_status)) # Convertir la chaîne en booléen

                    if is_favorite_bool:
                        if st.button("💔 Retirer des Favoris", key="remove_from_favorite_button"):
                            sc.update_row_in_sheet(WORKSHEET_NAMES["MORCEAUX_GENERES"], 'ID_Morceau', current_morceau['ID_Morceau'], {'Favori': 'FAUX'})
                            st.success("Retiré des favoris.")
                            st.experimental_rerun()
                    else:
                        if st.button("❤️ Ajouter aux Favoris", key="add_to_favorite_button_persistant"):
                            sc.update_row_in_sheet(WORKSHEET_NAMES["MORCEAUX_GENERES"], 'ID_Morceau', current_morceau['ID_Morceau'], {'Favori': 'VRAI'})
                            st.success("Ajouté aux favoris !")
                            st.experimental_rerun()
           
            with col_player_audio:
                if os.path.exists(audio_file_path) and current_morceau['URL_Audio_Local']:
                    st.audio(audio_file_path, format="audio/mp3", start_time=0)
                else:
                    st.warning("Fichier audio non trouvé localement ou URL non renseignée.")
                    if current_morceau['Prompt_Generation_Audio']:
                        st.info("Vous pouvez utiliser le prompt audio ci-dessous avec SUNO ou un autre générateur :")
                        st.text_area("Prompt Génération Audio", value=current_morceau['Prompt_Generation_Audio'], height=150, disabled=True)


                # --- Affichage des Paroles Associées ---
                st.markdown("---")
                st.subheader("Paroles")
               
                # Chercher les paroles dans MORCEAUX_GENERES (Prompt_Generation_Paroles)
                lyrics_from_morceau = current_morceau.get('Prompt_Generation_Paroles', '')
               
                # Ou chercher dans PAROLES_EXISTANTES si lié par ID_Morceau
                lyrics_from_existing = paroles_existantes_df[paroles_existantes_df['ID_Morceau'] == current_morceau['ID_Morceau']]['Paroles_Existantes'].iloc[0] if not paroles_existantes_df[paroles_existantes_df['ID_Morceau'] == current_morceau['ID_Morceau']].empty else ''

                displayed_lyrics = lyrics_from_morceau if lyrics_from_morceau else lyrics_from_existing

                if displayed_lyrics:
                    st.text_area("Paroles du Morceau :", value=displayed_lyrics, height=400, key="player_displayed_lyrics")
                else:
                    st.info("Aucune parole disponible pour ce morceau.")
                    st.markdown("Vous pouvez générer des paroles via la page 'Générateur de Contenu' et les lier à ce morceau.")

                # --- Visualiseur Audio Réactif (Conceptuel) ---
                st.markdown("---")
                st.subheader("Visualiseur Audio (Conceptuel)")
                st.info("Un visualiseur audio réactif pourrait être implémenté ici pour ajouter une dimension visuelle à l'écoute. Pour l'instant, c'est une idée à développer (nécessite des librairies complexes ou intégrations JS).")
                st.markdown("![Visualiseur conceptuel](https://via.placeholder.com/600x150?text=Visualiseur+Audio+Conceptuel)", unsafe_allow_html=True)


    else:
        st.info("Votre collection de morceaux est vide. Allez dans 'Mes Morceaux' pour ajouter vos premières créations !") 

# app.py - Suite du code

# --- Page : Mes Albums (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Mes Albums':
    st.header("💿 Mes Albums")
    st.write("Gérez vos albums, leurs pochettes, leurs descriptions et leurs dates de sortie.")

    albums_df = sc.get_all_albums()

    tab_albums_view, tab_albums_add, tab_albums_edit = st.tabs(["Voir/Rechercher Albums", "Ajouter un Nouvel Album", "Mettre à Jour/Supprimer Album"])

    with tab_albums_view:
        st.subheader("Voir et Rechercher des Albums")
        if not albums_df.empty:
            search_album_query = st.text_input("Rechercher par nom d'album ou artiste", key="search_albums")
            if search_album_query:
                filtered_albums_df = albums_df[albums_df.apply(lambda row: search_album_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_albums_df = albums_df
            display_dataframe(ut.format_dataframe_for_display(filtered_albums_df), key="albums_display")
        else:
            st.info("Aucun album enregistré pour le moment.")

    with tab_albums_add:
        st.subheader("Ajouter un Nouvel Album")
        with st.form("add_album_form"):
            new_album_nom = st.text_input("Nom de l'Album", key="add_album_nom")
            new_album_date_sortie = st.date_input("Date de Sortie", value=datetime.now(), key="add_album_date_sortie")
            new_album_artiste_ia = st.selectbox("Artiste IA Principal", [''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist(), key="add_album_artiste_ia")
            new_album_description = st.text_area("Description Thématique de l'Album", key="add_album_description")
           
            # --- Téléchargement de la Pochette ---
            uploaded_album_cover = st.file_uploader("Uploader Image de Pochette (.jpg, .png)", type=["jpg", "png"], key="upload_album_cover")

            submit_new_album = st.form_submit_button("Ajouter l'Album")

            if submit_new_album:
                cover_path_album = ut.save_uploaded_file(uploaded_album_cover, ALBUM_COVERS_DIR)

                new_album_data = {
                    'Nom_Album': new_album_nom,
                    'Date_Sortie': new_album_date_sortie.strftime('%Y-%m-%d'),
                    'ID_Artiste_Principal': new_album_artiste_ia,
                    'Description_Thematique': new_album_description,
                    'URL_Cover_Album': cover_path_album if cover_path_album else ''
                }
                if sc.add_album(new_album_data):
                    st.success(f"Album '{new_album_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout de l'album.")

    with tab_albums_edit:
        st.subheader("Mettre à Jour ou Supprimer un Album")
        if not albums_df.empty:
            album_to_select = st.selectbox(
                "Sélectionnez l'Album à modifier/supprimer",
                albums_df['ID_Album'].tolist(),
                format_func=lambda x: f"{x} - {albums_df[albums_df['ID_Album'] == x]['Nom_Album'].iloc[0]}",
                key="select_album_to_edit"
            )
            if album_to_select:
                selected_album = albums_df[albums_df['ID_Album'] == album_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_album['Nom_Album']}")

                with st.form("update_delete_album_form"):
                    upd_album_nom = st.text_input("Nom de l'Album", value=selected_album['Nom_Album'], key="upd_album_nom")
                    upd_album_date_sortie = st.date_input("Date de Sortie", value=pd.to_datetime(selected_album['Date_Sortie']), key="upd_album_date_sortie")
                    upd_album_artiste_ia = st.selectbox("Artiste IA Principal", [''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist(), index=([''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()).index(selected_album['ID_Artiste_Principal']) if selected_album['ID_Artiste_Principal'] in ([''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()) else 0, key="upd_album_artiste_ia")
                    upd_album_description = st.text_area("Description Thématique de l'Album", value=selected_album['Description_Thematique'], key="upd_album_description")

                    # Affichage de la pochette actuelle et upload pour mise à jour
                    st.markdown("##### Pochette Actuelle")
                    if selected_album['URL_Cover_Album']:
                        st.image(os.path.join(ALBUM_COVERS_DIR, selected_album['URL_Cover_Album']), width=150)
                    else:
                        st.info("Aucune pochette enregistrée.")
                    uploaded_album_cover_upd = st.file_uploader("Uploader Nouvelle Image de Pochette (.jpg, .png)", type=["jpg", "png"], key="upload_album_cover_upd")

                    col_album_form_buttons = st.columns(2)
                    with col_album_form_buttons[0]:
                        submit_update_album = st.form_submit_button("Mettre à Jour l'Album")
                    with col_album_form_buttons[1]:
                        submit_delete_album = st.form_submit_button("Supprimer l'Album")

                    if submit_update_album:
                        cover_path_album_upd = selected_album['URL_Cover_Album']
                        if uploaded_album_cover_upd:
                            new_cover_path_album = ut.save_uploaded_file(uploaded_album_cover_upd, ALBUM_COVERS_DIR)
                            if new_cover_path_album: cover_path_album_upd = new_cover_path_album

                        album_data_update = {
                            'Nom_Album': upd_album_nom,
                            'Date_Sortie': upd_album_date_sortie.strftime('%Y-%m-%d'),
                            'ID_Artiste_Principal': upd_album_artiste_ia,
                            'Description_Thematique': upd_album_description,
                            'URL_Cover_Album': cover_path_album_upd
                        }
                        if sc.update_album(album_to_select, album_data_update):
                            st.success(f"Album '{upd_album_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour de l'album.")

                    if submit_delete_album:
                        if st.warning(f"Voulez-vous vraiment supprimer l'album '{selected_album['Nom_Album']}' (ID: {album_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_album"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["ALBUMS"], 'ID_Album', album_to_select):
                                    st.success(f"Album '{album_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression de l'album.")
        else:
            st.info("Aucun album à modifier ou supprimer pour le moment.")

# --- Page : Mes Artistes IA (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Mes Artistes IA':
    st.header("🤖 Mes Artistes IA")
    st.write("Gérez les profils de vos artistes IA, leurs styles, leurs apparences et leurs métadonnées.")

    artistes_ia_df = sc.get_all_artistes_ia()

    tab_artistes_view, tab_artistes_add, tab_artistes_edit = st.tabs(["Voir/Rechercher Artistes IA", "Ajouter un Nouvel Artiste IA", "Mettre à Jour/Supprimer Artiste IA"])

    with tab_artistes_view:
        st.subheader("Voir et Rechercher des Artistes IA")
        if not artistes_ia_df.empty:
            search_artiste_query = st.text_input("Rechercher par nom d'artiste ou style", key="search_artistes")
            if search_artiste_query:
                filtered_artistes_ia_df = artistes_ia_df[artistes_ia_df.apply(lambda row: search_artiste_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_artistes_ia_df = artistes_ia_df
            display_dataframe(ut.format_dataframe_for_display(filtered_artistes_ia_df), key="artistes_display")
        else:
            st.info("Aucun artiste IA enregistré pour le moment.")

    with tab_artistes_add:
        st.subheader("Ajouter un Nouvel Artiste IA")
        with st.form("add_artiste_ia_form"):
            new_artiste_nom = st.text_input("Nom de l'Artiste IA", key="add_artiste_nom")
            new_artiste_style = st.text_area("Description du Style Musical", key="add_artiste_style")
            new_artiste_apparence = st.text_area("Description de l'Apparence Visuelle (pour les pochettes)", key="add_artiste_apparence")
            submit_new_artiste = st.form_submit_button("Ajouter l'Artiste IA")

            if submit_new_artiste:
                new_artiste_data = {
                    'Nom_Artiste_IA': new_artiste_nom,
                    'Description_Style': new_artiste_style,
                    'Description_Apparence': new_artiste_apparence
                }
                if sc.add_artiste_ia(new_artiste_data):
                    st.success(f"Artiste IA '{new_artiste_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout de l'artiste IA.")

    with tab_artistes_edit:
        st.subheader("Mettre à Jour ou Supprimer un Artiste IA")
        if not artistes_ia_df.empty:
            artiste_to_select = st.selectbox(
                "Sélectionnez l'Artiste IA à modifier/supprimer",
                artistes_ia_df['ID_Artiste_IA'].tolist(),
                format_func=lambda x: f"{x} - {artistes_ia_df[artistes_ia_df['ID_Artiste_IA'] == x]['Nom_Artiste_IA'].iloc[0]}",
                key="select_artiste_to_edit"
            )
            if artiste_to_select:
                selected_artiste = artistes_ia_df[artistes_ia_df['ID_Artiste_IA'] == artiste_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_artiste['Nom_Artiste_IA']}")

                with st.form("update_delete_artiste_form"):
                    upd_artiste_nom = st.text_input("Nom de l'Artiste IA", value=selected_artiste['Nom_Artiste_IA'], key="upd_artiste_nom")
                    upd_artiste_style = st.text_area("Description du Style Musical", value=selected_artiste['Description_Style'], key="upd_artiste_style")
                    upd_artiste_apparence = st.text_area("Description de l'Apparence Visuelle", value=selected_artiste['Description_Apparence'], key="upd_artiste_apparence")

                    col_artiste_form_buttons = st.columns(2)
                    with col_artiste_form_buttons[0]:
                        submit_update_artiste = st.form_submit_button("Mettre à Jour l'Artiste IA")
                    with col_artiste_form_buttons[1]:
                        submit_delete_artiste = st.form_submit_button("Supprimer l'Artiste IA")

                    if submit_update_artiste:
                        artiste_data_update = {
                            'Nom_Artiste_IA': upd_artiste_nom,
                            'Description_Style': upd_artiste_style,
                            'Description_Apparence': upd_artiste_apparence
                        }
                        if sc.update_artiste_ia(artiste_to_select, artiste_data_update):
                            st.success(f"Artiste IA '{upd_artiste_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour de l'artiste IA.")

                    if submit_delete_artiste:
                        if st.warning(f"Voulez-vous vraiment supprimer l'artiste IA '{selected_artiste['Nom_Artiste_IA']}' (ID: {artiste_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_artiste"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["ARTISTES_IA"], 'ID_Artiste_IA', artiste_to_select):
                                    st.success(f"Artiste IA '{artiste_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression de l'artiste IA.")
        else:
            st.info("Aucun artiste IA à modifier ou supprimer pour le moment.") 

# app.py - Suite du code

# --- Page : Stats & Tendances Sim. (Analyse & Stratégie) ---
if st.session_state['current_page'] == 'Stats & Tendances Sim.':
    st.header("📊 Stats & Tendances d'Écoute Simulées")
    st.write("Visualisez des statistiques d'écoute simulées pour vos morceaux, identifiez les tendances et suivez les performances virtuelles.")

    with st.form("stats_simulation_form"):
        st.subheader("Paramètres de Simulation")
        morceaux_pour_stats = st.multiselect(
            "Sélectionnez les Morceaux à Simuler",
            sc.get_all_morceaux()['ID_Morceau'].tolist(),
            format_func=lambda x: f"{x} - {sc.get_all_morceaux()[sc.get_all_morceaux()['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
            key="stats_morceaux_a_simuler"
        )
        nombre_mois_simulation = st.number_input("Nombre de Mois à Simuler", min_value=1, max_value=36, value=12, step=1, key="stats_nombre_mois")
        submit_stats_simulation = st.form_submit_button("Simuler les Statistiques")

        if submit_stats_simulation:
            if morceaux_pour_stats:
                with st.spinner("L'Oracle simule les tendances d'écoute..."):
                    stats_df = go.generate_simulated_streaming_stats(morceaux_pour_stats, nombre_mois_simulation)
                    st.session_state['simulated_stats_df'] = stats_df
                    st.success("Statistiques simulées avec succès !")
            else:
                st.warning("Veuillez sélectionner au moins un morceau.")

    if 'simulated_stats_df' in st.session_state and not st.session_state.simulated_stats_df.empty:
        st.markdown("---")
        st.subheader("Statistiques d'Écoute Simulées")
        display_dataframe(ut.format_dataframe_for_display(st.session_state.simulated_stats_df), key="simulated_stats_display")

        # --- Visualisations (Exemple : Graphique des écoutes par mois) ---
        st.markdown("---")
        st.subheader("Visualisations (Exemple)")
        st.info("Des graphiques interactifs peuvent être ajoutés ici pour visualiser les tendances d'écoute.")
        # Exemple conceptuel :
        # st.line_chart(st.session_state.simulated_stats_df.pivot(index='Mois_Annee', columns='ID_Morceau', values='Ecoutes_Totales'))

# --- Page : Directives Stratégiques (Analyse & Stratégie) ---
if st.session_state['current_page'] == 'Directives Stratégiques':
    st.header("🎯 Directives Stratégiques de l'Oracle")
    st.write("Recevez des conseils stratégiques de l'Oracle pour optimiser vos créations et votre présence musicale.")

    with st.form("strategic_directive_form"):
        st.subheader("Paramètres de la Directive")
        objectif_artiste = st.text_area("Quel est votre objectif principal pour cet artiste/morceau/album ? (ex: 'Maximiser les écoutes sur les plateformes', 'Développer une communauté de fans')", key="directive_objectif")
        morceaux_pour_analyse = st.multiselect(
            "Sélectionnez les Morceaux à Analyser (optionnel)",
            sc.get_all_morceaux()['ID_Morceau'].tolist(),
            format_func=lambda x: f"{x} - {sc.get_all_morceaux()[sc.get_all_morceaux()['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
            key="directive_morceaux_analyse"
        )
        submit_directive = st.form_submit_button("Obtenir la Directive Stratégique")

        if submit_directive:
            if objectif_artiste:
                with st.spinner("L'Oracle élabore une stratégie..."):
                    directive = go.generate_strategic_music_directive(objectif_artiste, morceaux_pour_analyse)
                    st.session_state['strategic_directive'] = directive
                    st.success("Directive stratégique générée !")
            else:
                st.warning("Veuillez définir votre objectif principal.")

    if 'strategic_directive' in st.session_state and st.session_state.strategic_directive:
        st.markdown("---")
        st.subheader("Directive Stratégique de l'Oracle")
        st.text_area("Voici les recommandations de l'Oracle :", value=st.session_state.strategic_directive, height=300, key="directive_output")

# --- Page : Potentiel Viral & Niches (Analyse & Stratégie) ---
if st.session_state['current_page'] == 'Potentiel Viral & Niches':
    st.header("📈 Analyse du Potentiel Viral et des Niches")
    st.write("Identifiez les éléments de vos morceaux qui pourraient attirer un large public et explorez les niches musicales potentielles.")
    st.info("Cette fonctionnalité est en cours de développement. Elle utilisera l'IA pour analyser les caractéristiques de vos morceaux et suggérer des stratégies de viralité et de ciblage.")

    st.warning("Cette section est un placeholder pour une future fonctionnalité. Elle nécessitera une modélisation AI avancée pour analyser les paroles, la musique et les tendances.")

    # Exemple conceptuel :
    # analyzed_morceau = st.selectbox("Sélectionnez un Morceau à Analyser", sc.get_all_morceaux()['ID_Morceau'].tolist(), key="viral_morceau_a_analyser")
    # if analyzed_morceau:
    #     with st.spinner("L'Oracle analyse le potentiel viral..."):
    #         viral_analysis = go.analyze_viral_potential(analyzed_morceau)
    #         st.session_state['viral_analysis'] = viral_analysis
    #         st.success("Analyse du potentiel viral terminée !")

    # if 'viral_analysis' in st.session_state:
    #     st.markdown("---")
    #     st.subheader("Analyse du Potentiel Viral")
    #     st.text_area("Recommandations de l'Oracle :", value=st.session_state.viral_analysis, height=200) 

# app.py - Suite du code

# --- Pages : Bibliothèques de l'Oracle (Gestion des Données de Référence) ---
# (Ce bloc de code est un exemple. Il faudra le dupliquer et l'adapter pour chaque bibliothèque : Styles Musicaux, Styles Lyriques, Thèmes, Moods, etc.)

# --- Page : Styles Musicaux (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Styles Musicaux':
    st.header("🎸 Styles Musicaux")
    st.write("Gérez les styles musicaux utilisés par l'Oracle pour la génération de contenu.")

    styles_musicaux_df = sc.get_all_styles_musicaux()

    tab_styles_view, tab_styles_add, tab_styles_edit = st.tabs(["Voir/Rechercher Styles", "Ajouter un Nouveau Style", "Mettre à Jour/Supprimer Style"])

    with tab_styles_view:
        st.subheader("Voir et Rechercher des Styles Musicaux")
        if not styles_musicaux_df.empty:
            search_style_query = st.text_input("Rechercher par nom de style ou description", key="search_styles")
            if search_style_query:
                filtered_styles_musicaux_df = styles_musicaux_df[styles_musicaux_df.apply(lambda row: search_style_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_styles_musicaux_df = styles_musicaux_df
            display_dataframe(ut.format_dataframe_for_display(filtered_styles_musicaux_df), key="styles_display")
        else:
            st.info("Aucun style musical enregistré pour le moment.")

    with tab_styles_add:
        st.subheader("Ajouter un Nouveau Style Musical")
        with st.form("add_style_musical_form"):
            new_style_nom = st.text_input("Nom du Style Musical", key="add_style_nom")
            new_style_description = st.text_area("Description du Style Musical", key="add_style_description")
            submit_new_style = st.form_submit_button("Ajouter le Style Musical")

            if submit_new_style:
                new_style_data = {
                    'Nom_Style_Musical': new_style_nom,
                    'Description_Style': new_style_description
                }
                if sc.add_style_musical(new_style_data):
                    st.success(f"Style musical '{new_style_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout du style musical.")

    with tab_styles_edit:
        st.subheader("Mettre à Jour ou Supprimer un Style Musical")
        if not styles_musicaux_df.empty:
            style_to_select = st.selectbox(
                "Sélectionnez le Style Musical à modifier/supprimer",
                styles_musicaux_df['ID_Style_Musical'].tolist(),
                format_func=lambda x: f"{x} - {styles_musicaux_df[styles_musicaux_df['ID_Style_Musical'] == x]['Nom_Style_Musical'].iloc[0]}",
                key="select_style_to_edit"
            )
            if style_to_select:
                selected_style = styles_musicaux_df[styles_musicaux_df['ID_Style_Musical'] == style_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_style['Nom_Style_Musical']}")

                with st.form("update_delete_style_form"):
                    upd_style_nom = st.text_input("Nom du Style Musical", value=selected_style['Nom_Style_Musical'], key="upd_style_nom")
                    upd_style_description = st.text_area("Description du Style Musical", value=selected_style['Description_Style'], key="upd_style_description")

                    col_style_form_buttons = st.columns(2)
                    with col_style_form_buttons[0]:
                        submit_update_style = st.form_submit_button("Mettre à Jour le Style Musical")
                    with col_style_form_buttons[1]:
                        submit_delete_style = st.form_submit_button("Supprimer le Style Musical")

                    if submit_update_style:
                        style_data_update = {
                            'Nom_Style_Musical': upd_style_nom,
                            'Description_Style': upd_style_description
                        }
                        if sc.update_style_musical(style_to_select, style_data_update):
                            st.success(f"Style musical '{upd_style_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du style musical.")

                    if submit_delete_style:
                        if st.warning(f"Voulez-vous vraiment supprimer le style musical '{selected_style['Nom_Style_Musical']}' (ID: {style_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_style"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["STYLES_MUSICAUX"], 'ID_Style_Musical', style_to_select):
                                    st.success(f"Style musical '{style_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du style musical.")
        else:
            st.info("Aucun style musical à modifier ou supprimer pour le moment.")

# app.py - Suite du code (Complète et Finale)

# --- Pages : Bibliothèques de l'Oracle (Gestion des Données de Référence) ---

# --- Page : Styles Musicaux (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Styles Musicaux':
    st.header("🎸 Styles Musicaux")
    st.write("Gérez les styles musicaux utilisés par l'Oracle pour la génération de contenu.")

    styles_musicaux_df = sc.get_all_styles_musicaux()

    tab_styles_view, tab_styles_add, tab_styles_edit = st.tabs(["Voir/Rechercher Styles", "Ajouter un Nouveau Style", "Mettre à Jour/Supprimer Style"])

    with tab_styles_view:
        st.subheader("Voir et Rechercher des Styles Musicaux")
        if not styles_musicaux_df.empty:
            search_style_query = st.text_input("Rechercher par nom de style ou description", key="search_styles")
            if search_style_query:
                filtered_styles_musicaux_df = styles_musicaux_df[styles_musicaux_df.apply(lambda row: search_style_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_styles_musicaux_df = styles_musicaux_df
            display_dataframe(ut.format_dataframe_for_display(filtered_styles_musicaux_df), key="styles_display")
        else:
            st.info("Aucun style musical enregistré pour le moment.")

    with tab_styles_add:
        st.subheader("Ajouter un Nouveau Style Musical")
        with st.form("add_style_musical_form"):
            new_style_nom = st.text_input("Nom du Style Musical", key="add_style_nom")
            new_style_description = st.text_area("Description Détaillée", key="add_style_description")
            new_style_artistes_ref = st.text_input("Artistes Références (séparés par des virgules)", key="add_style_artistes_ref")
            new_style_exemples_sonores = st.text_input("Exemples Sonores (URLs ou notes)", key="add_style_exemples_sonores")

            submit_new_style = st.form_submit_button("Ajouter le Style Musical")

            if submit_new_style:
                new_style_data = {
                    'Nom_Style_Musical': new_style_nom,
                    'Description_Detaillee': new_style_description,
                    'Artistes_References': new_style_artistes_ref,
                    'Exemples_Sonores': new_style_exemples_sonores
                }
                if sc.add_style_musical(new_style_data):
                    st.success(f"Style musical '{new_style_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout du style musical.")

    with tab_styles_edit:
        st.subheader("Mettre à Jour ou Supprimer un Style Musical")
        if not styles_musicaux_df.empty:
            style_to_select = st.selectbox(
                "Sélectionnez le Style Musical à modifier/supprimer",
                styles_musicaux_df['ID_Style_Musical'].tolist(),
                format_func=lambda x: f"{x} - {styles_musicaux_df[styles_musicaux_df['ID_Style_Musical'] == x]['Nom_Style_Musical'].iloc[0]}",
                key="select_style_to_edit"
            )
            if style_to_select:
                selected_style = styles_musicaux_df[styles_musicaux_df['ID_Style_Musical'] == style_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_style['Nom_Style_Musical']}")

                with st.form("update_delete_style_form"):
                    upd_style_nom = st.text_input("Nom du Style Musical", value=selected_style['Nom_Style_Musical'], key="upd_style_nom")
                    upd_style_description = st.text_area("Description Détaillée", value=selected_style['Description_Detaillee'], key="upd_style_description")
                    upd_style_artistes_ref = st.text_input("Artistes Références (séparés par des virgules)", value=selected_style['Artistes_References'], key="upd_style_artistes_ref")
                    upd_style_exemples_sonores = st.text_input("Exemples Sonores (URLs ou notes)", value=selected_style['Exemples_Sonores'], key="upd_style_exemples_sonores")

                    col_style_form_buttons = st.columns(2)
                    with col_style_form_buttons[0]:
                        submit_update_style = st.form_submit_button("Mettre à Jour le Style Musical")
                    with col_style_form_buttons[1]:
                        submit_delete_style = st.form_submit_button("Supprimer le Style Musical")

                    if submit_update_style:
                        style_data_update = {
                            'Nom_Style_Musical': upd_style_nom,
                            'Description_Detaillee': upd_style_description,
                            'Artistes_References': upd_style_artistes_ref,
                            'Exemples_Sonores': upd_style_exemples_sonores
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"], 'ID_Style_Musical', style_to_select, style_data_update):
                            st.success(f"Style musical '{upd_style_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du style musical.")

                    if submit_delete_style:
                        if st.warning(f"Voulez-vous vraiment supprimer le style musical '{selected_style['Nom_Style_Musical']}' (ID: {style_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_style"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["STYLES_MUSICAUX_GALACTIQUES"], 'ID_Style_Musical', style_to_select):
                                    st.success(f"Style musical '{style_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du style musical.")
        else:
            st.info("Aucun style musical à modifier ou supprimer pour le moment.")

# --- Page : Styles Lyriques (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Styles Lyriques':
    st.header("📝 Styles Lyriques")
    st.write("Gérez les styles d'écriture lyrique utilisés par l'Oracle pour la génération de paroles.")

    styles_lyriques_df = sc.get_all_styles_lyriques()

    tab_styles_lyriques_view, tab_styles_lyriques_add, tab_styles_lyriques_edit = st.tabs(["Voir/Rechercher Styles", "Ajouter un Nouveau Style", "Mettre à Jour/Supprimer Style"])

    with tab_styles_lyriques_view:
        st.subheader("Voir et Rechercher des Styles Lyriques")
        if not styles_lyriques_df.empty:
            search_style_lyrique_query = st.text_input("Rechercher par nom de style ou description", key="search_styles_lyriques")
            if search_style_lyrique_query:
                filtered_styles_lyriques_df = styles_lyriques_df[styles_lyriques_df.apply(lambda row: search_style_lyrique_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_styles_lyriques_df = styles_lyriques_df
            display_dataframe(ut.format_dataframe_for_display(filtered_styles_lyriques_df), key="styles_lyriques_display")
        else:
            st.info("Aucun style lyrique enregistré pour le moment.")

    with tab_styles_lyriques_add:
        st.subheader("Ajouter un Nouveau Style Lyrique")
        with st.form("add_style_lyrique_form"):
            new_style_lyrique_nom = st.text_input("Nom du Style Lyrique", key="add_style_lyrique_nom")
            new_style_lyrique_description = st.text_area("Description Détaillée", key="add_style_lyrique_description")
            new_style_lyrique_auteurs = st.text_input("Auteurs Références (séparés par des virgules)", key="add_style_lyrique_auteurs")
            new_style_lyrique_exemples = st.text_area("Exemples Textuels Courts", key="add_style_lyrique_exemples")
            submit_new_style_lyrique = st.form_submit_button("Ajouter le Style Lyrique")

            if submit_new_style_lyrique:
                new_style_lyrique_data = {
                    'Nom_Style_Lyrique': new_style_lyrique_nom,
                    'Description_Detaillee': new_style_lyrique_description,
                    'Auteurs_References': new_style_lyrique_auteurs,
                    'Exemples_Textuels_Courts': new_style_lyrique_exemples
                }
                if sc.add_style_lyrique(new_style_lyrique_data):
                    st.success(f"Style lyrique '{new_style_lyrique_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout du style lyrique.")

    with tab_styles_lyriques_edit:
        st.subheader("Mettre à Jour ou Supprimer un Style Lyrique")
        if not styles_lyriques_df.empty:
            style_lyrique_to_select = st.selectbox(
                "Sélectionnez le Style Lyrique à modifier/supprimer",
                styles_lyriques_df['ID_Style_Lyrique'].tolist(),
                format_func=lambda x: f"{x} - {styles_lyriques_df[styles_lyriques_df['ID_Style_Lyrique'] == x]['Nom_Style_Lyrique'].iloc[0]}",
                key="select_style_lyrique_to_edit"
            )
            if style_lyrique_to_select:
                selected_style_lyrique = styles_lyriques_df[styles_lyriques_df['ID_Style_Lyrique'] == style_lyrique_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_style_lyrique['Nom_Style_Lyrique']}")

                with st.form("update_delete_style_lyrique_form"):
                    upd_style_lyrique_nom = st.text_input("Nom du Style Lyrique", value=selected_style_lyrique['Nom_Style_Lyrique'], key="upd_style_lyrique_nom")
                    upd_style_lyrique_description = st.text_area("Description Détaillée", value=selected_style_lyrique['Description_Detaillee'], key="upd_style_lyrique_description")
                    upd_style_lyrique_auteurs = st.text_input("Auteurs Références (séparés par des virgules)", value=selected_style_lyrique['Auteurs_References'], key="upd_style_lyrique_auteurs")
                    upd_style_lyrique_exemples = st.text_area("Exemples Textuels Courts", value=selected_style_lyrique['Exemples_Textuels_Courts'], key="upd_style_lyrique_exemples")

                    col_style_lyrique_form_buttons = st.columns(2)
                    with col_style_lyrique_form_buttons[0]:
                        submit_update_style_lyrique = st.form_submit_button("Mettre à Jour le Style Lyrique")
                    with col_style_lyrique_form_buttons[1]:
                        submit_delete_style_lyrique = st.form_submit_button("Supprimer le Style Lyrique")

                    if submit_update_style_lyrique:
                        style_lyrique_data_update = {
                            'Nom_Style_Lyrique': upd_style_lyrique_nom,
                            'Description_Detaillee': upd_style_lyrique_description,
                            'Auteurs_References': upd_style_lyrique_auteurs,
                            'Exemples_Textuels_Courts': upd_style_lyrique_exemples
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"], 'ID_Style_Lyrique', style_lyrique_to_select, style_lyrique_data_update):
                            st.success(f"Style lyrique '{upd_style_lyrique_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du style lyrique.")

                    if submit_delete_style_lyrique:
                        if st.warning(f"Voulez-vous vraiment supprimer le style lyrique '{selected_style_lyrique['Nom_Style_Lyrique']}' (ID: {style_lyrique_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_style_lyrique"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["STYLES_LYRIQUES_UNIVERS"], 'ID_Style_Lyrique', style_lyrique_to_select):
                                    st.success(f"Style lyrique '{style_lyrique_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du style lyrique.")
        else:
            st.info("Aucun style lyrique à modifier ou supprimer pour le moment.")

# --- Page : Thèmes & Concepts (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Thèmes & Concepts':
    st.header("🌌 Thèmes & Concepts")
    st.write("Gérez les thèmes et concepts que l'Oracle peut explorer dans vos créations.")

    themes_df = sc.get_all_themes()

    tab_themes_view, tab_themes_add, tab_themes_edit = st.tabs(["Voir/Rechercher Thèmes", "Ajouter un Nouveau Thème", "Mettre à Jour/Supprimer Thème"])

    with tab_themes_view:
        st.subheader("Voir et Rechercher des Thèmes")
        if not themes_df.empty:
            search_theme_query = st.text_input("Rechercher par nom de thème ou description", key="search_themes")
            if search_theme_query:
                filtered_themes_df = themes_df[themes_df.apply(lambda row: search_theme_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_themes_df = themes_df
            display_dataframe(ut.format_dataframe_for_display(filtered_themes_df), key="themes_display")
        else:
            st.info("Aucun thème enregistré pour le moment.")

    with tab_themes_add:
        st.subheader("Ajouter un Nouveau Thème")
        with st.form("add_theme_form"):
            new_theme_nom = st.text_input("Nom du Thème", key="add_theme_nom")
            new_theme_description = st.text_area("Description Conceptuelle", key="add_theme_description")
            new_theme_mots_cles = st.text_input("Mots-clés Associés (séparés par des virgules)", key="add_theme_mots_cles")
            submit_new_theme = st.form_submit_button("Ajouter le Thème")

            if submit_new_theme:
                new_theme_data = {
                    'Nom_Theme': new_theme_nom,
                    'Description_Conceptuelle': new_theme_description,
                    'Mots_Cles_Associes': new_theme_mots_cles
                }
                if sc.add_theme(new_theme_data):
                    st.success(f"Thème '{new_theme_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout du thème.")

    with tab_themes_edit:
        st.subheader("Mettre à Jour ou Supprimer un Thème")
        if not themes_df.empty:
            theme_to_select = st.selectbox(
                "Sélectionnez le Thème à modifier/supprimer",
                themes_df['ID_Theme'].tolist(),
                format_func=lambda x: f"{x} - {themes_df[themes_df['ID_Theme'] == x]['Nom_Theme'].iloc[0]}",
                key="select_theme_to_edit"
            )
            if theme_to_select:
                selected_theme = themes_df[themes_df['ID_Theme'] == theme_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_theme['Nom_Theme']}")

                with st.form("update_delete_theme_form"):
                    upd_theme_nom = st.text_input("Nom du Thème", value=selected_theme['Nom_Theme'], key="upd_theme_nom")
                    upd_theme_description = st.text_area("Description Conceptuelle", value=selected_theme['Description_Conceptuelle'], key="upd_theme_description")
                    upd_theme_mots_cles = st.text_input("Mots-clés Associés (séparés par des virgules)", value=selected_theme['Mots_Cles_Associes'], key="upd_theme_mots_cles")

                    col_theme_form_buttons = st.columns(2)
                    with col_theme_form_buttons[0]:
                        submit_update_theme = st.form_submit_button("Mettre à Jour le Thème")
                    with col_theme_form_buttons[1]:
                        submit_delete_theme = st.form_submit_button("Supprimer le Thème")

                    if submit_update_theme:
                        theme_data_update = {
                            'Nom_Theme': upd_theme_nom,
                            'Description_Conceptuelle': upd_theme_description,
                            'Mots_Cles_Associes': upd_theme_mots_cles
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["THEMES_CONSTELLES"], 'ID_Theme', theme_to_select, theme_data_update):
                            st.success(f"Thème '{upd_theme_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du thème.")

                    if submit_delete_theme:
                        if st.warning(f"Voulez-vous vraiment supprimer le thème '{selected_theme['Nom_Theme']}' (ID: {theme_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_theme"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["THEMES_CONSTELLES"], 'ID_Theme', theme_to_select):
                                    st.success(f"Thème '{theme_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du thème.")
        else:
            st.info("Aucun thème à modifier ou supprimer pour le moment.")

# --- Page : Moods & Émotions (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Moods & Émotions':
    st.header("❤️ Moods & Émotions")
    st.write("Gérez les moods et émotions que l'Oracle peut utiliser pour colorer vos créations.")

    moods_df = sc.get_all_moods()

    tab_moods_view, tab_moods_add, tab_moods_edit = st.tabs(["Voir/Rechercher Moods", "Ajouter un Nouveau Mood", "Mettre à Jour/Supprimer Mood"])

    with tab_moods_view:
        st.subheader("Voir et Rechercher des Moods")
        if not moods_df.empty:
            search_mood_query = st.text_input("Rechercher par nom de mood ou description", key="search_moods")
            if search_mood_query:
                filtered_moods_df = moods_df[moods_df.apply(lambda row: search_mood_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_moods_df = moods_df
            display_dataframe(ut.format_dataframe_for_display(filtered_moods_df), key="moods_display")
        else:
            st.info("Aucun mood enregistré pour le moment.")

    with tab_moods_add:
        st.subheader("Ajouter un Nouveau Mood")
        with st.form("add_mood_form"):
            new_mood_nom = st.text_input("Nom du Mood", key="add_mood_nom")
            new_mood_description = st.text_area("Description Nuancée", key="add_mood_description")
            new_mood_intensite = st.number_input("Niveau d'Intensité (1-5)", min_value=1, max_value=5, value=3, step=1, key="add_mood_intensite")
            new_mood_mots_cles = st.text_input("Mots-clés Associés (séparés par des virgules)", key="add_mood_mots_cles")
            new_mood_couleur = st.color_picker("Couleur Associée", key="add_mood_couleur")
            new_mood_tempo_range = st.text_input("Plage de Tempo Suggérée (ex: 80-120)", key="add_mood_tempo_range")
            submit_new_mood = st.form_submit_button("Ajouter le Mood")

            if submit_new_mood:
                new_mood_data = {
                    'Nom_Mood': new_mood_nom,
                    'Description_Nuance': new_mood_description,
                    'Niveau_Intensite': new_mood_intensite,
                    'Mots_Cles_Associes': new_mood_mots_cles,
                    'Couleur_Associee': new_mood_couleur,
                    'Tempo_Range_Suggerer': new_mood_tempo_range
                }
                if sc.add_mood(new_mood_data):
                    st.success(f"Mood '{new_mood_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout du mood.")

    with tab_moods_edit:
        st.subheader("Mettre à Jour ou Supprimer un Mood")
        if not moods_df.empty:
            mood_to_select = st.selectbox(
                "Sélectionnez le Mood à modifier/supprimer",
                moods_df['ID_Mood'].tolist(),
                format_func=lambda x: f"{x} - {moods_df[moods_df['ID_Mood'] == x]['Nom_Mood'].iloc[0]}",
                key="select_mood_to_edit"
            )
            if mood_to_select:
                selected_mood = moods_df[moods_df['ID_Mood'] == mood_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_mood['Nom_Mood']}")

                with st.form("update_delete_mood_form"):
                    upd_mood_nom = st.text_input("Nom du Mood", value=selected_mood['Nom_Mood'], key="upd_mood_nom")
                    upd_mood_description = st.text_area("Description Nuancée", value=selected_mood['Description_Nuance'], key="upd_mood_description")
                    upd_mood_intensite = st.number_input("Niveau d'Intensité (1-5)", min_value=1, max_value=5, value=int(selected_mood['Niveau_Intensite']), step=1, key="upd_mood_intensite")
                    upd_mood_mots_cles = st.text_input("Mots-clés Associés (séparés par des virgules)", value=selected_mood['Mots_Cles_Associes'], key="upd_mood_mots_cles")
                    upd_mood_couleur = st.color_picker("Couleur Associée", value=selected_mood['Couleur_Associee'], key="upd_mood_couleur")
                    upd_mood_tempo_range = st.text_input("Plage de Tempo Suggérée (ex: 80-120)", value=selected_mood['Tempo_Range_Suggerer'], key="upd_mood_tempo_range")

                    col_mood_form_buttons = st.columns(2)
                    with col_mood_form_buttons[0]:
                        submit_update_mood = st.form_submit_button("Mettre à Jour le Mood")
                    with col_mood_form_buttons[1]:
                        submit_delete_mood = st.form_submit_button("Supprimer le Mood")

                    if submit_update_mood:
                        mood_data_update = {
                            'Nom_Mood': upd_mood_nom,
                            'Description_Nuance': upd_mood_description,
                            'Niveau_Intensite': upd_mood_intensite,
                            'Mots_Cles_Associes': upd_mood_mots_cles,
                            'Couleur_Associee': upd_mood_couleur,
                            'Tempo_Range_Suggerer': upd_mood_tempo_range
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"], 'ID_Mood', mood_to_select, mood_data_update):
                            st.success(f"Mood '{upd_mood_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du mood.")

                    if submit_delete_mood:
                        if st.warning(f"Voulez-vous vraiment supprimer le mood '{selected_mood['Nom_Mood']}' (ID: {mood_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_mood"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["MOODS_ET_EMOTIONS"], 'ID_Mood', mood_to_select):
                                    st.success(f"Mood '{mood_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du mood.")
        else:
            st.info("Aucun mood à modifier ou supprimer pour le moment.")


# --- Page : Instruments & Voix (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Instruments & Voix':
    st.header("🎤 Instruments & Voix")
    st.write("Gérez les instruments orchestraux et les styles vocaux utilisés par l'Oracle.")

    instruments_df = sc.get_all_instruments()
    voix_styles_df = sc.get_all_voix_styles()

    tab_instruments, tab_voix_styles = st.tabs(["Instruments Orchestraux", "Styles Vocaux"])

    with tab_instruments:
        st.subheader("Instruments Orchestraux")
        if not instruments_df.empty:
            display_dataframe(ut.format_dataframe_for_display(instruments_df), key="instruments_display")
        else:
            st.info("Aucun instrument enregistré pour le moment.")
       
        # Forms for adding/updating/deleting instruments
        st.markdown("##### Ajouter un Instrument")
        with st.form("add_instrument_form"):
            new_inst_nom = st.text_input("Nom de l'Instrument", key="add_inst_nom")
            new_inst_type = st.text_input("Type d'Instrument", key="add_inst_type")
            new_inst_sonorite = st.text_area("Sonorité Caractéristique", key="add_inst_sonorite")
            new_inst_utilisation = st.text_area("Utilisation Prévalente", key="add_inst_utilisation")
            new_inst_famille = st.text_input("Famille Sonore", key="add_inst_famille")
            submit_new_inst = st.form_submit_button("Ajouter l'Instrument")
            if submit_new_inst:
                new_inst_data = {
                    'Nom_Instrument': new_inst_nom, 'Type_Instrument': new_inst_type,
                    'Sonorité_Caractéristique': new_inst_sonorite, 'Utilisation_Prevalente': new_inst_utilisation,
                    'Famille_Sonore': new_inst_famille
                }
                if sc.add_instrument(new_inst_data):
                    st.success(f"Instrument '{new_inst_nom}' ajouté.")
                    st.experimental_rerun()
                else: st.error("Erreur ajout instrument.")

        st.markdown("##### Mettre à Jour/Supprimer un Instrument")
        if not instruments_df.empty:
            inst_to_select = st.selectbox("Sélectionnez l'Instrument", instruments_df['ID_Instrument'].tolist(), format_func=lambda x: f"{x} - {instruments_df[instruments_df['ID_Instrument'] == x]['Nom_Instrument'].iloc[0]}", key="select_inst_edit")
            if inst_to_select:
                selected_inst = instruments_df[instruments_df['ID_Instrument'] == inst_to_select].iloc[0]
                with st.form("update_delete_instrument_form"):
                    upd_inst_nom = st.text_input("Nom", value=selected_inst['Nom_Instrument'], key="upd_inst_nom")
                    upd_inst_type = st.text_input("Type", value=selected_inst['Type_Instrument'], key="upd_inst_type")
                    upd_inst_sonorite = st.text_area("Sonorité", value=selected_inst['Sonorité_Caractéristique'], key="upd_inst_sonorite")
                    upd_inst_utilisation = st.text_area("Utilisation", value=selected_inst['Utilisation_Prevalente'], key="upd_inst_utilisation")
                    upd_inst_famille = st.text_input("Famille", value=selected_inst['Famille_Sonore'], key="upd_inst_famille")
                    col_inst_buttons = st.columns(2)
                    with col_inst_buttons[0]: submit_upd_inst = st.form_submit_button("Mettre à Jour")
                    with col_inst_buttons[1]: submit_del_inst = st.form_submit_button("Supprimer")
                    if submit_upd_inst:
                        upd_inst_data = {'Nom_Instrument': upd_inst_nom, 'Type_Instrument': upd_inst_type, 'Sonorité_Caractéristique': upd_inst_sonorite, 'Utilisation_Prevalente': upd_inst_utilisation, 'Famille_Sonore': upd_inst_famille}
                        if sc.update_instrument(inst_to_select, upd_inst_data): st.success("Instrument mis à jour."); st.experimental_rerun()
                        else: st.error("Erreur mise à jour.")
                    if submit_del_inst:
                        if st.warning(f"Supprimer '{selected_inst['Nom_Instrument']}' ?"):
                            if st.button("Confirmer Suppression Instrument", key="confirm_del_inst"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["INSTRUMENTS_ORCHESTRAUX"], 'ID_Instrument', inst_to_select):
                                    st.success("Instrument supprimé."); st.experimental_rerun()
                                else: st.error("Erreur suppression.")
        else: st.info("Aucun instrument à modifier.")


    with tab_voix_styles:
        st.subheader("Styles Vocaux")
        if not voix_styles_df.empty:
            display_dataframe(ut.format_dataframe_for_display(voix_styles_df), key="voix_styles_display")
        else:
            st.info("Aucun style vocal enregistré pour le moment.")
       
        # Forms for adding/updating/deleting vocal styles
        st.markdown("##### Ajouter un Style Vocal")
        with st.form("add_vocal_style_form"):
            new_vocal_type = st.text_input("Type Vocal Général", key="add_vocal_type")
            new_vocal_tessiture = st.text_input("Tessiture Spécifique (ex: Soprano, N/A)", key="add_vocal_tessiture")
            new_vocal_style_detaille = st.text_area("Style Vocal Détaillé", key="add_vocal_style_detaille")
            new_vocal_caractere = st.text_input("Caractère Expressif", key="add_vocal_caractere")
            new_vocal_effets = st.text_area("Effets Voix Souhaités", key="add_vocal_effets")
            submit_new_vocal = st.form_submit_button("Ajouter le Style Vocal")
            if submit_new_vocal:
                new_vocal_data = {
                    'Type_Vocal_General': new_vocal_type, 'Tessiture_Specifique': new_vocal_tessiture,
                    'Style_Vocal_Detaille': new_vocal_style_detaille, 'Caractere_Expressif': new_vocal_caractere,
                    'Effets_Voix_Souhaites': new_vocal_effets
                }
                if sc.add_voix_style(new_vocal_data):
                    st.success(f"Style vocal '{new_vocal_style_detaille}' ajouté.")
                    st.experimental_rerun()
                else: st.error("Erreur ajout style vocal.")
       
        st.markdown("##### Mettre à Jour/Supprimer un Style Vocal")
        if not voix_styles_df.empty:
            vocal_to_select = st.selectbox("Sélectionnez le Style Vocal", voix_styles_df['ID_Vocal'].tolist(), format_func=lambda x: f"{x} - {voix_styles_df[voix_styles_df['ID_Vocal'] == x]['Style_Vocal_Detaille'].iloc[0]}", key="select_vocal_edit")
            if vocal_to_select:
                selected_vocal = voix_styles_df[voix_styles_df['ID_Vocal'] == vocal_to_select].iloc[0]
                with st.form("update_delete_vocal_style_form"):
                    upd_vocal_type = st.text_input("Type", value=selected_vocal['Type_Vocal_General'], key="upd_vocal_type")
                    upd_vocal_tessiture = st.text_input("Tessiture", value=selected_vocal['Tessiture_Specifique'], key="upd_vocal_tessiture")
                    upd_vocal_style_detaille = st.text_area("Style Détaillé", value=selected_vocal['Style_Vocal_Detaille'], key="upd_vocal_style_detaille")
                    upd_vocal_caractere = st.text_input("Caractère", value=selected_vocal['Caractere_Expressif'], key="upd_vocal_caractere")
                    upd_vocal_effets = st.text_area("Effets", value=selected_vocal['Effets_Voix_Souhaites'], key="upd_vocal_effets")
                    col_vocal_buttons = st.columns(2)
                    with col_vocal_buttons[0]: submit_upd_vocal = st.form_submit_button("Mettre à Jour")
                    with col_vocal_buttons[1]: submit_del_vocal = st.form_submit_button("Supprimer")
                    if submit_upd_vocal:
                        upd_vocal_data = {'Type_Vocal_General': upd_vocal_type, 'Tessiture_Specifique': upd_vocal_tessiture, 'Style_Vocal_Detaille': upd_vocal_style_detaille, 'Caractere_Expressif': upd_vocal_caractere, 'Effets_Voix_Souhaites': upd_vocal_effets}
                        if sc.update_voix_style(vocal_to_select, upd_vocal_data): st.success("Style vocal mis à jour."); st.experimental_rerun()
                        else: st.error("Erreur mise à jour.")
                    if submit_del_vocal:
                        if st.warning(f"Supprimer '{selected_vocal['Style_Vocal_Detaille']}' ?"):
                            if st.button("Confirmer Suppression Vocal", key="confirm_del_vocal"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["VOIX_ET_STYLES_VOCAUX"], 'ID_Vocal', vocal_to_select):
                                    st.success("Style vocal supprimé."); st.experimental_rerun()
                                else: st.error("Erreur suppression.")
        else: st.info("Aucun style vocal à modifier.")


# --- Page : Structures de Chanson (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Structures de Chanson':
    st.header("🏛️ Structures de Chanson")
    st.write("Gérez les modèles de structure de chanson que l'Oracle peut utiliser.")

    structures_df = sc.get_all_structures_song()

    tab_structures_view, tab_structures_add, tab_structures_edit = st.tabs(["Voir/Rechercher Structures", "Ajouter une Nouvelle Structure", "Mettre à Jour/Supprimer Structure"])

    with tab_structures_view:
        st.subheader("Voir et Rechercher des Structures de Chanson")
        if not structures_df.empty:
            search_structure_query = st.text_input("Rechercher par nom de structure ou schéma", key="search_structures")
            if search_structure_query:
                filtered_structures_df = structures_df[structures_df.apply(lambda row: search_structure_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_structures_df = structures_df
            display_dataframe(ut.format_dataframe_for_display(filtered_structures_df), key="structures_display")
        else:
            st.info("Aucune structure de chanson enregistrée pour le moment.")

    with tab_structures_add:
        st.subheader("Ajouter une Nouvelle Structure de Chanson")
        with st.form("add_structure_form"):
            new_structure_nom = st.text_input("Nom de la Structure", key="add_structure_nom")
            new_structure_schema = st.text_area("Schéma Détaillé (ex: Intro > Couplet > Refrain)", key="add_structure_schema")
            new_structure_notes_ia = st.text_area("Notes d'Application pour l'IA", key="add_structure_notes_ia")
            submit_new_structure = st.form_submit_button("Ajouter la Structure")

            if submit_new_structure:
                new_structure_data = {
                    'Nom_Structure': new_structure_nom,
                    'Schema_Detaille': new_structure_schema,
                    'Notes_Application_IA': new_structure_notes_ia
                }
                if sc.add_structure_song(new_structure_data): # Assumant sc.add_structure_song est défini
                    st.success(f"Structure '{new_structure_nom}' ajoutée avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout de la structure.")

    with tab_structures_edit:
        st.subheader("Mettre à Jour ou Supprimer une Structure de Chanson")
        if not structures_df.empty:
            structure_to_select = st.selectbox(
                "Sélectionnez la Structure à modifier/supprimer",
                structures_df['ID_Structure'].tolist(),
                format_func=lambda x: f"{x} - {structures_df[structures_df['ID_Structure'] == x]['Nom_Structure'].iloc[0]}",
                key="select_structure_to_edit"
            )
            if structure_to_select:
                selected_structure = structures_df[structures_df['ID_Structure'] == structure_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_structure['Nom_Structure']}")

                with st.form("update_delete_structure_form"):
                    upd_structure_nom = st.text_input("Nom de la Structure", value=selected_structure['Nom_Structure'], key="upd_structure_nom")
                    upd_structure_schema = st.text_area("Schéma Détaillé", value=selected_structure['Schema_Detaille'], key="upd_structure_schema")
                    upd_structure_notes_ia = st.text_area("Notes d'Application pour l'IA", value=selected_structure['Notes_Application_IA'], key="upd_structure_notes_ia")

                    col_structure_form_buttons = st.columns(2)
                    with col_structure_form_buttons[0]:
                        submit_update_structure = st.form_submit_button("Mettre à Jour la Structure")
                    with col_structure_form_buttons[1]:
                        submit_delete_structure = st.form_submit_button("Supprimer la Structure")

                    if submit_update_structure:
                        structure_data_update = {
                            'Nom_Structure': upd_structure_nom,
                            'Schema_Detaille': upd_structure_schema,
                            'Notes_Application_IA': upd_structure_notes_ia
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"], 'ID_Structure', structure_to_select, structure_data_update):
                            st.success(f"Structure '{upd_structure_nom}' mise à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour de la structure.")

                    if submit_delete_structure:
                        if st.warning(f"Voulez-vous vraiment supprimer la structure '{selected_structure['Nom_Structure']}' (ID: {structure_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_structure"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["STRUCTURES_SONG_UNIVERSELLES"], 'ID_Structure', structure_to_select):
                                    st.success(f"Structure '{structure_to_select}' supprimée avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression de la structure.")
        else:
            st.info("Aucune structure de chanson à modifier ou supprimer pour le moment.")


# --- Page : Règles de Génération (Bibliothèques de l'Oracle) ---
if st.session_state['current_page'] == 'Règles de Génération':
    st.header("⚖️ Règles de Génération de l'Oracle")
    st.write("Gérez les règles qui guident le comportement de l'Oracle lors de la génération de contenu.")

    regles_df = sc.get_all_regles_generation()

    tab_regles_view, tab_regles_add, tab_regles_edit = st.tabs(["Voir/Rechercher Règles", "Ajouter une Nouvelle Règle", "Mettre à Jour/Supprimer Règle"])

    with tab_regles_view:
        st.subheader("Voir et Rechercher des Règles de Génération")
        if not regles_df.empty:
            search_regle_query = st.text_input("Rechercher par nom de règle ou description", key="search_regles")
            if search_regle_query:
                filtered_regles_df = regles_df[regles_df.apply(lambda row: search_regle_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_regles_df = regles_df
            display_dataframe(ut.format_dataframe_for_display(filtered_regles_df), key="regles_display")
        else:
            st.info("Aucune règle de génération enregistrée pour le moment.")

    with tab_regles_add:
        st.subheader("Ajouter une Nouvelle Règle de Génération")
        with st.form("add_regle_form"):
            new_regle_type = st.text_input("Type de Règle (ex: Contrainte de Langage)", key="add_regle_type")
            new_regle_description = st.text_area("Description de la Règle", key="add_regle_description")
            new_regle_impact = st.text_input("Impact sur Génération (ex: Directive Pré-Génération)", key="add_regle_impact")
            new_regle_statut_actif = st.checkbox("Statut Actif", value=True, key="add_regle_statut_actif")
            submit_new_regle = st.form_submit_button("Ajouter la Règle")

            if submit_new_regle:
                new_regle_data = {
                    'Type_Regle': new_regle_type,
                    'Description_Regle': new_regle_description,
                    'Impact_Sur_Generation': new_regle_impact,
                    'Statut_Actif': 'VRAI' if new_regle_statut_actif else 'FAUX'
                }
                if sc.add_regle_generation(new_regle_data): # Assumant sc.add_regle_generation est défini
                    st.success(f"Règle '{new_regle_type}' ajoutée avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout de la règle.")

    with tab_regles_edit:
        st.subheader("Mettre à Jour ou Supprimer une Règle de Génération")
        if not regles_df.empty:
            regle_to_select = st.selectbox(
                "Sélectionnez la Règle à modifier/supprimer",
                regles_df['ID_Regle'].tolist(),
                format_func=lambda x: f"{x} - {regles_df[regles_df['ID_Regle'] == x]['Type_Regle'].iloc[0]}",
                key="select_regle_to_edit"
            )
            if regle_to_select:
                selected_regle = regles_df[regles_df['ID_Regle'] == regle_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_regle['Type_Regle']}")

                with st.form("update_delete_regle_form"):
                    upd_regle_type = st.text_input("Type de Règle", value=selected_regle['Type_Regle'], key="upd_regle_type")
                    upd_regle_description = st.text_area("Description de la Règle", value=selected_regle['Description_Regle'], key="upd_regle_description")
                    upd_regle_impact = st.text_input("Impact sur Génération", value=selected_regle['Impact_Sur_Generation'], key="upd_regle_impact")
                    upd_regle_statut_actif = st.checkbox("Statut Actif", value=ut.parse_boolean_string(selected_regle['Statut_Actif']), key="upd_regle_statut_actif")

                    col_regle_form_buttons = st.columns(2)
                    with col_regle_form_buttons[0]:
                        submit_update_regle = st.form_submit_button("Mettre à Jour la Règle")
                    with col_regle_form_buttons[1]:
                        submit_delete_regle = st.form_submit_button("Supprimer la Règle")

                    if submit_update_regle:
                        regle_data_update = {
                            'Type_Regle': upd_regle_type,
                            'Description_Regle': upd_regle_description,
                            'Impact_Sur_Generation': upd_regle_impact,
                            'Statut_Actif': 'VRAI' if upd_regle_statut_actif else 'FAUX'
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"], 'ID_Regle', regle_to_select, regle_data_update):
                            st.success(f"Règle '{upd_regle_type}' mise à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour de la règle.")

                    if submit_delete_regle:
                        if st.warning(f"Voulez-vous vraiment supprimer la règle '{selected_regle['Type_Regle']}' (ID: {regle_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_regle"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"], 'ID_Regle', regle_to_select):
                                    st.success(f"Règle '{regle_to_select}' supprimée avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression de la règle.")
        else:
            st.info("Aucune règle de génération à modifier ou supprimer pour le moment.")


# --- Page : Projets en Cours (Outils & Projets) ---
if st.session_state['current_page'] == 'Projets en Cours':
    st.header("🚧 Projets en Cours")
    st.write("Suivez l'avancement de vos projets musicaux, de l'idée à la publication.")

    projets_df = sc.get_all_projets_en_cours()

    tab_projets_view, tab_projets_add, tab_projets_edit = st.tabs(["Voir/Rechercher Projets", "Ajouter un Nouveau Projet", "Mettre à Jour/Supprimer Projet"])

    with tab_projets_view:
        st.subheader("Voir et Rechercher des Projets")
        if not projets_df.empty:
            search_projet_query = st.text_input("Rechercher par nom de projet ou statut", key="search_projets")
            if search_projet_query:
                filtered_projets_df = projets_df[projets_df.apply(lambda row: search_projet_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_projets_df = projets_df
            display_dataframe(ut.format_dataframe_for_display(filtered_projets_df), key="projets_display")
        else:
            st.info("Aucun projet enregistré pour le moment.")

    with tab_projets_add:
        st.subheader("Ajouter un Nouveau Projet")
        with st.form("add_projet_form"):
            new_projet_nom = st.text_input("Nom du Projet", key="add_projet_nom")
            new_projet_type = st.selectbox("Type de Projet", ["Single", "EP", "Album"], key="add_projet_type")
            new_projet_statut = st.selectbox("Statut du Projet", ["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"], key="add_projet_statut")
            new_projet_date_debut = st.date_input("Date de Début", value=datetime.now(), key="add_projet_date_debut")
            new_projet_date_cible_fin = st.date_input("Date Cible de Fin", value=datetime.now() + pd.DateOffset(months=3), key="add_projet_date_cible_fin")
            new_projet_morceaux_lies = st.text_input("IDs Morceaux Liés (séparés par des virgules)", key="add_projet_morceaux_lies")
            new_projet_notes = st.text_area("Notes de Production", key="add_projet_notes")
            new_projet_budget = st.number_input("Budget Estimé (€)", min_value=0.0, value=0.0, step=10.0, key="add_projet_budget")
            submit_new_projet = st.form_submit_button("Ajouter le Projet")

            if submit_new_projet:
                new_projet_data = {
                    'Nom_Projet': new_projet_nom,
                    'Type_Projet': new_projet_type,
                    'Statut_Projet': new_projet_statut,
                    'Date_Debut': new_projet_date_debut.strftime('%Y-%m-%d'),
                    'Date_Cible_Fin': new_projet_date_cible_fin.strftime('%Y-%m-%d'),
                    'ID_Morceaux_Lies': new_projet_morceaux_lies,
                    'Notes_Production': new_projet_notes,
                    'Budget_Estime': new_projet_budget
                }
                if sc.add_projet_en_cours(new_projet_data): # Assumant sc.add_projet_en_cours est défini
                    st.success(f"Projet '{new_projet_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout du projet.")

    with tab_projets_edit:
        st.subheader("Mettre à Jour ou Supprimer un Projet")
        if not projets_df.empty:
            projet_to_select = st.selectbox(
                "Sélectionnez le Projet à modifier/supprimer",
                projets_df['ID_Projet'].tolist(),
                format_func=lambda x: f"{x} - {projets_df[projets_df['ID_Projet'] == x]['Nom_Projet'].iloc[0]}",
                key="select_projet_to_edit"
            )
            if projet_to_select:
                selected_projet = projets_df[projets_df['ID_Projet'] == projet_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_projet['Nom_Projet']}")

                with st.form("update_delete_projet_form"):
                    upd_projet_nom = st.text_input("Nom du Projet", value=selected_projet['Nom_Projet'], key="upd_projet_nom")
                    upd_projet_type = st.selectbox("Type de Projet", ["Single", "EP", "Album"], index=["Single", "EP", "Album"].index(selected_projet['Type_Projet']), key="upd_projet_type")
                    upd_projet_statut = st.selectbox("Statut du Projet", ["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"], index=["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"].index(selected_projet['Statut_Projet']), key="upd_projet_statut")
                    upd_projet_date_debut = st.date_input("Date de Début", value=pd.to_datetime(selected_projet['Date_Debut']), key="upd_projet_date_debut")
                    upd_projet_date_cible_fin = st.date_input("Date Cible de Fin", value=pd.to_datetime(selected_projet['Date_Cible_Fin']), key="upd_projet_date_cible_fin")
                    upd_projet_morceaux_lies = st.text_input("IDs Morceaux Liés (séparés par des virgules)", value=selected_projet['ID_Morceaux_Lies'], key="upd_projet_morceaux_lies")
                    upd_projet_notes = st.text_area("Notes de Production", value=selected_projet['Notes_Production'], key="upd_projet_notes")
                    upd_projet_budget = st.number_input("Budget Estimé (€)", min_value=0.0, value=ut.safe_cast_to_float(selected_projet['Budget_Estime']) if ut.safe_cast_to_float(selected_projet['Budget_Estime']) is not None else 0.0, step=10.0, key="upd_projet_budget")

                    col_projet_form_buttons = st.columns(2)
                    with col_projet_form_buttons[0]:
                        submit_update_projet = st.form_submit_button("Mettre à Jour le Projet")
                    with col_projet_form_buttons[1]:
                        submit_delete_projet = st.form_submit_button("Supprimer le Projet")

                    if submit_update_projet:
                        projet_data_update = {
                            'Nom_Projet': upd_projet_nom,
                            'Type_Projet': upd_projet_type,
                            'Statut_Projet': upd_projet_statut,
                            'Date_Debut': upd_projet_date_debut.strftime('%Y-%m-%d'),
                            'Date_Cible_Fin': upd_projet_date_cible_fin.strftime('%Y-%m-%d'),
                            'ID_Morceaux_Lies': upd_projet_morceaux_lies,
                            'Notes_Production': upd_projet_notes,
                            'Budget_Estime': upd_projet_budget
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["PROJETS_EN_COURS"], 'ID_Projet', projet_to_select, projet_data_update):
                            st.success(f"Projet '{upd_projet_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du projet.")

                    if submit_delete_projet:
                        if st.warning(f"Voulez-vous vraiment supprimer le projet '{selected_projet['Nom_Projet']}' (ID: {projet_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_projet"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["PROJETS_EN_COURS"], 'ID_Projet', projet_to_select):
                                    st.success(f"Projet '{projet_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression du projet.")
        else:
            st.info("Aucun projet à modifier ou supprimer pour le moment.")


# --- Page : Outils IA Référencés (Outils & Projets) ---
if st.session_state['current_page'] == 'Outils IA Référencés':
    st.header("🛠️ Outils IA Référencés")
    st.write("Consultez les outils IA externes référencés qui peuvent compléter les capacités de l'Architecte Ω.")

    outils_ia_df = sc.get_all_outils_ia()

    tab_outils_view, tab_outils_add, tab_outils_edit = st.tabs(["Voir/Rechercher Outils", "Ajouter un Nouvel Outil", "Mettre à Jour/Supprimer Outil"])

    with tab_outils_view:
        st.subheader("Voir et Rechercher des Outils IA")
        if not outils_ia_df.empty:
            search_outil_query = st.text_input("Rechercher par nom d'outil ou fonction", key="search_outils")
            if search_outil_query:
                filtered_outils_df = outils_ia_df[outils_ia_df.apply(lambda row: search_outil_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_outils_df = outils_ia_df
            display_dataframe(ut.format_dataframe_for_display(filtered_outils_df), key="outils_display")
           
            st.markdown("---")
            st.subheader("Liens Directs vers les Outils")
            for index, row in filtered_outils_df.iterrows():
                if row['URL_Outil']:
                    st.markdown(f"**[{row['Nom_Outil']}]({row['URL_Outil']})** : {row['Description_Fonctionnalite']}")
        else:
            st.info("Aucun outil IA enregistré pour le moment.")

    with tab_outils_add:
        st.subheader("Ajouter un Nouvel Outil IA")
        with st.form("add_outil_ia_form"):
            new_outil_nom = st.text_input("Nom de l'Outil", key="add_outil_nom")
            new_outil_description = st.text_area("Description de la Fonctionnalité", key="add_outil_description")
            new_outil_type = st.text_input("Type de Fonction (ex: Génération audio, Mastering)", key="add_outil_type")
            new_outil_url = st.text_input("URL de l'Outil", key="add_outil_url")
            new_outil_compat = st.checkbox("Compatibilité API (Oui/Non)", key="add_outil_compat")
            new_outil_prix = st.text_input("Prix Approximatif", key="add_outil_prix")
            new_outil_eval = st.number_input("Évaluation Gardien (1-5)", min_value=1, max_value=5, value=3, step=1, key="add_outil_eval")
            new_outil_notes = st.text_area("Notes d'Utilisation", key="add_outil_notes")
            submit_new_outil = st.form_submit_button("Ajouter l'Outil")

            if submit_new_outil:
                new_outil_data = {
                    'Nom_Outil': new_outil_nom,
                    'Description_Fonctionnalite': new_outil_description,
                    'Type_Fonction': new_outil_type,
                    'URL_Outil': new_outil_url,
                    'Compatibilite_API': 'OUI' if new_outil_compat else 'NON',
                    'Prix_Approximatif': new_outil_prix,
                    'Evaluation_Gardien': new_outil_eval,
                    'Notes_Utilisation': new_outil_notes
                }
                if sc.add_outil_ia(new_outil_data): # Assumant sc.add_outil_ia est défini
                    st.success(f"Outil '{new_outil_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout de l'outil.")

    with tab_outils_edit:
        st.subheader("Mettre à Jour ou Supprimer un Outil IA")
        if not outils_ia_df.empty:
            outil_to_select = st.selectbox(
                "Sélectionnez l'Outil IA à modifier/supprimer",
                outils_ia_df['ID_Outil'].tolist(),
                format_func=lambda x: f"{x} - {outils_ia_df[outils_ia_df['ID_Outil'] == x]['Nom_Outil'].iloc[0]}",
                key="select_outil_to_edit"
            )
            if outil_to_select:
                selected_outil = outils_ia_df[outils_ia_df['ID_Outil'] == outil_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_outil['Nom_Outil']}")

                with st.form("update_delete_outil_form"):
                    upd_outil_nom = st.text_input("Nom de l'Outil", value=selected_outil['Nom_Outil'], key="upd_outil_nom")
                    upd_outil_description = st.text_area("Description de la Fonctionnalité", value=selected_outil['Description_Fonctionnalite'], key="upd_outil_description")
                    upd_outil_type = st.text_input("Type de Fonction", value=selected_outil['Type_Fonction'], key="upd_outil_type")
                    upd_outil_url = st.text_input("URL de l'Outil", value=selected_outil['URL_Outil'], key="upd_outil_url")
                    upd_outil_compat = st.checkbox("Compatibilité API (Oui/Non)", value=ut.parse_boolean_string(selected_outil['Compatibilite_API']), key="upd_outil_compat")
                    upd_outil_prix = st.text_input("Prix Approximatif", value=selected_outil['Prix_Approximatif'], key="upd_outil_prix")
                    upd_outil_eval = st.number_input("Évaluation Gardien (1-5)", min_value=1, max_value=5, value=int(selected_outil['Evaluation_Gardien']), step=1, key="upd_outil_eval")
                    upd_outil_notes = st.text_area("Notes d'Utilisation", value=selected_outil['Notes_Utilisation'], key="upd_outil_notes")

                    col_outil_form_buttons = st.columns(2)
                    with col_outil_form_buttons[0]:
                        submit_update_outil = st.form_submit_button("Mettre à Jour l'Outil")
                    with col_outil_form_buttons[1]:
                        submit_delete_outil = st.form_submit_button("Supprimer l'Outil")

                    if submit_update_outil:
                        outil_data_update = {
                            'Nom_Outil': upd_outil_nom,
                            'Description_Fonctionnalite': upd_outil_description,
                            'Type_Fonction': upd_outil_type,
                            'URL_Outil': upd_outil_url,
                            'Compatibilite_API': 'OUI' if upd_outil_compat else 'NON',
                            'Prix_Approximatif': upd_outil_prix,
                            'Evaluation_Gardien': upd_outil_eval,
                            'Notes_Utilisation': upd_outil_notes
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"], 'ID_Outil', outil_to_select, outil_data_update):
                            st.success(f"Outil '{upd_outil_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour de l'outil.")

                    if submit_delete_outil:
                        if st.warning(f"Voulez-vous vraiment supprimer l'outil '{selected_outil['Nom_Outil']}' (ID: {outil_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_outil"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"], 'ID_Outil', outil_to_select):
                                    st.success(f"Outil '{outil_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression de l'outil.")
        else:
            st.info("Aucun outil IA à modifier ou supprimer pour le moment.")


# --- Page : Timeline Événements (Outils & Projets) ---
if st.session_state['current_page'] == 'Timeline Événements':
    st.header("🗓️ Timeline des Événements Culturels")
    st.write("Consultez et gérez les événements majeurs pour planifier vos lancements musicaux et campagnes promotionnelles.")

    timeline_df = sc.get_all_timeline_evenements()

    tab_timeline_view, tab_timeline_add, tab_timeline_edit = st.tabs(["Voir/Rechercher Événements", "Ajouter un Nouvel Événement", "Mettre à Jour/Supprimer Événement"])

    with tab_timeline_view:
        st.subheader("Voir et Rechercher des Événements")
        if not timeline_df.empty:
            search_timeline_query = st.text_input("Rechercher par nom d'événement ou genre", key="search_timeline")
            if search_timeline_query:
                filtered_timeline_df = timeline_df[timeline_df.apply(lambda row: search_timeline_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_timeline_df = timeline_df
            display_dataframe(ut.format_dataframe_for_display(filtered_timeline_df), key="timeline_display")
        else:
            st.info("Aucun événement enregistré pour le moment.")

    with tab_timeline_add:
        st.subheader("Ajouter un Nouvel Événement")
        with st.form("add_timeline_event_form"):
            new_event_nom = st.text_input("Nom de l'Événement", key="add_event_nom")
            new_event_date_debut = st.date_input("Date de Début", value=datetime.now(), key="add_event_date_debut")
            new_event_date_fin = st.date_input("Date de Fin", value=datetime.now(), key="add_event_date_fin")
            new_event_type = st.selectbox("Type d'Événement", ["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"], key="add_event_type")
            new_event_genre = st.text_input("Genre(s) Associé(s) (séparés par des virgules)", key="add_event_genre")
            new_event_public = st.text_input("Public(s) Associé(s) (IDs séparés par virgules)", key="add_event_public")
            new_event_notes = st.text_area("Notes Stratégiques", key="add_event_notes")
            submit_new_event = st.form_submit_button("Ajouter l'Événement")

            if submit_new_event:
                new_event_data = {
                    'Nom_Evenement': new_event_nom,
                    'Date_Debut': new_event_date_debut.strftime('%Y-%m-%d'),
                    'Date_Fin': new_event_date_fin.strftime('%Y-%m-%d'),
                    'Type_Evenement': new_event_type,
                    'Genre_Associe': new_event_genre,
                    'Public_Associe': new_event_public,
                    'Notes_Strategiques': new_event_notes
                }
                if sc.add_timeline_event(new_event_data): # Assumant sc.add_timeline_event est défini
                    st.success(f"Événement '{new_event_nom}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout de l'événement.")

    with tab_timeline_edit:
        st.subheader("Mettre à Jour ou Supprimer un Événement")
        if not timeline_df.empty:
            event_to_select = st.selectbox(
                "Sélectionnez l'Événement à modifier/supprimer",
                timeline_df['ID_Evenement'].tolist(),
                format_func=lambda x: f"{x} - {timeline_df[timeline_df['ID_Evenement'] == x]['Nom_Evenement'].iloc[0]}",
                key="select_event_to_edit"
            )
            if event_to_select:
                selected_event = timeline_df[timeline_df['ID_Evenement'] == event_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_event['Nom_Evenement']}")

                with st.form("update_delete_event_form"):
                    upd_event_nom = st.text_input("Nom de l'Événement", value=selected_event['Nom_Evenement'], key="upd_event_nom")
                    upd_event_date_debut = st.date_input("Date de Début", value=pd.to_datetime(selected_event['Date_Debut']), key="upd_event_date_debut")
                    upd_event_date_fin = st.date_input("Date de Fin", value=pd.to_datetime(selected_event['Date_Fin']), key="upd_event_date_fin")
                    upd_event_type = st.selectbox("Type d'Événement", ["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"], index=["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"].index(selected_event['Type_Evenement']), key="upd_event_type")
                    upd_event_genre = st.text_input("Genre(s) Associé(s)", value=selected_event['Genre_Associe'], key="upd_event_genre")
                    upd_event_public = st.text_input("Public(s) Associé(s)", value=selected_event['Public_Associe'], key="upd_event_public")
                    upd_event_notes = st.text_area("Notes Stratégiques", value=selected_event['Notes_Strategiques'], key="upd_event_notes")

                    col_event_form_buttons = st.columns(2)
                    with col_event_form_buttons[0]:
                        submit_update_event = st.form_submit_button("Mettre à Jour l'Événement")
                    with col_event_form_buttons[1]:
                        submit_delete_event = st.form_submit_button("Supprimer l'Événement")

                    if submit_update_event:
                        event_data_update = {
                            'Nom_Evenement': upd_event_nom,
                            'Date_Debut': upd_event_date_debut.strftime('%Y-%m-%d'),
                            'Date_Fin': upd_event_date_fin.strftime('%Y-%m-%d'),
                            'Type_Evenement': upd_event_type,
                            'Genre_Associe': upd_event_genre,
                            'Public_Associe': upd_event_public,
                            'Notes_Strategiques': upd_event_notes
                        }
                        if sc.update_row_in_sheet(WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"], 'ID_Evenement', event_to_select, event_data_update):
                            st.success(f"Événement '{upd_event_nom}' mis à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour de l'événement.")

                    if submit_delete_event:
                        if st.warning(f"Voulez-vous vraiment supprimer l'événement '{selected_event['Nom_Evenement']}' (ID: {event_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_event"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["TIMELINE_EVENEMENTS_CULTURELS"], 'ID_Evenement', event_to_select):
                                    st.success(f"Événement '{event_to_select}' supprimé avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression de l'événement.")
        else:
            st.info("Aucun événement à modifier ou supprimer pour le moment.")


# --- Page : Historique de l'Oracle (Logging) ---
if st.session_state['current_page'] == "Historique de l'Oracle":
    st.header("📚 Historique de l'Oracle")
    st.write("Consultez l'historique de toutes vos interactions avec l'Oracle Architecte et évaluez ses générations.")

    historique_df = sc.get_all_historique_generations()

    tab_historique_view, tab_historique_feedback = st.tabs(["Voir Historique", "Donner du Feedback"])

    with tab_historique_view:
        st.subheader("Historique des Générations")
        if not historique_df.empty:
            search_hist_query = st.text_input("Rechercher dans l'historique", key="search_historique")
            if search_hist_query:
                filtered_hist_df = historique_df[historique_df.apply(lambda row: search_hist_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_hist_df = historique_df
            display_dataframe(ut.format_dataframe_for_display(filtered_hist_df), key="historique_display")
        else:
            st.info("Aucun historique de génération pour le moment.")

    with tab_historique_feedback:
        st.subheader("Donner du Feedback à l'Oracle")
        if not historique_df.empty:
            # Filtrer les entrées sans évaluation
            unrated_generations = historique_df[historique_df['Evaluation_Manuelle'] == '']
            if not unrated_generations.empty:
                gen_to_feedback_id = st.selectbox(
                    "Sélectionnez une génération à évaluer",
                    unrated_generations['ID_GenLog'].tolist(),
                    format_func=lambda x: f"{x} - {unrated_generations[unrated_generations['ID_GenLog'] == x]['Type_Generation'].iloc[0]} ({unrated_generations[unrated_generations['ID_GenLog'] == x]['Date_Heure'].iloc[0]})",
                    key="select_gen_to_feedback"
                )
                if gen_to_feedback_id:
                    selected_gen = unrated_generations[unrated_generations['ID_GenLog'] == gen_to_feedback_id].iloc[0]

                    st.markdown("---")
                    st.write(f"**Génération sélectionnée :** {selected_gen['Type_Generation']} du {selected_gen['Date_Heure']}")
                    st.text_area("Prompt envoyé :", value=selected_gen['Prompt_Envoye_Full'], height=150, disabled=True)
                    st.text_area("Réponse reçue :", value=selected_gen['Reponse_Recue_Full'], height=200, disabled=True)

                    with st.form("feedback_form"):
                        evaluation = st.slider("Évaluation de la qualité (1: Faible, 5: Excellente)", min_value=1, max_value=5, value=3, step=1, key="feedback_evaluation")
                        commentaire = st.text_area("Commentaire ou suggestion d'amélioration", key="feedback_commentaire")
                        tags_feedback = st.text_input("Tags de feedback (ex: 'trop long', 'mélodie parfaite', 'style non respecté')", key="feedback_tags")
                       
                        submit_feedback = st.form_submit_button("Soumettre le Feedback")

                        if submit_feedback:
                            feedback_data = {
                                'Evaluation_Manuelle': str(evaluation), # Convertir en string pour le Google Sheet
                                'Commentaire_Qualitatif': commentaire,
                                'Tags_Feedback': tags_feedback
                            }
                            if sc.update_row_in_sheet(WORKSHEET_NAMES["HISTORIQUE_GENERATIONS"], 'ID_GenLog', gen_to_feedback_id, feedback_data):
                                st.success("Feedback soumis avec succès ! L'Oracle vous remercie pour votre contribution.")
                                st.experimental_rerun()
                            else:
                                st.error("Échec de la soumission du feedback.")
            else:
                st.info("Toutes les générations ont été évaluées, ou il n'y a pas encore d'historique.")
        else:
            st.info("Aucun historique de génération pour le moment.")


# --- Page : Paroles Existantes (Gestion du Sanctuaire) ---
if st.session_state['current_page'] == 'Paroles Existantes':
    st.header("📜 Paroles Existantes (Manuelles)")
    st.write("Consultez et gérez vos propres paroles de chansons que l'Oracle peut utiliser comme référence.")

    paroles_existantes_df = sc.get_all_paroles_existantes()

    tab_paroles_view, tab_paroles_add, tab_paroles_edit = st.tabs(["Voir/Rechercher Paroles", "Ajouter de Nouvelles Paroles", "Mettre à Jour/Supprimer Paroles"])

    with tab_paroles_view:
        st.subheader("Voir et Rechercher des Paroles Existantes")
        if not paroles_existantes_df.empty:
            search_paroles_query = st.text_input("Rechercher par titre ou contenu", key="search_paroles_existantes")
            if search_paroles_query:
                filtered_paroles_df = paroles_existantes_df[paroles_existantes_df.apply(lambda row: search_paroles_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_paroles_df = paroles_existantes_df
            display_dataframe(ut.format_dataframe_for_display(filtered_paroles_df), key="paroles_existantes_display")
        else:
            st.info("Aucune parole existante enregistrée pour le moment.")

    with tab_paroles_add:
        st.subheader("Ajouter de Nouvelles Paroles Manuelles")
        with st.form("add_paroles_form"):
            new_paroles_titre_morceau = st.text_input("Titre du Morceau (pour ces paroles)", key="add_paroles_titre_morceau")
            new_paroles_artiste = st.text_input("Artiste Principal (ex: Le Gardien)", key="add_paroles_artiste")
            new_paroles_genre = st.text_input("Genre Musical (pour référence)", key="add_paroles_genre")
            new_paroles_texte = st.text_area("Collez les Paroles ici", height=300, key="add_paroles_texte")
            new_paroles_notes = st.text_area("Notes (ex: A retravailler, version finale)", key="add_paroles_notes")
            submit_new_paroles = st.form_submit_button("Ajouter les Paroles")

            if submit_new_paroles:
                new_paroles_data = {
                    'Titre_Morceau': new_paroles_titre_morceau,
                    'Artiste_Principal': new_paroles_artiste,
                    'Genre_Musical': new_paroles_genre,
                    'Paroles_Existantes': new_paroles_texte,
                    'Notes': new_paroles_notes
                }
                if sc.add_paroles_existantes(new_paroles_data): # Assumant sc.add_paroles_existantes est défini
                    st.success(f"Paroles pour '{new_paroles_titre_morceau}' ajoutées avec succès !")
                    st.experimental_rerun()
                else:
                    st.error("Échec de l'ajout des paroles.")

    with tab_paroles_edit:
        st.subheader("Mettre à Jour ou Supprimer des Paroles Existantes")
        if not paroles_existantes_df.empty:
            paroles_to_select = st.selectbox(
                "Sélectionnez les Paroles à modifier/supprimer",
                paroles_existantes_df['ID_Morceau'].tolist(),
                format_func=lambda x: f"{x} - {paroles_existantes_df[paroles_existantes_df['ID_Morceau'] == x]['Titre_Morceau'].iloc[0]}",
                key="select_paroles_to_edit"
            )
            if paroles_to_select:
                selected_paroles = paroles_existantes_df[paroles_existantes_df['ID_Morceau'] == paroles_to_select].iloc[0]

                st.markdown("---")
                st.write(f"**Modification de :** {selected_paroles['Titre_Morceau']}")

                with st.form("update_delete_paroles_form"):
                    upd_paroles_titre_morceau = st.text_input("Titre du Morceau", value=selected_paroles['Titre_Morceau'], key="upd_paroles_titre_morceau")
                    upd_paroles_artiste = st.text_input("Artiste Principal", value=selected_paroles['Artiste_Principal'], key="upd_paroles_artiste")
                    upd_paroles_genre = st.text_input("Genre Musical", value=selected_paroles['Genre_Musical'], key="upd_paroles_genre")
                    upd_paroles_texte = st.text_area("Paroles", value=selected_paroles['Paroles_Existantes'], height=300, key="upd_paroles_texte")
                    upd_paroles_notes = st.text_area("Notes", value=selected_paroles['Notes'], key="upd_paroles_notes")

                    col_paroles_form_buttons = st.columns(2)
                    with col_paroles_form_buttons[0]:
                        submit_update_paroles = st.form_submit_button("Mettre à Jour les Paroles")
                    with col_paroles_form_buttons[1]:
                        submit_delete_paroles = st.form_submit_button("Supprimer les Paroles")

                    if submit_update_paroles:
                        paroles_data_update = {
                            'Titre_Morceau': upd_paroles_titre_morceau,
                            'Artiste_Principal': upd_paroles_artiste,
                            'Genre_Musical': upd_paroles_genre,
                            'Paroles_Existantes': upd_paroles_texte,
                            'Notes': upd_paroles_notes
                        }
                        if sc.update_paroles_existantes(paroles_to_select, paroles_data_update):
                            st.success(f"Paroles pour '{upd_paroles_titre_morceau}' mises à jour avec succès !")
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour des paroles.")

                    if submit_delete_paroles:
                        if st.warning(f"Voulez-vous vraiment supprimer les paroles pour '{selected_paroles['Titre_Morceau']}' (ID: {paroles_to_select}) ?"):
                            if st.button("Confirmer la suppression", key="confirm_delete_paroles"):
                                if sc.delete_row_from_sheet(WORKSHEET_NAMES["PAROLES_EXISTANTES"], 'ID_Morceau', paroles_to_select):
                                    st.success(f"Paroles '{paroles_to_select}' supprimées avec succès !")
                                    st.experimental_rerun()
                                else:
                                    st.error("Échec de la suppression des paroles.")
        else:
            st.info("Aucune parole existante à modifier ou supprimer pour le moment.")

# --- FIN DU FICHIER app.py --- 
