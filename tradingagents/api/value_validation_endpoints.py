#!/usr/bin/env python3
"""
價值驗證數據收集API端點
任務 0.1.3: 建立價值驗證數據收集的API層
提供市場反饋收集、付費意願分析和定價優化API
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..services.value_validation_service import (
    ValueValidationService, 
    FeedbackType, 
    PaymentWillingnessLevel
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/value-validation", tags=["value-validation"])

# 請求模型
class MarketFeedbackRequest(BaseModel):
    user_id: str
    feedback_type: str  # rating, comment, survey, complaint, suggestion, testimonial
    content: str
    rating: Optional[int] = None
    insight_id: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None

class AnalyzePopularityRequest(BaseModel):
    days: int = 30

class AnalyzePaymentWillingnessRequest(BaseModel):
    user_id: Optional[str] = None

class OptimizePricingRequest(BaseModel):
    insight_category: Optional[str] = None
    personality_type: Optional[str] = None

# 響應模型
class InsightPopularityResponse(BaseModel):
    insight_id: str
    title: str
    category: str
    difficulty_level: str
    personality_types: List[str]
    view_count: int
    purchase_count: int
    conversion_rate: float
    avg_rating: float
    total_revenue: float
    engagement_score: float
    retention_rate: float

class PaymentWillingnessResponse(BaseModel):
    user_id: str
    personality_type: str
    willingness_level: str
    max_willing_price: float
    preferred_payment_model: str
    price_sensitivity_score: float
    value_perception_score: float
    purchase_frequency: float
    avg_session_value: float

class PricingOptimizationResponse(BaseModel):
    current_price: float
    optimal_price_min: float
    optimal_price_max: float
    demand_elasticity: float
    revenue_impact: float
    conversion_impact: float
    user_segment: str
    confidence_level: float

class MarketFeedbackAnalysisResponse(BaseModel):
    period_days: int
    feedback_by_type: List[Dict[str, Any]]
    feedback_by_insight: List[Dict[str, Any]]
    sentiment_trend: List[Dict[str, Any]]

# 服務實例
value_validation_service = ValueValidationService()

@router.post("/feedback")
async def submit_market_feedback(request: MarketFeedbackRequest):
    """提交市場反饋"""
    try:
        # 驗證反饋類型
        try:
            feedback_type = FeedbackType(request.feedback_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的反饋類型"
            )
        
        feedback_id = await value_validation_service.collect_market_feedback(
            user_id=request.user_id,
            feedback_type=feedback_type,
            content=request.content,
            rating=request.rating,
            insight_id=request.insight_id,
            context_data=request.context_data
        )
        
        if feedback_id:
            return {
                "success": True,
                "message": "反饋提交成功",
                "feedback_id": feedback_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="反饋提交失敗"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提交市場反饋API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="反饋提交失敗"
        )

@router.get("/popularity-analysis", response_model=List[InsightPopularityResponse])
async def analyze_insight_popularity(days: int = Query(30, ge=1, le=365)):
    """分析洞察受歡迎程度"""
    try:
        popularity_data = await value_validation_service.analyze_insight_popularity(days)
        
        response_data = []
        for data in popularity_data:
            response_data.append(InsightPopularityResponse(
                insight_id=data.insight_id,
                title=data.title,
                category=data.category,
                difficulty_level=data.difficulty_level,
                personality_types=data.personality_types,
                view_count=data.view_count,
                purchase_count=data.purchase_count,
                conversion_rate=data.conversion_rate,
                avg_rating=data.avg_rating,
                total_revenue=data.total_revenue,
                engagement_score=data.engagement_score,
                retention_rate=data.retention_rate
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"分析洞察受歡迎程度API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="受歡迎程度分析失敗"
        )

@router.get("/payment-willingness", response_model=List[PaymentWillingnessResponse])
async def analyze_payment_willingness(user_id: Optional[str] = Query(None)):
    """分析用戶付費意願"""
    try:
        willingness_data = await value_validation_service.analyze_payment_willingness(user_id)
        
        response_data = []
        for data in willingness_data:
            response_data.append(PaymentWillingnessResponse(
                user_id=data.user_id,
                personality_type=data.personality_type,
                willingness_level=data.willingness_level.value,
                max_willing_price=data.max_willing_price,
                preferred_payment_model=data.preferred_payment_model,
                price_sensitivity_score=data.price_sensitivity_score,
                value_perception_score=data.value_perception_score,
                purchase_frequency=data.purchase_frequency,
                avg_session_value=data.avg_session_value
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"分析用戶付費意願API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="付費意願分析失敗"
        )

@router.get("/pricing-optimization", response_model=List[PricingOptimizationResponse])
async def optimize_pricing_strategy(
    insight_category: Optional[str] = Query(None),
    personality_type: Optional[str] = Query(None)
):
    """優化定價策略"""
    try:
        optimization_data = await value_validation_service.optimize_pricing_strategy(
            insight_category=insight_category,
            personality_type=personality_type
        )
        
        response_data = []
        for data in optimization_data:
            response_data.append(PricingOptimizationResponse(
                current_price=data.current_price,
                optimal_price_min=data.optimal_price_range[0],
                optimal_price_max=data.optimal_price_range[1],
                demand_elasticity=data.demand_elasticity,
                revenue_impact=data.revenue_impact,
                conversion_impact=data.conversion_impact,
                user_segment=data.user_segment,
                confidence_level=data.confidence_level
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"優化定價策略API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="定價優化失敗"
        )

@router.get("/feedback-analysis", response_model=MarketFeedbackAnalysisResponse)
async def get_market_feedback_analysis(days: int = Query(30, ge=1, le=365)):
    """獲取市場反饋分析"""
    try:
        analysis = await value_validation_service.get_market_feedback_analysis(days)
        
        return MarketFeedbackAnalysisResponse(**analysis)
        
    except Exception as e:
        logger.error(f"獲取市場反饋分析API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="反饋分析失敗"
        )

@router.get("/summary")
async def get_value_validation_summary(days: int = Query(30, ge=1, le=365)):
    """獲取價值驗證摘要報告"""
    try:
        summary = await value_validation_service.get_value_validation_summary(days)
        
        return summary
        
    except Exception as e:
        logger.error(f"獲取價值驗證摘要API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="摘要報告生成失敗"
        )

@router.get("/feedback-types")
async def get_feedback_types():
    """獲取反饋類型"""
    try:
        feedback_types = [
            {
                "value": feedback_type.value,
                "name": feedback_type.name,
                "description": {
                    "rating": "用戶評分反饋",
                    "comment": "用戶評論反饋",
                    "survey": "調查問卷反饋",
                    "complaint": "投訴反饋",
                    "suggestion": "建議反饋",
                    "testimonial": "推薦證言"
                }.get(feedback_type.value, "")
            }
            for feedback_type in FeedbackType
        ]
        
        return {
            "feedback_types": feedback_types,
            "total": len(feedback_types)
        }
        
    except Exception as e:
        logger.error(f"獲取反饋類型API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取反饋類型失敗"
        )

@router.get("/willingness-levels")
async def get_willingness_levels():
    """獲取付費意願等級"""
    try:
        willingness_levels = [
            {
                "value": level.value,
                "name": level.name,
                "description": {
                    "very_low": "付費意願很低 (0-20%)",
                    "low": "付費意願較低 (21-40%)",
                    "medium": "付費意願中等 (41-60%)",
                    "high": "付費意願較高 (61-80%)",
                    "very_high": "付費意願很高 (81-100%)"
                }.get(level.value, "")
            }
            for level in PaymentWillingnessLevel
        ]
        
        return {
            "willingness_levels": willingness_levels,
            "total": len(willingness_levels)
        }
        
    except Exception as e:
        logger.error(f"獲取付費意願等級API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取意願等級失敗"
        )

@router.get("/top-insights")
async def get_top_performing_insights(
    metric: str = Query("conversion_rate", regex="^(conversion_rate|revenue|engagement|rating)$"),
    limit: int = Query(10, ge=1, le=50),
    days: int = Query(30, ge=1, le=365)
):
    """獲取表現最佳的洞察"""
    try:
        popularity_data = await value_validation_service.analyze_insight_popularity(days)
        
        # 根據指定指標排序
        if metric == "conversion_rate":
            sorted_data = sorted(popularity_data, key=lambda x: x.conversion_rate, reverse=True)
        elif metric == "revenue":
            sorted_data = sorted(popularity_data, key=lambda x: x.total_revenue, reverse=True)
        elif metric == "engagement":
            sorted_data = sorted(popularity_data, key=lambda x: x.engagement_score, reverse=True)
        elif metric == "rating":
            sorted_data = sorted(popularity_data, key=lambda x: x.avg_rating, reverse=True)
        else:
            sorted_data = popularity_data
        
        top_insights = sorted_data[:limit]
        
        return {
            "metric": metric,
            "period_days": days,
            "top_insights": [
                {
                    "insight_id": insight.insight_id,
                    "title": insight.title,
                    "category": insight.category,
                    "conversion_rate": insight.conversion_rate,
                    "total_revenue": insight.total_revenue,
                    "engagement_score": insight.engagement_score,
                    "avg_rating": insight.avg_rating,
                    "purchase_count": insight.purchase_count
                }
                for insight in top_insights
            ],
            "total_shown": len(top_insights)
        }
        
    except Exception as e:
        logger.error(f"獲取表現最佳洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取頂級洞察失敗"
        )

@router.get("/market-insights")
async def get_market_insights(days: int = Query(30, ge=1, le=365)):
    """獲取市場洞察和趨勢"""
    try:
        # 獲取各項分析數據
        popularity_data = await value_validation_service.analyze_insight_popularity(days)
        willingness_data = await value_validation_service.analyze_payment_willingness()
        feedback_analysis = await value_validation_service.get_market_feedback_analysis(days)
        
        # 分析市場趨勢
        category_performance = {}
        personality_preferences = {}
        
        for insight in popularity_data:
            category = insight.category
            if category not in category_performance:
                category_performance[category] = {
                    "total_revenue": 0,
                    "avg_conversion_rate": 0,
                    "insight_count": 0
                }
            
            category_performance[category]["total_revenue"] += insight.total_revenue
            category_performance[category]["avg_conversion_rate"] += insight.conversion_rate
            category_performance[category]["insight_count"] += 1
        
        # 計算平均值
        for category in category_performance:
            count = category_performance[category]["insight_count"]
            if count > 0:
                category_performance[category]["avg_conversion_rate"] /= count
        
        # 分析人格偏好
        for user in willingness_data:
            personality = user.personality_type
            if personality not in personality_preferences:
                personality_preferences[personality] = {
                    "avg_willingness": 0,
                    "avg_max_price": 0,
                    "user_count": 0
                }
            
            personality_preferences[personality]["avg_willingness"] += user.value_perception_score
            personality_preferences[personality]["avg_max_price"] += user.max_willing_price
            personality_preferences[personality]["user_count"] += 1
        
        # 計算平均值
        for personality in personality_preferences:
            count = personality_preferences[personality]["user_count"]
            if count > 0:
                personality_preferences[personality]["avg_willingness"] /= count
                personality_preferences[personality]["avg_max_price"] /= count
        
        return {
            "period_days": days,
            "category_performance": category_performance,
            "personality_preferences": personality_preferences,
            "market_sentiment": {
                "avg_sentiment": sum([item["avg_sentiment"] for item in feedback_analysis.get("feedback_by_type", [])]) / max(1, len(feedback_analysis.get("feedback_by_type", []))),
                "total_feedback": sum([item["count"] for item in feedback_analysis.get("feedback_by_type", [])])
            },
            "key_insights": [
                "最受歡迎的洞察類別",
                "用戶付費意願最高的人格類型",
                "市場反饋整體趨勢",
                "定價優化機會"
            ]
        }
        
    except Exception as e:
        logger.error(f"獲取市場洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="市場洞察分析失敗"
        )