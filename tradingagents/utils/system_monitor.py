#!/usr/bin/env python3
"""
System Monitor - 系統監控和健康檢查機制
天工 (TianGong) - 不老傳說 系統健康監控和告警系統

此模組負責：
1. 實時系統健康監控
2. 關鍵指標追蹤
3. 自動告警機制
4. 性能分析和報告
"""

import asyncio
import json
import logging
import os
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import aiohttp

class AlertLevel(Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(Enum):
    """指標類型"""
    SYSTEM = "system"          # 系統指標
    APPLICATION = "application" # 應用指標
    BUSINESS = "business"      # 業務指標
    AI_ANALYSIS = "ai_analysis" # AI分析指標

@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_io_sent: int
    network_io_recv: int
    process_count: int
    load_average: float

@dataclass
class ApplicationMetrics:
    """應用指標"""
    timestamp: str
    api_requests_count: int
    api_response_time_avg: float
    api_error_rate: float
    database_connections: int
    cache_hit_rate: float
    active_sessions: int
    queue_size: int

@dataclass 
class AIAnalysisMetrics:
    """AI分析指標"""
    timestamp: str
    analysis_requests: int
    analysis_success_rate: float
    avg_analysis_time: float
    llm_api_calls: int
    llm_api_cost: float
    enabled_users: int
    concurrent_analyses: int

@dataclass
class Alert:
    """告警"""
    id: str
    level: AlertLevel
    metric_type: MetricType
    metric_name: str
    current_value: Any
    threshold_value: Any
    message: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None

class SystemMonitor:
    """系統監控器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 監控狀態
        self.is_monitoring = False
        self.monitoring_task = None
        
        # 指標歷史
        self.system_metrics_history: List[SystemMetrics] = []
        self.app_metrics_history: List[ApplicationMetrics] = []
        self.ai_metrics_history: List[AIAnalysisMetrics] = []
        
        # 告警管理
        self.alerts: List[Alert] = []
        self.alert_callbacks: List[Callable] = []
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            'monitoring_interval': 30,  # 30秒監控間隔
            'metrics_retention_hours': 24,  # 保留24小時指標
            'alert_thresholds': {
                'cpu_percent': 80.0,         # CPU使用率 > 80%
                'memory_percent': 85.0,      # 記憶體使用率 > 85%
                'disk_percent': 90.0,        # 磁碟使用率 > 90%
                'api_error_rate': 0.05,      # API錯誤率 > 5%
                'api_response_time': 3.0,    # API響應時間 > 3秒
                'analysis_error_rate': 0.10, # AI分析錯誤率 > 10%
                'analysis_time': 60.0,       # AI分析時間 > 60秒
                'llm_api_cost_hourly': 100.0 # LLM API每小時成本 > $100
            },
            'alert_cooldown': 300,  # 5分鐘告警冷卻期
            'webhook_url': os.getenv('ALERT_WEBHOOK_URL'),
            'slack_webhook': os.getenv('SLACK_WEBHOOK_URL'),
            'email_alerts': os.getenv('EMAIL_ALERTS', 'false').lower() == 'true'
        }
    
    async def start_monitoring(self):
        """開始監控"""
        if self.is_monitoring:
            self.logger.warning("監控已在運行中")
            return
        
        self.is_monitoring = True
        self.logger.info("🚀 開始系統監控")
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # 啟動清理任務
        asyncio.create_task(self._cleanup_old_metrics())
    
    async def stop_monitoring(self):
        """停止監控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ 系統監控已停止")
    
    async def _monitoring_loop(self):
        """監控主循環"""
        try:
            while self.is_monitoring:
                try:
                    # 收集各類指標
                    system_metrics = await self._collect_system_metrics()
                    app_metrics = await self._collect_application_metrics()
                    ai_metrics = await self._collect_ai_analysis_metrics()
                    
                    # 存儲指標
                    self.system_metrics_history.append(system_metrics)
                    self.app_metrics_history.append(app_metrics)
                    self.ai_metrics_history.append(ai_metrics)
                    
                    # 檢查告警條件
                    await self._check_alerts(system_metrics, app_metrics, ai_metrics)
                    
                    # 記錄調試信息
                    self.logger.debug(f"監控指標更新 - CPU: {system_metrics.cpu_percent:.1f}%, "
                                    f"記憶體: {system_metrics.memory_percent:.1f}%, "
                                    f"API錯誤率: {app_metrics.api_error_rate:.2%}")
                    
                except Exception as e:
                    self.logger.error(f"監控循環錯誤: {str(e)}")
                
                # 等待下次監控
                await asyncio.sleep(self.config['monitoring_interval'])
                
        except asyncio.CancelledError:
            self.logger.info("監控循環已取消")
        except Exception as e:
            self.logger.error(f"監控循環致命錯誤: {str(e)}")
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 磁碟使用率 (主磁碟)
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 網路IO
            net_io = psutil.net_io_counters()
            
            # 進程數量
            process_count = len(psutil.pids())
            
            # 系統負載 (Unix系統)
            try:
                load_average = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else cpu_percent / 100
            except:
                load_average = cpu_percent / 100
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_io_sent=net_io.bytes_sent,
                network_io_recv=net_io.bytes_recv,
                process_count=process_count,
                load_average=load_average
            )
            
        except Exception as e:
            self.logger.error(f"收集系統指標失敗: {str(e)}")
            # 返回預設值
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_io_sent=0,
                network_io_recv=0,
                process_count=0,
                load_average=0.0
            )
    
    async def _collect_application_metrics(self) -> ApplicationMetrics:
        """收集應用指標"""
        try:
            # 這裡應該與實際的應用監控系統整合
            # 暫時使用模擬數據
            
            # 模擬API指標
            api_requests = len(self.system_metrics_history) * 10  # 模擬請求數
            api_response_time = 0.5 + (api_requests / 1000) * 0.1  # 響應時間隨負載增加
            api_error_rate = max(0.01, min(0.10, api_requests / 10000))  # 錯誤率
            
            # 模擬資料庫連接
            database_connections = min(50, api_requests // 10)
            
            # 模擬快取命中率
            cache_hit_rate = max(0.7, 1.0 - (api_requests / 5000))
            
            # 模擬活躍會話
            active_sessions = api_requests // 5
            
            # 模擬隊列大小
            queue_size = max(0, api_requests - 100)
            
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                api_requests_count=api_requests,
                api_response_time_avg=api_response_time,
                api_error_rate=api_error_rate,
                database_connections=database_connections,
                cache_hit_rate=cache_hit_rate,
                active_sessions=active_sessions,
                queue_size=queue_size
            )
            
        except Exception as e:
            self.logger.error(f"收集應用指標失敗: {str(e)}")
            return ApplicationMetrics(
                timestamp=datetime.now().isoformat(),
                api_requests_count=0,
                api_response_time_avg=0.0,
                api_error_rate=0.0,
                database_connections=0,
                cache_hit_rate=1.0,
                active_sessions=0,
                queue_size=0
            )
    
    async def _collect_ai_analysis_metrics(self) -> AIAnalysisMetrics:
        """收集AI分析指標"""
        try:
            # 這裡應該與AI分析系統整合
            # 暫時使用模擬數據
            
            # 模擬AI分析指標
            analysis_requests = len(self.ai_metrics_history) * 2
            analysis_success_rate = max(0.85, 1.0 - (analysis_requests / 1000))
            avg_analysis_time = 30.0 + (analysis_requests / 100) * 5.0
            
            # 模擬LLM API調用
            llm_api_calls = analysis_requests * 3  # 每次分析約3次LLM調用
            llm_api_cost = llm_api_calls * 0.002  # 每次調用約$0.002
            
            # 模擬啟用AI的用戶數
            enabled_users = min(100, analysis_requests)
            
            # 模擬並發分析數
            concurrent_analyses = min(10, analysis_requests // 5)
            
            return AIAnalysisMetrics(
                timestamp=datetime.now().isoformat(),
                analysis_requests=analysis_requests,
                analysis_success_rate=analysis_success_rate,
                avg_analysis_time=avg_analysis_time,
                llm_api_calls=llm_api_calls,
                llm_api_cost=llm_api_cost,
                enabled_users=enabled_users,
                concurrent_analyses=concurrent_analyses
            )
            
        except Exception as e:
            self.logger.error(f"收集AI分析指標失敗: {str(e)}")
            return AIAnalysisMetrics(
                timestamp=datetime.now().isoformat(),
                analysis_requests=0,
                analysis_success_rate=1.0,
                avg_analysis_time=0.0,
                llm_api_calls=0,
                llm_api_cost=0.0,
                enabled_users=0,
                concurrent_analyses=0
            )
    
    async def _check_alerts(self, system: SystemMetrics, app: ApplicationMetrics, ai: AIAnalysisMetrics):
        """檢查告警條件"""
        thresholds = self.config['alert_thresholds']
        
        # 檢查系統指標告警
        await self._check_metric_alert('cpu_percent', system.cpu_percent, 
                                     thresholds['cpu_percent'], MetricType.SYSTEM)
        
        await self._check_metric_alert('memory_percent', system.memory_percent,
                                     thresholds['memory_percent'], MetricType.SYSTEM)
        
        await self._check_metric_alert('disk_percent', system.disk_percent,
                                     thresholds['disk_percent'], MetricType.SYSTEM)
        
        # 檢查應用指標告警
        await self._check_metric_alert('api_error_rate', app.api_error_rate,
                                     thresholds['api_error_rate'], MetricType.APPLICATION)
        
        await self._check_metric_alert('api_response_time', app.api_response_time_avg,
                                     thresholds['api_response_time'], MetricType.APPLICATION)
        
        # 檢查AI分析指標告警
        analysis_error_rate = 1.0 - ai.analysis_success_rate
        await self._check_metric_alert('analysis_error_rate', analysis_error_rate,
                                     thresholds['analysis_error_rate'], MetricType.AI_ANALYSIS)
        
        await self._check_metric_alert('analysis_time', ai.avg_analysis_time,
                                     thresholds['analysis_time'], MetricType.AI_ANALYSIS)
        
        # 檢查LLM API成本 (每小時)
        hourly_cost = ai.llm_api_cost * (3600 / self.config['monitoring_interval'])
        await self._check_metric_alert('llm_api_cost_hourly', hourly_cost,
                                     thresholds['llm_api_cost_hourly'], MetricType.AI_ANALYSIS)
    
    async def _check_metric_alert(self, metric_name: str, current_value: float, 
                                threshold: float, metric_type: MetricType):
        """檢查單個指標告警"""
        if current_value > threshold:
            # 檢查是否已有未解決的相同告警
            existing_alert = self._find_existing_alert(metric_name, metric_type)
            
            if not existing_alert:
                # 創建新告警
                alert = Alert(
                    id=f"{metric_name}_{int(time.time())}",
                    level=self._determine_alert_level(metric_name, current_value, threshold),
                    metric_type=metric_type,
                    metric_name=metric_name,
                    current_value=current_value,
                    threshold_value=threshold,
                    message=self._generate_alert_message(metric_name, current_value, threshold),
                    timestamp=datetime.now().isoformat()
                )
                
                self.alerts.append(alert)
                await self._send_alert(alert)
                
                self.logger.warning(f"🚨 新告警: {alert.message}")
        else:
            # 檢查是否有需要解決的告警
            existing_alert = self._find_existing_alert(metric_name, metric_type)
            if existing_alert and not existing_alert.resolved:
                existing_alert.resolved = True
                existing_alert.resolved_at = datetime.now().isoformat()
                
                self.logger.info(f"✅ 告警已解決: {existing_alert.message}")
                await self._send_alert_resolved(existing_alert)
    
    def _find_existing_alert(self, metric_name: str, metric_type: MetricType) -> Optional[Alert]:
        """查找現有告警"""
        for alert in reversed(self.alerts):  # 從最新的開始查找
            if (alert.metric_name == metric_name and 
                alert.metric_type == metric_type and 
                not alert.resolved):
                return alert
        return None
    
    def _determine_alert_level(self, metric_name: str, current_value: float, threshold: float) -> AlertLevel:
        """確定告警級別"""
        ratio = current_value / threshold
        
        if ratio > 2.0:
            return AlertLevel.CRITICAL
        elif ratio > 1.5:
            return AlertLevel.ERROR
        elif ratio > 1.2:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO
    
    def _generate_alert_message(self, metric_name: str, current_value: float, threshold: float) -> str:
        """生成告警訊息"""
        messages = {
            'cpu_percent': f'CPU使用率過高: {current_value:.1f}% (閾值: {threshold:.1f}%)',
            'memory_percent': f'記憶體使用率過高: {current_value:.1f}% (閾值: {threshold:.1f}%)',
            'disk_percent': f'磁碟使用率過高: {current_value:.1f}% (閾值: {threshold:.1f}%)',
            'api_error_rate': f'API錯誤率過高: {current_value:.2%} (閾值: {threshold:.2%})',
            'api_response_time': f'API響應時間過長: {current_value:.2f}s (閾值: {threshold:.2f}s)',
            'analysis_error_rate': f'AI分析錯誤率過高: {current_value:.2%} (閾值: {threshold:.2%})',
            'analysis_time': f'AI分析時間過長: {current_value:.1f}s (閾值: {threshold:.1f}s)',
            'llm_api_cost_hourly': f'LLM API每小時成本過高: ${current_value:.2f} (閾值: ${threshold:.2f})'
        }
        
        return messages.get(metric_name, f'{metric_name}: {current_value} > {threshold}')
    
    async def _send_alert(self, alert: Alert):
        """發送告警"""
        try:
            # 調用註冊的回調函數
            for callback in self.alert_callbacks:
                try:
                    await callback(alert)
                except Exception as e:
                    self.logger.error(f"告警回調失敗: {str(e)}")
            
            # 發送Webhook通知
            if self.config.get('webhook_url'):
                await self._send_webhook_alert(alert)
            
            # 發送Slack通知
            if self.config.get('slack_webhook'):
                await self._send_slack_alert(alert)
            
        except Exception as e:
            self.logger.error(f"發送告警失敗: {str(e)}")
    
    async def _send_alert_resolved(self, alert: Alert):
        """發送告警解決通知"""
        try:
            # 創建解決通知
            resolved_message = f"✅ 告警已解決: {alert.message}"
            
            # 發送通知 (簡化版)
            self.logger.info(resolved_message)
            
        except Exception as e:
            self.logger.error(f"發送告警解決通知失敗: {str(e)}")
    
    async def _send_webhook_alert(self, alert: Alert):
        """發送Webhook告警"""
        try:
            webhook_url = self.config['webhook_url']
            if not webhook_url:
                return
            
            payload = {
                'alert': asdict(alert),
                'system': 'TradingAgents',
                'environment': os.getenv('ENVIRONMENT', 'development')
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self.logger.debug("Webhook告警發送成功")
                    else:
                        self.logger.warning(f"Webhook告警發送失敗: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Webhook告警發送錯誤: {str(e)}")
    
    async def _send_slack_alert(self, alert: Alert):
        """發送Slack告警"""
        try:
            slack_webhook = self.config['slack_webhook']
            if not slack_webhook:
                return
            
            # Slack訊息格式
            color_map = {
                AlertLevel.INFO: "#36a64f",
                AlertLevel.WARNING: "#ff9900", 
                AlertLevel.ERROR: "#ff4444",
                AlertLevel.CRITICAL: "#990000"
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.level, "#ff9900"),
                    "title": f"TradingAgents {alert.level.value.upper()} Alert",
                    "text": alert.message,
                    "fields": [
                        {"title": "Metric", "value": alert.metric_name, "short": True},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold_value), "short": True},
                        {"title": "Time", "value": alert.timestamp, "short": True}
                    ],
                    "footer": "TradingAgents Monitoring",
                    "ts": int(datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp())
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(slack_webhook, json=payload, timeout=10) as response:
                    if response.status == 200:
                        self.logger.debug("Slack告警發送成功")
                    else:
                        self.logger.warning(f"Slack告警發送失敗: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Slack告警發送錯誤: {str(e)}")
    
    async def _cleanup_old_metrics(self):
        """清理舊指標"""
        while self.is_monitoring:
            try:
                cutoff_time = datetime.now() - timedelta(hours=self.config['metrics_retention_hours'])
                cutoff_str = cutoff_time.isoformat()
                
                # 清理系統指標
                self.system_metrics_history = [
                    m for m in self.system_metrics_history 
                    if m.timestamp > cutoff_str
                ]
                
                # 清理應用指標
                self.app_metrics_history = [
                    m for m in self.app_metrics_history
                    if m.timestamp > cutoff_str
                ]
                
                # 清理AI指標
                self.ai_metrics_history = [
                    m for m in self.ai_metrics_history
                    if m.timestamp > cutoff_str
                ]
                
                # 清理舊告警 (保留7天)
                alert_cutoff = datetime.now() - timedelta(days=7)
                alert_cutoff_str = alert_cutoff.isoformat()
                
                self.alerts = [
                    a for a in self.alerts
                    if a.timestamp > alert_cutoff_str
                ]
                
                self.logger.debug("舊指標清理完成")
                
            except Exception as e:
                self.logger.error(f"清理舊指標失敗: {str(e)}")
            
            # 每小時清理一次
            await asyncio.sleep(3600)
    
    # 公開方法
    def add_alert_callback(self, callback: Callable):
        """添加告警回調函數"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """獲取當前指標"""
        latest_system = self.system_metrics_history[-1] if self.system_metrics_history else None
        latest_app = self.app_metrics_history[-1] if self.app_metrics_history else None
        latest_ai = self.ai_metrics_history[-1] if self.ai_metrics_history else None
        
        return {
            'system': asdict(latest_system) if latest_system else None,
            'application': asdict(latest_app) if latest_app else None,
            'ai_analysis': asdict(latest_ai) if latest_ai else None,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """獲取活躍告警"""
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        return [asdict(alert) for alert in active_alerts]
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """獲取指標摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff_time.isoformat()
        
        # 篩選時間範圍內的指標
        recent_system = [m for m in self.system_metrics_history if m.timestamp > cutoff_str]
        recent_app = [m for m in self.app_metrics_history if m.timestamp > cutoff_str]
        recent_ai = [m for m in self.ai_metrics_history if m.timestamp > cutoff_str]
        
        summary = {
            'time_range_hours': hours,
            'system': self._calculate_metrics_stats(recent_system, [
                'cpu_percent', 'memory_percent', 'disk_percent'
            ]) if recent_system else {},
            'application': self._calculate_metrics_stats(recent_app, [
                'api_response_time_avg', 'api_error_rate', 'database_connections'
            ]) if recent_app else {},
            'ai_analysis': self._calculate_metrics_stats(recent_ai, [
                'avg_analysis_time', 'analysis_success_rate', 'llm_api_cost'
            ]) if recent_ai else {},
            'alert_count': len(self.get_active_alerts()),
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def _calculate_metrics_stats(self, metrics: List, fields: List[str]) -> Dict[str, Any]:
        """計算指標統計"""
        stats = {}
        
        for field in fields:
            values = [getattr(m, field) for m in metrics if hasattr(m, field)]
            if values:
                stats[field] = {
                    'avg': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        return stats

# 便利函數
async def quick_system_check() -> Dict[str, Any]:
    """快速系統檢查"""
    monitor = SystemMonitor()
    
    system_metrics = await monitor._collect_system_metrics()
    app_metrics = await monitor._collect_application_metrics()
    ai_metrics = await monitor._collect_ai_analysis_metrics()
    
    return {
        'system_health': 'healthy' if (
            system_metrics.cpu_percent < 80 and 
            system_metrics.memory_percent < 85
        ) else 'warning',
        'system': asdict(system_metrics),
        'application': asdict(app_metrics),
        'ai_analysis': asdict(ai_metrics),
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_monitor():
        monitor = SystemMonitor()
        
        print("🔍 測試系統監控器")
        
        # 快速檢查
        check_result = await quick_system_check()
        print(f"系統健康狀況: {check_result['system_health']}")
        
        # 啟動監控 (短時間測試)
        await monitor.start_monitoring()
        await asyncio.sleep(35)  # 運行35秒
        await monitor.stop_monitoring()
        
        # 獲取摘要
        summary = monitor.get_metrics_summary()
        print(f"指標摘要: {summary}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_monitor())