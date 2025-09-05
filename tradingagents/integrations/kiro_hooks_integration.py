"""KIRO Hooks 監控系統整合
基於 .kiro/hooks 設計實作
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
import aiohttp
import json

logger = logging.getLogger(__name__)

class HookStatus(Enum):
    """Hook 狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class HookTrigger(Enum):
    """Hook 觸發類型"""
    SCHEDULED = "scheduled"
    EVENT = "event"
    API_CALL = "api_call"
    EXCEPTION = "exception"

class SystemHealthMetrics:
    """系統健康指標類"""
    
    def __init__(self):
        self.reset_metrics()
    
    def reset_metrics(self):
        """重置指標"""
        self.api_response_times = []
        self.error_count = 0
        self.success_count = 0
        self.last_check = datetime.now()
        self.component_status = {}
    
    def add_api_response(self, response_time: float, success: bool):
        """添加 API 回應記錄"""
        self.api_response_times.append({
            "time": response_time,
            "timestamp": datetime.now(),
            "success": success
        })
        
        # 保留最近100筆記錄
        if len(self.api_response_times) > 100:
            self.api_response_times = self.api_response_times[-100:]
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
    
    def get_average_response_time(self, minutes: int = 5) -> float:
        """取得平均回應時間"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_responses = [
            r["time"] for r in self.api_response_times
            if r["timestamp"] > cutoff_time and r["success"]
        ]
        
        if not recent_responses:
            return 0.0
        
        return sum(recent_responses) / len(recent_responses)
    
    def get_error_rate(self, minutes: int = 5) -> float:
        """取得錯誤率"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_responses = [
            r for r in self.api_response_times
            if r["timestamp"] > cutoff_time
        ]
        
        if not recent_responses:
            return 0.0
        
        error_count = sum(1 for r in recent_responses if not r["success"])
        return error_count / len(recent_responses)

