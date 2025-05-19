from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import time
import re

def scrape_weather():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    driver = webdriver.Chrome(options=options)

    driver.get("https://www.tmd.go.th/weather/province/past24Hr/rayong/55/478301")
    time.sleep(5)

    table = driver.find_element(By.TAG_NAME, "table")
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
        clean_str = re.sub(r'เวลา\s*|\s*น\.', '', thai_date_str)
        parts = clean_str.split()

        if len(parts) < 5 or ':' not in parts[4]:
            return None  

        try:
            day = int(parts[0])
            thai_months = {
                'มกราคม': 1, 'กุมภาพันธ์': 2, 'มีนาคม': 3, 'เมษายน': 4, 'พฤษภาคม': 5,
                'มิถุนายน': 6, 'กรกฎาคม': 7, 'สิงหาคม': 8, 'กันยายน': 9, 'ตุลาคม': 10,
                'พฤศจิกายน': 11, 'ธันวาคม': 12
            }
            month = thai_months.get(parts[1], 1)
            year = int(parts[2]) - 543
            hour, minute = map(int, parts[4].split(':'))
            return pd.Timestamp(year, month, day, hour, minute)
        except:
            return None


    df['datetime'] = df['วันที่'].apply(thai_date_to_datetime)
    df = df.sort_values('datetime').reset_index(drop=True)
    df = df.drop(columns=['datetime'])
    return df
