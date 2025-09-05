#!/usr/bin/env python3
"""
Text Processor - 文本處理器
天工 (TianGong) - 專業的中文金融文本分析處理系統

此模組提供：
1. 中文金融文本預處理
2. 情感分析和語義理解
3. 關鍵詞提取和主題分析
4. 實體識別和關聯分析
5. 文本品質評估和過濾
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging
import re
import json
import time
import numpy as np
from collections import defaultdict, Counter

# 中文處理相關
try:
    import jieba
    import jieba.analyse
    from jieba import posseg
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False

# TF-IDF和機器學習
try:
    from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class TextAnalysisType(Enum):
    """文本分析類型"""
    SENTIMENT_ANALYSIS = "sentiment_analysis"       # 情感分析
    KEYWORD_EXTRACTION = "keyword_extraction"       # 關鍵詞提取
    TOPIC_MODELING = "topic_modeling"               # 主題建模
    ENTITY_RECOGNITION = "entity_recognition"       # 實體識別
    TEXT_CLASSIFICATION = "text_classification"     # 文本分類
    SEMANTIC_SIMILARITY = "semantic_similarity"     # 語義相似度
    TEXT_SUMMARIZATION = "text_summarization"       # 文本摘要

@dataclass
class SentimentResult:
    """情感分析結果"""
    sentiment_score: float          # -1到1的情感分數
    sentiment_label: str           # positive/negative/neutral
    confidence: float              # 信心度
    emotional_keywords: List[str] = field(default_factory=list)
    analysis_method: str = ""
    
    def is_positive(self) -> bool:
        return self.sentiment_score > 0.1
    
    def is_negative(self) -> bool:
        return self.sentiment_score < -0.1
    
    def is_neutral(self) -> bool:
        return abs(self.sentiment_score) <= 0.1

@dataclass
class KeywordExtraction:
    """關鍵詞提取結果"""
    keywords: List[Tuple[str, float]]  # (詞, 權重)
    method: str
    total_keywords: int
    extraction_time: float
    
    def get_top_keywords(self, n: int = 10) -> List[str]:
        return [keyword for keyword, _ in self.keywords[:n]]
    
    def get_keyword_dict(self) -> Dict[str, float]:
        return dict(self.keywords)

@dataclass
class TopicAnalysis:
    """主題分析結果"""
    topics: List[Dict[str, Any]]       # 主題列表
    topic_distribution: List[float]    # 文檔在各主題上的分佈
    dominant_topic: int                # 主導主題索引
    coherence_score: float            # 主題一致性分數
    method: str = "LDA"

@dataclass
class EntityRecognition:
    """實體識別結果"""
    entities: Dict[str, List[str]]     # 實體類型 -> 實體列表
    entity_relations: List[Tuple[str, str, str]]  # (實體1, 關係, 實體2)
    confidence_scores: Dict[str, float]  # 實體 -> 信心度

class TextProcessor:
    """文本處理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 語言設定
        self.language = self.config.get('language', 'zh-TW')
        
        # 初始化中文處理工具
        self._init_chinese_tools()
        
        # 金融領域詞典
        self.financial_keywords = self._load_financial_keywords()
        self.sentiment_dict = self._load_sentiment_dict()
        
        # 處理緩存
        self.processing_cache: Dict[str, Any] = {}
        self.cache_ttl = self.config.get('cache_ttl', 3600)  # 1小時
        
        # 性能配置
        self.max_text_length = self.config.get('max_text_length', 10000)
        self.batch_size = self.config.get('batch_size', 32)
        
        self.logger.info("TextProcessor initialized")
    
    def _init_chinese_tools(self):
        """初始化中文處理工具"""
        if JIEBA_AVAILABLE:
            # 添加金融詞彙
            financial_words = [
                '股價', '股票', '投資', '獲利', '虧損', '漲停', '跌停',
                '法人', '外資', '投信', '自營商', '融資', '融券',
                '本益比', '股息', '配股', '除權', '除息', '減資',
                '台積電', '鴻海', '聯發科', '大立光'
            ]
            
            for word in financial_words:
                jieba.add_word(word, freq=1000)
            
            self.jieba_ready = True
        else:
            self.logger.warning("jieba not available, some features will be limited")
            self.jieba_ready = False
    
    def _load_financial_keywords(self) -> Dict[str, List[str]]:
        """載入金融關鍵詞典"""
        return {
            'positive': [
                '上漲', '漲幅', '獲利', '成長', '看好', '買進', '推薦',
                '利多', '突破', '創新高', '強勢', '樂觀', '回升'
            ],
            'negative': [
                '下跌', '跌幅', '虧損', '衰退', '看壞', '賣出', '降評',
                '利空', '破底', '創新低', '弱勢', '悲觀', '下滑'
            ],
            'neutral': [
                '持平', '整理', '觀望', '持有', '維持', '平盤', '區間'
            ],
            'financial_terms': [
                '營收', '毛利率', '淨利', '每股盈餘', 'EPS', 'ROE', 'ROA',
                '現金流', '負債比', '周轉率', '市占率'
            ]
        }
    
    def _load_sentiment_dict(self) -> Dict[str, float]:
        """載入情感詞典"""
        sentiment_dict = {}
        
        # 正面詞彙
        for word in self.financial_keywords['positive']:
            sentiment_dict[word] = 1.0
        
        # 負面詞彙
        for word in self.financial_keywords['negative']:
            sentiment_dict[word] = -1.0
        
        # 中性詞彙
        for word in self.financial_keywords['neutral']:
            sentiment_dict[word] = 0.0
        
        return sentiment_dict
    
    async def analyze_text(
        self,
        text: str,
        analysis_types: List[TextAnalysisType] = None,
        user_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        綜合文本分析
        
        Args:
            text: 待分析文本
            analysis_types: 分析類型列表
            user_context: 用戶上下文
            
        Returns:
            分析結果字典
        """
        if analysis_types is None:
            analysis_types = [
                TextAnalysisType.SENTIMENT_ANALYSIS,
                TextAnalysisType.KEYWORD_EXTRACTION
            ]
        
        # 文本預處理
        preprocessed_text = await self.preprocess_text(text)
        
        results = {
            'original_text': text,
            'preprocessed_text': preprocessed_text,
            'analysis_timestamp': time.time(),
            'text_stats': await self._get_text_statistics(text)
        }
        
        # 執行各種分析
        for analysis_type in analysis_types:
            try:
                if analysis_type == TextAnalysisType.SENTIMENT_ANALYSIS:
                    results['sentiment'] = await self.analyze_sentiment(preprocessed_text)
                elif analysis_type == TextAnalysisType.KEYWORD_EXTRACTION:
                    results['keywords'] = await self.extract_keywords(preprocessed_text)
                elif analysis_type == TextAnalysisType.TOPIC_MODELING:
                    results['topics'] = await self.analyze_topics([preprocessed_text])
                elif analysis_type == TextAnalysisType.ENTITY_RECOGNITION:
                    results['entities'] = await self.recognize_entities(preprocessed_text)
                    
            except Exception as e:
                self.logger.warning(f"分析 {analysis_type.value} 失敗: {e}")
                results[analysis_type.value] = None
        
        return results
    
    async def preprocess_text(self, text: str) -> str:
        """文本預處理"""
        if not text:
            return ""
        
        # 限制文本長度
        if len(text) > self.max_text_length:
            text = text[:self.max_text_length]
        
        # 清理文本
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符但保留中文標點
        text = re.sub(r'[^\u4e00-\u9fff\w\s.,!?;:()[]{}""''「」（）【】，。！？；：]', '', text)
        
        # 移除過短的詞
        if self.jieba_ready:
            words = jieba.lcut(text)
            words = [word for word in words if len(word.strip()) > 1]
            text = ' '.join(words)
        
        return text.strip()
    
    async def analyze_sentiment(self, text: str) -> SentimentResult:
        """情感分析"""
        if not text:
            return SentimentResult(
                sentiment_score=0.0,
                sentiment_label="neutral",
                confidence=0.0,
                analysis_method="empty_text"
            )
        
        # 檢查緩存
        cache_key = f"sentiment_{hash(text)}"
        if cache_key in self.processing_cache:
            cached_result = self.processing_cache[cache_key]
            if time.time() - cached_result['timestamp'] < self.cache_ttl:
                return cached_result['result']
        
        # 執行情感分析
        sentiment_score = 0.0
        emotional_keywords = []
        analysis_method = "dictionary_based"
        
        try:
            if self.jieba_ready:
                # 基於詞典的情感分析
                words = jieba.lcut(text)
                word_scores = []
                
                for word in words:
                    if word in self.sentiment_dict:
                        score = self.sentiment_dict[word]
                        word_scores.append(score)
                        if abs(score) > 0.5:
                            emotional_keywords.append(word)
                
                if word_scores:
                    sentiment_score = np.mean(word_scores)
                    
                    # 考慮強度詞的影響
                    intensifiers = ['很', '非常', '極其', '相當', '十分', '特別']
                    for intensifier in intensifiers:
                        if intensifier in text:
                            sentiment_score *= 1.2  # 增強情感強度
                
                # 考慮否定詞的影響
                negation_words = ['不', '沒', '未', '非', '無']
                for neg_word in negation_words:
                    if neg_word in text:
                        sentiment_score *= -0.8  # 反轉但減弱情感
            
            # 標準化分數到[-1, 1]
            sentiment_score = max(-1.0, min(1.0, sentiment_score))
            
            # 確定情感標籤
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            # 計算信心度
            confidence = min(abs(sentiment_score) + 0.3, 1.0)
            
            result = SentimentResult(
                sentiment_score=sentiment_score,
                sentiment_label=sentiment_label,
                confidence=confidence,
                emotional_keywords=emotional_keywords,
                analysis_method=analysis_method
            )
            
            # 緩存結果
            self.processing_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"情感分析失敗: {e}")
            return SentimentResult(
                sentiment_score=0.0,
                sentiment_label="neutral",
                confidence=0.0,
                analysis_method="error"
            )
    
    async def extract_keywords(
        self,
        text: str,
        max_keywords: int = 20,
        method: str = "tfidf"
    ) -> KeywordExtraction:
        """關鍵詞提取"""
        start_time = time.time()
        
        if not text:
            return KeywordExtraction(
                keywords=[],
                method=method,
                total_keywords=0,
                extraction_time=time.time() - start_time
            )
        
        keywords = []
        
        try:
            if method == "jieba_tfidf" and self.jieba_ready:
                # 使用jieba的TF-IDF提取
                keyword_list = jieba.analyse.extract_tags(
                    text,
                    topK=max_keywords,
                    withWeight=True,
                    allowPOS=('n', 'nr', 'ns', 'nt', 'nz', 'v', 'vn', 'a')
                )
                keywords = [(word, float(weight)) for word, weight in keyword_list]
                
            elif method == "textrank" and self.jieba_ready:
                # 使用TextRank算法
                keyword_list = jieba.analyse.textrank(
                    text,
                    topK=max_keywords,
                    withWeight=True
                )
                keywords = [(word, float(weight)) for word, weight in keyword_list]
                
            elif method == "frequency":
                # 基於詞頻的提取
                if self.jieba_ready:
                    words = jieba.lcut(text)
                else:
                    words = text.split()
                
                # 過濾停用詞和短詞
                filtered_words = [
                    word for word in words 
                    if len(word) > 1 and word not in self._get_stop_words()
                ]
                
                word_freq = Counter(filtered_words)
                total_words = len(filtered_words)
                
                keywords = [
                    (word, count / total_words) 
                    for word, count in word_freq.most_common(max_keywords)
                ]
            
            # 增強金融相關詞彙的權重
            enhanced_keywords = []
            for word, weight in keywords:
                if any(word in keyword_list for keyword_list in self.financial_keywords.values()):
                    enhanced_weight = min(weight * 1.5, 1.0)  # 增強但不超過1.0
                else:
                    enhanced_weight = weight
                enhanced_keywords.append((word, enhanced_weight))
            
            # 按權重排序
            enhanced_keywords.sort(key=lambda x: x[1], reverse=True)
            
            return KeywordExtraction(
                keywords=enhanced_keywords,
                method=method,
                total_keywords=len(enhanced_keywords),
                extraction_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"關鍵詞提取失敗: {e}")
            return KeywordExtraction(
                keywords=[],
                method=f"{method}_error",
                total_keywords=0,
                extraction_time=time.time() - start_time
            )
    
    async def analyze_topics(
        self,
        texts: List[str],
        num_topics: int = 5,
        method: str = "LDA"
    ) -> TopicAnalysis:
        """主題分析"""
        if not texts or not SKLEARN_AVAILABLE:
            return TopicAnalysis(
                topics=[],
                topic_distribution=[],
                dominant_topic=0,
                coherence_score=0.0,
                method=f"{method}_unavailable"
            )
        
        try:
            # 文本預處理
            processed_texts = []
            for text in texts:
                processed = await self.preprocess_text(text)
                if processed:
                    processed_texts.append(processed)
            
            if len(processed_texts) < 2:
                return TopicAnalysis(
                    topics=[],
                    topic_distribution=[],
                    dominant_topic=0,
                    coherence_score=0.0,
                    method=f"{method}_insufficient_data"
                )
            
            if method == "LDA":
                # 使用LDA主題建模
                vectorizer = CountVectorizer(
                    max_features=1000,
                    stop_words=self._get_stop_words(),
                    ngram_range=(1, 2)
                )
                
                doc_term_matrix = vectorizer.fit_transform(processed_texts)
                
                lda = LatentDirichletAllocation(
                    n_components=num_topics,
                    random_state=42,
                    max_iter=100
                )
                
                lda.fit(doc_term_matrix)
                
                # 提取主題
                feature_names = vectorizer.get_feature_names_out()
                topics = []
                
                for topic_idx, topic in enumerate(lda.components_):
                    top_words_idx = topic.argsort()[-10:][::-1]
                    top_words = [
                        (feature_names[i], topic[i]) 
                        for i in top_words_idx
                    ]
                    
                    topics.append({
                        'topic_id': topic_idx,
                        'top_words': top_words,
                        'weight': float(np.sum(topic))
                    })
                
                # 計算文檔主題分佈（使用第一個文檔）
                doc_topic_dist = lda.transform(doc_term_matrix[0:1])[0]
                dominant_topic = int(np.argmax(doc_topic_dist))
                
                # 簡單的主題一致性分數計算
                coherence_score = float(np.mean([
                    np.max(topic_dist) for topic_dist in lda.transform(doc_term_matrix)
                ]))
                
                return TopicAnalysis(
                    topics=topics,
                    topic_distribution=doc_topic_dist.tolist(),
                    dominant_topic=dominant_topic,
                    coherence_score=coherence_score,
                    method="LDA"
                )
            
        except Exception as e:
            self.logger.error(f"主題分析失敗: {e}")
        
        return TopicAnalysis(
            topics=[],
            topic_distribution=[],
            dominant_topic=0,
            coherence_score=0.0,
            method=f"{method}_error"
        )
    
    async def recognize_entities(self, text: str) -> EntityRecognition:
        """實體識別（簡化版）"""
        entities = {
            'companies': [],
            'financial_terms': [],
            'numbers': [],
            'dates': []
        }
        
        try:
            # 公司名稱識別（基於預定義列表）
            company_names = [
                '台積電', '鴻海', '聯發科', '大立光', '台塑', '中華電',
                '富邦金', '中信金', '國泰金', '玉山金', '兆豐金'
            ]
            
            for company in company_names:
                if company in text:
                    entities['companies'].append(company)
            
            # 金融術語識別
            for term in self.financial_keywords['financial_terms']:
                if term in text:
                    entities['financial_terms'].append(term)
            
            # 數字識別
            number_pattern = r'\d+(?:\.\d+)?(?:[萬億千百十])?'
            numbers = re.findall(number_pattern, text)
            entities['numbers'] = list(set(numbers))
            
            # 日期識別
            date_pattern = r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?'
            dates = re.findall(date_pattern, text)
            entities['dates'] = list(set(dates))
            
            # 簡單的信心度計算
            confidence_scores = {}
            for entity_type, entity_list in entities.items():
                if entity_list:
                    confidence_scores[entity_type] = 0.8  # 固定信心度
            
            return EntityRecognition(
                entities=entities,
                entity_relations=[],  # 簡化版本不實現關係抽取
                confidence_scores=confidence_scores
            )
            
        except Exception as e:
            self.logger.error(f"實體識別失敗: {e}")
            return EntityRecognition(
                entities=entities,
                entity_relations=[],
                confidence_scores={}
            )
    
    def _get_stop_words(self) -> List[str]:
        """獲取停用詞列表"""
        return [
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人',
            '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去',
            '你', '會', '著', '沒有', '看', '好', '自己', '這', '那', '它',
            '他', '她', '我們', '你們', '他們', '但是', '如果', '這樣',
            '那樣', '什麼', '怎麼', '為什麼', '因為', '所以', '雖然',
            '然而', '而且', '並且', '或者', '以及', '以前', '以後',
            '現在', '今天', '明天', '昨天'
        ]
    
    async def _get_text_statistics(self, text: str) -> Dict[str, Any]:
        """獲取文本統計信息"""
        stats = {
            'length': len(text),
            'char_count': len(text),
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0
        }
        
        try:
            # 詞數統計
            if self.jieba_ready:
                words = jieba.lcut(text)
                stats['word_count'] = len([w for w in words if len(w.strip()) > 0])
            else:
                stats['word_count'] = len(text.split())
            
            # 句子數統計
            sentence_endings = ['。', '！', '？', '.', '!', '?']
            stats['sentence_count'] = sum(text.count(ending) for ending in sentence_endings)
            
            # 段落數統計
            stats['paragraph_count'] = len([p for p in text.split('\n') if p.strip()])
            
        except Exception as e:
            self.logger.warning(f"文本統計失敗: {e}")
        
        return stats
    
    async def calculate_similarity(self, text1: str, text2: str) -> float:
        """計算文本相似度"""
        try:
            if not text1 or not text2:
                return 0.0
            
            if not SKLEARN_AVAILABLE:
                # 簡單的Jaccard相似度
                if self.jieba_ready:
                    words1 = set(jieba.lcut(text1))
                    words2 = set(jieba.lcut(text2))
                else:
                    words1 = set(text1.split())
                    words2 = set(text2.split())
                
                intersection = words1.intersection(words2)
                union = words1.union(words2)
                
                return len(intersection) / len(union) if union else 0.0
            
            # 使用TF-IDF向量計算餘弦相似度
            vectorizer = TfidfVectorizer(stop_words=self._get_stop_words())
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            return float(similarity_matrix[0][1])
            
        except Exception as e:
            self.logger.error(f"相似度計算失敗: {e}")
            return 0.0
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """獲取處理統計信息"""
        return {
            'cache_size': len(self.processing_cache),
            'jieba_available': self.jieba_ready,
            'sklearn_available': SKLEARN_AVAILABLE,
            'financial_keywords_count': sum(
                len(keyword_list) for keyword_list in self.financial_keywords.values()
            ),
            'sentiment_dict_size': len(self.sentiment_dict),
            'supported_analyses': [
                'sentiment_analysis',
                'keyword_extraction',
                'topic_modeling' if SKLEARN_AVAILABLE else None,
                'entity_recognition',
                'text_similarity'
            ]
        }
    
    def clear_cache(self):
        """清空處理緩存"""
        self.processing_cache.clear()
        self.logger.info("文本處理緩存已清空")