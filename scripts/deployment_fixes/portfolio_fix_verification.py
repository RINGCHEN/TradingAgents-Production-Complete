#!/usr/bin/env python3
"""
投資組合修復驗證腳本
專門測試前端是否還會收到 HTML 響應的問題
"""

import requests
import json
from datetime import datetime
import time

def verify_portfolio_fix():
    """驗證投資組合修復是否成功"""
    
    print("🎯 投資組合修復驗證測試")
    print(f"⏰ 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # 測試配置
    FRONTEND_URL = "https://tradingagents-main.web.app"
    API_BASE_URL = "https://tradingagents-main-351731559902.asia-east1.run.app"
    
    test_results = {
        "frontend_serving_html": False,
        "backend_serving_json": False,
        "problem_identified": False,
        "fix_status": "UNKNOWN"
    }
    
    print("1️⃣ 測試前端 API 路徑是否仍然返回 HTML...")
    
    # 測試前端的 /api/portfolios 路徑（這是問題的根源）
    try:
        response = requests.get(f"{FRONTEND_URL}/api/portfolios", timeout=10)
        
        content_type = response.headers.get('content-type', '')
        response_text = response.text[:200].replace('\n', ' ').strip()
        
        print(f"   📡 GET {FRONTEND_URL}/api/portfolios")
        print(f"   📊 狀態碼: {response.status_code}")
        print(f"   📄 Content-Type: {content_type}")
        print(f"   📝 響應預覽: {response_text}...")
        
        if response.status_code == 200 and 'text/html' in content_type:
            test_results["frontend_serving_html"] = True
            print("   🚨 確認：前端仍在為 /api/ 路徑提供 HTML 頁面")
        else:
            print("   ✅ 前端 /api/ 路徑行為已改變")
            
    except Exception as e:
        print(f"   ❌ 前端測試錯誤: {str(e)}")
    
    print("\n2️⃣ 測試後端 API 是否正確返回 JSON...")
    
    # 測試後端 API
    try:
        headers = {
            'Origin': FRONTEND_URL,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(f"{API_BASE_URL}/api/portfolios", headers=headers, timeout=10)
        
        content_type = response.headers.get('content-type', '')
        
        print(f"   📡 GET {API_BASE_URL}/api/portfolios")
        print(f"   📊 狀態碼: {response.status_code}")
        print(f"   📄 Content-Type: {content_type}")
        
        # 檢查是否是 JSON 響應
        is_json = 'application/json' in content_type
        
        if is_json:
            try:
                json_data = response.json()
                test_results["backend_serving_json"] = True
                print("   ✅ 後端正確返回 JSON 格式")
                
                # 檢查是否是身份驗證錯誤（這是預期的）
                if "身份驗證失敗" in str(json_data) or "Authentication" in str(json_data):
                    print("   ✅ 身份驗證保護正常工作")
                    
            except json.JSONDecodeError:
                print("   ⚠️  後端返回 JSON Content-Type 但內容無法解析")
        else:
            print(f"   ❌ 後端返回非 JSON 格式: {content_type}")
            
    except Exception as e:
        print(f"   ❌ 後端測試錯誤: {str(e)}")
    
    print("\n3️⃣ 分析問題與修復狀態...")
    
    # 分析結果
    if test_results["frontend_serving_html"] and test_results["backend_serving_json"]:
        test_results["problem_identified"] = True
        test_results["fix_status"] = "FRONTEND_ROUTING_ISSUE"
        
        print("   🔍 問題分析：")
        print("   ✅ 後端 API 工作正常，返回正確的 JSON")
        print("   🚨 前端仍然為 /api/ 路徑提供 HTML 頁面")
        print("   🎯 結論：globalFetch 修復可能沒有生效，或瀏覽器仍在使用緩存")
        
        print("\n   💡 推薦解決方案：")
        print("   1. 檢查瀏覽器緩存並強制刷新頁面")
        print("   2. 驗證 globalFetch.ts 是否正確載入")
        print("   3. 檢查前端構建是否包含最新代碼")
        
    elif test_results["backend_serving_json"] and not test_results["frontend_serving_html"]:
        test_results["fix_status"] = "POSSIBLY_FIXED"
        
        print("   🎉 可能已修復：")
        print("   ✅ 後端 API 工作正常")
        print("   ✅ 前端 /api/ 路徑行為已改變")
        print("   🔧 globalFetch 修復可能已生效")
        
    elif not test_results["backend_serving_json"]:
        test_results["fix_status"] = "BACKEND_ISSUE"
        
        print("   🚨 後端問題：")
        print("   ❌ 後端 API 沒有返回正確的 JSON")
        print("   🔧 需要檢查後端服務狀態")
        
    else:
        test_results["fix_status"] = "UNKNOWN_STATE"
        print("   ❓ 無法確定當前狀態，需要進一步診斷")
    
    print("\n4️⃣ 用戶體驗測試建議...")
    
    print("   📱 建議用戶執行以下測試：")
    print("   1. 清除瀏覽器緩存並硬刷新頁面 (Ctrl+F5)")
    print("   2. 打開瀏覽器開發者工具查看控制台")
    print("   3. 訪問投資組合頁面並嘗試創建投資組合")
    print("   4. 查看是否還有 'Unexpected token' 錯誤")
    print("   5. 查看是否有 '🔧 Global fetch' 日誌消息")
    
    print("\n" + "="*60)
    print("📊 測試結果摘要")
    print("="*60)
    
    for key, value in test_results.items():
        status = "✅" if value else "❌"
        if isinstance(value, str):
            print(f"{key}: {value}")
        else:
            print(f"{status} {key.replace('_', ' ').title()}: {value}")
    
    return test_results

if __name__ == "__main__":
    try:
        results = verify_portfolio_fix()
        
        print(f"\n🏁 最終狀態: {results['fix_status']}")
        
        if results['fix_status'] == "POSSIBLY_FIXED":
            print("🎉 投資組合功能很可能已經修復！")
            print("請用戶清除瀏覽器緩存後再次測試。")
        elif results['fix_status'] == "FRONTEND_ROUTING_ISSUE":
            print("⚠️ 還需要額外的前端修復工作。")
        else:
            print("🔧 需要進一步診斷和修復。")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {str(e)}")