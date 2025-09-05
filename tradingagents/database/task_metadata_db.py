#!/usr/bin/env python3
"""
Task Metadata Database Service
GPT-OSS任务元数据数据库服务
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, desc, func, text
from contextlib import contextmanager

from .database import SessionLocal, engine
from .task_metadata_models import (
    TaskMetadata, TaskRoutingRule, TaskPerformanceMetric, ModelCapability,
    TaskMetadataCreate, TaskMetadataUpdate, TaskMetadataResponse,
    ModelCapabilityResponse, RoutingDecisionRequest, RoutingDecisionResponse,
    TaskType, DataSensitivityLevel, BusinessPriority, TaskCategory
)

logger = logging.getLogger(__name__)

class TaskMetadataDBError(Exception):
    """任务元数据数据库错误"""
    pass

class TaskMetadataDB:
    """
    任务元数据数据库服务
    
    功能：
    1. 任务元数据的CRUD操作
    2. 智能路由决策支持
    3. 性能指标跟踪
    4. 模型能力管理
    """
    
    def __init__(self):
        """初始化数据库服务"""
        self.logger = logger
        self._ensure_tables()
    
    def _ensure_tables(self):
        """确保数据库表存在"""
        try:
            from .task_metadata_models import Base
            Base.metadata.create_all(bind=engine)
            self.logger.info("✅ Task metadata tables created/verified successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to create task metadata tables: {e}")
            raise TaskMetadataDBError(f"Database initialization failed: {e}")
    
    @contextmanager
    def get_session(self):
        """获取数据库会话上下文管理器"""
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== 任务元数据管理 ====================
    
    async def create_task_metadata(self, task_data: TaskMetadataCreate) -> TaskMetadataResponse:
        """
        创建新的任务元数据
        
        Args:
            task_data: 任务元数据创建请求
            
        Returns:
            创建的任务元数据
            
        Raises:
            TaskMetadataDBError: 创建失败时抛出
        """
        try:
            with self.get_session() as session:
                # 检查任务类型是否已存在
                existing = session.query(TaskMetadata).filter(
                    TaskMetadata.task_type == task_data.task_type
                ).first()
                
                if existing:
                    raise TaskMetadataDBError(f"Task type '{task_data.task_type}' already exists")
                
                # 创建新记录
                db_task = TaskMetadata(
                    task_type=task_data.task_type,
                    name=task_data.name,
                    description=task_data.description,
                    category=task_data.category.value,
                    required_quality_threshold=task_data.required_quality_threshold,
                    max_acceptable_latency_ms=task_data.max_acceptable_latency_ms,
                    max_acceptable_cost_per_1k=task_data.max_acceptable_cost_per_1k,
                    data_sensitivity_level=task_data.data_sensitivity_level.value,
                    requires_local_processing=task_data.requires_local_processing,
                    allow_cloud_fallback=task_data.allow_cloud_fallback,
                    business_priority=task_data.business_priority.value,
                    enable_caching=task_data.enable_caching,
                    cache_ttl_seconds=task_data.cache_ttl_seconds,
                    min_model_capability_score=task_data.min_model_capability_score,
                    preferred_model_types=task_data.preferred_model_types,
                    required_features=task_data.required_features,
                    max_tokens_input=task_data.max_tokens_input,
                    max_tokens_output=task_data.max_tokens_output,
                    max_retry_attempts=task_data.max_retry_attempts,
                    timeout_seconds=task_data.timeout_seconds,
                    success_rate_threshold=task_data.success_rate_threshold,
                    enable_quality_monitoring=task_data.enable_quality_monitoring,
                    enable_cost_tracking=task_data.enable_cost_tracking,
                    extra_metadata=task_data.extra_metadata,
                    version=task_data.version,
                )
                
                session.add(db_task)
                session.commit()
                session.refresh(db_task)
                
                self.logger.info(f"✅ Created task metadata: {task_data.task_type}")
                return TaskMetadataResponse.from_orm(db_task)
                
        except IntegrityError as e:
            self.logger.error(f"❌ Integrity error creating task metadata: {e}")
            raise TaskMetadataDBError(f"Task metadata creation failed: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error creating task metadata: {e}")
            raise TaskMetadataDBError(f"Unexpected error: {e}")
    
    async def get_task_metadata(self, task_type: str) -> Optional[TaskMetadataResponse]:
        """
        获取任务元数据
        
        Args:
            task_type: 任务类型
            
        Returns:
            任务元数据，如果不存在则返回None
        """
        try:
            with self.get_session() as session:
                db_task = session.query(TaskMetadata).filter(
                    and_(
                        TaskMetadata.task_type == task_type,
                        TaskMetadata.is_active == True
                    )
                ).first()
                
                if db_task:
                    return TaskMetadataResponse.from_orm(db_task)
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting task metadata: {e}")
            raise TaskMetadataDBError(f"Failed to get task metadata: {e}")
    
    async def update_task_metadata(self, task_type: str, update_data: TaskMetadataUpdate) -> TaskMetadataResponse:
        """
        更新任务元数据
        
        Args:
            task_type: 任务类型
            update_data: 更新数据
            
        Returns:
            更新后的任务元数据
            
        Raises:
            TaskMetadataDBError: 更新失败时抛出
        """
        try:
            with self.get_session() as session:
                db_task = session.query(TaskMetadata).filter(
                    TaskMetadata.task_type == task_type
                ).first()
                
                if not db_task:
                    raise TaskMetadataDBError(f"Task type '{task_type}' not found")
                
                # 更新字段
                update_fields = update_data.dict(exclude_unset=True)
                for field, value in update_fields.items():
                    if hasattr(db_task, field):
                        if hasattr(value, 'value'):  # 处理Enum类型
                            setattr(db_task, field, value.value)
                        else:
                            setattr(db_task, field, value)
                
                db_task.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                session.refresh(db_task)
                
                self.logger.info(f"✅ Updated task metadata: {task_type}")
                return TaskMetadataResponse.from_orm(db_task)
                
        except Exception as e:
            self.logger.error(f"❌ Error updating task metadata: {e}")
            raise TaskMetadataDBError(f"Failed to update task metadata: {e}")
    
    async def list_task_metadata(
        self,
        category: Optional[str] = None,
        business_priority: Optional[str] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[TaskMetadataResponse]:
        """
        列出任务元数据
        
        Args:
            category: 任务分类过滤
            business_priority: 业务优先级过滤
            is_active: 是否激活过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            任务元数据列表
        """
        try:
            with self.get_session() as session:
                query = session.query(TaskMetadata)
                
                # 添加过滤条件
                if category:
                    query = query.filter(TaskMetadata.category == category)
                if business_priority:
                    query = query.filter(TaskMetadata.business_priority == business_priority)
                if is_active is not None:
                    query = query.filter(TaskMetadata.is_active == is_active)
                
                # 排序和分页
                db_tasks = query.order_by(
                    TaskMetadata.business_priority,
                    TaskMetadata.created_at.desc()
                ).limit(limit).offset(offset).all()
                
                return [TaskMetadataResponse.from_orm(task) for task in db_tasks]
                
        except Exception as e:
            self.logger.error(f"❌ Error listing task metadata: {e}")
            raise TaskMetadataDBError(f"Failed to list task metadata: {e}")
    
    async def delete_task_metadata(self, task_type: str) -> bool:
        """
        删除任务元数据（软删除）
        
        Args:
            task_type: 任务类型
            
        Returns:
            是否删除成功
        """
        try:
            with self.get_session() as session:
                db_task = session.query(TaskMetadata).filter(
                    TaskMetadata.task_type == task_type
                ).first()
                
                if not db_task:
                    return False
                
                db_task.is_active = False
                db_task.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                
                self.logger.info(f"✅ Deleted task metadata: {task_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting task metadata: {e}")
            raise TaskMetadataDBError(f"Failed to delete task metadata: {e}")
    
    # ==================== 模型能力管理 ====================
    
    async def register_model_capability(
        self,
        provider: str,
        model_id: str,
        model_name: str,
        capability_data: Dict[str, Any]
    ) -> ModelCapabilityResponse:
        """
        注册模型能力
        
        Args:
            provider: 提供商
            model_id: 模型ID
            model_name: 模型名称
            capability_data: 能力数据
            
        Returns:
            模型能力信息
        """
        try:
            with self.get_session() as session:
                # 检查是否已存在
                existing = session.query(ModelCapability).filter(
                    and_(
                        ModelCapability.provider == provider,
                        ModelCapability.model_id == model_id
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    for field, value in capability_data.items():
                        if hasattr(existing, field):
                            setattr(existing, field, value)
                    existing.updated_at = datetime.now(timezone.utc)
                    db_model = existing
                else:
                    # 创建新记录
                    db_model = ModelCapability(
                        provider=provider,
                        model_id=model_id,
                        model_name=model_name,
                        **capability_data
                    )
                    session.add(db_model)
                
                session.commit()
                session.refresh(db_model)
                
                self.logger.info(f"✅ Registered model capability: {provider}/{model_id}")
                return ModelCapabilityResponse.from_orm(db_model)
                
        except Exception as e:
            self.logger.error(f"❌ Error registering model capability: {e}")
            raise TaskMetadataDBError(f"Failed to register model capability: {e}")
    
    async def get_available_models(
        self,
        task_requirements: Optional[Dict[str, Any]] = None,
        privacy_level: Optional[str] = None
    ) -> List[ModelCapabilityResponse]:
        """
        获取可用的模型列表
        
        Args:
            task_requirements: 任务要求
            privacy_level: 隐私级别要求
            
        Returns:
            可用模型列表
        """
        try:
            with self.get_session() as session:
                query = session.query(ModelCapability).filter(
                    ModelCapability.is_available == True
                )
                
                # 添加隐私级别过滤
                if privacy_level:
                    if privacy_level == "local":
                        query = query.filter(ModelCapability.privacy_level == "local")
                    elif privacy_level == "cloud":
                        query = query.filter(ModelCapability.privacy_level.in_(["cloud", "hybrid"]))
                
                # 添加任务要求过滤
                if task_requirements:
                    min_capability = task_requirements.get('min_capability_score', 0.0)
                    query = query.filter(ModelCapability.capability_score >= min_capability)
                    
                    max_cost = task_requirements.get('max_cost_per_1k', float('inf'))
                    query = query.filter(ModelCapability.cost_per_1k_input_tokens <= max_cost)
                    
                    max_latency = task_requirements.get('max_latency_ms', float('inf'))
                    query = query.filter(ModelCapability.avg_latency_ms <= max_latency)
                
                # 按能力评分排序
                models = query.order_by(desc(ModelCapability.capability_score)).all()
                
                return [ModelCapabilityResponse.from_orm(model) for model in models]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting available models: {e}")
            raise TaskMetadataDBError(f"Failed to get available models: {e}")
    
    # ==================== 智能路由决策 ====================
    
    async def make_routing_decision(self, request: RoutingDecisionRequest) -> RoutingDecisionResponse:
        """
        智能路由决策
        
        Args:
            request: 路由决策请求
            
        Returns:
            路由决策结果
        """
        try:
            # 获取任务元数据
            task_metadata = await self.get_task_metadata(request.task_type)
            if not task_metadata:
                raise TaskMetadataDBError(f"Task type '{request.task_type}' not found")
            
            # 构建任务要求
            task_requirements = {
                'min_capability_score': task_metadata.min_model_capability_score,
                'max_cost_per_1k': request.max_acceptable_cost or task_metadata.max_acceptable_cost_per_1k,
                'max_latency_ms': request.max_acceptable_latency or task_metadata.max_acceptable_latency_ms,
                'required_features': task_metadata.required_features,
                'max_tokens': max(task_metadata.max_tokens_input, task_metadata.max_tokens_output),
            }
            
            # 确定隐私级别要求
            privacy_level = None
            if task_metadata.requires_local_processing:
                privacy_level = "local"
            elif task_metadata.data_sensitivity_level in ["high", "confidential"]:
                privacy_level = "local" if not task_metadata.allow_cloud_fallback else None
            
            # 获取可用模型
            available_models = await self.get_available_models(task_requirements, privacy_level)
            
            if not available_models:
                raise TaskMetadataDBError("No suitable models available for this task")
            
            # 计算最优模型
            optimal_model = await self._calculate_optimal_model(
                available_models, task_requirements, request
            )
            
            # 生成决策响应
            response = RoutingDecisionResponse(
                selected_provider=optimal_model.provider,
                selected_model=optimal_model.model_id,
                reasoning=self._generate_routing_reasoning(optimal_model, task_metadata, request),
                expected_cost=self._calculate_expected_cost(optimal_model, request.estimated_tokens),
                expected_latency_ms=int(optimal_model.avg_latency_ms),
                expected_quality_score=optimal_model.capability_score,
                confidence_score=self._calculate_confidence_score(optimal_model, task_requirements),
                fallback_options=self._get_fallback_options(available_models, optimal_model),
                decision_metadata={
                    'task_type': request.task_type,
                    'user_tier': request.user_tier,
                    'estimated_tokens': request.estimated_tokens,
                    'privacy_level': privacy_level,
                    'decision_timestamp': datetime.now(timezone.utc).isoformat(),
                }
            )
            
            self.logger.info(f"✅ Routing decision made: {optimal_model.provider}/{optimal_model.model_id}")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error making routing decision: {e}")
            raise TaskMetadataDBError(f"Failed to make routing decision: {e}")
    
    async def _calculate_optimal_model(
        self,
        available_models: List[ModelCapabilityResponse],
        task_requirements: Dict[str, Any],
        request: RoutingDecisionRequest
    ) -> ModelCapabilityResponse:
        """计算最优模型"""
        best_model = None
        best_score = -1.0
        
        for model in available_models:
            # 计算综合评分
            score = self._calculate_model_score(model, task_requirements, request)
            
            if score > best_score:
                best_score = score
                best_model = model
        
        if not best_model:
            raise TaskMetadataDBError("No suitable model found")
        
        return best_model
    
    def _calculate_model_score(
        self,
        model: ModelCapabilityResponse,
        task_requirements: Dict[str, Any],
        request: RoutingDecisionRequest
    ) -> float:
        """计算模型评分"""
        # 基础能力评分 (40%)
        capability_score = model.capability_score * 0.4
        
        # 成本效益评分 (30%)
        expected_cost = self._calculate_expected_cost(model, request.estimated_tokens)
        max_cost = task_requirements.get('max_cost_per_1k', 0.01)
        cost_score = max(0, (max_cost - expected_cost) / max_cost) * 0.3
        
        # 延迟评分 (20%)
        max_latency = task_requirements.get('max_latency_ms', 5000)
        latency_score = max(0, (max_latency - model.avg_latency_ms) / max_latency) * 0.2
        
        # 用户偏好评分 (10%)
        preference_score = self._calculate_preference_score(model, request) * 0.1
        
        return capability_score + cost_score + latency_score + preference_score
    
    def _calculate_expected_cost(self, model: ModelCapabilityResponse, estimated_tokens: int) -> float:
        """计算预期成本"""
        input_cost = (estimated_tokens / 1000) * model.cost_per_1k_input_tokens
        output_cost = (estimated_tokens * 0.5 / 1000) * model.cost_per_1k_output_tokens  # 假设输出是输入的50%
        return input_cost + output_cost
    
    def _calculate_preference_score(self, model: ModelCapabilityResponse, request: RoutingDecisionRequest) -> float:
        """计算用户偏好评分"""
        preferences = request.user_preferences or {}
        
        # 提供商偏好
        preferred_provider = preferences.get('preferred_provider')
        if preferred_provider and model.provider == preferred_provider:
            return 1.0
        
        # 模型类型偏好
        preferred_model_type = preferences.get('preferred_model_type')
        if preferred_model_type and preferred_model_type in (model.model_name.lower()):
            return 0.8
        
        return 0.5  # 默认中性偏好
    
    def _calculate_confidence_score(self, model: ModelCapabilityResponse, task_requirements: Dict[str, Any]) -> float:
        """计算决策信心度"""
        # 基于模型能力与任务要求的匹配度
        capability_match = min(1.0, model.capability_score / task_requirements.get('min_capability_score', 0.5))
        
        # 基于模型的基准测试结果
        benchmark_confidence = 0.8  # 默认信心度，可以基于实际基准测试结果调整
        if model.benchmark_scores:
            benchmark_confidence = model.benchmark_scores.get('overall_confidence', 0.8)
        
        return (capability_match + benchmark_confidence) / 2
    
    def _generate_routing_reasoning(
        self,
        model: ModelCapabilityResponse,
        task_metadata: TaskMetadataResponse,
        request: RoutingDecisionRequest
    ) -> str:
        """生成路由决策推理"""
        reasons = []
        
        # 能力匹配
        if model.capability_score >= task_metadata.min_model_capability_score:
            reasons.append(f"模型能力评分 {model.capability_score:.2f} 满足任务要求 {task_metadata.min_model_capability_score:.2f}")
        
        # 成本考虑
        expected_cost = self._calculate_expected_cost(model, request.estimated_tokens)
        if expected_cost <= task_metadata.max_acceptable_cost_per_1k:
            reasons.append(f"预期成本 ${expected_cost:.4f} 在可接受范围内")
        
        # 延迟考虑
        if model.avg_latency_ms <= task_metadata.max_acceptable_latency_ms:
            reasons.append(f"平均延迟 {model.avg_latency_ms:.0f}ms 符合要求")
        
        # 隐私考虑
        if task_metadata.requires_local_processing and model.privacy_level == "local":
            reasons.append("满足本地处理的隐私要求")
        
        return "; ".join(reasons)
    
    def _get_fallback_options(
        self,
        available_models: List[ModelCapabilityResponse],
        selected_model: ModelCapabilityResponse
    ) -> List[Dict[str, str]]:
        """获取后备选项"""
        fallback_options = []
        
        for model in available_models:
            if model.id != selected_model.id:
                fallback_options.append({
                    'provider': model.provider,
                    'model': model.model_id,
                    'reason': f"备选方案 - 能力评分: {model.capability_score:.2f}"
                })
            
            if len(fallback_options) >= 3:  # 最多3个后备选项
                break
        
        return fallback_options
    
    # ==================== 性能指标管理 ====================
    
    async def record_task_performance(
        self,
        task_type: str,
        provider: str,
        model: str,
        latency_ms: float,
        success: bool,
        quality_score: Optional[float] = None,
        cost: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        记录任务性能指标
        
        Args:
            task_type: 任务类型
            provider: 提供商
            model: 模型
            latency_ms: 延迟
            success: 是否成功
            quality_score: 质量评分
            cost: 成本
            metadata: 元数据
            
        Returns:
            是否记录成功
        """
        try:
            with self.get_session() as session:
                # 获取任务元数据
                task_metadata = session.query(TaskMetadata).filter(
                    TaskMetadata.task_type == task_type
                ).first()
                
                if not task_metadata:
                    self.logger.warning(f"Task type '{task_type}' not found for performance recording")
                    return False
                
                # 获取或创建性能指标记录
                now = datetime.now(timezone.utc)
                period_start = now.replace(minute=0, second=0, microsecond=0)  # 按小时聚合
                period_end = period_start + timedelta(hours=1)
                
                metric = session.query(TaskPerformanceMetric).filter(
                    and_(
                        TaskPerformanceMetric.task_metadata_id == task_metadata.id,
                        TaskPerformanceMetric.provider == provider,
                        TaskPerformanceMetric.model == model,
                        TaskPerformanceMetric.measurement_period_start == period_start
                    )
                ).first()
                
                if metric:
                    # 更新现有记录
                    metric.total_requests += 1
                    if not success:
                        metric.total_failures += 1
                    
                    # 更新平均延迟
                    total_successful_requests = metric.total_requests - metric.total_failures
                    if total_successful_requests > 0:
                        metric.avg_latency_ms = (
                            (metric.avg_latency_ms * (total_successful_requests - 1) + latency_ms)
                            / total_successful_requests
                        )
                    
                    # 更新成功率
                    metric.success_rate = (metric.total_requests - metric.total_failures) / metric.total_requests
                    
                    # 更新质量评分
                    if quality_score is not None:
                        if metric.avg_quality_score is None:
                            metric.avg_quality_score = quality_score
                        else:
                            metric.avg_quality_score = (metric.avg_quality_score + quality_score) / 2
                    
                    # 更新成本
                    metric.total_cost += cost
                    metric.avg_cost_per_request = metric.total_cost / metric.total_requests
                    
                else:
                    # 创建新记录
                    metric = TaskPerformanceMetric(
                        task_metadata_id=task_metadata.id,
                        provider=provider,
                        model=model,
                        avg_latency_ms=latency_ms if success else 0.0,
                        p95_latency_ms=latency_ms if success else 0.0,  # 初始值
                        success_rate=1.0 if success else 0.0,
                        avg_quality_score=quality_score,
                        avg_cost_per_request=cost,
                        total_requests=1,
                        total_failures=0 if success else 1,
                        total_cost=cost,
                        measurement_period_start=period_start,
                        measurement_period_end=period_end,
                        perf_metadata=metadata
                    )
                    session.add(metric)
                
                session.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error recording task performance: {e}")
            return False
    
    async def get_task_performance_stats(
        self,
        task_type: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        hours_back: int = 24
    ) -> Dict[str, Any]:
        """
        获取任务性能统计
        
        Args:
            task_type: 任务类型
            provider: 提供商过滤
            model: 模型过滤
            hours_back: 回溯小时数
            
        Returns:
            性能统计数据
        """
        try:
            with self.get_session() as session:
                # 获取任务元数据
                task_metadata = session.query(TaskMetadata).filter(
                    TaskMetadata.task_type == task_type
                ).first()
                
                if not task_metadata:
                    return {}
                
                # 构建查询
                query = session.query(TaskPerformanceMetric).filter(
                    TaskPerformanceMetric.task_metadata_id == task_metadata.id
                )
                
                # 时间过滤
                time_threshold = datetime.now(timezone.utc) - timedelta(hours=hours_back)
                query = query.filter(TaskPerformanceMetric.measurement_period_start >= time_threshold)
                
                # 提供商和模型过滤
                if provider:
                    query = query.filter(TaskPerformanceMetric.provider == provider)
                if model:
                    query = query.filter(TaskPerformanceMetric.model == model)
                
                metrics = query.all()
                
                if not metrics:
                    return {}
                
                # 聚合统计
                total_requests = sum(m.total_requests for m in metrics)
                total_failures = sum(m.total_failures for m in metrics)
                total_cost = sum(m.total_cost for m in metrics)
                
                # 加权平均延迟
                weighted_latency = sum(m.avg_latency_ms * m.total_requests for m in metrics)
                avg_latency = weighted_latency / total_requests if total_requests > 0 else 0
                
                # 平均质量评分
                quality_scores = [m.avg_quality_score for m in metrics if m.avg_quality_score is not None]
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
                
                return {
                    'task_type': task_type,
                    'total_requests': total_requests,
                    'total_failures': total_failures,
                    'success_rate': (total_requests - total_failures) / total_requests if total_requests > 0 else 0,
                    'avg_latency_ms': avg_latency,
                    'total_cost': total_cost,
                    'avg_cost_per_request': total_cost / total_requests if total_requests > 0 else 0,
                    'avg_quality_score': avg_quality,
                    'time_period_hours': hours_back,
                    'provider_breakdown': self._get_provider_breakdown(metrics),
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting task performance stats: {e}")
            return {}
    
    def _get_provider_breakdown(self, metrics: List[TaskPerformanceMetric]) -> Dict[str, Dict[str, Any]]:
        """获取提供商性能分解"""
        breakdown = {}
        
        for metric in metrics:
            provider_key = f"{metric.provider}/{metric.model}"
            if provider_key not in breakdown:
                breakdown[provider_key] = {
                    'total_requests': 0,
                    'total_failures': 0,
                    'total_cost': 0.0,
                    'weighted_latency': 0.0,
                    'quality_scores': []
                }
            
            data = breakdown[provider_key]
            data['total_requests'] += metric.total_requests
            data['total_failures'] += metric.total_failures
            data['total_cost'] += metric.total_cost
            data['weighted_latency'] += metric.avg_latency_ms * metric.total_requests
            
            if metric.avg_quality_score is not None:
                data['quality_scores'].append(metric.avg_quality_score)
        
        # 计算最终统计
        for provider_key, data in breakdown.items():
            if data['total_requests'] > 0:
                data['success_rate'] = (data['total_requests'] - data['total_failures']) / data['total_requests']
                data['avg_latency_ms'] = data['weighted_latency'] / data['total_requests']
                data['avg_cost_per_request'] = data['total_cost'] / data['total_requests']
                data['avg_quality_score'] = (
                    sum(data['quality_scores']) / len(data['quality_scores'])
                    if data['quality_scores'] else None
                )
            
            # 清理临时字段
            del data['weighted_latency']
            del data['quality_scores']
        
        return breakdown
    
    # ==================== 初始化标准任务类型 ====================
    
    async def initialize_standard_task_types(self) -> List[str]:
        """
        初始化标准任务类型
        
        Returns:
            初始化的任务类型列表
        """
        standard_tasks = [
            # 摘要任务
            TaskMetadataCreate(
                task_type="financial_summary",
                name="财务摘要",
                description="生成公司财务数据的摘要分析",
                category=TaskCategory.BATCH,
                required_quality_threshold=0.8,
                max_acceptable_latency_ms=10000,
                max_acceptable_cost_per_1k=0.015,
                data_sensitivity_level=DataSensitivityLevel.MEDIUM,
                business_priority=BusinessPriority.IMPORTANT,
                preferred_model_types=["instruct", "chat"],
                required_features=["reasoning", "math"],
                max_tokens_input=8000,
                max_tokens_output=2000,
            ),
            
            # 分类任务
            TaskMetadataCreate(
                task_type="news_classification",
                name="新闻分类",
                description="对新闻文章进行主题和情感分类",
                category=TaskCategory.REAL_TIME,
                required_quality_threshold=0.75,
                max_acceptable_latency_ms=3000,
                max_acceptable_cost_per_1k=0.008,
                data_sensitivity_level=DataSensitivityLevel.LOW,
                business_priority=BusinessPriority.STANDARD,
                preferred_model_types=["classification", "chat"],
                max_tokens_input=4000,
                max_tokens_output=500,
            ),
            
            # 推理任务
            TaskMetadataCreate(
                task_type="investment_reasoning",
                name="投资推理",
                description="基于市场数据进行投资决策推理",
                category=TaskCategory.INTERACTIVE,
                required_quality_threshold=0.9,
                max_acceptable_latency_ms=15000,
                max_acceptable_cost_per_1k=0.025,
                data_sensitivity_level=DataSensitivityLevel.HIGH,
                requires_local_processing=True,
                allow_cloud_fallback=False,
                business_priority=BusinessPriority.CRITICAL,
                preferred_model_types=["reasoning", "chat"],
                required_features=["reasoning", "math", "analysis"],
                max_tokens_input=12000,
                max_tokens_output=3000,
            ),
            
            # 生成任务
            TaskMetadataCreate(
                task_type="report_generation",
                name="报告生成",
                description="生成投资分析报告",
                category=TaskCategory.BATCH,
                required_quality_threshold=0.85,
                max_acceptable_latency_ms=20000,
                max_acceptable_cost_per_1k=0.02,
                data_sensitivity_level=DataSensitivityLevel.MEDIUM,
                business_priority=BusinessPriority.IMPORTANT,
                preferred_model_types=["generation", "chat"],
                required_features=["writing", "formatting"],
                max_tokens_input=10000,
                max_tokens_output=5000,
            ),
            
            # 情感分析任务
            TaskMetadataCreate(
                task_type="market_sentiment",
                name="市场情感分析",
                description="分析市场新闻和社交媒体的情感倾向",
                category=TaskCategory.REAL_TIME,
                required_quality_threshold=0.7,
                max_acceptable_latency_ms=2000,
                max_acceptable_cost_per_1k=0.005,
                data_sensitivity_level=DataSensitivityLevel.LOW,
                business_priority=BusinessPriority.STANDARD,
                preferred_model_types=["sentiment", "classification"],
                max_tokens_input=2000,
                max_tokens_output=300,
            ),
        ]
        
        initialized_tasks = []
        
        for task_data in standard_tasks:
            try:
                existing = await self.get_task_metadata(task_data.task_type)
                if not existing:
                    await self.create_task_metadata(task_data)
                    initialized_tasks.append(task_data.task_type)
                    self.logger.info(f"✅ Initialized standard task type: {task_data.task_type}")
                else:
                    self.logger.info(f"ℹ️ Task type already exists: {task_data.task_type}")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize task type {task_data.task_type}: {e}")
        
        return initialized_tasks