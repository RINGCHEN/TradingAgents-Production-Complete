#!/usr/bin/env python3
"""
智能升級推薦服務
任務 0.1.2: 開發智能升級推薦系統
基於用戶行為和消費模式提供個性化升級推薦
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

class UpgradeRecommendationType(Enum):
    MONTHLY_THRESHOLD = "monthly_threshold"  # 月消費達門檻
    USAGE_PATTERN = "usage_pattern"  # 使用模式分析
    ENGAGEMENT_LEVEL = "engagement_level"  # 互動程度
    SEASONAL_PROMOTION = "seasonal_promotion"  # 季節性促銷
    PERSONALIZED_OFFER = "personalized_offer"  # 個性化優惠

class UpgradeStatus(Enum):
    PENDING = "pending"
    SHOWN = "shown"
    CLICKED = "clicked"
    CONVERTED = "converted"
    DISMISSED = "dismissed"
    EXPIRED = "expired"

@dataclass
class UpgradeRecommendation:
    id: str
    user_id: str
    recommendation_type: UpgradeRecommendationType
    trigger_data: Dict[str, Any]
    recommended_tier: str
    discount_percentage: float
    discount_amount: float
    expires_at: datetime
    personalized_message: str
    value_proposition: List[str]
    urgency_message: str
    status: UpgradeStatus
    created_at: datetime

@dataclass
class UserSpendingPattern:
    user_id: str
    monthly_spending: float
    transaction_frequency: float
    avg_transaction_amount: float
    preferred_insight_types: List[str]
    engagement_score: float
    days_since_first_purchase: int
    total_lifetime_spending: float

@dataclass
class ConversionFunnelData:
    step: str
    user_count: int
    conversion_rate: float
    avg_time_to_next_step: float
    drop_off_reasons: List[str]

class UpgradeRecommendationService:
    """智能升級推薦服務"""
    
    def __init__(self, db_path: str = "tradingagents.db"):
        self.db_path = db_path
        
        # 升級門檻配置
        self.MONTHLY_THRESHOLD = 50.0  # $50 月消費門檻
        self.DIAMOND_MONTHLY_PRICE = 99.0  # Diamond 月費
        self.ENGAGEMENT_THRESHOLD = 0.7  # 互動分數門檻
        
        # 折扣策略配置
        self.DISCOUNT_TIERS = {
            "first_time": {"percentage": 30, "message": "首次升級專享"},
            "high_engagement": {"percentage": 25, "message": "活躍用戶特惠"},
            "threshold_reached": {"percentage": 20, "message": "消費達標優惠"},
            "seasonal": {"percentage": 15, "message": "限時優惠"}
        }
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)
    
    async def analyze_user_spending_pattern(self, user_id: str) -> UserSpendingPattern:
        """分析用戶消費模式"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 獲取用戶月度消費數據
            cursor.execute("""
                SELECT total_amount, transaction_count, unique_insights_purchased,
                       created_at
                FROM user_monthly_spending 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 3
            """, (user_id,))
            
            monthly_data = cursor.fetchall()
            
            # 獲取用戶所有購買記錄
            cursor.execute("""
                SELECT ap.amount, ap.purchased_at, ai.category, ai.difficulty_level
                FROM alpha_purchases ap
                JOIN alpha_insights ai ON ap.insight_id = ai.id
                WHERE ap.user_id = ? AND ap.status = 'completed'
                ORDER BY ap.purchased_at DESC
            """, (user_id,))
            
            purchase_data = cursor.fetchall()
            
            # 獲取用戶互動數據
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM alpha_engagement 
                WHERE user_id = ?
                GROUP BY action
            """, (user_id,))
            
            engagement_data = cursor.fetchall()
            
            conn.close()
            
            # 計算消費模式指標
            monthly_spending = monthly_data[0][0] if monthly_data else 0.0
            transaction_frequency = len(purchase_data) / max(1, len(monthly_data))
            avg_transaction_amount = sum(p[0] for p in purchase_data) / max(1, len(purchase_data))
            
            # 分析偏好的洞察類型
            category_counts = {}
            for purchase in purchase_data:
                category = purchase[2]
                category_counts[category] = category_counts.get(category, 0) + 1
            
            preferred_types = sorted(category_counts.keys(), 
                                   key=lambda x: category_counts[x], reverse=True)[:3]
            
            # 計算互動分數
            engagement_score = self._calculate_engagement_score(engagement_data)
            
            # 計算用戶生命週期
            days_since_first = 0
            total_spending = sum(p[0] for p in purchase_data)
            
            if purchase_data:
                first_purchase = datetime.fromisoformat(purchase_data[-1][1])
                days_since_first = (datetime.now() - first_purchase).days
            
            return UserSpendingPattern(
                user_id=user_id,
                monthly_spending=monthly_spending,
                transaction_frequency=transaction_frequency,
                avg_transaction_amount=avg_transaction_amount,
                preferred_insight_types=preferred_types,
                engagement_score=engagement_score,
                days_since_first_purchase=days_since_first,
                total_lifetime_spending=total_spending
            )
            
        except Exception as e:
            logger.error(f"分析用戶消費模式失敗: {e}")
            return UserSpendingPattern(
                user_id=user_id, monthly_spending=0.0, transaction_frequency=0.0,
                avg_transaction_amount=0.0, preferred_insight_types=[],
                engagement_score=0.0, days_since_first_purchase=0, total_lifetime_spending=0.0
            )
    
    async def check_upgrade_triggers(self, user_id: str) -> List[UpgradeRecommendation]:
        """檢查升級觸發條件"""
        try:
            pattern = await self.analyze_user_spending_pattern(user_id)
            recommendations = []
            
            # 1. 月消費門檻觸發
            if pattern.monthly_spending >= self.MONTHLY_THRESHOLD:
                rec = await self._create_threshold_recommendation(user_id, pattern)
                if rec:
                    recommendations.append(rec)
            
            # 2. 高互動用戶觸發
            if pattern.engagement_score >= self.ENGAGEMENT_THRESHOLD:
                rec = await self._create_engagement_recommendation(user_id, pattern)
                if rec:
                    recommendations.append(rec)
            
            # 3. 使用模式觸發
            if pattern.transaction_frequency >= 2.0:  # 每月2次以上購買
                rec = await self._create_usage_pattern_recommendation(user_id, pattern)
                if rec:
                    recommendations.append(rec)
            
            # 4. 個性化優惠觸發
            if pattern.total_lifetime_spending >= 20.0:  # 累計消費$20以上
                rec = await self._create_personalized_offer(user_id, pattern)
                if rec:
                    recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"檢查升級觸發條件失敗: {e}")
            return []
    
    async def _create_threshold_recommendation(self, user_id: str, pattern: UserSpendingPattern) -> Optional[UpgradeRecommendation]:
        """創建月消費門檻推薦"""
        try:
            # 檢查是否已經推薦過
            if await self._has_recent_recommendation(user_id, UpgradeRecommendationType.MONTHLY_THRESHOLD):
                return None
            
            # 計算節省金額
            monthly_savings = pattern.monthly_spending - self.DIAMOND_MONTHLY_PRICE
            discount_config = self.DISCOUNT_TIERS["threshold_reached"]
            
            recommendation = UpgradeRecommendation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                recommendation_type=UpgradeRecommendationType.MONTHLY_THRESHOLD,
                trigger_data={
                    "monthly_spending": pattern.monthly_spending,
                    "threshold": self.MONTHLY_THRESHOLD,
                    "potential_savings": monthly_savings
                },
                recommended_tier="DIAMOND",
                discount_percentage=discount_config["percentage"],
                discount_amount=self.DIAMOND_MONTHLY_PRICE * discount_config["percentage"] / 100,
                expires_at=datetime.now() + timedelta(days=7),
                personalized_message=f"您本月已消費 ${pattern.monthly_spending:.0f}，升級 Diamond 每月只需 ${self.DIAMOND_MONTHLY_PRICE:.0f}，立即節省成本！",
                value_proposition=[
                    f"每月節省 ${monthly_savings:.0f} 以上",
                    "無限制訪問所有阿爾法洞察",
                    "專屬投資策略和市場分析",
                    "優先客戶支援服務"
                ],
                urgency_message=f"{discount_config['message']} - 限時 7 天",
                status=UpgradeStatus.PENDING,
                created_at=datetime.now()
            )
            
            await self._save_recommendation(recommendation)
            return recommendation
            
        except Exception as e:
            logger.error(f"創建門檻推薦失敗: {e}")
            return None
    
    async def _create_engagement_recommendation(self, user_id: str, pattern: UserSpendingPattern) -> Optional[UpgradeRecommendation]:
        """創建高互動用戶推薦"""
        try:
            if await self._has_recent_recommendation(user_id, UpgradeRecommendationType.ENGAGEMENT_LEVEL):
                return None
            
            discount_config = self.DISCOUNT_TIERS["high_engagement"]
            
            recommendation = UpgradeRecommendation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                recommendation_type=UpgradeRecommendationType.ENGAGEMENT_LEVEL,
                trigger_data={
                    "engagement_score": pattern.engagement_score,
                    "threshold": self.ENGAGEMENT_THRESHOLD
                },
                recommended_tier="DIAMOND",
                discount_percentage=discount_config["percentage"],
                discount_amount=self.DIAMOND_MONTHLY_PRICE * discount_config["percentage"] / 100,
                expires_at=datetime.now() + timedelta(days=5),
                personalized_message=f"感謝您的積極參與！作為活躍用戶，享受專屬 {discount_config['percentage']}% 折扣升級 Diamond 會員",
                value_proposition=[
                    "活躍用戶專屬優惠",
                    "解鎖所有高級功能",
                    "個性化投資建議",
                    "專屬社群和活動"
                ],
                urgency_message=f"{discount_config['message']} - 限時 5 天",
                status=UpgradeStatus.PENDING,
                created_at=datetime.now()
            )
            
            await self._save_recommendation(recommendation)
            return recommendation
            
        except Exception as e:
            logger.error(f"創建互動推薦失敗: {e}")
            return None
    
    async def _create_usage_pattern_recommendation(self, user_id: str, pattern: UserSpendingPattern) -> Optional[UpgradeRecommendation]:
        """創建使用模式推薦"""
        try:
            if await self._has_recent_recommendation(user_id, UpgradeRecommendationType.USAGE_PATTERN):
                return None
            
            # 基於使用頻率計算個性化折扣
            frequency_multiplier = min(pattern.transaction_frequency / 2.0, 1.5)
            base_discount = 15
            dynamic_discount = min(base_discount * frequency_multiplier, 25)
            
            recommendation = UpgradeRecommendation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                recommendation_type=UpgradeRecommendationType.USAGE_PATTERN,
                trigger_data={
                    "transaction_frequency": pattern.transaction_frequency,
                    "preferred_types": pattern.preferred_insight_types
                },
                recommended_tier="DIAMOND",
                discount_percentage=dynamic_discount,
                discount_amount=self.DIAMOND_MONTHLY_PRICE * dynamic_discount / 100,
                expires_at=datetime.now() + timedelta(days=10),
                personalized_message=f"基於您對 {', '.join(pattern.preferred_insight_types[:2])} 洞察的偏好，為您量身定制升級方案",
                value_proposition=[
                    f"專注於您喜愛的 {', '.join(pattern.preferred_insight_types[:2])} 分析",
                    "無限制訪問相關洞察",
                    "個性化內容推薦",
                    f"享受 {dynamic_discount:.0f}% 折扣優惠"
                ],
                urgency_message="個性化優惠 - 限時 10 天",
                status=UpgradeStatus.PENDING,
                created_at=datetime.now()
            )
            
            await self._save_recommendation(recommendation)
            return recommendation
            
        except Exception as e:
            logger.error(f"創建使用模式推薦失敗: {e}")
            return None
    
    async def _create_personalized_offer(self, user_id: str, pattern: UserSpendingPattern) -> Optional[UpgradeRecommendation]:
        """創建個性化優惠"""
        try:
            if await self._has_recent_recommendation(user_id, UpgradeRecommendationType.PERSONALIZED_OFFER):
                return None
            
            # 基於用戶價值計算折扣
            user_value_score = min(pattern.total_lifetime_spending / 100.0, 1.0)
            discount_percentage = 10 + (user_value_score * 15)  # 10-25% 折扣
            
            recommendation = UpgradeRecommendation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                recommendation_type=UpgradeRecommendationType.PERSONALIZED_OFFER,
                trigger_data={
                    "lifetime_spending": pattern.total_lifetime_spending,
                    "user_value_score": user_value_score
                },
                recommended_tier="DIAMOND",
                discount_percentage=discount_percentage,
                discount_amount=self.DIAMOND_MONTHLY_PRICE * discount_percentage / 100,
                expires_at=datetime.now() + timedelta(days=14),
                personalized_message=f"感謝您累計 ${pattern.total_lifetime_spending:.0f} 的支持！專屬 {discount_percentage:.0f}% 折扣等您升級",
                value_proposition=[
                    f"忠實用戶專享 {discount_percentage:.0f}% 折扣",
                    "解鎖所有高級功能",
                    "VIP 客戶專屬服務",
                    "優先獲得新功能體驗"
                ],
                urgency_message="忠實用戶專屬 - 限時 14 天",
                status=UpgradeStatus.PENDING,
                created_at=datetime.now()
            )
            
            await self._save_recommendation(recommendation)
            return recommendation
            
        except Exception as e:
            logger.error(f"創建個性化優惠失敗: {e}")
            return None
    
    async def _has_recent_recommendation(self, user_id: str, rec_type: UpgradeRecommendationType, days: int = 30) -> bool:
        """檢查是否有近期推薦"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT COUNT(*) FROM upgrade_recommendations 
                WHERE user_id = ? AND recommendation_type = ? 
                AND created_at > ?
            """, (user_id, rec_type.value, cutoff_date.isoformat()))
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"檢查近期推薦失敗: {e}")
            return False
    
    async def _save_recommendation(self, recommendation: UpgradeRecommendation):
        """保存推薦記錄"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO upgrade_recommendations 
                (id, user_id, recommendation_type, trigger_data, recommended_tier,
                 discount_percentage, discount_amount, expires_at, personalized_message,
                 value_proposition, urgency_message, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recommendation.id, recommendation.user_id, recommendation.recommendation_type.value,
                json.dumps(recommendation.trigger_data), recommendation.recommended_tier,
                recommendation.discount_percentage, recommendation.discount_amount,
                recommendation.expires_at.isoformat(), recommendation.personalized_message,
                json.dumps(recommendation.value_proposition), recommendation.urgency_message,
                recommendation.status.value, recommendation.created_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"保存升級推薦: {recommendation.id} for user {recommendation.user_id}")
            
        except Exception as e:
            logger.error(f"保存推薦記錄失敗: {e}")
    
    def _calculate_engagement_score(self, engagement_data: List[tuple]) -> float:
        """計算用戶互動分數"""
        if not engagement_data:
            return 0.0
        
        # 不同行為的權重
        action_weights = {
            "view": 0.1,
            "preview": 0.2,
            "purchase_click": 0.3,
            "unlock": 0.4,
            "read_complete": 0.5,
            "like": 0.3,
            "share": 0.4,
            "bookmark": 0.2
        }
        
        total_score = 0.0
        total_actions = 0
        
        for action, count in engagement_data:
            weight = action_weights.get(action, 0.1)
            total_score += count * weight
            total_actions += count
        
        # 標準化分數到 0-1 範圍
        if total_actions == 0:
            return 0.0
        
        avg_score = total_score / total_actions
        return min(avg_score, 1.0)
    
    async def track_recommendation_interaction(self, recommendation_id: str, action: str, additional_data: Optional[Dict[str, Any]] = None):
        """追蹤推薦互動"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 更新推薦狀態
            status_mapping = {
                "shown": UpgradeStatus.SHOWN,
                "clicked": UpgradeStatus.CLICKED,
                "converted": UpgradeStatus.CONVERTED,
                "dismissed": UpgradeStatus.DISMISSED
            }
            
            new_status = status_mapping.get(action, UpgradeStatus.PENDING)
            
            cursor.execute("""
                UPDATE upgrade_recommendations 
                SET status = ?, updated_at = ?
                WHERE id = ?
            """, (new_status.value, datetime.now().isoformat(), recommendation_id))
            
            # 記錄互動事件
            interaction_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO upgrade_recommendation_interactions 
                (id, recommendation_id, action, interaction_data, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                interaction_id, recommendation_id, action,
                json.dumps(additional_data) if additional_data else None,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"追蹤推薦互動: {recommendation_id} - {action}")
            
        except Exception as e:
            logger.error(f"追蹤推薦互動失敗: {e}")
    
    async def get_user_recommendations(self, user_id: str, active_only: bool = True) -> List[UpgradeRecommendation]:
        """獲取用戶推薦"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, user_id, recommendation_type, trigger_data, recommended_tier,
                       discount_percentage, discount_amount, expires_at, personalized_message,
                       value_proposition, urgency_message, status, created_at
                FROM upgrade_recommendations 
                WHERE user_id = ?
            """
            
            params = [user_id]
            
            if active_only:
                query += " AND status IN ('pending', 'shown') AND expires_at > ?"
                params.append(datetime.now().isoformat())
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()
            
            recommendations = []
            for row in rows:
                rec = UpgradeRecommendation(
                    id=row[0],
                    user_id=row[1],
                    recommendation_type=UpgradeRecommendationType(row[2]),
                    trigger_data=json.loads(row[3]) if row[3] else {},
                    recommended_tier=row[4],
                    discount_percentage=row[5],
                    discount_amount=row[6],
                    expires_at=datetime.fromisoformat(row[7]),
                    personalized_message=row[8],
                    value_proposition=json.loads(row[9]) if row[9] else [],
                    urgency_message=row[10],
                    status=UpgradeStatus(row[11]),
                    created_at=datetime.fromisoformat(row[12])
                )
                recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"獲取用戶推薦失敗: {e}")
            return []
    
    async def analyze_conversion_funnel(self, days: int = 30) -> List[ConversionFunnelData]:
        """分析轉換漏斗"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 分析推薦到轉換的漏斗
            funnel_steps = [
                ("推薦生成", "SELECT COUNT(DISTINCT user_id) FROM upgrade_recommendations WHERE created_at > ?"),
                ("推薦展示", "SELECT COUNT(DISTINCT user_id) FROM upgrade_recommendations WHERE status IN ('shown', 'clicked', 'converted') AND created_at > ?"),
                ("用戶點擊", "SELECT COUNT(DISTINCT user_id) FROM upgrade_recommendations WHERE status IN ('clicked', 'converted') AND created_at > ?"),
                ("成功轉換", "SELECT COUNT(DISTINCT user_id) FROM upgrade_recommendations WHERE status = 'converted' AND created_at > ?")
            ]
            
            funnel_data = []
            prev_count = None
            
            for step_name, query in funnel_steps:
                cursor.execute(query, (cutoff_date.isoformat(),))
                count = cursor.fetchone()[0]
                
                conversion_rate = 0.0
                if prev_count is not None and prev_count > 0:
                    conversion_rate = count / prev_count
                
                funnel_data.append(ConversionFunnelData(
                    step=step_name,
                    user_count=count,
                    conversion_rate=conversion_rate,
                    avg_time_to_next_step=0.0,  # 可以進一步計算
                    drop_off_reasons=[]  # 可以進一步分析
                ))
                
                prev_count = count
            
            conn.close()
            return funnel_data
            
        except Exception as e:
            logger.error(f"分析轉換漏斗失敗: {e}")
            return []
    
    async def get_recommendation_analytics(self, days: int = 30) -> Dict[str, Any]:
        """獲取推薦分析數據"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 總體統計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_recommendations,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(discount_percentage) as avg_discount,
                    SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as conversions
                FROM upgrade_recommendations 
                WHERE created_at > ?
            """, (cutoff_date.isoformat(),))
            
            overall_stats = cursor.fetchone()
            
            # 按類型統計
            cursor.execute("""
                SELECT 
                    recommendation_type,
                    COUNT(*) as count,
                    SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) as conversions,
                    AVG(discount_percentage) as avg_discount
                FROM upgrade_recommendations 
                WHERE created_at > ?
                GROUP BY recommendation_type
            """, (cutoff_date.isoformat(),))
            
            type_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                "period_days": days,
                "total_recommendations": overall_stats[0],
                "unique_users": overall_stats[1],
                "avg_discount_percentage": overall_stats[2] or 0.0,
                "total_conversions": overall_stats[3],
                "overall_conversion_rate": (overall_stats[3] / max(1, overall_stats[0])) * 100,
                "by_type": [
                    {
                        "type": row[0],
                        "count": row[1],
                        "conversions": row[2],
                        "conversion_rate": (row[2] / max(1, row[1])) * 100,
                        "avg_discount": row[3] or 0.0
                    }
                    for row in type_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"獲取推薦分析數據失敗: {e}")
            return {}