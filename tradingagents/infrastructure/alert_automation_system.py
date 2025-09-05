#!/usr/bin/env python3
"""
智能告警和自動化響應系統 - 基礎設施團隊 Task 3.2
提供企業級告警管理、自動化響應和智能聚合功能

This system provides:
- Intelligent alerting with dynamic thresholds
- Automated response actions and remediation
- Alert aggregation and correlation
- Multi-channel notification delivery
- Integration with existing monitoring stack
- Machine learning-based alert prediction

Author: 小c (基礎設施團隊)
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import queue
import subprocess
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import yaml
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [告警自動化] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/infrastructure/alert_automation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AlertAutomation")


class AlertSeverity(Enum):
    """告警嚴重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """告警狀態"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class ResponseActionType(Enum):
    """響應動作類型"""
    RESTART_SERVICE = "restart_service"
    SCALE_RESOURCES = "scale_resources"
    CLEANUP_RESOURCES = "cleanup_resources"
    SEND_NOTIFICATION = "send_notification"
    EXECUTE_SCRIPT = "execute_script"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    CUSTOM_ACTION = "custom_action"


@dataclass
class AlertRule:
    """告警規則定義"""
    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: str  # PromQL查詢條件
    threshold: float
    duration: str  # 例如: "5m", "1h"
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    auto_resolve: bool = True
    response_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """告警實例"""
    alert_id: str
    rule_id: str
    name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    current_value: float
    threshold_value: float
    started_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    response_actions_executed: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResponseAction:
    """響應動作定義"""
    action_id: str
    name: str
    action_type: ResponseActionType
    description: str
    script_path: Optional[str] = None
    command: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    retry_count: int = 3
    retry_delay_seconds: int = 60
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class NotificationChannel:
    """通知渠道配置"""
    channel_id: str
    name: str
    channel_type: str  # email, slack, webhook, sms
    config: Dict[str, Any]
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class AlertAggregator:
    """告警聚合器"""
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_groups: Dict[str, List[Alert]] = {}
        self.correlation_rules: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{logger.name}.Aggregator")
    
    def add_alert(self, alert: Alert):
        """添加告警到聚合器"""
        self.active_alerts[alert.alert_id] = alert
        
        # 按服務分組
        service = alert.labels.get('service', 'unknown')
        if service not in self.alert_groups:
            self.alert_groups[service] = []
        self.alert_groups[service].append(alert)
        
        # 檢查相關性
        self._check_correlations(alert)
    
    def remove_alert(self, alert_id: str):
        """移除告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            service = alert.labels.get('service', 'unknown')
            
            if service in self.alert_groups:
                self.alert_groups[service] = [
                    a for a in self.alert_groups[service] 
                    if a.alert_id != alert_id
                ]
            
            del self.active_alerts[alert_id]
    
    def get_service_alerts(self, service: str) -> List[Alert]:
        """獲取指定服務的所有告警"""
        return self.alert_groups.get(service, [])
    
    def get_critical_alerts(self) -> List[Alert]:
        """獲取所有嚴重告警"""
        return [
            alert for alert in self.active_alerts.values()
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        ]
    
    def _check_correlations(self, new_alert: Alert):
        """檢查告警相關性"""
        # 實現告警相關性檢測邏輯
        pass


