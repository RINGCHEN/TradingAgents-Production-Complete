#!/usr/bin/env python3
"""
Revenue Attribution Database Models for GPT-OSS Integration
GPT-OSS收益歸因數據模型 - 任務2.1.3

企業級收益歸因系統，用於追蹤GPT-OSS本地推理帶來的增量收益：
- API成本節省追蹤（相對於雲端API的成本節省）
- 新功能收益追蹤（由於GPT-OSS能力產生的新功能收益）
- 會員升級歸因（GPT-OSS功能如何促進會員升級）
- 收益預測建模（基於歷史數據的收益預測）
"""

import uuid
from datetime import datetime, timezone, date
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

from .database import Base

# ==================== 核心枚舉類型 ====================

class RevenueType(str, Enum):
    """收益類型枚舉"""
    API_COST_SAVINGS = "api_cost_savings"           # API成本節省
    NEW_FEATURE_REVENUE = "new_feature_revenue"     # 新功能收益
    MEMBERSHIP_UPGRADE = "membership_upgrade"        # 會員升級收益
    ENHANCED_PERFORMANCE = "enhanced_performance"    # 性能提升帶來的收益
    USER_RETENTION = "user_retention"               # 用戶留存提升收益
    OPERATIONAL_EFFICIENCY = "operational_efficiency" # 運營效率提升收益
    PREMIUM_FEATURES = "premium_features"           # 高級功能收益
    USAGE_INCREASE = "usage_increase"               # 使用量增加收益
    COST_AVOIDANCE = "cost_avoidance"              # 成本避免
    OTHER = "other"                                 # 其他收益

class AttributionMethod(str, Enum):
    """歸因方法枚舉"""
    DIRECT_ATTRIBUTION = "direct_attribution"       # 直接歸因
    STATISTICAL_ANALYSIS = "statistical_analysis"   # 統計分析歸因
    AB_TESTING = "ab_testing"                       # A/B測試歸因
    COHORT_ANALYSIS = "cohort_analysis"             # 群組分析歸因
    REGRESSION_ANALYSIS = "regression_analysis"     # 回歸分析歸因
    MACHINE_LEARNING = "machine_learning"           # 機器學習歸因
    EXPERT_JUDGMENT = "expert_judgment"             # 專家判斷歸因
    HYBRID_MODEL = "hybrid_model"                   # 混合模型歸因

class RevenueConfidence(str, Enum):
    """收益信心度等級"""
    VERY_HIGH = "very_high"     # 非常高 (>95%)
    HIGH = "high"               # 高 (85-95%)
    MEDIUM = "medium"           # 中等 (70-85%)
    LOW = "low"                 # 低 (50-70%)
    VERY_LOW = "very_low"       # 很低 (<50%)

class CustomerSegment(str, Enum):
    """客戶群體枚舉"""
    FREE = "free"               # 免費用戶
    BASIC = "basic"             # 基礎會員
    PREMIUM = "premium"         # 高級會員
    ENTERPRISE = "enterprise"   # 企業用戶
    VIP = "vip"                # VIP用戶
    TRIAL = "trial"            # 試用用戶

class FeatureCategory(str, Enum):
    """功能類別枚舉"""
    AI_ANALYSIS = "ai_analysis"         # AI分析功能
    REAL_TIME_DATA = "real_time_data"   # 實時數據功能
    ADVANCED_CHARTS = "advanced_charts" # 高級圖表功能
    PORTFOLIO_MGMT = "portfolio_mgmt"   # 投資組合管理
    RISK_ASSESSMENT = "risk_assessment" # 風險評估功能
    TRADING_SIGNALS = "trading_signals" # 交易信號功能
    PERSONALIZATION = "personalization" # 個性化功能
    API_ACCESS = "api_access"           # API訪問功能

# ==================== 核心數據模型 ====================

class GPTOSSRevenueAttribution(Base):
    """GPT-OSS收益歸因主表"""
    __tablename__ = "gpt_oss_revenue_attribution"
    
    # 主鍵和基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribution_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # 時間維度
    record_date = Column(Date, nullable=False, index=True)
    attribution_period_start = Column(Date, nullable=False, index=True)
    attribution_period_end = Column(Date, nullable=False, index=True)
    period_year = Column(Integer, nullable=False, index=True)
    period_quarter = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    
    # 收益分類
    revenue_type = Column(String(30), nullable=False, index=True)
    revenue_category = Column(String(50), nullable=True)
    feature_category = Column(String(30), nullable=True, index=True)
    
    # 收益金額
    total_revenue_amount = Column(Numeric(15, 2), nullable=False)
    gpt_oss_attributed_amount = Column(Numeric(15, 2), nullable=False)
    baseline_amount = Column(Numeric(15, 2), nullable=True)
    incremental_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 歸因信息
    attribution_method = Column(String(30), nullable=False)
    attribution_confidence = Column(String(20), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)  # 0.00-1.00
    gpt_oss_contribution_ratio = Column(Numeric(3, 2), nullable=False)  # 0.00-1.00
    
    # 客戶和產品信息
    customer_segment = Column(String(20), nullable=True, index=True)
    customer_count = Column(Integer, nullable=True)
    affected_users = Column(Integer, nullable=True)
    new_customers = Column(Integer, nullable=True)
    upgraded_customers = Column(Integer, nullable=True)
    
    # GPT-OSS具體貢獻
    gpt_oss_model_used = Column(String(50), nullable=True)
    gpt_oss_feature_used = Column(String(100), nullable=True)
    inference_count = Column(Integer, nullable=True)
    tokens_processed = Column(Integer, nullable=True)
    response_quality_score = Column(Numeric(3, 2), nullable=True)
    
    # 比較和基準
    baseline_period_start = Column(Date, nullable=True)
    baseline_period_end = Column(Date, nullable=True)
    comparison_metric = Column(String(50), nullable=True)
    improvement_percentage = Column(Numeric(5, 2), nullable=True)
    
    # 詳細信息
    description = Column(String(500), nullable=False)
    attribution_details = Column(JSON, nullable=True)
    revenue_breakdown = Column(JSON, nullable=True)
    supporting_metrics = Column(JSON, nullable=True)
    
    # 驗證和審計
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_method = Column(String(50), nullable=True)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verification_notes = Column(Text, nullable=True)
    
    # 來源追蹤
    data_source = Column(String(50), nullable=False)
    source_reference = Column(String(100), nullable=True)
    calculation_method = Column(String(100), nullable=True)
    
    # 狀態和元數據
    status = Column(String(20), nullable=False, default='active')  # active/inactive/disputed
    quality_flags = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    updated_by = Column(String(100), nullable=True)
    
    # 約束和索引
    __table_args__ = (
        Index('idx_gpt_oss_revenue_period', 'period_year', 'period_quarter', 'period_month'),
        Index('idx_gpt_oss_revenue_type', 'revenue_type', 'revenue_category'),
        Index('idx_gpt_oss_revenue_date', 'record_date', 'revenue_type'),
        Index('idx_gpt_oss_revenue_customer', 'customer_segment', 'feature_category'),
        Index('idx_gpt_oss_revenue_confidence', 'attribution_confidence', 'confidence_score'),
        CheckConstraint('total_revenue_amount >= 0', name='check_positive_total_revenue'),
        CheckConstraint('gpt_oss_attributed_amount >= 0', name='check_positive_attributed_revenue'),
        CheckConstraint('confidence_score BETWEEN 0 AND 1', name='check_valid_confidence'),
        CheckConstraint('gpt_oss_contribution_ratio BETWEEN 0 AND 1', name='check_valid_contribution'),
        CheckConstraint('period_quarter BETWEEN 1 AND 4', name='check_valid_quarter_rev_attr'),
        CheckConstraint('period_month BETWEEN 1 AND 12', name='check_valid_month_rev_attr'),
        CheckConstraint('attribution_period_start <= attribution_period_end', name='check_valid_period'),
    )

