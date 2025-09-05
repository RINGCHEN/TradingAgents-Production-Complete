#!/usr/bin/env python3
"""
RewardStorage - 獎勵數據持久化機制
天工 (TianGong) - 為ART系統提供高性能獎勵數據持久化

此模組提供：
1. RewardStorage - 獎勵數據的結構化存儲
2. RewardRecord - 標準化獎勵記錄格式
3. RewardQuery - 獎勵查詢介面
4. RewardIndex - 獎勵索引管理
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import json
import asyncio
import sqlite3
import aiosqlite
from pathlib import Path

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
    base_reward: float
    confidence: float
    weight: float
    final_reward: float
    calculation_details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'reward_type': self.reward_type.value,
            'base_reward': self.base_reward,
            'confidence': self.confidence,
            'weight': self.weight,
            'final_reward': self.final_reward,
            'calculation_details': self.calculation_details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RewardComponent':
        return cls(
            reward_type=RewardType(data['reward_type']),
            base_reward=data['base_reward'],
            confidence=data['confidence'],
            weight=data['weight'],
            final_reward=data['final_reward'],
            calculation_details=data.get('calculation_details', {})
        )

@dataclass
class RewardRecord:
    """獎勵記錄標準格式"""
    
    # 基本信息
    signal_id: str
    trajectory_id: str
    user_id: str
    stock_id: str
    analyst_type: str
    
    # 獎勵信息
    base_total_reward: float
    membership_multiplier: float
    weighted_total_reward: float
    calculation_timestamp: str
    
    # 可選字段
    reward_components: List[RewardComponent] = field(default_factory=list)
    evaluation_period_days: int = 1
    immediate_evaluation: bool = False
    
    # 市場數據
    market_data: Dict[str, Any] = field(default_factory=dict)
    benchmark_data: Dict[str, Any] = field(default_factory=dict)
    
    # 會員信息
    membership_tier: MembershipTier = MembershipTier.FREE
    tier_benefits: Dict[str, Any] = field(default_factory=dict)
    
    # 元數據
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'trajectory_id': self.trajectory_id,
            'user_id': self.user_id,
            'stock_id': self.stock_id,
            'analyst_type': self.analyst_type,
            'base_total_reward': self.base_total_reward,
            'membership_multiplier': self.membership_multiplier,
            'weighted_total_reward': self.weighted_total_reward,
            'reward_components': [comp.to_dict() for comp in self.reward_components],
            'calculation_timestamp': self.calculation_timestamp,
            'evaluation_period_days': self.evaluation_period_days,
            'immediate_evaluation': self.immediate_evaluation,
            'market_data': self.market_data,
            'benchmark_data': self.benchmark_data,
            'membership_tier': self.membership_tier.value,
            'tier_benefits': self.tier_benefits,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RewardRecord':
        """從字典創建獎勵記錄"""
        reward_components = [
            RewardComponent.from_dict(comp) if isinstance(comp, dict) else comp
            for comp in data.get('reward_components', [])
        ]
        
        return cls(
            signal_id=data['signal_id'],
            trajectory_id=data['trajectory_id'],
            user_id=data['user_id'],
            stock_id=data['stock_id'],
            analyst_type=data['analyst_type'],
            base_total_reward=data['base_total_reward'],
            membership_multiplier=data['membership_multiplier'],
            weighted_total_reward=data['weighted_total_reward'],
            reward_components=reward_components,
            calculation_timestamp=data['calculation_timestamp'],
            evaluation_period_days=data.get('evaluation_period_days', 1),
            immediate_evaluation=data.get('immediate_evaluation', False),
            market_data=data.get('market_data', {}),
            benchmark_data=data.get('benchmark_data', {}),
            membership_tier=MembershipTier(data.get('membership_tier', 'FREE')),
            tier_benefits=data.get('tier_benefits', {}),
            version=data.get('version', '1.0.0'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            metadata=data.get('metadata', {})
        )

@dataclass
class RewardQuery:
    """獎勵查詢參數"""
    
    # 基本篩選
    signal_ids: Optional[List[str]] = None
    trajectory_ids: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    stock_ids: Optional[List[str]] = None
    analyst_types: Optional[List[str]] = None
    
    # 時間範圍
    calculation_timestamp_from: Optional[str] = None
    calculation_timestamp_to: Optional[str] = None
    created_at_from: Optional[str] = None
    created_at_to: Optional[str] = None
    
    # 獎勵篩選
    reward_min: Optional[float] = None
    reward_max: Optional[float] = None
    membership_tiers: Optional[List[str]] = None
    immediate_evaluation: Optional[bool] = None
    
    # 評估期間篩選
    evaluation_period_min_days: Optional[int] = None
    evaluation_period_max_days: Optional[int] = None
    
    # 獎勵類型篩選
    reward_types: Optional[List[str]] = None
    
    # 排序和分頁
    order_by: str = "created_at"
    order_desc: bool = True
    limit: int = 100
    offset: int = 0
    
    # 包含選項
    include_components: bool = True
    include_market_data: bool = True
    include_metadata: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class RewardIndex:
    """獎勵索引定義"""
    
    # 基本索引
    PRIMARY_INDEX = IndexConfig(
        name="reward_primary",
        fields=["signal_id"],
        index_type=IndexType.PRIMARY,
        unique=True
    )
    
    # 軌跡索引
    TRAJECTORY_INDEX = IndexConfig(
        name="reward_trajectory",
        fields=["trajectory_id"],
        index_type=IndexType.COMPOSITE
    )
    
    # 用戶索引
    USER_INDEX = IndexConfig(
        name="reward_user",
        fields=["user_id", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 股票索引
    STOCK_INDEX = IndexConfig(
        name="reward_stock",
        fields=["stock_id", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 分析師類型索引
    ANALYST_INDEX = IndexConfig(
        name="reward_analyst",
        fields=["analyst_type", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 時間索引
    TIME_INDEX = IndexConfig(
        name="reward_time",
        fields=["calculation_timestamp"],
        index_type=IndexType.COMPOSITE
    )
    
    # 獎勵值索引
    REWARD_VALUE_INDEX = IndexConfig(
        name="reward_value",
        fields=["weighted_total_reward"],
        index_type=IndexType.COMPOSITE
    )
    
    # 會員等級索引
    MEMBERSHIP_INDEX = IndexConfig(
        name="reward_membership",
        fields=["membership_tier", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    @classmethod
    def get_all_indexes(cls) -> List[IndexConfig]:
        """獲取所有索引配置"""
        return [
            cls.PRIMARY_INDEX,
            cls.TRAJECTORY_INDEX,
            cls.USER_INDEX,
            cls.STOCK_INDEX,
            cls.ANALYST_INDEX,
            cls.TIME_INDEX,
            cls.REWARD_VALUE_INDEX,
            cls.MEMBERSHIP_INDEX
        ]

class RewardStorage(StorageBase[RewardRecord]):
    """獎勵數據存儲系統"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.table_name = "rewards"
        self.db_path = None
        
        # 創建存儲路徑
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if config.backend == config.backend.SQLITE:
            self.db_path = self.storage_path / f"{config.database_name}.db"
        elif config.backend == config.backend.JSON:
            self.json_path = self.storage_path / f"{self.table_name}.json"
    
    async def initialize(self) -> bool:
        """初始化獎勵存儲系統"""
        try:
            self.logger.info("Initializing reward storage...")
            
            if self.config.backend.value == "sqlite":
                await self._initialize_sqlite()
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
                description="Initial reward storage version",
                schema_version="1.0.0"
            )
            
            self._initialized = True
            self.logger.info("Reward storage initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize reward storage: {e}")
            raise StorageException(f"Initialization failed: {e}")
    
    async def _initialize_sqlite(self):
        """初始化SQLite數據庫"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 創建獎勵表
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    signal_id TEXT PRIMARY KEY,
                    trajectory_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    stock_id TEXT NOT NULL,
                    analyst_type TEXT NOT NULL,
                    base_total_reward REAL NOT NULL,
                    membership_multiplier REAL NOT NULL,
                    weighted_total_reward REAL NOT NULL,
                    reward_components TEXT NOT NULL,
                    calculation_timestamp TEXT NOT NULL,
                    evaluation_period_days INTEGER DEFAULT 1,
                    immediate_evaluation BOOLEAN DEFAULT 0,
                    market_data TEXT DEFAULT '{{}}',
                    benchmark_data TEXT DEFAULT '{{}}',
                    membership_tier TEXT DEFAULT 'FREE',
                    tier_benefits TEXT DEFAULT '{{}}',
                    version TEXT DEFAULT '1.0.0',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{{}}'
                )
            """)
            
            # 創建獎勵組件表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reward_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    reward_type TEXT NOT NULL,
                    base_reward REAL NOT NULL,
                    confidence REAL NOT NULL,
                    weight REAL NOT NULL,
                    final_reward REAL NOT NULL,
                    calculation_details TEXT DEFAULT '{{}}',
                    FOREIGN KEY (signal_id) REFERENCES rewards (signal_id)
                )
            """)
            
            await db.commit()
    
    async def _initialize_json(self):
        """初始化JSON文件存儲"""
        if not self.json_path.exists():
            data = {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'rewards': {}
            }
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def _create_indexes(self):
        """創建索引"""
        if self.config.backend.value == "sqlite":
            await self._create_sqlite_indexes()
    
    async def _create_sqlite_indexes(self):
        """創建SQLite索引"""
        indexes = RewardIndex.get_all_indexes()
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            for index in indexes:
                try:
                    if index.name == "reward_primary":
                        continue  # 主鍵索引自動創建
                    
                    fields_str = ", ".join(index.fields)
                    unique_str = "UNIQUE" if index.unique else ""
                    
                    await db.execute(f"""
                        CREATE {unique_str} INDEX IF NOT EXISTS {index.name}
                        ON {self.table_name} ({fields_str})
                    """)
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create index {index.name}: {e}")
            
            await db.commit()
    
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
    
    async def create_record(self, record: RewardRecord) -> str:
        """創建獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 驗證記錄
            if not self._validate_record(record):
                raise StorageException("Invalid reward record")
            
            record.updated_at = datetime.now().isoformat()
            
            if self.config.backend.value == "sqlite":
                await self._create_sqlite_record(record)
            elif self.config.backend.value == "json":
                await self._create_json_record(record)
            
            # 更新指標
            self.metrics.total_records += 1
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('write', duration_ms)
            
            self.logger.debug(f"Created reward record: {record.signal_id}")
            return record.signal_id
            
        except Exception as e:
            self.logger.error(f"Failed to create record: {e}")
            raise StorageException(f"Create failed: {e}")
    
    async def _create_sqlite_record(self, record: RewardRecord):
        """創建SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 插入主記錄
            await db.execute(f"""
                INSERT INTO {self.table_name} (
                    signal_id, trajectory_id, user_id, stock_id, analyst_type,
                    base_total_reward, membership_multiplier, weighted_total_reward,
                    reward_components, calculation_timestamp, evaluation_period_days,
                    immediate_evaluation, market_data, benchmark_data,
                    membership_tier, tier_benefits, version, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.signal_id, record.trajectory_id, record.user_id,
                record.stock_id, record.analyst_type, record.base_total_reward,
                record.membership_multiplier, record.weighted_total_reward,
                json.dumps([comp.to_dict() for comp in record.reward_components]),
                record.calculation_timestamp, record.evaluation_period_days,
                record.immediate_evaluation, json.dumps(record.market_data),
                json.dumps(record.benchmark_data), record.membership_tier.value,
                json.dumps(record.tier_benefits), record.version,
                record.created_at, record.updated_at, json.dumps(record.metadata)
            ))
            
            # 插入獎勵組件
            for comp in record.reward_components:
                await db.execute("""
                    INSERT INTO reward_components (
                        signal_id, reward_type, base_reward, confidence,
                        weight, final_reward, calculation_details
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.signal_id, comp.reward_type.value, comp.base_reward,
                    comp.confidence, comp.weight, comp.final_reward,
                    json.dumps(comp.calculation_details)
                ))
            
            await db.commit()
    
    async def _create_json_record(self, record: RewardRecord):
        """創建JSON記錄"""
        data = {}
        if self.json_path.exists():
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['rewards'][record.signal_id] = record.to_dict()
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def get_record(self, signal_id: str) -> Optional[RewardRecord]:
        """獲取獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 檢查緩存
            cache_key = self._get_cache_key("reward", signal_id)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            record = None
            if self.config.backend.value == "sqlite":
                record = await self._get_sqlite_record(signal_id)
            elif self.config.backend.value == "json":
                record = await self._get_json_record(signal_id)
            
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
    
    async def _get_sqlite_record(self, signal_id: str) -> Optional[RewardRecord]:
        """獲取SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                f"SELECT * FROM {self.table_name} WHERE signal_id = ?",
                (signal_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            # 獲取獎勵組件
            comp_cursor = await db.execute(
                "SELECT * FROM reward_components WHERE signal_id = ?",
                (signal_id,)
            )
            comp_rows = await comp_cursor.fetchall()
            
            reward_components = []
            for comp_row in comp_rows:
                reward_components.append(RewardComponent(
                    reward_type=RewardType(comp_row['reward_type']),
                    base_reward=comp_row['base_reward'],
                    confidence=comp_row['confidence'],
                    weight=comp_row['weight'],
                    final_reward=comp_row['final_reward'],
                    calculation_details=json.loads(comp_row['calculation_details'])
                ))
            
            return RewardRecord(
                signal_id=row['signal_id'],
                trajectory_id=row['trajectory_id'],
                user_id=row['user_id'],
                stock_id=row['stock_id'],
                analyst_type=row['analyst_type'],
                base_total_reward=row['base_total_reward'],
                membership_multiplier=row['membership_multiplier'],
                weighted_total_reward=row['weighted_total_reward'],
                reward_components=reward_components,
                calculation_timestamp=row['calculation_timestamp'],
                evaluation_period_days=row['evaluation_period_days'],
                immediate_evaluation=bool(row['immediate_evaluation']),
                market_data=json.loads(row['market_data']),
                benchmark_data=json.loads(row['benchmark_data']),
                membership_tier=MembershipTier(row['membership_tier']),
                tier_benefits=json.loads(row['tier_benefits']),
                version=row['version'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata'])
            )
    
    async def _get_json_record(self, signal_id: str) -> Optional[RewardRecord]:
        """獲取JSON記錄"""
        if not self.json_path.exists():
            return None
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        reward_data = data.get('rewards', {}).get(signal_id)
        if not reward_data:
            return None
        
        return RewardRecord.from_dict(reward_data)
    
    async def update_record(self, signal_id: str, updates: Dict[str, Any]) -> bool:
        """更新獎勵記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            success = False
            if self.config.backend.value == "sqlite":
                success = await self._update_sqlite_record(signal_id, updates)
            elif self.config.backend.value == "json":
                success = await self._update_json_record(signal_id, updates)
            
            if success:
                # 清除緩存
                cache_key = self._get_cache_key("reward", signal_id)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                
                # 更新指標
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                await self._record_operation('write', duration_ms)
                
                self.logger.debug(f"Updated reward record: {signal_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update record: {e}")
            raise StorageException(f"Update failed: {e}")
    
    async def _update_sqlite_record(self, signal_id: str, updates: Dict[str, Any]) -> bool:
        """更新SQLite記錄"""
        # 構建更新語句
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['reward_components', 'market_data', 'benchmark_data', 'tier_benefits', 'metadata']:
                if not isinstance(value, str):
                    value = json.dumps(value)
            elif key == 'membership_tier' and hasattr(value, 'value'):
                value = value.value
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(signal_id)
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE signal_id = ?",
                values
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def _update_json_record(self, signal_id: str, updates: Dict[str, Any]) -> bool:
        """更新JSON記錄"""
        if not self.json_path.exists():
            return False
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if signal_id not in data.get('rewards', {}):
            return False
        
        # 處理特殊字段
        processed_updates = {}
        for key, value in updates.items():
            if key == 'membership_tier' and hasattr(value, 'value'):
                processed_updates[key] = value.value
            else:
                processed_updates[key] = value
        
        data['rewards'][signal_id].update(processed_updates)
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    
    async def delete_record(self, signal_id: str) -> bool:
        """刪除獎勵記錄"""
        try:
            success = False
            if self.config.backend.value == "sqlite":
                success = await self._delete_sqlite_record(signal_id)
            elif self.config.backend.value == "json":
                success = await self._delete_json_record(signal_id)
            
            if success:
                # 清除緩存
                cache_key = self._get_cache_key("reward", signal_id)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                
                self.metrics.total_records -= 1
                self.metrics.delete_operations += 1
                
                self.logger.debug(f"Deleted reward record: {signal_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete record: {e}")
            raise StorageException(f"Delete failed: {e}")
    
    async def _delete_sqlite_record(self, signal_id: str) -> bool:
        """刪除SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 刪除獎勵組件
            await db.execute("DELETE FROM reward_components WHERE signal_id = ?", (signal_id,))
            
            # 刪除主記錄
            cursor = await db.execute(f"DELETE FROM {self.table_name} WHERE signal_id = ?", (signal_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def _delete_json_record(self, signal_id: str) -> bool:
        """刪除JSON記錄"""
        if not self.json_path.exists():
            return False
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if signal_id in data.get('rewards', {}):
            del data['rewards'][signal_id]
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        
        return False
    
    async def query_records(self, query: RewardQuery) -> List[RewardRecord]:
        """查詢獎勵記錄"""
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
    
    async def _query_sqlite_records(self, query: RewardQuery) -> List[RewardRecord]:
        """查詢SQLite記錄"""
        # 構建WHERE子句
        where_clauses = []
        values = []
        
        if query.signal_ids:
            placeholders = ','.join(['?' for _ in query.signal_ids])
            where_clauses.append(f"signal_id IN ({placeholders})")
            values.extend(query.signal_ids)
        
        if query.trajectory_ids:
            placeholders = ','.join(['?' for _ in query.trajectory_ids])
            where_clauses.append(f"trajectory_id IN ({placeholders})")
            values.extend(query.trajectory_ids)
        
        if query.user_ids:
            placeholders = ','.join(['?' for _ in query.user_ids])
            where_clauses.append(f"user_id IN ({placeholders})")
            values.extend(query.user_ids)
        
        if query.stock_ids:
            placeholders = ','.join(['?' for _ in query.stock_ids])
            where_clauses.append(f"stock_id IN ({placeholders})")
            values.extend(query.stock_ids)
        
        if query.analyst_types:
            placeholders = ','.join(['?' for _ in query.analyst_types])
            where_clauses.append(f"analyst_type IN ({placeholders})")
            values.extend(query.analyst_types)
        
        if query.calculation_timestamp_from:
            where_clauses.append("calculation_timestamp >= ?")
            values.append(query.calculation_timestamp_from)
        
        if query.calculation_timestamp_to:
            where_clauses.append("calculation_timestamp <= ?")
            values.append(query.calculation_timestamp_to)
        
        if query.reward_min:
            where_clauses.append("weighted_total_reward >= ?")
            values.append(query.reward_min)
        
        if query.reward_max:
            where_clauses.append("weighted_total_reward <= ?")
            values.append(query.reward_max)
        
        if query.membership_tiers:
            placeholders = ','.join(['?' for _ in query.membership_tiers])
            where_clauses.append(f"membership_tier IN ({placeholders})")
            values.extend(query.membership_tiers)
        
        if query.immediate_evaluation is not None:
            where_clauses.append("immediate_evaluation = ?")
            values.append(query.immediate_evaluation)
        
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
                # 獲取獎勵組件
                reward_components = []
                if query.include_components:
                    comp_cursor = await db.execute(
                        "SELECT * FROM reward_components WHERE signal_id = ?",
                        (row['signal_id'],)
                    )
                    comp_rows = await comp_cursor.fetchall()
                    
                    for comp_row in comp_rows:
                        reward_components.append(RewardComponent(
                            reward_type=RewardType(comp_row['reward_type']),
                            base_reward=comp_row['base_reward'],
                            confidence=comp_row['confidence'],
                            weight=comp_row['weight'],
                            final_reward=comp_row['final_reward'],
                            calculation_details=json.loads(comp_row['calculation_details'])
                        ))
                
                record = RewardRecord(
                    signal_id=row['signal_id'],
                    trajectory_id=row['trajectory_id'],
                    user_id=row['user_id'],
                    stock_id=row['stock_id'],
                    analyst_type=row['analyst_type'],
                    base_total_reward=row['base_total_reward'],
                    membership_multiplier=row['membership_multiplier'],
                    weighted_total_reward=row['weighted_total_reward'],
                    reward_components=reward_components,
                    calculation_timestamp=row['calculation_timestamp'],
                    evaluation_period_days=row['evaluation_period_days'],
                    immediate_evaluation=bool(row['immediate_evaluation']),
                    market_data=json.loads(row['market_data']) if query.include_market_data else {},
                    benchmark_data=json.loads(row['benchmark_data']) if query.include_market_data else {},
                    membership_tier=MembershipTier(row['membership_tier']),
                    tier_benefits=json.loads(row['tier_benefits']),
                    version=row['version'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=json.loads(row['metadata']) if query.include_metadata else {}
                )
                records.append(record)
        
        return records
    
    async def _query_json_records(self, query: RewardQuery) -> List[RewardRecord]:
        """查詢JSON記錄"""
        if not self.json_path.exists():
            return []
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        rewards = data.get('rewards', {})
        records = []
        
        for reward_data in rewards.values():
            # 應用篩選條件
            if query.signal_ids and reward_data['signal_id'] not in query.signal_ids:
                continue
            if query.trajectory_ids and reward_data['trajectory_id'] not in query.trajectory_ids:
                continue
            if query.user_ids and reward_data['user_id'] not in query.user_ids:
                continue
            if query.stock_ids and reward_data['stock_id'] not in query.stock_ids:
                continue
            if query.analyst_types and reward_data['analyst_type'] not in query.analyst_types:
                continue
            
            # 時間範圍篩選
            if query.calculation_timestamp_from and reward_data['calculation_timestamp'] < query.calculation_timestamp_from:
                continue
            if query.calculation_timestamp_to and reward_data['calculation_timestamp'] > query.calculation_timestamp_to:
                continue
            
            # 獎勵範圍篩選
            if query.reward_min and reward_data['weighted_total_reward'] < query.reward_min:
                continue
            if query.reward_max and reward_data['weighted_total_reward'] > query.reward_max:
                continue
            
            # 會員等級篩選
            if query.membership_tiers and reward_data['membership_tier'] not in query.membership_tiers:
                continue
            
            # 立即評估篩選
            if query.immediate_evaluation is not None and reward_data['immediate_evaluation'] != query.immediate_evaluation:
                continue
            
            # 創建記錄（根據包含選項）
            record_data = reward_data.copy()
            if not query.include_components:
                record_data['reward_components'] = []
            if not query.include_market_data:
                record_data['market_data'] = {}
                record_data['benchmark_data'] = {}
            if not query.include_metadata:
                record_data['metadata'] = {}
            
            records.append(RewardRecord.from_dict(record_data))
        
        # 排序
        reverse = query.order_desc
        if query.order_by == "created_at":
            records.sort(key=lambda r: r.created_at, reverse=reverse)
        elif query.order_by == "calculation_timestamp":
            records.sort(key=lambda r: r.calculation_timestamp, reverse=reverse)
        elif query.order_by == "weighted_total_reward":
            records.sort(key=lambda r: r.weighted_total_reward, reverse=reverse)
        
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
        
        return len(data.get('rewards', {}))
    
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
    
    def _validate_record(self, record: RewardRecord) -> bool:
        """驗證獎勵記錄"""
        if not record.signal_id or not record.trajectory_id:
            return False
        if not record.user_id or not record.stock_id:
            return False
        if not record.analyst_type:
            return False
        if record.base_total_reward < 0 or record.weighted_total_reward < 0:
            return False
        if record.membership_multiplier <= 0:
            return False
        return True
    
    # 特殊查詢方法
    async def get_user_reward_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """獲取用戶獎勵摘要"""
        try:
            # 計算時間範圍
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            query = RewardQuery(
                user_ids=[user_id],
                created_at_from=start_time.isoformat(),
                created_at_to=end_time.isoformat(),
                limit=1000  # 獲取更多記錄用於統計
            )
            
            records = await self.query_records(query)
            
            if not records:
                return {
                    'user_id': user_id,
                    'period_days': days,
                    'total_signals': 0,
                    'total_reward': 0.0,
                    'average_reward': 0.0,
                    'max_reward': 0.0,
                    'min_reward': 0.0,
                    'consistency_score': 0.0
                }
            
            # 計算統計數據
            total_reward = sum(r.weighted_total_reward for r in records)
            rewards = [r.weighted_total_reward for r in records]
            
            # 計算一致性分數（標準差的倒數）
            import statistics
            consistency_score = 0.0
            if len(rewards) > 1:
                std_dev = statistics.stdev(rewards)
                consistency_score = 1.0 / (1.0 + std_dev) if std_dev > 0 else 1.0
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_signals': len(records),
                'total_reward': total_reward,
                'average_reward': total_reward / len(records),
                'max_reward': max(rewards),
                'min_reward': min(rewards),
                'consistency_score': consistency_score,
                'membership_tier': records[0].membership_tier.value if records else 'FREE',
                'last_reward_time': max(r.created_at for r in records) if records else None
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get user reward summary: {e}")
            raise StorageException(f"User reward summary failed: {e}")
    
    async def get_stock_reward_analysis(self, stock_id: str, days: int = 30) -> Dict[str, Any]:
        """獲取股票獎勵分析"""
        try:
            # 計算時間範圍
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            query = RewardQuery(
                stock_ids=[stock_id],
                created_at_from=start_time.isoformat(),
                created_at_to=end_time.isoformat(),
                limit=1000
            )
            
            records = await self.query_records(query)
            
            if not records:
                return {
                    'stock_id': stock_id,
                    'period_days': days,
                    'total_analyses': 0,
                    'analyst_performance': {}
                }
            
            # 按分析師類型分組
            analyst_performance = {}
            for record in records:
                analyst_type = record.analyst_type
                if analyst_type not in analyst_performance:
                    analyst_performance[analyst_type] = {
                        'count': 0,
                        'total_reward': 0.0,
                        'average_reward': 0.0,
                        'best_reward': 0.0
                    }
                
                perf = analyst_performance[analyst_type]
                perf['count'] += 1
                perf['total_reward'] += record.weighted_total_reward
                perf['best_reward'] = max(perf['best_reward'], record.weighted_total_reward)
                perf['average_reward'] = perf['total_reward'] / perf['count']
            
            return {
                'stock_id': stock_id,
                'period_days': days,
                'total_analyses': len(records),
                'analyst_performance': analyst_performance,
                'total_reward': sum(r.weighted_total_reward for r in records),
                'average_reward': sum(r.weighted_total_reward for r in records) / len(records)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get stock reward analysis: {e}")
            raise StorageException(f"Stock reward analysis failed: {e}")

# 工廠函數
async def create_reward_storage(
    storage_path: str = "./art_storage",
    backend: str = "json",
    **kwargs
) -> RewardStorage:
    """創建獎勵存儲實例"""
    
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
    
    storage = RewardStorage(config)
    
    if await storage.initialize():
        await storage.connect()
        return storage
    else:
        raise StorageException("Failed to initialize reward storage")