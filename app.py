import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import time
import json

# --- بخش جدید: تنظیمات صفحه و دریافت کلید ---
# این خط سایدبار را به صورت پیش‌فرض باز نگه می‌دارد
st.set_page_config(initial_sidebar_state="expanded")

# ایجاد یک کادر در سایدبار برای دریافت کلید
api_key = st.sidebar.text_input("کلید API گوگل (Gemini)", type="password")

# بررسی می‌کنیم که آیا کلید وارد شده است یا نه
if api_key:
    # اگر کلید بود، هوش مصنوعی را فعال کن
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
else:
    # اگر کلید نبود، به کاربر پیام بده و برنامه را متوقف کن
    st.info("لطفاً برای فعال شدن برنامه، کلید API خود را در نوار کناری وارد کنید.")
    st.stop()

# --- بقیه کد شما از اینجا شروع می‌شود ---

st.title("🔬 دستیار پژوهشی هوشمند")
topic = st.text_input("موضوع تحقیق خود را وارد کنید:")

if topic:
    # (بقیه منطق برنامه شما که جستجو را انجام می‌دهد و...)
    # این بخش برای نمونه ساده شده است
    st.write(f"در حال جستجو برای: {topic}")
    
    try:
        # اینجا باید کد جستجوی پاب‌مد شما بیاید
        # برای سادگی، فعلا یک پیام نمایش می‌دهیم
        st.success("جستجو با موفقیت انجام شد (این یک پیام تست است).")

        # اینجا می‌توانید دکمه‌های تحلیل را اضافه کنید
        if st.button("یافتن گپ‌های تحقیقاتی"):
            with st.spinner("در حال تحلیل..."):
                prompt = f"Find research gaps for the topic: {topic}"
                response = model.generate_content(prompt)
                st.markdown(response.text)

    except Exception as e:
        st.error(f"خطایی رخ داد: {e}")