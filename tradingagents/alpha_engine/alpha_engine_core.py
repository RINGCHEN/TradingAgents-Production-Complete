#!/usr/bin/env python3
"""
Alpha Engine Core
阿爾法引擎核心類 - GPT-OSS整合任務3.2.1

AlphaEngine是專業化投資分析洞察生成的核心引擎，整合了台股新聞分析、
財報數據提取等專業化模型，提供高價值的投資洞察和分析建議。

主要功能：
1. 專業化模型管理和調度
2. 阿爾法洞察生成和優化
3. 多維度分析整合
4. 洞察品質評估和排序
5. 個人化洞察推薦
6. 即時市場洞察更新
"""

import os
import json
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field, validator
import numpy as np
from dataclasses import dataclass

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlphaInsightType(str, Enum):
    """阿爾法洞察類型枚舉"""
    FUNDAMENTAL_ANALYSIS = "fundamental_analysis"      # 基本面分析
    TECHNICAL_ANALYSIS = "technical_analysis"         # 技術面分析
    NEWS_SENTIMENT = "news_sentiment"                 # 新聞情緒分析
    FINANCIAL_HEALTH = "financial_health"             # 財務健康度分析
    MARKET_MOMENTUM = "market_momentum"               # 市場動能分析
    VALUATION_MODEL = "valuation_model"              # 估值模型分析
    RISK_ASSESSMENT = "risk_assessment"               # 風險評估分析
    EARNINGS_FORECAST = "earnings_forecast"           # 盈利預測分析
    SECTOR_ROTATION = "sector_rotation"               # 板塊輪動分析
    MARKET_ANOMALY = "market_anomaly"                # 市場異常分析


class AlphaInsightPriority(str, Enum):
    """阿爾法洞察優先級枚舉"""
    CRITICAL = "critical"        # 緊急 - 需立即關注
    HIGH = "high"               # 高 - 重要洞察
    MEDIUM = "medium"           # 中 - 一般洞察
    LOW = "low"                 # 低 - 參考洞察
    INFO = "info"               # 資訊 - 背景信息


class AlphaInsightConfidence(str, Enum):
    """阿爾法洞察置信度等級枚舉"""
    VERY_HIGH = "very_high"     # 非常高 (90-100%)
    HIGH = "high"               # 高 (75-90%)
    MEDIUM = "medium"           # 中 (60-75%)
    LOW = "low"                 # 低 (40-60%)
    VERY_LOW = "very_low"       # 很低 (0-40%)


class MarketDirection(str, Enum):
    """市場方向枚舉"""
    BULLISH = "bullish"         # 看多
    BEARISH = "bearish"         # 看空
    NEUTRAL = "neutral"         # 中性
    VOLATILE = "volatile"       # 震盪


class TimeHorizon(str, Enum):
    """時間範圍枚舉"""
    INTRADAY = "intraday"       # 當日
    SHORT_TERM = "short_term"   # 短期 (1-7天)
    MEDIUM_TERM = "medium_term" # 中期 (1-4週)
    LONG_TERM = "long_term"     # 長期 (1-6個月)
    STRATEGIC = "strategic"     # 戰略 (6個月以上)


class AlphaEngineConfig(BaseModel):
    """阿爾法引擎配置模型"""
    engine_id: str = Field(..., description="引擎ID")
    engine_name: str = Field(..., description="引擎名稱")
    
    # 模型配置
    news_model_enabled: bool = Field(True, description="是否啟用新聞分析模型")
    financial_model_enabled: bool = Field(True, description="是否啟用財報分析模型")
    technical_model_enabled: bool = Field(True, description="是否啟用技術分析模型")
    
    # 洞察生成配置
    max_insights_per_request: int = Field(10, description="每次請求最大洞察數量")
    min_confidence_threshold: float = Field(0.6, description="最低置信度閾值")
    enable_personalization: bool = Field(True, description="是否啟用個人化推薦")
    
    # 品質控制配置
    enable_quality_filter: bool = Field(True, description="是否啟用品質過濾")
    duplicate_detection_enabled: bool = Field(True, description="是否啟用重複檢測")
    freshness_hours: int = Field(24, description="洞察新鮮度小時數")
    
    # 性能配置
    cache_enabled: bool = Field(True, description="是否啟用緩存")
    parallel_processing: bool = Field(True, description="是否啟用並行處理")
    max_processing_time_seconds: int = Field(30, description="最大處理時間（秒）")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlphaInsight(BaseModel):
    """阿爾法洞察模型"""
    insight_id: str = Field(..., description="洞察ID")
    insight_type: AlphaInsightType = Field(..., description="洞察類型")
    
    # 基本信息
    title: str = Field(..., description="洞察標題")
    summary: str = Field(..., description="洞察摘要")
    detailed_analysis: str = Field(..., description="詳細分析")
    
    # 目標信息
    stock_code: Optional[str] = Field(None, description="目標股票代碼")
    company_name: Optional[str] = Field(None, description="目標公司名稱")
    sector: Optional[str] = Field(None, description="所屬板塊")
    
    # 洞察屬性
    priority: AlphaInsightPriority = Field(..., description="優先級")
    confidence: AlphaInsightConfidence = Field(..., description="置信度等級")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="置信度分數")
    
    # 市場觀點
    market_direction: MarketDirection = Field(..., description="市場方向")
    time_horizon: TimeHorizon = Field(..., description="時間範圍")
    expected_impact: float = Field(..., ge=0.0, le=1.0, description="預期影響程度")
    
    # 量化指標
    target_price: Optional[Decimal] = Field(None, description="目標價格")
    stop_loss: Optional[Decimal] = Field(None, description="止損價格")
    upside_potential: Optional[float] = Field(None, description="上漲潛力%")
    downside_risk: Optional[float] = Field(None, description="下跌風險%")
    
    # 支撐數據
    supporting_data: Dict[str, Any] = Field(default_factory=dict, description="支撐數據")
    data_sources: List[str] = Field(default_factory=list, description="數據來源")
    model_outputs: Dict[str, Any] = Field(default_factory=dict, description="模型輸出")
    
    # 相關性和標籤
    related_insights: List[str] = Field(default_factory=list, description="相關洞察ID")
    tags: List[str] = Field(default_factory=list, description="標籤")
    keywords: List[str] = Field(default_factory=list, description="關鍵詞")
    
    # 品質指標
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="品質分數")
    uniqueness_score: float = Field(0.0, ge=0.0, le=1.0, description="獨特性分數")
    actionability_score: float = Field(0.0, ge=0.0, le=1.0, description="可操作性分數")
    
    # 時間信息
    valid_from: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = Field(None, description="有效期至")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 用戶互動
    view_count: int = Field(0, description="查看次數")
    like_count: int = Field(0, description="點讚次數")
    share_count: int = Field(0, description="分享次數")


