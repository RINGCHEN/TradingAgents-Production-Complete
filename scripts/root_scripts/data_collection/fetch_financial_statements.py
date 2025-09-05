from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import os
import pandas as pd
import yaml

def fetch_financial_statements(stock_id="2330", report_type="IS_M_QUAR"):
    """
    Uses Selenium to fetch a financial statement from Goodinfo, parse the main table,
    and save the data to a CSV file.
    """
    url = f"https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT={report_type}&STOCK_ID={stock_id}"
    
    print(f"Attempting to fetch page with Selenium: {url}")
    
    # --- Selenium Setup ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1200")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")
    webdriver_path = os.path.join(os.getcwd(), 'chromedriver.exe')
    service = Service(executable_path=webdriver_path)
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(url)
        print("Waiting for page to render...")
        time.sleep(5)
        html = driver.page_source
        print("Page source captured.")

        # --- BeautifulSoup Parsing ---
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table', {'id': 'tblFinDetail'})
        
        if not table:
            print("Error: Could not find the data table with id='tblFinDetail'.")
            return

        print("Successfully found the data table 'tblFinDetail'. Parsing data...")

        # --- Header Extraction (Robust V3 Logic) ---
        header_rows = table.find_all('tr', {'class': 'bg_h1'})
        if len(header_rows) < 2:
            print("\nError: Could not find the expected header rows.")
            return
        
        main_header_row = header_rows[0]
        sub_header_row = header_rows[1]

        quarters = [th.text.strip() for th in main_header_row.find_all('th') if th.has_attr('colspan')]
        
        final_headers = [main_header_row.find('th').text.strip()] # First column, e.g., '獲利能力'
        for quarter in quarters:
            final_headers.append(f"{quarter}_金額")
            final_headers.append(f"{quarter}_％")
        
        print("Successfully parsed column headers.")

        # --- Header and Data Extraction (Conditional Logic for CF_M_QUAR) ---
        if report_type == "CF_M_QUAR":
            # Special handling for Cash Flow Statement due to different header structure
            header_rows = table.find_all('tr', {'class': 'bg_h1'})
            if len(header_rows) < 2:
                print("Error: Could not find expected header rows for CF_M_QUAR.")
                return
            
            # First row contains main categories (e.g., '營業活動')
            main_categories_row = header_rows[0]
            # Second row contains quarters (e.g., '2025Q2')
            quarters_row = header_rows[1]

            # The first element is the main category name (e.g., '營業活動')
            first_col_header = header_rows[0].find('th').text.strip()
            
            # The rest are the quarter names (e.g., '2025Q2', '2025Q1', ...)
            # We need to find all <th> elements in this row, and skip the first one.
            quarter_names = [th.text.strip() for th in header_rows[0].find_all('th')][1:] # Skip the first <th>

            # Construct the final headers: [Main Category, Quarter1, Quarter2, ...]
            final_headers = [first_col_header] + quarter_names

            print("Successfully parsed CF_M_QUAR column headers.")

            # Data Row Extraction for CF_M_QUAR
            all_rows_data = []
            data_rows = table.find_all('tr', id=lambda x: x and x.startswith('row'))

            for row in data_rows:
                row_name = row.find('th').text.strip()
                columns = [row_name] + [td.text.strip().replace('\n', '').replace('\r', '') for td in row.find_all('td')]
                all_rows_data.append(columns)

            df = pd.DataFrame(all_rows_data, columns=final_headers)

        else:
            # Existing logic for IS_M_QUAR and BS_M_QUAR
            header_rows = table.find_all('tr', {'class': 'bg_h1'})
            if len(header_rows) < 2:
                print("Error: Could not find the expected header rows.")
                return
            
            main_header_row = header_rows[0]
            sub_header_row = header_rows[1]

            quarters = [th.text.strip() for th in main_header_row.find_all('th') if th.has_attr('colspan')]
            
            final_headers = [main_header_row.find('th').text.strip()]
            for quarter in quarters:
                final_headers.append(f"{quarter}_金額")
                final_headers.append(f"{quarter}_％")
            
            print("Successfully parsed column headers.")

            all_rows_data = []
            data_rows = table.find_all('tr', id=lambda x: x and x.startswith('row'))

            for row in data_rows:
                row_name = row.find('th').text.strip()
                columns = [row_name] + [td.text.strip().replace('\n', '').replace('\r', '') for td in row.find_all('td')]
                all_rows_data.append(columns)

            df = pd.DataFrame(all_rows_data, columns=final_headers)

        # --- DataFrame and CSV Creation ---
        df = pd.DataFrame(all_rows_data, columns=final_headers)
        print(f"Successfully parsed {len(df)} rows of data.")

        # Load storage path from config
        with open("configs/data_sources.yaml", 'r', encoding='utf-8') as f:
            data_cfg = yaml.safe_load(f)
        
        storage_base = data_cfg['storage']['base_path']
        raw_subdir = data_cfg['storage']['raw_subdir']
        output_dir = os.path.join(storage_base, raw_subdir, 'financial_reports')
        os.makedirs(output_dir, exist_ok=True)

        output_filename = f"{stock_id}_{report_type}.csv"
        output_path = os.path.join(output_dir, output_filename)

        df.to_csv(output_path, index=False, encoding='utf_8_sig')
        print(f"\nSuccessfully saved financial data to: {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if driver:
            print("Closing the browser.")
            driver.quit()

if __name__ == '__main__':
    stock_id_to_fetch = "2330" # Define the stock ID here
    report_types_to_fetch = ["IS_M_QUAR", "BS_M_QUAR", "CF_M_QUAR"]
    
    for rpt_type in report_types_to_fetch:
        print(f"\n--- Fetching {rpt_type} for {stock_id_to_fetch} ---")
        fetch_financial_statements(stock_id=stock_id_to_fetch, report_type=rpt_type)
        time.sleep(2) # Add a small delay between requests to be polite to the server
    print("\nAll financial reports fetched successfully.")


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

