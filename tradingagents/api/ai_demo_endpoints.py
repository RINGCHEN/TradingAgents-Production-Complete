#!/usr/bin/env python3
"""
AI演示功能 API 端點
整合AI分析師演示功能與會員系統的REST API端點

提供方案A混合架構的API接口：
1. 創建AI演示會話
2. 獲取演示結果
3. 會員等級功能查詢
4. 使用量追蹤和統計
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ..database.database import get_db
from ..models.user import User
from ..utils.auth import get_current_user, get_current_user_optional
from ..utils.logging_config import get_logger
from ..utils.ai_demo_integrator import (
    get_ai_demo_integrator, AIDemoIntegrator, 
    create_ai_demo_for_member, get_member_ai_features
)
from ..utils.member_permission_bridge import check_user_can_analyze

logger = get_logger(__name__)
router = APIRouter(prefix="/ai-demo", tags=["ai-demo"])

# Pydantic 模型
class AIDemoRequest(BaseModel):
    """AI演示請求模型"""
    stock_symbol: str = Field(..., description="股票代碼", example="2330.TW")
    analyst_preferences: Optional[List[str]] = Field(
        None, 
        description="偏好的分析師類型", 
        example=["technical_analyst", "fundamentals_analyst"]
    )

class AIDemoResponse(BaseModel):
    """AI演示回應模型"""
    success: bool
    request_id: Optional[str] = None
    selected_analysts: Optional[List[str]] = None
    estimated_completion_time: Optional[datetime] = None
    demo_limitations: Optional[List[str]] = None
    status: Optional[str] = None
    error: Optional[str] = None
    message: Optional[str] = None

class DemoResultResponse(BaseModel):
    """演示結果回應模型"""
    request_id: str
    user_id: str
    stock_symbol: str
    status: str
    analysts_used: List[str]
    analysis_data: Dict[str, Any]
    start_time: str
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    demo_limitations: List[str]

class TierFeaturesResponse(BaseModel):
    """會員等級功能回應模型"""
    membership_tier: str
    available_analysts: List[Dict[str, str]]
    max_concurrent_demos: int
    daily_analysis_limit: int
    limitations: List[str]
    upgrade_benefits: List[str]

# API 端點實現

@router.post("/create", response_model=AIDemoResponse)
async def create_ai_demo_session(
    demo_request: AIDemoRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    創建AI演示會話
    
    為已登入的會員創建AI分析師演示會話，根據會員等級提供相應的分析功能。
    """
    try:
        integrator = get_ai_demo_integrator()
        
        # 獲取用戶會員等級
        user_tier = getattr(current_user, 'membership_tier', 'FREE')
        
        # 創建演示會話
        demo_result = await integrator.create_ai_demo_session(
            user_id=str(current_user.id),
            stock_symbol=demo_request.stock_symbol,
            analyst_preferences=demo_request.analyst_preferences
        )
        
        # 記錄使用量 (後台任務)
        if demo_result.get('success'):
            background_tasks.add_task(
                _record_demo_usage, 
                current_user.id, 
                demo_request.stock_symbol,
                user_tier
            )
        
        # 轉換回應格式
        return AIDemoResponse(
            success=demo_result.get('success', False),
            request_id=demo_result.get('request_id'),
            selected_analysts=demo_result.get('selected_analysts'),
            estimated_completion_time=demo_result.get('estimated_completion_time'),
            demo_limitations=demo_result.get('demo_limitations'),
            status=demo_result.get('status'),
            error=demo_result.get('error'),
            message=demo_result.get('message')
        )
        
    except Exception as e:
        logger.error(f"創建AI演示會話失敗 (用戶: {current_user.id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建AI演示會話時發生錯誤"
        )

@router.get("/result/{request_id}", response_model=DemoResultResponse)
async def get_demo_result(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取AI演示結果
    
    根據演示請求ID獲取分析結果。只能查看自己的演示結果。
    """
    try:
        integrator = get_ai_demo_integrator()
        
        demo_result = await integrator.get_demo_result(request_id, str(current_user.id))
        
        if not demo_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="演示結果不存在或無權限訪問"
            )
        
        return DemoResultResponse(**demo_result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取演示結果失敗 (用戶: {current_user.id}, 請求: {request_id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取演示結果時發生錯誤"
        )

@router.get("/user/sessions")
async def list_user_demo_sessions(
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="返回記錄數量"),
    db: Session = Depends(get_db)
):
    """
    列出用戶的AI演示會話歷史
    
    獲取當前用戶的所有AI演示會話記錄，按時間排序。
    """
    try:
        integrator = get_ai_demo_integrator()
        
        demo_sessions = await integrator.list_user_demos(str(current_user.id))
        
        # 限制返回數量
        return {
            "user_id": str(current_user.id),
            "total_sessions": len(demo_sessions),
            "sessions": demo_sessions[:limit],
            "retrieved_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"列出用戶演示會話失敗 (用戶: {current_user.id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取演示會話歷史時發生錯誤"
        )

@router.get("/tier/{tier}/features", response_model=TierFeaturesResponse)
async def get_tier_ai_features(
    tier: str,
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    獲取指定會員等級的AI功能
    
    查詢特定會員等級可使用的AI分析師功能和限制。
    """
    try:
        # 驗證等級名稱
        valid_tiers = ['FREE', 'GOLD', 'DIAMOND']
        if tier.upper() not in valid_tiers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"無效的會員等級: {tier}. 有效等級: {', '.join(valid_tiers)}"
            )
        
        # 獲取AI功能特性
        features = await get_member_ai_features(tier.upper())
        
        return TierFeaturesResponse(**features)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取會員等級AI功能失敗 (等級: {tier}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取會員等級功能時發生錯誤"
        )

@router.get("/current-user/features", response_model=TierFeaturesResponse)
async def get_current_user_ai_features(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取當前用戶的AI功能
    
    根據當前用戶的會員等級返回可用的AI分析功能。
    """
    try:
        user_tier = getattr(current_user, 'membership_tier', 'FREE')
        
        features = await get_member_ai_features(user_tier)
        
        return TierFeaturesResponse(**features)
        
    except Exception as e:
        logger.error(f"獲取用戶AI功能失敗 (用戶: {current_user.id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取用戶AI功能時發生錯誤"
        )

@router.post("/guest/preview")
async def create_guest_preview_demo(
    demo_request: AIDemoRequest,
    background_tasks: BackgroundTasks
):
    """
    創建訪客預覽演示
    
    為未登入的訪客提供有限的AI分析演示，用於展示產品功能。
    """
    try:
        # 為訪客創建臨時用戶ID
        guest_user_id = f"guest_{int(datetime.now().timestamp())}"
        
        # 使用免費會員等級創建演示
        demo_result = await create_ai_demo_for_member(
            user_id=guest_user_id,
            stock_symbol=demo_request.stock_symbol,
            tier='FREE',
            analyst_preferences=['technical_analyst']  # 限制訪客只能使用技術分析
        )
        
        # 添加訪客特有的限制說明
        if demo_result.get('success'):
            demo_result['demo_limitations'] = [
                "訪客演示功能，僅供體驗",
                "註冊會員享受更多分析師",
                "升級會員獲得完整功能"
            ] + demo_result.get('demo_limitations', [])
        
        return AIDemoResponse(
            success=demo_result.get('success', False),
            request_id=demo_result.get('request_id'),
            selected_analysts=demo_result.get('selected_analysts'),
            estimated_completion_time=demo_result.get('estimated_completion_time'),
            demo_limitations=demo_result.get('demo_limitations'),
            status=demo_result.get('status'),
            error=demo_result.get('error'),
            message=demo_result.get('message', "訪客演示會話已創建")
        )
        
    except Exception as e:
        logger.error(f"創建訪客演示失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建訪客演示時發生錯誤"
        )

@router.get("/guest/result/{request_id}")
async def get_guest_demo_result(request_id: str):
    """
    獲取訪客演示結果
    
    訪客可以查看自己的演示結果，無需登入。
    """
    try:
        integrator = get_ai_demo_integrator()
        
        # 從request_id提取guest_user_id
        if not request_id.startswith("demo_guest_"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無效的訪客演示請求ID"
            )
        
        # 提取用戶ID
        parts = request_id.split("_")
        if len(parts) >= 3:
            guest_user_id = f"{parts[1]}_{parts[2]}"
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="無效的演示請求格式"
            )
        
        demo_result = await integrator.get_demo_result(request_id, guest_user_id)
        
        if not demo_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="演示結果不存在"
            )
        
        # 添加註冊提示
        demo_result['registration_prompt'] = "註冊成為會員享受更多AI分析功能"
        
        return demo_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取訪客演示結果失敗 (請求: {request_id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取訪客演示結果時發生錯誤"
        )

@router.get("/stats/usage")
async def get_demo_usage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取AI演示使用統計
    
    返回當前用戶的AI演示使用情況和配額信息。
    """
    try:
        integrator = get_ai_demo_integrator()
        
        # 獲取用戶上下文
        user_context = await integrator.permission_bridge.get_user_context(str(current_user.id))
        
        if not user_context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶上下文不存在"
            )
        
        # 獲取使用統計
        usage_stats = await integrator.permission_bridge.get_user_analysis_stats(user_context)
        
        # 獲取演示會話統計
        user_demos = await integrator.list_user_demos(str(current_user.id))
        
        return {
            "user_id": str(current_user.id),
            "membership_tier": user_context.membership_tier,
            "daily_usage": usage_stats.get('daily_usage', {}),
            "monthly_usage": usage_stats.get('monthly_usage', {}),
            "concurrent_usage": usage_stats.get('concurrent_usage', {}),
            "demo_sessions": {
                "total_count": len(user_demos),
                "recent_sessions": user_demos[:5]
            },
            "available_features": usage_stats.get('enabled_features', []),
            "restrictions": usage_stats.get('restrictions', []),
            "retrieved_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取使用統計失敗 (用戶: {current_user.id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取使用統計時發生錯誤"
        )

@router.delete("/cleanup/expired")
async def cleanup_expired_demos(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    清理過期演示會話 (管理員功能)
    
    清理超過24小時的已完成演示會話，釋放系統資源。
    """
    try:
        # 簡單的管理員檢查 (這裡應該使用更嚴格的權限檢查)
        user_email = getattr(current_user, 'email', '')
        if not user_email or 'admin' not in user_email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="需要管理員權限"
            )
        
        integrator = get_ai_demo_integrator()
        
        # 後台任務執行清理
        background_tasks.add_task(integrator.cleanup_expired_demos, 24)
        
        return {
            "message": "清理任務已開始",
            "initiated_by": user_email,
            "initiated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清理過期演示失敗 (操作者: {current_user.id}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="執行清理任務時發生錯誤"
        )

# 輔助函數
async def _record_demo_usage(user_id: int, stock_symbol: str, tier: str):
    """記錄演示使用量 (後台任務)"""
    try:
        # 這裡可以實現更詳細的使用量記錄邏輯
        logger.info(f"記錄AI演示使用: 用戶={user_id}, 股票={stock_symbol}, 等級={tier}")
        
        # TODO: 實現實際的使用量記錄到數據庫
        
    except Exception as e:
        logger.error(f"記錄演示使用量失敗: {str(e)}")

# 健康檢查端點
@router.get("/health")
async def ai_demo_health_check():
    """AI演示系統健康檢查"""
    try:
        integrator = get_ai_demo_integrator()
        
        return {
            "status": "healthy",
            "service": "AI Demo Integration",
            "version": "1.0.0",
            "active_demos": len(integrator.active_demos),
            "checked_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"AI演示健康檢查失敗: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }