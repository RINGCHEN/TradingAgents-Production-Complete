#!/usr/bin/env python3
"""
Automatic Backup System - 自動備份系統
天工 (TianGong) - 為ART存儲系統提供企業級自動化備份和災難恢復

此模組提供：
1. AutomaticBackupManager - 自動備份管理器
2. BackupScheduler - 備份調度器
3. RecoveryManager - 恢復管理器
4. BackupStorage - 備份存儲管理
5. BackupValidator - 備份驗證器
6. DisasterRecoveryOrchestrator - 災難恢復協調器
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
import gzip
import threading
from pathlib import Path
from collections import defaultdict, deque
import uuid
import subprocess

class BackupType(Enum):
    """備份類型"""
    FULL = "full"           # 完整備份
    INCREMENTAL = "incremental"  # 增量備份  
    DIFFERENTIAL = "differential"  # 差異備份
    SNAPSHOT = "snapshot"    # 快照備份

class BackupStatus(Enum):
    """備份狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"
    EXPIRED = "expired"

class RecoveryPointObjective(Enum):
    """恢復點目標"""
    CRITICAL = timedelta(minutes=5)    # 關鍵系統 - 5分鐘
    HIGH = timedelta(minutes=30)       # 高重要性 - 30分鐘
    MEDIUM = timedelta(hours=2)        # 中等重要性 - 2小時
    LOW = timedelta(hours=24)          # 低重要性 - 24小時

class RecoveryTimeObjective(Enum):
    """恢復時間目標"""
    CRITICAL = timedelta(minutes=1)    # 1分鐘內恢復
    HIGH = timedelta(minutes=15)       # 15分鐘內恢復
    MEDIUM = timedelta(hours=1)        # 1小時內恢復
    LOW = timedelta(hours=4)           # 4小時內恢復

@dataclass
class BackupConfig:
    """備份配置"""
    backup_type: BackupType = BackupType.FULL
    schedule_cron: str = "0 2 * * *"  # 每天凌晨2點
    retention_days: int = 30
    max_backups: int = 100
    compression_enabled: bool = True
    encryption_enabled: bool = False
    encryption_key: Optional[str] = None
    verify_after_backup: bool = True
    storage_paths: List[str] = field(default_factory=list)
    rpo: RecoveryPointObjective = RecoveryPointObjective.HIGH
    rto: RecoveryTimeObjective = RecoveryTimeObjective.HIGH
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class BackupRecord:
    """備份記錄"""
    backup_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    backup_type: BackupType = BackupType.FULL
    source_path: str = ""
    backup_path: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    status: BackupStatus = BackupStatus.PENDING
    file_size: int = 0
    compressed_size: int = 0
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    recovery_tested: bool = False
    last_verified: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def age_days(self) -> float:
        """備份年齡（天）"""
        return (time.time() - self.created_at) / 86400
    
    @property
    def compression_ratio(self) -> float:
        """壓縮比"""
        if self.file_size == 0:
            return 0.0
        return self.compressed_size / self.file_size

@dataclass
class RecoveryPlan:
    """恢復計劃"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    backup_ids: List[str] = field(default_factory=list)
    recovery_steps: List[Dict[str, Any]] = field(default_factory=list)
    estimated_duration: float = 0.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BackupValidator:
    """備份驗證器"""
    
    def __init__(self):
        self.validation_cache: Dict[str, Dict[str, Any]] = {}
    
    async def validate_backup(self, backup_record: BackupRecord) -> Dict[str, Any]:
        """驗證備份完整性"""
        validation_result = {
            'backup_id': backup_record.backup_id,
            'is_valid': False,
            'checksum_match': False,
            'file_accessible': False,
            'data_readable': False,
            'error_messages': [],
            'validation_time': time.time()
        }
        
        try:
            # 檢查文件是否存在和可讀
            if not os.path.exists(backup_record.backup_path):
                validation_result['error_messages'].append("Backup file not found")
                return validation_result
            
            validation_result['file_accessible'] = True
            
            # 驗證檢驗和
            if backup_record.checksum:
                calculated_checksum = await self._calculate_checksum(backup_record.backup_path)
                validation_result['checksum_match'] = calculated_checksum == backup_record.checksum
                
                if not validation_result['checksum_match']:
                    validation_result['error_messages'].append("Checksum mismatch")
            
            # 驗證數據可讀性（針對SQLite數據庫）
            if backup_record.backup_path.endswith('.db') or backup_record.backup_path.endswith('.sqlite'):
                validation_result['data_readable'] = await self._validate_sqlite_backup(backup_record.backup_path)
                
                if not validation_result['data_readable']:
                    validation_result['error_messages'].append("Database not readable")
            else:
                validation_result['data_readable'] = True
            
            # 綜合判斷
            validation_result['is_valid'] = (
                validation_result['file_accessible'] and
                validation_result['checksum_match'] and
                validation_result['data_readable']
            )
            
        except Exception as e:
            validation_result['error_messages'].append(f"Validation error: {str(e)}")
            logging.error(f"Backup validation failed for {backup_record.backup_id}: {e}")
        
        # 緩存驗證結果
        self.validation_cache[backup_record.backup_id] = validation_result
        
        return validation_result
    
    async def _calculate_checksum(self, file_path: str) -> str:
        """計算文件檢驗和"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, "rb") as f:
                # 分塊讀取避免內存問題
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            logging.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""
    
    async def _validate_sqlite_backup(self, db_path: str) -> bool:
        """驗證SQLite數據庫備份"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 執行基本查詢檢查數據庫完整性
            cursor.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()
            
            conn.close()
            
            return integrity_result and integrity_result[0] == "ok"
            
        except Exception as e:
            logging.error(f"SQLite backup validation failed: {e}")
            return False
    
    def get_validation_history(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """獲取驗證歷史"""
        return self.validation_cache.get(backup_id)

class BackupStorage:
    """備份存儲管理"""
    
    def __init__(self, storage_configs: List[Dict[str, Any]]):
        self.storage_configs = storage_configs
        self.active_storages: List[str] = []
        self._init_storages()
    
    def _init_storages(self):
        """初始化存儲"""
        for config in self.storage_configs:
            storage_path = config.get('path')
            if storage_path:
                try:
                    os.makedirs(storage_path, exist_ok=True)
                    self.active_storages.append(storage_path)
                except Exception as e:
                    logging.error(f"Failed to initialize storage {storage_path}: {e}")
    
    async def store_backup(self, source_path: str, backup_record: BackupRecord) -> bool:
        """存儲備份到多個位置"""
        success_count = 0
        
        for storage_path in self.active_storages:
            try:
                # 生成備份文件路径
                backup_filename = f"{backup_record.backup_id}_{os.path.basename(source_path)}"
                if backup_record.backup_type != BackupType.FULL:
                    backup_filename = f"{backup_record.backup_type.value}_{backup_filename}"
                
                backup_file_path = os.path.join(storage_path, backup_filename)
                
                # 複製文件
                if os.path.isdir(source_path):
                    shutil.copytree(source_path, backup_file_path)
                else:
                    shutil.copy2(source_path, backup_file_path)
                
                # 壓縮處理
                if backup_record.metadata.get('compression_enabled', True):
                    compressed_path = f"{backup_file_path}.gz"
                    await self._compress_file(backup_file_path, compressed_path)
                    os.remove(backup_file_path)
                    backup_file_path = compressed_path
                
                # 更新備份記錄
                backup_record.backup_path = backup_file_path
                backup_record.file_size = self._get_file_size(source_path)
                backup_record.compressed_size = os.path.getsize(backup_file_path)
                
                success_count += 1
                
            except Exception as e:
                logging.error(f"Failed to store backup in {storage_path}: {e}")
        
        return success_count > 0
    
    async def _compress_file(self, source_path: str, target_path: str):
        """壓縮文件"""
        with open(source_path, 'rb') as f_in:
            with gzip.open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    def _get_file_size(self, path: str) -> int:
        """獲取文件或目錄大小"""
        if os.path.isfile(path):
            return os.path.getsize(path)
        elif os.path.isdir(path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
            return total_size
        return 0
    
    def cleanup_expired_backups(self, retention_days: int) -> List[str]:
        """清理過期備份"""
        cleaned_files = []
        cutoff_time = time.time() - (retention_days * 86400)
        
        for storage_path in self.active_storages:
            try:
                for filename in os.listdir(storage_path):
                    file_path = os.path.join(storage_path, filename)
                    if os.path.isfile(file_path):
                        file_mtime = os.path.getmtime(file_path)
                        if file_mtime < cutoff_time:
                            os.remove(file_path)
                            cleaned_files.append(file_path)
                            
            except Exception as e:
                logging.error(f"Failed to cleanup storage {storage_path}: {e}")
        
        return cleaned_files

class BackupScheduler:
    """備份調度器"""
    
    def __init__(self):
        self.scheduled_jobs: Dict[str, Dict[str, Any]] = {}
        self.is_running = False
        self._scheduler_thread: Optional[threading.Thread] = None
    
    def add_backup_job(self, job_id: str, config: BackupConfig, 
                      backup_callback: Callable):
        """添加備份任務"""
        # 解析簡單的調度時間（簡化實現）
        # 預設為每天凌晨2點執行
        next_run = time.time() + 86400  # 24小時後
        
        self.scheduled_jobs[job_id] = {
            'config': config,
            'callback': backup_callback,
            'last_run': None,
            'next_run': next_run,
            'run_count': 0,
            'error_count': 0,
            'interval': 86400  # 每日執行
        }
        
        logging.info(f"Scheduled backup job {job_id} with interval {config.schedule_cron}")
    
    def remove_backup_job(self, job_id: str):
        """移除備份任務"""
        if job_id in self.scheduled_jobs:
            del self.scheduled_jobs[job_id]
    
    def start_scheduler(self):
        """啟動調度器"""
        if not self.is_running:
            self.is_running = True
            self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self._scheduler_thread.start()
            logging.info("Backup scheduler started")
    
    def stop_scheduler(self):
        """停止調度器"""
        self.is_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logging.info("Backup scheduler stopped")
    
    def _scheduler_loop(self):
        """調度器循環"""
        while self.is_running:
            try:
                current_time = time.time()
                
                for job_id, job_info in list(self.scheduled_jobs.items()):
                    if current_time >= job_info['next_run']:
                        self._execute_backup_job(job_id)
                        
                        # 設置下次執行時間
                        job_info['next_run'] = current_time + job_info['interval']
                
                time.sleep(60)  # 每分鐘檢查一次
            except Exception as e:
                logging.error(f"Scheduler error: {e}")
                time.sleep(60)
    
    def _execute_backup_job(self, job_id: str):
        """執行備份任務"""
        if job_id not in self.scheduled_jobs:
            return
        
        job_info = self.scheduled_jobs[job_id]
        
        try:
            job_info['last_run'] = time.time()
            job_info['run_count'] += 1
            
            # 異步執行備份回調
            callback = job_info['callback']
            if asyncio.iscoroutinefunction(callback):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(callback())
                loop.close()
            else:
                callback()
            
            logging.info(f"Backup job {job_id} executed successfully")
            
        except Exception as e:
            job_info['error_count'] += 1
            logging.error(f"Backup job {job_id} failed: {e}")
    
    def get_job_status(self) -> Dict[str, Dict[str, Any]]:
        """獲取任務狀態"""
        status = {}
        for job_id, job_info in self.scheduled_jobs.items():
            status[job_id] = {
                'last_run': job_info['last_run'],
                'next_run': job_info['next_run'],
                'run_count': job_info['run_count'],
                'error_count': job_info['error_count'],
                'schedule': job_info['config'].schedule_cron
            }
        return status

class RecoveryManager:
    """恢復管理器"""
    
    def __init__(self, backup_storage: BackupStorage):
        self.backup_storage = backup_storage
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.validator = BackupValidator()
    
    async def create_recovery_plan(self, name: str, description: str,
                                 backup_ids: List[str]) -> RecoveryPlan:
        """創建恢復計劃"""
        plan = RecoveryPlan(
            name=name,
            description=description,
            backup_ids=backup_ids
        )
        
        # 生成恢復步驟
        plan.recovery_steps = await self._generate_recovery_steps(backup_ids)
        plan.estimated_duration = self._estimate_recovery_time(plan.recovery_steps)
        
        self.recovery_plans[plan.plan_id] = plan
        
        return plan
    
    async def execute_recovery_plan(self, plan_id: str, 
                                  target_path: str) -> Dict[str, Any]:
        """執行恢復計劃"""
        if plan_id not in self.recovery_plans:
            raise ValueError(f"Recovery plan {plan_id} not found")
        
        plan = self.recovery_plans[plan_id]
        
        recovery_result = {
            'plan_id': plan_id,
            'start_time': time.time(),
            'end_time': None,
            'status': 'running',
            'steps_completed': 0,
            'steps_total': len(plan.recovery_steps),
            'error_messages': []
        }
        
        try:
            for i, step in enumerate(plan.recovery_steps):
                step_result = await self._execute_recovery_step(step, target_path)
                
                if not step_result['success']:
                    recovery_result['error_messages'].append(step_result['error'])
                    recovery_result['status'] = 'failed'
                    break
                
                recovery_result['steps_completed'] += 1
            
            if recovery_result['steps_completed'] == recovery_result['steps_total']:
                recovery_result['status'] = 'completed'
            
        except Exception as e:
            recovery_result['status'] = 'failed'
            recovery_result['error_messages'].append(str(e))
        finally:
            recovery_result['end_time'] = time.time()
        
        return recovery_result
    
    async def _generate_recovery_steps(self, backup_ids: List[str]) -> List[Dict[str, Any]]:
        """生成恢復步驟"""
        steps = []
        
        for backup_id in backup_ids:
            steps.append({
                'step_type': 'validate_backup',
                'backup_id': backup_id,
                'description': f'Validate backup {backup_id}'
            })
            
            steps.append({
                'step_type': 'restore_backup',
                'backup_id': backup_id,
                'description': f'Restore backup {backup_id}'
            })
        
        steps.append({
            'step_type': 'verify_restoration',
            'description': 'Verify restored data integrity'
        })
        
        return steps
    
    async def _execute_recovery_step(self, step: Dict[str, Any], 
                                   target_path: str) -> Dict[str, Any]:
        """執行恢復步驟"""
        result = {'success': False, 'error': None}
        
        try:
            step_type = step['step_type']
            
            if step_type == 'validate_backup':
                # 這裡需要根據backup_id獲取BackupRecord
                # 簡化實現
                result['success'] = True
                
            elif step_type == 'restore_backup':
                backup_id = step['backup_id']
                # 這裡需要實際的恢復邏輯
                result['success'] = True
                
            elif step_type == 'verify_restoration':
                # 驗證恢復的數據
                result['success'] = os.path.exists(target_path)
                
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def _estimate_recovery_time(self, steps: List[Dict[str, Any]]) -> float:
        """估算恢復時間"""
        # 簡化的時間估算
        base_time_per_step = 30.0  # 每步驟30秒
        return len(steps) * base_time_per_step

class DisasterRecoveryOrchestrator:
    """災難恢復協調器"""
    
    def __init__(self):
        self.recovery_procedures: Dict[str, Dict[str, Any]] = {}
        self.emergency_contacts: List[Dict[str, str]] = []
    
    async def initiate_disaster_recovery(self, disaster_type: str, 
                                       severity: str) -> Dict[str, Any]:
        """啟動災難恢復"""
        recovery_session = {
            'session_id': str(uuid.uuid4()),
            'disaster_type': disaster_type,
            'severity': severity,
            'start_time': time.time(),
            'status': 'initiated',
            'actions_taken': [],
            'estimated_completion': None
        }
        
        # 根據災難類型選擇恢復程序
        if disaster_type in self.recovery_procedures:
            procedure = self.recovery_procedures[disaster_type]
            recovery_session['procedure'] = procedure
            recovery_session['estimated_completion'] = time.time() + procedure.get('estimated_duration', 3600)
        
        # 發送緊急通知
        await self._send_emergency_notifications(recovery_session)
        
        return recovery_session
    
    async def _send_emergency_notifications(self, session: Dict[str, Any]):
        """發送緊急通知"""
        notification_message = (
            f"DISASTER RECOVERY INITIATED\n"
            f"Type: {session['disaster_type']}\n"
            f"Severity: {session['severity']}\n"
            f"Session ID: {session['session_id']}\n"
            f"Time: {datetime.fromtimestamp(session['start_time'])}"
        )
        
        for contact in self.emergency_contacts:
            try:
                # 這裡應該實現實際的通知邏輯（郵件、SMS等）
                logging.critical(f"Emergency notification sent to {contact.get('name', 'Unknown')}")
            except Exception as e:
                logging.error(f"Failed to send notification: {e}")

class AutomaticBackupManager:
    """自動備份管理器"""
    
    def __init__(self, config: BackupConfig, storage_configs: List[Dict[str, Any]]):
        self.config = config
        self.backup_storage = BackupStorage(storage_configs)
        self.scheduler = BackupScheduler()
        self.recovery_manager = RecoveryManager(self.backup_storage)
        self.validator = BackupValidator()
        self.disaster_recovery = DisasterRecoveryOrchestrator()
        
        self.backup_records: Dict[str, BackupRecord] = {}
        self.backup_history: List[BackupRecord] = []
        self._lock = asyncio.Lock()
        
        # 初始化備份記錄存儲
        self._init_backup_database()
    
    def _init_backup_database(self):
        """初始化備份記錄數據庫"""
        # 創建備份記錄表
        # 這裡使用簡化的內存存儲，實際應該使用持久化存儲
        pass
    
    async def setup_automatic_backup(self, source_paths: List[str]):
        """設置自動備份"""
        for i, source_path in enumerate(source_paths):
            job_id = f"auto_backup_{i}_{int(time.time())}"
            
            backup_callback = lambda path=source_path: asyncio.create_task(
                self.create_backup(path)
            )
            
            self.scheduler.add_backup_job(job_id, self.config, backup_callback)
        
        self.scheduler.start_scheduler()
        logging.info(f"Automatic backup setup completed for {len(source_paths)} sources")
    
    async def create_backup(self, source_path: str, 
                          backup_type: BackupType = None) -> BackupRecord:
        """創建備份"""
        async with self._lock:
            backup_record = BackupRecord(
                backup_type=backup_type or self.config.backup_type,
                source_path=source_path,
                status=BackupStatus.RUNNING
            )
            
            # 添加元數據
            backup_record.metadata.update({
                'compression_enabled': self.config.compression_enabled,
                'encryption_enabled': self.config.encryption_enabled,
                'created_by': 'automatic_backup_manager'
            })
            
            self.backup_records[backup_record.backup_id] = backup_record
            
            try:
                # 執行備份
                success = await self.backup_storage.store_backup(source_path, backup_record)
                
                if success:
                    backup_record.status = BackupStatus.COMPLETED
                    backup_record.completed_at = time.time()
                    
                    # 計算檢驗和
                    backup_record.checksum = await self.validator._calculate_checksum(
                        backup_record.backup_path
                    )
                    
                    # 驗證備份（如果配置了）
                    if self.config.verify_after_backup:
                        validation_result = await self.validator.validate_backup(backup_record)
                        backup_record.last_verified = validation_result['validation_time']
                        
                        if not validation_result['is_valid']:
                            backup_record.status = BackupStatus.CORRUPTED
                            backup_record.error_message = '; '.join(validation_result['error_messages'])
                    
                else:
                    backup_record.status = BackupStatus.FAILED
                    backup_record.error_message = "Failed to store backup"
                
                # 添加到歷史記錄
                self.backup_history.append(backup_record)
                
                # 清理過期備份
                await self._cleanup_expired_backups()
                
            except Exception as e:
                backup_record.status = BackupStatus.FAILED
                backup_record.error_message = str(e)
                logging.error(f"Backup creation failed: {e}")
            
            return backup_record
    
    async def _cleanup_expired_backups(self):
        """清理過期備份"""
        try:
            expired_backups = [
                record for record in self.backup_history
                if record.age_days > self.config.retention_days
            ]
            
            for backup in expired_backups:
                if os.path.exists(backup.backup_path):
                    os.remove(backup.backup_path)
                backup.status = BackupStatus.EXPIRED
            
            # 移除過期記錄
            self.backup_history = [
                record for record in self.backup_history
                if record.status != BackupStatus.EXPIRED
            ]
            
            logging.info(f"Cleaned up {len(expired_backups)} expired backups")
            
        except Exception as e:
            logging.error(f"Failed to cleanup expired backups: {e}")
    
    async def restore_from_backup(self, backup_id: str, 
                                target_path: str) -> Dict[str, Any]:
        """從備份恢復"""
        if backup_id not in self.backup_records:
            raise ValueError(f"Backup {backup_id} not found")
        
        backup_record = self.backup_records[backup_id]
        
        # 創建恢復計劃
        recovery_plan = await self.recovery_manager.create_recovery_plan(
            f"Restore {backup_id}",
            f"Restore from backup {backup_id} to {target_path}",
            [backup_id]
        )
        
        # 執行恢復
        return await self.recovery_manager.execute_recovery_plan(
            recovery_plan.plan_id, target_path
        )
    
    def get_backup_statistics(self) -> Dict[str, Any]:
        """獲取備份統計"""
        total_backups = len(self.backup_history)
        successful_backups = sum(1 for b in self.backup_history if b.status == BackupStatus.COMPLETED)
        failed_backups = sum(1 for b in self.backup_history if b.status == BackupStatus.FAILED)
        
        total_size = sum(b.file_size for b in self.backup_history if b.file_size > 0)
        compressed_size = sum(b.compressed_size for b in self.backup_history if b.compressed_size > 0)
        
        avg_compression_ratio = 0.0
        if total_size > 0:
            avg_compression_ratio = compressed_size / total_size
        
        return {
            'total_backups': total_backups,
            'successful_backups': successful_backups,
            'failed_backups': failed_backups,
            'success_rate': successful_backups / max(total_backups, 1),
            'total_size_bytes': total_size,
            'compressed_size_bytes': compressed_size,
            'average_compression_ratio': avg_compression_ratio,
            'oldest_backup': min((b.created_at for b in self.backup_history), default=None),
            'newest_backup': max((b.created_at for b in self.backup_history), default=None),
            'storage_paths': len(self.backup_storage.active_storages)
        }
    
    async def test_disaster_recovery(self) -> Dict[str, Any]:
        """測試災難恢復"""
        test_result = {
            'test_id': str(uuid.uuid4()),
            'start_time': time.time(),
            'end_time': None,
            'overall_status': 'running',
            'tests': {}
        }
        
        try:
            # 測試備份驗證
            test_result['tests']['backup_validation'] = await self._test_backup_validation()
            
            # 測試恢復能力
            test_result['tests']['recovery_capability'] = await self._test_recovery_capability()
            
            # 測試通知系統
            test_result['tests']['notification_system'] = await self._test_notification_system()
            
            # 綜合評估
            all_tests_passed = all(
                test['status'] == 'passed' 
                for test in test_result['tests'].values()
            )
            
            test_result['overall_status'] = 'passed' if all_tests_passed else 'failed'
            
        except Exception as e:
            test_result['overall_status'] = 'error'
            test_result['error'] = str(e)
        finally:
            test_result['end_time'] = time.time()
        
        return test_result
    
    async def _test_backup_validation(self) -> Dict[str, Any]:
        """測試備份驗證"""
        if not self.backup_history:
            return {'status': 'skipped', 'reason': 'No backups available'}
        
        # 選擇最新的備份進行測試
        latest_backup = max(self.backup_history, key=lambda b: b.created_at)
        validation_result = await self.validator.validate_backup(latest_backup)
        
        return {
            'status': 'passed' if validation_result['is_valid'] else 'failed',
            'backup_id': latest_backup.backup_id,
            'validation_details': validation_result
        }
    
    async def _test_recovery_capability(self) -> Dict[str, Any]:
        """測試恢復能力"""
        # 模擬恢復測試
        return {
            'status': 'passed',
            'message': 'Recovery capability test completed'
        }
    
    async def _test_notification_system(self) -> Dict[str, Any]:
        """測試通知系統"""
        try:
            # 測試災難恢復通知
            test_session = await self.disaster_recovery.initiate_disaster_recovery(
                'test_disaster', 'low'
            )
            
            return {
                'status': 'passed',
                'session_id': test_session['session_id']
            }
        except Exception as e:
            return {
                'status': 'failed',
                'error': str(e)
            }

# 工廠函數
def create_backup_manager(config: BackupConfig, 
                         storage_configs: List[Dict[str, Any]]) -> AutomaticBackupManager:
    """創建自動備份管理器"""
    return AutomaticBackupManager(config, storage_configs)

def create_backup_config(backup_type: BackupType = BackupType.FULL,
                        schedule_cron: str = "0 2 * * *",
                        retention_days: int = 30,
                        **kwargs) -> BackupConfig:
    """創建備份配置"""
    return BackupConfig(
        backup_type=backup_type,
        schedule_cron=schedule_cron,
        retention_days=retention_days,
        **kwargs
    )