import streamlit as st
import pandas as pd

st.set_page_config(page_title="MNSA - المكتب الفني", layout="wide")
st.title("🏗️ آلة المكتب الفني (رادار الأعمدة الذكي)")

# --- محرك البحث المتقدم عن الأعمدة ---
def super_find_columns(df):
    targets = {
        'desc': ['بيان', 'بند', 'وصف', 'item', 'description', 'work'],
        'qty': ['كمية', 'كميات', 'qty', 'quantity', 'العدد'],
        'price': ['فئة', 'سعر', 'price', 'rate']
    }
    found = {'desc': None, 'qty': None, 'price': None}
    
    # تحويل أول 20 صفاً إلى نص للبحث فيها
    search_area = df.head(20).astype(str)
    
    for col in df.columns:
        # 1. البحث في اسم العمود نفسه
        c_name = str(col).strip().lower()
        for key, keywords in targets.items():
            if any(k in c_name for k in keywords):
                found[key] = col
        
        # 2. البحث داخل خلايا العمود (في حال وجود خلايا مدمجة أو عناوين تائهة)
        if found['desc'] is None or found['qty'] is None:
            for val in search_area[col]:
                val_clean = val.strip().lower()
                for key, keywords in targets.items():
                    if found[key] is None and any(k in val_clean for k in keywords):
                        found[key] = col
    return found

# --- دالة الحصر الشامل ---
def run_takeoff(df, cols):
    m = {
        "أسمنت (طن)": 0, "حديد (طن)": 0, "رمل (م3)": 0, "سن (م3)": 0,
        "طوب (ألف)": 0, "سيراميك (م2)": 0, "دهانات (بستلة)": 0, 
        "مواسير حريق (م.ط)": 0, "مواسير صرف (م.ط)": 0, "قطع/محابس (عدد)": 0
    }
    total_val = 0
    
    # محاولة تنظيف البيانات (حذف الصفوف التي لا تحتوي على أرقام في خانة الكمية)
    df[cols['qty']] = pd.to_numeric(df[cols['qty']], errors='coerce')
    df_clean = df.dropna(subset=[cols['qty']])

    for _, row in df_clean.iterrows():
        try:
            item = str(row[cols['desc']]).lower()
            qty = float(row[cols['qty']])
            price = pd.to_numeric(row[cols['price']], errors='coerce') if cols['price'] else 0
            total_val += (qty * price)

            # --- منطق الحصر ---
            if any(x in item for x in ["مسلحة", "ميد", "أعمدة", "سقف"]):
                m["أسمنت (طن)"] += qty * 0.35; m["حديد (طن)"] += qty * 0.095
                m["رمل (م3)"] += qty * 0.4; m["سن (م3)"] += qty * 0.8
            elif "عادية" in item:
                m["أسمنت (طن)"] += qty * 0.25; m["رمل (م3)"] += qty * 0.4; m["سن (م3)"] += qty * 0.8
            if "حريق" in item: m["مواسير حريق (م.ط)"] += qty
            if "صرف" in item or "upvc" in item: m["مواسير صرف (م.ط)"] += qty
            if "سيراميك" in item: m["سيراميك (م2)"] += qty
            if "مباني" in item: m["طوب (ألف)"] += qty * 0.06
        except: continue
    return m, total_val

# --- الواجهة ---
file = st.file_uploader("ارفع المقايسة", type=['xlsx', 'xls'])

if file:
    df = pd.read_excel(file)
    # عرض شكل الملف للتأكد
    with st.expander("🔍 معاينة الملف كما يراه النظام"):
        st.write(df.head(15))
    
    cols = super_find_columns(df)
    
    if cols['desc'] and cols['qty']:
        st.success(f"🎯 رادار MNSA وجد الأعمدة: البيان [{cols['desc']}] | الكمية [{cols['qty']}]")
        if st.button("🚀 تحليل وحصر المقايسة"):
            res, total = run_takeoff(df, cols)
            if total > 0: st.metric("💰 إجمالي قيمة العقد", f"{total:,.2f} ج.م")
            
            st.markdown("---")
            tabs = st.tabs(["🏗️ إنشائي ومباني", "🎨 تشطيبات", "🚿 شبكات"])
            with tabs[0]:
                c1, c2 = st.columns(2)
                c1.metric("أسمنت (طن)", f"{res['أسمنت (طن)']:,.2f}")
                c1.metric("حديد (طن)", f"{res['حديد (طن)']:,.2f}")
                c2.metric("طوب (ألف)", f"{res['طوب (ألف)']:,.2f}")
                c2.metric("رمل وسن (م3)", f"{res['رمل (م3)'] + res['سن (م3)']:,.2f}")
            with tabs[1]:
                st.metric("سيراميك (م2)", f"{res['سيراميك (م2)']:,.2f}")
            with tabs[2]:
                st.metric("مواسير حريق (م.ط)", f"{res['مواسير حريق (م.ط)']:,.2f}")
                st.metric("مواسير صرف (م.ط)", f"{res['مواسير صرف (م.ط)']:,.2f}")
    else:
        st.error("❌ فشل الرادار في العثور على الأعمدة.")
        st.write("أسماء الأعمدة المتاحة حالياً في ملفك:", list(df.columns))
        st.info("💡 نصيحة المهندس: تأكد أن ملف الإكسل يبدأ بجدول البيانات مباشرة ولا توجد نصوص كثيرة فوق جدول الكميات.")
