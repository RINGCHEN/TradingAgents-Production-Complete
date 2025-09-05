#!/usr/bin/env python3
"""
分析師管理路由器 (Analyst Management Router)
天工 (TianGong) - 分析師管理 API 端點

此模組提供完整的分析師管理 API 端點，包含：
1. 分析師註冊和管理
2. 分析任務協調和調度
3. 分析結果查詢和管理
4. 分析師性能監控
5. 分析師配置管理
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..models.analyst_coordinator import (
    AnalystInfo, AnalystRegistry, AnalystCommand, AnalystCommandResult,
    AnalysisRequest, AnalysisExecution, AnalysisResult,
    AnalystCoordinatorConfiguration, AnalystCoordinatorStatistics, AnalystCoordinatorHealth,
    AnalystQuery, AnalysisQuery, AnalystCoordinatorDashboard,
    AnalystStatus, AnalystType, AnalysisType, AnalysisStatus
)
from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("analyst_management")
security_logger = get_security_logger("analyst_management")

# 創建路由器
router = APIRouter(prefix="/analysts", tags=["分析師管理"])

# ==================== 分析師管理 ====================

@router.get("/registry", response_model=AnalystRegistry, summary="獲取分析師註冊表")
async def get_analyst_registry(
    query: AnalystQuery = Depends(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取分析師註冊表，包含所有註冊的分析師信息
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        registry = await coordinator_service.get_analyst_registry(query)
        
        api_logger.info("分析師註冊表查詢", extra={
            'admin_user_id': current_user.user_id,
            'query_params': query.dict(),
            'total_analysts': registry.total_analysts
        })
        
        return registry
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/registry',
            'admin_user_id': current_user.user_id,
            'query_params': query.dict()
        })
        
        api_logger.error("分析師註冊表查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析師註冊表查詢服務暫時不可用"
        )

@router.get("/{analyst_id}", response_model=AnalystInfo, summary="獲取分析師詳情")
async def get_analyst_info(
    analyst_id: str,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定分析師的詳細信息
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        analyst_info = await coordinator_service.get_analyst_info(analyst_id)
        
        if not analyst_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析師不存在"
            )
        
        api_logger.info("分析師詳情查詢", extra={
            'admin_user_id': current_user.user_id,
            'analyst_id': analyst_id,
            'analyst_status': analyst_info.status
        })
        
        return analyst_info
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/analysts/{analyst_id}',
            'admin_user_id': current_user.user_id,
            'analyst_id': analyst_id
        })
        
        api_logger.error("分析師詳情查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'analyst_id': analyst_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析師詳情查詢服務暫時不可用"
        )

@router.post("/{analyst_id}/command", response_model=AnalystCommandResult, summary="執行分析師命令")
async def execute_analyst_command(
    analyst_id: str,
    command: AnalystCommand,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    對指定分析師執行命令（啟動、停止、重啟等）
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        # 驗證分析師存在
        analyst_info = await coordinator_service.get_analyst_info(analyst_id)
        if not analyst_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析師不存在"
            )
        
        # 執行命令
        result = await coordinator_service.execute_analyst_command(analyst_id, command)
        
        security_logger.info("分析師命令執行", extra={
            'admin_user_id': current_user.user_id,
            'analyst_id': analyst_id,
            'command': command.command,
            'success': result.success,
            'execution_time': result.execution_time
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/analysts/{analyst_id}/command',
            'admin_user_id': current_user.user_id,
            'analyst_id': analyst_id,
            'command': command.dict()
        })
        
        api_logger.error("分析師命令執行失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'analyst_id': analyst_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析師命令執行服務暫時不可用"
        )

@router.post("/health-check", summary="執行分析師健康檢查")
async def run_analysts_health_check(
    analyst_ids: Optional[List[str]] = None,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    執行分析師健康檢查
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        results = await coordinator_service.run_analysts_health_check(analyst_ids)
        
        security_logger.info("分析師健康檢查執行", extra={
            'admin_user_id': current_user.user_id,
            'analyst_ids': analyst_ids,
            'check_count': len(results)
        })
        
        return {
            "message": "分析師健康檢查完成",
            "results": results,
            "total_checked": len(results),
            "healthy_analysts": len([r for r in results if r.get("status") == "healthy"])
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/health-check',
            'admin_user_id': current_user.user_id,
            'analyst_ids': analyst_ids
        })
        
        api_logger.error("分析師健康檢查失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析師健康檢查服務暫時不可用"
        )

# ==================== 分析任務管理 ====================

@router.post("/analysis", response_model=AnalysisExecution, summary="創建分析請求")
async def create_analysis_request(
    request: AnalysisRequest,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    創建新的分析請求
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        execution = await coordinator_service.create_analysis_request(request)
        
        security_logger.info("分析請求創建", extra={
            'admin_user_id': current_user.user_id,
            'request_id': request.request_id,
            'stock_id': request.stock_id,
            'execution_id': execution.execution_id,
            'assigned_analysts': execution.assigned_analysts
        })
        
        return execution
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/analysis',
            'admin_user_id': current_user.user_id,
            'request': request.dict()
        })
        
        api_logger.error("分析請求創建失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析請求創建服務暫時不可用"
        )

@router.get("/analysis", response_model=List[AnalysisExecution], summary="獲取分析執行列表")
async def get_analysis_executions(
    query: AnalysisQuery = Depends(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取分析執行列表
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        executions = await coordinator_service.get_analysis_executions(query)
        
        api_logger.info("分析執行列表查詢", extra={
            'admin_user_id': current_user.user_id,
            'query_params': query.dict(),
            'execution_count': len(executions)
        })
        
        return executions
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/analysis',
            'admin_user_id': current_user.user_id,
            'query_params': query.dict()
        })
        
        api_logger.error("分析執行列表查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析執行列表查詢服務暫時不可用"
        )

@router.get("/analysis/{execution_id}", response_model=AnalysisExecution, summary="獲取分析執行詳情")
async def get_analysis_execution(
    execution_id: str,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定分析執行的詳情
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        execution = await coordinator_service.get_analysis_execution(execution_id)
        
        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分析執行記錄不存在"
            )
        
        api_logger.info("分析執行詳情查詢", extra={
            'admin_user_id': current_user.user_id,
            'execution_id': execution_id,
            'execution_status': execution.status
        })
        
        return execution
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/analysts/analysis/{execution_id}',
            'admin_user_id': current_user.user_id,
            'execution_id': execution_id
        })
        
        api_logger.error("分析執行詳情查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'execution_id': execution_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析執行詳情查詢服務暫時不可用"
        )

# ==================== 協調器配置和監控 ====================

@router.get("/coordinator/statistics", response_model=AnalystCoordinatorStatistics, summary="獲取協調器統計")
async def get_coordinator_statistics(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取分析師協調器統計信息
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        statistics = await coordinator_service.get_coordinator_statistics()
        
        api_logger.info("協調器統計查詢", extra={
            'admin_user_id': current_user.user_id,
            'total_analysts': statistics.total_analysts,
            'total_analyses': statistics.total_analyses
        })
        
        return statistics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/coordinator/statistics',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("協調器統計查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="協調器統計查詢服務暫時不可用"
        )

@router.get("/coordinator/health", response_model=AnalystCoordinatorHealth, summary="獲取協調器健康狀態")
async def get_coordinator_health(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取分析師協調器健康狀態
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        health = await coordinator_service.get_coordinator_health()
        
        api_logger.info("協調器健康檢查", extra={
            'admin_user_id': current_user.user_id,
            'overall_status': health.overall_status
        })
        
        return health
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/coordinator/health',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("協調器健康檢查失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="協調器健康檢查服務暫時不可用"
        )

@router.get("/coordinator/dashboard", response_model=AnalystCoordinatorDashboard, summary="獲取協調器儀表板")
async def get_coordinator_dashboard(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取分析師協調器儀表板數據
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        # 獲取統計信息和健康狀態
        statistics = await coordinator_service.get_coordinator_statistics()
        health = await coordinator_service.get_coordinator_health()
        
        # 獲取實時數據
        analyst_query = AnalystQuery(statuses=[AnalystStatus.ACTIVE], limit=10)
        registry = await coordinator_service.get_analyst_registry(analyst_query)
        active_analysts = registry.analysts
        
        analysis_query = AnalysisQuery(limit=20)
        recent_analyses = await coordinator_service.get_analysis_executions(analysis_query)
        
        # 獲取表現最佳的分析師
        top_performing_query = AnalystQuery(limit=5)
        top_registry = await coordinator_service.get_analyst_registry(top_performing_query)
        top_performing_analysts = sorted(
            top_registry.analysts, 
            key=lambda x: x.success_rate, 
            reverse=True
        )[:5]
        
        # 構建儀表板
        dashboard = AnalystCoordinatorDashboard(
            dashboard_id=f"analyst_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            title="分析師協調器儀表板",
            last_updated=datetime.now(),
            statistics=statistics,
            health=health,
            active_analysts=active_analysts,
            recent_analyses=recent_analyses,
            top_performing_analysts=top_performing_analysts,
            charts_data={
                "analyst_performance": [
                    {"analyst_id": a.analyst_id, "success_rate": a.success_rate}
                    for a in top_performing_analysts
                ],
                "analysis_trends": [
                    {"date": datetime.now().strftime('%Y-%m-%d'), "count": len(recent_analyses)}
                ]
            }
        )
        
        api_logger.info("協調器儀表板查詢", extra={
            'admin_user_id': current_user.user_id,
            'dashboard_id': dashboard.dashboard_id
        })
        
        return dashboard
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/coordinator/dashboard',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("協調器儀表板查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="協調器儀表板查詢服務暫時不可用"
        )

# ==================== 批量操作 ====================

@router.post("/bulk-command", summary="批量執行分析師命令")
async def bulk_analyst_command(
    analyst_ids: List[str],
    command: AnalystCommand,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    對多個分析師批量執行命令
    """
    try:
        from ..services.analyst_coordinator import AnalystCoordinatorService
        coordinator_service = AnalystCoordinatorService()
        
        results = []
        
        for analyst_id in analyst_ids:
            try:
                result = await coordinator_service.execute_analyst_command(analyst_id, command)
                results.append(result)
            except Exception as e:
                results.append(AnalystCommandResult(
                    analyst_id=analyst_id,
                    command=command.command,
                    success=False,
                    message=f"執行失敗: {str(e)}",
                    execution_time=0.0,
                    executed_at=datetime.now()
                ))
        
        security_logger.info("批量分析師命令執行", extra={
            'admin_user_id': current_user.user_id,
            'analyst_ids': analyst_ids,
            'command': command.command,
            'total_analysts': len(analyst_ids),
            'success_count': len([r for r in results if r.success])
        })
        
        return {
            "message": "批量分析師命令執行完成",
            "total_analysts": len(analyst_ids),
            "results": results,
            "success_count": len([r for r in results if r.success]),
            "failed_count": len([r for r in results if not r.success])
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/analysts/bulk-command',
            'admin_user_id': current_user.user_id,
            'analyst_ids': analyst_ids,
            'command': command.dict()
        })
        
        api_logger.error("批量分析師命令執行失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="批量分析師命令執行服務暫時不可用"
        )