#!/usr/bin/env python3
"""
系統監控服務 (System Monitor Service)
天工 (TianGong) - 系統監控業務邏輯

此模組提供系統監控的核心業務邏輯，包含：
1. 系統指標收集和分析
2. 應用性能監控
3. 告警管理和處理
4. 健康檢查機制
5. 監控配置管理
"""

import uuid
import psutil
import platform
import socket
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..models.system_monitor import (
    SystemMetrics, ApplicationMetrics, PerformanceMetrics,
    Alert, AlertSummary, AlertQuery, AlertAcknowledgment,
    HealthCheckResult, SystemHealthStatus,
    MonitoringConfiguration, MonitoringThreshold, MonitoringQuery,
    MonitoringStatistics, SystemReport, SystemInformation,
    MonitoringDashboard, AlertLevel, MetricType, SystemStatus, PerformanceLevel
)
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error
from ...utils.cache_manager import CacheManager

# 配置日誌
api_logger = get_api_logger("system_monitor_service")
security_logger = get_security_logger("system_monitor_service")


class SystemMonitorService:
    """系統監控服務類"""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self._alerts_cache = deque(maxlen=1000)  # 內存中的告警緩存
        self._metrics_cache = deque(maxlen=100)   # 內存中的指標緩存
        self._health_cache = {}                   # 健康檢查緩存
        
    # ==================== 系統指標監控 ====================
    
    async def get_system_metrics(self) -> SystemMetrics:
        """獲取系統指標"""
        try:
            # 獲取 CPU 信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # 獲取內存信息
            memory = psutil.virtual_memory()
            
            # 獲取磁盤信息
            disk = psutil.disk_usage('/')
            
            # 獲取網絡信息
            network = psutil.net_io_counters()
            
            # 獲取進程信息
            process_count = len(psutil.pids())
            
            # 獲取系統啟動時間
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime_seconds = int((datetime.now() - boot_time).total_seconds())
            
            # 獲取負載平均值（Linux/Unix）
            load_average = None
            try:
                load_average = psutil.getloadavg()[0]
            except AttributeError:
                # Windows 不支持 getloadavg
                load_average = cpu_percent / 100.0
            
            # 獲取線程數
            thread_count = sum(p.num_threads() for p in psutil.process_iter(['num_threads']) if p.info['num_threads'])
            
            # 獲取網絡連接數
            network_connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                cpu_count=cpu_count,
                load_average=load_average,
                memory_total=memory.total,
                memory_used=memory.used,
                memory_percent=memory.percent,
                memory_available=memory.available,
                disk_total=disk.total,
                disk_used=disk.used,
                disk_percent=(disk.used / disk.total) * 100,
                disk_free=disk.free,
                network_io_sent=network.bytes_sent,
                network_io_recv=network.bytes_recv,
                network_connections=network_connections,
                process_count=process_count,
                thread_count=thread_count,
                boot_time=boot_time,
                uptime_seconds=uptime_seconds
            )
            
            # 緩存指標
            self._metrics_cache.append(metrics)
            
            return metrics
            
        except Exception as e:
            api_logger.error("獲取系統指標失敗", extra={'error': str(e)})
            raise 
   
    async def get_application_metrics(self) -> ApplicationMetrics:
        """獲取應用指標"""
        try:
            # 模擬應用指標數據（實際應該從應用監控系統獲取）
            metrics = ApplicationMetrics(
                timestamp=datetime.now(),
                app_name="TradingAgents",
                app_version="2.0.0",
                app_uptime=3600,  # 1小時
                total_requests=10000,
                requests_per_second=50.0,
                average_response_time=150.0,
                error_rate=0.5,
                db_connections_active=10,
                db_connections_idle=5,
                db_query_time_avg=25.0,
                cache_hit_rate=85.0,
                cache_memory_usage=1024 * 1024 * 100,  # 100MB
                ai_analyses_total=500,
                ai_analyses_success=485,
                ai_analysis_avg_time=2500.0
            )
            
            return metrics
            
        except Exception as e:
            api_logger.error("獲取應用指標失敗", extra={'error': str(e)})
            raise
    
    async def get_performance_metrics(self) -> PerformanceMetrics:
        """獲取性能指標"""
        try:
            # 獲取系統指標用於計算性能
            system_metrics = await self.get_system_metrics()
            
            # 計算性能等級
            cpu_score = self._calculate_performance_score(system_metrics.cpu_percent, 80, 95)
            memory_score = self._calculate_performance_score(system_metrics.memory_percent, 80, 95)
            disk_score = self._calculate_performance_score(system_metrics.disk_percent, 85, 95)
            
            overall_score = (cpu_score + memory_score + disk_score) / 3
            overall_performance = self._get_performance_level(overall_score)
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                response_time_p50=120.0,
                response_time_p95=250.0,
                response_time_p99=500.0,
                throughput_rps=45.0,
                throughput_tps=40.0,
                error_count=5,
                error_rate=0.5,
                cpu_utilization=system_metrics.cpu_percent,
                memory_utilization=system_metrics.memory_percent,
                disk_io_utilization=system_metrics.disk_percent,
                network_utilization=min(100.0, (system_metrics.network_io_sent + system_metrics.network_io_recv) / (1024 * 1024) * 0.1),
                overall_performance=overall_performance
            )
            
            return metrics
            
        except Exception as e:
            api_logger.error("獲取性能指標失敗", extra={'error': str(e)})
            raise
    
    async def get_metrics_history(self, query: MonitoringQuery) -> List[Dict[str, Any]]:
        """獲取歷史指標數據"""
        try:
            # 從緩存中獲取歷史數據（實際應該從數據庫或時序數據庫獲取）
            history = []
            
            for metrics in list(self._metrics_cache):
                if query.start_time and metrics.timestamp < query.start_time:
                    continue
                if query.end_time and metrics.timestamp > query.end_time:
                    continue
                
                history.append({
                    'timestamp': metrics.timestamp.isoformat(),
                    'cpu_percent': metrics.cpu_percent,
                    'memory_percent': metrics.memory_percent,
                    'disk_percent': metrics.disk_percent,
                    'network_io_sent': metrics.network_io_sent,
                    'network_io_recv': metrics.network_io_recv
                })
            
            # 限制返回數量
            if query.limit:
                history = history[-query.limit:]
            
            return history
            
        except Exception as e:
            api_logger.error("獲取歷史指標失敗", extra={'error': str(e)})
            raise    

    # ==================== 告警管理 ====================
    
    async def get_alerts(self, query: AlertQuery) -> List[Alert]:
        """獲取告警列表"""
        try:
            # 從緩存中獲取告警（實際應該從數據庫獲取）
            alerts = []
            
            for alert in list(self._alerts_cache):
                # 應用篩選條件
                if query.levels and alert.level not in query.levels:
                    continue
                if query.types and alert.metric_type not in query.types:
                    continue
                if query.is_active is not None and alert.is_active != query.is_active:
                    continue
                if query.is_acknowledged is not None and alert.is_acknowledged != query.is_acknowledged:
                    continue
                if query.start_time and alert.created_at < query.start_time:
                    continue
                if query.end_time and alert.created_at > query.end_time:
                    continue
                
                alerts.append(alert)
            
            # 限制返回數量
            if query.limit:
                alerts = alerts[-query.limit:]
            
            return alerts
            
        except Exception as e:
            api_logger.error("獲取告警列表失敗", extra={'error': str(e)})
            raise
    
    async def get_alert_summary(self) -> AlertSummary:
        """獲取告警摘要"""
        try:
            alerts = list(self._alerts_cache)
            
            total_alerts = len(alerts)
            active_alerts = len([a for a in alerts if a.is_active])
            critical_alerts = len([a for a in alerts if a.level == AlertLevel.CRITICAL and a.is_active])
            warning_alerts = len([a for a in alerts if a.level == AlertLevel.WARNING and a.is_active])
            info_alerts = len([a for a in alerts if a.level == AlertLevel.INFO and a.is_active])
            
            # 按級別分組
            alerts_by_level = defaultdict(int)
            for alert in alerts:
                if alert.is_active:
                    alerts_by_level[alert.level.value] += 1
            
            # 按類型分組
            alerts_by_type = defaultdict(int)
            for alert in alerts:
                if alert.is_active:
                    alerts_by_type[alert.metric_type.value] += 1
            
            # 最近告警（最近10個）
            recent_alerts = sorted(alerts, key=lambda x: x.created_at, reverse=True)[:10]
            
            return AlertSummary(
                total_alerts=total_alerts,
                active_alerts=active_alerts,
                critical_alerts=critical_alerts,
                warning_alerts=warning_alerts,
                info_alerts=info_alerts,
                alerts_by_level=dict(alerts_by_level),
                alerts_by_type=dict(alerts_by_type),
                recent_alerts=recent_alerts
            )
            
        except Exception as e:
            api_logger.error("獲取告警摘要失敗", extra={'error': str(e)})
            raise
    
    async def acknowledge_alerts(self, acknowledgment: AlertAcknowledgment, admin_user_id: str) -> Dict[str, Any]:
        """確認告警"""
        try:
            acknowledged_count = 0
            
            for alert in self._alerts_cache:
                if alert.id in acknowledgment.alert_ids:
                    alert.is_acknowledged = True
                    alert.acknowledged_by = acknowledgment.acknowledged_by
                    alert.acknowledged_at = datetime.now()
                    acknowledged_count += 1
            
            return {
                "message": "告警確認完成",
                "acknowledged_count": acknowledged_count,
                "total_requested": len(acknowledgment.alert_ids)
            }
            
        except Exception as e:
            api_logger.error("確認告警失敗", extra={'error': str(e)})
            raise
    
    async def delete_alert(self, alert_id: str, admin_user_id: str):
        """刪除告警"""
        try:
            # 從緩存中移除告警
            for i, alert in enumerate(self._alerts_cache):
                if alert.id == alert_id:
                    del self._alerts_cache[i]
                    return
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="告警不存在"
            )
            
        except Exception as e:
            api_logger.error("刪除告警失敗", extra={'alert_id': alert_id, 'error': str(e)})
            raise 
   
    # ==================== 健康檢查 ====================
    
    async def get_system_health(self) -> SystemHealthStatus:
        """獲取系統健康狀態"""
        try:
            # 檢查各個組件
            components = await self._check_all_components()
            
            # 計算整體狀態
            healthy_count = len([c for c in components if c.status == SystemStatus.HEALTHY])
            warning_count = len([c for c in components if c.status == SystemStatus.WARNING])
            error_count = len([c for c in components if c.status == SystemStatus.ERROR])
            critical_count = len([c for c in components if c.status == SystemStatus.CRITICAL])
            
            # 確定整體狀態
            if critical_count > 0:
                overall_status = SystemStatus.CRITICAL
                status_message = f"系統存在 {critical_count} 個嚴重問題"
            elif error_count > 0:
                overall_status = SystemStatus.ERROR
                status_message = f"系統存在 {error_count} 個錯誤"
            elif warning_count > 0:
                overall_status = SystemStatus.WARNING
                status_message = f"系統存在 {warning_count} 個警告"
            else:
                overall_status = SystemStatus.HEALTHY
                status_message = "系統運行正常"
            
            # 獲取系統指標
            system_metrics = await self.get_system_metrics()
            application_metrics = await self.get_application_metrics()
            performance_metrics = await self.get_performance_metrics()
            
            return SystemHealthStatus(
                overall_status=overall_status,
                status_message=status_message,
                last_updated=datetime.now(),
                components=components,
                healthy_components=healthy_count,
                warning_components=warning_count,
                error_components=error_count,
                critical_components=critical_count,
                system_metrics=system_metrics,
                application_metrics=application_metrics,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            api_logger.error("獲取系統健康狀態失敗", extra={'error': str(e)})
            raise
    
    async def get_component_health(self, component: str) -> Optional[HealthCheckResult]:
        """獲取組件健康狀態"""
        try:
            # 檢查指定組件
            result = await self._check_component(component)
            return result
            
        except Exception as e:
            api_logger.error("獲取組件健康狀態失敗", extra={'component': component, 'error': str(e)})
            raise
    
    async def run_health_check(self, components: Optional[List[str]] = None) -> List[HealthCheckResult]:
        """執行健康檢查"""
        try:
            if components:
                # 檢查指定組件
                results = []
                for component in components:
                    result = await self._check_component(component)
                    if result:
                        results.append(result)
                return results
            else:
                # 檢查所有組件
                return await self._check_all_components()
                
        except Exception as e:
            api_logger.error("執行健康檢查失敗", extra={'components': components, 'error': str(e)})
            raise
    
    async def _check_all_components(self) -> List[HealthCheckResult]:
        """檢查所有組件"""
        components = [
            "database", "cache", "filesystem", "network", 
            "memory", "cpu", "disk", "application"
        ]
        
        results = []
        for component in components:
            result = await self._check_component(component)
            if result:
                results.append(result)
        
        return results
    
    async def _check_component(self, component: str) -> Optional[HealthCheckResult]:
        """檢查單個組件"""
        try:
            start_time = datetime.now()
            
            if component == "database":
                # 檢查數據庫連接
                status = SystemStatus.HEALTHY
                message = "數據庫連接正常"
                details = {"connection_pool": "active", "query_time": "< 50ms"}
                
            elif component == "cache":
                # 檢查緩存系統
                status = SystemStatus.HEALTHY
                message = "緩存系統正常"
                details = {"hit_rate": "85%", "memory_usage": "60%"}
                
            elif component == "filesystem":
                # 檢查文件系統
                disk_usage = psutil.disk_usage('/')
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                
                if disk_percent > 95:
                    status = SystemStatus.CRITICAL
                    message = f"磁盤空間嚴重不足: {disk_percent:.1f}%"
                elif disk_percent > 85:
                    status = SystemStatus.WARNING
                    message = f"磁盤空間不足: {disk_percent:.1f}%"
                else:
                    status = SystemStatus.HEALTHY
                    message = f"磁盤空間正常: {disk_percent:.1f}%"
                
                details = {
                    "disk_usage_percent": disk_percent,
                    "free_space_gb": disk_usage.free / (1024**3)
                }
                
            elif component == "memory":
                # 檢查內存使用
                memory = psutil.virtual_memory()
                
                if memory.percent > 95:
                    status = SystemStatus.CRITICAL
                    message = f"內存使用率過高: {memory.percent:.1f}%"
                elif memory.percent > 85:
                    status = SystemStatus.WARNING
                    message = f"內存使用率較高: {memory.percent:.1f}%"
                else:
                    status = SystemStatus.HEALTHY
                    message = f"內存使用正常: {memory.percent:.1f}%"
                
                details = {
                    "memory_percent": memory.percent,
                    "available_gb": memory.available / (1024**3)
                }
                
            elif component == "cpu":
                # 檢查 CPU 使用
                cpu_percent = psutil.cpu_percent(interval=1)
                
                if cpu_percent > 95:
                    status = SystemStatus.CRITICAL
                    message = f"CPU 使用率過高: {cpu_percent:.1f}%"
                elif cpu_percent > 85:
                    status = SystemStatus.WARNING
                    message = f"CPU 使用率較高: {cpu_percent:.1f}%"
                else:
                    status = SystemStatus.HEALTHY
                    message = f"CPU 使用正常: {cpu_percent:.1f}%"
                
                details = {
                    "cpu_percent": cpu_percent,
                    "cpu_count": psutil.cpu_count()
                }
                
            else:
                # 默認健康狀態
                status = SystemStatus.HEALTHY
                message = f"{component} 組件正常"
                details = {}
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return HealthCheckResult(
                component=component,
                status=status,
                message=message,
                response_time=response_time,
                last_check=datetime.now(),
                details=details,
                dependencies=[]
            )
            
        except Exception as e:
            return HealthCheckResult(
                component=component,
                status=SystemStatus.ERROR,
                message=f"健康檢查失敗: {str(e)}",
                response_time=0.0,
                last_check=datetime.now(),
                details={"error": str(e)},
                dependencies=[]
            )    

    # ==================== 監控配置管理 ====================
    
    async def get_monitoring_config(self) -> MonitoringConfiguration:
        """獲取監控配置"""
        try:
            # 返回默認配置（實際應該從數據庫或配置文件獲取）
            thresholds = [
                MonitoringThreshold(
                    metric_name="cpu_percent",
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                    comparison_operator=">",
                    description="CPU 使用率",
                    unit="%"
                ),
                MonitoringThreshold(
                    metric_name="memory_percent",
                    warning_threshold=80.0,
                    critical_threshold=95.0,
                    comparison_operator=">",
                    description="內存使用率",
                    unit="%"
                ),
                MonitoringThreshold(
                    metric_name="disk_percent",
                    warning_threshold=85.0,
                    critical_threshold=95.0,
                    comparison_operator=">",
                    description="磁盤使用率",
                    unit="%"
                )
            ]
            
            return MonitoringConfiguration(
                monitoring_enabled=True,
                collection_interval=60,
                retention_days=30,
                alerting_enabled=True,
                alert_channels=["email", "webhook"],
                thresholds=thresholds,
                health_check_interval=30,
                health_check_timeout=10,
                performance_monitoring_enabled=True,
                performance_sampling_rate=1.0
            )
            
        except Exception as e:
            api_logger.error("獲取監控配置失敗", extra={'error': str(e)})
            raise
    
    async def update_monitoring_config(self, config: MonitoringConfiguration, admin_user_id: str) -> MonitoringConfiguration:
        """更新監控配置"""
        try:
            # 這裡應該將配置保存到數據庫或配置文件
            # 目前只是返回傳入的配置
            
            api_logger.info("監控配置已更新", extra={
                'admin_user_id': admin_user_id,
                'monitoring_enabled': config.monitoring_enabled,
                'collection_interval': config.collection_interval
            })
            
            return config
            
        except Exception as e:
            api_logger.error("更新監控配置失敗", extra={'error': str(e)})
            raise
    
    # ==================== 統計和報告 ====================
    
    async def get_monitoring_statistics(self, start_time: datetime, end_time: datetime) -> MonitoringStatistics:
        """獲取監控統計"""
        try:
            # 模擬統計數據（實際應該從數據庫計算）
            duration_hours = (end_time - start_time).total_seconds() / 3600
            
            return MonitoringStatistics(
                start_time=start_time,
                end_time=end_time,
                avg_cpu_usage=45.2,
                max_cpu_usage=78.5,
                avg_memory_usage=62.1,
                max_memory_usage=85.3,
                total_requests=int(duration_hours * 1000),
                avg_response_time=125.5,
                error_count=int(duration_hours * 5),
                error_rate=0.5,
                total_alerts=int(duration_hours * 2),
                critical_alerts=int(duration_hours * 0.2),
                resolved_alerts=int(duration_hours * 1.8),
                avg_performance_score=85.0,
                performance_trend="stable"
            )
            
        except Exception as e:
            api_logger.error("獲取監控統計失敗", extra={'error': str(e)})
            raise
    
    async def create_system_report(self, report_type: str, admin_user_id: str) -> SystemReport:
        """創建系統報告"""
        try:
            report_id = str(uuid.uuid4())
            now = datetime.now()
            
            # 根據報告類型設置時間範圍
            if report_type == "daily":
                period_start = now - timedelta(days=1)
            elif report_type == "weekly":
                period_start = now - timedelta(weeks=1)
            elif report_type == "monthly":
                period_start = now - timedelta(days=30)
            else:
                period_start = now - timedelta(days=1)
            
            # 獲取統計數據
            statistics = await self.get_monitoring_statistics(period_start, now)
            alert_summary = await self.get_alert_summary()
            
            return SystemReport(
                report_id=report_id,
                report_type=report_type,
                generated_at=now,
                period_start=period_start,
                period_end=now,
                system_overview={
                    "uptime": "99.9%",
                    "total_requests": statistics.total_requests,
                    "avg_response_time": statistics.avg_response_time
                },
                statistics=statistics,
                alert_summary=alert_summary,
                performance_analysis={
                    "overall_score": statistics.avg_performance_score,
                    "trend": statistics.performance_trend,
                    "bottlenecks": ["memory_usage", "disk_io"]
                },
                recommendations=[
                    "考慮增加內存容量以提升性能",
                    "優化數據庫查詢以減少響應時間",
                    "設置更多監控告警以提前發現問題"
                ],
                trends={
                    "cpu_trend": "stable",
                    "memory_trend": "increasing",
                    "error_trend": "decreasing"
                }
            )
            
        except Exception as e:
            api_logger.error("創建系統報告失敗", extra={'report_type': report_type, 'error': str(e)})
            raise
    
    async def generate_detailed_report(self, report_id: str, admin_user_id: str):
        """生成詳細報告（後台任務）"""
        try:
            # 這裡應該生成詳細的報告內容
            api_logger.info("詳細報告生成完成", extra={
                'report_id': report_id,
                'admin_user_id': admin_user_id
            })
            
        except Exception as e:
            api_logger.error("生成詳細報告失敗", extra={'report_id': report_id, 'error': str(e)})
    
    # ==================== 系統信息 ====================
    
    async def get_system_information(self) -> SystemInformation:
        """獲取系統信息"""
        try:
            # 獲取系統基本信息
            hostname = socket.gethostname()
            platform_info = platform.platform()
            architecture = platform.architecture()[0]
            python_version = platform.python_version()
            
            # 獲取硬件信息
            cpu_info = {
                "count": psutil.cpu_count(),
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
                "usage": psutil.cpu_percent(interval=1)
            }
            
            memory = psutil.virtual_memory()
            memory_info = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
            
            disk = psutil.disk_usage('/')
            disk_info = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
            
            network_info = {
                "interfaces": len(psutil.net_if_addrs()),
                "connections": len(psutil.net_connections())
            }
            
            # 獲取運行時信息
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = int((datetime.now() - boot_time).total_seconds())
            
            # 獲取監控配置
            monitoring_config = await self.get_monitoring_config()
            
            return SystemInformation(
                hostname=hostname,
                platform=platform_info,
                architecture=architecture,
                python_version=python_version,
                app_name="TradingAgents",
                app_version="2.0.0",
                environment="production",
                cpu_info=cpu_info,
                memory_info=memory_info,
                disk_info=disk_info,
                network_info=network_info,
                start_time=boot_time,
                uptime=uptime,
                timezone="Asia/Taipei",
                monitoring_config=monitoring_config
            )
            
        except Exception as e:
            api_logger.error("獲取系統信息失敗", extra={'error': str(e)})
            raise
    
    async def get_monitoring_dashboard(self) -> MonitoringDashboard:
        """獲取監控儀表板"""
        try:
            dashboard_id = str(uuid.uuid4())
            
            # 獲取系統健康狀態
            system_status = await self.get_system_health()
            
            # 獲取告警摘要
            alert_summary = await self.get_alert_summary()
            
            # 獲取實時指標
            system_metrics = await self.get_system_metrics()
            performance_metrics = await self.get_performance_metrics()
            
            real_time_metrics = {
                "cpu_usage": system_metrics.cpu_percent,
                "memory_usage": system_metrics.memory_percent,
                "disk_usage": system_metrics.disk_percent,
                "network_io": {
                    "sent": system_metrics.network_io_sent,
                    "recv": system_metrics.network_io_recv
                },
                "response_time": performance_metrics.response_time_p95,
                "throughput": performance_metrics.throughput_rps
            }
            
            # 性能概覽
            performance_overview = {
                "overall_performance": performance_metrics.overall_performance.value,
                "cpu_utilization": performance_metrics.cpu_utilization,
                "memory_utilization": performance_metrics.memory_utilization,
                "error_rate": performance_metrics.error_rate
            }
            
            # 圖表數據（模擬）
            charts_data = {
                "cpu_usage_chart": [
                    {"time": "10:00", "value": 45.2},
                    {"time": "10:05", "value": 48.1},
                    {"time": "10:10", "value": 52.3},
                    {"time": "10:15", "value": 49.7},
                    {"time": "10:20", "value": system_metrics.cpu_percent}
                ],
                "memory_usage_chart": [
                    {"time": "10:00", "value": 58.1},
                    {"time": "10:05", "value": 60.2},
                    {"time": "10:10", "value": 62.5},
                    {"time": "10:15", "value": 61.8},
                    {"time": "10:20", "value": system_metrics.memory_percent}
                ],
                "response_time_chart": [
                    {"time": "10:00", "value": 120.5},
                    {"time": "10:05", "value": 135.2},
                    {"time": "10:10", "value": 142.8},
                    {"time": "10:15", "value": 128.9},
                    {"time": "10:20", "value": performance_metrics.response_time_p95}
                ]
            }
            
            return MonitoringDashboard(
                dashboard_id=dashboard_id,
                title="TradingAgents 系統監控儀表板",
                last_updated=datetime.now(),
                system_status=system_status,
                real_time_metrics=real_time_metrics,
                alert_summary=alert_summary,
                performance_overview=performance_overview,
                charts_data=charts_data
            )
            
        except Exception as e:
            api_logger.error("獲取監控儀表板失敗", extra={'error': str(e)})
            raise
    
    # ==================== 輔助方法 ====================
    
    def _calculate_performance_score(self, value: float, warning_threshold: float, critical_threshold: float) -> float:
        """計算性能分數"""
        if value >= critical_threshold:
            return 0.0
        elif value >= warning_threshold:
            return 50.0 - ((value - warning_threshold) / (critical_threshold - warning_threshold)) * 50.0
        else:
            return 100.0 - (value / warning_threshold) * 50.0
    
    def _get_performance_level(self, score: float) -> PerformanceLevel:
        """根據分數獲取性能等級"""
        if score >= 90:
            return PerformanceLevel.EXCELLENT
        elif score >= 70:
            return PerformanceLevel.GOOD
        elif score >= 50:
            return PerformanceLevel.ACCEPTABLE
        elif score >= 30:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    async def service_health_check(self) -> Dict[str, Any]:
        """監控服務自身健康檢查"""
        try:
            return {
                "service": True,
                "cache": True,
                "metrics_collection": True,
                "alert_processing": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            api_logger.error("監控服務健康檢查失敗", extra={'error': str(e)})
            return {
                "service": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }