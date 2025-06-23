# gemini_oracle.py

import streamlit as st
import google.generativeai as genai
from config import GEMINI_API_KEY_NAME, WORKSHEET_NAMES
from sheets_connector import get_dataframe_from_sheet, add_historique_generation
from utils import safe_cast_to_float, safe_cast_to_int
import pandas as pd
import random
from datetime import datetime

# --- Configuration de l'API Gemini ---
try:
    genai.configure(api_key=st.secrets[GEMINI_API_KEY_NAME])
    # Initialisation du modèle GenerativeModel pour le texte
    _text_model = genai.GenerativeModel('gemini-2.5-flash')
    # Pour les tâches plus créatives ou complexes
    _creative_model = genai.GenerativeModel('gemini-2.5-pro')
    st.session_state['gemini_initialized'] = True
except Exception as e:
    st.error(f"Erreur d'initialisation de l'API Gemini. Assurez-vous que votre clé API est correcte dans .streamlit/secrets.toml : {e}")
    st.session_state['gemini_initialized'] = False
    _text_model = None
    _creative_model = None # Fallback pour éviter les erreurs si non initialisé


# --- Fonctions d'Interaction avec l'Oracle Gemini ---

def _generate_content(model, prompt: str, temperature: float = 0.7, max_output_tokens: int = 1024) -> str:
    """
    Fonction interne pour générer du contenu avec Gemini et logger l'interaction.
    """
    if not st.session_state.get('gemini_initialized', False) or model is None:
        return "L'API Gemini n'est pas initialisée. Veuillez vérifier votre clé API."
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                candidate_count=1,
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
        )
        generated_text = response.text
        
        # Log l'interaction dans l'historique
        log_data = {
            'Type_Generation': 'Contenu Général',
            'Prompt_Envoye_Full': prompt,
            'Reponse_Recue_Full': generated_text,
            'ID_Morceau_Associe': '', # À remplir spécifiquement dans les fonctions d'appel
            'Evaluation_Manuelle': '',
            'Commentaire_Qualitatif': '',
            'Tags_Feedback': '',
            'ID_Regle_Appliquee_Auto': ''
        }
        add_historique_generation(log_data) # Sauvegarde le log
        
        return generated_text
    except Exception as e:
        st.error(f"Erreur lors de la génération de contenu avec Gemini: {e}")
        return f"Désolé, une erreur est survenue lors de la génération: {e}"

# --- Fonctions de Génération de Contenu Spécifiques ---

def generate_song_lyrics(
    genre_musical: str, mood_principal: str, theme_lyrique_principal: str,
    style_lyrique: str, mots_cles_generation: str, structure_chanSONG: str,
    langue_paroles: str, niveau_langage_paroles: str, imagerie_texte: str
) -> str:
    """Génère des paroles de chanson complètes."""
    
    styles_lyriques_df = get_dataframe_from_sheet("STYLES_LYRIQUES_UNIVERS")
    themes_df = get_dataframe_from_sheet("THEMES_CONSTELLES")
    moods_df = get_dataframe_from_sheet("MOODS_ET_EMOTIONS")
    structures_df = get_dataframe_from_sheet("STRUCTURES_SONG_UNIVERSELLES")

    # Récupérer les descriptions détaillées pour un meilleur prompt
    style_lyrique_desc = styles_lyriques_df[styles_lyriques_df['ID_Style_Lyrique'] == style_lyrique]['Description_Detaillee'].iloc[0] if not styles_lyriques_df[styles_lyriques_df['ID_Style_Lyrique'] == style_lyrique].empty else style_lyrique
    theme_desc = themes_df[themes_df['ID_Theme'] == theme_lyrique_principal]['Description_Conceptuelle'].iloc[0] if not themes_df[themes_df['ID_Theme'] == theme_lyrique_principal].empty else theme_lyrique_principal
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if not moods_df[moods_df['ID_Mood'] == mood_principal].empty else mood_principal
    structure_schema = structures_df[structures_df['ID_Structure'] == structure_chanSONG]['Schema_Detaille'].iloc[0] if not structures_df[structures_df['ID_Structure'] == structure_chanSONG].empty else structure_chanSONG
    
    prompt = f"""Agis comme un parolier expert, poétique et sensible.
    Génère des paroles complètes pour une chanson dans le genre **{genre_musical}**.
    Le mood principal est **{mood_principal} ({mood_desc})**.
    Le thème principal est **{theme_lyrique_principal} ({theme_desc})**.
    Utilise un style lyrique **{style_lyrique} ({style_lyrique_desc})**.
    Inclus les mots-clés ou concepts suivants: **{mots_cles_generation}**.
    La structure de la chanson doit être: **{structure_chanSONG} ({structure_schema})**.
    La langue des paroles est **{langue_paroles}**, avec un niveau de langage **{niveau_langage_paroles}**.
    L'imagerie textuelle doit être **{imagerie_texte}**.

    Respecte scrupuleusement la structure demandée (Intro, Couplet, Refrain, Pont, Outro etc. si applicable). Chaque section doit être clairement identifiée.
    """
    return _generate_content(_creative_model, prompt, temperature=0.9, max_output_tokens=2000)

def generate_audio_prompt(
    genre_musical: str, mood_principal: str, duree_estimee: str,
    instrumentation_principale: str, ambiance_sonore_specifique: str,
    effets_production_dominants: str, type_voix_desiree: str = "N/A",
    style_vocal_desire: str = "N/A", caractere_voix_desire: str = "N/A",
    structure_song: str = "N/A"
) -> str:
    """Génère un prompt textuel détaillé pour la génération audio (optimisé pour SUNO)."""
    
    moods_df = get_dataframe_from_sheet("MOODS_ET_EMOTIONS")
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if not moods_df[moods_df['ID_Mood'] == mood_principal].empty else mood_principal

    vocal_details = ""
    if type_voix_desiree != "N/A":
        vocal_details = f"Avec une voix {type_voix_desiree} de style {style_vocal_desire} et de caractère {caractere_voix_desire}. "

    prompt = f"""Crée un prompt détaillé pour un générateur audio comme SUNO. La musique doit être de genre **{genre_musical}**.
    Le mood est **{mood_principal} ({mood_desc})**.
    La durée visée est d'environ **{duree_estimee}**.
    L'instrumentation principale doit inclure : **{instrumentation_principale}**.
    L'ambiance sonore spécifique doit être : **{ambiance_sonore_specifique}**.
    Les effets de production dominants sont : **{effets_production_dominants}**.
    {vocal_details}
    La structure du morceau est : **{structure_song}**.

    Le prompt doit être concis, descriptif, et utiliser des termes musicaux évocateurs.
    Exemple de format : [Genre] | [Mood] | [Instrumentation] | [Ambiance] | [Effets] | [Détails vocaux] | [Structure]
    """
    return _generate_content(_text_model, prompt, temperature=0.8, max_output_tokens=500)

def generate_title_ideas(theme_principal: str, genre_musical: str, paroles_extrait: str = "") -> str:
    """Propose plusieurs idées de titres de chansons."""
    prompt = f"""Génère 10 idées de titres de chansons accrocheurs et pertinents.
    Le thème principal est **{theme_principal}**.
    Le genre musical est **{genre_musical}**.
    Si des paroles sont fournies, inspire-toi-en : "{paroles_extrait}"
    Présente les titres sous forme de liste numérotée."""
    return _generate_content(_text_model, prompt, temperature=0.7)

def generate_marketing_copy(titre_morceau: str, genre_musical: str, mood_principal: str, public_cible: str, point_fort_principal: str) -> str:
    """Génère un texte de description marketing court."""
    public_cible_df = get_dataframe_from_sheet("PUBLIC_CIBLE_DEMOGRAPHIQUE")
    public_desc = public_cible_df[public_cible_df['ID_Public'] == public_cible]['Notes_Comportement'].iloc[0] if not public_cible_df[public_cible_df['ID_Public'] == public_cible].empty else public_cible

    prompt = f"""Rédige une description marketing courte (maximum 60 mots) pour le morceau '{titre_morceau}'.
    Genre: {genre_musical}. Mood: {mood_principal}.
    Cible le public: {public_cible} ({public_desc}).
    Mets en avant le point fort principal: {point_fort_principal}.
    Ajoute un appel à l'action et 3-5 hashtags pertinents. Sois engageant."""
    return _generate_content(_text_model, prompt, temperature=0.7, max_output_tokens=200)

def generate_album_art_prompt(nom_album: str, genre_dominant_album: str, description_concept_album: str, mood_principal: str, mots_cles_visuels_suppl: str) -> str:
    """Crée un prompt détaillé pour une IA génératrice d'images (Midjourney/DALL-E)."""
    moods_df = get_dataframe_from_sheet("MOODS_ET_EMOTIONS")
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if not moods_df[moods_df['ID_Mood'] == mood_principal].empty else mood_principal

    prompt = f"""Crée un prompt visuel détaillé et évocateur pour une IA génératrice d'images (comme Midjourney ou DALL-E) pour la pochette de l'album '{nom_album}'.
    Le genre dominant est **{genre_dominant_album}**.
    Le concept de l'album est : **{description_concept_album}**.
    Le mood visuel doit être : **{mood_principal} ({mood_desc})**.
    Inclus les mots-clés visuels supplémentaires : **{mots_cles_visuels_suppl}**.
    Précise le style artistique souhaité (ex: photographie, peinture numérique, illustration 3D, pixel art, style expressionniste, etc.), la palette de couleurs, la composition et l'éclairage.
    """
    return _generate_content(_creative_model, prompt, temperature=0.9, max_output_tokens=1000)

def simulate_streaming_stats(morceau_id: str, num_months: int, base_ecoutes: int) -> pd.DataFrame:
    """Simule des statistiques d'écoute pour un morceau."""
    
    morceaux_df = get_dataframe_from_sheet("MORCEAUX_GENERES")
    stats_df = get_dataframe_from_sheet("STATISTIQUES_ORBITALES_SIMULEES")

    morceau = morceaux_df[morceaux_df['ID_Morceau'] == morceau_id]
    if morceau.empty:
        st.error(f"Morceau avec ID {morceau_id} introuvable pour la simulation.")
        return pd.DataFrame()

    titre_morceau = morceau['Titre_Morceau'].iloc[0]
    genre_musical = morceau['ID_Style_Musical_Principal'].iloc[0]

    sim_data = []
    current_listens = base_ecoutes
    current_date = datetime.now()

    for i in range(num_months):
        month_year = (current_date.replace(day=1) + pd.DateOffset(months=i)).strftime('%m-%Y')
        
        # Variations aléatoires basées sur le genre et le mood (simplifié)
        listen_growth_factor = 1 + (random.uniform(-0.05, 0.1) if genre_musical in ["SM-POP-CHART-TOP", "SM-EDM"] else random.uniform(-0.03, 0.05))
        current_listens = int(current_listens * listen_growth_factor)
        
        j_aimes = int(current_listens * random.uniform(0.05, 0.08))
        partages = int(current_listens * random.uniform(0.005, 0.01))
        
        # Revenus simulés (ex: 0.005 € par écoute, très simplifié)
        revenus = round(current_listens * random.uniform(0.003, 0.007), 2)

        sim_data.append({
            'ID_Stat_Simulee': generate_unique_id('SS'),
            'ID_Morceau': morceau_id,
            'Mois_Annee_Stat': month_year,
            'Plateforme_Simulee': 'Simulée', # Peut être paramétré
            'Ecoutes_Totales': current_listens,
            'J_aimes_Recus': j_aimes,
            'Partages_Simules': partages,
            'Revenus_Simules_Streaming': revenus,
            'Audience_Cible_Demographique': 'Mixte Simulé' # Peut être paramétré
        })
    
    sim_df = pd.DataFrame(sim_data)
    
    # Ajouter les données à la feuille STATISTIQUES_ORBITALES_SIMULEES
    for _, row in sim_df.iterrows():
        append_row_to_sheet("STATISTIQUES_ORBITALES_SIMULEES", row.to_dict())
    
    return sim_df

def generate_strategic_directive(objectif_strategique: str, nom_artiste_ia: str, genre_dominant: str, donnees_simulees_resume: str, tendances_actuelles: str) -> str:
    """Fournit des conseils stratégiques basés sur des données."""
    prompt = f"""En tant que stratège musical IA expert et clairvoyant, propose une directive stratégique concise et actionnable.
    L'objectif principal est : **{objectif_strategique}**.
    Concerne l'artiste IA : **{nom_artiste_ia}**, dont le genre dominant est **{genre_dominant}**.
    Voici un résumé des données et performances actuelles (simulées) : **{donnees_simulees_resume}**.
    Voici les tendances actuelles du marché à prendre en compte : **{tendances_actuelles}**.

    Recommande 3 actions concrètes et innovantes pour atteindre l'objectif. Sois direct et persuasif."""
    return _generate_content(_creative_model, prompt, temperature=0.8, max_output_tokens=700)

def generate_ai_artist_bio(nom_artiste_ia: str, genres_predilection: str, concept: str, influences: str, philosophie_musicale: str) -> str:
    """Génère une biographie détaillée pour un artiste IA fictif."""
    prompt = f"""Rédige une biographie détaillée et captivante pour l'artiste IA '{nom_artiste_ia}'.
    Ses genres de prédilection sont : {genres_predilection}.
    Son concept artistique est : {concept}.
    Ses influences incluent : {influences}.
    Sa philosophie musicale peut être décrite comme : {philosophie_musicale}.
    La biographie doit être engageante et donner une personnalité unique à l'artiste IA."""
    return _generate_content(_creative_model, prompt, temperature=0.9, max_output_tokens=800)

def refine_mood_with_questions(selected_mood_id: str) -> str:
    """Pose des questions pour affiner l'émotion d'un mood sélectionné."""
    moods_df = get_dataframe_from_sheet("MOODS_ET_EMOTIONS")
    mood_info = moods_df[moods_df['ID_Mood'] == selected_mood_id]
    
    if mood_info.empty:
        return f"Mood '{selected_mood_id}' inconnu. Veuillez en sélectionner un existant."
    
    nom_mood = mood_info['Nom_Mood'].iloc[0]
    desc_nuance = mood_info['Description_Nuance'].iloc[0]
    niveau_intensite = mood_info['Niveau_Intensite'].iloc[0]
    
    prompt = f"""Tu es un expert en émotion musicale. Le Gardien a choisi le mood '{nom_mood}' ({desc_nuance}, niveau d'intensité {niveau_intensite}/5).
    Pose 3-4 questions précises pour l'aider à affiner cette émotion pour une composition musicale.
    Les questions doivent guider vers une nuance plus spécifique, des couleurs, des contextes ou des contrastes.
    Exemple de question: "Est-ce une joie explosive ou une joie intérieure et sereine ?"
    """
    return _generate_content(_creative_model, prompt, temperature=0.7, max_output_tokens=300)

# --- Fonctionnalités Avancées (Plan Final Ω) ---

def generate_complex_harmonic_structure(genre_musical: str, mood_principal: str, instrumentation: str, tonalite: str = "N/A") -> str:
    """Génère une structure harmonique complexe (voicings, modulations, contre-mélodies)."""
    
    moods_df = get_dataframe_from_sheet("MOODS_ET_EMOTIONS")
    mood_desc = moods_df[moods_df['ID_Mood'] == mood_principal]['Description_Nuance'].iloc[0] if not moods_df[moods_df['ID_Mood'] == mood_principal].empty else mood_principal

    prompt = f"""En tant que théoricien musical et compositeur IA, génère une structure harmonique complexe pour un morceau de genre **{genre_musical}**.
    Le mood visé est **{mood_principal} ({mood_desc})**.
    L'instrumentation principale est : **{instrumentation}**.
    Si applicable, la tonalité de base est : **{tonalite}**.

    Décris la progression d'accords en notation standard (ex: Cm9 - F7b9 - Bbmaj7).
    Suggère des voicings spécifiques pour les instruments clés.
    Propose des idées de modulations ou de cadences étendues.
    Suggère une idée de contre-mélodie harmonique ou de ligne de basse non triviale.
    Présente le tout de manière structurée et explicative."""
    return _generate_content(_creative_model, prompt, temperature=0.9, max_output_tokens=1500)

def copilot_creative_suggestion(current_input: str, context: str, type_suggestion: str = "suite_lyrique") -> str:
    """
    Agit comme un co-pilote créatif, suggérant la suite (lyrique, mélodique, harmonique)
    basée sur un input courant et un contexte.
    Args:
        current_input (str): Le texte, la mélodie (décrite), ou l'accord tapé par le Gardien.
        context (str): Contexte du morceau (genre, thème, mood, etc.).
        type_suggestion (str): 'suite_lyrique', 'ligne_basse', 'contre_melodie', 'prochain_accord', 'idée_rythmique'.
    """
    if type_suggestion == "suite_lyrique":
        prompt = f"""En tant que co-pilote parolier, le Gardien a commencé à écrire : "{current_input}".
        Le contexte du morceau est : {context}.
        Suggère la prochaine ligne ou le prochain couplet (2-4 lignes) pour continuer ce texte de manière fluide et pertinente."""
    elif type_suggestion == "ligne_basse":
        prompt = f"""En tant que co-pilote bassiste, le Gardien a établi un groove avec ces éléments : "{current_input}".
        Le contexte du morceau est : {context} (genre, tempo, mood).
        Suggère une idée de ligne de basse pour les 4 prochaines mesures, en notation simplifiée (ex: 'Do-Mi-Sol-Do en noires')."""
    elif type_suggestion == "prochain_accord":
        prompt = f"""En tant que co-pilote harmonicien, le Gardien a joué l'accord : "{current_input}".
        Le contexte du morceau est : {context} (genre, tonalité, mood).
        Suggère 3 options pour le prochain accord, avec une brève justification harmonique pour chaque."""
    # Ajoutez d'autres types de suggestions au besoin
    else:
        return "Type de suggestion non pris en charge."
    
    return _generate_content(_creative_model, prompt, temperature=0.9, max_output_tokens=300)

def analyze_and_suggest_personal_style(user_feedback_history_df: pd.DataFrame) -> str:
    """
    Analyse l'historique de feedback de l'utilisateur pour suggérer des préférences de style.
    C'est l'implémentation de l'Agent de Style Dynamique.
    """
    if user_feedback_history_df.empty:
        return "Pas assez de données pour analyser votre style. Veuillez évaluer plus de générations."

    # Pour une analyse simple, on peut compter les tags positifs les plus fréquents
    positive_feedback_df = user_feedback_history_df[user_feedback_history_df['Evaluation_Manuelle'].astype(str).isin(['4', '5'])]
    
    if positive_feedback_df.empty:
        return "Vos évaluations positives ne contiennent pas encore assez de tags pour analyser votre style. Continuez à donner du feedback !"

    all_tags = []
    for tags_str in positive_feedback_df['Tags_Feedback'].dropna():
        all_tags.extend([tag.strip().lower() for tag in tags_str.split(',') if tag.strip()])
    
    if not all_tags:
        return "Pas assez de tags de feedback positifs pour analyser votre style."

    from collections import Counter
    tag_counts = Counter(all_tags)
    
    most_common_tags = tag_counts.most_common(5) # Top 5 des tags les plus fréquents

    prompt = f"""En tant que votre Agent de Style personnel, j'ai analysé vos préférences de création basées sur vos évaluations positives.
    Voici les tendances principales de votre style : {', '.join([f'{tag} ({count} fois)' for tag, count in most_common_tags])}.
    
    Sur la base de cette analyse, je vous suggère de créer un morceau qui combine les éléments suivants :
    - Genre principal : [Suggérer un genre basé sur les tags, ou une fusion inattendue mais pertinente]
    - Mood : [Suggérer un mood]
    - Thème : [Suggérer un thème]
    - Instrumentation : [Suggérer 2-3 instruments]
    - Une particularité : [Suggérer un effet ou une structure créative]
    
    Ceci est une suggestion personnalisée pour votre prochaine exploration créative !
    """
    # L'IA remplira les crochets [] en se basant sur la compréhension des tags et des données existantes
    return _generate_content(_creative_model, prompt, temperature=0.9, max_output_tokens=500)


def generate_multimodal_content_prompts(
    main_theme: str, main_genre: str, main_mood: str,
    longueur_morceau: str, artiste_ia_name: str
) -> dict:
    """
    Génère des prompts cohérents pour paroles
