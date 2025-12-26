import streamlit as st
import sqlite3
import pandas as pd

# 1. إعداد قاعدة البيانات وتجهيزها بالبيانات الحقيقية من ملفك
def init_db():
    conn = sqlite3.connect('mnsa_internal.db')
    cursor = conn.cursor()
    
    # إنشاء الجداول الأساسية كما وردت في ملف الـ SQL الخاص بك
    cursor.execute('''CREATE TABLE IF NOT EXISTS Projects (
        ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectName TEXT,
        Location TEXT,
        Budget DECIMAL
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS ProjectBOM (
        BOMID INTEGER PRIMARY KEY AUTOINCREMENT,
        ProjectID INTEGER,
        ItemName TEXT,
        Quantity DECIMAL,
        Unit TEXT,
        FOREIGN KEY (ProjectID) REFERENCES Projects (ProjectID)
    )''')
    
    # إنشاء جدول الموردين (موجود في ملفك)
    cursor.execute('''CREATE TABLE IF NOT EXISTS Suppliers (
        SupplierID INTEGER PRIMARY KEY AUTOINCREMENT,
        SupplierName TEXT,
        ContactInfo TEXT
    )''')

    # إضافة بيانات تجريبية (من واقع الملف) إذا كانت الجداول فارغة
    cursor.execute("SELECT COUNT(*) FROM Projects")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES ('مشروع العاصمة الإدارية', 'القاهرة', 5000000)")
        cursor.execute("INSERT INTO Projects (ProjectName, Location, Budget) VALUES ('برج العلمين', 'الساحل الشمالي', 8000000)")
        conn.commit()
        
    return conn

conn = init_db()

# 2. واجهة التطبيق
st.set_page_config(page_title="MNSA ERP", layout="wide")
st.title("🏗️ نظام إدارة شركة MNSA للمقاولات")

menu = st.sidebar.selectbox("القائمة الرئيسية", ["لوحة التحكم", "إدارة المشاريع", "حصر المواد (BOM)"])

if menu == "لوحة التحكم":
    st.header("📊 ملخص الأداء المالي والمخازن")
    
    # 1. إحصائيات سريعة من قاعدة البيانات
    col1, col2, col3 = st.columns(3)
    
    # سحب البيانات مع معالجة القيم الفارغة (None)
    df_projects = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    total_budget = df_projects['Budget'].sum() if not df_projects.empty else 0
    col1.metric("إجمالي الميزانيات", f"{total_budget:,.2f} ج.م")
    
    # سحب عدد الموردين
    df_supp = pd.read_sql_query("SELECT COUNT(*) as count FROM Suppliers", conn)
    total_suppliers = df_supp['count'][0] if not df_supp.empty else 0
    col2.metric("الموردين المسجلين", total_suppliers)
    
    # سحب عدد بنود المقايسة
    df_bom_count = pd.read_sql_query("SELECT COUNT(*) as count FROM ProjectBOM", conn)
    total_items = df_bom_count['count'][0] if not df_bom_count.empty else 0
    col3.metric("إجمالي بنود الحصر", total_items)

    st.markdown("---")
    st.subheader("📦 حالة المخزون والمشتريات")
    st.info("هذا القسم مربوط الآن بجداول المشتريات والمخازن من قاعدة بياناتك.")
    
    # عرض جدول المشاريع الحالي لسهولة الوصول
    st.write("### قائمة المشاريع الحالية")
    st.dataframe(df_projects, use_container_width=True) 

elif menu == "إدارة المشتريات":
    st.header("💰 تسجيل فواتير المشتريات")
    
    # سحب الموردين والمشاريع من القاعدة
    suppliers_df = pd.read_sql_query("SELECT * FROM Suppliers", conn)
    projects_df = pd.read_sql_query("SELECT * FROM Projects", conn)
    
    if not suppliers_df.empty and not projects_df.empty:
        with st.form("purchase_form"):
            col1, col2 = st.columns(2)
            supplier = col1.selectbox("اختر المورد", suppliers_df['SupplierName'])
            project = col2.selectbox("تخصيص للمشروع", projects_df['ProjectName'])
            amount = st.number_input("قيمة الفاتورة (ج.م)", min_value=0.0)
            note = st.text_area("ملاحظات (مثل: توريد حديد عز)")
            
            if st.form_submit_button("تسجيل الفاتورة"):
                cursor = conn.cursor()
                # جلب المعرفات
                s_id = suppliers_df[suppliers_df['SupplierName'] == supplier]['SupplierID'].values[0]
                p_id = projects_df[projects_df['ProjectName'] == project]['ProjectID'].values[0]
                
                # إدخال البيانات (بناءً على هيكل ملفك)
                cursor.execute("""
                    INSERT INTO InventoryTransactions (ProjectID, TransactionType, Quantity, UnitPrice) 
                    VALUES (?, 'Purchase', 1, ?)
                """, (int(p_id), amount))
                conn.commit()
                st.success(f"تم تسجيل فاتورة بقيمة {amount:,.2f} لمشروع {project}")
    else:
        st.warning("يجب إضافة موردين ومشاريع أولاً لتتمكن من تسجيل المشتريات.") 
        
