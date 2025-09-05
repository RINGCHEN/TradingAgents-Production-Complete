"""
Multi-Language Intelligence System
Supports Chinese (Traditional/Simplified), English, Japanese, Korean
Task 4.2.2: 多語言智能系統

Features:
- Real-time translation of financial content
- Language-specific sentiment analysis
- Cultural adaptation of investment recommendations
- Localized financial terminology
- Multi-language report generation
- Cross-language market intelligence
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import json
from abc import ABC, abstractmethod
import logging

class Language(Enum):
    CHINESE_TRADITIONAL = "zh-TW"
    CHINESE_SIMPLIFIED = "zh-CN"
    ENGLISH = "en"
    JAPANESE = "ja"
    KOREAN = "ko"

class ContentType(Enum):
    NEWS = "news"
    REPORT = "report"
    ANALYSIS = "analysis"
    ALERT = "alert"
    RECOMMENDATION = "recommendation"

@dataclass
class TranslationRequest:
    """Translation request structure"""
    text: str
    source_language: Language
    target_language: Language
    content_type: ContentType
    preserve_financial_terms: bool = True

@dataclass
class TranslationResult:
    """Translation result with metadata"""
    original_text: str
    translated_text: str
    source_language: Language
    target_language: Language
    confidence_score: float
    financial_terms_preserved: List[str]
    cultural_adaptations: List[str]
    timestamp: datetime

@dataclass
class SentimentAnalysis:
    """Language-specific sentiment analysis result"""
    text: str
    language: Language
    sentiment_score: float  # -1 to 1
    sentiment_label: str  # positive, negative, neutral
    confidence: float
    key_phrases: List[str]
    financial_indicators: List[str]

class FinancialTerminologyManager:
    """Manages financial terminology across languages"""
    
    def __init__(self):
        self.terminology_db = {
            # Stock market terms
            "stock": {
                Language.CHINESE_TRADITIONAL: "股票",
                Language.CHINESE_SIMPLIFIED: "股票",
                Language.ENGLISH: "stock",
                Language.JAPANESE: "株式",
                Language.KOREAN: "주식"
            },
            "market_cap": {
                Language.CHINESE_TRADITIONAL: "市值",
                Language.CHINESE_SIMPLIFIED: "市值",
                Language.ENGLISH: "market capitalization",
                Language.JAPANESE: "時価総額",
                Language.KOREAN: "시가총액"
            },
            "dividend": {
                Language.CHINESE_TRADITIONAL: "股息",
                Language.CHINESE_SIMPLIFIED: "股息",
                Language.ENGLISH: "dividend",
                Language.JAPANESE: "配当金",
                Language.KOREAN: "배당금"
            },
            "p_e_ratio": {
                Language.CHINESE_TRADITIONAL: "本益比",
                Language.CHINESE_SIMPLIFIED: "市盈率",
                Language.ENGLISH: "P/E ratio",
                Language.JAPANESE: "株価収益率",
                Language.KOREAN: "주가수익비율"
            },
            "bull_market": {
                Language.CHINESE_TRADITIONAL: "牛市",
                Language.CHINESE_SIMPLIFIED: "牛市",
                Language.ENGLISH: "bull market",
                Language.JAPANESE: "強気市場",
                Language.KOREAN: "강세장"
            },
            "bear_market": {
                Language.CHINESE_TRADITIONAL: "熊市",
                Language.CHINESE_SIMPLIFIED: "熊市",
                Language.ENGLISH: "bear market",
                Language.JAPANESE: "弱気市場",
                Language.KOREAN: "약세장"
            },
            "volatility": {
                Language.CHINESE_TRADITIONAL: "波動率",
                Language.CHINESE_SIMPLIFIED: "波动率",
                Language.ENGLISH: "volatility",
                Language.JAPANESE: "ボラティリティ",
                Language.KOREAN: "변동성"
            },
            "risk_management": {
                Language.CHINESE_TRADITIONAL: "風險管理",
                Language.CHINESE_SIMPLIFIED: "风险管理",
                Language.ENGLISH: "risk management",
                Language.JAPANESE: "リスク管理",
                Language.KOREAN: "위험관리"
            }
        }
        
        self.currency_symbols = {
            "USD": {"symbol": "$", "name": {
                Language.CHINESE_TRADITIONAL: "美元",
                Language.CHINESE_SIMPLIFIED: "美元",
                Language.ENGLISH: "US Dollar",
                Language.JAPANESE: "米ドル",
                Language.KOREAN: "미국 달러"
            }},
            "TWD": {"symbol": "NT$", "name": {
                Language.CHINESE_TRADITIONAL: "新台幣",
                Language.CHINESE_SIMPLIFIED: "新台币",
                Language.ENGLISH: "Taiwan Dollar",
                Language.JAPANESE: "台湾ドル",
                Language.KOREAN: "대만 달러"
            }},
            "JPY": {"symbol": "¥", "name": {
                Language.CHINESE_TRADITIONAL: "日圓",
                Language.CHINESE_SIMPLIFIED: "日元",
                Language.ENGLISH: "Japanese Yen",
                Language.JAPANESE: "円",
                Language.KOREAN: "일본 엔"
            }}
        }
    
    def get_term(self, english_term: str, target_language: Language) -> str:
        """Get translated financial term"""
        term_key = english_term.lower().replace(" ", "_")
        if term_key in self.terminology_db:
            return self.terminology_db[term_key].get(target_language, english_term)
        return english_term
    
    def get_currency_name(self, currency_code: str, language: Language) -> str:
        """Get localized currency name"""
        if currency_code in self.currency_symbols:
            return self.currency_symbols[currency_code]["name"].get(language, currency_code)
        return currency_code

class TranslationEngine(ABC):
    """Abstract translation engine"""
    
    @abstractmethod
    async def translate(self, request: TranslationRequest) -> TranslationResult:
        pass

class AITranslationEngine(TranslationEngine):
    """AI-powered translation with financial specialization"""
    
    def __init__(self):
        self.terminology_manager = FinancialTerminologyManager()
        
    async def translate(self, request: TranslationRequest) -> TranslationResult:
        """Perform translation with financial context awareness"""
        
        # Extract financial terms before translation
        financial_terms = self._extract_financial_terms(request.text)
        
        # Perform translation (mock implementation)
        translated_text = await self._translate_text(
            request.text, 
            request.source_language, 
            request.target_language
        )
        
        # Apply cultural adaptations
        cultural_adaptations = []
        if request.content_type == ContentType.RECOMMENDATION:
            translated_text, adaptations = self._apply_cultural_adaptations(
                translated_text, 
                request.target_language
            )
            cultural_adaptations.extend(adaptations)
        
        # Preserve financial terminology
        if request.preserve_financial_terms:
            translated_text = self._preserve_financial_terms(
                translated_text, 
                financial_terms, 
                request.target_language
            )
        
        return TranslationResult(
            original_text=request.text,
            translated_text=translated_text,
            source_language=request.source_language,
            target_language=request.target_language,
            confidence_score=0.95,  # Mock confidence
            financial_terms_preserved=financial_terms,
            cultural_adaptations=cultural_adaptations,
            timestamp=datetime.now(timezone.utc)
        )
    
    def _extract_financial_terms(self, text: str) -> List[str]:
        """Extract financial terms from text"""
        financial_patterns = [
            r'\b(?:stock|share|equity)\b',
            r'\b(?:dividend|yield)\b',
            r'\b(?:market cap|capitalization)\b',
            r'\b(?:P/E|PE) ratio\b',
            r'\b(?:bull|bear) market\b',
            r'\b(?:volatility|risk)\b',
            r'\$[\d,.]+'
        ]
        
        terms = []
        for pattern in financial_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            terms.extend(matches)
        
        return terms
    
    async def _translate_text(self, text: str, source: Language, target: Language) -> str:
        """Core translation logic (mock implementation)"""
        
        # Translation mappings for demonstration
        translations = {
            (Language.ENGLISH, Language.CHINESE_TRADITIONAL): {
                "Apple Inc. shows strong performance": "蘋果公司表現強勁",
                "The stock market is bullish": "股市看漲",
                "Risk management is important": "風險管理很重要",
                "Dividend yield increased": "股息收益率上升"
            },
            (Language.CHINESE_TRADITIONAL, Language.ENGLISH): {
                "台積電股價上漲": "TSMC stock price rises",
                "市場風險增加": "Market risk increases",
                "投資建議謹慎": "Investment advice: be cautious"
            },
            (Language.ENGLISH, Language.JAPANESE): {
                "Strong earnings report": "好調な決算報告",
                "Market volatility": "市場のボラティリティ",
                "Investment recommendation": "投資推奨"
            }
        }
        
        translation_key = (source, target)
        if translation_key in translations and text in translations[translation_key]:
            return translations[translation_key][text]
        
        # Fallback: return original text with language note
        return f"[{target.value}] {text}"
    
    def _apply_cultural_adaptations(self, text: str, target_language: Language) -> Tuple[str, List[str]]:
        """Apply cultural adaptations for investment content"""
        adaptations = []
        adapted_text = text
        
        # Cultural adaptation rules
        if target_language == Language.JAPANESE:
            # Japanese investors prefer conservative language
            if "aggressive" in text.lower():
                adapted_text = adapted_text.replace("aggressive", "proactive")
                adaptations.append("Softened aggressive language for Japanese cultural preferences")
        
        elif target_language in [Language.CHINESE_TRADITIONAL, Language.CHINESE_SIMPLIFIED]:
            # Chinese investors value long-term stability
            if "short-term" in text.lower():
                adapted_text = adapted_text.replace("short-term", "strategic")
                adaptations.append("Adjusted timeframe language for Chinese market preferences")
        
        elif target_language == Language.KOREAN:
            # Korean investors are tech-focused
            if "technology sector" in text.lower():
                adapted_text = adapted_text.replace("sector", "innovation sector")
                adaptations.append("Enhanced technology focus for Korean market")
        
        return adapted_text, adaptations
    
    def _preserve_financial_terms(self, text: str, terms: List[str], target_language: Language) -> str:
        """Ensure financial terms are properly localized"""
        preserved_text = text
        
        for term in terms:
            localized_term = self.terminology_manager.get_term(term, target_language)
            if localized_term != term:
                preserved_text = preserved_text.replace(term, localized_term)
        
        return preserved_text

class MultiLanguageSentimentAnalyzer:
    """Language-specific sentiment analysis for financial content"""
    
    def __init__(self):
        self.sentiment_lexicons = {
            Language.CHINESE_TRADITIONAL: {
                "positive": ["上漲", "獲利", "成長", "強勁", "看漲", "突破"],
                "negative": ["下跌", "虧損", "衰退", "疲軟", "看跌", "暴跌"]
            },
            Language.CHINESE_SIMPLIFIED: {
                "positive": ["上涨", "获利", "成长", "强劲", "看涨", "突破"],
                "negative": ["下跌", "亏损", "衰退", "疲软", "看跌", "暴跌"]
            },
            Language.ENGLISH: {
                "positive": ["bullish", "gains", "growth", "strong", "surge", "rally"],
                "negative": ["bearish", "losses", "decline", "weak", "plunge", "crash"]
            },
            Language.JAPANESE: {
                "positive": ["上昇", "利益", "成長", "強気", "急騰", "回復"],
                "negative": ["下落", "損失", "衰退", "弱気", "急落", "暴落"]
            },
            Language.KOREAN: {
                "positive": ["상승", "이익", "성장", "강세", "급등", "회복"],
                "negative": ["하락", "손실", "쇠퇴", "약세", "급락", "폭락"]
            }
        }
    
    async def analyze_sentiment(self, text: str, language: Language) -> SentimentAnalysis:
        """Analyze sentiment with language-specific context"""
        
        lexicon = self.sentiment_lexicons.get(language, {})
        positive_terms = lexicon.get("positive", [])
        negative_terms = lexicon.get("negative", [])
        
        # Count positive and negative terms
        positive_count = sum(1 for term in positive_terms if term in text)
        negative_count = sum(1 for term in negative_terms if term in text)
        
        # Calculate sentiment score
        total_count = positive_count + negative_count
        if total_count == 0:
            sentiment_score = 0.0
            sentiment_label = "neutral"
        else:
            sentiment_score = (positive_count - negative_count) / total_count
            if sentiment_score > 0.1:
                sentiment_label = "positive"
            elif sentiment_score < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
        
        # Extract key phrases
        key_phrases = []
        for term in positive_terms + negative_terms:
            if term in text:
                key_phrases.append(term)
        
        # Identify financial indicators
        financial_indicators = self._extract_financial_indicators(text, language)
        
        return SentimentAnalysis(
            text=text,
            language=language,
            sentiment_score=sentiment_score,
            sentiment_label=sentiment_label,
            confidence=0.85,
            key_phrases=key_phrases[:10],  # Top 10
            financial_indicators=financial_indicators
        )
    
    def _extract_financial_indicators(self, text: str, language: Language) -> List[str]:
        """Extract financial indicators mentioned in text"""
        indicators = []
        
        # Pattern matching based on language
        if language in [Language.CHINESE_TRADITIONAL, Language.CHINESE_SIMPLIFIED]:
            patterns = [r'股價', r'市值', r'本益比', r'殖利率', r'成交量']
        elif language == Language.ENGLISH:
            patterns = [r'stock price', r'market cap', r'P/E ratio', r'yield', r'volume']
        elif language == Language.JAPANESE:
            patterns = [r'株価', r'時価総額', r'株価収益率', r'配当', r'出来高']
        elif language == Language.KOREAN:
            patterns = [r'주가', r'시가총액', r'주가수익비율', r'배당', r'거래량']
        else:
            patterns = []
        
        for pattern in patterns:
            if re.search(pattern, text):
                indicators.append(pattern)
        
        return indicators

class MultiLanguageIntelligenceSystem:
    """Main multi-language intelligence system"""
    
    def __init__(self):
        self.translation_engine = AITranslationEngine()
        self.sentiment_analyzer = MultiLanguageSentimentAnalyzer()
        self.terminology_manager = FinancialTerminologyManager()
        self.logger = logging.getLogger(__name__)
        
        # Supported language pairs for translation
        self.supported_translations = [
            (Language.ENGLISH, Language.CHINESE_TRADITIONAL),
            (Language.ENGLISH, Language.CHINESE_SIMPLIFIED),
            (Language.ENGLISH, Language.JAPANESE),
            (Language.ENGLISH, Language.KOREAN),
            (Language.CHINESE_TRADITIONAL, Language.ENGLISH),
            (Language.CHINESE_SIMPLIFIED, Language.ENGLISH),
            (Language.JAPANESE, Language.ENGLISH),
            (Language.KOREAN, Language.ENGLISH),
            (Language.CHINESE_TRADITIONAL, Language.CHINESE_SIMPLIFIED),
            (Language.CHINESE_SIMPLIFIED, Language.CHINESE_TRADITIONAL)
        ]
    
    async def translate_content(
        self, 
        text: str, 
        source_language: Language, 
        target_language: Language,
        content_type: ContentType = ContentType.ANALYSIS
    ) -> TranslationResult:
        """Translate financial content with context awareness"""
        
        if (source_language, target_language) not in self.supported_translations:
            raise ValueError(f"Translation from {source_language.value} to {target_language.value} not supported")
        
        request = TranslationRequest(
            text=text,
            source_language=source_language,
            target_language=target_language,
            content_type=content_type,
            preserve_financial_terms=True
        )
        
        return await self.translation_engine.translate(request)
    
    async def analyze_multilingual_sentiment(
        self, 
        contents: Dict[Language, str]
    ) -> Dict[Language, SentimentAnalysis]:
        """Analyze sentiment across multiple languages"""
        
        results = {}
        tasks = []
        
        for language, text in contents.items():
            task = self.sentiment_analyzer.analyze_sentiment(text, language)
            tasks.append((language, task))
        
        for language, task in tasks:
            try:
                results[language] = await task
            except Exception as e:
                self.logger.error(f"Sentiment analysis failed for {language.value}: {str(e)}")
        
        return results
    
    def generate_multilingual_report(
        self, 
        base_content: str, 
        base_language: Language,
        target_languages: List[Language]
    ) -> Dict[Language, str]:
        """Generate investment report in multiple languages"""
        
        reports = {base_language: base_content}
        
        for target_lang in target_languages:
            if target_lang != base_language:
                # This would use the translation engine in practice
                reports[target_lang] = f"[{target_lang.value}] {base_content}"
        
        return reports
    
    def get_localized_financial_summary(
        self, 
        data: Dict[str, Any], 
        language: Language
    ) -> Dict[str, str]:
        """Get financial summary with localized terms"""
        
        summary = {}
        
        # Localize key financial metrics
        summary["market_status"] = self.terminology_manager.get_term("market_status", language)
        summary["price_change"] = self.terminology_manager.get_term("price_change", language)
        summary["volume"] = self.terminology_manager.get_term("volume", language)
        summary["market_cap"] = self.terminology_manager.get_term("market_cap", language)
        
        # Add localized values
        if "price_usd" in data:
            currency_name = self.terminology_manager.get_currency_name("USD", language)
            summary["price"] = f"{data['price_usd']} {currency_name}"
        
        return summary
    
    async def cross_language_market_intelligence(
        self, 
        news_sources: Dict[Language, List[str]]
    ) -> Dict[str, Any]:
        """Gather and analyze market intelligence across languages"""
        
        intelligence = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sources_analyzed": sum(len(sources) for sources in news_sources.values()),
            "language_coverage": [lang.value for lang in news_sources.keys()],
            "sentiment_by_language": {},
            "key_topics": {},
            "cross_language_consensus": {}
        }
        
        # Analyze sentiment for each language
        for language, sources in news_sources.items():
            combined_text = " ".join(sources)
            sentiment = await self.sentiment_analyzer.analyze_sentiment(combined_text, language)
            intelligence["sentiment_by_language"][language.value] = {
                "sentiment_score": sentiment.sentiment_score,
                "sentiment_label": sentiment.sentiment_label,
                "key_phrases": sentiment.key_phrases,
                "financial_indicators": sentiment.financial_indicators
            }
        
        # Calculate cross-language consensus
        sentiments = [data["sentiment_score"] for data in intelligence["sentiment_by_language"].values()]
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            sentiment_variance = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
            
            intelligence["cross_language_consensus"] = {
                "average_sentiment": avg_sentiment,
                "sentiment_variance": sentiment_variance,
                "consensus_level": "high" if sentiment_variance < 0.1 else "low"
            }
        
        return intelligence

# Example usage and testing
if __name__ == "__main__":
    async def test_multilanguage_system():
        system = MultiLanguageIntelligenceSystem()
        
        print("Testing Multi-Language Intelligence System...")
        
        # Test translation
        print("\n1. Testing Translation:")
        translation = await system.translate_content(
            text="Apple Inc. shows strong performance with bullish market sentiment",
            source_language=Language.ENGLISH,
            target_language=Language.CHINESE_TRADITIONAL,
            content_type=ContentType.ANALYSIS
        )
        print(f"Original: {translation.original_text}")
        print(f"Translated: {translation.translated_text}")
        print(f"Confidence: {translation.confidence_score}")
        
        # Test multilingual sentiment analysis
        print("\n2. Testing Multilingual Sentiment Analysis:")
        content = {
            Language.ENGLISH: "The stock market shows strong bullish trends with significant gains",
            Language.CHINESE_TRADITIONAL: "股市表現強勁，呈現明顯的看漲趋势",
            Language.JAPANESE: "株式市場は強気のトレンドを示している"
        }
        
        sentiments = await system.analyze_multilingual_sentiment(content)
        for language, sentiment in sentiments.items():
            print(f"{language.value}: {sentiment.sentiment_label} ({sentiment.sentiment_score:.2f})")
        
        # Test cross-language market intelligence
        print("\n3. Testing Cross-Language Market Intelligence:")
        news_sources = {
            Language.ENGLISH: ["Strong earnings report", "Market rally continues"],
            Language.CHINESE_TRADITIONAL: ["財報亮眼", "市場持續上漲"],
            Language.JAPANESE: ["好調な決算", "市場の上昇が続く"]
        }
        
        intelligence = await system.cross_language_market_intelligence(news_sources)
        print(f"Languages analyzed: {intelligence['language_coverage']}")
        print(f"Consensus level: {intelligence['cross_language_consensus']['consensus_level']}")
        
        return intelligence
    
    # Run test
    result = asyncio.run(test_multilanguage_system())
    print("\nMulti-Language Intelligence System test completed successfully!")