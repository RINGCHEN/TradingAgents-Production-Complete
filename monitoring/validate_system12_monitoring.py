#!/usr/bin/env python3
"""
System 12 監控系統驗證腳本
驗證 Grafana + Prometheus 監控堆疊功能
"""

import requests
import json
import time
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringValidator:
    def __init__(self):
        self.prometheus_url = "http://localhost:9090"
        self.grafana_url = "http://localhost:3001" 
        self.alertmanager_url = "http://localhost:9093"
        
        # 預期運行的服務
        self.expected_services = [
            "prometheus", "grafana", "cadvisor", 
            "node-exporter", "alertmanager"
        ]
        
        # 基本指標查詢
        self.basic_queries = [
            "up",
            "node_memory_MemAvailable_bytes",
            "node_cpu_seconds_total",
            "container_memory_usage_bytes"
        ]

    def test_prometheus_api(self) -> Dict[str, Any]:
        """測試 Prometheus API 連接和基本查詢"""
        results = {
            "api_accessible": False,
            "targets_healthy": 0,
            "total_targets": 0,
            "metrics_available": [],
            "errors": []
        }
        
        try:
            # 測試 API 連接
            response = requests.get(f"{self.prometheus_url}/api/v1/status/config", timeout=5)
            if response.status_code == 200:
                results["api_accessible"] = True
                logger.info("✅ Prometheus API 連接成功")
            
            # 檢查目標狀態
            targets_response = requests.get(f"{self.prometheus_url}/api/v1/targets", timeout=5)
            if targets_response.status_code == 200:
                targets_data = targets_response.json()
                active_targets = targets_data["data"]["activeTargets"]
                results["total_targets"] = len(active_targets)
                results["targets_healthy"] = sum(1 for target in active_targets if target["health"] == "up")
                logger.info(f"✅ 目標狀態: {results['targets_healthy']}/{results['total_targets']} 健康")
            
            # 測試基本指標查詢
            for query in self.basic_queries:
                try:
                    query_response = requests.get(
                        f"{self.prometheus_url}/api/v1/query",
                        params={"query": query},
                        timeout=5
                    )
                    if query_response.status_code == 200:
                        data = query_response.json()
                        if data["data"]["result"]:
                            results["metrics_available"].append(query)
                            logger.info(f"✅ 指標 {query} 可用")
                except Exception as e:
                    results["errors"].append(f"查詢 {query} 失敗: {str(e)}")
            
        except Exception as e:
            results["errors"].append(f"Prometheus 連接失敗: {str(e)}")
            logger.error(f"❌ Prometheus 連接失敗: {e}")
        
        return results

    def test_grafana_access(self) -> Dict[str, Any]:
        """測試 Grafana 訪問"""
        results = {
            "accessible": False,
            "login_page": False,
            "errors": []
        }
        
        try:
            response = requests.get(self.grafana_url, timeout=5, allow_redirects=False)
            if response.status_code == 302 and "/login" in response.headers.get("Location", ""):
                results["accessible"] = True
                results["login_page"] = True
                logger.info("✅ Grafana 訪問正常，已重定向到登錄頁面")
            elif response.status_code == 200:
                results["accessible"] = True
                logger.info("✅ Grafana 訪問正常")
        except Exception as e:
            results["errors"].append(f"Grafana 連接失敗: {str(e)}")
            logger.error(f"❌ Grafana 連接失敗: {e}")
        
        return results

    def test_alertmanager_access(self) -> Dict[str, Any]:
        """測試 AlertManager 訪問"""
        results = {
            "accessible": False,
            "api_working": False,
            "errors": []
        }
        
        try:
            # 測試 AlertManager 狀態 API
            response = requests.get(f"{self.alertmanager_url}/api/v1/status", timeout=5)
            if response.status_code == 200:
                results["accessible"] = True
                results["api_working"] = True
                logger.info("✅ AlertManager API 正常運行")
            else:
                # 嘗試基本訪問
                base_response = requests.get(self.alertmanager_url, timeout=5)
                if base_response.status_code in [200, 405]:  # 405 is expected for HEAD request
                    results["accessible"] = True
                    logger.info("✅ AlertManager 基本訪問正常")
        except Exception as e:
            results["errors"].append(f"AlertManager 連接失敗: {str(e)}")
            logger.error(f"❌ AlertManager 連接失敗: {e}")
        
        return results

    def validate_system(self) -> Dict[str, Any]:
        """執行完整的系統驗證"""
        logger.info("🚀 開始 System 12 監控系統驗證...")
        
        validation_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": "UNKNOWN",
            "prometheus": {},
            "grafana": {},
            "alertmanager": {},
            "summary": {
                "services_tested": 3,
                "services_passed": 0,
                "critical_issues": [],
                "recommendations": []
            }
        }
        
        # 測試 Prometheus
        logger.info("📊 測試 Prometheus...")
        validation_results["prometheus"] = self.test_prometheus_api()
        if validation_results["prometheus"]["api_accessible"]:
            validation_results["summary"]["services_passed"] += 1
        else:
            validation_results["summary"]["critical_issues"].append("Prometheus API 不可訪問")
        
        # 測試 Grafana
        logger.info("📈 測試 Grafana...")
        validation_results["grafana"] = self.test_grafana_access()
        if validation_results["grafana"]["accessible"]:
            validation_results["summary"]["services_passed"] += 1
        else:
            validation_results["summary"]["critical_issues"].append("Grafana 不可訪問")
        
        # 測試 AlertManager
        logger.info("🚨 測試 AlertManager...")
        validation_results["alertmanager"] = self.test_alertmanager_access()
        if validation_results["alertmanager"]["accessible"]:
            validation_results["summary"]["services_passed"] += 1
        else:
            validation_results["summary"]["critical_issues"].append("AlertManager 不可訪問")
        
        # 計算總體狀態
        success_rate = validation_results["summary"]["services_passed"] / validation_results["summary"]["services_tested"] * 100
        
        if success_rate == 100:
            validation_results["overall_status"] = "PASS"
            logger.info("🎉 System 12 驗證通過！")
        elif success_rate >= 75:
            validation_results["overall_status"] = "PARTIAL_PASS"
            logger.warning("⚠️ System 12 部分通過")
        else:
            validation_results["overall_status"] = "FAIL"
            logger.error("❌ System 12 驗證失敗")
        
        # 生成建議
        if validation_results["prometheus"]["targets_healthy"] < validation_results["prometheus"]["total_targets"]:
            validation_results["summary"]["recommendations"].append(
                f"有 {validation_results['prometheus']['total_targets'] - validation_results['prometheus']['targets_healthy']} 個監控目標離線，檢查相關服務"
            )
        
        if len(validation_results["prometheus"]["metrics_available"]) < len(self.basic_queries):
            validation_results["summary"]["recommendations"].append("某些基本指標不可用，可能影響儀表板顯示")
        
        return validation_results

    def print_validation_report(self, results: Dict[str, Any]):
        """打印驗證報告"""
        print("\n" + "="*80)
        print(f"🔍 TradingAgents System 12 監控系統驗證報告")
        print(f"⏰ 驗證時間: {results['timestamp']}")
        print(f"🎯 總體狀態: {results['overall_status']}")
        print("="*80)
        
        # Prometheus 狀態
        prom = results["prometheus"]
        print(f"\n📊 Prometheus 狀態:")
        print(f"  - API 連接: {'✅' if prom.get('api_accessible') else '❌'}")
        print(f"  - 健康目標: {prom.get('targets_healthy', 0)}/{prom.get('total_targets', 0)}")
        print(f"  - 可用指標: {len(prom.get('metrics_available', []))}/{len(self.basic_queries)}")
        
        # Grafana 狀態  
        grafana = results["grafana"]
        print(f"\n📈 Grafana 狀態:")
        print(f"  - 服務可訪問: {'✅' if grafana.get('accessible') else '❌'}")
        print(f"  - 登錄頁面: {'✅' if grafana.get('login_page') else '❌'}")
        
        # AlertManager 狀態
        alert = results["alertmanager"]
        print(f"\n🚨 AlertManager 狀態:")
        print(f"  - 服務可訪問: {'✅' if alert.get('accessible') else '❌'}")
        print(f"  - API 運行: {'✅' if alert.get('api_working') else '❌'}")
        
        # 摘要
        summary = results["summary"]
        print(f"\n📋 驗證摘要:")
        print(f"  - 通過率: {summary['services_passed']}/{summary['services_tested']} ({summary['services_passed']/summary['services_tested']*100:.1f}%)")
        
        if summary["critical_issues"]:
            print(f"  - ⚠️ 關鍵問題:")
            for issue in summary["critical_issues"]:
                print(f"    • {issue}")
        
        if summary["recommendations"]:
            print(f"  - 💡 建議:")
            for rec in summary["recommendations"]:
                print(f"    • {rec}")
        
        # 訪問信息
        if results["overall_status"] in ["PASS", "PARTIAL_PASS"]:
            print(f"\n🔗 監控訪問地址:")
            print(f"  - Grafana: http://localhost:3001 (admin/admin123)")
            print(f"  - Prometheus: http://localhost:9090")
            print(f"  - AlertManager: http://localhost:9093")
            print(f"  - cAdvisor: http://localhost:8080")
        
        print("\n" + "="*80)

def main():
    validator = MonitoringValidator()
    results = validator.validate_system()
    validator.print_validation_report(results)
    
    # 保存結果到文件
    report_file = "system12_monitoring_validation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"📄 詳細報告已保存至: {report_file}")
    
    return 0 if results["overall_status"] == "PASS" else 1

if __name__ == "__main__":
    exit(main())