class APICostSavings(Base):
    """API成本節省追蹤表"""
    __tablename__ = "api_cost_savings"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribution_id = Column(UUID(as_uuid=True), ForeignKey('gpt_oss_revenue_attribution.id'), nullable=False, index=True)
    
    # 時間信息
    calculation_date = Column(Date, nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # GPT-OSS本地推理成本
    local_inference_requests = Column(Integer, nullable=False)
    local_inference_tokens = Column(Integer, nullable=False)
    local_compute_cost = Column(Numeric(12, 4), nullable=False)
    local_power_cost = Column(Numeric(12, 4), nullable=False)
    local_infrastructure_cost = Column(Numeric(12, 4), nullable=False)
    local_total_cost = Column(Numeric(12, 2), nullable=False)
    
    # 等效雲端API成本
    equivalent_cloud_requests = Column(Integer, nullable=False)
    equivalent_cloud_tokens = Column(Integer, nullable=False)
    cloud_api_rate_per_token = Column(Numeric(8, 6), nullable=False)
    cloud_api_base_cost = Column(Numeric(12, 4), nullable=False)
    cloud_api_premium_cost = Column(Numeric(12, 4), nullable=True, default=0)
    cloud_api_total_cost = Column(Numeric(12, 2), nullable=False)
    
    # 成本節省計算
    gross_savings = Column(Numeric(12, 2), nullable=False)
    net_savings = Column(Numeric(12, 2), nullable=False)  # 扣除本地成本後
    savings_percentage = Column(Numeric(5, 2), nullable=False)
    savings_per_request = Column(Numeric(8, 4), nullable=False)
    savings_per_token = Column(Numeric(8, 6), nullable=False)
    
    # 質量和性能比較
    local_avg_response_time = Column(Numeric(6, 2), nullable=True)  # 毫秒
    cloud_avg_response_time = Column(Numeric(6, 2), nullable=True)  # 毫秒
    local_availability_rate = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    cloud_availability_rate = Column(Numeric(3, 2), nullable=True)  # 0.00-1.00
    quality_score_difference = Column(Numeric(3, 2), nullable=True)  # -1.00 to 1.00
    
    # 使用模式分析
    peak_usage_savings = Column(Numeric(12, 2), nullable=True)
    off_peak_usage_savings = Column(Numeric(12, 2), nullable=True)
    burst_capacity_savings = Column(Numeric(12, 2), nullable=True)
    
    # 細分統計
    by_model_breakdown = Column(JSON, nullable=True)  # 按模型分解的節省
    by_user_type_breakdown = Column(JSON, nullable=True)  # 按用戶類型分解
    by_feature_breakdown = Column(JSON, nullable=True)  # 按功能分解
    
    # 預測和趨勢
    projected_monthly_savings = Column(Numeric(12, 2), nullable=True)
    projected_annual_savings = Column(Numeric(12, 2), nullable=True)
    trend_indicator = Column(String(20), nullable=True)  # increasing/decreasing/stable
    
    # 驗證信息
    calculation_method = Column(String(100), nullable=False)
    data_completeness_score = Column(Numeric(3, 2), nullable=False, default=1.0)
    validation_status = Column(String(20), nullable=False, default='pending')
    
    # 元數據
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    
    # 關係
    revenue_attribution = relationship("GPTOSSRevenueAttribution")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_api_savings_date', 'calculation_date'),
        Index('idx_api_savings_period', 'period_start', 'period_end'),
        CheckConstraint('local_inference_requests > 0', name='check_positive_local_requests'),
        CheckConstraint('equivalent_cloud_requests > 0', name='check_positive_cloud_requests'),
        CheckConstraint('local_total_cost >= 0', name='check_non_negative_local_cost'),
        CheckConstraint('cloud_api_total_cost >= 0', name='check_non_negative_cloud_cost'),
        CheckConstraint('period_start <= period_end', name='check_valid_savings_period'),
    )

class NewFeatureRevenue(Base):
    """新功能收益追蹤表"""
    __tablename__ = "new_feature_revenue"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribution_id = Column(UUID(as_uuid=True), ForeignKey('gpt_oss_revenue_attribution.id'), nullable=False, index=True)
    
    # 功能信息
    feature_name = Column(String(100), nullable=False, index=True)
    feature_id = Column(String(50), nullable=False, index=True)
    feature_category = Column(String(30), nullable=False, index=True)
    feature_launch_date = Column(Date, nullable=False)
    
    # GPT-OSS依賴性
    gpt_oss_dependency_level = Column(String(20), nullable=False)  # critical/high/medium/low
    gpt_oss_models_used = Column(JSON, nullable=False)
    gpt_oss_capabilities_used = Column(JSON, nullable=False)
    feature_uniqueness_score = Column(Numeric(3, 2), nullable=False)  # GPT-OSS獨有性分數
    
    # 收益追蹤
    direct_subscription_revenue = Column(Numeric(12, 2), nullable=False, default=0)
    usage_based_revenue = Column(Numeric(12, 2), nullable=False, default=0)
    upselling_revenue = Column(Numeric(12, 2), nullable=False, default=0)
    cross_selling_revenue = Column(Numeric(12, 2), nullable=False, default=0)
    retention_revenue = Column(Numeric(12, 2), nullable=False, default=0)
    total_feature_revenue = Column(Numeric(12, 2), nullable=False)
    
    # 用戶採用指標
    total_feature_users = Column(Integer, nullable=False)
    new_users_from_feature = Column(Integer, nullable=False, default=0)
    upgraded_users_from_feature = Column(Integer, nullable=False, default=0)
    feature_adoption_rate = Column(Numeric(3, 2), nullable=False)
    feature_retention_rate = Column(Numeric(3, 2), nullable=True)
    
    # 使用統計
    total_feature_usage_count = Column(Integer, nullable=False)
    avg_usage_per_user = Column(Numeric(8, 2), nullable=False)
    peak_daily_usage = Column(Integer, nullable=True)
    feature_engagement_score = Column(Numeric(3, 2), nullable=True)
    
    # 收益歸因計算
    baseline_revenue_without_gpt_oss = Column(Numeric(12, 2), nullable=True)
    gpt_oss_incremental_revenue = Column(Numeric(12, 2), nullable=False)
    attribution_confidence_level = Column(String(20), nullable=False)
    attribution_methodology = Column(Text, nullable=False)
    
    # 競爭分析
    competitor_equivalent_exists = Column(Boolean, nullable=False, default=False)
    competitive_advantage_score = Column(Numeric(3, 2), nullable=True)
    market_differentiation_value = Column(Numeric(12, 2), nullable=True)
    
    # 成本信息
    feature_development_cost = Column(Numeric(12, 2), nullable=True)
    feature_maintenance_cost = Column(Numeric(12, 2), nullable=True)
    gpt_oss_infrastructure_cost = Column(Numeric(12, 2), nullable=True)
    feature_roi = Column(Numeric(5, 2), nullable=True)
    
    # 預測指標
    projected_revenue_next_quarter = Column(Numeric(12, 2), nullable=True)
    projected_revenue_next_year = Column(Numeric(12, 2), nullable=True)
    feature_lifecycle_stage = Column(String(20), nullable=False)  # launch/growth/maturity/decline
    
    # 質量和滿意度
    user_satisfaction_score = Column(Numeric(3, 2), nullable=True)
    feature_quality_rating = Column(Numeric(3, 2), nullable=True)
    support_ticket_count = Column(Integer, nullable=True, default=0)
    
    # 細分分析
    revenue_by_customer_segment = Column(JSON, nullable=True)
    usage_by_region = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    
    # 時間信息
    measurement_period_start = Column(Date, nullable=False)
    measurement_period_end = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 關係
    revenue_attribution = relationship("GPTOSSRevenueAttribution")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_feature_revenue_name', 'feature_name'),
        Index('idx_feature_revenue_category', 'feature_category'),
        Index('idx_feature_revenue_launch', 'feature_launch_date'),
        Index('idx_feature_revenue_period', 'measurement_period_start', 'measurement_period_end'),
        CheckConstraint('total_feature_revenue >= 0', name='check_non_negative_feature_revenue'),
        CheckConstraint('total_feature_users >= 0', name='check_non_negative_users'),
        CheckConstraint('feature_adoption_rate BETWEEN 0 AND 1', name='check_valid_adoption_rate'),
        CheckConstraint('feature_uniqueness_score BETWEEN 0 AND 1', name='check_valid_uniqueness'),
        CheckConstraint('measurement_period_start <= measurement_period_end', name='check_valid_measurement_period'),
    )

