#!/usr/bin/env python3
"""
服務協調器服務 (Service Coordinator Service)
天工 (TianGong) - 服務協調器業務邏輯

此模組提供服務協調器的核心業務邏輯，包含：
1. 服務註冊和管理
2. 任務協調和調度
3. 工作流管理
4. 服務監控和健康檢查
5. 統一的服務調用機制
6. 工具管理整合
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
import importlib
import inspect

from ..models.service_coordinator import (
    ServiceInfo, ServiceRegistry, ServiceCommand, ServiceCommandResult,
    TaskDefinition, TaskExecution, WorkflowDefinition, WorkflowExecution,
    CoordinatorConfiguration, CoordinatorStatistics, CoordinatorHealth,
    ServiceQuery, TaskQuery, WorkflowQuery, CoordinatorDashboard,
    ServiceStatus, ServiceType, TaskStatus, TaskPriority, CoordinationStrategy
)
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error
from ...utils.cache_manager import CacheManager
from ...utils.tool_manager import get_tool_manager, ToolManager, ToolStatus, ToolType

# 配置日誌
api_logger = get_api_logger("service_coordinator_service")
security_logger = get_security_logger("service_coordinator_service")


class ServiceCoordinatorService:
    """服務協調器服務類"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # 整合工具管理器
        self.tool_manager = get_tool_manager()
        
        # 服務註冊表
        self._service_registry: Dict[str, ServiceInfo] = {}
        
        # 任務執行記錄
        self._task_executions: Dict[str, TaskExecution] = {}
        
        # 工作流執行記錄
        self._workflow_executions: Dict[str, WorkflowExecution] = {}
        
        # 協調器配置
        self._coordinator_config = CoordinatorConfiguration()
        
        # 服務模組映射
        self._service_modules = {
            'payment_service': 'tradingagents.services.payment_service',
            'user_experience_service': 'tradingagents.services.user_experience_service',
            'international_market_service': 'tradingagents.services.international_market_service',
            'upgrade_conversion_service': 'tradingagents.services.upgrade_conversion_service',
            'subscription_service': 'tradingagents.services.subscription_service',
            'membership_service': 'tradingagents.services.membership_service',
            'ab_testing_service': 'tradingagents.services.ab_testing_service',
            'pricing_strategy_service': 'tradingagents.services.pricing_strategy_service'
        }
        
        # 初始化服務註冊表
        self._initialize_service_registry()
    
    def _initialize_service_registry(self):
        """初始化服務註冊表"""
        try:
            # 註冊服務模組
            for service_id, module_path in self._service_modules.items():
                try:
                    module = importlib.import_module(module_path)
                    service_info = ServiceInfo(
                        service_id=service_id,
                        service_name=service_id.replace('_', ' ').title(),
                        service_type=ServiceType.API,
                        version="1.0.0",
                        status=ServiceStatus.RUNNING,
                        health_status="healthy",
                        last_health_check=datetime.now(),
                        endpoint=f"/api/{service_id.replace('_service', '')}",
                        config={},
                        dependencies=[],
                        dependents=[],
                        started_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    self._service_registry[service_id] = service_info
                    
                except ImportError as e:
                    api_logger.warning(f"無法導入服務模組 {module_path}: {str(e)}")
                    # 創建錯誤狀態的服務信息
                    service_info = ServiceInfo(
                        service_id=service_id,
                        service_name=service_id.replace('_', ' ').title(),
                        service_type=ServiceType.API,
                        version="1.0.0",
                        status=ServiceStatus.ERROR,
                        health_status="error",
                        last_health_check=datetime.now(),
                        config={},
                        dependencies=[],
                        dependents=[],
                        updated_at=datetime.now()
                    )
                    self._service_registry[service_id] = service_info
            
            # 整合工具管理器中的工具作為服務
            self._integrate_tools_as_services()
            
            api_logger.info(f"服務註冊表初始化完成，註冊了 {len(self._service_registry)} 個服務")
            
        except Exception as e:
            api_logger.error(f"服務註冊表初始化失敗: {str(e)}")
    
    def _integrate_tools_as_services(self):
        """將工具管理器中的工具整合為服務"""
        try:
            tools = self.tool_manager.list_tools()
            
            for tool_info in tools:
                # 將工具映射為服務類型
                service_type_mapping = {
                    ToolType.UTILITY: ServiceType.EXTERNAL,
                    ToolType.CACHE: ServiceType.CACHE,
                    ToolType.MONITOR: ServiceType.EXTERNAL,
                    ToolType.AUTH: ServiceType.EXTERNAL,
                    ToolType.AI: ServiceType.AI_ANALYSIS,
                    ToolType.PERFORMANCE: ServiceType.EXTERNAL,
                    ToolType.INTEGRATION: ServiceType.EXTERNAL,
                    ToolType.SYSTEM: ServiceType.EXTERNAL
                }
                
                # 將工具狀態映射為服務狀態
                status_mapping = {
                    ToolStatus.UNINITIALIZED: ServiceStatus.STOPPED,
                    ToolStatus.INITIALIZING: ServiceStatus.STARTING,
                    ToolStatus.READY: ServiceStatus.RUNNING,
                    ToolStatus.BUSY: ServiceStatus.RUNNING,
                    ToolStatus.ERROR: ServiceStatus.ERROR,
                    ToolStatus.DISABLED: ServiceStatus.MAINTENANCE
                }
                
                service_info = ServiceInfo(
                    service_id=f"tool_{tool_info.tool_id}",
                    service_name=f"Tool: {tool_info.tool_name}",
                    service_type=service_type_mapping.get(tool_info.tool_type, ServiceType.EXTERNAL),
                    version=tool_info.version,
                    status=status_mapping.get(tool_info.status, ServiceStatus.STOPPED),
                    health_status="healthy" if tool_info.status == ToolStatus.READY else "unknown",
                    last_health_check=datetime.now(),
                    config={"tool_type": tool_info.tool_type.value},
                    dependencies=[f"tool_{dep}" for dep in tool_info.dependencies],
                    dependents=[f"tool_{dep}" for dep in tool_info.dependents],
                    cpu_usage=0.0,
                    memory_usage=tool_info.memory_usage,
                    request_count=tool_info.usage_count,
                    error_count=tool_info.error_count,
                    started_at=tool_info.created_at,
                    updated_at=tool_info.updated_at
                )
                
                self._service_registry[f"tool_{tool_info.tool_id}"] = service_info
                
        except Exception as e:
            api_logger.error(f"整合工具為服務失敗: {str(e)}")
    
    # ==================== 服務管理 ====================
    
    async def get_service_registry(self, query: ServiceQuery) -> ServiceRegistry:
        """獲取服務註冊表"""
        try:
            # 更新工具狀態
            await self._update_tool_services_status()
            
            services = list(self._service_registry.values())
            
            # 應用篩選條件
            if query.service_types:
                services = [s for s in services if s.service_type in query.service_types]
            
            if query.statuses:
                services = [s for s in services if s.status in query.statuses]
            
            if query.health_status:
                services = [s for s in services if s.health_status == query.health_status]
            
            if query.keyword:
                keyword = query.keyword.lower()
                services = [s for s in services if 
                          keyword in s.service_name.lower() or 
                          keyword in s.service_id.lower()]
            
            # 應用限制
            if query.limit:
                services = services[:query.limit]
            
            # 統計信息
            total_services = len(self._service_registry)
            running_services = len([s for s in self._service_registry.values() if s.status == ServiceStatus.RUNNING])
            error_services = len([s for s in self._service_registry.values() if s.status == ServiceStatus.ERROR])
            
            return ServiceRegistry(
                services=services,
                total_services=total_services,
                running_services=running_services,
                error_services=error_services,
                last_updated=datetime.now()
            )
            
        except Exception as e:
            api_logger.error(f"獲取服務註冊表失敗: {str(e)}")
            raise
    
    async def _update_tool_services_status(self):
        """更新工具服務狀態"""
        try:
            tools = self.tool_manager.list_tools()
            
            for tool_info in tools:
                service_id = f"tool_{tool_info.tool_id}"
                if service_id in self._service_registry:
                    service_info = self._service_registry[service_id]
                    
                    # 更新狀態
                    status_mapping = {
                        ToolStatus.UNINITIALIZED: ServiceStatus.STOPPED,
                        ToolStatus.INITIALIZING: ServiceStatus.STARTING,
                        ToolStatus.READY: ServiceStatus.RUNNING,
                        ToolStatus.BUSY: ServiceStatus.RUNNING,
                        ToolStatus.ERROR: ServiceStatus.ERROR,
                        ToolStatus.DISABLED: ServiceStatus.MAINTENANCE
                    }
                    
                    service_info.status = status_mapping.get(tool_info.status, ServiceStatus.STOPPED)
                    service_info.health_status = "healthy" if tool_info.status == ToolStatus.READY else "unknown"
                    service_info.memory_usage = tool_info.memory_usage
                    service_info.request_count = tool_info.usage_count
                    service_info.error_count = tool_info.error_count
                    service_info.updated_at = tool_info.updated_at
                    
        except Exception as e:
            api_logger.error(f"更新工具服務狀態失敗: {str(e)}")
    
    async def get_service_info(self, service_id: str) -> Optional[ServiceInfo]:
        """獲取服務詳情"""
        try:
            # 如果是工具服務，更新狀態
            if service_id.startswith("tool_"):
                await self._update_tool_services_status()
            
            return self._service_registry.get(service_id)
            
        except Exception as e:
            api_logger.error(f"獲取服務詳情失敗: {str(e)}")
            raise
    
    async def execute_service_command(self, service_id: str, command: ServiceCommand) -> ServiceCommandResult:
        """執行服務命令"""
        try:
            start_time = datetime.now()
            
            service_info = self._service_registry.get(service_id)
            if not service_info:
                return ServiceCommandResult(
                    service_id=service_id,
                    command=command.command,
                    success=False,
                    message="服務不存在",
                    execution_time=0.0,
                    executed_at=start_time
                )
            
            # 如果是工具服務，使用工具管理器執行命令
            if service_id.startswith("tool_"):
                tool_id = service_id.replace("tool_", "")
                return await self._execute_tool_command(tool_id, command, start_time)
            
            # 模擬普通服務命令執行
            await asyncio.sleep(0.1)  # 模擬執行時間
            
            success = True
            message = f"命令 {command.command} 執行成功"
            
            # 更新服務狀態
            if command.command == "start":
                service_info.status = ServiceStatus.RUNNING
                service_info.health_status = "healthy"
                service_info.started_at = datetime.now()
            elif command.command == "stop":
                service_info.status = ServiceStatus.STOPPED
                service_info.health_status = "stopped"
            elif command.command == "restart":
                service_info.status = ServiceStatus.RUNNING
                service_info.health_status = "healthy"
                service_info.started_at = datetime.now()
            elif command.command == "reload":
                # 重新加載配置
                pass
            else:
                success = False
                message = f"不支持的命令: {command.command}"
            
            service_info.updated_at = datetime.now()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ServiceCommandResult(
                service_id=service_id,
                command=command.command,
                success=success,
                message=message,
                execution_time=execution_time,
                executed_at=start_time,
                details=command.parameters
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            api_logger.error(f"執行服務命令失敗: {str(e)}")
            
            return ServiceCommandResult(
                service_id=service_id,
                command=command.command,
                success=False,
                message=f"命令執行失敗: {str(e)}",
                execution_time=execution_time,
                executed_at=start_time
            )
    
    async def _execute_tool_command(self, tool_id: str, command: ServiceCommand, start_time: datetime) -> ServiceCommandResult:
        """執行工具命令"""
        try:
            success = False
            message = ""
            
            if command.command == "start" or command.command == "enable":
                success = await self.tool_manager.enable_tool(tool_id)
                message = "工具啟用成功" if success else "工具啟用失敗"
                
            elif command.command == "stop" or command.command == "disable":
                success = await self.tool_manager.disable_tool(tool_id)
                message = "工具禁用成功" if success else "工具禁用失敗"
                
            elif command.command == "restart":
                success = await self.tool_manager.restart_tool(tool_id)
                message = "工具重啟成功" if success else "工具重啟失敗"
                
            elif command.command == "health_check":
                health_results = await self.tool_manager.health_check([tool_id])
                health_result = health_results.get(tool_id, {})
                success = health_result.get('status') in ['healthy', 'ready']
                message = health_result.get('message', '健康檢查完成')
                
            else:
                message = f"不支持的工具命令: {command.command}"
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ServiceCommandResult(
                service_id=f"tool_{tool_id}",
                command=command.command,
                success=success,
                message=message,
                execution_time=execution_time,
                executed_at=start_time,
                details=command.parameters
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return ServiceCommandResult(
                service_id=f"tool_{tool_id}",
                command=command.command,
                success=False,
                message=f"工具命令執行失敗: {str(e)}",
                execution_time=execution_time,
                executed_at=start_time
            )
    
    async def run_services_health_check(self, service_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """執行服務健康檢查"""
        try:
            if service_ids is None:
                service_ids = list(self._service_registry.keys())
            
            results = []
            tool_ids = []
            regular_service_ids = []
            
            # 分離工具服務和普通服務
            for service_id in service_ids:
                if service_id.startswith("tool_"):
                    tool_ids.append(service_id.replace("tool_", ""))
                else:
                    regular_service_ids.append(service_id)
            
            # 執行工具健康檢查
            if tool_ids:
                tool_health_results = await self.tool_manager.health_check(tool_ids)
                for tool_id, health_info in tool_health_results.items():
                    results.append({
                        "service_id": f"tool_{tool_id}",
                        "service_type": "tool",
                        "status": health_info.get("status", "unknown"),
                        "message": health_info.get("message", ""),
                        "checked_at": health_info.get("checked_at", datetime.now()),
                        "performance": health_info.get("performance", {}),
                        "tool_type": health_info.get("tool_type", "unknown")
                    })
            
            # 執行普通服務健康檢查
            for service_id in regular_service_ids:
                service_info = self._service_registry.get(service_id)
                if not service_info:
                    results.append({
                        "service_id": service_id,
                        "service_type": "service",
                        "status": "not_found",
                        "message": "服務不存在",
                        "checked_at": datetime.now()
                    })
                    continue
                
                # 執行健康檢查
                try:
                    # 模擬健康檢查
                    await asyncio.sleep(0.05)
                    
                    if service_info.status == ServiceStatus.RUNNING:
                        health_status = "healthy"
                        message = "服務運行正常"
                    elif service_info.status == ServiceStatus.ERROR:
                        health_status = "error"
                        message = "服務運行異常"
                    else:
                        health_status = "stopped"
                        message = "服務已停止"
                    
                    # 更新健康檢查時間
                    service_info.health_status = health_status
                    service_info.last_health_check = datetime.now()
                    
                    results.append({
                        "service_id": service_id,
                        "service_type": "service",
                        "status": health_status,
                        "message": message,
                        "checked_at": datetime.now(),
                        "response_time": 0.05
                    })
                    
                except Exception as e:
                    service_info.health_status = "error"
                    service_info.last_health_check = datetime.now()
                    
                    results.append({
                        "service_id": service_id,
                        "service_type": "service",
                        "status": "error",
                        "message": f"健康檢查失敗: {str(e)}",
                        "checked_at": datetime.now()
                    })
            
            return results
            
        except Exception as e:
            api_logger.error(f"服務健康檢查失敗: {str(e)}")
            raise
    
    # ==================== 工具管理整合 ====================
    
    async def get_tool(self, tool_id: str, **kwargs) -> Optional[Any]:
        """獲取工具實例（通過工具管理器）"""
        try:
            return await self.tool_manager.get_tool(tool_id, **kwargs)
        except Exception as e:
            api_logger.error(f"獲取工具 {tool_id} 失敗: {str(e)}")
            return None
    
    async def get_tool_stats(self) -> Dict[str, Any]:
        """獲取工具統計信息"""
        try:
            return self.tool_manager.get_system_stats()
        except Exception as e:
            api_logger.error(f"獲取工具統計信息失敗: {str(e)}")
            return {}
    
    async def cleanup_tools(self):
        """清理工具實例"""
        try:
            await self.tool_manager.cleanup_all()
        except Exception as e:
            api_logger.error(f"清理工具實例失敗: {str(e)}")
    
    # ==================== 統計和監控 ====================
    
    async def get_coordinator_statistics(self) -> CoordinatorStatistics:
        """獲取協調器統計信息"""
        try:
            # 服務統計
            total_services = len(self._service_registry)
            running_services = len([s for s in self._service_registry.values() if s.status == ServiceStatus.RUNNING])
            error_services = len([s for s in self._service_registry.values() if s.status == ServiceStatus.ERROR])
            
            # 任務統計
            total_tasks = len(self._task_executions)
            pending_tasks = len([t for t in self._task_executions.values() if t.status == TaskStatus.PENDING])
            running_tasks = len([t for t in self._task_executions.values() if t.status == TaskStatus.RUNNING])
            completed_tasks = len([t for t in self._task_executions.values() if t.status == TaskStatus.COMPLETED])
            failed_tasks = len([t for t in self._task_executions.values() if t.status == TaskStatus.FAILED])
            
            # 工作流統計
            total_workflows = len(self._workflow_executions)
            active_workflows = len([w for w in self._workflow_executions.values() if w.status == TaskStatus.RUNNING])
            completed_workflows = len([w for w in self._workflow_executions.values() if w.status == TaskStatus.COMPLETED])
            failed_workflows = len([w for w in self._workflow_executions.values() if w.status == TaskStatus.FAILED])
            
            # 性能統計
            completed_task_durations = [t.duration for t in self._task_executions.values() if t.duration is not None]
            average_task_duration = sum(completed_task_durations) / len(completed_task_durations) if completed_task_durations else 0.0
            
            completed_workflow_durations = [w.duration for w in self._workflow_executions.values() if w.duration is not None]
            average_workflow_duration = sum(completed_workflow_durations) / len(completed_workflow_durations) if completed_workflow_durations else 0.0
            
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 100.0
            
            # 整合工具統計
            tool_stats = await self.get_tool_stats()
            
            return CoordinatorStatistics(
                total_services=total_services,
                running_services=running_services,
                error_services=error_services,
                total_tasks=total_tasks,
                pending_tasks=pending_tasks,
                running_tasks=running_tasks,
                completed_tasks=completed_tasks,
                failed_tasks=failed_tasks,
                total_workflows=total_workflows,
                active_workflows=active_workflows,
                completed_workflows=completed_workflows,
                failed_workflows=failed_workflows,
                average_task_duration=average_task_duration,
                average_workflow_duration=average_workflow_duration,
                success_rate=success_rate,
                cpu_usage=0.0,  # 模擬值
                memory_usage=0.0,  # 模擬值
                uptime=int((datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            api_logger.error(f"獲取協調器統計信息失敗: {str(e)}")
            raise
    
    async def get_coordinator_health(self) -> CoordinatorHealth:
        """獲取協調器健康狀態"""
        try:
            # 檢查各組件狀態
            overall_status = "healthy"
            coordinator_status = "healthy"
            scheduler_status = "healthy"
            service_registry_status = "healthy"
            task_queue_status = "healthy"
            workflow_engine_status = "healthy"
            
            # 執行健康檢查
            health_checks = []
            
            # 服務註冊表檢查
            health_checks.append({
                "component": "service_registry",
                "status": service_registry_status,
                "message": f"已註冊 {len(self._service_registry)} 個服務",
                "checked_at": datetime.now()
            })
            
            # 任務隊列檢查
            health_checks.append({
                "component": "task_queue",
                "status": task_queue_status,
                "message": f"當前有 {len(self._task_executions)} 個任務",
                "checked_at": datetime.now()
            })
            
            # 工作流引擎檢查
            health_checks.append({
                "component": "workflow_engine",
                "status": workflow_engine_status,
                "message": f"當前有 {len(self._workflow_executions)} 個工作流",
                "checked_at": datetime.now()
            })
            
            # 工具管理器檢查
            tool_stats = await self.get_tool_stats()
            tool_manager_status = "healthy" if tool_stats.get('error_tools', 0) == 0 else "warning"
            health_checks.append({
                "component": "tool_manager",
                "status": tool_manager_status,
                "message": f"管理 {tool_stats.get('total_tools', 0)} 個工具，{tool_stats.get('ready_tools', 0)} 個就緒",
                "checked_at": datetime.now()
            })
            
            return CoordinatorHealth(
                overall_status=overall_status,
                coordinator_status=coordinator_status,
                scheduler_status=scheduler_status,
                service_registry_status=service_registry_status,
                task_queue_status=task_queue_status,
                workflow_engine_status=workflow_engine_status,
                health_checks=health_checks,
                last_check=datetime.now(),
                uptime=int((datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())
            )
            
        except Exception as e:
            api_logger.error(f"獲取協調器健康狀態失敗: {str(e)}")
            raise
    
    # ==================== 批量操作 ====================
    
    async def bulk_service_command(self, service_ids: List[str], command: ServiceCommand) -> List[ServiceCommandResult]:
        """批量執行服務命令"""
        try:
            tasks = []
            for service_id in service_ids:
                task = self.execute_service_command(service_id, command)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理異常結果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(ServiceCommandResult(
                        service_id=service_ids[i],
                        command=command.command,
                        success=False,
                        message=f"執行失敗: {str(result)}",
                        execution_time=0.0,
                        executed_at=datetime.now()
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            api_logger.error(f"批量執行服務命令失敗: {str(e)}")
            raise