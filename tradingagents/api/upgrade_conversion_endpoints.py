#!/usr/bin/env python3
"""
TradingAgents 會員升級轉換 API 端點
提供升級提示、試用管理和轉換追蹤功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..services.upgrade_conversion_service import (
    UpgradeConversionService, UpgradePromptType, ConversionEventType
)
from ..models.membership import TierType
from ..utils.user_context import UserContext
from ..utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/upgrade-conversion", tags=["upgrade-conversion"])

# 請求模型
class UpgradeClickRequest(BaseModel):
    """升級點擊請求"""
    user_id: str = Field(..., description="用戶ID")
    prompt_id: str = Field(..., description="提示ID")
    target_tier: TierType = Field(..., description="目標會員等級")

class UpgradeCompletionRequest(BaseModel):
    """升級完成請求"""
    user_id: str = Field(..., description="用戶ID")
    old_tier: TierType = Field(..., description="原會員等級")
    new_tier: TierType = Field(..., description="新會員等級")
    prompt_id: Optional[str] = Field(None, description="提示ID")

class ValuePropositionRequest(BaseModel):
    """價值主張請求"""
    user_id: str = Field(..., description="用戶ID")
    current_tier: TierType = Field(..., description="當前會員等級")

# 響應模型
class UpgradePromptResponse(BaseModel):
    """升級提示響應"""
    success: bool
    prompt: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ValuePropositionResponse(BaseModel):
    """價值主張響應"""
    success: bool
    content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ConversionAnalyticsResponse(BaseModel):
    """轉換分析響應"""
    success: bool
    analytics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# 服務實例
upgrade_service = UpgradeConversionService()

@router.get("/value-proposition")
async def get_value_proposition(
    user_id: str = Query(..., description="用戶ID"),
    current_tier: TierType = Query(..., description="當前會員等級")
) -> ValuePropositionResponse:
    """
    獲取國際數據功能的價值主張內容
    
    Args:
        user_id: 用戶ID
        current_tier: 當前會員等級
        
    Returns:
        價值主張內容
    """
    try:
        # 創建用戶上下文
        user_context = UserContext(
            user_id=user_id,
            membership_tier=current_tier
        )
        
        # 獲取價值主張內容
        content = await upgrade_service.get_value_proposition_content(user_context)
        
        return ValuePropositionResponse(
            success=True,
            content=content
        )
        
    except Exception as e:
        logger.error(f"獲取價值主張失敗: {e}")
        return ValuePropositionResponse(
            success=False,
            error=str(e)
        )

@router.post("/track-upgrade-click")
async def track_upgrade_click(request: UpgradeClickRequest) -> Dict[str, Any]:
    """
    追蹤升級點擊事件
    
    Args:
        request: 升級點擊請求
        
    Returns:
        追蹤結果
    """
    try:
        success = await upgrade_service.track_upgrade_click(
            user_id=request.user_id,
            prompt_id=request.prompt_id,
            target_tier=request.target_tier
        )
        
        return {
            'success': success,
            'message': '升級點擊事件已記錄'
        }
        
    except Exception as e:
        logger.error(f"追蹤升級點擊失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/track-upgrade-completion")
async def track_upgrade_completion(request: UpgradeCompletionRequest) -> Dict[str, Any]:
    """
    追蹤升級完成事件
    
    Args:
        request: 升級完成請求
        
    Returns:
        追蹤結果
    """
    try:
        success = await upgrade_service.track_upgrade_completion(
            user_id=request.user_id,
            old_tier=request.old_tier,
            new_tier=request.new_tier,
            prompt_id=request.prompt_id
        )
        
        return {
            'success': success,
            'message': '升級完成事件已記錄'
        }
        
    except Exception as e:
        logger.error(f"追蹤升級完成失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics")
async def get_conversion_analytics(
    start_date: Optional[str] = Query(None, description="開始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="結束日期 (YYYY-MM-DD)")
) -> ConversionAnalyticsResponse:
    """
    獲取轉換分析數據
    
    Args:
        start_date: 開始日期
        end_date: 結束日期
        
    Returns:
        轉換分析數據
    """
    try:
        # 解析日期
        start_dt = None
        end_dt = None
        
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        
        # 獲取分析數據
        analytics = await upgrade_service.get_conversion_analytics(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return ConversionAnalyticsResponse(
            success=True,
            analytics=analytics
        )
        
    except Exception as e:
        logger.error(f"獲取轉換分析失敗: {e}")
        return ConversionAnalyticsResponse(
            success=False,
            error=str(e)
        )

@router.get("/trial-status/{user_id}")
async def get_trial_status(user_id: str) -> Dict[str, Any]:
    """
    獲取用戶的試用狀態
    
    Args:
        user_id: 用戶ID
        
    Returns:
        試用狀態信息
    """
    try:
        trial_key = f"{user_id}_international_data"
        trial_usage = upgrade_service.trial_usage.get(trial_key)
        
        if trial_usage is None:
            return {
                'success': True,
                'trial_available': True,
                'remaining_trials': 3,
                'total_trials': 3,
                'used_trials': 0,
                'first_used_at': None,
                'last_used_at': None
            }
        
        return {
            'success': True,
            'trial_available': trial_usage.can_use_trial(),
            'remaining_trials': trial_usage.get_remaining_trials(),
            'total_trials': trial_usage.max_usage,
            'used_trials': trial_usage.usage_count,
            'first_used_at': trial_usage.first_used_at.isoformat() if trial_usage.first_used_at else None,
            'last_used_at': trial_usage.last_used_at.isoformat() if trial_usage.last_used_at else None,
            'trial_expired': trial_usage.trial_expired
        }
        
    except Exception as e:
        logger.error(f"獲取試用狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/success-stories")
async def get_success_stories() -> Dict[str, Any]:
    """
    獲取成功案例
    
    Returns:
        成功案例列表
    """
    try:
        success_stories = [
            {
                'id': 1,
                'user_name': '張先生',
                'user_tier': 'Gold',
                'story': '通過國際數據分析，發現了美股科技股的投資機會，3個月獲得25%回報',
                'return_rate': '25%',
                'investment_period': '3個月',
                'key_features_used': [
                    '美股實時數據',
                    '跨市場比較分析',
                    '技術指標分析'
                ],
                'testimonial': '國際數據功能讓我發現了台股以外的投資機會，大大提升了投資組合的表現。',
                'created_at': '2024-01-15'
            },
            {
                'id': 2,
                'user_name': '李女士',
                'user_tier': 'Diamond',
                'story': '利用跨市場分析，成功規避了單一市場風險，保護了投資組合',
                'return_rate': '風險降低40%',
                'investment_period': '6個月',
                'key_features_used': [
                    '全球市場相關性分析',
                    '風險分散建議',
                    '經濟事件影響分析'
                ],
                'testimonial': '跨市場分析功能幫助我建立了更穩健的投資組合，即使在市場波動期間也能保持穩定。',
                'created_at': '2024-02-20'
            },
            {
                'id': 3,
                'user_name': '王先生',
                'user_tier': 'Gold',
                'story': '使用國際ETF分析功能，構建了全球化投資組合，年化收益率達到18%',
                'return_rate': '18%',
                'investment_period': '12個月',
                'key_features_used': [
                    '國際ETF數據',
                    '資產配置建議',
                    '匯率影響分析'
                ],
                'testimonial': '國際ETF分析讓我能夠輕鬆投資全球市場，分散風險的同時獲得穩定收益。',
                'created_at': '2024-03-10'
            }
        ]
        
        return {
            'success': True,
            'stories': success_stories,
            'total_count': len(success_stories),
            'average_return': '19.3%',
            'user_satisfaction': '95%'
        }
        
    except Exception as e:
        logger.error(f"獲取成功案例失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upgrade-benefits/{target_tier}")
async def get_upgrade_benefits(
    target_tier: TierType,
    current_tier: TierType = Query(..., description="當前會員等級")
) -> Dict[str, Any]:
    """
    獲取升級後的具體收益
    
    Args:
        target_tier: 目標會員等級
        current_tier: 當前會員等級
        
    Returns:
        升級收益詳情
    """
    try:
        benefits_mapping = {
            TierType.GOLD: {
                'data_access': {
                    'international_stocks': '無限制訪問美股、港股、日股等全球市場數據',
                    'real_time_data': '實時股價和交易數據',
                    'historical_data': '10年歷史數據',
                    'financial_statements': '完整財務報表數據'
                },
                'analysis_tools': {
                    'technical_analysis': '50+ 技術指標',
                    'fundamental_analysis': '深度基本面分析',
                    'cross_market_comparison': '跨市場同業比較',
                    'risk_assessment': '投資組合風險評估'
                },
                'ai_features': {
                    'personalized_recommendations': '個人化投資建議',
                    'market_alerts': '智能市場預警',
                    'portfolio_optimization': '投資組合優化建議',
                    'trend_analysis': 'AI趨勢分析'
                },
                'support': {
                    'priority_support': '優先客戶支持',
                    'educational_content': '投資教育內容',
                    'webinars': '專家網路研討會',
                    'community_access': '高級會員社群'
                }
            },
            TierType.DIAMOND: {
                'data_access': {
                    'institutional_data': '機構級數據訪問',
                    'alternative_data': '另類數據源',
                    'global_indices': '全球指數和ETF數據',
                    'economic_indicators': '宏觀經濟指標'
                },
                'analysis_tools': {
                    'advanced_modeling': '高級金融建模工具',
                    'backtesting': '策略回測平台',
                    'risk_modeling': '高級風險建模',
                    'scenario_analysis': '情境分析工具'
                },
                'ai_features': {
                    'custom_ai_models': '定制化AI模型',
                    'predictive_analytics': '預測性分析',
                    'sentiment_analysis': '市場情緒分析',
                    'news_impact_analysis': '新聞影響分析'
                },
                'support': {
                    'dedicated_advisor': '專屬投資顧問',
                    'custom_reports': '定制化研究報告',
                    'direct_access': '直接聯繫分析師',
                    'exclusive_events': '專屬投資活動'
                }
            }
        }
        
        target_benefits = benefits_mapping.get(target_tier, {})
        
        # 計算升級價值
        pricing = {
            TierType.FREE: 0,
            TierType.GOLD: 299,
            TierType.DIAMOND: 899
        }
        
        upgrade_cost = pricing.get(target_tier, 0) - pricing.get(current_tier, 0)
        
        return {
            'success': True,
            'target_tier': target_tier.value,
            'current_tier': current_tier.value,
            'upgrade_cost': upgrade_cost,
            'benefits': target_benefits,
            'roi_estimate': {
                'potential_return_improvement': '15-25%',
                'risk_reduction': '20-40%',
                'time_savings': '5-10 小時/週',
                'payback_period': '2-3 個月'
            }
        }
        
    except Exception as e:
        logger.error(f"獲取升級收益失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))