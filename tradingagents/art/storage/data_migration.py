#!/usr/bin/env python3
"""
Data Migration Engine - 數據遷移引擎
天工 (TianGong) - 為ART存儲系統提供企業級數據遷移和版本管理

此模組提供：
1. DataMigrationEngine - 數據遷移執行引擎
2. MigrationPlan - 遷移計劃管理器
3. VersionManager - 數據版本管理器
4. SchemaEvolution - 架構演進管理
5. DataTransformer - 數據轉換器
6. BackupManager - 遷移備份管理
"""

from typing import Dict, Any, List, Optional, Union, Tuple, AsyncGenerator, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import hashlib
import os
import shutil
import sqlite3
from pathlib import Path
from collections import defaultdict, OrderedDict
import uuid

class MigrationStatus(Enum):
    """遷移狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class MigrationDirection(Enum):
    """遷移方向"""
    UP = "up"      # 向前遷移
    DOWN = "down"  # 回滾遷移

class DataType(Enum):
    """數據類型"""
    TRAJECTORY = "trajectory"
    REWARD = "reward"
    USER_PROFILE = "user_profile"
    ANALYTICS = "analytics"
    METADATA = "metadata"

@dataclass
class MigrationStep:
    """遷移步驟"""
    step_id: str
    name: str
    description: str
    up_sql: Optional[str] = None
    down_sql: Optional[str] = None
    up_script: Optional[Callable] = None
    down_script: Optional[Callable] = None
    dependencies: List[str] = field(default_factory=list)
    data_types: List[DataType] = field(default_factory=list)
    estimated_duration: float = 0.0  # 預估執行時間（秒）
    batch_size: int = 1000
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MigrationResult:
    """遷移結果"""
    step_id: str
    status: MigrationStatus
    start_time: float
    end_time: Optional[float] = None
    records_processed: int = 0
    records_failed: int = 0
    error_message: Optional[str] = None
    rollback_info: Optional[Dict[str, Any]] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DataVersion:
    """數據版本"""
    version: str
    timestamp: float
    description: str
    schema_hash: str
    migration_steps: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class SchemaEvolution:
    """架構演進管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.schema_history: List[Dict[str, Any]] = []
        self._lock = asyncio.Lock()
    
    async def get_current_schema(self) -> Dict[str, Any]:
        """獲取當前架構"""
        async with self._lock:
            schema = {
                'tables': {},
                'indexes': {},
                'version': None
            }
            
            try:
                # 使用SQLite獲取架構信息
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 獲取表結構
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                for (table_name,) in tables:
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    
                    schema['tables'][table_name] = {
                        'columns': [
                            {
                                'name': col[1],
                                'type': col[2],
                                'not_null': bool(col[3]),
                                'default': col[4],
                                'primary_key': bool(col[5])
                            }
                            for col in columns
                        ]
                    }
                
                # 獲取索引信息
                cursor.execute("SELECT name, tbl_name, sql FROM sqlite_master WHERE type='index'")
                indexes = cursor.fetchall()
                
                for idx_name, table_name, sql in indexes:
                    if idx_name not in schema['indexes']:
                        schema['indexes'][idx_name] = {
                            'table': table_name,
                            'sql': sql
                        }
                
                conn.close()
                
            except Exception as e:
                logging.error(f"Failed to get current schema: {e}")
            
            return schema
    
    async def compare_schemas(self, old_schema: Dict[str, Any], 
                            new_schema: Dict[str, Any]) -> Dict[str, Any]:
        """比較架構差異"""
        differences = {
            'added_tables': [],
            'removed_tables': [],
            'modified_tables': [],
            'added_indexes': [],
            'removed_indexes': []
        }
        
        old_tables = set(old_schema.get('tables', {}).keys())
        new_tables = set(new_schema.get('tables', {}).keys())
        
        differences['added_tables'] = list(new_tables - old_tables)
        differences['removed_tables'] = list(old_tables - new_tables)
        
        # 檢查修改的表
        common_tables = old_tables & new_tables
        for table_name in common_tables:
            old_cols = old_schema['tables'][table_name]['columns']
            new_cols = new_schema['tables'][table_name]['columns']
            
            old_col_names = {col['name'] for col in old_cols}
            new_col_names = {col['name'] for col in new_cols}
            
            if old_col_names != new_col_names:
                differences['modified_tables'].append({
                    'table': table_name,
                    'added_columns': list(new_col_names - old_col_names),
                    'removed_columns': list(old_col_names - new_col_names)
                })
        
        return differences
    
    def calculate_schema_hash(self, schema: Dict[str, Any]) -> str:
        """計算架構哈希"""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()

