#!/usr/bin/env python3
"""
RewardStorage - PostgreSQL獎勵數據持久化機制
天工 (TianGong) - PostgreSQL版本的ART獎勵存儲系統

此模組提供：
1. RewardStorage - PostgreSQL獎勵數據存儲
2. RewardRecord - 標準化獎勵記錄格式
3. RewardQuery - 獎勵查詢介面
4. 完整的PostgreSQL集成
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import asyncpg
import os

from .storage_base import (
    StorageBase, StorageConfig, StorageMetrics, StorageException,
    IndexConfig, IndexType, DataVersionInfo
)

class RewardType(Enum):
    """獎勵類型"""
    ACCURACY = "accuracy"
    RETURN_PERFORMANCE = "return_performance"
    RISK_ADJUSTED_RETURN = "risk_adjusted_return" 
    REASONING_QUALITY = "reasoning_quality"
    TIMELINESS = "timeliness"
    CONSISTENCY = "consistency"
    MARKET_TIMING = "market_timing"
    PORTFOLIO_IMPACT = "portfolio_impact"

class MembershipTier(Enum):
    """會員等級"""
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"

@dataclass
class RewardComponent:
    """獎勵組成部分"""
    reward_type: RewardType
    base_score: float
    weight: float
    normalized_score: float
    component_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reward_type': self.reward_type.value,
            'base_score': self.base_score,
            'weight': self.weight,
            'normalized_score': self.normalized_score,
            'component_details': self.component_details
        }

@dataclass
class RewardRecord:
    """獎勵記錄標準格式"""
    
    # 基本信息
    reward_id: str
    trajectory_id: str
    stock_id: str
    user_id: str
    analyst_type: str
    
    # 獎勵計算
    final_reward: float
    reward_components: List[RewardComponent] = field(default_factory=list)
    
    # 時間信息
    evaluation_time: str
    period_start: str
    period_end: str
    
    # 背景信息
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    benchmark_comparison: Dict[str, Any] = field(default_factory=dict)
    
    # 會員系統
    membership_tier: MembershipTier = MembershipTier.FREE
    tier_multiplier: float = 1.0
    bonus_rewards: Dict[str, float] = field(default_factory=dict)
    
    # 元數據
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reward_id': self.reward_id,
            'trajectory_id': self.trajectory_id,
            'stock_id': self.stock_id,
            'user_id': self.user_id,
            'analyst_type': self.analyst_type,
            'final_reward': self.final_reward,
            'reward_components': [comp.to_dict() for comp in self.reward_components],
            'evaluation_time': self.evaluation_time,
            'period_start': self.period_start,
            'period_end': self.period_end,
            'market_conditions': self.market_conditions,
            'performance_metrics': self.performance_metrics,
            'benchmark_comparison': self.benchmark_comparison,
            'membership_tier': self.membership_tier.value,
            'tier_multiplier': self.tier_multiplier,
            'bonus_rewards': self.bonus_rewards,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }

class RewardStorage(StorageBase[RewardRecord]):
    """PostgreSQL獎勵數據存儲系統"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.table_name = "art_rewards"
        self.components_table = "art_reward_components"
    
    async def initialize(self) -> bool:
        """初始化獎勵存儲系統"""
        try:
            self.logger.info("Initializing PostgreSQL reward storage...")
            
            # 創建PostgreSQL連接池
            if not await self._create_pg_pool():
                raise StorageException("Failed to create PostgreSQL connection pool")
            
            # 創建數據表
            await self._create_tables()
            
            # 創建索引
            if self.config.auto_create_indexes:
                await self._create_indexes()
            
            # 設置當前版本
            self._current_version = DataVersionInfo(
                version="1.0.0",
                created_at=datetime.now().isoformat(),
                description="PostgreSQL reward storage version",
                schema_version="1.0.0"
            )
            
            self._initialized = True
            self.logger.info("PostgreSQL reward storage initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize reward storage: {e}")
            raise StorageException(f"Initialization failed: {e}")
    
    async def _create_tables(self):
        """創建PostgreSQL數據表"""
        async with self._pg_pool.acquire() as conn:
            # 創建獎勵表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    reward_id VARCHAR(255) PRIMARY KEY,
                    trajectory_id VARCHAR(255) NOT NULL,
                    stock_id VARCHAR(50) NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    analyst_type VARCHAR(50) NOT NULL,
                    final_reward DECIMAL(15,8) NOT NULL,
                    evaluation_time TIMESTAMP NOT NULL,
                    period_start TIMESTAMP NOT NULL,
                    period_end TIMESTAMP NOT NULL,
                    market_conditions JSONB NOT NULL DEFAULT '{{}}',
                    performance_metrics JSONB NOT NULL DEFAULT '{{}}',
                    benchmark_comparison JSONB NOT NULL DEFAULT '{{}}',
                    membership_tier VARCHAR(20) DEFAULT 'FREE',
                    tier_multiplier DECIMAL(5,2) DEFAULT 1.0,
                    bonus_rewards JSONB DEFAULT '{{}}',
                    version VARCHAR(20) DEFAULT '1.0.0',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{{}}'
                )
            """)
            
            # 創建獎勵組件表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.components_table} (
                    id SERIAL PRIMARY KEY,
                    reward_id VARCHAR(255) NOT NULL,
                    reward_type VARCHAR(50) NOT NULL,
                    base_score DECIMAL(15,8) NOT NULL,
                    weight DECIMAL(5,4) NOT NULL,
                    normalized_score DECIMAL(15,8) NOT NULL,
                    component_details JSONB DEFAULT '{{}}',
                    FOREIGN KEY (reward_id) REFERENCES {self.table_name} (reward_id) ON DELETE CASCADE
                )
            """)
            
            # 創建更新時間觸發器
            await conn.execute("""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            await conn.execute(f"""
                DROP TRIGGER IF EXISTS update_{self.table_name}_updated_at ON {self.table_name};
                CREATE TRIGGER update_{self.table_name}_updated_at
                BEFORE UPDATE ON {self.table_name}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
    
    async def _create_indexes(self):
        """創建PostgreSQL索引"""
        async with self._pg_pool.acquire() as conn:
            indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_trajectory ON {self.table_name} (trajectory_id)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_stock_id ON {self.table_name} (stock_id, evaluation_time)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id ON {self.table_name} (user_id, evaluation_time)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_analyst_type ON {self.table_name} (analyst_type, evaluation_time)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_time_range ON {self.table_name} (period_start, period_end)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_final_reward ON {self.table_name} (final_reward)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_membership ON {self.table_name} (membership_tier, tier_multiplier)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.components_table}_reward ON {self.components_table} (reward_id, reward_type)"
            ]
            
            for index_sql in indexes:
                try:
                    await conn.execute(index_sql)
                    self.logger.debug(f"Created index: {index_sql}")
                except Exception as e:
                    self.logger.warning(f"Failed to create index: {e}")
    
    async def connect(self) -> bool:
        """建立連接"""
        try:
            if not self._initialized:
                await self.initialize()
            
            # 測試連接
            await self.count_records()
            self._connected = True
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> bool:
        """斷開連接"""
        try:
            await self._close_pg_pool()
            self._connected = False
            return True
        except Exception as e:
            self.logger.error(f"Failed to disconnect: {e}")
            return False
    
    async def create_record(self, record: RewardRecord) -> str:
        """創建獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 驗證記錄
            if not self._validate_record(record):
                raise StorageException("Invalid reward record")
            
            record.updated_at = datetime.now().isoformat()
            
            async with self._pg_pool.acquire() as conn:
                async with conn.transaction():
                    # 插入主記錄
                    await conn.execute(f"""
                        INSERT INTO {self.table_name} (
                            reward_id, trajectory_id, stock_id, user_id, analyst_type,
                            final_reward, evaluation_time, period_start, period_end,
                            market_conditions, performance_metrics, benchmark_comparison,
                            membership_tier, tier_multiplier, bonus_rewards,
                            version, created_at, updated_at, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
                    """, 
                        record.reward_id, record.trajectory_id, record.stock_id,
                        record.user_id, record.analyst_type, record.final_reward,
                        record.evaluation_time, record.period_start, record.period_end,
                        json.dumps(record.market_conditions),
                        json.dumps(record.performance_metrics),
                        json.dumps(record.benchmark_comparison),
                        record.membership_tier.value, record.tier_multiplier,
                        json.dumps(record.bonus_rewards),
                        record.version, record.created_at, record.updated_at,
                        json.dumps(record.metadata)
                    )
                    
                    # 插入獎勵組件
                    for component in record.reward_components:
                        await conn.execute(f"""
                            INSERT INTO {self.components_table} (
                                reward_id, reward_type, base_score, weight,
                                normalized_score, component_details
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        """,
                            record.reward_id, component.reward_type.value,
                            component.base_score, component.weight,
                            component.normalized_score,
                            json.dumps(component.component_details)
                        )
            
            # 更新指標
            self.metrics.total_records += 1
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('write', duration_ms)
            
            self.logger.debug(f"Created reward record: {record.reward_id}")
            return record.reward_id
            
        except Exception as e:
            self.logger.error(f"Failed to create record: {e}")
            raise StorageException(f"Create failed: {e}")
    
    async def get_record(self, reward_id: str) -> Optional[RewardRecord]:
        """獲取獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 檢查緩存
            cache_key = self._get_cache_key("reward", reward_id)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            async with self._pg_pool.acquire() as conn:
                # 獲取主記錄
                row = await conn.fetchrow(
                    f"SELECT * FROM {self.table_name} WHERE reward_id = $1",
                    reward_id
                )
                
                if not row:
                    return None
                
                # 獲取獎勵組件
                component_rows = await conn.fetch(
                    f"SELECT * FROM {self.components_table} WHERE reward_id = $1",
                    reward_id
                )
                
                reward_components = []
                for comp_row in component_rows:
                    reward_components.append(RewardComponent(
                        reward_type=RewardType(comp_row['reward_type']),
                        base_score=float(comp_row['base_score']),
                        weight=float(comp_row['weight']),
                        normalized_score=float(comp_row['normalized_score']),
                        component_details=comp_row['component_details'] if isinstance(comp_row['component_details'], dict) else json.loads(comp_row['component_details'])
                    ))
                
                record = RewardRecord(
                    reward_id=row['reward_id'],
                    trajectory_id=row['trajectory_id'],
                    stock_id=row['stock_id'],
                    user_id=row['user_id'],
                    analyst_type=row['analyst_type'],
                    final_reward=float(row['final_reward']),
                    reward_components=reward_components,
                    evaluation_time=str(row['evaluation_time']),
                    period_start=str(row['period_start']),
                    period_end=str(row['period_end']),
                    market_conditions=row['market_conditions'] if isinstance(row['market_conditions'], dict) else json.loads(row['market_conditions']),
                    performance_metrics=row['performance_metrics'] if isinstance(row['performance_metrics'], dict) else json.loads(row['performance_metrics']),
                    benchmark_comparison=row['benchmark_comparison'] if isinstance(row['benchmark_comparison'], dict) else json.loads(row['benchmark_comparison']),
                    membership_tier=MembershipTier(row['membership_tier']),
                    tier_multiplier=float(row['tier_multiplier']),
                    bonus_rewards=row['bonus_rewards'] if isinstance(row['bonus_rewards'], dict) else json.loads(row['bonus_rewards']),
                    version=row['version'],
                    created_at=str(row['created_at']),
                    updated_at=str(row['updated_at']),
                    metadata=row['metadata'] if isinstance(row['metadata'], dict) else json.loads(row['metadata'])
                )
                
                # 設置緩存
                self._set_to_cache(cache_key, record)
                
                # 更新指標
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                await self._record_operation('read', duration_ms)
                
                return record
                
        except Exception as e:
            self.logger.error(f"Failed to get record: {e}")
            raise StorageException(f"Get failed: {e}")
    
    async def update_record(self, reward_id: str, updates: Dict[str, Any]) -> bool:
        """更新獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            # 構建更新語句
            set_clauses = []
            values = []
            param_num = 1
            
            for key, value in updates.items():
                if key in ['market_conditions', 'performance_metrics', 'benchmark_comparison', 'bonus_rewards', 'metadata']:
                    if not isinstance(value, str):
                        value = json.dumps(value)
                elif key == 'membership_tier' and hasattr(value, 'value'):
                    value = value.value
                set_clauses.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            values.append(reward_id)
            
            async with self._pg_pool.acquire() as conn:
                result = await conn.execute(
                    f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE reward_id = ${param_num}",
                    *values
                )
                
                success = "UPDATE 1" in result
                
                if success:
                    # 清除緩存
                    cache_key = self._get_cache_key("reward", reward_id)
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        del self._cache_timestamps[cache_key]
                    
                    # 更新指標
                    duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                    await self._record_operation('write', duration_ms)
                    
                    self.logger.debug(f"Updated reward record: {reward_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to update record: {e}")
            raise StorageException(f"Update failed: {e}")
    
    async def delete_record(self, reward_id: str) -> bool:
        """刪除獎勵記錄"""
        try:
            async with self._pg_pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self.table_name} WHERE reward_id = $1", 
                    reward_id
                )
                
                success = "DELETE 1" in result
                
                if success:
                    # 清除緩存
                    cache_key = self._get_cache_key("reward", reward_id)
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        del self._cache_timestamps[cache_key]
                    
                    self.metrics.total_records -= 1
                    self.metrics.delete_operations += 1
                    
                    self.logger.debug(f"Deleted reward record: {reward_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete record: {e}")
            raise StorageException(f"Delete failed: {e}")
    
    async def query_records(self, query: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[RewardRecord]:
        """查詢獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 構建WHERE子句
            where_clauses = []
            values = []
            param_num = 1
            
            for key, value in query.items():
                if key == "stock_ids" and isinstance(value, list):
                    placeholders = ','.join([f'${i}' for i in range(param_num, param_num + len(value))])
                    where_clauses.append(f"stock_id IN ({placeholders})")
                    values.extend(value)
                    param_num += len(value)
                elif key == "user_ids" and isinstance(value, list):
                    placeholders = ','.join([f'${i}' for i in range(param_num, param_num + len(value))])
                    where_clauses.append(f"user_id IN ({placeholders})")
                    values.extend(value)
                    param_num += len(value)
                elif key in ["stock_id", "user_id", "analyst_type", "trajectory_id"]:
                    where_clauses.append(f"{key} = ${param_num}")
                    values.append(value)
                    param_num += 1
                elif key == "reward_min":
                    where_clauses.append(f"final_reward >= ${param_num}")
                    values.append(value)
                    param_num += 1
                elif key == "reward_max":
                    where_clauses.append(f"final_reward <= ${param_num}")
                    values.append(value)
                    param_num += 1
                elif key == "membership_tier":
                    where_clauses.append(f"membership_tier = ${param_num}")
                    values.append(value if isinstance(value, str) else value.value)
                    param_num += 1
            
            # 構建完整查詢
            sql = f"SELECT * FROM {self.table_name}"
            if where_clauses:
                sql += f" WHERE {' AND '.join(where_clauses)}"
            
            sql += f" ORDER BY evaluation_time DESC LIMIT ${param_num} OFFSET ${param_num + 1}"
            values.extend([limit, offset])
            
            records = []
            async with self._pg_pool.acquire() as conn:
                rows = await conn.fetch(sql, *values)
                
                for row in rows:
                    record = RewardRecord(
                        reward_id=row['reward_id'],
                        trajectory_id=row['trajectory_id'],
                        stock_id=row['stock_id'],
                        user_id=row['user_id'],
                        analyst_type=row['analyst_type'],
                        final_reward=float(row['final_reward']),
                        reward_components=[],  # 基本查詢不加載組件
                        evaluation_time=str(row['evaluation_time']),
                        period_start=str(row['period_start']),
                        period_end=str(row['period_end']),
                        market_conditions=row['market_conditions'] if isinstance(row['market_conditions'], dict) else {},
                        performance_metrics=row['performance_metrics'] if isinstance(row['performance_metrics'], dict) else {},
                        benchmark_comparison=row['benchmark_comparison'] if isinstance(row['benchmark_comparison'], dict) else {},
                        membership_tier=MembershipTier(row['membership_tier']),
                        tier_multiplier=float(row['tier_multiplier']),
                        bonus_rewards=row['bonus_rewards'] if isinstance(row['bonus_rewards'], dict) else {},
                        version=row['version'],
                        created_at=str(row['created_at']),
                        updated_at=str(row['updated_at']),
                        metadata=row['metadata'] if isinstance(row['metadata'], dict) else {}
                    )
                    records.append(record)
            
            # 更新指標
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('query', duration_ms)
            
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to query records: {e}")
            raise StorageException(f"Query failed: {e}")
    
    async def count_records(self, query: Dict[str, Any] = None) -> int:
        """計算記錄數量"""
        try:
            async with self._pg_pool.acquire() as conn:
                if not query:
                    row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self.table_name}")
                    return row[0] if row else 0
                else:
                    # 簡化版本，實際應用中需要完整的WHERE子句構建
                    row = await conn.fetchrow(f"SELECT COUNT(*) FROM {self.table_name}")
                    return row[0] if row else 0
                    
        except Exception as e:
            self.logger.error(f"Failed to count records: {e}")
            raise StorageException(f"Count failed: {e}")
    
    async def create_index(self, index_config: IndexConfig) -> bool:
        """創建索引"""
        try:
            async with self._pg_pool.acquire() as conn:
                fields_str = ", ".join(index_config.fields)
                unique_str = "UNIQUE" if index_config.unique else ""
                index_name = f"idx_{self.table_name}_{index_config.name}"
                
                await conn.execute(f"""
                    CREATE {unique_str} INDEX IF NOT EXISTS {index_name}
                    ON {self.table_name} ({fields_str})
                """)
                return True
        except Exception as e:
            self.logger.error(f"Failed to create index: {e}")
            return False
    
    def _validate_record(self, record: RewardRecord) -> bool:
        """驗證獎勵記錄"""
        if not record.reward_id or not record.trajectory_id:
            return False
        if not record.stock_id or not record.user_id:
            return False
        if not record.evaluation_time or not record.period_start or not record.period_end:
            return False
        return True

# 工廠函數
async def create_reward_storage(
    storage_path: str = "./art_storage",
    backend: str = "postgresql",
    **kwargs
) -> RewardStorage:
    """創建獎勵存儲實例"""
    
    from .storage_base import StorageBackend, StorageMode, create_storage_config
    
    config = create_storage_config(
        backend=StorageBackend.POSTGRESQL,
        storage_path=storage_path,
        mode=StorageMode.PRODUCTION,
        **kwargs
    )
    
    storage = RewardStorage(config)
    
    if await storage.initialize():
        await storage.connect()
        return storage
    else:
        raise StorageException("Failed to initialize reward storage")