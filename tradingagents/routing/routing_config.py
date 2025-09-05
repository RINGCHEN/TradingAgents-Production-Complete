#!/usr/bin/env python3
"""
Routing Configuration System
路由策略配置系統 - GPT-OSS整合任務1.3.1

動態路由策略配置和管理系統，支持：
- 策略模板管理
- 動態權重調整
- 配置熱更新
- 策略A/B測試
"""

import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

from .ai_task_router import RoutingStrategy, RoutingWeights, DecisionFactor

logger = logging.getLogger(__name__)

# ==================== 配置數據類型 ====================

@dataclass
class StrategyTemplate:
    """策略模板"""
    name: str
    display_name: str
    description: str
    weights: RoutingWeights
    use_cases: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    performance_targets: Dict[str, float] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        data['weights'] = asdict(self.weights)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyTemplate':
        """從字典創建實例"""
        weights_data = data.pop('weights', {})
        weights = RoutingWeights(**weights_data)
        
        created_at = datetime.fromisoformat(data.pop('created_at', datetime.now(timezone.utc).isoformat()))
        updated_at = datetime.fromisoformat(data.pop('updated_at', datetime.now(timezone.utc).isoformat()))
        
        return cls(
            weights=weights,
            created_at=created_at,
            updated_at=updated_at,
            **data
        )

@dataclass 
class RoutingPolicy:
    """路由策略政策"""
    name: str
    task_type_mappings: Dict[str, str]  # task_type -> strategy_name
    user_tier_mappings: Dict[str, str]  # user_tier -> strategy_name
    priority_mappings: Dict[str, str]   # priority -> strategy_name
    fallback_strategy: str = "balanced"
    conditions: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    
    def get_strategy_for_request(
        self, 
        task_type: str, 
        user_tier: str = "free", 
        priority: str = "standard"
    ) -> str:
        """根據請求屬性獲取策略名稱"""
        
        # 1. 檢查任務類型映射
        if task_type in self.task_type_mappings:
            return self.task_type_mappings[task_type]
        
        # 2. 檢查用戶等級映射
        if user_tier in self.user_tier_mappings:
            return self.user_tier_mappings[user_tier]
        
        # 3. 檢查優先級映射
        if priority in self.priority_mappings:
            return self.priority_mappings[priority]
        
        # 4. 返回默認策略
        return self.fallback_strategy

@dataclass
class ConfigurationProfile:
    """配置檔案"""
    name: str
    version: str
    description: str
    strategy_templates: Dict[str, StrategyTemplate]
    routing_policies: Dict[str, RoutingPolicy] 
    global_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'strategy_templates': {
                name: template.to_dict() 
                for name, template in self.strategy_templates.items()
            },
            'routing_policies': {
                name: asdict(policy)
                for name, policy in self.routing_policies.items()
            },
            'global_settings': self.global_settings,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }

# ==================== 配置管理器 ====================

