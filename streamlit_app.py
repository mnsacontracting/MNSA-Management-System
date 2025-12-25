import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة
st.set_page_config(page_title="MNSA - المكتب الفني المتكامل", layout="wide")
st.title("🏗️ آلة المكتب الفني (إنشائي - تشطيبات - نجارة - شبكات)")

# --- محرك البحث الذكي عن الأعمدة (تم تصحيح الخطأ هنا) ---
def super_find_columns(df):
    targets = {
        'desc': ['بيان', 'بند', 'وصف', 'item', 'description', 'work', 'الأعمال'],
        'qty': ['كمية', 'كميات', 'qty', 'quantity', 'العدد', 'الكمية'],
        'price': ['فئة', 'سعر', 'price', 'rate', 'الفئة']
    }
    found = {'desc': None, 'qty': None, 'price': None}
    
    # تنظيف العناوين من المسافات
    df.columns = [str(c).strip() for c in df.columns]
    search_area = df.head(20).astype(str)
    
    for col in df.columns:
        c_name = str(col).lower()
        for key, keywords in targets.items():
            if any(k in c_name for k in keywords):
                found[key] = col
        
        # البحث داخل الخلايا إذا لم يجد في العناوين
        if found['desc'] is None or found['qty'] is None:
            for val in search_area[col]:
                val_clean = str(val).strip().lower()
                for key, keywords in targets.items(): # تم تعديل التسمية هنا لتطابق targets
                    if found[key] is None and any(k in val_clean for k in keywords):
                        found[key] = col
    return found

# --- دالة الحصر الهندسي الشاملة ---
def run_takeoff(df, cols):
    m = {
        "أسمنت (طن)": 0, "حديد (طن)": 0, "رمل (م3)": 0, "سن/زلط (م3)": 0, "طوب (ألف)": 0,
        "سيراميك (م2)": 0, "معجون دهانات (شكارة)": 0, "دهان بلاستيك (بستلة)": 0,
        "أبواب (عدد)": 0, "شبابيك (عدد)": 0,
        "مواسير حريق (م.ط)": 0, "مواسير صرف (م.ط)": 0, "قطع/محابس (عدد)": 0
    }
    total_val = 0
    
    # تحويل الكمية لأرقام وتجاهل الأخطاء
    df[cols['qty']] = pd.to_numeric(df[cols['qty']], errors='coerce')
    df_clean = df.dropna(subset=[cols['qty']])

    for _, row in df_clean.iterrows():
        try:
            item = str(row[cols['desc']]).lower()
            qty = float(row[cols['qty']])
            price = pd.to_numeric(row[cols['price']], errors='coerce') if cols['price'] else 0
            total_val += (qty * price)

            # --- الإنشاءات ---
            if any(x in item for x in ["مسلحة", "ميد", "أعمدة", "سقف", "كمرة"]):
                m["أسمنت (طن)"] += qty * 0.35; m["حديد (طن)"] += qty * 0.095
                m["رمل (م3)"] += qty * 0.4; m["سن/زلط (م3)"] += qty * 0.8
            elif "عادية" in item:
                m["أسمنت (طن)"] += qty * 0.25; m["رمل (م3)"] += qty * 0.4; m["سن/زلط (م3)"] += qty * 0.8
            
            # --- الدهانات والتشطيبات ---
            if any(x in item for x in ["دهانات", "بلاستيك", "نقاشة"]):
                m["معجون دهانات (شكارة)"] += qty * 0.06
                m["دهان بلاستيك (بستلة)"] += qty / 25
            if "سيراميك" in item or "بلاط" in item: m["سيراميك (م2)"] += qty
            if "مباني" in item: m["طوب (ألف)"] += qty * 0.06

            # --- النجارة ---
            if "باب" in item or "أبواب" in item: m["أبواب (عدد)"] += qty
            if "شباك" in item or "شبابيك" in item: m["شبابيك (عدد)"] += qty

            # --- الشبكات ---
            if "حريق" in item: m["مواسير حريق (م.ط)"] += qty
            elif any(x in item for x in ["صرف", "upvc", "مواسير"]): m["مواسير صرف (م.ط)"] += qty
            if any(x in item for x in ["محبس", "صندوق", "قطع"]): m["قطع/محابس (عدد)"] += qty

        except: continue
    return m, total_val

# --- الواجهة ---
file = st.file_uploader("ارفع المقايسة (Excel)", type=['xlsx', 'xls'])

if file:
    df = pd.read_excel(file)
    cols = super_find_columns(df)
    
    if cols['desc'] and cols['qty']:
        st.success(f"🎯 تم العثور على الأعمدة بنجاح")
        if st.button("🚀 تحليل وحصر المقايسة بالكامل"):
            res, total = run_takeoff(df, cols)
            if total > 0: st.metric("💰 إجمالي قيمة المقايسة", f"{total:,.2f} ج.م")
            
            st.markdown("---")
            tabs = st.tabs(["🏗️ إنشائي ومباني", "🎨 دهانات وتشطيبات", "🚪 نجارة", "🚿 شبكات"])
            
            with tabs[0]:
                c1, c2 = st.columns(2)
                c1.metric("أسمنت (طن)", f"{res['أسمنت (طن)']:,.2f}")
                c1.metric("حديد (طن)", f"{res['حديد (طن)']:,.2f}")
                c2.metric("طوب (ألف)", f"{res['طوب (ألف)']:,.2f}")
                c2.metric("رمل وسن (م3)", f"{res['رمل (م3)'] + res['سن/زلط (م3)']:,.2f}")
            with tabs[1]:
                c1, c2 = st.columns(2)
                c1.metric("سيراميك (م2)", f"{res['سيراميك (م2)']:,.2f}")
                c1.metric("بستلات دهان", f"{res['دهان بلاستيك (بستلة)']:,.2f}")
                c2.metric("شكاير معجون", f"{res['معجون دهانات (شكارة)']:,.2f}")
            with tabs[2]:
                c1, c2 = st.columns(2)
                c1.metric("أبواب (عدد)", f"{res['أبواب (عدد)']:,.2f}")
                c2.metric("شبابيك (عدد)", f"{res['شبابيك (عدد)']:,.2f}")
            with tabs[3]:
                st.metric("مواسير حريق (م.ط)", f"{res['مواسير حريق (م.ط)']:,.2f}")
                st.metric("مواسير صرف (م.ط)", f"{res['مواسير صرف (م.ط)']:,.2f}")
                st.metric("قطع ومحابس (عدد)", f"{res['قطع/محابس (عدد)']:,.2f}")
    else:
        st.error("❌ فشل الرادار في العثور على أعمدة البيان والكمية.")
        st.write("الأعمدة المكتشفة في ملفك:", list(df.columns))
