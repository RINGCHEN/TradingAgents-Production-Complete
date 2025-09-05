#!/usr/bin/env python3
"""
完整管理後台路由整合
整合所有管理功能的路由
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access

# 導入所有管理服務
from ..services.analytics_service import AnalyticsService
from ..services.reporting_service import ReportingService
from ..services.content_management_service import ContentManagementService
from ..services.financial_management_service import FinancialManagementService

# 創建主路由器
admin_router = APIRouter(prefix="/admin", tags=["管理後台"])

# 數據分析路由
@admin_router.get("/analytics/dashboard")
async def get_analytics_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access)
):
    """獲取分析儀表板"""
    service = AnalyticsService(db)
    return await service.get_analytics_dashboard()

# 報表生成路由
@admin_router.post("/reports/generate")
async def generate_report(
    report_request: dict,
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access)
):
    """生成報表"""
    service = ReportingService(db)
    return await service.generate_report(report_request)

# 內容管理路由
@admin_router.get("/content")
async def list_content(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access)
):
    """列出內容"""
    service = ContentManagementService(db)
    return await service.list_content()

# 財務管理路由
@admin_router.get("/financial/metrics")
async def get_financial_metrics(
    db: Session = Depends(get_db),
    current_user = Depends(require_admin_access)
):
    """獲取財務指標"""
    service = FinancialManagementService(db)
    return await service.get_financial_metrics()
