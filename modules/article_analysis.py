import streamlit as st
import logging
from modules.gemini_api import analyze_with_gemini_cached

def analyze_article(article, query):
    """Analyze a single article using Gemini analysis with error handling."""
    try:
        if not article.get("abstract"):
            return {"pmid": article.get("pmid"), "error": "Missing abstract"}
        result = analyze_with_gemini_cached(article["abstract"], query)
        return {"pmid": article.get("pmid"), "analysis": result}
    except Exception as e:
        logging.error(f"Error analyzing article {article.get('pmid')}: {e}")
        return {"pmid": article.get("pmid"), "error": str(e)}

def analyze_articles_with_progress(articles, query):
    """Analyze articles with Streamlit progress indication and error handling."""
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = []
    total = len(articles)
    for i, article in enumerate(articles):
        status_text.text(f"📄 Analyzing article {i+1}/{total}: {article.get('title', '')[:60]}")
        result = analyze_article(article, query)
        if "error" in result:
            st.warning(f"⚠️ Skipped article {i+1}: {result['error']}")
        else:
            results.append(result)
        progress_bar.progress((i + 1) / total)
    progress_bar.empty()
    status_text.empty()
    return results