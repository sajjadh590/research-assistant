import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import time
import json

# --- بخش جدید: تنظیمات صفحه و دریافت کلید ---
# این خط سایدبار را به صورت پیش‌فرض باز نگه می‌دارد
st.set_page_config(initial_sidebar_state="expanded")

# تلاش برای خواندن کلید API از Hugging Face Secrets
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except (KeyError, FileNotFoundError):
    # اگر کلید در Secrets نبود، آن را از کاربر دریافت کن
    api_key = st.sidebar.text_input("کلید API گوگل (Gemini)", type="password")

# بررسی می‌کنیم که آیا کلید API در دسترس است یا نه
if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
else:
    st.info("لطفاً برای فعال شدن برنامه، کلید API گوگل خود را (با نام GOOGLE_API_KEY) در بخش Secrets این Space تنظیم کرده و یا آن را در نوار کناری وارد کنید.")
    st.stop()

# --- بقیه کد شما از اینجا شروع می‌شود ---

def search_pubmed(query):
    """مقالات مرتبط با یک موضوع را در PubMed جستجو می‌کند."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax=5&sort=relevance&retmode=json"

    try:
        search_response = requests.get(search_url)
        search_data = search_response.json()

        if "esearchresult" not in search_data or not search_data["esearchresult"]["idlist"]:
            return []

        id_list = ",".join(search_data["esearchresult"]["idlist"])

        fetch_url = f"{base_url}efetch.fcgi?db=pubmed&id={id_list}&rettype=abstract&retmode=xml"
        fetch_response = requests.get(fetch_url)

        import xml.etree.ElementTree as ET

        articles = []
        root = ET.fromstring(fetch_response.content)
        for article in root.findall('.//PubmedArticle'):
            title_element = article.find('.//ArticleTitle')
            abstract_element = article.find('.//AbstractText')

            title = title_element.text if title_element is not None else "No Title"
            abstract = abstract_element.text if abstract_element is not None else "No Abstract"

            articles.append({'title': title, 'abstract': abstract})

        return articles

    except requests.exceptions.RequestException as e:
        st.error(f"خطا در ارتباط با PubMed: {e}")
        return []
    except ET.ParseError as e:
        st.error(f"خطا در پارس کردن پاسخ XML از PubMed: {e}")
        return []

st.title("🔬 دستیار پژوهشی هوشمند")
topic = st.text_input("موضوع تحقیق خود را وارد کنید:")

if topic:
    st.write(f"در حال جستجو برای: {topic}")
    
    with st.spinner("در حال جستجو در PubMed..."):
        articles = search_pubmed(topic)

    if articles:
        st.success(f"تعداد {len(articles)} مقاله یافت شد.")
        st.session_state.articles = articles

        for i, article in enumerate(articles):
            with st.expander(f"مقاله {i+1}: {article['title']}"):
                st.markdown(article['abstract'])

        # اینجا می‌توانید دکمه‌های تحلیل را اضافه کنید
        if st.button("یافتن گپ‌های تحقیقاتی"):
            with st.spinner("در حال تحلیل..."):
                abstracts = [article['abstract'] for article in articles if article['abstract'] != "No Abstract"]

                if not abstracts:
                    st.warning("هیچ خلاصه‌ای برای تحلیل یافت نشد.")
                    st.stop()

                prompt = f"Based on the following abstracts on the topic '{topic}', identify and summarize potential research gaps. Please present the gaps as a bulleted list:\n\n" + "\n\n".join(abstracts)
                response = model.generate_content(prompt)
                st.markdown("---")
                st.subheader("گپ‌های تحقیقاتی شناسایی‌شده:")
                st.markdown(response.text)
    else:
        st.warning("هیچ مقاله‌ای یافت نشد.")