import streamlit as st
import pandas as pd

st.set_page_config(page_title="MNSA - المكتب الفني المطور", layout="wide")
st.title("🏗️ آلة المكتب الفني لشركة MNSA")

# دالة ذكية جداً للبحث عن الأعمدة في كامل الملف
def smart_find_columns(df):
    # محاولة تنظيف الملف من الصفوف الفارغة في البداية
    df_clean = df.dropna(how='all', axis=0).dropna(how='all', axis=1)
    
    # الكلمات التي نبحث عنها
    targets = {
        'desc': ['بيان الأعمال', 'بيان الاعمال', 'البند', 'الوصف', 'item'],
        'qty': ['الكمية', 'الكميات', 'كمية', 'qty'],
        'price': ['الفئة', 'السعر', 'سعر', 'price']
    }
    
    found = {'desc': None, 'qty': None, 'price': None}
    
    # البحث في أول 10 صفوف وفي أسماء الأعمدة الحالية
    for i in range(min(10, len(df))):
        row_values = df.iloc[i].astype(str).tolist()
        for col_idx, value in enumerate(row_values):
            clean_val = value.strip().lower()
            for key, keywords in targets.items():
                if any(k in clean_val for k in keywords):
                    found[key] = df.columns[col_idx]
                    
    # إذا لم يجد في الصفوف، يبحث في أسماء الأعمدة الأصلية
    for col in df.columns:
        clean_col = str(col).strip().lower()
        for key, keywords in targets.items():
            if found[key] is None and any(k in clean_col for k in keywords):
                found[key] = col
                
    return found

# دالة التحليل الهندسي
def analyze_boq(df, cols):
    summary = {"أسمنت (طن)": 0, "رمل (م3)": 0, "سن (م3)": 0, "حديد (طن)": 0, "سيراميك (م2)": 0, "مواسير (م.ط)": 0}
    total_val = 0
    
    # بدء التحليل من بعد صف الرؤوس
    for index, row in df.iterrows():
        try:
            item = str(row[cols['desc']]).lower()
            qty = pd.to_numeric(row[cols['qty']], errors='coerce') or 0
            price = pd.to_numeric(row[cols['price']], errors='coerce') if cols['price'] else 0
            total_val += (qty * price)

            if any(x in item for x in ["مسلحة", "قواعد", "أعمدة", "سقف"]):
                summary["أسمنت (طن)"] += qty * 0.35
                summary["رمل (م3)"] += qty * 0.4
                summary["سن (م3)"] += qty * 0.8
                summary["حديد (طن)"] += qty * 0.09
            elif "عادية" in item:
                summary["أسمنت (طن)"] += qty * 0.25
                summary["رمل (م3)"] += qty * 0.4
                summary["سن (م3)"] += qty * 0.8
            if "سيراميك" in item or "بورسلين" in item:
                summary["سيراميك (م2)"] += qty
            if "مواسير" in item or "حريق" in item or "شبكة" in item:
                summary["مواسير (م.ط)"] += qty
        except: continue
    return summary, total_val

uploaded_file = st.file_uploader("ارفع مقايسة المشروع (Excel)", type=['xlsx', 'xls'])

if uploaded_file:
    # قراءة الملف بدون تحديد رؤوس أعمدة أولاً
    raw_df = pd.read_excel(uploaded_file)
    
    cols = smart_find_columns(raw_df)
    
    if cols['desc'] and cols['qty']:
        st.success(f"✅ تم العثور على البنود في عمود: {cols['desc']}")
        if st.button("🚀 تشغيل التحليل"):
            results, total_project = analyze_boq(raw_df, cols)
            if cols['price']:
                st.metric("💰 إجمالي قيمة المقايسة", f"{total_project:,.2f} جنيه")
            
            st.markdown("---")
            st.subheader("🏁 حصر الخامات المطلوبة")
            c = st.columns(3)
            for i, (label, value) in enumerate(results.items()):
                c[i % 3].metric(label, f"{value:,.2f}")
    else:
        st.error("❌ لم أجد الأعمدة. البرنامج سيعرض لك أسماء الأعمدة التي قرأها لتتأكد:")
        st.write(list(raw_df.columns))
        st.info("نصيحة: تأكد أن ملف الإكسل لا يحتوي على خلايا مدمجة (Merged Cells) في صف الرؤوس.")
