import logging
import streamlit as st
import requests
from ratelimit import limits, sleep_and_retry
from datetime import timedelta

PUBMED_RATE_CALLS = 3
PUBMED_RATE_PERIOD = 1  # seconds

PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

@sleep_and_retry
@limits(calls=PUBMED_RATE_CALLS, period=PUBMED_RATE_PERIOD)
def fetch_from_pubmed(query, max_results):
    try:
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
        }
        r = requests.get(PUBMED_API_URL, params=params, timeout=10)
        r.raise_for_status()
        idlist = r.json()["esearchresult"]["idlist"]
        if not idlist:
            return []
        # Fetch summaries for selected PMIDs
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(idlist),
            "retmode": "xml",
        }
        rf = requests.get(PUBMED_FETCH_URL, params=fetch_params, timeout=15)
        rf.raise_for_status()
        # Minimal mock parse here: Extend with xml parsing for actual abstracts
        articles = [{"pmid": pid, "title": f"PMID: {pid}", "abstract": ""} for pid in idlist]
        return articles

    except requests.Timeout:
        st.error("⏱️ PubMed request timed out. Please try again.")
        logging.error(f"PubMed timeout for query: {query}")
        return []
    except requests.RequestException as e:
        st.error(f"❌ Network error: {str(e)}")
        logging.error(f"PubMed request error: {e}", exc_info=True)
        return []
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")
        logging.error(f"Unexpected error in PubMed fetch: {e}", exc_info=True)
        return []

@st.cache_data(ttl=timedelta(hours=24))
def search_pubmed_cached(query, max_results=10):
    """Cache PubMed search results"""
    return fetch_from_pubmed(query, max_results)