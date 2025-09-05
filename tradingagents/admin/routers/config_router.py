#!/usr/bin/env python3
"""
配置管理路由器 (Configuration Management Router)
天工 (TianGong) - 配置管理 API 端點

此模組提供完整的配置管理 API 端點，包含：
1. 配置項的 CRUD 操作
2. 配置變更歷史管理
3. 配置驗證和審批
4. 配置統計和搜索
5. 批量操作和模板管理
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..models.config import (
    ConfigItemCreate, ConfigItemUpdate, ConfigItemResponse, ConfigItemListResponse,
    ConfigChangeHistoryResponse, ConfigChangeApproval, ConfigValidationRequest,
    ConfigValidationResult, ConfigStatistics, ConfigSearchRequest, ConfigSystemInfo,
    ConfigBulkAction, ConfigBulkActionResult, ConfigCategoryInfo, ConfigTypeInfo,
    ConfigEnvironmentInfo
)
from ...database.config_models import (
    ConfigCategory, ConfigType, ConfigEnvironment, ConfigStatus,
    ChangeType, ApprovalStatus
)
from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error
from ...utils.cache_manager import CacheManager

# 配置日誌
api_logger = get_api_logger("config_router")
security_logger = get_security_logger("config_router")

# 創建路由器
router = APIRouter(prefix="/config", tags=["配置管理"])

# ==================== 配置項管理 ====================

@router.get("/items", response_model=ConfigItemListResponse, summary="獲取配置項列表")
async def get_config_items(
    search: ConfigSearchRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取配置項列表，支持搜索和篩選
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        result = await config_service.search_config_items(search)
        
        api_logger.info("配置項列表查詢", extra={
            'user_id': current_user.user_id,
            'search_params': search.dict(),
            'result_count': result.total
        })
        
        return result
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/items',
            'user_id': current_user.user_id,
            'search_params': search.dict()
        })
        
        api_logger.error("配置項列表查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置項查詢服務暫時不可用"
        )

@router.get("/items/{item_id}", response_model=ConfigItemResponse, summary="獲取配置項詳情")
async def get_config_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定配置項的詳細信息
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        config_item = await config_service.get_config_item(item_id)
        
        if not config_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置項不存在"
            )
        
        api_logger.info("配置項詳情查詢", extra={
            'user_id': current_user.user_id,
            'config_id': item_id,
            'config_key': config_item.key
        })
        
        return config_item
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/config/items/{item_id}',
            'user_id': current_user.user_id
        })
        
        api_logger.error("配置項詳情查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'config_id': item_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置項查詢服務暫時不可用"
        )

@router.post("/items", response_model=ConfigItemResponse, summary="創建配置項")
async def create_config_item(
    config_data: ConfigItemCreate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    創建新的配置項
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        # 檢查配置鍵是否已存在
        existing_config = await config_service.get_config_by_key(
            config_data.key, config_data.environment
        )
        
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"配置鍵 '{config_data.key}' 在環境 '{config_data.environment}' 中已存在"
            )
        
        # 創建配置項
        config_item = await config_service.create_config_item(
            config_data, current_user.user_id
        )
        
        security_logger.info("配置項創建成功", extra={
            'user_id': current_user.user_id,
            'config_id': config_item.id,
            'config_key': config_item.key,
            'config_category': config_item.category
        })
        
        return config_item
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/items',
            'user_id': current_user.user_id,
            'config_data': config_data.dict()
        })
        
        api_logger.error("配置項創建失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'config_key': config_data.key
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置項創建服務暫時不可用"
        )

@router.put("/items/{item_id}", response_model=ConfigItemResponse, summary="更新配置項")
async def update_config_item(
    item_id: int,
    config_data: ConfigItemUpdate,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    更新指定的配置項
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        # 檢查配置項是否存在
        existing_config = await config_service.get_config_item(item_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置項不存在"
            )
        
        # 檢查是否為只讀配置
        if existing_config.is_readonly:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此配置項為只讀，無法修改"
            )
        
        # 更新配置項
        updated_config = await config_service.update_config_item(
            item_id, config_data, current_user.user_id
        )
        
        security_logger.info("配置項更新成功", extra={
            'user_id': current_user.user_id,
            'config_id': item_id,
            'config_key': updated_config.key,
            'change_reason': config_data.change_reason
        })
        
        return updated_config
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/config/items/{item_id}',
            'user_id': current_user.user_id,
            'config_data': config_data.dict()
        })
        
        api_logger.error("配置項更新失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'config_id': item_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置項更新服務暫時不可用"
        )

@router.delete("/items/{item_id}", summary="刪除配置項")
async def delete_config_item(
    item_id: int,
    change_reason: Optional[str] = Query(None, description="刪除原因"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    刪除指定的配置項
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        # 檢查配置項是否存在
        existing_config = await config_service.get_config_item(item_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="配置項不存在"
            )
        
        # 檢查是否為只讀配置
        if existing_config.is_readonly:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="此配置項為只讀，無法刪除"
            )
        
        # 刪除配置項
        await config_service.delete_config_item(
            item_id, current_user.user_id, change_reason
        )
        
        security_logger.info("配置項刪除成功", extra={
            'user_id': current_user.user_id,
            'config_id': item_id,
            'config_key': existing_config.key,
            'change_reason': change_reason
        })
        
        return {"message": "配置項刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/config/items/{item_id}',
            'user_id': current_user.user_id,
            'change_reason': change_reason
        })
        
        api_logger.error("配置項刪除失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'config_id': item_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置項刪除服務暫時不可用"
        )

# ==================== 配置變更管理 ====================

@router.get("/items/{item_id}/history", response_model=List[ConfigChangeHistoryResponse], summary="獲取配置變更歷史")
async def get_config_change_history(
    item_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回記錄數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定配置項的變更歷史
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        history = await config_service.get_config_change_history(
            item_id, limit, offset
        )
        
        api_logger.info("配置變更歷史查詢", extra={
            'user_id': current_user.user_id,
            'config_id': item_id,
            'history_count': len(history)
        })
        
        return history
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/config/items/{item_id}/history',
            'user_id': current_user.user_id
        })
        
        api_logger.error("配置變更歷史查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'config_id': item_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置變更歷史查詢服務暫時不可用"
        )

@router.post("/changes/{change_id}/approve", summary="審批配置變更")
async def approve_config_change(
    change_id: int,
    approval_data: ConfigChangeApproval,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    審批指定的配置變更
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        # 執行審批
        result = await config_service.approve_config_change(
            change_id, approval_data, current_user.user_id
        )
        
        security_logger.info("配置變更審批完成", extra={
            'user_id': current_user.user_id,
            'change_id': change_id,
            'approval_status': approval_data.approval_status,
            'approval_comment': approval_data.approval_comment
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/config/changes/{change_id}/approve',
            'user_id': current_user.user_id,
            'approval_data': approval_data.dict()
        })
        
        api_logger.error("配置變更審批失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'change_id': change_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置變更審批服務暫時不可用"
        )

# ==================== 配置驗證 ====================

@router.post("/validate", response_model=ConfigValidationResult, summary="驗證配置值")
async def validate_config_value(
    validation_request: ConfigValidationRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    驗證配置值的有效性
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        result = await config_service.validate_config_value(validation_request)
        
        api_logger.info("配置值驗證", extra={
            'user_id': current_user.user_id,
            'config_key': validation_request.key,
            'is_valid': result.is_valid
        })
        
        return result
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/validate',
            'user_id': current_user.user_id,
            'validation_request': validation_request.dict()
        })
        
        api_logger.error("配置值驗證失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'config_key': validation_request.key
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置值驗證服務暫時不可用"
        )

# ==================== 配置統計和系統信息 ====================

@router.get("/statistics", response_model=ConfigStatistics, summary="獲取配置統計")
async def get_config_statistics(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取配置系統的統計信息
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        statistics = await config_service.get_config_statistics()
        
        api_logger.info("配置統計查詢", extra={
            'user_id': current_user.user_id,
            'total_configs': statistics.total_configs
        })
        
        return statistics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/statistics',
            'user_id': current_user.user_id
        })
        
        api_logger.error("配置統計查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置統計查詢服務暫時不可用"
        )

@router.get("/system-info", response_model=ConfigSystemInfo, summary="獲取配置系統信息")
async def get_config_system_info(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取配置系統的整體信息
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        system_info = await config_service.get_system_info()
        
        api_logger.info("配置系統信息查詢", extra={
            'user_id': current_user.user_id,
            'current_environment': system_info.current_environment
        })
        
        return system_info
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/system-info',
            'user_id': current_user.user_id
        })
        
        api_logger.error("配置系統信息查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置系統信息查詢服務暫時不可用"
        )

# ==================== 批量操作 ====================

@router.post("/bulk-action", response_model=ConfigBulkActionResult, summary="批量操作配置項")
async def bulk_action_config_items(
    bulk_action: ConfigBulkAction,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    對多個配置項執行批量操作
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        result = await config_service.bulk_action_config_items(
            bulk_action, current_user.user_id
        )
        
        security_logger.info("配置項批量操作完成", extra={
            'user_id': current_user.user_id,
            'action': bulk_action.action,
            'total_count': result.total_count,
            'success_count': result.success_count,
            'failed_count': result.failed_count
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/bulk-action',
            'user_id': current_user.user_id,
            'bulk_action': bulk_action.dict()
        })
        
        api_logger.error("配置項批量操作失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'action': bulk_action.action
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="配置項批量操作服務暫時不可用"
        )

# ==================== 元數據和枚舉 ====================

@router.get("/categories", response_model=List[ConfigCategoryInfo], summary="獲取配置分類列表")
async def get_config_categories(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取所有可用的配置分類
    """
    categories = [
        ConfigCategoryInfo(
            value=ConfigCategory.SYSTEM,
            label="系統配置",
            description="系統核心配置項",
            icon="system"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.DATABASE,
            label="數據庫配置",
            description="數據庫連接和配置",
            icon="database"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.CACHE,
            label="緩存配置",
            description="緩存系統配置",
            icon="cache"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.SECURITY,
            label="安全配置",
            description="安全和認證配置",
            icon="security"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.API,
            label="API配置",
            description="API服務配置",
            icon="api"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.NOTIFICATION,
            label="通知配置",
            description="通知和消息配置",
            icon="notification"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.EXTERNAL,
            label="外部服務",
            description="外部服務集成配置",
            icon="external"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.FEATURE,
            label="功能開關",
            description="功能特性開關",
            icon="feature"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.UI,
            label="界面配置",
            description="用戶界面配置",
            icon="ui"
        ),
        ConfigCategoryInfo(
            value=ConfigCategory.MONITORING,
            label="監控配置",
            description="監控和日誌配置",
            icon="monitoring"
        )
    ]
    
    return categories

@router.get("/types", response_model=List[ConfigTypeInfo], summary="獲取配置類型列表")
async def get_config_types(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取所有可用的配置類型
    """
    types = [
        ConfigTypeInfo(
            value=ConfigType.STRING,
            label="字符串",
            description="文本字符串類型",
            validation_rules={"max_length": 1000}
        ),
        ConfigTypeInfo(
            value=ConfigType.INTEGER,
            label="整數",
            description="整數數值類型",
            validation_rules={"type": "integer"}
        ),
        ConfigTypeInfo(
            value=ConfigType.FLOAT,
            label="浮點數",
            description="浮點數數值類型",
            validation_rules={"type": "float"}
        ),
        ConfigTypeInfo(
            value=ConfigType.BOOLEAN,
            label="布爾值",
            description="真/假布爾類型",
            validation_rules={"type": "boolean"}
        ),
        ConfigTypeInfo(
            value=ConfigType.JSON,
            label="JSON",
            description="JSON對象類型",
            validation_rules={"type": "json"}
        ),
        ConfigTypeInfo(
            value=ConfigType.LIST,
            label="列表",
            description="數組列表類型",
            validation_rules={"type": "list"}
        ),
        ConfigTypeInfo(
            value=ConfigType.PASSWORD,
            label="密碼",
            description="敏感密碼類型",
            validation_rules={"sensitive": True, "min_length": 8}
        ),
        ConfigTypeInfo(
            value=ConfigType.URL,
            label="URL",
            description="網址鏈接類型",
            validation_rules={"format": "url"}
        ),
        ConfigTypeInfo(
            value=ConfigType.EMAIL,
            label="郵箱",
            description="電子郵箱類型",
            validation_rules={"format": "email"}
        ),
        ConfigTypeInfo(
            value=ConfigType.FILE_PATH,
            label="文件路徑",
            description="文件系統路徑類型",
            validation_rules={"format": "path"}
        )
    ]
    
    return types

@router.get("/environments", response_model=List[ConfigEnvironmentInfo], summary="獲取配置環境列表")
async def get_config_environments(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取所有可用的配置環境
    """
    environments = [
        ConfigEnvironmentInfo(
            value=ConfigEnvironment.DEVELOPMENT,
            label="開發環境",
            description="開發和測試環境",
            color="blue"
        ),
        ConfigEnvironmentInfo(
            value=ConfigEnvironment.TESTING,
            label="測試環境",
            description="自動化測試環境",
            color="yellow"
        ),
        ConfigEnvironmentInfo(
            value=ConfigEnvironment.STAGING,
            label="預發布環境",
            description="生產前驗證環境",
            color="orange"
        ),
        ConfigEnvironmentInfo(
            value=ConfigEnvironment.PRODUCTION,
            label="生產環境",
            description="正式生產環境",
            color="red"
        ),
        ConfigEnvironmentInfo(
            value=ConfigEnvironment.ALL,
            label="所有環境",
            description="適用於所有環境",
            color="green"
        )
    ]
    
    return environments

# ==================== 健康檢查 ====================

@router.get("/health", summary="配置管理服務健康檢查")
async def config_health_check(
    db: Session = Depends(get_db)
):
    """
    配置管理服務健康檢查
    """
    try:
        from ..services.config_service import ConfigService
        config_service = ConfigService(db)
        
        # 檢查數據庫連接
        health_status = await config_service.health_check()
        
        return {
            "status": "healthy" if health_status["database"] else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": health_status,
            "service": "config_management"
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/config/health'
        })
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_id": error_info.error_id,
            "service": "config_management"
        }

if __name__ == "__main__":
    # 測試路由配置
    print("配置管理路由配置:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")