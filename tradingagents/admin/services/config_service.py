#!/usr/bin/env python3
"""
配置管理服務 (Configuration Management Service)
天工 (TianGong) - 配置管理業務邏輯

此模組提供配置管理的核心業務邏輯，包含：
1. 配置項的 CRUD 操作
2. 配置變更歷史管理
3. 配置驗證和審批流程
4. 配置統計和搜索功能
5. 批量操作和模板管理
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from ..models.config import (
    ConfigItemCreate, ConfigItemUpdate, ConfigItemResponse, ConfigItemListResponse,
    ConfigChangeHistoryResponse, ConfigChangeApproval, ConfigValidationRequest,
    ConfigValidationResult, ConfigStatistics, ConfigSearchRequest, ConfigSystemInfo,
    ConfigBulkAction, ConfigBulkActionResult
)
from ...database.config_models import (
    ConfigItem, ConfigChangeHistory, ConfigValidation, ConfigTemplate, ConfigBackup,
    ConfigCategory, ConfigType, ConfigEnvironment, ConfigStatus,
    ChangeType, ApprovalStatus
)
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error
from ...utils.cache_manager import CacheManager

# 配置日誌
api_logger = get_api_logger(__name__)
security_logger = get_security_logger(__name__)


class ConfigService:
    """配置管理服務類"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_manager = CacheManager()
    
    # ==================== 配置項管理 ====================
    
    async def search_config_items(self, search: ConfigSearchRequest) -> ConfigItemListResponse:
        """搜索配置項"""
        try:
            query = self.db.query(ConfigItem)
            
            # 關鍵詞搜索
            if search.keyword:
                keyword_filter = or_(
                    ConfigItem.key.ilike(f"%{search.keyword}%"),
                    ConfigItem.name.ilike(f"%{search.keyword}%"),
                    ConfigItem.description.ilike(f"%{search.keyword}%")
                )
                query = query.filter(keyword_filter)
            
            # 分類篩選
            if search.category:
                query = query.filter(ConfigItem.category == search.category)
            
            # 環境篩選
            if search.environment:
                query = query.filter(
                    or_(
                        ConfigItem.environment == search.environment,
                        ConfigItem.environment == ConfigEnvironment.ALL
                    )
                )
            
            # 狀態篩選
            if search.status:
                query = query.filter(ConfigItem.status == search.status)
            
            # 類型篩選
            if search.type:
                query = query.filter(ConfigItem.type == search.type)
            
            # 組名篩選
            if search.group_name:
                query = query.filter(ConfigItem.group_name == search.group_name)
            
            # 敏感配置篩選
            if search.is_sensitive is not None:
                query = query.filter(ConfigItem.is_sensitive == search.is_sensitive)
            
            # 只讀配置篩選
            if search.is_readonly is not None:
                query = query.filter(ConfigItem.is_readonly == search.is_readonly)
            
            # 標籤篩選
            if search.tags:
                for tag in search.tags:
                    query = query.filter(ConfigItem.tags.contains([tag]))
            
            # 總數統計
            total = query.count()
            
            # 排序
            if search.sort_by == "created_at":
                order_column = ConfigItem.created_at
            elif search.sort_by == "updated_at":
                order_column = ConfigItem.updated_at
            elif search.sort_by == "name":
                order_column = ConfigItem.name
            elif search.sort_by == "key":
                order_column = ConfigItem.key
            else:
                order_column = ConfigItem.sort_order
            
            if search.sort_order == "desc":
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(order_column)
            
            # 分頁
            offset = (search.page - 1) * search.page_size
            items = query.offset(offset).limit(search.page_size).all()
            
            # 轉換為響應模型
            config_items = []
            for item in items:
                config_response = ConfigItemResponse.from_orm(item)
                # 計算字段
                config_response.is_default = (item.value == item.default_value)
                config_response.has_validation_errors = await self._has_validation_errors(item.id)
                config_items.append(config_response)
            
            total_pages = (total + search.page_size - 1) // search.page_size
            
            return ConfigItemListResponse(
                items=config_items,
                total=total,
                page=search.page,
                page_size=search.page_size,
                total_pages=total_pages
            )
            
        except Exception as e:
            api_logger.error("配置項搜索失敗", extra={'error': str(e)})
            raise
    
    async def get_config_item(self, item_id: int) -> Optional[ConfigItemResponse]:
        """獲取配置項詳情"""
        try:
            item = self.db.query(ConfigItem).filter(ConfigItem.id == item_id).first()
            
            if not item:
                return None
            
            config_response = ConfigItemResponse.from_orm(item)
            # 計算字段
            config_response.is_default = (item.value == item.default_value)
            config_response.has_validation_errors = await self._has_validation_errors(item.id)
            
            # 獲取最後驗證時間
            last_validation = self.db.query(ConfigValidation).filter(
                ConfigValidation.config_item_id == item_id
            ).order_by(desc(ConfigValidation.validated_at)).first()
            
            if last_validation:
                config_response.last_validated_at = last_validation.validated_at
            
            return config_response
            
        except Exception as e:
            api_logger.error("獲取配置項失敗", extra={'item_id': item_id, 'error': str(e)})
            raise
    
    async def get_config_by_key(self, key: str, environment: ConfigEnvironment) -> Optional[ConfigItem]:
        """根據鍵名和環境獲取配置項"""
        try:
            return self.db.query(ConfigItem).filter(
                and_(
                    ConfigItem.key == key,
                    or_(
                        ConfigItem.environment == environment,
                        ConfigItem.environment == ConfigEnvironment.ALL
                    )
                )
            ).first()
            
        except Exception as e:
            api_logger.error("根據鍵名獲取配置項失敗", extra={'key': key, 'environment': environment, 'error': str(e)})
            raise
    
    async def create_config_item(self, config_data: ConfigItemCreate, user_id: str) -> ConfigItemResponse:
        """創建配置項"""
        try:
            # 驗證配置值
            if config_data.value:
                validation_result = await self._validate_config_value(
                    config_data.key, config_data.value, config_data.type, config_data.validation_rules
                )
                if not validation_result.is_valid:
                    raise ValueError(f"配置值驗證失敗: {validation_result.error_message}")
            
            # 創建配置項
            config_item = ConfigItem(
                key=config_data.key,
                name=config_data.name,
                description=config_data.description,
                category=config_data.category,
                type=config_data.type,
                environment=config_data.environment,
                value=config_data.value,
                default_value=config_data.default_value,
                validation_rules=config_data.validation_rules,
                allowed_values=config_data.allowed_values,
                min_value=config_data.min_value,
                max_value=config_data.max_value,
                regex_pattern=config_data.regex_pattern,
                status=config_data.status,
                is_sensitive=config_data.is_sensitive,
                is_readonly=config_data.is_readonly,
                requires_restart=config_data.requires_restart,
                requires_approval=config_data.requires_approval,
                group_name=config_data.group_name,
                sort_order=config_data.sort_order,
                depends_on=config_data.depends_on,
                affects=config_data.affects,
                tags=config_data.tags,
                extra_metadata=config_data.extra_metadata,
                created_by=user_id,
                updated_by=user_id
            )
            
            self.db.add(config_item)
            self.db.commit()
            self.db.refresh(config_item)
            
            # 記錄變更歷史
            await self._record_change_history(
                config_item.id, ChangeType.CREATE, None, config_data.value,
                "創建配置項", user_id
            )
            
            # 清除緩存
            await self._clear_config_cache(config_data.key, config_data.environment)
            
            return ConfigItemResponse.from_orm(config_item)
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("創建配置項失敗", extra={'config_key': config_data.key, 'error': str(e)})
            raise
    
    async def update_config_item(self, item_id: int, config_data: ConfigItemUpdate, user_id: str) -> ConfigItemResponse:
        """更新配置項"""
        try:
            config_item = self.db.query(ConfigItem).filter(ConfigItem.id == item_id).first()
            if not config_item:
                raise ValueError("配置項不存在")
            
            # 記錄舊值
            old_value = config_item.value
            
            # 更新字段
            update_fields = {}
            if config_data.name is not None:
                update_fields['name'] = config_data.name
                config_item.name = config_data.name
            
            if config_data.description is not None:
                update_fields['description'] = config_data.description
                config_item.description = config_data.description
            
            if config_data.value is not None:
                # 驗證新值
                validation_result = await self._validate_config_value(
                    config_item.key, config_data.value, config_item.type, config_item.validation_rules
                )
                if not validation_result.is_valid:
                    raise ValueError(f"配置值驗證失敗: {validation_result.error_message}")
                
                update_fields['value'] = config_data.value
                config_item.value = config_data.value
            
            if config_data.status is not None:
                update_fields['status'] = config_data.status
                config_item.status = config_data.status
            
            if config_data.group_name is not None:
                update_fields['group_name'] = config_data.group_name
                config_item.group_name = config_data.group_name
            
            if config_data.sort_order is not None:
                update_fields['sort_order'] = config_data.sort_order
                config_item.sort_order = config_data.sort_order
            
            if config_data.tags is not None:
                update_fields['tags'] = config_data.tags
                config_item.tags = config_data.tags
            
            if config_data.extra_metadata is not None:
                update_fields['extra_metadata'] = config_data.extra_metadata
                config_item.extra_metadata = config_data.extra_metadata
            
            config_item.updated_by = user_id
            config_item.updated_at = datetime.now()
            
            self.db.commit()
            self.db.refresh(config_item)
            
            # 記錄變更歷史
            if config_data.value is not None and old_value != config_data.value:
                await self._record_change_history(
                    item_id, ChangeType.UPDATE, old_value, config_data.value,
                    config_data.change_reason or "更新配置項", user_id
                )
            
            # 清除緩存
            await self._clear_config_cache(config_item.key, config_item.environment)
            
            return ConfigItemResponse.from_orm(config_item)
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("更新配置項失敗", extra={'item_id': item_id, 'error': str(e)})
            raise
    
    async def delete_config_item(self, item_id: int, user_id: str, change_reason: Optional[str] = None):
        """刪除配置項"""
        try:
            config_item = self.db.query(ConfigItem).filter(ConfigItem.id == item_id).first()
            if not config_item:
                raise ValueError("配置項不存在")
            
            # 記錄變更歷史
            await self._record_change_history(
                item_id, ChangeType.DELETE, config_item.value, None,
                change_reason or "刪除配置項", user_id
            )
            
            # 清除緩存
            await self._clear_config_cache(config_item.key, config_item.environment)
            
            # 刪除配置項
            self.db.delete(config_item)
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("刪除配置項失敗", extra={'item_id': item_id, 'error': str(e)})
            raise
    
    # ==================== 配置變更管理 ====================
    
    async def get_config_change_history(self, item_id: int, limit: int = 50, offset: int = 0) -> List[ConfigChangeHistoryResponse]:
        """獲取配置變更歷史"""
        try:
            history_query = self.db.query(ConfigChangeHistory).filter(
                ConfigChangeHistory.config_item_id == item_id
            ).order_by(desc(ConfigChangeHistory.created_at))
            
            history_items = history_query.offset(offset).limit(limit).all()
            
            result = []
            for item in history_items:
                history_response = ConfigChangeHistoryResponse.from_orm(item)
                # 添加配置項信息
                config_item = self.db.query(ConfigItem).filter(ConfigItem.id == item_id).first()
                if config_item:
                    history_response.config_key = config_item.key
                    history_response.config_name = config_item.name
                
                result.append(history_response)
            
            return result
            
        except Exception as e:
            api_logger.error("獲取配置變更歷史失敗", extra={'item_id': item_id, 'error': str(e)})
            raise
    
    async def approve_config_change(self, change_id: int, approval_data: ConfigChangeApproval, user_id: str) -> Dict[str, Any]:
        """審批配置變更"""
        try:
            change_record = self.db.query(ConfigChangeHistory).filter(
                ConfigChangeHistory.id == change_id
            ).first()
            
            if not change_record:
                raise ValueError("變更記錄不存在")
            
            if change_record.approval_status != ApprovalStatus.PENDING:
                raise ValueError("此變更已經被審批過")
            
            # 更新審批狀態
            change_record.approval_status = approval_data.approval_status
            change_record.approved_by = user_id
            change_record.approved_at = datetime.now()
            change_record.approval_comment = approval_data.approval_comment
            
            # 如果審批通過，應用變更
            if approval_data.approval_status == ApprovalStatus.APPROVED:
                config_item = self.db.query(ConfigItem).filter(
                    ConfigItem.id == change_record.config_item_id
                ).first()
                
                if config_item and change_record.new_value is not None:
                    config_item.value = change_record.new_value
                    config_item.updated_by = user_id
                    config_item.updated_at = datetime.now()
                    
                    # 標記變更已應用
                    change_record.is_applied = True
                    change_record.applied_at = datetime.now()
                    
                    # 清除緩存
                    await self._clear_config_cache(config_item.key, config_item.environment)
            
            self.db.commit()
            
            return {
                "message": "配置變更審批完成",
                "change_id": change_id,
                "approval_status": approval_data.approval_status,
                "is_applied": change_record.is_applied
            }
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("配置變更審批失敗", extra={'change_id': change_id, 'error': str(e)})
            raise
    
    # ==================== 配置驗證 ====================
    
    async def validate_config_value(self, validation_request: ConfigValidationRequest) -> ConfigValidationResult:
        """驗證配置值"""
        try:
            return await self._validate_config_value(
                validation_request.key,
                validation_request.value,
                validation_request.type,
                validation_request.validation_rules
            )
            
        except Exception as e:
            api_logger.error("配置值驗證失敗", extra={'config_key': validation_request.key, 'error': str(e)})
            raise
    
    async def _validate_config_value(self, key: str, value: str, config_type: ConfigType, validation_rules: Optional[Dict[str, Any]] = None) -> ConfigValidationResult:
        """內部配置值驗證方法"""
        try:
            errors = []
            warnings = []
            suggestions = []
            validated_value = value
            
            # 基本類型驗證
            if config_type == ConfigType.INTEGER:
                try:
                    validated_value = str(int(value))
                except ValueError:
                    errors.append("值必須是整數")
            
            elif config_type == ConfigType.FLOAT:
                try:
                    validated_value = str(float(value))
                except ValueError:
                    errors.append("值必須是數字")
            
            elif config_type == ConfigType.BOOLEAN:
                if value.lower() not in ['true', 'false', '1', '0', 'yes', 'no']:
                    errors.append("值必須是布爾值 (true/false, 1/0, yes/no)")
                else:
                    validated_value = str(value.lower() in ['true', '1', 'yes'])
            
            elif config_type == ConfigType.JSON:
                try:
                    json.loads(value)
                except json.JSONDecodeError as e:
                    errors.append(f"無效的 JSON 格式: {str(e)}")
            
            elif config_type == ConfigType.URL:
                url_pattern = re.compile(
                    r'^https?://'  # http:// or https://
                    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                    r'localhost|'  # localhost...
                    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                    r'(?::\d+)?'  # optional port
                    r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                if not url_pattern.match(value):
                    errors.append("無效的 URL 格式")
            
            elif config_type == ConfigType.EMAIL:
                email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                if not email_pattern.match(value):
                    errors.append("無效的郵箱格式")
            
            # 驗證規則檢查
            if validation_rules:
                # 長度檢查
                if 'min_length' in validation_rules:
                    if len(value) < validation_rules['min_length']:
                        errors.append(f"值長度不能少於 {validation_rules['min_length']} 個字符")
                
                if 'max_length' in validation_rules:
                    if len(value) > validation_rules['max_length']:
                        errors.append(f"值長度不能超過 {validation_rules['max_length']} 個字符")
                
                # 數值範圍檢查
                if config_type in [ConfigType.INTEGER, ConfigType.FLOAT]:
                    try:
                        num_value = float(value)
                        if 'min_value' in validation_rules:
                            if num_value < validation_rules['min_value']:
                                errors.append(f"值不能小於 {validation_rules['min_value']}")
                        
                        if 'max_value' in validation_rules:
                            if num_value > validation_rules['max_value']:
                                errors.append(f"值不能大於 {validation_rules['max_value']}")
                    except ValueError:
                        pass  # 類型錯誤已在上面檢查
                
                # 正則表達式檢查
                if 'regex' in validation_rules:
                    try:
                        pattern = re.compile(validation_rules['regex'])
                        if not pattern.match(value):
                            errors.append("值不符合指定的格式要求")
                    except re.error:
                        warnings.append("驗證規則中的正則表達式無效")
                
                # 允許值列表檢查
                if 'allowed_values' in validation_rules:
                    if value not in validation_rules['allowed_values']:
                        errors.append(f"值必須是以下之一: {', '.join(validation_rules['allowed_values'])}")
            
            # 生成建議
            if config_type == ConfigType.PASSWORD and len(value) < 12:
                suggestions.append("建議使用至少12個字符的密碼以提高安全性")
            
            if config_type == ConfigType.URL and not value.startswith('https://'):
                suggestions.append("建議使用 HTTPS 協議以提高安全性")
            
            is_valid = len(errors) == 0
            error_message = "; ".join(errors) if errors else None
            warning_message = "; ".join(warnings) if warnings else None
            
            return ConfigValidationResult(
                is_valid=is_valid,
                error_message=error_message,
                warning_message=warning_message,
                suggestions=suggestions,
                validated_value=validated_value if is_valid else None
            )
            
        except Exception as e:
            return ConfigValidationResult(
                is_valid=False,
                error_message=f"驗證過程中發生錯誤: {str(e)}",
                warning_message=None,
                suggestions=[],
                validated_value=None
            )
    
    # ==================== 統計和系統信息 ====================
    
    async def get_config_statistics(self) -> ConfigStatistics:
        """獲取配置統計信息"""
        try:
            # 基本統計
            total_configs = self.db.query(ConfigItem).count()
            active_configs = self.db.query(ConfigItem).filter(ConfigItem.status == ConfigStatus.ACTIVE).count()
            inactive_configs = self.db.query(ConfigItem).filter(ConfigItem.status == ConfigStatus.INACTIVE).count()
            sensitive_configs = self.db.query(ConfigItem).filter(ConfigItem.is_sensitive == True).count()
            readonly_configs = self.db.query(ConfigItem).filter(ConfigItem.is_readonly == True).count()
            
            # 按分類統計
            category_stats = self.db.query(
                ConfigItem.category, func.count(ConfigItem.id)
            ).group_by(ConfigItem.category).all()
            category_distribution = {str(cat): count for cat, count in category_stats}
            
            # 按環境統計
            env_stats = self.db.query(
                ConfigItem.environment, func.count(ConfigItem.id)
            ).group_by(ConfigItem.environment).all()
            environment_distribution = {str(env): count for env, count in env_stats}
            
            # 按類型統計
            type_stats = self.db.query(
                ConfigItem.type, func.count(ConfigItem.id)
            ).group_by(ConfigItem.type).all()
            type_distribution = {str(typ): count for typ, count in type_stats}
            
            # 最近變更統計
            yesterday = datetime.now() - timedelta(days=1)
            recent_changes = self.db.query(ConfigChangeHistory).filter(
                ConfigChangeHistory.created_at >= yesterday
            ).count()
            
            pending_approvals = self.db.query(ConfigChangeHistory).filter(
                ConfigChangeHistory.approval_status == ApprovalStatus.PENDING
            ).count()
            
            return ConfigStatistics(
                total_configs=total_configs,
                active_configs=active_configs,
                inactive_configs=inactive_configs,
                sensitive_configs=sensitive_configs,
                readonly_configs=readonly_configs,
                category_distribution=category_distribution,
                environment_distribution=environment_distribution,
                type_distribution=type_distribution,
                recent_changes=recent_changes,
                pending_approvals=pending_approvals
            )
            
        except Exception as e:
            api_logger.error("獲取配置統計失敗", extra={'error': str(e)})
            raise
    
    async def get_system_info(self) -> ConfigSystemInfo:
        """獲取配置系統信息"""
        try:
            # 獲取統計信息
            statistics = await self.get_config_statistics()
            
            # 系統信息
            current_environment = "development"  # 從環境變量獲取
            total_configs = statistics.total_configs
            
            # 最後備份時間（模擬）
            last_backup = self.db.query(ConfigBackup).order_by(
                desc(ConfigBackup.created_at)
            ).first()
            last_backup_time = last_backup.created_at if last_backup else None
            
            # 待處理變更
            pending_changes = self.db.query(ConfigChangeHistory).filter(
                ConfigChangeHistory.approval_status == ApprovalStatus.PENDING
            ).count()
            
            # 可用環境
            available_environments = [env.value for env in ConfigEnvironment]
            
            # 環境狀態（模擬）
            environment_status = {
                "development": "healthy",
                "testing": "healthy",
                "staging": "healthy",
                "production": "healthy"
            }
            
            return ConfigSystemInfo(
                current_environment=current_environment,
                total_configs=total_configs,
                last_backup_time=last_backup_time,
                last_sync_time=None,  # 模擬
                pending_changes=pending_changes,
                system_health="healthy",
                available_environments=available_environments,
                environment_status=environment_status,
                statistics=statistics
            )
            
        except Exception as e:
            api_logger.error("獲取配置系統信息失敗", extra={'error': str(e)})
            raise
    
    # ==================== 批量操作 ====================
    
    async def bulk_action_config_items(self, bulk_action: ConfigBulkAction, user_id: str) -> ConfigBulkActionResult:
        """批量操作配置項"""
        try:
            total_count = len(bulk_action.config_ids)
            success_count = 0
            failed_count = 0
            skipped_count = 0
            
            success_items = []
            failed_items = []
            skipped_items = []
            
            for config_id in bulk_action.config_ids:
                try:
                    config_item = self.db.query(ConfigItem).filter(ConfigItem.id == config_id).first()
                    
                    if not config_item:
                        failed_items.append({
                            "id": config_id,
                            "error": "配置項不存在"
                        })
                        failed_count += 1
                        continue
                    
                    # 檢查只讀配置
                    if config_item.is_readonly and bulk_action.action in ['update', 'delete']:
                        skipped_items.append({
                            "id": config_id,
                            "reason": "配置項為只讀"
                        })
                        skipped_count += 1
                        continue
                    
                    # 執行操作
                    if bulk_action.action == "activate":
                        config_item.status = ConfigStatus.ACTIVE
                        config_item.updated_by = user_id
                        config_item.updated_at = datetime.now()
                        
                    elif bulk_action.action == "deactivate":
                        config_item.status = ConfigStatus.INACTIVE
                        config_item.updated_by = user_id
                        config_item.updated_at = datetime.now()
                        
                    elif bulk_action.action == "delete":
                        # 記錄變更歷史
                        await self._record_change_history(
                            config_id, ChangeType.DELETE, config_item.value, None,
                            bulk_action.change_reason or "批量刪除", user_id
                        )
                        self.db.delete(config_item)
                        
                    elif bulk_action.action == "update_group":
                        if bulk_action.parameters and 'group_name' in bulk_action.parameters:
                            config_item.group_name = bulk_action.parameters['group_name']
                            config_item.updated_by = user_id
                            config_item.updated_at = datetime.now()
                        
                    elif bulk_action.action == "add_tags":
                        if bulk_action.parameters and 'tags' in bulk_action.parameters:
                            existing_tags = config_item.tags or []
                            new_tags = bulk_action.parameters['tags']
                            config_item.tags = list(set(existing_tags + new_tags))
                            config_item.updated_by = user_id
                            config_item.updated_at = datetime.now()
                    
                    success_items.append(config_id)
                    success_count += 1
                    
                except Exception as e:
                    failed_items.append({
                        "id": config_id,
                        "error": str(e)
                    })
                    failed_count += 1
            
            self.db.commit()
            
            return ConfigBulkActionResult(
                total_count=total_count,
                success_count=success_count,
                failed_count=failed_count,
                skipped_count=skipped_count,
                success_items=success_items,
                failed_items=failed_items,
                skipped_items=skipped_items,
                action=bulk_action.action,
                executed_at=datetime.now(),
                executed_by=user_id
            )
            
        except Exception as e:
            self.db.rollback()
            api_logger.error("批量操作配置項失敗", extra={'action': bulk_action.action, 'error': str(e)})
            raise
    
    # ==================== 輔助方法 ====================
    
    async def _record_change_history(self, config_item_id: int, change_type: ChangeType, 
                                   old_value: Optional[str], new_value: Optional[str],
                                   change_reason: str, user_id: str):
        """記錄配置變更歷史"""
        try:
            change_record = ConfigChangeHistory(
                config_item_id=config_item_id,
                change_type=change_type,
                old_value=old_value,
                new_value=new_value,
                change_reason=change_reason,
                approval_status=ApprovalStatus.AUTO_APPROVED,  # 自動審批
                is_applied=True,
                applied_at=datetime.now(),
                created_by=user_id
            )
            
            self.db.add(change_record)
            
        except Exception as e:
            api_logger.error("記錄配置變更歷史失敗", extra={'config_item_id': config_item_id, 'error': str(e)})
            raise
    
    async def _has_validation_errors(self, config_item_id: int) -> bool:
        """檢查配置項是否有驗證錯誤"""
        try:
            last_validation = self.db.query(ConfigValidation).filter(
                ConfigValidation.config_item_id == config_item_id
            ).order_by(desc(ConfigValidation.validated_at)).first()
            
            return last_validation and not last_validation.is_valid
            
        except Exception as e:
            api_logger.error("檢查驗證錯誤失敗", extra={'config_item_id': config_item_id, 'error': str(e)})
            return False
    
    async def _clear_config_cache(self, key: str, environment: ConfigEnvironment):
        """清除配置緩存"""
        try:
            cache_key = f"config:{key}:{environment}"
            await self.cache_manager.delete(cache_key)
            
        except Exception as e:
            api_logger.warning("清除配置緩存失敗", extra={'key': key, 'environment': environment, 'error': str(e)})
    
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
            api_logger.error("配置服務健康檢查失敗", extra={'error': str(e)})
            return {
                "database": False,
                "cache": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }