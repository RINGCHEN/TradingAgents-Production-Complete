#!/usr/bin/env python3
"""
情緒分析師 (SentimentAnalyst) - 不老傳說 AI分析師系統
天工 (TianGong) - 市場情緒和投資人心理分析專家

此分析師專門分析市場情緒、投資人心理、社群媒體討論等，
提供投資情緒面的專業洞察和建議。

功能特色：
1. 社群媒體情緒分析 (PTT、Dcard、Facebook等)
2. 投資人心理指標評估
3. 市場恐慌/貪婪指數計算
4. 散戶vs法人情緒對比
5. 群眾心理和羊群效應識別
6. Taiwan市場特色情緒分析
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import re
import math

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType, AnalysisConfidenceLevel

# 配置日誌
logger = logging.getLogger(__name__)

class SentimentLevel(Enum):
    """情緒等級"""
    EXTREMELY_BULLISH = "extremely_bullish"      # 極度樂觀
    BULLISH = "bullish"                          # 樂觀
    NEUTRAL = "neutral"                          # 中性
    BEARISH = "bearish"                          # 悲觀
    EXTREMELY_BEARISH = "extremely_bearish"      # 極度悲觀

class SentimentSource(Enum):
    """情緒來源"""
    PTT = "ptt"                                  # PTT討論板
    DCARD = "dcard"                              # Dcard
    FACEBOOK = "facebook"                        # Facebook
    YOUTUBE = "youtube"                          # YouTube
    NEWS_COMMENTS = "news_comments"              # 新聞留言
    BROKER_REPORTS = "broker_reports"            # 券商報告
    EXPERT_OPINION = "expert_opinion"            # 專家意見

class MarketSentimentType(Enum):
    """市場情緒類型"""
    FEAR = "fear"                                # 恐慌情緒
    GREED = "greed"                              # 貪婪情緒
    FOMO = "fomo"                                # 錯失恐懼症
    PANIC_SELLING = "panic_selling"              # 恐慌性賣出
    EUPHORIA = "euphoria"                        # 過度樂觀
    UNCERTAINTY = "uncertainty"                  # 不確定性
    CONFIDENCE = "confidence"                    # 信心

@dataclass
class SentimentIndicator:
    """情緒指標"""
    indicator_name: str                          # 指標名稱
    value: float                                 # 指標值 (-1.0 to 1.0)
    description: str                             # 描述
    source: SentimentSource                      # 數據來源
    reliability: float                           # 可靠度 (0.0 to 1.0)
    timestamp: str                               # 時間戳

@dataclass
class SentimentAnalysis:
    """情緒分析結果"""
    overall_sentiment: SentimentLevel            # 整體情緒
    sentiment_score: float                       # 情緒分數 (-1.0 to 1.0)
    confidence_level: float                      # 信心水準
    dominant_emotion: MarketSentimentType        # 主導情緒
    retail_sentiment: float                      # 散戶情緒
    institutional_sentiment: float               # 法人情緒
    sentiment_indicators: List[SentimentIndicator] # 情緒指標列表
    sentiment_trends: Dict[str, Any]             # 情緒趨勢
    psychological_factors: List[str]             # 心理因素

class SentimentAnalyst(BaseAnalyst):
    """情緒分析師 - 專業市場情緒和投資人心理分析"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化情緒分析師
        
        Args:
            config: 配置參數
        """
        super().__init__(config)
        self.analyst_id = "sentiment_analyst"
        
        # 情緒分析配置
        config = config or {}
        self.sentiment_config = config.get('sentiment_config', {
            'sentiment_threshold': 0.3,           # 情緒閾值
            'reliability_threshold': 0.6,         # 可靠度閾值
            'social_media_weight': 0.4,          # 社群媒體權重
            'institutional_weight': 0.6,          # 法人情緒權重
            'enable_taiwan_features': True        # 啟用Taiwan特色
        })
        
        # Taiwan社群媒體關鍵詞庫
        self.taiwan_keywords = {
            'bullish': [
                '看好', '買進', '持有', '看漲', '上漲', '利多', '噴出',
                '起飛', '突破', '強勢', '看多', '加碼', '進場', '抄底'
            ],
            'bearish': [
                '看空', '賣出', '下跌', '利空', '崩跌', '套牢', '停損',
                '出場', '避險', '看衰', '減碼', '逃命', '殺低'
            ],
            'uncertainty': [
                '觀望', '等等看', '不確定', '猶豫', '觀察', '小心',
                '謹慎', '風險', '不明朗', '震盪'
            ]
        }
        
        # Taiwan投資人心理特徵
        self.taiwan_psychology = {
            'herd_mentality': ['跟風', '追高', '殺低', '羊群效應'],
            'speculation': ['炒作', '題材', '消息面', '短線'],
            'conservatism': ['定存', '穩健', '長期', '基本面']
        }
        
        logger.info(f"情緒分析師初始化完成: {self.analyst_id}")
    
    def get_analysis_type(self) -> AnalysisType:
        """返回分析類型"""
        return AnalysisType.MARKET_SENTIMENT
    
    def get_analyst_info(self) -> Dict[str, Any]:
        """獲取分析師資訊"""
        base_info = super().get_analyst_info()
        base_info.update({
            'analyst_type': '情緒分析師',
            'specialties': [
                '社群媒體情緒分析',
                '投資人心理評估', 
                '市場恐慌/貪婪指數',
                '散戶vs法人情緒對比',
                'Taiwan市場心理特色'
            ],
            'data_sources': [
                'PTT股票板',
                'Dcard投資板', 
                'Facebook投資社團',
                '券商報告',
                '專家意見'
            ],
            'taiwan_features': self.sentiment_config.get('enable_taiwan_features', True)
        })
        return base_info
    
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """獲取分析提示詞"""
        return f"""
作為專業的市場情緒分析師，請分析股票 {state.stock_id} 的市場情緒狀況。

請重點分析：
1. 社群媒體情緒 (PTT、Dcard、Facebook等平台討論)
2. 投資人心理指標 (恐慌貪婪指數、Put/Call比率)
3. 散戶vs法人情緒對比
4. Taiwan市場特有的投資心理特徵
5. 羊群效應和投機氛圍評估

請提供專業的情緒面投資建議。
"""
    
    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """
        執行情緒分析
        
        Args:
            state: 分析狀態
            
        Returns:
            情緒分析結果
        """
        try:
            self.logger.info(f"情緒分析師開始分析: {state.stock_id}")
            
            # 收集情緒數據
            sentiment_data = await self._collect_sentiment_data(state)
            
            # 分析社群媒體情緒
            social_sentiment = await self._analyze_social_media_sentiment(sentiment_data, state)
            
            # 分析投資人心理指標
            psychological_indicators = await self._analyze_psychological_indicators(sentiment_data, state)
            
            # 計算市場情緒指數
            market_sentiment = await self._calculate_market_sentiment_index(
                social_sentiment, psychological_indicators, state
            )
            
            # 分析散戶vs法人情緒
            sentiment_comparison = await self._analyze_retail_vs_institutional(sentiment_data, state)
            
            # Taiwan市場特色分析
            taiwan_sentiment = await self._analyze_taiwan_market_psychology(sentiment_data, state)
            
            # 整合情緒分析結果
            sentiment_analysis = await self._integrate_sentiment_analysis(
                social_sentiment, psychological_indicators, market_sentiment,
                sentiment_comparison, taiwan_sentiment, state
            )
            
            # 生成LLM洞察
            llm_insights = await self._generate_sentiment_insights(sentiment_analysis, state)
            
            # 生成最終建議
            final_result = await self._generate_final_recommendation(
                sentiment_analysis, llm_insights, state
            )
            
            self.logger.info(f"情緒分析完成: {state.stock_id}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"情緒分析失敗: {state.stock_id}, 錯誤: {str(e)}")
            return self._create_error_result(state, str(e))
    
    async def _collect_sentiment_data(self, state: AnalysisState) -> Dict[str, Any]:
        """收集情緒相關數據"""
        sentiment_data = {
            'social_media': await self._mock_social_media_data(state.stock_id),
            'market_indicators': await self._mock_market_sentiment_indicators(state.stock_id),
            'expert_opinions': await self._mock_expert_opinions(state.stock_id),
            'news_sentiment': await self._extract_news_sentiment(state),
            'trading_patterns': await self._analyze_trading_patterns(state)
        }
        
        self.logger.debug(f"情緒數據收集完成: {state.stock_id}")
        return sentiment_data
    
    async def _mock_social_media_data(self, stock_id: str) -> Dict[str, Any]:
        """模擬社群媒體數據"""
        # 模擬PTT、Dcard等社群媒體討論數據
        return {
            'ptt_sentiment': {
                'positive_posts': 45,
                'negative_posts': 25,
                'neutral_posts': 30,
                'hot_keywords': ['看好', '營收', '成長', '技術'],
                'sentiment_score': 0.35
            },
            'dcard_sentiment': {
                'positive_posts': 38,
                'negative_posts': 32,
                'neutral_posts': 30,
                'engagement_score': 0.75,
                'sentiment_score': 0.12
            },
            'facebook_groups': {
                'total_mentions': 156,
                'positive_sentiment': 0.42,
                'negative_sentiment': 0.28,
                'neutral_sentiment': 0.30
            }
        }
    
    async def _mock_market_sentiment_indicators(self, stock_id: str) -> Dict[str, Any]:
        """模擬市場情緒指標"""
        return {
            'fear_greed_index': 65,  # 0-100, >50表示貪婪
            'vix_taiwan': 18.5,      # Taiwan VIX指數
            'put_call_ratio': 0.85,  # Put/Call比率
            'margin_trading': {
                'margin_buy': 1250,
                'margin_sell': 890,
                'ratio': 1.40
            },
            'foreign_sentiment': {
                'net_buy': 125.5,  # 外資買超(億)
                'sentiment': 'positive'
            }
        }
    
    async def _mock_expert_opinions(self, stock_id: str) -> Dict[str, Any]:
        """模擬專家意見"""
        return {
            'analyst_ratings': {
                'buy': 8,
                'hold': 12,
                'sell': 2,
                'average_target': 650.0
            },
            'broker_reports': [
                {'broker': '國泰證券', 'rating': 'BUY', 'target': 680, 'sentiment': 0.7},
                {'broker': '元大證券', 'rating': 'HOLD', 'target': 620, 'sentiment': 0.2},
                {'broker': '富邦證券', 'rating': 'BUY', 'target': 660, 'sentiment': 0.6}
            ]
        }
    
    async def _extract_news_sentiment(self, state: AnalysisState) -> Dict[str, Any]:
        """從新聞數據中提取情緒"""
        news_data = state.news_data or {}
        
        # 簡化的新聞情緒分析
        positive_keywords = ['成長', '獲利', '突破', '創新', '利多']
        negative_keywords = ['下滑', '虧損', '衰退', '利空', '風險']
        
        news_sentiment = {
            'overall_sentiment': 0.25,
            'positive_news_count': 12,
            'negative_news_count': 8,
            'neutral_news_count': 15,
            'sentiment_trend': 'improving'
        }
        
        return news_sentiment
    
    async def _analyze_trading_patterns(self, state: AnalysisState) -> Dict[str, Any]:
        """分析交易模式情緒"""
        # 基於交易量、價格波動等分析投資人情緒
        return {
            'volume_sentiment': {
                'volume_trend': 'increasing',
                'high_volume_days': 8,
                'sentiment_score': 0.3
            },
            'price_action_sentiment': {
                'volatility': 'moderate',
                'support_resistance': 'strong_support',
                'sentiment_score': 0.15
            }
        }
    
    async def _analyze_social_media_sentiment(
        self, sentiment_data: Dict[str, Any], state: AnalysisState
    ) -> SentimentAnalysis:
        """分析社群媒體情緒"""
        
        social_media = sentiment_data.get('social_media', {})
        
        # 計算綜合社群情緒分數
        ptt_score = social_media.get('ptt_sentiment', {}).get('sentiment_score', 0)
        dcard_score = social_media.get('dcard_sentiment', {}).get('sentiment_score', 0)
        fb_positive = social_media.get('facebook_groups', {}).get('positive_sentiment', 0)
        fb_negative = social_media.get('facebook_groups', {}).get('negative_sentiment', 0)
        
        social_sentiment_score = (ptt_score * 0.4 + dcard_score * 0.3 + 
                                (fb_positive - fb_negative) * 0.3)
        
        # 判斷情緒等級
        if social_sentiment_score > 0.3:
            sentiment_level = SentimentLevel.BULLISH
            dominant_emotion = MarketSentimentType.CONFIDENCE
        elif social_sentiment_score > 0.1:
            sentiment_level = SentimentLevel.NEUTRAL
            dominant_emotion = MarketSentimentType.UNCERTAINTY
        elif social_sentiment_score > -0.1:
            sentiment_level = SentimentLevel.NEUTRAL
            dominant_emotion = MarketSentimentType.UNCERTAINTY
        elif social_sentiment_score > -0.3:
            sentiment_level = SentimentLevel.BEARISH
            dominant_emotion = MarketSentimentType.FEAR
        else:
            sentiment_level = SentimentLevel.EXTREMELY_BEARISH
            dominant_emotion = MarketSentimentType.PANIC_SELLING
        
        # 創建情緒指標
        indicators = [
            SentimentIndicator(
                indicator_name="PTT討論情緒",
                value=ptt_score,
                description=f"PTT股票板討論情緒: {ptt_score:.2f}",
                source=SentimentSource.PTT,
                reliability=0.7,
                timestamp=datetime.now().isoformat()
            ),
            SentimentIndicator(
                indicator_name="Dcard投資情緒", 
                value=dcard_score,
                description=f"Dcard投資板情緒: {dcard_score:.2f}",
                source=SentimentSource.DCARD,
                reliability=0.6,
                timestamp=datetime.now().isoformat()
            )
        ]
        
        return SentimentAnalysis(
            overall_sentiment=sentiment_level,
            sentiment_score=social_sentiment_score,
            confidence_level=0.75,
            dominant_emotion=dominant_emotion,
            retail_sentiment=social_sentiment_score * 1.2,  # 散戶情緒較放大
            institutional_sentiment=social_sentiment_score * 0.7,  # 法人較理性
            sentiment_indicators=indicators,
            sentiment_trends={'trend': 'stable', 'momentum': 'neutral'},
            psychological_factors=['社群討論熱度', '散戶參與度']
        )
    
    async def _analyze_psychological_indicators(
        self, sentiment_data: Dict[str, Any], state: AnalysisState
    ) -> Dict[str, Any]:
        """分析投資人心理指標"""
        
        market_indicators = sentiment_data.get('market_indicators', {})
        
        # Fear & Greed Index分析
        fear_greed = market_indicators.get('fear_greed_index', 50)
        if fear_greed > 75:
            psychological_state = "極度貪婪"
            risk_level = "高"
        elif fear_greed > 55:
            psychological_state = "貪婪"
            risk_level = "中高"
        elif fear_greed > 45:
            psychological_state = "中性"
            risk_level = "中"
        elif fear_greed > 25:
            psychological_state = "恐懼"
            risk_level = "中高"
        else:
            psychological_state = "極度恐懼"
            risk_level = "高"
        
        # Put/Call比率分析
        put_call_ratio = market_indicators.get('put_call_ratio', 1.0)
        if put_call_ratio > 1.2:
            put_call_sentiment = "過度悲觀"
        elif put_call_ratio > 0.8:
            put_call_sentiment = "正常"
        else:
            put_call_sentiment = "過度樂觀"
        
        return {
            'fear_greed_analysis': {
                'index': fear_greed,
                'state': psychological_state,
                'risk_level': risk_level
            },
            'put_call_analysis': {
                'ratio': put_call_ratio,
                'sentiment': put_call_sentiment
            },
            'overall_psychology': {
                'dominant_emotion': psychological_state,
                'market_phase': '牛市' if fear_greed > 60 else '熊市' if fear_greed < 40 else '整理'
            }
        }
    
    async def _calculate_market_sentiment_index(
        self, social_sentiment: SentimentAnalysis, 
        psychological_indicators: Dict[str, Any], 
        state: AnalysisState
    ) -> Dict[str, Any]:
        """計算市場情緒指數"""
        
        # 綜合各項指標計算市場情緒指數
        social_score = social_sentiment.sentiment_score
        fear_greed = psychological_indicators['fear_greed_analysis']['index']
        fear_greed_normalized = (fear_greed - 50) / 50  # 標準化到-1到1
        
        # 加權計算綜合情緒指數
        composite_sentiment = (
            social_score * 0.4 +           # 社群媒體情緒 40%
            fear_greed_normalized * 0.4 +  # 恐慌貪婪指數 40%
            0.1 * 0.2                      # 其他指標 20%
        )
        
        # 情緒強度
        sentiment_intensity = abs(composite_sentiment)
        
        # 情緒方向
        if composite_sentiment > 0.3:
            sentiment_direction = "強烈看多"
        elif composite_sentiment > 0.1:
            sentiment_direction = "溫和看多"
        elif composite_sentiment > -0.1:
            sentiment_direction = "中性觀望"
        elif composite_sentiment > -0.3:
            sentiment_direction = "溫和看空"
        else:
            sentiment_direction = "強烈看空"
        
        return {
            'composite_sentiment_index': composite_sentiment,
            'sentiment_intensity': sentiment_intensity,
            'sentiment_direction': sentiment_direction,
            'market_phase': self._determine_market_phase(composite_sentiment),
            'sentiment_reliability': min(0.8, 0.5 + sentiment_intensity)
        }
    
    def _determine_market_phase(self, sentiment_score: float) -> str:
        """確定市場階段"""
        if sentiment_score > 0.5:
            return "狂熱期"
        elif sentiment_score > 0.2:
            return "樂觀期"
        elif sentiment_score > -0.2:
            return "平衡期"
        elif sentiment_score > -0.5:
            return "悲觀期"
        else:
            return "恐慌期"
    
    async def _analyze_retail_vs_institutional(
        self, sentiment_data: Dict[str, Any], state: AnalysisState
    ) -> Dict[str, Any]:
        """分析散戶vs法人情緒對比"""
        
        social_media = sentiment_data.get('social_media', {})
        market_indicators = sentiment_data.get('market_indicators', {})
        expert_opinions = sentiment_data.get('expert_opinions', {})
        
        # 散戶情緒 (主要來自社群媒體)
        retail_sentiment = (
            social_media.get('ptt_sentiment', {}).get('sentiment_score', 0) * 0.4 +
            social_media.get('dcard_sentiment', {}).get('sentiment_score', 0) * 0.3 +
            (social_media.get('facebook_groups', {}).get('positive_sentiment', 0) - 
             social_media.get('facebook_groups', {}).get('negative_sentiment', 0)) * 0.3
        )
        
        # 法人情緒 (來自外資動向、專家意見)
        foreign_sentiment = 1 if market_indicators.get('foreign_sentiment', {}).get('sentiment') == 'positive' else -1
        broker_sentiment = self._calculate_broker_sentiment(expert_opinions.get('broker_reports', []))
        
        institutional_sentiment = (foreign_sentiment * 0.6 + broker_sentiment * 0.4) * 0.3
        
        # 情緒差異分析
        sentiment_divergence = retail_sentiment - institutional_sentiment
        
        if abs(sentiment_divergence) > 0.3:
            divergence_level = "顯著分歧"
        elif abs(sentiment_divergence) > 0.1:
            divergence_level = "輕微分歧"
        else:
            divergence_level = "基本一致"
        
        return {
            'retail_sentiment': retail_sentiment,
            'institutional_sentiment': institutional_sentiment,
            'sentiment_divergence': sentiment_divergence,
            'divergence_level': divergence_level,
            'market_implication': self._interpret_sentiment_divergence(sentiment_divergence)
        }
    
    def _calculate_broker_sentiment(self, broker_reports: List[Dict[str, Any]]) -> float:
        """計算券商情緒"""
        if not broker_reports:
            return 0.0
        
        sentiment_sum = sum(report.get('sentiment', 0) for report in broker_reports)
        return sentiment_sum / len(broker_reports)
    
    def _interpret_sentiment_divergence(self, divergence: float) -> str:
        """解釋情緒分歧"""
        if divergence > 0.3:
            return "散戶過度樂觀，法人較謹慎，可能存在回檔風險"
        elif divergence > 0.1:
            return "散戶略顯樂觀，法人持中性態度"
        elif divergence > -0.1:
            return "散戶與法人看法基本一致"
        elif divergence > -0.3:
            return "法人較散戶樂觀，可能存在投資機會"
        else:
            return "法人明顯較散戶樂觀，建議關注法人動向"
    
    async def _analyze_taiwan_market_psychology(
        self, sentiment_data: Dict[str, Any], state: AnalysisState
    ) -> Dict[str, Any]:
        """分析Taiwan市場心理特色"""
        
        # Taiwan投資人特色分析
        taiwan_features = {
            'speculation_level': 'moderate',  # 投機程度
            'herd_mentality': 'strong',       # 羊群效應
            'technical_focus': 'high',        # 技術面關注度
            'news_sensitivity': 'high',       # 消息敏感度
            'short_term_focus': 'very_high'   # 短線操作傾向
        }
        
        # 基於社群媒體數據分析Taiwan特色
        social_media = sentiment_data.get('social_media', {})
        ptt_keywords = social_media.get('ptt_sentiment', {}).get('hot_keywords', [])
        
        speculation_score = self._calculate_speculation_score(ptt_keywords)
        herd_score = self._calculate_herd_mentality_score(social_media)
        
        return {
            'taiwan_characteristics': taiwan_features,
            'speculation_analysis': {
                'score': speculation_score,
                'level': 'high' if speculation_score > 0.6 else 'moderate'
            },
            'herd_mentality_analysis': {
                'score': herd_score,
                'risk': 'high' if herd_score > 0.7 else 'moderate'
            },
            'market_psychology_summary': self._summarize_taiwan_psychology(
                speculation_score, herd_score
            )
        }
    
    def _calculate_speculation_score(self, keywords: List[str]) -> float:
        """計算投機程度分數"""
        speculation_keywords = ['短線', '炒作', '題材', '消息', '爆量']
        
        speculation_count = sum(1 for keyword in keywords 
                              if any(spec in keyword for spec in speculation_keywords))
        
        return min(1.0, speculation_count / max(len(keywords), 1) * 2)
    
    def _calculate_herd_mentality_score(self, social_media: Dict[str, Any]) -> float:
        """計算羊群效應分數"""
        # 基於討論熱度和一致性計算羊群效應
        ptt_posts = social_media.get('ptt_sentiment', {})
        total_posts = (ptt_posts.get('positive_posts', 0) + 
                      ptt_posts.get('negative_posts', 0) + 
                      ptt_posts.get('neutral_posts', 0))
        
        max_sentiment_posts = max(
            ptt_posts.get('positive_posts', 0),
            ptt_posts.get('negative_posts', 0),
            ptt_posts.get('neutral_posts', 0)
        )
        
        if total_posts == 0:
            return 0.5
        
        consensus_ratio = max_sentiment_posts / total_posts
        return min(1.0, consensus_ratio * 1.5)
    
    def _summarize_taiwan_psychology(self, speculation_score: float, herd_score: float) -> str:
        """總結Taiwan市場心理"""
        if speculation_score > 0.7 and herd_score > 0.7:
            return "市場投機氛圍濃厚，羊群效應明顯，需警惕泡沫風險"
        elif speculation_score > 0.5 or herd_score > 0.7:
            return "市場情緒偏向短線操作，建議理性投資"
        else:
            return "市場情緒相對理性，投資環境較為健康"
    
    async def _integrate_sentiment_analysis(
        self, social_sentiment: SentimentAnalysis,
        psychological_indicators: Dict[str, Any],
        market_sentiment: Dict[str, Any],
        sentiment_comparison: Dict[str, Any],
        taiwan_sentiment: Dict[str, Any],
        state: AnalysisState
    ) -> Dict[str, Any]:
        """整合情緒分析結果"""
        
        composite_sentiment = market_sentiment['composite_sentiment_index']
        sentiment_reliability = market_sentiment['sentiment_reliability']
        
        # 風險評估
        risk_factors = []
        if taiwan_sentiment['speculation_analysis']['score'] > 0.6:
            risk_factors.append("投機氛圍濃厚")
        if taiwan_sentiment['herd_mentality_analysis']['score'] > 0.7:
            risk_factors.append("羊群效應風險")
        if abs(sentiment_comparison['sentiment_divergence']) > 0.3:
            risk_factors.append("散戶法人情緒分歧")
        
        # 投資建議邏輯
        if composite_sentiment > 0.3 and sentiment_reliability > 0.7:
            investment_suggestion = "BUY"
            suggestion_reason = "市場情緒樂觀，多項指標支持"
        elif composite_sentiment > 0.1:
            investment_suggestion = "HOLD"
            suggestion_reason = "市場情緒溫和正面，建議持有觀察"
        elif composite_sentiment > -0.1:
            investment_suggestion = "HOLD"
            suggestion_reason = "市場情緒中性，建議謹慎觀察"
        elif composite_sentiment > -0.3:
            investment_suggestion = "SELL"
            suggestion_reason = "市場情緒偏空，建議謹慎"
        else:
            investment_suggestion = "SELL"
            suggestion_reason = "市場情緒極度悲觀，建議避險"
        
        return {
            'integrated_sentiment': {
                'composite_score': composite_sentiment,
                'reliability': sentiment_reliability,
                'direction': market_sentiment['sentiment_direction'],
                'market_phase': market_sentiment['market_phase']
            },
            'risk_assessment': {
                'risk_factors': risk_factors,
                'risk_level': len(risk_factors)
            },
            'investment_suggestion': {
                'action': investment_suggestion,
                'reason': suggestion_reason,
                'confidence': sentiment_reliability
            },
            'taiwan_insights': {
                'market_characteristics': taiwan_sentiment['taiwan_characteristics'],
                'psychology_summary': taiwan_sentiment['market_psychology_summary']
            }
        }
    
    async def _generate_sentiment_insights(
        self, sentiment_analysis: Dict[str, Any], state: AnalysisState
    ) -> Dict[str, Any]:
        """使用LLM生成情緒洞察"""
        
        # 準備LLM輸入
        llm_prompt = self._prepare_sentiment_prompt(sentiment_analysis, state)
        
        try:
            # 模擬LLM分析 (實際應該整合真實LLM客戶端)
            await asyncio.sleep(0.5)  # 模擬處理時間
            insights = self._generate_fallback_insights(sentiment_analysis)
            
        except Exception as e:
            self.logger.warning(f"LLM情緒洞察生成失敗: {str(e)}")
            insights = self._generate_fallback_insights(sentiment_analysis)
        
        return insights
    
    def _prepare_sentiment_prompt(
        self, sentiment_analysis: Dict[str, Any], state: AnalysisState
    ) -> str:
        """準備情緒分析LLM提示"""
        
        composite_score = sentiment_analysis['integrated_sentiment']['composite_score']
        market_phase = sentiment_analysis['integrated_sentiment']['market_phase']
        risk_factors = sentiment_analysis['risk_assessment']['risk_factors']
        taiwan_summary = sentiment_analysis['taiwan_insights']['psychology_summary']
        
        prompt = f"""
作為專業的市場情緒分析師，請分析以下Taiwan股市情緒數據：

股票代號: {state.stock_id}
綜合情緒分數: {composite_score:.3f} (-1到1，負數看空，正數看多)
市場階段: {market_phase}
風險因素: {', '.join(risk_factors) if risk_factors else '無特殊風險'}
Taiwan市場心理: {taiwan_summary}

請提供：
1. 情緒分析總結 (2-3句)
2. 投資心理洞察 (關鍵心理因素)
3. Taiwan市場特色影響
4. 情緒面風險提示
5. 建議操作策略

請用繁體中文回答，專業且實用。
"""
        return prompt
    
    def _parse_llm_sentiment_response(self, llm_response: str) -> Dict[str, Any]:
        """解析LLM情緒分析回應"""
        # 簡化的回應解析
        return {
            'sentiment_summary': "市場情緒分析：當前投資人情緒處於相對理性狀態",
            'psychological_insights': [
                "投資人心理面臨謹慎樂觀與不確定性的交錯",
                "社群媒體討論熱度反映市場關注度"
            ],
            'taiwan_market_impact': "Taiwan投資人短線操作傾向明顯，對消息面敏感度較高",
            'risk_warnings': [
                "注意羊群效應可能帶來的波動放大",
                "散戶情緒波動可能影響短期走勢"
            ],
            'strategy_recommendations': [
                "建議理性投資，避免情緒化決策",
                "可適度參考法人動向作為參考指標"
            ]
        }
    
    def _generate_fallback_insights(self, sentiment_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成備用洞察"""
        composite_score = sentiment_analysis['integrated_sentiment']['composite_score']
        
        if composite_score > 0.2:
            sentiment_summary = "市場情緒偏向樂觀，投資人信心相對較強"
        elif composite_score > -0.2:
            sentiment_summary = "市場情緒保持中性，投資人態度較為謹慎"
        else:
            sentiment_summary = "市場情緒偏向悲觀，投資人普遍較為保守"
        
        return {
            'sentiment_summary': sentiment_summary,
            'psychological_insights': ["基於綜合情緒指標的分析結果"],
            'taiwan_market_impact': "Taiwan市場特有的投資心理影響",
            'risk_warnings': ["建議關注市場情緒變化"],
            'strategy_recommendations': ["建議保持理性投資態度"]
        }
    
    async def _generate_final_recommendation(
        self, sentiment_analysis: Dict[str, Any], 
        llm_insights: Dict[str, Any], 
        state: AnalysisState
    ) -> AnalysisResult:
        """生成最終建議"""
        
        # 提取關鍵指標
        composite_sentiment = sentiment_analysis['integrated_sentiment']['composite_score']
        reliability = sentiment_analysis['integrated_sentiment']['reliability']
        suggestion = sentiment_analysis['investment_suggestion']['action']
        
        # 構建推理邏輯
        reasoning = [
            f"綜合情緒分數: {composite_sentiment:.3f}",
            f"市場階段: {sentiment_analysis['integrated_sentiment']['market_phase']}",
            f"投資建議: {suggestion}",
            llm_insights['sentiment_summary']
        ]
        
        # 構建風險因素
        risk_factors = sentiment_analysis['risk_assessment']['risk_factors'].copy()
        risk_factors.extend(llm_insights.get('risk_warnings', []))
        
        # 確定信心等級
        if reliability > 0.8:
            confidence_level = AnalysisConfidenceLevel.VERY_HIGH
        elif reliability > 0.6:
            confidence_level = AnalysisConfidenceLevel.HIGH
        elif reliability > 0.4:
            confidence_level = AnalysisConfidenceLevel.MODERATE
        else:
            confidence_level = AnalysisConfidenceLevel.LOW
        
        # 技術指標數據
        technical_indicators = {
            'sentiment_analysis': sentiment_analysis,
            'taiwan_insights': llm_insights.get('taiwan_market_impact'),
            'strategy_recommendations': llm_insights.get('strategy_recommendations', [])
        }
        
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation=suggestion,
            confidence=reliability,
            confidence_level=confidence_level,
            reasoning=reasoning[:5],  # 限制推理數量
            risk_factors=risk_factors[:5],  # 限制風險因素數量
            technical_indicators=technical_indicators,
            model_used="sentiment_analysis_model",
            timestamp=datetime.now().isoformat()
        )

# 便利函數
async def analyze_market_sentiment(
    stock_id: str,
    user_context: Optional[Dict[str, Any]] = None
) -> AnalysisResult:
    """
    快速市場情緒分析
    
    Args:
        stock_id: 股票代號
        user_context: 用戶上下文
        
    Returns:
        情緒分析結果
    """
    analyst = SentimentAnalyst()
    
    state = AnalysisState(
        stock_id=stock_id,
        analysis_date=datetime.now().strftime('%Y-%m-%d'),
        user_context=user_context
    )
    
    return await analyst.analyze(state)

if __name__ == "__main__":
    # 測試腳本
    async def test_sentiment_analyst():
        print("測試情緒分析師...")
        
        # 創建情緒分析師
        analyst = SentimentAnalyst({'debug': True})
        print(f"分析師ID: {analyst.analyst_id}")
        print(f"分析師資訊: {analyst.get_analyst_info()}")
        
        # 創建測試狀態
        state = AnalysisState(
            stock_id='2330',
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            user_context={'user_id': 'test_user', 'membership_tier': 'DIAMOND'}
        )
        
        # 執行分析
        result = await analyst.analyze(state)
        
        print(f"\n情緒分析結果:")
        print(f"  建議: {result.recommendation}")
        print(f"  信心度: {result.confidence:.2f}")
        print(f"  推理: {result.reasoning}")
        print(f"  風險因素: {result.risk_factors}")
        
        # 測試便利函數
        quick_result = await analyze_market_sentiment('2454')
        print(f"\n快速分析結果: {quick_result.recommendation}")
        
        print("情緒分析師測試完成！")
    
    asyncio.run(test_sentiment_analyst())