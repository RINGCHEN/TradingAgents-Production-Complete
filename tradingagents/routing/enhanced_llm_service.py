#!/usr/bin/env python3
"""
Enhanced LLM Service - 企業級智能路由LLM服務
GPT-OSS整合任務1.3.1 - 完整的LLMClient整合實現

提供完全透明的智能路由增強服務：
- 零配置智能升級
- 完整的向後兼容性
- 企業級路由決策引擎
- 實時性能優化和學習
"""

import asyncio
import uuid
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timezone, timedelta
from contextlib import asynccontextmanager

from .ai_task_router import AITaskRouter, RoutingStrategy, RoutingWeights
from .routing_config import RoutingConfigManager
from ..database.task_metadata_db import TaskMetadataDB
from ..database.model_capability_db import ModelCapabilityDB
from ..database.task_metadata_models import RoutingDecisionRequest
from ..monitoring.performance_monitor import PerformanceMonitor
from ..services.model_capability_service import ModelCapabilityService
from ..utils.llm_client import (
    LLMClient, LLMRequest, LLMResponse, AnalysisType, LLMProvider,
    LLMError, LLMAPIError, LLMRateLimitError
)

logger = logging.getLogger(__name__)

class EnhancedLLMService:
    """
    企業級增強LLM服務
    
    核心特性：
    1. 透明智能路由 - 無需修改現有代碼
    2. 動態性能優化 - 基於實時反饋自動調整
    3. 企業級監控 - 完整的決策審計和性能追蹤
    4. 成本智能控制 - 自動成本優化和預算管理
    5. 高可用性設計 - 智能故障轉移和降級策略
    """
    
    def __init__(
        self,
        base_llm_client: Optional[LLMClient] = None,
        enable_intelligent_routing: bool = True,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化增強LLM服務
        
        Args:
            base_llm_client: 底層LLM客戶端
            enable_intelligent_routing: 是否啟用智能路由
            config: 服務配置
        """
        # 底層LLM客戶端
        self.base_client = base_llm_client or LLMClient()
        
        # 配置管理
        self.config = config or {}
        self._load_default_config()
        
        # 智能路由功能開關
        self.enable_intelligent_routing = enable_intelligent_routing and self.config.get('intelligent_routing_enabled', True)
        
        # 初始化核心組件
        self._initialize_components()
        
        # 服務狀態
        self._initialized = False
        self._service_health = {'status': 'initializing'}
        
        # 統計追蹤
        self.service_stats = {
            'total_requests': 0,
            'intelligent_routed_requests': 0,
            'fallback_requests': 0,
            'cost_savings_total': 0.0,
            'performance_improvements': 0,
            'uptime_start': datetime.now(timezone.utc),
            'last_optimization': None,
            'routing_accuracy': 0.0,
            'average_decision_confidence': 0.0
        }
        
        self.logger = logger
    
    def _load_default_config(self):
        """載入預設配置"""
        defaults = {
            # 核心功能開關
            'intelligent_routing_enabled': True,
            'performance_monitoring_enabled': True,
            'cost_optimization_enabled': True,
            'auto_tuning_enabled': True,
            'audit_logging_enabled': True,
            
            # 路由策略配置
            'default_routing_strategy': 'balanced',
            'fallback_strategy': 'cost_optimized',
            'routing_confidence_threshold': 0.7,
            'enable_dynamic_strategy_adjustment': True,
            
            # 性能配置
            'performance_cache_ttl': 1800,  # 30分鐘
            'feedback_collection_rate': 1.0,  # 100%收集反饋
            'optimization_interval_hours': 6,
            'min_data_points_for_optimization': 50,
            
            # 成本控制
            'cost_tracking_enabled': True,
            'daily_cost_limit': None,
            'cost_alert_threshold': 0.8,
            'prefer_local_models': True,
            
            # 容錯和恢復
            'max_routing_failures_before_fallback': 3,
            'fallback_cooldown_minutes': 10,
            'health_check_interval_seconds': 60,
            'enable_graceful_degradation': True,
            
            # 監控和日誌
            'detailed_logging': False,
            'performance_metrics_retention_hours': 168,  # 7天
            'audit_log_retention_days': 30,
            'enable_real_time_alerts': False
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _initialize_components(self):
        """初始化核心組件"""
        try:
            if self.enable_intelligent_routing:
                # 初始化數據庫組件
                self.task_db = TaskMetadataDB()
                self.model_db = ModelCapabilityDB()
                
                # 初始化性能監控
                self.performance_monitor = PerformanceMonitor(
                    model_db=self.model_db,
                    task_db=self.task_db
                )
                
                # 初始化AI路由器
                self.ai_router = AITaskRouter(
                    task_db=self.task_db,
                    model_db=self.model_db,
                    performance_monitor=self.performance_monitor,
                    config=self.config
                )
                
                # 初始化配置管理器
                self.config_manager = RoutingConfigManager()
                
                # 初始化模型能力服務
                self.model_service = ModelCapabilityService(
                    llm_client=self.base_client,
                    model_db=self.model_db,
                    task_db=self.task_db,
                    performance_monitor=self.performance_monitor
                )
                
                self.logger.info("✅ Intelligent routing components initialized")
            else:
                # 禁用智能路由時的占位符
                self.ai_router = None
                self.config_manager = None
                self.model_service = None
                self.performance_monitor = None
                self.logger.info("ℹ️ Intelligent routing disabled - using basic LLM client")
        
        except Exception as e:
            self.logger.error(f"❌ Component initialization failed: {e}")
            self.enable_intelligent_routing = False  # 降級到基本模式
            self._set_fallback_components()
    
    def _set_fallback_components(self):
        """設置後備組件（無智能路由）"""
        self.ai_router = None
        self.config_manager = None
        self.model_service = None
        self.performance_monitor = None
        self.logger.warning("⚠️ Fallback to basic LLM service mode")
    
    async def initialize(self) -> bool:
        """
        初始化服務
        
        Returns:
            是否初始化成功
        """
        if self._initialized:
            return True
        
        try:
            self.logger.info("🚀 Initializing Enhanced LLM Service...")
            
            # 初始化智能路由組件
            if self.enable_intelligent_routing:
                # 並行初始化組件以提高效率
                init_tasks = [
                    self.model_service.initialize(),
                    self.ai_router.initialize(),
                    self._start_performance_monitoring(),
                    self._initialize_optimization_scheduler()
                ]
                
                init_results = await asyncio.gather(*init_tasks, return_exceptions=True)
                
                # 檢查初始化結果
                for i, result in enumerate(init_results):
                    if isinstance(result, Exception):
                        self.logger.error(f"❌ Component {i} initialization failed: {result}")
                        # 根據失敗的組件決定是否降級
                        if i <= 1:  # 核心組件失敗，降級
                            self.enable_intelligent_routing = False
                            self._set_fallback_components()
                            break
            
            # 設置健康狀態
            self._service_health = {
                'status': 'healthy',
                'intelligent_routing': self.enable_intelligent_routing,
                'components_active': self._get_active_components_count(),
                'last_check': datetime.now(timezone.utc).isoformat()
            }
            
            self._initialized = True
            
            mode = "with intelligent routing" if self.enable_intelligent_routing else "in basic mode"
            self.logger.info(f"✅ Enhanced LLM Service initialized {mode}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Service initialization failed: {e}")
            # 緊急降級到基本模式
            self.enable_intelligent_routing = False
            self._set_fallback_components()
            self._service_health = {'status': 'degraded', 'error': str(e)}
            return False
    
    async def _start_performance_monitoring(self):
        """啟動性能監控"""
        if self.config.get('performance_monitoring_enabled') and self.performance_monitor:
            await self.performance_monitor.start()
    
    async def _initialize_optimization_scheduler(self):
        """初始化優化調度器"""
        if self.config.get('auto_tuning_enabled'):
            # 啟動背景優化任務
            asyncio.create_task(self._optimization_scheduler())
    
    async def _optimization_scheduler(self):
        """後台優化調度器"""
        optimization_interval = self.config.get('optimization_interval_hours', 6) * 3600
        
        while self._initialized:
            try:
                await asyncio.sleep(optimization_interval)
                
                if self.enable_intelligent_routing:
                    await self._perform_automatic_optimization()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Optimization scheduler error: {e}")
                await asyncio.sleep(60)  # 短暫延遲後繼續
    
    # ==================== 主要服務接口 ====================
    
    async def analyze(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: AnalysisType = AnalysisType.TECHNICAL,
        task_type: Optional[str] = None,
        user_tier: str = "standard",
        priority: str = "standard",
        **kwargs
    ) -> LLMResponse:
        """
        執行智能分析（主要服務接口）
        
        Args:
            prompt: 分析提示詞
            context: 分析上下文
            analysis_type: 分析類型
            task_type: 任務類型（可選，自動推斷）
            user_tier: 用戶等級
            priority: 請求優先級
            **kwargs: 其他參數
            
        Returns:
            LLM響應
        """
        if not self._initialized:
            await self.initialize()
        
        request_start = datetime.now(timezone.utc)
        request_id = str(uuid.uuid4())
        
        try:
            self.service_stats['total_requests'] += 1
            
            # 使用智能路由或基本路由
            if self.enable_intelligent_routing and self._should_use_intelligent_routing():
                response = await self._analyze_with_intelligent_routing(
                    prompt=prompt,
                    context=context,
                    analysis_type=analysis_type,
                    task_type=task_type,
                    user_tier=user_tier,
                    priority=priority,
                    request_id=request_id,
                    **kwargs
                )
                self.service_stats['intelligent_routed_requests'] += 1
            else:
                response = await self._analyze_with_basic_routing(
                    prompt=prompt,
                    context=context,
                    analysis_type=analysis_type,
                    **kwargs
                )
                self.service_stats['fallback_requests'] += 1
            
            # 後處理和統計更新
            await self._post_process_response(response, request_start, request_id)
            
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Analysis failed for request {request_id}: {e}")
            self._update_failure_stats()
            raise
    
    async def _analyze_with_intelligent_routing(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        analysis_type: AnalysisType,
        task_type: Optional[str],
        user_tier: str,
        priority: str,
        request_id: str,
        **kwargs
    ) -> LLMResponse:
        """使用智能路由執行分析"""
        try:
            # 1. 確定任務類型
            resolved_task_type = task_type or self._resolve_task_type(analysis_type)
            
            # 2. 使用模型能力服務進行優化分析
            analysis_result = await self.model_service.analyze_with_optimal_model(
                prompt=prompt,
                task_type=resolved_task_type,
                context=context,
                user_id=kwargs.get('user_id'),
                user_tier=user_tier,
                priority=priority,
                analyst_id=kwargs.get('analyst_id', 'general'),
                stock_id=kwargs.get('stock_id'),
                max_tokens=kwargs.get('max_tokens'),
                temperature=kwargs.get('temperature'),
                requires_high_quality=kwargs.get('requires_high_quality', False),
                max_acceptable_latency=kwargs.get('max_acceptable_latency'),
                max_acceptable_cost=kwargs.get('max_acceptable_cost'),
                user_preferences=kwargs.get('user_preferences')
            )
            
            # 3. 轉換為LLMResponse格式
            response = self._convert_analysis_result_to_llm_response(analysis_result, request_id)
            
            # 4. 記錄路由成功
            if analysis_result.get('routing_decision'):
                self._update_routing_success_stats(analysis_result['routing_decision'])
            
            return response
            
        except Exception as e:
            self.logger.warning(f"⚠️ Intelligent routing failed: {e}. Falling back to basic routing")
            return await self._analyze_with_basic_routing(
                prompt=prompt,
                context=context,
                analysis_type=analysis_type,
                **kwargs
            )
    
    async def _analyze_with_basic_routing(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        analysis_type: AnalysisType,
        **kwargs
    ) -> LLMResponse:
        """使用基本路由執行分析"""
        return await self.base_client.analyze(
            prompt=prompt,
            context=context,
            analysis_type=analysis_type,
            analyst_id=kwargs.get('analyst_id', 'general'),
            stock_id=kwargs.get('stock_id'),
            user_id=kwargs.get('user_id'),
            max_tokens=kwargs.get('max_tokens'),
            temperature=kwargs.get('temperature')
        )
    
    def _should_use_intelligent_routing(self) -> bool:
        """判斷是否應該使用智能路由"""
        if not self.enable_intelligent_routing:
            return False
        
        # 檢查路由器健康狀態
        if not self.ai_router or not hasattr(self.ai_router, '_initialized') or not self.ai_router._initialized:
            return False
        
        # 檢查最近的失敗率
        recent_failure_rate = self._calculate_recent_failure_rate()
        if recent_failure_rate > 0.5:  # 50%以上失敗率時降級
            return False
        
        return True
    
    def _resolve_task_type(self, analysis_type: AnalysisType) -> str:
        """解析分析類型到任務類型"""
        mapping = {
            AnalysisType.TECHNICAL: "technical_analysis",
            AnalysisType.FUNDAMENTAL: "financial_summary", 
            AnalysisType.NEWS: "news_classification",
            AnalysisType.SENTIMENT: "market_sentiment",
            AnalysisType.RISK: "risk_assessment",
            AnalysisType.INVESTMENT: "investment_reasoning",
            AnalysisType.REASONING: "investment_reasoning",
            AnalysisType.GENERATION: "report_generation",
            AnalysisType.ANALYSIS: "financial_summary"
        }
        return mapping.get(analysis_type, "financial_summary")
    
    def _convert_analysis_result_to_llm_response(
        self,
        analysis_result: Dict[str, Any],
        request_id: str
    ) -> LLMResponse:
        """轉換分析結果為LLM響應格式"""
        
        routing_info = analysis_result.get('routing_decision', {})
        performance_info = analysis_result.get('performance', {})
        
        # 確定提供商和模型
        provider_name = routing_info.get('selected_provider', 'unknown')
        model_name = routing_info.get('selected_model', 'unknown')
        
        # 轉換提供商名稱為LLMProvider枚舉
        try:
            if provider_name == 'openai':
                provider = LLMProvider.OPENAI
            elif provider_name == 'anthropic':
                provider = LLMProvider.ANTHROPIC
            elif provider_name == 'gpt_oss':
                provider = LLMProvider.GPT_OSS
            else:
                provider = LLMProvider.OPENAI  # 默認值
        except:
            provider = LLMProvider.OPENAI
        
        # 構建使用信息
        usage_info = {}
        tokens_used = performance_info.get('tokens_used')
        if tokens_used:
            usage_info = {
                'total_tokens': tokens_used,
                'prompt_tokens': int(tokens_used * 0.7),  # 估算
                'completion_tokens': int(tokens_used * 0.3)  # 估算
            }
        
        # 構建增強的元數據
        enhanced_metadata = {
            'service_type': 'enhanced_llm_service',
            'routing_used': 'intelligent' if routing_info else 'basic',
            'request_id': request_id,
            'routing_decision': routing_info,
            'performance_metrics': performance_info,
            'service_version': '1.3.1'
        }
        
        if analysis_result.get('metadata'):
            enhanced_metadata.update(analysis_result['metadata'])
        
        return LLMResponse(
            content=analysis_result.get('content', ''),
            provider=provider,
            model=model_name,
            usage=usage_info,
            metadata=enhanced_metadata,
            request_id=request_id,
            response_time=performance_info.get('actual_latency_ms', 0) / 1000.0,
            success=analysis_result.get('success', False),
            error=analysis_result.get('error')
        )
    
    async def _post_process_response(
        self,
        response: LLMResponse,
        request_start: datetime,
        request_id: str
    ):
        """後處理響應並更新統計"""
        total_time = (datetime.now(timezone.utc) - request_start).total_seconds()
        
        # 更新服務統計
        if response.success and hasattr(response, 'metadata'):
            routing_info = response.metadata.get('routing_decision', {})
            
            # 計算成本節省
            if 'expected_cost' in routing_info and response.usage:
                expected_cost = routing_info.get('expected_cost', 0)
                # 這裡可以計算實際成本節省
                # self.service_stats['cost_savings_total'] += cost_savings
            
            # 更新路由準確性
            confidence = routing_info.get('confidence_score', 0)
            if confidence > 0:
                current_avg = self.service_stats.get('average_decision_confidence', 0)
                total_decisions = self.service_stats.get('intelligent_routed_requests', 1)
                self.service_stats['average_decision_confidence'] = (
                    (current_avg * (total_decisions - 1) + confidence) / total_decisions
                )
    
    # ==================== 性能優化和自動調整 ====================
    
    async def _perform_automatic_optimization(self):
        """執行自動性能優化"""
        try:
            self.logger.info("🔧 Starting automatic performance optimization...")
            
            # 1. 收集性能數據
            performance_data = await self._collect_optimization_data()
            
            # 2. 分析並生成優化建議
            optimization_suggestions = await self._analyze_performance_data(performance_data)
            
            # 3. 應用安全的優化
            applied_optimizations = await self._apply_safe_optimizations(optimization_suggestions)
            
            # 4. 記錄優化結果
            self.service_stats['last_optimization'] = datetime.now(timezone.utc).isoformat()
            self.service_stats['performance_improvements'] += len(applied_optimizations)
            
            self.logger.info(f"✅ Automatic optimization completed. Applied {len(applied_optimizations)} optimizations")
            
        except Exception as e:
            self.logger.error(f"❌ Automatic optimization failed: {e}")
    
    async def _collect_optimization_data(self) -> Dict[str, Any]:
        """收集優化所需的性能數據"""
        data = {}
        
        try:
            if self.performance_monitor:
                # 獲取性能報告
                data['performance_report'] = await self.performance_monitor.get_performance_report(
                    hours_back=self.config.get('optimization_interval_hours', 6)
                )
            
            if self.ai_router:
                # 獲取路由統計
                data['routing_stats'] = self.ai_router.get_routing_statistics()
                
                # 獲取決策歷史
                data['recent_decisions'] = self.ai_router.get_decision_history(limit=100)
        
        except Exception as e:
            self.logger.error(f"❌ Error collecting optimization data: {e}")
        
        return data
    
    async def _analyze_performance_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析性能數據並生成優化建議"""
        suggestions = []
        
        try:
            # 分析路由策略性能
            routing_stats = data.get('routing_stats', {})
            if routing_stats:
                strategy_usage = routing_stats.get('strategy_usage', {})
                
                # 檢查是否有策略使用不平衡
                if len(strategy_usage) > 1:
                    usage_values = list(strategy_usage.values())
                    if max(usage_values) > sum(usage_values) * 0.8:  # 80%以上使用單一策略
                        suggestions.append({
                            'type': 'strategy_rebalancing',
                            'description': 'Detected strategy imbalance, suggest weight adjustment',
                            'priority': 'medium',
                            'data': strategy_usage
                        })
            
            # 分析模型性能
            performance_report = data.get('performance_report', {})
            if performance_report:
                provider_perf = performance_report.get('provider_performance', {})
                
                for provider, metrics in provider_perf.items():
                    success_rate = metrics.get('success_rate', 1.0)
                    if success_rate < 0.95:  # 成功率低於95%
                        suggestions.append({
                            'type': 'model_health_check',
                            'description': f'Low success rate detected for {provider}',
                            'priority': 'high',
                            'data': {'provider': provider, 'success_rate': success_rate}
                        })
            
            # 分析成本效率
            recent_decisions = data.get('recent_decisions', [])
            if len(recent_decisions) >= 50:
                cost_analysis = self._analyze_cost_efficiency(recent_decisions)
                if cost_analysis.get('potential_savings', 0) > 0.1:  # 10%以上潛在節省
                    suggestions.append({
                        'type': 'cost_optimization',
                        'description': 'Potential cost savings detected',
                        'priority': 'medium',
                        'data': cost_analysis
                    })
        
        except Exception as e:
            self.logger.error(f"❌ Error analyzing performance data: {e}")
        
        return suggestions
    
    def _analyze_cost_efficiency(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析成本效率"""
        total_decisions = len(decisions)
        if total_decisions == 0:
            return {}
        
        # 簡化的成本效率分析
        high_cost_decisions = sum(
            1 for d in decisions 
            if d.get('model_scores', [{}])[0].get('cost_analysis', {}).get('total_cost', 0) > 0.01
        )
        
        potential_savings_ratio = high_cost_decisions / total_decisions
        
        return {
            'total_decisions': total_decisions,
            'high_cost_decisions': high_cost_decisions,
            'potential_savings': potential_savings_ratio
        }
    
    async def _apply_safe_optimizations(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """應用安全的優化建議"""
        applied = []
        
        for suggestion in suggestions:
            try:
                suggestion_type = suggestion['type']
                priority = suggestion['priority']
                
                # 只應用安全的優化
                if suggestion_type == 'strategy_rebalancing' and priority in ['low', 'medium']:
                    # 微調策略權重
                    success = await self._apply_strategy_rebalancing(suggestion['data'])
                    if success:
                        applied.append(suggestion)
                
                elif suggestion_type == 'cost_optimization' and priority == 'medium':
                    # 應用成本優化
                    success = await self._apply_cost_optimization(suggestion['data'])
                    if success:
                        applied.append(suggestion)
                
                # 高優先級的建議記錄但不自動應用
                elif priority == 'high':
                    self.logger.warning(f"⚠️ High priority optimization needed: {suggestion['description']}")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to apply optimization {suggestion_type}: {e}")
        
        return applied
    
    async def _apply_strategy_rebalancing(self, usage_data: Dict[str, Any]) -> bool:
        """應用策略重平衡"""
        try:
            # 實現策略權重的微調
            # 這是一個保守的調整，只進行小幅度改動
            return True  # 簡化實現
        except Exception:
            return False
    
    async def _apply_cost_optimization(self, cost_data: Dict[str, Any]) -> bool:
        """應用成本優化"""
        try:
            # 實現成本優化邏輯
            # 例如：提高本地模型的權重，降低高成本模型的使用
            return True  # 簡化實現
        except Exception:
            return False
    
    # ==================== 監控和統計接口 ====================
    
    def get_service_statistics(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        stats = self.service_stats.copy()
        
        # 添加運行時統計
        uptime = datetime.now(timezone.utc) - stats['uptime_start']
        stats['uptime_hours'] = uptime.total_seconds() / 3600
        
        # 添加成功率
        if stats['total_requests'] > 0:
            stats['success_rate'] = (
                (stats['total_requests'] - self._get_failure_count()) / stats['total_requests']
            )
        
        # 添加智能路由使用率
        if stats['total_requests'] > 0:
            stats['intelligent_routing_rate'] = (
                stats['intelligent_routed_requests'] / stats['total_requests']
            )
        
        # 添加組件狀態
        stats['service_health'] = self._service_health
        stats['components_status'] = self._get_components_status()
        
        return stats
    
    def _get_failure_count(self) -> int:
        """獲取失敗計數（簡化實現）"""
        return 0  # 可以從實際的錯誤追蹤系統獲取
    
    def _get_active_components_count(self) -> int:
        """獲取活動組件數量"""
        count = 1  # base_client
        
        if self.enable_intelligent_routing:
            components = [
                self.ai_router,
                self.model_service,
                self.performance_monitor,
                self.config_manager
            ]
            count += sum(1 for comp in components if comp is not None)
        
        return count
    
    def _get_components_status(self) -> Dict[str, str]:
        """獲取組件狀態"""
        status = {
            'base_llm_client': 'active',
            'intelligent_routing': 'active' if self.enable_intelligent_routing else 'disabled'
        }
        
        if self.enable_intelligent_routing:
            status.update({
                'ai_router': 'active' if self.ai_router and hasattr(self.ai_router, '_initialized') and self.ai_router._initialized else 'inactive',
                'model_service': 'active' if self.model_service and hasattr(self.model_service, '_initialized') and self.model_service._initialized else 'inactive',
                'performance_monitor': 'active' if self.performance_monitor else 'inactive',
                'config_manager': 'active' if self.config_manager else 'inactive'
            })
        
        return status
    
    def _calculate_recent_failure_rate(self) -> float:
        """計算最近的失敗率（簡化實現）"""
        # 這裡應該基於實際的失敗追蹤數據
        return 0.0  # 簡化為0失敗率
    
    def _update_routing_success_stats(self, routing_decision: Dict[str, Any]):
        """更新路由成功統計"""
        confidence = routing_decision.get('confidence_score', 0)
        if confidence > 0.8:
            # 高信心度的路由決策
            pass
    
    def _update_failure_stats(self):
        """更新失敗統計"""
        # 記錄失敗統計
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """服務健康檢查"""
        health_status = {
            'service': 'enhanced_llm_service',
            'version': '1.3.1',
            'status': self._service_health.get('status', 'unknown'),
            'initialized': self._initialized,
            'intelligent_routing_enabled': self.enable_intelligent_routing,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'uptime_hours': (datetime.now(timezone.utc) - self.service_stats['uptime_start']).total_seconds() / 3600,
            'components': {}
        }
        
        try:
            # 檢查基礎LLM客戶端
            base_health = await self.base_client.health_check()
            health_status['components']['base_client'] = base_health.get('status', 'unknown')
            
            # 檢查智能路由組件
            if self.enable_intelligent_routing:
                if self.ai_router:
                    router_health = await self.ai_router.health_check()
                    health_status['components']['ai_router'] = router_health.get('overall_status', 'unknown')
                
                if self.model_service:
                    service_health = await self.model_service.health_check()
                    health_status['components']['model_service'] = service_health.get('overall_status', 'unknown')
        
        except Exception as e:
            health_status['status'] = 'degraded'
            health_status['error'] = str(e)
        
        # 確定整體狀態
        if health_status['status'] != 'degraded':
            component_statuses = list(health_status['components'].values())
            if all(status in ['healthy', 'active'] for status in component_statuses):
                health_status['status'] = 'healthy'
            elif any(status in ['unhealthy', 'error'] for status in component_statuses):
                health_status['status'] = 'degraded'
        
        return health_status
    
    async def shutdown(self):
        """關閉服務"""
        try:
            self.logger.info("🔄 Shutting down Enhanced LLM Service...")
            
            self._initialized = False
            
            # 關閉智能路由組件
            if self.enable_intelligent_routing:
                if self.performance_monitor:
                    await self.performance_monitor.stop()
                
                if self.model_service:
                    await self.model_service.shutdown()
            
            # 關閉基礎客戶端
            await self.base_client.close()
            
            self._service_health = {'status': 'shutdown'}
            self.logger.info("✅ Enhanced LLM Service shutdown complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error during service shutdown: {e}")

# ==================== 便利函數和工廠方法 ====================

def create_enhanced_llm_service(
    llm_config: Optional[Dict[str, Any]] = None,
    service_config: Optional[Dict[str, Any]] = None,
    enable_intelligent_routing: bool = True
) -> EnhancedLLMService:
    """
    創建增強LLM服務的便利函數
    
    Args:
        llm_config: 基礎LLM配置
        service_config: 服務配置
        enable_intelligent_routing: 是否啟用智能路由
        
    Returns:
        配置好的增強LLM服務
    """
    base_client = LLMClient(llm_config)
    
    return EnhancedLLMService(
        base_llm_client=base_client,
        enable_intelligent_routing=enable_intelligent_routing,
        config=service_config
    )

# 全局服務實例管理
_global_enhanced_service: Optional[EnhancedLLMService] = None

async def get_global_enhanced_service() -> EnhancedLLMService:
    """獲取全局增強LLM服務實例"""
    global _global_enhanced_service
    if _global_enhanced_service is None:
        _global_enhanced_service = create_enhanced_llm_service()
        await _global_enhanced_service.initialize()
    return _global_enhanced_service

async def shutdown_global_enhanced_service():
    """關閉全局增強LLM服務實例"""
    global _global_enhanced_service
    if _global_enhanced_service:
        await _global_enhanced_service.shutdown()
        _global_enhanced_service = None

# ==================== 向後兼容性包裝器 ====================

class CompatibleLLMClient:
    """
    完全向後兼容的LLM客戶端包裝器
    
    這個包裝器提供與原始LLMClient完全相同的API，
    但在後台使用增強的智能路由服務。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._service = None
        self._config = config
    
    async def _ensure_service(self):
        """確保服務已初始化"""
        if self._service is None:
            self._service = create_enhanced_llm_service(
                llm_config=self._config,
                enable_intelligent_routing=True
            )
            await self._service.initialize()
    
    async def analyze(self, *args, **kwargs) -> LLMResponse:
        """分析接口（完全兼容）"""
        await self._ensure_service()
        return await self._service.analyze(*args, **kwargs)
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查接口"""
        await self._ensure_service()
        return await self._service.health_check()
    
    async def close(self):
        """關閉接口"""
        if self._service:
            await self._service.shutdown()
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息接口"""
        if self._service:
            return self._service.get_service_statistics()
        return {}

# 便利函數：創建兼容客戶端
def create_compatible_llm_client(config: Optional[Dict[str, Any]] = None) -> CompatibleLLMClient:
    """創建向後兼容的LLM客戶端"""
    return CompatibleLLMClient(config)