class KiroHook:
    """單個 KIRO Hook 的基礎類"""
    
    def __init__(
        self,
        name: str,
        description: str,
        trigger: HookTrigger,
        schedule: Optional[str] = None,
        enabled: bool = True
    ):
        self.name = name
        self.description = description
        self.trigger = trigger
        self.schedule = schedule
        self.enabled = enabled
        self.status = HookStatus.INACTIVE
        self.last_execution = None
        self.execution_count = 0
        self.error_count = 0
        self.callbacks = []
    
    def add_callback(self, callback: Callable):
        """添加回調函數"""
        self.callbacks.append(callback)
    
    async def execute(self, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行 Hook"""
        if not self.enabled:
            return {"status": "skipped", "reason": "disabled"}
        
        try:
            self.status = HookStatus.ACTIVE
            start_time = datetime.now()
            
            # 執行 Hook 邏輯
            result = await self._execute_logic(context or {})
            
            # 執行回調
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(result)
                    else:
                        callback(result)
                except Exception as e:
                    logger.error(f"Hook {self.name} 回調執行失敗: {e}")
            
            # 更新統計
            execution_time = (datetime.now() - start_time).total_seconds()
            self.last_execution = start_time
            self.execution_count += 1
            self.status = HookStatus.INACTIVE
            
            result.update({
                "hook_name": self.name,
                "execution_time": execution_time,
                "timestamp": start_time.isoformat()
            })
            
            logger.debug(f"Hook {self.name} 執行成功 ({execution_time:.3f}s)")
            return result
            
        except Exception as e:
            self.error_count += 1
            self.status = HookStatus.ERROR
            logger.error(f"Hook {self.name} 執行失敗: {e}")
            
            return {
                "status": "error",
                "error": str(e),
                "hook_name": self.name,
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_logic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Hook 具體邏輯 - 子類實作"""
        raise NotImplementedError("子類必須實作 _execute_logic 方法")

class SystemHealthMonitorHook(KiroHook):
    """系統健康監控 Hook
    基於 .kiro/hooks/system-health-monitor.md
    """
    
    def __init__(self):
        super().__init__(
            name="system-health-monitor",
            description="監控 FinMind API 連接狀態、系統效能和服務可用性",
            trigger=HookTrigger.SCHEDULED,
            schedule="*/5 * * * *",  # 每5分鐘
            enabled=True
        )
        self.metrics = SystemHealthMetrics()
        self.thresholds = {
            "max_response_time": 5.0,  # 5秒 
            "max_error_rate": 0.1,     # 10%
            "min_success_rate": 0.9    # 90%
        }
    
    async def _execute_logic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """執行系統健康檢查"""
        health_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "components": {}
        }
        
        try:
            # 1. 檢查 FinMind API 連接
            finmind_status = await self._check_finmind_api()
            health_report["components"]["finmind_api"] = finmind_status
            
            # 2. 檢查系統回應時間
            response_time_status = await self._check_response_times()
            health_report["components"]["response_time"] = response_time_status
            
            # 3. 檢查錯誤率
            error_rate_status = await self._check_error_rates()
            health_report["components"]["error_rate"] = error_rate_status
            
            # 4. 檢查記憶體和CPU使用率 (模擬)
            resource_status = await self._check_system_resources()
            health_report["components"]["system_resources"] = resource_status
            
            # 5. 確定整體健康狀態
            component_statuses = [
                comp["status"] for comp in health_report["components"].values()
            ]
            
            if "critical" in component_statuses:
                health_report["overall_status"] = "critical"
            elif "warning" in component_statuses:
                health_report["overall_status"] = "warning"
            else:
                health_report["overall_status"] = "healthy"
            
            # 6. 生成建議
            health_report["recommendations"] = self._generate_recommendations(health_report)
            
            return {
                "status": "success",
                "data": health_report
            }
            
        except Exception as e:
            logger.error(f"系統健康檢查失敗: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": {
                    "overall_status": "unknown",
                    "error_details": str(e)
                }
            }
    
    async def _check_finmind_api(self) -> Dict[str, Any]:
        """檢查 FinMind API 狀態"""
        try:
            start_time = datetime.now()
            
            # 模擬 API 調用檢查
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.finmindtrade.com/api/v4/data",
                    params={"dataset": "TaiwanStockInfo", "data_id": "2330"},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    success = response.status == 200
                    
                    self.metrics.add_api_response(response_time, success)
                    
                    return {
                        "name": "FinMind API",
                        "status": "healthy" if success else "critical",
                        "response_time": response_time,
                        "status_code": response.status,
                        "last_check": start_time.isoformat()
                    }
                    
        except Exception as e:
            self.metrics.add_api_response(10.0, False)  # 記錄失敗
            return {
                "name": "FinMind API",
                "status": "critical",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _check_response_times(self) -> Dict[str, Any]:
        """檢查系統回應時間"""
        avg_response_time = self.metrics.get_average_response_time(5)
        
        if avg_response_time > self.thresholds["max_response_time"]:
            status = "critical"
        elif avg_response_time > self.thresholds["max_response_time"] * 0.7:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "name": "Response Time",
            "status": status,
            "average_response_time": round(avg_response_time, 3),
            "threshold": self.thresholds["max_response_time"],
            "sample_size": len(self.metrics.api_response_times)
        }
    
    async def _check_error_rates(self) -> Dict[str, Any]:
        """檢查錯誤率"""
        error_rate = self.metrics.get_error_rate(5)
        
        if error_rate > self.thresholds["max_error_rate"]:
            status = "critical"
        elif error_rate > self.thresholds["max_error_rate"] * 0.5:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "name": "Error Rate",
            "status": status,
            "error_rate": round(error_rate, 3),
            "threshold": self.thresholds["max_error_rate"],
            "total_errors": self.metrics.error_count,
            "total_requests": self.metrics.success_count + self.metrics.error_count
        }
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """檢查系統資源使用率 (模擬實作)"""
        # 實際環境中應該使用 psutil 或其他系統監控工具
        import random
        
        cpu_usage = random.uniform(10, 80)  # 模擬CPU使用率
        memory_usage = random.uniform(20, 90)  # 模擬記憶體使用率
        
        status = "healthy"
        if cpu_usage > 90 or memory_usage > 95:
            status = "critical"
        elif cpu_usage > 80 or memory_usage > 85:
            status = "warning"
        
        return {
            "name": "System Resources",
            "status": status,
            "cpu_usage": round(cpu_usage, 1),
            "memory_usage": round(memory_usage, 1),
            "thresholds": {
                "cpu_warning": 80,
                "cpu_critical": 90,
                "memory_warning": 85,
                "memory_critical": 95
            }
        }
    
    def _generate_recommendations(self, health_report: Dict[str, Any]) -> List[str]:
        """生成改善建議"""
        recommendations = []
        
        for component_name, component_data in health_report["components"].items():
            if component_data["status"] == "critical":
                if component_name == "finmind_api":
                    recommendations.append("FinMind API 連接異常，請檢查網絡連接和 API 配額")
                elif component_name == "response_time":
                    recommendations.append("系統回應時間過長，建議檢查資料庫性能和網絡延遲")
                elif component_name == "error_rate":
                    recommendations.append("錯誤率過高，請檢查日誌並修復相關問題")
                elif component_name == "system_resources":
                    recommendations.append("系統資源使用率過高，建議擴展資源或優化代碼")
            
            elif component_data["status"] == "warning":
                recommendations.append(f"{component_name} 狀態需要關注，建議進行預防性維護")
        
        if not recommendations:
            recommendations.append("系統運行正常，繼續保持監控")
        
        return recommendations

