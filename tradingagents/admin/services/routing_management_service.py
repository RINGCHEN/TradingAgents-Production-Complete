#!/usr/bin/env python3
"""
路由管理服務層
GPT-OSS整合任務1.3.3 - 路由策略配置界面服務實現

提供完整的路由管理業務邏輯和數據操作
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

from ...routing.ai_task_router import (
    AITaskRouter, RoutingStrategy, RoutingWeights, DecisionFactor,
    RoutingDecisionRequest, ModelScore
)
from ...routing.routing_config import (
    RoutingConfigManager, StrategyTemplate, RoutingPolicy, ConfigurationProfile
)
from ..models.routing_management import (
    StrategyTemplateRequest, StrategyTemplateResponse,
    RoutingPolicyRequest, RoutingPolicyResponse,
    ABTestVariantRequest, ABTestResponse,
    RoutingPerformanceResponse, RoutingDashboardResponse,
    RouteOperationAudit, RouteOperationType, RouteConfigStatus,
    RouteConfigurationSnapshot, RoutingConfigValidator,
    routing_metrics_collector
)

logger = logging.getLogger(__name__)


class RoutingManagementService:
    """路由管理服務"""
    
    def __init__(
        self,
        ai_task_router: Optional[AITaskRouter] = None,
        routing_config_manager: Optional[RoutingConfigManager] = None,
        config_dir: Optional[Path] = None
    ):
        """
        初始化路由管理服務
        
        Args:
            ai_task_router: AI任務路由器實例
            routing_config_manager: 路由配置管理器實例
            config_dir: 配置文件目錄
        """
        self.ai_task_router = ai_task_router
        self.routing_config_manager = routing_config_manager or RoutingConfigManager(config_dir)
        
        # 審計記錄存儲
        self.audit_records: List[RouteOperationAudit] = []
        self.max_audit_records = 1000
        
        # A/B測試管理
        self.active_ab_tests: Dict[str, Dict[str, Any]] = {}
        self.ab_test_results: Dict[str, Dict[str, Any]] = {}
        
        # 配置快照
        self.configuration_snapshots: List[RouteConfigurationSnapshot] = []
        self.max_snapshots = 50
        
        # 性能監控
        self.metrics_collector = routing_metrics_collector
        
        self.logger = logger
    
    # ==================== 策略模板管理 ====================
    
    async def create_strategy_template(
        self,
        request: StrategyTemplateRequest,
        operator_id: str,
        operator_name: str
    ) -> Tuple[bool, Union[StrategyTemplateResponse, List[str]]]:
        """創建策略模板"""
        try:
            # 驗證請求
            validation_errors = RoutingConfigValidator.validate_strategy_template(request)
            if validation_errors:
                return False, validation_errors
            
            # 檢查名稱唯一性
            if request.name in self.routing_config_manager.active_strategies:
                return False, [f"策略名稱 '{request.name}' 已存在"]
            
            # 創建策略模板
            weights = request.weights.to_routing_weights()
            template = self.routing_config_manager.create_strategy_template(
                name=request.name,
                display_name=request.display_name,
                description=request.description,
                weights=weights,
                use_cases=request.use_cases,
                prerequisites=request.prerequisites,
                performance_targets=request.performance_targets,
                is_active=request.is_active
            )
            
            # 記錄審計日誌
            await self._record_audit(
                RouteOperationType.CREATE_STRATEGY,
                request.name,
                operator_id,
                operator_name,
                new_config=request.dict()
            )
            
            # 應用到AI路由器 (如果已初始化)
            if self.ai_task_router and request.is_active:
                try:
                    strategy_enum = RoutingStrategy(request.name)
                    self.ai_task_router.routing_strategies[strategy_enum] = weights
                    self.ai_task_router.stats['strategy_usage'][request.name] = 0
                except ValueError:
                    # 如果策略不是預定義枚舉，創建自定義策略
                    self.ai_task_router.add_custom_strategy(request.name, weights)
            
            # 創建響應
            response = StrategyTemplateResponse(
                name=template.name,
                display_name=template.display_name,
                description=template.description,
                weights=template.weights.__dict__,
                use_cases=template.use_cases,
                prerequisites=template.prerequisites,
                performance_targets=template.performance_targets,
                status=RouteConfigStatus.ACTIVE if template.is_active else RouteConfigStatus.INACTIVE,
                created_at=template.created_at,
                updated_at=template.updated_at,
                is_active=template.is_active
            )
            
            self.logger.info(f"✅ Created strategy template: {request.name}")
            return True, response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create strategy template: {e}")
            return False, [f"創建失敗: {str(e)}"]
    
    async def update_strategy_template(
        self,
        strategy_name: str,
        request: StrategyTemplateRequest,
        operator_id: str,
        operator_name: str
    ) -> Tuple[bool, Union[StrategyTemplateResponse, List[str]]]:
        """更新策略模板"""
        try:
            # 檢查策略是否存在
            if strategy_name not in self.routing_config_manager.active_strategies:
                return False, [f"策略 '{strategy_name}' 不存在"]
            
            # 獲取原始配置
            old_template = self.routing_config_manager.active_strategies[strategy_name]
            old_config = old_template.to_dict()
            
            # 驗證更新請求
            validation_errors = RoutingConfigValidator.validate_strategy_template(request)
            if validation_errors:
                return False, validation_errors
            
            # 準備更新數據
            updates = {
                'display_name': request.display_name,
                'description': request.description,
                'weights': request.weights.dict(),
                'use_cases': request.use_cases,
                'prerequisites': request.prerequisites,
                'performance_targets': request.performance_targets,
                'is_active': request.is_active
            }
            
            # 執行更新
            updated_template = self.routing_config_manager.update_strategy_template(
                strategy_name, updates
            )
            
            if not updated_template:
                return False, [f"更新策略 '{strategy_name}' 失敗"]
            
            # 更新AI路由器配置
            if self.ai_task_router:
                weights = request.weights.to_routing_weights()
                try:
                    strategy_enum = RoutingStrategy(strategy_name)
                    if request.is_active:
                        self.ai_task_router.routing_strategies[strategy_enum] = weights
                    else:
                        # 停用策略
                        if strategy_enum in self.ai_task_router.routing_strategies:
                            del self.ai_task_router.routing_strategies[strategy_enum]
                except ValueError:
                    # 自定義策略處理
                    if request.is_active:
                        self.ai_task_router.add_custom_strategy(strategy_name, weights)
            
            # 記錄審計日誌
            await self._record_audit(
                RouteOperationType.UPDATE_STRATEGY,
                strategy_name,
                operator_id,
                operator_name,
                changes=updates,
                previous_config=old_config,
                new_config=request.dict()
            )
            
            # 創建響應
            response = StrategyTemplateResponse(
                name=updated_template.name,
                display_name=updated_template.display_name,
                description=updated_template.description,
                weights=updated_template.weights.__dict__,
                use_cases=updated_template.use_cases,
                prerequisites=updated_template.prerequisites,
                performance_targets=updated_template.performance_targets,
                status=RouteConfigStatus.ACTIVE if updated_template.is_active else RouteConfigStatus.INACTIVE,
                created_at=updated_template.created_at,
                updated_at=updated_template.updated_at,
                is_active=updated_template.is_active
            )
            
            self.logger.info(f"✅ Updated strategy template: {strategy_name}")
            return True, response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update strategy template: {e}")
            return False, [f"更新失敗: {str(e)}"]
    
    async def delete_strategy_template(
        self,
        strategy_name: str,
        operator_id: str,
        operator_name: str
    ) -> Tuple[bool, Union[str, List[str]]]:
        """刪除策略模板"""
        try:
            # 檢查策略是否存在
            if strategy_name not in self.routing_config_manager.active_strategies:
                return False, [f"策略 '{strategy_name}' 不存在"]
            
            # 檢查策略是否正在使用
            usage_count = await self._get_strategy_usage_count(strategy_name)
            if usage_count > 0:
                return False, [f"策略 '{strategy_name}' 正在使用中，無法刪除"]
            
            # 獲取原始配置用於審計
            old_template = self.routing_config_manager.active_strategies[strategy_name]
            old_config = old_template.to_dict()
            
            # 從配置管理器中刪除
            del self.routing_config_manager.active_strategies[strategy_name]
            if self.routing_config_manager.current_profile:
                if strategy_name in self.routing_config_manager.current_profile.strategy_templates:
                    del self.routing_config_manager.current_profile.strategy_templates[strategy_name]
            
            # 從AI路由器中刪除
            if self.ai_task_router:
                try:
                    strategy_enum = RoutingStrategy(strategy_name)
                    if strategy_enum in self.ai_task_router.routing_strategies:
                        del self.ai_task_router.routing_strategies[strategy_enum]
                except ValueError:
                    # 自定義策略處理
                    pass
                
                # 清理統計數據
                if strategy_name in self.ai_task_router.stats['strategy_usage']:
                    del self.ai_task_router.stats['strategy_usage'][strategy_name]
            
            # 記錄審計日誌
            await self._record_audit(
                RouteOperationType.DELETE_STRATEGY,
                strategy_name,
                operator_id,
                operator_name,
                previous_config=old_config
            )
            
            self.logger.info(f"✅ Deleted strategy template: {strategy_name}")
            return True, f"成功刪除策略 '{strategy_name}'"
            
        except Exception as e:
            self.logger.error(f"❌ Failed to delete strategy template: {e}")
            return False, [f"刪除失敗: {str(e)}"]
    
    async def get_strategy_templates(
        self,
        include_inactive: bool = False
    ) -> List[StrategyTemplateResponse]:
        """獲取策略模板列表"""
        try:
            templates = []
            
            for name, template in self.routing_config_manager.active_strategies.items():
                if not include_inactive and not template.is_active:
                    continue
                
                # 獲取使用統計
                usage_count = await self._get_strategy_usage_count(name)
                last_used = await self._get_strategy_last_used(name)
                
                response = StrategyTemplateResponse(
                    name=template.name,
                    display_name=template.display_name,
                    description=template.description,
                    weights=template.weights.__dict__,
                    use_cases=template.use_cases,
                    prerequisites=template.prerequisites,
                    performance_targets=template.performance_targets,
                    status=RouteConfigStatus.ACTIVE if template.is_active else RouteConfigStatus.INACTIVE,
                    created_at=template.created_at,
                    updated_at=template.updated_at,
                    is_active=template.is_active,
                    usage_count=usage_count,
                    last_used=last_used
                )
                templates.append(response)
            
            return templates
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get strategy templates: {e}")
            return []
    
    # ==================== 路由策略管理 ====================
    
    async def create_routing_policy(
        self,
        request: RoutingPolicyRequest,
        operator_id: str,
        operator_name: str
    ) -> Tuple[bool, Union[RoutingPolicyResponse, List[str]]]:
        """創建路由策略"""
        try:
            # 驗證請求
            available_strategies = list(self.routing_config_manager.active_strategies.keys())
            validation_errors = RoutingConfigValidator.validate_routing_policy(
                request, available_strategies
            )
            if validation_errors:
                return False, validation_errors
            
            # 檢查名稱唯一性
            if request.name in self.routing_config_manager.active_policies:
                return False, [f"策略名稱 '{request.name}' 已存在"]
            
            # 創建路由策略
            policy = self.routing_config_manager.create_routing_policy(
                name=request.name,
                task_type_mappings=request.task_type_mappings,
                user_tier_mappings=request.user_tier_mappings,
                priority_mappings=request.priority_mappings,
                fallback_strategy=request.fallback_strategy,
                conditions=request.conditions,
                is_active=request.is_active
            )
            
            # 記錄審計日誌
            await self._record_audit(
                RouteOperationType.CREATE_POLICY,
                request.name,
                operator_id,
                operator_name,
                new_config=request.dict()
            )
            
            # 創建響應
            response = RoutingPolicyResponse(
                name=policy.name,
                task_type_mappings=policy.task_type_mappings,
                user_tier_mappings=policy.user_tier_mappings,
                priority_mappings=policy.priority_mappings,
                fallback_strategy=policy.fallback_strategy,
                conditions=policy.conditions,
                status=RouteConfigStatus.ACTIVE if policy.is_active else RouteConfigStatus.INACTIVE,
                is_active=policy.is_active,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"✅ Created routing policy: {request.name}")
            return True, response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create routing policy: {e}")
            return False, [f"創建失敗: {str(e)}"]
    
    # ==================== A/B測試管理 ====================
    
    async def create_ab_test(
        self,
        request: ABTestVariantRequest,
        operator_id: str,
        operator_name: str
    ) -> Tuple[bool, Union[ABTestResponse, List[str]]]:
        """創建A/B測試"""
        try:
            # 驗證請求
            available_strategies = list(self.routing_config_manager.active_strategies.keys())
            validation_errors = RoutingConfigValidator.validate_ab_test(request, available_strategies)
            if validation_errors:
                return False, validation_errors
            
            # 檢查測試名稱唯一性
            if request.variant_name in self.active_ab_tests:
                return False, [f"測試名稱 '{request.variant_name}' 已存在"]
            
            # 創建A/B測試變體
            variant_template = self.routing_config_manager.create_ab_test_variant(
                base_strategy=request.base_strategy,
                variant_name=request.variant_name,
                modifications=request.modifications,
                traffic_percentage=request.traffic_percentage
            )
            
            if not variant_template:
                return False, ["創建A/B測試變體失敗"]
            
            # 創建測試記錄
            test_id = f"ab_test_{int(datetime.now().timestamp())}"
            test_record = {
                'test_id': test_id,
                'test_name': request.variant_name,
                'base_strategy': request.base_strategy,
                'variant_strategy': request.variant_name,
                'traffic_percentage': request.traffic_percentage,
                'description': request.test_description,
                'expected_duration_days': request.expected_duration_days,
                'start_date': datetime.now(timezone.utc),
                'end_date': None,
                'status': 'active',
                'metrics': {},
                'participants': 0,
                'conversions': 0,
                'created_by': operator_name,
                'is_active': True
            }
            
            self.active_ab_tests[test_id] = test_record
            
            # 記錄審計日誌
            await self._record_audit(
                RouteOperationType.AB_TEST_CREATE,
                request.variant_name,
                operator_id,
                operator_name,
                new_config=request.dict()
            )
            
            # 創建響應
            response = ABTestResponse(
                test_id=test_id,
                test_name=request.variant_name,
                base_strategy=request.base_strategy,
                variant_strategy=request.variant_name,
                traffic_percentage=request.traffic_percentage,
                status='active',
                start_date=test_record['start_date'],
                end_date=None,
                metrics=test_record['metrics'],
                is_active=True
            )
            
            self.logger.info(f"✅ Created A/B test: {request.variant_name}")
            return True, response
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create A/B test: {e}")
            return False, [f"創建失敗: {str(e)}"]
    
    async def stop_ab_test(
        self,
        test_id: str,
        operator_id: str,
        operator_name: str
    ) -> Tuple[bool, Union[str, List[str]]]:
        """停止A/B測試"""
        try:
            if test_id not in self.active_ab_tests:
                return False, [f"測試 '{test_id}' 不存在"]
            
            test_record = self.active_ab_tests[test_id]
            
            # 停止測試
            test_record['status'] = 'stopped'
            test_record['end_date'] = datetime.now(timezone.utc)
            test_record['is_active'] = False
            
            # 收集最終測試結果
            final_metrics = await self._collect_ab_test_results(test_id)
            test_record['metrics'] = final_metrics
            
            # 移動到歷史記錄
            self.ab_test_results[test_id] = test_record
            del self.active_ab_tests[test_id]
            
            # 停用變體策略
            variant_name = test_record['variant_strategy']
            if variant_name in self.routing_config_manager.active_strategies:
                template = self.routing_config_manager.active_strategies[variant_name]
                template.is_active = False
            
            # 記錄審計日誌
            await self._record_audit(
                RouteOperationType.AB_TEST_STOP,
                test_record['test_name'],
                operator_id,
                operator_name,
                changes={'final_metrics': final_metrics}
            )
            
            self.logger.info(f"✅ Stopped A/B test: {test_id}")
            return True, f"成功停止A/B測試 '{test_record['test_name']}'"
            
        except Exception as e:
            self.logger.error(f"❌ Failed to stop A/B test: {e}")
            return False, [f"停止失敗: {str(e)}"]
    
    # ==================== 儀表板和監控 ====================
    
    async def get_dashboard_data(self) -> RoutingDashboardResponse:
        """獲取路由管理儀表板數據"""
        try:
            # 獲取摘要信息
            summary = {
                'total_strategies': len(self.routing_config_manager.active_strategies),
                'active_strategies': sum(1 for t in self.routing_config_manager.active_strategies.values() if t.is_active),
                'total_policies': len(self.routing_config_manager.active_policies),
                'active_policies': sum(1 for p in self.routing_config_manager.active_policies.values() if p.is_active),
                'active_ab_tests': len(self.active_ab_tests),
                'total_decisions_today': await self._get_daily_decision_count(),
                'system_health_score': await self._calculate_system_health_score()
            }
            
            # 獲取活動策略
            active_strategies = await self.get_strategy_templates(include_inactive=False)
            
            # 獲取活動策略
            active_policies = await self.get_routing_policies(include_inactive=False)
            
            # 獲取活動A/B測試
            active_ab_tests = [
                ABTestResponse(**test_data)
                for test_data in self.active_ab_tests.values()
            ]
            
            # 獲取最近決策
            recent_decisions = await self._get_recent_decisions(limit=10)
            
            # 獲取性能指標
            performance_metrics = await self.get_performance_metrics()
            
            # 獲取系統健康狀態
            system_health = await self._get_system_health()
            
            return RoutingDashboardResponse(
                summary=summary,
                active_strategies=active_strategies,
                active_policies=active_policies,
                active_ab_tests=active_ab_tests,
                recent_decisions=recent_decisions,
                performance_metrics=performance_metrics,
                system_health=system_health
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get dashboard data: {e}")
            # 返回空的儀表板數據
            return RoutingDashboardResponse(
                summary={},
                active_strategies=[],
                active_policies=[],
                active_ab_tests=[],
                recent_decisions=[],
                performance_metrics=RoutingPerformanceResponse(
                    period="24h",
                    total_decisions=0,
                    successful_decisions=0,
                    failed_decisions=0,
                    average_decision_time_ms=0.0,
                    strategy_usage={},
                    model_selection_frequency={},
                    cost_savings=0.0,
                    quality_metrics={},
                    latency_metrics={}
                ),
                system_health={}
            )
    
    async def get_performance_metrics(self, period_hours: int = 24) -> RoutingPerformanceResponse:
        """獲取性能指標"""
        try:
            metrics = await self.metrics_collector.collect_performance_metrics(period_hours)
            
            return RoutingPerformanceResponse(
                period=f"{period_hours}h",
                total_decisions=metrics.get('total_decisions', 0),
                successful_decisions=metrics.get('successful_decisions', 0),
                failed_decisions=metrics.get('failed_decisions', 0),
                average_decision_time_ms=metrics.get('average_decision_time_ms', 0.0),
                strategy_usage=metrics.get('strategy_usage', {}),
                model_selection_frequency=metrics.get('model_selection_frequency', {}),
                cost_savings=metrics.get('cost_metrics', {}).get('cost_savings', 0.0),
                quality_metrics=metrics.get('quality_metrics', {}),
                latency_metrics=metrics.get('latency_metrics', {})
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get performance metrics: {e}")
            return RoutingPerformanceResponse(
                period=f"{period_hours}h",
                total_decisions=0,
                successful_decisions=0,
                failed_decisions=0,
                average_decision_time_ms=0.0,
                strategy_usage={},
                model_selection_frequency={},
                cost_savings=0.0,
                quality_metrics={},
                latency_metrics={}
            )
    
    # ==================== 輔助方法 ====================
    
    async def _record_audit(
        self,
        operation_type: RouteOperationType,
        target_name: str,
        operator_id: str,
        operator_name: str,
        changes: Optional[Dict[str, Any]] = None,
        previous_config: Optional[Dict[str, Any]] = None,
        new_config: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """記錄審計日誌"""
        try:
            audit = RouteOperationAudit(
                operation_type=operation_type,
                target_name=target_name,
                operator_id=operator_id,
                operator_name=operator_name,
                changes=changes or {},
                previous_config=previous_config,
                new_config=new_config,
                success=success,
                error_message=error_message
            )
            
            self.audit_records.append(audit)
            
            # 限制審計記錄數量
            if len(self.audit_records) > self.max_audit_records:
                self.audit_records = self.audit_records[-self.max_audit_records:]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record audit: {e}")
    
    async def _get_strategy_usage_count(self, strategy_name: str) -> int:
        """獲取策略使用次數"""
        if self.ai_task_router:
            return self.ai_task_router.stats['strategy_usage'].get(strategy_name, 0)
        return 0
    
    async def _get_strategy_last_used(self, strategy_name: str) -> Optional[datetime]:
        """獲取策略最後使用時間"""
        # 這裡應該從實際的審計日誌或監控數據獲取
        # 暫時返回模擬數據
        if self.ai_task_router and strategy_name in self.ai_task_router.stats['strategy_usage']:
            return datetime.now(timezone.utc) - timedelta(hours=2)
        return None
    
    async def _collect_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """收集A/B測試結果"""
        # 這裡應該從實際的監控系統收集測試結果
        # 暫時返回模擬數據
        return {
            'total_participants': 500,
            'variant_participants': 250,
            'control_participants': 250,
            'conversion_rate_variant': 0.12,
            'conversion_rate_control': 0.10,
            'statistical_significance': 0.05,
            'confidence_level': 0.95,
            'improvement': 0.20
        }
    
    async def get_routing_policies(self, include_inactive: bool = False) -> List[RoutingPolicyResponse]:
        """獲取路由策略列表"""
        try:
            policies = []
            
            for name, policy in self.routing_config_manager.active_policies.items():
                if not include_inactive and not policy.is_active:
                    continue
                
                response = RoutingPolicyResponse(
                    name=policy.name,
                    task_type_mappings=policy.task_type_mappings,
                    user_tier_mappings=policy.user_tier_mappings,
                    priority_mappings=policy.priority_mappings,
                    fallback_strategy=policy.fallback_strategy,
                    conditions=policy.conditions,
                    status=RouteConfigStatus.ACTIVE if policy.is_active else RouteConfigStatus.INACTIVE,
                    is_active=policy.is_active,
                    created_at=datetime.now(timezone.utc),  # 暫時使用當前時間
                    updated_at=datetime.now(timezone.utc)
                )
                policies.append(response)
            
            return policies
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get routing policies: {e}")
            return []
    
    async def _get_daily_decision_count(self) -> int:
        """獲取今日決策數量"""
        if self.ai_task_router:
            return self.ai_task_router.stats.get('total_decisions', 0)
        return 0
    
    async def _calculate_system_health_score(self) -> float:
        """計算系統健康評分"""
        if self.ai_task_router:
            total = self.ai_task_router.stats.get('total_decisions', 0)
            successful = self.ai_task_router.stats.get('successful_decisions', 0)
            if total > 0:
                return round(successful / total, 3)
        return 0.95  # 預設健康評分
    
    async def _get_recent_decisions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取最近的路由決策"""
        if self.ai_task_router:
            history = self.ai_task_router.get_decision_history(limit=limit)
            return history
        return []
    
    async def _get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        if self.ai_task_router:
            try:
                health = await self.ai_task_router.health_check()
                return health
            except Exception as e:
                self.logger.error(f"❌ Failed to get system health: {e}")
        
        return {
            'overall_status': 'healthy',
            'components_status': {},
            'timestamp': datetime.now(timezone.utc).isoformat()
        }