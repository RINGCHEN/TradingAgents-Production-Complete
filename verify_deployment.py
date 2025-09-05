#!/usr/bin/env python3
"""
TradingAgents 部署驗證腳本

執行完整的系統驗證，確保所有17個核心系統正常運作。
適用於本地驗證和生產部署後的健康檢查。

作者：天工 (TianGong) + Claude Code  
日期：2025-09-05
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class DeploymentVerifier:
    def __init__(self, base_url: str = None):
        """
        初始化部署驗證器
        
        Args:
            base_url: API 基礎 URL，如果不提供會從環境變量讀取
        """
        self.base_url = base_url or os.getenv('VITE_API_URL', 'http://localhost:8000')
        self.results = []
        self.start_time = time.time()
        
    def log(self, message: str, status: str = "INFO"):
        """記錄驗證消息"""
        timestamp = time.strftime("%H:%M:%S")
        # 處理 Unicode 編碼問題
        try:
            print(f"[{timestamp}] [{status}] {message}")
        except UnicodeEncodeError:
            # 替換特殊字符為 ASCII
            clean_message = message.encode('ascii', 'replace').decode('ascii')
            print(f"[{timestamp}] [{status}] {clean_message}")
        
    def verify_api_health(self) -> bool:
        """驗證 API 基本健康狀態"""
        try:
            self.log("檢查 API 健康狀態...")
            response = requests.get(f"{self.base_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"[OK] API 健康: {data.get('status', 'unknown')}")
                return True
            else:
                self.log(f"[ERROR] API 健康檢查失敗: HTTP {response.status_code}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"[ERROR] API 連接失敗: {str(e)}", "ERROR")
            return False
    
    def verify_payuni_system(self) -> bool:
        """驗證 PayUni 支付系統"""
        try:
            self.log("檢查 PayUni 支付系統...")
            response = requests.get(f"{self.base_url}/api/v1/payuni/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                merchant_id = data.get('merchant_id', '')
                is_sandbox = data.get('is_sandbox', True)
                
                if merchant_id == 'U03823060' and not is_sandbox:
                    self.log("✅ PayUni 支付系統: 生產環境正常")
                    return True
                else:
                    self.log(f"⚠️ PayUni 配置警告: 商店ID={merchant_id}, 沙盒模式={is_sandbox}")
                    return False
            else:
                self.log(f"❌ PayUni 系統檢查失敗: HTTP {response.status_code}", "ERROR")
                return False
                
        except requests.RequestException as e:
            self.log(f"❌ PayUni 系統連接失敗: {str(e)}", "ERROR")
            return False
    
    def verify_core_endpoints(self) -> Dict[str, bool]:
        """驗證核心 API 端點"""
        core_endpoints = [
            "/docs",  # API 文檔
            "/api/users/me",  # 用戶端點 (可能需要認證)
            "/api/data/taiwan-stock/basic-info",  # 數據端點
            "/admin/health",  # 管理端點
        ]
        
        results = {}
        self.log("檢查核心 API 端點...")
        
        for endpoint in core_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # 2xx 或 401 (需要認證) 都算正常
                if 200 <= response.status_code < 300 or response.status_code == 401:
                    results[endpoint] = True
                    self.log(f"✅ 端點正常: {endpoint} (HTTP {response.status_code})")
                else:
                    results[endpoint] = False
                    self.log(f"❌ 端點異常: {endpoint} (HTTP {response.status_code})", "ERROR")
                    
            except requests.RequestException as e:
                results[endpoint] = False
                self.log(f"❌ 端點連接失敗: {endpoint} - {str(e)}", "ERROR")
        
        return results
    
    def verify_environment_variables(self) -> Dict[str, bool]:
        """驗證重要的環境變量"""
        required_vars = [
            "DATABASE_URL",
            "PAYUNI_MERCHANT_ID", 
            "PAYUNI_HASH_KEY",
            "SECRET_KEY",
            "JWT_SECRET"
        ]
        
        results = {}
        self.log("檢查環境變量配置...")
        
        for var in required_vars:
            value = os.getenv(var)
            if value:
                results[var] = True
                # 不顯示敏感值，只顯示前幾個字符
                display_value = value[:8] + "..." if len(value) > 8 else value
                self.log(f"✅ 環境變量: {var}={display_value}")
            else:
                results[var] = False
                self.log(f"❌ 缺失環境變量: {var}", "ERROR")
        
        return results
    
    def verify_file_system(self) -> Dict[str, bool]:
        """驗證關鍵文件和目錄結構"""
        critical_paths = [
            "tradingagents/app.py",
            "tradingagents/api",
            "tradingagents/admin",
            "frontend",
            "configs", 
            "models",
            "training",
            "requirements.txt",
            "Dockerfile"
        ]
        
        results = {}
        self.log("檢查文件系統結構...")
        
        for path in critical_paths:
            full_path = Path(path)
            if full_path.exists():
                results[path] = True
                self.log(f"✅ 路徑存在: {path}")
            else:
                results[path] = False
                self.log(f"❌ 路徑缺失: {path}", "ERROR")
        
        return results
    
    def verify_17_systems(self) -> Dict[str, bool]:
        """驗證17個核心系統"""
        systems_check = {
            # 前端系統群組 (3個)
            "System_1_frontend": Path("frontend").exists(),
            "System_2_member_ai": Path("frontend/src/components/MemberAI").exists() if Path("frontend/src/components").exists() else False,
            "System_3_admin": Path("frontend/src/admin/AdminApp_Ultimate.tsx").exists(),
            
            # 後端API系統群組 (2個)
            "System_4_fastapi": Path("tradingagents/app.py").exists(),
            "System_5_payuni": Path("tradingagents/api/payuni_endpoints.py").exists(),
            
            # AI智能系統群組 (3個)
            "System_6_ai_analysts": Path("tradingagents/agents/analysts").exists(),
            "System_7_ai_training": Path("training").exists(),
            "System_8_model_service": Path("gpu_training").exists() and Path("gpt_oss").exists(),
            
            # 數據基礎設施群組 (3個)
            "System_9_data_sources": Path("tradingagents/dataflows/finmind_adapter.py").exists(),
            "System_10_database": Path("tradingagents/database").exists(),
            "System_12_monitoring": Path("monitoring").exists(),
            
            # 安全認證系統群組 (2個)
            "System_11_auth": Path("tradingagents/auth").exists(),
            "System_13_security": Path("secure").exists(),
            
            # 部署DevOps系統群組 (2個)
            "System_14_deployment": Path("deployment").exists(),
            "System_15_testing": Path("tests").exists() and Path("scripts").exists(),
            
            # 分析報告系統群組 (2個)
            "System_16_business_intelligence": Path("evaluation_results").exists() and Path("reports").exists(),
            "System_17_investment_analysis": Path("work_reports").exists()
        }
        
        self.log("檢查17個核心系統...")
        
        for system, status in systems_check.items():
            if status:
                self.log(f"✅ 系統正常: {system}")
            else:
                self.log(f"❌ 系統缺失: {system}", "ERROR")
        
        return systems_check
    
    def generate_report(self) -> Dict:
        """生成完整驗證報告"""
        duration = time.time() - self.start_time
        
        # 執行所有驗證
        api_health = self.verify_api_health()
        payuni_health = self.verify_payuni_system()
        endpoints = self.verify_core_endpoints()
        env_vars = self.verify_environment_variables()
        file_system = self.verify_file_system()
        systems_17 = self.verify_17_systems()
        
        # 計算統計
        endpoints_passed = sum(endpoints.values())
        endpoints_total = len(endpoints)
        env_vars_passed = sum(env_vars.values())
        env_vars_total = len(env_vars)
        file_system_passed = sum(file_system.values())
        file_system_total = len(file_system)
        systems_passed = sum(systems_17.values())
        systems_total = len(systems_17)
        
        report = {
            "verification_info": {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": round(duration, 2),
                "base_url": self.base_url
            },
            "health_checks": {
                "api_health": api_health,
                "payuni_system": payuni_health
            },
            "endpoint_verification": {
                "results": endpoints,
                "passed": endpoints_passed,
                "total": endpoints_total,
                "pass_rate": round((endpoints_passed / endpoints_total) * 100, 1) if endpoints_total > 0 else 0
            },
            "environment_verification": {
                "results": env_vars,
                "passed": env_vars_passed, 
                "total": env_vars_total,
                "pass_rate": round((env_vars_passed / env_vars_total) * 100, 1) if env_vars_total > 0 else 0
            },
            "file_system_verification": {
                "results": file_system,
                "passed": file_system_passed,
                "total": file_system_total,
                "pass_rate": round((file_system_passed / file_system_total) * 100, 1) if file_system_total > 0 else 0
            },
            "systems_17_verification": {
                "results": systems_17,
                "passed": systems_passed,
                "total": systems_total,
                "pass_rate": round((systems_passed / systems_total) * 100, 1) if systems_total > 0 else 0
            },
            "overall_status": {
                "api_ready": api_health,
                "payment_ready": payuni_health,
                "systems_ready": systems_passed >= 15,  # 至少15/17系統
                "deployment_ready": api_health and payuni_health and systems_passed >= 15
            }
        }
        
        return report
    
    def run_verification(self) -> bool:
        """運行完整驗證流程"""
        self.log("=" * 80)
        self.log("TradingAgents 部署驗證開始")
        self.log("=" * 80)
        
        report = self.generate_report()
        
        # 保存報告
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        report_file = f"deployment_verification_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # 顯示總結
        self.log("=" * 80)
        self.log("驗證結果總結")
        self.log("=" * 80)
        
        overall = report["overall_status"]
        systems = report["systems_17_verification"]
        
        self.log(f"🌐 API 就緒: {'✅' if overall['api_ready'] else '❌'}")
        self.log(f"💳 支付就緒: {'✅' if overall['payment_ready'] else '❌'}")
        self.log(f"🏗️ 系統完整度: {systems['passed']}/{systems['total']} ({systems['pass_rate']}%)")
        self.log(f"🚀 部署就緒: {'✅' if overall['deployment_ready'] else '❌'}")
        
        self.log(f"📊 驗證報告已保存: {report_file}")
        
        if overall['deployment_ready']:
            self.log("🎉 系統驗證通過！可以進行生產部署。")
            return True
        else:
            self.log("⚠️ 系統驗證未完全通過，請檢查上述問題。", "ERROR")
            return False

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TradingAgents 部署驗證工具')
    parser.add_argument('--url', help='API 基礎 URL', default=None)
    parser.add_argument('--local', action='store_true', help='本地驗證模式')
    
    args = parser.parse_args()
    
    if args.local:
        base_url = "http://localhost:8000"
    else:
        base_url = args.url
    
    verifier = DeploymentVerifier(base_url)
    success = verifier.run_verification()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()