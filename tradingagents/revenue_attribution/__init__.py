#!/usr/bin/env python3
"""
Revenue Attribution System
收益歸因系統

GPT-OSS整合任務2.1.3 - 收益歸因系統初始化模組
提供統一的收益歸因和預測分析功能入口
"""

from .models import (
    # 枚舉類型
    RevenueType,
    AttributionMethod, 
    RevenueConfidence,
    PredictionHorizon,
    ModelType,
    
    # 數據模型
    RevenueAttributionRecord,
    APICostSaving,
    NewFeatureRevenue,
    MembershipUpgradeAttribution,
    RevenueForecast,
    
    # Pydantic 架構
    RevenueAttributionRecordSchema,
    APICostSavingSchema,
    NewFeatureRevenueSchema,
    MembershipUpgradeAttributionSchema,
    RevenueForecastSchema,
    
    # 請求/響應模型
    RevenueAttributionRequest,
    RevenueForecastRequest,
    RevenueAnalysisResponse
)

from .api_cost_calculator import (
    APICostCalculator,
    CostSavingsAnalyzer,
    APIProvider,
    APIPricingModel,
    HardwareCostModel
)

from .revenue_tracker import (
    NewFeatureRevenueTracker,
    MembershipUpgradeAttributor,
    FeatureCategory,
    MembershipTier,
    FeatureUsageMetrics,
    RevenueImpactModel
)

from .forecast_engine import (
    RevenueForecastEngine,
    ForecastModel,
    LinearRegressionForecastModel,
    ARIMAForecastModel,
    EnsembleForecastModel
)

from .service import RevenueAttributionService

# 版本信息
__version__ = "1.0.0"
__author__ = "GPT-OSS Integration Team"
__description__ = "Enterprise Revenue Attribution and Forecasting System"

# 導出的主要類和函數
__all__ = [
    # 枚舉
    "RevenueType",
    "AttributionMethod", 
    "RevenueConfidence",
    "PredictionHorizon",
    "ModelType",
    "FeatureCategory",
    "MembershipTier",
    "APIProvider",
    
    # 數據模型
    "RevenueAttributionRecord",
    "APICostSaving", 
    "NewFeatureRevenue",
    "MembershipUpgradeAttribution",
    "RevenueForecast",
    
    # 架構模型
    "RevenueAttributionRecordSchema",
    "APICostSavingSchema",
    "NewFeatureRevenueRevenueSchema",
    "MembershipUpgradeAttributionSchema",
    "RevenueForecastSchema",
    
    # 請求響應模型
    "RevenueAttributionRequest",
    "RevenueForecastRequest", 
    "RevenueAnalysisResponse",
    
    # 核心服務類
    "RevenueAttributionService",
    "APICostCalculator",
    "CostSavingsAnalyzer",
    "NewFeatureRevenueTracker",
    "MembershipUpgradeAttributor",
    "RevenueForecastEngine",
    
    # 預測模型
    "ForecastModel",
    "LinearRegressionForecastModel",
    "ARIMAForecastModel", 
    "EnsembleForecastModel",
    
    # 輔助類
    "APIPricingModel",
    "HardwareCostModel",
    "FeatureUsageMetrics",
    "RevenueImpactModel",
    
    # 便捷函數
    "create_revenue_attribution_service"
]


# ==================== 便捷函數 ====================

def create_revenue_attribution_service() -> RevenueAttributionService:
    """
    創建預配置的收益歸因服務實例
    
    Returns:
        配置完成的收益歸因服務
    """
    service = RevenueAttributionService()
    return service


async def create_integrated_revenue_system() -> dict:
    """
    創建完整的收益歸因分析系統
    
    Returns:
        包含所有組件的整合系統字典
    """
    # 創建核心服務
    service = RevenueAttributionService()
    await service.initialize_service()
    
    # 返回完整系統
    return {
        'revenue_attribution_service': service,
        'api_cost_calculator': service.api_cost_calculator,
        'cost_savings_analyzer': service.cost_savings_analyzer,
        'feature_revenue_tracker': service.feature_revenue_tracker,
        'membership_attributor': service.membership_attributor,
        'forecast_engine': service.forecast_engine,
        'system_version': __version__,
        'system_initialized': True
    }


# ==================== 模組級配置 ====================

# 默認配置
DEFAULT_CONFIG = {
    'attribution_confidence_threshold': 75.0,
    'forecast_confidence_level': 95.0,
    'cache_timeout_hours': 24,
    'max_forecast_periods': 12,
    'min_historical_data_points': 5,
    'default_gpt_oss_impact_factor': 60.0
}

# 支援的收益類型映射
REVENUE_TYPE_DESCRIPTIONS = {
    RevenueType.API_COST_SAVINGS: "API成本節省收益",
    RevenueType.NEW_FEATURE_REVENUE: "新功能直接收益", 
    RevenueType.MEMBERSHIP_UPGRADE: "會員升級收益",
    RevenueType.EFFICIENCY_GAINS: "效率提升收益",
    RevenueType.PREMIUM_SERVICE: "高級服務收益"
}

# 歸因方法說明
ATTRIBUTION_METHOD_DESCRIPTIONS = {
    AttributionMethod.DIRECT: "直接歸因 - 明確可追蹤的收益歸因",
    AttributionMethod.TIME_DECAY: "時間衰減歸因 - 基於時間權重的歸因模型",
    AttributionMethod.LINEAR: "線性歸因 - 平均分配歸因權重",
    AttributionMethod.ALGORITHMIC: "算法歸因 - 基於機器學習的智能歸因",
    AttributionMethod.WEIGHTED: "加權歸因 - 基於重要性的權重分配歸因"
}

# 預測模型說明
MODEL_TYPE_DESCRIPTIONS = {
    ModelType.LINEAR_REGRESSION: "線性回歸預測 - 適合趨勢明確的數據",
    ModelType.ARIMA: "ARIMA時間序列預測 - 適合有季節性模式的數據",
    ModelType.NEURAL_NETWORK: "神經網絡預測 - 適合複雜非線性關係",
    ModelType.ENSEMBLE: "集成預測 - 結合多種模型的預測結果",
    ModelType.CUSTOM: "自定義預測模型 - 針對特定場景的定制模型"
}


# ==================== 模組級驗證函數 ====================

def validate_attribution_request(request: RevenueAttributionRequest) -> bool:
    """驗證收益歸因請求的有效性"""
    if request.end_date <= request.start_date:
        return False
    
    if request.confidence_threshold < 0 or request.confidence_threshold > 100:
        return False
    
    return True


def validate_forecast_request(request: RevenueForecastRequest) -> bool:
    """驗證收益預測請求的有效性"""
    if request.historical_data_months < 3 or request.historical_data_months > 60:
        return False
    
    if request.confidence_level < 50 or request.confidence_level > 99:
        return False
    
    return True


# ==================== 模組級工具函數 ====================

def calculate_attribution_confidence(
    data_quality_score: float,
    temporal_proximity: float,
    method_reliability: float
) -> RevenueConfidence:
    """
    計算歸因信心度等級
    
    Args:
        data_quality_score: 數據品質分數 (0-100)
        temporal_proximity: 時間接近度分數 (0-1)
        method_reliability: 方法可靠性分數 (0-1)
    
    Returns:
        歸因信心度等級
    """
    composite_score = (
        data_quality_score / 100 * 0.4 +
        temporal_proximity * 0.3 +
        method_reliability * 0.3
    ) * 100
    
    if composite_score >= 85:
        return RevenueConfidence.HIGH
    elif composite_score >= 70:
        return RevenueConfidence.MEDIUM
    else:
        return RevenueConfidence.LOW


def format_revenue_amount(amount: float, currency: str = "USD") -> str:
    """格式化收益金額顯示"""
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def calculate_gpt_oss_roi(
    total_revenue_attributed: float,
    gpt_oss_investment: float,
    time_period_months: int
) -> dict:
    """
    計算GPT-OSS的投資回報率
    
    Args:
        total_revenue_attributed: 總歸因收益
        gpt_oss_investment: GPT-OSS投資額
        time_period_months: 時間期間（月）
    
    Returns:
        ROI分析結果字典
    """
    if gpt_oss_investment <= 0:
        return {'error': 'Invalid investment amount'}
    
    roi_percentage = (total_revenue_attributed - gpt_oss_investment) / gpt_oss_investment * 100
    payback_months = gpt_oss_investment / (total_revenue_attributed / time_period_months) if total_revenue_attributed > 0 else float('inf')
    
    return {
        'roi_percentage': roi_percentage,
        'payback_period_months': payback_months if payback_months != float('inf') else None,
        'total_net_benefit': total_revenue_attributed - gpt_oss_investment,
        'monthly_average_return': total_revenue_attributed / time_period_months,
        'analysis_period_months': time_period_months
    }


# ==================== 模組初始化日誌 ====================

import logging
logger = logging.getLogger(__name__)
logger.info(f"Revenue Attribution System v{__version__} 模組加載完成")
logger.info(f"支援收益類型: {list(REVENUE_TYPE_DESCRIPTIONS.keys())}")
logger.info(f"支援歸因方法: {list(ATTRIBUTION_METHOD_DESCRIPTIONS.keys())}")
logger.info(f"支援預測模型: {list(MODEL_TYPE_DESCRIPTIONS.keys())}")