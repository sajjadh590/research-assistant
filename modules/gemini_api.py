import streamlit as st
import google.generativeai as genai
import logging
from datetime import timedelta  # این را برای کش (cache) نیاز داریم

# --- تابع init_gemini (برای بارگذاری امن مدل) ---
def init_gemini():
    """
    کلید API را از Hugging Face Secrets می‌خواند و مدل Gemini را مقداردهی می‌کند.
    """
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
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
        return "خطا: مدل Gemini به درستی بارگذاری نشده است."
        
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ AI analysis failed: {str(e)}")
        logging.error(f"Gemini API error: {e}", exc_info=True)
        return "خطا در تحلیل هوش مصنوعی."

# ---!!! تابع گمشده (این همان چیزی است که خطا می‌داد) !!!---
@st.cache_data(ttl=timedelta(days=7))  # کش کردن نتایج برای ۷ روز
def analyze_with_gemini_cached(model, prompt):
    """
    این تابع، فراخوانی اصلی API را کش می‌کند تا از تماس‌های تکراری جلوگیری شود.
    app.py به دنبال این تابع می‌گشت.
    """
    # فراخوانی تابع واقعی که در بالا تعریف شد
    return call_gemini_api(model, prompt)