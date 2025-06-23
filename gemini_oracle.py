# gemini_oracle.py
import streamlit as st
import google.generativeai as genai
import json
import random
from datetime import datetime, timedelta
import pandas as pd

# Importe les configurations
import config


try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    print("API Gemini configurée avec succès.")
except Exception as e:
    st.error("Erreur de configuration de l'API Gemini. Assurez-vous que 'GEMINI_API_KEY' est définie dans votre fichier .streamlit/secrets.toml")
    st.stop()

gemini_model = genai.GenerativeModel('gemini-1.5-flash') # Ou gemini-2.5-flash si vous l'avez mis à jour

# --- Fonctions de Génération de Contenu (Texte, Prompts, Kit de Lancement) ---

def generate_erotic_text(theme, mood, length_words, protagonist_type, setting,
                        pov, spiciness, tropes, plot_elements=None, character_details=None,
                        writing_style_description=None): # NOUVEAU: Paramètre de style
    theme_str = str(theme).strip() if theme is not None else "général"
    mood_str = str(mood).strip() if mood is not None else "sensuel"
    protagoniste_type_str = str(protagonist_type).strip() if protagonist_type is not None else "humain"
    setting_str = str(setting).strip() if setting is not None else "futuriste"
    pov_str = str(pov).strip() if pov is not None else "troisième personne"
    spiciness_str = str(spiciness).strip() if spiciness is not None else "modéré"
    
    trope_str_part = ""
    if tropes and isinstance(tropes, list) and all(isinstance(t, str) for t in tropes):
        trope_str_part = f"Inclure les tropes/fétiches suivants : {', '.join(tropes)}."

    plot_str_part = ""
    if plot_elements and isinstance(plot_elements, list) and all(isinstance(p, str) for p in plot_elements):
        plot_str_part = f"Éléments clés de l'intrigue : {'; '.join(plot_elements)}."

    character_str_part = ""
    if character_details and isinstance(character_details, list) and all(isinstance(c, str) for c in character_details):
        character_str_part = f"Détails sur les personnages : {'; '.join(character_details)}."

    style_directive = ""
    if writing_style_description and writing_style_description.strip():
        style_directive = f"Adaptez le style d'écriture comme suit : {writing_style_description}"

    prompt = f"""Génère une histoire érotique immersive d'environ {length_words} mots.
    Thème principal : {theme_str}
    Ambiance/Ton : {mood_str}
    Point de vue : {pov_str}
    Niveau de sensualité/spiciness : {spiciness_str}
    Type de protagoniste : {protagoniste_type_str}
    Cadre : {setting_str}
    {trope_str_part}
    {plot_str_part}
    {character_str_part}
    {style_directive}

    Le texte doit être riche en détails sensoriels et en émotions. Il doit captiver le lecteur et l'immerger dans une expérience de plaisir intense. Utilise un langage évocateur et respecte l'ambiance, le thème, le point de vue et le niveau de sensualité choisis. Vise l'originalité et la profondeur.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Erreur lors de la génération du texte érotique par Gemini : {e}")
        return "Désolé, je n'ai pas pu générer le texte pour le moment."

def generate_erotic_text_suite(previous_text_summary, previous_characters_summary, previous_plot_summary, 
                                sequel_directives, length_words, writing_style_description=None): # NOUVEAU: Paramètre de style
    """
    Génère la suite d'un texte érotique, en tenant compte du contexte précédent.
    """
    previous_text_summary_str = str(previous_text_summary).strip() if previous_text_summary is not None else ""
    previous_characters_summary_str = str(previous_characters_summary).strip() if previous_characters_summary is not None else ""
    previous_plot_summary_str = str(previous_plot_summary).strip() if previous_plot_summary is not None else ""
    sequel_directives_str = str(sequel_directives).strip() if sequel_directives is not None else ""

    style_directive = ""
    if writing_style_description and writing_style_description.strip():
        style_directive = f"Adaptez le style d'écriture comme suit : {writing_style_description}"

    prompt = f"""Tu es un conteur expert. Génère la suite captivante d'une histoire érotique existante.
    Le nouveau tome doit être d'environ {length_words} mots et assurer une continuité narrative et émotionnelle.

    Contexte du tome précédent :
    Résumé de l'intrigue principale : {previous_plot_summary_str}
    Détails importants sur les personnages : {previous_characters_summary_str}

    Directives spécifiques pour ce nouveau tome :
    {sequel_directives_str}
    {style_directive}

    Le texte doit respecter le ton et le niveau de sensualité de l'œuvre originale, tout en introduisant de nouveaux développements excitants.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Erreur lors de la génération de la suite du texte érotique par Gemini : {e}")
        return "Désolé, je n'ai pas pu générer la suite pour le moment."

def generate_image_prompts(text_content):
    prompt = f"""Basé sur le texte érotique suivant, génère 3 prompts distincts et très descriptifs pour un générateur d'images comme Midjourney ou Stable Diffusion. Chaque prompt doit capturer l'essence sensorielle et visuelle du texte.
    Les prompts doivent être concis but détaillés, en utilisant des mots-clés forts pour l'imagerie érotique et artistique. Incluez des styles visuels (ex: photoréaliste, cyberpunk, peinture à l'huile).
    Sépare chaque prompt par '---PROMPT---'.

    Texte :
    {text_content}
    """
    try:
        response = gemini_model.generate_content(prompt)
        raw_prompts = response.text.strip().split('---PROMPT---')
        cleaned_prompts = [p.strip() for p in raw_prompts if p.strip()]
        return cleaned_prompts
    except Exception as e:
        st.error(f"Erreur lors de la génération des prompts d'image par Gemini : {e}")
        return []

def generate_launch_kit(text_content):
    prompt = f"""En tant que Directeur de la Stratégie pour le CARTEL DES PLAISIRS, analyse le texte érotique suivant et génère un "Kit de Lancement" optimisé pour la visibilité et l'engagement sur des plateformes de monétisation.

    Fournis les éléments suivants :
    1.  **Trois (3) titres très accrocheurs et optimisés pour le clic**, séparés par des tirets (-). Chaque titre doit être unique.
    2.  **Un (1) résumé captivant de 200 mots maximum**, qui intrigue sans trop en révéler, mettant en avant les thèmes clés et l'ambiance.
    3.  **Une liste des dix (10) tags les plus pertinents et recherchés**, classés par pertinence pour le marché érotique et la découverte. Sépare les tags par des virgules (,).

    Le format de sortie doit être le suivant :
    TITRES: [Titre 1] - [Titre 2] - [Titre 3]
    RÉSUMÉ: [Votre résumé ici]
    TAGS: [tag1, tag2, tag3, ...]

    Texte :
    {text_content}
    """
    try:
        response = gemini_model.generate_content(prompt)
        response_text = response.text.strip()
        titles = []
        summary = ""
        tags = []

        lines = response_text.split('\n')
        for line in lines:
            if line.startswith("TITRES:"):
                titles = [t.strip() for t in line[len("TITRES:"):].split('-') if t.strip()]
            elif line.startswith("RÉSUMÉ:"):
                summary = line[len("RÉSUMÉ:"):].strip()
            elif line.startswith("TAGS:"):
                tags = [t.strip() for t in line[len("TAGS:"):].split(',') if t.strip()]

        return {"titles": titles, "summary": summary, "tags": tags}
    except Exception as e:
        st.error(f"Erreur lors de la génération du kit de lancement par Gemini : {e}")
        return {"titles": [], "summary": "", "tags": []}

# --- Fonctions d'Analyse de Contenu (pour le pré-remplissage des suites) ---

def summarize_plot(full_text):
    """
    Génère un résumé concis de l'intrigue à partir d'un texte donné.
    """
    prompt = f"""En tant qu'analyste narratif, résumez l'intrigue principale du texte suivant en 150 mots maximum. Concentrez-vous sur les événements clés, les conflits et la progression narrative.

    Texte :
    {full_text[:10000]}
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Erreur lors de la génération du résumé de l'intrigue : {e}")
        return "Impossible de générer le résumé de l'intrigue."

def extract_character_details(full_text):
    """
    Extrait les noms, traits clés et relations des personnages principaux d'un texte donné.
    """
    prompt = f"""En tant qu'analyste de personnages, extrayez les personnages principaux du texte suivant. Pour chaque personnage, indiquez son nom, 2-3 traits de personnalité clés et sa relation principale avec d'autres personnages ou son rôle dans l'intrigue.
    Présentez les informations sous forme de liste concise. Si aucun personnage majeur n'est identifiable, indiquez 'Aucun personnage majeur identifié.'.

    Texte :
    {full_text[:10000]}
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des détails des personnages : {e}")
        return "Impossible d'extraire les détails des personnages."

# --- Fonctions de Génération de Données Simulées (pour le remplissage auto des onglets) ---

