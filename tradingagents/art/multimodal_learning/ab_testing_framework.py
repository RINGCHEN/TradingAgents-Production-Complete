#!/usr/bin/env python3
"""
A/B Testing Framework - A/B測試框架
天工 (TianGong) - 多模態學習系統的實驗和優化平台

此模組提供：
1. 多變體實驗設計和執行
2. 統計顯著性測試
3. 實驗結果分析和可視化
4. 動態流量分配
5. 實驗生命週期管理
"""

from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
import json
import time
import uuid
from collections import defaultdict, deque
import random
from scipy import stats
import hashlib

class ExperimentStatus(Enum):
    """實驗狀態"""
    DRAFT = "draft"                 # 草稿
    SCHEDULED = "scheduled"         # 已排程
    RUNNING = "running"             # 運行中
    PAUSED = "paused"              # 暫停
    COMPLETED = "completed"         # 已完成
    CANCELLED = "cancelled"         # 已取消
    FAILED = "failed"              # 失敗

class TrafficSplitMethod(Enum):
    """流量分配方法"""
    RANDOM = "random"               # 隨機分配
    HASH_BASED = "hash_based"       # 基於雜湊
    WEIGHTED = "weighted"           # 權重分配
    BAYESIAN = "bayesian"           # 貝葉斯優化
    ADAPTIVE = "adaptive"           # 自適應分配

class MetricType(Enum):
    """指標類型"""
    CONVERSION = "conversion"       # 轉換率
    CONTINUOUS = "continuous"       # 連續變數
    COUNT = "count"                # 計數
    RATIO = "ratio"                # 比率
    BINARY = "binary"              # 二元

@dataclass
class ExperimentVariant:
    """實驗變體"""
    variant_id: str
    variant_name: str
    description: str
    config: Dict[str, Any]
    traffic_allocation: float = 0.0  # 流量分配比例
    is_control: bool = False         # 是否為對照組
    
    def __post_init__(self):
        if self.traffic_allocation < 0 or self.traffic_allocation > 1:
            raise ValueError("流量分配比例必須在0-1之間")

@dataclass
class ExperimentMetric:
    """實驗指標"""
    metric_name: str
    metric_type: MetricType
    description: str
    primary: bool = False           # 是否為主要指標
    direction: str = "higher"       # "higher" 或 "lower" 表示期望方向
    min_detectable_effect: float = 0.05  # 最小可檢測效果
    significance_level: float = 0.05      # 顯著性水準

@dataclass
class ExperimentResult:
    """實驗結果"""
    variant_id: str
    metric_name: str
    sample_size: int
    mean_value: float
    std_dev: float
    confidence_interval: Tuple[float, float]
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    is_significant: bool = False

@dataclass
class ABTestExperiment:
    """A/B測試實驗"""
    experiment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experiment_name: str = ""
    description: str = ""
    hypothesis: str = ""
    
    # 實驗配置
    variants: List[ExperimentVariant] = field(default_factory=list)
    metrics: List[ExperimentMetric] = field(default_factory=list)
    
    # 流量配置
    traffic_split_method: TrafficSplitMethod = TrafficSplitMethod.RANDOM
    total_traffic_percentage: float = 1.0
    
    # 時間配置
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_days: int = 14
    
    # 統計配置
    minimum_sample_size: int = 1000
    statistical_power: float = 0.8
    
    # 狀態管理
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 結果數據
    results: List[ExperimentResult] = field(default_factory=list)
    participant_data: Dict[str, Any] = field(default_factory=dict)

class ABTestingFramework:
    """A/B測試框架主控制器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 實驗管理
        self.active_experiments: Dict[str, ABTestExperiment] = {}
        self.experiment_history: List[ABTestExperiment] = []
        
        # 參與者追蹤
        self.participant_assignments: Dict[str, Dict[str, str]] = defaultdict(dict)
        self.participant_metrics: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        
        # 統計配置
        self.default_significance_level = self.config.get('significance_level', 0.05)
        self.default_statistical_power = self.config.get('statistical_power', 0.8)
        self.min_sample_size = self.config.get('min_sample_size', 1000)
        
        # 分析配置
        self.analysis_interval = self.config.get('analysis_interval', 3600)  # 秒
        self.early_stopping_enabled = self.config.get('early_stopping', True)
        
        # 監控任務
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
        # 回調函數
        self.experiment_callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        self.logger.info("ABTestingFramework initialized")
    
    async def create_experiment(
        self,
        experiment_name: str,
        description: str,
        hypothesis: str,
        variants: List[Dict[str, Any]],
        metrics: List[Dict[str, Any]],
        config: Dict[str, Any] = None
    ) -> str:
        """
        創建新的A/B測試實驗
        
        Args:
            experiment_name: 實驗名稱
            description: 實驗描述
            hypothesis: 實驗假設
            variants: 變體配置列表
            metrics: 指標配置列表
            config: 額外配置
            
        Returns:
            實驗ID
        """
        try:
            experiment = ABTestExperiment(
                experiment_name=experiment_name,
                description=description,
                hypothesis=hypothesis
            )
            
            # 配置變體
            for variant_config in variants:
                variant = ExperimentVariant(
                    variant_id=variant_config.get('variant_id', str(uuid.uuid4())),
                    variant_name=variant_config['variant_name'],
                    description=variant_config.get('description', ''),
                    config=variant_config.get('config', {}),
                    traffic_allocation=variant_config.get('traffic_allocation', 0.5),
                    is_control=variant_config.get('is_control', False)
                )
                experiment.variants.append(variant)
            
            # 驗證流量分配
            total_allocation = sum(v.traffic_allocation for v in experiment.variants)
            if abs(total_allocation - 1.0) > 0.01:
                raise ValueError(f"流量分配總和必須等於1.0，當前: {total_allocation}")
            
            # 配置指標
            for metric_config in metrics:
                metric = ExperimentMetric(
                    metric_name=metric_config['metric_name'],
                    metric_type=MetricType(metric_config.get('metric_type', 'continuous')),
                    description=metric_config.get('description', ''),
                    primary=metric_config.get('primary', False),
                    direction=metric_config.get('direction', 'higher'),
                    min_detectable_effect=metric_config.get('min_detectable_effect', 0.05)
                )
                experiment.metrics.append(metric)
            
            # 應用額外配置
            if config:
                for key, value in config.items():
                    if hasattr(experiment, key):
                        setattr(experiment, key, value)
            
            # 計算所需樣本量
            experiment.minimum_sample_size = self._calculate_required_sample_size(experiment)
            
            # 保存實驗
            self.active_experiments[experiment.experiment_id] = experiment
            
            self.logger.info(f"創建實驗成功: {experiment_name} ({experiment.experiment_id})")
            return experiment.experiment_id
            
        except Exception as e:
            self.logger.error(f"創建實驗失敗: {e}")
            raise
    
    def _calculate_required_sample_size(self, experiment: ABTestExperiment) -> int:
        """計算所需樣本量"""
        try:
            # 找到主要指標
            primary_metrics = [m for m in experiment.metrics if m.primary]
            if not primary_metrics:
                return self.min_sample_size
            
            primary_metric = primary_metrics[0]
            
            # 使用Cohen's d計算樣本量
            alpha = primary_metric.significance_level
            beta = 1 - experiment.statistical_power
            effect_size = primary_metric.min_detectable_effect
            
            # 雙尾檢驗的臨界值
            z_alpha = stats.norm.ppf(1 - alpha/2)
            z_beta = stats.norm.ppf(1 - beta)
            
            # 每組所需樣本量
            n_per_group = ((z_alpha + z_beta) / effect_size) ** 2 * 2
            
            # 總樣本量（考慮所有變體）
            total_sample_size = int(n_per_group * len(experiment.variants))
            
            return max(total_sample_size, self.min_sample_size)
            
        except Exception as e:
            self.logger.warning(f"樣本量計算失敗，使用默認值: {e}")
            return self.min_sample_size
    
    async def start_experiment(self, experiment_id: str) -> bool:
        """啟動實驗"""
        try:
            if experiment_id not in self.active_experiments:
                raise ValueError(f"實驗不存在: {experiment_id}")
            
            experiment = self.active_experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.DRAFT:
                raise ValueError(f"只能啟動草稿狀態的實驗，當前狀態: {experiment.status}")
            
            # 驗證實驗配置
            await self._validate_experiment_config(experiment)
            
            # 設置開始時間
            experiment.start_time = datetime.now()
            if experiment.duration_days > 0:
                experiment.end_time = experiment.start_time + timedelta(days=experiment.duration_days)
            
            # 更新狀態
            experiment.status = ExperimentStatus.RUNNING
            experiment.updated_at = datetime.now()
            
            # 啟動監控任務
            await self._start_experiment_monitoring(experiment_id)
            
            # 執行啟動回調
            await self._execute_experiment_callbacks('experiment_started', experiment)
            
            self.logger.info(f"實驗啟動成功: {experiment.experiment_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"實驗啟動失敗: {e}")
            if experiment_id in self.active_experiments:
                self.active_experiments[experiment_id].status = ExperimentStatus.FAILED
            return False
    
    async def _validate_experiment_config(self, experiment: ABTestExperiment):
        """驗證實驗配置"""
        # 檢查變體配置
        if len(experiment.variants) < 2:
            raise ValueError("至少需要2個變體")
        
        # 檢查對照組
        control_variants = [v for v in experiment.variants if v.is_control]
        if len(control_variants) != 1:
            raise ValueError("必須有且僅有一個對照組")
        
        # 檢查指標配置
        if not experiment.metrics:
            raise ValueError("至少需要一個指標")
        
        primary_metrics = [m for m in experiment.metrics if m.primary]
        if len(primary_metrics) != 1:
            raise ValueError("必須有且僅有一個主要指標")
    
    async def assign_participant(
        self,
        participant_id: str,
        experiment_id: str,
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """
        為參與者分配實驗變體
        
        Args:
            participant_id: 參與者ID
            experiment_id: 實驗ID
            context: 上下文信息
            
        Returns:
            分配的變體ID，如果不參與則返回None
        """
        try:
            if experiment_id not in self.active_experiments:
                return None
            
            experiment = self.active_experiments[experiment_id]
            
            if experiment.status != ExperimentStatus.RUNNING:
                return None
            
            # 檢查是否已經分配過
            if experiment_id in self.participant_assignments[participant_id]:
                return self.participant_assignments[participant_id][experiment_id]
            
            # 檢查是否符合實驗條件
            if not self._is_eligible_participant(participant_id, experiment, context):
                return None
            
            # 分配變體
            variant_id = await self._allocate_variant(
                participant_id, experiment, context
            )
            
            if variant_id:
                # 記錄分配
                self.participant_assignments[participant_id][experiment_id] = variant_id
                
                # 初始化參與者指標
                for metric in experiment.metrics:
                    self.participant_metrics[participant_id][f"{experiment_id}_{metric.metric_name}"] = []
                
                self.logger.debug(f"參與者 {participant_id} 分配到變體 {variant_id}")
            
            return variant_id
            
        except Exception as e:
            self.logger.error(f"參與者分配失敗: {e}")
            return None
    
    def _is_eligible_participant(
        self,
        participant_id: str,
        experiment: ABTestExperiment,
        context: Dict[str, Any]
    ) -> bool:
        """檢查參與者是否符合實驗條件"""
        try:
            # 檢查總流量限制
            if experiment.total_traffic_percentage < 1.0:
                # 使用雜湊確定是否包含在流量中
                hash_value = int(hashlib.md5(
                    f"{experiment.experiment_id}_{participant_id}".encode()
                ).hexdigest(), 16)
                
                if (hash_value % 100) / 100 >= experiment.total_traffic_percentage:
                    return False
            
            # 可以在這裡添加其他篩選條件
            # 例如：地理位置、用戶類型、設備類型等
            
            return True
            
        except Exception as e:
            self.logger.warning(f"參與者篩選檢查失敗: {e}")
            return False
    
    async def _allocate_variant(
        self,
        participant_id: str,
        experiment: ABTestExperiment,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """分配變體"""
        try:
            if experiment.traffic_split_method == TrafficSplitMethod.RANDOM:
                return self._random_allocation(experiment)
            
            elif experiment.traffic_split_method == TrafficSplitMethod.HASH_BASED:
                return self._hash_based_allocation(participant_id, experiment)
            
            elif experiment.traffic_split_method == TrafficSplitMethod.WEIGHTED:
                return self._weighted_allocation(experiment)
            
            elif experiment.traffic_split_method == TrafficSplitMethod.BAYESIAN:
                return await self._bayesian_allocation(experiment)
            
            elif experiment.traffic_split_method == TrafficSplitMethod.ADAPTIVE:
                return await self._adaptive_allocation(experiment)
            
            else:
                return self._random_allocation(experiment)
                
        except Exception as e:
            self.logger.error(f"變體分配失敗: {e}")
            return None
    
    def _random_allocation(self, experiment: ABTestExperiment) -> str:
        """隨機分配"""
        rand_val = random.random()
        cumulative_prob = 0.0
        
        for variant in experiment.variants:
            cumulative_prob += variant.traffic_allocation
            if rand_val <= cumulative_prob:
                return variant.variant_id
        
        # 備選：返回最後一個變體
        return experiment.variants[-1].variant_id
    
    def _hash_based_allocation(self, participant_id: str, experiment: ABTestExperiment) -> str:
        """基於雜湊的分配（確保同一用戶總是得到相同變體）"""
        hash_value = int(hashlib.md5(
            f"{experiment.experiment_id}_{participant_id}".encode()
        ).hexdigest(), 16)
        
        rand_val = (hash_value % 10000) / 10000.0
        cumulative_prob = 0.0
        
        for variant in experiment.variants:
            cumulative_prob += variant.traffic_allocation
            if rand_val <= cumulative_prob:
                return variant.variant_id
        
        return experiment.variants[-1].variant_id
    
    def _weighted_allocation(self, experiment: ABTestExperiment) -> str:
        """權重分配"""
        weights = [variant.traffic_allocation for variant in experiment.variants]
        variant = random.choices(experiment.variants, weights=weights)[0]
        return variant.variant_id
    
    async def _bayesian_allocation(self, experiment: ABTestExperiment) -> str:
        """貝葉斯優化分配（偏向表現較好的變體）"""
        try:
            # 如果還沒有足夠的數據，使用隨機分配
            if not self._has_sufficient_data(experiment):
                return self._random_allocation(experiment)
            
            # 計算每個變體的貝葉斯置信區間
            variant_scores = {}
            for variant in experiment.variants:
                score = await self._calculate_bayesian_score(experiment, variant.variant_id)
                variant_scores[variant.variant_id] = score
            
            # 使用Thompson採樣
            best_variant_id = max(variant_scores.keys(), key=lambda x: variant_scores[x])
            
            # 仍然保留一定的隨機性
            if random.random() < 0.8:  # 80%機會選擇最佳變體
                return best_variant_id
            else:
                return self._random_allocation(experiment)
                
        except Exception as e:
            self.logger.warning(f"貝葉斯分配失敗，使用隨機分配: {e}")
            return self._random_allocation(experiment)
    
    async def _adaptive_allocation(self, experiment: ABTestExperiment) -> str:
        """自適應分配（根據實時表現調整流量）"""
        try:
            # 如果實驗剛開始，使用均等分配收集初始數據
            if not self._has_sufficient_data(experiment):
                return self._random_allocation(experiment)
            
            # 計算各變體的表現
            variant_performances = {}
            for variant in experiment.variants:
                performance = await self._calculate_variant_performance(
                    experiment, variant.variant_id
                )
                variant_performances[variant.variant_id] = performance
            
            # 根據表現調整流量分配
            adjusted_weights = self._calculate_adaptive_weights(
                experiment, variant_performances
            )
            
            # 使用調整後的權重進行分配
            rand_val = random.random()
            cumulative_prob = 0.0
            
            for variant in experiment.variants:
                weight = adjusted_weights.get(variant.variant_id, variant.traffic_allocation)
                cumulative_prob += weight
                if rand_val <= cumulative_prob:
                    return variant.variant_id
            
            return experiment.variants[-1].variant_id
            
        except Exception as e:
            self.logger.warning(f"自適應分配失敗，使用隨機分配: {e}")
            return self._random_allocation(experiment)
    
    def _has_sufficient_data(self, experiment: ABTestExperiment) -> bool:
        """檢查是否有足夠的數據進行高級分配"""
        min_samples_per_variant = 100
        
        for variant in experiment.variants:
            variant_participants = [
                pid for pid, assignments in self.participant_assignments.items()
                if assignments.get(experiment.experiment_id) == variant.variant_id
            ]
            
            if len(variant_participants) < min_samples_per_variant:
                return False
        
        return True
    
    async def _calculate_bayesian_score(self, experiment: ABTestExperiment, variant_id: str) -> float:
        """計算貝葉斯分數"""
        try:
            primary_metric = next(m for m in experiment.metrics if m.primary)
            
            # 收集該變體的指標數據
            variant_data = []
            for participant_id, assignments in self.participant_assignments.items():
                if assignments.get(experiment.experiment_id) == variant_id:
                    metric_key = f"{experiment.experiment_id}_{primary_metric.metric_name}"
                    if metric_key in self.participant_metrics[participant_id]:
                        variant_data.extend(self.participant_metrics[participant_id][metric_key])
            
            if not variant_data:
                return 0.5  # 無數據時返回中性分數
            
            # 簡單的貝葉斯分數計算
            mean_value = np.mean(variant_data)
            std_value = np.std(variant_data) if len(variant_data) > 1 else 1.0
            confidence = min(len(variant_data) / 100.0, 1.0)  # 樣本量信心度
            
            # 標準化分數
            normalized_score = (mean_value - np.mean([np.mean(variant_data)])) / (std_value + 1e-8)
            
            return 0.5 + normalized_score * 0.3 * confidence
            
        except Exception as e:
            self.logger.warning(f"貝葉斯分數計算失敗: {e}")
            return 0.5
    
    async def _calculate_variant_performance(self, experiment: ABTestExperiment, variant_id: str) -> float:
        """計算變體性能"""
        try:
            primary_metric = next(m for m in experiment.metrics if m.primary)
            
            # 收集該變體的數據
            variant_data = []
            for participant_id, assignments in self.participant_assignments.items():
                if assignments.get(experiment.experiment_id) == variant_id:
                    metric_key = f"{experiment.experiment_id}_{primary_metric.metric_name}"
                    if metric_key in self.participant_metrics[participant_id]:
                        variant_data.extend(self.participant_metrics[participant_id][metric_key])
            
            if not variant_data:
                return 0.0
            
            return np.mean(variant_data)
            
        except Exception as e:
            self.logger.warning(f"變體性能計算失敗: {e}")
            return 0.0
    
    def _calculate_adaptive_weights(
        self,
        experiment: ABTestExperiment,
        performances: Dict[str, float]
    ) -> Dict[str, float]:
        """計算自適應權重"""
        if not performances:
            return {v.variant_id: v.traffic_allocation for v in experiment.variants}
        
        # 使用softmax函數計算新權重
        performance_values = list(performances.values())
        if len(set(performance_values)) == 1:  # 所有性能相同
            return {v.variant_id: 1.0/len(experiment.variants) for v in experiment.variants}
        
        # 溫度參數控制探索vs利用的平衡
        temperature = 2.0
        exp_values = {
            variant_id: np.exp(performance / temperature)
            for variant_id, performance in performances.items()
        }
        
        total_exp = sum(exp_values.values())
        adaptive_weights = {
            variant_id: exp_val / total_exp
            for variant_id, exp_val in exp_values.items()
        }
        
        return adaptive_weights
    
    async def record_metric(
        self,
        participant_id: str,
        experiment_id: str,
        metric_name: str,
        value: Union[float, int, bool]
    ) -> bool:
        """
        記錄參與者指標數據
        
        Args:
            participant_id: 參與者ID
            experiment_id: 實驗ID
            metric_name: 指標名稱
            value: 指標值
            
        Returns:
            是否記錄成功
        """
        try:
            # 檢查實驗是否存在且正在運行
            if experiment_id not in self.active_experiments:
                return False
            
            experiment = self.active_experiments[experiment_id]
            if experiment.status != ExperimentStatus.RUNNING:
                return False
            
            # 檢查參與者是否被分配到該實驗
            if experiment_id not in self.participant_assignments[participant_id]:
                return False
            
            # 檢查指標是否在實驗中定義
            metric_names = [m.metric_name for m in experiment.metrics]
            if metric_name not in metric_names:
                return False
            
            # 記錄指標值
            metric_key = f"{experiment_id}_{metric_name}"
            self.participant_metrics[participant_id][metric_key].append(float(value))
            
            self.logger.debug(f"記錄指標: {participant_id}, {metric_name}, {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"指標記錄失敗: {e}")
            return False
    
    async def _start_experiment_monitoring(self, experiment_id: str):
        """啟動實驗監控"""
        if experiment_id in self.monitoring_tasks:
            return
        
        async def monitoring_loop():
            while experiment_id in self.active_experiments:
                try:
                    experiment = self.active_experiments[experiment_id]
                    
                    if experiment.status != ExperimentStatus.RUNNING:
                        break
                    
                    # 檢查實驗是否到期
                    if experiment.end_time and datetime.now() >= experiment.end_time:
                        await self.stop_experiment(experiment_id, "實驗時間到期")
                        break
                    
                    # 執行定期分析
                    await self._perform_interim_analysis(experiment_id)
                    
                    # 檢查提前停止條件
                    if self.early_stopping_enabled:
                        should_stop, reason = await self._check_early_stopping(experiment_id)
                        if should_stop:
                            await self.stop_experiment(experiment_id, f"提前停止: {reason}")
                            break
                    
                    await asyncio.sleep(self.analysis_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"實驗監控錯誤: {e}")
                    await asyncio.sleep(self.analysis_interval)
        
        task = asyncio.create_task(monitoring_loop())
        self.monitoring_tasks[experiment_id] = task
    
    async def _perform_interim_analysis(self, experiment_id: str):
        """執行中期分析"""
        try:
            experiment = self.active_experiments[experiment_id]
            
            # 計算當前結果
            results = await self.analyze_experiment_results(experiment_id)
            
            # 更新實驗結果
            experiment.results = results
            experiment.updated_at = datetime.now()
            
            # 執行分析回調
            await self._execute_experiment_callbacks('interim_analysis', experiment)
            
        except Exception as e:
            self.logger.error(f"中期分析失敗: {e}")
    
    async def _check_early_stopping(self, experiment_id: str) -> Tuple[bool, str]:
        """檢查提前停止條件"""
        try:
            experiment = self.active_experiments[experiment_id]
            
            # 檢查最小樣本量
            total_participants = len([
                pid for pid, assignments in self.participant_assignments.items()
                if experiment_id in assignments
            ])
            
            if total_participants < experiment.minimum_sample_size:
                return False, ""
            
            # 檢查統計顯著性
            primary_results = [r for r in experiment.results if any(m.primary and m.metric_name == r.metric_name for m in experiment.metrics)]
            
            if not primary_results:
                return False, ""
            
            # 檢查是否達到顯著性且效果大於最小可檢測效果
            for result in primary_results:
                if result.is_significant and result.effect_size:
                    primary_metric = next(m for m in experiment.metrics if m.metric_name == result.metric_name and m.primary)
                    if abs(result.effect_size) >= primary_metric.min_detectable_effect:
                        return True, f"達到統計顯著性和最小效果 ({result.metric_name})"
            
            return False, ""
            
        except Exception as e:
            self.logger.error(f"提前停止檢查失敗: {e}")
            return False, ""
    
    async def stop_experiment(self, experiment_id: str, reason: str = "手動停止") -> bool:
        """停止實驗"""
        try:
            if experiment_id not in self.active_experiments:
                return False
            
            experiment = self.active_experiments[experiment_id]
            
            # 執行最終分析
            final_results = await self.analyze_experiment_results(experiment_id)
            experiment.results = final_results
            
            # 更新狀態
            experiment.status = ExperimentStatus.COMPLETED
            experiment.end_time = datetime.now()
            experiment.updated_at = datetime.now()
            
            # 停止監控任務
            if experiment_id in self.monitoring_tasks:
                self.monitoring_tasks[experiment_id].cancel()
                del self.monitoring_tasks[experiment_id]
            
            # 移動到歷史記錄
            self.experiment_history.append(experiment)
            del self.active_experiments[experiment_id]
            
            # 執行停止回調
            await self._execute_experiment_callbacks('experiment_stopped', experiment)
            
            self.logger.info(f"實驗停止: {experiment.experiment_name} - {reason}")
            return True
            
        except Exception as e:
            self.logger.error(f"實驗停止失敗: {e}")
            return False
    
    async def analyze_experiment_results(self, experiment_id: str) -> List[ExperimentResult]:
        """分析實驗結果"""
        results = []
        
        try:
            if experiment_id not in self.active_experiments:
                experiment = next((e for e in self.experiment_history if e.experiment_id == experiment_id), None)
                if not experiment:
                    return results
            else:
                experiment = self.active_experiments[experiment_id]
            
            # 找到對照組
            control_variant = next(v for v in experiment.variants if v.is_control)
            
            for metric in experiment.metrics:
                # 收集每個變體的數據
                variant_data = {}
                
                for variant in experiment.variants:
                    data = []
                    for participant_id, assignments in self.participant_assignments.items():
                        if assignments.get(experiment_id) == variant.variant_id:
                            metric_key = f"{experiment_id}_{metric.metric_name}"
                            if metric_key in self.participant_metrics[participant_id]:
                                data.extend(self.participant_metrics[participant_id][metric_key])
                    
                    variant_data[variant.variant_id] = data
                
                # 對每個變體進行統計分析
                control_data = variant_data[control_variant.variant_id]
                
                for variant in experiment.variants:
                    if variant.is_control:
                        continue
                    
                    treatment_data = variant_data[variant.variant_id]
                    
                    if len(control_data) == 0 or len(treatment_data) == 0:
                        continue
                    
                    # 執行統計測試
                    result = await self._perform_statistical_test(
                        control_data, treatment_data, metric, variant.variant_id
                    )
                    
                    results.append(result)
            
        except Exception as e:
            self.logger.error(f"實驗結果分析失敗: {e}")
        
        return results
    
    async def _perform_statistical_test(
        self,
        control_data: List[float],
        treatment_data: List[float],
        metric: ExperimentMetric,
        variant_id: str
    ) -> ExperimentResult:
        """執行統計測試"""
        try:
            if metric.metric_type in [MetricType.CONTINUOUS, MetricType.COUNT]:
                # 使用t檢驗
                statistic, p_value = stats.ttest_ind(treatment_data, control_data)
                
                # 計算效果大小 (Cohen's d)
                pooled_std = np.sqrt(((len(treatment_data) - 1) * np.var(treatment_data, ddof=1) +
                                    (len(control_data) - 1) * np.var(control_data, ddof=1)) /
                                   (len(treatment_data) + len(control_data) - 2))
                
                effect_size = (np.mean(treatment_data) - np.mean(control_data)) / pooled_std if pooled_std > 0 else 0.0
                
            elif metric.metric_type == MetricType.BINARY:
                # 使用卡方檢驗或Fisher確切檢驗
                # 這裡簡化處理，將二元數據當作連續數據
                statistic, p_value = stats.ttest_ind(treatment_data, control_data)
                effect_size = np.mean(treatment_data) - np.mean(control_data)
                
            else:
                # 默認使用Mann-Whitney U檢驗（非參數）
                statistic, p_value = stats.mannwhitneyu(treatment_data, control_data, alternative='two-sided')
                effect_size = (np.mean(treatment_data) - np.mean(control_data)) / np.std(control_data + treatment_data)
            
            # 計算信賴區間
            treatment_mean = np.mean(treatment_data)
            treatment_std = np.std(treatment_data, ddof=1)
            n = len(treatment_data)
            
            margin_of_error = stats.t.ppf(0.975, n-1) * (treatment_std / np.sqrt(n))
            confidence_interval = (treatment_mean - margin_of_error, treatment_mean + margin_of_error)
            
            # 判斷統計顯著性
            is_significant = p_value < metric.significance_level
            
            return ExperimentResult(
                variant_id=variant_id,
                metric_name=metric.metric_name,
                sample_size=len(treatment_data),
                mean_value=treatment_mean,
                std_dev=treatment_std,
                confidence_interval=confidence_interval,
                p_value=p_value,
                effect_size=effect_size,
                is_significant=is_significant
            )
            
        except Exception as e:
            self.logger.error(f"統計測試失敗: {e}")
            return ExperimentResult(
                variant_id=variant_id,
                metric_name=metric.metric_name,
                sample_size=len(treatment_data),
                mean_value=np.mean(treatment_data) if treatment_data else 0.0,
                std_dev=np.std(treatment_data) if treatment_data else 0.0,
                confidence_interval=(0.0, 0.0)
            )
    
    async def _execute_experiment_callbacks(self, event: str, experiment: ABTestExperiment):
        """執行實驗回調"""
        callbacks = self.experiment_callbacks.get(event, [])
        for callback in callbacks:
            try:
                await callback(experiment)
            except Exception as e:
                self.logger.warning(f"回調執行失敗 ({event}): {e}")
    
    def add_experiment_callback(self, event: str, callback: Callable):
        """添加實驗回調"""
        self.experiment_callbacks[event].append(callback)
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """獲取實驗摘要"""
        try:
            # 先在活動實驗中查找
            experiment = self.active_experiments.get(experiment_id)
            
            # 如果沒找到，在歷史中查找
            if not experiment:
                experiment = next((e for e in self.experiment_history if e.experiment_id == experiment_id), None)
            
            if not experiment:
                return None
            
            # 統計參與者數量
            participant_counts = defaultdict(int)
            for assignments in self.participant_assignments.values():
                if experiment_id in assignments:
                    variant_id = assignments[experiment_id]
                    participant_counts[variant_id] += 1
            
            # 統計結果摘要
            results_summary = {}
            for result in experiment.results:
                if result.metric_name not in results_summary:
                    results_summary[result.metric_name] = {}
                
                results_summary[result.metric_name][result.variant_id] = {
                    'mean_value': result.mean_value,
                    'sample_size': result.sample_size,
                    'p_value': result.p_value,
                    'effect_size': result.effect_size,
                    'is_significant': result.is_significant
                }
            
            return {
                'experiment_id': experiment.experiment_id,
                'experiment_name': experiment.experiment_name,
                'status': experiment.status.value,
                'start_time': experiment.start_time.isoformat() if experiment.start_time else None,
                'end_time': experiment.end_time.isoformat() if experiment.end_time else None,
                'variants': [
                    {
                        'variant_id': v.variant_id,
                        'variant_name': v.variant_name,
                        'traffic_allocation': v.traffic_allocation,
                        'participant_count': participant_counts[v.variant_id],
                        'is_control': v.is_control
                    }
                    for v in experiment.variants
                ],
                'metrics': [
                    {
                        'metric_name': m.metric_name,
                        'metric_type': m.metric_type.value,
                        'primary': m.primary,
                        'direction': m.direction
                    }
                    for m in experiment.metrics
                ],
                'results_summary': results_summary,
                'total_participants': sum(participant_counts.values())
            }
            
        except Exception as e:
            self.logger.error(f"實驗摘要獲取失敗: {e}")
            return None
    
    def get_framework_statistics(self) -> Dict[str, Any]:
        """獲取框架統計信息"""
        return {
            'active_experiments': len(self.active_experiments),
            'completed_experiments': len(self.experiment_history),
            'total_participants': len(self.participant_assignments),
            'monitoring_tasks': len(self.monitoring_tasks),
            'framework_status': 'running' if self.is_running else 'stopped'
        }