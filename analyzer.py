"""
Module d'Analyse IA - Tanmia Scraper MVP v1.9
PATCH: Merge unifié page+fichiers + Focus Organisation/Emails

CHANGELOG v1.9:
- PATCH: merge_all_content() - fusionne page+fichiers AVANT appel IA
- PATCH: Prompt simplifié focus Organisation + Emails (copie exacte)
- PATCH: Déduplication + normalisation emails
- CONSERVÉ: Structure v1.8 qui fonctionne
"""
import re
import json
from typing import Dict, List, Optional


# ============================================================================
# PATCH v1.9: MERGE UNIFIÉ PAGE + FICHIERS
# ============================================================================

def merge_all_content(data: Dict) -> str:
    """
    Fusionne page + fichiers en un seul texte pour analyse.
    
    Args:
        data: Dict avec texte_complet et fichiers_attaches
    
    Returns:
        Texte unifié pour analyse IA
    """
    parts = []
    
    # 1. Contenu page
    texte_page = data.get('texte_complet', '')
    if texte_page:
        parts.append("=== CONTENU PAGE WEB ===")
        parts.append(texte_page)
    
    # 2. Contenu fichiers (si parsés)
    for f in data.get('fichiers_attaches', []):
        contenu = f.get('contenu_texte', '')
        if contenu:
            nom = f.get('nom', 'fichier_inconnu')
            parts.append(f"\n=== FICHIER: {nom} ===")
            # Limiter taille
            if len(contenu) > 4000:
                contenu = contenu[:4000] + "...[tronqué]"
            parts.append(contenu)
    
    return '\n\n'.join(parts)


def normalize_and_dedup_emails(emails_page: List[str], emails_fichiers: List[str]) -> List[str]:
    """
    Normalise et déduplique tous les emails.
    
    Returns:
        Liste unique, lowercase, triée
    """
    all_emails = set()
    
    for email in emails_page + emails_fichiers:
        if email and '@' in str(email):
            normalized = email.strip().lower()
            if re.match(r'^[\w\.\-\+]+@[\w\.\-]+\.\w{2,}$', normalized):
                all_emails.add(normalized)
    
    return sorted(all_emails)


# ============================================================================
# FORMATAGE FICHIERS POUR PROMPTS (v1.8 enrichi)
# ============================================================================

def format_fichiers_for_prompt(fichiers: List[Dict], include_content: bool = True) -> str:
    """
    Formate les fichiers attachés avec leur contenu pour le prompt IA.
    
    Args:
        fichiers: Liste de dicts {nom, url, type, contenu_texte, emails_fichier}
        include_content: Si True, inclut le contenu textuel des fichiers
    
    Returns:
        String formaté pour le prompt
    """
    if not fichiers or len(fichiers) == 0:
        return "Aucun fichier attaché."
    
    lines = []
    
    for idx, f in enumerate(fichiers, 1):
        nom = f.get('nom', 'Sans nom')
        type_f = f.get('type', 'inconnu').upper()
        contenu = f.get('contenu_texte', '')
        emails = f.get('emails_fichier', [])
        
        # En-tête fichier
        lines.append(f"\n--- FICHIER {idx}: {nom} ({type_f}) ---")
        
        # Emails trouvés dans le fichier
        if emails:
            lines.append(f"Emails trouvés dans ce fichier: {', '.join(emails)}")
        
        # Contenu textuel (si disponible et demandé)
        if include_content and contenu:
            # Tronquer si trop long
            if len(contenu) > 3000:
                contenu = contenu[:3000] + "...[contenu tronqué]"
            lines.append(f"Contenu extrait:\n{contenu}")
        elif not contenu:
            lines.append("(Contenu non disponible - fichier non parsé)")
    
    return '\n'.join(lines)


def get_all_emails_from_files(fichiers: List[Dict]) -> List[str]:
    """
    Récupère tous les emails trouvés dans les fichiers.
    
    Args:
        fichiers: Liste de fichiers avec emails_fichier
    
    Returns:
        Liste d'emails uniques
    """
    all_emails = []
    for f in fichiers:
        all_emails.extend(f.get('emails_fichier', []))
    return list(set(all_emails))


