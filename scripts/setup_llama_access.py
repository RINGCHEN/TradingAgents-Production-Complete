#!/usr/bin/env python3
"""
LLaMA 模型訪問配置腳本
設置 HuggingFace Token 和驗證 LLaMA 模型訪問權限
"""

import os
import sys
from pathlib import Path
from huggingface_hub import login, whoami, model_info
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def setup_hf_token():
    """設置 HuggingFace Token"""
    print("Setting up HuggingFace Token...")
    
    # 檢查是否已經登錄
    try:
        user_info = whoami()
        print(f"Already logged in as: {user_info['name']}")
        return True
    except Exception as e:
        print(f"Not logged in or invalid token: {e}")
        
        # 提示用戶輸入Token
        print("\n請按照以下步驟獲取並設置 HuggingFace Token:")
        print("1. 訪問 https://huggingface.co/settings/tokens")
        print("2. 創建新的 Token (至少需要 'Read' 權限)")
        print("3. 複製 Token")
        print("4. 在下方輸入 Token\n")
        
        token = input("請輸入您的 HuggingFace Token: ").strip()
        
        if not token:
            print("❌ Token 不能為空")
            return False
            
        try:
            login(token=token, add_to_git_credential=True)
            print("✅ Token 設置成功")
            return True
        except Exception as e:
            print(f"❌ Token 設置失敗: {e}")
            return False

def verify_llama_access():
    """驗證 LLaMA 模型訪問權限"""
    print("\n🔍 驗證 LLaMA 模型訪問權限...")
    
    llama_models = [
        "meta-llama/Llama-3.2-1B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct",
        "meta-llama/Llama-3.2-7B-Instruct"
    ]
    
    accessible_models = []
    
    for model_name in llama_models:
        try:
            print(f"  檢查模型: {model_name}")
            model_info_result = model_info(model_name)
            print(f"  ✅ {model_name} - 訪問權限確認")
            accessible_models.append(model_name)
        except Exception as e:
            print(f"  ❌ {model_name} - 無法訪問: {e}")
    
    return accessible_models

def test_llama_loading():
    """測試 LLaMA 模型載入"""
    print("\n🧪 測試 LLaMA 模型載入...")
    
    # 先測試最小的模型
    model_name = "meta-llama/Llama-3.2-1B-Instruct"
    
    try:
        print(f"  載入 Tokenizer: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("  ✅ Tokenizer 載入成功")
        
        print(f"  檢查 GPU 可用性...")
        if torch.cuda.is_available():
            print(f"  ✅ GPU 可用: {torch.cuda.get_device_name(0)}")
            print(f"  💾 GPU 記憶體: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f}GB")
        else:
            print("  ⚠️  GPU 不可用，將使用 CPU")
        
        # 測試快速載入 (不載入完整模型以節省時間)
        print(f"  測試模型配置載入...")
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained(model_name)
        print(f"  ✅ 模型配置載入成功")
        print(f"     - 隱藏層大小: {config.hidden_size}")
        print(f"     - 注意力頭數: {config.num_attention_heads}")
        print(f"     - 層數: {config.num_hidden_layers}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 模型測試失敗: {e}")
        return False

def update_system_config(accessible_models):
    """更新系統配置以支援 LLaMA 模型"""
    print("\n📝 更新系統配置...")
    
    # 更新自動化訓練配置
    config_file = "config/training_automation.yaml"
    
    try:
        import yaml
        
        # 讀取現有配置
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            config = {}
        
        # 添加 LLaMA 模型到默認模型列表
        if 'default_models' not in config:
            config['default_models'] = []
        
        # 添加可訪問的 LLaMA 模型
        for model in accessible_models:
            if model not in config['default_models']:
                config['default_models'].append(model)
        
        # 添加 LLaMA 特定配置
        config['llama_models'] = {
            "meta-llama/Llama-3.2-1B-Instruct": {
                "max_memory": "6GB",
                "recommended_batch_size": 4,
                "lora_r": 16,
                "lora_alpha": 32,
                "context_length": 4096,
                "priority": "high"
            },
            "meta-llama/Llama-3.2-3B-Instruct": {
                "max_memory": "8GB", 
                "recommended_batch_size": 2,
                "lora_r": 8,
                "lora_alpha": 16,
                "context_length": 4096,
                "priority": "medium"
            },
            "meta-llama/Llama-3.2-7B-Instruct": {
                "max_memory": "12GB",
                "recommended_batch_size": 1,
                "lora_r": 4,
                "lora_alpha": 8, 
                "context_length": 4096,
                "priority": "high"
            }
        }
        
        # 保存更新的配置
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"  ✅ 配置更新完成: {config_file}")
        print(f"     - 新增 {len(accessible_models)} 個 LLaMA 模型")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 配置更新失敗: {e}")
        return False

def create_llama_training_dataset():
    """創建 LLaMA 專用的訓練數據集"""
    print("\n📊 創建 LLaMA 訓練數據集...")
    
    # 創建更豐富的金融分析數據集
    llama_dataset = [
        {
            "instruction": "進行台積電技術面分析",
            "input": "台積電 (2330) 今日收盤價 520 元，成交量較昨日增加 25%，RSI 指標 65",
            "output": "根據技術分析，台積電目前呈現以下特徵：1) RSI 65 處於中性偏多區間，顯示股價上漲動能仍存但需注意過熱風險；2) 成交量放大 25% 顯示市場關注度提升，若能配合價格突破將形成強勢訊號；3) 建議關注 530 元阻力位，突破後有望挑戰 550 元；4) 止損設在 500 元支撐位。"
        },
        {
            "instruction": "評估鴻海基本面投資價值",
            "input": "鴻海 (2317) Q3 營收 1.8 兆新台幣，年增 20%，毛利率提升至 7.2%，AI 伺服器訂單大增",
            "output": "鴻海基本面分析結果：**正面因素**：1) 營收年增 20% 顯示業務成長強勁；2) 毛利率提升至 7.2% 反映產品組合優化和成本控制成效；3) AI 伺服器需求爆發將成為新成長動能；4) 受惠於 AI 基礎設施建設長期趨勢。**投資建議**：目標價調升 15%，建議逢低佈局，長期持有享受 AI 轉型紅利。風險提醒：需關注中美貿易政策變化對供應鏈的影響。"
        },
        {
            "instruction": "分析聯發科競爭優勢與風險",
            "input": "聯發科 (2454) 推出天璣 9400 旗艦晶片，採用 3nm 製程，AI 性能提升 40%，與高通 Snapdragon 8 Gen 4 正面競爭",
            "output": "聯發科競爭分析：**核心優勢**：1) 天璣 9400 採用最先進 3nm 製程，功耗控制優秀；2) AI 性能大幅提升 40% 符合手機 AI 化趨勢；3) 成本控制能力強，有望在中高階市場搶占更多份額。**面臨挑戰**：1) 與高通旗艦產品直接競爭，需要在性能和價格間找到平衡；2) 蘋果自研晶片對高階市場的壓縮；3) 地緣政治風險影響全球佈局。**投資策略**：建議關注產品發布後的市場接受度，若獲得主流品牌採用將有望重新評估估值。"
        },
        {
            "instruction": "提供半導體族群投資配置建議",
            "input": "目前半導體庫存調整接近尾聲，AI 需求持續強勁，記憶體價格開始回升，客戶補庫存需求增加",
            "output": "半導體投資配置策略：**核心配置 (40%)**：台積電 - AI 晶片代工龍頭，受惠明確且持續；**成長配置 (30%)**：聯發科、創意 - AI 晶片設計與 IP 授權，彈性較大；**循環配置 (20%)**：南亞科、華邦電 - 記憶體價格回升受惠；**衛星配置 (10%)**：矽力-KY、聯詠 - 電源管理和驅動 IC，下游復甦受惠。**時機判斷**：建議分批進場，重點關注 Q4 財報和 2025 年資本支出指引。風險控管：設定停損點位，關注美國對中政策變化。"
        },
        {
            "instruction": "分析金融股升息影響評估",
            "input": "央行升息 1 碼至 2.0%，銀行淨利差可望改善，但房貸需求可能受影響，信用風險需要關注",
            "output": "金融股升息影響評估：**正面效應**：1) 淨利差改善：升息直接有利銀行獲利，預估大型金控 NIM 可提升 5-10 bp；2) 資產品質：高利率環境有助篩選優質借款人；3) 投資收益：債券投資部位重訂價受惠。**負面風險**：1) 信貸需求下降：房貸、企業放款成長可能趨緩；2) 信用成本上升：經濟放緩時違約率可能提高；3) 估值壓制：金融股 P/B 在升息環境下通常承壓。**投資建議**：優選資本適足率高、資產品質佳的大型金控，如富邦金、國泰金，建議權重 15-20%。"
        },
        {
            "instruction": "預測台股未來 6 個月走勢",
            "input": "台股加權指數目前 17,800 點，外資持續賣超，但內資買盤支撐，美股那斯達克創新高，台積電 ADR 表現強勢",
            "output": "台股 6 個月展望分析：**技術面**：17,800 點為重要支撐區，需守住確保中期趨勢；上檔 18,500-19,000 為壓力區。**資金面**：外資賣壓主因匯率和中美關係，內資動能來自保險資金和退休基金；預期 Q4 資金面將趨於平衡。**基本面**：AI 概念股業績支撐指數，但傳統產業復甦仍需時間；關注台積電法說會和蘋果新品銷售。**預測區間**：樂觀情境 19,500 點（AI 超預期+資金回流），基準情境 18,200-18,800 點（震盪整理），悲觀情境 17,000 點（地緣風險+經濟衰退）。**操作策略**：建議維持 6-7 成倉位，重點布局 AI、綠能、軍工等題材。"
        }
    ]
    
    # 保存數據集
    dataset_dir = "data/datasets/llama_financial"
    os.makedirs(dataset_dir, exist_ok=True)
    
    import json
    dataset_file = f"{dataset_dir}/training_data.jsonl"
    
    with open(dataset_file, 'w', encoding='utf-8') as f:
        for item in llama_dataset:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print(f"  ✅ LLaMA 訓練數據集創建完成")
    print(f"     - 文件路徑: {dataset_file}")
    print(f"     - 樣本數量: {len(llama_dataset)}")
    
    return dataset_file

def main():
    """主函數"""
    print("LLaMA model access configuration starting...")
    print("=" * 50)
    
    # Step 1: 設置 HuggingFace Token
    if not setup_hf_token():
        print("❌ Token 設置失敗，請重新運行腳本")
        return False
    
    # Step 2: 驗證模型訪問權限
    accessible_models = verify_llama_access()
    if not accessible_models:
        print("❌ 無法訪問任何 LLaMA 模型，請檢查權限申請狀態")
        return False
    
    print(f"\n✅ 可訪問的模型數量: {len(accessible_models)}")
    
    # Step 3: 測試模型載入
    if not test_llama_loading():
        print("⚠️  模型載入測試失敗，但可以繼續配置")
    
    # Step 4: 更新系統配置
    if not update_system_config(accessible_models):
        print("❌ 系統配置更新失敗")
        return False
    
    # Step 5: 創建訓練數據集
    dataset_file = create_llama_training_dataset()
    
    print("\n" + "=" * 50)
    print("🎉 LLaMA 模型訪問配置完成！")
    print("\n下一步操作:")
    print("1. 運行自動化訓練測試:")
    print("   python training_automation/automated_training_pipeline.py --action create_job --model meta-llama/Llama-3.2-1B-Instruct --dataset data/datasets/llama_financial")
    print("2. 啟動性能基準測試:")
    print("   python scripts/benchmark_llama_models.py")
    print("3. 查看訓練儀表板:")
    print("   python training_automation/dashboard_app.py (訪問 http://localhost:8888)")
    
    return True


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

if __name__ == "__main__":
    main()