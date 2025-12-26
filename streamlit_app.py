import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات وتجهيز الجداول
def init_db():
    conn = sqlite3.connect('mnsa_internal.db')
    cursor = conn.cursor()
    
    # جدول المشاريع
    cursor.execute('''CREATE TABLE IF NOT EXISTS Projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectName TEXT, Location TEXT, Budget DECIMAL)''')
    
    # جدول المقايسة
    cursor.execute('''CREATE TABLE IF NOT EXISTS ProjectBOM (
        BOMID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER,
        ItemName TEXT, Quantity DECIMAL, Unit TEXT)''')
    
    # جدول الموردين
    cursor.execute('''CREATE TABLE IF NOT EXISTS Suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT)''')
    
    # جدول المشتريات (المصروفات)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Purchases (
        PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER,
        SupplierID INTEGER, Amount DECIMAL, Description TEXT)''')

    # إضافة بيانات افتراضية إذا كان الجدول فارغاً
    cursor.execute("SELECT COUNT(*) FROM Suppliers")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Suppliers (SupplierName) VALUES ('شركة عز للحديد'), ('السويدي للكابلات'), ('أسمنت لافارج')")
        conn.commit()
    return conn

conn = init_db()

# 2. الواجهة وتصميم القائمة
st.set_page_config(page_title="MNSA ERP", layout="wide")
st.title("🏗️ نظام إدارة شركة MNSA للمقاولات")

menu = st.sidebar.selectbox("القائمة الرئيسية", 
    ["📊 لوحة التحكم", "🏢 إدارة المشاريع", "📋 حصر المواد (BOM)", "💰 المشتريات والموردين"])

# --- القسم الأول: لوحة التحكم (الأرباح والخسائر) ---
if menu == "📊 لوحة التحكم":
    st.header("📊 ملخص الأداء المالي للمشاريع")
    df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    if not df_p.empty:
        for index, row in df_p.iterrows():
            with st.expander(f"📉 تحليل مشروع: {row['ProjectName']}"):
                p_id = row['ProjectID']
                # حساب إجمالي المصروفات من جدول المشتريات
                df_exp = pd.read_sql_query(f"SELECT SUM(Amount) as total FROM Purchases WHERE ProjectID = {p_id}", conn)
                expenses = df_exp['total'][0] or 0
                budget = row['Budget']
                remaining = budget - expenses
                
                c1, c2, c3 = st.columns(3)
                c1.metric("الميزانية المرصودة", f"{budget:,.2f}")
                c2.metric("إجمالي المصروفات", f"{expenses:,.2f}", delta=f"-{expenses:,.2f}", delta_color="inverse")
                c3.metric("المتبقي (الربح التقديري)", f"{remaining:,.2f}")
                
                # بار توضيحي لاستهلاك الميزانية
                progress = min(expenses / budget, 1.0) if budget > 0 else 0
                st.progress(progress, text=f"نسبة استهلاك الميزانية: {progress*100:.1f}%")
    else:
        st.info("لا توجد بيانات لعرضها حالياً.")

# --- القسم الثاني: إدارة المشاريع ---
elif menu == "🏢 إدارة المشاريع":
    st.header("🏢 تسجيل وإدارة المشاريع")
    with st.form("add_p"):
        name = st.text_input("اسم المشروع الجديد")
        loc = st.text_input("موقع المشروع")
        bud = st.number_input("الميزانية الإجمالية (ج.م)", min_value=0.0)
        if st.form_submit_button("حفظ المشروع"):
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?, ?, ?)", (name, loc, bud))
            conn.commit()
            st.success("تم الحفظ!")
            st.rerun()

# --- القسم الثالث: حصر المواد (BOM) ---
elif menu == "📋 حصر المواد (BOM)":
    st.header("📋 حصر الكميات والمقايسات")
    projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not projects.empty:
        sel_p = st.selectbox("اختر المشروع", projects['ProjectName'])
        p_id = projects[projects['ProjectName'] == sel_p]['ProjectID'].values[0]
        
        # إضافة بند وحصر تلقائي
        with st.expander("➕ إضافة بند جديد للمقايسة"):
            item = st.text_input("بيان العمل")
            qty = st.number_input("الكمية", min_value=0.0)
            unit = st.selectbox("الوحدة", ["م3", "طن", "م2", "م.ط"])
            if st.button("حفظ البند"):
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", (int(p_id), item, qty, unit))
                conn.commit()
                st.success("تمت الإضافة")
        
        # عرض الجدول
        df_bom = pd.read_sql_query(f"SELECT ItemName as البند, Quantity as الكمية, Unit as الوحدة FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
        st.table(df_bom)
    else:
        st.warning("أضف مشروعاً أولاً")

# --- القسم الرابع: المشتريات والموردين ---
elif menu == "💰 المشتريات والموردين":
    st.header("💰 إدارة فواتير المشتريات")
    projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    suppliers = pd.read_sql_query("SELECT * FROM Suppliers", conn)
    
    if not projects.empty:
        with st.form("buy"):
            p_sel = st.selectbox("تخصيص لمشروع", projects['ProjectName'])
            s_sel = st.selectbox("اسم المورد", suppliers['SupplierName'])
            amt = st.number_input("قيمة الفاتورة (ج.م)", min_value=0.0)
            desc = st.text_input("وصف المشتريات (مثلاً: دفعة حديد)")
            if st.form_submit_button("تسجيل الفاتورة"):
                p_id = projects[projects['ProjectName'] == p_sel]['ProjectID'].values[0]
                s_id = suppliers[suppliers['SupplierName'] == s_sel]['SupplierID'].values[0]
                cursor = conn.cursor()
                cursor.execute("INSERT INTO Purchases (ProjectID, SupplierID, Amount, Description) VALUES (?, ?, ?, ?)", (int(p_id), int(s_id), amt, desc))
                conn.commit()
                st.success("تم تسجيل المصروف بنجاح!")
    else:
        st.warning("أضف مشروعاً أولاً")  
        elif menu == "💰 المشتريات والموردين":
    # (إضافة تبويب جديد داخل المشتريات)
    st.subheader("📝 تحويل المقايسة إلى أمر شراء")
    
    projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not projects.empty:
        sel_p = st.selectbox("اختر المشروع لجلب احتياجاته:", projects['ProjectName'], key="po_proj")
        p_id = projects[projects['ProjectName'] == sel_p]['ProjectID'].values[0]
        
        # جلب بنود المقايسة لهذا المشروع
        df_needs = pd.read_sql_query(f"SELECT ItemName, Quantity, Unit FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
        
        if not df_needs.empty:
            st.write("البنود المطلوبة بناءً على الحصر:")
            st.dataframe(df_needs)
            
            with st.form("po_form"):
                supplier = st.selectbox("اختر المورد المرشح", pd.read_sql_query("SELECT SupplierName FROM Suppliers", conn))
                selected_item = st.selectbox("اختر البند المطلوب شراؤه", df_needs['ItemName'])
                po_price = st.number_input("سعر الوحدة المتفق عليه", min_value=0.0)
                po_qty = st.number_input("الكمية المطلوب توريدها الآن", min_value=0.0)
                
                if st.form_submit_button("إصدار أمر شراء رسمي"):
                    total_po = po_price * po_qty
                    cursor = conn.cursor()
                    # تسجيل في جدول المشتريات لخصمه من الميزانية
                    cursor.execute("""
                        INSERT INTO Purchases (ProjectID, SupplierID, Amount, Description) 
                        VALUES (?, (SELECT SupplierID FROM Suppliers WHERE SupplierName=?), ?, ?)
                    """, (int(p_id), supplier, total_po, f"أمر شراء: {selected_item}"))
                    conn.commit()
                    st.success(f"✅ تم إصدار أمر الشراء بقيمة {total_po:,.2f} ج.م وتحديث ميزانية المشروع!")
