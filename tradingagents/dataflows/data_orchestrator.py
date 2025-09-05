#!/usr/bin/env python3
"""
TradingAgents 統一數據編排器
協調 FinMind 和 FinnHub 數據源，提供統一的數據訪問接口
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import re
import time
import hashlib
import json
from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation

from ..default_config import DEFAULT_CONFIG
from ..utils.user_context import UserContext
from ..utils.cache_manager import CacheManager, CacheKey, CacheSource, CacheStatus
from ..services.upgrade_conversion_service import UpgradeConversionService, UpgradePrompt
from ..services.international_market_service import InternationalMarketService
from .finmind_api import FinMindAPI, create_finmind_client
# from .finnhub_api import (
#     FinnHubAPIClient
# )

# 設置日誌
logger = logging.getLogger(__name__)

class DataSource(Enum):
    """數據源枚舉"""
    FINMIND = "finmind"
    FINNHUB = "finnhub"
    AUTO = "auto"

class SymbolType(Enum):
    """股票代號類型枚舉"""
    TAIWAN_STOCK = "taiwan_stock"      # 台股：4位數字
    US_STOCK = "us_stock"              # 美股：字母組合
    HK_STOCK = "hk_stock"              # 港股：數字.HK
    INTERNATIONAL = "international"     # 其他國際股票
    UNKNOWN = "unknown"

class DataType(Enum):
    """數據類型枚舉"""
    STOCK_PRICE = "stock_price"
    COMPANY_PROFILE = "company_profile"
    COMPANY_NEWS = "company_news"
    FINANCIAL_DATA = "financial_data"
    EARNINGS = "earnings"
    DIVIDENDS = "dividends"
    MARKET_INDEX = "market_index"

class RoutingPriority(Enum):
    """路由優先級枚舉"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    DISABLED = "disabled"

class HealthStatus(Enum):
    """健康狀態枚舉"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class DataQuality(Enum):
    """數據質量枚舉"""
    HIGH = "high"        # 高質量：完整、準確、及時
    MEDIUM = "medium"    # 中等質量：基本完整，可能有小問題
    LOW = "low"          # 低質量：不完整或有明顯問題
    INVALID = "invalid"  # 無效：數據格式錯誤或無法使用

class NormalizationStatus(Enum):
    """標準化狀態枚舉"""
    SUCCESS = "success"           # 成功標準化
    PARTIAL = "partial"           # 部分標準化
    FAILED = "failed"             # 標準化失敗
    SKIPPED = "skipped"           # 跳過標準化

@dataclass
class SymbolInfo:
    """符號信息"""
    symbol: str
    symbol_type: SymbolType
    market: str
    currency: str
    exchange: str
    normalized_symbol: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'symbol_type': self.symbol_type.value,
            'market': self.market,
            'currency': self.currency,
            'exchange': self.exchange,
            'normalized_symbol': self.normalized_symbol
        }

@dataclass
class RoutingRule:
    """路由規則"""
    symbol_type: SymbolType
    data_type: DataType
    primary_source: DataSource
    fallback_sources: List[DataSource]
    priority: RoutingPriority
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    def matches(self, symbol_type: SymbolType, data_type: DataType) -> bool:
        """檢查規則是否匹配"""
        return self.symbol_type == symbol_type and self.data_type == data_type

@dataclass
class DataSourceHealth:
    """數據源健康狀態"""
    source: DataSource
    status: HealthStatus
    last_check: datetime
    response_time: float
    error_count: int
    success_rate: float
    consecutive_failures: int
    last_error: Optional[str] = None
    
    def is_available(self) -> bool:
        """檢查數據源是否可用"""
        return self.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'status': self.status.value,
            'last_check': self.last_check.isoformat(),
            'response_time': self.response_time,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'consecutive_failures': self.consecutive_failures,
            'last_error': self.last_error
        }

@dataclass
class RoutingMetrics:
    """路由指標"""
    source: DataSource
    symbol_type: SymbolType
    data_type: DataType
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_response_time: float = 0.0
    last_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        return (self.success_count / self.request_count * 100) if self.request_count > 0 else 0.0
    
    @property
    def average_response_time(self) -> float:
        return (self.total_response_time / self.request_count) if self.request_count > 0 else 0.0
    
    def update_success(self, response_time: float):
        """更新成功指標"""
        self.request_count += 1
        self.success_count += 1
        self.total_response_time += response_time
        self.last_used = datetime.now()
    
    def update_error(self, response_time: float):
        """更新錯誤指標"""
        self.request_count += 1
        self.error_count += 1
        self.total_response_time += response_time
        self.last_used = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'symbol_type': self.symbol_type.value,
            'data_type': self.data_type.value,
            'request_count': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'average_response_time': self.average_response_time,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

@dataclass
class DataSourceMetadata:
    """數據源元數據"""
    source: DataSource
    symbol: str
    data_type: DataType
    timestamp: datetime
    version: str
    checksum: str
    quality_score: float
    completeness: float
    freshness_score: float
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source': self.source.value,
            'symbol': self.symbol,
            'data_type': self.data_type.value,
            'timestamp': self.timestamp.isoformat(),
            'version': self.version,
            'checksum': self.checksum,
            'quality_score': self.quality_score,
            'completeness': self.completeness,
            'freshness_score': self.freshness_score,
            'additional_info': self.additional_info
        }

@dataclass
class DataQualityReport:
    """數據質量報告"""
    symbol: str
    data_type: DataType
    source: DataSource
    quality: DataQuality
    quality_score: float
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    completeness: float = 0.0
    accuracy: float = 0.0
    timeliness: float = 0.0
    consistency: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'data_type': self.data_type.value,
            'source': self.source.value,
            'quality': self.quality.value,
            'quality_score': self.quality_score,
            'issues': self.issues,
            'warnings': self.warnings,
            'completeness': self.completeness,
            'accuracy': self.accuracy,
            'timeliness': self.timeliness,
            'consistency': self.consistency,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class NormalizedData:
    """標準化數據"""
    symbol: str
    data_type: DataType
    data: Dict[str, Any]
    metadata: DataSourceMetadata
    quality_report: DataQualityReport
    normalization_status: NormalizationStatus
    normalization_timestamp: datetime = field(default_factory=datetime.now)
    cross_source_conflicts: List[str] = field(default_factory=list)
    reconciliation_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'data_type': self.data_type.value,
            'data': self.data,
            'metadata': self.metadata.to_dict(),
            'quality_report': self.quality_report.to_dict(),
            'normalization_status': self.normalization_status.value,
            'normalization_timestamp': self.normalization_timestamp.isoformat(),
            'cross_source_conflicts': self.cross_source_conflicts,
            'reconciliation_notes': self.reconciliation_notes
        }

@dataclass
class CrossSourceComparison:
    """跨數據源比較結果"""
    symbol: str
    data_type: DataType
    primary_source: DataSource
    secondary_sources: List[DataSource]
    consistency_score: float
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'data_type': self.data_type.value,
            'primary_source': self.primary_source.value,
            'secondary_sources': [s.value for s in self.secondary_sources],
            'consistency_score': self.consistency_score,
            'conflicts': self.conflicts,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat()
        }

@dataclass
class DataRequest:
    """統一數據請求"""
    symbol: str
    data_type: DataType
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    preferred_source: DataSource = DataSource.AUTO
    user_context: Optional[UserContext] = None
    
    def __post_init__(self):
        """初始化後處理"""
        # 標準化股票代號
        self.symbol = self.symbol.upper().strip()

@dataclass
class DataResponse:
    """統一數據響應"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    source: Optional[DataSource] = None
    symbol: str = ""
    data_type: Optional[DataType] = None
    timestamp: datetime = field(default_factory=datetime.now)
    response_time: Optional[float] = None
    cached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    upgrade_prompt: Optional[UpgradePrompt] = None  # 升級提示
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'source': self.source.value if self.source else None,
            'symbol': self.symbol,
            'data_type': self.data_type.value if self.data_type else None,
            'timestamp': self.timestamp.isoformat(),
            'response_time': self.response_time,
            'cached': self.cached,
            'metadata': self.metadata
        }
        
        if self.upgrade_prompt:
            result['upgrade_prompt'] = self.upgrade_prompt.to_dict()
        
        return result

