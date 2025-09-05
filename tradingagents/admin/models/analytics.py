#!/usr/bin/env python3
"""
數據分析模型 (Analytics Models)
天工 (TianGong) - 數據分析相關的數據模型

此模組定義數據分析功能的所有數據模型，包含：
1. 分析查詢和結果模型
2. 用戶行為分析模型
3. 業務指標模型
4. 收入分析模型
5. 轉化率分析模型
6. 預測分析模型
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# ==================== 基礎枚舉 ====================

class AnalyticsTimeFrame(str, Enum):
    """分析時間範圍"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

class MetricType(str, Enum):
    """指標類型"""
    USER_BEHAVIOR = "user_behavior"
    BUSINESS_METRICS = "business_metrics"
    REVENUE = "revenue"
    CONVERSION = "conversion"
    ENGAGEMENT = "engagement"
    PERFORMANCE = "performance"

class ReportType(str, Enum):
    """報表類型"""
    COMPREHENSIVE = "comprehensive"
    USER_BEHAVIOR = "user_behavior"
    REVENUE = "revenue"
    CONVERSION = "conversion"
    PREDICTIVE = "predictive"

# ==================== 基礎查詢模型 ====================

class AnalyticsQuery(BaseModel):
    """分析查詢模型"""
    metric_type: MetricType
    time_frame: AnalyticsTimeFrame
    start_date: datetime
    end_date: datetime
    filters: Optional[Dict[str, Any]] = None
    group_by: Optional[List[str]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalyticsResult(BaseModel):
    """分析結果模型"""
    query: AnalyticsQuery
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 用戶行為分析模型 ====================

class UserBehaviorAnalytics(BaseModel):
    """用戶行為分析模型"""
    period_start: datetime
    period_end: datetime
    total_sessions: int
    unique_users: int
    avg_session_duration: float  # 分鐘
    bounce_rate: float  # 0-1
    page_views: int
    page_views_data: Dict[str, int]  # 頁面 -> 訪問次數
    traffic_sources: Dict[str, float]  # 來源 -> 比例
    device_distribution: Dict[str, float]  # 設備 -> 比例
    geographic_distribution: Dict[str, float]  # 地區 -> 比例
    user_journey_analysis: Dict[str, Any]
    retention_analysis: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 業務指標模型 ====================

class BusinessMetrics(BaseModel):
    """業務指標模型"""
    period_start: datetime
    period_end: datetime
    total_revenue: float
    total_users: int
    active_users: int
    premium_users: int
    api_calls: int
    revenue_growth_rate: float
    user_growth_rate: float
    engagement_rate: float
    daily_metrics: List[Dict[str, Any]]
    top_features: List[Dict[str, Any]]
    performance_indicators: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 收入分析模型 ====================

class RevenueAnalytics(BaseModel):
    """收入分析模型"""
    period_start: datetime
    period_end: datetime
    total_revenue: float
    subscription_revenue: float
    api_revenue: float
    other_revenue: float
    revenue_sources: Dict[str, float]
    monthly_revenue: List[Dict[str, Any]]
    customer_lifetime_value: float
    average_revenue_per_user: float
    churn_rate: float
    revenue_forecast: Dict[str, Any]
    pricing_analysis: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 轉化率分析模型 ====================

class ConversionAnalytics(BaseModel):
    """轉化率分析模型"""
    period_start: datetime
    period_end: datetime
    total_visitors: int
    registered_users: int
    trial_users: int
    paid_users: int
    conversion_funnel: Dict[str, int]
    registration_rate: float
    trial_conversion_rate: float
    payment_conversion_rate: float
    overall_conversion_rate: float
    ab_test_results: List[Dict[str, Any]]
    conversion_optimization: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 預測分析模型 ====================

class PredictiveAnalytics(BaseModel):
    """預測分析模型"""
    forecast_period_days: int
    user_growth_forecast: List[Dict[str, Any]]
    revenue_forecast: List[Dict[str, Any]]
    churn_prediction: Dict[str, Any]
    market_trends: Dict[str, Any]
    risk_factors: List[Dict[str, Any]]
    opportunities: List[Dict[str, Any]]

# ==================== 指標趨勢模型 ====================

class MetricTrend(BaseModel):
    """指標趨勢模型"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # "up", "down", "stable"
    time_period: str
    
    @validator('trend_direction')
    def validate_trend_direction(cls, v):
        if v not in ['up', 'down', 'stable']:
            raise ValueError('trend_direction must be up, down, or stable')
        return v

# ==================== 儀表板模型 ====================

class AnalyticsDashboard(BaseModel):
    """分析儀表板模型"""
    key_metrics: Dict[str, Any]
    real_time_data: Dict[str, Any]
    charts_data: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    last_updated: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 報表模型 ====================

class AnalyticsReport(BaseModel):
    """分析報表模型"""
    report_id: str
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    generated_at: datetime
    sections: List[Dict[str, Any]]
    summary: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AnalyticsExport(BaseModel):
    """分析導出模型"""
    export_id: str
    export_type: str  # "csv", "excel", "pdf"
    report_id: str
    file_url: Optional[str] = None
    status: str  # "pending", "processing", "completed", "failed"
    created_at: datetime
    expires_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 請求模型 ====================

class AnalyticsRequest(BaseModel):
    """分析請求模型"""
    metric_types: List[MetricType]
    time_frame: AnalyticsTimeFrame
    start_date: datetime
    end_date: datetime
    include_predictions: bool = False
    include_comparisons: bool = False
    filters: Optional[Dict[str, Any]] = None
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('end_date must be after start_date')
        return v

class ReportGenerationRequest(BaseModel):
    """報表生成請求模型"""
    report_type: ReportType
    time_frame: AnalyticsTimeFrame
    start_date: datetime
    end_date: datetime
    include_charts: bool = True
    include_recommendations: bool = True
    export_format: str = "pdf"  # "pdf", "excel", "csv"
    
    @validator('export_format')
    def validate_export_format(cls, v):
        if v not in ['pdf', 'excel', 'csv']:
            raise ValueError('export_format must be pdf, excel, or csv')
        return v

# ==================== 響應模型 ====================

class AnalyticsResponse(BaseModel):
    """分析響應模型"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DashboardResponse(BaseModel):
    """儀表板響應模型"""
    dashboard: AnalyticsDashboard
    trends: List[MetricTrend]
    alerts_count: int
    system_status: str
    
class ReportResponse(BaseModel):
    """報表響應模型"""
    report: AnalyticsReport
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }