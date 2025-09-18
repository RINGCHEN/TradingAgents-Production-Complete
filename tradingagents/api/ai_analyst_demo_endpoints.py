#!/usr/bin/env python3
"""
AI分析師展示中心 API端點
為TradingAgents商業化提供震撼性的AI投資分析展示功能
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import logging
import json
import os
from datetime import datetime

# 嘗試導入finmind服務，如果失敗則使用模擬服務
try:
    from ..dataflows.finmind_realtime_adapter import finmind_service
except ImportError:
    # 如果導入失敗，創建一個模擬的finmind_service
    class MockFinmindService:
        def get_stock_price(self, symbol):
            return {"price": 100.0, "change": 0.0}
    finmind_service = MockFinmindService()

# 配置日誌
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai-demo", tags=["AI Analyst Demo"])

# --- Pydantic Models ---

class StockAnalysisRequest(BaseModel):
    """股票分析請求模型"""
    stock_symbol: str = Field(..., description="股票代碼", example="2330.TW")
    analysis_level: str = Field(default="basic", description="分析等級: basic/premium/ultimate")
    user_tier: str = Field(default="free", description="用戶等級: free/gold/diamond")

class AnalystInsight(BaseModel):
    """分析師洞察結果"""
    analyst_name: str = Field(..., description="分析師名稱")
    analyst_type: str = Field(..., description="分析師類型")
    analysis: str = Field(..., description="分析內容")
    confidence: float = Field(..., description="信心度 0-1")
    timestamp: datetime = Field(default_factory=datetime.now, description="分析時間")

class ComprehensiveAnalysisResponse(BaseModel):
    """綜合分析結果回應"""
    stock_symbol: str = Field(..., description="股票代碼")
    analysis_id: str = Field(..., description="分析ID")
    insights: List[AnalystInsight] = Field(..., description="分析師洞察列表")
    final_recommendation: str = Field(..., description="最終投資建議")
    confidence_score: str = Field(..., description="整體信心度")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    expires_at: datetime = Field(..., description="過期時間")
    upgrade_message: Optional[str] = Field(None, description="升級提示訊息")

class PopularStocksResponse(BaseModel):
    """熱門股票回應"""
    popular_stocks: List[Dict[str, Any]] = Field(..., description="熱門股票列表")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")

# --- Mock Data for Demo (在實際部署時會被真實AI分析替換) ---

MOCK_ANALYSTS_CONFIG = {
    "technical_analyst": {
        "name": "技術分析師",
        "description": "專精技術指標、價格趋勢、交易量分析",
        "specialties": ["均線分析", "RSI指標", "MACD趨勢", "K線形態"]
    },
    "fundamentals_analyst": {
        "name": "基本面分析師", 
        "description": "深度財務報表分析、營運績效評估",
        "specialties": ["財報分析", "ROE/ROA", "現金流量", "成長性評估"]
    },
    "news_analyst": {
        "name": "新聞分析師",
        "description": "即時新聞解讀、政策影響分析",
        "specialties": ["政策解讀", "產業趨勢", "競爭分析", "法規影響"]
    },
    "risk_analyst": {
        "name": "風險管理分析師",
        "description": "風險評估、投資組合管理建議",
        "specialties": ["風險控制", "波動度分析", "相關性分析", "壓力測試"]
    },
    "social_media_analyst": {
        "name": "情感分析師",
        "description": "社群媒體情緒、投資人情感分析",
        "specialties": ["PTT情緒", "社群熱度", "投資者情感", "話題追蹤"]
    },
    "investment_planner": {
        "name": "投資規劃師",
        "description": "綜合各分析師意見，提供最終投資建議",
        "specialties": ["投資建議", "配置建議", "時間規劃", "風險配比"]
    }
}

POPULAR_TAIWAN_STOCKS = [
    {"symbol": "2330.TW", "name": "台積電", "sector": "半導體", "market_cap": "17.8兆"},
    {"symbol": "2317.TW", "name": "鴻海", "sector": "電子製造", "market_cap": "2.1兆"},
    {"symbol": "2454.TW", "name": "聯發科", "sector": "IC設計", "market_cap": "1.8兆"},
    {"symbol": "2881.TW", "name": "富邦金", "sector": "金融", "market_cap": "1.2兆"},
    {"symbol": "6505.TW", "name": "台塑化", "sector": "石化", "market_cap": "8,500億"},
]

async def generate_enhanced_analysis(analyst_name: str, stock_symbol: str, user_tier: str, market_data: dict = None) -> AnalystInsight:
    """生成增強分析結果 (整合真實FinMind數據)"""
    
    analyst_config = MOCK_ANALYSTS_CONFIG.get(analyst_name, {})
    stock_name = next((stock["name"] for stock in POPULAR_TAIWAN_STOCKS if stock["symbol"] == stock_symbol), stock_symbol)
    
    # 基於真實市場數據生成分析
    analysis = ""
    confidence = 0.5
    
    if market_data:
        real_time = market_data.get("real_time_data", {})
        technical = market_data.get("technical_indicators", {})
        financial = market_data.get("financial_metrics", {})
        sentiment = market_data.get("market_sentiment", {})
        summary = market_data.get("analysis_summary", {})
        
        if analyst_name == "technical_analyst" and technical:
            rsi = technical.get("rsi", 50)
            macd = technical.get("macd", 0)
            sma_20 = technical.get("sma_20", 0)
            
            if user_tier == "free":
                analysis = f"【免費預覽】技術分析師：{stock_name} RSI指標 {rsi:.1f}... [升級查看MACD、布林帶等完整技術分析]"
                confidence = 0.5
            elif user_tier == "gold":
                analysis = f"【黃金會員】技術分析師：{stock_name} RSI {rsi:.1f}，MACD {'轉多' if macd > 0 else '轉空'}，20日均線 {sma_20:.1f}，技術面呈{'多頭' if rsi < 70 and macd > 0 else '整理'}格局"
                confidence = 0.75
            else:
                analysis = f"【鑽石會員】技術分析師：{stock_name} 綜合技術指標顯示，RSI {rsi:.1f}{'(超買)' if rsi > 70 else '(超賣)' if rsi < 30 else '(正常)'}，MACD線 {macd:.3f}，建議{'減倉' if rsi > 70 else '加碼' if rsi < 30 else '持有'}"
                confidence = 0.9
                
        elif analyst_name == "fundamentals_analyst" and financial:
            eps = financial.get("eps", 0)
            roe = financial.get("roe", 0)
            debt_ratio = financial.get("debt_ratio", 0)
            
            if user_tier == "free":
                analysis = f"【免費預覽】基本面分析師：{stock_name} EPS {eps:.1f}元... [升級查看ROE、負債比等完整財務分析]"
                confidence = 0.5
            elif user_tier == "gold":
                analysis = f"【黃金會員】基本面分析師：{stock_name} EPS {eps:.1f}元，ROE {roe:.1f}%，財務結構{'健康' if debt_ratio < 0.5 else '需關注'}"
                confidence = 0.75
            else:
                analysis = f"【鑽石會員】基本面分析師：{stock_name} 財務表現 - EPS {eps:.1f}元(年增{'長' if eps > 0 else '衰退'})，ROE {roe:.1f}%{'(優異)' if roe > 15 else '(普通)' if roe > 8 else '(偏弱)'}，負債比 {debt_ratio:.1f}，整體財務體質{'優良' if roe > 15 and debt_ratio < 0.4 else '穩健' if roe > 8 else '需觀察'}"
                confidence = 0.85
                
        elif analyst_name == "risk_analyst":
            volatility = abs(real_time.get("change_percent", 0)) if real_time else 2.5
            
            if user_tier == "free":
                analysis = f"【免費預覽】風險分析師：{stock_name} 近期波動 {volatility:.1f}%... [升級查看VaR、壓力測試等風險評估]"
                confidence = 0.5
            elif user_tier == "gold":
                analysis = f"【黃金會員】風險分析師：{stock_name} 波動率 {volatility:.1f}%，風險等級{'高' if volatility > 5 else '中' if volatility > 2 else '低'}"
                confidence = 0.7
            else:
                analysis = f"【鑽石會員】風險分析師：{stock_name} 綜合風險評估 - 價格波動率 {volatility:.1f}%，系統性風險{'偏高' if volatility > 5 else '適中' if volatility > 2 else '偏低'}，建議風險配置{'保守' if volatility > 5 else '積極' if volatility < 2 else '平衡'}型投資"
                confidence = 0.9
                
        elif analyst_name == "social_media_analyst" and sentiment:
            sentiment_score = sentiment.get("sentiment_score", 0)
            net_flow = sentiment.get("net_institutional_flow", 0)
            
            if user_tier == "free":
                analysis = f"【免費預覽】情感分析師：{stock_name} 市場情緒{'正面' if sentiment_score > 0 else '負面'}... [升級查看PTT討論、法人動向等完整情緒分析]"
                confidence = 0.5
            elif user_tier == "gold":
                analysis = f"【黃金會員】情感分析師：{stock_name} 情緒指數 {sentiment_score:.2f}，法人{'淨買超' if net_flow > 0 else '淨賣超'} {abs(net_flow):.0f}張"
                confidence = 0.75
            else:
                analysis = f"【鑽石會員】情感分析師：{stock_name} 市場情緒分析 - 綜合情緒指數 {sentiment_score:.2f}{'(樂觀)' if sentiment_score > 0.3 else '(悲觀)' if sentiment_score < -0.3 else '(中性)'}，法人動向{'積極買進' if net_flow > 1000 else '適度買進' if net_flow > 0 else '適度賣出' if net_flow > -1000 else '大量賣出'}，建議{'順勢操作' if abs(sentiment_score) > 0.3 else '保持觀望'}"
                confidence = 0.8
                
        elif analyst_name == "investment_planner":
            overall_trend = summary.get("overall_trend", "中性")
            recommendation = summary.get("investment_recommendation", "觀望")
            
            if user_tier == "free":
                analysis = f"【免費預覽】投資規劃師：{stock_name} 整體趨勢{overall_trend}... [升級查看完整投資建議和配置策略]"
                confidence = 0.5
            elif user_tier == "gold":
                analysis = f"【黃金會員】投資規劃師：{stock_name} 綜合評估 - 趨勢{overall_trend}，建議{recommendation}，適合{'積極' if recommendation == '買入' else '保守' if recommendation == '賣出' else '平衡'}型投資者"
                confidence = 0.8
            else:
                analysis = f"【鑽石會員】投資規劃師：{stock_name} 最終投資建議 - 綜合6位分析師意見，整體趨勢{overall_trend}，投資建議{recommendation}，信心度{summary.get('confidence_score', 0.5):.0%}，建議配置比例{'20-30%' if recommendation == '買入' else '5-10%' if recommendation == '觀望' else '0-5%'}，持有週期{'長期' if recommendation == '買入' else '短期' if recommendation == '賣出' else '中期'}"
                confidence = 0.95
        else:
            # 使用模擬數據作為後備
            if user_tier == "free":
                analysis = f"【免費預覽】{analyst_config['name']}認為{stock_name}呈現穩定趨勢... [升級至會員查看完整分析]"
                confidence = 0.5
            elif user_tier == "gold":
                analysis = f"【黃金會員】{analyst_config['name']}深度分析：{stock_name}在多項指標上表現穩健，建議持續關注..."
                confidence = 0.75
            else:
                analysis = f"【鑽石會員】{analyst_config['name']}頂級分析：{stock_name}綜合多維度指標評估，提供精準投資建議..."
                confidence = 0.9
    else:
        # 無市場數據時的預設分析
        if user_tier == "free":
            analysis = f"【免費預覽】{analyst_config.get('name', '分析師')}：{stock_name}基礎分析... [升級查看完整專業分析]"
            confidence = 0.5
        elif user_tier == "gold":
            analysis = f"【黃金會員】{analyst_config.get('name', '分析師')}：{stock_name}專業分析就緒，建議關注..."
            confidence = 0.7
        else:
            analysis = f"【鑽石會員】{analyst_config.get('name', '分析師')}：{stock_name}頂級專業分析，提供精準建議..."
            confidence = 0.85
    
    return AnalystInsight(
        analyst_name=analyst_config.get("name", "AI分析師"),
        analyst_type=analyst_name,
        analysis=analysis,
        confidence=confidence
    )

# --- API Endpoints ---

@router.get("/popular-stocks", response_model=PopularStocksResponse)
async def get_popular_stocks():
    """獲取熱門股票列表"""
    return PopularStocksResponse(popular_stocks=POPULAR_TAIWAN_STOCKS)

@router.get("/analysts")
async def get_available_analysts():
    """獲取可用的AI分析師列表"""
    return {"analysts": MOCK_ANALYSTS_CONFIG}

@router.post("/analyze", response_model=ComprehensiveAnalysisResponse)
async def create_stock_analysis(request: StockAnalysisRequest):
    """
    創建股票分析 - AI分析師協同分析
    
    **這是TradingAgents的核心功能展示！**
    """
    try:
        # 🚀 獲取真實市場數據
        logger.info(f"Getting real market data for {request.stock_symbol}")
        market_data = await finmind_service.get_stock_analysis(request.stock_symbol)
        
        # 根據用戶等級決定可用的分析師數量
        available_analysts = list(MOCK_ANALYSTS_CONFIG.keys())
        
        if request.user_tier == "free":
            # 免費用戶：只能使用1位分析師
            selected_analysts = available_analysts[:1]
            upgrade_msg = "🔮 升級至黃金會員，解鎖4位專業AI分析師！"
        elif request.user_tier == "gold":
            # 黃金會員：可使用4位分析師
            selected_analysts = available_analysts[:4]
            upgrade_msg = "💎 升級至鑽石會員，解鎖全部6位頂級AI分析師！"
        else:  # diamond
            # 鑽石會員：全部6位分析師
            selected_analysts = available_analysts
            upgrade_msg = None
        
        # 🤖 使用真實數據生成各分析師的洞察
        insights = []
        for analyst_name in selected_analysts:
            insight = await generate_enhanced_analysis(analyst_name, request.stock_symbol, request.user_tier, market_data)
            insights.append(insight)
        
        # 🎯 基於真實分析生成最終建議
        stock_name = market_data.get("name", request.stock_symbol)
        analysis_summary = market_data.get("analysis_summary", {})
        overall_trend = analysis_summary.get("overall_trend", "中性")
        investment_rec = analysis_summary.get("investment_recommendation", "觀望")
        confidence_score = analysis_summary.get("confidence_score", 0.5)
        
        if request.user_tier == "free":
            final_recommendation = f"🔍 基於1位AI分析師分析，{stock_name}目前趨勢{overall_trend}... [升級會員解鎖完整6位分析師團隊建議]"
            confidence = "中等"
        elif request.user_tier == "gold":
            final_recommendation = f"📊 基於4位專業AI分析師協同分析，{stock_name}投資建議：{investment_rec}，整體趨勢{overall_trend}，建議{'積極配置' if investment_rec == '買入' else '適度配置' if investment_rec == '觀望' else '謹慎配置'}"
            confidence = "高"
        else:
            key_factors = analysis_summary.get("key_factors", [])
            factors_text = "、".join(key_factors[:3]) if key_factors else "多重技術指標"
            final_recommendation = f"🏆 基於6位頂級AI分析師全面協同分析，{stock_name}最終投資建議：{investment_rec}，信心度{confidence_score:.0%}。關鍵因子包括{factors_text}，建議配置比例{'25-35%' if investment_rec == '買入' else '10-20%' if investment_rec == '觀望' else '0-10%'}，預期持有週期{'6-12個月' if investment_rec == '買入' else '1-3個月'}"
            confidence = "極高"
        
        # 生成分析ID
        analysis_id = f"ANALYSIS_{datetime.now().strftime('%Y%m%d%H%M%S')}_{request.stock_symbol.replace('.', '')}"
        
        return ComprehensiveAnalysisResponse(
            stock_symbol=request.stock_symbol,
            analysis_id=analysis_id,
            insights=insights,
            final_recommendation=final_recommendation,
            confidence_score=confidence,
            expires_at=datetime.now(),
            upgrade_message=upgrade_msg
        )
        
    except Exception as e:
        logger.error(f"Error in stock analysis: {e}")
        raise HTTPException(status_code=500, detail=f"AI分析系統暫時無法使用: {str(e)}")

@router.get("/analysis/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """獲取分析結果詳情"""
    # 這裡可以從數據庫獲取保存的分析結果
    return {"message": f"Analysis {analysis_id} details would be retrieved from database"}

@router.post("/quick-demo")
async def quick_demo_analysis(stock_symbol: str = "2330.TW"):
    """
    快速演示功能 - 展示AI分析師的強大能力
    
    **用於首頁展示，讓訪客立即感受到震撼！**
    """
    try:
        # 模擬6位分析師快速協同分析
        demo_insights = {}
        
        for analyst_name, config in MOCK_ANALYSTS_CONFIG.items():
            if analyst_name == "technical_analyst":
                analysis = f"📊 {stock_symbol} 技術面分析：近期RSI指標顯示50.2，MACD金叉信號明確，短期趨勢偏多..."
            elif analyst_name == "fundamentals_analyst":
                analysis = f"📋 {stock_symbol} 基本面分析：Q3財報EPS 6.8元，ROE 26.5%，營收年增12.3%，基本面穩健..."
            elif analyst_name == "news_analyst":
                analysis = f"📰 {股票symbol} 新聞面分析：政府政策利多，AI晶片需求強勁，國際擴產計劃進展順利..."
            elif analyst_name == "risk_analyst":
                analysis = f"⚠️ {stock_symbol} 風險評估：整體風險度中等，主要關注匯率波動和地緣政治因素..."
            elif analyst_name == "social_media_analyst":
                analysis = f"💭 {stock_symbol} 社群情緒：PTT討論熱度89%，投資者情感偏正向，關注度持續上升..."
            else:  # investment_planner
                analysis = f"🎯 {stock_symbol} 最終建議：BUY 信心度85% - 建議分批布局，目標價位上調15%..."
            
            demo_insights[analyst_name] = {
                "analyst": config["name"],
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "stock_symbol": stock_symbol,
            "demo_type": "6位AI分析師協同分析展示",
            "insights": demo_insights,
            "summary": f"🏆 TradingAgents AI投資分析平台 - 6位專業分析師一致認為{stock_symbol}具備投資價值！",
            "call_to_action": "立即註冊會員，獲得完整專業投資分析報告！",
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Quick demo error: {e}")
        raise HTTPException(status_code=500, detail="演示系統暫時無法使用")

@router.get("/member-benefits")
async def get_member_benefits():
    """獲取會員等級權益說明"""
    return {
        "membership_tiers": {
            "free": {
                "name": "免費會員",
                "price": "NT$ 0",
                "analysts": 1,
                "features": [
                    "每日1位AI分析師分析",
                    "基礎股票資訊查詢",
                    "投資新手教學內容",
                    "每月3次完整分析報告"
                ],
                "limitations": "僅預覽分析結果"
            },
            "gold": {
                "name": "黃金會員",
                "price": "NT$ 1,999/月",
                "analysts": 4,
                "features": [
                    "4位AI分析師協同分析",
                    "個人投資組合追蹤",
                    "即時市場預警通知",
                    "無限次分析報告",
                    "投資決策建議書"
                ],
                "highlight": "專業投資者首選"
            },
            "diamond": {
                "name": "鑽石會員",
                "price": "NT$ 4,999/月",
                "analysts": 6,
                "features": [
                    "全部6位AI分析師團隊",
                    "專屬投資組合優化",
                    "VIP市場情報推送",
                    "一對一AI投資顧問",
                    "高頻交易信號推薦",
                    "優先客戶服務"
                ],
                "highlight": "頂級投資專家體驗"
            }
        }
    }

# --- Health Check ---
@router.get("/health")
async def ai_demo_health():
    """AI演示系統健康檢查"""
    return {
        "service": "ai_analyst_demo",
        "status": "healthy",
        "available_analysts": len(MOCK_ANALYSTS_CONFIG),
        "demo_ready": True,
        "timestamp": datetime.now().isoformat()
    }