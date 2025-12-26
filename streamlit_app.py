import streamlit as st
import sqlite3
import pandas as pd
import os

# اسم قاعدة البيانات واسم ملف البيانات المرفوع
DB_NAME = "mnsa_company.db"
SQL_DUMP_FILE = "dump.sql"

def init_db():
    # التحقق مما إذا كانت قاعدة البيانات موجودة مسبقاً
    db_exists = os.path.exists(DB_NAME)
    conn = sqlite3.connect(DB_NAME)
    
    if not db_exists:
        st.warning("جاري ربط قاعدة بيانات الشركة لأول مرة من ملف SQL...")
        try:
            with open(SQL_DUMP_FILE, 'r', encoding='utf-16') as f: # ملفك مشفر utf-16 غالباً لأنه من SQL Server
                sql_script = f.read()
            
            # تنظيف السكريبت ليتوافق مع SQLite (حذف أوامر GO و USE)
            sql_script = sql_script.replace('GO', ';').replace('USE [master]', '')
            
            cursor = conn.cursor()
            cursor.executescript(sql_script)
            conn.commit()
            st.success("✅ تم ربط البيانات بنجاح!")
        except Exception as e:
            st.error(f"حدث خطأ أثناء الربط: {e}")
            # إنشاء جداول احتياطية في حال فشل القراءة
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS Projects (ProjectID INTEGER PRIMARY KEY, ProjectName TEXT)")
            conn.commit()
    return conn

conn = init_db()

# --- واجهة التحكم ---
st.title("🏗️ نظام MNSA المربوط بقاعدة البيانات")

# تجربة سحب المشاريع الحقيقية من ملفك
try:
    df_p = pd.read_sql_query("SELECT * FROM Projects", conn)
    if not df_p.empty:
        st.header("📊 المشاريع الموجودة في قاعدة بياناتك")
        st.dataframe(df_p)
    else:
        st.info("قاعدة البيانات مرتبطة ولكن لا توجد مشاريع مسجلة حالياً.")
except:
    st.error("فشل في قراءة جدول المشاريع. تأكد من رفع ملف dump.sql بجانب الكود.")
