import streamlit as st
import pandas as pd

# إعدادات الصفحة
st.set_page_config(page_title="MNSA - حصر الاحتياجات", layout="wide")

st.title("🏗️ محرك MNSA الذكي لحصر احتياجات المشروعات")
st.info("ارفع مقايسة المشروع (Excel) وسيقوم النظام بتشريح البنود وحصر المواد المطلوبة.")

# دالة تحليل المكونات (Engineering Logic)
def calculate_requirements(df):
    total_materials = {
        "أسمنت (طن)": 0,
        "رمل (م3)": 0,
        "زلط (م3)": 0,
        "حديد تسليح (طن)": 0,
        "طوب (ألف طوبة)": 0
    }
    
    # البحث في كل سطر في المقايسة
    for index, row in df.iterrows():
        item_text = str(row.get('البيان', '')).lower()
        qty = float(row.get('الكمية', 0))
        
        # 1. تحليل الخرسانات
        if "خرسانة مسلحة" in item_text:
            total_materials["أسمنت (طن)"] += qty * 0.350 # 350 كجم/م3
            total_materials["رمل (م3)"] += qty * 0.4
            total_materials["زلط (م3)"] += qty * 0.8
            total_materials["حديد تسليح (طن)"] += qty * 0.080 # متوسط 80 كجم/م3
            
        elif "خرسانة عادية" in item_text:
            total_materials["أسمنت (طن)"] += qty * 0.250
            total_materials["رمل (م3)"] += qty * 0.4
            total_materials["زلط (م3)"] += qty * 0.8

        # 2. تحليل المباني
        if "مباني" in item_text or "طوب" in item_text:
            total_materials["طوب (ألف طوبة)"] += qty * 0.055 # بفرض سمك الحائط

    return total_materials

# واجهة الرفع
uploaded_file = st.file_uploader("اختر ملف المقايسة (Excel فقط)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📋 مراجعة بنود المقايسة")
    st.dataframe(df, use_container_width=True)
    
    if st.button("🚀 ابدأ الحصر الهندسي للاحتياجات"):
        results = calculate_requirements(df)
        
        st.markdown("---")
        st.subheader("📦 إجمالي الاحتياجات التقديرية للمواد الخام")
        
        # عرض النتائج في شكل كروت جذابة
        cols = st.columns(len(results))
        for i, (mat, val) in enumerate(results.items()):
            cols[i].metric(mat, f"{val:.2f}")
            
        st.success("تم الحصر بناءً على معدلات الاستهلاك القياسية للأعمال الإنشائية.")

        # قسم الشبكات (بنية تحتية)
        st.subheader("🌐 حصر شبكات الحريق والبنية التحتية")
        fire_items = df[df['البيان'].str.contains('حريق|محابس|مواسير|UPVC', na=False)]
        if not fire_items.empty:
            st.write("تم العثور على بنود الشبكات التالية:")
            st.table(fire_items[['البيان', 'الكمية']])
        else:
            st.write("لم يتم العثور على بنود شبكات واضحة في هذا الملف.")
