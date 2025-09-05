#!/usr/bin/env python3
"""
最簡單直接的CORS修復
"""

cors_fix_code = '''
# 緊急CORS修復 - 在app.py最前面添加
from starlette.middleware.base import BaseHTTPMiddleware

class EmergencyCORSMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_origins):
        super().__init__(app)
        self.allowed_origins = allowed_origins
    
    async def dispatch(self, request, call_next):
        # 處理OPTIONS預檢請求
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            if origin in self.allowed_origins:
                from fastapi.responses import Response
                headers = {
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-Test-Client, Cache-Control, DNT, If-Modified-Since, Range, User-Agent",
                    "Access-Control-Max-Age": "86400"
                }
                return Response(content="OK", headers=headers)
        
        # 處理其他請求
        response = await call_next(request)
        origin = request.headers.get("origin")
        
        if origin in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, X-Test-Client, Cache-Control, DNT, If-Modified-Since, Range, User-Agent"
        
        return response

# 在app創建後立即添加
app.add_middleware(EmergencyCORSMiddleware, allowed_origins=allowed_origins)
'''

print("🚨 緊急CORS修復代碼生成")
print("需要在 tradingagents/app.py 中的 app = FastAPI(...) 之後立即添加：")
print(cors_fix_code)