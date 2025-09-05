#!/usr/bin/env python3
"""
Analyst Monitoring System - 分析師性能監控系統
天工 (TianGong) - 智能分析師實時監控與性能分析系統

此模組提供：
1. 實時性能監控和告警
2. 多維度指標追蹤
3. 異常檢測和自動恢復
4. 性能趨勢分析
5. 資源使用監控
"""

import asyncio
import logging
import time
import psutil
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Set
import json
import numpy as np
from collections import defaultdict, deque
import statistics
import weakref

from ..agents.analysts.base_analyst import AnalysisResult, AnalysisType
from .analyst_evaluation import AnalystEvaluation, EvaluationMetric


class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指標類型"""
    COUNTER = "counter"         # 計數器
    GAUGE = "gauge"             # 測量值
    HISTOGRAM = "histogram"     # 直方圖
    SUMMARY = "summary"         # 摘要


class MonitoringStatus(Enum):
    """監控狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class MetricPoint:
    """指標點"""
    timestamp: datetime
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'labels': self.labels
        }


@dataclass
class Alert:
    """告警"""
    alert_id: str
    analyst_id: str
    level: AlertLevel
    title: str
    description: str
    timestamp: datetime
    
    # 指標信息
    metric_name: str
    current_value: float
    threshold: float
    
    # 狀態
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolution_note: Optional[str] = None
    
    # 處理信息
    handler_called: bool = False
    auto_resolved: bool = False
    
    def resolve(self, note: str = None):
        """解決告警"""
        self.is_resolved = True
        self.resolved_at = datetime.now()
        self.resolution_note = note
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'analyst_id': self.analyst_id,
            'level': self.level.value,
            'title': self.title,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'metric_name': self.metric_name,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolution_note': self.resolution_note,
            'handler_called': self.handler_called,
            'auto_resolved': self.auto_resolved
        }


@dataclass
class MonitoringRule:
    """監控規則"""
    rule_id: str
    metric_name: str
    condition: str  # 'greater_than', 'less_than', 'equal', 'not_equal'
    threshold: float
    alert_level: AlertLevel
    alert_title: str
    alert_description: str
    
    # 觸發條件
    duration_seconds: int = 60  # 持續時間
    evaluation_window: int = 5  # 評估窗口大小
    
    # 狀態
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    
    def evaluate(self, recent_values: List[float]) -> bool:
        """評估規則"""
        
        if not self.enabled or not recent_values:
            return False
        
        # 獲取最新值
        current_value = recent_values[-1]
        
        # 評估條件
        if self.condition == 'greater_than':
            return current_value > self.threshold
        elif self.condition == 'less_than':
            return current_value < self.threshold
        elif self.condition == 'equal':
            return abs(current_value - self.threshold) < 1e-6
        elif self.condition == 'not_equal':
            return abs(current_value - self.threshold) >= 1e-6
        
        return False


class MetricStore:
    """指標存儲"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def record_metric(
        self, 
        metric_name: str, 
        value: float, 
        analyst_id: str = "global",
        labels: Dict[str, str] = None
    ):
        """記錄指標"""
        
        with self.lock:
            try:
                point = MetricPoint(
                    timestamp=datetime.now(),
                    value=value,
                    labels=labels or {}
                )
                
                # 使用 analyst_id 作為分組鍵
                self.metrics[metric_name][analyst_id].append(point)
                
                # 清理過期數據
                self._cleanup_expired_data(metric_name, analyst_id)
                
            except Exception as e:
                self.logger.error(f"記錄指標失敗: {str(e)}")
    
    def get_metric_values(
        self, 
        metric_name: str, 
        analyst_id: str = "global",
        duration: timedelta = timedelta(hours=1)
    ) -> List[MetricPoint]:
        """獲取指標值"""
        
        with self.lock:
            if metric_name not in self.metrics or analyst_id not in self.metrics[metric_name]:
                return []
            
            cutoff_time = datetime.now() - duration
            points = self.metrics[metric_name][analyst_id]
            
            # 過濾時間範圍內的點
            filtered_points = [
                point for point in points 
                if point.timestamp >= cutoff_time
            ]
            
            return list(filtered_points)
    
    def get_latest_value(
        self, 
        metric_name: str, 
        analyst_id: str = "global"
    ) -> Optional[float]:
        """獲取最新值"""
        
        with self.lock:
            if (metric_name not in self.metrics or 
                analyst_id not in self.metrics[metric_name] or
                not self.metrics[metric_name][analyst_id]):
                return None
            
            return self.metrics[metric_name][analyst_id][-1].value
    
    def get_aggregated_metrics(
        self, 
        metric_name: str, 
        analyst_id: str = "global",
        duration: timedelta = timedelta(hours=1),
        aggregation: str = "avg"
    ) -> Optional[float]:
        """獲取聚合指標"""
        
        points = self.get_metric_values(metric_name, analyst_id, duration)
        
        if not points:
            return None
        
        values = [point.value for point in points]
        
        if aggregation == "avg":
            return statistics.mean(values)
        elif aggregation == "sum":
            return sum(values)
        elif aggregation == "min":
            return min(values)
        elif aggregation == "max":
            return max(values)
        elif aggregation == "median":
            return statistics.median(values)
        elif aggregation == "std":
            return statistics.stdev(values) if len(values) > 1 else 0.0
        
        return None
    
    def list_metrics(self) -> Dict[str, List[str]]:
        """列出所有指標"""
        
        with self.lock:
            result = {}
            for metric_name, analyst_data in self.metrics.items():
                result[metric_name] = list(analyst_data.keys())
            return result
    
    def _cleanup_expired_data(self, metric_name: str, analyst_id: str):
        """清理過期數據"""
        
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        points = self.metrics[metric_name][analyst_id]
        
        # 移除過期點
        while points and points[0].timestamp < cutoff_time:
            points.popleft()


class PerformanceCollector:
    """性能數據收集器"""
    
    def __init__(self, metric_store: MetricStore):
        self.metric_store = metric_store
        self.logger = logging.getLogger(__name__)
        
        # 收集狀態
        self.is_collecting = False
        self.collection_task: Optional[asyncio.Task] = None
        self.collection_interval = 10  # 秒
    
    async def start_collection(self):
        """開始收集"""
        
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_task = asyncio.create_task(self._collection_loop())
            self.logger.info("性能數據收集已啟動")
    
    async def stop_collection(self):
        """停止收集"""
        
        if self.is_collecting:
            self.is_collecting = False
            
            if self.collection_task:
                self.collection_task.cancel()
                try:
                    await self.collection_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("性能數據收集已停止")
    
    async def _collection_loop(self):
        """收集循環"""
        
        while self.is_collecting:
            try:
                await self._collect_system_metrics()
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"收集系統指標失敗: {str(e)}")
                await asyncio.sleep(5)
    
    async def _collect_system_metrics(self):
        """收集系統指標"""
        
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metric_store.record_metric("system_cpu_percent", cpu_percent)
            
            # 內存使用
            memory = psutil.virtual_memory()
            self.metric_store.record_metric("system_memory_percent", memory.percent)
            self.metric_store.record_metric("system_memory_used_gb", memory.used / (1024**3))
            
            # 磁盤使用
            disk = psutil.disk_usage('/')
            self.metric_store.record_metric("system_disk_percent", 
                                          (disk.used / disk.total) * 100)
            
            # 網絡 I/O
            network = psutil.net_io_counters()
            self.metric_store.record_metric("system_network_bytes_sent", network.bytes_sent)
            self.metric_store.record_metric("system_network_bytes_recv", network.bytes_recv)
            
        except Exception as e:
            self.logger.error(f"收集系統指標失敗: {str(e)}")
    
    def record_analysis_metrics(self, analyst_id: str, result: AnalysisResult, execution_time: float):
        """記錄分析指標"""
        
        try:
            # 分析計數
            self.metric_store.record_metric("analyst_analysis_count", 1, analyst_id)
            
            # 執行時間
            self.metric_store.record_metric("analyst_execution_time_ms", execution_time, analyst_id)
            
            # 信心度
            self.metric_store.record_metric("analyst_confidence", result.confidence, analyst_id)
            
            # 成功指標
            success = 1.0 if result.confidence > 0.3 else 0.0
            self.metric_store.record_metric("analyst_success_rate", success, analyst_id)
            
            # 成本
            if result.cost_info:
                cost = result.cost_info.get('estimated_cost', 0.0)
                self.metric_store.record_metric("analyst_cost", cost, analyst_id)
            
            # 按分析類型分組
            analysis_type = result.analysis_type.value
            self.metric_store.record_metric(
                "analyst_analysis_by_type", 1, analyst_id, 
                labels={'analysis_type': analysis_type}
            )
            
        except Exception as e:
            self.logger.error(f"記錄分析指標失敗: {str(e)}")


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.rules: Dict[str, MonitoringRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.handlers: Dict[AlertLevel, List[Callable]] = defaultdict(list)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def add_rule(self, rule: MonitoringRule):
        """添加監控規則"""
        
        with self.lock:
            self.rules[rule.rule_id] = rule
            self.logger.info(f"添加監控規則: {rule.rule_id}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除監控規則"""
        
        with self.lock:
            if rule_id in self.rules:
                del self.rules[rule_id]
                self.logger.info(f"移除監控規則: {rule_id}")
                return True
            return False
    
    def add_handler(self, level: AlertLevel, handler: Callable[[Alert], None]):
        """添加告警處理器"""
        
        with self.lock:
            self.handlers[level].append(handler)
            self.logger.info(f"添加 {level.value} 級別告警處理器")
    
    def evaluate_rules(self, metric_name: str, analyst_id: str, recent_values: List[float]):
        """評估監控規則"""
        
        with self.lock:
            for rule in self.rules.values():
                if rule.metric_name == metric_name and rule.enabled:
                    try:
                        if rule.evaluate(recent_values):
                            self._trigger_alert(rule, analyst_id, recent_values[-1])
                    except Exception as e:
                        self.logger.error(f"評估規則失敗 {rule.rule_id}: {str(e)}")
    
    def _trigger_alert(self, rule: MonitoringRule, analyst_id: str, current_value: float):
        """觸發告警"""
        
        # 檢查是否已有相同的活躍告警
        alert_key = f"{rule.rule_id}_{analyst_id}"
        
        if alert_key in self.active_alerts:
            return  # 已有活躍告警，不重複觸發
        
        # 創建告警
        alert = Alert(
            alert_id=f"alert_{int(time.time())}_{alert_key}",
            analyst_id=analyst_id,
            level=rule.alert_level,
            title=rule.alert_title,
            description=rule.alert_description.format(
                analyst_id=analyst_id,
                current_value=current_value,
                threshold=rule.threshold
            ),
            timestamp=datetime.now(),
            metric_name=rule.metric_name,
            current_value=current_value,
            threshold=rule.threshold
        )
        
        # 記錄活躍告警
        self.active_alerts[alert_key] = alert
        self.alert_history.append(alert)
        
        # 更新規則觸發時間
        rule.last_triggered = datetime.now()
        
        # 調用處理器
        self._call_handlers(alert)
        
        self.logger.warning(f"觸發告警: {alert.title} - {alert.description}")
    
    def _call_handlers(self, alert: Alert):
        """調用告警處理器"""
        
        try:
            handlers = self.handlers.get(alert.level, [])
            
            for handler in handlers:
                try:
                    handler(alert)
                    alert.handler_called = True
                except Exception as e:
                    self.logger.error(f"告警處理器調用失敗: {str(e)}")
        
        except Exception as e:
            self.logger.error(f"調用告警處理器失敗: {str(e)}")
    
    def resolve_alert(self, alert_id: str, note: str = None) -> bool:
        """解決告警"""
        
        with self.lock:
            # 在活躍告警中查找
            for key, alert in list(self.active_alerts.items()):
                if alert.alert_id == alert_id:
                    alert.resolve(note)
                    del self.active_alerts[key]
                    self.logger.info(f"告警已解決: {alert_id}")
                    return True
            
            return False
    
    def get_active_alerts(self, analyst_id: str = None) -> List[Alert]:
        """獲取活躍告警"""
        
        with self.lock:
            alerts = list(self.active_alerts.values())
            
            if analyst_id:
                alerts = [alert for alert in alerts if alert.analyst_id == analyst_id]
            
            return alerts
    
    def get_alert_history(
        self, 
        analyst_id: str = None,
        level: AlertLevel = None,
        hours: int = 24
    ) -> List[Alert]:
        """獲取告警歷史"""
        
        with self.lock:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            filtered_alerts = []
            for alert in self.alert_history:
                if alert.timestamp < cutoff_time:
                    continue
                
                if analyst_id and alert.analyst_id != analyst_id:
                    continue
                
                if level and alert.level != level:
                    continue
                
                filtered_alerts.append(alert)
            
            return filtered_alerts


