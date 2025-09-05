#!/usr/bin/env python3
"""
訂閱管理 API 端點
TradingAgents 系統的訂閱和續費管理
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from ..models.subscription import (
    Subscription, SubscriptionHistory, TrialPeriod,
    SubscriptionCreate, SubscriptionUpdate, SubscriptionResponse,
    TrialPeriodResponse, SubscriptionStats, RenewalReminder,
    SubscriptionStatus, BillingCycle, RenewalType, TierType,
    calculate_subscription_price, get_next_billing_date, create_trial_subscription
)
from ..models.user import User
from ..database.database import get_db
from ..utils.auth import get_current_user, verify_admin_user
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

# 訂閱 CRUD 操作
@router.post("/", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    創建訂閱
    僅管理員可操作
    """
    try:
        # 檢查用戶是否存在
        user = db.query(User).filter(User.id == subscription_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        # 檢查用戶是否已有活躍訂閱
        existing_subscription = db.query(Subscription).filter(
            and_(
                Subscription.user_id == subscription_data.user_id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
            )
        ).first()
        
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用戶已有活躍訂閱"
            )
        
        # 計算訂閱價格
        pricing = calculate_subscription_price(
            subscription_data.tier_type,
            subscription_data.billing_cycle,
            subscription_data.promo_code
        )
        
        # 設定時間
        start_date = datetime.utcnow()
        end_date = get_next_billing_date(start_date, subscription_data.billing_cycle)
        
        # 試用期設定
        trial_end_date = None
        if subscription_data.is_trial and subscription_data.trial_days > 0:
            trial_end_date = start_date + timedelta(days=subscription_data.trial_days)
        
        # 獲取等級配額
        from ..models.membership import get_tier_config
        tier_config = get_tier_config(subscription_data.tier_type)
        
        # 創建訂閱
        subscription = Subscription(
            user_id=subscription_data.user_id,
            tier_type=subscription_data.tier_type,
            billing_cycle=subscription_data.billing_cycle,
            status=SubscriptionStatus.TRIAL if subscription_data.is_trial else SubscriptionStatus.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            trial_end_date=trial_end_date,
            auto_renewal=subscription_data.auto_renewal,
            original_price=pricing["original_price"],
            discount_amount=pricing["discount_amount"],
            final_price=pricing["final_price"],
            promo_code=subscription_data.promo_code,
            is_trial=subscription_data.is_trial,
            trial_days=subscription_data.trial_days,
            daily_api_quota=tier_config["daily_api_quota"],
            monthly_api_quota=tier_config["monthly_api_quota"],
            features=tier_config["features"]
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        # 更新用戶會員等級
        user.membership_tier = subscription_data.tier_type
        user.daily_api_quota = tier_config["daily_api_quota"]
        user.monthly_api_quota = tier_config["monthly_api_quota"]
        user.updated_at = datetime.utcnow()
        
        # 記錄訂閱歷史
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            user_id=user.id,
            action="created",
            to_tier=subscription_data.tier_type,
            to_status=subscription.status,
            reason=f"管理員創建訂閱 - {subscription_data.tier_type}"
        )
        db.add(history)
        
        db.commit()
        
        logger.info(f"訂閱創建成功: 用戶 {user.email} 訂閱 {subscription_data.tier_type} (操作者: {current_user.email})")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建訂閱失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建訂閱失敗"
        )

@router.get("/me", response_model=Optional[SubscriptionResponse])
async def get_current_user_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取當前用戶的訂閱信息
    """
    try:
        subscription = db.query(Subscription).filter(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.status.in_([
                    SubscriptionStatus.ACTIVE,
                    SubscriptionStatus.TRIAL,
                    SubscriptionStatus.EXPIRED
                ])
            )
        ).order_by(desc(Subscription.created_at)).first()
        
        return subscription
        
    except Exception as e:
        logger.error(f"獲取用戶訂閱失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訂閱信息失敗"
        )

@router.get("/", response_model=List[SubscriptionResponse])
async def list_subscriptions(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(50, ge=1, le=100, description="返回的記錄數"),
    status_filter: Optional[SubscriptionStatus] = Query(None, description="狀態過濾"),
    tier_filter: Optional[TierType] = Query(None, description="等級過濾"),
    user_id: Optional[int] = Query(None, description="用戶ID過濾"),
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    獲取訂閱列表
    僅管理員可訪問
    """
    try:
        query = db.query(Subscription)
        
        # 應用過濾條件
        if status_filter:
            query = query.filter(Subscription.status == status_filter)
        
        if tier_filter:
            query = query.filter(Subscription.tier_type == tier_filter)
        
        if user_id:
            query = query.filter(Subscription.user_id == user_id)
        
        # 排序和分頁
        subscriptions = query.order_by(desc(Subscription.created_at)).offset(skip).limit(limit).all()
        
        return subscriptions
        
    except Exception as e:
        logger.error(f"獲取訂閱列表失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訂閱列表失敗"
        )

@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取指定訂閱詳情
    用戶只能查看自己的訂閱，管理員可查看所有
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="訂閱不存在"
            )
        
        # 權限檢查
        if (subscription.user_id != current_user.id and 
            current_user.membership_tier.value != "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限訪問此訂閱"
            )
        
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取訂閱詳情失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訂閱詳情失敗"
        )

@router.put("/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    subscription_update: SubscriptionUpdate,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新訂閱信息
    僅管理員可操作
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="訂閱不存在"
            )
        
        old_tier = subscription.tier_type
        
        # 更新訂閱信息
        update_data = subscription_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscription, field, value)
        
        # 如果等級變更，重新計算配額
        if subscription_update.tier_type and subscription_update.tier_type != old_tier:
            from ..models.membership import get_tier_config
            tier_config = get_tier_config(subscription_update.tier_type)
            subscription.daily_api_quota = tier_config["daily_api_quota"]
            subscription.monthly_api_quota = tier_config["monthly_api_quota"]
            subscription.features = tier_config["features"]
            
            # 更新用戶等級
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                user.membership_tier = subscription_update.tier_type
                user.daily_api_quota = tier_config["daily_api_quota"]
                user.monthly_api_quota = tier_config["monthly_api_quota"]
                user.updated_at = datetime.utcnow()
        
        subscription.updated_at = datetime.utcnow()
        
        # 記錄變更歷史
        if subscription_update.tier_type and subscription_update.tier_type != old_tier:
            history = SubscriptionHistory(
                subscription_id=subscription.id,
                user_id=subscription.user_id,
                action="upgraded" if subscription_update.tier_type.value > old_tier.value else "downgraded",
                from_tier=old_tier,
                to_tier=subscription_update.tier_type,
                reason=f"管理員變更等級: {old_tier} -> {subscription_update.tier_type}"
            )
            db.add(history)
        
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"訂閱更新成功: ID {subscription_id} (操作者: {current_user.email})")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新訂閱失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新訂閱失敗"
        )

# 訂閱操作
@router.post("/{subscription_id}/cancel")
async def cancel_subscription(
    subscription_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消訂閱
    用戶可取消自己的訂閱，管理員可取消任何訂閱
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="訂閱不存在"
            )
        
        # 權限檢查
        is_admin = current_user.membership_tier.value == "ADMIN"
        if subscription.user_id != current_user.id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限取消此訂閱"
            )
        
        if subscription.status == SubscriptionStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="訂閱已被取消"
            )
        
        # 取消訂閱
        subscription.cancel_subscription(reason=reason, by_user=not is_admin)
        
        # 記錄取消歷史
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            action="canceled",
            from_status=SubscriptionStatus.ACTIVE,
            to_status=SubscriptionStatus.CANCELED,
            reason=reason or "用戶主動取消"
        )
        db.add(history)
        
        db.commit()
        
        logger.info(f"訂閱已取消: ID {subscription_id} (操作者: {current_user.email})")
        
        return {
            "message": "訂閱已取消",
            "subscription_id": subscription_id,
            "canceled_at": subscription.canceled_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消訂閱失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="取消訂閱失敗"
        )

@router.post("/{subscription_id}/reactivate")
async def reactivate_subscription(
    subscription_id: int,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    重新激活訂閱
    僅管理員可操作
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="訂閱不存在"
            )
        
        if subscription.status != SubscriptionStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="只能重新激活已取消的訂閱"
            )
        
        # 重新激活
        success = subscription.reactivate_subscription()
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="訂閱已過期，無法重新激活"
            )
        
        # 記錄激活歷史
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            action="reactivated",
            from_status=SubscriptionStatus.CANCELED,
            to_status=SubscriptionStatus.ACTIVE,
            reason="管理員重新激活"
        )
        db.add(history)
        
        db.commit()
        
        logger.info(f"訂閱已重新激活: ID {subscription_id} (操作者: {current_user.email})")
        
        return {
            "message": "訂閱已重新激活",
            "subscription_id": subscription_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新激活訂閱失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新激活訂閱失敗"
        )

@router.post("/{subscription_id}/extend")
async def extend_subscription(
    subscription_id: int,
    days: int = Query(..., ge=1, le=365, description="延長天數"),
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    延長訂閱期限
    僅管理員可操作
    """
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="訂閱不存在"
            )
        
        old_end_date = subscription.end_date
        subscription.extend_subscription(days)
        
        # 記錄延期歷史
        history = SubscriptionHistory(
            subscription_id=subscription.id,
            user_id=subscription.user_id,
            action="extended",
            reason=f"管理員延長 {days} 天",
            metadata={"old_end_date": old_end_date.isoformat(), "new_end_date": subscription.end_date.isoformat()}
        )
        db.add(history)
        
        db.commit()
        
        logger.info(f"訂閱已延長: ID {subscription_id} 延長 {days} 天 (操作者: {current_user.email})")
        
        return {
            "message": f"訂閱已延長 {days} 天",
            "subscription_id": subscription_id,
            "new_end_date": subscription.end_date
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"延長訂閱失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="延長訂閱失敗"
        )

# 試用期管理
@router.post("/trial/start")
async def start_trial(
    tier_type: TierType,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    開始試用期
    用戶可為自己開始試用期
    """
    try:
        # 檢查是否已有試用記錄
        existing_trial = db.query(TrialPeriod).filter(TrialPeriod.user_id == current_user.id).first()
        if existing_trial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已使用過試用期"
            )
        
        # 檢查是否已有訂閱
        existing_subscription = db.query(Subscription).filter(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
            )
        ).first()
        
        if existing_subscription:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="您已有活躍訂閱"
            )
        
        # 創建試用訂閱
        trial_data = create_trial_subscription(current_user.id, tier_type)
        
        subscription = Subscription(**trial_data)
        db.add(subscription)
        
        # 創建試用期記錄
        trial_period = TrialPeriod(
            user_id=current_user.id,
            tier_type=tier_type,
            trial_days=trial_data["trial_days"],
            start_date=trial_data["start_date"],
            end_date=trial_data["trial_end_date"]
        )
        db.add(trial_period)
        
        # 更新用戶等級
        current_user.membership_tier = tier_type
        current_user.daily_api_quota = trial_data["daily_api_quota"]
        current_user.monthly_api_quota = trial_data["monthly_api_quota"]
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"試用期開始: 用戶 {current_user.email} 開始 {tier_type} 試用")
        
        return {
            "message": "試用期已開始",
            "subscription": subscription,
            "trial_days": trial_data["trial_days"],
            "trial_end_date": trial_data["trial_end_date"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"開始試用期失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="開始試用期失敗"
        )

@router.get("/trial/me", response_model=Optional[TrialPeriodResponse])
async def get_my_trial(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取當前用戶的試用期信息
    """
    try:
        trial = db.query(TrialPeriod).filter(TrialPeriod.user_id == current_user.id).first()
        return trial
        
    except Exception as e:
        logger.error(f"獲取試用期信息失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取試用期信息失敗"
        )

# 續費管理
@router.get("/renewal-reminders", response_model=List[RenewalReminder])
async def get_renewal_reminders(
    days_ahead: int = Query(7, ge=1, le=30, description="提前天數"),
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    獲取續費提醒列表
    僅管理員可訪問
    """
    try:
        # 查找即將到期的訂閱
        cutoff_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        subscriptions = db.query(Subscription).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.end_date <= cutoff_date,
                Subscription.auto_renewal == True
            )
        ).all()
        
        reminders = []
        for sub in subscriptions:
            days_until_expiry = (sub.end_date - datetime.utcnow()).days
            if days_until_expiry >= 0:
                reminders.append(RenewalReminder(
                    subscription_id=sub.id,
                    user_id=sub.user_id,
                    tier_type=sub.tier_type,
                    end_date=sub.end_date,
                    days_until_expiry=days_until_expiry,
                    renewal_price=sub.final_price,
                    auto_renewal_enabled=sub.auto_renewal
                ))
        
        return reminders
        
    except Exception as e:
        logger.error(f"獲取續費提醒失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取續費提醒失敗"
        )

