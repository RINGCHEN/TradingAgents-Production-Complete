#!/usr/bin/env python3
"""
TradingAgents 國際市場差異化功能 API 端點
提供台股與美股同業配對、全球市場相關性分析等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..dataflows.data_orchestrator import DataOrchestrator
from ..utils.user_context import UserContext
from ..models.membership import TierType
from ..utils.logging_config import get_logger
from ..default_config import DEFAULT_CONFIG

logger = get_logger(__name__)
router = APIRouter(prefix="/international-market", tags=["international-market"])

# 請求模型
class PeerComparisonRequest(BaseModel):
    """同業比較請求"""
    taiwan_symbol: str = Field(..., description="台股代號")
    limit: int = Field(5, description="返回的同業公司數量", ge=1, le=10)

class CorrelationAnalysisRequest(BaseModel):
    """相關性分析請求"""
    symbols: List[str] = Field(..., description="股票代號列表", min_items=2, max_items=20)
    correlation_type: str = Field("price", description="相關性類型")
    time_period: str = Field("1Y", description="時間週期")

class RiskDiversificationRequest(BaseModel):
    """風險分散建議請求"""
    portfolio_symbols: List[str] = Field(..., description="投資組合股票代號", min_items=1)
    target_risk_level: str = Field("moderate", description="目標風險水平")

class CurrencyImpactRequest(BaseModel):
    """匯率影響分析請求"""
    taiwan_symbol: str = Field(..., description="台股代號")
    currency_pairs: Optional[List[str]] = Field(None, description="貨幣對列表")

class EventImpactRequest(BaseModel):
    """事件影響預測請求"""
    event_type: str = Field(..., description="事件類型")
    taiwan_symbols: List[str] = Field(..., description="台股代號列表", min_items=1)

# 響應模型
class StandardResponse(BaseModel):
    """標準響應格式"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    upgrade_prompt: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

# 數據編排器實例
orchestrator = DataOrchestrator(config=DEFAULT_CONFIG)

@router.post("/peer-comparison")
async def get_peer_comparison(
    request: PeerComparisonRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取台股的國際同業比較
    
    Args:
        request: 同業比較請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        同業比較結果
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 執行同業比較
        result = await orchestrator.find_international_peers(
            taiwan_symbol=request.taiwan_symbol,
            user_context=user_context,
            limit=request.limit
        )
        
        return StandardResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            upgrade_prompt=result.get('upgrade_prompt'),
            timestamp=result.get('timestamp')
        )
        
    except Exception as e:
        logger.error(f"同業比較失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/correlation-analysis")
async def get_correlation_analysis(
    request: CorrelationAnalysisRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取全球市場相關性分析
    
    Args:
        request: 相關性分析請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        相關性分析結果
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 執行相關性分析
        result = await orchestrator.analyze_global_market_correlation(
            symbols=request.symbols,
            user_context=user_context
        )
        
        return StandardResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            upgrade_prompt=result.get('upgrade_prompt'),
            timestamp=result.get('timestamp')
        )
        
    except Exception as e:
        logger.error(f"相關性分析失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/risk-diversification")
async def get_risk_diversification_advice(
    request: RiskDiversificationRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取風險分散建議
    
    Args:
        request: 風險分散建議請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        風險分散建議
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 執行風險分散分析
        result = await orchestrator.get_risk_diversification_advice(
            portfolio_symbols=request.portfolio_symbols,
            user_context=user_context,
            target_risk_level=request.target_risk_level
        )
        
        return StandardResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            upgrade_prompt=result.get('upgrade_prompt'),
            timestamp=result.get('timestamp')
        )
        
    except Exception as e:
        logger.error(f"風險分散建議失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/cross-timezone-alerts")
async def get_cross_timezone_alerts(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級"),
    symbols: Optional[str] = Query(None, description="關注的股票代號，用逗號分隔")
) -> StandardResponse:
    """
    獲取跨時區市場預警
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        symbols: 關注的股票代號列表
        
    Returns:
        跨時區預警列表
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 解析股票代號
        symbol_list = symbols.split(',') if symbols else None
        
        # 獲取跨時區預警
        result = await orchestrator.get_cross_timezone_alerts(
            user_context=user_context,
            symbols=symbol_list
        )
        
        return StandardResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            upgrade_prompt=result.get('upgrade_prompt'),
            timestamp=result.get('timestamp')
        )
        
    except Exception as e:
        logger.error(f"跨時區預警獲取失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/currency-impact")
async def get_currency_impact_analysis(
    request: CurrencyImpactRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取匯率影響分析
    
    Args:
        request: 匯率影響分析請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        匯率影響分析結果
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 執行匯率影響分析
        result = await orchestrator.analyze_currency_impact(
            taiwan_symbol=request.taiwan_symbol,
            user_context=user_context
        )
        
        return StandardResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            upgrade_prompt=result.get('upgrade_prompt'),
            timestamp=result.get('timestamp')
        )
        
    except Exception as e:
        logger.error(f"匯率影響分析失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.post("/event-impact-prediction")
async def get_event_impact_prediction(
    request: EventImpactRequest,
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取全球事件影響預測
    
    Args:
        request: 事件影響預測請求
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        事件影響預測結果
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=membership_tier
        )
        
        # 執行事件影響預測
        result = await orchestrator.predict_global_event_impact(
            event_type=request.event_type,
            taiwan_symbols=request.taiwan_symbols,
            user_context=user_context
        )
        
        return StandardResponse(
            success=result['success'],
            data=result.get('data'),
            error=result.get('error'),
            upgrade_prompt=result.get('upgrade_prompt'),
            timestamp=result.get('timestamp')
        )
        
    except Exception as e:
        logger.error(f"事件影響預測失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )

@router.get("/supported-features")
async def get_supported_features() -> Dict[str, Any]:
    """
    獲取支持的功能列表
    
    Returns:
        支持的功能和配置
    """
    try:
        return {
            'success': True,
            'data': {
                'peer_comparison': {
                    'description': '台股與國際同業公司比較',
                    'required_tier': 'GOLD',
                    'max_peers': 10
                },
                'correlation_analysis': {
                    'description': '全球市場相關性分析',
                    'required_tier': 'GOLD',
                    'max_symbols': 20
                },
                'risk_diversification': {
                    'description': '投資組合風險分散建議',
                    'required_tier': 'GOLD',
                    'risk_levels': ['conservative', 'moderate', 'aggressive']
                },
                'cross_timezone_alerts': {
                    'description': '跨時區市場預警',
                    'required_tier': 'GOLD',
                    'alert_types': ['price_movement', 'volume_spike', 'news_event', 'technical_signal']
                },
                'currency_impact': {
                    'description': '匯率影響分析',
                    'required_tier': 'GOLD',
                    'supported_currencies': ['USD', 'EUR', 'JPY', 'CNY', 'HKD']
                },
                'event_impact_prediction': {
                    'description': '全球事件影響預測',
                    'required_tier': 'DIAMOND',
                    'event_types': ['fed_rate_change', 'trade_war', 'pandemic', 'geopolitical', 'economic_data']
                }
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取支持功能失敗: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@router.get("/market-insights")
async def get_market_insights(
    user_id: str = Query(..., description="用戶ID"),
    membership_tier: TierType = Query(..., description="會員等級")
) -> StandardResponse:
    """
    獲取市場洞察和趨勢分析
    
    Args:
        user_id: 用戶ID
        membership_tier: 會員等級
        
    Returns:
        市場洞察信息
    """
    try:
        # 檢查用戶權限
        if membership_tier.value in ['FREE']:
            return StandardResponse(
                success=False,
                error='需要升級會員以獲取市場洞察',
                upgrade_prompt={
                    'title': '📈 專業市場洞察',
                    'message': '升級至 Gold 會員，獲得專業的市場趨勢分析和投資洞察',
                    'benefits': [
                        '每日市場趨勢分析',
                        '跨市場機會發現',
                        '專業投資策略建議',
                        '風險預警和提醒'
                    ]
                }
            )
        
        # 生成市場洞察（模擬數據）
        insights = {
            'global_market_trends': {
                'us_market': {
                    'trend': 'bullish',
                    'key_drivers': ['AI技術發展', '聯準會政策轉向', '企業獲利成長'],
                    'risk_factors': ['通膨壓力', '地緣政治風險']
                },
                'taiwan_market': {
                    'trend': 'neutral',
                    'key_drivers': ['半導體需求復甦', '出口訂單回升'],
                    'risk_factors': ['中美貿易關係', '匯率波動']
                }
            },
            'sector_rotation': {
                'outperforming': ['technology', 'healthcare'],
                'underperforming': ['utilities', 'real_estate'],
                'emerging_themes': ['AI革命', '綠色能源轉型', '數位化轉型']
            },
            'cross_market_opportunities': [
                {
                    'opportunity': '台積電 vs NVIDIA 估值差異',
                    'description': '兩家公司在AI晶片領域的不同定位創造套利機會',
                    'risk_level': 'medium'
                },
                {
                    'opportunity': '亞洲消費股復甦',
                    'description': '隨著中國經濟重啟，亞洲消費相關股票具備上漲潛力',
                    'risk_level': 'high'
                }
            ],
            'currency_outlook': {
                'USD_TWD': {
                    'forecast': '31.0-32.0',
                    'key_factors': ['美國利率政策', '台灣出口表現', '地緣政治風險']
                }
            }
        }
        
        return StandardResponse(
            success=True,
            data=insights,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"市場洞察獲取失敗: {e}")
        return StandardResponse(
            success=False,
            error=str(e)
        )