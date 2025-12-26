import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. بناء قاعدة البيانات (كافة الجداول المطلوبة بدقة) ---
def init_db():
    conn = sqlite3.connect('mnsa_ultimate_system_2025.db')
    cursor = conn.cursor()
    # المحاسبة والمالية
    cursor.execute('CREATE TABLE IF NOT EXISTS ChartOfAccounts (AccID INTEGER PRIMARY KEY, AccName TEXT, AccType TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS JournalEntries (EntryID INTEGER PRIMARY KEY AUTOINCREMENT, Date TEXT, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS CashBank (AccountID INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT, Type TEXT, Balance REAL)')
    
    # الأشخاص والمخازن
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Contact TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Customers (CustomerID INTEGER PRIMARY KEY AUTOINCREMENT, CustomerName TEXT, Contact TEXT, Balance REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Inventory (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, Qty REAL, Unit TEXT)')
    
    # المشتريات والمستخلصات
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Budget REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, Total REAL, Description TEXT, Date TEXT)')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Certificates 
                      (CertID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, TotalAmount REAL, Deductions REAL, NetAmount REAL, Status TEXT)''')
    
    conn.commit()
    return conn

conn = init_db()

# --- 2. إعداد واجهة البرنامج ---
st.set_page_config(page_title="MNSA ERP - Search & Entry", layout="wide")

# --- 3. محرك التنقل الرئيسي ---
st.sidebar.title("🏗️ نظام MNSA الموحد")
menu = st.sidebar.selectbox("اختر المحرك:", ["📥 محرك الإدخال", "🔍 محرك البحث والتقارير"])

# ---------------------------------------------------------
# القسم الأول: محرك الإدخال (Entry Engine)
# ---------------------------------------------------------
if menu == "📥 محرك الإدخال":
    st.header("📥 إدخال البيانات للجدول")
    target_table = st.selectbox("اختر الجدول المستهدف:", 
                                ["الموردين", "العملاء", "المخازن", "المشاريع", "المشتريات", "سندات نقدية"])
    
    st.markdown("---")
    
    if target_table == "الموردين":
        with st.form("supp_form"):
            name = st.text_input("اسم المورد")
            contact = st.text_input("رقم الهاتف")
            if st.form_submit_button("إضافة للموردين"):
                conn.execute("INSERT INTO Suppliers (SupplierName, Contact) VALUES (?,?)", (name, contact))
                conn.commit()
                st.success("تم الحفظ")

    elif target_table == "المخازن":
        with st.form("inv_form"):
            item = st.text_input("اسم الصنف")
            qty = st.number_input("الكمية")
            unit = st.selectbox("الوحدة", ["م3", "طن", "عدد"])
            if st.form_submit_button("تحديث المخزن"):
                conn.execute("INSERT INTO Inventory (ItemName, Qty, Unit) VALUES (?,?,?) ON CONFLICT(ItemName) DO UPDATE SET Qty = Qty + ?", (item, qty, unit, qty))
                conn.commit()
                st.success("تم التحديث")

# ---------------------------------------------------------
# القسم الثاني: محرك البحث (Search Engine)
# ---------------------------------------------------------
elif menu == "🔍 محرك البحث والتقارير":
    st.header("🔍 محرك البحث في قاعدة البيانات")
    
    search_table = st.selectbox("ابحث في جدول:", 
                                ["Suppliers", "Customers", "Inventory", "Projects", "Purchases", "Certificates"])
    
    # واجهة البحث الذكي
    search_query = st.text_input(f"اكتب اسم أو بيان للبحث في جدول {search_table}...")
    
    # سحب البيانات بناءً على البحث
    df = pd.read_sql_query(f"SELECT * FROM {search_table}", conn)
    
    if search_query:
        # فلترة البيانات برمجياً بناءً على نص البحث
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_filtered = df[mask]
    else:
        df_filtered = df

    st.subheader(f"نتائج جدول {search_table}")
    st.dataframe(df_filtered, use_container_width=True)
    
    # إحصائيات سريعة للجدول الظاهر
    if not df_filtered.empty:
        st.write(f"عدد السجلات المكتشفة: {len(df_filtered)}")
        if 'Balance' in df_filtered.columns or 'Total' in df_filtered.columns:
            total_val = df_filtered.iloc[:, -1].sum() # افتراض أن القيمة المالية في آخر عمود
            st.info(f"إجمالي القيم المالية في هذا البحث: {total_val:,.2f} ج.م")

# --- تذييل الصفحة ---
st.sidebar.markdown("---")
if st.sidebar.button("🔄 تحديث النظام"):
    st.rerun()
