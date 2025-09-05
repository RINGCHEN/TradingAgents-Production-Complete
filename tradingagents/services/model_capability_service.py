#!/usr/bin/env python3
"""
Model Capability Service
模型能力服務 - GPT-OSS整合任務1.2.2
統一LLMClient接口整合
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from ..database.model_capability_db import ModelCapabilityDB, ModelCapabilityDBError
from ..database.task_metadata_db import TaskMetadataDB, TaskMetadataDBError
from ..benchmarks.benchmark_runner import BenchmarkRunner
from ..monitoring.performance_monitor import PerformanceMonitor, MetricType
from ..utils.llm_client import LLMClient, LLMRequest, LLMResponse, AnalysisType

logger = logging.getLogger(__name__)

class ModelCapabilityServiceError(Exception):
    """模型能力服務錯誤"""
    pass

class ModelCapabilityService:
    """
    模型能力服務
    
    統一管理：
    1. 模型能力數據庫操作
    2. 基準測試執行
    3. 性能監控
    4. LLM客戶端集成
    5. 智能路由決策
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model_db: Optional[ModelCapabilityDB] = None,
        task_db: Optional[TaskMetadataDB] = None,
        benchmark_runner: Optional[BenchmarkRunner] = None,
        performance_monitor: Optional[PerformanceMonitor] = None
    ):
        """
        初始化模型能力服務
        
        Args:
            llm_client: LLM客戶端
            model_db: 模型能力數據庫
            task_db: 任務元數據數據庫
            benchmark_runner: 基準測試執行器
            performance_monitor: 性能監控器
        """
        self.llm_client = llm_client or LLMClient()
        self.model_db = model_db or ModelCapabilityDB()
        self.task_db = task_db or TaskMetadataDB()
        self.benchmark_runner = benchmark_runner or BenchmarkRunner(
            llm_client=self.llm_client,
            model_db=self.model_db
        )
        self.performance_monitor = performance_monitor or PerformanceMonitor(
            model_db=self.model_db,
            task_db=self.task_db
        )
        
        self.logger = logger
        self._initialized = False
    
    async def initialize(self) -> bool:
        """
        初始化服務
        
        Returns:
            是否初始化成功
        """
        try:
            self.logger.info("🚀 Initializing Model Capability Service...")
            
            # 初始化數據庫
            await self._initialize_databases()
            
            # 啟動性能監控
            await self.performance_monitor.start()
            
            # 添加性能監控的告警回調
            self.performance_monitor.add_alert_callback(self._handle_performance_alert)
            
            self._initialized = True
            self.logger.info("✅ Model Capability Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Model Capability Service: {e}")
            return False
    
    async def shutdown(self):
        """關閉服務"""
        try:
            self.logger.info("🔄 Shutting down Model Capability Service...")
            
            # 停止性能監控
            await self.performance_monitor.stop()
            
            # 關閉LLM客戶端
            await self.llm_client.close()
            
            self._initialized = False
            self.logger.info("✅ Model Capability Service shut down successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error during service shutdown: {e}")
    
    async def _initialize_databases(self):
        """初始化數據庫"""
        try:
            # 初始化標準任務類型
            task_types = await self.task_db.initialize_standard_task_types()
            self.logger.info(f"✅ Initialized {len(task_types)} standard task types")
            
            # 初始化標準模型
            models = await self.model_db.initialize_standard_models()
            self.logger.info(f"✅ Initialized {len(models)} standard models")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing databases: {e}")
            raise ModelCapabilityServiceError(f"Database initialization failed: {e}")
    
    def _handle_performance_alert(self, message: str, alert_data: Dict[str, Any]):
        """處理性能告警"""
        self.logger.warning(f"⚠️ Performance Alert: {message}")
        
        # 這裡可以添加更多告警處理邏輯
        # 例如：發送通知、自動調整路由策略等
    
    # ==================== 智能分析接口 ====================
    
    async def analyze_with_optimal_model(
        self,
        prompt: str,
        task_type: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        使用最優模型進行分析
        
        Args:
            prompt: 分析提示詞
            task_type: 任務類型
            context: 分析上下文
            user_id: 用戶ID
            **kwargs: 其他參數
            
        Returns:
            分析結果，包含路由決策信息
        """
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            # 獲取任務元數據
            task_metadata = await self.task_db.get_task_metadata(task_type)
            if not task_metadata:
                raise ModelCapabilityServiceError(f"Task type '{task_type}' not found")
            
            # 進行路由決策
            from ..database.task_metadata_models import RoutingDecisionRequest
            
            routing_request = RoutingDecisionRequest(
                task_type=task_type,
                user_tier=kwargs.get('user_tier', 'free'),
                estimated_tokens=len(prompt.split()) * 1.3,  # 估算token數
                priority=kwargs.get('priority', 'standard'),
                requires_high_quality=kwargs.get('requires_high_quality', False),
                max_acceptable_latency=kwargs.get('max_acceptable_latency'),
                max_acceptable_cost=kwargs.get('max_acceptable_cost'),
                user_preferences=kwargs.get('user_preferences')
            )
            
            routing_decision = await self.task_db.make_routing_decision(routing_request)
            
            # 使用性能監控器測量請求
            async with self.performance_monitor.measure_request(
                provider=routing_decision.selected_provider,
                model_id=routing_decision.selected_model,
                task_type=task_type,
                user_id=user_id
            ) as perf_ctx:
                
                # 執行LLM分析
                analysis_type = self._map_task_type_to_analysis_type(task_type)
                
                request = LLMRequest(
                    prompt=prompt,
                    context=context or {},
                    analysis_type=analysis_type,
                    analyst_id=kwargs.get('analyst_id', 'general'),
                    stock_id=kwargs.get('stock_id'),
                    user_id=user_id,
                    max_tokens=kwargs.get('max_tokens'),
                    temperature=kwargs.get('temperature')
                )
                
                response = await self.llm_client._execute_request(request)
                
                # 更新性能上下文
                perf_ctx.set_success(response.success)
                
                if response.success:
                    # 評估回應品質（簡化實現）
                    quality_score = self._evaluate_response_quality(response.content, task_type)
                    perf_ctx.set_accuracy(quality_score)
                
                    # 估算成本
                    if response.usage:
                        total_tokens = response.usage.get('total_tokens', 0)
                        cost = self._estimate_cost(
                            routing_decision.selected_provider,
                            routing_decision.selected_model,
                            total_tokens
                        )
                        perf_ctx.set_cost(cost)
                
                # 記錄任務性能到數據庫
                await self.task_db.record_task_performance(
                    task_type=task_type,
                    provider=routing_decision.selected_provider,
                    model=routing_decision.selected_model,
                    latency_ms=response.response_time * 1000 if response.response_time else 0,
                    success=response.success,
                    quality_score=perf_ctx.accuracy if hasattr(perf_ctx, 'accuracy') else None,
                    cost=perf_ctx.cost if hasattr(perf_ctx, 'cost') else 0.0,
                    metadata={
                        'user_id': user_id,
                        'estimated_tokens': routing_request.estimated_tokens,
                        'routing_confidence': routing_decision.confidence_score
                    }
                )
                
                # 構建完整回應
                return {
                    'success': response.success,
                    'content': response.content,
                    'error': response.error,
                    'routing_decision': {
                        'selected_provider': routing_decision.selected_provider,
                        'selected_model': routing_decision.selected_model,
                        'reasoning': routing_decision.reasoning,
                        'expected_cost': routing_decision.expected_cost,
                        'expected_latency_ms': routing_decision.expected_latency_ms,
                        'confidence_score': routing_decision.confidence_score,
                        'fallback_options': routing_decision.fallback_options
                    },
                    'performance': {
                        'actual_latency_ms': response.response_time * 1000 if response.response_time else 0,
                        'tokens_used': response.usage.get('total_tokens') if response.usage else None,
                        'quality_score': perf_ctx.accuracy if hasattr(perf_ctx, 'accuracy') else None
                    },
                    'metadata': response.metadata,
                    'request_id': response.request_id,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error in optimal model analysis: {e}")
            raise ModelCapabilityServiceError(f"Analysis failed: {e}")
    
    def _map_task_type_to_analysis_type(self, task_type: str) -> AnalysisType:
        """將任務類型映射為分析類型"""
        mapping = {
            'financial_summary': AnalysisType.FUNDAMENTAL,
            'news_classification': AnalysisType.NEWS,
            'investment_reasoning': AnalysisType.REASONING,
            'report_generation': AnalysisType.INVESTMENT,
            'market_sentiment': AnalysisType.SENTIMENT,
            'technical_analysis': AnalysisType.TECHNICAL,
            'risk_assessment': AnalysisType.RISK
        }
        return mapping.get(task_type, AnalysisType.TECHNICAL)
    
    def _evaluate_response_quality(self, content: str, task_type: str) -> float:
        """評估回應品質（簡化實現）"""
        if not content or len(content.strip()) < 20:
            return 0.0
        
        # 基本品質評分
        base_score = 0.5
        
        # 長度檢查
        if len(content) > 100:
            base_score += 0.2
        
        # JSON格式檢查
        if content.strip().startswith('{') and content.strip().endswith('}'):
            base_score += 0.2
        
        # 任務特定評分
        task_keywords = {
            'financial_summary': ['財務', '營收', '獲利', '成長'],
            'investment_reasoning': ['分析', '建議', '風險', '評估'],
            'market_sentiment': ['情緒', '市場', '投資人', '態度']
        }
        
        if task_type in task_keywords:
            keywords = task_keywords[task_type]
            keyword_count = sum(1 for keyword in keywords if keyword in content)
            base_score += (keyword_count / len(keywords)) * 0.1
        
        return min(1.0, base_score)
    
    def _estimate_cost(self, provider: str, model: str, tokens: int) -> float:
        """估算成本"""
        # 簡化的成本估算
        cost_per_1k = {
            'gpt_oss': 0.0,  # 本地免費
            'openai': {
                'gpt-4': 0.03,
                'gpt-3.5-turbo': 0.001
            },
            'anthropic': {
                'claude-3-sonnet-20240229': 0.003
            }
        }
        
        if provider in cost_per_1k:
            if isinstance(cost_per_1k[provider], dict):
                model_cost = cost_per_1k[provider].get(model, 0.002)
            else:
                model_cost = cost_per_1k[provider]
            
            return (tokens / 1000) * model_cost
        
        return 0.002 * (tokens / 1000)  # 默認成本
    
    # ==================== 基準測試接口 ====================
    
    async def run_model_benchmark(
        self,
        provider: str,
        model_id: str,
        suite_name: str = "standard"
    ) -> Dict[str, Any]:
        """執行模型基準測試"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            return await self.benchmark_runner.run_model_benchmark(
                provider=provider,
                model_id=model_id,
                suite_name=suite_name,
                llm_client=self.llm_client,
                update_database=True
            )
        except Exception as e:
            self.logger.error(f"❌ Benchmark failed for {provider}/{model_id}: {e}")
            raise ModelCapabilityServiceError(f"Benchmark execution failed: {e}")
    
    async def run_batch_benchmarks(
        self,
        models: List[Tuple[str, str]],
        suite_name: str = "standard",
        parallel: bool = False
    ) -> Dict[str, Any]:
        """執行批量基準測試"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            return await self.benchmark_runner.run_batch_benchmarks(
                models=models,
                suite_name=suite_name,
                llm_client=self.llm_client,
                update_database=True,
                parallel_models=parallel
            )
        except Exception as e:
            self.logger.error(f"❌ Batch benchmark failed: {e}")
            raise ModelCapabilityServiceError(f"Batch benchmark execution failed: {e}")
    
    async def run_all_model_benchmarks(self, suite_name: str = "standard") -> Dict[str, Any]:
        """對所有註冊模型執行基準測試"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            return await self.benchmark_runner.run_all_registered_models(
                suite_name=suite_name,
                llm_client=self.llm_client,
                update_database=True
            )
        except Exception as e:
            self.logger.error(f"❌ All models benchmark failed: {e}")
            raise ModelCapabilityServiceError(f"All models benchmark execution failed: {e}")
    
    # ==================== 模型管理接口 ====================
    
    async def register_model(
        self,
        provider: str,
        model_id: str,
        model_name: str,
        **model_properties
    ) -> Dict[str, Any]:
        """註冊新模型"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            model_capability = await self.model_db.create_model_capability(
                provider=provider,
                model_id=model_id,
                model_name=model_name,
                **model_properties
            )
            
            self.logger.info(f"✅ Registered model: {provider}/{model_id}")
            return model_capability.dict()
            
        except ModelCapabilityDBError as e:
            self.logger.error(f"❌ Failed to register model {provider}/{model_id}: {e}")
            raise ModelCapabilityServiceError(f"Model registration failed: {e}")
    
    async def list_available_models(
        self,
        provider: Optional[str] = None,
        privacy_level: Optional[str] = None,
        min_capability_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """列出可用模型"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            models = await self.model_db.list_model_capabilities(
                provider=provider,
                privacy_level=privacy_level,
                min_capability_score=min_capability_score,
                is_available=True
            )
            
            return [model.dict() for model in models]
            
        except ModelCapabilityDBError as e:
            self.logger.error(f"❌ Failed to list models: {e}")
            raise ModelCapabilityServiceError(f"Failed to list models: {e}")
    
    async def get_model_recommendations(
        self,
        task_requirements: Dict[str, Any],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """獲取模型推薦"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            recommendations = await self.model_db.recommend_models(
                task_requirements=task_requirements,
                limit=limit
            )
            
            return [
                {
                    'model': model.dict(),
                    'match_score': score,
                    'recommendation_reason': self._generate_recommendation_reason(model, score)
                }
                for model, score in recommendations
            ]
            
        except ModelCapabilityDBError as e:
            self.logger.error(f"❌ Failed to get recommendations: {e}")
            raise ModelCapabilityServiceError(f"Failed to get recommendations: {e}")
    
    def _generate_recommendation_reason(self, model, score: float) -> str:
        """生成推薦理由"""
        reasons = []
        
        if score >= 0.9:
            reasons.append("Excellent match for requirements")
        elif score >= 0.7:
            reasons.append("Good match for requirements")
        elif score >= 0.5:
            reasons.append("Moderate match for requirements")
        else:
            reasons.append("Low match for requirements")
        
        if model.privacy_level == 'local':
            reasons.append("High privacy protection")
        
        if model.cost_per_1k_input_tokens == 0.0:
            reasons.append("Free to use")
        elif model.cost_per_1k_input_tokens < 0.01:
            reasons.append("Low cost")
        
        if model.avg_latency_ms < 1000:
            reasons.append("Fast response")
        
        return "; ".join(reasons)
    
    # ==================== 性能監控接口 ====================
    
    async def get_performance_report(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """獲取性能報告"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            return await self.performance_monitor.get_performance_report(
                provider=provider,
                model_id=model_id,
                hours_back=hours_back
            )
        except Exception as e:
            self.logger.error(f"❌ Failed to get performance report: {e}")
            raise ModelCapabilityServiceError(f"Failed to get performance report: {e}")
    
    def get_current_metrics(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Dict[str, float]]:
        """獲取當前性能指標"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        return self.performance_monitor.get_current_metrics(
            provider=provider,
            model_id=model_id
        )
    
    # ==================== 統計和報告接口 ====================
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        if not self._initialized:
            raise ModelCapabilityServiceError("Service not initialized")
        
        try:
            # 模型統計
            model_stats = await self.model_db.get_performance_statistics()
            
            # 任務統計（簡化實現）
            task_count = len(await self.task_db.list_task_metadata())
            
            # LLM客戶端統計
            llm_stats = self.llm_client.get_stats()
            
            # 基準測試統計
            benchmark_history = self.benchmark_runner.framework.get_history(limit=50)
            
            return {
                'models': model_stats,
                'tasks': {
                    'total_task_types': task_count
                },
                'llm_client': llm_stats,
                'benchmarks': {
                    'total_runs': len(benchmark_history),
                    'recent_runs': benchmark_history[:5] if benchmark_history else []
                },
                'performance_monitoring': {
                    'active': self.performance_monitor._running if hasattr(self.performance_monitor, '_running') else False,
                    'current_metrics_count': len(self.get_current_metrics())
                },
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get system statistics: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """系統健康檢查"""
        health_status = {
            'service_initialized': self._initialized,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {}
        }
        
        try:
            # 檢查LLM客戶端
            llm_health = await self.llm_client.health_check()
            health_status['components']['llm_client'] = llm_health
            
            # 檢查數據庫（簡化檢查）
            try:
                models = await self.model_db.list_model_capabilities(limit=1)
                health_status['components']['model_db'] = {
                    'status': 'healthy',
                    'accessible': True,
                    'model_count': len(models)
                }
            except Exception as e:
                health_status['components']['model_db'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
            
            # 檢查性能監控
            health_status['components']['performance_monitor'] = {
                'status': 'healthy' if hasattr(self.performance_monitor, '_running') and self.performance_monitor._running else 'stopped',
                'metrics_count': len(self.get_current_metrics())
            }
            
            # 整體狀態
            component_statuses = [comp.get('status', 'unknown') for comp in health_status['components'].values()]
            if all(status == 'healthy' for status in component_statuses):
                health_status['overall_status'] = 'healthy'
            elif any(status == 'unhealthy' for status in component_statuses):
                health_status['overall_status'] = 'unhealthy'
            else:
                health_status['overall_status'] = 'degraded'
            
            return health_status
            
        except Exception as e:
            health_status['overall_status'] = 'error'
            health_status['error'] = str(e)
            return health_status