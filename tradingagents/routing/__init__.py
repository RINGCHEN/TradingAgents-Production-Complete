#!/usr/bin/env python3
"""
TradingAgents Routing Module - 企業級AI任務智能路由系統
GPT-OSS整合任務1.3.1 - 完整的核心路由決策引擎

提供完整的企業級AI任務智能路由功能：
- AITaskRouter: 核心智能路由決策引擎
- EnhancedLLMService: 企業級增強LLM服務
- RoutingConfigManager: 動態路由策略配置管理
- 多維度成本效益分析和優化
- 完整決策審計追蹤和性能監控
- 動態路由策略調整和A/B測試支持
"""

# 核心路由引擎
from .ai_task_router import (
    AITaskRouter,
    RoutingStrategy,
    RoutingWeights,
    DecisionFactor,
    ModelScore,
    RoutingContext,
    DecisionAudit,
    
    # 異常類型
    AITaskRouterError,
    RoutingDecisionError,
    CostCalculationError,
    ModelEvaluationError
)

# 企業級增強LLM服務
from .enhanced_llm_service import (
    EnhancedLLMService,
    create_enhanced_llm_service,
    CompatibleLLMClient,
    create_compatible_llm_client,
    get_global_enhanced_service,
    shutdown_global_enhanced_service
)

# 路由配置管理
from .routing_config import (
    RoutingConfigManager,
    StrategyTemplate,
    RoutingPolicy,
    ConfigurationProfile
)

# LLM客戶端整合（向後兼容）
from .llm_client_integration import (
    EnhancedLLMClient,
    create_enhanced_llm_client,
    get_global_enhanced_llm_client,
    close_global_enhanced_llm_client
)

__all__ = [
    # 核心路由引擎
    'AITaskRouter',
    'RoutingStrategy',
    'RoutingWeights',
    'DecisionFactor',
    'ModelScore',
    'RoutingContext',
    'DecisionAudit',
    
    # 企業級增強LLM服務
    'EnhancedLLMService',
    'CompatibleLLMClient',
    'create_enhanced_llm_service',
    'create_compatible_llm_client',
    'get_global_enhanced_service',
    'shutdown_global_enhanced_service',
    
    # 路由配置管理
    'RoutingConfigManager',
    'StrategyTemplate',
    'RoutingPolicy', 
    'ConfigurationProfile',
    
    # LLM客戶端整合（向後兼容）
    'EnhancedLLMClient',
    'create_enhanced_llm_client',
    'get_global_enhanced_llm_client',
    'close_global_enhanced_llm_client',
    
    # 異常類型
    'AITaskRouterError',
    'RoutingDecisionError',
    'CostCalculationError',
    'ModelEvaluationError',
    
    # 預設權重創建函數
    'create_balanced_weights',
    'create_cost_optimized_weights',
    'create_performance_optimized_weights',
    'create_quality_first_weights',
    'create_privacy_first_weights',
    'get_strategy_weights'
]

# 版本信息
__version__ = '1.3.1'
__author__ = 'TradingAgents Team'
__description__ = 'Enterprise AI Task Intelligent Routing System - GPT-OSS Integration Complete'

# 默認配置
DEFAULT_ROUTER_CONFIG = {
    'default_strategy': 'balanced',
    'enable_cost_optimization': True,
    'enable_performance_learning': True,
    'enable_load_balancing': True,
    'max_fallback_attempts': 3,
    'decision_confidence_threshold': 0.7,
    'cost_variance_threshold': 0.15,
    'latency_variance_threshold': 0.20,
    'quality_variance_threshold': 0.10,
    'performance_cache_ttl': 3600,
    'max_decision_history': 1000,
    'enable_audit_logging': True,
    'audit_detail_level': 'full'
}

def create_router(config: dict = None, **kwargs):
    """
    創建AI任務路由器的便利函數
    
    Args:
        config: 路由器配置字典
        **kwargs: 額外參數傳遞給AITaskRouter構造函數
        
    Returns:
        配置好的AITaskRouter實例
    """
    final_config = DEFAULT_ROUTER_CONFIG.copy()
    if config:
        final_config.update(config)
    
    return AITaskRouter(config=final_config, **kwargs)

def create_balanced_weights() -> RoutingWeights:
    """創建平衡路由權重配置"""
    return RoutingWeights(
        cost=0.25,
        latency=0.25,
        quality=0.25,
        availability=0.15,
        privacy=0.05,
        user_preference=0.05
    )

def create_cost_optimized_weights() -> RoutingWeights:
    """創建成本優化路由權重配置"""
    return RoutingWeights(
        cost=0.5,
        latency=0.15,
        quality=0.2,
        availability=0.1,
        privacy=0.03,
        user_preference=0.02
    )

def create_performance_optimized_weights() -> RoutingWeights:
    """創建性能優化路由權重配置"""
    return RoutingWeights(
        cost=0.1,
        latency=0.4,
        quality=0.35,
        availability=0.1,
        privacy=0.03,
        user_preference=0.02
    )

def create_quality_first_weights() -> RoutingWeights:
    """創建品質優先路由權重配置"""
    return RoutingWeights(
        cost=0.1,
        latency=0.15,
        quality=0.5,
        availability=0.15,
        privacy=0.05,
        user_preference=0.05
    )

def create_privacy_first_weights() -> RoutingWeights:
    """創建隱私優先路由權重配置"""
    return RoutingWeights(
        cost=0.15,
        latency=0.15,
        quality=0.2,
        availability=0.1,
        privacy=0.35,
        user_preference=0.05
    )

# 便利函數映射
WEIGHT_CREATORS = {
    RoutingStrategy.BALANCED: create_balanced_weights,
    RoutingStrategy.COST_OPTIMIZED: create_cost_optimized_weights,
    RoutingStrategy.PERFORMANCE_OPTIMIZED: create_performance_optimized_weights,
    RoutingStrategy.QUALITY_FIRST: create_quality_first_weights,
    RoutingStrategy.PRIVACY_FIRST: create_privacy_first_weights,
}

def get_strategy_weights(strategy: RoutingStrategy) -> RoutingWeights:
    """
    根據策略獲取對應的權重配置
    
    Args:
        strategy: 路由策略
        
    Returns:
        對應的權重配置
    """
    creator = WEIGHT_CREATORS.get(strategy, create_balanced_weights)
    return creator()