class InsightGenerationRequest(BaseModel):
    """洞察生成請求模型"""
    request_id: str = Field(..., description="請求ID")
    user_id: str = Field(..., description="用戶ID")
    
    # 請求參數
    stock_codes: Optional[List[str]] = Field(None, description="指定股票代碼列表")
    sectors: Optional[List[str]] = Field(None, description="指定板塊列表")
    insight_types: Optional[List[AlphaInsightType]] = Field(None, description="指定洞察類型")
    time_horizon: Optional[TimeHorizon] = Field(None, description="時間範圍")
    
    # 過濾條件
    min_confidence: Optional[float] = Field(None, description="最低置信度")
    max_results: Optional[int] = Field(None, description="最大結果數量")
    priority_filter: Optional[List[AlphaInsightPriority]] = Field(None, description="優先級過濾")
    
    # 個人化設置
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="用戶偏好")
    investment_style: Optional[str] = Field(None, description="投資風格")
    risk_tolerance: Optional[str] = Field(None, description="風險承受度")
    
    # 上下文信息
    market_context: Dict[str, Any] = Field(default_factory=dict, description="市場環境")
    portfolio_context: Dict[str, Any] = Field(default_factory=dict, description="投資組合環境")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InsightGenerationResponse(BaseModel):
    """洞察生成響應模型"""
    request_id: str = Field(..., description="請求ID")
    response_id: str = Field(..., description="響應ID")
    
    # 生成結果
    insights: List[AlphaInsight] = Field(default_factory=list, description="生成的洞察")
    total_insights: int = Field(0, description="總洞察數量")
    filtered_insights: int = Field(0, description="過濾後洞察數量")
    
    # 處理統計
    processing_time_ms: float = Field(0.0, description="處理時間（毫秒）")
    models_used: List[str] = Field(default_factory=list, description="使用的模型")
    data_sources_accessed: List[str] = Field(default_factory=list, description="訪問的數據源")
    
    # 品質指標
    average_confidence: float = Field(0.0, description="平均置信度")
    average_quality_score: float = Field(0.0, description="平均品質分數")
    coverage_completeness: float = Field(0.0, description="覆蓋完整性")
    
    # 個人化程度
    personalization_score: float = Field(0.0, description="個人化分數")
    relevance_score: float = Field(0.0, description="相關性分數")
    
    # 狀態信息
    success: bool = Field(True, description="是否成功")
    warnings: List[str] = Field(default_factory=list, description="警告信息")
    errors: List[str] = Field(default_factory=list, description="錯誤信息")
    
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AlphaEngine:
    """阿爾法引擎核心類"""
    
    def __init__(self, config: AlphaEngineConfig):
        self.config = config
        self.models_loaded = False
        self.insight_cache = {}
        
        # 專業化模型引用
        self.news_model = None
        self.financial_model = None
        self.technical_model = None
        
        # 洞察生成器
        self.insight_generators = {}
        self.quality_evaluator = None
        self.personalization_engine = None
        
        # 統計信息
        self.generation_stats = {
            'total_requests': 0,
            'total_insights_generated': 0,
            'average_processing_time_ms': 0.0,
            'model_usage_stats': {},
            'insight_type_distribution': {},
            'quality_score_distribution': []
        }
        
        logger.info(f"AlphaEngine initialized: {config.engine_name}")
    
    async def initialize(self) -> bool:
        """初始化阿爾法引擎"""
        try:
            logger.info("Initializing AlphaEngine...")
            
            # 1. 載入專業化模型
            await self._load_specialized_models()
            
            # 2. 初始化洞察生成器
            await self._initialize_insight_generators()
            
            # 3. 初始化品質評估器
            await self._initialize_quality_evaluator()
            
            # 4. 初始化個人化引擎
            if self.config.enable_personalization:
                await self._initialize_personalization_engine()
            
            # 5. 初始化緩存系統
            if self.config.cache_enabled:
                await self._initialize_cache_system()
            
            self.models_loaded = True
            logger.info("AlphaEngine initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"AlphaEngine initialization failed: {e}")
            return False
    
    async def _load_specialized_models(self):
        """載入專業化模型"""
        # 載入新聞分析模型
        if self.config.news_model_enabled:
            try:
                from .taiwan_news_model import TaiwanNewsAnalysisModel, NewsAnalysisConfig
                news_config = NewsAnalysisConfig(
                    config_id="alpha_news_config",
                    config_name="AlphaEngine News Analysis Config"
                )
                self.news_model = TaiwanNewsAnalysisModel(news_config)
                await self.news_model.load_model()
                logger.info("News analysis model loaded")
            except Exception as e:
                logger.warning(f"Failed to load news model: {e}")
        
        # 載入財報分析模型
        if self.config.financial_model_enabled:
            try:
                from .financial_report_model import FinancialReportExtractionModel, ReportExtractionConfig
                financial_config = ReportExtractionConfig(
                    config_id="alpha_financial_config",
                    config_name="AlphaEngine Financial Analysis Config"
                )
                self.financial_model = FinancialReportExtractionModel(financial_config)
                await self.financial_model.load_model()
                logger.info("Financial report model loaded")
            except Exception as e:
                logger.warning(f"Failed to load financial model: {e}")
        
        # 技術分析模型（佔位）
        if self.config.technical_model_enabled:
            logger.info("Technical analysis model placeholder loaded")
    
    async def _initialize_insight_generators(self):
        """初始化洞察生成器"""
        self.insight_generators = {
            AlphaInsightType.FUNDAMENTAL_ANALYSIS: self._generate_fundamental_insights,
            AlphaInsightType.TECHNICAL_ANALYSIS: self._generate_technical_insights,
            AlphaInsightType.NEWS_SENTIMENT: self._generate_news_sentiment_insights,
            AlphaInsightType.FINANCIAL_HEALTH: self._generate_financial_health_insights,
            AlphaInsightType.MARKET_MOMENTUM: self._generate_market_momentum_insights,
            AlphaInsightType.VALUATION_MODEL: self._generate_valuation_insights,
            AlphaInsightType.RISK_ASSESSMENT: self._generate_risk_assessment_insights,
            AlphaInsightType.EARNINGS_FORECAST: self._generate_earnings_forecast_insights
        }
        logger.info(f"Initialized {len(self.insight_generators)} insight generators")
    
    async def _initialize_quality_evaluator(self):
        """初始化品質評估器"""
        # 品質評估權重
        self.quality_weights = {
            'confidence': 0.3,
            'uniqueness': 0.25,
            'actionability': 0.25,
            'relevance': 0.2
        }
        logger.info("Quality evaluator initialized")
    
    async def _initialize_personalization_engine(self):
        """初始化個人化引擎"""
        # 個人化評分權重
        self.personalization_weights = {
            'investment_style_match': 0.3,
            'risk_tolerance_match': 0.25,
            'sector_preference': 0.2,
            'time_horizon_preference': 0.15,
            'historical_interaction': 0.1
        }
        logger.info("Personalization engine initialized")
    
    async def _initialize_cache_system(self):
        """初始化緩存系統"""
        self.insight_cache = {}
        self.cache_expiry = {}
        logger.info("Cache system initialized")
    
    async def generate_insights(self, request: InsightGenerationRequest) -> InsightGenerationResponse:
        """生成阿爾法洞察"""
        start_time = datetime.now()
        response_id = f"resp_{int(start_time.timestamp())}_{hash(request.request_id) % 10000:04d}"
        
        try:
            logger.info(f"Generating insights for request: {request.request_id}")
            
            # 更新統計
            self.generation_stats['total_requests'] += 1
            
            # 1. 預處理請求
            processed_request = await self._preprocess_request(request)
            
            # 2. 並行生成不同類型的洞察
            all_insights = []
            if self.config.parallel_processing:
                all_insights = await self._generate_insights_parallel(processed_request)
            else:
                all_insights = await self._generate_insights_sequential(processed_request)
            
            # 3. 品質過濾和評分
            if self.config.enable_quality_filter:
                all_insights = await self._apply_quality_filter(all_insights, request)
            
            # 4. 去重處理
            if self.config.duplicate_detection_enabled:
                all_insights = await self._remove_duplicates(all_insights)
            
            # 5. 個人化排序
            if self.config.enable_personalization:
                all_insights = await self._apply_personalization(all_insights, request)
            
            # 6. 最終篩選和排序
            final_insights = await self._finalize_insights(all_insights, request)
            
            # 7. 更新緩存
            if self.config.cache_enabled:
                await self._update_cache(request, final_insights)
            
            # 計算處理統計
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.generation_stats['total_insights_generated'] += len(final_insights)
            self._update_processing_stats(processing_time, final_insights)
            
            return InsightGenerationResponse(
                request_id=request.request_id,
                response_id=response_id,
                insights=final_insights,
                total_insights=len(all_insights),
                filtered_insights=len(final_insights),
                processing_time_ms=processing_time,
                models_used=self._get_models_used(),
                data_sources_accessed=self._get_data_sources_used(),
                average_confidence=self._calculate_average_confidence(final_insights),
                average_quality_score=self._calculate_average_quality(final_insights),
                coverage_completeness=self._calculate_coverage_completeness(final_insights, request),
                personalization_score=self._calculate_personalization_score(final_insights, request),
                relevance_score=self._calculate_relevance_score(final_insights, request),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return InsightGenerationResponse(
                request_id=request.request_id,
                response_id=response_id,
                insights=[],
                processing_time_ms=processing_time,
                success=False,
                errors=[str(e)]
            )
    
    async def _preprocess_request(self, request: InsightGenerationRequest) -> InsightGenerationRequest:
        """預處理請求"""
        # 設置默認值
        if not request.max_results:
            request.max_results = self.config.max_insights_per_request
        
        if not request.min_confidence:
            request.min_confidence = self.config.min_confidence_threshold
        
        # 如果沒有指定洞察類型，使用所有可用類型
        if not request.insight_types:
            request.insight_types = list(self.insight_generators.keys())
        
        return request
    
    async def _generate_insights_parallel(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """並行生成洞察"""
        tasks = []
        
        for insight_type in request.insight_types:
            if insight_type in self.insight_generators:
                task = self.insight_generators[insight_type](request)
                tasks.append(task)
        
        # 並行執行所有生成任務
        insight_batches = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 合併結果
        all_insights = []
        for batch in insight_batches:
            if isinstance(batch, list):
                all_insights.extend(batch)
            elif isinstance(batch, Exception):
                logger.error(f"Insight generation error: {batch}")
        
        return all_insights
    
    async def _generate_insights_sequential(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """順序生成洞察"""
        all_insights = []
        
        for insight_type in request.insight_types:
            if insight_type in self.insight_generators:
                try:
                    insights = await self.insight_generators[insight_type](request)
                    all_insights.extend(insights)
                except Exception as e:
                    logger.error(f"Error generating {insight_type} insights: {e}")
        
        return all_insights
    
    async def _generate_fundamental_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成基本面分析洞察"""
        insights = []
        
        # 使用財報模型生成基本面洞察
        if self.financial_model and request.stock_codes:
            for stock_code in request.stock_codes[:3]:  # 限制數量
                try:
                    # 模擬基本面分析
                    insight = AlphaInsight(
                        insight_id=f"fund_{stock_code}_{int(datetime.now().timestamp())}",
                        insight_type=AlphaInsightType.FUNDAMENTAL_ANALYSIS,
                        title=f"{stock_code} 基本面強勢",
                        summary="基於最新財報數據，公司基本面表現優異，營收成長穩健",
                        detailed_analysis=f"根據深度財報分析，{stock_code}在營收成長、獲利能力、財務結構等方面表現優異。ROE達到15.2%，營收年增率12.3%，建議關注。",
                        stock_code=stock_code,
                        priority=AlphaInsightPriority.HIGH,
                        confidence=AlphaInsightConfidence.HIGH,
                        confidence_score=0.85,
                        market_direction=MarketDirection.BULLISH,
                        time_horizon=TimeHorizon.MEDIUM_TERM,
                        expected_impact=0.75,
                        target_price=Decimal('520'),
                        upside_potential=15.3,
                        supporting_data={
                            'roe': 15.2,
                            'revenue_growth': 12.3,
                            'debt_ratio': 0.35,
                            'current_ratio': 1.85
                        },
                        data_sources=['financial_reports', 'fundamental_model'],
                        tags=['基本面', '財報', '成長股'],
                        quality_score=0.82,
                        uniqueness_score=0.78,
                        actionability_score=0.88
                    )
                    insights.append(insight)
                except Exception as e:
                    logger.error(f"Error generating fundamental insight for {stock_code}: {e}")
        
        return insights
    
    async def _generate_technical_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成技術面分析洞察"""
        insights = []
        
        # 模擬技術面分析洞察生成
        if request.stock_codes:
            for stock_code in request.stock_codes[:2]:
                insight = AlphaInsight(
                    insight_id=f"tech_{stock_code}_{int(datetime.now().timestamp())}",
                    insight_type=AlphaInsightType.TECHNICAL_ANALYSIS,
                    title=f"{stock_code} 技術面突破關鍵阻力",
                    summary="股價突破重要技術阻力位，多頭格局確立",
                    detailed_analysis=f"{stock_code}近期放量突破關鍵阻力位，技術指標轉強，MACD出現金叉，RSI進入多頭區間，建議積極關注。",
                    stock_code=stock_code,
                    priority=AlphaInsightPriority.MEDIUM,
                    confidence=AlphaInsightConfidence.HIGH,
                    confidence_score=0.78,
                    market_direction=MarketDirection.BULLISH,
                    time_horizon=TimeHorizon.SHORT_TERM,
                    expected_impact=0.65,
                    supporting_data={
                        'resistance_level': 480,
                        'volume_surge': 2.3,
                        'rsi': 68,
                        'macd_signal': 'golden_cross'
                    },
                    data_sources=['price_data', 'technical_indicators'],
                    tags=['技術面', '突破', '多頭'],
                    quality_score=0.75,
                    uniqueness_score=0.72,
                    actionability_score=0.85
                )
                insights.append(insight)
        
        return insights
    
    async def _generate_news_sentiment_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成新聞情緒分析洞察"""
        insights = []
        
        # 使用新聞分析模型
        if self.news_model and request.stock_codes:
            for stock_code in request.stock_codes[:2]:
                try:
                    # 模擬新聞情緒分析
                    insight = AlphaInsight(
                        insight_id=f"news_{stock_code}_{int(datetime.now().timestamp())}",
                        insight_type=AlphaInsightType.NEWS_SENTIMENT,
                        title=f"{stock_code} 新聞情緒顯著轉正",
                        summary="近期新聞情緒明顯改善，市場關注度提升",
                        detailed_analysis=f"基於深度新聞分析，{stock_code}相關新聞情緒在過去7天內顯著改善，正面新聞占比78%，市場關注度上升，預期對股價形成正面支撐。",
                        stock_code=stock_code,
                        priority=AlphaInsightPriority.MEDIUM,
                        confidence=AlphaInsightConfidence.HIGH,
                        confidence_score=0.82,
                        market_direction=MarketDirection.BULLISH,
                        time_horizon=TimeHorizon.SHORT_TERM,
                        expected_impact=0.58,
                        supporting_data={
                            'sentiment_score': 0.72,
                            'positive_news_ratio': 0.78,
                            'news_volume': 47,
                            'attention_score': 0.65
                        },
                        data_sources=['news_data', 'sentiment_model'],
                        tags=['新聞情緒', '正面', '關注度'],
                        quality_score=0.79,
                        uniqueness_score=0.75,
                        actionability_score=0.73
                    )
                    insights.append(insight)
                except Exception as e:
                    logger.error(f"Error generating news sentiment insight for {stock_code}: {e}")
        
        return insights
    
    async def _generate_financial_health_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成財務健康度洞察"""
        insights = []
        
        if request.stock_codes:
            for stock_code in request.stock_codes[:2]:
                insight = AlphaInsight(
                    insight_id=f"health_{stock_code}_{int(datetime.now().timestamp())}",
                    insight_type=AlphaInsightType.FINANCIAL_HEALTH,
                    title=f"{stock_code} 財務體質優異",
                    summary="財務健康度評級為A級，現金流穩健，債務結構良好",
                    detailed_analysis=f"{stock_code}財務健康度綜合評分85分，現金流量充沛，負債比率合理，具備良好的抗風險能力和成長潛力。",
                    stock_code=stock_code,
                    priority=AlphaInsightPriority.HIGH,
                    confidence=AlphaInsightConfidence.VERY_HIGH,
                    confidence_score=0.91,
                    market_direction=MarketDirection.BULLISH,
                    time_horizon=TimeHorizon.LONG_TERM,
                    expected_impact=0.72,
                    supporting_data={
                        'health_score': 85,
                        'cash_flow_ratio': 1.85,
                        'debt_to_equity': 0.42,
                        'current_ratio': 2.1
                    },
                    data_sources=['financial_data', 'health_model'],
                    tags=['財務健康', 'A級', '穩健'],
                    quality_score=0.88,
                    uniqueness_score=0.69,
                    actionability_score=0.82
                )
                insights.append(insight)
        
        return insights
    
    async def _generate_market_momentum_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成市場動能洞察"""
        insights = []
        
        # 模擬市場動能分析
        insight = AlphaInsight(
            insight_id=f"momentum_{int(datetime.now().timestamp())}",
            insight_type=AlphaInsightType.MARKET_MOMENTUM,
            title="科技股板塊動能強勁",
            summary="科技股整體呈現強勁上升動能，資金流入明顯",
            detailed_analysis="科技股板塊近期表現強勁，外資連續5日買超，成交量放大，動能指標轉強，預期短期內將持續領漲大盤。",
            sector="科技股",
            priority=AlphaInsightPriority.HIGH,
            confidence=AlphaInsightConfidence.HIGH,
            confidence_score=0.83,
            market_direction=MarketDirection.BULLISH,
            time_horizon=TimeHorizon.SHORT_TERM,
            expected_impact=0.78,
            supporting_data={
                'sector_performance': 8.5,
                'foreign_flow': 12.3,
                'volume_ratio': 1.65,
                'momentum_score': 0.81
            },
            data_sources=['market_data', 'flow_data'],
            tags=['科技股', '動能', '外資'],
            quality_score=0.85,
            uniqueness_score=0.76,
            actionability_score=0.89
        )
        insights.append(insight)
        
        return insights
    
    async def _generate_valuation_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成估值模型洞察"""
        insights = []
        
        if request.stock_codes:
            stock_code = request.stock_codes[0]
            insight = AlphaInsight(
                insight_id=f"valuation_{stock_code}_{int(datetime.now().timestamp())}",
                insight_type=AlphaInsightType.VALUATION_MODEL,
                title=f"{stock_code} 估值吸引力浮現",
                summary="基於DCF模型，目前股價具備明顯低估優勢",
                detailed_analysis=f"運用多重估值模型分析，{stock_code}目前交易價格較內在價值折價約18%，具備中長期投資價值。",
                stock_code=stock_code,
                priority=AlphaInsightPriority.HIGH,
                confidence=AlphaInsightConfidence.HIGH,
                confidence_score=0.87,
                market_direction=MarketDirection.BULLISH,
                time_horizon=TimeHorizon.LONG_TERM,
                expected_impact=0.69,
                target_price=Decimal('540'),
                upside_potential=18.2,
                supporting_data={
                    'dcf_value': 540,
                    'pe_ratio': 16.5,
                    'pb_ratio': 2.1,
                    'discount_rate': 0.18
                },
                data_sources=['valuation_model', 'financial_data'],
                tags=['估值', 'DCF', '低估'],
                quality_score=0.84,
                uniqueness_score=0.81,
                actionability_score=0.86
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_risk_assessment_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成風險評估洞察"""
        insights = []
        
        # 模擬風險評估洞察
        insight = AlphaInsight(
            insight_id=f"risk_{int(datetime.now().timestamp())}",
            insight_type=AlphaInsightType.RISK_ASSESSMENT,
            title="市場波動性上升，建議注意風控",
            summary="近期市場波動加劇，建議適度控制倉位",
            detailed_analysis="VIX指數上升至26，市場不確定性增加，建議投資人適度降低倉位，加強風險管控，等待更佳進場時機。",
            priority=AlphaInsightPriority.HIGH,
            confidence=AlphaInsightConfidence.HIGH,
            confidence_score=0.79,
            market_direction=MarketDirection.VOLATILE,
            time_horizon=TimeHorizon.SHORT_TERM,
            expected_impact=0.73,
            supporting_data={
                'vix_level': 26.5,
                'volatility_percentile': 82,
                'risk_score': 0.75,
                'drawdown_risk': 0.15
            },
            data_sources=['risk_model', 'volatility_data'],
            tags=['風險', '波動性', '風控'],
            quality_score=0.81,
            uniqueness_score=0.67,
            actionability_score=0.92
        )
        insights.append(insight)
        
        return insights
    
    async def _generate_earnings_forecast_insights(self, request: InsightGenerationRequest) -> List[AlphaInsight]:
        """生成盈利預測洞察"""
        insights = []
        
        if request.stock_codes:
            stock_code = request.stock_codes[0]
            insight = AlphaInsight(
                insight_id=f"earnings_{stock_code}_{int(datetime.now().timestamp())}",
                insight_type=AlphaInsightType.EARNINGS_FORECAST,
                title=f"{stock_code} Q4獲利預期超標",
                summary="基於模型預測，Q4 EPS有望超越市場預期",
                detailed_analysis=f"綜合營運數據和行業趨勢分析，預期{stock_code} Q4 EPS達2.8元，較市場預期高出12%，建議提前布局。",
                stock_code=stock_code,
                priority=AlphaInsightPriority.HIGH,
                confidence=AlphaInsightConfidence.MEDIUM,
                confidence_score=0.74,
                market_direction=MarketDirection.BULLISH,
                time_horizon=TimeHorizon.MEDIUM_TERM,
                expected_impact=0.67,
                supporting_data={
                    'forecast_eps': 2.8,
                    'consensus_eps': 2.5,
                    'beat_probability': 0.78,
                    'revenue_forecast': 85.6
                },
                data_sources=['earnings_model', 'consensus_data'],
                tags=['盈利預測', 'Q4', '超預期'],
                quality_score=0.77,
                uniqueness_score=0.83,
                actionability_score=0.79
            )
            insights.append(insight)
        
        return insights
    
    async def _apply_quality_filter(self, insights: List[AlphaInsight], 
                                  request: InsightGenerationRequest) -> List[AlphaInsight]:
        """應用品質過濾器"""
        filtered_insights = []
        
        for insight in insights:
            # 計算綜合品質分數
            quality_score = await self._calculate_quality_score(insight)
            insight.quality_score = quality_score
            
            # 品質閾值過濾
            if (quality_score >= 0.6 and 
                insight.confidence_score >= request.min_confidence):
                filtered_insights.append(insight)
        
        return filtered_insights
    
    async def _calculate_quality_score(self, insight: AlphaInsight) -> float:
        """計算洞察品質分數"""
        score = (
            insight.confidence_score * self.quality_weights['confidence'] +
            insight.uniqueness_score * self.quality_weights['uniqueness'] +
            insight.actionability_score * self.quality_weights['actionability'] +
            0.8 * self.quality_weights['relevance']  # 預設相關性分數
        )
        
        return min(1.0, score)
    
    async def _remove_duplicates(self, insights: List[AlphaInsight]) -> List[AlphaInsight]:
        """移除重複洞察"""
        unique_insights = []
        seen_signatures = set()
        
        for insight in insights:
            # 創建洞察簽名
            signature = f"{insight.stock_code}_{insight.insight_type.value}_{insight.title[:20]}"
            
            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_insights.append(insight)
        
        return unique_insights
    
    async def _apply_personalization(self, insights: List[AlphaInsight],
                                   request: InsightGenerationRequest) -> List[AlphaInsight]:
        """應用個人化推薦"""
        if not request.user_preferences:
            return insights
        
        # 為每個洞察計算個人化分數
        for insight in insights:
            personalization_score = await self._calculate_personalization_score_single(
                insight, request)
            insight.supporting_data['personalization_score'] = personalization_score
        
        # 根據個人化分數排序
        insights.sort(key=lambda x: x.supporting_data.get('personalization_score', 0.5), 
                     reverse=True)
        
        return insights
    
    async def _calculate_personalization_score_single(self, insight: AlphaInsight,
                                                    request: InsightGenerationRequest) -> float:
        """計算單個洞察的個人化分數"""
        score = 0.5  # 基礎分數
        
        preferences = request.user_preferences
        
        # 投資風格匹配
        if 'investment_style' in preferences:
            style_match = self._match_investment_style(insight, preferences['investment_style'])
            score += style_match * self.personalization_weights['investment_style_match']
        
        # 風險承受度匹配
        if 'risk_tolerance' in preferences:
            risk_match = self._match_risk_tolerance(insight, preferences['risk_tolerance'])
            score += risk_match * self.personalization_weights['risk_tolerance_match']
        
        # 板塊偏好
        if 'preferred_sectors' in preferences and insight.sector:
            sector_match = 1.0 if insight.sector in preferences['preferred_sectors'] else 0.3
            score += sector_match * self.personalization_weights['sector_preference']
        
        return min(1.0, score)
    
    def _match_investment_style(self, insight: AlphaInsight, investment_style: str) -> float:
        """匹配投資風格"""
        style_matches = {
            'growth': {
                AlphaInsightType.FUNDAMENTAL_ANALYSIS: 0.8,
                AlphaInsightType.EARNINGS_FORECAST: 0.9,
                AlphaInsightType.TECHNICAL_ANALYSIS: 0.6
            },
            'value': {
                AlphaInsightType.VALUATION_MODEL: 0.9,
                AlphaInsightType.FUNDAMENTAL_ANALYSIS: 0.8,
                AlphaInsightType.FINANCIAL_HEALTH: 0.7
            },
            'momentum': {
                AlphaInsightType.TECHNICAL_ANALYSIS: 0.9,
                AlphaInsightType.MARKET_MOMENTUM: 0.9,
                AlphaInsightType.NEWS_SENTIMENT: 0.7
            }
        }
        
        return style_matches.get(investment_style, {}).get(insight.insight_type, 0.5)
    
    def _match_risk_tolerance(self, insight: AlphaInsight, risk_tolerance: str) -> float:
        """匹配風險承受度"""
        if risk_tolerance == 'conservative':
            return 0.8 if insight.insight_type == AlphaInsightType.FINANCIAL_HEALTH else 0.5
        elif risk_tolerance == 'moderate':
            return 0.7
        elif risk_tolerance == 'aggressive':
            return 0.8 if insight.insight_type == AlphaInsightType.TECHNICAL_ANALYSIS else 0.6
        
        return 0.5
    
    async def _finalize_insights(self, insights: List[AlphaInsight],
                               request: InsightGenerationRequest) -> List[AlphaInsight]:
        """最終篩選和排序洞察"""
        # 按優先級和品質分數排序
        insights.sort(key=lambda x: (
            {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}[x.priority.value],
            x.quality_score,
            x.confidence_score
        ), reverse=True)
        
        # 限制數量
        max_results = request.max_results or self.config.max_insights_per_request
        return insights[:max_results]
    
    async def _update_cache(self, request: InsightGenerationRequest, 
                          insights: List[AlphaInsight]):
        """更新緩存"""
        cache_key = f"{request.user_id}_{hash(str(request.dict()))}"
        self.insight_cache[cache_key] = insights
        self.cache_expiry[cache_key] = datetime.now() + timedelta(
            hours=self.config.freshness_hours)
    
    def _get_models_used(self) -> List[str]:
        """獲取使用的模型列表"""
        models = []
        if self.news_model:
            models.append('taiwan_news_model')
        if self.financial_model:
            models.append('financial_report_model')
        if self.technical_model:
            models.append('technical_analysis_model')
        return models
    
    def _get_data_sources_used(self) -> List[str]:
        """獲取使用的數據源列表"""
        return [
            'financial_reports', 'news_data', 'price_data', 
            'market_data', 'sentiment_data', 'valuation_models'
        ]
    
    def _calculate_average_confidence(self, insights: List[AlphaInsight]) -> float:
        """計算平均置信度"""
        if not insights:
            return 0.0
        return sum(insight.confidence_score for insight in insights) / len(insights)
    
    def _calculate_average_quality(self, insights: List[AlphaInsight]) -> float:
        """計算平均品質分數"""
        if not insights:
            return 0.0
        return sum(insight.quality_score for insight in insights) / len(insights)
    
    def _calculate_coverage_completeness(self, insights: List[AlphaInsight],
                                       request: InsightGenerationRequest) -> float:
        """計算覆蓋完整性"""
        if not request.stock_codes:
            return 1.0
        
        covered_stocks = set(insight.stock_code for insight in insights 
                           if insight.stock_code)
        requested_stocks = set(request.stock_codes)
        
        return len(covered_stocks & requested_stocks) / len(requested_stocks)
    
    def _calculate_personalization_score(self, insights: List[AlphaInsight],
                                       request: InsightGenerationRequest) -> float:
        """計算個人化分數"""
        if not insights or not self.config.enable_personalization:
            return 0.0
        
        scores = [insight.supporting_data.get('personalization_score', 0.5) 
                 for insight in insights]
        return sum(scores) / len(scores)
    
    def _calculate_relevance_score(self, insights: List[AlphaInsight],
                                 request: InsightGenerationRequest) -> float:
        """計算相關性分數"""
        # 基於洞察類型匹配度計算相關性
        if not insights:
            return 0.0
        
        type_matches = 0
        if request.insight_types:
            for insight in insights:
                if insight.insight_type in request.insight_types:
                    type_matches += 1
            return type_matches / len(insights)
        
        return 0.8  # 預設相關性分數
    
    def _update_processing_stats(self, processing_time: float, insights: List[AlphaInsight]):
        """更新處理統計"""
        # 更新平均處理時間
        current_avg = self.generation_stats['average_processing_time_ms']
        total_requests = self.generation_stats['total_requests']
        
        new_avg = ((current_avg * (total_requests - 1)) + processing_time) / total_requests
        self.generation_stats['average_processing_time_ms'] = new_avg
        
        # 更新洞察類型分佈
        for insight in insights:
            insight_type = insight.insight_type.value
            self.generation_stats['insight_type_distribution'][insight_type] = (
                self.generation_stats['insight_type_distribution'].get(insight_type, 0) + 1
            )
        
        # 更新品質分數分佈
        for insight in insights:
            self.generation_stats['quality_score_distribution'].append(
                insight.quality_score)
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """獲取引擎統計信息"""
        return {
            'engine_config': self.config.dict(),
            'models_loaded': self.models_loaded,
            'generation_statistics': self.generation_stats,
            'cache_size': len(self.insight_cache),
            'available_generators': list(self.insight_generators.keys())
        }