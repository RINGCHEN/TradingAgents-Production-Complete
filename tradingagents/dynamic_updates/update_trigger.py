#!/usr/bin/env python3
"""
Update Trigger System
自動化更新觸發機制 - GPT-OSS整合任務1.2.3
實現基於條件的動態更新觸發
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from ..monitoring.performance_monitor import PerformanceMonitor, MetricType
from ..database.model_capability_db import ModelCapabilityDB
from .model_version_manager import ModelVersionManager, UpdateType, VersionStatus

logger = logging.getLogger(__name__)

class TriggerType(Enum):
    """觸發器類型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    SCHEDULED_UPDATE = "scheduled_update"
    MANUAL_TRIGGER = "manual_trigger"
    BENCHMARK_IMPROVEMENT = "benchmark_improvement"
    ERROR_THRESHOLD = "error_threshold"
    COST_OPTIMIZATION = "cost_optimization"

class TriggerPriority(Enum):
    """觸發器優先級"""
    CRITICAL = "critical"    # 立即執行
    HIGH = "high"           # 高優先級
    MEDIUM = "medium"       # 中優先級
    LOW = "low"            # 低優先級

@dataclass
class TriggerCondition:
    """觸發條件"""
    name: str
    description: str
    condition_type: TriggerType
    priority: TriggerPriority
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    cooldown_minutes: int = 60  # 冷卻時間
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    max_triggers_per_day: int = 10

    def is_in_cooldown(self) -> bool:
        """檢查是否在冷卻期"""
        if not self.last_triggered:
            return False
        
        cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
        return datetime.now(timezone.utc) < cooldown_end
    
    def can_trigger_today(self) -> bool:
        """檢查今天是否還能觸發"""
        if not self.last_triggered:
            return True
        
        today = datetime.now(timezone.utc).date()
        last_trigger_date = self.last_triggered.date()
        
        if last_trigger_date != today:
            return True
        
        return self.trigger_count < self.max_triggers_per_day
    
    def record_trigger(self):
        """記錄觸發"""
        now = datetime.now(timezone.utc)
        
        # 如果是新的一天，重置計數
        if not self.last_triggered or self.last_triggered.date() != now.date():
            self.trigger_count = 0
        
        self.last_triggered = now
        self.trigger_count += 1

@dataclass
class UpdateRequest:
    """更新請求"""
    trigger_condition: TriggerCondition
    provider: str
    model_id: str
    update_type: UpdateType
    reason: str
    priority: TriggerPriority
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'trigger_condition': self.trigger_condition.name,
            'provider': self.provider,
            'model_id': self.model_id,
            'update_type': self.update_type.value,
            'reason': self.reason,
            'priority': self.priority.value,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat()
        }

class TriggerConditionChecker(ABC):
    """觸發條件檢查器基類"""
    
    @abstractmethod
    async def check_condition(
        self,
        condition: TriggerCondition,
        context: Dict[str, Any]
    ) -> Optional[UpdateRequest]:
        """檢查條件是否滿足"""
        pass

