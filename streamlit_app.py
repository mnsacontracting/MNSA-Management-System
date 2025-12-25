import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="MNSA ERP", layout="wide")
st.title("🏗️ آلة المكتب الفني المتكاملة - MNSA")

# --- محرك البحث عن الأعمدة ---
def find_columns(df):
    # مصفوفة الكلمات البحثية
    search_keywords = {
        'desc': ['بيان', 'بند', 'وصف', 'item', 'description', 'الأعمال'],
        'qty': ['كمية', 'كميات', 'qty', 'quantity', 'العدد'],
        'price': ['فئة', 'سعر', 'price', 'rate']
    }
    found_cols = {'desc': None, 'qty': None, 'price': None}
    
    # تنظيف أسماء الأعمدة
    df.columns = [str(c).strip() for c in df.columns]
    
    for col in df.columns:
        col_lower = col.lower()
        for key, words in search_keywords.items():
            if any(w in col_lower for w in words):
                found_cols[key] = col
                
    # بحث إضافي في أول صفوف إذا لم يجد
    if not found_cols['desc'] or not found_cols['qty']:
        for i in range(min(5, len(df))):
            for idx, cell in enumerate(df.iloc[i]):
                cell_str = str(cell).lower()
                for key, words in search_keywords.items():
                    if found_cols[key] is None and any(w in cell_str for w in words):
                        found_cols[key] = df.columns[idx]
    return found_cols

# --- دالة الحصر ---
def run_calculation(df, cols):
    results = {
        "أسمنت (طن)": 0, "حديد (طن)": 0, "رمل (م3)": 0, "سن (م3)": 0,
        "طوب (ألف)": 0, "سيراميك (م2)": 0, "دهانات (بستلة)": 0,
        "أبواب (عدد)": 0, "شبابيك (عدد)": 0, "مواسير (م.ط)": 0
    }
    total_price = 0
    
    # تحويل الكميات لأرقام
    df[cols['qty']] = pd.to_numeric(df[cols['qty']], errors='coerce')
    df_clean = df.dropna(subset=[cols['qty']])

    for _, row in df_clean.iterrows():
        item = str(row[cols['desc']]).lower()
        q = float(row[cols['qty']])
        p = pd.to_numeric(row[cols['price']], errors='coerce') if cols['price'] else 0
        total_price += (q * p)

        # منطق الحصر
        if any(x in item for x in ["مسلحة", "ميد", "أعمدة", "سقف"]):
            results["أسمنت (طن)"] += q * 0.35
            results["حديد (طن)"] += q * 0.09
            results["رمل (م3)"] += q * 0.4
            results["سن (م3)"] += q * 0.8
        elif "عادية" in item:
            results["أسمنت (طن)"] += q * 0.25
            results["رمل (م3)"] += q * 0.4
            results["سن (م3)"] += q * 0.8
        
        if "دهان" in item or "بلاستيك" in item:
            results["دهانات (بستلة)"] += q / 25
        if "سيراميك" in item: results["سيراميك (م2)"] += q
        if "باب" in item: results["أبواب (عدد)"] += q
        if "شباك" in item: results["شبابيك (عدد)"] += q
        if any(x in item for x in ["مواسير", "حريق", "صرف"]):
            results["مواسير (م.ط)"] += q

    return results, total_price

# --- الواجهة ---
file = st.file_uploader("ارفع ملف الإكسل", type=['xlsx', 'xls'])

if file:
    df = pd.read_excel(file)
    identified_cols = find_columns(df)
    
    if identified_cols['desc'] and identified_cols['qty']:
        st.success(f"✅ تم تحديد الأعمدة: {identified_cols['desc']} و {identified_cols['qty']}")
        if st.button("🚀 ابدأ الحصر الشامل"):
            final_res, total_val = run_calculation(df, identified_cols)
            
            if total_val > 0:
                st.metric("💰 إجمالي قيمة العقد", f"{total_val:,.2f} ج.م")
            
            st.markdown("---")
            t1, t2, t3 = st.tabs(["🏗️ إنشائي ومباني", "🎨 تشطيبات ونجارة", "🚿 شبكات"])
            
            with t1:
                c = st.columns(2)
                c[0].metric("أسمنت (طن)", f"{final_res['أسمنت (طن)']:,.2f}")
                c[0].metric("حديد (طن)", f"{final_res['حديد (طن)']:,.2f}")
                c[1].metric("رمل وسن (م3)", f"{final_res['رمل (م3)']+final_res['سن (م3)']:,.2f}")
                c[1].metric("طوب (ألف)", f"{final_res['طوب (ألف)']:,.2f}")
            
            with t2:
                c = st.columns(2)
                c[0].metric("سيراميك (م2)", f"{final_res['سيراميك (م2)']:,.2f}")
                c[0].metric("دهانات (بستلة)", f"{final_res['دهانات (بستلة)']:,.2f}")
                c[1].metric("أبواب (عدد)", f"{final_res['أبواب (عدد)']:,.2f}")
                c[1].metric("شبابيك (عدد)", f"{final_res['شبابيك (عدد)']:,.2f}")
            
            with t3:
                st.metric("مواسير شبكات (م.ط)", f"{final_res['مواسير (م.ط)']:,.2f}")
    else:
        st.error("❌ لم يتم التعرف على الأعمدة. تأكد من وجود عمود للوصف وعمود للكمية.")
