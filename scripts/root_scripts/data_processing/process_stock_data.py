import pandas as pd
import os
import json
import yaml

def process_stock_data(stock_symbol, config_path="configs/data_sources.yaml"):
    """
    Reads a raw stock data CSV, transforms it into a prompt-completion format,
    and saves it as a JSONL file. Includes caching.
    """
    # Load configuration
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        return
    except Exception as e:
        print(f"Error reading or parsing YAML file: {e}")
        return

    # Get storage paths from config
    storage_config = config.get('storage', {})
    
    storage_base = os.environ.get('TRADING_AGENTS_DATA_DIR')
    if not storage_base:
        print("Warning: TRADING_AGENTS_DATA_DIR environment variable not set.")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        storage_base = os.path.join(project_root, 'ai_training_data')
        print(f"Falling back to default path: {storage_base}")

    raw_subdir = storage_config.get('raw_subdir', 'raw')
    processed_subdir = storage_config.get('processed_subdir', 'processed')

    # Construct dynamic input and output paths
    input_dir = os.path.join(storage_base, raw_subdir, 'stock_data')
    input_csv_path = os.path.join(input_dir, f"{stock_symbol}.csv")
    
    output_dir = os.path.join(storage_base, processed_subdir)
    output_filename = f"{stock_symbol}_processed.jsonl"
    output_path = os.path.join(output_dir, output_filename)

    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # --- Caching Logic ---
    if os.path.exists(output_path) and os.path.exists(input_csv_path):
        if os.path.getmtime(output_path) >= os.path.getmtime(input_csv_path):
            print(f"Cache is valid for {stock_symbol}. Skipping processing. Processed data at {output_path}")
            return
        else:
            print(f"Cache invalidated for {stock_symbol} by updated input file.")
    # --- End Caching Logic ---

    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_csv_path}")
        print("Please ensure you have run the data fetching script first.")
        return

    print(f"Processing data from {input_csv_path}...")

    with open(output_path, 'w', encoding='utf-8') as f:
        for index, row in df.iterrows():
            # Format the date to be more readable
            try:
                date_str = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
            except Exception:
                continue

            # Create the prompt
            prompt = (
                f"On {date_str}, stock {stock_symbol} had an opening price of {row['Open']:.2f}, "
                f"a high of {row['High']:.2f}, a low of {row['Low']:.2f}, and a closing price of "
                f"{row['Close']:.2f}, with a total volume of {int(row['Volume'])}."
            )

            # Create a more detailed, rule-based completion for better training data
            price_change = row['Close'] - row['Open']
            daily_range = row['High'] - row['Low']
            
            if price_change > 0.01:
                momentum = "positive"
                change_desc = f"a gain of {price_change:.2f} points"
            elif price_change < -0.01:
                momentum = "negative"
                change_desc = f"a loss of {abs(price_change):.2f} points"
            else:
                momentum = "neutral"
                change_desc = "no significant change"

            completion = (
                f"On this day, the stock showed {momentum} momentum, closing at {row['Close']:.2f}, "
                f"which was {change_desc} from the open. The daily trading range was {daily_range:.2f} points, "
                f"between a high of {row['High']:.2f} and a low of {row['Low']:.2f}."
            )

            # Write as a JSON line
            json_line = json.dumps({"prompt": prompt, "completion": completion}, ensure_ascii=False)
            f.write(json_line + '\n')

    print(f"Successfully processed data and saved to {output_path}")

if __name__ == '__main__':
    # Example: Process data for TSMC
    # Allow running with an argument for flexibility
    import argparse
    parser = argparse.ArgumentParser(description="Process raw stock data into JSONL format.")
    parser.add_argument("--symbol", type=str, default="2330.TW", help="Stock symbol to process (e.g., 2330.TW)")
    args = parser.parse_args()
    
    process_stock_data(args.symbol)



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

