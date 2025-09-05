#!/usr/bin/env python3
"""
TrajectoryStorage - PostgreSQL軌跡數據存儲
天工 (TianGong) - PostgreSQL版本的ART軌跡存儲系統

此模組提供：
1. TrajectoryStorage - PostgreSQL軌跡數據存儲
2. TrajectoryRecord - 標準化軌跡記錄格式
3. TrajectoryQuery - 軌跡查詢介面
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

@dataclass
class DecisionStep:
    """決策步驟記錄"""
    step_id: str
    timestamp: str
    step_type: str  # 'data_collection', 'analysis', 'reasoning', 'decision'
    description: str
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    confidence: float = 0.0
    execution_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TrajectoryRecord:
    """軌跡記錄標準格式"""
    
    # 基本信息
    trajectory_id: str
    stock_id: str
    user_id: str
    analyst_type: str
    
    # 時間信息
    start_time: str
    end_time: str
    duration_seconds: float
    
    # 分析結果
    final_recommendation: str
    final_confidence: float
    
    # 決策軌跡
    decision_steps: List[DecisionStep] = field(default_factory=list)
    
    # 上下文數據
    market_context: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, Any] = field(default_factory=dict)
    technical_context: Dict[str, Any] = field(default_factory=dict)
    
    # 元數據
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'trajectory_id': self.trajectory_id,
            'stock_id': self.stock_id,
            'user_id': self.user_id,
            'analyst_type': self.analyst_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration_seconds': self.duration_seconds,
            'final_recommendation': self.final_recommendation,
            'final_confidence': self.final_confidence,
            'decision_steps': [step.to_dict() for step in self.decision_steps],
            'market_context': self.market_context,
            'user_context': self.user_context,
            'technical_context': self.technical_context,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrajectoryRecord':
        """從字典創建軌跡記錄"""
        decision_steps = [
            DecisionStep(**step) if isinstance(step, dict) else step
            for step in data.get('decision_steps', [])
        ]
        
        return cls(
            trajectory_id=data['trajectory_id'],
            stock_id=data['stock_id'],
            user_id=data['user_id'],
            analyst_type=data['analyst_type'],
            start_time=data['start_time'],
            end_time=data['end_time'],
            duration_seconds=data['duration_seconds'],
            final_recommendation=data['final_recommendation'],
            final_confidence=data['final_confidence'],
            decision_steps=decision_steps,
            market_context=data.get('market_context', {}),
            user_context=data.get('user_context', {}),
            technical_context=data.get('technical_context', {}),
            version=data.get('version', '1.0.0'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            metadata=data.get('metadata', {})
        )

class TrajectoryStorage(StorageBase[TrajectoryRecord]):
    """PostgreSQL軌跡數據存儲系統"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.table_name = "art_trajectories"
        self.decision_steps_table = "art_trajectory_decision_steps"
    
    async def initialize(self) -> bool:
        """初始化軌跡存儲系統"""
        try:
            self.logger.info("Initializing PostgreSQL trajectory storage...")
            
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
                description="PostgreSQL trajectory storage version",
                schema_version="1.0.0"
            )
            
            self._initialized = True
            self.logger.info("PostgreSQL trajectory storage initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize trajectory storage: {e}")
            raise StorageException(f"Initialization failed: {e}")
    
    async def _create_tables(self):
        """創建PostgreSQL數據表"""
        async with self._pg_pool.acquire() as conn:
            # 創建軌跡表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    trajectory_id VARCHAR(255) PRIMARY KEY,
                    stock_id VARCHAR(50) NOT NULL,
                    user_id VARCHAR(100) NOT NULL,
                    analyst_type VARCHAR(50) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP NOT NULL,
                    duration_seconds DECIMAL(10,3) NOT NULL,
                    final_recommendation TEXT NOT NULL,
                    final_confidence DECIMAL(5,4) NOT NULL CHECK (final_confidence >= 0 AND final_confidence <= 1),
                    decision_steps JSONB NOT NULL DEFAULT '[]',
                    market_context JSONB NOT NULL DEFAULT '{{}}',
                    user_context JSONB NOT NULL DEFAULT '{{}}',
                    technical_context JSONB NOT NULL DEFAULT '{{}}',
                    version VARCHAR(20) DEFAULT '1.0.0',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB DEFAULT '{{}}'
                )
            """)
            
            # 創建決策步驟表
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.decision_steps_table} (
                    id SERIAL PRIMARY KEY,
                    trajectory_id VARCHAR(255) NOT NULL,
                    step_id VARCHAR(255) NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    step_type VARCHAR(50) NOT NULL,
                    description TEXT NOT NULL,
                    input_data JSONB DEFAULT '{{}}',
                    output_data JSONB DEFAULT '{{}}',
                    reasoning TEXT DEFAULT '',
                    confidence DECIMAL(5,4) DEFAULT 0.0 CHECK (confidence >= 0 AND confidence <= 1),
                    execution_time_ms DECIMAL(10,3) DEFAULT 0.0,
                    FOREIGN KEY (trajectory_id) REFERENCES {self.table_name} (trajectory_id) ON DELETE CASCADE
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
            # 基本索引
            indexes = [
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_stock_id ON {self.table_name} (stock_id, created_at)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_user_id ON {self.table_name} (user_id, created_at)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_analyst_type ON {self.table_name} (analyst_type, created_at)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_time_range ON {self.table_name} (start_time, end_time)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.table_name}_confidence ON {self.table_name} (final_confidence)",
                f"CREATE INDEX IF NOT EXISTS idx_{self.decision_steps_table}_trajectory ON {self.decision_steps_table} (trajectory_id, timestamp)"
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
    
    async def create_record(self, record: TrajectoryRecord) -> str:
        """創建軌跡記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 驗證記錄
            if not self._validate_record(record):
                raise StorageException("Invalid trajectory record")
            
            record.updated_at = datetime.now().isoformat()
            
            async with self._pg_pool.acquire() as conn:
                async with conn.transaction():
                    # 插入主記錄
                    await conn.execute(f"""
                        INSERT INTO {self.table_name} (
                            trajectory_id, stock_id, user_id, analyst_type,
                            start_time, end_time, duration_seconds,
                            final_recommendation, final_confidence,
                            decision_steps, market_context, user_context,
                            technical_context, version, created_at, updated_at, metadata
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                    """, 
                        record.trajectory_id, record.stock_id, record.user_id,
                        record.analyst_type, record.start_time, record.end_time,
                        record.duration_seconds, record.final_recommendation,
                        record.final_confidence,
                        json.dumps([step.to_dict() for step in record.decision_steps]),
                        json.dumps(record.market_context),
                        json.dumps(record.user_context),
                        json.dumps(record.technical_context),
                        record.version, record.created_at, record.updated_at,
                        json.dumps(record.metadata)
                    )
                    
                    # 插入決策步驟
                    for step in record.decision_steps:
                        await conn.execute(f"""
                            INSERT INTO {self.decision_steps_table} (
                                trajectory_id, step_id, timestamp, step_type,
                                description, input_data, output_data,
                                reasoning, confidence, execution_time_ms
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        """,
                            record.trajectory_id, step.step_id, step.timestamp,
                            step.step_type, step.description,
                            json.dumps(step.input_data),
                            json.dumps(step.output_data),
                            step.reasoning, step.confidence, step.execution_time_ms
                        )
            
            # 更新指標
            self.metrics.total_records += 1
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('write', duration_ms)
            
            self.logger.debug(f"Created trajectory record: {record.trajectory_id}")
            return record.trajectory_id
            
        except Exception as e:
            self.logger.error(f"Failed to create record: {e}")
            raise StorageException(f"Create failed: {e}")
    
    async def get_record(self, trajectory_id: str) -> Optional[TrajectoryRecord]:
        """獲取軌跡記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 檢查緩存
            cache_key = self._get_cache_key("trajectory", trajectory_id)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            async with self._pg_pool.acquire() as conn:
                # 獲取主記錄
                row = await conn.fetchrow(
                    f"SELECT * FROM {self.table_name} WHERE trajectory_id = $1",
                    trajectory_id
                )
                
                if not row:
                    return None
                
                # 獲取決策步驟
                step_rows = await conn.fetch(
                    f"SELECT * FROM {self.decision_steps_table} WHERE trajectory_id = $1 ORDER BY timestamp",
                    trajectory_id
                )
                
                decision_steps = []
                for step_row in step_rows:
                    decision_steps.append(DecisionStep(
                        step_id=step_row['step_id'],
                        timestamp=str(step_row['timestamp']),
                        step_type=step_row['step_type'],
                        description=step_row['description'],
                        input_data=step_row['input_data'] if isinstance(step_row['input_data'], dict) else json.loads(step_row['input_data']),
                        output_data=step_row['output_data'] if isinstance(step_row['output_data'], dict) else json.loads(step_row['output_data']),
                        reasoning=step_row['reasoning'],
                        confidence=float(step_row['confidence']),
                        execution_time_ms=float(step_row['execution_time_ms'])
                    ))
                
                record = TrajectoryRecord(
                    trajectory_id=row['trajectory_id'],
                    stock_id=row['stock_id'],
                    user_id=row['user_id'],
                    analyst_type=row['analyst_type'],
                    start_time=str(row['start_time']),
                    end_time=str(row['end_time']),
                    duration_seconds=float(row['duration_seconds']),
                    final_recommendation=row['final_recommendation'],
                    final_confidence=float(row['final_confidence']),
                    decision_steps=decision_steps,
                    market_context=row['market_context'] if isinstance(row['market_context'], dict) else json.loads(row['market_context']),
                    user_context=row['user_context'] if isinstance(row['user_context'], dict) else json.loads(row['user_context']),
                    technical_context=row['technical_context'] if isinstance(row['technical_context'], dict) else json.loads(row['technical_context']),
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
    
    async def update_record(self, trajectory_id: str, updates: Dict[str, Any]) -> bool:
        """更新軌跡記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            # 構建更新語句
            set_clauses = []
            values = []
            param_num = 1
            
            for key, value in updates.items():
                if key in ['decision_steps', 'market_context', 'user_context', 'technical_context', 'metadata']:
                    if not isinstance(value, str):
                        value = json.dumps(value)
                set_clauses.append(f"{key} = ${param_num}")
                values.append(value)
                param_num += 1
            
            values.append(trajectory_id)
            
            async with self._pg_pool.acquire() as conn:
                result = await conn.execute(
                    f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE trajectory_id = ${param_num}",
                    *values
                )
                
                success = "UPDATE 1" in result
                
                if success:
                    # 清除緩存
                    cache_key = self._get_cache_key("trajectory", trajectory_id)
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        del self._cache_timestamps[cache_key]
                    
                    # 更新指標
                    duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                    await self._record_operation('write', duration_ms)
                    
                    self.logger.debug(f"Updated trajectory record: {trajectory_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to update record: {e}")
            raise StorageException(f"Update failed: {e}")
    
    async def delete_record(self, trajectory_id: str) -> bool:
        """刪除軌跡記錄"""
        try:
            async with self._pg_pool.acquire() as conn:
                result = await conn.execute(
                    f"DELETE FROM {self.table_name} WHERE trajectory_id = $1", 
                    trajectory_id
                )
                
                success = "DELETE 1" in result
                
                if success:
                    # 清除緩存
                    cache_key = self._get_cache_key("trajectory", trajectory_id)
                    if cache_key in self._cache:
                        del self._cache[cache_key]
                        del self._cache_timestamps[cache_key]
                    
                    self.metrics.total_records -= 1
                    self.metrics.delete_operations += 1
                    
                    self.logger.debug(f"Deleted trajectory record: {trajectory_id}")
                
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete record: {e}")
            raise StorageException(f"Delete failed: {e}")
    
    async def query_records(self, query: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[TrajectoryRecord]:
        """查詢軌跡記錄"""
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
                elif key in ["stock_id", "user_id", "analyst_type"]:
                    where_clauses.append(f"{key} = ${param_num}")
                    values.append(value)
                    param_num += 1
                elif key == "confidence_min":
                    where_clauses.append(f"final_confidence >= ${param_num}")
                    values.append(value)
                    param_num += 1
                elif key == "confidence_max":
                    where_clauses.append(f"final_confidence <= ${param_num}")
                    values.append(value)
                    param_num += 1
            
            # 構建完整查詢
            sql = f"SELECT * FROM {self.table_name}"
            if where_clauses:
                sql += f" WHERE {' AND '.join(where_clauses)}"
            
            sql += f" ORDER BY created_at DESC LIMIT ${param_num} OFFSET ${param_num + 1}"
            values.extend([limit, offset])
            
            records = []
            async with self._pg_pool.acquire() as conn:
                rows = await conn.fetch(sql, *values)
                
                for row in rows:
                    record = TrajectoryRecord(
                        trajectory_id=row['trajectory_id'],
                        stock_id=row['stock_id'],
                        user_id=row['user_id'],
                        analyst_type=row['analyst_type'],
                        start_time=str(row['start_time']),
                        end_time=str(row['end_time']),
                        duration_seconds=float(row['duration_seconds']),
                        final_recommendation=row['final_recommendation'],
                        final_confidence=float(row['final_confidence']),
                        decision_steps=[],  # 基本查詢不加載步驟
                        market_context=row['market_context'] if isinstance(row['market_context'], dict) else {},
                        user_context=row['user_context'] if isinstance(row['user_context'], dict) else {},
                        technical_context=row['technical_context'] if isinstance(row['technical_context'], dict) else {},
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
    
    def _validate_record(self, record: TrajectoryRecord) -> bool:
        """驗證軌跡記錄"""
        if not record.trajectory_id or not record.stock_id:
            return False
        if not record.user_id or not record.analyst_type:
            return False
        if not record.start_time or not record.end_time:
            return False
        if record.final_confidence < 0 or record.final_confidence > 1:
            return False
        return True

# 工廠函數
async def create_trajectory_storage(
    storage_path: str = "./art_storage",
    backend: str = "postgresql",
    **kwargs
) -> TrajectoryStorage:
    """創建軌跡存儲實例"""
    
    from .storage_base import StorageBackend, StorageMode, create_storage_config
    
    config = create_storage_config(
        backend=StorageBackend.POSTGRESQL,
        storage_path=storage_path,
        mode=StorageMode.PRODUCTION,
        **kwargs
    )
    
    storage = TrajectoryStorage(config)
    
    if await storage.initialize():
        await storage.connect()
        return storage
    else:
        raise StorageException("Failed to initialize trajectory storage")