#!/usr/bin/env python3
"""
Multi-modal Learning System - 多模態學習系統
天工 (TianGong) - ART增強的多模態智能分析系統

此模組提供：
1. 多模態數據整合架構
2. 文本處理和語義分析
3. 時間序列數據融合
4. 跨模態特徵融合算法
5. 智能權重優化機制
"""

from .multimodal_data_integrator import (
    MultiModalDataIntegrator,
    DataModality,
    IntegrationStrategy,
    ModalityWeights
)

from .text_processor import (
    TextProcessor,
    TextAnalysisType,
    SentimentResult,
    KeywordExtraction,
    TopicAnalysis
)

from .time_series_fusion import (
    TimeSeriesFusion,
    FusionMethod,
    TemporalAlignment,
    SeriesPattern
)

from .feature_fusion_engine import (
    FeatureFusionEngine,
    FusionAlgorithm,
    FeatureImportance,
    CrossModalAttention
)

from .multimodal_analyzer import (
    MultiModalAnalyzer,
    AnalysisMode,
    MultiModalResult,
    ConfidenceMetrics
)

from .realtime_adjustment import (
    RealTimeAdjustmentManager,
    AdjustmentTrigger,
    AdjustmentAction,
    PerformanceMetric
)

from .ab_testing_framework import (
    ABTestingFramework,
    ABTestExperiment,
    ExperimentStatus,
    TrafficSplitMethod,
    MetricType
)

from .group_intelligence import (
    GroupIntelligenceSystem,
    LearningParticipant,
    GroupLearningTask,
    LearningMode,
    ConsensusMethod,
    ParticipantRole
)

__version__ = "1.0.0"
__author__ = "TianGong ART Team"

__all__ = [
    # 核心組件
    "MultiModalDataIntegrator",
    "TextProcessor", 
    "TimeSeriesFusion",
    "FeatureFusionEngine",
    "MultiModalAnalyzer",
    "RealTimeAdjustmentManager",
    "ABTestingFramework",
    "GroupIntelligenceSystem",
    
    # 數據類型
    "DataModality",
    "TextAnalysisType", 
    "FusionMethod",
    "FusionAlgorithm",
    "AnalysisMode",
    "AdjustmentTrigger",
    "AdjustmentAction",
    "ExperimentStatus",
    "TrafficSplitMethod",
    "MetricType",
    "LearningMode",
    "ConsensusMethod",
    "ParticipantRole",
    
    # 結果類型
    "SentimentResult",
    "KeywordExtraction",
    "TopicAnalysis",
    "SeriesPattern",
    "MultiModalResult",
    "ConfidenceMetrics",
    "PerformanceMetric",
    "ABTestExperiment",
    "LearningParticipant",
    "GroupLearningTask",
    
    # 配置類型
    "IntegrationStrategy",
    "ModalityWeights",
    "TemporalAlignment",
    "FeatureImportance",
    "CrossModalAttention"
]

# 系統配置
DEFAULT_CONFIG = {
    "text_processing": {
        "language": "zh-TW",
        "sentiment_model": "chinese-roberta-sentiment",
        "keyword_extraction_method": "jieba_tfidf",
        "topic_modeling_algorithm": "LDA"
    },
    "time_series": {
        "fusion_method": "attention_weighted",
        "temporal_window": 30,  # 天數
        "alignment_strategy": "forward_fill"
    },
    "feature_fusion": {
        "algorithm": "cross_modal_attention",
        "weight_optimization": "adaptive",
        "regularization": 0.1
    },
    "performance": {
        "batch_size": 32,
        "max_workers": 4,
        "cache_enabled": True,
        "cache_ttl": 3600  # 秒
    },
    "realtime_adjustment": {
        "monitoring_enabled": True,
        "monitoring_interval": 60,  # 秒
        "performance_window": 3600,  # 秒
        "performance_thresholds": {
            "accuracy": 0.7,
            "processing_time": 30.0,
            "confidence": 0.6,
            "consistency": 0.8,
            "error_rate": 0.1
        }
    },
    "ab_testing": {
        "significance_level": 0.05,
        "statistical_power": 0.8,
        "min_sample_size": 1000,
        "early_stopping": True,
        "analysis_interval": 3600  # 秒
    },
    "group_intelligence": {
        "max_learning_iterations": 100,
        "learning_iteration_interval": 5,  # 秒
        "convergence_threshold": 0.01,
        "default_learning_mode": "collaborative",
        "default_consensus_method": "weighted_vote"
    }
}

def create_multimodal_analyzer(config: dict = None) -> MultiModalAnalyzer:
    """
    創建多模態分析器實例
    
    Args:
        config: 配置字典，如果為None則使用默認配置
        
    Returns:
        配置好的MultiModalAnalyzer實例
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    return MultiModalAnalyzer(config=config)

def get_supported_modalities() -> list:
    """
    獲取支援的數據模態列表
    
    Returns:
        支援的數據模態列表
    """
    return [
        DataModality.TEXT,
        DataModality.NUMERICAL,
        DataModality.TIME_SERIES,
        DataModality.CATEGORICAL,
        DataModality.FINANCIAL_RATIOS,
        DataModality.MARKET_DATA,
        DataModality.NEWS_SENTIMENT,
        DataModality.SOCIAL_MEDIA
    ]

def get_fusion_algorithms() -> list:
    """
    獲取可用的特徵融合算法
    
    Returns:
        可用的融合算法列表
    """
    return [
        FusionAlgorithm.WEIGHTED_AVERAGE,
        FusionAlgorithm.ATTENTION_MECHANISM,
        FusionAlgorithm.CROSS_MODAL_ATTENTION,
        FusionAlgorithm.MULTIMODAL_TRANSFORMER,
        FusionAlgorithm.ADAPTIVE_FUSION,
        FusionAlgorithm.HIERARCHICAL_FUSION
    ]

# 版本兼容性檢查
def check_dependencies():
    """檢查必要的依賴是否已安裝"""
    required_packages = [
        'numpy', 'pandas', 'scikit-learn',
        'transformers', 'jieba', 'torch',
        'matplotlib', 'seaborn'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"WARNING: 以下套件未安裝: {', '.join(missing_packages)}")
        print("請安裝缺少的套件以使用完整功能")
        
    return len(missing_packages) == 0

# 初始化時檢查依賴
_dependencies_ok = check_dependencies()

if not _dependencies_ok:
    print("INFO: 多模態學習系統可能功能受限，建議安裝完整依賴")