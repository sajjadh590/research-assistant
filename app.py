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

# --- Sidebar settings ---
with st.sidebar:
    st.header("Settings")
    # Optional runtime API key (stored in session only)
    if "GEMINI_RUNTIME_KEY" not in st.session_state:
        st.session_state.GEMINI_RUNTIME_KEY = ""
    runtime_key = st.text_input("Gemini API key (optional)", type="password", value=st.session_state.GEMINI_RUNTIME_KEY)
    st.session_state.GEMINI_RUNTIME_KEY = runtime_key
    if runtime_key:
        import os
        os.environ["GEMINI_API_KEY"] = runtime_key

    model_name = st.selectbox(
        "Gemini model",
        options=["gemini-1.5-pro", "gemini-1.5-flash"],
        index=0
    )
    delay_seconds = st.slider("Delay between analyses (s)", 0.0, 2.0, 0.5, 0.1)

    # Key status indicator
    try:
        has_secret = "GEMINI_API_KEY" in st.secrets
    except Exception:
        has_secret = False
    import os
    has_env = bool(os.getenv("GEMINI_API_KEY"))
    has_key = bool(runtime_key) or has_secret or has_env
    st.session_state["HAS_GEMINI_KEY"] = has_key
    if has_key:
        st.success("API key detected")
    else:
        st.warning("No API key set. Enter one above or add to secrets.")

    # Test key button
    from modules.gemini_api import validate_gemini_key
    if st.button("Test API key"):
        ok, err = validate_gemini_key(model_name=model_name)
        if ok:
            st.success("Key is valid and model is reachable.")
        else:
            st.error(f"Key validation failed: {err}")

# --- Main Input ---
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input(
        "Enter your research topic or keywords",
        placeholder="e.g. pediatric asthma treatment, cancer immunotherapy, etc."
    )
with col2:
    max_results = st.slider("Articles", 5, 50, 10, 1)

search_disabled = len(query.strip()) == 0 or not st.session_state.get("HAS_GEMINI_KEY", False)
if st.button("Search and Analyze", type="primary", disabled=search_disabled) and query.strip() and st.session_state.get("HAS_GEMINI_KEY", False):
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
        analysis_results = analyze_articles_with_progress(articles_to_process, query, delay_seconds=delay_seconds, model_name=model_name)
        if analysis_results:
            st.success(f"✅ Completed analysis of {len(analysis_results)} articles.")
            # Display structured results
            try:
                import pandas as pd
                df = pd.DataFrame(analysis_results)
                if not df.empty:
                    st.subheader("Analysis Results")
                    st.dataframe(df[["pmid", "title", "analysis"]], use_container_width=True)

                    # Export buttons
                    csv = df.to_csv(index=False).encode('utf-8')
                    json_str = df.to_json(orient='records', force_ascii=False).encode('utf-8')
                    st.download_button("Download CSV", data=csv, file_name="analysis_results.csv", mime="text/csv")
                    st.download_button("Download JSON", data=json_str, file_name="analysis_results.json", mime="application/json")
            except Exception as e:
                logging.warning(f"Failed to render results table: {e}")
        else:
            st.warning("Analysis did not return any usable insights.")
else:
    st.info("Enter a query and click 'Search and Analyze'.")