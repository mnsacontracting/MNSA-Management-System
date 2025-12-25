import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json

# دالة ذكية لإظهار الأخطاء بوضوح
def connect():
    try:
        # 1. التأكد من وجود المفتاح السري
        if "GCP_SERVICE_ACCOUNT_KEY" not in st.secrets:
            return "MissingSecrets"
            
        info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT_KEY"])
        creds = Credentials.from_service_account_info(info, 
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        
        # 2. ضع رابط الشيت الخاص بك هنا بدقة
        # تأكد من أن الرابط بين علامتي التنصيص
        url = "ضع_رابط_جوجل_شيت_الخاص_بك_هنا" 
        
        return client.open_by_url(url).sheet1
    except Exception as e:
        return str(e)

st.title("🏗️ نظام إدارة المناقصات MNSA")

result = connect()

if result == "MissingSecrets":
    st.error("❌ لم نجد المفاتيح السرية في إعدادات Streamlit. يرجى إضافتها في خانة Secrets.")
elif isinstance(result, str):
    st.error(f"❌ حدث خطأ أثناء الاتصال: {result}")
    st.info("نصيحة: تأكد من مشاركة (Share) ملف جوجل شيت مع الإيميل الموجود في ملف الـ JSON.")
else:
    st.success("✅ مبروك يا مصطفى! الاتصال ناجح والقاعدة جاهزة.")
    # خانات الإدخال
    tender_name = st.text_input("اسم المناقصة")
    if st.button("حفظ البيانات"):
        result.append_row([tender_name])
        st.balloons()
        st.success("تم الحفظ في جوجل شيت بنجاح!")
