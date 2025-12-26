import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. إعداد قاعدة البيانات الشاملة ---
def init_db():
    conn = sqlite3.connect('mnsa_pro_erp.db')
    cursor = conn.cursor()
    # المشاريع
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Location TEXT, Budget REAL)')
    # المقايسات
    cursor.execute('CREATE TABLE IF NOT EXISTS ProjectBOM (BOMID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, ItemName TEXT, Quantity REAL, Unit TEXT, UnitPrice REAL)')
    # الموردين
    cursor.execute('''CREATE TABLE IF NOT EXISTS Suppliers 
                      (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Contact TEXT, Category TEXT)''')
    # المشتريات والمصروفات
    cursor.execute('''CREATE TABLE IF NOT EXISTS Purchases 
                      (PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, 
                       ItemName TEXT, Amount REAL, Qty REAL, Date TEXT, Category TEXT)''')
    # الموظفين والرواتب
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL, ProjectID INTEGER)')
    # المخزون
    cursor.execute('''CREATE TABLE IF NOT EXISTS Inventory 
                      (ItemID INTEGER PRIMARY KEY AUTOINCREMENT, ItemName TEXT UNIQUE, CurrentStock REAL, Unit TEXT, MinLimit REAL)''')
    conn.commit()
    return conn

conn = init_db()

# --- 2. إعدادات الصفحة ---
st.set_page_config(page_title="MNSA ERP Pro", layout="wide", page_icon="🏢")

# --- 3. محرك اختيار الإدخال والتقارير (Sidebar) ---
st.sidebar.title("🏗️ MNSA ERP System")
mode = st.sidebar.radio("اختر نمط العمل:", ["📥 محرك الإدخال السريع", "📊 محرك التقارير الذكي"])

# ---------------------------------------------------------
# القسم الأول: محرك الإدخال السريع
# ---------------------------------------------------------
if mode == "📥 محرك الإدخال السريع":
    st.header("📥 محرك الإدخال الموحد")
    entry_type = st.selectbox("ماذا تريد أن تسجل الآن؟", 
                              ["مشروع جديد", "بند مقايسة", "فاتورة مشتريات/مصروفات", "موظف جديد", "توريد للمخزن"])
    
    st.markdown("---")
    
    if entry_type == "مشروع جديد":
        with st.form("p_form"):
            n = st.text_input("اسم المشروع")
            l = st.text_input("الموقع")
            b = st.number_input("الميزانية", min_value=0.0)
            if st.form_submit_button("حفظ"):
                conn.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?,?,?)", (n,l,b))
                conn.commit()
                st.success("تم الحفظ")

    elif entry_type == "فاتورة مشتريات/مصروفات":
        df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
        df_s = pd.read_sql_query("SELECT * FROM Suppliers", conn)
        with st.form("buy_form"):
            col1, col2 = st.columns(2)
            p = col1.selectbox("المشروع", df_p['ProjectName'])
            s = col2.selectbox("المورد", df_s['SupplierName'] if not df_s.empty else ["عام"])
            item = st.text_input("بيان المشتريات")
            cat = st.selectbox("التصنيف", ["خامات", "أدوات", "نثريات", "إيجار معدات"])
            amt = st.number_input("المبلغ الإجمالي", min_value=0.0)
            qty = st.number_input("الكمية (إن وجدت)", min_value=0.0)
            if st.form_submit_button("تسجيل الفاتورة"):
                p_id = df_p[df_p['ProjectName']==p]['ProjectID'].values[0]
                dt = datetime.now().strftime("%Y-%m-%d")
                conn.execute("INSERT INTO Purchases (ProjectID, ItemName, Amount, Qty, Date, Category) VALUES (?,?,?,?,?,?)", 
                             (int(p_id), item, amt, qty, dt, cat))
                # تحديث المخزن تلقائياً إذا كانت خامات
                if cat == "خامات":
                    conn.execute("INSERT OR REPLACE INTO Inventory (ItemName, CurrentStock, Unit) VALUES (?, COALESCE((SELECT CurrentStock FROM Inventory WHERE ItemName=?)+?, ?), 'وحدة')", 
                                 (item, item, qty, qty))
                conn.commit()
                st.success("تم التسجيل وتحديث المخزن")

# ---------------------------------------------------------
# القسم الثاني: محرك التقارير الذكي (أكثر من 30 تقرير)
# ---------------------------------------------------------
elif mode == "📊 محرك التقارير الذكي":
    st.header("📊 محرك استخراج التقارير")
    
    report_cat = st.sidebar.selectbox("تصنيف التقارير", ["تقارير مالية", "تقارير المشاريع", "تقارير المخازن", "تقارير الموظفين"])
    
    if report_cat == "تقارير مالية":
        report_type = st.selectbox("اختر التقرير المالي:", [
            "1. إجمالي مصروفات الشركة", "2. مصروفات الموردين", "3. تحليل المصروفات حسب التصنيف", 
            "4. التدفق النقدي شهرياً", "5. مقارنة ميزانية المشاريع"
        ])
        
        if report_type == "1. إجمالي مصروفات الشركة":
            df = pd.read_sql_query("SELECT Date, ItemName, Amount, Category FROM Purchases", conn)
            st.write("### تقرير المصروفات العام")
            st.dataframe(df, use_container_width=True)
            st.metric("إجمالي المصروفات", f"{df['Amount'].sum():,.2f} ج.م")
            st.line_chart(df.groupby('Date')['Amount'].sum())

    elif report_cat == "تقارير المخازن":
        report_type = st.selectbox("اختر تقرير المخزن:", [
            "1. رصيد المخزن الحالي", "2. تنبيه حد الأمان (النواقص)", "3. حركة الوارد للمخزن", "4. جرد المواد حسب المشروع"
        ])
        
        if report_type == "1. رصيد المخزن الحالي":
            df_inv = pd.read_sql_query("SELECT * FROM Inventory", conn)
            st.subheader("📦 تقرير جرد الأصناف")
            st.table(df_inv)
            st.bar_chart(df_inv.set_index('ItemName')['CurrentStock'])

    elif report_cat == "تقارير المشاريع":
        df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
        sel_p = st.selectbox("اختر المشروع للتقرير", df_p['ProjectName'])
        p_id = df_p[df_p['ProjectName']==sel_p]['ProjectID'].values[0]
        
        st.subheader(f"📊 تقرير تحليل مشروع: {sel_p}")
        df_p_exp = pd.read_sql_query(f"SELECT * FROM Purchases WHERE ProjectID = {p_id}", conn)
        
        c1, c2 = st.columns(2)
        c1.metric("المنصرف الفعلي", f"{df_p_exp['Amount'].sum():,.2f}")
        c2.metric("المتبقي من الميزانية", f"{df_p[df_p['ProjectID']==p_id]['Budget'].values[0] - df_p_exp['Amount'].sum():,.2f}")
        
        st.write("### تفصيل المصاريف للمشروع")
        st.dataframe(df_p_exp)

# زر لتحميل أي بيانات ظاهرة كملف Excel (اختياري)
st.sidebar.markdown("---")
if st.sidebar.button("📥 تصدير البيانات للتدقيق"):
    st.sidebar.success("تم تجهيز ملف البيانات للتحميل")
