#!/usr/bin/env python3
"""
系統監控 API 模型

提供系統監控相關的 Pydantic 模型定義
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============================================================================
# 基礎枚舉
# ============================================================================

class AlertLevel(str, Enum):
    """告警級別"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """指標類型"""
    SYSTEM = "system"
    APPLICATION = "application"
    BUSINESS = "business"
    AI_ANALYSIS = "ai_analysis"


class PerformanceLevel(str, Enum):
    """性能等級"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class SystemStatus(str, Enum):
    """系統狀態"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


# ============================================================================
# 系統指標模型
# ============================================================================

class SystemMetrics(BaseModel):
    """系統指標模型"""
    timestamp: datetime = Field(..., description="時間戳")
    
    # CPU 指標
    cpu_percent: float = Field(..., description="CPU 使用率 (%)")
    cpu_count: int = Field(..., description="CPU 核心數")
    load_average: Optional[float] = Field(None, description="系統負載平均值")
    
    # 內存指標
    memory_total: int = Field(..., description="總內存 (bytes)")
    memory_used: int = Field(..., description="已用內存 (bytes)")
    memory_percent: float = Field(..., description="內存使用率 (%)")
    memory_available: int = Field(..., description="可用內存 (bytes)")
    
    # 磁盤指標
    disk_total: int = Field(..., description="總磁盤空間 (bytes)")
    disk_used: int = Field(..., description="已用磁盤空間 (bytes)")
    disk_percent: float = Field(..., description="磁盤使用率 (%)")
    disk_free: int = Field(..., description="可用磁盤空間 (bytes)")
    
    # 網絡指標
    network_io_sent: int = Field(..., description="網絡發送字節數")
    network_io_recv: int = Field(..., description="網絡接收字節數")
    network_connections: int = Field(..., description="網絡連接數")
    
    # 進程指標
    process_count: int = Field(..., description="進程數量")
    thread_count: int = Field(..., description="線程數量")
    
    # 系統運行時間
    boot_time: datetime = Field(..., description="系統啟動時間")
    uptime_seconds: int = Field(..., description="系統運行時間 (秒)")


class ApplicationMetrics(BaseModel):
    """應用指標模型"""
    timestamp: datetime = Field(..., description="時間戳")
    
    # 應用基本信息
    app_name: str = Field(..., description="應用名稱")
    app_version: str = Field(..., description="應用版本")
    app_uptime: int = Field(..., description="應用運行時間 (秒)")
    
    # 請求指標
    total_requests: int = Field(..., description="總請求數")
    requests_per_second: float = Field(..., description="每秒請求數")
    average_response_time: float = Field(..., description="平均響應時間 (ms)")
    error_rate: float = Field(..., description="錯誤率 (%)")
    
    # 數據庫指標
    db_connections_active: int = Field(..., description="活躍數據庫連接數")
    db_connections_idle: int = Field(..., description="空閒數據庫連接數")
    db_query_time_avg: float = Field(..., description="平均數據庫查詢時間 (ms)")
    
    # 緩存指標
    cache_hit_rate: float = Field(..., description="緩存命中率 (%)")
    cache_memory_usage: int = Field(..., description="緩存內存使用量 (bytes)")
    
    # AI 分析指標
    ai_analyses_total: int = Field(..., description="總 AI 分析次數")
    ai_analyses_success: int = Field(..., description="成功 AI 分析次數")
    ai_analysis_avg_time: float = Field(..., description="平均 AI 分析時間 (ms)")


class PerformanceMetrics(BaseModel):
    """性能指標模型"""
    timestamp: datetime = Field(..., description="時間戳")
    
    # 響應時間指標
    response_time_p50: float = Field(..., description="響應時間 P50 (ms)")
    response_time_p95: float = Field(..., description="響應時間 P95 (ms)")
    response_time_p99: float = Field(..., description="響應時間 P99 (ms)")
    
    # 吞吐量指標
    throughput_rps: float = Field(..., description="吞吐量 (requests/second)")
    throughput_tps: float = Field(..., description="事務吞吐量 (transactions/second)")
    
    # 錯誤指標
    error_count: int = Field(..., description="錯誤數量")
    error_rate: float = Field(..., description="錯誤率 (%)")
    
    # 資源利用率
    cpu_utilization: float = Field(..., description="CPU 利用率 (%)")
    memory_utilization: float = Field(..., description="內存利用率 (%)")
    disk_io_utilization: float = Field(..., description="磁盤 I/O 利用率 (%)")
    network_utilization: float = Field(..., description="網絡利用率 (%)")
    
    # 性能等級
    overall_performance: PerformanceLevel = Field(..., description="整體性能等級")


# ============================================================================
# 告警模型
# ============================================================================

class Alert(BaseModel):
    """告警模型"""
    id: str = Field(..., description="告警 ID")
    level: AlertLevel = Field(..., description="告警級別")
    title: str = Field(..., description="告警標題")
    message: str = Field(..., description="告警消息")
    metric_type: MetricType = Field(..., description="指標類型")
    metric_name: str = Field(..., description="指標名稱")
    current_value: Union[float, int, str] = Field(..., description="當前值")
    threshold_value: Union[float, int, str] = Field(..., description="閾值")
    
    # 時間信息
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")
    resolved_at: Optional[datetime] = Field(None, description="解決時間")
    
    # 狀態信息
    is_active: bool = Field(True, description="是否活躍")
    is_acknowledged: bool = Field(False, description="是否已確認")
    acknowledged_by: Optional[str] = Field(None, description="確認人")
    acknowledged_at: Optional[datetime] = Field(None, description="確認時間")
    
    # 額外信息
    tags: List[str] = Field(default_factory=list, description="標籤")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")


class AlertSummary(BaseModel):
    """告警摘要模型"""
    total_alerts: int = Field(..., description="總告警數")
    active_alerts: int = Field(..., description="活躍告警數")
    critical_alerts: int = Field(..., description="嚴重告警數")
    warning_alerts: int = Field(..., description="警告告警數")
    info_alerts: int = Field(..., description="信息告警數")
    
    # 按級別分組
    alerts_by_level: Dict[str, int] = Field(..., description="按級別分組的告警數")
    
    # 按類型分組
    alerts_by_type: Dict[str, int] = Field(..., description="按類型分組的告警數")
    
    # 最近告警
    recent_alerts: List[Alert] = Field(..., description="最近告警列表")


# ============================================================================
# 健康檢查模型
# ============================================================================

class HealthCheckResult(BaseModel):
    """健康檢查結果模型"""
    component: str = Field(..., description="組件名稱")
    status: SystemStatus = Field(..., description="狀態")
    message: str = Field(..., description="狀態消息")
    response_time: float = Field(..., description="響應時間 (ms)")
    last_check: datetime = Field(..., description="最後檢查時間")
    
    # 詳細信息
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細信息")
    
    # 依賴檢查
    dependencies: List[str] = Field(default_factory=list, description="依賴組件")


class SystemHealthStatus(BaseModel):
    """系統健康狀態模型"""
    overall_status: SystemStatus = Field(..., description="整體狀態")
    status_message: str = Field(..., description="狀態消息")
    last_updated: datetime = Field(..., description="最後更新時間")
    
    # 組件健康狀態
    components: List[HealthCheckResult] = Field(..., description="組件健康狀態")
    
    # 統計信息
    healthy_components: int = Field(..., description="健康組件數")
    warning_components: int = Field(..., description="警告組件數")
    error_components: int = Field(..., description="錯誤組件數")
    critical_components: int = Field(..., description="嚴重組件數")
    
    # 系統指標
    system_metrics: SystemMetrics = Field(..., description="系統指標")
    application_metrics: ApplicationMetrics = Field(..., description="應用指標")
    performance_metrics: PerformanceMetrics = Field(..., description="性能指標")


# ============================================================================
# 監控配置模型
# ============================================================================

class MonitoringThreshold(BaseModel):
    """監控閾值模型"""
    metric_name: str = Field(..., description="指標名稱")
    warning_threshold: Union[float, int] = Field(..., description="警告閾值")
    critical_threshold: Union[float, int] = Field(..., description="嚴重閾值")
    comparison_operator: str = Field(..., description="比較操作符")  # >, <, >=, <=, ==, !=
    enabled: bool = Field(True, description="是否啟用")
    
    # 告警配置
    alert_interval: int = Field(300, description="告警間隔 (秒)")
    auto_resolve: bool = Field(True, description="是否自動解決")
    
    # 描述信息
    description: str = Field(..., description="閾值描述")
    unit: str = Field(..., description="單位")


class MonitoringConfiguration(BaseModel):
    """監控配置模型"""
    # 基本配置
    monitoring_enabled: bool = Field(True, description="是否啟用監控")
    collection_interval: int = Field(60, description="數據收集間隔 (秒)")
    retention_days: int = Field(30, description="數據保留天數")
    
    # 告警配置
    alerting_enabled: bool = Field(True, description="是否啟用告警")
    alert_channels: List[str] = Field(default_factory=list, description="告警通道")
    
    # 閾值配置
    thresholds: List[MonitoringThreshold] = Field(..., description="監控閾值")
    
    # 健康檢查配置
    health_check_interval: int = Field(30, description="健康檢查間隔 (秒)")
    health_check_timeout: int = Field(10, description="健康檢查超時 (秒)")
    
    # 性能監控配置
    performance_monitoring_enabled: bool = Field(True, description="是否啟用性能監控")
    performance_sampling_rate: float = Field(1.0, description="性能採樣率")


# ============================================================================
# 統計和報告模型
# ============================================================================

class MonitoringStatistics(BaseModel):
    """監控統計模型"""
    # 時間範圍
    start_time: datetime = Field(..., description="開始時間")
    end_time: datetime = Field(..., description="結束時間")
    
    # 系統統計
    avg_cpu_usage: float = Field(..., description="平均 CPU 使用率")
    max_cpu_usage: float = Field(..., description="最大 CPU 使用率")
    avg_memory_usage: float = Field(..., description="平均內存使用率")
    max_memory_usage: float = Field(..., description="最大內存使用率")
    
    # 應用統計
    total_requests: int = Field(..., description="總請求數")
    avg_response_time: float = Field(..., description="平均響應時間")
    error_count: int = Field(..., description="錯誤數量")
    error_rate: float = Field(..., description="錯誤率")
    
    # 告警統計
    total_alerts: int = Field(..., description="總告警數")
    critical_alerts: int = Field(..., description="嚴重告警數")
    resolved_alerts: int = Field(..., description="已解決告警數")
    
    # 性能統計
    avg_performance_score: float = Field(..., description="平均性能分數")
    performance_trend: str = Field(..., description="性能趨勢")  # improving, stable, degrading


class SystemReport(BaseModel):
    """系統報告模型"""
    # 報告基本信息
    report_id: str = Field(..., description="報告 ID")
    report_type: str = Field(..., description="報告類型")  # daily, weekly, monthly
    generated_at: datetime = Field(..., description="生成時間")
    period_start: datetime = Field(..., description="報告期間開始")
    period_end: datetime = Field(..., description="報告期間結束")
    
    # 系統概覽
    system_overview: Dict[str, Any] = Field(..., description="系統概覽")
    
    # 統計數據
    statistics: MonitoringStatistics = Field(..., description="統計數據")
    
    # 告警摘要
    alert_summary: AlertSummary = Field(..., description="告警摘要")
    
    # 性能分析
    performance_analysis: Dict[str, Any] = Field(..., description="性能分析")
    
    # 建議和改進
    recommendations: List[str] = Field(..., description="建議列表")
    
    # 趨勢分析
    trends: Dict[str, Any] = Field(..., description="趨勢分析")


# ============================================================================
# 請求和響應模型
# ============================================================================

class MonitoringQuery(BaseModel):
    """監控查詢模型"""
    metric_types: Optional[List[MetricType]] = Field(None, description="指標類型篩選")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    interval: Optional[int] = Field(None, description="時間間隔 (秒)")
    aggregation: Optional[str] = Field("avg", description="聚合方式")  # avg, sum, max, min
    limit: Optional[int] = Field(100, description="返回記錄數限制")


class AlertQuery(BaseModel):
    """告警查詢模型"""
    levels: Optional[List[AlertLevel]] = Field(None, description="告警級別篩選")
    types: Optional[List[MetricType]] = Field(None, description="指標類型篩選")
    is_active: Optional[bool] = Field(None, description="是否活躍")
    is_acknowledged: Optional[bool] = Field(None, description="是否已確認")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    limit: Optional[int] = Field(50, description="返回記錄數限制")


class AlertAcknowledgment(BaseModel):
    """告警確認模型"""
    alert_ids: List[str] = Field(..., description="告警 ID 列表")
    acknowledged_by: str = Field(..., description="確認人")
    comment: Optional[str] = Field(None, description="確認備註")


# ============================================================================
# 系統信息模型
# ============================================================================

class SystemInformation(BaseModel):
    """系統信息模型"""
    # 基本信息
    hostname: str = Field(..., description="主機名")
    platform: str = Field(..., description="平台")
    architecture: str = Field(..., description="架構")
    python_version: str = Field(..., description="Python 版本")
    
    # 應用信息
    app_name: str = Field(..., description="應用名稱")
    app_version: str = Field(..., description="應用版本")
    environment: str = Field(..., description="運行環境")
    
    # 硬件信息
    cpu_info: Dict[str, Any] = Field(..., description="CPU 信息")
    memory_info: Dict[str, Any] = Field(..., description="內存信息")
    disk_info: Dict[str, Any] = Field(..., description="磁盤信息")
    network_info: Dict[str, Any] = Field(..., description="網絡信息")
    
    # 運行時信息
    start_time: datetime = Field(..., description="啟動時間")
    uptime: int = Field(..., description="運行時間 (秒)")
    timezone: str = Field(..., description="時區")
    
    # 配置信息
    monitoring_config: MonitoringConfiguration = Field(..., description="監控配置")


class MonitoringDashboard(BaseModel):
    """監控儀表板模型"""
    # 儀表板信息
    dashboard_id: str = Field(..., description="儀表板 ID")
    title: str = Field(..., description="儀表板標題")
    last_updated: datetime = Field(..., description="最後更新時間")
    
    # 系統狀態
    system_status: SystemHealthStatus = Field(..., description="系統健康狀態")
    
    # 實時指標
    real_time_metrics: Dict[str, Any] = Field(..., description="實時指標")
    
    # 告警摘要
    alert_summary: AlertSummary = Field(..., description="告警摘要")
    
    # 性能概覽
    performance_overview: Dict[str, Any] = Field(..., description="性能概覽")
    
    # 圖表數據
    charts_data: Dict[str, List[Dict[str, Any]]] = Field(..., description="圖表數據")