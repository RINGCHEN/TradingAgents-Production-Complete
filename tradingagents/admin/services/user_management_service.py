#!/usr/bin/env python3
"""
用戶管理服務 (User Management Service)
天工 (TianGong) - 用戶管理業務邏輯

此模組提供用戶管理的核心業務邏輯，包含：
1. 用戶的 CRUD 操作
2. 用戶搜索和篩選
3. 用戶統計和分析
4. 批量操作和導出
5. 用戶訂閱信息管理
"""

import uuid
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..models.user_management import (
    UserSearchRequest, UserResponse, UserListResponse, UserCreateRequest,
    UserUpdateRequest, UserQuotaUpdateRequest, UserSubscriptionInfo,
    UserStatistics, UserActivityLog, UserBulkAction, UserBulkActionResult,
    UserExportRequest, UserExportResult, UserManagementSystemInfo
)
from ...models.user import User, UserStatus, MembershipTier, AuthProvider
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error
from ...utils.cache_manager import CacheManager

# 配置日誌
api_logger = get_api_logger(__name__)
security_logger = get_security_logger(__name__)


class UserManagementService:
    """用戶管理服務類"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_manager = CacheManager()
    
    # ==================== 用戶管理 ====================
    
    async def search_users(self, search: UserSearchRequest) -> UserListResponse:
        """搜索用戶"""
        try:
            query = self.db.query(User)
            
            # 關鍵詞搜索
            if search.keyword:
                keyword_filter = or_(
                    User.email.ilike(f"%{search.keyword}%"),
                    User.username.ilike(f"%{search.keyword}%"),
                    User.display_name.ilike(f"%{search.keyword}%")
                )
                query = query.filter(keyword_filter)
            
            # 狀態篩選
            if search.status:
                query = query.filter(User.status == search.status)
            
            # 會員等級篩選
            if search.membership_tier:
                query = query.filter(User.membership_tier == search.membership_tier)
            
            # 認證提供者篩選
            if search.auth_provider:
                query = query.filter(User.auth_provider == search.auth_provider)
            
            # 國家篩選
            if search.country:
                query = query.filter(User.country == search.country)
            
            # 郵箱驗證狀態篩選
            if search.email_verified is not None:
                query = query.filter(User.email_verified == search.email_verified)
            
            # 付費會員篩選
            if search.is_premium is not None:
                if search.is_premium:
                    query = query.filter(User.membership_tier.in_([MembershipTier.GOLD, MembershipTier.DIAMOND]))
                else:
                    query = query.filter(User.membership_tier == MembershipTier.FREE)
            
            # 時間範圍篩選
            if search.created_after:
                query = query.filter(User.created_at >= search.created_after)
            
            if search.created_before:
                query = query.filter(User.created_at <= search.created_before)
            
            if search.last_login_after:
                query = query.filter(User.last_login >= search.last_login_after)
            
            if search.last_login_before:
                query = query.filter(User.last_login <= search.last_login_before)
            
            # 總數統計
            total = query.count()
            
            # 排序
            if search.sort_by == "email":
                order_column = User.email
            elif search.sort_by == "username":
                order_column = User.username
            elif search.sort_by == "membership_tier":
                order_column = User.membership_tier
            elif search.sort_by == "status":
                order_column = User.status
            elif search.sort_by == "last_login":
                order_column = User.last_login
            elif search.sort_by == "updated_at":
                order_column = User.updated_at
            else:
                order_column = User.created_at
            
            if search.sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
            
            # 分頁
            offset = (search.page - 1) * search.page_size
            users = query.offset(offset).limit(search.page_size).all()
            
            # 轉換為響應模型
            user_responses = []
            for user in users:
                user_response = await self._convert_user_to_response(user)
                user_responses.append(user_response)
            
            total_pages = (total + search.page_size - 1) // search.page_size
            
            return UserListResponse(
                items=user_responses,
                total=total,
                page=search.page,
                page_size=search.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            api_logger.error("用戶搜索失敗", extra={'error': str(e)})
            raise
    
    async def get_user(self, user_id: int) -> Optional[UserResponse]:
        """獲取用戶詳情"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return None
            
            return await self._convert_user_to_response(user)
            
        except Exception as e:
            api_logger.error("獲取用戶失敗", extra={'user_id': user_id, 'error': str(e)})
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """根據郵箱獲取用戶"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                return None
            
            return await self._convert_user_to_response(user)
            
        except Exception as e:
            api_logger.error("根據郵箱獲取用戶失敗", extra={'email': email, 'error': str(e)})
            raise
    
    async def create_user(self, user_data: UserCreateRequest, admin_user_id: str) -> UserResponse:
        """創建用戶"""
        try:
            # 設置默認配額
            daily_quota = user_data.daily_api_quota or self._get_default_quota(user_data.membership_tier, 'daily')
            monthly_quota = user_data.monthly_api_quota or self._get_default_quota(user_data.membership_tier, 'monthly')
            
            # 創建用戶
            user = User(
                uuid=str(uuid.uuid4()),
                email=user_data.email,
                username=user_data.username,
                display_name=user_data.display_name,
                password_hash=self._hash_password(user_data.password) if user_data.password else None,
                auth_provider=user_data.auth_provider,
                email_verified=user_data.email_verified,
                membership_tier=user_data.membership_tier,
                status=user_data.status,
                daily_api_quota=daily_quota,
                monthly_api_quota=monthly_quota,
                phone=user_data.phone,
                country=user_data.country,
                timezone=user_data.timezone,
                language=user_data.language,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            # 記錄活動日誌
            await self._log_user_activity(
                user.id, "user_created", f"管理員創建用戶: {user_data.creation_reason or '無原因'}",
                admin_user_id
            )
            
            return await self._convert_user_to_response(user)
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("創建用戶失敗", extra={'email': user_data.email, 'error': str(e)})
            raise
    
    async def update_user(self, user_id: int, user_data: UserUpdateRequest, admin_user_id: str) -> UserResponse:
        """更新用戶"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用戶不存在")
            
            # 記錄變更
            changes = []
            
            # 更新字段
            if user_data.username is not None and user_data.username != user.username:
                changes.append(f"用戶名: {user.username} -> {user_data.username}")
                user.username = user_data.username
            
            if user_data.display_name is not None and user_data.display_name != user.display_name:
                changes.append(f"顯示名稱: {user.display_name} -> {user_data.display_name}")
                user.display_name = user_data.display_name
            
            if user_data.membership_tier is not None and user_data.membership_tier != user.membership_tier:
                changes.append(f"會員等級: {user.membership_tier} -> {user_data.membership_tier}")
                user.membership_tier = user_data.membership_tier
                
                # 更新配額
                if user_data.daily_api_quota is None:
                    user.daily_api_quota = self._get_default_quota(user_data.membership_tier, 'daily')
                if user_data.monthly_api_quota is None:
                    user.monthly_api_quota = self._get_default_quota(user_data.membership_tier, 'monthly')
            
            if user_data.status is not None and user_data.status != user.status:
                changes.append(f"狀態: {user.status} -> {user_data.status}")
                user.status = user_data.status
            
            if user_data.daily_api_quota is not None and user_data.daily_api_quota != user.daily_api_quota:
                changes.append(f"每日配額: {user.daily_api_quota} -> {user_data.daily_api_quota}")
                user.daily_api_quota = user_data.daily_api_quota
            
            if user_data.monthly_api_quota is not None and user_data.monthly_api_quota != user.monthly_api_quota:
                changes.append(f"每月配額: {user.monthly_api_quota} -> {user_data.monthly_api_quota}")
                user.monthly_api_quota = user_data.monthly_api_quota
            
            if user_data.phone is not None and user_data.phone != user.phone:
                changes.append(f"電話: {user.phone} -> {user_data.phone}")
                user.phone = user_data.phone
            
            if user_data.country is not None and user_data.country != user.country:
                changes.append(f"國家: {user.country} -> {user_data.country}")
                user.country = user_data.country
            
            if user_data.timezone is not None and user_data.timezone != user.timezone:
                changes.append(f"時區: {user.timezone} -> {user_data.timezone}")
                user.timezone = user_data.timezone
            
            if user_data.language is not None and user_data.language != user.language:
                changes.append(f"語言: {user.language} -> {user_data.language}")
                user.language = user_data.language
            
            if user_data.email_verified is not None and user_data.email_verified != user.email_verified:
                changes.append(f"郵箱驗證: {user.email_verified} -> {user_data.email_verified}")
                user.email_verified = user_data.email_verified
            
            user.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(user)
            
            # 記錄活動日誌
            if changes:
                change_description = f"管理員更新用戶: {'; '.join(changes)}. 原因: {user_data.update_reason or '無原因'}"
                await self._log_user_activity(
                    user_id, "user_updated", change_description, admin_user_id
                )
            
            return await self._convert_user_to_response(user)
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("更新用戶失敗", extra={'user_id': user_id, 'error': str(e)})
            raise
    
    async def delete_user(self, user_id: int, admin_user_id: str, soft_delete: bool = True, deletion_reason: Optional[str] = None):
        """刪除用戶"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用戶不存在")
            
            if soft_delete:
                # 軟刪除
                user.status = UserStatus.DELETED
                user.deleted_at = datetime.now()
                user.updated_at = datetime.now()
                
                # 記錄活動日誌
                await self._log_user_activity(
                    user_id, "user_soft_deleted", f"管理員軟刪除用戶: {deletion_reason or '無原因'}",
                    admin_user_id
                )
            else:
                # 硬刪除
                await self._log_user_activity(
                    user_id, "user_hard_deleted", f"管理員硬刪除用戶: {deletion_reason or '無原因'}",
                    admin_user_id
                )
                
                self.db.delete(user)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("刪除用戶失敗", extra={'user_id': user_id, 'error': str(e)})
            raise
    
    # ==================== 用戶配額管理 ====================
    
    async def update_user_quota(self, user_id: int, quota_data: UserQuotaUpdateRequest, admin_user_id: str) -> UserResponse:
        """更新用戶配額"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用戶不存在")
            
            changes = []
            
            # 更新配額
            if quota_data.daily_api_quota is not None:
                changes.append(f"每日配額: {user.daily_api_quota} -> {quota_data.daily_api_quota}")
                user.daily_api_quota = quota_data.daily_api_quota
            
            if quota_data.monthly_api_quota is not None:
                changes.append(f"每月配額: {user.monthly_api_quota} -> {quota_data.monthly_api_quota}")
                user.monthly_api_quota = quota_data.monthly_api_quota
            
            # 重置使用量
            if quota_data.reset_daily_usage:
                changes.append(f"重置每日使用量: {user.api_calls_today} -> 0")
                user.api_calls_today = 0
                user.last_api_reset = datetime.now()
            
            if quota_data.reset_monthly_usage:
                changes.append(f"重置每月使用量: {user.api_calls_month} -> 0")
                user.api_calls_month = 0
            
            user.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(user)
            
            # 記錄活動日誌
            if changes:
                change_description = f"管理員更新配額: {'; '.join(changes)}. 原因: {quota_data.update_reason or '無原因'}"
                await self._log_user_activity(
                    user_id, "quota_updated", change_description, admin_user_id
                )
            
            return await self._convert_user_to_response(user)
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("更新用戶配額失敗", extra={'user_id': user_id, 'error': str(e)})
            raise
    
    # ==================== 用戶訂閱信息 ====================
    
    async def get_user_subscription_info(self, user_id: int) -> Optional[UserSubscriptionInfo]:
        """獲取用戶訂閱信息"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # 這裡應該查詢實際的訂閱表，目前返回模擬數據
            return UserSubscriptionInfo(
                user_id=user_id,
                has_active_subscription=user.membership_tier != MembershipTier.FREE,
                current_subscription=None,  # 實際應查詢訂閱表
                subscription_history=[],    # 實際應查詢訂閱歷史
                total_subscriptions=0,      # 實際應統計
                total_payments=0,           # 實際應統計
                total_revenue=0.0           # 實際應統計
            )
            
        except Exception as e:
            api_logger.error("獲取用戶訂閱信息失敗", extra={'user_id': user_id, 'error': str(e)})
            raise
    
    # ==================== 用戶活動日誌 ====================
    
    async def get_user_activity_logs(self, user_id: int, limit: int = 50, offset: int = 0, activity_type: Optional[str] = None) -> List[UserActivityLog]:
        """獲取用戶活動日誌"""
        try:
            # 這裡應該查詢實際的活動日誌表，目前返回模擬數據
            return []
            
        except Exception as e:
            api_logger.error("獲取用戶活動日誌失敗", extra={'user_id': user_id, 'error': str(e)})
            raise
    
    # ==================== 統計和分析 ====================
    
    async def get_user_statistics(self) -> UserStatistics:
        """獲取用戶統計信息"""
        try:
            # 基本統計
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.status == UserStatus.ACTIVE).count()
            inactive_users = self.db.query(User).filter(User.status == UserStatus.INACTIVE).count()
            suspended_users = self.db.query(User).filter(User.status == UserStatus.SUSPENDED).count()
            deleted_users = self.db.query(User).filter(User.status == UserStatus.DELETED).count()
            
            # 會員等級分佈
            membership_stats = self.db.query(
                User.membership_tier, func.count(User.id)
            ).group_by(User.membership_tier).all()
            membership_distribution = {str(tier): count for tier, count in membership_stats}
            
            # 認證提供者分佈
            auth_stats = self.db.query(
                User.auth_provider, func.count(User.id)
            ).group_by(User.auth_provider).all()
            auth_provider_distribution = {str(provider): count for provider, count in auth_stats}
            
            # 國家分佈
            country_stats = self.db.query(
                User.country, func.count(User.id)
            ).filter(User.country.isnot(None)).group_by(User.country).all()
            country_distribution = {country: count for country, count in country_stats}
            
            # 時間統計
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            new_users_today = self.db.query(User).filter(
                func.date(User.created_at) == today
            ).count()
            
            new_users_week = self.db.query(User).filter(
                func.date(User.created_at) >= week_ago
            ).count()
            
            new_users_month = self.db.query(User).filter(
                func.date(User.created_at) >= month_ago
            ).count()
            
            # 活躍度統計
            users_logged_in_today = self.db.query(User).filter(
                func.date(User.last_login) == today
            ).count()
            
            users_logged_in_week = self.db.query(User).filter(
                func.date(User.last_login) >= week_ago
            ).count()
            
            users_logged_in_month = self.db.query(User).filter(
                func.date(User.last_login) >= month_ago
            ).count()
            
            # API 使用統計
            total_api_calls_today = self.db.query(func.sum(User.api_calls_today)).scalar() or 0
            total_api_calls_month = self.db.query(func.sum(User.api_calls_month)).scalar() or 0
            average_api_calls_per_user = total_api_calls_month / max(total_users, 1)
            
            return UserStatistics(
                total_users=total_users,
                active_users=active_users,
                inactive_users=inactive_users,
                suspended_users=suspended_users,
                deleted_users=deleted_users,
                membership_distribution=membership_distribution,
                auth_provider_distribution=auth_provider_distribution,
                country_distribution=country_distribution,
                new_users_today=new_users_today,
                new_users_week=new_users_week,
                new_users_month=new_users_month,
                users_logged_in_today=users_logged_in_today,
                users_logged_in_week=users_logged_in_week,
                users_logged_in_month=users_logged_in_month,
                total_api_calls_today=total_api_calls_today,
                total_api_calls_month=total_api_calls_month,
                average_api_calls_per_user=average_api_calls_per_user
            )
            
        except Exception as e:
            api_logger.error("獲取用戶統計失敗", extra={'error': str(e)})
            raise
    
    async def get_system_info(self) -> UserManagementSystemInfo:
        """獲取用戶管理系統信息"""
        try:
            # 獲取統計信息
            statistics = await self.get_user_statistics()
            
            # 配額統計
            total_daily_quota = self.db.query(func.sum(User.daily_api_quota)).scalar() or 0
            total_monthly_quota = self.db.query(func.sum(User.monthly_api_quota)).scalar() or 0
            
            # 配額使用率
            total_monthly_usage = self.db.query(func.sum(User.api_calls_month)).scalar() or 0
            quota_utilization_rate = total_monthly_usage / max(total_monthly_quota, 1)
            
            return UserManagementSystemInfo(
                total_users=statistics.total_users,
                system_health="healthy",
                last_backup_time=None,  # 實際應查詢備份記錄
                total_daily_quota=total_daily_quota,
                total_monthly_quota=total_monthly_quota,
                quota_utilization_rate=quota_utilization_rate,
                statistics=statistics,
                database_status="healthy",
                cache_status="healthy",
                auth_system_status="healthy"
            )
            
        except Exception as e:
            api_logger.error("獲取用戶管理系統信息失敗", extra={'error': str(e)})
            raise
    
    # ==================== 批量操作 ====================
    
    async def bulk_action_users(self, bulk_action: UserBulkAction, admin_user_id: str) -> UserBulkActionResult:
        """批量操作用戶"""
        try:
            total_count = len(bulk_action.user_ids)
            success_count = 0
            failed_count = 0
            skipped_count = 0
            
            success_items = []
            failed_items = []
            skipped_items = []
            
            for user_id in bulk_action.user_ids:
                try:
                    user = self.db.query(User).filter(User.id == user_id).first()
                    
                    if not user:
                        failed_items.append({
                            "id": user_id,
                            "error": "用戶不存在"
                        })
                        failed_count += 1
                        continue
                    
                    # 執行操作
                    if bulk_action.action == "activate":
                        if user.status == UserStatus.ACTIVE:
                            skipped_items.append({
                                "id": user_id,
                                "reason": "用戶已經是活躍狀態"
                            })
                            skipped_count += 1
                            continue
                        
                        user.status = UserStatus.ACTIVE
                        user.updated_at = datetime.now()
                        
                    elif bulk_action.action == "suspend":
                        if user.status == UserStatus.SUSPENDED:
                            skipped_items.append({
                                "id": user_id,
                                "reason": "用戶已經被暫停"
                            })
                            skipped_count += 1
                            continue
                        
                        user.status = UserStatus.SUSPENDED
                        user.updated_at = datetime.now()
                        
                    elif bulk_action.action == "delete":
                        if user.status == UserStatus.DELETED:
                            skipped_items.append({
                                "id": user_id,
                                "reason": "用戶已經被刪除"
                            })
                            skipped_count += 1
                            continue
                        
                        user.status = UserStatus.DELETED
                        user.deleted_at = datetime.now()
                        user.updated_at = datetime.now()
                        
                    elif bulk_action.action == "update_tier":
                        if bulk_action.parameters and 'membership_tier' in bulk_action.parameters:
                            new_tier = MembershipTier(bulk_action.parameters['membership_tier'])
                            if user.membership_tier == new_tier:
                                skipped_items.append({
                                    "id": user_id,
                                    "reason": f"用戶已經是 {new_tier} 等級"
                                })
                                skipped_count += 1
                                continue
                            
                            user.membership_tier = new_tier
                            # 更新配額
                            user.daily_api_quota = self._get_default_quota(new_tier, 'daily')
                            user.monthly_api_quota = self._get_default_quota(new_tier, 'monthly')
                            user.updated_at = datetime.now()
                        
                    elif bulk_action.action == "reset_quota":
                        user.api_calls_today = 0
                        user.api_calls_month = 0
                        user.last_api_reset = datetime.now()
                        user.updated_at = datetime.now()
                    
                    # 記錄活動日誌
                    await self._log_user_activity(
                        user_id, f"bulk_{bulk_action.action}", 
                        f"批量操作: {bulk_action.action}. 原因: {bulk_action.action_reason or '無原因'}",
                        admin_user_id
                    )
                    
                    success_items.append(user_id)
                    success_count += 1
                    
                except Exception as e:
                    failed_items.append({
                        "id": user_id,
                        "error": str(e)
                    })
                    failed_count += 1
            
            self.db.commit()
            
            return UserBulkActionResult(
                total_count=total_count,
                success_count=success_count,
                failed_count=failed_count,
                skipped_count=skipped_count,
                success_items=success_items,
                failed_items=failed_items,
                skipped_items=skipped_items,
                action=bulk_action.action,
                executed_at=datetime.now(),
                executed_by=admin_user_id
            )
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("批量操作用戶失敗", extra={'action': bulk_action.action, 'error': str(e)})
            raise
    
    # ==================== 數據導出 ====================
    
    async def create_export_task(self, export_request: UserExportRequest, admin_user_id: str) -> UserExportResult:
        """創建導出任務"""
        try:
            export_id = str(uuid.uuid4())
            
            # 這裡應該創建實際的導出任務記錄
            return UserExportResult(
                export_id=export_id,
                status="pending",
                file_url=None,
                total_records=0,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=7)
            )
            
        except Exception as e:
            api_logger.error("創建導出任務失敗", extra={'error': str(e)})
            raise
    
    async def execute_export_task(self, export_id: str, admin_user_id: str):
        """執行導出任務（後台任務）"""
        try:
            # 這裡應該實現實際的導出邏輯
            api_logger.info("導出任務執行", extra={'export_id': export_id, 'admin_user_id': admin_user_id})
            
        except Exception as e:
            api_logger.error("執行導出任務失敗", extra={'export_id': export_id, 'error': str(e)})
    
    # ==================== 輔助方法 ====================
    
    async def _convert_user_to_response(self, user: User) -> UserResponse:
        """將用戶模型轉換為響應模型"""
        try:
            # 計算字段
            is_premium = user.membership_tier in [MembershipTier.GOLD, MembershipTier.DIAMOND]
            days_since_registration = (datetime.now() - user.created_at).days
            days_since_last_login = None
            if user.last_login:
                days_since_last_login = (datetime.now() - user.last_login).days
            
            return UserResponse(
                id=user.id,
                uuid=user.uuid,
                email=user.email,
                username=user.username,
                display_name=user.display_name,
                auth_provider=user.auth_provider,
                google_id=user.google_id,
                email_verified=user.email_verified,
                membership_tier=user.membership_tier,
                status=user.status,
                daily_api_quota=user.daily_api_quota,
                monthly_api_quota=user.monthly_api_quota,
                api_calls_today=user.api_calls_today,
                api_calls_month=user.api_calls_month,
                api_quota_remaining_today=max(0, user.daily_api_quota - user.api_calls_today),
                api_quota_remaining_month=max(0, user.monthly_api_quota - user.api_calls_month),
                avatar_url=user.avatar_url,
                phone=user.phone,
                country=user.country,
                timezone=user.timezone,
                language=user.language,
                total_analyses=user.total_analyses,
                last_login=user.last_login,
                login_count=user.login_count,
                created_at=user.created_at,
                updated_at=user.updated_at,
                deleted_at=user.deleted_at,
                is_premium=is_premium,
                days_since_registration=days_since_registration,
                days_since_last_login=days_since_last_login
            )
            
        except Exception as e:
            api_logger.error("轉換用戶模型失敗", extra={'user_id': user.id, 'error': str(e)})
            raise
    
    def _get_default_quota(self, membership_tier: MembershipTier, quota_type: str) -> int:
        """獲取默認配額"""
        quota_map = {
            MembershipTier.FREE: {'daily': 100, 'monthly': 3000},
            MembershipTier.GOLD: {'daily': 500, 'monthly': 15000},
            MembershipTier.DIAMOND: {'daily': 2000, 'monthly': 60000}
        }
        
        return quota_map.get(membership_tier, quota_map[MembershipTier.FREE])[quota_type]
    
    def _hash_password(self, password: str) -> str:
        """密碼哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    async def _log_user_activity(self, user_id: int, activity_type: str, description: str, admin_user_id: str):
        """記錄用戶活動日誌"""
        try:
            # 這裡應該記錄到實際的活動日誌表
            api_logger.info("用戶活動記錄", extra={
                'user_id': user_id,
                'activity_type': activity_type,
                'description': description,
                'admin_user_id': admin_user_id
            })
            
        except Exception as e:
            api_logger.warning("記錄用戶活動失敗", extra={'error': str(e)})
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 檢查數據庫連接
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
            
            return {
                "database": True,
                "cache": True,  # 簡化檢查
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            api_logger.error("用戶管理服務健康檢查失敗", extra={'error': str(e)})
            return {
                "database": False,
                "cache": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }