#!/usr/bin/env python3
"""
Storage Base - ART存儲系統基礎抽象類
天工 (TianGong) - 定義統一的存儲介面和基礎功能

此模組提供：
1. StorageBase - 所有存儲類的基礎抽象類
2. StorageConfig - 統一的存儲配置管理
3. StorageMetrics - 存儲性能指標追蹤
4. DataVersionInfo - 數據版本信息管理
5. IndexConfig - 索引配置和管理
"""

from typing import Dict, Any, List, Optional, Union, Generic, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import logging
import asyncio
import abc
import hashlib
import time
from collections import defaultdict, deque
import uuid

# Generic type for storage records
T = TypeVar('T')

class StorageBackend(Enum):
    """存儲後端類型"""
    JSON = "json"              # JSON文件存儲
    SQLITE = "sqlite"          # SQLite數據庫
    POSTGRESQL = "postgresql"  # PostgreSQL數據庫
    MONGODB = "mongodb"        # MongoDB文檔數據庫
    MEMORY = "memory"          # 內存存儲（測試用）

class StorageMode(Enum):
    """存儲模式"""
    DEVELOPMENT = "development"    # 開發模式
    STAGING = "staging"           # 測試模式
    PRODUCTION = "production"     # 生產模式

class IndexType(Enum):
    """索引類型"""
    PRIMARY = "primary"        # 主索引
    UNIQUE = "unique"          # 唯一索引
    COMPOSITE = "composite"    # 複合索引
    FULL_TEXT = "fulltext"     # 全文索引
    SPATIAL = "spatial"        # 空間索引

class CompressionType(Enum):
    """壓縮類型"""
    NONE = "none"
    GZIP = "gzip"
    ZLIB = "zlib"
    BROTLI = "brotli"

class StorageException(Exception):
    """存儲系統異常基類"""
    
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "STORAGE_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now()

class ConnectionException(StorageException):
    """連接異常"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "CONNECTION_ERROR", details)

class ValidationException(StorageException):
    """驗證異常"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class QueryException(StorageException):
    """查詢異常"""
    def __init__(self, message: str, details: Dict[str, Any] = None):
        super().__init__(message, "QUERY_ERROR", details)

@dataclass
class DataVersionInfo:
    """數據版本信息"""
    version: str
    created_at: str
    description: str = ""
    schema_version: str = "1.0.0"
    data_hash: str = ""
    size_bytes: int = 0
    record_count: int = 0
    migration_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'version': self.version,
            'created_at': self.created_at,
            'description': self.description,
            'schema_version': self.schema_version,
            'data_hash': self.data_hash,
            'size_bytes': self.size_bytes,
            'record_count': self.record_count,
            'migration_info': self.migration_info
        }

@dataclass
class IndexConfig:
    """索引配置"""
    name: str
    fields: List[str]
    index_type: IndexType = IndexType.COMPOSITE
    unique: bool = False
    partial_filter: Optional[Dict[str, Any]] = None
    collation: Optional[str] = None
    background: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'fields': self.fields,
            'index_type': self.index_type.value,
            'unique': self.unique,
            'partial_filter': self.partial_filter,
            'collation': self.collation,
            'background': self.background
        }

@dataclass
class StorageConfig:
    """統一存儲配置"""
    
    # 基本配置
    backend: StorageBackend = StorageBackend.JSON
    storage_path: str = "./art_storage"
    database_name: str = "art_system"
    mode: StorageMode = StorageMode.DEVELOPMENT
    
    # 連接配置
    connection_string: str = ""
    host: str = "localhost"
    port: int = 5432
    username: str = ""
    password: str = ""
    
    # 性能配置
    pool_size: int = 10
    max_connections: int = 20
    connection_timeout_seconds: int = 30
    query_timeout_seconds: int = 60
    
    # 緩存配置
    enable_caching: bool = True
    cache_size_mb: int = 256
    cache_ttl_seconds: int = 3600
    
    # 壓縮配置
    enable_compression: bool = True
    compression_type: CompressionType = CompressionType.GZIP
    compression_level: int = 6
    
    # 索引配置
    auto_create_indexes: bool = True
    index_configs: List[IndexConfig] = field(default_factory=list)
    
    # 備份配置
    enable_auto_backup: bool = True
    backup_interval_hours: int = 24
    backup_retention_days: int = 30
    
    # 監控配置
    enable_metrics: bool = True
    metrics_collection_interval_seconds: int = 60
    slow_query_threshold_ms: int = 1000
    
    # 安全配置
    enable_encryption: bool = False
    encryption_key: str = ""
    ssl_enabled: bool = False
    ssl_cert_path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'backend': self.backend.value,
            'storage_path': self.storage_path,
            'database_name': self.database_name,
            'mode': self.mode.value,
            'connection_string': self.connection_string,
            'host': self.host,
            'port': self.port,
            'username': self.username,
            'pool_size': self.pool_size,
            'max_connections': self.max_connections,
            'connection_timeout_seconds': self.connection_timeout_seconds,
            'query_timeout_seconds': self.query_timeout_seconds,
            'enable_caching': self.enable_caching,
            'cache_size_mb': self.cache_size_mb,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'enable_compression': self.enable_compression,
            'compression_type': self.compression_type.value,
            'compression_level': self.compression_level,
            'auto_create_indexes': self.auto_create_indexes,
            'index_configs': [idx.to_dict() for idx in self.index_configs],
            'enable_auto_backup': self.enable_auto_backup,
            'backup_interval_hours': self.backup_interval_hours,
            'backup_retention_days': self.backup_retention_days,
            'enable_metrics': self.enable_metrics,
            'metrics_collection_interval_seconds': self.metrics_collection_interval_seconds,
            'slow_query_threshold_ms': self.slow_query_threshold_ms,
            'enable_encryption': self.enable_encryption,
            'ssl_enabled': self.ssl_enabled,
            'ssl_cert_path': self.ssl_cert_path
        }

@dataclass
class StorageMetrics:
    """存儲性能指標"""
    
    # 基本統計
    total_records: int = 0
    total_size_bytes: int = 0
    active_connections: int = 0
    
    # 操作統計
    read_operations: int = 0
    write_operations: int = 0
    delete_operations: int = 0
    query_operations: int = 0
    
    # 性能指標
    average_read_time_ms: float = 0.0
    average_write_time_ms: float = 0.0
    average_query_time_ms: float = 0.0
    
    # 緩存統計
    cache_hits: int = 0
    cache_misses: int = 0
    cache_evictions: int = 0
    
    # 錯誤統計
    connection_errors: int = 0
    query_errors: int = 0
    timeout_errors: int = 0
    
    # 時間信息
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    uptime_seconds: float = 0.0
    
    def get_cache_hit_rate(self) -> float:
        """計算緩存命中率"""
        total = self.cache_hits + self.cache_misses
        return self.cache_hits / total if total > 0 else 0.0
    
    def get_error_rate(self) -> float:
        """計算錯誤率"""
        total_ops = self.read_operations + self.write_operations + self.query_operations
        total_errors = self.connection_errors + self.query_errors + self.timeout_errors
        return total_errors / total_ops if total_ops > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_records': self.total_records,
            'total_size_bytes': self.total_size_bytes,
            'active_connections': self.active_connections,
            'read_operations': self.read_operations,
            'write_operations': self.write_operations,
            'delete_operations': self.delete_operations,
            'query_operations': self.query_operations,
            'average_read_time_ms': self.average_read_time_ms,
            'average_write_time_ms': self.average_write_time_ms,
            'average_query_time_ms': self.average_query_time_ms,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_evictions': self.cache_evictions,
            'cache_hit_rate': self.get_cache_hit_rate(),
            'connection_errors': self.connection_errors,
            'query_errors': self.query_errors,
            'timeout_errors': self.timeout_errors,
            'error_rate': self.get_error_rate(),
            'last_updated': self.last_updated,
            'uptime_seconds': self.uptime_seconds
        }

