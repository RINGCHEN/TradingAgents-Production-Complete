import yfinance as yf
import pandas as pd
import yaml
import os

def fetch_stock_data(stock_symbol, config_path="configs/data_sources.yaml"):
    """
    Fetches historical stock data using yfinance based on the provided config
    and saves it to a dynamically configured directory.
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
    base_path = storage_config.get('base_path', 'data') # Default to 'data' if not set
    raw_subdir = storage_config.get('raw_subdir', 'raw')
    
    # Construct dynamic output directory path
    output_dir = os.path.join(base_path, raw_subdir, 'stock_data')

    source_config = config.get('stock_data_source', {})
    params = source_config.get('params', {'period': '5y', 'interval': '1d'}) # Add defaults

    print(f"Fetching data for {stock_symbol} with params: {params}")
    print(f"Data will be saved to: {output_dir}")

    try:
        # Fetch data
        stock = yf.Ticker(stock_symbol)
        hist_data = stock.history(**params)

        if hist_data.empty:
            print(f"No data found for symbol {stock_symbol}. It might be delisted or an incorrect symbol.")
            return

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save data
        output_path = os.path.join(output_dir, f"{stock_symbol}.csv")
        hist_data.to_csv(output_path)

        print(f"Successfully saved data to {output_path}")

    except Exception as e:
        print(f"An error occurred during data fetching or saving: {e}")


if __name__ == '__main__':
    # Example: Fetch data for TSMC (Taiwan Stock Market)
    # In Taiwan, stock symbols for common stocks are appended with .TW for yfinance
    tsmc_symbol = '2330.TW'
    fetch_stock_data(tsmc_symbol)



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

