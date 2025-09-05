#!/usr/bin/env python3
"""
Innovation Zone Database Models for GPT-OSS Integration
GPT-OSS創新特區數據模型 - 任務2.2.1

企業級創新特區管理系統，用於保護顛覆式創新能力的：
- 創新特區預算分配（5-10% 研發預算）
- ROI豁免權規則（前四季度免考核）
- 技術里程碑和用戶行為指標追蹤
- 創新項目准入標準評估
- 創新項目生命週期管理
"""

import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Union
from decimal import Decimal
from enum import Enum
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Date, Text, Boolean,
    JSON, UUID, Index, ForeignKey, UniqueConstraint, Numeric, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator, condecimal

from ..database.database import Base

# ==================== 核心枚舉類型 ====================

class InnovationType(str, Enum):
    """創新類型枚舉"""
    DISRUPTIVE = "disruptive"              # 顛覆式創新
    INCREMENTAL = "incremental"            # 漸進式創新
    BREAKTHROUGH = "breakthrough"          # 突破性創新
    PLATFORM = "platform"                 # 平台創新
    BUSINESS_MODEL = "business_model"      # 商業模式創新
    TECHNOLOGY = "technology"              # 技術創新
    PROCESS = "process"                    # 流程創新

class ProjectStage(str, Enum):
    """項目階段枚舉"""
    CONCEPT = "concept"                    # 概念階段
    FEASIBILITY = "feasibility"            # 可行性研究
    PROTOTYPE = "prototype"                # 原型開發
    PILOT = "pilot"                        # 試點測試
    SCALING = "scaling"                    # 規模化
    MATURE = "mature"                      # 成熟階段
    DISCONTINUED = "discontinued"          # 已停止

class ROIExemptionStatus(str, Enum):
    """ROI豁免狀態枚舉"""
    EXEMPT = "exempt"                      # 豁免中
    PARTIAL_EXEMPT = "partial_exempt"      # 部分豁免
    MONITORING = "monitoring"              # 監控中
    EVALUATION_REQUIRED = "evaluation_required"  # 需要評估
    EXPIRED = "expired"                    # 已過期

class MilestoneType(str, Enum):
    """里程碑類型枚舉"""
    TECHNICAL = "technical"                # 技術里程碑
    USER_ADOPTION = "user_adoption"        # 用戶採用里程碑
    MARKET_VALIDATION = "market_validation"  # 市場驗證里程碑
    REVENUE = "revenue"                    # 收益里程碑
    PARTNERSHIP = "partnership"            # 合作夥伴里程碑
    REGULATORY = "regulatory"              # 法規里程碑
    SCALABILITY = "scalability"            # 可擴展性里程碑

class AdmissionCriteria(str, Enum):
    """准入標準枚舉"""
    INNOVATION_POTENTIAL = "innovation_potential"      # 創新潛力
    MARKET_DISRUPTION = "market_disruption"           # 市場顛覆性
    TECHNICAL_FEASIBILITY = "technical_feasibility"    # 技術可行性
    TEAM_CAPABILITY = "team_capability"                # 團隊能力
    RESOURCE_REQUIREMENT = "resource_requirement"      # 資源需求
    STRATEGIC_ALIGNMENT = "strategic_alignment"        # 戰略一致性
    COMPETITIVE_ADVANTAGE = "competitive_advantage"    # 競爭優勢

class AnomalyType(str, Enum):
    """異常類型枚舉"""
    BUDGET_OVERRUN = "budget_overrun"                 # 預算超支
    MILESTONE_DELAY = "milestone_delay"               # 里程碑延遲
    LOW_USER_ENGAGEMENT = "low_user_engagement"       # 用戶參與度低
    TECHNICAL_BOTTLENECK = "technical_bottleneck"     # 技術瓶頸
    MARKET_REJECTION = "market_rejection"             # 市場拒絕
    TEAM_ATTRITION = "team_attrition"                # 團隊流失
    RESOURCE_CONSTRAINT = "resource_constraint"       # 資源約束

