#!/usr/bin/env python3
"""
價值驗證數據收集服務
任務 0.1.3: 建立價值驗證數據收集
追蹤用戶行為、分析付費意願、收集市場反饋並優化定價策略
"""

import logging
import sqlite3
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    RATING = "rating"
    COMMENT = "comment"
    SURVEY = "survey"
    COMPLAINT = "complaint"
    SUGGESTION = "suggestion"
    TESTIMONIAL = "testimonial"

class PaymentWillingnessLevel(Enum):
    VERY_LOW = "very_low"      # 0-20%
    LOW = "low"                # 21-40%
    MEDIUM = "medium"          # 41-60%
    HIGH = "high"              # 61-80%
    VERY_HIGH = "very_high"    # 81-100%

@dataclass
class InsightPopularityData:
    insight_id: str
    title: str
    category: str
    difficulty_level: str
    personality_types: List[str]
    view_count: int
    purchase_count: int
    conversion_rate: float
    avg_rating: float
    total_revenue: float
    engagement_score: float
    retention_rate: float

@dataclass
class UserPaymentWillingness:
    user_id: str
    personality_type: str
    willingness_level: PaymentWillingnessLevel
    max_willing_price: float
    preferred_payment_model: str  # per_use, subscription, bundle
    price_sensitivity_score: float
    value_perception_score: float
    purchase_frequency: float
    avg_session_value: float

@dataclass
class MarketFeedback:
    id: str
    user_id: str
    feedback_type: FeedbackType
    content: str
    rating: Optional[int]
    insight_id: Optional[str]
    context_data: Dict[str, Any]
    sentiment_score: float
    created_at: datetime

@dataclass
class PricingOptimizationData:
    current_price: float
    optimal_price_range: Tuple[float, float]
    demand_elasticity: float
    revenue_impact: float
    conversion_impact: float
    user_segment: str
    confidence_level: float
class ValueValidationService:
    """價值驗證數據收集服務"""
    
    def __init__(self, db_path: str = "tradingagents.db"):
        self.db_path = db_path
        
        # 定價策略配置
        self.BASE_PRICE = 5.00
        self.PRICE_TEST_RANGES = {
            "conservative": (3.00, 7.00),
            "aggressive": (4.00, 8.00),
            "balanced": (3.50, 6.50),
            "value": (2.50, 5.50)
        }
        
        # 市場反饋分析配置
        self.SENTIMENT_KEYWORDS = {
            "positive": ["excellent", "great", "amazing", "helpful", "valuable", "worth", "recommend"],
            "negative": ["expensive", "overpriced", "useless", "waste", "disappointed", "poor", "bad"],
            "neutral": ["okay", "average", "fine", "decent", "acceptable"]
        }
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)
    
    async def analyze_insight_popularity(self, days: int = 30) -> List[InsightPopularityData]:
        """分析阿爾法洞察受歡迎程度"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 獲取洞察基礎數據和統計
            cursor.execute("""
                SELECT 
                    ai.id, ai.title, ai.category, ai.difficulty_level, ai.personality_types,
                    ai.view_count, ai.purchase_count, ai.rating,
                    COALESCE(SUM(ap.amount), 0) as total_revenue,
                    COUNT(DISTINCT ae.user_id) as unique_engagers,
                    COUNT(ae.id) as total_engagements
                FROM alpha_insights ai
                LEFT JOIN alpha_purchases ap ON ai.id = ap.insight_id 
                    AND ap.status = 'completed' AND ap.purchased_at > ?
                LEFT JOIN alpha_engagement ae ON ai.id = ae.insight_id 
                    AND ae.created_at > ?
                WHERE ai.is_active = 1
                GROUP BY ai.id, ai.title, ai.category, ai.difficulty_level, 
                         ai.personality_types, ai.view_count, ai.purchase_count, ai.rating
                ORDER BY ai.purchase_count DESC, ai.view_count DESC
            """, (cutoff_date, cutoff_date))
            
            insights_data = cursor.fetchall()
            
            popularity_list = []
            
            for row in insights_data:
                insight_id, title, category, difficulty, personality_types_str = row[:5]
                view_count, purchase_count, rating = row[5:8]
                total_revenue, unique_engagers, total_engagements = row[8:11]
                
                # 計算轉換率
                conversion_rate = (purchase_count / max(1, view_count)) * 100
                
                # 計算互動分數
                engagement_score = (total_engagements / max(1, unique_engagers)) if unique_engagers > 0 else 0
                
                # 計算留存率（基於重複互動）
                cursor.execute("""
                    SELECT COUNT(DISTINCT user_id) as repeat_users
                    FROM alpha_engagement 
                    WHERE insight_id = ? AND created_at > ?
                    GROUP BY user_id
                    HAVING COUNT(*) > 1
                """, (insight_id, cutoff_date))
                
                repeat_users = len(cursor.fetchall())
                retention_rate = (repeat_users / max(1, unique_engagers)) * 100 if unique_engagers > 0 else 0
                
                # 解析人格類型
                try:
                    personality_types = json.loads(personality_types_str) if personality_types_str else []
                except:
                    personality_types = []
                
                popularity_data = InsightPopularityData(
                    insight_id=insight_id,
                    title=title,
                    category=category,
                    difficulty_level=difficulty,
                    personality_types=personality_types,
                    view_count=view_count,
                    purchase_count=purchase_count,
                    conversion_rate=conversion_rate,
                    avg_rating=rating or 0.0,
                    total_revenue=total_revenue,
                    engagement_score=engagement_score,
                    retention_rate=retention_rate
                )
                
                popularity_list.append(popularity_data)
            
            conn.close()
            return popularity_list
            
        except Exception as e:
            logger.error(f"分析洞察受歡迎程度失敗: {e}")
            return []
    
    async def analyze_payment_willingness(self, user_id: Optional[str] = None) -> List[UserPaymentWillingness]:
        """分析用戶付費意願模式"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 構建查詢條件
            where_clause = "WHERE ap.status = 'completed'"
            params = []
            
            if user_id:
                where_clause += " AND ap.user_id = ?"
                params.append(user_id)
            
            # 獲取用戶付費行為數據
            cursor.execute(f"""
                SELECT 
                    ap.user_id,
                    pt.personality_type,
                    COUNT(ap.id) as purchase_count,
                    AVG(ap.amount) as avg_amount,
                    SUM(ap.amount) as total_spent,
                    MIN(ap.purchased_at) as first_purchase,
                    MAX(ap.purchased_at) as last_purchase,
                    COUNT(DISTINCT DATE(ap.purchased_at)) as active_days
                FROM alpha_purchases ap
                LEFT JOIN personality_test_results pt ON ap.user_id = pt.user_id
                {where_clause}
                GROUP BY ap.user_id, pt.personality_type
                HAVING purchase_count > 0
            """, params)
            
            user_data = cursor.fetchall()
            
            willingness_list = []
            
            for row in user_data:
                user_id, personality_type, purchase_count = row[:3]
                avg_amount, total_spent, first_purchase, last_purchase, active_days = row[3:]
                
                # 計算購買頻率
                if first_purchase and last_purchase:
                    first_date = datetime.fromisoformat(first_purchase)
                    last_date = datetime.fromisoformat(last_purchase)
                    days_span = max(1, (last_date - first_date).days)
                    purchase_frequency = purchase_count / days_span
                else:
                    purchase_frequency = 0.0
                
                # 計算價格敏感度分數
                price_sensitivity = self._calculate_price_sensitivity(user_id, cursor)
                
                # 計算價值感知分數
                value_perception = self._calculate_value_perception(user_id, cursor)
                
                # 確定付費意願等級
                willingness_level = self._determine_willingness_level(
                    total_spent, purchase_frequency, price_sensitivity, value_perception
                )
                
                # 估算最大願付價格
                max_willing_price = self._estimate_max_willing_price(
                    avg_amount, price_sensitivity, value_perception
                )
                
                # 確定偏好的付費模式
                preferred_model = self._determine_preferred_payment_model(
                    purchase_frequency, avg_amount, total_spent
                )
                
                willingness_data = UserPaymentWillingness(
                    user_id=user_id,
                    personality_type=personality_type or "unknown",
                    willingness_level=willingness_level,
                    max_willing_price=max_willing_price,
                    preferred_payment_model=preferred_model,
                    price_sensitivity_score=price_sensitivity,
                    value_perception_score=value_perception,
                    purchase_frequency=purchase_frequency,
                    avg_session_value=avg_amount or 0.0
                )
                
                willingness_list.append(willingness_data)
            
            conn.close()
            return willingness_list
            
        except Exception as e:
            logger.error(f"分析用戶付費意願失敗: {e}")
            return [] 
   
    async def collect_market_feedback(self, user_id: str, feedback_type: FeedbackType, 
                                    content: str, rating: Optional[int] = None, 
                                    insight_id: Optional[str] = None, 
                                    context_data: Optional[Dict[str, Any]] = None) -> str:
        """收集市場反饋"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            feedback_id = str(uuid.uuid4())
            
            # 計算情感分數
            sentiment_score = self._analyze_sentiment(content)
            
            cursor.execute("""
                INSERT INTO market_feedback 
                (id, user_id, feedback_type, content, rating, insight_id, 
                 context_data, sentiment_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id, user_id, feedback_type.value, content, rating,
                insight_id, json.dumps(context_data) if context_data else None,
                sentiment_score, datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"收集市場反饋: {feedback_id} from user {user_id}")
            return feedback_id
            
        except Exception as e:
            logger.error(f"收集市場反饋失敗: {e}")
            return ""
    
    async def get_market_feedback_analysis(self, days: int = 30) -> Dict[str, Any]:
        """獲取市場反饋分析"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # 總體反饋統計
            cursor.execute("""
                SELECT 
                    feedback_type,
                    COUNT(*) as count,
                    AVG(sentiment_score) as avg_sentiment,
                    AVG(rating) as avg_rating
                FROM market_feedback 
                WHERE created_at > ?
                GROUP BY feedback_type
            """, (cutoff_date,))
            
            feedback_stats = cursor.fetchall()
            
            # 按洞察分組的反饋
            cursor.execute("""
                SELECT 
                    mf.insight_id,
                    ai.title,
                    COUNT(*) as feedback_count,
                    AVG(mf.sentiment_score) as avg_sentiment,
                    AVG(mf.rating) as avg_rating
                FROM market_feedback mf
                LEFT JOIN alpha_insights ai ON mf.insight_id = ai.id
                WHERE mf.created_at > ? AND mf.insight_id IS NOT NULL
                GROUP BY mf.insight_id, ai.title
                ORDER BY feedback_count DESC
            """, (cutoff_date,))
            
            insight_feedback = cursor.fetchall()
            
            # 情感趨勢分析
            cursor.execute("""
                SELECT 
                    DATE(created_at) as date,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(*) as feedback_count
                FROM market_feedback 
                WHERE created_at > ?
                GROUP BY DATE(created_at)
                ORDER BY date
            """, (cutoff_date,))
            
            sentiment_trend = cursor.fetchall()
            
            conn.close()
            
            return {
                "period_days": days,
                "feedback_by_type": [
                    {
                        "type": row[0],
                        "count": row[1],
                        "avg_sentiment": row[2] or 0.0,
                        "avg_rating": row[3] or 0.0
                    }
                    for row in feedback_stats
                ],
                "feedback_by_insight": [
                    {
                        "insight_id": row[0],
                        "title": row[1],
                        "feedback_count": row[2],
                        "avg_sentiment": row[3] or 0.0,
                        "avg_rating": row[4] or 0.0
                    }
                    for row in insight_feedback
                ],
                "sentiment_trend": [
                    {
                        "date": row[0],
                        "avg_sentiment": row[1] or 0.0,
                        "feedback_count": row[2]
                    }
                    for row in sentiment_trend
                ]
            }
            
        except Exception as e:
            logger.error(f"獲取市場反饋分析失敗: {e}")
            return {}
    
    async def optimize_pricing_strategy(self, insight_category: Optional[str] = None, 
                                      personality_type: Optional[str] = None) -> List[PricingOptimizationData]:
        """優化定價策略"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 構建查詢條件
            where_conditions = ["ai.is_active = 1"]
            params = []
            
            if insight_category:
                where_conditions.append("ai.category = ?")
                params.append(insight_category)
            
            if personality_type:
                where_conditions.append("ai.personality_types LIKE ?")
                params.append(f'%{personality_type}%')
            
            where_clause = " AND ".join(where_conditions)
            
            # 獲取定價相關數據
            cursor.execute(f"""
                SELECT 
                    ai.id, ai.title, ai.category, ai.price, ai.personality_types,
                    ai.view_count, ai.purchase_count,
                    COUNT(DISTINCT ap.user_id) as unique_buyers,
                    SUM(ap.amount) as total_revenue,
                    AVG(mf.rating) as avg_rating,
                    AVG(mf.sentiment_score) as avg_sentiment
                FROM alpha_insights ai
                LEFT JOIN alpha_purchases ap ON ai.id = ap.insight_id AND ap.status = 'completed'
                LEFT JOIN market_feedback mf ON ai.id = mf.insight_id
                WHERE {where_clause}
                GROUP BY ai.id, ai.title, ai.category, ai.price, ai.personality_types,
                         ai.view_count, ai.purchase_count
                HAVING ai.view_count > 0
            """, params)
            
            pricing_data = cursor.fetchall()
            
            optimization_results = []
            
            for row in pricing_data:
                insight_id, title, category, current_price = row[:4]
                personality_types_str, view_count, purchase_count = row[4:7]
                unique_buyers, total_revenue, avg_rating, avg_sentiment = row[7:]
                
                # 計算當前轉換率
                current_conversion_rate = (purchase_count / max(1, view_count)) * 100
                
                # 分析需求彈性
                demand_elasticity = self._calculate_demand_elasticity(
                    current_price, current_conversion_rate, avg_rating or 0, avg_sentiment or 0
                )
                
                # 確定用戶細分
                try:
                    personality_types = json.loads(personality_types_str) if personality_types_str else []
                    user_segment = personality_types[0] if personality_types else "general"
                except:
                    user_segment = "general"
                
                # 計算最優價格範圍
                optimal_range = self._calculate_optimal_price_range(
                    current_price, demand_elasticity, user_segment, avg_rating or 0
                )
                
                # 估算收入影響
                revenue_impact = self._estimate_revenue_impact(
                    current_price, optimal_range, current_conversion_rate, view_count
                )
                
                # 估算轉換影響
                conversion_impact = self._estimate_conversion_impact(
                    current_price, optimal_range, demand_elasticity
                )
                
                # 計算信心水平
                confidence_level = self._calculate_confidence_level(
                    view_count, purchase_count, avg_rating or 0
                )
                
                optimization_data = PricingOptimizationData(
                    current_price=current_price,
                    optimal_price_range=optimal_range,
                    demand_elasticity=demand_elasticity,
                    revenue_impact=revenue_impact,
                    conversion_impact=conversion_impact,
                    user_segment=user_segment,
                    confidence_level=confidence_level
                )
                
                optimization_results.append(optimization_data)
            
            conn.close()
            return optimization_results
            
        except Exception as e:
            logger.error(f"優化定價策略失敗: {e}")
            return []    
  
    def _calculate_price_sensitivity(self, user_id: str, cursor) -> float:
        """計算用戶價格敏感度"""
        try:
            # 分析用戶的購買行為模式
            cursor.execute("""
                SELECT amount, purchased_at
                FROM alpha_purchases 
                WHERE user_id = ? AND status = 'completed'
                ORDER BY purchased_at
            """, (user_id,))
            
            purchases = cursor.fetchall()
            
            if len(purchases) < 2:
                return 0.5  # 默認中等敏感度
            
            # 計算價格變化對購買頻率的影響
            amounts = [p[0] for p in purchases]
            price_variance = statistics.variance(amounts) if len(amounts) > 1 else 0
            
            # 價格方差越大，敏感度越高
            sensitivity = min(price_variance / 10.0, 1.0)
            return sensitivity
            
        except Exception:
            return 0.5
    
    def _calculate_value_perception(self, user_id: str, cursor) -> float:
        """計算用戶價值感知分數"""
        try:
            # 基於用戶反饋和行為計算價值感知
            cursor.execute("""
                SELECT AVG(rating), AVG(sentiment_score)
                FROM market_feedback 
                WHERE user_id = ?
            """, (user_id,))
            
            feedback_data = cursor.fetchone()
            
            if feedback_data and feedback_data[0]:
                avg_rating = feedback_data[0]
                avg_sentiment = feedback_data[1] or 0
                
                # 結合評分和情感分數
                value_perception = (avg_rating / 5.0 * 0.7) + (avg_sentiment * 0.3)
                return max(0, min(1, value_perception))
            
            # 如果沒有反饋，基於購買行為推斷
            cursor.execute("""
                SELECT COUNT(*), AVG(amount)
                FROM alpha_purchases 
                WHERE user_id = ? AND status = 'completed'
            """, (user_id,))
            
            purchase_data = cursor.fetchone()
            
            if purchase_data and purchase_data[0] > 0:
                purchase_count = purchase_data[0]
                avg_amount = purchase_data[1]
                
                # 購買次數和金額反映價值感知
                frequency_score = min(purchase_count / 10.0, 1.0)
                amount_score = min(avg_amount / 10.0, 1.0)
                
                return (frequency_score + amount_score) / 2
            
            return 0.5  # 默認中等價值感知
            
        except Exception:
            return 0.5
    
    def _determine_willingness_level(self, total_spent: float, purchase_frequency: float, 
                                   price_sensitivity: float, value_perception: float) -> PaymentWillingnessLevel:
        """確定付費意願等級"""
        # 綜合計算意願分數
        spending_score = min(total_spent / 50.0, 1.0)  # 基於總消費
        frequency_score = min(purchase_frequency * 30, 1.0)  # 基於購買頻率
        sensitivity_score = 1.0 - price_sensitivity  # 敏感度越低，意願越高
        
        overall_score = (spending_score * 0.3 + frequency_score * 0.3 + 
                        sensitivity_score * 0.2 + value_perception * 0.2)
        
        if overall_score >= 0.8:
            return PaymentWillingnessLevel.VERY_HIGH
        elif overall_score >= 0.6:
            return PaymentWillingnessLevel.HIGH
        elif overall_score >= 0.4:
            return PaymentWillingnessLevel.MEDIUM
        elif overall_score >= 0.2:
            return PaymentWillingnessLevel.LOW
        else:
            return PaymentWillingnessLevel.VERY_LOW
    
    def _estimate_max_willing_price(self, avg_amount: float, price_sensitivity: float, 
                                  value_perception: float) -> float:
        """估算最大願付價格"""
        if not avg_amount:
            return self.BASE_PRICE
        
        # 基於歷史支付和價值感知估算
        base_willingness = avg_amount * (1 + value_perception)
        sensitivity_adjustment = base_willingness * (1 - price_sensitivity * 0.5)
        
        return max(self.BASE_PRICE * 0.5, min(sensitivity_adjustment, self.BASE_PRICE * 3))
    
    def _determine_preferred_payment_model(self, purchase_frequency: float, 
                                         avg_amount: float, total_spent: float) -> str:
        """確定偏好的付費模式"""
        if purchase_frequency > 0.1:  # 高頻購買
            if total_spent > 30:
                return "subscription"  # 訂閱模式更划算
            else:
                return "bundle"  # 套餐模式
        else:
            return "per_use"  # 按次付費
    
    def _analyze_sentiment(self, content: str) -> float:
        """分析文本情感"""
        content_lower = content.lower()
        
        positive_count = sum(1 for word in self.SENTIMENT_KEYWORDS["positive"] if word in content_lower)
        negative_count = sum(1 for word in self.SENTIMENT_KEYWORDS["negative"] if word in content_lower)
        neutral_count = sum(1 for word in self.SENTIMENT_KEYWORDS["neutral"] if word in content_lower)
        
        total_words = positive_count + negative_count + neutral_count
        
        if total_words == 0:
            return 0.0  # 中性
        
        # 計算情感分數 (-1 到 1)
        sentiment_score = (positive_count - negative_count) / total_words
        return sentiment_score
    
    def _calculate_demand_elasticity(self, current_price: float, conversion_rate: float, 
                                   avg_rating: float, avg_sentiment: float) -> float:
        """計算需求彈性"""
        # 基於轉換率、評分和情感計算彈性
        quality_score = (avg_rating / 5.0 * 0.6) + (avg_sentiment * 0.4)
        
        # 質量越高，需求越不敏感（彈性越小）
        base_elasticity = 1.5  # 基礎彈性
        quality_adjustment = base_elasticity * (1 - quality_score * 0.5)
        
        # 轉換率越高，彈性越小
        conversion_adjustment = quality_adjustment * (1 - conversion_rate / 100 * 0.3)
        
        return max(0.5, min(2.0, conversion_adjustment))
    
    def _calculate_optimal_price_range(self, current_price: float, demand_elasticity: float, 
                                     user_segment: str, avg_rating: float) -> Tuple[float, float]:
        """計算最優價格範圍"""
        # 獲取用戶細分的價格範圍
        segment_range = self.PRICE_TEST_RANGES.get(user_segment, (3.00, 7.00))
        
        # 基於需求彈性調整
        if demand_elasticity < 1.0:  # 需求不敏感，可以提價
            price_multiplier = 1.2
        elif demand_elasticity > 1.5:  # 需求敏感，應該降價
            price_multiplier = 0.8
        else:
            price_multiplier = 1.0
        
        # 基於質量調整
        quality_multiplier = 0.8 + (avg_rating / 5.0 * 0.4)
        
        final_multiplier = price_multiplier * quality_multiplier
        
        optimal_min = max(segment_range[0], current_price * final_multiplier * 0.8)
        optimal_max = min(segment_range[1], current_price * final_multiplier * 1.2)
        
        return (optimal_min, optimal_max)
    
    def _estimate_revenue_impact(self, current_price: float, optimal_range: Tuple[float, float], 
                               conversion_rate: float, view_count: int) -> float:
        """估算收入影響"""
        current_revenue = current_price * (conversion_rate / 100) * view_count
        
        # 使用範圍中點估算
        optimal_price = (optimal_range[0] + optimal_range[1]) / 2
        
        # 假設價格變化對轉換率的影響
        price_change_ratio = optimal_price / current_price
        
        if price_change_ratio > 1:  # 提價
            conversion_impact = 1 - (price_change_ratio - 1) * 0.3  # 提價降低轉換率
        else:  # 降價
            conversion_impact = 1 + (1 - price_change_ratio) * 0.2  # 降價提高轉換率
        
        new_conversion_rate = conversion_rate * conversion_impact
        optimal_revenue = optimal_price * (new_conversion_rate / 100) * view_count
        
        return ((optimal_revenue - current_revenue) / current_revenue) * 100 if current_revenue > 0 else 0
    
    def _estimate_conversion_impact(self, current_price: float, optimal_range: Tuple[float, float], 
                                  demand_elasticity: float) -> float:
        """估算轉換影響"""
        optimal_price = (optimal_range[0] + optimal_range[1]) / 2
        price_change_ratio = optimal_price / current_price
        
        # 基於需求彈性計算轉換率變化
        if price_change_ratio != 1:
            conversion_change = -demand_elasticity * ((price_change_ratio - 1) * 100)
            return conversion_change
        
        return 0.0
    
    def _calculate_confidence_level(self, view_count: int, purchase_count: int, avg_rating: float) -> float:
        """計算信心水平"""
        # 基於數據量和質量計算信心水平
        data_volume_score = min(view_count / 100.0, 1.0)  # 瀏覽量
        purchase_volume_score = min(purchase_count / 20.0, 1.0)  # 購買量
        rating_score = avg_rating / 5.0 if avg_rating > 0 else 0.5  # 評分質量
        
        confidence = (data_volume_score * 0.4 + purchase_volume_score * 0.4 + rating_score * 0.2)
        return confidence
    
    async def get_value_validation_summary(self, days: int = 30) -> Dict[str, Any]:
        """獲取價值驗證摘要報告"""
        try:
            # 獲取各項分析數據
            popularity_data = await self.analyze_insight_popularity(days)
            willingness_data = await self.analyze_payment_willingness()
            feedback_analysis = await self.get_market_feedback_analysis(days)
            pricing_optimization = await self.optimize_pricing_strategy()
            
            # 生成摘要報告
            summary = {
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
                
                "popularity_insights": {
                    "total_insights_analyzed": len(popularity_data),
                    "top_performers": sorted(popularity_data, key=lambda x: x.conversion_rate, reverse=True)[:5],
                    "avg_conversion_rate": statistics.mean([p.conversion_rate for p in popularity_data]) if popularity_data else 0,
                    "total_revenue": sum([p.total_revenue for p in popularity_data])
                },
                
                "payment_willingness": {
                    "total_users_analyzed": len(willingness_data),
                    "willingness_distribution": self._get_willingness_distribution(willingness_data),
                    "avg_max_willing_price": statistics.mean([w.max_willing_price for w in willingness_data]) if willingness_data else 0,
                    "preferred_payment_models": self._get_payment_model_distribution(willingness_data)
                },
                
                "market_feedback": feedback_analysis,
                
                "pricing_recommendations": {
                    "total_insights_optimized": len(pricing_optimization),
                    "avg_revenue_impact": statistics.mean([p.revenue_impact for p in pricing_optimization]) if pricing_optimization else 0,
                    "high_confidence_recommendations": [p for p in pricing_optimization if p.confidence_level > 0.7]
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"獲取價值驗證摘要失敗: {e}")
            return {}
    
    def _get_willingness_distribution(self, willingness_data: List[UserPaymentWillingness]) -> Dict[str, int]:
        """獲取付費意願分佈"""
        distribution = {}
        for level in PaymentWillingnessLevel:
            distribution[level.value] = sum(1 for w in willingness_data if w.willingness_level == level)
        return distribution
    
    def _get_payment_model_distribution(self, willingness_data: List[UserPaymentWillingness]) -> Dict[str, int]:
        """獲取付費模式偏好分佈"""
        distribution = {}
        for w in willingness_data:
            model = w.preferred_payment_model
            distribution[model] = distribution.get(model, 0) + 1
        return distribution