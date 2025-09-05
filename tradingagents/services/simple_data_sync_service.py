"""
簡化的數據同步服務 - 用於任務5基礎功能實現
"""

import asyncio
import json
import logging
import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class SyncStatus(Enum):
    """同步狀態枚舉"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


class SyncType(Enum):
    """同步類型枚舉"""
    USER_DATA = "user_data"
    TEST_RESULT = "test_result"
    CONVERSION_DATA = "conversion_data"
    BEHAVIOR_DATA = "behavior_data"


@dataclass
class SyncConfig:
    """同步配置"""
    main_system_api_url: str = "mock://localhost:8001"
    sync_batch_size: int = 100
    retry_attempts: int = 3
    sync_interval: int = 300  # 5分鐘
    timeout: int = 30
    api_key: Optional[str] = None
    enable_real_time_sync: bool = True
    enable_batch_sync: bool = True


@dataclass
class SyncRecord:
    """同步記錄"""
    id: Optional[str] = None
    sync_type: SyncType = SyncType.USER_DATA
    source_id: str = ""
    target_id: Optional[str] = None
    status: SyncStatus = SyncStatus.PENDING
    data: Dict[str, Any] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None


class SimpleDataSyncService:
    """簡化的數據同步服務"""
    
    def __init__(self, config: Optional[SyncConfig] = None, db_path: Optional[str] = None):
        self.config = config or SyncConfig()
        self.logger = logging.getLogger(__name__)
        
        # 設置數據庫路徑
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                "tradingagents.db"
            )
        
        self.logger.info(f"Simple data sync service initialized with DB: {self.db_path}")
    
    def get_connection(self):
        """獲取數據庫連接"""
        return sqlite3.connect(self.db_path)
    
    async def sync_user_data(self, user_id: str, force: bool = False) -> bool:
        """
        同步用戶數據到主系統
        
        Args:
            user_id: 用戶ID
            force: 是否強制同步
            
        Returns:
            bool: 同步是否成功
        """
        try:
            # 檢查是否需要同步
            if not force and await self._is_recently_synced(user_id, SyncType.USER_DATA):
                self.logger.info(f"User {user_id} recently synced, skipping")
                return True
            
            # 獲取用戶數據
            user_data = await self._get_user_data(user_id)
            if not user_data:
                self.logger.warning(f"No user data found for {user_id}")
                return False
            
            # 創建同步記錄
            sync_record = SyncRecord(
                sync_type=SyncType.USER_DATA,
                source_id=user_id,
                data=user_data,
                status=SyncStatus.PENDING
            )
            
            # 執行同步
            success = await self._execute_sync(sync_record)
            
            # 記錄同步結果
            await self._save_sync_record(sync_record)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error syncing user data for {user_id}: {str(e)}")
            return False
    
    async def sync_test_result(self, result_id: str, force: bool = False) -> bool:
        """
        同步測試結果到主系統
        
        Args:
            result_id: 測試結果ID
            force: 是否強制同步
            
        Returns:
            bool: 同步是否成功
        """
        try:
            # 檢查是否需要同步
            if not force and await self._is_recently_synced(result_id, SyncType.TEST_RESULT):
                self.logger.info(f"Test result {result_id} recently synced, skipping")
                return True
            
            # 獲取測試結果數據
            test_data = await self._get_test_result_data(result_id)
            if not test_data:
                self.logger.warning(f"No test result data found for {result_id}")
                return False
            
            # 創建同步記錄
            sync_record = SyncRecord(
                sync_type=SyncType.TEST_RESULT,
                source_id=result_id,
                data=test_data,
                status=SyncStatus.PENDING
            )
            
            # 執行同步
            success = await self._execute_sync(sync_record)
            
            # 記錄同步結果
            await self._save_sync_record(sync_record)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error syncing test result for {result_id}: {str(e)}")
            return False
    
    async def sync_conversion_data(self, session_id: str, force: bool = False) -> bool:
        """
        同步轉換數據到主系統
        
        Args:
            session_id: 會話ID
            force: 是否強制同步
            
        Returns:
            bool: 同步是否成功
        """
        try:
            # 檢查是否需要同步
            if not force and await self._is_recently_synced(session_id, SyncType.CONVERSION_DATA):
                self.logger.info(f"Conversion data {session_id} recently synced, skipping")
                return True
            
            # 獲取轉換數據
            conversion_data = await self._get_conversion_data(session_id)
            if not conversion_data:
                self.logger.warning(f"No conversion data found for {session_id}")
                return False
            
            # 創建同步記錄
            sync_record = SyncRecord(
                sync_type=SyncType.CONVERSION_DATA,
                source_id=session_id,
                data=conversion_data,
                status=SyncStatus.PENDING
            )
            
            # 執行同步
            success = await self._execute_sync(sync_record)
            
            # 記錄同步結果
            await self._save_sync_record(sync_record)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error syncing conversion data for {session_id}: {str(e)}")
            return False
    
    async def batch_sync(self, sync_type: Optional[SyncType] = None, limit: int = 100) -> Dict[str, int]:
        """
        批量同步待同步的數據
        
        Args:
            sync_type: 同步類型，None表示所有類型
            limit: 批量限制
            
        Returns:
            Dict[str, int]: 同步統計結果
        """
        stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0
        }
        
        try:
            # 獲取待同步記錄
            pending_records = await self._get_pending_sync_records(sync_type, limit)
            stats["total"] = len(pending_records)
            
            # 批量處理
            for record in pending_records:
                try:
                    success = await self._execute_sync(record)
                    if success:
                        stats["success"] += 1
                    else:
                        stats["failed"] += 1
                    
                    await self._save_sync_record(record)
                    
                except Exception as e:
                    self.logger.error(f"Error processing sync record {record.id}: {str(e)}")
                    record.status = SyncStatus.FAILED
                    record.error_message = str(e)
                    stats["failed"] += 1
                    await self._save_sync_record(record)
            
            self.logger.info(f"Batch sync completed: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error in batch sync: {str(e)}")
            return stats
    
    async def validate_sync_data(self, data: Dict[str, Any], sync_type: SyncType) -> Tuple[bool, List[str]]:
        """
        驗證同步數據的完整性和格式
        
        Args:
            data: 要驗證的數據
            sync_type: 同步類型
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 錯誤列表)
        """
        errors = []
        
        try:
            if sync_type == SyncType.USER_DATA:
                errors.extend(self._validate_user_data(data))
            elif sync_type == SyncType.TEST_RESULT:
                errors.extend(self._validate_test_result_data(data))
            elif sync_type == SyncType.CONVERSION_DATA:
                errors.extend(self._validate_conversion_data(data))
            elif sync_type == SyncType.BEHAVIOR_DATA:
                errors.extend(self._validate_behavior_data(data))
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    async def get_sync_status(self, source_id: str, sync_type: SyncType) -> Optional[SyncRecord]:
        """
        獲取同步狀態
        
        Args:
            source_id: 源ID
            sync_type: 同步類型
            
        Returns:
            Optional[SyncRecord]: 同步記錄
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM sync_records 
                    WHERE source_id = ? AND sync_type = ?
                    ORDER BY created_at DESC LIMIT 1
                """, (source_id, sync_type.value))
                
                row = cursor.fetchone()
                if row:
                    return SyncRecord(
                        id=row[0],
                        sync_type=SyncType(row[1]),
                        source_id=row[2],
                        target_id=row[3],
                        status=SyncStatus(row[4]),
                        data=json.loads(row[5]) if row[5] else None,
                        error_message=row[6],
                        retry_count=row[7],
                        created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                        updated_at=datetime.fromisoformat(row[9]) if row[9] else None,
                        synced_at=datetime.fromisoformat(row[10]) if row[10] else None
                    )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting sync status: {str(e)}")
            return None
    
    # 私有方法
    
    async def _execute_sync(self, record: SyncRecord) -> bool:
        """執行實際的同步操作"""
        try:
            record.status = SyncStatus.IN_PROGRESS
            record.updated_at = datetime.utcnow()
            
            # 驗證數據
            is_valid, errors = await self.validate_sync_data(record.data, record.sync_type)
            if not is_valid:
                record.status = SyncStatus.FAILED
                record.error_message = "; ".join(errors)
                return False
            
            # 根據配置決定是否實際發送到主系統
            if self.config.main_system_api_url.startswith("mock://"):
                # 模擬模式
                success = await self._mock_sync_to_main_system(record)
            else:
                # 實際同步到主系統（暫未實現）
                success = await self._mock_sync_to_main_system(record)
            
            if success:
                record.status = SyncStatus.SUCCESS
                record.synced_at = datetime.utcnow()
            else:
                record.status = SyncStatus.FAILED
                record.retry_count += 1
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error executing sync: {str(e)}")
            record.status = SyncStatus.FAILED
            record.error_message = str(e)
            record.retry_count += 1
            return False
    
    async def _mock_sync_to_main_system(self, record: SyncRecord) -> bool:
        """模擬同步到主系統（用於測試）"""
        # 模擬網絡延遲
        await asyncio.sleep(0.1)
        
        # 模擬成功率（95%）
        import random
        success = random.random() < 0.95
        
        if success:
            # 模擬生成目標ID
            record.target_id = f"main_system_{record.source_id}_{int(datetime.utcnow().timestamp())}"
            self.logger.info(f"Mock sync successful: {record.source_id} -> {record.target_id}")
        else:
            record.error_message = "Mock sync failed (simulated failure)"
            self.logger.warning(f"Mock sync failed: {record.source_id}")
        
        return success
    
    async def _is_recently_synced(self, source_id: str, sync_type: SyncType, hours: int = 1) -> bool:
        """檢查是否最近已同步"""
        try:
            recent_sync = await self.get_sync_status(source_id, sync_type)
            if recent_sync and recent_sync.status == SyncStatus.SUCCESS:
                if recent_sync.synced_at:
                    time_diff = datetime.utcnow() - recent_sync.synced_at
                    return time_diff < timedelta(hours=hours)
            return False
        except Exception:
            return False
    
    async def _get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶數據"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT u.*, p.personality_type, p.risk_tolerance, p.investment_style
                    FROM users u
                    LEFT JOIN personality_test_results p ON u.id = p.user_id
                    WHERE u.id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "email": row[1],
                        "name": row[2],
                        "phone": row[3],
                        "created_at": row[4],
                        "personality_type": row[5] if len(row) > 5 else None,
                        "risk_tolerance": row[6] if len(row) > 6 else None,
                        "investment_style": row[7] if len(row) > 7 else None,
                        "source": "personality_test_website"
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting user data: {str(e)}")
            return None
    
    async def _get_test_result_data(self, result_id: str) -> Optional[Dict[str, Any]]:
        """獲取測試結果數據"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT r.*, u.email as user_email
                    FROM personality_test_results r
                    LEFT JOIN users u ON r.user_id = u.id
                    WHERE r.id = ?
                """, (result_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "user_id": row[1],
                        "personality_type": row[2],
                        "risk_tolerance": row[3],
                        "investment_style": row[4],
                        "scores": json.loads(row[5]) if row[5] else {},
                        "answers": json.loads(row[6]) if row[6] else {},
                        "completed_at": row[7],
                        "user_email": row[8] if len(row) > 8 else None,
                        "source": "personality_test_website"
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting test result data: {str(e)}")
            return None
    
    async def _get_conversion_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取轉換數據"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM conversion_tracking
                    WHERE session_id = ?
                    ORDER BY created_at
                """, (session_id,))
                
                rows = cursor.fetchall()
                if rows:
                    conversion_steps = []
                    for row in rows:
                        conversion_steps.append({
                            "step": row[2],
                            "action": row[3],
                            "data": json.loads(row[4]) if row[4] else {},
                            "timestamp": row[5]
                        })
                    
                    return {
                        "session_id": session_id,
                        "conversion_steps": conversion_steps,
                        "source": "personality_test_website"
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting conversion data: {str(e)}")
            return None
    
    async def _get_pending_sync_records(self, sync_type: Optional[SyncType] = None, limit: int = 100) -> List[SyncRecord]:
        """獲取待同步記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if sync_type:
                    cursor.execute("""
                        SELECT * FROM sync_records
                        WHERE sync_type = ? 
                        AND (status = ? OR (status = ? AND retry_count < ?))
                        ORDER BY created_at LIMIT ?
                    """, (
                        sync_type.value,
                        SyncStatus.PENDING.value,
                        SyncStatus.FAILED.value,
                        self.config.retry_attempts,
                        limit
                    ))
                else:
                    cursor.execute("""
                        SELECT * FROM sync_records
                        WHERE (status = ? OR (status = ? AND retry_count < ?))
                        ORDER BY created_at LIMIT ?
                    """, (
                        SyncStatus.PENDING.value,
                        SyncStatus.FAILED.value,
                        self.config.retry_attempts,
                        limit
                    ))
                
                rows = cursor.fetchall()
                records = []
                
                for row in rows:
                    records.append(SyncRecord(
                        id=row[0],
                        sync_type=SyncType(row[1]),
                        source_id=row[2],
                        target_id=row[3],
                        status=SyncStatus(row[4]),
                        data=json.loads(row[5]) if row[5] else None,
                        error_message=row[6],
                        retry_count=row[7],
                        created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                        updated_at=datetime.fromisoformat(row[9]) if row[9] else None,
                        synced_at=datetime.fromisoformat(row[10]) if row[10] else None
                    ))
                
                return records
                
        except Exception as e:
            self.logger.error(f"Error getting pending sync records: {str(e)}")
            return []
    
    async def _save_sync_record(self, record: SyncRecord) -> bool:
        """保存同步記錄"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if record.id:
                    # 更新現有記錄
                    cursor.execute("""
                        UPDATE sync_records SET
                            status = ?,
                            target_id = ?,
                            error_message = ?,
                            retry_count = ?,
                            updated_at = ?,
                            synced_at = ?
                        WHERE id = ?
                    """, (
                        record.status.value,
                        record.target_id,
                        record.error_message,
                        record.retry_count,
                        record.updated_at.isoformat() if record.updated_at else None,
                        record.synced_at.isoformat() if record.synced_at else None,
                        record.id
                    ))
                else:
                    # 創建新記錄
                    record.id = f"sync_{int(datetime.utcnow().timestamp() * 1000)}"
                    cursor.execute("""
                        INSERT INTO sync_records (
                            id, sync_type, source_id, target_id, status, data,
                            error_message, retry_count, created_at, updated_at, synced_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        record.id,
                        record.sync_type.value,
                        record.source_id,
                        record.target_id,
                        record.status.value,
                        json.dumps(record.data) if record.data else None,
                        record.error_message,
                        record.retry_count,
                        (record.created_at or datetime.utcnow()).isoformat(),
                        (record.updated_at or datetime.utcnow()).isoformat(),
                        record.synced_at.isoformat() if record.synced_at else None
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Error saving sync record: {str(e)}")
            return False
    
    def _validate_user_data(self, data: Dict[str, Any]) -> List[str]:
        """驗證用戶數據"""
        errors = []
        
        required_fields = ["id", "email"]
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        if data.get("email") and "@" not in data["email"]:
            errors.append("Invalid email format")
        
        return errors
    
    def _validate_test_result_data(self, data: Dict[str, Any]) -> List[str]:
        """驗證測試結果數據"""
        errors = []
        
        required_fields = ["id", "user_id", "personality_type"]
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        return errors
    
    def _validate_conversion_data(self, data: Dict[str, Any]) -> List[str]:
        """驗證轉換數據"""
        errors = []
        
        required_fields = ["session_id", "conversion_steps"]
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        if not isinstance(data.get("conversion_steps"), list):
            errors.append("conversion_steps must be a list")
        
        return errors
    
    def _validate_behavior_data(self, data: Dict[str, Any]) -> List[str]:
        """驗證行為數據"""
        errors = []
        
        required_fields = ["user_id", "action", "timestamp"]
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Missing required field: {field}")
        
        return errors


# 全局簡化數據同步服務實例
_simple_data_sync_service = None

def get_simple_data_sync_service(config: Optional[SyncConfig] = None, db_path: Optional[str] = None) -> SimpleDataSyncService:
    """獲取簡化數據同步服務實例"""
    global _simple_data_sync_service
    if _simple_data_sync_service is None:
        _simple_data_sync_service = SimpleDataSyncService(config, db_path)
    return _simple_data_sync_service