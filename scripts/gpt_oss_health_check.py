#!/usr/bin/env python3
"""
GPT-OSS 增強健康檢查腳本
提供完整的服務驗證，包括GPU檢測、模型加載、推理測試等
"""

import json
import time
import requests
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

class Colors:
    """終端顏色定義"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

class GPTOSSHealthChecker:
    """GPT-OSS健康檢查器"""
    
    def __init__(self, host: str = "localhost", port: int = 8080, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "host": host,
            "port": port,
            "checks": {},
            "overall_status": "unknown"
        }
    
    def print_status(self, message: str, status: str = "info"):
        """打印帶顏色的狀態消息"""
        color_map = {
            "success": Colors.GREEN,
            "error": Colors.RED,
            "warning": Colors.YELLOW,
            "info": Colors.BLUE,
            "header": Colors.PURPLE
        }
        color = color_map.get(status, Colors.NC)
        print(f"{color}{message}{Colors.NC}")
    
    def check_container_running(self) -> Dict[str, Any]:
        """檢查Docker容器是否運行"""
        self.print_status("🐳 檢查Docker容器狀態...", "info")
        
        try:
            # 檢查是否有GPT-OSS容器在運行
            result = subprocess.run(
                ["docker", "ps", "--filter", "ancestor=tradingagents:gpt-oss", "--format", "{{.Names}}\t{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                containers = result.stdout.strip().split('\n')
                container_info = []
                for container in containers:
                    if container:
                        name, status = container.split('\t', 1)
                        container_info.append({"name": name, "status": status})
                
                self.print_status(f"✓ 找到 {len(container_info)} 個運行中的容器", "success")
                return {
                    "status": "success",
                    "containers": container_info,
                    "message": f"Found {len(container_info)} running containers"
                }
            else:
                self.print_status("✗ 沒有找到運行中的GPT-OSS容器", "error")
                return {
                    "status": "error",
                    "containers": [],
                    "message": "No running GPT-OSS containers found"
                }
                
        except subprocess.TimeoutExpired:
            self.print_status("✗ Docker命令超時", "error")
            return {"status": "error", "message": "Docker command timeout"}
        except FileNotFoundError:
            self.print_status("✗ Docker未安裝或不在PATH中", "error")
            return {"status": "error", "message": "Docker not found"}
        except Exception as e:
            self.print_status(f"✗ 檢查容器狀態時發生錯誤: {e}", "error")
            return {"status": "error", "message": str(e)}
    
    def check_service_connectivity(self) -> Dict[str, Any]:
        """檢查服務連接性"""
        self.print_status("🌐 檢查服務連接性...", "info")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            
            if response.status_code == 200:
                self.print_status("✓ 服務連接正常", "success")
                return {
                    "status": "success",
                    "response_time": response.elapsed.total_seconds(),
                    "status_code": response.status_code
                }
            else:
                self.print_status(f"✗ 服務返回錯誤狀態碼: {response.status_code}", "error")
                return {
                    "status": "error",
                    "status_code": response.status_code,
                    "message": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.ConnectionError:
            self.print_status(f"✗ 無法連接到服務 {self.base_url}", "error")
            return {"status": "error", "message": "Connection refused"}
        except requests.exceptions.Timeout:
            self.print_status(f"✗ 連接超時 ({self.timeout}秒)", "error")
            return {"status": "error", "message": "Connection timeout"}
        except Exception as e:
            self.print_status(f"✗ 連接檢查失敗: {e}", "error")
            return {"status": "error", "message": str(e)}
    
    def check_health_endpoint(self) -> Dict[str, Any]:
        """檢查健康檢查端點"""
        self.print_status("🏥 檢查健康檢查端點...", "info")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # 檢查關鍵健康指標
                checks = {
                    "service_status": health_data.get("status") == "healthy",
                    "model_loaded": health_data.get("model_loaded", False),
                    "cuda_available": health_data.get("cuda_available", False)
                }
                
                all_healthy = all(checks.values())
                
                if all_healthy:
                    self.print_status("✓ 所有健康檢查通過", "success")
                else:
                    failed_checks = [k for k, v in checks.items() if not v]
                    self.print_status(f"⚠ 部分健康檢查失敗: {', '.join(failed_checks)}", "warning")
                
                return {
                    "status": "success" if all_healthy else "warning",
                    "health_data": health_data,
                    "checks": checks,
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                self.print_status(f"✗ 健康檢查端點返回錯誤: {response.status_code}", "error")
                return {"status": "error", "status_code": response.status_code}
                
        except Exception as e:
            self.print_status(f"✗ 健康檢查失敗: {e}", "error")
            return {"status": "error", "message": str(e)}
    
    def check_gpu_status(self) -> Dict[str, Any]:
        """檢查GPU狀態"""
        self.print_status("🎮 檢查GPU狀態...", "info")
        
        try:
            # 通過API檢查GPU狀態
            response = requests.get(f"{self.base_url}/memory", timeout=self.timeout)
            
            if response.status_code == 200:
                memory_data = response.json()
                
                if "memory_status" in memory_data:
                    memory_status = memory_data["memory_status"]
                    
                    if "message" in memory_status and "CUDA not available" in memory_status["message"]:
                        self.print_status("⚠ CUDA不可用，運行在CPU模式", "warning")
                        return {
                            "status": "warning",
                            "mode": "cpu",
                            "message": "Running in CPU mode"
                        }
                    else:
                        # GPU可用
                        allocated = memory_status.get("allocated_gb", 0)
                        reserved = memory_status.get("reserved_gb", 0)
                        free = memory_status.get("free_gb", 0)
                        usage_pct = memory_status.get("usage_percentage", 0)
                        
                        self.print_status(f"✓ GPU可用 - 已用: {allocated}GB, 保留: {reserved}GB, 空閒: {free}GB ({usage_pct}%)", "success")
                        
                        # 檢查記憶體使用率
                        if usage_pct > 90:
                            self.print_status("⚠ GPU記憶體使用率過高", "warning")
                            status = "warning"
                        else:
                            status = "success"
                        
                        return {
                            "status": status,
                            "mode": "gpu",
                            "memory_status": memory_status
                        }
                else:
                    self.print_status("✗ 無法獲取GPU記憶體信息", "error")
                    return {"status": "error", "message": "No memory status available"}
            else:
                self.print_status(f"✗ GPU狀態檢查失敗: {response.status_code}", "error")
                return {"status": "error", "status_code": response.status_code}
                
        except Exception as e:
            self.print_status(f"✗ GPU狀態檢查失敗: {e}", "error")
            return {"status": "error", "message": str(e)}
    
    def check_inference_capability(self) -> Dict[str, Any]:
        """檢查推理能力"""
        self.print_status("🧠 檢查推理能力...", "info")
        
        test_messages = [
            {"message": "Hello", "max_tokens": 10, "description": "簡單測試"},
            {"message": "分析AAPL股票", "max_tokens": 50, "description": "金融分析測試"}
        ]
        
        results = []
        
        for i, test in enumerate(test_messages, 1):
            self.print_status(f"  測試 {i}: {test['description']}", "info")
            
            try:
                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/chat",
                    json=test,
                    timeout=self.timeout
                )
                end_time = time.time()
                
                if response.status_code == 200:
                    data = response.json()
                    inference_time = end_time - start_time
                    tokens_used = data.get("tokens_used", 0)
                    
                    self.print_status(f"    ✓ 推理成功 - 時間: {inference_time:.2f}s, Tokens: {tokens_used}", "success")
                    
                    results.append({
                        "test": test["description"],
                        "status": "success",
                        "inference_time": inference_time,
                        "tokens_used": tokens_used,
                        "response_length": len(data.get("response", ""))
                    })
                else:
                    self.print_status(f"    ✗ 推理失敗: HTTP {response.status_code}", "error")
                    results.append({
                        "test": test["description"],
                        "status": "error",
                        "status_code": response.status_code
                    })
                    
            except requests.exceptions.Timeout:
                self.print_status(f"    ✗ 推理超時 ({self.timeout}秒)", "error")
                results.append({
                    "test": test["description"],
                    "status": "error",
                    "message": "Timeout"
                })
            except Exception as e:
                self.print_status(f"    ✗ 推理測試失敗: {e}", "error")
                results.append({
                    "test": test["description"],
                    "status": "error",
                    "message": str(e)
                })
        
        # 評估整體推理能力
        successful_tests = [r for r in results if r["status"] == "success"]
        success_rate = len(successful_tests) / len(results) * 100
        
        if success_rate == 100:
            self.print_status(f"✓ 推理能力檢查通過 ({success_rate}%)", "success")
            overall_status = "success"
        elif success_rate >= 50:
            self.print_status(f"⚠ 推理能力部分正常 ({success_rate}%)", "warning")
            overall_status = "warning"
        else:
            self.print_status(f"✗ 推理能力檢查失敗 ({success_rate}%)", "error")
            overall_status = "error"
        
        return {
            "status": overall_status,
            "success_rate": success_rate,
            "test_results": results,
            "avg_inference_time": sum(r.get("inference_time", 0) for r in successful_tests) / len(successful_tests) if successful_tests else 0
        }
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """檢查API端點可用性"""
        self.print_status("🔗 檢查API端點...", "info")
        
        endpoints = [
            {"path": "/health", "method": "GET", "description": "健康檢查"},
            {"path": "/status", "method": "GET", "description": "服務狀態"},
            {"path": "/models", "method": "GET", "description": "模型列表"},
            {"path": "/memory", "method": "GET", "description": "記憶體狀態"}
        ]
        
        results = []
        
        for endpoint in endpoints:
            try:
                if endpoint["method"] == "GET":
                    response = requests.get(f"{self.base_url}{endpoint['path']}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{endpoint['path']}", timeout=10)
                
                if response.status_code == 200:
                    self.print_status(f"  ✓ {endpoint['description']}: OK", "success")
                    results.append({
                        "endpoint": endpoint["path"],
                        "status": "success",
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds()
                    })
                else:
                    self.print_status(f"  ✗ {endpoint['description']}: HTTP {response.status_code}", "error")
                    results.append({
                        "endpoint": endpoint["path"],
                        "status": "error",
                        "status_code": response.status_code
                    })
                    
            except Exception as e:
                self.print_status(f"  ✗ {endpoint['description']}: {e}", "error")
                results.append({
                    "endpoint": endpoint["path"],
                    "status": "error",
                    "message": str(e)
                })
        
        successful_endpoints = [r for r in results if r["status"] == "success"]
        success_rate = len(successful_endpoints) / len(results) * 100
        
        return {
            "status": "success" if success_rate == 100 else "warning" if success_rate >= 75 else "error",
            "success_rate": success_rate,
            "endpoint_results": results
        }
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """運行完整的健康檢查"""
        self.print_status("=" * 60, "header")
        self.print_status("GPT-OSS 完整健康檢查", "header")
        self.print_status("=" * 60, "header")
        
        # 執行所有檢查
        checks = {
            "container": self.check_container_running(),
            "connectivity": self.check_service_connectivity(),
            "health": self.check_health_endpoint(),
            "gpu": self.check_gpu_status(),
            "inference": self.check_inference_capability(),
            "endpoints": self.check_api_endpoints()
        }
        
        self.results["checks"] = checks
        
        # 計算整體狀態
        statuses = [check["status"] for check in checks.values()]
        
        if all(status == "success" for status in statuses):
            overall_status = "healthy"
            self.print_status("\n🎉 整體狀態: 健康", "success")
        elif any(status == "error" for status in statuses):
            overall_status = "unhealthy"
            self.print_status("\n❌ 整體狀態: 不健康", "error")
        else:
            overall_status = "degraded"
            self.print_status("\n⚠️  整體狀態: 降級", "warning")
        
        self.results["overall_status"] = overall_status
        
        # 生成摘要
        self.print_status("\n" + "=" * 60, "header")
        self.print_status("檢查摘要", "header")
        self.print_status("=" * 60, "header")
        
        for check_name, check_result in checks.items():
            status_icon = {
                "success": "✓",
                "warning": "⚠",
                "error": "✗"
            }.get(check_result["status"], "?")
            
            self.print_status(f"{status_icon} {check_name.capitalize()}: {check_result['status']}", 
                            check_result["status"])
        
        return self.results
    
    def save_results(self, filename: str = None):
        """保存檢查結果到文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_check_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        self.print_status(f"\n📄 結果已保存到: {filename}", "info")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="GPT-OSS 增強健康檢查")
    parser.add_argument("--host", default="localhost", help="服務主機地址")
    parser.add_argument("--port", type=int, default=8080, help="服務端口")
    parser.add_argument("--timeout", type=int, default=30, help="請求超時時間(秒)")
    parser.add_argument("--save", help="保存結果到指定文件")
    parser.add_argument("--json", action="store_true", help="以JSON格式輸出結果")
    
    args = parser.parse_args()
    
    # 創建健康檢查器
    checker = GPTOSSHealthChecker(args.host, args.port, args.timeout)
    
    # 運行檢查
    results = checker.run_comprehensive_check()
    
    # 保存結果
    if args.save:
        checker.save_results(args.save)
    
    # JSON輸出
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    # 設置退出碼
    exit_code = {
        "healthy": 0,
        "degraded": 1,
        "unhealthy": 2
    }.get(results["overall_status"], 3)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()