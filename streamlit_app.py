import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="MNSA - المكتب الفني", layout="wide")

st.title("🏗️ آلة المكتب الفني لشركة MNSA")

# دالة التعرف على الأعمدة المصرية
def find_column(df, target_names):
    for col in df.columns:
        clean_col = str(col).strip().lower()
        for target in target_names:
            if target in clean_col:
                return col
    return None

# 2. محرك التحليل الهندسي
def analyze_boq(df, desc_col, qty_col, price_col):
    summary = {
        "أسمنت (طن)": 0, "رمل (م3)": 0, "سن/زلط (م3)": 0,
        "حديد (طن)": 0, "سيراميك (م2)": 0, "دهانات (بستلة)": 0,
        "مواسير شبكات (م.ط)": 0
    }
    total_val = 0
    
    for index, row in df.iterrows():
        try:
            item = str(row[desc_col]).lower()
            qty = float(row[qty_col]) if pd.notnull(row[qty_col]) else 0
            price = float(row[price_col]) if price_col and pd.notnull(row[price_col]) else 0
            total_val += (qty * price)

            # تحليل البنود
            if any(x in item for x in ["خرسانة مسلحة", "قواعد", "أعمدة", "سقف", "ميد"]):
                summary["أسمنت (طن)"] += qty * 0.35
                summary["رمل (م3)"] += qty * 0.4
                summary["سن/زلط (م3)"] += qty * 0.8
                summary["حديد (طن)"] += qty * 0.09
            elif "عادية" in item:
                summary["أسمنت (طن)"] += qty * 0.25
                summary["رمل (م3)"] += qty * 0.4
                summary["سن/زلط (م3)"] += qty * 0.8
            if any(x in item for x in ["سيراميك", "بورسلين", "تكسيات"]):
                summary["سيراميك (م2)"] += qty
            if any(x in item for x in ["دهانات", "بلاستيك", "وجه"]):
                summary["دهانات (بستلة)"] += qty / 30
            if any(x in item for x in ["مواسير", "حريق", "شبكة", "صرف", "upvc"]):
                summary["مواسير شبكات (م.ط)"] += qty
        except:
            continue
    return summary, total_val

# 3. الواجهة
uploaded_file = st.file_uploader("ارفع مقايسة المشروع (Excel)", type=['xlsx', 'xls'])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    desc_col = find_column(df, ['بيان الأعمال', 'بيان الاعمال', 'البند', 'الوصف'])
    qty_col = find_column(df, ['الكمية', 'الكميات', 'كمية'])
    price_col = find_column(df, ['الفئة', 'السعر', 'سعر الوحده'])
    
    if desc_col and qty_col:
        st.success(f"✅ تم التعرف على الأعمدة بنجاح")
        if st.button("🚀 تشغيل تحليل المكتب الفني"):
            results, total_project = analyze_boq(df, desc_col, qty_col, price_col)
            
            if price_col:
                st.metric("💰 إجمالي قيمة العقد", f"{total_project:,.2f} جنيه")
            
            st.markdown("---")
            st.subheader("🏁 حصر المواد الخام المطلوبة")
            cols = st.columns(4)
            for i, (label, value) in enumerate(results.items()):
                cols[i % 4].metric(label, f"{value:,.2f}")
    else:
        st.error("❌ لم أجد أعمدة (بيان الأعمال) و (الكمية). تأكد من مسميات الأعمدة في الإكسل.")
