import json
import os
import yaml

def process_ptt_posts_to_jsonl(output_filename="ptt_posts_processed.jsonl"):
    """
    Reads raw PTT posts from JSONL, generates prompt-completion pairs,
    and saves them to a new JSONL file for social media analysis training.
    Includes caching.
    """
    print("Starting PTT post processing...")

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
    input_dir = os.path.join(storage_base, raw_subdir, 'social_media_posts')
    input_jsonl_path = os.path.join(input_dir, 'ptt_posts.jsonl')
    
    output_dir = os.path.join(storage_base, processed_subdir)
    os.makedirs(output_dir, exist_ok=True)
    output_jsonl_path = os.path.join(output_dir, output_filename)

    # --- Caching Logic ---
    if os.path.exists(output_jsonl_path) and os.path.exists(input_jsonl_path):
        if os.path.getmtime(output_jsonl_path) >= os.path.getmtime(input_jsonl_path):
            print(f"Cache is valid. Skipping processing. Processed data already exists at {output_jsonl_path}")
            return
        else:
            print("Cache invalidated by updated input file.")
    # --- End Caching Logic ---

    # --- Define Keywords for Rule-based Sentiment/Impact Analysis ---
    positive_keywords = ["漲", "多", "買", "賺", "利多", "看好", "樂觀", "買超", "勁揚", "飆漲", "受惠", "推"]
    negative_keywords = ["跌", "空", "賣", "虧", "利空", "看壞", "悲觀", "賣超", "重挫", "崩跌", "衝擊", "噓"]
    neutral_keywords = ["中性", "觀望", "盤整", "整理"]

    all_processed_examples = []

    try:
        print(f"Reading raw PTT data from {input_jsonl_path}")
        with open(input_jsonl_path, 'r', encoding='utf-8') as f_in:
            for line in f_in:
                try:
                    post_item = json.loads(line)
                    title = post_item.get('title', '')
                    content = post_item.get('content', '')
                    comments_list = post_item.get('comments', [])

                    # Combine content and comments for analysis
                    full_text = title + "\n" + content + "\n" + " ".join([c.get('content', '') for c in comments_list])

                    # --- Create Prompt ---
                    # Limit full_text length for prompt to avoid excessively long inputs
                    prompt_full_text = full_text[:1000] + "..." if len(full_text) > 1000 else full_text
                    prompt_text = f"請根據以下PTT文章內容，判斷其對股市的影響是利多、利空還是中性，並簡要說明原因：\n標題：{title}\n內容：{prompt_full_text}"

                    # --- Create Completion (Rule-based Sentiment) ---
                    sentiment = "中性"
                    pos_count = sum(1 for kw in positive_keywords if kw in full_text)
                    neg_count = sum(1 for kw in negative_keywords if kw in full_text)
                    neu_count = sum(1 for kw in neutral_keywords if kw in full_text)

                    if pos_count > neg_count and pos_count > neu_count:
                        sentiment = "利多"
                        reason = "文章內容和推文中包含較多正面詞彙，暗示對股市有積極影響。"
                    elif neg_count > pos_count and neg_count > neu_count:
                        sentiment = "利空"
                        reason = "文章內容和推文中包含較多負面詞彙，暗示對股市有消極影響。"
                    else:
                        reason = "文章內容和推文中正面、負面或中性詞彙數量相近，或無明顯傾向，判斷為中性影響。"
                    
                    completion_text = f"判斷結果：{sentiment}。原因：{reason}"

                    all_processed_examples.append({"prompt": prompt_text, "completion": completion_text})

                except json.JSONDecodeError as e:
                    print(f"Warning: Skipping malformed JSONL line in input: {line.strip()} - {e}")
                    continue
                except Exception as e:
                    print(f"Warning: Error processing PTT post: {e}. Skipping.")
                    continue

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_jsonl_path}. Please run the PTT post scraper first.")
        return
    except Exception as e:
        print(f"An error occurred reading input file: {e}")
        return

    # --- Write to JSONL file ---
    print(f"Writing {len(all_processed_examples)} processed examples to {output_jsonl_path}")
    with open(output_jsonl_path, 'w', encoding='utf-8') as f:
        for example in all_processed_examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')

    print(f"\nSuccessfully processed {len(all_processed_examples)} PTT posts and saved to: {output_jsonl_path}")

if __name__ == '__main__':
    process_ptt_posts_to_jsonl()



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

