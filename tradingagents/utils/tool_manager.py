#!/usr/bin/env python3
"""
統一工具管理器 (Unified Tool Manager)
天工 (TianGong) - 統一工具管理系統

此模組提供統一的工具管理機制，包含：
1. 工具註冊和發現
2. 工具生命週期管理
3. 工具狀態監控
4. 工具依賴關係管理
5. 工具性能優化
"""

import asyncio
import importlib
import inspect
import threading
import weakref
from typing import Dict, List, Optional, Any, Type, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import logging

# 配置日誌
logger = logging.getLogger(__name__)


class ToolStatus(Enum):
    """工具狀態"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"


class ToolType(Enum):
    """工具類型"""
    UTILITY = "utility"           # 通用工具
    CACHE = "cache"              # 緩存工具
    MONITOR = "monitor"          # 監控工具
    AUTH = "auth"                # 認證工具
    AI = "ai"                    # AI 相關工具
    PERFORMANCE = "performance"   # 性能工具
    INTEGRATION = "integration"   # 整合工具
    SYSTEM = "system"            # 系統工具


@dataclass
class ToolInfo:
    """工具信息"""
    tool_id: str
    tool_name: str
    tool_type: ToolType
    module_path: str
    class_name: Optional[str] = None
    description: str = ""
    version: str = "1.0.0"
    
    # 狀態信息
    status: ToolStatus = ToolStatus.UNINITIALIZED
    last_used: Optional[datetime] = None
    usage_count: int = 0
    error_count: int = 0
    
    # 依賴信息
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # 性能信息
    initialization_time: float = 0.0
    average_execution_time: float = 0.0
    memory_usage: float = 0.0
    
    # 配置信息
    lazy_load: bool = True
    singleton: bool = True
    auto_cleanup: bool = True
    
    # 時間信息
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ToolUsageStats:
    """工具使用統計"""
    tool_id: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    last_call_time: Optional[datetime] = None
    peak_memory_usage: float = 0.0


class ToolManager:
    """統一工具管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._tools_registry: Dict[str, ToolInfo] = {}
        self._tool_instances: Dict[str, Any] = {}
        self._tool_stats: Dict[str, ToolUsageStats] = {}
        self._executor = ThreadPoolExecutor(max_workers=5)
        self._cleanup_tasks: Dict[str, asyncio.Task] = {}
        
        # 工具模組映射
        self._tool_modules = {
            'ai_analysis_optimizer': {
                'module_path': 'tradingagents.utils.ai_analysis_optimizer',
                'tool_type': ToolType.AI,
                'description': 'AI 分析優化器',
                'dependencies': ['llm_client', 'smart_model_selector']
            },
            'auth': {
                'module_path': 'tradingagents.utils.auth',
                'tool_type': ToolType.AUTH,
                'description': '認證工具',
                'dependencies': []
            },
            'cache_manager': {
                'module_path': 'tradingagents.utils.cache_manager',
                'tool_type': ToolType.CACHE,
                'description': '緩存管理器',
                'dependencies': []
            },
            'emergency_controller': {
                'module_path': 'tradingagents.utils.emergency_controller',
                'tool_type': ToolType.SYSTEM,
                'description': '緊急控制器',
                'dependencies': ['system_monitor', 'logging_config']
            },
            'error_handler': {
                'module_path': 'tradingagents.utils.error_handler',
                'tool_type': ToolType.UTILITY,
                'description': '錯誤處理器',
                'dependencies': ['logging_config']
            },
            'integration_bridge': {
                'module_path': 'tradingagents.utils.integration_bridge',
                'tool_type': ToolType.INTEGRATION,
                'description': '整合橋接器',
                'dependencies': ['cache_manager', 'error_handler']
            },
            'llm_client': {
                'module_path': 'tradingagents.utils.llm_client',
                'tool_type': ToolType.AI,
                'description': 'LLM 客戶端',
                'dependencies': ['llm_cost_optimizer']
            },
            'llm_cost_optimizer': {
                'module_path': 'tradingagents.utils.llm_cost_optimizer',
                'tool_type': ToolType.AI,
                'description': 'LLM 成本優化器',
                'dependencies': []
            },
            'logging_config': {
                'module_path': 'tradingagents.utils.logging_config',
                'tool_type': ToolType.UTILITY,
                'description': '日誌配置器',
                'dependencies': [],
                'lazy_load': False  # 日誌需要立即初始化
            },
            'member_permission_bridge': {
                'module_path': 'tradingagents.utils.member_permission_bridge',
                'tool_type': ToolType.AUTH,
                'description': '會員權限橋接器',
                'dependencies': ['auth', 'user_context']
            },
            'middleware': {
                'module_path': 'tradingagents.utils.middleware',
                'tool_type': ToolType.SYSTEM,
                'description': '中間件',
                'dependencies': ['logging_config', 'performance_monitor']
            },
            'migration_manager': {
                'module_path': 'tradingagents.utils.migration_manager',
                'tool_type': ToolType.SYSTEM,
                'description': '遷移管理器',
                'dependencies': ['logging_config']
            },
            'performance_monitor': {
                'module_path': 'tradingagents.utils.performance_monitor',
                'tool_type': ToolType.PERFORMANCE,
                'description': '性能監控器',
                'dependencies': ['logging_config']
            },
            'resilience_manager': {
                'module_path': 'tradingagents.utils.resilience_manager',
                'tool_type': ToolType.SYSTEM,
                'description': '彈性管理器',
                'dependencies': ['error_handler', 'performance_monitor']
            },
            'smart_model_selector': {
                'module_path': 'tradingagents.utils.smart_model_selector',
                'tool_type': ToolType.AI,
                'description': '智能模型選擇器',
                'dependencies': ['llm_cost_optimizer']
            },
            'system_monitor': {
                'module_path': 'tradingagents.utils.system_monitor',
                'tool_type': ToolType.MONITOR,
                'description': '系統監控器',
                'dependencies': ['logging_config']
            },
            'user_context': {
                'module_path': 'tradingagents.utils.user_context',
                'tool_type': ToolType.UTILITY,
                'description': '用戶上下文',
                'dependencies': []
            },
            'user_feedback_system': {
                'module_path': 'tradingagents.utils.user_feedback_system',
                'tool_type': ToolType.UTILITY,
                'description': '用戶反饋系統',
                'dependencies': ['cache_manager', 'logging_config']
            }
        }
        
        # 初始化工具註冊表
        self._initialize_tool_registry()
        
        logger.info(f"工具管理器初始化完成，註冊了 {len(self._tools_registry)} 個工具")
    
    def _initialize_tool_registry(self):
        """初始化工具註冊表"""
        try:
            for tool_id, config in self._tool_modules.items():
                tool_info = ToolInfo(
                    tool_id=tool_id,
                    tool_name=tool_id.replace('_', ' ').title(),
                    tool_type=config['tool_type'],
                    module_path=config['module_path'],
                    description=config['description'],
                    dependencies=config.get('dependencies', []),
                    lazy_load=config.get('lazy_load', True),
                    singleton=config.get('singleton', True),
                    auto_cleanup=config.get('auto_cleanup', True)
                )
                
                self._tools_registry[tool_id] = tool_info
                self._tool_stats[tool_id] = ToolUsageStats(tool_id=tool_id)
                
                # 建立依賴關係
                for dep_id in tool_info.dependencies:
                    if dep_id in self._tools_registry:
                        self._tools_registry[dep_id].dependents.append(tool_id)
            
        except Exception as e:
            logger.error(f"工具註冊表初始化失敗: {str(e)}")
    
    # ==================== 工具註冊和發現 ====================
    
    def register_tool(self, tool_info: ToolInfo) -> bool:
        """註冊工具"""
        try:
            if tool_info.tool_id in self._tools_registry:
                logger.warning(f"工具 {tool_info.tool_id} 已存在，將覆蓋")
            
            self._tools_registry[tool_info.tool_id] = tool_info
            self._tool_stats[tool_info.tool_id] = ToolUsageStats(tool_id=tool_info.tool_id)
            
            logger.info(f"工具 {tool_info.tool_id} 註冊成功")
            return True
            
        except Exception as e:
            logger.error(f"註冊工具 {tool_info.tool_id} 失敗: {str(e)}")
            return False
    
    async def unregister_tool(self, tool_id: str) -> bool:
        """取消註冊工具"""
        try:
            if tool_id not in self._tools_registry:
                logger.warning(f"工具 {tool_id} 不存在")
                return False
            
            # 檢查是否有其他工具依賴此工具
            tool_info = self._tools_registry[tool_id]
            if tool_info.dependents:
                logger.error(f"無法取消註冊工具 {tool_id}，有其他工具依賴: {tool_info.dependents}")
                return False
            
            # 清理實例
            if tool_id in self._tool_instances:
                await self._cleanup_tool_instance(tool_id)
            
            # 移除註冊
            del self._tools_registry[tool_id]
            del self._tool_stats[tool_id]
            
            logger.info(f"工具 {tool_id} 取消註冊成功")
            return True
            
        except Exception as e:
            logger.error(f"取消註冊工具 {tool_id} 失敗: {str(e)}")
            return False
    
    def get_tool_info(self, tool_id: str) -> Optional[ToolInfo]:
        """獲取工具信息"""
        return self._tools_registry.get(tool_id)
    
    def list_tools(self, tool_type: Optional[ToolType] = None, status: Optional[ToolStatus] = None) -> List[ToolInfo]:
        """列出工具"""
        tools = list(self._tools_registry.values())
        
        if tool_type:
            tools = [t for t in tools if t.tool_type == tool_type]
        
        if status:
            tools = [t for t in tools if t.status == status]
        
        return tools
    
    # ==================== 工具實例管理 ====================
    
    async def get_tool(self, tool_id: str, **kwargs) -> Optional[Any]:
        """獲取工具實例"""
        try:
            if tool_id not in self._tools_registry:
                logger.error(f"工具 {tool_id} 未註冊")
                return None
            
            tool_info = self._tools_registry[tool_id]
            
            # 檢查工具狀態
            if tool_info.status == ToolStatus.DISABLED:
                logger.warning(f"工具 {tool_id} 已禁用")
                return None
            
            # 如果是單例且已存在實例，直接返回
            if tool_info.singleton and tool_id in self._tool_instances:
                instance = self._tool_instances[tool_id]
                if instance is not None:
                    await self._update_usage_stats(tool_id, success=True)
                    return instance
            
            # 初始化工具實例
            instance = await self._initialize_tool(tool_id, **kwargs)
            
            if instance is not None:
                if tool_info.singleton:
                    self._tool_instances[tool_id] = instance
                
                await self._update_usage_stats(tool_id, success=True)
                return instance
            else:
                await self._update_usage_stats(tool_id, success=False)
                return None
                
        except Exception as e:
            logger.error(f"獲取工具 {tool_id} 失敗: {str(e)}")
            await self._update_usage_stats(tool_id, success=False)
            return None
    
    async def _initialize_tool(self, tool_id: str, **kwargs) -> Optional[Any]:
        """初始化工具實例"""
        try:
            tool_info = self._tools_registry[tool_id]
            tool_info.status = ToolStatus.INITIALIZING
            
            start_time = datetime.now()
            
            # 首先初始化依賴工具
            for dep_id in tool_info.dependencies:
                dep_instance = await self.get_tool(dep_id)
                if dep_instance is None:
                    logger.error(f"工具 {tool_id} 的依賴 {dep_id} 初始化失敗")
                    tool_info.status = ToolStatus.ERROR
                    return None
            
            # 導入模組
            try:
                module = importlib.import_module(tool_info.module_path)
            except ImportError as e:
                logger.error(f"無法導入工具模組 {tool_info.module_path}: {str(e)}")
                tool_info.status = ToolStatus.ERROR
                return None
            
            # 查找工具類或函數
            instance = None
            
            # 嘗試查找類
            if tool_info.class_name:
                if hasattr(module, tool_info.class_name):
                    tool_class = getattr(module, tool_info.class_name)
                    instance = tool_class(**kwargs)
            else:
                # 自動查找合適的類
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and not name.startswith('_'):
                        # 優先選擇包含工具名稱的類
                        if tool_id.lower().replace('_', '') in name.lower():
                            try:
                                instance = obj(**kwargs)
                                tool_info.class_name = name
                                break
                            except Exception:
                                continue
                
                # 如果沒找到類，嘗試使用模組本身
                if instance is None:
                    instance = module
            
            if instance is not None:
                tool_info.status = ToolStatus.READY
                tool_info.initialization_time = (datetime.now() - start_time).total_seconds()
                tool_info.updated_at = datetime.now()
                
                # 設置自動清理
                if tool_info.auto_cleanup:
                    await self._schedule_cleanup(tool_id)
                
                logger.info(f"工具 {tool_id} 初始化成功，耗時 {tool_info.initialization_time:.3f}s")
                return instance
            else:
                tool_info.status = ToolStatus.ERROR
                logger.error(f"工具 {tool_id} 初始化失敗：無法創建實例")
                return None
                
        except Exception as e:
            tool_info.status = ToolStatus.ERROR
            logger.error(f"初始化工具 {tool_id} 失敗: {str(e)}")
            return None
    
    async def _schedule_cleanup(self, tool_id: str, delay: int = 300):
        """調度工具清理"""
        try:
            # 取消之前的清理任務
            if tool_id in self._cleanup_tasks:
                self._cleanup_tasks[tool_id].cancel()
            
            # 創建新的清理任務
            async def cleanup_after_delay():
                await asyncio.sleep(delay)
                await self._cleanup_tool_instance(tool_id)
            
            task = asyncio.create_task(cleanup_after_delay())
            self._cleanup_tasks[tool_id] = task
            
        except Exception as e:
            logger.error(f"調度工具 {tool_id} 清理失敗: {str(e)}")
    
    async def _cleanup_tool_instance(self, tool_id: str):
        """清理工具實例"""
        try:
            if tool_id in self._tool_instances:
                instance = self._tool_instances[tool_id]
                
                # 如果實例有清理方法，調用它
                if hasattr(instance, 'cleanup'):
                    try:
                        if asyncio.iscoroutinefunction(instance.cleanup):
                            await instance.cleanup()
                        else:
                            instance.cleanup()
                    except Exception as e:
                        logger.warning(f"工具 {tool_id} 清理方法執行失敗: {str(e)}")
                
                # 移除實例
                del self._tool_instances[tool_id]
                
                # 更新狀態
                if tool_id in self._tools_registry:
                    self._tools_registry[tool_id].status = ToolStatus.UNINITIALIZED
                
                logger.info(f"工具 {tool_id} 實例已清理")
                
        except Exception as e:
            logger.error(f"清理工具 {tool_id} 實例失敗: {str(e)}")
    
    # ==================== 工具狀態管理 ====================
    
    async def enable_tool(self, tool_id: str) -> bool:
        """啟用工具"""
        try:
            if tool_id not in self._tools_registry:
                logger.error(f"工具 {tool_id} 未註冊")
                return False
            
            tool_info = self._tools_registry[tool_id]
            if tool_info.status != ToolStatus.DISABLED:
                logger.warning(f"工具 {tool_id} 當前狀態為 {tool_info.status}，無需啟用")
                return True
            
            tool_info.status = ToolStatus.UNINITIALIZED
            tool_info.updated_at = datetime.now()
            
            logger.info(f"工具 {tool_id} 已啟用")
            return True
            
        except Exception as e:
            logger.error(f"啟用工具 {tool_id} 失敗: {str(e)}")
            return False
    
    async def disable_tool(self, tool_id: str) -> bool:
        """禁用工具"""
        try:
            if tool_id not in self._tools_registry:
                logger.error(f"工具 {tool_id} 未註冊")
                return False
            
            tool_info = self._tools_registry[tool_id]
            
            # 檢查依賴
            if tool_info.dependents:
                logger.error(f"無法禁用工具 {tool_id}，有其他工具依賴: {tool_info.dependents}")
                return False
            
            # 清理實例
            if tool_id in self._tool_instances:
                await self._cleanup_tool_instance(tool_id)
            
            tool_info.status = ToolStatus.DISABLED
            tool_info.updated_at = datetime.now()
            
            logger.info(f"工具 {tool_id} 已禁用")
            return True
            
        except Exception as e:
            logger.error(f"禁用工具 {tool_id} 失敗: {str(e)}")
            return False
    
    async def restart_tool(self, tool_id: str) -> bool:
        """重啟工具"""
        try:
            if tool_id not in self._tools_registry:
                logger.error(f"工具 {tool_id} 未註冊")
                return False
            
            # 清理現有實例
            if tool_id in self._tool_instances:
                await self._cleanup_tool_instance(tool_id)
            
            # 重置狀態
            tool_info = self._tools_registry[tool_id]
            tool_info.status = ToolStatus.UNINITIALIZED
            tool_info.error_count = 0
            tool_info.updated_at = datetime.now()
            
            logger.info(f"工具 {tool_id} 已重啟")
            return True
            
        except Exception as e:
            logger.error(f"重啟工具 {tool_id} 失敗: {str(e)}")
            return False
    
    # ==================== 統計和監控 ====================
    
    async def _update_usage_stats(self, tool_id: str, success: bool, execution_time: float = 0.0):
        """更新使用統計"""
        try:
            if tool_id not in self._tool_stats:
                return
            
            stats = self._tool_stats[tool_id]
            stats.total_calls += 1
            stats.last_call_time = datetime.now()
            
            if success:
                stats.successful_calls += 1
            else:
                stats.failed_calls += 1
                if tool_id in self._tools_registry:
                    self._tools_registry[tool_id].error_count += 1
            
            if execution_time > 0:
                stats.total_execution_time += execution_time
                stats.average_execution_time = stats.total_execution_time / stats.total_calls
            
            # 更新工具信息
            if tool_id in self._tools_registry:
                tool_info = self._tools_registry[tool_id]
                tool_info.usage_count = stats.total_calls
                tool_info.last_used = stats.last_call_time
                tool_info.average_execution_time = stats.average_execution_time
                
        except Exception as e:
            logger.error(f"更新工具 {tool_id} 使用統計失敗: {str(e)}")
    
    def get_tool_stats(self, tool_id: str) -> Optional[ToolUsageStats]:
        """獲取工具使用統計"""
        return self._tool_stats.get(tool_id)
    
    def get_all_stats(self) -> Dict[str, ToolUsageStats]:
        """獲取所有工具使用統計"""
        return self._tool_stats.copy()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """獲取系統統計"""
        try:
            total_tools = len(self._tools_registry)
            ready_tools = len([t for t in self._tools_registry.values() if t.status == ToolStatus.READY])
            error_tools = len([t for t in self._tools_registry.values() if t.status == ToolStatus.ERROR])
            disabled_tools = len([t for t in self._tools_registry.values() if t.status == ToolStatus.DISABLED])
            
            total_calls = sum(stats.total_calls for stats in self._tool_stats.values())
            successful_calls = sum(stats.successful_calls for stats in self._tool_stats.values())
            failed_calls = sum(stats.failed_calls for stats in self._tool_stats.values())
            
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 100.0
            
            return {
                'total_tools': total_tools,
                'ready_tools': ready_tools,
                'error_tools': error_tools,
                'disabled_tools': disabled_tools,
                'active_instances': len(self._tool_instances),
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'success_rate': success_rate,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"獲取系統統計失敗: {str(e)}")
            return {}
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self, tool_ids: Optional[List[str]] = None) -> Dict[str, Dict[str, Any]]:
        """健康檢查"""
        try:
            if tool_ids is None:
                tool_ids = list(self._tools_registry.keys())
            
            results = {}
            
            for tool_id in tool_ids:
                if tool_id not in self._tools_registry:
                    results[tool_id] = {
                        'status': 'not_found',
                        'message': '工具未註冊',
                        'checked_at': datetime.now()
                    }
                    continue
                
                tool_info = self._tools_registry[tool_id]
                
                try:
                    # 基本狀態檢查
                    if tool_info.status == ToolStatus.DISABLED:
                        health_status = 'disabled'
                        message = '工具已禁用'
                    elif tool_info.status == ToolStatus.ERROR:
                        health_status = 'error'
                        message = f'工具錯誤，錯誤次數: {tool_info.error_count}'
                    elif tool_info.status == ToolStatus.READY:
                        health_status = 'healthy'
                        message = '工具運行正常'
                    else:
                        health_status = 'unknown'
                        message = f'工具狀態: {tool_info.status}'
                    
                    # 性能檢查
                    stats = self._tool_stats.get(tool_id)
                    performance_info = {}
                    if stats:
                        performance_info = {
                            'total_calls': stats.total_calls,
                            'success_rate': (stats.successful_calls / stats.total_calls * 100) if stats.total_calls > 0 else 100.0,
                            'average_execution_time': stats.average_execution_time,
                            'last_call': stats.last_call_time
                        }
                    
                    results[tool_id] = {
                        'status': health_status,
                        'message': message,
                        'tool_type': tool_info.tool_type.value,
                        'dependencies': tool_info.dependencies,
                        'performance': performance_info,
                        'checked_at': datetime.now()
                    }
                    
                except Exception as e:
                    results[tool_id] = {
                        'status': 'check_failed',
                        'message': f'健康檢查失敗: {str(e)}',
                        'checked_at': datetime.now()
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {str(e)}")
            return {}
    
    # ==================== 清理和關閉 ====================
    
    async def cleanup_all(self):
        """清理所有工具實例"""
        try:
            # 取消所有清理任務
            for task in self._cleanup_tasks.values():
                task.cancel()
            self._cleanup_tasks.clear()
            
            # 清理所有實例
            for tool_id in list(self._tool_instances.keys()):
                await self._cleanup_tool_instance(tool_id)
            
            # 關閉執行器
            self._executor.shutdown(wait=True)
            
            logger.info("所有工具實例已清理")
            
        except Exception as e:
            logger.error(f"清理所有工具實例失敗: {str(e)}")
    
    def __del__(self):
        """析構函數"""
        try:
            # 嘗試清理資源
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=False)
        except Exception:
            pass


# 全局工具管理器實例
_tool_manager = None


def get_tool_manager() -> ToolManager:
    """獲取工具管理器實例"""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager


async def get_tool(tool_id: str, **kwargs) -> Optional[Any]:
    """便捷函數：獲取工具實例"""
    manager = get_tool_manager()
    return await manager.get_tool(tool_id, **kwargs)


async def cleanup_tools():
    """便捷函數：清理所有工具"""
    global _tool_manager
    if _tool_manager is not None:
        await _tool_manager.cleanup_all()
        _tool_manager = None