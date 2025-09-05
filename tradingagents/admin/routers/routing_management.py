#!/usr/bin/env python3
"""
路由管理API路由器
GPT-OSS整合任務1.3.3 - 路由策略配置界面API

提供完整的路由管理REST API接口
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List, Optional, Union
import logging

from ..models.routing_management import (
    StrategyTemplateRequest, StrategyTemplateResponse,
    RoutingPolicyRequest, RoutingPolicyResponse,
    ABTestVariantRequest, ABTestResponse,
    RoutingPerformanceResponse, RoutingDashboardResponse,
    RouteConfigurationSnapshot
)
from ..services.routing_management_service import RoutingManagementService
from ...auth.dependencies import get_current_admin_user
from ...utils.error_handler import handle_error
from ...routing.ai_task_router import AITaskRouter
from ...routing.routing_config import RoutingConfigManager

logger = logging.getLogger(__name__)
security = HTTPBearer()

# 創建路由器
router = APIRouter(
    prefix="/api/admin/routing",
    tags=["路由管理"],
    dependencies=[Depends(get_current_admin_user)]
)

# 全局服務實例
routing_service: Optional[RoutingManagementService] = None


def get_routing_service() -> RoutingManagementService:
    """獲取路由管理服務實例"""
    global routing_service
    if not routing_service:
        # 初始化服務實例
        routing_service = RoutingManagementService()
    return routing_service


# ==================== 儀表板接口 ====================

@router.get(
    "/dashboard",
    response_model=RoutingDashboardResponse,
    summary="獲取路由管理儀表板",
    description="獲取路由管理系統的完整儀表板數據，包括策略、性能指標、A/B測試等"
)
async def get_routing_dashboard(
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> RoutingDashboardResponse:
    """獲取路由管理儀表板數據"""
    try:
        dashboard_data = await service.get_dashboard_data()
        logger.info(f"Dashboard accessed by user: {current_user.get('username', 'unknown')}")
        return dashboard_data
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取儀表板數據"
        )


@router.get(
    "/performance",
    response_model=RoutingPerformanceResponse,
    summary="獲取路由性能指標",
    description="獲取指定時間段內的路由系統性能指標"
)
async def get_performance_metrics(
    period_hours: int = Query(24, ge=1, le=168, description="統計時間段（小時）"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> RoutingPerformanceResponse:
    """獲取路由性能指標"""
    try:
        metrics = await service.get_performance_metrics(period_hours)
        return metrics
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取性能指標"
        )


# ==================== 策略模板管理 ====================

@router.get(
    "/strategies",
    response_model=List[StrategyTemplateResponse],
    summary="獲取策略模板列表",
    description="獲取所有策略模板，可選擇包含非活動策略"
)
async def get_strategy_templates(
    include_inactive: bool = Query(False, description="是否包含非活動策略"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> List[StrategyTemplateResponse]:
    """獲取策略模板列表"""
    try:
        strategies = await service.get_strategy_templates(include_inactive)
        return strategies
    except Exception as e:
        logger.error(f"Failed to get strategy templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取策略模板列表"
        )


@router.post(
    "/strategies",
    response_model=StrategyTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="創建策略模板",
    description="創建新的路由策略模板"
)
async def create_strategy_template(
    request: StrategyTemplateRequest,
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> StrategyTemplateResponse:
    """創建策略模板"""
    try:
        success, result = await service.create_strategy_template(
            request,
            current_user.get("user_id", "unknown"),
            current_user.get("username", "unknown")
        )
        
        if success:
            logger.info(f"Strategy template created: {request.name} by {current_user.get('username')}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": result}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create strategy template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建策略模板失敗"
        )


@router.put(
    "/strategies/{strategy_name}",
    response_model=StrategyTemplateResponse,
    summary="更新策略模板",
    description="更新指定的路由策略模板"
)
async def update_strategy_template(
    strategy_name: str = Path(..., description="策略名稱"),
    request: StrategyTemplateRequest = Body(...),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> StrategyTemplateResponse:
    """更新策略模板"""
    try:
        success, result = await service.update_strategy_template(
            strategy_name,
            request,
            current_user.get("user_id", "unknown"),
            current_user.get("username", "unknown")
        )
        
        if success:
            logger.info(f"Strategy template updated: {strategy_name} by {current_user.get('username')}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": result}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update strategy template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新策略模板失敗"
        )


@router.delete(
    "/strategies/{strategy_name}",
    summary="刪除策略模板",
    description="刪除指定的路由策略模板"
)
async def delete_strategy_template(
    strategy_name: str = Path(..., description="策略名稱"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> Dict[str, str]:
    """刪除策略模板"""
    try:
        success, result = await service.delete_strategy_template(
            strategy_name,
            current_user.get("user_id", "unknown"),
            current_user.get("username", "unknown")
        )
        
        if success:
            logger.info(f"Strategy template deleted: {strategy_name} by {current_user.get('username')}")
            return {"message": result}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": result}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete strategy template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除策略模板失敗"
        )


# ==================== 路由策略管理 ====================

@router.get(
    "/policies",
    response_model=List[RoutingPolicyResponse],
    summary="獲取路由策略列表",
    description="獲取所有路由策略，可選擇包含非活動策略"
)
async def get_routing_policies(
    include_inactive: bool = Query(False, description="是否包含非活動策略"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> List[RoutingPolicyResponse]:
    """獲取路由策略列表"""
    try:
        policies = await service.get_routing_policies(include_inactive)
        return policies
    except Exception as e:
        logger.error(f"Failed to get routing policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取路由策略列表"
        )


@router.post(
    "/policies",
    response_model=RoutingPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="創建路由策略",
    description="創建新的路由策略配置"
)
async def create_routing_policy(
    request: RoutingPolicyRequest,
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> RoutingPolicyResponse:
    """創建路由策略"""
    try:
        success, result = await service.create_routing_policy(
            request,
            current_user.get("user_id", "unknown"),
            current_user.get("username", "unknown")
        )
        
        if success:
            logger.info(f"Routing policy created: {request.name} by {current_user.get('username')}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": result}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create routing policy: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建路由策略失敗"
        )


# ==================== A/B測試管理 ====================

@router.get(
    "/ab-tests",
    response_model=List[ABTestResponse],
    summary="獲取A/B測試列表",
    description="獲取所有A/B測試，包括活動和已完成的測試"
)
async def get_ab_tests(
    include_completed: bool = Query(True, description="是否包含已完成測試"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> List[ABTestResponse]:
    """獲取A/B測試列表"""
    try:
        tests = []
        
        # 活動測試
        for test_data in service.active_ab_tests.values():
            tests.append(ABTestResponse(**test_data))
        
        # 已完成測試
        if include_completed:
            for test_data in service.ab_test_results.values():
                tests.append(ABTestResponse(**test_data))
        
        return tests
    except Exception as e:
        logger.error(f"Failed to get A/B tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取A/B測試列表"
        )


@router.post(
    "/ab-tests",
    response_model=ABTestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="創建A/B測試",
    description="創建新的A/B測試實驗"
)
async def create_ab_test(
    request: ABTestVariantRequest,
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> ABTestResponse:
    """創建A/B測試"""
    try:
        success, result = await service.create_ab_test(
            request,
            current_user.get("user_id", "unknown"),
            current_user.get("username", "unknown")
        )
        
        if success:
            logger.info(f"A/B test created: {request.variant_name} by {current_user.get('username')}")
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": result}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create A/B test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建A/B測試失敗"
        )


@router.post(
    "/ab-tests/{test_id}/stop",
    summary="停止A/B測試",
    description="停止指定的A/B測試並收集結果"
)
async def stop_ab_test(
    test_id: str = Path(..., description="測試ID"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> Dict[str, str]:
    """停止A/B測試"""
    try:
        success, result = await service.stop_ab_test(
            test_id,
            current_user.get("user_id", "unknown"),
            current_user.get("username", "unknown")
        )
        
        if success:
            logger.info(f"A/B test stopped: {test_id} by {current_user.get('username')}")
            return {"message": result}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": result}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop A/B test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="停止A/B測試失敗"
        )


# ==================== 路由決策監控 ====================

@router.get(
    "/decisions/recent",
    summary="獲取最近路由決策",
    description="獲取最近的路由決策記錄，用於監控和分析"
)
async def get_recent_decisions(
    limit: int = Query(50, ge=1, le=200, description="返回記錄數量"),
    task_type: Optional[str] = Query(None, description="過濾任務類型"),
    provider: Optional[str] = Query(None, description="過濾提供商"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> List[Dict[str, Any]]:
    """獲取最近路由決策"""
    try:
        if service.ai_task_router:
            decisions = service.ai_task_router.get_decision_history(
                limit=limit,
                task_type=task_type,
                provider=provider
            )
            return decisions
        else:
            return []
    except Exception as e:
        logger.error(f"Failed to get recent decisions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取路由決策記錄"
        )


@router.get(
    "/statistics",
    summary="獲取路由統計信息",
    description="獲取詳細的路由系統統計信息"
)
async def get_routing_statistics(
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """獲取路由統計信息"""
    try:
        if service.ai_task_router:
            stats = service.ai_task_router.get_routing_statistics()
            return stats
        else:
            return {}
    except Exception as e:
        logger.error(f"Failed to get routing statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取路由統計信息"
        )


# ==================== 系統健康檢查 ====================

@router.get(
    "/health",
    summary="路由系統健康檢查",
    description="檢查路由系統的健康狀態和各組件狀態"
)
async def health_check(
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """路由系統健康檢查"""
    try:
        if service.ai_task_router:
            health_status = await service.ai_task_router.health_check()
            return health_status
        else:
            return {
                "overall_status": "degraded",
                "message": "AI Task Router not initialized",
                "timestamp": "2025-08-08T00:00:00Z"
            }
    except Exception as e:
        logger.error(f"Failed to perform health check: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法執行健康檢查"
        )


# ==================== 配置管理 ====================

@router.post(
    "/configuration/backup",
    summary="備份路由配置",
    description="創建當前路由配置的備份快照"
)
async def backup_configuration(
    description: str = Body(..., embed=True, description="備份描述"),
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> Dict[str, str]:
    """備份路由配置"""
    try:
        if service.routing_config_manager.current_profile:
            # 保存當前配置
            success = service.routing_config_manager.save_configuration_profile(
                service.routing_config_manager.current_profile
            )
            
            if success:
                logger.info(f"Configuration backed up by {current_user.get('username')}: {description}")
                return {"message": f"配置已備份: {description}"}
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="配置備份失敗"
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="沒有可備份的配置"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to backup configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置備份失敗"
        )


@router.get(
    "/configuration/summary",
    summary="獲取配置摘要",
    description="獲取當前路由配置的摘要信息"
)
async def get_configuration_summary(
    service: RoutingManagementService = Depends(get_routing_service),
    current_user: Dict[str, Any] = Depends(get_current_admin_user)
) -> Dict[str, Any]:
    """獲取配置摘要"""
    try:
        summary = service.routing_config_manager.get_configuration_summary()
        return summary
    except Exception as e:
        logger.error(f"Failed to get configuration summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="無法獲取配置摘要"
        )