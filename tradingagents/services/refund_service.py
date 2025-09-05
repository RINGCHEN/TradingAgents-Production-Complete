#!/usr/bin/env python3
"""
退款服務層 - TradingAgents系統
實現完整的退款申請、審核、處理工作流
"""

from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
import asyncio

from ..models.user import User, MembershipTier
from ..database.database import get_db
from ..payments.gateways.payuni import PayUniGateway, create_payuni_gateway
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class RefundStatus(str, Enum):
    """退款狀態枚舉"""
    PENDING = "pending"           # 退款申請待審核
    APPROVED = "approved"         # 退款申請已批准
    PROCESSING = "processing"     # 退款處理中
    COMPLETED = "completed"       # 退款完成
    REJECTED = "rejected"         # 退款申請被拒絕
    FAILED = "failed"            # 退款處理失敗
    CANCELLED = "cancelled"       # 退款申請已取消


class RefundReason(str, Enum):
    """退款原因枚舉"""
    USER_REQUEST = "user_request"               # 用戶主動申請
    SERVICE_UNAVAILABLE = "service_unavailable" # 服務不可用
    BILLING_ERROR = "billing_error"            # 計費錯誤
    DUPLICATE_CHARGE = "duplicate_charge"       # 重複扣款
    TECHNICAL_ISSUE = "technical_issue"        # 技術問題
    POLICY_VIOLATION = "policy_violation"      # 違反政策
    CHARGEBACK = "chargeback"                  # 銀行拒付
    OTHER = "other"                            # 其他原因


class RefundType(str, Enum):
    """退款類型枚舉"""
    FULL = "full"        # 全額退款
    PARTIAL = "partial"  # 部分退款
    PRORATED = "prorated" # 按比例退款


# 退款政策配置
REFUND_POLICIES = {
    "FULL_REFUND_DAYS": 7,        # 7天內全額退款
    "PARTIAL_REFUND_DAYS": 30,    # 30天內部分退款
    "NO_REFUND_AFTER_DAYS": 90,   # 90天後不可退款
    "USAGE_BASED_REFUND": True,   # 基於使用量的退款
    "MIN_REFUND_AMOUNT": 1.0,     # 最小退款金額
    "AUTO_APPROVE_LIMIT": 1000.0, # 自動審批限額
    "ADMIN_APPROVAL_REQUIRED": True, # 需要管理員審批
}

# 會員等級退款權益
MEMBERSHIP_REFUND_BENEFITS = {
    MembershipTier.FREE: {
        "full_refund_days": 3,
        "partial_refund_days": 14,
        "priority_processing": False,
        "auto_approve_limit": 100.0
    },
    MembershipTier.GOLD: {
        "full_refund_days": 7,
        "partial_refund_days": 30,
        "priority_processing": True,
        "auto_approve_limit": 500.0
    },
    MembershipTier.DIAMOND: {
        "full_refund_days": 14,
        "partial_refund_days": 60,
        "priority_processing": True,
        "auto_approve_limit": 2000.0
    }
}


class RefundCalculator:
    """退款金額計算器"""
    
    @staticmethod
    def calculate_refund_amount(
        original_amount: Decimal,
        payment_date: datetime,
        usage_data: Optional[Dict[str, Any]] = None,
        refund_type: RefundType = RefundType.FULL
    ) -> Tuple[Decimal, str]:
        """
        計算退款金額
        
        Args:
            original_amount: 原始付款金額
            payment_date: 付款日期
            usage_data: 使用數據
            refund_type: 退款類型
            
        Returns:
            Tuple[Decimal, str]: (退款金額, 計算說明)
        """
        try:
            days_since_payment = (datetime.utcnow() - payment_date).days
            
            if refund_type == RefundType.FULL:
                if days_since_payment <= REFUND_POLICIES["FULL_REFUND_DAYS"]:
                    return original_amount, "全額退款 - 在全額退款期限內"
                else:
                    return Decimal("0"), "超出全額退款期限"
            
            elif refund_type == RefundType.PARTIAL:
                if days_since_payment <= REFUND_POLICIES["PARTIAL_REFUND_DAYS"]:
                    # 基於時間的部分退款
                    refund_ratio = max(0, 1 - (days_since_payment / REFUND_POLICIES["PARTIAL_REFUND_DAYS"]))
                    refund_amount = original_amount * Decimal(str(refund_ratio))
                    return refund_amount, f"部分退款 - 基於時間比例 ({refund_ratio:.2%})"
                else:
                    return Decimal("0"), "超出部分退款期限"
            
            elif refund_type == RefundType.PRORATED:
                if usage_data and REFUND_POLICIES["USAGE_BASED_REFUND"]:
                    # 基於使用量的按比例退款
                    usage_ratio = usage_data.get("usage_ratio", 0.0)
                    unused_ratio = max(0, 1 - usage_ratio)
                    refund_amount = original_amount * Decimal(str(unused_ratio))
                    return refund_amount, f"按比例退款 - 基於使用量 (未使用: {unused_ratio:.2%})"
                else:
                    # 回退到基於時間的計算
                    return RefundCalculator.calculate_refund_amount(
                        original_amount, payment_date, usage_data, RefundType.PARTIAL
                    )
            
            return Decimal("0"), "無法計算退款金額"
            
        except Exception as e:
            logger.error(f"退款金額計算失敗: {str(e)}")
            return Decimal("0"), f"計算錯誤: {str(e)}"


