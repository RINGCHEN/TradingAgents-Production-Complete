#!/usr/bin/env python3
"""
分析師協調器 API 模型

提供分析師協調器相關的 Pydantic 模型定義
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


# ============================================================================
# 基礎枚舉
# ============================================================================

class AnalystStatus(str, Enum):
    """分析師狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class AnalystType(str, Enum):
    """分析師類型"""
    FUNDAMENTALS = "fundamentals_analyst"
    NEWS = "news_analyst"
    RISK = "risk_analyst"
    SENTIMENT = "sentiment_analyst"
    INVESTMENT_PLANNER = "investment_planner"
    TAIWAN_MARKET = "taiwan_market_analyst"


class AnalysisType(str, Enum):
    """分析類型"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    NEWS_SENTIMENT = "news_sentiment"
    MARKET_SENTIMENT = "market_sentiment"
    RISK_ASSESSMENT = "risk_assessment"
    INVESTMENT_PLANNING = "investment_planning"
    TAIWAN_SPECIFIC = "taiwan_specific"


class AnalysisStatus(str, Enum):
    """分析狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AnalysisConfidenceLevel(str, Enum):
    """分析信心度級別"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# 分析師管理模型
# ============================================================================

class AnalystInfo(BaseModel):
    """分析師信息模型"""
    analyst_id: str = Field(..., description="分析師ID")
    analyst_name: str = Field(..., description="分析師名稱")
    analyst_type: AnalystType = Field(..., description="分析師類型")
    version: str = Field(..., description="分析師版本")
    
    # 狀態信息
    status: AnalystStatus = Field(..., description="分析師狀態")
    health_status: str = Field(..., description="健康狀態")
    last_health_check: datetime = Field(..., description="最後健康檢查時間")
    
    # 配置信息
    config: Dict[str, Any] = Field(default_factory=dict, description="分析師配置")
    capabilities: List[str] = Field(default_factory=list, description="分析師能力")
    supported_markets: List[str] = Field(default_factory=list, description="支持的市場")
    
    # 性能指標
    total_analyses: int = Field(0, description="總分析次數")
    successful_analyses: int = Field(0, description="成功分析次數")
    failed_analyses: int = Field(0, description="失敗分析次數")
    average_execution_time: float = Field(0.0, description="平均執行時間（秒）")
    success_rate: float = Field(0.0, description="成功率")
    
    # 時間信息
    created_at: datetime = Field(..., description="創建時間")
    last_used_at: Optional[datetime] = Field(None, description="最後使用時間")
    updated_at: datetime = Field(..., description="更新時間")
    
    class Config:
        from_attributes = True


class AnalystRegistry(BaseModel):
    """分析師註冊表模型"""
    analysts: List[AnalystInfo] = Field(..., description="分析師列表")
    total_analysts: int = Field(..., description="總分析師數")
    active_analysts: int = Field(..., description="活躍分析師數")
    busy_analysts: int = Field(..., description="忙碌分析師數")
    error_analysts: int = Field(..., description="錯誤分析師數")
    last_updated: datetime = Field(..., description="最後更新時間")


class AnalystCommand(BaseModel):
    """分析師命令模型"""
    analyst_id: str = Field(..., description="分析師ID")
    command: str = Field(..., description="命令")  # start, stop, restart, reload, reset
    parameters: Dict[str, Any] = Field(default_factory=dict, description="命令參數")
    timeout: int = Field(60, description="超時時間（秒）")


class AnalystCommandResult(BaseModel):
    """分析師命令執行結果模型"""
    analyst_id: str = Field(..., description="分析師ID")
    command: str = Field(..., description="執行的命令")
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="執行結果消息")
    execution_time: float = Field(..., description="執行時間（秒）")
    executed_at: datetime = Field(..., description="執行時間")
    details: Dict[str, Any] = Field(default_factory=dict, description="詳細信息")


# ============================================================================
# 分析任務模型
# ============================================================================

class AnalysisRequest(BaseModel):
    """分析請求模型"""
    request_id: str = Field(..., description="請求ID")
    stock_id: str = Field(..., description="股票代號")
    analysis_types: List[AnalysisType] = Field(..., description="分析類型列表")
    preferred_analysts: Optional[List[str]] = Field(None, description="指定分析師列表")
    
    # 請求配置
    priority: str = Field("normal", description="優先級")
    timeout: int = Field(300, description="超時時間（秒）")
    enable_debate: bool = Field(False, description="是否啟用辯論機制")
    
    # 用戶信息
    user_id: str = Field(..., description="用戶ID")
    user_tier: str = Field(..., description="用戶等級")
    
    # 額外參數
    additional_context: Dict[str, Any] = Field(default_factory=dict, description="額外上下文")
    
    # 時間信息
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")


class AnalysisExecution(BaseModel):
    """分析執行模型"""
    execution_id: str = Field(..., description="執行ID")
    request_id: str = Field(..., description="請求ID")
    stock_id: str = Field(..., description="股票代號")
    
    # 執行狀態
    status: AnalysisStatus = Field(..., description="執行狀態")
    progress: float = Field(0.0, description="執行進度（0-100）")
    
    # 分析師分配
    assigned_analysts: List[str] = Field(..., description="分配的分析師列表")
    completed_analysts: List[str] = Field(default_factory=list, description="已完成的分析師")
    failed_analysts: List[str] = Field(default_factory=list, description="失敗的分析師")
    
    # 時間信息
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    duration: Optional[float] = Field(None, description="執行時長（秒）")
    
    # 結果信息
    results: Dict[str, Any] = Field(default_factory=dict, description="分析結果")
    final_recommendation: Optional[str] = Field(None, description="最終建議")
    confidence_score: Optional[float] = Field(None, description="信心分數")
    error_message: Optional[str] = Field(None, description="錯誤消息")
    
    # 用戶信息
    user_id: str = Field(..., description="用戶ID")
    
    class Config:
        from_attributes = True


class AnalysisResult(BaseModel):
    """分析結果模型"""
    result_id: str = Field(..., description="結果ID")
    execution_id: str = Field(..., description="執行ID")
    analyst_id: str = Field(..., description="分析師ID")
    stock_id: str = Field(..., description="股票代號")
    
    # 分析結果
    analysis_type: AnalysisType = Field(..., description="分析類型")
    recommendation: str = Field(..., description="推薦結果")  # BUY, SELL, HOLD
    confidence: float = Field(..., description="信心度（0-1）")
    confidence_level: AnalysisConfidenceLevel = Field(..., description="信心度級別")
    
    # 詳細信息
    target_price: Optional[float] = Field(None, description="目標價格")
    reasoning: List[str] = Field(default_factory=list, description="分析理由")
    key_factors: List[str] = Field(default_factory=list, description="關鍵因素")
    risks: List[str] = Field(default_factory=list, description="風險因素")
    
    # 時間信息
    analysis_date: datetime = Field(..., description="分析日期")
    created_at: datetime = Field(..., description="創建時間")
    
    class Config:
        from_attributes = True


# ============================================================================
# 協調器配置模型
# ============================================================================

class AnalystCoordinatorConfiguration(BaseModel):
    """分析師協調器配置模型"""
    # 基本配置
    coordinator_enabled: bool = Field(True, description="是否啟用協調器")
    max_concurrent_analyses: int = Field(10, description="最大並發分析數")
    default_timeout: int = Field(300, description="默認超時時間（秒）")
    
    # 分析師配置
    auto_analyst_selection: bool = Field(True, description="是否自動選擇分析師")
    enable_analyst_debate: bool = Field(False, description="是否啟用分析師辯論")
    min_analysts_per_analysis: int = Field(2, description="每次分析的最少分析師數")
    max_analysts_per_analysis: int = Field(5, description="每次分析的最多分析師數")
    
    # 重試配置
    enable_retry: bool = Field(True, description="是否啟用重試")
    max_retry_count: int = Field(3, description="最大重試次數")
    retry_delay: int = Field(30, description="重試延遲（秒）")
    
    # 結果配置
    enable_result_aggregation: bool = Field(True, description="是否啟用結果聚合")
    confidence_threshold: float = Field(0.6, description="信心度閾值")
    enable_consensus_building: bool = Field(True, description="是否啟用共識建立")
    
    # 監控配置
    enable_performance_monitoring: bool = Field(True, description="是否啟用性能監控")
    health_check_interval: int = Field(60, description="健康檢查間隔（秒）")
    
    # 日誌配置
    log_level: str = Field("INFO", description="日誌級別")
    enable_detailed_logging: bool = Field(True, description="是否啟用詳細日誌")


# ============================================================================
# 統計和監控模型
# ============================================================================

class AnalystCoordinatorStatistics(BaseModel):
    """分析師協調器統計模型"""
    # 分析師統計
    total_analysts: int = Field(..., description="總分析師數")
    active_analysts: int = Field(..., description="活躍分析師數")
    busy_analysts: int = Field(..., description="忙碌分析師數")
    error_analysts: int = Field(..., description="錯誤分析師數")
    
    # 分析統計
    total_analyses: int = Field(..., description="總分析數")
    pending_analyses: int = Field(..., description="待執行分析數")
    running_analyses: int = Field(..., description="執行中分析數")
    completed_analyses: int = Field(..., description="已完成分析數")
    failed_analyses: int = Field(..., description="失敗分析數")
    
    # 性能統計
    average_analysis_time: float = Field(..., description="平均分析時間")
    success_rate: float = Field(..., description="成功率")
    average_confidence: float = Field(..., description="平均信心度")
    
    # 推薦統計
    buy_recommendations: int = Field(..., description="買入推薦數")
    sell_recommendations: int = Field(..., description="賣出推薦數")
    hold_recommendations: int = Field(..., description="持有推薦數")
    
    # 時間統計
    uptime: int = Field(..., description="運行時間（秒）")
    last_updated: datetime = Field(..., description="最後更新時間")


class AnalystCoordinatorHealth(BaseModel):
    """分析師協調器健康狀態模型"""
    overall_status: str = Field(..., description="整體狀態")
    coordinator_status: str = Field(..., description="協調器狀態")
    
    # 組件狀態
    analyst_registry_status: str = Field(..., description="分析師註冊表狀態")
    task_queue_status: str = Field(..., description="任務隊列狀態")
    result_aggregator_status: str = Field(..., description="結果聚合器狀態")
    
    # 分析師健康狀態
    healthy_analysts: int = Field(..., description="健康分析師數")
    unhealthy_analysts: int = Field(..., description="不健康分析師數")
    
    # 健康檢查結果
    health_checks: List[Dict[str, Any]] = Field(..., description="健康檢查結果")
    
    # 時間信息
    last_check: datetime = Field(..., description="最後檢查時間")
    uptime: int = Field(..., description="運行時間")


# ============================================================================
# 請求和響應模型
# ============================================================================

class AnalystQuery(BaseModel):
    """分析師查詢模型"""
    analyst_types: Optional[List[AnalystType]] = Field(None, description="分析師類型篩選")
    statuses: Optional[List[AnalystStatus]] = Field(None, description="狀態篩選")
    capabilities: Optional[List[str]] = Field(None, description="能力篩選")
    markets: Optional[List[str]] = Field(None, description="市場篩選")
    keyword: Optional[str] = Field(None, description="關鍵詞搜索")
    limit: int = Field(50, description="返回數量限制")


class AnalysisQuery(BaseModel):
    """分析查詢模型"""
    stock_ids: Optional[List[str]] = Field(None, description="股票代號篩選")
    analysis_types: Optional[List[AnalysisType]] = Field(None, description="分析類型篩選")
    statuses: Optional[List[AnalysisStatus]] = Field(None, description="狀態篩選")
    analyst_ids: Optional[List[str]] = Field(None, description="分析師ID篩選")
    user_ids: Optional[List[str]] = Field(None, description="用戶ID篩選")
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    limit: int = Field(100, description="返回數量限制")


class AnalystCoordinatorDashboard(BaseModel):
    """分析師協調器儀表板模型"""
    dashboard_id: str = Field(..., description="儀表板ID")
    title: str = Field(..., description="儀表板標題")
    last_updated: datetime = Field(..., description="最後更新時間")
    
    # 統計信息
    statistics: AnalystCoordinatorStatistics = Field(..., description="統計信息")
    
    # 健康狀態
    health: AnalystCoordinatorHealth = Field(..., description="健康狀態")
    
    # 實時數據
    active_analysts: List[AnalystInfo] = Field(..., description="活躍分析師")
    recent_analyses: List[AnalysisExecution] = Field(..., description="最近分析")
    top_performing_analysts: List[AnalystInfo] = Field(..., description="表現最佳分析師")
    
    # 圖表數據
    charts_data: Dict[str, List[Dict[str, Any]]] = Field(..., description="圖表數據")