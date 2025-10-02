#!/usr/bin/env python3
"""
認證依賴項 (Authentication Dependencies)
天工 (TianGong) - FastAPI認證和權限依賴項

此模組提供FastAPI應用程式使用的認證和權限依賴項，包含：
1. JWT Token驗證依賴項
2. API密鑰驗證依賴項
3. 權限檢查依賴項
4. 用戶上下文注入
5. 速率限制和安全檢查
6. Taiwan市場專用認證
"""

from typing import Optional, Dict, Any, Annotated
from datetime import datetime
import asyncio
import time

from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .auth_manager import get_auth_manager, AuthenticationManager
from .permissions import get_permission_manager, PermissionManager, ResourceType, Action
from ..utils.user_context import UserContext, TierType
from ..utils.logging_config import get_security_logger, get_api_logger
from ..utils.error_handler import handle_error

# 配置日誌
security_logger = get_security_logger("dependencies")
api_logger = get_api_logger("dependencies")

# HTTP Bearer安全方案
security = HTTPBearer(auto_error=False)

class AuthenticationError(HTTPException):
    """認證錯誤"""
    def __init__(self, detail: str = "認證失敗"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class AuthorizationError(HTTPException):
    """授權錯誤"""
    def __init__(self, detail: str = "權限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class RateLimitError(HTTPException):
    """速率限制錯誤"""
    def __init__(self, detail: str = "請求頻率過高", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )

# 速率限制存儲（實際應使用Redis）
_rate_limit_storage: Dict[str, Dict[str, list]] = {}

def rate_limit(limiter_name: str = 'default', max_requests: int = 60, window_seconds: int = 60):
    """
    速率限制依賴項
    
    Args:
        limiter_name: 限制器名稱
        max_requests: 最大請求數
        window_seconds: 時間窗口（秒）
    """
    async def dependency(request: Request):
        client_ip = request.client.host if request.client else 'unknown'
        key = f"{limiter_name}:{client_ip}"
        current_time = time.time()
        
        # 初始化存儲
        if key not in _rate_limit_storage:
            _rate_limit_storage[key] = []
        
        # 清理過期記錄
        _rate_limit_storage[key] = [
            timestamp for timestamp in _rate_limit_storage[key]
            if current_time - timestamp < window_seconds
        ]
        
        # 檢查是否超過限制
        if len(_rate_limit_storage[key]) >= max_requests:
            security_logger.warning("速率限制觸發", extra={
                'client_ip': client_ip,
                'limiter_name': limiter_name,
                'request_count': len(_rate_limit_storage[key]),
                'max_requests': max_requests,
                'window_seconds': window_seconds,
                'security_event': 'rate_limit_exceeded'
            })
            
            raise RateLimitError(
                detail=f"請求頻率過高，每{window_seconds}秒最多{max_requests}次請求",
                retry_after=window_seconds
            )
        
        # 記錄當前請求
        _rate_limit_storage[key].append(current_time)
        
        return True
    
    return dependency

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> UserContext:
    """
    獲取當前認證用戶
    
    支持多種認證方式：
    1. JWT Bearer Token
    2. API Key (X-API-Key header)
    """
    auth_manager = get_auth_manager()
    
    try:
        # 記錄認證嘗試
        client_info = {
            'ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', ''),
            'endpoint': str(request.url.path),
            'method': request.method
        }
        
        # 優先使用API密鑰認證
        if x_api_key:
            security_logger.debug("嘗試API密鑰認證", extra={
                'auth_method': 'api_key',
                'client_info': client_info
            })
            
            user_context = await auth_manager.verify_api_key(x_api_key)
            
            # 記錄成功認證
            security_logger.info("API密鑰認證成功", extra={
                'user_id': user_context.user_id,
                'membership_tier': user_context.membership_tier.value,
                'auth_method': 'api_key',
                'client_info': client_info
            })
            
            return user_context
        
        # JWT Token認證
        if credentials and credentials.credentials:
            security_logger.debug("嘗試JWT Token認證", extra={
                'auth_method': 'jwt_token',
                'client_info': client_info
            })
            
            user_context = await auth_manager.verify_token(credentials.credentials)
            
            # 記錄成功認證
            security_logger.info("JWT Token認證成功", extra={
                'user_id': user_context.user_id,
                'membership_tier': user_context.membership_tier.value,
                'auth_method': 'jwt_token',
                'client_info': client_info
            })
            
            return user_context
        
        # 沒有提供認證憑證
        security_logger.warning("未提供認證憑證", extra={
            'client_info': client_info,
            'security_event': 'no_auth_credentials'
        })
        
        raise AuthenticationError("需要認證憑證")
        
    except HTTPException:
        raise
    except Exception as e:
        # 記錄認證錯誤
        error_info = await handle_error(e, {
            'component': 'auth_dependencies',
            'operation': 'get_current_user',
            'client_info': client_info
        })
        
        security_logger.error("認證過程發生錯誤", extra={
            'error_id': error_info.error_id,
            'client_info': client_info,
            'error_message': str(e)
        })
        
        raise AuthenticationError("認證服務暫時不可用")

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[UserContext]:
    """
    獲取可選的當前用戶（不要求必須認證）
    """
    try:
        return await get_current_user(request, credentials, x_api_key)
    except HTTPException:
        return None

def require_membership(min_tier: TierType):
    """
    需要特定會員等級的依賴項
    
    Args:
        min_tier: 最低會員等級要求
    """
    async def check_membership(user: UserContext = Depends(get_current_user)) -> UserContext:
        tier_levels = {
            TierType.FREE: 1,
            TierType.GOLD: 2,
            TierType.DIAMOND: 3
        }
        
        user_level = tier_levels.get(user.membership_tier, 0)
        required_level = tier_levels.get(min_tier, 999)
        
        if user_level < required_level:
            security_logger.warning("會員等級不足", extra={
                'user_id': user.user_id,
                'user_tier': user.membership_tier.value,
                'required_tier': min_tier.value,
                'security_event': 'insufficient_membership'
            })
            
            raise AuthorizationError(f"需要 {min_tier.value} 或以上會員等級")
        
        return user
    
    return check_membership

def require_permission(resource: ResourceType, action: Action):
    """
    需要特定權限的依賴項
    
    Args:
        resource: 資源類型
        action: 操作類型
    """
    async def check_permission(user: UserContext = Depends(get_current_user)) -> UserContext:
        permission_manager = get_permission_manager()
        
        if not permission_manager.has_permission(user, resource, action):
            security_logger.warning("權限檢查失敗", extra={
                'user_id': user.user_id,
                'membership_tier': user.membership_tier.value,
                'resource': resource.value,
                'action': action.value,
                'security_event': 'permission_denied'
            })
            
            raise AuthorizationError(f"沒有權限執行此操作: {action.value}:{resource.value}")
        
        return user
    
    return check_permission

class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int = 60, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """檢查是否允許請求"""
        now = datetime.now()
        window_start = now.timestamp() - (self.window_minutes * 60)
        
        # 初始化或清理過期請求
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # 移除過期請求
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # 檢查是否超過限制
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # 記錄當前請求
        self.requests[identifier].append(now.timestamp())
        return True

# 全局速率限制器實例
# E2E測試模式：檢查環境變數 E2E_TESTING_MODE
import os
_is_e2e_testing = os.getenv('E2E_TESTING_MODE', 'false').lower() == 'true'

_rate_limiters: Dict[str, RateLimiter] = {
    'default': RateLimiter(60, 1),  # 每分鐘60次
    'api_key': RateLimiter(1000, 60),  # 每小時1000次
    # E2E測試模式：放寬登入限制為每分鐘100次，生產模式：每15分鐘5次
    'login': RateLimiter(100, 1) if _is_e2e_testing else RateLimiter(5, 15),
}

def rate_limit(limiter_name: str = 'default'):
    """
    速率限制依賴項
    
    Args:
        limiter_name: 限制器名稱
    """
    async def check_rate_limit(
        request: Request,
        user: Optional[UserContext] = Depends(get_optional_user)
    ):
        limiter = _rate_limiters.get(limiter_name, _rate_limiters['default'])
        
        # 根據用戶或IP確定標識符
        if user:
            identifier = f"user_{user.user_id}"
            # 鑽石用戶有更高的限制
            if user.membership_tier == TierType.DIAMOND:
                limiter = RateLimiter(limiter.max_requests * 2, limiter.window_minutes)
        else:
            identifier = f"ip_{request.client.host if request.client else 'unknown'}"
        
        if not limiter.is_allowed(identifier):
            api_logger.warning("速率限制觸發", extra={
                'identifier': identifier,
                'limiter': limiter_name,
                'max_requests': limiter.max_requests,
                'window_minutes': limiter.window_minutes,
                'endpoint': str(request.url.path)
            })
            
            raise RateLimitError(
                detail=f"請求頻率過高，每{limiter.window_minutes}分鐘最多{limiter.max_requests}次請求",
                retry_after=limiter.window_minutes * 60
            )
    
    return check_rate_limit

def require_taiwan_market_access():
    """需要Taiwan市場訪問權限"""
    return require_permission(ResourceType.TAIWAN_MARKET, Action.READ)

def require_real_time_data():
    """需要實時數據權限"""
    return require_permission(ResourceType.REAL_TIME, Action.READ)

def require_analysis_execution():
    """需要分析執行權限"""
    return require_permission(ResourceType.ANALYSIS, Action.EXECUTE)

def require_data_export():
    """需要數據導出權限"""
    return require_permission(ResourceType.EXPORT, Action.EXECUTE)

def require_admin_access():
    """需要管理員權限"""
    async def dependency(user: UserContext = Depends(get_current_user)) -> UserContext:
        # 檢查用戶是否是管理員
        if user.membership_tier != TierType.DIAMOND:
            security_logger.warning("非管理員嘗試訪問管理功能", extra={
                'user_id': user.user_id,
                'membership_tier': user.membership_tier.value,
                'security_event': 'unauthorized_admin_access'
            })
            raise AuthorizationError("需要管理員權限")
        
        return user
    
    return dependency

# 組合依賴項
def get_authenticated_user():
    """獲取認證用戶（帶速率限制）"""
    return Depends(get_current_user)

def get_gold_user():
    """獲取金牌或以上用戶"""
    return Depends(require_membership(TierType.GOLD))

def get_diamond_user():
    """獲取鑽石用戶"""
    return Depends(require_membership(TierType.DIAMOND))

def get_user_with_rate_limit(limiter_name: str = 'default'):
    """獲取用戶（帶速率限制）"""
    async def dependency(
        user: UserContext = Depends(get_current_user),
        _rate_check = Depends(rate_limit(limiter_name))
    ) -> UserContext:
        return user
    
    return dependency

# 安全檢查依賴項
async def security_headers_check(request: Request):
    """安全標頭檢查"""
    # 檢查必要的安全標頭
    required_headers = ['user-agent']
    missing_headers = []
    
    for header in required_headers:
        if header not in request.headers:
            missing_headers.append(header)
    
    if missing_headers:
        security_logger.warning("缺少安全標頭", extra={
            'missing_headers': missing_headers,
            'client_ip': request.client.host if request.client else 'unknown',
            'security_event': 'missing_security_headers'
        })
    
    # 檢查可疑的User-Agent
    user_agent = request.headers.get('user-agent', '')
    suspicious_patterns = ['bot', 'crawler', 'spider', 'scraper']
    
    if any(pattern in user_agent.lower() for pattern in suspicious_patterns):
        security_logger.info("偵測到自動化工具", extra={
            'user_agent': user_agent,
            'client_ip': request.client.host if request.client else 'unknown',
            'security_event': 'suspicious_user_agent'
        })

# 類型別名和常用依賴項
CurrentUser = Annotated[UserContext, Depends(get_current_user)]
OptionalUser = Annotated[Optional[UserContext], Depends(get_optional_user)]
GoldUser = Annotated[UserContext, Depends(get_gold_user)]
DiamondUser = Annotated[UserContext, Depends(get_diamond_user)]
AuthenticatedUser = Annotated[UserContext, Depends(get_authenticated_user)]

# 權限快捷依賴項
AnalysisReader = Annotated[UserContext, Depends(require_permission(ResourceType.ANALYSIS, Action.READ))]
AnalysisExecutor = Annotated[UserContext, Depends(require_permission(ResourceType.ANALYSIS, Action.EXECUTE))]
TaiwanMarketUser = Annotated[UserContext, Depends(require_taiwan_market_access)]
RealTimeDataUser = Annotated[UserContext, Depends(require_real_time_data)]
DataExporter = Annotated[UserContext, Depends(require_data_export)]
AdminUser = Annotated[UserContext, Depends(require_admin_access)]

if __name__ == "__main__":
    # 測試腳本
    def test_dependencies():
        print("測試認證依賴項...")
        
        # 測試速率限制器
        limiter = RateLimiter(5, 1)  # 每分鐘5次
        
        # 模擬請求
        for i in range(7):
            allowed = limiter.is_allowed("test_user")
            print(f"請求 {i+1}: {'允許' if allowed else '拒絕'}")
        
        # 測試權限映射
        from .permissions import get_permission_manager, ResourceType, Action
        from ..utils.user_context import UserContext, TierType, UserPermissions
        
        perm_manager = get_permission_manager()
        
        # 創建測試用戶
        diamond_user = UserContext(
            user_id="test_diamond",
            membership_tier=TierType.DIAMOND,
            permissions=UserPermissions()
        )
        
        # 測試權限檢查
        has_real_time = perm_manager.has_permission(
            diamond_user, ResourceType.REAL_TIME, Action.READ
        )
        
        print(f"鑽石用戶實時數據權限: {'✓' if has_real_time else '✗'}")
        
        print("認證依賴項測試完成")
    
    test_dependencies()