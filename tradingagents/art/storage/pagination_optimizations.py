#!/usr/bin/env python3
"""
Pagination Optimizations - 分頁查詢和批次處理優化
天工 (TianGong) - 為ART存儲系統提供高效分頁和批次處理

此模組提供：
1. PaginationManager - 高效分頁管理
2. CursorPagination - 基於游標的分頁
3. BatchQueryProcessor - 批次查詢處理器
4. SmartCaching - 智能分頁緩存
5. AdaptiveBatching - 自適應批次大小
6. QueryPrefetcher - 查詢預取器
"""

from typing import Dict, Any, List, Optional, Union, Tuple, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import hashlib
import logging
import math
from collections import defaultdict, OrderedDict
import bisect

class PaginationType(Enum):
    """分頁類型"""
    OFFSET = "offset"          # 傳統LIMIT/OFFSET分頁
    CURSOR = "cursor"          # 基於游標的分頁
    KEYSET = "keyset"          # 基於鍵集的分頁
    HYBRID = "hybrid"          # 混合分頁策略

class BatchStrategy(Enum):
    """批次策略"""
    FIXED_SIZE = "fixed_size"        # 固定批次大小
    ADAPTIVE = "adaptive"            # 自適應批次大小
    TIME_BASED = "time_based"        # 基於時間的批次
    MEMORY_BASED = "memory_based"    # 基於內存的批次

@dataclass
class PaginationConfig:
    """分頁配置"""
    default_page_size: int = 100
    max_page_size: int = 1000
    pagination_type: PaginationType = PaginationType.CURSOR
    enable_prefetch: bool = True
    prefetch_pages: int = 2
    cache_ttl_seconds: int = 300  # 5分鐘
    enable_count_optimization: bool = True
    use_estimated_count: bool = True

@dataclass
class BatchConfig:
    """批次處理配置"""
    default_batch_size: int = 1000
    max_batch_size: int = 10000
    batch_strategy: BatchStrategy = BatchStrategy.ADAPTIVE
    batch_timeout_ms: float = 5000.0
    memory_threshold_mb: int = 100
    enable_parallel_batches: bool = True
    max_concurrent_batches: int = 5

@dataclass
class PaginationResult:
    """分頁結果"""
    records: List[Dict[str, Any]] = field(default_factory=list)
    
    # 分頁信息
    current_page: int = 1
    page_size: int = 100
    total_pages: int = 0
    total_count: int = 0
    estimated_count: bool = False
    
    # 游標信息
    start_cursor: Optional[str] = None
    end_cursor: Optional[str] = None
    has_previous: bool = False
    has_next: bool = False
    
    # 性能信息
    query_time_ms: float = 0.0
    cache_hit: bool = False
    prefetch_triggered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'records': self.records,
            'pagination': {
                'current_page': self.current_page,
                'page_size': self.page_size,
                'total_pages': self.total_pages,
                'total_count': self.total_count,
                'estimated_count': self.estimated_count,
                'start_cursor': self.start_cursor,
                'end_cursor': self.end_cursor,
                'has_previous': self.has_previous,
                'has_next': self.has_next
            },
            'performance': {
                'query_time_ms': self.query_time_ms,
                'cache_hit': self.cache_hit,
                'prefetch_triggered': self.prefetch_triggered
            }
        }

