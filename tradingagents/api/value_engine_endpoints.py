#!/usr/bin/env python3
"""
Value Engine API Endpoints - 價值引擎API端點
天工 (TianGong) - 為ART系統提供價值計算和推薦服務的API接口

此模組提供：
1. 個人化價值計算API
2. 客戶生命週期價值(CLV)API  
3. 動態定價策略API
4. 服務使用效益分析API
5. 服務層級推薦API
6. 價值服務組合管理API
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import asyncio
import logging
import time
import uuid
import numpy as np

# 導入價值引擎組件
from ..art.value_engine.value_service_engine import (
    ValueServiceEngine, ServiceTier, CustomerSegment, ValueProposition
)
from ..art.value_engine.service_utilization_analyzer import (
    ServiceUtilizationAnalyzer, UtilizationStatus, ValueRealizationStage
)
from ..art.value_engine.service_tier_system import (
    ServiceTierSystem, TierMatchingStrategy, RecommendationType
)
from ..art.personalization.user_profile_analyzer import (
    UserProfileAnalyzer, BehaviorPattern, PersonalityMetrics
)

# 導入認證依賴
from ..auth.dependencies import get_current_user
from ..utils.error_handler import handle_api_error

# 創建路由器
router = APIRouter(prefix="/api/v1/value-engine", tags=["value-engine"])
logger = logging.getLogger(__name__)

# 初始化核心組件
value_service_engine = ValueServiceEngine()
utilization_analyzer = ServiceUtilizationAnalyzer()
tier_system = ServiceTierSystem()
user_profile_analyzer = UserProfileAnalyzer()

# Pydantic模型定義
class PersonalizedValueRequest(BaseModel):
    """個人化價值計算請求"""
    user_id: str = Field(..., description="用戶ID")
    service_definition: Dict[str, Any] = Field(..., description="服務定義")
    historical_data: Optional[List[Dict[str, Any]]] = Field(None, description="歷史數據")
    include_recommendations: bool = Field(True, description="是否包含推薦")

class PersonalizedValueResponse(BaseModel):
    """個人化價值計算響應"""
    user_id: str
    base_value: Dict[str, float]
    personalized_value: Dict[str, float]
    confidence_score: float
    behavior_patterns: List[str]
    value_drivers: List[str]
    recommendations: List[str]
    timestamp: float

class CLVCalculationRequest(BaseModel):
    """CLV計算請求"""
    user_id: str = Field(..., description="用戶ID")
    historical_data: Optional[List[Dict[str, Any]]] = Field(None, description="歷史數據")
    projection_months: int = Field(36, description="預測月數", ge=1, le=120)

class CLVCalculationResponse(BaseModel):
    """CLV計算響應"""
    user_id: str
    customer_lifetime_value: float
    clv_components: Dict[str, Any]
    personalization_impact: Dict[str, Any]
    value_breakdown: Dict[str, float]
    recommendations: List[str]
    timestamp: float

class DynamicPricingRequest(BaseModel):
    """動態定價請求"""
    user_id: str = Field(..., description="用戶ID")
    service_id: str = Field(..., description="服務ID")
    market_conditions: Dict[str, Any] = Field(..., description="市場條件")
    cost_data: Dict[str, Any] = Field(..., description="成本數據")

class DynamicPricingResponse(BaseModel):
    """動態定價響應"""
    user_id: str
    service_id: str
    base_price: float
    personalized_price: float
    pricing_factors: Dict[str, Any]
    optimization_suggestions: List[str]
    pricing_confidence: float
    valid_until: float

class UtilizationAnalysisRequest(BaseModel):
    """使用效益分析請求"""
    user_id: str = Field(..., description="用戶ID")
    service_id: str = Field(..., description="服務ID")
    usage_data: List[Dict[str, Any]] = Field(..., description="使用數據")
    analysis_period_days: int = Field(30, description="分析週期天數", ge=1, le=365)

class UtilizationAnalysisResponse(BaseModel):
    """使用效益分析響應"""
    user_id: str
    service_id: str
    utilization_status: str
    realization_stage: str
    realized_value: float
    value_realization_rate: float
    optimization_recommendations: List[Dict[str, Any]]
    efficiency_metrics: Dict[str, float]

class ServiceRecommendationRequest(BaseModel):
    """服務推薦請求"""
    user_id: str = Field(..., description="用戶ID")
    current_services: Optional[List[str]] = Field(None, description="當前服務ID列表")
    matching_strategy: str = Field("hybrid", description="匹配策略")
    max_recommendations: int = Field(5, description="最大推薦數量", ge=1, le=10)

class ServiceRecommendationResponse(BaseModel):
    """服務推薦響應"""
    user_id: str
    recommendations: List[Dict[str, Any]]
    matching_confidence: float
    personalization_score: float
    total_expected_value: float

class ServicePortfolioRequest(BaseModel):
    """服務組合請求"""
    user_id: str = Field(..., description="用戶ID")
    include_usage_data: bool = Field(True, description="是否包含使用數據")
    optimization_focus: str = Field("value", description="優化重點: value/cost/efficiency")

class ServicePortfolioResponse(BaseModel):
    """服務組合響應"""
    user_id: str
    portfolio_id: str
    active_services_count: int
    total_value: float
    portfolio_roi: float
    personalization_score: float
    optimization_opportunities: List[Dict[str, Any]]
    upgrade_recommendations: List[Dict[str, Any]]

# API端點實現
@router.post("/personalized-value", response_model=PersonalizedValueResponse)
async def calculate_personalized_value(
    request: PersonalizedValueRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """計算個人化價值"""
    try:
        logger.info(f"Calculating personalized value for user {request.user_id}")
        
        # 執行個人化價值計算
        result = await value_service_engine.personalized_value_calculator.calculate_personalized_value(
            request.user_id,
            request.service_definition,
            request.historical_data
        )
        
        response = PersonalizedValueResponse(
            user_id=result['user_id'],
            base_value=result['base_value'],
            personalized_value=result['personalized_value'],
            confidence_score=result['confidence_score'],
            behavior_patterns=result['behavior_patterns'],
            value_drivers=result['value_drivers'],
            recommendations=result['recommendations'],
            timestamp=result['timestamp']
        )
        
        logger.info(f"Personalized value calculation completed for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Personalized value calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Value calculation failed: {str(e)}")

@router.post("/customer-lifetime-value", response_model=CLVCalculationResponse)
async def calculate_customer_lifetime_value(
    request: CLVCalculationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """計算客戶生命週期價值"""
    try:
        logger.info(f"Calculating CLV for user {request.user_id}")
        
        # 執行CLV計算
        result = await value_service_engine.calculate_customer_lifetime_value(
            request.user_id,
            request.historical_data
        )
        
        response = CLVCalculationResponse(
            user_id=result['user_id'],
            customer_lifetime_value=result['customer_lifetime_value'],
            clv_components=result['clv_components'],
            personalization_impact=result['personalization_impact'],
            value_breakdown=result['value_breakdown'],
            recommendations=result['recommendations'],
            timestamp=result['timestamp']
        )
        
        logger.info(f"CLV calculation completed for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"CLV calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"CLV calculation failed: {str(e)}")

@router.post("/dynamic-pricing", response_model=DynamicPricingResponse)
async def calculate_dynamic_pricing(
    request: DynamicPricingRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """計算動態定價"""
    try:
        logger.info(f"Calculating dynamic pricing for user {request.user_id}, service {request.service_id}")
        
        # 獲取用戶行為模型和偏好
        user_behavior = user_profile_analyzer.user_profiles.get(request.user_id)
        user_preferences = user_profile_analyzer.preference_profiles.get(request.user_id)
        
        # 創建臨時價值主張用於定價計算
        value_proposition = ValueProposition(
            name=f"Service {request.service_id}",
            target_segment=CustomerSegment.INDIVIDUAL
        )
        
        # 執行動態定價計算
        result = await value_service_engine.pricing_engine.calculate_personalized_dynamic_pricing(
            request.user_id,
            value_proposition,
            request.cost_data,
            request.market_conditions,
            user_behavior,
            user_preferences
        )
        
        response = DynamicPricingResponse(
            user_id=result['user_id'],
            service_id=request.service_id,
            base_price=result['base_pricing_strategy'].base_price,
            personalized_price=result['personalized_pricing']['final_price'],
            pricing_factors=result['pricing_factors'],
            optimization_suggestions=result['optimization_suggestions'],
            pricing_confidence=result['pricing_confidence'],
            valid_until=result['valid_until']
        )
        
        logger.info(f"Dynamic pricing calculation completed for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Dynamic pricing calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Dynamic pricing failed: {str(e)}")

@router.post("/utilization-analysis", response_model=UtilizationAnalysisResponse)
async def analyze_service_utilization(
    request: UtilizationAnalysisRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """分析服務使用效益"""
    try:
        logger.info(f"Analyzing utilization for user {request.user_id}, service {request.service_id}")
        
        # 獲取用戶行為模型
        user_behavior = user_profile_analyzer.user_profiles.get(request.user_id)
        
        # 執行使用效益分析
        metrics = await utilization_analyzer.analyze_service_utilization(
            request.user_id,
            request.service_id,
            request.usage_data,
            user_behavior
        )
        
        # 生成優化建議
        recommendations = await utilization_analyzer.generate_optimization_recommendations(
            request.user_id,
            request.service_id
        )
        
        response = UtilizationAnalysisResponse(
            user_id=request.user_id,
            service_id=request.service_id,
            utilization_status=metrics.utilization_status.value,
            realization_stage=metrics.realization_stage.value,
            realized_value=metrics.realized_value,
            value_realization_rate=metrics.value_realization_rate,
            optimization_recommendations=recommendations,
            efficiency_metrics={
                'task_completion_rate': metrics.task_completion_rate,
                'user_satisfaction_score': metrics.user_satisfaction_score,
                'outcome_success_rate': metrics.outcome_success_rate,
                'error_rate': metrics.error_rate
            }
        )
        
        logger.info(f"Utilization analysis completed for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Utilization analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Utilization analysis failed: {str(e)}")

@router.post("/service-recommendations", response_model=ServiceRecommendationResponse)
async def get_service_recommendations(
    request: ServiceRecommendationRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """獲取服務推薦"""
    try:
        logger.info(f"Generating service recommendations for user {request.user_id}")
        
        # 獲取用戶行為和偏好
        user_behavior = user_profile_analyzer.user_profiles.get(request.user_id)
        user_preferences = user_profile_analyzer.preference_profiles.get(request.user_id)
        
        if not user_behavior or not user_preferences:
            raise HTTPException(
                status_code=404, 
                detail="User behavior profile or preferences not found"
            )
        
        # 獲取當前服務（簡化版）
        current_services = []  # 實際實現中需要從數據庫獲取
        
        # 獲取使用效益數據
        utilization_metrics = None
        if request.current_services:
            # 從使用分析器獲取最新的使用效益數據
            metrics_key = f"{request.user_id}_{request.current_services[0]}"
            utilization_metrics = utilization_analyzer.utilization_data.get(metrics_key)
        
        # 生成推薦
        recommendations = await tier_system.recommendation_engine.generate_personalized_recommendations(
            request.user_id,
            user_behavior,
            user_preferences,
            current_services,
            utilization_metrics
        )
        
        # 轉換推薦格式
        formatted_recommendations = []
        total_expected_value = 0
        
        for rec in recommendations[:request.max_recommendations]:
            formatted_rec = {
                'recommendation_id': rec.recommendation_id,
                'recommended_tier': rec.recommended_tier.value,
                'recommendation_type': rec.recommendation_type.value,
                'rationale': rec.rationale,
                'key_benefits': rec.key_benefits,
                'expected_value_increase': rec.expected_value_increase,
                'investment_required': rec.investment_required,
                'roi_projection': rec.roi_projection,
                'confidence_level': rec.confidence_level,
                'implementation_timeline': rec.implementation_timeline
            }
            formatted_recommendations.append(formatted_rec)
            total_expected_value += rec.expected_value_increase
        
        response = ServiceRecommendationResponse(
            user_id=request.user_id,
            recommendations=formatted_recommendations,
            matching_confidence=np.mean([r['confidence_level'] for r in formatted_recommendations]) if formatted_recommendations else 0,
            personalization_score=user_behavior.model_confidence,
            total_expected_value=total_expected_value
        )
        
        logger.info(f"Generated {len(formatted_recommendations)} recommendations for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Service recommendation generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")

@router.post("/service-portfolio", response_model=ServicePortfolioResponse)
async def create_service_portfolio(
    request: ServicePortfolioRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """創建服務組合"""
    try:
        logger.info(f"Creating service portfolio for user {request.user_id}")
        
        # 獲取用戶行為和偏好
        user_behavior = user_profile_analyzer.user_profiles.get(request.user_id)
        user_preferences = user_profile_analyzer.preference_profiles.get(request.user_id)
        
        if not user_behavior or not user_preferences:
            raise HTTPException(
                status_code=404,
                detail="User behavior profile or preferences not found"
            )
        
        # 獲取當前服務和使用數據
        current_services = []  # 實際實現中從數據庫獲取
        usage_data = []  # 實際實現中從數據庫獲取
        
        # 創建個人化服務組合
        portfolio = await tier_system.create_personalized_service_portfolio(
            request.user_id,
            user_behavior,
            user_preferences,
            current_services,
            usage_data if request.include_usage_data else None
        )
        
        # 格式化升級推薦
        formatted_recommendations = []
        for rec in portfolio.upgrade_recommendations:
            formatted_rec = {
                'recommendation_id': rec.recommendation_id,
                'recommended_tier': rec.recommended_tier.value,
                'recommendation_type': rec.recommendation_type.value,
                'rationale': rec.rationale,
                'expected_value_increase': rec.expected_value_increase,
                'roi_projection': rec.roi_projection,
                'implementation_timeline': rec.implementation_timeline
            }
            formatted_recommendations.append(formatted_rec)
        
        response = ServicePortfolioResponse(
            user_id=request.user_id,
            portfolio_id=portfolio.portfolio_id,
            active_services_count=len(portfolio.active_services),
            total_value=portfolio.total_value,
            portfolio_roi=portfolio.portfolio_roi,
            personalization_score=portfolio.personalization_score,
            optimization_opportunities=portfolio.optimization_opportunities,
            upgrade_recommendations=formatted_recommendations
        )
        
        logger.info(f"Service portfolio created for user {request.user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Service portfolio creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Portfolio creation failed: {str(e)}")

# 管理和分析端點
@router.get("/analytics/tier-system")
async def get_tier_system_analytics(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """獲取分層系統分析"""
    try:
        analytics = tier_system.get_tier_system_analytics()
        return JSONResponse(content=analytics)
        
    except Exception as e:
        logger.error(f"Tier system analytics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics generation failed: {str(e)}")

@router.get("/analytics/utilization-summary")
async def get_utilization_summary(
    user_id: Optional[str] = Query(None, description="特定用戶ID"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """獲取使用效益總結"""
    try:
        summary = utilization_analyzer.get_utilization_summary(user_id)
        return JSONResponse(content=summary)
        
    except Exception as e:
        logger.error(f"Utilization summary failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")

@router.get("/health")
async def health_check():
    """健康檢查端點"""
    try:
        # 檢查核心組件
        components_status = {
            'value_service_engine': 'healthy',
            'utilization_analyzer': 'healthy',
            'tier_system': 'healthy',
            'user_profile_analyzer': 'healthy'
        }
        
        # 檢查數據狀態
        data_status = {
            'personalized_calculations': len(value_service_engine.personalized_calculations),
            'utilization_data': len(utilization_analyzer.utilization_data),
            'user_portfolios': len(tier_system.user_portfolios),
            'user_profiles': len(user_profile_analyzer.user_profiles)
        }
        
        return {
            'status': 'healthy',
            'timestamp': time.time(),
            'components': components_status,
            'data_status': data_status,
            'version': '1.0.0'
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }
        )

# 批量操作端點
@router.post("/batch/personalized-values")
async def batch_calculate_personalized_values(
    requests: List[PersonalizedValueRequest],
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """批量計算個人化價值"""
    try:
        if len(requests) > 100:
            raise HTTPException(status_code=400, detail="Batch size too large (max 100)")
        
        batch_id = str(uuid.uuid4())
        logger.info(f"Starting batch personalized value calculation {batch_id} with {len(requests)} requests")
        
        # 啟動背景任務處理批量請求
        background_tasks.add_task(process_batch_value_calculations, batch_id, requests)
        
        return {
            'batch_id': batch_id,
            'status': 'processing',
            'request_count': len(requests),
            'estimated_completion_time': time.time() + (len(requests) * 2)  # 估算2秒/請求
        }
        
    except Exception as e:
        logger.error(f"Batch value calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

async def process_batch_value_calculations(batch_id: str, requests: List[PersonalizedValueRequest]):
    """處理批量價值計算"""
    try:
        logger.info(f"Processing batch {batch_id}")
        results = []
        
        for request in requests:
            try:
                result = await value_service_engine.personalized_value_calculator.calculate_personalized_value(
                    request.user_id,
                    request.service_definition,
                    request.historical_data
                )
                results.append({
                    'user_id': request.user_id,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                logger.error(f"Batch item failed for user {request.user_id}: {e}")
                results.append({
                    'user_id': request.user_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 這裡可以將結果存儲到數據庫或緩存中
        logger.info(f"Batch {batch_id} completed with {len(results)} results")
        
    except Exception as e:
        logger.error(f"Batch processing {batch_id} failed: {e}")

# 導出路由器
__all__ = ['router']