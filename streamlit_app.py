import streamlit as st
from supabase import create_client, Client
import pdfplumber
import pandas as pd

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP - Fixed Edition", layout="wide")

# --- 2. بيانات الربط ---
# يا مصطفى تأكد أنك تمسح أي مسافات زائدة قبل أو بعد الرابط والمفتاح
URL = "https://orliczcgajbdllgjcgfe.supabase.co".strip() 
KEY = "sb_secret_B7cwSIGnf_rKz48VKPaRzw_iVePq1CL".strip()

try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error(f"خطأ في الاتصال: {e}")

# --- 3. دالة قراءة الـ PDF (محسنة للعربية) ---
def extract_data(file):
    try:
        with pdfplumber.open(file) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            return full_text if full_text.strip() else "لم نجد نصاً داخل الملف، قد يكون الملف عبارة عن صور (Scan)."
    except Exception as e:
        return f"حدث خطأ أثناء قراءة الملف: {e}"

# --- 4. القائمة الجانبية ---
st.sidebar.title("🏗️ MNSA ERP")
menu = st.sidebar.radio("القائمة", ["📊 لوحة التحكم", "📝 المناقصات والـ PDF", "📦 المخازن"])

# --- 5. محتوى الصفحات ---
if menu == "📊 لوحة التحكم":
    st.title("🏗️ نظام إدارة شركة MNSA")
    st.success("الآن النظام جاهز للعمل يا مصطفى.")

elif menu == "📝 المناقصات والـ PDF":
    st.title("📝 قراءة ملفات المناقصات")
    uploaded_file = st.file_uploader("ارفع ملف PDF (تأكد أن الملف يحتوي على نص وليس صور فقط)", type=['pdf'])
    
    if uploaded_file:
        with st.spinner("جاري قراءة محتوى الملف..."):
            result = extract_data(uploaded_file)
            st.success("تمت المعالجة!")
            
            # عرض النص المستخرج
            content_box = st.text_area("محتوى الملف المستخرج:", result, height=300)
            
            # حفظ البيانات (مع تنظيف الحروف الخاصة)
            if st.button("حفظ اسم المناقصة في القاعدة"):
                # نرسل بيانات بسيطة أولاً للتأكد من نجاح الاتصال
                try:
                    data = {"title": "مناقصة جديدة", "status": "تحت الدراسة"}
                    supabase.table("tenders").insert(data).execute()
                    st.success("✅ تم الحفظ في قاعدة البيانات بنجاح!")
                except Exception as e:
                    st.error(f"❌ خطأ أثناء الحفظ: {e}")

elif menu == "📦 المخازن":
    st.title("📦 قسم المخازن")
    st.info("هذا القسم سيتم تفعيله بعد ضبط المناقصات.")
