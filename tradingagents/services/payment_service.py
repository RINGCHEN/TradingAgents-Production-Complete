#!/usr/bin/env python3
"""
支付服務 - PayUni整合優化版
TradingAgents天工團隊增強實現
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from ..models.payment import PaymentTransaction, PaymentStatus
from ..models.subscription import Subscription, SubscriptionStatus
from ..models.user import User
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class PaymentTransactionService:
    """支付交易服務 - 企業級實現"""
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
    
    def create_transaction(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建支付交易
        
        Args:
            payment_data: 支付數據包含所有必要信息
            
        Returns:
            Dict包含交易創建結果
        """
        try:
            # 驗證必要字段
            required_fields = ['user_id', 'amount', 'currency', 'payment_method']
            for field in required_fields:
                if field not in payment_data:
                    raise ValueError(f"缺少必要字段: {field}")
            
            # 創建交易記錄
            transaction = PaymentTransaction(
                user_id=payment_data['user_id'],
                subscription_id=payment_data.get('subscription_id'),
                amount=Decimal(str(payment_data['amount'])),
                currency=payment_data['currency'],
                payment_method=payment_data['payment_method'],
                status=PaymentStatus.PENDING,
                payuni_trade_no=payment_data.get('payuni_trade_no'),
                idempotency_key=payment_data.get('idempotency_key'),
                extra_data=payment_data.get('metadata', {}),
                created_at=datetime.utcnow()
            )
            
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
            
            self.logger.info(f"支付交易創建成功: {transaction.id} (金額: {payment_data['amount']})")
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "transaction": {
                    "id": transaction.id,
                    "user_id": transaction.user_id,
                    "amount": float(transaction.amount),
                    "currency": transaction.currency,
                    "status": transaction.status.value,
                    "created_at": transaction.created_at.isoformat()
                }
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"支付交易創建失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "TRANSACTION_CREATE_FAILED"
            }
    
    def update_transaction_status(self, 
                                trade_no: str, 
                                status: str, 
                                payment_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        更新交易狀態 - PayUni回調處理
        
        Args:
            trade_no: PayUni交易號
            status: 新的支付狀態
            payment_data: PayUni返回的支付數據
            
        Returns:
            Dict包含更新結果
        """
        try:
            # 查找交易
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.payuni_trade_no == trade_no
            ).first()
            
            if not transaction:
                return {
                    "success": False,
                    "error": f"找不到交易: {trade_no}",
                    "error_code": "TRANSACTION_NOT_FOUND"
                }
            
            # 防止重複處理
            if transaction.status != PaymentStatus.PENDING:
                self.logger.warning(f"交易狀態已更新: {trade_no} -> {transaction.status.value}")
                return {
                    "success": True,
                    "already_processed": True,
                    "current_status": transaction.status.value
                }
            
            # 更新交易狀態
            old_status = transaction.status
            transaction.status = PaymentStatus(status)
            transaction.paid_at = datetime.utcnow() if status == 'completed' else None
            
            # 更新PayUni相關數據
            if payment_data:
                transaction.payuni_response = payment_data
                transaction.payment_type = payment_data.get('PaymentType', '')
                if 'PayTime' in payment_data:
                    try:
                        transaction.paid_at = datetime.strptime(
                            payment_data['PayTime'], 
                            '%Y-%m-%d %H:%M:%S'
                        )
                    except:
                        transaction.paid_at = datetime.utcnow()
            
            self.db.commit()
            
            # 如果支付成功，處理訂閱激活
            if status == 'completed' and transaction.subscription_id:
                self._activate_subscription(transaction)
            
            self.logger.info(f"支付狀態更新成功: {trade_no} ({old_status.value} -> {status})")
            
            return {
                "success": True,
                "transaction_id": transaction.id,
                "old_status": old_status.value,
                "new_status": status,
                "subscription_activated": bool(transaction.subscription_id and status == 'completed')
            }
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"支付狀態更新失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "STATUS_UPDATE_FAILED"
            }
    
    def _activate_subscription(self, transaction: PaymentTransaction):
        """激活訂閱服務"""
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == transaction.subscription_id
            ).first()
            
            if subscription:
                # 計算訂閱期間
                start_date = datetime.utcnow()
                if subscription.billing_cycle == 'monthly':
                    end_date = start_date + timedelta(days=30)
                elif subscription.billing_cycle == 'yearly':
                    end_date = start_date + timedelta(days=365)
                else:
                    end_date = start_date + timedelta(days=30)  # 默認月訂閱
                
                # 更新訂閱狀態
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.current_period_start = start_date
                subscription.current_period_end = end_date
                subscription.activated_at = datetime.utcnow()
                
                self.db.commit()
                
                self.logger.info(f"訂閱激活成功: {subscription.id} (用戶: {transaction.user_id})")
                
        except Exception as e:
            self.logger.error(f"訂閱激活失敗: {str(e)}")
            # 不影響支付成功的主要流程
    
    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """獲取交易詳細信息"""
        try:
            transaction = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.id == transaction_id
            ).first()
            
            if not transaction:
                return {
                    "success": False,
                    "error": "交易不存在",
                    "error_code": "TRANSACTION_NOT_FOUND"
                }
            
            return {
                "success": True,
                "transaction": {
                    "id": transaction.id,
                    "user_id": transaction.user_id,
                    "subscription_id": transaction.subscription_id,
                    "amount": float(transaction.amount),
                    "currency": transaction.currency,
                    "payment_method": transaction.payment_method,
                    "status": transaction.status.value,
                    "payuni_trade_no": transaction.payuni_trade_no,
                    "payment_type": transaction.payment_type,
                    "created_at": transaction.created_at.isoformat(),
                    "paid_at": transaction.paid_at.isoformat() if transaction.paid_at else None,
                    "extra_data": transaction.extra_data or {}
                }
            }
            
        except Exception as e:
            self.logger.error(f"獲取交易信息失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "TRANSACTION_FETCH_FAILED"
            }
    
    def get_user_transactions(self, 
                            user_id: int, 
                            status: Optional[str] = None,
                            limit: int = 50) -> Dict[str, Any]:
        """獲取用戶交易記錄"""
        try:
            query = self.db.query(PaymentTransaction).filter(
                PaymentTransaction.user_id == user_id
            )
            
            if status:
                query = query.filter(PaymentTransaction.status == PaymentStatus(status))
            
            transactions = query.order_by(
                PaymentTransaction.created_at.desc()
            ).limit(limit).all()
            
            return {
                "success": True,
                "transactions": [
                    {
                        "id": t.id,
                        "amount": float(t.amount),
                        "currency": t.currency,
                        "status": t.status.value,
                        "payment_method": t.payment_method,
                        "created_at": t.created_at.isoformat(),
                        "paid_at": t.paid_at.isoformat() if t.paid_at else None
                    }
                    for t in transactions
                ],
                "total_count": len(transactions)
            }
            
        except Exception as e:
            self.logger.error(f"獲取用戶交易記錄失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "USER_TRANSACTIONS_FETCH_FAILED"
            }
    
    def get_payment_analytics(self, 
                            start_date: datetime, 
                            end_date: datetime) -> Dict[str, Any]:
        """獲取支付分析數據"""
        try:
            # 總交易統計
            total_transactions = self.db.query(PaymentTransaction).filter(
                and_(
                    PaymentTransaction.created_at >= start_date,
                    PaymentTransaction.created_at <= end_date
                )
            ).count()
            
            # 成功支付統計
            successful_payments = self.db.query(PaymentTransaction).filter(
                and_(
                    PaymentTransaction.created_at >= start_date,
                    PaymentTransaction.created_at <= end_date,
                    PaymentTransaction.status == PaymentStatus.COMPLETED
                )
            ).all()
            
            successful_count = len(successful_payments)
            total_revenue = sum(float(p.amount) for p in successful_payments)
            
            # 成功率計算
            success_rate = (successful_count / total_transactions * 100) if total_transactions > 0 else 0
            
            return {
                "success": True,
                "analytics": {
                    "period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "transactions": {
                        "total_count": total_transactions,
                        "successful_count": successful_count,
                        "success_rate": round(success_rate, 2)
                    },
                    "revenue": {
                        "total_amount": total_revenue,
                        "currency": "TWD",
                        "average_amount": total_revenue / successful_count if successful_count > 0 else 0
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"支付分析數據獲取失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "ANALYTICS_FETCH_FAILED"
            }