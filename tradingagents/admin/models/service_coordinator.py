#!/usr/bin/env python3
"""
服務協調器 API 模型

提供服務協調器相關的 Pydantic 模型定義
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============================================================================
# 基礎枚舉
# ============================================================================

class ServiceStatus(str, Enum):
    """服務狀態"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"
    MAINTENANCE = "maintenance"


class ServiceType(str, Enum):
    """服務類型"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    QUEUE = "queue"
    EXTERNAL = "external"
    AI_ANALYSIS = "ai_analysis"
    DATA_PROCESSING = "data_processing"
    NOTIFICATION = "notification"


class TaskStatus(str, Enum):
    """任務狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(str, Enum):
    """任務優先級"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class CoordinationStrategy(str, Enum):
    """協調策略"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    PIPELINE = "pipeline"
    CONDITIONAL = "conditional"
    RETRY = "retry"


# ============================================================================
# 服務管理模型
# ============================================================================

class ServiceInfo(BaseModel):
    """服務信息模型"""
    service_id: str = Field(..., description="服務ID")
    service_name: str = Field(..., description="服務名稱")
    service_type: ServiceType = Field(..., description="服務類型")
    version: str = Field(..., description="服務版本")
    
    # 狀態信息
    status: ServiceStatus = Field(..., description="服務狀態")
    health_status: str = Field(..., description="健康狀態")
    last_health_check: datetime = Field(..., description="最後健康檢查時間")
    
    # 配置信息
    endpoint: Optional[str] = Field(None, description="服務端點")
    port: Optional[int] = Field(None, description="服務端口")
    config: Dict[str, Any] = Field(default_factory=dict, description="服務配置")
    
    # 依賴關係
    dependencies: List[str] = Field(default_factory=list, description="依賴的服務")
    dependents: List[str] = Field(default_factory=list, description="依賴此服務的服務")
    
    # 性能指標
    cpu_usage: Optional[float] = Field(None, description="CPU使用率")
    memory_usage: Optional[float] = Field(None, description="內存使用率")
    request_count: Optional[int] = Field(None, description="請求數量")
    error_count: Optional[int] = Field(None, description="錯誤數量")
    
    # 時間信息
    started_at: Optional[datetime] = Field(None, description="啟動時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class ServiceRegistry(BaseModel):
    """服務註冊表模型"""
    services: List[ServiceInfo] = Field(..., description="服務列表")
    total_services: int = Field(..., description="總服務數")
    running_services: int = Field(..., description="運行中的服務數")
    error_services: int = Field(..., description="錯誤服務數")
    last_updated: datetime = Field(..., description="最後更新時間")


class ServiceCommand(BaseModel):
    """服務命令模型"""
    service_id: str = Field(..., description="服務ID")
    command: str = Field(..., description="命令")  # start, stop, restart, reload
    parameters: Dict[str, Any] = Field(default_factory=dict, description="命令參數")
    timeout: int = Field(30, description="超時時間（秒）")
    force: bool = Field(False, description="是否強制執行")


class ServiceCommandResult(BaseModel):
    """服務命令執行結果模型"""
    service_id: str = Field(..., description="服務ID")
    command: str = Field(..., description="執行的命令")
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="執行結果消息")
    execution_time: float = Field(..., description="執行時間（秒）")
    executed_at: datetime = Field(..., description="執行時間")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細信息")


# ============================================================================
# 任務協調模型
# ============================================================================

class TaskDefinition(BaseModel):
    """任務定義模型"""
    task_id: str = Field(..., description="任務ID")
    task_name: str = Field(..., description="任務名稱")
    task_type: str = Field(..., description="任務類型")
    description: str = Field(..., description="任務描述")
    
    # 執行配置
    service_id: str = Field(..., description="執行服務ID")
    function_name: str = Field(..., description="執行函數名")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任務參數")
    
    # 調度配置
    priority: TaskPriority = Field(TaskPriority.NORMAL, description="任務優先級")
    timeout: int = Field(300, description="超時時間（秒）")
    retry_count: int = Field(3, description="重試次數")
    retry_delay: int = Field(60, description="重試延遲（秒）")
    
    # 依賴關係
    dependencies: List[str] = Field(default_factory=list, description="依賴的任務")
    
    # 調度規則
    schedule: Optional[str] = Field(None, description="調度規則（cron表達式）")
    enabled: bool = Field(True, description="是否啟用")
    
    # 時間信息
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")


class TaskExecution(BaseModel):
    """任務執行模型"""
    execution_id: str = Field(..., description="執行ID")
    task_id: str = Field(..., description="任務ID")
    task_name: str = Field(..., description="任務名稱")
    
    # 執行狀態
    status: TaskStatus = Field(..., description="執行狀態")
    progress: float = Field(0.0, description="執行進度（0-100）")
    
    # 執行信息
    service_id: str = Field(..., description="執行服務ID")
    worker_id: Optional[str] = Field(None, description="工作進程ID")
    
    # 時間信息
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    duration: Optional[float] = Field(None, description="執行時長（秒）")
    
    # 結果信息
    result: Optional[Dict[str, Any]] = Field(None, description="執行結果")
    error_message: Optional[str] = Field(None, description="錯誤消息")
    logs: List[str] = Field(default_factory=list, description="執行日誌")
    
    # 重試信息
    retry_count: int = Field(0, description="已重試次數")
    max_retries: int = Field(3, description="最大重試次數")
    
    class Config:
        from_attributes = True


class WorkflowDefinition(BaseModel):
    """工作流定義模型"""
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名稱")
    description: str = Field(..., description="工作流描述")
    
    # 任務配置
    tasks: List[TaskDefinition] = Field(..., description="任務列表")
    coordination_strategy: CoordinationStrategy = Field(..., description="協調策略")
    
    # 執行配置
    timeout: int = Field(3600, description="總超時時間（秒）")
    max_concurrent_tasks: int = Field(10, description="最大並發任務數")
    
    # 調度配置
    schedule: Optional[str] = Field(None, description="調度規則")
    enabled: bool = Field(True, description="是否啟用")
    
    # 時間信息
    created_at: datetime = Field(..., description="創建時間")
    updated_at: datetime = Field(..., description="更新時間")


class WorkflowExecution(BaseModel):
    """工作流執行模型"""
    execution_id: str = Field(..., description="執行ID")
    workflow_id: str = Field(..., description="工作流ID")
    workflow_name: str = Field(..., description="工作流名稱")
    
    # 執行狀態
    status: TaskStatus = Field(..., description="執行狀態")
    progress: float = Field(0.0, description="執行進度")
    
    # 任務執行
    task_executions: List[TaskExecution] = Field(..., description="任務執行列表")
    completed_tasks: int = Field(0, description="已完成任務數")
    failed_tasks: int = Field(0, description="失敗任務數")
    
    # 時間信息
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    duration: Optional[float] = Field(None, description="執行時長")
    
    # 結果信息
    result: Optional[Dict[str, Any]] = Field(None, description="執行結果")
    error_message: Optional[str] = Field(None, description="錯誤消息")
    
    class Config:
        from_attributes = True


# ============================================================================
# 協調器配置模型
# ============================================================================

class CoordinatorConfiguration(BaseModel):
    """協調器配置模型"""
    # 基本配置
    coordinator_enabled: bool = Field(True, description="是否啟用協調器")
    max_concurrent_workflows: int = Field(50, description="最大並發工作流數")
    max_concurrent_tasks: int = Field(200, description="最大並發任務數")
    
    # 調度配置
    scheduler_enabled: bool = Field(True, description="是否啟用調度器")
    scheduler_interval: int = Field(10, description="調度器檢查間隔（秒）")
    
    # 重試配置
    default_retry_count: int = Field(3, description="默認重試次數")
    default_retry_delay: int = Field(60, description="默認重試延遲（秒）")
    exponential_backoff: bool = Field(True, description="是否使用指數退避")
    
    # 超時配置
    default_task_timeout: int = Field(300, description="默認任務超時（秒）")
    default_workflow_timeout: int = Field(3600, description="默認工作流超時（秒）")
    
    # 監控配置
    monitoring_enabled: bool = Field(True, description="是否啟用監控")
    metrics_collection_interval: int = Field(30, description="指標收集間隔（秒）")
    
    # 日誌配置
    log_level: str = Field("INFO", description="日誌級別")
    log_retention_days: int = Field(30, description="日誌保留天數")
    
    # 通知配置
    notification_enabled: bool = Field(True, description="是否啟用通知")
    notification_channels: List[str] = Field(default_factory=list, description="通知渠道")


# ============================================================================
# 統計和監控模型
# ============================================================================