class PaginationCache:
    """分頁緩存系統"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, Tuple[PaginationResult, float]] = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0
    
    def _generate_cache_key(self, query_hash: str, page: int, page_size: int, 
                           cursor: Optional[str] = None) -> str:
        """生成緩存鍵"""
        key_parts = [query_hash, str(page), str(page_size)]
        if cursor:
            key_parts.append(cursor)
        return "_".join(key_parts)
    
    def get(self, query_hash: str, page: int, page_size: int, 
            cursor: Optional[str] = None) -> Optional[PaginationResult]:
        """獲取緩存項"""
        cache_key = self._generate_cache_key(query_hash, page, page_size, cursor)
        
        if cache_key in self.cache:
            result, timestamp = self.cache[cache_key]
            
            # 檢查是否過期
            if time.time() - timestamp <= self.ttl_seconds:
                # 移動到最前面（LRU）
                self.cache.move_to_end(cache_key)
                self.hit_count += 1
                result.cache_hit = True
                return result
            else:
                # 過期，刪除
                del self.cache[cache_key]
        
        self.miss_count += 1
        return None
    
    def set(self, query_hash: str, page: int, page_size: int, result: PaginationResult,
            cursor: Optional[str] = None):
        """設置緩存項"""
        cache_key = self._generate_cache_key(query_hash, page, page_size, cursor)
        
        # 如果緩存滿了，移除最舊的項目
        if len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        
        self.cache[cache_key] = (result, time.time())
    
    def invalidate_query(self, query_hash: str):
        """失效特定查詢的所有緩存"""
        keys_to_remove = []
        for key in self.cache.keys():
            if key.startswith(query_hash):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
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

class CursorPagination:
    """基於游標的分頁實現"""
    
    def __init__(self, cursor_field: str = "id", order_desc: bool = True):
        self.cursor_field = cursor_field
        self.order_desc = order_desc
    
    def encode_cursor(self, record: Dict[str, Any]) -> str:
        """編碼游標"""
        cursor_value = record.get(self.cursor_field)
        if cursor_value is None:
            raise ValueError(f"Cursor field '{self.cursor_field}' not found in record")
        
        cursor_data = {
            'field': self.cursor_field,
            'value': cursor_value,
            'desc': self.order_desc
        }
        
        cursor_json = json.dumps(cursor_data, sort_keys=True)
        cursor_bytes = cursor_json.encode('utf-8')
        
        # 簡單的base64編碼
        import base64
        return base64.b64encode(cursor_bytes).decode('ascii')
    
    def decode_cursor(self, cursor: str) -> Dict[str, Any]:
        """解碼游標"""
        try:
            import base64
            cursor_bytes = base64.b64decode(cursor.encode('ascii'))
            cursor_json = cursor_bytes.decode('utf-8')
            return json.loads(cursor_json)
        except Exception as e:
            raise ValueError(f"Invalid cursor format: {e}")
    
    def build_cursor_condition(self, cursor: str) -> Tuple[str, List[Any]]:
        """構建游標條件"""
        cursor_data = self.decode_cursor(cursor)
        field = cursor_data['field']
        value = cursor_data['value']
        desc = cursor_data['desc']
        
        if desc:
            condition = f"{field} < ?"
        else:
            condition = f"{field} > ?"
        
        return condition, [value]
    
    def get_order_clause(self) -> str:
        """獲取排序子句"""
        order = "DESC" if self.order_desc else "ASC"
        return f"{self.cursor_field} {order}"

class SmartPrefetcher:
    """智能預取器"""
    
    def __init__(self, prefetch_pages: int = 2, hit_threshold: float = 0.7):
        self.prefetch_pages = prefetch_pages
        self.hit_threshold = hit_threshold
        self.access_patterns: Dict[str, List[int]] = defaultdict(list)
        self.prefetch_queue: List[Tuple[str, int, int]] = []
        
    def record_access(self, query_hash: str, page: int):
        """記錄頁面訪問"""
        self.access_patterns[query_hash].append(page)
        
        # 只保留最近100次訪問
        if len(self.access_patterns[query_hash]) > 100:
            self.access_patterns[query_hash] = self.access_patterns[query_hash][-100:]
    
    def should_prefetch(self, query_hash: str, current_page: int) -> List[int]:
        """決定是否應該預取以及預取哪些頁面"""
        if query_hash not in self.access_patterns:
            # 新查詢，預取下一頁
            return [current_page + 1]
        
        accesses = self.access_patterns[query_hash]
        if len(accesses) < 5:  # 訪問次數太少，不做預測
            return [current_page + 1]
        
        # 分析訪問模式
        sequential_access_ratio = self._calculate_sequential_ratio(accesses)
        
        if sequential_access_ratio > self.hit_threshold:
            # 順序訪問模式，預取後續頁面
            return [current_page + i for i in range(1, self.prefetch_pages + 1)]
        else:
            # 隨機訪問模式，預取可能的頁面
            likely_pages = self._predict_next_pages(accesses, current_page)
            return likely_pages[:self.prefetch_pages]
    
    def _calculate_sequential_ratio(self, accesses: List[int]) -> float:
        """計算順序訪問比例"""
        sequential_count = 0
        for i in range(1, len(accesses)):
            if accesses[i] == accesses[i-1] + 1:
                sequential_count += 1
        
        return sequential_count / (len(accesses) - 1) if len(accesses) > 1 else 0
    
    def _predict_next_pages(self, accesses: List[int], current_page: int) -> List[int]:
        """預測下一個可能訪問的頁面"""
        # 簡單的基於頻率的預測
        page_counts = defaultdict(int)
        for page in accesses[-20:]:  # 只考慮最近20次訪問
            page_counts[page] += 1
        
        # 找到最常訪問的頁面附近的頁面
        popular_pages = sorted(page_counts.keys(), key=lambda p: page_counts[p], reverse=True)
        
        predictions = []
        for page in popular_pages[:5]:
            for offset in [-1, 1, -2, 2]:
                predicted_page = page + offset
                if predicted_page > 0 and predicted_page != current_page:
                    predictions.append(predicted_page)
        
        return list(dict.fromkeys(predictions))  # 去重並保持順序

class AdaptiveBatchProcessor:
    """自適應批次處理器"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.batch_performance: Dict[int, List[float]] = defaultdict(list)
        self.current_batch_size = config.default_batch_size
        self.pending_operations: List[Tuple[str, List[Any], asyncio.Future]] = []
        self._lock = asyncio.Lock()
    
    async def add_operation(self, sql: str, params: List[Any] = None) -> Any:
        """添加操作到批次"""
        future = asyncio.Future()
        
        async with self._lock:
            self.pending_operations.append((sql, params or [], future))
            
            # 檢查是否達到批次大小或超時
            if (len(self.pending_operations) >= self.current_batch_size or 
                self._should_process_batch()):
                asyncio.create_task(self._process_batch())
        
        return await future
    
    def _should_process_batch(self) -> bool:
        """決定是否應該處理當前批次"""
        if not self.pending_operations:
            return False
        
        # 檢查第一個操作的等待時間
        first_op_time = getattr(self.pending_operations[0], '_timestamp', time.time())
        wait_time = (time.time() - first_op_time) * 1000
        
        return wait_time > self.config.batch_timeout_ms
    
    async def _process_batch(self):
        """處理當前批次"""
        async with self._lock:
            if not self.pending_operations:
                return
            
            operations = self.pending_operations.copy()
            self.pending_operations.clear()
        
        start_time = time.time()
        
        try:
            # 按SQL分組操作
            grouped_operations = defaultdict(list)
            for sql, params, future in operations:
                grouped_operations[sql].append((params, future))
            
            # 處理每組操作
            for sql, param_futures in grouped_operations.items():
                await self._execute_batch_sql(sql, param_futures)
            
            # 記錄性能
            execution_time = (time.time() - start_time) * 1000
            self._record_batch_performance(len(operations), execution_time)
            
        except Exception as e:
            # 設置所有future的異常
            for _, _, future in operations:
                if not future.done():
                    future.set_exception(e)
    
    async def _execute_batch_sql(self, sql: str, param_futures: List[Tuple[List[Any], asyncio.Future]]):
        """執行批次SQL"""
        # 這裡需要實際的數據庫連接來執行
        # 暫時模擬執行
        for params, future in param_futures:
            if not future.done():
                future.set_result(f"Executed: {sql} with {params}")
    
    def _record_batch_performance(self, batch_size: int, execution_time: float):
        """記錄批次性能"""
        self.batch_performance[batch_size].append(execution_time)
        
        # 只保留最近50次記錄
        if len(self.batch_performance[batch_size]) > 50:
            self.batch_performance[batch_size] = self.batch_performance[batch_size][-50:]
        
        # 調整批次大小
        self._adjust_batch_size()
    
    def _adjust_batch_size(self):
        """調整批次大小"""
        if self.config.batch_strategy != BatchStrategy.ADAPTIVE:
            return
        
        # 分析不同批次大小的性能
        size_performance = {}
        for batch_size, times in self.batch_performance.items():
            if len(times) >= 5:  # 需要足夠的樣本
                avg_time = sum(times) / len(times)
                throughput = batch_size / (avg_time / 1000)  # 每秒處理的記錄數
                size_performance[batch_size] = throughput
        
        if len(size_performance) >= 2:
            # 選擇吞吐量最高的批次大小
            best_size = max(size_performance.keys(), key=lambda s: size_performance[s])
            
            # 平滑調整
            if best_size != self.current_batch_size:
                adjustment = (best_size - self.current_batch_size) * 0.1
                self.current_batch_size = max(
                    self.config.default_batch_size // 2,
                    min(self.config.max_batch_size, 
                        int(self.current_batch_size + adjustment))
                )

class PaginationManager:
    """分頁管理器"""
    
    def __init__(self, config: PaginationConfig):
        self.config = config
        self.cache = PaginationCache(ttl_seconds=config.cache_ttl_seconds)
        self.prefetcher = SmartPrefetcher(config.prefetch_pages) if config.enable_prefetch else None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def paginate_query(self, 
                            sql: str, 
                            params: List[Any] = None,
                            page: int = 1,
                            page_size: Optional[int] = None,
                            cursor: Optional[str] = None,
                            count_query: Optional[str] = None,
                            executor: Optional[Callable] = None) -> PaginationResult:
        """執行分頁查詢"""
        
        if page_size is None:
            page_size = self.config.default_page_size
        
        page_size = min(page_size, self.config.max_page_size)
        
        # 生成查詢哈希
        query_hash = self._generate_query_hash(sql, params)
        
        # 檢查緩存
        cached_result = self.cache.get(query_hash, page, page_size, cursor)
        if cached_result:
            return cached_result
        
        start_time = time.time()
        
        try:
            # 根據分頁類型執行查詢
            if self.config.pagination_type == PaginationType.CURSOR and cursor:
                result = await self._cursor_paginate(sql, params, cursor, page_size, executor)
            else:
                result = await self._offset_paginate(sql, params, page, page_size, count_query, executor)
            
            result.query_time_ms = (time.time() - start_time) * 1000
            
            # 緩存結果
            self.cache.set(query_hash, page, page_size, result, cursor)
            
            # 記錄訪問模式並觸發預取
            if self.prefetcher:
                self.prefetcher.record_access(query_hash, page)
                prefetch_pages = self.prefetcher.should_prefetch(query_hash, page)
                if prefetch_pages:
                    asyncio.create_task(self._prefetch_pages(
                        sql, params, prefetch_pages, page_size, executor, query_hash
                    ))
                    result.prefetch_triggered = True
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pagination query failed: {e}")
            raise
    
    async def _offset_paginate(self, 
                              sql: str, 
                              params: List[Any],
                              page: int,
                              page_size: int,
                              count_query: Optional[str],
                              executor: Optional[Callable]) -> PaginationResult:
        """OFFSET分頁"""
        
        offset = (page - 1) * page_size
        
        # 構建分頁查詢
        paginated_sql = f"{sql} LIMIT {page_size} OFFSET {offset}"
        
        # 執行數據查詢
        if executor:
            records, _ = await executor(paginated_sql, params)
        else:
            records = []  # 模擬結果
        
        # 獲取總數
        total_count = 0
        estimated_count = False
        
        if count_query and self.config.enable_count_optimization:
            if executor:
                count_result, _ = await executor(count_query, params)
                total_count = count_result[0]['count'] if count_result else 0
            else:
                total_count = 10000  # 模擬總數
        
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0
        
        return PaginationResult(
            records=records,
            current_page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_count=total_count,
            estimated_count=estimated_count,
            has_previous=page > 1,
            has_next=page < total_pages
        )
    
    async def _cursor_paginate(self,
                              sql: str,
                              params: List[Any],
                              cursor: str,
                              page_size: int,
                              executor: Optional[Callable]) -> PaginationResult:
        """游標分頁"""
        
        cursor_pagination = CursorPagination()
        
        try:
            # 解析游標並構建條件
            cursor_condition, cursor_params = cursor_pagination.build_cursor_condition(cursor)
            
            # 構建游標查詢
            if "WHERE" in sql.upper():
                cursor_sql = f"{sql} AND {cursor_condition}"
            else:
                cursor_sql = f"{sql} WHERE {cursor_condition}"
            
            cursor_sql += f" ORDER BY {cursor_pagination.get_order_clause()} LIMIT {page_size + 1}"
            
            all_params = (params or []) + cursor_params
            
            # 執行查詢
            if executor:
                all_records, _ = await executor(cursor_sql, all_params)
            else:
                all_records = []  # 模擬結果
            
            # 檢查是否有下一頁
            has_next = len(all_records) > page_size
            if has_next:
                all_records = all_records[:page_size]
            
            # 生成新游標
            start_cursor = None
            end_cursor = None
            
            if all_records:
                start_cursor = cursor_pagination.encode_cursor(all_records[0])
                end_cursor = cursor_pagination.encode_cursor(all_records[-1])
            
            return PaginationResult(
                records=all_records,
                page_size=page_size,
                start_cursor=start_cursor,
                end_cursor=end_cursor,
                has_previous=True,  # 既然有cursor，說明有前頁
                has_next=has_next
            )
            
        except Exception as e:
            self.logger.error(f"Cursor pagination failed: {e}")
            raise
    
    async def _prefetch_pages(self,
                             sql: str,
                             params: List[Any],
                             prefetch_pages: List[int],
                             page_size: int,
                             executor: Optional[Callable],
                             query_hash: str):
        """預取頁面"""
        try:
            tasks = []
            for page in prefetch_pages:
                if not self.cache.get(query_hash, page, page_size):
                    task = self._offset_paginate(sql, params, page, page_size, None, executor)
                    tasks.append((page, task))
            
            if tasks:
                results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
                
                for (page, _), result in zip(tasks, results):
                    if isinstance(result, PaginationResult):
                        self.cache.set(query_hash, page, page_size, result)
                        
        except Exception as e:
            self.logger.warning(f"Prefetch failed: {e}")
    
    def _generate_query_hash(self, sql: str, params: List[Any] = None) -> str:
        """生成查詢哈希"""
        query_content = f"{sql}_{str(params or [])}"
        return hashlib.md5(query_content.encode()).hexdigest()[:16]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        return self.cache.get_stats()

# 工廠函數
def create_pagination_manager(
    default_page_size: int = 100,
    max_page_size: int = 1000,
    pagination_type: str = "cursor",
    enable_prefetch: bool = True,
    **kwargs
) -> PaginationManager:
    """創建分頁管理器"""
    
    config = PaginationConfig(
        default_page_size=default_page_size,
        max_page_size=max_page_size,
        pagination_type=PaginationType(pagination_type),
        enable_prefetch=enable_prefetch,
        **kwargs
    )
    
    return PaginationManager(config)

def create_batch_processor(
    default_batch_size: int = 1000,
    max_batch_size: int = 10000,
    batch_strategy: str = "adaptive",
    **kwargs
) -> AdaptiveBatchProcessor:
    """創建批次處理器"""
    
    config = BatchConfig(
        default_batch_size=default_batch_size,
        max_batch_size=max_batch_size,
        batch_strategy=BatchStrategy(batch_strategy),
        **kwargs
    )
    
    return AdaptiveBatchProcessor(config)