# ==================== 核心數據模型 ====================

class InnovationZone(Base):
    """創新特區表"""
    __tablename__ = "innovation_zones"
    
    # 主鍵和基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zone_name = Column(String(100), unique=True, nullable=False, index=True)
    zone_code = Column(String(20), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # 創新特區配置
    innovation_focus = Column(String(50), nullable=False)  # 創新重點領域
    target_innovation_types = Column(JSON, nullable=False)  # 目標創新類型列表
    
    # 預算配置
    total_budget_allocation = Column(Numeric(15, 2), nullable=False)
    budget_percentage_of_rd = Column(Numeric(5, 2), nullable=False)  # 占研發預算百分比
    quarterly_budget_limit = Column(Numeric(15, 2), nullable=True)
    
    # ROI豁免配置
    roi_exemption_quarters = Column(Integer, nullable=False, default=4)  # 豁免季度數
    roi_exemption_threshold = Column(Numeric(5, 2), nullable=True)  # 豁免閾值
    
    # 管理信息
    zone_manager = Column(String(100), nullable=False)
    sponsor_department = Column(String(50), nullable=False)
    
    # 准入標準權重配置
    admission_criteria_weights = Column(JSON, nullable=False)  # 各准入標準權重
    minimum_admission_score = Column(Numeric(5, 2), nullable=False, default=75.0)
    
    # 狀態和元數據
    is_active = Column(Boolean, nullable=False, default=True)
    established_date = Column(Date, nullable=False, default=date.today)
    review_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 關係
    innovation_projects = relationship("InnovationProject", back_populates="innovation_zone", cascade="all, delete-orphan")
    budget_allocations = relationship("InnovationBudgetAllocation", back_populates="innovation_zone", cascade="all, delete-orphan")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_innovation_zone_focus', 'innovation_focus'),
        Index('idx_innovation_zone_manager', 'zone_manager'),
        CheckConstraint('total_budget_allocation > 0', name='check_positive_budget'),
        CheckConstraint('budget_percentage_of_rd BETWEEN 5 AND 15', name='check_valid_rd_percentage'),
        CheckConstraint('roi_exemption_quarters BETWEEN 1 AND 8', name='check_valid_exemption_quarters'),
        CheckConstraint('minimum_admission_score BETWEEN 50 AND 100', name='check_valid_admission_score'),
    )

class InnovationProject(Base):
    """創新項目表"""
    __tablename__ = "innovation_projects"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    innovation_zone_id = Column(UUID(as_uuid=True), ForeignKey('innovation_zones.id'), nullable=False, index=True)
    
    # 項目基本信息
    project_name = Column(String(200), nullable=False)
    project_description = Column(Text, nullable=False)
    innovation_type = Column(String(30), nullable=False)
    current_stage = Column(String(30), nullable=False, default=ProjectStage.CONCEPT.value)
    
    # 項目團隊
    project_lead = Column(String(100), nullable=False)
    team_size = Column(Integer, nullable=False, default=1)
    team_members = Column(JSON, nullable=True)  # 團隊成員列表
    
    # 項目時間線
    start_date = Column(Date, nullable=False)
    planned_end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    
    # ROI豁免信息
    roi_exemption_status = Column(String(30), nullable=False, default=ROIExemptionStatus.EXEMPT.value)
    roi_exemption_start_date = Column(Date, nullable=False, default=date.today)
    roi_exemption_end_date = Column(Date, nullable=True)
    
    # 准入評分
    admission_score = Column(Numeric(5, 2), nullable=False)
    admission_criteria_scores = Column(JSON, nullable=False)  # 各項標準得分
    admission_date = Column(Date, nullable=False, default=date.today)
    admission_reviewed_by = Column(String(100), nullable=False)
    
    # 項目狀態
    is_active = Column(Boolean, nullable=False, default=True)
    priority_level = Column(String(20), nullable=False, default='medium')  # high/medium/low
    
    # 項目標籤和分類
    project_tags = Column(JSON, nullable=True)
    strategic_importance = Column(String(20), nullable=False, default='medium')
    
    # 項目配置
    project_configuration = Column(JSON, nullable=True)  # 項目特殊配置
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=False)
    
    # 關係
    innovation_zone = relationship("InnovationZone", back_populates="innovation_projects")
    milestones = relationship("TechnicalMilestone", back_populates="innovation_project", cascade="all, delete-orphan")
    budget_tracking = relationship("InnovationBudgetTracking", back_populates="innovation_project", cascade="all, delete-orphan")
    user_behavior_metrics = relationship("UserBehaviorMetrics", back_populates="innovation_project", cascade="all, delete-orphan")
    anomaly_detections = relationship("AnomalyDetection", back_populates="innovation_project", cascade="all, delete-orphan")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_innovation_project_stage', 'current_stage'),
        Index('idx_innovation_project_lead', 'project_lead'),
        Index('idx_innovation_project_type', 'innovation_type'),
        Index('idx_innovation_project_active', 'is_active'),
        CheckConstraint('admission_score BETWEEN 0 AND 100', name='check_valid_admission_score'),
        CheckConstraint('team_size > 0', name='check_positive_team_size'),
    )

class InnovationBudgetAllocation(Base):
    """創新特區預算分配表"""
    __tablename__ = "innovation_budget_allocations"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innovation_zone_id = Column(UUID(as_uuid=True), ForeignKey('innovation_zones.id'), nullable=False, index=True)
    
    # 預算期間
    fiscal_year = Column(Integer, nullable=False, index=True)
    quarter = Column(Integer, nullable=False)  # 1-4
    allocation_date = Column(Date, nullable=False, default=date.today)
    
    # 預算分配
    total_allocated_budget = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 分類預算
    research_budget = Column(Numeric(15, 2), nullable=False, default=0)
    development_budget = Column(Numeric(15, 2), nullable=False, default=0)
    prototyping_budget = Column(Numeric(15, 2), nullable=False, default=0)
    testing_budget = Column(Numeric(15, 2), nullable=False, default=0)
    market_validation_budget = Column(Numeric(15, 2), nullable=False, default=0)
    talent_acquisition_budget = Column(Numeric(15, 2), nullable=False, default=0)
    infrastructure_budget = Column(Numeric(15, 2), nullable=False, default=0)
    contingency_budget = Column(Numeric(15, 2), nullable=False, default=0)
    
    # 預算使用跟踪
    allocated_budget = Column(Numeric(15, 2), nullable=False)
    committed_budget = Column(Numeric(15, 2), nullable=False, default=0)
    spent_budget = Column(Numeric(15, 2), nullable=False, default=0)
    remaining_budget = Column(Numeric(15, 2), nullable=False)
    
    # 預算狀態
    allocation_status = Column(String(20), nullable=False, default='active')  # active/frozen/closed
    approval_required = Column(Boolean, nullable=False, default=False)
    
    # 預算備註
    allocation_notes = Column(Text, nullable=True)
    budget_constraints = Column(JSON, nullable=True)  # 預算約束條件
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # 關係
    innovation_zone = relationship("InnovationZone", back_populates="budget_allocations")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_budget_allocation_period', 'fiscal_year', 'quarter'),
        Index('idx_budget_allocation_status', 'allocation_status'),
        UniqueConstraint('innovation_zone_id', 'fiscal_year', 'quarter', name='uq_budget_allocation_period'),
        CheckConstraint('total_allocated_budget > 0', name='check_positive_total_budget'),
        CheckConstraint('quarter BETWEEN 1 AND 4', name='check_valid_quarter'),
        CheckConstraint('allocated_budget >= 0', name='check_non_negative_allocated'),
        CheckConstraint('spent_budget >= 0', name='check_non_negative_spent'),
        CheckConstraint('remaining_budget >= 0', name='check_non_negative_remaining'),
    )

