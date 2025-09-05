"""
數據同步服務 - 投資人格測試系統與主系統的數據同步
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import aiohttp
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from ..database.database_manager import get_database_manager
except ImportError:
    # 如果無法導入，使用簡化的數據庫連接
    import sqlite3
    import os
    
    def get_database_manager():
        class SimpleDatabaseManager:
            def __init__(self):
                self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "tradingagents.db")
            
            async def get_session(self):
                class SimpleSession:
                    def __init__(self, db_path):
                        self.db_path = db_path
                        self.conn = None
                    
                    async def __aenter__(self):
                        self.conn = sqlite3.connect(self.db_path)
                        return self
                    
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        if self.conn:
                            self.conn.close()
                    
                    async def execute(self, query, params=None):
                        cursor = self.conn.cursor()
                        if params:
                            cursor.execute(query, params)
                        else:
                            cursor.execute(query)
                        return cursor
                    
                    async def commit(self):
                        self.conn.commit()
                
                return SimpleSession(self.db_path)
        
        return SimpleDatabaseManager()
from ..utils.cache_manager import CacheManager


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
    main_system_api_url: str = "https://api.tradingagents.com"
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


class DataSyncService:
    """數據同步服務"""
    
    def __init__(self, config: Optional[SyncConfig] = None):
        self.config = config or SyncConfig()
        self.db_manager = get_database_manager()
        self.cache_manager = CacheManager()
        self.logger = logging.getLogger(__name__)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self._session:
            await self._session.close()
    
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
    
    async def sync_behavior_data(self, user_id: str, start_date: Optional[datetime] = None) -> bool:
        """
        同步用戶行為數據到主系統
        
        Args:
            user_id: 用戶ID
            start_date: 開始日期
            
        Returns:
            bool: 同步是否成功
        """
        try:
            # 獲取行為數據
            behavior_data = await self._get_behavior_data(user_id, start_date)
            if not behavior_data:
                self.logger.info(f"No behavior data found for {user_id}")
                return True
            
            # 批量同步行為數據
            success_count = 0
            total_count = len(behavior_data)
            
            for data in behavior_data:
                sync_record = SyncRecord(
                    sync_type=SyncType.BEHAVIOR_DATA,
                    source_id=f"{user_id}_{data.get('timestamp', '')}",
                    data=data,
                    status=SyncStatus.PENDING
                )
                
                if await self._execute_sync(sync_record):
                    success_count += 1
                
                await self._save_sync_record(sync_record)
            
            self.logger.info(f"Synced {success_count}/{total_count} behavior records for {user_id}")
            return success_count == total_count
            
        except Exception as e:
            self.logger.error(f"Error syncing behavior data for {user_id}: {str(e)}")
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
            async with self.db_manager.get_session() as session:
                query = text("""
                    SELECT * FROM sync_records 
                    WHERE source_id = :source_id AND sync_type = :sync_type
                    ORDER BY created_at DESC LIMIT 1
                """)
                
                result = await session.execute(query, {
                    "source_id": source_id,
                    "sync_type": sync_type.value
                })
                
                row = result.fetchone()
                if row:
                    return SyncRecord(
                        id=row.id,
                        sync_type=SyncType(row.sync_type),
                        source_id=row.source_id,
                        target_id=row.target_id,
                        status=SyncStatus(row.status),
                        data=json.loads(row.data) if row.data else None,
                        error_message=row.error_message,
                        retry_count=row.retry_count,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        synced_at=row.synced_at
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
                # 實際同步到主系統
                success = await self._sync_to_main_system(record)
            
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
    
    async def _sync_to_main_system(self, record: SyncRecord) -> bool:
        """實際同步到主系統"""
        if not self._session:
            self.logger.error("HTTP session not initialized")
            return False
        
        try:
            # 構建API端點
            endpoint = self._get_api_endpoint(record.sync_type)
            url = f"{self.config.main_system_api_url}{endpoint}"
            
            # 準備請求頭
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "PersonalityTest-DataSync/1.0"
            }
            
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            # 發送請求
            async with self._session.post(url, json=record.data, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    record.target_id = result.get("id") or result.get("target_id")
                    return True
                else:
                    error_text = await response.text()
                    record.error_message = f"HTTP {response.status}: {error_text}"
                    return False
                    
        except Exception as e:
            record.error_message = f"Sync error: {str(e)}"
            return False
    
    def _get_api_endpoint(self, sync_type: SyncType) -> str:
        """獲取API端點"""
        endpoints = {
            SyncType.USER_DATA: "/api/v1/users/sync",
            SyncType.TEST_RESULT: "/api/v1/personality-tests/sync",
            SyncType.CONVERSION_DATA: "/api/v1/conversions/sync",
            SyncType.BEHAVIOR_DATA: "/api/v1/behaviors/sync"
        }
        return endpoints.get(sync_type, "/api/v1/sync")
    
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
            async with self.db_manager.get_session() as session:
                query = text("""
                    SELECT u.*, p.personality_type, p.risk_tolerance, p.investment_style
                    FROM users u
                    LEFT JOIN personality_test_results p ON u.id = p.user_id
                    WHERE u.id = :user_id
                """)
                
                result = await session.execute(query, {"user_id": user_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row.id,
                        "email": row.email,
                        "name": row.name,
                        "phone": row.phone,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                        "personality_type": row.personality_type,
                        "risk_tolerance": row.risk_tolerance,
                        "investment_style": row.investment_style,
                        "source": "personality_test_website"
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting user data: {str(e)}")
            return None
    
    async def _get_test_result_data(self, result_id: str) -> Optional[Dict[str, Any]]:
        """獲取測試結果數據"""
        try:
            async with self.db_manager.get_session() as session:
                query = text("""
                    SELECT r.*, u.email as user_email
                    FROM personality_test_results r
                    LEFT JOIN users u ON r.user_id = u.id
                    WHERE r.id = :result_id
                """)
                
                result = await session.execute(query, {"result_id": result_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row.id,
                        "user_id": row.user_id,
                        "user_email": row.user_email,
                        "personality_type": row.personality_type,
                        "risk_tolerance": row.risk_tolerance,
                        "investment_style": row.investment_style,
                        "scores": json.loads(row.scores) if row.scores else {},
                        "answers": json.loads(row.answers) if row.answers else {},
                        "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                        "source": "personality_test_website"
                    }
                
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting test result data: {str(e)}")
            return None
    
    async def _get_conversion_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取轉換數據"""
        try:
            async with self.db_manager.get_session() as session:
                query = text("""
                    SELECT * FROM conversion_tracking
                    WHERE session_id = :session_id
                    ORDER BY created_at
                """)
                
                result = await session.execute(query, {"session_id": session_id})
                rows = result.fetchall()
                
                if rows:
                    conversion_steps = []
                    for row in rows:
                        conversion_steps.append({
                            "step": row.step,
                            "action": row.action,
                            "data": json.loads(row.data) if row.data else {},
                            "timestamp": row.created_at.isoformat() if row.created_at else None
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
    
    async def _get_behavior_data(self, user_id: str, start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """獲取行為數據"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)  # 默認最近7天
            
            async with self.db_manager.get_session() as session:
                query = text("""
                    SELECT * FROM user_behavior_logs
                    WHERE user_id = :user_id AND created_at >= :start_date
                    ORDER BY created_at
                """)
                
                result = await session.execute(query, {
                    "user_id": user_id,
                    "start_date": start_date
                })
                rows = result.fetchall()
                
                behavior_data = []
                for row in rows:
                    behavior_data.append({
                        "user_id": row.user_id,
                        "action": row.action,
                        "page": row.page,
                        "data": json.loads(row.data) if row.data else {},
                        "timestamp": row.created_at.isoformat() if row.created_at else None,
                        "source": "personality_test_website"
                    })
                
                return behavior_data
                
        except Exception as e:
            self.logger.error(f"Error getting behavior data: {str(e)}")
            return []
    
    async def _get_pending_sync_records(self, sync_type: Optional[SyncType] = None, limit: int = 100) -> List[SyncRecord]:
        """獲取待同步記錄"""
        try:
            async with self.db_manager.get_session() as session:
                if sync_type:
                    query = text("""
                        SELECT * FROM sync_records
                        WHERE sync_type = :sync_type 
                        AND (status = :pending OR (status = :failed AND retry_count < :max_retries))
                        ORDER BY created_at LIMIT :limit
                    """)
                    params = {
                        "sync_type": sync_type.value,
                        "pending": SyncStatus.PENDING.value,
                        "failed": SyncStatus.FAILED.value,
                        "max_retries": self.config.retry_attempts,
                        "limit": limit
                    }
                else:
                    query = text("""
                        SELECT * FROM sync_records
                        WHERE (status = :pending OR (status = :failed AND retry_count < :max_retries))
                        ORDER BY created_at LIMIT :limit
                    """)
                    params = {
                        "pending": SyncStatus.PENDING.value,
                        "failed": SyncStatus.FAILED.value,
                        "max_retries": self.config.retry_attempts,
                        "limit": limit
                    }
                
                result = await session.execute(query, params)
                rows = result.fetchall()
                
                records = []
                for row in rows:
                    records.append(SyncRecord(
                        id=row.id,
                        sync_type=SyncType(row.sync_type),
                        source_id=row.source_id,
                        target_id=row.target_id,
                        status=SyncStatus(row.status),
                        data=json.loads(row.data) if row.data else None,
                        error_message=row.error_message,
                        retry_count=row.retry_count,
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        synced_at=row.synced_at
                    ))
                
                return records
                
        except Exception as e:
            self.logger.error(f"Error getting pending sync records: {str(e)}")
            return []
    
    async def _save_sync_record(self, record: SyncRecord) -> bool:
        """保存同步記錄"""
        try:
            async with self.db_manager.get_session() as session:
                if record.id:
                    # 更新現有記錄
                    query = text("""
                        UPDATE sync_records SET
                            status = :status,
                            target_id = :target_id,
                            error_message = :error_message,
                            retry_count = :retry_count,
                            updated_at = :updated_at,
                            synced_at = :synced_at
                        WHERE id = :id
                    """)
                    params = {
                        "id": record.id,
                        "status": record.status.value,
                        "target_id": record.target_id,
                        "error_message": record.error_message,
                        "retry_count": record.retry_count,
                        "updated_at": record.updated_at or datetime.utcnow(),
                        "synced_at": record.synced_at
                    }
                else:
                    # 創建新記錄
                    query = text("""
                        INSERT INTO sync_records (
                            sync_type, source_id, target_id, status, data,
                            error_message, retry_count, created_at, updated_at, synced_at
                        ) VALUES (
                            :sync_type, :source_id, :target_id, :status, :data,
                            :error_message, :retry_count, :created_at, :updated_at, :synced_at
                        )
                    """)
                    params = {
                        "sync_type": record.sync_type.value,
                        "source_id": record.source_id,
                        "target_id": record.target_id,
                        "status": record.status.value,
                        "data": json.dumps(record.data) if record.data else None,
                        "error_message": record.error_message,
                        "retry_count": record.retry_count,
                        "created_at": record.created_at or datetime.utcnow(),
                        "updated_at": record.updated_at or datetime.utcnow(),
                        "synced_at": record.synced_at
                    }
                
                await session.execute(query, params)
                await session.commit()
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


# 全局數據同步服務實例
_data_sync_service = None

def get_data_sync_service(config: Optional[SyncConfig] = None) -> DataSyncService:
    """獲取數據同步服務實例"""
    global _data_sync_service
    if _data_sync_service is None:
        _data_sync_service = DataSyncService(config)
    return _data_sync_service