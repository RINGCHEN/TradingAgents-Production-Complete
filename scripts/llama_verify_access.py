#!/usr/bin/env python3
"""
LLaMA 訪問權限驗證腳本
檢查 HuggingFace token 和 LLaMA 模型訪問權限
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

def verify_llama_access():
    """驗證LLaMA訪問權限"""
    print("🔍 檢查 LLaMA 訪問權限...")
    
    # 檢查token
    hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
    if not hf_token or hf_token == "your_token_here":
        print("❌ HuggingFace token 未配置！")
        print("請在 .env 文件中設置 HUGGING_FACE_HUB_TOKEN")
        return False
    
    print(f"✅ HuggingFace token: {hf_token[:10]}...")
    
    try:
        from transformers import AutoTokenizer
        from huggingface_hub import login
        
        # 登錄
        print("🔐 登錄 HuggingFace...")
        login(token=hf_token)
        print("✅ HuggingFace 登錄成功")
        
        # 測試不同的LLaMA模型
        models_to_test = [
            "meta-llama/Llama-3.2-1B-Instruct",
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Meta-Llama-3.1-8B-Instruct"
        ]
        
        accessible_models = []
        
        for model_name in models_to_test:
            try:
                print(f"🧪 測試模型: {model_name}")
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                print(f"✅ {model_name} - 可訪問")
                accessible_models.append(model_name)
            except Exception as e:
                print(f"❌ {model_name} - 無法訪問: {str(e)[:100]}...")
        
        if accessible_models:
            print(f"\n🎉 成功！可訪問 {len(accessible_models)} 個 LLaMA 模型:")
            for model in accessible_models:
                print(f"  ✅ {model}")
            
            print(f"\n🚀 推薦使用: {accessible_models[0]} (最輕量)")
            return True
        else:
            print("\n❌ 無法訪問任何 LLaMA 模型")
            print("請確認:")
            print("1. 已在 HuggingFace 申請 LLaMA 訪問權限")
            print("2. Token 具有正確的權限")
            print("3. 網路連接正常")
            return False
            
    except ImportError as e:
        print(f"❌ 缺少必要的套件: {e}")
        print("請執行: pip install transformers huggingface_hub")
        return False
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    success = verify_llama_access()
    if success:
        print("\n✅ LLaMA 訪問權限驗證成功！")
        print("🚀 現在可以開始 AI 訓練了")
        print("執行: python start_llama_training.py")
    else:
        print("\n❌ LLaMA 訪問權限驗證失敗")
        sys.exit(1)