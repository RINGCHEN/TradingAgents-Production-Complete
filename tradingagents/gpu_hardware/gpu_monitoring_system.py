#!/usr/bin/env python3
"""
實時GPU性能監控系統
小c - 硬體優化與資源管理團隊

此模組提供：
1. 實時GPU性能指標收集
2. 溫度、記憶體、功耗、利用率監控
3. 多層級告警機制
4. 性能指標歷史數據存儲
5. 監控儀表板和可視化介面
"""

import asyncio
import logging
import time
import json
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from pathlib import Path
import sqlite3
import queue
import statistics

# GPU相關庫
try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logging.warning("NVML not available, using fallback monitoring")

try:
    import torch
    import torch.cuda
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available, GPU functionality limited")

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """指標類型"""
    TEMPERATURE = "temperature"
    MEMORY_USAGE = "memory_usage"
    GPU_UTILIZATION = "gpu_utilization"
    POWER_USAGE = "power_usage"
    MEMORY_ALLOCATED = "memory_allocated"
    MEMORY_RESERVED = "memory_reserved"


@dataclass
class GPUMetric:
    """GPU指標數據"""
    device_id: int
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """告警規則"""
    name: str
    metric_type: MetricType
    condition: str  # ">", "<", ">=", "<=", "=="
    threshold: float
    alert_level: AlertLevel
    enabled: bool = True
    cooldown_seconds: int = 300  # 冷卻時間


@dataclass
class Alert:
    """告警信息"""
    alert_id: str
    rule_name: str
    metric_type: MetricType
    current_value: float
    threshold: float
    alert_level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False


@dataclass
class MonitoringConfig:
    """監控配置"""
    device_id: int = 0
    collection_interval: float = 5.0  # 收集間隔秒數
    retention_days: int = 30  # 數據保留天數
    max_history_size: int = 10000  # 最大歷史記錄數
    
    # 告警閾值
    temperature_warning: float = 75.0
    temperature_critical: float = 83.0
    memory_warning: float = 85.0
    memory_critical: float = 95.0
    utilization_warning: float = 90.0
    utilization_critical: float = 95.0
    power_warning: float = 200.0  # Watts
    power_critical: float = 250.0  # Watts


