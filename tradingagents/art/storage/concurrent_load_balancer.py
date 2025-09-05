#!/usr/bin/env python3
"""
Concurrent Load Balancer - 並發查詢優化和負載均衡
天工 (TianGong) - 為ART存儲系統提供企業級並發處理和負載均衡

此模組提供：
1. QueryLoadBalancer - 查詢負載均衡器
2. ConcurrentQueryManager - 並發查詢管理器
3. ResourcePoolManager - 資源池管理
4. QueryPriorityScheduler - 查詢優先級調度
5. CircuitBreaker - 熔斷器模式
6. AdaptiveThrottling - 自適應限流
"""

from typing import Dict, Any, List, Optional, Union, Tuple, AsyncGenerator, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import hashlib
import logging
import math
import threading
import random
import statistics
from collections import defaultdict, OrderedDict, deque
import heapq
import weakref
from concurrent.futures import ThreadPoolExecutor, Future
import contextlib

class LoadBalancingStrategy(Enum):
    """負載均衡策略"""
    ROUND_ROBIN = "round_robin"           # 輪詢
    WEIGHTED_ROUND_ROBIN = "weighted_rr"  # 加權輪詢
    LEAST_CONNECTIONS = "least_conn"      # 最少連接
    LEAST_RESPONSE_TIME = "least_time"    # 最短響應時間
    CONSISTENT_HASH = "consistent_hash"   # 一致性哈希
    ADAPTIVE = "adaptive"                 # 自適應

class QueryPriority(Enum):
    """查詢優先級"""
    CRITICAL = "critical"     # 關鍵查詢
    HIGH = "high"            # 高優先級
    NORMAL = "normal"        # 普通優先級
    LOW = "low"              # 低優先級
    BACKGROUND = "background" # 後台查詢

class CircuitBreakerState(Enum):
    """熔斷器狀態"""
    CLOSED = "closed"         # 正常狀態
    OPEN = "open"            # 熔斷狀態
    HALF_OPEN = "half_open"  # 半開狀態

@dataclass
class QueryRequest:
    """查詢請求"""
    query_id: str
    sql: str
    params: List[Any] = field(default_factory=list)
    priority: QueryPriority = QueryPriority.NORMAL
    timeout: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age(self) -> float:
        """請求年齡（秒）"""
        return time.time() - self.created_at

@dataclass
class QueryResponse:
    """查詢響應"""
    query_id: str
    result: Any
    execution_time: float
    node_id: str
    cache_hit: bool = False
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DatabaseNode:
    """數據庫節點"""
    node_id: str
    host: str
    port: int
    weight: float = 1.0
    max_connections: int = 100
    current_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_health_check: float = 0.0
    is_healthy: bool = True
    is_active: bool = True
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def connection_utilization(self) -> float:
        """連接使用率"""
        return self.current_connections / self.max_connections
    
    @property
    def load_score(self) -> float:
        """負載分數（越低越好）"""
        return (
            self.connection_utilization * 0.4 +
            (1 - self.success_rate) * 0.3 +
            (self.avg_response_time / 1000) * 0.3
        )

