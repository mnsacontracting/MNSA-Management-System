import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات وتأمين الجداول
def init_db():
    conn = sqlite3.connect('mnsa_erp_final.db')
    cursor = conn.cursor()
    
    # جدول المشاريع
    cursor.execute('''CREATE TABLE IF NOT EXISTS Projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectName TEXT NOT NULL,
        Location TEXT,
        Budget DECIMAL(18, 2))''')
    
    # جدول المقايسة (BOM)
    cursor.execute('''CREATE TABLE IF NOT EXISTS ProjectBOM (
        BOMID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectID INTEGER,
        ItemName TEXT,
        Quantity DECIMAL(18, 2),
        Unit TEXT,
        FOREIGN KEY (ProjectID) REFERENCES Projects (ProjectID))''')
    
    # جدول الموردين
    cursor.execute('''CREATE TABLE IF NOT EXISTS Suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierName TEXT NOT NULL,
        Contact TEXT)''')
    
    # جدول المشتريات والمصروفات
    cursor.execute('''CREATE TABLE IF NOT EXISTS Purchases (
        PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectID INTEGER,
        SupplierID INTEGER,
        Amount DECIMAL(18, 2),
        Description TEXT,
        Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ProjectID) REFERENCES Projects (ProjectID),
        FOREIGN KEY (SupplierID) REFERENCES Suppliers (SupplierID))''')
    
    conn.commit()
    return conn

conn = init_db()

# 2. إعداد واجهة التطبيق
st.set_page_config(page_title="MNSA ERP System", layout="wide", initial_sidebar_state="expanded")

# تصميم القائمة الجانبية
st.sidebar.title("🏗️ شركة MNSA")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox("القائمة الرئيسية", [
    "📊 لوحة التحكم المالية",
    "🏢 إدارة المشاريع",
    "📋 مقايسات البنود (BOM)",
    "👷 إدارة الموردين",
    "💰 المشتريات والمصروفات"
])

# --- 1. لوحة التحكم المالية (تقرير الأرباح والخسائر) ---
if menu == "📊 لوحة التحكم المالية":
    st.header("📊 تحليل أداء المشاريع والأرباح")
    df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    if not df_p.empty:
        for _, row in df_p.iterrows():
            p_id = row['ProjectID']
            # حساب إجمالي المصروفات
            df_exp = pd.read_sql_query(f"SELECT SUM(Amount) as total FROM Purchases WHERE ProjectID = {p_id}", conn)
            expenses = df_exp['total'][0] or 0
            budget = row['Budget']
            remaining = budget - expenses
            
            with st.container():
                st.subheader(f"🏗️ مشروع: {row['ProjectName']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("الميزانية المرصودة", f"{budget:,.2f} ج.م")
                c2.metric("إجمالي المصروفات", f"{expenses:,.2f} ج.م", delta=f"-{expenses:,.2f}", delta_color="inverse")
                c3.metric("المتبقي (الربح التقديري)", f"{remaining:,.2f} ج.م")
                
                # شريط تقدم استهلاك الميزانية
                progress = min(expenses / budget, 1.0) if budget > 0 else 0
                st.progress(progress, text=f"نسبة استهلاك الميزانية: {progress*100:.1f}%")
                st.markdown("---")
    else:
        st.info("لا توجد مشاريع مسجلة حالياً. ابدأ بإضافة مشروع من القائمة الجانبية.")

# --- 2. إدارة المشاريع ---
elif menu == "🏢 إدارة المشاريع":
    st.header("🏢 تسجيل مشروع جديد")
    with st.form("project_form"):
        name = st.text_input("اسم المشروع")
        location = st.text_input("موقع المشروع")
        budget = st.number_input("الميزانية التقديرية (ج.م)", min_value=0.0)
        if st.form_submit_button("حفظ المشروع"):
            if name:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?, ?, ?)", (name, location, budget))
                conn.commit()
                st.success("✅ تم حفظ المشروع بنجاح!")
                st.rerun()
            else:
                st.error("يرجى إدخال اسم المشروع.")

# --- 3. مقايسات البنود (BOM) ---
elif menu == "📋 مقايسات البنود (BOM)":
    st.header("📋 حصر كميات بنود الأعمال")
    projects_df = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    if not projects_df.empty:
        sel_project = st.selectbox("اختر المشروع", projects_df['ProjectName'])
        p_id = projects_df[projects_df['ProjectName'] == sel_project]['ProjectID'].values[0]
        
        with st.expander("➕ إضافة بند جديد للمقايسة"):
            col1, col2, col3 = st.columns(3)
            item_name = col1.text_input("بيان العمل")
            qty = col2.number_input("الكمية", min_value=0.0)
            unit = col3.selectbox("الوحدة", ["م3", "طن", "م.ط", "م2", "عدد", "مقطوعية"])
            
            if st.button("إضافة للمقايسة"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", (int(p_id), item_name, qty, unit))
                conn.commit()
                st.success("✅ تم إضافة البند")
        
        # عرض المقايسة الحالية
        df_bom = pd.read_sql_query(f"SELECT ItemName as البند, Quantity as الكمية, Unit as الوحدة FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
        st.write(f"المقايسة الحالية لمشروع {sel_project}:")
        st.dataframe(df_bom, use_container_width=True)
    else:
        st.warning("يرجى إضافة مشروع أولاً.")

# --- 4. إدارة الموردين ---
elif menu == "👷 إدارة الموردين":
    st.header("👷 سجل الموردين ومقاولي الباطن")
    with st.form("supplier_form"):
        s_name = st.text_input("اسم الشركة / المورد")
        s_contact = st.text_input("بيانات الاتصال (هاتف/عنوان)")
        if st.form_submit_button("إضافة المورد"):
            if s_name:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Suppliers (SupplierName, Contact) VALUES (?, ?)", (s_name, s_contact))
                conn.commit()
                st.success(f"✅ تم تسجيل {s_name}")
                st.rerun()
    
    st.subheader("قائمة الموردين")
    df_supp = pd.read_sql_query("SELECT * FROM Suppliers", conn)
    st.dataframe(df_supp, use_container_width=True)

# --- 5. المشتريات والمصروفات ---
elif menu == "💰 المشتريات والمصروفات":
    st.header("💰 تسجيل حركات الشراء والمصاريف")
    projects_df = pd.read_sql_query("SELECT * FROM Projects", conn)
    suppliers_df = pd.read_sql_query("SELECT * FROM Suppliers", conn)
    
    if not projects_df.empty and not suppliers_df.empty:
        with st.form("purchase_form"):
            p_sel = st.selectbox("تخصيص لمشروع", projects_df['ProjectName'])
            s_sel = st.selectbox("اسم المورد", suppliers_df['SupplierName'])
            amount = st.number_input("قيمة الفاتورة (ج.م)", min_value=0.0)
            desc = st.text_input("وصف المصروف (مثلاً: توريد حديد، يومية عمال)")
            
            if st.form_submit_button("تسجيل المصروف"):
                p_id = projects_df[projects_df['ProjectName'] == p_sel]['ProjectID'].values[0]
                s_id = suppliers_df[suppliers_df['SupplierName'] == s_sel]['SupplierID'].values[0]
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Purchases (ProjectID, SupplierID, Amount, Description) VALUES (?, ?, ?, ?)", 
                               (int(p_id), int(s_id), amount, desc))
                conn.commit()
                st.success("✅ تم تسجيل الفاتورة وتحديث الميزانية!")
    else:
        st.warning("تأكد من وجود مشاريع وموردين مسجلين أولاً.")
