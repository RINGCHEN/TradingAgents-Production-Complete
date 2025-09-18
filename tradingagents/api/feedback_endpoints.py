#!/usr/bin/env python3
"""
User Feedback API Endpoints - 用戶反饋系統
天工 (TianGong) - 建立AI價值量化指標的關鍵組件

此模組提供API，用於收集用戶對AI分析結果的明確反饋，
是實現數據驅動、模型迭代的學習閉環的基礎。
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import json
from pathlib import Path
import asyncio

from ..auth.dependencies import get_current_user, CurrentUser
from ..utils.logging_config import get_api_logger

# 初始化路由器和日誌
router = APIRouter(
    prefix="/v1/feedback",
    tags=["User Feedback"],
)

logger = get_api_logger("feedback_endpoints")

# 反饋數據的存儲位置
FEEDBACK_LOG_FILE = Path("feedback_log.json")

# 用於文件寫入的異步鎖
file_lock = asyncio.Lock()

# --- 數據模型 --- 

class AnalysisFeedbackRequest(BaseModel):
    """分析反饋請求模型"""
    analysis_id: str = Field(..., description="被評價的分析ID")
    vote: str = Field(..., description="投票結果，'up' 或 'down'", pattern="^(up|down)$")
    feedback_text: Optional[str] = Field(None, description="用戶的文字反饋", max_length=1000)

class FeedbackResponse(BaseModel):
    """反饋提交成功的回應模型"""
    status: str = "success"
    feedback_id: str
    message: str

# --- API 端點實現 ---

@router.post("/analysis", response_model=FeedbackResponse)
async def submit_analysis_feedback(
    request: AnalysisFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    接收並存儲用戶對單次AI分析的反饋。
    
    - **analysis_id**: 分析結果的唯一ID。
    - **vote**: 'up' 代表有用，'down' 代表沒用。
    - **feedback_text**: 用戶可選填寫的詳細文字反饋。
    """
    feedback_id = f"fb_{current_user.user_id}_{request.analysis_id}"
    
    feedback_entry = {
        "feedback_id": feedback_id,
        "user_id": current_user.user_id,
        "analysis_id": request.analysis_id,
        "vote": request.vote,
        "feedback_text": request.feedback_text,
        "timestamp": datetime.now().isoformat(),
        "user_tier": current_user.membership_tier.value
    }
    
    logger.info(f"收到用戶反饋: {feedback_id}", extra=feedback_entry)
    
    try:
        async with file_lock:
            # 讀取現有數據
            if FEEDBACK_LOG_FILE.exists():
                with open(FEEDBACK_LOG_FILE, "r", encoding="utf-8") as f:
                    try:
                        log_data = json.load(f)
                        if not isinstance(log_data, list):
                            log_data = []
                    except json.JSONDecodeError:
                        log_data = [] # 如果文件損壞，則重新開始
            else:
                log_data = []
            
            # 添加新反饋
            log_data.append(feedback_entry)
            
            # 寫回文件
            with open(FEEDBACK_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=4)

    except Exception as e:
        logger.error(f"寫入反饋日誌失敗: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="無法儲存您的反饋，請稍後再試。"
        )
    
    return FeedbackResponse(
        feedback_id=feedback_id,
        message="感謝您的寶貴反饋！"
    )
