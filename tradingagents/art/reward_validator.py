#!/usr/bin/env python3
"""
RewardValidator - 獎勵驗證器
天工 (TianGong) - 獎勵信號驗證與優化系統

此模組提供：
1. 實時獎勵信號驗證
2. 獎勵函數自動調優機制
3. A/B測試框架支援
4. 歷史績效追蹤和分析
5. 獎勵模型品質評估
6. 異常檢測和修正機制
"""

from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import asyncio
import numpy as np
import pandas as pd
from pathlib import Path
import hashlib
import math
import statistics
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import warnings
import random

# Import reward system components
try:
    from .ruler_reward_system import RewardSignal, RewardMetrics, RewardType, MembershipTier
    REWARD_SYSTEM_AVAILABLE = True
except ImportError:
    REWARD_SYSTEM_AVAILABLE = False

class ValidationType(Enum):
    """驗證類型"""
    RANGE_CHECK = "range_check"                 # 範圍檢查
    CONSISTENCY_CHECK = "consistency_check"     # 一致性檢查
    OUTLIER_DETECTION = "outlier_detection"     # 異常值檢測
    CORRELATION_ANALYSIS = "correlation_analysis" # 相關性分析
    TEMPORAL_VALIDATION = "temporal_validation"  # 時間序列驗證
    CROSS_VALIDATION = "cross_validation"       # 交叉驗證
    PERFORMANCE_VALIDATION = "performance_validation" # 績效驗證
    BIAS_DETECTION = "bias_detection"           # 偏差檢測

class ValidationStatus(Enum):
    """驗證狀態"""
    PENDING = "pending"       # 等待驗證
    PASSED = "passed"         # 驗證通過
    FAILED = "failed"         # 驗證失敗
    WARNING = "warning"       # 警告
    NEEDS_REVIEW = "needs_review" # 需要審查

class OptimizationStrategy(Enum):
    """優化策略"""
    GRADIENT_BASED = "gradient_based"           # 基於梯度的優化
    EVOLUTIONARY = "evolutionary"               # 演化算法
    BAYESIAN = "bayesian"                       # 貝葉斯優化
    REINFORCEMENT_LEARNING = "reinforcement_learning" # 強化學習
    A_B_TESTING = "a_b_testing"                # A/B測試
    ENSEMBLE = "ensemble"                       # 集成方法

@dataclass
class ValidationRule:
    """驗證規則"""
    rule_id: str
    validation_type: ValidationType
    rule_description: str
    
    # 規則參數
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    threshold: Optional[float] = None
    tolerance: Optional[float] = None
    
    # 嚴重性和權重
    severity: str = "medium"  # low, medium, high, critical
    weight: float = 1.0
    
    # 適用條件
    applicable_reward_types: List[RewardType] = field(default_factory=list)
    applicable_membership_tiers: List[MembershipTier] = field(default_factory=list)
    
    # 自動修正
    auto_correction_enabled: bool = False
    correction_function: Optional[str] = None
    
    def is_applicable(self, reward_signal: 'RewardSignal') -> bool:
        """檢查規則是否適用於給定的獎勵信號"""
        # 檢查獎勵類型
        if self.applicable_reward_types:
            signal_reward_types = set(reward_signal.reward_components.keys())
            rule_reward_types = set(self.applicable_reward_types)
            if not signal_reward_types.intersection(rule_reward_types):
                return False
        
        # 檢查會員等級
        if self.applicable_membership_tiers:
            if reward_signal.membership_tier not in self.applicable_membership_tiers:
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['validation_type'] = self.validation_type.value
        result['applicable_reward_types'] = [rt.value for rt in self.applicable_reward_types]
        result['applicable_membership_tiers'] = [mt.value for mt in self.applicable_membership_tiers]
        return result

@dataclass
class ValidationResult:
    """驗證結果"""
    result_id: str
    signal_id: str
    rule_id: str
    validation_type: ValidationType
    
    # 驗證狀態
    status: ValidationStatus = ValidationStatus.PENDING
    confidence: float = 0.0
    
    # 結果詳情
    original_value: Any = None
    expected_value: Any = None
    corrected_value: Any = None
    deviation: float = 0.0
    
    # 詳細信息
    validation_details: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    recommendation: Optional[str] = None
    
    # 時間信息
    validation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['validation_type'] = self.validation_type.value
        result['status'] = self.status.value
        return result

@dataclass
class ValidationMetrics:
    """驗證指標"""
    validator_id: str
    
    # 基本統計
    total_validations: int = 0
    passed_validations: int = 0
    failed_validations: int = 0
    warning_validations: int = 0
    
    # 準確率指標
    validation_accuracy: float = 0.0
    false_positive_rate: float = 0.0
    false_negative_rate: float = 0.0
    
    # 效率指標
    avg_validation_time_ms: float = 0.0
    validation_throughput: float = 0.0
    
    # 質量指標
    avg_confidence: float = 0.0
    consistency_score: float = 0.0
    
    # 更新時間
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def calculate_pass_rate(self) -> float:
        """計算通過率"""
        if self.total_validations == 0:
            return 0.0
        return self.passed_validations / self.total_validations
    
    def calculate_quality_score(self) -> float:
        """計算質量分數"""
        accuracy_weight = 0.4
        consistency_weight = 0.3
        confidence_weight = 0.3
        
        return (
            self.validation_accuracy * accuracy_weight +
            self.consistency_score * consistency_weight +
            self.avg_confidence * confidence_weight
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['pass_rate'] = self.calculate_pass_rate()
        result['quality_score'] = self.calculate_quality_score()
        return result

@dataclass
class RewardModelConfig:
    """獎勵模型配置"""
    config_id: str
    model_version: str
    
    # 權重配置
    reward_weights: Dict[str, float] = field(default_factory=dict)
    membership_multipliers: Dict[str, float] = field(default_factory=dict)
    
    # 驗證配置
    validation_rules: List[ValidationRule] = field(default_factory=list)
    
    # 優化配置
    optimization_strategy: OptimizationStrategy = OptimizationStrategy.A_B_TESTING
    optimization_target: str = "total_reward_quality"
    
    # A/B測試配置
    ab_test_enabled: bool = False
    ab_test_split_ratio: float = 0.5
    ab_test_duration_days: int = 30
    
    # 性能基準
    performance_baseline: Dict[str, float] = field(default_factory=dict)
    
    # 元數據
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    created_by: str = "system"
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['optimization_strategy'] = self.optimization_strategy.value
        result['validation_rules'] = [rule.to_dict() for rule in self.validation_rules]
        return result

class ValidationEngine(ABC):
    """驗證引擎基類"""
    
    @abstractmethod
    async def validate(self, 
                      reward_signal: 'RewardSignal',
                      validation_rule: ValidationRule,
                      historical_data: List['RewardSignal'] = None) -> ValidationResult:
        """執行驗證"""
        pass
    
    @abstractmethod
    def get_validation_type(self) -> ValidationType:
        """獲取驗證類型"""
        pass

class RangeCheckEngine(ValidationEngine):
    """範圍檢查引擎"""
    
    async def validate(self, 
                      reward_signal: 'RewardSignal',
                      validation_rule: ValidationRule,
                      historical_data: List['RewardSignal'] = None) -> ValidationResult:
        """執行範圍檢查"""
        
        result_id = f"range_check_{reward_signal.signal_id}_{validation_rule.rule_id}"
        
        # 獲取要檢查的值
        value_to_check = reward_signal.weighted_total_reward
        
        # 執行範圍檢查
        is_valid = True
        deviation = 0.0
        error_message = None
        
        if validation_rule.min_value is not None and value_to_check < validation_rule.min_value:
            is_valid = False
            deviation = abs(value_to_check - validation_rule.min_value)
            error_message = f"Value {value_to_check:.3f} is below minimum {validation_rule.min_value:.3f}"
        
        if validation_rule.max_value is not None and value_to_check > validation_rule.max_value:
            is_valid = False
            deviation = abs(value_to_check - validation_rule.max_value)
            error_message = f"Value {value_to_check:.3f} is above maximum {validation_rule.max_value:.3f}"
        
        # 確定狀態
        if is_valid:
            status = ValidationStatus.PASSED
            confidence = 0.9
        else:
            # 根據偏差程度決定狀態
            if deviation > (validation_rule.tolerance or 0.1):
                status = ValidationStatus.FAILED
                confidence = 0.8
            else:
                status = ValidationStatus.WARNING
                confidence = 0.6
        
        return ValidationResult(
            result_id=result_id,
            signal_id=reward_signal.signal_id,
            rule_id=validation_rule.rule_id,
            validation_type=self.get_validation_type(),
            status=status,
            confidence=confidence,
            original_value=value_to_check,
            expected_value=(validation_rule.min_value, validation_rule.max_value),
            deviation=deviation,
            error_message=error_message,
            validation_details={
                'checked_field': 'weighted_total_reward',
                'min_threshold': validation_rule.min_value,
                'max_threshold': validation_rule.max_value,
                'tolerance': validation_rule.tolerance
            }
        )
    
    def get_validation_type(self) -> ValidationType:
        return ValidationType.RANGE_CHECK

class OutlierDetectionEngine(ValidationEngine):
    """異常值檢測引擎"""
    
    async def validate(self, 
                      reward_signal: 'RewardSignal',
                      validation_rule: ValidationRule,
                      historical_data: List['RewardSignal'] = None) -> ValidationResult:
        """執行異常值檢測"""
        
        result_id = f"outlier_detection_{reward_signal.signal_id}_{validation_rule.rule_id}"
        
        if not historical_data or len(historical_data) < 10:
            return ValidationResult(
                result_id=result_id,
                signal_id=reward_signal.signal_id,
                rule_id=validation_rule.rule_id,
                validation_type=self.get_validation_type(),
                status=ValidationStatus.WARNING,
                confidence=0.3,
                error_message="Insufficient historical data for outlier detection"
            )
        
        # 提取歷史獎勵值
        historical_rewards = [signal.weighted_total_reward for signal in historical_data]
        current_reward = reward_signal.weighted_total_reward
        
        # 計算統計指標
        mean_reward = statistics.mean(historical_rewards)
        std_dev = statistics.stdev(historical_rewards) if len(historical_rewards) > 1 else 0.1
        
        # Z-score檢測
        z_score = abs(current_reward - mean_reward) / std_dev if std_dev > 0 else 0
        outlier_threshold = validation_rule.threshold or 2.5
        
        # IQR檢測
        q1 = np.percentile(historical_rewards, 25)
        q3 = np.percentile(historical_rewards, 75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        is_iqr_outlier = current_reward < lower_bound or current_reward > upper_bound
        is_zscore_outlier = z_score > outlier_threshold
        
        # 綜合判定
        if is_zscore_outlier and is_iqr_outlier:
            status = ValidationStatus.FAILED
            confidence = 0.9
            error_message = f"Strong outlier detected (Z-score: {z_score:.2f}, IQR outlier: {is_iqr_outlier})"
        elif is_zscore_outlier or is_iqr_outlier:
            status = ValidationStatus.WARNING
            confidence = 0.7
            error_message = f"Potential outlier detected (Z-score: {z_score:.2f})"
        else:
            status = ValidationStatus.PASSED
            confidence = 0.8
            error_message = None
        
        return ValidationResult(
            result_id=result_id,
            signal_id=reward_signal.signal_id,
            rule_id=validation_rule.rule_id,
            validation_type=self.get_validation_type(),
            status=status,
            confidence=confidence,
            original_value=current_reward,
            expected_value=(lower_bound, upper_bound),
            deviation=z_score,
            error_message=error_message,
            validation_details={
                'z_score': z_score,
                'historical_mean': mean_reward,
                'historical_std': std_dev,
                'iqr_bounds': (lower_bound, upper_bound),
                'outlier_threshold': outlier_threshold,
                'sample_size': len(historical_rewards)
            }
        )
    
    def get_validation_type(self) -> ValidationType:
        return ValidationType.OUTLIER_DETECTION

class ConsistencyCheckEngine(ValidationEngine):
    """一致性檢查引擎"""
    
    async def validate(self, 
                      reward_signal: 'RewardSignal',
                      validation_rule: ValidationRule,
                      historical_data: List['RewardSignal'] = None) -> ValidationResult:
        """執行一致性檢查"""
        
        result_id = f"consistency_check_{reward_signal.signal_id}_{validation_rule.rule_id}"
        
        if not historical_data:
            return ValidationResult(
                result_id=result_id,
                signal_id=reward_signal.signal_id,
                rule_id=validation_rule.rule_id,
                validation_type=self.get_validation_type(),
                status=ValidationStatus.WARNING,
                confidence=0.5,
                error_message="No historical data available for consistency check"
            )
        
        # 檢查同類型獎勵的一致性
        consistency_scores = []
        
        for reward_type in reward_signal.reward_components.keys():
            current_metrics = reward_signal.reward_components[reward_type]
            
            # 收集歷史同類型獎勵
            historical_values = []
            for historical_signal in historical_data:
                if reward_type in historical_signal.reward_components:
                    historical_values.append(
                        historical_signal.reward_components[reward_type].final_reward
                    )
            
            if len(historical_values) >= 3:
                # 計算一致性分數
                historical_mean = statistics.mean(historical_values)
                historical_std = statistics.stdev(historical_values)
                current_value = current_metrics.final_reward
                
                if historical_std > 0:
                    consistency_score = max(0, 1 - abs(current_value - historical_mean) / historical_std)
                else:
                    consistency_score = 1.0 if abs(current_value - historical_mean) < 0.01 else 0.0
                
                consistency_scores.append(consistency_score)
        
        if not consistency_scores:
            return ValidationResult(
                result_id=result_id,
                signal_id=reward_signal.signal_id,
                rule_id=validation_rule.rule_id,
                validation_type=self.get_validation_type(),
                status=ValidationStatus.WARNING,
                confidence=0.3,
                error_message="Insufficient data for consistency analysis"
            )
        
        # 綜合一致性評分
        avg_consistency = statistics.mean(consistency_scores)
        consistency_threshold = validation_rule.threshold or 0.7
        
        if avg_consistency >= consistency_threshold:
            status = ValidationStatus.PASSED
            confidence = 0.8
            error_message = None
        elif avg_consistency >= consistency_threshold * 0.7:
            status = ValidationStatus.WARNING
            confidence = 0.6
            error_message = f"Moderate consistency concern (score: {avg_consistency:.2f})"
        else:
            status = ValidationStatus.FAILED
            confidence = 0.9
            error_message = f"Low consistency detected (score: {avg_consistency:.2f})"
        
        return ValidationResult(
            result_id=result_id,
            signal_id=reward_signal.signal_id,
            rule_id=validation_rule.rule_id,
            validation_type=self.get_validation_type(),
            status=status,
            confidence=confidence,
            original_value=avg_consistency,
            expected_value=consistency_threshold,
            deviation=abs(avg_consistency - consistency_threshold),
            error_message=error_message,
            validation_details={
                'consistency_scores': consistency_scores,
                'average_consistency': avg_consistency,
                'threshold': consistency_threshold,
                'analyzed_reward_types': len(consistency_scores)
            }
        )
    
    def get_validation_type(self) -> ValidationType:
        return ValidationType.CONSISTENCY_CHECK

class RewardValidator:
    """獎勵驗證器 - 主要控制器"""
    
    def __init__(self, 
                 storage_path: str = None,
                 model_config: RewardModelConfig = None,
                 enable_auto_correction: bool = True,
                 enable_ab_testing: bool = True):
        
        # 存儲配置
        self.storage_path = Path(storage_path) if storage_path else Path("./art_data/validation")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 模型配置
        self.model_config = model_config or self._create_default_config()
        
        # 驗證引擎
        self.validation_engines: Dict[ValidationType, ValidationEngine] = {
            ValidationType.RANGE_CHECK: RangeCheckEngine(),
            ValidationType.OUTLIER_DETECTION: OutlierDetectionEngine(),
            ValidationType.CONSISTENCY_CHECK: ConsistencyCheckEngine()
        }
        
        # 驗證歷史
        self.validation_history: Dict[str, List[ValidationResult]] = defaultdict(list)
        
        # A/B測試
        self.enable_ab_testing = enable_ab_testing
        self.ab_test_groups: Dict[str, str] = {}  # signal_id -> group_name
        self.ab_test_results: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # 自動修正
        self.enable_auto_correction = enable_auto_correction
        self.correction_functions: Dict[str, Callable] = {}
        
        # 性能追蹤
        self.validation_metrics = ValidationMetrics(validator_id="main_validator")
        
        # 日誌記錄
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 線程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="Reward-Validator")
        
        # 統計信息
        self.validation_stats = defaultdict(int)
        self._stats_lock = threading.Lock()
        
        self.logger.info(f"RewardValidator initialized with {len(self.validation_engines)} engines")
    
    def _setup_logging(self):
        """設置日誌記錄"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - RewardValidator - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _create_default_config(self) -> RewardModelConfig:
        """創建默認配置"""
        
        # 創建默認驗證規則
        validation_rules = [
            # 範圍檢查規則
            ValidationRule(
                rule_id="reward_range_check",
                validation_type=ValidationType.RANGE_CHECK,
                rule_description="Check if reward is within acceptable range",
                min_value=-1.0,
                max_value=1.0,
                tolerance=0.05,
                severity="high",
                weight=0.9,
                auto_correction_enabled=True
            ),
            
            # 異常值檢測規則
            ValidationRule(
                rule_id="outlier_detection",
                validation_type=ValidationType.OUTLIER_DETECTION,
                rule_description="Detect reward outliers using statistical methods",
                threshold=2.5,
                tolerance=0.5,
                severity="medium",
                weight=0.7
            ),
            
            # 一致性檢查規則
            ValidationRule(
                rule_id="consistency_check",
                validation_type=ValidationType.CONSISTENCY_CHECK,
                rule_description="Check reward consistency across similar scenarios",
                threshold=0.7,
                tolerance=0.1,
                severity="medium",
                weight=0.6
            )
        ]
        
        return RewardModelConfig(
            config_id="default_config_v1.0",
            model_version="1.0.0",
            validation_rules=validation_rules,
            optimization_strategy=OptimizationStrategy.A_B_TESTING,
            ab_test_enabled=True,
            ab_test_split_ratio=0.5,
            ab_test_duration_days=30,
            description="Default reward validation configuration"
        )
    
    async def validate_reward_signal(self,
                                   reward_signal: 'RewardSignal',
                                   historical_context: List['RewardSignal'] = None,
                                   custom_rules: List[ValidationRule] = None) -> List[ValidationResult]:
        """驗證獎勵信號"""
        
        validation_results = []
        
        # 獲取適用的驗證規則
        rules_to_apply = custom_rules or self.model_config.validation_rules
        applicable_rules = [
            rule for rule in rules_to_apply 
            if rule.is_applicable(reward_signal)
        ]
        
        # 並行執行驗證
        validation_tasks = []
        
        for rule in applicable_rules:
            if rule.validation_type in self.validation_engines:
                engine = self.validation_engines[rule.validation_type]
                task = engine.validate(reward_signal, rule, historical_context)
                validation_tasks.append(task)
        
        if validation_tasks:
            results = await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Validation failed for rule {applicable_rules[i].rule_id}: {result}")
                    # 創建失敗結果
                    failed_result = ValidationResult(
                        result_id=f"failed_{reward_signal.signal_id}_{applicable_rules[i].rule_id}",
                        signal_id=reward_signal.signal_id,
                        rule_id=applicable_rules[i].rule_id,
                        validation_type=applicable_rules[i].validation_type,
                        status=ValidationStatus.FAILED,
                        confidence=0.0,
                        error_message=str(result)
                    )
                    validation_results.append(failed_result)
                else:
                    validation_results.append(result)
        
        # 記錄驗證歷史
        self.validation_history[reward_signal.signal_id] = validation_results
        
        # 更新統計
        self._update_validation_statistics(validation_results)
        
        # 自動修正（如果啟用）
        if self.enable_auto_correction:
            corrected_signal = await self._apply_auto_corrections(reward_signal, validation_results)
            if corrected_signal != reward_signal:
                self.logger.info(f"Applied auto-corrections to signal {reward_signal.signal_id}")
        
        # A/B測試分組（如果啟用）
        if self.enable_ab_testing and self.model_config.ab_test_enabled:
            await self._assign_ab_test_group(reward_signal, validation_results)
        
        self.logger.info(f"Validated signal {reward_signal.signal_id}: {len(validation_results)} checks completed")
        return validation_results
    
    def _update_validation_statistics(self, results: List[ValidationResult]):
        """更新驗證統計"""
        with self._stats_lock:
            for result in results:
                self.validation_stats['total_validations'] += 1
                
                if result.status == ValidationStatus.PASSED:
                    self.validation_stats['passed_validations'] += 1
                elif result.status == ValidationStatus.FAILED:
                    self.validation_stats['failed_validations'] += 1
                elif result.status == ValidationStatus.WARNING:
                    self.validation_stats['warning_validations'] += 1
        
        # 更新主要指標
        self.validation_metrics.total_validations = self.validation_stats['total_validations']
        self.validation_metrics.passed_validations = self.validation_stats['passed_validations']
        self.validation_metrics.failed_validations = self.validation_stats['failed_validations']
        self.validation_metrics.warning_validations = self.validation_stats['warning_validations']
        
        # 計算準確率
        if self.validation_metrics.total_validations > 0:
            self.validation_metrics.validation_accuracy = (
                self.validation_metrics.passed_validations / 
                self.validation_metrics.total_validations
            )
    
    async def _apply_auto_corrections(self,
                                    reward_signal: 'RewardSignal',
                                    validation_results: List[ValidationResult]) -> 'RewardSignal':
        """應用自動修正"""
        
        corrected_signal = reward_signal  # 創建副本會更好，但為了簡化...
        
        for result in validation_results:
            if result.status == ValidationStatus.FAILED and result.corrected_value is not None:
                # 應用修正（這裡需要根據具體情況實現）
                if result.validation_type == ValidationType.RANGE_CHECK:
                    # 範圍修正
                    if result.original_value < -1.0:
                        corrected_signal.weighted_total_reward = -1.0
                    elif result.original_value > 1.0:
                        corrected_signal.weighted_total_reward = 1.0
                    
                    self.logger.info(f"Applied range correction to signal {reward_signal.signal_id}")
        
        return corrected_signal
    
    async def _assign_ab_test_group(self,
                                   reward_signal: 'RewardSignal',
                                   validation_results: List[ValidationResult]):
        """分配A/B測試組"""
        
        # 簡單的隨機分組
        if random.random() < self.model_config.ab_test_split_ratio:
            group = "control"
        else:
            group = "treatment"
        
        self.ab_test_groups[reward_signal.signal_id] = group
        
        # 記錄A/B測試數據
        group_key = f"ab_test_{group}"
        if group_key not in self.ab_test_results:
            self.ab_test_results[group_key] = {
                'total_signals': 0,
                'avg_reward': 0.0,
                'validation_pass_rate': 0.0,
                'signals': []
            }
        
        self.ab_test_results[group_key]['total_signals'] += 1
        self.ab_test_results[group_key]['signals'].append(reward_signal.signal_id)
        
        # 更新平均獎勵
        current_avg = self.ab_test_results[group_key]['avg_reward']
        current_count = self.ab_test_results[group_key]['total_signals']
        new_avg = ((current_avg * (current_count - 1)) + reward_signal.weighted_total_reward) / current_count
        self.ab_test_results[group_key]['avg_reward'] = new_avg
        
        # 更新驗證通過率
        passed_validations = sum(1 for r in validation_results if r.status == ValidationStatus.PASSED)
        total_validations = len(validation_results)
        if total_validations > 0:
            validation_pass_rate = passed_validations / total_validations
            current_pass_rate = self.ab_test_results[group_key]['validation_pass_rate']
            new_pass_rate = ((current_pass_rate * (current_count - 1)) + validation_pass_rate) / current_count
            self.ab_test_results[group_key]['validation_pass_rate'] = new_pass_rate
    
    async def optimize_reward_model(self,
                                  optimization_target: str = "validation_accuracy",
                                  historical_data: List['RewardSignal'] = None) -> Dict[str, Any]:
        """優化獎勵模型"""
        
        optimization_results = {
            'optimization_target': optimization_target,
            'strategy_used': self.model_config.optimization_strategy.value,
            'improvements': {},
            'new_config': None,
            'performance_gain': 0.0
        }
        
        if self.model_config.optimization_strategy == OptimizationStrategy.A_B_TESTING:
            # A/B測試優化
            ab_results = await self._analyze_ab_test_results()
            optimization_results['improvements'] = ab_results
            
            if ab_results.get('significant_difference', False):
                winning_group = ab_results.get('winning_group')
                if winning_group:
                    self.logger.info(f"A/B test shows {winning_group} group performs better")
                    # 在實際實現中，這裡會更新模型配置
        
        # 規則權重優化
        if historical_data and len(historical_data) > 100:
            weight_optimization = await self._optimize_rule_weights(historical_data)
            optimization_results['improvements']['weight_optimization'] = weight_optimization
        
        return optimization_results
    
    async def _analyze_ab_test_results(self) -> Dict[str, Any]:
        """分析A/B測試結果"""
        
        if 'ab_test_control' not in self.ab_test_results or 'ab_test_treatment' not in self.ab_test_results:
            return {'error': 'Insufficient A/B test data'}
        
        control_data = self.ab_test_results['ab_test_control']
        treatment_data = self.ab_test_results['ab_test_treatment']
        
        # 計算統計顯著性（簡化版本）
        control_avg = control_data['avg_reward']
        treatment_avg = treatment_data['avg_reward']
        
        # 效果大小
        effect_size = abs(treatment_avg - control_avg)
        relative_improvement = (treatment_avg - control_avg) / abs(control_avg) if control_avg != 0 else 0
        
        # 簡單的顯著性檢驗
        min_sample_size = 30
        significant_difference = (
            control_data['total_signals'] >= min_sample_size and
            treatment_data['total_signals'] >= min_sample_size and
            effect_size > 0.05  # 5%的最小有意義差異
        )
        
        winning_group = "treatment" if treatment_avg > control_avg else "control"
        
        return {
            'control_group': {
                'avg_reward': control_avg,
                'sample_size': control_data['total_signals'],
                'validation_pass_rate': control_data['validation_pass_rate']
            },
            'treatment_group': {
                'avg_reward': treatment_avg,
                'sample_size': treatment_data['total_signals'],
                'validation_pass_rate': treatment_data['validation_pass_rate']
            },
            'effect_size': effect_size,
            'relative_improvement': relative_improvement,
            'significant_difference': significant_difference,
            'winning_group': winning_group if significant_difference else None,
            'confidence_level': 0.8 if significant_difference else 0.3
        }
    
    async def _optimize_rule_weights(self, historical_data: List['RewardSignal']) -> Dict[str, Any]:
        """優化規則權重"""
        
        # 這是一個簡化的權重優化實現
        # 實際中可能需要更複雜的機器學習算法
        
        current_weights = {rule.rule_id: rule.weight for rule in self.model_config.validation_rules}
        
        # 分析每個規則的有效性
        rule_effectiveness = {}
        
        for rule in self.model_config.validation_rules:
            rule_id = rule.rule_id
            
            # 計算該規則的準確率
            total_applications = 0
            correct_predictions = 0
            
            for signal in historical_data:
                if rule.is_applicable(signal):
                    total_applications += 1
                    
                    # 這裡需要實際的驗證邏輯來判斷正確性
                    # 簡化為假設高獎勵信號更可能是正確的
                    if signal.weighted_total_reward > 0.5:
                        correct_predictions += 1
            
            if total_applications > 0:
                effectiveness = correct_predictions / total_applications
                rule_effectiveness[rule_id] = effectiveness
        
        # 調整權重
        optimized_weights = current_weights.copy()
        
        for rule_id, effectiveness in rule_effectiveness.items():
            if effectiveness > 0.8:  # 高效規則
                optimized_weights[rule_id] = min(1.0, current_weights[rule_id] * 1.1)
            elif effectiveness < 0.6:  # 低效規則
                optimized_weights[rule_id] = max(0.1, current_weights[rule_id] * 0.9)
        
        return {
            'current_weights': current_weights,
            'optimized_weights': optimized_weights,
            'rule_effectiveness': rule_effectiveness,
            'optimization_applied': True
        }
    
    async def get_validation_report(self, 
                                  signal_id: str = None,
                                  time_range_days: int = 30) -> Dict[str, Any]:
        """獲取驗證報告"""
        
        cutoff_date = datetime.now() - timedelta(days=time_range_days)
        
        if signal_id:
            # 單個信號的報告
            if signal_id in self.validation_history:
                results = self.validation_history[signal_id]
                return self._create_signal_report(signal_id, results)
            else:
                return {'error': f'No validation history found for signal {signal_id}'}
        
        # 整體報告
        all_results = []
        for results_list in self.validation_history.values():
            for result in results_list:
                result_date = datetime.fromisoformat(result.validation_timestamp)
                if result_date >= cutoff_date:
                    all_results.append(result)
        
        return self._create_summary_report(all_results, time_range_days)
    
    def _create_signal_report(self, signal_id: str, results: List[ValidationResult]) -> Dict[str, Any]:
        """創建單個信號的驗證報告"""
        
        passed_count = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_count = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_count = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        avg_confidence = statistics.mean([r.confidence for r in results]) if results else 0.0
        
        return {
            'signal_id': signal_id,
            'total_validations': len(results),
            'passed_validations': passed_count,
            'failed_validations': failed_count,
            'warning_validations': warning_count,
            'pass_rate': passed_count / len(results) if results else 0.0,
            'average_confidence': avg_confidence,
            'validation_details': [result.to_dict() for result in results],
            'overall_status': 'PASSED' if failed_count == 0 else 'FAILED' if failed_count > len(results) / 2 else 'WARNING'
        }
    
    def _create_summary_report(self, results: List[ValidationResult], time_range_days: int) -> Dict[str, Any]:
        """創建摘要報告"""
        
        if not results:
            return {
                'time_range_days': time_range_days,
                'total_validations': 0,
                'message': 'No validation data available for the specified time range'
            }
        
        # 基本統計
        passed_count = sum(1 for r in results if r.status == ValidationStatus.PASSED)
        failed_count = sum(1 for r in results if r.status == ValidationStatus.FAILED)
        warning_count = sum(1 for r in results if r.status == ValidationStatus.WARNING)
        
        # 按驗證類型分組
        type_breakdown = defaultdict(lambda: {'passed': 0, 'failed': 0, 'warning': 0})
        for result in results:
            type_key = result.validation_type.value
            if result.status == ValidationStatus.PASSED:
                type_breakdown[type_key]['passed'] += 1
            elif result.status == ValidationStatus.FAILED:
                type_breakdown[type_key]['failed'] += 1
            elif result.status == ValidationStatus.WARNING:
                type_breakdown[type_key]['warning'] += 1
        
        # 平均置信度
        confidences = [r.confidence for r in results if r.confidence > 0]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        # A/B測試摘要
        ab_test_summary = None
        if self.enable_ab_testing and self.ab_test_results:
            ab_test_summary = {
                'control_group_size': self.ab_test_results.get('ab_test_control', {}).get('total_signals', 0),
                'treatment_group_size': self.ab_test_results.get('ab_test_treatment', {}).get('total_signals', 0),
                'control_avg_reward': self.ab_test_results.get('ab_test_control', {}).get('avg_reward', 0.0),
                'treatment_avg_reward': self.ab_test_results.get('ab_test_treatment', {}).get('avg_reward', 0.0)
            }
        
        return {
            'time_range_days': time_range_days,
            'total_validations': len(results),
            'passed_validations': passed_count,
            'failed_validations': failed_count,
            'warning_validations': warning_count,
            'overall_pass_rate': passed_count / len(results),
            'average_confidence': avg_confidence,
            'validation_type_breakdown': dict(type_breakdown),
            'ab_test_summary': ab_test_summary,
            'system_metrics': self.validation_metrics.to_dict(),
            'report_generated_at': datetime.now().isoformat()
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'validator_status': 'active',
            'validation_engines': list(self.validation_engines.keys()),
            'active_rules': len(self.model_config.validation_rules),
            'ab_testing_enabled': self.enable_ab_testing,
            'auto_correction_enabled': self.enable_auto_correction,
            'validation_history_size': len(self.validation_history),
            'metrics': self.validation_metrics.to_dict(),
            'storage_path': str(self.storage_path),
            'last_optimization': 'not_implemented',
            'system_health': 'good'
        }
    
    async def cleanup(self):
        """清理資源"""
        # 保存驗證歷史
        await self._save_validation_history()
        
        # 關閉線程池
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("RewardValidator cleanup completed")
    
    async def _save_validation_history(self):
        """保存驗證歷史"""
        try:
            history_file = self.storage_path / "validation_history.json"
            
            # 轉換為可序列化格式
            serializable_history = {}
            for signal_id, results in self.validation_history.items():
                serializable_history[signal_id] = [result.to_dict() for result in results]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_history, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Saved validation history to {history_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save validation history: {e}")

# 工廠函數
async def create_reward_validator(
    storage_path: str = None,
    model_config: RewardModelConfig = None,
    enable_auto_correction: bool = True,
    enable_ab_testing: bool = True,
    custom_engines: Dict[ValidationType, ValidationEngine] = None
) -> RewardValidator:
    """創建獎勵驗證器實例"""
    
    validator = RewardValidator(
        storage_path=storage_path,
        model_config=model_config,
        enable_auto_correction=enable_auto_correction,
        enable_ab_testing=enable_ab_testing
    )
    
    # 添加自定義驗證引擎
    if custom_engines:
        validator.validation_engines.update(custom_engines)
    
    return validator


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_reward_validator():
        print("🔍 測試RewardValidator")
        
        # 創建驗證器
        validator = await create_reward_validator("./test_validation")
        
        # 創建模擬獎勵信號
        class MockRewardSignal:
            def __init__(self, signal_id: str, reward_value: float):
                self.signal_id = signal_id
                self.weighted_total_reward = reward_value
                self.reward_components = {}
                self.membership_tier = MembershipTier.GOLD
        
        # 測試不同場景的獎勵信號
        test_signals = [
            MockRewardSignal("normal_signal", 0.75),      # 正常
            MockRewardSignal("high_reward", 1.2),         # 超出範圍
            MockRewardSignal("negative_signal", -0.8),    # 負獎勵
            MockRewardSignal("extreme_outlier", 2.5)      # 極端異常值
        ]
        
        for signal in test_signals:
            print(f"\n🎯 驗證信號: {signal.signal_id} (獎勵: {signal.weighted_total_reward})")
            
            validation_results = await validator.validate_reward_signal(signal)
            
            for result in validation_results:
                status_emoji = {
                    ValidationStatus.PASSED: '✅',
                    ValidationStatus.WARNING: '⚠️',
                    ValidationStatus.FAILED: '❌'
                }.get(result.status, '❓')
                
                print(f"  {status_emoji} {result.validation_type.value}: {result.status.value} (信心: {result.confidence:.2f})")
                
                if result.error_message:
                    print(f"      詳情: {result.error_message}")
        
        # 獲取驗證報告
        print(f"\n📊 驗證報告:")
        report = await validator.get_validation_report()
        print(f"  總驗證次數: {report['total_validations']}")
        print(f"  通過率: {report['overall_pass_rate']:.2%}")
        print(f"  平均信心度: {report['average_confidence']:.2f}")
        
        # 系統狀態
        status = validator.get_system_status()
        print(f"  系統狀態: {status['validator_status']}")
        print(f"  啟用引擎: {len(status['validation_engines'])}")
        
        # 清理
        await validator.cleanup()
        
        print("✅ RewardValidator測試完成")
    
    asyncio.run(test_reward_validator())