#!/usr/bin/env python3
"""
不老傳說 FastAPI Application
天工 (TianGong) - 統一的AI投資分析系統API入口

此應用程式提供統一的RESTful API接口，整合所有AI分析師和工作流引擎，
為用戶提供專業級的投資分析服務。

功能特色：
1. 統一的API接口設計
2. 多層次會員服務支援
3. 實時分析狀態推送
4. 完整的錯誤處理和監控
5. 高性能異步處理
6. Taiwan市場專業化服務
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime
import uuid
from contextlib import asynccontextmanager

# 導入TradingAgents組件
from .graph.trading_graph import TradingAgentsGraph, create_trading_graph
from .utils.user_context import UserContext, TierType, UserPermissions
from .agents.analysts.base_analyst import AnalysisState, AnalysisResult
from .utils.error_handler import get_error_handler, handle_error, get_user_friendly_message, ErrorInfo
from .utils.logging_config import get_api_logger, get_system_logger, get_security_logger
from .utils.performance_monitor import log_performance
from .utils.middleware import setup_middleware
from .auth.routes import router as auth_router
from .auth.dependencies import get_current_user, CurrentUser, GoldUser, DiamondUser
from .simple_cors import setup_simple_cors

# 導入所有現有的 API 端點路由器
from .api.user_endpoints import router as user_router
from .api.subscription_endpoints import router as subscription_router
from .api.payment_endpoints import router as payment_router
from .api.payuni_endpoints import router as payuni_router
from .api.replay_endpoints import router as replay_router # AI決策復盤API
# from .api.membership_endpoints import router as membership_router
from .api.ab_testing_endpoints import router as ab_testing_router
from .api.pricing_strategy_endpoints import router as pricing_router
from .api.upgrade_conversion_endpoints import router as upgrade_router
from .api.user_experience_endpoints import router as ux_router
from .api.international_market_endpoints import router as intl_router
from .api.data_endpoints import router as data_router
from .api.share_endpoints import router as share_router
from .api.analyst_endpoints import router as analyst_router
from .api.dialogue_endpoints import router as dialogue_router
from .api.personality_test_endpoints import router as personality_test_router
from .api.pay_per_use_endpoints import router as pay_per_use_router
from .api.alpha_insight_endpoints import router as alpha_insight_router
from .api.upgrade_recommendation_endpoints import router as upgrade_recommendation_router
from .api.value_validation_endpoints import router as value_validation_router
from .api.google_auth_endpoints import router as google_auth_router
from .api.portfolio_endpoints import router as portfolio_router  # 舊的投資組合API
# from .api.simple_portfolio import router as simple_portfolio_router  # 全新的投資組合API
# from .api.enhanced_portfolio_endpoints import router as enhanced_portfolio_router  # 🏆 專業級投資組合API

# 導入 Admin 管理路由器
from .admin.routers.config_router import router as config_router
from .admin.routers.basic_stats_router import router as basic_stats_router
from .admin.routers.user_management import router as user_management_router
from .admin.routers.system_monitor import router as system_monitor_router
from .admin.routers.service_coordinator import router as service_coordinator_router
from .admin.routers.analyst_management import router as analyst_management_router
from .admin.routers.content_management import router as content_management_router
# from .admin.routers.tts_management import router as tts_management_router
# from .admin.routers.complete_admin_endpoints import admin_router as complete_admin_router

# 配置日誌
logger = get_api_logger("app")
system_logger = get_system_logger("app")
security_logger = get_security_logger("app")

# 安全標頭中間件
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 添加安全標頭
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https: https://cdn.jsdelivr.net; connect-src 'self' https: wss: ws:; media-src 'self' data: blob:; frame-ancestors 'none';"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # 記錄安全標頭配置
        security_logger.info("Security headers applied", extra={
            'request_path': str(request.url.path),
            'security_headers_count': 7,
            'component': 'security_middleware'
        })
        
        return response

# 全局變量
trading_graph: Optional[TradingAgentsGraph] = None
data_orchestrator = None
active_connections: Dict[str, WebSocket] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時初始化
    global trading_graph, data_orchestrator
    system_logger.info("正在初始化不老傳說系統...", extra={
        'startup_phase': 'initialization',
        'component': 'app_lifecycle'
    })
    
    try:
        # 初始化數據編排器
        from .dataflows.data_orchestrator import DataOrchestrator
        data_orchestrator = DataOrchestrator()
        await data_orchestrator.initialize()
        system_logger.info("數據編排器初始化完成", extra={
            'startup_phase': 'data_orchestrator_ready',
            'component': 'app_lifecycle'
        })
        
        # 初始化交易圖
        trading_graph = await create_trading_graph()
        system_logger.info("不老傳說系統初始化完成", extra={
            'startup_phase': 'completed',
            'component': 'app_lifecycle',
            'system_ready': True
        })
    except Exception as e:
        error_info = await handle_error(e, {
            'phase': 'system_initialization',
            'component': 'app_lifecycle'
        })
        system_logger.critical(f"系統初始化失敗: {str(e)}", extra={
            'startup_phase': 'failed',
            'error_id': error_info.error_id,
            'component': 'app_lifecycle'
        })
        raise
    
    yield
    
    # 關閉時清理
    system_logger.info("正在關閉不老傳說系統...", extra={
        'shutdown_phase': 'started',
        'component': 'app_lifecycle'
    })
    
    try:
        # 清理數據編排器
        if data_orchestrator:
            await data_orchestrator.cleanup()
            system_logger.info("數據編排器清理完成", extra={
                'shutdown_phase': 'data_orchestrator_cleanup',
                'component': 'app_lifecycle'
            })
        
        # 清理交易圖
        if trading_graph:
            # 清理活躍會話
            trading_graph.cleanup_completed_sessions(max_age_hours=0)
        
        system_logger.info("系統關閉完成", extra={
            'shutdown_phase': 'completed',
            'component': 'app_lifecycle'
        })
    except Exception as e:
        error_info = await handle_error(e, {
            'phase': 'system_shutdown',
            'component': 'app_lifecycle'
        })
        system_logger.error(f"系統關閉時發生錯誤: {str(e)}", extra={
            'shutdown_phase': 'error',
            'error_id': error_info.error_id,
            'component': 'app_lifecycle'
        })

# 創建FastAPI應用程式
app = FastAPI(
    title="不老傳說 AI投資分析系統",
    description="專業級AI多代理人投資分析平台 - 天工(TianGong)優化版",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 使用簡化的CORS配置
setup_simple_cors(app)

# 設置自定義中間件
middleware_config = {
    'enable_request_logging': True,
    'enable_security': True,
    'enable_performance_monitoring': True,
    'enable_usage_tracking': True,
    'enable_error_recovery': True,
    'logging': {
        'log_body': False,
        'log_headers': True
    },
    'security': {
        'rate_limit_enabled': True,
        'max_requests_per_minute': 60,
        'blocked_ips': []
    },
    'performance': {
        'slow_request_threshold': 2.0,
        'memory_check_enabled': True
    },
    'error_recovery': {
        'auto_recovery_enabled': True,
        'circuit_breaker_enabled': True,
        'circuit_breaker_threshold': 5
    }
}

setup_middleware(app, middleware_config)

# 添加安全標頭中間件
app.add_middleware(SecurityHeadersMiddleware)

# 安全設置
security = HTTPBearer()

# 註冊路由
app.include_router(auth_router)

# 註冊所有現有的 API 端點路由器
app.include_router(user_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(payment_router, prefix="/api")
app.include_router(payuni_router, prefix="/api/v1")
app.include_router(replay_router) # AI決策復盤API - prefix已在router中定義
# app.include_router(membership_router, prefix="/api")
app.include_router(ab_testing_router, prefix="/api")
app.include_router(pricing_router, prefix="/api")
app.include_router(upgrade_router, prefix="/api")
app.include_router(ux_router, prefix="/api")
app.include_router(intl_router, prefix="/api")
app.include_router(data_router, prefix="/api")
app.include_router(share_router, prefix="/api")
app.include_router(analyst_router, prefix="/api")
app.include_router(dialogue_router, prefix="/api")
app.include_router(personality_test_router, prefix="/api")
app.include_router(pay_per_use_router, prefix="/api")
app.include_router(alpha_insight_router, prefix="/api")
app.include_router(upgrade_recommendation_router, prefix="/api")
app.include_router(value_validation_router, prefix="/api")
app.include_router(portfolio_router, prefix="/api/v1")  # 舊的投資組合 API 路由器
# app.include_router(simple_portfolio_router, prefix="/api")  # 全新的投資組合 API 路由器
# app.include_router(enhanced_portfolio_router)  # 🏆 專業級投資組合 API 路由器
app.include_router(google_auth_router)  # Google Auth 路由器已包含 /api/auth 前綴

# 註冊 Admin 管理路由器
app.include_router(config_router, prefix="/admin")
app.include_router(basic_stats_router)
app.include_router(user_management_router, prefix="/admin")
app.include_router(system_monitor_router, prefix="/admin")
app.include_router(service_coordinator_router, prefix="/admin")
app.include_router(analyst_management_router, prefix="/admin")
app.include_router(content_management_router, prefix="/admin")
# app.include_router(tts_management_router)  # TTS管理路由器已包含 /admin/tts 前綴
# app.include_router(complete_admin_router)  # 完整管理後台路由器已包含 /admin 前綴

# ==================== 依賴注入 ====================

def get_data_orchestrator():
    """獲取數據編排器實例"""
    global data_orchestrator
    if data_orchestrator is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="數據編排器未初始化"
        )
    return data_orchestrator

def get_trading_graph():
    """獲取交易圖實例"""
    global trading_graph
    if trading_graph is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="交易圖未初始化"
        )
    return trading_graph

# ==================== 數據模型 ====================

class AnalysisRequest(BaseModel):
    """分析請求模型"""
    stock_id: str = Field(..., description="股票代號", example="2330")
    preferred_analysts: Optional[List[str]] = Field(
        None, 
        description="指定分析師列表", 
        example=["risk_analyst", "investment_planner"]
    )
    enable_debate: Optional[bool] = Field(
        None, 
        description="是否啟用辯論機制"
    )
    additional_context: Optional[Dict[str, Any]] = Field(
        None, 
        description="額外上下文資訊"
    )

class AnalysisResponse(BaseModel):
    """分析回應模型"""
    session_id: str = Field(..., description="分析會話ID")
    status: str = Field(..., description="分析狀態")
    message: str = Field(..., description="回應訊息")
    estimated_time: Optional[int] = Field(None, description="預估完成時間(秒)")

class SessionStatusResponse(BaseModel):
    """會話狀態回應模型"""
    session_id: str
    stock_id: str
    current_phase: str
    overall_status: str
    progress_percentage: float
    start_time: str
    end_time: Optional[str] = None
    analyst_executions: Dict[str, Any]
    final_result: Optional[Dict[str, Any]] = None
    errors: List[str]
    warnings: List[str]

class SystemMetricsResponse(BaseModel):
    """系統指標回應模型"""
    active_sessions: int
    completed_sessions: int
    total_sessions: int
    average_execution_time: float
    available_analysts: List[str]
    system_uptime: float
    timestamp: str

class UserInfo(BaseModel):
    """用戶資訊模型"""
    user_id: str
    membership_tier: str = Field(..., description="會員等級: FREE, GOLD, DIAMOND")
    permissions: Optional[Dict[str, Any]] = None

# ==================== 依賴注入 ====================

# 用戶認證依賴項已移到 auth.dependencies 模組

async def get_trading_graph() -> TradingAgentsGraph:
    """獲取交易圖實例"""
    if trading_graph is None:
        raise HTTPException(
            status_code=503,
            detail="不老傳說系統尚未初始化"
        )
    return trading_graph

# ==================== API路由 ====================

@app.get("/", tags=["系統"])
async def root():
    """系統根路由"""
    return {
        "message": "不老傳說 AI投資分析系統",
        "version": "2.0.0",
        "powered_by": "天工(TianGong)",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/simple-test", tags=["測試"])
async def simple_test():
    """簡單測試路由，用於診斷路由問題"""
    return {
        "message": "Simple test route working",
        "timestamp": "2025-09-06",
        "status": "OK"
    }

@app.get("/health", tags=["系統"])
async def health_check():
    """健康檢查"""
    error_handler = get_error_handler()
    system_health = error_handler.get_system_health()
    
    services_status = {
        "trading_graph": trading_graph is not None,
        "active_sessions": len(trading_graph.active_sessions) if trading_graph else 0,
        "error_handler": True,
        "logging_system": True
    }
    
    overall_status = "healthy"
    if system_health['status'] in ['degraded', 'unhealthy']:
        overall_status = system_health['status']
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "services": services_status,
        "system_health": system_health,
        "uptime_seconds": (datetime.now() - datetime.now()).total_seconds()  # 簡化實現
    }


@app.get("/system/error-stats", tags=["系統監控"])
async def get_error_statistics(
    user: DiamondUser,  # 只有鑽石用戶可以查看錯誤統計
    hours: int = 24
):
    """獲取錯誤統計"""
    # 檢查用戶權限 (僅DIAMOND用戶可查看系統統計)
    if user.membership_tier != TierType.DIAMOND:
        security_logger.warning("非授權用戶嘗試訪問錯誤統計", extra={
            'user_id': user.user_id,
            'membership_tier': user.membership_tier.value,
            'attempted_endpoint': '/system/error-stats'
        })
        raise HTTPException(
            status_code=403,
            detail="需要DIAMOND會員權限才能查看系統統計"
        )
    
    error_handler = get_error_handler()
    stats = error_handler.get_error_statistics(hours)
    
    logger.info("錯誤統計查詢", extra={
        'user_id': user.user_id,
        'timeframe_hours': hours,
        'total_errors': stats['total_errors']
    })
    
    return stats

@app.post("/analysis/start", response_model=AnalysisResponse, tags=["分析服務"])
@log_performance()
async def start_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks,
    user: CurrentUser,
    graph: TradingAgentsGraph = Depends(get_trading_graph)
):
    """開始股票分析"""
    try:
        logger.info(f"用戶 {user.user_id} 請求分析股票 {request.stock_id}", extra={
            'user_id': user.user_id,
            'stock_symbol': request.stock_id,
            'membership_tier': user.membership_tier.value,
            'preferred_analysts': request.preferred_analysts,
            'enable_debate': request.enable_debate,
            'api_endpoint': '/analysis/start'
        })
        
        # 開始分析
        session_id = await graph.analyze_stock(
            stock_id=request.stock_id,
            user_context=user,
            preferred_analysts=request.preferred_analysts,
            enable_debate=request.enable_debate
        )
        
        # 添加WebSocket通知任務
        background_tasks.add_task(
            notify_analysis_progress, 
            session_id, 
            user.user_id
        )
        
        logger.info(f"分析請求成功建立: {session_id}", extra={
            'user_id': user.user_id,
            'stock_symbol': request.stock_id,
            'session_id': session_id,
            'api_endpoint': '/analysis/start',
            'status': 'success'
        })
        
        return AnalysisResponse(
            session_id=session_id,
            status="started",
            message=f"已開始分析股票 {request.stock_id}",
            estimated_time=30
        )
        
    except Exception as e:
        error_info = await handle_error(e, {
            'api_endpoint': '/analysis/start',
            'stock_symbol': request.stock_id,
            'user_tier': user.membership_tier.value
        }, user_id=user.user_id)
        
        logger.error(f"分析請求失敗: {str(e)}", extra={
            'user_id': user.user_id,
            'stock_symbol': request.stock_id,
            'error_id': error_info.error_id,
            'api_endpoint': '/analysis/start',
            'status': 'error'
        })
        
        # 返回用戶友好的錯誤訊息
        user_message = get_user_friendly_message(error_info)
        raise HTTPException(
            status_code=500,
            detail=user_message
        )

@app.get("/analysis/{session_id}/status", response_model=SessionStatusResponse, tags=["分析服務"])
async def get_analysis_status(
    session_id: str,
    user: CurrentUser,
    graph: TradingAgentsGraph = Depends(get_trading_graph)
):
    """獲取分析狀態"""
    try:
        status = graph.get_session_status(session_id)
        
        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"找不到會話 {session_id}"
            )
        
        # 檢查用戶權限 (簡化檢查)
        session_user_id = status.get('user_context', {}).get('user_id')
        if session_user_id and session_user_id != user.user_id:
            raise HTTPException(
                status_code=403,
                detail="無權限查看此分析會話"
            )
        
        return SessionStatusResponse(**status)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取分析狀態失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取狀態失敗: {str(e)}"
        )

@app.delete("/analysis/{session_id}", tags=["分析服務"])
async def cancel_analysis(
    session_id: str,
    user: CurrentUser,
    graph: TradingAgentsGraph = Depends(get_trading_graph)
):
    """取消分析"""
    try:
        success = graph.cancel_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"找不到會話 {session_id}"
            )
        
        return {
            "message": f"已取消分析會話 {session_id}",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消分析失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"取消分析失敗: {str(e)}"
        )

@app.get("/analysis/sessions", tags=["分析服務"])
async def get_active_sessions(
    user: CurrentUser,
    graph: TradingAgentsGraph = Depends(get_trading_graph)
):
    """獲取活躍分析會話"""
    try:
        all_sessions = graph.get_all_active_sessions()
        
        # 過濾用戶的會話
        user_sessions = {
            session_id: session_data
            for session_id, session_data in all_sessions.items()
            if session_data.get('user_context', {}).get('user_id') == user.user_id
        }
        
        return {
            "sessions": user_sessions,
            "total_count": len(user_sessions),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取會話列表失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取會話列表失敗: {str(e)}"
        )

@app.get("/system/metrics", response_model=SystemMetricsResponse, tags=["系統監控"])
async def get_system_metrics(
    user: DiamondUser,  # 只有鑽石用戶可以查看系統指標
    graph: TradingAgentsGraph = Depends(get_trading_graph)
):
    """獲取系統指標"""
    try:
        metrics = graph.get_system_metrics()
        return SystemMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"獲取系統指標失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取系統指標失敗: {str(e)}"
        )

@app.get("/user/info", tags=["用戶服務"])
async def get_user_info(user: CurrentUser):
    """獲取用戶資訊"""
    return {
        "user_id": user.user_id,
        "membership_tier": user.membership_tier.value,
        "permissions": {
            "can_use_advanced_analysis": user.permissions.can_use_advanced_analysis,
            "can_export_data": user.permissions.can_export_data,
            "can_use_premium_features": user.permissions.can_use_premium_features
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/analysts/info", tags=["分析師服務"])
async def get_analysts_info(
    user: CurrentUser,
    graph: TradingAgentsGraph = Depends(get_trading_graph)
):
    """獲取可用分析師資訊"""
    try:
        analysts_info = {}
        
        for analyst_id, analyst in graph.analysts.items():
            if hasattr(analyst, 'get_analyst_info'):
                analysts_info[analyst_id] = analyst.get_analyst_info()
        
        # 根據會員等級過濾分析師
        available_analysts = graph._select_analysts(user, None)
        
        return {
            "available_analysts": available_analysts,
            "analysts_info": analysts_info,
            "membership_tier": user.membership_tier.value,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"獲取分析師資訊失敗: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"獲取分析師資訊失敗: {str(e)}"
        )

# ==================== WebSocket支援 ====================

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket連接，用於實時狀態推送"""
    await websocket.accept()
    active_connections[user_id] = websocket
    
    try:
        while True:
            # 保持連接活躍
            await websocket.receive_text()
            
    except WebSocketDisconnect:
        if user_id in active_connections:
            del active_connections[user_id]
        logger.info(f"用戶 {user_id} WebSocket連接已斷開")

async def notify_analysis_progress(session_id: str, user_id: str):
    """通知分析進度"""
    if user_id not in active_connections:
        return
    
    websocket = active_connections[user_id]
    
    try:
        # 監控分析進度
        while True:
            if trading_graph:
                status = trading_graph.get_session_status(session_id)
                
                if status:
                    await websocket.send_text(json.dumps({
                        "type": "analysis_progress",
                        "session_id": session_id,
                        "progress": status.get('progress_percentage', 0),
                        "phase": status.get('current_phase', 'unknown'),
                        "status": status.get('overall_status', 'unknown')
                    }))
                    
                    # 如果分析完成，發送最終結果
                    if status.get('overall_status') in ['completed', 'failed', 'cancelled']:
                        await websocket.send_text(json.dumps({
                            "type": "analysis_completed",
                            "session_id": session_id,
                            "final_status": status.get('overall_status'),
                            "result": status.get('final_result')
                        }))
                        break
            
            # 等待1秒後再次檢查
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.error(f"WebSocket通知失敗: {str(e)}")

# ==================== 異常處理 ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTP異常處理器"""
    logger.warning(f"HTTP異常: {exc.status_code} - {exc.detail}", extra={
        'status_code': exc.status_code,
        'detail': exc.detail,
        'url': str(request.url),
        'method': request.method,
        'exception_type': 'http_exception'
    })
    
    return exc

@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """全局異常處理器"""
    # 獲取請求相關資訊
    user_id = None
    try:
        # 嘗試從請求中提取用戶資訊
        if hasattr(request.state, 'user'):
            user_id = request.state.user.user_id
    except:
        pass
    
    # 處理錯誤
    error_info = await handle_error(exc, {
        'url': str(request.url),
        'method': request.method,
        'headers': dict(request.headers),
        'query_params': dict(request.query_params),
        'client_host': request.client.host if request.client else None
    }, user_id=user_id)
    
    system_logger.error(f"未處理的異常: {str(exc)}", extra={
        'error_id': error_info.error_id,
        'url': str(request.url),
        'method': request.method,
        'user_id': user_id,
        'exception_type': type(exc).__name__,
        'client_host': request.client.host if request.client else None
    })
    
    # 返回用戶友好的錯誤訊息
    user_message = get_user_friendly_message(error_info)
    
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={
            "detail": user_message,
            "error_id": error_info.error_id,
            "timestamp": error_info.timestamp.isoformat()
        }
    )

# ==================== 緊急投資組合API ====================
# 直接內嵌simple-portfolio端點以繞過模組導入問題

import time

# 記憶體存儲
emergency_portfolios = {}
emergency_holdings = {}

@app.get("/api/simple-portfolios/health", tags=["投資組合"])
async def simple_portfolios_health():
    """投資組合健康檢查端點"""
    return {
        "status": "healthy",
        "service": "simple-portfolios",
        "timestamp": time.time(),
        "portfolios_count": len(emergency_portfolios),
        "total_holdings": sum(len(h) for h in emergency_holdings.values())
    }

@app.get("/api/simple-portfolios", tags=["投資組合"])
async def get_simple_portfolios():
    """獲取所有投資組合"""
    return {
        "success": True,
        "portfolios": list(emergency_portfolios.values()),
        "timestamp": time.time()
    }

@app.post("/api/simple-portfolios", tags=["投資組合"]) 
async def create_simple_portfolio(request: Request):
    """創建新的投資組合"""
    try:
        body = await request.json()
        portfolio_id = f"portfolio_{int(time.time())}"
        emergency_portfolios[portfolio_id] = {
            "id": portfolio_id,
            "name": body.get("name", "新投資組合"),
            "description": body.get("description", ""),
            "created_at": time.time(),
            "holdings": []
        }
        
        return {
            "success": True,
            "portfolio": emergency_portfolios[portfolio_id],
            "message": "投資組合創建成功"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.options("/api/simple-portfolios", tags=["投資組合"])
@app.options("/api/simple-portfolios/health", tags=["投資組合"])
async def simple_portfolios_options():
    """處理OPTIONS預檢請求"""
    return {"status": "OK"}

# ==================== 啟動檢查 ====================

if __name__ == "__main__":
    import uvicorn
    
    # 開發環境啟動
    uvicorn.run(
        "tradingagents.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
