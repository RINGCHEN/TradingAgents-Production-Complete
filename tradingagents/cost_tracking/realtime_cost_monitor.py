#!/usr/bin/env python3
"""
Real-time Cost Monitor - 實時成本監控和預警系統
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級實時成本監控引擎，提供：
- 實時成本數據收集和處理
- 動態成本預警和閾值監控
- 成本趨勢分析和預測
- 自動化成本優化建議
- 多維度成本監控看板
- 異常檢測和告警機制
"""

import uuid
import logging
import asyncio
import json
import websockets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable, Set
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field, asdict
from enum import Enum
import statistics
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref
from contextlib import asynccontextmanager

from .hardware_cost_calculator import HardwareCostCalculator, HardwareCostCalculationResult
from .power_maintenance_tracker import PowerMaintenanceTracker, CostCalculationResult
from .labor_cost_allocator import LaborCostAllocator, CostAllocationResult

logger = logging.getLogger(__name__)

# ==================== 核心枚舉和數據類型 ====================

class AlertSeverity(Enum):
    """告警嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertType(Enum):
    """告警類型"""
    COST_THRESHOLD = "cost_threshold"       # 成本閾值
    BUDGET_OVERRUN = "budget_overrun"      # 預算超支
    COST_SPIKE = "cost_spike"              # 成本激增
    EFFICIENCY_DROP = "efficiency_drop"    # 效率下降
    UTILIZATION_LOW = "utilization_low"    # 利用率過低
    ANOMALY_DETECTED = "anomaly_detected"  # 異常檢測
    TREND_WARNING = "trend_warning"        # 趨勢預警

class MonitoringScope(Enum):
    """監控範圍"""
    ASSET = "asset"                        # 單個資產
    COST_CENTER = "cost_center"           # 成本中心
    PROJECT = "project"                   # 項目
    DEPARTMENT = "department"             # 部門
    ORGANIZATION = "organization"         # 組織

class MetricType(Enum):
    """指標類型"""
    COST = "cost"
    POWER_CONSUMPTION = "power_consumption"
    UTILIZATION = "utilization"
    EFFICIENCY = "efficiency"
    THROUGHPUT = "throughput"
    QUALITY = "quality"

@dataclass
class AlertRule:
    """告警規則"""
    rule_id: str
    name: str
    alert_type: AlertType
    severity: AlertSeverity
    
    # 監控目標
    scope: MonitoringScope
    target_ids: List[str] = field(default_factory=list)
    metric_type: MetricType = MetricType.COST
    
    # 閾值設定
    threshold_value: Optional[Decimal] = None
    threshold_percentage: Optional[float] = None
    comparison_operator: str = "greater_than"  # greater_than, less_than, equal, not_equal
    
    # 時間設定
    evaluation_period_minutes: int = 15
    consecutive_breaches_required: int = 1
    
    # 動作設定
    notification_enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)
    auto_action_enabled: bool = False
    auto_action_script: Optional[str] = None
    
    # 狀態
    is_active: bool = True
    last_evaluated_at: Optional[datetime] = None
    last_triggered_at: Optional[datetime] = None
    consecutive_breaches: int = 0
    
    # 抑制設定
    suppression_duration_minutes: int = 60
    is_suppressed: bool = False
    suppressed_until: Optional[datetime] = None

@dataclass
class Alert:
    """告警實例"""
    alert_id: str
    rule_id: str
    severity: AlertSeverity
    alert_type: AlertType
    
    # 基本信息
    title: str
    message: str
    target_id: str
    target_type: MonitoringScope
    
    # 指標信息
    metric_type: MetricType
    current_value: Union[Decimal, float]
    threshold_value: Union[Decimal, float]
    
    # 時間信息
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    
    # 狀態
    is_active: bool = True
    is_acknowledged: bool = False
    resolution_note: Optional[str] = None
    
    # 相關數據
    context_data: Dict[str, Any] = field(default_factory=dict)
    suggested_actions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'alert_id': self.alert_id,
            'rule_id': self.rule_id,
            'severity': self.severity.value,
            'alert_type': self.alert_type.value,
            'title': self.title,
            'message': self.message,
            'target_id': self.target_id,
            'target_type': self.target_type.value,
            'metric_type': self.metric_type.value,
            'current_value': float(self.current_value) if isinstance(self.current_value, Decimal) else self.current_value,
            'threshold_value': float(self.threshold_value) if isinstance(self.threshold_value, Decimal) else self.threshold_value,
            'triggered_at': self.triggered_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'is_active': self.is_active,
            'is_acknowledged': self.is_acknowledged,
            'resolution_note': self.resolution_note,
            'context_data': self.context_data,
            'suggested_actions': self.suggested_actions
        }

@dataclass
class MonitoringMetrics:
    """監控指標"""
    timestamp: datetime
    target_id: str
    target_type: MonitoringScope
    
    # 成本指標
    total_cost: Decimal = Decimal('0')
    hardware_cost: Decimal = Decimal('0')
    power_cost: Decimal = Decimal('0')
    maintenance_cost: Decimal = Decimal('0')
    labor_cost: Decimal = Decimal('0')
    
    # 效率指標
    utilization_rate: float = 0.0
    power_usage_effectiveness: float = 1.0
    cost_per_unit: Decimal = Decimal('0')
    
    # 性能指標
    throughput: float = 0.0
    latency_ms: float = 0.0
    error_rate: float = 0.0
    
    # 質量指標
    quality_score: float = 1.0
    satisfaction_score: float = 1.0
    
    # 預算指標
    budget_utilization: float = 0.0
    budget_remaining: Decimal = Decimal('0')
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'target_id': self.target_id,
            'target_type': self.target_type.value,
            'total_cost': float(self.total_cost),
            'hardware_cost': float(self.hardware_cost),
            'power_cost': float(self.power_cost),
            'maintenance_cost': float(self.maintenance_cost),
            'labor_cost': float(self.labor_cost),
            'utilization_rate': self.utilization_rate,
            'power_usage_effectiveness': self.power_usage_effectiveness,
            'cost_per_unit': float(self.cost_per_unit),
            'throughput': self.throughput,
            'latency_ms': self.latency_ms,
            'error_rate': self.error_rate,
            'quality_score': self.quality_score,
            'satisfaction_score': self.satisfaction_score,
            'budget_utilization': self.budget_utilization,
            'budget_remaining': float(self.budget_remaining)
        }

# ==================== 核心監控引擎 ====================

class RealtimeCostMonitor:
    """
    實時成本監控器
    
    功能：
    1. 實時成本數據收集和處理
    2. 動態成本預警和閾值監控
    3. 成本趨勢分析和預測
    4. 自動化成本優化建議
    5. 多維度成本監控看板
    6. 異常檢測和告警機制
    """
    
    def __init__(
        self,
        hardware_calculator: Optional[HardwareCostCalculator] = None,
        power_tracker: Optional[PowerMaintenanceTracker] = None,
        labor_allocator: Optional[LaborCostAllocator] = None,
        monitoring_interval_seconds: int = 60
    ):
        """初始化實時成本監控器"""
        self.logger = logger
        
        # 成本計算組件
        self.hardware_calculator = hardware_calculator or HardwareCostCalculator()
        self.power_tracker = power_tracker or PowerMaintenanceTracker()
        self.labor_allocator = labor_allocator or LaborCostAllocator()
        
        # 監控配置
        self.monitoring_interval_seconds = monitoring_interval_seconds
        
        # 數據存儲
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.metrics_history: List[MonitoringMetrics] = []
        
        # WebSocket連接管理
        self.websocket_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.websocket_server = None
        
        # 監控狀態
        self.is_monitoring = False
        self.monitoring_task = None
        
        # 線程池
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 配置
        self.config = {
            'max_metrics_history': 10000,
            'max_alert_history': 1000,
            'websocket_port': 8765,
            'anomaly_detection_enabled': True,
            'trend_analysis_enabled': True,
            'auto_optimization_enabled': False,
            'notification_retry_count': 3,
            'data_retention_days': 30
        }
        
        # 異常檢測參數
        self.anomaly_config = {
            'cost_spike_threshold_multiplier': 2.0,
            'efficiency_drop_threshold': 0.2,
            'utilization_low_threshold': 0.3,
            'moving_average_window': 20
        }
        
        self.logger.info("✅ Real-time Cost Monitor initialized")
    
    # ==================== 監控控制 ====================
    
    async def start_monitoring(self) -> bool:
        """開始監控"""
        try:
            if self.is_monitoring:
                self.logger.warning("Monitoring is already running")
                return True
            
            # 啟動WebSocket服務器
            if self.config.get('websocket_enabled', True):
                await self._start_websocket_server()
            
            # 啟動監控任務
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            self.logger.info("✅ Real-time monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error starting monitoring: {e}")
            return False
    
    async def stop_monitoring(self) -> bool:
        """停止監控"""
        try:
            self.is_monitoring = False
            
            # 停止監控任務
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # 停止WebSocket服務器
            if self.websocket_server:
                self.websocket_server.close()
                await self.websocket_server.wait_closed()
            
            # 關閉線程池
            self.executor.shutdown(wait=True)
            
            self.logger.info("✅ Real-time monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping monitoring: {e}")
            return False
    
    async def _monitoring_loop(self):
        """監控主循環"""
        while self.is_monitoring:
            try:
                # 收集監控指標
                await self._collect_monitoring_metrics()
                
                # 評估告警規則
                await self._evaluate_alert_rules()
                
                # 執行異常檢測
                if self.config['anomaly_detection_enabled']:
                    await self._detect_anomalies()
                
                # 執行趨勢分析
                if self.config['trend_analysis_enabled']:
                    await self._analyze_trends()
                
                # 自動優化
                if self.config['auto_optimization_enabled']:
                    await self._perform_auto_optimization()
                
                # 清理舊數據
                await self._cleanup_old_data()
                
                # 廣播更新到WebSocket客戶端
                await self._broadcast_updates()
                
                # 等待下一個監控周期
                await asyncio.sleep(self.monitoring_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(min(self.monitoring_interval_seconds, 30))
    
    # ==================== 指標收集 ====================
    
    async def _collect_monitoring_metrics(self):
        """收集監控指標"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # 收集硬體成本指標
            await self._collect_hardware_metrics(current_time)
            
            # 收集電力和維護成本指標
            await self._collect_power_maintenance_metrics(current_time)
            
            # 收集人力成本指標
            await self._collect_labor_metrics(current_time)
            
            # 管理指標歷史大小
            if len(self.metrics_history) > self.config['max_metrics_history']:
                self.metrics_history = self.metrics_history[-self.config['max_metrics_history']:]
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting monitoring metrics: {e}")
    
    async def _collect_hardware_metrics(self, timestamp: datetime):
        """收集硬體指標"""
        try:
            # 獲取所有硬體資產的成本
            period_start = timestamp - timedelta(hours=1)
            period_end = timestamp
            
            hardware_costs = await self.hardware_calculator.calculate_all_hardware_costs(
                timestamp.date(), period_start.date(), period_end.date()
            )
            
            for asset_id, cost_result in hardware_costs.items():
                metrics = MonitoringMetrics(
                    timestamp=timestamp,
                    target_id=asset_id,
                    target_type=MonitoringScope.ASSET,
                    total_cost=cost_result.total_cost,
                    hardware_cost=cost_result.total_cost,
                    utilization_rate=cost_result.utilization_rate,
                    cost_per_unit=cost_result.cost_per_token
                )
                
                self.metrics_history.append(metrics)
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting hardware metrics: {e}")
    
    async def _collect_power_maintenance_metrics(self, timestamp: datetime):
        """收集電力和維護指標"""
        try:
            # 這裡需要實現獲取資產列表的邏輯
            # 暫時使用示例代碼
            asset_ids = ['gpu_001', 'gpu_002']  # 示例資產ID
            
            for asset_id in asset_ids:
                period_start = timestamp - timedelta(hours=1)
                period_end = timestamp
                
                cost_result = await self.power_tracker.calculate_comprehensive_costs(
                    asset_id, period_start, period_end
                )
                
                metrics = MonitoringMetrics(
                    timestamp=timestamp,
                    target_id=asset_id,
                    target_type=MonitoringScope.ASSET,
                    total_cost=cost_result.total_cost,
                    power_cost=cost_result.total_electricity_cost,
                    maintenance_cost=cost_result.total_maintenance_cost,
                    power_usage_effectiveness=cost_result.power_usage_effectiveness or 1.0
                )
                
                self.metrics_history.append(metrics)
                
        except Exception as e:
            self.logger.error(f"❌ Error collecting power/maintenance metrics: {e}")
    
    async def _collect_labor_metrics(self, timestamp: datetime):
        """收集人力成本指標"""
        try:
            # 獲取所有活躍員工的成本分攤結果
            employee_ids = list(self.labor_allocator.employees.keys())
            
            for employee_id in employee_ids:
                if self.labor_allocator.employees[employee_id].is_active:
                    # 計算當月成本
                    start_of_month = timestamp.replace(day=1).date()
                    end_of_month = timestamp.date()
                    
                    cost_result = await self.labor_allocator.calculate_labor_cost_allocation(
                        employee_id, start_of_month, end_of_month
                    )
                    
                    metrics = MonitoringMetrics(
                        timestamp=timestamp,
                        target_id=employee_id,
                        target_type=MonitoringScope.ASSET,
                        total_cost=cost_result.total_cost,
                        labor_cost=cost_result.total_cost,
                        utilization_rate=cost_result.utilization_rate,
                        quality_score=cost_result.average_quality_score or 1.0
                    )
                    
                    self.metrics_history.append(metrics)
                    
        except Exception as e:
            self.logger.error(f"❌ Error collecting labor metrics: {e}")
    
    # ==================== 告警管理 ====================
    
    def create_alert_rule(self, rule: AlertRule) -> bool:
        """創建告警規則"""
        try:
            # 驗證規則
            if not self._validate_alert_rule(rule):
                raise ValueError(f"Invalid alert rule: {rule.rule_id}")
            
            self.alert_rules[rule.rule_id] = rule
            
            self.logger.info(f"✅ Created alert rule: {rule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating alert rule: {e}")
            return False
    
    async def _evaluate_alert_rules(self):
        """評估告警規則"""
        try:
            current_time = datetime.now(timezone.utc)
            
            for rule in self.alert_rules.values():
                if not rule.is_active or self._is_rule_suppressed(rule, current_time):
                    continue
                
                try:
                    await self._evaluate_single_rule(rule, current_time)
                except Exception as e:
                    self.logger.error(f"❌ Error evaluating rule {rule.rule_id}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating alert rules: {e}")
    
    async def _evaluate_single_rule(self, rule: AlertRule, current_time: datetime):
        """評估單個告警規則"""
        # 獲取相關指標
        relevant_metrics = self._get_relevant_metrics(rule, current_time)
        
        if not relevant_metrics:
            return
        
        # 評估閾值
        is_breach = False
        breach_metrics = []
        
        for metrics in relevant_metrics:
            current_value = self._get_metric_value(metrics, rule.metric_type)
            
            if self._evaluate_threshold(current_value, rule):
                is_breach = True
                breach_metrics.append((metrics, current_value))
        
        # 更新連續違規計數
        if is_breach:
            rule.consecutive_breaches += 1
        else:
            rule.consecutive_breaches = 0
        
        rule.last_evaluated_at = current_time
        
        # 檢查是否需要觸發告警
        if (rule.consecutive_breaches >= rule.consecutive_breaches_required and
            is_breach):
            await self._trigger_alert(rule, breach_metrics, current_time)
    
    def _get_relevant_metrics(self, rule: AlertRule, current_time: datetime) -> List[MonitoringMetrics]:
        """獲取相關指標"""
        cutoff_time = current_time - timedelta(minutes=rule.evaluation_period_minutes)
        
        relevant_metrics = []
        for metrics in self.metrics_history:
            if metrics.timestamp >= cutoff_time:
                if rule.scope == MonitoringScope.ASSET and metrics.target_id in rule.target_ids:
                    relevant_metrics.append(metrics)
                elif rule.scope == MonitoringScope.ORGANIZATION:  # 全局監控
                    relevant_metrics.append(metrics)
        
        return relevant_metrics
    
    def _get_metric_value(self, metrics: MonitoringMetrics, metric_type: MetricType) -> Union[Decimal, float]:
        """獲取指標值"""
        if metric_type == MetricType.COST:
            return metrics.total_cost
        elif metric_type == MetricType.POWER_CONSUMPTION:
            return metrics.power_cost
        elif metric_type == MetricType.UTILIZATION:
            return metrics.utilization_rate
        elif metric_type == MetricType.EFFICIENCY:
            return metrics.power_usage_effectiveness
        elif metric_type == MetricType.QUALITY:
            return metrics.quality_score
        else:
            return Decimal('0')
    
    def _evaluate_threshold(self, current_value: Union[Decimal, float], rule: AlertRule) -> bool:
        """評估閾值"""
        if rule.threshold_value is None:
            return False
        
        threshold = rule.threshold_value
        
        if rule.comparison_operator == "greater_than":
            return current_value > threshold
        elif rule.comparison_operator == "less_than":
            return current_value < threshold
        elif rule.comparison_operator == "equal":
            return abs(float(current_value - threshold)) < 0.01
        elif rule.comparison_operator == "not_equal":
            return abs(float(current_value - threshold)) >= 0.01
        
        return False
    
    async def _trigger_alert(
        self,
        rule: AlertRule,
        breach_metrics: List[Tuple[MonitoringMetrics, Union[Decimal, float]]],
        current_time: datetime
    ):
        """觸發告警"""
        try:
            # 創建告警
            for metrics, current_value in breach_metrics:
                alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    alert_type=rule.alert_type,
                    title=f"{rule.name} - {metrics.target_id}",
                    message=self._generate_alert_message(rule, metrics, current_value),
                    target_id=metrics.target_id,
                    target_type=rule.scope,
                    metric_type=rule.metric_type,
                    current_value=current_value,
                    threshold_value=rule.threshold_value or 0,
                    context_data=metrics.to_dict(),
                    suggested_actions=self._generate_suggested_actions(rule, metrics)
                )
                
                self.active_alerts[alert.alert_id] = alert
                self.alert_history.append(alert)
                
                # 發送通知
                if rule.notification_enabled:
                    await self._send_notification(alert, rule)
                
                # 執行自動動作
                if rule.auto_action_enabled and rule.auto_action_script:
                    await self._execute_auto_action(alert, rule)
            
            rule.last_triggered_at = current_time
            
            # 設置抑制期
            if rule.suppression_duration_minutes > 0:
                rule.is_suppressed = True
                rule.suppressed_until = current_time + timedelta(minutes=rule.suppression_duration_minutes)
            
        except Exception as e:
            self.logger.error(f"❌ Error triggering alert: {e}")
    
    def _generate_alert_message(
        self,
        rule: AlertRule,
        metrics: MonitoringMetrics,
        current_value: Union[Decimal, float]
    ) -> str:
        """生成告警消息"""
        metric_name = rule.metric_type.value.replace('_', ' ').title()
        
        if isinstance(current_value, Decimal):
            value_str = f"${current_value:.2f}" if rule.metric_type == MetricType.COST else f"{current_value:.4f}"
        else:
            value_str = f"{current_value:.4f}"
        
        threshold_str = f"${rule.threshold_value:.2f}" if rule.metric_type == MetricType.COST else f"{rule.threshold_value:.4f}"
        
        return (f"{metric_name} for {metrics.target_id} is {value_str}, "
                f"which {rule.comparison_operator.replace('_', ' ')} threshold of {threshold_str}")
    
    def _generate_suggested_actions(self, rule: AlertRule, metrics: MonitoringMetrics) -> List[str]:
        """生成建議動作"""
        actions = []
        
        if rule.alert_type == AlertType.COST_THRESHOLD:
            actions.extend([
                "Review resource utilization and optimize usage",
                "Check for unnecessary resource allocation",
                "Consider scaling down if appropriate"
            ])
        elif rule.alert_type == AlertType.UTILIZATION_LOW:
            actions.extend([
                "Redistribute workload to improve utilization",
                "Consider resource consolidation",
                "Review capacity planning"
            ])
        elif rule.alert_type == AlertType.EFFICIENCY_DROP:
            actions.extend([
                "Check system performance metrics",
                "Investigate potential bottlenecks",
                "Review configuration settings"
            ])
        
        return actions
    
    def _is_rule_suppressed(self, rule: AlertRule, current_time: datetime) -> bool:
        """檢查規則是否被抑制"""
        if not rule.is_suppressed:
            return False
        
        if rule.suppressed_until and current_time > rule.suppressed_until:
            rule.is_suppressed = False
            rule.suppressed_until = None
            return False
        
        return True
    
    # ==================== 異常檢測 ====================
    
    async def _detect_anomalies(self):
        """檢測異常"""
        try:
            # 檢測成本異常激增
            await self._detect_cost_spikes()
            
            # 檢測效率異常下降
            await self._detect_efficiency_drops()
            
            # 檢測利用率異常
            await self._detect_utilization_anomalies()
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting anomalies: {e}")
    
    async def _detect_cost_spikes(self):
        """檢測成本激增"""
        if len(self.metrics_history) < self.anomaly_config['moving_average_window']:
            return
        
        # 按資產分組
        asset_metrics = {}
        for metrics in self.metrics_history[-50:]:  # 最近50個數據點
            if metrics.target_id not in asset_metrics:
                asset_metrics[metrics.target_id] = []
            asset_metrics[metrics.target_id].append(metrics)
        
        for asset_id, metrics_list in asset_metrics.items():
            if len(metrics_list) < self.anomaly_config['moving_average_window']:
                continue
            
            # 計算移動平均
            recent_costs = [float(m.total_cost) for m in metrics_list[-10:]]
            historical_costs = [float(m.total_cost) for m in metrics_list[:-10]]
            
            if not historical_costs:
                continue
            
            avg_historical = statistics.mean(historical_costs)
            avg_recent = statistics.mean(recent_costs)
            
            # 檢測激增
            spike_threshold = avg_historical * self.anomaly_config['cost_spike_threshold_multiplier']
            
            if avg_recent > spike_threshold:
                await self._create_anomaly_alert(
                    AlertType.COST_SPIKE,
                    asset_id,
                    f"Cost spike detected: {avg_recent:.2f} vs historical average {avg_historical:.2f}",
                    avg_recent,
                    spike_threshold
                )
    
    async def _detect_efficiency_drops(self):
        """檢測效率下降"""
        if len(self.metrics_history) < self.anomaly_config['moving_average_window']:
            return
        
        # 按資產分組檢測PUE異常
        asset_metrics = {}
        for metrics in self.metrics_history[-50:]:
            if metrics.power_usage_effectiveness > 0:  # 過濾有效PUE數據
                if metrics.target_id not in asset_metrics:
                    asset_metrics[metrics.target_id] = []
                asset_metrics[metrics.target_id].append(metrics)
        
        for asset_id, metrics_list in asset_metrics.items():
            if len(metrics_list) < 10:
                continue
            
            recent_pue = [m.power_usage_effectiveness for m in metrics_list[-5:]]
            historical_pue = [m.power_usage_effectiveness for m in metrics_list[:-5]]
            
            if not historical_pue:
                continue
            
            avg_historical = statistics.mean(historical_pue)
            avg_recent = statistics.mean(recent_pue)
            
            # 檢測效率下降（PUE增加）
            efficiency_drop = (avg_recent - avg_historical) / avg_historical
            
            if efficiency_drop > self.anomaly_config['efficiency_drop_threshold']:
                await self._create_anomaly_alert(
                    AlertType.EFFICIENCY_DROP,
                    asset_id,
                    f"Efficiency drop detected: PUE increased from {avg_historical:.2f} to {avg_recent:.2f}",
                    avg_recent,
                    avg_historical
                )
    
    async def _detect_utilization_anomalies(self):
        """檢測利用率異常"""
        if len(self.metrics_history) < 20:
            return
        
        # 按資產檢測利用率過低
        asset_metrics = {}
        for metrics in self.metrics_history[-30:]:
            if metrics.target_id not in asset_metrics:
                asset_metrics[metrics.target_id] = []
            asset_metrics[metrics.target_id].append(metrics)
        
        for asset_id, metrics_list in asset_metrics.items():
            if len(metrics_list) < 10:
                continue
            
            recent_utilization = [m.utilization_rate for m in metrics_list[-10:]]
            avg_utilization = statistics.mean(recent_utilization)
            
            if avg_utilization < self.anomaly_config['utilization_low_threshold']:
                await self._create_anomaly_alert(
                    AlertType.UTILIZATION_LOW,
                    asset_id,
                    f"Low utilization detected: {avg_utilization:.1%}",
                    avg_utilization,
                    self.anomaly_config['utilization_low_threshold']
                )
    
    async def _create_anomaly_alert(
        self,
        alert_type: AlertType,
        target_id: str,
        message: str,
        current_value: float,
        threshold_value: float
    ):
        """創建異常告警"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id="anomaly_detector",
            severity=AlertSeverity.WARNING,
            alert_type=alert_type,
            title=f"Anomaly Detected - {target_id}",
            message=message,
            target_id=target_id,
            target_type=MonitoringScope.ASSET,
            metric_type=MetricType.COST if alert_type == AlertType.COST_SPIKE else MetricType.EFFICIENCY,
            current_value=current_value,
            threshold_value=threshold_value,
            suggested_actions=self._get_anomaly_actions(alert_type)
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
        
        # 發送通知
        await self._send_notification(alert)
    
    def _get_anomaly_actions(self, alert_type: AlertType) -> List[str]:
        """獲取異常處理建議"""
        if alert_type == AlertType.COST_SPIKE:
            return [
                "Investigate recent changes in usage patterns",
                "Check for resource leaks or inefficient processes",
                "Review recent deployment changes",
                "Consider implementing cost controls"
            ]
        elif alert_type == AlertType.EFFICIENCY_DROP:
            return [
                "Check hardware health and temperature",
                "Review system configuration changes",
                "Investigate cooling system performance",
                "Consider maintenance requirements"
            ]
        elif alert_type == AlertType.UTILIZATION_LOW:
            return [
                "Redistribute workloads across resources",
                "Consider scaling down underutilized resources",
                "Review capacity planning assumptions",
                "Investigate demand patterns"
            ]
        return []
    
    # ==================== 趨勢分析 ====================
    
    async def _analyze_trends(self):
        """分析趨勢"""
        try:
            # 成本趨勢分析
            await self._analyze_cost_trends()
            
            # 效率趨勢分析
            await self._analyze_efficiency_trends()
            
            # 預測未來趨勢
            await self._predict_future_trends()
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing trends: {e}")
    
    async def _analyze_cost_trends(self):
        """分析成本趨勢"""
        if len(self.metrics_history) < 50:
            return
        
        # 計算24小時成本趨勢
        recent_24h = [m for m in self.metrics_history 
                     if m.timestamp > datetime.now(timezone.utc) - timedelta(hours=24)]
        
        if len(recent_24h) < 10:
            return
        
        # 按小時分組
        hourly_costs = {}
        for metrics in recent_24h:
            hour_key = metrics.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_costs:
                hourly_costs[hour_key] = []
            hourly_costs[hour_key].append(float(metrics.total_cost))
        
        # 計算每小時平均成本
        hourly_averages = []
        for hour, costs in sorted(hourly_costs.items()):
            if costs:
                hourly_averages.append(statistics.mean(costs))
        
        if len(hourly_averages) < 6:
            return
        
        # 簡單線性趨勢檢測
        recent_avg = statistics.mean(hourly_averages[-3:])
        earlier_avg = statistics.mean(hourly_averages[:3])
        
        if recent_avg > earlier_avg * 1.2:  # 成本上升超過20%
            await self._create_trend_alert(
                "Cost Increasing Trend",
                f"Cost trend is increasing: {recent_avg:.2f} vs {earlier_avg:.2f}",
                recent_avg,
                earlier_avg
            )
    
    async def _analyze_efficiency_trends(self):
        """分析效率趨勢"""
        # 類似成本趨勢分析的邏輯
        pass
    
    async def _predict_future_trends(self):
        """預測未來趨勢"""
        # 實現簡單的線性預測
        pass
    
    async def _create_trend_alert(
        self,
        title: str,
        message: str,
        current_value: float,
        baseline_value: float
    ):
        """創建趨勢告警"""
        alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id="trend_analyzer",
            severity=AlertSeverity.INFO,
            alert_type=AlertType.TREND_WARNING,
            title=title,
            message=message,
            target_id="organization",
            target_type=MonitoringScope.ORGANIZATION,
            metric_type=MetricType.COST,
            current_value=current_value,
            threshold_value=baseline_value
        )
        
        self.active_alerts[alert.alert_id] = alert
        self.alert_history.append(alert)
    
    # ==================== 通知和WebSocket ====================
    
    async def _send_notification(self, alert: Alert, rule: Optional[AlertRule] = None):
        """發送通知"""
        try:
            notification_data = {
                'type': 'alert',
                'alert': alert.to_dict()
            }
            
            # 發送到WebSocket客戶端
            await self._broadcast_to_websockets(notification_data)
            
            # 其他通知渠道（郵件、Slack等）可以在這裡實現
            
        except Exception as e:
            self.logger.error(f"❌ Error sending notification: {e}")
    
    async def _start_websocket_server(self):
        """啟動WebSocket服務器"""
        try:
            async def handle_client(websocket, path):
                self.websocket_clients.add(websocket)
                try:
                    # 發送初始數據
                    initial_data = {
                        'type': 'initial',
                        'active_alerts': [alert.to_dict() for alert in self.active_alerts.values()],
                        'recent_metrics': [m.to_dict() for m in self.metrics_history[-100:]]
                    }
                    await websocket.send(json.dumps(initial_data))
                    
                    # 保持連接
                    await websocket.wait_closed()
                except websockets.exceptions.ConnectionClosed:
                    pass
                finally:
                    self.websocket_clients.discard(websocket)
            
            self.websocket_server = await websockets.serve(
                handle_client,
                "localhost",
                self.config['websocket_port']
            )
            
            self.logger.info(f"✅ WebSocket server started on port {self.config['websocket_port']}")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting WebSocket server: {e}")
    
    async def _broadcast_to_websockets(self, data: Dict[str, Any]):
        """廣播到WebSocket客戶端"""
        if not self.websocket_clients:
            return
        
        message = json.dumps(data)
        
        # 創建弱引用副本以避免在迭代過程中修改集合
        clients_copy = self.websocket_clients.copy()
        
        for client in clients_copy:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                self.websocket_clients.discard(client)
            except Exception as e:
                self.logger.error(f"❌ Error broadcasting to client: {e}")
                self.websocket_clients.discard(client)
    
    async def _broadcast_updates(self):
        """廣播更新"""
        try:
            if not self.websocket_clients:
                return
            
            # 準備更新數據
            update_data = {
                'type': 'update',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'active_alerts_count': len(self.active_alerts),
                'recent_metrics': [m.to_dict() for m in self.metrics_history[-10:]]
            }
            
            await self._broadcast_to_websockets(update_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error broadcasting updates: {e}")
    
    # ==================== 自動優化 ====================
    
    async def _perform_auto_optimization(self):
        """執行自動優化"""
        try:
            # 檢查是否有可以自動優化的場景
            await self._optimize_underutilized_resources()
            await self._optimize_cost_allocation()
            
        except Exception as e:
            self.logger.error(f"❌ Error performing auto optimization: {e}")
    
    async def _optimize_underutilized_resources(self):
        """優化利用率不足的資源"""
        # 識別利用率過低的資源
        underutilized_assets = []
        
        for metrics in self.metrics_history[-20:]:
            if metrics.utilization_rate < 0.3:  # 利用率低於30%
                underutilized_assets.append(metrics.target_id)
        
        # 統計頻繁出現的低利用率資產
        asset_counts = {}
        for asset_id in underutilized_assets:
            asset_counts[asset_id] = asset_counts.get(asset_id, 0) + 1
        
        # 對持續低利用率的資產提出優化建議
        for asset_id, count in asset_counts.items():
            if count >= 10:  # 連續10次監控週期都低利用率
                optimization_alert = Alert(
                    alert_id=str(uuid.uuid4()),
                    rule_id="auto_optimizer",
                    severity=AlertSeverity.INFO,
                    alert_type=AlertType.UTILIZATION_LOW,
                    title=f"Auto Optimization Suggestion - {asset_id}",
                    message=f"Asset {asset_id} has been consistently underutilized. Consider scaling down or redistributing workload.",
                    target_id=asset_id,
                    target_type=MonitoringScope.ASSET,
                    metric_type=MetricType.UTILIZATION,
                    current_value=0.3,
                    threshold_value=0.7,
                    suggested_actions=[
                        "Scale down resource allocation",
                        "Redistribute workload to this asset",
                        "Consider shutting down during low-demand periods",
                        "Evaluate if resource is still needed"
                    ]
                )
                
                self.active_alerts[optimization_alert.alert_id] = optimization_alert
                await self._send_notification(optimization_alert)
    
    async def _optimize_cost_allocation(self):
        """優化成本分攤"""
        # 分析成本分配效率
        pass
    
    # ==================== 數據清理 ====================
    
    async def _cleanup_old_data(self):
        """清理舊數據"""
        try:
            current_time = datetime.now(timezone.utc)
            cutoff_time = current_time - timedelta(days=self.config['data_retention_days'])
            
            # 清理舊指標
            self.metrics_history = [
                m for m in self.metrics_history if m.timestamp >= cutoff_time
            ]
            
            # 清理舊告警歷史
            if len(self.alert_history) > self.config['max_alert_history']:
                self.alert_history = self.alert_history[-self.config['max_alert_history']:]
            
            # 清理已解決的活躍告警
            resolved_alerts = [
                alert_id for alert_id, alert in self.active_alerts.items()
                if alert.resolved_at and alert.resolved_at < cutoff_time
            ]
            
            for alert_id in resolved_alerts:
                del self.active_alerts[alert_id]
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old data: {e}")
    
    # ==================== 告警操作 ====================
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """確認告警"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.is_acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now(timezone.utc)
            
            # 廣播更新
            update_data = {
                'type': 'alert_acknowledged',
                'alert_id': alert_id,
                'acknowledged_by': acknowledged_by
            }
            await self._broadcast_to_websockets(update_data)
            
            self.logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error acknowledging alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolution_note: str) -> bool:
        """解決告警"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.is_active = False
            alert.resolved_at = datetime.now(timezone.utc)
            alert.resolution_note = resolution_note
            
            # 移出活躍告警
            del self.active_alerts[alert_id]
            
            # 廣播更新
            update_data = {
                'type': 'alert_resolved',
                'alert_id': alert_id,
                'resolution_note': resolution_note
            }
            await self._broadcast_to_websockets(update_data)
            
            self.logger.info(f"✅ Alert {alert_id} resolved")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error resolving alert: {e}")
            return False
    
    # ==================== 輔助方法 ====================
    
    def _validate_alert_rule(self, rule: AlertRule) -> bool:
        """驗證告警規則"""
        if not rule.rule_id or not rule.name:
            return False
        
        if rule.threshold_value is None and rule.threshold_percentage is None:
            return False
        
        if rule.evaluation_period_minutes <= 0:
            return False
        
        if rule.consecutive_breaches_required <= 0:
            return False
        
        return True
    
    async def _execute_auto_action(self, alert: Alert, rule: AlertRule):
        """執行自動動作"""
        try:
            # 這裡可以實現各種自動化動作
            # 例如：調用API、執行腳本、發送通知等
            self.logger.info(f"Executing auto action for alert {alert.alert_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error executing auto action: {e}")
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """實時成本監控器健康檢查"""
        health_status = {
            'system': 'realtime_cost_monitor',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # 檢查監控狀態
            health_status['components']['monitoring'] = {
                'is_running': self.is_monitoring,
                'interval_seconds': self.monitoring_interval_seconds
            }
            
            # 檢查數據統計
            health_status['components']['data'] = {
                'metrics_count': len(self.metrics_history),
                'active_alerts_count': len(self.active_alerts),
                'alert_rules_count': len(self.alert_rules),
                'alert_history_count': len(self.alert_history)
            }
            
            # 檢查WebSocket連接
            health_status['components']['websocket'] = {
                'server_running': self.websocket_server is not None,
                'clients_connected': len(self.websocket_clients),
                'port': self.config['websocket_port']
            }
            
            # 檢查組件健康
            hardware_health = await self.hardware_calculator.health_check()
            power_health = await self.power_tracker.health_check()
            labor_health = await self.labor_allocator.health_check()
            
            health_status['components']['cost_calculators'] = {
                'hardware': hardware_health['status'],
                'power_maintenance': power_health['status'],
                'labor': labor_health['status']
            }
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Real-time cost monitor health check failed: {e}")
        
        return health_status


# ==================== 預設配置工廠 ====================

class AlertConfigurationFactory:
    """告警配置工廠"""
    
    @staticmethod
    def create_cost_threshold_rule(
        rule_id: str,
        target_ids: List[str],
        threshold_amount: float,
        severity: AlertSeverity = AlertSeverity.WARNING
    ) -> AlertRule:
        """創建成本閾值告警規則"""
        return AlertRule(
            rule_id=rule_id,
            name=f"Cost Threshold Alert - ${threshold_amount}",
            alert_type=AlertType.COST_THRESHOLD,
            severity=severity,
            scope=MonitoringScope.ASSET,
            target_ids=target_ids,
            metric_type=MetricType.COST,
            threshold_value=Decimal(str(threshold_amount)),
            comparison_operator="greater_than",
            evaluation_period_minutes=15,
            consecutive_breaches_required=2,
            notification_enabled=True
        )
    
    @staticmethod
    def create_utilization_rule(
        rule_id: str,
        target_ids: List[str],
        minimum_utilization: float = 0.3,
        severity: AlertSeverity = AlertSeverity.INFO
    ) -> AlertRule:
        """創建利用率告警規則"""
        return AlertRule(
            rule_id=rule_id,
            name=f"Low Utilization Alert - {minimum_utilization:.0%}",
            alert_type=AlertType.UTILIZATION_LOW,
            severity=severity,
            scope=MonitoringScope.ASSET,
            target_ids=target_ids,
            metric_type=MetricType.UTILIZATION,
            threshold_value=Decimal(str(minimum_utilization)),
            comparison_operator="less_than",
            evaluation_period_minutes=30,
            consecutive_breaches_required=3,
            notification_enabled=True
        )
    
    @staticmethod
    def create_budget_overrun_rule(
        rule_id: str,
        cost_center_ids: List[str],
        budget_limit: float,
        warning_threshold: float = 0.8,
        severity: AlertSeverity = AlertSeverity.CRITICAL
    ) -> AlertRule:
        """創建預算超支告警規則"""
        return AlertRule(
            rule_id=rule_id,
            name=f"Budget Overrun Alert - ${budget_limit}",
            alert_type=AlertType.BUDGET_OVERRUN,
            severity=severity,
            scope=MonitoringScope.COST_CENTER,
            target_ids=cost_center_ids,
            metric_type=MetricType.COST,
            threshold_value=Decimal(str(budget_limit * warning_threshold)),
            comparison_operator="greater_than",
            evaluation_period_minutes=60,
            consecutive_breaches_required=1,
            notification_enabled=True,
            notification_channels=['email', 'slack']
        )