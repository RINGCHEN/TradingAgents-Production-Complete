#!/usr/bin/env python3
"""
簡單 CORS 設定：預設只允許生產域名；可用環境變數 CORS_ALLOWED_ORIGINS 覆寫（逗號分隔）。
"""

from fastapi import FastAPI, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import os


def setup_simple_cors(app: FastAPI):
    """Attach CORS middleware and a small guard middleware.

    - Default allowed origins: https://03king.com, https://admin.03king.com
    - Overridable via env CORS_ALLOWED_ORIGINS="origin1,origin2"
    """

    origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "https://03king.com,https://admin.03king.com")
    allowed_origins = [o.strip() for o in origins_env.split(",") if o.strip()]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    )

    @app.middleware("http")
    async def simple_cors_middleware(request: Request, call_next):
        origin = request.headers.get("origin", "")

        # Handle preflight quickly
        if request.method == "OPTIONS":
            headers = {
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, Accept, Origin, X-Requested-With",
                "Access-Control-Max-Age": "86400",
            }
            if origin in allowed_origins:
                headers["Access-Control-Allow-Origin"] = origin
            return Response(content="", status_code=200, headers=headers)

        response = await call_next(request)
        if origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With"
        return response

    print(f"[OK] CORS configured; allowed origins: {allowed_origins}")

