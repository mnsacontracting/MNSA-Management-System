import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات وتجهيزها بالبيانات الحقيقية من ملفك
def init_db():
    conn = sqlite3.connect('mnsa_internal.db')
    cursor = conn.cursor()
    
    # إنشاء الجداول الأساسية كما وردت في ملف الـ SQL الخاص بك
    cursor.execute('''CREATE TABLE IF NOT EXISTS Projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectName TEXT,
        Location TEXT,
        Budget DECIMAL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ProjectBOM (
        BOMID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectID INTEGER,
        ItemName TEXT,
        Quantity DECIMAL,
        Unit TEXT,
        FOREIGN KEY (ProjectID) REFERENCES Projects (ProjectID)
    )''')
    
    # إنشاء جدول الموردين (موجود في ملفك)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierName TEXT,
        ContactInfo TEXT
    )''')

    # إضافة بيانات تجريبية (من واقع الملف) إذا كانت الجداول فارغة
    cursor.execute("SELECT COUNT(*) FROM Projects")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES ('مشروع العاصمة الإدارية', 'القاهرة', 5000000)")
        cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES ('برج العلمين', 'الساحل الشمالي', 8000000)")
        conn.commit()
        
    return conn

conn = init_db()

# 2. واجهة التطبيق
st.set_page_config(page_title="MNSA ERP", layout="wide")
st.title("🏗️ نظام إدارة شركة MNSA للمقاولات")

menu = st.sidebar.selectbox("القائمة الرئيسية", ["لوحة التحكم", "إدارة المشاريع", "حصر المواد (BOM)"])

if menu == "لوحة التحكم":
    st.header("📊 ملخص عام للمشاريع")
    df_projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    st.dataframe(df_projects, use_container_width=True)
    
    # إحصائية سريعة
    total_budget = df_projects['Budget'].sum()
    st.metric("إجمالي ميزانية المشاريع", f"{total_budget:,.2f} ج.م")

elif menu == "إدارة المشاريع":
    st.header("📝 إضافة مشروع جديد للقاعدة")
    with st.form("new_p"):
        name = st.text_input("اسم المشروع")
        loc = st.text_input("الموقع")
        bud = st.number_input("الميزانية", min_value=0.0)
        if st.form_submit_button("حفظ"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?, ?, ?)", (name, loc, bud))
            conn.commit()
            st.success("تم الحفظ بنجاح")
            st.rerun()

elif menu == "حصر المواد (BOM)":
    st.header("📋 حصر الكميات والمواد")
    projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    sel_p = st.selectbox("اختر المشروع", projects['ProjectName'])
    p_id = projects[projects['ProjectName'] == sel_p]['ProjectID'].values[0]
    
    # محرك الحصر التلقائي
    st.subheader("إضافة بند وحصر خاماته")
    col1, col2, col3 = st.columns(3)
    item = col1.text_input("اسم البند (مثال: خرسانة مسلحة)")
    qty = col2.number_input("الكمية", min_value=0.0)
    unit = col3.selectbox("الوحدة", ["م3", "طن", "م2", "عدد"])
    
    if st.button("حفظ وحصر"):
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", (int(p_id), item, qty, unit))
        conn.commit()
        st.success("تم الإضافة")

    # عرض الحصر
    df_bom = pd.read_sql_query(f"SELECT ItemName, Quantity, Unit FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
    st.table(df_bom)
