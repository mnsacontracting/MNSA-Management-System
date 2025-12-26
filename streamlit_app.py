import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. إعداد قاعدة البيانات وتأمين الهيكل البرمجي
def init_db():
    conn = sqlite3.connect('mnsa_erp_v3.db')
    cursor = conn.cursor()
    # إنشاء الجداول الأساسية مع التأكد من وجود كل الحقول المطلوبة
    cursor.execute('''CREATE TABLE IF NOT EXISTS Projects 
                      (ProjectID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectName TEXT, Location TEXT, Budget REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS ProjectBOM 
                      (BOMID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, ItemName TEXT, Quantity REAL, Unit TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Suppliers 
                      (SupplierID INTEGER PRIMARY KEY AUTOINCREMENT, SupplierName TEXT, Contact TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Purchases 
                      (PurchaseID INTEGER PRIMARY KEY AUTOINCREMENT, ProjectID INTEGER, SupplierID INTEGER, Amount REAL, Description TEXT, Date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Employees 
                      (EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT, EmployeeName TEXT, JobTitle TEXT, Salary REAL)''')
    conn.commit()
    return conn

conn = init_db()

# 2. إعدادات واجهة المستخدم
st.set_page_config(page_title="MNSA ERP System", layout="wide", page_icon="🏗️")

# القائمة الجانبية الموحدة
st.sidebar.title("🏗️ شركة MNSA للمقاولات")
st.sidebar.info("نظام إدارة المشاريع والموارد")
menu = st.sidebar.selectbox("انتقل إلى:", [
    "📊 لوحة التحكم المالية",
    "🏢 إدارة المشاريع",
    "📋 مقايسات البنود (BOM)",
    "👷 إدارة الموردين",
    "💰 المشتريات والمصروفات",
    "👥 شؤون الموظفين"
])

# --- 1. لوحة التحكم المالية (التحليل الذكي) ---
if menu == "📊 لوحة التحكم المالية":
    st.header("📊 داشبورد تحليل الأداء المالي")
    df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    if not df_p.empty:
        # إحصائيات الشركة الكلية
        total_budget = df_p['Budget'].sum()
        df_exp_all = pd.read_sql_query("SELECT SUM(Amount) as total FROM Purchases", conn)
        total_exp = df_exp_all['total'][0] or 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي ميزانيات المشاريع", f"{total_budget:,.2f} ج.م")
        col2.metric("إجمالي المصروفات الفعلي", f"{total_exp:,.2f} ج.م", delta=f"{(total_exp/total_budget)*100:.1f}% من الميزانية", delta_color="inverse")
        col3.metric("الربح التقديري (السيولة)", f"{total_budget - total_exp:,.2f} ج.م")

        st.markdown("---")
        st.subheader("📈 حالة الميزانية لكل مشروع")
        
        # رسم بياني تفاعلي
        chart_data = []
        for _, row in df_p.iterrows():
            p_id = row['ProjectID']
            p_exp = pd.read_sql_query(f"SELECT SUM(Amount) as total FROM Purchases WHERE ProjectID = {p_id}", conn)['total'][0] or 0
            chart_data.append({"المشروع": row['ProjectName'], "الميزانية": row['Budget'], "المنصرف": p_exp})
        
        st.bar_chart(pd.DataFrame(chart_data).set_index("المشروع"))
    else:
        st.warning("لا توجد بيانات مسجلة. يرجى البدء بإضافة مشروع.")

# --- 2. إدارة المشاريع ---
elif menu == "🏢 إدارة المشاريع":
    st.header("🏢 تسجيل مشروع جديد")
    with st.form("p_form", clear_on_submit=True):
        name = st.text_input("اسم المشروع")
        loc = st.text_input("الموقع الجغرافي")
        bud = st.number_input("الميزانية المرصودة", min_value=0.0, step=1000.0)
        if st.form_submit_button("حفظ المشروع في القاعدة"):
            if name and bud > 0:
                conn.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES (?, ?, ?)", (name, loc, bud))
                conn.commit()
                st.success(f"تم تسجيل مشروع {name} بنجاح")
                st.rerun()
            else:
                st.error("يرجى إكمال البيانات الأساسية")

