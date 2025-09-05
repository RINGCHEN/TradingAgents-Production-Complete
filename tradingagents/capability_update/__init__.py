#!/usr/bin/env python3
"""
Capability Update Module
動態能力更新模組 - GPT-OSS整合任務1.2.3

這個模組提供了完整的動態能力更新機制，包括：
- 模型版本控制和歷史追蹤
- 自動化能力數據更新觸發
- 能力變化告警系統
- A/B測試和灰度更新支援
- 綜合監控儀表板和報告
"""

from .model_version_control import (
    ModelVersionControl,
    VersionUpdateRequest,
    VersionComparisonResult,
    ChangeType,
    DeploymentStage
)

from .dynamic_capability_updater import (
    DynamicCapabilityUpdater,
    UpdateTrigger,
    UpdateStrategy,
    UpdateRule,
    UpdateTask,
    UpdateResult
)

from .capability_alert_system import (
    CapabilityAlertSystem,
    AlertSeverity,
    AlertType,
    AlertStatus,
    Alert,
    AlertCondition,
    AlertChannel,
    LogAlertChannel,
    WebhookAlertChannel,
    EmailAlertChannel
)

from .ab_testing_system import (
    ABTestingSystem,
    ExperimentType,
    ExperimentStatus,
    TrafficSplitStrategy,
    ExperimentDecision,
    Experiment,
    ExperimentVariant,
    TrafficSplitConfig
)

from .capability_dashboard import (
    CapabilityDashboard,
    DashboardMetricType,
    ReportType,
    DashboardWidget,
    DashboardLayout
)

__all__ = [
    # 版本控制
    'ModelVersionControl',
    'VersionUpdateRequest',
    'VersionComparisonResult',
    'ChangeType',
    'DeploymentStage',
    
    # 動態更新
    'DynamicCapabilityUpdater',
    'UpdateTrigger',
    'UpdateStrategy',
    'UpdateRule',
    'UpdateTask',
    'UpdateResult',
    
    # 告警系統
    'CapabilityAlertSystem',
    'AlertSeverity',
    'AlertType',
    'AlertStatus',
    'Alert',
    'AlertCondition',
    'AlertChannel',
    'LogAlertChannel',
    'WebhookAlertChannel',
    'EmailAlertChannel',
    
    # A/B測試
    'ABTestingSystem',
    'ExperimentType',
    'ExperimentStatus',
    'TrafficSplitStrategy',
    'ExperimentDecision',
    'Experiment',
    'ExperimentVariant',
    'TrafficSplitConfig',
    
    # 監控儀表板
    'CapabilityDashboard',
    'DashboardMetricType',
    'ReportType',
    'DashboardWidget',
    'DashboardLayout'
]

__version__ = "1.2.3"
__description__ = "Dynamic Capability Update System for GPT-OSS Integration"