class AnomalyDetector:
    """異常檢測器"""
    
    def __init__(self, metric_store: MetricStore):
        self.metric_store = metric_store
        self.logger = logging.getLogger(__name__)
        
        # 檢測參數
        self.window_size = 20
        self.threshold_multiplier = 3.0  # 3個標準差
    
    def detect_anomalies(
        self, 
        metric_name: str, 
        analyst_id: str = "global"
    ) -> List[Dict[str, Any]]:
        """檢測異常"""
        
        try:
            # 獲取歷史數據
            points = self.metric_store.get_metric_values(
                metric_name, analyst_id, timedelta(hours=2)
            )
            
            if len(points) < self.window_size:
                return []
            
            values = [point.value for point in points]
            anomalies = []
            
            # 滑動窗口異常檢測
            for i in range(self.window_size, len(values)):
                window = values[i-self.window_size:i]
                current_value = values[i]
                
                # 計算統計量
                mean = statistics.mean(window)
                std = statistics.stdev(window) if len(window) > 1 else 0
                
                # 檢測異常
                if std > 0:
                    z_score = abs(current_value - mean) / std
                    
                    if z_score > self.threshold_multiplier:
                        anomalies.append({
                            'timestamp': points[i].timestamp,
                            'value': current_value,
                            'expected_range': (mean - 2*std, mean + 2*std),
                            'z_score': z_score,
                            'severity': 'high' if z_score > 4 else 'medium'
                        })
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"異常檢測失敗: {str(e)}")
            return []


