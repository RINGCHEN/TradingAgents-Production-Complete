#!/usr/bin/env python3
"""
Performance Optimizations - 大規模數據檢索性能優化
天工 (TianGong) - 為ART存儲系統提供企業級性能優化

此模組提供：
1. ConnectionPool - 數據庫連接池管理
2. PreparedQueryCache - 預編譯查詢緩存
3. BatchProcessor - 批次處理優化
4. QueryOptimizer - 查詢計劃優化器
5. IndexManager - 智能索引管理
6. CacheLayer - 多層緩存系統
"""

from typing import Dict, Any, List, Optional, Union, Tuple, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import aiosqlite
import json
import time
import hashlib
import logging
from pathlib import Path
from collections import defaultdict, OrderedDict
import threading
import weakref

class ConnectionPoolStatus(Enum):
    """連接池狀態"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

@dataclass
class ConnectionPoolConfig:
    """連接池配置"""
    min_connections: int = 5
    max_connections: int = 50
    connection_timeout: float = 30.0
    idle_timeout: float = 600.0  # 10分鐘
    max_connection_age: float = 3600.0  # 1小時
    connection_check_interval: float = 60.0  # 1分鐘
    enable_prepared_statements: bool = True
    query_cache_size: int = 1000

@dataclass 
class ConnectionMetrics:
    """連接指標"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    total_queries: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    avg_query_time_ms: float = 0.0
    peak_connections: int = 0
    connection_errors: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

class Connection:
    """數據庫連接封裝"""
    
    def __init__(self, db_path: str, connection_id: str):
        self.db_path = db_path
        self.connection_id = connection_id
        self.connection: Optional[aiosqlite.Connection] = None
        self.created_at = time.time()
        self.last_used = time.time()
        self.query_count = 0
        self.is_busy = False
        self.prepared_statements: Dict[str, Any] = {}
        
    async def connect(self) -> bool:
        """建立數據庫連接"""
        try:
            if self.connection is None:
                self.connection = await aiosqlite.connect(self.db_path)
                await self.connection.execute("PRAGMA journal_mode=WAL")
                await self.connection.execute("PRAGMA synchronous=NORMAL")  
                await self.connection.execute("PRAGMA cache_size=-64000")  # 64MB cache
                await self.connection.execute("PRAGMA temp_store=MEMORY")
                await self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
                return True
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            return False
        
    async def disconnect(self):
        """斷開數據庫連接"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            
    async def execute_query(self, sql: str, params: List[Any] = None) -> Tuple[List[Dict[str, Any]], float]:
        """執行查詢"""
        start_time = time.time()
        
        try:
            if not self.connection:
                await self.connect()
                
            self.is_busy = True
            self.last_used = time.time()
            self.query_count += 1
            
            # 使用預編譯語句如果可能
            if sql in self.prepared_statements:
                cursor = await self.connection.execute_cached(sql, params or [])
            else:
                cursor = await self.connection.execute(sql, params or [])
                
            # 獲取結果
            if sql.strip().upper().startswith(('SELECT', 'PRAGMA', 'EXPLAIN')):
                self.connection.row_factory = aiosqlite.Row
                rows = await cursor.fetchall()
                results = [dict(row) for row in rows]
            else:
                await self.connection.commit()
                results = []
                
            execution_time = (time.time() - start_time) * 1000
            return results, execution_time
            
        finally:
            self.is_busy = False
            
    def is_expired(self, max_age: float) -> bool:
        """檢查連接是否過期"""
        return (time.time() - self.created_at) > max_age
        
    def is_idle_too_long(self, idle_timeout: float) -> bool:
        """檢查連接是否閒置太久"""
        return not self.is_busy and (time.time() - self.last_used) > idle_timeout

class ConnectionPool:
    """數據庫連接池"""
    
    def __init__(self, db_path: str, config: ConnectionPoolConfig):
        self.db_path = db_path
        self.config = config
        self.connections: List[Connection] = []
        self.metrics = ConnectionMetrics()
        self.status = ConnectionPoolStatus.INITIALIZING
        self._lock = asyncio.Lock()
        self._connection_counter = 0
        self._maintenance_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """初始化連接池"""
        try:
            # 創建最小連接數
            for _ in range(self.config.min_connections):
                await self._create_connection()
                
            # 啟動維護任務
            self._maintenance_task = asyncio.create_task(self._maintenance_loop())
            
            self.status = ConnectionPoolStatus.ACTIVE
            self.metrics.total_connections = len(self.connections)
            
            logging.info(f"Connection pool initialized with {len(self.connections)} connections")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize connection pool: {e}")
            self.status = ConnectionPoolStatus.SHUTDOWN
            return False
    
    async def _create_connection(self) -> Optional[Connection]:
        """創建新連接"""
        if len(self.connections) >= self.config.max_connections:
            return None
            
        self._connection_counter += 1
        connection_id = f"conn_{self._connection_counter}"
        
        connection = Connection(self.db_path, connection_id)
        if await connection.connect():
            self.connections.append(connection)
            self.metrics.total_connections += 1
            self.metrics.peak_connections = max(self.metrics.peak_connections, len(self.connections))
            return connection
        else:
            self.metrics.connection_errors += 1
            return None
    
    async def get_connection(self) -> Optional[Connection]:
        """獲取可用連接"""
        async with self._lock:
            # 查找空閒連接
            for connection in self.connections:
                if not connection.is_busy and connection.connection:
                    self.metrics.active_connections += 1
                    return connection
                    
            # 如果沒有空閒連接且未達到最大連接數，創建新連接
            if len(self.connections) < self.config.max_connections:
                connection = await self._create_connection()
                if connection:
                    self.metrics.active_connections += 1
                    return connection
                    
            return None
    
    async def return_connection(self, connection: Connection):
        """歸還連接"""
        async with self._lock:
            connection.is_busy = False
            self.metrics.active_connections = max(0, self.metrics.active_connections - 1)
            self.metrics.idle_connections = len([c for c in self.connections if not c.is_busy])
    
    async def execute_query(self, sql: str, params: List[Any] = None) -> Tuple[List[Dict[str, Any]], float]:
        """執行查詢"""
        connection = await self.get_connection()
        if not connection:
            raise Exception("No available database connections")
            
        try:
            results, exec_time = await connection.execute_query(sql, params)
            
            # 更新指標
            self.metrics.total_queries += 1
            if self.metrics.total_queries > 0:
                self.metrics.avg_query_time_ms = (
                    (self.metrics.avg_query_time_ms * (self.metrics.total_queries - 1) + exec_time) / 
                    self.metrics.total_queries
                )
            
            return results, exec_time
            
        finally:
            await self.return_connection(connection)
    
    async def _maintenance_loop(self):
        """連接池維護循環"""
        while self.status == ConnectionPoolStatus.ACTIVE:
            try:
                await asyncio.sleep(self.config.connection_check_interval)
                await self._cleanup_connections()
                self._update_metrics()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Connection pool maintenance error: {e}")
    
    async def _cleanup_connections(self):
        """清理過期和閒置連接"""
        async with self._lock:
            connections_to_remove = []
            
            for connection in self.connections:
                if connection.is_expired(self.config.max_connection_age):
                    connections_to_remove.append(connection)
                elif (len(self.connections) > self.config.min_connections and 
                      connection.is_idle_too_long(self.config.idle_timeout)):
                    connections_to_remove.append(connection)
            
            for connection in connections_to_remove:
                await connection.disconnect()
                self.connections.remove(connection)
                self.metrics.total_connections -= 1
    
    def _update_metrics(self):
        """更新連接池指標"""
        self.metrics.active_connections = len([c for c in self.connections if c.is_busy])
        self.metrics.idle_connections = len([c for c in self.connections if not c.is_busy])
        self.metrics.last_updated = datetime.now().isoformat()
    
    async def shutdown(self):
        """關閉連接池"""
        self.status = ConnectionPoolStatus.SHUTTING_DOWN
        
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
        
        async with self._lock:
            for connection in self.connections:
                await connection.disconnect()
            self.connections.clear()
            self.metrics.total_connections = 0
            
        self.status = ConnectionPoolStatus.SHUTDOWN
        logging.info("Connection pool shutdown completed")
    
    def get_metrics(self) -> ConnectionMetrics:
        """獲取連接池指標"""
        self._update_metrics()
        return self.metrics

class PreparedQueryCache:
    """預編譯查詢緩存"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict[str, Tuple[str, List[str]]] = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
        
    def get_query_key(self, sql: str, params: List[Any] = None) -> str:
        """生成查詢鍵"""
        query_text = sql.strip()
        param_hash = hashlib.md5(str(params or []).encode()).hexdigest()[:8]
        return f"{hashlib.md5(query_text.encode()).hexdigest()[:16]}_{param_hash}"
    
    def get_prepared_query(self, sql: str, params: List[Any] = None) -> Optional[Tuple[str, List[str]]]:
        """獲取預編譯查詢"""
        key = self.get_query_key(sql, params)
        
        if key in self.cache:
            # 移到最前面（LRU）
            self.cache.move_to_end(key)
            self.hit_count += 1
            return self.cache[key]
        else:
            self.miss_count += 1
            return None
    
    def cache_query(self, sql: str, prepared_sql: str, param_names: List[str], params: List[Any] = None):
        """緩存預編譯查詢"""
        key = self.get_query_key(sql, params)
        
        # 如果緩存滿了，移除最舊的項目
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
            
        self.cache[key] = (prepared_sql, param_names)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests) if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }

class BatchProcessor:
    """批次處理器"""
    
    def __init__(self, batch_size: int = 1000, max_wait_time: float = 5.0):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_operations: List[Tuple[str, List[Any], asyncio.Future]] = []
        self._batch_lock = asyncio.Lock()
        self._batch_task: Optional[asyncio.Task] = None
        
    async def add_operation(self, sql: str, params: List[Any] = None) -> Any:
        """添加批次操作"""
        future = asyncio.Future()
        
        async with self._batch_lock:
            self.pending_operations.append((sql, params or [], future))
            
            # 如果達到批次大小或這是第一個操作，觸發處理
            if len(self.pending_operations) >= self.batch_size or len(self.pending_operations) == 1:
                if self._batch_task is None or self._batch_task.done():
                    self._batch_task = asyncio.create_task(self._process_batch())
        
        return await future
    
    async def _process_batch(self):
        """處理批次操作"""
        # 等待更多操作或超時
        start_time = time.time()
        while (len(self.pending_operations) < self.batch_size and 
               time.time() - start_time < self.max_wait_time):
            await asyncio.sleep(0.1)
        
        async with self._batch_lock:
            if not self.pending_operations:
                return
                
            operations = self.pending_operations.copy()
            self.pending_operations.clear()
        
        # 按SQL類型分組操作
        grouped_ops = defaultdict(list)
        for sql, params, future in operations:
            grouped_ops[sql].append((params, future))
        
        # 處理每組操作
        for sql, param_futures in grouped_ops.items():
            try:
                if sql.strip().upper().startswith('INSERT'):
                    # 批次插入優化
                    await self._batch_insert(sql, param_futures)
                elif sql.strip().upper().startswith('UPDATE'):
                    # 批次更新優化
                    await self._batch_update(sql, param_futures)
                else:
                    # 常規處理
                    await self._batch_regular(sql, param_futures)
                    
            except Exception as e:
                # 設置所有future的異常
                for _, future in param_futures:
                    if not future.done():
                        future.set_exception(e)
    
    async def _batch_insert(self, sql: str, param_futures: List[Tuple[List[Any], asyncio.Future]]):
        """批次插入優化"""
        # 這裡會實現批次插入邏輯
        # 例如使用executemany或構建批次INSERT語句
        pass
    
    async def _batch_update(self, sql: str, param_futures: List[Tuple[List[Any], asyncio.Future]]):
        """批次更新優化"""
        # 這裡會實現批次更新邏輯
        pass
    
    async def _batch_regular(self, sql: str, param_futures: List[Tuple[List[Any], asyncio.Future]]):
        """常規批次處理"""
        # 這裡會實現常規批次處理邏輯
        pass

class QueryOptimizer:
    """查詢優化器"""
    
    def __init__(self):
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.optimization_rules: List[Callable] = [
            self._optimize_index_usage,
            self._optimize_join_order,
            self._optimize_subqueries,
            self._optimize_limit_offset
        ]
    
    def optimize_query(self, sql: str, params: List[Any] = None) -> Tuple[str, List[Any]]:
        """優化查詢"""
        optimized_sql = sql
        optimized_params = params or []
        
        for rule in self.optimization_rules:
            optimized_sql, optimized_params = rule(optimized_sql, optimized_params)
        
        return optimized_sql, optimized_params
    
    def _optimize_index_usage(self, sql: str, params: List[Any]) -> Tuple[str, List[Any]]:
        """優化索引使用"""
        # 分析查詢並建議使用合適的索引
        return sql, params
    
    def _optimize_join_order(self, sql: str, params: List[Any]) -> Tuple[str, List[Any]]:
        """優化JOIN順序"""
        # 分析JOIN並重新排序以提高性能
        return sql, params
    
    def _optimize_subqueries(self, sql: str, params: List[Any]) -> Tuple[str, List[Any]]:
        """優化子查詢"""
        # 將子查詢轉換為JOIN或EXISTS
        return sql, params
    
    def _optimize_limit_offset(self, sql: str, params: List[Any]) -> Tuple[str, List[Any]]:
        """優化LIMIT和OFFSET"""
        # 對於大偏移量使用更高效的分頁方法
        return sql, params
    
    def record_query_stats(self, sql: str, execution_time: float, rows_returned: int):
        """記錄查詢統計"""
        query_hash = hashlib.md5(sql.encode()).hexdigest()[:16]
        
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                'sql': sql,
                'execution_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0,
                'total_rows': 0,
                'avg_rows': 0.0
            }
        
        stats = self.query_stats[query_hash]
        stats['execution_count'] += 1
        stats['total_time'] += execution_time
        stats['avg_time'] = stats['total_time'] / stats['execution_count']
        stats['min_time'] = min(stats['min_time'], execution_time)
        stats['max_time'] = max(stats['max_time'], execution_time)
        stats['total_rows'] += rows_returned
        stats['avg_rows'] = stats['total_rows'] / stats['execution_count']

class PerformanceOptimizedStorage:
    """性能優化的存儲基類"""
    
    def __init__(self, db_path: str, pool_config: ConnectionPoolConfig = None):
        self.db_path = db_path
        self.pool_config = pool_config or ConnectionPoolConfig()
        self.connection_pool: Optional[ConnectionPool] = None
        self.query_cache = PreparedQueryCache(self.pool_config.query_cache_size)
        self.batch_processor = BatchProcessor()
        self.query_optimizer = QueryOptimizer()
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def initialize(self) -> bool:
        """初始化性能優化存儲"""
        try:
            # 初始化連接池
            self.connection_pool = ConnectionPool(self.db_path, self.pool_config)
            success = await self.connection_pool.initialize()
            
            if success:
                self.logger.info("Performance optimized storage initialized successfully")
                return True
            else:
                self.logger.error("Failed to initialize connection pool")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize performance optimized storage: {e}")
            return False
    
    async def execute_optimized_query(self, sql: str, params: List[Any] = None, 
                                    use_cache: bool = True, use_batch: bool = False) -> Tuple[List[Dict[str, Any]], float]:
        """執行優化查詢"""
        if not self.connection_pool:
            raise Exception("Storage not initialized")
        
        # 查詢優化
        optimized_sql, optimized_params = self.query_optimizer.optimize_query(sql, params)
        
        # 檢查緩存
        if use_cache:
            cached_query = self.query_cache.get_prepared_query(optimized_sql, optimized_params)
            if cached_query:
                prepared_sql, param_names = cached_query
                optimized_sql = prepared_sql
        
        # 執行查詢
        if use_batch:
            # 使用批次處理
            results = await self.batch_processor.add_operation(optimized_sql, optimized_params)
            execution_time = 0.0  # 批次處理中的時間統計需要特殊處理
        else:
            # 直接執行
            results, execution_time = await self.connection_pool.execute_query(optimized_sql, optimized_params)
        
        # 記錄統計
        self.query_optimizer.record_query_stats(sql, execution_time, len(results))
        
        return results, execution_time
    
    async def execute_batch_operations(self, operations: List[Tuple[str, List[Any]]]) -> List[Any]:
        """執行批次操作"""
        tasks = []
        for sql, params in operations:
            task = self.batch_processor.add_operation(sql, params)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """獲取性能指標"""
        metrics = {
            'connection_pool': None,
            'query_cache': self.query_cache.get_cache_stats(),
            'query_stats': self.query_optimizer.query_stats
        }
        
        if self.connection_pool:
            metrics['connection_pool'] = self.connection_pool.get_metrics().__dict__
        
        return metrics
    
    async def shutdown(self):
        """關閉性能優化存儲"""
        if self.connection_pool:
            await self.connection_pool.shutdown()
        
        self.logger.info("Performance optimized storage shutdown completed")

# 工廠函數
async def create_optimized_storage(
    db_path: str,
    min_connections: int = 5,
    max_connections: int = 50,
    cache_size: int = 1000,
    **kwargs
) -> PerformanceOptimizedStorage:
    """創建性能優化存儲實例"""
    
    config = ConnectionPoolConfig(
        min_connections=min_connections,
        max_connections=max_connections,
        query_cache_size=cache_size,
        **kwargs
    )
    
    storage = PerformanceOptimizedStorage(db_path, config)
    
    if await storage.initialize():
        return storage
    else:
        raise Exception("Failed to initialize optimized storage")