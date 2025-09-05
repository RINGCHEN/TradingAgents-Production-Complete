#!/usr/bin/env python3
"""
Model Capability Database Service
模型能力数据库服务 - GPT-OSS整合任务1.2.2
"""

import uuid
import logging
import asyncio
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, desc, func, text
from contextlib import contextmanager

from .database import SessionLocal, engine
from .task_metadata_models import (
    ModelCapability, ModelCapabilityResponse
)

logger = logging.getLogger(__name__)

class ModelCapabilityDBError(Exception):
    """模型能力数据库错误"""
    pass

class ModelCapabilityDB:
    """
    模型能力数据库服务
    
    功能：
    1. 模型能力的CRUD操作
    2. 基准测试结果管理
    3. 性能指标分析
    4. 模型推荐和筛选
    """
    
    def __init__(self):
        """初始化模型能力数据库服务"""
        self.logger = logger
        self._ensure_tables()
    
    def _ensure_tables(self):
        """确保数据库表存在"""
        try:
            from .task_metadata_models import Base
            Base.metadata.create_all(bind=engine)
            self.logger.info("✅ Model capability tables created/verified successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to create model capability tables: {e}")
            raise ModelCapabilityDBError(f"Database initialization failed: {e}")
    
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
    
    # ==================== 基础CRUD操作 ====================
    
    async def create_model_capability(
        self,
        provider: str,
        model_id: str,
        model_name: str,
        model_version: Optional[str] = None,
        capability_score: float = 0.5,
        cost_per_1k_input_tokens: float = 0.001,
        cost_per_1k_output_tokens: float = 0.002,
        max_tokens: int = 4096,
        context_length: int = 4096,
        privacy_level: str = "cloud",
        **kwargs
    ) -> ModelCapabilityResponse:
        """
        创建或更新模型能力记录
        
        Args:
            provider: 提供商名称
            model_id: 模型标识符
            model_name: 模型显示名称
            model_version: 模型版本
            capability_score: 综合能力评分 (0-1)
            cost_per_1k_input_tokens: 每1K输入token成本
            cost_per_1k_output_tokens: 每1K输出token成本
            max_tokens: 最大token数
            context_length: 上下文长度
            privacy_level: 隐私级别 (local/cloud/hybrid)
            **kwargs: 其他属性
            
        Returns:
            创建或更新的模型能力信息
            
        Raises:
            ModelCapabilityDBError: 操作失败时抛出
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
                    existing.model_name = model_name
                    existing.model_version = model_version
                    existing.capability_score = capability_score
                    existing.cost_per_1k_input_tokens = cost_per_1k_input_tokens
                    existing.cost_per_1k_output_tokens = cost_per_1k_output_tokens
                    existing.max_tokens = max_tokens
                    existing.context_length = context_length
                    existing.privacy_level = privacy_level
                    existing.updated_at = datetime.now(timezone.utc)
                    
                    # 更新其他属性
                    for key, value in kwargs.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    
                    db_model = existing
                else:
                    # 创建新记录
                    db_model = ModelCapability(
                        provider=provider,
                        model_id=model_id,
                        model_name=model_name,
                        model_version=model_version,
                        capability_score=capability_score,
                        cost_per_1k_input_tokens=cost_per_1k_input_tokens,
                        cost_per_1k_output_tokens=cost_per_1k_output_tokens,
                        max_tokens=max_tokens,
                        context_length=context_length,
                        privacy_level=privacy_level,
                        **{k: v for k, v in kwargs.items() if hasattr(ModelCapability, k)}
                    )
                    session.add(db_model)
                
                session.commit()
                session.refresh(db_model)
                
                self.logger.info(f"✅ Created/updated model capability: {provider}/{model_id}")
                return ModelCapabilityResponse.from_orm(db_model)
                
        except IntegrityError as e:
            self.logger.error(f"❌ Integrity error creating model capability: {e}")
            raise ModelCapabilityDBError(f"Model capability creation failed: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error creating model capability: {e}")
            raise ModelCapabilityDBError(f"Unexpected error: {e}")
    
    async def get_model_capability(
        self,
        provider: str,
        model_id: str
    ) -> Optional[ModelCapabilityResponse]:
        """
        获取模型能力信息
        
        Args:
            provider: 提供商名称
            model_id: 模型标识符
            
        Returns:
            模型能力信息，如果不存在则返回None
        """
        try:
            with self.get_session() as session:
                db_model = session.query(ModelCapability).filter(
                    and_(
                        ModelCapability.provider == provider,
                        ModelCapability.model_id == model_id,
                        ModelCapability.is_available == True
                    )
                ).first()
                
                if db_model:
                    return ModelCapabilityResponse.from_orm(db_model)
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error getting model capability: {e}")
            raise ModelCapabilityDBError(f"Failed to get model capability: {e}")
    
    async def list_model_capabilities(
        self,
        provider: Optional[str] = None,
        privacy_level: Optional[str] = None,
        min_capability_score: Optional[float] = None,
        max_cost_per_1k: Optional[float] = None,
        is_available: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[ModelCapabilityResponse]:
        """
        列出模型能力
        
        Args:
            provider: 提供商过滤
            privacy_level: 隐私级别过滤
            min_capability_score: 最小能力评分
            max_cost_per_1k: 最大每1K token成本
            is_available: 是否可用过滤
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            模型能力列表
        """
        try:
            with self.get_session() as session:
                query = session.query(ModelCapability)
                
                # 添加过滤条件
                if provider:
                    query = query.filter(ModelCapability.provider == provider)
                if privacy_level:
                    query = query.filter(ModelCapability.privacy_level == privacy_level)
                if min_capability_score is not None:
                    query = query.filter(ModelCapability.capability_score >= min_capability_score)
                if max_cost_per_1k is not None:
                    query = query.filter(ModelCapability.cost_per_1k_input_tokens <= max_cost_per_1k)
                if is_available is not None:
                    query = query.filter(ModelCapability.is_available == is_available)
                
                # 排序和分页
                db_models = query.order_by(
                    desc(ModelCapability.capability_score),
                    ModelCapability.cost_per_1k_input_tokens
                ).limit(limit).offset(offset).all()
                
                return [ModelCapabilityResponse.from_orm(model) for model in db_models]
                
        except Exception as e:
            self.logger.error(f"❌ Error listing model capabilities: {e}")
            raise ModelCapabilityDBError(f"Failed to list model capabilities: {e}")
    
    async def update_model_capability(
        self,
        provider: str,
        model_id: str,
        updates: Dict[str, Any]
    ) -> Optional[ModelCapabilityResponse]:
        """
        更新模型能力信息
        
        Args:
            provider: 提供商名称
            model_id: 模型标识符
            updates: 更新字段字典
            
        Returns:
            更新后的模型能力信息
            
        Raises:
            ModelCapabilityDBError: 更新失败时抛出
        """
        try:
            with self.get_session() as session:
                db_model = session.query(ModelCapability).filter(
                    and_(
                        ModelCapability.provider == provider,
                        ModelCapability.model_id == model_id
                    )
                ).first()
                
                if not db_model:
                    return None
                
                # 更新字段
                for field, value in updates.items():
                    if hasattr(db_model, field):
                        setattr(db_model, field, value)
                
                db_model.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                session.refresh(db_model)
                
                self.logger.info(f"✅ Updated model capability: {provider}/{model_id}")
                return ModelCapabilityResponse.from_orm(db_model)
                
        except Exception as e:
            self.logger.error(f"❌ Error updating model capability: {e}")
            raise ModelCapabilityDBError(f"Failed to update model capability: {e}")
    
    async def delete_model_capability(
        self,
        provider: str,
        model_id: str,
        soft_delete: bool = True
    ) -> bool:
        """
        删除模型能力记录
        
        Args:
            provider: 提供商名称
            model_id: 模型标识符
            soft_delete: 是否软删除（设置为不可用）
            
        Returns:
            是否删除成功
        """
        try:
            with self.get_session() as session:
                db_model = session.query(ModelCapability).filter(
                    and_(
                        ModelCapability.provider == provider,
                        ModelCapability.model_id == model_id
                    )
                ).first()
                
                if not db_model:
                    return False
                
                if soft_delete:
                    db_model.is_available = False
                    db_model.updated_at = datetime.now(timezone.utc)
                else:
                    session.delete(db_model)
                
                session.commit()
                
                action = "soft-deleted" if soft_delete else "deleted"
                self.logger.info(f"✅ {action.capitalize()} model capability: {provider}/{model_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error deleting model capability: {e}")
            raise ModelCapabilityDBError(f"Failed to delete model capability: {e}")
    
    # ==================== 基准测试结果管理 ====================
    
    async def update_benchmark_scores(
        self,
        provider: str,
        model_id: str,
        benchmark_results: Dict[str, Any]
    ) -> bool:
        """
        更新模型基准测试结果
        
        Args:
            provider: 提供商名称
            model_id: 模型标识符
            benchmark_results: 基准测试结果
            
        Returns:
            是否更新成功
        """
        try:
            with self.get_session() as session:
                db_model = session.query(ModelCapability).filter(
                    and_(
                        ModelCapability.provider == provider,
                        ModelCapability.model_id == model_id
                    )
                ).first()
                
                if not db_model:
                    self.logger.warning(f"Model {provider}/{model_id} not found for benchmark update")
                    return False
                
                # 更新基准测试结果
                db_model.benchmark_scores = benchmark_results
                db_model.last_benchmarked = datetime.now(timezone.utc)
                
                # 根据基准测试结果更新能力评分
                if 'overall_score' in benchmark_results:
                    db_model.capability_score = benchmark_results['overall_score']
                
                # 更新具体能力评分
                if 'reasoning_score' in benchmark_results:
                    db_model.reasoning_score = benchmark_results['reasoning_score']
                if 'creativity_score' in benchmark_results:
                    db_model.creativity_score = benchmark_results['creativity_score']
                if 'accuracy_score' in benchmark_results:
                    db_model.accuracy_score = benchmark_results['accuracy_score']
                if 'speed_score' in benchmark_results:
                    db_model.speed_score = benchmark_results['speed_score']
                
                # 更新平均延迟
                if 'avg_latency_ms' in benchmark_results:
                    db_model.avg_latency_ms = benchmark_results['avg_latency_ms']
                
                db_model.updated_at = datetime.now(timezone.utc)
                
                session.commit()
                
                self.logger.info(f"✅ Updated benchmark scores for {provider}/{model_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error updating benchmark scores: {e}")
            return False
    
    async def get_benchmark_history(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取基准测试历史记录
        
        Args:
            provider: 提供商过滤
            model_id: 模型过滤
            days_back: 回溯天数
            
        Returns:
            基准测试历史记录列表
        """
        try:
            with self.get_session() as session:
                query = session.query(ModelCapability)
                
                # 添加过滤条件
                if provider:
                    query = query.filter(ModelCapability.provider == provider)
                if model_id:
                    query = query.filter(ModelCapability.model_id == model_id)
                
                # 时间过滤
                time_threshold = datetime.now(timezone.utc) - timedelta(days=days_back)
                query = query.filter(ModelCapability.last_benchmarked >= time_threshold)
                
                models = query.order_by(desc(ModelCapability.last_benchmarked)).all()
                
                history = []
                for model in models:
                    if model.benchmark_scores:
                        history.append({
                            'provider': model.provider,
                            'model_id': model.model_id,
                            'model_name': model.model_name,
                            'benchmark_scores': model.benchmark_scores,
                            'capability_score': model.capability_score,
                            'last_benchmarked': model.last_benchmarked,
                            'updated_at': model.updated_at
                        })
                
                return history
                
        except Exception as e:
            self.logger.error(f"❌ Error getting benchmark history: {e}")
            return []
    
    # ==================== 模型推荐和筛选 ====================
    
    async def recommend_models(
        self,
        task_requirements: Dict[str, Any],
        limit: int = 5
    ) -> List[Tuple[ModelCapabilityResponse, float]]:
        """
        基于任务要求推荐最佳模型
        
        Args:
            task_requirements: 任务要求字典
            limit: 返回模型数量限制
            
        Returns:
            推荐模型列表，每项包含(模型信息, 匹配度评分)
        """
        try:
            # 获取所有可用模型
            all_models = await self.list_model_capabilities(is_available=True)
            
            if not all_models:
                return []
            
            # 计算每个模型的匹配度
            recommendations = []
            for model in all_models:
                match_score = self._calculate_model_match_score(model, task_requirements)
                recommendations.append((model, match_score))
            
            # 按匹配度排序并返回前N个
            recommendations.sort(key=lambda x: x[1], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Error recommending models: {e}")
            return []
    
    def _calculate_model_match_score(
        self,
        model: ModelCapabilityResponse,
        requirements: Dict[str, Any]
    ) -> float:
        """
        计算模型与任务要求的匹配度评分
        
        Args:
            model: 模型信息
            requirements: 任务要求
            
        Returns:
            匹配度评分 (0-1)
        """
        score = 0.0
        total_weight = 0.0
        
        # 能力评分匹配 (权重: 0.4)
        min_capability = requirements.get('min_capability_score', 0.0)
        if model.capability_score >= min_capability:
            capability_weight = 0.4
            capability_match = min(1.0, model.capability_score / max(min_capability, 0.1))
            score += capability_match * capability_weight
            total_weight += capability_weight
        
        # 成本匹配 (权重: 0.3)
        max_cost = requirements.get('max_cost_per_1k', float('inf'))
        if model.cost_per_1k_input_tokens <= max_cost:
            cost_weight = 0.3
            # 成本越低分数越高
            cost_ratio = 1.0 - (model.cost_per_1k_input_tokens / max(max_cost, 0.001))
            score += max(0.0, cost_ratio) * cost_weight
            total_weight += cost_weight
        
        # 延迟匹配 (权重: 0.2)
        max_latency = requirements.get('max_latency_ms', float('inf'))
        if model.avg_latency_ms <= max_latency:
            latency_weight = 0.2
            # 延迟越低分数越高
            latency_ratio = 1.0 - (model.avg_latency_ms / max(max_latency, 1.0))
            score += max(0.0, latency_ratio) * latency_weight
            total_weight += latency_weight
        
        # 隐私级别匹配 (权重: 0.1)
        required_privacy = requirements.get('privacy_level')
        if required_privacy:
            privacy_weight = 0.1
            if model.privacy_level == required_privacy:
                score += 1.0 * privacy_weight
            elif required_privacy == 'local' and model.privacy_level in ['local', 'hybrid']:
                score += 0.8 * privacy_weight
            elif required_privacy == 'cloud' and model.privacy_level in ['cloud', 'hybrid']:
                score += 0.8 * privacy_weight
            total_weight += privacy_weight
        
        # 特性支持匹配
        required_features = requirements.get('required_features', [])
        if required_features and model.supported_features:
            feature_weight = 0.1
            supported_count = sum(1 for feature in required_features if feature in model.supported_features)
            feature_match = supported_count / len(required_features) if required_features else 1.0
            score += feature_match * feature_weight
            total_weight += feature_weight
        
        # 归一化评分
        return score / max(total_weight, 0.1)
    
    # ==================== 性能分析和统计 ====================
    
    async def get_performance_statistics(
        self,
        provider: Optional[str] = None,
        privacy_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取模型性能统计信息
        
        Args:
            provider: 提供商过滤
            privacy_level: 隐私级别过滤
            
        Returns:
            性能统计信息
        """
        try:
            models = await self.list_model_capabilities(
                provider=provider,
                privacy_level=privacy_level,
                is_available=True
            )
            
            if not models:
                return {}
            
            # 计算统计指标
            capability_scores = [m.capability_score for m in models if m.capability_score is not None]
            cost_scores = [m.cost_per_1k_input_tokens for m in models if m.cost_per_1k_input_tokens is not None]
            latency_scores = [m.avg_latency_ms for m in models if m.avg_latency_ms is not None]
            
            stats = {
                'total_models': len(models),
                'providers': list(set(m.provider for m in models)),
                'privacy_levels': list(set(m.privacy_level for m in models)),
                'capability_stats': {
                    'mean': statistics.mean(capability_scores) if capability_scores else 0,
                    'median': statistics.median(capability_scores) if capability_scores else 0,
                    'std': statistics.stdev(capability_scores) if len(capability_scores) > 1 else 0,
                    'min': min(capability_scores) if capability_scores else 0,
                    'max': max(capability_scores) if capability_scores else 0
                },
                'cost_stats': {
                    'mean': statistics.mean(cost_scores) if cost_scores else 0,
                    'median': statistics.median(cost_scores) if cost_scores else 0,
                    'std': statistics.stdev(cost_scores) if len(cost_scores) > 1 else 0,
                    'min': min(cost_scores) if cost_scores else 0,
                    'max': max(cost_scores) if cost_scores else 0
                },
                'latency_stats': {
                    'mean': statistics.mean(latency_scores) if latency_scores else 0,
                    'median': statistics.median(latency_scores) if latency_scores else 0,
                    'std': statistics.stdev(latency_scores) if len(latency_scores) > 1 else 0,
                    'min': min(latency_scores) if latency_scores else 0,
                    'max': max(latency_scores) if latency_scores else 0
                },
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Error getting performance statistics: {e}")
            return {}
    
    # ==================== 初始化标准模型 ====================
    
    async def initialize_standard_models(self) -> List[str]:
        """
        初始化标准模型能力记录
        
        Returns:
            初始化的模型列表
        """
        standard_models = [
            # GPT-OSS 本地模型
            {
                'provider': 'gpt_oss',
                'model_id': 'gpt-oss-local',
                'model_name': 'GPT-OSS Local Model',
                'model_version': '1.0',
                'capability_score': 0.75,
                'reasoning_score': 0.8,
                'creativity_score': 0.7,
                'accuracy_score': 0.85,
                'speed_score': 0.9,
                'cost_per_1k_input_tokens': 0.0,  # 本地免费
                'cost_per_1k_output_tokens': 0.0,
                'max_tokens': 4096,
                'avg_latency_ms': 500.0,
                'supported_features': ['reasoning', 'generation', 'analysis'],
                'supported_languages': ['zh', 'en'],
                'context_length': 4096,
                'is_available': True,
                'privacy_level': 'local',
                'metadata': {
                    'description': '本地部署的GPT-OSS模型，提供高隐私保护',
                    'deployment_type': 'local',
                    'hardware_requirements': 'GPU recommended'
                }
            },
            
            # OpenAI GPT-4
            {
                'provider': 'openai',
                'model_id': 'gpt-4',
                'model_name': 'GPT-4',
                'model_version': '0613',
                'capability_score': 0.95,
                'reasoning_score': 0.95,
                'creativity_score': 0.9,
                'accuracy_score': 0.95,
                'speed_score': 0.6,
                'cost_per_1k_input_tokens': 0.03,
                'cost_per_1k_output_tokens': 0.06,
                'max_tokens': 8192,
                'avg_latency_ms': 2000.0,
                'supported_features': ['reasoning', 'generation', 'analysis', 'function_calling'],
                'supported_languages': ['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es'],
                'context_length': 8192,
                'is_available': True,
                'privacy_level': 'cloud',
                'metadata': {
                    'description': 'OpenAI最先进的语言模型',
                    'deployment_type': 'cloud',
                    'rate_limits': '10,000 RPM'
                }
            },
            
            # OpenAI GPT-3.5 Turbo
            {
                'provider': 'openai',
                'model_id': 'gpt-3.5-turbo',
                'model_name': 'GPT-3.5 Turbo',
                'model_version': '0613',
                'capability_score': 0.85,
                'reasoning_score': 0.8,
                'creativity_score': 0.85,
                'accuracy_score': 0.85,
                'speed_score': 0.9,
                'cost_per_1k_input_tokens': 0.001,
                'cost_per_1k_output_tokens': 0.002,
                'max_tokens': 4096,
                'avg_latency_ms': 1000.0,
                'supported_features': ['reasoning', 'generation', 'analysis', 'function_calling'],
                'supported_languages': ['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es'],
                'context_length': 4096,
                'is_available': True,
                'privacy_level': 'cloud',
                'metadata': {
                    'description': 'OpenAI高性价比语言模型',
                    'deployment_type': 'cloud',
                    'rate_limits': '60,000 RPM'
                }
            },
            
            # Anthropic Claude
            {
                'provider': 'anthropic',
                'model_id': 'claude-3-sonnet-20240229',
                'model_name': 'Claude 3 Sonnet',
                'model_version': '20240229',
                'capability_score': 0.9,
                'reasoning_score': 0.9,
                'creativity_score': 0.85,
                'accuracy_score': 0.9,
                'speed_score': 0.7,
                'cost_per_1k_input_tokens': 0.003,
                'cost_per_1k_output_tokens': 0.015,
                'max_tokens': 4096,
                'avg_latency_ms': 1500.0,
                'supported_features': ['reasoning', 'generation', 'analysis'],
                'supported_languages': ['zh', 'en', 'ja', 'ko', 'fr', 'de', 'es'],
                'context_length': 200000,
                'is_available': True,
                'privacy_level': 'cloud',
                'metadata': {
                    'description': 'Anthropic安全可靠的语言模型',
                    'deployment_type': 'cloud',
                    'context_advantage': 'Ultra-long context support'
                }
            }
        ]
        
        initialized_models = []
        
        for model_data in standard_models:
            try:
                existing = await self.get_model_capability(
                    model_data['provider'], 
                    model_data['model_id']
                )
                
                if not existing:
                    await self.create_model_capability(**model_data)
                    initialized_models.append(f"{model_data['provider']}/{model_data['model_id']}")
                    self.logger.info(f"✅ Initialized model: {model_data['provider']}/{model_data['model_id']}")
                else:
                    self.logger.info(f"ℹ️ Model already exists: {model_data['provider']}/{model_data['model_id']}")
                    
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize model {model_data['provider']}/{model_data['model_id']}: {e}")
        
        return initialized_models