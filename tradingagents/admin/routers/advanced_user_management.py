#!/usr/bin/env python3
"""
高級用戶管理路由器 (Advanced User Management Router)
天工 (TianGong) - 第二階段高級用戶管理功能

此模組提供企業級高級用戶管理功能，包含：
1. 用戶行為分析儀表板
2. 用戶群組和標籤管理
3. 用戶生命週期管理
4. 批量用戶操作中心
5. 智能用戶分群和推薦
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("advanced_user_management")
security_logger = get_security_logger("advanced_user_management")

# 創建路由器
router = APIRouter(prefix="/advanced-users", tags=["高級用戶管理"])

# ==================== 數據模型定義 ====================

class UserBehaviorMetrics(BaseModel):
    """用戶行為指標"""
    user_id: str
    daily_active_days: int = Field(..., description="日活躍天數")
    monthly_active_days: int = Field(..., description="月活躍天數")
    session_duration_avg: float = Field(..., description="平均會話時長(分鐘)")
    page_views_total: int = Field(..., description="總頁面瀏覽數")
    feature_usage_count: Dict[str, int] = Field(..., description="功能使用次數")
    last_active_time: datetime = Field(..., description="最後活躍時間")
    engagement_score: float = Field(..., description="參與度評分(0-100)")

class UserSegment(BaseModel):
    """用戶分群"""
    segment_id: str
    segment_name: str = Field(..., description="分群名稱")
    description: Optional[str] = Field(None, description="分群描述")
    criteria: Dict[str, Any] = Field(..., description="分群條件")
    user_count: int = Field(..., description="用戶數量")
    created_at: datetime
    updated_at: datetime

class UserTag(BaseModel):
    """用戶標籤"""
    tag_id: str
    tag_name: str = Field(..., description="標籤名稱")
    tag_category: str = Field(..., description="標籤類別")
    tag_color: Optional[str] = Field(None, description="標籤顏色")
    description: Optional[str] = Field(None, description="標籤描述")
    user_count: int = Field(..., description="使用此標籤的用戶數")
    is_system_tag: bool = Field(False, description="是否為系統標籤")
    created_at: datetime

class UserLifecycleStage(str, Enum):
    """用戶生命週期階段"""
    PROSPECT = "prospect"
    ONBOARDING = "onboarding"
    ACTIVE = "active"
    POWER_USER = "power_user"
    AT_RISK = "at_risk"
    CHURNED = "churned"
    REACTIVATED = "reactivated"

class UserLifecycleInfo(BaseModel):
    """用戶生命週期信息"""
    user_id: str
    current_stage: UserLifecycleStage
    stage_duration: int = Field(..., description="當前階段持續天數")
    stage_history: List[Dict[str, Any]] = Field(..., description="階段變化歷史")
    predicted_next_stage: Optional[UserLifecycleStage] = Field(None)
    risk_score: float = Field(..., description="流失風險評分(0-100)")

class BulkOperationRequest(BaseModel):
    """批量操作請求"""
    operation_type: str = Field(..., description="操作類型")
    user_ids: List[str] = Field(..., description="用戶ID列表")
    operation_data: Dict[str, Any] = Field(..., description="操作數據")
    execute_at: Optional[datetime] = Field(None, description="執行時間")
    notification_enabled: bool = Field(True, description="是否發送通知")

class BulkOperationResult(BaseModel):
    """批量操作結果"""
    operation_id: str
    operation_type: str
    total_users: int
    successful_count: int
    failed_count: int
    failed_users: List[Dict[str, Any]] = Field(..., description="操作失敗的用戶")
    execution_time: datetime
    duration_seconds: float

# ==================== 用戶行為分析 ====================

@router.get("/analytics/behavior", 
           response_model=Dict[str, Any], 
           summary="獲取用戶行為分析數據")
async def get_user_behavior_analytics(
    time_range: str = Query("7d", description="時間範圍: 1d, 7d, 30d, 90d"),
    user_segment: Optional[str] = Query(None, description="用戶分群ID"),
    metrics: List[str] = Query(["engagement", "activity", "retention"], description="指標類型"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取用戶行為分析數據，支持多維度分析
    """
    try:
        # 解析時間範圍
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(time_range, 7)
        start_date = datetime.now() - timedelta(days=days)
        
        # 模擬數據 - 實際實施時連接真實數據庫
        analytics_data = {
            "overview": {
                "total_users": 12847,
                "active_users": 8934,
                "new_users": 234,
                "returning_users": 8700,
                "user_growth_rate": 2.1,
                "engagement_rate": 69.5
            },
            "activity_metrics": {
                "daily_active_users": [
                    {"date": "2025-08-14", "count": 1847},
                    {"date": "2025-08-13", "count": 1923},
                    {"date": "2025-08-12", "count": 1756},
                    {"date": "2025-08-11", "count": 1834},
                    {"date": "2025-08-10", "count": 1912},
                    {"date": "2025-08-09", "count": 1678},
                    {"date": "2025-08-08", "count": 1789}
                ],
                "session_duration": {
                    "average_minutes": 23.4,
                    "median_minutes": 18.7,
                    "distribution": {
                        "0-5min": 15.2,
                        "5-15min": 32.1,
                        "15-30min": 28.9,
                        "30-60min": 18.3,
                        "60min+": 5.5
                    }
                },
                "page_views": {
                    "total": 145678,
                    "per_user_avg": 16.3,
                    "top_pages": [
                        {"page": "/dashboard", "views": 34567, "unique_users": 3456},
                        {"page": "/portfolio", "views": 28934, "unique_users": 2893},
                        {"page": "/analysis", "views": 25678, "unique_users": 2567}
                    ]
                }
            },
            "feature_usage": {
                "portfolio_management": {"usage_count": 45678, "unique_users": 3456},
                "market_analysis": {"usage_count": 38934, "unique_users": 2893},
                "alert_system": {"usage_count": 29876, "unique_users": 2345},
                "educational_content": {"usage_count": 18765, "unique_users": 1876},
                "community_features": {"usage_count": 12345, "unique_users": 1234}
            },
            "user_segmentation": {
                "by_engagement": {
                    "highly_engaged": {"count": 2847, "percentage": 22.1},
                    "moderately_engaged": {"count": 6124, "percentage": 47.7},
                    "low_engaged": {"count": 3876, "percentage": 30.2}
                },
                "by_value": {
                    "premium_users": {"count": 1234, "percentage": 9.6},
                    "standard_users": {"count": 8765, "percentage": 68.2},
                    "trial_users": {"count": 2848, "percentage": 22.2}
                }
            },
            "churn_analysis": {
                "churn_rate": 3.2,
                "at_risk_users": 456,
                "factors": {
                    "low_engagement": 45.2,
                    "poor_performance": 23.1,
                    "support_issues": 18.7,
                    "pricing_concerns": 13.0
                }
            }
        }
        
        api_logger.info(f"User behavior analytics requested", extra={
            "user_id": current_user.user_id,
            "time_range": time_range,
            "metrics": metrics,
            "segment": user_segment
        })
        
        return analytics_data
        
    except Exception as e:
        return await handle_error(e, "獲取用戶行為分析數據失敗", api_logger)

