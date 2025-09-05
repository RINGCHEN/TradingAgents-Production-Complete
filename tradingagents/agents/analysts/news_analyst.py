#!/usr/bin/env python3
"""
News Analyst - 新聞分析師
天工 (TianGong) - 整合原工程師設計與天工優化的新聞情緒分析師

此模組提供：
1. 新聞數據獲取功能
2. 新聞事件影響分析
3. 關鍵字提取和分類
4. 天工成本優化和智能分析
"""

from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import asyncio
import re
from collections import Counter

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType


class NewsAnalyst(BaseAnalyst):
    """新聞分析師 - 天工優化版"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 新聞重要性權重配置
        self.news_weights = {
            'earnings': 0.3,         # 財報相關
            'management': 0.25,      # 經營層異動
            'industry': 0.2,         # 產業政策
            'market': 0.15,          # 市場趨勢
            'technical': 0.1         # 技術發展
        }
        
        # 新聞來源可信度評分
        self.source_credibility = {
            '經濟日報': 0.9,
            '工商時報': 0.9,
            '中央社': 0.95,
            '財訊雜誌': 0.85,
            '科技新報': 0.8,
            '商周': 0.85,
            'MoneyDJ': 0.8,
            '鉅亨網': 0.75,
            '自由時報': 0.7,
            '聯合報': 0.8,
            '其他': 0.6
        }
        
        # 情緒分析關鍵詞庫 (簡化版)
        self.sentiment_keywords = {
            'positive': [
                '成長', '獲利', '突破', '創新', '領先', '優勢', '看好', '上調',
                '擴張', '合作', '訂單', '營收', '利多', '強勁', '亮眼', '超越'
            ],
            'negative': [
                '下滑', '虧損', '衰退', '困難', '挑戰', '風險', '下修', '疲軟',
                '競爭', '壓力', '減少', '削減', '警告', '擔憂', '不確定', '下跌'
            ],
            'neutral': [
                '持平', '維持', '觀察', '評估', '調整', '計畫', '預計', '預期'
            ]
        }
        
        # Taiwan股市特色新聞分類
        self.taiwan_news_categories = {
            '法人動向': ['外資', '投信', '自營商', '持股', '買超', '賣超', '大戶', '融資', '融券'],
            '政策影響': ['政府', '央行', '金管會', '經濟部', '政策', '法規', '補助', '稅收', '監管'],
            '產業趨勢': ['半導體', '電子', '金融', '傳產', '生技', '綠能', 'AI', '物聯網', '5G'],
            '兩岸關係': ['中國', '大陸', '貿易戰', '供應鏈', '台商', '關稅', '制裁'],
            '國際情勢': ['美國', '聯準會', '升息', '通膨', '地緣政治', '歐洲', '日本', '原油'],
            '財報事件': ['財報', '營收', '獲利', '股利', '除權息', '業績', 'EPS', '毛利率'],
            '公司治理': ['董事會', '股東會', '併購', '增資', '減資', '私募', '庫藏股'],
            '技術創新': ['研發', '專利', '新產品', '技術突破', '創新', '授權', '合作']
        }
    
    def get_analysis_type(self) -> AnalysisType:
        """獲取分析類型"""
        return AnalysisType.NEWS_SENTIMENT
    
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """生成新聞分析提示詞"""
        stock_id = state.stock_id
        
        prompt = f"""
請作為專業的新聞分析師，針對台股代碼 {stock_id} 進行新聞情緒和事件影響分析。

請基於以下新聞數據進行分析：
新聞數據：{state.news_data if state.news_data else '待獲取'}

分析重點：
1. 新聞情緒分析 (正面、負面、中性比例)
2. 關鍵事件識別 (財報、併購、產品發布、政策變化)
3. 新聞影響程度評估 (短期、中期、長期影響)
4. 市場關注度分析 (新聞數量、媒體覆蓋度)
5. Taiwan市場特色分析 (法人動向、政策影響、產業趨勢)
6. 事件驅動的價格影響預測
7. 新聞可信度和來源權威性評估

特別關注：
- 法人進出相關新聞
- 產業政策變化
- 國際市場對Taiwan科技業的影響
- 兩岸關係對相關個股的影響

請提供：
- 明確的投資建議 (BUY/SELL/HOLD)
- 0-1之間的信心度分數
- 詳細的分析理由
- 主要新聞事件對股價的預期影響
- 需要關注的風險因素
"""
        return prompt
    
    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """執行新聞分析"""
        return await self._execute_analysis_with_optimization(state)
    
    async def _perform_core_analysis(self, state: AnalysisState, model_config) -> AnalysisResult:
        """執行核心新聞分析邏輯"""
        
        try:
            # 1. 獲取新聞數據
            news_data = await self._get_news_data(state.stock_id)
            
            # 2. 進行情緒分析
            sentiment_analysis = await self._analyze_news_sentiment(news_data)
            
            # 3. 識別關鍵事件
            key_events = await self._identify_key_events(news_data)
            
            # 4. 評估新聞影響
            impact_assessment = await self._assess_news_impact(news_data, key_events)
            
            # 5. Taiwan市場特色分析
            taiwan_insights = await self._analyze_taiwan_market_news(news_data)
            
            # 6. 生成分析上下文
            analysis_context = self._prepare_news_context(
                state, news_data, sentiment_analysis, key_events, impact_assessment, taiwan_insights
            )
            
            # 7. 調用LLM進行智慧分析
            llm_result = await self._call_llm_analysis(
                self.get_analysis_prompt(state), 
                analysis_context, 
                model_config
            )
            
            # 8. 創建分析結果
            from .base_analyst import AnalysisConfidenceLevel
            
            confidence_score = llm_result.get('confidence', 0.5)
            
            # 計算信心度級別
            if confidence_score >= 0.8:
                confidence_level = AnalysisConfidenceLevel.VERY_HIGH
            elif confidence_score >= 0.6:
                confidence_level = AnalysisConfidenceLevel.HIGH
            elif confidence_score >= 0.4:
                confidence_level = AnalysisConfidenceLevel.MODERATE
            elif confidence_score >= 0.2:
                confidence_level = AnalysisConfidenceLevel.LOW
            else:
                confidence_level = AnalysisConfidenceLevel.VERY_LOW
            
            result = AnalysisResult(
                analyst_id=self.analyst_id,
                stock_id=state.stock_id,
                analysis_date=state.analysis_date,
                analysis_type=self.get_analysis_type(),
                recommendation=llm_result.get('recommendation', 'HOLD'),
                confidence=confidence_score,
                confidence_level=confidence_level,
                reasoning=llm_result.get('reasoning', []),
                risk_factors=llm_result.get('risk_factors', []),
                taiwan_insights=taiwan_insights,
                market_conditions={
                    'news_sentiment': sentiment_analysis,
                    'key_events': key_events,
                    'impact_assessment': impact_assessment
                },
                model_used=model_config.model_name if hasattr(model_config, 'model_name') else 'news_analysis_model'
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"新聞分析失敗: {str(e)}")
            return self._create_error_result(state, str(e))
    
    async def _get_news_data(self, stock_id: str) -> List[Dict[str, Any]]:
        """獲取新聞數據"""
        
        try:
            # 模擬新聞數據獲取 (實際應整合新聞API)
            await asyncio.sleep(0.3)
            
            # 根據股票代碼生成相關模擬新聞
            company_names = {
                '2330': '台積電',
                '2454': '聯發科',
                '2317': '鴻海',
                '2882': '國泰金',
                '1301': '台塑',
                '2412': '中華電',
                '2002': '中鋼',
                '3008': '大立光',
                '2357': '華碩'
            }
            
            company_name = company_names.get(stock_id, f'股票{stock_id}')
            
            # 更豐富的模擬新聞數據
            mock_news = [
                {
                    'title': f'{company_name}第三季財報超預期，獲利創新高',
                    'content': f'{company_name}公布第三季財報，營收和淨利雙雙超越市場預期，EPS達到3.2元，超出法人預估的2.8元，毛利率維持在50%以上，展現強勁競爭力。',
                    'published_date': (datetime.now() - timedelta(days=1)).isoformat(),
                    'source': '經濟日報',
                    'sentiment_score': 0.8,
                    'importance': 'high',
                    'url': 'https://example.com/news1',
                    'credibility_score': 0.9,
                    'impact_score': 0.85
                },
                {
                    'title': f'外資連續買超{company_name}，目標價上調至500元',
                    'content': f'外資券商摩根士丹利連續三日買超{company_name}，累計買超張數達5000張，並將目標價由450元上調至500元，維持買進評等。',
                    'published_date': (datetime.now() - timedelta(days=2)).isoformat(),
                    'source': '工商時報',
                    'sentiment_score': 0.7,
                    'importance': 'high',
                    'url': 'https://example.com/news2',
                    'credibility_score': 0.9,
                    'impact_score': 0.75
                },
                {
                    'title': f'{company_name}發布3奈米製程新技術，領先全球',
                    'content': f'{company_name}正式發布3奈米製程技術，良率已達70%，領先競爭對手至少一年，預期將大幅提升高階晶片產能。',
                    'published_date': (datetime.now() - timedelta(days=3)).isoformat(),
                    'source': '科技新報',
                    'sentiment_score': 0.9,
                    'importance': 'high',
                    'url': 'https://example.com/news3',
                    'credibility_score': 0.8,
                    'impact_score': 0.9
                },
                {
                    'title': f'產業競爭加劇，{company_name}面臨成本壓力',
                    'content': f'隨著產業競爭加劇和原物料價格上漲，{company_name}毛利率面臨壓力，需要透過技術創新和規模經濟來維持競爭優勢。',
                    'published_date': (datetime.now() - timedelta(days=4)).isoformat(),
                    'source': '財訊雜誌',
                    'sentiment_score': -0.3,
                    'importance': 'medium',
                    'url': 'https://example.com/news4',
                    'credibility_score': 0.85,
                    'impact_score': 0.6
                },
                {
                    'title': f'{company_name}與蘋果簽署長期供應協議',
                    'content': f'{company_name}宣布與蘋果公司簽署為期5年的長期供應協議，預計每年帶來超過200億美元營收，強化雙方合作關係。',
                    'published_date': (datetime.now() - timedelta(days=5)).isoformat(),
                    'source': '中央社',
                    'sentiment_score': 0.8,
                    'importance': 'high',
                    'url': 'https://example.com/news5',
                    'credibility_score': 0.95,
                    'impact_score': 0.9
                },
                {
                    'title': f'投信持續加碼{company_name}，持股比重創新高',
                    'content': f'據統計，投信法人持續加碼{company_name}，持股比重已達8.5%，創下歷史新高，顯示法人對公司長期前景看好。',
                    'published_date': (datetime.now() - timedelta(days=6)).isoformat(),
                    'source': 'MoneyDJ',
                    'sentiment_score': 0.6,
                    'importance': 'medium',
                    'url': 'https://example.com/news6',
                    'credibility_score': 0.8,
                    'impact_score': 0.65
                },
                {
                    'title': f'市場傳言{company_name}考慮海外設廠',
                    'content': f'市場傳言{company_name}正評估在美國或歐洲設立新廠，以因應地緣政治風險和客戶在地化需求，但公司尚未正式回應。',
                    'published_date': (datetime.now() - timedelta(days=7)).isoformat(),
                    'source': '其他',
                    'sentiment_score': 0.2,
                    'importance': 'low',
                    'url': 'https://example.com/news7',
                    'credibility_score': 0.6,
                    'impact_score': 0.4
                }
            ]
            
            # 為每則新聞添加可信度評分
            for news in mock_news:
                source = news.get('source', '其他')
                news['credibility_score'] = self.source_credibility.get(source, 0.6)
                
                # 計算綜合影響分數
                sentiment_weight = abs(news.get('sentiment_score', 0)) * 0.4
                importance_weight = {'high': 0.8, 'medium': 0.5, 'low': 0.2}.get(news.get('importance', 'low'), 0.2)
                credibility_weight = news['credibility_score'] * 0.3
                news['impact_score'] = sentiment_weight + importance_weight + credibility_weight
            
            return mock_news
            
        except Exception as e:
            self.logger.error(f"新聞數據獲取失敗: {str(e)}")
            return []
    
    async def _analyze_news_sentiment(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析新聞情緒"""
        
        if not news_data:
            return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0}
        
        try:
            sentiment_scores = []
            sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            for news in news_data:
                # 使用預設sentiment_score或根據內容分析
                score = news.get('sentiment_score', 0.0)
                sentiment_scores.append(score)
                
                # 分類情緒
                if score > 0.2:
                    sentiment_counts['positive'] += 1
                elif score < -0.2:
                    sentiment_counts['negative'] += 1
                else:
                    sentiment_counts['neutral'] += 1
                
                # 使用關鍵詞分析補強 (簡化版)
                content = news.get('content', '') + news.get('title', '')
                keyword_sentiment = self._analyze_keyword_sentiment(content)
                sentiment_scores.append(keyword_sentiment)
            
            # 計算整體情緒
            overall_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            total_news = len(news_data)
            
            sentiment_analysis = {
                'overall_sentiment': self._classify_sentiment(overall_score),
                'sentiment_score': round(overall_score, 3),
                'sentiment_distribution': {
                    'positive_ratio': sentiment_counts['positive'] / total_news,
                    'negative_ratio': sentiment_counts['negative'] / total_news,
                    'neutral_ratio': sentiment_counts['neutral'] / total_news
                },
                'news_count': total_news,
                'recent_trend': self._analyze_sentiment_trend(news_data)
            }
            
            return sentiment_analysis
            
        except Exception as e:
            self.logger.error(f"情緒分析失敗: {str(e)}")
            return {'overall_sentiment': 'neutral', 'sentiment_score': 0.0}
    
    def _analyze_keyword_sentiment(self, text: str) -> float:
        """基於關鍵詞的情緒分析"""
        
        text_lower = text.lower()
        positive_count = 0
        negative_count = 0
        
        # 計算正面關鍵詞
        for keyword in self.sentiment_keywords['positive']:
            positive_count += text_lower.count(keyword.lower())
        
        # 計算負面關鍵詞
        for keyword in self.sentiment_keywords['negative']:
            negative_count += text_lower.count(keyword.lower())
        
        # 計算情緒分數
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0
        
        sentiment_score = (positive_count - negative_count) / total_keywords
        return max(-1.0, min(1.0, sentiment_score))
    
    def _classify_sentiment(self, score: float) -> str:
        """分類情緒"""
        if score > 0.3:
            return 'positive'
        elif score < -0.3:
            return 'negative'
        else:
            return 'neutral'
    
    def _analyze_sentiment_trend(self, news_data: List[Dict[str, Any]]) -> str:
        """分析情緒趋势"""
        
        if len(news_data) < 3:
            return 'insufficient_data'
        
        # 按時間排序 (最新在前)
        sorted_news = sorted(news_data, key=lambda x: x.get('published_date', ''), reverse=True)
        
        # 計算最近3天的平均情緒
        recent_sentiment = sum(news.get('sentiment_score', 0) for news in sorted_news[:3]) / 3
        
        # 計算較早期的平均情緒
        older_sentiment = sum(news.get('sentiment_score', 0) for news in sorted_news[3:]) / max(len(sorted_news[3:]), 1)
        
        if recent_sentiment > older_sentiment + 0.1:
            return 'improving'
        elif recent_sentiment < older_sentiment - 0.1:
            return 'deteriorating'
        else:
            return 'stable'
    
    async def _identify_key_events(self, news_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """識別關鍵事件"""
        
        if not news_data:
            return []
        
        try:
            key_events = []
            
            for news in news_data:
                title = news.get('title', '')
                content = news.get('content', '')
                importance = news.get('importance', 'low')
                
                # 識別事件類型
                event_type = self._classify_event_type(title + ' ' + content)
                
                # 只保留重要事件
                if importance in ['high', 'medium'] or abs(news.get('sentiment_score', 0)) > 0.5:
                    event = {
                        'title': title,
                        'event_type': event_type,
                        'importance': importance,
                        'sentiment_score': news.get('sentiment_score', 0),
                        'published_date': news.get('published_date', ''),
                        'source': news.get('source', ''),
                        'impact_assessment': self._assess_event_impact(event_type, news.get('sentiment_score', 0))
                    }
                    key_events.append(event)
            
            # 按重要性和情緒強度排序
            key_events.sort(key=lambda x: (
                {'high': 3, 'medium': 2, 'low': 1}[x['importance']] + abs(x['sentiment_score'])
            ), reverse=True)
            
            return key_events[:10]  # 最多返回10個關鍵事件
            
        except Exception as e:
            self.logger.error(f"關鍵事件識別失敗: {str(e)}")
            return []
    
    def _classify_event_type(self, text: str) -> str:
        """分類事件類型"""
        
        text_lower = text.lower()
        
        # 財報相關
        if any(keyword in text_lower for keyword in ['財報', '營收', '獲利', '淨利', '毛利', 'eps']):
            return 'earnings'
        
        # 經營層異動
        if any(keyword in text_lower for keyword in ['董事長', '總經理', '執行長', '高層', '人事']):
            return 'management'
        
        # 產業政策
        if any(keyword in text_lower for keyword in ['政策', '法規', '政府', '央行', '補助']):
            return 'policy'
        
        # 合作併購
        if any(keyword in text_lower for keyword in ['合作', '併購', '收購', '策略聯盟', '合資']):
            return 'partnership'
        
        # 產品技術
        if any(keyword in text_lower for keyword in ['新產品', '技術', '研發', '專利', '創新']):
            return 'product'
        
        # 法人動向
        if any(keyword in text_lower for keyword in ['外資', '投信', '自營商', '買超', '賣超']):
            return 'institutional'
        
        return 'general'
    
    def _assess_event_impact(self, event_type: str, sentiment_score: float) -> Dict[str, str]:
        """評估事件影響"""
        
        # 影響程度乘數
        impact_multipliers = {
            'earnings': 1.0,
            'management': 0.7,
            'policy': 0.8,
            'partnership': 0.6,
            'product': 0.5,
            'institutional': 0.9,
            'general': 0.3
        }
        
        multiplier = impact_multipliers.get(event_type, 0.5)
        impact_strength = abs(sentiment_score) * multiplier
        
        # 影響時間框架
        time_frames = {
            'earnings': 'medium',
            'management': 'long',
            'policy': 'long',
            'partnership': 'medium',
            'product': 'long',
            'institutional': 'short',
            'general': 'short'
        }
        
        return {
            'strength': 'high' if impact_strength > 0.6 else 'medium' if impact_strength > 0.3 else 'low',
            'timeframe': time_frames.get(event_type, 'short'),
            'direction': 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral'
        }
    
    async def _assess_news_impact(self, news_data: List[Dict[str, Any]], key_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """評估新聞影響"""
        
        if not news_data:
            return {'overall_impact': 'low', 'impact_score': 0.0}
        
        try:
            # 計算整體影響分數
            impact_scores = []
            
            for event in key_events:
                importance_weight = {'high': 1.0, 'medium': 0.6, 'low': 0.3}[event['importance']]
                sentiment_impact = abs(event['sentiment_score'])
                impact_scores.append(importance_weight * sentiment_impact)
            
            overall_impact_score = sum(impact_scores) / len(impact_scores) if impact_scores else 0.0
            
            # 分析影響分布
            short_term_events = [e for e in key_events if e['impact_assessment']['timeframe'] == 'short']
            medium_term_events = [e for e in key_events if e['impact_assessment']['timeframe'] == 'medium']
            long_term_events = [e for e in key_events if e['impact_assessment']['timeframe'] == 'long']
            
            impact_assessment = {
                'overall_impact': 'high' if overall_impact_score > 0.6 else 'medium' if overall_impact_score > 0.3 else 'low',
                'impact_score': round(overall_impact_score, 3),
                'timeframe_distribution': {
                    'short_term': len(short_term_events),
                    'medium_term': len(medium_term_events),
                    'long_term': len(long_term_events)
                },
                'dominant_themes': self._identify_dominant_themes(key_events),
                'market_attention': len(news_data)  # 新聞數量代表市場關注度
            }
            
            return impact_assessment
            
        except Exception as e:
            self.logger.error(f"新聞影響評估失敗: {str(e)}")
            return {'overall_impact': 'low', 'impact_score': 0.0}
    
    def _identify_dominant_themes(self, key_events: List[Dict[str, Any]]) -> List[str]:
        """識別主導主題"""
        
        event_types = [event['event_type'] for event in key_events]
        type_counts = Counter(event_types)
        
        # 返回最常見的3個主題
        dominant_themes = [theme for theme, count in type_counts.most_common(3)]
        return dominant_themes
    
    async def _analyze_taiwan_market_news(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析Taiwan市場特色新聞"""
        
        if not news_data:
            return {}
        
        try:
            taiwan_insights = {
                'institutional_flow': {'foreign': 'neutral', 'investment_trust': 'neutral', 'proprietary': 'neutral'},
                'policy_impact': 'neutral',
                'cross_strait_impact': 'neutral',
                'industry_trends': []
            }
            
            for news in news_data:
                content = (news.get('title', '') + ' ' + news.get('content', '')).lower()
                
                # 法人動向分析
                if '外資' in content:
                    if any(word in content for word in ['買超', '看好', '上調']):
                        taiwan_insights['institutional_flow']['foreign'] = 'positive'
                    elif any(word in content for word in ['賣超', '下調', '減持']):
                        taiwan_insights['institutional_flow']['foreign'] = 'negative'
                
                # 政策影響分析
                if any(keyword in content for keyword in self.taiwan_news_categories['政策影響']):
                    sentiment = news.get('sentiment_score', 0)
                    if sentiment > 0.2:
                        taiwan_insights['policy_impact'] = 'positive'
                    elif sentiment < -0.2:
                        taiwan_insights['policy_impact'] = 'negative'
                
                # 兩岸關係影響
                if any(keyword in content for keyword in self.taiwan_news_categories['兩岸關係']):
                    sentiment = news.get('sentiment_score', 0)
                    if sentiment > 0.1:
                        taiwan_insights['cross_strait_impact'] = 'positive'
                    elif sentiment < -0.1:
                        taiwan_insights['cross_strait_impact'] = 'negative'
                
                # 產業趨勢識別
                for industry, keywords in self.taiwan_news_categories.items():
                    if any(keyword.lower() in content for keyword in keywords):
                        taiwan_insights['industry_trends'].append({
                            'industry': industry,
                            'sentiment': self._classify_sentiment(news.get('sentiment_score', 0))
                        })
            
            return taiwan_insights
            
        except Exception as e:
            self.logger.error(f"Taiwan市場新聞分析失敗: {str(e)}")
            return {}
    
    def _calculate_event_importance_score(
        self, 
        importance: str, 
        sentiment_score: float, 
        credibility_score: float, 
        event_type: str
    ) -> float:
        """計算事件重要性綜合分數"""
        
        # 基本重要性分數
        base_score = {'high': 0.8, 'medium': 0.5, 'low': 0.2}.get(importance, 0.2)
        
        # 情緒強度加權
        sentiment_weight = abs(sentiment_score) * 0.3
        
        # 來源可信度加權
        credibility_weight = credibility_score * 0.2
        
        # 事件類型加權
        event_type_weights = {
            'earnings': 0.9,        # 財報相關最重要
            'major_event': 0.8,     # 重大事件
            'institutional': 0.75,  # 法人動向
            'product': 0.7,         # 產品技術
            'policy': 0.65,         # 產業政策
            'financial_action': 0.6, # 財務動作
            'partnership': 0.55,    # 合作協議
            'management': 0.5,      # 經營層異動
            'market_rumor': 0.3,    # 市場傳言
            'general': 0.4          # 一般事件
        }
        event_weight = event_type_weights.get(event_type, 0.4) * 0.3
        
        # 綜合分數
        final_score = base_score + sentiment_weight + credibility_weight + event_weight
        return min(1.0, final_score)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取關鍵詞"""
        import re
        
        # 簡化的關鍵詞提取（實際專案中應使用更進階的NLP）
        keywords = []
        
        # 提取數字資訊
        numbers = re.findall(r'\d+(?:\.\d+)?%?', text)
        keywords.extend([f'數字:{num}' for num in numbers[:3]])  # 只取前3個
        
        # 提取公司名稱
        company_patterns = ['台積電', '聯發科', '鴻海', '國泰金', '台塑']
        for pattern in company_patterns:
            if pattern in text:
                keywords.append(f'公司:{pattern}')
        
        # 提取重要概念
        important_concepts = ['財報', 'EPS', '營收', '獲利', '合作', '突破', '新產品']
        for concept in important_concepts:
            if concept in text:
                keywords.append(f'概念:{concept}')
        
        return keywords[:8]  # 限制關鍵詞數量
    
    def _assess_market_timing(self, published_date: str) -> str:
        """評估市場時機"""
        try:
            from datetime import datetime
            pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            now = datetime.now()
            
            hours_diff = (now - pub_date).total_seconds() / 3600
            
            if hours_diff < 1:
                return 'immediate'    # 立即影響
            elif hours_diff < 24:
                return 'same_day'     # 當日影響
            elif hours_diff < 168:  # 7天
                return 'this_week'    # 本週影響
            else:
                return 'historical'   # 歷史事件
        except:
            return 'unknown'
    
    def _assess_news_verification(self, news: Dict[str, Any]) -> str:
        """評估新聞驗證狀態"""
        source = news.get('source', '')
        credibility = news.get('credibility_score', 0.6)
        
        # 權威來源
        if credibility >= 0.9:
            return 'verified'      # 已驗證
        elif credibility >= 0.75:
            return 'reliable'      # 可信
        elif credibility >= 0.6:
            return 'uncertain'     # 不確定
        else:
            return 'unverified'    # 未驗證
    
    def _prepare_news_context(
        self,
        state: AnalysisState,
        news_data: List[Dict[str, Any]],
        sentiment_analysis: Dict[str, Any],
        key_events: List[Dict[str, Any]],
        impact_assessment: Dict[str, Any],
        taiwan_insights: Dict[str, Any]
    ) -> Dict[str, Any]:
        """準備新聞分析上下文"""
        
        context = {
            'stock_id': state.stock_id,
            'analysis_date': state.analysis_date,
            'analyst_type': 'news_sentiment_analysis',
            'news_data_available': bool(news_data),
            'news_count': len(news_data),
            'sentiment_analysis': sentiment_analysis,
            'key_events': key_events,
            'impact_assessment': impact_assessment,
            'taiwan_market_insights': taiwan_insights
        }
        
        return context
    
    async def _call_llm_analysis(self, prompt: str, context: Dict[str, Any], model_config) -> Dict[str, Any]:
        """調用LLM進行新聞分析"""
        
        try:
            # 簡化的分析結果生成 (實際應整合真實LLM)
            await asyncio.sleep(0.6)  # 模擬LLM調用時間
            
            sentiment_analysis = context.get('sentiment_analysis', {})
            key_events = context.get('key_events', [])
            impact_assessment = context.get('impact_assessment', {})
            taiwan_insights = context.get('taiwan_market_insights', {})
            
            # 基於新聞情緒和事件影響生成建議
            overall_sentiment = sentiment_analysis.get('sentiment_score', 0)
            impact_score = impact_assessment.get('impact_score', 0)
            news_count = context.get('news_count', 0)
            
            # 綜合評分邏輯
            score = 0.5  # 基礎分數
            reasoning = []
            
            # 情緒分析評分
            if overall_sentiment > 0.3:
                score += 0.2
                reasoning.append(f"新聞整體情緒正面 (情緒分數: {overall_sentiment:.2f})")
            elif overall_sentiment < -0.3:
                score -= 0.2
                reasoning.append(f"新聞整體情緒負面 (情緒分數: {overall_sentiment:.2f})")
            else:
                reasoning.append(f"新聞整體情緒中性 (情緒分數: {overall_sentiment:.2f})")
            
            # 影響程度評分
            if impact_score > 0.6:
                score += 0.15
                reasoning.append(f"關鍵事件影響程度高 (影響分數: {impact_score:.2f})")
            elif impact_score > 0.3:
                score += 0.05
                reasoning.append(f"關鍵事件影響程度中等 (影響分數: {impact_score:.2f})")
            
            # 市場關注度評分
            if news_count >= 5:
                score += 0.1
                reasoning.append(f"市場關注度高 ({news_count}則相關新聞)")
            elif news_count >= 3:
                score += 0.05
                reasoning.append(f"市場關注度中等 ({news_count}則相關新聞)")
            
            # Taiwan特色因素
            institutional_flow = taiwan_insights.get('institutional_flow', {})
            if institutional_flow.get('foreign') == 'positive':
                score += 0.1
                reasoning.append("外資動向正面，有利股價表現")
            elif institutional_flow.get('foreign') == 'negative':
                score -= 0.1
                reasoning.append("外資動向負面，可能壓抑股價")
            
            # 關鍵事件影響
            high_impact_events = [e for e in key_events if e['impact_assessment']['strength'] == 'high']
            if high_impact_events:
                reasoning.append(f"發現{len(high_impact_events)}個高影響事件")
                for event in high_impact_events[:2]:  # 只列出前2個
                    reasoning.append(f"- {event['title']}")
            
            # 決定建議
            if score >= 0.65:
                recommendation = 'BUY'
            elif score >= 0.4:
                recommendation = 'HOLD'
            else:
                recommendation = 'SELL'
            
            return {
                'recommendation': recommendation,
                'confidence': min(max(score, 0.3), 0.9),  # 限制信心度範圍
                'reasoning': reasoning,
                'risk_factors': [
                    '新聞情緒變化風險',
                    '事件影響不如預期風險',
                    '市場情緒轉變風險',
                    '資訊解讀偏差風險'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"LLM新聞分析失敗: {str(e)}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.4,
                'reasoning': [f'新聞分析過程中發生錯誤: {str(e)}'],
                'error': str(e)
            }


if __name__ == "__main__":
    # 測試腳本
    import asyncio
    from ..base_analyst import create_analysis_state
    
    async def test_news_analyst():
        print("測試新聞分析師")
        
        config = {'debug': True}
        analyst = NewsAnalyst(config)
        
        print(f"分析師信息: {analyst.get_analyst_info()}")
        
        # 創建測試狀態
        state = create_analysis_state(
            stock_id='2330',  # 台積電
            user_context={'user_id': 'test_user', 'membership_tier': 'GOLD'}
        )
        
        # 執行分析
        result = await analyst.analyze(state)
        
        print(f"分析結果: {result.recommendation}")
        print(f"信心度: {result.confidence}")
        print(f"分析理由: {result.reasoning}")
        print(f"市場條件: {result.market_conditions}")
        print(f"Taiwan洞察: {result.taiwan_insights}")
        
        print("✅ 新聞分析師測試完成")
    
    asyncio.run(test_news_analyst())