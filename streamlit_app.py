import streamlit as st
from supabase import create_client, Client
import pdfplumber
import pandas as pd
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP - AI Edition", layout="wide")

# --- 2. بيانات الربط (تأكد من وضع بياناتك هنا) ---
URL = "sb_publishable_LmVQgvh1ActBvEOPS54Zgw_anYZN6lH"
KEY = "sb_secret_B7cwSIGnf_rKz48VKPaRzw_iVePq1CL"

try:
    supabase: Client = create_client(URL, KEY)
except:
    st.error("خطأ في الاتصال بقاعدة البيانات")

# --- دالة قراءة الـ PDF الذكية ---
def extract_data_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        full_text = ""
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text

# --- 3. القائمة الجانبية ---
st.sidebar.markdown("<h1 style='text-align: center; color: #007bff;'>MNSA ERP v1.1</h1>", unsafe_allow_html=True)
menu = st.sidebar.radio("القائمة الرئيسية", ["📊 لوحة التحكم", "📝 المناقصات الذكية", "📦 المخازن", "👥 الموظفين"])

# --- 4. محتوى الصفحات ---

if menu == "📊 لوحة التحكم":
    st.title("🏗️ لوحة تحكم شركة MNSA")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("المناقصات المسجلة", "جاري التحديث..")
    c2.metric("إجمالي بنود الحصر", "جاري التحديث..")
    c3.metric("تنبيهات النظام", "لا توجد")

elif menu == "📝 المناقصات الذكية":
    st.title("📝 رفع وقراءة المناقصات بالذكاء الاصطناعي")
    
    tab1, tab2 = st.tabs(["رفع ملف جديد", "عرض الأرشيف"])
    
    with tab1:
        with st.expander("خطوة 1: رفع ملف المقايسة (PDF)"):
            uploaded_file = st.file_uploader("اختر ملف PDF للمناقصة", type=['pdf'])
            
            if uploaded_file is not None:
                with st.spinner("جاري قراءة الملف وتحليل البيانات..."):
                    text_content = extract_data_from_pdf(uploaded_file)
                    st.success("تمت قراءة الملف بنجاح!")
                    
                    # عرض عينة من النص المستخرج
                    st.text_area("النص المستخرج من الملف:", text_content[:500] + "...", height=150)
        
        with st.form("tender_details"):
            st.subheader("خطوة 2: تأكيد البيانات الأساسية")
            t_name = st.text_input("اسم المشروع (تم استخراجه)")
            t_client = st.text_input("جهة الإسناد")
            t_value = st.number_input("القيمة التقديرية", min_value=0)
            
            if st.form_submit_button("حفظ المناقصة والبدء في حصر البنود"):
                if t_name:
                    data = {"title": t_name, "client": t_client, "insurance_amount": t_value}
                    res = supabase.table("tenders").insert(data).execute()
                    st.balloons()
                    st.success(f"تم تسجيل {t_name} في النظام!")
                else:
                    st.warning("يرجى التأكد من اسم المناقصة")

elif menu == "📦 المخازن":
    st.title("📦 إدارة المخازن والمشتريات")
    st.info("هنا سيتم رفع ملفات الإكسل لمقارنتها بالبنود التي استخرجناها من الـ PDF.")

# --- التذييل ---
st.sidebar.markdown("---")
st.sidebar.caption("MNSA Contracting | AI Powered")
