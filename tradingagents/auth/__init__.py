#!/usr/bin/env python3
"""
認證和授權系統模組
天工 (TianGong) - 企業級認證授權解決方案

此模組提供完整的用戶認證、授權和會話管理功能。

主要組件：
- AuthenticationManager: 用戶認證和JWT管理
- PermissionManager: 細粒度權限控制
- Dependencies: FastAPI依賴項和中間件
- Routes: 認證相關API端點

使用示例：
    from tradingagents.auth import get_auth_manager, get_permission_manager
    from tradingagents.auth.dependencies import CurrentUser, DiamondUser
    from tradingagents.auth.permissions import require_permission, ResourceType, Action
"""

from .auth_manager import (
    get_auth_manager,
    AuthenticationManager,
    AuthToken,
    UserSession,
    APIKey,
    PasswordManager,
    JWTManager
)

from .permissions import (
    get_permission_manager,
    PermissionManager,
    Permission,
    Role,
    ResourceType,
    Action,
    PermissionLevel,
    require_permission
)

from .dependencies import (
    get_current_user,
    get_optional_user,
    require_membership,
    require_permission as require_perm_dep,
    rate_limit,
    # 類型別名
    CurrentUser,
    OptionalUser,
    GoldUser,
    DiamondUser,
    AuthenticatedUser,
    AnalysisReader,
    AnalysisExecutor,
    TaiwanMarketUser,
    RealTimeDataUser,
    DataExporter,
    AdminUser,
    # 便利依賴項
    get_authenticated_user,
    get_gold_user,
    get_diamond_user,
    require_taiwan_market_access,
    require_real_time_data,
    require_analysis_execution,
    require_data_export,
    require_admin_access
)

from .routes import router as auth_router

__all__ = [
    # 管理器
    'get_auth_manager',
    'AuthenticationManager',
    'get_permission_manager', 
    'PermissionManager',
    
    # 認證相關類
    'AuthToken',
    'UserSession',
    'APIKey',
    'PasswordManager',
    'JWTManager',
    
    # 權限相關類
    'Permission',
    'Role',
    'ResourceType',
    'Action',
    'PermissionLevel',
    'require_permission',
    
    # 依賴項
    'get_current_user',
    'get_optional_user',
    'require_membership',
    'require_perm_dep',
    'rate_limit',
    
    # 類型別名
    'CurrentUser',
    'OptionalUser',
    'GoldUser',
    'DiamondUser',
    'AuthenticatedUser',
    'AnalysisReader',
    'AnalysisExecutor',
    'TaiwanMarketUser',
    'RealTimeDataUser',
    'DataExporter',
    'AdminUser',
    
    # 便利依賴項
    'get_authenticated_user',
    'get_gold_user',
    'get_diamond_user',
    'require_taiwan_market_access',
    'require_real_time_data',
    'require_analysis_execution',
    'require_data_export',
    'require_admin_access',
    
    # 路由
    'auth_router'
]

# 版本資訊
__version__ = "1.0.0"
__author__ = "天工 (TianGong) Team"
__description__ = "TradingAgents認證授權系統"

# 快速配置函數
def setup_auth_system(app, config=None):
    """
    快速設置認證系統
    
    Args:
        app: FastAPI應用實例
        config: 認證配置字典
    """
    # 初始化管理器
    auth_manager = get_auth_manager(config)
    permission_manager = get_permission_manager(config)
    
    # 註冊路由
    app.include_router(auth_router)
    
    return {
        'auth_manager': auth_manager,
        'permission_manager': permission_manager
    }

# 默認配置
DEFAULT_AUTH_CONFIG = {
    'jwt_secret_key': 'your-secret-key-change-in-production',
    'max_login_attempts': 5,
    'lockout_minutes': 30,
    'cache_ttl_minutes': 15,
    'enable_api_keys': True,
    'enable_rate_limiting': True
}

if __name__ == "__main__":
    print("TradingAgents認證授權系統")
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    print(f"描述: {__description__}")
    print("\n可用組件:")
    for component in __all__:
        print(f"  - {component}")