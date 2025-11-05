import streamlit as st
import logging
from modules.gemini_api import analyze_with_gemini_cached # این تابع حالا فقط 1 ورودی می‌گیرد
from concurrent.futures import ThreadPoolExecutor, as_completed

def create_prompt_for_article(article):
    """یک پرامپت دقیق برای تحلیل یک مقاله ایجاد می‌کند."""
    title = article.get('title', 'No Title')
    abstract = article.get('abstract', 'No Abstract')
    
    return f"""
    Analyze the following abstract to find research gaps.
    Title: {title}
    Abstract: {abstract}
    
    Instruction: Based ONLY on this abstract, identify a potential research gap.
    Return a single, concise gap.
    """

def analyze_article(article):
    """یک مقاله را دریافت و تحلیل می‌کند."""
    if not article.get('abstract'):
        logging.warning(f"Skipping article {article.get('pmid', 'N/A')}: Missing abstract")
        raise ValueError("Missing abstract") # این باعث می‌شود در UI پیام "skipped" نشان داده شود

    # ۱. ایجاد پرامپت
    prompt = create_prompt_for_article(article)
    
    # ۲. فراخوانی تابع کش (فقط با 'prompt')
    # !!! این خط اصلاح شده است !!!
    analysis = analyze_with_gemini_cached(prompt)
    
    return {
        "pmid": article.get('pmid'),
        "title": article.get('title'),
        "analysis": analysis
    }

def analyze_articles_with_progress(articles, query):
    """
    مقالات را با استفاده از پردازش موازی و نوار پیشرفت تحلیل می‌کند.
    """
    results = []
    skipped_count = 0
    total = len(articles)
    
    progress_bar = st.progress(0, text="Starting analysis...")
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_article = {executor.submit(analyze_article, article): article for article in articles}
        
        for i, future in enumerate(as_completed(future_to_article)):
            try:
                result = future.result()
                results.append(result)
                st.success(f"✅ Analysis successful for: {result['title'][:50]}...")
                st.markdown(f"> {result['analysis']}") # نمایش تحلیل
                
            except ValueError as e: # خطایی که برای چکیده خالی تعریف کردیم
                skipped_count += 1
                st.warning(f"⚠️ Skipped article: {str(e)}")
            except Exception as e:
                skipped_count += 1
                st.error(f"❌ AI analysis failed: {str(e)}")
            
            # آپدیت نوار پیشرفت
            progress_bar.progress((i + 1) / total, text=f"Analyzed {i+1}/{total} articles")

    progress_bar.empty()
    st.info(f"Analysis complete. {len(results)} articles analyzed, {skipped_count} skipped.")
    return results