class InnovationBudgetTracking(Base):
    """創新項目預算追蹤表"""
    __tablename__ = "innovation_budget_tracking"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innovation_project_id = Column(UUID(as_uuid=True), ForeignKey('innovation_projects.id'), nullable=False, index=True)
    
    # 交易信息
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False)  # allocation/expense/adjustment
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 分類信息
    expense_category = Column(String(50), nullable=False)
    expense_subcategory = Column(String(50), nullable=True)
    description = Column(String(200), nullable=False)
    
    # 預算狀態
    project_total_budget = Column(Numeric(15, 2), nullable=False)
    budget_utilized = Column(Numeric(15, 2), nullable=False)
    budget_remaining = Column(Numeric(15, 2), nullable=False)
    budget_utilization_rate = Column(Numeric(5, 2), nullable=False)
    
    # ROI豁免相關
    is_roi_exempt_period = Column(Boolean, nullable=False, default=True)
    roi_exemption_quarters_remaining = Column(Integer, nullable=True)
    
    # 交易詳情
    transaction_details = Column(JSON, nullable=True)
    vendor_supplier = Column(String(100), nullable=True)
    approval_reference = Column(String(100), nullable=True)
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # 關係
    innovation_project = relationship("InnovationProject", back_populates="budget_tracking")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_budget_tracking_date', 'transaction_date'),
        Index('idx_budget_tracking_type', 'transaction_type'),
        Index('idx_budget_tracking_category', 'expense_category'),
        CheckConstraint('amount != 0', name='check_non_zero_amount'),
        CheckConstraint('budget_utilization_rate BETWEEN 0 AND 150', name='check_valid_utilization_rate'),
        CheckConstraint('roi_exemption_quarters_remaining >= 0', name='check_non_negative_quarters'),
    )

class TechnicalMilestone(Base):
    """技術里程碑表"""
    __tablename__ = "technical_milestones"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innovation_project_id = Column(UUID(as_uuid=True), ForeignKey('innovation_projects.id'), nullable=False, index=True)
    
    # 里程碑基本信息
    milestone_name = Column(String(200), nullable=False)
    milestone_type = Column(String(30), nullable=False)
    milestone_description = Column(Text, nullable=False)
    
    # 里程碑時間線
    planned_date = Column(Date, nullable=False)
    actual_date = Column(Date, nullable=True)
    is_completed = Column(Boolean, nullable=False, default=False)
    completion_rate = Column(Numeric(5, 2), nullable=False, default=0)
    
    # 技術指標
    technical_metrics = Column(JSON, nullable=False)  # 技術指標目標和實際值
    success_criteria = Column(JSON, nullable=False)   # 成功標準
    deliverables = Column(JSON, nullable=True)        # 交付物清單
    
    # 依賴關係
    prerequisite_milestones = Column(JSON, nullable=True)  # 前置里程碑
    blocking_issues = Column(JSON, nullable=True)          # 阻塞問題
    
    # 里程碑狀態
    status = Column(String(30), nullable=False, default='not_started')  # not_started/in_progress/completed/delayed/cancelled
    priority_level = Column(String(20), nullable=False, default='medium')
    
    # 風險評估
    risk_level = Column(String(20), nullable=False, default='medium')  # low/medium/high/critical
    risk_factors = Column(JSON, nullable=True)
    mitigation_plans = Column(JSON, nullable=True)
    
    # 質量評估
    quality_score = Column(Numeric(5, 2), nullable=True)
    quality_criteria = Column(JSON, nullable=True)
    review_feedback = Column(Text, nullable=True)
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 關係
    innovation_project = relationship("InnovationProject", back_populates="milestones")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_milestone_date', 'planned_date', 'actual_date'),
        Index('idx_milestone_status', 'status'),
        Index('idx_milestone_type', 'milestone_type'),
        Index('idx_milestone_completion', 'is_completed'),
        CheckConstraint('completion_rate BETWEEN 0 AND 100', name='check_valid_completion_rate'),
        CheckConstraint('quality_score IS NULL OR quality_score BETWEEN 0 AND 100', name='check_valid_quality_score'),
    )

