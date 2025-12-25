import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="MNSA - المكتب الفني الاحترافي", layout="wide")

st.title("🏗️ آلة المكتب الفني لشركة MNSA")
st.markdown("### تحليل شامل: (بيان الأعمال - الكميات - الفئات المالية)")

# دالة مطورة للتعرف على أعمدة المقايسة المصرية
def find_column(df, target_names):
    for col in df.columns:
        clean_col = str(col).strip().lower()
        for target in target_names:
            if target in clean_col:
                return col
    return None

# 2. محرك التحليل الهندسي والمالي
def analyze_boq(df, desc_col, qty_col, price_col):
    summary = {
        "إجمالي الأسمنت (طن)": 0,
        "إجمالي الرمل (م3)": 0,
        "إجمالي السن/الزلط (م3)": 0,
        "حديد تسليح (طن)": 0,
        "سيراميك/بورسلين (م2)": 0,
        "دهانات (بستلة)": 0,
        "مواسير حريق/شبكات (م.ط)": 0
    }
    total_project_value = 0
    
    for index, row in df.iterrows():
        try:
            item = str(row[desc_col]).lower()
            qty = float(row[qty_col]) if pd.notnull(row[qty_col]) else 0
            price = float(row[price_col]) if pd.notnull(row[price_col]) else 0
            
            # حساب القيمة المالية الكلية للمشروع
            total_project_value += (qty * price)

            # --- تحليل المكونات بناءً على "بيان الأعمال" ---
            if any(x in item for x in ["خرسانة مسلحة", "قواعد", "أعمدة", "سقف", "ميد"]):
                summary["إجمالي الأسمنت (طن)"] += qty * 0.350
                summary["إجمالي الرمل (م3)"] += qty * 0.4
                summary["إجمالي السن/الزلط (م3)"] += qty * 0.8
                summary["حديد تسليح (طن)"] += qty * 0.090
            
            elif "عادية" in item:
                summary["إجمالي الأسمنت (طن)"] += qty * 0.250
                summary["إجمالي الرمل (م3)"] += qty * 0.4
                summary["إجمالي السن/الزلط (م3)"] += qty * 0.8
            
            if any(x in item for x in ["سيراميك", "بورسلين", "رخام", "تكسيات"]):
                summary["سيراميك/بورسلين (م2)"] += qty
            
            if any(x in item for x in ["دهانات", "بلاستيك", "وجه"]):
                summary["دهانات (بستلة)"] += qty / 30
                
            if any(x in item for x in ["مواسير", "حريق", "شبكة", "صرف", "تغذية", "upvc"]):
                summary["مواسير حريق/شبكات (م.ط)"] += qty
        except:
            continue # تخطي السطور التي تحتوي على أخطاء في البيانات

    return summary, total_project_value

# 3. واجهة المستخدم
uploaded_file = st.file_uploader("ارفع مقايسة المشروع (Excel)", type=['xlsx', 'xls'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📝 معاينة بيانات المقايسة")
    st.dataframe(df.head(10), use_container_width=True)
    
    # محاولة تحديد الأعمدة بالمسميات التي ذكرتها يا مصطفى
    desc_col = find_column(df, ['بيان الأعمال', 'بيان الاعمال', 'البند', 'الوصف'])
    qty_col = find_column(df, ['الكمية', 'الكميات', 'كمية'])
    price_col = find_column(df, ['الفئة', 'السعر', 'سعر الوحده'])
    
    if desc_col and qty_col:
        st.success(f"✅ تم التعرف على: [الوصف: {desc_col}] | [الكمية: {qty_col}]" + (f" | [الفئة: {price_col}]" if price_col else ""))
        
        if st.button("🚀 تشغيل تحليل المكتب الفني"):
            results, total_val = analyze_boq(df, desc_col, qty_col, price_col if price_col else qty_col)
            
            # عرض النتائج المالية
            if price_col:
                st.markdown("---")
                st.metric("💰 إجمالي قيمة المقايسة (عقد المشروع)", f"{total_val:,.2f} جنيه")

            st.markdown("---")
            st.header("🏁 تقرير حصر المواد الخام المطلوبة")
            
            # عرض نتائج الحصر الهندسي
            res_cols = st.columns(4)
            for i, (label, value) in enumerate(results.items()):
                res_cols[i % 4].metric(label, f"{value:,.2f}")
            
            # قسم الشبكات
            st.subheader("🌐 تفاصيل بنود الشبكات والمواسير")
            network_df = df[df[desc_col].str.contains('مواسير|حريق|شبكة|صرف|تغذية', na=False, case=False)]
            if not network_df.empty:
                st.table(network_df[[desc_col, qty_col]])
    else:
        st.error("❌ لم أستطع تحديد الأعمدة. تأكد أن الملف يحتوي على أعمدة بأسماء: (بيان الأعمال) و (الكمية).")
ما الذي أضفته لك في هذا التعديل؟ تسمية الأعمدة بوضوح في ملف الإكسل.")
