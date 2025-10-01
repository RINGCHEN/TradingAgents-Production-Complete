"""
認證路由器
提供管理員認證相關的API端點
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import jwt
import bcrypt
from sqlalchemy.orm import Session

from ...auth.dependencies import require_admin_access
from ...auth.permissions import ResourceType, Action
from ...utils.user_context import UserContext

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
async def get_current_user_info(
    _: UserContext = Depends(require_permission(ResourceType.SYSTEM, Action.READ)),
    current_user: dict = Depends(get_current_user)
):
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
async def logout(
    _: UserContext = Depends(require_permission(ResourceType.SYSTEM, Action.WRITE)),
    current_user: dict = Depends(get_current_user)
):
    """
    用戶登出
    """
    # 在實際實現中，這裡應該將token加入黑名單
    # 目前只是返回成功響應
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_token_endpoint(
    _: UserContext = Depends(require_permission(ResourceType.SYSTEM, Action.READ)),
    current_user: dict = Depends(get_current_user)
):
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