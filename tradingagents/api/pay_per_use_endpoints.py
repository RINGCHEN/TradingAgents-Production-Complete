#!/usr/bin/env python3
"""
按次付費API端點
提供阿爾法洞察的購買和訪問API
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from ..services.pay_per_use_service import PayPerUseService, AccessLevel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pay-per-use", tags=["pay-per-use"])

# 請求模型
class PurchaseRequest(BaseModel):
    stock_id: str
    insight_type: str
    user_id: int

class ContentRequest(BaseModel):
    stock_id: str
    insight_type: str
    user_id: int
    access_level: str = "basic"

# 響應模型
class PurchaseResponse(BaseModel):
    success: bool
    message: str
    transaction_id: Optional[str] = None
    amount: Optional[float] = None
    access_expires_at: Optional[str] = None
    insight: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    code: Optional[str] = None

class ContentResponse(BaseModel):
    granted: bool
    reason: str
    content: Optional[Dict[str, Any]] = None
    expires_at: Optional[str] = None
    upgrade_suggestion: Optional[Dict[str, Any]] = None
    purchase_option: Optional[Dict[str, Any]] = None

class SpendingSummaryResponse(BaseModel):
    monthly_spending: float
    monthly_transactions: int
    unique_insights: int
    upgrade_threshold_reached: bool
    upgrade_converted: bool
    remaining_to_threshold: float

# 服務實例
pay_per_use_service = PayPerUseService()

@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_alpha_insight(request: PurchaseRequest):
    """購買阿爾法洞察"""
    try:
        result = await pay_per_use_service.purchase_alpha_insight(
            user_id=request.user_id,
            stock_id=request.stock_id,
            insight_type=request.insight_type
        )
        
        return PurchaseResponse(**result)
        
    except Exception as e:
        logger.error(f"購買阿爾法洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="購買處理失敗"
        )

@router.post("/content", response_model=ContentResponse)
async def get_insight_content(request: ContentRequest):
    """獲取洞察內容"""
    try:
        # 驗證訪問級別
        try:
            access_level = AccessLevel(request.access_level)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的訪問級別"
            )
        
        result = await pay_per_use_service.get_insight_content(
            user_id=request.user_id,
            stock_id=request.stock_id,
            insight_type=request.insight_type,
            access_level=access_level
        )
        
        return ContentResponse(
            granted=result.granted,
            reason=result.reason,
            content=result.content,
            expires_at=result.expires_at.isoformat() if result.expires_at else None,
            upgrade_suggestion=result.upgrade_suggestion,
            purchase_option=result.purchase_option
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取洞察內容API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="內容獲取失敗"
        )

@router.get("/spending/{user_id}", response_model=SpendingSummaryResponse)
async def get_user_spending_summary(user_id: int):
    """獲取用戶消費摘要"""
    try:
        result = await pay_per_use_service.get_user_spending_summary(user_id)
        
        return SpendingSummaryResponse(**result)
        
    except Exception as e:
        logger.error(f"獲取用戶消費摘要API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="消費摘要獲取失敗"
        )

@router.get("/insights/{stock_id}")
async def get_available_insights(stock_id: str):
    """獲取可用的洞察類型"""
    try:
        # 這裡可以查詢該股票可用的洞察類型
        available_insights = [
            {
                "insight_type": "technical_alpha",
                "title": "技術分析阿爾法洞察",
                "description": "深度技術指標分析和機構資金流向",
                "price": 5.00,
                "confidence_range": "0.8-0.9"
            },
            {
                "insight_type": "fundamental_alpha", 
                "title": "基本面分析阿爾法洞察",
                "description": "DCF估值模型和競爭優勢分析",
                "price": 5.00,
                "confidence_range": "0.75-0.85"
            },
            {
                "insight_type": "sentiment_alpha",
                "title": "情緒分析阿爾法洞察", 
                "description": "AI語義分析和市場情緒追蹤",
                "price": 5.00,
                "confidence_range": "0.7-0.8"
            }
        ]
        
        return {
            "stock_id": stock_id,
            "available_insights": available_insights,
            "total_insights": len(available_insights)
        }
        
    except Exception as e:
        logger.error(f"獲取可用洞察API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取可用洞察失敗"
        )

@router.get("/preview/{stock_id}/{insight_type}")
async def get_insight_preview(stock_id: str, insight_type: str):
    """獲取洞察預覽（免費用戶可見）"""
    try:
        result = await pay_per_use_service.get_insight_content(
            user_id=0,  # 匿名用戶
            stock_id=stock_id,
            insight_type=insight_type,
            access_level=AccessLevel.BASIC
        )
        
        if result.granted:
            return {
                "stock_id": stock_id,
                "insight_type": insight_type,
                "preview": result.content,
                "purchase_option": result.purchase_option,
                "upgrade_suggestion": result.upgrade_suggestion
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="洞察預覽不可用"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取洞察預覽API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="預覽獲取失敗"
        )

@router.get("/analytics/popular")
async def get_popular_insights():
    """獲取熱門洞察統計"""
    try:
        # 這裡可以實現熱門洞察的統計邏輯
        popular_insights = [
            {
                "stock_id": "2330",
                "insight_type": "technical_alpha",
                "purchase_count": 156,
                "avg_rating": 4.2,
                "last_updated": "2025-08-08T10:30:00"
            },
            {
                "stock_id": "2317", 
                "insight_type": "fundamental_alpha",
                "purchase_count": 89,
                "avg_rating": 4.0,
                "last_updated": "2025-08-08T09:45:00"
            }
        ]
        
        return {
            "popular_insights": popular_insights,
            "total_purchases_today": 245,
            "avg_satisfaction": 4.1
        }
        
    except Exception as e:
        logger.error(f"獲取熱門洞察統計API錯誤: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="統計數據獲取失敗"
        )