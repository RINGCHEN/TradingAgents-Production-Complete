#!/usr/bin/env python3
"""
PayUni 支付閘道 - 生產級實現
從 mindful_sphere 專案移植的成熟實現
"""

import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs
import aiohttp
import asyncio
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
import base64
import logging

logger = logging.getLogger(__name__)


class PayUniConfig:
    """PayUni 配置類"""
    
    def __init__(self, merchant_id: str, hash_key: str, hash_iv: str, 
                 is_sandbox: bool = True):
        self.merchant_id = merchant_id
        self.hash_key = hash_key
        self.hash_iv = hash_iv
        self.is_sandbox = is_sandbox
        
        # API URLs
        if is_sandbox:
            self.api_url = "https://sandbox-api.payuni.com.tw/api/payment"
            self.query_url = "https://sandbox-api.payuni.com.tw/api/trade/query"
            self.refund_url = "https://sandbox-api.payuni.com.tw/api/trade/refund"
            self.refund_query_url = "https://sandbox-api.payuni.com.tw/api/trade/refund/query"
        else:
            self.api_url = "https://api.payuni.com.tw/api/payment"
            self.query_url = "https://api.payuni.com.tw/api/trade/query"
            self.refund_url = "https://api.payuni.com.tw/api/trade/refund"
            self.refund_query_url = "https://api.payuni.com.tw/api/trade/refund/query"


class PayUniGateway:
    """PayUni 支付閘道 - 生產級實現"""
    
    def __init__(self, config: PayUniConfig):
        self.config = config
        self.logger = logger
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """創建PayUni支付訂單"""
        try:
            # 驗證必要參數
            required_fields = ['order_number', 'amount', 'description']
            for field in required_fields:
                if field not in payment_data:
                    raise ValueError(f"缺少必要參數: {field}")
            
            # 準備支付參數
            params = {
                "MerchantID": self.config.merchant_id,
                "TradeNo": payment_data["order_number"],
                "TradeAmt": int(float(payment_data["amount"])),
                "TradeDesc": payment_data["description"][:200],  # 限制長度
                "ItemName": payment_data.get("item_name", "TradingAgents服務")[:200],
                "ReturnURL": payment_data.get("return_url", ""),
                "NotifyURL": payment_data.get("notify_url", ""),
                "CustomerURL": payment_data.get("customer_url", ""),
                "ClientBackURL": payment_data.get("client_back_url", ""),
                "Email": payment_data.get("email", ""),
                "LoginType": 0,  # 不須登入
                "OrderComment": payment_data.get("comment", "")[:200],
                "Timestamp": int(time.time())
            }
            
            # 添加可選參數
            if "expire_date" in payment_data:
                params["ExpireDate"] = payment_data["expire_date"]
            
            if "payment_type" in payment_data:
                params["PaymentType"] = payment_data["payment_type"]
            
            # 生成檢查碼
            params["CheckValue"] = self._generate_check_value(params)
            
            # 加密參數
            encrypted_data = self._aes_encrypt(urlencode(params))
            
            # 準備POST數據
            post_data = {
                "MerchantID": self.config.merchant_id,
                "TradeInfo": encrypted_data,
                "TradeSha": self._generate_trade_sha(encrypted_data),
                "Version": "2.0"
            }
            
            self.logger.info(f"PayUni支付訂單創建成功: {payment_data['order_number']}")
            
            return {
                "success": True,
                "payment_url": self.config.api_url,
                "post_data": post_data,
                "trade_no": payment_data["order_number"],
                "encrypted_data": encrypted_data
            }
            
        except Exception as e:
            self.logger.error(f"PayUni支付創建失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "PAYMENT_CREATE_FAILED"
            }
    
    async def query_payment(self, trade_no: str) -> Dict[str, Any]:
        """查詢PayUni支付狀態"""
        try:
            params = {
                "MerchantID": self.config.merchant_id,
                "TradeNo": trade_no,
                "Timestamp": int(time.time())
            }
            
            # 生成檢查碼
            params["CheckValue"] = self._generate_check_value(params)
            
            # 加密參數
            encrypted_data = self._aes_encrypt(urlencode(params))
            
            post_data = {
                "MerchantID": self.config.merchant_id,
                "TradeInfo": encrypted_data,
                "TradeSha": self._generate_trade_sha(encrypted_data),
                "Version": "2.0"
            }
            
            # 發送查詢請求
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.config.query_url, data=post_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_query_response(result)
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "error_code": "HTTP_ERROR"
                        }
                        
        except asyncio.TimeoutError:
            self.logger.error(f"PayUni支付查詢超時: {trade_no}")
            return {
                "success": False,
                "error": "查詢超時",
                "error_code": "TIMEOUT"
            }
        except Exception as e:
            self.logger.error(f"PayUni支付查詢失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "QUERY_FAILED"
            }
    
    def verify_callback(self, callback_data: Dict[str, Any]) -> Dict[str, Any]:
        """驗證PayUni回調數據"""
        try:
            # 檢查必要欄位
            required_fields = ["MerchantID", "TradeInfo", "TradeSha"]
            for field in required_fields:
                if field not in callback_data:
                    return {
                        "success": False,
                        "error": f"缺少必要欄位: {field}",
                        "error_code": "MISSING_FIELD"
                    }
            
            # 驗證商店代號
            if callback_data["MerchantID"] != self.config.merchant_id:
                return {
                    "success": False,
                    "error": "商店代號不符",
                    "error_code": "INVALID_MERCHANT"
                }
            
            # 驗證簽名
            if not self._verify_callback_signature(callback_data):
                return {
                    "success": False,
                    "error": "簽名驗證失敗",
                    "error_code": "SIGNATURE_FAILED"
                }
            
            # 解密交易資料
            trade_info = callback_data.get("TradeInfo", "")
            decrypted_data = self._aes_decrypt(trade_info)
            
            # 解析交易資料
            trade_data = self._parse_trade_data(decrypted_data)
            
            # 驗證交易資料完整性
            if not trade_data.get("TradeNo"):
                return {
                    "success": False,
                    "error": "交易資料不完整",
                    "error_code": "INCOMPLETE_DATA"
                }
            
            self.logger.info(f"PayUni回調驗證成功: {trade_data.get('TradeNo')}")
            
            return {
                "success": True,
                "trade_data": trade_data,
                "status": self._map_payment_status(trade_data.get("TradeStatus", "")),
                "amount": trade_data.get("TradeAmt", "0"),
                "trade_no": trade_data.get("TradeNo", ""),
                "payment_type": trade_data.get("PaymentType", ""),
                "pay_time": trade_data.get("PayTime", "")
            }
            
        except Exception as e:
            self.logger.error(f"PayUni回調驗證失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "VERIFICATION_FAILED"
            }
    
    def _generate_check_value(self, params: Dict[str, Any]) -> str:
        """生成檢查碼"""
        try:
            # 排序參數 (排除CheckValue)
            sorted_params = sorted(
                [(k, v) for k, v in params.items() if k != "CheckValue"]
            )
            
            # 組合字串
            param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            
            # 加上HashKey和HashIV
            raw_string = f"HashKey={self.config.hash_key}&{param_string}&HashIV={self.config.hash_iv}"
            
            # URL編碼處理
            encoded_string = raw_string.replace("%", "%25").replace(" ", "%20")
            
            # SHA256加密
            return hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
            
        except Exception as e:
            self.logger.error(f"檢查碼生成失敗: {str(e)}")
            raise
    
    def _generate_trade_sha(self, trade_info: str) -> str:
        """生成交易SHA"""
        try:
            raw_string = f"HashKey={self.config.hash_key}&{trade_info}&HashIV={self.config.hash_iv}"
            return hashlib.sha256(raw_string.encode('utf-8')).hexdigest().upper()
        except Exception as e:
            self.logger.error(f"交易SHA生成失敗: {str(e)}")
            raise
    
    def _aes_encrypt(self, data: str) -> str:
        """AES加密 using cryptography library"""
        try:
            # 準備密鑰和IV
            key = self.config.hash_key.encode('utf-8')
            iv = self.config.hash_iv.encode('utf-8')

            # 創建 AES CBC cipher
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            encryptor = cipher.encryptor()

            # 創建 PKCS7 padding
            padder = padding.PKCS7(algorithms.AES.block_size).padder()
            padded_data = padder.update(data.encode('utf-8')) + padder.finalize()

            # 加密
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()

            # Base64編碼
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            self.logger.error(f"AES加密失敗: {str(e)}")
            raise
    
    def _aes_decrypt(self, encrypted_data: str) -> str:
        """AES解密 using cryptography library"""
        try:
            # 準備密鑰和IV
            key = self.config.hash_key.encode('utf-8')
            iv = self.config.hash_iv.encode('utf-8')

            # Base64解碼
            encrypted_bytes = base64.b64decode(encrypted_data)

            # 創建 AES CBC cipher
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            decryptor = cipher.decryptor()

            # 解密
            decrypted_padded_data = decryptor.update(encrypted_bytes) + decryptor.finalize()

            # 移除 PKCS7 padding
            unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
            unpadded_data = unpadder.update(decrypted_padded_data) + unpadder.finalize()

            return unpadded_data.decode('utf-8')

        except Exception as e:
            self.logger.error(f"AES解密失敗: {str(e)}")
            raise
    
    def _verify_callback_signature(self, callback_data: Dict[str, Any]) -> bool:
        """驗證回調簽名"""
        try:
            trade_info = callback_data.get("TradeInfo", "")
            trade_sha = callback_data.get("TradeSha", "")
            
            expected_sha = self._generate_trade_sha(trade_info)
            
            return hmac.compare_digest(trade_sha, expected_sha)
            
        except Exception as e:
            logger.error(f"簽名驗證失敗: {str(e)}")
            return False
    
    def _parse_trade_data(self, decrypted_data: str) -> Dict[str, Any]:
        """解析交易數據"""
        try:
            # 解析URL編碼的數據
            params = {}
            for pair in decrypted_data.split("&"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    params[key] = value
            
            return params
            
        except Exception as e:
            logger.error(f"交易數據解析失敗: {str(e)}")
            return {}
    
    def _parse_query_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析查詢回應"""
        try:
            if response.get("Status") == "SUCCESS":
                # 解密結果數據
                result_data = response.get("Result", {})
                trade_info = result_data.get("TradeInfo", "")
                
                if trade_info:
                    decrypted_data = self._aes_decrypt(trade_info)
                    trade_data = self._parse_trade_data(decrypted_data)
                    
                    return {
                        "success": True,
                        "trade_data": trade_data,
                        "status": self._map_payment_status(trade_data.get("TradeStatus", ""))
                    }
            
            return {
                "success": False,
                "error": response.get("Message", "查詢失敗")
            }
            
        except Exception as e:
            logger.error(f"查詢回應解析失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _map_payment_status(self, payuni_status: str) -> str:
        """映射PayUni狀態到系統狀態"""
        status_mapping = {
            "SUCCESS": "completed",
            "FAILED": "failed",
            "PENDING": "pending",
            "CANCEL": "cancelled",
            "REFUND": "refunded",
            "PARTIAL_REFUND": "partial_refunded"
        }
        
        return status_mapping.get(payuni_status.upper(), "unknown")
    
    def get_supported_payment_methods(self) -> List[str]:
        """獲取支援的支付方式"""
        return [
            "CREDIT",      # 信用卡
            "WEBATM",      # 網路ATM
            "VACC",        # 虛擬帳號
            "CVS",         # 超商代碼
            "BARCODE"      # 超商條碼
        ]
    
    def validate_amount(self, amount: float) -> bool:
        """驗證金額"""
        return 1 <= amount <= 999999
    
    def validate_trade_no(self, trade_no: str) -> bool:
        """驗證訂單號"""
        return len(trade_no) <= 20 and trade_no.isalnum()
    
    async def refund_payment(self, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        PayUni 退款處理
        
        Args:
            refund_data: 退款數據
                - original_trade_no: 原始交易號碼
                - refund_amount: 退款金額 (None 表示全額退款)
                - refund_reason: 退款原因
                - notify_url: 退款通知URL (可選)
        
        Returns:
            Dict: 退款處理結果
        """
        try:
            # 驗證必要參數
            required_fields = ['original_trade_no', 'refund_reason']
            for field in required_fields:
                if field not in refund_data:
                    raise ValueError(f"缺少必要參數: {field}")
            
            # 生成退款訂單號
            refund_trade_no = f"RF{int(time.time())}{str(uuid.uuid4())[:8]}"
            
            # 準備退款參數
            params = {
                "MerchantID": self.config.merchant_id,
                "TradeNo": refund_data["original_trade_no"],
                "RefundNo": refund_trade_no,
                "RefundAmt": refund_data.get("refund_amount", ""),  # 空值表示全額退款
                "RefundDesc": refund_data["refund_reason"][:200],
                "NotifyURL": refund_data.get("notify_url", ""),
                "Timestamp": int(time.time())
            }
            
            # 生成檢查碼
            params["CheckValue"] = self._generate_check_value(params)
            
            # 加密參數
            encrypted_data = self._aes_encrypt(urlencode(params))
            
            # 準備POST數據
            post_data = {
                "MerchantID": self.config.merchant_id,
                "TradeInfo": encrypted_data,
                "TradeSha": self._generate_trade_sha(encrypted_data),
                "Version": "2.0"
            }
            
            # 發送退款請求
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.config.refund_url, data=post_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_refund_response(result, refund_trade_no)
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "error_code": "HTTP_ERROR"
                        }
            
        except asyncio.TimeoutError:
            self.logger.error(f"PayUni退款請求超時: {refund_data.get('original_trade_no')}")
            return {
                "success": False,
                "error": "退款請求超時",
                "error_code": "TIMEOUT"
            }
        except Exception as e:
            self.logger.error(f"PayUni退款處理失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "REFUND_FAILED"
            }
    
    async def query_refund(self, refund_no: str) -> Dict[str, Any]:
        """
        查詢PayUni退款狀態
        
        Args:
            refund_no: 退款訂單號
            
        Returns:
            Dict: 退款查詢結果
        """
        try:
            params = {
                "MerchantID": self.config.merchant_id,
                "RefundNo": refund_no,
                "Timestamp": int(time.time())
            }
            
            # 生成檢查碼
            params["CheckValue"] = self._generate_check_value(params)
            
            # 加密參數
            encrypted_data = self._aes_encrypt(urlencode(params))
            
            post_data = {
                "MerchantID": self.config.merchant_id,
                "TradeInfo": encrypted_data,
                "TradeSha": self._generate_trade_sha(encrypted_data),
                "Version": "2.0"
            }
            
            # 發送查詢請求
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self.config.refund_query_url, data=post_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return self._parse_refund_query_response(result)
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "error_code": "HTTP_ERROR"
                        }
                        
        except asyncio.TimeoutError:
            self.logger.error(f"PayUni退款查詢超時: {refund_no}")
            return {
                "success": False,
                "error": "退款查詢超時",
                "error_code": "TIMEOUT"
            }
        except Exception as e:
            self.logger.error(f"PayUni退款查詢失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "REFUND_QUERY_FAILED"
            }
    
    def _parse_refund_response(self, response: Dict[str, Any], refund_trade_no: str) -> Dict[str, Any]:
        """解析退款回應"""
        try:
            if response.get("Status") == "SUCCESS":
                result_data = response.get("Result", {})
                
                # 如果有加密的退款資料，解密它
                if "TradeInfo" in result_data:
                    trade_info = result_data.get("TradeInfo", "")
                    if trade_info:
                        decrypted_data = self._aes_decrypt(trade_info)
                        refund_data = self._parse_trade_data(decrypted_data)
                        
                        return {
                            "success": True,
                            "refund_no": refund_trade_no,
                            "refund_data": refund_data,
                            "status": self._map_refund_status(refund_data.get("RefundStatus", "")),
                            "message": response.get("Message", "退款處理成功")
                        }
                
                # 如果沒有加密資料，直接返回基本資訊
                return {
                    "success": True,
                    "refund_no": refund_trade_no,
                    "status": "processing",
                    "message": response.get("Message", "退款處理中")
                }
            else:
                return {
                    "success": False,
                    "error": response.get("Message", "退款處理失敗"),
                    "error_code": "REFUND_REJECTED"
                }
                
        except Exception as e:
            self.logger.error(f"退款回應解析失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "RESPONSE_PARSE_ERROR"
            }
    
    def _parse_refund_query_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """解析退款查詢回應"""
        try:
            if response.get("Status") == "SUCCESS":
                result_data = response.get("Result", {})
                trade_info = result_data.get("TradeInfo", "")
                
                if trade_info:
                    decrypted_data = self._aes_decrypt(trade_info)
                    refund_data = self._parse_trade_data(decrypted_data)
                    
                    return {
                        "success": True,
                        "refund_data": refund_data,
                        "status": self._map_refund_status(refund_data.get("RefundStatus", "")),
                        "refund_amount": refund_data.get("RefundAmt", "0"),
                        "refund_time": refund_data.get("RefundTime", ""),
                        "original_trade_no": refund_data.get("TradeNo", ""),
                        "refund_no": refund_data.get("RefundNo", "")
                    }
            
            return {
                "success": False,
                "error": response.get("Message", "退款查詢失敗"),
                "error_code": "REFUND_QUERY_FAILED"
            }
            
        except Exception as e:
            self.logger.error(f"退款查詢回應解析失敗: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "RESPONSE_PARSE_ERROR"
            }
    
    def _map_refund_status(self, payuni_refund_status: str) -> str:
        """映射PayUni退款狀態到系統狀態"""
        status_mapping = {
            "SUCCESS": "completed",      # 退款成功
            "PROCESSING": "processing",  # 退款處理中
            "FAILED": "failed",         # 退款失敗
            "PENDING": "pending",       # 退款待處理
            "REJECTED": "rejected"      # 退款被拒絕
        }
        
        return status_mapping.get(payuni_refund_status.upper(), "unknown")


