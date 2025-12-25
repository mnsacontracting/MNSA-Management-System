

import streamlit as st
from supabase import create_client, Client
import pdfplumber
import pandas as pd
import re
import easyocr
import numpy as np
from PIL import Image
from pdf2image import convert_from_bytes

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP - المتكامل", layout="wide", initial_sidebar_state="expanded")

# --- 2. بيانات الربط ---
# تأكد من وضع بياناتك الصحيحة هنا
URL = "https://orliczcgajbdllgjcgfe.supabase.co".strip() 
KEY = "sb_secret_B7cwS••••••••••••••••".strip()


try:
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من الرابط والمفتاح.")

# --- 3. تحميل محرك الذكاء الاصطناعي (مرة واحدة فقط) ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ar', 'en'])

reader = load_ocr()

# --- 4. دالة معالجة المقايسات (النص والصور) ---
def process_document(file):
    text = ""
    # المحاولة الأولى: قراءة PDF رقمي
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content: text += content + "\n"
    
    # المحاولة الثانية: إذا كان الملف "سكانر"
    if len(text.strip()) < 10:
        st.info("🔄 جاري المسح الضوئي للصور (AI OCR)...")
        file.seek(0)
        images = convert_from_bytes(file.read())
        for img in images:
            img_np = np.array(img)
            results = reader.readtext(img_np, detail=0)
            text += " ".join(results) + "\n"
    
    # تحويل النص إلى جدول بيانات (البحث عن البند والكمية والوحدة)
    pattern = r"(.+?)\s+(\d+(?:\.\d+)?)\s+(م3|م2|طن|عدد|لتر|م\.ط)"
    matches = re.findall(pattern, text)
    if matches:
        return pd.DataFrame(matches, columns=['item', 'qty', 'unit'])
    return text

# --- 5. القائمة الجانبية الموحدة ---
st.sidebar.markdown("<h2 style='text-align: center;'>MNSA ERP</h2>", unsafe_allow_html=True)
menu = st.sidebar.selectbox("انتقل إلى:", ["📊 لوحة التحكم", "📝 رفع المقايسات", "📋 أرشيف المشاريع", "📦 إدارة المخازن"])

# --- 6. محتوى الصفحات ---

if menu == "📊 لوحة التحكم":
    st.title("🏗️ نظام إدارة شركة MNSA")
    st.markdown("---")
    # إحصائيات سريعة من القاعدة
    try:
        tenders_count = supabase.table("tenders").select("id", count="exact").execute()
        st.metric("إجمالي المشاريع المسجلة", tenders_count.count if tenders_count.count else 0)
    except:
        st.info("ارفع أول مقايسة لتظهر الإحصائيات هنا.")

elif menu == "📝 رفع المقايسات":
    st.title("📝 معالجة وحصر المقايسات")
    c1, c2 = st.columns(2)
    with c1:
        p_name = st.text_input("اسم المشروع/المناقصة")
    with c2:
        c_name = st.text_input("جهة الإسناد")
        
    uploaded_file = st.file_uploader("اختر ملف المقايسة (PDF)", type=['pdf'])
    
    if uploaded_file and p_name:
        if st.button("بدء التحليل والحفظ"):
            with st.spinner("ذكاء MNSA يحلل الملف الآن..."):
                result = process_document(uploaded_file)
                
                if isinstance(result, pd.DataFrame):
                    st.success(f"تم استخراج {len(result)} بند بنجاح!")
                    st.dataframe(result, use_container_width=True)
                    
                    # حفظ في Supabase
                    t_res = supabase.table("tenders").insert({"project_name": p_name, "client_name": c_name}).execute()
                    t_id = t_res.data[0]['id']
                    
                    items_data = []
                    for _, row in result.iterrows():
                        items_data.append({
                            "tender_id": t_id,
                            "item_description": row['item'],
                            "quantity": float(row['qty']),
                            "unit": row['unit']
                        })
                    supabase.table("tender_items").insert(items_data).execute()
                    st.balloons()
                    st.success("✅ تم حفظ المشروع والبنود في قاعدة البيانات.")
                else:
                    st.warning("تم قراءة نص ولكن لم يتم تنظيم جدول. محتوى النص:")
                    st.text(result)

elif menu == "📋 أرشيف المشاريع":
    st.title("📋 سجل المشاريع والكميات")
    try:
        res = supabase.table("tenders").select("*, tender_items(*)").execute()
        if res.data:
            for p in res.data:
                with st.expander(f"📌 {p['project_name']} - {p['client_name']}"):
                    st.write(f"تاريخ الإضافة: {p['created_at']}")
                    if p['tender_items']:
                        st.table(pd.DataFrame(p['tender_items'])[['item_description', 'unit', 'quantity']])
        else:
            st.info("لا توجد مشاريع مسجلة حالياً.")
    except Exception as e:
        st.error(f"حدث خطأ أثناء جلب البيانات: {e}")

elif menu == "📦 إدارة المخازن":
    st.title("📦 المشتريات والمخازن")
    st.info("هذا القسم جاهز للربط مع ملفات الإكسل الخاصة بالمشتريات في الخطوة القادمة.")