class DataTransformer:
    """數據轉換器"""
    
    def __init__(self):
        self.transformers: Dict[str, Callable] = {}
    
    def register_transformer(self, data_type: str, transformer: Callable):
        """註冊數據轉換器"""
        self.transformers[data_type] = transformer
    
    async def transform_data(self, data_type: str, old_data: Any, 
                           version_from: str, version_to: str) -> Any:
        """轉換數據"""
        if data_type not in self.transformers:
            return old_data
        
        transformer = self.transformers[data_type]
        
        if asyncio.iscoroutinefunction(transformer):
            return await transformer(old_data, version_from, version_to)
        else:
            return transformer(old_data, version_from, version_to)
    
    async def batch_transform(self, data_type: str, data_batch: List[Any],
                            version_from: str, version_to: str) -> List[Any]:
        """批量轉換數據"""
        results = []
        
        for data_item in data_batch:
            transformed = await self.transform_data(
                data_type, data_item, version_from, version_to
            )
            results.append(transformed)
        
        return results

class BackupManager:
    """備份管理器"""
    
    def __init__(self, backup_dir: str):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, source_path: str, backup_name: str) -> str:
        """創建備份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{backup_name}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_filename
        
        try:
            if os.path.isfile(source_path):
                shutil.copy2(source_path, backup_path)
            else:
                shutil.copytree(source_path, backup_path)
            
            return str(backup_path)
            
        except Exception as e:
            logging.error(f"Failed to create backup: {e}")
            raise
    
    async def restore_backup(self, backup_path: str, target_path: str):
        """恢復備份"""
        try:
            if os.path.isfile(backup_path):
                shutil.copy2(backup_path, target_path)
            else:
                if os.path.exists(target_path):
                    shutil.rmtree(target_path)
                shutil.copytree(backup_path, target_path)
            
        except Exception as e:
            logging.error(f"Failed to restore backup: {e}")
            raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """列出所有備份"""
        backups = []
        
        for backup_file in self.backup_dir.glob("*.backup"):
            stat = backup_file.stat()
            backups.append({
                'name': backup_file.name,
                'path': str(backup_file),
                'size': stat.st_size,
                'created': stat.st_ctime
            })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

class VersionManager:
    """版本管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.versions: Dict[str, DataVersion] = {}
        self.current_version: Optional[str] = None
        self._init_version_table()
    
    def _init_version_table(self):
        """初始化版本表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_versions (
                    version TEXT PRIMARY KEY,
                    timestamp REAL NOT NULL,
                    description TEXT NOT NULL,
                    schema_hash TEXT NOT NULL,
                    migration_steps TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to initialize version table: {e}")
    
    async def create_version(self, version: str, description: str,
                           schema_hash: str, migration_steps: List[str] = None,
                           metadata: Dict[str, Any] = None) -> DataVersion:
        """創建新版本"""
        data_version = DataVersion(
            version=version,
            timestamp=time.time(),
            description=description,
            schema_hash=schema_hash,
            migration_steps=migration_steps or [],
            metadata=metadata or {}
        )
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO data_versions 
                (version, timestamp, description, schema_hash, migration_steps, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                version,
                data_version.timestamp,
                description,
                schema_hash,
                json.dumps(migration_steps or []),
                json.dumps(metadata or {})
            ))
            
            conn.commit()
            conn.close()
            
            self.versions[version] = data_version
            
        except Exception as e:
            logging.error(f"Failed to create version: {e}")
            raise
        
        return data_version
    
    async def get_version(self, version: str) -> Optional[DataVersion]:
        """獲取版本信息"""
        if version in self.versions:
            return self.versions[version]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT version, timestamp, description, schema_hash, migration_steps, metadata
                FROM data_versions WHERE version = ?
            """, (version,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                data_version = DataVersion(
                    version=row[0],
                    timestamp=row[1],
                    description=row[2],
                    schema_hash=row[3],
                    migration_steps=json.loads(row[4]),
                    metadata=json.loads(row[5])
                )
                self.versions[version] = data_version
                return data_version
            
        except Exception as e:
            logging.error(f"Failed to get version {version}: {e}")
        
        return None
    
    async def list_versions(self) -> List[DataVersion]:
        """列出所有版本"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT version, timestamp, description, schema_hash, migration_steps, metadata
                FROM data_versions ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            versions = []
            for row in rows:
                version = DataVersion(
                    version=row[0],
                    timestamp=row[1],
                    description=row[2],
                    schema_hash=row[3],
                    migration_steps=json.loads(row[4]),
                    metadata=json.loads(row[5])
                )
                versions.append(version)
                self.versions[row[0]] = version
            
            return versions
            
        except Exception as e:
            logging.error(f"Failed to list versions: {e}")
            return []
    
    async def set_current_version(self, version: str):
        """設置當前版本"""
        self.current_version = version

class MigrationPlan:
    """遷移計劃"""
    
    def __init__(self, plan_id: str, name: str, description: str):
        self.plan_id = plan_id
        self.name = name
        self.description = description
        self.steps: List[MigrationStep] = []
        self.created_at = time.time()
        self.metadata: Dict[str, Any] = {}
    
    def add_step(self, step: MigrationStep):
        """添加遷移步驟"""
        self.steps.append(step)
    
    def get_execution_order(self) -> List[MigrationStep]:
        """獲取執行順序（拓撲排序）"""
        # 簡化的拓撲排序實現
        ordered_steps = []
        remaining_steps = self.steps.copy()
        
        while remaining_steps:
            # 查找沒有未滿足依賴的步驟
            ready_steps = []
            for step in remaining_steps:
                if all(dep in [s.step_id for s in ordered_steps] for dep in step.dependencies):
                    ready_steps.append(step)
            
            if not ready_steps:
                # 檢查是否有循環依賴
                raise ValueError("Circular dependency detected in migration plan")
            
            # 添加準備好的步驟
            for step in ready_steps:
                ordered_steps.append(step)
                remaining_steps.remove(step)
        
        return ordered_steps
    
    def estimate_duration(self) -> float:
        """估算總執行時間"""
        return sum(step.estimated_duration for step in self.steps)

class DataMigrationEngine:
    """數據遷移執行引擎"""
    
    def __init__(self, db_path: str, backup_dir: str = None):
        self.db_path = db_path
        self.backup_manager = BackupManager(backup_dir or "./backups")
        self.version_manager = VersionManager(db_path)
        self.schema_evolution = SchemaEvolution(db_path)
        self.data_transformer = DataTransformer()
        
        self.migration_history: List[MigrationResult] = []
        self._lock = asyncio.Lock()
    
    async def execute_migration_plan(self, plan: MigrationPlan, 
                                   direction: MigrationDirection = MigrationDirection.UP,
                                   create_backup: bool = True) -> List[MigrationResult]:
        """執行遷移計劃"""
        async with self._lock:
            results = []
            
            try:
                # 創建備份
                if create_backup:
                    backup_path = await self.backup_manager.create_backup(
                        self.db_path, f"pre_migration_{plan.plan_id}"
                    )
                    logging.info(f"Created backup: {backup_path}")
                
                # 獲取執行順序
                if direction == MigrationDirection.UP:
                    steps = plan.get_execution_order()
                else:
                    steps = list(reversed(plan.get_execution_order()))
                
                # 執行遷移步驟
                for step in steps:
                    result = await self._execute_step(step, direction)
                    results.append(result)
                    self.migration_history.append(result)
                    
                    if result.status == MigrationStatus.FAILED:
                        logging.error(f"Migration step failed: {step.step_id}")
                        break
                
                # 更新版本信息
                if direction == MigrationDirection.UP and all(r.status == MigrationStatus.COMPLETED for r in results):
                    current_schema = await self.schema_evolution.get_current_schema()
                    schema_hash = self.schema_evolution.calculate_schema_hash(current_schema)
                    
                    new_version = f"v_{int(time.time())}"
                    await self.version_manager.create_version(
                        new_version,
                        f"Migration plan: {plan.name}",
                        schema_hash,
                        [step.step_id for step in steps]
                    )
                    await self.version_manager.set_current_version(new_version)
                
                return results
                
            except Exception as e:
                logging.error(f"Migration plan execution failed: {e}")
                
                # 創建失敗結果
                error_result = MigrationResult(
                    step_id="PLAN_EXECUTION",
                    status=MigrationStatus.FAILED,
                    start_time=time.time(),
                    error_message=str(e)
                )
                results.append(error_result)
                
                return results
    
    async def _execute_step(self, step: MigrationStep, 
                          direction: MigrationDirection) -> MigrationResult:
        """執行單個遷移步驟"""
        result = MigrationResult(
            step_id=step.step_id,
            status=MigrationStatus.RUNNING,
            start_time=time.time()
        )
        
        try:
            logging.info(f"Executing migration step: {step.step_id} ({direction.value})")
            
            if direction == MigrationDirection.UP:
                if step.up_sql:
                    await self._execute_sql(step.up_sql, result)
                elif step.up_script:
                    await self._execute_script(step.up_script, result)
            else:  # DOWN
                if step.down_sql:
                    await self._execute_sql(step.down_sql, result)
                elif step.down_script:
                    await self._execute_script(step.down_script, result)
            
            result.status = MigrationStatus.COMPLETED
            result.end_time = time.time()
            
        except Exception as e:
            result.status = MigrationStatus.FAILED
            result.end_time = time.time()
            result.error_message = str(e)
            logging.error(f"Migration step {step.step_id} failed: {e}")
        
        return result
    
    async def _execute_sql(self, sql: str, result: MigrationResult):
        """執行SQL語句"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 分割並執行多個SQL語句
            statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
            
            for statement in statements:
                cursor.execute(statement)
                result.records_processed += cursor.rowcount
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            result.records_failed += 1
            raise e
    
    async def _execute_script(self, script: Callable, result: MigrationResult):
        """執行Python腳本"""
        try:
            if asyncio.iscoroutinefunction(script):
                script_result = await script(self.db_path)
            else:
                script_result = script(self.db_path)
            
            if isinstance(script_result, dict):
                result.records_processed = script_result.get('processed', 0)
                result.records_failed = script_result.get('failed', 0)
                result.performance_metrics.update(script_result.get('metrics', {}))
                
        except Exception as e:
            result.records_failed += 1
            raise e
    
    async def rollback_to_version(self, target_version: str) -> List[MigrationResult]:
        """回滾到指定版本"""
        current_version = self.version_manager.current_version
        
        if not current_version:
            raise ValueError("No current version set")
        
        target_ver = await self.version_manager.get_version(target_version)
        if not target_ver:
            raise ValueError(f"Target version {target_version} not found")
        
        # 這裡需要實現復雜的回滾邏輯
        # 為了簡化，我們使用備份恢復
        backups = self.backup_manager.list_backups()
        
        # 查找最接近目標版本的備份
        suitable_backup = None
        for backup in backups:
            # 簡化的備份匹配邏輯
            if target_version in backup['name']:
                suitable_backup = backup
                break
        
        if suitable_backup:
            await self.backup_manager.restore_backup(
                suitable_backup['path'], self.db_path
            )
            await self.version_manager.set_current_version(target_version)
        
        return []
    
    def get_migration_history(self) -> List[MigrationResult]:
        """獲取遷移歷史"""
        return self.migration_history.copy()
    
    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        current_schema = await self.schema_evolution.get_current_schema()
        versions = await self.version_manager.list_versions()
        backups = self.backup_manager.list_backups()
        
        return {
            'current_version': self.version_manager.current_version,
            'schema_hash': self.schema_evolution.calculate_schema_hash(current_schema),
            'total_versions': len(versions),
            'total_backups': len(backups),
            'migration_history_count': len(self.migration_history),
            'last_migration': self.migration_history[-1] if self.migration_history else None
        }

# 工廠函數
def create_migration_engine(db_path: str, backup_dir: str = None) -> DataMigrationEngine:
    """創建數據遷移引擎"""
    return DataMigrationEngine(db_path, backup_dir)

def create_migration_plan(plan_id: str, name: str, description: str) -> MigrationPlan:
    """創建遷移計劃"""
    return MigrationPlan(plan_id, name, description)

def create_migration_step(step_id: str, name: str, description: str,
                         up_sql: str = None, down_sql: str = None,
                         **kwargs) -> MigrationStep:
    """創建遷移步驟"""
    return MigrationStep(
        step_id=step_id,
        name=name,
        description=description,
        up_sql=up_sql,
        down_sql=down_sql,
        **kwargs
    )