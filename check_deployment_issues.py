#!/usr/bin/env python3
"""
DigitalOcean 部署問題檢查腳本
檢查 TradingAgents 系統的部署狀態和潛在問題
"""

import requests
import time
from datetime import datetime

def check_digitalocean_deployment():
    """檢查 DigitalOcean 部署狀態"""
    
    print("🔍 DigitalOcean 部署狀態檢查")
    print("=" * 50)
    
    base_url = "https://twshocks-app-79rsx.ondigitalocean.app"
    
    endpoints_to_check = [
        "/",
        "/health", 
        "/docs",
        "/redoc",
        "/api/simple-portfolios/health"
    ]
    
    print(f"📋 檢查目標: {base_url}")
    print(f"⏰ 檢查時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    for endpoint in endpoints_to_check:
        url = f"{base_url}{endpoint}"
        print(f"🌐 測試: {endpoint}")
        
        try:
            response = requests.get(url, timeout=10)
            status_code = response.status_code
            
            if status_code == 200:
                print(f"   ✅ {status_code} - OK")
                try:
                    json_data = response.json()
                    if endpoint == "/" and "message" in json_data:
                        print(f"   📝 訊息: {json_data.get('message', 'N/A')}")
                        print(f"   📦 版本: {json_data.get('version', 'N/A')}")
                    elif endpoint == "/health" and "status" in json_data:
                        print(f"   🏥 健康狀態: {json_data.get('status', 'N/A')}")
                        print(f"   📊 服務: {json_data.get('services', {})}")
                except:
                    print(f"   📄 回應長度: {len(response.text)} bytes")
            else:
                print(f"   ❌ {status_code} - 失敗")
                print(f"   📄 錯誤訊息: {response.text[:100]}...")
                
            results[endpoint] = {
                'status_code': status_code,
                'success': status_code == 200,
                'response_length': len(response.text)
            }
            
        except requests.exceptions.Timeout:
            print(f"   ⏰ 超時 - 請求超過10秒")
            results[endpoint] = {'status_code': 'TIMEOUT', 'success': False}
            
        except requests.exceptions.ConnectionError:
            print(f"   🚫 連接錯誤 - 無法連接到伺服器")
            results[endpoint] = {'status_code': 'CONNECTION_ERROR', 'success': False}
            
        except Exception as e:
            print(f"   💥 異常: {str(e)}")
            results[endpoint] = {'status_code': 'ERROR', 'success': False, 'error': str(e)}
        
        print()
        time.sleep(1)  # 避免過度請求
    
    # 摘要報告
    print("📊 檢查摘要")
    print("=" * 30)
    
    successful_endpoints = sum(1 for r in results.values() if r['success'])
    total_endpoints = len(results)
    
    print(f"✅ 成功端點: {successful_endpoints}/{total_endpoints}")
    print(f"❌ 失敗端點: {total_endpoints - successful_endpoints}/{total_endpoints}")
    
    if successful_endpoints == 0:
        print()
        print("🚨 嚴重問題：所有端點都無法訪問")
        print("   可能原因:")
        print("   1. FastAPI 應用未正常啟動")
        print("   2. 環境變數配置錯誤（特別是 DATABASE_URL）")
        print("   3. 依賴項安裝失敗")
        print("   4. DigitalOcean 部署失敗")
        print()
        print("🔧 建議解決步驟:")
        print("   1. 更新 DigitalOcean 環境變數（DATABASE_URL 最優先）")
        print("   2. 檢查 DigitalOcean App 建構日誌")
        print("   3. 確認 Python 依賴項完整安裝")
        print("   4. 重新部署應用")
        
    elif successful_endpoints == total_endpoints:
        print()
        print("🎉 所有端點正常運行！")
        print("   ✅ TradingAgents 系統部署成功")
        
    else:
        print()
        print("⚠️  部分端點有問題")
        print("   📋 需要進一步檢查失敗的端點")
    
    return results

def main():
    """主函數"""
    print("🚀 TradingAgents DigitalOcean 部署檢查工具")
    print("天工 (TianGong) - 2025-09-06")
    print()
    
    results = check_digitalocean_deployment()
    
    print()
    print("🔗 相關連結:")
    print("   📚 API文檔: https://twshocks-app-79rsx.ondigitalocean.app/docs")
    print("   🏥 健康檢查: https://twshocks-app-79rsx.ondigitalocean.app/health")
    print("   🏠 主頁: https://twshocks-app-79rsx.ondigitalocean.app/")
    print()
    print("📧 如需支援，請檢查 PRODUCTION_ENV_FINAL.md 的環境變數配置")

if __name__ == "__main__":
    main()