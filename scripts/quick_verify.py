#!/usr/bin/env python3
"""
GPT-OSS 快速驗證腳本
用於快速檢查服務是否正常運行
"""

import requests
import json
import time
import sys
from datetime import datetime

def print_status(message, status="info"):
    """打印狀態消息"""
    colors = {
        "success": "\033[0;32m",
        "error": "\033[0;31m", 
        "warning": "\033[1;33m",
        "info": "\033[0;34m"
    }
    color = colors.get(status, "\033[0m")
    print(f"{color}{message}\033[0m")

def quick_verify(host="localhost", port=8080):
    """快速驗證GPT-OSS服務"""
    base_url = f"http://{host}:{port}"
    
    print_status("🚀 GPT-OSS 快速驗證開始", "info")
    print_status(f"📍 目標服務: {base_url}", "info")
    print_status(f"⏰ 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
    print("-" * 50)
    
    # 1. 連接測試
    print_status("1️⃣ 測試服務連接...", "info")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print_status("   ✅ 連接成功", "success")
        else:
            print_status(f"   ❌ 連接失敗: HTTP {response.status_code}", "error")
            return False
    except Exception as e:
        print_status(f"   ❌ 連接失敗: {e}", "error")
        return False
    
    # 2. 健康檢查
    print_status("2️⃣ 檢查服務健康狀態...", "info")
    try:
        health_data = response.json()
        status = health_data.get("status", "unknown")
        
        if status == "healthy":
            print_status("   ✅ 服務健康", "success")
            
            # 顯示關鍵信息
            model = health_data.get("model", "unknown")
            device = health_data.get("device", "unknown")
            cuda_available = health_data.get("cuda_available", False)
            
            print_status(f"   📊 模型: {model}", "info")
            print_status(f"   🖥️  設備: {device}", "info")
            print_status(f"   🎮 CUDA: {'可用' if cuda_available else '不可用'}", "success" if cuda_available else "warning")
            
        else:
            print_status(f"   ⚠️ 服務狀態: {status}", "warning")
            
    except Exception as e:
        print_status(f"   ❌ 健康檢查失敗: {e}", "error")
        return False
    
    # 3. 推理測試
    print_status("3️⃣ 測試推理功能...", "info")
    try:
        test_request = {
            "message": "Hello, this is a test.",
            "max_tokens": 20,
            "temperature": 0.7
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/chat", json=test_request, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            inference_time = end_time - start_time
            result = response.json()
            
            print_status("   ✅ 推理測試成功", "success")
            print_status(f"   ⏱️ 推理時間: {inference_time:.2f}秒", "info")
            print_status(f"   🔢 使用tokens: {result.get('tokens_used', 'N/A')}", "info")
            
            # 顯示部分回應
            response_text = result.get('response', '')
            if len(response_text) > 100:
                response_text = response_text[:100] + "..."
            print_status(f"   💬 回應預覽: {response_text}", "info")
            
        else:
            print_status(f"   ❌ 推理測試失敗: HTTP {response.status_code}", "error")
            return False
            
    except Exception as e:
        print_status(f"   ❌ 推理測試失敗: {e}", "error")
        return False
    
    # 4. 記憶體檢查
    print_status("4️⃣ 檢查記憶體狀態...", "info")
    try:
        response = requests.get(f"{base_url}/memory", timeout=10)
        if response.status_code == 200:
            memory_data = response.json()
            memory_status = memory_data.get("memory_status", {})
            
            if "message" in memory_status and "CUDA not available" in memory_status["message"]:
                print_status("   ⚠️ 運行在CPU模式", "warning")
            else:
                allocated = memory_status.get("allocated_gb", 0)
                reserved = memory_status.get("reserved_gb", 0)
                usage_pct = memory_status.get("usage_percentage", 0)
                
                print_status("   ✅ GPU記憶體狀態正常", "success")
                print_status(f"   📊 已分配: {allocated}GB", "info")
                print_status(f"   📊 已保留: {reserved}GB", "info")
                print_status(f"   📊 使用率: {usage_pct}%", "info")
                
                if usage_pct > 80:
                    print_status("   ⚠️ 記憶體使用率較高", "warning")
        else:
            print_status("   ⚠️ 無法獲取記憶體狀態", "warning")
            
    except Exception as e:
        print_status(f"   ⚠️ 記憶體檢查失敗: {e}", "warning")
    
    print("-" * 50)
    print_status("🎉 快速驗證完成 - 服務運行正常！", "success")
    return True

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GPT-OSS 快速驗證")
    parser.add_argument("--host", default="localhost", help="服務主機")
    parser.add_argument("--port", type=int, default=8080, help="服務端口")
    
    args = parser.parse_args()
    
    success = quick_verify(args.host, args.port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()