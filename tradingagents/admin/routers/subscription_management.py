"""
會員訂閱管理路由
提供完整的會員訂閱管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..services.subscription_management_service import SubscriptionManagementService
from ..models.subscription_management import (
    SubscriptionPlan, 
    UserSubscription, 
    SubscriptionStats,
    CreateSubscriptionPlanRequest,
    UpdateSubscriptionPlanRequest,
    SubscriptionAnalytics
)
from ..middleware.auth_middleware import require_admin_permission

router = APIRouter(prefix="/admin/subscriptions", tags=["subscription-management"])
logger = logging.getLogger(__name__)

@router.get("/plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans(
    active_only: bool = Query(False, description="只顯示啟用的方案"),
    service: SubscriptionManagementService = Depends()
):
    """獲取所有訂閱方案"""
    try:
        plans = await service.get_subscription_plans(active_only=active_only)
        return plans
    except Exception as e:
        logger.error(f"獲取訂閱方案失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取訂閱方案失敗")

@router.post("/plans", response_model=SubscriptionPlan)
async def create_subscription_plan(
    plan_data: CreateSubscriptionPlanRequest,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """創建新的訂閱方案"""
    try:
        plan = await service.create_subscription_plan(plan_data)
        logger.info(f"管理員 {current_user['username']} 創建了訂閱方案: {plan.name}")
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"創建訂閱方案失敗: {e}")
        raise HTTPException(status_code=500, detail="創建訂閱方案失敗")

@router.put("/plans/{plan_id}", response_model=SubscriptionPlan)
async def update_subscription_plan(
    plan_id: str,
    plan_data: UpdateSubscriptionPlanRequest,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """更新訂閱方案"""
    try:
        plan = await service.update_subscription_plan(plan_id, plan_data)
        logger.info(f"管理員 {current_user['username']} 更新了訂閱方案: {plan_id}")
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新訂閱方案失敗: {e}")
        raise HTTPException(status_code=500, detail="更新訂閱方案失敗")

@router.delete("/plans/{plan_id}")
async def delete_subscription_plan(
    plan_id: str,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """刪除訂閱方案"""
    try:
        await service.delete_subscription_plan(plan_id)
        logger.info(f"管理員 {current_user['username']} 刪除了訂閱方案: {plan_id}")
        return {"message": "訂閱方案已刪除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"刪除訂閱方案失敗: {e}")
        raise HTTPException(status_code=500, detail="刪除訂閱方案失敗")

@router.get("/users", response_model=List[UserSubscription])
async def get_user_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="訂閱狀態篩選"),
    plan_id: Optional[str] = Query(None, description="方案ID篩選"),
    search: Optional[str] = Query(None, description="搜尋用戶"),
    service: SubscriptionManagementService = Depends()
):
    """獲取用戶訂閱列表"""
    try:
        subscriptions = await service.get_user_subscriptions(
            page=page,
            limit=limit,
            status=status,
            plan_id=plan_id,
            search=search
        )
        return subscriptions
    except Exception as e:
        logger.error(f"獲取用戶訂閱失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取用戶訂閱失敗")

@router.get("/users/{user_id}/subscription", response_model=UserSubscription)
async def get_user_subscription(
    user_id: str,
    service: SubscriptionManagementService = Depends()
):
    """獲取特定用戶的訂閱信息"""
    try:
        subscription = await service.get_user_subscription(user_id)
        if not subscription:
            raise HTTPException(status_code=404, detail="用戶訂閱不存在")
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶訂閱失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取用戶訂閱失敗")

@router.post("/users/{user_id}/subscription")
async def create_user_subscription(
    user_id: str,
    plan_id: str,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """為用戶創建訂閱"""
    try:
        subscription = await service.create_user_subscription(user_id, plan_id)
        logger.info(f"管理員 {current_user['username']} 為用戶 {user_id} 創建了訂閱")
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"創建用戶訂閱失敗: {e}")
        raise HTTPException(status_code=500, detail="創建用戶訂閱失敗")

@router.put("/users/{user_id}/subscription/cancel")
async def cancel_user_subscription(
    user_id: str,
    reason: Optional[str] = None,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """取消用戶訂閱"""
    try:
        await service.cancel_user_subscription(user_id, reason)
        logger.info(f"管理員 {current_user['username']} 取消了用戶 {user_id} 的訂閱")
        return {"message": "訂閱已取消"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消用戶訂閱失敗: {e}")
        raise HTTPException(status_code=500, detail="取消用戶訂閱失敗")

@router.put("/users/{user_id}/subscription/renew")
async def renew_user_subscription(
    user_id: str,
    months: int = 1,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """續費用戶訂閱"""
    try:
        subscription = await service.renew_user_subscription(user_id, months)
        logger.info(f"管理員 {current_user['username']} 為用戶 {user_id} 續費了 {months} 個月")
        return subscription
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"續費用戶訂閱失敗: {e}")
        raise HTTPException(status_code=500, detail="續費用戶訂閱失敗")

@router.get("/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    service: SubscriptionManagementService = Depends()
):
    """獲取訂閱統計數據"""
    try:
        stats = await service.get_subscription_stats()
        return stats
    except Exception as e:
        logger.error(f"獲取訂閱統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取訂閱統計失敗")

@router.get("/analytics", response_model=SubscriptionAnalytics)
async def get_subscription_analytics(
    days: int = Query(30, ge=1, le=365, description="分析天數"),
    service: SubscriptionManagementService = Depends()
):
    """獲取訂閱分析數據"""
    try:
        analytics = await service.get_subscription_analytics(days)
        return analytics
    except Exception as e:
        logger.error(f"獲取訂閱分析失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取訂閱分析失敗")

@router.get("/revenue")
async def get_revenue_report(
    start_date: Optional[str] = Query(None, description="開始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="結束日期 YYYY-MM-DD"),
    service: SubscriptionManagementService = Depends()
):
    """獲取收入報告"""
    try:
        report = await service.get_revenue_report(start_date, end_date)
        return report
    except Exception as e:
        logger.error(f"獲取收入報告失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取收入報告失敗")

@router.post("/bulk-operations")
async def bulk_subscription_operations(
    operation: str,
    user_ids: List[str],
    data: Optional[Dict[str, Any]] = None,
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """批量訂閱操作"""
    try:
        result = await service.bulk_subscription_operations(operation, user_ids, data)
        logger.info(f"管理員 {current_user['username']} 執行了批量操作: {operation}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"批量操作失敗: {e}")
        raise HTTPException(status_code=500, detail="批量操作失敗")

@router.get("/expiring")
async def get_expiring_subscriptions(
    days: int = Query(7, ge=1, le=30, description="即將到期天數"),
    service: SubscriptionManagementService = Depends()
):
    """獲取即將到期的訂閱"""
    try:
        subscriptions = await service.get_expiring_subscriptions(days)
        return subscriptions
    except Exception as e:
        logger.error(f"獲取即將到期訂閱失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取即將到期訂閱失敗")

@router.post("/notifications/renewal-reminder")
async def send_renewal_reminders(
    days_before: int = Query(7, ge=1, le=30, description="提前提醒天數"),
    service: SubscriptionManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("subscription_management"))
):
    """發送續費提醒"""
    try:
        result = await service.send_renewal_reminders(days_before)
        logger.info(f"管理員 {current_user['username']} 發送了續費提醒")
        return result
    except Exception as e:
        logger.error(f"發送續費提醒失敗: {e}")
        raise HTTPException(status_code=500, detail="發送續費提醒失敗")