# ============================================================================
# PROMPTS PROFESSIONNELS - GEMINI 2.5 PRO (v1.8)
# ============================================================================

GEMINI_ANALYSIS_PROMPT = """Tu es un expert analyste spécialisé dans l'extraction d'informations structurées à partir d'annonces professionnelles et de leurs documents annexes (TDR, cahiers des charges) dans le secteur du développement international au Maroc.

CONTEXTE:
Tu analyses des opportunités publiées sur Tanmia.ma avec leurs fichiers attachés (PDF, DOC).
Ces documents contiennent souvent des informations cruciales: emails de contact, détails de mission, profils recherchés.

DONNÉES À ANALYSER:

URL: {url}
Métadonnées:
- Titre: {titre}
- Organisation: {organisation}
- Date: {date}

EMAILS DÉJÀ EXTRAITS DES FICHIERS (v1.8):
{emails_from_files}

FICHIERS ATTACHÉS ET LEUR CONTENU:
{fichiers_attaches}

TEXTE DE LA PAGE WEB:
{texte_complet}

TÂCHE:
Analyse LE TEXTE DE LA PAGE et LE CONTENU DES FICHIERS pour extraire:

0. ORGANISATION / EMPLOYEUR
   - Cherche dans le texte ET dans les fichiers attachés
   - Les TDR mentionnent souvent l'organisation commanditaire
   - Retourne le NOM PROPRE (1-4 mots)

1. EMAILS DE CONTACT (PRIORITÉ ABSOLUE)
   - FUSIONNE les emails de la page ET ceux des fichiers
   - Les emails déjà extraits des fichiers sont fournis ci-dessus
   - Cherche aussi dans le texte de la page
   - Formats: standard, avec espaces, obfusqués
   - NE MANQUE AUCUN EMAIL - c'est l'info la plus critique

2. SECTEUR D'ACTIVITÉ (LISTE FERMÉE)
   Choisis UN parmi: "Santé", "Éducation", "Environnement", "Humanitaire", "Développement", "Gouvernance", "Droits humains", "Autre"

3. TYPE D'OPPORTUNITÉ
   Parmi: "CDI", "CDD", "Freelance", "Mission courte", "Appel d'offres"

4. LOCALISATION
   Ville(s), "National", ou "Non spécifié"

5. RÉSUMÉ PROFESSIONNEL (ENRICHI v1.8)
   - 2-3 phrases max (80 mots)
   - UTILISE les infos des fichiers attachés (TDR, cahiers des charges)
   - Mentionne: objectif, profil recherché, budget si mentionné, durée mission
   - Exemple: "Mission d'évaluation finale sur 3 mois. Budget indicatif: 50 000 MAD. Profil expert M&E requis."

6. MOTS-CLÉS TECHNIQUES
   - 5-8 mots-clés du texte ET des fichiers
   - Inclus compétences spécifiques mentionnées dans les TDR
   - Ajoute "TDR détaillé", "Cahier des charges" si fichiers importants présents

CONTRAINTES:
- Analyse TOUS les contenus (page + fichiers)
- Priorise les emails (fusionne toutes sources)
- JSON strict sans markdown

FORMAT RÉPONSE:
{{
    "organisation": "Nom organisation",
    "emails": ["email1@org.ma", "email2@org.ma"],
    "secteur": "UN des 8 choix",
    "type_opportunite": "Type exact",
    "localisation": "Ville(s)",
    "resume": "Synthèse incluant infos des fichiers attachés.",
    "mots_cles": ["mot1", "mot2", "mot3", "mot4", "mot5"]
}}

ANALYSE MAINTENANT.
"""


# ============================================================================
# PROMPTS PROFESSIONNELS - CLAUDE (v1.8)
# ============================================================================

CLAUDE_ANALYSIS_PROMPT = """Tu es un expert analyste spécialisé dans l'extraction d'informations à partir d'annonces professionnelles ET de leurs documents annexes (TDR, cahiers des charges) dans le secteur humanitaire au Maroc.

<contexte>
Tu analyses des opportunités Tanmia.ma avec leurs fichiers attachés parsés.
Les TDR et cahiers des charges contiennent souvent les informations les plus précises: emails directs, détails budgétaires, profils exacts recherchés.
</contexte>

<donnees>
URL: {url}

Métadonnées:
- Titre: {titre}
- Organisation: {organisation}
- Date: {date}

EMAILS EXTRAITS DES FICHIERS (pré-extraction v1.8):
{emails_from_files}

FICHIERS ATTACHÉS AVEC CONTENU:
{fichiers_attaches}

TEXTE PAGE WEB:
{texte_complet}
</donnees>

<instructions>
Analyse le texte de la page ET le contenu des fichiers attachés.

0. ORGANISATION
   - Cherche dans page ET fichiers (les TDR mentionnent le commanditaire)
   - NOM PROPRE court (1-4 mots)

1. EMAILS (PRIORITÉ ABSOLUE)
   - FUSIONNE: emails page + emails fichiers (fournis ci-dessus)
   - Les TDR contiennent souvent l'email direct du contact
   - Détecte tous formats (standard, obfusqués)
   - Retourne TOUS les emails trouvés

2. SECTEUR
   STRICTEMENT parmi: "Santé", "Éducation", "Environnement", "Humanitaire", "Développement", "Gouvernance", "Droits humains", "Autre"

3. TYPE D'OPPORTUNITÉ
   Parmi: "CDI", "CDD", "Freelance", "Mission courte", "Appel d'offres"

4. LOCALISATION
   Ville(s), "National", ou "Non spécifié"

5. RÉSUMÉ (ENRICHI v1.8)
   - 2-3 phrases maximum
   - EXPLOITE les infos des fichiers:
     * Budget si mentionné
     * Durée mission
     * Livrables attendus
     * Qualifications spécifiques
   - Exemple: "Évaluation programme VIH/SIDA sur 45 jours. Budget: 80 000 MAD. Expert santé publique avec 10 ans d'expérience requis. TDR complet disponible."

6. MOTS-CLÉS
   - 5-8 mots-clés de la page ET des fichiers
   - Compétences techniques des TDR
   - Ajoute "TDR détaillé" ou "Cahier des charges" si pertinent
</instructions>

<format_reponse>
JSON strict sans backticks:
{{
    "organisation": "Nom",
    "emails": ["email1@domain.com", "email2@domain.com"],
    "secteur": "UN des 8 choix",
    "type_opportunite": "Type",
    "localisation": "Ville(s)",
    "resume": "Synthèse avec infos fichiers.",
    "mots_cles": ["mot1", "mot2", "mot3", "mot4", "mot5"]
}}
</format_reponse>

ANALYSE MAINTENANT.
"""


# ============================================================================
# FONCTION PRINCIPALE D'ANALYSE
# ============================================================================

def analyze_opportunity(
    data: Dict, 
    api_key: str, 
    ai_type: str = "claude"
) -> Dict:
    """
    Analyse une opportunité avec l'IA (v1.8 avec contenu fichiers).
    
    Args:
        data: Données scrapées incluant fichiers avec contenu
        api_key: Clé API
        ai_type: "claude" ou "gemini"
    
    Returns:
        Dict avec analyse structurée
    """
    if ai_type == "claude":
        return analyze_with_claude(data, api_key)
    else:
        return analyze_with_gemini(data, api_key)


def create_fallback_analysis(data: Dict) -> Dict:
    """Crée une analyse fallback si l'IA échoue."""
    texte = data.get('texte_complet', '')
    
    # Emails de la page
    emails = extract_emails_regex(texte)
    
    # Emails des fichiers (v1.8)
    emails_files = data.get('emails_from_files', [])
    all_emails = list(set(emails + emails_files))
    
    # Résumé
    resume = texte[:200] + "..." if len(texte) > 200 else texte
    
    fichiers = data.get('fichiers_attaches', [])
    if fichiers:
        nb_parses = sum(1 for f in fichiers if f.get('contenu_texte'))
        resume += f" ({len(fichiers)} fichier(s), {nb_parses} parsé(s))"
    
    return {
        'organisation': data.get('organisation', 'Non spécifié'),
        'emails': all_emails,
        'secteur': 'Autre',
        'type_opportunite': 'Non déterminé',
        'localisation': 'Non spécifié',
        'resume': resume,
        'mots_cles': []
    }


def analyze_with_gemini(data: Dict, api_key: str) -> Dict:
    """Analyse avec Gemini (v1.9 - texte unifié)."""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            generation_config={
                'temperature': 0.1,
                'top_p': 0.9,
                'max_output_tokens': 1024,
            }
        )
        
        # PATCH v1.9: Merge tout le contenu
        texte_unifie = merge_all_content(data)
        
        # Limiter taille
        if len(texte_unifie) > 12000:
            texte_unifie = texte_unifie[:12000] + "...[tronqué]"
        
        # Emails pré-extraits (regex)
        emails_page = extract_emails_regex(data.get('texte_complet', ''))
        emails_fichiers = []
        for f in data.get('fichiers_attaches', []):
            emails_fichiers.extend(f.get('emails_fichier', []))
        
        # PATCH v1.9: Prompt simplifié
        prompt = f"""Tu es un extracteur de données. Analyse le texte ci-dessous et extrait UNIQUEMENT:

1. ORGANISATION: Le nom EXACT et COMPLET de l'entité qui publie cette offre.
   - Copie le nom tel qu'il apparaît, sans abréger ni reformuler.
   - Cherche: Association, Fondation, ONG, Direction, Ministère, etc.

2. EMAILS: Tous les emails de contact trouvés.

RÈGLES STRICTES:
- NE PAS inventer. Si non trouvé, mettre "Non spécifié".
- NE PAS résumer ou interpréter. Copier EXACTEMENT.
- Répondre UNIQUEMENT en JSON valide, sans markdown.

=== TEXTE À ANALYSER ===

{texte_unifie}

=== FIN DU TEXTE ===

Réponds avec ce JSON uniquement:
{{"organisation": "...", "emails": ["...", "..."], "secteur": "Autre", "type_opportunite": "Offre", "localisation": "Non spécifié", "resume": "...", "mots_cles": []}}
"""
        
        response = model.generate_content(prompt)
        response_text = clean_json_response(response.text.strip())
        result = json.loads(response_text)
        
        # PATCH v1.9: Fusionner et normaliser emails
        emails_ia = result.get('emails', [])
        all_emails = normalize_and_dedup_emails(emails_page + emails_fichiers, emails_ia)
        result['emails'] = all_emails
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur Gemini: {e}")
        return create_fallback_analysis(data)


def analyze_with_claude(data: Dict, api_key: str) -> Dict:
    """Analyse avec Claude (v1.9 - texte unifié)."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # PATCH v1.9: Merge tout le contenu
        texte_unifie = merge_all_content(data)
        
        # Limiter taille
        if len(texte_unifie) > 12000:
            texte_unifie = texte_unifie[:12000] + "...[tronqué]"
        
        # Emails pré-extraits (regex)
        emails_page = extract_emails_regex(data.get('texte_complet', ''))
        emails_fichiers = []
        for f in data.get('fichiers_attaches', []):
            emails_fichiers.extend(f.get('emails_fichier', []))
        
        # PATCH v1.9: Prompt simplifié
        prompt = f"""Tu es un extracteur de données. Analyse le texte ci-dessous et extrait UNIQUEMENT:

1. ORGANISATION: Le nom EXACT et COMPLET de l'entité qui publie cette offre.
   - Copie le nom tel qu'il apparaît, sans abréger ni reformuler.
   - Cherche: Association, Fondation, ONG, Direction, Ministère, etc.

2. EMAILS: Tous les emails de contact trouvés.

RÈGLES STRICTES:
- NE PAS inventer. Si non trouvé, mettre "Non spécifié".
- NE PAS résumer ou interpréter. Copier EXACTEMENT.
- Répondre UNIQUEMENT en JSON valide, sans markdown.

=== TEXTE À ANALYSER ===

{texte_unifie}

=== FIN DU TEXTE ===

Réponds avec ce JSON uniquement:
{{"organisation": "...", "emails": ["...", "..."], "secteur": "Autre", "type_opportunite": "Offre", "localisation": "Non spécifié", "resume": "...", "mots_cles": []}}
"""
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.1,
            messages=[{"role": "user", "content": prompt}]
        )
        
        response_text = clean_json_response(message.content[0].text.strip())
        result = json.loads(response_text)
        
        # PATCH v1.9: Fusionner et normaliser emails
        emails_ia = result.get('emails', [])
        all_emails = normalize_and_dedup_emails(emails_page + emails_fichiers, emails_ia)
        result['emails'] = all_emails
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur Claude: {e}")
        return create_fallback_analysis(data)


# ============================================================================
# UTILITAIRES
# ============================================================================

def clean_json_response(text: str) -> str:
    """Nettoie la réponse IA pour extraire le JSON."""
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
        if text.strip().startswith("json"):
            text = text.strip()[4:]
    return text.strip()


def extract_emails_regex(text: str) -> List[str]:
    """Extraction emails par regex (fallback)."""
    if not text:
        return []
    
    emails = set()
    
    # Standard
    pattern1 = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails.update(re.findall(pattern1, text))
    
    # Avec espaces
    pattern2 = r'\b([A-Za-z0-9._%+-]+)\s*@\s*([A-Za-z0-9.-]+)\s*\.\s*([A-Z|a-z]{2,})\b'
    for match in re.finditer(pattern2, text):
        emails.add(f"{match.group(1)}@{match.group(2)}.{match.group(3)}")
    
    # AT/DOT
    pattern3 = r'\b([A-Za-z0-9._%+-]+)\s+(?:at|AT)\s+([A-Za-z0-9.-]+)\s+(?:dot|DOT)\s+([A-Z|a-z]{2,})\b'
    for match in re.finditer(pattern3, text):
        emails.add(f"{match.group(1)}@{match.group(2)}.{match.group(3)}")
    
    # [at] [dot]
    pattern4 = r'\b([A-Za-z0-9._%+-]+)\s*\[at\]\s*([A-Za-z0-9.-]+)\s*\[dot\]\s*([A-Z|a-z]{2,})\b'
    for match in re.finditer(pattern4, text, re.IGNORECASE):
        emails.add(f"{match.group(1)}@{match.group(2)}.{match.group(3)}")
    
    cleaned = []
    for email in emails:
        email = re.sub(r'\s+', '', email).lower()
        if '@' in email and '.' in email.split('@')[1]:
            cleaned.append(email)
    
    return list(set(cleaned))


# ============================================================================
# TEST
# ============================================================================

def test_analyzer():
    """Test analyzer v1.8."""
    print("🧪 TEST ANALYZER v1.8 (avec contenu fichiers)")
    print("=" * 60)
    
    test_data = {
        'url': 'https://tanmia.ma/test',
        'organisation': 'CIDEAL',
        'titre': 'Mission évaluation',
        'date': '2026-02-11',
        'texte_complet': "L'ALCS recherche un consultant. Contact: web@alcs.ma",
        'fichiers_attaches': [
            {
                'nom': 'TDR_Mission.pdf',
                'url': 'https://example.com/tdr.pdf',
                'type': 'pdf',
                'contenu_texte': "Termes de Référence\nMission: Évaluation VIH\nBudget: 50000 MAD\nDurée: 45 jours\nContact: tdr@alcs.ma",
                'emails_fichier': ['tdr@alcs.ma']
            }
        ],
        'emails_from_files': ['tdr@alcs.ma']
    }
    
    print("\n1. Formatage fichiers pour prompt:")
    fichiers_str = format_fichiers_for_prompt(test_data['fichiers_attaches'])
    print(fichiers_str[:500] + "...")
    
    print("\n2. Emails from files:")
    emails = get_all_emails_from_files(test_data['fichiers_attaches'])
    print(f"   {emails}")
    
    print("\n3. Fallback analysis:")
    fallback = create_fallback_analysis(test_data)
    print(f"   Emails fusionnés: {fallback['emails']}")
    
    print("\n✅ Test terminé")


if __name__ == "__main__":
    test_analyzer()
