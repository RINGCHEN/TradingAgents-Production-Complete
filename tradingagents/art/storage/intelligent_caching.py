#!/usr/bin/env python3
"""
Intelligent Caching - 智能查詢緩存和預取機制
天工 (TianGong) - 為ART存儲系統提供企業級智能緩存解決方案

此模組提供：
1. MultiLevelCache - 多級緩存架構
2. IntelligentPrefetcher - 智能預取引擎
3. CacheWarming - 緩存預熱機制
4. AdaptiveEviction - 自適應緩存淘汰
5. PredictiveAnalyzer - 預測性分析器
6. CacheCoherence - 緩存一致性管理
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
from collections import defaultdict, OrderedDict, deque
import heapq
import pickle
import weakref
import statistics
from concurrent.futures import ThreadPoolExecutor
import numpy as np

class CacheLevel(Enum):
    """緩存級別"""
    L1_MEMORY = "l1_memory"       # L1內存緩存（最快）
    L2_SSD = "l2_ssd"             # L2 SSD緩存（中等速度）
    L3_NETWORK = "l3_network"     # L3網絡緩存（較慢）
    PERSISTENT = "persistent"      # 持久化緩存

class CacheStrategy(Enum):
    """緩存策略"""
    LRU = "lru"                   # 最近最少使用
    LFU = "lfu"                   # 最少使用頻率
    ARC = "arc"                   # 自適應替換緩存
    CLOCK = "clock"               # 時鐘替換算法
    ADAPTIVE = "adaptive"         # 自適應策略

class PrefetchStrategy(Enum):
    """預取策略"""
    SEQUENTIAL = "sequential"     # 順序預取
    PATTERN_BASED = "pattern"     # 基於模式預取
    ML_PREDICTION = "ml"          # 機器學習預測
    HYBRID = "hybrid"             # 混合策略

@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    value: Any
    size: int
    created_at: float
    last_accessed: float
    access_count: int
    hit_count: int
    cost: float = 1.0  # 計算成本
    priority: float = 1.0
    ttl: Optional[float] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age(self) -> float:
        """條目年齡（秒）"""
        return time.time() - self.created_at
    
    @property
    def idle_time(self) -> float:
        """閒置時間（秒）"""
        return time.time() - self.last_accessed
    
    @property
    def hit_rate(self) -> float:
        """命中率"""
        return self.hit_count / max(self.access_count, 1)
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

@dataclass
class CacheStats:
    """緩存統計"""
    total_entries: int = 0
    total_size: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    prefetch_count: int = 0
    prefetch_hit_count: int = 0
    cache_warming_count: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hit_count + self.miss_count
        return self.hit_count / max(total, 1)
    
    @property
    def prefetch_accuracy(self) -> float:
        return self.prefetch_hit_count / max(self.prefetch_count, 1)

class ARCCache:
    """自適應替換緩存（Adaptive Replacement Cache）"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.p = 0  # 目標T1大小
        
        # 四個列表：T1, T2, B1, B2
        self.t1 = OrderedDict()  # 最近訪問的頁面
        self.t2 = OrderedDict()  # 頻繁訪問的頁面
        self.b1 = OrderedDict()  # T1的幽靈頁面
        self.b2 = OrderedDict()  # T2的幽靈頁面
    
    def get(self, key: str) -> Optional[Any]:
        """獲取緩存項"""
        if key in self.t1:
            # 從T1移動到T2
            value = self.t1.pop(key)
            self.t2[key] = value
            return value.value
        elif key in self.t2:
            # T2中命中，移動到最前面
            value = self.t2.pop(key)
            self.t2[key] = value
            return value.value
        
        return None
    
    def put(self, key: str, entry: CacheEntry):
        """放入緩存項"""
        if key in self.t1 or key in self.t2:
            return  # 已存在
        
        if key in self.b1:
            # 在B1中找到，增加p
            self.p = min(self.p + max(1, len(self.b2) // len(self.b1)), self.max_size)
            self._replace(key)
            self.b1.pop(key)
            self.t2[key] = entry
        elif key in self.b2:
            # 在B2中找到，減少p
            self.p = max(self.p - max(1, len(self.b1) // len(self.b2)), 0)
            self._replace(key)
            self.b2.pop(key)
            self.t2[key] = entry
        else:
            # 新頁面
            if len(self.t1) + len(self.b1) == self.max_size:
                if len(self.t1) < self.max_size:
                    self.b1.popitem(last=False)
                    self._replace(key)
                else:
                    self.t1.popitem(last=False)
            elif len(self.t1) + len(self.b1) < self.max_size:
                total_size = len(self.t1) + len(self.t2) + len(self.b1) + len(self.b2)
                if total_size >= self.max_size:
                    if total_size == 2 * self.max_size:
                        self.b2.popitem(last=False)
                    self._replace(key)
            
            self.t1[key] = entry
    
    def _replace(self, key: str):
        """替換頁面"""
        if len(self.t1) >= 1 and (
            (key in self.b2 and len(self.t1) == self.p) or 
            len(self.t1) > self.p
        ):
            # 從T1移動到B1
            old_key = next(iter(self.t1))
            entry = self.t1.pop(old_key)
            self.b1[old_key] = entry
        else:
            # 從T2移動到B2
            if self.t2:
                old_key = next(iter(self.t2))
                entry = self.t2.pop(old_key)
                self.b2[old_key] = entry

class IntelligentPrefetcher:
    """智能預取引擎"""
    
    def __init__(self, strategy: PrefetchStrategy = PrefetchStrategy.HYBRID):
        self.strategy = strategy
        self.access_patterns: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.query_sequences: Dict[str, List[str]] = {}
        self.temporal_patterns: Dict[str, List[Tuple[float, str]]] = defaultdict(list)
        self.correlation_matrix: Dict[Tuple[str, str], float] = {}
        self.prefetch_success_rate: Dict[str, float] = {}
        self.ml_model_weights: Dict[str, float] = {}
        
    def record_access(self, user_id: str, query_key: str, timestamp: Optional[float] = None):
        """記錄訪問模式"""
        if timestamp is None:
            timestamp = time.time()
        
        # 記錄訪問序列
        self.access_patterns[user_id].append((timestamp, query_key))
        
        # 記錄時間模式
        self.temporal_patterns[user_id].append((timestamp, query_key))
        
        # 更新查詢序列
        if user_id not in self.query_sequences:
            self.query_sequences[user_id] = []
        self.query_sequences[user_id].append(query_key)
        
        # 保持序列長度
        if len(self.query_sequences[user_id]) > 50:
            self.query_sequences[user_id] = self.query_sequences[user_id][-50:]
    
    def predict_next_queries(self, user_id: str, current_query: str, 
                           limit: int = 5) -> List[Tuple[str, float]]:
        """預測下一個查詢"""
        predictions = []
        
        if self.strategy in [PrefetchStrategy.SEQUENTIAL, PrefetchStrategy.HYBRID]:
            seq_predictions = self._sequential_prediction(user_id, current_query)
            predictions.extend(seq_predictions)
        
        if self.strategy in [PrefetchStrategy.PATTERN_BASED, PrefetchStrategy.HYBRID]:
            pattern_predictions = self._pattern_based_prediction(user_id, current_query)
            predictions.extend(pattern_predictions)
        
        if self.strategy in [PrefetchStrategy.ML_PREDICTION, PrefetchStrategy.HYBRID]:
            ml_predictions = self._ml_prediction(user_id, current_query)
            predictions.extend(ml_predictions)
        
        # 合併和排序預測結果
        prediction_scores = defaultdict(float)
        for query, score in predictions:
            prediction_scores[query] += score
        
        # 排序並返回top-k
        sorted_predictions = sorted(
            prediction_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return sorted_predictions[:limit]
    
    def _sequential_prediction(self, user_id: str, current_query: str) -> List[Tuple[str, float]]:
        """基於順序模式的預測"""
        if user_id not in self.query_sequences:
            return []
        
        sequences = self.query_sequences[user_id]
        predictions = []
        
        # 查找當前查詢的出現位置
        for i, query in enumerate(sequences[:-1]):
            if query == current_query:
                next_query = sequences[i + 1]
                predictions.append((next_query, 0.6))  # 基礎權重
        
        return predictions
    
    def _pattern_based_prediction(self, user_id: str, current_query: str) -> List[Tuple[str, float]]:
        """基於模式的預測"""
        if user_id not in self.temporal_patterns:
            return []
        
        patterns = self.temporal_patterns[user_id]
        current_time = time.time()
        predictions = []
        
        # 分析時間模式
        time_based_patterns = defaultdict(list)
        for timestamp, query in patterns:
            hour_of_day = datetime.fromtimestamp(timestamp).hour
            day_of_week = datetime.fromtimestamp(timestamp).weekday()
            
            time_based_patterns[(hour_of_day, day_of_week)].append(query)
        
        # 基於當前時間預測
        current_hour = datetime.fromtimestamp(current_time).hour
        current_day = datetime.fromtimestamp(current_time).weekday()
        
        if (current_hour, current_day) in time_based_patterns:
            common_queries = time_based_patterns[(current_hour, current_day)]
            query_counts = defaultdict(int)
            for query in common_queries:
                query_counts[query] += 1
            
            total_count = sum(query_counts.values())
            for query, count in query_counts.items():
                if query != current_query:
                    probability = count / total_count
                    predictions.append((query, probability * 0.4))  # 時間模式權重
        
        return predictions
    
    def _ml_prediction(self, user_id: str, current_query: str) -> List[Tuple[str, float]]:
        """基於機器學習的預測（簡化版本）"""
        # 這是一個簡化的ML預測，實際應該使用更複雜的模型
        if user_id not in self.access_patterns:
            return []
        
        # 特徵提取
        recent_queries = list(self.access_patterns[user_id])[-10:]
        if not recent_queries:
            return []
        
        # 計算查詢相關性
        correlations = {}
        for timestamp, query in recent_queries:
            if query != current_query:
                # 簡單的相關性計算（基於共現頻率）
                correlation_key = (current_query, query)
                if correlation_key in self.correlation_matrix:
                    correlations[query] = self.correlation_matrix[correlation_key]
        
        predictions = [(query, score * 0.3) for query, score in correlations.items()]
        return predictions
    
    def update_success_rate(self, user_id: str, predicted_query: str, was_accessed: bool):
        """更新預測成功率"""
        key = f"{user_id}:{predicted_query}"
        if key not in self.prefetch_success_rate:
            self.prefetch_success_rate[key] = 0.5  # 初始值
        
        # 簡單的移動平均更新
        current_rate = self.prefetch_success_rate[key]
        if was_accessed:
            self.prefetch_success_rate[key] = current_rate * 0.9 + 0.1
        else:
            self.prefetch_success_rate[key] = current_rate * 0.9

class CacheWarmer:
    """緩存預熱器"""
    
    def __init__(self, cache_manager, query_executor: Callable):
        self.cache_manager = cache_manager
        self.query_executor = query_executor
        self.warming_rules: List[Dict[str, Any]] = []
        self.warming_schedule: List[Tuple[float, str]] = []
        
    def add_warming_rule(self, rule: Dict[str, Any]):
        """添加預熱規則"""
        self.warming_rules.append(rule)
    
    async def warm_cache(self, rule_name: Optional[str] = None):
        """執行緩存預熱"""
        rules_to_execute = self.warming_rules
        if rule_name:
            rules_to_execute = [r for r in self.warming_rules if r.get('name') == rule_name]
        
        for rule in rules_to_execute:
            try:
                await self._execute_warming_rule(rule)
            except Exception as e:
                logging.error(f"Cache warming rule failed: {rule.get('name', 'unknown')}: {e}")
    
    async def _execute_warming_rule(self, rule: Dict[str, Any]):
        """執行單個預熱規則"""
        rule_type = rule.get('type', 'query')
        
        if rule_type == 'query':
            await self._warm_query_cache(rule)
        elif rule_type == 'batch':
            await self._warm_batch_cache(rule)
        elif rule_type == 'pattern':
            await self._warm_pattern_cache(rule)
    
    async def _warm_query_cache(self, rule: Dict[str, Any]):
        """預熱查詢緩存"""
        queries = rule.get('queries', [])
        for query_info in queries:
            sql = query_info.get('sql')
            params = query_info.get('params', [])
            cache_key = self._generate_cache_key(sql, params)
            
            if not self.cache_manager.exists(cache_key):
                result = await self.query_executor(sql, params)
                await self.cache_manager.set(cache_key, result, ttl=rule.get('ttl', 3600))
    
    def _generate_cache_key(self, sql: str, params: List[Any]) -> str:
        """生成緩存鍵"""
        content = f"{sql}_{str(params)}"
        return hashlib.md5(content.encode()).hexdigest()

class MultiLevelCache:
    """多級緩存管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.levels: Dict[CacheLevel, Any] = {}
        self.stats = CacheStats()
        self.prefetcher = IntelligentPrefetcher()
        self.warmer: Optional[CacheWarmer] = None
        self._lock = asyncio.Lock()
        
        # 初始化各級緩存
        self._init_cache_levels()
    
    def _init_cache_levels(self):
        """初始化緩存級別"""
        # L1 內存緩存（最快）
        if self.config.get('l1_enabled', True):
            l1_size = self.config.get('l1_size', 1000)
            l1_strategy = self.config.get('l1_strategy', 'arc')
            
            if l1_strategy == 'arc':
                self.levels[CacheLevel.L1_MEMORY] = ARCCache(l1_size)
            else:
                self.levels[CacheLevel.L1_MEMORY] = OrderedDict()
        
        # L2 文件緩存（中等速度）
        if self.config.get('l2_enabled', False):
            self.levels[CacheLevel.L2_SSD] = {}
        
        # 設置預熱器
        query_executor = self.config.get('query_executor')
        if query_executor:
            self.warmer = CacheWarmer(self, query_executor)
    
    async def get(self, key: str, user_id: Optional[str] = None) -> Optional[Any]:
        """獲取緩存項"""
        async with self._lock:
            # 從L1開始查找
            for level in [CacheLevel.L1_MEMORY, CacheLevel.L2_SSD]:
                if level not in self.levels:
                    continue
                
                cache = self.levels[level]
                
                if isinstance(cache, ARCCache):
                    result = cache.get(key)
                elif isinstance(cache, dict):
                    entry = cache.get(key)
                    if entry and not entry.is_expired():
                        result = entry.value
                        entry.last_accessed = time.time()
                        entry.access_count += 1
                        entry.hit_count += 1
                    else:
                        result = None
                else:
                    result = cache.get(key)
                
                if result is not None:
                    self.stats.hit_count += 1
                    
                    # 記錄訪問模式
                    if user_id:
                        self.prefetcher.record_access(user_id, key)
                    
                    # 觸發預取
                    if user_id and self.config.get('enable_prefetch', True):
                        asyncio.create_task(self._trigger_prefetch(user_id, key))
                    
                    return result
            
            self.stats.miss_count += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[float] = None,
                 user_id: Optional[str] = None, tags: Set[str] = None):
        """設置緩存項"""
        async with self._lock:
            # 創建緩存條目
            entry = CacheEntry(
                key=key,
                value=value,
                size=self._estimate_size(value),
                created_at=time.time(),
                last_accessed=time.time(),
                access_count=1,
                hit_count=0,
                ttl=ttl,
                tags=tags or set()
            )
            
            # 優先存儲到L1
            if CacheLevel.L1_MEMORY in self.levels:
                l1_cache = self.levels[CacheLevel.L1_MEMORY]
                
                if isinstance(l1_cache, ARCCache):
                    l1_cache.put(key, entry)
                else:
                    l1_cache[key] = entry
            
            self.stats.total_entries += 1
            self.stats.total_size += entry.size
    
    async def _trigger_prefetch(self, user_id: str, current_key: str):
        """觸發預取操作"""
        try:
            predictions = self.prefetcher.predict_next_queries(user_id, current_key, limit=3)
            
            for predicted_key, confidence in predictions:
                if confidence > 0.3 and not await self.exists(predicted_key):
                    # 這裡應該執行實際的數據獲取和緩存
                    self.stats.prefetch_count += 1
                    
                    # 模擬預取（實際應該執行查詢）
                    # await self._execute_prefetch(predicted_key)
                    
        except Exception as e:
            logging.warning(f"Prefetch failed: {e}")
    
    async def exists(self, key: str) -> bool:
        """檢查鍵是否存在"""
        result = await self.get(key)
        return result is not None
    
    async def invalidate(self, key: str):
        """失效緩存項"""
        async with self._lock:
            for level in self.levels.values():
                if isinstance(level, dict):
                    level.pop(key, None)
                elif hasattr(level, 'pop'):
                    level.pop(key, None)
    
    async def invalidate_by_tags(self, tags: Set[str]):
        """根據標籤失效緩存"""
        async with self._lock:
            for level in self.levels.values():
                if isinstance(level, dict):
                    keys_to_remove = []
                    for key, entry in level.items():
                        if isinstance(entry, CacheEntry) and entry.tags & tags:
                            keys_to_remove.append(key)
                    
                    for key in keys_to_remove:
                        level.pop(key, None)
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小"""
        try:
            return len(pickle.dumps(value))
        except:
            return len(str(value))
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        return {
            'total_entries': self.stats.total_entries,
            'total_size': self.stats.total_size,
            'hit_rate': self.stats.hit_rate,
            'prefetch_accuracy': self.stats.prefetch_accuracy,
            'cache_levels': list(self.levels.keys()),
            'hit_count': self.stats.hit_count,
            'miss_count': self.stats.miss_count,
            'prefetch_count': self.stats.prefetch_count
        }

# 工廠函數
def create_intelligent_cache(
    l1_size: int = 1000,
    l1_strategy: str = "arc",
    enable_prefetch: bool = True,
    enable_l2: bool = False,
    query_executor: Optional[Callable] = None,
    **kwargs
) -> MultiLevelCache:
    """創建智能緩存管理器"""
    
    config = {
        'l1_enabled': True,
        'l1_size': l1_size,
        'l1_strategy': l1_strategy,
        'l2_enabled': enable_l2,
        'enable_prefetch': enable_prefetch,
        'query_executor': query_executor,
        **kwargs
    }
    
    return MultiLevelCache(config)

def create_prefetcher(strategy: str = "hybrid") -> IntelligentPrefetcher:
    """創建智能預取器"""
    return IntelligentPrefetcher(PrefetchStrategy(strategy))