#!/usr/bin/env python3
"""
財務管理模型 (Financial Management Models)
天工 (TianGong) - 財務管理相關的數據模型

此模組定義財務管理功能的所有數據模型，包含：
1. 交易和付款模型
2. 發票和訂閱模型
3. 財務報表模型
4. 稅務和預算模型
5. 退款和預測模型
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pydantic import BaseModel, Field, validator

# ==================== 基礎枚舉 ====================

class TransactionType(str, Enum):
    """交易類型"""
    PAYMENT = "payment"
    REFUND = "refund"
    ADJUSTMENT = "adjustment"
    TRANSFER = "transfer"
    FEE = "fee"
    COMMISSION = "commission"

class TransactionStatus(str, Enum):
    """交易狀態"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentMethod(str, Enum):
    """付款方式"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    CRYPTO = "crypto"

class InvoiceStatus(str, Enum):
    """發票狀態"""
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionStatus(str, Enum):
    """訂閱狀態"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TRIAL = "trial"

class RefundStatus(str, Enum):
    """退款狀態"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# ==================== 交易模型 ====================

class Transaction(BaseModel):
    """交易模型"""
    transaction_id: str
    user_id: str
    amount: Decimal
    currency: str = "TWD"
    transaction_type: TransactionType
    payment_method: PaymentMethod
    status: TransactionStatus
    description: Optional[str] = None
    reference_id: Optional[str] = None  # 關聯的訂閱或發票ID
    gateway_transaction_id: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class TransactionRequest(BaseModel):
    """交易請求模型"""
    user_id: str
    amount: Decimal
    currency: str = "TWD"
    transaction_type: TransactionType
    payment_method: PaymentMethod
    description: Optional[str] = None
    reference_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('交易金額必須大於0')
        return v

# ==================== 發票模型 ====================

class Invoice(BaseModel):
    """發票模型"""
    invoice_id: str
    invoice_number: str
    user_id: str
    amount: Decimal
    tax_amount: Decimal = Decimal('0')
    currency: str = "TWD"
    status: InvoiceStatus
    due_date: datetime
    items: List[Dict[str, Any]] = []
    billing_address: Dict[str, str] = {}
    notes: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class InvoiceItem(BaseModel):
    """發票項目模型"""
    item_id: str
    description: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    tax_rate: Decimal = Decimal('0.05')  # 5% 營業稅
    
    @validator('total_price', always=True)
    def calculate_total(cls, v, values):
        if 'quantity' in values and 'unit_price' in values:
            return values['quantity'] * values['unit_price']
        return v

# ==================== 訂閱模型 ====================

class Subscription(BaseModel):
    """訂閱模型"""
    subscription_id: str
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    amount: Decimal
    currency: str = "TWD"
    billing_cycle: str = "monthly"  # monthly, yearly, weekly
    start_date: datetime
    end_date: Optional[datetime] = None
    next_billing_date: datetime
    trial_end_date: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# ==================== 退款模型 ====================

class RefundRequest(BaseModel):
    """退款請求模型"""
    refund_id: str
    transaction_id: str
    user_id: str
    amount: Decimal
    currency: str = "TWD"
    reason: str
    status: RefundStatus
    requested_at: datetime
    processed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# ==================== 財務報表模型 ====================

class FinancialReport(BaseModel):
    """財務報表模型"""
    report_id: str
    report_type: str  # revenue, expense, profit_loss, cash_flow
    period_start: datetime
    period_end: datetime
    data: Dict[str, Any]
    generated_at: datetime
    generated_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RevenueAnalysis(BaseModel):
    """收入分析模型"""
    period_start: datetime
    period_end: datetime
    total_revenue: Decimal
    subscription_revenue: Decimal
    one_time_revenue: Decimal
    revenue_by_source: Dict[str, Decimal] = {}
    monthly_trends: List[Dict[str, Any]] = []
    growth_rate: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

class ExpenseAnalysis(BaseModel):
    """支出分析模型"""
    period_start: datetime
    period_end: datetime
    total_expenses: Decimal
    expense_by_category: Dict[str, Decimal] = {}
    monthly_trends: List[Dict[str, Any]] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# ==================== 財務指標模型 ====================

class FinancialMetrics(BaseModel):
    """財務指標模型"""
    period: str
    total_revenue: Decimal
    total_expenses: Decimal
    net_profit: Decimal
    gross_margin: float
    net_margin: float
    customer_acquisition_cost: Decimal
    customer_lifetime_value: Decimal
    monthly_recurring_revenue: Decimal
    annual_recurring_revenue: Decimal
    churn_rate: float
    revenue_growth_rate: float
    cash_flow: Decimal
    burn_rate: Decimal
    runway_months: int
    active_subscriptions: int
    average_revenue_per_user: Decimal
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ==================== 預算模型 ====================

class Budget(BaseModel):
    """預算模型"""
    budget_id: str
    name: str
    description: Optional[str] = None
    category: str
    amount: Decimal
    currency: str = "TWD"
    period_start: datetime
    period_end: datetime
    status: str = "active"
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# ==================== 財務預測模型 ====================

class FinancialForecast(BaseModel):
    """財務預測模型"""
    forecast_id: str
    forecast_months: int
    monthly_forecasts: List[Dict[str, Any]]
    assumptions: Dict[str, float] = {}
    scenarios: Dict[str, Dict[str, float]] = {}
    confidence_level: float = 0.8
    generated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 稅務模型 ====================

class TaxRecord(BaseModel):
    """稅務記錄模型"""
    tax_record_id: str
    period_start: datetime
    period_end: datetime
    gross_income: Decimal
    deductible_expenses: Decimal
    taxable_income: Decimal
    business_tax: Decimal  # 營業稅
    income_tax: Decimal    # 營所稅
    total_tax: Decimal
    currency: str = "TWD"
    status: str = "calculated"
    calculated_at: datetime
    filed_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# ==================== 支付網關模型 ====================

class PaymentGateway(BaseModel):
    """支付網關模型"""
    gateway_id: str
    name: str
    provider: str  # stripe, paypal, payuni, etc.
    is_active: bool = True
    configuration: Dict[str, Any] = {}
    supported_methods: List[PaymentMethod] = []
    supported_currencies: List[str] = ["TWD"]
    transaction_fee_rate: Decimal = Decimal('0.029')  # 2.9%
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        }

# ==================== 請求響應模型 ====================

class FinancialSummaryRequest(BaseModel):
    """財務摘要請求模型"""
    start_date: datetime
    end_date: datetime
    include_forecasts: bool = False
    include_comparisons: bool = False
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('結束日期必須晚於開始日期')
        return v

class FinancialSummaryResponse(BaseModel):
    """財務摘要響應模型"""
    period_start: datetime
    period_end: datetime
    revenue_summary: RevenueAnalysis
    expense_summary: ExpenseAnalysis
    key_metrics: FinancialMetrics
    forecasts: Optional[FinancialForecast] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }