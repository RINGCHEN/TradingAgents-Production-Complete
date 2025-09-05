import pandas as pd
import json
import os
import yaml
import numpy as np

def process_financial_ratios_to_jsonl(stock_id="2330", output_filename="financial_ratios_processed.jsonl"):
    """
    Reads calculated financial ratios from CSV, generates prompt-completion pairs,
    and saves them to a new JSONL file for risk analysis training. Includes caching.
    """
    print(f"Starting financial ratio processing for {stock_id}...")

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
        processed_subdir = data_cfg['storage']['processed_subdir']
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # Define input and output paths
    input_dir = os.path.join(storage_base, raw_subdir, 'financial_ratios')
    input_csv_path = os.path.join(input_dir, f"{stock_id}_financial_ratios.csv")
    
    output_dir = os.path.join(storage_base, processed_subdir)
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl_path = os.path.join(output_dir, f"{stock_id}_{output_filename}")

    # --- Caching Logic ---
    if os.path.exists(output_jsonl_path) and os.path.exists(input_csv_path):
        if os.path.getmtime(output_jsonl_path) >= os.path.getmtime(input_csv_path):
            print(f"Cache is valid for {stock_id} ratio processing. Skipping. Processed data at {output_jsonl_path}")
            return
        else:
            print(f"Cache invalidated for {stock_id} ratio processing by updated input file.")
    # --- End Caching Logic ---

    all_processed_examples = []

    try:
        df_ratios = pd.read_csv(input_csv_path, index_col=0) # Quarters are index
        print(f"Successfully read {input_csv_path}")
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}. Please run calculate_financial_ratios.py first.")
        return
    except Exception as e:
        print(f"An error occurred reading input file: {e}")
        return

    # Iterate through each quarter (row) in the ratios DataFrame
    for quarter, row in df_ratios.iterrows():
        prompt_text = ""
        completion_text = ""
        
        # --- Create Prompt ---
        key_ratios = [
            'Gross Profit Margin', 'Operating Profit Margin', 'Net Profit Margin',
            'Current Ratio', 'Quick Ratio', 'Debt-to-Equity Ratio',
            'ROA', 'ROE'
        ]
        prompt_data = []
        for ratio in key_ratios:
            value = row.get(ratio)
            if pd.notna(value):
                prompt_data.append(f"{ratio}: {value:.2f}")
            else:
                prompt_data.append(f"{ratio}: N/A")
        
        prompt_text = f"請根據台積電({stock_id})在{quarter}的財務比率數據，判斷其財務風險等級（低、中、高）並說明原因：\n" + "\n".join(prompt_data)

        # --- Create Completion (Rule-based Risk Assessment) ---
        risk_level = "中等風險"
        reasons = []

        current_ratio = row.get('Current Ratio', np.nan)
        debt_to_equity = row.get('Debt-to-Equity Ratio', np.nan)
        net_profit_margin = row.get('Net Profit Margin', np.nan)

        if pd.notna(current_ratio):
            if current_ratio < 1.0:
                risk_level = "高風險"
                reasons.append(f"流動比率({current_ratio:.2f})過低，短期償債能力較差。")
            elif current_ratio < 1.5:
                risk_level = "中等風險"
                reasons.append(f"流動比率({current_ratio:.2f})偏低，短期償債能力需關注。")
            else:
                reasons.append(f"流動比率({current_ratio:.2f})良好，短期償債能力較強。")
        
        if pd.notna(debt_to_equity):
            if debt_to_equity > 2.0:
                risk_level = "高風險"
                reasons.append(f"負債權益比({debt_to_equity:.2f})過高，財務槓桿較大，償債風險較高。")
            elif debt_to_equity > 1.0:
                risk_level = "中等風險"
                reasons.append(f"負債權益比({debt_to_equity:.2f})偏高，需關注長期償債能力。")
            else:
                reasons.append(f"負債權益比({debt_to_equity:.2f})較低，財務結構穩健。")

        if pd.notna(net_profit_margin):
            if net_profit_margin < 0:
                risk_level = "高風險"
                reasons.append(f"淨利率({net_profit_margin:.2f}%)為負，公司處於虧損狀態。")
            elif net_profit_margin < 5 and risk_level != "高風險":
                risk_level = "中等風險"
                reasons.append(f"淨利率({net_profit_margin:.2f}%)偏低，盈利能力需提升。")

        if not any(r in risk_level for r in ["高風險", "中等風險"]):
             risk_level = "低風險"
             if not reasons: reasons.append("各項財務比率表現良好，財務風險較低。")

        completion_text = f"風險等級：{risk_level}。原因：{"".join(reasons)}"

        all_processed_examples.append({"prompt": prompt_text, "completion": completion_text})

    # --- Write to JSONL file ---
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for example in all_processed_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\nSuccessfully processed {len(all_processed_examples)} financial ratio examples and saved to: {output_jsonl_path}")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Process financial ratios into JSONL format for AI training.")
    parser.add_argument("--stock_id", type=str, default="2330", help="Stock ID to process.")
    args = parser.parse_args()
    process_financial_ratios_to_jsonl(stock_id=args.stock_id)



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

