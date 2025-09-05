#!/usr/bin/env python3
"""
系統監控模組 (System Monitor)
天工 (TianGong) - 實時系統監控和指標收集

此模組提供全面的系統監控功能，包含：
1. 實時性能指標收集
2. 應用程式健康檢查
3. 資源使用監控
4. 告警和通知系統
5. 監控數據可視化
6. Taiwan市場特定監控
"""

import asyncio
import psutil
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque, defaultdict
import statistics
import socket
import platform

from ..utils.logging_config import get_system_logger, get_api_logger
from ..utils.error_handler import handle_error, ErrorCategory, ErrorSeverity

# 配置日誌
system_logger = get_system_logger("system_monitor")
api_logger = get_api_logger("system_monitor")

class MetricType(Enum):
    """指標類型"""
    GAUGE = "gauge"           # 瞬時值
    COUNTER = "counter"       # 累計值
    HISTOGRAM = "histogram"   # 分佈統計
    SUMMARY = "summary"       # 摘要統計

class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class MetricPoint:
    """指標數據點"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels,
            'type': self.metric_type.value
        }

@dataclass
class Alert:
    """告警"""
    alert_id: str
    name: str
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self):
        """解決告警"""
        self.resolved = True
        self.resolved_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'name': self.name,
            'level': self.level.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'metadata': self.metadata
        }

class SystemMetricsCollector:
    """系統指標收集器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.collection_interval = self.config.get('collection_interval', 5)  # 5秒
        self.metrics_buffer: deque = deque(maxlen=1440)  # 保留2小時數據(5秒間隔)
        self.is_collecting = False
        self.collection_task = None
        
    async def start_collection(self):
        """開始收集指標"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.collection_task = asyncio.create_task(self._collection_loop())
        system_logger.info("系統指標收集已啟動")
    
    async def stop_collection(self):
        """停止收集指標"""
        self.is_collecting = False
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        system_logger.info("系統指標收集已停止")
    
    async def _collection_loop(self):
        """指標收集循環"""
        while self.is_collecting:
            try:
                metrics = await self._collect_system_metrics()
                self.metrics_buffer.extend(metrics)
                
                # 記錄關鍵指標
                cpu_metric = next((m for m in metrics if m.name == 'cpu_percent'), None)
                memory_metric = next((m for m in metrics if m.name == 'memory_percent'), None)
                
                if cpu_metric and memory_metric:
                    system_logger.debug("系統指標收集", extra={
                        'cpu_percent': cpu_metric.value,
                        'memory_percent': memory_metric.value,
                        'metrics_count': len(metrics)
                    })
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                system_logger.error(f"指標收集錯誤: {str(e)}")
                await asyncio.sleep(self.collection_interval * 2)  # 錯誤時等待更長時間
    
    async def _collect_system_metrics(self) -> List[MetricPoint]:
        """收集系統指標"""
        metrics = []
        now = datetime.now()
        
        try:
            # CPU 指標
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            metrics.extend([
                MetricPoint('cpu_percent', cpu_percent, now),
                MetricPoint('cpu_count', cpu_count, now),
                MetricPoint('load_avg_1m', load_avg[0], now),
                MetricPoint('load_avg_5m', load_avg[1], now),
                MetricPoint('load_avg_15m', load_avg[2], now),
            ])
            
            # 記憶體指標
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            metrics.extend([
                MetricPoint('memory_total', memory.total, now),
                MetricPoint('memory_available', memory.available, now),
                MetricPoint('memory_used', memory.used, now),
                MetricPoint('memory_percent', memory.percent, now),
                MetricPoint('swap_total', swap.total, now),
                MetricPoint('swap_used', swap.used, now),
                MetricPoint('swap_percent', swap.percent, now),
            ])
            
            # 磁碟指標
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            metrics.extend([
                MetricPoint('disk_total', disk_usage.total, now),
                MetricPoint('disk_used', disk_usage.used, now),
                MetricPoint('disk_free', disk_usage.free, now),
                MetricPoint('disk_percent', disk_usage.percent, now),
            ])
            
            if disk_io:
                metrics.extend([
                    MetricPoint('disk_read_bytes', disk_io.read_bytes, now, metric_type=MetricType.COUNTER),
                    MetricPoint('disk_write_bytes', disk_io.write_bytes, now, metric_type=MetricType.COUNTER),
                    MetricPoint('disk_read_count', disk_io.read_count, now, metric_type=MetricType.COUNTER),
                    MetricPoint('disk_write_count', disk_io.write_count, now, metric_type=MetricType.COUNTER),
                ])
            
            # 網路指標
            net_io = psutil.net_io_counters()
            if net_io:
                metrics.extend([
                    MetricPoint('network_bytes_sent', net_io.bytes_sent, now, metric_type=MetricType.COUNTER),
                    MetricPoint('network_bytes_recv', net_io.bytes_recv, now, metric_type=MetricType.COUNTER),
                    MetricPoint('network_packets_sent', net_io.packets_sent, now, metric_type=MetricType.COUNTER),
                    MetricPoint('network_packets_recv', net_io.packets_recv, now, metric_type=MetricType.COUNTER),
                ])
            
            # 進程指標
            current_process = psutil.Process()
            process_memory = current_process.memory_info()
            
            metrics.extend([
                MetricPoint('process_cpu_percent', current_process.cpu_percent(), now),
                MetricPoint('process_memory_rss', process_memory.rss, now),
                MetricPoint('process_memory_vms', process_memory.vms, now),
                MetricPoint('process_open_files', len(current_process.open_files()), now),
                MetricPoint('process_num_threads', current_process.num_threads(), now),
            ])
            
        except Exception as e:
            system_logger.error(f"系統指標收集失敗: {str(e)}")
        
        return metrics
    
    def get_latest_metrics(self, count: int = 1) -> List[MetricPoint]:
        """獲取最新指標"""
        if not self.metrics_buffer:
            return []
        
        # 獲取最新的指標組
        latest_timestamp = self.metrics_buffer[-1].timestamp
        latest_metrics = [
            m for m in self.metrics_buffer
            if m.timestamp == latest_timestamp
        ]
        
        return latest_metrics
    
    def get_metrics_history(self, metric_name: str, duration_minutes: int = 60) -> List[MetricPoint]:
        """獲取指標歷史"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        return [
            m for m in self.metrics_buffer
            if m.name == metric_name and m.timestamp > cutoff_time
        ]

