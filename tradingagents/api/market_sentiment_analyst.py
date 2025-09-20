"""
市場情緒分析師 - 專門分析市場情緒和投資者行為
結合社交媒體、新聞情緒、技術指標等多維度數據進行情緒分析
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class MarketSentimentAnalyst:
    """市場情緒分析師"""
    
    def __init__(self):
        self.analyst_id = "market_sentiment_analyst"
        self.name = "市場情緒分析師"
        self.description = "專精於分析市場情緒、投資者心理和群體行為模式，提供情緒驅動的投資洞察"
        self.specialties = [
            "市場恐慌指數分析",
            "社交媒體情緒監測", 
            "投資者行為模式",
            "情緒週期判斷",
            "群體心理分析",
            "市場情緒轉折點預測"
        ]
        self.version = "1.0.0"

    async def analyze_stock(self, symbol: str, user_tier: str = "free") -> Dict[str, Any]:
        """執行市場情緒分析"""
        try:
            logger.info(f"市場情緒分析師開始分析 {symbol}")
            
            # 模擬分析延遲
            await asyncio.sleep(2)
            
            # 獲取情緒數據
            sentiment_data = await self._get_sentiment_data(symbol)
            
            # 分析結果
            analysis_result = {
                "analyst_id": self.analyst_id,
                "analyst_name": self.name,
                "symbol": symbol,
                "analysis_type": "market_sentiment",
                "timestamp": datetime.now().isoformat(),
                "sentiment_score": sentiment_data["overall_sentiment"],
                "fear_greed_index": sentiment_data["fear_greed_index"],
                "social_sentiment": sentiment_data["social_sentiment"],
                "news_sentiment": sentiment_data["news_sentiment"],
                "technical_sentiment": sentiment_data["technical_sentiment"],
                "investor_behavior": sentiment_data["investor_behavior"],
                "market_mood": sentiment_data["market_mood"],
                "sentiment_trend": sentiment_data["sentiment_trend"],
                "key_insights": self._generate_insights(sentiment_data, user_tier),
                "recommendation": self._generate_recommendation(sentiment_data),
                "confidence_level": self._calculate_confidence(sentiment_data),
                "risk_assessment": self._assess_sentiment_risk(sentiment_data),
                "tier_limitations": self._get_tier_limitations(user_tier)
            }
            
            logger.info(f"市場情緒分析師完成分析 {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"市場情緒分析師分析失敗 {symbol}: {str(e)}")
            return {
                "analyst_id": self.analyst_id,
                "analyst_name": self.name,
                "symbol": symbol,
                "error": f"分析過程發生錯誤: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    async def _get_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """獲取情緒相關數據"""
        # 模擬市場情緒數據
        import random
        
        # 基礎情緒分數 (-100 到 100)
        base_sentiment = random.uniform(-50, 50)
        
        return {
            "overall_sentiment": round(base_sentiment, 2),
            "fear_greed_index": random.randint(10, 90),
            "social_sentiment": {
                "twitter_sentiment": round(random.uniform(-30, 30), 2),
                "reddit_sentiment": round(random.uniform(-20, 40), 2),
                "forum_sentiment": round(random.uniform(-25, 35), 2),
                "mention_volume": random.randint(100, 5000),
                "trending_topics": [
                    "AI晶片需求強勁", "地緣政治風險", "央行政策",
                    "財報季預期", "技術突破", "供應鏈穩定"
                ][:random.randint(2, 4)]
            },
            "news_sentiment": {
                "financial_news": round(random.uniform(-40, 40), 2),
                "industry_news": round(random.uniform(-30, 50), 2),
                "company_news": round(random.uniform(-35, 45), 2),
                "positive_news_count": random.randint(5, 25),
                "negative_news_count": random.randint(3, 20)
            },
            "technical_sentiment": {
                "momentum_sentiment": round(random.uniform(-50, 50), 2),
                "volume_sentiment": round(random.uniform(-30, 70), 2),
                "volatility_sentiment": round(random.uniform(-60, 20), 2),
                "pattern_sentiment": round(random.uniform(-40, 60), 2)
            },
            "investor_behavior": {
                "institutional_flow": random.choice(["買入", "賣出", "中性"]),
                "retail_activity": random.choice(["積極", "謹慎", "觀望"]),
                "foreign_investment": random.choice(["流入", "流出", "平衡"]),
                "options_activity": random.choice(["看多", "看空", "中性"]),
                "insider_trading": random.choice(["買入", "賣出", "無明顯動作"])
            },
            "market_mood": random.choice([
                "極度樂觀", "樂觀", "中性樂觀", "中性", 
                "中性悲觀", "悲觀", "極度悲觀"
            ]),
            "sentiment_trend": random.choice([
                "快速改善", "緩慢改善", "穩定", "緩慢惡化", "快速惡化"
            ])
        }

    def _generate_insights(self, sentiment_data: Dict, user_tier: str) -> List[str]:
        """生成情緒分析洞察"""
        insights = []
        
        overall_sentiment = sentiment_data["overall_sentiment"]
        fear_greed = sentiment_data["fear_greed_index"]
        social_sentiment = sentiment_data["social_sentiment"]
        
        # 基礎洞察 (所有用戶)
        if overall_sentiment > 30:
            insights.append("🟢 市場情緒整體偏向樂觀，投資者信心較強")
        elif overall_sentiment < -30:
            insights.append("🔴 市場情緒偏向悲觀，建議謹慎評估風險")
        else:
            insights.append("🟡 市場情緒處於中性區間，觀望氣氛濃厚")
            
        if fear_greed > 70:
            insights.append("⚠️ 恐慌貪婪指數顯示市場過度貪婪，注意回調風險")
        elif fear_greed < 30:
            insights.append("💎 恐慌貪婪指數顯示市場恐慌，可能是逢低買入機會")
            
        # 進階洞察 (Gold以上)
        if user_tier in ["gold", "diamond"]:
            if social_sentiment["mention_volume"] > 2000:
                insights.append("📈 社交媒體討論熱度高，關注度持續上升")
            
            trend = sentiment_data["sentiment_trend"]
            if trend in ["快速改善", "緩慢改善"]:
                insights.append("📊 情緒趨勢正向發展，市場信心逐步恢復")
            elif trend in ["快速惡化", "緩慢惡化"]:
                insights.append("📉 情緒趨勢轉負，建議密切關注市場變化")
                
        # 專業洞察 (Diamond)
        if user_tier == "diamond":
            behavior = sentiment_data["investor_behavior"]
            if behavior["institutional_flow"] == "買入" and behavior["foreign_investment"] == "流入":
                insights.append("🏦 機構投資者和外資同步買入，顯示長期看好")
            
            if behavior["options_activity"] == "看多" and overall_sentiment > 0:
                insights.append("📈 選擇權活動與情緒指標一致看多，多方動能強勁")
                
            technical_sentiment = sentiment_data["technical_sentiment"]
            if technical_sentiment["momentum_sentiment"] > 30 and technical_sentiment["volume_sentiment"] > 30:
                insights.append("⚡ 技術面動能與成交量情緒雙重確認，趨勢可靠度高")
        
        return insights

    def _generate_recommendation(self, sentiment_data: Dict) -> str:
        """生成投資建議"""
        overall_sentiment = sentiment_data["overall_sentiment"]
        fear_greed = sentiment_data["fear_greed_index"]
        trend = sentiment_data["sentiment_trend"]
        
        if overall_sentiment > 40 and fear_greed > 50 and trend in ["快速改善", "緩慢改善"]:
            return "STRONG_BUY"
        elif overall_sentiment > 20 and fear_greed > 40:
            return "BUY"
        elif overall_sentiment > -20 and overall_sentiment < 20:
            return "HOLD"
        elif overall_sentiment < -20 and fear_greed < 40:
            return "SELL"
        else:
            return "STRONG_SELL"

    def _calculate_confidence(self, sentiment_data: Dict) -> float:
        """計算分析信心度"""
        # 基於多個情緒指標的一致性計算信心度
        sentiment_consistency = 0
        
        overall = sentiment_data["overall_sentiment"]
        social_avg = sum(sentiment_data["social_sentiment"].values()) / 3 if isinstance(sentiment_data["social_sentiment"], dict) else 0
        news_avg = sum([v for v in sentiment_data["news_sentiment"].values() if isinstance(v, (int, float))]) / 3
        tech_avg = sum(sentiment_data["technical_sentiment"].values()) / 4
        
        sentiments = [overall, social_avg, news_avg, tech_avg]
        positive_count = sum(1 for s in sentiments if s > 10)
        negative_count = sum(1 for s in sentiments if s < -10)
        
        if positive_count >= 3 or negative_count >= 3:
            sentiment_consistency = 0.8
        elif positive_count >= 2 or negative_count >= 2:
            sentiment_consistency = 0.6
        else:
            sentiment_consistency = 0.4
            
        return min(0.95, max(0.5, sentiment_consistency + 0.1))

    def _assess_sentiment_risk(self, sentiment_data: Dict) -> Dict[str, Any]:
        """評估情緒相關風險"""
        fear_greed = sentiment_data["fear_greed_index"]
        trend = sentiment_data["sentiment_trend"]
        
        if fear_greed > 80 or trend == "快速惡化":
            risk_level = "HIGH"
            risk_factors = ["情緒過度樂觀", "可能面臨回調", "群體行為風險"]
        elif fear_greed < 20 or trend == "快速改善":
            risk_level = "MEDIUM"
            risk_factors = ["市場恐慌情緒", "情緒波動加劇", "不確定性增加"]
        else:
            risk_level = "LOW"
            risk_factors = ["情緒相對穩定", "風險可控"]
            
        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "sentiment_volatility": "高" if abs(sentiment_data["overall_sentiment"]) > 40 else "中" if abs(sentiment_data["overall_sentiment"]) > 20 else "低"
        }

    def _get_tier_limitations(self, user_tier: str) -> List[str]:
        """獲取用戶等級限制"""
        if user_tier == "free":
            return [
                "僅提供基礎情緒指標",
                "不包含詳細社交媒體分析",
                "限制進階行為模式洞察"
            ]
        elif user_tier == "gold":
            return [
                "不包含機構投資者行為深度分析",
                "選擇權活動分析有限"
            ]
        else:  # diamond
            return []

    def get_analyst_info(self) -> Dict[str, Any]:
        """獲取分析師基本資訊"""
        return {
            "analyst_id": self.analyst_id,
            "name": self.name,
            "description": self.description,
            "specialties": self.specialties,
            "analyst_type": "market_sentiment_analyst",
            "version": self.version,
            "supported_analysis": [
                "market_sentiment",
                "fear_greed_analysis", 
                "social_sentiment",
                "investor_behavior",
                "emotion_cycle"
            ]
        }

# 全局實例
market_sentiment_analyst = MarketSentimentAnalyst()