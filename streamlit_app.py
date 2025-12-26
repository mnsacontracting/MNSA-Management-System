import streamlit as st
import sqlite3
import pandas as pd
import os

# --- 1. إعداد قاعدة البيانات ---
# هذا الجزء يقوم بإنشاء الجداول بناءً على هيكل شركتك
def init_db():
    conn = sqlite3.connect('mnsa_erp.db')
    cursor = conn.cursor()
    
    # إنشاء جدول المشاريع
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Projects (
            ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectName TEXT NOT NULL,
            Budget DECIMAL(18, 2)
        )
    ''')
    
    # إنشاء جدول المقايسة (BOM)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProjectBOM (
            BOMID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectID INTEGER,
            ItemName TEXT,
            Quantity DECIMAL(18, 2),
            Unit TEXT,
            FOREIGN KEY (ProjectID) REFERENCES Projects (ProjectID)
        )
    ''')
    conn.commit()
    return conn

# تشغيل قاعدة البيانات
conn = init_db()

# --- 2. واجهة التطبيق ---
st.set_page_config(page_title="MNSA ERP", layout="wide")
st.title("🏗️ نظام إدارة شركة MNSA للمقاولات")

# القائمة الجانبية
st.sidebar.title("MNSA Control Panel")
menu = st.sidebar.radio("انتقل إلى:", ["لوحة التحكم", "إضافة مشاريع", "المقايسات والحصر"])

# --- القسم الأول: لوحة التحكم ---
if menu == "لوحة التحكم":
    st.header("📊 حالة المشاريع الحالية")
    df_projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not df_projects.empty:
        st.dataframe(df_projects, use_container_width=True)
    else:
        st.info("لا توجد مشاريع مسجلة حالياً.")

# --- القسم الثاني: إضافة المشاريع ---
elif menu == "إضافة مشاريع":
    st.header("➕ تسجيل مشروع جديد")
    with st.form("project_form"):
        p_name = st.text_input("اسم المشروع")
        p_budget = st.number_input("الميزانية المرصودة", min_value=0.0)
        submitted = st.form_submit_button("حفظ المشروع في SQL")
        
        if submitted and p_name:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Projects (ProjectName, Budget) VALUES (?, ?)", (p_name, p_budget))
            conn.commit()
            st.success(f"تم تسجيل مشروع {p_name} بنجاح!")

# --- القسم الثالث: المقايسات والحصر ---
elif menu == "المقايسات والحصر":
    st.header("📋 إدارة مقايسات بنود الأعمال")
    
    # سحب المشاريع المتاحة
    df_projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    if not df_projects.empty:
        selected_p = st.selectbox("اختر المشروع لتعديل مقايسته:", df_projects['ProjectName'])
        p_id = df_projects[df_projects['ProjectName'] == selected_p]['ProjectID'].values[0]
        
        st.subheader(f"إضافة بند لمشروع: {selected_p}")
        col1, col2, col3 = st.columns(3)
        item = col1.text_input("بيان العمل (مثل: خرسانة مسلحة)")
        qty = col2.number_input("الكمية", min_value=0.0)
        unit = col3.selectbox("الوحدة", ["طن", "م3", "م.ط", "م2", "عدد"])
        
        if st.button("حفظ البند في المقايسة"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", 
                           (int(p_id), item, qty, unit))
            conn.commit()
            st.success("تمت إضافة البند بنجاح")
            
        # عرض الحصر الحالي للمشروع
        st.markdown("---")
        st.subheader("📝 المقايسة الحالية")
        df_bom = pd.read_sql_query(f"SELECT ItemName as 'البند', Quantity as 'الكمية', Unit as 'الوحدة' FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
        st.table(df_bom)
    else:
        st.warning("يرجى إضافة مشروع أولاً.")
