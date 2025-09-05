"""
交易管理路由
提供完整的交易監控和管理功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from ..services.trading_management_service import TradingManagementService
from ..models.trading_management import (
    TradingOrder,
    TradingPosition,
    TradingStats,
    TradingAnalytics,
    RiskMetrics,
    TradingAlert,
    MarketData,
    TradingStrategy
)
from ..middleware.auth_middleware import require_admin_permission

router = APIRouter(prefix="/admin/trading", tags=["trading-management"])
logger = logging.getLogger(__name__)

@router.get("/orders", response_model=List[TradingOrder])
async def get_trading_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="訂單狀態"),
    user_id: Optional[str] = Query(None, description="用戶ID"),
    symbol: Optional[str] = Query(None, description="股票代號"),
    start_date: Optional[str] = Query(None, description="開始日期"),
    end_date: Optional[str] = Query(None, description="結束日期"),
    service: TradingManagementService = Depends()
):
    """獲取交易訂單列表"""
    try:
        orders = await service.get_trading_orders(
            page=page,
            limit=limit,
            status=status,
            user_id=user_id,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return orders
    except Exception as e:
        logger.error(f"獲取交易訂單失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易訂單失敗")

@router.get("/orders/{order_id}", response_model=TradingOrder)
async def get_trading_order(
    order_id: str,
    service: TradingManagementService = Depends()
):
    """獲取特定交易訂單"""
    try:
        order = await service.get_trading_order(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="交易訂單不存在")
        return order
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取交易訂單失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易訂單失敗")

@router.put("/orders/{order_id}/cancel")
async def cancel_trading_order(
    order_id: str,
    reason: Optional[str] = None,
    service: TradingManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("trading_management"))
):
    """取消交易訂單"""
    try:
        result = await service.cancel_trading_order(order_id, reason)
        logger.info(f"管理員 {current_user['username']} 取消了交易訂單: {order_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"取消交易訂單失敗: {e}")
        raise HTTPException(status_code=500, detail="取消交易訂單失敗")

@router.get("/positions", response_model=List[TradingPosition])
async def get_trading_positions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: Optional[str] = Query(None, description="用戶ID"),
    symbol: Optional[str] = Query(None, description="股票代號"),
    status: Optional[str] = Query(None, description="持倉狀態"),
    service: TradingManagementService = Depends()
):
    """獲取交易持倉列表"""
    try:
        positions = await service.get_trading_positions(
            page=page,
            limit=limit,
            user_id=user_id,
            symbol=symbol,
            status=status
        )
        return positions
    except Exception as e:
        logger.error(f"獲取交易持倉失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易持倉失敗")

@router.get("/positions/{position_id}", response_model=TradingPosition)
async def get_trading_position(
    position_id: str,
    service: TradingManagementService = Depends()
):
    """獲取特定交易持倉"""
    try:
        position = await service.get_trading_position(position_id)
        if not position:
            raise HTTPException(status_code=404, detail="交易持倉不存在")
        return position
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取交易持倉失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易持倉失敗")

@router.put("/positions/{position_id}/close")
async def close_trading_position(
    position_id: str,
    reason: Optional[str] = None,
    service: TradingManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("trading_management"))
):
    """強制平倉"""
    try:
        result = await service.close_trading_position(position_id, reason)
        logger.info(f"管理員 {current_user['username']} 強制平倉: {position_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"強制平倉失敗: {e}")
        raise HTTPException(status_code=500, detail="強制平倉失敗")

@router.get("/stats", response_model=TradingStats)
async def get_trading_stats(
    period: str = Query("today", description="統計週期: today, week, month, year"),
    service: TradingManagementService = Depends()
):
    """獲取交易統計數據"""
    try:
        stats = await service.get_trading_stats(period)
        return stats
    except Exception as e:
        logger.error(f"獲取交易統計失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易統計失敗")

@router.get("/analytics", response_model=TradingAnalytics)
async def get_trading_analytics(
    days: int = Query(30, ge=1, le=365, description="分析天數"),
    service: TradingManagementService = Depends()
):
    """獲取交易分析數據"""
    try:
        analytics = await service.get_trading_analytics(days)
        return analytics
    except Exception as e:
        logger.error(f"獲取交易分析失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易分析失敗")

@router.get("/risk-metrics", response_model=RiskMetrics)
async def get_risk_metrics(
    service: TradingManagementService = Depends()
):
    """獲取風險指標"""
    try:
        metrics = await service.get_risk_metrics()
        return metrics
    except Exception as e:
        logger.error(f"獲取風險指標失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取風險指標失敗")

@router.get("/alerts", response_model=List[TradingAlert])
async def get_trading_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    severity: Optional[str] = Query(None, description="告警嚴重程度"),
    status: Optional[str] = Query(None, description="告警狀態"),
    service: TradingManagementService = Depends()
):
    """獲取交易告警"""
    try:
        alerts = await service.get_trading_alerts(
            page=page,
            limit=limit,
            severity=severity,
            status=status
        )
        return alerts
    except Exception as e:
        logger.error(f"獲取交易告警失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易告警失敗")

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_trading_alert(
    alert_id: str,
    service: TradingManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("trading_management"))
):
    """確認交易告警"""
    try:
        result = await service.acknowledge_trading_alert(alert_id, current_user['user_id'])
        logger.info(f"管理員 {current_user['username']} 確認了交易告警: {alert_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"確認交易告警失敗: {e}")
        raise HTTPException(status_code=500, detail="確認交易告警失敗")

@router.get("/market-data")
async def get_market_data(
    symbols: Optional[str] = Query(None, description="股票代號，多個用逗號分隔"),
    service: TradingManagementService = Depends()
):
    """獲取市場數據"""
    try:
        data = await service.get_market_data(symbols)
        return data
    except Exception as e:
        logger.error(f"獲取市場數據失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取市場數據失敗")

@router.get("/strategies", response_model=List[TradingStrategy])
async def get_trading_strategies(
    active_only: bool = Query(False, description="只顯示啟用的策略"),
    service: TradingManagementService = Depends()
):
    """獲取交易策略"""
    try:
        strategies = await service.get_trading_strategies(active_only)
        return strategies
    except Exception as e:
        logger.error(f"獲取交易策略失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易策略失敗")

@router.put("/strategies/{strategy_id}/toggle")
async def toggle_trading_strategy(
    strategy_id: str,
    service: TradingManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("trading_management"))
):
    """啟用/停用交易策略"""
    try:
        result = await service.toggle_trading_strategy(strategy_id)
        logger.info(f"管理員 {current_user['username']} 切換了交易策略狀態: {strategy_id}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"切換交易策略失敗: {e}")
        raise HTTPException(status_code=500, detail="切換交易策略失敗")

@router.get("/performance")
async def get_trading_performance(
    user_id: Optional[str] = Query(None, description="用戶ID"),
    period: str = Query("month", description="統計週期"),
    service: TradingManagementService = Depends()
):
    """獲取交易績效"""
    try:
        performance = await service.get_trading_performance(user_id, period)
        return performance
    except Exception as e:
        logger.error(f"獲取交易績效失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易績效失敗")

@router.post("/emergency-stop")
async def emergency_trading_stop(
    reason: str,
    service: TradingManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("trading_emergency"))
):
    """緊急停止所有交易"""
    try:
        result = await service.emergency_trading_stop(reason, current_user['user_id'])
        logger.critical(f"管理員 {current_user['username']} 執行了緊急停止交易: {reason}")
        return result
    except Exception as e:
        logger.error(f"緊急停止交易失敗: {e}")
        raise HTTPException(status_code=500, detail="緊急停止交易失敗")

@router.post("/resume-trading")
async def resume_trading(
    service: TradingManagementService = Depends(),
    current_user: dict = Depends(require_admin_permission("trading_emergency"))
):
    """恢復交易"""
    try:
        result = await service.resume_trading(current_user['user_id'])
        logger.info(f"管理員 {current_user['username']} 恢復了交易")
        return result
    except Exception as e:
        logger.error(f"恢復交易失敗: {e}")
        raise HTTPException(status_code=500, detail="恢復交易失敗")

@router.get("/audit-log")
async def get_trading_audit_log(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None, description="操作類型"),
    user_id: Optional[str] = Query(None, description="操作用戶"),
    start_date: Optional[str] = Query(None, description="開始日期"),
    end_date: Optional[str] = Query(None, description="結束日期"),
    service: TradingManagementService = Depends()
):
    """獲取交易審計日誌"""
    try:
        logs = await service.get_trading_audit_log(
            page=page,
            limit=limit,
            action=action,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        return logs
    except Exception as e:
        logger.error(f"獲取交易審計日誌失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取交易審計日誌失敗")