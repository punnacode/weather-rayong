from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    options.add_argument("--user-data-dir=/tmp/chrome-data")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")

    driver = webdriver.Chrome(options=options)
    
    try:
        print("Loading page...")
        driver.get("https://www.tmd.go.th/weather/province/past24Hr/rayong/55/478301")

        time.sleep(5)

        table = None
        tbody = None

        try:
            print("Looking for table with ID 'tableWeatherPast24Hours'...")
            table = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.ID, "tableWeatherPast24Hours"))
            )
            print("Found table by ID")
            
            # Also try to find the tbody specifically
            try:
                tbody = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "tbody24Hours"))
                )
                print("Found tbody by ID")
            except TimeoutException:
                print("Could not find tbody by ID, will use table")
                
        except TimeoutException:
            print("Could not find table by ID, trying other selectors...")

            selectors = [
                "table",
                ".table",
                "table.table",
                "[class*='table']",
                "div table",
                "#content table"
            ]
            
            for selector in selectors:
                try:
                    print(f"Trying selector: {selector}")
                    if selector == "table":
                        table = WebDriverWait(driver, 20).until(
                            EC.presence_of_element_located((By.TAG_NAME, "table"))
                        )
                    else:
                        table = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    print(f"Found table with selector: {selector}")
                    break
                except TimeoutException:
                    print(f"Selector {selector} failed")
                    continue
        
        if table is None:
 
            print("Trying to find any table-like elements...")
            page_source = driver.page_source
            print(f"Page title: {driver.title}")
            print(f"Page URL: {driver.current_url}")

            if "404" in page_source or "ไม่พบหน้า" in page_source:
                raise Exception("หน้าเว็บไม่พบ (404)")

            table_divs = driver.find_elements(By.CSS_SELECTOR, "div[class*='table'], div[id*='table']")
            if table_divs:
                table = table_divs[0]
                print("Found table-like div element")
            else:
                raise Exception("ไม่พบตารางข้อมูลในหน้าเว็บ")

        print("Extracting data from table...")

        data_container = tbody if tbody else table
        
        rows = []
        try:
            rows = data_container.find_elements(By.TAG_NAME, "tr")
            print(f"Found {len(rows)} tr elements")
        except:
            print("No tr elements found, trying other approaches...")

            rows = data_container.find_elements(By.CSS_SELECTOR, "[class*='row'], div")
        
        if not rows:
            raise Exception("ไม่พบแถวข้อมูลในตาราง")
        
        print(f"Total rows found: {len(rows)}")
        
        data = []
        header_found = False
        
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "th") + row.find_elements(By.TAG_NAME, "td")
                if not cells:
                    cells = row.find_elements(By.CSS_SELECTOR, "div, span")
                
                texts = [cell.text.strip() for cell in cells if cell.text.strip()]

                if not texts:
                    continue

                if not header_found and any(keyword in ''.join(texts) for keyword in ['วันที่', 'อุณหภูมิ', 'ความชื้น', 'จุดน้ำค้าง']):
                    header_found = True
                    print(f"Header row {i}: {texts}")
                    continue

                if len(texts) >= 4:
                    data.append(texts[:4])
                    print(f"Data row {i}: {texts[:4]}")
                elif len(texts) >= 2:

                    print(f"Partial row {i}: {texts}")
                
            except Exception as e:
                print(f"Error processing row {i}: {e}")
                continue

        if not data:
            raise Exception("ไม่สามารถดึงข้อมูลจากตารางได้")

    except Exception as e:
        print(f"Error during scraping: {e}")

        try:
            with open("/tmp/page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("Page source saved to /tmp/page_source.html for debugging")
        except:
            pass
        raise e
    
    finally:
        driver.quit()

    data = [row for row in data if len(row) == 4]
    
    if len(data) < 1:  
        raise Exception("ข้อมูลไม่เพียงพอ - ไม่พบข้อมูลที่สามารถใช้งานได้")

    columns = ['วันที่', 'อุณหภูมิ (°C)', 'จุดน้ำค้าง (°C)', 'ความชื้นสัมพัทธ์ (%)']
    df = pd.DataFrame(data, columns=columns)

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

    # Process datetime
    df['datetime'] = df['วันที่'].apply(thai_date_to_datetime)
    df = df.dropna(subset=['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    df = df.drop(columns=['datetime'])

    print(f"Successfully scraped {len(df)} records")
    return df

def scrape_weather_alternative():
    """
    Alternative scraping method using requests and BeautifulSoup
    This is often more reliable than Selenium for static content
    """
    import requests
    from bs4 import BeautifulSoup
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'th-TH,th;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(
            "https://www.tmd.go.th/weather/province/past24Hr/rayong/55/478301",
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        table = soup.find('table', id='tableWeatherPast24Hours')
        if not table:
            table = soup.find('table')
        if not table:
            tables = soup.find_all(['div', 'section'], class_=lambda x: x and 'table' in x.lower())
            if tables:
                table = tables[0]
            else:
                raise Exception("ไม่พบตารางข้อมูล")

        tbody = table.find('tbody', id='tbody24Hours') if table else None
        data_container = tbody if tbody else table

        rows = data_container.find_all('tr') if data_container else []
        if not rows:
            rows = data_container.find_all(['div', 'p']) if data_container else []
            
        data = []
        
        for row in rows:
            cells = row.find_all(['td', 'th']) or row.find_all(['span', 'div'])
            texts = [cell.get_text().strip() for cell in cells if cell.get_text().strip()]

            if texts and not any(keyword in ''.join(texts) for keyword in ['วันที่', 'อุณหภูมิ', 'ความชื้น']):
                if len(texts) >= 4:
                    data.append(texts[:4])
        
        if len(data) < 1:
            raise Exception("ข้อมูลไม่เพียงพอ")

        columns = ['วันที่', 'อุณหภูมิ (°C)', 'จุดน้ำค้าง (°C)', 'ความชื้นสัมพัทธ์ (%)']
        df = pd.DataFrame(data, columns=columns)
        
        return df
        
    except Exception as e:
        print(f"Alternative scraping failed: {e}")
        raise e
