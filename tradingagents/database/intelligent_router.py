#!/usr/bin/env python3
"""
Intelligent Task Router
智能任务路由器 - 与现有TradingAgents系统整合
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .task_metadata_db import TaskMetadataDB, TaskMetadataDBError
from .task_metadata_models import RoutingDecisionRequest, RoutingDecisionResponse
from .task_standards import task_standard_registry, TaskStandard
from ..utils.llm_client import LLMClientError
from ..default_config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)

class ProviderStatus(Enum):
    """提供商状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"  
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"

@dataclass
class ProviderHealthCheck:
    """提供商健康检查结果"""
    provider: str
    status: ProviderStatus
    latency_ms: float
    success_rate: float
    last_check: datetime
    error_message: Optional[str] = None

@dataclass
class RouteTask:
    """路由任务定义"""
    task_id: str
    task_type: str
    user_id: str
    user_tier: str
    priority: str
    estimated_tokens: int
    max_latency: Optional[int] = None
    max_cost: Optional[float] = None
    requires_local: bool = False
    user_preferences: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

class IntelligentTaskRouter:
    """
    智能任务路由器
    
    功能：
    1. 基于任务元数据进行智能路由决策
    2. 监控提供商健康状态
    3. 实现故障转移和负载均衡
    4. 收集和分析性能指标
    """
    
    def __init__(self, metadata_db: Optional[TaskMetadataDB] = None):
        """初始化路由器"""
        self.metadata_db = metadata_db or TaskMetadataDB()
        self.logger = logger
        self.config = DEFAULT_CONFIG['llm_config']
        
        # 提供商健康状态缓存
        self._provider_health: Dict[str, ProviderHealthCheck] = {}
        self._health_check_interval = self.config.get('health_check_interval', 60)
        self._last_health_check = datetime.min
        
        # 路由统计
        self._routing_stats = {
            'total_requests': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'provider_usage': {},
            'average_decision_time_ms': 0.0
        }
        
        # 缓存
        self._routing_cache: Dict[str, Tuple[RoutingDecisionResponse, datetime]] = {}
        self._cache_ttl = 300  # 5分钟缓存
        
        self.logger.info("✅ Intelligent Task Router initialized")
    
    # ==================== 主要路由接口 ====================
    
    async def route_task(self, task: RouteTask) -> RoutingDecisionResponse:
        """
        路由任务到最优提供商
        
        Args:
            task: 路由任务
            
        Returns:
            路由决策结果
            
        Raises:
            TaskMetadataDBError: 路由失败时抛出
        """
        start_time = time.time()
        self._routing_stats['total_requests'] += 1
        
        try:
            self.logger.info(f"🚀 Routing task: {task.task_type} for user {task.user_id}")
            
            # 检查缓存
            cached_decision = self._get_cached_decision(task)
            if cached_decision:
                self.logger.info(f"📦 Using cached routing decision for {task.task_type}")
                return cached_decision
            
            # 健康检查
            await self._ensure_provider_health()
            
            # 构建路由请求
            routing_request = RoutingDecisionRequest(
                task_type=task.task_type,
                user_tier=task.user_tier,
                estimated_tokens=task.estimated_tokens,
                priority=task.priority,
                requires_high_quality=task.priority in ['critical', 'important'],
                max_acceptable_latency=task.max_latency,
                max_acceptable_cost=task.max_cost,
                user_preferences=task.user_preferences
            )
            
            # 执行路由决策
            decision = await self.metadata_db.make_routing_decision(routing_request)
            
            # 应用业务规则和健康检查
            final_decision = await self._apply_business_rules(decision, task)
            
            # 缓存决策
            self._cache_decision(task, final_decision)
            
            # 更新统计
            self._routing_stats['successful_routes'] += 1
            self._update_provider_usage(final_decision.selected_provider)
            
            decision_time = (time.time() - start_time) * 1000
            self._update_average_decision_time(decision_time)
            
            self.logger.info(
                f"✅ Routed {task.task_type} to {final_decision.selected_provider}/{final_decision.selected_model} "
                f"in {decision_time:.1f}ms"
            )
            
            return final_decision
            
        except Exception as e:
            self._routing_stats['failed_routes'] += 1
            self.logger.error(f"❌ Failed to route task {task.task_type}: {e}")
            
            # 尝试故障转移
            fallback_decision = await self._handle_routing_failure(task, e)
            if fallback_decision:
                return fallback_decision
            
            raise TaskMetadataDBError(f"Task routing failed: {e}")
    
    async def _apply_business_rules(
        self, 
        decision: RoutingDecisionResponse, 
        task: RouteTask
    ) -> RoutingDecisionResponse:
        """应用业务规则和健康检查"""
        
        # 检查提供商健康状态
        provider_health = self._provider_health.get(decision.selected_provider)
        if provider_health and provider_health.status != ProviderStatus.HEALTHY:
            self.logger.warning(
                f"⚠️ Selected provider {decision.selected_provider} is {provider_health.status.value}, "
                "looking for alternatives"
            )
            
            # 寻找健康的替代方案
            for fallback in decision.fallback_options:
                fallback_health = self._provider_health.get(fallback['provider'])
                if fallback_health and fallback_health.status == ProviderStatus.HEALTHY:
                    self.logger.info(f"🔄 Using fallback provider: {fallback['provider']}")
                    decision.selected_provider = fallback['provider']
                    decision.selected_model = fallback['model']
                    decision.reasoning += f" (Fallback due to {provider_health.status.value} primary provider)"
                    break
        
        # 应用用户层级限制
        if task.user_tier == 'free':
            # 免费用户限制到本地或低成本提供商
            if decision.expected_cost > 0.01:  # $0.01 per 1k tokens
                for fallback in decision.fallback_options:
                    if fallback['provider'] == 'gpt_oss':  # 本地免费
                        decision.selected_provider = fallback['provider']
                        decision.selected_model = fallback['model']
                        decision.reasoning += " (Cost optimization for free tier)"
                        break
        
        # 应用数据敏感性规则
        if task.requires_local:
            if decision.selected_provider != 'gpt_oss':
                # 强制使用本地提供商
                for fallback in decision.fallback_options:
                    if fallback['provider'] == 'gpt_oss':
                        decision.selected_provider = fallback['provider']
                        decision.selected_model = fallback['model']
                        decision.reasoning += " (Privacy requirement: local processing only)"
                        break
        
        return decision
    
    async def _handle_routing_failure(
        self, 
        task: RouteTask, 
        error: Exception
    ) -> Optional[RoutingDecisionResponse]:
        """处理路由失败，尝试故障转移"""
        
        self.logger.warning(f"🔄 Attempting fallback routing for task {task.task_type}")
        
        # 获取默认提供商配置
        provider_priority = self.config.get('provider_priority', ['gpt_oss', 'openai', 'anthropic'])
        
        for provider in provider_priority:
            try:
                # 检查提供商健康状态
                health = self._provider_health.get(provider)
                if health and health.status != ProviderStatus.HEALTHY:
                    continue
                
                # 创建简化的故障转移决策
                fallback_decision = RoutingDecisionResponse(
                    selected_provider=provider,
                    selected_model=self._get_default_model_for_provider(provider),
                    reasoning=f"Fallback routing due to error: {str(error)[:100]}",
                    expected_cost=self._estimate_cost_for_provider(provider, task.estimated_tokens),
                    expected_latency_ms=self._estimate_latency_for_provider(provider),
                    expected_quality_score=0.7,  # 默认质量评分
                    confidence_score=0.5,  # 低信心度
                    fallback_options=[],
                    decision_metadata={
                        'fallback_routing': True,
                        'original_error': str(error),
                        'task_id': task.task_id,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }
                )
                
                self.logger.info(f"🆘 Fallback routing to {provider} for task {task.task_type}")
                return fallback_decision
                
            except Exception as fallback_error:
                self.logger.error(f"❌ Fallback to {provider} also failed: {fallback_error}")
                continue
        
        return None
    
    # ==================== 提供商健康监控 ====================
    
    async def _ensure_provider_health(self):
        """确保提供商健康状态是最新的"""
        now = datetime.now(timezone.utc)
        if (now - self._last_health_check).total_seconds() > self._health_check_interval:
            await self._check_all_providers_health()
            self._last_health_check = now
    
    async def _check_all_providers_health(self):
        """检查所有提供商的健康状态"""
        providers = self.config.get('provider_priority', ['gpt_oss', 'openai', 'anthropic'])
        
        health_checks = []
        for provider in providers:
            health_checks.append(self._check_provider_health(provider))
        
        try:
            results = await asyncio.gather(*health_checks, return_exceptions=True)
            
            for provider, result in zip(providers, results):
                if isinstance(result, Exception):
                    self._provider_health[provider] = ProviderHealthCheck(
                        provider=provider,
                        status=ProviderStatus.UNAVAILABLE,
                        latency_ms=float('inf'),
                        success_rate=0.0,
                        last_check=datetime.now(timezone.utc),
                        error_message=str(result)
                    )
                else:
                    self._provider_health[provider] = result
            
            self.logger.info("🏥 Provider health check completed")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to complete health checks: {e}")
    
    async def _check_provider_health(self, provider: str) -> ProviderHealthCheck:
        """检查单个提供商的健康状态"""
        start_time = time.time()
        
        try:
            # 这里应该实现实际的健康检查逻辑
            # 对于演示，我们使用简化的检查
            
            if provider == 'gpt_oss':
                # 检查本地GPT-OSS服务
                url = self.config.get('gpt_oss_url', 'http://localhost:8080')
                # 实际应该发送健康检查请求
                latency_ms = (time.time() - start_time) * 1000
                
                return ProviderHealthCheck(
                    provider=provider,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency_ms,
                    success_rate=0.95,
                    last_check=datetime.now(timezone.utc)
                )
            
            elif provider == 'openai':
                # 检查OpenAI API
                api_key = self.config.get('openai_api_key')
                if not api_key:
                    return ProviderHealthCheck(
                        provider=provider,
                        status=ProviderStatus.UNAVAILABLE,
                        latency_ms=float('inf'),
                        success_rate=0.0,
                        last_check=datetime.now(timezone.utc),
                        error_message="API key not configured"
                    )
                
                latency_ms = (time.time() - start_time) * 1000
                return ProviderHealthCheck(
                    provider=provider,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency_ms,
                    success_rate=0.98,
                    last_check=datetime.now(timezone.utc)
                )
            
            elif provider == 'anthropic':
                # 检查Anthropic API
                api_key = self.config.get('anthropic_api_key')
                if not api_key:
                    return ProviderHealthCheck(
                        provider=provider,
                        status=ProviderStatus.UNAVAILABLE,
                        latency_ms=float('inf'),
                        success_rate=0.0,
                        last_check=datetime.now(timezone.utc),
                        error_message="API key not configured"
                    )
                
                latency_ms = (time.time() - start_time) * 1000
                return ProviderHealthCheck(
                    provider=provider,
                    status=ProviderStatus.HEALTHY,
                    latency_ms=latency_ms,
                    success_rate=0.97,
                    last_check=datetime.now(timezone.utc)
                )
            
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ProviderHealthCheck(
                provider=provider,
                status=ProviderStatus.UNAVAILABLE,
                latency_ms=latency_ms,
                success_rate=0.0,
                last_check=datetime.now(timezone.utc),
                error_message=str(e)
            )
    
    # ==================== 缓存管理 ====================
    
    def _get_cached_decision(self, task: RouteTask) -> Optional[RoutingDecisionResponse]:
        """获取缓存的路由决策"""
        cache_key = self._get_cache_key(task)
        
        if cache_key in self._routing_cache:
            decision, cached_at = self._routing_cache[cache_key]
            
            # 检查缓存是否过期
            if (datetime.now(timezone.utc) - cached_at).total_seconds() < self._cache_ttl:
                return decision
            else:
                # 清理过期缓存
                del self._routing_cache[cache_key]
        
        return None
    
    def _cache_decision(self, task: RouteTask, decision: RoutingDecisionResponse):
        """缓存路由决策"""
        cache_key = self._get_cache_key(task)
        self._routing_cache[cache_key] = (decision, datetime.now(timezone.utc))
        
        # 清理过期缓存
        self._cleanup_expired_cache()
    
    def _get_cache_key(self, task: RouteTask) -> str:
        """生成缓存键"""
        return f"{task.task_type}:{task.user_tier}:{task.estimated_tokens}:{task.priority}"
    
    def _cleanup_expired_cache(self):
        """清理过期的缓存条目"""
        now = datetime.now(timezone.utc)
        expired_keys = []
        
        for cache_key, (decision, cached_at) in self._routing_cache.items():
            if (now - cached_at).total_seconds() > self._cache_ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            del self._routing_cache[key]
    
    # ==================== 工具方法 ====================
    
    def _get_default_model_for_provider(self, provider: str) -> str:
        """获取提供商的默认模型"""
        models = self.config.get('models', {})
        provider_models = models.get(provider, {})
        
        if provider_models:
            return list(provider_models.keys())[0]
        
        # 后备默认值
        defaults = {
            'gpt_oss': 'gpt-oss',
            'openai': 'gpt-3.5-turbo',
            'anthropic': 'claude-3-haiku'
        }
        return defaults.get(provider, 'unknown')
    
    def _estimate_cost_for_provider(self, provider: str, tokens: int) -> float:
        """估算提供商的成本"""
        models = self.config.get('models', {})
        provider_models = models.get(provider, {})
        
        if provider_models:
            model_name = list(provider_models.keys())[0]
            model_config = provider_models[model_name]
            return (tokens / 1000) * model_config.get('cost_per_1k', 0.01)
        
        # 后备估算
        defaults = {
            'gpt_oss': 0.0,
            'openai': 0.002,
            'anthropic': 0.00025
        }
        return (tokens / 1000) * defaults.get(provider, 0.01)
    
    def _estimate_latency_for_provider(self, provider: str) -> int:
        """估算提供商的延迟"""
        health = self._provider_health.get(provider)
        if health:
            return int(health.latency_ms)
        
        # 后备估算
        defaults = {
            'gpt_oss': 5000,    # 本地推理较慢
            'openai': 2000,     # API调用
            'anthropic': 2500   # API调用
        }
        return defaults.get(provider, 5000)
    
    def _update_provider_usage(self, provider: str):
        """更新提供商使用统计"""
        if provider not in self._routing_stats['provider_usage']:
            self._routing_stats['provider_usage'][provider] = 0
        self._routing_stats['provider_usage'][provider] += 1
    
    def _update_average_decision_time(self, decision_time_ms: float):
        """更新平均决策时间"""
        current_avg = self._routing_stats['average_decision_time_ms']
        total_requests = self._routing_stats['total_requests']
        
        if total_requests == 1:
            self._routing_stats['average_decision_time_ms'] = decision_time_ms
        else:
            self._routing_stats['average_decision_time_ms'] = (
                (current_avg * (total_requests - 1) + decision_time_ms) / total_requests
            )
    
    # ==================== 监控和统计 ====================
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """获取路由统计信息"""
        stats = self._routing_stats.copy()
        
        # 添加成功率
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_routes'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
        
        # 添加提供商健康状态
        stats['provider_health'] = {
            provider: {
                'status': health.status.value,
                'latency_ms': health.latency_ms,
                'success_rate': health.success_rate,
                'last_check': health.last_check.isoformat()
            }
            for provider, health in self._provider_health.items()
        }
        
        return stats
    
    def get_provider_health(self, provider: str) -> Optional[ProviderHealthCheck]:
        """获取特定提供商的健康状态"""
        return self._provider_health.get(provider)
    
    def reset_stats(self):
        """重置统计信息"""
        self._routing_stats = {
            'total_requests': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'provider_usage': {},
            'average_decision_time_ms': 0.0
        }
        self.logger.info("📊 Routing statistics reset")
    
    # ==================== 任务性能反馈 ====================
    
    async def record_task_completion(
        self,
        task_id: str,
        task_type: str,
        provider: str,
        model: str,
        latency_ms: float,
        success: bool,
        quality_score: Optional[float] = None,
        cost: float = 0.0,
        error_message: Optional[str] = None
    ):
        """
        记录任务完成情况，用于优化后续路由决策
        
        Args:
            task_id: 任务ID
            task_type: 任务类型
            provider: 提供商
            model: 模型
            latency_ms: 实际延迟
            success: 是否成功
            quality_score: 质量评分
            cost: 实际成本
            error_message: 错误信息（如果失败）
        """
        try:
            # 记录到数据库
            await self.metadata_db.record_task_performance(
                task_type=task_type,
                provider=provider,
                model=model,
                latency_ms=latency_ms,
                success=success,
                quality_score=quality_score,
                cost=cost,
                metadata={
                    'task_id': task_id,
                    'error_message': error_message,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # 更新提供商健康状态
            if provider in self._provider_health:
                health = self._provider_health[provider]
                
                # 更新成功率（使用指数移动平均）
                alpha = 0.1  # 学习率
                if success:
                    health.success_rate = health.success_rate * (1 - alpha) + alpha
                else:
                    health.success_rate = health.success_rate * (1 - alpha)
                
                # 更新延迟（使用指数移动平均）
                if success:  # 只有成功的请求才更新延迟
                    health.latency_ms = health.latency_ms * (1 - alpha) + latency_ms * alpha
                
                # 如果连续失败过多，标记为降级
                if health.success_rate < 0.8:
                    health.status = ProviderStatus.DEGRADED
                elif health.success_rate < 0.5:
                    health.status = ProviderStatus.UNAVAILABLE
                else:
                    health.status = ProviderStatus.HEALTHY
            
            self.logger.info(f"📝 Recorded task completion: {task_id} -> {provider}/{model}")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record task completion: {e}")

# ==================== 工厂函数 ====================

def create_intelligent_router(config: Optional[Dict[str, Any]] = None) -> IntelligentTaskRouter:
    """
    创建智能路由器实例
    
    Args:
        config: 可选的配置覆盖
        
    Returns:
        智能路由器实例
    """
    metadata_db = TaskMetadataDB()
    router = IntelligentTaskRouter(metadata_db)
    
    # 如果提供了配置，则更新
    if config:
        router.config.update(config)
    
    return router