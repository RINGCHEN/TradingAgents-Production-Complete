#!/usr/bin/env python3
"""
Performance Monitoring System
性能指標收集和更新系統 - GPT-OSS整合任務1.2.2
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager

from ..database.model_capability_db import ModelCapabilityDB
from ..database.task_metadata_db import TaskMetadataDB

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """指標類型"""
    LATENCY = "latency"
    ACCURACY = "accuracy"
    COST = "cost"
    SUCCESS_RATE = "success_rate"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"

@dataclass
class PerformanceMetric:
    """性能指標"""
    provider: str
    model_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_type: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'provider': self.provider,
            'model_id': self.model_id,
            'metric_type': self.metric_type.value,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'task_type': self.task_type,
            'user_id': self.user_id,
            'metadata': self.metadata
        }

@dataclass 
class PerformanceWindow:
    """性能統計窗口"""
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    window_size: int = 100
    
    def add_value(self, value: float, timestamp: Optional[datetime] = None):
        """添加新值"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        self.values.append(value)
        self.timestamps.append(timestamp)
        
        # 保持窗口大小
        if len(self.values) > self.window_size:
            self.values.pop(0)
            self.timestamps.pop(0)
    
    def get_statistics(self) -> Dict[str, float]:
        """獲取統計信息"""
        if not self.values:
            return {}
        
        return {
            'mean': statistics.mean(self.values),
            'median': statistics.median(self.values),
            'std': statistics.stdev(self.values) if len(self.values) > 1 else 0.0,
            'min': min(self.values),
            'max': max(self.values),
            'count': len(self.values),
            'p95': statistics.quantiles(self.values, n=20)[18] if len(self.values) >= 20 else max(self.values),
            'p99': statistics.quantiles(self.values, n=100)[98] if len(self.values) >= 100 else max(self.values)
        }
    
    def clear_old_values(self, max_age_hours: int = 24):
        """清理舊值"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        
        # 找到要保留的值
        keep_indices = []
        for i, timestamp in enumerate(self.timestamps):
            if timestamp >= cutoff_time:
                keep_indices.append(i)
        
        # 更新列表
        self.values = [self.values[i] for i in keep_indices]
        self.timestamps = [self.timestamps[i] for i in keep_indices]

class PerformanceCollector:
    """性能數據收集器"""
    
    def __init__(self, buffer_size: int = 1000, flush_interval: int = 60):
        """
        初始化性能收集器
        
        Args:
            buffer_size: 緩衝區大小
            flush_interval: 刷新間隔（秒）
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.metrics_buffer: List[PerformanceMetric] = []
        self.windows: Dict[str, PerformanceWindow] = {}
        self.logger = logger
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    def start(self):
        """啟動收集器"""
        if not self._running:
            self._running = True
            self._flush_task = asyncio.create_task(self._periodic_flush())
            self.logger.info("✅ Performance collector started")
    
    async def stop(self):
        """停止收集器"""
        if self._running:
            self._running = False
            if self._flush_task:
                self._flush_task.cancel()
                try:
                    await self._flush_task
                except asyncio.CancelledError:
                    pass
            
            # 最終刷新
            await self._flush_buffer()
            self.logger.info("✅ Performance collector stopped")
    
    def record_metric(
        self,
        provider: str,
        model_id: str,
        metric_type: MetricType,
        value: float,
        task_type: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """記錄性能指標"""
        metric = PerformanceMetric(
            provider=provider,
            model_id=model_id,
            metric_type=metric_type,
            value=value,
            task_type=task_type,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        self.metrics_buffer.append(metric)
        
        # 更新滑動窗口
        window_key = f"{provider}/{model_id}/{metric_type.value}"
        if window_key not in self.windows:
            self.windows[window_key] = PerformanceWindow()
        
        self.windows[window_key].add_value(value, metric.timestamp)
        
        # 檢查是否需要刷新
        if len(self.metrics_buffer) >= self.buffer_size:
            asyncio.create_task(self._flush_buffer())
    
    def get_current_statistics(
        self,
        provider: str,
        model_id: str,
        metric_type: MetricType
    ) -> Dict[str, float]:
        """獲取當前統計信息"""
        window_key = f"{provider}/{model_id}/{metric_type.value}"
        window = self.windows.get(window_key)
        
        if window:
            return window.get_statistics()
        return {}
    
    def get_all_statistics(self) -> Dict[str, Dict[str, float]]:
        """獲取所有統計信息"""
        stats = {}
        for window_key, window in self.windows.items():
            stats[window_key] = window.get_statistics()
        return stats
    
    async def _periodic_flush(self):
        """定期刷新緩衝區"""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
                self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in periodic flush: {e}")
    
    async def _flush_buffer(self):
        """刷新緩衝區到數據庫"""
        if not self.metrics_buffer:
            return
        
        try:
            # 這裡可以添加數據庫寫入邏輯
            flushed_count = len(self.metrics_buffer)
            self.metrics_buffer.clear()
            
            self.logger.debug(f"Flushed {flushed_count} performance metrics")
            
        except Exception as e:
            self.logger.error(f"❌ Error flushing performance buffer: {e}")
    
    def _cleanup_old_data(self):
        """清理舊數據"""
        try:
            for window in self.windows.values():
                window.clear_old_values(max_age_hours=24)
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old data: {e}")

class PerformanceMonitor:
    """
    性能監控器
    
    功能：
    1. 實時監控模型性能
    2. 自動收集和聚合指標
    3. 觸發性能更新和告警
    4. 提供性能分析和報告
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        task_db: Optional[TaskMetadataDB] = None,
        collector: Optional[PerformanceCollector] = None
    ):
        """
        初始化性能監控器
        
        Args:
            model_db: 模型能力數據庫
            task_db: 任務元數據數據庫
            collector: 性能收集器
        """
        self.model_db = model_db or ModelCapabilityDB()
        self.task_db = task_db or TaskMetadataDB()
        self.collector = collector or PerformanceCollector()
        
        # 性能閾值配置
        self.thresholds = {
            MetricType.LATENCY: 5000.0,  # 5秒
            MetricType.ACCURACY: 0.8,     # 80%
            MetricType.SUCCESS_RATE: 0.95, # 95%
            MetricType.ERROR_RATE: 0.05   # 5%
        }
        
        # 告警回調
        self.alert_callbacks: List[Callable] = []
        
        self.logger = logger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """啟動性能監控"""
        if not self._running:
            self._running = True
            self.collector.start()
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("✅ Performance monitor started")
    
    async def stop(self):
        """停止性能監控"""
        if self._running:
            self._running = False
            
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            await self.collector.stop()
            self.logger.info("✅ Performance monitor stopped")
    
    @asynccontextmanager
    async def measure_request(
        self,
        provider: str,
        model_id: str,
        task_type: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """
        測量請求性能的上下文管理器
        
        Usage:
            async with monitor.measure_request("openai", "gpt-4") as ctx:
                response = await llm_client.analyze(...)
                ctx.set_success(True)
                ctx.set_accuracy(0.95)
                ctx.set_cost(0.02)
        """
        start_time = time.time()
        
        class RequestContext:
            def __init__(self):
                self.success = False
                self.accuracy: Optional[float] = None
                self.cost: Optional[float] = None
                self.metadata: Dict[str, Any] = {}
            
            def set_success(self, success: bool):
                self.success = success
            
            def set_accuracy(self, accuracy: float):
                self.accuracy = accuracy
            
            def set_cost(self, cost: float):
                self.cost = cost
            
            def add_metadata(self, key: str, value: Any):
                self.metadata[key] = value
        
        context = RequestContext()
        
        try:
            yield context
            
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            # 記錄延遲指標
            self.collector.record_metric(
                provider=provider,
                model_id=model_id,
                metric_type=MetricType.LATENCY,
                value=latency_ms,
                task_type=task_type,
                user_id=user_id,
                metadata=context.metadata
            )
            
            # 記錄成功率指標
            self.collector.record_metric(
                provider=provider,
                model_id=model_id,
                metric_type=MetricType.SUCCESS_RATE,
                value=1.0 if context.success else 0.0,
                task_type=task_type,
                user_id=user_id,
                metadata=context.metadata
            )
            
            # 記錄錯誤率指標
            self.collector.record_metric(
                provider=provider,
                model_id=model_id,
                metric_type=MetricType.ERROR_RATE,
                value=0.0 if context.success else 1.0,
                task_type=task_type,
                user_id=user_id,
                metadata=context.metadata
            )
            
            # 記錄準確性指標
            if context.accuracy is not None:
                self.collector.record_metric(
                    provider=provider,
                    model_id=model_id,
                    metric_type=MetricType.ACCURACY,
                    value=context.accuracy,
                    task_type=task_type,
                    user_id=user_id,
                    metadata=context.metadata
                )
            
            # 記錄成本指標
            if context.cost is not None:
                self.collector.record_metric(
                    provider=provider,
                    model_id=model_id,
                    metric_type=MetricType.COST,
                    value=context.cost,
                    task_type=task_type,
                    user_id=user_id,
                    metadata=context.metadata
                )
    
    def add_alert_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """添加告警回調函數"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable):
        """移除告警回調函數"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                await self._check_performance_thresholds()
                await self._update_model_capabilities()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
    
    async def _check_performance_thresholds(self):
        """檢查性能閾值"""
        try:
            all_stats = self.collector.get_all_statistics()
            
            for window_key, stats in all_stats.items():
                if not stats:
                    continue
                
                parts = window_key.split('/')
                if len(parts) != 3:
                    continue
                
                provider, model_id, metric_type_str = parts
                
                try:
                    metric_type = MetricType(metric_type_str)
                except ValueError:
                    continue
                
                # 檢查閾值
                threshold = self.thresholds.get(metric_type)
                if threshold is None:
                    continue
                
                current_value = stats.get('mean', 0)
                
                # 檢查是否超過閾值
                if self._is_threshold_exceeded(metric_type, current_value, threshold):
                    await self._trigger_alert(
                        provider=provider,
                        model_id=model_id,
                        metric_type=metric_type,
                        current_value=current_value,
                        threshold=threshold,
                        statistics=stats
                    )
                    
        except Exception as e:
            self.logger.error(f"❌ Error checking performance thresholds: {e}")
    
    def _is_threshold_exceeded(
        self,
        metric_type: MetricType,
        current_value: float,
        threshold: float
    ) -> bool:
        """檢查是否超過閾值"""
        if metric_type in [MetricType.LATENCY, MetricType.ERROR_RATE]:
            # 越低越好的指標
            return current_value > threshold
        else:
            # 越高越好的指標
            return current_value < threshold
    
    async def _trigger_alert(
        self,
        provider: str,
        model_id: str,
        metric_type: MetricType,
        current_value: float,
        threshold: float,
        statistics: Dict[str, float]
    ):
        """觸發告警"""
        alert_data = {
            'provider': provider,
            'model_id': model_id,
            'metric_type': metric_type.value,
            'current_value': current_value,
            'threshold': threshold,
            'statistics': statistics,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'severity': self._calculate_severity(metric_type, current_value, threshold)
        }
        
        alert_message = (
            f"Performance Alert: {provider}/{model_id} "
            f"{metric_type.value} = {current_value:.3f} "
            f"(threshold: {threshold:.3f})"
        )
        
        self.logger.warning(f"⚠️ {alert_message}")
        
        # 調用告警回調
        for callback in self.alert_callbacks:
            try:
                callback(alert_message, alert_data)
            except Exception as e:
                self.logger.error(f"❌ Error in alert callback: {e}")
    
    def _calculate_severity(
        self,
        metric_type: MetricType,
        current_value: float,
        threshold: float
    ) -> str:
        """計算告警嚴重程度"""
        if metric_type in [MetricType.LATENCY, MetricType.ERROR_RATE]:
            ratio = current_value / threshold
        else:
            ratio = threshold / max(current_value, 0.001)
        
        if ratio >= 2.0:
            return "critical"
        elif ratio >= 1.5:
            return "high"
        elif ratio >= 1.2:
            return "medium"
        else:
            return "low"
    
    async def _update_model_capabilities(self):
        """更新模型能力數據庫"""
        try:
            all_stats = self.collector.get_all_statistics()
            
            # 按模型分組統計
            model_stats = {}
            for window_key, stats in all_stats.items():
                parts = window_key.split('/')
                if len(parts) != 3:
                    continue
                
                provider, model_id, metric_type_str = parts
                model_key = f"{provider}/{model_id}"
                
                if model_key not in model_stats:
                    model_stats[model_key] = {}
                
                model_stats[model_key][metric_type_str] = stats
            
            # 更新每個模型的能力數據
            for model_key, stats in model_stats.items():
                provider, model_id = model_key.split('/', 1)
                
                updates = {}
                
                # 更新平均延遲
                if 'latency' in stats:
                    latency_stats = stats['latency']
                    if 'mean' in latency_stats:
                        updates['avg_latency_ms'] = latency_stats['mean']
                
                # 更新能力評分（基於多個指標的綜合評分）
                capability_score = self._calculate_capability_score(stats)
                if capability_score is not None:
                    updates['capability_score'] = capability_score
                
                # 執行更新
                if updates:
                    await self.model_db.update_model_capability(
                        provider=provider,
                        model_id=model_id,
                        updates=updates
                    )
                    
        except Exception as e:
            self.logger.error(f"❌ Error updating model capabilities: {e}")
    
    def _calculate_capability_score(self, stats: Dict[str, Dict[str, float]]) -> Optional[float]:
        """基於性能統計計算能力評分"""
        try:
            scores = []
            weights = {
                'accuracy': 0.4,
                'success_rate': 0.3,
                'latency': 0.2,
                'error_rate': 0.1
            }
            
            total_weight = 0.0
            
            for metric_name, weight in weights.items():
                if metric_name in stats:
                    metric_stats = stats[metric_name]
                    mean_value = metric_stats.get('mean')
                    
                    if mean_value is not None:
                        # 根據指標類型計算評分
                        if metric_name == 'latency':
                            # 延遲轉換為評分 (越低越好)
                            score = max(0.0, min(1.0, 2.0 - (mean_value / 3000.0)))
                        elif metric_name == 'error_rate':
                            # 錯誤率轉換為評分 (越低越好)
                            score = max(0.0, 1.0 - mean_value)
                        else:
                            # accuracy, success_rate (越高越好)
                            score = min(1.0, mean_value)
                        
                        scores.append(score * weight)
                        total_weight += weight
            
            if total_weight > 0:
                return sum(scores) / total_weight
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating capability score: {e}")
            return None
    
    async def get_performance_report(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        獲取性能報告
        
        Args:
            provider: 提供商過濾
            model_id: 模型過濾
            hours_back: 回溯小時數
            
        Returns:
            性能報告
        """
        try:
            all_stats = self.collector.get_all_statistics()
            
            # 過濾統計數據
            filtered_stats = {}
            for window_key, stats in all_stats.items():
                parts = window_key.split('/')
                if len(parts) != 3:
                    continue
                
                key_provider, key_model_id, metric_type = parts
                
                # 應用過濾條件
                if provider and key_provider != provider:
                    continue
                if model_id and key_model_id != model_id:
                    continue
                
                filtered_stats[window_key] = stats
            
            # 生成報告
            report = {
                "summary": {
                    "total_metrics": len(filtered_stats),
                    "time_range_hours": hours_back,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                },
                "metrics": filtered_stats,
                "alerts": self._get_recent_alerts(),
                "recommendations": self._generate_recommendations(filtered_stats)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating performance report: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """獲取最近的告警（簡化實現）"""
        # 在實際實現中，這裡應該從告警存儲中獲取
        return []
    
    def _generate_recommendations(self, stats: Dict[str, Dict[str, float]]) -> List[str]:
        """基於性能統計生成建議"""
        recommendations = []
        
        try:
            for window_key, metric_stats in stats.items():
                if not metric_stats:
                    continue
                
                parts = window_key.split('/')
                if len(parts) != 3:
                    continue
                
                provider, model_id, metric_type = parts
                mean_value = metric_stats.get('mean', 0)
                
                # 基於不同指標生成建議
                if metric_type == 'latency' and mean_value > 3000:
                    recommendations.append(
                        f"Consider optimizing {provider}/{model_id} for better latency "
                        f"(current: {mean_value:.0f}ms)"
                    )
                
                elif metric_type == 'success_rate' and mean_value < 0.9:
                    recommendations.append(
                        f"Investigate reliability issues with {provider}/{model_id} "
                        f"(success rate: {mean_value:.1%})"
                    )
                
                elif metric_type == 'error_rate' and mean_value > 0.1:
                    recommendations.append(
                        f"High error rate detected for {provider}/{model_id} "
                        f"({mean_value:.1%})"
                    )
            
        except Exception as e:
            self.logger.error(f"❌ Error generating recommendations: {e}")
        
        return recommendations[:10]  # 限制建議數量
    
    def get_current_metrics(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """獲取當前指標"""
        all_stats = self.collector.get_all_statistics()
        
        if not provider and not model_id:
            return all_stats
        
        # 應用過濾
        filtered_stats = {}
        for window_key, stats in all_stats.items():
            parts = window_key.split('/')
            if len(parts) != 3:
                continue
            
            key_provider, key_model_id, metric_type = parts
            
            if provider and key_provider != provider:
                continue
            if model_id and key_model_id != model_id:
                continue
            
            filtered_stats[window_key] = stats
        
        return filtered_stats