import streamlit as st
from weather_report import scrape_weather
import io

st.set_page_config(page_title="Rayong Weather", layout="centered")

st.title("📈 รายงานสภาพอากาศจังหวัดระยอง - ห้วยโป่ง สกษ. (ย้อนหลัง 24 ชั่วโมง)")

if st.button("📥 ดาวน์โหลดข้อมูลอากาศ (CSV)"):
    with st.spinner("กำลังดึงข้อมูล..."):
        df = scrape_weather()
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        buffer = io.BytesIO()
        buffer.write(csv.encode('utf-8-sig'))
        buffer.seek(0)
        st.success("ดึงข้อมูลสำเร็จแล้ว ✅")
        st.download_button(
            label="คลิกเพื่อดาวน์โหลด CSV",
            data=buffer,
            file_name="rayong_weather.csv",
            mime="text/csv"
        )
