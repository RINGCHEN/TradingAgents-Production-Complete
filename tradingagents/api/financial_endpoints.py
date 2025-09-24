"""
P2-2 財務管理 API 端點
完整的財務儀表板後端支援，對接前端 FinancialDashboardV2
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from pydantic import BaseModel
import logging
import asyncio

from ..auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

# 創建路由器
router = APIRouter(prefix="/api/v1/financial", tags=["財務管理"])

# ============================================================================
# Pydantic 模型定義
# ============================================================================

class FinancialKPI(BaseModel):
    id: str
    name: str
    value: float
    change: float
    changePercentage: float
    trend: str  # 'up', 'down', 'stable'
    period: str  # 'daily', 'weekly', 'monthly', 'quarterly', 'yearly'
    currency: str  # 'TWD', 'USD'
    format: str  # 'currency', 'percentage', 'number', 'rate'
    target: Optional[float] = None
    description: Optional[str] = None
    lastUpdated: str
    category: str  # 'revenue', 'cost', 'profit', 'growth', 'efficiency', 'risk'

class RevenueDataPoint(BaseModel):
    period: str
    actual: float
    target: Optional[float] = None
    lastYear: Optional[float] = None

class CostCategoryData(BaseModel):
    category: str
    amount: float
    percentage: float
    change: float
    changePercentage: float
    color: Optional[str] = None
    description: Optional[str] = None

class PerformanceMetric(BaseModel):
    metric: str
    actual: float
    target: float
    industryAverage: Optional[float] = None
    unit: str
    category: str  # 'financial', 'operational', 'growth', 'efficiency'
    description: Optional[str] = None

class DateRangeRequest(BaseModel):
    start_date: str
    end_date: str

# ============================================================================
# 模擬數據生成器 (生產環境中將連接真實數據庫)
# ============================================================================

async def generate_mock_kpis(start_date: str, end_date: str) -> List[FinancialKPI]:
    """生成模擬 KPI 數據"""
    await asyncio.sleep(0.1)  # 模擬數據庫查詢延遲
    
    return [
        FinancialKPI(
            id="total_revenue",
            name="總營收",
            value=2847560,
            change=285640,
            changePercentage=11.2,
            trend="up",
            period="monthly",
            currency="TWD",
            format="currency",
            target=3000000,
            description="本月總營收金額，包含所有會員訂閱和服務費用",
            lastUpdated=datetime.now().isoformat(),
            category="revenue"
        ),
        FinancialKPI(
            id="monthly_revenue",
            name="月度營收",
            value=456789,
            change=45678,
            changePercentage=11.1,
            trend="up",
            period="monthly",
            currency="TWD",
            format="currency",
            target=500000,
            description="當月營收增長情況",
            lastUpdated=datetime.now().isoformat(),
            category="revenue"
        ),
        FinancialKPI(
            id="profit_margin",
            name="淨利潤率",
            value=23.4,
            change=2.1,
            changePercentage=9.8,
            trend="up",
            period="monthly",
            currency="TWD",
            format="percentage",
            target=25.0,
            description="扣除所有成本後的淨利潤率",
            lastUpdated=datetime.now().isoformat(),
            category="profit"
        ),
        FinancialKPI(
            id="total_cost",
            name="營運成本",
            value=1654320,
            change=-45678,
            changePercentage=-2.7,
            trend="down",
            period="monthly",
            currency="TWD",
            format="currency",
            target=1500000,
            description="包含服務器、人力、營銷等所有營運成本",
            lastUpdated=datetime.now().isoformat(),
            category="cost"
        ),
        FinancialKPI(
            id="user_acquisition_cost",
            name="用戶獲取成本",
            value=245,
            change=-12,
            changePercentage=-4.7,
            trend="down",
            period="monthly",
            currency="TWD",
            format="currency",
            target=200,
            description="每獲取一個新用戶的平均成本 (CAC)",
            lastUpdated=datetime.now().isoformat(),
            category="cost"
        ),
        FinancialKPI(
            id="ltv",
            name="用戶生命週期價值",
            value=3420,
            change=156,
            changePercentage=4.8,
            trend="up",
            period="monthly",
            currency="TWD",
            format="currency",
            target=3600,
            description="用戶在整個生命週期中為公司創造的價值 (LTV)",
            lastUpdated=datetime.now().isoformat(),
            category="growth"
        ),
        FinancialKPI(
            id="conversion_rate",
            name="付費轉換率",
            value=12.3,
            change=1.2,
            changePercentage=10.8,
            trend="up",
            period="monthly",
            currency="TWD",
            format="percentage",
            target=15.0,
            description="免費用戶轉換為付費用戶的比率",
            lastUpdated=datetime.now().isoformat(),
            category="growth"
        ),
        FinancialKPI(
            id="churn_rate",
            name="用戶流失率",
            value=3.2,
            change=-0.5,
            changePercentage=-13.5,
            trend="down",
            period="monthly",
            currency="TWD",
            format="percentage",
            target=2.5,
            description="用戶取消訂閱或停止使用的比率",
            lastUpdated=datetime.now().isoformat(),
            category="risk"
        )
    ]

async def generate_mock_revenue_data(start_date: str, end_date: str) -> List[RevenueDataPoint]:
    """生成模擬營收趨勢數據"""
    await asyncio.sleep(0.1)
    
    return [
        RevenueDataPoint(period="2024-01", actual=2156000, target=2000000, lastYear=1890000),
        RevenueDataPoint(period="2024-02", actual=2334000, target=2100000, lastYear=2010000),
        RevenueDataPoint(period="2024-03", actual=2567000, target=2200000, lastYear=2156000),
        RevenueDataPoint(period="2024-04", actual=2789000, target=2300000, lastYear=2298000),
        RevenueDataPoint(period="2024-05", actual=2456000, target=2400000, lastYear=2445000),
        RevenueDataPoint(period="2024-06", actual=2678000, target=2500000, lastYear=2523000),
        RevenueDataPoint(period="2024-07", actual=2845000, target=2600000, lastYear=2634000),
        RevenueDataPoint(period="2024-08", actual=2923000, target=2700000, lastYear=2756000),
        RevenueDataPoint(period="2024-09", actual=2847000, target=2800000, lastYear=2678000),
        RevenueDataPoint(period="2024-10", actual=2945000, target=2900000, lastYear=2789000),
        RevenueDataPoint(period="2024-11", actual=3123000, target=3000000, lastYear=2856000),
        RevenueDataPoint(period="2024-12", actual=3345000, target=3100000, lastYear=2934000)
    ]

async def generate_mock_cost_data(start_date: str, end_date: str) -> List[CostCategoryData]:
    """生成模擬成本結構數據"""
    await asyncio.sleep(0.1)
    
    return [
        CostCategoryData(
            category="人力成本",
            amount=856000,
            percentage=51.7,
            change=-23000,
            changePercentage=-2.6,
            color="#1890ff",
            description="員工薪資、獎金、福利等人力相關支出"
        ),
        CostCategoryData(
            category="營運成本",
            amount=345000,
            percentage=20.9,
            change=12000,
            changePercentage=3.6,
            color="#52c41a",
            description="租金、水電、辦公用品等營運支出"
        ),
        CostCategoryData(
            category="行銷成本",
            amount=234000,
            percentage=14.1,
            change=45000,
            changePercentage=23.8,
            color="#fa541c",
            description="廣告投放、市場推廣、品牌建設等"
        ),
        CostCategoryData(
            category="技術成本",
            amount=123000,
            percentage=7.4,
            change=-8000,
            changePercentage=-6.1,
            color="#722ed1",
            description="軟體授權、雲端服務、技術維護等"
        ),
        CostCategoryData(
            category="其他成本",
            amount=96000,
            percentage=5.8,
            change=3000,
            changePercentage=3.2,
            color="#13c2c2",
            description="法務、會計、保險等其他雜項支出"
        )
    ]

async def generate_mock_performance_data(start_date: str, end_date: str) -> List[PerformanceMetric]:
    """生成模擬績效指標數據"""
    await asyncio.sleep(0.1)
    
    return [
        PerformanceMetric(
            metric="營收增長率",
            actual=15.6,
            target=12.0,
            industryAverage=8.5,
            unit="%",
            category="growth",
            description="年度營收增長百分比"
        ),
        PerformanceMetric(
            metric="淨利潤率",
            actual=23.4,
            target=25.0,
            industryAverage=18.2,
            unit="%",
            category="financial",
            description="淨利潤占營收的百分比"
        ),
        PerformanceMetric(
            metric="用戶轉換率",
            actual=12.3,
            target=15.0,
            industryAverage=10.1,
            unit="%",
            category="operational",
            description="訪客轉換為付費用戶的比率"
        ),
        PerformanceMetric(
            metric="ROI",
            actual=145.8,
            target=120.0,
            industryAverage=98.5,
            unit="%",
            category="financial",
            description="投資回報率"
        ),
        PerformanceMetric(
            metric="客戶滿意度",
            actual=87.5,
            target=90.0,
            industryAverage=82.3,
            unit="分",
            category="operational",
            description="客戶滿意度評分 (0-100)"
        ),
        PerformanceMetric(
            metric="營運效率",
            actual=78.9,
            target=85.0,
            industryAverage=75.6,
            unit="分",
            category="efficiency",
            description="營運效率綜合評分"
        )
    ]

# ============================================================================
# API 端點定義
# ============================================================================

@router.get("/health")
async def financial_health_check():
    """財務管理系統健康檢查"""
    return {
        "success": True,
        "service": "financial_management",
        "status": "healthy",
        "version": "2.0.0",
        "features": [
            "kpi_dashboard",
            "revenue_analytics", 
            "cost_analysis",
            "performance_metrics"
        ],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/kpis", response_model=Dict[str, Any])
async def get_financial_kpis(
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="KPI 類別篩選"),
    current_user = Depends(get_current_user)
):
    """
    獲取財務 KPI 數據
    
    支援的類別: revenue, cost, profit, growth, efficiency, risk
    """
    try:
        logger.info(f"獲取 KPI 數據: {start_date} 到 {end_date}, 用戶: {current_user.get('email', 'unknown')}")
        
        kpis = await generate_mock_kpis(start_date, end_date)
        
        # 按類別篩選
        if category and category != "all":
            kpis = [kpi for kpi in kpis if kpi.category == category]
        
        return {
            "success": True,
            "data": {
                "kpis": [kpi.dict() for kpi in kpis],
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "category_filter": category,
                "total_count": len(kpis),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取 KPI 數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取 KPI 數據失敗: {str(e)}")

@router.get("/revenue", response_model=Dict[str, Any])
async def get_revenue_data(
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user)
):
    """獲取營收趨勢數據"""
    try:
        logger.info(f"獲取營收數據: {start_date} 到 {end_date}")
        
        revenue_data = await generate_mock_revenue_data(start_date, end_date)
        
        return {
            "success": True,
            "data": {
                "revenue": [item.dict() for item in revenue_data],
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "total_periods": len(revenue_data),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取營收數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取營收數據失敗: {str(e)}")

@router.get("/costs", response_model=Dict[str, Any])
async def get_cost_data(
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user)
):
    """獲取成本結構數據"""
    try:
        logger.info(f"獲取成本數據: {start_date} 到 {end_date}")
        
        cost_data = await generate_mock_cost_data(start_date, end_date)
        
        return {
            "success": True,
            "data": {
                "costs": [item.dict() for item in cost_data],
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "total_categories": len(cost_data),
                "total_cost": sum(item.amount for item in cost_data),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取成本數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取成本數據失敗: {str(e)}")

@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_data(
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="績效類別篩選"),
    current_user = Depends(get_current_user)
):
    """
    獲取績效指標數據
    
    支援的類別: financial, operational, growth, efficiency
    """
    try:
        logger.info(f"獲取績效數據: {start_date} 到 {end_date}")
        
        performance_data = await generate_mock_performance_data(start_date, end_date)
        
        # 按類別篩選
        if category and category != "all":
            performance_data = [item for item in performance_data if item.category == category]
        
        return {
            "success": True,
            "data": {
                "performance": [item.dict() for item in performance_data],
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "category_filter": category,
                "total_metrics": len(performance_data),
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取績效數據失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取績效數據失敗: {str(e)}")

@router.put("/kpis/{kpi_id}")
async def update_kpi(
    kpi_id: str,
    updates: Dict[str, Any],
    current_user = Depends(get_current_user)
):
    """更新指定 KPI 的數據"""
    try:
        logger.info(f"更新 KPI {kpi_id}: {updates}")
        
        # 在實際實現中，這裡會更新資料庫
        # 目前返回模擬的更新結果
        
        return {
            "success": True,
            "data": {
                "kpi_id": kpi_id,
                "updates_applied": updates,
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"更新 KPI 失敗: {e}")
        raise HTTPException(status_code=500, detail=f"更新 KPI 失敗: {str(e)}")

@router.post("/reports/generate")
async def generate_financial_report(
    report_type: str = Query(..., description="報告類型: summary, detailed, custom"),
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    format: str = Query("json", description="報告格式: json, excel, pdf"),
    current_user = Depends(get_current_user)
):
    """生成財務報告"""
    try:
        logger.info(f"生成財務報告: 類型={report_type}, 格式={format}")
        
        # 獲取所有數據
        kpis = await generate_mock_kpis(start_date, end_date)
        revenue_data = await generate_mock_revenue_data(start_date, end_date)
        cost_data = await generate_mock_cost_data(start_date, end_date)
        performance_data = await generate_mock_performance_data(start_date, end_date)
        
        report_data = {
            "report_id": f"FR_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "report_type": report_type,
            "date_range": {
                "start": start_date,
                "end": end_date
            },
            "summary": {
                "total_kpis": len(kpis),
                "total_revenue": sum(item.actual for item in revenue_data),
                "total_costs": sum(item.amount for item in cost_data),
                "performance_score": sum(item.actual for item in performance_data) / len(performance_data)
            },
            "data": {
                "kpis": [kpi.dict() for kpi in kpis],
                "revenue": [item.dict() for item in revenue_data],
                "costs": [item.dict() for item in cost_data],
                "performance": [item.dict() for item in performance_data]
            },
            "generated_at": datetime.now().isoformat(),
            "generated_by": current_user.get('email', 'system')
        }
        
        if format == "json":
            return {
                "success": True,
                "data": report_data
            }
        else:
            # 對於 Excel 和 PDF 格式，返回下載連結
            return {
                "success": True,
                "data": {
                    "report_id": report_data["report_id"],
                    "download_url": f"/api/v1/financial/reports/{report_data['report_id']}/download",
                    "format": format,
                    "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
                }
            }
        
    except Exception as e:
        logger.error(f"生成財務報告失敗: {e}")
        raise HTTPException(status_code=500, detail=f"生成報告失敗: {str(e)}")

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    start_date: str = Query(..., description="開始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="結束日期 (YYYY-MM-DD)"),
    current_user = Depends(get_current_user)
):
    """獲取儀表板摘要統計"""
    try:
        # 並行獲取所有數據
        kpis, revenue_data, cost_data, performance_data = await asyncio.gather(
            generate_mock_kpis(start_date, end_date),
            generate_mock_revenue_data(start_date, end_date),
            generate_mock_cost_data(start_date, end_date),
            generate_mock_performance_data(start_date, end_date)
        )
        
        # 計算摘要統計
        positive_kpis = len([kpi for kpi in kpis if kpi.changePercentage > 0])
        negative_kpis = len([kpi for kpi in kpis if kpi.changePercentage < 0])
        avg_change = sum(kpi.changePercentage for kpi in kpis) / len(kpis) if kpis else 0
        
        total_revenue = sum(item.actual for item in revenue_data)
        total_costs = sum(item.amount for item in cost_data)
        profit_margin = ((total_revenue - total_costs) / total_revenue * 100) if total_revenue > 0 else 0
        
        achieved_targets = len([metric for metric in performance_data if metric.actual >= metric.target])
        performance_score = (achieved_targets / len(performance_data) * 100) if performance_data else 0
        
        return {
            "success": True,
            "data": {
                "kpi_summary": {
                    "total_kpis": len(kpis),
                    "positive_count": positive_kpis,
                    "negative_count": negative_kpis,
                    "average_change": round(avg_change, 2)
                },
                "financial_summary": {
                    "total_revenue": total_revenue,
                    "total_costs": total_costs,
                    "profit_margin": round(profit_margin, 2),
                    "net_profit": total_revenue - total_costs
                },
                "performance_summary": {
                    "total_metrics": len(performance_data),
                    "achieved_targets": achieved_targets,
                    "performance_score": round(performance_score, 2)
                },
                "date_range": {
                    "start": start_date,
                    "end": end_date
                },
                "last_updated": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"獲取儀表板摘要失敗: {e}")
        raise HTTPException(status_code=500, detail=f"獲取摘要失敗: {str(e)}")