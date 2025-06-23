# utils.py

import os
import streamlit as st
import pandas as pd
from datetime import datetime
import random

def generate_unique_id(prefix="ID", length=8):
    """Génère un identifiant unique basé sur la date et un préfixe, avec un suffixe aléatoire."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f") # Ajout des microsecondes pour plus d'unicité
    suffix = ''.join(random.choices('0123456789ABCDEF', k=length))
    return f"{prefix}-{timestamp}-{suffix}"

def save_uploaded_file(uploaded_file, target_dir):
    """
    Sauvegarde un fichier uploadé par Streamlit dans un répertoire local.
    Retourne le chemin relatif du fichier sauvegardé ou None en cas d'erreur.
    """
    if uploaded_file is None:
        return None

    # Assure que le répertoire cible existe
    os.makedirs(target_dir, exist_ok=True)
    
    # Nettoie le nom du fichier pour éviter les caractères spéciaux et garantir l'unicité
    filename = os.path.basename(uploaded_file.name)
    base, ext = os.path.splitext(filename)
    
    # Rendre le nom de fichier sûr pour le système de fichiers
    clean_base = "".join(c for c in base if c.isalnum() or c in (' ', '_', '-')).strip()
    clean_base = clean_base.replace(' ', '_') # Remplacer les espaces par des underscores

    unique_filename = f"{clean_base}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{ext.lower()}"
    file_path = os.path.join(target_dir, unique_filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Fichier sauvegardé: {unique_filename}")
        # Retourne le chemin relatif par rapport au dossier assets/ pour un stockage léger en BDD
        return os.path.join(os.path.basename(target_dir), unique_filename)
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde du fichier {unique_filename}: {e}")
        return None

def format_dataframe_for_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Formate un DataFrame pour un affichage plus lisible dans Streamlit,
    gérant les dates et les listes d'IDs.
    """
    df_display = df.copy()
    for col in df_display.columns:
        # Formatage des dates
        if 'Date' in col and not df_display[col].empty and pd.api.types.is_object_dtype(df_display[col]):
            try:
                # Convertit en datetime, gère les erreurs, puis formate
                df_display[col] = pd.to_datetime(df_display[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna('')
            except:
                pass # Laisse tel quel si la conversion échoue

        # Gérer les listes d'IDs (par exemple, ID_Morceaux_Affectes) stockées comme chaînes
        if 'ID_' in col and 's' in col: # Heuristic for plural IDs like 'ID_Morceaux_Lies' or 'Tags_Feedback'
            df_display[col] = df_display[col].apply(lambda x: x.replace(',', ', ') if isinstance(x, str) else x)
        
        # Pour les colonnes 'Favori' ou 'Statut_Actif', affichage plus lisible
        if col in ['Favori', 'Statut_Actif']:
            df_display[col] = df_display[col].apply(lambda x: '✅ VRAI' if str(x).upper() == 'VRAI' else '❌ FAUX')

    return df_display

def parse_boolean_string(value):
    """Convertit une chaîne de caractères en booléen."""
    if isinstance(value, str):
        return value.strip().upper() == 'VRAI'
    return bool(value)

def safe_cast_to_int(value):
    """Tente de convertir une valeur en int, retourne None si échec."""
    try:
        # Essayer de nettoyer la chaîne avant conversion
        if isinstance(value, str):
            value = value.strip()
            if not value: # Gérer les chaînes vides
                return None
            value = value.replace('.', '') # Supprimer les points pour les milliers (format européen)
            value = value.replace(',', '.') # Convertir virgule en point pour décimaux avant int
        return int(float(value)) # Convertir d'abord en float pour gérer les décimaux puis en int
    except (ValueError, TypeError):
        return None

def safe_cast_to_float(value):
    """Tente de convertir une valeur en float, retourne None si échec."""
    try:
        # Remplacer la virgule par un point pour la conversion en float si format français
        if isinstance(value, str):
            value = value.strip().replace(',', '.')
            if not value: # Gérer les chaînes vides
                return None
        return float(value)
    except (ValueError, TypeError):
        return None
