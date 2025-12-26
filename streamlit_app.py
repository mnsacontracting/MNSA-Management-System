import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. إعداد قاعدة البيانات الشاملة (تحديث الجداول المالية) ---
def init_db():
    conn = sqlite3.connect('mnsa_enterprise_erp.db')
    cursor = conn.cursor()
    # المشاريع والمقايسات
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Budget REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ProjectBOM (BOMID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, ItemName TEXT, Quantity REAL, Unit TEXT)')
    
    # الخزينة والبنوك
    cursor.execute('''CREATE TABLE IF NOT EXISTS FinanceAccounts 
                      (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, AccountName TEXT UNIQUE, AccountType TEXT, Balance REAL)''')
    
    # حركات القبض والصرف (خزينة وبنوك)
    cursor.execute('''CREATE TABLE IF NOT EXISTS FinanceTransactions 
                      (TransID INTEGER PRIMARY KEY AUTOINCREMENT, AccountID INTEGER, TransType TEXT, 
                       Amount REAL, Statement TEXT, Date TEXT, ProjectID INTEGER)''')

    # المستخلصات (Invoices/Certificates)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Certificates 
                      (CertID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, CertNumber TEXT, 
                       TotalAmount REAL, NetAmount REAL, Status TEXT, Date TEXT)''')

    # الموردين والمشتريات والمخزن (كما في النسخ السابقة)
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, Amount REAL, Description TEXT, Date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, CurrentStock REAL, Unit TEXT)')
    
    # إضافة حسابات افتراضية إذا كانت فارغة
    cursor.execute("SELECT COUNT(*) FROM FinanceAccounts")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO FinanceAccounts (AccountName, AccountType, Balance) VALUES ('الخزينة الرئيسية', 'Cash', 0), ('بنك مصر', 'Bank', 0)")
    
    conn.commit()
    return conn

conn = init_db()

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA Enterprise ERP", layout="wide", page_icon="💰")

# --- 3. محرك الإدخال والتقارير ---
st.sidebar.title("🏗️ MNSA Enterprise")
mode = st.sidebar.radio("اختر القسم:", ["📥 مدخلات النظام", "📊 محرك التقارير والمستخلصات", "💸 المالية والبنوك"])

# ---------------------------------------------------------
# القسم الأول: مدخلات النظام
# ---------------------------------------------------------
if mode == "📥 مدخلات النظام":
    st.header("📥 إدخال بيانات جديدة")
    sub_mode = st.selectbox("نوع الإدخال:", ["مشروع", "مورد", "مقايسة (BOM)"])
    
    if sub_mode == "مشروع":
        with st.form("p_f"):
            n = st.text_input("اسم المشروع")
            b = st.number_input("الميزانية", min_value=0.0)
            if st.form_submit_button("حفظ"):
                conn.execute("INSERT INTO Projects (ProjectName, Budget) VALUES (?,?)", (n, b))
                conn.commit()
                st.success("تم الحفظ")

# ---------------------------------------------------------
# القسم الثاني: المالية والبنوك (الجديد)
# ---------------------------------------------------------
elif mode == "💸 المالية والبنوك":
    st.header("💸 إدارة الخزينة والبنوك والمستخلصات")
    
    tab1, tab2, tab3 = st.tabs(["💵 حركة الخزينة والبنوك", "📄 المستخلصات", "🏦 أرصدة الحسابات"])
    
    with tab1:
        st.subheader("تسجيل عملية (قبض / صرف)")
        df_accs = pd.read_sql_query("SELECT * FROM FinanceAccounts", conn)
        df_projs = pd.read_sql_query("SELECT * FROM Projects", conn)
        
        with st.form("trans_form"):
            col1, col2 = st.columns(2)
            acc = col1.selectbox("الحساب (من/إلى)", df_accs['AccountName'])
            ttype = col2.selectbox("نوع العملية", ["قبض (توريد)", "صرف (دفع)"])
            amt = st.number_input("المبلغ", min_value=0.0)
            proj = st.selectbox("مرتبط بمشروع (اختياري)", ["عام"] + list(df_projs['ProjectName']))
            statement = st.text_area("البيان / السبب")
            
            if st.form_submit_button("تأكيد العملية الممالية"):
                acc_id = df_accs[df_accs['AccountName']==acc]['AccountID'].values[0]
                dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                # تحديث رصيد الحساب
                mod = amt if ttype == "قبض (توريد)" else -amt
                conn.execute("UPDATE FinanceAccounts SET Balance = Balance + ? WHERE AccountID = ?", (mod, int(acc_id)))
                # تسجيل الحركة
                conn.execute("INSERT INTO FinanceTransactions (AccountID, TransType, Amount, Statement, Date) VALUES (?,?,?,?,?)", 
                             (int(acc_id), ttype, amt, statement, dt))
                conn.commit()
                st.success(f"تم تنفيذ العملية بنجاح. الرصيد المحدث لـ {acc} هو الحالي.")

    with tab2:
        st.subheader("📑 إدارة مستخلصات المشاريع")
        with st.form("cert_form"):
            p_sel = st.selectbox("المشروع", df_projs['ProjectName'])
            c_num = st.text_input("رقم المستخلص")
            c_total = st.number_input("إجمالي قيمة الأعمال", min_value=0.0)
            c_net = st.number_input("صافي القيمة (بعد الخصومات)", min_value=0.0)
            c_status = st.selectbox("الحالة", ["قيد المراجعة", "تم الاعتماد", "تم التحصيل"])
            if st.form_submit_button("حفظ المستخلص"):
                p_id = df_projs[df_projs['ProjectName']==p_sel]['ProjectID'].values[0]
                dt = datetime.now().strftime("%Y-%m-%d")
                conn.execute("INSERT INTO Certificates (ProjectID, CertNumber, TotalAmount, NetAmount, Status, Date) VALUES (?,?,?,?,?,?)", 
                             (int(p_id), c_num, c_total, c_net, c_status, dt))
                conn.commit()
                st.success("تم تسجيل المستخلص")

    with tab3:
        st.subheader("🏦 الأرصدة الحالية")
        df_bal = pd.read_sql_query("SELECT AccountName as الحساب, AccountType as النوع, Balance as الرصيد FROM FinanceAccounts", conn)
        st.table(df_bal)

# ---------------------------------------------------------
# القسم الثالث: محرك التقارير
# ---------------------------------------------------------
elif mode == "📊 محرك التقارير والمستخلصات":
    st.header("📊 محرك التقارير الشامل")
    rep_type = st.selectbox("نوع التقرير:", ["كشف حساب خزينة/بنك", "موقف مستخلصات المشاريع", "الأرباح والخسائر للمشروع"])
    
    if rep_type == "كشف حساب خزينة/بنك":
        accs = pd.read_sql_query("SELECT AccountName FROM FinanceAccounts", conn)
        s_acc = st.selectbox("اختر الحساب", accs['AccountName'])
        df_t = pd.read_sql_query(f"SELECT Date, TransType, Amount, Statement FROM FinanceTransactions WHERE AccountID = (SELECT AccountID FROM FinanceAccounts WHERE AccountName='{s_acc}')", conn)
        st.dataframe(df_t, use_container_width=True)

    elif rep_type == "موقف مستخلصات المشاريع":
        df_c = pd.read_sql_query("""
            SELECT p.ProjectName, c.CertNumber, c.TotalAmount, c.Status, c.Date 
            FROM Certificates c JOIN Projects p ON c.ProjectID = p.ProjectID
        """, conn)
        st.dataframe(df_c, use_container_width=True)