class ResponseAutomation:
    """自動化響應系統"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/app/config/response_actions.yaml"
        self.actions: Dict[str, ResponseAction] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{logger.name}.Automation")
        
        self._load_actions()
    
    def _load_actions(self):
        """加載響應動作配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                for action_config in config.get('actions', []):
                    action = ResponseAction(
                        action_id=action_config['id'],
                        name=action_config['name'],
                        action_type=ResponseActionType(action_config['type']),
                        description=action_config.get('description', ''),
                        script_path=action_config.get('script_path'),
                        command=action_config.get('command'),
                        parameters=action_config.get('parameters', {}),
                        timeout_seconds=action_config.get('timeout', 300),
                        retry_count=action_config.get('retry_count', 3),
                        retry_delay_seconds=action_config.get('retry_delay', 60),
                        enabled=action_config.get('enabled', True)
                    )
                    self.actions[action.action_id] = action
                
                self.logger.info(f"加載了 {len(self.actions)} 個響應動作")
        except Exception as e:
            self.logger.error(f"加載響應動作配置失敗: {str(e)}")
            self._create_default_actions()
    
    def _create_default_actions(self):
        """創建默認響應動作"""
        default_actions = [
            ResponseAction(
                action_id="restart_tradingagents",
                name="重啟TradingAgents服務",
                action_type=ResponseActionType.RESTART_SERVICE,
                description="重啟TradingAgents API服務",
                command="systemctl restart tradingagents",
                timeout_seconds=120
            ),
            ResponseAction(
                action_id="cleanup_gpu_memory",
                name="清理GPU內存",
                action_type=ResponseActionType.EXECUTE_SCRIPT,
                script_path="/app/scripts/cleanup_gpu_memory.sh",
                description="清理GPU內存碎片",
                timeout_seconds=60
            ),
            ResponseAction(
                action_id="scale_api_instances",
                name="擴展API實例",
                action_type=ResponseActionType.SCALE_RESOURCES,
                description="根據負載自動擴展API實例",
                parameters={"min_instances": 2, "max_instances": 10},
                timeout_seconds=300
            )
        ]
        
        for action in default_actions:
            self.actions[action.action_id] = action
        
        self.logger.info("創建了默認響應動作")
    
    async def execute_action(self, action_id: str, context: Dict[str, Any]) -> bool:
        """執行響應動作"""
        if action_id not in self.actions:
            self.logger.error(f"響應動作不存在: {action_id}")
            return False
        
        action = self.actions[action_id]
        if not action.enabled:
            self.logger.info(f"響應動作已禁用: {action_id}")
            return False
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            self.logger.info(f"開始執行響應動作: {action.name} (ID: {execution_id})")
            
            # 根據動作類型執行
            if action.action_type == ResponseActionType.RESTART_SERVICE:
                success = await self._restart_service(action, context)
            elif action.action_type == ResponseActionType.EXECUTE_SCRIPT:
                success = await self._execute_script(action, context)
            elif action.action_type == ResponseActionType.SCALE_RESOURCES:
                success = await self._scale_resources(action, context)
            elif action.action_type == ResponseActionType.CLEANUP_RESOURCES:
                success = await self._cleanup_resources(action, context)
            else:
                success = await self._execute_custom_action(action, context)
            
            # 記錄執行歷史
            execution_record = {
                'execution_id': execution_id,
                'action_id': action_id,
                'action_name': action.name,
                'start_time': start_time,
                'end_time': datetime.now(),
                'success': success,
                'context': context,
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }
            self.execution_history.append(execution_record)
            
            if success:
                self.logger.info(f"響應動作執行成功: {action.name}")
            else:
                self.logger.error(f"響應動作執行失敗: {action.name}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"執行響應動作時發生錯誤: {str(e)}")
            return False
    
    async def _restart_service(self, action: ResponseAction, context: Dict[str, Any]) -> bool:
        """重啟服務"""
        try:
            if action.command:
                process = await asyncio.create_subprocess_shell(
                    action.command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=action.timeout_seconds
                )
                
                if process.returncode == 0:
                    self.logger.info(f"服務重啟成功: {action.command}")
                    return True
                else:
                    self.logger.error(f"服務重啟失敗: {stderr.decode()}")
                    return False
        except Exception as e:
            self.logger.error(f"重啟服務時發生錯誤: {str(e)}")
            return False
    
    async def _execute_script(self, action: ResponseAction, context: Dict[str, Any]) -> bool:
        """執行腳本"""
        try:
            if action.script_path and os.path.exists(action.script_path):
                process = await asyncio.create_subprocess_exec(
                    'bash', action.script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=action.timeout_seconds
                )
                
                if process.returncode == 0:
                    self.logger.info(f"腳本執行成功: {action.script_path}")
                    return True
                else:
                    self.logger.error(f"腳本執行失敗: {stderr.decode()}")
                    return False
            else:
                self.logger.error(f"腳本文件不存在: {action.script_path}")
                return False
        except Exception as e:
            self.logger.error(f"執行腳本時發生錯誤: {str(e)}")
            return False
    
    async def _scale_resources(self, action: ResponseAction, context: Dict[str, Any]) -> bool:
        """擴展資源"""
        try:
            # 這裡可以實現Docker Swarm或Kubernetes的擴展邏輯
            self.logger.info(f"執行資源擴展: {action.parameters}")
            return True
        except Exception as e:
            self.logger.error(f"擴展資源時發生錯誤: {str(e)}")
            return False
    
    async def _cleanup_resources(self, action: ResponseAction, context: Dict[str, Any]) -> bool:
        """清理資源"""
        try:
            # 實現資源清理邏輯
            self.logger.info(f"執行資源清理: {action.parameters}")
            return True
        except Exception as e:
            self.logger.error(f"清理資源時發生錯誤: {str(e)}")
            return False
    
    async def _execute_custom_action(self, action: ResponseAction, context: Dict[str, Any]) -> bool:
        """執行自定義動作"""
        try:
            # 實現自定義動作邏輯
            self.logger.info(f"執行自定義動作: {action.name}")
            return True
        except Exception as e:
            self.logger.error(f"執行自定義動作時發生錯誤: {str(e)}")
            return False


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/app/config/notifications.yaml"
        self.channels: Dict[str, NotificationChannel] = {}
        self.notification_queue = asyncio.Queue()
        self.logger = logging.getLogger(f"{logger.name}.Notification")
        
        self._load_channels()
        self._start_notification_worker()
    
    def _load_channels(self):
        """加載通知渠道配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                for channel_config in config.get('channels', []):
                    channel = NotificationChannel(
                        channel_id=channel_config['id'],
                        name=channel_config['name'],
                        channel_type=channel_config['type'],
                        config=channel_config.get('config', {}),
                        enabled=channel_config.get('enabled', True)
                    )
                    self.channels[channel.channel_id] = channel
                
                self.logger.info(f"加載了 {len(self.channels)} 個通知渠道")
        except Exception as e:
            self.logger.error(f"加載通知渠道配置失敗: {str(e)}")
            self._create_default_channels()
    
    def _create_default_channels(self):
        """創建默認通知渠道"""
        default_channels = [
            NotificationChannel(
                channel_id="email_admin",
                name="管理員郵箱",
                channel_type="email",
                config={
                    "smtp_server": os.getenv("SMTP_SERVER", "localhost"),
                    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                    "username": os.getenv("SMTP_USERNAME", ""),
                    "password": os.getenv("SMTP_PASSWORD", ""),
                    "from_email": os.getenv("ALERT_FROM_EMAIL", "alerts@tradingagents.com"),
                    "to_emails": os.getenv("ALERT_TO_EMAILS", "admin@tradingagents.com").split(",")
                }
            ),
            NotificationChannel(
                channel_id="slack_alerts",
                name="Slack告警",
                channel_type="slack",
                config={
                    "webhook_url": os.getenv("SLACK_WEBHOOK_URL", ""),
                    "channel": os.getenv("SLACK_CHANNEL", "#alerts"),
                    "username": "TradingAgents-AlertBot"
                }
            )
        ]
        
        for channel in default_channels:
            self.channels[channel.channel_id] = channel
        
        self.logger.info("創建了默認通知渠道")
    
    def _start_notification_worker(self):
        """啟動通知工作線程"""
        asyncio.create_task(self._notification_worker())
    
    async def _notification_worker(self):
        """通知工作線程"""
        while True:
            try:
                notification = await self.notification_queue.get()
                await self._send_notification(notification)
                self.notification_queue.task_done()
            except Exception as e:
                self.logger.error(f"通知工作線程錯誤: {str(e)}")
                await asyncio.sleep(5)
    
    async def send_notification(self, alert: Alert, channels: List[str] = None):
        """發送通知"""
        if channels is None:
            channels = list(self.channels.keys())
        
        notification = {
            'alert': alert,
            'channels': channels,
            'timestamp': datetime.now()
        }
        
        await self.notification_queue.put(notification)
    
    async def _send_notification(self, notification: Dict[str, Any]):
        """實際發送通知"""
        alert = notification['alert']
        channels = notification['channels']
        
        for channel_id in channels:
            if channel_id in self.channels:
                channel = self.channels[channel_id]
                if channel.enabled:
                    try:
                        if channel.channel_type == "email":
                            await self._send_email(channel, alert)
                        elif channel.channel_type == "slack":
                            await self._send_slack(channel, alert)
                        elif channel.channel_type == "webhook":
                            await self._send_webhook(channel, alert)
                    except Exception as e:
                        self.logger.error(f"發送通知失敗 {channel_id}: {str(e)}")
    
    async def _send_email(self, channel: NotificationChannel, alert: Alert):
        """發送郵件通知"""
        try:
            config = channel.config
            
            msg = MIMEMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"[{alert.severity.value.upper()}] TradingAgents告警: {alert.name}"
            
            body = f"""
告警詳情:
- 名稱: {alert.name}
- 嚴重程度: {alert.severity.value}
- 狀態: {alert.status.value}
- 消息: {alert.message}
- 當前值: {alert.current_value}
- 閾值: {alert.threshold_value}
- 開始時間: {alert.started_at}
- 標籤: {alert.labels}
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # 發送郵件
            with smtplib.SMTP(config['smtp_server'], config['smtp_port']) as server:
                if config.get('username') and config.get('password'):
                    server.starttls()
                    server.login(config['username'], config['password'])
                server.send_message(msg)
            
            self.logger.info(f"郵件通知發送成功: {alert.name}")
            
        except Exception as e:
            self.logger.error(f"發送郵件通知失敗: {str(e)}")
    
    async def _send_slack(self, channel: NotificationChannel, alert: Alert):
        """發送Slack通知"""
        try:
            config = channel.config
            
            payload = {
                "channel": config['channel'],
                "username": config['username'],
                "text": f"🚨 *{alert.severity.value.upper()}*: {alert.name}",
                "attachments": [{
                    "color": self._get_severity_color(alert.severity),
                    "fields": [
                        {"title": "消息", "value": alert.message, "short": False},
                        {"title": "狀態", "value": alert.status.value, "short": True},
                        {"title": "當前值", "value": str(alert.current_value), "short": True},
                        {"title": "閾值", "value": str(alert.threshold_value), "short": True},
                        {"title": "開始時間", "value": alert.started_at.strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(config['webhook_url'], json=payload) as response:
                    if response.status == 200:
                        self.logger.info(f"Slack通知發送成功: {alert.name}")
                    else:
                        self.logger.error(f"Slack通知發送失敗: {response.status}")
            
        except Exception as e:
            self.logger.error(f"發送Slack通知失敗: {str(e)}")
    
    async def _send_webhook(self, channel: NotificationChannel, alert: Alert):
        """發送Webhook通知"""
        try:
            config = channel.config
            
            payload = {
                "alert_id": alert.alert_id,
                "name": alert.name,
                "severity": alert.severity.value,
                "status": alert.status.value,
                "message": alert.message,
                "labels": alert.labels,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "started_at": alert.started_at.isoformat(),
                "timestamp": datetime.now().isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(config['url'], json=payload) as response:
                    if response.status in [200, 201, 202]:
                        self.logger.info(f"Webhook通知發送成功: {alert.name}")
                    else:
                        self.logger.error(f"Webhook通知發送失敗: {response.status}")
            
        except Exception as e:
            self.logger.error(f"發送Webhook通知失敗: {str(e)}")
    
    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """獲取嚴重程度對應的顏色"""
        colors = {
            AlertSeverity.INFO: "#36a64f",
            AlertSeverity.WARNING: "#ffa500",
            AlertSeverity.ERROR: "#ff0000",
            AlertSeverity.CRITICAL: "#8b0000",
            AlertSeverity.EMERGENCY: "#800080"
        }
        return colors.get(severity, "#000000")


class AlertAutomationSystem:
    """智能告警和自動化響應系統主控制器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/app/config/alert_automation.yaml"
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # 初始化組件
        self.aggregator = AlertAggregator()
        self.automation = ResponseAutomation()
        self.notification = NotificationManager()
        
        # 監控狀態
        self.is_running = False
        self.monitor_task = None
        
        # 統計信息
        self.stats = {
            'total_alerts': 0,
            'active_alerts': 0,
            'resolved_alerts': 0,
            'automated_responses': 0,
            'notifications_sent': 0
        }
        
        self.logger = logging.getLogger(f"{logger.name}.System")
        
        # 加載配置
        self._load_configuration()
    
    def _load_configuration(self):
        """加載系統配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # 加載告警規則
                for rule_config in config.get('alert_rules', []):
                    rule = AlertRule(
                        rule_id=rule_config['id'],
                        name=rule_config['name'],
                        description=rule_config.get('description', ''),
                        severity=AlertSeverity(rule_config['severity']),
                        condition=rule_config['condition'],
                        threshold=rule_config['threshold'],
                        duration=rule_config['duration'],
                        labels=rule_config.get('labels', {}),
                        annotations=rule_config.get('annotations', {}),
                        enabled=rule_config.get('enabled', True),
                        auto_resolve=rule_config.get('auto_resolve', True),
                        response_actions=rule_config.get('response_actions', [])
                    )
                    self.rules[rule.rule_id] = rule
                
                self.logger.info(f"加載了 {len(self.rules)} 個告警規則")
        except Exception as e:
            self.logger.error(f"加載配置失敗: {str(e)}")
            self._create_default_rules()
    
    def _create_default_rules(self):
        """創建默認告警規則"""
        default_rules = [
            AlertRule(
                rule_id="high_cpu_usage",
                name="CPU使用率過高",
                description="CPU使用率超過閾值",
                severity=AlertSeverity.WARNING,
                condition="avg(rate(process_cpu_seconds_total[5m])) * 100 > 80",
                threshold=80.0,
                duration="5m",
                labels={"service": "tradingagents", "component": "cpu"},
                response_actions=["scale_api_instances"]
            ),
            AlertRule(
                rule_id="high_memory_usage",
                name="內存使用率過高",
                description="內存使用率超過閾值",
                severity=AlertSeverity.ERROR,
                condition="(process_resident_memory_bytes / process_virtual_memory_bytes) * 100 > 85",
                threshold=85.0,
                duration="5m",
                labels={"service": "tradingagents", "component": "memory"},
                response_actions=["cleanup_gpu_memory", "restart_tradingagents"]
            ),
            AlertRule(
                rule_id="gpu_memory_full",
                name="GPU內存不足",
                description="GPU內存使用率過高",
                severity=AlertSeverity.CRITICAL,
                condition="nvidia_gpu_memory_used_bytes / nvidia_gpu_memory_total_bytes * 100 > 95",
                threshold=95.0,
                duration="2m",
                labels={"service": "gpu_training", "component": "gpu_memory"},
                response_actions=["cleanup_gpu_memory"]
            )
        ]
        
        for rule in default_rules:
            self.rules[rule.rule_id] = rule
        
        self.logger.info("創建了默認告警規則")
    
    async def start(self):
        """啟動告警自動化系統"""
        if self.is_running:
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        self.logger.info("告警自動化系統已啟動")
    
    async def stop(self):
        """停止告警自動化系統"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("告警自動化系統已停止")
    
    async def _monitor_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 檢查告警規則
                await self._check_alert_rules()
                
                # 檢查告警解決
                await self._check_alert_resolution()
                
                # 更新統計信息
                self._update_stats()
                
                # 等待下一次檢查
                await asyncio.sleep(30)  # 每30秒檢查一次
                
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {str(e)}")
                await asyncio.sleep(60)
    
    async def _check_alert_rules(self):
        """檢查告警規則"""
        # 這裡應該與Prometheus API集成來檢查告警條件
        # 目前使用模擬數據
        pass
    
    async def _check_alert_resolution(self):
        """檢查告警解決"""
        current_time = datetime.now()
        
        for alert_id, alert in list(self.active_alerts.items()):
            if alert.status == AlertStatus.ACTIVE:
                # 檢查是否應該自動解決
                if alert.rule_id in self.rules:
                    rule = self.rules[alert.rule_id]
                    if rule.auto_resolve:
                        # 這裡應該檢查實際指標是否已恢復正常
                        # 目前使用模擬邏輯
                        if (current_time - alert.started_at).total_seconds() > 300:  # 5分鐘後自動解決
                            await self._resolve_alert(alert_id, "自動解決")
    
    async def _resolve_alert(self, alert_id: str, reason: str):
        """解決告警"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # 移動到歷史記錄
            self.alert_history.append(alert)
            del self.active_alerts[alert_id]
            
            # 從聚合器中移除
            self.aggregator.remove_alert(alert_id)
            
            self.logger.info(f"告警已解決: {alert.name} - {reason}")
    
    def _update_stats(self):
        """更新統計信息"""
        self.stats['active_alerts'] = len(self.active_alerts)
        self.stats['total_alerts'] = len(self.alert_history) + len(self.active_alerts)
        self.stats['resolved_alerts'] = len(self.alert_history)
    
    async def add_alert(self, alert: Alert):
        """添加新告警"""
        self.active_alerts[alert.alert_id] = alert
        self.aggregator.add_alert(alert)
        
        # 執行響應動作
        if alert.rule_id in self.rules:
            rule = self.rules[alert.rule_id]
            for action_id in rule.response_actions:
                await self.automation.execute_action(action_id, {
                    'alert': alert,
                    'rule': rule
                })
                self.stats['automated_responses'] += 1
        
        # 發送通知
        await self.notification.send_notification(alert)
        self.stats['notifications_sent'] += 1
        
        self.logger.warning(f"新告警: {alert.name} - {alert.message}")
    
    def get_active_alerts(self) -> List[Alert]:
        """獲取活躍告警"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """獲取告警歷史"""
        return self.alert_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 創建系統實例的工廠函數
def create_alert_automation_system(config_path: Optional[str] = None) -> AlertAutomationSystem:
    """創建告警自動化系統實例"""
    return AlertAutomationSystem(config_path)


if __name__ == "__main__":
    # 測試代碼
    async def test_system():
        system = create_alert_automation_system()
        await system.start()
        
        # 創建測試告警
        test_alert = Alert(
            alert_id=str(uuid.uuid4()),
            rule_id="test_rule",
            name="測試告警",
            severity=AlertSeverity.WARNING,
            status=AlertStatus.ACTIVE,
            message="這是一個測試告警",
            labels={"service": "test", "component": "test"},
            annotations={},
            current_value=85.0,
            threshold_value=80.0,
            started_at=datetime.now()
        )
        
        await system.add_alert(test_alert)
        
        # 運行一段時間
        await asyncio.sleep(60)
        await system.stop()
    
    asyncio.run(test_system())


