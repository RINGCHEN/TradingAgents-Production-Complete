#!/usr/bin/env python3
"""
Simple admin authentication test router
"""

from fastapi import APIRouter
from pydantic import BaseModel

# 創建簡單的測試路由器
router = APIRouter(prefix="/admin/auth", tags=["admin-auth-test"])

class SimpleResponse(BaseModel):
    success: bool
    message: str

@router.get("/health")
async def simple_health():
    """簡單健康檢查端點"""
    return {"status": "healthy", "message": "Admin auth test working"}

@router.post("/test-login")
async def test_login():
    """測試登入端點"""
    return SimpleResponse(
        success=True,
        message="Admin auth test endpoint working"
    )