import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات الشاملة (MNSA ERP)
def init_db():
    conn = sqlite3.connect('mnsa_erp_final.db')
    cursor = conn.cursor()
    # جداول النظام - إنشاء الجداول إذا لم تكن موجودة
    cursor.execute('CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Location TEXT, Budget DECIMAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS ProjectBOM (BOMID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, ItemName TEXT, Quantity DECIMAL, Unit TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Suppliers (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Contact TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Purchases (PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, Amount DECIMAL, Description TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Employees (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary DECIMAL)')
    conn.commit()
    return conn

conn = init_db()

# 2. إعداد واجهة التطبيق
st.set_page_config(page_title="MNSA ERP System", layout="wide")

# تصميم القائمة الجانبية (هنا تظهر القائمة مرة واحدة فقط)
st.sidebar.title("🏗️ شركة MNSA")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox("القائمة الرئيسية", [
    "📊 لوحة التحكم المالية",
    "🏢 إدارة المشاريع",
    "📋 مقايسات البنود (BOM)",
    "👷 إدارة الموردين",
    "💰 المشتريات والمصروفات",
    "👥 شؤون الموظفين والرواتب"
])

# --- 1. لوحة التحكم المالية ---
if menu == "📊 لوحة التحكم المالية":
    st.header("📊 تحليل الأداء المالي للأعمال")
    df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not df_p.empty:
        for _, row in df_p.iterrows():
            with st.expander(f"📉 مشروع: {row['ProjectName']}"):
                p_id = row['ProjectID']
                df_exp = pd.read_sql_query(f"SELECT SUM(Amount) as total FROM Purchases WHERE ProjectID = {p_id}", conn)
                expenses = df_exp['total'][0] or 0
                budget = row['Budget'] or 0
                remaining = budget - expenses
                
                c1, c2, c3 = st.columns(3)
                c1.metric("الميزانية المرصودة", f"{budget:,.2f}")
                c2.metric("إجمالي المصروفات", f"{expenses:,.2f}", delta=f"-{expenses:,.2f}", delta_color="inverse")
                c3.metric("المتبقي (الربح)", f"{remaining:,.2f}")
                
                progress = min(expenses/budget, 1.0) if budget > 0 else 0
                st.progress(progress, text=f"نسبة الاستهلاك: {progress*100:.1f}%")
    else:
        st.info("لا توجد مشاريع مسجلة حالياً.")

# --- 2. إدارة المشاريع ---
elif menu == "🏢 إدارة المشاريع":
    st.header("🏢 تسجيل وإدارة المشاريع")
    with st.form("p_form"):
        name = st.text_input("اسم المشروع")
        loc = st.text_input("الموقع")
        bud = st.number_input("الميزانية التقديرية", min_value=0.0)
        if st.form_submit_button("حفظ المشروع"):
            if name:
                conn.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?, ?, ?)", (name, loc, bud))
                conn.commit()
                st.success("✅ تم حفظ المشروع")
                st.rerun()

# --- 3. مقايسات البنود (BOM) ---
elif menu == "📋 مقايسات البنود (BOM)":
    st.header("📋 حصر الكميات والمواد")
    projs = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not projs.empty:
        sel_p = st.selectbox("اختر المشروع", projs['ProjectName'])
        p_id = projs[projs['ProjectName']==sel_p]['ProjectID'].values[0]
        with st.form("bom_form"):
            item = st.text_input("بيان البند/المادة")
            qty = st.number_input("الكمية")
            unit = st.selectbox("الوحدة", ["م3", "طن", "م.ط", "م2", "عدد"])
            if st.form_submit_button("إضافة للمقايسة"):
                conn.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", (int(p_id), item, qty, unit))
                conn.commit()
                st.success("تمت الإضافة")
        
        df_bom = pd.read_sql_query(f"SELECT ItemName, Quantity, Unit FROM ProjectBOM WHERE ProjectID={p_id}", conn)
        st.dataframe(df_bom, use_container_width=True)
    else:
        st.warning("يجب إضافة مشروع أولاً")

# --- 4. إدارة الموردين ---
elif menu == "👷 إدارة الموردين":
    st.header("👷 سجل الموردين ومقاولي الباطن")
    with st.form("s_form"):
        s_name = st.text_input("اسم المورد")
        s_contact = st.text_input("بيانات الاتصال")
        if st.form_submit_button("إضافة المورد"):
            conn.execute("INSERT INTO Suppliers (SupplierName, Contact) VALUES (?, ?)", (s_name, s_contact))
            conn.commit()
            st.success("تم التسجيل")
    st.dataframe(pd.read_sql_query("SELECT * FROM Suppliers", conn), use_container_width=True)

# --- 5. المشتريات والمصروفات ---
elif menu == "💰 المشتريات والمصروفات":
    st.header("💰 تسجيل الفواتير والمصروفات")
    projs = pd.read_sql_query("SELECT * FROM Projects", conn)
    supps = pd.read_sql_query("SELECT * FROM Suppliers", conn)
    if not projs.empty:
        with st.form("buy_form"):
            p_sel = st.selectbox("المشروع المحمل عليه المصرف", projs['ProjectName'])
            s_sel = st.selectbox("المورد", supps['SupplierName'] if not supps.empty else ["مورد عام"])
            amt = st.number_input("قيمة الفاتورة")
            desc = st.text_input("وصف المصروف")
            if st.form_submit_button("تسجيل المصرف"):
                p_id = projs[projs['ProjectName']==p_sel]['ProjectID'].values[0]
                conn.execute("INSERT INTO Purchases (ProjectID, Amount, Description) VALUES (?, ?, ?)", (int(p_id), amt, desc))
                conn.commit()
                st.success("✅ تم تحديث ميزانية المشروع")
    else:
        st.warning("أضف مشاريع لتتمكن من تسجيل مصروفات")

# --- 6. شؤون الموظفين والرواتب ---
elif menu == "👥 شؤون الموظفين والرواتب":
    st.header("👥 إدارة الموظفين واليوميات")
    with st.form("e_form"):
        e_name = st.text_input("اسم الموظف")
        job = st.text_input("المسمى الوظيفي")
        sal = st.number_input("الراتب/اليومية")
        if st.form_submit_button("حفظ بيانات الموظف"):
            conn.execute("INSERT INTO Employees (EmployeeName, JobTitle, Salary) VALUES (?, ?, ?)", (e_name, job, sal))
            conn.commit()
            st.success("تم الحفظ")
    st.dataframe(pd.read_sql_query("SELECT * FROM Employees", conn), use_container_width=True)
