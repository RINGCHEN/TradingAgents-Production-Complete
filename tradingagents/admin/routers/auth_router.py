#!/usr/bin/env python3
"""
管理後台認證路由器 (Admin Authentication Router)
天工 (TianGong) - 管理後台認證 API 端點

此模組提供管理後台的認證功能，包含：
1. 管理員登入認證
2. 權限驗證
3. Token 管理
4. 登入歷史記錄
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import jwt
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.database import get_db
from ...utils.logging_config import get_security_logger

# 配置日誌
security_logger = get_security_logger("admin_auth")

# 創建路由器
router = APIRouter(prefix="/admin/auth", tags=["管理後台認證"])

# 請求模型
class AdminLoginRequest(BaseModel):
    """管理員登入請求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    twoFactorCode: Optional[str] = Field(None, min_length=6, max_length=8)

class AdminLoginResponse(BaseModel):
    """管理員登入響應"""
    success: bool
    token: Optional[str] = None
    adminData: Optional[Dict[str, Any]] = None
    requiresTwoFactor: bool = False
    message: str = ""

# 預設管理員帳戶
DEFAULT_ADMIN_ACCOUNTS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "data": {
            "id": "admin_001",
            "username": "admin",
            "email": "admin@03king.com",
            "role": "super_admin",
            "permissions": ["*"],  # 所有權限
            "display_name": "系統管理員",
            "created_at": "2024-01-01T00:00:00Z"
        }
    },
    "manager": {
        "password_hash": hashlib.sha256("manager123".encode()).hexdigest(),
        "data": {
            "id": "admin_002", 
            "username": "manager",
            "email": "manager@03king.com",
            "role": "admin",
            "permissions": [
                "dashboard", "user_management", "analytics", 
                "financial_management", "ai_effectiveness"
            ],
            "display_name": "營運經理",
            "created_at": "2024-01-01T00:00:00Z"
        }
    },
    "analyst": {
        "password_hash": hashlib.sha256("analyst123".encode()).hexdigest(),
        "data": {
            "id": "admin_003",
            "username": "analyst", 
            "email": "analyst@03king.com",
            "role": "analyst",
            "permissions": [
                "dashboard", "analytics", "ai_effectiveness", "behavior_dashboard"
            ],
            "display_name": "數據分析師",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }
}

def create_admin_token(admin_data: Dict[str, Any]) -> str:
    """創建管理員JWT Token"""
    payload = {
        "user_id": admin_data["id"],
        "username": admin_data["username"],
        "role": admin_data["role"],
        "permissions": admin_data["permissions"],
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
        "type": "admin"
    }
    
    # 使用固定密鑰用於演示
    secret_key = "tradingagents-admin-secret-key-2025"
    return jwt.encode(payload, secret_key, algorithm="HS256")

def verify_admin_password(username: str, password: str) -> Optional[Dict[str, Any]]:
    """驗證管理員密碼"""
    if username not in DEFAULT_ADMIN_ACCOUNTS:
        return None
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if password_hash == DEFAULT_ADMIN_ACCOUNTS[username]["password_hash"]:
        return DEFAULT_ADMIN_ACCOUNTS[username]["data"]
    
    return None

@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    request: AdminLoginRequest,
    client_request: Request,
    db: Session = Depends(get_db)
):
    """管理員登入端點"""
    try:
        # 記錄登入嘗試
        client_ip = client_request.client.host if client_request.client else "unknown"
        security_logger.info(f"管理員登入嘗試: {request.username} from {client_ip}")
        
        # 驗證帳號密碼
        admin_data = verify_admin_password(request.username, request.password)
        
        if not admin_data:
            security_logger.warning(f"管理員登入失敗: 無效帳號或密碼 - {request.username} from {client_ip}")
            return AdminLoginResponse(
                success=False,
                message="用戶名或密碼錯誤"
            )
        
        # 創建Token
        token = create_admin_token(admin_data)
        
        # 記錄成功登入
        security_logger.info(f"管理員登入成功: {request.username} ({admin_data['role']}) from {client_ip}")
        
        return AdminLoginResponse(
            success=True,
            token=token,
            adminData={
                "id": admin_data["id"],
                "username": admin_data["username"],
                "email": admin_data["email"],
                "role": admin_data["role"],
                "permissions": admin_data["permissions"],
                "display_name": admin_data["display_name"],
                "token": token
            },
            message="登入成功"
        )
        
    except Exception as e:
        security_logger.error(f"管理員登入錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登入服務暫時不可用"
        )

@router.post("/verify")
async def verify_admin_token(
    token: str,
    db: Session = Depends(get_db)
):
    """驗證管理員Token"""
    try:
        secret_key = "tradingagents-admin-secret-key-2025"
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        
        if payload.get("type") != "admin":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="無效的管理員Token")
        
        return {
            "valid": True,
            "user_id": payload["user_id"],
            "username": payload["username"],
            "role": payload["role"],
            "permissions": payload["permissions"]
        }
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token已過期")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="無效Token")

@router.post("/logout")
async def admin_logout():
    """管理員登出端點"""
    # 實際環境中應該將Token加入黑名單
    return {"success": True, "message": "登出成功"}

@router.get("/health")
async def admin_auth_health():
    """管理後台認證健康檢查"""
    return {
        "status": "healthy",
        "service": "admin_authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "available_accounts": list(DEFAULT_ADMIN_ACCOUNTS.keys())
    }

@router.get("/permissions")
async def get_all_permissions():
    """獲取所有可用權限清單"""
    return {
        "permissions": [
            {"key": "dashboard", "name": "儀表板", "description": "查看系統總覽"},
            {"key": "user_management", "name": "用戶管理", "description": "管理系統用戶"},
            {"key": "permission_management", "name": "權限管理", "description": "管理用戶權限"},
            {"key": "analyst_management", "name": "分析師管理", "description": "管理AI分析師"},
            {"key": "ai_training", "name": "AI訓練", "description": "監控AI訓練過程"},
            {"key": "subscription_management", "name": "訂閱管理", "description": "管理用戶訂閱"},
            {"key": "financial_management", "name": "財務管理", "description": "查看財務數據"},
            {"key": "revenue_analytics", "name": "營收分析", "description": "分析營收數據"},
            {"key": "behavior_dashboard", "name": "行為追蹤", "description": "用戶行為分析"},
            {"key": "ai_effectiveness", "name": "AI效果分析", "description": "分析AI效果"},
            {"key": "customer_service", "name": "客服中心", "description": "客戶服務管理"},
            {"key": "analytics", "name": "數據分析", "description": "基礎數據分析"},
            {"key": "advanced_analytics", "name": "高級分析", "description": "進階數據分析"},
            {"key": "workflow_automation", "name": "工作流程", "description": "自動化流程管理"},
            {"key": "ai_optimization", "name": "AI優化", "description": "AI系統優化"},
            {"key": "performance_optimization", "name": "性能優化", "description": "系統性能優化"}
        ]
    }

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import jwt
import bcrypt
from sqlalchemy.orm import Session

# 創建路由器
router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

# JWT配置
SECRET_KEY = "your-secret-key-change-in-production"  # 生產環境中應該從環境變數讀取
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 請求模型
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str
    permissions: list[str]
    is_admin: bool
    is_active: bool

# 模擬用戶數據（生產環境中應該從數據庫讀取）
MOCK_USERS = {
    "admin@example.com": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "password_hash": bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "admin",
        "permissions": ["user_management", "system_config", "analytics", "reports"],
        "is_admin": True,
        "is_active": True
    },
    "manager@example.com": {
        "id": 2,
        "username": "manager",
        "email": "manager@example.com", 
        "password_hash": bcrypt.hashpw("manager123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        "role": "manager",
        "permissions": ["user_management", "analytics"],
        "is_admin": False,
        "is_active": True
    }
}

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """創建訪問token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """創建刷新token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access"):
    """驗證token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """獲取當前用戶"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    if email is None or email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return MOCK_USERS[email]

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    管理員登錄
    """
    user = MOCK_USERS.get(login_data.email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # 驗證密碼
    if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # 創建tokens
    access_token = create_access_token(data={"sub": user["email"]})
    refresh_token = create_refresh_token(data={"sub": user["email"]})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    刷新訪問token
    """
    refresh_token = credentials.credentials
    payload = verify_token(refresh_token, "refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    email = payload.get("sub")
    if email is None or email not in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = MOCK_USERS[email]
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # 創建新的訪問token
    access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    獲取當前用戶信息
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        permissions=current_user["permissions"],
        is_admin=current_user["is_admin"],
        is_active=current_user["is_active"]
    )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    用戶登出
    """
    # 在實際實現中，這裡應該將token加入黑名單
    # 目前只是返回成功響應
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_token_endpoint(current_user: dict = Depends(get_current_user)):
    """
    驗證token有效性
    """
    return {
        "valid": True,
        "user": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "role": current_user["role"]
        }
    }