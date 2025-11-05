import streamlit as st
import google.generativeai as genai
import logging

# تابع برای مقداردهی اولیه مدل
def init_gemini():
    """
    کلید API را از Hugging Face Secrets می‌خواند و مدل Gemini را مقداردهی می‌کند.
    """
    try:
        # ۱. خواندن کلید به صورت امن از Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)

        # ۲. استفاده از مدل gemini-pro (پایدارتر)
        model = genai.GenerativeModel('gemini-pro')
        return model
    except KeyError:
        # اگر کلید در Secrets تنظیم نشده باشد
        st.error("کلید GEMINI_API_KEY در Hugging Face Secrets تنظیم نشده است.")
        logging.error("GEMINI_API_KEY not found in st.secrets")
        return None
    except Exception as e:
        st.error(f"خطا در اتصال به Gemini: {e}")
        logging.error(f"Gemini configuration error: {e}")
        return None

# تابع برای فراخوانی API (کد کوپایلوت احتمالاً چیزی شبیه این نوشته)
def call_gemini_api(model, prompt):
    """
    یک پرامپت به مدل Gemini ارسال می‌کند.
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