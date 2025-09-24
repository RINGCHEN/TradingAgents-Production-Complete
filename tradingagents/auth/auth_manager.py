#!/usr/bin/env python3
"""
認證管理系統 (Authentication Manager)
天工 (TianGong) - 企業級用戶認證和權限管理系統

此模組提供完整的用戶認證、授權和會話管理功能，包含：
1. JWT Token 生成和驗證
2. 多層次權限控制
3. 會話管理和安全檢查
4. 密碼安全和雜湊
5. API密鑰管理
6. Taiwan市場用戶特殊權限
"""

from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
import bcrypt
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from collections import defaultdict
import json
import re

from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..utils.logging_config import get_security_logger, get_api_logger
from ..utils.error_handler import handle_error, ErrorCategory, ErrorSeverity
from ..utils.user_context import UserContext, TierType, UserPermissions

# 配置日誌
security_logger = get_security_logger(__name__)
api_logger = get_api_logger(__name__)

class AuthMethod(Enum):
    """認證方式"""
    JWT_TOKEN = "jwt_token"
    API_KEY = "api_key"
    SESSION = "session"
    OAUTH = "oauth"

class SessionStatus(Enum):
    """會話狀態"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

@dataclass
class AuthToken:
    """認證令牌"""
    token: str
    token_type: str = "Bearer"
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    user_id: str = ""
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'token': self.token,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat(),
            'expires_in': int((self.expires_at - datetime.now()).total_seconds()),
            'user_id': self.user_id,
            'permissions': self.permissions,
            'metadata': self.metadata
        }

@dataclass
class UserSession:
    """用戶會話"""
    session_id: str
    user_id: str
    user_context: UserContext
    auth_method: AuthMethod
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=24))
    status: SessionStatus = SessionStatus.ACTIVE
    client_info: Dict[str, Any] = field(default_factory=dict)
    security_flags: Dict[str, Any] = field(default_factory=dict)
    
    def is_valid(self) -> bool:
        """檢查會話是否有效"""
        return (
            self.status == SessionStatus.ACTIVE and
            datetime.now() < self.expires_at
        )
    
    def refresh(self, extend_hours: int = 24):
        """刷新會話"""
        self.last_activity = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=extend_hours)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'session_id': self.session_id,
            'user_id': self.user_id,
            'auth_method': self.auth_method.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'status': self.status.value,
            'client_info': self.client_info,
            'security_flags': self.security_flags
        }

@dataclass
class APIKey:
    """API密鑰"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: List[str] = field(default_factory=list)
    rate_limit: int = 1000  # 每小時請求限制
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    usage_count: int = 0
    
    def is_valid(self) -> bool:
        """檢查API密鑰是否有效"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True

class PasswordManager:
    """密碼管理器"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """雜湊密碼"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """驗證密碼"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """生成安全密碼"""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """驗證密碼強度"""
        score = 0
        feedback = []
        
        # 長度檢查
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("密碼至少需要8個字符")
        
        # 複雜度檢查
        if re.search(r'[a-z]', password):
            score += 1
        else:
            feedback.append("需要包含小寫字母")
        
        if re.search(r'[A-Z]', password):
            score += 1
        else:
            feedback.append("需要包含大寫字母")
        
        if re.search(r'[0-9]', password):
            score += 1
        else:
            feedback.append("需要包含數字")
        
        if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            score += 1
        else:
            feedback.append("需要包含特殊字符")
        
        # 常見密碼檢查
        common_passwords = ["password", "123456", "qwerty", "admin", "letmein"]
        if password.lower() in common_passwords:
            score = 0
            feedback.append("不能使用常見密碼")
        
        strength_levels = {
            0: "very_weak",
            1: "weak", 
            2: "fair",
            3: "good",
            4: "strong",
            5: "very_strong"
        }
        
        return {
            'score': score,
            'strength': strength_levels.get(score, "very_weak"),
            'is_valid': score >= 3,
            'feedback': feedback
        }

class JWTManager:
    """JWT管理器"""
    
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        if len(secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.token_expiry = timedelta(hours=1)  # 縮短token有效期
        self.refresh_token_expiry = timedelta(days=7)
        # 添加已撤銷的token JTI列表
        self.revoked_jtis: set = set()
    
    def generate_token(
        self,
        user_id: str,
        permissions: List[str],
        token_type: str = "access",
        custom_claims: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成JWT令牌"""
        now = datetime.now()
        expiry = now + (self.refresh_token_expiry if token_type == "refresh" else self.token_expiry)
        
        payload = {
            'user_id': user_id,
            'permissions': permissions,
            'token_type': token_type,
            'iat': now.timestamp(),
            'exp': expiry.timestamp(),
            'jti': str(uuid.uuid4())  # JWT ID
        }
        
        if custom_claims:
            payload.update(custom_claims)
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def decode_token(self, token: str) -> Dict[str, Any]:
        """解碼JWT令牌"""
        try:
            # 添加audience和issuer驗證選項
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_signature": True
                }
            )
            
            # 檢查JTI是否被撤銷
            jti = payload.get('jti')
            if jti and jti in self.revoked_jtis:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="令牌已被撤銷"
                )
            
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已過期"
            )
        except (JWTError, JWTClaimsError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的令牌"
            )
    
    def refresh_token(self, refresh_token: str) -> str:
        """刷新令牌"""
        payload = self.decode_token(refresh_token)
        
        if payload.get('token_type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的刷新令牌"
            )
        
        # 生成新的訪問令牌
        new_token = self.generate_token(
            user_id=payload['user_id'],
            permissions=payload['permissions'],
            token_type='access'
        )
        
        return new_token