class MembershipUpgradeAttribution(Base):
    """會員升級歸因表"""
    __tablename__ = "membership_upgrade_attribution"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attribution_id = Column(UUID(as_uuid=True), ForeignKey('gpt_oss_revenue_attribution.id'), nullable=False, index=True)
    
    # 升級事件信息
    upgrade_event_date = Column(Date, nullable=False, index=True)
    customer_id = Column(String(50), nullable=False, index=True)
    previous_tier = Column(String(20), nullable=False)
    new_tier = Column(String(20), nullable=False, index=True)
    upgrade_revenue = Column(Numeric(10, 2), nullable=False)
    
    # GPT-OSS歸因分析
    gpt_oss_triggered_upgrade = Column(Boolean, nullable=False)
    primary_gpt_oss_feature = Column(String(100), nullable=True)
    secondary_gpt_oss_features = Column(JSON, nullable=True)
    gpt_oss_usage_before_upgrade = Column(Integer, nullable=True)
    gpt_oss_satisfaction_score = Column(Numeric(3, 2), nullable=True)
    
    # 升級觸發因素分析
    trigger_event_type = Column(String(50), nullable=False)  # feature_trial/usage_limit/ai_recommendation等
    trigger_event_date = Column(Date, nullable=True)
    days_from_trigger_to_upgrade = Column(Integer, nullable=True)
    touchpoints_before_upgrade = Column(JSON, nullable=True)
    
    # 用戶行為分析
    pre_upgrade_session_count = Column(Integer, nullable=True)
    pre_upgrade_feature_usage = Column(JSON, nullable=True)
    pre_upgrade_engagement_score = Column(Numeric(3, 2), nullable=True)
    user_journey_stage = Column(String(30), nullable=True)
    
    # 歸因信心和方法
    attribution_confidence = Column(String(20), nullable=False)
    attribution_score = Column(Numeric(3, 2), nullable=False)  # 0.00-1.00
    attribution_method_used = Column(String(50), nullable=False)
    counter_factual_analysis = Column(JSON, nullable=True)  # 反事實分析
    
    # 競爭和替代分析
    considered_alternatives = Column(JSON, nullable=True)
    competitive_features_comparison = Column(JSON, nullable=True)
    unique_value_proposition = Column(Text, nullable=True)
    price_sensitivity_score = Column(Numeric(3, 2), nullable=True)
    
    # 收益持續性
    subscription_length_months = Column(Integer, nullable=True)
    retention_probability = Column(Numeric(3, 2), nullable=True)
    lifetime_value_increase = Column(Numeric(10, 2), nullable=True)
    upselling_potential_score = Column(Numeric(3, 2), nullable=True)
    
    # 群組和分段分析
    customer_segment = Column(String(20), nullable=False, index=True)
    geographic_region = Column(String(50), nullable=True)
    acquisition_channel = Column(String(50), nullable=True)
    customer_age_days = Column(Integer, nullable=True)
    previous_upgrade_count = Column(Integer, nullable=True, default=0)
    
    # 實驗和測試信息
    ab_test_group = Column(String(20), nullable=True)
    control_group_comparison = Column(JSON, nullable=True)
    statistical_significance = Column(Numeric(3, 2), nullable=True)
    
    # 預測和建模
    upgrade_propensity_score = Column(Numeric(3, 2), nullable=True)
    churn_risk_score = Column(Numeric(3, 2), nullable=True)
    next_upgrade_probability = Column(Numeric(3, 2), nullable=True)
    predicted_next_upgrade_date = Column(Date, nullable=True)
    
    # 驗證和質量
    manual_verification_status = Column(String(20), nullable=False, default='pending')
    verification_notes = Column(Text, nullable=True)
    data_quality_score = Column(Numeric(3, 2), nullable=False, default=1.0)
    
    # 元數據
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    
    # 關係
    revenue_attribution = relationship("GPTOSSRevenueAttribution")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_upgrade_attr_date', 'upgrade_event_date'),
        Index('idx_upgrade_attr_customer', 'customer_id'),
        Index('idx_upgrade_attr_tier', 'previous_tier', 'new_tier'),
        Index('idx_upgrade_attr_trigger', 'trigger_event_type'),
        CheckConstraint('upgrade_revenue > 0', name='check_positive_upgrade_revenue'),
        CheckConstraint('attribution_score BETWEEN 0 AND 1', name='check_valid_attribution_score'),
        CheckConstraint('days_from_trigger_to_upgrade >= 0', name='check_non_negative_days'),
    )

