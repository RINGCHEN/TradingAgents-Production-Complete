#!/usr/bin/env python3
"""
Dynamic Capability Updater
動態能力更新器 - GPT-OSS整合任務1.2.3
"""

import asyncio
import logging
import time
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..database.model_capability_db import ModelCapabilityDB
from ..monitoring.performance_monitor import PerformanceMonitor, MetricType
from ..benchmarks.benchmark_runner import BenchmarkRunner
from .model_version_control import ModelVersionControl, VersionUpdateRequest, ChangeType

logger = logging.getLogger(__name__)

class UpdateTrigger(Enum):
    """更新觸發條件"""
    PERFORMANCE_THRESHOLD = "performance_threshold"
    BENCHMARK_SCHEDULE = "benchmark_schedule"
    DRIFT_DETECTION = "drift_detection"
    MANUAL_REQUEST = "manual_request"
    TIME_BASED = "time_based"
    ALERT_BASED = "alert_based"

class UpdateStrategy(Enum):
    """更新策略"""
    IMMEDIATE = "immediate"
    BATCHED = "batched"
    SCHEDULED = "scheduled"
    GRADUAL = "gradual"

@dataclass
class UpdateRule:
    """更新規則"""
    rule_id: str
    trigger_type: UpdateTrigger
    conditions: Dict[str, Any]
    strategy: UpdateStrategy
    enabled: bool = True
    priority: int = 1  # 1=high, 2=medium, 3=low
    cooldown_minutes: int = 60
    max_retries: int = 3
    
    # 過濾條件
    provider_filter: Optional[Set[str]] = None
    model_filter: Optional[Set[str]] = None
    
    # 回調函數
    pre_update_callback: Optional[Callable] = None
    post_update_callback: Optional[Callable] = None

@dataclass
class UpdateTask:
    """更新任務"""
    task_id: str
    provider: str
    model_id: str
    update_type: ChangeType
    trigger: UpdateTrigger
    priority: int
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    scheduled_at: Optional[datetime] = None
    retry_count: int = 0
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UpdateResult:
    """更新結果"""
    task_id: str
    success: bool
    version_id: Optional[str] = None
    changes_applied: List[str] = field(default_factory=list)
    error: Optional[str] = None
    execution_time_ms: float = 0
    performance_impact: Dict[str, float] = field(default_factory=dict)

