import json
import os
import yaml

def generate_and_save_investment_scenarios(output_filename="investment_scenarios.jsonl"):
    """
    Generates a small, synthetic dataset of investment scenarios (prompt-completion pairs)
    for the Investment Planner. Includes caching.
    """
    print("Starting investment scenario generation...")

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

    # Define output directory
    output_dir = os.path.join(storage_base, raw_subdir, 'investment_scenarios')
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl_path = os.path.join(output_dir, output_filename)

    # --- Caching Logic ---
    # Since this script generates synthetic data from code, if the file exists, it's always up-to-date.
    if os.path.exists(output_jsonl_path):
        print(f"Cache is valid. Synthetic data already exists at {output_jsonl_path}. Skipping generation.")
        return
    # --- End Caching Logic ---

    # --- Define Synthetic Scenarios ---
    scenarios = [
        {
            "market_trend": "上漲趨勢",
            "fundamentals_summary": "營收穩健增長，獲利能力強，財務結構健康。",
            "news_sentiment": "利多",
            "risk_level": "低風險",
            "investor_goal": "長期穩健增長",
            "recommendation": "買入並長期持有",
            "rationale": "公司基本面極佳，市場趨勢向上，新聞情緒積極，且風險評估為低。符合長期穩健增長目標。"
        },
        {
            "market_trend": "盤整",
            "fundamentals_summary": "營收持平，獲利能力穩定，但成長動能不足。",
            "news_sentiment": "中性",
            "risk_level": "中等風險",
            "investor_goal": "短期高報酬",
            "recommendation": "觀望，等待明確突破信號",
            "rationale": "市場處於盤整，公司成長動能不足，短期內難有爆發性表現。不符合短期高報酬目標。"
        },
        {
            "market_trend": "下跌趨勢",
            "fundamentals_summary": "營收下滑，獲利承壓，負債比率升高。",
            "news_sentiment": "利空",
            "risk_level": "高風險",
            "investor_goal": "保本",
            "recommendation": "減持或賣出，規避風險",
            "rationale": "公司基本面惡化，市場趨勢向下，新聞情緒負面，且風險評估為高。應優先保本。"
        },
        {
            "market_trend": "上漲趨勢",
            "fundamentals_summary": "營收快速增長，但獲利能力不穩定，現金流緊張。",
            "news_sentiment": "利多",
            "risk_level": "中等風險",
            "investor_goal": "長期穩健增長",
            "recommendation": "謹慎觀望，待基本面改善",
            "rationale": "儘管市場趨勢向上，但公司基本面存在不確定性，不符合穩健增長目標。"
        },
        {
            "market_trend": "盤整",
            "fundamentals_summary": "營收穩健，獲利穩定，但行業面臨政策不確定性。",
            "news_sentiment": "中性",
            "risk_level": "中等風險",
            "investor_goal": "短期高報酬",
            "recommendation": "不建議操作，風險與報酬不匹配",
            "rationale": "市場盤整，行業政策不確定性增加風險，不適合短期高報酬策略。"
        },
        {
            "market_trend": "下跌趨勢",
            "fundamentals_summary": "營收持平，但有潛在技術突破，長期前景看好。",
            "news_sentiment": "中性",
            "risk_level": "中等風險",
            "investor_goal": "長期穩健增長",
            "recommendation": "分批買入，長期佈局",
            "rationale": "市場短期下跌，但公司有長期利好因素，適合分批建倉。"
        }
    ]

    all_processed_examples = []

    for scenario in scenarios:
        prompt_text = (
            f"基於以下分析師報告和投資目標，請提供一個投資建議：\n"
            f"市場趨勢：{scenario['market_trend']}\n"
            f"基本面摘要：{scenario['fundamentals_summary']}\n"
            f"新聞情緒：{scenario['news_sentiment']}\n"
            f"風險等級：{scenario['risk_level']}\n"
            f"我的投資目標是：{scenario['investor_goal']}\n"
            f"請提供具體的投資建議和理由。"
        )
        
        completion_text = f"建議：{scenario['recommendation']}。理由：{scenario['rationale']}"

        all_processed_examples.append({"prompt": prompt_text, "completion": completion_text})

    # --- Write to JSONL file ---
    print(f"Generating and writing {len(all_processed_examples)} scenarios to {output_jsonl_path}")
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for example in all_processed_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\nSuccessfully generated {len(all_processed_examples)} investment scenarios and saved to: {output_jsonl_path}")

if __name__ == '__main__':
    generate_and_save_investment_scenarios()



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

