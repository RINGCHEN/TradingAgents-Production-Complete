#!/usr/bin/env python3
"""
QueryEngine - 高性能查詢和索引系統
天工 (TianGong) - 為ART系統提供企業級查詢和索引管理

此模組提供：
1. QueryEngine - 統一查詢引擎
2. QueryBuilder - 動態查詢構建器
3. IndexManager - 索引管理器
4. QueryResult - 查詢結果封裝
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import sqlite3
import aiosqlite
from pathlib import Path
import logging
import time
from collections import defaultdict
import uuid

from .storage_base import (
    StorageBase, StorageConfig, StorageMetrics, StorageException,
    IndexConfig, IndexType
)

class QueryType(Enum):
    """查詢類型"""
    SIMPLE = "simple"            # 簡單查詢
    COMPLEX = "complex"          # 複雜查詢
    AGGREGATION = "aggregation"  # 聚合查詢
    FULL_TEXT = "full_text"      # 全文搜索
    ANALYTICS = "analytics"      # 分析查詢

class SortOrder(Enum):
    """排序方向"""
    ASC = "ASC"
    DESC = "DESC"

class AggregateFunction(Enum):
    """聚合函數"""
    COUNT = "COUNT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    GROUP_CONCAT = "GROUP_CONCAT"

class ComparisonOperator(Enum):
    """比較操作符"""
    EQ = "="          # 等於
    NE = "!="         # 不等於  
    GT = ">"          # 大於
    GTE = ">="        # 大於等於
    LT = "<"          # 小於
    LTE = "<="        # 小於等於
    LIKE = "LIKE"     # 模糊匹配
    IN = "IN"         # 包含於
    NOT_IN = "NOT IN" # 不包含於
    BETWEEN = "BETWEEN" # 範圍
    IS_NULL = "IS NULL"     # 為空
    IS_NOT_NULL = "IS NOT NULL" # 不為空

@dataclass
class QueryCondition:
    """查詢條件"""
    field: str
    operator: ComparisonOperator
    value: Any
    table_alias: str = ""
    
    def to_sql(self) -> Tuple[str, List[Any]]:
        """轉換為SQL語句"""
        field_name = f"{self.table_alias}.{self.field}" if self.table_alias else self.field
        
        if self.operator == ComparisonOperator.IS_NULL:
            return f"{field_name} IS NULL", []
        elif self.operator == ComparisonOperator.IS_NOT_NULL:
            return f"{field_name} IS NOT NULL", []
        elif self.operator == ComparisonOperator.IN:
            if isinstance(self.value, (list, tuple)):
                placeholders = ','.join(['?' for _ in self.value])
                return f"{field_name} IN ({placeholders})", list(self.value)
            else:
                return f"{field_name} IN (?)", [self.value]
        elif self.operator == ComparisonOperator.NOT_IN:
            if isinstance(self.value, (list, tuple)):
                placeholders = ','.join(['?' for _ in self.value])
                return f"{field_name} NOT IN ({placeholders})", list(self.value)
            else:
                return f"{field_name} NOT IN (?)", [self.value]
        elif self.operator == ComparisonOperator.BETWEEN:
            if isinstance(self.value, (list, tuple)) and len(self.value) == 2:
                return f"{field_name} BETWEEN ? AND ?", [self.value[0], self.value[1]]
            else:
                raise ValueError("BETWEEN operator requires a list/tuple of 2 values")
        else:
            return f"{field_name} {self.operator.value} ?", [self.value]

@dataclass
class JoinClause:
    """JOIN子句"""
    table: str
    alias: str
    join_type: str = "INNER"  # INNER, LEFT, RIGHT, FULL
    on_conditions: List[str] = field(default_factory=list)
    
    def to_sql(self) -> str:
        """轉換為SQL語句"""
        on_clause = " AND ".join(self.on_conditions) if self.on_conditions else "1=1"
        return f"{self.join_type} JOIN {self.table} AS {self.alias} ON {on_clause}"

@dataclass
class QueryResult:
    """查詢結果"""
    
    # 結果數據
    records: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    page_size: int = 100
    page_number: int = 1
    
    # 執行信息
    execution_time_ms: float = 0.0
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query_sql: str = ""
    query_params: List[Any] = field(default_factory=list)
    
    # 索引使用信息
    indexes_used: List[str] = field(default_factory=list)
    query_plan: Dict[str, Any] = field(default_factory=dict)
    
    # 統計信息
    cache_hit: bool = False
    rows_examined: int = 0
    rows_filtered: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'records': self.records,
            'total_count': self.total_count,
            'page_size': self.page_size,
            'page_number': self.page_number,
            'execution_time_ms': self.execution_time_ms,
            'query_id': self.query_id,
            'query_sql': self.query_sql,
            'indexes_used': self.indexes_used,
            'query_plan': self.query_plan,
            'cache_hit': self.cache_hit,
            'rows_examined': self.rows_examined,
            'rows_filtered': self.rows_filtered
        }
    
    @property
    def has_more_pages(self) -> bool:
        """是否有更多頁面"""
        return self.total_count > self.page_number * self.page_size
    
    @property
    def total_pages(self) -> int:
        """總頁數"""
        return (self.total_count + self.page_size - 1) // self.page_size

class QueryBuilder:
    """動態查詢構建器"""
    
    def __init__(self, table: str, alias: str = ""):
        self.table = table
        self.alias = alias or table
        self.select_fields: List[str] = []
        self.conditions: List[QueryCondition] = []
        self.joins: List[JoinClause] = []
        self.group_by_fields: List[str] = []
        self.having_conditions: List[QueryCondition] = []
        self.order_by_fields: List[Tuple[str, SortOrder]] = []
        self.limit_count: Optional[int] = None
        self.offset_count: int = 0
        self.aggregates: Dict[str, Tuple[AggregateFunction, str]] = {}
        self.distinct: bool = False
    
    def select(self, *fields: str) -> 'QueryBuilder':
        """選擇字段"""
        self.select_fields.extend(fields)
        return self
    
    def where(self, field: str, operator: ComparisonOperator, value: Any) -> 'QueryBuilder':
        """添加WHERE條件"""
        condition = QueryCondition(field, operator, value, self.alias)
        self.conditions.append(condition)
        return self
    
    def where_in(self, field: str, values: List[Any]) -> 'QueryBuilder':
        """WHERE IN條件"""
        return self.where(field, ComparisonOperator.IN, values)
    
    def where_between(self, field: str, start: Any, end: Any) -> 'QueryBuilder':
        """WHERE BETWEEN條件"""
        return self.where(field, ComparisonOperator.BETWEEN, [start, end])
    
    def where_like(self, field: str, pattern: str) -> 'QueryBuilder':
        """WHERE LIKE條件"""
        return self.where(field, ComparisonOperator.LIKE, pattern)
    
    def where_null(self, field: str) -> 'QueryBuilder':
        """WHERE IS NULL條件"""
        return self.where(field, ComparisonOperator.IS_NULL, None)
    
    def where_not_null(self, field: str) -> 'QueryBuilder':
        """WHERE IS NOT NULL條件"""
        return self.where(field, ComparisonOperator.IS_NOT_NULL, None)
    
    def join(self, table: str, alias: str, join_type: str = "INNER") -> 'QueryBuilder':
        """添加JOIN"""
        join_clause = JoinClause(table, alias, join_type)
        self.joins.append(join_clause)
        return self
    
    def on(self, condition: str) -> 'QueryBuilder':
        """添加JOIN ON條件"""
        if self.joins:
            self.joins[-1].on_conditions.append(condition)
        return self
    
    def group_by(self, *fields: str) -> 'QueryBuilder':
        """GROUP BY"""
        self.group_by_fields.extend(fields)
        return self
    
    def having(self, field: str, operator: ComparisonOperator, value: Any) -> 'QueryBuilder':
        """HAVING條件"""
        condition = QueryCondition(field, operator, value)
        self.having_conditions.append(condition)
        return self
    
    def order_by(self, field: str, order: SortOrder = SortOrder.ASC) -> 'QueryBuilder':
        """ORDER BY"""
        self.order_by_fields.append((field, order))
        return self
    
    def limit(self, count: int, offset: int = 0) -> 'QueryBuilder':
        """LIMIT和OFFSET"""
        self.limit_count = count
        self.offset_count = offset
        return self
    
    def paginate(self, page: int, page_size: int) -> 'QueryBuilder':
        """分頁"""
        offset = (page - 1) * page_size
        return self.limit(page_size, offset)
    
    def aggregate(self, alias: str, function: AggregateFunction, field: str) -> 'QueryBuilder':
        """聚合函數"""
        self.aggregates[alias] = (function, field)
        return self
    
    def count(self, alias: str = "count", field: str = "*") -> 'QueryBuilder':
        """COUNT聚合"""
        return self.aggregate(alias, AggregateFunction.COUNT, field)
    
    def sum(self, alias: str, field: str) -> 'QueryBuilder':
        """SUM聚合"""
        return self.aggregate(alias, AggregateFunction.SUM, field)
    
    def avg(self, alias: str, field: str) -> 'QueryBuilder':
        """AVG聚合"""
        return self.aggregate(alias, AggregateFunction.AVG, field)
    
    def min(self, alias: str, field: str) -> 'QueryBuilder':
        """MIN聚合"""
        return self.aggregate(alias, AggregateFunction.MIN, field)
    
    def max(self, alias: str, field: str) -> 'QueryBuilder':
        """MAX聚合"""
        return self.aggregate(alias, AggregateFunction.MAX, field)
    
    def set_distinct(self, distinct: bool = True) -> 'QueryBuilder':
        """設置DISTINCT"""
        self.distinct = distinct
        return self
    
    def to_sql(self) -> Tuple[str, List[Any]]:
        """生成SQL語句"""
        params = []
        
        # SELECT子句
        select_parts = []
        
        # 普通字段
        if self.select_fields:
            for field in self.select_fields:
                if '.' not in field and self.alias:
                    select_parts.append(f"{self.alias}.{field}")
                else:
                    select_parts.append(field)
        
        # 聚合字段
        for alias, (func, field) in self.aggregates.items():
            if '.' not in field and self.alias and field != "*":
                field = f"{self.alias}.{field}"
            select_parts.append(f"{func.value}({field}) AS {alias}")
        
        # 如果沒有指定字段，默認選擇所有
        if not select_parts:
            select_parts = [f"{self.alias}.*" if self.alias else "*"]
        
        distinct_clause = "DISTINCT " if self.distinct else ""
        select_clause = f"SELECT {distinct_clause}{', '.join(select_parts)}"
        
        # FROM子句
        from_clause = f"FROM {self.table}"
        if self.alias != self.table:
            from_clause += f" AS {self.alias}"
        
        # JOIN子句
        join_clauses = []
        for join in self.joins:
            join_clauses.append(join.to_sql())
        
        # WHERE子句
        where_conditions = []
        for condition in self.conditions:
            sql, condition_params = condition.to_sql()
            where_conditions.append(sql)
            params.extend(condition_params)
        
        where_clause = ""
        if where_conditions:
            where_clause = f"WHERE {' AND '.join(where_conditions)}"
        
        # GROUP BY子句
        group_by_clause = ""
        if self.group_by_fields:
            group_fields = []
            for field in self.group_by_fields:
                if '.' not in field and self.alias:
                    group_fields.append(f"{self.alias}.{field}")
                else:
                    group_fields.append(field)
            group_by_clause = f"GROUP BY {', '.join(group_fields)}"
        
        # HAVING子句
        having_conditions = []
        for condition in self.having_conditions:
            sql, condition_params = condition.to_sql()
            having_conditions.append(sql)
            params.extend(condition_params)
        
        having_clause = ""
        if having_conditions:
            having_clause = f"HAVING {' AND '.join(having_conditions)}"
        
        # ORDER BY子句
        order_by_clause = ""
        if self.order_by_fields:
            order_fields = []
            for field, order in self.order_by_fields:
                if '.' not in field and self.alias:
                    order_fields.append(f"{self.alias}.{field} {order.value}")
                else:
                    order_fields.append(f"{field} {order.value}")
            order_by_clause = f"ORDER BY {', '.join(order_fields)}"
        
        # LIMIT子句
        limit_clause = ""
        if self.limit_count is not None:
            if self.offset_count > 0:
                limit_clause = f"LIMIT {self.limit_count} OFFSET {self.offset_count}"
            else:
                limit_clause = f"LIMIT {self.limit_count}"
        
        # 組合所有子句
        sql_parts = [select_clause, from_clause]
        sql_parts.extend(join_clauses)
        if where_clause:
            sql_parts.append(where_clause)
        if group_by_clause:
            sql_parts.append(group_by_clause)
        if having_clause:
            sql_parts.append(having_clause)
        if order_by_clause:
            sql_parts.append(order_by_clause)
        if limit_clause:
            sql_parts.append(limit_clause)
        
        sql = ' '.join(sql_parts)
        return sql, params

class IndexManager:
    """索引管理器"""
    
    def __init__(self, storage_config: StorageConfig):
        self.config = storage_config
        self.logger = logging.getLogger(__name__)
        self.indexes: Dict[str, IndexConfig] = {}
        self.index_statistics: Dict[str, Dict[str, Any]] = {}
    
    async def create_index(self, table: str, index_config: IndexConfig) -> bool:
        """創建索引"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._create_sqlite_index(table, index_config)
            
            self.indexes[index_config.name] = index_config
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create index {index_config.name}: {e}")
            return False
    
    async def _create_sqlite_index(self, table: str, index_config: IndexConfig) -> bool:
        """創建SQLite索引"""
        db_path = Path(self.config.storage_path) / f"{self.config.database_name}.db"
        
        async with aiosqlite.connect(str(db_path)) as db:
            fields_str = ", ".join(index_config.fields)
            unique_str = "UNIQUE" if index_config.unique else ""
            
            sql = f"CREATE {unique_str} INDEX IF NOT EXISTS {index_config.name} ON {table} ({fields_str})"
            
            if index_config.partial_filter:
                # 部分索引支持（SQLite 3.8.0+）
                filter_conditions = []
                for key, value in index_config.partial_filter.items():
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    else:
                        filter_conditions.append(f"{key} = {value}")
                
                if filter_conditions:
                    sql += f" WHERE {' AND '.join(filter_conditions)}"
            
            await db.execute(sql)
            await db.commit()
            
            self.indexes[index_config.name] = index_config
            return True
    
    async def drop_index(self, index_name: str) -> bool:
        """刪除索引"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._drop_sqlite_index(index_name)
            
            if index_name in self.indexes:
                del self.indexes[index_name]
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to drop index {index_name}: {e}")
            return False
    
    async def _drop_sqlite_index(self, index_name: str) -> bool:
        """刪除SQLite索引"""
        db_path = Path(self.config.storage_path) / f"{self.config.database_name}.db"
        
        async with aiosqlite.connect(str(db_path)) as db:
            await db.execute(f"DROP INDEX IF EXISTS {index_name}")
            await db.commit()
            
            if index_name in self.indexes:
                del self.indexes[index_name]
            return True
    
    async def analyze_query(self, sql: str, params: List[Any]) -> Dict[str, Any]:
        """分析查詢執行計劃"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._analyze_sqlite_query(sql, params)
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to analyze query: {e}")
            return {}
    
    async def _analyze_sqlite_query(self, sql: str, params: List[Any]) -> Dict[str, Any]:
        """分析SQLite查詢執行計劃"""
        db_path = Path(self.config.storage_path) / f"{self.config.database_name}.db"
        
        async with aiosqlite.connect(str(db_path)) as db:
            # 獲取查詢計劃
            explain_sql = f"EXPLAIN QUERY PLAN {sql}"
            cursor = await db.execute(explain_sql, params)
            rows = await cursor.fetchall()
            
            plan_info = {
                'plan_steps': [],
                'indexes_used': [],
                'table_scans': 0,
                'index_scans': 0
            }
            
            for row in rows:
                step_info = {
                    'id': row[0] if len(row) > 0 else 0,
                    'parent': row[1] if len(row) > 1 else 0,
                    'detail': row[2] if len(row) > 2 else str(row)
                }
                plan_info['plan_steps'].append(step_info)
                
                detail = step_info['detail'].upper()
                if 'INDEX' in detail:
                    plan_info['index_scans'] += 1
                    # 提取索引名稱
                    import re
                    index_match = re.search(r'INDEX\s+(\w+)', detail)
                    if index_match:
                        plan_info['indexes_used'].append(index_match.group(1))
                elif 'SCAN' in detail:
                    plan_info['table_scans'] += 1
            
            return plan_info
    
    async def get_index_statistics(self) -> Dict[str, Dict[str, Any]]:
        """獲取索引統計信息"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._get_sqlite_index_stats()
            return self.index_statistics
            
        except Exception as e:
            self.logger.error(f"Failed to get index statistics: {e}")
            return {}
    
    async def _get_sqlite_index_stats(self) -> Dict[str, Dict[str, Any]]:
        """獲取SQLite索引統計信息"""
        db_path = Path(self.config.storage_path) / f"{self.config.database_name}.db"
        
        stats = {}
        async with aiosqlite.connect(str(db_path)) as db:
            # 獲取所有索引信息
            cursor = await db.execute("""
                SELECT name, sql, type 
                FROM sqlite_master 
                WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
            """)
            rows = await cursor.fetchall()
            
            for row in rows:
                index_name, index_sql, index_type = row
                stats[index_name] = {
                    'name': index_name,
                    'sql': index_sql,
                    'type': index_type,
                    'size_bytes': 0,  # SQLite不直接提供索引大小
                    'usage_count': 0   # 需要通過查詢分析來估算
                }
        
        self.index_statistics = stats
        return stats
    
    def get_recommended_indexes(self, table: str, query_patterns: List[Dict[str, Any]]) -> List[IndexConfig]:
        """根據查詢模式推薦索引"""
        recommendations = []
        
        # 分析查詢模式
        field_frequencies = defaultdict(int)
        field_combinations = defaultdict(int)
        
        for pattern in query_patterns:
            # 統計字段使用頻率
            if 'where_fields' in pattern:
                for field in pattern['where_fields']:
                    field_frequencies[field] += pattern.get('frequency', 1)
            
            if 'order_by_fields' in pattern:
                for field in pattern['order_by_fields']:
                    field_frequencies[field] += pattern.get('frequency', 1) * 0.5
            
            # 統計字段組合
            if 'field_combinations' in pattern:
                for combo in pattern['field_combinations']:
                    combo_key = tuple(sorted(combo))
                    field_combinations[combo_key] += pattern.get('frequency', 1)
        
        # 生成單字段索引推薦
        for field, frequency in field_frequencies.items():
            if frequency >= 5:  # 頻率閾值
                recommendations.append(IndexConfig(
                    name=f"idx_{table}_{field}",
                    fields=[field],
                    index_type=IndexType.COMPOSITE
                ))
        
        # 生成複合索引推薦
        for combo, frequency in field_combinations.items():
            if frequency >= 3 and len(combo) > 1:  # 複合索引閾值
                recommendations.append(IndexConfig(
                    name=f"idx_{table}_{'_'.join(combo)}",
                    fields=list(combo),
                    index_type=IndexType.COMPOSITE
                ))
        
        # 按頻率排序
        recommendations.sort(key=lambda x: field_frequencies.get(x.fields[0], 0), reverse=True)
        
        return recommendations[:5]  # 返回前5個推薦

class QueryEngine:
    """統一查詢引擎"""
    
    def __init__(self, storage_config: StorageConfig):
        self.config = storage_config
        self.logger = logging.getLogger(__name__)
        self.index_manager = IndexManager(storage_config)
        
        # 查詢緩存
        self._query_cache: Dict[str, QueryResult] = {}
        self._cache_timestamps: Dict[str, float] = {}
        self._cache_ttl = 300  # 5分鐘
        
        # 統計信息
        self.query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'average_execution_time': 0.0,
            'slow_queries': []
        }
        
        # 查詢模式分析
        self.query_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    async def execute_query(self, query_builder: QueryBuilder, cache_key: str = None) -> QueryResult:
        """執行查詢"""
        start_time = time.time()
        
        try:
            # 生成SQL
            sql, params = query_builder.to_sql()
            
            # 檢查緩存
            if cache_key and self._should_use_cache(cache_key):
                cached_result = self._get_from_cache(cache_key)
                if cached_result:
                    cached_result.cache_hit = True
                    self.query_stats['cache_hits'] += 1
                    return cached_result
            
            # 執行查詢
            result = QueryResult()
            result.query_sql = sql
            result.query_params = params
            
            if self.config.backend.value == "sqlite":
                await self._execute_sqlite_query(result, sql, params)
            elif self.config.backend.value == "json":
                await self._execute_json_query(result, query_builder)
            
            # 記錄執行時間
            result.execution_time_ms = (time.time() - start_time) * 1000
            
            # 分析查詢計劃
            if self.config.backend.value == "sqlite":
                plan_info = await self.index_manager.analyze_query(sql, params)
                result.query_plan = plan_info
                result.indexes_used = plan_info.get('indexes_used', [])
            
            # 更新統計
            self._update_query_stats(result)
            
            # 緩存結果
            if cache_key and result.execution_time_ms < 1000:  # 只緩存快速查詢
                self._set_to_cache(cache_key, result)
            
            # 記錄查詢模式
            self._record_query_pattern(query_builder.table, query_builder, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Query execution failed: {e}")
            raise StorageException(f"Query execution failed: {e}")
    
    async def _execute_sqlite_query(self, result: QueryResult, sql: str, params: List[Any]):
        """執行SQLite查詢"""
        db_path = Path(self.config.storage_path) / f"{self.config.database_name}.db"
        
        async with aiosqlite.connect(str(db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(sql, params)
            rows = await cursor.fetchall()
            
            # 轉換結果
            result.records = [dict(row) for row in rows]
            result.rows_examined = len(result.records)
            
            # 如果是分頁查詢，獲取總數
            if "LIMIT" in sql.upper():
                count_sql = self._build_count_sql(sql)
                count_cursor = await db.execute(count_sql, params)
                count_row = await count_cursor.fetchone()
                result.total_count = count_row[0] if count_row else len(result.records)
            else:
                result.total_count = len(result.records)
    
    def _build_count_sql(self, original_sql: str) -> str:
        """構建計數SQL"""
        # 移除ORDER BY和LIMIT子句
        sql_upper = original_sql.upper()
        
        # 找到ORDER BY位置
        order_by_pos = sql_upper.find(" ORDER BY ")
        if order_by_pos != -1:
            sql = original_sql[:order_by_pos]
        else:
            sql = original_sql
        
        # 找到LIMIT位置
        limit_pos = sql_upper.find(" LIMIT ")
        if limit_pos != -1:
            sql = original_sql[:limit_pos]
        
        # 替換SELECT子句
        select_pos = sql_upper.find("SELECT")
        from_pos = sql_upper.find(" FROM ")
        
        if select_pos != -1 and from_pos != -1:
            count_sql = f"SELECT COUNT(*){sql[from_pos:]}"
        else:
            count_sql = sql
        
        return count_sql
    
    async def _execute_json_query(self, result: QueryResult, query_builder: QueryBuilder):
        """執行JSON查詢（簡化實現）"""
        # 這裡需要實現JSON文件的查詢邏輯
        # 為了簡化，這裡只提供基本框架
        result.records = []
        result.total_count = 0
        result.rows_examined = 0
    
    def _should_use_cache(self, cache_key: str) -> bool:
        """判斷是否應該使用緩存"""
        if not self.config.enable_caching:
            return False
        
        if cache_key not in self._cache_timestamps:
            return False
        
        age = time.time() - self._cache_timestamps[cache_key]
        return age < self._cache_ttl
    
    def _get_from_cache(self, cache_key: str) -> Optional[QueryResult]:
        """從緩存獲取結果"""
        return self._query_cache.get(cache_key)
    
    def _set_to_cache(self, cache_key: str, result: QueryResult):
        """設置緩存"""
        # 簡單的LRU實現
        if len(self._query_cache) >= 100:  # 限制緩存大小
            oldest_key = min(self._cache_timestamps.keys(), 
                           key=self._cache_timestamps.get)
            del self._query_cache[oldest_key]
            del self._cache_timestamps[oldest_key]
        
        self._query_cache[cache_key] = result
        self._cache_timestamps[cache_key] = time.time()
    
    def _update_query_stats(self, result: QueryResult):
        """更新查詢統計"""
        self.query_stats['total_queries'] += 1
        
        if not result.cache_hit:
            self.query_stats['cache_misses'] += 1
        
        # 更新平均執行時間
        total_time = (self.query_stats['average_execution_time'] * 
                     (self.query_stats['total_queries'] - 1) + 
                     result.execution_time_ms)
        self.query_stats['average_execution_time'] = total_time / self.query_stats['total_queries']
        
        # 記錄慢查詢
        if result.execution_time_ms > self.config.slow_query_threshold_ms:
            slow_query = {
                'sql': result.query_sql,
                'execution_time_ms': result.execution_time_ms,
                'timestamp': datetime.now().isoformat(),
                'indexes_used': result.indexes_used
            }
            self.query_stats['slow_queries'].append(slow_query)
            
            # 保持最近100個慢查詢
            if len(self.query_stats['slow_queries']) > 100:
                self.query_stats['slow_queries'] = self.query_stats['slow_queries'][-100:]
    
    def _record_query_pattern(self, table: str, query_builder: QueryBuilder, result: QueryResult):
        """記錄查詢模式"""
        pattern = {
            'timestamp': datetime.now().isoformat(),
            'where_fields': [cond.field for cond in query_builder.conditions],
            'order_by_fields': [field for field, _ in query_builder.order_by_fields],
            'select_fields': query_builder.select_fields,
            'execution_time_ms': result.execution_time_ms,
            'rows_examined': result.rows_examined,
            'indexes_used': result.indexes_used
        }
        
        self.query_patterns[table].append(pattern)
        
        # 保持每個表最近1000個查詢模式
        if len(self.query_patterns[table]) > 1000:
            self.query_patterns[table] = self.query_patterns[table][-1000:]
    
    async def optimize_indexes(self, table: str) -> List[IndexConfig]:
        """優化索引建議"""
        try:
            patterns = self.query_patterns.get(table, [])
            if not patterns:
                return []
            
            # 分析查詢模式
            query_analysis = self._analyze_query_patterns(patterns)
            
            # 獲取推薦索引
            recommendations = self.index_manager.get_recommended_indexes(table, query_analysis)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to optimize indexes: {e}")
            return []
    
    def _analyze_query_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析查詢模式"""
        analysis = []
        
        # 按字段組合分組
        field_groups = defaultdict(list)
        for pattern in patterns:
            key = tuple(sorted(pattern['where_fields']))
            field_groups[key].append(pattern)
        
        # 分析每個組合
        for fields, group_patterns in field_groups.items():
            if not fields:
                continue
            
            avg_time = sum(p['execution_time_ms'] for p in group_patterns) / len(group_patterns)
            frequency = len(group_patterns)
            
            analysis.append({
                'field_combinations': [list(fields)],
                'where_fields': list(fields),
                'frequency': frequency,
                'average_execution_time': avg_time,
                'pattern_count': len(group_patterns)
            })
        
        return analysis
    
    def get_query_statistics(self) -> Dict[str, Any]:
        """獲取查詢統計信息"""
        return {
            'query_stats': self.query_stats.copy(),
            'cache_info': {
                'cache_size': len(self._query_cache),
                'cache_hit_rate': (
                    self.query_stats['cache_hits'] / 
                    max(1, self.query_stats['total_queries'])
                ),
                'cache_ttl_seconds': self._cache_ttl
            },
            'index_stats': self.index_manager.index_statistics.copy()
        }
    
    def clear_cache(self):
        """清空查詢緩存"""
        self._query_cache.clear()
        self._cache_timestamps.clear()
    
    async def cleanup(self):
        """清理資源"""
        self.clear_cache()

# 工廠函數
async def create_query_engine(
    storage_path: str = "./art_storage",
    backend: str = "sqlite",
    **kwargs
) -> QueryEngine:
    """創建查詢引擎實例"""
    
    from .storage_base import StorageBackend, StorageMode, create_storage_config
    
    backend_enum = StorageBackend.SQLITE
    if backend.lower() == "json":
        backend_enum = StorageBackend.JSON
    elif backend.lower() == "postgresql":
        backend_enum = StorageBackend.POSTGRESQL
    elif backend.lower() == "mongodb":
        backend_enum = StorageBackend.MONGODB
    
    config = create_storage_config(
        backend=backend_enum,
        storage_path=storage_path,
        mode=StorageMode.DEVELOPMENT,
        **kwargs
    )
    
    return QueryEngine(config)