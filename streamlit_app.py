import streamlit as st
import pandas as pd

st.set_page_config(page_title="MNSA - إدارة التكاليف", layout="wide")

st.title("🏗️ نظام MNSA المبسط لإدارة المشروعات")
st.markdown("---")

# --- الجزء الأول: رفع وتحليل المناقصة ---
st.subheader("1️⃣ رفع مقايسة المناقصة (Excel)")
tender_file = st.file_uploader("اختر ملف المقايسة", type=['xlsx', 'xls'], key="tender")

if tender_file:
    df_tender = pd.read_excel(tender_file)
    st.write("📊 بنود المقايسة المستخرجة:")
    st.dataframe(df_tender, use_container_width=True)
    
    # حساب إجمالي قيمة المقايسة (بفرض وجود أعمدة: الكمية، السعر)
    if 'الكمية' in df_tender.columns and 'السعر' in df_tender.columns:
        total_tender = (df_tender['الكمية'] * df_tender['السعر']).sum()
        st.info(f"💰 إجمالي قيمة المقايسة المتوقعة: {total_tender:,.2f} جنيه")
    else:
        st.warning("⚠️ يرجى التأكد أن ملف الإكسل يحتوي على أعمدة باسم (الكمية) و (السعر) للحساب التلقائي.")

st.markdown("---")

# --- الجزء الثاني: رفع المشتريات/التكاليف والمقارنة ---
st.subheader("2️⃣ رفع تكاليف المشروع الفعلية (Excel)")
costs_file = st.file_uploader("ارفع ملف المشتريات أو المصاريف الفعلية", type=['xlsx', 'xls'], key="costs")

if costs_file and tender_file:
    df_costs = pd.read_excel(costs_file)
    st.write("🧾 سجل التكاليف الفعلية:")
    st.dataframe(df_costs, use_container_width=True)
    
    # المقارنة والتحليل
    if 'التكلفة' in df_costs.columns:
        actual_total = df_costs['التكلفة'].sum()
        st.error(f"📉 إجمالي التكاليف الفعلية حتى الآن: {actual_total:,.2f} جنيه")
        
        # حساب الربحية
        try:
            total_tender = (df_tender['الكمية'] * df_tender['السعر']).sum()
            profit = total_tender - actual_total
            percent = (profit / total_tender) * 100
            
            col1, col2 = st.columns(2)
            col1.metric("صافي الربح التقديري", f"{profit:,.2f} ج.م")
            col2.metric("نسبة الربح", f"{percent:.1f}%")
        except:
            st.write("قم بتسمية الأعمدة بشكل صحيح للمقارنة المالية.")
