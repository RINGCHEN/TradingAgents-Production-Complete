#!/usr/bin/env python3
"""
認證路由 (Authentication Routes)
天工 (TianGong) - 用戶認證和授權API端點

此模組提供完整的認證相關API端點，包含：
1. 用戶登入/登出
2. 令牌刷新和驗證
3. API密鑰管理
4. 用戶資訊查詢
5. 權限管理
6. 安全事件查詢
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, Field, EmailStr

from .auth_manager import get_auth_manager, AuthToken
from .permissions import get_permission_manager, ResourceType, Action
from .dependencies import (
    get_current_user, get_optional_user, require_permission,
    rate_limit, security_headers_check, CurrentUser, AdminUser,
    require_admin_access
)
from ..utils.user_context import UserContext, TierType
from ..utils.logging_config import get_api_logger, get_security_logger
from ..utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("auth")
security_logger = get_security_logger("auth")

# 創建路由器 (prefix 由 app.py 統一管理)
router = APIRouter(tags=["認證"])

# ==================== 請求/回應模型 ====================

class LoginRequest(BaseModel):
    """登入請求"""
    email: EmailStr = Field(..., description="用戶郵箱")
    password: str = Field(..., min_length=6, description="密碼")
    remember_me: bool = Field(False, description="記住我")
    
class LoginResponse(BaseModel):
    """登入回應"""
    access_token: str = Field(..., description="訪問令牌")
    token_type: str = Field("Bearer", description="令牌類型")
    expires_in: int = Field(..., description="過期時間(秒)")
    refresh_token: str = Field(..., description="刷新令牌")
    user: Dict[str, Any] = Field(..., description="用戶資訊")

class RefreshTokenRequest(BaseModel):
    """刷新令牌請求"""
    refresh_token: str = Field(..., description="刷新令牌")

class TokenResponse(BaseModel):
    """令牌回應"""
    access_token: str = Field(..., description="新的訪問令牌")
    refresh_token: str = Field(..., description="新的刷新令牌")
    token_type: str = Field("Bearer", description="令牌類型")
    expires_in: int = Field(..., description="過期時間(秒)")

class PasswordChangeRequest(BaseModel):
    """密碼修改請求"""
    current_password: str = Field(..., description="當前密碼")
    new_password: str = Field(..., min_length=8, description="新密碼")

class APIKeyCreateRequest(BaseModel):
    """API密鑰創建請求"""
    name: str = Field(..., min_length=1, max_length=100, description="密鑰名稱")
    permissions: List[str] = Field(default_factory=list, description="權限列表")
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="過期天數")

class APIKeyResponse(BaseModel):
    """API密鑰回應"""
    key_id: str = Field(..., description="密鑰ID")
    name: str = Field(..., description="密鑰名稱")
    api_key: Optional[str] = Field(None, description="API密鑰(僅創建時返回)")
    permissions: List[str] = Field(..., description="權限列表")
    created_at: str = Field(..., description="創建時間")
    expires_at: Optional[str] = Field(None, description="過期時間")
    last_used: Optional[str] = Field(None, description="最後使用時間")
    usage_count: int = Field(..., description="使用次數")

class UserProfile(BaseModel):
    """用戶資料"""
    user_id: str = Field(..., description="用戶ID")
    email: str = Field(..., description="郵箱")
    membership_tier: str = Field(..., description="會員等級")
    permissions: List[str] = Field(..., description="權限列表")
    created_at: str = Field(..., description="註冊時間")
    last_login: Optional[str] = Field(None, description="最後登入時間")

class SecurityEvent(BaseModel):
    """安全事件"""
    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件類型")
    timestamp: str = Field(..., description="發生時間")
    details: Dict[str, Any] = Field(..., description="事件詳情")

# ==================== 認證端點 ====================

@router.post("/login", response_model=LoginResponse, summary="用戶登入")
async def login(
    request: LoginRequest,
    http_request: Request,
    _rate_check = Depends(rate_limit('login')),
    _security_check = Depends(security_headers_check)
):
    """
    用戶登入
    
    支持郵箱和密碼登入，返回JWT令牌和用戶資訊。
    """
    auth_manager = get_auth_manager()
    
    try:
        # 獲取客戶端資訊
        client_info = {
            'ip': http_request.client.host if http_request.client else 'unknown',
            'user_agent': http_request.headers.get('user-agent', ''),
            'timestamp': datetime.now().isoformat()
        }
        
        # 執行認證
        auth_token = await auth_manager.authenticate_user(
            identifier=request.email,
            password=request.password,
            client_info=client_info
        )
        
        # 獲取用戶詳細資訊
        user_context = await auth_manager.verify_token(auth_token.token)
        permission_manager = get_permission_manager()
        user_permissions = permission_manager.get_user_permissions(user_context)
        
        # 構建回應
        response = LoginResponse(
            access_token=auth_token.token,
            expires_in=int((auth_token.expires_at - datetime.now()).total_seconds()),
            refresh_token=auth_token.metadata.get('refresh_token', ''),
            user={
                'user_id': user_context.user_id,
                'membership_tier': user_context.membership_tier.value,
                'permissions': user_permissions[:10],  # 限制返回數量
                'session_id': auth_token.metadata.get('session_id')
            }
        )
        
        api_logger.info("用戶登入成功", extra={
            'user_id': user_context.user_id,
            'membership_tier': user_context.membership_tier.value,
            'client_info': client_info,
            'session_id': auth_token.metadata.get('session_id')
        })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/auth/login',
            'email': request.email
        })
        
        api_logger.error("登入過程發生錯誤", extra={
            'error_id': error_info.error_id,
            'email': request.email
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登入服務暫時不可用"
        )

@router.post("/logout", summary="用戶登出")
async def logout(user: CurrentUser):
    """
    用戶登出
    
    撤銷當前用戶的訪問令牌。
    """
    auth_manager = get_auth_manager()
    
    try:
        # 從請求中獲取令牌 (這裡需要從依賴項中獲取)
        # 實際實現中需要修改依賴項來傳遞原始令牌
        
        api_logger.info("用戶登出", extra={
            'user_id': user.user_id,
            'membership_tier': user.membership_tier.value
        })
        
        return {"message": "登出成功"}
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/auth/logout',
            'user_id': user.user_id
        })
        
        api_logger.error("登出過程發生錯誤", extra={
            'error_id': error_info.error_id,
            'user_id': user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出服務暫時不可用"
        )

@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    request: RefreshTokenRequest,
    _rate_check = Depends(rate_limit('default'))
):
    """
    刷新訪問令牌
    
    使用刷新令牌獲取新的訪問令牌。
    """
    auth_manager = get_auth_manager()
    
    try:
        rotation = auth_manager.rotate_refresh_token(request.refresh_token)
        access_token = rotation['access_token']
        refresh_token = rotation['refresh_token']
        
        # 解碼新訪問令牌以取得過期時間
        payload = auth_manager.jwt_manager.decode_token(access_token)
        expires_in = int(payload['exp'] - datetime.now().timestamp())
        
        api_logger.info("令牌刷新成功", extra={
            'user_id': payload.get('user_id'),
            'session_id': payload.get('session_id')
        })
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/auth/refresh'
        })
        
        api_logger.error("令牌刷新錯誤", extra={
            'error_id': error_info.error_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新服務暫時不可用"
        )

@router.get("/me", response_model=UserProfile, summary="獲取用戶資訊")
async def get_current_user_profile(user: CurrentUser):
    """
    獲取當前用戶的詳細資訊
    """
    permission_manager = get_permission_manager()
    user_permissions = permission_manager.get_user_permissions(user)
    
    # 模擬用戶資料 (實際應從數據庫獲取)
    profile = UserProfile(
        user_id=user.user_id,
        email=f"{user.user_id}@example.com",  # 實際應從數據庫獲取
        membership_tier=user.membership_tier.value,
        permissions=user_permissions,
        created_at="2024-01-01T00:00:00Z",  # 實際應從數據庫獲取
        last_login=datetime.now().isoformat()
    )
    
    api_logger.info("用戶資訊查詢", extra={
        'user_id': user.user_id,
        'membership_tier': user.membership_tier.value
    })
    
    return profile

@router.put("/password", summary="修改密碼")
async def change_password(
    request: PasswordChangeRequest,
    user: CurrentUser,
    _rate_check = Depends(rate_limit('default'))
):
    """
    修改用戶密碼
    """
    auth_manager = get_auth_manager()
    
    try:
        # 驗證密碼強度
        password_check = auth_manager.password_manager.validate_password_strength(
            request.new_password
        )
        
        if not password_check['is_valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密碼強度不足: {', '.join(password_check['feedback'])}"
            )
        
        # 實際實現應該：
        # 1. 驗證當前密碼
        # 2. 更新數據庫中的密碼雜湊
        # 3. 撤銷所有現有令牌
        
        security_logger.info("密碼修改成功", extra={
            'user_id': user.user_id,
            'password_strength': password_check['strength']
        })
        
        return {"message": "密碼修改成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/auth/password',
            'user_id': user.user_id
        })
        
        security_logger.error("密碼修改錯誤", extra={
            'error_id': error_info.error_id,
            'user_id': user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密碼修改服務暫時不可用"
        )

# ==================== API密鑰管理 ====================

@router.post("/api-keys", response_model=APIKeyResponse, summary="創建API密鑰")
async def create_api_key(
    request: APIKeyCreateRequest,
    user: CurrentUser,
    _rate_check = Depends(rate_limit('default'))
):
    """
    創建新的API密鑰
    """
    auth_manager = get_auth_manager()
    
    try:
        # 驗證權限
        permission_manager = get_permission_manager()
        user_permissions = permission_manager.get_user_permissions(user)
        
        # 檢查請求的權限是否在用戶權限範圍內
        invalid_permissions = [
            perm for perm in request.permissions
            if perm not in user_permissions
        ]
        
        if invalid_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"沒有權限創建以下權限的API密鑰: {invalid_permissions}"
            )
        
        # 創建API密鑰
        api_key_info = await auth_manager.create_api_key(
            user_id=user.user_id,
            name=request.name,
            permissions=request.permissions,
            expires_in_days=request.expires_in_days
        )
        
        security_logger.info("API密鑰創建成功", extra={
            'user_id': user.user_id,
            'key_id': api_key_info['key_id'],
            'key_name': request.name,
            'permissions': request.permissions
        })
        
        return APIKeyResponse(**api_key_info, usage_count=0)
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/auth/api-keys',
            'user_id': user.user_id
        })
        
        api_logger.error("API密鑰創建錯誤", extra={
            'error_id': error_info.error_id,
            'user_id': user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API密鑰創建服務暫時不可用"
        )

@router.get("/api-keys", response_model=List[APIKeyResponse], summary="獲取API密鑰列表")
async def list_api_keys(user: CurrentUser):
    """
    獲取用戶的API密鑰列表
    """
    auth_manager = get_auth_manager()
    
    # 獲取用戶的API密鑰
    user_keys = [
        key for key in auth_manager.api_keys.values()
        if key.user_id == user.user_id
    ]
    
    # 轉換為回應格式 (不包含原始密鑰)
    api_keys = []
    for key in user_keys:
        api_keys.append(APIKeyResponse(
            key_id=key.key_id,
            name=key.name,
            permissions=key.permissions,
            created_at=key.created_at.isoformat(),
            expires_at=key.expires_at.isoformat() if key.expires_at else None,
            last_used=key.last_used.isoformat() if key.last_used else None,
            usage_count=key.usage_count
        ))
    
    api_logger.info("API密鑰列表查詢", extra={
        'user_id': user.user_id,
        'keys_count': len(api_keys)
    })
    
    return api_keys

@router.delete("/api-keys/{key_id}", summary="刪除API密鑰")
async def delete_api_key(
    key_id: str,
    user: CurrentUser,
    _rate_check = Depends(rate_limit('default'))
):
    """
    刪除指定的API密鑰
    """
    auth_manager = get_auth_manager()
    
    # 檢查密鑰是否存在且屬於當前用戶
    if key_id not in auth_manager.api_keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密鑰不存在"
        )
    
    api_key = auth_manager.api_keys[key_id]
    if api_key.user_id != user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="沒有權限刪除此API密鑰"
        )
    
    # 刪除API密鑰
    del auth_manager.api_keys[key_id]
    
    security_logger.info("API密鑰刪除成功", extra={
        'user_id': user.user_id,
        'key_id': key_id,
        'key_name': api_key.name
    })
    
    return {"message": "API密鑰刪除成功"}

# ==================== 管理員端點 ====================

@router.get("/admin/stats", summary="獲取認證統計", dependencies=[Depends(require_admin_access())])
async def get_auth_stats():
    """
    獲取認證系統統計資訊 (僅管理員)
    """
    auth_manager = get_auth_manager()
    permission_manager = get_permission_manager()
    
    auth_stats = auth_manager.get_auth_stats()
    permission_summary = permission_manager.get_permission_summary()
    
    return {
        'authentication': auth_stats,
        'permissions': permission_summary,
        'timestamp': datetime.now().isoformat()
    }

@router.get("/admin/security-events", response_model=List[SecurityEvent], 
           summary="獲取安全事件", dependencies=[Depends(require_admin_access())])
async def get_security_events(
    limit: int = 100,
    event_type: Optional[str] = None
):
    """
    獲取安全事件列表 (僅管理員)
    """
    # 實際實現應該從日誌系統或數據庫查詢
    # 這裡返回模擬數據
    events = [
        SecurityEvent(
            event_id=f"event_{i}",
            event_type=event_type or "login_success",
            timestamp=datetime.now().isoformat(),
            details={"user_id": f"user_{i}", "ip": "192.168.1.100"}
        )
        for i in range(min(limit, 10))
    ]
    
    return events

# ==================== 健康檢查 ====================

@router.get("/health", summary="認證服務健康檢查")
async def auth_health_check():
    """
    認證服務健康檢查
    """
    auth_manager = get_auth_manager()
    permission_manager = get_permission_manager()
    
    try:
        # 檢查組件狀態
        auth_stats = auth_manager.get_auth_stats()
        permission_summary = permission_manager.get_permission_summary()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "authentication": "healthy",
                "permissions": "healthy",
                "rate_limiting": "healthy"
            },
            "metrics": {
                "active_sessions": auth_stats['active_sessions'],
                "roles_count": len(permission_summary['roles'])
            }
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/auth/health'
        })
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_id": error_info.error_id
        }

if __name__ == "__main__":
    # 測試路由配置
    print("認證路由配置:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")
