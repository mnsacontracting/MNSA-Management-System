import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# دالة الاتصال بجوجل شيت
def connect_to_sheet():
    try:
        # استدعاء المفتاح السري من Secrets
        key_dict = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_KEY"])
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(key_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # --- ضع رابط جوجل شيت الخاص بك هنا ---
        sheet_url = "ضع_رابط_جوجل_شيت_الخاص_بك_هنا" 
        
        return client.open_by_url(sheet_url).sheet1
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None

st.title("🏗️ نظام إدارة المناقصات (MNSA)")

sheet = connect_to_sheet()

if sheet:
    st.success("✅ متصل الآن بجوجل شيت!")
    name = st.text_input("اسم المناقصة")
    client = st.text_input("جهة الإسناد")
    if st.button("حفظ"):
        sheet.append_row([name, client])
        st.balloons()
        st.success("تم الحفظ بنجاح!")