class PayUniWebhookHandler:
    """PayUni Webhook處理器"""
    
    def __init__(self, gateway: PayUniGateway):
        self.gateway = gateway
    
    async def handle_payment_notify(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理支付通知"""
        try:
            # 驗證回調
            verification_result = self.gateway.verify_callback(request_data)
            
            if not verification_result["success"]:
                logger.error(f"PayUni通知驗證失敗: {verification_result['error']}")
                return {
                    "success": False,
                    "response": "0|驗證失敗"
                }
            
            trade_data = verification_result["trade_data"]
            payment_status = verification_result["status"]
            
            # 處理支付狀態更新
            await self._update_payment_status(trade_data, payment_status)
            
            logger.info(f"PayUni支付通知處理成功: {trade_data.get('TradeNo', 'Unknown')}")
            
            return {
                "success": True,
                "response": "1|OK"
            }
            
        except Exception as e:
            logger.error(f"PayUni通知處理失敗: {str(e)}")
            return {
                "success": False,
                "response": "0|處理失敗"
            }
    
    async def _update_payment_status(self, trade_data: Dict[str, Any], status: str):
        """更新支付狀態"""
        try:
            # 這裡應該調用支付服務更新狀態
            # 暫時記錄日誌
            logger.info(f"更新支付狀態: {trade_data.get('TradeNo')} -> {status}")
            
            # TODO: 實際實現狀態更新邏輯
            # payment_service.update_payment_status(trade_data['TradeNo'], status, trade_data)
            
        except Exception as e:
            logger.error(f"支付狀態更新失敗: {str(e)}")
            raise


# 工廠函數
def create_payuni_gateway(merchant_id: str, hash_key: str, hash_iv: str, 
                         is_sandbox: bool = True) -> PayUniGateway:
    """創建PayUni閘道實例"""
    config = PayUniConfig(merchant_id, hash_key, hash_iv, is_sandbox)
    return PayUniGateway(config)


def create_payuni_config(merchant_id: str, hash_key: str, hash_iv: str, 
                        is_sandbox: bool = True) -> PayUniConfig:
    """創建PayUni配置實例"""
    return PayUniConfig(merchant_id, hash_key, hash_iv, is_sandbox)