class RoutingConfigManager:
    """路由配置管理器"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目錄
        """
        self.config_dir = config_dir or Path("routing_configs")
        self.config_dir.mkdir(exist_ok=True)
        
        # 當前配置
        self.current_profile: Optional[ConfigurationProfile] = None
        self.active_strategies: Dict[str, StrategyTemplate] = {}
        self.active_policies: Dict[str, RoutingPolicy] = {}
        
        # 配置歷史和版本管理
        self.config_history: List[ConfigurationProfile] = []
        self.max_history_size = 10
        
        self.logger = logger
        
        # 初始化預設配置
        self._initialize_default_configurations()
    
    def _initialize_default_configurations(self):
        """初始化預設配置"""
        try:
            # 創建預設策略模板
            default_templates = self._create_default_strategy_templates()
            
            # 創建預設路由策略
            default_policies = self._create_default_routing_policies()
            
            # 創建預設配置檔案
            default_profile = ConfigurationProfile(
                name="default",
                version="1.0.0",
                description="預設路由配置檔案",
                strategy_templates=default_templates,
                routing_policies=default_policies,
                global_settings={
                    'enable_a_b_testing': False,
                    'performance_monitoring_enabled': True,
                    'auto_strategy_adjustment': False,
                    'decision_cache_ttl': 3600,
                    'max_fallback_attempts': 3
                }
            )
            
            self.current_profile = default_profile
            self.active_strategies = default_templates
            self.active_policies = default_policies
            
            # 保存預設配置
            self.save_configuration_profile(default_profile)
            
            self.logger.info("✅ Default routing configurations initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize default configurations: {e}")
            raise
    
    def _create_default_strategy_templates(self) -> Dict[str, StrategyTemplate]:
        """創建預設策略模板"""
        templates = {}
        
        # 成本優化策略
        templates['cost_optimized'] = StrategyTemplate(
            name='cost_optimized',
            display_name='成本優化',
            description='優先選擇成本最低的模型，適合大批量處理任務',
            weights=RoutingWeights(
                cost=0.5, latency=0.15, quality=0.2, 
                availability=0.1, privacy=0.03, user_preference=0.02
            ),
            use_cases=['批量數據處理', '非關鍵業務分析', '開發測試環境'],
            performance_targets={'max_cost_per_1k': 0.005}
        )
        
        # 性能優化策略
        templates['performance_optimized'] = StrategyTemplate(
            name='performance_optimized',
            display_name='性能優化',
            description='優先選擇響應最快、品質最好的模型',
            weights=RoutingWeights(
                cost=0.1, latency=0.4, quality=0.35,
                availability=0.1, privacy=0.03, user_preference=0.02
            ),
            use_cases=['實時交易決策', '緊急風險評估', '用戶互動分析'],
            performance_targets={'max_latency_ms': 2000, 'min_quality_score': 0.85}
        )
        
        # 平衡策略
        templates['balanced'] = StrategyTemplate(
            name='balanced',
            display_name='平衡策略',
            description='在成本、性能、品質間取得最佳平衡',
            weights=RoutingWeights(
                cost=0.25, latency=0.25, quality=0.25,
                availability=0.15, privacy=0.05, user_preference=0.05
            ),
            use_cases=['日常業務分析', '標準投資建議', '一般用戶服務'],
            performance_targets={'max_cost_per_1k': 0.015, 'max_latency_ms': 5000}
        )
        
        # 品質優先策略  
        templates['quality_first'] = StrategyTemplate(
            name='quality_first',
            display_name='品質優先',
            description='優先選擇能力評分最高的模型',
            weights=RoutingWeights(
                cost=0.1, latency=0.15, quality=0.5,
                availability=0.15, privacy=0.05, user_preference=0.05
            ),
            use_cases=['高風險投資決策', '監管報告生成', '精準市場分析'],
            performance_targets={'min_quality_score': 0.9}
        )
        
        # 隱私優先策略
        templates['privacy_first'] = StrategyTemplate(
            name='privacy_first',
            display_name='隱私優先',
            description='優先使用本地部署或高隱私保護的模型',
            weights=RoutingWeights(
                cost=0.15, latency=0.15, quality=0.2,
                availability=0.1, privacy=0.35, user_preference=0.05
            ),
            use_cases=['敏感數據分析', '內部風控模型', '合規性檢查'],
            prerequisites=['local_models_available'],
            performance_targets={'privacy_level': 'local'}
        )
        
        # 延遲優先策略
        templates['latency_first'] = StrategyTemplate(
            name='latency_first', 
            display_name='延遲優先',
            description='優先選擇響應最快的模型',
            weights=RoutingWeights(
                cost=0.15, latency=0.5, quality=0.2,
                availability=0.1, privacy=0.03, user_preference=0.02
            ),
            use_cases=['高頻交易', '實時風險監控', '即時客戶服務'],
            performance_targets={'max_latency_ms': 1000}
        )
        
        return templates
    
    def _create_default_routing_policies(self) -> Dict[str, RoutingPolicy]:
        """創建預設路由策略"""
        policies = {}
        
        # 標準業務策略
        policies['standard_business'] = RoutingPolicy(
            name='standard_business',
            task_type_mappings={
                'financial_summary': 'balanced',
                'news_classification': 'performance_optimized',
                'investment_reasoning': 'quality_first',
                'report_generation': 'balanced',
                'market_sentiment': 'performance_optimized'
            },
            user_tier_mappings={
                'free': 'cost_optimized',
                'basic': 'cost_optimized', 
                'premium': 'balanced',
                'gold': 'quality_first',
                'enterprise': 'quality_first'
            },
            priority_mappings={
                'low': 'cost_optimized',
                'standard': 'balanced',
                'high': 'performance_optimized',
                'urgent': 'latency_first'
            },
            fallback_strategy='balanced'
        )
        
        # 高安全性策略
        policies['high_security'] = RoutingPolicy(
            name='high_security',
            task_type_mappings={
                'investment_reasoning': 'privacy_first',
                'financial_summary': 'privacy_first',
                'report_generation': 'privacy_first'
            },
            user_tier_mappings={
                'enterprise': 'privacy_first',
                'gold': 'privacy_first'
            },
            priority_mappings={},
            fallback_strategy='privacy_first',
            conditions={
                'data_sensitivity_level': ['high', 'confidential'],
                'requires_local_processing': True
            }
        )
        
        # 成本控制策略
        policies['cost_control'] = RoutingPolicy(
            name='cost_control',
            task_type_mappings={},
            user_tier_mappings={
                'free': 'cost_optimized',
                'basic': 'cost_optimized'
            },
            priority_mappings={
                'low': 'cost_optimized',
                'standard': 'cost_optimized'
            },
            fallback_strategy='cost_optimized',
            conditions={
                'max_daily_cost': 100.0,
                'cost_alert_threshold': 0.8
            }
        )
        
        return policies
    
    # ==================== 配置管理接口 ====================
    
    def create_strategy_template(
        self,
        name: str,
        display_name: str,
        description: str,
        weights: RoutingWeights,
        **kwargs
    ) -> StrategyTemplate:
        """創建新的策略模板"""
        try:
            weights.normalize()
            
            template = StrategyTemplate(
                name=name,
                display_name=display_name,
                description=description,
                weights=weights,
                **kwargs
            )
            
            if self.current_profile:
                self.current_profile.strategy_templates[name] = template
                self.active_strategies[name] = template
            
            self.logger.info(f"✅ Created strategy template: {name}")
            return template
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create strategy template {name}: {e}")
            raise
    
    def update_strategy_template(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> Optional[StrategyTemplate]:
        """更新策略模板"""
        try:
            if name not in self.active_strategies:
                self.logger.warning(f"Strategy template '{name}' not found")
                return None
            
            template = self.active_strategies[name]
            
            # 更新字段
            for key, value in updates.items():
                if hasattr(template, key):
                    if key == 'weights' and isinstance(value, dict):
                        # 更新權重
                        for weight_key, weight_value in value.items():
                            if hasattr(template.weights, weight_key):
                                setattr(template.weights, weight_key, weight_value)
                        template.weights.normalize()
                    else:
                        setattr(template, key, value)
            
            template.updated_at = datetime.now(timezone.utc)
            
            self.logger.info(f"✅ Updated strategy template: {name}")
            return template
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update strategy template {name}: {e}")
            raise
    
    def create_routing_policy(
        self,
        name: str,
        task_type_mappings: Dict[str, str],
        user_tier_mappings: Dict[str, str],
        priority_mappings: Dict[str, str],
        **kwargs
    ) -> RoutingPolicy:
        """創建新的路由策略"""
        try:
            policy = RoutingPolicy(
                name=name,
                task_type_mappings=task_type_mappings,
                user_tier_mappings=user_tier_mappings,
                priority_mappings=priority_mappings,
                **kwargs
            )
            
            if self.current_profile:
                self.current_profile.routing_policies[name] = policy
                self.active_policies[name] = policy
            
            self.logger.info(f"✅ Created routing policy: {name}")
            return policy
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create routing policy {name}: {e}")
            raise
    
    def get_strategy_for_request(
        self,
        task_type: str,
        user_tier: str = "free",
        priority: str = "standard",
        policy_name: str = "standard_business"
    ) -> Optional[str]:
        """根據請求獲取推薦策略"""
        try:
            if policy_name not in self.active_policies:
                policy_name = "standard_business"  # 使用預設策略
            
            policy = self.active_policies.get(policy_name)
            if not policy:
                return "balanced"  # 最終後備策略
            
            return policy.get_strategy_for_request(task_type, user_tier, priority)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get strategy for request: {e}")
            return "balanced"
    
    def get_strategy_weights(self, strategy_name: str) -> Optional[RoutingWeights]:
        """獲取策略權重"""
        template = self.active_strategies.get(strategy_name)
        return template.weights if template else None
    
    # ==================== 配置持久化 ====================
    
    def save_configuration_profile(
        self, 
        profile: ConfigurationProfile,
        format: str = "yaml"
    ) -> bool:
        """保存配置檔案"""
        try:
            filename = f"{profile.name}_{profile.version}.{format}"
            filepath = self.config_dir / filename
            
            profile_data = profile.to_dict()
            
            if format.lower() == "yaml":
                with open(filepath, 'w', encoding='utf-8') as f:
                    yaml.dump(profile_data, f, default_flow_style=False, allow_unicode=True)
            else:  # json
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(profile_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"✅ Saved configuration profile: {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save configuration profile: {e}")
            return False
    
    def load_configuration_profile(
        self,
        name: str,
        version: Optional[str] = None
    ) -> Optional[ConfigurationProfile]:
        """載入配置檔案"""
        try:
            # 尋找匹配的配置文件
            pattern = f"{name}_*.yaml" if version is None else f"{name}_{version}.yaml"
            config_files = list(self.config_dir.glob(pattern))
            
            if not config_files:
                # 嘗試JSON格式
                pattern = f"{name}_*.json" if version is None else f"{name}_{version}.json"
                config_files = list(self.config_dir.glob(pattern))
            
            if not config_files:
                self.logger.warning(f"No configuration files found for {name}")
                return None
            
            # 使用最新的文件
            config_file = max(config_files, key=lambda f: f.stat().st_mtime)
            
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_file.suffix == '.yaml':
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            
            # 重構配置檔案對象
            profile = self._reconstruct_configuration_profile(data)
            
            self.logger.info(f"✅ Loaded configuration profile: {config_file.name}")
            return profile
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load configuration profile: {e}")
            return None
    
    def _reconstruct_configuration_profile(self, data: Dict[str, Any]) -> ConfigurationProfile:
        """重構配置檔案對象"""
        # 重構策略模板
        strategy_templates = {}
        for name, template_data in data.get('strategy_templates', {}).items():
            strategy_templates[name] = StrategyTemplate.from_dict(template_data)
        
        # 重構路由策略
        routing_policies = {}
        for name, policy_data in data.get('routing_policies', {}).items():
            routing_policies[name] = RoutingPolicy(**policy_data)
        
        # 重構配置檔案
        created_at = datetime.fromisoformat(data.get('created_at', datetime.now(timezone.utc).isoformat()))
        
        return ConfigurationProfile(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            strategy_templates=strategy_templates,
            routing_policies=routing_policies,
            global_settings=data.get('global_settings', {}),
            created_at=created_at,
            is_active=data.get('is_active', True)
        )
    
    def apply_configuration_profile(self, profile: ConfigurationProfile) -> bool:
        """應用配置檔案"""
        try:
            # 備份當前配置
            if self.current_profile:
                self.config_history.append(self.current_profile)
                if len(self.config_history) > self.max_history_size:
                    self.config_history = self.config_history[-self.max_history_size:]
            
            # 應用新配置
            self.current_profile = profile
            self.active_strategies = profile.strategy_templates.copy()
            self.active_policies = profile.routing_policies.copy()
            
            self.logger.info(f"✅ Applied configuration profile: {profile.name} v{profile.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to apply configuration profile: {e}")
            return False
    
    # ==================== A/B測試支持 ====================
    
    def create_ab_test_variant(
        self,
        base_strategy: str,
        variant_name: str,
        modifications: Dict[str, Any],
        traffic_percentage: float = 0.1
    ) -> Optional[StrategyTemplate]:
        """創建A/B測試變體策略"""
        try:
            if base_strategy not in self.active_strategies:
                self.logger.error(f"Base strategy '{base_strategy}' not found")
                return None
            
            base_template = self.active_strategies[base_strategy]
            
            # 創建變體模板
            variant_template = StrategyTemplate(
                name=variant_name,
                display_name=f"{base_template.display_name} (A/B變體)",
                description=f"A/B測試變體 - 基於 {base_strategy}",
                weights=RoutingWeights(**asdict(base_template.weights)),
                use_cases=base_template.use_cases.copy(),
                prerequisites=base_template.prerequisites.copy(),
                performance_targets=base_template.performance_targets.copy()
            )
            
            # 應用修改
            for key, value in modifications.items():
                if key == 'weights':
                    for weight_key, weight_value in value.items():
                        if hasattr(variant_template.weights, weight_key):
                            setattr(variant_template.weights, weight_key, weight_value)
                    variant_template.weights.normalize()
                elif hasattr(variant_template, key):
                    setattr(variant_template, key, value)
            
            # 添加A/B測試元數據
            variant_template.performance_targets['ab_test_traffic_percentage'] = traffic_percentage
            variant_template.performance_targets['ab_test_base_strategy'] = base_strategy
            
            self.active_strategies[variant_name] = variant_template
            
            self.logger.info(f"✅ Created A/B test variant: {variant_name}")
            return variant_template
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create A/B test variant: {e}")
            return None
    
    # ==================== 統計和監控 ====================
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """獲取配置摘要"""
        return {
            'current_profile': {
                'name': self.current_profile.name if self.current_profile else None,
                'version': self.current_profile.version if self.current_profile else None,
                'strategy_count': len(self.active_strategies),
                'policy_count': len(self.active_policies)
            },
            'available_strategies': list(self.active_strategies.keys()),
            'available_policies': list(self.active_policies.keys()),
            'config_history_count': len(self.config_history),
            'config_directory': str(self.config_dir),
            'last_update': datetime.now(timezone.utc).isoformat()
        }
    
    def validate_configuration(
        self, 
        profile: Optional[ConfigurationProfile] = None
    ) -> Dict[str, Any]:
        """驗證配置有效性"""
        profile = profile or self.current_profile
        if not profile:
            return {'valid': False, 'errors': ['No configuration profile available']}
        
        errors = []
        warnings = []
        
        # 驗證策略模板
        for name, template in profile.strategy_templates.items():
            # 檢查權重總和
            total_weight = (
                template.weights.cost + template.weights.latency + 
                template.weights.quality + template.weights.availability +
                template.weights.privacy + template.weights.user_preference
            )
            if abs(total_weight - 1.0) > 0.01:
                warnings.append(f"Strategy '{name}' weights sum to {total_weight:.3f}, not 1.0")
        
        # 驗證路由策略
        for name, policy in profile.routing_policies.items():
            # 檢查策略引用
            all_referenced_strategies = set()
            all_referenced_strategies.update(policy.task_type_mappings.values())
            all_referenced_strategies.update(policy.user_tier_mappings.values())
            all_referenced_strategies.update(policy.priority_mappings.values())
            all_referenced_strategies.add(policy.fallback_strategy)
            
            for strategy_name in all_referenced_strategies:
                if strategy_name not in profile.strategy_templates:
                    errors.append(f"Policy '{name}' references unknown strategy '{strategy_name}'")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'strategy_count': len(profile.strategy_templates),
            'policy_count': len(profile.routing_policies)
        }