class AuthenticationManager:
    """認證管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # JWT設置
        self.secret_key = self.config.get('jwt_secret_key', secrets.token_urlsafe(32))
        self.jwt_manager = JWTManager(self.secret_key)
        
        # 密碼管理
        self.password_manager = PasswordManager()
        
        # 會話存儲 (實際應使用Redis等外部存儲)
        self.active_sessions: Dict[str, UserSession] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.revoked_tokens: set = set()
        
        # 安全設置
        self.max_login_attempts = self.config.get('max_login_attempts', 5)
        self.lockout_duration = timedelta(minutes=self.config.get('lockout_minutes', 30))
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        
        # HTTP Bearer安全方案
        self.security = HTTPBearer(auto_error=False)
        
        security_logger.info("認證管理器初始化完成", extra={
            'max_login_attempts': self.max_login_attempts,
            'lockout_duration_minutes': self.lockout_duration.total_seconds() / 60
        })
    
    async def authenticate_user(
        self,
        identifier: str,  # 用戶名或郵箱
        password: str,
        client_info: Optional[Dict[str, Any]] = None
    ) -> AuthToken:
        """用戶認證"""
        # 檢查帳戶鎖定
        if self._is_account_locked(identifier):
            security_logger.warning(f"帳戶被鎖定: {identifier}", extra={
                'account': identifier,
                'security_event': 'account_locked',
                'failed_attempts': len(self.failed_attempts[identifier])
            })
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="帳戶因多次失敗登入而被暫時鎖定"
            )
        
        try:
            # 模擬用戶驗證 (實際應從數據庫獲取)
            user_data = await self._get_user_by_identifier(identifier)
            
            if not user_data or not self.password_manager.verify_password(password, user_data['password_hash']):
                # 記錄失敗嘗試
                self._record_failed_attempt(identifier)
                
                security_logger.warning(f"登入失敗: {identifier}", extra={
                    'account': identifier,
                    'security_event': 'login_failed',
                    'client_info': client_info
                })
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用戶名或密碼錯誤"
                )
            
            # 清除失敗記錄
            if identifier in self.failed_attempts:
                del self.failed_attempts[identifier]
            
            # 創建用戶上下文
            user_context = UserContext(
                user_id=user_data['user_id'],
                membership_tier=TierType(user_data['membership_tier']),
                permissions=UserPermissions()
            )
            
            # 生成令牌
            permissions = self._get_user_permissions(user_context)
            access_token = self.jwt_manager.generate_token(
                user_id=user_context.user_id,
                permissions=permissions,
                token_type='access'
            )
            
            refresh_token = self.jwt_manager.generate_token(
                user_id=user_context.user_id,
                permissions=permissions,
                token_type='refresh'
            )
            
            # 創建會話
            session = await self._create_session(
                user_context=user_context,
                auth_method=AuthMethod.JWT_TOKEN,
                client_info=client_info or {}
            )
            
            # 創建認證令牌
            auth_token = AuthToken(
                token=access_token,
                user_id=user_context.user_id,
                permissions=permissions,
                metadata={
                    'refresh_token': refresh_token,
                    'session_id': session.session_id
                }
            )
            
            security_logger.info(f"用戶登入成功: {identifier}", extra={
                'user_id': user_context.user_id,
                'membership_tier': user_context.membership_tier.value,
                'session_id': session.session_id,
                'security_event': 'login_success',
                'client_info': client_info
            })
            
            return auth_token
            
        except HTTPException:
            raise
        except Exception as e:
            error_info = await handle_error(e, {
                'component': 'auth_manager',
                'operation': 'authenticate_user',
                'identifier': identifier
            })
            
            security_logger.error(f"認證過程發生錯誤: {str(e)}", extra={
                'error_id': error_info.error_id,
                'identifier': identifier
            })
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="認證服務暫時不可用"
            )
    
    async def verify_token(self, token: str) -> UserContext:
        """驗證令牌"""
        if token in self.revoked_tokens:
            security_logger.warning("嘗試使用已撤銷的令牌", extra={
                'security_event': 'revoked_token_used'
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已被撤銷"
            )
        
        try:
            payload = self.jwt_manager.decode_token(token)
            user_id = payload['user_id']
            
            # 獲取用戶上下文
            user_context = await self._get_user_context(user_id)
            
            # 更新會話活動時間
            session_id = payload.get('session_id')
            if session_id and session_id in self.active_sessions:
                self.active_sessions[session_id].refresh()
            
            return user_context
            
        except HTTPException:
            raise
        except Exception as e:
            error_info = await handle_error(e, {
                'component': 'auth_manager',
                'operation': 'verify_token'
            })
            
            security_logger.error(f"令牌驗證錯誤: {str(e)}", extra={
                'error_id': error_info.error_id
            })
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌驗證失敗"
            )
    
    async def verify_api_key(self, api_key: str) -> UserContext:
        """驗證API密鑰"""
        # 雜湊API密鑰進行比較
        key_hash = self.password_manager.hash_password(api_key)
        
        for stored_key in self.api_keys.values():
            if self.password_manager.verify_password(api_key, stored_key.key_hash):
                if not stored_key.is_valid():
                    security_logger.warning("使用無效的API密鑰", extra={
                        'key_id': stored_key.key_id,
                        'user_id': stored_key.user_id,
                        'security_event': 'invalid_api_key'
                    })
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="API密鑰無效或已過期"
                    )
                
                # 更新使用記錄
                stored_key.last_used = datetime.now()
                stored_key.usage_count += 1
                
                # 獲取用戶上下文
                user_context = await self._get_user_context(stored_key.user_id)
                
                security_logger.info("API密鑰驗證成功", extra={
                    'key_id': stored_key.key_id,
                    'user_id': stored_key.user_id,
                    'usage_count': stored_key.usage_count
                })
                
                return user_context
        
        security_logger.warning("無效的API密鑰", extra={
            'security_event': 'invalid_api_key_attempt'
        })
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的API密鑰"
        )
    
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        permissions: List[str],
        expires_in_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """創建API密鑰"""
        # 生成密鑰
        raw_key = secrets.token_urlsafe(32)
        key_hash = self.password_manager.hash_password(raw_key)
        key_id = str(uuid.uuid4())
        
        # 設置過期時間
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        # 創建API密鑰對象
        api_key = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            permissions=permissions,
            expires_at=expires_at
        )
        
        self.api_keys[key_id] = api_key
        
        security_logger.info(f"API密鑰創建成功: {name}", extra={
            'key_id': key_id,
            'user_id': user_id,
            'permissions': permissions,
            'expires_at': expires_at.isoformat() if expires_at else None
        })
        
        return {
            'key_id': key_id,
            'api_key': raw_key,  # 僅此次返回原始密鑰
            'name': name,
            'permissions': permissions,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'created_at': api_key.created_at.isoformat()
        }
    
    async def logout(self, token: str) -> bool:
        """登出"""
        try:
            payload = self.jwt_manager.decode_token(token)
            
            # 添加到撤銷列表
            self.revoked_tokens.add(token)
            
            # 移除會話
            session_id = payload.get('session_id')
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.status = SessionStatus.REVOKED
                del self.active_sessions[session_id]
            
            security_logger.info("用戶登出成功", extra={
                'user_id': payload['user_id'],
                'session_id': session_id,
                'security_event': 'logout_success'
            })
            
            return True
            
        except Exception as e:
            security_logger.error(f"登出過程發生錯誤: {str(e)}")
            return False
    
    async def _create_session(
        self,
        user_context: UserContext,
        auth_method: AuthMethod,
        client_info: Dict[str, Any]
    ) -> UserSession:
        """創建用戶會話"""
        session_id = str(uuid.uuid4())
        
        session = UserSession(
            session_id=session_id,
            user_id=user_context.user_id,
            user_context=user_context,
            auth_method=auth_method,
            client_info=client_info
        )
        
        self.active_sessions[session_id] = session
        return session
    
    def _get_user_permissions(self, user_context: UserContext) -> List[str]:
        """獲取用戶權限列表"""
        permissions = []
        
        # 基礎權限
        permissions.append("read:profile")
        permissions.append("read:analysis")
        
        # 根據會員等級添加權限
        if user_context.membership_tier in [TierType.GOLD, TierType.DIAMOND]:
            permissions.extend([
                "read:advanced_analysis",
                "write:watchlist",
                "read:historical_data"
            ])
        
        if user_context.membership_tier == TierType.DIAMOND:
            permissions.extend([
                "read:real_time_data",
                "write:custom_alerts",
                "read:system_metrics",
                "export:data"
            ])
        
        return permissions
    
    def _is_account_locked(self, identifier: str) -> bool:
        """檢查帳戶是否被鎖定"""
        if identifier not in self.failed_attempts:
            return False
        
        recent_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if datetime.now() - attempt < self.lockout_duration
        ]
        
        return len(recent_attempts) >= self.max_login_attempts
    
    def _record_failed_attempt(self, identifier: str):
        """記錄失敗嘗試"""
        self.failed_attempts[identifier].append(datetime.now())
        
        # 清理舊記錄
        cutoff_time = datetime.now() - self.lockout_duration
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff_time
        ]
    
    async def _get_user_by_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """根據標識符獲取用戶 (模擬實現)"""
        # 實際實現應該從數據庫查詢
        mock_users = {
            "admin@example.com": {
                "user_id": "admin_001",
                "email": "admin@example.com",
                "password_hash": self.password_manager.hash_password("admin123"),
                "membership_tier": "DIAMOND"
            },
            "test@example.com": {
                "user_id": "user_123",
                "email": "test@example.com",
                "password_hash": self.password_manager.hash_password("password123"),
                "membership_tier": "FREE"
            },
            "gold@example.com": {
                "user_id": "user_456", 
                "email": "gold@example.com",
                "password_hash": self.password_manager.hash_password("goldpass123"),
                "membership_tier": "GOLD"
            },
            "diamond@example.com": {
                "user_id": "user_789",
                "email": "diamond@example.com", 
                "password_hash": self.password_manager.hash_password("diamondpass123"),
                "membership_tier": "DIAMOND"
            }
        }
        
        return mock_users.get(identifier)
    
    async def _get_user_context(self, user_id: str) -> UserContext:
        """獲取用戶上下文"""
        # 實際實現應該從數據庫查詢
        mock_context = {
            "admin_001": UserContext(
                user_id="admin_001",
                membership_tier=TierType.DIAMOND,
                permissions=UserPermissions()
            ),
            "user_123": UserContext(
                user_id="user_123",
                membership_tier=TierType.FREE,
                permissions=UserPermissions()
            ),
            "user_456": UserContext(
                user_id="user_456",
                membership_tier=TierType.GOLD,
                permissions=UserPermissions()
            ),
            "user_789": UserContext(
                user_id="user_789",
                membership_tier=TierType.DIAMOND,
                permissions=UserPermissions()
            )
        }
        
        return mock_context.get(user_id) or UserContext(
            user_id=user_id,
            membership_tier=TierType.FREE,
            permissions=UserPermissions()
        )
    
    def get_auth_stats(self) -> Dict[str, Any]:
        """獲取認證統計"""
        return {
            'active_sessions': len(self.active_sessions),
            'api_keys': len(self.api_keys),
            'revoked_tokens': len(self.revoked_tokens),
            'failed_attempts': len(self.failed_attempts),
            'locked_accounts': sum(1 for identifier in self.failed_attempts.keys() 
                                 if self._is_account_locked(identifier))
        }

# 便利函數
_global_auth_manager: Optional[AuthenticationManager] = None

def get_auth_manager(config: Optional[Dict[str, Any]] = None) -> AuthenticationManager:
    """獲取全局認證管理器實例"""
    global _global_auth_manager
    
    if _global_auth_manager is None:
        _global_auth_manager = AuthenticationManager(config)
    
    return _global_auth_manager

if __name__ == "__main__":
    # 測試腳本
    async def test_auth_manager():
        print("測試認證管理器...")
        
        # 創建認證管理器
        auth_manager = get_auth_manager()
        
        # 測試密碼強度驗證
        password_check = PasswordManager.validate_password_strength("Test123!")
        print(f"密碼強度: {password_check}")
        
        # 測試用戶認證
        try:
            auth_token = await auth_manager.authenticate_user(
                "test@example.com",
                "password123",
                {"ip": "192.168.1.100", "user_agent": "TestClient"}
            )
            print(f"認證成功: {auth_token.to_dict()}")
            
            # 測試令牌驗證
            user_context = await auth_manager.verify_token(auth_token.token)
            print(f"令牌驗證成功: {user_context.user_id}")
            
            # 測試登出
            logout_success = await auth_manager.logout(auth_token.token)
            print(f"登出成功: {logout_success}")
            
        except HTTPException as e:
            print(f"認證失敗: {e.detail}")
        
        # 測試API密鑰創建
        api_key_info = await auth_manager.create_api_key(
            user_id="user_123",
            name="測試密鑰",
            permissions=["read:analysis"],
            expires_in_days=30
        )
        print(f"API密鑰創建成功: {api_key_info['key_id']}")
        
        # 獲取統計資訊
        stats = auth_manager.get_auth_stats()
        print(f"認證統計: {stats}")
        
        print("認證管理器測試完成")
    
    asyncio.run(test_auth_manager())