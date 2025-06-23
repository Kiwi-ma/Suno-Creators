# utils.py
import re

def clean_filename_slug(text, max_length=50):
    """
    Nettoyage robuste pour un nom de fichier sûr et limité.
    """
    if not isinstance(text, str):
        text = str(text)

    # Remplace les caractères non alphanumériques (sauf -, _, .) par des underscores
    cleaned_text = re.sub(r'[\\/\s]+', '_', text)
    cleaned_text = re.sub(r'[^a-zA-Z0-9_.-]', '', cleaned_text)

    # Retire les underscores multiples ou au début/fin
    cleaned_text = re.sub(r'__+', '_', cleaned_text)
    cleaned_text = cleaned_text.strip('_')

    return cleaned_text[:max_length]