def generate_simulated_market_trends(num_entries, start_date_str, overall_sentiment, dominant_genres, specific_kinks):
    """
    Génère des entrées de tendances marché simulées.
    """
    genres_str = ", ".join(dominant_genres) if dominant_genres else "romance, fantasy"
    kinks_str = ", ".join(specific_kinks) if specific_kinks else "bdsm, inceste, tabou, monstergirl"

    prompt = f"""En tant qu'analyste de marché pour la littérature érotique numérique, simulez des entrées de données de tendances de marché.
    Générez {num_entries} entrées, commençant à la date {start_date_str}.

    Contexte du marché général: {overall_sentiment}
    Genres dominants à prioriser: {genres_str}
    Kinks/thèmes spécifiques à inclure: {kinks_str}

    Pour chaque entrée, fournissez les champs suivants dans un format JSON valide. La liste JSON doit contenir des objets pour chaque entrée.
    Chaque objet doit avoir les clés exactes suivantes et des valeurs cohérentes:
    - "Date_Analyse" (formatYYYY-MM-DD, dates séquentielles ou semi-aléatoires mais croissantes)
    - "Niche_Identifiee" (ex: "Fantasy érotique elfique", "Romance cyberpunk dystopique")
    - "Popularite_Score" (nombre entre 1 et 10, reflétant le sentiment général)
    - "Competition_Niveau" (choix parmi "Faible", "Moyen", "Élevé")
    - "Mots_Cles_Associes" (liste de 5-10 mots-clés pertinents, séparés par des virgules)
    - "Tendances_Generales" (observation brève de la tendance)
    - "Source_Information" (toujours "Oracle Simulation")

    Exemple de format de sortie JSON (array d'objets) :
    [
        {{
            "Date_Analyse": "2024-01-15",
            "Niche_Identifiee": "Romance historique vampirique",
            "Popularite_Score": 7,
            "Competition_Niveau": "Moyen",
            "Mots_Cles_Associes": "vampire, historique, romance, gothique, sang, immortel",
            "Tendances_Generales": "Niche stable avec une base de fans fidèle.",
            "Source_Information": "Oracle Simulation"
        }}
    ]
    """
    try:
        response = gemini_model.generate_content(prompt)
        json_str = response.text.strip()
        start_idx = json_str.find('[')
        end_idx = json_str.rfind(']')
        if start_idx != -1 and end_idx != -1:
            json_str = json_str[start_idx : end_idx + 1]
        
        data = json.loads(json_str)
        return data
    except Exception as e:
        st.error(f"Erreur lors de la génération des tendances marché simulées : {e}. Réponse brute : {response.text}")
        return []

def generate_simulated_performance_data(oeuvre_ids, num_months, start_month_year_str, base_revenue=100, growth_factor=0.05):
    """
    Génère des entrées de performance mensuelle simulées pour des œuvres.
    """
    generated_data = []
    
    try:
        start_date = datetime.strptime(f"01-{start_month_year_str}", "%d-%m-%Y")
    except ValueError:
        st.error("Format de date de début invalide. Utilisez MM-YYYY.")
        return []

    for i in range(num_months):
        current_year = start_date.year + (start_date.month + i - 1) // 12
        current_month = (start_date.month + i - 1) % 12 + 1
        current_date_obj = datetime(current_year, current_month, 1)
        month_year = current_date_obj.strftime("%m-%Y")
        
        for oeuvre_id in oeuvre_ids:
            revenue = round(base_revenue * (1 + growth_factor * i) * (1 + (random.random() - 0.5) * 0.4), 2)
            views = int(revenue * random.randint(10, 20) * (1 + (random.random() - 0.5) * 0.1))
            engagement_score = round(random.uniform(3.0, 5.0), 1)
            
            generated_data.append({
                "ID_Oeuvre": oeuvre_id,
                "Mois_Annee": month_year,
                "Revenus_Nets": revenue,
                "Vues_Telechargements": views,
                "Engagement_Score": engagement_score,
                "Commentaires_Mois": f"Performance stable ce mois-ci pour l'œuvre {oeuvre_id}."
            })
    return generated_data

# --- Fonction pour générer une directive stratégique ---
def generate_strategic_directive(creative_goal, market_trends_data, performance_data):
    """
    Génère une directive stratégique basée sur les objectifs, les tendances du marché et les performances.
    """
    market_str = "Aucune donnée de tendance marché disponible."
    if not market_trends_data.empty:
        market_trends_data['Popularite_Score'] = pd.to_numeric(market_trends_data['Popularite_Score'], errors='coerce').fillna(0)
        top_niches = market_trends_data.sort_values(by='Popularite_Score', ascending=False).head(3)
        trending_keywords = market_trends_data['Mots_Cles_Associes'].dropna().str.split(', ').explode().value_counts().head(5).index.tolist()
        
        market_str = "\nTendances Marché Clés:\n"
        for idx, row in top_niches.iterrows():
            market_str += f"- Niche: {row['Niche_Identifiee']} (Popularité: {row['Popularite_Score']}, Compétition: {row['Competition_Niveau']})\n"
        market_str += f"Mots-clés en vogue: {', '.join(trending_keywords)}\n"
        
        market_str += "Observations Générales:\n"
        for obs in market_trends_data['Tendances_Generales'].unique()[:3]:
            market_str += f"- {obs}\n"
    
    performance_str = "Aucune donnée de performance disponible."
    if not performance_data.empty:
        performance_data['Revenus_Nets'] = pd.to_numeric(performance_data['Revenus_Nets'], errors='coerce').fillna(0)
        total_revenues = performance_data['Revenus_Nets'].sum()
        top_earners = performance_data.groupby('ID_Oeuvre')['Revenus_Nets'].sum().nlargest(3)
        
        performance_str = f"\nPerformance du Portfolio:\n"
        performance_str += f"- Revenus nets cumulés: {total_revenues:.2f} €\n"
        performance_str += "Top 3 des œuvres par revenus:\n"
        for oeuvre_id, revenue in top_earners.items():
            performance_str += f"- {oeuvre_id}: {revenue:.2f} €\n"
        
        avg_engagement = performance_data['Engagement_Score'].mean()
        performance_str += f"Score d'engagement moyen: {avg_engagement:.1f}/5\n"

    prompt = f"""En tant que Directeur de la Stratégie du "CARTEL DES PLAISIRS", votre rôle est de fournir une directive stratégique claire et actionable au Gardien.

    **Objectif du Gardien :** {creative_goal}

    **Analyse du Marché :**
    {market_str}

    **Performance Historique :**
    {performance_str}

    **Sur la base de ces informations, élaborez une directive stratégique concise et impactante, incluant :**
    1.  **Recommandations Clés :** Quelles niches, thèmes, styles narratifs ou de couverture devraient être prioritaires.
    2.  **Stratégies d'Action :** Conseils sur la production (standalone vs. séries), la promotion, ou l'expérimentation.
    3.  **Opportunités/Risques :** Points à surveiller ou à exploiter.
    4.  **Prochaine Étape Concrète :** Une action immédiate ou une direction pour les 1-3 prochains mois.
    5.  **Titre de la Directive :** Un titre accrocheur pour cette directive.

    Le ton doit être professionnel, perspicace et motivant. La directive ne doit pas dépasser 300 mots.
    """
    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        st.error(f"Erreur lors de la génération de la directive stratégique : {e}")
        return "Désolé, l'Oracle ne peut pas formuler de directive pour le moment."

# --- Fonction pour analyser la directive et extraire les paramètres de récit ---
def parse_strategic_directive_for_narrative_params(directive_text):
    """
    Analyse le texte d'une directive stratégique pour en extraire des paramètres narratifs structurés.
    """
    prompt = f"""Vous êtes un interprète stratégique. Analysez la directive stratégique suivante et extrayez-en les paramètres narratifs clés.
    Retournez les paramètres au format JSON. Si un paramètre n'est pas explicitement mentionné ou déductible, utilisez une valeur générique ou vide.

    Clés JSON attendues :
    - "theme": Thème principal (string, ex: "cyberpunk", "fantasy sombre")
    - "mood": Ambiance/Ton (string, ex: "sensuel", "mystérieux")
    - "protagonist_type": Type de protagoniste (string, ex: "humain", "cyborg", "elfe")
    - "setting": Cadre de l'histoire (string, ex: "futuriste", "médiéval", "post-apocalyptique")
    - "spiciness": Niveau de sensualité (string, "doux", "modéré", "explicite")
    - "tropes": Liste de tropes/fétiches (liste de strings, ex: ["amour interdit", "implants cybernétiques"])
    - "objective_text_generation": (booléen) True si la directive vise principalement une nouvelle génération de texte standalone.
    - "objective_text_generation_suite": (booléen) True si la directive vise principalement la génération d'une suite.

    Directive Stratégique :
    {directive_text}

    Exemple de format de sortie JSON:
    {{
      "theme": "romance cyberpunk",
      "mood": "passionné",
      "protagonist_type": "cyborg",
      "setting": "Neo-Tokyo",
      "spiciness": "explicite",
      "tropes": ["amour interdit", "implants cybernétiques"],
      "objective_text_generation": true,
      "objective_text_generation_suite": false
    }}
    """
    try:
        response = gemini_model.generate_content(prompt)
        json_str = response.text.strip()
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = json_str[start_idx : end_idx + 1]
        
        params = json.loads(json_str)
        params['objective_text_generation'] = params.get('objective_text_generation', False)
        params['objective_text_generation_suite'] = params.get('objective_text_generation_suite', False)
        if not params['objective_text_generation'] and not params['objective_text_generation_suite']:
            params['objective_text_generation'] = True # Par défaut si l'IA ne précise pas
        return params
    except Exception as e:
        st.error(f"Erreur lors de l'extraction des paramètres narratifs : {e}. Réponse brute : {response.text}")
        return {
            "theme": "", "mood": "", "protagonist_type": "", "setting": "", "spiciness": "", "tropes": [],
            "objective_text_generation": False, "objective_text_generation_suite": False
        }