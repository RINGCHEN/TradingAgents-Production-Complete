#!/usr/bin/env python3
"""
TradingAgents 統一緩存管理器
支援 Redis 緩存，提供跨數據源緩存協調和統一監控
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
from collections import defaultdict, deque

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..default_config import DEFAULT_CONFIG

# 設置日誌
logger = logging.getLogger(__name__)

class CacheStatus(Enum):
    """緩存狀態枚舉"""
    HIT = "hit"           # 緩存命中
    MISS = "miss"         # 緩存未命中
    EXPIRED = "expired"   # 緩存過期
    ERROR = "error"       # 緩存錯誤
    DISABLED = "disabled" # 緩存禁用

class CacheSource(Enum):
    """緩存數據源枚舉"""
    FINMIND = "finmind"
    FINNHUB = "finnhub"
    ORCHESTRATOR = "orchestrator"

@dataclass
class CacheKey:
    """緩存鍵結構"""
    source: CacheSource
    data_type: str
    symbol: str
    params_hash: str
    version: str = "v1"
    
    def to_string(self) -> str:
        """轉換為字符串格式的緩存鍵"""
        return f"tradingagents:{self.version}:{self.source.value}:{self.data_type}:{self.symbol}:{self.params_hash}"
    
    @classmethod
    def from_params(cls, source: CacheSource, data_type: str, symbol: str, params: Dict[str, Any] = None) -> 'CacheKey':
        """從參數創建緩存鍵"""
        params = params or {}
        params_str = json.dumps(params, sort_keys=True, default=str)
        params_hash = hashlib.sha256(params_str.encode()).hexdigest()[:8]  # 安全修復：使用SHA256替換MD5
        
        return cls(
            source=source,
            data_type=data_type,
            symbol=symbol.upper(),
            params_hash=params_hash
        )

@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return datetime.now() > self.expires_at
    
    def is_valid(self) -> bool:
        """檢查是否有效"""
        return not self.is_expired() and self.data is not None
    
    def access(self):
        """記錄訪問"""
        self.access_count += 1
        self.last_accessed = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'key': self.key,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'size_bytes': self.size_bytes,
            'is_expired': self.is_expired(),
            'is_valid': self.is_valid()
        }

@dataclass
class CacheStats:
    """緩存統計"""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cache_errors: int = 0
    total_size_bytes: int = 0
    entry_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        """緩存命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100
    
    @property
    def miss_rate(self) -> float:
        """緩存未命中率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_misses / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        """緩存錯誤率"""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_errors / self.total_requests) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'total_requests': self.total_requests,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_errors': self.cache_errors,
            'hit_rate': round(self.hit_rate, 2),
            'miss_rate': round(self.miss_rate, 2),
            'error_rate': round(self.error_rate, 2),
            'total_size_bytes': self.total_size_bytes,
            'entry_count': self.entry_count
        }

class CacheManager:
    """統一緩存管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化緩存管理器
        
        Args:
            config: 配置字典
        """
        self.config = config or DEFAULT_CONFIG
        self.redis_client = None
        self.redis_available = False
        
        # 緩存配置
        self.cache_config = self.config.get('cache', {})
        self.redis_config = self.cache_config.get('redis', {})
        self.enabled = self.cache_config.get('enabled', True)
        
        # 默認 TTL 配置（秒）
        self.default_ttl = {
            CacheSource.FINMIND: {
                'stock_price': 3600,      # 1小時
                'financial_data': 86400 * 7,  # 7天
                'market_index': 1800,     # 30分鐘
                'company_profile': 86400, # 1天
                'company_news': 900       # 15分鐘
            },
            CacheSource.FINNHUB: {
                'quote': 60,              # 1分鐘
                'stock_candles': 300,     # 5分鐘
                'company_profile': 3600,  # 1小時
                'company_news': 900,      # 15分鐘
                'financial_data': 1800,   # 30分鐘
                'recommendation': 3600,   # 1小時
                'price_target': 3600      # 1小時
            },
            CacheSource.ORCHESTRATOR: {
                'normalized_data': 1800,  # 30分鐘
                'quality_report': 3600,   # 1小時
                'cross_source_comparison': 1800  # 30分鐘
            }
        }
        
        # 統計信息
        self.stats = {
            CacheSource.FINMIND: CacheStats(),
            CacheSource.FINNHUB: CacheStats(),
            CacheSource.ORCHESTRATOR: CacheStats()
        }
        
        # 本地緩存（作為 Redis 的備用）
        self.local_cache = {}
        self.local_cache_access_times = deque(maxlen=1000)
        
        # 緩存協調
        self.invalidation_patterns = defaultdict(list)
        self.cross_source_dependencies = {}
        
        logger.info("緩存管理器初始化完成")
    
    async def initialize(self):
        """異步初始化緩存連接"""
        if not self.enabled:
            logger.info("緩存已禁用")
            return
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis 模塊不可用，將使用本地緩存")
            return
            
        # DigitalOcean 生產環境檢查 - 強制跳過 Redis 連接
        import os
        hostname = os.getenv('HOSTNAME', '')
        dyno = os.getenv('DYNO', '')
        
        # 檢查多種部署環境指標
        if (os.getenv('ENVIRONMENT') == 'production' or 
            'ondigitalocean.app' in hostname or
            'heroku' in hostname.lower() or
            dyno or  # Heroku dyno 存在
            os.path.exists('/workspace/.heroku')):  # Heroku 構建環境
            logger.warning(f"雲端部署環境偵測 (hostname: {hostname}), 跳過 Redis 連接，使用本地緩存")
            return
        
        try:
            # 初始化 Redis 連接
            redis_url = self.redis_config.get('url', 'redis://localhost:6379/0')
            max_connections = self.redis_config.get('max_connections', 10)
            
            self.redis_client = redis.from_url(
                redis_url,
                max_connections=max_connections,
                decode_responses=True
            )
            
            # 測試連接
            await self.redis_client.ping()
            self.redis_available = True
            
            logger.info(f"Redis 連接成功: {redis_url}")
            
        except Exception as e:
            logger.error(f"Redis 連接失敗: {e}")
            self.redis_available = False
    
    async def get(self, cache_key: CacheKey) -> Tuple[Any, CacheStatus]:
        """
        獲取緩存數據
        
        Args:
            cache_key: 緩存鍵
            
        Returns:
            (數據, 緩存狀態)
        """
        if not self.enabled:
            return None, CacheStatus.DISABLED
        
        key_str = cache_key.to_string()
        source_stats = self.stats[cache_key.source]
        source_stats.total_requests += 1
        
        try:
            # 嘗試從 Redis 獲取
            if self.redis_available:
                data = await self._get_from_redis(key_str)
                if data is not None:
                    source_stats.cache_hits += 1
                    return data, CacheStatus.HIT
            
            # 嘗試從本地緩存獲取
            if key_str in self.local_cache:
                entry = self.local_cache[key_str]
                if entry.is_valid():
                    entry.access()
                    source_stats.cache_hits += 1
                    return entry.data, CacheStatus.HIT
                else:
                    # 清理過期條目
                    del self.local_cache[key_str]
                    source_stats.cache_misses += 1
                    return None, CacheStatus.EXPIRED
            
            source_stats.cache_misses += 1
            return None, CacheStatus.MISS
            
        except Exception as e:
            logger.error(f"緩存獲取錯誤: {e}")
            source_stats.cache_errors += 1
            return None, CacheStatus.ERROR
    
    async def set(self, cache_key: CacheKey, data: Any, ttl: Optional[int] = None) -> bool:
        """
        設置緩存數據
        
        Args:
            cache_key: 緩存鍵
            data: 要緩存的數據
            ttl: 過期時間（秒），如果為 None 則使用默認值
            
        Returns:
            是否成功設置
        """
        if not self.enabled:
            return False
        
        if ttl is None:
            ttl = self._get_default_ttl(cache_key)
        
        key_str = cache_key.to_string()
        
        try:
            # 序列化數據
            serialized_data = self._serialize_data(data)
            data_size = len(serialized_data.encode('utf-8'))
            
            # 設置到 Redis
            if self.redis_available:
                success = await self._set_to_redis(key_str, serialized_data, ttl)
                if success:
                    self._update_cache_stats(cache_key.source, data_size, 1)
                    return True
            
            # 設置到本地緩存
            expires_at = datetime.now() + timedelta(seconds=ttl)
            entry = CacheEntry(
                key=key_str,
                data=data,
                created_at=datetime.now(),
                expires_at=expires_at,
                size_bytes=data_size
            )
            
            self.local_cache[key_str] = entry
            self._update_cache_stats(cache_key.source, data_size, 1)
            
            # 清理過期的本地緩存
            await self._cleanup_local_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"緩存設置錯誤: {e}")
            return False
    
    async def delete(self, cache_key: CacheKey) -> bool:
        """
        刪除緩存數據
        
        Args:
            cache_key: 緩存鍵
            
        Returns:
            是否成功刪除
        """
        if not self.enabled:
            return False
        
        key_str = cache_key.to_string()
        
        try:
            deleted = False
            
            # 從 Redis 刪除
            if self.redis_available:
                result = await self.redis_client.delete(key_str)
                if result > 0:
                    deleted = True
            
            # 從本地緩存刪除
            if key_str in self.local_cache:
                entry = self.local_cache[key_str]
                self._update_cache_stats(cache_key.source, -entry.size_bytes, -1)
                del self.local_cache[key_str]
                deleted = True
            
            return deleted
            
        except Exception as e:
            logger.error(f"緩存刪除錯誤: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str, source: Optional[CacheSource] = None) -> int:
        """
        根據模式批量失效緩存
        
        Args:
            pattern: 緩存鍵模式
            source: 數據源（可選）
            
        Returns:
            失效的緩存條目數量
        """
        if not self.enabled:
            return 0
        
        try:
            deleted_count = 0
            
            # 構建完整模式
            if source:
                full_pattern = f"tradingagents:*:{source.value}:{pattern}"
            else:
                full_pattern = f"tradingagents:*:{pattern}"
            
            # 從 Redis 批量刪除
            if self.redis_available:
                keys = await self.redis_client.keys(full_pattern)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
            
            # 從本地緩存批量刪除
            import re
            regex_pattern = pattern.replace('*', '.*')
            keys_to_delete = []
            
            for key in self.local_cache.keys():
                if re.match(regex_pattern, key):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                entry = self.local_cache[key]
                # 更新統計（需要從鍵中解析數據源）
                for src in CacheSource:
                    if src.value in key:
                        self._update_cache_stats(src, -entry.size_bytes, -1)
                        break
                del self.local_cache[key]
                deleted_count += 1
            
            logger.info(f"批量失效緩存: {pattern}, 刪除 {deleted_count} 個條目")
            return deleted_count
            
        except Exception as e:
            logger.error(f"批量失效緩存錯誤: {e}")
            return 0
    
    async def clear_source_cache(self, source: CacheSource) -> int:
        """
        清空特定數據源的所有緩存
        
        Args:
            source: 數據源
            
        Returns:
            清空的緩存條目數量
        """
        pattern = f"*:{source.value}:*"
        return await self.invalidate_pattern(pattern)
    
    async def setup_cross_source_dependencies(self, symbol: str, dependencies: Dict[CacheSource, List[str]]):
        """
        設置跨數據源依賴關係
        
        Args:
            symbol: 股票代號
            dependencies: 依賴關係映射
        """
        self.cross_source_dependencies[symbol] = dependencies
    
    async def invalidate_cross_source_cache(self, symbol: str, changed_source: CacheSource, data_type: str):
        """
        根據跨數據源依賴關係失效相關緩存
        
        Args:
            symbol: 股票代號
            changed_source: 變更的數據源
            data_type: 數據類型
        """
        if symbol not in self.cross_source_dependencies:
            return
        
        dependencies = self.cross_source_dependencies[symbol]
        
        # 失效依賴的緩存
        for dep_source, dep_data_types in dependencies.items():
            if dep_source != changed_source and data_type in dep_data_types:
                pattern = f"{dep_source.value}:*:{symbol}:*"
                await self.invalidate_pattern(pattern)
                logger.info(f"跨數據源緩存失效: {symbol} {dep_source.value}")
    
    def get_stats(self, source: Optional[CacheSource] = None) -> Dict[str, Any]:
        """
        獲取緩存統計信息
        
        Args:
            source: 數據源（可選）
            
        Returns:
            統計信息
        """
        if source:
            return {
                'source': source.value,
                'stats': self.stats[source].to_dict(),
                'local_cache_entries': len([k for k in self.local_cache.keys() if source.value in k]),
                'redis_available': self.redis_available
            }
        
        # 返回所有數據源的統計
        all_stats = {}
        total_stats = CacheStats()
        
        for src, stats in self.stats.items():
            all_stats[src.value] = stats.to_dict()
            total_stats.total_requests += stats.total_requests
            total_stats.cache_hits += stats.cache_hits
            total_stats.cache_misses += stats.cache_misses
            total_stats.cache_errors += stats.cache_errors
            total_stats.total_size_bytes += stats.total_size_bytes
            total_stats.entry_count += stats.entry_count
        
        return {
            'sources': all_stats,
            'total': total_stats.to_dict(),
            'local_cache_entries': len(self.local_cache),
            'redis_available': self.redis_available,
            'cache_enabled': self.enabled
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        緩存系統健康檢查
        
        Returns:
            健康狀態信息
        """
        health_info = {
            'cache_enabled': self.enabled,
            'redis_available': self.redis_available,
            'local_cache_entries': len(self.local_cache),
            'timestamp': datetime.now().isoformat()
        }
        
        if self.redis_available:
            try:
                # 測試 Redis 連接
                await self.redis_client.ping()
                redis_info = await self.redis_client.info()
                
                health_info['redis_status'] = 'healthy'
                health_info['redis_info'] = {
                    'used_memory': redis_info.get('used_memory_human', 'unknown'),
                    'connected_clients': redis_info.get('connected_clients', 0),
                    'total_commands_processed': redis_info.get('total_commands_processed', 0)
                }
            except Exception as e:
                health_info['redis_status'] = 'unhealthy'
                health_info['redis_error'] = str(e)
        else:
            health_info['redis_status'] = 'unavailable'
        
        return health_info
    
    # ==================== 私有方法 ====================
    
    async def _get_from_redis(self, key: str) -> Any:
        """從 Redis 獲取數據"""
        try:
            data = await self.redis_client.get(key)
            if data:
                return self._deserialize_data(data)
            return None
        except Exception as e:
            logger.error(f"Redis 獲取錯誤: {e}")
            return None
    
    async def _set_to_redis(self, key: str, data: str, ttl: int) -> bool:
        """設置數據到 Redis"""
        try:
            await self.redis_client.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Redis 設置錯誤: {e}")
            return False
    
    def _serialize_data(self, data: Any) -> str:
        """序列化數據"""
        return json.dumps(data, default=str, ensure_ascii=False)
    
    def _deserialize_data(self, data: str) -> Any:
        """反序列化數據"""
        return json.loads(data)
    
    def _get_default_ttl(self, cache_key: CacheKey) -> int:
        """獲取默認 TTL"""
        source_ttl = self.default_ttl.get(cache_key.source, {})
        return source_ttl.get(cache_key.data_type, 3600)  # 默認 1 小時
    
    def _update_cache_stats(self, source: CacheSource, size_delta: int, count_delta: int):
        """更新緩存統計"""
        stats = self.stats[source]
        stats.total_size_bytes += size_delta
        stats.entry_count += count_delta
    
    async def _cleanup_local_cache(self):
        """清理過期的本地緩存"""
        current_time = datetime.now()
        keys_to_delete = []
        
        for key, entry in self.local_cache.items():
            if entry.is_expired():
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            entry = self.local_cache[key]
            # 更新統計
            for src in CacheSource:
                if src.value in key:
                    self._update_cache_stats(src, -entry.size_bytes, -1)
                    break
            del self.local_cache[key]
        
        if keys_to_delete:
            logger.debug(f"清理過期本地緩存: {len(keys_to_delete)} 個條目")

# ==================== 工具函數 ====================

def create_cache_manager(config: Optional[Dict[str, Any]] = None) -> CacheManager:
    """創建緩存管理器的便利函數"""
    return CacheManager(config)

async def create_and_initialize_cache_manager(config: Optional[Dict[str, Any]] = None) -> CacheManager:
    """創建並初始化緩存管理器"""
    cache_manager = create_cache_manager(config)
    await cache_manager.initialize()
    return cache_manager