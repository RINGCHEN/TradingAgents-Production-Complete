"""
Third-party Data Source Integration System
Comprehensive integration with external data providers and alternative data sources
Task 4.4.1: 第三方數據源集成

Features:
- Multiple data provider integration (Bloomberg, Reuters, Quandl, Alpha Vantage, etc.)
- Alternative data sources (social media, satellite imagery, news sentiment, etc.)
- Real-time data streaming and batch processing
- Data quality validation and normalization
- API rate limiting and cost management
- Data lineage and audit trails
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import uuid
import hashlib
from abc import ABC, abstractmethod
import aiohttp
import pandas as pd
import numpy as np

class DataProviderType(Enum):
    TRADITIONAL_FINANCIAL = "traditional_financial"  # Bloomberg, Reuters
    MARKET_DATA = "market_data"  # Alpha Vantage, IEX Cloud
    ALTERNATIVE_DATA = "alternative_data"  # Social media, satellite, etc.
    NEWS_MEDIA = "news_media"  # News APIs, RSS feeds
    ECONOMIC_DATA = "economic_data"  # Government, central banks
    CRYPTOCURRENCY = "cryptocurrency"  # Crypto exchanges
    ESG_DATA = "esg_data"  # ESG ratings and metrics

class DataFormat(Enum):
    JSON = "json"
    CSV = "csv"
    XML = "xml" 
    PARQUET = "parquet"
    AVRO = "avro"
    FIX = "fix"  # Financial Information eXchange

class UpdateFrequency(Enum):
    REAL_TIME = "real_time"
    MINUTE = "minute"
    FIVE_MINUTE = "5_minute"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

@dataclass
class DataProviderConfig:
    """Configuration for third-party data provider"""
    provider_id: str
    provider_name: str
    provider_type: DataProviderType
    api_endpoint: str
    authentication_method: str  # "api_key", "oauth", "basic_auth"
    credentials: Dict[str, str]
    rate_limits: Dict[str, int]  # requests per time period
    supported_formats: List[DataFormat]
    cost_per_request: float
    data_categories: List[str]
    reliability_score: float  # 0-1 scale
    created_at: datetime
    status: str = "active"

@dataclass
class DataFeed:
    """Configuration for a specific data feed"""
    feed_id: str
    feed_name: str
    provider_id: str
    data_category: str
    symbols: List[str]
    update_frequency: UpdateFrequency
    data_format: DataFormat
    transformation_rules: Dict[str, Any]
    quality_checks: List[str]
    retention_days: int
    created_at: datetime
    last_updated: Optional[datetime] = None
    status: str = "active"

@dataclass
class DataQualityMetrics:
    """Data quality assessment metrics"""
    feed_id: str
    assessment_date: datetime
    completeness_score: float  # 0-1
    accuracy_score: float  # 0-1
    timeliness_score: float  # 0-1
    consistency_score: float  # 0-1
    overall_quality_score: float  # 0-1
    issues_detected: List[str]
    recommendations: List[str]

class DataProviderAdapter(ABC):
    """Abstract base class for data provider adapters"""
    
    def __init__(self, config: DataProviderConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{config.provider_name}")
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the data provider"""
        pass
    
    @abstractmethod
    async def fetch_data(
        self, 
        endpoint: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch data from provider API"""
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize data to standard format"""
        pass

class BloombergAdapter(DataProviderAdapter):
    """Bloomberg Terminal/API adapter"""
    
    async def authenticate(self) -> bool:
        """Authenticate with Bloomberg API"""
        # Mock authentication - in practice would use Bloomberg API SDK
        return True
    
    async def fetch_data(
        self, 
        endpoint: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch data from Bloomberg API"""
        
        # Mock Bloomberg data response
        if "equity" in endpoint:
            return {
                "securities": [
                    {
                        "ticker": parameters.get("symbols", ["AAPL"])[0],
                        "last_price": 150.25,
                        "change": 2.50,
                        "volume": 1000000,
                        "market_cap": 2500000000000,
                        "pe_ratio": 28.5,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                ]
            }
        return {}
    
    def normalize_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize Bloomberg data"""
        normalized = []
        
        for security in raw_data.get("securities", []):
            normalized.append({
                "symbol": security["ticker"],
                "price": security["last_price"],
                "change": security["change"],
                "volume": security["volume"],
                "market_cap": security["market_cap"],
                "pe_ratio": security["pe_ratio"],
                "timestamp": security["timestamp"],
                "source": "bloomberg",
                "data_quality": "high"
            })
        
        return normalized

class AlphaVantageAdapter(DataProviderAdapter):
    """Alpha Vantage API adapter"""
    
    async def authenticate(self) -> bool:
        """Alpha Vantage uses API key authentication"""
        return "apikey" in self.config.credentials
    
    async def fetch_data(
        self, 
        endpoint: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch data from Alpha Vantage API"""
        
        # Mock Alpha Vantage response
        symbol = parameters.get("symbol", "AAPL")
        return {
            "Meta Data": {
                "1. Information": "Daily Prices (open, high, low, close) and Volumes",
                "2. Symbol": symbol,
                "3. Last Refreshed": datetime.now().strftime("%Y-%m-%d"),
                "4. Output Size": "Full size"
            },
            "Time Series (Daily)": {
                datetime.now().strftime("%Y-%m-%d"): {
                    "1. open": "148.50",
                    "2. high": "152.00", 
                    "3. low": "147.25",
                    "4. close": "150.25",
                    "5. volume": "1000000"
                }
            }
        }
    
    def normalize_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize Alpha Vantage data"""
        normalized = []
        
        meta_data = raw_data.get("Meta Data", {})
        time_series = raw_data.get("Time Series (Daily)", {})
        
        for date, data in time_series.items():
            normalized.append({
                "symbol": meta_data.get("2. Symbol", ""),
                "date": date,
                "open": float(data["1. open"]),
                "high": float(data["2. high"]),
                "low": float(data["3. low"]),
                "close": float(data["4. close"]),
                "volume": int(data["5. volume"]),
                "source": "alpha_vantage",
                "data_quality": "medium"
            })
        
        return normalized

class TwitterSentimentAdapter(DataProviderAdapter):
    """Twitter/X sentiment data adapter (Alternative Data)"""
    
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API v2"""
        return "bearer_token" in self.config.credentials
    
    async def fetch_data(
        self, 
        endpoint: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch Twitter sentiment data"""
        
        # Mock Twitter sentiment response
        query = parameters.get("query", "$AAPL")
        return {
            "data": [
                {
                    "id": "1234567890",
                    "text": f"Great earnings from {query}! Strong performance ahead.",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "public_metrics": {
                        "retweet_count": 45,
                        "like_count": 123,
                        "reply_count": 12
                    }
                },
                {
                    "id": "1234567891",
                    "text": f"Concerned about {query} valuation. Might be overpriced.",
                    "created_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                    "public_metrics": {
                        "retweet_count": 23,
                        "like_count": 67,
                        "reply_count": 34
                    }
                }
            ],
            "meta": {
                "result_count": 2
            }
        }
    
    def normalize_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize Twitter sentiment data"""
        normalized = []
        
        for tweet in raw_data.get("data", []):
            # Simple sentiment analysis (mock)
            text = tweet["text"].lower()
            positive_words = ["great", "strong", "bullish", "buy", "growth"]
            negative_words = ["concerned", "worried", "bearish", "sell", "decline"]
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                sentiment = "positive"
                sentiment_score = 0.7
            elif negative_count > positive_count:
                sentiment = "negative"
                sentiment_score = -0.7
            else:
                sentiment = "neutral"
                sentiment_score = 0.0
            
            normalized.append({
                "tweet_id": tweet["id"],
                "text": tweet["text"],
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "engagement_score": (
                    tweet["public_metrics"]["retweet_count"] * 3 +
                    tweet["public_metrics"]["like_count"] +
                    tweet["public_metrics"]["reply_count"] * 2
                ),
                "created_at": tweet["created_at"],
                "source": "twitter",
                "data_quality": "medium"
            })
        
        return normalized

class NewsAPIAdapter(DataProviderAdapter):
    """News API adapter for financial news"""
    
    async def authenticate(self) -> bool:
        """News API authentication"""
        return "api_key" in self.config.credentials
    
    async def fetch_data(
        self, 
        endpoint: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fetch news articles"""
        
        # Mock news API response
        query = parameters.get("q", "Apple")
        return {
            "status": "ok",
            "totalResults": 100,
            "articles": [
                {
                    "source": {"id": "reuters", "name": "Reuters"},
                    "author": "John Doe",
                    "title": f"{query} Reports Strong Q3 Earnings",
                    "description": f"{query} exceeded expectations with strong revenue growth.",
                    "url": "https://reuters.com/article/apple-earnings",
                    "urlToImage": "https://reuters.com/image.jpg",
                    "publishedAt": datetime.now(timezone.utc).isoformat(),
                    "content": f"{query} reported quarterly earnings that beat analyst expectations..."
                },
                {
                    "source": {"id": "cnbc", "name": "CNBC"},
                    "author": "Jane Smith",
                    "title": f"{query} Stock Analysis: Buy or Sell?",
                    "description": f"Technical analysis of {query} stock performance.",
                    "url": "https://cnbc.com/article/apple-analysis",
                    "urlToImage": "https://cnbc.com/image.jpg",
                    "publishedAt": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                    "content": f"Our analysis of {query} suggests mixed signals in the market..."
                }
            ]
        }
    
    def normalize_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Normalize news data"""
        normalized = []
        
        for article in raw_data.get("articles", []):
            # Simple sentiment analysis
            title_text = article.get("title", "").lower()
            content_text = article.get("description", "").lower()
            combined_text = f"{title_text} {content_text}"
            
            positive_words = ["strong", "beat", "exceeded", "growth", "buy", "bullish"]
            negative_words = ["weak", "missed", "declined", "loss", "sell", "bearish"]
            
            positive_count = sum(1 for word in positive_words if word in combined_text)
            negative_count = sum(1 for word in negative_words if word in combined_text)
            
            if positive_count > negative_count:
                sentiment = "positive"
                sentiment_score = min(0.8, positive_count / 10)
            elif negative_count > positive_count:
                sentiment = "negative" 
                sentiment_score = -min(0.8, negative_count / 10)
            else:
                sentiment = "neutral"
                sentiment_score = 0.0
            
            normalized.append({
                "article_id": hashlib.md5(article["url"].encode()).hexdigest(),
                "title": article["title"],
                "description": article["description"],
                "source": article["source"]["name"],
                "author": article.get("author", "Unknown"),
                "published_at": article["publishedAt"],
                "url": article["url"],
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "source_provider": "newsapi",
                "data_quality": "high"
            })
        
        return normalized

class DataQualityValidator:
    """Validates and scores data quality"""
    
    def __init__(self):
        self.quality_rules = {
            "completeness": [
                "required_fields_present",
                "no_null_critical_fields",
                "data_volume_threshold"
            ],
            "accuracy": [
                "data_type_validation",
                "range_validation", 
                "format_validation"
            ],
            "timeliness": [
                "data_freshness",
                "update_frequency_compliance"
            ],
            "consistency": [
                "cross_field_validation",
                "historical_consistency"
            ]
        }
    
    async def validate_data_quality(
        self, 
        feed_id: str, 
        data: List[Dict[str, Any]]
    ) -> DataQualityMetrics:
        """Perform comprehensive data quality validation"""
        
        assessment_results = {
            "completeness": await self._assess_completeness(data),
            "accuracy": await self._assess_accuracy(data),
            "timeliness": await self._assess_timeliness(data),
            "consistency": await self._assess_consistency(data)
        }
        
        # Calculate overall quality score
        overall_score = sum(assessment_results.values()) / len(assessment_results)
        
        # Identify issues and recommendations
        issues = []
        recommendations = []
        
        for dimension, score in assessment_results.items():
            if score < 0.8:
                issues.append(f"Low {dimension} score: {score:.2f}")
                recommendations.append(f"Improve {dimension} validation rules")
        
        return DataQualityMetrics(
            feed_id=feed_id,
            assessment_date=datetime.now(timezone.utc),
            completeness_score=assessment_results["completeness"],
            accuracy_score=assessment_results["accuracy"],
            timeliness_score=assessment_results["timeliness"],
            consistency_score=assessment_results["consistency"],
            overall_quality_score=overall_score,
            issues_detected=issues,
            recommendations=recommendations
        )
    
    async def _assess_completeness(self, data: List[Dict[str, Any]]) -> float:
        """Assess data completeness"""
        if not data:
            return 0.0
        
        total_fields = 0
        missing_fields = 0
        
        for record in data:
            for value in record.values():
                total_fields += 1
                if value is None or value == "":
                    missing_fields += 1
        
        completeness = (total_fields - missing_fields) / total_fields if total_fields > 0 else 0
        return min(1.0, completeness)
    
    async def _assess_accuracy(self, data: List[Dict[str, Any]]) -> float:
        """Assess data accuracy"""
        if not data:
            return 0.0
        
        valid_records = 0
        total_records = len(data)
        
        for record in data:
            is_valid = True
            
            # Check numeric fields
            for key, value in record.items():
                if key in ["price", "volume", "market_cap"] and value is not None:
                    try:
                        numeric_value = float(value)
                        if numeric_value < 0:  # Basic validation
                            is_valid = False
                            break
                    except (ValueError, TypeError):
                        is_valid = False
                        break
            
            if is_valid:
                valid_records += 1
        
        return valid_records / total_records if total_records > 0 else 0
    
    async def _assess_timeliness(self, data: List[Dict[str, Any]]) -> float:
        """Assess data timeliness"""
        if not data:
            return 0.0
        
        current_time = datetime.now(timezone.utc)
        timely_records = 0
        
        for record in data:
            timestamp_str = record.get("timestamp") or record.get("created_at")
            if timestamp_str:
                try:
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    else:
                        timestamp = timestamp_str
                    
                    age_hours = (current_time - timestamp).total_seconds() / 3600
                    if age_hours <= 24:  # Consider data timely if less than 24 hours old
                        timely_records += 1
                except:
                    pass  # Invalid timestamp format
        
        return timely_records / len(data) if data else 0
    
    async def _assess_consistency(self, data: List[Dict[str, Any]]) -> float:
        """Assess data consistency"""
        if len(data) < 2:
            return 1.0  # Cannot assess consistency with less than 2 records
        
        consistent_records = 0
        total_comparisons = 0
        
        # Check for consistent data types and formats
        for i in range(len(data) - 1):
            current = data[i]
            next_record = data[i + 1]
            
            for key in current.keys():
                if key in next_record:
                    total_comparisons += 1
                    
                    # Check type consistency
                    if type(current[key]) == type(next_record[key]):
                        consistent_records += 1
        
        return consistent_records / total_comparisons if total_comparisons > 0 else 1.0

class ThirdPartyDataIntegrationSystem:
    """Main third-party data integration orchestrator"""
    
    def __init__(self):
        self.providers = {}
        self.adapters = {}
        self.data_feeds = {}
        self.quality_validator = DataQualityValidator()
        self.usage_metrics = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize system
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize default data providers"""
        
        # Bloomberg provider
        bloomberg_config = DataProviderConfig(
            provider_id="bloomberg_01",
            provider_name="Bloomberg Terminal",
            provider_type=DataProviderType.TRADITIONAL_FINANCIAL,
            api_endpoint="https://api.bloomberg.com/v1",
            authentication_method="api_key",
            credentials={"api_key": "mock_bloomberg_key"},
            rate_limits={"requests_per_minute": 60, "requests_per_day": 10000},
            supported_formats=[DataFormat.JSON, DataFormat.XML],
            cost_per_request=0.10,
            data_categories=["equity", "fixed_income", "derivatives", "currencies"],
            reliability_score=0.99,
            created_at=datetime.now(timezone.utc)
        )
        
        self.providers[bloomberg_config.provider_id] = bloomberg_config
        self.adapters[bloomberg_config.provider_id] = BloombergAdapter(bloomberg_config)
        
        # Alpha Vantage provider
        alphavantage_config = DataProviderConfig(
            provider_id="alphavantage_01",
            provider_name="Alpha Vantage",
            provider_type=DataProviderType.MARKET_DATA,
            api_endpoint="https://www.alphavantage.co/query",
            authentication_method="api_key",
            credentials={"apikey": "mock_av_key"},
            rate_limits={"requests_per_minute": 5, "requests_per_day": 500},
            supported_formats=[DataFormat.JSON, DataFormat.CSV],
            cost_per_request=0.01,
            data_categories=["stocks", "forex", "crypto", "technical_indicators"],
            reliability_score=0.92,
            created_at=datetime.now(timezone.utc)
        )
        
        self.providers[alphavantage_config.provider_id] = alphavantage_config
        self.adapters[alphavantage_config.provider_id] = AlphaVantageAdapter(alphavantage_config)
        
        # Twitter sentiment provider
        twitter_config = DataProviderConfig(
            provider_id="twitter_01",
            provider_name="Twitter/X API",
            provider_type=DataProviderType.ALTERNATIVE_DATA,
            api_endpoint="https://api.twitter.com/2",
            authentication_method="oauth",
            credentials={"bearer_token": "mock_twitter_token"},
            rate_limits={"requests_per_15min": 300, "tweets_per_month": 2000000},
            supported_formats=[DataFormat.JSON],
            cost_per_request=0.005,
            data_categories=["sentiment", "social_trends", "influencer_data"],
            reliability_score=0.85,
            created_at=datetime.now(timezone.utc)
        )
        
        self.providers[twitter_config.provider_id] = twitter_config
        self.adapters[twitter_config.provider_id] = TwitterSentimentAdapter(twitter_config)
        
        # News API provider
        newsapi_config = DataProviderConfig(
            provider_id="newsapi_01",
            provider_name="News API",
            provider_type=DataProviderType.NEWS_MEDIA,
            api_endpoint="https://newsapi.org/v2",
            authentication_method="api_key",
            credentials={"api_key": "mock_newsapi_key"},
            rate_limits={"requests_per_day": 1000},
            supported_formats=[DataFormat.JSON],
            cost_per_request=0.02,
            data_categories=["business_news", "financial_news", "market_news"],
            reliability_score=0.90,
            created_at=datetime.now(timezone.utc)
        )
        
        self.providers[newsapi_config.provider_id] = newsapi_config
        self.adapters[newsapi_config.provider_id] = NewsAPIAdapter(newsapi_config)
    
    async def create_data_feed(
        self,
        feed_name: str,
        provider_id: str,
        data_category: str,
        symbols: List[str],
        update_frequency: UpdateFrequency
    ) -> DataFeed:
        """Create new data feed configuration"""
        
        if provider_id not in self.providers:
            raise ValueError(f"Provider {provider_id} not found")
        
        feed_id = f"feed_{uuid.uuid4().hex[:8]}"
        provider = self.providers[provider_id]
        
        feed = DataFeed(
            feed_id=feed_id,
            feed_name=feed_name,
            provider_id=provider_id,
            data_category=data_category,
            symbols=symbols,
            update_frequency=update_frequency,
            data_format=provider.supported_formats[0],  # Use first supported format
            transformation_rules={},
            quality_checks=["completeness", "accuracy", "timeliness"],
            retention_days=365,
            created_at=datetime.now(timezone.utc)
        )
        
        self.data_feeds[feed_id] = feed
        return feed
    
    async def fetch_feed_data(
        self,
        feed_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Fetch data for specific feed"""
        
        if feed_id not in self.data_feeds:
            raise ValueError(f"Feed {feed_id} not found")
        
        feed = self.data_feeds[feed_id]
        provider = self.providers[feed.provider_id]
        adapter = self.adapters[feed.provider_id]
        
        # Check authentication
        if not await adapter.authenticate():
            raise RuntimeError(f"Authentication failed for {provider.provider_name}")
        
        # Prepare parameters
        parameters = {
            "symbols": feed.symbols,
            "category": feed.data_category
        }
        
        if start_date and end_date:
            parameters.update({
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            })
        
        # Fetch raw data
        raw_data = await adapter.fetch_data("", parameters)
        
        # Normalize data
        normalized_data = adapter.normalize_data(raw_data)
        
        # Validate data quality
        quality_metrics = await self.quality_validator.validate_data_quality(
            feed_id, normalized_data
        )
        
        # Update usage metrics
        await self._update_usage_metrics(provider.provider_id, len(normalized_data))
        
        # Update feed last updated time
        feed.last_updated = datetime.now(timezone.utc)
        
        return {
            "feed_id": feed_id,
            "provider": provider.provider_name,
            "data_count": len(normalized_data),
            "data": normalized_data,
            "quality_metrics": {
                "overall_score": quality_metrics.overall_quality_score,
                "completeness": quality_metrics.completeness_score,
                "accuracy": quality_metrics.accuracy_score,
                "timeliness": quality_metrics.timeliness_score,
                "consistency": quality_metrics.consistency_score,
                "issues": quality_metrics.issues_detected
            },
            "fetch_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _update_usage_metrics(self, provider_id: str, request_count: int):
        """Update provider usage metrics"""
        
        if provider_id not in self.usage_metrics:
            self.usage_metrics[provider_id] = {
                "total_requests": 0,
                "total_cost": 0.0,
                "daily_usage": {},
                "monthly_usage": {}
            }
        
        provider = self.providers[provider_id]
        metrics = self.usage_metrics[provider_id]
        
        # Update totals
        metrics["total_requests"] += request_count
        metrics["total_cost"] += provider.cost_per_request * request_count
        
        # Update daily usage
        today = datetime.now().strftime("%Y-%m-%d")
        metrics["daily_usage"][today] = metrics["daily_usage"].get(today, 0) + request_count
        
        # Update monthly usage
        this_month = datetime.now().strftime("%Y-%m")
        metrics["monthly_usage"][this_month] = metrics["monthly_usage"].get(this_month, 0) + request_count
    
    def get_provider_catalog(self) -> List[Dict[str, Any]]:
        """Get catalog of available data providers"""
        
        catalog = []
        
        for provider_id, provider in self.providers.items():
            usage = self.usage_metrics.get(provider_id, {})
            
            catalog.append({
                "provider_id": provider_id,
                "provider_name": provider.provider_name,
                "provider_type": provider.provider_type.value,
                "data_categories": provider.data_categories,
                "supported_formats": [fmt.value for fmt in provider.supported_formats],
                "cost_per_request": provider.cost_per_request,
                "reliability_score": provider.reliability_score,
                "rate_limits": provider.rate_limits,
                "total_usage": usage.get("total_requests", 0),
                "total_cost": usage.get("total_cost", 0.0),
                "status": provider.status
            })
        
        return catalog
    
    def get_feed_summary(self) -> Dict[str, Any]:
        """Get summary of all data feeds"""
        
        active_feeds = len([f for f in self.data_feeds.values() if f.status == "active"])
        total_symbols = sum(len(f.symbols) for f in self.data_feeds.values())
        
        feeds_by_provider = {}
        feeds_by_frequency = {}
        
        for feed in self.data_feeds.values():
            # Count by provider
            provider_name = self.providers[feed.provider_id].provider_name
            feeds_by_provider[provider_name] = feeds_by_provider.get(provider_name, 0) + 1
            
            # Count by frequency
            freq = feed.update_frequency.value
            feeds_by_frequency[freq] = feeds_by_frequency.get(freq, 0) + 1
        
        return {
            "total_feeds": len(self.data_feeds),
            "active_feeds": active_feeds,
            "total_symbols": total_symbols,
            "feeds_by_provider": feeds_by_provider,
            "feeds_by_frequency": feeds_by_frequency,
            "total_providers": len(self.providers),
            "active_providers": len([p for p in self.providers.values() if p.status == "active"])
        }
    
    async def run_quality_assessment(self) -> Dict[str, Any]:
        """Run quality assessment across all active feeds"""
        
        assessment_results = {
            "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
            "feeds_assessed": 0,
            "quality_scores": {},
            "overall_quality": 0.0,
            "high_quality_feeds": 0,
            "issues_summary": {}
        }
        
        total_quality_score = 0.0
        feeds_assessed = 0
        
        for feed_id, feed in self.data_feeds.items():
            if feed.status == "active":
                try:
                    # Fetch recent data for quality assessment
                    result = await self.fetch_feed_data(feed_id)
                    quality_score = result["quality_metrics"]["overall_score"]
                    
                    assessment_results["quality_scores"][feed_id] = {
                        "feed_name": feed.feed_name,
                        "provider": self.providers[feed.provider_id].provider_name,
                        "quality_score": quality_score,
                        "issues": result["quality_metrics"]["issues"]
                    }
                    
                    total_quality_score += quality_score
                    feeds_assessed += 1
                    
                    if quality_score >= 0.8:
                        assessment_results["high_quality_feeds"] += 1
                    
                    # Aggregate issues
                    for issue in result["quality_metrics"]["issues"]:
                        issue_type = issue.split(":")[0]
                        assessment_results["issues_summary"][issue_type] = \
                            assessment_results["issues_summary"].get(issue_type, 0) + 1
                
                except Exception as e:
                    self.logger.error(f"Quality assessment failed for feed {feed_id}: {str(e)}")
        
        assessment_results["feeds_assessed"] = feeds_assessed
        assessment_results["overall_quality"] = total_quality_score / feeds_assessed if feeds_assessed > 0 else 0.0
        
        return assessment_results
    
    def get_cost_analysis(self, period_days: int = 30) -> Dict[str, Any]:
        """Get cost analysis for data providers"""
        
        total_cost = 0.0
        cost_by_provider = {}
        
        for provider_id, usage in self.usage_metrics.items():
            provider_name = self.providers[provider_id].provider_name
            provider_cost = usage.get("total_cost", 0.0)
            
            cost_by_provider[provider_name] = provider_cost
            total_cost += provider_cost
        
        # Calculate average daily cost
        avg_daily_cost = total_cost / period_days if period_days > 0 else 0.0
        
        return {
            "analysis_period_days": period_days,
            "total_cost": total_cost,
            "average_daily_cost": avg_daily_cost,
            "projected_monthly_cost": avg_daily_cost * 30,
            "cost_by_provider": cost_by_provider,
            "highest_cost_provider": max(cost_by_provider.items(), key=lambda x: x[1]) if cost_by_provider else None
        }

# Example usage and testing
if __name__ == "__main__":
    async def test_third_party_integration():
        integration_system = ThirdPartyDataIntegrationSystem()
        
        print("Testing Third-party Data Integration System...")
        
        # Test provider catalog
        print("\n1. Testing Provider Catalog:")
        catalog = integration_system.get_provider_catalog()
        print(f"Available providers: {len(catalog)}")
        
        for provider in catalog:
            print(f"  - {provider['provider_name']} ({provider['provider_type']})")
            print(f"    Categories: {', '.join(provider['data_categories'])}")
            print(f"    Cost: ${provider['cost_per_request']}/request")
            print(f"    Reliability: {provider['reliability_score']:.2%}")
        
        # Test data feed creation
        print("\n2. Testing Data Feed Creation:")
        
        # Create market data feed
        market_feed = await integration_system.create_data_feed(
            "AAPL Market Data",
            "alphavantage_01",
            "stocks",
            ["AAPL", "TSLA", "MSFT"],
            UpdateFrequency.DAILY
        )
        print(f"Created market feed: {market_feed.feed_id}")
        
        # Create sentiment feed
        sentiment_feed = await integration_system.create_data_feed(
            "Tech Stocks Sentiment",
            "twitter_01",
            "sentiment",
            ["$AAPL", "$TSLA", "$MSFT"],
            UpdateFrequency.HOURLY
        )
        print(f"Created sentiment feed: {sentiment_feed.feed_id}")
        
        # Create news feed
        news_feed = await integration_system.create_data_feed(
            "Financial News",
            "newsapi_01",
            "business_news",
            ["Apple", "Tesla", "Microsoft"],
            UpdateFrequency.HOURLY
        )
        print(f"Created news feed: {news_feed.feed_id}")
        
        # Test data fetching
        print("\n3. Testing Data Fetching:")
        
        # Fetch market data
        market_data = await integration_system.fetch_feed_data(market_feed.feed_id)
        print(f"Market data: {market_data['data_count']} records")
        print(f"Quality score: {market_data['quality_metrics']['overall_score']:.2%}")
        
        # Fetch sentiment data
        sentiment_data = await integration_system.fetch_feed_data(sentiment_feed.feed_id)
        print(f"Sentiment data: {sentiment_data['data_count']} records")
        print(f"Quality score: {sentiment_data['quality_metrics']['overall_score']:.2%}")
        
        # Fetch news data
        news_data = await integration_system.fetch_feed_data(news_feed.feed_id)
        print(f"News data: {news_data['data_count']} records")
        print(f"Quality score: {news_data['quality_metrics']['overall_score']:.2%}")
        
        # Test feed summary
        print("\n4. Testing Feed Summary:")
        summary = integration_system.get_feed_summary()
        print(f"Total feeds: {summary['total_feeds']}")
        print(f"Active feeds: {summary['active_feeds']}")
        print(f"Total symbols: {summary['total_symbols']}")
        print(f"Feeds by provider: {summary['feeds_by_provider']}")
        
        # Test quality assessment
        print("\n5. Testing Quality Assessment:")
        quality_assessment = await integration_system.run_quality_assessment()
        print(f"Feeds assessed: {quality_assessment['feeds_assessed']}")
        print(f"Overall quality: {quality_assessment['overall_quality']:.2%}")
        print(f"High quality feeds: {quality_assessment['high_quality_feeds']}")
        
        # Test cost analysis
        print("\n6. Testing Cost Analysis:")
        cost_analysis = integration_system.get_cost_analysis(30)
        print(f"Total cost (30 days): ${cost_analysis['total_cost']:.2f}")
        print(f"Average daily cost: ${cost_analysis['average_daily_cost']:.2f}")
        print(f"Projected monthly cost: ${cost_analysis['projected_monthly_cost']:.2f}")
        
        if cost_analysis['highest_cost_provider']:
            provider, cost = cost_analysis['highest_cost_provider']
            print(f"Highest cost provider: {provider} (${cost:.2f})")
        
        return integration_system
    
    # Run test
    system = asyncio.run(test_third_party_integration())
    print("\nThird-party Data Integration System test completed successfully!")