#!/usr/bin/env python3
"""
A/B Testing and Canary Deployment System
A/B測試和灰度更新系統 - GPT-OSS整合任務1.2.3
"""

import asyncio
import logging
import time
import random
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from contextlib import asynccontextmanager

from ..database.model_capability_db import ModelCapabilityDB
from ..monitoring.performance_monitor import PerformanceMonitor, MetricType
from .model_version_control import ModelVersionControl, VersionUpdateRequest, ChangeType, DeploymentStage

logger = logging.getLogger(__name__)

class ExperimentType(Enum):
    """實驗類型"""
    AB_TEST = "ab_test"
    CANARY_DEPLOYMENT = "canary_deployment"
    GRADUAL_ROLLOUT = "gradual_rollout"
    BLUE_GREEN = "blue_green"
    SHADOW_TESTING = "shadow_testing"

class ExperimentStatus(Enum):
    """實驗狀態"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class TrafficSplitStrategy(Enum):
    """流量分割策略"""
    RANDOM = "random"
    USER_ID_HASH = "user_id_hash"
    GEOGRAPHIC = "geographic"
    FEATURE_FLAG = "feature_flag"
    PERCENTAGE = "percentage"

class ExperimentDecision(Enum):
    """實驗決策"""
    CONTINUE = "continue"
    PROMOTE_VARIANT = "promote_variant"
    ROLLBACK = "rollback"
    EXTEND = "extend"
    TERMINATE = "terminate"

@dataclass
class TrafficSplitConfig:
    """流量分割配置"""
    strategy: TrafficSplitStrategy
    control_percentage: float  # 控制組百分比 (0-100)
    variant_percentage: float  # 變體組百分比 (0-100)
    ramp_up_schedule: Optional[List[Tuple[datetime, float]]] = None  # 漸進式部署時間表
    filters: Dict[str, Any] = field(default_factory=dict)  # 過濾條件

@dataclass
class ExperimentVariant:
    """實驗變體"""
    variant_id: str
    variant_name: str
    provider: str
    model_id: str
    model_version: str
    configuration: Dict[str, Any]
    traffic_percentage: float
    
    # 性能指標
    metrics: Dict[str, List[float]] = field(default_factory=dict)
    sample_count: int = 0
    
    # 狀態
    is_control: bool = False
    is_enabled: bool = True

@dataclass
class ExperimentMetrics:
    """實驗指標"""
    variant_id: str
    metric_name: str
    values: List[float]
    timestamps: List[datetime]
    
    def get_statistics(self) -> Dict[str, float]:
        """獲取統計信息"""
        if not self.values:
            return {}
        
        return {
            'mean': statistics.mean(self.values),
            'median': statistics.median(self.values),
            'std': statistics.stdev(self.values) if len(self.values) > 1 else 0.0,
            'min': min(self.values),
            'max': max(self.values),
            'count': len(self.values),
            'p95': statistics.quantiles(self.values, n=20)[18] if len(self.values) >= 20 else max(self.values),
            'p99': statistics.quantiles(self.values, n=100)[98] if len(self.values) >= 100 else max(self.values)
        }

@dataclass
class StatisticalTestResult:
    """統計檢驗結果"""
    test_name: str
    p_value: float
    confidence_level: float
    is_significant: bool
    effect_size: float
    power: float
    sample_size_recommendation: Optional[int] = None

@dataclass
class Experiment:
    """A/B測試實驗"""
    experiment_id: str
    experiment_name: str
    experiment_type: ExperimentType
    description: str
    
    # 實驗配置
    variants: Dict[str, ExperimentVariant]
    traffic_split: TrafficSplitConfig
    
    # 實驗時間
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    planned_duration_hours: int = 24
    
    # 狀態
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = "system"
    
    # 實驗指標
    primary_metrics: List[str] = field(default_factory=lambda: ["capability_score", "latency"])
    secondary_metrics: List[str] = field(default_factory=lambda: ["accuracy", "cost"])
    
    # 停止條件
    stop_conditions: Dict[str, Any] = field(default_factory=dict)
    significance_threshold: float = 0.05
    minimum_sample_size: int = 100
    
    # 結果
    results: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[ExperimentDecision] = None
    decision_reason: str = ""

class ABTestingSystem:
    """
    A/B測試和灰度更新系統
    
    功能：
    1. A/B測試實驗管理
    2. 灰度/金絲雀部署
    3. 流量分割和路由
    4. 統計顯著性檢驗
    5. 自動決策和回滾
    6. 實驗結果分析
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        version_control: Optional[ModelVersionControl] = None
    ):
        """初始化A/B測試系統"""
        self.model_db = model_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.version_control = version_control or ModelVersionControl()
        
        self.logger = logger
        
        # 實驗管理
        self.experiments: Dict[str, Experiment] = {}
        self.active_experiments: Dict[str, Experiment] = {}
        
        # 流量路由緩存
        self.routing_cache: Dict[str, str] = {}  # user_id -> variant_id
        self.cache_ttl: Dict[str, datetime] = {}
        
        # 運行時狀態
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 統計
        self.experiment_stats = {
            'total_experiments': 0,
            'active_experiments': 0,
            'completed_experiments': 0,
            'successful_promotions': 0,
            'rollbacks': 0
        }
    
    async def start(self):
        """啟動A/B測試系統"""
        if not self._running:
            self._running = True
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("✅ A/B testing system started")
    
    async def stop(self):
        """停止A/B測試系統"""
        if self._running:
            self._running = False
            
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("✅ A/B testing system stopped")
    
    async def _monitoring_loop(self):
        """監控主循環"""
        while self._running:
            try:
                await self._update_experiment_metrics()
                await self._evaluate_stop_conditions()
                await self._cleanup_cache()
                
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in A/B testing monitoring loop: {e}")
                await asyncio.sleep(10)
    
    # ==================== 實驗管理 ====================
    
    async def create_experiment(
        self,
        experiment_name: str,
        experiment_type: ExperimentType,
        description: str,
        control_variant: Dict[str, Any],
        test_variants: List[Dict[str, Any]],
        traffic_split: TrafficSplitConfig,
        primary_metrics: List[str],
        planned_duration_hours: int = 24,
        **kwargs
    ) -> str:
        """
        創建A/B測試實驗
        
        Args:
            experiment_name: 實驗名稱
            experiment_type: 實驗類型
            description: 實驗描述
            control_variant: 控制組變體配置
            test_variants: 測試組變體配置列表
            traffic_split: 流量分割配置
            primary_metrics: 主要指標
            planned_duration_hours: 計劃持續時間（小時）
            **kwargs: 其他參數
            
        Returns:
            實驗ID
        """
        try:
            experiment_id = f"exp_{int(time.time())}_{experiment_name}".replace(' ', '_')
            
            # 創建變體
            variants = {}
            
            # 創建控制組
            control_id = f"{experiment_id}_control"
            variants[control_id] = ExperimentVariant(
                variant_id=control_id,
                variant_name="Control",
                provider=control_variant['provider'],
                model_id=control_variant['model_id'],
                model_version=control_variant.get('model_version', 'current'),
                configuration=control_variant.get('configuration', {}),
                traffic_percentage=traffic_split.control_percentage,
                is_control=True
            )
            
            # 創建測試組變體
            for i, test_variant in enumerate(test_variants):
                variant_id = f"{experiment_id}_variant_{i+1}"
                variants[variant_id] = ExperimentVariant(
                    variant_id=variant_id,
                    variant_name=test_variant.get('name', f"Variant {i+1}"),
                    provider=test_variant['provider'],
                    model_id=test_variant['model_id'],
                    model_version=test_variant.get('model_version', 'latest'),
                    configuration=test_variant.get('configuration', {}),
                    traffic_percentage=traffic_split.variant_percentage / len(test_variants)
                )
            
            # 創建實驗
            experiment = Experiment(
                experiment_id=experiment_id,
                experiment_name=experiment_name,
                experiment_type=experiment_type,
                description=description,
                variants=variants,
                traffic_split=traffic_split,
                planned_duration_hours=planned_duration_hours,
                primary_metrics=primary_metrics,
                secondary_metrics=kwargs.get('secondary_metrics', ['accuracy', 'cost']),
                significance_threshold=kwargs.get('significance_threshold', 0.05),
                minimum_sample_size=kwargs.get('minimum_sample_size', 100),
                stop_conditions=kwargs.get('stop_conditions', {}),
                created_by=kwargs.get('created_by', 'system')
            )
            
            self.experiments[experiment_id] = experiment
            self.experiment_stats['total_experiments'] += 1
            
            self.logger.info(f"✅ Created experiment: {experiment_id}")
            return experiment_id
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create experiment: {e}")
            raise
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """啟動實驗"""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            experiment = self.experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.DRAFT:
                raise ValueError(f"Experiment {experiment_id} is not in draft status")
            
            # 驗證實驗配置
            await self._validate_experiment_config(experiment)
            
            # 啟動實驗
            experiment.status = ExperimentStatus.RUNNING
            experiment.start_time = datetime.now(timezone.utc)
            experiment.end_time = experiment.start_time + timedelta(hours=experiment.planned_duration_hours)
            
            # 添加到活躍實驗
            self.active_experiments[experiment_id] = experiment
            self.experiment_stats['active_experiments'] += 1
            
            # 如果是灰度部署，設置版本階段
            if experiment.experiment_type == ExperimentType.CANARY_DEPLOYMENT:
                await self._setup_canary_deployment(experiment)
            
            self.logger.info(f"✅ Started experiment: {experiment_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start experiment {experiment_id}: {e}")
            return False
    
    async def _validate_experiment_config(self, experiment: Experiment):
        """驗證實驗配置"""
        # 檢查變體模型是否存在
        for variant in experiment.variants.values():
            model = await self.model_db.get_model_capability(variant.provider, variant.model_id)
            if not model:
                raise ValueError(f"Model {variant.provider}/{variant.model_id} not found")
            if not model.is_available:
                raise ValueError(f"Model {variant.provider}/{variant.model_id} is not available")
        
        # 檢查流量分割是否合理
        total_traffic = sum(v.traffic_percentage for v in experiment.variants.values())
        if abs(total_traffic - 100.0) > 0.01:
            raise ValueError(f"Traffic split does not add up to 100%: {total_traffic}")
    
    async def _setup_canary_deployment(self, experiment: Experiment):
        """設置灰度部署"""
        for variant in experiment.variants.values():
            if not variant.is_control:
                # 將測試變體設為canary階段
                await self.version_control.promote_version_stage(
                    provider=variant.provider,
                    model_id=variant.model_id,
                    version=variant.model_version,
                    target_stage=DeploymentStage.CANARY
                )
    
    # ==================== 流量路由 ====================
    
    async def route_request(
        self,
        experiment_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ExperimentVariant]:
        """
        路由請求到實驗變體
        
        Args:
            experiment_id: 實驗ID
            user_id: 用戶ID
            context: 請求上下文
            
        Returns:
            選中的變體，如果實驗不活躍則返回None
        """
        try:
            if experiment_id not in self.active_experiments:
                return None
            
            experiment = self.active_experiments[experiment_id]
            
            # 檢查實驗是否仍然活躍
            if experiment.status != ExperimentStatus.RUNNING:
                return None
            
            # 檢查緩存
            cache_key = f"{experiment_id}:{user_id}"
            if cache_key in self.routing_cache:
                cache_time = self.cache_ttl.get(cache_key)
                if cache_time and datetime.now(timezone.utc) < cache_time:
                    variant_id = self.routing_cache[cache_key]
                    return experiment.variants.get(variant_id)
            
            # 進行流量分割
            selected_variant = await self._split_traffic(experiment, user_id, context)
            
            # 更新緩存
            if selected_variant:
                self.routing_cache[cache_key] = selected_variant.variant_id
                self.cache_ttl[cache_key] = datetime.now(timezone.utc) + timedelta(hours=1)
            
            return selected_variant
            
        except Exception as e:
            self.logger.error(f"❌ Error routing request for experiment {experiment_id}: {e}")
            return None
    
    async def _split_traffic(
        self,
        experiment: Experiment,
        user_id: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[ExperimentVariant]:
        """執行流量分割"""
        try:
            strategy = experiment.traffic_split.strategy
            
            if strategy == TrafficSplitStrategy.RANDOM:
                return self._random_split(experiment)
            
            elif strategy == TrafficSplitStrategy.USER_ID_HASH:
                return self._hash_based_split(experiment, user_id)
            
            elif strategy == TrafficSplitStrategy.PERCENTAGE:
                return self._percentage_split(experiment)
            
            elif strategy == TrafficSplitStrategy.FEATURE_FLAG:
                return self._feature_flag_split(experiment, context)
            
            else:
                # 默認使用隨機分割
                return self._random_split(experiment)
                
        except Exception as e:
            self.logger.error(f"❌ Error in traffic splitting: {e}")
            return None
    
    def _random_split(self, experiment: Experiment) -> ExperimentVariant:
        """隨機流量分割"""
        rand_val = random.random() * 100
        cumulative = 0
        
        for variant in experiment.variants.values():
            cumulative += variant.traffic_percentage
            if rand_val <= cumulative:
                return variant
        
        # 默認返回控制組
        return next(v for v in experiment.variants.values() if v.is_control)
    
    def _hash_based_split(self, experiment: Experiment, user_id: str) -> ExperimentVariant:
        """基於用戶ID哈希的分割"""
        # 使用用戶ID和實驗ID創建確定性哈希
        hash_input = f"{experiment.experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = (hash_value % 100) + 1  # 1-100
        
        cumulative = 0
        for variant in experiment.variants.values():
            cumulative += variant.traffic_percentage
            if bucket <= cumulative:
                return variant
        
        return next(v for v in experiment.variants.values() if v.is_control)
    
    def _percentage_split(self, experiment: Experiment) -> ExperimentVariant:
        """基於百分比的分割"""
        # 檢查是否有漸進式部署計劃
        ramp_up = experiment.traffic_split.ramp_up_schedule
        if ramp_up:
            current_time = datetime.now(timezone.utc)
            
            # 找到當前應該使用的流量百分比
            for schedule_time, percentage in ramp_up:
                if current_time >= schedule_time:
                    # 更新變體流量百分比
                    for variant in experiment.variants.values():
                        if not variant.is_control:
                            variant.traffic_percentage = percentage
                            # 相應調整控制組
                            control_variant = next(v for v in experiment.variants.values() if v.is_control)
                            control_variant.traffic_percentage = 100 - percentage
                    break
        
        return self._random_split(experiment)
    
    def _feature_flag_split(
        self,
        experiment: Experiment,
        context: Optional[Dict[str, Any]]
    ) -> ExperimentVariant:
        """基於特性標誌的分割"""
        if not context:
            return next(v for v in experiment.variants.values() if v.is_control)
        
        # 檢查特性標誌
        feature_flags = context.get('feature_flags', {})
        experiment_flag = feature_flags.get(experiment.experiment_id, False)
        
        if experiment_flag:
            # 如果啟用特性標誌，使用測試變體
            test_variants = [v for v in experiment.variants.values() if not v.is_control]
            if test_variants:
                return random.choice(test_variants)
        
        # 默認使用控制組
        return next(v for v in experiment.variants.values() if v.is_control)
    
    # ==================== 指標收集和分析 ====================
    
    async def record_experiment_metric(
        self,
        experiment_id: str,
        variant_id: str,
        metric_name: str,
        value: float,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """記錄實驗指標"""
        try:
            if experiment_id not in self.active_experiments:
                return
            
            experiment = self.active_experiments[experiment_id]
            
            if variant_id not in experiment.variants:
                return
            
            variant = experiment.variants[variant_id]
            
            # 記錄到變體指標
            if metric_name not in variant.metrics:
                variant.metrics[metric_name] = []
            
            variant.metrics[metric_name].append(value)
            variant.sample_count += 1
            
            self.logger.debug(f"📊 Recorded metric {metric_name}={value} for {experiment_id}/{variant_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error recording experiment metric: {e}")
    
    async def _update_experiment_metrics(self):
        """更新實驗指標"""
        for experiment in self.active_experiments.values():
            try:
                await self._collect_performance_metrics(experiment)
            except Exception as e:
                self.logger.error(f"❌ Error updating metrics for experiment {experiment.experiment_id}: {e}")
    
    async def _collect_performance_metrics(self, experiment: Experiment):
        """收集性能指標"""
        for variant in experiment.variants.values():
            # 從性能監控器獲取指標
            current_metrics = self.performance_monitor.get_current_metrics(
                variant.provider, variant.model_id
            )
            
            for metric_key, metric_stats in current_metrics.items():
                metric_type = metric_key.split('/')[-1]
                
                if metric_type in experiment.primary_metrics or metric_type in experiment.secondary_metrics:
                    mean_value = metric_stats.get('mean')
                    
                    if mean_value is not None:
                        await self.record_experiment_metric(
                            experiment.experiment_id,
                            variant.variant_id,
                            metric_type,
                            mean_value
                        )
    
    # ==================== 統計分析 ====================
    
    async def analyze_experiment_results(self, experiment_id: str) -> Dict[str, Any]:
        """分析實驗結果"""
        try:
            if experiment_id not in self.experiments:
                raise ValueError(f"Experiment {experiment_id} not found")
            
            experiment = self.experiments[experiment_id]
            
            # 獲取控制組和測試組
            control_variant = next(v for v in experiment.variants.values() if v.is_control)
            test_variants = [v for v in experiment.variants.values() if not v.is_control]
            
            analysis_results = {
                'experiment_id': experiment_id,
                'experiment_name': experiment.experiment_name,
                'status': experiment.status.value,
                'duration_hours': self._calculate_experiment_duration(experiment),
                'sample_sizes': {},
                'metric_comparisons': {},
                'statistical_tests': {},
                'recommendations': []
            }
            
            # 計算樣本大小
            for variant in experiment.variants.values():
                analysis_results['sample_sizes'][variant.variant_id] = variant.sample_count
            
            # 對每個主要指標進行分析
            for metric_name in experiment.primary_metrics:
                metric_analysis = await self._analyze_metric(
                    metric_name, control_variant, test_variants, experiment.significance_threshold
                )
                analysis_results['metric_comparisons'][metric_name] = metric_analysis
            
            # 生成建議
            analysis_results['recommendations'] = self._generate_experiment_recommendations(
                experiment, analysis_results
            )
            
            # 更新實驗結果
            experiment.results = analysis_results
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing experiment results: {e}")
            return {'error': str(e)}
    
    async def _analyze_metric(
        self,
        metric_name: str,
        control_variant: ExperimentVariant,
        test_variants: List[ExperimentVariant],
        significance_threshold: float
    ) -> Dict[str, Any]:
        """分析單個指標"""
        try:
            control_values = control_variant.metrics.get(metric_name, [])
            
            metric_analysis = {
                'control_stats': self._calculate_metric_stats(control_values),
                'variant_comparisons': []
            }
            
            for test_variant in test_variants:
                test_values = test_variant.metrics.get(metric_name, [])
                
                if len(control_values) < 10 or len(test_values) < 10:
                    # 樣本不足
                    comparison = {
                        'variant_id': test_variant.variant_id,
                        'variant_name': test_variant.variant_name,
                        'test_stats': self._calculate_metric_stats(test_values),
                        'statistical_test': {
                            'test_name': 'insufficient_data',
                            'is_significant': False,
                            'p_value': None,
                            'message': 'Insufficient sample size for statistical testing'
                        }
                    }
                else:
                    # 進行統計檢驗
                    test_result = self._perform_statistical_test(
                        control_values, test_values, significance_threshold
                    )
                    
                    comparison = {
                        'variant_id': test_variant.variant_id,
                        'variant_name': test_variant.variant_name,
                        'test_stats': self._calculate_metric_stats(test_values),
                        'statistical_test': {
                            'test_name': test_result.test_name,
                            'is_significant': test_result.is_significant,
                            'p_value': test_result.p_value,
                            'effect_size': test_result.effect_size,
                            'confidence_level': test_result.confidence_level
                        },
                        'improvement': self._calculate_improvement(control_values, test_values)
                    }
                
                metric_analysis['variant_comparisons'].append(comparison)
            
            return metric_analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing metric {metric_name}: {e}")
            return {'error': str(e)}
    
    def _calculate_metric_stats(self, values: List[float]) -> Dict[str, float]:
        """計算指標統計信息"""
        if not values:
            return {}
        
        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std': statistics.stdev(values) if len(values) > 1 else 0.0,
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }
    
    def _perform_statistical_test(
        self,
        control_values: List[float],
        test_values: List[float],
        significance_threshold: float
    ) -> StatisticalTestResult:
        """執行統計顯著性檢驗"""
        try:
            # 簡化的t檢驗實現
            import scipy.stats as stats
            
            # 執行獨立樣本t檢驗
            t_stat, p_value = stats.ttest_ind(test_values, control_values)
            
            is_significant = p_value < significance_threshold
            
            # 計算效應大小（Cohen's d）
            control_mean = statistics.mean(control_values)
            test_mean = statistics.mean(test_values)
            pooled_std = statistics.stdev(control_values + test_values)
            
            effect_size = (test_mean - control_mean) / pooled_std if pooled_std > 0 else 0.0
            
            return StatisticalTestResult(
                test_name="independent_t_test",
                p_value=p_value,
                confidence_level=1 - significance_threshold,
                is_significant=is_significant,
                effect_size=effect_size,
                power=0.8  # 簡化假設
            )
            
        except ImportError:
            # 如果沒有scipy，使用簡化檢驗
            return self._simple_significance_test(
                control_values, test_values, significance_threshold
            )
        except Exception as e:
            self.logger.error(f"❌ Error in statistical test: {e}")
            return StatisticalTestResult(
                test_name="error",
                p_value=1.0,
                confidence_level=0.0,
                is_significant=False,
                effect_size=0.0,
                power=0.0
            )
    
    def _simple_significance_test(
        self,
        control_values: List[float],
        test_values: List[float],
        significance_threshold: float
    ) -> StatisticalTestResult:
        """簡化的顯著性檢驗"""
        try:
            control_mean = statistics.mean(control_values)
            test_mean = statistics.mean(test_values)
            
            # 簡化的差異檢驗
            relative_difference = abs(test_mean - control_mean) / abs(control_mean) if control_mean != 0 else 0
            
            # 簡單規則：如果差異超過10%且樣本足夠，認為顯著
            is_significant = (
                relative_difference > 0.1 and
                len(control_values) >= 30 and
                len(test_values) >= 30
            )
            
            # 模擬p值
            p_value = 0.01 if is_significant else 0.5
            
            effect_size = (test_mean - control_mean) / control_mean if control_mean != 0 else 0
            
            return StatisticalTestResult(
                test_name="simple_difference_test",
                p_value=p_value,
                confidence_level=1 - significance_threshold,
                is_significant=is_significant,
                effect_size=effect_size,
                power=0.8
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error in simple significance test: {e}")
            return StatisticalTestResult(
                test_name="error",
                p_value=1.0,
                confidence_level=0.0,
                is_significant=False,
                effect_size=0.0,
                power=0.0
            )
    
    def _calculate_improvement(self, control_values: List[float], test_values: List[float]) -> Dict[str, float]:
        """計算改進幅度"""
        if not control_values or not test_values:
            return {}
        
        control_mean = statistics.mean(control_values)
        test_mean = statistics.mean(test_values)
        
        if control_mean == 0:
            return {'absolute_improvement': test_mean - control_mean}
        
        relative_improvement = ((test_mean - control_mean) / abs(control_mean)) * 100
        
        return {
            'absolute_improvement': test_mean - control_mean,
            'relative_improvement_percent': relative_improvement
        }
    
    def _calculate_experiment_duration(self, experiment: Experiment) -> float:
        """計算實驗持續時間"""
        if not experiment.start_time:
            return 0.0
        
        end_time = experiment.end_time or datetime.now(timezone.utc)
        duration = end_time - experiment.start_time
        return duration.total_seconds() / 3600  # 轉換為小時
    
    # ==================== 停止條件和決策 ====================
    
    async def _evaluate_stop_conditions(self):
        """評估停止條件"""
        for experiment in list(self.active_experiments.values()):
            try:
                decision = await self._evaluate_experiment_decision(experiment)
                
                if decision != ExperimentDecision.CONTINUE:
                    await self._execute_experiment_decision(experiment, decision)
                    
            except Exception as e:
                self.logger.error(f"❌ Error evaluating stop conditions for {experiment.experiment_id}: {e}")
    
    async def _evaluate_experiment_decision(self, experiment: Experiment) -> ExperimentDecision:
        """評估實驗決策"""
        current_time = datetime.now(timezone.utc)
        
        # 檢查時間限制
        if experiment.end_time and current_time >= experiment.end_time:
            # 分析結果決定是否推廣
            analysis = await self.analyze_experiment_results(experiment.experiment_id)
            
            if self._should_promote_variant(analysis):
                return ExperimentDecision.PROMOTE_VARIANT
            else:
                return ExperimentDecision.TERMINATE
        
        # 檢查最小樣本大小
        min_samples = experiment.minimum_sample_size
        all_variants_ready = all(
            v.sample_count >= min_samples for v in experiment.variants.values()
        )
        
        if not all_variants_ready:
            return ExperimentDecision.CONTINUE
        
        # 檢查停止條件
        stop_conditions = experiment.stop_conditions
        
        # 早期停止條件：顯著差異
        if stop_conditions.get('early_stop_on_significance', False):
            analysis = await self.analyze_experiment_results(experiment.experiment_id)
            
            for metric_name in experiment.primary_metrics:
                metric_analysis = analysis.get('metric_comparisons', {}).get(metric_name, {})
                
                for comparison in metric_analysis.get('variant_comparisons', []):
                    stat_test = comparison.get('statistical_test', {})
                    
                    if stat_test.get('is_significant', False):
                        improvement = comparison.get('improvement', {})
                        relative_improvement = improvement.get('relative_improvement_percent', 0)
                        
                        # 如果有顯著改進，推廣變體
                        if relative_improvement > 5:  # 5%以上改進
                            return ExperimentDecision.PROMOTE_VARIANT
                        # 如果有顯著退化，回滾
                        elif relative_improvement < -5:
                            return ExperimentDecision.ROLLBACK
        
        # 檢查性能退化
        if self._check_performance_degradation(experiment):
            return ExperimentDecision.ROLLBACK
        
        return ExperimentDecision.CONTINUE
    
    def _should_promote_variant(self, analysis: Dict[str, Any]) -> bool:
        """判斷是否應該推廣變體"""
        try:
            metric_comparisons = analysis.get('metric_comparisons', {})
            
            promotion_score = 0
            total_metrics = 0
            
            for metric_name, metric_analysis in metric_comparisons.items():
                for comparison in metric_analysis.get('variant_comparisons', []):
                    total_metrics += 1
                    
                    stat_test = comparison.get('statistical_test', {})
                    improvement = comparison.get('improvement', {})
                    
                    if stat_test.get('is_significant', False):
                        relative_improvement = improvement.get('relative_improvement_percent', 0)
                        
                        if relative_improvement > 2:  # 2%以上改進
                            promotion_score += 2
                        elif relative_improvement > 0:
                            promotion_score += 1
                        else:
                            promotion_score -= 1
                    
            # 如果大部分指標有改進，推廣變體
            return promotion_score > total_metrics * 0.5
            
        except Exception as e:
            self.logger.error(f"❌ Error in promotion decision: {e}")
            return False
    
    def _check_performance_degradation(self, experiment: Experiment) -> bool:
        """檢查性能是否退化"""
        try:
            # 檢查測試變體的關鍵指標是否大幅下降
            for variant in experiment.variants.values():
                if variant.is_control:
                    continue
                
                # 檢查錯誤率
                error_rates = variant.metrics.get('error_rate', [])
                if error_rates and len(error_rates) >= 10:
                    recent_error_rate = statistics.mean(error_rates[-10:])
                    if recent_error_rate > 0.2:  # 錯誤率超過20%
                        return True
                
                # 檢查延遲
                latencies = variant.metrics.get('latency', [])
                if latencies and len(latencies) >= 10:
                    recent_latency = statistics.mean(latencies[-10:])
                    if recent_latency > 10000:  # 延遲超過10秒
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking performance degradation: {e}")
            return True  # 出錯時保守處理
    
    async def _execute_experiment_decision(self, experiment: Experiment, decision: ExperimentDecision):
        """執行實驗決策"""
        try:
            experiment.decision = decision
            experiment.decision_reason = f"Automated decision based on {decision.value}"
            
            if decision == ExperimentDecision.PROMOTE_VARIANT:
                await self._promote_winning_variant(experiment)
                
            elif decision == ExperimentDecision.ROLLBACK:
                await self._rollback_experiment(experiment)
                
            elif decision == ExperimentDecision.TERMINATE:
                await self._terminate_experiment(experiment)
            
            # 從活躍實驗中移除
            if experiment.experiment_id in self.active_experiments:
                del self.active_experiments[experiment.experiment_id]
                self.experiment_stats['active_experiments'] -= 1
                
        except Exception as e:
            self.logger.error(f"❌ Error executing experiment decision: {e}")
    
    async def _promote_winning_variant(self, experiment: Experiment):
        """推廣獲勝變體"""
        try:
            # 找到最佳變體
            winning_variant = self._find_winning_variant(experiment)
            
            if winning_variant and not winning_variant.is_control:
                # 將獲勝變體推廣到生產環境
                await self.version_control.promote_version_stage(
                    provider=winning_variant.provider,
                    model_id=winning_variant.model_id,
                    version=winning_variant.model_version,
                    target_stage=DeploymentStage.PRODUCTION
                )
                
                # 更新模型能力數據庫
                updates = {}
                for metric_name in experiment.primary_metrics:
                    values = winning_variant.metrics.get(metric_name, [])
                    if values:
                        if metric_name == 'capability_score':
                            updates['capability_score'] = statistics.mean(values)
                        elif metric_name == 'latency':
                            updates['avg_latency_ms'] = statistics.mean(values)
                        elif metric_name == 'accuracy':
                            updates['accuracy_score'] = statistics.mean(values)
                
                if updates:
                    await self.model_db.update_model_capability(
                        provider=winning_variant.provider,
                        model_id=winning_variant.model_id,
                        updates=updates
                    )
                
                experiment.status = ExperimentStatus.COMPLETED
                self.experiment_stats['completed_experiments'] += 1
                self.experiment_stats['successful_promotions'] += 1
                
                self.logger.info(f"✅ Promoted winning variant for experiment {experiment.experiment_id}")
        
        except Exception as e:
            self.logger.error(f"❌ Error promoting winning variant: {e}")
            experiment.status = ExperimentStatus.FAILED
    
    def _find_winning_variant(self, experiment: Experiment) -> Optional[ExperimentVariant]:
        """找到獲勝變體"""
        try:
            best_variant = None
            best_score = float('-inf')
            
            for variant in experiment.variants.values():
                if variant.is_control:
                    continue
                
                # 計算變體綜合評分
                score = 0
                metric_count = 0
                
                for metric_name in experiment.primary_metrics:
                    values = variant.metrics.get(metric_name, [])
                    if values:
                        mean_value = statistics.mean(values)
                        
                        # 根據指標類型調整評分
                        if metric_name in ['capability_score', 'accuracy']:
                            score += mean_value
                        elif metric_name == 'latency':
                            score += max(0, 1.0 - (mean_value / 5000.0))  # 延遲歸一化
                        
                        metric_count += 1
                
                if metric_count > 0:
                    avg_score = score / metric_count
                    if avg_score > best_score:
                        best_score = avg_score
                        best_variant = variant
            
            return best_variant
            
        except Exception as e:
            self.logger.error(f"❌ Error finding winning variant: {e}")
            return None
    
    async def _rollback_experiment(self, experiment: Experiment):
        """回滾實驗"""
        try:
            # 將所有測試變體回滾到開發階段
            for variant in experiment.variants.values():
                if not variant.is_control:
                    await self.version_control.promote_version_stage(
                        provider=variant.provider,
                        model_id=variant.model_id,
                        version=variant.model_version,
                        target_stage=DeploymentStage.DEVELOPMENT
                    )
            
            experiment.status = ExperimentStatus.ROLLED_BACK
            self.experiment_stats['rollbacks'] += 1
            
            self.logger.warning(f"⚠️ Rolled back experiment {experiment.experiment_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error rolling back experiment: {e}")
            experiment.status = ExperimentStatus.FAILED
    
    async def _terminate_experiment(self, experiment: Experiment):
        """終止實驗"""
        experiment.status = ExperimentStatus.COMPLETED
        self.experiment_stats['completed_experiments'] += 1
        self.logger.info(f"✅ Terminated experiment {experiment.experiment_id}")
    
    def _generate_experiment_recommendations(
        self,
        experiment: Experiment,
        analysis: Dict[str, Any]
    ) -> List[str]:
        """生成實驗建議"""
        recommendations = []
        
        try:
            sample_sizes = analysis.get('sample_sizes', {})
            min_sample_size = experiment.minimum_sample_size
            
            # 檢查樣本大小
            for variant_id, sample_count in sample_sizes.items():
                if sample_count < min_sample_size:
                    recommendations.append(
                        f"Variant {variant_id} has insufficient sample size ({sample_count} < {min_sample_size}). "
                        "Consider extending experiment duration."
                    )
            
            # 檢查統計顯著性
            metric_comparisons = analysis.get('metric_comparisons', {})
            significant_improvements = 0
            total_comparisons = 0
            
            for metric_name, metric_analysis in metric_comparisons.items():
                for comparison in metric_analysis.get('variant_comparisons', []):
                    total_comparisons += 1
                    
                    stat_test = comparison.get('statistical_test', {})
                    improvement = comparison.get('improvement', {})
                    
                    if stat_test.get('is_significant', False):
                        relative_improvement = improvement.get('relative_improvement_percent', 0)
                        
                        if relative_improvement > 5:
                            significant_improvements += 1
                            recommendations.append(
                                f"Significant improvement detected in {metric_name} "
                                f"({relative_improvement:.1f}% improvement). Consider promoting variant."
                            )
                        elif relative_improvement < -5:
                            recommendations.append(
                                f"Significant degradation detected in {metric_name} "
                                f"({relative_improvement:.1f}% degradation). Consider rolling back."
                            )
            
            # 總體建議
            if significant_improvements == 0 and total_comparisons > 0:
                recommendations.append(
                    "No significant improvements detected. Consider terminating experiment or "
                    "extending duration to collect more data."
                )
            elif significant_improvements >= total_comparisons * 0.5:
                recommendations.append(
                    "Multiple significant improvements detected. Strong candidate for promotion."
                )
            
        except Exception as e:
            self.logger.error(f"❌ Error generating recommendations: {e}")
            recommendations.append("Error generating recommendations. Please review results manually.")
        
        return recommendations
    
    # ==================== 清理和維護 ====================
    
    async def _cleanup_cache(self):
        """清理路由緩存"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_keys = []
            
            for cache_key, expire_time in self.cache_ttl.items():
                if current_time >= expire_time:
                    expired_keys.append(cache_key)
            
            for key in expired_keys:
                if key in self.routing_cache:
                    del self.routing_cache[key]
                if key in self.cache_ttl:
                    del self.cache_ttl[key]
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up cache: {e}")
    
    # ==================== 公共接口 ====================
    
    def get_experiment_status(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """獲取實驗狀態"""
        if experiment_id not in self.experiments:
            return None
        
        experiment = self.experiments[experiment_id]
        
        return {
            'experiment_id': experiment_id,
            'experiment_name': experiment.experiment_name,
            'experiment_type': experiment.experiment_type.value,
            'status': experiment.status.value,
            'created_at': experiment.created_at.isoformat(),
            'start_time': experiment.start_time.isoformat() if experiment.start_time else None,
            'end_time': experiment.end_time.isoformat() if experiment.end_time else None,
            'duration_hours': self._calculate_experiment_duration(experiment),
            'variants': {
                variant_id: {
                    'variant_name': variant.variant_name,
                    'provider': variant.provider,
                    'model_id': variant.model_id,
                    'traffic_percentage': variant.traffic_percentage,
                    'sample_count': variant.sample_count,
                    'is_control': variant.is_control
                }
                for variant_id, variant in experiment.variants.items()
            },
            'decision': experiment.decision.value if experiment.decision else None,
            'decision_reason': experiment.decision_reason
        }
    
    def list_experiments(
        self,
        status: Optional[ExperimentStatus] = None,
        experiment_type: Optional[ExperimentType] = None
    ) -> List[Dict[str, Any]]:
        """列出實驗"""
        experiments = []
        
        for experiment in self.experiments.values():
            # 應用過濾條件
            if status and experiment.status != status:
                continue
            if experiment_type and experiment.experiment_type != experiment_type:
                continue
            
            experiments.append(self.get_experiment_status(experiment.experiment_id))
        
        # 按創建時間排序
        experiments.sort(key=lambda x: x['created_at'], reverse=True)
        
        return experiments
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計"""
        return {
            **self.experiment_stats.copy(),
            'cache_size': len(self.routing_cache),
            'running': self._running
        }