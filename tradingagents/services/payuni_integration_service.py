#!/usr/bin/env python3
"""
PayUni與不老傳說系統整合服務
處理支付與會員系統的完整整合
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..payments.gateways.payuni import PayUniGateway, PayUniConfig
from ..models.payment import Payment
from ..models.membership import MembershipTier, TierType
from ..services.payment_service import PaymentTransactionService
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class PayUniIntegrationService:
    """PayUni與不老傳說系統整合服務"""
    
    def __init__(self, db: Session):
        self.db = db
        self.payment_service = PaymentTransactionService(db)
        
        # PayUni配置 - 不老傳說-靈性智慧 正式商店
        self.payuni_config = {
            "merchant_id": "U03823060",  # 正式店家編號
            "hash_key": "kfud6pP4HFbGuJ9T4YBU4p85a7W9OhoU",  # Hash Key
            "hash_iv": "maO3kqxZObzGTnBu",  # IV Key
            "is_sandbox": False  # 生產環境
        }
        
        config = PayUniConfig(
            merchant_id=self.payuni_config["merchant_id"],
            hash_key=self.payuni_config["hash_key"],
            hash_iv=self.payuni_config["hash_iv"],
            is_sandbox=self.payuni_config["is_sandbox"]
        )
        self.gateway = PayUniGateway(config)
    
    def create_subscription_payment(self, user_id: int, tier_type: TierType, 
                                  duration_months: int = 1) -> Dict[str, Any]:
        """創建會員訂閱支付"""
        try:
            # 獲取會員方案價格
            pricing = self._get_tier_pricing(tier_type, duration_months)
            
            # 生成訂單號
            order_number = f"TA{user_id}{int(datetime.now().timestamp())}"
            
            # 準備支付數據
            payment_data = {
                "order_number": order_number,
                "amount": float(pricing["amount"]),
                "description": f"TradingAgents {pricing['tier_name']} {duration_months}個月訂閱",
                "item_name": f"{pricing['tier_name']}會員",
                "email": self._get_user_email(user_id),
                "return_url": f"http://localhost:3000/payment/success?order={order_number}",
                "notify_url": "http://localhost:8000/api/v1/payuni/webhook/notify",
                "customer_url": f"http://localhost:3000/payment/result?order={order_number}",
                "client_back_url": "http://localhost:3000/payment/cancel"
            }
            
            # 創建PayUni支付訂單
            payuni_result = self.gateway.create_payment(payment_data)
            
            if not payuni_result["success"]:
                return {
                    "success": False,
                    "error": f"PayUni支付創建失敗: {payuni_result['error']}"
                }
            
            # 記錄支付交易到數據庫
            payment_record = self._create_payment_record(
                user_id=user_id,
                order_number=order_number,
                amount=pricing["amount"],
                tier_type=tier_type,
                duration_months=duration_months,
                payuni_data=payuni_result
            )
            
            logger.info(f"會員訂閱支付創建成功: {order_number} (用戶: {user_id})")
            
            return {
                "success": True,
                "order_number": order_number,
                "payment_url": payuni_result["payment_url"],
                "post_data": payuni_result["post_data"],
                "amount": pricing["amount"],
                "tier_name": pricing["tier_name"],
                "duration_months": duration_months,
                "payment_id": payment_record.id if payment_record else None
            }
            
        except Exception as e:
            logger.error(f"創建會員訂閱支付失敗: {str(e)}")
            return {
                "success": False,
                "error": f"系統錯誤: {str(e)}"
            }
    
    async def handle_payment_notification(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理PayUni支付通知"""
        try:
            # 驗證PayUni回調
            verification_result = self.gateway.verify_callback(callback_data)
            
            if not verification_result["success"]:
                logger.error(f"PayUni通知驗證失敗: {verification_result['error']}")
                return {
                    "success": False,
                    "response": "0|驗證失敗"
                }
            
            trade_data = verification_result["trade_data"]
            payment_status = verification_result["status"]
            trade_no = verification_result["trade_no"]
            
            # 查找對應的支付記錄
            payment_record = self._get_payment_by_order_number(trade_no)
            if not payment_record:
                logger.error(f"找不到對應的支付記錄: {trade_no}")
                return {
                    "success": False,
                    "response": "0|找不到訂單"
                }
            
            # 更新支付狀態
            update_result = await self._update_payment_status(
                payment_record, 
                payment_status, 
                trade_data
            )
            
            if not update_result["success"]:
                logger.error(f"支付狀態更新失敗: {update_result['error']}")
                return {
                    "success": False,
                    "response": "0|狀態更新失敗"
                }
            
            # 如果支付成功，處理會員升級
            if payment_status == "completed":
                upgrade_result = await self._process_membership_upgrade(payment_record)
                if not upgrade_result["success"]:
                    logger.error(f"會員升級處理失敗: {upgrade_result['error']}")
                    # 即使升級失敗，也要回應成功，避免重複通知
            
            logger.info(f"PayUni支付通知處理完成: {trade_no} (狀態: {payment_status})")
            
            return {
                "success": True,
                "response": "1|OK",
                "payment_status": payment_status,
                "trade_no": trade_no
            }
            
        except Exception as e:
            logger.error(f"PayUni支付通知處理失敗: {str(e)}")
            return {
                "success": False,
                "response": "0|系統錯誤"
            }
    
    def _get_tier_pricing(self, tier_type: TierType, duration_months: int) -> Dict[str, Any]:
        """獲取會員方案價格"""
        # 基礎價格表
        base_prices = {
            TierType.BASIC: 0,      # 免費
            TierType.PREMIUM: 999,   # 高級會員
            TierType.VIP: 1999,     # VIP會員
            TierType.ENTERPRISE: 4999  # 企業會員
        }
        
        tier_names = {
            TierType.BASIC: "基礎會員",
            TierType.PREMIUM: "高級會員", 
            TierType.VIP: "VIP會員",
            TierType.ENTERPRISE: "企業會員"
        }
        
        base_price = base_prices.get(tier_type, 999)
        
        # 多月折扣
        discount_rates = {
            1: 1.0,    # 無折扣
            3: 0.9,    # 9折
            6: 0.8,    # 8折
            12: 0.7    # 7折
        }
        
        discount_rate = discount_rates.get(duration_months, 1.0)
        final_amount = base_price * duration_months * discount_rate
        
        return {
            "tier_type": tier_type,
            "tier_name": tier_names.get(tier_type, "未知方案"),
            "base_price": base_price,
            "duration_months": duration_months,
            "discount_rate": discount_rate,
            "amount": Decimal(str(final_amount))
        }
    
    def _get_user_email(self, user_id: int) -> str:
        """獲取用戶郵箱"""
        # 這裡應該查詢用戶表獲取郵箱
        # 暫時返回預設值
        return f"user{user_id}@tradingagents.com"
    
    def _create_payment_record(self, user_id: int, order_number: str, 
                             amount: Decimal, tier_type: TierType, 
                             duration_months: int, payuni_data: Dict[str, Any]) -> Optional[Payment]:
        """創建支付記錄"""
        try:
            payment = Payment(
                user_id=user_id,
                order_number=order_number,
                amount=amount,
                currency="TWD",
                payment_method="payuni",
                status="pending",
                tier_type=tier_type.value,
                duration_months=duration_months,
                gateway_data=payuni_data,
                created_at=datetime.now()
            )
            
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            
            return payment
            
        except Exception as e:
            logger.error(f"創建支付記錄失敗: {str(e)}")
            self.db.rollback()
            return None
    
    def _get_payment_by_order_number(self, order_number: str) -> Optional[Payment]:
        """根據訂單號獲取支付記錄"""
        try:
            return self.db.query(Payment).filter(
                Payment.order_number == order_number
            ).first()
        except Exception as e:
            logger.error(f"查詢支付記錄失敗: {str(e)}")
            return None
    
    async def _update_payment_status(self, payment: Payment, status: str, 
                                   trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新支付狀態"""
        try:
            payment.status = status
            payment.gateway_response = trade_data
            payment.paid_at = datetime.now() if status == "completed" else None
            payment.updated_at = datetime.now()
            
            self.db.commit()
            
            logger.info(f"支付狀態更新成功: {payment.order_number} -> {status}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"支付狀態更新失敗: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _process_membership_upgrade(self, payment: Payment) -> Dict[str, Any]:
        """處理會員升級"""
        try:
            # 計算會員到期時間
            expire_date = datetime.now() + timedelta(days=payment.duration_months * 30)
            
            # 查找或創建會員記錄
            membership = self.db.query(MembershipTier).filter(
                MembershipTier.user_id == payment.user_id
            ).first()
            
            if membership:
                # 更新現有會員
                membership.tier_type = payment.tier_type
                membership.expire_date = expire_date
                membership.updated_at = datetime.now()
            else:
                # 創建新會員記錄
                membership = MembershipTier(
                    user_id=payment.user_id,
                    tier_type=payment.tier_type,
                    start_date=datetime.now(),
                    expire_date=expire_date,
                    is_active=True,
                    created_at=datetime.now()
                )
                self.db.add(membership)
            
            self.db.commit()
            
            logger.info(f"會員升級成功: 用戶{payment.user_id} -> {payment.tier_type}")
            
            return {
                "success": True,
                "membership_id": membership.id,
                "tier_type": payment.tier_type,
                "expire_date": expire_date
            }
            
        except Exception as e:
            logger.error(f"會員升級處理失敗: {str(e)}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_payment_status(self, order_number: str) -> Dict[str, Any]:
        """獲取支付狀態"""
        try:
            payment = self._get_payment_by_order_number(order_number)
            
            if not payment:
                return {
                    "success": False,
                    "error": "找不到支付記錄"
                }
            
            return {
                "success": True,
                "order_number": payment.order_number,
                "status": payment.status,
                "amount": float(payment.amount),
                "tier_type": payment.tier_type,
                "duration_months": payment.duration_months,
                "created_at": payment.created_at.isoformat(),
                "paid_at": payment.paid_at.isoformat() if payment.paid_at else None
            }
            
        except Exception as e:
            logger.error(f"獲取支付狀態失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def query_payment_from_payuni(self, order_number: str) -> Dict[str, Any]:
        """從PayUni查詢支付狀態"""
        try:
            result = await self.gateway.query_payment(order_number)
            
            if result["success"]:
                # 同步更新本地支付狀態
                payment_record = self._get_payment_by_order_number(order_number)
                if payment_record:
                    await self._update_payment_status(
                        payment_record,
                        result["status"],
                        result.get("trade_data", {})
                    )
            
            return result
            
        except Exception as e:
            logger.error(f"PayUni支付查詢失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_supported_payment_methods(self) -> List[str]:
        """獲取支援的支付方式"""
        return self.gateway.get_supported_payment_methods()
    
    def validate_payment_data(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證支付數據"""
        errors = []
        
        # 驗證金額
        amount = payment_data.get("amount", 0)
        if not self.gateway.validate_amount(amount):
            errors.append("金額必須在1-999999之間")
        
        # 驗證訂單號
        order_number = payment_data.get("order_number", "")
        if not self.gateway.validate_trade_no(order_number):
            errors.append("訂單號格式不正確")
        
        # 驗證必要欄位
        required_fields = ["amount", "description", "order_number"]
        for field in required_fields:
            if not payment_data.get(field):
                errors.append(f"缺少必要欄位: {field}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }


# 工廠函數
def create_payuni_integration_service(db: Session) -> PayUniIntegrationService:
    """創建PayUni整合服務實例"""
    return PayUniIntegrationService(db)