class PerformanceDegradationChecker(TriggerConditionChecker):
    """性能退化檢查器"""
    
    def __init__(self, performance_monitor: PerformanceMonitor):
        self.performance_monitor = performance_monitor
    
    async def check_condition(
        self,
        condition: TriggerCondition,
        context: Dict[str, Any]
    ) -> Optional[UpdateRequest]:
        """檢查性能退化條件"""
        try:
            provider = context.get('provider')
            model_id = context.get('model_id')
            
            if not provider or not model_id:
                return None
            
            # 獲取當前性能指標
            current_metrics = self.performance_monitor.get_current_metrics(provider, model_id)
            
            # 檢查關鍵指標
            for metric_key, stats in current_metrics.items():
                if not stats:
                    continue
                
                parts = metric_key.split('/')
                if len(parts) != 3:
                    continue
                
                _, _, metric_type = parts
                mean_value = stats.get('mean', 0)
                
                # 檢查延遲退化
                if metric_type == 'latency':
                    threshold = condition.parameters.get('latency_threshold_ms', 3000)
                    if mean_value > threshold:
                        return UpdateRequest(
                            trigger_condition=condition,
                            provider=provider,
                            model_id=model_id,
                            update_type=UpdateType.PATCH,
                            reason=f"Latency degradation detected: {mean_value:.0f}ms > {threshold}ms",
                            priority=TriggerPriority.HIGH,
                            metadata={'current_latency': mean_value, 'threshold': threshold}
                        )
                
                # 檢查錯誤率上升
                elif metric_type == 'error_rate':
                    threshold = condition.parameters.get('error_rate_threshold', 0.05)
                    if mean_value > threshold:
                        return UpdateRequest(
                            trigger_condition=condition,
                            provider=provider,
                            model_id=model_id,
                            update_type=UpdateType.HOTFIX,
                            reason=f"Error rate increased: {mean_value:.1%} > {threshold:.1%}",
                            priority=TriggerPriority.CRITICAL,
                            metadata={'current_error_rate': mean_value, 'threshold': threshold}
                        )
                
                # 檢查準確性下降
                elif metric_type == 'accuracy':
                    threshold = condition.parameters.get('accuracy_threshold', 0.8)
                    if mean_value < threshold:
                        return UpdateRequest(
                            trigger_condition=condition,
                            provider=provider,
                            model_id=model_id,
                            update_type=UpdateType.MINOR,
                            reason=f"Accuracy degradation: {mean_value:.1%} < {threshold:.1%}",
                            priority=TriggerPriority.MEDIUM,
                            metadata={'current_accuracy': mean_value, 'threshold': threshold}
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking performance degradation: {e}")
            return None

class ScheduledUpdateChecker(TriggerConditionChecker):
    """定時更新檢查器"""
    
    async def check_condition(
        self,
        condition: TriggerCondition,
        context: Dict[str, Any]
    ) -> Optional[UpdateRequest]:
        """檢查定時更新條件"""
        try:
            provider = context.get('provider')
            model_id = context.get('model_id')
            
            if not provider or not model_id:
                return None
            
            # 檢查更新間隔
            update_interval_days = condition.parameters.get('update_interval_days', 30)
            last_update = context.get('last_update_time')
            
            if last_update:
                if isinstance(last_update, str):
                    last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                
                days_since_update = (datetime.now(timezone.utc) - last_update).days
                
                if days_since_update >= update_interval_days:
                    return UpdateRequest(
                        trigger_condition=condition,
                        provider=provider,
                        model_id=model_id,
                        update_type=UpdateType.MINOR,
                        reason=f"Scheduled update: {days_since_update} days since last update",
                        priority=TriggerPriority.LOW,
                        metadata={'days_since_update': days_since_update, 'interval': update_interval_days}
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking scheduled update: {e}")
            return None

class BenchmarkImprovementChecker(TriggerConditionChecker):
    """基準測試改進檢查器"""
    
    def __init__(self, model_db: ModelCapabilityDB):
        self.model_db = model_db
    
    async def check_condition(
        self,
        condition: TriggerCondition,
        context: Dict[str, Any]
    ) -> Optional[UpdateRequest]:
        """檢查基準測試改進條件"""
        try:
            provider = context.get('provider')
            model_id = context.get('model_id')
            
            if not provider or not model_id:
                return None
            
            # 獲取最新基準測試結果
            model_capability = await self.model_db.get_model_capability(provider, model_id)
            if not model_capability or not model_capability.benchmark_scores:
                return None
            
            # 檢查改進幅度
            improvement_threshold = condition.parameters.get('improvement_threshold', 0.1)
            current_score = model_capability.benchmark_scores.get('overall_score', 0)
            
            # 這裡應該與歷史基準進行比較，簡化實現
            baseline_score = context.get('baseline_score', current_score * 0.9)
            
            if current_score > baseline_score * (1 + improvement_threshold):
                return UpdateRequest(
                    trigger_condition=condition,
                    provider=provider,
                    model_id=model_id,
                    update_type=UpdateType.MINOR,
                    reason=f"Benchmark improvement detected: {current_score:.3f} > {baseline_score:.3f}",
                    priority=TriggerPriority.MEDIUM,
                    metadata={
                        'current_score': current_score,
                        'baseline_score': baseline_score,
                        'improvement': (current_score - baseline_score) / baseline_score
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error checking benchmark improvement: {e}")
            return None

class UpdateTriggerSystem:
    """
    更新觸發系統
    
    功能：
    1. 監控多種觸發條件
    2. 評估更新請求的優先級
    3. 管理更新隊列
    4. 執行自動化更新流程
    """
    
    def __init__(
        self,
        performance_monitor: Optional[PerformanceMonitor] = None,
        model_db: Optional[ModelCapabilityDB] = None,
        version_manager: Optional[ModelVersionManager] = None
    ):
        """
        初始化更新觸發系統
        
        Args:
            performance_monitor: 性能監控器
            model_db: 模型能力數據庫
            version_manager: 版本管理器
        """
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.model_db = model_db or ModelCapabilityDB()
        self.version_manager = version_manager or ModelVersionManager()
        
        # 觸發條件
        self.trigger_conditions: Dict[str, TriggerCondition] = {}
        
        # 條件檢查器
        self.checkers: Dict[TriggerType, TriggerConditionChecker] = {
            TriggerType.PERFORMANCE_DEGRADATION: PerformanceDegradationChecker(self.performance_monitor),
            TriggerType.SCHEDULED_UPDATE: ScheduledUpdateChecker(),
            TriggerType.BENCHMARK_IMPROVEMENT: BenchmarkImprovementChecker(self.model_db)
        }
        
        # 更新隊列
        self.update_queue: List[UpdateRequest] = []
        
        # 更新回調
        self.update_callbacks: List[Callable[[UpdateRequest], None]] = []
        
        self.logger = logger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._processing_task: Optional[asyncio.Task] = None
        self._running = False
    
    def add_trigger_condition(self, condition: TriggerCondition):
        """添加觸發條件"""
        self.trigger_conditions[condition.name] = condition
        self.logger.info(f"✅ Added trigger condition: {condition.name}")
    
    def remove_trigger_condition(self, name: str) -> bool:
        """移除觸發條件"""
        if name in self.trigger_conditions:
            del self.trigger_conditions[name]
            self.logger.info(f"✅ Removed trigger condition: {name}")
            return True
        return False
    
    def enable_condition(self, name: str) -> bool:
        """啟用條件"""
        if name in self.trigger_conditions:
            self.trigger_conditions[name].enabled = True
            return True
        return False
    
    def disable_condition(self, name: str) -> bool:
        """禁用條件"""
        if name in self.trigger_conditions:
            self.trigger_conditions[name].enabled = False
            return True
        return False
    
    def add_update_callback(self, callback: Callable[[UpdateRequest], None]):
        """添加更新回調"""
        self.update_callbacks.append(callback)
    
    async def start(self):
        """啟動觸發系統"""
        if not self._running:
            self._running = True
            
            # 初始化默認觸發條件
            self._initialize_default_conditions()
            
            # 啟動監控和處理任務
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._processing_task = asyncio.create_task(self._processing_loop())
            
            self.logger.info("✅ Update trigger system started")
    
    async def stop(self):
        """停止觸發系統"""
        if self._running:
            self._running = False
            
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("✅ Update trigger system stopped")
    
    def _initialize_default_conditions(self):
        """初始化默認觸發條件"""
        default_conditions = [
            TriggerCondition(
                name="performance_degradation",
                description="Trigger when performance degrades significantly",
                condition_type=TriggerType.PERFORMANCE_DEGRADATION,
                priority=TriggerPriority.HIGH,
                parameters={
                    'latency_threshold_ms': 3000,
                    'error_rate_threshold': 0.05,
                    'accuracy_threshold': 0.8
                },
                cooldown_minutes=30,
                max_triggers_per_day=5
            ),
            TriggerCondition(
                name="scheduled_monthly_update",
                description="Monthly scheduled update",
                condition_type=TriggerType.SCHEDULED_UPDATE,
                priority=TriggerPriority.LOW,
                parameters={'update_interval_days': 30},
                cooldown_minutes=1440,  # 24 hours
                max_triggers_per_day=1
            ),
            TriggerCondition(
                name="benchmark_improvement",
                description="Trigger when benchmark shows significant improvement",
                condition_type=TriggerType.BENCHMARK_IMPROVEMENT,
                priority=TriggerPriority.MEDIUM,
                parameters={'improvement_threshold': 0.1},
                cooldown_minutes=120,
                max_triggers_per_day=3
            )
        ]
        
        for condition in default_conditions:
            self.add_trigger_condition(condition)
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                await self._check_all_conditions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
    
    async def _processing_loop(self):
        """處理循環"""
        while self._running:
            try:
                await asyncio.sleep(10)  # 每10秒處理一次隊列
                await self._process_update_queue()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in processing loop: {e}")
    
    async def _check_all_conditions(self):
        """檢查所有觸發條件"""
        try:
            # 獲取所有活躍模型
            models = await self.model_db.list_model_capabilities(is_available=True)
            
            for model in models:
                context = {
                    'provider': model.provider,
                    'model_id': model.model_id,
                    'last_update_time': model.updated_at
                }
                
                # 檢查每個觸發條件
                for condition in self.trigger_conditions.values():
                    if not condition.enabled:
                        continue
                    
                    if condition.is_in_cooldown():
                        continue
                    
                    if not condition.can_trigger_today():
                        continue
                    
                    # 使用對應的檢查器
                    checker = self.checkers.get(condition.condition_type)
                    if not checker:
                        continue
                    
                    update_request = await checker.check_condition(condition, context)
                    if update_request:
                        condition.record_trigger()
                        self._add_to_queue(update_request)
                        
                        self.logger.info(
                            f"🔔 Triggered update: {condition.name} for "
                            f"{model.provider}/{model.model_id} - {update_request.reason}"
                        )
                        
        except Exception as e:
            self.logger.error(f"❌ Error checking conditions: {e}")
    
    def _add_to_queue(self, update_request: UpdateRequest):
        """添加到更新隊列"""
        # 避免重複請求
        existing = any(
            req.provider == update_request.provider and
            req.model_id == update_request.model_id and
            req.trigger_condition.name == update_request.trigger_condition.name
            for req in self.update_queue
        )
        
        if not existing:
            self.update_queue.append(update_request)
            # 按優先級排序
            self.update_queue.sort(key=lambda x: (
                {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}[x.priority.value],
                x.created_at
            ))
    
    async def _process_update_queue(self):
        """處理更新隊列"""
        if not self.update_queue:
            return
        
        # 取出最高優先級的請求
        update_request = self.update_queue.pop(0)
        
        try:
            await self._execute_update_request(update_request)
            
        except Exception as e:
            self.logger.error(f"❌ Error executing update request: {e}")
    
    async def _execute_update_request(self, request: UpdateRequest):
        """執行更新請求"""
        try:
            self.logger.info(
                f"🔄 Executing update: {request.provider}/{request.model_id} "
                f"({request.update_type.value}) - {request.reason}"
            )
            
            # 調用更新回調
            for callback in self.update_callbacks:
                try:
                    callback(request)
                except Exception as e:
                    self.logger.error(f"❌ Error in update callback: {e}")
            
            # 這裡可以集成實際的模型更新邏輯
            # 例如：重新訓練模型、更新配置、運行基準測試等
            
            # 記錄更新到版本管理器
            current_model = await self.model_db.get_model_capability(
                request.provider, request.model_id
            )
            
            if current_model:
                await self.version_manager.create_model_version(
                    provider=request.provider,
                    model_id=request.model_id,
                    update_type=request.update_type,
                    capabilities=current_model.dict(),
                    change_summary=request.reason,
                    metadata=request.metadata
                )
            
            self.logger.info(f"✅ Update executed successfully: {request.provider}/{request.model_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to execute update request: {e}")
            raise
    
    async def manual_trigger(
        self,
        provider: str,
        model_id: str,
        update_type: UpdateType,
        reason: str,
        priority: TriggerPriority = TriggerPriority.MEDIUM
    ) -> bool:
        """手動觸發更新"""
        try:
            manual_condition = TriggerCondition(
                name=f"manual_trigger_{datetime.now(timezone.utc).timestamp()}",
                description="Manual trigger",
                condition_type=TriggerType.MANUAL_TRIGGER,
                priority=priority
            )
            
            update_request = UpdateRequest(
                trigger_condition=manual_condition,
                provider=provider,
                model_id=model_id,
                update_type=update_type,
                reason=reason,
                priority=priority
            )
            
            self._add_to_queue(update_request)
            
            self.logger.info(f"🔔 Manual trigger added: {provider}/{model_id} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error in manual trigger: {e}")
            return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """獲取隊列狀態"""
        return {
            'queue_length': len(self.update_queue),
            'pending_requests': [req.to_dict() for req in self.update_queue],
            'active_conditions': len([c for c in self.trigger_conditions.values() if c.enabled]),
            'total_conditions': len(self.trigger_conditions),
            'system_running': self._running
        }
    
    def get_condition_status(self) -> List[Dict[str, Any]]:
        """獲取條件狀態"""
        status_list = []
        
        for condition in self.trigger_conditions.values():
            status = {
                'name': condition.name,
                'description': condition.description,
                'enabled': condition.enabled,
                'type': condition.condition_type.value,
                'priority': condition.priority.value,
                'trigger_count': condition.trigger_count,
                'last_triggered': condition.last_triggered.isoformat() if condition.last_triggered else None,
                'in_cooldown': condition.is_in_cooldown(),
                'can_trigger_today': condition.can_trigger_today()
            }
            status_list.append(status)
        
        return status_list