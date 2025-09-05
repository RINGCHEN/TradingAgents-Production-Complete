import pandas as pd
import json
import os
import yaml
import numpy as np

def process_financial_statements_to_jsonl(stock_id="2330", report_types=None):
    """
    Reads raw financial statement CSVs for multiple report types, and transforms each quarter's data
    into prompt-completion pairs, saved in a single combined JSONL file.
    Includes caching to avoid reprocessing unchanged data.
    """
    if report_types is None:
        report_types = ["IS_M_QUAR", "BS_M_QUAR", "CF_M_QUAR"]

    print("Starting comprehensive financial data processing...")

    # --- Load Paths from Config ---
    try:
        with open("configs/data_sources.yaml", 'r', encoding='utf-8') as f:
            data_cfg = yaml.safe_load(f)
        
        # Use environment variable if available, otherwise fallback to config
        storage_base = os.environ.get('TRADING_AGENTS_DATA_DIR')
        if not storage_base:
            print("Warning: TRADING_AGENTS_DATA_DIR environment variable not set.")
            # Assuming the script is run from the project root, construct path relative to it
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            storage_base = os.path.join(project_root, 'ai_training_data')
            print(f"Falling back to default path: {storage_base}")

        raw_subdir = data_cfg['storage']['raw_subdir']
        processed_subdir = data_cfg['storage']['processed_subdir']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # Define input and output directories
    input_dir = os.path.join(storage_base, raw_subdir, 'financial_reports')
    output_dir = os.path.join(storage_base, processed_subdir)
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl_path = os.path.join(output_dir, f"{stock_id}_financial_reports_processed.jsonl")

    # --- Caching Logic ---
    input_csv_paths = [os.path.join(input_dir, f"{stock_id}_{rpt_type}.csv") for rpt_type in report_types]
    
    cache_is_valid = False
    if os.path.exists(output_jsonl_path):
        cache_is_valid = True
        output_mtime = os.path.getmtime(output_jsonl_path)
        for input_path in input_csv_paths:
            if os.path.exists(input_path):
                if os.path.getmtime(input_path) > output_mtime:
                    print(f"Cache invalidated by updated file: {os.path.basename(input_path)}")
                    cache_is_valid = False
                    break
            # If an input file doesn't exist, we can't be sure, so we might need to reprocess
            # but for this logic, we assume missing files are handled later.
    
    if cache_is_valid:
        print(f"Cache is valid. Skipping processing. Processed data already exists at {output_jsonl_path}")
        return
    # --- End Caching Logic ---

    all_processed_examples = []

    for rpt_type in report_types:
        input_csv_path = os.path.join(input_dir, f"{stock_id}_{rpt_type}.csv")
        
        try:
            df = pd.read_csv(input_csv_path)
            print(f"Successfully read {input_csv_path}")
        except FileNotFoundError:
            print(f"Warning: Input file not found at {input_csv_path}. Skipping {rpt_type}.")
            continue
        except Exception as e:
            print(f"Error reading {input_csv_path}: {e}. Skipping {rpt_type}.")
            continue

        # Set the financial item as the index for easier lookup
        df.set_index(df.columns[0], inplace=True)

        # Extract quarters from column names (e.g., '2025Q2_金額' -> '2025Q2')
        # Assuming all columns have _金額 or _% suffix for IS/BS, or are just quarter names for CF
        quarters = sorted(list(set([col.split('_')[0] for col in df.columns if '_' in col])), reverse=True)
        if not quarters and rpt_type == "CF_M_QUAR": # Handle CF_M_QUAR which has simple quarter names
            quarters = sorted(list(set([col for col in df.columns])), reverse=True)

        for quarter in quarters:
            prompt_text = ""
            completion_text = ""
            
            # --- Conditional Logic for Prompt/Completion Generation based on Report Type ---
            if rpt_type == "IS_M_QUAR": # Income Statement
                key_items = ['營業收入', '營業毛利', '營業利益', '稅後淨利']
                prompt_data = []
                for item in key_items:
                    try:
                        amount = df.loc[item, f'{quarter}_金額']
                        prompt_data.append(f"{item}: {amount}")
                    except KeyError:
                        prompt_data.append(f"{item}: N/A") # Handle missing data
                
                prompt_text = f"請根據以下台積電({stock_id})在{quarter}的損益表數據，做一個簡要總結：\n" + "\n".join(prompt_data)

                try:
                    revenue = pd.to_numeric(df.loc['營業收入', f'{quarter}_金額'], errors='coerce')
                    gross_profit = pd.to_numeric(df.loc['營業毛利', f'{quarter}_金額'], errors='coerce')
                    net_profit = pd.to_numeric(df.loc['稅後淨利', f'{quarter}_金額'], errors='coerce')
                    gross_margin = (gross_profit / revenue * 100) if revenue != 0 else 0
                    net_margin = (net_profit / revenue * 100) if revenue != 0 else 0

                    completion_text = (
                        f"在{quarter}，公司營收為{revenue:,.0f}億元，"
                        f"營業毛利為{gross_profit:,.0f}億元，毛利率為{gross_margin:.2f}%。"
                        f"最終稅後淨利為{net_profit:,.0f}億元，淨利率為{net_margin:.2f}%。"
                    )
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Warning: Missing data for IS {quarter}: {e}")
                    continue # Skip this quarter if key data is missing

            elif rpt_type == "BS_M_QUAR": # Balance Sheet
                key_items = ['流動資產合計', '非流動資產合計', '流動負債合計', '非流動負債合計', '股東權益總額']
                prompt_data = []
                for item in key_items:
                    try:
                        amount = df.loc[item, f'{quarter}_金額']
                        prompt_data.append(f"{item}: {amount}")
                    except KeyError:
                        prompt_data.append(f"{item}: N/A")
                
                prompt_text = f"請根據以下台積電({stock_id})在{quarter}的資產負債表數據，做一個簡要總結：\n" + "\n".join(prompt_data)

                try:
                    current_assets = pd.to_numeric(df.loc['流動資產合計', f'{quarter}_金額'], errors='coerce')
                    non_current_assets = pd.to_numeric(df.loc['非流動資產合計', f'{quarter}_金額'], errors='coerce')
                    current_liabilities = pd.to_numeric(df.loc['流動負債合計', f'{quarter}_金額'], errors='coerce')
                    non_current_liabilities = pd.to_numeric(df.loc['非流動負債合計', f'{quarter}_金額'], errors='coerce')
                    shareholders_equity = pd.to_numeric(df.loc['股東權益總額', f'{quarter}_金額'], errors='coerce')

                    total_assets = current_assets + non_current_assets
                    total_liabilities = current_liabilities + non_current_liabilities

                    completion_text = (
                        f"在{quarter}，公司總資產為{total_assets:,.0f}億元，其中流動資產{current_assets:,.0f}億元。"
                        f"總負債為{total_liabilities:,.0f}億元，其中流動負債{current_liabilities:,.0f}億元。"
                        f"股東權益總額為{shareholders_equity:,.0f}億元。"
                    )
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Warning: Missing data for BS {quarter}: {e}")
                    continue

            elif rpt_type == "CF_M_QUAR": # Cash Flow Statement
                key_items = ['營業活動之淨現金流入(出)', '投資活動之淨現金流入(出)', '融資活動之淨現金流入(出)', '期末現金及約當現金餘額']
                prompt_data = []
                for item in key_items:
                    try:
                        amount = df.loc[item, quarter] # CF has simple quarter names as columns
                        prompt_data.append(f"{item}: {amount}")
                    except KeyError:
                        prompt_data.append(f"{item}: N/A")
                
                prompt_text = f"請根據以下台積電({stock_id})在{quarter}的現金流量表數據，做一個簡要總結：\n" + "\n".join(prompt_data)

                try:
                    operating_cf = pd.to_numeric(df.loc['營業活動之淨現金流入(出)', quarter], errors='coerce')
                    investing_cf = pd.to_numeric(df.loc['投資活動之淨現金流入(出)', quarter], errors='coerce')
                    financing_cf = pd.to_numeric(df.loc['融資活動之淨現金流入(出)', quarter], errors='coerce')
                    ending_cash = pd.to_numeric(df.loc['期末現金及約當現金餘額', quarter], errors='coerce')

                    completion_text = (
                        f"在{quarter}，公司營業活動淨現金為{operating_cf:,.0f}億元，"
                        f"投資活動淨現金為{investing_cf:,.0f}億元，融資活動淨現金為{financing_cf:,.0f}億元。"
                        f"期末現金餘額為{ending_cash:,.0f}億元。"
                    )
                except (KeyError, TypeError, ValueError) as e:
                    print(f"Warning: Missing data for CF {quarter}: {e}")
                    continue

            if prompt_text and completion_text:
                all_processed_examples.append({"prompt": prompt_text, "completion": completion_text})

    # --- Write to JSONL file ---
    # This part only runs if the cache was invalid
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for example in all_processed_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\nSuccessfully processed {len(all_processed_examples)} examples and saved to: {output_jsonl_path}")

if __name__ == '__main__':
    # You can add argument parsing here to make the script more flexible
    import argparse
    parser = argparse.ArgumentParser(description="Process financial statements into JSONL format for AI training.")
    parser.add_argument("--stock_id", type=str, default="2330", help="Stock ID to process.")
    args = parser.parse_args()
    
    process_financial_statements_to_jsonl(stock_id=args.stock_id)



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

