#!/usr/bin/env python3
"""
Capability Alert System
能力變化告警系統 - GPT-OSS整合任務1.2.3
實現智能的模型能力監控和告警機制
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional, Callable, Set
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..monitoring.performance_monitor import PerformanceMonitor, MetricType
from ..database.model_capability_db import ModelCapabilityDB
from .model_version_manager import ModelVersionManager

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """告警嚴重程度"""
    CRITICAL = "critical"    # 嚴重：服務可能中斷
    HIGH = "high"           # 高：性能明顯下降
    MEDIUM = "medium"       # 中：性能輕微下降
    LOW = "low"            # 低：趨勢性變化
    INFO = "info"          # 信息：正面變化

class AlertType(Enum):
    """告警類型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CAPABILITY_IMPROVEMENT = "capability_improvement"
    MODEL_UNAVAILABLE = "model_unavailable"
    COST_INCREASE = "cost_increase"
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"
    ACCURACY_DROP = "accuracy_drop"
    VERSION_CHANGE = "version_change"

@dataclass
class AlertRule:
    """告警規則"""
    name: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    enabled: bool = True
    
    # 觸發條件
    metric_thresholds: Dict[str, float] = field(default_factory=dict)
    time_window_minutes: int = 15
    min_sample_count: int = 3
    
    # 告警控制
    cooldown_minutes: int = 30
    max_alerts_per_hour: int = 5
    escalation_threshold: int = 3  # 連續觸發次數
    
    # 過濾條件
    provider_filter: Optional[str] = None
    model_filter: Optional[str] = None
    
    # 狀態追蹤
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    consecutive_triggers: int = 0
    alert_count_last_hour: int = 0

    def can_trigger(self) -> bool:
        """檢查是否可以觸發告警"""
        now = datetime.now(timezone.utc)
        
        # 檢查冷卻期
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if now < cooldown_end:
                return False
        
        # 檢查每小時限制
        if self.alert_count_last_hour >= self.max_alerts_per_hour:
            return False
        
        return self.enabled

    def record_trigger(self):
        """記錄觸發"""
        now = datetime.now(timezone.utc)
        
        # 重置每小時計數
        if not self.last_triggered or (now - self.last_triggered).total_seconds() > 3600:
            self.alert_count_last_hour = 0
        
        self.last_triggered = now
        self.trigger_count += 1
        self.consecutive_triggers += 1
        self.alert_count_last_hour += 1

    def reset_consecutive_triggers(self):
        """重置連續觸發計數"""
        self.consecutive_triggers = 0

@dataclass
class Alert:
    """告警實例"""
    id: str
    rule: AlertRule
    provider: str
    model_id: str
    severity: AlertSeverity
    alert_type: AlertType
    title: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    escalated: bool = False
    escalated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'id': self.id,
            'rule_name': self.rule.name,
            'provider': self.provider,
            'model_id': self.model_id,
            'severity': self.severity.value,
            'alert_type': self.alert_type.value,
            'title': self.title,
            'message': self.message,
            'details': self.details,
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved': self.resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'escalated': self.escalated,
            'escalated_at': self.escalated_at.isoformat() if self.escalated_at else None
        }

    def acknowledge(self, user: str = "system"):
        """確認告警"""
        if not self.acknowledged:
            self.acknowledged = True
            self.acknowledged_at = datetime.now(timezone.utc)
            self.acknowledged_by = user

    def resolve(self):
        """解決告警"""
        if not self.resolved:
            self.resolved = True
            self.resolved_at = datetime.now(timezone.utc)

    def escalate(self):
        """升級告警"""
        if not self.escalated:
            self.escalated = True
            self.escalated_at = datetime.now(timezone.utc)
            
            # 提升嚴重程度
            severity_levels = [AlertSeverity.INFO, AlertSeverity.LOW, AlertSeverity.MEDIUM, AlertSeverity.HIGH, AlertSeverity.CRITICAL]
            current_index = severity_levels.index(self.severity)
            if current_index < len(severity_levels) - 1:
                self.severity = severity_levels[current_index + 1]

class AlertHandler:
    """告警處理器基類"""
    
    async def handle_alert(self, alert: Alert) -> bool:
        """處理告警"""
        pass

class LogAlertHandler(AlertHandler):
    """日誌告警處理器"""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
    
    async def handle_alert(self, alert: Alert) -> bool:
        """記錄告警到日誌"""
        try:
            log_level = {
                AlertSeverity.CRITICAL: logging.CRITICAL,
                AlertSeverity.HIGH: logging.ERROR,
                AlertSeverity.MEDIUM: logging.WARNING,
                AlertSeverity.LOW: logging.INFO,
                AlertSeverity.INFO: logging.INFO
            }.get(alert.severity, logging.INFO)
            
            self.logger.log(
                log_level,
                f"🚨 Alert: {alert.title} | {alert.provider}/{alert.model_id} | {alert.message}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error handling alert: {e}")
            return False

class EmailAlertHandler(AlertHandler):
    """郵件告警處理器"""
    
    def __init__(self, email_config: Dict[str, Any]):
        self.email_config = email_config
        # 這裡可以初始化郵件發送配置
    
    async def handle_alert(self, alert: Alert) -> bool:
        """發送郵件告警"""
        try:
            # 這裡應該實現實際的郵件發送邏輯
            logger.info(f"📧 Email alert sent for: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending email alert: {e}")
            return False

