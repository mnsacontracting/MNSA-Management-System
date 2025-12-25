import streamlit as st
from supabase import create_client, Client

# --- 1. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP System", layout="wide")

# --- 2. بيانات الربط المباشرة ---
# يا مصطفى: ضع بياناتك الحقيقية هنا بدلاً من النقط
URL = "https://your-project.supabase.co" 
KEY = "your-anon-key-here"

# محاولة الربط
try:
    supabase: Client = create_client(URL, KEY)
except Exception as e:
    st.error("فشل الاتصال بـ Supabase. تأكد من المفاتيح.")

# --- 3. تصميم القائمة الجانبية (Sidebar) ---
# تم تصحيح الخطأ هنا (استخدام html بدلاً من input)
st.sidebar.markdown("<h1 style='text-align: center; color: #007bff;'>MNSA Contracting</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

menu = st.sidebar.radio("نظام إدارة الموارد ERP", 
    ["📊 لوحة التحكم", "📝 المناقصات والعقود", "📦 المخازن والمشتريات", "👥 الموظفين والمقاولين", "💰 الحسابات العامة"])

# --- 4. محتوى الصفحات ---

if menu == "📊 لوحة التحكم":
    st.title("🏗️ نظام MNSA ERP المتكامل")
    st.markdown("---")
    
    # بطاقات إحصائية (Metrics)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("المناقصات الجارية", "12", "+2")
    with c2: st.metric("المشاريع القائمة", "5")
    with c3: st.metric("تأمينات محجوزة", "450k", "ج.م")
    with c4: st.metric("مشتريات الشهر", "120k", "-5%")

elif menu == "📝 المناقصات والعقود":
    st.title("📝 إدارة المناقصات")
    with st.form("tender_form", clear_on_submit=True):
        t_name = st.text_input("اسم المناقصة")
        t_client = st.text_input("جهة الإسناد")
        t_ins = st.number_input("قيمة التأمين الابتدائي", min_value=0)
        t_file = st.file_uploader("ارفع ملف المناقصة (PDF/Image)")
        
        if st.form_submit_button("حفظ المناقصة"):
            if t_name and t_client:
                data = {"title": t_name, "client": t_client, "insurance_amount": t_ins}
                supabase.table("tenders").insert(data).execute()
                st.success(f"تم حفظ {t_name} بنجاح!")
            else:
                st.warning("يرجى ملء البيانات الأساسية")

elif menu == "📦 المخازن والمشتريات":
    st.title("📦 إدارة المخازن")
    st.info("قسم مقارنة فواتير الإكسل بالمناقصات قيد التجهيز.")
    st.file_uploader("ارفع ملف فواتير المشتريات (Excel)")

else:
    st.title(f"قسم {menu}")
    st.write("سيتم ربط هذا القسم بجداول Supabase فور إنشائها.")

# تذييل
st.sidebar.markdown("---")
st.sidebar.caption("v1.0.1 | MNSA Contracting")