# --- 3. مقايسات البنود (BOM) ---
elif menu == "📋 مقايسات البنود (BOM)":
    st.header("📋 حصر كميات بنود المقايسة")
    df_projs = pd.read_sql_query("SELECT ProjectID, ProjectName FROM Projects", conn)
    if not df_projs.empty:
        sel_name = st.selectbox("اختر المشروع", df_projs['ProjectName'])
        p_id = df_projs[df_projs['ProjectName'] == sel_name]['ProjectID'].values[0]
        
        with st.expander("➕ إضافة بند عمل جديد"):
            item = st.text_input("بيان العمل (مثال: خرسانة أعمدة)")
            qty = st.number_input("الكمية التقديرية", min_value=0.0)
            unit = st.selectbox("الوحدة", ["م3", "طن", "م2", "م.ط", "عدد"])
            if st.button("حفظ البند"):
                conn.execute("INSERT INTO ProjectBOM (ProjectID, ItemName, Quantity, Unit) VALUES (?, ?, ?, ?)", (int(p_id), item, qty, unit))
                conn.commit()
                st.success("تم التحديث")
        
        df_bom = pd.read_sql_query(f"SELECT ItemName as البند, Quantity as الكمية, Unit as الوحدة FROM ProjectBOM WHERE ProjectID = {p_id}", conn)
        st.dataframe(df_bom, use_container_width=True)
    else:
        st.info("سجل مشروعاً أولاً لتتمكن من إضافة مقايسته.")

# --- 4. إدارة الموردين ---
elif menu == "👷 إدارة الموردين":
    st.header("👷 سجل الموردين ومقاولي الباطن")
    with st.form("s_form", clear_on_submit=True):
        s_name = st.text_input("اسم الشركة / المورد")
        s_tel = st.text_input("رقم التليفون / العنوان")
        if st.form_submit_button("إضافة المورد"):
            if s_name:
                conn.execute("INSERT INTO Suppliers (SupplierName, Contact) VALUES (?, ?)", (s_name, s_tel))
                conn.commit()
                st.success("تم الحفظ")
                st.rerun()
    
    df_supp = pd.read_sql_query("SELECT SupplierName as المورد, Contact as الاتصال FROM Suppliers", conn)
    st.table(df_supp)

# --- 5. المشتريات والمصروفات ---
elif menu == "💰 المشتريات والمصروفات":
    st.header("💰 تسجيل فواتير المصروفات")
    df_p = pd.read_sql_query("SELECT ProjectID, ProjectName FROM Projects", conn)
    df_s = pd.read_sql_query("SELECT SupplierID, SupplierName FROM Suppliers", conn)
    
    if not df_p.empty:
        with st.form("buy_form", clear_on_submit=True):
            p_sel = st.selectbox("تحميل على مشروع:", df_p['ProjectName'])
            s_sel = st.selectbox("اسم المورد:", df_s['SupplierName'] if not df_s.empty else ["مورد عام"])
            amt = st.number_input("قيمة الفاتورة", min_value=0.0)
            desc = st.text_input("البيان (ماذا اشتريت؟)")
            if st.form_submit_button("تسجيل المصرف"):
                p_id = df_p[df_p['ProjectName'] == p_sel]['ProjectID'].values[0]
                date_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                conn.execute("INSERT INTO Purchases (ProjectID, Amount, Description, Date) VALUES (?, ?, ?, ?)", (int(p_id), amt, desc, date_now))
                conn.commit()
                st.success("تم تحديث حساب المشروع")
    else:
        st.error("يجب إدخال المشاريع أولاً")

# --- 6. شؤون الموظفين ---
elif menu == "👥 شؤون الموظفين":
    st.header("👥 كشوف الموظفين والرواتب")
    with st.form("e_form", clear_on_submit=True):
        e_name = st.text_input("اسم الموظف")
        job = st.text_input("الوظيفة")
        sal = st.number_input("الراتب الشهري / اليومية")
        if st.form_submit_button("إضافة"):
            conn.execute("INSERT INTO Employees (EmployeeName, JobTitle, Salary) VALUES (?, ?, ?)", (e_name, job, sal))
            conn.commit()
            st.success("تم الحفظ")
            st.rerun()
    
    df_emp = pd.read_sql_query("SELECT EmployeeName as الاسم, JobTitle as الوظيفة, Salary as الراتب FROM Employees", conn)
    st.dataframe(df_emp, use_container_width=True)
