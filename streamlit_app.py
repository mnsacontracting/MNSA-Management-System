import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. بناء قاعدة البيانات المتكاملة (كافة الجداول) ---
def init_db():
    conn = sqlite3.connect('mnsa_ultimate_system_2025.db')
    cursor = conn.cursor()
    # المحاسبة
    cursor.execute('CREATE TABLE IF NOT EXISTS ChartOfAccounts (AccID INTEGER PRIMARY KEY, AccName TEXT, AccType TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS JournalEntries (EntryID INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS EntryDetails (DetailID INTEGER PRIMARY KEY AUTOINCREMENT, EntryID INTEGER, AccID INTEGER, Debit REAL, Credit REAL, ProjectID INTEGER)')
    # المالية
    cursor.execute('CREATE TABLE IF NOT EXISTS CashBank (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, Type TEXT, Balance REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Checks (CheckID INTEGER PRIMARY KEY AUTOINCREMENT, CheckNum TEXT, DueDate TEXT, Amount REAL, Status TEXT, Type TEXT)')
    # المشتريات والمخازن
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, Qty REAL, Unit TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, Total REAL, Description TEXT, Date TEXT)')
    # المشاريع والموظفين
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Budget REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL)')
    
    # بيانات أساسية
    cursor.execute("SELECT COUNT(*) FROM ChartOfAccounts")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ChartOfAccounts VALUES (?,?,?)", 
                           [(101, 'الخزينة', 'Asset'), (102, 'البنك', 'Asset'), (103, 'المخزون', 'Asset'), (201, 'الموردين', 'Liability')])
        cursor.executemany("INSERT INTO CashBank (Name, Type, Balance) VALUES (?,?,?)", [('الخزينة الرئيسية', 'Cash', 0), ('البنك الأهلي', 'Bank', 0)])
    conn.commit()
    return conn

conn = init_db()

# --- 2. واجهة البرنامج ---
st.set_page_config(page_title="MNSA ERP Professional", layout="wide")
st.sidebar.title("🏗️ شركة MNSA")
main_menu = st.sidebar.selectbox("المحرك الرئيسي:", ["📥 المدخلات والعمليات", "📊 التقارير الذكية", "📑 المالية والقيد"])

# ---------------------------------------------------------
# القسم الأول: المدخلات والعمليات (الخزينة، المخازن، المشتريات)
# ---------------------------------------------------------
if main_menu == "📥 المدخلات والعمليات":
    tab_op = st.selectbox("نوع العملية:", ["سندات (قبض/صرف)", "فاتورة مشتريات", "توريد/صرف مخازن", "بيانات أساسية"])
    
    if tab_op == "سندات (قبض/صرف)":
        st.subheader("💵 إدارة السيولة (سند قبض وصرف)")
        with st.form("cash_form"):
            accs = pd.read_sql_query("SELECT * FROM CashBank", conn)
            mode = st.radio("نوع السند", ["سند قبض", "سند صرف"], horizontal=True)
            acc_name = st.selectbox("من/إلى حساب", accs['Name'])
            amount = st.number_input("المبلغ", min_value=0.0)
            note = st.text_input("البيان/السبب")
            if st.form_submit_button("تنفيذ السند"):
                change = amount if mode == "سند قبض" else -amount
                conn.execute("UPDATE CashBank SET Balance = Balance + ? WHERE Name = ?", (change, acc_name))
                conn.commit()
                st.success(f"تم تنفيذ {mode} بنجاح. رصيد الحساب المحدث: {acc_name}")

    elif tab_op == "فاتورة مشتريات":
        st.subheader("🛒 تسجيل مشتريات وتحديث موردين")
        with st.form("purch_form"):
            supps = pd.read_sql_query("SELECT * FROM Suppliers", conn)
            projs = pd.read_sql_query("SELECT * FROM Projects", conn)
            s_name = st.selectbox("المورد", supps['SupplierName'] if not supps.empty else [""])
            p_name = st.selectbox("المشروع", projs['ProjectName'] if not projs.empty else [""])
            total = st.number_input("إجمالي الفاتورة")
            if st.form_submit_button("حفظ الفاتورة"):
                conn.execute("UPDATE Suppliers SET Balance = Balance + ? WHERE SupplierName = ?", (total, s_name))
                conn.commit()
                st.success("تم تسجيل الفاتورة وتحديث مديونية المورد.")

    elif tab_op == "توريد/صرف مخازن":
        st.subheader("📦 حركة المخازن")
        with st.form("inv_form"):
            m = st.radio("العملية", ["إضافة للمخزن (توريد)", "صرف من المخزن"], horizontal=True)
            item = st.text_input("اسم الصنف")
            q = st.number_input("الكمية")
            if st.form_submit_button("تحديث المخزن"):
                change = q if m == "إضافة للمخزن (توريد)" else -q
                cursor = conn.cursor()
                cursor.execute("SELECT Qty FROM Inventory WHERE ItemName = ?", (item,))
                res = cursor.fetchone()
                if res:
                    cursor.execute("UPDATE Inventory SET Qty = Qty + ? WHERE ItemName = ?", (change, item))
                else:
                    cursor.execute("INSERT INTO Inventory (ItemName, Qty, Unit) VALUES (?,?,?)", (item, q, 'وحدة'))
                conn.commit()
                st.success(f"تم تحديث مخزن {item} بنجاح.")

# ---------------------------------------------------------
# القسم الثاني: محرك التقارير (تقارير مالية ومخازن حقيقية)
# ---------------------------------------------------------
elif main_menu == "📊 التقارير الذكية":
    st.header("📊 محرك التقارير الشامل")
    rep_cat = st.sidebar.selectbox("فئة التقارير:", ["المالية والبنوك", "جرد المخازن", "الموردين والعملاء"])
    
    if rep_cat == "المالية والبنوك":
        st.subheader("🏦 أرصدة الخزينة والبنوك اللحظية")
        df_bal = pd.read_sql_query("SELECT Name, Type, Balance FROM CashBank", conn)
        st.table(df_bal)
        

    elif rep_cat == "جرد المخازن":
        st.subheader("📦 تقرير جرد الأصناف")
        df_inv = pd.read_sql_query("SELECT ItemName, Qty, Unit FROM Inventory", conn)
        st.dataframe(df_inv, use_container_width=True)
        st.bar_chart(df_inv.set_index('ItemName')['Qty'])

# ---------------------------------------------------------
# القسم الثالث: الحسابات والقيد
# ---------------------------------------------------------
elif main_menu == "📑 المالية والقيد":
    st.header("📑 شجرة الحسابات والقيود")
    tab_acc = st.tabs(["🌳 شجرة الحسابات", "🖋️ قيد يدوي"])
    with tab_acc[0]:
        st.dataframe(pd.read_sql_query("SELECT * FROM ChartOfAccounts", conn), use_container_width=True)
