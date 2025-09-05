#!/usr/bin/env python3
"""
Task Metadata Database Models
GPT-OSS任务元数据数据库模型
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum
from sqlalchemy import (
    Column, String, Float, Integer, DateTime, Text, Boolean,
    JSON, UUID, Index, ForeignKey, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, validator

from .database import Base

class TaskType(str, Enum):
    """标准任务类型枚举"""
    SUMMARY = "summary"
    CLASSIFICATION = "classification"
    REASONING = "reasoning"
    GENERATION = "generation"
    ANALYSIS = "analysis"
    SENTIMENT = "sentiment"
    TRANSLATION = "translation"
    EXTRACTION = "extraction"

class DataSensitivityLevel(str, Enum):
    """数据敏感度等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIDENTIAL = "confidential"

class BusinessPriority(str, Enum):
    """业务优先级"""
    CRITICAL = "critical"
    IMPORTANT = "important"
    STANDARD = "standard"
    LOW = "low"

class TaskCategory(str, Enum):
    """任务分类"""
    REAL_TIME = "real_time"
    BATCH = "batch"
    INTERACTIVE = "interactive"
    BACKGROUND = "background"

# ==================== Database Models ====================

class TaskMetadata(Base):
    """任务元数据表"""
    __tablename__ = "task_metadata"
    
    # 主键和基础信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_type = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, default=TaskCategory.INTERACTIVE.value)
    
    # 质量和性能要求
    required_quality_threshold = Column(Float, nullable=False, default=0.7)
    max_acceptable_latency_ms = Column(Integer, nullable=False, default=5000)
    max_acceptable_cost_per_1k = Column(Float, nullable=False, default=0.01)
    
    # 安全和敏感度
    data_sensitivity_level = Column(String(20), nullable=False, default=DataSensitivityLevel.MEDIUM.value)
    requires_local_processing = Column(Boolean, nullable=False, default=False)
    allow_cloud_fallback = Column(Boolean, nullable=False, default=True)
    
    # 业务配置
    business_priority = Column(String(20), nullable=False, default=BusinessPriority.STANDARD.value)
    enable_caching = Column(Boolean, nullable=False, default=True)
    cache_ttl_seconds = Column(Integer, nullable=False, default=300)
    
    # 模型要求
    min_model_capability_score = Column(Float, nullable=False, default=0.5)
    preferred_model_types = Column(JSON, nullable=True)  # ["instruct", "chat", "completion"]
    required_features = Column(JSON, nullable=True)  # ["reasoning", "code", "math"]
    
    # 资源限制
    max_tokens_input = Column(Integer, nullable=False, default=4000)
    max_tokens_output = Column(Integer, nullable=False, default=1000)
    max_retry_attempts = Column(Integer, nullable=False, default=3)
    timeout_seconds = Column(Integer, nullable=False, default=30)
    
    # 度量和监控
    success_rate_threshold = Column(Float, nullable=False, default=0.95)
    enable_quality_monitoring = Column(Boolean, nullable=False, default=True)
    enable_cost_tracking = Column(Boolean, nullable=False, default=True)
    
    # 元数据和时间戳
    extra_metadata = Column(JSON, nullable=True)
    version = Column(String(20), nullable=False, default="1.0")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    
    # 关系
    routing_rules = relationship("TaskRoutingRule", back_populates="task_metadata", cascade="all, delete-orphan")
    performance_metrics = relationship("TaskPerformanceMetric", back_populates="task_metadata", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_task_metadata_type_active', 'task_type', 'is_active'),
        Index('idx_task_metadata_priority_latency', 'business_priority', 'max_acceptable_latency_ms'),
        Index('idx_task_metadata_sensitivity', 'data_sensitivity_level'),
        Index('idx_task_metadata_category', 'category'),
    )

class TaskRoutingRule(Base):
    """任务路由规则表"""
    __tablename__ = "task_routing_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_metadata_id = Column(UUID(as_uuid=True), ForeignKey('task_metadata.id'), nullable=False)
    
    # 路由条件
    condition_name = Column(String(100), nullable=False)
    condition_type = Column(String(50), nullable=False)  # "user_tier", "time_of_day", "load", "cost"
    condition_value = Column(JSON, nullable=False)
    
    # 路由目标
    preferred_providers = Column(JSON, nullable=False)  # ["gpt_oss", "openai", "anthropic"]
    provider_weights = Column(JSON, nullable=True)  # {"gpt_oss": 0.8, "openai": 0.2}
    fallback_strategy = Column(String(50), nullable=False, default="next_available")
    
    # 规则配置
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # 关系
    task_metadata = relationship("TaskMetadata", back_populates="routing_rules")
    
    # 索引
    __table_args__ = (
        Index('idx_routing_rule_task_active', 'task_metadata_id', 'is_active'),
        Index('idx_routing_rule_priority', 'priority'),
    )

class TaskPerformanceMetric(Base):
    """任务性能指标表"""
    __tablename__ = "task_performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_metadata_id = Column(UUID(as_uuid=True), ForeignKey('task_metadata.id'), nullable=False)
    
    # 提供商信息
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    
    # 性能指标
    avg_latency_ms = Column(Float, nullable=False)
    p95_latency_ms = Column(Float, nullable=False)
    success_rate = Column(Float, nullable=False)
    avg_quality_score = Column(Float, nullable=True)
    avg_cost_per_request = Column(Float, nullable=False)
    
    # 统计信息
    total_requests = Column(Integer, nullable=False, default=0)
    total_failures = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    
    # 时间窗口
    measurement_period_start = Column(DateTime(timezone=True), nullable=False)
    measurement_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # 元数据
    perf_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # 关系
    task_metadata = relationship("TaskMetadata", back_populates="performance_metrics")
    
    # 索引
    __table_args__ = (
        Index('idx_performance_task_provider', 'task_metadata_id', 'provider'),
        Index('idx_performance_measurement_period', 'measurement_period_start', 'measurement_period_end'),
        UniqueConstraint('task_metadata_id', 'provider', 'model', 'measurement_period_start', name='uq_performance_measurement'),
    )

class ModelCapability(Base):
    """模型能力表"""
    __tablename__ = "model_capabilities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 模型信息
    provider = Column(String(50), nullable=False)
    model_id = Column(String(100), nullable=False)
    model_name = Column(String(200), nullable=False)
    model_version = Column(String(50), nullable=True)
    
    # 能力指标
    capability_score = Column(Float, nullable=False)  # 综合能力评分 0-1
    reasoning_score = Column(Float, nullable=True)
    creativity_score = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)
    speed_score = Column(Float, nullable=True)
    
    # 成本和性能
    cost_per_1k_input_tokens = Column(Float, nullable=False)
    cost_per_1k_output_tokens = Column(Float, nullable=False)
    max_tokens = Column(Integer, nullable=False)
    avg_latency_ms = Column(Float, nullable=False)
    
    # 特性支持
    supported_features = Column(JSON, nullable=True)  # ["function_calling", "json_mode", "vision"]
    supported_languages = Column(JSON, nullable=True)  # ["zh", "en", "ja"]
    context_length = Column(Integer, nullable=False)
    
    # 可用性
    is_available = Column(Boolean, nullable=False, default=True)
    availability_region = Column(String(50), nullable=True)
    privacy_level = Column(String(20), nullable=False)  # "local", "cloud", "hybrid"
    
    # 基准测试结果
    benchmark_scores = Column(JSON, nullable=True)
    last_benchmarked = Column(DateTime(timezone=True), nullable=True)
    
    # 元数据
    capability_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 索引
    __table_args__ = (
        Index('idx_model_capability_provider_model', 'provider', 'model_id'),
        Index('idx_model_capability_score', 'capability_score'),
        Index('idx_model_capability_available', 'is_available'),
        UniqueConstraint('provider', 'model_id', name='uq_provider_model'),
    )

# ==================== Pydantic Models ====================

class TaskMetadataCreate(BaseModel):
    """创建任务元数据的请求模型"""
    task_type: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: TaskCategory = TaskCategory.INTERACTIVE
    
    required_quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_acceptable_latency_ms: int = Field(default=5000, gt=0)
    max_acceptable_cost_per_1k: float = Field(default=0.01, ge=0.0)
    
    data_sensitivity_level: DataSensitivityLevel = DataSensitivityLevel.MEDIUM
    requires_local_processing: bool = False
    allow_cloud_fallback: bool = True
    
    business_priority: BusinessPriority = BusinessPriority.STANDARD
    enable_caching: bool = True
    cache_ttl_seconds: int = Field(default=300, gt=0)
    
    min_model_capability_score: float = Field(default=0.5, ge=0.0, le=1.0)
    preferred_model_types: Optional[List[str]] = None
    required_features: Optional[List[str]] = None
    
    max_tokens_input: int = Field(default=4000, gt=0)
    max_tokens_output: int = Field(default=1000, gt=0)
    max_retry_attempts: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=30, gt=0)
    
    success_rate_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    enable_quality_monitoring: bool = True
    enable_cost_tracking: bool = True
    
    extra_metadata: Optional[Dict[str, Any]] = None
    version: str = Field(default="1.0", max_length=20)

class TaskMetadataUpdate(BaseModel):
    """更新任务元数据的请求模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    required_quality_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_acceptable_latency_ms: Optional[int] = Field(None, gt=0)
    max_acceptable_cost_per_1k: Optional[float] = Field(None, ge=0.0)
    data_sensitivity_level: Optional[DataSensitivityLevel] = None
    business_priority: Optional[BusinessPriority] = None
    is_active: Optional[bool] = None
    extra_metadata: Optional[Dict[str, Any]] = None

class TaskMetadataResponse(BaseModel):
    """任务元数据响应模型"""
    id: uuid.UUID
    task_type: str
    name: str
    description: Optional[str]
    category: str
    required_quality_threshold: float
    max_acceptable_latency_ms: int
    max_acceptable_cost_per_1k: float
    data_sensitivity_level: str
    requires_local_processing: bool
    allow_cloud_fallback: bool
    business_priority: str
    enable_caching: bool
    cache_ttl_seconds: int
    min_model_capability_score: float
    preferred_model_types: Optional[List[str]]
    required_features: Optional[List[str]]
    max_tokens_input: int
    max_tokens_output: int
    max_retry_attempts: int
    timeout_seconds: int
    success_rate_threshold: float
    enable_quality_monitoring: bool
    enable_cost_tracking: bool
    extra_metadata: Optional[Dict[str, Any]]
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True

class ModelCapabilityResponse(BaseModel):
    """模型能力响应模型"""
    id: uuid.UUID
    provider: str
    model_id: str
    model_name: str
    model_version: Optional[str]
    capability_score: float
    reasoning_score: Optional[float]
    creativity_score: Optional[float]
    accuracy_score: Optional[float]
    speed_score: Optional[float]
    cost_per_1k_input_tokens: float
    cost_per_1k_output_tokens: float
    max_tokens: int
    avg_latency_ms: float
    supported_features: Optional[List[str]]
    supported_languages: Optional[List[str]]
    context_length: int
    is_available: bool
    availability_region: Optional[str]
    privacy_level: str
    benchmark_scores: Optional[Dict[str, Any]]
    last_benchmarked: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class RoutingDecisionRequest(BaseModel):
    """路由决策请求模型"""
    task_type: str
    user_tier: Optional[str] = "free"
    estimated_tokens: int = 1000
    priority: Optional[str] = "standard"
    requires_high_quality: bool = False
    max_acceptable_latency: Optional[int] = None
    max_acceptable_cost: Optional[float] = None
    user_preferences: Optional[Dict[str, Any]] = None

class RoutingDecisionResponse(BaseModel):
    """路由决策响应模型"""
    selected_provider: str
    selected_model: str
    reasoning: str
    expected_cost: float
    expected_latency_ms: int
    expected_quality_score: float
    confidence_score: float
    fallback_options: List[Dict[str, str]]
    decision_metadata: Dict[str, Any]