class ApplicationMetricsCollector:
    """應用程式指標收集器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.counters: Dict[str, float] = defaultdict(float)
        
    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """記錄計數器指標"""
        key = self._make_key(name, labels)
        self.counters[key] += value
        
        metric = MetricPoint(
            name=name,
            value=self.counters[key],
            labels=labels or {},
            metric_type=MetricType.COUNTER
        )
        
        self.metrics[name].append(metric)
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """記錄瞬時值指標"""
        metric = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            metric_type=MetricType.GAUGE
        )
        
        self.metrics[name].append(metric)
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """記錄直方圖指標"""
        metric = MetricPoint(
            name=name,
            value=value,
            labels=labels or {},
            metric_type=MetricType.HISTOGRAM
        )
        
        self.metrics[name].append(metric)
    
    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """生成指標鍵"""
        if not labels:
            return name
        
        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metric_summary(self, name: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """獲取指標摘要統計"""
        if name not in self.metrics:
            return {}
        
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [
            m for m in self.metrics[name]
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        values = [m.value for m in recent_metrics]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'p95': self._percentile(values, 95),
            'p99': self._percentile(values, 99),
            'latest': values[-1] if values else 0
        }
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """計算百分位數"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_handlers: List[Callable] = []
        
        # 設置默認告警規則
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """設置默認告警規則"""
        self.alert_rules = [
            {
                'name': 'high_cpu_usage',
                'condition': lambda metrics: self._check_cpu_usage(metrics, 85),
                'level': AlertLevel.WARNING,
                'message': 'CPU使用率過高'
            },
            {
                'name': 'critical_cpu_usage',
                'condition': lambda metrics: self._check_cpu_usage(metrics, 95),
                'level': AlertLevel.CRITICAL,
                'message': 'CPU使用率嚴重過高'
            },
            {
                'name': 'high_memory_usage',
                'condition': lambda metrics: self._check_memory_usage(metrics, 85),
                'level': AlertLevel.WARNING,
                'message': '記憶體使用率過高'
            },
            {
                'name': 'critical_memory_usage',
                'condition': lambda metrics: self._check_memory_usage(metrics, 95),
                'level': AlertLevel.CRITICAL,
                'message': '記憶體使用率嚴重過高'
            },
            {
                'name': 'disk_space_low',
                'condition': lambda metrics: self._check_disk_usage(metrics, 90),
                'level': AlertLevel.WARNING,
                'message': '磁碟空間不足'
            },
            {
                'name': 'disk_space_critical',
                'condition': lambda metrics: self._check_disk_usage(metrics, 95),
                'level': AlertLevel.CRITICAL,
                'message': '磁碟空間嚴重不足'
            }
        ]
    
    def check_alerts(self, metrics: List[MetricPoint]):
        """檢查告警條件"""
        for rule in self.alert_rules:
            try:
                if rule['condition'](metrics):
                    self._trigger_alert(rule)
                else:
                    self._resolve_alert(rule['name'])
            except Exception as e:
                system_logger.error(f"告警規則檢查失敗 {rule['name']}: {str(e)}")
    
    def _trigger_alert(self, rule: Dict[str, Any]):
        """觸發告警"""
        alert_name = rule['name']
        
        # 如果告警已存在且未解決，不重複觸發
        if alert_name in self.alerts and not self.alerts[alert_name].resolved:
            return
        
        # 創建新告警
        alert = Alert(
            alert_id=f"{alert_name}_{int(time.time())}",
            name=alert_name,
            level=rule['level'],
            message=rule['message'],
            metadata={'rule': rule}
        )
        
        self.alerts[alert_name] = alert
        
        # 發送通知
        asyncio.create_task(self._send_notifications(alert))
        
        system_logger.warning(f"告警觸發: {alert.message}", extra={
            'alert_id': alert.alert_id,
            'alert_name': alert_name,
            'alert_level': alert.level.value
        })
    
    def _resolve_alert(self, alert_name: str):
        """解決告警"""
        if alert_name in self.alerts and not self.alerts[alert_name].resolved:
            alert = self.alerts[alert_name]
            alert.resolve()
            
            system_logger.info(f"告警解決: {alert.message}", extra={
                'alert_id': alert.alert_id,
                'alert_name': alert_name,
                'duration_seconds': (alert.resolved_at - alert.timestamp).total_seconds()
            })
    
    async def _send_notifications(self, alert: Alert):
        """發送告警通知"""
        for handler in self.notification_handlers:
            try:
                await handler(alert)
            except Exception as e:
                system_logger.error(f"告警通知發送失敗: {str(e)}")
    
    def add_notification_handler(self, handler: Callable):
        """添加通知處理器"""
        self.notification_handlers.append(handler)
    
    def _check_cpu_usage(self, metrics: List[MetricPoint], threshold: float) -> bool:
        """檢查CPU使用率"""
        cpu_metric = next((m for m in metrics if m.name == 'cpu_percent'), None)
        return cpu_metric and cpu_metric.value > threshold
    
    def _check_memory_usage(self, metrics: List[MetricPoint], threshold: float) -> bool:
        """檢查記憶體使用率"""
        memory_metric = next((m for m in metrics if m.name == 'memory_percent'), None)
        return memory_metric and memory_metric.value > threshold
    
    def _check_disk_usage(self, metrics: List[MetricPoint], threshold: float) -> bool:
        """檢查磁碟使用率"""
        disk_metric = next((m for m in metrics if m.name == 'disk_percent'), None)
        return disk_metric and disk_metric.value > threshold
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍告警"""
        return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """獲取告警歷史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts.values()
            if alert.timestamp > cutoff_time
        ]

