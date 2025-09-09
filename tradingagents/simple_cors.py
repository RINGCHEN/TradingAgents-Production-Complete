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
    # 使用最基本的設置，明確指定域名
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://03king.com", "https://03king.web.app", "https://admin.03king.com", "http://localhost:3000", "http://localhost:5173"],  # 明確允許的來源（不能使用通配符 * 當 credentials=True）
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明確允許的方法
        allow_headers=["*"],  # 允許所有頭部
        expose_headers=["*"]  # 暴露所有標頭
    )
    
    # 添加強制性 CORS 中間件
    @app.middleware("http")
    async def simple_cors_middleware(request: Request, call_next):
        # 獲取請求來源
        origin = request.headers.get("origin", "")
        allowed_origins = [
            "https://03king.com", 
            "https://03king.web.app", 
            "https://admin.03king.com",
            "http://localhost:3000",
            "http://localhost:5173"
        ]
        
        # 確定允許的來源
        allow_origin = origin if origin in allowed_origins else "https://03king.com"
        
        # 對於 OPTIONS 請求，直接返回 CORS 標頭
        if request.method == "OPTIONS":
            response = Response(
                content="",
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": allow_origin,
                    "Access-Control-Allow-Credentials": "true", 
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "86400"
                }
            )
            return response
        
        # 對於其他請求，正常處理並添加 CORS 標頭
        response = await call_next(request)
        
        # 強制添加CORS頭部到所有響應
        response.headers["Access-Control-Allow-Origin"] = allow_origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        
        return response
    
    # 讓 FastAPI 自己處理 OPTIONS 請求
    # 移除通用 OPTIONS 處理器以避免路由衝突
    
    print("[OK] 簡單CORS設置完成")