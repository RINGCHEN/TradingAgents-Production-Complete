#!/usr/bin/env python3
"""
報表生成模型 (Reporting Models)
天工 (TianGong) - 報表生成相關的數據模型

此模組定義報表生成功能的所有數據模型，包含：
1. 報表請求和結果模型
2. 報表模板模型
3. 報表調度模型
4. 報表分發模型
5. 圖表和可視化模型
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator

# ==================== 基礎枚舉 ====================

class ReportType(str, Enum):
    """報表類型"""
    USER_ANALYTICS = "user_analytics"
    FINANCIAL = "financial"
    SYSTEM_PERFORMANCE = "system_performance"
    MARKETING = "marketing"
    CUSTOM = "custom"
    COMPLIANCE = "compliance"
    SECURITY = "security"

class ReportStatus(str, Enum):
    """報表狀態"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReportExportFormat(str, Enum):
    """報表導出格式"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"

class ChartType(str, Enum):
    """圖表類型"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    RADAR = "radar"
    HEATMAP = "heatmap"
    GAUGE = "gauge"

class ScheduleFrequency(str, Enum):
    """調度頻率"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"

# ==================== 報表請求模型 ====================

class ReportRequest(BaseModel):
    """報表請求模型"""
    report_type: ReportType
    title: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    export_formats: Optional[List[ReportExportFormat]] = None
    include_charts: bool = True
    include_raw_data: bool = False
    created_by: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CustomReportRequest(ReportRequest):
    """自定義報表請求模型"""
    template_id: Optional[str] = None
    sections: List[str] = []
    filters: Optional[Dict[str, Any]] = None
    grouping: Optional[List[str]] = None
    sorting: Optional[Dict[str, str]] = None

# ==================== 報表結果模型 ====================

class ReportMetadata(BaseModel):
    """報表元數據模型"""
    report_id: str
    report_type: ReportType
    title: str
    description: Optional[str] = None
    created_at: datetime
    created_by: str
    parameters: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ReportChart(BaseModel):
    """報表圖表模型"""
    chart_id: str
    title: str
    chart_type: ChartType
    data: str  # base64編碼的圖片數據
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class ReportSection(BaseModel):
    """報表章節模型"""
    section_id: str
    title: str
    content: Dict[str, Any]
    charts: Optional[List[ReportChart]] = None
    order: int = 0

class ReportResult(BaseModel):
    """報表結果模型"""
    report_id: str
    metadata: ReportMetadata
    content: Dict[str, Any]
    charts: List[ReportChart] = []
    sections: Optional[List[ReportSection]] = None
    status: ReportStatus
    generated_at: datetime
    file_paths: Dict[str, str] = {}  # 格式 -> 文件路徑
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 報表模板模型 ====================

class ReportTemplate(BaseModel):
    """報表模板模型"""
    template_id: str
    name: str
    description: Optional[str] = None
    report_type: ReportType
    sections: List[Dict[str, Any]] = []
    parameters: Dict[str, Any] = {}
    default_charts: List[str] = []
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TemplateSection(BaseModel):
    """模板章節模型"""
    section_id: str
    title: str
    data_source: str  # 數據源查詢
    chart_configs: List[Dict[str, Any]] = []
    filters: Optional[Dict[str, Any]] = None
    order: int = 0

# ==================== 報表調度模型 ====================

class ReportSchedule(BaseModel):
    """報表調度模型"""
    schedule_id: str
    name: str
    description: Optional[str] = None
    report_template_id: str
    frequency: ScheduleFrequency = ScheduleFrequency.WEEKLY
    cron_expression: Optional[str] = None
    parameters: Dict[str, Any] = {}
    recipients: List[str] = []  # 郵箱列表
    export_formats: List[ReportExportFormat] = [ReportExportFormat.PDF]
    is_active: bool = True
    created_at: datetime
    created_by: str
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScheduleExecution(BaseModel):
    """調度執行記錄模型"""
    execution_id: str
    schedule_id: str
    report_id: Optional[str] = None
    status: ReportStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 報表分發模型 ====================

class ReportDistribution(BaseModel):
    """報表分發模型"""
    distribution_id: str
    report_id: str
    recipients: List[str]
    distribution_method: str  # "email", "slack", "webhook"
    status: str  # "pending", "sent", "failed"
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EmailDistribution(ReportDistribution):
    """郵件分發模型"""
    subject: str
    body: Optional[str] = None
    attachments: List[str] = []  # 文件路徑列表

class SlackDistribution(ReportDistribution):
    """Slack分發模型"""
    channel: str
    message: Optional[str] = None
    webhook_url: str

# ==================== 自定義報表模型 ====================

class CustomReport(BaseModel):
    """自定義報表模型"""
    report_id: str
    name: str
    description: Optional[str] = None
    query: str  # SQL查詢或數據源配置
    visualization_config: Dict[str, Any] = {}
    filters: List[Dict[str, Any]] = []
    parameters: Dict[str, Any] = {}
    created_by: str
    created_at: datetime
    is_public: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ReportFilter(BaseModel):
    """報表篩選器模型"""
    filter_id: str
    name: str
    field: str
    operator: str  # "eq", "ne", "gt", "lt", "in", "like"
    value: Any
    data_type: str  # "string", "number", "date", "boolean"

class ReportParameter(BaseModel):
    """報表參數模型"""
    parameter_id: str
    name: str
    label: str
    data_type: str
    default_value: Any
    required: bool = False
    options: Optional[List[Dict[str, Any]]] = None  # 下拉選項

# ==================== 請求響應模型 ====================

class ReportListRequest(BaseModel):
    """報表列表請求模型"""
    report_type: Optional[ReportType] = None
    status: Optional[ReportStatus] = None
    created_by: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be asc or desc')
        return v

class ReportListResponse(BaseModel):
    """報表列表響應模型"""
    items: List[ReportMetadata]
    total: int
    page: int
    page_size: int
    total_pages: int

class TemplateListResponse(BaseModel):
    """模板列表響應模型"""
    items: List[ReportTemplate]
    total: int

class ScheduleListResponse(BaseModel):
    """調度列表響應模型"""
    items: List[ReportSchedule]
    total: int

# ==================== 統計模型 ====================

class ReportStatistics(BaseModel):
    """報表統計模型"""
    total_reports: int
    reports_by_type: Dict[str, int]
    reports_by_status: Dict[str, int]
    reports_this_month: int
    most_popular_templates: List[Dict[str, Any]]
    average_generation_time: float  # 秒
    success_rate: float  # 0-1

class ReportUsageAnalytics(BaseModel):
    """報表使用分析模型"""
    period_start: datetime
    period_end: datetime
    total_generations: int
    unique_users: int
    most_used_formats: Dict[str, int]
    peak_usage_hours: List[int]
    user_engagement: Dict[str, Any]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== 系統配置模型 ====================

class ReportingSystemConfig(BaseModel):
    """報表系統配置模型"""
    max_concurrent_reports: int = 5
    default_export_format: ReportExportFormat = ReportExportFormat.PDF
    report_retention_days: int = 90
    max_file_size_mb: int = 100
    allowed_export_formats: List[ReportExportFormat] = [
        ReportExportFormat.PDF,
        ReportExportFormat.EXCEL,
        ReportExportFormat.CSV
    ]
    email_settings: Dict[str, Any] = {}
    storage_settings: Dict[str, Any] = {}

# ==================== 錯誤模型 ====================

class ReportError(BaseModel):
    """報表錯誤模型"""
    error_code: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    occurred_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }