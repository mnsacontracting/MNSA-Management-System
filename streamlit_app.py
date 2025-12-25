import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="MNSA - المكتب الفني", layout="wide")

st.title("🏗️ آلة المكتب الفني الذكية - شركة MNSA")
st.markdown("### حصر شامل للمواد (إنشاءات - تشطيبات - شبكات حريق وصرف)")

# --- دالة إيجاد الأعمدة مهما كانت التسمية ---
def find_columns_flexibly(df):
    search_map = {
        'desc': ['بيان', 'بند', 'وصف', 'item', 'description', 'work'],
        'qty': ['كمية', 'كميات', 'qty', 'quantity', 'العدد'],
        'price': ['فئة', 'سعر', 'price', 'rate', 'القيمة']
    }
    found = {'desc': None, 'qty': None, 'price': None}
    
    # البحث في أسماء الأعمدة
    for col in df.columns:
        c_clean = str(col).strip().lower()
        for key, keywords in search_map.items():
            if any(k in c_clean for k in keywords):
                found[key] = col
                
    # البحث في أول 5 صفوف (لحالات الخلايا المدمجة)
    if not found['desc'] or not found['qty']:
        for i in range(min(5, len(df))):
            row_vals = df.iloc[i].astype(str).tolist()
            for idx, val in enumerate(row_vals):
                v_clean = val.strip().lower()
                for key, keywords in search_map.items():
                    if found[key] is None and any(k in v_clean for k in keywords):
                        found[key] = df.columns[idx]
    return found

# --- دالة الحصر الهندسي ---
def run_full_takeoff(df, cols):
    m = {
        "أسمنت بورتلاندي (طن)": 0, "حديد تسليح (طن)": 0, "رمل (م3)": 0, "سن/زلط (م3)": 0,
        "طوب (ألف طوبة)": 0, "سيراميك (م2)": 0, "دهانات (بستلة)": 0, 
        "مواسير حريق (م.ط)": 0, "مواسير صرف (م.ط)": 0, "محابس وقطع (عدد)": 0
    }
    total_val = 0
    
    for _, row in df.iterrows():
        try:
            item = str(row[cols['desc']]).lower()
            qty = pd.to_numeric(row[cols['qty']], errors='coerce') or 0
            price = pd.to_numeric(row[cols['price']], errors='coerce') if cols['price'] else 0
            total_val += (qty * price)

            # تحليل الإنشاءات
            if any(x in item for x in ["مسلحة", "ميد", "أعمدة", "سقف", "كمرات"]):
                m["أسمنت بورتلاندي (طن)"] += qty * 0.35
                m["حديد تسليح (طن)"] += qty * 0.095
                m["رمل (م3)"] += qty * 0.4
                m["سن/زلط (م3)"] += qty * 0.8
            elif "عادية" in item or "فرشة" in item:
                m["أسمنت بورتلاندي (طن)"] += qty * 0.25
                m["رمل (م3)"] += qty * 0.4
                m["سن/زلط (م3)"] += qty * 0.8

            # تحليل الشبكات
            if "حريق" in item: m["مواسير حريق (م.ط)"] += qty
            elif any(x in item for x in ["صرف", "upvc", "مواسير", "بنية"]): m["مواسير صرف (م.ط)"] += qty
            if any(x in item for x in ["محبس", "صندوق", "قطع"]): m["محابس وقطع (عدد)"] += qty

            # تحليل التشطيبات والمباني
            if "مباني" in item: m["طوب (ألف طوبة)"] += qty * 0.06
            if "سيراميك" in item or "بلاط" in item: m["سيراميك (م2)"] += qty
            if "دهانات" in item or "بلاستيك" in item: m["دهانات (بستلة)"] += qty / 25
        except: continue
        
    return m, total_val

# --- الواجهة ---
uploaded_file = st.file_uploader("ارفع مقايسة المشروع (Excel)", type=['xlsx', 'xls'])

if uploaded_file:
    df_raw = pd.read_excel(uploaded_file)
    cols = find_columns_flexibly(df_raw)
    
    if cols['desc'] and cols['qty']:
        st.success(f"✅ تم التعرف على: ({cols['desc']}) و ({cols['qty']})")
        if st.button("🚀 تنفيذ الحصر الهندسي والمالي"):
            results, total_v = run_full_takeoff(df_raw, cols)
            if cols['price']:
                st.metric("💰 إجمالي قيمة المقايسة", f"{total_v:,.2f} ج.م")
            
            st.markdown("---")
            t1, t2, t3 = st.tabs(["🏗️ إنشاءات ومباني", "🎨 تشطيبات", "🚿 شبكات ومواسير"])
            with t1:
                c1, c2 = st.columns(2)
                c1.metric("أسمنت (طن)", f"{results['أسمنت بورتلاندي (طن)']:,.2f}")
                c1.metric("حديد تسليح (طن)", f"{results['حديد تسليح (طن)']:,.2f}")
                c2.metric("طوب (ألف)", f"{results['طوب (ألف طوبة)']:,.2f}")
                c2.metric("رمل وسن (م3)", f"{results['سن/زلط (م3)'] + results['رمل (م3)']:,.2f}")
            with t2:
                st.metric("سيراميك (م2)", f"{results['سيراميك (م2)']:,.2f}")
                st.metric("دهانات (بستلة)", f"{results['دهانات (بستلة)']:,.2f}")
            with t3:
                st.metric("مواسير حريق (م.ط)", f"{results['مواسير حريق (م.ط)']:,.2f}")
                st.metric("مواسير صرف (م.ط)", f"{results['مواسير صرف (م.ط)']:,.2f}")
                st.metric("محابس وقطع (عدد)", f"{results['محابس وقطع (عدد)']:,.2f}")
    else:
        st.error("❌ لم أتمكن من العثور على أعمدة البيان والكمية.")
        st.write("الأعمدة المكتشفة:", list(df_raw.columns))