class RefundEligibilityChecker:
    """退款資格檢查器"""
    
    @staticmethod
    def check_eligibility(
        user: User,
        transaction_data: Dict[str, Any],
        requested_amount: Optional[Decimal] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        檢查退款資格
        
        Args:
            user: 用戶對象
            transaction_data: 交易數據
            requested_amount: 請求退款金額
            
        Returns:
            Tuple[bool, str, Dict]: (是否符合資格, 原因, 詳細信息)
        """
        try:
            payment_date = transaction_data.get("created_at")
            if not payment_date:
                return False, "無法獲取付款日期", {}
            
            # 轉換為 datetime 對象
            if isinstance(payment_date, str):
                payment_date = datetime.fromisoformat(payment_date.replace('Z', '+00:00'))
            
            days_since_payment = (datetime.utcnow() - payment_date).days
            original_amount = Decimal(str(transaction_data.get("amount", 0)))
            
            # 獲取會員權益
            benefits = MEMBERSHIP_REFUND_BENEFITS.get(
                user.membership_tier, 
                MEMBERSHIP_REFUND_BENEFITS[MembershipTier.FREE]
            )
            
            # 檢查時間限制
            if days_since_payment > REFUND_POLICIES["NO_REFUND_AFTER_DAYS"]:
                return False, "超出最大退款期限", {
                    "days_since_payment": days_since_payment,
                    "max_days": REFUND_POLICIES["NO_REFUND_AFTER_DAYS"]
                }
            
            # 檢查金額限制
            min_amount = REFUND_POLICIES["MIN_REFUND_AMOUNT"]
            if requested_amount and requested_amount < Decimal(str(min_amount)):
                return False, f"退款金額低於最小限額 NT${min_amount}", {
                    "requested_amount": float(requested_amount),
                    "min_amount": min_amount
                }
            
            # 檢查是否超過原始金額
            if requested_amount and requested_amount > original_amount:
                return False, "退款金額不能超過原始付款金額", {
                    "requested_amount": float(requested_amount),
                    "original_amount": float(original_amount)
                }
            
            # 檢查交易狀態
            transaction_status = transaction_data.get("status", "")
            if transaction_status not in ["completed", "success"]:
                return False, "只能對已完成的交易申請退款", {
                    "transaction_status": transaction_status
                }
            
            # 檢查是否已有退款申請
            existing_refunds = transaction_data.get("refunds", [])
            if existing_refunds:
                total_refunded = sum(Decimal(str(r.get("amount", 0))) for r in existing_refunds)
                remaining_amount = original_amount - total_refunded
                
                if requested_amount and requested_amount > remaining_amount:
                    return False, "退款金額超過可退款餘額", {
                        "requested_amount": float(requested_amount),
                        "remaining_amount": float(remaining_amount),
                        "total_refunded": float(total_refunded)
                    }
            
            return True, "符合退款資格", {
                "days_since_payment": days_since_payment,
                "original_amount": float(original_amount),
                "membership_benefits": benefits,
                "can_full_refund": days_since_payment <= benefits["full_refund_days"],
                "can_partial_refund": days_since_payment <= benefits["partial_refund_days"]
            }
            
        except Exception as e:
            logger.error(f"退款資格檢查失敗: {str(e)}")
            return False, f"檢查失敗: {str(e)}", {}


class RefundService:
    """退款服務 - 核心業務邏輯處理"""
    
    def __init__(self, db: Session, payuni_config: Dict[str, Any]):
        self.db = db
        self.payuni_config = payuni_config
        self.payuni_gateway = create_payuni_gateway(
            payuni_config["merchant_id"],
            payuni_config["hash_key"], 
            payuni_config["hash_iv"],
            payuni_config["is_sandbox"]
        )
        self.logger = logger
    
    async def create_refund_request(
        self,
        user_id: int,
        transaction_id: str,
        refund_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        創建退款申請
        
        Args:
            user_id: 用戶ID
            transaction_id: 交易ID
            refund_data: 退款數據
                - amount: 退款金額 (可選，為空表示全額退款)
                - reason: 退款原因
                - description: 退款說明
                - refund_type: 退款類型 (可選)
                
        Returns:
            Dict: 退款申請結果
        """
        try:
            # 獲取用戶和交易信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"success": False, "error": "用戶不存在"}
            
            # 模擬獲取交易數據 (實際應該從數據庫獲取)
            transaction_data = await self._get_transaction_data(transaction_id)
            if not transaction_data:
                return {"success": False, "error": "交易不存在"}
            
            # 檢查退款資格
            eligible, reason, eligibility_info = RefundEligibilityChecker.check_eligibility(
                user, transaction_data, refund_data.get("amount")
            )
            
            if not eligible:
                return {
                    "success": False,
                    "error": reason,
                    "eligibility_info": eligibility_info
                }
            
            # 計算退款金額
            requested_amount = refund_data.get("amount")
            if not requested_amount:
                # 自動計算退款金額
                refund_type = RefundType(refund_data.get("refund_type", RefundType.FULL))
                calculated_amount, calculation_note = RefundCalculator.calculate_refund_amount(
                    Decimal(str(transaction_data["amount"])),
                    transaction_data["created_at"],
                    refund_data.get("usage_data"),
                    refund_type
                )
                requested_amount = calculated_amount
            else:
                requested_amount = Decimal(str(requested_amount))
                calculation_note = "用戶指定金額"
            
            # 檢查最小退款金額
            if requested_amount < Decimal(str(REFUND_POLICIES["MIN_REFUND_AMOUNT"])):
                return {
                    "success": False,
                    "error": f"退款金額低於最小限額 NT${REFUND_POLICIES['MIN_REFUND_AMOUNT']}"
                }
            
            # 生成退款申請記錄
            refund_request = {
                "id": f"REF{int(datetime.utcnow().timestamp())}{user_id}",
                "user_id": user_id,
                "transaction_id": transaction_id,
                "amount": float(requested_amount),
                "reason": RefundReason(refund_data["reason"]),
                "description": refund_data.get("description", ""),
                "status": RefundStatus.PENDING,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "calculation_note": calculation_note,
                "eligibility_info": eligibility_info
            }
            
            # 判斷是否需要自動審批
            auto_approve_limit = MEMBERSHIP_REFUND_BENEFITS.get(
                user.membership_tier, 
                MEMBERSHIP_REFUND_BENEFITS[MembershipTier.FREE]
            )["auto_approve_limit"]
            
            if (requested_amount <= Decimal(str(auto_approve_limit)) and 
                refund_data["reason"] in [RefundReason.USER_REQUEST, RefundReason.BILLING_ERROR]):
                # 自動審批
                refund_request["status"] = RefundStatus.APPROVED
                refund_request["approved_at"] = datetime.utcnow()
                refund_request["approved_by"] = "system_auto"
                
                self.logger.info(f"退款申請自動審批: {refund_request['id']} (金額: NT${requested_amount})")
            else:
                # 需要人工審批
                self.logger.info(f"退款申請待審核: {refund_request['id']} (金額: NT${requested_amount})")
            
            # 保存退款申請 (實際應該保存到數據庫)
            await self._save_refund_request(refund_request)
            
            return {
                "success": True,
                "refund_request_id": refund_request["id"],
                "amount": float(requested_amount),
                "status": refund_request["status"],
                "message": "退款申請創建成功",
                "auto_approved": refund_request["status"] == RefundStatus.APPROVED,
                "calculation_note": calculation_note
            }
            
        except Exception as e:
            self.logger.error(f"創建退款申請失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "REFUND_REQUEST_FAILED"
            }
    
    async def process_refund(self, refund_request_id: str) -> Dict[str, Any]:
        """
        處理退款 - 調用PayUni API執行退款
        
        Args:
            refund_request_id: 退款申請ID
            
        Returns:
            Dict: 退款處理結果
        """
        try:
            # 獲取退款申請
            refund_request = await self._get_refund_request(refund_request_id)
            if not refund_request:
                return {"success": False, "error": "退款申請不存在"}
            
            # 檢查狀態
            if refund_request["status"] != RefundStatus.APPROVED:
                return {
                    "success": False,
                    "error": f"退款申請狀態錯誤: {refund_request['status']}"
                }
            
            # 獲取原始交易信息
            transaction_data = await self._get_transaction_data(refund_request["transaction_id"])
            if not transaction_data:
                return {"success": False, "error": "原始交易不存在"}
            
            # 準備PayUni退款數據
            payuni_refund_data = {
                "original_trade_no": transaction_data["payuni_trade_no"],
                "refund_amount": refund_request["amount"],
                "refund_reason": refund_request["description"] or "用戶申請退款",
                "notify_url": "http://localhost:8000/api/v1/payuni/webhook/refund-notify"
            }
            
            # 更新狀態為處理中
            await self._update_refund_status(
                refund_request_id, 
                RefundStatus.PROCESSING,
                "開始處理退款"
            )
            
            # 調用PayUni退款API
            refund_result = await self.payuni_gateway.refund_payment(payuni_refund_data)
            
            if refund_result["success"]:
                # 退款請求成功
                await self._update_refund_status(
                    refund_request_id,
                    RefundStatus.PROCESSING,
                    "退款請求已發送到PayUni",
                    {
                        "payuni_refund_no": refund_result.get("refund_no"),
                        "payuni_status": refund_result.get("status"),
                        "payuni_message": refund_result.get("message")
                    }
                )
                
                self.logger.info(f"PayUni退款請求成功: {refund_request_id} -> {refund_result.get('refund_no')}")
                
                return {
                    "success": True,
                    "refund_request_id": refund_request_id,
                    "payuni_refund_no": refund_result.get("refund_no"),
                    "status": RefundStatus.PROCESSING,
                    "message": "退款請求已發送，等待處理結果"
                }
            else:
                # 退款請求失敗
                await self._update_refund_status(
                    refund_request_id,
                    RefundStatus.FAILED,
                    f"PayUni退款失敗: {refund_result.get('error', 'Unknown error')}",
                    {"payuni_error": refund_result.get("error")}
                )
                
                self.logger.error(f"PayUni退款失敗: {refund_request_id} - {refund_result.get('error')}")
                
                return {
                    "success": False,
                    "refund_request_id": refund_request_id,
                    "error": refund_result.get("error", "退款處理失敗"),
                    "error_code": refund_result.get("error_code", "PAYUNI_REFUND_FAILED")
                }
                
        except Exception as e:
            # 處理異常
            self.logger.error(f"退款處理異常: {str(e)}")
            
            try:
                await self._update_refund_status(
                    refund_request_id,
                    RefundStatus.FAILED,
                    f"處理異常: {str(e)}"
                )
            except:
                pass  # 防止二次異常
            
            return {
                "success": False,
                "error": str(e),
                "error_code": "REFUND_PROCESS_EXCEPTION"
            }
    
    async def query_refund_status(self, refund_request_id: str) -> Dict[str, Any]:
        """
        查詢退款狀態
        
        Args:
            refund_request_id: 退款申請ID
            
        Returns:
            Dict: 退款狀態信息
        """
        try:
            # 獲取本地退款申請
            refund_request = await self._get_refund_request(refund_request_id)
            if not refund_request:
                return {"success": False, "error": "退款申請不存在"}
            
            # 如果有PayUni退款號，查詢PayUni狀態
            payuni_refund_no = refund_request.get("payuni_refund_no")
            if payuni_refund_no and refund_request["status"] == RefundStatus.PROCESSING:
                payuni_result = await self.payuni_gateway.query_refund(payuni_refund_no)
                
                if payuni_result["success"]:
                    payuni_status = payuni_result.get("status", "unknown")
                    
                    # 同步狀態
                    if payuni_status == "completed":
                        await self._update_refund_status(
                            refund_request_id,
                            RefundStatus.COMPLETED,
                            "退款完成",
                            {
                                "completed_at": datetime.utcnow(),
                                "payuni_refund_data": payuni_result.get("refund_data", {})
                            }
                        )
                        refund_request["status"] = RefundStatus.COMPLETED
                    elif payuni_status == "failed":
                        await self._update_refund_status(
                            refund_request_id,
                            RefundStatus.FAILED,
                            "PayUni退款失敗",
                            {"payuni_error": payuni_result.get("error")}
                        )
                        refund_request["status"] = RefundStatus.FAILED
            
            return {
                "success": True,
                "refund_request": refund_request,
                "payuni_status": payuni_result if 'payuni_result' in locals() else None
            }
            
        except Exception as e:
            self.logger.error(f"查詢退款狀態失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "REFUND_QUERY_FAILED"
            }
    
    async def get_user_refunds(self, user_id: int, status: Optional[RefundStatus] = None) -> Dict[str, Any]:
        """
        獲取用戶退款記錄
        
        Args:
            user_id: 用戶ID
            status: 退款狀態過濾 (可選)
            
        Returns:
            Dict: 用戶退款記錄列表
        """
        try:
            # 實際應該從數據庫查詢
            user_refunds = await self._get_user_refunds_from_db(user_id, status)
            
            return {
                "success": True,
                "refunds": user_refunds,
                "count": len(user_refunds)
            }
            
        except Exception as e:
            self.logger.error(f"獲取用戶退款記錄失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "GET_REFUNDS_FAILED"
            }
    
    # 私有輔助方法
    async def _get_transaction_data(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """獲取交易數據 (模擬實現)"""
        # 實際應該從數據庫或支付服務獲取
        return {
            "id": transaction_id,
            "amount": 299.0,
            "status": "completed",
            "payuni_trade_no": f"TA{transaction_id}",
            "created_at": datetime.utcnow() - timedelta(days=3),
            "refunds": []
        }
    
    async def _save_refund_request(self, refund_request: Dict[str, Any]) -> bool:
        """保存退款申請 (模擬實現)"""
        # 實際應該保存到數據庫
        self.logger.info(f"保存退款申請: {refund_request['id']}")
        return True
    
    async def _get_refund_request(self, refund_request_id: str) -> Optional[Dict[str, Any]]:
        """獲取退款申請 (模擬實現)"""
        # 實際應該從數據庫獲取
        return {
            "id": refund_request_id,
            "user_id": 1,
            "transaction_id": "TEST_TRANS_001",
            "amount": 299.0,
            "status": RefundStatus.APPROVED,
            "reason": RefundReason.USER_REQUEST,
            "description": "用戶主動申請退款",
            "created_at": datetime.utcnow(),
            "payuni_refund_no": None
        }
    
    async def _update_refund_status(
        self,
        refund_request_id: str,
        status: RefundStatus,
        note: str,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新退款狀態 (模擬實現)"""
        self.logger.info(f"更新退款狀態: {refund_request_id} -> {status} ({note})")
        if additional_data:
            self.logger.debug(f"附加數據: {additional_data}")
        return True
    
    async def _get_user_refunds_from_db(
        self,
        user_id: int,
        status: Optional[RefundStatus] = None
    ) -> List[Dict[str, Any]]:
        """從數據庫獲取用戶退款記錄 (模擬實現)"""
        # 實際應該從數據庫查詢
        return [
            {
                "id": f"REF{user_id}001",
                "transaction_id": "TEST_TRANS_001",
                "amount": 299.0,
                "status": RefundStatus.COMPLETED,
                "reason": RefundReason.USER_REQUEST,
                "created_at": datetime.utcnow() - timedelta(days=5),
                "completed_at": datetime.utcnow() - timedelta(days=3)
            }
        ]


# 工廠函數
def create_refund_service(db: Session, payuni_config: Dict[str, Any]) -> RefundService:
    """創建退款服務實例"""
    return RefundService(db, payuni_config)


# 退款政策工具函數
def get_refund_policy_info(membership_tier: MembershipTier) -> Dict[str, Any]:
    """獲取退款政策信息"""
    general_policy = REFUND_POLICIES.copy()
    membership_benefits = MEMBERSHIP_REFUND_BENEFITS.get(
        membership_tier, 
        MEMBERSHIP_REFUND_BENEFITS[MembershipTier.FREE]
    )
    
    return {
        "general_policy": general_policy,
        "membership_benefits": membership_benefits,
        "effective_policy": {
            **general_policy,
            "full_refund_days": membership_benefits["full_refund_days"],
            "partial_refund_days": membership_benefits["partial_refund_days"],
            "auto_approve_limit": membership_benefits["auto_approve_limit"],
            "priority_processing": membership_benefits["priority_processing"]
        }
    }


def validate_refund_amount(amount: Decimal, original_amount: Decimal) -> Tuple[bool, str]:
    """驗證退款金額"""
    min_amount = Decimal(str(REFUND_POLICIES["MIN_REFUND_AMOUNT"]))
    
    if amount < min_amount:
        return False, f"退款金額不能少於 NT${min_amount}"
    
    if amount > original_amount:
        return False, "退款金額不能超過原始付款金額"
    
    return True, "金額驗證通過"