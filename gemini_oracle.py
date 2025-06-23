# gemini_oracle.py

import streamlit as st
import google.generativeai as genai
import pandas as pd
import random
from datetime import datetime
import json

from config import GEMINI_API_KEY_NAME, WORKSHEET_NAMES
from sheets_connector import add_historique_generation, get_dataframe_from_sheet

# --- Initialisation de la Connexion à l'API Gemini ---
try:
    gemini_api_key = st.secrets[GEMINI_API_KEY_NAME]
    genai.configure(api_key=gemini_api_key)
    # **Ω MISE A NIVEAU**: Utilisation exclusive de gemini-2.5-pro pour toutes les générations.
    _model = genai.GenerativeModel('gemini-2.5-pro')
    st.session_state['gemini_initialized'] = True
    st.session_state['gemini_error'] = None
except (KeyError, Exception) as e:
    st.session_state['gemini_initialized'] = False
    st.session_state['gemini_error'] = f"Clé API Gemini '{GEMINI_API_KEY_NAME}' manquante ou invalide dans les secrets. Erreur: {e}"
    _model = None

# --- Fonctions Utilitaires Internes ---
def _log_gemini_interaction(type_generation: str, prompt_sent: str, response_received: str, associated_id: str = ""):
    """Logue l'interaction avec Gemini dans l'historique."""
    try:
        log_data = {
            'Type_Generation': type_generation,
            'Prompt_Envoye_Full': prompt_sent,
            'Reponse_Recue_Full': response_received,
            'ID_Morceau_Associe': associated_id,
        }
        add_historique_generation(log_data)
    except Exception as e:
        st.warning(f"Erreur lors du logging de l'interaction Gemini: {e}")

def _generate_content(prompt: str, type_generation: str, associated_id: str = "", temperature: float = 0.7, max_output_tokens: int = 2048) -> str:
    """Fonction centrale et robuste pour générer du contenu avec Gemini."""
    if not st.session_state.get('gemini_initialized', False) or _model is None:
        return st.session_state.get('gemini_error', "L'Oracle est indisponible.")
    
    # **Ω NOTE**: Les instructions de sécurité sont cruciales.
    safety_instructions = "Votre réponse doit être sûre, appropriée, et ne jamais inclure de contenu sensible ou interdit. Si la requête est ambiguë, répondez de manière neutre et sûre, ou indiquez que le contenu ne peut être généré pour des raisons de conformité."
    final_prompt = f"{safety_instructions}\n\n--- REQUETE ---\n\n{prompt}"
    
    try:
        response = _model.generate_content(
            final_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens
            )
        )
        
        if not response.candidates:
            reason = "Raison inconnue"
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason.name
            error_message = f"Génération bloquée par les filtres de sécurité de l'Oracle. Raison: {reason}. Ajustez votre prompt."
            _log_gemini_interaction(type_generation, final_prompt, f"BLOCKED: {reason}", associated_id)
            return error_message
            
        generated_text = response.text
        _log_gemini_interaction(type_generation, final_prompt, generated_text, associated_id)
        return generated_text
        
    except Exception as e:
        error_message = f"Erreur de l'API Gemini: {e}"
        _log_gemini_interaction(type_generation, final_prompt, f"ERREUR API: {e}", associated_id)
        return error_message

# --- Fonctions de Génération Spécifiques ---

def generate_song_lyrics(
    genre_musical: str, mood_principal: str, theme_lyrique_principal: str,
    style_lyrique: str, mots_cles_generation: str, structure_chanson: str,
    langue_paroles: str, niveau_langage_paroles: str, imagerie_texte: str
) -> str:
    """Génère des paroles de chanson complètes."""
    prompt = f"""En tant que parolier expert, crée des paroles complètes et originales.
    - Genre: {genre_musical}
    - Mood: {mood_principal}
    - Thème: {theme_lyrique_principal}
    - Style Lyrique: {style_lyrique}
    - Mots-clés: {mots_cles_generation}
    - Structure: {structure_chanson} (Chaque section doit être clairement identifiée, ex: [COUPLET 1], [REFRAIN]).
    - Langue: {langue_paroles} ({niveau_langage_paroles})
    - Imagerie: {imagerie_texte}
    Ne produis que les paroles, sans notes ou explications additionnelles.
    """
    # **Ω CALIBRATION**: Température élevée pour une créativité accrue.
    return _generate_content(prompt, "Paroles de Chanson", temperature=0.9)

def generate_audio_prompt(
    genre_musical: str, mood_principal: str, duree_estimee: str,
    instrumentation_principale: str, ambiance_sonore_specifique: str,
    effets_production_dominants: str, type_voix_desiree: str = "N/A",
    style_vocal_desire: str = "N/A", caractere_voix_desire: str = "N/A",
    structure_song: str = "N/A"
) -> str:
    """Génère un prompt textuel détaillé pour la génération audio (optimisé pour SUNO)."""
    vocal_details = f"Voix {type_voix_desiree}, style {style_vocal_desire}, caractère {caractere_voix_desire}" if type_voix_desiree != "N/A" else "Instrumental"
    prompt = f"""Crée un prompt détaillé et concis pour SUNO.
    - Format: [Genre], [Instrumentation], [Mood], [Ambiance], [Effets], [{vocal_details}], [Structure], [Durée]
    - Détails:
        - Genre: {genre_musical}
        - Instrumentation: {instrumentation_principale or 'standard pour le genre'}
        - Mood: {mood_principal}
        - Ambiance: {ambiance_sonore_specifique or 'cohérente avec le mood'}
        - Effets: {effets_production_dominants or 'standards pour le genre'}
        - Structure: {structure_song or 'typique du genre'}
        - Durée: {duree_estimee}
    Combine ces éléments en une seule ligne de prompt cohérente et évocatrice.
    """
    # **Ω CALIBRATION**: Température modérée pour un prompt technique mais inspiré.
    return _generate_content(prompt, "Prompt Audio", temperature=0.6, max_output_tokens=500)

def generate_title_ideas(theme_principal: str, genre_musical: str, paroles_extrait: str = "") -> str:
    """Propose plusieurs idées de titres de chansons."""
    prompt = f"Génère 10 idées de titres de chansons accrocheurs pour un morceau de genre '{genre_musical}' sur le thème '{theme_principal}'. Inspire-toi de cet extrait de paroles : \"{paroles_extrait}\". Présente les titres en liste numérotée, sans texte superflu."
    return _generate_content(prompt, "Idées de Titres", temperature=0.8)

def generate_marketing_copy(titre_morceau: str, genre_musical: str, mood_principal: str, public_cible: str, point_fort_principal: str) -> str:
    """Génère un texte de description marketing court."""
    prompt = f"Rédige une description marketing courte (60 mots max) et percutante pour le morceau '{titre_morceau}' ({genre_musical}, mood: {mood_principal}). Cible: '{public_cible}'. Point fort: '{point_fort_principal}'. Termine par un appel à l'action et 3-5 hashtags pertinents."
    return _generate_content(prompt, "Description Marketing", temperature=0.8, max_output_tokens=300)

def generate_album_art_prompt(nom_album: str, genre_dominant_album: str, description_concept_album: str, mood_principal: str, mots_cles_visuels_suppl: str) -> str:
    """Crée un prompt détaillé pour une IA génératrice d'images (Midjourney/DALL-E)."""
    prompt = f"""Crée un prompt visuel détaillé pour une IA génératrice d'images (Midjourney/DALL-E) pour la pochette de l'album '{nom_album}'.
    - Concept: {description_concept_album}
    - Genre musical: {genre_dominant_album}
    - Mood visuel: {mood_principal}
    - Mots-clés visuels: {mots_cles_visuels_suppl}
    Décris le style artistique (ex: photographie surréaliste, peinture numérique abstraite), la palette de couleurs, la composition, et l'éclairage. Ajoute le ratio d'image '--ar 1:1' pour une pochette carrée.
    """
    # **Ω CALIBRATION**: Température élevée pour un art évocateur.
    return _generate_content(prompt, "Prompt Pochette Album", temperature=0.9, max_output_tokens=1000)

def simulate_streaming_stats(morceau_ids: list, num_months: int) -> pd.DataFrame:
    """Simule des statistiques d'écoute pour un ou plusieurs morceaux."""
    # **Ω NOTE**: La logique de simulation reste la même, car elle est indépendante de l'IA.
    morceaux_df = get_dataframe_from_sheet(WORKSHEET_NAMES["MORCEAUX_GENERES"])
    sim_data = []
    current_date = datetime.now()
    for morceau_id in morceau_ids:
        morceau = morceaux_df[morceaux_df['ID_Morceau'] == morceau_id]
        if morceau.empty: continue
        
        base_ecoutes_initial = random.randint(1000, 10000)
        current_listens = base_ecoutes_initial
        
        for i in range(num_months):
            month_year = (current_date.replace(day=1) + pd.DateOffset(months=i)).strftime('%m-%Y')
            listen_growth_factor = 1 + random.uniform(-0.05, 0.1)
            current_listens = int(current_listens * listen_growth_factor)
            j_aimes = int(current_listens * random.uniform(0.04, 0.08))
            partages = int(current_listens * random.uniform(0.005, 0.012))
            revenus = round(current_listens * random.uniform(0.003, 0.005), 2)
            
            sim_data.append({
                'ID_Stat_Simulee': generate_unique_id('SS'), 'ID_Morceau': morceau_id,
                'Mois_Annee_Stat': month_year, 'Plateforme_Simulee': 'Simulée',
                'Ecoutes_Totales': current_listens, 'J_aimes_Recus': j_aimes,
                'Partages_Simules': partages, 'Revenus_Simules_Streaming': revenus,
                'Audience_Cible_Demographique': 'Mixte Simulé'
            })
            
    sim_df = pd.DataFrame(sim_data)
    for _, row in sim_df.iterrows():
        append_row_to_sheet(WORKSHEET_NAMES["STATISTIQUES_ORBITALES_SIMULEES"], row.to_dict())
    return sim_df

def generate_strategic_directive(objectif_strategique: str, nom_artiste_ia: str, genre_dominant: str, donnees_simulees_resume: str, tendances_actuelles: str) -> str:
    """Fournit des conseils stratégiques basés sur des données."""
    prompt = f"En tant que stratège musical IA, propose 3 actions concrètes et innovantes pour l'artiste IA '{nom_artiste_ia}' ({genre_dominant}). Objectif: '{objectif_strategique}'. Données actuelles: '{donnees_simulees_resume or 'non fournies'}'. Tendances marché: '{tendances_actuelles or 'non fournies'}'. Sois direct et persuasif."
    return _generate_content(prompt, "Directive Stratégique", temperature=0.8, max_output_tokens=1000)

def refine_mood_with_questions(selected_mood_name: str) -> str:
    """Pose des questions pour affiner l'émotion d'un mood sélectionné."""
    prompt = f"Tu es un expert en psychologie de la musique. Le Gardien a choisi le mood '{selected_mood_name}'. Pose 3-4 questions précises pour l'aider à affiner cette émotion en termes de textures sonores, de contextes narratifs ou de souvenirs personnels. Commence directement par la première question."
    return _generate_content(prompt, "Affinement Mood", temperature=0.7, max_output_tokens=500)

def copilot_creative_suggestion(current_input: str, context: str, type_suggestion: str) -> str:
    """Agit comme un co-pilote créatif."""
    prompts = {
        "suite_lyrique": "Suggère la prochaine ligne ou le prochain court couplet (2-4 lignes).",
        "ligne_basse": "Suggère une idée de ligne de basse pour 4 mesures (ex: 'Do-Mi-Sol-Do en noires').",
        "prochain_accord": "Suggère 3 options pour le prochain accord avec une brève justification.",
        "idee_rythmique": "Suggère un pattern rythmique pour 4 mesures (kick, snare, hi-hat)."
    }
    instruction = prompts.get(type_suggestion, "Donne une suggestion créative pertinente.")
    prompt = f"En tant que co-pilote créatif, le contexte est: {context}. L'input actuel est: '{current_input}'.\n\n{instruction} Sois concis et inspirant."
    return _generate_content(prompt, f"Copilote - {type_suggestion}", temperature=0.9, max_output_tokens=400)

def generate_multimodal_content_prompts(main_theme: str, main_genre: str, main_mood: str, longueur_morceau: str, artiste_ia_name: str) -> dict:
    """Génère des prompts cohérents pour paroles, audio, et visuels."""
    prompt = f"""En tant qu'Architecte Multimodal, génère trois prompts distincts mais parfaitement cohérents. Le cœur de la création est: Thème: {main_theme}, Genre: {main_genre}, Mood: {main_mood}, Artiste: {artiste_ia_name}, Longueur: {longueur_morceau}.

    ###PROMPT_PAROLES###
    [Crée ici un prompt détaillé pour un parolier, incluant style, imagerie, et structure.]

    ###PROMPT_AUDIO_SUNO###
    [Crée ici un prompt d'une ligne pour SUNO, format : Genre, Instrumentation, Mood, Ambiance, Effets, Voix, Structure.]

    ###PROMPT_IMAGE_MIDJOURNEY###
    [Crée ici un prompt pour Midjourney, incluant style artistique, couleurs, composition, éclairage, et le ratio --ar 1:1.]
    """
    response_text = _generate_content(prompt, "Création Multimodale", temperature=0.9, max_output_tokens=3000)
    
    prompts_dict = {}
    try:
        prompts_dict["paroles_prompt"] = response_text.split("###PROMPT_PAROLES###")[1].split("###PROMPT_AUDIO_SUNO###")[0].strip()
        prompts_dict["audio_suno_prompt"] = response_text.split("###PROMPT_AUDIO_SUNO###")[1].split("###PROMPT_IMAGE_MIDJOURNEY###")[0].strip()
        prompts_dict["image_prompt"] = response_text.split("###PROMPT_IMAGE_MIDJOURNEY###")[1].strip()
    except IndexError:
        st.error("L'IA n'a pas respecté le format de sortie multimodal. Réponse brute affichée.")
        return {"paroles_prompt": response_text, "audio_suno_prompt": "Erreur de parsing.", "image_prompt": "Erreur de parsing."}
        
    return prompts_dict

def analyze_viral_potential_and_niche_recommendations(morceau_data: dict, public_cible_name: str, current_trends: str) -> str:
    """Analyse le potentiel viral d'un morceau et recommande des niches."""
    prompt = f"""En tant qu'analyste de marché musical, évalue le potentiel viral du morceau '{morceau_data.get('Titre_Morceau')}' et recommande des niches.
    - Détails: Genre: {morceau_data.get('ID_Style_Musical_Principal')}, Mood: {morceau_data.get('Ambiance_Sonore_Specifique')}, Thème: {morceau_data.get('Theme_Principal_Lyrique')}.
    - Cible: {public_cible_name}
    - Tendances: {current_trends or "Tendances générales du marché (vidéos courtes, niches émergentes)."}

    Analyse structurée:
    1.  **Potentiel Viral (Faible, Modéré, Fort, Excellent):** Justification basée sur l'adéquation aux tendances.
    2.  **Niches de Marché (2-3):** Propose des niches précises et non saturées.
    3.  **Stratégies Actionnables (3-5):** Actions concrètes pour maximiser le potentiel.
    """
    return _generate_content(prompt, "Analyse Potentiel Viral", temperature=0.8, max_output_tokens=1500)
