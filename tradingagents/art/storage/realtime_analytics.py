#!/usr/bin/env python3
"""
Real-time Analytics Engine - 實時數據分析引擎
天工 (TianGong) - 為ART存儲系統提供企業級實時數據分析

此模組提供：
1. RealTimeEventProcessor - 實時事件處理器
2. StreamingAnalyzer - 流式數據分析器
3. MetricsCollector - 實時指標收集器
4. AlertingSystem - 智能警報系統
5. DataStreamManager - 數據流管理器
6. AggregationEngine - 實時聚合引擎
"""

from typing import Dict, Any, List, Optional, Union, Tuple, AsyncGenerator, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import statistics
import math
from collections import defaultdict, deque, OrderedDict
import heapq
import weakref
from concurrent.futures import ThreadPoolExecutor, Future
import contextlib
import threading
import uuid

class EventType(Enum):
    """事件類型"""
    TRAJECTORY_CREATED = "trajectory_created"
    REWARD_UPDATED = "reward_updated"
    USER_ACTION = "user_action"
    SYSTEM_ALERT = "system_alert"
    PERFORMANCE_METRIC = "performance_metric"
    MARKET_DATA = "market_data"
    ANALYSIS_COMPLETED = "analysis_completed"
    ERROR_OCCURRED = "error_occurred"

class AnalyticsLevel(Enum):
    """分析級別"""
    BASIC = "basic"          # 基本統計
    DETAILED = "detailed"    # 詳細分析
    ADVANCED = "advanced"    # 高級分析
    PREDICTIVE = "predictive" # 預測分析

class AlertSeverity(Enum):
    """警報嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class RealTimeEvent:
    """實時事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.USER_ACTION
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    source: str = "unknown"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age(self) -> float:
        """事件年齡（秒）"""
        return time.time() - self.timestamp

@dataclass
class MetricPoint:
    """指標數據點"""
    timestamp: float
    value: Union[int, float, str]
    metric_name: str
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Alert:
    """警報"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    severity: AlertSeverity = AlertSeverity.INFO
    message: str = ""
    timestamp: float = field(default_factory=time.time)
    source: str = "system"
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    tags: Set[str] = field(default_factory=set)
    resolved: bool = False
    resolved_at: Optional[float] = None

class RealTimeEventProcessor:
    """實時事件處理器"""
    
    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size
        self.event_queue = asyncio.Queue(maxsize=max_queue_size)
        self.event_handlers: Dict[EventType, List[Callable]] = defaultdict(list)
        self.processing_stats = {
            'events_processed': 0,
            'events_failed': 0,
            'avg_processing_time': 0.0,
            'queue_size': 0
        }
        self._processing_times = deque(maxlen=1000)
        self._lock = asyncio.Lock()
        self._processing_task = None
        self._is_running = False
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """註冊事件處理器"""
        self.event_handlers[event_type].append(handler)
    
    async def emit_event(self, event: RealTimeEvent):
        """發送事件"""
        try:
            await self.event_queue.put(event)
        except asyncio.QueueFull:
            logging.warning(f"Event queue full, dropping event {event.event_id}")
    
    async def start_processing(self):
        """開始事件處理"""
        if self._is_running:
            return
        
        self._is_running = True
        self._processing_task = asyncio.create_task(self._process_events())
    
    async def stop_processing(self):
        """停止事件處理"""
        self._is_running = False
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
    
    async def _process_events(self):
        """處理事件循環"""
        while self._is_running:
            try:
                # 獲取事件（帶超時）
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 處理事件
                start_time = time.time()
                await self._handle_event(event)
                processing_time = time.time() - start_time
                
                # 更新統計
                async with self._lock:
                    self.processing_stats['events_processed'] += 1
                    self._processing_times.append(processing_time)
                    self.processing_stats['avg_processing_time'] = statistics.mean(
                        self._processing_times
                    )
                    self.processing_stats['queue_size'] = self.event_queue.qsize()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Event processing error: {e}")
                async with self._lock:
                    self.processing_stats['events_failed'] += 1
    
    async def _handle_event(self, event: RealTimeEvent):
        """處理單個事件"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        if not handlers:
            return
        
        # 並行執行所有處理器
        tasks = []
        for handler in handlers:
            tasks.append(self._safe_execute_handler(handler, event))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _safe_execute_handler(self, handler: Callable, event: RealTimeEvent):
        """安全執行處理器"""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logging.error(f"Handler execution error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取處理統計"""
        return {
            **self.processing_stats,
            'is_running': self._is_running,
            'handlers_count': sum(len(handlers) for handlers in self.event_handlers.values())
        }

class StreamingAnalyzer:
    """流式數據分析器"""
    
    def __init__(self, window_size: int = 3600):  # 1小時窗口
        self.window_size = window_size
        self.data_windows: Dict[str, deque] = defaultdict(lambda: deque())
        self.analysis_results: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    async def add_data_point(self, metric_name: str, point: MetricPoint):
        """添加數據點"""
        async with self._lock:
            window = self.data_windows[metric_name]
            
            # 添加新數據點
            window.append(point)
            
            # 清理過期數據
            current_time = time.time()
            while window and (current_time - window[0].timestamp) > self.window_size:
                window.popleft()
            
            # 觸發分析
            await self._analyze_window(metric_name)
    
    async def _analyze_window(self, metric_name: str):
        """分析窗口數據"""
        window = self.data_windows[metric_name]
        
        if not window:
            return
        
        # 提取數值數據
        values = []
        for point in window:
            if isinstance(point.value, (int, float)):
                values.append(point.value)
        
        if not values:
            return
        
        # 基本統計分析
        analysis = {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0,
            'latest': values[-1] if values else None,
            'trend': self._calculate_trend(values),
            'anomalies': self._detect_anomalies(values)
        }
        
        # 時間序列分析
        if len(values) > 5:
            analysis['moving_average_5'] = statistics.mean(values[-5:])
        if len(values) > 10:
            analysis['moving_average_10'] = statistics.mean(values[-10:])
        
        self.analysis_results[metric_name] = analysis
    
    def _calculate_trend(self, values: List[float]) -> str:
        """計算趨勢"""
        if len(values) < 2:
            return "stable"
        
        # 簡單線性回歸計算趨勢
        n = len(values)
        x = list(range(n))
        
        # 計算斜率
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return "stable"
        
        slope = numerator / denominator
        
        if slope > 0.01:
            return "increasing"
        elif slope < -0.01:
            return "decreasing"
        else:
            return "stable"
    
    def _detect_anomalies(self, values: List[float]) -> List[Dict[str, Any]]:
        """檢測異常值"""
        if len(values) < 5:
            return []
        
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        
        anomalies = []
        threshold = 2 * std  # 2西格馬規則
        
        for i, value in enumerate(values):
            if abs(value - mean) > threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'deviation': abs(value - mean),
                    'z_score': (value - mean) / std if std > 0 else 0
                })
        
        return anomalies
    
    def get_analysis(self, metric_name: str) -> Optional[Dict[str, Any]]:
        """獲取分析結果"""
        return self.analysis_results.get(metric_name)
    
    def get_all_analyses(self) -> Dict[str, Any]:
        """獲取所有分析結果"""
        return self.analysis_results.copy()

class MetricsCollector:
    """實時指標收集器"""
    
    def __init__(self, collection_interval: float = 10.0):
        self.collection_interval = collection_interval
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.collectors: List[Callable] = []
        self._collection_task = None
        self._is_running = False
    
    def register_collector(self, collector: Callable):
        """註冊指標收集器"""
        self.collectors.append(collector)
    
    async def record_metric(self, name: str, value: Union[int, float], 
                           labels: Dict[str, str] = None):
        """記錄指標"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            metric_name=name,
            labels=labels or {}
        )
        
        self.metrics[name].append(point)
    
    async def start_collection(self):
        """開始指標收集"""
        if self._is_running:
            return
        
        self._is_running = True
        self._collection_task = asyncio.create_task(self._collect_metrics())
    
    async def stop_collection(self):
        """停止指標收集"""
        self._is_running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
    
    async def _collect_metrics(self):
        """收集指標循環"""
        while self._is_running:
            try:
                # 執行所有收集器
                for collector in self.collectors:
                    try:
                        if asyncio.iscoroutinefunction(collector):
                            await collector(self)
                        else:
                            collector(self)
                    except Exception as e:
                        logging.error(f"Metric collection error: {e}")
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
    
    def get_latest_value(self, metric_name: str) -> Optional[float]:
        """獲取最新指標值"""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return None
        
        latest_point = self.metrics[metric_name][-1]
        if isinstance(latest_point.value, (int, float)):
            return float(latest_point.value)
        return None
    
    def get_metric_history(self, metric_name: str, 
                          duration: float = 3600) -> List[MetricPoint]:
        """獲取指標歷史"""
        if metric_name not in self.metrics:
            return []
        
        cutoff_time = time.time() - duration
        return [
            point for point in self.metrics[metric_name]
            if point.timestamp >= cutoff_time
        ]

class AlertingSystem:
    """智能警報系統"""
    
    def __init__(self):
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.alert_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
    
    def add_alert_rule(self, metric_name: str, condition: str, 
                      threshold: float, severity: AlertSeverity,
                      message: str = None):
        """添加警報規則"""
        self.alert_rules[f"{metric_name}_{condition}"] = {
            'metric_name': metric_name,
            'condition': condition,  # 'gt', 'lt', 'eq', 'anomaly'
            'threshold': threshold,
            'severity': severity,
            'message': message or f"{metric_name} {condition} {threshold}"
        }
    
    def register_alert_handler(self, handler: Callable):
        """註冊警報處理器"""
        self.alert_handlers.append(handler)
    
    async def check_metric(self, metric_name: str, value: float, 
                          analysis: Dict[str, Any] = None):
        """檢查指標是否觸發警報"""
        async with self._lock:
            for rule_id, rule in self.alert_rules.items():
                if rule['metric_name'] != metric_name:
                    continue
                
                triggered = False
                condition = rule['condition']
                threshold = rule['threshold']
                
                # 檢查條件
                if condition == 'gt' and value > threshold:
                    triggered = True
                elif condition == 'lt' and value < threshold:
                    triggered = True
                elif condition == 'eq' and abs(value - threshold) < 0.001:
                    triggered = True
                elif condition == 'anomaly' and analysis:
                    # 檢查是否為異常值
                    anomalies = analysis.get('anomalies', [])
                    if any(abs(a['z_score']) > threshold for a in anomalies):
                        triggered = True
                
                if triggered:
                    await self._create_alert(rule, value)
                else:
                    # 檢查是否需要解除警報
                    await self._resolve_alert(rule_id)
    
    async def _create_alert(self, rule: Dict[str, Any], actual_value: float):
        """創建警報"""
        rule_id = f"{rule['metric_name']}_{rule['condition']}"
        
        # 檢查是否已有活躍警報
        if rule_id in self.active_alerts and not self.active_alerts[rule_id].resolved:
            return
        
        alert = Alert(
            severity=rule['severity'],
            message=rule['message'],
            source="alerting_system",
            metric_name=rule['metric_name'],
            threshold_value=rule['threshold'],
            actual_value=actual_value
        )
        
        self.active_alerts[rule_id] = alert
        self.alert_history.append(alert)
        
        # 通知處理器
        await self._notify_handlers(alert)
    
    async def _resolve_alert(self, rule_id: str):
        """解除警報"""
        if rule_id in self.active_alerts and not self.active_alerts[rule_id].resolved:
            alert = self.active_alerts[rule_id]
            alert.resolved = True
            alert.resolved_at = time.time()
            
            # 通知處理器
            await self._notify_handlers(alert)
    
    async def _notify_handlers(self, alert: Alert):
        """通知警報處理器"""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logging.error(f"Alert handler error: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍警報"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_alert_history(self, duration: float = 3600) -> List[Alert]:
        """獲取警報歷史"""
        cutoff_time = time.time() - duration
        return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]

class AggregationEngine:
    """實時聚合引擎"""
    
    def __init__(self):
        self.aggregations: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def setup_aggregation(self, agg_name: str, source_metric: str,
                               agg_type: str, window_size: int = 60,
                               group_by: List[str] = None):
        """設置聚合"""
        async with self._lock:
            self.aggregations[agg_name] = {
                'source_metric': source_metric,
                'agg_type': agg_type,  # 'sum', 'avg', 'min', 'max', 'count'
                'window_size': window_size,
                'group_by': group_by or [],
                'data_points': deque(),
                'results': {}
            }
    
    async def process_data_point(self, metric_name: str, point: MetricPoint):
        """處理數據點"""
        async with self._lock:
            # 查找相關聚合
            for agg_name, agg_config in self.aggregations.items():
                if agg_config['source_metric'] == metric_name:
                    await self._update_aggregation(agg_name, point)
    
    async def _update_aggregation(self, agg_name: str, point: MetricPoint):
        """更新聚合"""
        agg_config = self.aggregations[agg_name]
        
        # 添加數據點
        agg_config['data_points'].append(point)
        
        # 清理過期數據
        current_time = time.time()
        window_size = agg_config['window_size']
        
        while (agg_config['data_points'] and 
               (current_time - agg_config['data_points'][0].timestamp) > window_size):
            agg_config['data_points'].popleft()
        
        # 計算聚合結果
        await self._calculate_aggregation(agg_name)
    
    async def _calculate_aggregation(self, agg_name: str):
        """計算聚合結果"""
        agg_config = self.aggregations[agg_name]
        data_points = list(agg_config['data_points'])
        
        if not data_points:
            return
        
        agg_type = agg_config['agg_type']
        group_by = agg_config['group_by']
        
        # 根據分組字段分組
        groups = defaultdict(list)
        
        for point in data_points:
            if isinstance(point.value, (int, float)):
                if group_by:
                    # 創建分組鍵
                    group_key = tuple(point.labels.get(field, 'unknown') for field in group_by)
                else:
                    group_key = 'all'
                
                groups[group_key].append(point.value)
        
        # 計算每組的聚合值
        results = {}
        
        for group_key, values in groups.items():
            if agg_type == 'sum':
                result = sum(values)
            elif agg_type == 'avg':
                result = statistics.mean(values)
            elif agg_type == 'min':
                result = min(values)
            elif agg_type == 'max':
                result = max(values)
            elif agg_type == 'count':
                result = len(values)
            else:
                result = None
            
            results[group_key] = result
        
        agg_config['results'] = results
    
    def get_aggregation_result(self, agg_name: str) -> Optional[Dict[str, Any]]:
        """獲取聚合結果"""
        if agg_name in self.aggregations:
            return self.aggregations[agg_name]['results']
        return None

class DataStreamManager:
    """數據流管理器"""
    
    def __init__(self):
        self.event_processor = RealTimeEventProcessor()
        self.streaming_analyzer = StreamingAnalyzer()
        self.metrics_collector = MetricsCollector()
        self.alerting_system = AlertingSystem()
        self.aggregation_engine = AggregationEngine()
        
        self._setup_integration()
    
    def _setup_integration(self):
        """設置組件集成"""
        # 事件處理器處理指標事件
        async def handle_metric_event(event: RealTimeEvent):
            if event.event_type == EventType.PERFORMANCE_METRIC:
                metric_name = event.data.get('metric_name')
                value = event.data.get('value')
                
                if metric_name and isinstance(value, (int, float)):
                    # 記錄到指標收集器
                    await self.metrics_collector.record_metric(metric_name, value)
                    
                    # 創建指標點
                    point = MetricPoint(
                        timestamp=event.timestamp,
                        value=value,
                        metric_name=metric_name,
                        labels=event.data.get('labels', {})
                    )
                    
                    # 流式分析
                    await self.streaming_analyzer.add_data_point(metric_name, point)
                    
                    # 聚合處理
                    await self.aggregation_engine.process_data_point(metric_name, point)
                    
                    # 警報檢查
                    analysis = self.streaming_analyzer.get_analysis(metric_name)
                    await self.alerting_system.check_metric(metric_name, value, analysis)
        
        self.event_processor.register_handler(EventType.PERFORMANCE_METRIC, handle_metric_event)
        
        # 警報處理器
        def handle_alert(alert: Alert):
            logging.info(f"Alert: {alert.severity.value} - {alert.message}")
        
        self.alerting_system.register_alert_handler(handle_alert)
    
    async def start(self):
        """啟動數據流管理器"""
        await self.event_processor.start_processing()
        await self.metrics_collector.start_collection()
    
    async def stop(self):
        """停止數據流管理器"""
        await self.event_processor.stop_processing()
        await self.metrics_collector.stop_collection()
    
    async def emit_metric(self, metric_name: str, value: Union[int, float],
                         labels: Dict[str, str] = None, 
                         user_id: str = None):
        """發送指標事件"""
        event = RealTimeEvent(
            event_type=EventType.PERFORMANCE_METRIC,
            data={
                'metric_name': metric_name,
                'value': value,
                'labels': labels or {}
            },
            user_id=user_id
        )
        
        await self.event_processor.emit_event(event)
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """獲取綜合統計"""
        return {
            'event_processor': self.event_processor.get_stats(),
            'streaming_analysis': self.streaming_analyzer.get_all_analyses(),
            'active_alerts': len(self.alerting_system.get_active_alerts()),
            'metrics_count': len(self.metrics_collector.metrics),
            'aggregations': list(self.aggregation_engine.aggregations.keys())
        }

# 工廠函數
def create_realtime_analytics(
    max_queue_size: int = 10000,
    collection_interval: float = 10.0,
    window_size: int = 3600
) -> DataStreamManager:
    """創建實時分析系統"""
    manager = DataStreamManager()
    manager.event_processor.max_queue_size = max_queue_size
    manager.metrics_collector.collection_interval = collection_interval
    manager.streaming_analyzer.window_size = window_size
    
    return manager

def create_event_processor(max_queue_size: int = 10000) -> RealTimeEventProcessor:
    """創建事件處理器"""
    return RealTimeEventProcessor(max_queue_size)

def create_streaming_analyzer(window_size: int = 3600) -> StreamingAnalyzer:
    """創建流式分析器"""
    return StreamingAnalyzer(window_size)

def create_metrics_collector(collection_interval: float = 10.0) -> MetricsCollector:
    """創建指標收集器"""
    return MetricsCollector(collection_interval)

def create_alerting_system() -> AlertingSystem:
    """創建警報系統"""
    return AlertingSystem()