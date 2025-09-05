#!/usr/bin/env python3
"""
Version Control System - 數據版本控制系統
天工 (TianGong) - 為ART存儲系統提供Git風格的數據版本控制

此模組提供：
1. DataVersionControl - 數據版本控制核心
2. DataCommit - 數據提交管理
3. DataBranch - 數據分支管理
4. DataMerge - 數據合併引擎
5. VersionHistory - 版本歷史追蹤
6. ConflictResolver - 衝突解決器
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import hashlib
import os
import sqlite3
import uuid
import difflib
from collections import defaultdict, OrderedDict
from pathlib import Path

class CommitType(Enum):
    """提交類型"""
    INITIAL = "initial"       # 初始提交
    FEATURE = "feature"       # 功能提交
    BUGFIX = "bugfix"        # 錯誤修復
    REFACTOR = "refactor"    # 重構
    MERGE = "merge"          # 合併提交
    ROLLBACK = "rollback"    # 回滾提交

class MergeStrategy(Enum):
    """合併策略"""
    AUTO = "auto"           # 自動合併
    MANUAL = "manual"       # 手動合併
    OURS = "ours"          # 使用當前分支
    THEIRS = "theirs"      # 使用目標分支
    THREE_WAY = "three_way" # 三方合併

class ConflictType(Enum):
    """衝突類型"""
    DATA_CONFLICT = "data_conflict"       # 數據衝突
    SCHEMA_CONFLICT = "schema_conflict"   # 架構衝突
    DELETE_MODIFY = "delete_modify"       # 刪除-修改衝突
    RENAME_RENAME = "rename_rename"       # 重命名衝突

@dataclass
class DataCommit:
    """數據提交"""
    commit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_commits: List[str] = field(default_factory=list)
    branch_name: str = "main"
    commit_type: CommitType = CommitType.FEATURE
    message: str = ""
    author: str = "system"
    timestamp: float = field(default_factory=time.time)
    changes: Dict[str, Any] = field(default_factory=dict)
    affected_tables: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def short_id(self) -> str:
        """短版本ID"""
        return self.commit_id[:8]
    
    @property
    def is_merge_commit(self) -> bool:
        """是否為合併提交"""
        return len(self.parent_commits) > 1

@dataclass
class DataBranch:
    """數據分支"""
    branch_name: str
    head_commit: str
    base_commit: str
    created_at: float = field(default_factory=time.time)
    created_by: str = "system"
    description: str = ""
    is_active: bool = True
    merge_target: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChangeRecord:
    """變更記錄"""
    table_name: str
    operation: str  # INSERT, UPDATE, DELETE
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    primary_key: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class ConflictInfo:
    """衝突信息"""
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.DATA_CONFLICT
    table_name: str = ""
    primary_key: Dict[str, Any] = field(default_factory=dict)
    base_data: Optional[Dict[str, Any]] = None
    current_data: Optional[Dict[str, Any]] = None
    incoming_data: Optional[Dict[str, Any]] = None
    resolution: Optional[Dict[str, Any]] = None
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConflictResolver:
    """衝突解決器"""
    
    def __init__(self):
        self.resolution_strategies = {
            ConflictType.DATA_CONFLICT: self._resolve_data_conflict,
            ConflictType.SCHEMA_CONFLICT: self._resolve_schema_conflict,
            ConflictType.DELETE_MODIFY: self._resolve_delete_modify_conflict,
            ConflictType.RENAME_RENAME: self._resolve_rename_conflict
        }
    
    async def detect_conflicts(self, base_changes: List[ChangeRecord],
                             current_changes: List[ChangeRecord],
                             incoming_changes: List[ChangeRecord]) -> List[ConflictInfo]:
        """檢測衝突"""
        conflicts = []
        
        # 按表和主鍵組織變更
        current_by_key = self._group_changes_by_key(current_changes)
        incoming_by_key = self._group_changes_by_key(incoming_changes)
        
        # 檢測每個鍵的衝突
        all_keys = set(current_by_key.keys()) | set(incoming_by_key.keys())
        
        for key in all_keys:
            current_change = current_by_key.get(key)
            incoming_change = incoming_by_key.get(key)
            
            if current_change and incoming_change:
                conflict = await self._analyze_conflict(key, current_change, incoming_change)
                if conflict:
                    conflicts.append(conflict)
        
        return conflicts
    
    def _group_changes_by_key(self, changes: List[ChangeRecord]) -> Dict[str, ChangeRecord]:
        """按鍵分組變更"""
        result = {}
        for change in changes:
            key = f"{change.table_name}:{json.dumps(change.primary_key, sort_keys=True)}"
            result[key] = change
        return result
    
    async def _analyze_conflict(self, key: str, current: ChangeRecord, 
                              incoming: ChangeRecord) -> Optional[ConflictInfo]:
        """分析具體衝突"""
        table_name = current.table_name
        
        # 檢查是否真的有衝突
        if current.operation == incoming.operation == "UPDATE":
            if current.new_data != incoming.new_data:
                return ConflictInfo(
                    conflict_type=ConflictType.DATA_CONFLICT,
                    table_name=table_name,
                    primary_key=current.primary_key,
                    current_data=current.new_data,
                    incoming_data=incoming.new_data
                )
        
        elif (current.operation == "DELETE" and incoming.operation == "UPDATE") or \
             (current.operation == "UPDATE" and incoming.operation == "DELETE"):
            return ConflictInfo(
                conflict_type=ConflictType.DELETE_MODIFY,
                table_name=table_name,
                primary_key=current.primary_key,
                current_data=current.new_data if current.operation == "UPDATE" else None,
                incoming_data=incoming.new_data if incoming.operation == "UPDATE" else None
            )
        
        return None
    
    async def resolve_conflicts(self, conflicts: List[ConflictInfo],
                              strategy: MergeStrategy = MergeStrategy.AUTO) -> List[ConflictInfo]:
        """解決衝突"""
        resolved_conflicts = []
        
        for conflict in conflicts:
            if strategy == MergeStrategy.AUTO:
                await self._auto_resolve_conflict(conflict)
            elif strategy == MergeStrategy.OURS:
                conflict.resolution = conflict.current_data
                conflict.resolved = True
            elif strategy == MergeStrategy.THEIRS:
                conflict.resolution = conflict.incoming_data
                conflict.resolved = True
            elif strategy == MergeStrategy.THREE_WAY:
                await self._three_way_resolve(conflict)
            
            resolved_conflicts.append(conflict)
        
        return resolved_conflicts
    
    async def _auto_resolve_conflict(self, conflict: ConflictInfo):
        """自動解決衝突"""
        resolver = self.resolution_strategies.get(conflict.conflict_type)
        if resolver:
            await resolver(conflict)
    
    async def _resolve_data_conflict(self, conflict: ConflictInfo):
        """解決數據衝突"""
        current = conflict.current_data or {}
        incoming = conflict.incoming_data or {}
        
        # 簡單的字段級合併策略
        resolution = current.copy()
        
        for key, incoming_value in incoming.items():
            if key not in current:
                # 新字段，直接添加
                resolution[key] = incoming_value
            elif current[key] != incoming_value:
                # 衝突字段，使用時間戳較新的值（簡化策略）
                # 實際應用中可能需要更複雜的策略
                resolution[key] = incoming_value
        
        conflict.resolution = resolution
        conflict.resolved = True
    
    async def _resolve_schema_conflict(self, conflict: ConflictInfo):
        """解決架構衝突"""
        # 架構衝突通常需要人工介入
        conflict.resolved = False
    
    async def _resolve_delete_modify_conflict(self, conflict: ConflictInfo):
        """解決刪除-修改衝突"""
        # 預設保留修改，忽略刪除
        if conflict.current_data:
            conflict.resolution = conflict.current_data
        elif conflict.incoming_data:
            conflict.resolution = conflict.incoming_data
        
        conflict.resolved = True
    
    async def _resolve_rename_conflict(self, conflict: ConflictInfo):
        """解決重命名衝突"""
        # 重命名衝突需要人工解決
        conflict.resolved = False
    
    async def _three_way_resolve(self, conflict: ConflictInfo):
        """三方合併解決"""
        # 實現三方合併邏輯
        # 這是一個複雜的算法，這裡提供簡化版本
        await self._auto_resolve_conflict(conflict)

class VersionHistory:
    """版本歷史追蹤"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_history_tables()
    
    def _init_history_tables(self):
        """初始化歷史表"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 提交歷史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS version_commits (
                    commit_id TEXT PRIMARY KEY,
                    parent_commits TEXT NOT NULL,
                    branch_name TEXT NOT NULL,
                    commit_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    changes TEXT NOT NULL,
                    affected_tables TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            
            # 分支表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS version_branches (
                    branch_name TEXT PRIMARY KEY,
                    head_commit TEXT NOT NULL,
                    base_commit TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    created_by TEXT NOT NULL,
                    description TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL,
                    merge_target TEXT,
                    metadata TEXT NOT NULL
                )
            """)
            
            # 變更記錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS version_changes (
                    change_id TEXT PRIMARY KEY,
                    commit_id TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    old_data TEXT,
                    new_data TEXT,
                    primary_key TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (commit_id) REFERENCES version_commits (commit_id)
                )
            """)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to initialize version history tables: {e}")
    
    async def record_commit(self, commit: DataCommit, changes: List[ChangeRecord]):
        """記錄提交"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 插入提交記錄
            cursor.execute("""
                INSERT INTO version_commits 
                (commit_id, parent_commits, branch_name, commit_type, message, author, 
                 timestamp, changes, affected_tables, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                commit.commit_id,
                json.dumps(commit.parent_commits),
                commit.branch_name,
                commit.commit_type.value,
                commit.message,
                commit.author,
                commit.timestamp,
                json.dumps(commit.changes),
                json.dumps(list(commit.affected_tables)),
                json.dumps(commit.metadata)
            ))
            
            # 插入變更記錄
            for change in changes:
                change_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO version_changes 
                    (change_id, commit_id, table_name, operation, old_data, new_data, 
                     primary_key, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    change_id,
                    commit.commit_id,
                    change.table_name,
                    change.operation,
                    json.dumps(change.old_data) if change.old_data else None,
                    json.dumps(change.new_data) if change.new_data else None,
                    json.dumps(change.primary_key),
                    change.timestamp
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to record commit: {e}")
            raise
    
    async def get_commit_history(self, branch_name: str = None,
                               limit: int = 100) -> List[DataCommit]:
        """獲取提交歷史"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if branch_name:
                cursor.execute("""
                    SELECT * FROM version_commits 
                    WHERE branch_name = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (branch_name, limit))
            else:
                cursor.execute("""
                    SELECT * FROM version_commits 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            commits = []
            for row in rows:
                commit = DataCommit(
                    commit_id=row[0],
                    parent_commits=json.loads(row[1]),
                    branch_name=row[2],
                    commit_type=CommitType(row[3]),
                    message=row[4],
                    author=row[5],
                    timestamp=row[6],
                    changes=json.loads(row[7]),
                    affected_tables=set(json.loads(row[8])),
                    metadata=json.loads(row[9])
                )
                commits.append(commit)
            
            return commits
            
        except Exception as e:
            logging.error(f"Failed to get commit history: {e}")
            return []
    
    async def get_changes_for_commit(self, commit_id: str) -> List[ChangeRecord]:
        """獲取提交的變更"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name, operation, old_data, new_data, primary_key, timestamp
                FROM version_changes 
                WHERE commit_id = ?
            """, (commit_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            changes = []
            for row in rows:
                change = ChangeRecord(
                    table_name=row[0],
                    operation=row[1],
                    old_data=json.loads(row[2]) if row[2] else None,
                    new_data=json.loads(row[3]) if row[3] else None,
                    primary_key=json.loads(row[4]),
                    timestamp=row[5]
                )
                changes.append(change)
            
            return changes
            
        except Exception as e:
            logging.error(f"Failed to get changes for commit: {e}")
            return []

class DataMerge:
    """數據合併引擎"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conflict_resolver = ConflictResolver()
        self.history = VersionHistory(db_path)
    
    async def merge_branches(self, source_branch: str, target_branch: str,
                           strategy: MergeStrategy = MergeStrategy.AUTO) -> Dict[str, Any]:
        """合併分支"""
        merge_result = {
            'success': False,
            'merge_commit': None,
            'conflicts': [],
            'resolved_conflicts': [],
            'error': None
        }
        
        try:
            # 獲取分支信息
            source_commits = await self.history.get_commit_history(source_branch)
            target_commits = await self.history.get_commit_history(target_branch)
            
            if not source_commits or not target_commits:
                merge_result['error'] = "Invalid branch"
                return merge_result
            
            # 找到共同祖先
            common_ancestor = await self._find_common_ancestor(source_commits, target_commits)
            
            # 獲取變更集
            source_changes = await self._get_changes_since_commit(common_ancestor, source_branch)
            target_changes = await self._get_changes_since_commit(common_ancestor, target_branch)
            
            # 檢測衝突
            conflicts = await self.conflict_resolver.detect_conflicts(
                [], target_changes, source_changes
            )
            
            merge_result['conflicts'] = conflicts
            
            if conflicts and strategy != MergeStrategy.MANUAL:
                # 自動解決衝突
                resolved_conflicts = await self.conflict_resolver.resolve_conflicts(
                    conflicts, strategy
                )
                merge_result['resolved_conflicts'] = resolved_conflicts
                
                # 檢查是否還有未解決的衝突
                unresolved = [c for c in resolved_conflicts if not c.resolved]
                if unresolved:
                    merge_result['error'] = f"Unable to resolve {len(unresolved)} conflicts"
                    return merge_result
            
            # 執行合併
            merge_commit = await self._execute_merge(
                source_branch, target_branch, source_changes, resolved_conflicts
            )
            
            merge_result['merge_commit'] = merge_commit
            merge_result['success'] = True
            
        except Exception as e:
            merge_result['error'] = str(e)
            logging.error(f"Merge failed: {e}")
        
        return merge_result
    
    async def _find_common_ancestor(self, commits1: List[DataCommit],
                                  commits2: List[DataCommit]) -> Optional[str]:
        """找到共同祖先"""
        commit_ids1 = {c.commit_id for c in commits1}
        
        for commit in commits2:
            if commit.commit_id in commit_ids1:
                return commit.commit_id
        
        return None
    
    async def _get_changes_since_commit(self, ancestor_commit: str,
                                     branch_name: str) -> List[ChangeRecord]:
        """獲取自指定提交以來的變更"""
        commits = await self.history.get_commit_history(branch_name)
        changes = []
        
        for commit in commits:
            if commit.commit_id == ancestor_commit:
                break
            
            commit_changes = await self.history.get_changes_for_commit(commit.commit_id)
            changes.extend(commit_changes)
        
        return changes
    
    async def _execute_merge(self, source_branch: str, target_branch: str,
                           changes: List[ChangeRecord],
                           resolved_conflicts: List[ConflictInfo]) -> DataCommit:
        """執行合併"""
        # 創建合併提交
        merge_commit = DataCommit(
            parent_commits=[
                (await self.history.get_commit_history(target_branch, 1))[0].commit_id,
                (await self.history.get_commit_history(source_branch, 1))[0].commit_id
            ],
            branch_name=target_branch,
            commit_type=CommitType.MERGE,
            message=f"Merge branch '{source_branch}' into '{target_branch}'",
            author="system",
            affected_tables={change.table_name for change in changes}
        )
        
        # 應用變更和衝突解決
        await self._apply_changes(changes, resolved_conflicts)
        
        # 記錄合併提交
        await self.history.record_commit(merge_commit, changes)
        
        return merge_commit
    
    async def _apply_changes(self, changes: List[ChangeRecord],
                           resolved_conflicts: List[ConflictInfo]):
        """應用變更"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 應用衝突解決
            for conflict in resolved_conflicts:
                if conflict.resolved and conflict.resolution:
                    # 這裡需要根據具體的數據結構來實現更新邏輯
                    # 簡化實現
                    pass
            
            # 應用其他變更
            for change in changes:
                if change.operation == "INSERT" and change.new_data:
                    # 構建插入語句
                    pass
                elif change.operation == "UPDATE" and change.new_data:
                    # 構建更新語句
                    pass
                elif change.operation == "DELETE":
                    # 構建刪除語句
                    pass
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to apply changes: {e}")
            raise

class DataVersionControl:
    """數據版本控制核心"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.history = VersionHistory(db_path)
        self.merge_engine = DataMerge(db_path)
        self.branches: Dict[str, DataBranch] = {}
        self.current_branch = "main"
        
        # 初始化版本控制
        asyncio.create_task(self._initialize())
    
    async def _initialize(self):
        """初始化版本控制系統"""
        try:
            # 創建主分支
            if "main" not in self.branches:
                main_branch = DataBranch(
                    branch_name="main",
                    head_commit="",
                    base_commit="",
                    description="Main branch"
                )
                self.branches["main"] = main_branch
                await self._save_branch(main_branch)
            
        except Exception as e:
            logging.error(f"Failed to initialize version control: {e}")
    
    async def create_commit(self, message: str, author: str = "system",
                          commit_type: CommitType = CommitType.FEATURE,
                          changes: List[ChangeRecord] = None) -> DataCommit:
        """創建提交"""
        # 獲取當前分支的HEAD
        current_branch_info = self.branches.get(self.current_branch)
        parent_commits = [current_branch_info.head_commit] if current_branch_info and current_branch_info.head_commit else []
        
        # 創建提交對象
        commit = DataCommit(
            parent_commits=parent_commits,
            branch_name=self.current_branch,
            commit_type=commit_type,
            message=message,
            author=author,
            changes={},
            affected_tables={change.table_name for change in changes or []}
        )
        
        # 記錄提交
        await self.history.record_commit(commit, changes or [])
        
        # 更新分支HEAD
        if current_branch_info:
            current_branch_info.head_commit = commit.commit_id
            await self._save_branch(current_branch_info)
        
        return commit
    
    async def create_branch(self, branch_name: str, base_commit: str = None,
                          description: str = "") -> DataBranch:
        """創建分支"""
        if branch_name in self.branches:
            raise ValueError(f"Branch '{branch_name}' already exists")
        
        # 確定基礎提交
        if not base_commit:
            current_branch_info = self.branches.get(self.current_branch)
            base_commit = current_branch_info.head_commit if current_branch_info else ""
        
        # 創建分支
        branch = DataBranch(
            branch_name=branch_name,
            head_commit=base_commit,
            base_commit=base_commit,
            description=description
        )
        
        self.branches[branch_name] = branch
        await self._save_branch(branch)
        
        return branch
    
    async def checkout_branch(self, branch_name: str):
        """切換分支"""
        if branch_name not in self.branches:
            raise ValueError(f"Branch '{branch_name}' does not exist")
        
        self.current_branch = branch_name
        logging.info(f"Switched to branch '{branch_name}'")
    
    async def merge_branch(self, source_branch: str,
                         strategy: MergeStrategy = MergeStrategy.AUTO) -> Dict[str, Any]:
        """合併分支"""
        if source_branch not in self.branches:
            raise ValueError(f"Source branch '{source_branch}' does not exist")
        
        return await self.merge_engine.merge_branches(
            source_branch, self.current_branch, strategy
        )
    
    async def get_branch_list(self) -> List[DataBranch]:
        """獲取分支列表"""
        return list(self.branches.values())
    
    async def get_commit_log(self, branch_name: str = None,
                           limit: int = 50) -> List[DataCommit]:
        """獲取提交日誌"""
        branch = branch_name or self.current_branch
        return await self.history.get_commit_history(branch, limit)
    
    async def get_commit_diff(self, commit_id1: str, commit_id2: str) -> Dict[str, Any]:
        """獲取提交差異"""
        changes1 = await self.history.get_changes_for_commit(commit_id1)
        changes2 = await self.history.get_changes_for_commit(commit_id2)
        
        return {
            'commit1_changes': len(changes1),
            'commit2_changes': len(changes2),
            'affected_tables': list(set(
                [c.table_name for c in changes1] + 
                [c.table_name for c in changes2]
            )),
            'changes1': changes1,
            'changes2': changes2
        }
    
    async def rollback_to_commit(self, commit_id: str) -> DataCommit:
        """回滾到指定提交"""
        # 創建回滾提交
        rollback_commit = DataCommit(
            parent_commits=[self.branches[self.current_branch].head_commit],
            branch_name=self.current_branch,
            commit_type=CommitType.ROLLBACK,
            message=f"Rollback to commit {commit_id[:8]}",
            author="system"
        )
        
        # 這裡需要實現實際的數據回滾邏輯
        # 簡化實現，實際需要根據提交歷史恢復數據狀態
        
        await self.history.record_commit(rollback_commit, [])
        
        # 更新分支HEAD
        self.branches[self.current_branch].head_commit = rollback_commit.commit_id
        await self._save_branch(self.branches[self.current_branch])
        
        return rollback_commit
    
    async def _save_branch(self, branch: DataBranch):
        """保存分支信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO version_branches
                (branch_name, head_commit, base_commit, created_at, created_by,
                 description, is_active, merge_target, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                branch.branch_name,
                branch.head_commit,
                branch.base_commit,
                branch.created_at,
                branch.created_by,
                branch.description,
                branch.is_active,
                branch.merge_target,
                json.dumps(branch.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"Failed to save branch: {e}")
    
    async def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        commits = await self.history.get_commit_history(limit=1000)
        
        return {
            'current_branch': self.current_branch,
            'total_branches': len(self.branches),
            'total_commits': len(commits),
            'branches': [
                {
                    'name': branch.branch_name,
                    'head_commit': branch.head_commit[:8] if branch.head_commit else None,
                    'is_active': branch.is_active,
                    'created_at': branch.created_at
                }
                for branch in self.branches.values()
            ],
            'recent_commits': [
                {
                    'commit_id': commit.short_id,
                    'message': commit.message,
                    'author': commit.author,
                    'branch': commit.branch_name,
                    'type': commit.commit_type.value,
                    'timestamp': commit.timestamp
                }
                for commit in commits[:10]
            ]
        }

# 工廠函數
def create_version_control(db_path: str) -> DataVersionControl:
    """創建版本控制系統"""
    return DataVersionControl(db_path)

def create_change_record(table_name: str, operation: str,
                        old_data: Dict[str, Any] = None,
                        new_data: Dict[str, Any] = None,
                        **kwargs) -> ChangeRecord:
    """創建變更記錄"""
    return ChangeRecord(
        table_name=table_name,
        operation=operation,
        old_data=old_data,
        new_data=new_data,
        **kwargs
    )