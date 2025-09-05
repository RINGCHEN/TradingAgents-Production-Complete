#!/usr/bin/env python3
"""
全新的簡單投資組合API
完全重新編寫，不依賴任何舊代碼
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import time

# 創建路由器
router = APIRouter()

# 簡單的資料模型
class SimplePortfolio(BaseModel):
    name: str
    description: str = ""

class SimpleHolding(BaseModel):
    symbol: str
    quantity: float
    price: float

# 記憶體存儲（實際應用中會用資料庫）
portfolios_data = {}
holdings_data = {}

# 簡單的CORS處理
def add_cors_headers(response: JSONResponse, origin: str = None) -> JSONResponse:
    """為響應添加CORS headers"""
    if origin and origin in ["https://03king.com", "https://03king.web.app", "https://www.03king.com"]:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin"
    return response

@router.get("/simple-portfolios")
async def get_simple_portfolios():
    """獲取所有投資組合"""
    try:
        data = {
            "success": True,
            "portfolios": list(portfolios_data.values()),
            "timestamp": time.time()
        }
        response = JSONResponse(content=data)
        return add_cors_headers(response)
    except Exception as e:
        data = {"success": False, "error": str(e), "portfolios": []}
        response = JSONResponse(content=data, status_code=500)
        return add_cors_headers(response)

@router.post("/simple-portfolios")
async def create_simple_portfolio(portfolio: SimplePortfolio):
    """創建新的投資組合"""
    try:
        portfolio_id = f"portfolio_{int(time.time())}"
        portfolios_data[portfolio_id] = {
            "id": portfolio_id,
            "name": portfolio.name,
            "description": portfolio.description,
            "created_at": time.time(),
            "holdings": []
        }
        
        data = {
            "success": True,
            "portfolio": portfolios_data[portfolio_id],
            "message": "投資組合創建成功"
        }
        response = JSONResponse(content=data)
        return add_cors_headers(response)
    except Exception as e:
        data = {"success": False, "error": str(e)}
        response = JSONResponse(content=data, status_code=500)
        return add_cors_headers(response)

@router.get("/simple-portfolios/{portfolio_id}/holdings")
async def get_simple_holdings(portfolio_id: str):
    """獲取投資組合的持股"""
    try:
        if portfolio_id not in portfolios_data:
            data = {"success": False, "error": "投資組合不存在", "holdings": []}
            response = JSONResponse(content=data, status_code=404)
            return add_cors_headers(response)
        
        holdings = holdings_data.get(portfolio_id, [])
        data = {
            "success": True,
            "holdings": holdings,
            "portfolio_id": portfolio_id
        }
        response = JSONResponse(content=data)
        return add_cors_headers(response)
    except Exception as e:
        data = {"success": False, "error": str(e), "holdings": []}
        response = JSONResponse(content=data, status_code=500)
        return add_cors_headers(response)

@router.post("/simple-portfolios/{portfolio_id}/holdings")
async def add_simple_holding(portfolio_id: str, holding: SimpleHolding):
    """添加持股到投資組合"""
    try:
        if portfolio_id not in portfolios_data:
            data = {"success": False, "error": "投資組合不存在"}
            response = JSONResponse(content=data, status_code=404)
            return add_cors_headers(response)
        
        if portfolio_id not in holdings_data:
            holdings_data[portfolio_id] = []
        
        holding_data = {
            "id": f"holding_{int(time.time())}",
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "price": holding.price,
            "value": holding.quantity * holding.price,
            "created_at": time.time()
        }
        
        holdings_data[portfolio_id].append(holding_data)
        
        data = {
            "success": True,
            "holding": holding_data,
            "message": "持股添加成功"
        }
        response = JSONResponse(content=data)
        return add_cors_headers(response)
    except Exception as e:
        data = {"success": False, "error": str(e)}
        response = JSONResponse(content=data, status_code=500)
        return add_cors_headers(response)

@router.options("/simple-portfolios")
@router.options("/simple-portfolios/{portfolio_id}")
@router.options("/simple-portfolios/{portfolio_id}/holdings")
async def simple_portfolios_options():
    """處理OPTIONS預檢請求"""
    response = JSONResponse(content={"status": "OK"})
    return add_cors_headers(response)

# 健康檢查
@router.get("/simple-portfolios/health")
async def simple_portfolios_health():
    """健康檢查端點"""
    data = {
        "status": "healthy",
        "service": "simple-portfolios",
        "timestamp": time.time(),
        "portfolios_count": len(portfolios_data),
        "total_holdings": sum(len(h) for h in holdings_data.values())
    }
    response = JSONResponse(content=data)
    return add_cors_headers(response)