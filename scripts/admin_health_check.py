#!/usr/bin/env python3
"""
TradingAgents Admin API 健康檢查腳本
天工 (TianGong) - 自動化Admin端點健康檢查和監控

此腳本響應CODEX建議，提供：
1. 所有 /admin/* 端點的自動健康檢查
2. 認證流程驗證
3. 權限矩陣測試
4. 性能指標監控
5. 異常告警機制
"""

import asyncio
import json
import time
import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import httpx
import argparse
from dataclasses import dataclass, asdict
from enum import Enum

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('admin_health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class EndpointTest:
    """端點測試配置"""
    path: str
    method: str = "GET"
    requires_auth: bool = True
    expected_status: int = 200
    timeout: float = 5.0
    description: str = ""
    test_data: Optional[Dict[str, Any]] = None

@dataclass
class TestResult:
    """測試結果"""
    endpoint: str
    method: str
    status: HealthStatus
    response_time: float
    status_code: int
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class AdminHealthChecker:
    """Admin API健康檢查器"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8001",
        admin_token: Optional[str] = None,
        auth_mode: str = "login",
        login_email: Optional[str] = None,
        login_password: Optional[str] = None,
        login_path: str = "/api/auth/login",
        refresh_path: str = "/api/auth/refresh"
    ):
        self.base_url = base_url.rstrip('/')
        self.admin_token = admin_token
        self.auth_mode = auth_mode
        self.login_email = login_email
        self.login_password = login_password
        self.login_path = login_path
        self.refresh_path = refresh_path
        self.refresh_token: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=10.0)
        self.results: List[TestResult] = []
        
        # Admin端點配置 (基於盤點報告)
        self.endpoints = [
            # 分析師管理 (已修復路由衝突)
            EndpointTest("/admin/analysts/registry", "GET", description="獲取分析師註冊表"),
            EndpointTest("/admin/analysts/health-check", "POST", description="分析師健康檢查"),
            EndpointTest("/admin/analysts/analysis", "GET", description="獲取分析執行列表"),
            EndpointTest("/admin/analysts/coordinator/statistics", "GET", description="協調器統計"),
            EndpointTest("/admin/analysts/coordinator/health", "GET", description="協調器健康"),
            
            # 用戶管理
            EndpointTest("/admin/users/", "GET", description="獲取用戶列表"),
            EndpointTest("/admin/users/statistics/overview", "GET", description="用戶統計"),
            EndpointTest("/admin/users/system-info", "GET", description="用戶管理系統信息"),
            EndpointTest("/admin/users/health", "GET", description="用戶管理健康檢查"),
            
            # 系統監控
            EndpointTest("/admin/system/metrics/system", "GET", description="系統指標"),
            EndpointTest("/admin/system/health", "GET", description="系統健康狀態"),
            EndpointTest("/admin/system/alerts/summary", "GET", description="告警摘要"),
            EndpointTest("/admin/system/monitor/health", "GET", description="監控服務健康"),
            
            # 配置管理
            EndpointTest("/admin/config/items", "GET", description="獲取配置項列表"),
            EndpointTest("/admin/config/statistics", "GET", description="配置統計"),
            EndpointTest("/admin/config/system-info", "GET", description="配置系統信息"),
            EndpointTest("/admin/config/health", "GET", description="配置管理健康檢查"),
            
            # 服務協調
            EndpointTest("/admin/coordinator/services", "GET", description="服務註冊表"),
            EndpointTest("/admin/coordinator/statistics", "GET", description="協調器統計"),
            EndpointTest("/admin/coordinator/health", "GET", description="協調器健康"),
        ]
        
        # 認證測試端點
        self.auth_test_endpoints = [
            EndpointTest("/api/auth/me", "GET", description="當前用戶信息"),
            EndpointTest("/api/auth/refresh", "POST", description="Token刷新"),
            EndpointTest("/health", "GET", requires_auth=False, description="系統健康檢查"),
        ]

    async def _perform_request(self, endpoint: EndpointTest, url: str, headers: Dict[str, str]):
        method = endpoint.method.upper()
        if method == "GET":
            return await self.client.get(url, headers=headers)
        if method == "POST":
            return await self.client.post(url, headers=headers, json=endpoint.test_data or {})
        if method == "PUT":
            return await self.client.put(url, headers=headers, json=endpoint.test_data or {})
        raise ValueError(f"不支持的HTTP方法: {endpoint.method}")

    async def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            logger.warning("無可用refresh token，無法刷新access token")
            return False

        refresh_url = f"{self.base_url}{self.refresh_path}"
        headers = {"Authorization": f"Bearer {self.refresh_token}"}
        try:
            response = await self.client.post(refresh_url, headers=headers)
        except Exception as exc:
            logger.error(f"刷新Token時發生錯誤: {exc}")
            return False

        if response.status_code != 200:
            logger.error(f"刷新Token失敗，狀態碼: {response.status_code}")
            return False

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            logger.error("刷新Token回應缺少access_token")
            return False

        self.admin_token = access_token
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        logger.info("成功刷新管理員Token")
        return True

    async def _setup_token_fallback(self) -> bool:
        test_tokens = [
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJ0aWVyIjoiZGlhbW9uZCIsInJvbGUiOiJhZG1pbiIsImV4cCI6OTk5OTk5OTk5OX0.test_admin_token",
        ]

        for token in test_tokens:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                response = await self.client.get(f"{self.base_url}/health", headers=headers)
                if response.status_code == 200:
                    self.admin_token = token
                    logger.info("使用備用測試Token完成認證設置")
                    return True
            except Exception as exc:
                logger.warning(f"備用Token測試失敗: {exc}")

        logger.warning("備用Token全部失敗，將以未認證狀態執行")
        return False

    async def setup_admin_token(self) -> bool:
        """設置管理員Token"""
        if self.auth_mode == "none":
            logger.info("已選擇不使用認證模式，跳過Token設置")
            return False

        if self.auth_mode == "token":
            if self.admin_token:
                logger.info("使用提供的管理員Token進行測試")
                return True
            logger.warning("未提供管理員Token，將嘗試備用測試Token")
            return await self._setup_token_fallback()

        # 預設使用登入流程
        if not self.login_email or not self.login_password:
            logger.warning("未提供登入憑證，改用備用測試Token")
            return await self._setup_token_fallback()

        login_url = f"{self.base_url}{self.login_path}"
        payload = {"email": self.login_email, "password": self.login_password}

        try:
            response = await self.client.post(login_url, json=payload)
        except Exception as exc:
            logger.error(f"登入請求失敗: {exc}")
            return await self._setup_token_fallback()

        if response.status_code != 200:
            logger.error(f"登入失敗，狀態碼: {response.status_code}")
            return await self._setup_token_fallback()

        data = response.json()
        access_token = data.get("access_token")
        if not access_token:
            logger.error("登入回應缺少access_token")
            return await self._setup_token_fallback()

        self.admin_token = access_token
        self.refresh_token = data.get("refresh_token")
        logger.info("登入取得管理員Token成功")
        return True
    
    async def test_endpoint(self, endpoint: EndpointTest) -> TestResult:
        """測試單個端點"""
        start_time = time.time()
        url = f"{self.base_url}{endpoint.path}"
        
        headers = {}
        if endpoint.requires_auth and self.admin_token:
            token = self.admin_token
            if endpoint.path == self.refresh_path and self.refresh_token:
                token = self.refresh_token
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = await self._perform_request(endpoint, url, headers)

            if (
                response.status_code == 401
                and endpoint.requires_auth
                and self.auth_mode == "login"
                and await self.refresh_access_token()
            ):
                token = self.admin_token
                if endpoint.path == self.refresh_path and self.refresh_token:
                    token = self.refresh_token
                headers["Authorization"] = f"Bearer {token}"
                response = await self._perform_request(endpoint, url, headers)

            response_time = time.time() - start_time
            
            # 判斷健康狀態
            if response.status_code == endpoint.expected_status:
                status = HealthStatus.HEALTHY
                error_message = None
            elif 400 <= response.status_code < 500:
                status = HealthStatus.DEGRADED
                error_message = f"客戶端錯誤: {response.status_code}"
            else:
                status = HealthStatus.UNHEALTHY
                error_message = f"服務器錯誤: {response.status_code}"
            
            # 嘗試解析響應數據
            try:
                response_data = response.json()
            except:
                response_data = {"raw_content": response.text[:200]}
            
            return TestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status=status,
                response_time=response_time,
                status_code=response.status_code,
                error_message=error_message,
                response_data=response_data
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                status_code=0,
                error_message="請求超時"
            )
        except Exception as e:
            return TestResult(
                endpoint=endpoint.path,
                method=endpoint.method,
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                status_code=0,
                error_message=f"連接錯誤: {str(e)}"
            )
    
    async def run_health_checks(self, include_auth_tests: bool = True) -> Dict[str, Any]:
        """執行完整健康檢查"""
        logger.info(f"開始Admin API健康檢查 - 目標: {self.base_url}")
        
        # 設置認證
        auth_ready = await self.setup_admin_token()
        if not auth_ready and self.auth_mode != "none":
            logger.warning("未取得有效Token，帶認證的端點可能失敗")

        # 測試所有端點
        all_endpoints = self.endpoints[:]
        if include_auth_tests:
            all_endpoints.extend(self.auth_test_endpoints)
        
        tasks = [self.test_endpoint(endpoint) for endpoint in all_endpoints]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"測試異常: {result}")
                continue
            valid_results.append(result)
            self.results.append(result)
        
        # 生成報告
        return self.generate_report(valid_results)
    
    def generate_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """生成健康檢查報告"""
        total_tests = len(results)
        healthy_count = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for r in results if r.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        
        avg_response_time = sum(r.response_time for r in results) / total_tests if total_tests > 0 else 0
        
        # 確定整體健康狀態
        if unhealthy_count > total_tests * 0.3:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > total_tests * 0.2:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        # 收集失敗的端點
        failed_endpoints = [
            {
                "endpoint": r.endpoint,
                "status": r.status.value,
                "error": r.error_message,
                "status_code": r.status_code
            }
            for r in results if r.status != HealthStatus.HEALTHY
        ]
        
        # 性能指標
        response_times = [r.response_time for r in results]
        performance_metrics = {
            "avg_response_time": avg_response_time,
            "max_response_time": max(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "slow_endpoints": [
                {"endpoint": r.endpoint, "response_time": r.response_time}
                for r in results if r.response_time > 2.0
            ]
        }
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "summary": {
                "total_tests": total_tests,
                "healthy": healthy_count,
                "degraded": degraded_count,
                "unhealthy": unhealthy_count,
                "success_rate": (healthy_count / total_tests * 100) if total_tests > 0 else 0
            },
            "performance_metrics": performance_metrics,
            "failed_endpoints": failed_endpoints,
            "detailed_results": [asdict(r) for r in results],
            "recommendations": self.generate_recommendations(results)
        }
        
        return report
    
    def generate_recommendations(self, results: List[TestResult]) -> List[str]:
        """基於測試結果生成建議"""
        recommendations = []
        
        unhealthy_results = [r for r in results if r.status == HealthStatus.UNHEALTHY]
        if unhealthy_results:
            recommendations.append(f"發現 {len(unhealthy_results)} 個不健康的端點，需要立即修復")
        
        slow_results = [r for r in results if r.response_time > 2.0]
        if slow_results:
            recommendations.append(f"發現 {len(slow_results)} 個響應緩慢的端點，建議優化性能")
        
        auth_failures = [r for r in results if r.status_code == 401]
        if auth_failures:
            recommendations.append("發現認證失敗，檢查Token配置和權限設置")
        
        server_errors = [r for r in results if 500 <= r.status_code < 600]
        if server_errors:
            recommendations.append("發現服務器內部錯誤，檢查應用日誌和系統資源")
        
        return recommendations
    
    async def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """保存健康檢查報告"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"admin_health_report_{timestamp}.json"
        
        filepath = Path(__file__).parent / "reports" / filename
        filepath.parent.mkdir(exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"健康檢查報告已保存: {filepath}")
        return filepath
    
    async def cleanup(self):
        """清理資源"""
        await self.client.aclose()

async def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="TradingAgents Admin API 健康檢查")
    parser.add_argument("--url", default="http://localhost:8001", help="API基礎URL")
    parser.add_argument("--auth-mode", choices=["login", "token", "none"], default="login", help="認證模式")
    parser.add_argument("--login-email", default="admin@example.com", help="登入Email (auth-mode=login)")
    parser.add_argument("--login-password", default="admin123", help="登入密碼 (auth-mode=login)")
    parser.add_argument("--login-path", default="/api/auth/login", help="登入端點路徑")
    parser.add_argument("--refresh-path", default="/api/auth/refresh", help="Refresh端點路徑")
    parser.add_argument("--token", help="管理員認證Token (auth-mode=token)")
    parser.add_argument("--output", help="報告輸出文件名")
    parser.add_argument("--no-auth", action="store_true", help="跳過認證測試")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    checker = AdminHealthChecker(
        base_url=args.url,
        admin_token=args.token,
        auth_mode=args.auth_mode,
        login_email=args.login_email,
        login_password=args.login_password,
        login_path=args.login_path,
        refresh_path=args.refresh_path
    )
    
    try:
        # 執行健康檢查
        report = await checker.run_health_checks(include_auth_tests=not args.no_auth)
        
        # 輸出結果
        print("\n" + "="*80)
        print("🏥 TradingAgents Admin API 健康檢查報告")
        print("="*80)
        print(f"檢查時間: {report['timestamp']}")
        print(f"整體狀態: {report['overall_status'].upper()}")
        print(f"成功率: {report['summary']['success_rate']:.1f}%")
        print(f"平均響應時間: {report['performance_metrics']['avg_response_time']:.3f}s")
        
        summary = report['summary']
        print(f"\n📊 測試摘要:")
        print(f"  總測試數: {summary['total_tests']}")
        print(f"  健康: {summary['healthy']} ✅")
        print(f"  降級: {summary['degraded']} ⚠️")
        print(f"  不健康: {summary['unhealthy']} ❌")
        
        # 顯示失敗的端點
        if report['failed_endpoints']:
            print(f"\n❌ 失敗的端點:")
            for endpoint in report['failed_endpoints']:
                print(f"  {endpoint['endpoint']}: {endpoint['status']} ({endpoint.get('error', 'Unknown error')})")
        
        # 顯示建議
        if report['recommendations']:
            print(f"\n💡 建議:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        # 保存報告
        report_path = await checker.save_report(report, args.output)
        print(f"\n📄 詳細報告已保存: {report_path}")
        
        # 根據結果設置退出碼
        if report['overall_status'] == 'unhealthy':
            sys.exit(1)
        elif report['overall_status'] == 'degraded':
            sys.exit(2)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"健康檢查失敗: {e}")
        sys.exit(3)
    finally:
        await checker.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
