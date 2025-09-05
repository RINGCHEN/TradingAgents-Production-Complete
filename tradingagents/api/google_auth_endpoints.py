#!/usr/bin/env python3
"""
Google OAuth 認證 API 端點
處理 Google 帳號註冊和登入
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr, validator
import psycopg2
import jwt
from jwt import PyJWTError

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/auth", tags=["Google Authentication"])

# 資料庫配置
DATABASE_CONFIG = {
    'host': '35.194.205.200',
    'port': 5432,
    'database': 'tradingagents',
    'user': 'postgres',
    'password': 'secure_postgres_password_2024'
}

# JWT 配置
JWT_SECRET_KEY = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

# Pydantic 模型
class GoogleAuthRequest(BaseModel):
    """Google OAuth 認證請求"""
    google_token: str  # Google JWT token
    name: str
    email: EmailStr
    picture: Optional[str] = None
    
    @validator('name')
    def validate_name(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('姓名不能為空')
        return v.strip()

class GoogleAuthResponse(BaseModel):
    """Google OAuth 認證回應"""
    success: bool
    message: str
    user_id: int
    access_token: str
    is_new_user: bool
    user_data: Dict[str, Any]

class UserProfileResponse(BaseModel):
    """用戶資料回應"""
    user_id: int
    email: str
    name: str
    membership_tier: str
    auth_provider: str
    email_verified: bool
    created_at: str
    last_login: str

def get_database_connection():
    """獲取資料庫連接"""
    try:
        return psycopg2.connect(**DATABASE_CONFIG)
    except Exception as e:
        logger.error(f"資料庫連接失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="資料庫服務暫時不可用"
        )

def verify_google_token(token: str) -> Dict[str, Any]:
    """驗證 Google JWT token (簡化版本)"""
    try:
        # 在實際生產環境中，應該使用 Google 的公鑰驗證 JWT
        # 這裡為了演示，直接解析 token
        import base64
        import json
        
        # 分割 JWT
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("無效的 JWT 格式")
        
        # 解碼 payload
        payload = parts[1]
        # 添加必要的 padding
        payload += '=' * (4 - len(payload) % 4)
        decoded_bytes = base64.urlsafe_b64decode(payload)
        payload_data = json.loads(decoded_bytes.decode('utf-8'))
        
        # 檢查必要的字段
        required_fields = ['sub', 'email', 'name', 'email_verified']
        for field in required_fields:
            if field not in payload_data:
                raise ValueError(f"JWT 缺少必要字段: {field}")
        
        return payload_data
        
    except Exception as e:
        logger.error(f"Google token 驗證失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無效的 Google token"
        )

def create_access_token(user_data: Dict[str, Any]) -> str:
    """創建訪問 token"""
    try:
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'membership_tier': user_data['membership_tier'],
            'exp': datetime.utcnow().timestamp() + 3600 * 24,  # 24小時過期
            'iat': datetime.utcnow().timestamp()
        }
        
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
    except Exception as e:
        logger.error(f"創建 access token 失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="token 創建失敗"
        )

@router.post("/google-login", response_model=GoogleAuthResponse, summary="Google 帳號登入/註冊")
async def google_auth(
    request: GoogleAuthRequest,
    background_tasks: BackgroundTasks
):
    """
    處理 Google OAuth 登入和註冊
    
    如果用戶不存在則自動註冊，如果存在則更新登入時間
    """
    try:
        # 驗證 Google token
        google_user_data = verify_google_token(request.google_token)
        
        # 獲取資料庫連接
        conn = get_database_connection()
        cur = conn.cursor()
        
        try:
            # 檢查用戶是否已存在 (透過 email 或 google_id)
            cur.execute("""
                SELECT id, email, username, display_name, membership_tier, 
                       auth_provider, google_id, last_login, created_at
                FROM users 
                WHERE email = %s OR google_id = %s
            """, (request.email, google_user_data['sub']))
            
            existing_user = cur.fetchone()
            is_new_user = False
            
            if existing_user:
                # 用戶已存在 - 更新登入時間和 Google 資訊
                user_id = existing_user[0]
                
                cur.execute("""
                    UPDATE users 
                    SET last_login = NOW(),
                        login_count = login_count + 1,
                        google_id = %s,
                        auth_provider = 'google',
                        updated_at = NOW()
                    WHERE id = %s
                """, (google_user_data['sub'], user_id))
                
                logger.info(f"用戶登入: {request.email} (ID: {user_id})")
                
            else:
                # 新用戶 - 創建記錄
                is_new_user = True
                
                cur.execute("""
                    INSERT INTO users (
                        email, display_name, auth_provider, google_id, 
                        membership_tier, status, email_verified,
                        profile_picture, created_at, updated_at, last_login, login_count
                    ) VALUES (
                        %s, %s, 'google', %s,
                        'FREE', 'active', TRUE,
                        %s, NOW(), NOW(), NOW(), 1
                    ) RETURNING id
                """, (
                    request.email,
                    request.name,
                    google_user_data['sub'],
                    request.picture
                ))
                
                user_id = cur.fetchone()[0]
                
                logger.info(f"新用戶註冊: {request.email} (ID: {user_id})")
            
            # 獲取完整用戶資料
            cur.execute("""
                SELECT id, email, display_name, membership_tier, 
                       auth_provider, email_verified, created_at, last_login
                FROM users 
                WHERE id = %s
            """, (user_id,))
            
            user_record = cur.fetchone()
            
            # 提交事務
            conn.commit()
            
            # 構建用戶資料
            user_data = {
                'id': user_record[0],
                'email': user_record[1],
                'name': user_record[2],
                'membership_tier': user_record[3],
                'auth_provider': user_record[4],
                'email_verified': user_record[5]
            }
            
            # 創建訪問 token
            access_token = create_access_token(user_data)
            
            # 在背景任務中處理額外操作
            if is_new_user:
                background_tasks.add_task(
                    handle_new_user_tasks,
                    user_id,
                    request.email,
                    request.name
                )
            
            # 回傳結果
            return GoogleAuthResponse(
                success=True,
                message="登入成功" if not is_new_user else "註冊成功",
                user_id=user_id,
                access_token=access_token,
                is_new_user=is_new_user,
                user_data=user_data
            )
            
        except Exception as db_error:
            # 回滾事務
            conn.rollback()
            raise db_error
            
        finally:
            # 關閉資料庫連接
            cur.close()
            conn.close()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google 認證處理失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="認證服務暫時不可用"
        )

@router.get("/profile", response_model=UserProfileResponse, summary="獲取用戶資料")
async def get_user_profile(
    user_id: int,
    # 在實際實現中應該從 JWT token 中獲取 user_id
):
    """
    獲取用戶詳細資料
    """
    try:
        conn = get_database_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, email, display_name, membership_tier, 
                   auth_provider, email_verified, created_at, last_login
            FROM users 
            WHERE id = %s
        """, (user_id,))
        
        user_record = cur.fetchone()
        
        if not user_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用戶不存在"
            )
        
        return UserProfileResponse(
            user_id=user_record[0],
            email=user_record[1],
            name=user_record[2] or "未設置",
            membership_tier=user_record[3],
            auth_provider=user_record[4],
            email_verified=user_record[5],
            created_at=user_record[6].isoformat() if user_record[6] else "",
            last_login=user_record[7].isoformat() if user_record[7] else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取用戶資料失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用戶資料服務暫時不可用"
        )
    finally:
        if 'conn' in locals():
            cur.close()
            conn.close()

async def handle_new_user_tasks(user_id: int, email: str, name: str):
    """處理新用戶的背景任務"""
    try:
        logger.info(f"處理新用戶背景任務: {email} (ID: {user_id})")
        
        # 這裡可以添加：
        # 1. 發送歡迎郵件
        # 2. 創建用戶偏好設置
        # 3. 記錄註冊來源分析
        # 4. 觸發 webhook 通知
        
        # 模擬處理
        import asyncio
        await asyncio.sleep(1)
        
        logger.info(f"新用戶背景任務完成: {email}")
        
    except Exception as e:
        logger.error(f"新用戶背景任務失敗: {e}")

@router.get("/health", summary="Google 認證服務健康檢查")
async def health_check():
    """檢查 Google 認證服務健康狀態"""
    try:
        # 測試資料庫連接
        conn = get_database_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        conn.close()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "google_auth",
            "database": "connected"
        }
        
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "google_auth",
            "database": "disconnected",
            "error": str(e)
        }

if __name__ == "__main__":
    # 測試路由配置
    print("Google Auth API 端點:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")