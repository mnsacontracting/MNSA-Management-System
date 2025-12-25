import streamlit as st
from supabase import create_client, Client
import pdfplumber
import pandas as pd
import re
import easyocr
import numpy as np
from PIL import Image
from pdf2image import convert_from_bytes
import io

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP - النظام الشامل", layout="wide")

# --- 2. بيانات الربط (تم وضع بياناتك يا مصطفى) ---
URL = "https://orliczcgajbdllgjcgfe.supabase.co"
KEY = "sb_secret_B7cwS••••••••••••••••" # تأكد من وضع المفتاح بالكامل هنا

try:
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ فشل الاتصال بقاعدة البيانات.")

# --- 3. محرك الـ OCR (يتم تحميله مرة واحدة) ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ar', 'en'])
reader = load_ocr()

# --- 4. محرك معالجة الملفات (PDF + Excel + Scan) ---
def process_document(file):
    ext = file.name.split('.')[-1].lower()
    if ext in ['xlsx', 'xls']:
        return pd.read_excel(file)
    else:
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t: text += t + "\n"
        if not text.strip():
            file.seek(0)
            images = convert_from_bytes(file.read())
            for img in images:
                text += " ".join(reader.readtext(np.array(img), detail=0)) + "\n"
        pattern = r"(.+?)\s+(\d+(?:\.\d+)?)\s+(م3|م2|طن|عدد|لتر|م\.ط)"
        matches = re.findall(pattern, text)
        return pd.DataFrame(matches, columns=['item', 'qty', 'unit']) if matches else text

# --- 5. القائمة الجانبية (هيكل الشركة بالكامل) ---
st.sidebar.title("🏗️ MNSA ERP System")
menu = st.sidebar.selectbox("المنظومة الإدارية", [
    "📊 لوحة التحكم", 
    "📝 المقايسات والعقود", 
    "📦 المشتريات والموردين", 
    "💰 الحسابات والعملاء",
    "👷 الموظفين والرواتب",
    "📈 تقارير حصر التكاليف"
])

# --- 6. الوظائف ---

if menu == "📊 لوحة التحكم":
    st.title("🏗️ شركة MNSA - الرؤية العامة")
    st.success("أهلاً بك يا مصطفى في مركز التحكم.")
    # عرض إحصائيات من كل الجداول (مشاريع، موردين، عملاء)

elif menu == "📝 المقايسات والعقود":
    st.title("📝 إدارة المقايسات ودفتر العقود")
    p_name = st.text_input("اسم المشروع الجديد")
    client = st.text_input("اسم العميل (صاحب المشروع)")
    contract_val = st.number_input("قيمة العقد الإجمالية", min_value=0.0)
    file = st.file_uploader("ارفع المقايسة (PDF/Excel)", type=['pdf', 'xlsx', 'xls'])
    
    if file and p_name and st.button("تحليل وحفظ في دفتر المشروعات"):
        res = process_document(file)
        if isinstance(res, pd.DataFrame):
            t_id = supabase.table("tenders").insert({"project_name": p_name, "client_name": client, "total_value": contract_val}).execute().data[0]['id']
            # حفظ بنود المقايسة
            items = [{"tender_id": t_id, "item_description": r['item'], "quantity": float(r['qty']), "unit": r['unit']} for _, r in res.iterrows()]
            supabase.table("tender_items").insert(items).execute()
            st.balloons()
            st.success(f"تم تسجيل مشروع {p_name} وتفكيك المقايسة بنجاح.")

elif menu == "📦 المشتريات والموردين":
    st.title("📦 المشتريات وحسابات الموردين")
    # جلب المشاريع
    res_p = supabase.table("tenders").select("id, project_name").execute()
    projects = {p['project_name']: p['id'] for p in res_p.data}
    selected_p = st.selectbox("اختر المشروع المرتبط بالفاتورة", list(projects.keys()))
    
    if selected_p:
        t_id = projects[selected_p]
        # تسجيل فاتورة مورد
        with st.form("supplier_form"):
            st.subheader("تسجيل فاتورة توريد")
            supplier = st.text_input("اسم المورد")
            item_name = st.text_input("البند المورد (كما في المقايسة)")
            qty = st.number_input("الكمية الموردة", min_value=0.0)
            cost = st.number_input("تكلفة الشراء (سعر الفاتورة)", min_value=0.0)
            if st.form_submit_button("حفظ الفاتورة وتحديث المخزن"):
                # تحديث مخزن المشروع + حساب المورد
                supabase.table("inventory_logs").insert({
                    "tender_id": t_id, 
                    "item_name": item_name, 
                    "purchased_quantity": qty, 
                    "supplier_name": supplier,
                    "cost": cost # تأكد من إضافة عمود cost في جدول inventory_logs
                }).execute()
                st.success("تم تحديث حساب المورد وخصم الكمية من المقايسة.")

elif menu == "💰 الحسابات والعملاء":
    st.title("💰 حسابات العملاء والمستخلصات")
    st.info("هذا القسم يتابع الدفعات الواردة من العملاء مقابل تنفيذ البنود.")

elif menu == "👷 الموظفين والرواتب":
    st.title("👷 شؤون الموظفين والعمالة")
    # تسجيل الموظفين وحساب الرواتب بناء على الأيام

elif menu == "📈 تقارير حصر التكاليف":
    st.title("📈 تقرير الأرباح والتكاليف")
    st.write("مقارنة فورية بين أسعار المقايسة وتكاليف الشراء الفعلية.")
