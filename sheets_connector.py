# sheets_connector.py (Mise à jour)
import streamlit as st
import gspread
# REMOVE THESE IMPORTS, no longer needed for service account auth
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from google.auth.transport.requests import Request
import os
import pandas as pd
from datetime import datetime
import random

# Importe les configurations
import config
import utils


# Variables globales pour le client gspread et la feuille de calcul
gc = None
spreadsheet = None
worksheet_oeuvres = None

@st.cache_resource
def get_gspread_client_and_worksheets():
    global gc, spreadsheet, worksheet_oeuvres
    
    # Récupérer les identifiants du compte de service depuis Streamlit secrets
    # Assurez-vous que votre fichier secrets.toml aura la structure suivante pour le service account:
    # [gsheets_service_account]
    # type = "service_account"
    # project_id = "your-gcp-project-id"
    # private_key_id = "your-private-key-id"
    # private_key = "your-private-key"
    # client_email = "your-service-account-email"
    # client_id = "your-client-id"
    # auth_uri = "https://accounts.google.com/o/oauth2/auth"
    # token_uri = "https://oauth2.googleapis.com/token"
    # auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    # client_x509_cert_url = "your-client-cert-url"
    
    # Charger les identifiants sous forme de dict JSON
    try:
        creds_json = {
            "type": st.secrets["gsheets_service_account"]["type"],
            "project_id": st.secrets["gsheets_service_account"]["project_id"],
            "private_key_id": st.secrets["gsheets_service_account"]["private_key_id"],
            "private_key": st.secrets["gsheets_service_account"]["private_key"].replace("\\n", "\n"), # Important: les sauts de ligne doivent être réels
            "client_email": st.secrets["gsheets_service_account"]["client_email"],
            "client_id": st.secrets["gsheets_service_account"]["client_id"],
            "auth_uri": st.secrets["gsheets_service_account"]["auth_uri"],
            "token_uri": st.secrets["gsheets_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gsheets_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gsheets_service_account"]["client_x509_cert_url"]
        }
        
        # Authentifier gspread avec les identifiants du compte de service
        gc = gspread.service_account_from_dict(creds_json)
        
        spreadsheet = gc.open_by_url(config.SPREADSHEET_URL)
        worksheet_oeuvres = spreadsheet.worksheet(config.WORKSHEET_NAME_OEUVRES)
        
        print("Connexion à Google Sheets établie avec succès via Compte de Service.")
        return gc, spreadsheet, worksheet_oeuvres
    except Exception as e:
        st.error(f"Erreur lors de la connexion à Google Sheets via Compte de Service : {e}")
        st.error("Vérifiez la configuration de 'gsheets_service_account' dans votre fichier .streamlit/secrets.toml.")
        st.stop() # Arrête l'application si l'authentification échoue

    try:
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_url(config.SPREADSHEET_URL)
        worksheet_oeuvres = spreadsheet.worksheet(config.WORKSHEET_NAME_OEUVRES)
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Feuille de calcul introuvable à l'URL : {config.SPREADSHEET_URL}. Veuillez vérifier l'URL et les permissions.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound as e:
        st.error(f"L'une des feuilles de calcul nécessaires n'a pas été trouvée : {e}. Veuillez vous assurer que les onglets spécifiés dans config.py existent.")
        st.stop()
    except Exception as e:
        st.error(f"Erreur inattendue lors de la connexion à Google Sheets : {e}")
        st.stop()

    return gc, spreadsheet, worksheet_oeuvres

