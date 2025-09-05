#!/usr/bin/env python3
"""
Revenue Attribution Models
收益歸因數據模型

GPT-OSS整合任務2.1.3 - 收益歸因系統核心數據模型
提供完整的收益追蹤、歸因分析和預測建模數據結構
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, Numeric, Integer, Text, Boolean, ForeignKey, JSON, Date, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

Base = declarative_base()


# ==================== 枚舉定義 ====================

class RevenueType(str, Enum):
    """收益類型"""
    API_COST_SAVINGS = "api_cost_savings"  # API成本節省
    NEW_FEATURE_REVENUE = "new_feature_revenue"  # 新功能收益
    MEMBERSHIP_UPGRADE = "membership_upgrade"  # 會員升級
    EFFICIENCY_GAINS = "efficiency_gains"  # 效率提升收益
    PREMIUM_SERVICE = "premium_service"  # 高級服務收益


class AttributionMethod(str, Enum):
    """歸因方法"""
    DIRECT = "direct"  # 直接歸因
    TIME_DECAY = "time_decay"  # 時間衰減
    LINEAR = "linear"  # 線性分配
    ALGORITHMIC = "algorithmic"  # 算法歸因
    WEIGHTED = "weighted"  # 加權歸因


class RevenueConfidence(str, Enum):
    """收益信心度等級"""
    HIGH = "high"  # 高信心度 (>90%)
    MEDIUM = "medium"  # 中等信心度 (70-90%)
    LOW = "low"  # 低信心度 (<70%)
    ESTIMATED = "estimated"  # 估算值


class PredictionHorizon(str, Enum):
    """預測時間範圍"""
    WEEKLY = "weekly"  # 週預測
    MONTHLY = "monthly"  # 月預測
    QUARTERLY = "quarterly"  # 季預測
    ANNUAL = "annual"  # 年預測


class ModelType(str, Enum):
    """預測模型類型"""
    LINEAR_REGRESSION = "linear_regression"
    ARIMA = "arima"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    CUSTOM = "custom"


# ==================== SQLAlchemy 數據模型 ====================

class RevenueAttributionRecord(Base):
    """收益歸因記錄表"""
    __tablename__ = "revenue_attribution_records"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    revenue_type = Column(SQLEnum(RevenueType), nullable=False)
    attribution_method = Column(SQLEnum(AttributionMethod), nullable=False)
    
    # 收益基本信息
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="USD")
    attribution_date = Column(Date, nullable=False)
    attribution_period_start = Column(Date, nullable=False)
    attribution_period_end = Column(Date, nullable=False)
    
    # GPT-OSS 歸因信息
    source_gpt_oss_feature = Column(String(200), nullable=False)
    gpt_oss_contribution_percentage = Column(Numeric(5, 2), nullable=False)
    baseline_cost_without_gpt_oss = Column(Numeric(15, 2), nullable=True)
    
    # 歸因詳細信息
    confidence_level = Column(SQLEnum(RevenueConfidence), nullable=False)
    confidence_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    attribution_factors = Column(JSON, nullable=True)
    
    # 業務關聯信息
    user_id = Column(String(100), nullable=True)
    service_id = Column(String(100), nullable=True)
    feature_id = Column(String(100), nullable=True)
    campaign_id = Column(String(100), nullable=True)
    
    # 元數據
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    created_by = Column(String(100), nullable=False)
    validation_status = Column(String(50), default="pending")
    notes = Column(Text, nullable=True)
    additional_metadata = Column(JSON, nullable=True)
    
    # 關係
    cost_savings = relationship("APICostSaving", back_populates="attribution_record")
    membership_upgrades = relationship("MembershipUpgradeAttribution", back_populates="attribution_record")


class APICostSaving(Base):
    """API成本節省記錄表"""
    __tablename__ = "api_cost_savings"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    attribution_record_id = Column(PG_UUID(as_uuid=True), ForeignKey("revenue_attribution_records.id"))
    
    # 成本節省詳細信息
    original_api_provider = Column(String(100), nullable=False)  # OpenAI, Anthropic
    gpt_oss_provider = Column(String(100), nullable=False)  # Local GPT-OSS
    
    # 使用量統計
    total_tokens_processed = Column(Integer, nullable=False)
    total_requests_handled = Column(Integer, nullable=False)
    processing_time_hours = Column(Numeric(10, 2), nullable=False)
    
    # 成本計算
    original_api_cost = Column(Numeric(15, 6), nullable=False)
    gpt_oss_cost = Column(Numeric(15, 6), nullable=False)
    savings_amount = Column(Numeric(15, 6), nullable=False)
    savings_percentage = Column(Numeric(5, 2), nullable=False)
    
    # 品質指標
    quality_score = Column(Numeric(5, 2), nullable=True)  # 0-100
    latency_improvement = Column(Numeric(8, 2), nullable=True)  # milliseconds
    accuracy_comparison = Column(Numeric(5, 2), nullable=True)  # percentage
    
    # 時間信息
    calculation_date = Column(Date, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # 元數據
    calculation_method = Column(String(100), nullable=False)
    pricing_model_version = Column(String(50), nullable=False)
    additional_metrics = Column(JSON, nullable=True)
    
    # 關係
    attribution_record = relationship("RevenueAttributionRecord", back_populates="cost_savings")


class NewFeatureRevenue(Base):
    """新功能收益記錄表"""
    __tablename__ = "new_feature_revenues"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    attribution_record_id = Column(PG_UUID(as_uuid=True), ForeignKey("revenue_attribution_records.id"))
    
    # 功能信息
    feature_name = Column(String(200), nullable=False)
    feature_category = Column(String(100), nullable=False)
    launch_date = Column(Date, nullable=False)
    gpt_oss_dependency_level = Column(String(50), nullable=False)  # high, medium, low
    
    # 收益追蹤
    direct_revenue = Column(Numeric(15, 2), nullable=False)
    indirect_revenue = Column(Numeric(15, 2), nullable=False)
    recurring_revenue = Column(Numeric(15, 2), nullable=False)
    one_time_revenue = Column(Numeric(15, 2), nullable=False)
    
    # 用戶採用指標
    total_users_engaged = Column(Integer, nullable=False)
    paid_conversions = Column(Integer, nullable=False)
    conversion_rate = Column(Numeric(5, 2), nullable=False)
    average_revenue_per_user = Column(Numeric(10, 2), nullable=False)
    
    # GPT-OSS 貢獻分析
    performance_without_gpt_oss = Column(Numeric(5, 2), nullable=True)  # estimated percentage
    unique_capabilities_enabled = Column(JSON, nullable=True)
    cost_efficiency_gained = Column(Numeric(8, 2), nullable=True)
    
    # 時間信息
    measurement_period_start = Column(Date, nullable=False)
    measurement_period_end = Column(Date, nullable=False)
    
    # 元數據
    tracking_methodology = Column(String(200), nullable=False)
    data_sources = Column(JSON, nullable=False)
    validation_notes = Column(Text, nullable=True)


class MembershipUpgradeAttribution(Base):
    """會員升級歸因記錄表"""
    __tablename__ = "membership_upgrade_attributions"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    attribution_record_id = Column(PG_UUID(as_uuid=True), ForeignKey("revenue_attribution_records.id"))
    
    # 會員升級信息
    user_id = Column(String(100), nullable=False)
    from_tier = Column(String(50), nullable=False)
    to_tier = Column(String(50), nullable=False)
    upgrade_date = Column(DateTime, nullable=False)
    
    # 收益信息
    upgrade_revenue = Column(Numeric(10, 2), nullable=False)
    projected_annual_value = Column(Numeric(12, 2), nullable=False)
    retention_probability = Column(Numeric(5, 2), nullable=False)
    
    # GPT-OSS 歸因分析
    gpt_oss_features_used = Column(JSON, nullable=False)
    usage_frequency_before_upgrade = Column(Integer, nullable=False)  # days
    key_trigger_features = Column(JSON, nullable=False)
    
    # 歸因權重
    direct_influence_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    indirect_influence_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    competitive_advantage_score = Column(Numeric(5, 2), nullable=False)  # 0-100
    
    # 分析方法
    attribution_algorithm = Column(String(100), nullable=False)
    touchpoint_analysis = Column(JSON, nullable=True)
    behavioral_analysis = Column(JSON, nullable=True)
    
    # 元數據
    analysis_date = Column(DateTime, nullable=False)
    analyst_notes = Column(Text, nullable=True)
    confidence_factors = Column(JSON, nullable=True)
    
    # 關係
    attribution_record = relationship("RevenueAttributionRecord", back_populates="membership_upgrades")


class RevenueForecast(Base):
    """收益預測記錄表"""
    __tablename__ = "revenue_forecasts"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 預測基本信息
    forecast_name = Column(String(200), nullable=False)
    revenue_type = Column(SQLEnum(RevenueType), nullable=False)
    prediction_horizon = Column(SQLEnum(PredictionHorizon), nullable=False)
    model_type = Column(SQLEnum(ModelType), nullable=False)
    
    # 預測結果
    predicted_amount = Column(Numeric(15, 2), nullable=False)
    confidence_interval_lower = Column(Numeric(15, 2), nullable=False)
    confidence_interval_upper = Column(Numeric(15, 2), nullable=False)
    prediction_accuracy = Column(Numeric(5, 2), nullable=True)  # if available
    
    # 預測期間
    forecast_period_start = Column(Date, nullable=False)
    forecast_period_end = Column(Date, nullable=False)
    forecast_generated_date = Column(DateTime, nullable=False)
    
    # 模型信息
    model_version = Column(String(50), nullable=False)
    training_data_size = Column(Integer, nullable=False)
    feature_importance = Column(JSON, nullable=True)
    model_parameters = Column(JSON, nullable=True)
    
    # GPT-OSS 特定預測
    gpt_oss_impact_factor = Column(Numeric(5, 2), nullable=False)
    baseline_scenario = Column(Numeric(15, 2), nullable=False)
    optimistic_scenario = Column(Numeric(15, 2), nullable=False)
    pessimistic_scenario = Column(Numeric(15, 2), nullable=False)
    
    # 驗證和更新
    last_validation_date = Column(DateTime, nullable=True)
    actual_vs_predicted = Column(Numeric(8, 2), nullable=True)
    model_drift_score = Column(Numeric(5, 2), nullable=True)
    
    # 元數據
    created_by = Column(String(100), nullable=False)
    validation_status = Column(String(50), default="active")
    notes = Column(Text, nullable=True)
    additional_attributes = Column(JSON, nullable=True)


# ==================== Pydantic 架構模型 ====================

class RevenueAttributionRecordSchema(BaseModel):
    """收益歸因記錄架構"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    revenue_type: RevenueType
    attribution_method: AttributionMethod
    
    # 收益基本信息
    amount: Decimal = Field(ge=0)
    currency: str = Field(default="USD", max_length=10)
    attribution_date: date
    attribution_period_start: date
    attribution_period_end: date
    
    # GPT-OSS 歸因信息
    source_gpt_oss_feature: str = Field(max_length=200)
    gpt_oss_contribution_percentage: Decimal = Field(ge=0, le=100)
    baseline_cost_without_gpt_oss: Optional[Decimal] = Field(default=None, ge=0)
    
    # 歸因詳細信息
    confidence_level: RevenueConfidence
    confidence_score: Decimal = Field(ge=0, le=100)
    attribution_factors: Optional[Dict[str, Any]] = None
    
    # 業務關聯信息
    user_id: Optional[str] = Field(default=None, max_length=100)
    service_id: Optional[str] = Field(default=None, max_length=100)
    feature_id: Optional[str] = Field(default=None, max_length=100)
    campaign_id: Optional[str] = Field(default=None, max_length=100)
    
    # 元數據
    created_at: datetime
    updated_at: datetime
    created_by: str = Field(max_length=100)
    validation_status: str = Field(default="pending", max_length=50)
    notes: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None
    
    @validator('attribution_period_end')
    def end_after_start(cls, v, values):
        if 'attribution_period_start' in values and v <= values['attribution_period_start']:
            raise ValueError('attribution_period_end must be after attribution_period_start')
        return v
    
    class Config:
        from_attributes = True


