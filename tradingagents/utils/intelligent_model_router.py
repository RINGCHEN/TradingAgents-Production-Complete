#!/usr/bin/env python3
"""
智能模型路由器
GPT-OSS 整合任务 1.2.2 - LLMClient智能路由系统集成

基于模型能力评分和任务特征进行智能模型选择和负载均衡。
与ModelCapabilityDB和性能监控系统深度集成。
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

from ..database.model_capability_db import (
    ModelCapabilityDB, ModelCapabilitySearch, ModelCapabilityResponse
)
from ..monitoring.model_performance_monitor import (
    ModelPerformanceMonitor, MetricType
)
from .llm_client import (
    LLMClient, LLMProvider, LLMRequest, LLMResponse, AnalysisType
)

# 设置日志
logger = logging.getLogger(__name__)

class RoutingStrategy(str, Enum):
    """路由策略类型"""
    CAPABILITY_BASED = "capability_based"  # 基于能力评分
    COST_OPTIMIZED = "cost_optimized"     # 成本优化
    LATENCY_OPTIMIZED = "latency_optimized"  # 延迟优化
    LOAD_BALANCED = "load_balanced"       # 负载均衡
    FAILOVER = "failover"                # 故障转移
    HYBRID = "hybrid"                    # 混合策略

class TaskComplexity(str, Enum):
    """任务复杂度"""
    SIMPLE = "simple"      # 简单任务
    MODERATE = "moderate"   # 中等复杂度
    COMPLEX = "complex"     # 复杂任务
    EXPERT = "expert"      # 专家级任务

class UserTier(str, Enum):
    """用户等级"""
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    VIP = "vip"

@dataclass
class RoutingContext:
    """路由上下文信息"""
    analysis_type: AnalysisType
    task_complexity: TaskComplexity = TaskComplexity.MODERATE
    user_tier: UserTier = UserTier.FREE
    max_latency_ms: Optional[int] = None
    max_cost_per_request: Optional[float] = None
    quality_threshold: float = 0.7
    require_local_processing: bool = False
    preferred_providers: Optional[List[str]] = None
    fallback_enabled: bool = True
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ModelCandidate:
    """候选模型信息"""
    provider: str
    model_id: str
    model_name: str
    capability_score: float
    estimated_cost: float
    estimated_latency_ms: float
    quality_score: float
    availability_score: float
    confidence_score: float  # 综合评估置信度
    selection_reason: str
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RoutingDecision:
    """路由决策结果"""
    selected_provider: str
    selected_model: str
    selection_confidence: float
    estimated_cost: float
    estimated_latency_ms: float
    estimated_quality: float
    fallback_models: List[ModelCandidate]
    routing_strategy_used: RoutingStrategy
    decision_factors: Dict[str, float]
    reasoning: str
    timestamp: datetime

class IntelligentModelRouter:
    """智能模型路由器
    
    提供基于多维度评估的智能模型选择功能：
    - 能力评分匹配
    - 成本效益分析
    - 性能预测
    - 负载均衡
    - 故障转移
    - 用户等级适配
    """
    
    def __init__(
        self,
        model_capability_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[ModelPerformanceMonitor] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """初始化智能路由器
        
        Args:
            model_capability_db: 模型能力数据库
            performance_monitor: 性能监控器
            llm_client: LLM客户端
        """
        self.model_capability_db = model_capability_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor
        self.llm_client = llm_client
        
        # 路由配置
        self.default_strategy = RoutingStrategy.HYBRID
        self.capability_weight = 0.3
        self.cost_weight = 0.25
        self.latency_weight = 0.25
        self.availability_weight = 0.2
        
        # 缓存配置
        self.routing_cache_enabled = True
        self.cache_ttl_seconds = 300  # 5分钟缓存
        self._routing_cache: Dict[str, RoutingDecision] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # 统计信息
        self.total_routing_requests = 0
        self.cache_hits = 0
        self.successful_routings = 0
        self.failed_routings = 0
        self.last_routing_time: Optional[datetime] = None
        
        # 用户等级配置
        self.tier_config = self._initialize_tier_config()
        
        logger.info("智能模型路由器初始化完成")
    
    def _initialize_tier_config(self) -> Dict[UserTier, Dict[str, Any]]:
        """初始化用户等级配置"""
        return {
            UserTier.FREE: {
                "max_cost_per_request": 0.01,
                "max_latency_ms": 10000,
                "min_capability_score": 0.5,
                "allowed_providers": ["gpt_oss"],
                "priority_bonus": 0.0
            },
            UserTier.PREMIUM: {
                "max_cost_per_request": 0.05,
                "max_latency_ms": 5000,
                "min_capability_score": 0.6,
                "allowed_providers": ["gpt_oss", "openai"],
                "priority_bonus": 0.1
            },
            UserTier.ENTERPRISE: {
                "max_cost_per_request": 0.15,
                "max_latency_ms": 3000,
                "min_capability_score": 0.7,
                "allowed_providers": ["gpt_oss", "openai", "anthropic"],
                "priority_bonus": 0.2
            },
            UserTier.VIP: {
                "max_cost_per_request": None,  # 无限制
                "max_latency_ms": 2000,
                "min_capability_score": 0.8,
                "allowed_providers": ["gpt_oss", "openai", "anthropic"],
                "priority_bonus": 0.3
            }
        }
    
    # ==================== 核心路由功能 ====================
    
    async def route_request(
        self,
        request: LLMRequest,
        routing_context: Optional[RoutingContext] = None,
        strategy: Optional[RoutingStrategy] = None
    ) -> RoutingDecision:
        """执行智能路由决策
        
        Args:
            request: LLM请求
            routing_context: 路由上下文
            strategy: 路由策略，如果为None则使用默认策略
            
        Returns:
            路由决策结果
        """
        start_time = time.time()
        self.total_routing_requests += 1
        
        # 使用默认上下文如果未提供
        if routing_context is None:
            routing_context = RoutingContext(
                analysis_type=request.analysis_type,
                task_complexity=self._infer_task_complexity(request)
            )
        
        # 使用默认策略如果未提供
        if strategy is None:
            strategy = self.default_strategy
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(request, routing_context, strategy)
            if self.routing_cache_enabled and self._is_cache_valid(cache_key):
                self.cache_hits += 1
                cached_decision = self._routing_cache[cache_key]
                logger.debug(f"使用缓存的路由决策: {cached_decision.selected_provider}/{cached_decision.selected_model}")
                return cached_decision
            
            # 获取候选模型
            candidates = await self._get_model_candidates(routing_context)
            if not candidates:
                raise Exception("没有找到符合条件的候选模型")
            
            # 执行路由决策
            decision = await self._make_routing_decision(
                candidates, routing_context, strategy
            )
            
            # 记录决策时间
            decision_time = time.time() - start_time
            decision.metadata = decision.metadata or {}
            decision.metadata['decision_time_ms'] = decision_time * 1000
            
            # 缓存决策结果
            if self.routing_cache_enabled:
                self._cache_routing_decision(cache_key, decision)
            
            # 更新统计
            self.successful_routings += 1
            self.last_routing_time = datetime.now(timezone.utc)
            
            logger.info(f"路由决策完成: {decision.selected_provider}/{decision.selected_model} "
                       f"(置信度: {decision.selection_confidence:.2f}, "
                       f"耗时: {decision_time*1000:.1f}ms)")
            
            return decision
            
        except Exception as e:
            self.failed_routings += 1
            logger.error(f"路由决策失败: {e}")
            
            # 返回默认的故障转移决策
            return self._create_fallback_decision(e)
    
    async def _get_model_candidates(
        self, 
        routing_context: RoutingContext
    ) -> List[ModelCandidate]:
        """获取候选模型列表"""
        
        # 构建搜索条件
        search_criteria = ModelCapabilitySearch(
            min_capability_score=max(
                routing_context.quality_threshold,
                self.tier_config[routing_context.user_tier]["min_capability_score"]
            ),
            is_available=True
        )
        
        # 应用用户等级限制
        tier_config = self.tier_config[routing_context.user_tier]
        if tier_config["max_cost_per_request"]:
            search_criteria.max_cost_per_1k = tier_config["max_cost_per_request"] * 50  # 假设50 token平均
        
        if routing_context.max_latency_ms:
            search_criteria.max_latency_ms = min(
                routing_context.max_latency_ms,
                tier_config["max_latency_ms"]
            )
        else:
            search_criteria.max_latency_ms = tier_config["max_latency_ms"]
        
        # 隐私要求
        if routing_context.require_local_processing:
            search_criteria.privacy_level = "local"
        
        # 特定提供商偏好
        if routing_context.preferred_providers:
            allowed_providers = set(routing_context.preferred_providers) & set(tier_config["allowed_providers"])
        else:
            allowed_providers = set(tier_config["allowed_providers"])
        
        # 查询候选模型
        all_candidates = []
        for provider in allowed_providers:
            search_criteria.provider = provider
            models = await self.model_capability_db.search_models(
                search_criteria, limit=10, order_by="capability_score", ascending=False
            )
            
            for model in models:
                candidate = await self._evaluate_model_candidate(model, routing_context)
                if candidate:
                    all_candidates.append(candidate)
        
        # 按置信度排序
        all_candidates.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return all_candidates[:20]  # 返回前20个候选模型
    
    async def _evaluate_model_candidate(
        self,
        model: ModelCapabilityResponse,
        routing_context: RoutingContext
    ) -> Optional[ModelCandidate]:
        """评估单个候选模型"""
        
        try:
            # 基础能力评估
            capability_score = model.capability_score
            
            # 任务类型匹配度
            task_match_score = self._calculate_task_match_score(
                model, routing_context.analysis_type
            )
            
            # 成本估算
            estimated_cost = self._estimate_request_cost(model, routing_context)
            
            # 延迟估算
            estimated_latency = await self._estimate_request_latency(model, routing_context)
            
            # 可用性评估
            availability_score = await self._assess_model_availability(model)
            
            # 质量预测
            quality_score = self._predict_quality_score(model, routing_context)
            
            # 综合置信度计算
            confidence_score = self._calculate_confidence_score(
                capability_score, task_match_score, availability_score,
                estimated_cost, estimated_latency, routing_context
            )
            
            # 选择理由
            selection_reason = self._generate_selection_reason(
                model, capability_score, task_match_score, estimated_cost, estimated_latency
            )
            
            return ModelCandidate(
                provider=model.provider,
                model_id=model.model_id,
                model_name=model.model_name,
                capability_score=capability_score,
                estimated_cost=estimated_cost,
                estimated_latency_ms=estimated_latency,
                quality_score=quality_score,
                availability_score=availability_score,
                confidence_score=confidence_score,
                selection_reason=selection_reason,
                metadata={
                    "task_match_score": task_match_score,
                    "context_length": model.context_length,
                    "supported_features": model.supported_features,
                    "privacy_level": model.privacy_level
                }
            )
            
        except Exception as e:
            logger.error(f"评估候选模型失败 {model.provider}/{model.model_id}: {e}")
            return None
    
    def _calculate_task_match_score(
        self, 
        model: ModelCapabilityResponse, 
        analysis_type: AnalysisType
    ) -> float:
        """计算任务匹配度"""
        
        # 基于分析类型的模型适配度
        type_score_mapping = {
            AnalysisType.TECHNICAL: {
                "reasoning_score": 0.4,
                "accuracy_score": 0.4,
                "speed_score": 0.2
            },
            AnalysisType.FUNDAMENTAL: {
                "reasoning_score": 0.3,
                "accuracy_score": 0.5,
                "creativity_score": 0.2
            },
            AnalysisType.NEWS: {
                "accuracy_score": 0.4,
                "creativity_score": 0.3,
                "speed_score": 0.3
            },
            AnalysisType.SENTIMENT: {
                "accuracy_score": 0.5,
                "reasoning_score": 0.3,
                "creativity_score": 0.2
            },
            AnalysisType.RISK: {
                "reasoning_score": 0.5,
                "accuracy_score": 0.4,
                "speed_score": 0.1
            },
            AnalysisType.INVESTMENT: {
                "reasoning_score": 0.4,
                "creativity_score": 0.3,
                "accuracy_score": 0.3
            }
        }
        
        weights = type_score_mapping.get(analysis_type, {
            "reasoning_score": 0.25,
            "accuracy_score": 0.25,
            "creativity_score": 0.25,
            "speed_score": 0.25
        })
        
        match_score = 0.0
        total_weight = 0.0
        
        for score_field, weight in weights.items():
            score_value = getattr(model, score_field, None)
            if score_value is not None:
                match_score += score_value * weight
                total_weight += weight
        
        if total_weight > 0:
            match_score /= total_weight
        else:
            match_score = model.capability_score  # 回退到总体能力评分
        
        return match_score
    
    def _estimate_request_cost(
        self, 
        model: ModelCapabilityResponse, 
        routing_context: RoutingContext
    ) -> float:
        """估算请求成本"""
        
        # 基于复杂度估算token使用量
        token_estimates = {
            TaskComplexity.SIMPLE: 500,
            TaskComplexity.MODERATE: 1000,
            TaskComplexity.COMPLEX: 2000,
            TaskComplexity.EXPERT: 4000
        }
        
        estimated_tokens = token_estimates[routing_context.task_complexity]
        
        # 计算输入输出token成本（假设输出token为输入的一半）
        input_tokens = estimated_tokens * 0.7
        output_tokens = estimated_tokens * 0.3
        
        total_cost = (
            (input_tokens / 1000) * model.cost_per_1k_input_tokens +
            (output_tokens / 1000) * model.cost_per_1k_output_tokens
        )
        
        return total_cost
    
    async def _estimate_request_latency(
        self, 
        model: ModelCapabilityResponse, 
        routing_context: RoutingContext
    ) -> float:
        """估算请求延迟"""
        
        # 基础延迟（从模型数据）
        base_latency = model.avg_latency_ms
        
        # 复杂度调整因子
        complexity_factors = {
            TaskComplexity.SIMPLE: 0.7,
            TaskComplexity.MODERATE: 1.0,
            TaskComplexity.COMPLEX: 1.5,
            TaskComplexity.EXPERT: 2.0
        }
        
        complexity_factor = complexity_factors[routing_context.task_complexity]
        
        # 从性能监控器获取实时延迟数据
        if self.performance_monitor:
            try:
                summary = self.performance_monitor.get_performance_summary(
                    provider=model.provider, 
                    model_id=model.model_id, 
                    hours=1
                )
                
                latency_data = summary.get('metric_summaries', {}).get('latency')
                if latency_data and latency_data['count'] > 0:
                    real_time_latency = latency_data['average']
                    # 使用实时数据和模型数据的加权平均
                    base_latency = (base_latency * 0.3 + real_time_latency * 0.7)
            except:
                pass  # 使用模型基础延迟
        
        estimated_latency = base_latency * complexity_factor
        
        return estimated_latency
    
    async def _assess_model_availability(
        self, 
        model: ModelCapabilityResponse
    ) -> float:
        """评估模型可用性"""
        
        # 基础可用性
        if not model.is_available:
            return 0.0
        
        availability_score = 1.0
        
        # 从性能监控器获取可用性数据
        if self.performance_monitor:
            try:
                summary = self.performance_monitor.get_performance_summary(
                    provider=model.provider,
                    model_id=model.model_id,
                    hours=1
                )
                
                availability_data = summary.get('metric_summaries', {}).get('availability')
                if availability_data and availability_data['count'] > 0:
                    availability_score = availability_data['latest'] / 100.0  # 转换为0-1分值
                
                # 考虑错误率
                error_rate_data = summary.get('metric_summaries', {}).get('error_rate')
                if error_rate_data and error_rate_data['count'] > 0:
                    error_rate = error_rate_data['average'] / 100.0  # 转换为0-1
                    availability_score *= (1.0 - error_rate)
                    
            except:
                pass  # 使用基础可用性
        
        return max(0.0, min(1.0, availability_score))
    
    def _predict_quality_score(
        self, 
        model: ModelCapabilityResponse, 
        routing_context: RoutingContext
    ) -> float:
        """预测质量评分"""
        
        # 基于任务匹配度和历史能力评分预测质量
        task_match = self._calculate_task_match_score(model, routing_context.analysis_type)
        base_capability = model.capability_score
        
        # 加权平均
        predicted_quality = (task_match * 0.6 + base_capability * 0.4)
        
        # 考虑用户等级的质量提升
        tier_bonus = self.tier_config[routing_context.user_tier]["priority_bonus"]
        predicted_quality += tier_bonus
        
        return min(1.0, predicted_quality)
    
    def _calculate_confidence_score(
        self,
        capability_score: float,
        task_match_score: float,
        availability_score: float,
        estimated_cost: float,
        estimated_latency: float,
        routing_context: RoutingContext
    ) -> float:
        """计算综合置信度评分"""
        
        # 基础评分权重
        scores = {
            "capability": capability_score * self.capability_weight,
            "task_match": task_match_score * 0.3,
            "availability": availability_score * self.availability_weight
        }
        
        # 成本评分（成本越低越好）
        tier_config = self.tier_config[routing_context.user_tier]
        max_cost = tier_config["max_cost_per_request"] or 1.0
        cost_score = max(0.0, 1.0 - (estimated_cost / max_cost))
        scores["cost"] = cost_score * self.cost_weight
        
        # 延迟评分（延迟越低越好）
        max_latency = routing_context.max_latency_ms or tier_config["max_latency_ms"]
        latency_score = max(0.0, 1.0 - (estimated_latency / max_latency))
        scores["latency"] = latency_score * self.latency_weight
        
        # 计算综合评分
        confidence_score = sum(scores.values())
        
        # 标准化到0-1范围
        confidence_score = max(0.0, min(1.0, confidence_score))
        
        return confidence_score
    
    def _generate_selection_reason(
        self,
        model: ModelCapabilityResponse,
        capability_score: float,
        task_match_score: float,
        estimated_cost: float,
        estimated_latency: float
    ) -> str:
        """生成选择理由"""
        
        reasons = []
        
        if capability_score >= 0.8:
            reasons.append(f"高能力评分({capability_score:.2f})")
        elif capability_score >= 0.6:
            reasons.append(f"良好能力评分({capability_score:.2f})")
        
        if task_match_score >= 0.7:
            reasons.append("任务匹配度高")
        
        if estimated_cost <= 0.01:
            reasons.append("成本效益优秀")
        elif estimated_cost <= 0.05:
            reasons.append("成本合理")
        
        if estimated_latency <= 2000:
            reasons.append("响应速度快")
        elif estimated_latency <= 5000:
            reasons.append("响应速度适中")
        
        if model.privacy_level == "local":
            reasons.append("本地处理保护隐私")
        
        return "、".join(reasons) if reasons else "符合基础要求"
    
    # ==================== 路由策略实现 ====================
    
    async def _make_routing_decision(
        self,
        candidates: List[ModelCandidate],
        routing_context: RoutingContext,
        strategy: RoutingStrategy
    ) -> RoutingDecision:
        """根据策略制定路由决策"""
        
        if not candidates:
            raise Exception("没有可用的候选模型")
        
        # 根据策略选择最佳模型
        if strategy == RoutingStrategy.CAPABILITY_BASED:
            selected_candidate = self._select_by_capability(candidates)
            strategy_factors = {"capability": 1.0}
            
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            selected_candidate = self._select_by_cost(candidates)
            strategy_factors = {"cost": 1.0}
            
        elif strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            selected_candidate = self._select_by_latency(candidates)
            strategy_factors = {"latency": 1.0}
            
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            selected_candidate = await self._select_by_load_balance(candidates)
            strategy_factors = {"load_balance": 1.0}
            
        elif strategy == RoutingStrategy.FAILOVER:
            selected_candidate = self._select_by_failover(candidates)
            strategy_factors = {"failover": 1.0}
            
        else:  # HYBRID 或其他
            selected_candidate = self._select_by_hybrid(candidates, routing_context)
            strategy_factors = {
                "capability": self.capability_weight,
                "cost": self.cost_weight,
                "latency": self.latency_weight,
                "availability": self.availability_weight
            }
        
        # 生成故障转移候选列表
        fallback_models = [c for c in candidates if c != selected_candidate][:3]
        
        # 生成决策推理
        reasoning = self._generate_decision_reasoning(
            selected_candidate, candidates, strategy, routing_context
        )
        
        return RoutingDecision(
            selected_provider=selected_candidate.provider,
            selected_model=selected_candidate.model_id,
            selection_confidence=selected_candidate.confidence_score,
            estimated_cost=selected_candidate.estimated_cost,
            estimated_latency_ms=selected_candidate.estimated_latency_ms,
            estimated_quality=selected_candidate.quality_score,
            fallback_models=fallback_models,
            routing_strategy_used=strategy,
            decision_factors=strategy_factors,
            reasoning=reasoning,
            timestamp=datetime.now(timezone.utc)
        )
    
    def _select_by_capability(self, candidates: List[ModelCandidate]) -> ModelCandidate:
        """基于能力评分选择"""
        return max(candidates, key=lambda x: x.capability_score)
    
    def _select_by_cost(self, candidates: List[ModelCandidate]) -> ModelCandidate:
        """基于成本优化选择"""
        return min(candidates, key=lambda x: x.estimated_cost)
    
    def _select_by_latency(self, candidates: List[ModelCandidate]) -> ModelCandidate:
        """基于延迟优化选择"""
        return min(candidates, key=lambda x: x.estimated_latency_ms)
    
    async def _select_by_load_balance(self, candidates: List[ModelCandidate]) -> ModelCandidate:
        """基于负载均衡选择"""
        # 简化的负载均衡逻辑：选择可用性最高的模型
        return max(candidates, key=lambda x: x.availability_score)
    
    def _select_by_failover(self, candidates: List[ModelCandidate]) -> ModelCandidate:
        """基于故障转移选择"""
        # 优先选择可用性最高且质量不低的模型
        viable_candidates = [c for c in candidates if c.availability_score >= 0.8]
        if not viable_candidates:
            viable_candidates = candidates
        
        return max(viable_candidates, key=lambda x: (x.availability_score, x.quality_score))
    
    def _select_by_hybrid(
        self, 
        candidates: List[ModelCandidate], 
        routing_context: RoutingContext
    ) -> ModelCandidate:
        """基于混合策略选择"""
        # 使用置信度评分进行选择
        return max(candidates, key=lambda x: x.confidence_score)
    
    def _generate_decision_reasoning(
        self,
        selected_candidate: ModelCandidate,
        all_candidates: List[ModelCandidate],
        strategy: RoutingStrategy,
        routing_context: RoutingContext
    ) -> str:
        """生成决策推理说明"""
        
        reasoning_parts = []
        
        # 策略说明
        strategy_descriptions = {
            RoutingStrategy.CAPABILITY_BASED: "基于能力评分选择最优模型",
            RoutingStrategy.COST_OPTIMIZED: "优先考虑成本效益",
            RoutingStrategy.LATENCY_OPTIMIZED: "优先考虑响应速度",
            RoutingStrategy.LOAD_BALANCED: "基于负载均衡策略",
            RoutingStrategy.FAILOVER: "基于高可用性故障转移",
            RoutingStrategy.HYBRID: "基于综合评估的混合策略"
        }
        
        reasoning_parts.append(strategy_descriptions[strategy])
        
        # 选择优势
        reasoning_parts.append(f"选择{selected_candidate.provider}/{selected_candidate.model_name}")
        reasoning_parts.append(f"原因：{selected_candidate.selection_reason}")
        
        # 性能预期
        reasoning_parts.append(
            f"预期成本${selected_candidate.estimated_cost:.4f}，"
            f"响应时间{selected_candidate.estimated_latency_ms:.0f}ms，"
            f"质量评分{selected_candidate.quality_score:.2f}"
        )
        
        # 用户等级适配
        reasoning_parts.append(f"适配{routing_context.user_tier.value}用户等级")
        
        # 候选模型数量
        reasoning_parts.append(f"从{len(all_candidates)}个候选模型中选择")
        
        return "；".join(reasoning_parts)
    
    # ==================== 执行LLM请求 ====================
    
    async def execute_routed_request(
        self,
        request: LLMRequest,
        routing_decision: Optional[RoutingDecision] = None,
        routing_context: Optional[RoutingContext] = None
    ) -> LLMResponse:
        """执行路由决策后的LLM请求
        
        Args:
            request: LLM请求
            routing_decision: 路由决策，如果为None则自动路由
            routing_context: 路由上下文
            
        Returns:
            LLM响应
        """
        
        # 如果没有路由决策，先执行路由
        if routing_decision is None:
            routing_decision = await self.route_request(request, routing_context)
        
        try:
            # 记录路由决策执行
            logger.info(f"执行路由决策: {routing_decision.selected_provider}/{routing_decision.selected_model}")
            
            # 确保LLM客户端可用
            if not self.llm_client:
                raise Exception("LLM客户端未初始化")
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行请求
            response = await self.llm_client.analyze(
                prompt=request.prompt,
                context=request.context,
                analysis_type=request.analysis_type,
                analyst_id=request.analyst_id,
                stock_id=request.stock_id,
                user_id=request.user_id,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            execution_time = time.time() - start_time
            
            # 记录性能指标（如果有性能监控器）
            if self.performance_monitor:
                await self.performance_monitor.record_llm_response_metrics(
                    response=response,
                    task_type=request.analysis_type.value
                )
            
            # 验证响应与决策的匹配
            if response.provider.value != routing_decision.selected_provider:
                logger.warning(f"实际执行的提供商({response.provider.value})与路由决策不匹配"
                             f"({routing_decision.selected_provider})")
            
            # 添加路由元数据到响应
            if response.metadata is None:
                response.metadata = {}
            
            response.metadata.update({
                "routing_decision": asdict(routing_decision),
                "actual_execution_time_ms": execution_time * 1000,
                "cost_prediction_accuracy": self._calculate_cost_accuracy(
                    routing_decision.estimated_cost, response
                ),
                "latency_prediction_accuracy": self._calculate_latency_accuracy(
                    routing_decision.estimated_latency_ms, execution_time * 1000
                )
            })
            
            logger.info(f"路由请求执行完成: {response.success}, "
                       f"耗时{execution_time*1000:.1f}ms")
            
            return response
            
        except Exception as e:
            logger.error(f"执行路由请求失败: {e}")
            
            # 尝试故障转移
            if routing_decision.fallback_models and routing_context and routing_context.fallback_enabled:
                logger.info("尝试故障转移到备选模型")
                return await self._execute_fallback(request, routing_decision)
            else:
                # 返回错误响应
                return LLMResponse(
                    content="",
                    provider=LLMProvider(routing_decision.selected_provider),
                    model=routing_decision.selected_model,
                    success=False,
                    error=f"路由执行失败: {str(e)}"
                )
    
    async def _execute_fallback(
        self,
        request: LLMRequest,
        original_decision: RoutingDecision
    ) -> LLMResponse:
        """执行故障转移"""
        
        for fallback_candidate in original_decision.fallback_models:
            try:
                logger.info(f"尝试故障转移: {fallback_candidate.provider}/{fallback_candidate.model_id}")
                
                # 创建新的路由决策
                fallback_decision = RoutingDecision(
                    selected_provider=fallback_candidate.provider,
                    selected_model=fallback_candidate.model_id,
                    selection_confidence=fallback_candidate.confidence_score,
                    estimated_cost=fallback_candidate.estimated_cost,
                    estimated_latency_ms=fallback_candidate.estimated_latency_ms,
                    estimated_quality=fallback_candidate.quality_score,
                    fallback_models=[],
                    routing_strategy_used=RoutingStrategy.FAILOVER,
                    decision_factors={"failover": 1.0},
                    reasoning=f"故障转移到{fallback_candidate.selection_reason}",
                    timestamp=datetime.now(timezone.utc)
                )
                
                # 递归调用（无故障转移避免无限循环）
                response = await self.execute_routed_request(
                    request, fallback_decision, None
                )
                
                if response.success:
                    response.metadata = response.metadata or {}
                    response.metadata["fallback_executed"] = True
                    response.metadata["original_provider"] = original_decision.selected_provider
                    return response
                    
            except Exception as e:
                logger.warning(f"故障转移失败 {fallback_candidate.provider}: {e}")
                continue
        
        # 所有故障转移都失败
        return LLMResponse(
            content="",
            provider=LLMProvider(original_decision.selected_provider),
            model=original_decision.selected_model,
            success=False,
            error="所有模型（包括故障转移模型）都执行失败"
        )
    
    # ==================== 工具方法 ====================
    
    def _infer_task_complexity(self, request: LLMRequest) -> TaskComplexity:
        """推断任务复杂度"""
        
        prompt_length = len(request.prompt)
        context_size = len(str(request.context)) if request.context else 0
        
        # 基于提示词长度和上下文大小推断复杂度
        if prompt_length > 1500 or context_size > 2000:
            return TaskComplexity.EXPERT
        elif prompt_length > 800 or context_size > 1000:
            return TaskComplexity.COMPLEX
        elif prompt_length > 300 or context_size > 500:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE
    
    def _generate_cache_key(
        self,
        request: LLMRequest,
        routing_context: RoutingContext,
        strategy: RoutingStrategy
    ) -> str:
        """生成缓存键"""
        
        key_components = [
            request.analysis_type.value,
            routing_context.task_complexity.value,
            routing_context.user_tier.value,
            str(routing_context.quality_threshold),
            str(routing_context.require_local_processing),
            strategy.value
        ]
        
        # 添加约束条件
        if routing_context.max_latency_ms:
            key_components.append(f"max_lat_{routing_context.max_latency_ms}")
        if routing_context.max_cost_per_request:
            key_components.append(f"max_cost_{routing_context.max_cost_per_request}")
        if routing_context.preferred_providers:
            key_components.append("_".join(sorted(routing_context.preferred_providers)))
        
        return "_".join(key_components)
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self._routing_cache:
            return False
        
        timestamp = self._cache_timestamps.get(cache_key)
        if not timestamp:
            return False
        
        return (datetime.now(timezone.utc) - timestamp).total_seconds() < self.cache_ttl_seconds
    
    def _cache_routing_decision(self, cache_key: str, decision: RoutingDecision):
        """缓存路由决策"""
        self._routing_cache[cache_key] = decision
        self._cache_timestamps[cache_key] = datetime.now(timezone.utc)
    
    def _create_fallback_decision(self, error: Exception) -> RoutingDecision:
        """创建故障转移决策"""
        return RoutingDecision(
            selected_provider="gpt_oss",  # 默认使用本地GPT-OSS
            selected_model="default",
            selection_confidence=0.1,
            estimated_cost=0.0,
            estimated_latency_ms=5000.0,
            estimated_quality=0.5,
            fallback_models=[],
            routing_strategy_used=RoutingStrategy.FAILOVER,
            decision_factors={"emergency": 1.0},
            reasoning=f"紧急故障转移：{str(error)}",
            timestamp=datetime.now(timezone.utc)
        )
    
    def _calculate_cost_accuracy(
        self, 
        predicted_cost: float, 
        actual_response: LLMResponse
    ) -> float:
        """计算成本预测准确性"""
        if not actual_response.usage:
            return 0.0
        
        # 简化的实际成本计算
        total_tokens = actual_response.usage.get('total_tokens', 0)
        actual_cost = (total_tokens / 1000) * 0.002  # 简化成本
        
        if predicted_cost == 0:
            return 1.0 if actual_cost == 0 else 0.0
        
        accuracy = 1.0 - abs(predicted_cost - actual_cost) / predicted_cost
        return max(0.0, accuracy)
    
    def _calculate_latency_accuracy(
        self, 
        predicted_latency_ms: float, 
        actual_latency_ms: float
    ) -> float:
        """计算延迟预测准确性"""
        if predicted_latency_ms == 0:
            return 1.0 if actual_latency_ms == 0 else 0.0
        
        accuracy = 1.0 - abs(predicted_latency_ms - actual_latency_ms) / predicted_latency_ms
        return max(0.0, accuracy)
    
    # ==================== 监控和统计 ====================
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        
        success_rate = 0.0
        if self.total_routing_requests > 0:
            success_rate = (self.successful_routings / self.total_routing_requests) * 100
        
        cache_hit_rate = 0.0
        if self.total_routing_requests > 0:
            cache_hit_rate = (self.cache_hits / self.total_routing_requests) * 100
        
        return {
            "total_requests": self.total_routing_requests,
            "successful_routings": self.successful_routings,
            "failed_routings": self.failed_routings,
            "success_rate_percent": round(success_rate, 2),
            "cache_hits": self.cache_hits,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "cached_decisions": len(self._routing_cache),
            "last_routing_time": (
                self.last_routing_time.isoformat() 
                if self.last_routing_time else None
            ),
            "configuration": {
                "default_strategy": self.default_strategy.value,
                "cache_enabled": self.routing_cache_enabled,
                "cache_ttl_seconds": self.cache_ttl_seconds,
                "weights": {
                    "capability": self.capability_weight,
                    "cost": self.cost_weight,
                    "latency": self.latency_weight,
                    "availability": self.availability_weight
                }
            }
        }
    
    def clear_routing_cache(self):
        """清除路由缓存"""
        self._routing_cache.clear()
        self._cache_timestamps.clear()
        logger.info("路由缓存已清除")
    
    async def close(self):
        """关闭路由器，清理资源"""
        if self.model_capability_db:
            self.model_capability_db.close()
        
        if self.performance_monitor:
            await self.performance_monitor.close()
        
        if self.llm_client:
            await self.llm_client.close()
        
        logger.info("智能模型路由器已关闭")

# ==================== 工具函数 ====================

def create_intelligent_model_router(
    model_capability_db: Optional[ModelCapabilityDB] = None,
    performance_monitor: Optional[ModelPerformanceMonitor] = None,
    llm_client: Optional[LLMClient] = None
) -> IntelligentModelRouter:
    """创建智能模型路由器的便利函数"""
    return IntelligentModelRouter(
        model_capability_db, performance_monitor, llm_client
    )