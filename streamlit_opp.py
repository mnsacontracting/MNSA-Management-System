import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# دالة الاتصال بجوجل شيت
def connect_to_sheet():
    try:
        # استدعاء المفتاح السري الذي وضعناه سابقاً في Secrets
        key_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_KEY"])
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(key_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # --- هام جداً: ضع رابط جوجل شيت الخاص بك هنا بين علامتي التنصيص ---
        sheet_url = "ضع_رابط_جوجل_شيت_الخاص_بك_هنا" 
        
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال بالقاعدة: {e}")
        return None

# إعدادات واجهة الصفحة
st.set_page_config(page_title="نظام MNSA الذكي", layout="wide")
st.title("🏗️ نظام إدارة المناقصات (MNSA)")

# محاولة الاتصال
sheet = connect_to_sheet()

if sheet:
    st.success("✅ تم الاتصال بجوجل شيت بنجاح!")
    
    # واجهة إدخال البيانات
    with st.form("tender_form"):
        st.subheader("إضافة بيانات مناقصة جديدة")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("اسم المناقصة")
        with col2:
            client = st.text_input("جهة الإسناد")
            
        value = st.number_input("القيمة التقديرية (اختياري)", min_value=0)
        
        submit_button = st.form_submit_button("حفظ في جوجل شيت")
        
        if submit_button:
            if name:
                # إضافة سطر جديد للشيت (اسم، جهة، قيمة)
                sheet.append_row([name, client, "", value])
                st.balloons()
                st.success(f"تم حفظ '{name}' بنجاح!")
            else:
                st.warning("يرجى إدخال اسم المناقصة على الأقل.")
