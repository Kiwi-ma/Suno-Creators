# config.py
import os

# Google Sheets Configuration
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
GOOGLE_CREDENTIALS_FILE = 'credentials.json'
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1Lq3UnBYWFAHO2QEbCDkzh04Zfr8vK8SvrNazil8_tzA/edit?usp=sharing' # VOTRE URL ICI

# Sheet Names
WORKSHEET_NAME_OEUVRES = 'Oeuvres'
WORKSHEET_NAME_TENDANCES = 'Tendances_Marche'
WORKSHEET_NAME_PERFORMANCE = 'Performance_Mensuelle'
WORKSHEET_NAME_UNIVERS = 'Univers_Personnages'
WORKSHEET_NAME_STYLES = 'Styles_Ecriture' # NOUVEAU

# Local Assets Folders
ASSETS_FOLDER = 'assets'
TEXTS_FOLDER = os.path.join(ASSETS_FOLDER, 'texts')
COVERS_FOLDER = os.path.join(ASSETS_FOLDER, 'covers')

# Assurez-vous que les dossiers existent (le code de app.py le fera aussi au démarrage)
os.makedirs(TEXTS_FOLDER, exist_ok=True)
os.makedirs(COVERS_FOLDER, exist_ok=True)