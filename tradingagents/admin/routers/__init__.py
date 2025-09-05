"""
Admin 路由器模組

提供管理員功能的 API 路由器
"""

from .auth_router import router as auth_router
from .config_router import router as config_router
from .user_management import router as user_management_router
from .system_monitor import router as system_monitor_router

__all__ = ["auth_router", "config_router", "user_management_router", "system_monitor_router"]