class UserBehaviorMetrics(Base):
    """用戶行為指標表"""
    __tablename__ = "user_behavior_metrics"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innovation_project_id = Column(UUID(as_uuid=True), ForeignKey('innovation_projects.id'), nullable=False, index=True)
    
    # 時間維度
    measurement_date = Column(Date, nullable=False, index=True)
    measurement_period = Column(String(20), nullable=False)  # daily/weekly/monthly
    
    # 用戶參與指標
    total_users = Column(Integer, nullable=False, default=0)
    new_users = Column(Integer, nullable=False, default=0)
    active_users = Column(Integer, nullable=False, default=0)
    returning_users = Column(Integer, nullable=False, default=0)
    churned_users = Column(Integer, nullable=False, default=0)
    
    # 使用行為指標
    total_sessions = Column(Integer, nullable=False, default=0)
    average_session_duration = Column(Numeric(8, 2), nullable=False, default=0)  # 分鐘
    feature_usage_frequency = Column(JSON, nullable=False)  # 各功能使用頻次
    user_journey_patterns = Column(JSON, nullable=True)     # 用戶旅程模式
    
    # 滿意度指標
    user_satisfaction_score = Column(Numeric(5, 2), nullable=True)  # 1-5 分
    net_promoter_score = Column(Numeric(5, 2), nullable=True)       # -100 到 100
    feature_adoption_rate = Column(Numeric(5, 2), nullable=False, default=0)  # 百分比
    
    # 轉化指標
    conversion_rate = Column(Numeric(5, 2), nullable=False, default=0)
    upgrade_conversion_rate = Column(Numeric(5, 2), nullable=False, default=0)
    retention_rate = Column(Numeric(5, 2), nullable=False, default=0)
    
    # 參與深度指標
    engagement_score = Column(Numeric(5, 2), nullable=False, default=0)
    feature_depth_usage = Column(JSON, nullable=True)      # 功能深度使用數據
    advanced_feature_adoption = Column(Numeric(5, 2), nullable=False, default=0)
    
    # 反饋數據
    user_feedback_sentiment = Column(String(20), nullable=True)  # positive/neutral/negative
    feedback_count = Column(Integer, nullable=False, default=0)
    improvement_suggestions = Column(JSON, nullable=True)
    
    # 行為分析
    user_segments = Column(JSON, nullable=True)  # 用戶細分
    behavior_anomalies = Column(JSON, nullable=True)  # 行為異常
    
    # 數據質量
    data_completeness_score = Column(Numeric(5, 2), nullable=False, default=100)
    data_sources = Column(JSON, nullable=False)
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    collected_by = Column(String(100), nullable=False)
    
    # 關係
    innovation_project = relationship("InnovationProject", back_populates="user_behavior_metrics")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_user_metrics_date', 'measurement_date'),
        Index('idx_user_metrics_period', 'measurement_period'),
        UniqueConstraint('innovation_project_id', 'measurement_date', 'measurement_period', name='uq_user_metrics_period'),
        CheckConstraint('total_users >= 0', name='check_non_negative_users'),
        CheckConstraint('conversion_rate BETWEEN 0 AND 100', name='check_valid_conversion_rate'),
        CheckConstraint('engagement_score BETWEEN 0 AND 100', name='check_valid_engagement_score'),
        CheckConstraint('user_satisfaction_score IS NULL OR user_satisfaction_score BETWEEN 1 AND 5', name='check_valid_satisfaction'),
        CheckConstraint('net_promoter_score IS NULL OR net_promoter_score BETWEEN -100 AND 100', name='check_valid_nps'),
    )

