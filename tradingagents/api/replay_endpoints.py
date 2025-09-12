from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import asyncio
import json

from ..auth.dependencies import get_current_user
from ..auth.permissions import require_permission, ResourceType, Action
from ..utils.user_context import UserContext, TierType
from ..services.analysts_service import get_analysts_service, AnalysisState, create_analysis_state

# 建立一個新的 API 路由器
router = APIRouter(
    prefix="/replay",
    tags=["AI Decision Replay"],
)

# --- 數據模型 (我們的 API 契約) ---

class DecisionReplayRequest(BaseModel):
    """
    前端發送的請求模型
    """
    stock_id: str = Field(..., description="股票代號", example="2330")
    trade_price: float = Field(..., description="交易價格", example=650.0)
    trade_date: date = Field(..., description="交易日期", example="2025-08-20")

# Enhanced Models based on GEMINI's rich structure

class StoryChapter(BaseModel):
    """
    故事章節模型 - GEMINI 增強版
    """
    type: str = Field("chapter", description="章節類型")
    title: str = Field(..., description="章節標題", example="第一章：營收與盈利能力")
    content: str = Field(..., description="章節內容詳述")

class OverallAssessment(BaseModel):
    """
    綜合評估模型 - GEMINI 增強版
    """
    rating: str = Field(..., description="評估評級", example="中性偏多")
    summary: str = Field(..., description="評估總結")
    confidence: Optional[float] = Field(None, description="信心度分數", ge=0, le=1)

class EnhancedAnalystOpinion(BaseModel):
    """
    增強版 AI 分析師意見模型 - 基於 GEMINI 的豐富結構
    """
    replay_id: str = Field(..., description="復盤分析ID")
    stock_id: str = Field(..., description="股票代號") 
    decision_point: str = Field(..., description="決策時間點")
    analyst_name: str = Field(..., description="分析師名稱")
    analyst_avatar: str = Field(..., description="分析師頭像")
    title: str = Field(..., description="分析報告標題")
    story: List[StoryChapter] = Field(..., description="多章節故事結構")
    key_takeaways: List[str] = Field(..., description="關鍵要點列表")
    overall_assessment: OverallAssessment = Field(..., description="綜合評估")
    historical_accuracy: Optional[float] = Field(None, description="歷史準確率", ge=0, le=1)


class EnhancedDecisionReplayResponse(BaseModel):
    """
    增強版決策復盤回應模型 - 基於 GEMINI 的豐富結構
    """
    # Meta information
    request_info: Dict[str, Any] = Field(..., description="請求信息摘要")
    generated_at: str = Field(..., description="生成時間戳")
    
    # Rich analyst opinions using GEMINI's structure
    analyst_opinions: List[EnhancedAnalystOpinion] = Field(..., description="5個專業AI分析師的詳細意見")
    
    # Summary and shareability 
    overall_narrative: str = Field(..., description="綜合故事敘述")
    top_shareable_quote: str = Field(..., description="最適合分享的金句")
    overall_confidence_score: int = Field(..., description="綜合信心評分", ge=0, le=100)
    
    # Additional insights
    risk_level: str = Field(..., description="整體風險等級", example="中等")
    recommended_action: str = Field(..., description="建議行動", example="持有觀察")
    
    # Tier-specific fields
    upgrade_required: bool = Field(False, description="是否需要升級以查看完整內容")
    trial_days_remaining: Optional[int] = Field(None, description="試用期剩餘天數")


# --- API 端點實現 ---

@router.get("/test")
async def test_replay_endpoint():
    """測試端點 - 確認路由正常工作"""
    return {"status": "ok", "message": "Replay API is working!", "timestamp": datetime.now().isoformat()}

@router.post("/decision", response_model=EnhancedDecisionReplayResponse)
@require_permission(ResourceType.ANALYSIS, Action.EXECUTE)
async def get_decision_replay(
    request: DecisionReplayRequest,
    user_context: UserContext = Depends(get_current_user)
):
    """
    接收交易決策請求，返回由真實AI模型驅動的故事性復盤分析。
    """
    analysts_service = get_analysts_service()
    available_analysts = [
        analyst['analyst_id'] for analyst in analysts_service.list_analysts() 
        if analyst['available'] and 'base' not in analyst['analyst_id']
    ]

    if not available_analysts:
        raise HTTPException(status_code=503, detail="沒有可用的分析師服務。")

    analysis_state = create_analysis_state(
        stock_id=request.stock_id,
        user_context=user_context.dict(),
        trade_info={
            "trade_price": request.trade_price,
            "trade_date": str(request.trade_date)
        }
    )

    # 並行執行所有分析師的分析
    tasks = [analysts_service.analyze(analyst_id, analysis_state) for analyst_id in available_analysts]
    analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

    # 處理分析結果
    enhanced_opinions = []
    total_confidence = 0
    valid_results_count = 0

    for i, result in enumerate(analysis_results):
        analyst_id = available_analysts[i]
        if isinstance(result, Exception):
            # 如果分析失敗，可以記錄日誌並跳過
            # logger.error(f"分析師 {analyst_id} 分析失敗: {result}")
            continue

        # 從服務獲取性能指標
        perf_metrics = analysts_service.get_performance_metrics(analyst_id)
        
        # 將 AnalysisResult 轉換為 EnhancedAnalystOpinion
        # 注意：這一步需要一個轉換函數，這裡做一個簡化實現
        opinion = EnhancedAnalystOpinion(
            replay_id=f"replay_{request.stock_id}_{analyst_id}_{int(datetime.now().timestamp())}",
            stock_id=f"{request.stock_id}.TW",
            decision_point=f"{request.trade_date}T10:00:00Z",
            analyst_name=result.metadata.get("analyst_name", analyst_id.replace('_', ' ').title()),
            analyst_avatar=result.metadata.get("avatar", f"avatars/{analyst_id}.svg"),
            title=f"{result.metadata.get('title_prefix', 'AI分析')}：{request.stock_id} 的 {result.analysis_type.value} 復盤",
            story=[StoryChapter(title=f"第{i+1}章", content=content) for i, content in enumerate(result.reasoning)],
            key_takeaways=result.metadata.get("key_takeaways", result.reasoning[:3]),
            overall_assessment=OverallAssessment(
                rating=result.metadata.get("rating", "中性"),
                summary=result.reasoning[-1] if result.reasoning else "沒有足夠的摘要。",
                confidence=result.confidence
            ),
            historical_accuracy=perf_metrics.get('accuracy_rate') if perf_metrics else None
        )
        enhanced_opinions.append(opinion)
        total_confidence += result.confidence
        valid_results_count += 1

    if valid_results_count == 0:
        raise HTTPException(status_code=503, detail="所有分析師服務均未能成功返回結果。" )

    overall_confidence_score = int((total_confidence / valid_results_count) * 100) if valid_results_count > 0 else 0

    # 創建回應
    enhanced_response = EnhancedDecisionReplayResponse(
        request_info={
            "stock_id": request.stock_id,
            "trade_price": request.trade_price,
            "trade_date": str(request.trade_date)
        },
        generated_at=datetime.now().isoformat(),
        analyst_opinions=enhanced_opinions,
        overall_narrative=f"關於您在 {request.trade_date} 的交易決策，我們的AI分析師團隊從 {len(enhanced_opinions)} 個維度進行了深度復盤。",
        top_shareable_quote=enhanced_opinions[0].key_takeaways[0] if enhanced_opinions and enhanced_opinions[0].key_takeaways else "AI深度分析，助您做出更明智的決策。",
        overall_confidence_score=overall_confidence_score,
        risk_level="中等",  # 可由風險分析師提供
        recommended_action="持有觀察" # 可由投資組合分析師提供
    )

    # --- Tiered Access Logic ---
    is_trial_user = user_context.membership_tier == TierType.FREE and \
                    (datetime.now() - user_context.created_at) < timedelta(days=7)

    if user_context.membership_tier == TierType.FREE and not is_trial_user:
        # Free user after trial
        enhanced_response.upgrade_required = True
        enhanced_response.recommended_action = "升級至付費會員以解鎖建議"
        enhanced_response.overall_narrative = "您的決策復盤已生成。升級至付費會員以解鎖所有AI分析師的完整見解和投資建議。"
        enhanced_response.top_shareable_quote = "想知道AI對這次交易的看法嗎？註冊會員即可查看完整分析！"
        
        for opinion in enhanced_response.analyst_opinions:
            opinion.key_takeaways = ["升級以解鎖關鍵要點。"]
            opinion.overall_assessment.summary = "升級至付費會員以查看完整評估。"
            opinion.story = opinion.story[:1]
            opinion.story[0].content = "升級至付費會員以閱讀完整分析故事..."

    elif is_trial_user:
        # Trial user
        days_left = 7 - (datetime.now() - user_context.created_at).days
        enhanced_response.trial_days_remaining = days_left
        enhanced_response.overall_narrative += f"\n\n**您的完整功能試用期還剩下 {days_left} 天。**"

    return enhanced_response


# =================================================================
# ================= TEMPORARY INTERNAL TEST ROUTE =================
# =================================================================
# NOTE: This entire block should be removed after verification is complete.

class InternalTestResponse(BaseModel):
    """Response model for the internal test endpoint."""
    message: str
    stock_id: str
    available_analysts: List[str]
    analysis_results: List[Dict[str, Any]]

@router.post(
    "/internal-test-analysis",
    response_model=InternalTestResponse,
    tags=["Internal Testing"],
    include_in_schema=False  # Hide from public OpenAPI docs
)
async def internal_test_analysis(request: DecisionReplayRequest):
    """
    [INTERNAL-TESTING-ONLY]
    This is a temporary, unprotected endpoint to verify the core AI analysis service.
    It bypasses authentication and returns raw analysis results.
    THIS MUST BE REMOVED BEFORE FINAL PRODUCTION.
    """
    analysts_service = get_analysts_service()
    available_analysts = [
        analyst['analyst_id'] for analyst in analysts_service.list_analysts()
        if analyst['available'] and 'base' not in analyst['analyst_id']
    ]

    if not available_analysts:
        raise HTTPException(status_code=503, detail="No available analyst services.")

    # Create a mock user context with DIAMOND tier to bypass permission checks for testing
    mock_user_context = {
        "user_id": "internal_test_user",
        "membership_tier": "diamond",
        "created_at": datetime.now().isoformat(),
        "permissions": {"can_use_advanced_analysis": True, "can_export_data": True, "can_use_premium_features": True},
        "usage_stats": {"daily_analyses": 0}
    }

    analysis_state = create_analysis_state(
        stock_id=request.stock_id,
        user_context=mock_user_context,
        trade_info={
            "trade_price": request.trade_price,
            "trade_date": str(request.trade_date)
        }
    )

    tasks = [analysts_service.analyze(analyst_id, analysis_state) for analyst_id in available_analysts]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_results = []
    for i, result in enumerate(results):
        analyst_id = available_analysts[i]
        if isinstance(result, Exception):
            processed_results.append({
                "analyst_id": analyst_id,
                "status": "error",
                "detail": str(result)
            })
        else:
            # The result from the service is an AnalysisResult Pydantic model
            processed_results.append({
                "analyst_id": analyst_id,
                "status": "success",
                "data": result.dict()
            })

    return InternalTestResponse(
        message="Internal test successful. Raw data returned.",
        stock_id=request.stock_id,
        available_analysts=available_analysts,
        analysis_results=processed_results
    )

# ================= END OF TEMPORARY TEST ROUTE ================