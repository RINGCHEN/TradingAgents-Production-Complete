#!/usr/bin/env python3
"""
AI Task Router - 企業級智能路由決策引擎
GPT-OSS整合任務1.3.1 - 核心路由決策引擎實現

基於現有基礎設施，實現高級AI任務路由決策系統：
- 智能成本效益分析
- 多維度路由決策
- 完整決策審計
- 動態策略調整
"""

import uuid
import json
import logging
import asyncio
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, NamedTuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from contextlib import asynccontextmanager

from ..database.task_metadata_db import TaskMetadataDB, TaskMetadataDBError
from ..database.model_capability_db import ModelCapabilityDB, ModelCapabilityDBError
from ..database.task_metadata_models import (
    RoutingDecisionRequest, RoutingDecisionResponse,
    TaskMetadataResponse, ModelCapabilityResponse
)
from ..utils.llm_client import LLMProvider
from ..monitoring.performance_monitor import PerformanceMonitor

logger = logging.getLogger(__name__)

# ==================== 核心數據類型 ====================

class RoutingStrategy(Enum):
    """路由策略枚舉"""
    COST_OPTIMIZED = "cost_optimized"           # 成本優化
    PERFORMANCE_OPTIMIZED = "performance_optimized"  # 性能優化  
    BALANCED = "balanced"                       # 平衡模式
    QUALITY_FIRST = "quality_first"             # 品質優先
    LATENCY_FIRST = "latency_first"             # 延遲優先
    PRIVACY_FIRST = "privacy_first"             # 隱私優先
    CUSTOM = "custom"                          # 自定義策略

class DecisionFactor(Enum):
    """決策因子枚舉"""
    COST = "cost"
    LATENCY = "latency"
    QUALITY = "quality"
    AVAILABILITY = "availability"
    PRIVACY = "privacy"
    USER_PREFERENCE = "user_preference"
    HISTORICAL_PERFORMANCE = "historical_performance"
    LOAD_BALANCING = "load_balancing"

@dataclass
class RoutingWeights:
    """路由決策權重配置"""
    cost: float = 0.3
    latency: float = 0.2
    quality: float = 0.25
    availability: float = 0.15
    privacy: float = 0.05
    user_preference: float = 0.05
    
    def normalize(self):
        """標準化權重使總和為1.0"""
        total = self.cost + self.latency + self.quality + self.availability + self.privacy + self.user_preference
        if total > 0:
            self.cost /= total
            self.latency /= total
            self.quality /= total
            self.availability /= total
            self.privacy /= total
            self.user_preference /= total

@dataclass
class ModelScore:
    """模型評分詳情"""
    model: ModelCapabilityResponse
    total_score: float
    factor_scores: Dict[DecisionFactor, float] = field(default_factory=dict)
    cost_analysis: Dict[str, Any] = field(default_factory=dict)
    performance_prediction: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: List[str] = field(default_factory=list)

@dataclass
class RoutingContext:
    """路由上下文信息"""
    request_id: str
    task_metadata: TaskMetadataResponse
    available_models: List[ModelCapabilityResponse]
    routing_request: RoutingDecisionRequest
    strategy: RoutingStrategy
    weights: RoutingWeights
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionAudit:
    """決策審計記錄"""
    decision_id: str
    request_id: str
    task_type: str
    selected_model: ModelCapabilityResponse
    all_model_scores: List[ModelScore]
    routing_context: RoutingContext
    decision_reasoning: List[str]
    confidence_score: float
    execution_time_ms: float
    fallback_chain: List[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式供存儲"""
        return {
            'decision_id': self.decision_id,
            'request_id': self.request_id,
            'task_type': self.task_type,
            'selected_provider': self.selected_model.provider,
            'selected_model': self.selected_model.model_id,
            'selected_model_name': self.selected_model.model_name,
            'total_candidates': len(self.all_model_scores),
            'decision_reasoning': self.decision_reasoning,
            'confidence_score': self.confidence_score,
            'execution_time_ms': self.execution_time_ms,
            'routing_strategy': self.routing_context.strategy.value,
            'weights_used': asdict(self.routing_context.weights),
            'fallback_chain': self.fallback_chain,
            'timestamp': self.timestamp.isoformat(),
            'model_scores': [
                {
                    'provider': score.model.provider,
                    'model_id': score.model.model_id,
                    'total_score': score.total_score,
                    'confidence': score.confidence,
                    'cost_analysis': score.cost_analysis,
                    'reasoning': score.reasoning
                }
                for score in self.all_model_scores
            ]
        }

# ==================== 異常類型 ====================

class AITaskRouterError(Exception):
    """AI任務路由器基礎錯誤"""
    pass

class RoutingDecisionError(AITaskRouterError):
    """路由決策錯誤"""
    pass

class CostCalculationError(AITaskRouterError):
    """成本計算錯誤"""
    pass

class ModelEvaluationError(AITaskRouterError):
    """模型評估錯誤"""
    pass

# ==================== 核心路由器類 ====================

class AITaskRouter:
    """
    企業級AI任務智能路由器
    
    功能特性：
    1. 多維度智能路由決策
    2. 真實成本效益計算  
    3. 完整決策審計追蹤
    4. 動態策略調整
    5. 性能反饋學習
    """
    
    def __init__(
        self,
        task_db: Optional[TaskMetadataDB] = None,
        model_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化AI任務路由器
        
        Args:
            task_db: 任務元數據數據庫
            model_db: 模型能力數據庫  
            performance_monitor: 性能監控器
            config: 路由器配置
        """
        self.task_db = task_db or TaskMetadataDB()
        self.model_db = model_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor
        
        # 配置初始化
        self.config = config or {}
        self._load_default_config()
        
        # 路由策略配置
        self.routing_strategies = self._initialize_routing_strategies()
        self.default_strategy = RoutingStrategy(
            self.config.get('default_strategy', 'balanced')
        )
        
        # 決策審計存儲
        self.decision_history: List[DecisionAudit] = []
        self.max_history_size = self.config.get('max_decision_history', 1000)
        
        # 性能統計
        self.stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_decision_time_ms': 0.0,
            'strategy_usage': {strategy.value: 0 for strategy in RoutingStrategy},
            'model_selection_frequency': {},
            'cost_savings': 0.0,
            'last_reset': datetime.now(timezone.utc)
        }
        
        # 模型性能緩存
        self.model_performance_cache = {}
        self.cache_ttl_seconds = self.config.get('performance_cache_ttl', 3600)
        
        self.logger = logger
        self._initialized = False
    
    def _load_default_config(self):
        """載入預設配置"""
        defaults = {
            'enable_cost_optimization': True,
            'enable_performance_learning': True,
            'enable_load_balancing': True,
            'max_fallback_attempts': 3,
            'decision_confidence_threshold': 0.7,
            'cost_variance_threshold': 0.15,
            'latency_variance_threshold': 0.20,
            'quality_variance_threshold': 0.10,
            'performance_cache_ttl': 3600,
            'max_decision_history': 1000,
            'default_strategy': 'balanced',
            'enable_audit_logging': True,
            'audit_detail_level': 'full'
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def _initialize_routing_strategies(self) -> Dict[RoutingStrategy, RoutingWeights]:
        """初始化路由策略權重配置"""
        strategies = {
            RoutingStrategy.COST_OPTIMIZED: RoutingWeights(
                cost=0.5, latency=0.15, quality=0.2, availability=0.1, privacy=0.03, user_preference=0.02
            ),
            RoutingStrategy.PERFORMANCE_OPTIMIZED: RoutingWeights(
                cost=0.1, latency=0.4, quality=0.35, availability=0.1, privacy=0.03, user_preference=0.02
            ),
            RoutingStrategy.BALANCED: RoutingWeights(
                cost=0.25, latency=0.25, quality=0.25, availability=0.15, privacy=0.05, user_preference=0.05
            ),
            RoutingStrategy.QUALITY_FIRST: RoutingWeights(
                cost=0.1, latency=0.15, quality=0.5, availability=0.15, privacy=0.05, user_preference=0.05
            ),
            RoutingStrategy.LATENCY_FIRST: RoutingWeights(
                cost=0.15, latency=0.5, quality=0.2, availability=0.1, privacy=0.03, user_preference=0.02
            ),
            RoutingStrategy.PRIVACY_FIRST: RoutingWeights(
                cost=0.15, latency=0.15, quality=0.2, availability=0.1, privacy=0.35, user_preference=0.05
            ),
        }
        
        # 標準化所有權重
        for weights in strategies.values():
            weights.normalize()
        
        return strategies
    
    async def initialize(self) -> bool:
        """
        初始化路由器
        
        Returns:
            是否初始化成功
        """
        try:
            self.logger.info("🚀 Initializing AI Task Router...")
            
            # 預熱模型性能緩存
            if self.config.get('enable_performance_learning'):
                await self._warmup_performance_cache()
            
            self._initialized = True
            self.logger.info("✅ AI Task Router initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize AI Task Router: {e}")
            return False
    
    async def _warmup_performance_cache(self):
        """預熱性能緩存"""
        try:
            if self.performance_monitor:
                # 獲取最近的性能數據
                report = await self.performance_monitor.get_performance_report(hours_back=24)
                
                # 更新緩存
                for provider_model, metrics in report.get('provider_performance', {}).items():
                    self.model_performance_cache[provider_model] = {
                        'avg_latency': metrics.get('avg_latency_ms', 0),
                        'success_rate': metrics.get('success_rate', 0.95),
                        'avg_quality': metrics.get('avg_quality_score', 0.8),
                        'total_requests': metrics.get('total_requests', 0),
                        'last_updated': datetime.now(timezone.utc)
                    }
            
            self.logger.info(f"✅ Performance cache warmed up with {len(self.model_performance_cache)} models")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Performance cache warmup failed: {e}")
    
    # ==================== 主要路由決策接口 ====================
    
    async def make_routing_decision(
        self,
        request: RoutingDecisionRequest,
        strategy: Optional[RoutingStrategy] = None,
        custom_weights: Optional[RoutingWeights] = None
    ) -> RoutingDecisionResponse:
        """
        執行智能路由決策
        
        Args:
            request: 路由決策請求
            strategy: 指定的路由策略
            custom_weights: 自定義權重配置
            
        Returns:
            路由決策響應
            
        Raises:
            RoutingDecisionError: 決策執行失敗
        """
        if not self._initialized:
            raise RoutingDecisionError("Router not initialized")
        
        decision_start_time = datetime.now()
        request_id = str(uuid.uuid4())
        
        try:
            # 更新統計
            self.stats['total_decisions'] += 1
            
            # 獲取任務元數據
            task_metadata = await self.task_db.get_task_metadata(request.task_type)
            if not task_metadata:
                raise RoutingDecisionError(f"Task type '{request.task_type}' not found")
            
            # 獲取可用模型
            available_models = await self._get_available_models_for_task(task_metadata, request)
            if not available_models:
                raise RoutingDecisionError("No suitable models available")
            
            # 確定路由策略和權重
            selected_strategy = strategy or self._determine_optimal_strategy(request, task_metadata)
            weights = custom_weights or self.routing_strategies.get(selected_strategy, self.routing_strategies[RoutingStrategy.BALANCED])
            
            # 創建路由上下文
            routing_context = RoutingContext(
                request_id=request_id,
                task_metadata=task_metadata,
                available_models=available_models,
                routing_request=request,
                strategy=selected_strategy,
                weights=weights,
                user_context=self._extract_user_context(request)
            )
            
            # 評估所有候選模型
            model_scores = await self._evaluate_models(routing_context)
            
            if not model_scores:
                raise RoutingDecisionError("Failed to evaluate any models")
            
            # 選擇最優模型
            best_model_score = self._select_optimal_model(model_scores, weights)
            
            # 生成決策響應
            decision_response = await self._generate_decision_response(
                best_model_score, model_scores, routing_context
            )
            
            # 記錄決策審計
            execution_time = (datetime.now() - decision_start_time).total_seconds() * 1000
            await self._record_decision_audit(
                decision_response, model_scores, routing_context, execution_time
            )
            
            # 更新統計
            self.stats['successful_decisions'] += 1
            self.stats['strategy_usage'][selected_strategy.value] += 1
            self._update_performance_stats(execution_time)
            
            self.logger.info(
                f"✅ Routing decision completed: {decision_response.selected_provider}/"
                f"{decision_response.selected_model} (confidence: {decision_response.confidence_score:.3f})"
            )
            
            return decision_response
            
        except Exception as e:
            self.stats['failed_decisions'] += 1
            self.logger.error(f"❌ Routing decision failed: {e}")
            raise RoutingDecisionError(f"Failed to make routing decision: {e}")
    
    async def _get_available_models_for_task(
        self,
        task_metadata: TaskMetadataResponse,
        request: RoutingDecisionRequest
    ) -> List[ModelCapabilityResponse]:
        """獲取任務的可用模型"""
        try:
            # 構建任務需求
            task_requirements = {
                'min_capability_score': task_metadata.min_model_capability_score,
                'max_cost_per_1k': request.max_acceptable_cost or task_metadata.max_acceptable_cost_per_1k,
                'max_latency_ms': request.max_acceptable_latency or task_metadata.max_acceptable_latency_ms,
                'required_features': task_metadata.required_features,
                'max_tokens': max(task_metadata.max_tokens_input, task_metadata.max_tokens_output),
            }
            
            # 確定隱私要求
            privacy_level = None
            if task_metadata.requires_local_processing:
                privacy_level = "local"
            elif task_metadata.data_sensitivity_level in ["high", "confidential"]:
                privacy_level = "local" if not task_metadata.allow_cloud_fallback else None
            
            # 獲取可用模型
            available_models = await self.model_db.list_model_capabilities(
                privacy_level=privacy_level,
                min_capability_score=task_requirements['min_capability_score'],
                max_cost_per_1k=task_requirements['max_cost_per_1k'],
                is_available=True
            )
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get available models: {e}")
            raise ModelEvaluationError(f"Failed to get available models: {e}")
    
    def _determine_optimal_strategy(
        self,
        request: RoutingDecisionRequest,
        task_metadata: TaskMetadataResponse
    ) -> RoutingStrategy:
        """智能確定最優路由策略"""
        
        # 用戶明確指定策略
        user_preferences = request.user_preferences or {}
        if 'routing_strategy' in user_preferences:
            try:
                return RoutingStrategy(user_preferences['routing_strategy'])
            except ValueError:
                pass
        
        # 基於任務特性推薦策略
        if task_metadata.requires_local_processing or task_metadata.data_sensitivity_level == "high":
            return RoutingStrategy.PRIVACY_FIRST
        
        if request.requires_high_quality:
            return RoutingStrategy.QUALITY_FIRST
        
        if request.priority == "urgent":
            return RoutingStrategy.LATENCY_FIRST
        
        if request.user_tier in ["free", "basic"]:
            return RoutingStrategy.COST_OPTIMIZED
        
        # 默認平衡策略
        return self.default_strategy
    
    def _extract_user_context(self, request: RoutingDecisionRequest) -> Dict[str, Any]:
        """提取用戶上下文信息"""
        return {
            'user_tier': request.user_tier,
            'priority': request.priority,
            'preferences': request.user_preferences or {},
            'historical_usage': {},  # 可以從數據庫獲取
            'estimated_tokens': request.estimated_tokens
        }
    
    # ==================== 模型評估和評分 ====================
    
    async def _evaluate_models(self, context: RoutingContext) -> List[ModelScore]:
        """評估所有候選模型"""
        model_scores = []
        
        for model in context.available_models:
            try:
                score = await self._evaluate_single_model(model, context)
                model_scores.append(score)
                
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to evaluate model {model.provider}/{model.model_id}: {e}")
                continue
        
        # 按總分排序
        model_scores.sort(key=lambda x: x.total_score, reverse=True)
        
        return model_scores
    
    async def _evaluate_single_model(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> ModelScore:
        """評估單個模型"""
        factor_scores = {}
        reasoning = []
        
        # 1. 成本評估
        cost_score, cost_analysis = await self._calculate_cost_score(model, context)
        factor_scores[DecisionFactor.COST] = cost_score
        reasoning.append(f"成本評分: {cost_score:.3f} ({cost_analysis.get('reasoning', '')})")
        
        # 2. 延遲評估
        latency_score, latency_analysis = await self._calculate_latency_score(model, context)
        factor_scores[DecisionFactor.LATENCY] = latency_score
        reasoning.append(f"延遲評分: {latency_score:.3f}")
        
        # 3. 品質評估
        quality_score = self._calculate_quality_score(model, context)
        factor_scores[DecisionFactor.QUALITY] = quality_score
        reasoning.append(f"品質評分: {quality_score:.3f}")
        
        # 4. 可用性評估
        availability_score = await self._calculate_availability_score(model, context)
        factor_scores[DecisionFactor.AVAILABILITY] = availability_score
        reasoning.append(f"可用性評分: {availability_score:.3f}")
        
        # 5. 隱私評估
        privacy_score = self._calculate_privacy_score(model, context)
        factor_scores[DecisionFactor.PRIVACY] = privacy_score
        
        # 6. 用戶偏好評估
        preference_score = self._calculate_user_preference_score(model, context)
        factor_scores[DecisionFactor.USER_PREFERENCE] = preference_score
        
        # 計算加權總分
        weights = context.weights
        total_score = (
            factor_scores[DecisionFactor.COST] * weights.cost +
            factor_scores[DecisionFactor.LATENCY] * weights.latency +
            factor_scores[DecisionFactor.QUALITY] * weights.quality +
            factor_scores[DecisionFactor.AVAILABILITY] * weights.availability +
            factor_scores[DecisionFactor.PRIVACY] * weights.privacy +
            factor_scores[DecisionFactor.USER_PREFERENCE] * weights.user_preference
        )
        
        # 計算信心度
        confidence = self._calculate_model_confidence(model, factor_scores, context)
        
        return ModelScore(
            model=model,
            total_score=total_score,
            factor_scores=factor_scores,
            cost_analysis=cost_analysis,
            performance_prediction=latency_analysis,
            confidence=confidence,
            reasoning=reasoning
        )
    
    async def _calculate_cost_score(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> Tuple[float, Dict[str, Any]]:
        """計算成本評分"""
        try:
            # 基礎成本計算
            estimated_tokens = context.routing_request.estimated_tokens
            input_tokens = estimated_tokens * 0.7  # 估算70%為輸入
            output_tokens = estimated_tokens * 0.3  # 估算30%為輸出
            
            input_cost = (input_tokens / 1000) * model.cost_per_1k_input_tokens
            output_cost = (output_tokens / 1000) * model.cost_per_1k_output_tokens
            total_cost = input_cost + output_cost
            
            # 獲取任務最大可接受成本
            max_cost = context.task_metadata.max_acceptable_cost_per_1k
            max_total_cost = (estimated_tokens / 1000) * max_cost
            
            # 計算成本評分（成本越低分數越高）
            if total_cost == 0:  # 免費模型
                cost_score = 1.0
            elif total_cost <= max_total_cost * 0.5:  # 成本在預算50%內
                cost_score = 1.0
            elif total_cost <= max_total_cost:  # 成本在預算內
                cost_score = 1.0 - (total_cost / max_total_cost) * 0.5
            else:  # 超出預算
                cost_score = max(0.0, 0.5 - (total_cost - max_total_cost) / max_total_cost)
            
            # 成本分析詳情
            cost_analysis = {
                'total_cost': round(total_cost, 6),
                'input_cost': round(input_cost, 6),
                'output_cost': round(output_cost, 6),
                'cost_per_1k_input': model.cost_per_1k_input_tokens,
                'cost_per_1k_output': model.cost_per_1k_output_tokens,
                'estimated_input_tokens': int(input_tokens),
                'estimated_output_tokens': int(output_tokens),
                'max_acceptable_cost': round(max_total_cost, 6),
                'cost_efficiency': round(cost_score, 3),
                'is_within_budget': total_cost <= max_total_cost,
                'reasoning': f"總成本 ${total_cost:.4f}, 預算 ${max_total_cost:.4f}"
            }
            
            return cost_score, cost_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Cost calculation error for {model.provider}/{model.model_id}: {e}")
            return 0.0, {'error': str(e), 'total_cost': 0.0}
    
    async def _calculate_latency_score(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> Tuple[float, Dict[str, Any]]:
        """計算延遲評分"""
        try:
            # 獲取歷史性能數據
            performance_data = await self._get_model_performance_data(model)
            
            # 使用歷史數據或模型默認延遲
            if performance_data and 'avg_latency' in performance_data:
                predicted_latency = performance_data['avg_latency']
                confidence = 0.9
            else:
                predicted_latency = model.avg_latency_ms
                confidence = 0.6
            
            # 基於任務複雜度調整延遲預測
            token_complexity_factor = min(2.0, context.routing_request.estimated_tokens / 1000)
            adjusted_latency = predicted_latency * (1 + token_complexity_factor * 0.1)
            
            # 獲取任務最大可接受延遲
            max_latency = context.task_metadata.max_acceptable_latency_ms
            
            # 計算延遲評分
            if adjusted_latency <= max_latency * 0.5:  # 延遲在限制50%內
                latency_score = 1.0
            elif adjusted_latency <= max_latency:  # 延遲在限制內
                latency_score = 1.0 - (adjusted_latency / max_latency) * 0.5
            else:  # 超出延遲限制
                latency_score = max(0.0, 0.5 - (adjusted_latency - max_latency) / max_latency)
            
            latency_analysis = {
                'predicted_latency_ms': round(adjusted_latency, 2),
                'base_latency_ms': model.avg_latency_ms,
                'max_acceptable_latency_ms': max_latency,
                'complexity_factor': round(token_complexity_factor, 2),
                'confidence': confidence,
                'is_within_limit': adjusted_latency <= max_latency,
                'performance_data_available': performance_data is not None
            }
            
            return latency_score, latency_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Latency calculation error for {model.provider}/{model.model_id}: {e}")
            return 0.0, {'error': str(e)}
    
    def _calculate_quality_score(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> float:
        """計算品質評分"""
        try:
            # 基礎品質評分
            base_score = model.capability_score
            
            # 根據任務要求調整
            min_required = context.task_metadata.min_model_capability_score
            if base_score >= min_required:
                # 超出最低要求的額外加分
                quality_score = min(1.0, base_score + (base_score - min_required) * 0.1)
            else:
                # 不滿足最低要求
                quality_score = base_score * 0.5
            
            # 基於歷史品質表現調整
            performance_data = self.model_performance_cache.get(f"{model.provider}/{model.model_id}")
            if performance_data and 'avg_quality' in performance_data:
                historical_quality = performance_data['avg_quality']
                # 結合歷史表現（70%當前模型能力 + 30%歷史表現）
                quality_score = quality_score * 0.7 + historical_quality * 0.3
            
            return min(1.0, max(0.0, quality_score))
            
        except Exception as e:
            self.logger.error(f"❌ Quality calculation error: {e}")
            return 0.5
    
    async def _calculate_availability_score(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> float:
        """計算可用性評分"""
        try:
            # 基礎可用性（模型本身是否可用）
            if not model.is_available:
                return 0.0
            
            base_availability = 0.8  # 基礎可用性評分
            
            # 獲取歷史成功率
            performance_data = await self._get_model_performance_data(model)
            if performance_data and 'success_rate' in performance_data:
                historical_success_rate = performance_data['success_rate']
                base_availability = historical_success_rate
            
            # 考慮負載平衡
            if self.config.get('enable_load_balancing'):
                load_factor = await self._calculate_load_factor(model)
                availability_score = base_availability * load_factor
            else:
                availability_score = base_availability
            
            return min(1.0, max(0.0, availability_score))
            
        except Exception as e:
            self.logger.error(f"❌ Availability calculation error: {e}")
            return 0.5
    
    def _calculate_privacy_score(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> float:
        """計算隱私評分"""
        try:
            task_sensitivity = context.task_metadata.data_sensitivity_level
            model_privacy = model.privacy_level
            requires_local = context.task_metadata.requires_local_processing
            
            # 隱私匹配度評分
            if requires_local:
                return 1.0 if model_privacy == 'local' else 0.0
            
            privacy_scores = {
                ('low', 'cloud'): 1.0,
                ('low', 'hybrid'): 0.9,
                ('low', 'local'): 1.0,
                ('medium', 'cloud'): 0.7,
                ('medium', 'hybrid'): 0.9,
                ('medium', 'local'): 1.0,
                ('high', 'cloud'): 0.0 if not context.task_metadata.allow_cloud_fallback else 0.3,
                ('high', 'hybrid'): 0.6,
                ('high', 'local'): 1.0,
                ('confidential', 'cloud'): 0.0,
                ('confidential', 'hybrid'): 0.0,
                ('confidential', 'local'): 1.0
            }
            
            return privacy_scores.get((task_sensitivity, model_privacy), 0.5)
            
        except Exception as e:
            self.logger.error(f"❌ Privacy calculation error: {e}")
            return 0.5
    
    def _calculate_user_preference_score(
        self,
        model: ModelCapabilityResponse,
        context: RoutingContext
    ) -> float:
        """計算用戶偏好評分"""
        try:
            preferences = context.user_context.get('preferences', {})
            score = 0.5  # 基礎中性評分
            
            # 提供商偏好
            preferred_provider = preferences.get('preferred_provider')
            if preferred_provider:
                if model.provider == preferred_provider:
                    score += 0.3
                elif model.provider in preferences.get('avoided_providers', []):
                    score -= 0.3
            
            # 模型類型偏好
            preferred_model_type = preferences.get('preferred_model_type')
            if preferred_model_type and preferred_model_type.lower() in model.model_name.lower():
                score += 0.2
            
            # 歷史使用偏好（可以基於用戶歷史使用數據）
            historical_preference = preferences.get('historical_preference', {})
            model_key = f"{model.provider}/{model.model_id}"
            if model_key in historical_preference:
                historical_score = historical_preference[model_key]
                score = score * 0.7 + historical_score * 0.3
            
            return min(1.0, max(0.0, score))
            
        except Exception as e:
            self.logger.error(f"❌ User preference calculation error: {e}")
            return 0.5
    
    def _calculate_model_confidence(
        self,
        model: ModelCapabilityResponse,
        factor_scores: Dict[DecisionFactor, float],
        context: RoutingContext
    ) -> float:
        """計算模型選擇信心度"""
        try:
            # 基於各因子評分的穩定性計算信心度
            scores = list(factor_scores.values())
            
            if not scores:
                return 0.5
            
            # 評分的平均值和標準差
            avg_score = statistics.mean(scores)
            if len(scores) > 1:
                score_variance = statistics.variance(scores)
                stability = 1.0 / (1.0 + score_variance)
            else:
                stability = 0.8
            
            # 基礎信心度
            base_confidence = avg_score * stability
            
            # 根據歷史表現調整信心度
            performance_data = self.model_performance_cache.get(f"{model.provider}/{model.model_id}")
            if performance_data:
                requests_count = performance_data.get('total_requests', 0)
                # 更多歷史數據 = 更高信心
                experience_factor = min(1.0, requests_count / 100)
                base_confidence = base_confidence * 0.8 + experience_factor * 0.2
            
            return min(1.0, max(0.0, base_confidence))
            
        except Exception as e:
            self.logger.error(f"❌ Confidence calculation error: {e}")
            return 0.5
    
    def _select_optimal_model(
        self,
        model_scores: List[ModelScore],
        weights: RoutingWeights
    ) -> ModelScore:
        """選擇最優模型"""
        if not model_scores:
            raise RoutingDecisionError("No model scores available for selection")
        
        # 過濾掉信心度過低的模型
        confidence_threshold = self.config.get('decision_confidence_threshold', 0.7)
        qualified_models = [
            score for score in model_scores 
            if score.confidence >= confidence_threshold
        ]
        
        # 如果沒有滿足信心度的模型，使用最高分的模型
        if not qualified_models:
            self.logger.warning("⚠️ No models meet confidence threshold, using best available")
            qualified_models = model_scores[:1]
        
        # 選擇最高總分的模型
        best_model = max(qualified_models, key=lambda x: x.total_score)
        
        return best_model
    
    # ==================== 決策響應和審計 ====================
    
    async def _generate_decision_response(
        self,
        best_model_score: ModelScore,
        all_model_scores: List[ModelScore],
        context: RoutingContext
    ) -> RoutingDecisionResponse:
        """生成路由決策響應"""
        try:
            selected_model = best_model_score.model
            
            # 生成決策推理
            decision_reasoning = self._generate_detailed_reasoning(
                best_model_score, all_model_scores, context
            )
            
            # 計算期望成本
            expected_cost = best_model_score.cost_analysis.get('total_cost', 0.0)
            
            # 計算期望延遲
            expected_latency = best_model_score.performance_prediction.get('predicted_latency_ms', 0.0)
            
            # 獲取後備選項
            fallback_options = self._generate_fallback_options(all_model_scores, best_model_score)
            
            # 決策元數據
            decision_metadata = {
                'routing_strategy': context.strategy.value,
                'weights_used': asdict(context.weights),
                'total_candidates_evaluated': len(all_model_scores),
                'decision_factors': {
                    factor.value: score 
                    for factor, score in best_model_score.factor_scores.items()
                },
                'cost_analysis': best_model_score.cost_analysis,
                'performance_prediction': best_model_score.performance_prediction,
                'model_reasoning': best_model_score.reasoning,
                'decision_timestamp': context.timestamp.isoformat(),
                'request_id': context.request_id
            }
            
            return RoutingDecisionResponse(
                selected_provider=selected_model.provider,
                selected_model=selected_model.model_id,
                reasoning=decision_reasoning,
                expected_cost=expected_cost,
                expected_latency_ms=int(expected_latency),
                expected_quality_score=selected_model.capability_score,
                confidence_score=best_model_score.confidence,
                fallback_options=fallback_options,
                decision_metadata=decision_metadata
            )
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate decision response: {e}")
            raise RoutingDecisionError(f"Failed to generate decision response: {e}")
    
    def _generate_detailed_reasoning(
        self,
        best_model_score: ModelScore,
        all_model_scores: List[ModelScore],
        context: RoutingContext
    ) -> str:
        """生成詳細決策推理"""
        reasoning_parts = []
        
        # 策略說明
        strategy_desc = {
            RoutingStrategy.COST_OPTIMIZED: "成本優化策略：優先選擇成本最低的模型",
            RoutingStrategy.PERFORMANCE_OPTIMIZED: "性能優化策略：優先選擇延遲最低、品質最高的模型",
            RoutingStrategy.BALANCED: "平衡策略：在成本、性能、品質間尋求最佳平衡",
            RoutingStrategy.QUALITY_FIRST: "品質優先策略：優先選擇能力評分最高的模型",
            RoutingStrategy.LATENCY_FIRST: "延遲優先策略：優先選擇響應最快的模型",
            RoutingStrategy.PRIVACY_FIRST: "隐私優先策略：優先選擇本地或高隱私模型"
        }
        
        reasoning_parts.append(
            strategy_desc.get(context.strategy, f"使用策略: {context.strategy.value}")
        )
        
        # 模型選擇原因
        selected_model = best_model_score.model
        reasoning_parts.append(
            f"選擇模型 {selected_model.provider}/{selected_model.model_id} "
            f"(總分: {best_model_score.total_score:.3f}, 信心度: {best_model_score.confidence:.3f})"
        )
        
        # 關鍵決策因子
        top_factors = sorted(
            best_model_score.factor_scores.items(),
            key=lambda x: x[1] * getattr(context.weights, x[0].value.lower()),
            reverse=True
        )[:3]
        
        reasoning_parts.append("主要決策因子:")
        for factor, score in top_factors:
            weight = getattr(context.weights, factor.value.lower())
            weighted_score = score * weight
            reasoning_parts.append(f"• {factor.value}: 評分 {score:.3f} (權重 {weight:.2f}, 加權分 {weighted_score:.3f})")
        
        # 與其他候選模型比較
        if len(all_model_scores) > 1:
            second_best = all_model_scores[1] if len(all_model_scores) > 1 else None
            if second_best:
                score_diff = best_model_score.total_score - second_best.total_score
                reasoning_parts.append(
                    f"相比次優選項 {second_best.model.provider}/{second_best.model.model_id}, "
                    f"領先 {score_diff:.3f} 分"
                )
        
        return "; ".join(reasoning_parts)
    
    def _generate_fallback_options(
        self,
        all_model_scores: List[ModelScore],
        selected_model_score: ModelScore
    ) -> List[Dict[str, str]]:
        """生成後備選項"""
        fallback_options = []
        
        # 排除已選擇的模型，選擇前3個作為後備
        other_models = [
            score for score in all_model_scores 
            if score.model.id != selected_model_score.model.id
        ]
        
        for model_score in other_models[:3]:
            model = model_score.model
            reason_parts = []
            
            # 生成後備理由
            if model_score.factor_scores.get(DecisionFactor.COST, 0) > 0.8:
                reason_parts.append("低成本")
            if model_score.factor_scores.get(DecisionFactor.LATENCY, 0) > 0.8:
                reason_parts.append("低延遲")
            if model_score.factor_scores.get(DecisionFactor.QUALITY, 0) > 0.8:
                reason_parts.append("高品質")
            if model.privacy_level == 'local':
                reason_parts.append("本地部署")
            
            reason = "、".join(reason_parts) if reason_parts else f"綜合評分 {model_score.total_score:.3f}"
            
            fallback_options.append({
                'provider': model.provider,
                'model': model.model_id,
                'reason': f"後備選項 - {reason}"
            })
        
        return fallback_options
    
    async def _record_decision_audit(
        self,
        decision_response: RoutingDecisionResponse,
        all_model_scores: List[ModelScore],
        context: RoutingContext,
        execution_time_ms: float
    ):
        """記錄決策審計"""
        try:
            if not self.config.get('enable_audit_logging', True):
                return
            
            # 找到選中的模型評分
            selected_model_score = None
            for score in all_model_scores:
                if (score.model.provider == decision_response.selected_provider and 
                    score.model.model_id == decision_response.selected_model):
                    selected_model_score = score
                    break
            
            if not selected_model_score:
                self.logger.error("❌ Could not find selected model score for audit")
                return
            
            # 生成後備鏈
            fallback_chain = [
                f"{option['provider']}/{option['model']}"
                for option in decision_response.fallback_options
            ]
            
            # 創建審計記錄
            audit_record = DecisionAudit(
                decision_id=str(uuid.uuid4()),
                request_id=context.request_id,
                task_type=context.task_metadata.task_type,
                selected_model=selected_model_score.model,
                all_model_scores=all_model_scores,
                routing_context=context,
                decision_reasoning=decision_response.reasoning.split("; "),
                confidence_score=decision_response.confidence_score,
                execution_time_ms=execution_time_ms,
                fallback_chain=fallback_chain
            )
            
            # 存儲審計記錄
            self.decision_history.append(audit_record)
            
            # 維護歷史記錄大小
            if len(self.decision_history) > self.max_history_size:
                self.decision_history = self.decision_history[-self.max_history_size:]
            
            # 詳細審計日誌
            if self.config.get('audit_detail_level') == 'full':
                self.logger.info(f"📝 Decision audit recorded: {audit_record.decision_id}")
                if self.logger.isEnabledFor(logging.DEBUG):
                    audit_dict = audit_record.to_dict()
                    self.logger.debug(f"📋 Full audit details: {json.dumps(audit_dict, indent=2, ensure_ascii=False)}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record decision audit: {e}")
    
    # ==================== 輔助工具方法 ====================
    
    async def _get_model_performance_data(
        self,
        model: ModelCapabilityResponse
    ) -> Optional[Dict[str, Any]]:
        """獲取模型歷史性能數據"""
        model_key = f"{model.provider}/{model.model_id}"
        
        # 檢查緩存
        cached_data = self.model_performance_cache.get(model_key)
        if cached_data:
            last_updated = cached_data.get('last_updated')
            if last_updated and (datetime.now(timezone.utc) - last_updated).seconds < self.cache_ttl_seconds:
                return cached_data
        
        # 從性能監控器獲取數據
        if self.performance_monitor:
            try:
                report = await self.performance_monitor.get_performance_report(
                    provider=model.provider,
                    model_id=model.model_id,
                    hours_back=24
                )
                
                if report and 'provider_performance' in report:
                    performance_data = report['provider_performance'].get(model_key, {})
                    if performance_data:
                        # 更新緩存
                        performance_data['last_updated'] = datetime.now(timezone.utc)
                        self.model_performance_cache[model_key] = performance_data
                        return performance_data
                        
            except Exception as e:
                self.logger.debug(f"Could not get performance data for {model_key}: {e}")
        
        return None
    
    async def _calculate_load_factor(self, model: ModelCapabilityResponse) -> float:
        """計算模型負載因子"""
        try:
            # 簡化的負載計算 - 可以基於實際請求計數、隊列長度等
            model_key = f"{model.provider}/{model.model_id}"
            
            # 檢查最近的使用頻率
            recent_selections = sum(
                1 for audit in self.decision_history[-50:]  # 最近50個決策
                if f"{audit.selected_model.provider}/{audit.selected_model.model_id}" == model_key
            )
            
            # 負載因子：使用頻率越高，因子越低
            if recent_selections == 0:
                return 1.0  # 未使用，最高優先
            elif recent_selections <= 5:
                return 0.9
            elif recent_selections <= 15:
                return 0.8
            else:
                return 0.6  # 高負載，降低優先級
                
        except Exception as e:
            self.logger.debug(f"Load factor calculation error: {e}")
            return 0.8  # 預設中等負載因子
    
    def _update_performance_stats(self, execution_time_ms: float):
        """更新性能統計"""
        # 更新平均決策時間
        current_avg = self.stats['average_decision_time_ms']
        total_decisions = self.stats['total_decisions']
        
        if total_decisions > 1:
            self.stats['average_decision_time_ms'] = (
                (current_avg * (total_decisions - 1) + execution_time_ms) / total_decisions
            )
        else:
            self.stats['average_decision_time_ms'] = execution_time_ms
    
    # ==================== 配置和管理接口 ====================
    
    def update_strategy_weights(
        self,
        strategy: RoutingStrategy,
        weights: RoutingWeights
    ) -> bool:
        """動態更新路由策略權重"""
        try:
            weights.normalize()
            self.routing_strategies[strategy] = weights
            self.logger.info(f"✅ Updated weights for strategy {strategy.value}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to update strategy weights: {e}")
            return False
    
    def add_custom_strategy(
        self,
        name: str,
        weights: RoutingWeights
    ) -> bool:
        """添加自定義路由策略"""
        try:
            weights.normalize()
            custom_strategy = RoutingStrategy(name)  # 這會創建動態枚舉值
            self.routing_strategies[custom_strategy] = weights
            self.stats['strategy_usage'][name] = 0
            self.logger.info(f"✅ Added custom strategy: {name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to add custom strategy: {e}")
            return False
    
    def get_decision_history(
        self,
        limit: int = 50,
        task_type: Optional[str] = None,
        provider: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """獲取決策歷史"""
        try:
            # 過濾條件
            filtered_history = self.decision_history
            
            if task_type:
                filtered_history = [
                    audit for audit in filtered_history 
                    if audit.task_type == task_type
                ]
            
            if provider:
                filtered_history = [
                    audit for audit in filtered_history 
                    if audit.selected_model.provider == provider
                ]
            
            # 限制數量並轉換為字典
            recent_history = filtered_history[-limit:] if filtered_history else []
            return [audit.to_dict() for audit in recent_history]
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get decision history: {e}")
            return []
    
    def get_routing_statistics(self) -> Dict[str, Any]:
        """獲取路由統計信息"""
        try:
            # 計算模型選擇頻率
            model_frequency = {}
            for audit in self.decision_history:
                model_key = f"{audit.selected_model.provider}/{audit.selected_model.model_id}"
                model_frequency[model_key] = model_frequency.get(model_key, 0) + 1
            
            # 計算平均信心度
            confidence_scores = [audit.confidence_score for audit in self.decision_history]
            avg_confidence = statistics.mean(confidence_scores) if confidence_scores else 0.0
            
            stats = self.stats.copy()
            stats.update({
                'model_selection_frequency': model_frequency,
                'average_confidence_score': round(avg_confidence, 3),
                'total_audit_records': len(self.decision_history),
                'strategy_distribution': {
                    strategy: count for strategy, count in self.stats['strategy_usage'].items()
                    if count > 0
                },
                'performance_cache_size': len(self.model_performance_cache),
                'uptime_seconds': (datetime.now(timezone.utc) - self.stats['last_reset']).total_seconds()
            })
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get routing statistics: {e}")
            return self.stats.copy()
    
    def reset_statistics(self):
        """重置統計信息"""
        self.stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'failed_decisions': 0,
            'average_decision_time_ms': 0.0,
            'strategy_usage': {strategy.value: 0 for strategy in RoutingStrategy},
            'model_selection_frequency': {},
            'cost_savings': 0.0,
            'last_reset': datetime.now(timezone.utc)
        }
        self.decision_history.clear()
        self.logger.info("✅ Routing statistics reset")
    
    async def health_check(self) -> Dict[str, Any]:
        """路由器健康檢查"""
        health_status = {
            'router_initialized': self._initialized,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'statistics': self.get_routing_statistics(),
            'configuration': {
                'strategies_available': len(self.routing_strategies),
                'default_strategy': self.default_strategy.value,
                'audit_logging_enabled': self.config.get('enable_audit_logging', True),
                'performance_learning_enabled': self.config.get('enable_performance_learning', True),
                'load_balancing_enabled': self.config.get('enable_load_balancing', True)
            },
            'components_status': {}
        }
        
        try:
            # 檢查任務數據庫
            task_metadata = await self.task_db.list_task_metadata(limit=1)
            health_status['components_status']['task_db'] = {
                'status': 'healthy',
                'task_types_available': len(task_metadata)
            }
        except Exception as e:
            health_status['components_status']['task_db'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        try:
            # 檢查模型數據庫
            models = await self.model_db.list_model_capabilities(limit=1)
            health_status['components_status']['model_db'] = {
                'status': 'healthy',
                'models_available': len(models)
            }
        except Exception as e:
            health_status['components_status']['model_db'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # 檢查性能監控器
        if self.performance_monitor:
            health_status['components_status']['performance_monitor'] = {
                'status': 'available',
                'cache_size': len(self.model_performance_cache)
            }
        else:
            health_status['components_status']['performance_monitor'] = {
                'status': 'not_configured'
            }
        
        # 整體健康狀態
        component_statuses = [
            comp.get('status', 'unknown') 
            for comp in health_status['components_status'].values()
        ]
        
        if all(status in ['healthy', 'available', 'not_configured'] for status in component_statuses):
            health_status['overall_status'] = 'healthy'
        else:
            health_status['overall_status'] = 'degraded'
        
        return health_status