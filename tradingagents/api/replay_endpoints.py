#!/usr/bin/env python3
"""
Replay Decision API端點 - 生產環境版本
實現4層級用戶價值階梯系統
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any
import json
import base64
import logging
from datetime import datetime, timedelta

# 設置日誌
logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1", tags=["replay"])

class ReplayDecisionRequest(BaseModel):
    stock_symbol: Optional[str] = None  # CLAUDE格式
    stock_id: Optional[str] = None      # GEMINI格式
    trade_price: Optional[float] = None
    trade_date: Optional[str] = None
    
class ReplayDecisionResponse(BaseModel):
    model_config = ConfigDict(exclude_none=True)  # Pydantic v2語法
    user_tier: str = Field(..., description="用戶層級")
    trial_days_remaining: Optional[int] = Field(None, description="試用期剩餘天數")
    analysis: Dict[str, Any] = Field(..., description="股票分析結果")
    upgrade_prompt: Optional[str] = Field(None, description="升級提示")

def decode_test_token(token: str) -> Dict[str, Any]:
    """解碼測試token - 修復JWT解析"""
    try:
        # 從Bearer token中提取JWT token
        if token.startswith('Bearer '):
            token = token[7:]  # 移除 "Bearer " 前綴
        
        # JWT token格式: header.payload.signature
        # 我們只需要payload部分
        parts = token.split('.')
        if len(parts) >= 2:
            payload_part = parts[1]
            # JWT使用URL安全的base64編碼，需要補充padding
            payload_part += '=' * (4 - len(payload_part) % 4)
            
            # Base64解碼
            decoded = base64.urlsafe_b64decode(payload_part).decode('utf-8')
            payload = json.loads(decoded)
            
            # 提取關鍵信息
            result = {
                "tier": payload.get("tier", payload.get("user_role", "visitor")),
                "user_id": payload.get("user_id", "anonymous"),
                "registered_at": payload.get("registered_at", None)
            }
            return result
        else:
            # 如果不是JWT格式，嘗試直接Base64解碼
            decoded = base64.b64decode(token).decode('utf-8')
            payload = json.loads(decoded)
            return payload
    except Exception as e:
        logger.warning(f"Token decode error: {e}")  # 調試信息
        return {"tier": "visitor"}

def determine_user_tier(authorization_header: Optional[str]) -> tuple[str, Optional[int]]:
    """確定用戶層級和試用天數"""
    if not authorization_header:
        return "visitor", None
    
    payload = decode_test_token(authorization_header)
    if not payload:
        return "visitor", None
    
    tier = payload.get("tier", "visitor")
    
    # 計算試用期剩餘天數
    trial_days_remaining = None
    if tier == "trial":
        created_at_str = payload.get("created_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                days_since_creation = (datetime.now() - created_at.replace(tzinfo=None)).days
                trial_days_remaining = max(0, 7 - days_since_creation)
            except:
                trial_days_remaining = 5  # 預設值
    
    return tier, trial_days_remaining

def get_stock_analysis(stock_symbol: str, user_tier: str) -> Dict[str, Any]:
    """獲取股票分析（模擬數據）"""
    
    base_analysis = {
        "technical_analysis": f"📈 {stock_symbol} 技術分析顯示目前處於上升趨勢，RSI指標為65，MACD呈現黃金交叉格局。",
        "fundamental_analysis": f"💰 {stock_symbol} 基本面分析：本季EPS成長15%，ROE維持在20%以上，財務結構穩健。",
        "news_sentiment": f"📰 {stock_symbol} 近期新聞情感分析：市場對該股票保持樂觀態度，機構投資人增持。"
    }
    
    # 只有試用和付費用戶才能看到投資建議
    if user_tier in ["trial", "paid"]:
        base_analysis["recommendation"] = {
            "action": "buy",
            "confidence": 85,
            "target_price": 580,
            "reasoning": "基於技術面和基本面分析，建議適量買入並設定停利點於600元。"
        }
    
    return base_analysis

def get_upgrade_prompt(user_tier: str) -> Optional[str]:
    """獲取升級提示"""
    if user_tier == "visitor":
        return "註冊立即享受7天完整功能體驗，包含專業投資建議！"
    elif user_tier == "free":
        return "升級至付費會員，獲得完整投資建議和目標價位分析！"
    return None

@router.post("/replay/decision", response_model=ReplayDecisionResponse)
async def get_replay_decision(
    request: ReplayDecisionRequest,
    authorization: Optional[str] = Header(None)
) -> ReplayDecisionResponse:
    """
    獲取股票決策復盤分析
    根據用戶層級返回不同詳細度的分析結果
    """
    try:
        # 確定用戶層級
        user_tier, trial_days_remaining = determine_user_tier(authorization)
        
        # 處理股票代號
        stock_symbol = request.stock_symbol or request.stock_id or "2330"
        
        logger.info(f"處理 {stock_symbol} 的請求，用戶層級：{user_tier}")
        
        # 獲取分析數據
        analysis = get_stock_analysis(stock_symbol, user_tier)
        
        # 構建回應
        response_data = {
            "user_tier": user_tier,
            "analysis": analysis
        }
        
        # 添加試用期資訊
        if trial_days_remaining is not None:
            response_data["trial_days_remaining"] = trial_days_remaining
        
        # 添加升級提示
        upgrade_prompt = get_upgrade_prompt(user_tier)
        if upgrade_prompt:
            response_data["upgrade_prompt"] = upgrade_prompt
        
        return ReplayDecisionResponse(**response_data)
        
    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")

# 健康檢查端點
@router.get("/replay/health")
async def replay_health():
    """Replay服務健康檢查"""
    return {
        "service": "replay_decision",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