class CircuitBreaker:
    """熔斷器"""
    
    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0, 
                 success_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """通過熔斷器調用函數"""
        async with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if time.time() - self.last_failure_time < self.timeout:
                    raise Exception("Circuit breaker is OPEN")
                else:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """成功回調"""
        async with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        """失敗回調"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN

class AdaptiveThrottling:
    """自適應限流器"""
    
    def __init__(self, initial_limit: int = 100, min_limit: int = 10, 
                 max_limit: int = 1000):
        self.current_limit = initial_limit
        self.min_limit = min_limit
        self.max_limit = max_limit
        
        self.request_count = 0
        self.success_count = 0
        self.window_start = time.time()
        self.window_duration = 60.0  # 1分鐘窗口
        
        self.semaphore = asyncio.Semaphore(self.current_limit)
        self._lock = asyncio.Lock()
    
    @contextlib.asynccontextmanager
    async def acquire(self):
        """獲取許可"""
        async with self.semaphore:
            async with self._lock:
                self.request_count += 1
            
            try:
                yield
                async with self._lock:
                    self.success_count += 1
            except:
                # 失敗不增加成功計數
                raise
            finally:
                await self._adjust_limit()
    
    async def _adjust_limit(self):
        """調整限流閾值"""
        current_time = time.time()
        
        async with self._lock:
            # 檢查是否需要調整窗口
            if current_time - self.window_start >= self.window_duration:
                success_rate = self.success_count / max(self.request_count, 1)
                
                # 根據成功率調整限流
                if success_rate > 0.95:  # 成功率高，增加限流
                    new_limit = min(int(self.current_limit * 1.1), self.max_limit)
                elif success_rate < 0.8:  # 成功率低，減少限流
                    new_limit = max(int(self.current_limit * 0.9), self.min_limit)
                else:
                    new_limit = self.current_limit
                
                if new_limit != self.current_limit:
                    self.current_limit = new_limit
                    # 創建新的信號量
                    self.semaphore = asyncio.Semaphore(self.current_limit)
                
                # 重置計數器
                self.request_count = 0
                self.success_count = 0
                self.window_start = current_time

class QueryPriorityScheduler:
    """查詢優先級調度器"""
    
    def __init__(self):
        self.priority_queues = {
            QueryPriority.CRITICAL: asyncio.Queue(),
            QueryPriority.HIGH: asyncio.Queue(),
            QueryPriority.NORMAL: asyncio.Queue(),
            QueryPriority.LOW: asyncio.Queue(),
            QueryPriority.BACKGROUND: asyncio.Queue()
        }
        
        self.priority_weights = {
            QueryPriority.CRITICAL: 100,
            QueryPriority.HIGH: 50,
            QueryPriority.NORMAL: 20,
            QueryPriority.LOW: 10,
            QueryPriority.BACKGROUND: 1
        }
        
        self._counters = {priority: 0 for priority in QueryPriority}
        self._lock = asyncio.Lock()
    
    async def enqueue(self, request: QueryRequest):
        """入隊查詢請求"""
        await self.priority_queues[request.priority].put(request)
    
    async def dequeue(self) -> Optional[QueryRequest]:
        """出隊查詢請求（按優先級）"""
        async with self._lock:
            # 使用加權輪詢選擇隊列
            for priority in QueryPriority:
                queue = self.priority_queues[priority]
                weight = self.priority_weights[priority]
                counter = self._counters[priority]
                
                if not queue.empty() and counter < weight:
                    self._counters[priority] += 1
                    try:
                        return queue.get_nowait()
                    except asyncio.QueueEmpty:
                        continue
            
            # 重置計數器
            self._counters = {priority: 0 for priority in QueryPriority}
            
            # 如果沒有找到，再嘗試一次
            for priority in QueryPriority:
                queue = self.priority_queues[priority]
                if not queue.empty():
                    try:
                        return queue.get_nowait()
                    except asyncio.QueueEmpty:
                        continue
            
            return None
    
    def get_queue_sizes(self) -> Dict[str, int]:
        """獲取各優先級隊列大小"""
        return {
            priority.value: queue.qsize() 
            for priority, queue in self.priority_queues.items()
        }

class ResourcePoolManager:
    """資源池管理器"""
    
    def __init__(self, max_connections: int = 100):
        self.max_connections = max_connections
        self.active_connections = 0
        self.connection_pool = asyncio.Queue(maxsize=max_connections)
        self.connection_stats = defaultdict(int)
        self._lock = asyncio.Lock()
        
        # 初始化連接池
        self._initialize_pool()
    
    def _initialize_pool(self):
        """初始化連接池"""
        for i in range(self.max_connections):
            connection_id = f"conn_{i:04d}"
            self.connection_pool.put_nowait(connection_id)
    
    @contextlib.asynccontextmanager
    async def acquire_connection(self):
        """獲取連接"""
        connection = await self.connection_pool.get()
        
        async with self._lock:
            self.active_connections += 1
            self.connection_stats[connection] += 1
        
        try:
            yield connection
        finally:
            async with self._lock:
                self.active_connections -= 1
            await self.connection_pool.put(connection)
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """獲取連接池統計"""
        return {
            'max_connections': self.max_connections,
            'active_connections': self.active_connections,
            'available_connections': self.connection_pool.qsize(),
            'connection_usage': dict(self.connection_stats)
        }

class QueryLoadBalancer:
    """查詢負載均衡器"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE):
        self.strategy = strategy
        self.nodes: List[DatabaseNode] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.throttling = AdaptiveThrottling()
        self.scheduler = QueryPriorityScheduler()
        self.resource_pool = ResourcePoolManager()
        
        # 負載均衡狀態
        self.current_node_index = 0
        self.request_counts = defaultdict(int)
        self._lock = asyncio.Lock()
        
        # 統計信息
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        
        # 啟動後台任務
        self._health_check_task = None
        self._start_background_tasks()
    
    def add_node(self, node: DatabaseNode):
        """添加數據庫節點"""
        self.nodes.append(node)
        self.circuit_breakers[node.node_id] = CircuitBreaker()
    
    def remove_node(self, node_id: str):
        """移除數據庫節點"""
        self.nodes = [node for node in self.nodes if node.node_id != node_id]
        self.circuit_breakers.pop(node_id, None)
    
    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """執行查詢"""
        async with self.throttling.acquire():
            # 入隊到優先級調度器
            await self.scheduler.enqueue(request)
            
            # 從調度器獲取請求
            scheduled_request = await self.scheduler.dequeue()
            if not scheduled_request:
                raise Exception("Failed to schedule query")
            
            # 選擇最佳節點
            node = await self._select_node(scheduled_request)
            if not node:
                raise Exception("No available nodes")
            
            # 執行查詢
            try:
                response = await self._execute_on_node(node, scheduled_request)
                await self._record_success(node)
                return response
            except Exception as e:
                await self._record_failure(node, e)
                
                # 重試邏輯
                if scheduled_request.retry_count < scheduled_request.max_retries:
                    scheduled_request.retry_count += 1
                    return await self.execute_query(scheduled_request)
                else:
                    raise e
    
    async def _select_node(self, request: QueryRequest) -> Optional[DatabaseNode]:
        """選擇最佳節點"""
        healthy_nodes = [node for node in self.nodes if node.is_healthy and node.is_active]
        
        if not healthy_nodes:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return await self._round_robin_select(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return await self._weighted_round_robin_select(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return await self._least_connections_select(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return await self._least_response_time_select(healthy_nodes)
        elif self.strategy == LoadBalancingStrategy.CONSISTENT_HASH:
            return await self._consistent_hash_select(healthy_nodes, request)
        elif self.strategy == LoadBalancingStrategy.ADAPTIVE:
            return await self._adaptive_select(healthy_nodes, request)
        else:
            return healthy_nodes[0]
    
    async def _round_robin_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """輪詢選擇"""
        async with self._lock:
            node = nodes[self.current_node_index % len(nodes)]
            self.current_node_index += 1
            return node
    
    async def _weighted_round_robin_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """加權輪詢選擇"""
        total_weight = sum(node.weight for node in nodes)
        random_weight = random.uniform(0, total_weight)
        
        current_weight = 0
        for node in nodes:
            current_weight += node.weight
            if random_weight <= current_weight:
                return node
        
        return nodes[0]
    
    async def _least_connections_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """最少連接選擇"""
        return min(nodes, key=lambda n: n.current_connections)
    
    async def _least_response_time_select(self, nodes: List[DatabaseNode]) -> DatabaseNode:
        """最短響應時間選擇"""
        return min(nodes, key=lambda n: n.avg_response_time)
    
    async def _consistent_hash_select(self, nodes: List[DatabaseNode], 
                                   request: QueryRequest) -> DatabaseNode:
        """一致性哈希選擇"""
        # 使用用戶ID或會話ID作為哈希鍵
        hash_key = request.user_id or request.session_id or request.query_id
        hash_value = hash(hash_key) % len(nodes)
        return nodes[hash_value]
    
    async def _adaptive_select(self, nodes: List[DatabaseNode], 
                             request: QueryRequest) -> DatabaseNode:
        """自適應選擇"""
        # 根據節點負載分數選擇最佳節點
        best_node = min(nodes, key=lambda n: n.load_score)
        
        # 如果最佳節點負載過高，使用加權隨機選擇
        if best_node.connection_utilization > 0.8:
            weights = [1 / max(node.load_score, 0.01) for node in nodes]
            total_weight = sum(weights)
            random_weight = random.uniform(0, total_weight)
            
            current_weight = 0
            for i, node in enumerate(nodes):
                current_weight += weights[i]
                if random_weight <= current_weight:
                    return node
        
        return best_node
    
    async def _execute_on_node(self, node: DatabaseNode, 
                              request: QueryRequest) -> QueryResponse:
        """在指定節點執行查詢"""
        circuit_breaker = self.circuit_breakers[node.node_id]
        
        async def execute():
            async with self.resource_pool.acquire_connection() as connection:
                start_time = time.time()
                
                # 模擬查詢執行
                await asyncio.sleep(0.01 + random.uniform(0, 0.05))
                
                execution_time = (time.time() - start_time) * 1000
                
                # 模擬查詢結果
                result = {
                    "query_id": request.query_id,
                    "data": f"Result for {request.sql}",
                    "node": node.node_id,
                    "connection": connection
                }
                
                return QueryResponse(
                    query_id=request.query_id,
                    result=result,
                    execution_time=execution_time,
                    node_id=node.node_id,
                    retry_count=request.retry_count
                )
        
        return await circuit_breaker.call(execute)
    
    async def _record_success(self, node: DatabaseNode):
        """記錄成功"""
        async with self._lock:
            node.successful_requests += 1
            node.total_requests += 1
            self.successful_requests += 1
            self.total_requests += 1
    
    async def _record_failure(self, node: DatabaseNode, error: Exception):
        """記錄失敗"""
        async with self._lock:
            node.failed_requests += 1
            node.total_requests += 1
            self.failed_requests += 1
            self.total_requests += 1
    
    def _start_background_tasks(self):
        """啟動後台任務"""
        self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while True:
            try:
                await asyncio.sleep(30)  # 每30秒檢查一次
                await self._perform_health_checks()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Health check error: {e}")
    
    async def _perform_health_checks(self):
        """執行健康檢查"""
        for node in self.nodes:
            try:
                # 模擬健康檢查
                await asyncio.sleep(0.01)
                
                # 更新健康狀態
                node.is_healthy = node.success_rate > 0.5
                node.last_health_check = time.time()
                
            except Exception:
                node.is_healthy = False
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取負載均衡統計"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.successful_requests / max(self.total_requests, 1),
            'nodes': [
                {
                    'node_id': node.node_id,
                    'is_healthy': node.is_healthy,
                    'success_rate': node.success_rate,
                    'avg_response_time': node.avg_response_time,
                    'connection_utilization': node.connection_utilization,
                    'load_score': node.load_score
                }
                for node in self.nodes
            ],
            'queue_sizes': self.scheduler.get_queue_sizes(),
            'throttling_limit': self.throttling.current_limit,
            'resource_pool': self.resource_pool.get_pool_stats()
        }
    
    async def shutdown(self):
        """關閉負載均衡器"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

class ConcurrentQueryManager:
    """並發查詢管理器"""
    
    def __init__(self, max_concurrent_queries: int = 100):
        self.max_concurrent_queries = max_concurrent_queries
        self.load_balancer = QueryLoadBalancer()
        self.active_queries: Dict[str, QueryRequest] = {}
        self.query_results: Dict[str, QueryResponse] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent_queries)
        self._lock = asyncio.Lock()
    
    async def submit_query(self, request: QueryRequest) -> str:
        """提交查詢"""
        async with self._lock:
            self.active_queries[request.query_id] = request
        
        # 異步執行查詢
        asyncio.create_task(self._execute_query_async(request))
        return request.query_id
    
    async def _execute_query_async(self, request: QueryRequest):
        """異步執行查詢"""
        async with self._semaphore:
            try:
                response = await self.load_balancer.execute_query(request)
                
                async with self._lock:
                    self.query_results[request.query_id] = response
                    self.active_queries.pop(request.query_id, None)
                    
            except Exception as e:
                error_response = QueryResponse(
                    query_id=request.query_id,
                    result=None,
                    execution_time=0,
                    node_id="",
                    error=str(e)
                )
                
                async with self._lock:
                    self.query_results[request.query_id] = error_response
                    self.active_queries.pop(request.query_id, None)
    
    async def get_result(self, query_id: str, timeout: Optional[float] = None) -> QueryResponse:
        """獲取查詢結果"""
        start_time = time.time()
        
        while True:
            async with self._lock:
                if query_id in self.query_results:
                    return self.query_results.pop(query_id)
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Query {query_id} timeout")
            
            await asyncio.sleep(0.1)
    
    def add_database_node(self, node: DatabaseNode):
        """添加數據庫節點"""
        self.load_balancer.add_node(node)
    
    def get_manager_stats(self) -> Dict[str, Any]:
        """獲取管理器統計"""
        return {
            'active_queries': len(self.active_queries),
            'pending_results': len(self.query_results),
            'max_concurrent': self.max_concurrent_queries,
            'load_balancer': self.load_balancer.get_stats()
        }
    
    async def shutdown(self):
        """關閉管理器"""
        await self.load_balancer.shutdown()

# 工廠函數
def create_load_balancer(
    strategy: str = "adaptive",
    max_connections: int = 100,
    **kwargs
) -> QueryLoadBalancer:
    """創建負載均衡器"""
    
    return QueryLoadBalancer(LoadBalancingStrategy(strategy))

def create_concurrent_manager(
    max_concurrent: int = 100,
    load_balancing_strategy: str = "adaptive",
    **kwargs
) -> ConcurrentQueryManager:
    """創建並發查詢管理器"""
    
    manager = ConcurrentQueryManager(max_concurrent)
    manager.load_balancer.strategy = LoadBalancingStrategy(load_balancing_strategy)
    
    return manager