class DataOrchestrator:
    """統一數據編排器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化數據編排器
        
        Args:
            config: 配置字典
        """
        self.config = config or DEFAULT_CONFIG
        
        # 初始化數據源客戶端
        self.finmind_client = None
        self.finnhub_client = None
        
        # 統計信息
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.source_usage = {
            DataSource.FINMIND: 0,
            DataSource.FINNHUB: 0
        }
        
        # 智能路由系統
        self.routing_rules = self._initialize_routing_rules()
        self.routing_metrics = defaultdict(lambda: defaultdict(lambda: defaultdict(RoutingMetrics)))
        self.symbol_cache = {}  # 符號信息緩存
        
        # 數據源健康監控
        self.source_health = {
            DataSource.FINMIND: DataSourceHealth(
                source=DataSource.FINMIND,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now(),
                response_time=0.0,
                error_count=0,
                success_rate=0.0,
                consecutive_failures=0
            ),
            DataSource.FINNHUB: DataSourceHealth(
                source=DataSource.FINNHUB,
                status=HealthStatus.UNKNOWN,
                last_check=datetime.now(),
                response_time=0.0,
                error_count=0,
                success_rate=0.0,
                consecutive_failures=0
            )
        }
        
        # 性能監控
        self.response_times = {
            DataSource.FINMIND: deque(maxlen=100),
            DataSource.FINNHUB: deque(maxlen=100)
        }
        
        # 故障轉移配置
        self.max_consecutive_failures = 3
        self.health_check_interval = 300  # 5分鐘
        self.last_health_check = datetime.now()
        
        # 數據標準化和質量控制
        self.data_quality_thresholds = {
            'completeness_min': 0.8,
            'accuracy_min': 0.9,
            'timeliness_max_age': 3600,  # 1小時
            'consistency_min': 0.85
        }
        
        self.normalization_cache = {}  # 標準化結果緩存
        self.quality_reports = defaultdict(list)  # 質量報告歷史
        self.cross_source_comparisons = {}  # 跨數據源比較結果
        self.metadata_store = {}  # 元數據存儲
        
        # 初始化緩存管理器
        self.cache_manager = CacheManager(config=self.config)
        
        # 初始化升級轉換服務
        self.upgrade_service = UpgradeConversionService(config=self.config)
        
        # 初始化國際市場服務
        self.international_market_service = InternationalMarketService(config=self.config)
        
        logger.info("數據編排器初始化完成")
    
    def _initialize_routing_rules(self) -> List[RoutingRule]:
        """初始化路由規則"""
        rules = []
        
        # 台股路由規則
        rules.append(RoutingRule(
            symbol_type=SymbolType.TAIWAN_STOCK,
            data_type=DataType.STOCK_PRICE,
            primary_source=DataSource.FINMIND,
            fallback_sources=[DataSource.FINNHUB],
            priority=RoutingPriority.HIGH
        ))
        
        rules.append(RoutingRule(
            symbol_type=SymbolType.TAIWAN_STOCK,
            data_type=DataType.FINANCIAL_DATA,
            primary_source=DataSource.FINMIND,
            fallback_sources=[],
            priority=RoutingPriority.HIGH
        ))
        
        # 美股路由規則
        rules.append(RoutingRule(
            symbol_type=SymbolType.US_STOCK,
            data_type=DataType.STOCK_PRICE,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.HIGH
        ))
        
        rules.append(RoutingRule(
            symbol_type=SymbolType.US_STOCK,
            data_type=DataType.COMPANY_PROFILE,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.HIGH
        ))
        
        rules.append(RoutingRule(
            symbol_type=SymbolType.US_STOCK,
            data_type=DataType.COMPANY_NEWS,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.MEDIUM
        ))
        
        rules.append(RoutingRule(
            symbol_type=SymbolType.US_STOCK,
            data_type=DataType.FINANCIAL_DATA,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.HIGH
        ))
        
        # 港股路由規則
        rules.append(RoutingRule(
            symbol_type=SymbolType.HK_STOCK,
            data_type=DataType.STOCK_PRICE,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.HIGH
        ))
        
        rules.append(RoutingRule(
            symbol_type=SymbolType.HK_STOCK,
            data_type=DataType.COMPANY_PROFILE,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.MEDIUM
        ))
        
        # 國際股票路由規則
        rules.append(RoutingRule(
            symbol_type=SymbolType.INTERNATIONAL,
            data_type=DataType.STOCK_PRICE,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.MEDIUM
        ))
        
        rules.append(RoutingRule(
            symbol_type=SymbolType.INTERNATIONAL,
            data_type=DataType.COMPANY_PROFILE,
            primary_source=DataSource.FINNHUB,
            fallback_sources=[],
            priority=RoutingPriority.MEDIUM
        ))
        
        return rules
    
    async def initialize(self):
        """異步初始化數據源客戶端"""
        try:
            # 初始化 FinMind 客戶端
            finmind_config = self.config.get('finmind', {})
            self.finmind_client = create_finmind_client(finmind_config)
            logger.info("FinMind 客戶端初始化完成")
            
            # 初始化 FinnHub 客戶端 (臨時禁用)
            # finnhub_config = self.config.get('finnhub', {})
            # self.finnhub_client = create_finnhub_client(finnhub_config)
            self.finnhub_client = None
            logger.info("FinnHub 客戶端初始化跳過 (臨時禁用)")
            
            # 初始化緩存管理器
            await self.cache_manager.initialize()
            logger.info("緩存管理器初始化完成")
            
            # 執行健康檢查
            await self._perform_health_checks()
            
        except Exception as e:
            logger.error(f"數據編排器初始化失敗: {e}")
            raise
    
    # ==================== 統一數據請求接口 ====================
    
    async def get_stock_data(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_context: Optional[UserContext] = None,
        preferred_source: DataSource = DataSource.AUTO
    ) -> DataResponse:
        """
        獲取股票價格數據
        
        Args:
            symbol: 股票代號
            start_date: 開始日期
            end_date: 結束日期
            user_context: 用戶上下文
            preferred_source: 首選數據源
            
        Returns:
            統一數據響應
        """
        request = DataRequest(
            symbol=symbol,
            data_type=DataType.STOCK_PRICE,
            start_date=start_date,
            end_date=end_date,
            preferred_source=preferred_source,
            user_context=user_context
        )
        
        return await self._execute_request(request)
    
    async def get_company_profile(
        self,
        symbol: str,
        user_context: Optional[UserContext] = None,
        preferred_source: DataSource = DataSource.AUTO
    ) -> DataResponse:
        """
        獲取公司資料
        
        Args:
            symbol: 股票代號
            user_context: 用戶上下文
            preferred_source: 首選數據源
            
        Returns:
            統一數據響應
        """
        request = DataRequest(
            symbol=symbol,
            data_type=DataType.COMPANY_PROFILE,
            preferred_source=preferred_source,
            user_context=user_context
        )
        
        return await self._execute_request(request)
    
    async def get_company_news(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_context: Optional[UserContext] = None,
        preferred_source: DataSource = DataSource.AUTO
    ) -> DataResponse:
        """
        獲取公司新聞
        
        Args:
            symbol: 股票代號
            start_date: 開始日期
            end_date: 結束日期
            user_context: 用戶上下文
            preferred_source: 首選數據源
            
        Returns:
            統一數據響應
        """
        request = DataRequest(
            symbol=symbol,
            data_type=DataType.COMPANY_NEWS,
            start_date=start_date,
            end_date=end_date,
            preferred_source=preferred_source,
            user_context=user_context
        )
        
        return await self._execute_request(request)
    
    async def get_financial_data(
        self,
        symbol: str,
        statement_type: str = "annual",
        user_context: Optional[UserContext] = None,
        preferred_source: DataSource = DataSource.AUTO
    ) -> DataResponse:
        """
        獲取財務數據
        
        Args:
            symbol: 股票代號
            statement_type: 報表類型
            user_context: 用戶上下文
            preferred_source: 首選數據源
            
        Returns:
            統一數據響應
        """
        request = DataRequest(
            symbol=symbol,
            data_type=DataType.FINANCIAL_DATA,
            params={'statement_type': statement_type},
            preferred_source=preferred_source,
            user_context=user_context
        )
        
        return await self._execute_request(request)
    
    # ==================== 批量數據請求接口 ====================
    
    async def batch_get_stock_data(
        self,
        symbols: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_context: Optional[UserContext] = None,
        max_concurrent: int = 5
    ) -> Dict[str, DataResponse]:
        """
        批量獲取股票數據
        
        Args:
            symbols: 股票代號列表
            start_date: 開始日期
            end_date: 結束日期
            user_context: 用戶上下文
            max_concurrent: 最大並發數
            
        Returns:
            股票代號到響應的映射
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def get_single_stock(symbol: str) -> Tuple[str, DataResponse]:
            async with semaphore:
                response = await self.get_stock_data(symbol, start_date, end_date, user_context)
                return symbol, response
        
        tasks = [get_single_stock(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        stock_data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量獲取股票數據失敗: {result}")
                continue
            
            symbol, response = result
            stock_data[symbol] = response
        
        return stock_data
    
    async def batch_get_company_profiles(
        self,
        symbols: List[str],
        user_context: Optional[UserContext] = None,
        max_concurrent: int = 5
    ) -> Dict[str, DataResponse]:
        """
        批量獲取公司資料
        
        Args:
            symbols: 股票代號列表
            user_context: 用戶上下文
            max_concurrent: 最大並發數
            
        Returns:
            股票代號到響應的映射
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def get_single_profile(symbol: str) -> Tuple[str, DataResponse]:
            async with semaphore:
                response = await self.get_company_profile(symbol, user_context)
                return symbol, response
        
        tasks = [get_single_profile(symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        profile_data = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"批量獲取公司資料失敗: {result}")
                continue
            
            symbol, response = result
            profile_data[symbol] = response
        
        return profile_data
    
    # ==================== 核心請求執行邏輯 ====================
    
    async def _execute_request(self, request: DataRequest) -> DataResponse:
        """
        執行統一數據請求
        
        Args:
            request: 數據請求
            
        Returns:
            統一數據響應
        """
        start_time = datetime.now()
        self.request_count += 1
        
        try:
            # 1. 檢查國際數據訪問權限和升級轉換
            upgrade_prompt = None
            if request.user_context:
                can_access, upgrade_prompt = await self.upgrade_service.check_international_data_access(
                    request.user_context, request.symbol
                )
                
                if not can_access and upgrade_prompt:
                    # 返回帶有升級提示的響應
                    return DataResponse(
                        success=False,
                        error="需要升級會員以訪問國際數據",
                        symbol=request.symbol,
                        data_type=request.data_type,
                        response_time=(datetime.now() - start_time).total_seconds(),
                        upgrade_prompt=upgrade_prompt
                    )
            
            # 2. 符號分析和數據源路由
            symbol_info = self._analyze_symbol(request.symbol)
            data_source = self._route_data_source(request, symbol_info)
            
            logger.debug(f"請求路由: {request.symbol} -> {symbol_info.symbol_type.value} -> {data_source.value}")
            
            # 3. 檢查緩存
            cache_key = self._create_cache_key(request, data_source)
            cached_response = await self._get_cached_response(cache_key)
            
            if cached_response:
                logger.debug(f"緩存命中: {request.symbol} ({data_source.value})")
                cached_response.response_time = (datetime.now() - start_time).total_seconds()
                cached_response.from_cache = True
                return cached_response
            
            # 4. 執行數據請求
            response = await self._execute_source_request(request, data_source)
            
            # 5. 響應標準化
            standardized_response = self._standardize_response(response, request, data_source)
            
            # 6. 緩存成功的響應
            if standardized_response.success:
                await self._cache_response(cache_key, standardized_response)
            
            # 7. 更新統計信息和健康狀態
            response_time = (datetime.now() - start_time).total_seconds()
            
            if standardized_response.success:
                self.success_count += 1
                self._update_source_health(data_source, True, response_time)
                self._update_routing_metrics(data_source, symbol_info.symbol_type, request.data_type, True, response_time)
            else:
                self.error_count += 1
                self._update_source_health(data_source, False, response_time)
                self._update_routing_metrics(data_source, symbol_info.symbol_type, request.data_type, False, response_time)
                
                # 如果主要數據源失敗，嘗試故障轉移
                fallback_response = await self._try_fallback(request, data_source, symbol_info)
                if fallback_response and fallback_response.success:
                    standardized_response = fallback_response
                    self.success_count += 1
                    self.error_count -= 1
            
            self.source_usage[data_source] += 1
            
            # 5. 設置響應時間
            standardized_response.response_time = response_time
            
            # 6. 定期健康檢查
            await self._periodic_health_check()
            
            return standardized_response
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"請求執行失敗: {e}")
            
            response_time = (datetime.now() - start_time).total_seconds()
            return DataResponse(
                success=False,
                error=str(e),
                symbol=request.symbol,
                data_type=request.data_type,
                response_time=response_time
            )
    
    # ==================== 符號分類和路由邏輯 ====================
    
    def _analyze_symbol(self, symbol: str) -> SymbolInfo:
        """
        分析股票代號，返回詳細信息
        
        Args:
            symbol: 股票代號
            
        Returns:
            符號信息
        """
        # 檢查緩存
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]
        
        original_symbol = symbol
        symbol = symbol.upper().strip()
        
        # 台股分析
        if re.match(r'^\d{4}$', symbol):
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.TAIWAN_STOCK,
                market="TW",
                currency="TWD",
                exchange="TPE",
                normalized_symbol=symbol
            )
        elif re.match(r'^\d{4}\.TW$', symbol):
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.TAIWAN_STOCK,
                market="TW",
                currency="TWD",
                exchange="TPE",
                normalized_symbol=symbol.replace('.TW', '')
            )
        elif re.match(r'^\d{4}\.TWO$', symbol):
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.TAIWAN_STOCK,
                market="TW",
                currency="TWD",
                exchange="TWO",
                normalized_symbol=symbol.replace('.TWO', '')
            )
        
        # 港股分析
        elif re.match(r'^\d+\.HK$', symbol):
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.HK_STOCK,
                market="HK",
                currency="HKD",
                exchange="HKEX",
                normalized_symbol=symbol
            )
        
        # 美股分析
        elif re.match(r'^[A-Z]{1,5}$', symbol) and '.' not in symbol:
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.US_STOCK,
                market="US",
                currency="USD",
                exchange="NASDAQ",  # 默認，實際可能是 NYSE 或其他
                normalized_symbol=symbol
            )
        
        # 日股分析
        elif re.match(r'^\d+\.T$', symbol):
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.INTERNATIONAL,
                market="JP",
                currency="JPY",
                exchange="TSE",
                normalized_symbol=symbol
            )
        
        # 英股分析
        elif re.match(r'^[A-Z]+\.L$', symbol):
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.INTERNATIONAL,
                market="GB",
                currency="GBP",
                exchange="LSE",
                normalized_symbol=symbol
            )
        
        # 其他國際股票
        elif '.' in symbol:
            parts = symbol.split('.')
            suffix = parts[-1]
            
            # 根據後綴推斷市場
            market_map = {
                'AS': ('NL', 'EUR', 'AEX'),
                'PA': ('FR', 'EUR', 'EPA'),
                'DE': ('DE', 'EUR', 'XETRA'),
                'MI': ('IT', 'EUR', 'BIT'),
                'TO': ('CA', 'CAD', 'TSX'),
                'AX': ('AU', 'AUD', 'ASX'),
            }
            
            market_info = market_map.get(suffix, ('UNKNOWN', 'USD', 'UNKNOWN'))
            
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.INTERNATIONAL,
                market=market_info[0],
                currency=market_info[1],
                exchange=market_info[2],
                normalized_symbol=symbol
            )
        
        # 未知類型
        else:
            symbol_info = SymbolInfo(
                symbol=original_symbol,
                symbol_type=SymbolType.UNKNOWN,
                market="UNKNOWN",
                currency="USD",
                exchange="UNKNOWN",
                normalized_symbol=symbol
            )
        
        # 緩存結果
        self.symbol_cache[original_symbol] = symbol_info
        
        return symbol_info
    
    def _classify_symbol(self, symbol: str) -> SymbolType:
        """
        分類股票代號類型（向後兼容方法）
        
        Args:
            symbol: 股票代號
            
        Returns:
            符號類型
        """
        return self._analyze_symbol(symbol).symbol_type
    
    def _route_data_source(self, request: DataRequest, symbol_info: SymbolInfo) -> DataSource:
        """
        智能路由到合適的數據源
        
        Args:
            request: 數據請求
            symbol_info: 符號信息
            
        Returns:
            選擇的數據源
        """
        # 如果指定了首選數據源且不是 AUTO，檢查可用性後使用
        if request.preferred_source != DataSource.AUTO:
            if self._is_source_available(request.preferred_source):
                return request.preferred_source
            else:
                logger.warning(f"首選數據源 {request.preferred_source.value} 不可用，使用智能路由")
        
        # 查找匹配的路由規則
        matching_rule = self._find_routing_rule(symbol_info.symbol_type, request.data_type)
        
        if matching_rule:
            # 檢查主要數據源是否可用
            if self._is_source_available(matching_rule.primary_source):
                return matching_rule.primary_source
            
            # 嘗試故障轉移數據源
            for fallback_source in matching_rule.fallback_sources:
                if self._is_source_available(fallback_source):
                    logger.info(f"主數據源 {matching_rule.primary_source.value} 不可用，使用故障轉移: {fallback_source.value}")
                    return fallback_source
        
        # 如果沒有匹配的規則或所有數據源都不可用，使用默認邏輯
        return self._get_default_data_source(symbol_info.symbol_type, request.data_type)
    
    def _find_routing_rule(self, symbol_type: SymbolType, data_type: DataType) -> Optional[RoutingRule]:
        """
        查找匹配的路由規則
        
        Args:
            symbol_type: 符號類型
            data_type: 數據類型
            
        Returns:
            匹配的路由規則或 None
        """
        for rule in self.routing_rules:
            if rule.matches(symbol_type, data_type) and rule.priority != RoutingPriority.DISABLED:
                return rule
        return None
    
    def _is_source_available(self, source: DataSource) -> bool:
        """
        檢查數據源是否可用
        
        Args:
            source: 數據源
            
        Returns:
            是否可用
        """
        health = self.source_health.get(source)
        if not health:
            return False
        
        # 如果連續失敗次數超過閾值，認為不可用
        if health.consecutive_failures >= self.max_consecutive_failures:
            return False
        
        return health.is_available()
    
    def _get_default_data_source(self, symbol_type: SymbolType, data_type: DataType) -> DataSource:
        """
        獲取默認數據源（當沒有匹配規則時使用）
        
        Args:
            symbol_type: 符號類型
            data_type: 數據類型
            
        Returns:
            默認數據源
        """
        # 根據符號類型和數據類型進行默認路由
        if symbol_type == SymbolType.TAIWAN_STOCK:
            return DataSource.FINMIND
        elif symbol_type in [SymbolType.US_STOCK, SymbolType.HK_STOCK, SymbolType.INTERNATIONAL]:
            return DataSource.FINNHUB
        else:
            # 未知類型，根據數據類型決定
            if data_type in [DataType.STOCK_PRICE, DataType.FINANCIAL_DATA]:
                return DataSource.FINNHUB
            else:
                return DataSource.FINMIND
    
    # ==================== 數據源請求執行 ====================
    
    async def _execute_source_request(self, request: DataRequest, source: DataSource) -> Any:
        """
        執行特定數據源的請求
        
        Args:
            request: 數據請求
            source: 數據源
            
        Returns:
            原始響應數據
        """
        if source == DataSource.FINMIND:
            return await self._execute_finmind_request(request)
        elif source == DataSource.FINNHUB:
            return await self._execute_finnhub_request(request)
        else:
            raise ValueError(f"不支援的數據源: {source}")
    
    async def _execute_finmind_request(self, request: DataRequest) -> Any:
        """執行 FinMind 請求"""
        if not self.finmind_client:
            raise RuntimeError("FinMind 客戶端未初始化")
        
        try:
            if request.data_type == DataType.STOCK_PRICE:
                # 獲取股價數據
                return await self.finmind_client.get_stock_price(
                    stock_id=request.symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    user_context=request.user_context
                )
            
            elif request.data_type == DataType.FINANCIAL_DATA:
                # 獲取財務數據
                return await self.finmind_client.get_financial_statement(
                    stock_id=request.symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    user_context=request.user_context
                )
            
            else:
                raise ValueError(f"FinMind 不支援的數據類型: {request.data_type}")
                
        except Exception as e:
            logger.error(f"FinMind 請求失敗: {e}")
            raise
    
    async def _execute_finnhub_request(self, request: DataRequest):
        """執行 FinnHub 請求 (臨時禁用)"""
        logger.warning("FinnHub 請求被跳過 (服務臨時禁用)")
        return None
        
        try:
            if request.data_type == DataType.STOCK_PRICE:
                # 獲取股價數據
                if request.start_date and request.end_date:
                    # 歷史數據
                    return await self.finnhub_client.get_stock_candles(
                        symbol=request.symbol,
                        resolution="D",
                        from_date=request.start_date,
                        to_date=request.end_date,
                        user_context=request.user_context
                    )
                else:
                    # 實時報價
                    return await self.finnhub_client.get_quote(
                        symbol=request.symbol,
                        user_context=request.user_context
                    )
            
            elif request.data_type == DataType.COMPANY_PROFILE:
                # 獲取公司資料
                return await self.finnhub_client.get_company_profile(
                    symbol=request.symbol,
                    user_context=request.user_context
                )
            
            elif request.data_type == DataType.COMPANY_NEWS:
                # 獲取公司新聞
                return await self.finnhub_client.get_company_news(
                    symbol=request.symbol,
                    from_date=request.start_date,
                    to_date=request.end_date,
                    user_context=request.user_context
                )
            
            elif request.data_type == DataType.FINANCIAL_DATA:
                # 獲取財務數據
                statement_type = request.params.get('statement_type', 'annual')
                return await self.finnhub_client.get_financials(
                    symbol=request.symbol,
                    freq=statement_type,
                    user_context=request.user_context
                )
            
            else:
                raise ValueError(f"FinnHub 不支援的數據類型: {request.data_type}")
                
        except Exception as e:
            logger.error(f"FinnHub 請求失敗: {e}")
            raise
    
    # ==================== 跨數據源數據標準化 ====================
    
    def normalize_data(self, raw_data: Any, source: DataSource, symbol: str, data_type: DataType) -> NormalizedData:
        """
        標準化數據為統一格式
        
        Args:
            raw_data: 原始數據
            source: 數據源
            symbol: 股票代號
            data_type: 數據類型
            
        Returns:
            標準化數據
        """
        try:
            # 1. 生成元數據
            metadata = self._generate_metadata(raw_data, source, symbol, data_type)
            
            # 2. 數據質量評估
            quality_report = self._assess_data_quality(raw_data, source, symbol, data_type)
            
            # 3. 數據格式轉換
            normalized_data = self._convert_to_unified_format(raw_data, source, data_type)
            
            # 4. 數據驗證和清理
            validated_data = self._validate_and_clean_data(normalized_data, data_type)
            
            # 5. 創建標準化數據對象
            result = NormalizedData(
                symbol=symbol,
                data_type=data_type,
                data=validated_data,
                metadata=metadata,
                quality_report=quality_report,
                normalization_status=NormalizationStatus.SUCCESS
            )
            
            # 6. 緩存標準化結果
            cache_key = f"{source.value}:{symbol}:{data_type.value}"
            self.normalization_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"數據標準化失敗: {e}")
            
            # 創建失敗的標準化結果
            return NormalizedData(
                symbol=symbol,
                data_type=data_type,
                data={},
                metadata=DataSourceMetadata(
                    source=source,
                    symbol=symbol,
                    data_type=data_type,
                    timestamp=datetime.now(),
                    version="unknown",
                    checksum="",
                    quality_score=0.0,
                    completeness=0.0,
                    freshness_score=0.0
                ),
                quality_report=DataQualityReport(
                    symbol=symbol,
                    data_type=data_type,
                    source=source,
                    quality=DataQuality.INVALID,
                    quality_score=0.0,
                    issues=[f"標準化失敗: {str(e)}"]
                ),
                normalization_status=NormalizationStatus.FAILED
            )
    
    def _generate_metadata(self, raw_data: Any, source: DataSource, symbol: str, data_type: DataType) -> DataSourceMetadata:
        """
        生成數據源元數據
        
        Args:
            raw_data: 原始數據
            source: 數據源
            symbol: 股票代號
            data_type: 數據類型
            
        Returns:
            數據源元數據
        """
        # 計算數據校驗和 - 安全修復：使用SHA256替換MD5
        data_str = json.dumps(raw_data, sort_keys=True, default=str)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()
        
        # 評估數據完整性
        completeness = self._calculate_completeness(raw_data, data_type)
        
        # 評估數據新鮮度
        freshness_score = self._calculate_freshness(raw_data, data_type)
        
        # 計算整體質量分數
        quality_score = (completeness + freshness_score) / 2
        
        return DataSourceMetadata(
            source=source,
            symbol=symbol,
            data_type=data_type,
            timestamp=datetime.now(),
            version="1.0",
            checksum=checksum,
            quality_score=quality_score,
            completeness=completeness,
            freshness_score=freshness_score,
            additional_info={
                'data_size': len(data_str),
                'processing_time': datetime.now().isoformat()
            }
        )
    
    def _assess_data_quality(self, raw_data: Any, source: DataSource, symbol: str, data_type: DataType) -> DataQualityReport:
        """
        評估數據質量
        
        Args:
            raw_data: 原始數據
            source: 數據源
            symbol: 股票代號
            data_type: 數據類型
            
        Returns:
            數據質量報告
        """
        issues = []
        warnings = []
        
        # 評估完整性
        completeness = self._calculate_completeness(raw_data, data_type)
        if completeness < self.data_quality_thresholds['completeness_min']:
            issues.append(f"數據完整性不足: {completeness:.2f}")
        
        # 評估準確性
        accuracy = self._calculate_accuracy(raw_data, data_type)
        if accuracy < self.data_quality_thresholds['accuracy_min']:
            issues.append(f"數據準確性不足: {accuracy:.2f}")
        
        # 評估及時性
        timeliness = self._calculate_timeliness(raw_data, data_type)
        if timeliness < 0.8:
            warnings.append(f"數據可能不夠及時: {timeliness:.2f}")
        
        # 評估一致性
        consistency = self._calculate_consistency(raw_data, data_type)
        if consistency < self.data_quality_thresholds['consistency_min']:
            warnings.append(f"數據一致性問題: {consistency:.2f}")
        
        # 計算整體質量分數
        quality_score = (completeness + accuracy + timeliness + consistency) / 4
        
        # 確定質量等級
        if quality_score >= 0.9:
            quality = DataQuality.HIGH
        elif quality_score >= 0.7:
            quality = DataQuality.MEDIUM
        elif quality_score >= 0.5:
            quality = DataQuality.LOW
        else:
            quality = DataQuality.INVALID
        
        report = DataQualityReport(
            symbol=symbol,
            data_type=data_type,
            source=source,
            quality=quality,
            quality_score=quality_score,
            issues=issues,
            warnings=warnings,
            completeness=completeness,
            accuracy=accuracy,
            timeliness=timeliness,
            consistency=consistency
        )
        
        # 存儲質量報告
        self.quality_reports[f"{symbol}:{data_type.value}"].append(report)
        
        return report
    
    def _convert_to_unified_format(self, raw_data: Any, source: DataSource, data_type: DataType) -> Dict[str, Any]:
        """
        轉換為統一格式
        
        Args:
            raw_data: 原始數據
            source: 數據源
            data_type: 數據類型
            
        Returns:
            統一格式的數據
        """
        if source == DataSource.FINMIND:
            return self._convert_finmind_data(raw_data, data_type)
        elif source == DataSource.FINNHUB:
            return self._convert_finnhub_data(raw_data, data_type)
        else:
            return raw_data
    
    def _convert_finmind_data(self, raw_data: Any, data_type: DataType) -> Dict[str, Any]:
        """
        轉換 FinMind 數據為統一格式
        
        Args:
            raw_data: FinMind 原始數據
            data_type: 數據類型
            
        Returns:
            統一格式的數據
        """
        if data_type == DataType.STOCK_PRICE:
            # FinMind 股價數據標準化
            if hasattr(raw_data, 'data') and raw_data.data:
                data_list = raw_data.data if isinstance(raw_data.data, list) else [raw_data.data]
                
                normalized_prices = []
                for item in data_list:
                    normalized_item = {
                        'symbol': item.get('stock_id', ''),
                        'date': item.get('date', ''),
                        'open': self._safe_decimal(item.get('open')),
                        'high': self._safe_decimal(item.get('max')),
                        'low': self._safe_decimal(item.get('min')),
                        'close': self._safe_decimal(item.get('close')),
                        'volume': self._safe_int(item.get('Trading_Volume')),
                        'turnover': self._safe_decimal(item.get('Trading_money')),
                        'currency': 'TWD',
                        'market': 'TW',
                        'data_source': 'finmind'
                    }
                    normalized_prices.append(normalized_item)
                
                return {
                    'type': 'stock_price',
                    'data': normalized_prices,
                    'count': len(normalized_prices)
                }
        
        elif data_type == DataType.FINANCIAL_DATA:
            # FinMind 財務數據標準化
            if hasattr(raw_data, 'data') and raw_data.data:
                data_list = raw_data.data if isinstance(raw_data.data, list) else [raw_data.data]
                
                normalized_financials = []
                for item in data_list:
                    normalized_item = {
                        'symbol': item.get('stock_id', ''),
                        'date': item.get('date', ''),
                        'revenue': self._safe_decimal(item.get('revenue')),
                        'operating_income': self._safe_decimal(item.get('operating_income')),
                        'net_income': self._safe_decimal(item.get('net_income')),
                        'total_assets': self._safe_decimal(item.get('total_assets')),
                        'total_liabilities': self._safe_decimal(item.get('total_liabilities')),
                        'shareholders_equity': self._safe_decimal(item.get('shareholders_equity')),
                        'currency': 'TWD',
                        'unit': 'thousand_twd',
                        'data_source': 'finmind'
                    }
                    normalized_financials.append(normalized_item)
                
                return {
                    'type': 'financial_data',
                    'data': normalized_financials,
                    'count': len(normalized_financials)
                }
        
        # 默認返回原始數據
        return {'type': 'unknown', 'data': raw_data, 'data_source': 'finmind'}
    
    def _convert_finnhub_data(self, raw_data: Any, data_type: DataType) -> Dict[str, Any]:
        """
        轉換 FinnHub 數據為統一格式
        
        Args:
            raw_data: FinnHub 原始數據
            data_type: 數據類型
            
        Returns:
            統一格式的數據
        """
        if not hasattr(raw_data, 'data') or not raw_data.data:
            return {'type': 'unknown', 'data': {}, 'data_source': 'finnhub'}
        
        data = raw_data.data
        
        if data_type == DataType.STOCK_PRICE:
            # FinnHub 股價數據標準化
            if isinstance(data, dict):
                if 'c' in data and isinstance(data['c'], list):  # Candle 數據
                    candles = []
                    for i in range(len(data.get('c', []))):
                        candle = {
                            'timestamp': datetime.fromtimestamp(data['t'][i]) if i < len(data.get('t', [])) else None,
                            'open': self._safe_decimal(data['o'][i]) if i < len(data.get('o', [])) else None,
                            'high': self._safe_decimal(data['h'][i]) if i < len(data.get('h', [])) else None,
                            'low': self._safe_decimal(data['l'][i]) if i < len(data.get('l', [])) else None,
                            'close': self._safe_decimal(data['c'][i]) if i < len(data.get('c', [])) else None,
                            'volume': self._safe_int(data['v'][i]) if i < len(data.get('v', [])) else None,
                            'currency': 'USD',
                            'data_source': 'finnhub'
                        }
                        candles.append(candle)
                    
                    return {
                        'type': 'stock_candles',
                        'data': candles,
                        'count': len(candles)
                    }
                
                elif 'c' in data:  # Quote 數據
                    normalized_data = {
                        'current_price': self._safe_decimal(data.get('c')),
                        'change': self._safe_decimal(data.get('d')),
                        'change_percent': self._safe_decimal(data.get('dp')),
                        'high': self._safe_decimal(data.get('h')),
                        'low': self._safe_decimal(data.get('l')),
                        'open': self._safe_decimal(data.get('o')),
                        'previous_close': self._safe_decimal(data.get('pc')),
                        'timestamp': datetime.fromtimestamp(data.get('t', 0)) if data.get('t') and isinstance(data.get('t'), (int, float)) else None,
                        'currency': 'USD',
                        'data_source': 'finnhub'
                    }
                    
                    return {
                        'type': 'stock_quote',
                        'data': normalized_data
                    }
        
        elif data_type == DataType.COMPANY_PROFILE:
            # FinnHub 公司資料標準化
            if isinstance(data, dict):
                normalized_data = {
                    'symbol': data.get('ticker', ''),
                    'name': data.get('name', ''),
                    'description': data.get('description', ''),
                    'industry': data.get('finnhubIndustry', ''),
                    'sector': data.get('ggroup', ''),
                    'country': data.get('country', ''),
                    'currency': data.get('currency', 'USD'),
                    'market_cap': self._safe_decimal(data.get('marketCapitalization')),
                    'employees': self._safe_int(data.get('employeeTotal')),
                    'website': data.get('weburl', ''),
                    'logo': data.get('logo', ''),
                    'exchange': data.get('exchange', ''),
                    'ipo_date': data.get('ipo', ''),
                    'data_source': 'finnhub'
                }
                
                return {
                    'type': 'company_profile',
                    'data': normalized_data
                }
        
        elif data_type == DataType.COMPANY_NEWS:
            # FinnHub 新聞數據標準化
            if isinstance(data, list):
                normalized_news = []
                for news_item in data:
                    normalized_item = {
                        'id': str(news_item.get('id', '')),
                        'headline': news_item.get('headline', ''),
                        'summary': news_item.get('summary', ''),
                        'url': news_item.get('url', ''),
                        'source': news_item.get('source', ''),
                        'category': news_item.get('category', ''),
                        'datetime': datetime.fromtimestamp(news_item.get('datetime', 0)) if news_item.get('datetime') else None,
                        'image': news_item.get('image', ''),
                        'data_source': 'finnhub'
                    }
                    normalized_news.append(normalized_item)
                
                return {
                    'type': 'company_news',
                    'data': normalized_news,
                    'count': len(normalized_news)
                }
        
        # 默認返回原始數據
        return {'type': 'unknown', 'data': data, 'data_source': 'finnhub'}
    
    def _validate_and_clean_data(self, data: Dict[str, Any], data_type: DataType) -> Dict[str, Any]:
        """
        驗證和清理數據
        
        Args:
            data: 待驗證的數據
            data_type: 數據類型
            
        Returns:
            清理後的數據
        """
        cleaned_data = data.copy()
        
        if data_type == DataType.STOCK_PRICE:
            # 股價數據驗證
            if 'data' in cleaned_data:
                if isinstance(cleaned_data['data'], list):
                    # 清理價格數據列表
                    valid_items = []
                    for item in cleaned_data['data']:
                        if self._is_valid_price_data(item):
                            valid_items.append(item)
                    cleaned_data['data'] = valid_items
                    cleaned_data['count'] = len(valid_items)
                elif isinstance(cleaned_data['data'], dict):
                    # 清理單個價格數據
                    if not self._is_valid_price_data(cleaned_data['data']):
                        cleaned_data['data'] = {}
        
        elif data_type == DataType.COMPANY_PROFILE:
            # 公司資料驗證
            if 'data' in cleaned_data and isinstance(cleaned_data['data'], dict):
                profile_data = cleaned_data['data']
                
                # 驗證必需字段
                if not profile_data.get('symbol') or not profile_data.get('name'):
                    cleaned_data['data'] = {}
                else:
                    # 清理數值字段
                    if 'market_cap' in profile_data:
                        profile_data['market_cap'] = self._safe_decimal(profile_data['market_cap'])
                    if 'employees' in profile_data:
                        profile_data['employees'] = self._safe_int(profile_data['employees'])
        
        elif data_type == DataType.COMPANY_NEWS:
            # 新聞數據驗證
            if 'data' in cleaned_data and isinstance(cleaned_data['data'], list):
                valid_news = []
                for news_item in cleaned_data['data']:
                    if self._is_valid_news_data(news_item):
                        valid_news.append(news_item)
                cleaned_data['data'] = valid_news
                cleaned_data['count'] = len(valid_news)
        
        return cleaned_data
    
    def reconcile_cross_source_data(self, symbol: str, data_type: DataType, primary_data: NormalizedData, secondary_data_list: List[NormalizedData]) -> CrossSourceComparison:
        """
        跨數據源數據協調
        
        Args:
            symbol: 股票代號
            data_type: 數據類型
            primary_data: 主要數據源數據
            secondary_data_list: 次要數據源數據列表
            
        Returns:
            跨數據源比較結果
        """
        conflicts = []
        recommendations = []
        consistency_scores = []
        
        for secondary_data in secondary_data_list:
            # 比較數據一致性
            consistency_score, data_conflicts = self._compare_data_consistency(
                primary_data, secondary_data, data_type
            )
            
            consistency_scores.append(consistency_score)
            conflicts.extend(data_conflicts)
            
            # 生成建議
            if consistency_score < 0.8:
                recommendations.append(
                    f"數據源 {secondary_data.metadata.source.value} 與主數據源存在顯著差異 (一致性: {consistency_score:.2f})"
                )
        
        # 計算整體一致性分數
        overall_consistency = sum(consistency_scores) / len(consistency_scores) if consistency_scores else 1.0
        
        comparison = CrossSourceComparison(
            symbol=symbol,
            data_type=data_type,
            primary_source=primary_data.metadata.source,
            secondary_sources=[data.metadata.source for data in secondary_data_list],
            consistency_score=overall_consistency,
            conflicts=conflicts,
            recommendations=recommendations
        )
        
        # 存儲比較結果
        comparison_key = f"{symbol}:{data_type.value}"
        self.cross_source_comparisons[comparison_key] = comparison
        
        return comparison
    
    # ==================== 輔助方法 ====================
    
    def _calculate_completeness(self, raw_data: Any, data_type: DataType) -> float:
        """計算數據完整性分數"""
        if not raw_data:
            return 0.0
        
        if data_type == DataType.STOCK_PRICE:
            # 檢查股價數據的完整性
            if hasattr(raw_data, 'data') and raw_data.data:
                if isinstance(raw_data.data, list):
                    if not raw_data.data:
                        return 0.0
                    
                    # 檢查必需字段的完整性
                    required_fields = ['close', 'volume']
                    total_score = 0.0
                    
                    for item in raw_data.data:
                        item_score = 0.0
                        for field in required_fields:
                            if field in item and item[field] is not None:
                                item_score += 1.0
                        total_score += item_score / len(required_fields)
                    
                    return total_score / len(raw_data.data)
                elif isinstance(raw_data.data, dict):
                    # 單個數據項的完整性
                    required_fields = ['c', 'v']  # FinnHub 格式
                    score = 0.0
                    for field in required_fields:
                        if field in raw_data.data and raw_data.data[field] is not None:
                            score += 1.0
                    return score / len(required_fields)
        
        elif data_type == DataType.COMPANY_PROFILE:
            # 檢查公司資料的完整性
            if hasattr(raw_data, 'data') and isinstance(raw_data.data, dict):
                required_fields = ['name', 'industry', 'country']
                score = 0.0
                for field in required_fields:
                    if field in raw_data.data and raw_data.data[field]:
                        score += 1.0
                return score / len(required_fields)
        
        return 0.5  # 默認中等完整性
    
    def _calculate_accuracy(self, raw_data: Any, data_type: DataType) -> float:
        """計算數據準確性分數"""
        # 基本的數據格式和範圍檢查
        if not raw_data:
            return 0.0
        
        if data_type == DataType.STOCK_PRICE:
            if hasattr(raw_data, 'data') and raw_data.data:
                if isinstance(raw_data.data, dict) and 'c' in raw_data.data:
                    # 檢查價格是否在合理範圍內
                    price = raw_data.data.get('c')
                    if price and 0 < price < 1000000:  # 合理的價格範圍
                        return 0.9
                    else:
                        return 0.3
                elif isinstance(raw_data.data, list):
                    valid_count = 0
                    for item in raw_data.data:
                        close_price = item.get('close') or item.get('c')
                        if close_price and 0 < close_price < 1000000:
                            valid_count += 1
                    return valid_count / len(raw_data.data) if raw_data.data else 0.0
        
        return 0.8  # 默認較高準確性
    
    def _calculate_timeliness(self, raw_data: Any, data_type: DataType) -> float:
        """計算數據及時性分數"""
        now = datetime.now()
        max_age = self.data_quality_thresholds['timeliness_max_age']
        
        # 檢查數據時間戳
        data_time = None
        
        if hasattr(raw_data, 'data') and raw_data.data:
            if isinstance(raw_data.data, dict):
                # FinnHub 格式
                if 't' in raw_data.data:
                    data_time = datetime.fromtimestamp(raw_data.data['t'])
            elif isinstance(raw_data.data, list) and raw_data.data:
                # FinMind 格式
                latest_item = raw_data.data[-1]
                if 'date' in latest_item:
                    try:
                        data_time = datetime.strptime(latest_item['date'], '%Y-%m-%d')
                    except ValueError:
                        pass
        
        if data_time:
            age_seconds = (now - data_time).total_seconds()
            if age_seconds <= max_age:
                return 1.0
            elif age_seconds <= max_age * 2:
                return 0.7
            elif age_seconds <= max_age * 5:
                return 0.4
            else:
                return 0.1
        
        return 0.5  # 無法確定時間時的默認值
    
    def _calculate_consistency(self, raw_data: Any, data_type: DataType) -> float:
        """計算數據一致性分數"""
        if not raw_data or not hasattr(raw_data, 'data'):
            return 0.0
        
        if data_type == DataType.STOCK_PRICE:
            if isinstance(raw_data.data, list) and len(raw_data.data) > 1:
                # 檢查價格數據的一致性
                inconsistencies = 0
                total_checks = 0
                
                for i in range(1, len(raw_data.data)):
                    prev_item = raw_data.data[i-1]
                    curr_item = raw_data.data[i]
                    
                    # 檢查價格變化是否合理
                    prev_close = prev_item.get('close') or prev_item.get('c')
                    curr_open = curr_item.get('open') or curr_item.get('o')
                    
                    if prev_close and curr_open:
                        total_checks += 1
                        # 如果開盤價與前一日收盤價差異超過20%，認為不一致
                        if abs(curr_open - prev_close) / prev_close > 0.2:
                            inconsistencies += 1
                
                if total_checks > 0:
                    return 1.0 - (inconsistencies / total_checks)
        
        return 0.9  # 默認高一致性
    
    def _compare_data_consistency(self, primary_data: NormalizedData, secondary_data: NormalizedData, data_type: DataType) -> Tuple[float, List[Dict[str, Any]]]:
        """比較兩個數據源的一致性"""
        conflicts = []
        consistency_score = 1.0
        
        if data_type == DataType.STOCK_PRICE:
            # 比較股價數據
            primary_price = self._extract_price_from_normalized_data(primary_data.data)
            secondary_price = self._extract_price_from_normalized_data(secondary_data.data)
            
            if primary_price and secondary_price:
                price_diff = abs(primary_price - secondary_price) / primary_price
                if price_diff > 0.05:  # 5% 差異閾值
                    conflicts.append({
                        'field': 'price',
                        'primary_value': primary_price,
                        'secondary_value': secondary_price,
                        'difference_percent': price_diff * 100
                    })
                    consistency_score -= price_diff
        
        elif data_type == DataType.COMPANY_PROFILE:
            # 比較公司資料
            primary_profile = primary_data.data.get('data', {})
            secondary_profile = secondary_data.data.get('data', {})
            
            # 比較公司名稱
            if primary_profile.get('name') and secondary_profile.get('name'):
                if primary_profile['name'].lower() != secondary_profile['name'].lower():
                    conflicts.append({
                        'field': 'name',
                        'primary_value': primary_profile['name'],
                        'secondary_value': secondary_profile['name']
                    })
                    consistency_score -= 0.2
        
        return max(0.0, consistency_score), conflicts
    
    def _extract_price_from_normalized_data(self, data: Dict[str, Any]) -> Optional[float]:
        """從標準化數據中提取價格"""
        if data.get('type') == 'stock_quote':
            return data.get('data', {}).get('current_price')
        elif data.get('type') == 'stock_price' and data.get('data'):
            if isinstance(data['data'], list) and data['data']:
                return data['data'][-1].get('close')
        return None
    
    def _safe_decimal(self, value: Any) -> Optional[float]:
        """安全轉換為 Decimal 然後轉為 float"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return float(Decimal(str(value)))
        except (ValueError, TypeError, InvalidOperation):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """安全轉換為整數"""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.replace(',', '').strip()
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def _is_valid_price_data(self, item: Dict[str, Any]) -> bool:
        """驗證價格數據是否有效"""
        # 檢查必需字段
        price_fields = ['close', 'current_price', 'c']
        has_price = any(field in item and item[field] is not None for field in price_fields)
        
        if not has_price:
            return False
        
        # 檢查價格範圍
        for field in price_fields:
            if field in item and item[field] is not None:
                price = item[field]
                if not (0 < price < 1000000):  # 合理的價格範圍
                    return False
        
        return True
    
    def _is_valid_news_data(self, item: Dict[str, Any]) -> bool:
        """驗證新聞數據是否有效"""
        # 檢查必需字段
        return (item.get('headline') and 
                len(item['headline'].strip()) > 0 and
                item.get('datetime') is not None)
    
    def get_data_quality_summary(self) -> Dict[str, Any]:
        """獲取數據質量摘要"""
        summary = {
            'total_reports': 0,
            'quality_distribution': {
                'high': 0,
                'medium': 0,
                'low': 0,
                'invalid': 0
            },
            'average_scores': {
                'completeness': 0.0,
                'accuracy': 0.0,
                'timeliness': 0.0,
                'consistency': 0.0
            },
            'common_issues': defaultdict(int),
            'source_quality': {}
        }
        
        all_reports = []
        for reports_list in self.quality_reports.values():
            all_reports.extend(reports_list)
        
        if not all_reports:
            return summary
        
        summary['total_reports'] = len(all_reports)
        
        # 統計質量分佈
        for report in all_reports:
            summary['quality_distribution'][report.quality.value] += 1
            
            # 統計常見問題
            for issue in report.issues:
                summary['common_issues'][issue] += 1
        
        # 計算平均分數
        if all_reports:
            summary['average_scores']['completeness'] = sum(r.completeness for r in all_reports) / len(all_reports)
            summary['average_scores']['accuracy'] = sum(r.accuracy for r in all_reports) / len(all_reports)
            summary['average_scores']['timeliness'] = sum(r.timeliness for r in all_reports) / len(all_reports)
            summary['average_scores']['consistency'] = sum(r.consistency for r in all_reports) / len(all_reports)
        
        # 按數據源統計質量
        source_reports = defaultdict(list)
        for report in all_reports:
            source_reports[report.source.value].append(report)
        
        for source, reports in source_reports.items():
            summary['source_quality'][source] = {
                'count': len(reports),
                'average_quality_score': sum(r.quality_score for r in reports) / len(reports),
                'quality_distribution': {
                    'high': sum(1 for r in reports if r.quality == DataQuality.HIGH),
                    'medium': sum(1 for r in reports if r.quality == DataQuality.MEDIUM),
                    'low': sum(1 for r in reports if r.quality == DataQuality.LOW),
                    'invalid': sum(1 for r in reports if r.quality == DataQuality.INVALID)
                }
            }
        
        return summary
    
    def get_cross_source_analysis(self) -> Dict[str, Any]:
        """獲取跨數據源分析結果"""
        if not self.cross_source_comparisons:
            return {'message': '暫無跨數據源比較數據'}
        
        analysis = {
            'total_comparisons': len(self.cross_source_comparisons),
            'average_consistency': 0.0,
            'consistency_distribution': {
                'high': 0,    # > 0.9
                'medium': 0,  # 0.7 - 0.9
                'low': 0      # < 0.7
            },
            'common_conflicts': defaultdict(int),
            'recommendations_summary': defaultdict(int)
        }
        
        consistency_scores = []
        
        for comparison in self.cross_source_comparisons.values():
            consistency_scores.append(comparison.consistency_score)
            
            # 統計一致性分佈
            if comparison.consistency_score > 0.9:
                analysis['consistency_distribution']['high'] += 1
            elif comparison.consistency_score > 0.7:
                analysis['consistency_distribution']['medium'] += 1
            else:
                analysis['consistency_distribution']['low'] += 1
            
            # 統計常見衝突
            for conflict in comparison.conflicts:
                field = conflict.get('field', 'unknown')
                analysis['common_conflicts'][field] += 1
            
            # 統計建議
            for recommendation in comparison.recommendations:
                analysis['recommendations_summary'][recommendation] += 1
        
        if consistency_scores:
            analysis['average_consistency'] = sum(consistency_scores) / len(consistency_scores)
        
        return analysis
    
    # ==================== 響應標準化 ====================
    
    def _standardize_response(
        self,
        raw_response: Any,
        request: DataRequest,
        source: DataSource
    ) -> DataResponse:
        """
        標準化響應數據（增強版本，包含數據質量評估）
        
        Args:
            raw_response: 原始響應
            request: 原始請求
            source: 數據源
            
        Returns:
            標準化的數據響應
        """
        try:
            # 1. 基本響應標準化
            if source == DataSource.FINMIND:
                basic_response = self._standardize_finmind_response(raw_response, request)
            elif source == DataSource.FINNHUB:
                basic_response = self._standardize_finnhub_response(raw_response, request)
            else:
                raise ValueError(f"不支援的數據源: {source}")
            
            # 2. 如果基本標準化成功，進行高級數據標準化
            if basic_response.success:
                try:
                    # 執行跨數據源數據標準化
                    normalized_data = self.normalize_data(
                        raw_response, source, request.symbol, request.data_type
                    )
                    
                    # 更新響應數據為標準化後的數據
                    basic_response.data = normalized_data.to_dict()
                    
                    # 添加數據質量信息到響應中
                    if not hasattr(basic_response, 'metadata'):
                        basic_response.metadata = {}
                    
                    basic_response.metadata.update({
                        'data_quality': normalized_data.quality_report.to_dict(),
                        'normalization_status': normalized_data.normalization_status.value,
                        'data_source_metadata': normalized_data.metadata.to_dict()
                    })
                    
                except Exception as norm_error:
                    logger.warning(f"高級數據標準化失敗，使用基本標準化結果: {norm_error}")
                    # 繼續使用基本標準化結果
            
            return basic_response
                
        except Exception as e:
            logger.error(f"響應標準化失敗: {e}")
            return DataResponse(
                success=False,
                error=f"響應標準化失敗: {str(e)}",
                source=source,
                symbol=request.symbol,
                data_type=request.data_type
            )
    
    def _standardize_finmind_response(self, raw_response: Any, request: DataRequest) -> DataResponse:
        """標準化 FinMind 響應"""
        # 這裡需要根據 FinMind 的實際響應格式進行標準化
        # 暫時返回基本的響應結構
        if hasattr(raw_response, 'success') and raw_response.success:
            return DataResponse(
                success=True,
                data=raw_response.data if hasattr(raw_response, 'data') else raw_response,
                source=DataSource.FINMIND,
                symbol=request.symbol,
                data_type=request.data_type
            )
        else:
            error_msg = getattr(raw_response, 'error', '未知錯誤')
            return DataResponse(
                success=False,
                error=error_msg,
                source=DataSource.FINMIND,
                symbol=request.symbol,
                data_type=request.data_type
            )
    
    def _standardize_finnhub_response(self, raw_response: Any, request: DataRequest) -> DataResponse:
        """標準化 FinnHub 響應 (臨時禁用)"""
        logger.warning("FinnHub 響應處理被跳過 (服務臨時禁用)")
        return DataResponse(
            success=False,
            data=None,
            error="FinnHub服務臨時禁用",
            source=DataSource.FINNHUB,
            symbol=request.symbol,
            data_type=request.data_type,
            cached=False,
            timestamp=datetime.now()
        )
        
        if raw_response and hasattr(raw_response, 'success') and raw_response.success:
            # 根據數據類型進行統一格式轉換
            unified_data = None
            
            if request.data_type == DataType.STOCK_PRICE:
                unified_data = self.finnhub_client.to_unified_stock_data(raw_response, request.symbol)
            elif request.data_type == DataType.COMPANY_PROFILE:
                unified_data = self.finnhub_client.to_unified_company_data(raw_response, request.symbol)
            elif request.data_type == DataType.COMPANY_NEWS:
                unified_data = self.finnhub_client.to_unified_news_data(raw_response, request.symbol)
            elif request.data_type == DataType.FINANCIAL_DATA:
                unified_data = self.finnhub_client.to_unified_financial_data(raw_response, request.symbol)
            
            return DataResponse(
                success=True,
                data=unified_data.to_dict() if unified_data and hasattr(unified_data, 'to_dict') else (unified_data if unified_data else raw_response.data),
                source=DataSource.FINNHUB,
                symbol=request.symbol,
                data_type=request.data_type,
                cached=raw_response.cached
            )
        else:
            return DataResponse(
                success=False,
                error=raw_response.error,
                source=DataSource.FINNHUB,
                symbol=request.symbol,
                data_type=request.data_type
            )
    
    # ==================== 健康監控和性能追蹤 ====================
    
    def _update_source_health(self, source: DataSource, success: bool, response_time: float):
        """
        更新數據源健康狀態
        
        Args:
            source: 數據源
            success: 是否成功
            response_time: 響應時間
        """
        health = self.source_health.get(source)
        if not health:
            return
        
        # 更新響應時間
        health.response_time = response_time
        health.last_check = datetime.now()
        
        # 更新響應時間歷史
        self.response_times[source].append(response_time)
        
        if success:
            # 成功請求
            health.consecutive_failures = 0
            health.success_rate = min(100.0, health.success_rate + 1.0)
            
            # 根據響應時間調整健康狀態
            if response_time < 2.0:
                health.status = HealthStatus.HEALTHY
            elif response_time < 5.0:
                health.status = HealthStatus.DEGRADED
            else:
                health.status = HealthStatus.DEGRADED
        else:
            # 失敗請求
            health.error_count += 1
            health.consecutive_failures += 1
            health.success_rate = max(0.0, health.success_rate - 5.0)
            
            # 根據連續失敗次數調整健康狀態
            if health.consecutive_failures >= self.max_consecutive_failures:
                health.status = HealthStatus.UNHEALTHY
            elif health.consecutive_failures >= 1:
                health.status = HealthStatus.DEGRADED
    
    def _update_routing_metrics(
        self, 
        source: DataSource, 
        symbol_type: SymbolType, 
        data_type: DataType, 
        success: bool, 
        response_time: float
    ):
        """
        更新路由指標
        
        Args:
            source: 數據源
            symbol_type: 符號類型
            data_type: 數據類型
            success: 是否成功
            response_time: 響應時間
        """
        metrics = self.routing_metrics[source][symbol_type][data_type]
        
        if not hasattr(metrics, 'source'):
            # 初始化指標
            metrics.source = source
            metrics.symbol_type = symbol_type
            metrics.data_type = data_type
        
        if success:
            metrics.update_success(response_time)
        else:
            metrics.update_error(response_time)
    
    async def _periodic_health_check(self):
        """
        定期健康檢查
        """
        now = datetime.now()
        if (now - self.last_health_check).total_seconds() >= self.health_check_interval:
            await self._perform_health_checks()
            self.last_health_check = now
    
    def get_routing_performance(self) -> Dict[str, Any]:
        """
        獲取路由性能統計
        
        Returns:
            路由性能數據
        """
        performance_data = {
            'source_health': {
                source.value: health.to_dict() 
                for source, health in self.source_health.items()
            },
            'routing_metrics': {},
            'response_time_stats': {}
        }
        
        # 路由指標
        for source, symbol_types in self.routing_metrics.items():
            source_key = source.value
            performance_data['routing_metrics'][source_key] = {}
            
            for symbol_type, data_types in symbol_types.items():
                symbol_key = symbol_type.value
                performance_data['routing_metrics'][source_key][symbol_key] = {}
                
                for data_type, metrics in data_types.items():
                    data_key = data_type.value
                    performance_data['routing_metrics'][source_key][symbol_key][data_key] = metrics.to_dict()
        
        # 響應時間統計
        for source, times in self.response_times.items():
            if times:
                performance_data['response_time_stats'][source.value] = {
                    'count': len(times),
                    'average': sum(times) / len(times),
                    'min': min(times),
                    'max': max(times),
                    'recent_average': sum(list(times)[-10:]) / min(len(times), 10)
                }
        
        return performance_data
    
    def optimize_routing_rules(self):
        """
        基於性能數據優化路由規則
        """
        # 分析路由性能數據
        performance = self.get_routing_performance()
        
        # 根據成功率和響應時間調整路由優先級
        for rule in self.routing_rules:
            source_metrics = self.routing_metrics.get(rule.primary_source, {}).get(rule.symbol_type, {}).get(rule.data_type)
            
            if source_metrics and hasattr(source_metrics, 'success_rate'):
                # 如果成功率太低，降低優先級
                if source_metrics.success_rate < 80.0:
                    if rule.priority == RoutingPriority.HIGH:
                        rule.priority = RoutingPriority.MEDIUM
                        logger.info(f"降低路由規則優先級: {rule.symbol_type.value} -> {rule.data_type.value} -> {rule.primary_source.value}")
                
                # 如果成功率很高且響應時間快，提升優先級
                elif source_metrics.success_rate > 95.0 and source_metrics.average_response_time < 1.0:
                    if rule.priority == RoutingPriority.MEDIUM:
                        rule.priority = RoutingPriority.HIGH
                        logger.info(f"提升路由規則優先級: {rule.symbol_type.value} -> {rule.data_type.value} -> {rule.primary_source.value}")
    
    # ==================== 故障轉移邏輯 ====================
    
    async def _try_fallback(self, request: DataRequest, failed_source: DataSource, symbol_info: SymbolInfo) -> Optional[DataResponse]:
        """
        嘗試故障轉移到備用數據源
        
        Args:
            request: 原始請求
            failed_source: 失敗的數據源
            symbol_info: 符號信息
            
        Returns:
            備用數據源的響應或 None
        """
        # 查找路由規則中的故障轉移數據源
        matching_rule = self._find_routing_rule(symbol_info.symbol_type, request.data_type)
        fallback_sources = []
        
        if matching_rule and matching_rule.primary_source == failed_source:
            fallback_sources = matching_rule.fallback_sources
        else:
            # 使用默認故障轉移邏輯
            if failed_source == DataSource.FINMIND:
                fallback_sources = [DataSource.FINNHUB]
            elif failed_source == DataSource.FINNHUB:
                fallback_sources = [DataSource.FINMIND]
        
        # 嘗試每個故障轉移數據源
        for fallback_source in fallback_sources:
            # 檢查備用數據源是否可用
            if not self._is_source_available(fallback_source):
                logger.debug(f"備用數據源 {fallback_source.value} 不可用")
                continue
            
            # 檢查備用數據源是否支援該請求
            if not self._is_request_supported(request, fallback_source):
                logger.debug(f"備用數據源 {fallback_source.value} 不支援請求類型 {request.data_type.value}")
                continue
            
            try:
                logger.info(f"嘗試故障轉移: {failed_source.value} -> {fallback_source.value}")
                
                # 執行備用請求
                start_time = datetime.now()
                raw_response = await self._execute_source_request(request, fallback_source)
                response_time = (datetime.now() - start_time).total_seconds()
                
                standardized_response = self._standardize_response(raw_response, request, fallback_source)
                standardized_response.response_time = response_time
                
                if standardized_response.success:
                    logger.info(f"故障轉移成功: {fallback_source.value}")
                    
                    # 更新故障轉移數據源的健康狀態和指標
                    self._update_source_health(fallback_source, True, response_time)
                    self._update_routing_metrics(fallback_source, symbol_info.symbol_type, request.data_type, True, response_time)
                    
                    return standardized_response
                else:
                    # 故障轉移也失敗了
                    self._update_source_health(fallback_source, False, response_time)
                    self._update_routing_metrics(fallback_source, symbol_info.symbol_type, request.data_type, False, response_time)
                
            except Exception as e:
                logger.error(f"故障轉移到 {fallback_source.value} 失敗: {e}")
                # 記錄故障轉移失敗
                self._update_source_health(fallback_source, False, 0.0)
        
        logger.warning(f"所有故障轉移選項都失敗了")
        return None
    
    def _is_request_supported(self, request: DataRequest, source: DataSource) -> bool:
        """
        檢查數據源是否支援特定請求
        
        Args:
            request: 數據請求
            source: 數據源
            
        Returns:
            是否支援
        """
        symbol_type = self._classify_symbol(request.symbol)
        
        if source == DataSource.FINMIND:
            # FinMind 主要支援台股
            if symbol_type != SymbolType.TAIWAN_STOCK:
                return False
            # 支援的數據類型
            return request.data_type in [DataType.STOCK_PRICE, DataType.FINANCIAL_DATA]
        
        elif source == DataSource.FINNHUB:
            # FinnHub 主要支援國際股票
            if symbol_type == SymbolType.TAIWAN_STOCK:
                return False
            # 支援的數據類型
            return request.data_type in [
                DataType.STOCK_PRICE, DataType.COMPANY_PROFILE,
                DataType.COMPANY_NEWS, DataType.FINANCIAL_DATA
            ]
        
        return False
    
    # ==================== 健康檢查和監控 ====================
    
    async def _perform_health_checks(self):
        """執行數據源健康檢查"""
        # 檢查 FinMind
        try:
            if self.finmind_client:
                start_time = datetime.now()
                health_result = await self.finmind_client.health_check()
                response_time = (datetime.now() - start_time).total_seconds()
                
                health = self.source_health[DataSource.FINMIND]
                health.last_check = datetime.now()
                health.response_time = response_time
                
                if health_result.get('status') == 'healthy':
                    health.status = HealthStatus.HEALTHY
                    health.consecutive_failures = 0
                elif health_result.get('status') == 'degraded':
                    health.status = HealthStatus.DEGRADED
                else:
                    health.status = HealthStatus.UNHEALTHY
                    health.consecutive_failures += 1
                    health.last_error = health_result.get('error')
                    
        except Exception as e:
            logger.error(f"FinMind 健康檢查失敗: {e}")
            health = self.source_health[DataSource.FINMIND]
            health.status = HealthStatus.UNHEALTHY
            health.last_check = datetime.now()
            health.error_count += 1
            health.consecutive_failures += 1
            health.last_error = str(e)
        
        # 檢查 FinnHub
        try:
            if self.finnhub_client:
                start_time = datetime.now()
                health_result = await self.finnhub_client.health_check()
                response_time = (datetime.now() - start_time).total_seconds()
                
                health = self.source_health[DataSource.FINNHUB]
                health.last_check = datetime.now()
                health.response_time = response_time
                
                if health_result.get('status') == 'healthy':
                    health.status = HealthStatus.HEALTHY
                    health.consecutive_failures = 0
                elif health_result.get('status') == 'degraded':
                    health.status = HealthStatus.DEGRADED
                else:
                    health.status = HealthStatus.UNHEALTHY
                    health.consecutive_failures += 1
                    health.last_error = health_result.get('error')
                    
        except Exception as e:
            logger.error(f"FinnHub 健康檢查失敗: {e}")
            health = self.source_health[DataSource.FINNHUB]
            health.status = HealthStatus.UNHEALTHY
            health.last_check = datetime.now()
            health.error_count += 1
            health.consecutive_failures += 1
            health.last_error = str(e)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        獲取編排器健康狀態
        
        Returns:
            健康狀態信息
        """
        await self._perform_health_checks()
        
        # 計算整體狀態
        overall_status = HealthStatus.HEALTHY
        for health in self.source_health.values():
            if health.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
                break
            elif health.status == HealthStatus.DEGRADED:
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'sources': {
                source.value: health.to_dict() for source, health in self.source_health.items()
            },
            'statistics': self.get_stats(),
            'routing_performance': self.get_routing_performance(),
            'timestamp': datetime.now().isoformat()
        }
    
    # ==================== 統計和監控 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        success_rate = (self.success_count / self.request_count * 100) if self.request_count > 0 else 0
        
        return {
            'request_count': self.request_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'success_rate': round(success_rate, 2),
            'source_usage': {
                source.value: count for source, count in self.source_usage.items()
            },
            'finmind_client_available': self.finmind_client is not None,
            'cache_stats': self.cache_manager.get_stats() if self.cache_manager else {}
        }
    
    # ==================== 緩存整合方法 ====================
    
    def _create_cache_key(self, request: DataRequest, source: DataSource) -> CacheKey:
        """
        創建緩存鍵
        
        Args:
            request: 數據請求
            source: 數據源
            
        Returns:
            緩存鍵
        """
        # 將數據源映射到緩存源
        cache_source_mapping = {
            DataSource.FINMIND: CacheSource.FINMIND,
            DataSource.FINNHUB: CacheSource.FINNHUB
        }
        
        cache_source = cache_source_mapping.get(source, CacheSource.ORCHESTRATOR)
        
        # 生成參數哈希
        params_dict = {
            'start_date': request.start_date,
            'end_date': request.end_date,
            'params': request.params or {}
        }
        params_str = json.dumps(params_dict, sort_keys=True)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:8]  # 安全修復：使用SHA256替換MD5
        
        return CacheKey(
            source=cache_source,
            data_type=request.data_type.value,
            symbol=request.symbol.upper(),
            params_hash=params_hash
        )
    
    async def _get_cached_response(self, cache_key: CacheKey) -> Optional[DataResponse]:
        """
        從緩存獲取響應
        
        Args:
            cache_key: 緩存鍵
            
        Returns:
            緩存的響應或 None
        """
        if not self.cache_manager:
            return None
        
        try:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                # 緩存管理器返回 (data, status) 元組
                if isinstance(cached_result, tuple) and len(cached_result) == 2:
                    cached_data, cache_status = cached_result
                else:
                    cached_data = cached_result
                
                # 將緩存數據轉換為 DataResponse
                if isinstance(cached_data, dict):
                    return DataResponse(
                        success=cached_data.get('success', True),
                        data=cached_data.get('data'),
                        error=cached_data.get('error'),
                        source=DataSource(cached_data.get('source', 'unknown')),
                        metadata=cached_data.get('metadata', {}),
                        from_cache=True
                    )
        except Exception as e:
            logger.error(f"緩存獲取失敗: {e}")
        
        return None
        
        return None
    
    async def _cache_response(self, cache_key: CacheKey, response: DataResponse):
        """
        緩存響應數據
        
        Args:
            cache_key: 緩存鍵
            response: 響應數據
        """
        if not self.cache_manager or not response.success:
            return
        
        try:
            # 準備緩存數據
            cache_data = {
                'success': response.success,
                'data': response.data,
                'error': response.error,
                'source': response.source.value,
                'metadata': response.metadata,
                'timestamp': datetime.now().isoformat()
            }
            
            # 設置緩存
            await self.cache_manager.set(cache_key, cache_data)
            logger.debug(f"響應已緩存: {cache_key.symbol} ({cache_key.source.value})")
            
        except Exception as e:
            logger.error(f"緩存設置失敗: {e}")
    
    async def invalidate_cache(self, symbol: str = None, data_type: DataType = None) -> int:
        """
        使緩存失效
        
        Args:
            symbol: 股票代號（可選）
            data_type: 數據類型（可選）
            
        Returns:
            失效的緩存條目數量
        """
        if not self.cache_manager:
            return 0
        
        try:
            # 構建緩存鍵模式
            if symbol and data_type:
                pattern = f"*:{symbol.upper()}:{data_type.value}:*"
            elif symbol:
                pattern = f"*:{symbol.upper()}:*"
            elif data_type:
                pattern = f"*:*:{data_type.value}:*"
            else:
                pattern = "*"
            
            return await self.cache_manager.invalidate_pattern(pattern)
            
        except Exception as e:
            logger.error(f"緩存失效失敗: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        獲取緩存統計信息
        
        Returns:
            緩存統計信息
        """
        if not self.cache_manager:
            return {'cache_enabled': False}
        
        return self.cache_manager.get_stats()
    
    # ==================== 國際市場差異化功能 ====================
    
    async def find_international_peers(self, taiwan_symbol: str, user_context: Optional[UserContext] = None, limit: int = 5) -> Dict[str, Any]:
        """
        尋找台股的國際同業公司
        
        Args:
            taiwan_symbol: 台股代號
            user_context: 用戶上下文
            limit: 返回的同業公司數量限制
            
        Returns:
            同業比較結果
        """
        try:
            # 檢查用戶權限
            if user_context and user_context.membership_tier.value in ['FREE']:
                can_access, upgrade_prompt = await self.upgrade_service.check_international_data_access(
                    user_context, taiwan_symbol
                )
                if not can_access:
                    return {
                        'success': False,
                        'error': '需要升級會員以使用國際同業比較功能',
                        'upgrade_prompt': upgrade_prompt.to_dict() if upgrade_prompt else None
                    }
            
            # 執行同業分析
            peer_comparison = await self.international_market_service.find_international_peers(
                taiwan_symbol, limit
            )
            
            if peer_comparison:
                return {
                    'success': True,
                    'data': peer_comparison.to_dict(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'找不到 {taiwan_symbol} 的國際同業公司'
                }
                
        except Exception as e:
            logger.error(f"國際同業分析失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reset_stats(self):
        """重置統計信息"""
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.source_usage = {
            DataSource.FINMIND: 0,
            DataSource.FINNHUB: 0
        }

# ==================== 工具函數 ====================

def create_data_orchestrator(config: Optional[Dict[str, Any]] = None) -> DataOrchestrator:
    """創建數據編排器的便利函數"""
    return DataOrchestrator(config)

async def create_and_initialize_orchestrator(config: Optional[Dict[str, Any]] = None) -> DataOrchestrator:
    """創建並初始化數據編排器"""
    orchestrator = create_data_orchestrator(config)
    await orchestrator.initialize()
    return orchestrator
    
    # ==================== 國際市場差異化功能 ====================
    
    async def find_international_peers(self, taiwan_symbol: str, user_context: Optional[UserContext] = None, limit: int = 5) -> Dict[str, Any]:
        """
        尋找台股的國際同業公司
        
        Args:
            taiwan_symbol: 台股代號
            user_context: 用戶上下文
            limit: 返回的同業公司數量限制
            
        Returns:
            同業比較結果
        """
        try:
            # 檢查用戶權限
            if user_context and user_context.membership_tier.value in ['FREE']:
                can_access, upgrade_prompt = await self.upgrade_service.check_international_data_access(
                    user_context, taiwan_symbol
                )
                if not can_access:
                    return {
                        'success': False,
                        'error': '需要升級會員以使用國際同業比較功能',
                        'upgrade_prompt': upgrade_prompt.to_dict() if upgrade_prompt else None
                    }
            
            # 執行同業分析
            peer_comparison = await self.international_market_service.find_international_peers(
                taiwan_symbol, limit
            )
            
            if peer_comparison:
                return {
                    'success': True,
                    'data': peer_comparison.to_dict(),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': f'找不到 {taiwan_symbol} 的國際同業公司'
                }
                
        except Exception as e:
            logger.error(f"國際同業分析失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_global_market_correlation(self, symbols: List[str], user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """
        分析全球市場相關性
        
        Args:
            symbols: 股票代號列表
            user_context: 用戶上下文
            
        Returns:
            相關性分析結果
        """
        try:
            # 檢查用戶權限
            if user_context and user_context.membership_tier.value in ['FREE']:
                # 檢查是否包含國際股票
                has_international = any(
                    not self.international_market_service._is_international_symbol(symbol) == False
                    for symbol in symbols
                )
                
                if has_international:
                    return {
                        'success': False,
                        'error': '需要升級會員以使用全球市場相關性分析功能',
                        'upgrade_prompt': {
                            'title': '🌍 解鎖全球市場相關性分析',
                            'message': '升級至 Gold 會員，獲得專業的跨市場相關性分析工具',
                            'benefits': [
                                '全球股票相關性分析',
                                '投資組合風險評估',
                                '跨市場套利機會發現',
                                '專業級風險管理工具'
                            ]
                        }
                    }
            
            # 執行相關性分析
            correlations = await self.international_market_service.analyze_market_correlation(symbols)
            
            return {
                'success': True,
                'data': {
                    'correlations': [corr.to_dict() for corr in correlations],
                    'analysis_summary': self._generate_correlation_summary(correlations),
                    'risk_insights': self._generate_risk_insights(correlations)
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"全球市場相關性分析失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_risk_diversification_advice(self, portfolio_symbols: List[str], user_context: Optional[UserContext] = None, target_risk_level: str = "moderate") -> Dict[str, Any]:
        """
        獲取風險分散建議
        
        Args:
            portfolio_symbols: 投資組合股票代號
            user_context: 用戶上下文
            target_risk_level: 目標風險水平
            
        Returns:
            風險分散建議
        """
        try:
            # 檢查用戶權限
            if user_context and user_context.membership_tier.value in ['FREE']:
                return {
                    'success': False,
                    'error': '需要升級會員以使用投資組合風險分散建議功能',
                    'upgrade_prompt': {
                        'title': '📊 專業投資組合分析',
                        'message': '升級至 Gold 會員，獲得個人化的投資組合優化建議',
                        'benefits': [
                            '專業風險分散分析',
                            '個人化資產配置建議',
                            '投資組合優化策略',
                            '風險管理最佳實踐'
                        ]
                    }
                }
            
            # 執行風險分散分析
            advice = await self.international_market_service.generate_risk_diversification_advice(
                portfolio_symbols, target_risk_level
            )
            
            return {
                'success': True,
                'data': advice.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"風險分散建議生成失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_cross_timezone_alerts(self, user_context: Optional[UserContext] = None, symbols: List[str] = None) -> Dict[str, Any]:
        """
        獲取跨時區市場預警
        
        Args:
            user_context: 用戶上下文
            symbols: 關注的股票代號列表
            
        Returns:
            跨時區預警列表
        """
        try:
            # 檢查用戶權限
            if user_context and user_context.membership_tier.value in ['FREE']:
                return {
                    'success': False,
                    'error': '需要升級會員以使用跨時區市場預警功能',
                    'upgrade_prompt': {
                        'title': '⏰ 24小時全球市場監控',
                        'message': '升級至 Gold 會員，獲得專業的跨時區市場預警服務',
                        'benefits': [
                            '24小時全球市場監控',
                            '重要事件即時預警',
                            '跨時區影響分析',
                            '個人化預警設定'
                        ]
                    }
                }
            
            # 獲取活躍預警
            alerts = await self.international_market_service.get_active_alerts(user_context, symbols)
            
            return {
                'success': True,
                'data': {
                    'alerts': [alert.to_dict() for alert in alerts],
                    'total_count': len(alerts),
                    'high_priority_count': len([a for a in alerts if a.severity == 'high'])
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"跨時區預警獲取失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def analyze_currency_impact(self, taiwan_symbol: str, user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """
        分析匯率影響
        
        Args:
            taiwan_symbol: 台股代號
            user_context: 用戶上下文
            
        Returns:
            匯率影響分析
        """
        try:
            # 檢查用戶權限
            if user_context and user_context.membership_tier.value in ['FREE']:
                return {
                    'success': False,
                    'error': '需要升級會員以使用匯率影響分析功能',
                    'upgrade_prompt': {
                        'title': '💱 專業匯率影響分析',
                        'message': '升級至 Gold 會員，獲得深度的匯率風險分析工具',
                        'benefits': [
                            '匯率敏感度分析',
                            '貨幣風險評估',
                            '避險策略建議',
                            '跨國投資指導'
                        ]
                    }
                }
            
            # 執行匯率影響分析
            analysis = await self.international_market_service.analyze_currency_impact(taiwan_symbol)
            
            return {
                'success': True,
                'data': analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"匯率影響分析失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def predict_global_event_impact(self, event_type: str, taiwan_symbols: List[str], user_context: Optional[UserContext] = None) -> Dict[str, Any]:
        """
        預測全球經濟事件影響
        
        Args:
            event_type: 事件類型
            taiwan_symbols: 台股代號列表
            user_context: 用戶上下文
            
        Returns:
            事件影響預測
        """
        try:
            # 檢查用戶權限（Diamond 會員專屬功能）
            if user_context and user_context.membership_tier.value not in ['DIAMOND']:
                return {
                    'success': False,
                    'error': '需要升級至 Diamond 會員以使用全球事件影響預測功能',
                    'upgrade_prompt': {
                        'title': '🔮 AI驅動的事件影響預測',
                        'message': '升級至 Diamond 會員，獲得最先進的全球事件影響預測模型',
                        'benefits': [
                            'AI驅動的影響預測',
                            '多情境分析模型',
                            '專業投資策略建議',
                            '機構級風險管理工具'
                        ]
                    }
                }
            
            # 執行事件影響預測
            prediction = await self.international_market_service.predict_global_event_impact(
                event_type, taiwan_symbols
            )
            
            return {
                'success': True,
                'data': prediction,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"全球事件影響預測失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_correlation_summary(self, correlations: List) -> str:
        """生成相關性分析摘要"""
        if not correlations:
            return "無相關性數據"
        
        high_corr = [c for c in correlations if abs(c.correlation_coefficient) > 0.7]
        medium_corr = [c for c in correlations if 0.3 < abs(c.correlation_coefficient) <= 0.7]
        low_corr = [c for c in correlations if abs(c.correlation_coefficient) <= 0.3]
        
        summary_parts = []
        
        if high_corr:
            summary_parts.append(f"發現 {len(high_corr)} 對股票具有高度相關性（>0.7）")
        
        if medium_corr:
            summary_parts.append(f"{len(medium_corr)} 對股票具有中度相關性（0.3-0.7）")
        
        if low_corr:
            summary_parts.append(f"{len(low_corr)} 對股票相關性較低（<0.3）")
        
        return "，".join(summary_parts) + "。"
    
    def _generate_risk_insights(self, correlations: List) -> List[str]:
        """生成風險洞察"""
        insights = []
        
        high_positive_corr = [c for c in correlations if c.correlation_coefficient > 0.7]
        high_negative_corr = [c for c in correlations if c.correlation_coefficient < -0.7]
        
        if high_positive_corr:
            insights.append("部分股票高度正相關，可能存在集中風險")
        
        if high_negative_corr:
            insights.append("發現負相關股票，可用於風險對沖")
        
        if len(high_positive_corr) > len(correlations) * 0.5:
            insights.append("投資組合整體相關性偏高，建議增加分散化")
        
        return insights