@st.cache_data(ttl=3600)
def load_data_from_sheet(worksheet_name):
    """Charge toutes les données d'un onglet spécifique depuis Google Sheets."""
    try:
        if spreadsheet is None:
            raise Exception("Google Sheets client not initialized. Call get_gspread_client_and_worksheets() first.")

        current_worksheet = spreadsheet.worksheet(worksheet_name)
        data = current_worksheet.get_all_records()
        df = pd.DataFrame(data)

        if worksheet_name == config.WORKSHEET_NAME_OEUVRES:
            expected_cols = [
                'ID_Oeuvre', 'Titre_Original', 'Titre_Optimise', 'Date_Creation', 'Statut_Publication',
                'Description_Courte', 'URL_Texte_Local', 'Prompt_Image_Genere', 'URL_Image_Couverture',
                'Prompt_Image_1', 'Prompt_Image_2', 'Prompt_Image_3',
                'Titre_Suggere_1', 'Titre_Suggere_2', 'Titre_Suggere_3', 'Resume_Suggere', 'Tags_Suggérés',
                'Tags_Manuels', 'Plateforme_Publication', 'Notes_Editeur', 'Texte_Genere',
                'ID_Parent_Serie', 'Numero_Tome'
            ]
            for col in expected_cols:
                if col not in df.columns:
                    df[col] = ''
            df['Numero_Tome'] = pd.to_numeric(df['Numero_Tome'], errors='coerce').fillna(0)

        elif worksheet_name == config.WORKSHEET_NAME_TENDANCES:
            expected_cols_tendances = ['Date_Analyse', 'Niche_Identifiee', 'Popularite_Score', 'Competition_Niveau', 'Mots_Cles_Associes', 'Tendances_Generales', 'Source_Information']
            for col in expected_cols_tendances:
                if col not in df.columns:
                    df[col] = ''
            df['Date_Analyse'] = pd.to_datetime(df['Date_Analyse'], errors='coerce')
            df['Popularite_Score'] = pd.to_numeric(df['Popularite_Score'], errors='coerce').fillna(0)

        elif worksheet_name == config.WORKSHEET_NAME_PERFORMANCE:
            expected_cols_performance = ['ID_Oeuvre', 'Mois_Annee', 'Revenus_Nets', 'Vues_Telechargements', 'Engagement_Score', 'Commentaires_Mois']
            for col in expected_cols_performance:
                if col not in df.columns:
                    df[col] = ''
            df['Mois_Annee'] = pd.to_datetime(df['Mois_Annee'], format='%m-%Y', errors='coerce')
            df['Revenus_Nets'] = pd.to_numeric(df['Revenus_Nets'], errors='coerce').fillna(0)
            df['Vues_Telechargements'] = pd.to_numeric(df['Vues_Telechargements'], errors='coerce').fillna(0)
            df['Engagement_Score'] = pd.to_numeric(df['Engagement_Score'], errors='coerce').fillna(0)

        elif worksheet_name == config.WORKSHEET_NAME_UNIVERS:
            expected_cols_univers = ['ID_Univers', 'Nom_Univers', 'Description_Globale', 'Elements_Cles_Intrigue', 'Personnages_Cles', 'Notes_Internes']
            for col in expected_cols_univers:
                if col not in df.columns:
                    df[col] = ''

        elif worksheet_name == config.WORKSHEET_NAME_STYLES:
            expected_cols_styles = ['ID_Style', 'Nom_Style', 'Description_Style', 'Exemples_Textuels', 'Niveau_Explicite_Defaut', 'Notes_Internes']
            for col in expected_cols_styles:
                if col not in df.columns:
                    df[col] = ''

        return df
    except gspread.exceptions.WorksheetNotFound:
        st.warning(f"L'onglet '{worksheet_name}' n'a pas été trouvé. Veuillez le créer dans votre Google Sheet.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Erreur lors du chargement des données depuis Google Sheets (onglet '{worksheet_name}') : {e}")
        return pd.DataFrame()


def append_rows_to_sheet(worksheet_name, data_list):
    """
    Ajoute une liste de dictionnaires (chaque dict est une ligne) à un onglet donné.
    Les clés des dictionnaires doivent correspondre aux en-têtes de colonnes.
    """
    try:
        if spreadsheet is None:
            raise Exception("Google Sheets client not initialized. Call get_gspread_client_and_worksheets() first.")

        target_worksheet = spreadsheet.worksheet(worksheet_name)
        headers = target_worksheet.row_values(1)

        rows_to_append = []
        for item_data in data_list:
            row = []
            for header in headers:
                value = item_data.get(header, "")
                row.append(value)
            rows_to_append.append(row)

        if rows_to_append:
            target_worksheet.append_rows(rows_to_append)
            st.success(f"{len(rows_to_append)} nouvelles entrées ajoutées à l'onglet '{worksheet_name}'!")
            return True
        else:
            st.info(f"Aucune donnée à ajouter à l'onglet '{worksheet_name}'.")
            return False
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Erreur: L'onglet '{worksheet_name}' n'a pas été trouvé dans Google Sheets.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de l'ajout de données à l'onglet '{worksheet_name}' : {e}")
        return False

