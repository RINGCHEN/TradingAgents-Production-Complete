"""
會員訂閱管理模型定義
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class BillingCycle(str, Enum):
    """計費週期"""
    MONTHLY = "monthly"
    YEARLY = "yearly"
    QUARTERLY = "quarterly"

class SubscriptionStatus(str, Enum):
    """訂閱狀態"""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    PENDING = "pending"

class PaymentMethod(str, Enum):
    """付款方式"""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"

class SubscriptionPlan(BaseModel):
    """訂閱方案模型"""
    id: str = Field(..., description="方案ID")
    name: str = Field(..., description="方案名稱")
    description: str = Field(..., description="方案描述")
    price: float = Field(..., description="價格")
    currency: str = Field(default="TWD", description="貨幣")
    billing_cycle: BillingCycle = Field(..., description="計費週期")
    features: List[str] = Field(default=[], description="功能列表")
    max_api_calls: int = Field(default=1000, description="API調用限制，-1表示無限制")
    max_ai_requests: int = Field(default=10, description="AI請求限制，-1表示無限制")
    is_active: bool = Field(default=True, description="是否啟用")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")

class CreateSubscriptionPlanRequest(BaseModel):
    """創建訂閱方案請求"""
    name: str = Field(..., description="方案名稱")
    description: str = Field(..., description="方案描述")
    price: float = Field(..., description="價格")
    currency: str = Field(default="TWD", description="貨幣")
    billing_cycle: BillingCycle = Field(..., description="計費週期")
    features: List[str] = Field(default=[], description="功能列表")
    max_api_calls: int = Field(default=1000, description="API調用限制")
    max_ai_requests: int = Field(default=10, description="AI請求限制")

class UpdateSubscriptionPlanRequest(BaseModel):
    """更新訂閱方案請求"""
    name: Optional[str] = Field(None, description="方案名稱")
    description: Optional[str] = Field(None, description="方案描述")
    price: Optional[float] = Field(None, description="價格")
    features: Optional[List[str]] = Field(None, description="功能列表")
    max_api_calls: Optional[int] = Field(None, description="API調用限制")
    max_ai_requests: Optional[int] = Field(None, description="AI請求限制")
    is_active: Optional[bool] = Field(None, description="是否啟用")

class UserSubscription(BaseModel):
    """用戶訂閱模型"""
    id: str = Field(..., description="訂閱ID")
    user_id: str = Field(..., description="用戶ID")
    username: str = Field(..., description="用戶名")
    email: str = Field(..., description="用戶郵箱")
    plan_id: str = Field(..., description="方案ID")
    plan_name: str = Field(..., description="方案名稱")
    status: SubscriptionStatus = Field(..., description="訂閱狀態")
    start_date: datetime = Field(..., description="開始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")
    auto_renew: bool = Field(default=False, description="自動續費")
    payment_method: Optional[PaymentMethod] = Field(None, description="付款方式")
    last_payment_date: Optional[datetime] = Field(None, description="最後付款日期")
    next_billing_date: Optional[datetime] = Field(None, description="下次計費日期")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")

class SubscriptionStats(BaseModel):
    """訂閱統計模型"""
    total_subscribers: int = Field(..., description="總訂閱用戶數")
    active_subscribers: int = Field(..., description="活躍訂閱用戶數")
    free_users: int = Field(..., description="免費用戶數")
    paid_users: int = Field(..., description="付費用戶數")
    monthly_revenue: float = Field(..., description="月收入")
    churn_rate: float = Field(..., description="流失率")
    conversion_rate: float = Field(..., description="轉換率")
    average_revenue_per_user: float = Field(..., description="平均每用戶收入")
    plan_distribution: Dict[str, int] = Field(..., description="方案分佈")
    growth_rate: float = Field(..., description="增長率")

class SubscriptionAnalytics(BaseModel):
    """訂閱分析模型"""
    period_days: int = Field(..., description="分析週期天數")
    new_subscriptions: int = Field(..., description="新增訂閱數")
    cancelled_subscriptions: int = Field(..., description="取消訂閱數")
    upgraded_subscriptions: int = Field(..., description="升級訂閱數")
    downgraded_subscriptions: int = Field(..., description="降級訂閱數")
    revenue_trend: List[Dict[str, Any]] = Field(..., description="收入趨勢")
    subscription_trend: List[Dict[str, Any]] = Field(..., description="訂閱趨勢")
    top_performing_plans: List[Dict[str, Any]] = Field(..., description="表現最佳方案")

class SubscriptionEvent(BaseModel):
    """訂閱事件模型"""
    id: str = Field(..., description="事件ID")
    subscription_id: str = Field(..., description="訂閱ID")
    event_type: str = Field(..., description="事件類型")
    event_data: Dict[str, Any] = Field(..., description="事件數據")
    created_at: datetime = Field(..., description="創建時間")

class SubscriptionUsage(BaseModel):
    """訂閱使用情況模型"""
    subscription_id: str = Field(..., description="訂閱ID")
    api_calls_used: int = Field(default=0, description="已使用API調用次數")
    ai_requests_used: int = Field(default=0, description="已使用AI請求次數")
    usage_date: datetime = Field(..., description="使用日期")
    reset_date: datetime = Field(..., description="重置日期")

class SubscriptionInvoice(BaseModel):
    """訂閱發票模型"""
    id: str = Field(..., description="發票ID")
    subscription_id: str = Field(..., description="訂閱ID")
    amount: float = Field(..., description="金額")
    currency: str = Field(..., description="貨幣")
    status: str = Field(..., description="發票狀態")
    issued_date: datetime = Field(..., description="開立日期")
    due_date: datetime = Field(..., description="到期日期")
    paid_date: Optional[datetime] = Field(None, description="付款日期")

class SubscriptionDiscount(BaseModel):
    """訂閱折扣模型"""
    id: str = Field(..., description="折扣ID")
    code: str = Field(..., description="折扣碼")
    name: str = Field(..., description="折扣名稱")
    discount_type: str = Field(..., description="折扣類型: percentage, fixed")
    discount_value: float = Field(..., description="折扣值")
    min_amount: Optional[float] = Field(None, description="最低金額")
    max_discount: Optional[float] = Field(None, description="最大折扣")
    valid_from: datetime = Field(..., description="有效開始時間")
    valid_until: datetime = Field(..., description="有效結束時間")
    usage_limit: Optional[int] = Field(None, description="使用次數限制")
    used_count: int = Field(default=0, description="已使用次數")
    is_active: bool = Field(default=True, description="是否啟用")

class SubscriptionNotification(BaseModel):
    """訂閱通知模型"""
    id: str = Field(..., description="通知ID")
    subscription_id: str = Field(..., description="訂閱ID")
    notification_type: str = Field(..., description="通知類型")
    title: str = Field(..., description="通知標題")
    message: str = Field(..., description="通知內容")
    is_sent: bool = Field(default=False, description="是否已發送")
    sent_at: Optional[datetime] = Field(None, description="發送時間")
    created_at: datetime = Field(..., description="創建時間")