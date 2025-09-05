"""
配置管理系統 API 模型

提供配置管理相關的 Pydantic 模型定義
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from ...database.config_models import (
    ConfigCategory, ConfigType, ConfigEnvironment, ConfigStatus,
    ChangeType, ApprovalStatus
)


# ============================================================================
# 基礎模型
# ============================================================================

class ConfigCategoryInfo(BaseModel):
    """配置分類信息"""
    value: ConfigCategory
    label: str
    description: str
    icon: Optional[str] = None


class ConfigTypeInfo(BaseModel):
    """配置類型信息"""
    value: ConfigType
    label: str
    description: str
    validation_rules: Dict[str, Any] = {}


class ConfigEnvironmentInfo(BaseModel):
    """配置環境信息"""
    value: ConfigEnvironment
    label: str
    description: str
    color: Optional[str] = None


# ============================================================================
# 配置項模型
# ============================================================================

class ConfigItemBase(BaseModel):
    """配置項基礎模型"""
    key: str = Field(..., description="配置鍵名", max_length=255)
    name: str = Field(..., description="配置名稱", max_length=255)
    description: Optional[str] = Field(None, description="配置描述")
    category: ConfigCategory = Field(..., description="配置分類")
    type: ConfigType = Field(..., description="配置類型")
    environment: ConfigEnvironment = Field(ConfigEnvironment.ALL, description="適用環境")
    
    value: Optional[str] = Field(None, description="配置值")
    default_value: Optional[str] = Field(None, description="預設值")
    
    # 驗證規則
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="驗證規則")
    allowed_values: Optional[List[str]] = Field(None, description="允許的值列表")
    min_value: Optional[str] = Field(None, description="最小值")
    max_value: Optional[str] = Field(None, description="最大值")
    regex_pattern: Optional[str] = Field(None, description="正則表達式驗證", max_length=500)
    
    # 狀態和權限
    status: ConfigStatus = Field(ConfigStatus.ACTIVE, description="配置狀態")
    is_sensitive: bool = Field(False, description="是否為敏感配置")
    is_readonly: bool = Field(False, description="是否只讀")
    requires_restart: bool = Field(False, description="是否需要重啟")
    requires_approval: bool = Field(False, description="是否需要審批")
    
    # 分組和排序
    group_name: Optional[str] = Field(None, description="配置組名", max_length=100)
    sort_order: int = Field(0, description="排序順序")
    
    # 依賴關係
    depends_on: Optional[List[str]] = Field(None, description="依賴的配置項")
    affects: Optional[List[str]] = Field(None, description="影響的配置項")
    
    # 元數據
    tags: Optional[List[str]] = Field(None, description="標籤")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")


class ConfigItemCreate(ConfigItemBase):
    """創建配置項模型"""
    pass


class ConfigItemUpdate(BaseModel):
    """更新配置項模型"""
    name: Optional[str] = Field(None, description="配置名稱", max_length=255)
    description: Optional[str] = Field(None, description="配置描述")
    value: Optional[str] = Field(None, description="配置值")
    status: Optional[ConfigStatus] = Field(None, description="配置狀態")
    group_name: Optional[str] = Field(None, description="配置組名", max_length=100)
    sort_order: Optional[int] = Field(None, description="排序順序")
    tags: Optional[List[str]] = Field(None, description="標籤")
    extra_metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")
    change_reason: Optional[str] = Field(None, description="變更原因")


class ConfigItemResponse(ConfigItemBase):
    """配置項響應模型"""
    id: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # 計算字段
    is_default: bool = Field(False, description="是否使用預設值")
    has_validation_errors: bool = Field(False, description="是否有驗證錯誤")
    last_validated_at: Optional[datetime] = Field(None, description="最後驗證時間")
    
    class Config:
        from_attributes = True


class ConfigItemListResponse(BaseModel):
    """配置項列表響應模型"""
    items: List[ConfigItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# 配置變更模型
# ============================================================================

class ConfigChangeHistoryResponse(BaseModel):
    """配置變更歷史響應模型"""
    id: int
    config_item_id: int
    change_type: ChangeType
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    change_reason: Optional[str] = None
    approval_status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_comment: Optional[str] = None
    is_applied: bool
    applied_at: Optional[datetime] = None
    version: Optional[str] = None
    environment_applied: Optional[str] = None
    created_at: datetime
    created_by: Optional[str] = None
    
    # 關聯數據
    config_key: Optional[str] = Field(None, description="配置鍵名")
    config_name: Optional[str] = Field(None, description="配置名稱")
    
    class Config:
        from_attributes = True


class ConfigChangeApproval(BaseModel):
    """配置變更審批模型"""
    approval_status: ApprovalStatus = Field(..., description="審批狀態")
    approval_comment: Optional[str] = Field(None, description="審批意見")


# ============================================================================
# 配置驗證模型
# ============================================================================

class ConfigValidationRequest(BaseModel):
    """配置驗證請求模型"""
    key: str = Field(..., description="配置鍵名")
    value: str = Field(..., description="配置值")
    type: ConfigType = Field(..., description="配置類型")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="驗證規則")


class ConfigValidationResult(BaseModel):
    """配置驗證結果模型"""
    is_valid: bool = Field(..., description="是否有效")
    error_message: Optional[str] = Field(None, description="錯誤信息")
    warning_message: Optional[str] = Field(None, description="警告信息")
    suggestions: Optional[List[str]] = Field(None, description="建議")
    validated_value: Optional[str] = Field(None, description="驗證後的值")


# ============================================================================
# 統計和查詢模型
# ============================================================================

class ConfigStatistics(BaseModel):
    """配置統計模型"""
    total_configs: int = Field(..., description="總配置數")
    active_configs: int = Field(..., description="活躍配置數")
    inactive_configs: int = Field(..., description="非活躍配置數")
    sensitive_configs: int = Field(..., description="敏感配置數")
    readonly_configs: int = Field(..., description="只讀配置數")
    
    # 按分類統計
    category_distribution: Dict[str, int] = Field(..., description="分類分佈")
    
    # 按環境統計
    environment_distribution: Dict[str, int] = Field(..., description="環境分佈")
    
    # 按類型統計
    type_distribution: Dict[str, int] = Field(..., description="類型分佈")
    
    # 最近變更
    recent_changes: int = Field(..., description="最近24小時變更數")
    pending_approvals: int = Field(..., description="待審批變更數")


class ConfigSearchRequest(BaseModel):
    """配置搜索請求模型"""
    keyword: Optional[str] = Field(None, description="關鍵詞")
    category: Optional[ConfigCategory] = Field(None, description="分類篩選")
    environment: Optional[ConfigEnvironment] = Field(None, description="環境篩選")
    status: Optional[ConfigStatus] = Field(None, description="狀態篩選")
    type: Optional[ConfigType] = Field(None, description="類型篩選")
    group_name: Optional[str] = Field(None, description="組名篩選")
    is_sensitive: Optional[bool] = Field(None, description="是否敏感")
    is_readonly: Optional[bool] = Field(None, description="是否只讀")
    tags: Optional[List[str]] = Field(None, description="標籤篩選")
    
    # 排序
    sort_by: str = Field("sort_order", description="排序字段")
    sort_order: str = Field("asc", description="排序方向")
    
    # 分頁
    page: int = Field(1, ge=1, description="頁碼")
    page_size: int = Field(20, ge=1, le=100, description="每頁數量")


class ConfigSystemInfo(BaseModel):
    """配置系統信息模型"""
    current_environment: str = Field(..., description="當前環境")
    total_configs: int = Field(..., description="總配置數")
    last_backup_time: Optional[datetime] = Field(None, description="最後備份時間")
    last_sync_time: Optional[datetime] = Field(None, description="最後同步時間")
    pending_changes: int = Field(..., description="待處理變更數")
    system_health: str = Field(..., description="系統健康狀態")
    
    # 環境信息
    available_environments: List[str] = Field(..., description="可用環境列表")
    environment_status: Dict[str, str] = Field(..., description="環境狀態")
    
    # 配置統計
    statistics: ConfigStatistics = Field(..., description="配置統計")


# ============================================================================
# 批量操作模型
# ============================================================================

class ConfigBulkAction(BaseModel):
    """配置批量操作模型"""
    action: str = Field(..., description="操作類型")  # activate, deactivate, delete, update_group, add_tags
    config_ids: List[int] = Field(..., description="配置ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作參數")
    change_reason: Optional[str] = Field(None, description="變更原因")


class ConfigBulkActionResult(BaseModel):
    """配置批量操作結果模型"""
    total_count: int = Field(..., description="總數量")
    success_count: int = Field(..., description="成功數量")
    failed_count: int = Field(..., description="失敗數量")
    skipped_count: int = Field(..., description="跳過數量")
    
    # 詳細結果
    success_items: List[int] = Field(..., description="成功的配置ID")
    failed_items: List[Dict[str, Any]] = Field(..., description="失敗的配置詳情")
    skipped_items: List[Dict[str, Any]] = Field(..., description="跳過的配置詳情")
    
    # 操作信息
    action: str = Field(..., description="操作類型")
    executed_at: datetime = Field(..., description="執行時間")
    executed_by: Optional[str] = Field(None, description="執行者")