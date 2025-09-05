#!/usr/bin/env python3
"""
用戶數據模型
不老傳說 系統的核心用戶管理模型
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr
import uuid

Base = declarative_base()

class UserStatus(str, Enum):
    """用戶狀態枚舉"""
    ACTIVE = "active"           # 活躍用戶
    INACTIVE = "inactive"       # 非活躍用戶  
    SUSPENDED = "suspended"     # 暫停使用
    DELETED = "deleted"         # 已刪除

class MembershipTier(str, Enum):
    """會員等級枚舉"""
    FREE = "FREE"               # 免費會員
    GOLD = "GOLD"               # 黃金會員
    DIAMOND = "DIAMOND"         # 鑽石會員

class AuthProvider(str, Enum):
    """認證提供者枚舉"""
    GOOGLE = "google"           # Google OAuth
    EMAIL = "email"             # 電子郵件註冊
    FACEBOOK = "facebook"       # Facebook OAuth (未來支持)
    LINE = "line"               # LINE OAuth (未來支持)

# SQLAlchemy 數據庫模型
class User(Base):
    """用戶主表"""
    __tablename__ = "users"

    # 基本信息
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True)
    display_name = Column(String(100))
    
    # 認證信息
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.EMAIL)
    google_id = Column(String(100), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=True)  # OAuth 用戶可為空
    email_verified = Column(Boolean, default=False)
    
    # 會員信息
    membership_tier = Column(SQLEnum(MembershipTier), default=MembershipTier.FREE)
    status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE)
    
    # 配額管理
    daily_api_quota = Column(Integer, default=100)  # 每日 API 配額
    monthly_api_quota = Column(Integer, default=3000)  # 每月 API 配額
    api_calls_today = Column(Integer, default=0)
    api_calls_month = Column(Integer, default=0)
    last_api_reset = Column(DateTime, default=datetime.utcnow)
    
    # 個人資料
    avatar_url = Column(String(500))
    phone = Column(String(20))
    country = Column(String(2))  # ISO 國家代碼
    timezone = Column(String(50), default="Asia/Taipei")
    language = Column(String(5), default="zh-TW")
    
    # 偏好設置
    preferences = Column(JSON, default=dict)  # 用戶偏好設置
    notification_settings = Column(JSON, default=dict)  # 通知設置
    
    # 使用統計
    total_analyses = Column(Integer, default=0)  # 總分析次數
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)
    
    # 系統字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # 外鍵關係 (稍後實現)
    # subscriptions = relationship("Subscription", back_populates="user")
    # payments = relationship("Payment", back_populates="user")
    # dialogue_histories = relationship("DialogueHistory", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tier='{self.membership_tier}')>"

    @property
    def is_premium(self) -> bool:
        """檢查是否為付費會員"""
        return self.membership_tier in [MembershipTier.GOLD, MembershipTier.DIAMOND]

    @property
    def api_quota_remaining_today(self) -> int:
        """獲取今日剩餘 API 配額"""
        return max(0, self.daily_api_quota - self.api_calls_today)

    @property
    def api_quota_remaining_month(self) -> int:
        """獲取本月剩餘 API 配額"""
        return max(0, self.monthly_api_quota - self.api_calls_month)

    def reset_daily_quota(self):
        """重置每日配額"""
        self.api_calls_today = 0
        self.last_api_reset = datetime.utcnow()

    def reset_monthly_quota(self):
        """重置每月配額"""
        self.api_calls_month = 0

    def can_make_api_call(self) -> bool:
        """檢查是否還能進行 API 調用"""
        return self.api_quota_remaining_today > 0 and self.api_quota_remaining_month > 0

    def increment_api_usage(self):
        """增加 API 使用次數"""
        self.api_calls_today += 1
        self.api_calls_month += 1

# Pydantic 數據傳輸對象
class UserBase(BaseModel):
    """用戶基礎信息"""
    email: EmailStr
    username: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: str = "Asia/Taipei"
    language: str = "zh-TW"

class UserCreate(UserBase):
    """創建用戶請求"""
    password: Optional[str] = None
    auth_provider: AuthProvider = AuthProvider.EMAIL
    google_id: Optional[str] = None

class UserUpdate(BaseModel):
    """更新用戶請求"""
    username: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None
    notification_settings: Optional[dict] = None

class UserResponse(UserBase):
    """用戶響應數據"""
    id: int
    uuid: str
    membership_tier: MembershipTier
    status: UserStatus
    auth_provider: AuthProvider
    email_verified: bool
    avatar_url: Optional[str] = None
    daily_api_quota: int
    api_calls_today: int
    api_quota_remaining_today: int
    total_analyses: int
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserStats(BaseModel):
    """用戶統計信息"""
    user_id: int
    total_analyses: int
    api_calls_today: int
    api_calls_month: int
    daily_quota_remaining: int
    monthly_quota_remaining: int
    membership_tier: MembershipTier
    member_since: datetime
    last_active: Optional[datetime] = None

class QuotaInfo(BaseModel):
    """配額信息"""
    daily_quota: int
    daily_used: int
    daily_remaining: int
    monthly_quota: int
    monthly_used: int
    monthly_remaining: int
    can_make_call: bool
    next_reset: datetime

# 會員等級配額配置
MEMBERSHIP_QUOTAS = {
    MembershipTier.FREE: {
        "daily_api_quota": 100,
        "monthly_api_quota": 3000,
        "max_concurrent_analyses": 1,
        "priority_support": False,
        "advanced_features": False,
        "export_formats": ["json"],
        "data_retention_days": 30
    },
    MembershipTier.GOLD: {
        "daily_api_quota": 1000,
        "monthly_api_quota": 30000,
        "max_concurrent_analyses": 3,
        "priority_support": True,
        "advanced_features": True,
        "export_formats": ["json", "csv", "excel"],
        "data_retention_days": 90
    },
    MembershipTier.DIAMOND: {
        "daily_api_quota": -1,  # 無限制
        "monthly_api_quota": -1,  # 無限制
        "max_concurrent_analyses": 10,
        "priority_support": True,
        "advanced_features": True,
        "export_formats": ["json", "csv", "excel", "pdf"],
        "data_retention_days": 365
    }
}

def get_membership_benefits(tier: MembershipTier) -> dict:
    """獲取會員等級權益"""
    return MEMBERSHIP_QUOTAS.get(tier, MEMBERSHIP_QUOTAS[MembershipTier.FREE])

def upgrade_user_quotas(user: User, new_tier: MembershipTier):
    """升級用戶配額"""
    benefits = get_membership_benefits(new_tier)
    user.membership_tier = new_tier
    user.daily_api_quota = benefits["daily_api_quota"]
    user.monthly_api_quota = benefits["monthly_api_quota"]
    user.updated_at = datetime.utcnow()