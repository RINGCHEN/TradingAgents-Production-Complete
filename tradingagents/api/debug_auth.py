#!/usr/bin/env python3
"""
Debug authentication endpoint
Temporary diagnostic tool
"""

from fastapi import APIRouter
from sqlalchemy import text
from ..database.database import SessionLocal

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/check-user/{email}")
async def check_user(email: str):
    """檢查用戶是否存在於資料庫"""
    try:
        db = SessionLocal()
        try:
            query = text("""
                SELECT id, email, username, membership_tier, status
                FROM users
                WHERE email = :email
                LIMIT 1
            """)

            result = db.execute(query, {"email": email})
            row = result.fetchone()

            if not row:
                return {
                    "found": False,
                    "email": email,
                    "message": "User not found in database"
                }

            return {
                "found": True,
                "user": {
                    "id": row[0],
                    "email": row[1],
                    "username": row[2],
                    "membership_tier": row[3],
                    "status": row[4]
                }
            }

        finally:
            db.close()

    except Exception as e:
        return {
            "error": str(e),
            "message": "Database query failed"
        }
