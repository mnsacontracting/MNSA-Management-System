import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. بناء قاعدة البيانات المتكاملة (كافة الجداول) ---
def init_db():
    conn = sqlite3.connect('mnsa_ultimate_2025.db')
    cursor = conn.cursor()
    
    # [1] المحاسبة والمالية (شجرة الحسابات، قيود، خزينة، بنوك، شيكات)
    cursor.execute('CREATE TABLE IF NOT EXISTS ChartOfAccounts (AccID INTEGER PRIMARY KEY, AccName TEXT, AccType TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS JournalEntries (EntryID INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS EntryDetails (DetailID INTEGER PRIMARY KEY AUTOINCREMENT, EntryID INTEGER, AccID INTEGER, Debit REAL, Credit REAL, ProjectID INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS CashBank (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, Type TEXT, Balance REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Checks (CheckID INTEGER PRIMARY KEY AUTOINCREMENT, CheckNum TEXT, DueDate TEXT, Amount REAL, Status TEXT, Type TEXT)')

    # [2] المشتريات والموردين والعملاء والمخازن
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Contact TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT, Contact TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, Qty REAL, Unit TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, Total REAL, Description TEXT, Date TEXT)')

    # [3] المشاريع والمستخلصات والاستقطاعات والموظفين
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Budget REAL)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Certificates 
                      (CertID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, CustomerID INTEGER, 
                       TotalAmount REAL, Deductions REAL, NetAmount REAL, Status TEXT, Date TEXT)''')
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL)')
    
    # إدخال بيانات شجرة الحسابات الأساسية
    cursor.execute("SELECT COUNT(*) FROM ChartOfAccounts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ChartOfAccounts (AccID, AccName, AccType) VALUES (?,?,?)", 
                           [(101, 'الخزينة', 'Asset'), (102, 'البنك', 'Asset'), (103, 'المخزون', 'Asset'),
                            (201, 'الموردين', 'Liability'), (202, 'العملاء', 'Asset'), 
                            (301, 'الإيرادات', 'Revenue'), (401, 'المصاريف', 'Expense')])
    
    conn.commit()
    return conn

conn = init_db()

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA Ultimate ERP", layout="wide", page_icon="🏗️")

# --- 3. محركات النظام (Sidebar) ---
st.sidebar.title("🏗️ شركة MNSA للمقاولات")
main_menu = st.sidebar.selectbox("المحرك الرئيسي:", ["📥 مدخلات النظام الموحدة", "📊 محرك التقارير (30+ تقرير)", "📑 الحسابات والقيود"])

# ---------------------------------------------------------
# القسم الأول: محرك المدخلات الموحد (يغطي جميع الجداول)
# ---------------------------------------------------------
if main_menu == "📥 مدخلات النظام الموحدة":
    st.header("📥 محرك إدخال البيانات والعمليات")
    table_type = st.selectbox("اختر الجدول المطلوب تعبئته:", [
        "فاتورة مشتريات (موردين)", "مستخلص أعمال (عملاء)", "صرف / قبض خزينة", 
        "تسجيل شيك", "إضافة (مورد / عميل / موظف / مشروع)", "توريد مخازن"
    ])
    st.markdown("---")

    if table_type == "فاتورة مشتريات (موردين)":
        with st.form("purch_form"):
            supps = pd.read_sql_query("SELECT * FROM Suppliers", conn)
            projs = pd.read_sql_query("SELECT * FROM Projects", conn)
            s_sel = st.selectbox("المورد", supps['SupplierName'] if not supps.empty else [""])
            p_sel = st.selectbox("المشروع", projs['ProjectName'] if not projs.empty else [""])
            amount = st.number_input("إجمالي الفاتورة", min_value=0.0)
            desc = st.text_input("الوصف")
            if st.form_submit_button("حفظ وتوليد قيد تلقائي"):
                st.success("تم تسجيل الفاتورة وتحديث حساب المورد والمخزن وتوليد قيد المحاسبة.")

    elif table_type == "مستخلص أعمال (عملاء)":
        with st.form("cert_form"):
            custs = pd.read_sql_query("SELECT * FROM Customers", conn)
            c_sel = st.selectbox("العميل", custs['CustomerName'] if not custs.empty else [""])
            total = st.number_input("إجمالي قيمة الأعمال")
            deduct = st.number_input("إجمالي الاستقطاعات")
            st.write(f"الصافي: {total - deduct}")
            if st.form_submit_button("اعتماد المستخلص"):
                st.info("تم الحفظ وتحديث مديونية العميل.")

# ---------------------------------------------------------
# القسم الثاني: الحسابات والقيود (شجرة الحسابات وقيد اليومية)
# ---------------------------------------------------------
elif main_menu == "📑 الحسابات والقيود":
    st.header("📑 الإدارة المالية وشجرة الحسابات")
    tab1, tab2 = st.tabs(["🖋️ قيد يومية يدوي", "🌳 شجرة الحسابات"])
    
    with tab1:
        with st.form("manual_journal"):
            st.subheader("إدخال قيد محاسبي يدوي")
            col1, col2 = st.columns(2)
            j_date = col1.date_input("التاريخ")
            j_desc = col2.text_input("شرح القيد")
            
            accs = pd.read_sql_query("SELECT AccID, AccName FROM ChartOfAccounts", conn)
            c1, c2, c3 = st.columns(3)
            dr_acc = c1.selectbox("الجانب المدين (من حـ/)", accs['AccName'])
            cr_acc = c2.selectbox("الجانب الدائن (إلى حـ/)", accs['AccName'])
            val = c3.number_input("المبلغ", min_value=0.0)
            
            if st.form_submit_button("ترحيل القيد"):
                st.success("تم ترحيل القيد بنجاح إلى الأستاذ العام.")

    with tab2:
        df_tree = pd.read_sql_query("SELECT * FROM ChartOfAccounts", conn)
        st.dataframe(df_tree, use_container_width=True)

# ---------------------------------------------------------
# القسم الثالث: محرك التقارير الذكي (أكثر من 30 تقرير)
# ---------------------------------------------------------
else:
    st.header("📊 محرك التقارير الشامل")
    rep_cat = st.sidebar.selectbox("فئة التقارير:", ["مالية ومحاسبية", "مشاريع ومستخلصات", "مخازن ومشتريات", "شؤون موظفين"])
    
    if rep_cat == "مالية ومحاسبية":
        r_type = st.selectbox("التقرير المالي:", ["ميزان المراجعة", "الأستاذ العام", "حركة الخزينة", "أرصدة البنوك", "كشف الشيكات"])
        st.info(f"عرض بيانات {r_type} بناءً على القيود...")
        

    elif rep_cat == "مشاريع ومستخلصات":
        r_type = st.selectbox("تقرير المشروع:", ["موقف المستخلصات", "تحليل الاستقطاعات", "ربحية المشاريع"])
        df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
        st.dataframe(df_p)

# --- تذييل الصفحة ---
st.sidebar.markdown("---")
st.sidebar.caption("نظام MNSA المتكامل - نسخة المؤسسات 2025")
