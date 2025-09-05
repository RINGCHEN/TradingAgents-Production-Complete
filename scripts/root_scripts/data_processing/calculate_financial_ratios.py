import pandas as pd
import os
import yaml
import numpy as np

def calculate_and_save_financial_ratios(stock_id="2330"):
    """
    Reads Income Statement, Balance Sheet, and Cash Flow Statement CSVs,
    calculates key financial ratios, and saves them to a new CSV.
    Includes caching to avoid reprocessing.
    """
    print(f"Starting financial ratio calculation for {stock_id}...")

    # --- Load Paths from Config ---
    try:
        with open("configs/data_sources.yaml", 'r', encoding='utf-8') as f:
            data_cfg = yaml.safe_load(f)
        
        storage_base = os.environ.get('TRADING_AGENTS_DATA_DIR')
        if not storage_base:
            print("Warning: TRADING_AGENTS_DATA_DIR environment variable not set.")
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            storage_base = os.path.join(project_root, 'ai_training_data')
            print(f"Falling back to default path: {storage_base}")

        raw_subdir = data_cfg['storage']['raw_subdir']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # Define input and output directories
    input_dir = os.path.join(storage_base, raw_subdir, 'financial_reports')
    output_dir = os.path.join(storage_base, raw_subdir, 'financial_ratios') # New directory for ratios
    os.makedirs(output_dir, exist_ok=True)
    output_csv_path = os.path.join(output_dir, f"{stock_id}_financial_ratios.csv")

    # --- Caching Logic ---
    input_files = [
        os.path.join(input_dir, f"{stock_id}_IS_M_QUAR.csv"),
        os.path.join(input_dir, f"{stock_id}_BS_M_QUAR.csv"),
        os.path.join(input_dir, f"{stock_id}_CF_M_QUAR.csv")
    ]

    cache_is_valid = False
    if os.path.exists(output_csv_path):
        cache_is_valid = True
        output_mtime = os.path.getmtime(output_csv_path)
        for input_file in input_files:
            if os.path.exists(input_file):
                if os.path.getmtime(input_file) > output_mtime:
                    print(f"Cache invalidated by updated file: {os.path.basename(input_file)}")
                    cache_is_valid = False
                    break
            else:
                # If a required input file is missing, cache is not valid, and we should attempt to run
                # The process will then fail gracefully later with a clear error message.
                cache_is_valid = False
                break
    
    if cache_is_valid:
        print(f"Cache is valid for {stock_id} financial ratios. Skipping calculation.")
        return
    # --- End Caching Logic ---

    # --- Load Financial Statements ---
    try:
        df_is = pd.read_csv(input_files[0], index_col=0)
        df_bs = pd.read_csv(input_files[1], index_col=0)
        df_cf = pd.read_csv(input_files[2], index_col=0)
        print("Successfully loaded financial statements.")
    except FileNotFoundError as e:
        print(f"Error: One or more financial statement files not found: {e}. Please run fetch_financial_statements.py first.")
        return
    except Exception as e:
        print(f"Error loading financial statements: {e}")
        return

    # --- Data Cleaning and Transposition ---
    def clean_df(df):
        df_t = df.T
        df_cleaned_str = df_t.astype(str).applymap(lambda x: x.replace(',', '').replace('-', '0'))
        df_numeric = df_cleaned_str.apply(pd.to_numeric, errors='coerce')
        return df_numeric

    df_is_t = clean_df(df_is)
    df_bs_t = clean_df(df_bs)
    df_cf_t = clean_df(df_cf)

    df_is_base = df_is_t.copy()
    df_is_base.index = [idx.split('_')[0] for idx in df_is_t.index]
    df_is_base = df_is_base.loc[~df_is_base.index.duplicated(keep='first')]

    df_bs_base = df_bs_t.copy()
    df_bs_base.index = [idx.split('_')[0] for idx in df_bs_t.index]
    df_bs_base = df_bs_base.loc[~df_bs_base.index.duplicated(keep='first')]

    df_cf_base = df_cf_t.copy()
    df_cf_base.index = [idx for idx in df_cf_t.index]
    df_cf_base = df_cf_base.loc[~df_cf_base.index.duplicated(keep='first')]

    common_quarters = sorted(list(set(df_is_base.index) & set(df_bs_base.index) & set(df_cf_base.index)))

    if not common_quarters:
        print("Error: No common quarters found. Ratios CSV will be empty.")
        ratios_df = pd.DataFrame(columns=['Gross Profit Margin', 'Operating Profit Margin', 'Net Profit Margin',
                                        'Current Ratio', 'Quick Ratio', 'Debt-to-Equity Ratio', 'ROA', 'ROE'])
        ratios_df.to_csv(output_csv_path, encoding='utf_8_sig')
        return

    df_is_filtered = df_is_base.loc[common_quarters]
    df_bs_filtered = df_bs_base.loc[common_quarters]
    df_cf_filtered = df_cf_base.loc[common_quarters]

    # --- Calculate Ratios ---
    ratios_df = pd.DataFrame(index=common_quarters)

    # Use .get() to avoid KeyErrors for missing columns
    ratios_df['Gross Profit Margin'] = (df_is_filtered.get('營業毛利', 0) / df_is_filtered.get('營業收入', np.nan)) * 100
    ratios_df['Operating Profit Margin'] = (df_is_filtered.get('營業利益', 0) / df_is_filtered.get('營業收入', np.nan)) * 100
    ratios_df['Net Profit Margin'] = (df_is_filtered.get('稅後淨利', 0) / df_is_filtered.get('營業收入', np.nan)) * 100

    ratios_df['Current Ratio'] = df_bs_filtered.get('流動資產合計', 0) / df_bs_filtered.get('流動負債合計', np.nan)
    ratios_df['Quick Ratio'] = (df_bs_filtered.get('流動資產合計', 0) - df_bs_filtered.get('存貨', 0)) / df_bs_filtered.get('流動負債合計', np.nan)

    ratios_df['Debt-to-Equity Ratio'] = df_bs_filtered.get('負債總額', 0) / df_bs_filtered.get('股東權益總額', np.nan)

    ratios_df['ROA'] = (df_is_filtered.get('稅後淨利', 0) / df_bs_filtered.get('資產總額', np.nan)) * 100
    ratios_df['ROE'] = (df_is_filtered.get('稅後淨利', 0) / df_bs_filtered.get('股東權益總額', np.nan)) * 100

    # Replace potential inf values with NaN
    ratios_df.replace([np.inf, -np.inf], np.nan, inplace=True)

    # --- Save Ratios to CSV ---
    ratios_df.to_csv(output_csv_path, encoding='utf_8_sig')
    print(f"\nSuccessfully calculated and saved financial ratios to: {output_csv_path}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Calculate and save financial ratios from raw financial statements.")
    parser.add_argument("--stock_id", type=str, default="2330", help="Stock ID to process.")
    args = parser.parse_args()
    calculate_and_save_financial_ratios(stock_id=args.stock_id)



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

