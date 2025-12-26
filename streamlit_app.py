import streamlit as st
import sqlite3
import pandas as pd

# الاتصال بقاعدة البيانات (تأكد أن اسم الملف مطابق لملفك)
def get_connection():
    return sqlite3.connect('mnsa_ultimate_2025.db')

st.set_page_config(page_title="MNSA Database Search", layout="wide")
st.title("🔍 محرك البحث في قاعدة بيانات MNSA")

# 1. جلب أسماء كل الجداول الموجودة في قاعدة بياناتك تلقائياً
conn = get_connection()
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']

if tables:
    # اختيار الجدول المراد البحث داخله
    selected_table = st.sidebar.selectbox("اختر الجدول (الموردين، العملاء، المخازن...):", tables)
    
    # 2. قراءة بيانات الجدول المختار
    df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
    
    st.header(f"جدول: {selected_table}")
    
    # 3. محرك البحث الذكي داخل الجدول
    search_term = st.text_input(f"اكتب أي كلمة للبحث داخل {selected_table} (اسم، مبلغ، تاريخ...):")
    
    if search_term:
        # البحث في كل الأعمدة في وقت واحد
        mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
        filtered_df = df[mask]
        st.success(f"تم العثور على {len(filtered_df)} سجل")
    else:
        filtered_df = df

    # 4. عرض الجدول بشكل مطابق لقاعدة البيانات
    st.dataframe(filtered_df, use_container_width=True)
    
    # ميزة إضافية: إحصائيات سريعة للقيم المالية
    numeric_cols = filtered_df.select_dtypes(include=['number']).columns
    if not filtered_df.empty and len(numeric_cols) > 0:
        st.subheader("📊 ملخص مالي سريع لنتائج البحث:")
        col_to_sum = st.selectbox("اختر العمود لجمع قيمه (مثل الرصيد أو الإجمالي):", numeric_cols)
        st.metric(label=f"إجمالي {col_to_sum}", value=f"{filtered_df[col_to_sum].sum():,.2f}")

else:
    st.error("لم يتم العثور على جداول في قاعدة البيانات. تأكد من رفع الملف الصحيح.")

conn.close()
لماذا هذا الكود هو الحل؟
