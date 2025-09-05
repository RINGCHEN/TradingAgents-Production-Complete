#!/usr/bin/env python3
"""
User Feedback System - 用戶反饋系統
天工 (TianGong) - 智能用戶反饋收集和分析品質追蹤系統

此模組負責：
1. 多維度反饋收集
2. 反饋智能分析
3. 品質趨勢追蹤
4. 個性化改善建議
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import re
from collections import defaultdict

class FeedbackType(Enum):
    """反饋類型"""
    RATING = "rating"                   # 評分反饋
    TEXT_FEEDBACK = "text_feedback"     # 文字反饋
    QUICK_REACTION = "quick_reaction"   # 快速反應 (👍👎)
    DETAILED_REVIEW = "detailed_review" # 詳細評論
    BUG_REPORT = "bug_report"          # 錯誤報告
    FEATURE_REQUEST = "feature_request" # 功能請求

class FeedbackCategory(Enum):
    """反饋類別"""
    ANALYSIS_QUALITY = "analysis_quality"       # 分析品質
    RESPONSE_SPEED = "response_speed"           # 回應速度
    USER_EXPERIENCE = "user_experience"        # 用戶體驗
    CONTENT_ACCURACY = "content_accuracy"      # 內容準確性
    USEFULNESS = "usefulness"                  # 實用性
    INTERFACE_DESIGN = "interface_design"      # 介面設計

class SentimentPolarity(Enum):
    """情感極性"""
    VERY_POSITIVE = "very_positive"    # 非常正面
    POSITIVE = "positive"              # 正面
    NEUTRAL = "neutral"                # 中性
    NEGATIVE = "negative"              # 負面
    VERY_NEGATIVE = "very_negative"    # 非常負面

@dataclass
class UserFeedback:
    """用戶反饋"""
    feedback_id: str
    user_id: str
    analysis_id: Optional[str]         # 關聯的分析ID
    feedback_type: FeedbackType
    category: FeedbackCategory
    rating_score: Optional[float]      # 1-10評分
    text_content: Optional[str]        # 文字內容
    sentiment_polarity: SentimentPolarity
    tags: List[str]                    # 標籤
    timestamp: str
    user_context: Dict[str, Any]       # 用戶上下文
    processed: bool = False
    response_generated: bool = False

@dataclass
class FeedbackAnalysis:
    """反饋分析結果"""
    analysis_id: str
    feedback_ids: List[str]
    category: FeedbackCategory
    sentiment_distribution: Dict[SentimentPolarity, int]
    key_themes: List[str]
    common_issues: List[str]
    improvement_suggestions: List[str]
    severity_score: float              # 問題嚴重程度 (0-10)
    confidence_level: float
    created_at: str

@dataclass
class QualityMetrics:
    """品質指標"""
    metric_id: str
    time_period: str                   # daily, weekly, monthly
    avg_rating: float
    total_feedbacks: int
    positive_ratio: float              # 正面反饋比例
    sentiment_scores: Dict[str, float]
    category_breakdown: Dict[FeedbackCategory, float]
    trend_direction: str               # improving, stable, declining
    quality_score: float               # 綜合品質分數 (0-100)

class UserFeedbackSystem:
    """用戶反饋系統"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 反饋存儲
        self.feedbacks: List[UserFeedback] = []
        self.feedback_analyses: List[FeedbackAnalysis] = []
        self.quality_metrics: List[QualityMetrics] = []
        
        # 情感分析關鍵詞
        self.sentiment_keywords = self._initialize_sentiment_keywords()
        
        # 分類關鍵詞
        self.category_keywords = self._initialize_category_keywords()
        
        # 配置
        self.auto_analysis_enabled = True
        self.feedback_threshold_for_analysis = 5
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _initialize_sentiment_keywords(self) -> Dict[SentimentPolarity, List[str]]:
        """初始化情感分析關鍵詞"""
        return {
            SentimentPolarity.VERY_POSITIVE: [
                "非常好", "極佳", "完美", "傑出", "優秀", "驚艷", "amazing", "excellent", "perfect"
            ],
            SentimentPolarity.POSITIVE: [
                "好", "不錯", "滿意", "有用", "準確", "快速", "good", "nice", "useful", "accurate"
            ],
            SentimentPolarity.NEUTRAL: [
                "還可以", "普通", "一般", "ok", "okay", "average", "normal"
            ],
            SentimentPolarity.NEGATIVE: [
                "不好", "有問題", "錯誤", "慢", "不準", "差", "bad", "wrong", "slow", "poor"
            ],
            SentimentPolarity.VERY_NEGATIVE: [
                "很差", "非常糟", "完全錯誤", "無用", "terrible", "awful", "useless", "horrible"
            ]
        }
    
    def _initialize_category_keywords(self) -> Dict[FeedbackCategory, List[str]]:
        """初始化分類關鍵詞"""
        return {
            FeedbackCategory.ANALYSIS_QUALITY: [
                "分析", "預測", "建議", "準確", "analysis", "prediction", "accuracy"
            ],
            FeedbackCategory.RESPONSE_SPEED: [
                "速度", "快", "慢", "等待", "time", "speed", "fast", "slow", "wait"
            ],
            FeedbackCategory.USER_EXPERIENCE: [
                "體驗", "使用", "操作", "介面", "experience", "interface", "usability"
            ],
            FeedbackCategory.CONTENT_ACCURACY: [
                "正確", "錯誤", "數據", "資訊", "correct", "wrong", "data", "information"
            ],
            FeedbackCategory.USEFULNESS: [
                "有用", "實用", "幫助", "價值", "useful", "helpful", "valuable"
            ],
            FeedbackCategory.INTERFACE_DESIGN: [
                "設計", "佈局", "顏色", "按鈕", "design", "layout", "button", "UI"
            ]
        }
    
    async def collect_feedback(
        self,
        user_id: str,
        feedback_type: FeedbackType,
        category: FeedbackCategory = None,
        rating_score: float = None,
        text_content: str = None,
        analysis_id: str = None,
        user_context: Dict[str, Any] = None
    ) -> str:
        """收集用戶反饋"""
        
        feedback_id = f"feedback_{int(time.time())}_{user_id}"
        
        # 自動分類（如果未指定）
        if not category and text_content:
            category = self._auto_categorize_feedback(text_content)
        
        # 情感分析
        sentiment = self._analyze_sentiment(text_content, rating_score)
        
        # 提取標籤
        tags = self._extract_tags(text_content) if text_content else []
        
        # 創建反饋記錄
        feedback = UserFeedback(
            feedback_id=feedback_id,
            user_id=user_id,
            analysis_id=analysis_id,
            feedback_type=feedback_type,
            category=category or FeedbackCategory.ANALYSIS_QUALITY,
            rating_score=rating_score,
            text_content=text_content,
            sentiment_polarity=sentiment,
            tags=tags,
            timestamp=datetime.now().isoformat(),
            user_context=user_context or {}
        )
        
        self.feedbacks.append(feedback)
        
        # 觸發自動分析
        if self.auto_analysis_enabled:
            await self._trigger_auto_analysis(category)
        
        self.logger.info(f"收集反饋: {feedback_id} - {category.value} - {sentiment.value}")
        
        return feedback_id
    
    def _auto_categorize_feedback(self, text_content: str) -> FeedbackCategory:
        """自動分類反饋"""
        text_lower = text_content.lower()
        
        category_scores = {}
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return FeedbackCategory.ANALYSIS_QUALITY  # 預設分類
    
    def _analyze_sentiment(self, text_content: str, rating_score: float = None) -> SentimentPolarity:
        """分析情感極性"""
        
        # 優先使用評分
        if rating_score is not None:
            if rating_score >= 9:
                return SentimentPolarity.VERY_POSITIVE
            elif rating_score >= 7:
                return SentimentPolarity.POSITIVE
            elif rating_score >= 5:
                return SentimentPolarity.NEUTRAL
            elif rating_score >= 3:
                return SentimentPolarity.NEGATIVE
            else:
                return SentimentPolarity.VERY_NEGATIVE
        
        # 文字情感分析
        if not text_content:
            return SentimentPolarity.NEUTRAL
        
        text_lower = text_content.lower()
        sentiment_scores = {}
        
        for sentiment, keywords in self.sentiment_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                sentiment_scores[sentiment] = score
        
        if sentiment_scores:
            return max(sentiment_scores, key=sentiment_scores.get)
        else:
            return SentimentPolarity.NEUTRAL
    
    def _extract_tags(self, text_content: str) -> List[str]:
        """提取標籤"""
        if not text_content:
            return []
        
        # 簡化的標籤提取
        tags = []
        text_lower = text_content.lower()
        
        # 技術相關標籤
        tech_keywords = {
            "ai": ["ai", "人工智慧", "機器學習"],
            "股票": ["股票", "股市", "投資", "交易"],
            "分析": ["分析", "預測", "建議"],
            "介面": ["介面", "UI", "設計", "佈局"],
            "速度": ["速度", "快", "慢", "效能"],
            "準確": ["準確", "正確", "精確", "可靠"]
        }
        
        for tag, keywords in tech_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags[:5]  # 限制最多5個標籤
    
    async def _trigger_auto_analysis(self, category: FeedbackCategory):
        """觸發自動分析"""
        
        # 檢查該類別的反饋數量
        category_feedbacks = [
            f for f in self.feedbacks
            if f.category == category and not f.processed
        ]
        
        if len(category_feedbacks) >= self.feedback_threshold_for_analysis:
            await self.analyze_feedback_batch(category, time_period="recent")
    
    async def analyze_feedback_batch(
        self,
        category: FeedbackCategory,
        time_period: str = "recent",  # recent, daily, weekly, monthly
        days: int = 7
    ) -> FeedbackAnalysis:
        """分析反饋批次"""
        
        # 獲取指定時期的反饋
        if time_period == "recent":
            target_feedbacks = [
                f for f in self.feedbacks[-50:]  # 最近50條
                if f.category == category
            ]
        else:
            cutoff_date = datetime.now() - timedelta(days=days)
            target_feedbacks = [
                f for f in self.feedbacks
                if (f.category == category and 
                    datetime.fromisoformat(f.timestamp) >= cutoff_date)
            ]
        
        if not target_feedbacks:
            return None
        
        analysis_id = f"analysis_{category.value}_{int(time.time())}"
        
        # 情感分布統計
        sentiment_distribution = {}
        for sentiment in SentimentPolarity:
            sentiment_distribution[sentiment] = sum(
                1 for f in target_feedbacks if f.sentiment_polarity == sentiment
            )
        
        # 提取關鍵主題
        key_themes = self._extract_key_themes(target_feedbacks)
        
        # 識別常見問題
        common_issues = self._identify_common_issues(target_feedbacks)
        
        # 生成改善建議
        improvement_suggestions = self._generate_improvement_suggestions(
            target_feedbacks, key_themes, common_issues
        )
        
        # 計算嚴重程度
        severity_score = self._calculate_severity_score(target_feedbacks)
        
        # 計算信心度
        confidence_level = min(1.0, len(target_feedbacks) / 20.0)  # 20個樣本達到最高信心度
        
        # 創建分析結果
        analysis = FeedbackAnalysis(
            analysis_id=analysis_id,
            feedback_ids=[f.feedback_id for f in target_feedbacks],
            category=category,
            sentiment_distribution=sentiment_distribution,
            key_themes=key_themes,
            common_issues=common_issues,
            improvement_suggestions=improvement_suggestions,
            severity_score=severity_score,
            confidence_level=confidence_level,
            created_at=datetime.now().isoformat()
        )
        
        self.feedback_analyses.append(analysis)
        
        # 標記反饋為已處理
        for feedback in target_feedbacks:
            feedback.processed = True
        
        self.logger.info(f"完成反饋分析: {analysis_id} - {len(target_feedbacks)} 條反饋")
        
        return analysis
    
    def _extract_key_themes(self, feedbacks: List[UserFeedback]) -> List[str]:
        """提取關鍵主題"""
        
        # 統計標籤頻率
        tag_frequency = defaultdict(int)
        for feedback in feedbacks:
            for tag in feedback.tags:
                tag_frequency[tag] += 1
        
        # 統計文字中的關鍵詞
        keyword_frequency = defaultdict(int)
        for feedback in feedbacks:
            if feedback.text_content:
                # 簡化的關鍵詞提取
                words = re.findall(r'\\b\\w+\\b', feedback.text_content.lower())
                for word in words:
                    if len(word) > 2:  # 過濾短詞
                        keyword_frequency[word] += 1
        
        # 合併並排序
        all_themes = {}
        all_themes.update(tag_frequency)
        all_themes.update({k: v for k, v in keyword_frequency.items() if v >= 2})
        
        # 返回前10個主題
        sorted_themes = sorted(all_themes.items(), key=lambda x: x[1], reverse=True)
        return [theme[0] for theme in sorted_themes[:10]]
    
    def _identify_common_issues(self, feedbacks: List[UserFeedback]) -> List[str]:
        """識別常見問題"""
        
        issues = []
        
        # 負面反饋中的共同模式
        negative_feedbacks = [
            f for f in feedbacks
            if f.sentiment_polarity in [SentimentPolarity.NEGATIVE, SentimentPolarity.VERY_NEGATIVE]
        ]
        
        if negative_feedbacks:
            # 統計負面反饋的常見詞彙
            negative_words = defaultdict(int)
            for feedback in negative_feedbacks:
                if feedback.text_content:
                    words = re.findall(r'\\b\\w+\\b', feedback.text_content.lower())
                    for word in words:
                        if word in ["錯誤", "慢", "差", "問題", "bug", "error", "slow", "bad"]:
                            negative_words[word] += 1
            
            # 生成問題描述
            for word, count in negative_words.items():
                if count >= 2:  # 至少出現2次
                    percentage = (count / len(negative_feedbacks)) * 100
                    issues.append(f"{word} 問題 (出現在 {percentage:.0f}% 的負面反饋中)")
        
        # 低分評分的模式分析
        low_rating_feedbacks = [
            f for f in feedbacks
            if f.rating_score and f.rating_score <= 5
        ]
        
        if len(low_rating_feedbacks) > len(feedbacks) * 0.3:  # 超過30%低分
            issues.append(f"整體滿意度偏低 ({len(low_rating_feedbacks)}/{len(feedbacks)} 為低分評價)")
        
        return issues[:5]  # 返回前5個問題
    
    def _generate_improvement_suggestions(
        self,
        feedbacks: List[UserFeedback],
        key_themes: List[str],
        common_issues: List[str]
    ) -> List[str]:
        """生成改善建議"""
        
        suggestions = []
        
        # 基於情感分布的建議
        negative_count = sum(
            1 for f in feedbacks
            if f.sentiment_polarity in [SentimentPolarity.NEGATIVE, SentimentPolarity.VERY_NEGATIVE]
        )
        
        negative_ratio = negative_count / len(feedbacks) if feedbacks else 0
        
        if negative_ratio > 0.3:
            suggestions.append("負面反饋比例較高，需要緊急改善用戶體驗")
        elif negative_ratio > 0.15:
            suggestions.append("考慮優化用戶體驗，降低負面反饋")
        
        # 基於常見問題的建議
        if "錯誤" in key_themes or "error" in key_themes:
            suggestions.append("加強錯誤處理和系統穩定性")
        
        if "慢" in key_themes or "slow" in key_themes:
            suggestions.append("優化系統性能，提升響應速度")
        
        if "介面" in key_themes or "UI" in key_themes:
            suggestions.append("改進用戶介面設計和交互體驗")
        
        if "分析" in key_themes and negative_ratio > 0.2:
            suggestions.append("提升AI分析的準確性和實用性")
        
        # 基於評分的建議
        ratings = [f.rating_score for f in feedbacks if f.rating_score]
        if ratings:
            avg_rating = statistics.mean(ratings)
            if avg_rating < 6:
                suggestions.append(f"整體評分偏低 ({avg_rating:.1f}/10)，需要全面改善")
            elif avg_rating < 7.5:
                suggestions.append("評分有改善空間，可針對具體問題優化")
        
        return suggestions[:10]  # 最多10個建議
    
    def _calculate_severity_score(self, feedbacks: List[UserFeedback]) -> float:
        """計算嚴重程度評分"""
        
        if not feedbacks:
            return 0.0
        
        # 基於情感分布計算
        severity_weights = {
            SentimentPolarity.VERY_NEGATIVE: 10,
            SentimentPolarity.NEGATIVE: 7,
            SentimentPolarity.NEUTRAL: 5,
            SentimentPolarity.POSITIVE: 3,
            SentimentPolarity.VERY_POSITIVE: 1
        }
        
        total_severity = sum(
            severity_weights[f.sentiment_polarity] for f in feedbacks
        )
        
        max_possible = len(feedbacks) * 10
        severity_score = (total_severity / max_possible) * 10
        
        return min(10.0, severity_score)
    
    async def generate_quality_metrics(self, time_period: str = "weekly") -> QualityMetrics:
        """生成品質指標"""
        
        # 確定時間範圍
        if time_period == "daily":
            days = 1
        elif time_period == "weekly":
            days = 7
        elif time_period == "monthly":
            days = 30
        else:
            days = 7
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 篩選反饋
        period_feedbacks = [
            f for f in self.feedbacks
            if datetime.fromisoformat(f.timestamp) >= cutoff_date
        ]
        
        if not period_feedbacks:
            return None
        
        metric_id = f"metrics_{time_period}_{int(time.time())}"
        
        # 計算平均評分
        ratings = [f.rating_score for f in period_feedbacks if f.rating_score]
        avg_rating = statistics.mean(ratings) if ratings else 0.0
        
        # 計算正面比例
        positive_count = sum(
            1 for f in period_feedbacks
            if f.sentiment_polarity in [SentimentPolarity.POSITIVE, SentimentPolarity.VERY_POSITIVE]
        )
        positive_ratio = positive_count / len(period_feedbacks)
        
        # 情感分數
        sentiment_scores = {}
        for sentiment in SentimentPolarity:
            count = sum(1 for f in period_feedbacks if f.sentiment_polarity == sentiment)
            sentiment_scores[sentiment.value] = count / len(period_feedbacks)
        
        # 類別分佈
        category_breakdown = {}
        for category in FeedbackCategory:
            category_feedbacks = [f for f in period_feedbacks if f.category == category]
            if category_feedbacks:
                category_ratings = [f.rating_score for f in category_feedbacks if f.rating_score]
                if category_ratings:
                    category_breakdown[category] = statistics.mean(category_ratings)
        
        # 趨勢方向
        trend_direction = self._calculate_trend_direction(time_period)
        
        # 綜合品質分數
        quality_score = self._calculate_quality_score(
            avg_rating, positive_ratio, sentiment_scores
        )
        
        metrics = QualityMetrics(
            metric_id=metric_id,
            time_period=time_period,
            avg_rating=avg_rating,
            total_feedbacks=len(period_feedbacks),
            positive_ratio=positive_ratio,
            sentiment_scores=sentiment_scores,
            category_breakdown=category_breakdown,
            trend_direction=trend_direction,
            quality_score=quality_score
        )
        
        self.quality_metrics.append(metrics)
        
        return metrics
    
    def _calculate_trend_direction(self, time_period: str) -> str:
        """計算趨勢方向"""
        
        # 獲取歷史指標
        historical_metrics = [
            m for m in self.quality_metrics
            if m.time_period == time_period
        ]
        
        if len(historical_metrics) < 2:
            return "stable"
        
        # 比較最近兩個週期
        recent_score = historical_metrics[-1].quality_score
        previous_score = historical_metrics[-2].quality_score
        
        diff = recent_score - previous_score
        
        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_quality_score(
        self,
        avg_rating: float,
        positive_ratio: float,
        sentiment_scores: Dict[str, float]
    ) -> float:
        """計算綜合品質分數"""
        
        # 評分權重 40%
        rating_score = (avg_rating / 10.0) * 40
        
        # 正面比例權重 30%
        positive_score = positive_ratio * 30
        
        # 情感分佈權重 30%
        sentiment_score = (
            sentiment_scores.get("very_positive", 0) * 5 +
            sentiment_scores.get("positive", 0) * 3 +
            sentiment_scores.get("neutral", 0) * 2 +
            sentiment_scores.get("negative", 0) * 1 +
            sentiment_scores.get("very_negative", 0) * 0
        ) * 30
        
        total_score = rating_score + positive_score + sentiment_score
        
        return min(100.0, max(0.0, total_score))
    
    def get_user_feedback_summary(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶反饋摘要"""
        
        user_feedbacks = [f for f in self.feedbacks if f.user_id == user_id]
        
        if not user_feedbacks:
            return {
                "user_id": user_id,
                "total_feedbacks": 0,
                "message": "該用戶尚未提供反饋"
            }
        
        # 統計數據
        ratings = [f.rating_score for f in user_feedbacks if f.rating_score]
        avg_rating = statistics.mean(ratings) if ratings else 0.0
        
        sentiment_dist = {}
        for sentiment in SentimentPolarity:
            count = sum(1 for f in user_feedbacks if f.sentiment_polarity == sentiment)
            sentiment_dist[sentiment.value] = count
        
        category_dist = {}
        for category in FeedbackCategory:
            count = sum(1 for f in user_feedbacks if f.category == category)
            if count > 0:
                category_dist[category.value] = count
        
        # 最近反饋
        recent_feedbacks = sorted(user_feedbacks, key=lambda x: x.timestamp, reverse=True)[:5]
        recent_feedback_data = [
            {
                "feedback_id": f.feedback_id,
                "category": f.category.value,
                "rating": f.rating_score,
                "sentiment": f.sentiment_polarity.value,
                "timestamp": f.timestamp
            }
            for f in recent_feedbacks
        ]
        
        return {
            "user_id": user_id,
            "total_feedbacks": len(user_feedbacks),
            "avg_rating": avg_rating,
            "sentiment_distribution": sentiment_dist,
            "category_distribution": category_dist,
            "recent_feedbacks": recent_feedback_data,
            "user_engagement_level": self._calculate_engagement_level(user_feedbacks),
            "last_feedback_date": user_feedbacks[-1].timestamp
        }
    
    def _calculate_engagement_level(self, user_feedbacks: List[UserFeedback]) -> str:
        """計算用戶參與度"""
        
        feedback_count = len(user_feedbacks)
        
        # 檢查反饋頻率
        if feedback_count >= 20:
            return "high"
        elif feedback_count >= 5:
            return "medium"
        else:
            return "low"
    
    def get_feedback_dashboard(self) -> Dict[str, Any]:
        """獲取反饋儀表板"""
        
        if not self.feedbacks:
            return {
                "message": "暫無反饋數據",
                "total_feedbacks": 0
            }
        
        # 最近30天的反饋
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_feedbacks = [
            f for f in self.feedbacks
            if datetime.fromisoformat(f.timestamp) >= recent_cutoff
        ]
        
        # 總體統計
        total_feedbacks = len(self.feedbacks)
        recent_count = len(recent_feedbacks)
        
        # 評分統計
        all_ratings = [f.rating_score for f in self.feedbacks if f.rating_score]
        avg_rating = statistics.mean(all_ratings) if all_ratings else 0.0
        
        # 情感分布
        sentiment_dist = {}
        for sentiment in SentimentPolarity:
            count = sum(1 for f in recent_feedbacks if f.sentiment_polarity == sentiment)
            sentiment_dist[sentiment.value] = count
        
        # 類別分佈
        category_dist = {}
        for category in FeedbackCategory:
            count = sum(1 for f in recent_feedbacks if f.category == category)
            category_dist[category.value] = count
        
        # 品質趨勢
        quality_trend = []
        for i in range(4):  # 最近4週
            week_start = datetime.now() - timedelta(weeks=i+1)
            week_end = datetime.now() - timedelta(weeks=i)
            
            week_feedbacks = [
                f for f in self.feedbacks
                if week_start <= datetime.fromisoformat(f.timestamp) < week_end
            ]
            
            if week_feedbacks:
                week_ratings = [f.rating_score for f in week_feedbacks if f.rating_score]
                week_avg = statistics.mean(week_ratings) if week_ratings else 0
                
                quality_trend.append({
                    "week": f"第{4-i}週",
                    "avg_rating": week_avg,
                    "feedback_count": len(week_feedbacks)
                })
        
        # 最新分析
        recent_analyses = self.feedback_analyses[-5:] if self.feedback_analyses else []
        
        return {
            "summary": {
                "total_feedbacks": total_feedbacks,
                "recent_feedbacks_30_days": recent_count,
                "average_rating": avg_rating,
                "total_analyses": len(self.feedback_analyses)
            },
            "sentiment_distribution": sentiment_dist,
            "category_distribution": category_dist,
            "quality_trend": quality_trend,
            "recent_analyses": [asdict(analysis) for analysis in recent_analyses],
            "timestamp": datetime.now().isoformat()
        }

# 便利函數
async def quick_feedback_collection(
    user_id: str,
    rating: float,
    category: str = "analysis_quality",
    comment: str = None
) -> str:
    """快速反饋收集"""
    
    system = UserFeedbackSystem()
    
    try:
        feedback_category = FeedbackCategory(category)
    except ValueError:
        feedback_category = FeedbackCategory.ANALYSIS_QUALITY
    
    return await system.collect_feedback(
        user_id=user_id,
        feedback_type=FeedbackType.RATING,
        category=feedback_category,
        rating_score=rating,
        text_content=comment
    )

async def analyze_user_satisfaction(days: int = 30) -> Dict[str, Any]:
    """分析用戶滿意度"""
    
    system = UserFeedbackSystem()
    
    # 生成週度品質指標
    weekly_metrics = await system.generate_quality_metrics("weekly")
    
    # 分析各類別反饋
    category_analyses = {}
    for category in FeedbackCategory:
        analysis = await system.analyze_feedback_batch(category, days=days)
        if analysis:
            category_analyses[category.value] = asdict(analysis)
    
    return {
        "quality_metrics": asdict(weekly_metrics) if weekly_metrics else None,
        "category_analyses": category_analyses,
        "dashboard": system.get_feedback_dashboard(),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_feedback_system():
        print("📝 測試用戶反饋系統")
        
        system = UserFeedbackSystem()
        
        # 收集測試反饋
        feedback_id1 = await system.collect_feedback(
            user_id="test_user_1",
            feedback_type=FeedbackType.RATING,
            category=FeedbackCategory.ANALYSIS_QUALITY,
            rating_score=8.5,
            text_content="分析很準確，對我的投資決策很有幫助"
        )
        
        feedback_id2 = await system.collect_feedback(
            user_id="test_user_2",
            feedback_type=FeedbackType.TEXT_FEEDBACK,
            category=FeedbackCategory.RESPONSE_SPEED,
            rating_score=6.0,
            text_content="速度有點慢，希望能更快一些"
        )
        
        print(f"收集反饋: {feedback_id1}, {feedback_id2}")
        
        # 生成品質指標
        metrics = await system.generate_quality_metrics("weekly")
        if metrics:
            print(f"品質分數: {metrics.quality_score:.1f}/100")
        
        # 獲取儀表板
        dashboard = system.get_feedback_dashboard()
        print(f"總反饋數: {dashboard['summary']['total_feedbacks']}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_feedback_system())