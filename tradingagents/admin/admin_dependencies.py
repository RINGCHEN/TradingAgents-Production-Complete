#!/usr/bin/env python3
"""
Admin 認證依賴項 (Admin Authentication Dependencies)
專門為 Admin 系統設計的認證和授權依賴項

此模組提供 Admin 系統專用的認證邏輯，完全獨立於普通用戶系統：
1. Admin JWT Token 驗證
2. Admin 權限檢查
3. Admin 用戶上下文管理
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import logging
from datetime import datetime

# 配置日誌
logger = logging.getLogger(__name__)

# HTTP Bearer 安全方案
security = HTTPBearer(auto_error=False)

# JWT 配置（應與 auth_router.py 保持一致）
SECRET_KEY = "your-secret-key-change-in-production"  # 應從環境變量讀取
ALGORITHM = "HS256"


class AdminContext:
    """Admin 用戶上下文"""
    def __init__(self, email: str, role: str = "admin", permissions: list = None):
        self.user_id = email  # Admin 系統使用 email 作為標識
        self.email = email
        self.role = role
        self.permissions = permissions or []
        self.is_admin = True


async def get_current_admin_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> AdminContext:
    """
    獲取當前 Admin 用戶

    專門用於 Admin 系統的 JWT token 驗證
    從 admin_users 表驗證用戶身份
    """
    if not credentials:
        logger.warning("未提供認證憑證")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要認證憑證",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # 解碼 JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type", "access")

        if email is None:
            logger.error("Token payload 缺少 'sub' 字段")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if token_type != "access":
            logger.error(f"Token 類型錯誤: {token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="無效的令牌類型",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 從資料庫驗證 Admin 用戶
        admin_user = await get_admin_from_db(email)

        if not admin_user:
            logger.warning(f"Admin 用戶不存在: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用戶不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not admin_user.get("is_active", True):
            logger.warning(f"Admin 帳號已停用: {email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="帳號已停用",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 創建 Admin 上下文
        admin_context = AdminContext(
            email=admin_user["email"],
            role=admin_user.get("role", "admin"),
            permissions=admin_user.get("permissions", [])
        )

        logger.info(f"Admin 用戶驗證成功: {email}, role: {admin_context.role}")

        return admin_context

    except JWTError as e:
        logger.error(f"JWT 解碼失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin 認證過程發生錯誤: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認證服務暫時不可用"
        )


async def get_admin_from_db(email: str) -> Optional[dict]:
    """
    從資料庫查詢 Admin 用戶（admin_users 表）

    Args:
        email: Admin 郵箱

    Returns:
        Admin 用戶資料字典，如果不存在則返回 None
    """
    from sqlalchemy import text
    from ...database.database import SessionLocal

    # 創建資料庫連接
    db = SessionLocal()

    try:
        query = text("""
            SELECT
                id,
                email,
                name,
                role,
                permissions,
                is_active
            FROM admin_users
            WHERE email = :email
            LIMIT 1
        """)

        result = db.execute(query, {"email": email})
        row = result.fetchone()

        if not row:
            logger.info(f"Admin 用戶不存在: {email}")
            return None

        admin_data = {
            "id": str(row[0]),
            "email": row[1],
            "name": row[2] or row[1].split('@')[0],
            "role": row[3] or "admin",
            "permissions": row[4] if row[4] else [],
            "is_active": row[5] if row[5] is not None else True
        }

        logger.debug(f"Admin 用戶查詢成功: {email}")
        return admin_data

    except Exception as e:
        logger.error(f"資料庫查詢 Admin 用戶失敗: {email}, 錯誤: {str(e)}", exc_info=True)
        return None
    finally:
        db.close()


def require_admin_permission(required_permissions: list = None):
    """
    要求特定 Admin 權限的依賴項工廠

    Args:
        required_permissions: 需要的權限列表

    Returns:
        依賴項函數
    """
    async def check_permission(admin: AdminContext = Depends(get_current_admin_user)) -> AdminContext:
        if required_permissions:
            for perm in required_permissions:
                if perm not in admin.permissions:
                    logger.warning(
                        f"Admin 權限不足: {admin.email}, "
                        f"需要: {required_permissions}, "
                        f"擁有: {admin.permissions}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"權限不足: 需要 {perm} 權限"
                    )

        return admin

    return check_permission


def require_admin_role(required_role: str = "admin"):
    """
    要求特定 Admin 角色的依賴項工廠

    Args:
        required_role: 需要的角色（admin, manager 等）

    Returns:
        依賴項函數
    """
    async def check_role(admin: AdminContext = Depends(get_current_admin_user)) -> AdminContext:
        # 角色層級: admin > manager
        role_hierarchy = {"admin": 2, "manager": 1}

        user_level = role_hierarchy.get(admin.role, 0)
        required_level = role_hierarchy.get(required_role, 999)

        if user_level < required_level:
            logger.warning(
                f"Admin 角色不足: {admin.email}, "
                f"需要: {required_role}, "
                f"擁有: {admin.role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"角色不足: 需要 {required_role} 或更高級別"
            )

        return admin

    return check_role


# 便捷依賴項別名
CurrentAdmin = Depends(get_current_admin_user)
AdminOnly = Depends(require_admin_role("admin"))
ManagerOrAbove = Depends(require_admin_role("manager"))
