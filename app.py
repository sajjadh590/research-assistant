import streamlit as st
import logging
from datetime import timedelta
from modules.pubmed_api import search_pubmed_cached
from modules.gemini_api import analyze_with_gemini_cached
from modules.article_analysis import analyze_articles_with_progress

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

st.set_page_config(
    page_title="Research Gap Finder",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔬 Research Assistant — Identify Research Gaps with Gemini AI")

# --- Main Input ---
query = st.text_input(
    "Enter your research topic or keywords",
    placeholder="e.g. pediatric asthma treatment, cancer immunotherapy, etc."
)
max_results = st.slider("Articles to analyze", 5, 50, 10, 1)

if st.button("Search and Analyze", type="primary") and query.strip():
    with st.spinner("🔎 Searching PubMed..."):
        try:
            pubmed_results = search_pubmed_cached(query, max_results)
            if not pubmed_results:
                st.warning("No articles found for your query.")
                st.stop()
        except Exception as e:
            st.error(f"❌ Failed to fetch from PubMed: {e}")
            logging.error(f"PubMed fetch error: {e}", exc_info=True)
            st.stop()

    st.success(f"Found {len(pubmed_results)} articles. Starting analysis...")
    articles_to_process = pubmed_results

    with st.spinner("🧠 Analyzing articles using Gemini AI..."):
        # Each analysis is separately cached and error-handled
        analysis_results = analyze_articles_with_progress(articles_to_process, query)
        if analysis_results:
            st.success(f"✅ Completed analysis of {len(analysis_results)} articles.")
            # Display summary or pass to next phase/component
        else:
            st.warning("Analysis did not return any usable insights.")
else:
    st.info("Enter a query and click 'Search and Analyze'.")