def save_new_oeuvre_to_sheet(generated_text, image_prompts, launch_kit,
                             titre_original, description_courte, id_parent_serie="", numero_tome=""):
    """
    Sauvegarde une nouvelle œuvre générée dans l'onglet 'Oeuvres' et localement.
    """
    try:
        if worksheet_oeuvres is None:
            raise Exception("Google Sheets client not initialized for Oeuvres worksheet. Call get_gspread_client_and_worksheets() first.")

        oeuvre_id = f"OEUVRE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}"
        date_creation = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        clean_title_for_filename = utils.clean_filename_slug(titre_original)
        local_text_filename = f"{oeuvre_id}_{clean_title_for_filename}.txt"
        local_text_filepath_full = os.path.join(config.TEXTS_FOLDER, local_text_filename) # Full path for saving
        url_texte_local = os.path.join(os.path.basename(config.ASSETS_FOLDER), os.path.basename(config.TEXTS_FOLDER), local_text_filename) # Relative path to assets folder for sheet

        try:
            with open(local_text_filepath_full, "w", encoding="utf-8") as f:
                f.write(generated_text)
            st.info(f"Texte sauvegardé localement : `{local_text_filepath_full}`")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde locale du texte : {e}")
            url_texte_local = "Erreur de sauvegarde locale" # Mark it in sheet if saving failed


        new_oeuvre_data = {
            'ID_Oeuvre': oeuvre_id,
            'Titre_Original': titre_original,
            'Titre_Optimise': launch_kit.get('titles', [''])[0],
            'Date_Creation': date_creation,
            'Statut_Publication': 'Brouillon',
            'Description_Courte': description_courte if description_courte else launch_kit.get('summary', ''),
            'URL_Texte_Local': url_texte_local,
            'Prompt_Image_Genere': '',
            'URL_Image_Couverture': '',
            'Prompt_Image_1': image_prompts[0] if len(image_prompts) > 0 else '',
            'Prompt_Image_2': image_prompts[1] if len(image_prompts) > 1 else '',
            'Prompt_Image_3': image_prompts[2] if len(image_prompts) > 2 else '',
            'Titre_Suggere_1': launch_kit.get('titles', [''])[0],
            'Titre_Suggere_2': launch_kit.get('titles', ['', ''])[1],
            'Titre_Suggere_3': launch_kit.get('titles', ['', '', ''])[2],
            'Resume_Suggere': launch_kit.get('summary', ''),
            'Tags_Suggérés': ", ".join(launch_kit.get('tags', [])),
            'Tags_Manuels': '',
            'Plateforme_Publication': 'Non publié',
            'Notes_Editeur': '',
            'Texte_Genere': generated_text,
            'ID_Parent_Serie': id_parent_serie,
            'Numero_Tome': numero_tome
        }

        success = append_rows_to_sheet(config.WORKSHEET_NAME_OEUVRES, [new_oeuvre_data])
        return success

    except Exception as e:
        st.error(f"Erreur globale lors de la sauvegarde de la nouvelle œuvre : {e}")
        return False


def update_oeuvre_in_sheet(oeuvre_id, updates_dict):
    """Met à jour les champs spécifiés d'une œuvre existante dans l'onglet 'Oeuvres'."""
    try:
        if worksheet_oeuvres is None:
            raise Exception("Google Sheets client not initialized for Oeuvres worksheet. Call get_gspread_client_and_worksheets() first.")

        headers = worksheet_oeuvres.row_values(1)
        col_map = {header: i+1 for i, header in enumerate(headers)}

        try:
            cell = worksheet_oeuvres.find(oeuvre_id, in_column=col_map['ID_Oeuvre'])
            row_index = cell.row
        except gspread.exceptions.CellNotFound:
            st.error(f"Erreur : Œuvre avec ID '{oeuvre_id}' non trouvée dans Google Sheets.")
            return False

        updates_list = []
        for col_name, value in updates_dict.items():
            if col_name in col_map:
                if col_name == 'Numero_Tome':
                    try:
                        value = int(value) if pd.notna(value) and str(value).strip() != '' else ''
                    except ValueError:
                        value = ''
                updates_list.append({
                    'range': gspread.utils.rowcol_to_a1(row_index, col_map[col_name]),
                    'values': [[value]]
                })

        if updates_list:
            worksheet_oeuvres.batch_update(updates_list)
            st.success(f"Œuvre '{oeuvre_id}' mise à jour avec succès dans Google Sheets!")
            return True
        else:
            st.info("Aucune modification à appliquer.")
            return False

    except Exception as e:
        st.error(f"Erreur lors de la mise à jour de l'œuvre dans Google Sheets : {e}")
        return False

# Fonction générique pour mettre à jour une ligne par ID dans n'importe quel onglet
def update_row_by_id(worksheet_name, id_column, row_id, updates_dict):
    """
    Met à jour les champs spécifiés d'une ligne existante dans un onglet donné, basée sur un ID.
    :param worksheet_name: Nom de l'onglet à modifier.
    :param id_column: Nom de la colonne contenant l'ID unique (ex: 'ID_Univers', 'ID_Style').
    :param row_id: La valeur de l'ID à trouver.
    :param updates_dict: Dictionnaire {nom_colonne: nouvelle_valeur} des champs à mettre à jour.
    """
    try:
        if spreadsheet is None:
            raise Exception("Google Sheets client not initialized. Call get_gspread_client_and_worksheets() first.")

        target_worksheet = spreadsheet.worksheet(worksheet_name)
        headers = target_worksheet.row_values(1)
        col_map = {header: i+1 for i, header in enumerate(headers)}

        search_value = str(row_id)
        try:
            cell = target_worksheet.find(search_value, in_column=col_map[id_column])
            row_index = cell.row
        except gspread.exceptions.CellNotFound:
            st.error(f"Erreur : Entrée avec ID '{row_id}' non trouvée dans l'onglet '{worksheet_name}'.")
            return False

        updates_list = []
        for col_name, value in updates_dict.items():
            if col_name in col_map:
                updates_list.append({
                    'range': gspread.utils.rowcol_to_a1(row_index, col_map[col_name]),
                    'values': [[value]]
                })

        if updates_list:
            target_worksheet.batch_update(updates_list)
            st.success(f"Entrée '{row_id}' mise à jour avec succès dans l'onglet '{worksheet_name}'!")
            return True
        else:
            st.info("Aucune modification à appliquer.")
            return False

    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Erreur: L'onglet '{worksheet_name}' n'a pas été trouvé dans Google Sheets.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la mise à jour de l'entrée dans l'onglet '{worksheet_name}' : {e}")
        return False

# NOUVEAU: Fonction générique pour supprimer une ligne par ID
def delete_row_by_id(worksheet_name, id_column, row_id):
    """
    Supprime une ligne d'un onglet donné, basée sur un ID.
    :param worksheet_name: Nom de l'onglet à modifier.
    :param id_column: Nom de la colonne contenant l'ID unique (ex: 'ID_Univers', 'ID_Style').
    :param row_id: La valeur de l'ID de la ligne à supprimer.
    """
    try:
        if spreadsheet is None:
            raise Exception("Google Sheets client not initialized. Call get_gspread_client_and_worksheets() first.")

        target_worksheet = spreadsheet.worksheet(worksheet_name)
        headers = target_worksheet.row_values(1)
        col_map = {header: i+1 for i, header in enumerate(headers)}

        search_value = str(row_id)
        try:
            cell = target_worksheet.find(search_value, in_column=col_map[id_column])
            row_index = cell.row
        except gspread.exceptions.CellNotFound:
            st.warning(f"Impossible de supprimer : Entrée avec ID '{row_id}' non trouvée dans l'onglet '{worksheet_name}'.")
            return False

        target_worksheet.delete_rows(row_index)
        st.success(f"Entrée '{row_id}' supprimée avec succès de l'onglet '{worksheet_name}'!")
        return True

    except gspread.exceptions.WorksheetNotFound:
        st.error(f"Erreur: L'onglet '{worksheet_name}' n'a pas été trouvé dans Google Sheets pour la suppression.")
        return False
    except Exception as e:
        st.error(f"Erreur lors de la suppression de l'entrée dans l'onglet '{worksheet_name}' : {e}")
        return False


# Initialise la connexion aux sheets au démarrage du module
gc, spreadsheet, worksheet_oeuvres = get_gspread_client_and_worksheets()