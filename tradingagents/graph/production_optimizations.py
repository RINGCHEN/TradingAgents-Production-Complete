#!/usr/bin/env python3
"""
工作流引擎生產環境優化 (Production Optimizations)
天工 (TianGong) - TradingAgentsGraph生產級別優化組件

此模組提供TradingAgentsGraph的生產環境優化功能，包含：
1. 高性能並發處理優化
2. 智能資源管理和回收
3. 容錯和自動恢復機制
4. 細粒度監控和指標
5. 內存優化和垃圾回收
6. Taiwan市場特定優化
"""

import asyncio
import time
import gc
import psutil
import logging
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict
import weakref
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
# uvloop 僅在 Unix 系統上可用
try:
    import uvloop
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False

from ..utils.logging_config import get_system_logger, get_analysis_logger, log_performance
from ..utils.error_handler import handle_error, ErrorCategory, ErrorSeverity

# 配置日誌
system_logger = get_system_logger("production_optimizations")
analysis_logger = get_analysis_logger("production_optimizations")

class ResourceType(Enum):
    """資源類型"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"
    AI_MODEL = "ai_model"

class OptimizationLevel(Enum):
    """優化級別"""
    BASIC = "basic"          # 基本優化
    BALANCED = "balanced"    # 平衡優化
    AGGRESSIVE = "aggressive" # 激進優化

@dataclass
class PerformanceMetrics:
    """性能指標"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 系統資源
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_mb: float = 0.0
    
    # 會話統計
    active_sessions: int = 0
    completed_sessions: int = 0
    failed_sessions: int = 0
    
    # 性能統計
    avg_session_time: float = 0.0
    avg_analyst_time: float = 0.0
    queue_depth: int = 0
    
    # 錯誤統計
    error_rate: float = 0.0
    recovery_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'system': {
                'cpu_percent': self.cpu_percent,
                'memory_percent': self.memory_percent,
                'memory_mb': self.memory_mb
            },
            'sessions': {
                'active': self.active_sessions,
                'completed': self.completed_sessions,
                'failed': self.failed_sessions
            },
            'performance': {
                'avg_session_time': self.avg_session_time,
                'avg_analyst_time': self.avg_analyst_time,
                'queue_depth': self.queue_depth
            },
            'reliability': {
                'error_rate': self.error_rate,
                'recovery_rate': self.recovery_rate
            }
        }

class ResourceManager:
    """資源管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 資源限制
        self.resource_limits = {
            ResourceType.CPU: self.config.get('max_cpu_percent', 80.0),
            ResourceType.MEMORY: self.config.get('max_memory_percent', 85.0),
            ResourceType.NETWORK: self.config.get('max_network_mb_per_sec', 100.0)
        }
        
        # 資源使用追蹤
        self.resource_usage: Dict[ResourceType, deque] = {
            res_type: deque(maxlen=100) for res_type in ResourceType
        }
        
        # 線程池
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('max_worker_threads', 8),
            thread_name_prefix="TradingAgents"
        )
        
        # 監控標誌
        self._monitoring = False
        self._monitor_task = None
        
    async def start_monitoring(self):
        """開始資源監控"""
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_resources())
        system_logger.info("資源監控已啟動")
    
    async def stop_monitoring(self):
        """停止資源監控"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        system_logger.info("資源監控已停止")
    
    async def _monitor_resources(self):
        """監控系統資源"""
        while self._monitoring:
            try:
                # 獲取系統資源使用情況
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # 記錄資源使用
                self.resource_usage[ResourceType.CPU].append((datetime.now(), cpu_percent))
                self.resource_usage[ResourceType.MEMORY].append((datetime.now(), memory.percent))
                
                # 檢查資源限制
                await self._check_resource_limits(cpu_percent, memory.percent)
                
                # 等待下一次檢查
                await asyncio.sleep(5)  # 每5秒檢查一次
                
            except Exception as e:
                system_logger.error(f"資源監控錯誤: {str(e)}")
                await asyncio.sleep(10)  # 錯誤時等待更長時間
    
    async def _check_resource_limits(self, cpu_percent: float, memory_percent: float):
        """檢查資源限制"""
        if cpu_percent > self.resource_limits[ResourceType.CPU]:
            system_logger.warning(f"CPU使用率過高: {cpu_percent:.1f}%", extra={
                'resource_type': 'cpu',
                'usage_percent': cpu_percent,
                'limit_percent': self.resource_limits[ResourceType.CPU],
                'resource_alert': True
            })
        
        if memory_percent > self.resource_limits[ResourceType.MEMORY]:
            system_logger.warning(f"記憶體使用率過高: {memory_percent:.1f}%", extra={
                'resource_type': 'memory',
                'usage_percent': memory_percent,
                'limit_percent': self.resource_limits[ResourceType.MEMORY],
                'resource_alert': True
            })
            
            # 觸發垃圾回收
            await self.trigger_gc()
    
    async def trigger_gc(self):
        """觸發垃圾回收"""
        def run_gc():
            collected = gc.collect()
            return collected
        
        # 在線程池中執行垃圾回收
        loop = asyncio.get_event_loop()
        collected = await loop.run_in_executor(self.thread_pool, run_gc)
        
        system_logger.info(f"垃圾回收完成，回收對象數: {collected}", extra={
            'gc_collected': collected,
            'resource_optimization': True
        })
    
    def get_resource_status(self) -> Dict[str, Any]:
        """獲取資源狀態"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            return {
                'cpu': {
                    'current_percent': cpu_percent,
                    'limit_percent': self.resource_limits[ResourceType.CPU],
                    'status': 'normal' if cpu_percent < self.resource_limits[ResourceType.CPU] else 'high'
                },
                'memory': {
                    'current_percent': memory.percent,
                    'current_mb': memory.used / 1024 / 1024,
                    'available_mb': memory.available / 1024 / 1024,
                    'limit_percent': self.resource_limits[ResourceType.MEMORY],
                    'status': 'normal' if memory.percent < self.resource_limits[ResourceType.MEMORY] else 'high'
                },
                'threads': {
                    'active_threads': threading.active_count(),
                    'thread_pool_size': self.thread_pool._max_workers
                }
            }
        except Exception as e:
            system_logger.error(f"獲取資源狀態失敗: {str(e)}")
            return {}

class ConcurrencyOptimizer:
    """並發優化器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 並發配置
        self.max_concurrent_sessions = self.config.get('max_concurrent_sessions', 10)
        self.max_concurrent_analysts = self.config.get('max_concurrent_analysts', 20)
        self.adaptive_concurrency = self.config.get('adaptive_concurrency', True)
        
        # 信號量控制並發
        self.session_semaphore = asyncio.Semaphore(self.max_concurrent_sessions)
        self.analyst_semaphore = asyncio.Semaphore(self.max_concurrent_analysts)
        
        # 性能追蹤
        self.performance_history: deque = deque(maxlen=1000)
        self.last_adjustment = datetime.now()
        
    async def acquire_session_slot(self) -> bool:
        """獲取會話槽位"""
        try:
            await asyncio.wait_for(self.session_semaphore.acquire(), timeout=30)
            return True
        except asyncio.TimeoutError:
            system_logger.warning("會話槽位獲取超時")
            return False
    
    def release_session_slot(self):
        """釋放會話槽位"""
        self.session_semaphore.release()
    
    async def acquire_analyst_slot(self) -> bool:
        """獲取分析師槽位"""
        try:
            await asyncio.wait_for(self.analyst_semaphore.acquire(), timeout=10)
            return True
        except asyncio.TimeoutError:
            system_logger.warning("分析師槽位獲取超時")
            return False
    
    def release_analyst_slot(self):
        """釋放分析師槽位"""
        self.analyst_semaphore.release()
    
    async def adaptive_adjust(self, performance_metrics: PerformanceMetrics):
        """自適應調整並發數量"""
        if not self.adaptive_concurrency:
            return
        
        # 檢查是否需要調整（至少間隔5分鐘）
        if datetime.now() - self.last_adjustment < timedelta(minutes=5):
            return
        
        current_error_rate = performance_metrics.error_rate
        current_cpu = performance_metrics.cpu_percent
        current_memory = performance_metrics.memory_percent
        
        # 調整邏輯
        should_increase = (
            current_error_rate < 0.05 and  # 錯誤率低於5%
            current_cpu < 70.0 and         # CPU使用率低於70%
            current_memory < 75.0           # 記憶體使用率低於75%
        )
        
        should_decrease = (
            current_error_rate > 0.15 or   # 錯誤率高於15%
            current_cpu > 85.0 or          # CPU使用率高於85%
            current_memory > 85.0          # 記憶體使用率高於85%
        )
        
        if should_increase and self.max_concurrent_sessions < 20:
            self._adjust_concurrency(1)
            system_logger.info(f"增加並發數量至: {self.max_concurrent_sessions}")
        elif should_decrease and self.max_concurrent_sessions > 3:
            self._adjust_concurrency(-1)
            system_logger.info(f"減少並發數量至: {self.max_concurrent_sessions}")
        
        self.last_adjustment = datetime.now()
    
    def _adjust_concurrency(self, delta: int):
        """調整並發數量"""
        # 調整會話並發數
        new_session_limit = max(1, self.max_concurrent_sessions + delta)
        self.max_concurrent_sessions = new_session_limit
        
        # 創建新的信號量（注意：這是簡化實現）
        self.session_semaphore = asyncio.Semaphore(new_session_limit)
        
        # 調整分析師並發數
        new_analyst_limit = max(2, self.max_concurrent_analysts + delta * 2)
        self.max_concurrent_analysts = new_analyst_limit
        self.analyst_semaphore = asyncio.Semaphore(new_analyst_limit)

