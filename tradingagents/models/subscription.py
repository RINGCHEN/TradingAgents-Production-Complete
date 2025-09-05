#!/usr/bin/env python3
"""
訂閱管理數據模型
不老傳說 系統的訂閱和續費管理
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, JSON, Numeric, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
import uuid

Base = declarative_base()

class SubscriptionStatus(str, Enum):
    """訂閱狀態"""
    ACTIVE = "active"           # 有效訂閱
    INACTIVE = "inactive"       # 無效訂閱
    EXPIRED = "expired"         # 已過期
    CANCELED = "canceled"       # 已取消
    SUSPENDED = "suspended"     # 暫停
    PENDING = "pending"         # 待激活
    TRIAL = "trial"            # 試用期

class BillingCycle(str, Enum):
    """計費週期"""
    MONTHLY = "monthly"         # 月付
    QUARTERLY = "quarterly"     # 季付
    YEARLY = "yearly"          # 年付
    LIFETIME = "lifetime"      # 終身

class RenewalType(str, Enum):
    """續費類型"""
    AUTO = "auto"              # 自動續費
    MANUAL = "manual"          # 手動續費
    CANCELED = "canceled"      # 已取消續費

class TierType(str, Enum):
    """會員等級類型"""
    FREE = "FREE"
    GOLD = "GOLD"
    DIAMOND = "DIAMOND"

# SQLAlchemy 數據庫模型
class Subscription(Base):
    """訂閱記錄表"""
    __tablename__ = "subscriptions"

    # 基本信息
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # 訂閱詳情
    tier_type = Column(SQLEnum(TierType), nullable=False)
    billing_cycle = Column(SQLEnum(BillingCycle), nullable=False)
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.PENDING)
    
    # 時間管理
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    trial_end_date = Column(DateTime, nullable=True)  # 試用期結束時間
    
    # 續費設置
    renewal_type = Column(SQLEnum(RenewalType), default=RenewalType.AUTO)
    auto_renewal = Column(Boolean, default=True)
    renewal_reminder_sent = Column(Boolean, default=False)
    
    # 價格信息
    original_price = Column(Numeric(10, 2), nullable=False)  # 原價
    discount_amount = Column(Numeric(10, 2), default=0)     # 折扣金額
    final_price = Column(Numeric(10, 2), nullable=False)    # 實付金額
    currency = Column(String(3), default="TWD")             # 貨幣
    
    # 促銷信息
    promo_code = Column(String(50), nullable=True)          # 促銷代碼
    discount_percentage = Column(Numeric(5, 2), default=0)   # 折扣百分比
    
    # 取消信息
    canceled_at = Column(DateTime, nullable=True)
    cancelation_reason = Column(Text, nullable=True)
    canceled_by_user = Column(Boolean, default=True)
    
    # 試用期信息
    is_trial = Column(Boolean, default=False)
    trial_days = Column(Integer, default=0)
    trial_converted = Column(Boolean, default=False)
    
    # 配額和權限
    daily_api_quota = Column(Integer, nullable=False)
    monthly_api_quota = Column(Integer, nullable=False)
    features = Column(JSON, default=dict)
    
    # 系統字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 外鍵關係
    # user = relationship("User", back_populates="subscriptions")
    # payments = relationship("Payment", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier_type}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """檢查訂閱是否有效"""
        return (
            self.status == SubscriptionStatus.ACTIVE and 
            self.end_date > datetime.utcnow()
        )

    @property
    def is_expired(self) -> bool:
        """檢查訂閱是否已過期"""
        return self.end_date <= datetime.utcnow()

    @property
    def days_remaining(self) -> int:
        """獲取剩餘天數"""
        if self.is_expired:
            return 0
        return (self.end_date - datetime.utcnow()).days

    @property
    def is_trial_active(self) -> bool:
        """檢查試用期是否有效"""
        if not self.is_trial or not self.trial_end_date:
            return False
        return self.trial_end_date > datetime.utcnow()

    @property
    def trial_days_remaining(self) -> int:
        """獲取試用期剩餘天數"""
        if not self.is_trial_active:
            return 0
        return (self.trial_end_date - datetime.utcnow()).days

    def extend_subscription(self, days: int):
        """延長訂閱期限"""
        self.end_date += timedelta(days=days)
        self.updated_at = datetime.utcnow()

    def cancel_subscription(self, reason: str = None, by_user: bool = True):
        """取消訂閱"""
        self.status = SubscriptionStatus.CANCELED
        self.canceled_at = datetime.utcnow()
        self.cancelation_reason = reason
        self.canceled_by_user = by_user
        self.auto_renewal = False
        self.updated_at = datetime.utcnow()

    def reactivate_subscription(self):
        """重新激活訂閱"""
        if self.is_expired:
            return False
        self.status = SubscriptionStatus.ACTIVE
        self.canceled_at = None
        self.cancelation_reason = None
        self.updated_at = datetime.utcnow()
        return True

class SubscriptionHistory(Base):
    """訂閱歷史記錄表"""
    __tablename__ = "subscription_history"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 變更信息
    action = Column(String(50), nullable=False)  # created, renewed, canceled, upgraded, downgraded
    from_tier = Column(SQLEnum(TierType), nullable=True)
    to_tier = Column(SQLEnum(TierType), nullable=True)
    from_status = Column(SQLEnum(SubscriptionStatus), nullable=True)
    to_status = Column(SQLEnum(SubscriptionStatus), nullable=True)
    
    # 詳情
    reason = Column(Text, nullable=True)
    meta_data = Column(JSON, default=dict)
    
    # 系統字段
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SubscriptionHistory(id={self.id}, action='{self.action}')>"

class TrialPeriod(Base):
    """試用期管理表"""
    __tablename__ = "trial_periods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    tier_type = Column(SQLEnum(TierType), nullable=False)
    
    # 試用期設置
    trial_days = Column(Integer, default=14)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    
    # 狀態
    is_active = Column(Boolean, default=True)
    is_converted = Column(Boolean, default=False)  # 是否轉為付費
    converted_at = Column(DateTime, nullable=True)
    
    # 使用統計
    api_calls_used = Column(Integer, default=0)
    analyses_performed = Column(Integer, default=0)
    
    # 系統字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TrialPeriod(user_id={self.user_id}, tier='{self.tier_type}')>"

    @property
    def is_trial_active(self) -> bool:
        """檢查試用期是否有效"""
        return self.is_active and self.end_date > datetime.utcnow()

    @property
    def days_remaining(self) -> int:
        """獲取試用期剩餘天數"""
        if not self.is_trial_active:
            return 0
        return (self.end_date - datetime.utcnow()).days

# Pydantic 數據傳輸對象
class SubscriptionBase(BaseModel):
    """訂閱基礎信息"""
    tier_type: TierType
    billing_cycle: BillingCycle
    start_date: datetime
    end_date: datetime
    auto_renewal: bool = True
    original_price: Decimal
    discount_amount: Decimal = Decimal("0.00")
    final_price: Decimal
    currency: str = "TWD"

class SubscriptionCreate(BaseModel):
    """創建訂閱請求"""
    user_id: int
    tier_type: TierType
    billing_cycle: BillingCycle
    promo_code: Optional[str] = None
    auto_renewal: bool = True
    is_trial: bool = False
    trial_days: int = 0

class SubscriptionUpdate(BaseModel):
    """更新訂閱請求"""
    tier_type: Optional[TierType] = None
    billing_cycle: Optional[BillingCycle] = None
    auto_renewal: Optional[bool] = None
    renewal_type: Optional[RenewalType] = None

class SubscriptionResponse(SubscriptionBase):
    """訂閱響應數據"""
    id: int
    uuid: str
    user_id: int
    status: SubscriptionStatus
    renewal_type: RenewalType
    is_trial: bool
    trial_days: int
    trial_end_date: Optional[datetime] = None
    days_remaining: int
    is_active: bool
    is_expired: bool
    daily_api_quota: int
    monthly_api_quota: int
    features: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TrialPeriodResponse(BaseModel):
    """試用期響應數據"""
    id: int
    user_id: int
    tier_type: TierType
    trial_days: int
    start_date: datetime
    end_date: datetime
    is_active: bool
    is_converted: bool
    days_remaining: int
    is_trial_active: bool
    api_calls_used: int
    analyses_performed: int
    created_at: datetime

    class Config:
        from_attributes = True

class SubscriptionStats(BaseModel):
    """訂閱統計信息"""
    total_subscriptions: int
    active_subscriptions: int
    trial_subscriptions: int
    expired_subscriptions: int
    canceled_subscriptions: int
    revenue_this_month: Decimal
    revenue_this_year: Decimal
    churn_rate: float
    conversion_rate: float

class RenewalReminder(BaseModel):
    """續費提醒"""
    subscription_id: int
    user_id: int
    tier_type: TierType
    end_date: datetime
    days_until_expiry: int
    renewal_price: Decimal
    auto_renewal_enabled: bool

# 訂閱配置常量
SUBSCRIPTION_CONFIGS = {
    TierType.FREE: {
        "monthly_price": Decimal("0.00"),
        "yearly_price": Decimal("0.00"),
        "trial_days": 0,
        "daily_api_quota": 100,
        "monthly_api_quota": 3000
    },
    TierType.GOLD: {
        "monthly_price": Decimal("299.00"),
        "quarterly_price": Decimal("799.00"),
        "yearly_price": Decimal("2999.00"),
        "trial_days": 14,
        "daily_api_quota": 1000,
        "monthly_api_quota": 30000
    },
    TierType.DIAMOND: {
        "monthly_price": Decimal("999.00"),
        "quarterly_price": Decimal("2699.00"),
        "yearly_price": Decimal("9999.00"),
        "trial_days": 7,
        "daily_api_quota": -1,  # 無限制
        "monthly_api_quota": -1  # 無限制
    }
}

def calculate_subscription_price(tier_type: TierType, billing_cycle: BillingCycle, promo_code: str = None) -> Dict[str, Decimal]:
    """計算訂閱價格"""
    config = SUBSCRIPTION_CONFIGS.get(tier_type, SUBSCRIPTION_CONFIGS[TierType.FREE])
    
    if billing_cycle == BillingCycle.MONTHLY:
        original_price = config["monthly_price"]
    elif billing_cycle == BillingCycle.QUARTERLY:
        original_price = config.get("quarterly_price", config["monthly_price"] * 3)
    elif billing_cycle == BillingCycle.YEARLY:
        original_price = config.get("yearly_price", config["monthly_price"] * 12)
    else:
        original_price = Decimal("0.00")
    
    # 應用促銷代碼折扣
    discount_amount = Decimal("0.00")
    if promo_code:
        discount_amount = apply_promo_discount(original_price, promo_code)
    
    final_price = original_price - discount_amount
    
    return {
        "original_price": original_price,
        "discount_amount": discount_amount,
        "final_price": final_price
    }

def apply_promo_discount(original_price: Decimal, promo_code: str) -> Decimal:
    """應用促銷代碼折扣"""
    promo_discounts = {
        "WELCOME50": Decimal("0.50"),  # 50% 折扣
        "NEWUSER": Decimal("0.30"),    # 30% 折扣
        "SAVE20": Decimal("0.20"),     # 20% 折扣
        "FIRST100": Decimal("100.00")  # 減免100元
    }
    
    if promo_code in promo_discounts:
        discount = promo_discounts[promo_code]
        if discount < 1:  # 百分比折扣
            return original_price * discount
        else:  # 固定金額折扣
            return min(discount, original_price)
    
    return Decimal("0.00")

def get_next_billing_date(current_date: datetime, billing_cycle: BillingCycle) -> datetime:
    """獲取下次計費日期"""
    if billing_cycle == BillingCycle.MONTHLY:
        return current_date + timedelta(days=30)
    elif billing_cycle == BillingCycle.QUARTERLY:
        return current_date + timedelta(days=90)
    elif billing_cycle == BillingCycle.YEARLY:
        return current_date + timedelta(days=365)
    else:
        return current_date

def create_trial_subscription(user_id: int, tier_type: TierType) -> Dict[str, Any]:
    """創建試用訂閱"""
    config = SUBSCRIPTION_CONFIGS.get(tier_type, SUBSCRIPTION_CONFIGS[TierType.GOLD])
    trial_days = config.get("trial_days", 14)
    
    start_date = datetime.utcnow()
    trial_end_date = start_date + timedelta(days=trial_days)
    
    return {
        "user_id": user_id,
        "tier_type": tier_type,
        "billing_cycle": BillingCycle.MONTHLY,
        "status": SubscriptionStatus.TRIAL,
        "start_date": start_date,
        "end_date": trial_end_date,
        "trial_end_date": trial_end_date,
        "is_trial": True,
        "trial_days": trial_days,
        "original_price": Decimal("0.00"),
        "final_price": Decimal("0.00"),
        "daily_api_quota": config["daily_api_quota"],
        "monthly_api_quota": config["monthly_api_quota"]
    }