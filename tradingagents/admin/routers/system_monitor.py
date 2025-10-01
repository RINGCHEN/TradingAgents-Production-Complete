#!/usr/bin/env python3
"""
系統監控路由器 (System Monitor Router)
天工 (TianGong) - 系統監控 API 端點

此模組提供完整的系統監控 API 端點，包含：
1. 系統指標監控
2. 應用性能監控
3. 告警管理
4. 健康檢查
5. 監控配置管理
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..models.system_monitor import (
    SystemMetrics, ApplicationMetrics, PerformanceMetrics,
    Alert, AlertSummary, AlertQuery, AlertAcknowledgment,
    HealthCheckResult, SystemHealthStatus,
    MonitoringConfiguration, MonitoringThreshold, MonitoringQuery,
    MonitoringStatistics, SystemReport, SystemInformation,
    MonitoringDashboard, AlertLevel, MetricType, SystemStatus
)
from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access, require_permission
from ...auth.permissions import ResourceType, Action
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("system_monitor")
security_logger = get_security_logger("system_monitor")

# 創建路由器
router = APIRouter(prefix="/system", tags=["系統監控"])

# ==================== 系統指標監控 ====================

@router.get("/metrics/system", response_model=SystemMetrics, summary="獲取系統指標")
async def get_system_metrics(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取當前系統指標
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        metrics = await monitor_service.get_system_metrics()
        
        api_logger.info("系統指標查詢", extra={
            'admin_user_id': current_user.user_id,
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent
        })
        
        return metrics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/metrics/system',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("系統指標查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系統指標查詢服務暫時不可用"
        )

@router.get("/metrics/application", response_model=ApplicationMetrics, summary="獲取應用指標")
async def get_application_metrics(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取當前應用指標
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        metrics = await monitor_service.get_application_metrics()
        
        api_logger.info("應用指標查詢", extra={
            'admin_user_id': current_user.user_id,
            'requests_per_second': metrics.requests_per_second,
            'error_rate': metrics.error_rate
        })
        
        return metrics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/metrics/application',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("應用指標查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="應用指標查詢服務暫時不可用"
        )

@router.get("/metrics/performance", response_model=PerformanceMetrics, summary="獲取性能指標")
async def get_performance_metrics(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取當前性能指標
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        metrics = await monitor_service.get_performance_metrics()
        
        api_logger.info("性能指標查詢", extra={
            'admin_user_id': current_user.user_id,
            'response_time_p95': metrics.response_time_p95,
            'overall_performance': metrics.overall_performance
        })
        
        return metrics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/metrics/performance',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("性能指標查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="性能指標查詢服務暫時不可用"
        )

@router.get("/metrics/history", response_model=List[Dict[str, Any]], summary="獲取歷史指標")
async def get_metrics_history(
    query: MonitoringQuery = Depends(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取歷史指標數據
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        history = await monitor_service.get_metrics_history(query)
        
        api_logger.info("歷史指標查詢", extra={
            'admin_user_id': current_user.user_id,
            'query_params': query.dict(),
            'result_count': len(history)
        })
        
        return history
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/metrics/history',
            'admin_user_id': current_user.user_id,
            'query_params': query.dict()
        })
        
        api_logger.error("歷史指標查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="歷史指標查詢服務暫時不可用"
        )

# ==================== 告警管理 ====================

@router.get("/alerts", response_model=List[Alert], summary="獲取告警列表")
async def get_alerts(
    query: AlertQuery = Depends(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取告警列表
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        alerts = await monitor_service.get_alerts(query)
        
        api_logger.info("告警列表查詢", extra={
            'admin_user_id': current_user.user_id,
            'query_params': query.dict(),
            'alert_count': len(alerts)
        })
        
        return alerts
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/alerts',
            'admin_user_id': current_user.user_id,
            'query_params': query.dict()
        })
        
        api_logger.error("告警列表查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="告警查詢服務暫時不可用"
        )

@router.get("/alerts/summary", response_model=AlertSummary, summary="獲取告警摘要")
async def get_alert_summary(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取告警摘要統計
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        summary = await monitor_service.get_alert_summary()
        
        api_logger.info("告警摘要查詢", extra={
            'admin_user_id': current_user.user_id,
            'total_alerts': summary.total_alerts,
            'critical_alerts': summary.critical_alerts
        })
        
        return summary
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/alerts/summary',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("告警摘要查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="告警摘要查詢服務暫時不可用"
        )

@router.post("/alerts/acknowledge", summary="確認告警")
async def acknowledge_alerts(
    acknowledgment: AlertAcknowledgment,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    確認指定的告警
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        result = await monitor_service.acknowledge_alerts(
            acknowledgment, current_user.user_id
        )
        
        security_logger.info("告警確認操作", extra={
            'admin_user_id': current_user.user_id,
            'alert_ids': acknowledgment.alert_ids,
            'acknowledged_by': acknowledgment.acknowledged_by,
            'comment': acknowledgment.comment
        })
        
        return result
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/alerts/acknowledge',
            'admin_user_id': current_user.user_id,
            'acknowledgment': acknowledgment.dict()
        })
        
        api_logger.error("告警確認失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="告警確認服務暫時不可用"
        )

@router.delete("/alerts/{alert_id}", summary="刪除告警")
async def delete_alert(
    alert_id: str,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    刪除指定的告警
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        await monitor_service.delete_alert(alert_id, current_user.user_id)
        
        security_logger.info("告警刪除操作", extra={
            'admin_user_id': current_user.user_id,
            'alert_id': alert_id
        })
        
        return {"message": "告警刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/system/alerts/{alert_id}',
            'admin_user_id': current_user.user_id,
            'alert_id': alert_id
        })
        
        api_logger.error("告警刪除失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'alert_id': alert_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="告警刪除服務暫時不可用"
        )

# ==================== 健康檢查 ====================

@router.get("/health", response_model=SystemHealthStatus, summary="獲取系統健康狀態")
async def get_system_health(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取系統整體健康狀態
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        health_status = await monitor_service.get_system_health()
        
        api_logger.info("系統健康狀態查詢", extra={
            'admin_user_id': current_user.user_id,
            'overall_status': health_status.overall_status,
            'healthy_components': health_status.healthy_components,
            'error_components': health_status.error_components
        })
        
        return health_status
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/health',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("系統健康狀態查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系統健康檢查服務暫時不可用"
        )

@router.get("/health/{component}", response_model=HealthCheckResult, summary="獲取組件健康狀態")
async def get_component_health(
    component: str,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定組件的健康狀態
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        health_result = await monitor_service.get_component_health(component)
        
        if not health_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="組件不存在"
            )
        
        api_logger.info("組件健康狀態查詢", extra={
            'admin_user_id': current_user.user_id,
            'component': component,
            'status': health_result.status
        })
        
        return health_result
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/system/health/{component}',
            'admin_user_id': current_user.user_id,
            'component': component
        })
        
        api_logger.error("組件健康狀態查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'component': component
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="組件健康檢查服務暫時不可用"
        )

@router.post("/health/check", summary="執行健康檢查")
async def run_health_check(
    components: Optional[List[str]] = None,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    手動執行健康檢查
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        result = await monitor_service.run_health_check(components)
        
        security_logger.info("手動健康檢查執行", extra={
            'admin_user_id': current_user.user_id,
            'components': components,
            'check_count': len(result)
        })
        
        return {
            "message": "健康檢查執行完成",
            "checked_components": len(result),
            "results": result
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/health/check',
            'admin_user_id': current_user.user_id,
            'components': components
        })
        
        api_logger.error("手動健康檢查失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="健康檢查服務暫時不可用"
        )

# ==================== 監控配置管理 ====================

@router.get("/config", response_model=MonitoringConfiguration, summary="獲取監控配置")
async def get_monitoring_config(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取當前監控配置
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        config = await monitor_service.get_monitoring_config()
        
        api_logger.info("監控配置查詢", extra={
            'admin_user_id': current_user.user_id,
            'monitoring_enabled': config.monitoring_enabled,
            'alerting_enabled': config.alerting_enabled
        })
        
        return config
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/config',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("監控配置查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="監控配置查詢服務暫時不可用"
        )

@router.put("/config", response_model=MonitoringConfiguration, summary="更新監控配置")
async def update_monitoring_config(
    config: MonitoringConfiguration,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    更新監控配置
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        updated_config = await monitor_service.update_monitoring_config(
            config, current_user.user_id
        )
        
        security_logger.info("監控配置更新", extra={
            'admin_user_id': current_user.user_id,
            'monitoring_enabled': config.monitoring_enabled,
            'alerting_enabled': config.alerting_enabled,
            'collection_interval': config.collection_interval
        })
        
        return updated_config
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/config',
            'admin_user_id': current_user.user_id,
            'config': config.dict()
        })
        
        api_logger.error("監控配置更新失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="監控配置更新服務暫時不可用"
        )

# ==================== 統計和報告 ====================

@router.get("/statistics", response_model=MonitoringStatistics, summary="獲取監控統計")
async def get_monitoring_statistics(
    start_time: Optional[datetime] = Query(None, description="開始時間"),
    end_time: Optional[datetime] = Query(None, description="結束時間"),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取監控統計數據
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        # 設置默認時間範圍（最近24小時）
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        statistics = await monitor_service.get_monitoring_statistics(start_time, end_time)
        
        api_logger.info("監控統計查詢", extra={
            'admin_user_id': current_user.user_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'total_requests': statistics.total_requests
        })
        
        return statistics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/statistics',
            'admin_user_id': current_user.user_id,
            'start_time': start_time.isoformat() if start_time else None,
            'end_time': end_time.isoformat() if end_time else None
        })
        
        api_logger.error("監控統計查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="監控統計查詢服務暫時不可用"
        )

@router.post("/reports/generate", response_model=SystemReport, summary="生成系統報告")
async def generate_system_report(
    report_type: str = Query("daily", description="報告類型"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    生成系統報告
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        # 創建報告任務
        report = await monitor_service.create_system_report(report_type, current_user.user_id)
        
        # 添加後台任務生成詳細報告
        background_tasks.add_task(
            monitor_service.generate_detailed_report,
            report.report_id,
            current_user.user_id
        )
        
        security_logger.info("系統報告生成任務創建", extra={
            'admin_user_id': current_user.user_id,
            'report_id': report.report_id,
            'report_type': report_type
        })
        
        return report
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/reports/generate',
            'admin_user_id': current_user.user_id,
            'report_type': report_type
        })
        
        api_logger.error("系統報告生成失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'report_type': report_type
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系統報告生成服務暫時不可用"
        )

# ==================== 系統信息 ====================

@router.get("/info", response_model=SystemInformation, summary="獲取系統信息")
async def get_system_information(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取系統基本信息
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        system_info = await monitor_service.get_system_information()
        
        api_logger.info("系統信息查詢", extra={
            'admin_user_id': current_user.user_id,
            'hostname': system_info.hostname,
            'app_version': system_info.app_version
        })
        
        return system_info
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/info',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("系統信息查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="系統信息查詢服務暫時不可用"
        )

@router.get("/dashboard", response_model=MonitoringDashboard, summary="獲取監控儀表板")
async def get_monitoring_dashboard(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取監控儀表板數據
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        dashboard = await monitor_service.get_monitoring_dashboard()
        
        api_logger.info("監控儀表板查詢", extra={
            'admin_user_id': current_user.user_id,
            'dashboard_id': dashboard.dashboard_id,
            'system_status': dashboard.system_status.overall_status
        })
        
        return dashboard
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/dashboard',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("監控儀表板查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="監控儀表板查詢服務暫時不可用"
        )

# ==================== 健康檢查端點 ====================

@router.get("/monitor/health", summary="監控服務健康檢查")
async def monitor_service_health_check(
    current_user: UserContext = Depends(require_permission(ResourceType.SYSTEM, Action.READ))
):
    """
    監控服務自身的健康檢查
    """
    try:
        from ..services.system_monitor_service import SystemMonitorService
        monitor_service = SystemMonitorService()
        
        # 檢查監控服務狀態
        health_status = await monitor_service.service_health_check()
        
        return {
            "status": "healthy" if health_status["service"] else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": health_status,
            "service": "system_monitor"
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/system/monitor/health'
        })
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_id": error_info.error_id,
            "service": "system_monitor"
        }

if __name__ == "__main__":
    # 測試路由配置
    print("系統監控路由配置:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")