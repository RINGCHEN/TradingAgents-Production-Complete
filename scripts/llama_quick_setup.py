#!/usr/bin/env python3
"""
LLaMA Quick Setup - Simple configuration script
"""

import os
import sys
from huggingface_hub import login, whoami, model_info
import torch
import yaml
import json

def check_hf_login():
    """Check HuggingFace login status"""
    try:
        user_info = whoami()
        print(f"Logged in as: {user_info['name']}")
        return True
    except Exception as e:
        print("Please login to HuggingFace first:")
        print("huggingface-cli login")
        print("Or use: from huggingface_hub import login; login()")
        return False

def test_llama_access():
    """Test LLaMA model access"""
    models = [
        "meta-llama/Llama-3.2-1B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct", 
        "meta-llama/Llama-3.2-7B-Instruct"
    ]
    
    accessible = []
    for model in models:
        try:
            info = model_info(model)
            print(f"Access confirmed: {model}")
            accessible.append(model)
        except Exception as e:
            print(f"Cannot access: {model} - {e}")
    
    return accessible

def update_config(models):
    """Update training automation config"""
    config_file = "config/training_automation.yaml"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except:
        config = {'default_models': []}
    
    # Add LLaMA models
    if 'default_models' not in config:
        config['default_models'] = []
    
    for model in models:
        if model not in config['default_models']:
            config['default_models'].append(model)
    
    # Add LLaMA specific configs
    config['llama_models'] = {
        "meta-llama/Llama-3.2-1B-Instruct": {
            "max_memory": "6GB",
            "batch_size": 4,
            "lora_r": 16,
            "lora_alpha": 32
        },
        "meta-llama/Llama-3.2-3B-Instruct": {
            "max_memory": "8GB",
            "batch_size": 2, 
            "lora_r": 8,
            "lora_alpha": 16
        }
    }
    
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    print(f"Config updated: {len(models)} LLaMA models added")

def create_dataset():
    """Create LLaMA training dataset"""
    os.makedirs("data/datasets/llama_financial", exist_ok=True)
    
    data = [
        {
            "instruction": "Analyze TSMC stock performance",
            "input": "TSMC stock price increased 2% today with high volume",
            "output": "TSMC shows strong bullish momentum with increased volume confirming the upward trend. Technical indicators suggest continued strength."
        },
        {
            "instruction": "Evaluate MediaTek investment potential", 
            "input": "MediaTek launches new AI chip with 40% performance improvement",
            "output": "MediaTek's new AI chip represents significant technological advancement, potentially improving market share and margins in premium segment."
        },
        {
            "instruction": "Assess semiconductor sector outlook",
            "input": "AI demand remains strong while inventory correction nears end",
            "output": "Semiconductor sector shows recovery signs with AI demand offsetting traditional weakness. Recommend selective positioning in AI-focused names."
        }
    ]
    
    with open("data/datasets/llama_financial/training_data.jsonl", 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    print("LLaMA training dataset created")

def main():
    print("LLaMA Quick Setup Starting...")
    print("=" * 40)
    
    # Check HF login
    if not check_hf_login():
        return False
    
    # Test model access
    models = test_llama_access()
    if not models:
        print("No LLaMA models accessible")
        return False
    
    print(f"Accessible models: {len(models)}")
    
    # Update config
    update_config(models)
    
    # Create dataset
    create_dataset()
    
    print("=" * 40)
    print("LLaMA setup completed successfully!")
    print(f"GPU Available: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory/1024**3:.1f}GB")
    
    print("\nNext steps:")
    print("1. Test training: python training_automation/automated_training_pipeline.py")  
    print("2. Run benchmark: python scripts/benchmark_llama.py")
    
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