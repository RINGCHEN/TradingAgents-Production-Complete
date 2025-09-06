#!/usr/bin/env python3
"""
最簡單的CORS解決方案
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

def setup_simple_cors(app: FastAPI):
    """設置最簡單的CORS"""
    
    # 移除所有現有的CORS中間件
    # 使用最基本的設置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允許所有來源
        allow_credentials=True,
        allow_methods=["*"],  # 允許所有方法
        allow_headers=["*"],  # 允許所有頭部
    )
    
    # 添加簡單的CORS中間件
    @app.middleware("http")
    async def simple_cors_middleware(request: Request, call_next):
        response = await call_next(request)
        
        # 強制添加CORS頭部到所有響應
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response
    
    # 讓 FastAPI 自己處理 OPTIONS 請求
    # 移除通用 OPTIONS 處理器以避免路由衝突
    
    print("[OK] 簡單CORS設置完成")