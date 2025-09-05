#!/usr/bin/env python3
"""
網站架構驗證腳本 - 防止配置錯誤
根據 steering 文件驗證網站配置是否正確

使用方法:
python scripts/validate_website_architecture.py
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

class WebsiteArchitectureValidator:
    def __init__(self):
        """初始化驗證器，讀取 steering 文件中的正確配置"""
        self.correct_config = {
            "main_site": {
                "domain": "https://03king.com",
                "firebase_url": "https://03king.web.app", 
                "expected_title": "不老傳說 - AI 智能投資分析平台",
                "expected_description": "智能投資分析平台",
                "purpose": "主站 - 一般用戶使用",
                "entry_point": "main.tsx"
            },
            "admin_site": {
                "domain": "https://admin.03king.com",
                "firebase_url": "https://twstock-admin-466914.web.app",
                "expected_title": "不老傳說 - 企業管理後台", 
                "expected_description": "企業級管理後台",
                "purpose": "管理後台 - 管理員使用",
                "entry_point": "index-admin.tsx"
            }
        }
        
        self.results = []
        
    def validate_site_content(self, site_key: str) -> Dict:
        """驗證網站內容是否符合預期"""
        config = self.correct_config[site_key]
        domain = config["domain"]
        
        print(f"🔍 驗證 {site_key}: {domain}")
        
        try:
            response = requests.get(domain, timeout=10)
            content = response.text.lower()
            
            # 檢查標題
            title_match = config["expected_title"].lower() in content
            desc_match = config["expected_description"].lower() in content
            
            # 檢查是否包含錯誤內容
            if site_key == "main_site":
                has_admin_content = "管理後台" in content or "企業管理" in content
                wrong_content = has_admin_content
                wrong_content_type = "包含管理後台內容" if has_admin_content else None
            else:
                has_main_content = "智能投資分析" in content and "企業管理" not in content
                wrong_content = has_main_content
                wrong_content_type = "包含主站內容" if has_main_content else None
            
            result = {
                "site": site_key,
                "domain": domain,
                "status": "✅ 正確" if title_match and not wrong_content else "❌ 錯誤",
                "title_match": title_match,
                "desc_match": desc_match,
                "wrong_content": wrong_content,
                "wrong_content_type": wrong_content_type,
                "expected_title": config["expected_title"],
                "expected_purpose": config["purpose"]
            }
            
        except Exception as e:
            result = {
                "site": site_key,
                "domain": domain, 
                "status": "💥 連接失敗",
                "error": str(e),
                "title_match": False,
                "desc_match": False,
                "wrong_content": True,
                "wrong_content_type": f"連接錯誤: {e}"
            }
            
        return result
    
    def validate_google_auth_config(self) -> Dict:
        """驗證 Google 認證配置"""
        print("🔍 驗證 Google 認證配置...")
        
        # 檢查前端配置文件
        config_files_to_check = [
            "TradingAgents/frontend/firebase.json",
            "TradingAgents/frontend/src/services/GoogleAuthService.ts",
            "TradingAgents/frontend/index.html"
        ]
        
        results = []
        for file_path in config_files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 檢查關鍵配置
                has_client_id = "351731559902-11g45sv5947cr3q89lhkar272kfeiput.apps.googleusercontent.com" in content
                has_google_domains = "accounts.google.com" in content and "gsi.google.com" in content
                has_script_src_elem = "script-src-elem" in content if file_path.endswith("firebase.json") else True
                
                results.append({
                    "file": file_path,
                    "has_client_id": has_client_id,
                    "has_google_domains": has_google_domains, 
                    "has_script_src_elem": has_script_src_elem,
                    "status": "✅" if has_client_id and has_google_domains and has_script_src_elem else "❌"
                })
                
            except Exception as e:
                results.append({
                    "file": file_path,
                    "error": str(e),
                    "status": "💥"
                })
        
        return {"google_auth_files": results}
    
    def check_firebase_targets(self) -> Dict:
        """檢查 Firebase 目標配置"""
        print("🔍 檢查 Firebase 目標配置...")
        
        try:
            with open("TradingAgents/frontend/.firebaserc", 'r', encoding='utf-8') as f:
                firebaserc = json.load(f)
            
            # 檢查專案配置
            projects = firebaserc.get("projects", {})
            targets = firebaserc.get("targets", {})
            
            correct_setup = (
                "tradingagents-main" in projects.values() and
                "twstock-admin-466914" in str(targets) and
                "03king" in str(targets)
            )
            
            return {
                "firebase_config": {
                    "projects": projects,
                    "has_correct_targets": correct_setup,
                    "status": "✅" if correct_setup else "❌"
                }
            }
        except Exception as e:
            return {
                "firebase_config": {
                    "error": str(e),
                    "status": "💥"
                }
            }
    
    def generate_fix_recommendations(self) -> List[str]:
        """根據驗證結果生成修復建議"""
        recommendations = []
        
        for result in self.results:
            if result["status"].startswith("❌"):
                if result["site"] == "main_site" and result.get("wrong_content"):
                    recommendations.append(
                        f"🔧 修復主站 ({result['domain']}):\n"
                        f"   - 當前錯誤: {result.get('wrong_content_type', '未知錯誤')}\n"
                        f"   - 應顯示: {result['expected_purpose']}\n"
                        f"   - 檢查 index.html 入口點是否為 main.tsx"
                    )
                elif result["site"] == "admin_site" and result.get("wrong_content"):
                    recommendations.append(
                        f"🔧 修復管理後台 ({result['domain']}):\n"
                        f"   - 當前錯誤: {result.get('wrong_content_type', '未知錯誤')}\n" 
                        f"   - 應顯示: {result['expected_purpose']}\n"
                        f"   - 檢查 index.html 入口點是否為 index-admin.tsx"
                    )
        
        return recommendations
    
    def run_validation(self) -> bool:
        """執行完整驗證"""
        print("=" * 60)
        print("🛡️  網站架構驗證開始")
        print("=" * 60)
        print(f"⏰ 驗證時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 驗證主站和管理後台
        for site_key in self.correct_config.keys():
            result = self.validate_site_content(site_key)
            self.results.append(result)
        
        # 驗證 Google 認證配置
        google_result = self.validate_google_auth_config()
        self.results.append(google_result)
        
        # 檢查 Firebase 配置  
        firebase_result = self.check_firebase_targets()
        self.results.append(firebase_result)
        
        # 輸出結果
        print("\n" + "=" * 60)
        print("📊 驗證結果")
        print("=" * 60)
        
        all_correct = True
        
        for result in self.results:
            if "site" in result:
                print(f"\n🌐 {result['site'].upper()}")
                print(f"   域名: {result['domain']}")
                print(f"   狀態: {result['status']}")
                print(f"   預期用途: {result.get('expected_purpose', 'N/A')}")
                
                if result['status'].startswith("❌"):
                    all_correct = False
                    print(f"   ❗ 問題: {result.get('wrong_content_type', '配置錯誤')}")
                    
            elif "google_auth_files" in result:
                print(f"\n🔐 GOOGLE 認證配置")
                for file_result in result["google_auth_files"]:
                    print(f"   {file_result['status']} {file_result['file']}")
                    if file_result['status'] == "❌":
                        all_correct = False
                        
            elif "firebase_config" in result:
                print(f"\n🔥 FIREBASE 配置")
                config = result["firebase_config"]
                print(f"   狀態: {config['status']}")
                if config['status'] == "❌":
                    all_correct = False
        
        # 生成修復建議
        if not all_correct:
            recommendations = self.generate_fix_recommendations()
            print("\n" + "=" * 60) 
            print("🔧 修復建議")
            print("=" * 60)
            for i, rec in enumerate(recommendations, 1):
                print(f"\n{i}. {rec}")
        
        print(f"\n" + "=" * 60)
        print(f"✅ 總體狀態: {'全部正確' if all_correct else '發現錯誤，需要修復'}")
        print("=" * 60)
        
        return all_correct

def main():
    """主函數"""
    validator = WebsiteArchitectureValidator()
    is_valid = validator.run_validation()
    
    # 返回適當的退出代碼
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()