class DynamicCapabilityUpdater:
    """
    動態能力更新器
    
    功能：
    1. 自動監測模型性能變化
    2. 基於規則的更新觸發
    3. 智能更新策略調度
    4. 批量處理和優化
    5. 錯誤處理和重試機制
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        benchmark_runner: Optional[BenchmarkRunner] = None,
        version_control: Optional[ModelVersionControl] = None
    ):
        """初始化動態能力更新器"""
        self.model_db = model_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.benchmark_runner = benchmark_runner or BenchmarkRunner()
        self.version_control = version_control or ModelVersionControl()
        
        self.logger = logger
        
        # 更新規則和任務隊列
        self.update_rules: Dict[str, UpdateRule] = {}
        self.task_queue: List[UpdateTask] = []
        self.active_tasks: Dict[str, UpdateTask] = {}
        
        # 運行時狀態
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._worker_tasks: List[asyncio.Task] = []
        
        # 配置
        self.max_concurrent_updates = 3
        self.update_interval_seconds = 30
        self.batch_size = 5
        
        # 統計
        self.update_stats = {
            'total_updates': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'average_execution_time': 0.0
        }
        
        # 初始化默認規則
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """初始化默認更新規則"""
        # 性能閾值觸發規則
        self.add_update_rule(UpdateRule(
            rule_id="performance_degradation",
            trigger_type=UpdateTrigger.PERFORMANCE_THRESHOLD,
            conditions={
                'capability_score_threshold': 0.1,  # 能力評分下降超過0.1
                'latency_increase_threshold': 2000,  # 延遲增加超過2秒
                'error_rate_threshold': 0.15,  # 錯誤率超過15%
                'min_samples': 10  # 最少樣本數
            },
            strategy=UpdateStrategy.IMMEDIATE,
            priority=1,
            cooldown_minutes=30
        ))
        
        # 定期基準測試規則
        self.add_update_rule(UpdateRule(
            rule_id="scheduled_benchmark",
            trigger_type=UpdateTrigger.BENCHMARK_SCHEDULE,
            conditions={
                'schedule_hours': [2, 14],  # 每日2點和14點執行
                'min_days_since_last': 1  # 最少間隔1天
            },
            strategy=UpdateStrategy.BATCHED,
            priority=2,
            cooldown_minutes=720  # 12小時冷卻期
        ))
        
        # 模型漂移檢測規則
        self.add_update_rule(UpdateRule(
            rule_id="capability_drift",
            trigger_type=UpdateTrigger.DRIFT_DETECTION,
            conditions={
                'drift_threshold': 0.05,  # 5%的性能漂移
                'monitoring_window_hours': 24,  # 24小時監控窗口
                'confidence_threshold': 0.8  # 80%置信度
            },
            strategy=UpdateStrategy.GRADUAL,
            priority=2,
            cooldown_minutes=120
        ))
    
    def add_update_rule(self, rule: UpdateRule):
        """添加更新規則"""
        self.update_rules[rule.rule_id] = rule
        self.logger.info(f"✅ Added update rule: {rule.rule_id}")
    
    def remove_update_rule(self, rule_id: str) -> bool:
        """移除更新規則"""
        if rule_id in self.update_rules:
            del self.update_rules[rule_id]
            self.logger.info(f"✅ Removed update rule: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str, enabled: bool = True):
        """啟用/禁用規則"""
        if rule_id in self.update_rules:
            self.update_rules[rule_id].enabled = enabled
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"✅ Rule {rule_id} {status}")
    
    async def start(self):
        """啟動動態更新器"""
        if not self._running:
            self._running = True
            
            # 啟動調度器
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            
            # 啟動工作者
            for i in range(self.max_concurrent_updates):
                worker_task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
                self._worker_tasks.append(worker_task)
            
            # 註冊性能監控回調
            if hasattr(self.performance_monitor, 'add_alert_callback'):
                self.performance_monitor.add_alert_callback(self._handle_performance_alert)
            
            self.logger.info("✅ Dynamic capability updater started")
    
    async def stop(self):
        """停止動態更新器"""
        if self._running:
            self._running = False
            
            # 停止調度器
            if self._scheduler_task:
                self._scheduler_task.cancel()
                try:
                    await self._scheduler_task
                except asyncio.CancelledError:
                    pass
            
            # 停止工作者
            for worker_task in self._worker_tasks:
                worker_task.cancel()
            
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
            self._worker_tasks.clear()
            
            # 移除性能監控回調
            if hasattr(self.performance_monitor, 'remove_alert_callback'):
                self.performance_monitor.remove_alert_callback(self._handle_performance_alert)
            
            self.logger.info("✅ Dynamic capability updater stopped")
    
    async def _scheduler_loop(self):
        """調度器主循環"""
        while self._running:
            try:
                # 檢查所有啟用的規則
                for rule in self.update_rules.values():
                    if rule.enabled:
                        await self._evaluate_rule(rule)
                
                # 處理定時更新
                await self._process_scheduled_updates()
                
                # 等待下一次檢查
                await asyncio.sleep(self.update_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in scheduler loop: {e}")
                await asyncio.sleep(5)  # 錯誤後短暫休息
    
    async def _worker_loop(self, worker_id: str):
        """工作者主循環"""
        while self._running:
            try:
                # 從隊列獲取任務
                task = await self._get_next_task()
                
                if task:
                    self.active_tasks[task.task_id] = task
                    
                    try:
                        # 執行更新任務
                        result = await self._execute_update_task(task)
                        self.logger.info(f"✅ Worker {worker_id} completed task {task.task_id}")
                        
                    except Exception as e:
                        self.logger.error(f"❌ Worker {worker_id} failed task {task.task_id}: {e}")
                        
                        # 處理重試
                        if task.retry_count < 3:  # 最多重試3次
                            task.retry_count += 1
                            await self._schedule_task(task)
                    
                    finally:
                        # 移除活躍任務
                        if task.task_id in self.active_tasks:
                            del self.active_tasks[task.task_id]
                
                else:
                    # 沒有任務時短暫休息
                    await asyncio.sleep(1)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in worker {worker_id}: {e}")
                await asyncio.sleep(5)
    
    async def _evaluate_rule(self, rule: UpdateRule):
        """評估更新規則"""
        try:
            if rule.trigger_type == UpdateTrigger.PERFORMANCE_THRESHOLD:
                await self._check_performance_thresholds(rule)
            
            elif rule.trigger_type == UpdateTrigger.BENCHMARK_SCHEDULE:
                await self._check_benchmark_schedule(rule)
            
            elif rule.trigger_type == UpdateTrigger.DRIFT_DETECTION:
                await self._check_capability_drift(rule)
            
            elif rule.trigger_type == UpdateTrigger.TIME_BASED:
                await self._check_time_based_triggers(rule)
                
        except Exception as e:
            self.logger.error(f"❌ Error evaluating rule {rule.rule_id}: {e}")
    
    async def _check_performance_thresholds(self, rule: UpdateRule):
        """檢查性能閾值觸發條件"""
        conditions = rule.conditions
        
        # 獲取所有模型的當前指標
        current_metrics = self.performance_monitor.get_current_metrics()
        
        for window_key, metrics in current_metrics.items():
            if not metrics:
                continue
            
            parts = window_key.split('/')
            if len(parts) != 3:
                continue
            
            provider, model_id, metric_type = parts
            
            # 應用過濾條件
            if rule.provider_filter and provider not in rule.provider_filter:
                continue
            if rule.model_filter and model_id not in rule.model_filter:
                continue
            
            # 檢查樣本數
            sample_count = metrics.get('count', 0)
            if sample_count < conditions.get('min_samples', 10):
                continue
            
            # 檢查各項閾值
            trigger_update = False
            trigger_reason = []
            
            # 檢查能力評分下降
            if metric_type == 'accuracy' or metric_type == 'success_rate':
                current_value = metrics.get('mean', 1.0)
                threshold = conditions.get('capability_score_threshold', 0.1)
                
                # 獲取歷史基準
                model_capability = await self.model_db.get_model_capability(provider, model_id)
                if model_capability:
                    baseline = model_capability.accuracy_score or model_capability.capability_score or 0.8
                    if baseline - current_value > threshold:
                        trigger_update = True
                        trigger_reason.append(f"Performance degradation: {current_value:.3f} vs baseline {baseline:.3f}")
            
            # 檢查延遲增加
            if metric_type == 'latency':
                current_latency = metrics.get('mean', 0)
                threshold = conditions.get('latency_increase_threshold', 2000)
                
                model_capability = await self.model_db.get_model_capability(provider, model_id)
                if model_capability:
                    baseline_latency = model_capability.avg_latency_ms or 1000
                    if current_latency - baseline_latency > threshold:
                        trigger_update = True
                        trigger_reason.append(f"Latency increase: {current_latency:.0f}ms vs baseline {baseline_latency:.0f}ms")
            
            # 檢查錯誤率
            if metric_type == 'error_rate':
                error_rate = metrics.get('mean', 0)
                threshold = conditions.get('error_rate_threshold', 0.15)
                
                if error_rate > threshold:
                    trigger_update = True
                    trigger_reason.append(f"High error rate: {error_rate:.1%}")
            
            # 觸發更新任務
            if trigger_update:
                await self._create_update_task(
                    provider=provider,
                    model_id=model_id,
                    update_type=ChangeType.PERFORMANCE_UPDATE,
                    trigger=rule.trigger_type,
                    priority=rule.priority,
                    context={
                        'rule_id': rule.rule_id,
                        'trigger_reasons': trigger_reason,
                        'metrics': metrics
                    }
                )
    
    async def _check_benchmark_schedule(self, rule: UpdateRule):
        """檢查基準測試調度條件"""
        conditions = rule.conditions
        schedule_hours = conditions.get('schedule_hours', [])
        min_days_since_last = conditions.get('min_days_since_last', 1)
        
        current_hour = datetime.now(timezone.utc).hour
        
        if current_hour in schedule_hours:
            # 獲取所有可用模型
            models = await self.model_db.list_model_capabilities(is_available=True)
            
            for model in models:
                # 檢查最後基準測試時間
                if model.last_benchmarked:
                    time_since_last = datetime.now(timezone.utc) - model.last_benchmarked
                    if time_since_last.days < min_days_since_last:
                        continue
                
                # 創建基準測試任務
                await self._create_update_task(
                    provider=model.provider,
                    model_id=model.model_id,
                    update_type=ChangeType.BENCHMARK_RESULT,
                    trigger=rule.trigger_type,
                    priority=rule.priority,
                    context={
                        'rule_id': rule.rule_id,
                        'benchmark_type': 'scheduled',
                        'last_benchmarked': model.last_benchmarked.isoformat() if model.last_benchmarked else None
                    }
                )
    
    async def _check_capability_drift(self, rule: UpdateRule):
        """檢查能力漂移條件"""
        conditions = rule.conditions
        drift_threshold = conditions.get('drift_threshold', 0.05)
        window_hours = conditions.get('monitoring_window_hours', 24)
        confidence_threshold = conditions.get('confidence_threshold', 0.8)
        
        # 獲取所有模型的性能歷史
        models = await self.model_db.list_model_capabilities(is_available=True)
        
        for model in models:
            # 檢測性能漂移
            drift_detected = await self._detect_performance_drift(
                provider=model.provider,
                model_id=model.model_id,
                window_hours=window_hours,
                threshold=drift_threshold,
                confidence_threshold=confidence_threshold
            )
            
            if drift_detected:
                await self._create_update_task(
                    provider=model.provider,
                    model_id=model.model_id,
                    update_type=ChangeType.PERFORMANCE_UPDATE,
                    trigger=rule.trigger_type,
                    priority=rule.priority,
                    context={
                        'rule_id': rule.rule_id,
                        'drift_detected': True,
                        'monitoring_window_hours': window_hours
                    }
                )
    
    async def _detect_performance_drift(
        self,
        provider: str,
        model_id: str,
        window_hours: int,
        threshold: float,
        confidence_threshold: float
    ) -> bool:
        """檢測性能漂移"""
        try:
            # 獲取性能統計
            stats = self.performance_monitor.get_current_metrics(provider, model_id)
            
            for metric_key, metric_stats in stats.items():
                if not metric_stats or 'values' not in metric_stats:
                    continue
                
                values = metric_stats.get('values', [])
                if len(values) < 20:  # 需要足夠的樣本
                    continue
                
                # 計算滑動平均和趨勢
                window_size = min(10, len(values) // 2)
                recent_avg = statistics.mean(values[-window_size:])
                earlier_avg = statistics.mean(values[:window_size])
                
                # 計算相對變化
                if earlier_avg != 0:
                    relative_change = abs(recent_avg - earlier_avg) / abs(earlier_avg)
                    
                    if relative_change > threshold:
                        # 檢查置信度（簡化實現）
                        if len(values) > 30 and window_size >= 10:
                            return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting drift for {provider}/{model_id}: {e}")
            return False
    
    async def _create_update_task(
        self,
        provider: str,
        model_id: str,
        update_type: ChangeType,
        trigger: UpdateTrigger,
        priority: int,
        context: Optional[Dict[str, Any]] = None
    ):
        """創建更新任務"""
        task_id = f"{provider}-{model_id}-{int(time.time())}"
        
        task = UpdateTask(
            task_id=task_id,
            provider=provider,
            model_id=model_id,
            update_type=update_type,
            trigger=trigger,
            priority=priority,
            context=context or {}
        )
        
        await self._schedule_task(task)
    
    async def _schedule_task(self, task: UpdateTask):
        """調度任務"""
        # 檢查是否已有相同的活躍任務
        for active_task in self.active_tasks.values():
            if (active_task.provider == task.provider and 
                active_task.model_id == task.model_id and 
                active_task.update_type == task.update_type):
                self.logger.debug(f"Task already active for {task.provider}/{task.model_id}, skipping")
                return
        
        # 根據策略調度任務
        rule_id = task.context.get('rule_id')
        rule = self.update_rules.get(rule_id) if rule_id else None
        
        if rule and rule.strategy == UpdateStrategy.IMMEDIATE:
            # 立即執行
            self.task_queue.insert(0, task)  # 優先隊列
        else:
            # 添加到普通隊列
            self.task_queue.append(task)
        
        # 按優先級排序
        self.task_queue.sort(key=lambda t: t.priority)
        
        self.logger.debug(f"Scheduled task {task.task_id} (priority: {task.priority})")
    
    async def _get_next_task(self) -> Optional[UpdateTask]:
        """獲取下一個任務"""
        if self.task_queue:
            return self.task_queue.pop(0)
        return None
    
    async def _execute_update_task(self, task: UpdateTask) -> UpdateResult:
        """執行更新任務"""
        start_time = time.time()
        
        try:
            self.logger.info(f"🔄 Executing update task {task.task_id} for {task.provider}/{task.model_id}")
            
            result = UpdateResult(task_id=task.task_id, success=False)
            
            if task.update_type == ChangeType.BENCHMARK_RESULT:
                # 執行基準測試
                benchmark_result = await self._run_benchmark_update(task)
                result.success = benchmark_result['success']
                result.version_id = benchmark_result.get('version_id')
                result.changes_applied = benchmark_result.get('changes_applied', [])
                result.error = benchmark_result.get('error')
            
            elif task.update_type == ChangeType.PERFORMANCE_UPDATE:
                # 執行性能更新
                perf_result = await self._run_performance_update(task)
                result.success = perf_result['success']
                result.version_id = perf_result.get('version_id')
                result.changes_applied = perf_result.get('changes_applied', [])
                result.error = perf_result.get('error')
            
            # 更新統計
            execution_time = (time.time() - start_time) * 1000
            result.execution_time_ms = execution_time
            
            self._update_stats(result)
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            result = UpdateResult(
                task_id=task.task_id,
                success=False,
                error=str(e),
                execution_time_ms=execution_time
            )
            
            self._update_stats(result)
            raise
    
    async def _run_benchmark_update(self, task: UpdateTask) -> Dict[str, Any]:
        """執行基準測試更新"""
        try:
            # 運行基準測試
            benchmark_result = await self.benchmark_runner.run_model_benchmark(
                provider=task.provider,
                model_id=task.model_id,
                suite_name="standard"
            )
            
            if benchmark_result['success']:
                # 提取基準測試結果
                scores = benchmark_result.get('results', {})
                
                # 創建版本更新請求
                update_request = VersionUpdateRequest(
                    provider=task.provider,
                    model_id=task.model_id,
                    changes={
                        'benchmark_scores': scores,
                        'last_benchmarked': datetime.now(timezone.utc).isoformat()
                    },
                    change_type=ChangeType.BENCHMARK_RESULT,
                    change_summary=f"Automated benchmark update - {task.trigger.value}",
                    created_by="dynamic_updater",
                    reason=f"Triggered by rule: {task.context.get('rule_id', 'unknown')}",
                    context=task.context
                )
                
                # 執行版本化更新
                version_result = await self.version_control.update_model_capability_with_versioning(
                    update_request
                )
                
                return {
                    'success': version_result['success'],
                    'version_id': version_result.get('version_id'),
                    'changes_applied': version_result.get('changes_applied', []),
                    'benchmark_results': scores
                }
            
            else:
                return {
                    'success': False,
                    'error': benchmark_result.get('error', 'Benchmark failed')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _run_performance_update(self, task: UpdateTask) -> Dict[str, Any]:
        """執行性能更新"""
        try:
            # 獲取當前性能指標
            current_metrics = self.performance_monitor.get_current_metrics(
                task.provider, 
                task.model_id
            )
            
            # 計算新的能力評分
            updates = {}
            
            for metric_key, stats in current_metrics.items():
                if not stats:
                    continue
                
                metric_type = metric_key.split('/')[-1]
                mean_value = stats.get('mean')
                
                if mean_value is not None:
                    if metric_type == 'latency':
                        updates['avg_latency_ms'] = mean_value
                    elif metric_type == 'accuracy':
                        updates['accuracy_score'] = min(1.0, mean_value)
                    elif metric_type == 'success_rate':
                        # 更新整體能力評分
                        capability_score = self._calculate_updated_capability_score(stats, current_metrics)
                        if capability_score is not None:
                            updates['capability_score'] = capability_score
            
            if not updates:
                return {
                    'success': False,
                    'error': 'No performance updates to apply'
                }
            
            # 創建版本更新請求
            update_request = VersionUpdateRequest(
                provider=task.provider,
                model_id=task.model_id,
                changes=updates,
                change_type=ChangeType.PERFORMANCE_UPDATE,
                change_summary=f"Automated performance update - {task.trigger.value}",
                created_by="dynamic_updater",
                reason=f"Performance monitoring detected changes: {task.context.get('trigger_reasons', [])}",
                context=task.context
            )
            
            # 執行版本化更新
            version_result = await self.version_control.update_model_capability_with_versioning(
                update_request
            )
            
            return {
                'success': version_result['success'],
                'version_id': version_result.get('version_id'),
                'changes_applied': version_result.get('changes_applied', []),
                'performance_updates': updates
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_updated_capability_score(
        self, 
        primary_stats: Dict[str, float], 
        all_metrics: Dict[str, Dict[str, float]]
    ) -> Optional[float]:
        """計算更新的能力評分"""
        try:
            scores = []
            weights = {
                'success_rate': 0.4,
                'accuracy': 0.3,
                'latency': 0.2,
                'error_rate': 0.1
            }
            
            total_weight = 0.0
            
            for metric_key, metric_stats in all_metrics.items():
                metric_type = metric_key.split('/')[-1]
                
                if metric_type in weights:
                    mean_value = metric_stats.get('mean')
                    
                    if mean_value is not None:
                        weight = weights[metric_type]
                        
                        if metric_type == 'latency':
                            # 延遲轉換為評分 (越低越好)
                            score = max(0.0, min(1.0, 2.0 - (mean_value / 3000.0)))
                        elif metric_type == 'error_rate':
                            # 錯誤率轉換為評分 (越低越好)
                            score = max(0.0, 1.0 - mean_value)
                        else:
                            # success_rate, accuracy (越高越好)
                            score = min(1.0, mean_value)
                        
                        scores.append(score * weight)
                        total_weight += weight
            
            if total_weight > 0:
                return sum(scores) / total_weight
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating capability score: {e}")
            return None
    
    def _update_stats(self, result: UpdateResult):
        """更新統計信息"""
        self.update_stats['total_updates'] += 1
        
        if result.success:
            self.update_stats['successful_updates'] += 1
        else:
            self.update_stats['failed_updates'] += 1
        
        # 更新平均執行時間
        total_time = self.update_stats['average_execution_time'] * (self.update_stats['total_updates'] - 1)
        self.update_stats['average_execution_time'] = (total_time + result.execution_time_ms) / self.update_stats['total_updates']
    
    def _handle_performance_alert(self, message: str, alert_data: Dict[str, Any]):
        """處理性能告警"""
        try:
            provider = alert_data.get('provider')
            model_id = alert_data.get('model_id')
            
            if provider and model_id:
                # 創建告警驅動的更新任務
                asyncio.create_task(self._create_update_task(
                    provider=provider,
                    model_id=model_id,
                    update_type=ChangeType.PERFORMANCE_UPDATE,
                    trigger=UpdateTrigger.ALERT_BASED,
                    priority=1,  # 高優先級
                    context={
                        'alert_message': message,
                        'alert_data': alert_data,
                        'severity': alert_data.get('severity', 'medium')
                    }
                ))
        except Exception as e:
            self.logger.error(f"❌ Error handling performance alert: {e}")
    
    async def _process_scheduled_updates(self):
        """處理預定的更新"""
        # 檢查是否有需要執行的預定任務
        current_time = datetime.now(timezone.utc)
        
        for task in list(self.task_queue):
            if task.scheduled_at and task.scheduled_at <= current_time:
                # 移動到隊列前端
                self.task_queue.remove(task)
                self.task_queue.insert(0, task)
    
    def get_update_status(self) -> Dict[str, Any]:
        """獲取更新器狀態"""
        return {
            'running': self._running,
            'active_tasks': len(self.active_tasks),
            'queued_tasks': len(self.task_queue),
            'enabled_rules': len([r for r in self.update_rules.values() if r.enabled]),
            'total_rules': len(self.update_rules),
            'statistics': self.update_stats.copy(),
            'worker_threads': self.max_concurrent_updates
        }
    
    def get_rule_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取規則狀態"""
        return {
            rule_id: {
                'enabled': rule.enabled,
                'trigger_type': rule.trigger_type.value,
                'strategy': rule.strategy.value,
                'priority': rule.priority,
                'cooldown_minutes': rule.cooldown_minutes,
                'conditions': rule.conditions
            }
            for rule_id, rule in self.update_rules.items()
        }
    
    async def manual_update_request(
        self,
        provider: str,
        model_id: str,
        update_type: ChangeType = ChangeType.PERFORMANCE_UPDATE,
        priority: int = 1
    ) -> str:
        """手動請求更新"""
        task_id = await self._create_update_task(
            provider=provider,
            model_id=model_id,
            update_type=update_type,
            trigger=UpdateTrigger.MANUAL_REQUEST,
            priority=priority,
            context={'requested_by': 'manual'}
        )
        
        self.logger.info(f"✅ Manual update request created: {task_id}")
        return task_id