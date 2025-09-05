#!/usr/bin/env python3
"""
支付相關數據模型
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class PaymentStatus(Enum):
    """支付狀態枚舉"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIAL_REFUNDED = "partial_refunded"


class PaymentMethod(Enum):
    """支付方式枚舉"""
    PAYUNI = "payuni"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"


class Payment(Base):
    """支付記錄模型"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="TWD")
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    
    # 會員相關
    tier_type = Column(String(20), nullable=True)
    duration_months = Column(Integer, nullable=True)
    
    # 閘道相關
    gateway_data = Column(JSON, nullable=True)
    gateway_response = Column(JSON, nullable=True)
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    paid_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Payment(id={self.id}, order_number='{self.order_number}', amount={self.amount}, status='{self.status}')>"


class PaymentTransaction(Base):
    """支付交易模型 - PayUni 整合專用"""
    __tablename__ = "payment_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    subscription_id = Column(Integer, nullable=True, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="TWD")
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    
    # PayUni 專用字段
    payuni_trade_no = Column(String(100), nullable=True, unique=True, index=True)
    payuni_response = Column(JSON, nullable=True)
    payment_type = Column(String(50), nullable=True)
    
    # 交易管理
    idempotency_key = Column(String(100), nullable=True, unique=True, index=True)
    extra_data = Column(JSON, nullable=True)  # 避免使用保留字 metadata
    
    # 時間戳
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    paid_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<PaymentTransaction(id={self.id}, payuni_trade_no='{self.payuni_trade_no}', amount={self.amount}, status='{self.status}')>"