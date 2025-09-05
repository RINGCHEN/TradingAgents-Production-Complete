#!/usr/bin/env python3
"""
用戶管理 API 端點
TradingAgents 系統的用戶 CRUD 操作和管理功能
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models.user import (
    User, UserCreate, UserUpdate, UserResponse, UserStats, QuotaInfo,
    MembershipTier, UserStatus, AuthProvider, MEMBERSHIP_QUOTAS,
    get_membership_benefits, upgrade_user_quotas
)
from ..database.database import get_db
from ..utils.auth import get_current_user, verify_admin_user
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])
security = HTTPBearer()

# 用戶 CRUD 操作
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    創建新用戶
    支持郵件註冊和 OAuth 註冊
    """
    try:
        # 檢查郵件是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="郵件地址已被使用"
            )
        
        # 檢查用戶名是否已存在
        if user_data.username:
            existing_username = db.query(User).filter(User.username == user_data.username).first()
            if existing_username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用戶名已被使用"
                )
        
        # 檢查 Google ID 是否已存在
        if user_data.google_id:
            existing_google = db.query(User).filter(User.google_id == user_data.google_id).first()
            if existing_google:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Google 帳號已被註冊"
                )
        
        # 創建用戶
        user = User(
            email=user_data.email,
            username=user_data.username,
            display_name=user_data.display_name,
            auth_provider=user_data.auth_provider,
            google_id=user_data.google_id,
            phone=user_data.phone,
            country=user_data.country,
            timezone=user_data.timezone,
            language=user_data.language,
            membership_tier=MembershipTier.FREE,
            status=UserStatus.ACTIVE
        )
        
        # 設置免費會員的配額
        benefits = get_membership_benefits(MembershipTier.FREE)
        user.daily_api_quota = benefits["daily_api_quota"]
        user.monthly_api_quota = benefits["monthly_api_quota"]
        
        # OAuth 用戶自動驗證郵件
        if user_data.auth_provider != AuthProvider.EMAIL:
            user.email_verified = True
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"用戶創建成功: {user.email} (ID: {user.id})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建用戶失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建用戶失敗"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    獲取當前用戶信息
    """
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新當前用戶信息
    """
    try:
        # 檢查用戶名是否已被其他用戶使用
        if user_update.username and user_update.username != current_user.username:
            existing_user = db.query(User).filter(
                and_(User.username == user_update.username, User.id != current_user.id)
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用戶名已被使用"
                )
        
        # 更新用戶信息
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"用戶信息更新成功: {current_user.email}")
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用戶信息失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶信息失敗"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    根據 ID 獲取用戶信息
    僅管理員和用戶本人可訪問
    """
    # 檢查權限
    if current_user.id != user_id and current_user.membership_tier != MembershipTier.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="沒有權限訪問此用戶信息"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用戶不存在"
        )
    
    return user

@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0, description="跳過的記錄數"),
    limit: int = Query(50, ge=1, le=100, description="返回的記錄數"),
    status_filter: Optional[UserStatus] = Query(None, description="狀態過濾"),
    tier_filter: Optional[MembershipTier] = Query(None, description="會員等級過濾"),
    search: Optional[str] = Query(None, description="搜索關鍵字"),
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    獲取用戶列表
    僅管理員可訪問
    """
    try:
        query = db.query(User)
        
        # 應用過濾條件
        if status_filter:
            query = query.filter(User.status == status_filter)
        
        if tier_filter:
            query = query.filter(User.membership_tier == tier_filter)
        
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.email.ilike(search_pattern),
                    User.username.ilike(search_pattern),
                    User.display_name.ilike(search_pattern)
                )
            )
        
        # 排序和分頁
        users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
        
        return users
        
    except Exception as e:
        logger.error(f"獲取用戶列表失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶列表失敗"
        )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新指定用戶信息
    僅管理員可操作
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        # 更新用戶信息
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"管理員更新用戶信息: {user.email} (操作者: {current_user.email})")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用戶信息失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用戶信息失敗"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    刪除用戶（軟刪除）
    僅管理員可操作
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        # 軟刪除
        user.status = UserStatus.DELETED
        user.deleted_at = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"用戶已刪除: {user.email} (操作者: {current_user.email})")
        return {"message": "用戶已刪除"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除用戶失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除用戶失敗"
        )

# 會員等級管理
@router.post("/{user_id}/upgrade-tier")
async def upgrade_user_tier(
    user_id: int,
    new_tier: MembershipTier,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    升級/降級用戶會員等級
    僅管理員可操作
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        old_tier = user.membership_tier
        
        # 升級用戶等級和配額
        upgrade_user_quotas(user, new_tier)
        user.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"用戶等級變更: {user.email} {old_tier} -> {new_tier} (操作者: {current_user.email})")
        
        return {
            "message": f"用戶等級已從 {old_tier} 變更為 {new_tier}",
            "user": user,
            "old_tier": old_tier,
            "new_tier": new_tier
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"升級用戶等級失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="升級用戶等級失敗"
        )

# 配額管理
@router.get("/me/quota", response_model=QuotaInfo)
async def get_user_quota(
    current_user: User = Depends(get_current_user)
):
    """
    獲取用戶 API 配額信息
    """
    try:
        # 檢查是否需要重置每日配額
        now = datetime.utcnow()
        if current_user.last_api_reset and (now - current_user.last_api_reset).days >= 1:
            current_user.reset_daily_quota()
        
        next_reset = current_user.last_api_reset + timedelta(days=1) if current_user.last_api_reset else now + timedelta(days=1)
        
        quota_info = QuotaInfo(
            daily_quota=current_user.daily_api_quota,
            daily_used=current_user.api_calls_today,
            daily_remaining=current_user.api_quota_remaining_today,
            monthly_quota=current_user.monthly_api_quota,
            monthly_used=current_user.api_calls_month,
            monthly_remaining=current_user.api_quota_remaining_month,
            can_make_call=current_user.can_make_api_call(),
            next_reset=next_reset
        )
        
        return quota_info
        
    except Exception as e:
        logger.error(f"獲取用戶配額失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取配額信息失敗"
        )

@router.post("/me/api-call")
async def record_api_call(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    記錄 API 調用
    增加用戶的 API 使用次數
    """
    try:
        # 檢查配額
        if not current_user.can_make_api_call():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="API 配額已用完"
            )
        
        # 記錄使用
        current_user.increment_api_usage()
        current_user.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "API 調用已記錄",
            "remaining_today": current_user.api_quota_remaining_today,
            "remaining_month": current_user.api_quota_remaining_month
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"記錄 API 調用失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="記錄 API 調用失敗"
        )

@router.get("/me/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user)
):
    """
    獲取用戶統計信息
    """
    try:
        stats = UserStats(
            user_id=current_user.id,
            total_analyses=current_user.total_analyses,
            api_calls_today=current_user.api_calls_today,
            api_calls_month=current_user.api_calls_month,
            daily_quota_remaining=current_user.api_quota_remaining_today,
            monthly_quota_remaining=current_user.api_quota_remaining_month,
            membership_tier=current_user.membership_tier,
            member_since=current_user.created_at,
            last_active=current_user.last_login
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"獲取用戶統計失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取統計信息失敗"
        )

# 用戶狀態管理
@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    暫停用戶
    僅管理員可操作
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        user.status = UserStatus.SUSPENDED
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"用戶已暫停: {user.email} 原因: {reason} (操作者: {current_user.email})")
        
        return {
            "message": "用戶已暫停",
            "reason": reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暫停用戶失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="暫停用戶失敗"
        )

@router.post("/{user_id}/reactivate")
async def reactivate_user(
    user_id: int,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    重新激活用戶
    僅管理員可操作
    """
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        user.status = UserStatus.ACTIVE
        user.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"用戶已重新激活: {user.email} (操作者: {current_user.email})")
        
        return {"message": "用戶已重新激活"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重新激活用戶失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重新激活用戶失敗"
        )