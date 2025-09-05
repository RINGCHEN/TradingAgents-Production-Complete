#!/usr/bin/env python3
"""
支付管理 API 端點
TradingAgents 系統的支付處理和交易管理
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from pydantic import BaseModel

from ..models.payment import Payment, PaymentStatus, PaymentMethod
from ..models.user import User
from ..database.database import get_db
from ..auth.dependencies import get_current_user
from ..utils.logging_config import get_api_logger

logger = get_api_logger("payment_endpoints")
router = APIRouter(prefix="/payments", tags=["payments"])


# Pydantic 模型
class PaymentCreate(BaseModel):
    """創建支付請求模型"""
    user_id: int
    amount: Decimal
    currency: str = "TWD"
    payment_method: str
    tier_type: Optional[str] = None
    duration_months: Optional[int] = None


class PaymentResponse(BaseModel):
    """支付響應模型"""
    id: int
    user_id: int
    order_number: str
    amount: Decimal
    currency: str
    payment_method: str
    status: str
    tier_type: Optional[str] = None
    duration_months: Optional[int] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# 支付 CRUD 操作
@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    創建支付訂單
    用戶可為自己創建支付，管理員可為任何用戶創建
    """
    try:
        # 權限檢查
        if (payment_data.user_id != current_user.id and 
            current_user.membership_tier.value != "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限為其他用戶創建支付"
            )
        
        # 生成訂單號
        order_number = f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}{payment_data.user_id:06d}"
        
        # 創建支付記錄
        payment = Payment(
            user_id=payment_data.user_id,
            order_number=order_number,
            amount=payment_data.amount,
            currency=payment_data.currency,
            payment_method=payment_data.payment_method,
            status=PaymentStatus.PENDING.value,
            tier_type=payment_data.tier_type,
            duration_months=payment_data.duration_months,
            created_at=datetime.now()
        )
        
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        logger.info(f"創建支付訂單: {order_number}, 用戶: {payment_data.user_id}, 金額: {payment_data.amount}")
        return payment
        
    except Exception as e:
        logger.error(f"創建支付失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建支付失敗: {str(e)}"
        )


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取支付列表
    用戶只能看到自己的支付記錄，管理員可以看到所有記錄
    """
    try:
        query = db.query(Payment)
        
        # 權限控制
        if current_user.membership_tier.value != "ADMIN":
            query = query.filter(Payment.user_id == current_user.id)
        
        # 狀態過濾
        if status_filter:
            query = query.filter(Payment.status == status_filter)
        
        payments = query.order_by(desc(Payment.created_at)).offset(skip).limit(limit).all()
        
        logger.info(f"獲取支付列表: 用戶 {current_user.id}, 數量: {len(payments)}")
        return payments
        
    except Exception as e:
        logger.error(f"獲取支付列表失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取支付列表失敗: {str(e)}"
        )


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取單筆支付詳情
    """
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付記錄不存在"
            )
        
        # 權限檢查
        if (payment.user_id != current_user.id and 
            current_user.membership_tier.value != "ADMIN"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="沒有權限查看此支付記錄"
            )
        
        logger.info(f"獲取支付詳情: {payment_id}")
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取支付詳情失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取支付詳情失敗: {str(e)}"
        )


@router.patch("/{payment_id}/status", response_model=PaymentResponse)
async def update_payment_status(
    payment_id: int,
    status_update: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新支付狀態 (僅管理員)
    """
    try:
        # 權限檢查
        if current_user.membership_tier.value != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理員可以更新支付狀態"
            )
        
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="支付記錄不存在"
            )
        
        # 更新狀態
        old_status = payment.status
        payment.status = status_update
        payment.updated_at = datetime.now()
        
        # 如果標記為已完成，記錄支付時間
        if status_update == PaymentStatus.COMPLETED.value:
            payment.paid_at = datetime.now()
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"更新支付狀態: {payment_id}, {old_status} -> {status_update}")
        return payment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新支付狀態失敗: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新支付狀態失敗: {str(e)}"
        )


@router.get("/stats/summary")
async def get_payment_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    獲取支付統計 (僅管理員)
    """
    try:
        # 權限檢查
        if current_user.membership_tier.value != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理員可以查看支付統計"
            )
        
        # 基本統計
        total_payments = db.query(Payment).count()
        completed_payments = db.query(Payment).filter(Payment.status == PaymentStatus.COMPLETED.value).count()
        pending_payments = db.query(Payment).filter(Payment.status == PaymentStatus.PENDING.value).count()
        failed_payments = db.query(Payment).filter(Payment.status == PaymentStatus.FAILED.value).count()
        
        # 總金額統計
        total_amount = db.query(func.sum(Payment.amount)).filter(
            Payment.status == PaymentStatus.COMPLETED.value
        ).scalar() or 0
        
        stats = {
            "total_payments": total_payments,
            "completed_payments": completed_payments,
            "pending_payments": pending_payments,
            "failed_payments": failed_payments,
            "total_amount": float(total_amount),
            "success_rate": (completed_payments / total_payments * 100) if total_payments > 0 else 0
        }
        
        logger.info(f"獲取支付統計: {stats}")
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取支付統計失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取支付統計失敗: {str(e)}"
        )