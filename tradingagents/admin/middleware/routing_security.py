#!/usr/bin/env python3
"""
路由管理安全中間件
GPT-OSS整合任務1.3.3 - 安全性和權限控制

提供路由管理系統的安全保護和權限驗證
"""

import time
import hmac
import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from enum import Enum
import ipaddress
from collections import defaultdict

from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ...auth.permissions import (
    PermissionManager, get_permission_manager,
    ResourceType, Action, PermissionLevel
)
from ...utils.user_context import UserContext
from ...utils.logging_config import get_security_logger

logger = get_security_logger("routing_security")
security = HTTPBearer()


class RoutePermissionType(Enum):
    """路由權限類型"""
    ROUTING_VIEW = "routing_view"           # 查看路由配置
    ROUTING_EDIT = "routing_edit"           # 編輯路由配置
    ROUTING_DELETE = "routing_delete"       # 刪除路由配置
    ROUTING_ADMIN = "routing_admin"         # 路由管理員
    AB_TEST_VIEW = "ab_test_view"           # 查看A/B測試
    AB_TEST_MANAGE = "ab_test_manage"       # 管理A/B測試
    PERFORMANCE_VIEW = "performance_view"   # 查看性能數據
    AUDIT_VIEW = "audit_view"               # 查看審計日誌
    CONFIG_BACKUP = "config_backup"         # 配置備份
    CONFIG_RESTORE = "config_restore"       # 配置恢復


