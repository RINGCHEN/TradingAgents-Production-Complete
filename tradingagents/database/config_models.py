"""
配置管理系統數據庫模型

提供統一的配置管理、版本控制和環境管理功能
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Enum as SQLEnum, Index, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any

from .database import Base


class ConfigCategory(str, Enum):
    """配置分類"""
    SYSTEM = "system"           # 系統配置
    DATABASE = "database"       # 數據庫配置
    CACHE = "cache"            # 緩存配置
    SECURITY = "security"       # 安全配置
    API = "api"                # API配置
    NOTIFICATION = "notification"  # 通知配置
    EXTERNAL = "external"       # 外部服務配置
    FEATURE = "feature"         # 功能開關
    UI = "ui"                  # 界面配置
    MONITORING = "monitoring"   # 監控配置


class ConfigType(str, Enum):
    """配置類型"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    LIST = "list"
    PASSWORD = "password"
    URL = "url"
    EMAIL = "email"
    FILE_PATH = "file_path"


class ConfigEnvironment(str, Enum):
    """配置環境"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    ALL = "all"  # 適用於所有環境


class ConfigStatus(str, Enum):
    """配置狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    PENDING = "pending"


class ChangeType(str, Enum):
    """變更類型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESTORE = "restore"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"


class ApprovalStatus(str, Enum):
    """審批狀態"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


class ConfigItem(Base):
    """配置項目表"""
    __tablename__ = "config_items"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, index=True, comment="配置鍵名")
    name = Column(String(255), nullable=False, comment="配置名稱")
    description = Column(Text, comment="配置描述")
    category = Column(SQLEnum(ConfigCategory), nullable=False, index=True, comment="配置分類")
    type = Column(SQLEnum(ConfigType), nullable=False, comment="配置類型")
    environment = Column(SQLEnum(ConfigEnvironment), nullable=False, default=ConfigEnvironment.ALL, index=True, comment="適用環境")
    
    # 配置值
    value = Column(Text, comment="配置值")
    default_value = Column(Text, comment="預設值")
    
    # 驗證規則
    validation_rules = Column(JSON, comment="驗證規則 JSON")
    allowed_values = Column(JSON, comment="允許的值列表")
    min_value = Column(String(50), comment="最小值")
    max_value = Column(String(50), comment="最大值")
    regex_pattern = Column(String(500), comment="正則表達式驗證")
    
    # 狀態和權限
    status = Column(SQLEnum(ConfigStatus), nullable=False, default=ConfigStatus.ACTIVE, index=True, comment="配置狀態")
    is_sensitive = Column(Boolean, default=False, comment="是否為敏感配置")
    is_readonly = Column(Boolean, default=False, comment="是否只讀")
    requires_restart = Column(Boolean, default=False, comment="是否需要重啟")
    requires_approval = Column(Boolean, default=False, comment="是否需要審批")
    
    # 分組和排序
    group_name = Column(String(100), comment="配置組名")
    sort_order = Column(Integer, default=0, comment="排序順序")
    
    # 依賴關係
    depends_on = Column(JSON, comment="依賴的配置項")
    affects = Column(JSON, comment="影響的配置項")
    
    # 元數據
    tags = Column(JSON, comment="標籤")
    extra_metadata = Column(JSON, comment="額外元數據")
    
    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="創建時間")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新時間")
    created_by = Column(String(100), comment="創建者")
    updated_by = Column(String(100), comment="更新者")
    
    # 關聯
    change_history = relationship("ConfigChangeHistory", back_populates="config_item", cascade="all, delete-orphan")
    validations = relationship("ConfigValidation", back_populates="config_item", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_config_key_env', 'key', 'environment'),
        Index('idx_config_category_status', 'category', 'status'),
        Index('idx_config_group_sort', 'group_name', 'sort_order'),
    )


class ConfigChangeHistory(Base):
    """配置變更歷史表"""
    __tablename__ = "config_change_history"
    
    id = Column(Integer, primary_key=True, index=True)
    config_item_id = Column(Integer, ForeignKey("config_items.id"), nullable=False, index=True, comment="配置項ID")
    
    # 變更信息
    change_type = Column(SQLEnum(ChangeType), nullable=False, comment="變更類型")
    old_value = Column(Text, comment="舊值")
    new_value = Column(Text, comment="新值")
    change_reason = Column(Text, comment="變更原因")
    
    # 審批信息
    approval_status = Column(SQLEnum(ApprovalStatus), default=ApprovalStatus.PENDING, comment="審批狀態")
    approved_by = Column(String(100), comment="審批人")
    approved_at = Column(DateTime(timezone=True), comment="審批時間")
    approval_comment = Column(Text, comment="審批意見")
    
    # 應用信息
    is_applied = Column(Boolean, default=False, comment="是否已應用")
    applied_at = Column(DateTime(timezone=True), comment="應用時間")
    rollback_id = Column(Integer, ForeignKey("config_change_history.id"), comment="回滾到的版本ID")
    
    # 元數據
    version = Column(String(50), comment="版本號")
    environment_applied = Column(String(100), comment="應用的環境")
    impact_assessment = Column(JSON, comment="影響評估")
    
    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="創建時間")
    created_by = Column(String(100), comment="創建者")
    
    # 關聯
    config_item = relationship("ConfigItem", back_populates="change_history")
    rollback_target = relationship("ConfigChangeHistory", remote_side=[id])
    
    # 索引
    __table_args__ = (
        Index('idx_change_config_time', 'config_item_id', 'created_at'),
        Index('idx_change_approval', 'approval_status', 'created_at'),
        Index('idx_change_applied', 'is_applied', 'applied_at'),
    )


class ConfigValidation(Base):
    """配置驗證記錄表"""
    __tablename__ = "config_validations"
    
    id = Column(Integer, primary_key=True, index=True)
    config_item_id = Column(Integer, ForeignKey("config_items.id"), nullable=False, index=True, comment="配置項ID")
    
    # 驗證信息
    validation_type = Column(String(50), nullable=False, comment="驗證類型")
    is_valid = Column(Boolean, nullable=False, comment="是否有效")
    error_message = Column(Text, comment="錯誤信息")
    warning_message = Column(Text, comment="警告信息")
    
    # 驗證詳情
    validated_value = Column(Text, comment="驗證的值")
    validation_rules_used = Column(JSON, comment="使用的驗證規則")
    validation_result = Column(JSON, comment="驗證結果詳情")
    
    # 時間戳
    validated_at = Column(DateTime(timezone=True), server_default=func.now(), comment="驗證時間")
    validated_by = Column(String(100), comment="驗證者")
    
    # 關聯
    config_item = relationship("ConfigItem", back_populates="validations")
    
    # 索引
    __table_args__ = (
        Index('idx_validation_config_time', 'config_item_id', 'validated_at'),
        Index('idx_validation_result', 'is_valid', 'validated_at'),
    )


class ConfigTemplate(Base):
    """配置模板表"""
    __tablename__ = "config_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="模板名稱")
    description = Column(Text, comment="模板描述")
    category = Column(SQLEnum(ConfigCategory), nullable=False, index=True, comment="模板分類")
    environment = Column(SQLEnum(ConfigEnvironment), nullable=False, default=ConfigEnvironment.ALL, comment="適用環境")
    
    # 模板內容
    template_data = Column(JSON, nullable=False, comment="模板數據")
    variables = Column(JSON, comment="模板變量")
    
    # 狀態
    is_active = Column(Boolean, default=True, comment="是否啟用")
    is_default = Column(Boolean, default=False, comment="是否為預設模板")
    
    # 版本信息
    version = Column(String(50), comment="模板版本")
    
    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="創建時間")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新時間")
    created_by = Column(String(100), comment="創建者")
    updated_by = Column(String(100), comment="更新者")
    
    # 索引
    __table_args__ = (
        Index('idx_template_category_active', 'category', 'is_active'),
        Index('idx_template_env_default', 'environment', 'is_default'),
    )


class ConfigBackup(Base):
    """配置備份表"""
    __tablename__ = "config_backups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, comment="備份名稱")
    description = Column(Text, comment="備份描述")
    environment = Column(SQLEnum(ConfigEnvironment), nullable=False, comment="備份環境")
    
    # 備份內容
    backup_data = Column(JSON, nullable=False, comment="備份數據")
    config_count = Column(Integer, comment="配置項數量")
    
    # 備份類型
    backup_type = Column(String(50), default="manual", comment="備份類型")  # manual, scheduled, auto
    
    # 狀態
    is_compressed = Column(Boolean, default=False, comment="是否壓縮")
    file_size = Column(Integer, comment="文件大小（字節）")
    checksum = Column(String(64), comment="校驗和")
    
    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="創建時間")
    created_by = Column(String(100), comment="創建者")
    
    # 索引
    __table_args__ = (
        Index('idx_backup_env_time', 'environment', 'created_at'),
        Index('idx_backup_type_time', 'backup_type', 'created_at'),
    )


class ConfigEnvironmentSync(Base):
    """配置環境同步記錄表"""
    __tablename__ = "config_environment_sync"
    
    id = Column(Integer, primary_key=True, index=True)
    source_environment = Column(SQLEnum(ConfigEnvironment), nullable=False, comment="源環境")
    target_environment = Column(SQLEnum(ConfigEnvironment), nullable=False, comment="目標環境")
    
    # 同步信息
    sync_type = Column(String(50), default="manual", comment="同步類型")  # manual, scheduled, auto
    config_keys = Column(JSON, comment="同步的配置鍵")
    
    # 同步結果
    total_configs = Column(Integer, comment="總配置數")
    success_count = Column(Integer, comment="成功數量")
    failed_count = Column(Integer, comment="失敗數量")
    skipped_count = Column(Integer, comment="跳過數量")
    
    # 狀態
    status = Column(String(50), default="pending", comment="同步狀態")  # pending, running, completed, failed
    error_message = Column(Text, comment="錯誤信息")
    sync_log = Column(JSON, comment="同步日誌")
    
    # 時間戳
    started_at = Column(DateTime(timezone=True), server_default=func.now(), comment="開始時間")
    completed_at = Column(DateTime(timezone=True), comment="完成時間")
    created_by = Column(String(100), comment="創建者")
    
    # 索引
    __table_args__ = (
        Index('idx_sync_env_time', 'source_environment', 'target_environment', 'started_at'),
        Index('idx_sync_status_time', 'status', 'started_at'),
    )