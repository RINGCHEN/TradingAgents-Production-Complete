#!/usr/bin/env python3
"""
模型持續進化機制
Model Evolution System - GPT-OSS整合任務4.1.4

模型持續進化機制是階段4智能化增強的核心組件，通過模型版本控制和A/B測試框架，
實現AI模型的持續優化和自動化演進能力。

主要功能：
1. 模型版本控制 - 自動化模型版本管理
2. A/B測試框架 - 多模型並行測試和評估
3. 性能監控系統 - 實時模型性能追蹤
4. 自動模型選擇 - 基於性能指標的模型切換
5. 增量學習機制 - 在線模型更新和優化
6. 模型融合策略 - 多模型集成和權重調整
"""

import os
import json
import logging
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field, asdict
from pydantic import BaseModel, Field, validator
from pathlib import Path
import pickle
import hashlib
import shutil
from collections import defaultdict, deque
import uuid
import warnings
from abc import ABC, abstractmethod
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from concurrent.futures import ThreadPoolExecutor
import threading
import time

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 忽略警告
warnings.filterwarnings("ignore")


class ModelStatus(str, Enum):
    """模型狀態枚舉"""
    DEVELOPMENT = "development"         # 開發中
    TESTING = "testing"                # 測試中
    STAGING = "staging"                # 預發布
    PRODUCTION = "production"          # 生產環境
    DEPRECATED = "deprecated"          # 已棄用
    RETIRED = "retired"                # 已退役


class TestType(str, Enum):
    """測試類型枚舉"""
    AB_TEST = "ab_test"                # A/B測試
    CANARY = "canary"                  # 金絲雀發布
    CHAMPION_CHALLENGER = "champion_challenger"  # 冠軍挑戰者
    MULTI_VARIANT = "multi_variant"    # 多變量測試
    SHADOW = "shadow"                  # 影子測試


class EvolutionStrategy(str, Enum):
    """進化策略枚舉"""
    PERFORMANCE_BASED = "performance_based"      # 基於性能
    DIVERSITY_BASED = "diversity_based"          # 基於多樣性
    ENSEMBLE_BASED = "ensemble_based"            # 基於集成
    INCREMENTAL = "incremental"                  # 增量式
    REVOLUTIONARY = "revolutionary"              # 革命式


class MetricType(str, Enum):
    """指標類型枚舉"""
    ACCURACY = "accuracy"              # 準確率
    PRECISION = "precision"            # 精確率
    RECALL = "recall"                  # 召回率
    F1_SCORE = "f1_score"             # F1分數
    AUC = "auc"                       # AUC
    RETURN = "return"                 # 收益率
    SHARPE_RATIO = "sharpe_ratio"     # 夏普比率
    MAX_DRAWDOWN = "max_drawdown"     # 最大回撤
    WIN_RATE = "win_rate"             # 勝率
    VOLATILITY = "volatility"         # 波動率


@dataclass
class ModelMetrics:
    """模型指標類"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc: float = 0.0
    return_rate: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    volatility: float = 0.0
    prediction_latency: float = 0.0
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """轉換為字典"""
        return asdict(self)
    
    def calculate_composite_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """計算綜合評分"""
        if weights is None:
            weights = {
                'accuracy': 0.15,
                'f1_score': 0.15,
                'return_rate': 0.25,
                'sharpe_ratio': 0.20,
                'max_drawdown': -0.10,  # 負權重，回撤越小越好
                'win_rate': 0.15,
                'prediction_latency': -0.05,  # 負權重，延遲越小越好
                'confidence_score': 0.15
            }
        
        score = 0.0
        for metric, weight in weights.items():
            if hasattr(self, metric):
                value = getattr(self, metric)
                score += value * weight
        
        return max(0.0, min(1.0, score))


@dataclass
class ModelVersion:
    """模型版本類"""
    version_id: str
    model_name: str
    version_number: str
    status: ModelStatus
    created_at: datetime
    created_by: str
    description: str
    model_config: Dict[str, Any]
    training_data_hash: str
    model_file_path: str
    metrics: ModelMetrics
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_version_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'version_id': self.version_id,
            'model_name': self.model_name,
            'version_number': self.version_number,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'description': self.description,
            'model_config': self.model_config,
            'training_data_hash': self.training_data_hash,
            'model_file_path': self.model_file_path,
            'metrics': self.metrics.to_dict(),
            'metadata': self.metadata,
            'parent_version_id': self.parent_version_id
        }


@dataclass
class ExperimentResult:
    """實驗結果類"""
    experiment_id: str
    model_version_id: str
    test_data_hash: str
    metrics: ModelMetrics
    test_duration: float
    sample_size: int
    timestamp: datetime
    additional_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'experiment_id': self.experiment_id,
            'model_version_id': self.model_version_id,
            'test_data_hash': self.test_data_hash,
            'metrics': self.metrics.to_dict(),
            'test_duration': self.test_duration,
            'sample_size': self.sample_size,
            'timestamp': self.timestamp.isoformat(),
            'additional_metrics': self.additional_metrics
        }


@dataclass
class ABTestConfig:
    """A/B測試配置類"""
    test_id: str
    test_name: str
    test_type: TestType
    control_model_id: str
    treatment_model_ids: List[str]
    traffic_allocation: Dict[str, float]
    success_metrics: List[MetricType]
    minimum_sample_size: int
    test_duration_days: int
    significance_level: float = 0.05
    power: float = 0.8
    early_stopping_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'test_type': self.test_type.value,
            'control_model_id': self.control_model_id,
            'treatment_model_ids': self.treatment_model_ids,
            'traffic_allocation': self.traffic_allocation,
            'success_metrics': [metric.value for metric in self.success_metrics],
            'minimum_sample_size': self.minimum_sample_size,
            'test_duration_days': self.test_duration_days,
            'significance_level': self.significance_level,
            'power': self.power,
            'early_stopping_enabled': self.early_stopping_enabled
        }


class ModelEvolutionConfig(BaseModel):
    """模型進化系統配置"""
    system_id: str = Field(..., description="系統ID")
    system_name: str = Field(..., description="系統名稱")
    
    # 版本控制配置
    model_repository_path: str = Field("./model_repository", description="模型倉庫路径")
    max_versions_per_model: int = Field(10, description="每個模型最大版本數")
    auto_cleanup_enabled: bool = Field(True, description="是否啟用自動清理")
    backup_enabled: bool = Field(True, description="是否啟用備份")
    
    # A/B測試配置
    ab_testing_enabled: bool = Field(True, description="是否啟用A/B測試")
    default_test_duration_days: int = Field(7, description="默認測試持續天數")
    minimum_sample_size: int = Field(1000, description="最小樣本大小")
    significance_level: float = Field(0.05, description="顯著性水平")
    max_concurrent_tests: int = Field(5, description="最大並發測試數")
    
    # 性能監控配置
    monitoring_enabled: bool = Field(True, description="是否啟用監控")
    monitoring_interval_minutes: int = Field(60, description="監控間隔分鐘數")
    alert_threshold_performance_drop: float = Field(0.1, description="性能下降預警閾值")
    metric_retention_days: int = Field(90, description="指標保留天數")
    
    # 自動進化配置
    auto_evolution_enabled: bool = Field(True, description="是否啟用自動進化")
    evolution_strategy: EvolutionStrategy = Field(EvolutionStrategy.PERFORMANCE_BASED, description="進化策略")
    evolution_frequency_hours: int = Field(24, description="進化頻率小時數")
    performance_threshold: float = Field(0.05, description="性能改進閾值")
    
    # 集成模型配置
    ensemble_enabled: bool = Field(True, description="是否啟用集成模型")
    max_ensemble_models: int = Field(5, description="最大集成模型數量")
    ensemble_weight_update_frequency: int = Field(100, description="集成權重更新頻率")
    
    # 增量學習配置
    incremental_learning_enabled: bool = Field(True, description="是否啟用增量學習")
    batch_size_incremental: int = Field(32, description="增量學習批量大小")
    learning_rate_decay: float = Field(0.95, description="學習率衰減")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ModelRegistry:
    """模型註冊表"""
    
    def __init__(self, repository_path: str):
        self.repository_path = Path(repository_path)
        self.registry_file = self.repository_path / "registry.json"
        self.models = {}
        self.versions = {}
        
        # 確保目錄存在
        self.repository_path.mkdir(parents=True, exist_ok=True)
        
        # 載入現有註冊表
        self._load_registry()
    
    def register_model(self, model_version: ModelVersion) -> bool:
        """註冊模型版本"""
        try:
            model_name = model_version.model_name
            version_id = model_version.version_id
            
            # 更新模型索引
            if model_name not in self.models:
                self.models[model_name] = {
                    'model_name': model_name,
                    'versions': [],
                    'active_version': None,
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            
            # 添加版本
            self.models[model_name]['versions'].append(version_id)
            self.versions[version_id] = model_version
            
            # 如果是第一個版本或狀態為生產環境，設為活躍版本
            if (not self.models[model_name]['active_version'] or 
                model_version.status == ModelStatus.PRODUCTION):
                self.models[model_name]['active_version'] = version_id
            
            # 保存註冊表
            self._save_registry()
            
            logger.info(f"Model version registered: {model_name}:{model_version.version_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register model: {e}")
            return False
    
    def get_model_version(self, version_id: str) -> Optional[ModelVersion]:
        """獲取模型版本"""
        return self.versions.get(version_id)
    
    def get_active_version(self, model_name: str) -> Optional[ModelVersion]:
        """獲取活躍模型版本"""
        if model_name not in self.models:
            return None
        
        active_version_id = self.models[model_name]['active_version']
        return self.versions.get(active_version_id) if active_version_id else None
    
    def list_model_versions(self, model_name: str) -> List[ModelVersion]:
        """列出模型的所有版本"""
        if model_name not in self.models:
            return []
        
        version_ids = self.models[model_name]['versions']
        return [self.versions[vid] for vid in version_ids if vid in self.versions]
    
    def update_model_status(self, version_id: str, new_status: ModelStatus) -> bool:
        """更新模型狀態"""
        if version_id not in self.versions:
            return False
        
        self.versions[version_id].status = new_status
        self._save_registry()
        
        logger.info(f"Model status updated: {version_id} -> {new_status.value}")
        return True
    
    def set_active_version(self, model_name: str, version_id: str) -> bool:
        """設置活躍版本"""
        if (model_name not in self.models or 
            version_id not in self.versions):
            return False
        
        self.models[model_name]['active_version'] = version_id
        self._save_registry()
        
        logger.info(f"Active version updated: {model_name} -> {version_id}")
        return True
    
    def cleanup_old_versions(self, model_name: str, max_versions: int) -> int:
        """清理舊版本"""
        if model_name not in self.models:
            return 0
        
        versions = self.list_model_versions(model_name)
        if len(versions) <= max_versions:
            return 0
        
        # 按創建時間排序，保留最新的版本
        versions.sort(key=lambda v: v.created_at, reverse=True)
        versions_to_remove = versions[max_versions:]
        
        removed_count = 0
        for version in versions_to_remove:
            if version.status in [ModelStatus.DEPRECATED, ModelStatus.RETIRED]:
                # 刪除模型文件
                try:
                    if os.path.exists(version.model_file_path):
                        os.remove(version.model_file_path)
                except Exception as e:
                    logger.warning(f"Failed to remove model file {version.model_file_path}: {e}")
                
                # 從註冊表移除
                self.models[model_name]['versions'].remove(version.version_id)
                del self.versions[version.version_id]
                removed_count += 1
        
        if removed_count > 0:
            self._save_registry()
            logger.info(f"Cleaned up {removed_count} old versions for {model_name}")
        
        return removed_count
    
    def _load_registry(self):
        """載入註冊表"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.models = data.get('models', {})
                
                # 載入版本信息
                versions_data = data.get('versions', {})
                for version_id, version_dict in versions_data.items():
                    # 重建ModelVersion對象
                    version = ModelVersion(
                        version_id=version_dict['version_id'],
                        model_name=version_dict['model_name'],
                        version_number=version_dict['version_number'],
                        status=ModelStatus(version_dict['status']),
                        created_at=datetime.fromisoformat(version_dict['created_at']),
                        created_by=version_dict['created_by'],
                        description=version_dict['description'],
                        model_config=version_dict['model_config'],
                        training_data_hash=version_dict['training_data_hash'],
                        model_file_path=version_dict['model_file_path'],
                        metrics=ModelMetrics(**version_dict['metrics']),
                        metadata=version_dict.get('metadata', {}),
                        parent_version_id=version_dict.get('parent_version_id')
                    )
                    self.versions[version_id] = version
                
            except Exception as e:
                logger.warning(f"Failed to load registry: {e}")
                self.models = {}
                self.versions = {}
    
    def _save_registry(self):
        """保存註冊表"""
        try:
            data = {
                'models': self.models,
                'versions': {
                    version_id: version.to_dict() 
                    for version_id, version in self.versions.items()
                }
            }
            
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            logger.error(f"Failed to save registry: {e}")
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """獲取註冊表統計信息"""
        status_counts = defaultdict(int)
        for version in self.versions.values():
            status_counts[version.status.value] += 1
        
        return {
            'total_models': len(self.models),
            'total_versions': len(self.versions),
            'status_distribution': dict(status_counts),
            'models_summary': [
                {
                    'model_name': name,
                    'version_count': len(info['versions']),
                    'active_version': info['active_version']
                }
                for name, info in self.models.items()
            ]
        }


class ABTestRunner:
    """A/B測試運行器"""
    
    def __init__(self, model_registry: ModelRegistry):
        self.model_registry = model_registry
        self.active_tests = {}
        self.test_results = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def create_ab_test(self, config: ABTestConfig) -> bool:
        """創建A/B測試"""
        try:
            # 驗證模型存在
            control_model = self.model_registry.get_model_version(config.control_model_id)
            if not control_model:
                logger.error(f"Control model not found: {config.control_model_id}")
                return False
            
            for treatment_id in config.treatment_model_ids:
                treatment_model = self.model_registry.get_model_version(treatment_id)
                if not treatment_model:
                    logger.error(f"Treatment model not found: {treatment_id}")
                    return False
            
            # 驗證流量分配
            total_allocation = sum(config.traffic_allocation.values())
            if abs(total_allocation - 1.0) > 0.001:
                logger.error(f"Traffic allocation must sum to 1.0, got {total_allocation}")
                return False
            
            # 創建測試
            test_info = {
                'config': config,
                'status': 'running',
                'start_time': datetime.now(timezone.utc),
                'end_time': datetime.now(timezone.utc) + timedelta(days=config.test_duration_days),
                'samples_collected': defaultdict(int),
                'results': defaultdict(list)
            }
            
            self.active_tests[config.test_id] = test_info
            
            logger.info(f"A/B test created: {config.test_name} ({config.test_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create A/B test: {e}")
            return False
    
    def collect_sample(self, test_id: str, model_id: str, 
                      prediction: Any, actual: Any, metrics: Dict[str, float]) -> bool:
        """收集測試樣本"""
        if test_id not in self.active_tests:
            return False
        
        test_info = self.active_tests[test_id]
        
        # 記錄樣本
        test_info['samples_collected'][model_id] += 1
        test_info['results'][model_id].append({
            'prediction': prediction,
            'actual': actual,
            'metrics': metrics,
            'timestamp': datetime.now(timezone.utc)
        })
        
        # 檢查是否滿足早停條件
        if test_info['config'].early_stopping_enabled:
            if self._check_early_stopping(test_id):
                self._finalize_test(test_id)
        
        return True
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """獲取測試狀態"""
        if test_id not in self.active_tests:
            return None
        
        test_info = self.active_tests[test_id]
        config = test_info['config']
        
        # 計算進度
        total_samples = sum(test_info['samples_collected'].values())
        progress = min(1.0, total_samples / config.minimum_sample_size)
        
        # 計算當前指標
        current_metrics = {}
        for model_id, results in test_info['results'].items():
            if results:
                model_metrics = defaultdict(list)
                for result in results:
                    for metric, value in result['metrics'].items():
                        model_metrics[metric].append(value)
                
                current_metrics[model_id] = {
                    metric: np.mean(values) 
                    for metric, values in model_metrics.items()
                }
        
        return {
            'test_id': test_id,
            'test_name': config.test_name,
            'status': test_info['status'],
            'progress': progress,
            'start_time': test_info['start_time'].isoformat(),
            'end_time': test_info['end_time'].isoformat(),
            'samples_collected': dict(test_info['samples_collected']),
            'current_metrics': current_metrics
        }
    
    def analyze_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """分析測試結果"""
        if test_id not in self.active_tests:
            return None
        
        test_info = self.active_tests[test_id]
        config = test_info['config']
        
        try:
            # 計算各模型的統計指標
            model_stats = {}
            for model_id, results in test_info['results'].items():
                if not results:
                    continue
                
                metrics_arrays = defaultdict(list)
                for result in results:
                    for metric, value in result['metrics'].items():
                        metrics_arrays[metric].append(value)
                
                stats = {}
                for metric, values in metrics_arrays.items():
                    stats[metric] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'count': len(values),
                        'confidence_interval': self._calculate_confidence_interval(values)
                    }
                
                model_stats[model_id] = stats
            
            # 執行統計顯著性測試
            significance_tests = {}
            control_id = config.control_model_id
            
            for treatment_id in config.treatment_model_ids:
                if control_id in model_stats and treatment_id in model_stats:
                    test_results = {}
                    
                    for metric in config.success_metrics:
                        metric_name = metric.value
                        if (metric_name in model_stats[control_id] and 
                            metric_name in model_stats[treatment_id]):
                            
                            control_values = [
                                r['metrics'][metric_name] 
                                for r in test_info['results'][control_id]
                                if metric_name in r['metrics']
                            ]
                            
                            treatment_values = [
                                r['metrics'][metric_name] 
                                for r in test_info['results'][treatment_id]
                                if metric_name in r['metrics']
                            ]
                            
                            if control_values and treatment_values:
                                p_value, effect_size = self._perform_statistical_test(
                                    control_values, treatment_values
                                )
                                
                                test_results[metric_name] = {
                                    'p_value': p_value,
                                    'effect_size': effect_size,
                                    'significant': p_value < config.significance_level,
                                    'control_mean': np.mean(control_values),
                                    'treatment_mean': np.mean(treatment_values),
                                    'improvement': (np.mean(treatment_values) - np.mean(control_values)) / np.mean(control_values) if np.mean(control_values) != 0 else 0
                                }
                    
                    significance_tests[f"{control_id}_vs_{treatment_id}"] = test_results
            
            # 確定獲勝模型
            winner = self._determine_winner(model_stats, significance_tests, config)
            
            return {
                'test_id': test_id,
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                'model_statistics': model_stats,
                'significance_tests': significance_tests,
                'winner': winner,
                'recommendations': self._generate_recommendations(model_stats, significance_tests, winner)
            }
            
        except Exception as e:
            logger.error(f"Test analysis failed: {e}")
            return None
    
    def _check_early_stopping(self, test_id: str) -> bool:
        """檢查早停條件"""
        test_info = self.active_tests[test_id]
        config = test_info['config']
        
        # 檢查最小樣本量
        total_samples = sum(test_info['samples_collected'].values())
        if total_samples < config.minimum_sample_size:
            return False
        
        # 檢查統計顯著性
        analysis = self.analyze_test_results(test_id)
        if not analysis:
            return False
        
        # 如果所有主要指標都達到顯著性，可以早停
        for test_name, test_results in analysis['significance_tests'].items():
            for metric in config.success_metrics:
                metric_name = metric.value
                if (metric_name in test_results and 
                    test_results[metric_name].get('significant', False)):
                    return True
        
        return False
    
    def _finalize_test(self, test_id: str):
        """完成測試"""
        if test_id in self.active_tests:
            self.active_tests[test_id]['status'] = 'completed'
            self.active_tests[test_id]['actual_end_time'] = datetime.now(timezone.utc)
            
            # 分析最終結果
            final_analysis = self.analyze_test_results(test_id)
            if final_analysis:
                self.test_results[test_id] = final_analysis
            
            logger.info(f"A/B test completed: {test_id}")
    
    def _calculate_confidence_interval(self, values: List[float], 
                                     confidence_level: float = 0.95) -> Tuple[float, float]:
        """計算置信區間"""
        if len(values) < 2:
            return (0.0, 0.0)
        
        mean = np.mean(values)
        std_error = np.std(values) / np.sqrt(len(values))
        
        # 使用t分佈
        from scipy.stats import t
        alpha = 1 - confidence_level
        t_value = t.ppf(1 - alpha/2, len(values) - 1)
        
        margin_error = t_value * std_error
        
        return (mean - margin_error, mean + margin_error)
    
    def _perform_statistical_test(self, control_values: List[float], 
                                treatment_values: List[float]) -> Tuple[float, float]:
        """執行統計檢驗"""
        try:
            from scipy.stats import ttest_ind
            
            # 獨立樣本t檢驗
            t_stat, p_value = ttest_ind(control_values, treatment_values)
            
            # 計算效應大小（Cohen's d）
            control_mean = np.mean(control_values)
            treatment_mean = np.mean(treatment_values)
            pooled_std = np.sqrt((np.var(control_values) + np.var(treatment_values)) / 2)
            
            effect_size = (treatment_mean - control_mean) / pooled_std if pooled_std > 0 else 0
            
            return p_value, effect_size
            
        except Exception as e:
            logger.warning(f"Statistical test failed: {e}")
            return 1.0, 0.0
    
    def _determine_winner(self, model_stats: Dict[str, Any], 
                         significance_tests: Dict[str, Any],
                         config: ABTestConfig) -> Dict[str, Any]:
        """確定獲勝模型"""
        
        # 簡單的獲勝者判定邏輯
        best_model = config.control_model_id
        best_score = 0.0
        
        for model_id, stats in model_stats.items():
            # 計算綜合得分
            score = 0.0
            for metric in config.success_metrics:
                metric_name = metric.value
                if metric_name in stats:
                    score += stats[metric_name]['mean']
            
            if score > best_score:
                best_score = score
                best_model = model_id
        
        return {
            'winning_model': best_model,
            'score': best_score,
            'confidence': 'high' if best_model != config.control_model_id else 'low'
        }
    
    def _generate_recommendations(self, model_stats: Dict[str, Any],
                                significance_tests: Dict[str, Any],
                                winner: Dict[str, Any]) -> List[str]:
        """生成建議"""
        recommendations = []
        
        if winner['winning_model'] != winner.get('control_model', ''):
            recommendations.append(f"建議將模型切換至 {winner['winning_model']}")
        
        # 基於統計檢驗結果生成更多建議
        for test_name, results in significance_tests.items():
            significant_improvements = [
                metric for metric, result in results.items()
                if result.get('significant', False) and result.get('improvement', 0) > 0
            ]
            
            if significant_improvements:
                recommendations.append(f"在指標 {', '.join(significant_improvements)} 上有顯著改進")
        
        if not recommendations:
            recommendations.append("未發現顯著性差異，建議繼續使用當前模型")
        
        return recommendations
    
    def get_active_tests(self) -> List[Dict[str, Any]]:
        """獲取活躍測試"""
        return [
            self.get_test_status(test_id) 
            for test_id in self.active_tests.keys()
        ]


class PerformanceMonitor:
    """性能監控器"""
    
    def __init__(self, config: ModelEvolutionConfig):
        self.config = config
        self.metrics_history = defaultdict(deque)
        self.alerts = deque(maxlen=1000)
        self.monitoring_thread = None
        self.stop_monitoring = False
        
    def start_monitoring(self, model_registry: ModelRegistry):
        """開始監控"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(model_registry,)
        )
        self.monitoring_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring_service(self):
        """停止監控"""
        self.stop_monitoring = True
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def record_prediction_metrics(self, model_id: str, metrics: ModelMetrics):
        """記錄預測指標"""
        timestamp = datetime.now(timezone.utc)
        
        # 記錄各項指標
        metric_dict = metrics.to_dict()
        for metric_name, value in metric_dict.items():
            self.metrics_history[f"{model_id}_{metric_name}"].append((timestamp, value))
        
        # 清理舊數據
        self._cleanup_old_metrics()
        
        # 檢查預警條件
        self._check_alerts(model_id, metrics)
    
    def get_model_performance_trend(self, model_id: str, 
                                  hours_back: int = 24) -> Dict[str, Any]:
        """獲取模型性能趨勢"""
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        trends = {}
        
        for key, history in self.metrics_history.items():
            if key.startswith(f"{model_id}_"):
                metric_name = key[len(f"{model_id}_"):]
                
                # 過濾最近的數據
                recent_data = [(t, v) for t, v in history if t >= cutoff_time]
                
                if len(recent_data) >= 2:
                    values = [v for _, v in recent_data]
                    timestamps = [t for t, _ in recent_data]
                    
                    trends[metric_name] = {
                        'current_value': values[-1],
                        'average_value': np.mean(values),
                        'trend_slope': self._calculate_trend_slope(timestamps, values),
                        'data_points': len(values)
                    }
        
        return trends
    
    def detect_performance_degradation(self, model_id: str) -> Dict[str, Any]:
        """檢測性能退化"""
        
        # 比較最近1小時vs最近24小時的性能
        recent_trend = self.get_model_performance_trend(model_id, hours_back=1)
        baseline_trend = self.get_model_performance_trend(model_id, hours_back=24)
        
        degradation_alerts = []
        
        for metric_name in recent_trend:
            if metric_name in baseline_trend:
                recent_avg = recent_trend[metric_name]['average_value']
                baseline_avg = baseline_trend[metric_name]['average_value']
                
                if baseline_avg > 0:
                    change_ratio = (recent_avg - baseline_avg) / baseline_avg
                    
                    # 檢查是否超過閾值
                    if change_ratio < -self.config.alert_threshold_performance_drop:
                        degradation_alerts.append({
                            'metric': metric_name,
                            'recent_avg': recent_avg,
                            'baseline_avg': baseline_avg,
                            'change_ratio': change_ratio,
                            'severity': 'high' if change_ratio < -0.2 else 'medium'
                        })
        
        return {
            'model_id': model_id,
            'degradation_detected': len(degradation_alerts) > 0,
            'alerts': degradation_alerts,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _monitoring_loop(self, model_registry: ModelRegistry):
        """監控循環"""
        while not self.stop_monitoring:
            try:
                # 獲取所有生產環境模型
                for model_name, model_info in model_registry.models.items():
                    active_version_id = model_info.get('active_version')
                    if active_version_id:
                        active_version = model_registry.get_model_version(active_version_id)
                        if active_version and active_version.status == ModelStatus.PRODUCTION:
                            
                            # 檢測性能退化
                            degradation = self.detect_performance_degradation(active_version_id)
                            if degradation['degradation_detected']:
                                self._create_alert(
                                    f"Performance degradation detected for {model_name}",
                                    degradation,
                                    'high'
                                )
                
                # 等待下一次檢查
                time.sleep(self.config.monitoring_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)  # 錯誤時等待1分鐘
    
    def _cleanup_old_metrics(self):
        """清理舊指標"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.config.metric_retention_days)
        
        for key, history in self.metrics_history.items():
            while history and history[0][0] < cutoff_time:
                history.popleft()
    
    def _check_alerts(self, model_id: str, metrics: ModelMetrics):
        """檢查預警條件"""
        
        # 檢查延遲預警
        if metrics.prediction_latency > 1000:  # 大於1秒
            self._create_alert(
                f"High prediction latency for model {model_id}",
                {'latency': metrics.prediction_latency, 'threshold': 1000},
                'medium'
            )
        
        # 檢查準確率預警
        if metrics.accuracy < 0.6:  # 準確率低於60%
            self._create_alert(
                f"Low accuracy for model {model_id}",
                {'accuracy': metrics.accuracy, 'threshold': 0.6},
                'high'
            )
    
    def _create_alert(self, message: str, details: Dict[str, Any], severity: str):
        """創建預警"""
        alert = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': message,
            'details': details,
            'severity': severity
        }
        
        self.alerts.append(alert)
        logger.warning(f"Alert: {message}")
    
    def _calculate_trend_slope(self, timestamps: List[datetime], values: List[float]) -> float:
        """計算趨勢斜率"""
        if len(timestamps) < 2:
            return 0.0
        
        # 將時間戳轉換為數值
        time_numeric = [(t - timestamps[0]).total_seconds() for t in timestamps]
        
        # 簡單線性回歸
        x_mean = np.mean(time_numeric)
        y_mean = np.mean(values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(time_numeric, values))
        denominator = sum((x - x_mean) ** 2 for x in time_numeric)
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def get_recent_alerts(self, hours_back: int = 24) -> List[Dict[str, Any]]:
        """獲取最近的預警"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
        ]


class ModelEvolutionSystem:
    """模型進化系統核心類"""
    
    def __init__(self, config: ModelEvolutionConfig):
        self.config = config
        self.is_initialized = False
        
        # 核心組件
        self.model_registry = None
        self.ab_test_runner = None
        self.performance_monitor = None
        
        # 進化狀態
        self.evolution_history = deque(maxlen=1000)
        self.current_experiments = {}
        
        # 統計信息
        self.system_stats = {
            'total_models_registered': 0,
            'total_experiments_run': 0,
            'successful_evolutions': 0,
            'average_improvement': 0.0
        }
        
        logger.info(f"ModelEvolutionSystem initialized: {config.system_name}")
    
    async def initialize(self) -> bool:
        """初始化模型進化系統"""
        try:
            logger.info("Initializing ModelEvolutionSystem...")
            
            # 1. 初始化模型註冊表
            self.model_registry = ModelRegistry(self.config.model_repository_path)
            
            # 2. 初始化A/B測試運行器
            if self.config.ab_testing_enabled:
                self.ab_test_runner = ABTestRunner(self.model_registry)
            
            # 3. 初始化性能監控器
            if self.config.monitoring_enabled:
                self.performance_monitor = PerformanceMonitor(self.config)
                self.performance_monitor.start_monitoring(self.model_registry)
            
            # 4. 載入系統統計
            await self._load_system_stats()
            
            self.is_initialized = True
            logger.info("ModelEvolutionSystem initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"ModelEvolutionSystem initialization failed: {e}")
            return False
    
    async def register_model(self, model_name: str, model_config: Dict[str, Any],
                           model_file_path: str, training_data_hash: str,
                           creator: str, description: str = "") -> Optional[str]:
        """註冊新模型版本"""
        try:
            # 生成版本ID
            version_id = str(uuid.uuid4())
            
            # 確定版本號
            existing_versions = self.model_registry.list_model_versions(model_name)
            version_number = f"v{len(existing_versions) + 1}.0"
            
            # 初始化指標
            initial_metrics = ModelMetrics()
            
            # 創建模型版本
            model_version = ModelVersion(
                version_id=version_id,
                model_name=model_name,
                version_number=version_number,
                status=ModelStatus.DEVELOPMENT,
                created_at=datetime.now(timezone.utc),
                created_by=creator,
                description=description,
                model_config=model_config,
                training_data_hash=training_data_hash,
                model_file_path=model_file_path,
                metrics=initial_metrics
            )
            
            # 註冊模型
            if self.model_registry.register_model(model_version):
                self.system_stats['total_models_registered'] += 1
                await self._save_system_stats()
                
                logger.info(f"Model registered: {model_name}:{version_number} ({version_id})")
                return version_id
            
            return None
            
        except Exception as e:
            logger.error(f"Model registration failed: {e}")
            return None
    
    async def evaluate_model_version(self, version_id: str,
                                   evaluation_data: Any,
                                   evaluation_metrics: List[MetricType]) -> bool:
        """評估模型版本"""
        try:
            model_version = self.model_registry.get_model_version(version_id)
            if not model_version:
                logger.error(f"Model version not found: {version_id}")
                return False
            
            # 模擬模型評估（實際應用中需要載入模型並評估）
            logger.info(f"Evaluating model version: {version_id}")
            
            # 生成模擬評估結果
            evaluation_results = self._simulate_model_evaluation(evaluation_metrics)
            
            # 更新模型指標
            model_version.metrics = ModelMetrics(**evaluation_results)
            
            # 更新模型狀態為測試中
            self.model_registry.update_model_status(version_id, ModelStatus.TESTING)
            
            logger.info(f"Model evaluation completed: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Model evaluation failed: {e}")
            return False
    
    async def create_ab_test(self, test_name: str, control_model_name: str,
                           treatment_model_names: List[str],
                           success_metrics: List[MetricType],
                           test_duration_days: int = None) -> Optional[str]:
        """創建A/B測試"""
        
        if not self.config.ab_testing_enabled or not self.ab_test_runner:
            logger.warning("A/B testing is not enabled")
            return None
        
        try:
            # 獲取模型版本ID
            control_version = self.model_registry.get_active_version(control_model_name)
            if not control_version:
                logger.error(f"Control model not found: {control_model_name}")
                return None
            
            treatment_version_ids = []
            for treatment_name in treatment_model_names:
                treatment_version = self.model_registry.get_active_version(treatment_name)
                if not treatment_version:
                    logger.error(f"Treatment model not found: {treatment_name}")
                    return None
                treatment_version_ids.append(treatment_version.version_id)
            
            # 生成測試ID
            test_id = str(uuid.uuid4())
            
            # 生成流量分配（平均分配）
            total_models = 1 + len(treatment_version_ids)
            allocation_per_model = 1.0 / total_models
            
            traffic_allocation = {control_version.version_id: allocation_per_model}
            for treatment_id in treatment_version_ids:
                traffic_allocation[treatment_id] = allocation_per_model
            
            # 創建測試配置
            test_config = ABTestConfig(
                test_id=test_id,
                test_name=test_name,
                test_type=TestType.AB_TEST,
                control_model_id=control_version.version_id,
                treatment_model_ids=treatment_version_ids,
                traffic_allocation=traffic_allocation,
                success_metrics=success_metrics,
                minimum_sample_size=self.config.minimum_sample_size,
                test_duration_days=test_duration_days or self.config.default_test_duration_days
            )
            
            # 創建測試
            if self.ab_test_runner.create_ab_test(test_config):
                self.current_experiments[test_id] = test_config
                self.system_stats['total_experiments_run'] += 1
                await self._save_system_stats()
                
                logger.info(f"A/B test created: {test_name} ({test_id})")
                return test_id
            
            return None
            
        except Exception as e:
            logger.error(f"A/B test creation failed: {e}")
            return None
    
    async def promote_model_to_production(self, version_id: str) -> bool:
        """將模型提升到生產環境"""
        try:
            model_version = self.model_registry.get_model_version(version_id)
            if not model_version:
                logger.error(f"Model version not found: {version_id}")
                return False
            
            # 檢查模型是否已經過充分測試
            if model_version.status not in [ModelStatus.TESTING, ModelStatus.STAGING]:
                logger.error(f"Model must be in testing or staging status, current: {model_version.status}")
                return False
            
            # 獲取當前生產模型（如果存在）
            current_production = self.model_registry.get_active_version(model_version.model_name)
            
            # 將當前生產模型標記為已棄用
            if current_production and current_production.status == ModelStatus.PRODUCTION:
                self.model_registry.update_model_status(current_production.version_id, ModelStatus.DEPRECATED)
            
            # 將新模型設置為生產狀態
            self.model_registry.update_model_status(version_id, ModelStatus.PRODUCTION)
            self.model_registry.set_active_version(model_version.model_name, version_id)
            
            # 記錄進化事件
            evolution_event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': 'model_promotion',
                'model_name': model_version.model_name,
                'old_version': current_production.version_id if current_production else None,
                'new_version': version_id,
                'reason': 'manual_promotion'
            }
            self.evolution_history.append(evolution_event)
            
            self.system_stats['successful_evolutions'] += 1
            await self._save_system_stats()
            
            logger.info(f"Model promoted to production: {model_version.model_name}:{model_version.version_number}")
            return True
            
        except Exception as e:
            logger.error(f"Model promotion failed: {e}")
            return False
    
    async def auto_evolve_models(self) -> Dict[str, Any]:
        """自動進化模型"""
        
        if not self.config.auto_evolution_enabled:
            return {'auto_evolution_disabled': True}
        
        try:
            logger.info("Starting automatic model evolution")
            
            evolution_results = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'models_evaluated': 0,
                'models_evolved': 0,
                'evolution_decisions': []
            }
            
            # 遍歷所有模型
            for model_name, model_info in self.model_registry.models.items():
                active_version_id = model_info.get('active_version')
                if not active_version_id:
                    continue
                
                active_version = self.model_registry.get_model_version(active_version_id)
                if not active_version or active_version.status != ModelStatus.PRODUCTION:
                    continue
                
                evolution_results['models_evaluated'] += 1
                
                # 檢查是否需要進化
                should_evolve, reason = await self._should_model_evolve(active_version)
                
                decision = {
                    'model_name': model_name,
                    'current_version': active_version.version_number,
                    'should_evolve': should_evolve,
                    'reason': reason
                }
                
                if should_evolve:
                    # 執行進化
                    evolution_success = await self._execute_model_evolution(active_version)
                    decision['evolution_success'] = evolution_success
                    
                    if evolution_success:
                        evolution_results['models_evolved'] += 1
                
                evolution_results['evolution_decisions'].append(decision)
            
            logger.info(f"Auto evolution completed: {evolution_results['models_evolved']}/{evolution_results['models_evaluated']} models evolved")
            
            return evolution_results
            
        except Exception as e:
            logger.error(f"Auto evolution failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        try:
            # 註冊表統計
            registry_stats = self.model_registry.get_registry_stats() if self.model_registry else {}
            
            # A/B測試統計
            ab_test_stats = {}
            if self.ab_test_runner:
                active_tests = self.ab_test_runner.get_active_tests()
                ab_test_stats = {
                    'active_tests': len(active_tests),
                    'tests_summary': [
                        {
                            'test_id': test['test_id'],
                            'test_name': test['test_name'],
                            'progress': test['progress'],
                            'status': test['status']
                        }
                        for test in active_tests
                    ]
                }
            
            # 監控統計
            monitoring_stats = {}
            if self.performance_monitor:
                recent_alerts = self.performance_monitor.get_recent_alerts(hours_back=24)
                monitoring_stats = {
                    'monitoring_active': True,
                    'recent_alerts_count': len(recent_alerts),
                    'high_severity_alerts': len([a for a in recent_alerts if a['severity'] == 'high'])
                }
            
            return {
                'system_id': self.config.system_id,
                'system_name': self.config.system_name,
                'is_initialized': self.is_initialized,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'registry_statistics': registry_stats,
                'ab_testing_statistics': ab_test_stats,
                'monitoring_statistics': monitoring_stats,
                'system_statistics': self.system_stats,
                'evolution_history_count': len(self.evolution_history),
                'current_experiments_count': len(self.current_experiments)
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _should_model_evolve(self, model_version: ModelVersion) -> Tuple[bool, str]:
        """判斷模型是否應該進化"""
        
        # 檢查性能退化
        if self.performance_monitor:
            degradation = self.performance_monitor.detect_performance_degradation(model_version.version_id)
            if degradation['degradation_detected']:
                return True, "Performance degradation detected"
        
        # 檢查模型年齡
        model_age = datetime.now(timezone.utc) - model_version.created_at
        if model_age.days > 30:  # 模型超過30天
            return True, "Model age exceeds threshold"
        
        # 檢查是否有更好的候選版本
        all_versions = self.model_registry.list_model_versions(model_version.model_name)
        for version in all_versions:
            if (version.status == ModelStatus.TESTING and
                version.metrics.calculate_composite_score() > 
                model_version.metrics.calculate_composite_score() + self.config.performance_threshold):
                return True, f"Better candidate version available: {version.version_number}"
        
        return False, "No evolution needed"
    
    async def _execute_model_evolution(self, current_version: ModelVersion) -> bool:
        """執行模型進化"""
        try:
            # 尋找最佳候選版本
            all_versions = self.model_registry.list_model_versions(current_version.model_name)
            best_candidate = None
            best_score = current_version.metrics.calculate_composite_score()
            
            for version in all_versions:
                if version.status == ModelStatus.TESTING:
                    candidate_score = version.metrics.calculate_composite_score()
                    if candidate_score > best_score:
                        best_candidate = version
                        best_score = candidate_score
            
            if best_candidate:
                # 提升候選版本到生產環境
                success = await self.promote_model_to_production(best_candidate.version_id)
                
                if success:
                    # 記錄進化事件
                    evolution_event = {
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'event_type': 'auto_evolution',
                        'model_name': current_version.model_name,
                        'old_version': current_version.version_id,
                        'new_version': best_candidate.version_id,
                        'improvement': best_score - current_version.metrics.calculate_composite_score(),
                        'reason': 'performance_improvement'
                    }
                    self.evolution_history.append(evolution_event)
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Model evolution execution failed: {e}")
            return False
    
    def _simulate_model_evaluation(self, metrics: List[MetricType]) -> Dict[str, float]:
        """模擬模型評估（實際應用中應替換為真實評估）"""
        results = {}
        
        for metric in metrics:
            if metric == MetricType.ACCURACY:
                results['accuracy'] = np.random.uniform(0.7, 0.95)
            elif metric == MetricType.PRECISION:
                results['precision'] = np.random.uniform(0.65, 0.9)
            elif metric == MetricType.RECALL:
                results['recall'] = np.random.uniform(0.6, 0.88)
            elif metric == MetricType.F1_SCORE:
                results['f1_score'] = np.random.uniform(0.65, 0.9)
            elif metric == MetricType.AUC:
                results['auc'] = np.random.uniform(0.75, 0.95)
            elif metric == MetricType.RETURN:
                results['return_rate'] = np.random.uniform(-0.05, 0.15)
            elif metric == MetricType.SHARPE_RATIO:
                results['sharpe_ratio'] = np.random.uniform(0.5, 2.5)
            elif metric == MetricType.MAX_DRAWDOWN:
                results['max_drawdown'] = np.random.uniform(0.02, 0.15)
            elif metric == MetricType.WIN_RATE:
                results['win_rate'] = np.random.uniform(0.45, 0.75)
            elif metric == MetricType.VOLATILITY:
                results['volatility'] = np.random.uniform(0.1, 0.4)
        
        # 添加默認指標
        results['prediction_latency'] = np.random.uniform(50, 500)
        results['confidence_score'] = np.random.uniform(0.6, 0.95)
        
        return results
    
    async def _load_system_stats(self):
        """載入系統統計"""
        stats_file = Path(self.config.model_repository_path) / "system_stats.json"
        
        if stats_file.exists():
            try:
                with open(stats_file, 'r', encoding='utf-8') as f:
                    self.system_stats = json.load(f)
                logger.info("System stats loaded")
            except Exception as e:
                logger.warning(f"Failed to load system stats: {e}")
    
    async def _save_system_stats(self):
        """保存系統統計"""
        stats_file = Path(self.config.model_repository_path) / "system_stats.json"
        
        try:
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.system_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save system stats: {e}")
    
    async def cleanup(self):
        """清理資源"""
        try:
            if self.performance_monitor:
                self.performance_monitor.stop_monitoring_service()
            
            # 保存系統統計
            await self._save_system_stats()
            
            logger.info("ModelEvolutionSystem cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# 使用示例和測試函數
async def create_model_evolution_system_example():
    """創建模型進化系統示例"""
    
    # 創建配置
    config = ModelEvolutionConfig(
        system_id="evolution_v1",
        system_name="TradingAgents模型進化系統",
        model_repository_path="./test_model_repository",
        ab_testing_enabled=True,
        monitoring_enabled=True,
        auto_evolution_enabled=True,
        evolution_strategy=EvolutionStrategy.PERFORMANCE_BASED,
        ensemble_enabled=True
    )
    
    # 創建系統
    evolution_system = ModelEvolutionSystem(config)
    
    # 初始化
    success = await evolution_system.initialize()
    
    if success:
        logger.info("模型進化系統創建成功")
        
        # 註冊模型版本
        model1_id = await evolution_system.register_model(
            model_name="alpha_predictor",
            model_config={"model_type": "transformer", "hidden_size": 256},
            model_file_path="./models/alpha_predictor_v1.pt",
            training_data_hash="abc123",
            creator="system",
            description="Alpha預測模型v1"
        )
        
        model2_id = await evolution_system.register_model(
            model_name="alpha_predictor",
            model_config={"model_type": "transformer", "hidden_size": 512},
            model_file_path="./models/alpha_predictor_v2.pt",
            training_data_hash="def456",
            creator="system",
            description="Alpha預測模型v2"
        )
        
        # 評估模型版本
        if model1_id:
            await evolution_system.evaluate_model_version(
                model1_id,
                evaluation_data=None,
                evaluation_metrics=[MetricType.ACCURACY, MetricType.RETURN, MetricType.SHARPE_RATIO]
            )
            
            # 提升到生產環境
            await evolution_system.promote_model_to_production(model1_id)
        
        if model2_id:
            await evolution_system.evaluate_model_version(
                model2_id,
                evaluation_data=None,
                evaluation_metrics=[MetricType.ACCURACY, MetricType.RETURN, MetricType.SHARPE_RATIO]
            )
        
        # 創建A/B測試
        if model1_id and model2_id:
            test_id = await evolution_system.create_ab_test(
                test_name="Alpha預測模型對比測試",
                control_model_name="alpha_predictor",
                treatment_model_names=["alpha_predictor"],
                success_metrics=[MetricType.RETURN, MetricType.SHARPE_RATIO],
                test_duration_days=7
            )
            
            if test_id:
                logger.info(f"A/B test created: {test_id}")
        
        # 模擬監控數據
        if evolution_system.performance_monitor and model1_id:
            # 記錄一些性能指標
            test_metrics = ModelMetrics(
                accuracy=0.85,
                return_rate=0.12,
                sharpe_ratio=1.8,
                prediction_latency=150,
                confidence_score=0.82
            )
            
            evolution_system.performance_monitor.record_prediction_metrics(model1_id, test_metrics)
        
        # 自動進化
        evolution_result = await evolution_system.auto_evolve_models()
        
        # 獲取系統狀態
        system_status = evolution_system.get_system_status()
        
        # 清理資源
        await evolution_system.cleanup()
        
        return {
            'initialization_success': success,
            'registered_models': [model1_id, model2_id],
            'evolution_result': evolution_result,
            'system_status': system_status
        }
    
    return {'initialization_success': False}



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
    # 運行示例
    import asyncio
    
    async def main():
        result = await create_model_evolution_system_example()
        print("=== 模型進化系統測試結果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    asyncio.run(main())