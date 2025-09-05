#!/usr/bin/env python3
"""
服務協調器路由器 (Service Coordinator Router)
天工 (TianGong) - 服務協調器 API 端點

此模組提供完整的服務協調器 API 端點，包含：
1. 服務管理和註冊
2. 任務協調和調度
3. 工作流管理
4. 服務監控和健康檢查
5. 協調器配置管理
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..models.service_coordinator import (
    ServiceInfo, ServiceRegistry, ServiceCommand, ServiceCommandResult,
    TaskDefinition, TaskExecution, WorkflowDefinition, WorkflowExecution,
    CoordinatorConfiguration, CoordinatorStatistics, CoordinatorHealth,
    ServiceQuery, TaskQuery, WorkflowQuery, CoordinatorDashboard,
    ServiceStatus, ServiceType, TaskStatus, TaskPriority, CoordinationStrategy
)
from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("service_coordinator")
security_logger = get_security_logger("service_coordinator")

# 創建路由器
router = APIRouter(prefix="/coordinator", tags=["服務協調器"])

# ==================== 服務管理 ====================

@router.get("/services", response_model=ServiceRegistry, summary="獲取服務註冊表")
async def get_service_registry(
    query: ServiceQuery = Depends(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取服務註冊表，包含所有註冊的服務信息
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        registry = await coordinator_service.get_service_registry(query)
        
        api_logger.info("服務註冊表查詢", extra={
            'admin_user_id': current_user.user_id,
            'query_params': query.dict(),
            'total_services': registry.total_services
        })
        
        return registry
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/coordinator/services',
            'admin_user_id': current_user.user_id,
            'query_params': query.dict()
        })
        
        api_logger.error("服務註冊表查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服務註冊表查詢服務暫時不可用"
        )

@router.get("/services/{service_id}", response_model=ServiceInfo, summary="獲取服務詳情")
async def get_service_info(
    service_id: str,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定服務的詳細信息
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        service_info = await coordinator_service.get_service_info(service_id)
        
        if not service_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="服務不存在"
            )
        
        api_logger.info("服務詳情查詢", extra={
            'admin_user_id': current_user.user_id,
            'service_id': service_id,
            'service_status': service_info.status
        })
        
        return service_info
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/coordinator/services/{service_id}',
            'admin_user_id': current_user.user_id,
            'service_id': service_id
        })
        
        api_logger.error("服務詳情查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'service_id': service_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服務詳情查詢服務暫時不可用"
        )

@router.post("/services/{service_id}/command", response_model=ServiceCommandResult, summary="執行服務命令")
async def execute_service_command(
    service_id: str,
    command: ServiceCommand,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    對指定服務執行命令（啟動、停止、重啟等）
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        # 驗證服務存在
        service_info = await coordinator_service.get_service_info(service_id)
        if not service_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="服務不存在"
            )
        
        # 執行命令
        result = await coordinator_service.execute_service_command(service_id, command)
        
        security_logger.info("服務命令執行", extra={
            'admin_user_id': current_user.user_id,
            'service_id': service_id,
            'command': command.command,
            'success': result.success,
            'execution_time': result.execution_time
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/coordinator/services/{service_id}/command',
            'admin_user_id': current_user.user_id,
            'service_id': service_id,
            'command': command.dict()
        })
        
        api_logger.error("服務命令執行失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'service_id': service_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服務命令執行服務暫時不可用"
        )

@router.post("/services/health-check", summary="執行服務健康檢查")
async def run_services_health_check(
    service_ids: Optional[List[str]] = None,
    current_user: UserContext = Depends(require_admin_access())
):
    """
    執行服務健康檢查
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        results = await coordinator_service.run_services_health_check(service_ids)
        
        security_logger.info("服務健康檢查執行", extra={
            'admin_user_id': current_user.user_id,
            'service_ids': service_ids,
            'check_count': len(results)
        })
        
        return {
            "message": "服務健康檢查完成",
            "results": results,
            "total_checked": len(results),
            "healthy_services": len([r for r in results if r.get("status") == "healthy"])
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/coordinator/services/health-check',
            'admin_user_id': current_user.user_id,
            'service_ids': service_ids
        })
        
        api_logger.error("服務健康檢查失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服務健康檢查服務暫時不可用"
        )

# ==================== 任務協調 ====================

@router.get("/tasks", response_model=List[TaskExecution], summary="獲取任務列表")
async def get_tasks(
    query: TaskQuery = Depends(),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取任務執行列表
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        tasks = await coordinator_service.get_tasks(query)
        
        api_logger.info("任務列表查詢", extra={
            'admin_user_id': current_user.user_id,
            'query_params': query.dict(),
            'task_count': len(tasks)
        })
        
        return tasks
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/coordinator/tasks',
            'admin_user_id': current_user.user_id,
            'query_params': query.dict()
        })
        
        api_logger.error("任務列表查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任務列表查詢服務暫時不可用"
        )

@router.get("/statistics", response_model=CoordinatorStatistics, summary="獲取協調器統計")
async def get_coordinator_statistics(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取服務協調器統計信息
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        statistics = await coordinator_service.get_coordinator_statistics()
        
        api_logger.info("協調器統計查詢", extra={
            'admin_user_id': current_user.user_id,
            'total_services': statistics.total_services,
            'total_tasks': statistics.total_tasks
        })
        
        return statistics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/coordinator/statistics',
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

@router.get("/health", response_model=CoordinatorHealth, summary="獲取協調器健康狀態")
async def get_coordinator_health(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取服務協調器健康狀態
    """
    try:
        from ..services.service_coordinator_service import ServiceCoordinatorService
        coordinator_service = ServiceCoordinatorService()
        
        health = await coordinator_service.get_coordinator_health()
        
        api_logger.info("協調器健康檢查", extra={
            'admin_user_id': current_user.user_id,
            'overall_status': health.overall_status
        })
        
        return health
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/coordinator/health',
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