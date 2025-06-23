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
        # Récupère la chaîne Base64 de la clé du compte de service
        # Cette clé doit être configurée dans .streamlit/secrets.toml sous le nom GCP_SERVICE_ACCOUNT_B64
        service_account_info_b64 = st.secrets["GCP_SERVICE_ACCOUNT_B64"]
        
        # Décode la chaîne Base64 en JSON (c'est ici que l'erreur précédente se situait dans ma logique)
        # La clé privée dans le JSON original peut contenir des retours à la ligne '\n'.
        # Lorsque le JSON est encodé en Base64, ces '\n' sont préservés.
        # Après décodage Base64, nous obtenons la chaîne JSON originale.
        # json.loads() va alors correctement interpréter les '\n' dans la clé privée.
        service_account_info_json_str = base64.b64decode(service_account_info_b64).decode('utf-8')
        creds = json.loads(service_account_info_json_str)
        
        # Initialise le client gspread avec le dictionnaire de credentials
        gc = gspread.service_account_from_dict(creds)
        return gc
    except KeyError:
        st.error("La clé 'GCP_SERVICE_ACCOUNT_B64' est manquante dans votre fichier .streamlit/secrets.toml. Veuillez la configurer.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur d'authentification gspread. Assurez-vous que la clé GCP_SERVICE_ACCOUNT_B64 est correctement encodée et configurée: {e}")
        # Pour le debug, on peut imprimer la chaîne décodée avant le chargement JSON si l'erreur persiste ici:
        # st.code(service_account_info_json_str)
        st.stop() # Arrête l'exécution de l'application si l'authentification échoue

gc = get_gspread_client()

# --- Fonctions d'interaction avec Google Sheets ---

@st.cache_data(ttl=600) # Mise en cache des données lues pendant 10 minutes
def get_dataframe_from_sheet(sheet_name: str) -> pd.DataFrame:
    """
    Lit un onglet spécifique du Google Sheet et le retourne sous forme de DataFrame Pandas.
    Vérifie la présence des colonnes attendues.
    """
    try:
        spreadsheet = gc.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAMES[sheet_name])
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # Vérifier si les colonnes attendues sont présentes
        if sheet_name in EXPECTED_COLUMNS:
            missing_cols = [col for col in EXPECTED_COLUMNS[sheet_name] if col not in df.columns]
            if missing_cols:
                st.warning(f"Attention: Les colonnes suivantes sont manquantes dans l'onglet '{sheet_name}': {', '.join(missing_cols)}. Veuillez les ajouter dans votre Google Sheet.")
                # Ajouter les colonnes manquantes au DataFrame pour éviter les erreurs futures
                for col in missing_cols:
                    df[col] = ''
            # Réordonner les colonnes selon EXPECTED_COLUMNS
            # S'assurer que toutes les colonnes attendues sont présentes avant de réordonner
            for col in EXPECTED_COLUMNS[sheet_name]:
                if col not in df.columns:
                    df[col] = '' # Ajoutez-les si manquantes avec une valeur par défaut
            df = df[EXPECTED_COLUMNS[sheet_name]] # Réordonner

        # Gérer les types de données spécifiques
        if sheet_name == WORKSHEET_NAMES["REGLES_DE_GENERATION_ORACLE"]:
            if 'Statut_Actif' in df.columns:
                df['Statut_Actif'] = df['Statut_Actif'].apply(parse_boolean_string)
        
        # Pour les colonnes numériques, convertir en numérique si possible
        numeric_cols_to_check = {
            WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"]: ['Ecoutes_Totales', 'J_aimes_Recus', 'Partages_Simules', 'Revenus_Simules_Streaming'],
            WORKSHEET_NAMES["MOODS_ET_EMOTIONS"]: ['Niveau_Intensite'],
            WORKSHEET_NAMES["PROJETS_EN_COURS"]: ['Budget_Estime'],
            WORKSHEET_NAMES["OUTILS_IA_REFERENCEMENT"]: ['Evaluation_Gardien']
        }
        if sheet_name in numeric_cols_to_check:
            for col in numeric_cols_to_check[sheet_name]:
                if col in df.columns:
                    if 'Revenus' in col or 'Budget' in col: # Float pour les montants
                        df[col] = df[col].apply(safe_cast_to_float)
                    else: # Int pour les autres chiffres
                        df[col] = df[col].apply(safe_cast_to_int)


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
        # Ceci est particulièrement utile si de nouvelles colonnes sont ajoutées au modèle.
        expected_cols_for_sheet = EXPECTED_COLUMNS.get(WORKSHEET_NAMES[sheet_name], current_headers)
        
        ordered_values = [row_data.get(col, '') for col in expected_cols_for_sheet]
        
        worksheet.append_row(ordered_values)
        st.cache_data.clear() # Invalider le cache après une écriture
        return True
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
        id_col_index = worksheet.find(unique_id_col).col
        
        # Trouver la cellule contenant la valeur de l'ID unique
        cell = worksheet.find(unique_id_value, in_column=id_col_index)
        row_index = cell.row

        # Récupérer toutes les valeurs de l'en-tête pour s'assurer d'avoir le bon ordre
        headers = worksheet.row_values(1)
        
        # Récupérer les valeurs actuelles de la ligne pour ne modifier que les champs concernés
        current_row_values = worksheet.row_values(row_index)
        updated_values = current_row_values[:] # Copie pour modification
        
        for col_name, new_value in row_data.items():
            if col_name in headers:
                col_index = headers.index(col_name)
                updated_values[col_index] = new_value
            else:
                st.warning(f"La colonne '{col_name}' n'existe pas dans l'onglet '{sheet_name}'. Ignoré lors de la mise à jour.")

        # Mettre à jour toute la ligne
        worksheet.update(f'A{row_index}', [updated_values])
        st.cache_data.clear() # Invalider le cache après une écriture
        return True
    except gspread.exceptions.CellNotFound:
        st.error(f"L'identifiant '{unique_id_value}' n'a pas été trouvé dans la colonne '{unique_id_col}' de l'onglet '{sheet_name}'.")
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
        
        id_col_index = worksheet.find(unique_id_col).col
        cell = worksheet.find(unique_id_value, in_column=id_col_index)
        worksheet.delete_rows(cell.row)
        st.cache_data.clear() # Invalider le cache après une suppression
        return True
    except gspread.exceptions.CellNotFound:
        st.error(f"L'identifiant '{unique_id_value}' n'a pas été trouvé dans la colonne '{unique_id_col}' de l'onglet '{sheet_name}'.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la suppression de la ligne dans l'onglet '{sheet_name}': {e}")
        return False

# --- Fonctions spécifiques pour chaque onglet (simplifiées ici pour les ajouts) ---

def add_morceau_generes(data: dict) -> bool:
    data['ID_Morceau'] = generate_unique_id('M')
    data['Date_Creation'] = datetime.now().strftime('%Y-%m-%d')
    data['Date_Mise_A_Jour'] = datetime.now().strftime('%Y-%m-%d')
    return append_row_to_sheet("MORCEAUX_GENERES", data)

def update_morceau_generes(morceau_id: str, data: dict) -> bool:
    data['Date_Mise_A_Jour'] = datetime.now().strftime('%Y-%m-%d')
    return update_row_in_sheet("MORCEAUX_GENERES", 'ID_Morceau', morceau_id, data)

def add_historique_generation(data: dict) -> bool:
    data['ID_GenLog'] = generate_unique_id('LOG')
    data['Date_Heure'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Assurez-vous que 'user_id' est initialisé dans st.session_state si utilisé
    data['ID_Utilisateur'] = st.session_state.get('user_id', 'Gardien')
    return append_row_to_sheet("HISTORIQUE_GENERATIONS", data)

# Ajout de fonctions pour les nouveaux onglets si nécessaire (par exemple, pour les onglets des bibliothèques)
# Ces fonctions sont des wrappers pour append_row_to_sheet et update_row_in_sheet,
# pour ajouter des ID uniques ou des dates si nécessaire, avant l'appel générique.

def add_album(data: dict) -> bool:
    data['ID_Album'] = generate_unique_id('A')
    # Ajouter Date_Sortie_Prevue si non présente, ou s'assurer du format
    if 'Date_Sortie_Prevue' not in data or not data['Date_Sortie_Prevue']:
        data['Date_Sortie_Prevue'] = datetime.now().strftime('%Y-%m-%d')
    return append_row_to_sheet("ALBUMS_PLANETAIRES", data)

def update_album(album_id: str, data: dict) -> bool:
    return update_row_in_sheet("ALBUMS_PLANETAIRES", 'ID_Album', album_id, data)

def add_artiste_ia(data: dict) -> bool:
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
    data['ID_Style_Musical'] = generate_unique_id('SM')
    return append_row_to_sheet("STYLES_MUSICAUX_GALACTIQUES", data)

def update_style_musical(style_id: str, data: dict) -> bool:
    return update_row_in_sheet("STYLES_MUSICAUX_GALACTIQUES", 'ID_Style_Musical', style_id, data)

def add_style_lyrique(data: dict) -> bool:
    data['ID_Style_Lyrique'] = generate_unique_id('SL')
    return append_row_to_sheet("STYLES_LYRIQUES_UNIVERS", data)

def update_style_lyrique(style_id: str, data: dict) -> bool:
    return update_row_in_sheet("STYLES_LYRIQUES_UNIVERS", 'ID_Style_Lyrique', style_id, data)

def add_theme(data: dict) -> bool:
    data['ID_Theme'] = generate_unique_id('TH')
    return append_row_to_sheet("THEMES_CONSTELLES", data)

def update_theme(theme_id: str, data: dict) -> bool:
    return update_row_in_sheet("THEMES_CONSTELLES", 'ID_Theme', theme_id, data)

def add_mood(data: dict) -> bool:
    data['ID_Mood'] = generate_unique_id('MOOD')
    return append_row_to_sheet("MOODS_ET_EMOTIONS", data)

def update_mood(mood_id: str, data: dict) -> bool:
    return update_row_in_sheet("MOODS_ET_EMOTIONS", 'ID_Mood', mood_id, data)

def add_instrument(data: dict) -> bool:
    data['ID_Instrument'] = generate_unique_id('INST')
    return append_row_to_sheet("INSTRUMENTS_ORCHESTRAUX", data)

def update_instrument(instrument_id: str, data: dict) -> bool:
    return update_row_in_sheet("INSTRUMENTS_ORCHESTRAUX", 'ID_Instrument', instrument_id, data)

def add_voix_style(data: dict) -> bool:
    data['ID_Vocal'] = generate_unique_id('VOC')
    return append_row_to_sheet("VOIX_ET_STYLES_VOCAUX", data)

def update_voix_style(vocal_id: str, data: dict) -> bool:
    return update_row_in_sheet("VOIX_ET_STYLES_VOCAUX", 'ID_Vocal', vocal_id, data)

def add_structure_song(data: dict) -> bool:
    data['ID_Structure'] = generate_unique_id('STR')
    return append_row_to_sheet("STRUCTURES_SONG_UNIVERSELLES", data)

def update_structure_song(structure_id: str, data: dict) -> bool:
    return update_row_in_sheet("STRUCTURES_SONG_UNIVERSELLES", 'ID_Structure', structure_id, data)

def add_regle_generation(data: dict) -> bool:
    data['ID_Regle'] = generate_unique_id('REGLE')
    return append_row_to_sheet("REGLES_DE_GENERATION_ORACLE", data)

def update_regle_generation(regle_id: str, data: dict) -> bool:
    return update_row_in_sheet("REGLES_DE_GENERATION_ORACLE", 'ID_Regle', regle_id, data)

def add_projet_en_cours(data: dict) -> bool:
    data['ID_Projet'] = generate_unique_id('PROJ')
    # Les dates sont gérées par app.py avant d'appeler cette fonction
    return append_row_to_sheet("PROJETS_EN_COURS", data)

def update_projet_en_cours(projet_id: str, data: dict) -> bool:
    return update_row_in_sheet("PROJETS_EN_COURS", 'ID_Projet', projet_id, data)

def add_outil_ia(data: dict) -> bool:
    data['ID_Outil'] = generate_unique_id('IA')
    return append_row_to_sheet("OUTILS_IA_REFERENCEMENT", data)

def update_outil_ia(outil_id: str, data: dict) -> bool:
    return update_row_in_sheet("OUTILS_IA_REFERENCEMENT", 'ID_Outil', outil_id, data)

def add_timeline_event(data: dict) -> bool:
    data['ID_Evenement'] = generate_unique_id('EV')
    # Les dates sont gérées par app.py avant d'appeler cette fonction
    return append_row_to_sheet("TIMELINE_EVENEMENTS_CULTURELS", data)

def update_timeline_event(event_id: str, data: dict) -> bool:
    return update_row_in_sheet("TIMELINE_EVENEMENTS_CULTURELS", 'ID_Evenement', event_id, data)

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
