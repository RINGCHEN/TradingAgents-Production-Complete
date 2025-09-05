#!/usr/bin/env python3
"""
阿爾法洞察服務
任務 0.1.1: 實現按次付費基礎架構的核心服務
提供個性化阿爾法洞察推薦、內容管理和用戶互動追蹤
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .pay_per_use_service import PayPerUseService, AccessLevel
from .personality_test_service import PersonalityTestService

logger = logging.getLogger(__name__)

class InsightCategory(Enum):
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    SENTIMENT = "sentiment"
    RISK_MANAGEMENT = "risk_management"
    MARKET_TIMING = "market_timing"

class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class AlphaInsight:
    id: str
    title: str
    description: str
    content: str
    personality_types: List[str]
    price: float
    category: InsightCategory
    difficulty_level: DifficultyLevel
    estimated_read_time: int
    tags: List[str]
    view_count: int
    purchase_count: int
    rating: float
    created_at: datetime
    updated_at: datetime
    is_active: bool

@dataclass
class AlphaPurchase:
    id: str
    user_id: str
    insight_id: str
    payment_id: Optional[str]
    amount: float
    currency: str
    status: str
    payment_method: Optional[str]
    purchased_at: datetime
    unlocked_at: Optional[datetime]

@dataclass
class PersonalizedRecommendation:
    insight: AlphaInsight
    relevance_score: float
    personalization_reason: str
    urgency_level: str
    expected_value: str

class AlphaInsightService:
    """阿爾法洞察服務"""
    
    def __init__(self, db_path: str = "tradingagents.db"):
        self.db_path = db_path
        self.pay_per_use_service = PayPerUseService(db_path)
        self.personality_service = PersonalityTestService(db_path)
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)
    
    async def get_personalized_insights(self, user_id: str, personality_type: str, limit: int = 5) -> List[PersonalizedRecommendation]:
        """獲取個性化阿爾法洞察推薦"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 獲取適合該人格類型的洞察
            cursor.execute("""
                SELECT id, title, description, content, personality_types, price, 
                       category, difficulty_level, estimated_read_time, tags,
                       view_count, purchase_count, rating, created_at, updated_at, is_active
                FROM alpha_insights 
                WHERE is_active = 1 
                AND (personality_types LIKE ? OR personality_types LIKE '%all%')
                ORDER BY rating DESC, purchase_count DESC
                LIMIT ?
            """, (f'%{personality_type}%', limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            recommendations = []
            for row in rows:
                insight = AlphaInsight(
                    id=row[0],
                    title=row[1],
                    description=row[2],
                    content=row[3],
                    personality_types=json.loads(row[4]) if row[4] else [],
                    price=row[5],
                    category=InsightCategory(row[6]),
                    difficulty_level=DifficultyLevel(row[7]),
                    estimated_read_time=row[8],
                    tags=json.loads(row[9]) if row[9] else [],
                    view_count=row[10],
                    purchase_count=row[11],
                    rating=row[12],
                    created_at=datetime.fromisoformat(row[13]) if row[13] else datetime.now(),
                    updated_at=datetime.fromisoformat(row[14]) if row[14] else datetime.now(),
                    is_active=bool(row[15])
                )
                
                # 計算個性化推薦分數
                relevance_score = await self._calculate_relevance_score(insight, personality_type, user_id)
                personalization_reason = await self._generate_personalization_reason(insight, personality_type)
                urgency_level = await self._determine_urgency_level(insight, user_id)
                expected_value = await self._calculate_expected_value(insight, personality_type)
                
                recommendations.append(PersonalizedRecommendation(
                    insight=insight,
                    relevance_score=relevance_score,
                    personalization_reason=personalization_reason,
                    urgency_level=urgency_level,
                    expected_value=expected_value
                ))
            
            # 按相關性分數排序
            recommendations.sort(key=lambda x: x.relevance_score, reverse=True)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"獲取個性化洞察推薦失敗: {e}")
            return []
    
    async def unlock_insight(self, user_id: str, insight_id: str, payment_id: str) -> bool:
        """解鎖阿爾法洞察"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 檢查洞察是否存在
            cursor.execute("SELECT id FROM alpha_insights WHERE id = ? AND is_active = 1", (insight_id,))
            if not cursor.fetchone():
                logger.error(f"洞察 {insight_id} 不存在或已停用")
                return False
            
            # 創建購買記錄
            purchase_id = str(uuid.uuid4())
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO alpha_purchases 
                (id, user_id, insight_id, payment_id, amount, currency, status, 
                 purchased_at, unlocked_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                purchase_id, user_id, insight_id, payment_id, 5.00, 'USD', 
                'completed', now.isoformat(), now.isoformat()
            ))
            
            # 更新洞察統計
            cursor.execute("""
                UPDATE alpha_insights 
                SET purchase_count = purchase_count + 1,
                    updated_at = ?
                WHERE id = ?
            """, (now.isoformat(), insight_id))
            
            conn.commit()
            conn.close()
            
            # 追蹤解鎖事件
            await self.track_insight_engagement(user_id, insight_id, "unlock")
            
            logger.info(f"用戶 {user_id} 成功解鎖洞察 {insight_id}")
            return True
            
        except Exception as e:
            logger.error(f"解鎖洞察失敗: {e}")
            return False
    
    async def get_user_unlocked_insights(self, user_id: str) -> List[AlphaPurchase]:
        """獲取用戶已解鎖的洞察"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, user_id, insight_id, payment_id, amount, currency, 
                       status, payment_method, purchased_at, unlocked_at
                FROM alpha_purchases 
                WHERE user_id = ? AND status = 'completed'
                ORDER BY purchased_at DESC
            """, (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            purchases = []
            for row in rows:
                purchases.append(AlphaPurchase(
                    id=row[0],
                    user_id=row[1],
                    insight_id=row[2],
                    payment_id=row[3],
                    amount=row[4],
                    currency=row[5],
                    status=row[6],
                    payment_method=row[7],
                    purchased_at=datetime.fromisoformat(row[8]) if row[8] else datetime.now(),
                    unlocked_at=datetime.fromisoformat(row[9]) if row[9] else None
                ))
            
            return purchases
            
        except Exception as e:
            logger.error(f"獲取用戶解鎖洞察失敗: {e}")
            return []
    
    async def track_insight_engagement(self, user_id: str, insight_id: str, action: str, action_data: Optional[Dict[str, Any]] = None):
        """追蹤洞察互動"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            engagement_id = str(uuid.uuid4())
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO alpha_engagement 
                (id, user_id, insight_id, action, action_data, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                engagement_id, user_id, insight_id, action, 
                json.dumps(action_data) if action_data else None,
                now.isoformat()
            ))
            
            # 更新洞察瀏覽統計
            if action == "view":
                cursor.execute("""
                    UPDATE alpha_insights 
                    SET view_count = view_count + 1,
                        updated_at = ?
                    WHERE id = ?
                """, (now.isoformat(), insight_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"記錄用戶 {user_id} 對洞察 {insight_id} 的 {action} 行為")
            
        except Exception as e:
            logger.error(f"追蹤洞察互動失敗: {e}")
    
    async def get_insight_analytics(self, insight_id: str) -> Dict[str, Any]:
        """獲取洞察分析數據"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 基礎統計
            cursor.execute("""
                SELECT view_count, purchase_count, rating, created_at
                FROM alpha_insights WHERE id = ?
            """, (insight_id,))
            
            insight_row = cursor.fetchone()
            if not insight_row:
                return {}
            
            # 互動統計
            cursor.execute("""
                SELECT action, COUNT(*) as count
                FROM alpha_engagement 
                WHERE insight_id = ?
                GROUP BY action
            """, (insight_id,))
            
            engagement_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 收入統計
            cursor.execute("""
                SELECT COUNT(*) as purchases, SUM(amount) as revenue
                FROM alpha_purchases 
                WHERE insight_id = ? AND status = 'completed'
            """, (insight_id,))
            
            revenue_row = cursor.fetchone()
            
            conn.close()
            
            return {
                "insight_id": insight_id,
                "view_count": insight_row[0],
                "purchase_count": insight_row[1],
                "rating": insight_row[2],
                "created_at": insight_row[3],
                "engagement_stats": engagement_stats,
                "total_purchases": revenue_row[0] if revenue_row else 0,
                "total_revenue": revenue_row[1] if revenue_row else 0.0,
                "conversion_rate": (revenue_row[0] / insight_row[0]) if insight_row[0] > 0 else 0.0
            }
            
        except Exception as e:
            logger.error(f"獲取洞察分析數據失敗: {e}")
            return {}
    
    async def create_insight(self, insight_data: Dict[str, Any]) -> str:
        """創建新的阿爾法洞察"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            insight_id = str(uuid.uuid4())
            now = datetime.now()
            
            cursor.execute("""
                INSERT INTO alpha_insights 
                (id, title, description, content, personality_types, price, 
                 category, difficulty_level, estimated_read_time, tags, 
                 view_count, purchase_count, rating, created_at, updated_at, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                insight_id,
                insight_data['title'],
                insight_data['description'],
                insight_data['content'],
                json.dumps(insight_data.get('personality_types', [])),
                insight_data.get('price', 5.00),
                insight_data.get('category', 'technical'),
                insight_data.get('difficulty_level', 'intermediate'),
                insight_data.get('estimated_read_time', 10),
                json.dumps(insight_data.get('tags', [])),
                0, 0, 0.0,  # 初始統計
                now.isoformat(), now.isoformat(), True
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功創建阿爾法洞察: {insight_id}")
            return insight_id
            
        except Exception as e:
            logger.error(f"創建阿爾法洞察失敗: {e}")
            return ""
    
    async def _calculate_relevance_score(self, insight: AlphaInsight, personality_type: str, user_id: str) -> float:
        """計算洞察相關性分數"""
        score = 0.0
        
        # 人格匹配度 (40%)
        if personality_type in insight.personality_types or 'all' in insight.personality_types:
            score += 0.4
        
        # 難度匹配度 (20%)
        # 這裡可以根據用戶歷史行為調整
        if insight.difficulty_level == DifficultyLevel.INTERMEDIATE:
            score += 0.2
        
        # 熱門度 (20%)
        if insight.purchase_count > 50:
            score += 0.2
        elif insight.purchase_count > 20:
            score += 0.1
        
        # 評分 (20%)
        if insight.rating >= 4.0:
            score += 0.2
        elif insight.rating >= 3.5:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _generate_personalization_reason(self, insight: AlphaInsight, personality_type: str) -> str:
        """生成個性化推薦理由"""
        reasons = {
            "conservative": f"基於您的保守型投資風格，這個{insight.category.value}洞察將幫助您更好地控制風險",
            "aggressive": f"適合您的積極型投資策略，這個{insight.category.value}洞察提供高成長機會分析",
            "balanced": f"符合您的平衡型投資理念，這個{insight.category.value}洞察提供全面的風險收益分析",
            "value": f"針對您的價值投資偏好，這個{insight.category.value}洞察深度挖掘被低估的投資機會"
        }
        
        return reasons.get(personality_type, f"這個{insight.category.value}洞察為您提供專業的投資分析")
    
    async def _determine_urgency_level(self, insight: AlphaInsight, user_id: str) -> str:
        """確定緊急程度"""
        # 基於洞察的時效性和用戶行為確定緊急程度
        days_since_created = (datetime.now() - insight.created_at).days
        
        if days_since_created <= 1:
            return "high"
        elif days_since_created <= 7:
            return "medium"
        else:
            return "low"
    
    async def _calculate_expected_value(self, insight: AlphaInsight, personality_type: str) -> str:
        """計算預期價值"""
        # 基於洞察類型和用戶人格計算預期價值描述
        value_descriptions = {
            "technical": "技術分析優勢，提升交易時機把握",
            "fundamental": "基本面深度洞察，發現價值投資機會", 
            "sentiment": "市場情緒分析，掌握群眾心理動向",
            "risk_management": "風險控制策略，保護投資組合",
            "market_timing": "市場時機判斷，優化進出場點"
        }
        
        return value_descriptions.get(insight.category.value, "專業投資洞察，提升投資決策質量")