class StorageBase(abc.ABC, Generic[T]):
    """存儲系統基礎抽象類"""
    
    def __init__(self, config: StorageConfig):
        """初始化存儲基類"""
        self.config = config
        self.metrics = StorageMetrics()
        self.logger = logging.getLogger(self.__class__.__name__)
        self._setup_logging()
        
        # 狀態管理
        self._initialized = False
        self._connected = False
        self._start_time = time.time()
        
        # 緩存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # 連接池（子類實現）
        self._connection_pool = None
        self._pg_pool = None  # PostgreSQL連接池
        
        # 索引管理
        self._indexes: Dict[str, IndexConfig] = {}
        
        # 版本管理
        self._current_version: Optional[DataVersionInfo] = None
    
    def _setup_logging(self):
        """設置日誌"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'%(asctime)s - {self.__class__.__name__} - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
            # 根據模式設置日誌級別
            if self.config.mode == StorageMode.DEVELOPMENT:
                self.logger.setLevel(logging.DEBUG)
            elif self.config.mode == StorageMode.STAGING:
                self.logger.setLevel(logging.INFO)
            else:
                self.logger.setLevel(logging.WARNING)
    
    @abc.abstractmethod
    async def initialize(self) -> bool:
        """初始化存儲系統"""
        pass
    
    @abc.abstractmethod
    async def connect(self) -> bool:
        """建立連接"""
        pass
    
    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """斷開連接"""
        pass
    
    @abc.abstractmethod
    async def create_record(self, record: T) -> str:
        """創建記錄"""
        pass
    
    @abc.abstractmethod
    async def get_record(self, record_id: str) -> Optional[T]:
        """獲取記錄"""
        pass
    
    @abc.abstractmethod
    async def update_record(self, record_id: str, updates: Dict[str, Any]) -> bool:
        """更新記錄"""
        pass
    
    @abc.abstractmethod
    async def delete_record(self, record_id: str) -> bool:
        """刪除記錄"""
        pass
    
    @abc.abstractmethod
    async def query_records(self, query: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[T]:
        """查詢記錄"""
        pass
    
    @abc.abstractmethod
    async def count_records(self, query: Dict[str, Any] = None) -> int:
        """計算記錄數量"""
        pass
    
    @abc.abstractmethod
    async def create_index(self, index_config: IndexConfig) -> bool:
        """創建索引"""
        pass
    
    async def get_metrics(self) -> StorageMetrics:
        """獲取存儲指標"""
        self.metrics.uptime_seconds = time.time() - self._start_time
        self.metrics.last_updated = datetime.now().isoformat()
        return self.metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 基本連接測試
            if not self._connected:
                await self.connect()
            
            # 性能測試
            start_time = time.time()
            await self.count_records({})
            query_time = (time.time() - start_time) * 1000
            
            return {
                'status': 'healthy',
                'connected': self._connected,
                'query_time_ms': query_time,
                'metrics': (await self.get_metrics()).to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'connected': self._connected,
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_cache_key(self, *args) -> str:
        """生成緩存鍵"""
        key_data = str(args)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """從緩存獲取數據"""
        if not self.config.enable_caching:
            return None
        
        if key in self._cache:
            # 檢查TTL
            if time.time() - self._cache_timestamps[key] < self.config.cache_ttl_seconds:
                self.metrics.cache_hits += 1
                return self._cache[key]
            else:
                # TTL過期，移除緩存
                del self._cache[key]
                del self._cache_timestamps[key]
                self.metrics.cache_evictions += 1
        
        self.metrics.cache_misses += 1
        return None
    
    def _set_to_cache(self, key: str, value: Any):
        """設置數據到緩存"""
        if not self.config.enable_caching:
            return
        
        # 簡單的LRU實現
        if len(self._cache) >= 1000:  # 限制緩存大小
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=self._cache_timestamps.get)
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
            self.metrics.cache_evictions += 1
        
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()
    
    def _clear_cache(self):
        """清空緩存"""
        self._cache.clear()
        self._cache_timestamps.clear()
    
    async def _record_operation(self, operation_type: str, duration_ms: float):
        """記錄操作指標"""
        if operation_type == 'read':
            self.metrics.read_operations += 1
            # 計算移動平均
            total_time = self.metrics.average_read_time_ms * (self.metrics.read_operations - 1)
            self.metrics.average_read_time_ms = (total_time + duration_ms) / self.metrics.read_operations
            
        elif operation_type == 'write':
            self.metrics.write_operations += 1
            total_time = self.metrics.average_write_time_ms * (self.metrics.write_operations - 1)
            self.metrics.average_write_time_ms = (total_time + duration_ms) / self.metrics.write_operations
            
        elif operation_type == 'query':
            self.metrics.query_operations += 1
            total_time = self.metrics.average_query_time_ms * (self.metrics.query_operations - 1)
            self.metrics.average_query_time_ms = (total_time + duration_ms) / self.metrics.query_operations
    
    def _generate_record_id(self) -> str:
        """生成記錄ID"""
        return f"{int(time.time() * 1000000)}_{uuid.uuid4().hex[:8]}"
    
    def _validate_record(self, record: Any) -> bool:
        """驗證記錄（子類可重寫）"""
        return True
    
    async def _create_pg_pool(self):
        """創建PostgreSQL連接池"""
        try:
            import asyncpg
            import os
            
            # 從環境變量或配置獲取數據庫連接信息
            connection_string = self.config.connection_string
            if not connection_string:
                db_user = os.getenv('DB_USER', 'postgres')
                db_password = os.getenv('DB_PASSWORD', '')
                db_name = os.getenv('DB_NAME', 'tradingagents')
                db_host = self.config.host
                db_port = self.config.port
                
                connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            
            self._pg_pool = await asyncpg.create_pool(
                connection_string,
                min_size=5,
                max_size=self.config.max_connections,
                command_timeout=self.config.query_timeout_seconds,
                server_settings={
                    'application_name': 'tradingagents_art_storage',
                    'timezone': 'Asia/Taipei'
                }
            )
            
            self.logger.info("PostgreSQL connection pool created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create PostgreSQL pool: {e}")
            return False
    
    async def _close_pg_pool(self):
        """關閉PostgreSQL連接池"""
        try:
            if self._pg_pool:
                await self._pg_pool.close()
                self._pg_pool = None
                self.logger.info("PostgreSQL connection pool closed")
        except Exception as e:
            self.logger.error(f"Failed to close PostgreSQL pool: {e}")

    async def cleanup(self):
        """清理資源"""
        try:
            await self.disconnect()
            await self._close_pg_pool()
            self._clear_cache()
            self.logger.info("Storage cleanup completed")
        except Exception as e:
            self.logger.error(f"Storage cleanup failed: {e}")
    
    def get_storage_info(self) -> Dict[str, Any]:
        """獲取存儲系統信息"""
        return {
            'backend': self.config.backend.value,
            'mode': self.config.mode.value,
            'database_name': self.config.database_name,
            'initialized': self._initialized,
            'connected': self._connected,
            'cache_enabled': self.config.enable_caching,
            'compression_enabled': self.config.enable_compression,
            'metrics_enabled': self.config.enable_metrics,
            'version': self._current_version.to_dict() if self._current_version else None
        }

# 工廠函數
def create_storage_config(
    backend: StorageBackend = StorageBackend.JSON,
    storage_path: str = "./art_storage",
    mode: StorageMode = StorageMode.DEVELOPMENT,
    **kwargs
) -> StorageConfig:
    """創建存儲配置"""
    config = StorageConfig(
        backend=backend,
        storage_path=storage_path,
        mode=mode
    )
    
    # 應用額外配置
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config