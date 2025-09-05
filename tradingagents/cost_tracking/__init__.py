#!/usr/bin/env python3
"""
Cost Tracking System - 成本追蹤系統
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級成本追蹤系統，提供完整的成本計算、監控和分析功能。
"""

from .hardware_cost_calculator import (
    HardwareCostCalculator,
    HardwareAsset,
    DepreciationSchedule,
    CostAllocationRule,
    HardwareCostCalculationResult,
    DepreciationMethod,
    AmortizationMethod,
    CostAllocationMethod,
    HardwareCategory,
    HardwareCostConfigurationFactory
)

from .power_maintenance_tracker import (
    PowerMaintenanceTracker,
    PowerConsumptionRecord,
    ElectricityPriceSchedule,
    MaintenanceRecord,
    CostCalculationResult as PowerMaintenanceCostResult,
    PowerSource,
    ElectricityPriceType,
    MaintenanceType,
    MaintenanceStatus,
    PowerMaintenanceConfigurationFactory
)

from .labor_cost_allocator import (
    LaborCostAllocator,
    Employee,
    WorkActivity,
    AllocationRule as LaborAllocationRule,
    CostAllocationResult as LaborCostResult,
    EmployeeRole,
    SkillLevel,
    ActivityType,
    AllocationMethod as LaborAllocationMethod,
    LaborCostConfigurationFactory
)

from .realtime_cost_monitor import (
    RealtimeCostMonitor,
    AlertRule,
    Alert,
    MonitoringMetrics,
    AlertSeverity,
    AlertType,
    MonitoringScope,
    MetricType as MonitoringMetricType,
    AlertConfigurationFactory
)

from .cost_calculation_service import (
    CostCalculationService,
    CostCalculationRequest,
    CostCalculationResult as ServiceCostResult,
    CalculationScope,
    ReportType
)

from .cost_analytics import (
    CostAnalytics,
    AnalysisRequest,
    AnalysisResult,
    CostDataPoint,
    AnalysisType,
    AnalysisDimension,
    MetricType as AnalyticsMetricType,
    AnalyticsFactory
)

__version__ = "1.0.0"
__author__ = "魯班 (Luban) - Code Artisan"

# 系統組件
__all__ = [
    # 硬體成本計算
    "HardwareCostCalculator",
    "HardwareAsset", 
    "DepreciationSchedule",
    "CostAllocationRule",
    "HardwareCostCalculationResult",
    "DepreciationMethod",
    "AmortizationMethod", 
    "CostAllocationMethod",
    "HardwareCategory",
    "HardwareCostConfigurationFactory",
    
    # 電力和維護成本追蹤
    "PowerMaintenanceTracker",
    "PowerConsumptionRecord",
    "ElectricityPriceSchedule", 
    "MaintenanceRecord",
    "PowerMaintenanceCostResult",
    "PowerSource",
    "ElectricityPriceType",
    "MaintenanceType",
    "MaintenanceStatus", 
    "PowerMaintenanceConfigurationFactory",
    
    # 人力成本分攤
    "LaborCostAllocator",
    "Employee",
    "WorkActivity",
    "LaborAllocationRule",
    "LaborCostResult", 
    "EmployeeRole",
    "SkillLevel",
    "ActivityType",
    "LaborAllocationMethod",
    "LaborCostConfigurationFactory",
    
    # 實時成本監控
    "RealtimeCostMonitor",
    "AlertRule",
    "Alert",
    "MonitoringMetrics",
    "AlertSeverity",
    "AlertType", 
    "MonitoringScope",
    "MonitoringMetricType",
    "AlertConfigurationFactory",
    
    # 成本計算服務
    "CostCalculationService", 
    "CostCalculationRequest",
    "ServiceCostResult",
    "CalculationScope",
    "ReportType",
    
    # 成本分析
    "CostAnalytics",
    "AnalysisRequest", 
    "AnalysisResult",
    "CostDataPoint",
    "AnalysisType",
    "AnalysisDimension",
    "AnalyticsMetricType",
    "AnalyticsFactory"
]

# 系統信息
SYSTEM_INFO = {
    "name": "GPT-OSS Cost Tracking System",
    "version": __version__,
    "description": "企業級GPT-OSS成本追蹤和分析系統",
    "components": {
        "hardware_calculator": "GPU硬體成本計算和折舊管理",
        "power_maintenance_tracker": "電力消耗和維護成本追蹤",
        "labor_allocator": "人力成本分攤和工時管理", 
        "realtime_monitor": "實時成本監控和告警系統",
        "calculation_service": "統一成本計算服務API",
        "analytics": "高級成本分析和商業智能"
    },
    "features": [
        "多維度成本計算和分攤",
        "實時成本監控和預警",
        "預測性成本建模",
        "自動化異常檢測",
        "成本優化建議",
        "完整的審計追蹤",
        "高性能並行處理",
        "企業級數據安全"
    ]
}


def get_system_info() -> dict:
    """獲取系統信息"""
    return SYSTEM_INFO


def get_version() -> str:
    """獲取系統版本"""
    return __version__


# 快速啟動函數
def create_integrated_cost_system(**kwargs):
    """創建集成的成本追蹤系統"""
    from ..database.virtual_pnl_db import VirtualPnLDB
    
    # 初始化核心組件
    virtual_pnl_db = VirtualPnLDB()
    hardware_calculator = HardwareCostCalculator()
    power_tracker = PowerMaintenanceTracker()
    labor_allocator = LaborCostAllocator() 
    cost_monitor = RealtimeCostMonitor(
        hardware_calculator=hardware_calculator,
        power_tracker=power_tracker,
        labor_allocator=labor_allocator
    )
    calculation_service = CostCalculationService(
        virtual_pnl_db=virtual_pnl_db,
        hardware_calculator=hardware_calculator,
        power_tracker=power_tracker,
        labor_allocator=labor_allocator,
        cost_monitor=cost_monitor
    )
    analytics = CostAnalytics()
    
    return {
        "virtual_pnl_db": virtual_pnl_db,
        "hardware_calculator": hardware_calculator,
        "power_tracker": power_tracker,
        "labor_allocator": labor_allocator,
        "cost_monitor": cost_monitor,
        "calculation_service": calculation_service,
        "analytics": analytics
    }