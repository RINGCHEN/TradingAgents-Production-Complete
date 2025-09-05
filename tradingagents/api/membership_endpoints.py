#!/usr/bin/env python3
"""
會員等級管理 API 端點
TradingAgents 系統的會員等級配置和權益管理
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.membership import (
    MembershipTier, TierFeature, TierUpgradeRule,
    MembershipTierCreate, MembershipTierUpdate, MembershipTierResponse,
    TierFeatureResponse, TierComparison, UpgradeRecommendation,
    TierType, FeatureType, DEFAULT_TIER_CONFIGS,
    get_tier_config, get_tier_comparison, recommend_tier_upgrade
)
from ..models.user import User
from ..database.database import get_db
from ..utils.auth import get_current_user, verify_admin_user
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/membership", tags=["membership"])

# 會員等級 CRUD 操作
@router.post("/tiers", response_model=MembershipTierResponse, status_code=status.HTTP_201_CREATED)
async def create_membership_tier(
    tier_data: MembershipTierCreate,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    創建會員等級
    僅管理員可操作
    """
    try:
        # 檢查等級類型是否已存在
        existing_tier = db.query(MembershipTier).filter(
            MembershipTier.tier_type == tier_data.tier_type
        ).first()
        
        if existing_tier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"會員等級 {tier_data.tier_type} 已存在"
            )
        
        # 創建會員等級
        tier = MembershipTier(
            tier_type=tier_data.tier_type,
            name=tier_data.name,
            description=tier_data.description,
            monthly_price=tier_data.monthly_price,
            quarterly_price=tier_data.quarterly_price,
            yearly_price=tier_data.yearly_price,
            daily_api_quota=tier_data.daily_api_quota,
            monthly_api_quota=tier_data.monthly_api_quota,
            max_concurrent_analyses=tier_data.max_concurrent_analyses,
            features=tier_data.features,
            export_formats=tier_data.export_formats
        )
        
        db.add(tier)
        db.commit()
        db.refresh(tier)
        
        logger.info(f"會員等級創建成功: {tier.tier_type} (操作者: {current_user.email})")
        return tier
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建會員等級失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建會員等級失敗"
        )

@router.get("/tiers", response_model=List[MembershipTierResponse])
async def list_membership_tiers(
    active_only: bool = Query(True, description="僅顯示活躍等級"),
    db: Session = Depends(get_db)
):
    """
    獲取會員等級列表
    """
    try:
        query = db.query(MembershipTier)
        
        if active_only:
            query = query.filter(MembershipTier.is_active == True)
        
        tiers = query.order_by(MembershipTier.sort_order).all()
        return tiers
        
    except Exception as e:
        logger.error(f"獲取會員等級列表失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取會員等級列表失敗"
        )

@router.get("/tiers/{tier_type}", response_model=MembershipTierResponse)
async def get_membership_tier(
    tier_type: TierType,
    db: Session = Depends(get_db)
):
    """
    獲取指定會員等級詳情
    """
    try:
        tier = db.query(MembershipTier).filter(
            MembershipTier.tier_type == tier_type
        ).first()
        
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="會員等級不存在"
            )
        
        return tier
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取會員等級失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取會員等級失敗"
        )

@router.put("/tiers/{tier_type}", response_model=MembershipTierResponse)
async def update_membership_tier(
    tier_type: TierType,
    tier_update: MembershipTierUpdate,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    更新會員等級
    僅管理員可操作
    """
    try:
        tier = db.query(MembershipTier).filter(
            MembershipTier.tier_type == tier_type
        ).first()
        
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="會員等級不存在"
            )
        
        # 更新等級信息
        update_data = tier_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(tier, field, value)
        
        tier.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(tier)
        
        logger.info(f"會員等級更新成功: {tier_type} (操作者: {current_user.email})")
        return tier
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新會員等級失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新會員等級失敗"
        )

@router.delete("/tiers/{tier_type}")
async def delete_membership_tier(
    tier_type: TierType,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    刪除會員等級（軟刪除）
    僅管理員可操作
    """
    try:
        tier = db.query(MembershipTier).filter(
            MembershipTier.tier_type == tier_type
        ).first()
        
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="會員等級不存在"
            )
        
        # 檢查是否有用戶使用此等級
        from ..models.user import User as UserModel
        users_count = db.query(UserModel).filter(
            UserModel.membership_tier == tier_type
        ).count()
        
        if users_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無法刪除，仍有 {users_count} 個用戶使用此等級"
            )
        
        # 軟刪除
        tier.is_active = False
        tier.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"會員等級已停用: {tier_type} (操作者: {current_user.email})")
        return {"message": "會員等級已停用"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除會員等級失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除會員等級失敗"
        )

# 會員等級比較和推薦
@router.get("/comparison", response_model=TierComparison)
async def get_tier_comparison():
    """
    獲取會員等級比較表
    """
    try:
        comparison = get_tier_comparison()
        return comparison
        
    except Exception as e:
        logger.error(f"獲取等級比較失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取等級比較失敗"
        )

@router.get("/recommendation", response_model=Optional[UpgradeRecommendation])
async def get_upgrade_recommendation(
    current_user: User = Depends(get_current_user)
):
    """
    獲取會員升級建議
    """
    try:
        # 構建用戶使用數據
        usage_data = {
            "current_tier": current_user.membership_tier.value,
            "daily_api_calls": current_user.api_calls_today,
            "monthly_api_calls": current_user.api_calls_month,
            "total_analyses": current_user.total_analyses,
            "member_days": (datetime.utcnow() - current_user.created_at).days
        }
        
        recommendation = recommend_tier_upgrade(usage_data)
        return recommendation
        
    except Exception as e:
        logger.error(f"獲取升級建議失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取升級建議失敗"
        )

# 等級功能管理
@router.post("/tiers/{tier_type}/features", response_model=TierFeatureResponse)
async def add_tier_feature(
    tier_type: TierType,
    feature_type: FeatureType,
    feature_name: str,
    feature_value: Optional[str] = None,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    為會員等級添加功能
    僅管理員可操作
    """
    try:
        # 檢查等級是否存在
        tier = db.query(MembershipTier).filter(
            MembershipTier.tier_type == tier_type
        ).first()
        
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="會員等級不存在"
            )
        
        # 創建功能
        feature = TierFeature(
            tier_id=tier.id,
            feature_type=feature_type,
            feature_name=feature_name,
            feature_value=feature_value
        )
        
        db.add(feature)
        db.commit()
        db.refresh(feature)
        
        logger.info(f"等級功能添加成功: {tier_type} - {feature_name} (操作者: {current_user.email})")
        return feature
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加等級功能失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加等級功能失敗"
        )

@router.get("/tiers/{tier_type}/features", response_model=List[TierFeatureResponse])
async def list_tier_features(
    tier_type: TierType,
    db: Session = Depends(get_db)
):
    """
    獲取會員等級功能列表
    """
    try:
        tier = db.query(MembershipTier).filter(
            MembershipTier.tier_type == tier_type
        ).first()
        
        if not tier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="會員等級不存在"
            )
        
        features = db.query(TierFeature).filter(
            TierFeature.tier_id == tier.id,
            TierFeature.is_enabled == True
        ).all()
        
        return features
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取等級功能列表失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取等級功能列表失敗"
        )

# 等級配置初始化
@router.post("/initialize-default-tiers")
async def initialize_default_tiers(
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    初始化預設會員等級配置
    僅管理員可操作
    """
    try:
        created_tiers = []
        
        for tier_type, config in DEFAULT_TIER_CONFIGS.items():
            # 檢查等級是否已存在
            existing_tier = db.query(MembershipTier).filter(
                MembershipTier.tier_type == tier_type
            ).first()
            
            if existing_tier:
                logger.info(f"等級已存在，跳過: {tier_type}")
                continue
            
            # 創建等級
            tier = MembershipTier(
                tier_type=tier_type,
                name=config["name"],
                description=config["description"],
                monthly_price=config["monthly_price"],
                quarterly_price=config.get("quarterly_price", config["monthly_price"] * 3),
                yearly_price=config.get("yearly_price", config["monthly_price"] * 12),
                daily_api_quota=config["daily_api_quota"],
                monthly_api_quota=config["monthly_api_quota"],
                max_concurrent_analyses=config["max_concurrent_analyses"],
                features=config["features"],
                export_formats=config["export_formats"],
                sort_order=config["sort_order"]
            )
            
            db.add(tier)
            created_tiers.append(tier_type.value)
        
        if created_tiers:
            db.commit()
            logger.info(f"預設等級初始化完成: {created_tiers} (操作者: {current_user.email})")
        
        return {
            "message": "預設等級初始化完成",
            "created_tiers": created_tiers,
            "total_created": len(created_tiers)
        }
        
    except Exception as e:
        logger.error(f"初始化預設等級失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="初始化預設等級失敗"
        )

# 等級升級規則管理
@router.post("/upgrade-rules")
async def create_upgrade_rule(
    from_tier: TierType,
    to_tier: TierType,
    min_usage_days: int = 0,
    min_api_calls: int = 0,
    min_analyses: int = 0,
    discount_percentage: float = 0,
    free_trial_days: int = 0,
    current_user: User = Depends(verify_admin_user),
    db: Session = Depends(get_db)
):
    """
    創建等級升級規則
    僅管理員可操作
    """
    try:
        # 檢查規則是否已存在
        existing_rule = db.query(TierUpgradeRule).filter(
            TierUpgradeRule.from_tier == from_tier,
            TierUpgradeRule.to_tier == to_tier
        ).first()
        
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="升級規則已存在"
            )
        
        # 創建升級規則
        rule = TierUpgradeRule(
            from_tier=from_tier,
            to_tier=to_tier,
            min_usage_days=min_usage_days,
            min_api_calls=min_api_calls,
            min_analyses=min_analyses,
            discount_percentage=discount_percentage,
            free_trial_days=free_trial_days
        )
        
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        logger.info(f"升級規則創建成功: {from_tier} -> {to_tier} (操作者: {current_user.email})")
        return rule
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建升級規則失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建升級規則失敗"
        )

@router.get("/health")
async def membership_health_check():
    """
    會員系統健康檢查
    """
    try:
        return {
            "service": "membership",
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "features": [
                "tier_management",
                "upgrade_recommendations", 
                "feature_configuration",
                "pricing_management"
            ]
        }
        
    except Exception as e:
        logger.error(f"會員系統健康檢查失敗: {str(e)}")
        return {
            "service": "membership",
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }