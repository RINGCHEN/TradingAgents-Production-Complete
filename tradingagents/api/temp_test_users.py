#!/usr/bin/env python3
"""
臨時測試用戶創建端點 - 僅用於 Phase 4 E2E 測試
部署後可通過 API 創建測試用戶

**警告**: 此端點僅用於測試環境，完成後應立即移除
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from datetime import datetime
import uuid
import bcrypt
from typing import Dict, Any

router = APIRouter(prefix="/api/temp", tags=["temp-testing"])

class TestUserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    membership_tier: str
    full_name: str = None

def hash_password(password: str) -> str:
    """使用bcrypt雜湊密碼"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

@router.post("/create-test-user")
async def create_test_user(user_data: TestUserCreate) -> Dict[str, Any]:
    """
    創建測試用戶 (臨時端點)

    **警告**: 此端點僅用於 Phase 4 E2E 測試
    """
    from ..database.database import SessionLocal

    db = SessionLocal()

    try:
        # 檢查用戶是否已存在
        check_query = text("""
            SELECT id, email, membership_tier
            FROM users
            WHERE email = :email
            LIMIT 1
        """)

        result = db.execute(check_query, {"email": user_data.email})
        existing_user = result.fetchone()

        if existing_user:
            return {
                "success": True,
                "message": "User already exists",
                "email": user_data.email,
                "tier": existing_user[2],
                "status": "already_exists"
            }

        # 創建新用戶
        user_id = str(uuid.uuid4())
        password_hash = hash_password(user_data.password)
        created_at = datetime.now()

        insert_query = text("""
            INSERT INTO users (
                user_id,
                email,
                username,
                name,
                password_hash,
                membership_tier,
                email_verified,
                phone_verified,
                is_oauth_user,
                is_active,
                created_at,
                updated_at
            ) VALUES (
                :user_id,
                :email,
                :username,
                :name,
                :password_hash,
                :membership_tier,
                true,
                false,
                false,
                true,
                :created_at,
                :created_at
            )
            RETURNING id, user_id, email, membership_tier
        """)

        result = db.execute(insert_query, {
            "user_id": user_id,
            "email": user_data.email,
            "username": user_data.username,
            "name": user_data.full_name or user_data.username,
            "password_hash": password_hash,
            "membership_tier": user_data.membership_tier,
            "created_at": created_at
        })

        db.commit()

        inserted_user = result.fetchone()

        return {
            "success": True,
            "message": "Test user created successfully",
            "user_id": inserted_user[1],
            "email": inserted_user[2],
            "tier": inserted_user[3],
            "status": "created"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create test user: {str(e)}"
        )
    finally:
        db.close()

@router.post("/create-all-test-users")
async def create_all_test_users() -> Dict[str, Any]:
    """
    一次創建所有 E2E 測試需要的用戶
    """
    test_users = [
        {
            "email": "admin@example.com",
            "password": "admin123",
            "username": "admin",
            "membership_tier": "DIAMOND",
            "full_name": "Admin Test User"
        },
        {
            "email": "gold@example.com",
            "password": "gold123",
            "username": "golduser",
            "membership_tier": "GOLD",
            "full_name": "Gold Test User"
        }
    ]

    results = []

    for user_config in test_users:
        try:
            user_data = TestUserCreate(**user_config)
            result = await create_test_user(user_data)
            results.append(result)
        except HTTPException as e:
            results.append({
                "success": False,
                "email": user_config["email"],
                "error": f"HTTPException: {e.detail}",
                "status_code": e.status_code
            })
        except Exception as e:
            import traceback
            results.append({
                "success": False,
                "email": user_config["email"],
                "error": str(e),
                "traceback": traceback.format_exc()
            })

    return {
        "success": True,
        "message": "Test users creation completed",
        "results": results
    }