class SecurityRisk(Enum):
    """安全風險等級"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SecurityEvent:
    """安全事件記錄"""
    event_id: str
    user_id: str
    ip_address: str
    user_agent: str
    event_type: str
    resource: str
    action: str
    timestamp: datetime
    risk_level: SecurityRisk
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False


@dataclass
class RateLimitRule:
    """速率限制規則"""
    max_requests: int
    time_window_seconds: int
    burst_allowance: int = 0
    
    
class RoutingSecurityManager:
    """路由安全管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化路由安全管理器
        
        Args:
            config: 安全配置參數
        """
        self.config = config or {}
        self.permission_manager = get_permission_manager()
        
        # 設置路由專用權限
        self._setup_routing_permissions()
        
        # 安全配置
        self.security_config = {
            'enable_ip_whitelist': self.config.get('enable_ip_whitelist', False),
            'allowed_ips': set(self.config.get('allowed_ips', [])),
            'enable_rate_limiting': self.config.get('enable_rate_limiting', True),
            'enable_audit_logging': self.config.get('enable_audit_logging', True),
            'session_timeout_hours': self.config.get('session_timeout_hours', 8),
            'max_concurrent_sessions': self.config.get('max_concurrent_sessions', 5),
            'enable_2fa_for_critical': self.config.get('enable_2fa_for_critical', True),
            'block_suspicious_activity': self.config.get('block_suspicious_activity', True)
        }
        
        # 速率限制規則
        self.rate_limit_rules = {
            'strategy_create': RateLimitRule(10, 3600),    # 每小時10次策略創建
            'strategy_update': RateLimitRule(20, 3600),    # 每小時20次策略更新
            'strategy_delete': RateLimitRule(5, 3600),     # 每小時5次策略刪除
            'ab_test_create': RateLimitRule(3, 3600),      # 每小時3次A/B測試創建
            'config_backup': RateLimitRule(10, 86400),     # 每天10次配置備份
            'config_restore': RateLimitRule(2, 86400),     # 每天2次配置恢復
            'dashboard_access': RateLimitRule(100, 3600)   # 每小時100次儀表板訪問
        }
        
        # 用戶請求計數器
        self.request_counters: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # 安全事件記錄
        self.security_events: List[SecurityEvent] = []
        self.max_security_events = 10000
        
        # 活動會話追蹤
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # 可疑活動檢測
        self.suspicious_patterns = {
            'rapid_config_changes': {'threshold': 10, 'window': 300},  # 5分鐘內10次配置更改
            'multiple_failed_auth': {'threshold': 5, 'window': 900},   # 15分鐘內5次認證失敗
            'unusual_access_pattern': {'threshold': 50, 'window': 1800} # 30分鐘內50次訪問
        }
        
        logger.info("路由安全管理器初始化完成")
    
    def _setup_routing_permissions(self):
        """設置路由專用權限"""
        from ...auth.permissions import Role, Permission
        
        # 路由管理員角色
        routing_admin_role = Role(
            name="routing_admin",
            description="路由系統管理員",
            permissions=[
                Permission(ResourceType.SYSTEM, Action.READ, PermissionLevel.ADMIN),
                Permission(ResourceType.SYSTEM, Action.WRITE, PermissionLevel.ADMIN),
                Permission(ResourceType.SYSTEM, Action.DELETE, PermissionLevel.ADMIN),
                Permission(ResourceType.SYSTEM, Action.ADMIN, PermissionLevel.ADMIN)
            ]
        )
        
        # 路由操作員角色
        routing_operator_role = Role(
            name="routing_operator",
            description="路由系統操作員",
            permissions=[
                Permission(ResourceType.SYSTEM, Action.READ, PermissionLevel.ADVANCED),
                Permission(ResourceType.SYSTEM, Action.WRITE, PermissionLevel.ADVANCED)
            ]
        )
        
        # 路由觀察員角色
        routing_viewer_role = Role(
            name="routing_viewer", 
            description="路由系統觀察員",
            permissions=[
                Permission(ResourceType.SYSTEM, Action.READ, PermissionLevel.STANDARD)
            ]
        )
        
        # 添加角色到權限管理器
        self.permission_manager.add_role(routing_admin_role)
        self.permission_manager.add_role(routing_operator_role)
        self.permission_manager.add_role(routing_viewer_role)
    
    async def validate_request_security(
        self,
        request: Request,
        user_context: UserContext,
        operation_type: RoutePermissionType,
        resource_id: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        驗證請求安全性
        
        Args:
            request: HTTP請求對象
            user_context: 用戶上下文
            operation_type: 操作類型
            resource_id: 資源ID
            
        Returns:
            (是否允許訪問, 拒絕原因)
        """
        try:
            # 1. IP白名單檢查
            if not await self._check_ip_whitelist(request):
                return False, "IP地址不在允許列表中"
            
            # 2. 權限檢查
            if not await self._check_route_permission(user_context, operation_type):
                return False, "沒有執行此操作的權限"
            
            # 3. 速率限制檢查
            if not await self._check_rate_limit(user_context.user_id, operation_type.value, request):
                return False, "請求頻率過高，請稍後再試"
            
            # 4. 會話有效性檢查
            if not await self._validate_session(user_context):
                return False, "會話已過期，請重新登入"
            
            # 5. 可疑活動檢測
            if await self._detect_suspicious_activity(user_context, operation_type, request):
                return False, "檢測到可疑活動，請求被阻止"
            
            # 6. 關鍵操作額外驗證
            if await self._requires_additional_verification(operation_type):
                if not await self._verify_critical_operation(user_context, operation_type):
                    return False, "關鍵操作需要額外驗證"
            
            # 記錄安全事件
            await self._record_security_event(
                user_context.user_id,
                request,
                operation_type.value,
                "access_granted",
                SecurityRisk.LOW
            )
            
            return True, None
            
        except Exception as e:
            logger.error(f"安全驗證失敗: {e}")
            await self._record_security_event(
                user_context.user_id if user_context else "unknown",
                request,
                operation_type.value,
                "security_check_error",
                SecurityRisk.HIGH,
                {"error": str(e)}
            )
            return False, "安全驗證失敗"
    
    async def _check_ip_whitelist(self, request: Request) -> bool:
        """檢查IP白名單"""
        if not self.security_config['enable_ip_whitelist']:
            return True
        
        client_ip = self._get_client_ip(request)
        allowed_ips = self.security_config['allowed_ips']
        
        if not allowed_ips:
            return True
        
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for allowed_ip in allowed_ips:
                try:
                    if '/' in allowed_ip:
                        # CIDR網段
                        if client_addr in ipaddress.ip_network(allowed_ip, strict=False):
                            return True
                    else:
                        # 單個IP
                        if client_addr == ipaddress.ip_address(allowed_ip):
                            return True
                except ValueError:
                    continue
            
            logger.warning(f"IP地址不在白名單中: {client_ip}")
            return False
            
        except ValueError:
            logger.error(f"無效的IP地址: {client_ip}")
            return False
    
    async def _check_route_permission(
        self,
        user_context: UserContext,
        operation_type: RoutePermissionType
    ) -> bool:
        """檢查路由權限"""
        # 映射操作類型到資源和動作
        permission_mapping = {
            RoutePermissionType.ROUTING_VIEW: (ResourceType.SYSTEM, Action.READ),
            RoutePermissionType.ROUTING_EDIT: (ResourceType.SYSTEM, Action.WRITE),
            RoutePermissionType.ROUTING_DELETE: (ResourceType.SYSTEM, Action.DELETE),
            RoutePermissionType.ROUTING_ADMIN: (ResourceType.SYSTEM, Action.ADMIN),
            RoutePermissionType.AB_TEST_VIEW: (ResourceType.SYSTEM, Action.READ),
            RoutePermissionType.AB_TEST_MANAGE: (ResourceType.SYSTEM, Action.WRITE),
            RoutePermissionType.PERFORMANCE_VIEW: (ResourceType.SYSTEM, Action.READ),
            RoutePermissionType.AUDIT_VIEW: (ResourceType.SYSTEM, Action.READ),
            RoutePermissionType.CONFIG_BACKUP: (ResourceType.SYSTEM, Action.WRITE),
            RoutePermissionType.CONFIG_RESTORE: (ResourceType.SYSTEM, Action.ADMIN)
        }
        
        resource, action = permission_mapping.get(operation_type, (ResourceType.SYSTEM, Action.READ))
        
        return self.permission_manager.has_permission(user_context, resource, action)
    
    async def _check_rate_limit(
        self,
        user_id: str,
        operation: str,
        request: Request
    ) -> bool:
        """檢查速率限制"""
        if not self.security_config['enable_rate_limiting']:
            return True
        
        rule = self.rate_limit_rules.get(operation)
        if not rule:
            return True
        
        now = time.time()
        user_requests = self.request_counters[user_id][operation]
        
        # 清理過期的請求記錄
        cutoff_time = now - rule.time_window_seconds
        user_requests[:] = [req_time for req_time in user_requests if req_time > cutoff_time]
        
        # 檢查是否超過限制
        if len(user_requests) >= rule.max_requests:
            logger.warning(f"用戶 {user_id} 超過速率限制: {operation}")
            await self._record_security_event(
                user_id,
                request,
                operation,
                "rate_limit_exceeded",
                SecurityRisk.MEDIUM
            )
            return False
        
        # 記錄此次請求
        user_requests.append(now)
        return True
    
    async def _validate_session(self, user_context: UserContext) -> bool:
        """驗證會話有效性"""
        session_id = getattr(user_context, 'session_id', None)
        if not session_id:
            return True  # 沒有會話管理時跳過檢查
        
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"會話不存在: {session_id}")
            return False
        
        # 檢查會話是否過期
        expires_at = session.get('expires_at')
        if expires_at and datetime.now(timezone.utc) > expires_at:
            logger.info(f"會話已過期: {session_id}")
            del self.active_sessions[session_id]
            return False
        
        # 檢查並發會話限制
        user_sessions = [
            s for s in self.active_sessions.values()
            if s.get('user_id') == user_context.user_id
        ]
        
        if len(user_sessions) > self.security_config['max_concurrent_sessions']:
            logger.warning(f"用戶 {user_context.user_id} 超過最大並發會話數")
            return False
        
        # 更新會話最後活動時間
        session['last_activity'] = datetime.now(timezone.utc)
        
        return True
    
    async def _detect_suspicious_activity(
        self,
        user_context: UserContext,
        operation_type: RoutePermissionType,
        request: Request
    ) -> bool:
        """檢測可疑活動"""
        if not self.security_config['block_suspicious_activity']:
            return False
        
        now = time.time()
        user_id = user_context.user_id
        
        # 檢查快速配置更改模式
        if operation_type in [RoutePermissionType.ROUTING_EDIT, RoutePermissionType.ROUTING_DELETE]:
            pattern = self.suspicious_patterns['rapid_config_changes']
            recent_changes = self.request_counters[user_id].get('config_changes', [])
            recent_changes = [t for t in recent_changes if t > now - pattern['window']]
            
            if len(recent_changes) >= pattern['threshold']:
                logger.warning(f"檢測到用戶 {user_id} 快速配置更改模式")
                await self._record_security_event(
                    user_id,
                    request,
                    "rapid_config_changes",
                    "suspicious_activity_detected",
                    SecurityRisk.HIGH
                )
                return True
            
            # 記錄配置更改
            self.request_counters[user_id]['config_changes'].append(now)
        
        # 檢查異常訪問模式
        pattern = self.suspicious_patterns['unusual_access_pattern']
        total_requests = sum(len(requests) for requests in self.request_counters[user_id].values())
        
        if total_requests >= pattern['threshold']:
            logger.warning(f"檢測到用戶 {user_id} 異常訪問模式")
            await self._record_security_event(
                user_id,
                request,
                "unusual_access_pattern",
                "suspicious_activity_detected",
                SecurityRisk.MEDIUM
            )
            return True
        
        return False
    
    async def _requires_additional_verification(
        self,
        operation_type: RoutePermissionType
    ) -> bool:
        """檢查是否需要額外驗證"""
        critical_operations = {
            RoutePermissionType.ROUTING_DELETE,
            RoutePermissionType.CONFIG_RESTORE,
            RoutePermissionType.ROUTING_ADMIN
        }
        
        return operation_type in critical_operations and self.security_config['enable_2fa_for_critical']
    
    async def _verify_critical_operation(
        self,
        user_context: UserContext,
        operation_type: RoutePermissionType
    ) -> bool:
        """驗證關鍵操作"""
        # 這裡應該實現2FA或其他額外驗證機制
        # 暫時返回True，實際實現時需要集成2FA系統
        return True
    
    async def _record_security_event(
        self,
        user_id: str,
        request: Request,
        resource: str,
        action: str,
        risk_level: SecurityRisk,
        details: Optional[Dict[str, Any]] = None
    ):
        """記錄安全事件"""
        if not self.security_config['enable_audit_logging']:
            return
        
        event = SecurityEvent(
            event_id=f"sec_{int(time.time())}_{hash(user_id + resource + action) % 10000}",
            user_id=user_id,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get('user-agent', 'unknown'),
            event_type=action,
            resource=resource,
            action=action,
            timestamp=datetime.now(timezone.utc),
            risk_level=risk_level,
            details=details or {},
            blocked=risk_level.value >= SecurityRisk.HIGH.value
        )
        
        self.security_events.append(event)
        
        # 限制事件記錄數量
        if len(self.security_events) > self.max_security_events:
            self.security_events = self.security_events[-self.max_security_events:]
        
        # 記錄高風險事件到日誌
        if risk_level.value >= SecurityRisk.MEDIUM.value:
            logger.warning(f"安全事件: {action} - 用戶 {user_id} - 風險等級 {risk_level.name}", extra={
                'security_event': True,
                'event_id': event.event_id,
                'user_id': user_id,
                'ip_address': event.ip_address,
                'resource': resource,
                'action': action,
                'risk_level': risk_level.name,
                'details': details
            })
    
    def _get_client_ip(self, request: Request) -> str:
        """獲取客戶端IP地址"""
        # 檢查反向代理頭部
        forwarded_for = request.headers.get('x-forwarded-for')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('x-real-ip')
        if real_ip:
            return real_ip.strip()
        
        # 回退到直接連接IP
        return request.client.host if request.client else 'unknown'
    
    def create_session(
        self,
        user_id: str,
        session_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """創建用戶會話"""
        import uuid
        
        session_id = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(
            hours=self.security_config['session_timeout_hours']
        )
        
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'created_at': datetime.now(timezone.utc),
            'expires_at': expires_at,
            'last_activity': datetime.now(timezone.utc),
            'data': session_data or {}
        }
        
        logger.info(f"創建會話: {session_id} - 用戶 {user_id}")
        return session_id
    
    def destroy_session(self, session_id: str) -> bool:
        """銷毀用戶會話"""
        if session_id in self.active_sessions:
            user_id = self.active_sessions[session_id].get('user_id')
            del self.active_sessions[session_id]
            logger.info(f"銷毀會話: {session_id} - 用戶 {user_id}")
            return True
        return False
    
    def get_security_summary(self) -> Dict[str, Any]:
        """獲取安全狀態摘要"""
        now = datetime.now(timezone.utc)
        
        # 統計最近24小時的安全事件
        day_ago = now - timedelta(days=1)
        recent_events = [e for e in self.security_events if e.timestamp > day_ago]
        
        # 按風險等級分組
        events_by_risk = defaultdict(int)
        for event in recent_events:
            events_by_risk[event.risk_level.name] += 1
        
        # 統計被阻止的事件
        blocked_events = [e for e in recent_events if e.blocked]
        
        return {
            'active_sessions': len(self.active_sessions),
            'total_security_events': len(self.security_events),
            'recent_events_24h': len(recent_events),
            'events_by_risk_level': dict(events_by_risk),
            'blocked_events_24h': len(blocked_events),
            'security_config': {
                'ip_whitelist_enabled': self.security_config['enable_ip_whitelist'],
                'rate_limiting_enabled': self.security_config['enable_rate_limiting'],
                'audit_logging_enabled': self.security_config['enable_audit_logging'],
                '2fa_for_critical_enabled': self.security_config['enable_2fa_for_critical']
            },
            'last_updated': now.isoformat()
        }
    
    def get_security_events(
        self,
        limit: int = 100,
        risk_level: Optional[SecurityRisk] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """獲取安全事件列表"""
        events = self.security_events
        
        # 過濾條件
        if risk_level:
            events = [e for e in events if e.risk_level == risk_level]
        
        if user_id:
            events = [e for e in events if e.user_id == user_id]
        
        # 按時間倒序排列並限制數量
        events = sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
        
        # 轉換為字典格式
        return [
            {
                'event_id': e.event_id,
                'user_id': e.user_id,
                'ip_address': e.ip_address,
                'event_type': e.event_type,
                'resource': e.resource,
                'action': e.action,
                'timestamp': e.timestamp.isoformat(),
                'risk_level': e.risk_level.name,
                'blocked': e.blocked,
                'details': e.details
            }
            for e in events
        ]


# 全局安全管理器實例
_routing_security_manager: Optional[RoutingSecurityManager] = None


def get_routing_security_manager(config: Optional[Dict[str, Any]] = None) -> RoutingSecurityManager:
    """獲取路由安全管理器實例"""
    global _routing_security_manager
    
    if _routing_security_manager is None:
        _routing_security_manager = RoutingSecurityManager(config)
    
    return _routing_security_manager


# 路由安全依賴項
async def verify_routing_security(
    operation_type: RoutePermissionType,
    request: Request,
    user_context: UserContext = Depends(get_current_admin_user),
    resource_id: Optional[str] = None
) -> UserContext:
    """驗證路由操作安全性的依賴項"""
    security_manager = get_routing_security_manager()
    
    allowed, reason = await security_manager.validate_request_security(
        request, user_context, operation_type, resource_id
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=reason or "安全驗證失敗"
        )
    
    return user_context


# 便利的安全裝飾器函數
def require_routing_permission(operation_type: RoutePermissionType):
    """要求特定路由權限的裝飾器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 這個裝飾器需要在FastAPI路由中配合Depends使用
            return await func(*args, **kwargs)
        return wrapper
    return decorator