class GPUMonitoringSystem:
    """
    實時GPU性能監控系統
    
    提供完整的GPU性能監控解決方案，包括指標收集、告警管理、
    歷史數據存儲和可視化介面。
    """
    
    def __init__(self, config: MonitoringConfig = None):
        """
        初始化GPU監控系統
        
        Args:
            config: 監控配置
        """
        self.config = config or MonitoringConfig()
        
        # 數據存儲
        self.metrics_history: List[GPUMetric] = []
        self.alerts_history: List[Alert] = []
        self.active_alerts: Dict[str, Alert] = {}
        
        # 告警規則
        self.alert_rules: List[AlertRule] = self._create_default_alert_rules()
        
        # 監控狀態
        self.is_monitoring = False
        self.monitor_thread = None
        self.monitor_queue = queue.Queue()
        
        # 回調函數
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self.metric_callbacks: List[Callable[[GPUMetric], None]] = []
        
        # 統計信息
        self.stats = {
            'total_metrics_collected': 0,
            'total_alerts_triggered': 0,
            'last_collection_time': None,
            'collection_errors': 0
        }
        
        # 數據庫
        self.db_path = Path("logs/gpu_monitoring.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        logger.info(f"GPU監控系統初始化完成 - 設備{self.config.device_id}")
    
    def _init_database(self):
        """初始化數據庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 創建指標表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gpu_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id INTEGER,
                    metric_type TEXT,
                    value REAL,
                    unit TEXT,
                    timestamp TEXT,
                    metadata TEXT
                )
            ''')
            
            # 創建告警表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gpu_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    rule_name TEXT,
                    metric_type TEXT,
                    current_value REAL,
                    threshold REAL,
                    alert_level TEXT,
                    message TEXT,
                    timestamp TEXT,
                    acknowledged BOOLEAN,
                    resolved BOOLEAN
                )
            ''')
            
            # 創建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON gpu_metrics(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_metrics_type ON gpu_metrics(metric_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON gpu_alerts(timestamp)')
            
            conn.commit()
            conn.close()
            
            logger.info("監控數據庫初始化完成")
            
        except Exception as e:
            logger.error(f"數據庫初始化失敗: {e}")
    
    def _create_default_alert_rules(self) -> List[AlertRule]:
        """創建默認告警規則"""
        return [
            AlertRule(
                name="temperature_warning",
                metric_type=MetricType.TEMPERATURE,
                condition=">=",
                threshold=self.config.temperature_warning,
                alert_level=AlertLevel.WARNING
            ),
            AlertRule(
                name="temperature_critical",
                metric_type=MetricType.TEMPERATURE,
                condition=">=",
                threshold=self.config.temperature_critical,
                alert_level=AlertLevel.CRITICAL
            ),
            AlertRule(
                name="memory_warning",
                metric_type=MetricType.MEMORY_USAGE,
                condition=">=",
                threshold=self.config.memory_warning,
                alert_level=AlertLevel.WARNING
            ),
            AlertRule(
                name="memory_critical",
                metric_type=MetricType.MEMORY_USAGE,
                condition=">=",
                threshold=self.config.memory_critical,
                alert_level=AlertLevel.CRITICAL
            ),
            AlertRule(
                name="utilization_warning",
                metric_type=MetricType.GPU_UTILIZATION,
                condition=">=",
                threshold=self.config.utilization_warning,
                alert_level=AlertLevel.WARNING
            ),
            AlertRule(
                name="utilization_critical",
                metric_type=MetricType.GPU_UTILIZATION,
                condition=">=",
                threshold=self.config.utilization_critical,
                alert_level=AlertLevel.CRITICAL
            ),
            AlertRule(
                name="power_warning",
                metric_type=MetricType.POWER_USAGE,
                condition=">=",
                threshold=self.config.power_warning,
                alert_level=AlertLevel.WARNING
            ),
            AlertRule(
                name="power_critical",
                metric_type=MetricType.POWER_USAGE,
                condition=">=",
                threshold=self.config.power_critical,
                alert_level=AlertLevel.CRITICAL
            )
        ]
    
    async def start_monitoring(self):
        """啟動監控"""
        if self.is_monitoring:
            logger.warning("監控已啟動")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="GPU-Monitor"
        )
        self.monitor_thread.start()
        
        logger.info("GPU監控系統啟動")
    
    async def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("GPU監控系統停止")
    
    def _monitor_loop(self):
        """監控循環"""
        while self.is_monitoring:
            try:
                # 收集指標
                metrics = self._collect_metrics()
                
                # 存儲指標
                for metric in metrics:
                    self._store_metric(metric)
                    self._check_alerts(metric)
                
                # 更新統計
                self.stats['total_metrics_collected'] += len(metrics)
                self.stats['last_collection_time'] = datetime.now().isoformat()
                
                # 清理舊數據
                self._cleanup_old_data()
                
                time.sleep(self.config.collection_interval)
                
            except Exception as e:
                logger.error(f"監控循環異常: {e}")
                self.stats['collection_errors'] += 1
                time.sleep(self.config.collection_interval)
    
    def _collect_metrics(self) -> List[GPUMetric]:
        """收集GPU指標"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            if NVML_AVAILABLE:
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.config.device_id)
                
                # 溫度
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                metrics.append(GPUMetric(
                    device_id=self.config.device_id,
                    metric_type=MetricType.TEMPERATURE,
                    value=temperature,
                    unit="°C",
                    timestamp=timestamp
                ))
                
                # 記憶體使用率
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                memory_usage_percent = (memory_info.used / memory_info.total) * 100
                metrics.append(GPUMetric(
                    device_id=self.config.device_id,
                    metric_type=MetricType.MEMORY_USAGE,
                    value=memory_usage_percent,
                    unit="%",
                    timestamp=timestamp,
                    metadata={
                        'total_gb': memory_info.total / (1024**3),
                        'used_gb': memory_info.used / (1024**3),
                        'free_gb': memory_info.free / (1024**3)
                    }
                ))
                
                # GPU利用率
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                metrics.append(GPUMetric(
                    device_id=self.config.device_id,
                    metric_type=MetricType.GPU_UTILIZATION,
                    value=utilization.gpu,
                    unit="%",
                    timestamp=timestamp
                ))
                
                # 功耗
                power_usage_w = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                metrics.append(GPUMetric(
                    device_id=self.config.device_id,
                    metric_type=MetricType.POWER_USAGE,
                    value=power_usage_w,
                    unit="W",
                    timestamp=timestamp
                ))
                
            else:
                # 模擬數據
                import random
                metrics = [
                    GPUMetric(
                        device_id=self.config.device_id,
                        metric_type=MetricType.TEMPERATURE,
                        value=random.uniform(60, 80),
                        unit="°C",
                        timestamp=timestamp
                    ),
                    GPUMetric(
                        device_id=self.config.device_id,
                        metric_type=MetricType.MEMORY_USAGE,
                        value=random.uniform(50, 90),
                        unit="%",
                        timestamp=timestamp
                    ),
                    GPUMetric(
                        device_id=self.config.device_id,
                        metric_type=MetricType.GPU_UTILIZATION,
                        value=random.uniform(30, 85),
                        unit="%",
                        timestamp=timestamp
                    ),
                    GPUMetric(
                        device_id=self.config.device_id,
                        metric_type=MetricType.POWER_USAGE,
                        value=random.uniform(100, 200),
                        unit="W",
                        timestamp=timestamp
                    )
                ]
            
            # PyTorch記憶體指標
            if TORCH_AVAILABLE and torch.cuda.is_available():
                try:
                    allocated = torch.cuda.memory_allocated(self.config.device_id) / (1024**3)
                    reserved = torch.cuda.memory_reserved(self.config.device_id) / (1024**3)
                    
                    metrics.append(GPUMetric(
                        device_id=self.config.device_id,
                        metric_type=MetricType.MEMORY_ALLOCATED,
                        value=allocated,
                        unit="GB",
                        timestamp=timestamp
                    ))
                    
                    metrics.append(GPUMetric(
                        device_id=self.config.device_id,
                        metric_type=MetricType.MEMORY_RESERVED,
                        value=reserved,
                        unit="GB",
                        timestamp=timestamp
                    ))
                    
                except Exception as e:
                    logger.warning(f"PyTorch記憶體指標收集失敗: {e}")
            
        except Exception as e:
            logger.error(f"指標收集失敗: {e}")
            self.stats['collection_errors'] += 1
        
        return metrics
    
    def _store_metric(self, metric: GPUMetric):
        """存儲指標"""
        # 內存存儲
        self.metrics_history.append(metric)
        
        # 限制歷史記錄大小
        if len(self.metrics_history) > self.config.max_history_size:
            self.metrics_history.pop(0)
        
        # 數據庫存儲
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO gpu_metrics 
                (device_id, metric_type, value, unit, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                metric.device_id,
                metric.metric_type.value,
                metric.value,
                metric.unit,
                metric.timestamp.isoformat(),
                json.dumps(metric.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"指標存儲失敗: {e}")
        
        # 觸發回調
        for callback in self.metric_callbacks:
            try:
                callback(metric)
            except Exception as e:
                logger.error(f"指標回調執行失敗: {e}")
    
    def _check_alerts(self, metric: GPUMetric):
        """檢查告警"""
        for rule in self.alert_rules:
            if not rule.enabled or rule.metric_type != metric.metric_type:
                continue
            
            # 檢查條件
            should_alert = False
            if rule.condition == ">=" and metric.value >= rule.threshold:
                should_alert = True
            elif rule.condition == ">" and metric.value > rule.threshold:
                should_alert = True
            elif rule.condition == "<=" and metric.value <= rule.threshold:
                should_alert = True
            elif rule.condition == "<" and metric.value < rule.threshold:
                should_alert = True
            elif rule.condition == "==" and metric.value == rule.threshold:
                should_alert = True
            
            if should_alert:
                self._trigger_alert(rule, metric)
    
    def _trigger_alert(self, rule: AlertRule, metric: GPUMetric):
        """觸發告警"""
        import uuid
        
        alert_id = str(uuid.uuid4())
        
        # 檢查冷卻時間
        if rule.name in self.active_alerts:
            last_alert = self.active_alerts[rule.name]
            time_diff = (datetime.now() - last_alert.timestamp).total_seconds()
            if time_diff < rule.cooldown_seconds:
                return
        
        # 創建告警
        alert = Alert(
            alert_id=alert_id,
            rule_name=rule.name,
            metric_type=metric.metric_type,
            current_value=metric.value,
            threshold=rule.threshold,
            alert_level=rule.alert_level,
            message=f"{metric.metric_type.value} {rule.condition} {rule.threshold} "
                    f"(當前值: {metric.value:.2f}{metric.unit})",
            timestamp=datetime.now()
        )
        
        # 存儲告警
        self.active_alerts[rule.name] = alert
        self.alerts_history.append(alert)
        
        # 數據庫存儲
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO gpu_alerts 
                (alert_id, rule_name, metric_type, current_value, threshold, 
                 alert_level, message, timestamp, acknowledged, resolved)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert.alert_id,
                alert.rule_name,
                alert.metric_type.value,
                alert.current_value,
                alert.threshold,
                alert.alert_level.value,
                alert.message,
                alert.timestamp.isoformat(),
                alert.acknowledged,
                alert.resolved
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"告警存儲失敗: {e}")
        
        # 更新統計
        self.stats['total_alerts_triggered'] += 1
        
        # 觸發回調
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回調執行失敗: {e}")
        
        # 日誌記錄
        logger.warning(f"GPU告警觸發: {alert.message}")
    
    def _cleanup_old_data(self):
        """清理舊數據"""
        cutoff_time = datetime.now() - timedelta(days=self.config.retention_days)
        
        # 清理內存數據
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        # 清理數據庫
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'DELETE FROM gpu_metrics WHERE timestamp < ?',
                (cutoff_time.isoformat(),)
            )
            
            cursor.execute(
                'DELETE FROM gpu_alerts WHERE timestamp < ?',
                (cutoff_time.isoformat(),)
            )
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"數據清理失敗: {e}")
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回調"""
        self.alert_callbacks.append(callback)
    
    def add_metric_callback(self, callback: Callable[[GPUMetric], None]):
        """添加指標回調"""
        self.metric_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[str, GPUMetric]:
        """獲取當前指標"""
        current_metrics = {}
        
        for metric in reversed(self.metrics_history):
            if metric.metric_type.value not in current_metrics:
                current_metrics[metric.metric_type.value] = metric
        
        return current_metrics
    
    def get_metrics_history(
        self,
        metric_type: MetricType,
        hours: int = 24
    ) -> List[GPUMetric]:
        """獲取指標歷史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            m for m in self.metrics_history
            if m.metric_type == metric_type and m.timestamp > cutoff_time
        ]
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍告警"""
        return list(self.active_alerts.values())
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """確認告警"""
        for alert in self.active_alerts.values():
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解決告警"""
        for rule_name, alert in list(self.active_alerts.items()):
            if alert.alert_id == alert_id:
                alert.resolved = True
                del self.active_alerts[rule_name]
                return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            'active_alerts_count': len(self.active_alerts),
            'metrics_history_size': len(self.metrics_history),
            'is_monitoring': self.is_monitoring
        }
    
    def export_metrics(self, file_path: str, hours: int = 24):
        """導出指標數據"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            metrics = [
                m for m in self.metrics_history
                if m.timestamp > cutoff_time
            ]
            
            data = [asdict(m) for m in metrics]
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"指標數據已導出到: {file_path}")
            
        except Exception as e:
            logger.error(f"指標導出失敗: {e}")


# 工廠函數
def create_gpu_monitoring_system(device_id: int = 0) -> GPUMonitoringSystem:
    """
    創建GPU監控系統實例
    
    Args:
        device_id: GPU設備ID
        
    Returns:
        GPU監控系統實例
    """
    config = MonitoringConfig(device_id=device_id)
    return GPUMonitoringSystem(config)
