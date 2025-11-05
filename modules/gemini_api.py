import streamlit as st
import google.generativeai as genai
import logging
from datetime import timedelta

# --- تابع init_gemini (برای بارگذاری امن مدل) ---
# این تابع در هر بار که کش (cache) خالی باشد، یک بار اجرا می‌شود
def init_gemini():
    """
    کلید API را از Hugging Face Secrets می‌خواند و مدل Gemini را مقداردهی می‌کند.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        logging.info("Gemini model initialized successfully.")
        return model
    except KeyError:
        st.error("کلید GEMINI_API_KEY در Hugging Face Secrets تنظیم نشده است.")
        logging.error("GEMINI_API_KEY not found in st.secrets")
        return None
    except Exception as e:
        st.error(f"خطا در اتصال به Gemini: {e}")
        logging.error(f"Gemini configuration error: {e}")
        return None

# --- تابع call_gemini_api (فراخوانی واقعی API) ---
def call_gemini_api(model, prompt):
    """
    یک پرامپت به مدل Gemini ارسال می‌کند. (این تابع کش نمی‌شود)
    """
    if model is None:
        logging.error("Model is None, cannot generate content.")
        return "خطا: مدل Gemini به درستی بارگذاری نشده است."
        
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ AI analysis failed: {str(e)}")
        logging.error(f"Gemini API error: {e}", exc_info=True)
        return "خطا در تحلیل هوش مصنوعی."

# ---!!! تابع اصلاح شده (این همان چیزی است که خطا می‌داد) !!!---
@st.cache_data(ttl=timedelta(days=7))  # کش کردن نتایج برای ۷ روز
def analyze_with_gemini_cached(prompt):
    """
    این تابع، فراخوانی اصلی API را کش می‌کند.
    حالا فقط 'prompt' را به عنوان ورودی می‌گیرد و خودش مدل را مدیریت می‌کند.
    """
    logging.info("Cache miss. Calling Gemini API.")
    # ۱. مدل را مقداردهی اولیه کن
    model = init_gemini()
    
    # ۲. تابع واقعی را با مدل و پرامپت صدا بزن
    return call_gemini_api(model, prompt)