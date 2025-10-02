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

from ...auth.dependencies import require_admin_access, require_permission
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

# Database connection helper
def get_db_connection():
    """獲取資料庫連接"""
    from ...database.database import SessionLocal
    return SessionLocal()

def get_user_from_db(email: str) -> Optional[dict]:
    """從資料庫查詢管理員用戶 (admin_users 表)"""
    from sqlalchemy import text
    import logging

    logger = logging.getLogger(__name__)
    db = get_db_connection()

    try:
        # 查詢 admin_users 表（包含 password_hash）
        query = text("""
            SELECT
                id,
                email,
                name,
                role,
                permissions,
                is_active,
                password_hash
            FROM admin_users
            WHERE email = :email
            LIMIT 1
        """)

        result = db.execute(query, {"email": email})
        row = result.fetchone()

        if not row:
            logger.info(f"Admin user not found: {email}")
            return None

        # 從 admin_users 表構建管理員數據
        admin_id = str(row[0])
        admin_email = row[1]
        admin_name = row[2] or admin_email.split('@')[0]
        admin_role = row[3] or 'admin'
        admin_permissions = row[4] if row[4] else ['user_management', 'analytics']
        is_active = row[5] if row[5] is not None else True
        password_hash = row[6]  # 從 admin_users 表獲取密碼 hash

        logger.info(f"Admin user found: {admin_email}, role: {admin_role}")

        return {
            "id": admin_id,
            "username": admin_name,
            "email": admin_email,
            "password_hash": password_hash,  # 真實的密碼 hash
            "role": admin_role,
            "permissions": admin_permissions if isinstance(admin_permissions, list) else ['user_management'],
            "is_admin": True,  # admin_users 表中的都是管理員
            "is_active": is_active
        }
    except Exception as e:
        logger.error(f"❌ Database error in get_user_from_db: {str(e)}", exc_info=True)
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details", exc_info=True)
        # Return None and let caller handle the error
        return None
    finally:
        db.close()

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
    """獲取當前用戶（從資料庫查詢）"""
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 從資料庫查詢用戶
    user = get_user_from_db(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

@router.get("/debug/database-status")
async def debug_database_status():
    """診斷端點：檢查資料庫和admin_users表狀態"""
    from sqlalchemy import text
    import logging

    logger = logging.getLogger(__name__)
    db = get_db_connection()

    try:
        # Check if admin_users table exists
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'admin_users'
            );
        """))
        table_exists = result.fetchone()[0]

        if not table_exists:
            return {
                "status": "error",
                "message": "admin_users table does not exist",
                "table_exists": False,
                "migration_needed": True
            }

        # Check if password_hash column exists
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'admin_users'
            AND column_name = 'password_hash';
        """))
        password_column_exists = result.fetchone() is not None

        # Count admin users
        result = db.execute(text("SELECT COUNT(*) FROM admin_users"))
        admin_count = result.fetchone()[0]

        # Get admin emails
        result = db.execute(text("SELECT email FROM admin_users"))
        admin_emails = [row[0] for row in result.fetchall()]

        return {
            "status": "success",
            "table_exists": True,
            "password_column_exists": password_column_exists,
            "admin_count": admin_count,
            "admin_emails": admin_emails,
            "migration_needed": not password_column_exists
        }

    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "exception_type": type(e).__name__
        }
    finally:
        db.close()

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    管理員登錄（從資料庫驗證）
    """
    # 從資料庫查詢用戶
    user = get_user_from_db(login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # 驗證密碼（資料庫中的密碼已經是 bcrypt hashed）
    if not user["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    try:
        # 比對密碼 hash
        if not bcrypt.checkpw(login_data.password.encode('utf-8'), user["password_hash"].encode('utf-8')):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
    except (ValueError, AttributeError):
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
    刷新訪問token（從資料庫驗證）
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
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 從資料庫查詢用戶
    user = get_user_from_db(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

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