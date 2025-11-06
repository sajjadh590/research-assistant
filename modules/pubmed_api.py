import streamlit as st
import requests
import logging
from datetime import timedelta
from ratelimit import limits, sleep_and_retry
import time
from xml.etree import ElementTree # برای خواندن چکیده‌ها
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- تنظیمات محدودیت API پاب‌مد ---
@sleep_and_retry
@limits(calls=3, period=1)
@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4), retry=retry_if_exception_type(requests.exceptions.RequestException))
def _request_with_retry(url, params, headers):
    return requests.get(url, params=params, headers=headers, timeout=15)

def safe_request_get(url, params):
    """یک تابع امن برای ارسال درخواست GET با مدیریت خطا و محدودیت سرعت."""
    try:
        # افزودن شناسه ابزار و ایمیل در صورت وجود در secrets
        tool = st.secrets.get("NCBI_TOOL", None)
        email = st.secrets.get("NCBI_EMAIL", None)
        if tool:
            params = {**params, "tool": tool}
        if email:
            params = {**params, "email": email}

        headers = {"User-Agent": f"research-assistant/1.0 ({email})" if email else "research-assistant/1.0"}

        response = _request_with_retry(url, params, headers)
        response.raise_for_status()
        return response
    except requests.exceptions.Timeout:
        logging.error(f"Timeout while requesting {url}")
        st.warning("PubMed request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error for {url}: {e}")
        st.warning(f"Network error: {e}")
        return None

def fetch_abstracts(pmid_list):
    """
    دریافت چکیده مقالات با استفاده از efetch.
    """
    if not pmid_list:
        return {}

    ids_str = ",".join(pmid_list)
    fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {
        "db": "pubmed",
        "id": ids_str,
        "retmode": "xml",
        "rettype": "abstract"
    }
    
    try:
        response = safe_request_get(fetch_url, fetch_params)
        if response is None:
            return {}
            
        root = ElementTree.fromstring(response.content)
        abstracts = {}
        for article in root.findall('.//PubmedArticle'):
            pmid_node = article.find('.//PMID')
            if pmid_node is None: continue
            pmid = pmid_node.text
            
            # برخی مقالات چندین بخش AbstractText دارند؛ همه را ادغام کنیم
            abstract_nodes = article.findall('.//AbstractText')
            abstract_texts = [node.text for node in abstract_nodes if node is not None and node.text]
            abstracts[pmid] = "\n".join(abstract_texts) if abstract_texts else None
        return abstracts
        
    except Exception as e:
        logging.error(f"Error fetching/parsing abstracts: {e}")
        return {}


def search_pubmed(query, max_results=10):
    """
    جستجوی پاب‌مد، دریافت خلاصه‌ها و چکیده‌ها.
    """
    logging.info(f"Searching PubMed for: {query}")
    
    # --- مرحله ۱: جستجو و دریافت شناسه‌ها (PMIDs) ---
    search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    search_params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    
    search_response = safe_request_get(search_url, search_params)
    if search_response is None: return []
    search_data = search_response.json()
    
    if "esearchresult" not in search_data:
        return []
    
    id_list = search_data["esearchresult"]["idlist"]
    if not id_list:
        st.info("No articles found for this query.")
        return []

    # --- مرحله ۲: دریافت اطلاعات اولیه (Title, Authors) با esummary ---
    summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    summary_params = {"db": "pubmed", "id": ",".join(id_list), "retmode": "json"}
    
    summary_response = safe_request_get(summary_url, summary_params)
    if summary_response is None: return []
    summary_data = summary_response.json()

    if "result" not in summary_data:
        return []

    # --- مرحله ۳: دریافت چکیده‌ها (Abstracts) با efetch ---
    time.sleep(1) # تاخیر قبل از درخواست بعدی
    abstracts = fetch_abstracts(id_list)

    # --- مرحله ۴: ترکیب نتایج ---
    articles = []
    summary_result = summary_data["result"]
    
    for pmid in id_list:
        if pmid not in summary_result: continue
        
        article_data = summary_result[pmid]
        # دسترسی امن‌تر به فهرست نویسندگان
        authors_list = article_data.get("authors", []) or []
        author_names = []
        for author in authors_list:
            name = None
            if isinstance(author, dict):
                name = author.get("name") or author.get("authtype")
            if name:
                author_names.append(name)

        articles.append({
            "pmid": pmid,
            "title": article_data.get("title", "No Title"),
            "authors": ", ".join(author_names),
            "year": article_data.get("pubdate", "N/A").split(" ")[0],
            "journal": article_data.get("source", "N/A"),
            "abstract": abstracts.get(pmid, None) # اضافه کردن چکیده از نتایج efetch
        })
    
    return articles

# --- تابع کش (Caching) ---
@st.cache_data(ttl=timedelta(hours=24)) # کش کردن نتایج برای ۲۴ ساعت
def search_pubmed_cached(query, max_results=10):
    """
    این تابع، فراخوانی اصلی جستجوی پاب‌مد را کش می‌کند.
    """
    return search_pubmed(query, max_results)