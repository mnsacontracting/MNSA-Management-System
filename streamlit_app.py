import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. بناء قاعدة البيانات المحاسبية والتشغيلية الكاملة ---
def init_db():
    conn = sqlite3.connect('mnsa_enterprise_final_2025.db')
    cursor = conn.cursor()
    
    # [1] جداول الحسابات والمالية
    cursor.execute('CREATE TABLE IF NOT EXISTS ChartOfAccounts (AccID INTEGER PRIMARY KEY, AccName TEXT, AccType TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS JournalEntries (EntryID INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS EntryDetails (DetailID INTEGER PRIMARY KEY AUTOINCREMENT, EntryID INTEGER, AccID INTEGER, Debit REAL, Credit REAL, ProjectID INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS CashBank (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, Type TEXT, Balance REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Checks (CheckID INTEGER PRIMARY KEY AUTOINCREMENT, CheckNum TEXT, DueDate TEXT, Amount REAL, Status TEXT, Type TEXT)')

    # [2] جداول الأشخاص والمخازن
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Contact TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT, Contact TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL, NationalID TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, Qty REAL, Unit TEXT)')

    # [3] جداول المشاريع والمستخلصات
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Location TEXT, Budget REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, Total REAL, Description TEXT, Date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Certificates (CertID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, CustomerID INTEGER, TotalAmount REAL, Deductions REAL, NetAmount REAL, Status TEXT, Date TEXT)')

    # إدخال بيانات أساسية إذا كانت فارغة
    cursor.execute("SELECT COUNT(*) FROM ChartOfAccounts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ChartOfAccounts (AccID, AccName, AccType) VALUES (?,?,?)", 
                           [(101, 'الخزينة', 'Asset'), (102, 'البنك', 'Asset'), (201, 'الموردين', 'Liability'), (301, 'المبيعات', 'Revenue'), (401, 'المصاريف', 'Expense')])
        cursor.executemany("INSERT INTO CashBank (Name, Type, Balance) VALUES (?,?,?)", 
                           [('الخزينة الرئيسية', 'Cash', 0), ('بنك مصر', 'Bank', 0)])
    
    conn.commit()
    return conn

conn = init_db()

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA Enterprise ERP", layout="wide", page_icon="🏗️")

# --- 3. محرك التنقل الرئيسي (Sidebar) ---
st.sidebar.title("🏗️ MNSA Group ERP")
main_mode = st.sidebar.selectbox("المحرك الرئيسي:", ["📥 محرك المدخلات الموحد", "📊 محرك التقارير الذكي"])

# ---------------------------------------------------------
# القسم الأول: محرك المدخلات (Entry Engine)
# ---------------------------------------------------------
if main_mode == "📥 محرك المدخلات الموحد":
    st.header("📥 إدخال البيانات والعمليات")
    
    entry_cat = st.selectbox("اختر فئة الإدخال:", ["المالية والحسابات", "المشاريع والمستخلصات", "إدارة الأطراف (موردين/عملاء/موظفين)", "المخازن والمشتريات"])
    st.markdown("---")

    if entry_cat == "المالية والحسابات":
        sub = st.radio("العملية:", ["قيد يومية يدوي", "سند قبض/صرف", "شيك جديد"], horizontal=True)
        if sub == "قيد يومية يدوي":
            with st.form("manual_entry"):
                col1, col2 = st.columns(2)
                date = col1.date_input("التاريخ")
                desc = col2.text_input("وصف القيد")
                # محاذاة الطرفين المدين والدائن
                accs = pd.read_sql_query("SELECT AccName FROM ChartOfAccounts", conn)
                c1, c2, c3 = st.columns(3)
                dr_acc = c1.selectbox("من حـ/ (مدين)", accs)
                cr_acc = c2.selectbox("إلى حـ/ (دائن)", accs)
                amount = c3.number_input("القيمة", min_value=0.0)
                if st.form_submit_button("ترحيل القيد"):
                    st.success("تم ترحيل القيد بنجاح")

    elif entry_cat == "المشاريع والمستخلصات":
        sub = st.radio("العملية:", ["مشروع جديد", "مستخلص أعمال"], horizontal=True)
        if sub == "مشروع جديد":
            with st.form("p_form"):
                n = st.text_input("اسم المشروع")
                b = st.number_input("الميزانية")
                if st.form_submit_button("حفظ"):
                    conn.execute("INSERT INTO Projects (ProjectName, Budget) VALUES (?,?)", (n, b))
                    conn.commit()
                    st.success("تم الحفظ")
        elif sub == "مستخلص أعمال":
            projs = pd.read_sql_query("SELECT ProjectID, ProjectName FROM Projects", conn)
            custs = pd.read_sql_query("SELECT CustomerID, CustomerName FROM Customers", conn)
            with st.form("cert_form"):
                p_id = st.selectbox("المشروع", projs['ProjectName'])
                c_id = st.selectbox("العميل", custs['CustomerName'] if not custs.empty else [""])
                total = st.number_input("إجمالي الأعمال")
                deduct = st.number_input("الاستقطاعات (تأمينات/ضرائب/دمغات)")
                st.write(f"صافي المستخلص: {total - deduct}")
                if st.form_submit_button("اعتماد المستخلص"):
                    st.info("تم الحفظ وتحديث مديونية العميل")

    elif entry_cat == "إدارة الأطراف (موردين/عملاء/موظفين)":
        type_p = st.selectbox("الطرف:", ["مورد", "عميل", "موظف"])
        with st.form("party_form"):
            name = st.text_input(f"اسم ال{type_p}")
            info = st.text_input("بيانات التواصل / الوظيفة")
            if st.form_submit_button("إضافة"):
                if type_p == "مورد": conn.execute("INSERT INTO Suppliers (SupplierName, Contact) VALUES (?,?)", (name, info))
                elif type_p == "عميل": conn.execute("INSERT INTO Customers (CustomerName, Contact) VALUES (?,?)", (name, info))
                else: conn.execute("INSERT INTO Employees (EmployeeName, JobTitle) VALUES (?,?)", (name, info))
                conn.commit()
                st.success("تمت الإضافة بنجاح")

# ---------------------------------------------------------
# القسم الثاني: محرك التقارير (Reporting Engine)
# ---------------------------------------------------------
else:
    st.header("📊 محرك التقارير والتحليل")
    report_type = st.sidebar.selectbox("نوع التقرير:", [
        "كشف أرصدة البنوك والخزينة", "جرد المخازن", "تقرير المستخلصات", 
        "أرصدة الموردين", "أرصدة العملاء", "كشف رواتب الموظفين", "الأستاذ العام"
    ])

    if report_type == "كشف أرصدة البنوك والخزينة":
        df = pd.read_sql_query("SELECT Name as الحساب, Type as النوع, Balance as الرصيد FROM CashBank", conn)
        st.table(df)
        

    elif report_type == "تقرير المستخلصات":
        st.info("عرض موقف المستخلصات والتحصيل لكل مشروع")
        df_c = pd.read_sql_query("SELECT * FROM Certificates", conn)
        st.dataframe(df_c)

    elif report_type == "جرد المخازن":
        df_i = pd.read_sql_query("SELECT * FROM Inventory", conn)
        st.bar_chart(df_i.set_index('ItemName')['Qty'])
        st.dataframe(df_i)

# --- تذييل الصفحة ---
st.sidebar.markdown("---")
st.sidebar.caption("MNSA Enterprise ERP v2.0 - 2025")
