import streamlit as st
import pandas as pd

# إعداد واجهة البرنامج
st.set_page_config(page_title="MNSA ERP", layout="wide")

st.title("🏗️ نظام MNSA لإدارة المشروعات")
st.info("مرحباً يا مصطفى، هذا الإصدار الآمن للتشغيل السريع.")

# --- قسم رفع وتحليل الملفات ---
st.subheader("📊 تحليل المقايسات والتكاليف (Excel)")

col1, col2 = st.columns(2)

with col1:
    tender_file = st.file_uploader("ارفع مقايسة المناقصة", type=['xlsx'])
    if tender_file:
        df_t = pd.read_excel(tender_file)
        st.write("✅ تم تحميل المقايسة")
        st.dataframe(df_t.head(5)) # عرض أول 5 سطور فقط

with col2:
    cost_file = st.file_uploader("ارفع ملف التكاليف الفعلية", type=['xlsx'])
    if cost_file:
        df_c = pd.read_excel(cost_file)
        st.write("✅ تم تحميل التكاليف")
        st.dataframe(df_c.head(5))

# --- زر المقارنة والحساب ---
if tender_file and cost_file:
    st.markdown("---")
    if st.button("إجراء المقارنة وحصر الأرباح"):
        # هنا سنضع معادلات الحساب في الخطوة القادمة
        st.success("البيانات جاهزة للمقارنة!")