class CoordinatorStatistics(BaseModel):
    """協調器統計模型"""
    # 服務統計
    total_services: int = Field(..., description="總服務數")
    running_services: int = Field(..., description="運行中服務數")
    error_services: int = Field(..., description="錯誤服務數")
    
    # 任務統計
    total_tasks: int = Field(..., description="總任務數")
    pending_tasks: int = Field(..., description="待執行任務數")
    running_tasks: int = Field(..., description="執行中任務數")
    completed_tasks: int = Field(..., description="已完成任務數")
    failed_tasks: int = Field(..., description="失敗任務數")
    
    # 工作流統計
    total_workflows: int = Field(..., description="總工作流數")
    active_workflows: int = Field(..., description="活躍工作流數")
    completed_workflows: int = Field(..., description="已完成工作流數")
    failed_workflows: int = Field(..., description="失敗工作流數")
    
    # 性能統計
    average_task_duration: float = Field(..., description="平均任務執行時間")
    average_workflow_duration: float = Field(..., description="平均工作流執行時間")
    success_rate: float = Field(..., description="成功率")
    
    # 資源統計
    cpu_usage: float = Field(..., description="CPU使用率")
    memory_usage: float = Field(..., description="內存使用率")
    
    # 時間統計
    uptime: int = Field(..., description="運行時間（秒）")
    last_updated: datetime = Field(..., description="最後更新時間")


class CoordinatorHealth(BaseModel):
    """協調器健康狀態模型"""
    overall_status: str = Field(..., description="整體狀態")
    coordinator_status: str = Field(..., description="協調器狀態")
    scheduler_status: str = Field(..., description="調度器狀態")
    
    # 組件狀態
    service_registry_status: str = Field(..., description="服務註冊表狀態")
    task_queue_status: str = Field(..., description="任務隊列狀態")
    workflow_engine_status: str = Field(..., description="工作流引擎狀態")
    
    # 健康檢查結果
    health_checks: List[Dict[str, Any]] = Field(..., description="健康檢查結果")
    
    # 時間信息
    last_check: datetime = Field(..., description="最後檢查時間")
    uptime: int = Field(..., description="運行時間")


# ============================================================================
# 請求和響應模型
# ============================================================================

class ServiceQuery(BaseModel):
    """服務查詢模型"""
    service_types: Optional[List[ServiceType]] = Field(None, description="服務類型篩選")
    statuses: Optional[List[ServiceStatus]] = Field(None, description="狀態篩選")
    health_status: Optional[str] = Field(None, description="健康狀態篩選")
    keyword: Optional[str] = Field(None, description="關鍵詞搜索")
    limit: int = Field(50, description="返回數量限制")


class TaskQuery(BaseModel):
    """任務查詢模型"""
    task_types: Optional[List[str]] = Field(None, description="任務類型篩選")
    statuses: Optional[List[TaskStatus]] = Field(None, description="狀態篩選")
    priorities: Optional[List[TaskPriority]] = Field(None, description="優先級篩選")
    service_ids: Optional[List[str]] = Field(None, description="服務ID篩選")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    limit: int = Field(100, description="返回數量限制")


class WorkflowQuery(BaseModel):
    """工作流查詢模型"""
    statuses: Optional[List[TaskStatus]] = Field(None, description="狀態篩選")
    strategies: Optional[List[CoordinationStrategy]] = Field(None, description="策略篩選")
    enabled: Optional[bool] = Field(None, description="是否啟用")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    limit: int = Field(50, description="返回數量限制")


class CoordinatorDashboard(BaseModel):
    """協調器儀表板模型"""
    dashboard_id: str = Field(..., description="儀表板ID")
    title: str = Field(..., description="儀表板標題")
    last_updated: datetime = Field(..., description="最後更新時間")
    
    # 統計信息
    statistics: CoordinatorStatistics = Field(..., description="統計信息")
    
    # 健康狀態
    health: CoordinatorHealth = Field(..., description="健康狀態")
    
    # 實時數據
    active_services: List[ServiceInfo] = Field(..., description="活躍服務")
    recent_tasks: List[TaskExecution] = Field(..., description="最近任務")
    active_workflows: List[WorkflowExecution] = Field(..., description="活躍工作流")
    
    # 圖表數據
    charts_data: Dict[str, List[Dict[str, Any]]] = Field(..., description="圖表數據")