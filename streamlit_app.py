import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد الاتصال بقاعدة البيانات (اسم الملف الذي سيتم إنشاؤه)
DB_NAME = "mnsa_company.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # إنشاء الجداول الأساسية بناءً على ملف dump.sql الخاص بك
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Projects (
            ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectName NVARCHAR(255) NOT NULL,
            Location NVARCHAR(255),
            Budget DECIMAL(18, 2)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ProjectBOM (
            BOMID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectID INT,
            ItemName NVARCHAR(255),
            Quantity DECIMAL(18, 2),
            Unit NVARCHAR(50),
            FOREIGN KEY (ProjectID) REFERENCES Projects (ProjectID)
        )
    ''')
    conn.commit()
    return conn

conn = init_db()

# 2. واجهة التحكم
st.set_page_config(page_title="MNSA ERP System", layout="wide")
st.title("🏗️ نظام إدارة شركة MNSA للمقاولات")

# القائمة الجانبية
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4300/4300058.png", width=100)
menu = st.sidebar.selectbox("القائمة الرئيسية", ["لوحة التحكم", "إضافة مشروع جديد", "حصر الكميات (BOM)"])

if menu == "لوحة التحكم":
    st.header("📊 نظرة عامة على المشاريع")
    df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not df_p.empty:
        st.dataframe(df_p, use_container_width=True)
    else:
        st.info("لا توجد مشاريع مسجلة بعد. اذهب لصفحة 'إضافة مشروع' للبدء.")

elif menu == "إضافة مشروع جديد":
    st.header("📝 تسجيل بيانات المشروع")
    with st.form("add_project"):
        name = st.text_input("اسم المشروع")
        loc = st.text_input("الموقع")
        budget = st.number_input("الميزانية المرصودة (جنيه)", min_value=0.0)
        submit = st.form_submit_button("حفظ المشروع")
        
        if submit and name:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?, ?, ?)", (name, loc, budget))
            conn.commit()
            st.success(f"تم إضافة مشروع {name} بنجاح!")

elif menu == "حصر الكميات (BOM)":
    st.header("📋 حصر بنود المقايسة")
    projects = pd.read_sql_query("SELECT ProjectID, ProjectName FROM Projects", conn)
    
    if not projects.empty:
        project_choice = st.selectbox("اختر المشروع", projects['ProjectName'])
        p_id = projects[projects['ProjectName'] == project_choice]['ProjectID'].values[0]
        
        with st.expander("إضافة بند جديد"):
            col1, col2, col3 = st.columns(3)
            item = col1.text_input("اسم المادة/البند")
            qty = col2.number_input("الكمية", min_value=0.0)
            unit = col3.selectbox("الوحدة", ["م3", "طن", "م2", "م.ط", "عدد"])
            
            if st.button("إضافة للمقايسة"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", 
                               (int(p_id), item, qty, unit))
                conn.commit()
                st.success("تم إضافة البند")

        # عرض المقايسة
        df_bom = pd.read_sql_query(f"SELECT ItemName, Quantity, Unit FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
        st.table(df_bom)
    else:
        st.warning("يجب إضافة مشروع أولاً.")
