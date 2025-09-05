#!/usr/bin/env python3
"""
Capability Alert System
能力變化告警系統 - GPT-OSS整合任務1.2.3
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

from ..database.model_capability_db import ModelCapabilityDB
from ..monitoring.performance_monitor import PerformanceMonitor
from .model_version_control import ModelVersionControl

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """告警嚴重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(Enum):
    """告警類型"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CAPABILITY_DECLINE = "capability_decline"
    AVAILABILITY_CHANGE = "availability_change"
    COST_INCREASE = "cost_increase"
    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_HIGH = "error_rate_high"
    BENCHMARK_FAILURE = "benchmark_failure"
    VERSION_ROLLBACK = "version_rollback"
    CONFIGURATION_CHANGE = "configuration_change"
    THRESHOLD_EXCEEDED = "threshold_exceeded"

class AlertStatus(Enum):
    """告警狀態"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class AlertCondition:
    """告警條件"""
    condition_id: str
    alert_type: AlertType
    severity: AlertSeverity
    conditions: Dict[str, Any]
    enabled: bool = True
    cooldown_minutes: int = 30
    auto_resolve_minutes: Optional[int] = None
    
    # 過濾條件
    provider_filter: Optional[Set[str]] = None
    model_filter: Optional[Set[str]] = None
    
    # 條件邏輯
    require_consecutive_triggers: int = 1
    evaluation_window_minutes: int = 5

@dataclass
class Alert:
    """告警實例"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    provider: str
    model_id: str
    title: str
    message: str
    details: Dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # 關聯信息
    condition_id: str = ""
    version_id: Optional[str] = None
    related_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # 處理信息
    actions_taken: List[str] = field(default_factory=list)
    escalation_level: int = 0

class AlertChannel(ABC):
    """告警通道基類"""
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """發送告警"""
        pass
    
    @abstractmethod
    async def send_alert_update(self, alert: Alert, update_type: str) -> bool:
        """發送告警更新"""
        pass

class LogAlertChannel(AlertChannel):
    """日誌告警通道"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    async def send_alert(self, alert: Alert) -> bool:
        try:
            log_message = f"🚨 ALERT [{alert.severity.value.upper()}] {alert.title} - {alert.provider}/{alert.model_id}: {alert.message}"
            
            if alert.severity == AlertSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif alert.severity == AlertSeverity.HIGH:
                self.logger.error(log_message)
            elif alert.severity == AlertSeverity.MEDIUM:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to send log alert: {e}")
            return False
    
    async def send_alert_update(self, alert: Alert, update_type: str) -> bool:
        try:
            log_message = f"📢 ALERT UPDATE [{alert.severity.value.upper()}] {update_type}: {alert.title} - {alert.provider}/{alert.model_id}"
            self.logger.info(log_message)
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to send alert update: {e}")
            return False

class WebhookAlertChannel(AlertChannel):
    """Webhook告警通道"""
    
    def __init__(self, webhook_url: str, headers: Optional[Dict[str, str]] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def send_alert(self, alert: Alert) -> bool:
        try:
            import aiohttp
            
            payload = {
                'alert_id': alert.alert_id,
                'type': alert.alert_type.value,
                'severity': alert.severity.value,
                'provider': alert.provider,
                'model_id': alert.model_id,
                'title': alert.title,
                'message': alert.message,
                'details': alert.details,
                'created_at': alert.created_at.isoformat(),
                'status': alert.status.value
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                ) as response:
                    return response.status < 400
                    
        except Exception as e:
            logger.error(f"❌ Failed to send webhook alert: {e}")
            return False
    
    async def send_alert_update(self, alert: Alert, update_type: str) -> bool:
        try:
            import aiohttp
            
            payload = {
                'alert_id': alert.alert_id,
                'update_type': update_type,
                'status': alert.status.value,
                'updated_at': alert.updated_at.isoformat(),
                'acknowledged_by': alert.acknowledged_by,
                'acknowledged_at': alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10
                ) as response:
                    return response.status < 400
                    
        except Exception as e:
            logger.error(f"❌ Failed to send webhook alert update: {e}")
            return False

class EmailAlertChannel(AlertChannel):
    """郵件告警通道"""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        from_email: str,
        to_emails: List[str]
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def send_alert(self, alert: Alert) -> bool:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            subject = f"[{alert.severity.value.upper()}] Model Alert: {alert.title}"
            
            # 創建郵件內容
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = subject
            
            # 郵件正文
            body = f"""
Alert Details:
- Type: {alert.alert_type.value}
- Severity: {alert.severity.value}
- Model: {alert.provider}/{alert.model_id}
- Message: {alert.message}
- Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Details:
{json.dumps(alert.details, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 發送郵件
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_emails, text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
            return False
    
    async def send_alert_update(self, alert: Alert, update_type: str) -> bool:
        # 簡化實現，只記錄日誌
        logger.info(f"📧 Email alert update: {alert.alert_id} - {update_type}")
        return True

class CapabilityAlertSystem:
    """
    能力變化告警系統
    
    功能：
    1. 實時監控模型能力變化
    2. 多種告警條件和規則
    3. 多通道告警發送
    4. 告警生命周期管理
    5. 告警聚合和抑制
    6. 自動解決和升級
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        version_control: Optional[ModelVersionControl] = None
    ):
        """初始化告警系統"""
        self.model_db = model_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.version_control = version_control or ModelVersionControl()
        
        self.logger = logger
        
        # 告警配置
        self.alert_conditions: Dict[str, AlertCondition] = {}
        self.alert_channels: List[AlertChannel] = []
        self.active_alerts: Dict[str, Alert] = {}
        
        # 告警歷史（內存中，實際應存儲在數據庫）
        self.alert_history: List[Alert] = []
        
        # 運行時狀態
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 統計信息
        self.alert_stats = {
            'total_alerts': 0,
            'active_alerts': 0,
            'resolved_alerts': 0,
            'suppressed_alerts': 0,
            'false_positives': 0
        }
        
        # 初始化默認告警條件
        self._initialize_default_conditions()
        
        # 添加默認日誌通道
        self.add_alert_channel(LogAlertChannel(logger))
    
    def _initialize_default_conditions(self):
        """初始化默認告警條件"""
        # 性能下降告警
        self.add_alert_condition(AlertCondition(
            condition_id="performance_degradation",
            alert_type=AlertType.PERFORMANCE_DEGRADATION,
            severity=AlertSeverity.HIGH,
            conditions={
                'capability_score_drop_threshold': 0.15,
                'min_baseline_score': 0.5,
                'evaluation_period_minutes': 10
            },
            cooldown_minutes=60,
            require_consecutive_triggers=2
        ))
        
        # 可用性變化告警
        self.add_alert_condition(AlertCondition(
            condition_id="availability_change",
            alert_type=AlertType.AVAILABILITY_CHANGE,
            severity=AlertSeverity.CRITICAL,
            conditions={
                'availability_change': True
            },
            cooldown_minutes=5,
            require_consecutive_triggers=1
        ))
        
        # 延遲飆升告警
        self.add_alert_condition(AlertCondition(
            condition_id="latency_spike",
            alert_type=AlertType.LATENCY_SPIKE,
            severity=AlertSeverity.MEDIUM,
            conditions={
                'latency_increase_threshold': 3000,  # 增加3秒
                'baseline_multiplier': 2.0,  # 超過基準2倍
                'min_samples': 5
            },
            cooldown_minutes=30,
            require_consecutive_triggers=3
        ))
        
        # 錯誤率過高告警
        self.add_alert_condition(AlertCondition(
            condition_id="high_error_rate",
            alert_type=AlertType.ERROR_RATE_HIGH,
            severity=AlertSeverity.HIGH,
            conditions={
                'error_rate_threshold': 0.2,  # 20%
                'min_requests': 10,
                'evaluation_window_minutes': 15
            },
            cooldown_minutes=45,
            auto_resolve_minutes=30
        ))
        
        # 成本增加告警
        self.add_alert_condition(AlertCondition(
            condition_id="cost_increase",
            alert_type=AlertType.COST_INCREASE,
            severity=AlertSeverity.MEDIUM,
            conditions={
                'cost_increase_percentage': 50,  # 成本增加50%
                'min_baseline_cost': 0.001
            },
            cooldown_minutes=120
        ))
    
    def add_alert_condition(self, condition: AlertCondition):
        """添加告警條件"""
        self.alert_conditions[condition.condition_id] = condition
        self.logger.info(f"✅ Added alert condition: {condition.condition_id}")
    
    def remove_alert_condition(self, condition_id: str) -> bool:
        """移除告警條件"""
        if condition_id in self.alert_conditions:
            del self.alert_conditions[condition_id]
            self.logger.info(f"✅ Removed alert condition: {condition_id}")
            return True
        return False
    
    def add_alert_channel(self, channel: AlertChannel):
        """添加告警通道"""
        self.alert_channels.append(channel)
        self.logger.info(f"✅ Added alert channel: {channel.__class__.__name__}")
    
    def enable_condition(self, condition_id: str, enabled: bool = True):
        """啟用/禁用告警條件"""
        if condition_id in self.alert_conditions:
            self.alert_conditions[condition_id].enabled = enabled
            status = "enabled" if enabled else "disabled"
            self.logger.info(f"✅ Alert condition {condition_id} {status}")
    
    async def start(self):
        """啟動告警系統"""
        if not self._running:
            self._running = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            
            # 註冊性能監控回調
            if hasattr(self.performance_monitor, 'add_alert_callback'):
                self.performance_monitor.add_alert_callback(self._handle_performance_alert)
            
            self.logger.info("✅ Capability alert system started")
    
    async def stop(self):
        """停止告警系統"""
        if self._running:
            self._running = False
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            # 移除性能監控回調
            if hasattr(self.performance_monitor, 'remove_alert_callback'):
                self.performance_monitor.remove_alert_callback(self._handle_performance_alert)
            
            self.logger.info("✅ Capability alert system stopped")
    
    async def _monitoring_loop(self):
        """監控主循環"""
        while self._running:
            try:
                await self._evaluate_all_conditions()
                await self._check_auto_resolve()
                await self._cleanup_old_alerts()
                
                await asyncio.sleep(30)  # 30秒檢查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in alert monitoring loop: {e}")
                await asyncio.sleep(5)
    
    async def _evaluate_all_conditions(self):
        """評估所有告警條件"""
        for condition in self.alert_conditions.values():
            if condition.enabled:
                try:
                    await self._evaluate_condition(condition)
                except Exception as e:
                    self.logger.error(f"❌ Error evaluating condition {condition.condition_id}: {e}")
    
    async def _evaluate_condition(self, condition: AlertCondition):
        """評估單個告警條件"""
        # 獲取所有符合過濾條件的模型
        models = await self.model_db.list_model_capabilities(
            provider=list(condition.provider_filter)[0] if condition.provider_filter and len(condition.provider_filter) == 1 else None,
            is_available=True
        )
        
        for model in models:
            # 應用過濾條件
            if condition.provider_filter and model.provider not in condition.provider_filter:
                continue
            if condition.model_filter and model.model_id not in condition.model_filter:
                continue
            
            # 檢查冷卻期
            if await self._is_in_cooldown(condition.condition_id, model.provider, model.model_id):
                continue
            
            # 評估具體條件
            alert_triggered = False
            alert_details = {}
            
            if condition.alert_type == AlertType.PERFORMANCE_DEGRADATION:
                alert_triggered, alert_details = await self._check_performance_degradation(
                    model, condition.conditions
                )
            
            elif condition.alert_type == AlertType.AVAILABILITY_CHANGE:
                alert_triggered, alert_details = await self._check_availability_change(
                    model, condition.conditions
                )
            
            elif condition.alert_type == AlertType.LATENCY_SPIKE:
                alert_triggered, alert_details = await self._check_latency_spike(
                    model, condition.conditions
                )
            
            elif condition.alert_type == AlertType.ERROR_RATE_HIGH:
                alert_triggered, alert_details = await self._check_high_error_rate(
                    model, condition.conditions
                )
            
            elif condition.alert_type == AlertType.COST_INCREASE:
                alert_triggered, alert_details = await self._check_cost_increase(
                    model, condition.conditions
                )
            
            # 如果觸發條件，創建告警
            if alert_triggered:
                await self._create_alert(condition, model, alert_details)
    
    async def _check_performance_degradation(self, model, conditions) -> tuple[bool, Dict[str, Any]]:
        """檢查性能下降"""
        try:
            current_score = model.capability_score or 0.0
            drop_threshold = conditions.get('capability_score_drop_threshold', 0.15)
            min_baseline = conditions.get('min_baseline_score', 0.5)
            
            # 獲取歷史基準（簡化實現，使用固定基準）
            baseline_score = 0.8  # 在實際實現中應從歷史數據計算
            
            if baseline_score >= min_baseline:
                score_drop = baseline_score - current_score
                
                if score_drop >= drop_threshold:
                    return True, {
                        'current_score': current_score,
                        'baseline_score': baseline_score,
                        'score_drop': score_drop,
                        'drop_percentage': (score_drop / baseline_score) * 100
                    }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"❌ Error checking performance degradation: {e}")
            return False, {}
    
    async def _check_availability_change(self, model, conditions) -> tuple[bool, Dict[str, Any]]:
        """檢查可用性變化"""
        try:
            # 檢查模型可用性是否發生變化
            # 這裡需要比較當前狀態與歷史狀態
            current_availability = model.is_available
            
            # 簡化實現：檢查最近的版本變化
            version_history = await self.version_control.get_version_history(
                model.provider, model.model_id, limit=2
            )
            
            if len(version_history) >= 2:
                latest_version = version_history[0]
                previous_version = version_history[1]
                
                latest_available = latest_version['capability_snapshot'].get('is_available', True)
                previous_available = previous_version['capability_snapshot'].get('is_available', True)
                
                if latest_available != previous_available:
                    return True, {
                        'current_availability': latest_available,
                        'previous_availability': previous_available,
                        'change_type': 'disabled' if not latest_available else 'enabled',
                        'change_time': latest_version['created_at']
                    }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"❌ Error checking availability change: {e}")
            return False, {}
    
    async def _check_latency_spike(self, model, conditions) -> tuple[bool, Dict[str, Any]]:
        """檢查延遲飆升"""
        try:
            # 獲取當前延遲指標
            current_metrics = self.performance_monitor.get_current_metrics(
                model.provider, model.model_id
            )
            
            latency_key = f"{model.provider}/{model.model_id}/latency"
            latency_stats = current_metrics.get(latency_key, {})
            
            if not latency_stats:
                return False, {}
            
            current_latency = latency_stats.get('mean', 0)
            baseline_latency = model.avg_latency_ms or 1000
            sample_count = latency_stats.get('count', 0)
            
            increase_threshold = conditions.get('latency_increase_threshold', 3000)
            baseline_multiplier = conditions.get('baseline_multiplier', 2.0)
            min_samples = conditions.get('min_samples', 5)
            
            if sample_count >= min_samples:
                latency_increase = current_latency - baseline_latency
                
                if (latency_increase >= increase_threshold or 
                    current_latency >= baseline_latency * baseline_multiplier):
                    
                    return True, {
                        'current_latency': current_latency,
                        'baseline_latency': baseline_latency,
                        'latency_increase': latency_increase,
                        'increase_percentage': (latency_increase / baseline_latency) * 100,
                        'sample_count': sample_count
                    }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"❌ Error checking latency spike: {e}")
            return False, {}
    
    async def _check_high_error_rate(self, model, conditions) -> tuple[bool, Dict[str, Any]]:
        """檢查高錯誤率"""
        try:
            # 獲取錯誤率指標
            current_metrics = self.performance_monitor.get_current_metrics(
                model.provider, model.model_id
            )
            
            error_key = f"{model.provider}/{model.model_id}/error_rate"
            error_stats = current_metrics.get(error_key, {})
            
            if not error_stats:
                return False, {}
            
            error_rate = error_stats.get('mean', 0)
            sample_count = error_stats.get('count', 0)
            
            error_threshold = conditions.get('error_rate_threshold', 0.2)
            min_requests = conditions.get('min_requests', 10)
            
            if sample_count >= min_requests and error_rate >= error_threshold:
                return True, {
                    'error_rate': error_rate,
                    'error_percentage': error_rate * 100,
                    'threshold': error_threshold * 100,
                    'sample_count': sample_count
                }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"❌ Error checking error rate: {e}")
            return False, {}
    
    async def _check_cost_increase(self, model, conditions) -> tuple[bool, Dict[str, Any]]:
        """檢查成本增加"""
        try:
            current_cost = model.cost_per_1k_input_tokens or 0.0
            min_baseline = conditions.get('min_baseline_cost', 0.001)
            increase_percentage = conditions.get('cost_increase_percentage', 50)
            
            # 獲取基準成本（簡化實現）
            baseline_cost = 0.01  # 在實際實現中應從歷史數據獲取
            
            if baseline_cost >= min_baseline:
                cost_increase = ((current_cost - baseline_cost) / baseline_cost) * 100
                
                if cost_increase >= increase_percentage:
                    return True, {
                        'current_cost': current_cost,
                        'baseline_cost': baseline_cost,
                        'cost_increase_percentage': cost_increase,
                        'threshold_percentage': increase_percentage
                    }
            
            return False, {}
            
        except Exception as e:
            self.logger.error(f"❌ Error checking cost increase: {e}")
            return False, {}
    
    async def _create_alert(
        self,
        condition: AlertCondition,
        model,
        alert_details: Dict[str, Any]
    ):
        """創建告警"""
        try:
            alert_id = f"{condition.condition_id}_{model.provider}_{model.model_id}_{int(time.time())}"
            
            # 生成告警標題和消息
            title, message = self._generate_alert_content(condition.alert_type, model, alert_details)
            
            alert = Alert(
                alert_id=alert_id,
                alert_type=condition.alert_type,
                severity=condition.severity,
                provider=model.provider,
                model_id=model.model_id,
                title=title,
                message=message,
                details=alert_details,
                condition_id=condition.condition_id,
                related_metrics=await self._get_related_metrics(model.provider, model.model_id)
            )
            
            # 添加到活躍告警
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # 更新統計
            self.alert_stats['total_alerts'] += 1
            self.alert_stats['active_alerts'] += 1
            
            # 發送告警到所有通道
            await self._send_alert_to_channels(alert)
            
            self.logger.warning(f"🚨 Alert created: {alert_id} - {title}")
            
        except Exception as e:
            self.logger.error(f"❌ Error creating alert: {e}")
    
    def _generate_alert_content(
        self,
        alert_type: AlertType,
        model,
        details: Dict[str, Any]
    ) -> tuple[str, str]:
        """生成告警標題和消息"""
        provider_model = f"{model.provider}/{model.model_id}"
        
        if alert_type == AlertType.PERFORMANCE_DEGRADATION:
            title = f"Performance Degradation - {provider_model}"
            current_score = details.get('current_score', 0)
            baseline_score = details.get('baseline_score', 0)
            drop_pct = details.get('drop_percentage', 0)
            message = f"Capability score dropped from {baseline_score:.3f} to {current_score:.3f} ({drop_pct:.1f}% decrease)"
            
        elif alert_type == AlertType.AVAILABILITY_CHANGE:
            title = f"Availability Change - {provider_model}"
            change_type = details.get('change_type', 'unknown')
            message = f"Model availability changed to {change_type}"
            
        elif alert_type == AlertType.LATENCY_SPIKE:
            title = f"Latency Spike - {provider_model}"
            current_latency = details.get('current_latency', 0)
            baseline_latency = details.get('baseline_latency', 0)
            increase_pct = details.get('increase_percentage', 0)
            message = f"Latency increased from {baseline_latency:.0f}ms to {current_latency:.0f}ms ({increase_pct:.1f}% increase)"
            
        elif alert_type == AlertType.ERROR_RATE_HIGH:
            title = f"High Error Rate - {provider_model}"
            error_pct = details.get('error_percentage', 0)
            message = f"Error rate is {error_pct:.1f}%"
            
        elif alert_type == AlertType.COST_INCREASE:
            title = f"Cost Increase - {provider_model}"
            increase_pct = details.get('cost_increase_percentage', 0)
            current_cost = details.get('current_cost', 0)
            message = f"Cost per 1K tokens increased by {increase_pct:.1f}% to ${current_cost:.4f}"
            
        else:
            title = f"{alert_type.value.replace('_', ' ').title()} - {provider_model}"
            message = f"Alert condition triggered for {provider_model}"
        
        return title, message
    
    async def _get_related_metrics(self, provider: str, model_id: str) -> Dict[str, Any]:
        """獲取相關指標"""
        try:
            return self.performance_monitor.get_current_metrics(provider, model_id)
        except Exception as e:
            self.logger.error(f"❌ Error getting related metrics: {e}")
            return {}
    
    async def _send_alert_to_channels(self, alert: Alert):
        """發送告警到所有通道"""
        send_tasks = []
        
        for channel in self.alert_channels:
            task = asyncio.create_task(channel.send_alert(alert))
            send_tasks.append(task)
        
        if send_tasks:
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            self.logger.info(f"📢 Alert {alert.alert_id} sent to {success_count}/{len(self.alert_channels)} channels")
    
    async def _is_in_cooldown(self, condition_id: str, provider: str, model_id: str) -> bool:
        """檢查是否在冷卻期內"""
        condition = self.alert_conditions.get(condition_id)
        if not condition:
            return False
        
        cooldown_minutes = condition.cooldown_minutes
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
        
        # 檢查是否有相同條件的近期告警
        for alert in self.alert_history:
            if (alert.condition_id == condition_id and
                alert.provider == provider and
                alert.model_id == model_id and
                alert.created_at > cutoff_time):
                return True
        
        return False
    
    async def _check_auto_resolve(self):
        """檢查自動解決條件"""
        current_time = datetime.now(timezone.utc)
        
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.status != AlertStatus.ACTIVE:
                continue
            
            condition = self.alert_conditions.get(alert.condition_id)
            if not condition or not condition.auto_resolve_minutes:
                continue
            
            auto_resolve_time = alert.created_at + timedelta(minutes=condition.auto_resolve_minutes)
            
            if current_time >= auto_resolve_time:
                # 檢查告警條件是否仍然存在
                still_triggered = await self._check_alert_still_active(alert)
                
                if not still_triggered:
                    await self.resolve_alert(alert_id, "auto_resolved", "Condition no longer triggered")
    
    async def _check_alert_still_active(self, alert: Alert) -> bool:
        """檢查告警條件是否仍然活躍"""
        try:
            # 獲取模型當前狀態
            model = await self.model_db.get_model_capability(alert.provider, alert.model_id)
            if not model:
                return False
            
            condition = self.alert_conditions.get(alert.condition_id)
            if not condition:
                return False
            
            # 重新評估條件
            if condition.alert_type == AlertType.PERFORMANCE_DEGRADATION:
                triggered, _ = await self._check_performance_degradation(model, condition.conditions)
            elif condition.alert_type == AlertType.LATENCY_SPIKE:
                triggered, _ = await self._check_latency_spike(model, condition.conditions)
            elif condition.alert_type == AlertType.ERROR_RATE_HIGH:
                triggered, _ = await self._check_high_error_rate(model, condition.conditions)
            else:
                # 對於其他類型，默認為仍然活躍
                triggered = True
            
            return triggered
            
        except Exception as e:
            self.logger.error(f"❌ Error checking if alert still active: {e}")
            return True  # 出錯時保持告警狀態
    
    async def _cleanup_old_alerts(self):
        """清理舊告警"""
        try:
            # 清理7天前的已解決告警
            cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
            
            self.alert_history = [
                alert for alert in self.alert_history
                if not (alert.status == AlertStatus.RESOLVED and alert.resolved_at and alert.resolved_at < cutoff_time)
            ]
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old alerts: {e}")
    
    def _handle_performance_alert(self, message: str, alert_data: Dict[str, Any]):
        """處理來自性能監控的告警"""
        try:
            # 將性能監控告警轉換為系統告警
            provider = alert_data.get('provider', 'unknown')
            model_id = alert_data.get('model_id', 'unknown')
            metric_type = alert_data.get('metric_type', 'unknown')
            severity_str = alert_data.get('severity', 'medium')
            
            # 映射嚴重程度
            severity_mapping = {
                'critical': AlertSeverity.CRITICAL,
                'high': AlertSeverity.HIGH,
                'medium': AlertSeverity.MEDIUM,
                'low': AlertSeverity.LOW
            }
            severity = severity_mapping.get(severity_str, AlertSeverity.MEDIUM)
            
            # 映射告警類型
            alert_type_mapping = {
                'latency': AlertType.LATENCY_SPIKE,
                'error_rate': AlertType.ERROR_RATE_HIGH,
                'accuracy': AlertType.PERFORMANCE_DEGRADATION,
                'success_rate': AlertType.PERFORMANCE_DEGRADATION
            }
            alert_type = alert_type_mapping.get(metric_type, AlertType.THRESHOLD_EXCEEDED)
            
            # 創建告警任務
            asyncio.create_task(self._create_performance_alert(
                alert_type=alert_type,
                severity=severity,
                provider=provider,
                model_id=model_id,
                message=message,
                details=alert_data
            ))
            
        except Exception as e:
            self.logger.error(f"❌ Error handling performance alert: {e}")
    
    async def _create_performance_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        provider: str,
        model_id: str,
        message: str,
        details: Dict[str, Any]
    ):
        """創建性能告警"""
        try:
            alert_id = f"perf_{alert_type.value}_{provider}_{model_id}_{int(time.time())}"
            
            alert = Alert(
                alert_id=alert_id,
                alert_type=alert_type,
                severity=severity,
                provider=provider,
                model_id=model_id,
                title=f"Performance Alert - {provider}/{model_id}",
                message=message,
                details=details,
                condition_id="performance_monitor",
                related_metrics=details
            )
            
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            self.alert_stats['total_alerts'] += 1
            self.alert_stats['active_alerts'] += 1
            
            await self._send_alert_to_channels(alert)
            
        except Exception as e:
            self.logger.error(f"❌ Error creating performance alert: {e}")
    
    # ==================== 公共接口 ====================
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """確認告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now(timezone.utc)
            alert.updated_at = datetime.now(timezone.utc)
            
            # 發送更新通知
            await self._send_alert_update_to_channels(alert, "acknowledged")
            
            self.logger.info(f"✅ Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        
        return False
    
    async def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str = "system",
        resolution_note: str = ""
    ) -> bool:
        """解決告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now(timezone.utc)
            alert.updated_at = datetime.now(timezone.utc)
            
            if resolution_note:
                alert.actions_taken.append(f"Resolved: {resolution_note}")
            
            # 從活躍告警中移除
            del self.active_alerts[alert_id]
            
            # 更新統計
            self.alert_stats['active_alerts'] -= 1
            self.alert_stats['resolved_alerts'] += 1
            
            # 發送更新通知
            await self._send_alert_update_to_channels(alert, "resolved")
            
            self.logger.info(f"✅ Alert {alert_id} resolved by {resolved_by}")
            return True
        
        return False
    
    async def suppress_alert(self, alert_id: str, suppression_reason: str) -> bool:
        """抑制告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.SUPPRESSED
            alert.updated_at = datetime.now(timezone.utc)
            alert.actions_taken.append(f"Suppressed: {suppression_reason}")
            
            # 更新統計
            self.alert_stats['suppressed_alerts'] += 1
            
            # 發送更新通知
            await self._send_alert_update_to_channels(alert, "suppressed")
            
            self.logger.info(f"✅ Alert {alert_id} suppressed: {suppression_reason}")
            return True
        
        return False
    
    async def _send_alert_update_to_channels(self, alert: Alert, update_type: str):
        """發送告警更新到所有通道"""
        update_tasks = []
        
        for channel in self.alert_channels:
            task = asyncio.create_task(channel.send_alert_update(alert, update_type))
            update_tasks.append(task)
        
        if update_tasks:
            await asyncio.gather(*update_tasks, return_exceptions=True)
    
    def get_active_alerts(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """獲取活躍告警"""
        alerts = []
        
        for alert in self.active_alerts.values():
            # 應用過濾條件
            if provider and alert.provider != provider:
                continue
            if model_id and alert.model_id != model_id:
                continue
            if severity and alert.severity != severity:
                continue
            
            alerts.append({
                'alert_id': alert.alert_id,
                'type': alert.alert_type.value,
                'severity': alert.severity.value,
                'provider': alert.provider,
                'model_id': alert.model_id,
                'title': alert.title,
                'message': alert.message,
                'created_at': alert.created_at.isoformat(),
                'updated_at': alert.updated_at.isoformat(),
                'status': alert.status.value,
                'acknowledged_by': alert.acknowledged_by,
                'details': alert.details
            })
        
        # 按嚴重程度和創建時間排序
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }
        
        alerts.sort(key=lambda x: (
            severity_order.get(AlertSeverity(x['severity']), 5),
            x['created_at']
        ))
        
        return alerts
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """獲取告警統計"""
        return {
            **self.alert_stats.copy(),
            'condition_count': len(self.alert_conditions),
            'enabled_conditions': len([c for c in self.alert_conditions.values() if c.enabled]),
            'channel_count': len(self.alert_channels),
            'running': self._running
        }
    
    def get_alert_conditions(self) -> Dict[str, Dict[str, Any]]:
        """獲取告警條件配置"""
        return {
            condition_id: {
                'alert_type': condition.alert_type.value,
                'severity': condition.severity.value,
                'enabled': condition.enabled,
                'cooldown_minutes': condition.cooldown_minutes,
                'auto_resolve_minutes': condition.auto_resolve_minutes,
                'conditions': condition.conditions
            }
            for condition_id, condition in self.alert_conditions.items()
        }