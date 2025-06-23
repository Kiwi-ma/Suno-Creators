# sheets_connector.py

import streamlit as st
import gspread
import pandas as pd
from config import SHEET_NAME, WORKSHEET_NAMES, EXPECTED_COLUMNS
from datetime import datetime
from utils import generate_unique_id, parse_boolean_string, safe_cast_to_int, safe_cast_to_float
import base64
import json # Nécessaire pour décoder le JSON de la clé

# --- Initialisation de la connexion à Google Sheets ---
@st.cache_resource(ttl=3600) # Mise en cache de la connexion pendant 1 heure
def get_gspread_client():
    """
    Initialise et retourne un client gspread authentifié.
    Utilise les secrets Streamlit pour l'authentification du compte de service (clé JSON encodée en Base64).
    """
    try:
        service_account_info_b64 = st.secrets["GCP_SERVICE_ACCOUNT_B64"]
        
        # Décode la chaîne Base64 en JSON. Gère les retours à la ligne qui peuvent être dans la clé privée.
        service_account_info_json_str = base64.b64decode(service_account_info_b64).decode('utf-8')
        creds = json.loads(service_account_info_json_str)
        
        gc = gspread.service_account_from_dict(creds)
        return gc
    except KeyError:
        st.error("La clé 'GCP_SERVICE_ACCOUNT_B64' est manquante dans votre fichier .streamlit/secrets.toml. Veuillez la configurer.")
        st.stop()
    except json.JSONDecodeError as e:
        st.error(f"Erreur de décodage JSON de la clé de service. Assurez-vous que le contenu Base64 est un JSON valide: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Erreur d'authentification gspread. Assurez-vous que la clé GCP_SERVICE_ACCOUNT_B64 est correctement encodée et configurée: {e}")
        st.stop()

gc = get_gspread_client()

# --- Fonctions d'interaction avec Google Sheets ---

@st.cache_data(ttl=600) # Mise en cache des données lues pendant 10 minutes
def get_dataframe_from_sheet(sheet_name: str) -> pd.DataFrame:
    """
    Lit un onglet spécifique du Google Sheet et le retourne sous forme de DataFrame Pandas.
    Vérifie la présence des colonnes attendues et tente des conversions de type.
    """
    try:
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAMES[sheet_name])
        
        # Récupère toutes les données, y compris les en-têtes
        data = worksheet.get_all_values()
        if not data:
            return pd.DataFrame(columns=EXPECTED_COLUMNS.get(WORKSHEET_NAMES[sheet_name], [])) # Retourne un DF vide avec les colonnes attendues
        
        headers = data[0]
        records = data[1:]
        df = pd.DataFrame(records, columns=headers)

        # Assurer que toutes les colonnes attendues sont présentes
        expected_cols_for_sheet = EXPECTED_COLUMNS.get(WORKSHEET_NAMES[sheet_name], headers)
        missing_cols = [col for col in expected_cols_for_sheet if col not in df.columns]
        if missing_cols:
            st.warning(f"Attention: Les colonnes suivantes sont manquantes dans l'onglet '{WORKSHEET_NAMES[sheet_name]}': {', '.join(missing_cols)}. Ajoutées avec des valeurs vides.")
            for col in missing_cols:
                df[col] = '' # Ajoute les colonnes manquantes
        
        # Réordonner les colonnes pour correspondre à l'ordre attendu
        df = df[expected_cols_for_sheet]

        # Gérer les types de données spécifiques
        if WORKSHEET_NAMES[sheet_name] == WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"]:
            if 'Statut_Actif' in df.columns:
                df['Statut_Actif'] = df['Statut_Actif'].apply(parse_boolean_string)
        if WORKSHEET_NAMES[sheet_name] == WORKSHEET_NAMES["MORCEAUX_GENERES"]:
            if 'Favori' in df.columns:
                df['Favori'] = df['Favori'].apply(parse_boolean_string)
        if WORKSHEET_NAMES[sheet_name] == WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"]:
            if 'Compatibilite_API' in df.columns:
                df['Compatibilite_API'] = df['Compatibilite_API'].apply(parse_boolean_string)

        # Pour les colonnes numériques, convertir en numérique si possible
        numeric_cols_to_check = {
            WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"]: ['Ecoutes_Totales', 'J_aimes_Recus', 'Partages_Simules', 'Revenus_Simules_Streaming'],
            WORKSHEET_NAMES["MOODS_ET_EMOTIONS"]: ['Niveau_Intensite'],
            WORKSHEET_NAMES["PROJETS_EN_COURS"]: ['Budget_Estime'],
            WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"]: ['Evaluation_Gardien']
        }
        if WORKSHEET_NAMES[sheet_name] in numeric_cols_to_check:
            for col in numeric_cols_to_check[WORKSHEET_NAMES[sheet_name]]:
                if col in df.columns:
                    if 'Revenus' in col or 'Budget' in col: # Float pour les montants
                        df[col] = df[col].apply(safe_cast_to_float)
                    else: # Int pour les autres chiffres
                        df[col] = df[col].apply(safe_cast_to_int)

        # Conversion des colonnes de date au format YYYY-MM-DD
        for col in ['Date_Creation', 'Date_Mise_A_Jour', 'Date_Sortie_Prevue', 'Date_Debut', 'Date_Cible_Fin', 'Date_Session', 'Date_Conseil', 'Date_Debut', 'Date_Fin', 'Date_Heure']:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
                except Exception:
                    pass # Laisser la colonne telle quelle si la conversion échoue

        return df
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Le Google Sheet '{SHEET_NAME}' est introuvable. Veuillez vérifier le nom ou s'il est partagé avec le compte de service.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"L'onglet '{WORKSHEET_NAMES[sheet_name]}' est introuvable dans le Google Sheet '{SHEET_NAME}'.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur lors de la lecture de l'onglet '{sheet_name}': {e}")
        st.stop()


def append_row_to_sheet(sheet_name: str, row_data: dict) -> bool:
    """
    Ajoute une nouvelle ligne à l'onglet spécifié.
    row_data doit être un dictionnaire où les clés correspondent aux en-têtes de colonnes.
    """
    try:
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAMES[sheet_name])

        # Récupérer les en-têtes actuels de la feuille pour s'assurer de l'ordre et des colonnes manquantes
        current_headers = worksheet.row_values(1)
        
        # Assurer que toutes les colonnes attendues par l'onglet sont présentes dans row_data
        # Si une colonne attendue n'est pas dans row_data, elle sera ajoutée vide
        expected_cols_for_sheet = EXPECTED_COLUMNS.get(WORKSHEET_NAMES[sheet_name], current_headers)
        
        # Créer la liste des valeurs dans le bon ordre
        ordered_values = []
        for col in expected_cols_for_sheet:
            value = row_data.get(col, '')
            # Convertir les booléens en 'VRAI'/'FAUX' pour Google Sheets
            if isinstance(value, bool):
                value = 'VRAI' if value else 'FAUX'
            # Gérer les listes pour les transformer en chaînes
            if isinstance(value, list):
                value = ', '.join(map(str, value))
            ordered_values.append(str(value)) # Convertir toutes les valeurs en string pour gspread
        
        worksheet.append_row(ordered_values)
        st.cache_data.clear() # Invalider le cache après une écriture
        return True
    except gspread.exceptions.APIError as e:
        st.error(f"Erreur API Google Sheets lors de l'ajout à '{sheet_name}': {e.response.text}")
        return False
    except Exception as e:
        st.error(f"Erreur lors de l'ajout de la ligne à l'onglet '{sheet_name}': {e}")
        return False

def update_row_in_sheet(sheet_name: str, unique_id_col: str, unique_id_value: str, row_data: dict) -> bool:
    """
    Met à jour une ligne existante dans l'onglet spécifié, identifiée par une colonne et une valeur unique.
    unique_id_col: Nom de la colonne qui contient l'identifiant unique (ex: 'ID_Morceau').
    unique_id_value: La valeur de l'identifiant unique de la ligne à mettre à jour.
    row_data: Dictionnaire des données à mettre à jour (clés = en-têtes de colonnes).
    """
    try:
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAMES[sheet_name])
        
        # Trouver la colonne de l'ID unique
        # Utiliser `find` avec `re.compile` pour une correspondance exacte (ignorer les sous-chaînes)
        # Assure-toi que la première ligne contient les en-têtes.
        list_of_headers = worksheet.row_values(1)
        try:
            id_col_index = list_of_headers.index(unique_id_col) + 1 # +1 car gspread est 1-indexé
        except ValueError:
            st.error(f"La colonne '{unique_id_col}' est introuvable dans l'onglet '{sheet_name}'.")
            return False

        # Trouver la cellule contenant la valeur de l'ID unique
        cell = worksheet.find(unique_id_value, in_column=id_col_index)
        row_index = cell.row

        # Récupérer les valeurs actuelles de la ligne pour ne modifier que les champs concernés
        current_row_values = worksheet.row_values(row_index)
        updated_values = current_row_values[:] # Copie pour modification
        
        for col_name, new_value in row_data.items():
            if col_name in list_of_headers:
                col_idx_to_update = list_of_headers.index(col_name)
                # Convertir les booléens en 'VRAI'/'FAUX' pour Google Sheets
                if isinstance(new_value, bool):
                    new_value = 'VRAI' if new_value else 'FAUX'
                # Gérer les listes pour les transformer en chaînes
                if isinstance(new_value, list):
                    new_value = ', '.join(map(str, new_value))
                updated_values[col_idx_to_update] = str(new_value) # Convertir en string

        # Mettre à jour toute la ligne
        worksheet.update(f'A{row_index}', [updated_values])
        st.cache_data.clear() # Invalider le cache après une écriture
        return True
    except gspread.exceptions.CellNotFound:
        st.error(f"L'identifiant '{unique_id_value}' n'a pas été trouvé dans la colonne '{unique_id_col}' de l'onglet '{sheet_name}'.")
        return False
    except gspread.exceptions.APIError as e:
        st.error(f"Erreur API Google Sheets lors de la mise à jour dans '{sheet_name}': {e.response.text}")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour de la ligne dans l'onglet '{sheet_name}': {e}")
        return False

def delete_row_from_sheet(sheet_name: str, unique_id_col: str, unique_id_value: str) -> bool:
    """
    Supprime une ligne de l'onglet spécifié, identifiée par une colonne et une valeur unique.
    """
    try:
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAMES[sheet_name])
        
        list_of_headers = worksheet.row_values(1)
        try:
            id_col_index = list_of_headers.index(unique_id_col) + 1
        except ValueError:
            st.error(f"La colonne '{unique_id_col}' est introuvable dans l'onglet '{sheet_name}'.")
            return False

        cell = worksheet.find(unique_id_value, in_column=id_col_index)
        worksheet.delete_rows(cell.row)
        st.cache_data.clear() # Invalider le cache après une suppression
        return True
    except gspread.exceptions.CellNotFound:
        st.error(f"L'identifiant '{unique_id_value}' n'a pas été trouvé dans la colonne '{unique_id_col}' de l'onglet '{sheet_name}'.")
        return False
    except gspread.exceptions.APIError as e:
        st.error(f"Erreur API Google Sheets lors de la suppression dans '{sheet_name}': {e.response.text}")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la ligne dans l'onglet '{sheet_name}': {e}")
        return False

# --- Fonctions spécifiques pour chaque onglet (simplifiées pour les ajouts/mises à jour) ---
# Ces fonctions sont des wrappers qui ajoutent des ID uniques et des dates si nécessaire
# avant d'appeler les fonctions append_row_to_sheet et update_row_in_sheet.

def add_morceau_generes(data: dict) -> bool:
    if 'ID_Morceau' not in data or not data['ID_Morceau']:
        data['ID_Morceau'] = generate_unique_id('M')
    data['Date_Creation'] = datetime.now().strftime('%Y-%m-%d')
    data['Date_Mise_A_Jour'] = datetime.now().strftime('%Y-%m-%d')
    return append_row_to_sheet("MORCEAUX_GENERES", data)

def update_morceau_generes(morceau_id: str, data: dict) -> bool:
    data['Date_Mise_A_Jour'] = datetime.now().strftime('%Y-%m-%d')
    return update_row_in_sheet("MORCEAUX_GENERES", 'ID_Morceau', morceau_id, data)

def add_album(data: dict) -> bool:
    if 'ID_Album' not in data or not data['ID_Album']:
        data['ID_Album'] = generate_unique_id('A')
    if 'Date_Sortie_Prevue' in data and isinstance(data['Date_Sortie_Prevue'], datetime):
        data['Date_Sortie_Prevue'] = data['Date_Sortie_Prevue'].strftime('%Y-%m-%d')
    elif 'Date_Sortie_Prevue' not in data or not data['Date_Sortie_Prevue']:
        data['Date_Sortie_Prevue'] = datetime.now().strftime('%Y-%m-%d')
    return append_row_to_sheet("ALBUMS_PLANETAIRES", data)

def update_album(album_id: str, data: dict) -> bool:
    if 'Date_Sortie_Prevue' in data and isinstance(data['Date_Sortie_Prevue'], datetime):
        data['Date_Sortie_Prevue'] = data['Date_Sortie_Prevue'].strftime('%Y-%m-%d')
    return update_row_in_sheet("ALBUMS_PLANETAIRES", 'ID_Album', album_id, data)

def add_artiste_ia(data: dict) -> bool:
    if 'ID_Artiste_IA' not in data or not data['ID_Artiste_IA']:
        data['ID_Artiste_IA'] = generate_unique_id('AI')
    return append_row_to_sheet("ARTISTES_IA_COSMIQUES", data)

def update_artiste_ia(artiste_id: str, data: dict) -> bool:
    return update_row_in_sheet("ARTISTES_IA_COSMIQUES", 'ID_Artiste_IA', artiste_id, data)

def add_paroles_existantes(data: dict) -> bool:
    if 'ID_Morceau' not in data or not data['ID_Morceau']:
        data['ID_Morceau'] = generate_unique_id('M') # Génère si non fourni
    return append_row_to_sheet("PAROLES_EXISTANTES", data)

def update_paroles_existantes(morceau_id: str, data: dict) -> bool:
    return update_row_in_sheet("PAROLES_EXISTANTES", 'ID_Morceau', morceau_id, data)

def add_style_musical(data: dict) -> bool:
    if 'ID_Style_Musical' not in data or not data['ID_Style_Musical']:
        data['ID_Style_Musical'] = generate_unique_id('SM')
    return append_row_to_sheet("STYLES_MUSICAUX_GALACTIQUES", data)

def update_style_musical(style_id: str, data: dict) -> bool:
    return update_row_in_sheet("STYLES_MUSICAUX_GALACTIQUES", 'ID_Style_Musical', style_id, data)

def add_style_lyrique(data: dict) -> bool:
    if 'ID_Style_Lyrique' not in data or not data['ID_Style_Lyrique']:
        data['ID_Style_Lyrique'] = generate_unique_id('SL')
    return append_row_to_sheet("STYLES_LYRIQUES_UNIVERS", data)

def update_style_lyrique(style_id: str, data: dict) -> bool:
    return update_row_in_sheet("STYLES_LYRIQUES_UNIVERS", 'ID_Style_Lyrique', style_id, data)

def add_theme(data: dict) -> bool:
    if 'ID_Theme' not in data or not data['ID_Theme']:
        data['ID_Theme'] = generate_unique_id('TH')
    return append_row_to_sheet("THEMES_CONSTELLES", data)

def update_theme(theme_id: str, data: dict) -> bool:
    return update_row_in_sheet("THEMES_CONSTELLES", 'ID_Theme', theme_id, data)

def add_mood(data: dict) -> bool:
    if 'ID_Mood' not in data or not data['ID_Mood']:
        data['ID_Mood'] = generate_unique_id('MOOD')
    return append_row_to_sheet("MOODS_ET_EMOTIONS", data)

def update_mood(mood_id: str, data: dict) -> bool:
    return update_row_in_sheet("MOODS_ET_EMOTIONS", 'ID_Mood', mood_id, data)

def add_instrument(data: dict) -> bool:
    if 'ID_Instrument' not in data or not data['ID_Instrument']:
        data['ID_Instrument'] = generate_unique_id('INST')
    return append_row_to_sheet("INSTRUMENTS_ORCHESTRAUX", data)

def update_instrument(instrument_id: str, data: dict) -> bool:
    return update_row_in_sheet("INSTRUMENTS_ORCHESTRAUX", 'ID_Instrument', instrument_id, data)

def add_voix_style(data: dict) -> bool:
    if 'ID_Vocal' not in data or not data['ID_Vocal']:
        data['ID_Vocal'] = generate_unique_id('VOC')
    return append_row_to_sheet("VOIX_ET_STYLES_VOCAUX", data)

def update_voix_style(vocal_id: str, data: dict) -> bool:
    return update_row_in_sheet("VOIX_ET_STYLES_VOCAUX", 'ID_Vocal', vocal_id, data)

def add_structure_song(data: dict) -> bool:
    if 'ID_Structure' not in data or not data['ID_Structure']:
        data['ID_Structure'] = generate_unique_id('STR')
    return append_row_to_sheet("STRUCTURES_SONG_UNIVERSELLES", data)

def update_structure_song(structure_id: str, data: dict) -> bool:
    return update_row_in_sheet("STRUCTURES_SONG_UNIVERSELLES", 'ID_Structure', structure_id, data)

def add_regle_generation(data: dict) -> bool:
    if 'ID_Regle' not in data or not data['ID_Regle']:
        data['ID_Regle'] = generate_unique_id('REGLE')
    return append_row_to_sheet("REGLES_DE_GENERATION_ORACLE", data)

def update_regle_generation(regle_id: str, data: dict) -> bool:
    return update_row_in_sheet("REGLES_DE_GENERATION_ORACLE", 'ID_Regle', regle_id, data)

def add_projet_en_cours(data: dict) -> bool:
    if 'ID_Projet' not in data or not data['ID_Projet']:
        data['ID_Projet'] = generate_unique_id('PROJ')
    if 'Date_Debut' in data and isinstance(data['Date_Debut'], datetime):
        data['Date_Debut'] = data['Date_Debut'].strftime('%Y-%m-%d')
    if 'Date_Cible_Fin' in data and isinstance(data['Date_Cible_Fin'], datetime):
        data['Date_Cible_Fin'] = data['Date_Cible_Fin'].strftime('%Y-%m-%d')
    return append_row_to_sheet("PROJETS_EN_COURS", data)

def update_projet_en_cours(projet_id: str, data: dict) -> bool:
    if 'Date_Debut' in data and isinstance(data['Date_Debut'], datetime):
        data['Date_Debut'] = data['Date_Debut'].strftime('%Y-%m-%d')
    if 'Date_Cible_Fin' in data and isinstance(data['Date_Cible_Fin'], datetime):
        data['Date_Cible_Fin'] = data['Date_Cible_Fin'].strftime('%Y-%m-%d')
    return update_row_in_sheet("PROJETS_EN_COURS", 'ID_Projet', projet_id, data)

def add_outil_ia(data: dict) -> bool:
    if 'ID_Outil' not in data or not data['ID_Outil']:
        data['ID_Outil'] = generate_unique_id('IA_TOOL') # Renommé pour éviter conflit avec ID_Artiste_IA
    return append_row_to_sheet("OUTILS_IA_REFERENCEMENT", data)

def update_outil_ia(outil_id: str, data: dict) -> bool:
    return update_row_in_sheet("OUTILS_IA_REFERENCEMENT", 'ID_Outil', outil_id, data)

def add_timeline_event(data: dict) -> bool:
    if 'ID_Evenement' not in data or not data['ID_Evenement']:
        data['ID_Evenement'] = generate_unique_id('EV')
    if 'Date_Debut' in data and isinstance(data['Date_Debut'], datetime):
        data['Date_Debut'] = data['Date_Debut'].strftime('%Y-%m-%d')
    if 'Date_Fin' in data and isinstance(data['Date_Fin'], datetime):
        data['Date_Fin'] = data['Date_Fin'].strftime('%Y-%m-%d')
    return append_row_to_sheet("TIMELINE_EVENEMENTS_CULTURELS", data)

def update_timeline_event(event_id: str, data: dict) -> bool:
    if 'Date_Debut' in data and isinstance(data['Date_Debut'], datetime):
        data['Date_Debut'] = data['Date_Debut'].strftime('%Y-%m-%d')
    if 'Date_Fin' in data and isinstance(data['Date_Fin'], datetime):
        data['Date_Fin'] = data['Date_Fin'].strftime('%Y-%m-%d')
    return update_row_in_sheet("TIMELINE_EVENEMENTS_CULTURELS", 'ID_Evenement', event_id, data)

def add_historique_generation(data: dict) -> bool:
    data['ID_GenLog'] = generate_unique_id('LOG')
    data['Date_Heure'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    data['ID_Utilisateur'] = st.session_state.get('user_id', 'Gardien') # Récupère l'ID utilisateur de la session
    return append_row_to_sheet("HISTORIQUE_GENERATIONS", data)

# Fonctions génériques pour obtenir toutes les données d'un onglet
def get_all_morceaux():
    return get_dataframe_from_sheet("MORCEAUX_GENERES")

def get_all_albums():
    return get_dataframe_from_sheet("ALBUMS_PLANETAIRES")

def get_all_sessions_creatives():
    return get_dataframe_from_sheet("SESSIONS_CREATIVES_ORACLE")

def get_all_artistes_ia():
    return get_dataframe_from_sheet("ARTISTES_IA_COSMIQUES")

def get_all_styles_musicaux():
    return get_dataframe_from_sheet("STYLES_MUSICAUX_GALACTIQUES")

def get_all_styles_lyriques():
    return get_dataframe_from_sheet("STYLES_LYRIQUES_UNIVERS")

def get_all_themes():
    return get_dataframe_from_sheet("THEMES_CONSTELLES")

def get_all_stats_simulees():
    return get_dataframe_from_sheet("STATISTIQUES_ORBITALES_SIMULEES")

def get_all_conseils_strategiques():
    return get_dataframe_from_sheet("CONSEILS_STRATEGIQUES_ORACLE")

def get_all_instruments():
    return get_dataframe_from_sheet("INSTRUMENTS_ORCHESTRAUX")

def get_all_structures_song():
    return get_dataframe_from_sheet("STRUCTURES_SONG_UNIVERSELLES")

def get_all_voix_styles():
    return get_dataframe_from_sheet("VOIX_ET_STYLES_VOCAUX")

def get_all_regles_generation():
    return get_dataframe_from_sheet("REGLES_DE_GENERATION_ORACLE")

def get_all_moods():
    return get_dataframe_from_sheet("MOODS_ET_EMOTIONS")

def get_all_references_sonores():
    return get_dataframe_from_sheet("REFERENCES_SONORES_DETAILLES")

def get_all_public_cible():
    return get_dataframe_from_sheet("PUBLIC_CIBLE_DEMOGRAPHIQUE")

def get_all_prompts_types():
    return get_dataframe_from_sheet("PROMPTS_TYPES_ET_GUIDES")

def get_all_projets_en_cours():
    return get_dataframe_from_sheet("PROJETS_EN_COURS")

def get_all_outils_ia():
    return get_dataframe_from_sheet("OUTILS_IA_REFERENCEMENT")

def get_all_timeline_evenements():
    return get_dataframe_from_sheet("TIMELINE_EVENEMENTS_CULTURELS")

def get_all_paroles_existantes():
    return get_dataframe_from_sheet("PAROLES_EXISTANTES")

def get_all_historique_generations():
    return get_dataframe_from_sheet("HISTORIQUE_GENERATIONS")
