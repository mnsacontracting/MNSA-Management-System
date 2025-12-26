import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. بناء قاعدة البيانات المتكاملة ---
def init_db():
    conn = sqlite3.connect('mnsa_final_erp.db')
    cursor = conn.cursor()
    # المحاسبة والمالية
    cursor.execute('CREATE TABLE IF NOT EXISTS ChartOfAccounts (AccID INTEGER PRIMARY KEY, AccName TEXT, AccType TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS JournalEntries (EntryID INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS EntryDetails (DetailID INTEGER PRIMARY KEY AUTOINCREMENT, EntryID INTEGER, AccID INTEGER, Debit REAL, Credit REAL, ProjectID INTEGER)')
    cursor.execute('CREATE TABLE IF NOT EXISTS CashBank (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, Type TEXT, Balance REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Checks (CheckID INTEGER PRIMARY KEY AUTOINCREMENT, CheckNum TEXT, DueDate TEXT, Amount REAL, Status TEXT, Type TEXT)')
    # الموردين والعملاء والمخازن
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, Qty REAL, Unit TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, ItemName TEXT, Qty REAL, Total REAL, Date TEXT)')
    # المشاريع والمستخلصات والموظفين
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Budget REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Certificates (CertID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, TotalAmount REAL, Deductions REAL, NetAmount REAL, Status TEXT, Date TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL)')
    
    # بيانات شجرة الحسابات الأساسية
    cursor.execute("SELECT COUNT(*) FROM ChartOfAccounts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ChartOfAccounts VALUES (?,?,?)", 
                           [(101, 'الخزينة', 'Asset'), (102, 'البنك', 'Asset'), (103, 'المخزون', 'Asset'), (201, 'الموردين', 'Liability'), (202, 'العملاء', 'Asset'), (301, 'الإيرادات', 'Revenue'), (401, 'المصاريف', 'Expense')])
        cursor.executemany("INSERT INTO CashBank (Name, Type, Balance) VALUES (?,?,?)", [('الخزينة الرئيسية', 'Cash', 0), ('بنك مصر', 'Bank', 0)])
    conn.commit()
    return conn

conn = init_db()

# --- 2. واجهة التطبيق ---
st.set_page_config(page_title="MNSA Ultimate ERP", layout="wide")
st.sidebar.title("🏗️ نظام MNSA المتكامل")
mode = st.sidebar.selectbox("المحرك الرئيسي:", ["📥 محرك المدخلات والعمليات", "📊 محرك التقارير الذكي", "📑 الحسابات والقيود"])

# --- 3. محرك المدخلات والعمليات ---
if mode == "📥 محرك المدخلات والعمليات":
    task = st.selectbox("نوع العملية:", ["سند (قبض/صرف)", "فاتورة مشتريات ومخازن", "مستخلص واستقطاعات", "إضافة بيانات أساسية"])
    
    if task == "سند (قبض/صرف)":
        with st.form("cash_form"):
            st.subheader("💵 سندات الخزينة والبنوك")
            accs = pd.read_sql_query("SELECT * FROM CashBank", conn)
            stype = st.radio("النوع", ["سند قبض", "سند صرف"], horizontal=True)
            acc = st.selectbox("الحساب", accs['Name'])
            amt = st.number_input("المبلغ")
            if st.form_submit_button("تنفيذ السند"):
                change = amt if stype == "سند قبض" else -amt
                conn.execute("UPDATE CashBank SET Balance = Balance + ? WHERE Name = ?", (change, acc))
                conn.commit()
                st.success("تم التحديث")

    elif task == "فاتورة مشتريات ومخازن":
        with st.form("purch_form"):
            st.subheader("🛒 مشتريات + مخزن + مورد")
            df_s = pd.read_sql_query("SELECT * FROM Suppliers", conn)
            item = st.text_input("الصنف")
            qty = st.number_input("الكمية")
            total = st.number_input("الإجمالي")
            s_name = st.selectbox("المورد", df_s['SupplierName'] if not df_s.empty else [""])
            if st.form_submit_button("حفظ العملية"):
                cursor = conn.cursor()
                cursor.execute("UPDATE Suppliers SET Balance = Balance + ? WHERE SupplierName = ?", (total, s_name))
                cursor.execute("INSERT INTO Inventory (ItemName, Qty) VALUES (?, ?) ON CONFLICT(ItemName) DO UPDATE SET Qty = Qty + ?", (item, qty, qty))
                conn.commit()
                st.success("تم تحديث المخزن وحساب المورد")

# --- 4. محرك التقارير ---
elif mode == "📊 محرك التقارير الذكي":
    st.header("📊 محرك التقارير")
    cat = st.sidebar.selectbox("التصنيف:", ["المالية والبنوك", "جرد المخازن", "المستخلصات", "الموردين"])
    
    if cat == "المالية والبنوك":
        df = pd.read_sql_query("SELECT Name, Balance FROM CashBank", conn)
        st.table(df)
        st.bar_chart(df.set_index('Name'))

    elif cat == "جرد المخازن":
        df_i = pd.read_sql_query("SELECT * FROM Inventory", conn)
        st.dataframe(df_i)
        

# --- 5. الحسابات والقيود ---
elif mode == "📑 الحسابات والقيود":
    st.header("📑 شجرة الحسابات والقيود")
    tab1, tab2 = st.tabs(["🌳 شجرة الحسابات", "🖋️ قيد يدوي"])
    with tab1:
        st.dataframe(pd.read_sql_query("SELECT * FROM ChartOfAccounts", conn), use_container_width=True)