class SystemMonitor:
    """系統監控主控制器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化組件
        self.system_collector = SystemMetricsCollector(self.config.get('system_metrics', {}))
        self.app_collector = ApplicationMetricsCollector(self.config.get('app_metrics', {}))
        self.alert_manager = AlertManager(self.config.get('alerts', {}))
        
        # 監控狀態
        self.is_running = False
        self.monitor_task = None
        
        # 設置默認通知處理器
        self.alert_manager.add_notification_handler(self._log_alert_notification)
        
        system_logger.info("系統監控器初始化完成")
    
    async def start(self):
        """啟動監控"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 啟動系統指標收集
        await self.system_collector.start_collection()
        
        # 啟動監控任務
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        system_logger.info("系統監控已啟動")
    
    async def stop(self):
        """停止監控"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # 停止監控任務
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        # 停止系統指標收集
        await self.system_collector.stop_collection()
        
        system_logger.info("系統監控已停止")
    
    async def _monitor_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 獲取最新指標
                latest_metrics = self.system_collector.get_latest_metrics()
                
                # 檢查告警
                if latest_metrics:
                    self.alert_manager.check_alerts(latest_metrics)
                
                # 等待下一次檢查
                await asyncio.sleep(10)  # 每10秒檢查一次告警
                
            except Exception as e:
                system_logger.error(f"監控循環錯誤: {str(e)}")
                await asyncio.sleep(30)  # 錯誤時等待更長時間
    
    async def _log_alert_notification(self, alert: Alert):
        """日誌告警通知處理器"""
        if alert.level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            system_logger.error(f"系統告警: {alert.message}", extra={
                'alert_id': alert.alert_id,
                'alert_level': alert.level.value,
                'alert_metadata': alert.metadata
            })
        else:
            system_logger.warning(f"系統告警: {alert.message}", extra={
                'alert_id': alert.alert_id,
                'alert_level': alert.level.value
            })
    
    def record_api_request(self, endpoint: str, status_code: int, duration: float):
        """記錄API請求指標"""
        labels = {'endpoint': endpoint, 'status': str(status_code)}
        
        self.app_collector.record_counter('api_requests_total', 1.0, labels)
        self.app_collector.record_histogram('api_request_duration_seconds', duration, labels)
    
    def record_analysis_session(self, status: str, duration: float, analyst_count: int):
        """記錄分析會話指標"""
        labels = {'status': status}
        
        self.app_collector.record_counter('analysis_sessions_total', 1.0, labels)
        self.app_collector.record_histogram('analysis_session_duration_seconds', duration, labels)
        self.app_collector.record_gauge('analysis_session_analysts', analyst_count, labels)
    
    def record_user_activity(self, user_tier: str, action: str):
        """記錄用戶活動指標"""
        labels = {'tier': user_tier, 'action': action}
        self.app_collector.record_counter('user_activities_total', 1.0, labels)
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """獲取監控儀表板數據"""
        # 系統指標
        latest_system_metrics = self.system_collector.get_latest_metrics()
        system_summary = {}
        
        for metric in latest_system_metrics:
            system_summary[metric.name] = metric.value
        
        # 應用指標摘要
        app_summaries = {}
        for metric_name in ['api_requests_total', 'analysis_sessions_total', 'user_activities_total']:
            summary = self.app_collector.get_metric_summary(metric_name, 60)
            if summary:
                app_summaries[metric_name] = summary
        
        # 活躍告警
        active_alerts = self.alert_manager.get_active_alerts()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_metrics': system_summary,
            'application_metrics': app_summaries,
            'active_alerts': [alert.to_dict() for alert in active_alerts],
            'system_info': {
                'hostname': socket.gethostname(),
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'uptime_seconds': time.time() - psutil.boot_time()
            }
        }

# 全局監控實例
_global_monitor: Optional[SystemMonitor] = None

def get_system_monitor(config: Optional[Dict[str, Any]] = None) -> SystemMonitor:
    """獲取全局系統監控實例"""
    global _global_monitor
    
    if _global_monitor is None:
        _global_monitor = SystemMonitor(config)
    
    return _global_monitor

if __name__ == "__main__":
    # 測試腳本
    async def test_system_monitor():
        print("測試系統監控...")
        
        # 創建監控器
        monitor = get_system_monitor()
        
        # 啟動監控
        await monitor.start()
        
        # 模擬記錄一些指標
        monitor.record_api_request('/analysis/start', 200, 1.5)
        monitor.record_analysis_session('completed', 30.0, 3)
        monitor.record_user_activity('DIAMOND', 'analysis_request')
        
        # 等待一段時間收集指標
        await asyncio.sleep(10)
        
        # 獲取監控儀表板
        dashboard = monitor.get_monitoring_dashboard()
        print(f"監控儀表板數據: {json.dumps(dashboard, indent=2, ensure_ascii=False)}")
        
        # 停止監控
        await monitor.stop()
        
        print("系統監控測試完成")
    
    asyncio.run(test_system_monitor())