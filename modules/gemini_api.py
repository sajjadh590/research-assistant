import streamlit as st
import google.generativeai as genai
import logging
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_exponential
import os

# --- تابع init_gemini (برای بارگذاری امن مدل) ---
# این تابع در هر بار که کش (cache) خالی باشد، یک بار اجرا می‌شود
def init_gemini(model_name: str = 'gemini-1.5-pro'):
    """
    کلید API را از Streamlit secrets می‌خواند و مدل Gemini را مقداردهی می‌کند.
    """
    try:
        # 1) Try Streamlit secrets, 2) fallback to env var
        api_key = st.secrets.get("GEMINI_API_KEY", None)
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise KeyError("GEMINI_API_KEY not found in secrets or environment")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        logging.info("Gemini model initialized successfully.")
        return model
    except KeyError:
        st.error("کلید GEMINI_API_KEY یافت نشد. آن را در Streamlit secrets یا متغیر محیطی تنظیم کنید.")
        logging.error("GEMINI_API_KEY not found in st.secrets")
        return None
    except Exception as e:
        st.error(f"خطا در اتصال به Gemini: {e}")
        logging.error(f"Gemini configuration error: {e}")
        return None

# --- تابع call_gemini_api (فراخوانی واقعی API) ---
@retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4))
def _generate_with_retry(model, prompt: str) -> str:
    response = model.generate_content(prompt)
    return response.text

def call_gemini_api(model, prompt):
    """
    یک پرامپت به مدل Gemini ارسال می‌کند. (این تابع کش نمی‌شود)
    """
    if model is None:
        logging.error("Model is None, cannot generate content.")
        return "خطا: مدل Gemini به درستی بارگذاری نشده است."
        
    try:
        return _generate_with_retry(model, prompt)
    except Exception as e:
        st.error(f"❌ AI analysis failed: {str(e)}")
        logging.error(f"Gemini API error: {e}", exc_info=True)
        return "خطا در تحلیل هوش مصنوعی."

# --- Key validation helper ---
def validate_gemini_key(model_name: str = 'gemini-1.5-pro'):
    """
    تلاش برای مقداردهی مدل و یک فراخوانی سبک برای اعتبارسنجی کلید.
    خروجی: (ok: bool, err: Optional[str])
    """
    try:
        model = init_gemini(model_name)
        if model is None:
            return False, "Model initialization failed."
        try:
            # فراخوانی بسیار سبک؛ اگر خطایی باشد همانجا بازمی‌گردد
            _ = model.generate_content("ping")
            return True, None
        except Exception as e:
            logging.error(f"Gemini validation call failed: {e}", exc_info=True)
            return False, str(e)
    except Exception as e:
        logging.error(f"Gemini key validation error: {e}", exc_info=True)
        return False, str(e)

# ---!!! تابع اصلاح شده (این همان چیزی است که خطا می‌داد) !!!---
@st.cache_data(ttl=timedelta(days=7))  # کش کردن نتایج برای ۷ روز
def analyze_with_gemini_cached(prompt: str, model_name: str = 'gemini-1.5-pro'):
    """
    این تابع، فراخوانی اصلی API را کش می‌کند.
    کش با توجه به نام مدل نیز تفکیک می‌شود.
    """
    logging.info("Cache miss. Calling Gemini API.")
    # ۱. مدل را مقداردهی اولیه کن
    model = init_gemini(model_name)
    
    # ۲. تابع واقعی را با مدل و پرامپت صدا بزن
    return call_gemini_api(model, prompt)