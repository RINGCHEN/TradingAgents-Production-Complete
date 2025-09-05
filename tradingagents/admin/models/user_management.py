#!/usr/bin/env python3
"""
用戶管理 API 模型

提供用戶管理相關的 Pydantic 模型定義
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from ...models.user import UserStatus, MembershipTier, AuthProvider


# ============================================================================
# 基礎模型
# ============================================================================

class UserStatusInfo(BaseModel):
    """用戶狀態信息"""
    value: UserStatus
    label: str
    description: str
    color: Optional[str] = None


class MembershipTierInfo(BaseModel):
    """會員等級信息"""
    value: MembershipTier
    label: str
    description: str
    features: List[str] = []
    daily_quota: int
    monthly_quota: int


class AuthProviderInfo(BaseModel):
    """認證提供者信息"""
    value: AuthProvider
    label: str
    description: str
    icon: Optional[str] = None


# ============================================================================
# 用戶管理模型
# ============================================================================

class UserSearchRequest(BaseModel):
    """用戶搜索請求模型"""
    keyword: Optional[str] = Field(None, description="關鍵詞搜索")
    status: Optional[UserStatus] = Field(None, description="用戶狀態篩選")
    membership_tier: Optional[MembershipTier] = Field(None, description="會員等級篩選")
    auth_provider: Optional[AuthProvider] = Field(None, description="認證提供者篩選")
    country: Optional[str] = Field(None, description="國家篩選")
    email_verified: Optional[bool] = Field(None, description="郵箱驗證狀態篩選")
    is_premium: Optional[bool] = Field(None, description="是否付費會員篩選")
    
    # 時間範圍篩選
    created_after: Optional[datetime] = Field(None, description="註冊時間起始")
    created_before: Optional[datetime] = Field(None, description="註冊時間結束")
    last_login_after: Optional[datetime] = Field(None, description="最後登入時間起始")
    last_login_before: Optional[datetime] = Field(None, description="最後登入時間結束")
    
    # 排序
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向")
    
    # 分頁
    page: int = Field(1, ge=1, description="頁碼")
    page_size: int = Field(20, ge=1, le=100, description="每頁數量")


class UserResponse(BaseModel):
    """用戶響應模型"""
    id: int
    uuid: str
    email: str
    username: Optional[str] = None
    display_name: Optional[str] = None
    
    # 認證信息
    auth_provider: AuthProvider
    google_id: Optional[str] = None
    email_verified: bool
    
    # 會員信息
    membership_tier: MembershipTier
    status: UserStatus
    
    # 配額信息
    daily_api_quota: int
    monthly_api_quota: int
    api_calls_today: int
    api_calls_month: int
    api_quota_remaining_today: int
    api_quota_remaining_month: int
    
    # 個人資料
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: str
    language: str
    
    # 使用統計
    total_analyses: int
    last_login: Optional[datetime] = None
    login_count: int
    
    # 系統字段
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None
    
    # 計算字段
    is_premium: bool = Field(False, description="是否為付費會員")
    days_since_registration: int = Field(0, description="註冊天數")
    days_since_last_login: Optional[int] = Field(None, description="最後登入天數")
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用戶列表響應模型"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserCreateRequest(BaseModel):
    """創建用戶請求模型"""
    email: EmailStr = Field(..., description="用戶郵箱")
    username: Optional[str] = Field(None, description="用戶名")
    display_name: Optional[str] = Field(None, description="顯示名稱")
    password: Optional[str] = Field(None, description="密碼")
    
    # 會員信息
    membership_tier: MembershipTier = Field(MembershipTier.FREE, description="會員等級")
    status: UserStatus = Field(UserStatus.ACTIVE, description="用戶狀態")
    
    # 認證信息
    auth_provider: AuthProvider = Field(AuthProvider.EMAIL, description="認證提供者")
    email_verified: bool = Field(False, description="郵箱是否已驗證")
    
    # 配額設置
    daily_api_quota: Optional[int] = Field(None, description="每日API配額")
    monthly_api_quota: Optional[int] = Field(None, description="每月API配額")
    
    # 個人資料
    phone: Optional[str] = Field(None, description="電話號碼")
    country: Optional[str] = Field(None, description="國家代碼")
    timezone: str = Field("Asia/Taipei", description="時區")
    language: str = Field("zh-TW", description="語言")
    
    # 創建原因
    creation_reason: Optional[str] = Field(None, description="創建原因")


class UserUpdateRequest(BaseModel):
    """更新用戶請求模型"""
    username: Optional[str] = Field(None, description="用戶名")
    display_name: Optional[str] = Field(None, description="顯示名稱")
    
    # 會員信息
    membership_tier: Optional[MembershipTier] = Field(None, description="會員等級")
    status: Optional[UserStatus] = Field(None, description="用戶狀態")
    
    # 配額設置
    daily_api_quota: Optional[int] = Field(None, description="每日API配額")
    monthly_api_quota: Optional[int] = Field(None, description="每月API配額")
    
    # 個人資料
    phone: Optional[str] = Field(None, description="電話號碼")
    country: Optional[str] = Field(None, description="國家代碼")
    timezone: Optional[str] = Field(None, description="時區")
    language: Optional[str] = Field(None, description="語言")
    
    # 狀態控制
    email_verified: Optional[bool] = Field(None, description="郵箱驗證狀態")
    
    # 更新原因
    update_reason: Optional[str] = Field(None, description="更新原因")


class UserQuotaUpdateRequest(BaseModel):
    """用戶配額更新請求模型"""
    daily_api_quota: Optional[int] = Field(None, description="每日API配額")
    monthly_api_quota: Optional[int] = Field(None, description="每月API配額")
    reset_daily_usage: bool = Field(False, description="是否重置每日使用量")
    reset_monthly_usage: bool = Field(False, description="是否重置每月使用量")
    update_reason: Optional[str] = Field(None, description="更新原因")


class UserSubscriptionInfo(BaseModel):
    """用戶訂閱信息模型"""
    user_id: int
    has_active_subscription: bool
    current_subscription: Optional[Dict[str, Any]] = None
    subscription_history: List[Dict[str, Any]] = []
    total_subscriptions: int
    total_payments: int
    total_revenue: float


# ============================================================================
# 統計和分析模型
# ============================================================================

class UserStatistics(BaseModel):
    """用戶統計模型"""
    total_users: int = Field(..., description="總用戶數")
    active_users: int = Field(..., description="活躍用戶數")
    inactive_users: int = Field(..., description="非活躍用戶數")
    suspended_users: int = Field(..., description="暫停用戶數")
    deleted_users: int = Field(..., description="已刪除用戶數")
    
    # 會員等級分佈
    membership_distribution: Dict[str, int] = Field(..., description="會員等級分佈")
    
    # 認證提供者分佈
    auth_provider_distribution: Dict[str, int] = Field(..., description="認證提供者分佈")
    
    # 地理分佈
    country_distribution: Dict[str, int] = Field(..., description="國家分佈")
    
    # 時間統計
    new_users_today: int = Field(..., description="今日新用戶")
    new_users_week: int = Field(..., description="本週新用戶")
    new_users_month: int = Field(..., description="本月新用戶")
    
    # 活躍度統計
    users_logged_in_today: int = Field(..., description="今日登入用戶")
    users_logged_in_week: int = Field(..., description="本週登入用戶")
    users_logged_in_month: int = Field(..., description="本月登入用戶")
    
    # API 使用統計
    total_api_calls_today: int = Field(..., description="今日總API調用")
    total_api_calls_month: int = Field(..., description="本月總API調用")
    average_api_calls_per_user: float = Field(..., description="平均每用戶API調用")


class UserActivityLog(BaseModel):
    """用戶活動日誌模型"""
    id: int
    user_id: int
    activity_type: str
    activity_description: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    # 用戶信息
    user_email: Optional[str] = None
    user_display_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# 批量操作模型
# ============================================================================

class UserBulkAction(BaseModel):
    """用戶批量操作模型"""
    action: str = Field(..., description="操作類型")  # activate, suspend, delete, update_tier, reset_quota
    user_ids: List[int] = Field(..., description="用戶ID列表")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作參數")
    action_reason: Optional[str] = Field(None, description="操作原因")


class UserBulkActionResult(BaseModel):
    """用戶批量操作結果模型"""
    total_count: int = Field(..., description="總數量")
    success_count: int = Field(..., description="成功數量")
    failed_count: int = Field(..., description="失敗數量")
    skipped_count: int = Field(..., description="跳過數量")
    
    # 詳細結果
    success_items: List[int] = Field(..., description="成功的用戶ID")
    failed_items: List[Dict[str, Any]] = Field(..., description="失敗的用戶詳情")
    skipped_items: List[Dict[str, Any]] = Field(..., description="跳過的用戶詳情")
    
    # 操作信息
    action: str = Field(..., description="操作類型")
    executed_at: datetime = Field(..., description="執行時間")
    executed_by: Optional[str] = Field(None, description="執行者")


# ============================================================================
# 導出和報告模型
# ============================================================================

class UserExportRequest(BaseModel):
    """用戶數據導出請求模型"""
    format: str = Field("csv", description="導出格式")  # csv, excel, json
    filters: Optional[UserSearchRequest] = Field(None, description="篩選條件")
    fields: Optional[List[str]] = Field(None, description="導出字段")
    include_sensitive: bool = Field(False, description="是否包含敏感信息")


class UserExportResult(BaseModel):
    """用戶數據導出結果模型"""
    export_id: str = Field(..., description="導出任務ID")
    status: str = Field(..., description="導出狀態")
    file_url: Optional[str] = Field(None, description="文件下載URL")
    total_records: int = Field(..., description="總記錄數")
    created_at: datetime = Field(..., description="創建時間")
    expires_at: datetime = Field(..., description="過期時間")


# ============================================================================
# 系統信息模型
# ============================================================================

class UserManagementSystemInfo(BaseModel):
    """用戶管理系統信息模型"""
    total_users: int = Field(..., description="總用戶數")
    system_health: str = Field(..., description="系統健康狀態")
    last_backup_time: Optional[datetime] = Field(None, description="最後備份時間")
    
    # 配額統計
    total_daily_quota: int = Field(..., description="總每日配額")
    total_monthly_quota: int = Field(..., description="總每月配額")
    quota_utilization_rate: float = Field(..., description="配額使用率")
    
    # 統計信息
    statistics: UserStatistics = Field(..., description="用戶統計")
    
    # 系統狀態
    database_status: str = Field(..., description="數據庫狀態")
    cache_status: str = Field(..., description="緩存狀態")
    auth_system_status: str = Field(..., description="認證系統狀態")