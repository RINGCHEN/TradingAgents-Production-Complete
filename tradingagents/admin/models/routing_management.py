#!/usr/bin/env python3
"""
路由管理數據模型
GPT-OSS整合任務1.3.3 - 路由策略配置界面

提供路由管理系統的核心數據模型和業務邏輯
"""

import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
from pydantic import BaseModel, validator, Field

from ...routing.ai_task_router import RoutingStrategy, RoutingWeights, DecisionFactor
from ...routing.routing_config import StrategyTemplate, RoutingPolicy, ConfigurationProfile


class RouteOperationType(str, Enum):
    """路由操作類型"""
    CREATE_STRATEGY = "create_strategy"
    UPDATE_STRATEGY = "update_strategy" 
    DELETE_STRATEGY = "delete_strategy"
    ACTIVATE_STRATEGY = "activate_strategy"
    DEACTIVATE_STRATEGY = "deactivate_strategy"
    CREATE_POLICY = "create_policy"
    UPDATE_POLICY = "update_policy"
    DELETE_POLICY = "delete_policy"
    AB_TEST_CREATE = "ab_test_create"
    AB_TEST_UPDATE = "ab_test_update"
    AB_TEST_STOP = "ab_test_stop"
    CONFIG_BACKUP = "config_backup"
    CONFIG_RESTORE = "config_restore"


class RouteConfigStatus(str, Enum):
    """路由配置狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TESTING = "testing"
    DEPRECATED = "deprecated"
    DRAFT = "draft"


# ==================== 請求模型 ====================

class RoutingWeightsRequest(BaseModel):
    """路由權重請求模型"""
    cost: float = Field(ge=0, le=1, description="成本權重")
    latency: float = Field(ge=0, le=1, description="延遲權重")
    quality: float = Field(ge=0, le=1, description="品質權重")
    availability: float = Field(ge=0, le=1, description="可用性權重")
    privacy: float = Field(ge=0, le=1, description="隱私權重")
    user_preference: float = Field(ge=0, le=1, description="用戶偏好權重")
    
    @validator('*')
    def validate_weights(cls, v):
        """驗證權重值"""
        if not 0 <= v <= 1:
            raise ValueError('權重值必須在0到1之間')
        return v
    
    def to_routing_weights(self) -> RoutingWeights:
        """轉換為路由權重對象"""
        weights = RoutingWeights(**self.dict())
        weights.normalize()
        return weights


class StrategyTemplateRequest(BaseModel):
    """策略模板請求模型"""
    name: str = Field(min_length=1, max_length=50, description="策略名稱")
    display_name: str = Field(min_length=1, max_length=100, description="顯示名稱")
    description: str = Field(max_length=500, description="策略描述")
    weights: RoutingWeightsRequest = Field(description="路由權重")
    use_cases: List[str] = Field(default=[], description="使用案例")
    prerequisites: List[str] = Field(default=[], description="前置條件")
    performance_targets: Dict[str, Union[float, str]] = Field(default={}, description="性能目標")
    is_active: bool = Field(default=True, description="是否啟用")
    
    @validator('name')
    def validate_name(cls, v):
        """驗證策略名稱"""
        if not v.replace('_', '').isalnum():
            raise ValueError('策略名稱只能包含字母、數字和下劃線')
        return v.lower()


class RoutingPolicyRequest(BaseModel):
    """路由策略請求模型"""
    name: str = Field(min_length=1, max_length=50, description="策略名稱")
    task_type_mappings: Dict[str, str] = Field(default={}, description="任務類型映射")
    user_tier_mappings: Dict[str, str] = Field(default={}, description="用戶等級映射")
    priority_mappings: Dict[str, str] = Field(default={}, description="優先級映射")
    fallback_strategy: str = Field(default="balanced", description="後備策略")
    conditions: Dict[str, Any] = Field(default={}, description="條件配置")
    is_active: bool = Field(default=True, description="是否啟用")


class ABTestVariantRequest(BaseModel):
    """A/B測試變體請求模型"""
    base_strategy: str = Field(description="基礎策略名稱")
    variant_name: str = Field(min_length=1, max_length=50, description="變體名稱")
    traffic_percentage: float = Field(ge=0.01, le=0.5, description="流量百分比")
    modifications: Dict[str, Any] = Field(description="修改配置")
    test_description: str = Field(max_length=500, description="測試描述")
    expected_duration_days: int = Field(ge=1, le=90, default=7, description="預期測試天數")


# ==================== 響應模型 ====================

class StrategyTemplateResponse(BaseModel):
    """策略模板響應模型"""
    name: str
    display_name: str
    description: str
    weights: Dict[str, float]
    use_cases: List[str]
    prerequisites: List[str]
    performance_targets: Dict[str, Any]
    status: RouteConfigStatus
    created_at: datetime
    updated_at: datetime
    is_active: bool
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RoutingPolicyResponse(BaseModel):
    """路由策略響應模型"""
    name: str
    task_type_mappings: Dict[str, str]
    user_tier_mappings: Dict[str, str]
    priority_mappings: Dict[str, str]
    fallback_strategy: str
    conditions: Dict[str, Any]
    status: RouteConfigStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ABTestResponse(BaseModel):
    """A/B測試響應模型"""
    test_id: str
    test_name: str
    base_strategy: str
    variant_strategy: str
    traffic_percentage: float
    status: str
    start_date: datetime
    end_date: Optional[datetime]
    metrics: Dict[str, Any]
    is_active: bool
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RoutingPerformanceResponse(BaseModel):
    """路由性能響應模型"""
    period: str
    total_decisions: int
    successful_decisions: int
    failed_decisions: int
    average_decision_time_ms: float
    strategy_usage: Dict[str, int]
    model_selection_frequency: Dict[str, int]
    cost_savings: float
    quality_metrics: Dict[str, float]
    latency_metrics: Dict[str, float]
    
    
class RoutingDashboardResponse(BaseModel):
    """路由儀表板響應模型"""
    summary: Dict[str, Any]
    active_strategies: List[StrategyTemplateResponse]
    active_policies: List[RoutingPolicyResponse]
    active_ab_tests: List[ABTestResponse]
    recent_decisions: List[Dict[str, Any]]
    performance_metrics: RoutingPerformanceResponse
    system_health: Dict[str, Any]


# ==================== 審計和日誌模型 ====================

@dataclass
class RouteOperationAudit:
    """路由操作審計記錄"""
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: RouteOperationType
    target_name: str
    operator_id: str
    operator_name: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    changes: Dict[str, Any] = field(default_factory=dict)
    previous_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None
    success: bool = True
    error_message: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        result = asdict(self)
        result['operation_type'] = self.operation_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result


class RouteConfigurationSnapshot(BaseModel):
    """路由配置快照模型"""
    snapshot_id: str
    profile_name: str
    version: str
    created_by: str
    created_at: datetime
    description: str
    strategy_count: int
    policy_count: int
    configuration_data: Dict[str, Any]
    is_backup: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ==================== 業務邏輯模型 ====================

class RoutingConfigValidator:
    """路由配置驗證器"""
    
    @staticmethod
    def validate_strategy_template(template: StrategyTemplateRequest) -> List[str]:
        """驗證策略模板"""
        errors = []
        
        # 檢查權重總和
        weights = template.weights
        total_weight = (
            weights.cost + weights.latency + weights.quality + 
            weights.availability + weights.privacy + weights.user_preference
        )
        
        if abs(total_weight - 1.0) > 0.01:
            errors.append(f"權重總和為 {total_weight:.3f}，應該等於 1.0")
        
        # 檢查性能目標
        for key, value in template.performance_targets.items():
            if key.startswith('max_') and isinstance(value, (int, float)) and value <= 0:
                errors.append(f"性能目標 {key} 的值必須大於 0")
        
        return errors
    
    @staticmethod
    def validate_routing_policy(policy: RoutingPolicyRequest, available_strategies: List[str]) -> List[str]:
        """驗證路由策略"""
        errors = []
        
        # 檢查策略引用
        all_referenced_strategies = set()
        all_referenced_strategies.update(policy.task_type_mappings.values())
        all_referenced_strategies.update(policy.user_tier_mappings.values())
        all_referenced_strategies.update(policy.priority_mappings.values())
        all_referenced_strategies.add(policy.fallback_strategy)
        
        for strategy_name in all_referenced_strategies:
            if strategy_name not in available_strategies:
                errors.append(f"引用了未知的策略: {strategy_name}")
        
        return errors
    
    @staticmethod
    def validate_ab_test(test: ABTestVariantRequest, available_strategies: List[str]) -> List[str]:
        """驗證A/B測試配置"""
        errors = []
        
        if test.base_strategy not in available_strategies:
            errors.append(f"基礎策略 {test.base_strategy} 不存在")
        
        if test.traffic_percentage > 0.5:
            errors.append("A/B測試流量不應超過50%")
        
        # 檢查修改配置
        if 'weights' in test.modifications:
            weights = test.modifications['weights']
            if not isinstance(weights, dict):
                errors.append("權重修改必須是字典格式")
            else:
                total = sum(weights.values())
                if abs(total - 1.0) > 0.01:
                    errors.append(f"修改後的權重總和為 {total:.3f}，應該等於 1.0")
        
        return errors


class RoutingMetricsCollector:
    """路由指標收集器"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.cache_ttl = 300  # 5分鐘緩存
        
    async def collect_performance_metrics(
        self, 
        period_hours: int = 24
    ) -> Dict[str, Any]:
        """收集性能指標"""
        cache_key = f"performance_{period_hours}h"
        
        if self._is_cache_valid(cache_key):
            return self.metrics_cache[cache_key]['data']
        
        # 這裡應該從實際的監控系統獲取數據
        # 暫時返回模擬數據
        metrics = {
            'total_decisions': 1500,
            'successful_decisions': 1485,
            'failed_decisions': 15,
            'success_rate': 0.99,
            'average_decision_time_ms': 285.7,
            'strategy_usage': {
                'balanced': 650,
                'cost_optimized': 400,
                'quality_first': 300,
                'performance_optimized': 150
            },
            'model_selection_frequency': {
                'openai/gpt-4': 800,
                'openai/gpt-3.5-turbo': 500,
                'local/llama2': 200
            },
            'cost_metrics': {
                'total_cost': 125.50,
                'average_cost_per_1k': 0.0837,
                'cost_savings': 23.4
            },
            'latency_metrics': {
                'p50': 250,
                'p95': 850,
                'p99': 1200,
                'max': 2100
            },
            'quality_metrics': {
                'average_score': 0.847,
                'min_score': 0.623,
                'max_score': 0.965,
                'quality_variance': 0.042
            }
        }
        
        self.metrics_cache[cache_key] = {
            'data': metrics,
            'timestamp': datetime.now(timezone.utc)
        }
        
        return metrics
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """檢查緩存是否有效"""
        if cache_key not in self.metrics_cache:
            return False
        
        cache_time = self.metrics_cache[cache_key]['timestamp']
        return (datetime.now(timezone.utc) - cache_time).seconds < self.cache_ttl


# 全局指標收集器實例
routing_metrics_collector = RoutingMetricsCollector()