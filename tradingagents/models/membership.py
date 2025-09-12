#!/usr/bin/env python3
"""
會員相關數據模型
"""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TierType(Enum):
    """會員等級枚舉"""
    # Tiers used by the permission system and other new logic
    FREE = "free"
    GOLD = "gold"
    DIAMOND = "diamond"
    
    # Legacy or alternative tiers
    BASIC = "basic"
    PREMIUM = "premium"
    VIP = "vip"
    ENTERPRISE = "enterprise"


class MembershipTier(Base):
    """會員等級模型"""
    __tablename__ = "membership_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tier_type = Column(String(20), nullable=False)
    
    # 時間相關
    start_date = Column(DateTime, nullable=False)
    expire_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<MembershipTier(id={self.id}, user_id={self.user_id}, tier_type='{self.tier_type}', expire_date='{self.expire_date}')>"