class WebhookAlertHandler(AlertHandler):
    """Webhook告警處理器"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def handle_alert(self, alert: Alert) -> bool:
        """發送Webhook告警"""
        try:
            import aiohttp
            
            payload = alert.to_dict()
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers
                ) as response:
                    if response.status == 200:
                        logger.info(f"📡 Webhook alert sent for: {alert.title}")
                        return True
                    else:
                        logger.error(f"❌ Webhook failed with status {response.status}")
                        return False
            
        except Exception as e:
            logger.error(f"❌ Error sending webhook alert: {e}")
            return False

class CapabilityAlertSystem:
    """
    能力變化告警系統
    
    功能：
    1. 監控模型能力變化
    2. 基於規則生成告警
    3. 管理告警生命周期
    4. 支援多種告警處理方式
    5. 提供告警統計和分析
    """
    
    def __init__(
        self,
        performance_monitor: Optional[PerformanceMonitor] = None,
        model_db: Optional[ModelCapabilityDB] = None,
        version_manager: Optional[ModelVersionManager] = None,
        storage_path: Optional[str] = None
    ):
        """
        初始化告警系統
        
        Args:
            performance_monitor: 性能監控器
            model_db: 模型能力數據庫
            version_manager: 版本管理器
            storage_path: 告警數據存儲路徑
        """
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.model_db = model_db or ModelCapabilityDB()
        self.version_manager = version_manager or ModelVersionManager()
        
        self.storage_path = Path(storage_path or "alerts")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 告警規則
        self.alert_rules: Dict[str, AlertRule] = {}
        
        # 活躍告警
        self.active_alerts: Dict[str, Alert] = {}
        
        # 告警歷史
        self.alert_history: List[Alert] = []
        
        # 告警處理器
        self.alert_handlers: List[AlertHandler] = []
        
        # 統計數據
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': {},
            'alerts_by_type': {},
            'alerts_by_model': {}
        }
        
        self.logger = logger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
        
        # 加載現有數據
        self._load_existing_data()
    
    def _load_existing_data(self):
        """加載現有數據"""
        try:
            # 加載告警規則
            rules_file = self.storage_path / "alert_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                for rule_data in rules_data.get('rules', []):
                    rule = AlertRule(
                        name=rule_data['name'],
                        description=rule_data['description'],
                        alert_type=AlertType(rule_data['alert_type']),
                        severity=AlertSeverity(rule_data['severity']),
                        enabled=rule_data.get('enabled', True),
                        metric_thresholds=rule_data.get('metric_thresholds', {}),
                        time_window_minutes=rule_data.get('time_window_minutes', 15),
                        cooldown_minutes=rule_data.get('cooldown_minutes', 30)
                    )
                    self.alert_rules[rule.name] = rule
            
            # 加載告警歷史（最近1000條）
            history_file = self.storage_path / "alert_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                
                self.stats = history_data.get('stats', self.stats)
                # 簡化實現，不加載完整歷史
            
            self.logger.info(f"✅ Loaded {len(self.alert_rules)} alert rules")
            
        except Exception as e:
            self.logger.error(f"❌ Error loading alert data: {e}")
    
    def _save_data(self):
        """保存數據"""
        try:
            # 保存告警規則
            rules_data = {
                'rules': [
                    {
                        'name': rule.name,
                        'description': rule.description,
                        'alert_type': rule.alert_type.value,
                        'severity': rule.severity.value,
                        'enabled': rule.enabled,
                        'metric_thresholds': rule.metric_thresholds,
                        'time_window_minutes': rule.time_window_minutes,
                        'cooldown_minutes': rule.cooldown_minutes
                    }
                    for rule in self.alert_rules.values()
                ],
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            rules_file = self.storage_path / "alert_rules.json"
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False)
            
            # 保存統計數據
            history_data = {
                'stats': self.stats,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            history_file = self.storage_path / "alert_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            self.logger.error(f"❌ Error saving alert data: {e}")
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警規則"""
        self.alert_rules[rule.name] = rule
        self._save_data()
        self.logger.info(f"✅ Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, name: str) -> bool:
        """移除告警規則"""
        if name in self.alert_rules:
            del self.alert_rules[name]
            self._save_data()
            self.logger.info(f"✅ Removed alert rule: {name}")
            return True
        return False
    
    def enable_rule(self, name: str) -> bool:
        """啟用規則"""
        if name in self.alert_rules:
            self.alert_rules[name].enabled = True
            self._save_data()
            return True
        return False
    
    def disable_rule(self, name: str) -> bool:
        """禁用規則"""
        if name in self.alert_rules:
            self.alert_rules[name].enabled = False
            self._save_data()
            return True
        return False
    
    def add_alert_handler(self, handler: AlertHandler):
        """添加告警處理器"""
        self.alert_handlers.append(handler)
        self.logger.info(f"✅ Added alert handler: {type(handler).__name__}")
    
    async def start(self):
        """啟動告警系統"""
        if not self._running:
            self._running = True
            
            # 初始化默認規則和處理器
            self._initialize_default_rules()
            self._initialize_default_handlers()
            
            # 啟動監控任務
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("✅ Capability alert system started")
    
    async def stop(self):
        """停止告警系統"""
        if self._running:
            self._running = False
            
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            if self._cleanup_task:
                self._cleanup_task.cancel()
                try:
                    await self._cleanup_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("✅ Capability alert system stopped")
    
    def _initialize_default_rules(self):
        """初始化默認告警規則"""
        if not self.alert_rules:  # 只在沒有規則時初始化
            default_rules = [
                AlertRule(
                    name="high_latency",
                    description="Alert when model latency is too high",
                    alert_type=AlertType.LATENCY_SPIKE,
                    severity=AlertSeverity.HIGH,
                    metric_thresholds={'latency_ms': 5000},
                    time_window_minutes=10,
                    cooldown_minutes=15
                ),
                AlertRule(
                    name="high_error_rate",
                    description="Alert when error rate increases",
                    alert_type=AlertType.ERROR_RATE_INCREASE,
                    severity=AlertSeverity.CRITICAL,
                    metric_thresholds={'error_rate': 0.1},
                    time_window_minutes=5,
                    cooldown_minutes=10
                ),
                AlertRule(
                    name="accuracy_drop",
                    description="Alert when accuracy drops significantly",
                    alert_type=AlertType.ACCURACY_DROP,
                    severity=AlertSeverity.MEDIUM,
                    metric_thresholds={'accuracy_drop_percentage': 15},
                    time_window_minutes=20,
                    cooldown_minutes=30
                ),
                AlertRule(
                    name="performance_improvement",
                    description="Alert when performance improves significantly",
                    alert_type=AlertType.CAPABILITY_IMPROVEMENT,
                    severity=AlertSeverity.INFO,
                    metric_thresholds={'improvement_percentage': 20},
                    time_window_minutes=30,
                    cooldown_minutes=60
                )
            ]
            
            for rule in default_rules:
                self.add_alert_rule(rule)
    
    def _initialize_default_handlers(self):
        """初始化默認告警處理器"""
        if not self.alert_handlers:
            # 添加日誌處理器
            self.add_alert_handler(LogAlertHandler())
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self._running:
            try:
                await asyncio.sleep(30)  # 每30秒檢查一次
                await self._check_all_rules()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in monitoring loop: {e}")
    
    async def _cleanup_loop(self):
        """清理循環"""
        while self._running:
            try:
                await asyncio.sleep(3600)  # 每小時清理一次
                await self._cleanup_old_alerts()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in cleanup loop: {e}")
    
    async def _check_all_rules(self):
        """檢查所有告警規則"""
        try:
            # 獲取所有活躍模型
            models = await self.model_db.list_model_capabilities(is_available=True)
            
            for model in models:
                await self._check_model_rules(model.provider, model.model_id)
                
        except Exception as e:
            self.logger.error(f"❌ Error checking alert rules: {e}")
    
    async def _check_model_rules(self, provider: str, model_id: str):
        """檢查特定模型的告警規則"""
        try:
            # 獲取當前性能指標
            current_metrics = self.performance_monitor.get_current_metrics(provider, model_id)
            
            # 檢查每個規則
            for rule in self.alert_rules.values():
                if not rule.enabled or not rule.can_trigger():
                    continue
                
                # 應用過濾器
                if rule.provider_filter and rule.provider_filter != provider:
                    continue
                if rule.model_filter and rule.model_filter != model_id:
                    continue
                
                # 檢查規則條件
                alert = await self._evaluate_rule(rule, provider, model_id, current_metrics)
                if alert:
                    await self._handle_new_alert(alert)
                    rule.record_trigger()
                else:
                    rule.reset_consecutive_triggers()
                    
        except Exception as e:
            self.logger.error(f"❌ Error checking rules for {provider}/{model_id}: {e}")
    
    async def _evaluate_rule(
        self,
        rule: AlertRule,
        provider: str,
        model_id: str,
        current_metrics: Dict[str, Dict[str, float]]
    ) -> Optional[Alert]:
        """評估告警規則"""
        try:
            if rule.alert_type == AlertType.LATENCY_SPIKE:
                return self._check_latency_spike(rule, provider, model_id, current_metrics)
            
            elif rule.alert_type == AlertType.ERROR_RATE_INCREASE:
                return self._check_error_rate_increase(rule, provider, model_id, current_metrics)
            
            elif rule.alert_type == AlertType.ACCURACY_DROP:
                return self._check_accuracy_drop(rule, provider, model_id, current_metrics)
            
            elif rule.alert_type == AlertType.CAPABILITY_IMPROVEMENT:
                return self._check_capability_improvement(rule, provider, model_id, current_metrics)
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating rule {rule.name}: {e}")
            return None
    
    def _check_latency_spike(
        self,
        rule: AlertRule,
        provider: str,
        model_id: str,
        current_metrics: Dict[str, Dict[str, float]]
    ) -> Optional[Alert]:
        """檢查延遲尖峰"""
        latency_key = f"{provider}/{model_id}/latency"
        latency_stats = current_metrics.get(latency_key, {})
        
        if not latency_stats:
            return None
        
        current_latency = latency_stats.get('mean', 0)
        threshold = rule.metric_thresholds.get('latency_ms', 5000)
        
        if current_latency > threshold:
            alert_id = f"latency_spike_{provider}_{model_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            return Alert(
                id=alert_id,
                rule=rule,
                provider=provider,
                model_id=model_id,
                severity=rule.severity,
                alert_type=rule.alert_type,
                title=f"High Latency Alert: {provider}/{model_id}",
                message=f"Model latency ({current_latency:.0f}ms) exceeds threshold ({threshold}ms)",
                details={
                    'current_latency_ms': current_latency,
                    'threshold_ms': threshold,
                    'p95_latency': latency_stats.get('p95', 0),
                    'p99_latency': latency_stats.get('p99', 0),
                    'sample_count': latency_stats.get('count', 0)
                }
            )
        
        return None
    
    def _check_error_rate_increase(
        self,
        rule: AlertRule,
        provider: str,
        model_id: str,
        current_metrics: Dict[str, Dict[str, float]]
    ) -> Optional[Alert]:
        """檢查錯誤率上升"""
        error_rate_key = f"{provider}/{model_id}/error_rate"
        error_stats = current_metrics.get(error_rate_key, {})
        
        if not error_stats:
            return None
        
        current_error_rate = error_stats.get('mean', 0)
        threshold = rule.metric_thresholds.get('error_rate', 0.05)
        
        if current_error_rate > threshold:
            alert_id = f"error_rate_{provider}_{model_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            return Alert(
                id=alert_id,
                rule=rule,
                provider=provider,
                model_id=model_id,
                severity=rule.severity,
                alert_type=rule.alert_type,
                title=f"High Error Rate Alert: {provider}/{model_id}",
                message=f"Model error rate ({current_error_rate:.1%}) exceeds threshold ({threshold:.1%})",
                details={
                    'current_error_rate': current_error_rate,
                    'threshold': threshold,
                    'sample_count': error_stats.get('count', 0)
                }
            )
        
        return None
    
    def _check_accuracy_drop(
        self,
        rule: AlertRule,
        provider: str,
        model_id: str,
        current_metrics: Dict[str, Dict[str, float]]
    ) -> Optional[Alert]:
        """檢查準確性下降"""
        accuracy_key = f"{provider}/{model_id}/accuracy"
        accuracy_stats = current_metrics.get(accuracy_key, {})
        
        if not accuracy_stats:
            return None
        
        current_accuracy = accuracy_stats.get('mean', 0)
        
        # 這裡應該與歷史基線比較，簡化實現
        baseline_accuracy = 0.9  # 假設基線
        threshold_drop = rule.metric_thresholds.get('accuracy_drop_percentage', 10) / 100
        
        if current_accuracy < baseline_accuracy * (1 - threshold_drop):
            alert_id = f"accuracy_drop_{provider}_{model_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            accuracy_drop = (baseline_accuracy - current_accuracy) / baseline_accuracy
            
            return Alert(
                id=alert_id,
                rule=rule,
                provider=provider,
                model_id=model_id,
                severity=rule.severity,
                alert_type=rule.alert_type,
                title=f"Accuracy Drop Alert: {provider}/{model_id}",
                message=f"Model accuracy dropped by {accuracy_drop:.1%} from baseline",
                details={
                    'current_accuracy': current_accuracy,
                    'baseline_accuracy': baseline_accuracy,
                    'drop_percentage': accuracy_drop * 100,
                    'threshold_percentage': threshold_drop * 100
                }
            )
        
        return None
    
    def _check_capability_improvement(
        self,
        rule: AlertRule,
        provider: str,
        model_id: str,
        current_metrics: Dict[str, Dict[str, float]]
    ) -> Optional[Alert]:
        """檢查能力改善"""
        # 簡化實現，檢查整體性能改善
        improvement_detected = False
        improvement_details = {}
        
        # 檢查各項指標的改善
        for metric_key, stats in current_metrics.items():
            if not stats or provider not in metric_key or model_id not in metric_key:
                continue
            
            current_value = stats.get('mean', 0)
            # 這裡應該與歷史數據比較，簡化實現
            baseline_value = current_value * 0.8  # 假設基線
            
            if metric_key.endswith('/accuracy') or metric_key.endswith('/success_rate'):
                # 越高越好的指標
                if current_value > baseline_value * 1.2:  # 20%改善
                    improvement_detected = True
                    improvement_details[metric_key] = {
                        'current': current_value,
                        'baseline': baseline_value,
                        'improvement': (current_value - baseline_value) / baseline_value
                    }
        
        if improvement_detected:
            alert_id = f"improvement_{provider}_{model_id}_{int(datetime.now(timezone.utc).timestamp())}"
            
            return Alert(
                id=alert_id,
                rule=rule,
                provider=provider,
                model_id=model_id,
                severity=rule.severity,
                alert_type=rule.alert_type,
                title=f"Performance Improvement: {provider}/{model_id}",
                message="Significant performance improvement detected",
                details=improvement_details
            )
        
        return None
    
    async def _handle_new_alert(self, alert: Alert):
        """處理新告警"""
        try:
            # 檢查是否為重複告警
            duplicate_key = f"{alert.provider}_{alert.model_id}_{alert.alert_type.value}"
            
            # 檢查活躍告警中是否有類似的
            for active_alert in self.active_alerts.values():
                active_key = f"{active_alert.provider}_{active_alert.model_id}_{active_alert.alert_type.value}"
                if active_key == duplicate_key:
                    # 更新現有告警而不是創建新的
                    active_alert.details.update(alert.details)
                    return
            
            # 添加到活躍告警
            self.active_alerts[alert.id] = alert
            
            # 添加到歷史記錄
            self.alert_history.append(alert)
            
            # 更新統計
            self._update_stats(alert)
            
            # 發送告警
            for handler in self.alert_handlers:
                try:
                    await handler.handle_alert(alert)
                except Exception as e:
                    self.logger.error(f"❌ Error in alert handler: {e}")
            
            # 檢查是否需要升級
            if alert.rule.consecutive_triggers >= alert.rule.escalation_threshold:
                alert.escalate()
                self.logger.warning(f"🔺 Alert escalated: {alert.title}")
            
            self.logger.info(f"🚨 New alert: {alert.title} [{alert.severity.value.upper()}]")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling new alert: {e}")
    
    def _update_stats(self, alert: Alert):
        """更新統計數據"""
        self.stats['total_alerts'] += 1
        
        severity_key = alert.severity.value
        self.stats['alerts_by_severity'][severity_key] = \
            self.stats['alerts_by_severity'].get(severity_key, 0) + 1
        
        type_key = alert.alert_type.value
        self.stats['alerts_by_type'][type_key] = \
            self.stats['alerts_by_type'].get(type_key, 0) + 1
        
        model_key = f"{alert.provider}/{alert.model_id}"
        self.stats['alerts_by_model'][model_key] = \
            self.stats['alerts_by_model'].get(model_key, 0) + 1
    
    async def _cleanup_old_alerts(self):
        """清理舊告警"""
        try:
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(hours=24)
            
            # 清理已解決的舊告警
            alerts_to_remove = []
            for alert_id, alert in self.active_alerts.items():
                if alert.resolved and alert.resolved_at and alert.resolved_at < cutoff_time:
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.active_alerts[alert_id]
            
            # 限制歷史記錄數量
            if len(self.alert_history) > 1000:
                self.alert_history = self.alert_history[-1000:]
            
            if alerts_to_remove:
                self.logger.info(f"✅ Cleaned up {len(alerts_to_remove)} old alerts")
                self._save_data()
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up alerts: {e}")
    
    async def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """確認告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledge(user)
            self.logger.info(f"✅ Alert acknowledged: {alert_id} by {user}")
            return True
        return False
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """解決告警"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolve()
            self.logger.info(f"✅ Alert resolved: {alert_id}")
            return True
        return False
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None,
        alert_type: Optional[AlertType] = None,
        provider: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[Alert]:
        """獲取活躍告警"""
        alerts = list(self.active_alerts.values())
        
        # 應用過濾器
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if provider:
            alerts = [a for a in alerts if a.provider == provider]
        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]
        
        # 按創建時間排序（最新的在前）
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        
        return alerts
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """獲取告警統計"""
        active_count = len(self.active_alerts)
        acknowledged_count = sum(1 for a in self.active_alerts.values() if a.acknowledged)
        resolved_count = sum(1 for a in self.active_alerts.values() if a.resolved)
        
        return {
            'total_alerts': self.stats['total_alerts'],
            'active_alerts': active_count,
            'acknowledged_alerts': acknowledged_count,
            'resolved_alerts': resolved_count,
            'alerts_by_severity': self.stats['alerts_by_severity'],
            'alerts_by_type': self.stats['alerts_by_type'],
            'alerts_by_model': self.stats['alerts_by_model'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }