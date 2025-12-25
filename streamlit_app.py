import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="MNSA - المكتب الفني الذكي", layout="wide")

st.title("🏗️ آلة المكتب الفني لشركة MNSA")
st.markdown("### تحليل المقايسات الشامل (إنشائي - تشطيبات - شبكات)")

# دالة ذكية لإيجاد الأعمدة مهما كان اسمها
def find_column(df, possible_names):
    for name in possible_names:
        for col in df.columns:
            if name.lower() in col.lower().strip():
                return col
    return None

# 2. محرك التحليل الهندسي
def analyze_boq(df, desc_col, qty_col):
    summary = {
        "إجمالي الأسمنت (طن)": 0,
        "إجمالي الرمل (م3)": 0,
        "إجمالي السن/الزلط (م3)": 0,
        "حديد تسليح (طن)": 0,
        "دهانات (بستلة)": 0,
        "سيراميك/بورسلين (م2)": 0,
        "مؤونة لصق (شكارة)": 0,
        "مواسير حريق/شبكات (م.ط)": 0
    }
    
    for index, row in df.iterrows():
        item = str(row[desc_col]).lower()
        try:
            qty = float(row[qty_col])
        except:
            qty = 0

        # --- الحصر الهندسي ---
        if any(x in item for x in ["خرسانة مسلحة", "قواعد", "أعمدة", "سقف"]):
            summary["إجمالي الأسمنت (طن)"] += qty * 0.350
            summary["إجمالي الرمل (م3)"] += qty * 0.4
            summary["إجمالي السن/الزلط (م3)"] += qty * 0.8
            summary["حديد تسليح (طن)"] += qty * 0.090
        
        elif "عادية" in item:
            summary["إجمالي الأسمنت (طن)"] += qty * 0.250
            summary["إجمالي الرمل (م3)"] += qty * 0.4
            summary["إجمالي السن/الزلط (م3)"] += qty * 0.8
        
        if any(x in item for x in ["سيراميك", "بورسلين", "رخام"]):
            summary["سيراميك/بورسلين (م2)"] += qty
            summary["مؤونة لصق (شكارة)"] += qty * 0.25
            summary["إجمالي الرمل (م3)"] += qty * 0.04
        
        if any(x in item for x in ["دهانات", "بلاستيك", "نقاشة"]):
            summary["دهانات (بستلة)"] += qty / 30
            
        if any(x in item for x in ["محارة", "بياض", "طرطشة"]):
            summary["إجمالي الأسمنت (طن)"] += qty * 0.012
            summary["إجمالي الرمل (م3)"] += qty * 0.03

        if any(x in item for x in ["مواسير", "حريق", "شبكات", "upvc", "صرف"]):
            summary["مواسير حريق/شبكات (م.ط)"] += qty

    return summary

# 3. واجهة المستخدم
uploaded_file = st.file_uploader("ارفع مقايسة المشروع (Excel)", type=['xlsx'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📝 معاينة الملف")
    st.dataframe(df.head(10), use_container_width=True)
    
    # محاولة تحديد الأعمدة آلياً
    desc_col = find_column(df, ['البيان', 'بند', 'الوصف', 'item', 'description', 'الأعمال'])
    qty_col = find_column(df, ['الكمية', 'كمية', 'qty', 'quantity'])
    
    if desc_col and qty_col:
        st.success(f"تم التعرف على الأعمدة: [الوصف: {desc_col}] و [الكمية: {qty_col}]")
        
        if st.button("📊 تشغيل آلة الحصر والتحليل"):
            results = analyze_boq(df, desc_col, qty_col)
            
            st.markdown("---")
            st.header("🏁 نتائج حصر المكتب الفني (تقديري)")
            
            # عرض النتائج
            res_cols = st.columns(4)
            for i, (label, value) in enumerate(results.items()):
                res_cols[i % 4].metric(label, f"{value:,.2f}")
            
            # عرض بنود الشبكات المكتشفة
            st.subheader("🌐 تفاصيل بنود الشبكات والمواسير")
            network_df = df[df[desc_col].str.contains('مواسير|حريق|شبكة|صرف|تغذية', na=False, case=False)]
            if not network_df.empty:
                st.table(network_df[[desc_col, qty_col]])
    else:
        st.error("❌ لم أستطع تحديد أعمدة (البيان) و (الكمية). يرجى التأكد من تسمية الأعمدة بوضوح في ملف الإكسل.")
