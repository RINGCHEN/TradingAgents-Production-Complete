#!/usr/bin/env python3
"""
統一數據管理器 (DataManager)
天工 (TianGong) - 統一的數據層整合和格式標準化

此模組提供統一的數據接口，整合所有數據源並提供標準化的數據格式，
確保系統各組件之間的數據一致性和互操作性。

功能特色：
1. 統一的數據接口和格式標準化
2. 多數據源智能路由和容錯
3. 數據質量檢查和驗證
4. 緩存優化和性能提升
5. 實時數據更新和同步
6. Taiwan市場數據專業化處理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
from abc import ABC, abstractmethod

from .data_orchestrator import DataOrchestrator, DataRequest, DataResponse, DataType, DataSource
from ..utils.cache_manager import CacheManager
from ..default_config import DEFAULT_CONFIG

# 配置日誌
logger = logging.getLogger(__name__)

class DataQuality(Enum):
    """數據質量等級"""
    EXCELLENT = "excellent"       # 優秀 - 完整、及時、準確
    GOOD = "good"                # 良好 - 基本完整和準確
    FAIR = "fair"                # 一般 - 部分缺失但可用
    POOR = "poor"                # 較差 - 有明顯缺失或延遲
    UNAVAILABLE = "unavailable"  # 不可用 - 數據源故障

class DataPriority(Enum):
    """數據優先級"""
    CRITICAL = "critical"        # 關鍵 - 系統核心功能必需
    HIGH = "high"               # 高 - 重要功能需要
    MEDIUM = "medium"           # 中 - 一般功能使用
    LOW = "low"                 # 低 - 輔助功能

@dataclass
class DataMetrics:
    """數據指標"""
    source: str                  # 數據源
    quality: DataQuality         # 數據質量
    latency_ms: float           # 延遲(毫秒)
    completeness: float         # 完整度(0-1)
    freshness_seconds: int      # 新鮮度(秒)
    size_bytes: int             # 數據大小
    timestamp: datetime         # 時間戳

@dataclass
class StandardizedData:
    """標準化數據格式"""
    data_type: DataType          # 數據類型
    symbol: str                  # 股票代號
    data: Dict[str, Any]        # 數據內容
    metadata: Dict[str, Any]    # 元數據
    quality_metrics: DataMetrics # 質量指標
    source_info: Dict[str, Any] # 來源資訊
    timestamp: datetime         # 時間戳
    expires_at: Optional[datetime] = None  # 過期時間

class DataValidator(ABC):
    """數據驗證器抽象基類"""
    
    @abstractmethod
    async def validate(self, data: Dict[str, Any]) -> bool:
        """驗證數據"""
        pass
    
    @abstractmethod
    def get_quality_score(self, data: Dict[str, Any]) -> float:
        """獲取質量分數 (0-1)"""
        pass

class StockPriceValidator(DataValidator):
    """股價數據驗證器"""
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """驗證股價數據"""
        required_fields = ['close', 'volume', 'date']
        
        # 檢查必需字段
        for field in required_fields:
            if field not in data:
                return False
        
        # 檢查數值合理性
        try:
            close_price = float(data['close'])
            volume = int(data['volume'])
            
            if close_price <= 0 or volume < 0:
                return False
                
            # 檢查價格變動合理性
            if 'open' in data:
                open_price = float(data['open'])
                change_ratio = abs(close_price - open_price) / open_price
                if change_ratio > 0.3:  # 單日變動超過30%需要特別檢查
                    logger.warning(f"異常價格變動: {change_ratio:.2%}")
            
            return True
            
        except (ValueError, TypeError, ZeroDivisionError):
            return False
    
    def get_quality_score(self, data: Dict[str, Any]) -> float:
        """獲取股價數據質量分數"""
        score = 0.0
        
        # 基礎字段完整性 (40%)
        required_fields = ['close', 'open', 'high', 'low', 'volume']
        present_fields = sum(1 for field in required_fields if field in data and data[field] is not None)
        score += (present_fields / len(required_fields)) * 0.4
        
        # 數據新鮮度 (30%)
        if 'date' in data:
            try:
                data_date = datetime.strptime(str(data['date']), '%Y-%m-%d')
                days_old = (datetime.now() - data_date).days
                freshness_score = max(0, 1 - days_old / 7)  # 7天內為滿分
                score += freshness_score * 0.3
            except:
                pass
        
        # 數值合理性 (30%)
        try:
            if all(field in data for field in ['open', 'high', 'low', 'close']):
                o, h, l, c = data['open'], data['high'], data['low'], data['close']
                if l <= o <= h and l <= c <= h:  # 價格關係合理
                    score += 0.3
        except:
            pass
        
        return min(1.0, score)

class FinancialDataValidator(DataValidator):
    """財務數據驗證器"""
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """驗證財務數據"""
        # 檢查關鍵財務指標
        key_metrics = ['revenue', 'net_income', 'total_assets', 'shareholders_equity']
        
        valid_metrics = 0
        for metric in key_metrics:
            if metric in data and isinstance(data[metric], (int, float)):
                valid_metrics += 1
        
        return valid_metrics >= 2  # 至少需要2個有效指標
    
    def get_quality_score(self, data: Dict[str, Any]) -> float:
        """獲取財務數據質量分數"""
        # 簡化的質量評分
        total_fields = len(data)
        valid_fields = sum(1 for v in data.values() if v is not None and v != 0)
        
        if total_fields == 0:
            return 0.0
        
        return valid_fields / total_fields

class NewsDataValidator(DataValidator):
    """新聞數據驗證器"""
    
    async def validate(self, data: Dict[str, Any]) -> bool:
        """驗證新聞數據"""
        required_fields = ['title', 'content', 'published_at']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # 檢查內容長度
        if len(data['title']) < 5 or len(data['content']) < 10:
            return False
        
        return True
    
    def get_quality_score(self, data: Dict[str, Any]) -> float:
        """獲取新聞數據質量分數"""
        score = 0.0
        
        # 標題質量 (25%)
        if 'title' in data and len(data['title']) >= 5:
            score += 0.25
        
        # 內容質量 (35%)
        if 'content' in data:
            content_length = len(data['content'])
            if content_length >= 100:
                score += 0.35
            elif content_length >= 50:
                score += 0.2
        
        # 時效性 (25%)
        if 'published_at' in data:
            try:
                pub_time = datetime.fromisoformat(data['published_at'].replace('Z', '+00:00'))
                hours_old = (datetime.now() - pub_time.replace(tzinfo=None)).total_seconds() / 3600
                if hours_old <= 24:
                    score += 0.25
                elif hours_old <= 72:
                    score += 0.15
            except:
                pass
        
        # 來源可信度 (15%)
        if 'source' in data:
            trusted_sources = ['reuters', 'bloomberg', 'cnbc', '經濟日報', '工商時報']
            if any(source in data['source'].lower() for source in trusted_sources):
                score += 0.15
        
        return min(1.0, score)

class DataManager:
    """統一數據管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化數據管理器
        
        Args:
            config: 配置參數
        """
        self.config = config or DEFAULT_CONFIG
        self.data_orchestrator = None
        self.cache_manager = CacheManager(self.config.get('cache', {}))
        
        # 數據驗證器
        self.validators = {
            DataType.STOCK_PRICE: StockPriceValidator(),
            DataType.FINANCIAL_DATA: FinancialDataValidator(),
            DataType.COMPANY_NEWS: NewsDataValidator()
        }
        
        # 數據質量追蹤
        self.quality_history = {}
        self.performance_metrics = {
            'total_requests': 0,
            'cache_hits': 0,
            'validation_failures': 0,
            'average_latency': 0.0
        }
        
        logger.info("統一數據管理器初始化完成")
    
    async def initialize(self):
        """異步初始化"""
        try:
            # 初始化數據編排器
            self.data_orchestrator = DataOrchestrator(self.config.get('data_orchestrator', {}))
            await self.data_orchestrator.initialize()
            
            # 初始化緩存管理器
            await self.cache_manager.initialize()
            
            logger.info("數據管理器異步初始化完成")
            
        except Exception as e:
            logger.error(f"數據管理器初始化失敗: {str(e)}")
            raise
    
    async def get_standardized_data(
        self,
        symbol: str,
        data_type: DataType,
        priority: DataPriority = DataPriority.MEDIUM,
        force_refresh: bool = False,
        quality_threshold: float = 0.6
    ) -> Optional[StandardizedData]:
        """
        獲取標準化數據
        
        Args:
            symbol: 股票代號
            data_type: 數據類型
            priority: 數據優先級
            force_refresh: 強制刷新
            quality_threshold: 質量閾值
            
        Returns:
            標準化數據對象
        """
        start_time = datetime.now()
        self.performance_metrics['total_requests'] += 1
        
        try:
            # 檢查緩存
            if not force_refresh:
                cached_data = await self._get_from_cache(symbol, data_type)
                if cached_data:
                    self.performance_metrics['cache_hits'] += 1
                    return cached_data
            
            # 從數據源獲取數據
            raw_data = await self._fetch_raw_data(symbol, data_type, priority)
            if not raw_data:
                return None
            
            # 數據驗證和質量評估
            validation_result = await self._validate_and_assess_quality(raw_data, data_type)
            if validation_result['quality_score'] < quality_threshold:
                logger.warning(f"數據質量不符合要求: {validation_result['quality_score']:.2f} < {quality_threshold}")
                self.performance_metrics['validation_failures'] += 1
                
                # 嘗試備用數據源
                backup_data = await self._try_backup_sources(symbol, data_type, priority)
                if backup_data:
                    raw_data = backup_data
                    validation_result = await self._validate_and_assess_quality(raw_data, data_type)
            
            # 標準化數據格式
            standardized_data = await self._standardize_data(
                symbol, data_type, raw_data, validation_result
            )
            
            # 緩存結果
            await self._cache_data(standardized_data)
            
            # 更新性能指標
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self._update_performance_metrics(latency)
            
            return standardized_data
            
        except Exception as e:
            logger.error(f"獲取標準化數據失敗: {symbol}, {data_type}, 錯誤: {str(e)}")
            return None
    
    async def _get_from_cache(self, symbol: str, data_type: DataType) -> Optional[StandardizedData]:
        """從緩存獲取數據"""
        cache_key = f"standardized:{data_type.value}:{symbol}"
        
        try:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                # 檢查數據是否過期
                data_dict = json.loads(cached_data)
                if 'expires_at' in data_dict and data_dict['expires_at']:
                    expires_at = datetime.fromisoformat(data_dict['expires_at'])
                    if datetime.now() > expires_at:
                        await self.cache_manager.delete(cache_key)
                        return None
                
                # 重構StandardizedData對象
                return self._reconstruct_standardized_data(data_dict)
            
        except Exception as e:
            logger.warning(f"緩存讀取失敗: {str(e)}")
        
        return None
    
    async def _fetch_raw_data(
        self, symbol: str, data_type: DataType, priority: DataPriority
    ) -> Optional[Dict[str, Any]]:
        """從數據源獲取原始數據"""
        request = DataRequest(
            symbol=symbol,
            data_type=data_type,
            priority=priority.value,
            timeout=30 if priority == DataPriority.CRITICAL else 10
        )
        
        response = await self.data_orchestrator.get_data(request)
        
        if response.success:
            return response.data
        else:
            logger.warning(f"數據獲取失敗: {symbol}, {data_type}, 錯誤: {response.error}")
            return None
    
    async def _validate_and_assess_quality(
        self, data: Dict[str, Any], data_type: DataType
    ) -> Dict[str, Any]:
        """驗證數據並評估質量"""
        validator = self.validators.get(data_type)
        
        if not validator:
            # 沒有對應驗證器，使用基本驗證
            is_valid = data is not None and len(data) > 0
            quality_score = 0.5 if is_valid else 0.0
        else:
            is_valid = await validator.validate(data)
            quality_score = validator.get_quality_score(data) if is_valid else 0.0
        
        return {
            'is_valid': is_valid,
            'quality_score': quality_score,
            'quality_level': self._get_quality_level(quality_score)
        }
    
    def _get_quality_level(self, score: float) -> DataQuality:
        """根據分數獲取質量等級"""
        if score >= 0.9:
            return DataQuality.EXCELLENT
        elif score >= 0.7:
            return DataQuality.GOOD
        elif score >= 0.5:
            return DataQuality.FAIR
        elif score > 0:
            return DataQuality.POOR
        else:
            return DataQuality.UNAVAILABLE
    
    async def _try_backup_sources(
        self, symbol: str, data_type: DataType, priority: DataPriority
    ) -> Optional[Dict[str, Any]]:
        """嘗試備用數據源"""
        # 實現備用數據源邏輯
        # 這裡可以嘗試不同的數據源或API端點
        logger.info(f"嘗試備用數據源: {symbol}, {data_type}")
        
        # 暫時返回None，實際實現需要根據具體數據源配置
        return None
    
    async def _standardize_data(
        self,
        symbol: str,
        data_type: DataType,
        raw_data: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> StandardizedData:
        """標準化數據格式"""
        now = datetime.now()
        
        # 計算過期時間
        expires_at = None
        if data_type == DataType.STOCK_PRICE:
            expires_at = now + timedelta(minutes=15)  # 股價數據15分鐘後過期
        elif data_type == DataType.COMPANY_NEWS:
            expires_at = now + timedelta(hours=1)     # 新聞數據1小時後過期
        elif data_type == DataType.FINANCIAL_DATA:
            expires_at = now + timedelta(days=1)      # 財務數據1天後過期
        
        # 創建質量指標
        quality_metrics = DataMetrics(
            source=raw_data.get('source', 'unknown'),
            quality=validation_result['quality_level'],
            latency_ms=0.0,  # 將在後續更新
            completeness=validation_result['quality_score'],
            freshness_seconds=0,  # 將在後續計算
            size_bytes=len(str(raw_data)),
            timestamp=now
        )
        
        # 標準化數據內容
        standardized_content = self._standardize_content(data_type, raw_data)
        
        # 生成元數據
        metadata = {
            'processing_time': now.isoformat(),
            'data_version': '1.0',
            'standardization_rules': self._get_standardization_rules(data_type),
            'taiwan_market_specific': self._is_taiwan_symbol(symbol)
        }
        
        # 來源資訊
        source_info = {
            'primary_source': raw_data.get('source', 'unknown'),
            'api_endpoint': raw_data.get('endpoint', 'unknown'),
            'request_id': raw_data.get('request_id', 'unknown'),
            'rate_limit_info': raw_data.get('rate_limit', {})
        }
        
        return StandardizedData(
            data_type=data_type,
            symbol=symbol,
            data=standardized_content,
            metadata=metadata,
            quality_metrics=quality_metrics,
            source_info=source_info,
            timestamp=now,
            expires_at=expires_at
        )
    
    def _standardize_content(self, data_type: DataType, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """標準化數據內容"""
        if data_type == DataType.STOCK_PRICE:
            return self._standardize_stock_price(raw_data)
        elif data_type == DataType.FINANCIAL_DATA:
            return self._standardize_financial_data(raw_data)
        elif data_type == DataType.COMPANY_NEWS:
            return self._standardize_news_data(raw_data)
        else:
            return raw_data
    
    def _standardize_stock_price(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """標準化股價數據"""
        standardized = {
            'symbol': raw_data.get('symbol', ''),
            'date': raw_data.get('date', ''),
            'open': self._safe_float(raw_data.get('open')),
            'high': self._safe_float(raw_data.get('high')),
            'low': self._safe_float(raw_data.get('low')),
            'close': self._safe_float(raw_data.get('close')),
            'volume': self._safe_int(raw_data.get('volume')),
            'adjusted_close': self._safe_float(raw_data.get('adjusted_close')),
            'currency': raw_data.get('currency', 'TWD')
        }
        
        # 計算額外指標
        if standardized['open'] and standardized['close']:
            standardized['change'] = standardized['close'] - standardized['open']
            standardized['change_percent'] = (standardized['change'] / standardized['open']) * 100
        
        return standardized
    
    def _standardize_financial_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """標準化財務數據"""
        return {
            'symbol': raw_data.get('symbol', ''),
            'period': raw_data.get('period', ''),
            'currency': raw_data.get('currency', 'TWD'),
            'revenue': self._safe_float(raw_data.get('revenue')),
            'net_income': self._safe_float(raw_data.get('net_income')),
            'total_assets': self._safe_float(raw_data.get('total_assets')),
            'shareholders_equity': self._safe_float(raw_data.get('shareholders_equity')),
            'eps': self._safe_float(raw_data.get('eps')),
            'roe': self._safe_float(raw_data.get('roe')),
            'roa': self._safe_float(raw_data.get('roa')),
            'debt_ratio': self._safe_float(raw_data.get('debt_ratio')),
            'report_date': raw_data.get('report_date', '')
        }
    
    def _standardize_news_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """標準化新聞數據"""
        return {
            'title': raw_data.get('title', ''),
            'content': raw_data.get('content', ''),
            'summary': raw_data.get('summary', ''),
            'published_at': raw_data.get('published_at', ''),
            'source': raw_data.get('source', ''),
            'author': raw_data.get('author', ''),
            'url': raw_data.get('url', ''),
            'category': raw_data.get('category', ''),
            'sentiment': raw_data.get('sentiment', 'neutral'),
            'language': raw_data.get('language', 'zh-TW'),
            'related_symbols': raw_data.get('related_symbols', [])
        }
    
    def _safe_float(self, value: Any) -> Optional[float]:
        """安全轉換為浮點數"""
        try:
            return float(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value: Any) -> Optional[int]:
        """安全轉換為整數"""
        try:
            return int(value) if value is not None else None
        except (ValueError, TypeError):
            return None
    
    def _get_standardization_rules(self, data_type: DataType) -> List[str]:
        """獲取標準化規則"""
        rules = {
            DataType.STOCK_PRICE: [
                "價格欄位轉換為浮點數",
                "成交量轉換為整數",
                "計算漲跌幅",
                "統一貨幣單位"
            ],
            DataType.FINANCIAL_DATA: [
                "財務指標標準化",
                "貨幣單位統一",
                "比率計算",
                "期間格式化"
            ],
            DataType.COMPANY_NEWS: [
                "文字編碼統一",
                "時間格式標準化",
                "語言標註",
                "相關股票提取"
            ]
        }
        return rules.get(data_type, [])
    
    def _is_taiwan_symbol(self, symbol: str) -> bool:
        """檢查是否為台股代號"""
        return symbol.isdigit() and len(symbol) == 4
    
    async def _cache_data(self, data: StandardizedData):
        """緩存數據"""
        cache_key = f"standardized:{data.data_type.value}:{data.symbol}"
        
        # 序列化數據
        data_dict = asdict(data)
        data_dict['data_type'] = data.data_type.value
        data_dict['quality_metrics']['quality'] = data.quality_metrics.quality.value
        data_dict['timestamp'] = data.timestamp.isoformat()
        if data.expires_at:
            data_dict['expires_at'] = data.expires_at.isoformat()
        
        # 設置緩存
        cache_ttl = 900  # 15分鐘默認TTL
        if data.data_type == DataType.FINANCIAL_DATA:
            cache_ttl = 3600  # 財務數據1小時
        elif data.data_type == DataType.COMPANY_NEWS:
            cache_ttl = 1800  # 新聞數據30分鐘
        
        try:
            await self.cache_manager.set(
                cache_key, 
                json.dumps(data_dict), 
                ttl=cache_ttl
            )
        except Exception as e:
            logger.warning(f"緩存數據失敗: {str(e)}")
    
    def _reconstruct_standardized_data(self, data_dict: Dict[str, Any]) -> StandardizedData:
        """重構StandardizedData對象"""
        # 重構數據類型枚舉
        data_dict['data_type'] = DataType(data_dict['data_type'])
        
        # 重構質量指標
        quality_metrics_dict = data_dict['quality_metrics']
        quality_metrics_dict['quality'] = DataQuality(quality_metrics_dict['quality'])
        quality_metrics_dict['timestamp'] = datetime.fromisoformat(quality_metrics_dict['timestamp'])
        data_dict['quality_metrics'] = DataMetrics(**quality_metrics_dict)
        
        # 重構時間戳
        data_dict['timestamp'] = datetime.fromisoformat(data_dict['timestamp'])
        if data_dict.get('expires_at'):
            data_dict['expires_at'] = datetime.fromisoformat(data_dict['expires_at'])
        
        return StandardizedData(**data_dict)
    
    def _update_performance_metrics(self, latency_ms: float):
        """更新性能指標"""
        # 更新平均延遲
        total_requests = self.performance_metrics['total_requests']
        current_avg = self.performance_metrics['average_latency']
        
        new_avg = ((current_avg * (total_requests - 1)) + latency_ms) / total_requests
        self.performance_metrics['average_latency'] = new_avg
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        total_requests = self.performance_metrics['total_requests']
        
        return {
            'total_requests': total_requests,
            'cache_hit_rate': (self.performance_metrics['cache_hits'] / total_requests) if total_requests > 0 else 0,
            'validation_failure_rate': (self.performance_metrics['validation_failures'] / total_requests) if total_requests > 0 else 0,
            'average_latency_ms': self.performance_metrics['average_latency'],
            'data_quality_summary': self._get_quality_summary()
        }
    
    def _get_quality_summary(self) -> Dict[str, int]:
        """獲取數據質量總結"""
        # 簡化的質量統計
        return {
            'excellent': 0,
            'good': 0,
            'fair': 0,
            'poor': 0,
            'unavailable': 0
        }

# 便利函數
async def create_data_manager(config: Optional[Dict[str, Any]] = None) -> DataManager:
    """創建並初始化數據管理器"""
    manager = DataManager(config)
    await manager.initialize()
    return manager

if __name__ == "__main__":
    # 測試腳本
    async def test_data_manager():
        print("測試統一數據管理器...")
        
        # 創建數據管理器
        manager = await create_data_manager()
        
        # 測試獲取標準化數據
        data = await manager.get_standardized_data(
            symbol="2330",
            data_type=DataType.STOCK_PRICE,
            priority=DataPriority.HIGH
        )
        
        if data:
            print(f"獲取到標準化數據: {data.symbol}")
            print(f"數據質量: {data.quality_metrics.quality.value}")
            print(f"完整度: {data.quality_metrics.completeness:.2f}")
        else:
            print("未能獲取到數據")
        
        # 獲取性能指標
        metrics = manager.get_performance_metrics()
        print(f"性能指標: {metrics}")
        
        print("數據管理器測試完成")
    
    asyncio.run(test_data_manager())