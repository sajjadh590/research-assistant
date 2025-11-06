import streamlit as st
import logging
from modules.gemini_api import analyze_with_gemini_cached
import time

def create_prompt_for_article(article):
    """یک پرامپت دقیق برای تحلیل یک مقاله ایجاد می‌کند."""
    title = article.get('title', 'No Title')
    abstract = article.get('abstract', 'No Abstract')
    
    # پرامپت بهینه‌سازی شده از پرامپت فاز ۲
    return f"""
    You are an expert medical researcher. Analyze the following abstract:
    Title: {title}
    Abstract: {abstract}
    
    Instruction: Based ONLY on this abstract, identify a potential research gap.
    Return a single, concise gap. If no abstract is provided, state that.
    """

def analyze_articles_with_progress(articles, query, delay_seconds: float = 0.5, model_name: str = 'gemini-1.5-pro'):
    """
    مقالات را به صورت ترتیبی (یکی یکی) برای جلوگیری از Rate Limit تحلیل می‌کند.
    """
    results = []
    skipped_count = 0
    total = len(articles)
    
    progress_bar = st.progress(0, text="Starting analysis (sequentially)...")
    
    for i, article in enumerate(articles):
        # بررسی وجود چکیده قبل از ارسال
        if not article.get('abstract'):
            st.warning(f"⚠️ Skipped article (Missing abstract): {article.get('title', 'N/A')[:50]}...")
            skipped_count += 1
            continue # رفتن به مقاله بعدی

        try:
            # ۱. ایجاد پرامپت
            prompt = create_prompt_for_article(article)
            
            # ۲. فراخوانی تابع کش (فقط با 'prompt')
            analysis_text = analyze_with_gemini_cached(prompt, model_name=model_name)
            
            # ۳. بررسی اینکه آیا خود جمنای خطا داده است یا نه
            if analysis_text.startswith("خطا"):
                st.error(f"❌ AI analysis failed for: {article.get('title', 'N/A')[:50]}...")
            else:
                st.success(f"✅ Analysis successful for: {article.get('title', 'N/A')[:50]}...")
                st.markdown(f"> {analysis_text}") # نمایش تحلیل
                results.append({
                    "pmid": article.get('pmid'),
                    "title": article.get('title'),
                    "analysis": analysis_text
                })

        except Exception as e:
            skipped_count += 1
            st.error(f"❌ Critical error analyzing article: {str(e)}")
        
        # آپدیت نوار پیشرفت
        progress_bar.progress((i + 1) / total, text=f"Analyzed {i+1}/{total} articles")
        time.sleep(delay_seconds) # تاخیر قابل تنظیم برای احترام به محدودیت API

    progress_bar.empty()
    st.info(f"Analysis complete. {len(results)} articles analyzed, {skipped_count} skipped.")
    return results