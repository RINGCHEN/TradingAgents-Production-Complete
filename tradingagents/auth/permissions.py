#!/usr/bin/env python3
"""
權限控制系統 (Permission Control System)
天工 (TianGong) - 細粒度權限管理和訪問控制

此模組提供靈活的權限控制機制，包含：
1. 基於角色的訪問控制 (RBAC)
2. 資源級權限檢查
3. 動態權限評估
4. 權限繼承和組合
5. Taiwan市場特殊權限
6. API端點權限映射
"""

from typing import Dict, List, Set, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import functools
from datetime import datetime, timedelta
import re

from fastapi import HTTPException, status, Depends, Request
from ..utils.user_context import UserContext, TierType
from ..utils.logging_config import get_security_logger

# 配置日誌
security_logger = get_security_logger(__name__)

class ResourceType(Enum):
    """資源類型"""
    ANALYSIS = "analysis"
    DATA = "data"
    PROFILE = "profile"
    SYSTEM = "system"
    API = "api"
    EXPORT = "export"
    TAIWAN_MARKET = "taiwan_market"
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    ALERTS = "alerts"
    WATCHLIST = "watchlist"

class Action(Enum):
    """操作類型"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    EXECUTE = "execute"
    ADMIN = "admin"
    EXPORT = "export"
    SHARE = "share"

class PermissionLevel(Enum):
    """權限級別"""
    DENIED = 0      # 拒絕
    BASIC = 1       # 基礎權限
    STANDARD = 2    # 標準權限
    ADVANCED = 3    # 高級權限
    PREMIUM = 4     # 付費權限
    ADMIN = 5       # 管理員權限

@dataclass
class Permission:
    """權限定義"""
    resource: ResourceType
    action: Action
    level: PermissionLevel = PermissionLevel.BASIC
    conditions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return f"{self.action.value}:{self.resource.value}"
    
    def matches(self, required_resource: ResourceType, required_action: Action) -> bool:
        """檢查權限是否匹配"""
        return self.resource == required_resource and self.action == required_action

@dataclass
class Role:
    """角色定義"""
    name: str
    permissions: List[Permission] = field(default_factory=list)
    inherits_from: List[str] = field(default_factory=list)
    description: str = ""
    is_active: bool = True
    
    def has_permission(self, resource: ResourceType, action: Action) -> bool:
        """檢查角色是否擁有特定權限"""
        return any(
            perm.matches(resource, action) 
            for perm in self.permissions
        )

class PermissionManager:
    """權限管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 預定義角色
        self.roles: Dict[str, Role] = {}
        self._setup_default_roles()
        
        # 權限緩存
        self.permission_cache: Dict[str, Dict[str, bool]] = {}
        self.cache_ttl = timedelta(minutes=self.config.get('cache_ttl_minutes', 15))
        
        # 會員等級權限映射
        self.tier_permissions = self._setup_tier_permissions()
        
        security_logger.info("權限管理器初始化完成", extra={
            'roles_count': len(self.roles),
            'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60
        })
    
    def _setup_default_roles(self):
        """設置默認角色"""
        # 免費用戶角色
        free_role = Role(
            name="free_user",
            description="免費用戶",
            permissions=[
                Permission(ResourceType.PROFILE, Action.READ),
                Permission(ResourceType.PROFILE, Action.WRITE),
                Permission(ResourceType.ANALYSIS, Action.READ, PermissionLevel.BASIC),
                Permission(ResourceType.DATA, Action.READ, PermissionLevel.BASIC),
            ]
        )
        
        # 金牌用戶角色
        gold_role = Role(
            name="gold_user",
            description="金牌用戶",
            inherits_from=["free_user"],
            permissions=[
                Permission(ResourceType.ANALYSIS, Action.READ, PermissionLevel.STANDARD),
                Permission(ResourceType.ANALYSIS, Action.EXECUTE, PermissionLevel.STANDARD),
                Permission(ResourceType.DATA, Action.READ, PermissionLevel.STANDARD),
                Permission(ResourceType.HISTORICAL, Action.READ, PermissionLevel.STANDARD),
                Permission(ResourceType.WATCHLIST, Action.READ),
                Permission(ResourceType.WATCHLIST, Action.WRITE),
                Permission(ResourceType.ALERTS, Action.READ),
                Permission(ResourceType.ALERTS, Action.WRITE),
            ]
        )
        
        # 鑽石用戶角色
        diamond_role = Role(
            name="diamond_user",
            description="鑽石用戶",
            inherits_from=["gold_user"],
            permissions=[
                Permission(ResourceType.ANALYSIS, Action.READ, PermissionLevel.ADVANCED),
                Permission(ResourceType.ANALYSIS, Action.EXECUTE, PermissionLevel.ADVANCED),
                Permission(ResourceType.DATA, Action.READ, PermissionLevel.ADVANCED),
                Permission(ResourceType.REAL_TIME, Action.READ, PermissionLevel.PREMIUM),
                Permission(ResourceType.TAIWAN_MARKET, Action.READ, PermissionLevel.PREMIUM),
                Permission(ResourceType.EXPORT, Action.EXECUTE, PermissionLevel.PREMIUM),
                Permission(ResourceType.SYSTEM, Action.READ, PermissionLevel.BASIC),
                Permission(ResourceType.API, Action.READ, PermissionLevel.PREMIUM),
            ]
        )
        
        # 管理員角色
        admin_role = Role(
            name="admin",
            description="系統管理員",
            permissions=[
                Permission(ResourceType.SYSTEM, Action.ADMIN, PermissionLevel.ADMIN),
                Permission(ResourceType.API, Action.ADMIN, PermissionLevel.ADMIN),
                Permission(ResourceType.DATA, Action.ADMIN, PermissionLevel.ADMIN),
                Permission(ResourceType.ANALYSIS, Action.ADMIN, PermissionLevel.ADMIN),
            ]
        )
        
        # 添加角色到管理器
        for role in [free_role, gold_role, diamond_role, admin_role]:
            self.roles[role.name] = role
    
    def _setup_tier_permissions(self) -> Dict[TierType, List[str]]:
        """設置會員等級權限映射"""
        return {
            TierType.FREE: ["free_user"],
            TierType.GOLD: ["gold_user"],
            TierType.DIAMOND: ["diamond_user"]
        }
    
    def get_user_roles(self, user_context: UserContext) -> List[str]:
        """獲取用戶角色列表"""
        roles = self.tier_permissions.get(user_context.membership_tier, ["free_user"])
        
        # 如果有自定義角色，也包含進來
        if hasattr(user_context, 'custom_roles'):
            roles.extend(user_context.custom_roles)
        
        return roles
    
    def has_permission(
        self,
        user_context: UserContext,
        resource: ResourceType,
        action: Action,
        resource_id: Optional[str] = None
    ) -> bool:
        """檢查用戶是否擁有特定權限"""
        # 生成緩存鍵
        cache_key = f"{user_context.user_id}:{resource.value}:{action.value}"
        if resource_id:
            cache_key += f":{resource_id}"
        
        # 檢查緩存
        if cache_key in self.permission_cache:
            cached_result = self.permission_cache[cache_key]
            if cached_result.get('expires_at', datetime.min) > datetime.now():
                return cached_result['has_permission']
        
        # 計算權限
        has_perm = self._calculate_permission(user_context, resource, action, resource_id)
        
        # 緩存結果
        self.permission_cache[cache_key] = {
            'has_permission': has_perm,
            'expires_at': datetime.now() + self.cache_ttl
        }
        
        return has_perm
    
    def _calculate_permission(
        self,
        user_context: UserContext,
        resource: ResourceType,
        action: Action,
        resource_id: Optional[str] = None
    ) -> bool:
        """計算用戶權限"""
        # 檢查7天試用期
        if user_context.membership_tier == TierType.FREE and \
           (datetime.now() - user_context.created_at) < timedelta(days=7):
            trial_role = self.roles.get("diamond_user")
            if trial_role:
                # 檢查試用期用戶是否擁有鑽石會員的權限
                if self._check_role_permission(trial_role, resource, action) or \
                   self._check_inherited_permissions(trial_role, resource, action):
                    return True

        user_roles = self.get_user_roles(user_context)
        
        # 檢查每個角色的權限
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if not role or not role.is_active:
                continue
            
            # 檢查直接權限
            if self._check_role_permission(role, resource, action):
                return True
            
            # 檢查繼承權限
            if self._check_inherited_permissions(role, resource, action):
                return True
        
        # 檢查特殊條件權限
        if self._check_conditional_permissions(user_context, resource, action, resource_id):
            return True
        
        return False
    
    def _check_role_permission(self, role: Role, resource: ResourceType, action: Action) -> bool:
        """檢查角色直接權限"""
        return any(
            perm.matches(resource, action)
            for perm in role.permissions
        )
    
    def _check_inherited_permissions(self, role: Role, resource: ResourceType, action: Action) -> bool:
        """檢查繼承權限"""
        for parent_role_name in role.inherits_from:
            parent_role = self.roles.get(parent_role_name)
            if parent_role and parent_role.is_active:
                if self._check_role_permission(parent_role, resource, action):
                    return True
                # 遞歸檢查父角色的繼承
                if self._check_inherited_permissions(parent_role, resource, action):
                    return True
        
        return False
    
    def _check_conditional_permissions(
        self,
        user_context: UserContext,
        resource: ResourceType,
        action: Action,
        resource_id: Optional[str] = None
    ) -> bool:
        """檢查條件權限"""
        # 資源擁有者權限
        if resource_id and self._is_resource_owner(user_context.user_id, resource_id):
            return action in [Action.READ, Action.WRITE, Action.DELETE]
        
        # Taiwan市場特殊權限檢查
        if resource == ResourceType.TAIWAN_MARKET:
            return self._check_taiwan_market_permission(user_context)
        
        # 時間限制權限
        if resource == ResourceType.REAL_TIME:
            return self._check_time_based_permission(user_context)
        
        return False
    
    def _is_resource_owner(self, user_id: str, resource_id: str) -> bool:
        """檢查是否為資源擁有者"""
        # 實際實現應該查詢數據庫
        # 這裡是簡化的實現
        return resource_id.startswith(f"user_{user_id}_")
    
    def _check_taiwan_market_permission(self, user_context: UserContext) -> bool:
        """檢查Taiwan市場權限"""
        # 檢查用戶是否位於Taiwan或有特殊權限
        return user_context.membership_tier in [TierType.GOLD, TierType.DIAMOND]
    
    def _check_time_based_permission(self, user_context: UserContext) -> bool:
        """檢查時間限制權限"""
        # 例如：只有在台股交易時間才能訪問實時數據
        current_hour = datetime.now().hour
        trading_hours = 9 <= current_hour <= 13  # 台股交易時間簡化版
        
        return (
            user_context.membership_tier == TierType.DIAMOND or
            (user_context.membership_tier == TierType.GOLD and trading_hours)
        )
    
    def require_permission(
        self,
        resource: ResourceType,
        action: Action,
        resource_id_param: Optional[str] = None
    ):
        """權限裝飾器"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # 從參數中找到用戶上下文
                user_context = None
                resource_id = None
                
                # 檢查函數參數
                for arg in args:
                    if isinstance(arg, UserContext):
                        user_context = arg
                        break
                
                # 檢查關鍵字參數
                if not user_context:
                    user_context = kwargs.get('user_context')
                
                # 獲取資源ID
                if resource_id_param:
                    resource_id = kwargs.get(resource_id_param)
                
                if not user_context:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="需要用戶認證"
                    )
                
                # 檢查權限
                if not self.has_permission(user_context, resource, action, resource_id):
                    security_logger.warning("權限檢查失敗", extra={
                        'user_id': user_context.user_id,
                        'membership_tier': user_context.membership_tier.value,
                        'resource': resource.value,
                        'action': action.value,
                        'resource_id': resource_id,
                        'security_event': 'permission_denied'
                    })
                    
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"沒有權限執行此操作: {action.value}:{resource.value}"
                    )
                
                # 記錄權限檢查成功
                security_logger.debug("權限檢查通過", extra={
                    'user_id': user_context.user_id,
                    'resource': resource.value,
                    'action': action.value,
                    'resource_id': resource_id
                })
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get_user_permissions(self, user_context: UserContext) -> List[str]:
        """獲取用戶所有權限列表"""
        permissions = set()
        user_roles = self.get_user_roles(user_context)
        
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and role.is_active:
                # 添加直接權限
                for perm in role.permissions:
                    permissions.add(str(perm))
                
                # 添加繼承權限
                inherited_perms = self._get_inherited_permissions(role)
                permissions.update(inherited_perms)
        
        return list(permissions)
    
    def _get_inherited_permissions(self, role: Role) -> Set[str]:
        """獲取繼承的權限"""
        permissions = set()
        
        for parent_role_name in role.inherits_from:
            parent_role = self.roles.get(parent_role_name)
            if parent_role and parent_role.is_active:
                for perm in parent_role.permissions:
                    permissions.add(str(perm))
                
                # 遞歸獲取父角色的繼承權限
                inherited = self._get_inherited_permissions(parent_role)
                permissions.update(inherited)
        
        return permissions
    
    def add_role(self, role: Role) -> bool:
        """添加新角色"""
        try:
            self.roles[role.name] = role
            
            security_logger.info(f"角色添加成功: {role.name}", extra=    {
                'role_name': role.name,
                'permissions_count': len(role.permissions),
                'inherits_from': role.inherits_from
            })
            
            # 清除相關緩存
            self._clear_permission_cache()
            
            return True
        except Exception as e:
            security_logger.error(f"角色添加失敗: {str(e)}")
            return False
    
    def remove_role(self, role_name: str) -> bool:
        """移除角色"""
        try:
            if role_name in self.roles:
                del self.roles[role_name]
                
                security_logger.info(f"角色移除成功: {role_name}")
                
                # 清除相關緩存
                self._clear_permission_cache()
                
                return True
            return False
        except Exception as e:
            security_logger.error(f"角色移除失敗: {str(e)}")
            return False
    
    def _clear_permission_cache(self):
        """清除權限緩存"""
        self.permission_cache.clear()
        security_logger.debug("權限緩存已清除")
    
    def get_permission_summary(self) -> Dict[str, Any]:
        """獲取權限系統概要"""
        return {
            'roles': {
                name: {
                    'description': role.description,
                    'permissions_count': len(role.permissions),
                    'inherits_from': role.inherits_from,
                    'is_active': role.is_active
                }
                for name, role in self.roles.items()
            },
            'cache_stats': {
                'cached_permissions': len(self.permission_cache),
                'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60
            },
            'tier_mappings': {
                tier.value: roles for tier, roles in self.tier_permissions.items()
            }
        }

# 全局權限管理器實例
_global_permission_manager: Optional[PermissionManager] = None

def get_permission_manager(config: Optional[Dict[str, Any]] = None) -> PermissionManager:
    """獲取全局權限管理器實例"""
    global _global_permission_manager
    
    if _global_permission_manager is None:
        _global_permission_manager = PermissionManager(config)
    
    return _global_permission_manager

# 便利裝飾器
def require_permission(resource: ResourceType, action: Action, resource_id_param: Optional[str] = None):
    """權限檢查裝飾器"""
    permission_manager = get_permission_manager()
    return permission_manager.require_permission(resource, action, resource_id_param)

# 常用權限檢查裝飾器
def require_read_analysis(func):
    """需要分析讀取權限"""
    return require_permission(ResourceType.ANALYSIS, Action.READ)(func)

def require_execute_analysis(func):
    """需要分析執行權限"""
    return require_permission(ResourceType.ANALYSIS, Action.EXECUTE)(func)

def require_taiwan_market_access(func):
    """需要Taiwan市場訪問權限"""
    return require_permission(ResourceType.TAIWAN_MARKET, Action.READ)(func)

def require_real_time_data(func):
    """需要實時數據權限"""
    return require_permission(ResourceType.REAL_TIME, Action.READ)(func)

def require_admin_access(func):
    """需要管理員權限"""
    return require_permission(ResourceType.SYSTEM, Action.ADMIN)(func)

# 全局權限管理器實例
_global_permission_manager: Optional[PermissionManager] = None

def get_permission_manager(config: Optional[Dict[str, Any]] = None) -> PermissionManager:
    """獲取全局權限管理器實例"""
    global _global_permission_manager
    
    if _global_permission_manager is None:
        _global_permission_manager = PermissionManager(config)
    
    return _global_permission_manager

if __name__ == "__main__":
    # 測試腳本
    def test_permission_system():
        print("測試權限系統...")
        
        # 創建權限管理器
        perm_manager = get_permission_manager()
        
        # 創建測試用戶
        from ..utils.user_context import UserContext, TierType, UserPermissions
        
        free_user = UserContext(
            user_id="free_user_123",
            membership_tier=TierType.FREE,
            permissions=UserPermissions()
        )
        
        diamond_user = UserContext(
            user_id="diamond_user_456",
            membership_tier=TierType.DIAMOND,
            permissions=UserPermissions()
        )
        
        # 測試權限檢查
        test_cases = [
            (free_user, ResourceType.ANALYSIS, Action.READ, "免費用戶讀取分析"),
            (free_user, ResourceType.REAL_TIME, Action.READ, "免費用戶讀取實時數據"),
            (diamond_user, ResourceType.REAL_TIME, Action.READ, "鑽石用戶讀取實時數據"),
            (diamond_user, ResourceType.EXPORT, Action.EXECUTE, "鑽石用戶導出數據"),
        ]
        
        for user, resource, action, description in test_cases:
            has_perm = perm_manager.has_permission(user, resource, action)
            print(f"{description}: {'✓' if has_perm else '✗'}")
        
        # 獲取用戶權限列表
        free_permissions = perm_manager.get_user_permissions(free_user)
        diamond_permissions = perm_manager.get_user_permissions(diamond_user)
        
        print(f"\n免費用戶權限 ({len(free_permissions)}): {free_permissions[:3]}...")
        print(f"鑽石用戶權限 ({len(diamond_permissions)}): {diamond_permissions[:5]}...")
        
        # 獲取系統概要
        summary = perm_manager.get_permission_summary()
        print(f"\n權限系統概要:")
        print(f"角色數量: {len(summary['roles'])}")
        print(f"緩存權限數量: {summary['cache_stats']['cached_permissions']}")
        
        print("權限系統測試完成")
    
    test_permission_system()