class APICostSavingSchema(BaseModel):
    """API成本節省記錄架構"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    attribution_record_id: UUID
    
    # 成本節省詳細信息
    original_api_provider: str = Field(max_length=100)
    gpt_oss_provider: str = Field(max_length=100)
    
    # 使用量統計
    total_tokens_processed: int = Field(ge=0)
    total_requests_handled: int = Field(ge=0)
    processing_time_hours: Decimal = Field(ge=0)
    
    # 成本計算
    original_api_cost: Decimal = Field(ge=0)
    gpt_oss_cost: Decimal = Field(ge=0)
    savings_amount: Decimal = Field(ge=0)
    savings_percentage: Decimal = Field(ge=0, le=100)
    
    # 品質指標
    quality_score: Optional[Decimal] = Field(default=None, ge=0, le=100)
    latency_improvement: Optional[Decimal] = None
    accuracy_comparison: Optional[Decimal] = Field(default=None, ge=-100, le=100)
    
    # 時間信息
    calculation_date: date
    period_start: datetime
    period_end: datetime
    
    # 元數據
    calculation_method: str = Field(max_length=100)
    pricing_model_version: str = Field(max_length=50)
    additional_metrics: Optional[Dict[str, Any]] = None
    
    @validator('savings_amount')
    def calculate_savings(cls, v, values):
        if 'original_api_cost' in values and 'gpt_oss_cost' in values:
            expected_savings = values['original_api_cost'] - values['gpt_oss_cost']
            if abs(v - expected_savings) > Decimal('0.01'):
                raise ValueError('savings_amount must equal original_api_cost - gpt_oss_cost')
        return v
    
    class Config:
        from_attributes = True


class NewFeatureRevenueSchema(BaseModel):
    """新功能收益記錄架構"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    attribution_record_id: UUID
    
    # 功能信息
    feature_name: str = Field(max_length=200)
    feature_category: str = Field(max_length=100)
    launch_date: date
    gpt_oss_dependency_level: str = Field(max_length=50)
    
    # 收益追蹤
    direct_revenue: Decimal = Field(ge=0)
    indirect_revenue: Decimal = Field(ge=0)
    recurring_revenue: Decimal = Field(ge=0)
    one_time_revenue: Decimal = Field(ge=0)
    
    # 用戶採用指標
    total_users_engaged: int = Field(ge=0)
    paid_conversions: int = Field(ge=0)
    conversion_rate: Decimal = Field(ge=0, le=100)
    average_revenue_per_user: Decimal = Field(ge=0)
    
    # GPT-OSS 貢獻分析
    performance_without_gpt_oss: Optional[Decimal] = Field(default=None, ge=0, le=100)
    unique_capabilities_enabled: Optional[List[str]] = None
    cost_efficiency_gained: Optional[Decimal] = Field(default=None, ge=0)
    
    # 時間信息
    measurement_period_start: date
    measurement_period_end: date
    
    # 元數據
    tracking_methodology: str = Field(max_length=200)
    data_sources: List[str]
    validation_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class MembershipUpgradeAttributionSchema(BaseModel):
    """會員升級歸因記錄架構"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    attribution_record_id: UUID
    
    # 會員升級信息
    user_id: str = Field(max_length=100)
    from_tier: str = Field(max_length=50)
    to_tier: str = Field(max_length=50)
    upgrade_date: datetime
    
    # 收益信息
    upgrade_revenue: Decimal = Field(ge=0)
    projected_annual_value: Decimal = Field(ge=0)
    retention_probability: Decimal = Field(ge=0, le=100)
    
    # GPT-OSS 歸因分析
    gpt_oss_features_used: List[str]
    usage_frequency_before_upgrade: int = Field(ge=0)
    key_trigger_features: List[str]
    
    # 歸因權重
    direct_influence_score: Decimal = Field(ge=0, le=100)
    indirect_influence_score: Decimal = Field(ge=0, le=100)
    competitive_advantage_score: Decimal = Field(ge=0, le=100)
    
    # 分析方法
    attribution_algorithm: str = Field(max_length=100)
    touchpoint_analysis: Optional[Dict[str, Any]] = None
    behavioral_analysis: Optional[Dict[str, Any]] = None
    
    # 元數據
    analysis_date: datetime
    analyst_notes: Optional[str] = None
    confidence_factors: Optional[Dict[str, float]] = None
    
    class Config:
        from_attributes = True


class RevenueForecastSchema(BaseModel):
    """收益預測記錄架構"""
    id: Optional[UUID] = Field(default_factory=uuid4)
    
    # 預測基本信息
    forecast_name: str = Field(max_length=200)
    revenue_type: RevenueType
    prediction_horizon: PredictionHorizon
    model_type: ModelType
    
    # 預測結果
    predicted_amount: Decimal = Field(ge=0)
    confidence_interval_lower: Decimal = Field(ge=0)
    confidence_interval_upper: Decimal = Field(ge=0)
    prediction_accuracy: Optional[Decimal] = Field(default=None, ge=0, le=100)
    
    # 預測期間
    forecast_period_start: date
    forecast_period_end: date
    forecast_generated_date: datetime
    
    # 模型信息
    model_version: str = Field(max_length=50)
    training_data_size: int = Field(ge=0)
    feature_importance: Optional[Dict[str, float]] = None
    model_parameters: Optional[Dict[str, Any]] = None
    
    # GPT-OSS 特定預測
    gpt_oss_impact_factor: Decimal = Field(ge=0, le=100)
    baseline_scenario: Decimal = Field(ge=0)
    optimistic_scenario: Decimal = Field(ge=0)
    pessimistic_scenario: Decimal = Field(ge=0)
    
    # 驗證和更新
    last_validation_date: Optional[datetime] = None
    actual_vs_predicted: Optional[Decimal] = Field(default=None, ge=-1000, le=1000)  # percentage difference
    model_drift_score: Optional[Decimal] = Field(default=None, ge=0, le=100)
    
    # 元數據
    created_by: str = Field(max_length=100)
    validation_status: str = Field(default="active", max_length=50)
    notes: Optional[str] = None
    additional_attributes: Optional[Dict[str, Any]] = None
    
    @validator('confidence_interval_upper')
    def upper_ge_lower(cls, v, values):
        if 'confidence_interval_lower' in values and v < values['confidence_interval_lower']:
            raise ValueError('confidence_interval_upper must be >= confidence_interval_lower')
        return v
    
    @validator('confidence_interval_lower')
    def lower_le_predicted(cls, v, values):
        if 'predicted_amount' in values and v > values['predicted_amount']:
            raise ValueError('confidence_interval_lower must be <= predicted_amount')
        return v
    
    @validator('confidence_interval_upper')
    def upper_ge_predicted(cls, v, values):
        if 'predicted_amount' in values and v < values['predicted_amount']:
            raise ValueError('confidence_interval_upper must be >= predicted_amount')
        return v
    
    class Config:
        from_attributes = True


# ==================== 請求/響應模型 ====================

class RevenueAttributionRequest(BaseModel):
    """收益歸因請求模型"""
    revenue_type: RevenueType
    attribution_method: AttributionMethod
    target_ids: List[str]
    start_date: date
    end_date: date
    confidence_threshold: Optional[Decimal] = Field(default=Decimal('70.0'), ge=0, le=100)
    include_projections: bool = False
    attribution_factors: Optional[Dict[str, Any]] = None


class RevenueForecastRequest(BaseModel):
    """收益預測請求模型"""
    forecast_name: str = Field(max_length=200)
    revenue_type: RevenueType
    prediction_horizon: PredictionHorizon
    model_type: ModelType
    target_ids: Optional[List[str]] = None
    historical_data_months: int = Field(default=12, ge=3, le=60)
    include_scenarios: bool = True
    confidence_level: Decimal = Field(default=Decimal('95.0'), ge=50, le=99)


class RevenueAnalysisResponse(BaseModel):
    """收益分析響應模型"""
    analysis_id: UUID
    analysis_type: str
    total_attributed_revenue: Decimal
    confidence_score: Decimal
    gpt_oss_contribution: Decimal
    key_insights: List[str]
    recommendations: List[str]
    data_quality_score: Decimal
    analysis_date: datetime
    next_review_date: date