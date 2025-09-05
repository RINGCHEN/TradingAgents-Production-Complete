#!/usr/bin/env python3
"""
按次付費服務
處理阿爾法洞察的按次付費購買和訪問控制
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class AccessLevel(Enum):
    BASIC = "basic"
    STANDARD = "standard"
    ALPHA = "alpha"

@dataclass
class AlphaInsight:
    id: str
    stock_id: str
    insight_type: str
    analyst_id: str
    standard_content: Dict[str, Any]
    alpha_content: Dict[str, Any]
    confidence_score: float
    target_price: Optional[float]
    created_at: datetime
    is_active: bool

@dataclass
class PayPerUseTransaction:
    id: str
    user_id: int
    insight_id: str
    amount: float
    payment_status: PaymentStatus
    access_granted_at: Optional[datetime]
    access_expires_at: Optional[datetime]
    access_count: int
    created_at: datetime

@dataclass
class AccessResult:
    granted: bool
    reason: str
    content: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    upgrade_suggestion: Optional[Dict[str, Any]] = None
    purchase_option: Optional[Dict[str, Any]] = None

class PayPerUseService:
    """按次付費服務"""
    
    def __init__(self, db_path: str = "tradingagents.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)
    
    async def get_alpha_insight(self, stock_id: str, insight_type: str) -> Optional[AlphaInsight]:
        """獲取阿爾法洞察"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, stock_id, insight_type, analyst_id, standard_content, 
                       alpha_content, confidence_score, target_price, created_at, is_active
                FROM alpha_insights 
                WHERE stock_id = ? AND insight_type = ? AND is_active = 1
                ORDER BY created_at DESC LIMIT 1
            """, (stock_id, insight_type))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return AlphaInsight(
                    id=row[0],
                    stock_id=row[1],
                    insight_type=row[2],
                    analyst_id=row[3],
                    standard_content=json.loads(row[4]),
                    alpha_content=json.loads(row[5]),
                    confidence_score=row[6],
                    target_price=row[7],
                    created_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    is_active=bool(row[9])
                )
            return None
            
        except Exception as e:
            logger.error(f"獲取阿爾法洞察失敗: {e}")
            return None
    
    async def check_existing_purchase(self, user_id: int, insight_id: str) -> Optional[PayPerUseTransaction]:
        """檢查是否已購買該洞察"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, insight_id, amount, payment_status,
                       access_granted_at, access_expires_at, access_count, created_at
                FROM pay_per_use_transactions 
                WHERE user_id = ? AND insight_id = ? AND payment_status = 'completed'
                ORDER BY created_at DESC LIMIT 1
            """, (user_id, insight_id))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return PayPerUseTransaction(
                    id=row[0],
                    user_id=row[1],
                    insight_id=row[2],
                    amount=row[3],
                    payment_status=PaymentStatus(row[4]),
                    access_granted_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    access_expires_at=datetime.fromisoformat(row[6]) if row[6] else None,
                    access_count=row[7],
                    created_at=datetime.fromisoformat(row[8])
                )
            return None
            
        except Exception as e:
            logger.error(f"檢查購買記錄失敗: {e}")
            return None
    
    async def purchase_alpha_insight(self, user_id: int, stock_id: str, insight_type: str) -> Dict[str, Any]:
        """購買阿爾法洞察"""
        try:
            # 1. 獲取洞察內容
            insight = await self.get_alpha_insight(stock_id, insight_type)
            if not insight:
                return {
                    "success": False,
                    "error": "洞察內容不可用",
                    "code": "INSIGHT_NOT_FOUND"
                }
            
            # 2. 檢查是否已購買
            existing = await self.check_existing_purchase(user_id, insight.id)
            if existing and existing.access_expires_at and existing.access_expires_at > datetime.now():
                return {
                    "success": True,
                    "message": "已購買該洞察",
                    "transaction_id": existing.id,
                    "access_expires_at": existing.access_expires_at.isoformat(),
                    "already_purchased": True
                }
            
            # 3. 創建購買記錄
            transaction_id = str(uuid.uuid4())
            access_granted_at = datetime.now()
            access_expires_at = access_granted_at + timedelta(days=7)  # 7天訪問期
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pay_per_use_transactions 
                (id, user_id, insight_id, amount, payment_status, 
                 access_granted_at, access_expires_at, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id, user_id, insight.id, 5.00, 'completed',
                access_granted_at.isoformat(), access_expires_at.isoformat(), 0
            ))
            
            conn.commit()
            conn.close()
            
            # 4. 更新月度消費統計
            await self.update_monthly_spending(user_id, 5.00)
            
            # 5. 檢查升級推薦
            await self.check_upgrade_recommendation(user_id)
            
            return {
                "success": True,
                "message": "購買成功",
                "transaction_id": transaction_id,
                "amount": 5.00,
                "access_expires_at": access_expires_at.isoformat(),
                "insight": {
                    "id": insight.id,
                    "stock_id": insight.stock_id,
                    "insight_type": insight.insight_type,
                    "confidence_score": insight.confidence_score,
                    "target_price": insight.target_price
                }
            }
            
        except Exception as e:
            logger.error(f"購買阿爾法洞察失敗: {e}")
            return {
                "success": False,
                "error": "購買處理失敗",
                "code": "PURCHASE_ERROR"
            }
    
    async def get_insight_content(self, user_id: int, stock_id: str, insight_type: str, 
                                access_level: AccessLevel = AccessLevel.BASIC) -> AccessResult:
        """獲取洞察內容（根據用戶權限）"""
        try:
            # 1. 獲取洞察
            insight = await self.get_alpha_insight(stock_id, insight_type)
            if not insight:
                return AccessResult(
                    granted=False,
                    reason="INSIGHT_NOT_FOUND",
                    content=None
                )
            
            # 2. 基礎內容：所有用戶都可訪問
            if access_level == AccessLevel.BASIC:
                basic_content = self.mask_content_for_free_user(insight.standard_content)
                return AccessResult(
                    granted=True,
                    reason="basic_access",
                    content=basic_content,
                    upgrade_suggestion=self.generate_upgrade_suggestion(insight)
                )
            
            # 3. 阿爾法內容：需要購買或會員權限
            elif access_level == AccessLevel.ALPHA:
                # 檢查按次付費權限
                purchase = await self.check_existing_purchase(user_id, insight.id)
                if purchase and purchase.access_expires_at and purchase.access_expires_at > datetime.now():
                    # 記錄訪問
                    await self.record_access(purchase.id)
                    
                    return AccessResult(
                        granted=True,
                        reason="pay_per_use",
                        content={
                            **insight.standard_content,
                            "alpha_insights": insight.alpha_content,
                            "access_level": "alpha"
                        },
                        expires_at=purchase.access_expires_at
                    )
                else:
                    # 無權限：提供購買選項
                    return AccessResult(
                        granted=False,
                        reason="alpha_access_required",
                        content=self.mask_content_for_free_user(insight.standard_content),
                        purchase_option=self.generate_purchase_option(insight),
                        upgrade_suggestion=self.generate_upgrade_suggestion(insight)
                    )
            
            # 4. 標準內容：GOLD會員權限
            else:  # AccessLevel.STANDARD
                return AccessResult(
                    granted=True,
                    reason="standard_access",
                    content=insight.standard_content,
                    upgrade_suggestion=self.generate_alpha_upgrade_suggestion(insight)
                )
                
        except Exception as e:
            logger.error(f"獲取洞察內容失敗: {e}")
            return AccessResult(
                granted=False,
                reason="SYSTEM_ERROR",
                content=None
            )
    
    def mask_content_for_free_user(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """為免費用戶模糊化內容"""
        return {
            "recommendation": "***",
            "confidence": content.get("confidence", 0),
            "reasoning": [
                "基於多項技術指標分析...",
                "綜合市場條件評估...",
                "*** (購買完整分析)"
            ],
            "target_price": None,
            "access_level": "basic",
            "upgrade_required": True
        }
    
    def generate_purchase_option(self, insight: AlphaInsight) -> Dict[str, Any]:
        """生成購買選項"""
        return {
            "price": 5.00,
            "currency": "USD",
            "access_duration": "7天",
            "title": f"解鎖 {insight.stock_id} 阿爾法洞察",
            "description": "獲得深度量化分析和專業投資建議",
            "benefits": [
                "機構級投資洞察",
                "量化風險評估",
                "競爭優勢分析",
                "7天內可重複查看"
            ]
        }
    
    def generate_upgrade_suggestion(self, insight: AlphaInsight) -> Dict[str, Any]:
        """生成升級建議"""
        return {
            "title": "升級至鑽石會員",
            "description": "無限制訪問所有阿爾法洞察",
            "benefits": [
                "無限制阿爾法洞察訪問",
                "歷史數據分析",
                "個性化投資建議",
                "優先客戶支援"
            ],
            "cta": "立即升級",
            "monthly_savings": "每月可節省超過$50"
        }
    
    def generate_alpha_upgrade_suggestion(self, insight: AlphaInsight) -> Dict[str, Any]:
        """生成阿爾法升級建議"""
        return {
            "title": "解鎖阿爾法洞察",
            "description": "獲得更深入的投資分析",
            "options": [
                {
                    "type": "pay_per_use",
                    "price": 5.00,
                    "title": "單次購買",
                    "description": "7天訪問期"
                },
                {
                    "type": "upgrade",
                    "title": "升級至鑽石會員",
                    "description": "無限制訪問"
                }
            ]
        }
    
    async def record_access(self, transaction_id: str):
        """記錄訪問"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE pay_per_use_transactions 
                SET access_count = access_count + 1, 
                    last_accessed_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), transaction_id))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"記錄訪問失敗: {e}")
    
    async def update_monthly_spending(self, user_id: int, amount: float):
        """更新月度消費統計"""
        try:
            now = datetime.now()
            year, month = now.year, now.month
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 檢查是否存在記錄
            cursor.execute("""
                SELECT id, total_amount, transaction_count, unique_insights_purchased
                FROM user_monthly_spending 
                WHERE user_id = ? AND year = ? AND month = ?
            """, (user_id, year, month))
            
            row = cursor.fetchone()
            
            if row:
                # 更新現有記錄
                new_total = row[1] + amount
                new_count = row[2] + 1
                new_unique = row[3] + 1
                
                cursor.execute("""
                    UPDATE user_monthly_spending 
                    SET total_amount = ?, transaction_count = ?, 
                        unique_insights_purchased = ?, updated_at = ?
                    WHERE id = ?
                """, (new_total, new_count, new_unique, datetime.now().isoformat(), row[0]))
            else:
                # 創建新記錄
                cursor.execute("""
                    INSERT INTO user_monthly_spending 
                    (id, user_id, year, month, total_amount, transaction_count, unique_insights_purchased)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (str(uuid.uuid4()), user_id, year, month, amount, 1, 1))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"更新月度消費統計失敗: {e}")
    
    async def check_upgrade_recommendation(self, user_id: int):
        """檢查升級推薦觸發"""
        try:
            now = datetime.now()
            year, month = now.year, now.month
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 獲取當月消費
            cursor.execute("""
                SELECT total_amount, upgrade_threshold_reached
                FROM user_monthly_spending 
                WHERE user_id = ? AND year = ? AND month = ?
            """, (user_id, year, month))
            
            row = cursor.fetchone()
            
            if row and row[0] >= 50.0 and not row[1]:
                # 達到$50門檻且未推薦過
                cursor.execute("""
                    UPDATE user_monthly_spending 
                    SET upgrade_threshold_reached = 1, upgrade_recommended_at = ?
                    WHERE user_id = ? AND year = ? AND month = ?
                """, (datetime.now().isoformat(), user_id, year, month))
                
                # 創建升級推薦記錄
                cursor.execute("""
                    INSERT INTO upgrade_recommendations 
                    (id, user_id, trigger_type, trigger_amount, trigger_date, recommended_tier)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), user_id, 'monthly_threshold', 
                    row[0], datetime.now().isoformat(), 'DIAMOND'
                ))
                
                conn.commit()
                logger.info(f"用戶 {user_id} 達到升級推薦門檻: ${row[0]}")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"檢查升級推薦失敗: {e}")
    
    async def get_user_spending_summary(self, user_id: int) -> Dict[str, Any]:
        """獲取用戶消費摘要"""
        try:
            now = datetime.now()
            year, month = now.year, now.month
            
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 獲取當月消費
            cursor.execute("""
                SELECT total_amount, transaction_count, unique_insights_purchased,
                       upgrade_threshold_reached, upgrade_converted
                FROM user_monthly_spending 
                WHERE user_id = ? AND year = ? AND month = ?
            """, (user_id, year, month))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "monthly_spending": row[0],
                    "monthly_transactions": row[1],
                    "unique_insights": row[2],
                    "upgrade_threshold_reached": bool(row[3]),
                    "upgrade_converted": bool(row[4]),
                    "remaining_to_threshold": max(0, 50.0 - row[0])
                }
            else:
                return {
                    "monthly_spending": 0.0,
                    "monthly_transactions": 0,
                    "unique_insights": 0,
                    "upgrade_threshold_reached": False,
                    "upgrade_converted": False,
                    "remaining_to_threshold": 50.0
                }
            
        except Exception as e:
            logger.error(f"獲取用戶消費摘要失敗: {e}")
            return {
                "monthly_spending": 0.0,
                "monthly_transactions": 0,
                "unique_insights": 0,
                "upgrade_threshold_reached": False,
                "upgrade_converted": False,
                "remaining_to_threshold": 50.0
            }