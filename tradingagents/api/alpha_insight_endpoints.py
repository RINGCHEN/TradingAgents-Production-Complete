#!/usr/bin/env python3
"""
阿爾法洞察API端點
任務 0.1.1: 實現按次付費基礎架構的API層
提供阿爾法洞察的推薦、購買和管理API
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..services.alpha_insight_service import AlphaInsightService, InsightCategory, DifficultyLevel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/alpha-insights", tags=["alpha-insights"])

# 請求模型
class PersonalizedRecommendationRequest(BaseModel):
    user_id: str
    personality_type: str
    limit: int = 5

class UnlockInsightRequest(BaseModel):
    user_id: str
    insight_id: str
    payment_id: str

class TrackEngagementRequest(BaseModel):
    user_id: str
    insight_id: str
    action: str
    action_data: Optional[Dict[str, Any]] = None

class CreateInsightRequest(BaseModel):
    title: str
    description: str
    content: str
    personality_types: List[str]
    price: float = 5.00
    category: str = "technical"
    difficulty_level: str = "intermediate"
    estimated_read_time: int = 10
    tags: List[str] = []

# 響應模型
class AlphaInsightResponse(BaseModel):
    id: str
    title: str
    description: str
    personality_types: List[str]
    price: float
    category: str
    difficulty_level: str
    estimated_read_time: int
    tags: List[str]
    view_count: int
    purchase_count: int
    rating: float
    is_active: bool

class PersonalizedRecommendationResponse(BaseModel):
    insight: AlphaInsightResponse
    relevance_score: float
    personalization_reason: str
    urgency_level: str
    expected_value: str

class UnlockResponse(BaseModel):
    success: bool
    message: str
    insight_id: Optional[str] = None

class AnalyticsResponse(BaseModel):
    insight_id: str
    view_count: int
    purchase_count: int
    rating: float
    engagement_stats: Dict[str, int]
    total_purchases: int
    total_revenue: float
    conversion_rate: float

# 服務實例
alpha_insight_service = AlphaInsightService()

@router.post("/recommendations", response_model=List[PersonalizedRecommendationResponse])
async def get_personalized_recommendations(request: PersonalizedRecommendationRequest):
    """獲取個性化阿爾法洞察推薦"""
    try:
        recommendations = await alpha_insight_service.get_personalized_insights(
            user_id=request.user_id,
            personality_type=request.personality_type,
            limit=request.limit
        )
        
        response_data = []
        for rec in recommendations:
            insight_data = AlphaInsightResponse(
                id=rec.insight.id,
                title=rec.insight.title,
                description=rec.insight.description,
                personality_types=rec.insight.personality_types,
                price=rec.insight.price,
                category=rec.insight.category.value,
                difficulty_level=rec.insight.difficulty_level.value,
                estimated_read_time=rec.insight.estimated_read_time,
                tags=rec.insight.tags,
                view_count=rec.insight.view_count,
                purchase_count=rec.insight.purchase_count,
                rating=rec.insight.rating,
                is_active=rec.insight.is_active
            )
            
            response_data.append(PersonalizedRecommendationResponse(
                insight=insight_data,
                relevance_score=rec.relevance_score,
                personalization_reason=rec.personalization_reason,
                urgency_level=rec.urgency_level,
                expected_value=rec.expected_value
            ))
        
        return response_data
        
    except Exception as e:
        logger.error(f"獲取個性化推薦API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取推薦失敗"
        )

@router.post("/unlock", response_model=UnlockResponse)
async def unlock_insight(request: UnlockInsightRequest):
    """解鎖阿爾法洞察"""
    try:
        success = await alpha_insight_service.unlock_insight(
            user_id=request.user_id,
            insight_id=request.insight_id,
            payment_id=request.payment_id
        )
        
        if success:
            return UnlockResponse(
                success=True,
                message="洞察解鎖成功",
                insight_id=request.insight_id
            )
        else:
            return UnlockResponse(
                success=False,
                message="洞察解鎖失敗"
            )
        
    except Exception as e:
        logger.error(f"解鎖洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解鎖處理失敗"
        )

@router.get("/user/{user_id}/unlocked")
async def get_user_unlocked_insights(user_id: str):
    """獲取用戶已解鎖的洞察"""
    try:
        purchases = await alpha_insight_service.get_user_unlocked_insights(user_id)
        
        return {
            "user_id": user_id,
            "unlocked_insights": [
                {
                    "id": purchase.id,
                    "insight_id": purchase.insight_id,
                    "amount": purchase.amount,
                    "currency": purchase.currency,
                    "status": purchase.status,
                    "purchased_at": purchase.purchased_at.isoformat(),
                    "unlocked_at": purchase.unlocked_at.isoformat() if purchase.unlocked_at else None
                }
                for purchase in purchases
            ],
            "total_unlocked": len(purchases)
        }
        
    except Exception as e:
        logger.error(f"獲取用戶解鎖洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取解鎖洞察失敗"
        )

@router.post("/engagement/track")
async def track_engagement(request: TrackEngagementRequest):
    """追蹤洞察互動"""
    try:
        await alpha_insight_service.track_insight_engagement(
            user_id=request.user_id,
            insight_id=request.insight_id,
            action=request.action,
            action_data=request.action_data
        )
        
        return {
            "success": True,
            "message": "互動追蹤成功",
            "user_id": request.user_id,
            "insight_id": request.insight_id,
            "action": request.action
        }
        
    except Exception as e:
        logger.error(f"追蹤互動API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="互動追蹤失敗"
        )

@router.get("/analytics/{insight_id}", response_model=AnalyticsResponse)
async def get_insight_analytics(insight_id: str):
    """獲取洞察分析數據"""
    try:
        analytics = await alpha_insight_service.get_insight_analytics(insight_id)
        
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="洞察不存在"
            )
        
        return AnalyticsResponse(**analytics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取洞察分析API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取分析數據失敗"
        )

@router.post("/create", response_model=Dict[str, str])
async def create_insight(request: CreateInsightRequest):
    """創建新的阿爾法洞察"""
    try:
        insight_data = {
            "title": request.title,
            "description": request.description,
            "content": request.content,
            "personality_types": request.personality_types,
            "price": request.price,
            "category": request.category,
            "difficulty_level": request.difficulty_level,
            "estimated_read_time": request.estimated_read_time,
            "tags": request.tags
        }
        
        insight_id = await alpha_insight_service.create_insight(insight_data)
        
        if insight_id:
            return {
                "success": "true",
                "message": "洞察創建成功",
                "insight_id": insight_id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="洞察創建失敗"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="洞察創建失敗"
        )

@router.get("/categories")
async def get_insight_categories():
    """獲取洞察分類"""
    try:
        categories = [
            {
                "value": category.value,
                "name": category.name,
                "description": {
                    "technical": "技術分析相關洞察",
                    "fundamental": "基本面分析洞察",
                    "sentiment": "市場情緒分析",
                    "risk_management": "風險管理策略",
                    "market_timing": "市場時機判斷"
                }.get(category.value, "")
            }
            for category in InsightCategory
        ]
        
        return {
            "categories": categories,
            "total": len(categories)
        }
        
    except Exception as e:
        logger.error(f"獲取洞察分類API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取分類失敗"
        )

@router.get("/difficulty-levels")
async def get_difficulty_levels():
    """獲取難度級別"""
    try:
        levels = [
            {
                "value": level.value,
                "name": level.name,
                "description": {
                    "beginner": "適合投資新手",
                    "intermediate": "適合有一定經驗的投資者",
                    "advanced": "適合進階投資者",
                    "expert": "適合專業投資者"
                }.get(level.value, "")
            }
            for level in DifficultyLevel
        ]
        
        return {
            "difficulty_levels": levels,
            "total": len(levels)
        }
        
    except Exception as e:
        logger.error(f"獲取難度級別API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取難度級別失敗"
        )

@router.get("/popular")
async def get_popular_insights(limit: int = Query(10, ge=1, le=50)):
    """獲取熱門洞察"""
    try:
        # 這裡可以實現熱門洞察的查詢邏輯
        # 暫時返回模擬數據
        popular_insights = [
            {
                "insight_id": "alpha_001_conservative_risk_mgmt",
                "title": "保守型投資者的風險管理黃金法則",
                "category": "risk_management",
                "purchase_count": 156,
                "rating": 4.2,
                "price": 5.00
            },
            {
                "insight_id": "alpha_002_aggressive_growth_stocks",
                "title": "積極型投資者的高成長股挖掘術",
                "category": "fundamental",
                "purchase_count": 89,
                "rating": 4.0,
                "price": 5.00
            }
        ]
        
        return {
            "popular_insights": popular_insights[:limit],
            "total_shown": min(len(popular_insights), limit),
            "total_available": len(popular_insights)
        }
        
    except Exception as e:
        logger.error(f"獲取熱門洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取熱門洞察失敗"
        )

@router.get("/search")
async def search_insights(
    query: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    personality_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """搜索阿爾法洞察"""
    try:
        # 這裡可以實現搜索邏輯
        # 暫時返回模擬數據
        search_results = [
            {
                "insight_id": "alpha_001_conservative_risk_mgmt",
                "title": "保守型投資者的風險管理黃金法則",
                "description": "專為保守型投資者設計的風險控制策略",
                "category": "risk_management",
                "difficulty_level": "beginner",
                "price": 5.00,
                "rating": 4.2,
                "relevance_score": 0.95
            }
        ]
        
        # 根據查詢參數過濾結果
        filtered_results = search_results
        if category:
            filtered_results = [r for r in filtered_results if r["category"] == category]
        if difficulty:
            filtered_results = [r for r in filtered_results if r["difficulty_level"] == difficulty]
        
        return {
            "query": query,
            "filters": {
                "category": category,
                "difficulty": difficulty,
                "personality_type": personality_type
            },
            "results": filtered_results[:limit],
            "total_results": len(filtered_results),
            "total_shown": min(len(filtered_results), limit)
        }
        
    except Exception as e:
        logger.error(f"搜索洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="搜索失敗"
        )