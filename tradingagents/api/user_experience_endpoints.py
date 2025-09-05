#!/usr/bin/env python3
"""
TradingAgents 用戶體驗和留存率優化 API 端點
提供智能推薦、學習中心、社群功能、績效追蹤等
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..services.user_experience_service import (
    UserExperienceService, RecommendationType, RiskProfile, InvestmentGoal
)
from ..utils.user_context import UserContext
from ..models.membership import TierType
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/user-experience", tags=["user-experience"])

# 請求模型
class UserProfileRequest(BaseModel):
    """用戶檔案請求"""
    risk_profile: str = Field(..., description="風險偏好")
    investment_goals: List[str] = Field(..., description="投資目標")
    investment_horizon: str = Field(..., description="投資期限")
    preferred_markets: List[str] = Field(..., description="偏好市場")
    preferred_sectors: List[str] = Field(..., description="偏好行業")
    portfolio_size: float = Field(..., description="投資組合規模")
    experience_level: str = Field(..., description="經驗水平")

class CommunityPostRequest(BaseModel):
    """社群貼文請求"""
    title: str = Field(..., description="標題")
    content: str = Field(..., description="內容")
    category: str = Field("general", description="分類")
    tags: List[str] = Field(default_factory=list, description="標籤")
    symbols_mentioned: List[str] = Field(default_factory=list, description="提及的股票")

class CommentRequest(BaseModel):
    """評論請求"""
    post_id: str = Field(..., description="貼文ID")
    content: str = Field(..., description="評論內容")

class PortfolioTrackingRequest(BaseModel):
    """投資組合追蹤請求"""
    total_value: float = Field(..., description="總價值")
    positions: List[Dict[str, Any]] = Field(..., description="持倉列表")

# 響應模型
class StandardResponse(BaseModel):
    """標準響應格式"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None

# 服務實例
ux_service = UserExperienceService()

@router.post("/profile")
async def create_user_profile(
    request: UserProfileRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    創建或更新用戶投資檔案
    
    Args:
        request: 用戶檔案請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        用戶檔案創建結果
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 創建用戶檔案
        profile = await ux_service.create_user_profile(
            user_context=user_context,
            profile_data=request.dict()
        )
        
        return StandardResponse(
            success=True,
            data=profile.to_dict(),
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"創建用戶檔案失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/recommendations")
async def get_smart_recommendations(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級"),
    limit: int = Query(5, description="推薦數量", ge=1, le=20)
) -> StandardResponse:
    """
    獲取智能推薦
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        limit: 推薦數量限制
        
    Returns:
        智能推薦列表
    """
    try:
        # 檢查會員權限
        if membership_tier == TierType.FREE:
            return StandardResponse(
                success=False,
                error='需要升級會員以獲取智能推薦',
                data={
                    'upgrade_prompt': {
                        'title': '🤖 AI智能推薦',
                        'message': '升級至 Gold 會員，獲得個人化的投資建議和智能推薦',
                        'benefits': [
                            '基於AI的個人化股票推薦',
                            '投資組合優化建議',
                            '風險管理策略指導',
                            '市場機會及時提醒'
                        ]
                    }
                }
            )
        
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 生成智能推薦
        recommendations = await ux_service.generate_smart_recommendations(
            user_context=user_context,
            limit=limit
        )
        
        return StandardResponse(
            success=True,
            data={
                'recommendations': [rec.to_dict() for rec in recommendations],
                'total_count': len(recommendations)
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"獲取智能推薦失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/learning-path")
async def get_learning_path(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取個人化學習路徑
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        個人化學習路徑
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 獲取學習路徑
        learning_path = await ux_service.get_personalized_learning_path(user_context)
        
        return StandardResponse(
            success=True,
            data=learning_path,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"獲取學習路徑失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/community/post")
async def create_community_post(
    request: CommunityPostRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    創建社群貼文
    
    Args:
        request: 貼文請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        貼文創建結果
    """
    try:
        # 檢查會員權限
        if membership_tier == TierType.FREE:
            return StandardResponse(
                success=False,
                error='需要升級會員以參與社群討論',
                data={
                    'upgrade_prompt': {
                        'title': '💬 投資社群',
                        'message': '升級至 Gold 會員，加入專業投資者社群',
                        'benefits': [
                            '參與投資討論和經驗分享',
                            '獲得其他投資者的見解',
                            '發布投資分析和觀點',
                            '建立投資人脈網絡'
                        ]
                    }
                }
            )
        
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 創建貼文
        post = await ux_service.create_community_post(
            user_context=user_context,
            post_data=request.dict()
        )
        
        return StandardResponse(
            success=True,
            data=post,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"創建社群貼文失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/community/feed")
async def get_community_feed(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級"),
    category: Optional[str] = Query(None, description="分類過濾"),
    limit: int = Query(20, description="返回數量", ge=1, le=50)
) -> StandardResponse:
    """
    獲取社群動態
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        category: 分類過濾
        limit: 返回數量限制
        
    Returns:
        社群貼文列表
    """
    try:
        # 檢查會員權限
        if membership_tier == TierType.FREE:
            return StandardResponse(
                success=False,
                error='需要升級會員以查看社群內容'
            )
        
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 獲取社群動態
        feed = await ux_service.get_community_feed(
            user_context=user_context,
            category=category,
            limit=limit
        )
        
        return StandardResponse(
            success=True,
            data={
                'posts': feed,
                'total_count': len(feed),
                'category_filter': category
            },
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"獲取社群動態失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/community/comment")
async def add_comment(
    request: CommentRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    添加評論
    
    Args:
        request: 評論請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        評論添加結果
    """
    try:
        # 檢查會員權限
        if membership_tier == TierType.FREE:
            return StandardResponse(
                success=False,
                error='需要升級會員以參與討論'
            )
        
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 添加評論
        success = await ux_service.add_comment_to_post(
            user_context=user_context,
            post_id=request.post_id,
            comment_content=request.content
        )
        
        return StandardResponse(
            success=success,
            data={'comment_added': success},
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"添加評論失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/performance/track")
async def track_portfolio_performance(
    request: PortfolioTrackingRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    追蹤投資組合績效
    
    Args:
        request: 投資組合追蹤請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        績效追蹤結果
    """
    try:
        # 檢查會員權限
        if membership_tier == TierType.FREE:
            return StandardResponse(
                success=False,
                error='需要升級會員以使用績效追蹤功能',
                data={
                    'upgrade_prompt': {
                        'title': '📊 投資績效追蹤',
                        'message': '升級至 Gold 會員，獲得專業的投資績效分析工具',
                        'benefits': [
                            '詳細的投資績效分析',
                            '與基準指數的比較',
                            '風險調整後回報計算',
                            '個人化改善建議'
                        ]
                    }
                }
            )
        
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 追蹤績效
        performance_result = await ux_service.track_portfolio_performance(
            user_context=user_context,
            portfolio_data=request.dict()
        )
        
        return StandardResponse(
            success=True,
            data=performance_result,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"追蹤投資組合績效失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/vip-report")
async def get_vip_research_report(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級"),
    report_type: str = Query("weekly", description="報告類型")
) -> StandardResponse:
    """
    獲取VIP專屬研究報告
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        report_type: 報告類型
        
    Returns:
        VIP研究報告
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 生成VIP報告
        report = await ux_service.generate_vip_research_report(
            user_context=user_context,
            report_type=report_type
        )
        
        if 'error' in report:
            return StandardResponse(
                success=False,
                error=report['error'],
                data=report.get('upgrade_prompt')
            )
        
        return StandardResponse(
            success=True,
            data=report,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"獲取VIP研究報告失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/engagement-stats")
async def get_engagement_stats(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取用戶參與度統計
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        用戶參與度統計
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 獲取參與度統計
        stats = await ux_service.get_user_engagement_stats(user_context)
        
        return StandardResponse(
            success=True,
            data=stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"獲取參與度統計失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/service-stats")
async def get_service_stats() -> StandardResponse:
    """
    獲取服務統計信息
    
    Returns:
        服務統計信息
    """
    try:
        stats = await ux_service.get_service_stats()
        
        return StandardResponse(
            success=True,
            data=stats,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"獲取服務統計失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )