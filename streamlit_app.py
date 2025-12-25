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
st.set_page_config(page_title="MNSA ERP - النظام المتكامل", layout="wide")

# --- 2. بيانات الربط (ضع بياناتك هنا) ---
URL = "https://orliczcgajbdllgjcgfe.supabase.co".strip()
KEY = "sb_secret_B7cwS••••••••••••••••".strip()


try:
    supabase: Client = create_client(URL, KEY)
except:
    st.error("⚠️ فشل الاتصال بقاعدة البيانات. تأكد من الرابط والمفتاح.")

# --- 3. تحميل محرك OCR (للعربية والإنجليزية) ---
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['ar', 'en'])

reader = load_ocr()

# --- 4. محرك المعالجة الشامل (Excel + PDF + Scan) ---
def process_document(file):
    file_extension = file.name.split('.')[-1].lower()
    
    # أولاً: معالجة ملفات الإكسل
    if file_extension in ['xlsx', 'xls']:
        df_excel = pd.read_excel(file)
        # توحيد أسماء الأعمدة (توقع أسماء قريبة من: بند، كمية، وحدة)
        return df_excel

    # ثانياً: معالجة ملفات الـ PDF والصور
    else:
        text = ""
        # محاولة قراءة النص الرقمي أولاً
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content: text += content + "\n"
        
        # إذا كان الملف "سكانر" (لا يوجد نص مستخرج)
        if len(text.strip()) < 10:
            st.info("🔄 جاري المسح الضوئي الذكي (AI OCR)...")
            file.seek(0)
            images = convert_from_bytes(file.read())
            for img in images:
                img_np = np.array(img)
                results = reader.readtext(img_np, detail=0)
                text += " ".join(results) + "\n"
        
        # تفكيك النص لجدول باستخدام الأنماط (Regex)
        pattern = r"(.+?)\s+(\d+(?:\.\d+)?)\s+(م3|م2|طن|عدد|لتر|م\.ط)"
        matches = re.findall(pattern, text)
        if matches:
            return pd.DataFrame(matches, columns=['item', 'qty', 'unit'])
        return text

# --- 5. القائمة الجانبية ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4300/4300058.png", width=100)
st.sidebar.title("🏗️ MNSA ERP System")
menu = st.sidebar.radio("انتقل إلى:", ["📊 لوحة التحكم", "📝 رفع المقايسات", "📋 أرشيف المشاريع", "📦 إدارة المخازن"])

# --- 6. محتوى الصفحات ---

if menu == "📊 لوحة التحكم":
    st.title("🏗️ نظام إدارة شركة MNSA للمقاولات")
    st.markdown("---")
    st.success("أهلاً بك يا مصطفى. النظام يعمل بكامل طاقته الآن.")
    
    # إحصائيات سريعة
    try:
        t_count = supabase.table("tenders").select("id", count="exact").execute()
        st.metric("عدد المشاريع المسجلة", t_count.count if t_count.count else 0)
    except:
        st.write("ابدأ برفع أول مقايسة لتفعيل الإحصائيات.")

elif menu == "📝 رفع المقايسات":
    st.title("📝 تسجيل وحصر مقايسة جديدة")
    col1, col2 = st.columns(2)
    with col1: p_name = st.text_input("اسم المشروع")
    with col2: c_name = st.text_input("جهة الإسناد")
    
    uploaded_file = st.file_uploader("ارفع الملف (PDF أو Excel)", type=['pdf', 'xlsx', 'xls'])
    
    if uploaded_file and p_name:
        if st.button("🚀 بدء التحليل والحفظ"):
            with st.spinner("جاري معالجة البيانات..."):
                result = process_document(uploaded_file)
                
                if isinstance(result, pd.DataFrame):
                    st.write("🔍 البيانات المستخرجة:")
                    st.dataframe(result, use_container_width=True)
                    
                    # حفظ في القاعدة
                    t_res = supabase.table("tenders").insert({"project_name": p_name, "client_name": c_name}).execute()
                    t_id = t_res.data[0]['id']
                    
                    items_to_db = []
                    for _, row in result.iterrows():
                        # محاولة جلب البيانات سواء كان المصدر إكسل أو PDF
                        desc = row.get('item') or row.get('البيان') or row.get('Description') or "بند غير محدد"
                        q = row.get('qty') or row.get('الكمية') or row.get('Quantity') or 0
                        u = row.get('unit') or row.get('الوحدة') or row.get('Unit') or "-"
                        
                        items_to_db.append({
                            "tender_id": t_id,
                            "item_description": str(desc),
                            "quantity": float(q),
                            "unit": str(u)
                        })
                    
                    supabase.table("tender_items").insert(items_data).execute()
                    st.balloons()
                    st.success(f"✅ تم حفظ مشروع '{p_name}' بنجاح!")
                else:
                    st.warning("تم استخراج نص ولكن لم يتم تنظيم جدول. النص:")
                    st.text(result)

elif menu == "📋 أرشيف المشاريع":
    st.title("📋 سجل المشاريع والكميات")
    res = supabase.table("tenders").select("*, tender_items(*)").execute()
    if res.data:
        for p in res.data:
            with st.expander(f"📌 {p['project_name']} - {p['client_name']}"):
                st.table(pd.DataFrame(p['tender_items'])[['item_description', 'unit', 'quantity']])

elif menu == "📦 إدارة المخازن":
    st.title("📦 مراقبة المشتريات والمخازن")
    res = supabase.table("tenders").select("id, project_name").execute()
    projects = {p['project_name']: p['id'] for p in res.data}
    selected_p = st.selectbox("اختر المشروع للمراجعة:", list(projects.keys()))

    if selected_p:
        t_id = projects[selected_p]
        items_res = supabase.table("tender_items").select("*").eq("tender_id", t_id).execute()
        logs_res = supabase.table("inventory_logs").select("*").eq("tender_id", t_id).execute()
        
        df_items = pd.DataFrame(items_res.data)
        df_logs = pd.DataFrame(logs_res.data)

        st.subheader("📊 مقارنة الاستهلاك")
        for _, item in df_items.iterrows():
            purchased = df_logs[df_logs['item_name'] == item['item_description']]['purchased_quantity'].sum() if not df_logs.empty else 0
            remaining = item['quantity'] - purchased
            
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"**{item['item_description']}**")
            col2.write(f"مشتريات: {purchased} من {item['quantity']}")
            color = "green" if remaining >= 0 else "red"
            col3.markdown(f"<span style='color:{color}'>المتبقي: {remaining}</span>", unsafe_allow_html=True)
            st.progress(min(float(purchased / item['quantity']), 1.0) if item['quantity'] > 0 else 0)

        st.markdown("---")
        st.subheader("➕ إضافة فاتورة مشتريات")
        with st.form("buy_form"):
            item_buy = st.selectbox("اختر البند", df_items['item_description'].tolist())
            qty_buy = st.number_input("الكمية", min_value=0.0)
            supp = st.text_input("المورد")
            if st.form_submit_button("حفظ الفاتورة"):
                supabase.table("inventory_logs").insert({"tender_id": t_id, "item_name": item_buy, "purchased_quantity": qty_buy, "supplier_name": supp}).execute()
                st.success("تم التحديث!")
                st.rerun()


