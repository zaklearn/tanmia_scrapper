# 🎯 TANMIA SCRAPER MVP v1.8

## 📥 Nouveauté: Parsing Complet des Fichiers Attachés

Cette version ajoute le **téléchargement et parsing** du contenu des fichiers PDF, DOC et DOCX pour extraire automatiquement les emails et enrichir l'analyse IA.

---

## 🆕 Changelog v1.8 vs v1.7

| Fonctionnalité | v1.7 | v1.8 |
|----------------|------|------|
| Détection fichiers | ✅ | ✅ |
| Extraction contenu PDF | ❌ | ✅ |
| Extraction contenu DOCX | ❌ | ✅ |
| Extraction contenu DOC | ❌ | ✅ |
| Emails depuis fichiers | ❌ | ✅ |
| Fusion emails page+fichiers | ❌ | ✅ |
| Option activer/désactiver | ❌ | ✅ |

---

## 📦 Structure

```
TANMIA_SCRAPER_V18/
├── app.py          # Interface Streamlit
├── scraper.py      # Scraping + parsing fichiers
├── analyzer.py     # Analyse IA enrichie
├── utils.py        # Export + statistiques
└── README_V18.md   # Documentation
```

---

## 🚀 Installation

### Prérequis

```bash
# Python 3.10+
pip install streamlit pandas openpyxl requests beautifulsoup4 lxml

# IA
pip install anthropic google-generativeai

# NOUVEAU v1.8: Parsing fichiers
pip install pdfplumber python-docx

# Optionnel: parsing .doc (ancien format)
sudo apt install antiword  # Linux
```

### Lancement

```bash
cd TANMIA_SCRAPER_V18
streamlit run app.py
```

---

## 🔧 Fonctionnement du Parsing

### Formats Supportés

| Format | Librairie | Notes |
|--------|-----------|-------|
| PDF | `pdfplumber` | Texte + tableaux (max 20 pages) |
| DOCX | `python-docx` | Paragraphes + tableaux |
| DOC | `antiword` | Nécessite installation système |

### Processus

```
1. Détection lien fichier dans page HTML
2. Téléchargement fichier (max 10 MB)
3. Parsing selon type
4. Extraction texte (max 5000 chars)
5. Extraction emails via regex
6. Injection dans prompt IA
```

### Données Extraites

```python
{
    'nom': 'TDR_Mission.pdf',
    'url': 'https://...',
    'type': 'pdf',
    'contenu_texte': 'Termes de Référence...',  # NOUVEAU
    'emails_fichier': ['contact@org.ma']        # NOUVEAU
}
```

---

## 📊 Colonnes Excel (v1.8)

| Colonne | Description |
|---------|-------------|
| URL | Lien opportunité |
| Organisation | Nom extrait |
| Titre | Titre offre |
| Email | Emails page (fusionnés) |
| Secteur | Catégorie |
| Type | CDI, CDD, etc. |
| Localisation | Ville(s) |
| Résumé | Synthèse IA |
| Mots-clés | Tags |
| Fichiers | Noms fichiers |
| Liens_Fichiers | URLs |
| Nb_Fichiers | Compteur |
| **Emails_Fichiers** | Emails extraits des fichiers |
| **Nb_Parses** | Fichiers parsés avec succès |

---

## ⚙️ Options Interface

### Parsing Activé (défaut)

- Télécharge PDF, DOC, DOCX
- Extrait contenu textuel
- Cherche emails dans fichiers
- Enrichit prompts IA

**Impact:** Temps scraping x3-5

### Parsing Désactivé

- Mode v1.7: métadonnées uniquement
- Plus rapide
- Pas d'emails fichiers

---

## 📈 Statistiques v1.8

L'interface affiche:

- **Fichiers détectés:** Total fichiers trouvés
- **Fichiers parsés:** PDF/DOC/DOCX traités
- **Taux parsing:** % fichiers analysés
- **Emails fichiers:** Opportunités avec emails extraits

---

## 💡 Cas d'Usage

### Trouver les TDR avec emails directs

1. Activer parsing ✅
2. Lancer scraping appels d'offres
3. Onglet "📥 Fichiers parsés"
4. Colonne "Emails_Fichiers" 

### Export rapide sans parsing

1. Désactiver parsing ❌
2. Scraping rapide (mode v1.7)
3. Export Excel métadonnées

---

## ⚠️ Limitations

- **Taille max fichier:** 10 MB
- **Pages PDF max:** 20
- **Contenu max:** 5000 caractères/fichier
- **Formats non supportés:** XLS, XLSX, PPT (détectés mais non parsés)
- **DOC:** Nécessite `antiword` installé

---

## 🧪 Tests

```bash
# Test complet
python scraper.py

# Test parsing seul
python -c "
from scraper import download_and_parse_attachment
text, emails = download_and_parse_attachment('https://example.com/test.pdf', 'pdf')
print(f'Texte: {len(text)} chars, Emails: {emails}')
"
```

---

## 🔜 Évolutions Futures

- **OCR:** Support PDFs scannés (Tesseract)
- **Parsing XLS/XLSX:** Extraction données tabulaires
- **Cache fichiers:** Éviter re-téléchargement
- **Parsing parallèle:** Multithread pour performance

---

## 📝 Notes Techniques

### Performance

| Scénario | Temps moyen |
|----------|-------------|
| Sans parsing | ~2 min/page |
| Avec parsing | ~5-8 min/page |

### Mémoire

- Fichiers traités en streaming
- Contenu tronqué à 5000 chars
- Pas de stockage local

### Sécurité

- Vérification taille avant téléchargement
- Timeout téléchargement: 60s
- Pas d'exécution code des fichiers

---

## 👨‍💻 Auteur

HBN Consulting SARL

---

## 📄 Licence

Usage interne - Tous droits réservés