class APIQuotaMonitorHook(KiroHook):
    """API 配額監控 Hook
    基於 .kiro/hooks/api-quota-monitor.md
    """
    
    def __init__(self):
        super().__init__(
            name="api-quota-monitor",
            description="監控 API 配額使用狀況和使用者限制",
            trigger=HookTrigger.API_CALL,
            enabled=True
        )
        self.quota_usage = {}
        self.warning_thresholds = {
            "finmind_api": 0.8,  # 80% 警告
            "user_daily_limit": 0.9  # 90% 警告
        }
    
    async def _execute_logic(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """監控 API 配額使用"""
        api_name = context.get("api_name", "unknown")
        user_id = context.get("user_id")
        usage_info = context.get("usage_info", {})
        
        # 更新使用量記錄
        self._update_usage_tracking(api_name, user_id, usage_info)
        
        # 檢查是否超過警告閾值
        warnings = self._check_quota_warnings(api_name, user_id)
        
        quota_report = {
            "api_name": api_name,
            "user_id": user_id,
            "current_usage": usage_info,
            "warnings": warnings,
            "recommendations": self._generate_quota_recommendations(warnings)
        }
        
        return {
            "status": "success",
            "data": quota_report
        }
    
    def _update_usage_tracking(self, api_name: str, user_id: str, usage_info: Dict[str, Any]):
        """更新使用量追蹤"""
        today = datetime.now().date().isoformat()
        
        if api_name not in self.quota_usage:
            self.quota_usage[api_name] = {}
        
        if today not in self.quota_usage[api_name]:
            self.quota_usage[api_name][today] = {}
        
        if user_id not in self.quota_usage[api_name][today]:
            self.quota_usage[api_name][today][user_id] = {
                "requests": 0,
                "data_points": 0,
                "errors": 0
            }
        
        # 更新統計
        user_usage = self.quota_usage[api_name][today][user_id]
        user_usage["requests"] += usage_info.get("requests", 1)
        user_usage["data_points"] += usage_info.get("data_points", 0)
        user_usage["errors"] += usage_info.get("errors", 0)
    
    def _check_quota_warnings(self, api_name: str, user_id: str) -> List[Dict[str, Any]]:
        """檢查配額警告"""
        warnings = []
        today = datetime.now().date().isoformat()
        
        if (api_name in self.quota_usage and 
            today in self.quota_usage[api_name] and
            user_id in self.quota_usage[api_name][today]):
            
            user_usage = self.quota_usage[api_name][today][user_id]
            
            # 假設的用戶每日限制
            daily_limits = {
                "free": 10,
                "gold": 100,
                "diamond": 500
            }
            
            # 模擬用戶等級 (實際應該從用戶服務取得)
            user_tier = "free"  # 預設
            daily_limit = daily_limits.get(user_tier, 10)
            
            usage_rate = user_usage["requests"] / daily_limit
            
            if usage_rate >= self.warning_thresholds.get("user_daily_limit", 0.9):
                warnings.append({
                    "type": "user_limit_warning",
                    "message": f"用戶 {user_id} 接近每日限制",
                    "usage_rate": usage_rate,
                    "current_usage": user_usage["requests"],
                    "limit": daily_limit
                })
        
        return warnings
    
    def _generate_quota_recommendations(self, warnings: List[Dict[str, Any]]) -> List[str]:
        """生成配額建議"""
        recommendations = []
        
        for warning in warnings:
            if warning["type"] == "user_limit_warning":
                recommendations.append(
                    f"建議提醒用戶升級會員等級或優化 API 使用頻率"
                )
        
        if not recommendations:
            recommendations.append("配額使用狀況正常")
        
        return recommendations

class KiroHooksManager:
    """KIRO Hooks 管理器"""
    
    def __init__(self):
        self.hooks = {}
        self.scheduler_running = False
        self.scheduler_tasks = {}
        
        # 初始化所有 hooks
        self._initialize_hooks()
    
    def _initialize_hooks(self):
        """初始化所有 KIRO hooks"""
        # 1. 系統健康監控
        system_health_hook = SystemHealthMonitorHook()
        self.register_hook(system_health_hook)
        
        # 2. API 配額監控
        api_quota_hook = APIQuotaMonitorHook()
        self.register_hook(api_quota_hook)
        
        # TODO: 實作其他 hooks
        # 3. 數據品質檢查
        # 4. 對話串流監控
        # 5. 權限異常處理
        
        logger.info(f"已初始化 {len(self.hooks)} 個 KIRO hooks")
    
    def register_hook(self, hook: KiroHook):
        """註冊 Hook"""
        self.hooks[hook.name] = hook
        logger.info(f"已註冊 Hook: {hook.name}")
    
    async def execute_hook(self, hook_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """執行指定的 Hook"""
        if hook_name not in self.hooks:
            return {
                "status": "error",
                "error": f"Hook {hook_name} 不存在"
            }
        
        hook = self.hooks[hook_name]
        return await hook.execute(context)
    
    async def execute_hooks_by_trigger(self, trigger: HookTrigger, context: Dict[str, Any] = None):
        """根據觸發類型執行 Hooks"""
        results = {}
        
        for hook_name, hook in self.hooks.items():
            if hook.trigger == trigger and hook.enabled:
                result = await hook.execute(context)
                results[hook_name] = result
        
        return results
    
    async def start_scheduler(self):
        """啟動排程器"""
        if self.scheduler_running:
            logger.warning("排程器已在運行中")
            return
        
        self.scheduler_running = True
        logger.info("KIRO Hooks 排程器已啟動")
        
        # 為每個排程 Hook 建立任務
        for hook_name, hook in self.hooks.items():
            if hook.trigger == HookTrigger.SCHEDULED and hook.schedule:
                task = asyncio.create_task(self._schedule_hook(hook))
                self.scheduler_tasks[hook_name] = task
                logger.info(f"已排程 Hook: {hook_name} ({hook.schedule})")
    
    async def stop_scheduler(self):
        """停止排程器"""
        self.scheduler_running = False
        
        # 取消所有排程任務
        for hook_name, task in self.scheduler_tasks.items():
            task.cancel()
            logger.info(f"已取消排程 Hook: {hook_name}")
        
        self.scheduler_tasks.clear()
        logger.info("KIRO Hooks 排程器已停止")
    
    async def _schedule_hook(self, hook: KiroHook):
        """排程單個 Hook"""
        try:
            while self.scheduler_running:
                # 解析 cron 表達式 (簡化版本，實際應使用 cron 庫)
                if hook.schedule == "*/5 * * * *":  # 每5分鐘
                    await asyncio.sleep(300)  # 5分鐘 = 300秒
                else:
                    await asyncio.sleep(60)  # 預設1分鐘
                
                if self.scheduler_running:
                    await hook.execute()
                    
        except asyncio.CancelledError:
            logger.info(f"Hook {hook.name} 排程已取消")
        except Exception as e:
            logger.error(f"Hook {hook.name} 排程執行異常: {e}")
    
    def get_hooks_status(self) -> Dict[str, Any]:
        """取得所有 Hooks 狀態"""
        status_report = {
            "total_hooks": len(self.hooks),
            "scheduler_running": self.scheduler_running,
            "hooks": {}
        }
        
        for hook_name, hook in self.hooks.items():
            status_report["hooks"][hook_name] = {
                "name": hook.name,
                "description": hook.description,
                "trigger": hook.trigger.value,
                "enabled": hook.enabled,
                "status": hook.status.value,
                "execution_count": hook.execution_count,
                "error_count": hook.error_count,
                "last_execution": hook.last_execution.isoformat() if hook.last_execution else None
            }
        
        return status_report