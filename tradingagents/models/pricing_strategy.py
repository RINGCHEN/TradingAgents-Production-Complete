"""
多層次定價策略數據模型
Task 5.3 - 多層次定價策略實現
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional, List
import uuid

Base = declarative_base()

class PricingTier(Enum):
    """定價層級枚舉"""
    BASIC = "basic"           # 基礎版
    STANDARD = "standard"     # 標準版
    PREMIUM = "premium"       # 高級版
    ENTERPRISE = "enterprise" # 企業版

class DiscountType(Enum):
    """折扣類型枚舉"""
    PERCENTAGE = "percentage"  # 百分比折扣
    FIXED_AMOUNT = "fixed_amount"  # 固定金額折扣
    FREE_TRIAL = "free_trial"  # 免費試用
    UPGRADE_BONUS = "upgrade_bonus"  # 升級獎勵

class CouponStatus(Enum):
    """優惠券狀態枚舉"""
    ACTIVE = "active"         # 有效
    EXPIRED = "expired"       # 已過期
    USED = "used"            # 已使用
    DISABLED = "disabled"     # 已禁用

class PricingPlan(Base):
    """定價方案表"""
    __tablename__ = 'pricing_plans'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, comment="方案名稱")
    tier = Column(String(50), nullable=False, comment="定價層級")
    
    # 價格信息
    monthly_price = Column(Float, nullable=False, comment="月付價格")
    yearly_price = Column(Float, comment="年付價格")
    original_price = Column(Float, comment="原價（用於顯示折扣）")
    
    # 方案特性
    features = Column(JSON, comment="功能特性列表")
    limitations = Column(JSON, comment="使用限制")
    
    # 顯示配置
    is_recommended = Column(Boolean, default=False, comment="是否推薦方案")
    is_popular = Column(Boolean, default=False, comment="是否熱門方案")
    display_order = Column(Integer, default=0, comment="顯示順序")
    
    # 價格錨定
    anchor_price = Column(Float, comment="錨定價格（用於對比）")
    savings_highlight = Column(String(255), comment="節省金額提示")
    
    # 狀態信息
    is_active = Column(Boolean, default=True, comment="是否啟用")
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新時間")
    
    # 關聯關係
    dynamic_pricing_rules = relationship("DynamicPricingRule", back_populates="plan")
    coupons = relationship("CouponCode", back_populates="applicable_plans", secondary="coupon_plan_association")

class DynamicPricingRule(Base):
    """動態定價規則表"""
    __tablename__ = 'dynamic_pricing_rules'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey('pricing_plans.id'), nullable=False)
    
    # 規則信息
    name = Column(String(255), nullable=False, comment="規則名稱")
    description = Column(Text, comment="規則描述")
    
    # 觸發條件
    trigger_conditions = Column(JSON, nullable=False, comment="觸發條件")
    user_segments = Column(JSON, comment="適用用戶群體")
    
    # 定價調整
    price_adjustment_type = Column(String(50), comment="調整類型：percentage/fixed/override")
    price_adjustment_value = Column(Float, comment="調整值")
    adjusted_price = Column(Float, comment="調整後價格")
    
    # 時間限制
    start_date = Column(DateTime, comment="開始時間")
    end_date = Column(DateTime, comment="結束時間")
    
    # 使用限制
    max_uses = Column(Integer, comment="最大使用次數")
    current_uses = Column(Integer, default=0, comment="當前使用次數")
    
    # 狀態信息
    is_active = Column(Boolean, default=True, comment="是否啟用")
    priority = Column(Integer, default=0, comment="優先級")
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    
    # 關聯關係
    plan = relationship("PricingPlan", back_populates="dynamic_pricing_rules")

class CouponCode(Base):
    """優惠券代碼表"""
    __tablename__ = 'coupon_codes'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(50), unique=True, nullable=False, comment="優惠券代碼")
    
    # 優惠券信息
    name = Column(String(255), nullable=False, comment="優惠券名稱")
    description = Column(Text, comment="優惠券描述")
    
    # 折扣配置
    discount_type = Column(String(50), nullable=False, comment="折扣類型")
    discount_value = Column(Float, nullable=False, comment="折扣值")
    max_discount_amount = Column(Float, comment="最大折扣金額")
    min_purchase_amount = Column(Float, comment="最小購買金額")
    
    # 使用限制
    max_uses = Column(Integer, comment="最大使用次數")
    max_uses_per_user = Column(Integer, comment="每用戶最大使用次數")
    current_uses = Column(Integer, default=0, comment="當前使用次數")
    
    # 時間限制
    start_date = Column(DateTime, nullable=False, comment="開始時間")
    end_date = Column(DateTime, nullable=False, comment="結束時間")
    
    # 適用範圍
    applicable_plans = relationship("PricingPlan", secondary="coupon_plan_association", back_populates="coupons")
    user_segments = Column(JSON, comment="適用用戶群體")
    
    # 狀態信息
    status = Column(String(50), default=CouponStatus.ACTIVE.value, comment="優惠券狀態")
    is_public = Column(Boolean, default=False, comment="是否公開")
    created_by = Column(String(100), comment="創建者")
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    
    # 關聯關係
    usage_records = relationship("CouponUsage", back_populates="coupon")

# 優惠券和方案關聯表
from sqlalchemy import Table
coupon_plan_association = Table(
    'coupon_plan_association',
    Base.metadata,
    Column('coupon_id', String(36), ForeignKey('coupon_codes.id')),
    Column('plan_id', String(36), ForeignKey('pricing_plans.id'))
)

class CouponUsage(Base):
    """優惠券使用記錄表"""
    __tablename__ = 'coupon_usage'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    coupon_id = Column(String(36), ForeignKey('coupon_codes.id'), nullable=False)
    
    # 使用信息
    user_id = Column(Integer, comment="用戶ID")
    session_id = Column(String(255), comment="會話ID")
    plan_id = Column(String(36), ForeignKey('pricing_plans.id'), comment="使用的方案")
    
    # 折扣詳情
    original_price = Column(Float, nullable=False, comment="原價")
    discount_amount = Column(Float, nullable=False, comment="折扣金額")
    final_price = Column(Float, nullable=False, comment="最終價格")
    
    # 使用時間
    used_at = Column(DateTime, default=datetime.utcnow, comment="使用時間")
    
    # 訂單信息
    order_id = Column(String(255), comment="訂單ID")
    payment_status = Column(String(50), comment="支付狀態")
    
    # 關聯關係
    coupon = relationship("CouponCode", back_populates="usage_records")

class PriceComparison(Base):
    """價格對比表"""
    __tablename__ = 'price_comparisons'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 對比信息
    name = Column(String(255), nullable=False, comment="對比名稱")
    description = Column(Text, comment="對比描述")
    
    # 對比配置
    comparison_data = Column(JSON, nullable=False, comment="對比數據")
    highlight_plan_id = Column(String(36), ForeignKey('pricing_plans.id'), comment="突出顯示的方案")
    
    # 顯示配置
    display_order = Column(Integer, default=0, comment="顯示順序")
    is_active = Column(Boolean, default=True, comment="是否啟用")
    
    # 時間信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="創建時間")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新時間")

class UserPricingHistory(Base):
    """用戶定價歷史表"""
    __tablename__ = 'user_pricing_history'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 用戶信息
    user_id = Column(Integer, comment="用戶ID")
    session_id = Column(String(255), comment="會話ID")
    
    # 定價信息
    plan_id = Column(String(36), ForeignKey('pricing_plans.id'), nullable=False)
    shown_price = Column(Float, nullable=False, comment="展示價格")
    original_price = Column(Float, nullable=False, comment="原價")
    applied_rules = Column(JSON, comment="應用的規則")
    
    # 用戶行為
    viewed_at = Column(DateTime, default=datetime.utcnow, comment="查看時間")
    clicked = Column(Boolean, default=False, comment="是否點擊")
    converted = Column(Boolean, default=False, comment="是否轉換")
    
    # 上下文信息
    page_url = Column(String(500), comment="頁面URL")
    referrer = Column(String(500), comment="來源頁面")
    user_agent = Column(String(500), comment="用戶代理")

# 配置類
class PricingConfig:
    """定價配置類"""
    
    # 默認配置
    DEFAULT_TRIAL_DAYS = 7
    DEFAULT_DISCOUNT_PERCENTAGE = 10
    
    # 價格錨定策略
    ANCHOR_STRATEGIES = {
        'high_anchor': {
            'description': '高價錨定策略',
            'multiplier': 3.0,
            'highlight_savings': True
        },
        'competitor_anchor': {
            'description': '競爭對手錨定',
            'multiplier': 2.5,
            'highlight_savings': True
        },
        'value_anchor': {
            'description': '價值錨定',
            'multiplier': 2.0,
            'highlight_savings': False
        }
    }
    
    # 動態定價觸發條件
    DYNAMIC_PRICING_TRIGGERS = {
        'new_user': {
            'description': '新用戶優惠',
            'conditions': {'user_age_days': {'$lt': 1}},
            'discount': 20
        },
        'returning_user': {
            'description': '回頭客優惠',
            'conditions': {'visit_count': {'$gt': 3}},
            'discount': 15
        },
        'high_value_user': {
            'description': '高價值用戶',
            'conditions': {'engagement_score': {'$gt': 80}},
            'discount': 25
        },
        'cart_abandonment': {
            'description': '購物車放棄挽回',
            'conditions': {'cart_abandoned': True, 'hours_since_abandon': {'$gt': 24}},
            'discount': 30
        }
    }
    
    # 用戶細分
    USER_SEGMENTS = {
        'new_users': {
            'description': '新用戶',
            'conditions': {'registration_days': {'$lt': 7}}
        },
        'trial_users': {
            'description': '試用用戶',
            'conditions': {'subscription_status': 'trial'}
        },
        'premium_prospects': {
            'description': '高級版潛在客戶',
            'conditions': {'feature_usage': {'$gt': 70}}
        },
        'enterprise_prospects': {
            'description': '企業版潛在客戶',
            'conditions': {'team_size': {'$gt': 10}}
        }
    }
    
    @classmethod
    def get_default_plans(cls) -> List[Dict[str, Any]]:
        """獲取默認定價方案"""
        return [
            {
                'name': '基礎版',
                'tier': PricingTier.BASIC.value,
                'monthly_price': 99.0,
                'yearly_price': 990.0,
                'original_price': 149.0,
                'features': [
                    '5位AI分析師',
                    '每日10次分析',
                    '基礎技術指標',
                    '郵件支援'
                ],
                'limitations': {
                    'analysis_per_day': 10,
                    'analysts_count': 5,
                    'support_level': 'email'
                },
                'is_recommended': False,
                'display_order': 1
            },
            {
                'name': '標準版',
                'tier': PricingTier.STANDARD.value,
                'monthly_price': 199.0,
                'yearly_price': 1990.0,
                'original_price': 299.0,
                'features': [
                    '10位AI分析師',
                    '無限次分析',
                    '進階技術指標',
                    '即時通訊支援',
                    '投資組合追蹤'
                ],
                'limitations': {
                    'analysis_per_day': -1,  # 無限制
                    'analysts_count': 10,
                    'support_level': 'chat'
                },
                'is_recommended': True,
                'display_order': 2,
                'anchor_price': 399.0,
                'savings_highlight': '每月節省$200'
            },
            {
                'name': '高級版',
                'tier': PricingTier.PREMIUM.value,
                'monthly_price': 399.0,
                'yearly_price': 3990.0,
                'original_price': 599.0,
                'features': [
                    '20位AI分析師',
                    '無限次分析',
                    '全套技術指標',
                    '專屬客服',
                    '投資組合管理',
                    '風險評估',
                    '市場預警'
                ],
                'limitations': {
                    'analysis_per_day': -1,
                    'analysts_count': 20,
                    'support_level': 'dedicated'
                },
                'is_recommended': False,
                'is_popular': True,
                'display_order': 3,
                'anchor_price': 799.0,
                'savings_highlight': '每月節省$400'
            }
        ]
    
    @classmethod
    def get_default_coupons(cls) -> List[Dict[str, Any]]:
        """獲取默認優惠券"""
        return [
            {
                'code': 'WELCOME50',
                'name': '新用戶歡迎優惠',
                'description': '新用戶專享50%折扣',
                'discount_type': DiscountType.PERCENTAGE.value,
                'discount_value': 50.0,
                'max_uses': 1000,
                'max_uses_per_user': 1,
                'start_date': datetime.utcnow(),
                'end_date': datetime.utcnow() + timedelta(days=30),
                'user_segments': ['new_users'],
                'is_public': True
            },
            {
                'code': 'UPGRADE25',
                'name': '升級優惠',
                'description': '升級用戶25%折扣',
                'discount_type': DiscountType.PERCENTAGE.value,
                'discount_value': 25.0,
                'max_uses': 500,
                'max_uses_per_user': 1,
                'start_date': datetime.utcnow(),
                'end_date': datetime.utcnow() + timedelta(days=60),
                'user_segments': ['trial_users'],
                'is_public': False
            },
            {
                'code': 'SAVE100',
                'name': '固定折扣',
                'description': '立減$100',
                'discount_type': DiscountType.FIXED_AMOUNT.value,
                'discount_value': 100.0,
                'min_purchase_amount': 300.0,
                'max_uses': 200,
                'start_date': datetime.utcnow(),
                'end_date': datetime.utcnow() + timedelta(days=14),
                'is_public': True
            }
        ]