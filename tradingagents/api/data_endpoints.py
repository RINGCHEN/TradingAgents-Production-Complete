#!/usr/bin/env python3
"""
數據 API 端點 (Data API Endpoints)
天工 (TianGong) - 前端所需的數據 API

此模組提供前端所需的數據 API 端點，包含：
1. 股票搜尋 API
2. 市場監控 API
3. 分析管理 API
4. 數據查詢 API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user
from ..utils.user_context import UserContext
from ..utils.logging_config import get_api_logger
from ..utils.error_handler import handle_error

# 依賴注入函數
def get_data_orchestrator(request: Request):
    """獲取數據編排器實例"""
    return getattr(request.app.state, 'data_orchestrator', None)

# 配置日誌
api_logger = get_api_logger("data_endpoints")

# 創建路由器
router = APIRouter(prefix="/data", tags=["數據服務"])

# ==================== 數據模型 ====================

class StockSearchRequest(BaseModel):
    """股票搜尋請求模型"""
    query: str = Field(..., description="搜尋關鍵詞", min_length=1, max_length=50)
    market: Optional[str] = Field(None, description="市場篩選", pattern="^(TWS|US|HK|ALL)$")
    limit: int = Field(20, description="返回數量限制", ge=1, le=100)
    include_delisted: bool = Field(False, description="是否包含下市股票")


class StockInfo(BaseModel):
    """股票信息模型"""
    symbol: str = Field(..., description="股票代號")
    name: str = Field(..., description="股票名稱")
    market: str = Field(..., description="市場")
    exchange: str = Field(..., description="交易所")
    currency: str = Field(..., description="貨幣")
    sector: Optional[str] = Field(None, description="行業")
    industry: Optional[str] = Field(None, description="產業")
    market_cap: Optional[float] = Field(None, description="市值")
    is_active: bool = Field(True, description="是否活躍")


class StockSearchResponse(BaseModel):
    """股票搜尋響應模型"""
    query: str = Field(..., description="搜尋關鍵詞")
    total_results: int = Field(..., description="總結果數")
    results: List[StockInfo] = Field(..., description="搜尋結果")
    search_time: float = Field(..., description="搜尋耗時（秒）")


class MarketDataRequest(BaseModel):
    """市場數據請求模型"""
    symbols: List[str] = Field(..., description="股票代號列表", max_items=50)
    data_types: List[str] = Field(
        ["price"], 
        description="數據類型列表 (price, profile, news, financials)"
    )
    start_date: Optional[datetime] = Field(None, description="開始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")


class MarketDataPoint(BaseModel):
    """市場數據點模型"""
    symbol: str = Field(..., description="股票代號")
    timestamp: datetime = Field(..., description="時間戳")
    data_type: str = Field(..., description="數據類型")
    data: Dict[str, Any] = Field(..., description="數據內容")
    source: str = Field(..., description="數據源")
    quality: str = Field(..., description="數據質量")


class MarketDataResponse(BaseModel):
    """市場數據響應模型"""
    request_id: str = Field(..., description="請求ID")
    symbols: List[str] = Field(..., description="請求的股票代號")
    data_points: List[MarketDataPoint] = Field(..., description="數據點列表")
    total_points: int = Field(..., description="總數據點數")
    processing_time: float = Field(..., description="處理耗時（秒）")


class AnalysisTaskRequest(BaseModel):
    """分析任務請求模型"""
    symbol: str = Field(..., description="股票代號")
    analysis_types: List[str] = Field(
        ["fundamental"], 
        description="分析類型列表 (fundamental, technical, news, sentiment, risk)"
    )
    preferred_analysts: Optional[List[str]] = Field(None, description="指定分析師")
    priority: str = Field("normal", description="任務優先級", pattern="^(low|normal|high|urgent)$")
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="額外上下文")


class AnalysisTaskInfo(BaseModel):
    """分析任務信息模型"""
    task_id: str = Field(..., description="任務ID")
    symbol: str = Field(..., description="股票代號")
    analysis_types: List[str] = Field(..., description="分析類型")
    status: str = Field(..., description="任務狀態")
    progress: float = Field(..., description="進度百分比")
    assigned_analysts: List[str] = Field(..., description="分配的分析師")
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")
    estimated_completion: Optional[datetime] = Field(None, description="預計完成時間")


class AnalysisTaskResponse(BaseModel):
    """分析任務響應模型"""
    task: AnalysisTaskInfo = Field(..., description="任務信息")
    message: str = Field(..., description="響應消息")


# ==================== 股票搜尋 API ====================

@router.post("/stocks/search", response_model=StockSearchResponse, summary="股票搜尋")
async def search_stocks(
    request: StockSearchRequest,
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    搜尋股票信息
    
    支持按股票代號、名稱、行業等條件搜尋股票
    """
    try:
        start_time = datetime.now()
        
        # 記錄搜尋請求
        api_logger.info("股票搜尋請求", extra={
            'user_id': current_user.user_id,
            'query': request.query,
            'market': request.market,
            'limit': request.limit
        })
        
        # 執行搜尋（模擬實現）
        search_results = []
        
        # 這裡應該調用數據編排器的搜尋功能
        # 目前使用模擬數據
        if request.query.isdigit() and len(request.query) == 4:
            # 台股代號搜尋
            search_results.append(StockInfo(
                symbol=request.query,
                name=f"台股 {request.query}",
                market="TWS",
                exchange="TWSE",
                currency="TWD",
                sector="Technology",
                industry="Semiconductors",
                market_cap=1000000000.0,
                is_active=True
            ))
        elif request.query.isalpha():
            # 美股代號搜尋
            search_results.append(StockInfo(
                symbol=request.query.upper(),
                name=f"US Stock {request.query.upper()}",
                market="US",
                exchange="NASDAQ",
                currency="USD",
                sector="Technology",
                industry="Software",
                market_cap=5000000000.0,
                is_active=True
            ))
        
        # 計算搜尋時間
        search_time = (datetime.now() - start_time).total_seconds()
        
        response = StockSearchResponse(
            query=request.query,
            total_results=len(search_results),
            results=search_results,
            search_time=search_time
        )
        
        api_logger.info("股票搜尋完成", extra={
            'user_id': current_user.user_id,
            'query': request.query,
            'results_count': len(search_results),
            'search_time': search_time
        })
        
        return response
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/api/data/stocks/search',
            'user_id': current_user.user_id,
            'request': request.dict()
        })
        
        api_logger.error("股票搜尋失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'query': request.query
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="股票搜尋服務暫時不可用"
        )


@router.get("/stocks/{symbol}", response_model=StockInfo, summary="獲取股票詳情")
async def get_stock_info(
    symbol: str,
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    獲取指定股票的詳細信息
    """
    try:
        api_logger.info("股票詳情查詢", extra={
            'user_id': current_user.user_id,
            'symbol': symbol
        })
        
        # 這裡應該調用數據編排器獲取股票信息
        # 目前使用模擬數據
        if symbol.isdigit() and len(symbol) == 4:
            stock_info = StockInfo(
                symbol=symbol,
                name=f"台股 {symbol}",
                market="TWS",
                exchange="TWSE",
                currency="TWD",
                sector="Technology",
                industry="Semiconductors",
                market_cap=1000000000.0,
                is_active=True
            )
        elif symbol.isalpha():
            stock_info = StockInfo(
                symbol=symbol.upper(),
                name=f"US Stock {symbol.upper()}",
                market="US",
                exchange="NASDAQ",
                currency="USD",
                sector="Technology",
                industry="Software",
                market_cap=5000000000.0,
                is_active=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="股票不存在"
            )
        
        return stock_info
        
    except HTTPException:
        raise
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/api/data/stocks/{symbol}',
            'user_id': current_user.user_id,
            'symbol': symbol
        })
        
        api_logger.error("股票詳情查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'symbol': symbol
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="股票詳情查詢服務暫時不可用"
        )


# ==================== 市場監控 API ====================

@router.post("/market/data", response_model=MarketDataResponse, summary="獲取市場數據")
async def get_market_data(
    request: MarketDataRequest,
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    獲取多個股票的市場數據
    
    支持批量獲取股票價格、公司資料、新聞等數據
    """
    try:
        start_time = datetime.now()
        request_id = f"req_{int(start_time.timestamp())}"
        
        api_logger.info("市場數據請求", extra={
            'user_id': current_user.user_id,
            'request_id': request_id,
            'symbols': request.symbols,
            'data_types': request.data_types
        })
        
        # 生成模擬數據點
        data_points = []
        for symbol in request.symbols:
            for data_type in request.data_types:
                data_point = MarketDataPoint(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    data_type=data_type,
                    data={
                        "price": 100.0 + hash(symbol) % 100,
                        "volume": 1000000,
                        "change": 1.5,
                        "change_percent": 1.52
                    } if data_type == "price" else {
                        "company_name": f"Company {symbol}",
                        "sector": "Technology",
                        "employees": 10000
                    },
                    source="finmind" if symbol.isdigit() else "finnhub",
                    quality="high"
                )
                data_points.append(data_point)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = MarketDataResponse(
            request_id=request_id,
            symbols=request.symbols,
            data_points=data_points,
            total_points=len(data_points),
            processing_time=processing_time
        )
        
        api_logger.info("市場數據獲取完成", extra={
            'user_id': current_user.user_id,
            'request_id': request_id,
            'data_points_count': len(data_points),
            'processing_time': processing_time
        })
        
        return response
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/api/data/market/data',
            'user_id': current_user.user_id,
            'request': request.dict()
        })
        
        api_logger.error("市場數據獲取失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="市場數據服務暫時不可用"
        )


@router.get("/market/status", summary="獲取市場狀態")
async def get_market_status(
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    獲取各個市場的開市狀態和基本信息
    """
    try:
        api_logger.info("市場狀態查詢", extra={
            'user_id': current_user.user_id
        })
        
        # 模擬市場狀態數據
        market_status = {
            "markets": {
                "TWS": {
                    "name": "台灣證券交易所",
                    "timezone": "Asia/Taipei",
                    "is_open": True,
                    "next_open": "2025-08-05T09:00:00+08:00",
                    "next_close": "2025-08-04T13:30:00+08:00",
                    "trading_hours": "09:00-13:30"
                },
                "US": {
                    "name": "美國股市",
                    "timezone": "America/New_York",
                    "is_open": False,
                    "next_open": "2025-08-04T09:30:00-05:00",
                    "next_close": "2025-08-04T16:00:00-05:00",
                    "trading_hours": "09:30-16:00"
                },
                "HK": {
                    "name": "香港交易所",
                    "timezone": "Asia/Hong_Kong",
                    "is_open": True,
                    "next_open": "2025-08-05T09:30:00+08:00",
                    "next_close": "2025-08-04T16:00:00+08:00",
                    "trading_hours": "09:30-16:00"
                }
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return market_status
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/api/data/market/status',
            'user_id': current_user.user_id
        })
        
        api_logger.error("市場狀態查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="市場狀態查詢服務暫時不可用"
        )


# ==================== 分析管理 API ====================

@router.post("/analysis/tasks", response_model=AnalysisTaskResponse, summary="創建分析任務")
async def create_analysis_task(
    request: AnalysisTaskRequest,
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    創建新的分析任務
    
    基於指定的股票和分析類型創建分析任務
    """
    try:
        task_id = f"task_{int(datetime.now().timestamp())}"
        
        api_logger.info("分析任務創建", extra={
            'user_id': current_user.user_id,
            'task_id': task_id,
            'symbol': request.symbol,
            'analysis_types': request.analysis_types
        })
        
        # 創建任務信息
        task_info = AnalysisTaskInfo(
            task_id=task_id,
            symbol=request.symbol,
            analysis_types=request.analysis_types,
            status="pending",
            progress=0.0,
            assigned_analysts=request.preferred_analysts or ["fundamentals_analyst"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
            estimated_completion=datetime.now() + timedelta(minutes=5)
        )
        
        response = AnalysisTaskResponse(
            task=task_info,
            message="分析任務創建成功"
        )
        
        api_logger.info("分析任務創建完成", extra={
            'user_id': current_user.user_id,
            'task_id': task_id,
            'symbol': request.symbol
        })
        
        return response
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/api/data/analysis/tasks',
            'user_id': current_user.user_id,
            'request': request.dict()
        })
        
        api_logger.error("分析任務創建失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'symbol': request.symbol
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析任務創建服務暫時不可用"
        )


@router.get("/analysis/tasks/{task_id}", response_model=AnalysisTaskInfo, summary="獲取分析任務狀態")
async def get_analysis_task(
    task_id: str,
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    獲取指定分析任務的狀態和進度
    """
    try:
        api_logger.info("分析任務狀態查詢", extra={
            'user_id': current_user.user_id,
            'task_id': task_id
        })
        
        # 模擬任務信息
        task_info = AnalysisTaskInfo(
            task_id=task_id,
            symbol="2330",
            analysis_types=["fundamental"],
            status="running",
            progress=65.0,
            assigned_analysts=["fundamentals_analyst"],
            created_at=datetime.now() - timedelta(minutes=3),
            updated_at=datetime.now(),
            estimated_completion=datetime.now() + timedelta(minutes=2)
        )
        
        return task_info
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': f'/api/data/analysis/tasks/{task_id}',
            'user_id': current_user.user_id,
            'task_id': task_id
        })
        
        api_logger.error("分析任務狀態查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id,
            'task_id': task_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析任務狀態查詢服務暫時不可用"
        )


@router.get("/analysis/tasks", summary="獲取分析任務列表")
async def list_analysis_tasks(
    status: Optional[str] = Query(None, description="任務狀態篩選"),
    symbol: Optional[str] = Query(None, description="股票代號篩選"),
    limit: int = Query(20, description="返回數量限制", ge=1, le=100),
    current_user: UserContext = Depends(get_current_user),
    data_orchestrator = Depends(get_data_orchestrator)
):
    """
    獲取用戶的分析任務列表
    """
    try:
        api_logger.info("分析任務列表查詢", extra={
            'user_id': current_user.user_id,
            'status_filter': status,
            'symbol_filter': symbol,
            'limit': limit
        })
        
        # 模擬任務列表
        tasks = [
            AnalysisTaskInfo(
                task_id=f"task_{i}",
                symbol="2330" if i % 2 == 0 else "AAPL",
                analysis_types=["fundamental"],
                status="completed" if i % 3 == 0 else "running",
                progress=100.0 if i % 3 == 0 else 50.0 + (i * 10) % 50,
                assigned_analysts=["fundamentals_analyst"],
                created_at=datetime.now() - timedelta(hours=i),
                updated_at=datetime.now() - timedelta(minutes=i * 10),
                estimated_completion=None if i % 3 == 0 else datetime.now() + timedelta(minutes=5 - i)
            )
            for i in range(min(limit, 10))
        ]
        
        # 應用篩選
        if status:
            tasks = [t for t in tasks if t.status == status]
        if symbol:
            tasks = [t for t in tasks if t.symbol == symbol]
        
        return {
            "tasks": tasks,
            "total": len(tasks),
            "filtered": bool(status or symbol)
        }
        
    except Exception as e:
        error_info = await handle_error(e, {
            'endpoint': '/api/data/analysis/tasks',
            'user_id': current_user.user_id,
            'filters': {'status': status, 'symbol': symbol}
        })
        
        api_logger.error("分析任務列表查詢失敗", extra={
            'error_id': error_info.error_id,
            'user_id': current_user.user_id
        })
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析任務列表查詢服務暫時不可用"
        )


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