# 訂閱統計
@router.get("/stats", response_model=SubscriptionStats)
async def get_subscription_stats(
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    獲取訂閱統計信息
    僅管理員可訪問
    """
    try:
        # 總訂閱數
        total_subscriptions = db.query(Subscription).count()
        
        # 活躍訂閱數
        active_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).count()
        
        # 試用訂閱數
        trial_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.TRIAL
        ).count()
        
        # 過期訂閱數
        expired_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.EXPIRED
        ).count()
        
        # 取消訂閱數
        canceled_subscriptions = db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.CANCELED
        ).count()
        
        # 本月收入
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_this_month = db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_of_month,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED])
            )
        ).with_entities(Subscription.final_price).all()
        
        revenue_this_month = sum([r[0] for r in revenue_this_month])
        
        # 本年收入
        start_of_year = datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_this_year = db.query(Subscription).filter(
            and_(
                Subscription.created_at >= start_of_year,
                Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.EXPIRED])
            )
        ).with_entities(Subscription.final_price).all()
        
        revenue_this_year = sum([r[0] for r in revenue_this_year])
        
        # 計算流失率和轉換率
        churn_rate = canceled_subscriptions / max(total_subscriptions, 1) * 100
        
        converted_trials = db.query(TrialPeriod).filter(TrialPeriod.is_converted == True).count()
        total_trials = db.query(TrialPeriod).count()
        conversion_rate = converted_trials / max(total_trials, 1) * 100
        
        stats = SubscriptionStats(
            total_subscriptions=total_subscriptions,
            active_subscriptions=active_subscriptions,
            trial_subscriptions=trial_subscriptions,
            expired_subscriptions=expired_subscriptions,
            canceled_subscriptions=canceled_subscriptions,
            revenue_this_month=revenue_this_month,
            revenue_this_year=revenue_this_year,
            churn_rate=churn_rate,
            conversion_rate=conversion_rate
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"獲取訂閱統計失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訂閱統計失敗"
        )

@router.get("/health")
async def subscription_health_check():
    """
    訂閱系統健康檢查
    """
    try:
        return {
            "service": "subscription",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": [
                "subscription_management",
                "trial_periods",
                "auto_renewal",
                "pricing_calculation",
                "subscription_analytics"
            ]
        }
        
    except Exception as e:
        logger.error(f"訂閱系統健康檢查失敗: {str(e)}")
        return {
            "service": "subscription",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }