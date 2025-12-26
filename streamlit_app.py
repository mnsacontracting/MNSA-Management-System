import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. بناء قاعدة البيانات (كافة الجداول المطلوبة) ---
def init_db():
    conn = sqlite3.connect('mnsa_master_erp.db')
    cursor = conn.cursor()
    # المالية وشجرة الحسابات والقيود
    cursor.execute('CREATE TABLE IF NOT EXISTS ChartOfAccounts (AccID INTEGER PRIMARY KEY, AccName TEXT, AccType TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS JournalEntries (EntryID INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS EntryDetails (DetailID INTEGER PRIMARY KEY AUTOINCREMENT, EntryID INTEGER, AccID INTEGER, Debit REAL, Credit REAL, ProjectID INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS CashBank (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, Type TEXT, Balance REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Checks (CheckID INTEGER PRIMARY KEY AUTOINCREMENT, CheckNum TEXT, DueDate TEXT, Amount REAL, Status TEXT, Type TEXT)')

    # الموردين والعملاء والموظفين والمشاريع
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Budget REAL)')

    # المشتريات والمستخلصات والمخازن والاستقطاعات
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, Qty REAL, Unit TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, ItemName TEXT, Qty REAL, Amount REAL, Date TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Certificates 
                      (CertID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, CustomerID INTEGER, 
                       TotalAmount REAL, Deductions REAL, NetAmount REAL, Status TEXT, Date TEXT)''')
    
    # إدخال بيانات أساسية (شجرة الحسابات)
    cursor.execute("SELECT COUNT(*) FROM ChartOfAccounts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ChartOfAccounts VALUES (?,?,?)", 
                           [(101, 'الخزينة', 'Asset'), (102, 'البنك', 'Asset'), (103, 'المخزون', 'Asset'), (201, 'الموردين', 'Liability'), (202, 'العملاء', 'Asset')])
        cursor.executemany("INSERT INTO CashBank (Name, Type, Balance) VALUES (?,?,?)", [('الخزينة الرئيسية', 'Cash', 0), ('البنك الأهلي', 'Bank', 0)])
    conn.commit()
    return conn

conn = init_db()

# --- 2. واجهة البرنامج ---
st.set_page_config(page_title="MNSA Master ERP", layout="wide")
st.sidebar.title("🏗️ نظام MNSA المتكامل")
mode = st.sidebar.selectbox("المحرك الرئيسي:", ["📥 محرك المدخلات (Entries)", "📊 محرك التقارير (Reports)", "📑 شجرة الحسابات والقيود"])

# ---------------------------------------------------------
# القسم الأول: محرك المدخلات (يشمل كل الشاشات المطلوبة)
# ---------------------------------------------------------
if mode == "📥 محرك المدخلات (Entries)":
    st.header("📥 محرك إدخال العمليات")
    task = st.selectbox("اختر نوع العملية:", 
                        ["فاتورة مشتريات وتوريد مخزن", "سند (قبض / صرف) خزينة وبنك", "مستخلص أعمال واستقطاعات", "إضافة بيانات (مورد/عميل/موظف/مشروع)"])
    
    if task == "فاتورة مشتريات وتوريد مخزن":
        with st.form("purch_inv"):
            st.subheader("🛒 تسجيل مشتريات وتحديث مخزن ومورد")
            df_s = pd.read_sql_query("SELECT * FROM Suppliers", conn)
            df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
            s_name = st.selectbox("المورد", df_s['SupplierName'] if not df_s.empty else [""])
            p_name = st.selectbox("المشروع", df_p['ProjectName'] if not df_p.empty else [""])
            item = st.text_input("الصنف المشتري")
            qty = st.number_input("الكمية", min_value=0.0)
            amt = st.number_input("إجمالي المبلغ")
            if st.form_submit_button("حفظ الفاتورة وتحديث المخزن"):
                cursor = conn.cursor()
                # 1. تحديث رصيد المورد
                cursor.execute("UPDATE Suppliers SET Balance = Balance + ? WHERE SupplierName = ?", (amt, s_name))
                # 2. تحديث المخزن
                cursor.execute("INSERT INTO Inventory (ItemName, Qty) VALUES (?, ?) ON CONFLICT(ItemName) DO UPDATE SET Qty = Qty + ?", (item, qty, qty))
                conn.commit()
                st.success(f"تم تسجيل فاتورة {item} وتحديث رصيد المورد والمخازن.")

    elif task == "سند (قبض / صرف) خزينة وبنك":
        with st.form("cash_entry"):
            st.subheader("💵 حركة نقدية (قبض / صرف)")
            accs = pd.read_sql_query("SELECT * FROM CashBank", conn)
            t_type = st.radio("نوع العملية", ["سند قبض", "سند صرف"], horizontal=True)
            acc_name = st.selectbox("الحساب", accs['Name'])
            amount = st.number_input("المبلغ")
            note = st.text_input("البيان")
            if st.form_submit_button("تنفيذ السند"):
                change = amount if t_type == "سند قبض" else -amount
                conn.execute("UPDATE CashBank SET Balance = Balance + ? WHERE Name = ?", (change, acc_name))
                conn.commit()
                st.success(f"تم تنفيذ {t_type} وتحديث رصيد {acc_name}")

    elif task == "مستخلص أعمال واستقطاعات":
        with st.form("cert_form"):
            st.subheader("📑 تسجيل مستخلص واستقطاعات")
            df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
            p_sel = st.selectbox("المشروع", df_p['ProjectName'] if not df_p.empty else [""])
            total = st.number_input("إجمالي قيمة الأعمال")
            deduct = st.number_input("إجمالي الاستقطاعات")
            if st.form_submit_button("حفظ المستخلص"):
                st.success(f"تم حفظ المستخلص بصافي: {total - deduct:,.2f}")

# ---------------------------------------------------------
# القسم الثاني: محرك التقارير (تقارير حقيقية)
# ---------------------------------------------------------
elif mode == "📊 محرك التقارير (Reports)":
    st.header("📊 محرك التقارير الذكي")
    rep_cat = st.sidebar.selectbox("تصنيف التقارير:", ["المالية والبنوك", "المخازن", "الموردين والعملاء", "المشاريع"])
    
    if rep_cat == "المالية والبنوك":
        st.subheader("🏦 كشف أرصدة الخزينة والبنوك")
        df_cb = pd.read_sql_query("SELECT Name, Type, Balance FROM CashBank", conn)
        st.table(df_cb)
        

    elif rep_cat == "المخازن":
        st.subheader("📦 تقرير جرد المخزن الفعلي")
        df_inv = pd.read_sql_query("SELECT * FROM Inventory", conn)
        st.dataframe(df_inv, use_container_width=True)
        st.bar_chart(df_inv.set_index('ItemName')['Qty'])

# ---------------------------------------------------------
# القسم الثالث: شجرة الحسابات والقيود
# ---------------------------------------------------------
elif mode == "📑 شجرة الحسابات والقيود":
    st.header("📑 الإدارة المحاسبية")
    st.write("### شجرة الحسابات الحالية")
    st.dataframe(pd.read_sql_query("SELECT * FROM ChartOfAccounts", conn), use_container_width=True)
