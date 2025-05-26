from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time
import re

def scrape_weather():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--user-data-dir=/tmp/chrome-data") 

    driver = webdriver.Chrome(options=options)

    driver.get("https://www.tmd.go.th/weather/province/past24Hr/rayong/55/478301")

    try:
        table = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except TimeoutException:
        driver.quit()
        raise Exception("โหลดตารางไม่สำเร็จภายใน 10 วินาที")

    rows = table.find_elements(By.TAG_NAME, "tr")
    data = []
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
        data.append([cell.text.strip() for cell in cells])

    driver.quit()

    header_len = len(data[0]) + len(data[1]) - 1
    clean_data = [row for row in data[1:] if len(row) in {header_len, header_len - 1, header_len + 1}]
    for row in clean_data:
        if len(row) < header_len:
            row.insert(5, '-')
            row[6] = '0'

    columns = ['วันที่', 'อุณหภูมิ (°C)', 'จุดน้ำค้าง (°C)', 'ความชื้นสัมพัทธ์ (%)', 'ความกดอากาศ (hPa)',
               'ทิศลม', 'ความเร็วลม (กม./ชม.)', 'ทัศนวิสัย (กม.)', 'ฝน 3 ชม. (มม.)', 'เมฆ']
    valid_data = [row for row in clean_data if len(row) == len(columns)]

    df = pd.DataFrame(valid_data, columns=columns)

    def thai_date_to_datetime(thai_date_str):
        thai_months = {
            'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4, 'พฤษภาคม': 5,
            'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8, 'กันยายน': 9, 'ตุลาคม': 10,
            'พฤศจิกายน': 11, 'ธันวาคม': 12
        }

        pattern = r'(\d{1,2})\s+([ก-๙]+)\s+(\d{4})\s+เวลา\s+(\d{1,2}):(\d{2})'
        match = re.search(pattern, thai_date_str)
        if not match:
            return None

        day = int(match.group(1))
        month_name = match.group(2)
        year = int(match.group(3)) - 543
        hour = int(match.group(4))
        minute = int(match.group(5))
        month = thai_months.get(month_name)
        if not month:
            return None
        return pd.Timestamp(year, month, day, hour, minute)

    df['datetime'] = df['วันที่'].apply(thai_date_to_datetime)
    df = df.dropna(subset=['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    df = df.drop(columns=['datetime'])

    return df
