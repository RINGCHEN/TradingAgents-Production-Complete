#!/usr/bin/env python3
"""
Deep Behavior Learning Module - 深度行為學習模組
天工 (TianGong) - 為TradingAgents提供深度行為學習和預測分析

此模組提供：
1. DeepBehaviorAnalyzer - 深度行為分析器
2. BehaviorPredictor - 行為預測器  
3. AdaptiveLearningEngine - 自適應學習引擎
4. ReinforcementLearningAgent - 強化學習智能體
5. BehaviorOptimizer - 行為優化器
"""

from .deep_behavior_analyzer import (
    DeepBehaviorAnalyzer,
    BehaviorMetrics,
    BehaviorInsight,
    BehaviorCluster
)

from .behavior_predictor import (
    BehaviorPredictor,
    PredictionModel,
    BehaviorForecast,
    ModelType
)

from .adaptive_learning_engine import (
    AdaptiveLearningEngine,
    LearningStrategy,
    AdaptationResult,
    LearningMetrics
)

from .reinforcement_learning_agent import (
    ReinforcementLearningAgent,
    RLAction,
    RLState,
    RLReward
)

from .behavior_optimizer import (
    BehaviorOptimizer,
    OptimizationResult,
    OptimizationObjective
)

__all__ = [
    'DeepBehaviorAnalyzer',
    'BehaviorMetrics', 
    'BehaviorInsight',
    'BehaviorCluster',
    'BehaviorPredictor',
    'PredictionModel',
    'BehaviorForecast',
    'ModelType',
    'AdaptiveLearningEngine',
    'LearningStrategy',
    'AdaptationResult', 
    'LearningMetrics',
    'ReinforcementLearningAgent',
    'RLAction',
    'RLState',
    'RLReward',
    'BehaviorOptimizer',
    'OptimizationResult',
    'OptimizationObjective'
]

__version__ = '1.0.0'