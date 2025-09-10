#!/usr/bin/env python3
"""
Replay Decision API端點 - 生產環境版本
實現4層級用戶價值階梯系統
"""

from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
import json
import base64
import logging
from datetime import datetime, timedelta
import asyncio

# 設置日誌
logger = logging.getLogger(__name__)

# AI分析師導入
from ..agents.analysts.base_analyst import AnalysisState, AnalysisResult
from ..agents.analysts.fundamentals_analyst import FundamentalsAnalyst
from ..agents.analysts.technical_analyst import TechnicalAnalyst
from ..agents.analysts.news_analyst import NewsAnalyst
from ..agents.analysts.risk_analyst import RiskAnalyst
from ..agents.analysts.investment_planner import InvestmentPlanner

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
        created_at_str = payload.get("registered_at")
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                days_since_creation = (datetime.now() - created_at.replace(tzinfo=None)).days
                trial_days_remaining = max(0, 7 - days_since_creation)
            except:
                trial_days_remaining = 5  # 預設值
    
    return tier, trial_days_remaining

async def get_stock_analysis(stock_id: str, user_tier: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """獲取股票分析（真實模型整合版）"""
    
    logger.info(f"開始為股票 {stock_id} 進行真實AI分析...")
    
    # 1. 初始化所有分析師
    analysts = {
        "fundamentals_analyst": FundamentalsAnalyst(config={}),
        "technical_analyst": TechnicalAnalyst(config={}),
        "news_analyst": NewsAnalyst(config={}),
        # "risk_analyst": RiskAnalyst(config={}),
        # "investment_planner": InvestmentPlanner(config={})
    }
    
    # 2. 創建共享的分析狀態
    state = AnalysisState(
        stock_id=stock_id,
        analysis_date=datetime.now().strftime('%Y-%m-%d'),
        user_context=user_context
    )
    
    # 3. 並發執行所有分析師的分析
    tasks = [analyst.analyze(state) for analyst in analysts.values()]
    results: List[AnalysisResult] = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 4. 組合分析結果
    combined_analysis = {}
    final_recommendation = {
        "actions": [],
        "confidences": [],
        "reasons": []
    }

    for result in results:
        if isinstance(result, AnalysisResult):
            analyst_type = result.analysis_type.value
            combined_analysis[analyst_type] = {
                "recommendation": result.recommendation,
                "confidence": result.confidence,
                "reasoning": result.reasoning[0] if result.reasoning else ""
            }
            final_recommendation["actions"].append(result.recommendation)
            final_recommendation["confidences"].append(result.confidence)
            final_recommendation["reasons"].extend(result.reasoning)
        else:
            logger.error(f"分析時發生錯誤: {result}")

    # 5. 根據用戶層級決定是否包含最終建議
    if user_tier in ["trial", "paid"]:
        # 簡單的投票機制決定最終建議
        action = max(set(final_recommendation["actions"]), key=final_recommendation["actions"].count) if final_recommendation["actions"] else "HOLD"
        confidence = round(sum(final_recommendation["confidences"]) / len(final_recommendation["confidences"]), 2) if final_recommendation["confidences"] else 0.5
        
        combined_analysis["recommendation"] = {
            "action": action,
            "confidence": confidence * 100,
            "target_price": None, # 暫不提供
            "reasoning": ". ".join(list(set(final_recommendation["reasons"])))
        }

    logger.info(f"股票 {stock_id} 的真實AI分析完成")
    return combined_analysis

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
        # 確定用戶層級和上下文
        user_tier, trial_days_remaining = determine_user_tier(authorization)
        user_payload = decode_test_token(authorization) if authorization else {}
        user_context = {
            "user_id": user_payload.get("user_id", "anonymous"),
            "membership_tier": user_tier
        }
        
        # 處理股票代號
        stock_symbol = request.stock_symbol or request.stock_id or "2330"
        
        logger.info(f"處理 {stock_symbol} 的請求，用戶層級：{user_tier}")
        
        # 獲取分析數據
        analysis = await get_stock_analysis(stock_symbol, user_tier, user_context)
        
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
        logger.error(f"處理請求時發生錯誤: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"內部服務器錯誤: {str(e)}")

# 健康檢查端點
@router.get("/replay/health")
async def replay_health():
    """Replay服務健康檢查"""
    return {
        "service": "replay_decision",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0-real-engine"
    }
