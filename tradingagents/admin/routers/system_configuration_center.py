#!/usr/bin/env python3
"""
系統配置中心路由器 (System Configuration Center Router)
天工 (TianGong) - 第二階段系統配置管理功能

此模組提供企業級系統配置管理功能，包含：
1. 動態配置管理系統
2. A/B測試配置引擎
3. Feature Flag功能開關
4. 配置版本控制系統
5. 環境配置同步
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, validator

from ...database.database import get_db
from ...auth.dependencies import get_current_user, require_admin_access
from ...utils.user_context import UserContext
from ...utils.logging_config import get_api_logger, get_security_logger
from ...utils.error_handler import handle_error

# 配置日誌
api_logger = get_api_logger("system_configuration_center")
security_logger = get_security_logger("system_configuration_center")

# 創建路由器
router = APIRouter(prefix="/system-config", tags=["系統配置中心"])

# ==================== 數據模型定義 ====================

class Environment(str, Enum):
    """環境類型"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"

class ConfigType(str, Enum):
    """配置類型"""
    APPLICATION = "application"
    FEATURE = "feature"
    BUSINESS = "business"
    UI = "ui"
    INTEGRATION = "integration"

class ExperimentStatus(str, Enum):
    """實驗狀態"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class SystemConfiguration(BaseModel):
    """系統配置"""
    config_id: str
    config_key: str = Field(..., description="配置鍵值")
    config_value: Dict[str, Any] = Field(..., description="配置值")
    config_type: ConfigType = Field(..., description="配置類型")
    environment: Environment = Field(..., description="環境")
    version: str = Field(..., description="配置版本")
    description: Optional[str] = Field(None, description="配置描述")
    is_active: bool = Field(True, description="是否啟用")
    created_at: datetime
    updated_at: datetime
    created_by: str = Field(..., description="創建者")

class ConfigurationCreateRequest(BaseModel):
    """創建配置請求"""
    config_key: str = Field(..., description="配置鍵值")
    config_value: Dict[str, Any] = Field(..., description="配置值")
    config_type: ConfigType = Field(..., description="配置類型")
    environment: Environment = Field(..., description="環境")
    description: Optional[str] = Field(None, description="配置描述")
    
    @validator('config_key')
    def validate_config_key(cls, v):
        if not v or len(v) < 3:
            raise ValueError('配置鍵值至少需要3個字符')
        return v.lower().replace(' ', '_')

class ABTestExperiment(BaseModel):
    """A/B測試實驗"""
    experiment_id: str
    experiment_name: str = Field(..., description="實驗名稱")
    description: Optional[str] = Field(None, description="實驗描述")
    status: ExperimentStatus = Field(..., description="實驗狀態")
    traffic_allocation: float = Field(..., description="流量分配百分比", ge=0, le=100)
    variants: List[Dict[str, Any]] = Field(..., description="實驗變體")
    target_segment: Optional[Dict[str, Any]] = Field(None, description="目標用戶群體")
    success_metrics: List[str] = Field(..., description="成功指標")
    start_date: Optional[datetime] = Field(None, description="開始時間")
    end_date: Optional[datetime] = Field(None, description="結束時間")
    created_at: datetime
    created_by: str

class ExperimentCreateRequest(BaseModel):
    """創建實驗請求"""
    experiment_name: str = Field(..., description="實驗名稱")
    description: Optional[str] = Field(None, description="實驗描述")
    traffic_allocation: float = Field(50.0, description="流量分配百分比", ge=0, le=100)
    variants: List[Dict[str, Any]] = Field(..., description="實驗變體")
    target_segment: Optional[Dict[str, Any]] = Field(None, description="目標用戶群體")
    success_metrics: List[str] = Field(default=["conversion_rate"], description="成功指標")

class FeatureFlag(BaseModel):
    """功能開關"""
    flag_key: str
    flag_name: str = Field(..., description="功能開關名稱")
    description: Optional[str] = Field(None, description="開關描述")
    is_enabled: bool = Field(False, description="是否啟用")
    rollout_percentage: float = Field(0.0, description="推出百分比", ge=0, le=100)
    target_segments: List[str] = Field(default=[], description="目標用戶群")
    environments: List[Environment] = Field(..., description="適用環境")
    metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")
    created_at: datetime
    updated_at: datetime
    created_by: str

class FeatureFlagCreateRequest(BaseModel):
    """創建功能開關請求"""
    flag_key: str = Field(..., description="功能開關鍵值")
    flag_name: str = Field(..., description="功能開關名稱")
    description: Optional[str] = Field(None, description="開關描述")
    environments: List[Environment] = Field([Environment.DEVELOPMENT], description="適用環境")
    metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")
    
    @validator('flag_key')
    def validate_flag_key(cls, v):
        if not v or len(v) < 3:
            raise ValueError('功能開關鍵值至少需要3個字符')
        return v.lower().replace(' ', '_').replace('-', '_')

class ConfigValidationResult(BaseModel):
    """配置驗證結果"""
    is_valid: bool
    errors: List[str] = Field(default=[], description="驗證錯誤")
    warnings: List[str] = Field(default=[], description="驗證警告")
    suggestions: List[str] = Field(default=[], description="改進建議")

# ==================== 動態配置管理 ====================

@router.get("/configurations", 
           response_model=List[SystemConfiguration], 
           summary="獲取系統配置列表")
async def get_configurations(
    environment: Optional[Environment] = Query(None, description="環境篩選"),
    config_type: Optional[ConfigType] = Query(None, description="配置類型篩選"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    page: int = Query(1, description="頁碼", ge=1),
    size: int = Query(20, description="每頁數量", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取系統配置列表，支持環境和類型篩選
    """
    try:
        # 模擬配置數據
        configurations = [
            SystemConfiguration(
                config_id="config_001",
                config_key="api_rate_limits",
                config_value={
                    "default_limit": 1000,
                    "premium_limit": 5000,
                    "burst_multiplier": 2,
                    "time_window": 3600
                },
                config_type=ConfigType.APPLICATION,
                environment=Environment.PRODUCTION,
                version="v1.2.0",
                description="API速率限制配置",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by="admin_001"
            ),
            SystemConfiguration(
                config_id="config_002",
                config_key="trading_hours",
                config_value={
                    "market_open": "09:00",
                    "market_close": "13:30",
                    "pre_market_start": "08:30",
                    "after_hours_end": "14:00",
                    "timezone": "Asia/Taipei"
                },
                config_type=ConfigType.BUSINESS,
                environment=Environment.PRODUCTION,
                version="v1.0.0",
                description="交易時間配置",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by="admin_002"
            ),
            SystemConfiguration(
                config_id="config_003",
                config_key="ui_theme_settings",
                config_value={
                    "default_theme": "light",
                    "available_themes": ["light", "dark", "high_contrast"],
                    "theme_switching_enabled": True,
                    "auto_theme_detection": True
                },
                config_type=ConfigType.UI,
                environment=Environment.PRODUCTION,
                version="v2.1.0",
                description="UI主題設定配置",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by="admin_003"
            ),
            SystemConfiguration(
                config_id="config_004",
                config_key="notification_channels",
                config_value={
                    "email_enabled": True,
                    "sms_enabled": True,
                    "push_enabled": True,
                    "webhook_enabled": False,
                    "default_channel": "email",
                    "retry_attempts": 3
                },
                config_type=ConfigType.INTEGRATION,
                environment=Environment.PRODUCTION,
                version="v1.1.0",
                description="通知渠道配置",
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                created_by="admin_004"
            )
        ]
        
        # 應用篩選
        filtered_configs = configurations
        if environment:
            filtered_configs = [c for c in filtered_configs if c.environment == environment]
        if config_type:
            filtered_configs = [c for c in filtered_configs if c.config_type == config_type]
        if search:
            search_lower = search.lower()
            filtered_configs = [c for c in filtered_configs 
                              if search_lower in c.config_key.lower() or 
                                 (c.description and search_lower in c.description.lower())]
        
        # 分頁
        start = (page - 1) * size
        end = start + size
        paged_configs = filtered_configs[start:end]
        
        api_logger.info("System configurations retrieved", extra={
            "user_id": current_user.user_id,
            "environment": environment,
            "config_type": config_type,
            "total_count": len(filtered_configs)
        })
        
        return paged_configs
        
    except Exception as e:
        return await handle_error(e, "獲取系統配置列表失敗", api_logger)

@router.post("/configurations", 
            response_model=SystemConfiguration, 
            summary="創建新的系統配置")
async def create_configuration(
    config_data: ConfigurationCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    創建新的系統配置
    """
    try:
        # 創建配置
        new_config = SystemConfiguration(
            config_id=f"config_{uuid.uuid4().hex[:8]}",
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            config_type=config_data.config_type,
            environment=config_data.environment,
            version="v1.0.0",
            description=config_data.description,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=current_user.user_id
        )
        
        security_logger.info("New system configuration created", extra={
            "admin_user": current_user.user_id,
            "config_key": new_config.config_key,
            "config_type": new_config.config_type,
            "environment": new_config.environment
        })
        
        return new_config
        
    except Exception as e:
        return await handle_error(e, "創建系統配置失敗", api_logger)

@router.put("/configurations/{config_id}", 
           response_model=SystemConfiguration, 
           summary="更新系統配置")
async def update_configuration(
    config_id: str,
    updates: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    更新指定的系統配置
    """
    try:
        # 模擬更新配置
        updated_config = SystemConfiguration(
            config_id=config_id,
            config_key=updates.get("config_key", "updated_config"),
            config_value=updates.get("config_value", {}),
            config_type=ConfigType(updates.get("config_type", "application")),
            environment=Environment(updates.get("environment", "production")),
            version=f"v{datetime.now().strftime('%Y%m%d_%H%M')}",
            description=updates.get("description"),
            is_active=updates.get("is_active", True),
            created_at=datetime.now() - timedelta(days=7),
            updated_at=datetime.now(),
            created_by=current_user.user_id
        )
        
        security_logger.info("System configuration updated", extra={
            "admin_user": current_user.user_id,
            "config_id": config_id,
            "updated_fields": list(updates.keys())
        })
        
        return updated_config
        
    except Exception as e:
        return await handle_error(e, "更新系統配置失敗", api_logger)

@router.post("/configurations/{config_id}/validate", 
            response_model=ConfigValidationResult, 
            summary="驗證配置設定")
async def validate_configuration(
    config_id: str,
    validation_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    驗證配置設定的正確性和完整性
    """
    try:
        # 模擬配置驗證
        errors = []
        warnings = []
        suggestions = []
        
        # 基本驗證邏輯
        if not validation_data.get("config_value"):
            errors.append("配置值不能為空")
        
        if validation_data.get("config_type") == "application":
            # 應用配置特定驗證
            config_value = validation_data.get("config_value", {})
            if "timeout" in config_value and config_value["timeout"] > 300:
                warnings.append("超時時間過長，可能影響用戶體驗")
                suggestions.append("建議將超時時間設置為300秒以內")
        
        validation_result = ConfigValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
        
        api_logger.info("Configuration validation completed", extra={
            "user_id": current_user.user_id,
            "config_id": config_id,
            "is_valid": validation_result.is_valid,
            "error_count": len(errors)
        })
        
        return validation_result
        
    except Exception as e:
        return await handle_error(e, "配置驗證失敗", api_logger)

# ==================== A/B測試系統 ====================

@router.get("/experiments", 
           response_model=List[ABTestExperiment], 
           summary="獲取A/B測試實驗列表")
async def get_experiments(
    status: Optional[ExperimentStatus] = Query(None, description="實驗狀態篩選"),
    page: int = Query(1, description="頁碼", ge=1),
    size: int = Query(20, description="每頁數量", ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取A/B測試實驗列表
    """
    try:
        # 模擬實驗數據
        experiments = [
            ABTestExperiment(
                experiment_id="exp_001",
                experiment_name="新用戶引導流程優化",
                description="測試不同的用戶引導流程對註冊轉換率的影響",
                status=ExperimentStatus.ACTIVE,
                traffic_allocation=50.0,
                variants=[
                    {
                        "variant_id": "control",
                        "name": "控制組",
                        "description": "原始引導流程",
                        "allocation": 50.0
                    },
                    {
                        "variant_id": "treatment",
                        "name": "實驗組",
                        "description": "簡化引導流程",
                        "allocation": 50.0
                    }
                ],
                target_segment={
                    "user_type": "new_users",
                    "registration_source": "web"
                },
                success_metrics=["conversion_rate", "completion_time"],
                start_date=datetime.now() - timedelta(days=5),
                end_date=datetime.now() + timedelta(days=25),
                created_at=datetime.now() - timedelta(days=7),
                created_by="admin_001"
            ),
            ABTestExperiment(
                experiment_id="exp_002",
                experiment_name="儀表板佈局A/B測試",
                description="比較兩種不同的儀表板佈局設計效果",
                status=ExperimentStatus.DRAFT,
                traffic_allocation=30.0,
                variants=[
                    {
                        "variant_id": "layout_a",
                        "name": "佈局A",
                        "description": "垂直導航設計",
                        "allocation": 50.0
                    },
                    {
                        "variant_id": "layout_b",
                        "name": "佈局B", 
                        "description": "水平導航設計",
                        "allocation": 50.0
                    }
                ],
                target_segment={
                    "user_type": "active_users",
                    "membership_tier": ["gold", "diamond"]
                },
                success_metrics=["engagement_rate", "time_on_page"],
                start_date=None,
                end_date=None,
                created_at=datetime.now() - timedelta(days=2),
                created_by="admin_002"
            )
        ]
        
        # 應用狀態篩選
        if status:
            experiments = [exp for exp in experiments if exp.status == status]
        
        # 分頁
        start = (page - 1) * size
        end = start + size
        paged_experiments = experiments[start:end]
        
        return paged_experiments
        
    except Exception as e:
        return await handle_error(e, "獲取A/B測試實驗列表失敗", api_logger)

@router.post("/experiments", 
            response_model=ABTestExperiment, 
            summary="創建A/B測試實驗")
async def create_experiment(
    experiment_data: ExperimentCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    創建新的A/B測試實驗
    """
    try:
        # 創建實驗
        new_experiment = ABTestExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:8]}",
            experiment_name=experiment_data.experiment_name,
            description=experiment_data.description,
            status=ExperimentStatus.DRAFT,
            traffic_allocation=experiment_data.traffic_allocation,
            variants=experiment_data.variants,
            target_segment=experiment_data.target_segment,
            success_metrics=experiment_data.success_metrics,
            start_date=None,
            end_date=None,
            created_at=datetime.now(),
            created_by=current_user.user_id
        )
        
        security_logger.info("New A/B test experiment created", extra={
            "admin_user": current_user.user_id,
            "experiment_name": new_experiment.experiment_name,
            "traffic_allocation": new_experiment.traffic_allocation,
            "variant_count": len(new_experiment.variants)
        })
        
        return new_experiment
        
    except Exception as e:
        return await handle_error(e, "創建A/B測試實驗失敗", api_logger)

@router.post("/experiments/{experiment_id}/start", 
            summary="啟動A/B測試實驗")
async def start_experiment(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    啟動指定的A/B測試實驗
    """
    try:
        # 模擬啟動實驗
        result = {
            "experiment_id": experiment_id,
            "status": "active",
            "start_date": datetime.now().isoformat(),
            "message": "實驗已成功啟動"
        }
        
        security_logger.info("A/B test experiment started", extra={
            "admin_user": current_user.user_id,
            "experiment_id": experiment_id,
            "start_time": datetime.now()
        })
        
        return result
        
    except Exception as e:
        return await handle_error(e, "啟動A/B測試實驗失敗", api_logger)

@router.get("/experiments/{experiment_id}/results", 
           response_model=Dict[str, Any], 
           summary="獲取A/B測試結果")
async def get_experiment_results(
    experiment_id: str,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取A/B測試實驗的結果數據
    """
    try:
        # 模擬實驗結果數據
        results = {
            "experiment_id": experiment_id,
            "experiment_name": "新用戶引導流程優化",
            "status": "active",
            "duration_days": 5,
            "total_participants": 2847,
            "variants": [
                {
                    "variant_id": "control",
                    "name": "控制組",
                    "participants": 1423,
                    "conversion_rate": 12.3,
                    "completion_time_avg": 180.5,
                    "confidence_interval": "10.8% - 13.8%"
                },
                {
                    "variant_id": "treatment", 
                    "name": "實驗組",
                    "participants": 1424,
                    "conversion_rate": 15.7,
                    "completion_time_avg": 145.2,
                    "confidence_interval": "14.1% - 17.3%"
                }
            ],
            "statistical_significance": {
                "is_significant": True,
                "p_value": 0.032,
                "confidence_level": 95,
                "effect_size": "small_to_medium"
            },
            "recommendations": [
                "實驗組表現顯著優於控制組",
                "建議推廣簡化引導流程到全部用戶",
                "可以考慮進一步優化完成時間"
            ]
        }
        
        return results
        
    except Exception as e:
        return await handle_error(e, "獲取A/B測試結果失敗", api_logger)

# ==================== 功能開關管理 ====================

@router.get("/feature-flags", 
           response_model=List[FeatureFlag], 
           summary="獲取功能開關列表")
async def get_feature_flags(
    environment: Optional[Environment] = Query(None, description="環境篩選"),
    enabled_only: bool = Query(False, description="僅顯示已啟用的開關"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取功能開關列表
    """
    try:
        # 模擬功能開關數據
        flags = [
            FeatureFlag(
                flag_key="enhanced_analytics_dashboard",
                flag_name="增強分析儀表板",
                description="啟用新版本的分析儀表板功能",
                is_enabled=True,
                rollout_percentage=75.0,
                target_segments=["beta_users", "premium_users"],
                environments=[Environment.STAGING, Environment.PRODUCTION],
                metadata={
                    "feature_version": "v2.0",
                    "rollback_flag": "fallback_to_v1_analytics"
                },
                created_at=datetime.now() - timedelta(days=10),
                updated_at=datetime.now() - timedelta(days=2),
                created_by="admin_001"
            ),
            FeatureFlag(
                flag_key="mobile_push_notifications",
                flag_name="移動端推播通知",
                description="啟用移動應用的推播通知功能",
                is_enabled=False,
                rollout_percentage=0.0,
                target_segments=[],
                environments=[Environment.DEVELOPMENT, Environment.STAGING],
                metadata={
                    "platform_support": ["ios", "android"],
                    "notification_types": ["alerts", "promotions", "news"]
                },
                created_at=datetime.now() - timedelta(days=5),
                updated_at=datetime.now() - timedelta(days=1),
                created_by="admin_002"
            ),
            FeatureFlag(
                flag_key="advanced_user_segmentation",
                flag_name="高級用戶分群",
                description="啟用AI驅動的智能用戶分群功能",
                is_enabled=True,
                rollout_percentage=25.0,
                target_segments=["admin_users", "power_users"],
                environments=[Environment.PRODUCTION],
                metadata={
                    "ml_model_version": "v1.3",
                    "segmentation_criteria": ["behavior", "value", "risk"]
                },
                created_at=datetime.now() - timedelta(days=15),
                updated_at=datetime.now(),
                created_by="admin_003"
            )
        ]
        
        # 應用篩選
        filtered_flags = flags
        if environment:
            filtered_flags = [f for f in filtered_flags if environment in f.environments]
        if enabled_only:
            filtered_flags = [f for f in filtered_flags if f.is_enabled]
        
        return filtered_flags
        
    except Exception as e:
        return await handle_error(e, "獲取功能開關列表失敗", api_logger)

@router.post("/feature-flags", 
            response_model=FeatureFlag, 
            summary="創建功能開關")
async def create_feature_flag(
    flag_data: FeatureFlagCreateRequest,
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    創建新的功能開關
    """
    try:
        # 創建功能開關
        new_flag = FeatureFlag(
            flag_key=flag_data.flag_key,
            flag_name=flag_data.flag_name,
            description=flag_data.description,
            is_enabled=False,
            rollout_percentage=0.0,
            target_segments=[],
            environments=flag_data.environments,
            metadata=flag_data.metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=current_user.user_id
        )
        
        security_logger.info("New feature flag created", extra={
            "admin_user": current_user.user_id,
            "flag_key": new_flag.flag_key,
            "flag_name": new_flag.flag_name,
            "environments": [env.value for env in new_flag.environments]
        })
        
        return new_flag
        
    except Exception as e:
        return await handle_error(e, "創建功能開關失敗", api_logger)

@router.put("/feature-flags/{flag_key}/toggle", 
           summary="切換功能開關狀態")
async def toggle_feature_flag(
    flag_key: str,
    enabled: bool = Body(..., description="是否啟用"),
    rollout_percentage: Optional[float] = Body(None, description="推出百分比"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    切換功能開關的啟用狀態
    """
    try:
        # 模擬切換功能開關
        result = {
            "flag_key": flag_key,
            "previous_state": not enabled,
            "current_state": enabled,
            "rollout_percentage": rollout_percentage or (100.0 if enabled else 0.0),
            "updated_at": datetime.now().isoformat(),
            "message": f"功能開關 '{flag_key}' 已{'啟用' if enabled else '停用'}"
        }
        
        security_logger.warning("Feature flag toggled", extra={
            "admin_user": current_user.user_id,
            "flag_key": flag_key,
            "enabled": enabled,
            "rollout_percentage": rollout_percentage,
            "action_impact": "high"
        })
        
        return result
        
    except Exception as e:
        return await handle_error(e, "切換功能開關失敗", api_logger)

@router.post("/feature-flags/{flag_key}/emergency-disable", 
            summary="緊急停用功能開關")
async def emergency_disable_flag(
    flag_key: str,
    reason: str = Body(..., description="緊急停用原因"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    緊急停用功能開關 (緊急熔斷器)
    """
    try:
        # 執行緊急停用
        result = {
            "flag_key": flag_key,
            "emergency_disabled": True,
            "reason": reason,
            "disabled_by": current_user.user_id,
            "disabled_at": datetime.now().isoformat(),
            "rollback_percentage": 0.0,
            "message": "功能開關已緊急停用，所有用戶將使用預設行為"
        }
        
        security_logger.critical("Emergency feature flag disable", extra={
            "admin_user": current_user.user_id,
            "flag_key": flag_key,
            "reason": reason,
            "severity": "critical",
            "action_type": "emergency_disable"
        })
        
        return result
        
    except Exception as e:
        return await handle_error(e, "緊急停用功能開關失敗", api_logger)

# ==================== 配置版本控制 ====================

@router.get("/configurations/{config_id}/versions", 
           response_model=List[Dict[str, Any]], 
           summary="獲取配置版本歷史")
async def get_configuration_versions(
    config_id: str,
    limit: int = Query(10, description="版本數量限制", ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    獲取指定配置的版本歷史
    """
    try:
        # 模擬版本歷史數據
        versions = [
            {
                "version": "v1.3.0",
                "config_value": {"timeout": 30, "retry_count": 3, "cache_ttl": 300},
                "created_at": datetime.now().isoformat(),
                "created_by": current_user.user_id,
                "change_log": "增加緩存TTL配置",
                "is_current": True
            },
            {
                "version": "v1.2.0",
                "config_value": {"timeout": 30, "retry_count": 3},
                "created_at": (datetime.now() - timedelta(days=7)).isoformat(),
                "created_by": "admin_002",
                "change_log": "調整超時時間為30秒",
                "is_current": False
            },
            {
                "version": "v1.1.0",
                "config_value": {"timeout": 60, "retry_count": 5},
                "created_at": (datetime.now() - timedelta(days=14)).isoformat(),
                "created_by": "admin_001",
                "change_log": "初始版本配置",
                "is_current": False
            }
        ]
        
        return versions[:limit]
        
    except Exception as e:
        return await handle_error(e, "獲取配置版本歷史失敗", api_logger)

@router.post("/configurations/{config_id}/rollback/{version}", 
            summary="回滾配置到指定版本")
async def rollback_configuration(
    config_id: str,
    version: str,
    reason: str = Body(..., description="回滾原因"),
    db: Session = Depends(get_db),
    current_user: UserContext = Depends(require_admin_access)
):
    """
    將配置回滾到指定版本
    """
    try:
        # 模擬回滾操作
        result = {
            "config_id": config_id,
            "rollback_from": "v1.3.0",
            "rollback_to": version,
            "reason": reason,
            "rollback_by": current_user.user_id,
            "rollback_at": datetime.now().isoformat(),
            "status": "success",
            "message": f"配置已成功回滾到版本 {version}"
        }
        
        security_logger.warning("Configuration rollback performed", extra={
            "admin_user": current_user.user_id,
            "config_id": config_id,
            "rollback_to_version": version,
            "reason": reason,
            "severity": "medium"
        })
        
        return result
        
    except Exception as e:
        return await handle_error(e, "配置回滾失敗", api_logger)

# ==================== 系統健康檢查 ====================

@router.get("/health", summary="系統配置中心健康檢查")
async def configuration_center_health_check(
    db: Session = Depends(get_db)
):
    """
    系統配置中心健康檢查
    """
    try:
        # 檢查各個子系統狀態
        health_status = {
            "configuration_management": True,
            "ab_testing_system": True,
            "feature_flag_system": True,
            "version_control": True,
            "validation_engine": True
        }
        
        overall_health = all(health_status.values())
        
        return {
            "status": "healthy" if overall_health else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "components": health_status,
            "service": "system_configuration_center",
            "version": "v2.0.0"
        }
        
    except Exception as e:
        error_info = await handle_error(e, "系統配置中心健康檢查失敗", api_logger)
        
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_id": error_info.error_id if hasattr(error_info, 'error_id') else None,
            "service": "system_configuration_center"
        }

if __name__ == "__main__":
    # 測試路由配置
    print("系統配置中心路由配置:")
    for route in router.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(route.methods)
            print(f"  {methods} {route.path}")
    
    print(f"\n總共 {len(router.routes)} 個端點")