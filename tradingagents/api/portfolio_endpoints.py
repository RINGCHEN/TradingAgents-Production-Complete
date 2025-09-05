#!/usr/bin/env python3
"""
投資組合 API 端點
為用戶提供完整的投資組合管理功能
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncpg
import json
import logging

from ..auth.dependencies import get_current_user, CurrentUser
from ..utils.logging_config import get_api_logger

# 配置日誌
logger = get_api_logger("portfolio")

# 創建路由器
router = APIRouter(tags=["portfolio"])

# ==================== 數據模型 ====================

class HoldingCreate(BaseModel):
    """創建持股請求模型"""
    symbol: str = Field(..., min_length=1, max_length=20, description="股票代碼")
    quantity: float = Field(..., gt=0, description="持有數量")
    averagePrice: float = Field(..., gt=0, description="平均買入價格", alias="average_price")
    purchaseDate: Optional[str] = Field(None, description="購買日期", alias="purchase_date")
    
    class Config:
        allow_population_by_field_name = True

class HoldingResponse(BaseModel):
    """持股回應模型"""
    id: str
    symbol: str
    companyName: Optional[str] = None
    market: Optional[str] = None
    quantity: float
    averagePrice: float
    currentPrice: Optional[float] = None
    totalValue: Optional[float] = None
    totalCost: float
    unrealizedGain: Optional[float] = None
    unrealizedGainPercent: Optional[float] = None
    dayChange: Optional[float] = None
    dayChangePercent: Optional[float] = None
    weight: Optional[float] = None
    sector: Optional[str] = None
    addedAt: str
    lastUpdated: str

class PortfolioCreate(BaseModel):
    """創建投資組合請求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="投資組合名稱")
    description: Optional[str] = Field(None, max_length=500, description="投資組合描述")
    initial_capital: Optional[float] = Field(None, gt=0, description="初始資本")

class PortfolioResponse(BaseModel):
    """投資組合回應模型"""
    id: str
    name: str
    description: Optional[str] = None
    totalValue: float
    totalCost: float
    totalGain: float
    totalGainPercent: float
    dayChange: Optional[float] = None
    dayChangePercent: Optional[float] = None
    holdings: List[HoldingResponse] = []
    createdAt: str
    updatedAt: str

class PortfolioAnalysis(BaseModel):
    """投資組合分析模型"""
    riskScore: float
    diversificationScore: float
    sectorAllocation: Dict[str, float]
    marketAllocation: Dict[str, float]
    recommendations: List[str]
    riskFactors: List[str]
    opportunities: List[str]
    overallRating: str
    expectedReturn: float
    targetReturn: float

# ==================== 資料庫連接 ====================

async def get_db_connection():
    """獲取資料庫連接"""
    try:
        return await asyncpg.connect(
            host="35.194.205.200",
            port=5432,
            database="tradingagents", 
            user="postgres",
            password="secure_postgres_password_2024"
        )
    except Exception as e:
        logger.error(f"資料庫連接失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="資料庫服務暫時無法使用"
        )

# ==================== 輔助函數 ====================

async def create_holdings_table_if_not_exists():
    """創建holdings表（如果不存在）"""
    conn = await get_db_connection()
    try:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_holdings (
                id SERIAL PRIMARY KEY,
                portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
                symbol VARCHAR(20) NOT NULL,
                company_name VARCHAR(200),
                market VARCHAR(50) DEFAULT 'TWSE',
                quantity DECIMAL(15,6) NOT NULL,
                average_price DECIMAL(15,4) NOT NULL,
                current_price DECIMAL(15,4),
                total_cost DECIMAL(20,4) GENERATED ALWAYS AS (quantity * average_price) STORED,
                total_value DECIMAL(20,4),
                unrealized_gain DECIMAL(20,4),
                unrealized_gain_percent DECIMAL(8,4),
                day_change DECIMAL(15,4),
                day_change_percent DECIMAL(8,4),
                weight DECIMAL(8,4),
                sector VARCHAR(100),
                purchase_date DATE DEFAULT CURRENT_DATE,
                added_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                
                UNIQUE(portfolio_id, symbol)
            );
        ''')
        
        # 創建索引
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_holdings_portfolio_id ON portfolio_holdings(portfolio_id);
        ''')
        await conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_holdings_symbol ON portfolio_holdings(symbol);
        ''')
        
        logger.info("portfolio_holdings表創建/檢查完成")
        
    except Exception as e:
        logger.error(f"創建holdings表失敗: {e}")
        raise
    finally:
        await conn.close()

async def get_stock_info(symbol: str) -> Dict[str, Any]:
    """獲取股票基本資訊"""
    # 模擬股票資訊獲取
    # 實際應該從API或資料庫獲取
    return {
        "companyName": f"{symbol} 公司",
        "market": "TWSE",
        "currentPrice": 100.0,
        "sector": "科技業"
    }

async def calculate_portfolio_metrics(portfolio_id: int):
    """計算投資組合指標"""
    conn = await get_db_connection()
    try:
        # 查詢所有持股
        holdings = await conn.fetch('''
            SELECT * FROM portfolio_holdings WHERE portfolio_id = $1
        ''', portfolio_id)
        
        total_value = 0
        total_cost = 0
        
        for holding in holdings:
            current_price = holding['current_price'] or holding['average_price']
            holding_value = holding['quantity'] * current_price
            holding_cost = holding['quantity'] * holding['average_price']
            
            total_value += holding_value
            total_cost += holding_cost
            
            # 更新持股數據
            await conn.execute('''
                UPDATE portfolio_holdings 
                SET 
                    current_price = $1,
                    total_value = $2,
                    unrealized_gain = $3,
                    unrealized_gain_percent = $4,
                    updated_at = NOW()
                WHERE id = $5
            ''', 
            current_price,
            holding_value, 
            holding_value - holding_cost,
            ((holding_value - holding_cost) / holding_cost * 100) if holding_cost > 0 else 0,
            holding['id']
            )
        
        # 更新投資組合總計
        total_gain = total_value - total_cost
        gain_percent = (total_gain / total_cost * 100) if total_cost > 0 else 0
        
        await conn.execute('''
            UPDATE portfolios 
            SET 
                current_value = $1,
                total_return = $2,
                return_percentage = $3,
                updated_at = NOW()
            WHERE id = $4
        ''', total_value, total_gain, gain_percent, portfolio_id)
        
        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_gain": total_gain,
            "gain_percent": gain_percent
        }
        
    finally:
        await conn.close()

# ==================== API 端點 ====================

@router.get("/portfolios", response_model=List[PortfolioResponse])
async def get_portfolios(current_user: CurrentUser):
    """獲取用戶的投資組合列表"""
    
    # 確保holdings表存在
    await create_holdings_table_if_not_exists()
    
    conn = await get_db_connection()
    try:
        # 查詢用戶的投資組合
        portfolios = await conn.fetch('''
            SELECT 
                id, name, description,
                COALESCE(current_value, 0) as current_value,
                COALESCE(initial_capital, 0) as total_cost,
                COALESCE(total_return, 0) as total_return,
                COALESCE(return_percentage, 0) as return_percentage,
                created_at, updated_at
            FROM portfolios 
            WHERE user_id = $1 
            ORDER BY created_at DESC
        ''', current_user.id)
        
        result = []
        for portfolio in portfolios:
            # 查詢持股資料
            holdings = await conn.fetch('''
                SELECT 
                    id, symbol, company_name, market, quantity, average_price,
                    COALESCE(current_price, average_price) as current_price,
                    COALESCE(total_value, quantity * average_price) as total_value,
                    total_cost, unrealized_gain, unrealized_gain_percent,
                    day_change, day_change_percent, weight, sector,
                    added_at, updated_at
                FROM portfolio_holdings 
                WHERE portfolio_id = $1
                ORDER BY added_at DESC
            ''', portfolio['id'])
            
            holdings_list = []
            for holding in holdings:
                holdings_list.append(HoldingResponse(
                    id=str(holding['id']),
                    symbol=holding['symbol'],
                    companyName=holding['company_name'],
                    market=holding['market'],
                    quantity=float(holding['quantity']),
                    averagePrice=float(holding['average_price']),
                    currentPrice=float(holding['current_price']) if holding['current_price'] else None,
                    totalValue=float(holding['total_value']) if holding['total_value'] else None,
                    totalCost=float(holding['total_cost']),
                    unrealizedGain=float(holding['unrealized_gain']) if holding['unrealized_gain'] else None,
                    unrealizedGainPercent=float(holding['unrealized_gain_percent']) if holding['unrealized_gain_percent'] else None,
                    dayChange=float(holding['day_change']) if holding['day_change'] else None,
                    dayChangePercent=float(holding['day_change_percent']) if holding['day_change_percent'] else None,
                    weight=float(holding['weight']) if holding['weight'] else None,
                    sector=holding['sector'],
                    addedAt=holding['added_at'].isoformat(),
                    lastUpdated=holding['updated_at'].isoformat()
                ))
            
            result.append(PortfolioResponse(
                id=str(portfolio['id']),
                name=portfolio['name'],
                description=portfolio['description'],
                totalValue=float(portfolio['current_value']),
                totalCost=float(portfolio['total_cost']),
                totalGain=float(portfolio['total_return']),
                totalGainPercent=float(portfolio['return_percentage']),
                dayChange=0.0,  # 模擬數據
                dayChangePercent=0.0,  # 模擬數據
                holdings=holdings_list,
                createdAt=portfolio['created_at'].isoformat(),
                updatedAt=portfolio['updated_at'].isoformat()
            ))
        
        logger.info(f"用戶 {current_user.email} 查詢投資組合，返回 {len(result)} 個組合")
        return result
        
    except Exception as e:
        logger.error(f"查詢投資組合失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="查詢投資組合失敗"
        )
    finally:
        await conn.close()

@router.post("/portfolio", response_model=Dict[str, Any])
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user: CurrentUser
):
    """創建新的投資組合"""
    
    conn = await get_db_connection()
    try:
        # 檢查用戶是否已有同名投資組合
        existing = await conn.fetchrow('''
            SELECT id FROM portfolios 
            WHERE user_id = $1 AND name = $2
        ''', current_user.id, portfolio_data.name)
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="已存在同名的投資組合"
            )
        
        # 創建投資組合
        portfolio = await conn.fetchrow('''
            INSERT INTO portfolios (user_id, name, description, initial_capital)
            VALUES ($1, $2, $3, $4)
            RETURNING id, name, description, initial_capital, created_at, updated_at
        ''', current_user.id, portfolio_data.name, portfolio_data.description, portfolio_data.initial_capital)
        
        portfolio_response = PortfolioResponse(
            id=str(portfolio['id']),
            name=portfolio['name'],
            description=portfolio['description'],
            totalValue=0.0,
            totalCost=float(portfolio['initial_capital']) if portfolio['initial_capital'] else 0.0,
            totalGain=0.0,
            totalGainPercent=0.0,
            holdings=[],
            createdAt=portfolio['created_at'].isoformat(),
            updatedAt=portfolio['updated_at'].isoformat()
        )
        
        logger.info(f"用戶 {current_user.email} 創建投資組合: {portfolio_data.name}")
        
        return {
            "success": True,
            "message": "投資組合創建成功",
            "portfolio": portfolio_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"創建投資組合失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="創建投資組合失敗"
        )
    finally:
        await conn.close()

@router.post("/portfolio/{portfolio_id}/holdings", response_model=Dict[str, Any])
async def add_holding(
    portfolio_id: int,
    holding_data: HoldingCreate,
    current_user: CurrentUser
):
    """添加持股到投資組合"""
    
    # 確保holdings表存在
    await create_holdings_table_if_not_exists()
    
    conn = await get_db_connection()
    try:
        # 驗證投資組合所有權
        portfolio = await conn.fetchrow('''
            SELECT id FROM portfolios WHERE id = $1 AND user_id = $2
        ''', portfolio_id, current_user.id)
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="投資組合不存在或無權限"
            )
        
        # 獲取股票資訊
        stock_info = await get_stock_info(holding_data.symbol)
        
        # 檢查是否已存在該持股
        existing = await conn.fetchrow('''
            SELECT id FROM portfolio_holdings 
            WHERE portfolio_id = $1 AND symbol = $2
        ''', portfolio_id, holding_data.symbol)
        
        if existing:
            # 更新現有持股（加權平均）
            current_holding = await conn.fetchrow('''
                SELECT quantity, average_price FROM portfolio_holdings
                WHERE id = $1
            ''', existing['id'])
            
            old_quantity = float(current_holding['quantity'])
            old_price = float(current_holding['average_price'])
            new_quantity = holding_data.quantity
            new_price = holding_data.averagePrice
            
            total_quantity = old_quantity + new_quantity
            weighted_price = ((old_quantity * old_price) + (new_quantity * new_price)) / total_quantity
            
            await conn.execute('''
                UPDATE portfolio_holdings 
                SET 
                    quantity = $1,
                    average_price = $2,
                    updated_at = NOW()
                WHERE id = $3
            ''', total_quantity, weighted_price, existing['id'])
            
            holding_id = existing['id']
        else:
            # 創建新持股
            holding_id = await conn.fetchval('''
                INSERT INTO portfolio_holdings (
                    portfolio_id, symbol, company_name, market, quantity, average_price
                ) VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            ''', 
            portfolio_id, 
            holding_data.symbol, 
            stock_info['companyName'],
            stock_info['market'],
            holding_data.quantity, 
            holding_data.averagePrice
            )
        
        # 重新計算投資組合指標
        await calculate_portfolio_metrics(portfolio_id)
        
        # 查詢更新後的持股資料
        updated_holding = await conn.fetchrow('''
            SELECT * FROM portfolio_holdings WHERE id = $1
        ''', holding_id)
        
        holding_response = HoldingResponse(
            id=str(updated_holding['id']),
            symbol=updated_holding['symbol'],
            companyName=updated_holding['company_name'],
            market=updated_holding['market'],
            quantity=float(updated_holding['quantity']),
            averagePrice=float(updated_holding['average_price']),
            totalCost=float(updated_holding['total_cost']),
            addedAt=updated_holding['added_at'].isoformat(),
            lastUpdated=updated_holding['updated_at'].isoformat()
        )
        
        # 查詢更新後的投資組合資料
        updated_portfolio = await conn.fetchrow('''
            SELECT current_value, total_return, return_percentage 
            FROM portfolios WHERE id = $1
        ''', portfolio_id)
        
        logger.info(f"用戶 {current_user.email} 添加持股: {holding_data.symbol}")
        
        return {
            "success": True,
            "message": "持股添加成功",
            "holding": holding_response,
            "portfolio": {
                "totalValue": float(updated_portfolio['current_value']) if updated_portfolio['current_value'] else 0,
                "totalCost": 0,  # 需要重新計算
                "totalGain": float(updated_portfolio['total_return']) if updated_portfolio['total_return'] else 0,
                "totalGainPercent": float(updated_portfolio['return_percentage']) if updated_portfolio['return_percentage'] else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加持股失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加持股失敗"
        )
    finally:
        await conn.close()

@router.delete("/portfolio/{portfolio_id}/holdings/{holding_id}")
async def remove_holding(
    portfolio_id: int,
    holding_id: int,
    current_user: CurrentUser
):
    """刪除持股"""
    
    conn = await get_db_connection()
    try:
        # 驗證投資組合所有權
        portfolio = await conn.fetchrow('''
            SELECT id FROM portfolios WHERE id = $1 AND user_id = $2
        ''', portfolio_id, current_user.id)
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="投資組合不存在或無權限"
            )
        
        # 刪除持股
        result = await conn.execute('''
            DELETE FROM portfolio_holdings 
            WHERE id = $1 AND portfolio_id = $2
        ''', holding_id, portfolio_id)
        
        if result == "DELETE 0":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="持股不存在"
            )
        
        # 重新計算投資組合指標
        await calculate_portfolio_metrics(portfolio_id)
        
        logger.info(f"用戶 {current_user.email} 刪除持股ID: {holding_id}")
        
        return {"success": True, "message": "持股刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除持股失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除持股失敗"
        )
    finally:
        await conn.close()

@router.get("/portfolio/{portfolio_id}/analysis", response_model=PortfolioAnalysis)
async def get_portfolio_analysis(
    portfolio_id: int,
    current_user: CurrentUser
):
    """獲取投資組合分析"""
    
    conn = await get_db_connection()
    try:
        # 驗證投資組合所有權
        portfolio = await conn.fetchrow('''
            SELECT id FROM portfolios WHERE id = $1 AND user_id = $2
        ''', portfolio_id, current_user.id)
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="投資組合不存在或無權限"
            )
        
        # 模擬投資組合分析數據
        # 實際應該有更複雜的分析算法
        analysis = PortfolioAnalysis(
            riskScore=7.5,
            diversificationScore=6.8,
            sectorAllocation={"科技業": 60.0, "金融業": 30.0, "其他": 10.0},
            marketAllocation={"TWSE": 80.0, "OTC": 20.0},
            recommendations=[
                "建議增加金融股比重",
                "考慮分散至國際市場",
                "降低單一股票權重"
            ],
            riskFactors=[
                "科技股集中度過高",
                "缺乏防禦型股票"
            ],
            opportunities=[
                "ESG概念股投資機會",
                "dividend yield提升空間"
            ],
            overallRating="GOOD",
            expectedReturn=8.5,
            targetReturn=10.0
        )
        
        logger.info(f"用戶 {current_user.email} 查詢投資組合分析: {portfolio_id}")
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取投資組合分析失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="獲取投資組合分析失敗"
        )
    finally:
        await conn.close()

@router.delete("/portfolio/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    current_user: CurrentUser
):
    """刪除投資組合"""
    
    conn = await get_db_connection()
    try:
        # 驗證投資組合所有權
        portfolio = await conn.fetchrow('''
            SELECT id FROM portfolios WHERE id = $1 AND user_id = $2
        ''', portfolio_id, current_user.id)
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="投資組合不存在或無權限"
            )
        
        # 刪除投資組合（CASCADE會自動刪除相關持股）
        await conn.execute('''
            DELETE FROM portfolios WHERE id = $1
        ''', portfolio_id)
        
        logger.info(f"用戶 {current_user.email} 刪除投資組合: {portfolio_id}")
        
        return {"success": True, "message": "投資組合刪除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除投資組合失敗: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刪除投資組合失敗"
        )
    finally:
        await conn.close()