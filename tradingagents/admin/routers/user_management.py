#!/usr/bin/env python3
"""
用戶管理路由器 (User Management Router)
天工 (TianGong) - 用戶管理 API 端點

此模組提供完整的用戶管理 API 端點，包含：
1. 用戶的 CRUD 操作
2. 用戶搜索和篩選
3. 用戶統計和分析
4. 批量操作和導出
5. 用戶訂閱信息管理
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session

from ..models.user_management import (
    UserSearchRequest, UserResponse, UserListResponse, UserCreateRequest,
    UserUpdateRequest, UserQuotaUpdateRequest, UserSubscriptionInfo,
    UserStatistics, UserActivityLog, UserBulkAction, UserBulkActionResult,
    UserExportRequest, UserExportResult, UserManagementSystemInfo,
    UserStatusInfo, MembershipTierInfo, AuthProviderInfo
)
from ...models.user import UserStatus, MembershipTier, AuthProvider
from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("user_management")
security_logger = get_security_logger("user_management")

# 創建路由器
router = APIRouter(prefix="/users", tags=["用戶管理"])

# ==================== 用戶管理 ====================

@router.get("/", response_model=UserListResponse, summary="獲取用戶列表")
async def get_users(
    search: UserSearchRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取用戶列表，支持搜索和篩選
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        result = await user_service.search_users(search)
        
        api_logger.info("用戶列表查詢", extra={
            'admin_user_id': current_user.user_id,
            'search_params': search.dict(),
            'result_count': result.total
        })
        
        return result
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/',
            'admin_user_id': current_user.user_id,
            'search_params': search.dict()
        })
        
        api_logger.error("用戶列表查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶查詢服務暫時不可用"
        )

@router.get("/{user_id}", response_model=UserResponse, summary="獲取用戶詳情")
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取指定用戶的詳細信息
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        user = await user_service.get_user(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        api_logger.info("用戶詳情查詢", extra={
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'target_user_email': user.email
        })
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/users/{user_id}',
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        api_logger.error("用戶詳情查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶查詢服務暫時不可用"
        )

@router.post("/", response_model=UserResponse, summary="創建用戶")
async def create_user(
    user_data: UserCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    創建新用戶
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        # 檢查郵箱是否已存在
        existing_user = await user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"郵箱 '{user_data.email}' 已被使用"
            )
        
        # 創建用戶
        user = await user_service.create_user(user_data, current_user.user_id)
        
        security_logger.info("管理員創建用戶", extra={
            'admin_user_id': current_user.user_id,
            'created_user_id': user.id,
            'created_user_email': user.email,
            'membership_tier': user.membership_tier,
            'creation_reason': user_data.creation_reason
        })
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/',
            'admin_user_id': current_user.user_id,
            'user_data': user_data.dict(exclude={'password'})
        })
        
        api_logger.error("用戶創建失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_email': user_data.email
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶創建服務暫時不可用"
        )

@router.put("/{user_id}", response_model=UserResponse, summary="更新用戶")
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    更新指定用戶的信息
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        # 檢查用戶是否存在
        existing_user = await user_service.get_user(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        # 更新用戶
        updated_user = await user_service.update_user(
            user_id, user_data, current_user.user_id
        )
        
        security_logger.info("管理員更新用戶", extra={
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'target_user_email': updated_user.email,
            'update_reason': user_data.update_reason,
            'updated_fields': [k for k, v in user_data.dict().items() if v is not None]
        })
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/users/{user_id}',
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'user_data': user_data.dict()
        })
        
        api_logger.error("用戶更新失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶更新服務暫時不可用"
        )

@router.delete("/{user_id}", summary="刪除用戶")
async def delete_user(
    user_id: int,
    soft_delete: bool = Query(True, description="是否軟刪除"),
    deletion_reason: Optional[str] = Query(None, description="刪除原因"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    刪除指定用戶
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        # 檢查用戶是否存在
        existing_user = await user_service.get_user(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        # 防止刪除自己
        if user_id == int(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能刪除自己的帳戶"
            )
        
        # 刪除用戶
        await user_service.delete_user(
            user_id, current_user.user_id, soft_delete, deletion_reason
        )
        
        security_logger.warning("管理員刪除用戶", extra={
            'admin_user_id': current_user.user_id,
            'deleted_user_id': user_id,
            'deleted_user_email': existing_user.email,
            'soft_delete': soft_delete,
            'deletion_reason': deletion_reason
        })
        
        return {"message": "用戶刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/users/{user_id}',
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'soft_delete': soft_delete
        })
        
        api_logger.error("用戶刪除失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶刪除服務暫時不可用"
        )

# ==================== 用戶配額管理 ====================

@router.put("/{user_id}/quota", response_model=UserResponse, summary="更新用戶配額")
async def update_user_quota(
    user_id: int,
    quota_data: UserQuotaUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    更新用戶的 API 配額
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        # 檢查用戶是否存在
        existing_user = await user_service.get_user(user_id)
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        # 更新配額
        updated_user = await user_service.update_user_quota(
            user_id, quota_data, current_user.user_id
        )
        
        security_logger.info("管理員更新用戶配額", extra={
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'target_user_email': updated_user.email,
            'quota_changes': quota_data.dict(),
            'update_reason': quota_data.update_reason
        })
        
        return updated_user
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/users/{user_id}/quota',
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'quota_data': quota_data.dict()
        })
        
        api_logger.error("用戶配額更新失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶配額更新服務暫時不可用"
        )

# ==================== 用戶訂閱信息 ====================

@router.get("/{user_id}/subscription", response_model=UserSubscriptionInfo, summary="獲取用戶訂閱信息")
async def get_user_subscription(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取用戶的訂閱信息
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        subscription_info = await user_service.get_user_subscription_info(user_id)
        
        if not subscription_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        api_logger.info("用戶訂閱信息查詢", extra={
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'has_subscription': subscription_info.has_active_subscription
        })
        
        return subscription_info
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/users/{user_id}/subscription',
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        api_logger.error("用戶訂閱信息查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶訂閱信息查詢服務暫時不可用"
        )

# ==================== 用戶活動日誌 ====================

@router.get("/{user_id}/activity", response_model=List[UserActivityLog], summary="獲取用戶活動日誌")
async def get_user_activity(
    user_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回記錄數量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    activity_type: Optional[str] = Query(None, description="活動類型篩選"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取用戶的活動日誌
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        activity_logs = await user_service.get_user_activity_logs(
            user_id, limit, offset, activity_type
        )
        
        api_logger.info("用戶活動日誌查詢", extra={
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id,
            'activity_count': len(activity_logs)
        })
        
        return activity_logs
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/admin/users/{user_id}/activity',
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        api_logger.error("用戶活動日誌查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'target_user_id': user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶活動日誌查詢服務暫時不可用"
        )

# ==================== 統計和分析 ====================

@router.get("/statistics/overview", response_model=UserStatistics, summary="獲取用戶統計")
async def get_user_statistics(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取用戶統計信息
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        statistics = await user_service.get_user_statistics()
        
        api_logger.info("用戶統計查詢", extra={
            'admin_user_id': current_user.user_id,
            'total_users': statistics.total_users
        })
        
        return statistics
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/statistics/overview',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("用戶統計查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶統計查詢服務暫時不可用"
        )

@router.get("/system-info", response_model=UserManagementSystemInfo, summary="獲取用戶管理系統信息")
async def get_user_management_system_info(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取用戶管理系統的整體信息
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        system_info = await user_service.get_system_info()
        
        api_logger.info("用戶管理系統信息查詢", extra={
            'admin_user_id': current_user.user_id,
            'total_users': system_info.total_users
        })
        
        return system_info
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/system-info',
            'admin_user_id': current_user.user_id
        })
        
        api_logger.error("用戶管理系統信息查詢失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶管理系統信息查詢服務暫時不可用"
        )

# ==================== 批量操作 ====================

@router.post("/bulk-action", response_model=UserBulkActionResult, summary="批量操作用戶")
async def bulk_action_users(
    bulk_action: UserBulkAction,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    對多個用戶執行批量操作
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        result = await user_service.bulk_action_users(
            bulk_action, current_user.user_id
        )
        
        security_logger.info("用戶批量操作完成", extra={
            'admin_user_id': current_user.user_id,
            'action': bulk_action.action,
            'total_count': result.total_count,
            'success_count': result.success_count,
            'failed_count': result.failed_count,
            'action_reason': bulk_action.action_reason
        })
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/bulk-action',
            'admin_user_id': current_user.user_id,
            'bulk_action': bulk_action.dict()
        })
        
        api_logger.error("用戶批量操作失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id,
            'action': bulk_action.action
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶批量操作服務暫時不可用"
        )

# ==================== 數據導出 ====================

@router.post("/export", response_model=UserExportResult, summary="導出用戶數據")
async def export_users(
    export_request: UserExportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access())
):
    """
    導出用戶數據
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        # 創建導出任務
        export_result = await user_service.create_export_task(
            export_request, current_user.user_id
        )
        
        # 添加後台任務執行實際導出
        background_tasks.add_task(
            user_service.execute_export_task,
            export_result.export_id,
            current_user.user_id
        )
        
        security_logger.info("用戶數據導出任務創建", extra={
            'admin_user_id': current_user.user_id,
            'export_id': export_result.export_id,
            'export_format': export_request.format,
            'include_sensitive': export_request.include_sensitive
        })
        
        return export_result
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/export',
            'admin_user_id': current_user.user_id,
            'export_request': export_request.dict()
        })
        
        api_logger.error("用戶數據導出失敗", extra={
            'error_id': error_info.error_id,
            'admin_user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶數據導出服務暫時不可用"
        )

# ==================== 元數據和枚舉 ====================

@router.get("/metadata/statuses", response_model=List[UserStatusInfo], summary="獲取用戶狀態列表")
async def get_user_statuses(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取所有可用的用戶狀態
    """
    statuses = [
        UserStatusInfo(
            value=UserStatus.ACTIVE,
            label="活躍",
            description="正常使用的用戶",
            color="green"
        ),
        UserStatusInfo(
            value=UserStatus.INACTIVE,
            label="非活躍",
            description="長時間未使用的用戶",
            color="gray"
        ),
        UserStatusInfo(
            value=UserStatus.SUSPENDED,
            label="暫停",
            description="被暫停使用的用戶",
            color="orange"
        ),
        UserStatusInfo(
            value=UserStatus.DELETED,
            label="已刪除",
            description="已刪除的用戶",
            color="red"
        )
    ]
    
    return statuses

@router.get("/metadata/membership-tiers", response_model=List[MembershipTierInfo], summary="獲取會員等級列表")
async def get_membership_tiers(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取所有可用的會員等級
    """
    tiers = [
        MembershipTierInfo(
            value=MembershipTier.FREE,
            label="免費會員",
            description="基礎功能使用者",
            features=["基礎分析", "有限配額"],
            daily_quota=100,
            monthly_quota=3000
        ),
        MembershipTierInfo(
            value=MembershipTier.GOLD,
            label="黃金會員",
            description="進階功能使用者",
            features=["進階分析", "更多配額", "優先支援"],
            daily_quota=500,
            monthly_quota=15000
        ),
        MembershipTierInfo(
            value=MembershipTier.DIAMOND,
            label="鑽石會員",
            description="完整功能使用者",
            features=["完整分析", "無限配額", "專屬支援", "API 訪問"],
            daily_quota=2000,
            monthly_quota=60000
        )
    ]
    
    return tiers

@router.get("/metadata/auth-providers", response_model=List[AuthProviderInfo], summary="獲取認證提供者列表")
async def get_auth_providers(
    current_user: UserContext = Depends(require_admin_access())
):
    """
    獲取所有可用的認證提供者
    """
    providers = [
        AuthProviderInfo(
            value=AuthProvider.EMAIL,
            label="郵箱註冊",
            description="使用郵箱和密碼註冊",
            icon="email"
        ),
        AuthProviderInfo(
            value=AuthProvider.GOOGLE,
            label="Google OAuth",
            description="使用 Google 帳戶登入",
            icon="google"
        ),
        AuthProviderInfo(
            value=AuthProvider.FACEBOOK,
            label="Facebook OAuth",
            description="使用 Facebook 帳戶登入",
            icon="facebook"
        ),
        AuthProviderInfo(
            value=AuthProvider.LINE,
            label="LINE OAuth",
            description="使用 LINE 帳戶登入",
            icon="line"
        )
    ]
    
    return providers

# ==================== 健康檢查 ====================

@router.get("/health", summary="用戶管理服務健康檢查")
async def user_management_health_check(
    db: Session = Depends(get_db)
):
    """
    用戶管理服務健康檢查
    """
    try:
        from ..services.user_management_service import UserManagementService
        user_service = UserManagementService(db)
        
        # 檢查數據庫連接和基本功能
        health_status = await user_service.health_check()
        
        return {
            "status": "healthy" if health_status["database"] else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": health_status,
            "service": "user_management"
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/admin/users/health'
        })
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_id": error_info.error_id,
            "service": "user_management"
        }


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    # 測試路由配置
    print("用戶管理路由配置:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")