class SessionManager:
    """會話管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 會話存儲
        self.active_sessions: Dict[str, Any] = {}
        self.completed_sessions: Dict[str, Any] = {}
        self.session_history: deque = deque(maxlen=10000)
        
        # 會話清理配置
        self.session_timeout = timedelta(
            seconds=self.config.get('session_timeout', 1800)  # 30分鐘
        )
        self.cleanup_interval = self.config.get('cleanup_interval', 300)  # 5分鐘
        
        # 弱引用追蹤
        self.session_refs: weakref.WeakValueDictionary = weakref.WeakValueDictionary()
        
        # 清理任務
        self._cleanup_task = None
        self._running = False
    
    async def start_cleanup_task(self):
        """啟動清理任務"""
        self._running = True
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        system_logger.info("會話清理任務已啟動")
    
    async def stop_cleanup_task(self):
        """停止清理任務"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        system_logger.info("會話清理任務已停止")
    
    async def _periodic_cleanup(self):
        """定期清理過期會話"""
        while self._running:
            try:
                await self.cleanup_expired_sessions()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                system_logger.error(f"會話清理錯誤: {str(e)}")
                await asyncio.sleep(60)  # 錯誤時等待更長時間
    
    async def cleanup_expired_sessions(self):
        """清理過期會話"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_state in self.active_sessions.items():
            if hasattr(session_state, 'start_time'):
                session_age = current_time - session_state.start_time
                if session_age > self.session_timeout:
                    expired_sessions.append(session_id)
        
        # 清理過期會話
        for session_id in expired_sessions:
            await self._cleanup_session(session_id, reason="timeout")
        
        if expired_sessions:
            system_logger.info(f"清理了 {len(expired_sessions)} 個過期會話")
    
    async def _cleanup_session(self, session_id: str, reason: str = "manual"):
        """清理單個會話"""
        if session_id in self.active_sessions:
            session_state = self.active_sessions[session_id]
            
            # 移動到已完成會話
            self.completed_sessions[session_id] = {
                'state': session_state,
                'cleanup_time': datetime.now(),
                'cleanup_reason': reason
            }
            
            # 從活躍會話中移除
            del self.active_sessions[session_id]
            
            # 記錄到歷史
            self.session_history.append({
                'session_id': session_id,
                'cleanup_time': datetime.now(),
                'reason': reason
            })
            
            system_logger.debug(f"會話 {session_id} 已清理，原因: {reason}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """獲取會話統計"""
        return {
            'active_sessions': len(self.active_sessions),
            'completed_sessions': len(self.completed_sessions),
            'total_historical': len(self.session_history),
            'session_timeout_minutes': self.session_timeout.total_seconds() / 60,
            'cleanup_interval_seconds': self.cleanup_interval
        }

class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 監控配置
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.metrics_retention_hours = self.config.get('metrics_retention_hours', 24)
        
        # 指標存儲
        self.metrics_history: deque = deque(maxlen=17280)  # 24小時，每5秒一個數據點
        self.alert_thresholds = {
            'cpu_percent': self.config.get('cpu_alert_threshold', 85.0),
            'memory_percent': self.config.get('memory_alert_threshold', 85.0),
            'error_rate': self.config.get('error_rate_threshold', 0.1),
            'avg_session_time': self.config.get('session_time_threshold', 300.0)
        }
        
        # 告警狀態
        self.active_alerts: Dict[str, datetime] = {}
        
    async def collect_metrics(
        self,
        active_sessions: int,
        completed_sessions: int,
        failed_sessions: int,
        avg_session_time: float = 0.0,
        avg_analyst_time: float = 0.0,
        queue_depth: int = 0,
        error_rate: float = 0.0,
        recovery_rate: float = 0.0
    ) -> PerformanceMetrics:
        """收集性能指標"""
        try:
            # 獲取系統資源
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            
            # 創建指標對象
            metrics = PerformanceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / 1024 / 1024,
                active_sessions=active_sessions,
                completed_sessions=completed_sessions,
                failed_sessions=failed_sessions,
                avg_session_time=avg_session_time,
                avg_analyst_time=avg_analyst_time,
                queue_depth=queue_depth,
                error_rate=error_rate,
                recovery_rate=recovery_rate
            )
            
            # 存儲指標
            if self.monitoring_enabled:
                self.metrics_history.append(metrics)
                
                # 檢查告警條件
                await self._check_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            system_logger.error(f"指標收集失敗: {str(e)}")
            return PerformanceMetrics()
    
    async def _check_alerts(self, metrics: PerformanceMetrics):
        """檢查告警條件"""
        alerts_to_trigger = []
        alerts_to_clear = []
        
        # 檢查各項指標
        if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
            alerts_to_trigger.append(('cpu_high', f"CPU使用率過高: {metrics.cpu_percent:.1f}%"))
        else:
            alerts_to_clear.append('cpu_high')
        
        if metrics.memory_percent > self.alert_thresholds['memory_percent']:
            alerts_to_trigger.append(('memory_high', f"記憶體使用率過高: {metrics.memory_percent:.1f}%"))
        else:
            alerts_to_clear.append('memory_high')
        
        if metrics.error_rate > self.alert_thresholds['error_rate']:
            alerts_to_trigger.append(('error_rate_high', f"錯誤率過高: {metrics.error_rate:.2%}"))
        else:
            alerts_to_clear.append('error_rate_high')
        
        if metrics.avg_session_time > self.alert_thresholds['avg_session_time']:
            alerts_to_trigger.append(('session_time_high', f"平均會話時間過長: {metrics.avg_session_time:.1f}秒"))
        else:
            alerts_to_clear.append('session_time_high')
        
        # 觸發新告警
        for alert_key, alert_message in alerts_to_trigger:
            if alert_key not in self.active_alerts:
                self.active_alerts[alert_key] = datetime.now()
                system_logger.warning(f"性能告警: {alert_message}", extra={
                    'alert_type': alert_key,
                    'alert_message': alert_message,
                    'performance_alert': True
                })
        
        # 清除已恢復的告警
        for alert_key in alerts_to_clear:
            if alert_key in self.active_alerts:
                duration = datetime.now() - self.active_alerts[alert_key]
                del self.active_alerts[alert_key]
                system_logger.info(f"性能告警恢復: {alert_key}，持續時間: {duration.total_seconds():.1f}秒", extra={
                    'alert_type': alert_key,
                    'alert_resolved': True,
                    'duration_seconds': duration.total_seconds()
                })
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """獲取性能摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {'message': '沒有可用的性能數據'}
        
        # 計算統計值
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        session_times = [m.avg_session_time for m in recent_metrics if m.avg_session_time > 0]
        
        return {
            'timeframe_hours': hours,
            'data_points': len(recent_metrics),
            'cpu': {
                'avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory': {
                'avg': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            },
            'sessions': {
                'total_active': recent_metrics[-1].active_sessions if recent_metrics else 0,
                'total_completed': recent_metrics[-1].completed_sessions if recent_metrics else 0,
                'total_failed': recent_metrics[-1].failed_sessions if recent_metrics else 0,
                'avg_processing_time': sum(session_times) / len(session_times) if session_times else 0
            },
            'active_alerts': list(self.active_alerts.keys()),
            'timestamp': datetime.now().isoformat()
        }

class ProductionOptimizer:
    """生產環境優化器 - 主控制器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 優化級別
        self.optimization_level = OptimizationLevel(
            self.config.get('optimization_level', 'balanced')
        )
        
        # 組件初始化
        self.resource_manager = ResourceManager(self.config.get('resource_manager', {}))
        self.concurrency_optimizer = ConcurrencyOptimizer(self.config.get('concurrency', {}))
        self.session_manager = SessionManager(self.config.get('session_manager', {}))
        self.performance_monitor = PerformanceMonitor(self.config.get('monitoring', {}))
        
        # 運行狀態
        self._running = False
        self._optimization_task = None
        
        system_logger.info(f"生產優化器初始化完成，優化級別: {self.optimization_level.value}")
    
    async def start(self):
        """啟動優化器"""
        if self._running:
            return
        
        self._running = True
        
        # 啟動各組件
        await self.resource_manager.start_monitoring()
        await self.session_manager.start_cleanup_task()
        
        # 啟動主優化循環
        self._optimization_task = asyncio.create_task(self._optimization_loop())
        
        system_logger.info("生產優化器已啟動")
    
    async def stop(self):
        """停止優化器"""
        if not self._running:
            return
        
        self._running = False
        
        # 停止主優化循環
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass
        
        # 停止各組件
        await self.resource_manager.stop_monitoring()
        await self.session_manager.stop_cleanup_task()
        
        system_logger.info("生產優化器已停止")
    
    async def _optimization_loop(self):
        """主優化循環"""
        while self._running:
            try:
                # 收集當前指標
                session_stats = self.session_manager.get_session_stats()
                
                metrics = await self.performance_monitor.collect_metrics(
                    active_sessions=session_stats['active_sessions'],
                    completed_sessions=session_stats['completed_sessions'],
                    failed_sessions=0,  # 需要從錯誤處理器獲取
                    queue_depth=0  # 需要實現隊列深度統計
                )
                
                # 自適應並發調整
                await self.concurrency_optimizer.adaptive_adjust(metrics)
                
                # 根據優化級別執行不同的優化策略
                await self._execute_optimization_strategy(metrics)
                
                # 等待下一次優化週期
                await asyncio.sleep(30)  # 每30秒執行一次優化
                
            except Exception as e:
                error_info = await handle_error(e, {
                    'component': 'production_optimizer',
                    'phase': 'optimization_loop'
                })
                system_logger.error(f"優化循環錯誤: {str(e)}", extra={
                    'error_id': error_info.error_id
                })
                await asyncio.sleep(60)  # 錯誤時等待更長時間
    
    async def _execute_optimization_strategy(self, metrics: PerformanceMetrics):
        """執行優化策略"""
        if self.optimization_level == OptimizationLevel.AGGRESSIVE:
            # 激進優化：更頻繁的垃圾回收和資源清理
            if metrics.memory_percent > 70.0:
                await self.resource_manager.trigger_gc()
        
        elif self.optimization_level == OptimizationLevel.BALANCED:
            # 平衡優化：適度的資源管理
            if metrics.memory_percent > 80.0:
                await self.resource_manager.trigger_gc()
        
        # 基本優化：僅在資源緊張時執行清理
        if metrics.memory_percent > 90.0:
            await self.resource_manager.trigger_gc()
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """獲取優化狀態"""
        return {
            'running': self._running,
            'optimization_level': self.optimization_level.value,
            'resource_status': self.resource_manager.get_resource_status(),
            'session_stats': self.session_manager.get_session_stats(),
            'performance_summary': self.performance_monitor.get_performance_summary(),
            'concurrency_limits': {
                'max_sessions': self.concurrency_optimizer.max_concurrent_sessions,
                'max_analysts': self.concurrency_optimizer.max_concurrent_analysts
            }
        }

# 便利函數
def create_production_optimizer(config: Optional[Dict[str, Any]] = None) -> ProductionOptimizer:
    """創建生產環境優化器"""
    return ProductionOptimizer(config)

# 裝飾器
def optimize_for_production(func):
    """生產環境優化裝飾器"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 記錄性能指標
            analysis_logger.debug(f"函數執行完成: {func.__name__}", extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'status': 'success',
                'production_optimized': True
            })
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # 記錄錯誤
            analysis_logger.error(f"函數執行失敗: {func.__name__}", extra={
                'function': func.__name__,
                'execution_time': execution_time,
                'error': str(e),
                'status': 'error',
                'production_optimized': True
            })
            
            raise
    
    return wrapper

if __name__ == "__main__":
    # 測試腳本
    async def test_production_optimizer():
        print("測試生產環境優化器...")
        
        # 創建優化器
        optimizer = create_production_optimizer({
            'optimization_level': 'balanced',
            'resource_manager': {
                'max_cpu_percent': 75.0,
                'max_memory_percent': 80.0
            },
            'concurrency': {
                'max_concurrent_sessions': 5,
                'adaptive_concurrency': True
            }
        })
        
        # 啟動優化器
        await optimizer.start()
        
        # 運行一段時間
        await asyncio.sleep(10)
        
        # 獲取狀態
        status = optimizer.get_optimization_status()
        print(f"優化狀態: {status}")
        
        # 停止優化器
        await optimizer.stop()
        
        print("生產環境優化器測試完成")
    
    # 如果可能，使用uvloop優化事件循環
    if UVLOOP_AVAILABLE:
        try:
            uvloop.install()
            system_logger.info("已安裝uvloop事件循環優化")
        except Exception as e:
            system_logger.warning(f"uvloop安裝失敗: {str(e)}")
    else:
        system_logger.info("uvloop不可用（Windows系統），使用默認事件循環")
    
    asyncio.run(test_production_optimizer())