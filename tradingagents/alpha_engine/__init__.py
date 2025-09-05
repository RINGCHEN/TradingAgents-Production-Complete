#!/usr/bin/env python3
"""
Alpha Engine Module
阿爾法引擎模組

GPT-OSS整合任務3.1-3.3 - 阿爾法引擎產品化
提供專業化模型開發和阿爾法引擎核心系統

主要組件：
- ModelFineTuningInfrastructure: 模型微調基礎設施（任務3.1.1）
- TaiwanNewsAnalysisModel: 台股新聞情緒分析模型（任務3.1.2）
- FinancialReportExtractionModel: 財報數據提取模型（任務3.1.3）
- AlphaEngine: 阿爾法引擎核心類（任務3.2.1）
- MemberTierAccessControl: 會員分級訪問控制（任務3.2.2）
- AnalysisReportIntegration: 分析報告系統集成（任務3.2.3）
- UpgradeConversionSystem: 升級轉換系統（任務3.3.1）
- ValueDisplayMechanism: 價值展示機制（任務3.3.2）

功能特性：
1. GPU訓練環境和模型微調基礎設施
2. 微調數據管道和版本管理系統
3. 微調性能評估框架
4. 專業化台股新聞情緒分析
5. 智能財報數據提取
6. 阿爾法洞察生成和管理
7. 會員分級訪問控制
8. 分析報告系統無縫集成
9. 升級轉換優化
10. 價值展示和社會證明
"""

from .fine_tuning_infrastructure import (
    ModelFineTuningInfrastructure,
    FineTuningConfig,
    FineTuningJob,
    ModelVersionManager,
    FineTuningStatus,
    ModelEvaluationFramework,
    FineTuningMetrics,
    FineTuningJobRequest,
    FineTuningJobResponse
)

from .taiwan_news_model import (
    TaiwanNewsAnalysisModel,
    NewsAnalysisConfig,
    NewsAnalysisResult,
    SentimentAnalysis,
    MarketImpactAssessment,
    NewsDataPreprocessor,
    NewsModelTrainer
)

from .financial_report_model import (
    FinancialReportExtractionModel,
    ReportExtractionConfig,
    ReportExtractionResult,
    FinancialDataExtractor,
    ReportStructureAnalyzer,
    ReportModelTrainer
)

from .alpha_engine_core import (
    AlphaEngine,
    AlphaInsight,
    AlphaInsightType,
    AlphaInsightPriority,
    AlphaEngineConfig,
    InsightGenerationRequest,
    InsightGenerationResponse
)

from .member_access_control import (
    MemberTierAccessControl,
    MemberTier,
    AccessLevel,
    ContentGating,
    UpgradePrompt,
    AccessControlConfig,
    AccessRequest,
    AccessResponse
)

from .report_integration import (
    AnalysisReportIntegration,
    ReportIntegrationConfig,
    StandardInsight,
    AlphaInsightComparison,
    ReportUpgradePromotion,
    IntegrationRequest,
    IntegrationResponse
)

from .conversion_system import (
    UpgradeConversionSystem,
    ConversionConfig,
    ConversionTrigger,
    ConversionOpportunity,
    ConversionTracking,
    ConversionMetrics,
    ConversionRequest,
    ConversionResponse
)

from .value_display import (
    ValueDisplayMechanism,
    ValueDisplayConfig,
    AccuracyShowcase,
    UniqueInsightHighlight,
    SocialProof,
    ValueQuantification,
    DisplayRequest,
    DisplayResponse
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude Code Artisan"
__description__ = "Alpha Engine Module for GPT-OSS Integration Stage 3"

# 導出所有公共接口
__all__ = [
    # 模型微調基礎設施 (任務 3.1.1)
    "ModelFineTuningInfrastructure",
    "FineTuningConfig",
    "FineTuningJob",
    "ModelVersionManager",
    "FineTuningStatus",
    "ModelEvaluationFramework",
    "FineTuningMetrics",
    "FineTuningJobRequest",
    "FineTuningJobResponse",
    
    # 台股新聞情緒分析模型 (任務 3.1.2)
    "TaiwanNewsAnalysisModel",
    "NewsAnalysisConfig",
    "NewsAnalysisResult",
    "SentimentAnalysis",
    "MarketImpactAssessment",
    "NewsDataPreprocessor",
    "NewsModelTrainer",
    
    # 財報數據提取模型 (任務 3.1.3)
    "FinancialReportExtractionModel",
    "ReportExtractionConfig",
    "ReportExtractionResult",
    "FinancialDataExtractor",
    "ReportStructureAnalyzer",
    "ReportModelTrainer",
    
    # 阿爾法引擎核心類 (任務 3.2.1)
    "AlphaEngine",
    "AlphaInsight",
    "AlphaInsightType",
    "AlphaInsightPriority",
    "AlphaEngineConfig",
    "InsightGenerationRequest",
    "InsightGenerationResponse",
    
    # 會員分級訪問控制 (任務 3.2.2)
    "MemberTierAccessControl",
    "MemberTier",
    "AccessLevel",
    "ContentGating",
    "UpgradePrompt",
    "AccessControlConfig",
    "AccessRequest",
    "AccessResponse",
    
    # 分析報告系統集成 (任務 3.2.3)
    "AnalysisReportIntegration",
    "ReportIntegrationConfig",
    "StandardInsight",
    "AlphaInsightComparison",
    "ReportUpgradePromotion",
    "IntegrationRequest",
    "IntegrationResponse",
    
    # 升級轉換系統 (任務 3.3.1)
    "UpgradeConversionSystem",
    "ConversionConfig",
    "ConversionTrigger",
    "ConversionOpportunity",
    "ConversionTracking",
    "ConversionMetrics",
    "ConversionRequest",
    "ConversionResponse",
    
    # 價值展示機制 (任務 3.3.2)
    "ValueDisplayMechanism",
    "ValueDisplayConfig",
    "AccuracyShowcase",
    "UniqueInsightHighlight",
    "SocialProof",
    "ValueQuantification",
    "DisplayRequest",
    "DisplayResponse"
]