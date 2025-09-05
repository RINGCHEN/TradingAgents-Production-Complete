#!/usr/bin/env python3
"""
LLM Client Integration - 將AITaskRouter集成到現有LLMClient
GPT-OSS整合任務1.3.1 - 無縫升級集成

提供：
- LLMClient的AI路由增強版本
- 向後兼容的API
- 漸進式升級路徑
- 完整的企業級路由功能
"""

import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union

from .ai_task_router import (
    AITaskRouter, RoutingStrategy, RoutingWeights,
    AITaskRouterError, RoutingDecisionError
)
from .performance_feedback import PerformanceFeedbackSystem
from ..database.task_metadata_db import TaskMetadataDB
from ..database.model_capability_db import ModelCapabilityDB
from ..database.task_metadata_models import RoutingDecisionRequest
from ..monitoring.performance_monitor import PerformanceMonitor
from ..utils.llm_client import LLMClient, LLMRequest, LLMResponse, AnalysisType

logger = logging.getLogger(__name__)

class EnhancedLLMClient(LLMClient):
    """
    增強版LLM客戶端，集成AI任務智能路由功能
    
    保持與原始LLMClient完全兼容的同時，添加：
    - 智能路由決策
    - 性能反饋學習
    - 動態策略調整
    - 完整的決策審計
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        enable_ai_routing: bool = True,
        router_config: Optional[Dict[str, Any]] = None,
        feedback_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化增強版LLM客戶端
        
        Args:
            config: 基礎LLM配置
            enable_ai_routing: 是否啟用AI智能路由
            router_config: 路由器配置
            feedback_config: 反饋系統配置
        """
        # 初始化基礎LLMClient
        super().__init__(config)
        
        # AI路由功能配置
        self.enable_ai_routing = enable_ai_routing
        
        if self.enable_ai_routing:
            # 初始化路由組件
            self.task_db = TaskMetadataDB()
            self.model_db = ModelCapabilityDB()
            self.performance_monitor = PerformanceMonitor(
                model_db=self.model_db,
                task_db=self.task_db
            )
            
            # 創建AI路由器
            self.ai_router = AITaskRouter(
                task_db=self.task_db,
                model_db=self.model_db,
                performance_monitor=self.performance_monitor,
                config=router_config or {}
            )
            
            # 創建性能反饋系統
            self.feedback_system = PerformanceFeedbackSystem(
                config=feedback_config or {}
            )
            
            # 路由統計
            self.routing_stats = {
                'ai_routing_enabled': True,
                'total_ai_routed_requests': 0,
                'fallback_to_legacy_routing': 0,
                'performance_feedback_records': 0,
                'last_routing_decision': None
            }
        else:
            # 禁用AI路由時的佔位符
            self.ai_router = None
            self.feedback_system = None
            self.routing_stats = {
                'ai_routing_enabled': False,
                'note': 'AI routing disabled, using legacy routing only'
            }
        
        self._ai_routing_initialized = False
        self.logger = logger
    
    async def initialize_ai_routing(self) -> bool:
        """
        初始化AI路由功能
        
        Returns:
            是否初始化成功
        """
        if not self.enable_ai_routing:
            self.logger.info("ℹ️ AI routing disabled, using legacy routing")
            return True
        
        if self._ai_routing_initialized:
            return True
        
        try:
            self.logger.info("🚀 Initializing AI Task Router integration...")
            
            # 初始化各組件
            await self.ai_router.initialize()
            await self.feedback_system.initialize()
            await self.performance_monitor.start()
            
            self._ai_routing_initialized = True
            self.logger.info("✅ AI Task Router integration initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI routing: {e}")
            self.logger.info("📱 Falling back to legacy routing")
            return False
    
    async def analyze(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: AnalysisType = AnalysisType.TECHNICAL,
        analyst_id: str = "general",
        stock_id: Optional[str] = None,
        user_id: Optional[str] = None,
        # 新增的AI路由參數
        routing_strategy: Optional[RoutingStrategy] = None,
        custom_weights: Optional[RoutingWeights] = None,
        enable_feedback_collection: bool = True,
        user_tier: str = "standard",
        priority: str = "standard",
        **kwargs
    ) -> LLMResponse:
        """
        執行分析（增強版，支持AI智能路由）
        
        Args:
            prompt: 分析提示詞
            context: 分析上下文數據
            analysis_type: 分析類型
            analyst_id: 分析師ID
            stock_id: 股票代碼
            user_id: 用戶ID
            routing_strategy: 路由策略（AI路由）
            custom_weights: 自定義權重（AI路由）
            enable_feedback_collection: 是否收集性能反饋
            user_tier: 用戶等級
            priority: 請求優先級
            **kwargs: 其他參數
            
        Returns:
            LLM回應
        """
        # 確保AI路由已初始化
        if self.enable_ai_routing and not self._ai_routing_initialized:
            await self.initialize_ai_routing()
        
        # 使用AI路由或回退到傳統路由
        if self.enable_ai_routing and self._ai_routing_initialized:
            return await self._analyze_with_ai_routing(
                prompt=prompt,
                context=context,
                analysis_type=analysis_type,
                analyst_id=analyst_id,
                stock_id=stock_id,
                user_id=user_id,
                routing_strategy=routing_strategy,
                custom_weights=custom_weights,
                enable_feedback_collection=enable_feedback_collection,
                user_tier=user_tier,
                priority=priority,
                **kwargs
            )
        else:
            # 回退到傳統路由
            self.routing_stats['fallback_to_legacy_routing'] += 1
            return await super().analyze(
                prompt=prompt,
                context=context,
                analysis_type=analysis_type,
                analyst_id=analyst_id,
                stock_id=stock_id,
                user_id=user_id,
                **kwargs
            )
    
    async def _analyze_with_ai_routing(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        analysis_type: AnalysisType,
        analyst_id: str,
        stock_id: Optional[str],
        user_id: Optional[str],
        routing_strategy: Optional[RoutingStrategy],
        custom_weights: Optional[RoutingWeights],
        enable_feedback_collection: bool,
        user_tier: str,
        priority: str,
        **kwargs
    ) -> LLMResponse:
        """使用AI路由執行分析"""
        try:
            start_time = datetime.now(timezone.utc)
            
            # 1. 創建路由決策請求
            task_type = self._map_analysis_type_to_task_type(analysis_type)
            
            routing_request = RoutingDecisionRequest(
                task_type=task_type,
                user_tier=user_tier,
                estimated_tokens=self._estimate_tokens(prompt, context),
                priority=priority,
                requires_high_quality=kwargs.get('requires_high_quality', False),
                max_acceptable_latency=kwargs.get('max_acceptable_latency'),
                max_acceptable_cost=kwargs.get('max_acceptable_cost'),
                user_preferences=kwargs.get('user_preferences')
            )
            
            # 2. 執行智能路由決策
            routing_decision = await self.ai_router.make_routing_decision(
                request=routing_request,
                strategy=routing_strategy,
                custom_weights=custom_weights
            )
            
            self.routing_stats['total_ai_routed_requests'] += 1
            self.routing_stats['last_routing_decision'] = {
                'provider': routing_decision.selected_provider,
                'model': routing_decision.selected_model,
                'confidence': routing_decision.confidence_score,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(
                f"🎯 AI routing decision: {routing_decision.selected_provider}/"
                f"{routing_decision.selected_model} (confidence: {routing_decision.confidence_score:.3f})"
            )
            
            # 3. 強制使用路由決策選擇的提供商和模型
            original_provider = self.provider
            original_model = self.model
            
            try:
                # 臨時切換到路由選擇的提供商和模型
                self._temporarily_switch_provider(
                    routing_decision.selected_provider,
                    routing_decision.selected_model
                )
                
                # 4. 執行實際的LLM請求
                request = LLMRequest(
                    prompt=prompt,
                    context=context or {},
                    analysis_type=analysis_type,
                    analyst_id=analyst_id,
                    stock_id=stock_id,
                    user_id=user_id,
                    max_tokens=kwargs.get('max_tokens'),
                    temperature=kwargs.get('temperature')
                )
                
                response = await self._execute_request(request)
                
                # 5. 增強響應信息
                response.metadata = response.metadata or {}
                response.metadata.update({
                    'ai_routing_decision': {
                        'selected_provider': routing_decision.selected_provider,
                        'selected_model': routing_decision.selected_model,
                        'reasoning': routing_decision.reasoning,
                        'confidence_score': routing_decision.confidence_score,
                        'expected_cost': routing_decision.expected_cost,
                        'expected_latency_ms': routing_decision.expected_latency_ms,
                        'fallback_options': routing_decision.fallback_options
                    },
                    'routing_execution_time_ms': (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
                })
                
                # 6. 收集性能反饋（如果啟用）
                if enable_feedback_collection and self.feedback_system:
                    await self._collect_performance_feedback(
                        routing_decision=routing_decision,
                        response=response,
                        request_context={
                            'task_type': task_type,
                            'user_id': user_id,
                            'request_start_time': start_time
                        }
                    )
                
                return response
                
            finally:
                # 恢復原始提供商和模型設置
                self.provider = original_provider
                self.model = original_model
            
        except (AITaskRouterError, RoutingDecisionError) as e:
            self.logger.warning(f"⚠️ AI routing failed: {e}. Falling back to legacy routing")
            self.routing_stats['fallback_to_legacy_routing'] += 1
            
            # 回退到傳統路由
            return await super().analyze(
                prompt=prompt,
                context=context,
                analysis_type=analysis_type,
                analyst_id=analyst_id,
                stock_id=stock_id,
                user_id=user_id,
                **kwargs
            )
        except Exception as e:
            self.logger.error(f"❌ Unexpected error in AI routing: {e}")
            self.routing_stats['fallback_to_legacy_routing'] += 1
            raise
    
    def _map_analysis_type_to_task_type(self, analysis_type: AnalysisType) -> str:
        """將分析類型映射為任務類型"""
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
    
    def _estimate_tokens(self, prompt: str, context: Optional[Dict[str, Any]]) -> float:
        """估算token數量"""
        # 簡化的token估算
        token_count = len(prompt.split()) * 1.3  # 英文單詞到token的粗略比例
        
        if context:
            context_text = str(context)
            token_count += len(context_text.split()) * 1.3
        
        return token_count
    
    def _temporarily_switch_provider(self, provider: str, model: str):
        """臨時切換提供商和模型"""
        # 根據路由決策臨時切換提供商
        from ..utils.llm_client import LLMProvider
        
        if provider == "openai":
            self.provider = LLMProvider.OPENAI
        elif provider == "anthropic":
            self.provider = LLMProvider.ANTHROPIC
        elif provider == "gpt_oss":
            self.provider = LLMProvider.GPT_OSS
        
        self.model = model
    
    async def _collect_performance_feedback(
        self,
        routing_decision,
        response: LLMResponse,
        request_context: Dict[str, Any]
    ):
        """收集性能反饋"""
        try:
            if not response.success:
                # 記錄失敗反饋
                self.feedback_system.record_execution_feedback(
                    decision_id=str(hash(routing_decision.decision_metadata.get('request_id', ''))),
                    request_id=request_context.get('user_id', 'unknown'),
                    provider=routing_decision.selected_provider,
                    model_id=routing_decision.selected_model,
                    task_type=request_context['task_type'],
                    predicted_cost=routing_decision.expected_cost,
                    actual_cost=0.0,  # 失敗時成本為0
                    predicted_latency=routing_decision.expected_latency_ms,
                    actual_latency=response.response_time * 1000 if response.response_time else 0,
                    predicted_quality=routing_decision.expected_quality_score,
                    actual_quality=0.0,  # 失敗時品質為0
                    execution_success=False
                )
            else:
                # 計算實際指標
                actual_cost = self._calculate_actual_cost(response)
                actual_latency = response.response_time * 1000 if response.response_time else 0
                actual_quality = self._evaluate_response_quality(response, request_context['task_type'])
                
                self.feedback_system.record_execution_feedback(
                    decision_id=str(hash(routing_decision.decision_metadata.get('request_id', ''))),
                    request_id=request_context.get('user_id', 'unknown'),
                    provider=routing_decision.selected_provider,
                    model_id=routing_decision.selected_model,
                    task_type=request_context['task_type'],
                    predicted_cost=routing_decision.expected_cost,
                    actual_cost=actual_cost,
                    predicted_latency=routing_decision.expected_latency_ms,
                    actual_latency=actual_latency,
                    predicted_quality=routing_decision.expected_quality_score,
                    actual_quality=actual_quality,
                    execution_success=True
                )
            
            self.routing_stats['performance_feedback_records'] += 1
            
        except Exception as e:
            self.logger.error(f"❌ Failed to collect performance feedback: {e}")
    
    def _calculate_actual_cost(self, response: LLMResponse) -> float:
        """計算實際成本"""
        if not response.usage:
            return 0.0
        
        # 簡化的成本計算
        input_tokens = response.usage.get('prompt_tokens', 0)
        output_tokens = response.usage.get('completion_tokens', 0)
        
        # 使用基本的成本估算
        cost_per_1k = self._get_cost_per_1k_tokens(response.provider, response.model)
        return ((input_tokens + output_tokens) / 1000) * cost_per_1k
    
    def _evaluate_response_quality(self, response: LLMResponse, task_type: str) -> float:
        """評估響應品質"""
        if not response.content:
            return 0.0
        
        # 基本品質評估
        base_score = 0.7
        
        # 內容長度檢查
        if len(response.content) > 50:
            base_score += 0.1
        
        # JSON格式檢查
        content = response.content.strip()
        if content.startswith('{') and content.endswith('}'):
            base_score += 0.1
        
        return min(1.0, base_score)
    
    # ==================== AI路由管理接口 ====================
    
    async def optimize_routing_weights(
        self,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        analysis_hours: int = 72
    ) -> Dict[str, Any]:
        """
        基於性能反饋優化路由權重
        
        Args:
            strategy: 要優化的路由策略
            analysis_hours: 分析時間窗口
            
        Returns:
            優化結果
        """
        if not self.enable_ai_routing or not self._ai_routing_initialized:
            return {'status': 'ai_routing_disabled'}
        
        try:
            current_weights = self.ai_router.routing_strategies.get(strategy)
            if not current_weights:
                return {'status': 'strategy_not_found'}
            
            # 獲取權重調整建議
            suggested_weights, reasons = self.feedback_system.suggest_weight_adjustments(
                current_weights=current_weights,
                strategy=strategy,
                analysis_hours=analysis_hours
            )
            
            # 應用調整
            if reasons and reasons[0] != '數據不足，無法進行權重調整建議':
                success = self.feedback_system.apply_weight_adjustments(
                    router=self.ai_router,
                    suggested_weights=suggested_weights,
                    strategy=strategy,
                    reasons=reasons
                )
                
                return {
                    'status': 'optimized' if success else 'optimization_failed',
                    'strategy': strategy.value,
                    'old_weights': current_weights.__dict__,
                    'new_weights': suggested_weights.__dict__,
                    'reasons': reasons,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            else:
                return {
                    'status': 'no_optimization_needed',
                    'strategy': strategy.value,
                    'current_weights': current_weights.__dict__,
                    'reason': reasons[0] if reasons else 'No feedback data available'
                }
            
        except Exception as e:
            self.logger.error(f"❌ Weight optimization failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_ai_routing_statistics(self) -> Dict[str, Any]:
        """獲取AI路由統計信息"""
        if not self.enable_ai_routing:
            return self.routing_stats
        
        try:
            stats = self.routing_stats.copy()
            
            if self._ai_routing_initialized:
                # 添加路由器統計
                router_stats = self.ai_router.get_routing_statistics()
                stats.update({
                    'router_statistics': router_stats,
                    'feedback_statistics': self.feedback_system.get_feedback_statistics(),
                    'decision_history_count': len(self.ai_router.get_decision_history())
                })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get AI routing statistics: {e}")
            return self.routing_stats
    
    def get_routing_decision_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """獲取路由決策歷史"""
        if not self.enable_ai_routing or not self._ai_routing_initialized:
            return []
        
        try:
            return self.ai_router.get_decision_history(limit=limit)
        except Exception as e:
            self.logger.error(f"❌ Failed to get routing decision history: {e}")
            return []
    
    def get_model_performance_report(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        hours_back: int = 168
    ) -> Dict[str, Any]:
        """獲取模型性能報告"""
        if not self.enable_ai_routing or not self._ai_routing_initialized:
            return {'status': 'ai_routing_disabled'}
        
        try:
            return self.feedback_system.get_model_performance_summary(
                provider=provider,
                model_id=model_id,
                hours_back=hours_back
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to get model performance report: {e}")
            return {'status': 'error', 'error': str(e)}
    
    # ==================== 增強的健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """增強的健康檢查，包含AI路由狀態"""
        # 獲取基礎健康檢查
        health_status = await super().health_check()
        
        # 添加AI路由健康狀態
        if self.enable_ai_routing:
            try:
                if self._ai_routing_initialized:
                    router_health = await self.ai_router.health_check()
                    feedback_health = await self.feedback_system.health_check()
                    
                    health_status['ai_routing'] = {
                        'enabled': True,
                        'initialized': True,
                        'router_status': router_health['overall_status'],
                        'feedback_status': feedback_health['overall_status'],
                        'statistics': self.routing_stats
                    }
                else:
                    health_status['ai_routing'] = {
                        'enabled': True,
                        'initialized': False,
                        'note': 'AI routing not yet initialized'
                    }
            except Exception as e:
                health_status['ai_routing'] = {
                    'enabled': True,
                    'status': 'error',
                    'error': str(e)
                }
        else:
            health_status['ai_routing'] = {
                'enabled': False,
                'note': 'AI routing disabled'
            }
        
        return health_status
    
    async def close(self):
        """關閉客戶端，包括AI路由組件"""
        try:
            # 關閉AI路由組件
            if self.enable_ai_routing and self._ai_routing_initialized:
                if self.performance_monitor:
                    await self.performance_monitor.stop()
                
            # 關閉基礎LLM客戶端
            await super().close()
            
            self.logger.info("✅ Enhanced LLM Client closed successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error closing Enhanced LLM Client: {e}")

# ==================== 便利函數 ====================

def create_enhanced_llm_client(
    llm_config: Optional[Dict[str, Any]] = None,
    enable_ai_routing: bool = True,
    router_config: Optional[Dict[str, Any]] = None,
    feedback_config: Optional[Dict[str, Any]] = None
) -> EnhancedLLMClient:
    """
    創建增強版LLM客戶端的便利函數
    
    Args:
        llm_config: 基礎LLM配置
        enable_ai_routing: 是否啟用AI路由
        router_config: 路由器配置
        feedback_config: 反饋系統配置
        
    Returns:
        配置好的增強版LLM客戶端
    """
    return EnhancedLLMClient(
        config=llm_config,
        enable_ai_routing=enable_ai_routing,
        router_config=router_config,
        feedback_config=feedback_config
    )

# 全局增強客戶端管理
_global_enhanced_llm_client: Optional[EnhancedLLMClient] = None

def get_global_enhanced_llm_client() -> EnhancedLLMClient:
    """獲取全局增強版LLM客戶端"""
    global _global_enhanced_llm_client
    if _global_enhanced_llm_client is None:
        _global_enhanced_llm_client = create_enhanced_llm_client()
    return _global_enhanced_llm_client

async def close_global_enhanced_llm_client():
    """關閉全局增強版LLM客戶端"""
    global _global_enhanced_llm_client
    if _global_enhanced_llm_client:
        await _global_enhanced_llm_client.close()
        _global_enhanced_llm_client = None