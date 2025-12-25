import streamlit as st
from supabase import create_client, Client
import pdfplumber
import pandas as pd

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP - AI Edition", layout="wide")

# --- 2. بيانات الربط (انتبه لهذه النقطة يا مصطفى) ---
# تأكد أن الرابط يبدأ بـ https:// وينتهي بـ .co
# وتأكد أن المفتاح طويل جداً
URL = "https://orliczcgajbdllgjcgfe.supabase.co" 
KEY = "sb_secret_B7cwS••••••••••••••••"


# محاولة الربط بالقاعدة
try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"خطأ في الرابط أو المفتاح: {e}")

# --- 3. دالة قراءة الـ PDF ---
def extract_data(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

# --- 4. القائمة الجانبية ---
st.sidebar.title("🏗️ MNSA ERP")
menu = st.sidebar.radio("القائمة", ["📊 لوحة التحكم", "📝 المناقصات والـ PDF", "📦 المخازن"])

# --- 5. محتوى الصفحات ---
if menu == "📊 لوحة التحكم":
    st.title("🏗️ نظام إدارة شركة MNSA")
    st.info("مرحباً بك يا مصطفى في لوحة التحكم الخاصة بشركتك.")

elif menu == "📝 المناقصات والـ PDF":
    st.title("📝 قراءة ملفات المناقصات")
    uploaded_file = st.file_uploader("ارفع ملف PDF", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("جاري القراءة..."):
            result = extract_data(uploaded_file)
            st.success("تمت القراءة!")
            st.text_area("محتوى الملف:", result, height=200)
            
            # زر للحفظ في القاعدة
            if st.button("حفظ اسم المناقصة في القاعدة"):
                data = {"title": "مناقصة جديدة من ملف", "status": "تحت الدراسة"}
                supabase.table("tenders").insert(data).execute()
                st.success("تم الحفظ!")

elif menu == "📦 المخازن":
    st.title("📦 قسم المخازن")
    st.write("هنا سنقوم بمقارنة الكميات لاحقاً.")


   
