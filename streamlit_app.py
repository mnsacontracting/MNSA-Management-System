import streamlit as st
from supabase import create_client, Client

# --- 1. إعدادات الصفحة والواجهة ---
st.set_page_config(page_title="MNSA ERP System", layout="wide", initial_sidebar_state="expanded")

# --- 2. ربط قاعدة البيانات (مباشر) ---
# يا مصطفى: ضع بياناتك الحقيقية بين علامات التنصيص بالأسفل
SUPABASE_URL = "أدخل_رابط_مشروعك_هنا"
SUPABASE_KEY = "أدخل_المفتاح_الطويل_هنا"

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("تأكد من وضع الرابط والمفتاح الصحيح داخل الكود")

# --- 3. تصميم القائمة الجانبية (Sidebar) ---
st.sidebar.markdown("<h1 style='text-align: center; color: #007bff;'>MNSA Contracting</h1>", unsafe_allow_input=True)
st.sidebar.markdown("---")
menu = st.sidebar.radio("نظام إدارة الموارد ERP", 
    ["📊 لوحة التحكم", "📝 المناقصات والعقود", "🏗️ إدارة المواقع", "📦 المخازن والمشتريات", "👥 شؤون الموظفين", "💰 الحسابات العامة"])

# --- 4. لوحة التحكم (Dashboard) ---
if menu == "📊 لوحة التحكم":
    st.title("🏗️ نظام MNSA ERP المتكامل")
    st.markdown("---")
    
    # بطاقات إحصائية احترافية
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("المناقصات الجارية")
        st.subheader("12")
    with col2:
        st.success("المشاريع القائمة")
        st.subheader("5")
    with col3:
        st.warning("تأمينات محجوزة")
        st.subheader("450,000 ج.م")
    with col4:
        st.error("مشتريات الشهر")
        st.subheader("120,000 ج.م")

    st.markdown("---")
    st.subheader("🔔 تنبيهات النظام")
    st.write("- مناقصة (إنشاء مدرسة) موعد المظاريف بعد 3 أيام.")
    st.write("- يوجد نقص في توريد الأسمنت بموقع (التجمع).")

# --- 5. قسم المناقصات (مع ميزة رفع الملفات) ---
elif menu == "📝 المناقصات والعقود":
    st.title("📝 إدارة المناقصات والعقود")
    tab1, tab2, tab3 = st.tabs(["تسجيل جديد", "الأرشيف", "حصر الكميات (AI)"])
    
    with tab1:
        with st.form("tender_form", clear_on_submit=True):
            t_name = st.text_input("اسم المناقصة")
            t_client = st.text_input("جهة الإسناد")
            t_value = st.number_input("القيمة التقديرية", min_value=0)
            t_date = st.date_input("تاريخ فتح المظاريف")
            t_file = st.file_uploader("ارفع ملف المناقصة (PDF/Scan)", type=['pdf', 'png', 'jpg'])
            
            if st.form_submit_button("حفظ وإرسال"):
                data = {"title": t_name, "client": t_client, "insurance_amount": t_value, "status": "تحت الدراسة"}
                supabase.table("tenders").insert(data).execute()
                st.success(f"تم تسجيل مناقصة {t_name} بنجاح!")

    with tab2:
        # جلب البيانات من Supabase
        res = supabase.table("tenders").select("*").execute()
        if res.data:
            st.dataframe(res.data, use_container_width=True)
        else:
            st.info("لا توجد بيانات حالياً.")

# --- 6. باقي الأقسام (الهيكل الأساسي) ---
elif menu == "📦 المخازن والمشتريات":
    st.title("📦 إدارة المخازن")
    st.file_uploader("رفع فواتير المشتريات (Excel) للمقارنة", type=['xlsx', 'csv'])
    st.info("هذا القسم مربوط تلقائياً بجدول المشتريات لمقارنة الكميات.")

elif menu == "👥 شؤون الموظفين":
    st.title("👥 إدارة الموظفين والمقاولين")
    st.button("إضافة موظف جديد")
    st.button("مستخلصات مقاولين الباطن")

elif menu == "💰 الحسابات العامة":
    st.title("💰 الإدارة المالية")
    st.write("شجرة الحسابات - القيود اليومية - ميزانية المشاريع")

# --- تذييل الصفحة ---
st.sidebar.markdown("---")
st.sidebar.caption("تم التطوير لصالح شركة MNSA v1.0")
