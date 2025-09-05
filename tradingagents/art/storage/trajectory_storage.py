#!/usr/bin/env python3
"""
TrajectoryStorage - 軌跡數據結構化存儲
天工 (TianGong) - 為ART系統提供高性能軌跡數據持久化

此模組提供：
1. TrajectoryStorage - 軌跡數據的結構化存儲
2. TrajectoryRecord - 標準化軌跡記錄格式
3. TrajectoryQuery - 軌跡查詢介面
4. TrajectoryIndex - 軌跡索引管理
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import asyncpg
import os
from pathlib import Path

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

@dataclass
class TrajectoryQuery:
    """軌跡查詢參數"""
    
    # 基本篩選
    trajectory_ids: Optional[List[str]] = None
    stock_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    analyst_types: Optional[List[str]] = None
    
    # 時間範圍
    start_time_from: Optional[str] = None
    start_time_to: Optional[str] = None
    end_time_from: Optional[str] = None
    end_time_to: Optional[str] = None
    
    # 分析結果篩選
    recommendations: Optional[List[str]] = None
    confidence_min: Optional[float] = None
    confidence_max: Optional[float] = None
    
    # 持續時間篩選
    duration_min_seconds: Optional[float] = None
    duration_max_seconds: Optional[float] = None
    
    # 決策步驟篩選
    min_decision_steps: Optional[int] = None
    max_decision_steps: Optional[int] = None
    
    # 排序和分頁
    order_by: str = "created_at"
    order_desc: bool = True
    limit: int = 100
    offset: int = 0
    
    # 包含選項
    include_decision_steps: bool = True
    include_context: bool = True
    include_metadata: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass 
class TrajectoryIndex:
    """軌跡索引定義"""
    
    # 基本索引
    PRIMARY_INDEX = IndexConfig(
        name="trajectory_primary",
        fields=["trajectory_id"],
        index_type=IndexType.PRIMARY,
        unique=True
    )
    
    # 股票索引
    STOCK_INDEX = IndexConfig(
        name="trajectory_stock",
        fields=["stock_id", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 用戶索引
    USER_INDEX = IndexConfig(
        name="trajectory_user",
        fields=["user_id", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 分析師類型索引
    ANALYST_INDEX = IndexConfig(
        name="trajectory_analyst",
        fields=["analyst_type", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 時間索引
    TIME_INDEX = IndexConfig(
        name="trajectory_time",
        fields=["start_time", "end_time"],
        index_type=IndexType.COMPOSITE
    )
    
    # 信心度索引
    CONFIDENCE_INDEX = IndexConfig(
        name="trajectory_confidence",
        fields=["final_confidence"],
        index_type=IndexType.COMPOSITE
    )
    
    @classmethod
    def get_all_indexes(cls) -> List[IndexConfig]:
        """獲取所有索引配置"""
        return [
            cls.PRIMARY_INDEX,
            cls.STOCK_INDEX,
            cls.USER_INDEX,
            cls.ANALYST_INDEX,
            cls.TIME_INDEX,
            cls.CONFIDENCE_INDEX
        ]

class TrajectoryStorage(StorageBase[TrajectoryRecord]):
    """軌跡數據存儲系統"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.table_name = "art_trajectories"
        self.decision_steps_table = "art_trajectory_decision_steps"
        
        # 創建存儲路徑（僅JSON後端使用）
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if config.backend == config.backend.JSON:
            self.json_path = self.storage_path / f"{self.table_name}.json"
    
    async def initialize(self) -> bool:
        """初始化軌跡存儲系統"""
        try:
            self.logger.info("Initializing trajectory storage...")
            
            if self.config.backend.value == "postgresql":
                await self._initialize_postgresql()
            elif self.config.backend.value == "json":
                await self._initialize_json()
            else:
                raise StorageException(f"Unsupported backend: {self.config.backend}")
            
            # 創建索引
            if self.config.auto_create_indexes:
                await self._create_indexes()
            
            # 設置當前版本
            self._current_version = DataVersionInfo(
                version="1.0.0",
                created_at=datetime.now().isoformat(),
                description="Initial trajectory storage version",
                schema_version="1.0.0"
            )
            
            self._initialized = True
            self.logger.info("Trajectory storage initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize trajectory storage: {e}")
            raise StorageException(f"Initialization failed: {e}")
    
    async def _initialize_postgresql(self):
        """初始化PostgreSQL數據庫"""
        if not await self._create_pg_pool():
            raise StorageException("Failed to create PostgreSQL connection pool")
            
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
                    final_confidence DECIMAL(5,4) NOT NULL,
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
                    confidence DECIMAL(5,4) DEFAULT 0.0,
                    execution_time_ms DECIMAL(10,3) DEFAULT 0.0,
                    FOREIGN KEY (trajectory_id) REFERENCES {self.table_name} (trajectory_id) ON DELETE CASCADE
                )
            """)
            
            # 創建更新時間觸發器
            await conn.execute(f"""
                CREATE OR REPLACE FUNCTION update_updated_at_column()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.updated_at = CURRENT_TIMESTAMP;
                    RETURN NEW;
                END;
                $$ language 'plpgsql';
            """)
            
            await conn.execute(f"""
                CREATE TRIGGER IF NOT EXISTS update_{self.table_name}_updated_at
                BEFORE UPDATE ON {self.table_name}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """)
    
    async def _initialize_json(self):
        """初始化JSON文件存儲"""
        if not self.json_path.exists():
            data = {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'trajectories': {}
            }
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def _create_indexes(self):
        """創建索引"""
        if self.config.backend.value == "postgresql":
            await self._create_postgresql_indexes()
    
    async def _create_postgresql_indexes(self):
        """創建PostgreSQL索引"""
        indexes = TrajectoryIndex.get_all_indexes()
        
        async with self._pg_pool.acquire() as conn:
            for index in indexes:
                try:
                    if index.name == "trajectory_primary":
                        continue  # 主鍵索引自動創建
                    
                    fields_str = ", ".join(index.fields)
                    unique_str = "UNIQUE" if index.unique else ""
                    
                    # PostgreSQL索引語法
                    index_name = f"idx_{self.table_name}_{index.name}"
                    await conn.execute(f"""
                        CREATE {unique_str} INDEX IF NOT EXISTS {index_name}
                        ON {self.table_name} ({fields_str})
                    """)
                    
                    self.logger.debug(f"Created index: {index_name}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create index {index.name}: {e}")
    
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
            
            if self.config.backend.value == "postgresql":
                await self._create_postgresql_record(record)
            elif self.config.backend.value == "json":
                await self._create_json_record(record)
            
            # 更新指標
            self.metrics.total_records += 1
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('write', duration_ms)
            
            self.logger.debug(f"Created trajectory record: {record.trajectory_id}")
            return record.trajectory_id
            
        except Exception as e:
            self.logger.error(f"Failed to create record: {e}")
            raise StorageException(f"Create failed: {e}")
    
    async def _create_postgresql_record(self, record: TrajectoryRecord):
        """創建PostgreSQL記錄"""
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
    
    async def _create_json_record(self, record: TrajectoryRecord):
        """創建JSON記錄"""
        data = {}
        if self.json_path.exists():
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['trajectories'][record.trajectory_id] = record.to_dict()
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def get_record(self, trajectory_id: str) -> Optional[TrajectoryRecord]:
        """獲取軌跡記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 檢查緩存
            cache_key = self._get_cache_key("trajectory", trajectory_id)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            record = None
            if self.config.backend.value == "postgresql":
                record = await self._get_postgresql_record(trajectory_id)
            elif self.config.backend.value == "json":
                record = await self._get_json_record(trajectory_id)
            
            # 設置緩存
            if record:
                self._set_to_cache(cache_key, record)
            
            # 更新指標
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('read', duration_ms)
            
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to get record: {e}")
            raise StorageException(f"Get failed: {e}")
    
    async def _get_postgresql_record(self, trajectory_id: str) -> Optional[TrajectoryRecord]:
        """獲取PostgreSQL記錄"""
        async with self._pg_pool.acquire() as conn:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                f"SELECT * FROM {self.table_name} WHERE trajectory_id = ?",
                (trajectory_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            # 獲取決策步驟
            step_cursor = await db.execute(
                "SELECT * FROM decision_steps WHERE trajectory_id = ? ORDER BY timestamp",
                (trajectory_id,)
            )
            step_rows = await step_cursor.fetchall()
            
            decision_steps = []
            for step_row in step_rows:
                decision_steps.append(DecisionStep(
                    step_id=step_row['step_id'],
                    timestamp=step_row['timestamp'],
                    step_type=step_row['step_type'],
                    description=step_row['description'],
                    input_data=json.loads(step_row['input_data']),
                    output_data=json.loads(step_row['output_data']),
                    reasoning=step_row['reasoning'],
                    confidence=step_row['confidence'],
                    execution_time_ms=step_row['execution_time_ms']
                ))
            
            return TrajectoryRecord(
                trajectory_id=row['trajectory_id'],
                stock_id=row['stock_id'],
                user_id=row['user_id'],
                analyst_type=row['analyst_type'],
                start_time=row['start_time'],
                end_time=row['end_time'],
                duration_seconds=row['duration_seconds'],
                final_recommendation=row['final_recommendation'],
                final_confidence=row['final_confidence'],
                decision_steps=decision_steps,
                market_context=json.loads(row['market_context']),
                user_context=json.loads(row['user_context']),
                technical_context=json.loads(row['technical_context']),
                version=row['version'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata'])
            )
    
    async def _get_json_record(self, trajectory_id: str) -> Optional[TrajectoryRecord]:
        """獲取JSON記錄"""
        if not self.json_path.exists():
            return None
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        trajectory_data = data.get('trajectories', {}).get(trajectory_id)
        if not trajectory_data:
            return None
        
        return TrajectoryRecord.from_dict(trajectory_data)
    
    async def update_record(self, trajectory_id: str, updates: Dict[str, Any]) -> bool:
        """更新軌跡記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            success = False
            if self.config.backend.value == "sqlite":
                success = await self._update_sqlite_record(trajectory_id, updates)
            elif self.config.backend.value == "json":
                success = await self._update_json_record(trajectory_id, updates)
            
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
    
    async def _update_sqlite_record(self, trajectory_id: str, updates: Dict[str, Any]) -> bool:
        """更新SQLite記錄"""
        # 構建更新語句
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['decision_steps', 'market_context', 'user_context', 'technical_context', 'metadata']:
                if not isinstance(value, str):
                    value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(trajectory_id)
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE trajectory_id = ?",
                values
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def _update_json_record(self, trajectory_id: str, updates: Dict[str, Any]) -> bool:
        """更新JSON記錄"""
        if not self.json_path.exists():
            return False
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if trajectory_id not in data.get('trajectories', {}):
            return False
        
        data['trajectories'][trajectory_id].update(updates)
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    
    async def delete_record(self, trajectory_id: str) -> bool:
        """刪除軌跡記錄"""
        try:
            success = False
            if self.config.backend.value == "sqlite":
                success = await self._delete_sqlite_record(trajectory_id)
            elif self.config.backend.value == "json":
                success = await self._delete_json_record(trajectory_id)
            
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
    
    async def _delete_sqlite_record(self, trajectory_id: str) -> bool:
        """刪除SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 刪除決策步驟
            await db.execute("DELETE FROM decision_steps WHERE trajectory_id = ?", (trajectory_id,))
            
            # 刪除主記錄
            cursor = await db.execute(f"DELETE FROM {self.table_name} WHERE trajectory_id = ?", (trajectory_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def _delete_json_record(self, trajectory_id: str) -> bool:
        """刪除JSON記錄"""
        if not self.json_path.exists():
            return False
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if trajectory_id in data.get('trajectories', {}):
            del data['trajectories'][trajectory_id]
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        
        return False
    
    async def query_records(self, query: TrajectoryQuery) -> List[TrajectoryRecord]:
        """查詢軌跡記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            records = []
            if self.config.backend.value == "sqlite":
                records = await self._query_sqlite_records(query)
            elif self.config.backend.value == "json":
                records = await self._query_json_records(query)
            
            # 更新指標
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('query', duration_ms)
            
            return records
            
        except Exception as e:
            self.logger.error(f"Failed to query records: {e}")
            raise StorageException(f"Query failed: {e}")
    
    async def _query_sqlite_records(self, query: TrajectoryQuery) -> List[TrajectoryRecord]:
        """查詢SQLite記錄"""
        # 構建WHERE子句
        where_clauses = []
        values = []
        
        if query.trajectory_ids:
            placeholders = ','.join(['?' for _ in query.trajectory_ids])
            where_clauses.append(f"trajectory_id IN ({placeholders})")
            values.extend(query.trajectory_ids)
        
        if query.stock_ids:
            placeholders = ','.join(['?' for _ in query.stock_ids])
            where_clauses.append(f"stock_id IN ({placeholders})")
            values.extend(query.stock_ids)
        
        if query.user_ids:
            placeholders = ','.join(['?' for _ in query.user_ids])
            where_clauses.append(f"user_id IN ({placeholders})")
            values.extend(query.user_ids)
        
        if query.analyst_types:
            placeholders = ','.join(['?' for _ in query.analyst_types])
            where_clauses.append(f"analyst_type IN ({placeholders})")
            values.extend(query.analyst_types)
        
        if query.start_time_from:
            where_clauses.append("start_time >= ?")
            values.append(query.start_time_from)
        
        if query.start_time_to:
            where_clauses.append("start_time <= ?")
            values.append(query.start_time_to)
        
        if query.confidence_min:
            where_clauses.append("final_confidence >= ?")
            values.append(query.confidence_min)
        
        if query.confidence_max:
            where_clauses.append("final_confidence <= ?")
            values.append(query.confidence_max)
        
        # 構建完整查詢
        sql = f"SELECT * FROM {self.table_name}"
        if where_clauses:
            sql += f" WHERE {' AND '.join(where_clauses)}"
        
        sql += f" ORDER BY {query.order_by}"
        if query.order_desc:
            sql += " DESC"
        
        sql += f" LIMIT {query.limit} OFFSET {query.offset}"
        
        # 執行查詢
        records = []
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(sql, values)
            rows = await cursor.fetchall()
            
            for row in rows:
                # 獲取決策步驟
                decision_steps = []
                if query.include_decision_steps:
                    step_cursor = await db.execute(
                        "SELECT * FROM decision_steps WHERE trajectory_id = ? ORDER BY timestamp",
                        (row['trajectory_id'],)
                    )
                    step_rows = await step_cursor.fetchall()
                    
                    for step_row in step_rows:
                        decision_steps.append(DecisionStep(
                            step_id=step_row['step_id'],
                            timestamp=step_row['timestamp'],
                            step_type=step_row['step_type'],
                            description=step_row['description'],
                            input_data=json.loads(step_row['input_data']),
                            output_data=json.loads(step_row['output_data']),
                            reasoning=step_row['reasoning'],
                            confidence=step_row['confidence'],
                            execution_time_ms=step_row['execution_time_ms']
                        ))
                
                record = TrajectoryRecord(
                    trajectory_id=row['trajectory_id'],
                    stock_id=row['stock_id'],
                    user_id=row['user_id'],
                    analyst_type=row['analyst_type'],
                    start_time=row['start_time'],
                    end_time=row['end_time'],
                    duration_seconds=row['duration_seconds'],
                    final_recommendation=row['final_recommendation'],
                    final_confidence=row['final_confidence'],
                    decision_steps=decision_steps,
                    market_context=json.loads(row['market_context']) if query.include_context else {},
                    user_context=json.loads(row['user_context']) if query.include_context else {},
                    technical_context=json.loads(row['technical_context']) if query.include_context else {},
                    version=row['version'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=json.loads(row['metadata']) if query.include_metadata else {}
                )
                records.append(record)
        
        return records
    
    async def _query_json_records(self, query: TrajectoryQuery) -> List[TrajectoryRecord]:
        """查詢JSON記錄"""
        if not self.json_path.exists():
            return []
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        trajectories = data.get('trajectories', {})
        records = []
        
        for trajectory_data in trajectories.values():
            # 應用篩選條件
            if query.trajectory_ids and trajectory_data['trajectory_id'] not in query.trajectory_ids:
                continue
            if query.stock_ids and trajectory_data['stock_id'] not in query.stock_ids:
                continue
            if query.user_ids and trajectory_data['user_id'] not in query.user_ids:
                continue
            if query.analyst_types and trajectory_data['analyst_type'] not in query.analyst_types:
                continue
            
            # 時間範圍篩選
            if query.start_time_from and trajectory_data['start_time'] < query.start_time_from:
                continue
            if query.start_time_to and trajectory_data['start_time'] > query.start_time_to:
                continue
            
            # 信心度篩選
            if query.confidence_min and trajectory_data['final_confidence'] < query.confidence_min:
                continue
            if query.confidence_max and trajectory_data['final_confidence'] > query.confidence_max:
                continue
            
            # 創建記錄（根據包含選項）
            record_data = trajectory_data.copy()
            if not query.include_decision_steps:
                record_data['decision_steps'] = []
            if not query.include_context:
                record_data['market_context'] = {}
                record_data['user_context'] = {}
                record_data['technical_context'] = {}
            if not query.include_metadata:
                record_data['metadata'] = {}
            
            records.append(TrajectoryRecord.from_dict(record_data))
        
        # 排序
        reverse = query.order_desc
        if query.order_by == "created_at":
            records.sort(key=lambda r: r.created_at, reverse=reverse)
        elif query.order_by == "start_time":
            records.sort(key=lambda r: r.start_time, reverse=reverse)
        elif query.order_by == "final_confidence":
            records.sort(key=lambda r: r.final_confidence, reverse=reverse)
        
        # 分頁
        start = query.offset
        end = start + query.limit
        return records[start:end]
    
    async def count_records(self, query: Dict[str, Any] = None) -> int:
        """計算記錄數量"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._count_sqlite_records(query or {})
            elif self.config.backend.value == "json":
                return await self._count_json_records(query or {})
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to count records: {e}")
            raise StorageException(f"Count failed: {e}")
    
    async def _count_sqlite_records(self, query: Dict[str, Any]) -> int:
        """計算SQLite記錄數量"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(f"SELECT COUNT(*) FROM {self.table_name}")
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    async def _count_json_records(self, query: Dict[str, Any]) -> int:
        """計算JSON記錄數量"""
        if not self.json_path.exists():
            return 0
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return len(data.get('trajectories', {}))
    
    async def create_index(self, index_config: IndexConfig) -> bool:
        """創建索引"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._create_sqlite_index(index_config)
            return True
        except Exception as e:
            self.logger.error(f"Failed to create index: {e}")
            return False
    
    async def _create_sqlite_index(self, index_config: IndexConfig) -> bool:
        """創建SQLite索引"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            fields_str = ", ".join(index_config.fields)
            unique_str = "UNIQUE" if index_config.unique else ""
            
            await db.execute(f"""
                CREATE {unique_str} INDEX IF NOT EXISTS {index_config.name}
                ON {self.table_name} ({fields_str})
            """)
            await db.commit()
            return True
    
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
    backend: str = "json",
    **kwargs
) -> TrajectoryStorage:
    """創建軌跡存儲實例"""
    
    from .storage_base import StorageBackend, StorageMode, create_storage_config
    
    backend_enum = StorageBackend.JSON
    if backend.lower() == "sqlite":
        backend_enum = StorageBackend.SQLITE
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
    
    storage = TrajectoryStorage(config)
    
    if await storage.initialize():
        await storage.connect()
        return storage
    else:
        raise StorageException("Failed to initialize trajectory storage")