#!/usr/bin/env python3
"""
Google 認證配置清理腳本
清除重複和錯誤的配置，保留正確的設定

使用方法:
python scripts/cleanup_google_auth.py --dry-run  # 預覽將要做的更改
python scripts/cleanup_google_auth.py           # 執行清理
"""

import os
import json
import argparse
import shutil
from datetime import datetime
from pathlib import Path

class GoogleAuthCleaner:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.changes_made = []
        
        # 正確的 Google 認證配置
        self.correct_config = {
            "client_id": "351731559902-11g45sv5947cr3q89lhkar272kfeiput.apps.googleusercontent.com",
            "google_domains": [
                "https://accounts.google.com",
                "https://gsi.google.com", 
                "https://apis.google.com",
                "https://www.googleapis.com",
                "https://oauth2.googleapis.com",
                "https://lh3.googleusercontent.com"
            ],
            "csp_directives": {
                "script-src": "https://accounts.google.com https://gsi.google.com https://apis.google.com https://www.googleapis.com",
                "script-src-elem": "https://accounts.google.com https://gsi.google.com https://apis.google.com https://www.googleapis.com",
                "frame-src": "https://accounts.google.com https://gsi.google.com",
                "connect-src": "https://oauth2.googleapis.com https://accounts.google.com https://gsi.google.com",
                "img-src": "https://lh3.googleusercontent.com"
            }
        }
        
    def backup_file(self, file_path: str) -> str:
        """備份文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{file_path}.backup_{timestamp}"
        
        if not self.dry_run:
            shutil.copy2(file_path, backup_path)
            
        self.changes_made.append(f"✅ 備份: {file_path} -> {backup_path}")
        return backup_path
    
    def clean_firebase_config(self) -> bool:
        """清理 Firebase 配置中的 Google 認證設定"""
        firebase_json_path = "TradingAgents/frontend/firebase.json"
        
        print(f"🔍 檢查 Firebase 配置: {firebase_json_path}")
        
        if not os.path.exists(firebase_json_path):
            print(f"❌ 文件不存在: {firebase_json_path}")
            return False
            
        try:
            with open(firebase_json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 備份原文件
            self.backup_file(firebase_json_path)
            
            # 查找並更新 CSP 配置
            updated = False
            
            def update_csp_in_headers(headers_list):
                nonlocal updated
                for header in headers_list:
                    if header.get("key") == "Content-Security-Policy":
                        old_value = header["value"]
                        
                        # 構建正確的 CSP
                        correct_csp = self.build_correct_csp()
                        
                        if old_value != correct_csp:
                            header["value"] = correct_csp
                            updated = True
                            self.changes_made.append(f"🔧 更新 CSP 配置")
                            self.changes_made.append(f"   舊值: {old_value[:100]}...")
                            self.changes_made.append(f"   新值: {correct_csp[:100]}...")
            
            # 檢查不同的配置結構
            if isinstance(config.get("hosting"), list):
                for hosting_config in config["hosting"]:
                    if "headers" in hosting_config:
                        for header_rule in hosting_config["headers"]:
                            if "headers" in header_rule:
                                update_csp_in_headers(header_rule["headers"])
            elif isinstance(config.get("hosting"), dict):
                if "headers" in config["hosting"]:
                    for header_rule in config["hosting"]["headers"]:
                        if "headers" in header_rule:
                            update_csp_in_headers(header_rule["headers"])
            
            # 保存更新後的配置
            if updated and not self.dry_run:
                with open(firebase_json_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                self.changes_made.append(f"💾 已保存更新後的 {firebase_json_path}")
                
            return updated
            
        except Exception as e:
            print(f"❌ 處理 Firebase 配置時出錯: {e}")
            return False
    
    def build_correct_csp(self) -> str:
        """構建正確的 CSP 配置字符串"""
        csp_parts = [
            "default-src 'self'",
            f"script-src 'self' 'unsafe-inline' 'unsafe-eval' {self.correct_config['csp_directives']['script-src']} https://tradingagents-main-xe4ri7r7zq-de.a.run.app https://storage.googleapis.com",
            f"script-src-elem 'self' 'unsafe-inline' {self.correct_config['csp_directives']['script-src-elem']}",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            f"img-src 'self' data: https: blob: {self.correct_config['csp_directives']['img-src']}",
            f"connect-src 'self' https://tradingagents-main-xe4ri7r7zq-de.a.run.app wss://tradingagents-main-xe4ri7r7zq-de.a.run.app wss://echo.websocket.org https://api.finmindtrade.com https://storage.googleapis.com {self.correct_config['csp_directives']['connect-src']}",
            "media-src 'self' data: blob:",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            f"frame-src 'self' {self.correct_config['csp_directives']['frame-src']}",
            "child-src 'self' https://accounts.google.com",
            "frame-ancestors 'none'",
            "upgrade-insecure-requests",
            "report-uri /api/security/csp-report"
        ]
        
        return "; ".join(csp_parts)
    
    def clean_google_auth_service(self) -> bool:
        """清理 GoogleAuthService.ts"""
        service_path = "TradingAgents/frontend/src/services/GoogleAuthService.ts"
        
        print(f"🔍 檢查 Google 認證服務: {service_path}")
        
        if not os.path.exists(service_path):
            print(f"❌ 文件不存在: {service_path}")
            return False
        
        try:
            with open(service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查是否包含正確的 Client ID
            if self.correct_config["client_id"] not in content:
                self.backup_file(service_path)
                
                # 這裡可以添加更多的清理邏輯
                self.changes_made.append(f"⚠️  {service_path} 可能需要手動檢查 Client ID")
                return False
            else:
                self.changes_made.append(f"✅ {service_path} Client ID 正確")
                return True
                
        except Exception as e:
            print(f"❌ 處理 GoogleAuthService 時出錯: {e}")
            return False
    
    def remove_deprecated_files(self) -> bool:
        """移除已棄用的認證相關文件"""
        deprecated_files = [
            "TradingAgents/frontend/src/services/AdminApiService.ts",  # 已標記為 deprecated
            "TradingAgents/frontend/src/admin/AdminApp_Complete.tsx.deprecated",
            "TradingAgents/frontend/src/admin/AdminApp_Enterprise.tsx.deprecated"
        ]
        
        removed_count = 0
        
        for file_path in deprecated_files:
            if os.path.exists(file_path):
                print(f"🗑️  發現已棄用文件: {file_path}")
                
                if not self.dry_run:
                    # 先備份再刪除
                    backup_path = self.backup_file(file_path)
                    os.remove(file_path)
                    
                self.changes_made.append(f"🗑️  移除已棄用文件: {file_path}")
                removed_count += 1
        
        return removed_count > 0
    
    def validate_entry_points(self) -> bool:
        """驗證入口點配置"""
        index_html_path = "TradingAgents/frontend/index.html"
        
        print(f"🔍 檢查入口點配置: {index_html_path}")
        
        if not os.path.exists(index_html_path):
            print(f"❌ 文件不存在: {index_html_path}")
            return False
        
        try:
            with open(index_html_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查當前是主站配置還是管理後台配置
            is_main_site = "main.tsx" in content and "AI 智能投資分析平台" in content
            is_admin_site = "index-admin.tsx" in content and "企業管理後台" in content
            
            if is_main_site:
                self.changes_made.append("✅ index.html 配置為主站 (正確)")
                return True
            elif is_admin_site:
                self.changes_made.append("⚠️  index.html 配置為管理後台 (可能需要檢查)")
                return True
            else:
                self.changes_made.append("❌ index.html 配置不明確")
                return False
                
        except Exception as e:
            print(f"❌ 檢查入口點時出錯: {e}")
            return False
    
    def run_cleanup(self):
        """執行完整清理"""
        print("=" * 60)
        print("🧹 Google 認證配置清理開始")
        if self.dry_run:
            print("🔍 模擬模式 - 不會實際修改文件")
        print("=" * 60)
        print(f"⏰ 清理時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 執行各項清理任務
        firebase_updated = self.clean_firebase_config()
        service_ok = self.clean_google_auth_service()
        deprecated_removed = self.remove_deprecated_files()
        entry_points_ok = self.validate_entry_points()
        
        # 輸出結果
        print("\n" + "=" * 60)
        print("📊 清理結果")
        print("=" * 60)
        
        for change in self.changes_made:
            print(change)
        
        print(f"\n" + "=" * 60)
        if self.dry_run:
            print("🔍 模擬完成 - 使用 --execute 執行實際清理")
        else:
            print("✅ 清理完成")
        print("=" * 60)

def main():
    parser = argparse.ArgumentParser(description="清理 Google 認證配置")
    parser.add_argument("--dry-run", action="store_true", 
                       help="模擬模式，不實際修改文件")
    
    args = parser.parse_args()
    
    cleaner = GoogleAuthCleaner(dry_run=args.dry_run)
    cleaner.run_cleanup()

if __name__ == "__main__":
    main()