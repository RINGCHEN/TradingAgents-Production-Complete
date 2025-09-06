#!/usr/bin/env python3
"""
最小化 FastAPI 應用，用於診斷部署問題
不依賴任何外部服務，純粹測試路由是否工作
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# 創建最簡單的 FastAPI 應用
app = FastAPI(
    title="TradingAgents 最小化測試應用",
    description="用於診斷 DigitalOcean 部署問題",
    version="1.0.0"
)

# 基本 CORS 設置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路由 - 最基本的測試"""
    return {
        "message": "最小化 TradingAgents 測試成功！",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "port": os.environ.get("PORT", "unknown")
    }

@app.get("/health")
async def health_check():
    """健康檢查"""
    return {
        "status": "healthy",
        "service": "minimal-tradingagents",
        "timestamp": datetime.now().isoformat(),
        "environment": {
            "PORT": os.environ.get("PORT", "not_set"),
            "PYTHONPATH": os.environ.get("PYTHONPATH", "not_set")
        }
    }

@app.get("/test")
async def test_endpoint():
    """測試端點"""
    return {
        "test": "OK",
        "message": "測試端點工作正常",
        "success": True
    }

# 如果直接運行此文件
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)