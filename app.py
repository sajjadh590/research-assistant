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

def search_pubmed(query, max_results=10):
    """مقالات مرتبط با یک موضوع را در PubMed جستجو می‌کند."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    search_url = f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax={max_results}&sort=relevance&retmode=json"

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
        for article_xml in root.findall('.//PubmedArticle'):
            # --- استخراج اطلاعات کامل مقاله ---
            pmid_element = article_xml.find('.//PMID')
            pmid = pmid_element.text if pmid_element is not None else ""

            title_element = article_xml.find('.//ArticleTitle')
            title = title_element.text if title_element is not None else "No Title Available"

            abstract_element = article_xml.find('.//AbstractText')
            abstract = abstract_element.text if abstract_element is not None else "No Abstract Available"

            author_elements = article_xml.findall('.//AuthorList/Author')
            authors = []
            for author in author_elements:
                last_name = author.find('LastName')
                fore_name = author.find('ForeName')
                if last_name is not None and fore_name is not None:
                    authors.append(f"{last_name.text}, {fore_name.text}")
            authors_str = " and ".join(authors)

            journal_element = article_xml.find('.//Journal/Title')
            journal = journal_element.text if journal_element is not None else "N/A"

            year_element = article_xml.find('.//PubDate/Year')
            year = year_element.text if year_element is not None else "N/A"

            articles.append({
                'pmid': pmid,
                'title': title,
                'abstract': abstract,
                'authors': authors_str,
                'journal': journal,
                'year': year
            })

        return articles

    except requests.exceptions.RequestException as e:
        st.error(f"خطا در ارتباط با PubMed: {e}")
        return []
    except ET.ParseError as e:
        st.error(f"خطا در پارس کردن پاسخ XML از PubMed: {e}")
        return []

st.title("🔬 دستیار پژوهشی هوشمند")

# ابزارهای ورودی کاربر در سایدبار
with st.sidebar:
    st.header("تنظیمات جستجو")
    topic = st.text_input("موضوع تحقیق خود را وارد کنید:", placeholder="مثلاً: New treatments for Alzheimer's")
    num_articles = st.slider("تعداد مقالات:", min_value=5, max_value=100, value=10, step=5)
    output_language = st.selectbox("زبان خروجی تحلیل:", ("فارسی", "English", "Deutsch", "Français", "العربية"))

if topic:
    st.write(f"در حال جستجو برای {num_articles} مقاله در مورد: {topic}")
    
    with st.spinner("در حال جستجو در PubMed..."):
        articles = search_pubmed(topic, max_results=num_articles)

    if articles:
        st.success(f"تعداد {len(articles)} مقاله یافت شد.")
        st.session_state.articles = articles

        # --- بخش مدیریت منابع ---
        def generate_bibtex(articles_list):
            bib_entries = []
            for article in articles_list:
                # Sanitize characters for BibTeX
                title = article['title'].replace('{', '').replace('}', '')
                authors = article['authors'].replace('{', '').replace('}', '')

                bib_entry = (
                    f"@article{{{article['pmid']},\n"
                    f"  author    = {{{authors}}},\n"
                    f"  title     = {{{title}}},\n"
                    f"  journal   = {{{article['journal']}}},\n"
                    f"  year      = {{{article['year']}}},\n"
                    f"  pmid      = {{{article['pmid']}}}\n"
                    f"}}"
                )
                bib_entries.append(bib_entry)
            return "\n\n".join(bib_entries)

        bibtex_str = generate_bibtex(articles)
        st.download_button(
            label="دانلود فایل BibTeX",
            data=bibtex_str,
            file_name=f"{topic.replace(' ', '_')}_references.bib",
            mime="application/x-bibtex",
        )
        # --- پایان بخش مدیریت منابع ---

        for i, article in enumerate(articles):
            with st.expander(f"مقاله {i+1}: {article['title']}"):
                st.markdown(f"**نویسندگان:** {article['authors']}")
                st.markdown(f"**ژورنال:** {article['journal']} ({article['year']})")
                st.markdown(f"**چکیده:**\n{article['abstract']}")

        st.markdown("---")
        st.subheader("ابزارهای تحلیل پیشرفته")

        # ایجاد چهار ستون برای دکمه‌ها
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("یافتن گپ‌های تحقیقاتی"):
                with st.spinner("در حال تحلیل گپ‌های تحقیقاتی..."):
                    abstracts = [article['abstract'] for article in articles if article['abstract'] != "No Abstract"]
                    if not abstracts:
                        st.warning("هیچ خلاصه‌ای برای تحلیل یافت نشد.")
                    else:
                        prompt = f"Based on the following abstracts on the topic '{topic}', identify and summarize potential research gaps. Please present the gaps as a bulleted list.\n\n**Abstracts:**\n" + "\n\n".join(abstracts) + f"\n\n**IMPORTANT: The final output must be in {output_language}.**"
                        response = model.generate_content(prompt)
                        st.subheader(f"گپ‌های تحقیقاتی شناسایی‌شده (به زبان {output_language}):")
                        st.markdown(response.text)

        with col2:
            if st.button("نوشتن پیش‌نویس مرور ادبیات"):
                with st.spinner("در حال نوشتن پیش‌نویس مرور ادبیات..."):
                    abstracts = [article['abstract'] for article in articles if article['abstract'] != "No Abstract"]
                    if not abstracts:
                        st.warning("هیچ خلاصه‌ای برای نوشتن پیش‌نویس یافت نشد.")
                    else:
                        prompt = f"Write a literature review draft based on the following abstracts on the topic '{topic}'. The draft should be well-structured, coherent, and synthesize the key findings from the articles. It should include an introduction, thematic sections, and a conclusion identifying the main research gaps.\n\n**Abstracts:**\n" + "\n\n".join(abstracts) + f"\n\n**IMPORTANT: The final output must be in {output_language}.**"
                        response = model.generate_content(prompt)
                        st.subheader(f"پیش‌نویس مرور ادبیات (به زبان {output_language}):")
                        st.markdown(response.text)

        with col3:
            # بخش ساخت پروپوزال
            with st.expander("تنظیمات ساخت پروپوزال"):
                default_proposal_format = """
1. **عنوان تحقیق (Title)**:
2. **بیان مسئله (Problem Statement)**:
3. **اهمیت و ضرورت تحقیق (Significance of the Study)**:
4. **اهداف تحقیق (Research Objectives)**:
   - هدف اصلی
   - اهداف فرعی
5. **سوالات تحقیق (Research Questions)**:
6. **روش تحقیق (Methodology)**:
7. **جامعه و نمونه آماری (Population and Sample)**:
8. **ابزارهای گردآوری داده‌ها (Data Collection Tools)**:
9. **محدودیت‌های تحقیق (Limitations)**:
"""
                proposal_format = st.text_area("فرمت پروپوزال خود را اینجا وارد یا ویرایش کنید:", value=default_proposal_format, height=300)

            if st.button("ساخت پروپوزال"):
                with st.spinner("در حال ساخت پروپوزال..."):
                    abstracts = [article['abstract'] for article in articles if article['abstract'] != "No Abstract"]
                    if not abstracts:
                        st.warning("هیچ خلاصه‌ای برای ساخت پروپوزال یافت نشد.")
                    else:
                        prompt = f"""
As an expert academic assistant, generate a comprehensive research proposal on the topic '{topic}'.
Use the information from the following article abstracts to fill out each section of the proposal.
The proposal must strictly follow the provided format.

**Article Abstracts:**
{"\n\n".join(abstracts)}

**Proposal Format to Follow:**
{proposal_format}

**IMPORTANT: The final output must be in {output_language}. If the proposal format is in a different language, translate the generated content to the language of the format.**
"""
                        response = model.generate_content(prompt)
                        st.subheader(f"پیش‌نویس پروپوزال تحقیق (به زبان {output_language}):")
                        st.markdown(response.text)

        with col4:
            if st.button("تحلیل موضوعی پیشرفته"):
                with st.spinner("در حال انجام تحلیل موضوعی پیشرفته..."):
                    abstracts = [f"Title: {a['title']}\nAbstract: {a['abstract']}" for a in articles if a['abstract'] != "No Abstract"]
                    if not abstracts:
                        st.warning("هیچ خلاصه‌ای برای تحلیل یافت نشد.")
                    else:
                        prompt = f"""
As a senior researcher, perform an in-depth thematic analysis of the following article abstracts on the topic '{topic}'.
Based on your analysis, provide a comprehensive report that includes:
1.  **Main Research Themes**: Identify and describe the dominant themes or sub-topics discussed across the articles.
2.  **Common Methodologies**: Summarize the most frequently used research methods and approaches.
3.  **Key Debates and Discussions**: Highlight any conflicting findings, ongoing debates, or key discussions in the field.
4.  **Prominent Authors/Groups**: If possible, identify any authors or research groups that appear frequently.

**Article Abstracts:**
{"\n\n---\n\n".join(abstracts)}

**IMPORTANT: The final output must be in {output_language}.**
"""
                        response = model.generate_content(prompt)
                        st.subheader(f"تحلیل موضوعی پیشرفته (به زبان {output_language}):")
                        st.markdown(response.text)
    else:
        st.warning("هیچ مقاله‌ای یافت نشد.")