class AnomalyDetection(Base):
    """異常檢測表"""
    __tablename__ = "anomaly_detections"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    innovation_project_id = Column(UUID(as_uuid=True), ForeignKey('innovation_projects.id'), nullable=False, index=True)
    
    # 異常基本信息
    anomaly_type = Column(String(30), nullable=False, index=True)
    anomaly_severity = Column(String(20), nullable=False, default='medium')  # low/medium/high/critical
    anomaly_title = Column(String(200), nullable=False)
    anomaly_description = Column(Text, nullable=False)
    
    # 檢測信息
    detected_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    detection_method = Column(String(50), nullable=False)  # automated/manual/hybrid
    confidence_score = Column(Numeric(5, 2), nullable=False)  # 異常檢測信心度
    
    # 異常數據
    baseline_value = Column(Numeric(15, 6), nullable=True)
    actual_value = Column(Numeric(15, 6), nullable=False)
    deviation_percentage = Column(Numeric(8, 2), nullable=False)
    anomaly_threshold = Column(Numeric(15, 6), nullable=False)
    
    # 影響評估
    impact_level = Column(String(20), nullable=False)  # minimal/moderate/significant/severe
    affected_areas = Column(JSON, nullable=False)  # 受影響的領域
    potential_consequences = Column(JSON, nullable=True)
    
    # 異常狀態
    status = Column(String(30), nullable=False, default='detected')  # detected/investigating/resolved/false_positive
    resolution_priority = Column(String(20), nullable=False, default='medium')
    
    # 處理信息
    assigned_to = Column(String(100), nullable=True)
    investigation_notes = Column(Text, nullable=True)
    resolution_actions = Column(JSON, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    # 預防措施
    prevention_measures = Column(JSON, nullable=True)
    monitoring_adjustments = Column(JSON, nullable=True)
    
    # 關聯數據
    related_metrics = Column(JSON, nullable=True)  # 相關指標數據
    external_factors = Column(JSON, nullable=True)  # 外部因素
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 關係
    innovation_project = relationship("InnovationProject", back_populates="anomaly_detections")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_anomaly_detected_at', 'detected_at'),
        Index('idx_anomaly_severity', 'anomaly_severity'),
        Index('idx_anomaly_status', 'status'),
        Index('idx_anomaly_type_project', 'anomaly_type', 'innovation_project_id'),
        CheckConstraint('confidence_score BETWEEN 0 AND 100', name='check_valid_confidence'),
        CheckConstraint('deviation_percentage >= -100', name='check_valid_deviation'),
    )

# ==================== Pydantic 請求/響應模型 ====================

class InnovationZoneCreate(BaseModel):
    """創新特區創建請求"""
    zone_name: str = Field(..., min_length=1, max_length=100)
    zone_code: str = Field(..., min_length=1, max_length=20)
    description: Optional[str] = None
    innovation_focus: str = Field(..., max_length=50)
    target_innovation_types: List[InnovationType]
    total_budget_allocation: condecimal(max_digits=15, decimal_places=2, gt=0)
    budget_percentage_of_rd: condecimal(max_digits=5, decimal_places=2, ge=5, le=15)
    roi_exemption_quarters: int = Field(4, ge=1, le=8)
    zone_manager: str = Field(..., max_length=100)
    sponsor_department: str = Field(..., max_length=50)
    admission_criteria_weights: Dict[str, float]
    minimum_admission_score: condecimal(max_digits=5, decimal_places=2, ge=50, le=100) = 75.0
    
    @validator('admission_criteria_weights')
    def validate_weights(cls, v):
        if not v:
            raise ValueError('Admission criteria weights cannot be empty')
        
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError('Admission criteria weights must sum to 1.0')
        
        valid_criteria = [c.value for c in AdmissionCriteria]
        for criterion in v.keys():
            if criterion not in valid_criteria:
                raise ValueError(f'Invalid admission criterion: {criterion}')
        
        return v

class InnovationProjectCreate(BaseModel):
    """創新項目創建請求"""
    project_code: str = Field(..., max_length=50)
    innovation_zone_id: uuid.UUID
    project_name: str = Field(..., min_length=1, max_length=200)
    project_description: str = Field(..., min_length=1)
    innovation_type: InnovationType
    project_lead: str = Field(..., max_length=100)
    team_size: int = Field(..., gt=0)
    team_members: Optional[List[str]] = None
    start_date: date
    planned_end_date: Optional[date] = None
    priority_level: str = Field('medium', pattern='^(high|medium|low)$')
    strategic_importance: str = Field('medium', pattern='^(high|medium|low)$')
    project_tags: Optional[List[str]] = None
    project_configuration: Optional[Dict[str, Any]] = None
    created_by: str = Field(..., max_length=100)
    
    @validator('planned_end_date')
    def validate_end_date(cls, v, values):
        if v and 'start_date' in values and v <= values['start_date']:
            raise ValueError('Planned end date must be after start date')
        return v

class TechnicalMilestoneCreate(BaseModel):
    """技術里程碑創建請求"""
    innovation_project_id: uuid.UUID
    milestone_name: str = Field(..., min_length=1, max_length=200)
    milestone_type: MilestoneType
    milestone_description: str = Field(..., min_length=1)
    planned_date: date
    technical_metrics: Dict[str, Any]
    success_criteria: Dict[str, Any]
    deliverables: Optional[List[str]] = None
    prerequisite_milestones: Optional[List[uuid.UUID]] = None
    priority_level: str = Field('medium', pattern='^(high|medium|low)$')
    risk_level: str = Field('medium', pattern='^(low|medium|high|critical)$')
    risk_factors: Optional[List[str]] = None
    mitigation_plans: Optional[List[str]] = None
    created_by: str = Field(..., max_length=100)

class UserBehaviorMetricsCreate(BaseModel):
    """用戶行為指標創建請求"""
    innovation_project_id: uuid.UUID
    measurement_date: date
    measurement_period: str = Field(..., pattern='^(daily|weekly|monthly)$')
    total_users: int = Field(0, ge=0)
    new_users: int = Field(0, ge=0)
    active_users: int = Field(0, ge=0)
    returning_users: int = Field(0, ge=0)
    churned_users: int = Field(0, ge=0)
    total_sessions: int = Field(0, ge=0)
    average_session_duration: condecimal(max_digits=8, decimal_places=2, ge=0) = 0
    feature_usage_frequency: Dict[str, int]
    user_journey_patterns: Optional[Dict[str, Any]] = None
    user_satisfaction_score: Optional[condecimal(max_digits=5, decimal_places=2, ge=1, le=5)] = None
    net_promoter_score: Optional[condecimal(max_digits=5, decimal_places=2, ge=-100, le=100)] = None
    feature_adoption_rate: condecimal(max_digits=5, decimal_places=2, ge=0, le=100) = 0
    conversion_rate: condecimal(max_digits=5, decimal_places=2, ge=0, le=100) = 0
    upgrade_conversion_rate: condecimal(max_digits=5, decimal_places=2, ge=0, le=100) = 0
    retention_rate: condecimal(max_digits=5, decimal_places=2, ge=0, le=100) = 0
    engagement_score: condecimal(max_digits=5, decimal_places=2, ge=0, le=100) = 0
    collected_by: str = Field(..., max_length=100)

class AnomalyDetectionCreate(BaseModel):
    """異常檢測創建請求"""
    innovation_project_id: uuid.UUID
    anomaly_type: AnomalyType
    anomaly_severity: str = Field('medium', pattern='^(low|medium|high|critical)$')
    anomaly_title: str = Field(..., min_length=1, max_length=200)
    anomaly_description: str = Field(..., min_length=1)
    detection_method: str = Field(..., max_length=50)
    confidence_score: condecimal(max_digits=5, decimal_places=2, ge=0, le=100)
    baseline_value: Optional[condecimal(max_digits=15, decimal_places=6)] = None
    actual_value: condecimal(max_digits=15, decimal_places=6)
    deviation_percentage: condecimal(max_digits=8, decimal_places=2, ge=-100)
    anomaly_threshold: condecimal(max_digits=15, decimal_places=6)
    impact_level: str = Field(..., pattern='^(minimal|moderate|significant|severe)$')
    affected_areas: List[str]
    potential_consequences: Optional[List[str]] = None
    resolution_priority: str = Field('medium', pattern='^(low|medium|high|critical)$')
    related_metrics: Optional[Dict[str, Any]] = None
    external_factors: Optional[Dict[str, Any]] = None

class InnovationZoneResponse(BaseModel):
    """創新特區響應"""
    id: uuid.UUID
    zone_name: str
    zone_code: str
    description: Optional[str]
    innovation_focus: str
    target_innovation_types: List[str]
    total_budget_allocation: Decimal
    budget_percentage_of_rd: Decimal
    roi_exemption_quarters: int
    zone_manager: str
    sponsor_department: str
    admission_criteria_weights: Dict[str, float]
    minimum_admission_score: Decimal
    is_active: bool
    established_date: date
    created_at: datetime
    updated_at: datetime
    
    # 統計數據
    active_projects_count: Optional[int] = None
    total_budget_allocated: Optional[Decimal] = None
    total_budget_spent: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

class InnovationProjectResponse(BaseModel):
    """創新項目響應"""
    id: uuid.UUID
    project_code: str
    innovation_zone_id: uuid.UUID
    project_name: str
    project_description: str
    innovation_type: str
    current_stage: str
    project_lead: str
    team_size: int
    team_members: Optional[List[str]]
    start_date: date
    planned_end_date: Optional[date]
    actual_end_date: Optional[date]
    roi_exemption_status: str
    roi_exemption_start_date: date
    roi_exemption_end_date: Optional[date]
    admission_score: Decimal
    admission_criteria_scores: Dict[str, float]
    is_active: bool
    priority_level: str
    strategic_importance: str
    project_tags: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # 項目統計
    milestones_count: Optional[int] = None
    completed_milestones_count: Optional[int] = None
    budget_utilization_rate: Optional[Decimal] = None
    
    class Config:
        from_attributes = True

class InnovationAnalyticsRequest(BaseModel):
    """創新分析請求"""
    innovation_zone_ids: Optional[List[uuid.UUID]] = None
    project_ids: Optional[List[uuid.UUID]] = None
    start_date: date
    end_date: date
    include_budget_analysis: bool = True
    include_milestone_analysis: bool = True
    include_user_behavior_analysis: bool = True
    include_anomaly_analysis: bool = True
    analysis_granularity: str = Field('monthly', pattern='^(daily|weekly|monthly|quarterly)$')

class InnovationAnalyticsResponse(BaseModel):
    """創新分析響應"""
    analysis_id: uuid.UUID
    analysis_date: datetime
    analysis_period: str
    
    # 總體統計
    total_zones: int
    total_projects: int
    active_projects: int
    total_budget_allocated: Decimal
    total_budget_spent: Decimal
    
    # 預算分析
    budget_utilization_rate: Decimal
    projects_over_budget: int
    average_roi_exemption_usage: Decimal
    
    # 里程碑分析
    total_milestones: int
    completed_milestones: int
    delayed_milestones: int
    milestone_completion_rate: Decimal
    
    # 用戶行為分析
    total_users_engaged: int
    average_user_satisfaction: Optional[Decimal]
    average_feature_adoption_rate: Decimal
    
    # 異常分析
    total_anomalies_detected: int
    critical_anomalies: int
    resolved_anomalies: int
    
    # 趨勢分析
    innovation_trends: Dict[str, Any]
    recommendations: List[str]