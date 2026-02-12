"""
Tanmia Scraper MVP v1.8 - Interface Streamlit
Scraping et analyse IA avec PARSING COMPLET des fichiers attachés

CHANGELOG v1.8:
- NOUVEAU: Option activer/désactiver parsing fichiers
- NOUVEAU: Affichage emails extraits des fichiers
- NOUVEAU: Indicateur "fichier parsé" dans détails
- NOUVEAU: KPI fichiers parsés vs détectés
- Amélioration: Temps estimé ajusté pour parsing
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import traceback

# Import modules locaux
from scraper import scrape_tanmia
from analyzer import analyze_opportunity
from utils import (
    export_to_excel,
    create_export_filename,
    calculate_statistics,
    merge_analysis_results
)

# Import modules pour cache
import json
import hashlib
from pathlib import Path


# ============================================================================
# SYSTÈME DE CACHE JSON
# ============================================================================

CACHE_DIR = Path("cache_scraping")
CACHE_DIR.mkdir(exist_ok=True)


def get_cache_key(url_type: str, max_pages: int, parse_files: bool) -> str:
    """Génère clé unique incluant option parsing (v1.8)."""
    today = datetime.now().strftime('%Y-%m-%d')
    parse_flag = "parsed" if parse_files else "meta"
    raw = f"{url_type}_{max_pages}_{parse_flag}_{today}"
    return hashlib.md5(raw.encode()).hexdigest()


def save_to_cache(cache_key: str, scraped_data: list, analysis_results: list):
    """Sauvegarde dans cache JSON."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    data = {
        'scraped_data': scraped_data,
        'analysis_results': analysis_results,
        'timestamp': datetime.now().isoformat(),
        'version': '1.8'
    }
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_from_cache(cache_key: str) -> dict:
    """Charge depuis cache si existe."""
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None


# ============================================================================
# SESSION STATE
# ============================================================================

if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'df' not in st.session_state:
    st.session_state.df = None


# ============================================================================
# CONFIGURATION PAGE
# ============================================================================

st.set_page_config(
    page_title="Tanmia Scraper MVP v1.8",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# STYLES CSS
# ============================================================================

st.markdown("""
<style>
    h1 {
        color: #366092;
        padding-bottom: 10px;
        border-bottom: 3px solid #366092;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
    }
    
    .stButton > button {
        width: 100%;
        background-color: #366092;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 10px;
        border: none;
    }
    
    .stButton > button:hover {
        background-color: #2c4d73;
    }
    
    .email-badge {
        background-color: #28a745;
        color: white;
        padding: 3px 10px;
        border-radius: 15px;
        font-size: 14px;
        margin: 2px;
        display: inline-block;
    }
    
    .file-parsed {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 8px;
        margin: 5px 0;
    }
    
    .file-not-parsed {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 5px;
        padding: 8px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.image("https://tanmia.ma/wp-content/themes/tanmia/images/tanmia-logo.svg", width=200)
    
    st.markdown("---")
    
    st.header("⚙️ Configuration")
    
    # Badge version
    st.markdown("**📦 Version 1.8** - *Parsing Fichiers*")
    
    st.markdown("---")
    
    # IA
    st.subheader("1️⃣ Intelligence Artificielle")
    ai_choice = st.radio(
        "Sélectionnez l'IA:",
        ["🔵 Claude Sonnet 4", "🟢 Gemini 2.5 Pro"]
    )
    
    ai_type = "claude" if "Claude" in ai_choice else "gemini"
    ai_label = "Claude" if ai_type == "claude" else "Gemini"
    
    api_key = st.text_input(
        f"🔑 Clé API {ai_label}:",
        type="password"
    )
    
    st.markdown("---")
    
    # Source
    st.subheader("2️⃣ Source de données")
    url_choice = st.radio(
        "Type d'opportunités:",
        ["📢 Appels d'offres", "💼 Offres d'emploi"]
    )
    
    url_type = "appels-doffres" if "Appel" in url_choice else "offres-demploi"
    st.info(f"🔗 URL: https://tanmia.ma/{url_type}/")
    
    st.markdown("---")
    
    # Paramètres
    st.subheader("3️⃣ Paramètres")
    max_pages = st.slider(
        "📄 Nombre de pages:",
        min_value=1,
        max_value=50,
        value=5
    )
    
    # NOUVEAU v1.8: Option parsing
    st.markdown("---")
    st.subheader("4️⃣ Parsing Fichiers (v1.8)")
    
    parse_files = st.checkbox(
        "📥 Parser le contenu des fichiers",
        value=True,
        help="Télécharge et extrait le texte des PDF, DOC, DOCX pour trouver des emails et enrichir l'analyse"
    )
    
    if parse_files:
        st.success("✅ Parsing activé (PDF, DOC, DOCX)")
        st.caption("⚠️ Temps scraping ~x3-5")
        estimated_time = max_pages * 5  # Plus long avec parsing
    else:
        st.info("ℹ️ Métadonnées uniquement (v1.7)")
        estimated_time = max_pages * 2
    
    st.caption(f"⏱️ Durée estimée: ~{estimated_time} minutes")
    st.caption(f"📊 ~{max_pages * 8} opportunités")
    
    # Dépendances
    if parse_files:
        st.markdown("---")
        st.caption("**Dépendances requises:**")
        st.code("pip install pdfplumber python-docx", language="bash")


# ============================================================================
# MAIN
# ============================================================================

st.title("🎯 TANMIA SCRAPER - MVP v1.8")
st.markdown("**Extraction avec PARSING COMPLET des fichiers attachés** | *📥 PDF, DOC, DOCX*")

st.markdown("---")

# Validation
api_valid = api_key and len(api_key) > 10

if not api_valid:
    st.warning("⚠️ Veuillez configurer votre clé API dans la barre latérale")
    st.info("""
    📝 **Clés API:**
    - **Claude:** [console.anthropic.com](https://console.anthropic.com)
    - **Gemini:** [makersuite.google.com](https://makersuite.google.com)
    """)

# Boutons
col_btn1, col_btn2 = st.columns([3, 1])

with col_btn1:
    launch_button = st.button(
        "🚀 LANCER LE SCRAPING & ANALYSE",
        type="primary",
        disabled=not api_valid,
        use_container_width=True
    )

with col_btn2:
    if st.session_state.scraped_data is not None:
        if st.button("🗑️ Réinitialiser", use_container_width=True):
            st.session_state.scraped_data = None
            st.session_state.analysis_results = None
            st.session_state.df = None
            st.rerun()


# ============================================================================
# LOGIQUE PRINCIPALE
# ============================================================================

if launch_button and api_valid:
    cache_key = get_cache_key(url_type, max_pages, parse_files)
    cached_data = load_from_cache(cache_key)
    
    if cached_data:
        st.success("💾 Données en cache! Chargement instantané...")
        st.session_state.scraped_data = cached_data['scraped_data']
        st.session_state.analysis_results = cached_data['analysis_results']
    else:
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_container = st.empty()
            
            def update_progress(progress, message):
                progress_bar.progress(progress)
                status_text.text(message)
            
            # Phase 1: Scraping + Parsing fichiers
            parse_label = "avec parsing PDF/DOC" if parse_files else "métadonnées"
            with status_container:
                st.info(f"🕷️ **PHASE 1/2:** Scraping ({parse_label})...")
            
            scraped_data = scrape_tanmia(
                url_type=url_type,
                max_pages=max_pages,
                progress_callback=update_progress,
                parse_attachments=parse_files  # v1.8
            )
            
            if not scraped_data or len(scraped_data) == 0:
                st.error("❌ Aucune opportunité trouvée.")
                st.stop()
            
            # Stats rapides (v1.8)
            total_fichiers = sum(len(d.get('fichiers_attaches', [])) for d in scraped_data)
            total_parses = sum(
                sum(1 for f in d.get('fichiers_attaches', []) if f.get('contenu_texte'))
                for d in scraped_data
            )
            total_emails_files = sum(len(d.get('emails_from_files', [])) for d in scraped_data)
            
            with status_container:
                st.info(f"📎 {total_fichiers} fichiers | {total_parses} parsés | {total_emails_files} emails extraits")
            
            # Phase 2: Analyse IA
            with status_container:
                st.info(f"🤖 **PHASE 2/2:** Analyse IA ({ai_label})...")
            
            analysis_results = []
            
            for idx, item in enumerate(scraped_data):
                progress = 0.5 + ((idx + 1) / len(scraped_data)) * 0.5
                progress_bar.progress(progress)
                
                titre_short = item['titre'][:40]
                nb_emails_f = len(item.get('emails_from_files', []))
                emails_info = f" | 📧 {nb_emails_f} email(s) fichiers" if nb_emails_f > 0 else ""
                status_text.text(f"🤖 {idx+1}/{len(scraped_data)}: {titre_short}...{emails_info}")
                
                try:
                    analysis = analyze_opportunity(item, api_key, ai_type)
                    analysis_results.append(analysis)
                except Exception as e:
                    st.warning(f"⚠️ Erreur analyse: {titre_short}")
                    analysis_results.append({
                        'organisation': 'Erreur',
                        'emails': item.get('emails_from_files', []),  # Au moins ceux des fichiers
                        'secteur': 'Autre',
                        'type_opportunite': 'Non déterminé',
                        'localisation': 'Non spécifié',
                        'resume': item.get('texte_complet', '')[:200],
                        'mots_cles': []
                    })
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.scraped_data = scraped_data
            st.session_state.analysis_results = analysis_results
            
            save_to_cache(cache_key, scraped_data, analysis_results)
            
        except Exception as e:
            st.error(f"❌ **ERREUR:** {str(e)}")
            with st.expander("🔍 Détails"):
                st.code(traceback.format_exc())
            st.stop()


# ============================================================================
# AFFICHAGE RÉSULTATS
# ============================================================================

if st.session_state.scraped_data:
    merged_data = merge_analysis_results(
        st.session_state.scraped_data,
        st.session_state.analysis_results
    )
    st.session_state.df = pd.DataFrame(merged_data)
    df = st.session_state.df
    
    st.success(f"✅ **TERMINÉ:** {len(df)} opportunités analysées")
    
    st.markdown("---")
    
    # KPIs (v1.8 enrichi)
    st.header("📊 Statistiques")
    
    stats = calculate_statistics(df)
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        st.metric("🎯 Total", stats['total_opportunites'])
    
    with col2:
        st.metric("📧 Emails page", f"{stats['avec_email']}", f"{stats['taux_email']}%")
    
    with col3:
        st.metric("📎 Fichiers", stats['total_fichiers'])
    
    with col4:
        # NOUVEAU v1.8
        st.metric(
            "📥 Parsés", 
            stats['fichiers_parses'],
            f"{stats['taux_parsing']}%",
            help="Fichiers PDF/DOC/DOCX dont le contenu a été extrait"
        )
    
    with col5:
        # NOUVEAU v1.8
        st.metric(
            "📧 Emails fichiers",
            stats['emails_from_files'],
            help="Opportunités avec emails trouvés dans les fichiers attachés"
        )
    
    with col6:
        st.metric("🏢 Secteurs", stats['secteurs_uniques'])
    
    st.markdown("---")
    
    # Tableau
    st.header("📋 Résultats")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Toutes",
        "📧 Avec emails",
        "📎 Avec fichiers",
        "📥 Fichiers parsés",  # NOUVEAU v1.8
        "🔍 Détails"
    ])
    
    with tab1:
        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("🔗", width="small"),
                "Organisation": st.column_config.TextColumn("🏢 Org", width="medium"),
                "Titre": st.column_config.TextColumn("📝 Titre", width="large"),
                "Email": st.column_config.TextColumn("📧 Email", width="medium"),
                "Emails_Fichiers": st.column_config.TextColumn("📧📎", width="medium"),
                "Nb_Fichiers": st.column_config.NumberColumn("📎", width="small"),
                "Nb_Parses": st.column_config.NumberColumn("📥", width="small"),
            },
            use_container_width=True,
            height=500
        )
    
    with tab2:
        df_emails = df[df['Email'].str.len() > 0]
        if len(df_emails) > 0:
            st.dataframe(df_emails, use_container_width=True, height=500)
        else:
            st.info("Aucune opportunité avec email")
    
    with tab3:
        df_files = df[df['Nb_Fichiers'] > 0]
        if len(df_files) > 0:
            st.success(f"📎 {len(df_files)} opportunités avec fichiers")
            st.dataframe(df_files[['Organisation', 'Titre', 'Fichiers', 'Nb_Fichiers', 'Nb_Parses', 'Emails_Fichiers']], height=500)
        else:
            st.info("Aucune opportunité avec fichiers")
    
    # NOUVEAU v1.8: Onglet fichiers parsés
    with tab4:
        df_parsed = df[df['Nb_Parses'] > 0]
        if len(df_parsed) > 0:
            st.success(f"📥 {len(df_parsed)} opportunités avec fichiers parsés")
            st.dataframe(
                df_parsed[['Organisation', 'Titre', 'Fichiers', 'Nb_Parses', 'Emails_Fichiers', 'URL']],
                column_config={
                    "URL": st.column_config.LinkColumn("🔗"),
                    "Emails_Fichiers": st.column_config.TextColumn("📧 Emails extraits"),
                },
                height=500
            )
        else:
            st.info("Aucun fichier parsé (parsing désactivé ou pas de PDF/DOC/DOCX)")
    
    with tab5:
        if len(df) > 0:
            selected_idx = st.selectbox(
                "Sélectionnez une opportunité:",
                range(len(df)),
                format_func=lambda x: f"{df.iloc[x]['Organisation']} - {df.iloc[x]['Titre'][:50]}"
            )
            
            selected = df.iloc[selected_idx]
            selected_scraped = st.session_state.scraped_data[selected_idx]
            
            st.markdown("---")
            
            col_left, col_right = st.columns([2, 1])
            
            with col_left:
                st.subheader(selected['Titre'])
                st.markdown(f"**🏢 Organisation:** {selected['Organisation']}")
                st.markdown(f"**📅 Date:** {selected['Date']}")
                st.markdown(f"**📍 Localisation:** {selected['Localisation']}")
                
                # Emails combinés
                st.markdown("**📧 Emails:**")
                if selected['Email']:
                    st.success(selected['Email'])
                else:
                    st.caption("*Aucun email page*")
            
            with col_right:
                st.markdown(f"**🎯 Secteur:** {selected['Secteur']}")
                st.markdown(f"**💼 Type:** {selected['Type']}")
            
            st.markdown("---")
            
            st.markdown("**📝 Résumé IA:**")
            st.info(selected['Résumé'])
            
            st.markdown("**🔑 Mots-clés:**")
            st.caption(selected['Mots-clés'])
            
            # ================================================================
            # FICHIERS ATTACHÉS DÉTAILLÉS (v1.8)
            # ================================================================
            st.markdown("---")
            st.markdown("**📎 Fichiers attachés:**")
            
            fichiers = selected_scraped.get('fichiers_attaches', [])
            
            if fichiers:
                for f in fichiers:
                    is_parsed = bool(f.get('contenu_texte'))
                    emails_f = f.get('emails_fichier', [])
                    
                    # Badge parsing
                    if is_parsed:
                        st.markdown(f"""
                        <div class="file-parsed">
                            <strong>📄 {f['nom']}</strong> ({f['type'].upper()}) 
                            <span style="color: green;">✅ PARSÉ</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="file-not-parsed">
                            <strong>📄 {f['nom']}</strong> ({f['type'].upper()})
                            <span style="color: gray;">⬜ Non parsé</span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Emails extraits du fichier (v1.8)
                    if emails_f:
                        st.markdown("📧 **Emails extraits de ce fichier:**")
                        for email in emails_f:
                            st.markdown(f'<span class="email-badge">{email}</span>', unsafe_allow_html=True)
                    
                    # Aperçu contenu (v1.8)
                    contenu = f.get('contenu_texte', '')
                    if contenu:
                        with st.expander(f"📖 Aperçu contenu ({len(contenu)} chars)"):
                            st.text(contenu[:1000] + "..." if len(contenu) > 1000 else contenu)
                    
                    # Bouton téléchargement
                    st.link_button(f"⬇️ Télécharger {f['nom']}", f['url'])
                    st.markdown("---")
            else:
                st.caption("*Aucun fichier attaché*")
            
            st.link_button("🔗 Voir l'annonce complète", selected['URL'])
    
    st.markdown("---")
    
    # Export
    st.header("📥 Export")
    
    col_export1, col_export2 = st.columns([3, 1])
    
    with col_export1:
        excel_data = export_to_excel(df)
        filename = create_export_filename(url_type)
        
        st.download_button(
            label="📥 TÉLÉCHARGER EXCEL (v1.8 enrichi)",
            data=excel_data,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col_export2:
        st.metric("📊 Lignes", len(df))
        st.metric("📧 Emails fichiers", stats['emails_from_files'])


# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")

col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.caption("🎯 **Tanmia Scraper MVP v1.8**")
    st.caption("*📥 Parsing PDF/DOC/DOCX*")

with col_footer2:
    st.caption("🤖 Claude & Gemini")

with col_footer3:
    st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d')}")
