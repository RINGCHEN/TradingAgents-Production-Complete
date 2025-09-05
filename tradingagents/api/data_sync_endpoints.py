"""
數據同步API端點
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field

from ..services.data_sync_service import (
    get_data_sync_service, 
    DataSyncService, 
    SyncConfig, 
    SyncType, 
    SyncStatus
)
from ..database.database_manager import get_database_manager


# 請求模型
class SyncRequest(BaseModel):
    """同步請求模型"""
    source_id: str = Field(..., description="源ID")
    sync_type: SyncType = Field(..., description="同步類型")
    force: bool = Field(False, description="是否強制同步")


class BatchSyncRequest(BaseModel):
    """批量同步請求模型"""
    sync_type: Optional[SyncType] = Field(None, description="同步類型，None表示所有類型")
    limit: int = Field(100, description="批量限制", ge=1, le=1000)


class SyncConfigRequest(BaseModel):
    """同步配置請求模型"""
    main_system_api_url: Optional[str] = None
    sync_batch_size: Optional[int] = Field(None, ge=1, le=1000)
    retry_attempts: Optional[int] = Field(None, ge=1, le=10)
    sync_interval: Optional[int] = Field(None, ge=60, le=3600)
    timeout: Optional[int] = Field(None, ge=5, le=300)
    api_key: Optional[str] = None
    enable_real_time_sync: Optional[bool] = None
    enable_batch_sync: Optional[bool] = None


# 響應模型
class SyncResponse(BaseModel):
    """同步響應模型"""
    success: bool
    message: str
    sync_id: Optional[str] = None
    target_id: Optional[str] = None


class SyncStatusResponse(BaseModel):
    """同步狀態響應模型"""
    source_id: str
    sync_type: SyncType
    status: SyncStatus
    target_id: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    synced_at: Optional[datetime] = None


class BatchSyncResponse(BaseModel):
    """批量同步響應模型"""
    total: int
    success: int
    failed: int
    skipped: int
    message: str


class SyncStatisticsResponse(BaseModel):
    """同步統計響應模型"""
    date: str
    sync_type: SyncType
    total_records: int
    success_records: int
    failed_records: int
    success_rate: float
    avg_sync_time: Optional[float] = None


# 創建路由器
router = APIRouter(prefix="/api/data-sync", tags=["數據同步"])


@router.post("/sync-user", response_model=SyncResponse)
async def sync_user_data(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    同步用戶數據到主系統
    """
    try:
        if request.sync_type != SyncType.USER_DATA:
            raise HTTPException(status_code=400, detail="Invalid sync type for user data")
        
        async with sync_service:
            success = await sync_service.sync_user_data(request.source_id, request.force)
            
            if success:
                # 獲取同步狀態
                sync_record = await sync_service.get_sync_status(request.source_id, SyncType.USER_DATA)
                
                return SyncResponse(
                    success=True,
                    message="User data synced successfully",
                    sync_id=sync_record.id if sync_record else None,
                    target_id=sync_record.target_id if sync_record else None
                )
            else:
                return SyncResponse(
                    success=False,
                    message="Failed to sync user data"
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/sync-test-result", response_model=SyncResponse)
async def sync_test_result(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    同步測試結果到主系統
    """
    try:
        if request.sync_type != SyncType.TEST_RESULT:
            raise HTTPException(status_code=400, detail="Invalid sync type for test result")
        
        async with sync_service:
            success = await sync_service.sync_test_result(request.source_id, request.force)
            
            if success:
                sync_record = await sync_service.get_sync_status(request.source_id, SyncType.TEST_RESULT)
                
                return SyncResponse(
                    success=True,
                    message="Test result synced successfully",
                    sync_id=sync_record.id if sync_record else None,
                    target_id=sync_record.target_id if sync_record else None
                )
            else:
                return SyncResponse(
                    success=False,
                    message="Failed to sync test result"
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/sync-conversion", response_model=SyncResponse)
async def sync_conversion_data(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    同步轉換數據到主系統
    """
    try:
        if request.sync_type != SyncType.CONVERSION_DATA:
            raise HTTPException(status_code=400, detail="Invalid sync type for conversion data")
        
        async with sync_service:
            success = await sync_service.sync_conversion_data(request.source_id, request.force)
            
            if success:
                sync_record = await sync_service.get_sync_status(request.source_id, SyncType.CONVERSION_DATA)
                
                return SyncResponse(
                    success=True,
                    message="Conversion data synced successfully",
                    sync_id=sync_record.id if sync_record else None,
                    target_id=sync_record.target_id if sync_record else None
                )
            else:
                return SyncResponse(
                    success=False,
                    message="Failed to sync conversion data"
                )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/sync-behavior", response_model=SyncResponse)
async def sync_behavior_data(
    user_id: str,
    background_tasks: BackgroundTasks,
    days: int = Query(7, description="同步最近幾天的數據", ge=1, le=30),
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    同步用戶行為數據到主系統
    """
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with sync_service:
            success = await sync_service.sync_behavior_data(user_id, start_date)
            
            return SyncResponse(
                success=success,
                message=f"Behavior data synced successfully for {days} days" if success else "Failed to sync behavior data"
            )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")


@router.post("/batch-sync", response_model=BatchSyncResponse)
async def batch_sync(
    request: BatchSyncRequest,
    background_tasks: BackgroundTasks,
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    批量同步待同步的數據
    """
    try:
        async with sync_service:
            stats = await sync_service.batch_sync(request.sync_type, request.limit)
            
            return BatchSyncResponse(
                total=stats["total"],
                success=stats["success"],
                failed=stats["failed"],
                skipped=stats["skipped"],
                message=f"Batch sync completed: {stats['success']}/{stats['total']} successful"
            )
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch sync error: {str(e)}")


@router.get("/status/{source_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    source_id: str,
    sync_type: SyncType,
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    獲取同步狀態
    """
    try:
        async with sync_service:
            sync_record = await sync_service.get_sync_status(source_id, sync_type)
            
            if not sync_record:
                raise HTTPException(status_code=404, detail="Sync record not found")
            
            return SyncStatusResponse(
                source_id=sync_record.source_id,
                sync_type=sync_record.sync_type,
                status=sync_record.status,
                target_id=sync_record.target_id,
                error_message=sync_record.error_message,
                retry_count=sync_record.retry_count,
                created_at=sync_record.created_at,
                updated_at=sync_record.updated_at,
                synced_at=sync_record.synced_at
            )
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync status: {str(e)}")


@router.get("/statistics", response_model=List[SyncStatisticsResponse])
async def get_sync_statistics(
    days: int = Query(7, description="統計最近幾天的數據", ge=1, le=30),
    sync_type: Optional[SyncType] = Query(None, description="同步類型篩選")
):
    """
    獲取同步統計數據
    """
    try:
        db_manager = get_database_manager()
        
        async with db_manager.get_session() as session:
            # 構建查詢
            if sync_type:
                query = """
                    SELECT 
                        date,
                        sync_type,
                        total_records,
                        success_records,
                        failed_records,
                        avg_sync_time
                    FROM sync_statistics 
                    WHERE date >= date('now', '-{} days') AND sync_type = ?
                    ORDER BY date DESC, sync_type
                """.format(days)
                params = [sync_type.value]
            else:
                query = """
                    SELECT 
                        date,
                        sync_type,
                        total_records,
                        success_records,
                        failed_records,
                        avg_sync_time
                    FROM sync_statistics 
                    WHERE date >= date('now', '-{} days')
                    ORDER BY date DESC, sync_type
                """.format(days)
                params = []
            
            from sqlalchemy import text
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            statistics = []
            for row in rows:
                success_rate = (row.success_records / row.total_records * 100) if row.total_records > 0 else 0
                
                statistics.append(SyncStatisticsResponse(
                    date=row.date,
                    sync_type=SyncType(row.sync_type),
                    total_records=row.total_records,
                    success_records=row.success_records,
                    failed_records=row.failed_records,
                    success_rate=round(success_rate, 2),
                    avg_sync_time=row.avg_sync_time
                ))
            
            return statistics
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync statistics: {str(e)}")


@router.get("/config", response_model=Dict[str, Any])
async def get_sync_config():
    """
    獲取同步配置
    """
    try:
        db_manager = get_database_manager()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            query = text("SELECT config_key, config_value FROM sync_config")
            result = await session.execute(query)
            rows = result.fetchall()
            
            config = {}
            for row in rows:
                # 轉換配置值類型
                value = row.config_value
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif value.replace('.', '').isdigit():
                    value = float(value)
                
                config[row.config_key] = value
            
            return config
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sync config: {str(e)}")


@router.put("/config", response_model=Dict[str, str])
async def update_sync_config(request: SyncConfigRequest):
    """
    更新同步配置
    """
    try:
        db_manager = get_database_manager()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # 更新配置
            config_updates = request.dict(exclude_unset=True)
            updated_keys = []
            
            for key, value in config_updates.items():
                if value is not None:
                    query = text("""
                        UPDATE sync_config 
                        SET config_value = :value, updated_at = CURRENT_TIMESTAMP 
                        WHERE config_key = :key
                    """)
                    
                    await session.execute(query, {
                        "key": key,
                        "value": str(value)
                    })
                    updated_keys.append(key)
            
            await session.commit()
            
            return {
                "message": f"Updated {len(updated_keys)} configuration items",
                "updated_keys": updated_keys
            }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating sync config: {str(e)}")


@router.post("/validate", response_model=Dict[str, Any])
async def validate_sync_data(
    sync_type: SyncType,
    data: Dict[str, Any],
    sync_service: DataSyncService = Depends(get_data_sync_service)
):
    """
    驗證同步數據的完整性和格式
    """
    try:
        async with sync_service:
            is_valid, errors = await sync_service.validate_sync_data(data, sync_type)
            
            return {
                "valid": is_valid,
                "errors": errors,
                "sync_type": sync_type.value,
                "data_size": len(str(data))
            }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")


@router.delete("/records/{source_id}")
async def delete_sync_records(
    source_id: str,
    sync_type: Optional[SyncType] = Query(None, description="同步類型篩選")
):
    """
    刪除同步記錄
    """
    try:
        db_manager = get_database_manager()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            if sync_type:
                query = text("DELETE FROM sync_records WHERE source_id = :source_id AND sync_type = :sync_type")
                params = {"source_id": source_id, "sync_type": sync_type.value}
            else:
                query = text("DELETE FROM sync_records WHERE source_id = :source_id")
                params = {"source_id": source_id}
            
            result = await session.execute(query, params)
            await session.commit()
            
            return {
                "message": f"Deleted {result.rowcount} sync records",
                "source_id": source_id,
                "sync_type": sync_type.value if sync_type else "all"
            }
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting sync records: {str(e)}")


@router.get("/health")
async def sync_service_health():
    """
    同步服務健康檢查
    """
    try:
        db_manager = get_database_manager()
        
        async with db_manager.get_session() as session:
            from sqlalchemy import text
            
            # 檢查數據庫連接
            await session.execute(text("SELECT 1"))
            
            # 檢查同步記錄表
            result = await session.execute(text("SELECT COUNT(*) as count FROM sync_records"))
            total_records = result.fetchone().count
            
            # 檢查最近的同步活動
            result = await session.execute(text("""
                SELECT COUNT(*) as count FROM sync_records 
                WHERE created_at >= datetime('now', '-1 hour')
            """))
            recent_records = result.fetchone().count
            
            return {
                "status": "healthy",
                "database": "connected",
                "total_sync_records": total_records,
                "recent_sync_records": recent_records,
                "timestamp": datetime.utcnow().isoformat()
            }
                
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")