class AnalystMonitor:
    """分析師監控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 組件
        self.metric_store = MetricStore(
            retention_hours=self.config.get('retention_hours', 24)
        )
        self.performance_collector = PerformanceCollector(self.metric_store)
        self.alert_manager = AlertManager()
        self.anomaly_detector = AnomalyDetector(self.metric_store)
        
        # 狀態追蹤
        self.analyst_status: Dict[str, MonitoringStatus] = {}
        self.last_activity: Dict[str, datetime] = {}
        
        # 監控狀態
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        
        # 初始化默認規則和處理器
        self._setup_default_rules()
        self._setup_default_handlers()
    
    async def start_monitoring(self):
        """開始監控"""
        
        if not self.is_monitoring:
            self.is_monitoring = True
            
            # 啟動性能收集
            await self.performance_collector.start_collection()
            
            # 啟動監控循環
            self.monitor_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("分析師監控已啟動")
    
    async def stop_monitoring(self):
        """停止監控"""
        
        if self.is_monitoring:
            self.is_monitoring = False
            
            # 停止性能收集
            await self.performance_collector.stop_collection()
            
            # 停止監控循環
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("分析師監控已停止")
    
    def record_analysis(self, analyst_id: str, result: AnalysisResult, execution_time: float):
        """記錄分析活動"""
        
        # 記錄性能指標
        self.performance_collector.record_analysis_metrics(analyst_id, result, execution_time)
        
        # 更新活動時間
        self.last_activity[analyst_id] = datetime.now()
        
        # 更新狀態
        if analyst_id not in self.analyst_status:
            self.analyst_status[analyst_id] = MonitoringStatus.HEALTHY
    
    def get_analyst_status(self, analyst_id: str) -> Dict[str, Any]:
        """獲取分析師狀態"""
        
        status_info = {
            'analyst_id': analyst_id,
            'status': self.analyst_status.get(analyst_id, MonitoringStatus.OFFLINE).value,
            'last_activity': self.last_activity.get(analyst_id),
            'metrics': {},
            'alerts': len(self.alert_manager.get_active_alerts(analyst_id)),
            'anomalies': 0
        }
        
        # 獲取關鍵指標
        key_metrics = [
            'analyst_analysis_count',
            'analyst_execution_time_ms',
            'analyst_confidence',
            'analyst_success_rate',
            'analyst_cost'
        ]
        
        for metric in key_metrics:
            latest_value = self.metric_store.get_latest_value(metric, analyst_id)
            avg_value = self.metric_store.get_aggregated_metrics(
                metric, analyst_id, timedelta(hours=1), "avg"
            )
            
            status_info['metrics'][metric] = {
                'latest': latest_value,
                'hourly_avg': avg_value
            }
        
        # 檢測異常
        for metric in key_metrics:
            anomalies = self.anomaly_detector.detect_anomalies(metric, analyst_id)
            status_info['anomalies'] += len(anomalies)
        
        return status_info
    
    def get_system_overview(self) -> Dict[str, Any]:
        """獲取系統總覽"""
        
        overview = {
            'timestamp': datetime.now().isoformat(),
            'total_analysts': len(self.analyst_status),
            'status_distribution': {},
            'active_alerts': len(self.alert_manager.active_alerts),
            'system_metrics': {},
            'top_performers': [],
            'problematic_analysts': []
        }
        
        # 狀態分佈
        status_counts = defaultdict(int)
        for status in self.analyst_status.values():
            status_counts[status.value] += 1
        overview['status_distribution'] = dict(status_counts)
        
        # 系統指標
        system_metrics = ['system_cpu_percent', 'system_memory_percent', 'system_disk_percent']
        for metric in system_metrics:
            latest = self.metric_store.get_latest_value(metric)
            overview['system_metrics'][metric] = latest
        
        # 分析師性能排名
        analyst_performances = []
        for analyst_id in self.analyst_status.keys():
            success_rate = self.metric_store.get_aggregated_metrics(
                'analyst_success_rate', analyst_id, timedelta(hours=1), 'avg'
            )
            if success_rate is not None:
                analyst_performances.append((analyst_id, success_rate))
        
        # 排序並取前5
        analyst_performances.sort(key=lambda x: x[1], reverse=True)
        overview['top_performers'] = analyst_performances[:5]
        
        # 問題分析師（有活躍告警的）
        problematic = []
        for analyst_id in self.analyst_status.keys():
            alerts = self.alert_manager.get_active_alerts(analyst_id)
            if alerts:
                problematic.append({
                    'analyst_id': analyst_id,
                    'alert_count': len(alerts),
                    'highest_alert_level': max(alert.level.value for alert in alerts)
                })
        
        overview['problematic_analysts'] = problematic
        
        return overview
    
    async def _monitoring_loop(self):
        """監控循環"""
        
        while self.is_monitoring:
            try:
                await self._check_analyst_health()
                await self._evaluate_alert_rules()
                await asyncio.sleep(30)  # 每30秒檢查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {str(e)}")
                await asyncio.sleep(10)
    
    async def _check_analyst_health(self):
        """檢查分析師健康狀態"""
        
        current_time = datetime.now()
        inactive_threshold = timedelta(minutes=15)
        
        for analyst_id in list(self.analyst_status.keys()):
            last_activity = self.last_activity.get(analyst_id)
            
            if last_activity:
                time_since_activity = current_time - last_activity
                
                if time_since_activity > inactive_threshold:
                    # 分析師長時間無活動
                    if self.analyst_status[analyst_id] != MonitoringStatus.OFFLINE:
                        self.analyst_status[analyst_id] = MonitoringStatus.OFFLINE
                        self.logger.warning(f"分析師離線: {analyst_id}")
                else:
                    # 分析師活躍
                    if self.analyst_status[analyst_id] == MonitoringStatus.OFFLINE:
                        self.analyst_status[analyst_id] = MonitoringStatus.HEALTHY
                        self.logger.info(f"分析師恢復在線: {analyst_id}")
    
    async def _evaluate_alert_rules(self):
        """評估告警規則"""
        
        # 獲取所有指標
        all_metrics = self.metric_store.list_metrics()
        
        for metric_name, analyst_ids in all_metrics.items():
            for analyst_id in analyst_ids:
                # 獲取最近的值
                recent_points = self.metric_store.get_metric_values(
                    metric_name, analyst_id, timedelta(minutes=5)
                )
                
                if recent_points:
                    recent_values = [point.value for point in recent_points]
                    self.alert_manager.evaluate_rules(metric_name, analyst_id, recent_values)
    
    def _setup_default_rules(self):
        """設置默認監控規則"""
        
        # 高錯誤率告警
        error_rate_rule = MonitoringRule(
            rule_id="high_error_rate",
            metric_name="analyst_success_rate",
            condition="less_than",
            threshold=0.5,
            alert_level=AlertLevel.WARNING,
            alert_title="分析師錯誤率過高",
            alert_description="分析師 {analyst_id} 的成功率降至 {current_value:.2%}，低於閾值 {threshold:.2%}"
        )
        self.alert_manager.add_rule(error_rate_rule)
        
        # 響應時間過長告警
        response_time_rule = MonitoringRule(
            rule_id="slow_response",
            metric_name="analyst_execution_time_ms",
            condition="greater_than",
            threshold=10000,  # 10秒
            alert_level=AlertLevel.WARNING,
            alert_title="分析師響應時間過長",
            alert_description="分析師 {analyst_id} 的響應時間達到 {current_value:.0f}ms，超過閾值 {threshold:.0f}ms"
        )
        self.alert_manager.add_rule(response_time_rule)
        
        # 高成本告警
        high_cost_rule = MonitoringRule(
            rule_id="high_cost",
            metric_name="analyst_cost",
            condition="greater_than",
            threshold=0.1,
            alert_level=AlertLevel.ERROR,
            alert_title="分析師成本過高",
            alert_description="分析師 {analyst_id} 的分析成本達到 ${current_value:.4f}，超過閾值 ${threshold:.4f}"
        )
        self.alert_manager.add_rule(high_cost_rule)
        
        # 系統資源告警
        cpu_rule = MonitoringRule(
            rule_id="high_cpu",
            metric_name="system_cpu_percent",
            condition="greater_than",
            threshold=80.0,
            alert_level=AlertLevel.WARNING,
            alert_title="系統CPU使用率過高",
            alert_description="系統CPU使用率達到 {current_value:.1f}%，超過閾值 {threshold:.1f}%"
        )
        self.alert_manager.add_rule(cpu_rule)
        
        memory_rule = MonitoringRule(
            rule_id="high_memory",
            metric_name="system_memory_percent",
            condition="greater_than",
            threshold=85.0,
            alert_level=AlertLevel.ERROR,
            alert_title="系統內存使用率過高",
            alert_description="系統內存使用率達到 {current_value:.1f}%，超過閾值 {threshold:.1f}%"
        )
        self.alert_manager.add_rule(memory_rule)
    
    def _setup_default_handlers(self):
        """設置默認告警處理器"""
        
        def log_alert(alert: Alert):
            """記錄告警到日誌"""
            level_map = {
                AlertLevel.INFO: self.logger.info,
                AlertLevel.WARNING: self.logger.warning,
                AlertLevel.ERROR: self.logger.error,
                AlertLevel.CRITICAL: self.logger.critical
            }
            
            log_func = level_map.get(alert.level, self.logger.info)
            log_func(f"告警: {alert.title} - {alert.description}")
        
        # 為所有級別添加日誌處理器
        for level in AlertLevel:
            self.alert_manager.add_handler(level, log_alert)


# 全局監控器實例
_global_monitor: Optional[AnalystMonitor] = None


def get_analyst_monitor() -> AnalystMonitor:
    """獲取全局分析師監控器"""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = AnalystMonitor()
    
    return _global_monitor


if __name__ == "__main__":
    # 測試腳本
    import asyncio
    from ..agents.analysts.base_analyst import AnalysisResult, AnalysisType, AnalysisConfidenceLevel
    
    async def test_analyst_monitoring():
        print("測試分析師監控系統")
        
        monitor = get_analyst_monitor()
        await monitor.start_monitoring()
        
        # 模擬分析活動
        for i in range(5):
            result = AnalysisResult(
                analyst_id="test_analyst",
                stock_id="2330",
                analysis_date="2024-01-01",
                analysis_type=AnalysisType.TECHNICAL,
                recommendation="BUY",
                confidence=0.8 - i * 0.1,
                confidence_level=AnalysisConfidenceLevel.HIGH
            )
            
            execution_time = 1000 + i * 500  # 逐漸增加響應時間
            
            monitor.record_analysis("test_analyst", result, execution_time)
            await asyncio.sleep(1)
        
        # 等待一段時間讓監控系統處理
        await asyncio.sleep(5)
        
        # 獲取狀態
        status = monitor.get_analyst_status("test_analyst")
        print(f"分析師狀態: {json.dumps(status, indent=2, default=str)}")
        
        # 獲取系統總覽
        overview = monitor.get_system_overview()
        print(f"系統總覽: {json.dumps(overview, indent=2, default=str)}")
        
        # 獲取活躍告警
        alerts = monitor.alert_manager.get_active_alerts()
        print(f"活躍告警數量: {len(alerts)}")
        
        await monitor.stop_monitoring()
        print("✅ 測試完成")
    
    asyncio.run(test_analyst_monitoring())