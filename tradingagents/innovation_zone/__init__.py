#!/usr/bin/env python3
"""
Innovation Zone Module
創新特區模組

GPT-OSS整合任務2.2.1 - 創新特區機制
提供完整的創新特區管理功能，保護顛覆式創新能力

主要組件：
- InnovationZoneService: 創新特區管理服務
- TechnicalMilestoneTracker: 技術里程碑追蹤引擎
- ProjectAdmissionEvaluator: 項目准入評估系統
- BudgetROIManager: 預算分配和ROI豁免管理器
- InnovationAnomalyDetector: 異常檢測和預警機制
- InnovationZoneDB: 數據庫管理層
- ProjectPerformanceMonitor: 項目性能監控系統（GPT-OSS任務2.2.2）
- ObjectiveDecisionEngine: 客觀決策引擎（GPT-OSS任務2.2.3）
- ProjectLifecycleManager: 項目生命週期管理系統（GPT-OSS任務2.2.4）

功能特性：
1. 創新特區預算分配（5-10% 研發預算）
2. ROI豁免權規則（前四季度免考核）
3. 技術里程碑和用戶行為指標追蹤
4. 創新項目准入標準評估
5. 創新項目生命週期管理
6. 異常檢測和預警機制
7. 項目性能監控和健康評估（GPT-OSS任務2.2.2）
8. 客觀決策建議和自動化決策支持（GPT-OSS任務2.2.3）
9. 自動化階段推進和關卡控制（GPT-OSS任務2.2.4）
"""

from .innovation_zone_service import InnovationZoneService
from .milestone_tracker import TechnicalMilestoneTracker
from .project_admission_evaluator import ProjectAdmissionEvaluator
from .budget_roi_manager import BudgetROIManager
from .anomaly_detector import InnovationAnomalyDetector
from .innovation_zone_db import InnovationZoneDB
from .project_performance_monitor import (
    ProjectPerformanceMonitor,
    ProjectPerformanceMetrics,
    ProjectPerformanceAlert,
    ProjectHealthStatus,
    PerformanceTrend
)
from .objective_decision_engine import (
    ObjectiveDecisionEngine,
    DecisionRecommendation,
    DecisionCriteria,
    DecisionContext,
    DecisionType,
    DecisionConfidence,
    DecisionUrgency,
    DecisionImpact
)
from .project_lifecycle_manager import (
    ProjectLifecycleManager,
    ProjectLifecycleState,
    LifecycleGate,
    LifecycleAction,
    LifecycleEvent,
    LifecycleGateType,
    LifecycleActionType,
    LifecycleEventType,
    GateStatus
)

# 導入核心模型
from .models import (
    # 枚舉類型
    InnovationType,
    ProjectStage,
    ROIExemptionStatus,
    MilestoneType,
    AnomalyType,
    AdmissionCriteria,
    
    # 數據模型
    InnovationZone,
    InnovationProject,
    InnovationBudgetAllocation,
    InnovationBudgetTracking,
    TechnicalMilestone,
    UserBehaviorMetrics,
    AnomalyDetection,
    
    # 請求/響應模型
    InnovationZoneCreate,
    InnovationProjectCreate,
    TechnicalMilestoneCreate,
    UserBehaviorMetricsCreate,
    AnomalyDetectionCreate,
    InnovationZoneResponse,
    InnovationProjectResponse,
    InnovationAnalyticsRequest,
    InnovationAnalyticsResponse
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude Code Artisan"
__description__ = "Innovation Zone Management System for GPT-OSS Integration"

# 導出所有公共接口
__all__ = [
    # 核心服務
    "InnovationZoneService",
    "TechnicalMilestoneTracker", 
    "ProjectAdmissionEvaluator",
    "BudgetROIManager",
    "InnovationAnomalyDetector",
    "InnovationZoneDB",
    "ProjectPerformanceMonitor",
    "ProjectPerformanceMetrics",
    "ProjectPerformanceAlert",
    "ProjectHealthStatus",
    "PerformanceTrend",
    "ObjectiveDecisionEngine",
    "DecisionRecommendation",
    "DecisionCriteria",
    "DecisionContext",
    "DecisionType",
    "DecisionConfidence",
    "DecisionUrgency",
    "DecisionImpact",
    "ProjectLifecycleManager",
    "ProjectLifecycleState",
    "LifecycleGate",
    "LifecycleAction",
    "LifecycleEvent",
    "LifecycleGateType",
    "LifecycleActionType",
    "LifecycleEventType",
    "GateStatus",
    
    # 枚舉類型
    "InnovationType",
    "ProjectStage",
    "ROIExemptionStatus",
    "MilestoneType",
    "AnomalyType",
    "AdmissionCriteria",
    
    # 數據模型
    "InnovationZone",
    "InnovationProject",
    "InnovationBudgetAllocation",
    "InnovationBudgetTracking",
    "TechnicalMilestone",
    "UserBehaviorMetrics",
    "AnomalyDetection",
    
    # 請求/響應模型
    "InnovationZoneCreate",
    "InnovationProjectCreate",
    "TechnicalMilestoneCreate",
    "UserBehaviorMetricsCreate",
    "AnomalyDetectionCreate",
    "InnovationZoneResponse",
    "InnovationProjectResponse",
    "InnovationAnalyticsRequest",
    "InnovationAnalyticsResponse"
]