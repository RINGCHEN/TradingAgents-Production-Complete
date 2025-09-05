#!/usr/bin/env python3
"""
Virtual P&L Database Models for GPT-OSS Integration
GPT-OSS虛擬損益表數據模型 - 任務2.1.1

企業級虛擬損益表系統，用於追蹤GPT-OSS本地推理服務的：
- 精確成本追蹤（硬體、電力、人力、維護）
- 收益歸因分析（阿爾法引擎會員升級等）
- 季度預算管理和ROI計算
- 內部計費和成本分攤機制
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

class CostCategory(str, Enum):
    """成本類別枚舉"""
    HARDWARE = "hardware"               # 硬體成本
    INFRASTRUCTURE = "infrastructure"   # 基礎設施成本
    POWER = "power"                    # 電力成本
    PERSONNEL = "personnel"            # 人力成本
    MAINTENANCE = "maintenance"        # 維護成本
    SOFTWARE = "software"              # 軟體許可成本
    CLOUD_FALLBACK = "cloud_fallback"  # 雲端後備成本
    NETWORK = "network"                # 網路成本
    SECURITY = "security"              # 安全相關成本
    OTHER = "other"                    # 其他成本

class CostType(str, Enum):
    """成本類型枚舉"""
    FIXED = "fixed"         # 固定成本
    VARIABLE = "variable"   # 變動成本
    AMORTIZED = "amortized"  # 攤銷成本
    ALLOCATED = "allocated"  # 分攤成本

class RevenueSource(str, Enum):
    """收益來源枚舉"""
    MEMBERSHIP_UPGRADE = "membership_upgrade"     # 會員升級
    ALPHA_ENGINE_PREMIUM = "alpha_engine_premium" # 阿爾法引擎高級功能
    API_USAGE_FEES = "api_usage_fees"            # API使用費
    SUBSCRIPTION_FEES = "subscription_fees"       # 訂閱費用
    TRADING_COMMISSION = "trading_commission"     # 交易佣金
    DATA_SERVICES = "data_services"              # 數據服務
    CONSULTING = "consulting"                    # 諮詢服務
    COST_SAVINGS = "cost_savings"               # 成本節省
    OTHER = "other"                             # 其他收益

class BudgetPeriodType(str, Enum):
    """預算週期類型"""
    MONTHLY = "monthly"     # 月度
    QUARTERLY = "quarterly" # 季度
    ANNUAL = "annual"      # 年度

class AllocationMethod(str, Enum):
    """成本分攤方法"""
    TOKEN_USAGE = "token_usage"         # 按Token使用量分攤
    REQUEST_COUNT = "request_count"     # 按請求次數分攤
    USER_COUNT = "user_count"          # 按用戶數分攤
    COMPUTE_TIME = "compute_time"      # 按計算時間分攤
    FIXED_RATIO = "fixed_ratio"        # 固定比例分攤
    ACTIVITY_BASED = "activity_based"  # 基於活動的分攤

# ==================== 核心數據模型 ====================

class CostCenter(Base):
    """成本中心表"""
    __tablename__ = "cost_centers"
    
    # 主鍵和基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # 層級結構
    parent_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=True)
    level = Column(Integer, nullable=False, default=0)
    path = Column(String(500), nullable=False)  # 層級路徑，如 "/root/ai_services/gpt_oss"
    
    # 管理信息
    manager = Column(String(100), nullable=True)
    department = Column(String(50), nullable=True)
    
    # 預算權限
    has_budget_authority = Column(Boolean, nullable=False, default=False)
    budget_limit = Column(Numeric(15, 2), nullable=True)
    
    # 狀態和元數據
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 關係
    parent = relationship("CostCenter", remote_side=[id], back_populates="children")
    children = relationship("CostCenter", back_populates="parent", cascade="all, delete-orphan")
    cost_tracking = relationship("CostTracking", back_populates="cost_center", cascade="all, delete-orphan")
    budget_allocations = relationship("BudgetAllocation", back_populates="cost_center", cascade="all, delete-orphan")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_cost_center_path', 'path'),
        Index('idx_cost_center_level', 'level'),
        Index('idx_cost_center_parent', 'parent_id'),
        CheckConstraint('budget_limit IS NULL OR budget_limit > 0', name='check_positive_budget'),
    )

class CostTracking(Base):
    """成本追蹤表 - 記錄所有成本明細"""
    __tablename__ = "cost_tracking"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=False, index=True)
    
    # 時間維度
    record_date = Column(Date, nullable=False, index=True)
    period_year = Column(Integer, nullable=False, index=True)
    period_quarter = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    
    # 成本分類
    cost_category = Column(String(30), nullable=False, index=True)
    cost_type = Column(String(20), nullable=False)
    cost_subcategory = Column(String(50), nullable=True)
    
    # 成本金額
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 成本描述和詳情
    description = Column(String(200), nullable=False)
    cost_details = Column(JSON, nullable=True)  # 存儲成本明細
    
    # 分攤信息
    allocation_method = Column(String(30), nullable=True)
    allocation_basis = Column(Numeric(15, 6), nullable=True)  # 分攤基準數值
    allocation_percentage = Column(Numeric(5, 4), nullable=True)  # 分攤百分比
    
    # 來源追蹤
    source_system = Column(String(50), nullable=True)  # 數據來源系統
    source_reference = Column(String(100), nullable=True)  # 原始記錄引用
    transaction_id = Column(String(50), nullable=True)  # 關聯交易ID
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(100), nullable=True)
    
    # 關係
    cost_center = relationship("CostCenter", back_populates="cost_tracking")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_cost_tracking_period', 'period_year', 'period_quarter', 'period_month'),
        Index('idx_cost_tracking_category', 'cost_category', 'cost_type'),
        Index('idx_cost_tracking_date_center', 'record_date', 'cost_center_id'),
        CheckConstraint('amount > 0', name='check_positive_amount'),
        CheckConstraint('period_quarter BETWEEN 1 AND 4', name='check_valid_quarter'),
        CheckConstraint('period_month BETWEEN 1 AND 12', name='check_valid_month'),
        CheckConstraint('allocation_percentage IS NULL OR allocation_percentage BETWEEN 0 AND 1', name='check_valid_percentage'),
    )

class RevenueAttribution(Base):
    """收益歸因表 - 追蹤GPT-OSS帶來的增量收益"""
    __tablename__ = "revenue_attribution"
    
    # 主鍵和基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 時間維度
    record_date = Column(Date, nullable=False, index=True)
    period_year = Column(Integer, nullable=False, index=True)
    period_quarter = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    
    # 收益分類
    revenue_source = Column(String(30), nullable=False, index=True)
    revenue_subcategory = Column(String(50), nullable=True)
    
    # 收益金額
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 歸因信息
    attribution_method = Column(String(50), nullable=False)  # 歸因方法
    attribution_confidence = Column(Numeric(3, 2), nullable=False, default=1.0)  # 歸因信心度
    gpt_oss_contribution_ratio = Column(Numeric(3, 2), nullable=False, default=1.0)  # GPT-OSS貢獻比例
    
    # 客戶和產品信息
    customer_id = Column(String(50), nullable=True)
    customer_tier = Column(String(20), nullable=True)
    product_feature = Column(String(50), nullable=True)
    
    # 收益描述和詳情
    description = Column(String(200), nullable=False)
    revenue_details = Column(JSON, nullable=True)
    
    # 比較基準
    baseline_period = Column(String(20), nullable=True)  # 基準期間
    baseline_amount = Column(Numeric(15, 2), nullable=True)  # 基準金額
    incremental_amount = Column(Numeric(15, 2), nullable=True)  # 增量金額
    
    # 來源追蹤
    source_system = Column(String(50), nullable=True)
    source_reference = Column(String(100), nullable=True)
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(String(100), nullable=True)
    
    # 約束和索引
    __table_args__ = (
        Index('idx_revenue_period', 'period_year', 'period_quarter', 'period_month'),
        Index('idx_revenue_source', 'revenue_source'),
        Index('idx_revenue_customer', 'customer_id', 'customer_tier'),
        Index('idx_revenue_date_source', 'record_date', 'revenue_source'),
        CheckConstraint('amount >= 0', name='check_non_negative_amount'),
        CheckConstraint('attribution_confidence BETWEEN 0 AND 1', name='check_valid_confidence'),
        CheckConstraint('gpt_oss_contribution_ratio BETWEEN 0 AND 1', name='check_valid_contribution'),
        CheckConstraint('period_quarter BETWEEN 1 AND 4', name='check_valid_quarter_rev'),
        CheckConstraint('period_month BETWEEN 1 AND 12', name='check_valid_month_rev'),
    )

class BudgetAllocation(Base):
    """預算分配表 - 管理季度和年度預算"""
    __tablename__ = "budget_allocations"
    
    # 主鍵和關聯
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=False, index=True)
    
    # 預算期間
    budget_year = Column(Integer, nullable=False, index=True)
    budget_period_type = Column(String(20), nullable=False)  # monthly/quarterly/annual
    budget_period = Column(Integer, nullable=True)  # 季度(1-4)或月份(1-12)，年度預算為NULL
    
    # 預算分配
    total_budget = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 分類預算
    hardware_budget = Column(Numeric(15, 2), nullable=True, default=0)
    infrastructure_budget = Column(Numeric(15, 2), nullable=True, default=0)
    power_budget = Column(Numeric(15, 2), nullable=True, default=0)
    personnel_budget = Column(Numeric(15, 2), nullable=True, default=0)
    maintenance_budget = Column(Numeric(15, 2), nullable=True, default=0)
    software_budget = Column(Numeric(15, 2), nullable=True, default=0)
    other_budget = Column(Numeric(15, 2), nullable=True, default=0)
    
    # 收益目標
    revenue_target = Column(Numeric(15, 2), nullable=True, default=0)
    cost_savings_target = Column(Numeric(15, 2), nullable=True, default=0)
    roi_target = Column(Numeric(5, 2), nullable=True)  # ROI目標百分比
    
    # 預算狀態
    budget_status = Column(String(20), nullable=False, default='draft')  # draft/approved/active/closed
    approval_level = Column(Integer, nullable=False, default=0)
    
    # 預算描述和備註
    description = Column(Text, nullable=True)
    budget_details = Column(JSON, nullable=True)
    assumptions = Column(JSON, nullable=True)  # 預算假設
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(100), nullable=True)
    
    # 關係
    cost_center = relationship("CostCenter", back_populates="budget_allocations")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_budget_period', 'budget_year', 'budget_period_type', 'budget_period'),
        Index('idx_budget_status', 'budget_status'),
        UniqueConstraint('cost_center_id', 'budget_year', 'budget_period_type', 'budget_period', 
                        name='uq_budget_allocation'),
        CheckConstraint('total_budget > 0', name='check_positive_total_budget'),
        CheckConstraint('revenue_target IS NULL OR revenue_target >= 0', name='check_non_negative_revenue_target'),
        CheckConstraint('budget_period IS NULL OR (budget_period_type = \'quarterly\' AND budget_period BETWEEN 1 AND 4) OR (budget_period_type = \'monthly\' AND budget_period BETWEEN 1 AND 12)', name='check_valid_budget_period'),
    )

class InternalBilling(Base):
    """內部計費表 - 管理內部成本分攤和計費"""
    __tablename__ = "internal_billing"
    
    # 主鍵和基本信息
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # 計費期間
    billing_date = Column(Date, nullable=False, index=True)
    billing_year = Column(Integer, nullable=False, index=True)
    billing_quarter = Column(Integer, nullable=False)
    billing_month = Column(Integer, nullable=False)
    
    # 計費主體
    provider_cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=False)
    consumer_cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=False)
    
    # 服務信息
    service_type = Column(String(50), nullable=False, index=True)  # GPT推理、數據分析等
    service_category = Column(String(30), nullable=False)
    service_description = Column(String(200), nullable=False)
    
    # 使用量信息
    usage_metric = Column(String(30), nullable=False)  # tokens/requests/compute_hours等
    usage_quantity = Column(Numeric(15, 6), nullable=False)
    unit_rate = Column(Numeric(10, 6), nullable=False)
    
    # 計費金額
    base_amount = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), nullable=True, default=0)
    tax_amount = Column(Numeric(15, 2), nullable=True, default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # 分攤信息
    allocation_method = Column(String(30), nullable=False)
    allocation_details = Column(JSON, nullable=True)
    
    # 計費狀態
    billing_status = Column(String(20), nullable=False, default='draft')  # draft/sent/paid/disputed/cancelled
    due_date = Column(Date, nullable=True)
    paid_date = Column(Date, nullable=True)
    
    # 審計信息
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    created_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(100), nullable=True)
    
    # 關係
    provider_cost_center = relationship("CostCenter", foreign_keys=[provider_cost_center_id])
    consumer_cost_center = relationship("CostCenter", foreign_keys=[consumer_cost_center_id])
    
    # 約束和索引
    __table_args__ = (
        Index('idx_billing_period', 'billing_year', 'billing_quarter', 'billing_month'),
        Index('idx_billing_service', 'service_type', 'service_category'),
        Index('idx_billing_provider_consumer', 'provider_cost_center_id', 'consumer_cost_center_id'),
        Index('idx_billing_status', 'billing_status'),
        CheckConstraint('usage_quantity > 0', name='check_positive_usage'),
        CheckConstraint('unit_rate >= 0', name='check_non_negative_rate'),
        CheckConstraint('base_amount >= 0', name='check_non_negative_base'),
        CheckConstraint('total_amount >= 0', name='check_non_negative_total'),
        CheckConstraint('provider_cost_center_id != consumer_cost_center_id', name='check_different_cost_centers'),
    )

class VirtualPnLSummary(Base):
    """虛擬損益表匯總表 - 提供週期性P&L視圖"""
    __tablename__ = "virtual_pnl_summary"
    
    # 主鍵和維度
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey('cost_centers.id'), nullable=False, index=True)
    
    # 時間維度
    summary_date = Column(Date, nullable=False, index=True)
    period_year = Column(Integer, nullable=False, index=True)
    period_quarter = Column(Integer, nullable=False, index=True)
    period_month = Column(Integer, nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # monthly/quarterly/annual
    
    # 成本匯總
    total_costs = Column(Numeric(15, 2), nullable=False, default=0)
    hardware_costs = Column(Numeric(15, 2), nullable=False, default=0)
    infrastructure_costs = Column(Numeric(15, 2), nullable=False, default=0)
    power_costs = Column(Numeric(15, 2), nullable=False, default=0)
    personnel_costs = Column(Numeric(15, 2), nullable=False, default=0)
    maintenance_costs = Column(Numeric(15, 2), nullable=False, default=0)
    software_costs = Column(Numeric(15, 2), nullable=False, default=0)
    cloud_fallback_costs = Column(Numeric(15, 2), nullable=False, default=0)
    other_costs = Column(Numeric(15, 2), nullable=False, default=0)
    
    # 收益匯總
    total_revenues = Column(Numeric(15, 2), nullable=False, default=0)
    membership_revenue = Column(Numeric(15, 2), nullable=False, default=0)
    alpha_engine_revenue = Column(Numeric(15, 2), nullable=False, default=0)
    api_usage_revenue = Column(Numeric(15, 2), nullable=False, default=0)
    cost_savings_revenue = Column(Numeric(15, 2), nullable=False, default=0)
    other_revenue = Column(Numeric(15, 2), nullable=False, default=0)
    
    # 損益計算
    gross_profit = Column(Numeric(15, 2), nullable=False, default=0)
    net_profit = Column(Numeric(15, 2), nullable=False, default=0)
    profit_margin = Column(Numeric(5, 2), nullable=True)
    
    # 關鍵指標
    roi = Column(Numeric(5, 2), nullable=True)  # 投資報酬率
    cost_per_token = Column(Numeric(10, 8), nullable=True)  # 每Token成本
    revenue_per_user = Column(Numeric(10, 2), nullable=True)  # 每用戶收益
    cost_savings_ratio = Column(Numeric(3, 2), nullable=True)  # 成本節省比例
    
    # 預算比較
    budget_variance_cost = Column(Numeric(15, 2), nullable=True)  # 成本預算差異
    budget_variance_revenue = Column(Numeric(15, 2), nullable=True)  # 收益預算差異
    budget_utilization = Column(Numeric(3, 2), nullable=True)  # 預算使用率
    
    # 統計信息
    total_tokens_processed = Column(Numeric(15, 0), nullable=True)
    total_requests_served = Column(Numeric(12, 0), nullable=True)
    active_users_count = Column(Integer, nullable=True)
    
    # 貨幣和狀態
    currency = Column(String(3), nullable=False, default='USD')
    is_consolidated = Column(Boolean, nullable=False, default=False)  # 是否為合併報表
    
    # 審計信息
    generated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    generated_by = Column(String(100), nullable=True)
    last_updated = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # 關係
    cost_center = relationship("CostCenter")
    
    # 約束和索引
    __table_args__ = (
        Index('idx_pnl_summary_period', 'period_year', 'period_quarter', 'period_month'),
        Index('idx_pnl_summary_type', 'period_type'),
        Index('idx_pnl_summary_date_center', 'summary_date', 'cost_center_id'),
        UniqueConstraint('cost_center_id', 'period_year', 'period_quarter', 'period_month', 'period_type', 
                        name='uq_pnl_summary'),
        CheckConstraint('total_costs >= 0', name='check_non_negative_costs'),
        CheckConstraint('total_revenues >= 0', name='check_non_negative_revenues'),
        CheckConstraint('profit_margin IS NULL OR profit_margin BETWEEN -100 AND 100', name='check_valid_margin'),
        CheckConstraint('roi IS NULL OR roi BETWEEN -100 AND 1000', name='check_valid_roi'),
    )

# ==================== Pydantic 請求/響應模型 ====================

class CostTrackingCreate(BaseModel):
    """成本追蹤創建請求"""
    cost_center_id: uuid.UUID
    record_date: date
    cost_category: CostCategory
    cost_type: CostType
    amount: condecimal(max_digits=15, decimal_places=2, gt=0)
    currency: str = "USD"
    description: str = Field(..., min_length=1, max_length=200)
    cost_subcategory: Optional[str] = Field(None, max_length=50)
    cost_details: Optional[Dict[str, Any]] = None
    allocation_method: Optional[AllocationMethod] = None
    allocation_basis: Optional[condecimal(max_digits=15, decimal_places=6)] = None
    allocation_percentage: Optional[condecimal(max_digits=1, decimal_places=4, ge=0, le=1)] = None
    source_system: Optional[str] = Field(None, max_length=50)
    source_reference: Optional[str] = Field(None, max_length=100)
    transaction_id: Optional[str] = Field(None, max_length=50)

class RevenueAttributionCreate(BaseModel):
    """收益歸因創建請求"""
    record_date: date
    revenue_source: RevenueSource
    amount: condecimal(max_digits=15, decimal_places=2, ge=0)
    currency: str = "USD"
    description: str = Field(..., min_length=1, max_length=200)
    attribution_method: str = Field(..., max_length=50)
    attribution_confidence: condecimal(max_digits=3, decimal_places=2, ge=0, le=1) = 1.0
    gpt_oss_contribution_ratio: condecimal(max_digits=3, decimal_places=2, ge=0, le=1) = 1.0
    revenue_subcategory: Optional[str] = Field(None, max_length=50)
    customer_id: Optional[str] = Field(None, max_length=50)
    customer_tier: Optional[str] = Field(None, max_length=20)
    product_feature: Optional[str] = Field(None, max_length=50)
    revenue_details: Optional[Dict[str, Any]] = None
    baseline_period: Optional[str] = Field(None, max_length=20)
    baseline_amount: Optional[condecimal(max_digits=15, decimal_places=2)] = None
    incremental_amount: Optional[condecimal(max_digits=15, decimal_places=2)] = None

class BudgetAllocationCreate(BaseModel):
    """預算分配創建請求"""
    cost_center_id: uuid.UUID
    budget_year: int = Field(..., ge=2020, le=2100)
    budget_period_type: BudgetPeriodType
    budget_period: Optional[int] = Field(None, ge=1, le=12)
    total_budget: condecimal(max_digits=15, decimal_places=2, gt=0)
    currency: str = "USD"
    hardware_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    infrastructure_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    power_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    personnel_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    maintenance_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    software_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    other_budget: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    revenue_target: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    cost_savings_target: Optional[condecimal(max_digits=15, decimal_places=2, ge=0)] = 0
    roi_target: Optional[condecimal(max_digits=5, decimal_places=2)] = None
    description: Optional[str] = None
    budget_details: Optional[Dict[str, Any]] = None
    assumptions: Optional[Dict[str, Any]] = None
    
    @validator('budget_period')
    def validate_budget_period(cls, v, values):
        period_type = values.get('budget_period_type')
        if period_type == BudgetPeriodType.QUARTERLY and v and (v < 1 or v > 4):
            raise ValueError('Quarterly budget period must be between 1 and 4')
        elif period_type == BudgetPeriodType.MONTHLY and v and (v < 1 or v > 12):
            raise ValueError('Monthly budget period must be between 1 and 12')
        elif period_type == BudgetPeriodType.ANNUAL and v is not None:
            raise ValueError('Annual budget should not have a period value')
        return v

class VirtualPnLSummaryResponse(BaseModel):
    """虛擬損益表匯總響應"""
    id: uuid.UUID
    cost_center_id: uuid.UUID
    summary_date: date
    period_year: int
    period_quarter: int
    period_month: int
    period_type: str
    
    # 成本明細
    total_costs: Decimal
    hardware_costs: Decimal
    infrastructure_costs: Decimal
    power_costs: Decimal
    personnel_costs: Decimal
    maintenance_costs: Decimal
    software_costs: Decimal
    cloud_fallback_costs: Decimal
    other_costs: Decimal
    
    # 收益明細
    total_revenues: Decimal
    membership_revenue: Decimal
    alpha_engine_revenue: Decimal
    api_usage_revenue: Decimal
    cost_savings_revenue: Decimal
    other_revenue: Decimal
    
    # 損益指標
    gross_profit: Decimal
    net_profit: Decimal
    profit_margin: Optional[Decimal]
    roi: Optional[Decimal]
    cost_per_token: Optional[Decimal]
    revenue_per_user: Optional[Decimal]
    cost_savings_ratio: Optional[Decimal]
    
    # 預算比較
    budget_variance_cost: Optional[Decimal]
    budget_variance_revenue: Optional[Decimal]
    budget_utilization: Optional[Decimal]
    
    # 統計信息
    total_tokens_processed: Optional[int]
    total_requests_served: Optional[int]
    active_users_count: Optional[int]
    
    currency: str
    is_consolidated: bool
    generated_at: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True

class CostAnalysisRequest(BaseModel):
    """成本分析請求"""
    cost_center_ids: Optional[List[uuid.UUID]] = None
    start_date: date
    end_date: date
    cost_categories: Optional[List[CostCategory]] = None
    period_type: str = "monthly"  # daily/weekly/monthly/quarterly
    include_allocation: bool = True
    currency: str = "USD"

class ROIAnalysisRequest(BaseModel):
    """ROI分析請求"""
    cost_center_ids: Optional[List[uuid.UUID]] = None
    analysis_period_start: date
    analysis_period_end: date
    baseline_period_start: Optional[date] = None
    baseline_period_end: Optional[date] = None
    include_soft_benefits: bool = True
    discount_rate: Optional[condecimal(max_digits=5, decimal_places=4)] = 0.08
    currency: str = "USD"