@router.get("/analytics/cohort", 
           response_model=Dict[str, Any], 
           summary="獲取用戶群組分析數據")
async def get_cohort_analysis(
    cohort_type: str = Query("monthly", description="群組類型: weekly, monthly"),
    periods: int = Query(12, description="分析週期數"),
    metric: str = Query("retention", description="分析指標: retention, revenue"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取用戶群組分析數據，分析用戶留存和價值變化
    """
    try:
        # 模擬群組分析數據
        cohort_data = {
            "cohort_table": [
                {
                    "cohort": "2024-01",
                    "users": 1250,
                    "period_0": 100.0,
                    "period_1": 85.6,
                    "period_2": 76.3,
                    "period_3": 68.9,
                    "period_4": 62.1,
                    "period_5": 57.8,
                    "period_6": 54.2
                },
                {
                    "cohort": "2024-02",
                    "users": 1380,
                    "period_0": 100.0,
                    "period_1": 87.2,
                    "period_2": 78.9,
                    "period_3": 71.5,
                    "period_4": 64.8,
                    "period_5": 59.3
                },
                {
                    "cohort": "2024-03",
                    "users": 1456,
                    "period_0": 100.0,
                    "period_1": 89.1,
                    "period_2": 81.2,
                    "period_3": 74.6,
                    "period_4": 67.9
                }
            ],
            "retention_summary": {
                "day_1": 87.4,
                "day_7": 78.9,
                "day_30": 65.2,
                "day_90": 47.8
            },
            "trends": {
                "improving": ["user_onboarding", "feature_adoption"],
                "stable": ["monthly_retention", "user_satisfaction"],
                "declining": ["daily_engagement"]
            }
        }
        
        return cohort_data
        
    except Exception as e:
        return await handle_error(e, "獲取群組分析數據失敗", api_logger)

# ==================== 用戶標籤管理 ====================

@router.get("/tags", response_model=List[UserTag], summary="獲取用戶標籤列表")
async def get_user_tags(
    category: Optional[str] = Query(None, description="標籤類別"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取用戶標籤列表，支持按類別篩選和搜尋
    """
    try:
        # 模擬標籤數據
        tags = [
            UserTag(
                tag_id="tag_001",
                tag_name="高價值用戶",
                tag_category="value",
                tag_color="#10b981",
                description="月交易額超過10萬的用戶",
                user_count=234,
                is_system_tag=True,
                created_at=datetime.now()
            ),
            UserTag(
                tag_id="tag_002",
                tag_name="新手用戶",
                tag_category="experience",
                tag_color="#f59e0b",
                description="註冊不到30天的用戶",
                user_count=1456,
                is_system_tag=True,
                created_at=datetime.now()
            ),
            UserTag(
                tag_id="tag_003",
                tag_name="活躍交易者",
                tag_category="behavior",
                tag_color="#3b82f6",
                description="每週交易次數超過5次",
                user_count=867,
                is_system_tag=False,
                created_at=datetime.now()
            ),
            UserTag(
                tag_id="tag_004",
                tag_name="風險偏好高",
                tag_category="risk_profile",
                tag_color="#ef4444",
                description="投資組合風險評分>80",
                user_count=345,
                is_system_tag=False,
                created_at=datetime.now()
            )
        ]
        
        # 應用篩選
        if category:
            tags = [tag for tag in tags if tag.tag_category == category]
        if search:
            tags = [tag for tag in tags if search.lower() in tag.tag_name.lower()]
            
        return tags
        
    except Exception as e:
        return await handle_error(e, "獲取用戶標籤列表失敗", api_logger)

@router.post("/tags", response_model=UserTag, summary="創建新的用戶標籤")
async def create_user_tag(
    tag_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    創建新的用戶標籤
    """
    try:
        # 創建新標籤
        new_tag = UserTag(
            tag_id=f"tag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            tag_name=tag_data["tag_name"],
            tag_category=tag_data["tag_category"],
            tag_color=tag_data.get("tag_color", "#6b7280"),
            description=tag_data.get("description"),
            user_count=0,
            is_system_tag=False,
            created_at=datetime.now()
        )
        
        security_logger.info(f"New user tag created", extra={
            "admin_user": current_user.user_id,
            "tag_name": new_tag.tag_name,
            "tag_category": new_tag.tag_category
        })
        
        return new_tag
        
    except Exception as e:
        return await handle_error(e, "創建用戶標籤失敗", api_logger)

@router.post("/users/{user_id}/tags", summary="為用戶添加標籤")
async def assign_tags_to_user(
    user_id: str,
    tag_ids: List[str] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    為指定用戶添加標籤
    """
    try:
        # 模擬標籤分配
        result = {
            "user_id": user_id,
            "assigned_tags": tag_ids,
            "success": True,
            "message": f"成功為用戶添加 {len(tag_ids)} 個標籤"
        }
        
        security_logger.info(f"Tags assigned to user", extra={
            "admin_user": current_user.user_id,
            "target_user": user_id,
            "tag_count": len(tag_ids)
        })
        
        return result
        
    except Exception as e:
        return await handle_error(e, "為用戶添加標籤失敗", api_logger)

# ==================== 用戶分群管理 ====================

@router.get("/segments", response_model=List[UserSegment], summary="獲取用戶分群列表")
async def get_user_segments(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取所有用戶分群
    """
    try:
        segments = [
            UserSegment(
                segment_id="seg_001",
                segment_name="高價值VIP用戶",
                description="月交易金額超過50萬且連續活躍3個月以上",
                criteria={
                    "monthly_transaction_amount": {"min": 500000},
                    "active_months": {"min": 3},
                    "user_tier": ["diamond", "gold"]
                },
                user_count=456,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            UserSegment(
                segment_id="seg_002",
                segment_name="潛在流失用戶",
                description="最近30天活躍度下降且交易頻率減少",
                criteria={
                    "last_activity_days": {"min": 14},
                    "engagement_score": {"max": 30},
                    "transaction_frequency_change": {"max": -50}
                },
                user_count=234,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            UserSegment(
                segment_id="seg_003",
                segment_name="新用戶(入門期)",
                description="註冊不到30天的新用戶",
                criteria={
                    "registration_days": {"max": 30},
                    "completed_onboarding": True
                },
                user_count=1234,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        return segments
        
    except Exception as e:
        return await handle_error(e, "獲取用戶分群列表失敗", api_logger)

@router.get("/segments/{segment_id}/users", summary="獲取分群內的用戶")
async def get_segment_users(
    segment_id: str,
    page: int = Query(1, description="頁碼"),
    size: int = Query(20, description="每頁數量"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取指定分群內的用戶列表
    """
    try:
        # 模擬分群用戶數據
        users = [
            {
                "user_id": f"user_{i:04d}",
                "username": f"trader_{i:04d}",
                "email": f"user{i}@example.com",
                "registration_date": datetime.now() - timedelta(days=i*10),
                "last_activity": datetime.now() - timedelta(days=i),
                "segment_match_score": round(90 - i*0.5, 1),
                "tags": ["高價值用戶", "活躍交易者"] if i < 100 else ["新手用戶"]
            }
            for i in range((page-1)*size + 1, min(page*size + 1, 201))
        ]
        
        return {
            "segment_id": segment_id,
            "users": users,
            "pagination": {
                "page": page,
                "size": size,
                "total": 200,
                "total_pages": 10
            }
        }
        
    except Exception as e:
        return await handle_error(e, "獲取分群用戶失敗", api_logger)

# ==================== 生命週期管理 ====================

@router.get("/lifecycle/overview", 
           response_model=Dict[str, Any], 
           summary="獲取用戶生命週期概覽")
async def get_lifecycle_overview(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取用戶生命週期分佈和轉換數據
    """
    try:
        lifecycle_data = {
            "stage_distribution": {
                "prospect": {"count": 1234, "percentage": 9.6},
                "onboarding": {"count": 2345, "percentage": 18.3},
                "active": {"count": 6789, "percentage": 52.8},
                "power_user": {"count": 1567, "percentage": 12.2},
                "at_risk": {"count": 678, "percentage": 5.3},
                "churned": {"count": 234, "percentage": 1.8}
            },
            "transition_matrix": {
                "prospect_to_onboarding": 78.5,
                "onboarding_to_active": 65.2,
                "active_to_power_user": 23.1,
                "active_to_at_risk": 8.9,
                "at_risk_to_churned": 34.5,
                "at_risk_to_active": 45.2
            },
            "churn_prediction": {
                "high_risk_count": 456,
                "medium_risk_count": 789,
                "prevention_opportunities": 234
            }
        }
        
        return lifecycle_data
        
    except Exception as e:
        return await handle_error(e, "獲取生命週期概覽失敗", api_logger)

@router.get("/users/{user_id}/lifecycle", 
           response_model=UserLifecycleInfo, 
           summary="獲取用戶生命週期信息")
async def get_user_lifecycle(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取指定用戶的生命週期信息
    """
    try:
        # 模擬用戶生命週期數據
        lifecycle_info = UserLifecycleInfo(
            user_id=user_id,
            current_stage=UserLifecycleStage.ACTIVE,
            stage_duration=45,
            stage_history=[
                {"stage": "prospect", "start_date": "2024-01-15", "end_date": "2024-01-20", "duration": 5},
                {"stage": "onboarding", "start_date": "2024-01-20", "end_date": "2024-02-05", "duration": 16},
                {"stage": "active", "start_date": "2024-02-05", "end_date": None, "duration": 45}
            ],
            predicted_next_stage=UserLifecycleStage.POWER_USER,
            risk_score=25.3
        )
        
        return lifecycle_info
        
    except Exception as e:
        return await handle_error(e, "獲取用戶生命週期信息失敗", api_logger)

# ==================== 批量操作 ====================

@router.post("/bulk-operations", 
            response_model=BulkOperationResult, 
            summary="執行批量用戶操作")
async def execute_bulk_operation(
    operation: BulkOperationRequest,
    # background_tasks parameter removed for compatibility
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    執行批量用戶操作，如批量更新、批量發送郵件等
    """
    try:
        operation_id = f"bulk_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        # 模擬批量操作執行
        successful_count = len(operation.user_ids) - 2  # 模擬2個失敗
        failed_count = 2
        failed_users = [
            {"user_id": operation.user_ids[0], "error": "用戶不存在"},
            {"user_id": operation.user_ids[1], "error": "權限不足"}
        ] if len(operation.user_ids) > 1 else []
        
        # 記錄安全日誌
        security_logger.info(f"Bulk operation executed", extra={
            "admin_user": current_user.user_id,
            "operation_type": operation.operation_type,
            "target_users": len(operation.user_ids),
            "operation_id": operation_id
        })
        
        result = BulkOperationResult(
            operation_id=operation_id,
            operation_type=operation.operation_type,
            total_users=len(operation.user_ids),
            successful_count=successful_count,
            failed_count=failed_count,
            failed_users=failed_users,
            execution_time=start_time,
            duration_seconds=(datetime.now() - start_time).total_seconds()
        )
        
        return result
        
    except Exception as e:
        return await handle_error(e, "批量操作執行失敗", api_logger)

@router.get("/bulk-operations/{operation_id}", 
           response_model=Dict[str, Any], 
           summary="獲取批量操作狀態")
async def get_bulk_operation_status(
    operation_id: str,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取批量操作的執行狀態和結果
    """
    try:
        # 模擬操作狀態數據
        status_data = {
            "operation_id": operation_id,
            "status": "completed",
            "progress": 100,
            "total_users": 1000,
            "processed_users": 1000,
            "successful_count": 985,
            "failed_count": 15,
            "start_time": datetime.now() - timedelta(minutes=5),
            "end_time": datetime.now(),
            "error_log": [
                {"user_id": "user_0001", "error": "Email格式錯誤"},
                {"user_id": "user_0015", "error": "用戶已停用"}
            ]
        }
        
        return status_data
        
    except Exception as e:
        return await handle_error(e, "獲取批量操作狀態失敗", api_logger)

# ==================== 智能推薦 ====================

@router.get("/recommendations/segments", 
           response_model=List[Dict[str, Any]], 
           summary="獲取智能分群推薦")
async def get_segment_recommendations(
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    基於用戶行為分析，智能推薦新的用戶分群
    """
    try:
        recommendations = [
            {
                "segment_name": "高潛力新用戶",
                "description": "註冊後7天內完成首次交易且交易金額>1萬的用戶",
                "estimated_size": 234,
                "confidence_score": 85.6,
                "business_impact": "high",
                "criteria": {
                    "registration_days": {"max": 7},
                    "first_transaction_amount": {"min": 10000},
                    "completed_kyc": True
                }
            },
            {
                "segment_name": "沉默用戶待激活",
                "description": "註冊超過30天但交易次數少於3次的用戶",
                "estimated_size": 567,
                "confidence_score": 78.9,
                "business_impact": "medium",
                "criteria": {
                    "registration_days": {"min": 30},
                    "transaction_count": {"max": 3},
                    "last_login_days": {"min": 7}
                }
            }
        ]
        
        return recommendations
        
    except Exception as e:
        return await handle_error(e, "獲取分群推薦失敗", api_logger)

@router.get("/recommendations/tags", 
           response_model=List[Dict[str, Any]], 
           summary="獲取智能標籤推薦")
async def get_tag_recommendations(
    user_id: str = Query(..., description="用戶ID"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    為指定用戶智能推薦標籤
    """
    try:
        recommendations = [
            {
                "tag_name": "成長型投資者",
                "confidence": 89.5,
                "reason": "該用戶70%的投資集中在成長型股票",
                "tag_category": "investment_style"
            },
            {
                "tag_name": "技術分析愛好者",
                "confidence": 76.3,
                "reason": "頻繁使用技術分析工具，查看技術指標",
                "tag_category": "behavior"
            },
            {
                "tag_name": "高頻交易者",
                "confidence": 82.1,
                "reason": "月平均交易次數達到15次",
                "tag_category": "activity"
            }
        ]
        
        return recommendations
        
    except Exception as e:
        return await handle_error(e, "獲取標籤推薦失敗", api_logger)