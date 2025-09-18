"""
營收分析儀表板API
PayUni營收分析的完整API端點
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import logging
import os

from ..core.deps import get_current_user
from ...analytics.warehouse import DataWarehouseManager
from ...analytics.revenue import RevenueAnalyzer

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/analytics/revenue", tags=["營收分析"])

# 全局變量存儲管理器實例
_warehouse_manager = None
_revenue_analyzer = None

def get_revenue_analyzer() -> RevenueAnalyzer:
    """獲取營收分析器實例"""
    global _warehouse_manager, _revenue_analyzer
    
    if _warehouse_manager is None:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise HTTPException(status_code=500, detail="DATABASE_URL環境變數未設置")
        _warehouse_manager = DataWarehouseManager(database_url)
    
    if _revenue_analyzer is None:
        _revenue_analyzer = RevenueAnalyzer(_warehouse_manager)
    
    return _revenue_analyzer

@router.get("/dashboard")
async def get_revenue_dashboard(
    period: str = Query("month", description="時間週期: today, week, month, quarter"),
    date_filter: Optional[date] = Query(None, description="指定日期過濾")
):
    """
    獲取營收儀表板數據
    
    - **period**: 時間週期選擇
      - today: 今日數據
      - week: 本週數據  
      - month: 本月數據
      - quarter: 本季數據
    - **date_filter**: 可選的具體日期過濾
    """
    try:
        analyzer = get_revenue_analyzer()
        
        if period == "today":
            if date_filter:
                metrics = await analyzer.calculate_daily_metrics(date_filter)
            else:
                metrics = await analyzer.calculate_daily_metrics()
        elif period == "month":
            if date_filter:
                target_month = date_filter.replace(day=1)
                metrics = await analyzer.calculate_monthly_metrics(target_month)
            else:
                metrics = await analyzer.calculate_monthly_metrics()
        else:
            # 使用通用儀表板數據
            dashboard_data = await analyzer.get_revenue_dashboard_data(period)
            return {
                "success": True,
                "data": dashboard_data
            }
        
        # 並行獲取其他數據
        trends = await analyzer.calculate_growth_trends()
        kpis = await analyzer.calculate_key_kpis()
        
        return {
            "success": True,
            "data": {
                "metrics": metrics,
                "trends": trends,
                "kpis": kpis,
                "period": period,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取營收儀表板失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取儀表板數據失敗: {str(e)}")

@router.get("/kpis")
async def get_key_kpis():
    """
    獲取關鍵KPI指標
    
    返回當前月份的核心營收指標，包括：
    - 當月營收
    - 付費用戶數
    - ARPU (平均每用戶收入)
    - 增長率等
    """
    try:
        analyzer = get_revenue_analyzer()
        kpis = await analyzer.calculate_key_kpis()
        
        return {
            "success": True,
            "data": kpis
        }
        
    except Exception as e:
        logger.error(f"獲取KPI失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取KPI失敗: {str(e)}")

@router.get("/trends")
async def get_revenue_trends(
    days: int = Query(30, ge=7, le=365, description="分析天數，7-365天")
):
    """
    獲取營收增長趨勢
    
    - **days**: 分析的天數範圍
    """
    try:
        analyzer = get_revenue_analyzer()
        trends = await analyzer.calculate_growth_trends(days)
        
        return {
            "success": True,
            "data": trends
        }
        
    except Exception as e:
        logger.error(f"獲取營收趨勢失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取趨勢失敗: {str(e)}")

@router.get("/daily/{target_date}")
async def get_daily_metrics(target_date: date):
    """
    獲取指定日期的營收指標
    
    - **target_date**: 目標日期 (YYYY-MM-DD格式)
    """
    try:
        analyzer = get_revenue_analyzer()
        metrics = await analyzer.calculate_daily_metrics(target_date)
        
        return {
            "success": True,
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"獲取每日營收指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取每日指標失敗: {str(e)}")

@router.get("/monthly")
async def get_monthly_metrics(
    year: Optional[int] = Query(None, description="年份"),
    month: Optional[int] = Query(None, ge=1, le=12, description="月份")
):
    """
    獲取月度營收指標
    
    - **year**: 指定年份，默認當前年份
    - **month**: 指定月份，默認當前月份
    """
    try:
        analyzer = get_revenue_analyzer()
        
        if year and month:
            target_month = date(year, month, 1)
            metrics = await analyzer.calculate_monthly_metrics(target_month)
        else:
            metrics = await analyzer.calculate_monthly_metrics()
        
        return {
            "success": True,
            "data": metrics
        }
        
    except Exception as e:
        logger.error(f"獲取月度營收指標失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取月度指標失敗: {str(e)}")

@router.get("/subscription-performance")
async def get_subscription_performance():
    """
    獲取訂閱層級表現分析
    
    分析不同訂閱層級（Gold/Diamond）的表現，包括：
    - 收入貢獻
    - 用戶數量
    - 續費率
    - 市場份額等
    """
    try:
        analyzer = get_revenue_analyzer()
        performance = await analyzer.analyze_subscription_performance()
        
        return {
            "success": True,
            "data": performance
        }
        
    except Exception as e:
        logger.error(f"獲取訂閱表現失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取訂閱分析失敗: {str(e)}")

@router.get("/comparison")
async def get_revenue_comparison(
    period1_start: date = Query(..., description="第一個週期開始日期"),
    period1_end: date = Query(..., description="第一個週期結束日期"),
    period2_start: date = Query(..., description="第二個週期開始日期"), 
    period2_end: date = Query(..., description="第二個週期結束日期")
):
    """
    營收週期比較分析
    
    比較兩個時間週期的營收表現
    """
    try:
        analyzer = get_revenue_analyzer()
        warehouse = analyzer.warehouse
        
        async with warehouse.async_engine.begin() as conn:
            # 週期1數據
            period1_query = text("""
                SELECT 
                    COUNT(*) as transactions,
                    SUM(amount) as revenue,
                    COUNT(DISTINCT user_id) as unique_users,
                    AVG(amount) as avg_transaction_value
                FROM fact_revenue 
                WHERE date_id >= :start_date AND date_id <= :end_date
            """)
            
            period1_result = await conn.execute(period1_query, {
                'start_date': period1_start,
                'end_date': period1_end
            })
            period1_data = dict(period1_result.fetchone()._mapping)
            
            # 週期2數據
            period2_result = await conn.execute(period1_query, {
                'start_date': period2_start,
                'end_date': period2_end
            })
            period2_data = dict(period2_result.fetchone()._mapping)
        
        # 計算變化率
        def calculate_change_rate(current, previous):
            if previous == 0:
                return 0 if current == 0 else 100
            return ((current - previous) / previous) * 100
        
        comparison = {
            'period1': {
                'start_date': period1_start,
                'end_date': period1_end,
                'data': period1_data
            },
            'period2': {
                'start_date': period2_start,
                'end_date': period2_end,
                'data': period2_data
            },
            'changes': {
                'revenue_change': calculate_change_rate(
                    float(period2_data['revenue'] or 0),
                    float(period1_data['revenue'] or 0)
                ),
                'transaction_change': calculate_change_rate(
                    period2_data['transactions'] or 0,
                    period1_data['transactions'] or 0
                ),
                'user_change': calculate_change_rate(
                    period2_data['unique_users'] or 0,
                    period1_data['unique_users'] or 0
                )
            }
        }
        
        return {
            "success": True,
            "data": comparison
        }
        
    except Exception as e:
        logger.error(f"營收比較分析失敗: {e}")
        raise HTTPException(status_code=500, detail=f"比較分析失敗: {str(e)}")

@router.get("/top-users")
async def get_top_revenue_users(
    limit: int = Query(10, ge=1, le=100, description="返回用戶數量"),
    period_days: int = Query(30, ge=1, le=365, description="分析週期天數")
):
    """
    獲取高價值用戶排行
    
    - **limit**: 返回的用戶數量
    - **period_days**: 分析的時間週期
    """
    try:
        analyzer = get_revenue_analyzer()
        warehouse = analyzer.warehouse
        
        async with warehouse.async_engine.begin() as conn:
            top_users_query = text("""
                SELECT 
                    fr.user_id,
                    SUM(fr.amount) as total_revenue,
                    COUNT(fr.transaction_id) as total_transactions,
                    AVG(fr.amount) as avg_transaction_value,
                    MAX(fr.date_id) as last_transaction_date,
                    du.subscription_tier,
                    du.registration_date
                FROM fact_revenue fr
                LEFT JOIN dim_users du ON fr.user_id = du.user_id
                WHERE fr.date_id >= CURRENT_DATE - INTERVAL ':period_days days'
                GROUP BY fr.user_id, du.subscription_tier, du.registration_date
                ORDER BY total_revenue DESC
                LIMIT :limit
            """)
            
            result = await conn.execute(top_users_query, {
                'period_days': period_days,
                'limit': limit
            })
            
            top_users = [dict(row._mapping) for row in result.fetchall()]
        
        return {
            "success": True,
            "data": {
                "top_users": top_users,
                "analysis_period_days": period_days,
                "total_users_analyzed": len(top_users)
            }
        }
        
    except Exception as e:
        logger.error(f"獲取高價值用戶失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取高價值用戶失敗: {str(e)}")

@router.get("/health")
async def revenue_analytics_health():
    """營收分析系統健康檢查"""
    try:
        analyzer = get_revenue_analyzer()
        warehouse = analyzer.warehouse
        
        # 檢查數據庫連接
        health_status = await warehouse.health_check()
        
        # 檢查數據新鮮度
        async with warehouse.async_engine.begin() as conn:
            latest_data_query = text("""
                SELECT MAX(created_at) as latest_revenue_data
                FROM fact_revenue
            """)
            result = await conn.execute(latest_data_query)
            latest_data = result.fetchone()
            
            data_freshness = "current"
            if latest_data and latest_data.latest_revenue_data:
                hours_old = (datetime.now() - latest_data.latest_revenue_data).total_seconds() / 3600
                if hours_old > 24:
                    data_freshness = "stale"
                elif hours_old > 6:
                    data_freshness = "old"
        
        return {
            "success": True,
            "service": "revenue_analytics",
            "status": "healthy" if health_status['status'] == 'healthy' else "degraded",
            "database_status": health_status['status'],
            "data_freshness": data_freshness,
            "latest_data_time": latest_data.latest_revenue_data if latest_data else None,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"營收分析健康檢查失敗: {e}")
        return {
            "success": False,
            "service": "revenue_analytics", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }