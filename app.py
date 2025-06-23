import streamlit as st
import os
import pandas as pd
from datetime import datetime
import base64

# Importation de nos modules personnalisés
# Assurez-vous que config.py, sheets_connector.py, gemini_oracle.py, utils.py sont dans le même dossier
from config import (
    SHEET_NAME, WORKSHEET_NAMES, ASSETS_DIR, AUDIO_CLIPS_DIR, SONG_COVERS_DIR, ALBUM_COVERS_DIR, GENERATED_TEXTS_DIR, GEMINI_API_KEY_NAME
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
if 'app_initialized' not in st.session_state:
    st.session_state['app_initialized'] = True
    st.session_state['current_page'] = 'Accueil'
    st.session_state['user_id'] = 'Gardien' # Peut être étendu pour des profils utilisateur
    st.session_state['theme_mode'] = 'light' # Ou 'dark', si tu veux un toggle plus tard

    # Initialisation des états pour les confirmations de suppression pour chaque type de données
    delete_keys = [
        'morceau', 'album', 'artiste', 'style', 'style_lyrique', 'theme', 'mood',
        'instrument', 'vocal', 'structure', 'regle', 'projet', 'outil', 'event', 'paroles'
    ]
    for key in delete_keys:
        st.session_state[f'confirm_delete_{key}_id'] = None
        st.session_state[f'confirm_delete_{key}_name'] = None

# --- Vérification et Création des Dossiers d'Assets ---
for directory in [ASSETS_DIR, AUDIO_CLIPS_DIR, SONG_COVERS_DIR, ALBUM_COVERS_DIR, GENERATED_TEXTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# --- Fonctions Utilitaires d'Affichage pour l'UI ---
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

# Tu peux choisir une image de fond par défaut ici si tu en as une dans le dossier assets.
# set_background_image(os.path.join(ASSETS_DIR, "background_default.jpg")) # Décommenter et adapter

# --- Menu de Navigation Latéral ---
st.sidebar.title("ARCHITECTE Ω - Menu")

menu_options = {
    "Accueil": "🏠 Vue d'ensemble de l'empire",
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
            if st.sidebar.button(f"{value}", key=f"menu_button_{full_key}"):
                st.session_state['current_page'] = key
                # Réinitialiser tous les états de confirmation de suppression à chaque changement de page
                delete_keys = [
                    'morceau', 'album', 'artiste', 'style', 'style_lyrique', 'theme', 'mood',
                    'instrument', 'vocal', 'structure', 'regle', 'projet', 'outil', 'event', 'paroles'
                ]
                for d_key in delete_keys:
                    st.session_state[f'confirm_delete_{d_key}_id'] = None
                    st.session_state[f'confirm_delete_{d_key}_name'] = None


# Affichage dynamique du menu
display_menu(menu_options)

# --- Fonctions Génériques pour les CRUD de Feuilles Google ---

def _get_options_for_selectbox(df: pd.DataFrame, id_col: str, name_col: str) -> list:
    """Génère une liste d'options formatées pour les selectbox à partir d'un DataFrame."""
    if df.empty:
        return ['']
    # Assurez-vous que name_col existe, sinon utilisez id_col pour le display
    display_name_col = name_col if name_col in df.columns else id_col
    return [''] + df.apply(lambda row: f"{row[id_col]} - {row[display_name_col]}", axis=1).tolist()

def _get_id_from_display_string(display_string: str) -> str:
    """Extrait l'ID d'une chaîne de format 'ID - Nom'."""
    if display_string and ' - ' in display_string:
        return display_string.split(' - ')[0].strip()
    return ''

def _render_add_tab(sheet_name_key: str, fields_config: dict, add_function, form_key: str):
    """
    Rend un onglet d'ajout générique pour une feuille Google Sheet.
    :param sheet_name_key: La clé de l'onglet dans WORKSHEET_NAMES (ex: "MORCEAUX_GENERES").
    :param fields_config: Dictionnaire de la configuration des champs {col_name: {'type': 'text_input', 'label': 'Label', 'options': [], 'default': ''}}.
    :param add_function: La fonction sc.add_x à appeler.
    :param form_key: Clé unique pour le formulaire Streamlit.
    """
    st.subheader(f"Ajouter un Nouveau Entrée dans {WORKSHEET_NAMES[sheet_name_key]}")
    with st.form(form_key):
        new_data = {}
        for col_name, config in fields_config.items():
            # Skip file upload configs here, they are handled separately
            if col_name.startswith('file_upload_'):
                continue

            label = config.get('label', col_name)
            input_type = config.get('type', 'text_input')
            default_value = config.get('default', '')
            options = config.get('options', [])
            required = config.get('required', False) # Keep required for internal validation if needed

            if input_type == 'text_input':
                new_data[col_name] = st.text_input(label, value=default_value, key=f"{form_key}_{col_name}")
            elif input_type == 'text_area':
                new_data[col_name] = st.text_area(label, value=default_value, key=f"{form_key}_{col_name}", height=config.get('height', None))
            elif input_type == 'selectbox':
                if callable(options): # If options is a function (e.g., sc.get_all_styles_musicaux)
                    resolved_options_df = options()
                    # Determine ID and Name columns for display in selectbox
                    id_col_for_select = config.get('id_col_for_options', col_name) # Default to col_name
                    name_col_for_select = config.get('name_col_for_options', col_name) # Default to col_name
                    
                    # Heuristics for common cases
                    if 'ID_Style_Musical' in col_name or 'Genre' in col_name:
                        id_col_for_select = 'ID_Style_Musical'
                        name_col_for_select = 'Nom_Style_Musical'
                    elif 'ID_Mood' in col_name or 'Mood' in col_name:
                        id_col_for_select = 'ID_Mood'
                        name_col_for_select = 'Nom_Mood'
                    elif 'ID_Theme' in col_name or 'Theme' in col_name:
                        id_col_for_select = 'ID_Theme'
                        name_col_for_select = 'Nom_Theme'
                    elif 'ID_Artiste_IA' in col_name or 'Artiste_IA' in col_name:
                        id_col_for_select = 'ID_Artiste_IA'
                        name_col_for_select = 'Nom_Artiste_IA'
                    elif 'ID_Album' in col_name or 'Album' in col_name:
                        id_col_for_select = 'ID_Album'
                        name_col_for_select = 'Nom_Album'
                    elif 'ID_Style_Lyrique' in col_name or 'Style_Lyrique' in col_name:
                        id_col_for_select = 'ID_Style_Lyrique'
                        name_col_for_select = 'Nom_Style_Lyrique'
                    elif 'ID_Structure' in col_name or 'Structure_Chanson' in col_name:
                        id_col_for_select = 'ID_Structure'
                        name_col_for_select = 'Nom_Structure'
                    elif 'Type_Voix_Desiree' in col_name or 'Type_Vocal_General' in col_name:
                        id_col_for_select = 'ID_Vocal'
                        name_col_for_select = 'Type_Vocal_General' # This is the actual name column for VOIX_ET_STYLES_VOCAUX
                    elif 'Public_Cible' in col_name:
                        id_col_for_select = 'ID_Public'
                        name_col_for_select = 'Nom_Public'
                    elif 'Type_Evenement' in col_name:
                        id_col_for_select = 'Type_Evenement' # No specific ID column, use name
                        name_col_for_select = 'Type_Evenement'

                    available_options = _get_options_for_selectbox(resolved_options_df, id_col_for_select, name_col_for_select)
                    selected_display_value = st.selectbox(label, available_options, key=f"{form_key}_{col_name}")
                    new_data[col_name] = _get_id_from_display_string(selected_display_value)
                else: # Static options list
                    new_data[col_name] = st.selectbox(label, options, key=f"{form_key}_{col_name}")
            elif input_type == 'multiselect':
                current_values = config.get('current_value', [])
                if callable(options):
                    resolved_options_df = options()
                    select_options_id_col = config.get('id_col_for_options', 'ID') # Default ID col for multiselect options
                    select_options = resolved_options_df[select_options_id_col].tolist() if not resolved_options_df.empty and select_options_id_col in resolved_options_df.columns else []
                    new_data[col_name] = st.multiselect(label, select_options, default=current_values, key=f"{form_key}_{col_name}")
                else:
                    new_data[col_name] = st.multiselect(label, options, default=current_values, key=f"{form_key}_{col_name}")
                new_data[col_name] = ', '.join(new_data[col_name]) # Store as comma-separated string
            elif input_type == 'date_input':
                new_data[col_name] = st.date_input(label, value=default_value, key=f"{form_key}_{col_name}")
            elif input_type == 'number_input':
                new_data[col_name] = st.number_input(label, value=default_value, key=f"{form_key}_{col_name}", min_value=config.get('min_value'), max_value=config.get('max_value'), step=config.get('step'))
            elif input_type == 'checkbox':
                new_data[col_name] = st.checkbox(label, value=default_value, key=f"{form_key}_{col_name}")
                new_data[col_name] = 'VRAI' if new_data[col_name] else 'FAUX' # Standardize boolean to string for GSheets

        uploaded_files = {}
        if 'file_upload_audio' in fields_config:
            uploaded_files['audio'] = st.file_uploader(fields_config['file_upload_audio']['label'], type=fields_config['file_upload_audio']['type'], key=f"{form_key}_audio_file")
        if 'file_upload_cover' in fields_config:
            uploaded_files['cover'] = st.file_uploader(fields_config['file_upload_cover']['label'], type=fields_config['file_upload_cover']['type'], key=f"{form_key}_cover_file")
        if 'file_upload_profile_img' in fields_config:
            uploaded_files['profile_img'] = st.file_uploader(fields_config['file_upload_profile_img']['label'], type=fields_config['file_upload_profile_img']['type'], key=f"{form_key}_profile_img")

        submit_button = st.form_submit_button("Ajouter")

        if submit_button:
            # Manual validation for required fields, now that 'required=True' is removed from widgets
            all_required_filled = True
            for col_name, config in fields_config.items():
                if col_name.startswith('file_upload_'): # Skip file upload configs
                    continue
                if config.get('required', False) and (not new_data.get(col_name) or new_data.get(col_name) == ''):
                    st.error(f"Le champ '{config['label']}' est obligatoire.")
                    all_required_filled = False
                    break
            
            if all_required_filled:
                if 'file_upload_audio' in uploaded_files and uploaded_files['audio']:
                    audio_path = ut.save_uploaded_file(uploaded_files['audio'], AUDIO_CLIPS_DIR)
                    if audio_path:
                        new_data['URL_Audio_Local'] = audio_path
                    else:
                        st.error("Échec de la sauvegarde du fichier audio.")
                        return
                if 'file_upload_cover' in uploaded_files and uploaded_files['cover']:
                    cover_path = ut.save_uploaded_file(uploaded_files['cover'], SONG_COVERS_DIR if sheet_name_key == "MORCEAUX_GENERES" else ALBUM_COVERS_DIR)
                    if cover_path:
                        new_data['URL_Cover_Album' if sheet_name_key == "MORCEAUX_GENERES" else 'URL_Cover_Principale'] = cover_path
                    else:
                        st.error("Échec de la sauvegarde de l'image de cover.")
                        return
                if 'file_upload_profile_img' in uploaded_files and uploaded_files['profile_img']:
                    profile_img_path = ut.save_uploaded_file(uploaded_files['profile_img'], ALBUM_COVERS_DIR) # Using Album_covers for simplicity for profile images
                    if profile_img_path:
                        new_data['URL_Image_Profil'] = profile_img_path
                    else:
                        st.error("Échec de la sauvegarde de l'image de profil.")
                        return

                if add_function(new_data):
                    st.success(f"'{sheet_name_key}' ajouté avec succès !")
                    st.experimental_rerun()
                else:
                    st.error(f"Échec de l'ajout de '{sheet_name_key}'.")

def _render_update_delete_tab(sheet_name_key: str, unique_id_col: str, display_col: str, fields_config: dict, update_function, form_key: str):
    """
    Rend un onglet de modification/suppression générique pour une feuille Google Sheet.
    :param sheet_name_key: La clé de l'onglet dans WORKSHEET_NAMES.
    :param unique_id_col: Le nom de la colonne ID (ex: 'ID_Morceau').
    :param display_col: La colonne à afficher dans le selectbox (ex: 'Titre_Morceau').
    :param fields_config: Dictionnaire de la configuration des champs.
    :param update_function: La fonction sc.update_x à appeler.
    :param form_key: Clé unique pour le formulaire Streamlit.
    """
    st.subheader(f"Mettre à Jour ou Supprimer un Entrée dans {WORKSHEET_NAMES[sheet_name_key]}")
    current_df = sc.get_dataframe_from_sheet(sheet_name_key)

    if current_df.empty:
        st.info("Aucune donnée à modifier ou supprimer pour le moment.")
        return

    options_display = _get_options_for_selectbox(current_df, unique_id_col, display_col)
    selected_item_display = st.selectbox(
        f"Sélectionnez l'élément à modifier/supprimer dans {WORKSHEET_NAMES[sheet_name_key]}",
        options_display,
        key=f"{form_key}_select_item"
    )

    selected_item_id = _get_id_from_display_string(selected_item_display)
    
    if selected_item_id:
        selected_row = current_df[current_df[unique_id_col] == selected_item_id].iloc[0]

        st.markdown("---")
        st.write(f"**Modification de :** {selected_row[display_col]}")

        with st.form(form_key):
            updated_data = {}
            for col_name, config in fields_config.items():
                # Skip file path configs here, they are handled separately
                if col_name.startswith('file_path_'):
                    continue

                label = config.get('label', col_name)
                input_type = config.get('type', 'text_input')
                current_value = selected_row.get(col_name, config.get('default', ''))
                options = config.get('options', [])
                
                if input_type == 'text_input':
                    updated_data[col_name] = st.text_input(label, value=current_value, key=f"{form_key}_{col_name}")
                elif input_type == 'text_area':
                    updated_data[col_name] = st.text_area(label, value=current_value, key=f"{form_key}_{col_name}", height=config.get('height', None))
                elif input_type == 'selectbox':
                    if callable(options):
                        resolved_options_df = options()
                        id_col_for_select = config.get('id_col_for_options', col_name)
                        name_col_for_select = config.get('name_col_for_options', col_name)
                        
                        # Heuristics for common cases
                        if 'ID_Style_Musical' in col_name or 'Genre' in col_name:
                            id_col_for_select = 'ID_Style_Musical'
                            name_col_for_select = 'Nom_Style_Musical'
                        elif 'ID_Mood' in col_name or 'Mood' in col_name:
                            id_col_for_select = 'ID_Mood'
                            name_col_for_select = 'Nom_Mood'
                        elif 'ID_Theme' in col_name or 'Theme' in col_name:
                            id_col_for_select = 'ID_Theme'
                            name_col_for_select = 'Nom_Theme'
                        elif 'ID_Artiste_IA' in col_name or 'Artiste_IA' in col_name:
                            id_col_for_select = 'ID_Artiste_IA'
                            name_col_for_select = 'Nom_Artiste_IA'
                        elif 'ID_Album' in col_name or 'Album' in col_name:
                            id_col_for_select = 'ID_Album'
                            name_col_for_select = 'Nom_Album'
                        elif 'ID_Style_Lyrique' in col_name or 'Style_Lyrique' in col_name:
                            id_col_for_select = 'ID_Style_Lyrique'
                            name_col_for_select = 'Nom_Style_Lyrique'
                        elif 'ID_Structure' in col_name or 'Structure_Chanson' in col_name:
                            id_col_for_select = 'ID_Structure'
                            name_col_for_select = 'Nom_Structure'
                        elif 'Type_Voix_Desiree' in col_name or 'Type_Vocal_General' in col_name:
                            id_col_for_select = 'ID_Vocal'
                            name_col_for_select = 'Type_Vocal_General'
                        elif 'Public_Cible' in col_name:
                            id_col_for_select = 'ID_Public'
                            name_col_for_select = 'Nom_Public'
                        elif 'Type_Evenement' in col_name:
                            id_col_for_select = 'Type_Evenement'
                            name_col_for_select = 'Type_Evenement'

                        available_options_display = _get_options_for_selectbox(resolved_options_df, id_col_for_select, name_col_for_select)
                        
                        # Find the index of the current value. Handle cases where current_value might be empty or not found.
                        default_index = 0
                        if current_value:
                            try:
                                # Try to match exact ID-Name format first
                                if f"{current_value} - {current_value}" in available_options_display:
                                     default_index = available_options_display.index(f"{current_value} - {current_value}")
                                elif f"{current_value} - {current_value}" in resolved_options_df[id_col_for_select].tolist():
                                     # If the actual data source doesn't have a distinct name column,
                                     # but the ID is there, use it to find the index.
                                     default_index = available_options_display.index(f"{current_value} - {current_value}")
                                else: # Fallback if current_value is just the name and not an ID
                                    matching_rows = resolved_options_df[resolved_options_df[name_col_for_select] == current_value]
                                    if not matching_rows.empty:
                                        matched_id = matching_rows[id_col_for_select].iloc[0]
                                        default_index = available_options_display.index(f"{matched_id} - {current_value}")

                            except ValueError:
                                default_index = 0 # Fallback if value not found

                        selected_display_value = st.selectbox(label, available_options_display, index=default_index, key=f"{form_key}_{col_name}")
                        updated_data[col_name] = _get_id_from_display_string(selected_display_value)

                    else: # Static options list
                        try:
                            default_index = options.index(current_value) if current_value in options else 0
                        except ValueError:
                            default_index = 0
                        updated_data[col_name] = st.selectbox(label, options, index=default_index, key=f"{form_key}_{col_name}")

                elif input_type == 'multiselect':
                    current_values_list = [v.strip() for v in str(current_value).split(',')] if current_value else []
                    if callable(options):
                        resolved_options_df = options()
                        select_options_id_col = config.get('id_col_for_options', 'ID') # Default ID col for multiselect options
                        select_options = resolved_options_df[select_options_id_col].tolist() if not resolved_options_df.empty and select_options_id_col in resolved_options_df.columns else []
                        updated_data[col_name] = st.multiselect(label, select_options, default=current_values_list, key=f"{form_key}_{col_name}")
                    else:
                        updated_data[col_name] = st.multiselect(label, options, default=current_values_list, key=f"{form_key}_{col_name}")
                    updated_data[col_name] = ', '.join(updated_data[col_name]) # Store as comma-separated string
                elif input_type == 'date_input':
                    try:
                        date_value = pd.to_datetime(current_value).date() if current_value else datetime.now().date()
                    except Exception:
                        date_value = datetime.now().date()
                    updated_data[col_name] = st.date_input(label, value=date_value, key=f"{form_key}_{col_name}")
                elif input_type == 'number_input':
                    try:
                        num_value = float(current_value) if current_value else config.get('default', 0.0)
                    except ValueError:
                        num_value = config.get('default', 0.0)
                    updated_data[col_name] = st.number_input(label, value=num_value, key=f"{form_key}_{col_name}", min_value=config.get('min_value'), max_value=config.get('max_value'), step=config.get('step'))
                elif input_type == 'checkbox':
                    updated_data[col_name] = st.checkbox(label, value=ut.parse_boolean_string(current_value), key=f"{form_key}_{col_name}")
                    updated_data[col_name] = 'VRAI' if updated_data[col_name] else 'FAUX'

            # Display existing local files and allow new uploads for update
            if 'file_path_audio' in fields_config:
                audio_col_name = fields_config['file_path_audio']['col_name']
                if selected_row.get(audio_col_name) and os.path.exists(os.path.join(AUDIO_CLIPS_DIR, selected_row[audio_col_name])):
                    st.markdown("##### Fichier Audio Actuel")
                    st.audio(os.path.join(AUDIO_CLIPS_DIR, selected_row[audio_col_name]), format="audio/mp3")
                uploaded_audio_file = st.file_uploader(fields_config['file_path_audio']['label'], type=fields_config['file_path_audio']['type'], key=f"{form_key}_audio_file_upd")
                if uploaded_audio_file:
                    new_audio_path = ut.save_uploaded_file(uploaded_audio_file, AUDIO_CLIPS_DIR)
                    if new_audio_path:
                        updated_data[audio_col_name] = new_audio_path
            
            if 'file_path_cover' in fields_config:
                cover_col_name = fields_config['file_path_cover']['col_name']
                target_dir_cover = SONG_COVERS_DIR if sheet_name_key == "MORCEAUX_GENERES" else ALBUM_COVERS_DIR
                if selected_row.get(cover_col_name) and os.path.exists(os.path.join(target_dir_cover, selected_row[cover_col_name])):
                    st.markdown("##### Image de Cover Actuelle")
                    st.image(os.path.join(target_dir_cover, selected_row[cover_col_name]), width=150)
                uploaded_cover_file = st.file_uploader(fields_config['file_path_cover']['label'], type=fields_config['file_path_cover']['type'], key=f"{form_key}_cover_file_upd")
                if uploaded_cover_file:
                    new_cover_path = ut.save_uploaded_file(uploaded_cover_file, target_dir_cover)
                    if new_cover_path:
                        updated_data[cover_col_name] = new_cover_path

            if 'file_path_profile_img' in fields_config:
                profile_img_col_name = fields_config['file_path_profile_img']['col_name']
                if selected_row.get(profile_img_col_name) and os.path.exists(os.path.join(ALBUM_COVERS_DIR, selected_row[profile_img_col_name])):
                    st.markdown("##### Image de Profil Actuelle")
                    st.image(os.path.join(ALBUM_COVERS_DIR, selected_row[profile_img_col_name]), width=100)
                uploaded_profile_img = st.file_uploader(fields_config['file_path_profile_img']['label'], type=fields_config['file_path_profile_img']['type'], key=f"{form_key}_profile_img_upd")
                if uploaded_profile_img:
                    new_profile_img_path = ut.save_uploaded_file(uploaded_profile_img, ALBUM_COVERS_DIR)
                    if new_profile_img_path:
                        updated_data[profile_img_col_name] = new_profile_img_path
            
            col_form_buttons = st.columns(2)
            with col_form_buttons[0]:
                submit_update_button = st.form_submit_button("Mettre à Jour")
            with col_form_buttons[1]:
                submit_delete_trigger_button = st.form_submit_button("Supprimer", help="Cliquez pour lancer la confirmation de suppression.")

            if submit_update_button:
                # Manual validation for required fields
                all_required_filled = True
                for col_name, config in fields_config.items():
                    if col_name.startswith('file_path_'):
                        continue
                    if config.get('required', False) and (not updated_data.get(col_name) or updated_data.get(col_name) == ''):
                        st.error(f"Le champ '{config['label']}' est obligatoire.")
                        all_required_filled = False
                        break

                if all_required_filled:
                    if update_function(selected_item_id, updated_data):
                        st.success(f"'{selected_row[display_col]}' mis à jour avec succès !")
                        st.experimental_rerun()
                    else:
                        st.error(f"Échec de la mise à jour de '{selected_row[display_col]}'.")

            if submit_delete_trigger_button:
                st.session_state[f'confirm_delete_{sheet_name_key.lower().replace("_", "")}_id'] = selected_item_id
                st.session_state[f'confirm_delete_{sheet_name_key.lower().replace("_", "")}_name'] = selected_row[display_col]
                st.experimental_rerun()

def _handle_generic_delete_confirmation(session_state_id_key: str, session_state_name_key: str, sheet_name_key: str, unique_id_col: str, delete_function):
    """
    Gère le bloc de confirmation de suppression générique, en dehors des formulaires.
    :param session_state_id_key: Clé session_state pour l'ID à supprimer (ex: 'confirm_delete_morceau_id').
    :param session_state_name_key: Clé session_state pour le nom à supprimer (ex: 'confirm_delete_morceau_name').
    :param sheet_name_key: La clé de l'onglet dans WORKSHEET_NAMES.
    :param unique_id_col: Le nom de la colonne ID (ex: 'ID_Morceau').
    :param delete_function: La fonction sc.delete_row_from_sheet à appeler.
    """
    if st.session_state[session_state_id_key]:
        st.error(f"Confirmez-vous la suppression définitive de '{st.session_state[session_state_name_key]}' ?")
        col_confirm_buttons = st.columns(2)
        with col_confirm_buttons[0]:
            if st.button("Oui, Supprimer Définitivement", key=f"final_confirm_delete_{session_state_id_key}"):
                if delete_function(WORKSHEET_NAMES[sheet_name_key], unique_id_col, st.session_state[session_state_id_key]):
                    st.success(f"'{st.session_state[session_state_name_key]}' supprimé avec succès !")
                    st.session_state[session_state_id_key] = None # Nettoyer l'état
                    st.experimental_rerun()
                else:
                    st.error("Échec de la suppression.")
        with col_confirm_buttons[1]:
            if st.button("Annuler", key=f"cancel_delete_{session_state_id_key}"):
                st.info("Suppression annulée.")
                st.session_state[session_state_id_key] = None # Nettoyer l'état
                st.experimental_rerun()

# --- Fonctions de Rendu des Pages Spécifiques ---

def render_home_page():
    st.write("Bienvenue dans votre Quartier Général de Micro-Empire Numérique Musical IA. Utilisez le menu latéral pour naviguer.")
    st.info("Pensez à bien configurer vos dossiers d'assets et vos secrets dans les paramètres de votre application Streamlit Cloud!")
    st.markdown("---")
    st.subheader("État de l'Oracle")
    if st.session_state.get('gemini_initialized'):
        st.success("L'Oracle Architecte (Gemini) est initialisé et prêt à servir.")
    else:
        st.error(st.session_state.get('gemini_error', "L'Oracle Architecte (Gemini) n'a pas pu être initialisé. Vérifiez vos secrets API."))
    st.subheader("État des Connexions Google Sheets")
    try:
        # Tente de récupérer une petite feuille pour tester la connexion GS
        sc.get_all_styles_musicaux()
        st.success(f"Connexion à Google Sheet '{SHEET_NAME}' réussie.")
    except Exception as e:
        st.error(f"Échec de la connexion à Google Sheet : {e}. Vérifiez les permissions de votre compte de service et le partage du Sheet.")

def render_content_generator_page():
    st.header("✍️ Générateur de Contenu Musical par l'Oracle")
    st.write("Utilisez cette interface pour demander à l'Oracle de générer des paroles, des prompts audio, des titres, des descriptions marketing et des prompts visuels pour vos pochettes d'album.")

    content_type = st.radio(
        "Quel type de contenu souhaitez-vous générer ?",
        ["Paroles de Chanson", "Prompt Audio (pour SUNO)", "Idées de Titres", "Description Marketing", "Prompt Pochette d'Album"],
        key="content_type_radio"
    )

    st.markdown("---")

    # --- Formulaire de Génération de Paroles ---
    if content_type == "Paroles de Chanson":
        st.subheader("Générer des Paroles de Chanson")
        
        genres_musicaux = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods = sc.get_all_moods()['ID_Mood'].tolist()
        themes = sc.get_all_themes()['ID_Theme'].tolist()
        styles_lyriques = sc.get_all_styles_lyriques()['ID_Style_Lyrique'].tolist()
        structures_song = sc.get_all_structures_song()['ID_Structure'].tolist()
        
        with st.form("lyrics_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                # Removed 'required=True' to prevent the original error
                st.selectbox("Genre Musical", [''] + genres_musicaux, key="lyrics_genre_musical")
                st.selectbox("Mood Principal", [''] + moods, key="lyrics_mood_principal")
                st.selectbox("Thème Principal Lyrique", [''] + themes, key="lyrics_theme_lyrique_principal")
                st.selectbox("Style Lyrique", [''] + styles_lyriques, key="lyrics_style_lyrique")
                st.text_input("Mots-clés de Génération (séparés par des virgules)", key="lyrics_mots_cles_generation")
            with col2:
                st.selectbox("Structure de Chanson", [''] + structures_song, key="lyrics_structure_chanson")
                st.selectbox("Langue des Paroles", ["", "Français", "Anglais", "Espagnol"], key="lyrics_langue_paroles")
                st.selectbox("Niveau de Langage", ["", "Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"], key="lyrics_niveau_langage_paroles")
                st.selectbox("Imagerie Texte", ["", "Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"], key="lyrics_imagerie_texte")
                
            submit_lyrics_button = st.form_submit_button("Générer les Paroles")

        if st.session_state.get('lyrics_mood_principal') and st.session_state.lyrics_mood_principal != '':
            st.markdown("---")
            st.subheader("Affiner le Mood de vos Paroles avec l'Oracle")
            if st.button("Affiner le Mood avec l'Oracle 🧠", key="refine_mood_button_outside_form"):    
                with st.spinner("L'Oracle affine le mood..."):
                    mood_questions = go.refine_mood_with_questions(st.session_state.lyrics_mood_principal)
                    st.session_state['mood_refinement_questions'] = mood_questions
                
            if 'mood_refinement_questions' in st.session_state and st.session_state.mood_refinement_questions:
                st.info("Voici les questions de l'Oracle pour affiner votre mood :\n" + st.session_state.mood_refinement_questions)
                st.text_area("Vos réponses / Affinement du mood (optionnel)", key="lyrics_mood_refinement_response_outside_form")


        if submit_lyrics_button:
            # Manual validation after form submission
            required_lyrics_fields = {
                "lyrics_genre_musical": "Genre Musical",
                "lyrics_mood_principal": "Mood Principal",
                "lyrics_theme_lyrique_principal": "Thème Principal Lyrique",
                "lyrics_style_lyrique": "Style Lyrique",
                "lyrics_structure_chanson": "Structure de Chanson"
            }
            
            all_lyrics_fields_filled = True
            for field_key, field_name in required_lyrics_fields.items():
                if not st.session_state.get(field_key):
                    st.warning(f"Veuillez remplir le champ obligatoire : {field_name}.")
                    all_lyrics_fields_filled = False
                    break

            if all_lyrics_fields_filled:
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
            # else: validation message is handled by the loop above

        if 'generated_lyrics' in st.session_state and st.session_state.generated_lyrics:
            st.markdown("---")
            st.subheader("Paroles Générées")
            st.text_area("Copiez les paroles ici :", st.session_state.generated_lyrics, height=400, key="displayed_generated_lyrics")
            
            save_lyrics_option = st.radio(
                "Où souhaitez-vous sauvegarder ces paroles ?",
                ["Ne pas sauvegarder", "Dans un nouveau Morceau (Google Sheet)", "Dans un Morceau Existant (Google Sheet)", "Dans un fichier local"],
                key="save_lyrics_option"
            )

            if save_lyrics_option == "Dans un nouveau Morceau (Google Sheet)":
                with st.form("save_new_morceau_lyrics_form"):
                    st.info("Ces paroles seront ajoutées à un nouveau morceau dans l'onglet `MORCEAUX_GENERES`.")
                    artistes_ia_list = [''] + sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()
                    new_morceau_title = st.text_input("Titre du nouveau morceau", value=f"Nouveau Morceau - {st.session_state.lyrics_genre_musical}", key="new_morceau_lyrics_title")
                    # Removed 'required=True'
                    new_morceau_artist_ia = st.selectbox("Artiste IA Associé", artistes_ia_list, key="new_morceau_lyrics_artist_ia")
                    
                    save_button = st.form_submit_button("Sauvegarder le nouveau Morceau")
                    if save_button:
                        if new_morceau_title and new_morceau_artist_ia:
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
                                'Ambiance_Sonore_Specifique': st.session_state.lyrics_mood_principal,
                                # Remplir les colonnes restantes avec des valeurs par défaut pour éviter les erreurs
                                'Effets_Production_Dominants': '', 'Type_Voix_Desiree': '', 'Style_Vocal_Desire': '', 'Caractere_Voix_Desire': '',
                                'Durée_Estimee': '', 'URL_Audio_Local': '', 'URL_Cover_Album': '', 'URL_Video_Clip_Associe': '', 'Mots_Cles_SEO': '', 'Description_Courte_Marketing': '',
                                'ID_Album_Associe': '', 'Favori': 'FAUX'
                            }
                            if sc.add_morceau_generes(morceau_data):
                                st.success(f"Paroles sauvegardées comme nouveau morceau '{new_morceau_title}' dans Google Sheet !")
                                st.session_state['generated_lyrics'] = "" # Effacer après sauvegarde
                                st.experimental_rerun()
                            else:
                                st.error("Échec de la sauvegarde des paroles.")
                        else:
                            st.warning("Veuillez remplir le titre et sélectionner l'artiste IA.")
            
            elif save_lyrics_option == "Dans un Morceau Existant (Google Sheet)":
                morceaux_df_all = sc.get_all_morceaux()
                if not morceaux_df_all.empty:
                    morceau_to_update_id_display = st.selectbox(
                        "Sélectionnez le morceau à mettre à jour",
                        _get_options_for_selectbox(morceaux_df_all, 'ID_Morceau', 'Titre_Morceau'),
                        key="update_existing_morceau_lyrics_id"
                    )
                    morceau_to_update_id = _get_id_from_display_string(morceau_to_update_id_display)

                    if st.button("Mettre à jour les Paroles du Morceau Existant", key="update_lyrics_existing_btn"):
                        if morceau_to_update_id:
                            morceau_data_update = {
                                'Prompt_Generation_Paroles': st.session_state.generated_lyrics,
                                'Statut_Production': 'Paroles Générées'
                            }
                            if sc.update_morceau_generes(morceau_to_update_id, morceau_data_update):
                                st.success(f"Paroles mises à jour pour le morceau '{morceau_to_update_id}' dans Google Sheet !")
                                st.session_state['generated_lyrics'] = ""
                                st.experimental_rerun()
                            else:
                                st.error("Échec de la mise à jour des paroles.")
                        else:
                            st.warning("Veuillez sélectionner un morceau à mettre à jour.")
                else:
                    st.info("Aucun morceau existant dans votre Google Sheet.")

            elif save_lyrics_option == "Dans un fichier local":
                filename = st.text_input("Nom du fichier local (.txt)", value=f"paroles_{st.session_state.lyrics_genre_musical}_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", key="local_lyrics_filename")
                if st.button("Sauvegarder les Paroles en local", key="save_lyrics_local_btn"):
                    file_path = os.path.join(GENERATED_TEXTS_DIR, filename)
                    try:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(st.session_state.generated_lyrics)
                        st.success(f"Paroles sauvegardées localement: {file_path}")
                        st.session_state['generated_lyrics'] = ""
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde locale des paroles: {e}")

    st.markdown("---")

    # --- Formulaire de Génération de Prompt Audio ---
    if content_type == "Prompt Audio (pour SUNO)":
        st.subheader("Générer un Prompt Audio Détaillé (pour SUNO)")
        
        styles_musicaux = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods = sc.get_all_moods()['ID_Mood'].tolist()
        structures_song = sc.get_all_structures_song()['ID_Structure'].tolist()
        types_voix = sc.get_all_voix_styles()['Type_Vocal_General'].unique().tolist()

        with st.form("audio_prompt_generator_form"):
            col1, col2 = st.columns(2)
            with col1:
                # Removed 'required=True'
                st.selectbox("Genre Musical", [''] + styles_musicaux, key="audio_genre_musical_input")
                st.selectbox("Mood Principal", [''] + moods, key="audio_mood_principal_input")
                st.text_input("Durée Estimée (ex: 03:30)", key="audio_duree_estimee_input")
                st.text_input("Instrumentation Principale (ex: Piano, Violoncelle, Pads)", key="audio_instrumentation_principale_input")
            with col2:
                st.text_input("Ambiance Sonore Spécifique", key="audio_ambiance_sonore_specifique_input")
                st.text_input("Effets de Production Dominants (ex: Réverbération luxuriante)", key="audio_effets_production_dominants_input")
                st.selectbox("Type de Voix Désirée", ['N/A'] + types_voix, key="audio_type_voix_desiree_input")
                st.text_input("Style Vocal Désiré (ex: Lyrique, Râpeux)", key="audio_style_vocal_desire_input")
                st.text_input("Caractère de la Voix (ex: Puissant, Doux)", key="audio_caractere_voix_desire_input")
                st.selectbox("Structure de Chanson", ['N/A'] + structures_song, key="audio_structure_song_input")

            submit_audio_prompt_button = st.form_submit_button("Générer le Prompt Audio")

        if submit_audio_prompt_button:
            # Manual validation
            if st.session_state.audio_genre_musical_input and st.session_state.audio_mood_principal_input:
                with st.spinner("L'Oracle génère le prompt audio..."):
                    generated_audio_prompt = go.generate_audio_prompt(
                        genre_musical=st.session_state.audio_genre_musical_input,
                        mood_principal=st.session_state.audio_mood_principal_input,
                        duree_estimee=st.session_state.audio_duree_estimee_input,
                        instrumentation_principale=st.session_state.audio_instrumentation_principale_input,
                        ambiance_sonore_specifique=st.session_state.audio_ambiance_sonore_specifique_input,
                        effets_production_dominants=st.session_state.audio_effets_production_dominants_input,
                        type_voix_desiree=st.session_state.audio_type_voix_desiree_input,
                        style_vocal_desire=st.session_state.audio_style_vocal_desire_input,
                        caractere_voix_desire=st.session_state.audio_caractere_voix_desire_input,
                        structure_song=st.session_state.audio_structure_song_input
                    )
                    st.session_state['generated_audio_prompt'] = generated_audio_prompt
                    st.success("Prompt Audio généré avec succès !")
            else:
                st.warning("Veuillez remplir les champs obligatoires (Genre Musical, Mood Principal).")

        if 'generated_audio_prompt' in st.session_state and st.session_state.generated_audio_prompt:
            st.markdown("---")
            st.subheader("Prompt Audio Généré (pour SUNO ou autre)")
            st.text_area("Copiez ce prompt pour votre générateur audio :", st.session_state.generated_audio_prompt, height=200, key="displayed_generated_audio_prompt")

            morceaux_df_all = sc.get_all_morceaux()
            if not morceaux_df_all.empty:
                morceau_to_update_audio_id_display = st.selectbox(
                    "Liez ce prompt à un morceau existant (Google Sheet) :",
                    _get_options_for_selectbox(morceaux_df_all, 'ID_Morceau', 'Titre_Morceau'),
                    key="update_existing_morceau_audio_prompt_id"
                )
                morceau_to_update_audio_id = _get_id_from_display_string(morceau_to_update_audio_id_display)

                if st.button("Mettre à jour le Prompt Audio du Morceau Existant", key="update_audio_prompt_existing_btn"):
                    if morceau_to_update_audio_id:
                        morceau_data_update = {
                            'Prompt_Generation_Audio': st.session_state.generated_audio_prompt,
                            'Statut_Production': 'Prompt Audio Généré'
                        }
                        if sc.update_morceau_generes(morceau_to_update_audio_id, morceau_data_update):
                            st.success(f"Prompt Audio mis à jour pour le morceau '{morceau_to_update_audio_id}' !")
                            st.session_state['generated_audio_prompt'] = ""
                            st.experimental_rerun()
                        else:
                            st.error("Échec de la mise à jour du prompt audio.")
                    else:
                        st.warning("Veuillez sélectionner un morceau à mettre à jour.")
            else:
                st.info("Aucun morceau existant pour lier le prompt audio.")

    st.markdown("---")

    # --- Formulaire de Génération d'Idées de Titres ---
    if content_type == "Idées de Titres":
        st.subheader("Générer des Idées de Titres de Chansons")
        themes_list = sc.get_all_themes()['ID_Theme'].tolist()
        genres_list = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

        with st.form("title_generator_form"):
            # Removed 'required=True'
            st.selectbox("Thème Principal", [''] + themes_list, key="title_theme_principal")
            st.selectbox("Genre Musical", [''] + genres_list, key="title_genre_musical")
            st.text_area("Extrait de paroles (optionnel, pour inspiration)", key="title_paroles_extrait")
            submit_title_button = st.form_submit_button("Générer les Titres")

        if submit_title_button:
            # Manual validation
            if st.session_state.title_theme_principal and st.session_state.title_genre_musical:
                with st.spinner("L'Oracle brainstorme des titres..."):
                    generated_titles = go.generate_title_ideas(
                        theme_principal=st.session_state.title_theme_principal,
                        genre_musical=st.session_state.title_genre_musical,
                        paroles_extrait=st.session_state.title_paroles_extrait
                    )
                    st.session_state['generated_titles'] = generated_titles
                    st.success("Idées de titres générées avec succès !")
            else:
                st.warning("Veuillez remplir les champs obligatoires (Thème Principal, Genre Musical).")
            
        if 'generated_titles' in st.session_state and st.session_state.generated_titles:
            st.markdown("---")
            st.subheader("Idées de Titres Générées")
            st.text_area("Copiez les titres ici :", st.session_state.generated_titles, height=250, key="displayed_generated_titles")

    st.markdown("---")

    # --- Formulaire de Génération de Description Marketing ---
    if content_type == "Description Marketing":
        st.subheader("Générer une Description Marketing")
        styles_musicaux_list = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods_list = sc.get_all_moods()['ID_Mood'].tolist()
        public_cible_list = sc.get_all_public_cible()['ID_Public'].tolist()

        with st.form("marketing_copy_form"):
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("Titre du Morceau/Album", key="marketing_titre_morceau") # Removed 'required=True'
                st.selectbox("Genre Musical", [''] + styles_musicaux_list, key="marketing_genre_musical") # Removed 'required=True'
            with col2:
                st.selectbox("Mood Principal", [''] + moods_list, key="marketing_mood_principal") # Removed 'required=True'
                st.selectbox("Public Cible", [''] + public_cible_list, key="marketing_public_cible") # Removed 'required=True'
            st.text_input("Point Fort Principal (ex: 'son unique', 'message profond')", key="marketing_point_fort") # Removed 'required=True'
            submit_marketing_button = st.form_submit_button("Générer la Description Marketing")

            if submit_marketing_button:
                # Manual validation
                required_marketing_fields = {
                    "marketing_titre_morceau": "Titre du Morceau/Album",
                    "marketing_genre_musical": "Genre Musical",
                    "marketing_mood_principal": "Mood Principal",
                    "marketing_public_cible": "Public Cible",
                    "marketing_point_fort": "Point Fort Principal"
                }

                all_marketing_fields_filled = True
                for field_key, field_name in required_marketing_fields.items():
                    if not st.session_state.get(field_key):
                        st.warning(f"Veuillez remplir le champ obligatoire : {field_name}.")
                        all_marketing_fields_filled = False
                        break

                if all_marketing_fields_filled:
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
                # else: validation message is handled by the loop above
            
        if 'generated_marketing_copy' in st.session_state and st.session_state.generated_marketing_copy:
            st.markdown("---")
            st.subheader("Description Marketing Générée")
            st.text_area("Copiez la description ici :", st.session_state.generated_marketing_copy, height=150, key="displayed_generated_marketing_copy")

    st.markdown("---")

    # --- Formulaire de Génération de Prompt Pochette d'Album ---
    if content_type == "Prompt Pochette d'Album":
        st.subheader("Générer un Prompt pour Pochette d'Album (Midjourney/DALL-E)")
        styles_musicaux_list = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
        moods_list = sc.get_all_moods()['ID_Mood'].tolist()

        with st.form("album_art_prompt_form"):
            st.text_input("Nom de l'Album", key="album_art_nom_album") # Removed 'required=True'
            st.selectbox("Genre Dominant de l'Album", [''] + styles_musicaux_list, key="album_art_genre_dominant") # Removed 'required=True'
            st.text_area("Description du Concept de l'Album", key="album_art_description_concept") # Removed 'required=True'
            st.selectbox("Mood Principal Visuel", [''] + moods_list, key="album_art_mood_principal") # Removed 'required=True'
            st.text_input("Mots-clés Visuels Supplémentaires (ex: 'couleurs vives', 'style néon', 'minimaliste')", key="album_art_mots_cles_visuels")
            submit_album_art_button = st.form_submit_button("Générer le Prompt Visuel")

            if submit_album_art_button:
                # Manual validation
                required_album_art_fields = {
                    "album_art_nom_album": "Nom de l'Album",
                    "album_art_genre_dominant": "Genre Dominant de l'Album",
                    "album_art_description_concept": "Description du Concept de l'Album",
                    "album_art_mood_principal": "Mood Principal Visuel"
                }

                all_album_art_fields_filled = True
                for field_key, field_name in required_album_art_fields.items():
                    if not st.session_state.get(field_key):
                        st.warning(f"Veuillez remplir le champ obligatoire : {field_name}.")
                        all_album_art_fields_filled = False
                        break

                if all_album_art_fields_filled:
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
                # else: validation message is handled by the loop above
            
        if 'generated_album_art_prompt' in st.session_state and st.session_state.generated_album_art_prompt:
            st.markdown("---")
            st.subheader("Prompt de Pochette d'Album Généré")
            st.text_area("Copiez ce prompt pour votre générateur d'images :", st.session_state.generated_album_art_prompt, height=300, key="displayed_generated_album_art_prompt")

def render_copilot_creative_page():
    st.header("💡 Co-pilote Créatif de l'Oracle (Beta)")
    st.write("Laissez l'Oracle vous accompagner en temps réel pour l'écriture de paroles, la composition harmonique ou rythmique.")
    st.info("Cette fonctionnalité est en version Beta. Les suggestions sont basées sur votre input et le contexte défini.")

    co_pilot_type = st.radio(
        "Quel type de suggestion souhaitez-vous ?",
        ["Suite Lyrique", "Ligne de Basse", "Prochain Accord", "Idée Rythmique"],
        key="co_pilot_type_radio"
    )

    st.markdown("---")

    # Contexte global pour le co-pilote
    st.subheader("Contexte du Morceau")
    col_ctx1, col_ctx2 = st.columns(2)
    with col_ctx1:
        st.selectbox("Genre Musical du morceau", [''] + sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist(), key="copilot_genre_musical")
    with col_ctx2:
        st.selectbox("Mood du morceau", [''] + sc.get_all_moods()['ID_Mood'].tolist(), key="copilot_mood_principal")
    
    st.selectbox("Thème Principal du morceau", [''] + sc.get_all_themes()['ID_Theme'].tolist(), key="copilot_theme_principal")
    st.text_input("Mots-clés contextuels (ex: 'solitude urbaine', 'rythme entraînant')", key="copilot_context_keywords")
        
    full_context = f"Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}, Thème: {st.session_state.copilot_theme_principal}, Mots-clés: {st.session_state.copilot_context_keywords}"

    st.markdown("---")

    # --- Formulaire pour Suite Lyrique ---
    if co_pilot_type == "Suite Lyrique":
        st.subheader("Suggérer la Suite des Paroles")
        with st.form("copilot_lyrics_form"):
            st.text_area("Commencez à écrire vos paroles ici :", key="copilot_current_lyrics_input", height=100)
            submit_copilot_lyrics = st.form_submit_button("Suggérer la suite")

            if submit_copilot_lyrics:
                # Manual validation
                if st.session_state.copilot_current_lyrics_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
                    with st.spinner("L'Oracle brainstorme la suite des paroles..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_lyrics_input,
                            context=full_context,
                            type_suggestion="suite_lyrique"
                        )
                        st.session_state['copilot_lyrics_suggestion'] = suggestion
                        st.success("Suggestion de paroles prête !")
                else:
                    st.warning("Veuillez entrer du texte et définir le contexte musical pour obtenir une suggestion.")

        if 'copilot_lyrics_suggestion' in st.session_state and st.session_state.copilot_lyrics_suggestion:
            st.markdown("---")
            st.subheader("Suggestion de Paroles")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_lyrics_suggestion, height=200)
            if st.button("Utiliser cette suggestion", key="use_lyrics_suggestion"):
                st.session_state.copilot_current_lyrics_input += "\n" + st.session_state.copilot_lyrics_suggestion
                st.experimental_rerun()

    # --- Formulaire pour Ligne de Basse ---
    elif co_pilot_type == "Ligne de Basse":
        st.subheader("Suggérer une Ligne de Basse")
        with st.form("copilot_bass_form"):
            st.text_input("Décrivez le groove ou la progression d'accords actuelle (ex: 'groove funk sur Am - G - C - F')", key="copilot_current_bass_input")
            submit_copilot_bass = st.form_submit_button("Suggérer une ligne de basse")

            if submit_copilot_bass:
                # Manual validation
                if st.session_state.copilot_current_bass_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
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
                # Manual validation
                if st.session_state.copilot_current_chord_input and st.session_state.copilot_tonalite_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
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
                    st.warning("Veuillez entrer l'accord actuel, la tonalité et le contexte.")

        if 'copilot_chord_suggestion' in st.session_state and st.session_state.copilot_chord_suggestion:
            st.markdown("---")
            st.subheader("Suggestions de Prochains Accords")
            st.text_area("Voici les options du Co-pilote :", st.session_state.copilot_chord_suggestion, height=200)

    # --- Formulaire pour Idée Rythmique ---
    elif co_pilot_type == "Idée Rythmique":
        st.subheader("Suggérer une Idée Rythmique")
        with st.form("copilot_rhythm_form"):
            st.text_input("Décrivez le feeling rythmique désiré (ex: 'un groove entraînant', 'un rythme brisé')", key="copilot_current_rhythm_input")
            submit_copilot_rhythm = st.form_submit_button("Suggérer un rythme")

            if submit_copilot_rhythm:
                # Manual validation
                if st.session_state.copilot_current_rhythm_input and st.session_state.copilot_genre_musical and st.session_state.copilot_mood_principal:
                    rhythm_context = f"Genre: {st.session_state.copilot_genre_musical}, Mood: {st.session_state.copilot_mood_principal}"
                    with st.spinner("L'Oracle imagine un rythme..."):
                        suggestion = go.copilot_creative_suggestion(
                            current_input=st.session_state.copilot_current_rhythm_input,
                            context=rhythm_context,
                            type_suggestion="idee_rythmique"
                        )
                        st.session_state['copilot_rhythm_suggestion'] = suggestion
                        st.success("Suggestion rythmique prête !")
                else:
                    st.warning("Veuillez décrire le feeling rythmique et le contexte musical.")

        if 'copilot_rhythm_suggestion' in st.session_state and st.session_state.copilot_rhythm_suggestion:
            st.markdown("---")
            st.subheader("Suggestion Rythmique")
            st.text_area("Voici la suggestion du Co-pilote :", st.session_state.copilot_rhythm_suggestion, height=150)

def render_multimodal_creation_page():
    st.header("🎬 Création Multimodale Synchronisée")
    st.write("L'Oracle génère des prompts cohérents pour vos paroles, votre audio (pour SUNO) et vos visuels (pour Midjourney/DALL-E), assurant une harmonie parfaite de votre œuvre.")

    themes_list = sc.get_all_themes()['ID_Theme'].tolist()
    genres_list = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()
    moods_list = sc.get_all_moods()['ID_Mood'].tolist()
    artistes_ia_list = sc.get_all_artistes_ia()['ID_Artiste_IA'].tolist()

    with st.form("multimodal_creation_form"):
        col_multi1, col_multi2 = st.columns(2)
        with col_multi1:
            st.selectbox("Thème Principal", [''] + themes_list, key="multi_main_theme") # Removed 'required=True'
            st.selectbox("Genre Musical Général", [''] + genres_list, key="multi_main_genre") # Removed 'required=True'
        with col_multi2:
            st.selectbox("Mood Général", [''] + moods_list, key="multi_main_mood") # Removed 'required=True'
            st.selectbox("Artiste IA Associé", [''] + artistes_ia_list, key="multi_artiste_ia_name") # Removed 'required=True'
            
        st.text_input("Longueur Estimée du Morceau (ex: '03:45')", key="multi_longueur_morceau") # Removed 'required=True'

        submit_multimodal_button = st.form_submit_button("Générer les Prompts Multimodaux")

        if submit_multimodal_button:
            # Manual validation
            required_multimodal_fields = {
                "multi_main_theme": "Thème Principal",
                "multi_main_genre": "Genre Musical Général",
                "multi_main_mood": "Mood Général",
                "multi_artiste_ia_name": "Artiste IA Associé",
                "multi_longueur_morceau": "Longueur Estimée du Morceau"
            }

            all_multimodal_fields_filled = True
            for field_key, field_name in required_multimodal_fields.items():
                if not st.session_state.get(field_key):
                    st.warning(f"Veuillez remplir le champ obligatoire : {field_name}.")
                    all_multimodal_fields_filled = False
                    break

            if all_multimodal_fields_filled:
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
                # else: validation message is handled by the loop above

    if 'multimodal_prompts' in st.session_state and st.session_state.multimodal_prompts:
        st.markdown("---")
        st.subheader("Prompts Multimodaux Générés")
        
        st.write("### Prompt pour les Paroles de Chanson :")
        st.text_area("Copiez pour votre parolier ou pour affiner :", st.session_state.multimodal_prompts.get("paroles_prompt", ""), height=300, key="multi_lyrics_output")

        st.write("### Prompt pour la Génération Audio (pour SUNO) :")
        st.text_area("Copiez pour SUNO ou votre générateur audio :", st.session_state.multimodal_prompts.get("audio_suno_prompt", ""), height=200, key="multi_audio_output")

        st.write("### Prompt pour l'Image de Pochette (Midjourney/DALL-E) :")
        st.text_area("Copiez pour votre générateur d'images :", st.session_state.multimodal_prompts.get("image_prompt", ""), height=250, key="multi_image_output")

def render_my_tracks_page():
    st.header("🎶 Mes Morceaux Générés")
    st.write("Gérez et consultez toutes vos créations musicales, qu'elles soient entièrement générées par l'IA ou co-créées.")

    morceaux_df = sc.get_all_morceaux()
    
    tab1, tab2, tab3 = st.tabs(["Voir/Rechercher Morceaux", "Ajouter un Nouveau Morceau", "Mettre à Jour/Supprimer Morceau"])

    with tab1:
        st.subheader("Voir et Rechercher des Morceaux")
        if not morceaux_df.empty:
            search_query = st.text_input("Rechercher par titre, genre ou mots-clés", key="search_morceaux")
            if search_query:
                filtered_df = morceaux_df[morceaux_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
            else:
                filtered_df = morceaux_df
            display_dataframe(ut.format_dataframe_for_display(filtered_df), key="morceaux_display")
        else:
            st.info("Aucun morceau enregistré pour le moment.")

    with tab2:
        _render_add_tab(
            sheet_name_key="MORCEAUX_GENERES",
            fields_config={
                'Titre_Morceau': {'type': 'text_input', 'label': 'Titre du Morceau', 'required': True},
                'Statut_Production': {'type': 'selectbox', 'label': 'Statut de Production', 'options': ["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"]},
                'Durée_Estimee': {'type': 'text_input', 'label': 'Durée Estimée (ex: 03:45)'},
                'ID_Style_Musical_Principal': {'type': 'selectbox', 'label': 'Style Musical Principal', 'options': sc.get_all_styles_musicaux, 'required': True},
                'Ambiance_Sonore_Specifique': {'type': 'selectbox', 'label': 'Mood Principal', 'options': sc.get_all_moods},
                'Theme_Principal_Lyrique': {'type': 'selectbox', 'label': 'Thème Principal Lyrique', 'options': sc.get_all_themes},
                'ID_Style_Lyrique_Principal': {'type': 'selectbox', 'label': 'Style Lyrique', 'options': sc.get_all_styles_lyriques},
                'Structure_Chanson_Specifique': {'type': 'selectbox', 'label': 'Structure de Chanson', 'options': sc.get_all_structures_song},
                'Mots_Cles_Generation': {'type': 'text_area', 'label': 'Mots-clés de Génération (séparés par des virgules)'},
                'Langue_Paroles': {'type': 'selectbox', 'label': 'Langue des Paroles', 'options': ["", "Français", "Anglais", "Espagnol"]},
                'Niveau_Langage_Paroles': {'type': 'selectbox', 'label': 'Niveau de Langage Paroles', 'options': ["", "Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"]},
                'Imagerie_Texte': {'type': 'selectbox', 'label': 'Imagerie Texte', 'options': ["", "Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"]},
                'ID_Artiste_IA': {'type': 'selectbox', 'label': 'Artiste IA Associé', 'options': sc.get_all_artistes_ia, 'required': True},
                'ID_Album_Associe': {'type': 'selectbox', 'label': 'Album Associé', 'options': sc.get_all_albums},
                'Prompt_Generation_Audio': {'type': 'text_area', 'label': 'Prompt Génération Audio (pour SUNO)', 'height': 150},
                'Prompt_Generation_Paroles': {'type': 'text_area', 'label': 'Prompt Génération Paroles', 'height': 150},
                'Instrumentation_Principale': {'type': 'text_input', 'label': 'Instrumentation Principale'},
                'Effets_Production_Dominants': {'type': 'text_input', 'label': 'Effets Production Dominants'},
                'Type_Voix_Desiree': {'type': 'selectbox', 'label': 'Type de Voix Désirée', 'options': sc.get_all_voix_styles, 'id_col_for_options': 'Type_Vocal_General', 'name_col_for_options': 'Type_Vocal_General'},
                'Style_Vocal_Desire': {'type': 'text_input', 'label': 'Style Vocal Désiré (ex: Lyrique, Râpeux)'},
                'Caractere_Voix_Desire': {'type': 'text_input', 'label': 'Caractère Voix Désiré (ex: Puissant, Doux)'},
                'Mots_Cles_SEO': {'type': 'text_input', 'label': 'Mots-clés SEO'},
                'Description_Courte_Marketing': {'type': 'text_area', 'label': 'Description Courte Marketing', 'height': 100},
                'file_upload_audio': {'label': 'Uploader Fichier Audio (.mp3, .wav)', 'type': ["mp3", "wav"]},
                'file_upload_cover': {'label': 'Uploader Image de Cover (.jpg, .png)', 'type': ["jpg", "png"]},
                'Favori': {'type': 'checkbox', 'label': 'Marquer comme Favori', 'default': False}
            },
            add_function=sc.add_morceau_generes,
            form_key="add_morceau_form_generic"
        )

    with tab3:
        _render_update_delete_tab(
            sheet_name_key="MORCEAUX_GENERES",
            unique_id_col='ID_Morceau',
            display_col='Titre_Morceau',
            fields_config={
                'Titre_Morceau': {'type': 'text_input', 'label': 'Titre du Morceau', 'required': True},
                'Statut_Production': {'type': 'selectbox', 'label': 'Statut de Production', 'options': ["Idée", "Paroles Générées", "Prompt Audio Généré", "Audio Généré", "Mix/Master", "Finalisé", "Publié"]},
                'Durée_Estimee': {'type': 'text_input', 'label': 'Durée Estimée (ex: 03:45)'},
                'ID_Style_Musical_Principal': {'type': 'selectbox', 'label': 'Style Musical Principal', 'options': sc.get_all_styles_musicaux},
                'Ambiance_Sonore_Specifique': {'type': 'selectbox', 'label': 'Mood Principal', 'options': sc.get_all_moods},
                'Theme_Principal_Lyrique': {'type': 'selectbox', 'label': 'Thème Principal Lyrique', 'options': sc.get_all_themes},
                'ID_Style_Lyrique_Principal': {'type': 'selectbox', 'label': 'Style Lyrique', 'options': sc.get_all_styles_lyriques},
                'Structure_Chanson_Specifique': {'type': 'selectbox', 'label': 'Structure de Chanson', 'options': sc.get_all_structures_song},
                'Mots_Cles_Generation': {'type': 'text_area', 'label': 'Mots-clés de Génération (séparés par des virgules)'},
                'Langue_Paroles': {'type': 'selectbox', 'label': 'Langue des Paroles', 'options': ["Français", "Anglais", "Espagnol"]},
                'Niveau_Langage_Paroles': {'type': 'selectbox', 'label': 'Niveau de Langage Paroles', 'options': ["Familier", "Courant", "Soutenu", "Poétique", "Argotique", "Technique"]},
                'Imagerie_Texte': {'type': 'selectbox', 'label': 'Imagerie Texte', 'options': ["Forte et Descriptive", "Métaphorique", "Abstraite", "Concrète"]},
                'ID_Artiste_IA': {'type': 'selectbox', 'label': 'Artiste IA Associé', 'options': sc.get_all_artistes_ia},
                'ID_Album_Associe': {'type': 'selectbox', 'label': 'Album Associé', 'options': sc.get_all_albums},
                'Prompt_Generation_Audio': {'type': 'text_area', 'label': 'Prompt Génération Audio (pour SUNO)', 'height': 150},
                'Prompt_Generation_Paroles': {'type': 'text_area', 'label': 'Prompt Génération Paroles', 'height': 150},
                'Instrumentation_Principale': {'type': 'text_input', 'label': 'Instrumentation Principale'},
                'Effets_Production_Dominants': {'type': 'text_input', 'label': 'Effets Production Dominants'},
                'Type_Voix_Desiree': {'type': 'selectbox', 'label': 'Type de Voix Désirée', 'options': sc.get_all_voix_styles, 'id_col_for_options': 'Type_Vocal_General', 'name_col_for_options': 'Type_Vocal_General'},
                'Style_Vocal_Desire': {'type': 'text_input', 'label': 'Style Vocal Désiré (ex: Lyrique, Râpeux)'},
                'Caractere_Voix_Desire': {'type': 'text_input', 'label': 'Caractère Voix Désiré (ex: Puissant, Doux)'},
                'Mots_Cles_SEO': {'type': 'text_input', 'label': 'Mots-clés SEO'},
                'Description_Courte_Marketing': {'type': 'text_area', 'label': 'Description Courte Marketing', 'height': 100},
                'file_path_audio': {'label': 'Uploader Nouveau Fichier Audio (.mp3, .wav)', 'type': ["mp3", "wav"], 'col_name': 'URL_Audio_Local'},
                'file_path_cover': {'label': 'Uploader Nouvelle Image de Cover (.jpg, .png)', 'type': ["jpg", "png"], 'col_name': 'URL_Cover_Album'},
                'Favori': {'type': 'checkbox', 'label': 'Marquer comme Favori'}
            },
            update_function=sc.update_morceau_generes,
            form_key="update_delete_morceau_form_generic"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_morceau_id',
        session_state_name_key='confirm_delete_morceau_name',
        sheet_name_key="MORCEAUX_GENERES",
        unique_id_col='ID_Morceau',
        delete_function=sc.delete_row_from_sheet
    )

def render_audio_player_page():
    st.header("🎵 Lecteur Audios de l'Architecte Ω")
    st.write("Écoutez vos morceaux générés par l'IA, visualisez leurs paroles et marquez vos favoris. Une expérience immersive pour vos créations.")

    morceaux_df_player = sc.get_all_morceaux()
    paroles_existantes_df_player = sc.get_all_paroles_existantes()

    if not morceaux_df_player.empty:
        # Filtrage et sélection du morceau
        col_select_track, col_filter_track = st.columns([0.7, 0.3])
        
        with col_filter_track:
            st.subheader("Filtres")
            st.selectbox("Filtrer par Genre", ['Tous'] + morceaux_df_player['ID_Style_Musical_Principal'].unique().tolist(), key="player_filter_genre")
            st.selectbox("Filtrer par Artiste IA", ['Tous'] + morceaux_df_player['ID_Artiste_IA'].unique().tolist(), key="player_filter_artist")
            st.selectbox("Filtrer par Statut", ['Tous'] + morceaux_df_player['Statut_Production'].unique().tolist(), key="player_filter_status")

        filtered_morceaux_player = morceaux_df_player.copy()
        if st.session_state.player_filter_genre != 'Tous':
            filtered_morceaux_player = filtered_morceaux_player[filtered_morceaux_player['ID_Style_Musical_Principal'] == st.session_state.player_filter_genre]
        if st.session_state.player_filter_artist != 'Tous':
            filtered_morceaux_player = filtered_morceaux_player[filtered_morceaux_player['ID_Artiste_IA'] == st.session_state.player_filter_artist]
        if st.session_state.player_filter_status != 'Tous':
            filtered_morceaux_player = filtered_morceaux_player[filtered_morceaux_player['Statut_Production'] == st.session_state.player_filter_status]

        with col_select_track:
            st.subheader("Sélection du Morceau")
            if not filtered_morceaux_player.empty:
                track_options = filtered_morceaux_player.apply(lambda row: f"{row['Titre_Morceau']} ({row['ID_Morceau']}) - {row['ID_Artiste_IA']}", axis=1).tolist()
                selected_track_display = st.selectbox("Choisissez un morceau à écouter", track_options, key="player_select_track")

                selected_morceau_id = selected_track_display.split('(')[1].split(')')[0] if selected_track_display else None
                st.session_state['selected_morceau_id'] = selected_morceau_id
                
                current_morceau = filtered_morceaux_player[filtered_morceaux_player['ID_Morceau'] == st.session_state.selected_morceau_id].iloc[0] if st.session_state.selected_morceau_id else None
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
                if current_morceau['URL_Cover_Album'] and os.path.exists(cover_image_path):
                    st.image(cover_image_path, caption=current_morceau['Titre_Morceau'], use_column_width=True)
                else:
                    st.image("https://via.placeholder.com/200?text=Pas+de+Cover", caption="Aucune image de cover", use_column_width=True)
                
                st.markdown(f"**Artiste IA :** {current_morceau['ID_Artiste_IA']}")
                st.markdown(f"**Genre :** {current_morceau['ID_Style_Musical_Principal']}")
                st.markdown(f"**Durée Estimée :** {current_morceau['Durée_Estimee']}")
                st.markdown(f"**Statut :** {current_morceau['Statut_Production']}")

                # --- Fonctionnalité "Favori" ---
                if 'Favori' in morceaux_df_player.columns:
                    current_favorite_status = current_morceau.get('Favori', 'FAUX')
                    is_favorite_bool = ut.parse_boolean_string(str(current_favorite_status))

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
                else:
                    st.info("Ajoutez une colonne 'Favori' (VRAI/FAUX) à l'onglet 'MORCEAUX_GENERES' de votre Google Sheet pour activer la persistance des favoris.")
                    st.button("❤️ Ajouter aux Favoris (non persistant)", key="add_to_favorite_button_no_persist")
                
            with col_player_audio:
                if current_morceau['URL_Audio_Local'] and os.path.exists(audio_file_path):
                    st.audio(audio_file_path, format="audio/mp3", start_time=0)
                else:
                    st.warning("Fichier audio non trouvé localement ou URL non renseignée.")
                    if current_morceau['Prompt_Generation_Audio']:
                        st.info("Vous pouvez utiliser le prompt audio ci-dessous avec SUNO ou un autre générateur :")
                        st.text_area("Prompt Génération Audio", value=current_morceau['Prompt_Generation_Audio'], height=150, disabled=True)

                # --- Affichage des Paroles Associées ---
                st.markdown("---")
                st.subheader("Paroles")
                
                lyrics_from_morceau = current_morceau.get('Prompt_Generation_Paroles', '')
                
                lyrics_from_existing = ''
                if not paroles_existantes_df_player.empty:
                    matching_paroles = paroles_existantes_df_player[paroles_existantes_df_player['ID_Morceau'] == current_morceau['ID_Morceau']]
                    if not matching_paroles.empty:
                        lyrics_from_existing = matching_paroles['Paroles_Existantes'].iloc[0]

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

def render_my_albums_page():
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
        _render_add_tab(
            sheet_name_key="ALBUMS_PLANETAIRES",
            fields_config={
                'Nom_Album': {'type': 'text_input', 'label': 'Nom de l\'Album', 'required': True},
                'Date_Sortie_Prevue': {'type': 'date_input', 'label': 'Date de Sortie', 'default': datetime.now().date()},
                'Statut_Album': {'type': 'selectbox', 'label': 'Statut de l\'Album', 'options': ["En Production", "En Idée", "Mix/Master", "Publié", "Archivé"]},
                'Description_Concept_Album': {'type': 'text_area', 'label': 'Description Thématique de l\'Album'},
                'ID_Artiste_IA_Principal': {'type': 'selectbox', 'label': 'Artiste IA Principal', 'options': sc.get_all_artistes_ia, 'required': True},
                'Genre_Dominant_Album': {'type': 'selectbox', 'label': 'Genre Dominant de l\'Album', 'options': sc.get_all_styles_musicaux},
                'Mots_Cles_Album_SEO': {'type': 'text_input', 'label': 'Mots-clés SEO de l\'Album'},
                'file_upload_cover': {'label': 'Uploader Image de Pochette (.jpg, .png)', 'type': ["jpg", "png"]}
            },
            add_function=sc.add_album,
            form_key="add_album_form_generic"
        )

    with tab_albums_edit:
        _render_update_delete_tab(
            sheet_name_key="ALBUMS_PLANETAIRES",
            unique_id_col='ID_Album',
            display_col='Nom_Album',
            fields_config={
                'Nom_Album': {'type': 'text_input', 'label': 'Nom de l\'Album', 'required': True},
                'Date_Sortie_Prevue': {'type': 'date_input', 'label': 'Date de Sortie'},
                'Statut_Album': {'type': 'selectbox', 'label': 'Statut de l\'Album', 'options': ["En Production", "En Idée", "Mix/Master", "Publié", "Archivé"]},
                'Description_Concept_Album': {'type': 'text_area', 'label': 'Description Thématique de l\'Album'},
                'ID_Artiste_IA_Principal': {'type': 'selectbox', 'label': 'Artiste IA Principal', 'options': sc.get_all_artistes_ia, 'required': True},
                'Genre_Dominant_Album': {'type': 'selectbox', 'label': 'Genre Dominant de l\'Album', 'options': sc.get_all_styles_musicaux},
                'Mots_Cles_Album_SEO': {'type': 'text_input', 'label': 'Mots-clés SEO de l\'Album'},
                'file_path_cover': {'label': 'Uploader Nouvelle Image de Pochette (.jpg, .png)', 'type': ["jpg", "png"], 'col_name': 'URL_Cover_Principale'}
            },
            update_function=sc.update_album,
            form_key="update_delete_album_form_generic"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_album_id',
        session_state_name_key='confirm_delete_album_name',
        sheet_name_key="ALBUMS_PLANETAIRES",
        unique_id_col='ID_Album',
        delete_function=sc.delete_row_from_sheet
    )

def render_my_ia_artists_page():
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
        _render_add_tab(
            sheet_name_key="ARTISTES_IA_COSMIQUES",
            fields_config={
                'Nom_Artiste_IA': {'type': 'text_input', 'label': 'Nom de l\'Artiste IA', 'required': True},
                'Description_Artiste': {'type': 'text_area', 'label': 'Description de l\'Artiste (Biographie/Concept)'},
                'Genres_Predilection': {'type': 'multiselect', 'label': 'Genres de Prédilection (IDs)', 'options': sc.get_all_styles_musicaux, 'id_col_for_options': 'ID_Style_Musical'},
                'file_upload_profile_img': {'label': 'Uploader Image de Profil (.jpg, .png)', 'type': ["jpg", "png"]}
            },
            add_function=sc.add_artiste_ia,
            form_key="add_artiste_ia_form_generic"
        )

    with tab_artistes_edit:
        _render_update_delete_tab(
            sheet_name_key="ARTISTES_IA_COSMIQUES",
            unique_id_col='ID_Artiste_IA',
            display_col='Nom_Artiste_IA',
            fields_config={
                'Nom_Artiste_IA': {'type': 'text_input', 'label': 'Nom de l\'Artiste IA', 'required': True},
                'Description_Artiste': {'type': 'text_area', 'label': 'Description de l\'Artiste (Biographie/Concept)'},
                'Genres_Predilection': {'type': 'multiselect', 'label': 'Genres de Prédilection (IDs)', 'options': sc.get_all_styles_musicaux, 'id_col_for_options': 'ID_Style_Musical', 'current_value': lambda df, col: [g.strip() for g in df.get(col, '').split(',')] if df.get(col, '') else []},
                'file_path_profile_img': {'label': 'Uploader Nouvelle Image de Profil (.jpg, .png)', 'type': ["jpg", "png"], 'col_name': 'URL_Image_Profil'}
            },
            update_function=sc.update_artiste_ia,
            form_key="update_delete_artiste_ia_form_generic"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_artiste_id',
        session_state_key='confirm_delete_artiste_name',
        sheet_name_key="ARTISTES_IA_COSMIQUES",
        unique_id_col='ID_Artiste_IA',
        delete_function=sc.delete_row_from_sheet
    )

def render_existing_lyrics_page():
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
        _render_add_tab(
            sheet_name_key="PAROLES_EXISTANTES",
            fields_config={
                'Titre_Morceau': {'type': 'text_input', 'label': 'Titre du Morceau (pour ces paroles)', 'required': True},
                'Artiste_Principal': {'type': 'text_input', 'label': 'Artiste Principal (ex: Le Gardien)'},
                'Genre_Musical': {'type': 'text_input', 'label': 'Genre Musical (pour référence)'},
                'Paroles_Existantes': {'type': 'text_area', 'label': 'Collez les Paroles ici', 'required': True, 'height': 300},
                'Notes': {'type': 'text_area', 'label': 'Notes (ex: A retravailler, version finale)'}
            },
            add_function=sc.add_paroles_existantes,
            form_key="add_paroles_form_generic"
        )

    with tab_paroles_edit:
        _render_update_delete_tab(
            sheet_name_key="PAROLES_EXISTANTES",
            unique_id_col='ID_Morceau',
            display_col='Titre_Morceau',
            fields_config={
                'Titre_Morceau': {'type': 'text_input', 'label': 'Titre du Morceau', 'required': True},
                'Artiste_Principal': {'type': 'text_input', 'label': 'Artiste Principal'},
                'Genre_Musical': {'type': 'text_input', 'label': 'Genre Musical'},
                'Paroles_Existantes': {'type': 'text_area', 'label': 'Paroles', 'required': True, 'height': 300},
                'Notes': {'type': 'text_area', 'label': 'Notes'}
            },
            update_function=sc.update_paroles_existantes,
            form_key="update_delete_paroles_form_generic"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_paroles_id',
        session_state_name_key='confirm_delete_paroles_name',
        sheet_name_key="PAROLES_EXISTANTES",
        unique_id_col='ID_Morceau',
        delete_function=sc.delete_row_from_sheet
    )

def render_stats_trends_sim_page():
    st.header("📊 Stats & Tendances d'Écoute Simulées")
    st.write("Visualisez des statistiques d'écoute simulées pour vos morceaux, identifiez les tendances et suivez les performances virtuelles.")

    morceaux_pour_stats_df = sc.get_all_morceaux()
    
    with st.form("stats_simulation_form"):
        st.subheader("Paramètres de Simulation")
        morceaux_options_stats = _get_options_for_selectbox(morceaux_pour_stats_df, 'ID_Morceau', 'Titre_Morceau')
        morceaux_pour_stats = st.multiselect(
            "Sélectionnez les Morceaux à Simuler",
            morceaux_options_stats[1:] if not morceaux_pour_stats_df.empty else [], # Exclude the empty option
            key="stats_morceaux_a_simuler"
        )
        nombre_mois_simulation = st.number_input("Nombre de Mois à Simuler", min_value=1, max_value=36, value=12, step=1, key="stats_nombre_mois")
        submit_stats_simulation = st.form_submit_button("Simuler les Statistiques")

        if submit_stats_simulation:
            if morceaux_pour_stats:
                selected_morceau_ids = [_get_id_from_display_string(s) for s in morceaux_pour_stats]
                with st.spinner("L'Oracle simule les tendances d'écoute..."):
                    stats_df = go.simulate_streaming_stats(selected_morceau_ids, nombre_mois_simulation)
                    st.session_state['simulated_stats_df'] = stats_df
                    st.success("Statistiques simulées avec succès !")
            else:
                st.warning("Veuillez sélectionner au moins un morceau.")

    if 'simulated_stats_df' in st.session_state and not st.session_state.simulated_stats_df.empty:
        st.markdown("---")
        st.subheader("Statistiques d'Écoute Simulées")
        display_dataframe(ut.format_dataframe_for_display(st.session_state.simulated_stats_df), key="simulated_stats_display")

        st.markdown("---")
        st.subheader("Visualisations (Exemple)")
        if 'Mois_Annee_Stat' in st.session_state.simulated_stats_df.columns and 'Ecoutes_Totales' in st.session_state.simulated_stats_df.columns:
            try:
                plot_df = st.session_state.simulated_stats_df.pivot_table(
                    index='Mois_Annee_Stat', 
                    columns='ID_Morceau', 
                    values='Ecoutes_Totales', 
                    aggfunc='sum'
                ).reset_index()
                
                plot_df['Mois_Annee_Stat_dt'] = pd.to_datetime(plot_df['Mois_Annee_Stat'], format='%m-%Y')
                plot_df = plot_df.sort_values('Mois_Annee_Stat_dt')
                plot_df = plot_df.drop(columns=['Mois_Annee_Stat_dt'])

                st.line_chart(plot_df.set_index('Mois_Annee_Stat'))
                st.info("Ce graphique montre l'évolution des écoutes simulées par mois pour les morceaux sélectionnés. Des visualisations plus avancées sont possibles avec `Plotly` ou `Altair`.")
            except Exception as e:
                st.error(f"Erreur lors de la création du graphique: {e}")
                st.info("Assurez-vous que vos données simulées sont numériques et que le format de date est correct.")
        else:
            st.info("Données insuffisantes ou format incorrect pour la visualisation.")

def render_strategic_directives_page():
    st.header("🎯 Directives Stratégiques de l'Oracle")
    st.write("Recevez des conseils stratégiques de l'Oracle pour optimiser vos créations et votre présence musicale.")

    artistes_ia_list = sc.get_all_artistes_ia()['Nom_Artiste_IA'].tolist()
    genres_musicaux_list = sc.get_all_styles_musicaux()['ID_Style_Musical'].tolist()

    with st.form("strategic_directive_form"):
        st.subheader("Paramètres de la Directive")
        st.text_area("Quel est votre objectif principal pour cet artiste/morceau/album ? (ex: 'Maximiser les écoutes sur les plateformes', 'Développer une communauté de fans')", key="directive_objectif") # Removed 'required=True'
        st.selectbox("Artiste IA concerné", [''] + artistes_ia_list, key="directive_artiste_ia") # Removed 'required=True'
        st.selectbox("Genre dominant de l'artiste/projet", [''] + genres_musicaux_list, key="directive_genre_dominant") # Removed 'required=True'
        
        st.info("Les données simulées peuvent influencer la directive. Effectuez une simulation de stats pour les morceaux pertinents avant de générer la directive.")
        st.text_area("Résumé des données et performances actuelles (optionnel, ex: '5k écoutes en 1 mois sur Spotify')", key="directive_donnees_resume")
        st.text_area("Tendances actuelles du marché à prendre en compte (optionnel, ex: 'TikTok est clé pour les artistes émergents')", key="directive_tendances_actuelles")
        
        submit_directive = st.form_submit_button("Obtenir la Directive Stratégique")

        if submit_directive:
            # Manual validation
            required_directive_fields = {
                "directive_objectif": "Objectif Principal",
                "directive_artiste_ia": "Artiste IA concerné",
                "directive_genre_dominant": "Genre dominant de l'artiste/projet"
            }

            all_directive_fields_filled = True
            for field_key, field_name in required_directive_fields.items():
                if not st.session_state.get(field_key):
                    st.warning(f"Veuillez remplir le champ obligatoire : {field_name}.")
                    all_directive_fields_filled = False
                    break

            if all_directive_fields_filled:
                with st.spinner("L'Oracle élabore une stratégie..."):
                    directive = go.generate_strategic_directive(
                        objectif_strategique=st.session_state.directive_objectif,
                        nom_artiste_ia=st.session_state.directive_artiste_ia,
                        genre_dominant=st.session_state.directive_genre_dominant,
                        donnees_simulees_resume=st.session_state.directive_donnees_resume,
                        tendances_actuelles=st.session_state.directive_tendances_actuelles
                    )
                    st.session_state['strategic_directive'] = directive
                    st.success("Directive stratégique générée !")
                # else: validation message is handled by the loop above

    if 'strategic_directive' in st.session_state and st.session_state.strategic_directive:
        st.markdown("---")
        st.subheader("Directive Stratégique de l'Oracle")
        st.text_area("Voici les recommandations de l'Oracle :", value=st.session_state.strategic_directive, height=300, key="directive_output")

def render_viral_potential_niches_page():
    st.header("📈 Analyse du Potentiel Viral et des Niches")
    st.write("Identifiez les éléments de vos morceaux qui pourraient attirer un large public et explorez les niches musicales potentielles.")
    
    morceaux_all_viral = sc.get_all_morceaux()
    public_cible_list = sc.get_all_public_cible()['ID_Public'].tolist()

    with st.form("viral_potential_form"):
        st.subheader("Paramètres d'Analyse")
        morceau_to_analyze_display = st.selectbox(
            "Sélectionnez le Morceau à Analyser",
            _get_options_for_selectbox(morceaux_all_viral, 'ID_Morceau', 'Titre_Morceau'),
            key="viral_morceau_a_analyser" # Removed 'required=True'
        )
        morceau_to_analyze_id = _get_id_from_display_string(morceau_to_analyze_display)

        st.selectbox("Public Cible Principal de ce morceau", [''] + public_cible_list, key="viral_public_cible") # Removed 'required=True'
        st.text_area("Tendances actuelles du marché général à considérer (ex: 'Popularité croissante des vidéos courtes sur TikTok')", key="viral_current_trends")
        
        submit_viral_analysis = st.form_submit_button("Analyser le Potentiel Viral")

        if submit_viral_analysis:
            # Manual validation
            if morceau_to_analyze_id and st.session_state.viral_public_cible:
                selected_morceau_data = morceaux_all_viral[morceaux_all_viral['ID_Morceau'] == morceau_to_analyze_id].iloc[0].to_dict()
                with st.spinner("L'Oracle analyse le potentiel viral..."):
                    viral_analysis_result = go.analyze_viral_potential_and_niche_recommendations(
                        morceau_data=selected_morceau_data,
                        public_cible_id=st.session_state.viral_public_cible,
                        current_trends=st.session_state.viral_current_trends
                    )
                    st.session_state['viral_analysis_result'] = viral_analysis_result
                    st.success("Analyse du potentiel viral terminée !")
            else:
                st.warning("Veuillez sélectionner un morceau et un public cible.")

    if 'viral_analysis_result' in st.session_state and st.session_state.viral_analysis_result:
        st.markdown("---")
        st.subheader("Analyse du Potentiel Viral et Recommandations de Niche")
        st.text_area("Analyse de l'Oracle :", value=st.session_state.viral_analysis_result, height=400, key="viral_analysis_output")

def render_musical_styles_page():
    st.header("🎸 Styles Musicaux")
    st.write("Gérez les styles musicaux et leurs descriptions détaillées pour guider l'Oracle.")
    styles_musicaux_df = sc.get_all_styles_musicaux()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Styles", "Ajouter un Nouveau Style", "Mettre à Jour/Supprimer Style"])
    with tab_view:
        st.subheader("Voir et Rechercher des Styles Musicaux")
        search_query = st.text_input("Rechercher par nom de style ou description", key="search_musical_styles")
        df_display = styles_musicaux_df
        if search_query:
            df_display = styles_musicaux_df[styles_musicaux_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="musical_styles_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="STYLES_MUSICAUX_GALACTIQUES",
            fields_config={
                'Nom_Style_Musical': {'type': 'text_input', 'label': 'Nom du Style Musical', 'required': True},
                'Description_Detaillee': {'type': 'text_area', 'label': 'Description Détaillée'},
                'Artistes_References': {'type': 'text_area', 'label': 'Artistes Références (séparés par des virgules)'},
                'Exemples_Sonores': {'type': 'text_input', 'label': 'Exemples Sonores (URL ou description)'}
            },
            add_function=sc.add_style_musical,
            form_key="add_musical_style_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="STYLES_MUSICAUX_GALACTIQUES",
            unique_id_col='ID_Style_Musical',
            display_col='Nom_Style_Musical',
            fields_config={
                'Nom_Style_Musical': {'type': 'text_input', 'label': 'Nom du Style Musical', 'required': True},
                'Description_Detaillee': {'type': 'text_area', 'label': 'Description Détaillée'},
                'Artistes_References': {'type': 'text_area', 'label': 'Artistes Références (séparés par des virgules)'},
                'Exemples_Sonores': {'type': 'text_input', 'label': 'Exemples Sonores (URL ou description)'}
            },
            update_function=sc.update_style_musical,
            form_key="update_delete_musical_style_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_style_id',
        session_state_name_key='confirm_delete_style_name',
        sheet_name_key="STYLES_MUSICAUX_GALACTIQUES",
        unique_id_col='ID_Style_Musical',
        delete_function=sc.delete_row_from_sheet
    )

def render_lyrical_styles_page():
    st.header("📝 Styles Lyriques")
    st.write("Gérez les styles lyriques et leurs descriptions détaillées pour affiner la génération de paroles.")
    styles_lyriques_df = sc.get_all_styles_lyriques()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Styles", "Ajouter un Nouveau Style", "Mettre à Jour/Supprimer Style"])
    with tab_view:
        st.subheader("Voir et Rechercher des Styles Lyriques")
        search_query = st.text_input("Rechercher par nom de style ou description", key="search_lyrical_styles")
        df_display = styles_lyriques_df
        if search_query:
            df_display = styles_lyriques_df[styles_lyriques_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="lyrical_styles_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="STYLES_LYRIQUES_UNIVERS",
            fields_config={
                'Nom_Style_Lyrique': {'type': 'text_input', 'label': 'Nom du Style Lyrique', 'required': True},
                'Description_Detaillee': {'type': 'text_area', 'label': 'Description Détaillée'},
                'Auteurs_References': {'type': 'text_area', 'label': 'Auteurs Références (séparés par des virgules)'},
                'Exemples_Textuels_Courts': {'type': 'text_area', 'label': 'Exemples Textuels Courts'}
            },
            add_function=sc.add_style_lyrique,
            form_key="add_lyrical_style_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="STYLES_LYRIQUES_UNIVERS",
            unique_id_col='ID_Style_Lyrique',
            display_col='Nom_Style_Lyrique',
            fields_config={
                'Nom_Style_Lyrique': {'type': 'text_input', 'label': 'Nom du Style Lyrique', 'required': True},
                'Description_Detaillee': {'type': 'text_area', 'label': 'Description Détaillée'},
                'Auteurs_References': {'type': 'text_area', 'label': 'Auteurs Références (séparés par des virgules)'},
                'Exemples_Textuels_Courts': {'type': 'text_area', 'label': 'Exemples Textuels Courts'}
            },
            update_function=sc.update_style_lyrique,
            form_key="update_delete_lyrical_style_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_style_lyrique_id',
        session_state_name_key='confirm_delete_style_lyrique_name',
        sheet_name_key="STYLES_LYRIQUES_UNIVERS",
        unique_id_col='ID_Style_Lyrique',
        delete_function=sc.delete_row_from_sheet
    )

def render_themes_concepts_page():
    st.header("🌌 Thèmes & Concepts")
    st.write("Gérez les thèmes et concepts qui peuvent être utilisés dans vos créations musicales.")
    themes_df = sc.get_all_themes()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Thèmes", "Ajouter un Nouveau Thème", "Mettre à Jour/Supprimer Thème"])
    with tab_view:
        st.subheader("Voir et Rechercher des Thèmes")
        search_query = st.text_input("Rechercher par nom de thème ou description", key="search_themes")
        df_display = themes_df
        if search_query:
            df_display = themes_df[themes_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="themes_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="THEMES_CONSTELLES",
            fields_config={
                'Nom_Theme': {'type': 'text_input', 'label': 'Nom du Thème', 'required': True},
                'Description_Conceptuelle': {'type': 'text_area', 'label': 'Description Conceptuelle'},
                'Mots_Cles_Associes': {'type': 'text_area', 'label': 'Mots-clés Associés (séparés par des virgules)'}
            },
            add_function=sc.add_theme,
            form_key="add_theme_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="THEMES_CONSTELLES",
            unique_id_col='ID_Theme',
            display_col='Nom_Theme',
            fields_config={
                'Nom_Theme': {'type': 'text_input', 'label': 'Nom du Thème', 'required': True},
                'Description_Conceptuelle': {'type': 'text_area', 'label': 'Description Conceptuelle'},
                'Mots_Cles_Associes': {'type': 'text_area', 'label': 'Mots-clés Associés (séparés par des virgules)'}
            },
            update_function=sc.update_theme,
            form_key="update_delete_theme_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_theme_id',
        session_state_name_key='confirm_delete_theme_name',
        sheet_name_key="THEMES_CONSTELLES",
        unique_id_col='ID_Theme',
        delete_function=sc.delete_row_from_sheet
    )

def render_moods_emotions_page():
    st.header("❤️ Moods & Émotions")
    st.write("Gérez les moods et émotions pour affiner l'expression musicale et lyrique.")
    moods_df = sc.get_all_moods()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Moods", "Ajouter un Nouveau Mood", "Mettre à Jour/Supprimer Mood"])
    with tab_view:
        st.subheader("Voir et Rechercher des Moods")
        search_query = st.text_input("Rechercher par nom de mood ou description", key="search_moods")
        df_display = moods_df
        if search_query:
            df_display = moods_df[moods_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="moods_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="MOODS_ET_EMOTIONS",
            fields_config={
                'Nom_Mood': {'type': 'text_input', 'label': 'Nom du Mood', 'required': True},
                'Description_Nuance': {'type': 'text_area', 'label': 'Description de la Nuance'},
                'Niveau_Intensite': {'type': 'number_input', 'label': 'Niveau d\'Intensité (1-5)', 'min_value': 1, 'max_value': 5, 'default': 3, 'step': 1},
                'Mots_Cles_Associes': {'type': 'text_area', 'label': 'Mots-clés Associés (séparés par des virgules)'},
                'Couleur_Associee': {'type': 'text_input', 'label': 'Couleur Associée (ex: Rouge, #FF0000)'},
                'Tempo_Range_Suggerer': {'type': 'text_input', 'label': 'Tempo Suggéré (ex: 80-120 BPM)'}
            },
            add_function=sc.add_mood,
            form_key="add_mood_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="MOODS_ET_EMOTIONS",
            unique_id_col='ID_Mood',
            display_col='Nom_Mood',
            fields_config={
                'Nom_Mood': {'type': 'text_input', 'label': 'Nom du Mood', 'required': True},
                'Description_Nuance': {'type': 'text_area', 'label': 'Description de la Nuance'},
                'Niveau_Intensite': {'type': 'number_input', 'label': 'Niveau d\'Intensité (1-5)', 'min_value': 1, 'max_value': 5, 'step': 1},
                'Mots_Cles_Associes': {'type': 'text_area', 'label': 'Mots-clés Associés (séparés par des virgules)'},
                'Couleur_Associee': {'type': 'text_input', 'label': 'Couleur Associée (ex: Rouge, #FF0000)'},
                'Tempo_Range_Suggerer': {'type': 'text_input', 'label': 'Tempo Suggéré (ex: 80-120 BPM)'}
            },
            update_function=sc.update_mood,
            form_key="update_delete_mood_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_mood_id',
        session_state_name_key='confirm_delete_mood_name',
        sheet_name_key="MOODS_ET_EMOTIONS",
        unique_id_col='ID_Mood',
        delete_function=sc.delete_row_from_sheet
    )

def render_instruments_voices_page():
    st.header("🎤 Instruments & Voix")
    st.write("Gérez les instruments orchestraux et les styles vocaux utilisés par l'Oracle.")

    instruments_df = sc.get_all_instruments()
    voix_styles_df = sc.get_all_voix_styles()

    tab_instruments, tab_voix_styles = st.tabs(["Instruments Orchestraux", "Styles Vocaux"])

    with tab_instruments:
        st.subheader("Instruments Orchestraux")
        display_dataframe(ut.format_dataframe_for_display(instruments_df), key="instruments_display")
        
        st.markdown("##### Ajouter un Instrument")
        _render_add_tab(
            sheet_name_key="INSTRUMENTS_ORCHESTRAUX",
            fields_config={
                'Nom_Instrument': {'type': 'text_input', 'label': 'Nom de l\'Instrument', 'required': True},
                'Type_Instrument': {'type': 'text_input', 'label': 'Type d\'Instrument', 'required': True},
                'Sonorité_Caractéristique': {'type': 'text_area', 'label': 'Sonorité Caractéristique'},
                'Utilisation_Prevalente': {'type': 'text_area', 'label': 'Utilisation Prévalente'},
                'Famille_Sonore': {'type': 'text_input', 'label': 'Famille Sonore'}
            },
            add_function=sc.add_instrument,
            form_key="add_instrument_form_tab"
        )
        st.markdown("##### Mettre à Jour/Supprimer un Instrument")
        _render_update_delete_tab(
            sheet_name_key="INSTRUMENTS_ORCHESTRAUX",
            unique_id_col='ID_Instrument',
            display_col='Nom_Instrument',
            fields_config={
                'Nom_Instrument': {'type': 'text_input', 'label': 'Nom', 'required': True},
                'Type_Instrument': {'type': 'text_input', 'label': 'Type', 'required': True},
                'Sonorité_Caractéristique': {'type': 'text_area', 'label': 'Sonorité'},
                'Utilisation_Prevalente': {'type': 'text_area', 'label': 'Utilisation'},
                'Famille_Sonore': {'type': 'text_input', 'label': 'Famille'}
            },
            update_function=sc.update_instrument,
            form_key="update_delete_instrument_form_tab"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_instrument_id',
        session_state_name_key='confirm_delete_instrument_name',
        sheet_name_key="INSTRUMENTS_ORCHESTRAUX",
        unique_id_col='ID_Instrument',
        delete_function=sc.delete_row_from_sheet
    )

    with tab_voix_styles:
        st.subheader("Styles Vocaux")
        display_dataframe(ut.format_dataframe_for_display(voix_styles_df), key="voix_styles_display")
        
        st.markdown("##### Ajouter un Style Vocal")
        _render_add_tab(
            sheet_name_key="VOIX_ET_STYLES_VOCAUX",
            fields_config={
                'Type_Vocal_General': {'type': 'text_input', 'label': 'Type Vocal Général', 'required': True},
                'Tessiture_Specifique': {'type': 'text_input', 'label': 'Tessiture Spécifique (ex: Soprano, N/A)'},
                'Style_Vocal_Detaille': {'type': 'text_area', 'label': 'Style Vocal Détaillé', 'required': True},
                'Caractere_Expressif': {'type': 'text_input', 'label': 'Caractère Expressif'},
                'Effets_Voix_Souhaites': {'type': 'text_area', 'label': 'Effets Voix Souhaités'}
            },
            add_function=sc.add_voix_style,
            form_key="add_vocal_style_form_tab"
        )
        st.markdown("##### Mettre à Jour/Supprimer un Style Vocal")
        _render_update_delete_tab(
            sheet_name_key="VOIX_ET_STYLES_VOCAUX",
            unique_id_col='ID_Vocal',
            display_col='Style_Vocal_Detaille',
            fields_config={
                'Type_Vocal_General': {'type': 'text_input', 'label': 'Type', 'required': True},
                'Tessiture_Specifique': {'type': 'text_input', 'label': 'Tessiture'},
                'Style_Vocal_Detaille': {'type': 'text_area', 'label': 'Style Détaillé', 'required': True},
                'Caractere_Expressif': {'type': 'text_input', 'label': 'Caractère'},
                'Effets_Voix_Souhaites': {'type': 'text_area', 'label': 'Effets'}
            },
            update_function=sc.update_voix_style,
            form_key="update_delete_vocal_style_form_tab"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_vocal_id',
        session_state_name_key='confirm_delete_vocal_name',
        sheet_name_key="VOIX_ET_STYLES_VOCAUX",
        unique_id_col='ID_Vocal',
        delete_function=sc.delete_row_from_sheet
    )

def render_song_structures_page():
    st.header("🏛️ Structures de Chanson")
    st.write("Gérez les modèles de structure de chanson que l'Oracle peut utiliser.")
    structures_df = sc.get_all_structures_song()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Structures", "Ajouter une Nouvelle Structure", "Mettre à Jour/Supprimer Structure"])
    with tab_view:
        st.subheader("Voir et Rechercher des Structures de Chanson")
        search_query = st.text_input("Rechercher par nom de structure ou schéma", key="search_structures")
        df_display = structures_df
        if search_query:
            df_display = structures_df[structures_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="structures_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="STRUCTURES_SONG_UNIVERSELLES",
            fields_config={
                'Nom_Structure': {'type': 'text_input', 'label': 'Nom de la Structure', 'required': True},
                'Schema_Detaille': {'type': 'text_area', 'label': 'Schéma Détaillé (ex: Intro > Couplet > Refrain)', 'required': True},
                'Notes_Application_IA': {'type': 'text_area', 'label': 'Notes d\'Application pour l\'IA'}
            },
            add_function=sc.add_structure_song,
            form_key="add_structure_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="STRUCTURES_SONG_UNIVERSELLES",
            unique_id_col='ID_Structure',
            display_col='Nom_Structure',
            fields_config={
                'Nom_Structure': {'type': 'text_input', 'label': 'Nom de la Structure', 'required': True},
                'Schema_Detaille': {'type': 'text_area', 'label': 'Schéma Détaillé', 'required': True},
                'Notes_Application_IA': {'type': 'text_area', 'label': 'Notes d\'Application pour l\'IA'}
            },
            update_function=sc.update_structure_song,
            form_key="update_delete_structure_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_structure_id',
        session_state_name_key='confirm_delete_structure_name',
        sheet_name_key="STRUCTURES_SONG_UNIVERSELLES",
        unique_id_col='ID_Structure',
        delete_function=sc.delete_row_from_sheet
    )

def render_generation_rules_page():
    st.header("⚖️ Règles de Génération de l'Oracle")
    st.write("Gérez les règles qui guident le comportement de l'Oracle lors de la génération de contenu.")
    regles_df = sc.get_all_regles_generation()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Règles", "Ajouter une Nouvelle Règle", "Mettre à Jour/Supprimer Règle"])
    with tab_view:
        st.subheader("Voir et Rechercher des Règles de Génération")
        search_query = st.text_input("Rechercher par nom de règle ou description", key="search_regles")
        df_display = regles_df
        if search_query:
            df_display = regles_df[regles_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="regles_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="REGLES_DE_GENERATION_ORACLE",
            fields_config={
                'Type_Regle': {'type': 'text_input', 'label': 'Type de Règle (ex: Contrainte de Langage)', 'required': True},
                'Description_Regle': {'type': 'text_area', 'label': 'Description de la Règle', 'required': True},
                'Impact_Sur_Generation': {'type': 'text_input', 'label': 'Impact sur Génération (ex: Directive Pré-Génération)'},
                'Statut_Actif': {'type': 'checkbox', 'label': 'Statut Actif', 'default': True}
            },
            add_function=sc.add_regle_generation,
            form_key="add_regle_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="REGLES_DE_GENERATION_ORACLE",
            unique_id_col='ID_Regle',
            display_col='Type_Regle',
            fields_config={
                'Type_Regle': {'type': 'text_input', 'label': 'Type de Règle', 'required': True},
                'Description_Regle': {'type': 'text_area', 'label': 'Description de la Règle', 'required': True},
                'Impact_Sur_Generation': {'type': 'text_input', 'label': 'Impact sur Génération'},
                'Statut_Actif': {'type': 'checkbox', 'label': 'Statut Actif'}
            },
            update_function=sc.update_regle_generation,
            form_key="update_delete_regle_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_regle_id',
        session_state_name_key='confirm_delete_regle_name',
        sheet_name_key="REGLES_DE_GENERATION_ORACLE",
        unique_id_col='ID_Regle',
        delete_function=sc.delete_row_from_sheet
    )

def render_current_projects_page():
    st.header("🚧 Projets en Cours")
    st.write("Suivez l'avancement de vos projets musicaux, de l'idée à la publication.")
    projets_df = sc.get_all_projets_en_cours()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Projets", "Ajouter un Nouveau Projet", "Mettre à Jour/Supprimer Projet"])
    with tab_view:
        st.subheader("Voir et Rechercher des Projets")
        search_query = st.text_input("Rechercher par nom de projet ou statut", key="search_projets")
        df_display = projets_df
        if search_query:
            df_display = projets_df[projets_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="projets_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="PROJETS_EN_COURS",
            fields_config={
                'Nom_Projet': {'type': 'text_input', 'label': 'Nom du Projet', 'required': True},
                'Type_Projet': {'type': 'selectbox', 'label': 'Type de Projet', 'options': ["Single", "EP", "Album"], 'required': True},
                'Statut_Projet': {'type': 'selectbox', 'label': 'Statut du Projet', 'options': ["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"], 'required': True},
                'Date_Debut': {'type': 'date_input', 'label': 'Date de Début', 'default': datetime.now().date()},
                'Date_Cible_Fin': {'type': 'date_input', 'label': 'Date Cible de Fin', 'default': (datetime.now() + pd.DateOffset(months=3)).date()},
                'ID_Morceaux_Lies': {'type': 'text_input', 'label': 'IDs Morceaux Liés (séparés par des virgules)'},
                'Notes_Production': {'type': 'text_area', 'label': 'Notes de Production'},
                'Budget_Estime': {'type': 'number_input', 'label': 'Budget Estimé (€)', 'min_value': 0.0, 'default': 0.0, 'step': 10.0}
            },
            add_function=sc.add_projet_en_cours,
            form_key="add_projet_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="PROJETS_EN_COURS",
            unique_id_col='ID_Projet',
            display_col='Nom_Projet',
            fields_config={
                'Nom_Projet': {'type': 'text_input', 'label': 'Nom du Projet', 'required': True},
                'Type_Projet': {'type': 'selectbox', 'label': 'Type de Projet', 'options': ["Single", "EP", "Album"]},
                'Statut_Projet': {'type': 'selectbox', 'label': 'Statut du Projet', 'options': ["En Idée", "En Production", "Mix/Master", "Promotion", "Terminé"]},
                'Date_Debut': {'type': 'date_input', 'label': 'Date de Début'},
                'Date_Cible_Fin': {'type': 'date_input', 'label': 'Date Cible de Fin'},
                'ID_Morceaux_Lies': {'type': 'text_input', 'label': 'IDs Morceaux Liés (séparés par des virgules)'},
                'Notes_Production': {'type': 'text_area', 'label': 'Notes de Production'},
                'Budget_Estime': {'type': 'number_input', 'label': 'Budget Estimé (€)', 'min_value': 0.0, 'step': 10.0}
            },
            update_function=sc.update_projet_en_cours,
            form_key="update_delete_projet_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_projet_id',
        session_state_name_key='confirm_delete_projet_name',
        sheet_name_key="PROJETS_EN_COURS",
        unique_id_col='ID_Projet',
        delete_function=sc.delete_row_from_sheet
    )

def render_ai_tools_referenced_page():
    st.header("🛠️ Outils IA Référencés")
    st.write("Consultez les outils IA externes référencés qui peuvent compléter les capacités de l'Architecte Ω.")
    outils_ia_df = sc.get_all_outils_ia()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Outils", "Ajouter un Nouvel Outil", "Mettre à Jour/Supprimer Outil"])
    with tab_view:
        st.subheader("Voir et Rechercher des Outils IA")
        search_query = st.text_input("Rechercher par nom d'outil ou fonction", key="search_outils")
        df_display = outils_ia_df
        if search_query:
            df_display = outils_ia_df[outils_ia_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="outils_display")
        
        st.markdown("---")
        st.subheader("Liens Directs vers les Outils")
        for index, row in df_display.iterrows():
            if row['URL_Outil']:
                st.markdown(f"**[{row['Nom_Outil']}]({row['URL_Outil']})** : {row['Description_Fonctionnalite']}")
    with tab_add:
        _render_add_tab(
            sheet_name_key="OUTILS_IA_REFERENCEMENT",
            fields_config={
                'Nom_Outil': {'type': 'text_input', 'label': 'Nom de l\'Outil', 'required': True},
                'Description_Fonctionnalite': {'type': 'text_area', 'label': 'Description de la Fonctionnalité', 'required': True},
                'Type_Fonction': {'type': 'text_input', 'label': 'Type de Fonction (ex: Génération audio, Mastering)', 'required': True},
                'URL_Outil': {'type': 'text_input', 'label': 'URL de l\'Outil'},
                'Compatibilite_API': {'type': 'checkbox', 'label': 'Compatibilité API', 'default': False},
                'Prix_Approximatif': {'type': 'text_input', 'label': 'Prix Approximatif'},
                'Evaluation_Gardien': {'type': 'number_input', 'label': 'Évaluation Gardien (1-5)', 'min_value': 1, 'max_value': 5, 'default': 3, 'step': 1},
                'Notes_Utilisation': {'type': 'text_area', 'label': 'Notes d\'Utilisation'}
            },
            add_function=sc.add_outil_ia,
            form_key="add_outil_ia_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="OUTILS_IA_REFERENCEMENT",
            unique_id_col='ID_Outil',
            display_col='Nom_Outil',
            fields_config={
                'Nom_Outil': {'type': 'text_input', 'label': 'Nom de l\'Outil', 'required': True},
                'Description_Fonctionnalite': {'type': 'text_area', 'label': 'Description de la Fonctionnalité', 'required': True},
                'Type_Fonction': {'type': 'text_input', 'label': 'Type de Fonction', 'required': True},
                'URL_Outil': {'type': 'text_input', 'label': 'URL de l\'Outil'},
                'Compatibilite_API': {'type': 'checkbox', 'label': 'Compatibilité API'},
                'Prix_Approximatif': {'type': 'text_input', 'label': 'Prix Approximatif'},
                'Evaluation_Gardien': {'type': 'number_input', 'label': 'Évaluation Gardien (1-5)', 'min_value': 1, 'max_value': 5, 'step': 1},
                'Notes_Utilisation': {'type': 'text_area', 'label': 'Notes d\'Utilisation'}
            },
            update_function=sc.update_outil_ia,
            form_key="update_delete_outil_ia_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_outil_id',
        session_state_name_key='confirm_delete_outil_name',
        sheet_name_key="OUTILS_IA_REFERENCEMENT",
        unique_id_col='ID_Outil',
        delete_function=sc.delete_row_from_sheet
    )

def render_cultural_events_timeline_page():
    st.header("🗓️ Timeline des Événements Culturels")
    st.write("Consultez et gérez les événements majeurs pour planifier vos lancements musicaux et campagnes promotionnelles.")
    timeline_df = sc.get_all_timeline_evenements()
    tab_view, tab_add, tab_edit = st.tabs(["Voir/Rechercher Événements", "Ajouter un Nouvel Événement", "Mettre à Jour/Supprimer Événement"])
    with tab_view:
        st.subheader("Voir et Rechercher des Événements")
        search_query = st.text_input("Rechercher par nom d'événement ou genre", key="search_timeline")
        df_display = timeline_df
        if search_query:
            df_display = timeline_df[timeline_df.apply(lambda row: search_query.lower() in row.astype(str).str.lower().to_string(), axis=1)]
        display_dataframe(ut.format_dataframe_for_display(df_display), key="timeline_display")
    with tab_add:
        _render_add_tab(
            sheet_name_key="TIMELINE_EVENEMENTS_CULTURELS",
            fields_config={
                'Nom_Evenement': {'type': 'text_input', 'label': 'Nom de l\'Événement', 'required': True},
                'Date_Debut': {'type': 'date_input', 'label': 'Date de Début', 'default': datetime.now().date()},
                'Date_Fin': {'type': 'date_input', 'label': 'Date de Fin', 'default': datetime.now().date()},
                'Type_Evenement': {'type': 'selectbox', 'label': 'Type d\'Événement', 'options': ["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"], 'required': True},
                'Genre_Associe': {'type': 'text_input', 'label': 'Genre(s) Associé(s) (séparés par des virgules)'},
                'Public_Associe': {'type': 'text_input', 'label': 'Public(s) Associé(s) (IDs séparés par virgules)'},
                'Notes_Strategiques': {'type': 'text_area', 'label': 'Notes Stratégiques'}
            },
            add_function=sc.add_timeline_event,
            form_key="add_timeline_event_form"
        )
    with tab_edit:
        _render_update_delete_tab(
            sheet_name_key="TIMELINE_EVENEMENTS_CULTURELS",
            unique_id_col='ID_Evenement',
            display_col='Nom_Evenement',
            fields_config={
                'Nom_Evenement': {'type': 'text_input', 'label': 'Nom de l\'Événement', 'required': True},
                'Date_Debut': {'type': 'date_input', 'label': 'Date de Début'},
                'Date_Fin': {'type': 'date_input', 'label': 'Date de Fin'},
                'Type_Evenement': {'type': 'selectbox', 'label': 'Type d\'Événement', 'options': ["Festival", "Conférence", "Mois Thématique", "Cérémonie de récompenses", "Fête", "Journée Thématique"]},
                'Genre_Associe': {'type': 'text_input', 'label': 'Genre(s) Associé(s)'},
                'Public_Associe': {'type': 'text_input', 'label': 'Public(s) Associé(s)'},
                'Notes_Strategiques': {'type': 'text_area', 'label': 'Notes Stratégiques'}
            },
            update_function=sc.update_timeline_event,
            form_key="update_delete_timeline_event_form"
        )
    _handle_generic_delete_confirmation(
        session_state_id_key='confirm_delete_event_id',
        session_state_name_key='confirm_delete_event_name',
        sheet_name_key="TIMELINE_EVENEMENTS_CULTURELS",
        unique_id_col='ID_Evenement',
        delete_function=sc.delete_row_from_sheet
    )

def render_oracle_history_page():
    st.header("📚 Historique de l'Oracle")
    st.write("Consultez l'historique de toutes vos interactions avec l'Oracle Architecte et évaluez ses générations.")

    historique_df = sc.get_all_historique_generations()

    tab_historique_view, tab_historique_feedback, tab_style_agent = st.tabs(["Voir Historique", "Donner du Feedback", "Agent de Style Personnel"])

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
            unrated_generations = historique_df[historique_df['Evaluation_Manuelle'] == '']
            if not unrated_generations.empty:
                gen_options_feedback = unrated_generations.apply(lambda row: f"{row['ID_GenLog']} - {row['Type_Generation']} ({row['Date_Heure']})", axis=1).tolist()
                gen_to_feedback_id_display = st.selectbox(
                    "Sélectionnez une génération à évaluer",
                    gen_options_feedback,
                    key="select_gen_to_feedback"
                )
                gen_to_feedback_id = unrated_generations[unrated_generations.apply(lambda row: f"{row['ID_GenLog']} - {row['Type_Generation']} ({row['Date_Heure']})" == gen_to_feedback_id_display, axis=1)]['ID_GenLog'].iloc[0]

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

    with tab_style_agent:
        st.subheader("Agent de Style Personnel de l'Oracle")
        st.write("L'Oracle analyse vos préférences basées sur votre historique de feedback positif pour vous suggérer de nouvelles directions créatives.")
        if not historique_df.empty:
            if st.button("Demander une Suggestion de Style à l'Oracle", key="ask_style_agent"):
                with st.spinner("L'Oracle analyse votre style personnel..."):
                    style_suggestion = go.analyze_and_suggest_personal_style(historique_df)
                    st.session_state['personal_style_suggestion'] = style_suggestion
                    st.success("Suggestion de style personnel générée !")
            
            if 'personal_style_suggestion' in st.session_state and st.session_state.personal_style_suggestion:
                st.markdown("---")
                st.text_area("Votre Agent de Style personnel suggère :", value=st.session_state.personal_style_suggestion, height=400, key="style_agent_output")
        else:
            st.info("L'historique de générations est vide. L'Oracle a besoin de plus d'interactions pour analyser votre style.")


# --- Mapping des pages aux fonctions de rendu ---
page_render_functions = {
    'Accueil': render_home_page,
    'Générateur de Contenu': render_content_generator_page,
    'Co-pilote Créatif': render_copilot_creative_page,
    'Création Multimodale': render_multimodal_creation_page,
    'Mes Morceaux': render_my_tracks_page,
    'Mes Albums': render_my_albums_page,
    'Mes Artistes IA': render_my_ia_artists_page,
    'Paroles Existantes': render_existing_lyrics_page,
    'Stats & Tendances Sim.': render_stats_trends_sim_page,
    'Directives Stratégiques': render_strategic_directives_page,
    'Potentiel Viral & Niches': render_viral_potential_niches_page,
    'Styles Musicaux': render_musical_styles_page,
    'Styles Lyriques': render_lyrical_styles_page,
    'Thèmes & Concepts': render_themes_concepts_page,
    'Moods & Émotions': render_moods_emotions_page,
    'Instruments & Voix': render_instruments_voices_page,
    'Structures de Chanson': render_song_structures_page,
    'Règles de Génération': render_generation_rules_page,
    'Projets en Cours': render_current_projects_page,
    'Outils IA Référencés': render_ai_tools_referenced_page,
    'Timeline Événements': render_cultural_events_timeline_page,
    "Historique de l'Oracle": render_oracle_history_page,
    'Lecteur Audios': render_audio_player_page
}

# --- Affichage du contenu de la page actuelle ---
if st.session_state['current_page'] in page_render_functions:
    page_render_functions[st.session_state['current_page']]()
else:
    st.error("Page non trouvée.")
