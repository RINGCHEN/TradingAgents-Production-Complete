#!/usr/bin/env python3
"""
UserProfileStorage - 用戶檔案可靠存儲
天工 (TianGong) - 為ART系統提供高性能用戶檔案持久化

此模組提供：
1. UserProfileStorage - 用戶檔案的結構化存儲
2. UserProfileRecord - 標準化用戶檔案格式
3. UserProfileQuery - 用戶檔案查詢介面
4. UserProfileIndex - 用戶檔案索引管理
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

class PersonalizationLevel(Enum):
    """個人化等級"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class MembershipTier(Enum):
    """會員等級"""
    FREE = "FREE"
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"
    GOLD = "GOLD"
    PLATINUM = "PLATINUM"

class UserStatus(Enum):
    """用戶狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"

@dataclass
class AnalystPreference:
    """分析師偏好"""
    analyst_type: str
    usage_count: int
    average_confidence: float
    last_used: str
    satisfaction_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AnalystPreference':
        return cls(**data)

@dataclass
class PerformanceHistory:
    """績效歷史記錄"""
    timestamp: str
    trajectory_id: str
    reward_value: float
    confidence: float
    recommendation: str
    stock_id: str
    analyst_type: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceHistory':
        return cls(**data)

@dataclass
class UserProfileRecord:
    """用戶檔案記錄標準格式"""
    
    # 基本信息
    user_id: str
    username: str
    email: str = ""
    full_name: str = ""
    
    # 會員信息
    membership_tier: MembershipTier = MembershipTier.FREE
    membership_start_date: str = ""
    membership_expiry_date: str = ""
    
    # 使用統計
    total_analyses: int = 0
    total_trajectories: int = 0
    total_rewards: float = 0.0
    average_reward: float = 0.0
    
    # 個人化信息
    personalization_level: PersonalizationLevel = PersonalizationLevel.BASIC
    analyst_preferences: List[AnalystPreference] = field(default_factory=list)
    performance_history: List[PerformanceHistory] = field(default_factory=list)
    
    # 偏好設置
    preferred_stocks: List[str] = field(default_factory=list)
    risk_tolerance: float = 0.5  # 0.0 - 1.0
    investment_horizon_days: int = 30
    notification_preferences: Dict[str, bool] = field(default_factory=dict)
    
    # 學習數據
    learning_profile: Dict[str, Any] = field(default_factory=dict)
    adaptation_parameters: Dict[str, float] = field(default_factory=dict)
    
    # 狀態信息
    user_status: UserStatus = UserStatus.ACTIVE
    last_login: str = ""
    last_analysis: str = ""
    
    # 統計信息
    success_rate: float = 0.0
    consistency_score: float = 0.0
    expertise_level: float = 0.0
    
    # 元數據
    version: str = "1.0.0"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'membership_tier': self.membership_tier.value,
            'membership_start_date': self.membership_start_date,
            'membership_expiry_date': self.membership_expiry_date,
            'total_analyses': self.total_analyses,
            'total_trajectories': self.total_trajectories,
            'total_rewards': self.total_rewards,
            'average_reward': self.average_reward,
            'personalization_level': self.personalization_level.value,
            'analyst_preferences': [pref.to_dict() for pref in self.analyst_preferences],
            'performance_history': [perf.to_dict() for perf in self.performance_history],
            'preferred_stocks': self.preferred_stocks,
            'risk_tolerance': self.risk_tolerance,
            'investment_horizon_days': self.investment_horizon_days,
            'notification_preferences': self.notification_preferences,
            'learning_profile': self.learning_profile,
            'adaptation_parameters': self.adaptation_parameters,
            'user_status': self.user_status.value,
            'last_login': self.last_login,
            'last_analysis': self.last_analysis,
            'success_rate': self.success_rate,
            'consistency_score': self.consistency_score,
            'expertise_level': self.expertise_level,
            'version': self.version,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfileRecord':
        """從字典創建用戶檔案記錄"""
        analyst_preferences = [
            AnalystPreference.from_dict(pref) if isinstance(pref, dict) else pref
            for pref in data.get('analyst_preferences', [])
        ]
        
        performance_history = [
            PerformanceHistory.from_dict(perf) if isinstance(perf, dict) else perf
            for perf in data.get('performance_history', [])
        ]
        
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            email=data.get('email', ''),
            full_name=data.get('full_name', ''),
            membership_tier=MembershipTier(data.get('membership_tier', 'FREE')),
            membership_start_date=data.get('membership_start_date', ''),
            membership_expiry_date=data.get('membership_expiry_date', ''),
            total_analyses=data.get('total_analyses', 0),
            total_trajectories=data.get('total_trajectories', 0),
            total_rewards=data.get('total_rewards', 0.0),
            average_reward=data.get('average_reward', 0.0),
            personalization_level=PersonalizationLevel(data.get('personalization_level', 'basic')),
            analyst_preferences=analyst_preferences,
            performance_history=performance_history,
            preferred_stocks=data.get('preferred_stocks', []),
            risk_tolerance=data.get('risk_tolerance', 0.5),
            investment_horizon_days=data.get('investment_horizon_days', 30),
            notification_preferences=data.get('notification_preferences', {}),
            learning_profile=data.get('learning_profile', {}),
            adaptation_parameters=data.get('adaptation_parameters', {}),
            user_status=UserStatus(data.get('user_status', 'active')),
            last_login=data.get('last_login', ''),
            last_analysis=data.get('last_analysis', ''),
            success_rate=data.get('success_rate', 0.0),
            consistency_score=data.get('consistency_score', 0.0),
            expertise_level=data.get('expertise_level', 0.0),
            version=data.get('version', '1.0.0'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            updated_at=data.get('updated_at', datetime.now().isoformat()),
            metadata=data.get('metadata', {})
        )

@dataclass
class UserProfileQuery:
    """用戶檔案查詢參數"""
    
    # 基本篩選
    user_ids: Optional[List[str]] = None
    usernames: Optional[List[str]] = None
    emails: Optional[List[str]] = None
    
    # 會員信息篩選
    membership_tiers: Optional[List[str]] = None
    membership_active: Optional[bool] = None
    
    # 使用統計篩選
    min_total_analyses: Optional[int] = None
    max_total_analyses: Optional[int] = None
    min_total_rewards: Optional[float] = None
    max_total_rewards: Optional[float] = None
    
    # 個人化等級篩選
    personalization_levels: Optional[List[str]] = None
    
    # 狀態篩選
    user_statuses: Optional[List[str]] = None
    
    # 時間範圍篩選
    created_at_from: Optional[str] = None
    created_at_to: Optional[str] = None
    last_login_from: Optional[str] = None
    last_login_to: Optional[str] = None
    
    # 績效篩選
    min_success_rate: Optional[float] = None
    max_success_rate: Optional[float] = None
    min_consistency_score: Optional[float] = None
    max_consistency_score: Optional[float] = None
    
    # 排序和分頁
    order_by: str = "created_at"
    order_desc: bool = True
    limit: int = 100
    offset: int = 0
    
    # 包含選項
    include_preferences: bool = True
    include_history: bool = True
    include_learning_data: bool = False
    include_metadata: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

@dataclass
class UserProfileIndex:
    """用戶檔案索引定義"""
    
    # 基本索引
    PRIMARY_INDEX = IndexConfig(
        name="user_profile_primary",
        fields=["user_id"],
        index_type=IndexType.PRIMARY,
        unique=True
    )
    
    # 用戶名索引
    USERNAME_INDEX = IndexConfig(
        name="user_profile_username",
        fields=["username"],
        index_type=IndexType.UNIQUE,
        unique=True
    )
    
    # 郵箱索引
    EMAIL_INDEX = IndexConfig(
        name="user_profile_email",
        fields=["email"],
        index_type=IndexType.UNIQUE,
        unique=True
    )
    
    # 會員等級索引
    MEMBERSHIP_INDEX = IndexConfig(
        name="user_profile_membership",
        fields=["membership_tier", "created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    # 個人化等級索引
    PERSONALIZATION_INDEX = IndexConfig(
        name="user_profile_personalization",
        fields=["personalization_level", "total_analyses"],
        index_type=IndexType.COMPOSITE
    )
    
    # 狀態索引
    STATUS_INDEX = IndexConfig(
        name="user_profile_status",
        fields=["user_status", "last_login"],
        index_type=IndexType.COMPOSITE
    )
    
    # 績效索引
    PERFORMANCE_INDEX = IndexConfig(
        name="user_profile_performance",
        fields=["success_rate", "consistency_score"],
        index_type=IndexType.COMPOSITE
    )
    
    # 時間索引
    TIME_INDEX = IndexConfig(
        name="user_profile_time",
        fields=["created_at"],
        index_type=IndexType.COMPOSITE
    )
    
    @classmethod
    def get_all_indexes(cls) -> List[IndexConfig]:
        """獲取所有索引配置"""
        return [
            cls.PRIMARY_INDEX,
            cls.USERNAME_INDEX,
            cls.EMAIL_INDEX,
            cls.MEMBERSHIP_INDEX,
            cls.PERSONALIZATION_INDEX,
            cls.STATUS_INDEX,
            cls.PERFORMANCE_INDEX,
            cls.TIME_INDEX
        ]

class UserProfileStorage(StorageBase[UserProfileRecord]):
    """用戶檔案存儲系統"""
    
    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self.table_name = "user_profiles"
        self.db_path = None
        
        # 創建存儲路徑
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if config.backend == config.backend.SQLITE:
            self.db_path = self.storage_path / f"{config.database_name}.db"
        elif config.backend == config.backend.JSON:
            self.json_path = self.storage_path / f"{self.table_name}.json"
    
    async def initialize(self) -> bool:
        """初始化用戶檔案存儲系統"""
        try:
            self.logger.info("Initializing user profile storage...")
            
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
                description="Initial user profile storage version",
                schema_version="1.0.0"
            )
            
            self._initialized = True
            self.logger.info("User profile storage initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize user profile storage: {e}")
            raise StorageException(f"Initialization failed: {e}")
    
    async def _initialize_sqlite(self):
        """初始化SQLite數據庫"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 創建用戶檔案表
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE,
                    full_name TEXT DEFAULT '',
                    membership_tier TEXT DEFAULT 'FREE',
                    membership_start_date TEXT DEFAULT '',
                    membership_expiry_date TEXT DEFAULT '',
                    total_analyses INTEGER DEFAULT 0,
                    total_trajectories INTEGER DEFAULT 0,
                    total_rewards REAL DEFAULT 0.0,
                    average_reward REAL DEFAULT 0.0,
                    personalization_level TEXT DEFAULT 'basic',
                    analyst_preferences TEXT DEFAULT '[]',
                    performance_history TEXT DEFAULT '[]',
                    preferred_stocks TEXT DEFAULT '[]',
                    risk_tolerance REAL DEFAULT 0.5,
                    investment_horizon_days INTEGER DEFAULT 30,
                    notification_preferences TEXT DEFAULT '{{}}',
                    learning_profile TEXT DEFAULT '{{}}',
                    adaptation_parameters TEXT DEFAULT '{{}}',
                    user_status TEXT DEFAULT 'active',
                    last_login TEXT DEFAULT '',
                    last_analysis TEXT DEFAULT '',
                    success_rate REAL DEFAULT 0.0,
                    consistency_score REAL DEFAULT 0.0,
                    expertise_level REAL DEFAULT 0.0,
                    version TEXT DEFAULT '1.0.0',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT DEFAULT '{{}}'
                )
            """)
            
            # 創建分析師偏好表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS analyst_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    analyst_type TEXT NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    average_confidence REAL DEFAULT 0.0,
                    last_used TEXT DEFAULT '',
                    satisfaction_score REAL DEFAULT 0.0,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id),
                    UNIQUE(user_id, analyst_type)
                )
            """)
            
            # 創建績效歷史表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS performance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    trajectory_id TEXT NOT NULL,
                    reward_value REAL NOT NULL,
                    confidence REAL NOT NULL,
                    recommendation TEXT NOT NULL,
                    stock_id TEXT NOT NULL,
                    analyst_type TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES user_profiles (user_id)
                )
            """)
            
            await db.commit()
    
    async def _initialize_json(self):
        """初始化JSON文件存儲"""
        if not self.json_path.exists():
            data = {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'user_profiles': {}
            }
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def _create_indexes(self):
        """創建索引"""
        if self.config.backend.value == "sqlite":
            await self._create_sqlite_indexes()
    
    async def _create_sqlite_indexes(self):
        """創建SQLite索引"""
        indexes = UserProfileIndex.get_all_indexes()
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            for index in indexes:
                try:
                    if index.name in ["user_profile_primary", "user_profile_username", "user_profile_email"]:
                        continue  # 這些索引由約束自動創建
                    
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
    
    async def create_record(self, record: UserProfileRecord) -> str:
        """創建用戶檔案記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 驗證記錄
            if not self._validate_record(record):
                raise StorageException("Invalid user profile record")
            
            record.updated_at = datetime.now().isoformat()
            
            if self.config.backend.value == "sqlite":
                await self._create_sqlite_record(record)
            elif self.config.backend.value == "json":
                await self._create_json_record(record)
            
            # 更新指標
            self.metrics.total_records += 1
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            await self._record_operation('write', duration_ms)
            
            self.logger.debug(f"Created user profile record: {record.user_id}")
            return record.user_id
            
        except Exception as e:
            self.logger.error(f"Failed to create record: {e}")
            raise StorageException(f"Create failed: {e}")
    
    async def _create_sqlite_record(self, record: UserProfileRecord):
        """創建SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 插入主記錄
            await db.execute(f"""
                INSERT INTO {self.table_name} (
                    user_id, username, email, full_name,
                    membership_tier, membership_start_date, membership_expiry_date,
                    total_analyses, total_trajectories, total_rewards, average_reward,
                    personalization_level, analyst_preferences, performance_history,
                    preferred_stocks, risk_tolerance, investment_horizon_days,
                    notification_preferences, learning_profile, adaptation_parameters,
                    user_status, last_login, last_analysis,
                    success_rate, consistency_score, expertise_level,
                    version, created_at, updated_at, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.user_id, record.username, record.email, record.full_name,
                record.membership_tier.value, record.membership_start_date, record.membership_expiry_date,
                record.total_analyses, record.total_trajectories, record.total_rewards, record.average_reward,
                record.personalization_level.value,
                json.dumps([pref.to_dict() for pref in record.analyst_preferences]),
                json.dumps([perf.to_dict() for perf in record.performance_history]),
                json.dumps(record.preferred_stocks), record.risk_tolerance, record.investment_horizon_days,
                json.dumps(record.notification_preferences), json.dumps(record.learning_profile),
                json.dumps(record.adaptation_parameters), record.user_status.value,
                record.last_login, record.last_analysis,
                record.success_rate, record.consistency_score, record.expertise_level,
                record.version, record.created_at, record.updated_at, json.dumps(record.metadata)
            ))
            
            # 插入分析師偏好
            for pref in record.analyst_preferences:
                await db.execute("""
                    INSERT OR REPLACE INTO analyst_preferences (
                        user_id, analyst_type, usage_count, average_confidence,
                        last_used, satisfaction_score
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    record.user_id, pref.analyst_type, pref.usage_count,
                    pref.average_confidence, pref.last_used, pref.satisfaction_score
                ))
            
            # 插入績效歷史
            for perf in record.performance_history:
                await db.execute("""
                    INSERT INTO performance_history (
                        user_id, timestamp, trajectory_id, reward_value,
                        confidence, recommendation, stock_id, analyst_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record.user_id, perf.timestamp, perf.trajectory_id, perf.reward_value,
                    perf.confidence, perf.recommendation, perf.stock_id, perf.analyst_type
                ))
            
            await db.commit()
    
    async def _create_json_record(self, record: UserProfileRecord):
        """創建JSON記錄"""
        data = {}
        if self.json_path.exists():
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['user_profiles'][record.user_id] = record.to_dict()
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    async def get_record(self, user_id: str) -> Optional[UserProfileRecord]:
        """獲取用戶檔案記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 檢查緩存
            cache_key = self._get_cache_key("user_profile", user_id)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            record = None
            if self.config.backend.value == "sqlite":
                record = await self._get_sqlite_record(user_id)
            elif self.config.backend.value == "json":
                record = await self._get_json_record(user_id)
            
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
    
    async def _get_sqlite_record(self, user_id: str) -> Optional[UserProfileRecord]:
        """獲取SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                f"SELECT * FROM {self.table_name} WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            # 獲取分析師偏好
            pref_cursor = await db.execute(
                "SELECT * FROM analyst_preferences WHERE user_id = ?",
                (user_id,)
            )
            pref_rows = await pref_cursor.fetchall()
            
            analyst_preferences = []
            for pref_row in pref_rows:
                analyst_preferences.append(AnalystPreference(
                    analyst_type=pref_row['analyst_type'],
                    usage_count=pref_row['usage_count'],
                    average_confidence=pref_row['average_confidence'],
                    last_used=pref_row['last_used'],
                    satisfaction_score=pref_row['satisfaction_score']
                ))
            
            # 獲取績效歷史
            perf_cursor = await db.execute(
                "SELECT * FROM performance_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 100",
                (user_id,)
            )
            perf_rows = await perf_cursor.fetchall()
            
            performance_history = []
            for perf_row in perf_rows:
                performance_history.append(PerformanceHistory(
                    timestamp=perf_row['timestamp'],
                    trajectory_id=perf_row['trajectory_id'],
                    reward_value=perf_row['reward_value'],
                    confidence=perf_row['confidence'],
                    recommendation=perf_row['recommendation'],
                    stock_id=perf_row['stock_id'],
                    analyst_type=perf_row['analyst_type']
                ))
            
            return UserProfileRecord(
                user_id=row['user_id'],
                username=row['username'],
                email=row['email'],
                full_name=row['full_name'],
                membership_tier=MembershipTier(row['membership_tier']),
                membership_start_date=row['membership_start_date'],
                membership_expiry_date=row['membership_expiry_date'],
                total_analyses=row['total_analyses'],
                total_trajectories=row['total_trajectories'],
                total_rewards=row['total_rewards'],
                average_reward=row['average_reward'],
                personalization_level=PersonalizationLevel(row['personalization_level']),
                analyst_preferences=analyst_preferences,
                performance_history=performance_history,
                preferred_stocks=json.loads(row['preferred_stocks']),
                risk_tolerance=row['risk_tolerance'],
                investment_horizon_days=row['investment_horizon_days'],
                notification_preferences=json.loads(row['notification_preferences']),
                learning_profile=json.loads(row['learning_profile']),
                adaptation_parameters=json.loads(row['adaptation_parameters']),
                user_status=UserStatus(row['user_status']),
                last_login=row['last_login'],
                last_analysis=row['last_analysis'],
                success_rate=row['success_rate'],
                consistency_score=row['consistency_score'],
                expertise_level=row['expertise_level'],
                version=row['version'],
                created_at=row['created_at'],
                updated_at=row['updated_at'],
                metadata=json.loads(row['metadata'])
            )
    
    async def _get_json_record(self, user_id: str) -> Optional[UserProfileRecord]:
        """獲取JSON記錄"""
        if not self.json_path.exists():
            return None
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profile_data = data.get('user_profiles', {}).get(user_id)
        if not profile_data:
            return None
        
        return UserProfileRecord.from_dict(profile_data)
    
    async def get_by_username(self, username: str) -> Optional[UserProfileRecord]:
        """根據用戶名獲取用戶檔案"""
        try:
            if self.config.backend.value == "sqlite":
                return await self._get_sqlite_record_by_username(username)
            elif self.config.backend.value == "json":
                return await self._get_json_record_by_username(username)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get record by username: {e}")
            raise StorageException(f"Get by username failed: {e}")
    
    async def _get_sqlite_record_by_username(self, username: str) -> Optional[UserProfileRecord]:
        """根據用戶名獲取SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                f"SELECT user_id FROM {self.table_name} WHERE username = ?",
                (username,)
            )
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return await self._get_sqlite_record(row['user_id'])
    
    async def _get_json_record_by_username(self, username: str) -> Optional[UserProfileRecord]:
        """根據用戶名獲取JSON記錄"""
        if not self.json_path.exists():
            return None
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for profile_data in data.get('user_profiles', {}).values():
            if profile_data.get('username') == username:
                return UserProfileRecord.from_dict(profile_data)
        
        return None
    
    async def update_record(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新用戶檔案記錄"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            updates['updated_at'] = datetime.now().isoformat()
            
            success = False
            if self.config.backend.value == "sqlite":
                success = await self._update_sqlite_record(user_id, updates)
            elif self.config.backend.value == "json":
                success = await self._update_json_record(user_id, updates)
            
            if success:
                # 清除緩存
                cache_key = self._get_cache_key("user_profile", user_id)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                
                # 更新指標
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                await self._record_operation('write', duration_ms)
                
                self.logger.debug(f"Updated user profile record: {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to update record: {e}")
            raise StorageException(f"Update failed: {e}")
    
    async def _update_sqlite_record(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新SQLite記錄"""
        # 構建更新語句
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['analyst_preferences', 'performance_history', 'preferred_stocks', 
                      'notification_preferences', 'learning_profile', 'adaptation_parameters', 'metadata']:
                if not isinstance(value, str):
                    value = json.dumps(value)
            elif key in ['membership_tier', 'personalization_level', 'user_status'] and hasattr(value, 'value'):
                value = value.value
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        values.append(user_id)
        
        async with aiosqlite.connect(str(self.db_path)) as db:
            cursor = await db.execute(
                f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE user_id = ?",
                values
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def _update_json_record(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """更新JSON記錄"""
        if not self.json_path.exists():
            return False
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if user_id not in data.get('user_profiles', {}):
            return False
        
        # 處理特殊字段
        processed_updates = {}
        for key, value in updates.items():
            if key in ['membership_tier', 'personalization_level', 'user_status'] and hasattr(value, 'value'):
                processed_updates[key] = value.value
            else:
                processed_updates[key] = value
        
        data['user_profiles'][user_id].update(processed_updates)
        
        with open(self.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
    
    async def delete_record(self, user_id: str) -> bool:
        """刪除用戶檔案記錄"""
        try:
            success = False
            if self.config.backend.value == "sqlite":
                success = await self._delete_sqlite_record(user_id)
            elif self.config.backend.value == "json":
                success = await self._delete_json_record(user_id)
            
            if success:
                # 清除緩存
                cache_key = self._get_cache_key("user_profile", user_id)
                if cache_key in self._cache:
                    del self._cache[cache_key]
                    del self._cache_timestamps[cache_key]
                
                self.metrics.total_records -= 1
                self.metrics.delete_operations += 1
                
                self.logger.debug(f"Deleted user profile record: {user_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete record: {e}")
            raise StorageException(f"Delete failed: {e}")
    
    async def _delete_sqlite_record(self, user_id: str) -> bool:
        """刪除SQLite記錄"""
        async with aiosqlite.connect(str(self.db_path)) as db:
            # 刪除相關表記錄
            await db.execute("DELETE FROM performance_history WHERE user_id = ?", (user_id,))
            await db.execute("DELETE FROM analyst_preferences WHERE user_id = ?", (user_id,))
            
            # 刪除主記錄
            cursor = await db.execute(f"DELETE FROM {self.table_name} WHERE user_id = ?", (user_id,))
            await db.commit()
            return cursor.rowcount > 0
    
    async def _delete_json_record(self, user_id: str) -> bool:
        """刪除JSON記錄"""
        if not self.json_path.exists():
            return False
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if user_id in data.get('user_profiles', {}):
            del data['user_profiles'][user_id]
            
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        
        return False
    
    async def query_records(self, query: UserProfileQuery) -> List[UserProfileRecord]:
        """查詢用戶檔案記錄"""
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
    
    async def _query_sqlite_records(self, query: UserProfileQuery) -> List[UserProfileRecord]:
        """查詢SQLite記錄"""
        # 構建WHERE子句
        where_clauses = []
        values = []
        
        if query.user_ids:
            placeholders = ','.join(['?' for _ in query.user_ids])
            where_clauses.append(f"user_id IN ({placeholders})")
            values.extend(query.user_ids)
        
        if query.usernames:
            placeholders = ','.join(['?' for _ in query.usernames])
            where_clauses.append(f"username IN ({placeholders})")
            values.extend(query.usernames)
        
        if query.emails:
            placeholders = ','.join(['?' for _ in query.emails])
            where_clauses.append(f"email IN ({placeholders})")
            values.extend(query.emails)
        
        if query.membership_tiers:
            placeholders = ','.join(['?' for _ in query.membership_tiers])
            where_clauses.append(f"membership_tier IN ({placeholders})")
            values.extend(query.membership_tiers)
        
        if query.personalization_levels:
            placeholders = ','.join(['?' for _ in query.personalization_levels])
            where_clauses.append(f"personalization_level IN ({placeholders})")
            values.extend(query.personalization_levels)
        
        if query.user_statuses:
            placeholders = ','.join(['?' for _ in query.user_statuses])
            where_clauses.append(f"user_status IN ({placeholders})")
            values.extend(query.user_statuses)
        
        if query.min_total_analyses:
            where_clauses.append("total_analyses >= ?")
            values.append(query.min_total_analyses)
        
        if query.max_total_analyses:
            where_clauses.append("total_analyses <= ?")
            values.append(query.max_total_analyses)
        
        if query.min_success_rate:
            where_clauses.append("success_rate >= ?")
            values.append(query.min_success_rate)
        
        if query.max_success_rate:
            where_clauses.append("success_rate <= ?")
            values.append(query.max_success_rate)
        
        # 會員有效性檢查
        if query.membership_active is not None:
            if query.membership_active:
                # 檢查會員是否有效（未過期）
                current_time = datetime.now().isoformat()
                where_clauses.append("(membership_expiry_date = '' OR membership_expiry_date > ?)")
                values.append(current_time)
            else:
                # 檢查會員是否已過期
                current_time = datetime.now().isoformat()
                where_clauses.append("membership_expiry_date != '' AND membership_expiry_date <= ?")
                values.append(current_time)
        
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
                # 獲取分析師偏好和績效歷史
                analyst_preferences = []
                performance_history = []
                
                if query.include_preferences:
                    pref_cursor = await db.execute(
                        "SELECT * FROM analyst_preferences WHERE user_id = ?",
                        (row['user_id'],)
                    )
                    pref_rows = await pref_cursor.fetchall()
                    
                    for pref_row in pref_rows:
                        analyst_preferences.append(AnalystPreference(
                            analyst_type=pref_row['analyst_type'],
                            usage_count=pref_row['usage_count'],
                            average_confidence=pref_row['average_confidence'],
                            last_used=pref_row['last_used'],
                            satisfaction_score=pref_row['satisfaction_score']
                        ))
                
                if query.include_history:
                    perf_cursor = await db.execute(
                        "SELECT * FROM performance_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT 50",
                        (row['user_id'],)
                    )
                    perf_rows = await perf_cursor.fetchall()
                    
                    for perf_row in perf_rows:
                        performance_history.append(PerformanceHistory(
                            timestamp=perf_row['timestamp'],
                            trajectory_id=perf_row['trajectory_id'],
                            reward_value=perf_row['reward_value'],
                            confidence=perf_row['confidence'],
                            recommendation=perf_row['recommendation'],
                            stock_id=perf_row['stock_id'],
                            analyst_type=perf_row['analyst_type']
                        ))
                
                record = UserProfileRecord(
                    user_id=row['user_id'],
                    username=row['username'],
                    email=row['email'],
                    full_name=row['full_name'],
                    membership_tier=MembershipTier(row['membership_tier']),
                    membership_start_date=row['membership_start_date'],
                    membership_expiry_date=row['membership_expiry_date'],
                    total_analyses=row['total_analyses'],
                    total_trajectories=row['total_trajectories'],
                    total_rewards=row['total_rewards'],
                    average_reward=row['average_reward'],
                    personalization_level=PersonalizationLevel(row['personalization_level']),
                    analyst_preferences=analyst_preferences,
                    performance_history=performance_history,
                    preferred_stocks=json.loads(row['preferred_stocks']),
                    risk_tolerance=row['risk_tolerance'],
                    investment_horizon_days=row['investment_horizon_days'],
                    notification_preferences=json.loads(row['notification_preferences']),
                    learning_profile=json.loads(row['learning_profile']) if query.include_learning_data else {},
                    adaptation_parameters=json.loads(row['adaptation_parameters']) if query.include_learning_data else {},
                    user_status=UserStatus(row['user_status']),
                    last_login=row['last_login'],
                    last_analysis=row['last_analysis'],
                    success_rate=row['success_rate'],
                    consistency_score=row['consistency_score'],
                    expertise_level=row['expertise_level'],
                    version=row['version'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    metadata=json.loads(row['metadata']) if query.include_metadata else {}
                )
                records.append(record)
        
        return records
    
    async def _query_json_records(self, query: UserProfileQuery) -> List[UserProfileRecord]:
        """查詢JSON記錄"""
        if not self.json_path.exists():
            return []
        
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profiles = data.get('user_profiles', {})
        records = []
        
        for profile_data in profiles.values():
            # 應用篩選條件
            if query.user_ids and profile_data['user_id'] not in query.user_ids:
                continue
            if query.usernames and profile_data['username'] not in query.usernames:
                continue
            if query.emails and profile_data.get('email') not in query.emails:
                continue
            if query.membership_tiers and profile_data['membership_tier'] not in query.membership_tiers:
                continue
            if query.personalization_levels and profile_data['personalization_level'] not in query.personalization_levels:
                continue
            if query.user_statuses and profile_data['user_status'] not in query.user_statuses:
                continue
            
            # 數量範圍篩選
            if query.min_total_analyses and profile_data['total_analyses'] < query.min_total_analyses:
                continue
            if query.max_total_analyses and profile_data['total_analyses'] > query.max_total_analyses:
                continue
            
            # 績效範圍篩選
            if query.min_success_rate and profile_data['success_rate'] < query.min_success_rate:
                continue
            if query.max_success_rate and profile_data['success_rate'] > query.max_success_rate:
                continue
            
            # 創建記錄（根據包含選項）
            record_data = profile_data.copy()
            if not query.include_preferences:
                record_data['analyst_preferences'] = []
            if not query.include_history:
                record_data['performance_history'] = []
            if not query.include_learning_data:
                record_data['learning_profile'] = {}
                record_data['adaptation_parameters'] = {}
            if not query.include_metadata:
                record_data['metadata'] = {}
            
            records.append(UserProfileRecord.from_dict(record_data))
        
        # 排序
        reverse = query.order_desc
        if query.order_by == "created_at":
            records.sort(key=lambda r: r.created_at, reverse=reverse)
        elif query.order_by == "username":
            records.sort(key=lambda r: r.username, reverse=reverse)
        elif query.order_by == "total_analyses":
            records.sort(key=lambda r: r.total_analyses, reverse=reverse)
        elif query.order_by == "success_rate":
            records.sort(key=lambda r: r.success_rate, reverse=reverse)
        
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
        
        return len(data.get('user_profiles', {}))
    
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
    
    def _validate_record(self, record: UserProfileRecord) -> bool:
        """驗證用戶檔案記錄"""
        if not record.user_id or not record.username:
            return False
        if record.risk_tolerance < 0 or record.risk_tolerance > 1:
            return False
        if record.investment_horizon_days <= 0:
            return False
        if record.success_rate < 0 or record.success_rate > 1:
            return False
        if record.consistency_score < 0 or record.consistency_score > 1:
            return False
        return True
    
    # 特殊查詢方法
    async def get_active_users(self, days: int = 30) -> List[UserProfileRecord]:
        """獲取活躍用戶"""
        try:
            # 計算時間範圍
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            
            query = UserProfileQuery(
                user_statuses=['active'],
                last_login_from=start_time.isoformat(),
                order_by="last_login",
                order_desc=True,
                limit=500
            )
            
            return await self.query_records(query)
            
        except Exception as e:
            self.logger.error(f"Failed to get active users: {e}")
            raise StorageException(f"Get active users failed: {e}")
    
    async def get_membership_statistics(self) -> Dict[str, Any]:
        """獲取會員統計信息"""
        try:
            stats = {
                'total_users': 0,
                'by_tier': {},
                'active_members': 0,
                'expired_members': 0
            }
            
            if self.config.backend.value == "sqlite":
                async with aiosqlite.connect(str(self.db_path)) as db:
                    # 總用戶數
                    cursor = await db.execute(f"SELECT COUNT(*) FROM {self.table_name}")
                    row = await cursor.fetchone()
                    stats['total_users'] = row[0] if row else 0
                    
                    # 按會員等級統計
                    cursor = await db.execute(f"SELECT membership_tier, COUNT(*) FROM {self.table_name} GROUP BY membership_tier")
                    rows = await cursor.fetchall()
                    for row in rows:
                        stats['by_tier'][row[0]] = row[1]
                    
                    # 有效會員數
                    current_time = datetime.now().isoformat()
                    cursor = await db.execute(f"""
                        SELECT COUNT(*) FROM {self.table_name} 
                        WHERE membership_tier != 'FREE' AND 
                        (membership_expiry_date = '' OR membership_expiry_date > ?)
                    """, (current_time,))
                    row = await cursor.fetchone()
                    stats['active_members'] = row[0] if row else 0
                    
                    # 過期會員數
                    cursor = await db.execute(f"""
                        SELECT COUNT(*) FROM {self.table_name} 
                        WHERE membership_tier != 'FREE' AND 
                        membership_expiry_date != '' AND membership_expiry_date <= ?
                    """, (current_time,))
                    row = await cursor.fetchone()
                    stats['expired_members'] = row[0] if row else 0
            
            elif self.config.backend.value == "json":
                if self.json_path.exists():
                    with open(self.json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    profiles = data.get('user_profiles', {})
                    stats['total_users'] = len(profiles)
                    
                    # 按會員等級統計
                    tier_counts = {}
                    current_time = datetime.now().isoformat()
                    active_members = 0
                    expired_members = 0
                    
                    for profile in profiles.values():
                        tier = profile['membership_tier']
                        tier_counts[tier] = tier_counts.get(tier, 0) + 1
                        
                        if tier != 'FREE':
                            expiry_date = profile.get('membership_expiry_date', '')
                            if not expiry_date or expiry_date > current_time:
                                active_members += 1
                            else:
                                expired_members += 1
                    
                    stats['by_tier'] = tier_counts
                    stats['active_members'] = active_members
                    stats['expired_members'] = expired_members
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get membership statistics: {e}")
            raise StorageException(f"Membership statistics failed: {e}")

# 工廠函數
async def create_user_profile_storage(
    storage_path: str = "./art_storage",
    backend: str = "json",
    **kwargs
) -> UserProfileStorage:
    """創建用戶檔案存儲實例"""
    
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
    
    storage = UserProfileStorage(config)
    
    if await storage.initialize():
        await storage.connect()
        return storage
    else:
        raise StorageException("Failed to initialize user profile storage")