class RevenueForecast(Base):
    """收益預測表"""
    __tablename__ = "revenue_forecast"
    
    # 主鍵和基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    forecast_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # 預測時間信息
    forecast_created_date = Column(Date, nullable=False, index=True)
    forecast_period_start = Column(Date, nullable=False, index=True)
    forecast_period_end = Column(Date, nullable=False, index=True)
    forecast_horizon_days = Column(Integer, nullable=False)
    forecast_granularity = Column(String(20), nullable=False)  # daily/weekly/monthly/quarterly
    
    # 預測範圍
    revenue_type = Column(String(30), nullable=False, index=True)
    customer_segment = Column(String(20), nullable=True, index=True)
    feature_category = Column(String(30), nullable=True)
    geographic_region = Column(String(50), nullable=True)
    
    # 預測結果
    forecasted_revenue = Column(Numeric(15, 2), nullable=False)
    lower_bound_90pct = Column(Numeric(15, 2), nullable=False)
    upper_bound_90pct = Column(Numeric(15, 2), nullable=False)
    lower_bound_95pct = Column(Numeric(15, 2), nullable=False)
    upper_bound_95pct = Column(Numeric(15, 2), nullable=False)
    confidence_interval_width = Column(Numeric(15, 2), nullable=False)
    
    # 模型信息
    forecasting_model = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=False)
    training_data_start = Column(Date, nullable=False)
    training_data_end = Column(Date, nullable=False)
    training_sample_size = Column(Integer, nullable=False)
    
    # 模型性能指標
    model_accuracy_score = Column(Numeric(3, 2), nullable=True)
    mean_absolute_error = Column(Numeric(12, 2), nullable=True)
    mean_squared_error = Column(Numeric(12, 2), nullable=True)
    r_squared = Column(Numeric(3, 2), nullable=True)
    cross_validation_score = Column(Numeric(3, 2), nullable=True)
    
    # 特徵重要性
    top_predictive_features = Column(JSON, nullable=True)
    gpt_oss_feature_importance = Column(Numeric(3, 2), nullable=True)
    seasonal_factors = Column(JSON, nullable=True)
    trend_components = Column(JSON, nullable=True)
    
    # 假設和條件
    forecast_assumptions = Column(JSON, nullable=False)
    external_factors = Column(JSON, nullable=True)
    scenario_type = Column(String(20), nullable=False, default='base')  # optimistic/base/pessimistic
    sensitivity_analysis = Column(JSON, nullable=True)
    
    # 更新和追蹤
    actual_revenue_to_date = Column(Numeric(15, 2), nullable=True)
    forecast_accuracy_to_date = Column(Numeric(3, 2), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    update_frequency = Column(String(20), nullable=False, default='weekly')
    next_update_date = Column(Date, nullable=True)
    
    # 業務影響
    business_impact_score = Column(Numeric(3, 2), nullable=True)
    strategic_importance = Column(String(20), nullable=False, default='medium')
    risk_factors = Column(JSON, nullable=True)
    mitigation_strategies = Column(JSON, nullable=True)
    
    # 細分預測
    monthly_breakdown = Column(JSON, nullable=True)
    customer_tier_breakdown = Column(JSON, nullable=True)
    feature_contribution_breakdown = Column(JSON, nullable=True)
    
    # 驗證和質量
    forecast_status = Column(String(20), nullable=False, default='active')
    validation_status = Column(String(20), nullable=False, default='pending')
    peer_review_status = Column(String(20), nullable=True)
    
    # 元數據
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    model_trained_by = Column(String(100), nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # 約束和索引
    __table_args__ = (
        Index('idx_forecast_period', 'forecast_period_start', 'forecast_period_end'),
        Index('idx_forecast_type', 'revenue_type', 'customer_segment'),
        Index('idx_forecast_created', 'forecast_created_date'),
        Index('idx_forecast_model', 'forecasting_model', 'model_version'),
        CheckConstraint('forecasted_revenue >= 0', name='check_non_negative_forecast'),
        CheckConstraint('forecast_horizon_days > 0', name='check_positive_horizon'),
        CheckConstraint('lower_bound_90pct <= forecasted_revenue', name='check_lower_bound_90'),
        CheckConstraint('forecasted_revenue <= upper_bound_90pct', name='check_upper_bound_90'),
        CheckConstraint('lower_bound_95pct <= lower_bound_90pct', name='check_lower_bound_consistency'),
        CheckConstraint('upper_bound_90pct <= upper_bound_95pct', name='check_upper_bound_consistency'),
        CheckConstraint('forecast_period_start <= forecast_period_end', name='check_valid_forecast_period'),
        CheckConstraint('training_data_start <= training_data_end', name='check_valid_training_period'),
    )

# ==================== Pydantic 請求/響應模型 ====================

class GPTOSSRevenueAttributionCreate(BaseModel):
    """GPT-OSS收益歸因創建請求"""
    attribution_id: str = Field(..., min_length=1, max_length=50)
    record_date: date
    attribution_period_start: date
    attribution_period_end: date
    revenue_type: RevenueType
    total_revenue_amount: condecimal(max_digits=15, decimal_places=2, ge=0)
    gpt_oss_attributed_amount: condecimal(max_digits=15, decimal_places=2, ge=0)
    incremental_amount: condecimal(max_digits=15, decimal_places=2, ge=0)
    attribution_method: AttributionMethod
    attribution_confidence: RevenueConfidence
    confidence_score: condecimal(max_digits=3, decimal_places=2, ge=0, le=1)
    gpt_oss_contribution_ratio: condecimal(max_digits=3, decimal_places=2, ge=0, le=1)
    description: str = Field(..., min_length=1, max_length=500)
    
    # 可選字段
    revenue_category: Optional[str] = Field(None, max_length=50)
    feature_category: Optional[FeatureCategory] = None
    baseline_amount: Optional[condecimal(max_digits=15, decimal_places=2)] = None
    currency: str = "USD"
    customer_segment: Optional[CustomerSegment] = None
    customer_count: Optional[int] = Field(None, ge=0)
    affected_users: Optional[int] = Field(None, ge=0)
    new_customers: Optional[int] = Field(None, ge=0)
    upgraded_customers: Optional[int] = Field(None, ge=0)
    
    # GPT-OSS詳細信息
    gpt_oss_model_used: Optional[str] = Field(None, max_length=50)
    gpt_oss_feature_used: Optional[str] = Field(None, max_length=100)
    inference_count: Optional[int] = Field(None, ge=0)
    tokens_processed: Optional[int] = Field(None, ge=0)
    response_quality_score: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = None
    
    # 比較信息
    baseline_period_start: Optional[date] = None
    baseline_period_end: Optional[date] = None
    comparison_metric: Optional[str] = Field(None, max_length=50)
    improvement_percentage: Optional[condecimal(max_digits=5, decimal_places=2)] = None
    
    # 詳細數據
    attribution_details: Optional[Dict[str, Any]] = None
    revenue_breakdown: Optional[Dict[str, Any]] = None
    supporting_metrics: Optional[Dict[str, Any]] = None
    
    # 來源信息
    data_source: str = Field(..., max_length=50)
    source_reference: Optional[str] = Field(None, max_length=100)
    calculation_method: Optional[str] = Field(None, max_length=100)
    
    @validator('attribution_period_end')
    def validate_period(cls, v, values):
        start = values.get('attribution_period_start')
        if start and v < start:
            raise ValueError('Attribution period end must be after start')
        return v
    
    @validator('baseline_period_end')
    def validate_baseline_period(cls, v, values):
        start = values.get('baseline_period_start')
        if start and v and v < start:
            raise ValueError('Baseline period end must be after start')
        return v

class APICostSavingsCreate(BaseModel):
    """API成本節省創建請求"""
    attribution_id: uuid.UUID
    calculation_date: date
    period_start: date
    period_end: date
    
    # 本地推理數據
    local_inference_requests: int = Field(..., gt=0)
    local_inference_tokens: int = Field(..., gt=0)
    local_compute_cost: condecimal(max_digits=12, decimal_places=4, ge=0)
    local_power_cost: condecimal(max_digits=12, decimal_places=4, ge=0)
    local_infrastructure_cost: condecimal(max_digits=12, decimal_places=4, ge=0)
    
    # 雲端API等效數據
    equivalent_cloud_requests: int = Field(..., gt=0)
    equivalent_cloud_tokens: int = Field(..., gt=0)
    cloud_api_rate_per_token: condecimal(max_digits=8, decimal_places=6, gt=0)
    cloud_api_base_cost: condecimal(max_digits=12, decimal_places=4, ge=0)
    cloud_api_premium_cost: Optional[condecimal(max_digits=12, decimal_places=4, ge=0)] = 0
    
    # 可選性能數據
    local_avg_response_time: Optional[condecimal(max_digits=6, decimal_places=2, gt=0)] = None
    cloud_avg_response_time: Optional[condecimal(max_digits=6, decimal_places=2, gt=0)] = None
    local_availability_rate: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = None
    cloud_availability_rate: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = None
    quality_score_difference: Optional[condecimal(max_digits=3, decimal_places=2, ge=-1, le=1)] = None
    
    # 詳細分解數據
    by_model_breakdown: Optional[Dict[str, Any]] = None
    by_user_type_breakdown: Optional[Dict[str, Any]] = None
    by_feature_breakdown: Optional[Dict[str, Any]] = None
    
    # 計算方法
    calculation_method: str = Field(..., max_length=100)
    data_completeness_score: condecimal(max_digits=3, decimal_places=2, ge=0, le=1) = 1.0
    
    @validator('period_end')
    def validate_period(cls, v, values):
        start = values.get('period_start')
        if start and v < start:
            raise ValueError('Period end must be after start')
        return v

class RevenueAttributionResponse(BaseModel):
    """收益歸因響應模型"""
    id: uuid.UUID
    attribution_id: str
    record_date: date
    attribution_period_start: date
    attribution_period_end: date
    revenue_type: str
    total_revenue_amount: Decimal
    gpt_oss_attributed_amount: Decimal
    incremental_amount: Decimal
    attribution_confidence: str
    confidence_score: Decimal
    gpt_oss_contribution_ratio: Decimal
    description: str
    
    # 可選響應字段
    revenue_category: Optional[str]
    feature_category: Optional[str]
    customer_segment: Optional[str]
    customer_count: Optional[int]
    affected_users: Optional[int]
    gpt_oss_model_used: Optional[str]
    gpt_oss_feature_used: Optional[str]
    
    # 驗證信息
    is_verified: bool
    verification_date: Optional[datetime]
    status: str
    
    # 元數據
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RevenueForecastCreate(BaseModel):
    """收益預測創建請求"""
    forecast_id: str = Field(..., min_length=1, max_length=50)
    forecast_period_start: date
    forecast_period_end: date
    forecast_horizon_days: int = Field(..., gt=0, le=365)
    forecast_granularity: str = Field(..., regex='^(daily|weekly|monthly|quarterly)$')
    revenue_type: RevenueType
    forecasting_model: str = Field(..., max_length=50)
    model_version: str = Field(..., max_length=20)
    
    # 預測結果
    forecasted_revenue: condecimal(max_digits=15, decimal_places=2, ge=0)
    lower_bound_90pct: condecimal(max_digits=15, decimal_places=2, ge=0)
    upper_bound_90pct: condecimal(max_digits=15, decimal_places=2, ge=0)
    lower_bound_95pct: condecimal(max_digits=15, decimal_places=2, ge=0)
    upper_bound_95pct: condecimal(max_digits=15, decimal_places=2, ge=0)
    
    # 訓練數據信息
    training_data_start: date
    training_data_end: date
    training_sample_size: int = Field(..., gt=0)
    
    # 假設和條件
    forecast_assumptions: Dict[str, Any] = Field(..., min_items=1)
    scenario_type: str = Field('base', regex='^(optimistic|base|pessimistic)$')
    
    # 可選字段
    customer_segment: Optional[CustomerSegment] = None
    feature_category: Optional[FeatureCategory] = None
    geographic_region: Optional[str] = Field(None, max_length=50)
    
    # 模型性能
    model_accuracy_score: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = None
    mean_absolute_error: Optional[condecimal(max_digits=12, decimal_places=2, ge=0)] = None
    r_squared: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = None
    
    # 特徵和因子
    top_predictive_features: Optional[Dict[str, Any]] = None
    gpt_oss_feature_importance: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = None
    seasonal_factors: Optional[Dict[str, Any]] = None
    external_factors: Optional[Dict[str, Any]] = None
    
    @validator('forecast_period_end')
    def validate_forecast_period(cls, v, values):
        start = values.get('forecast_period_start')
        if start and v <= start:
            raise ValueError('Forecast period end must be after start')
        return v
    
    @validator('training_data_end')
    def validate_training_period(cls, v, values):
        start = values.get('training_data_start')
        if start and v <= start:
            raise ValueError('Training data end must be after start')
        return v
    
    @validator('upper_bound_90pct')
    def validate_bounds_90(cls, v, values):
        lower = values.get('lower_bound_90pct')
        forecast = values.get('forecasted_revenue')
        if lower is not None and v < lower:
            raise ValueError('Upper bound 90% must be >= lower bound 90%')
        if forecast is not None and (v < forecast or forecast < lower):
            raise ValueError('Forecasted revenue must be between 90% bounds')
        return v
    
    @validator('upper_bound_95pct')
    def validate_bounds_95(cls, v, values):
        lower_95 = values.get('lower_bound_95pct')
        lower_90 = values.get('lower_bound_90pct')
        upper_90 = values.get('upper_bound_90pct')
        
        if lower_95 is not None and v < lower_95:
            raise ValueError('Upper bound 95% must be >= lower bound 95%')
        if lower_90 is not None and lower_95 < lower_90:
            raise ValueError('Lower bound 95% must be <= lower bound 90%')
        if upper_90 is not None and v < upper_90:
            raise ValueError('Upper bound 95% must be >= upper bound 90%')
        return v

class RevenueAnalysisRequest(BaseModel):
    """收益分析請求"""
    analysis_period_start: date
    analysis_period_end: date
    revenue_types: Optional[List[RevenueType]] = None
    customer_segments: Optional[List[CustomerSegment]] = None
    feature_categories: Optional[List[FeatureCategory]] = None
    attribution_methods: Optional[List[AttributionMethod]] = None
    min_confidence_score: Optional[condecimal(max_digits=3, decimal_places=2, ge=0, le=1)] = 0.5
    include_forecasts: bool = False
    include_breakdown: bool = True
    currency: str = "USD"
    
    @validator('analysis_period_end')
    def validate_analysis_period(cls, v, values):
        start = values.get('analysis_period_start')
        if start and v <= start:
            raise ValueError('Analysis period end must be after start')
        return v

class RevenueOptimizationRequest(BaseModel):
    """收益優化請求"""
    optimization_period_start: date
    optimization_period_end: date
    target_revenue_types: List[RevenueType] = Field(..., min_items=1)
    current_performance_baseline: Optional[Dict[str, Any]] = None
    optimization_objectives: Dict[str, Any] = Field(..., min_items=1)
    constraint_parameters: Optional[Dict[str, Any]] = None
    include_sensitivity_analysis: bool = True
    include_scenario_modeling: bool = True
    optimization_horizon_months: int = Field(3, gt=0, le=12)
    
    @validator('optimization_period_end')
    def validate_optimization_period(cls, v, values):
        start = values.get('optimization_period_start')
        if start and v <= start:
            raise ValueError('Optimization period end must be after start')
        return v