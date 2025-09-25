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

# 配置簡單日誌 (避免複雜依賴)
import logging
security_logger = logging.getLogger("admin_auth")

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

