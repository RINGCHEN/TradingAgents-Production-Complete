#!/usr/bin/env python3
"""
智能升級推薦API端點
任務 0.1.2: 開發智能升級推薦系統的API層
提供升級推薦、互動追蹤和轉換分析API
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..services.upgrade_recommendation_service import (
    UpgradeRecommendationService, 
    UpgradeRecommendationType, 
    UpgradeStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upgrade-recommendations", tags=["upgrade-recommendations"])

# 請求模型
class CheckUpgradeTriggersRequest(BaseModel):
    user_id: str

class TrackInteractionRequest(BaseModel):
    recommendation_id: str
    action: str  # shown, clicked, converted, dismissed
    additional_data: Optional[Dict[str, Any]] = None

class GetRecommendationsRequest(BaseModel):
    user_id: str
    active_only: bool = True

# 響應模型
class UserSpendingPatternResponse(BaseModel):
    user_id: str
    monthly_spending: float
    transaction_frequency: float
    avg_transaction_amount: float
    preferred_insight_types: List[str]
    engagement_score: float
    days_since_first_purchase: int
    total_lifetime_spending: float

class UpgradeRecommendationResponse(BaseModel):
    id: str
    user_id: str
    recommendation_type: str
    trigger_data: Dict[str, Any]
    recommended_tier: str
    discount_percentage: float
    discount_amount: float
    expires_at: str
    personalized_message: str
    value_proposition: List[str]
    urgency_message: str
    status: str
    created_at: str

class ConversionFunnelResponse(BaseModel):
    step: str
    user_count: int
    conversion_rate: float
    avg_time_to_next_step: float
    drop_off_reasons: List[str]

class RecommendationAnalyticsResponse(BaseModel):
    period_days: int
    total_recommendations: int
    unique_users: int
    avg_discount_percentage: float
    total_conversions: int
    overall_conversion_rate: float
    by_type: List[Dict[str, Any]]

# 服務實例
upgrade_service = UpgradeRecommendationService()

@router.post("/analyze-spending-pattern", response_model=UserSpendingPatternResponse)
async def analyze_user_spending_pattern(request: CheckUpgradeTriggersRequest):
    """分析用戶消費模式"""
    try:
        pattern = await upgrade_service.analyze_user_spending_pattern(request.user_id)
        
        return UserSpendingPatternResponse(
            user_id=pattern.user_id,
            monthly_spending=pattern.monthly_spending,
            transaction_frequency=pattern.transaction_frequency,
            avg_transaction_amount=pattern.avg_transaction_amount,
            preferred_insight_types=pattern.preferred_insight_types,
            engagement_score=pattern.engagement_score,
            days_since_first_purchase=pattern.days_since_first_purchase,
            total_lifetime_spending=pattern.total_lifetime_spending
        )
        
    except Exception as e:
        logger.error(f"分析用戶消費模式API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析消費模式失敗"
        )

@router.post("/check-triggers", response_model=List[UpgradeRecommendationResponse])
async def check_upgrade_triggers(request: CheckUpgradeTriggersRequest):
    """檢查升級觸發條件並生成推薦"""
    try:
        recommendations = await upgrade_service.check_upgrade_triggers(request.user_id)
        
        response_data = []
        for rec in recommendations:
            response_data.append(UpgradeRecommendationResponse(
                id=rec.id,
                user_id=rec.user_id,
                recommendation_type=rec.recommendation_type.value,
                trigger_data=rec.trigger_data,
                recommended_tier=rec.recommended_tier,
                discount_percentage=rec.discount_percentage,
                discount_amount=rec.discount_amount,
                expires_at=rec.expires_at.isoformat(),
                personalized_message=rec.personalized_message,
                value_proposition=rec.value_proposition,
                urgency_message=rec.urgency_message,
                status=rec.status.value,
                created_at=rec.created_at.isoformat()
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"檢查升級觸發條件API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="檢查升級觸發條件失敗"
        )

@router.post("/track-interaction")
async def track_recommendation_interaction(request: TrackInteractionRequest):
    """追蹤推薦互動"""
    try:
        await upgrade_service.track_recommendation_interaction(
            recommendation_id=request.recommendation_id,
            action=request.action,
            additional_data=request.additional_data
        )
        
        return {
            "success": True,
            "message": "互動追蹤成功",
            "recommendation_id": request.recommendation_id,
            "action": request.action
        }
        
    except Exception as e:
        logger.error(f"追蹤推薦互動API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="互動追蹤失敗"
        )

@router.get("/user/{user_id}", response_model=List[UpgradeRecommendationResponse])
async def get_user_recommendations(
    user_id: str,
    active_only: bool = Query(True, description="只返回活躍的推薦")
):
    """獲取用戶的升級推薦"""
    try:
        recommendations = await upgrade_service.get_user_recommendations(
            user_id=user_id,
            active_only=active_only
        )
        
        response_data = []
        for rec in recommendations:
            response_data.append(UpgradeRecommendationResponse(
                id=rec.id,
                user_id=rec.user_id,
                recommendation_type=rec.recommendation_type.value,
                trigger_data=rec.trigger_data,
                recommended_tier=rec.recommended_tier,
                discount_percentage=rec.discount_percentage,
                discount_amount=rec.discount_amount,
                expires_at=rec.expires_at.isoformat(),
                personalized_message=rec.personalized_message,
                value_proposition=rec.value_proposition,
                urgency_message=rec.urgency_message,
                status=rec.status.value,
                created_at=rec.created_at.isoformat()
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"獲取用戶推薦API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶推薦失敗"
        )

@router.get("/conversion-funnel", response_model=List[ConversionFunnelResponse])
async def analyze_conversion_funnel(
    days: int = Query(30, ge=1, le=365, description="分析天數")
):
    """分析轉換漏斗"""
    try:
        funnel_data = await upgrade_service.analyze_conversion_funnel(days)
        
        response_data = []
        for data in funnel_data:
            response_data.append(ConversionFunnelResponse(
                step=data.step,
                user_count=data.user_count,
                conversion_rate=data.conversion_rate,
                avg_time_to_next_step=data.avg_time_to_next_step,
                drop_off_reasons=data.drop_off_reasons
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"分析轉換漏斗API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="轉換漏斗分析失敗"
        )

@router.get("/analytics", response_model=RecommendationAnalyticsResponse)
async def get_recommendation_analytics(
    days: int = Query(30, ge=1, le=365, description="分析天數")
):
    """獲取推薦分析數據"""
    try:
        analytics = await upgrade_service.get_recommendation_analytics(days)
        
        return RecommendationAnalyticsResponse(**analytics)
        
    except Exception as e:
        logger.error(f"獲取推薦分析數據API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取分析數據失敗"
        )

@router.get("/trigger-types")
async def get_trigger_types():
    """獲取推薦觸發類型"""
    try:
        trigger_types = [
            {
                "value": trigger_type.value,
                "name": trigger_type.name,
                "description": {
                    "monthly_threshold": "月消費達到門檻時觸發",
                    "usage_pattern": "基於使用模式分析觸發",
                    "engagement_level": "基於用戶互動程度觸發",
                    "seasonal_promotion": "季節性促銷活動觸發",
                    "personalized_offer": "個性化優惠觸發"
                }.get(trigger_type.value, "")
            }
            for trigger_type in UpgradeRecommendationType
        ]
        
        return {
            "trigger_types": trigger_types,
            "total": len(trigger_types)
        }
        
    except Exception as e:
        logger.error(f"獲取觸發類型API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取觸發類型失敗"
        )

@router.get("/status-types")
async def get_status_types():
    """獲取推薦狀態類型"""
    try:
        status_types = [
            {
                "value": status_type.value,
                "name": status_type.name,
                "description": {
                    "pending": "推薦已生成，等待展示",
                    "shown": "推薦已展示給用戶",
                    "clicked": "用戶已點擊推薦",
                    "converted": "用戶已完成升級轉換",
                    "dismissed": "用戶已忽略推薦",
                    "expired": "推薦已過期"
                }.get(status_type.value, "")
            }
            for status_type in UpgradeStatus
        ]
        
        return {
            "status_types": status_types,
            "total": len(status_types)
        }
        
    except Exception as e:
        logger.error(f"獲取狀態類型API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取狀態類型失敗"
        )

@router.post("/simulate-trigger")
async def simulate_upgrade_trigger(
    user_id: str,
    trigger_type: str,
    force: bool = Query(False, description="強制觸發，忽略近期推薦檢查")
):
    """模擬升級觸發（測試用）"""
    try:
        # 驗證觸發類型
        try:
            trigger_enum = UpgradeRecommendationType(trigger_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的觸發類型"
            )
        
        # 分析用戶消費模式
        pattern = await upgrade_service.analyze_user_spending_pattern(user_id)
        
        # 根據觸發類型創建推薦
        recommendation = None
        
        if trigger_enum == UpgradeRecommendationType.MONTHLY_THRESHOLD:
            # 臨時修改消費金額以觸發門檻
            pattern.monthly_spending = max(pattern.monthly_spending, 50.0)
            recommendation = await upgrade_service._create_threshold_recommendation(user_id, pattern)
        
        elif trigger_enum == UpgradeRecommendationType.ENGAGEMENT_LEVEL:
            # 臨時修改互動分數以觸發
            pattern.engagement_score = max(pattern.engagement_score, 0.7)
            recommendation = await upgrade_service._create_engagement_recommendation(user_id, pattern)
        
        elif trigger_enum == UpgradeRecommendationType.USAGE_PATTERN:
            # 臨時修改使用頻率以觸發
            pattern.transaction_frequency = max(pattern.transaction_frequency, 2.0)
            recommendation = await upgrade_service._create_usage_pattern_recommendation(user_id, pattern)
        
        elif trigger_enum == UpgradeRecommendationType.PERSONALIZED_OFFER:
            # 臨時修改總消費以觸發
            pattern.total_lifetime_spending = max(pattern.total_lifetime_spending, 20.0)
            recommendation = await upgrade_service._create_personalized_offer(user_id, pattern)
        
        if recommendation:
            return {
                "success": True,
                "message": f"成功模擬 {trigger_type} 觸發",
                "recommendation": {
                    "id": recommendation.id,
                    "user_id": recommendation.user_id,
                    "recommendation_type": recommendation.recommendation_type.value,
                    "discount_percentage": recommendation.discount_percentage,
                    "personalized_message": recommendation.personalized_message,
                    "expires_at": recommendation.expires_at.isoformat()
                }
            }
        else:
            return {
                "success": False,
                "message": f"無法觸發 {trigger_type}，可能已有近期推薦"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"模擬升級觸發API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="模擬觸發失敗"
        )

@router.get("/dashboard-summary/{user_id}")
async def get_user_upgrade_dashboard(user_id: str):
    """獲取用戶升級儀表板摘要"""
    try:
        # 獲取用戶消費模式
        pattern = await upgrade_service.analyze_user_spending_pattern(user_id)
        
        # 獲取活躍推薦
        recommendations = await upgrade_service.get_user_recommendations(user_id, active_only=True)
        
        # 計算升級建議
        upgrade_suggestions = []
        
        # 月消費門檻建議
        if pattern.monthly_spending >= 30.0:  # 接近門檻
            remaining_to_threshold = max(0, 50.0 - pattern.monthly_spending)
            upgrade_suggestions.append({
                "type": "threshold_approaching",
                "message": f"再消費 ${remaining_to_threshold:.0f} 即可享受升級優惠",
                "progress": (pattern.monthly_spending / 50.0) * 100
            })
        
        # 互動程度建議
        if pattern.engagement_score >= 0.5:
            upgrade_suggestions.append({
                "type": "engagement_bonus",
                "message": "您的活躍度很高，可享受活躍用戶專屬折扣",
                "progress": (pattern.engagement_score / 1.0) * 100
            })
        
        return {
            "user_id": user_id,
            "spending_pattern": {
                "monthly_spending": pattern.monthly_spending,
                "transaction_frequency": pattern.transaction_frequency,
                "engagement_score": pattern.engagement_score,
                "total_lifetime_spending": pattern.total_lifetime_spending,
                "preferred_insight_types": pattern.preferred_insight_types
            },
            "active_recommendations": len(recommendations),
            "upgrade_suggestions": upgrade_suggestions,
            "next_milestone": {
                "threshold": 50.0,
                "current": pattern.monthly_spending,
                "remaining": max(0, 50.0 - pattern.monthly_spending),
                "progress_percentage": min((pattern.monthly_spending / 50.0) * 100, 100)
            }
        }
        
    except Exception as e:
        logger.error(f"獲取用戶升級儀表板API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取儀表板數據失敗"
        )