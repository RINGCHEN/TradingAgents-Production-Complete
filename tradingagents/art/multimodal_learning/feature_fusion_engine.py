#!/usr/bin/env python3
"""
Feature Fusion Engine - 特徵融合引擎
天工 (TianGong) - 跨模態特徵融合和權重優化系統

此模組提供：
1. 跨模態特徵對齊和標準化
2. 多種特徵融合算法
3. 動態權重優化機制
4. 特徵重要性分析
5. 融合效果評估和調優
"""

from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import time
import json
import uuid

# 機器學習和統計
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
    from sklearn.decomposition import PCA, FastICA
    from sklearn.feature_selection import SelectKBest, mutual_info_regression, f_regression
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.ensemble import RandomForestRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# 高級數值計算
try:
    from scipy.optimize import minimize
    from scipy.stats import pearsonr, spearmanr
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

class FusionAlgorithm(Enum):
    """融合算法類型"""
    WEIGHTED_AVERAGE = "weighted_average"           # 加權平均
    ATTENTION_MECHANISM = "attention_mechanism"     # 注意力機制
    CROSS_MODAL_ATTENTION = "cross_modal_attention" # 跨模態注意力
    MULTIMODAL_TRANSFORMER = "multimodal_transformer" # 多模態Transformer
    ADAPTIVE_FUSION = "adaptive_fusion"             # 自適應融合
    HIERARCHICAL_FUSION = "hierarchical_fusion"     # 階層式融合
    NEURAL_FUSION = "neural_fusion"                # 神經網絡融合
    ENSEMBLE_FUSION = "ensemble_fusion"             # 集成融合

@dataclass
class FeatureGroup:
    """特徵組"""
    group_id: str
    modality: str                      # 所屬模態
    features: Dict[str, np.ndarray]    # 特徵名 -> 特徵值數組
    feature_types: Dict[str, str]      # 特徵名 -> 特徵類型 (numerical, categorical, text)
    normalization_params: Dict[str, Dict] = field(default_factory=dict)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

@dataclass
class FeatureImportance:
    """特徵重要性分析結果"""
    feature_scores: Dict[str, float]   # 特徵名 -> 重要性分數
    modality_scores: Dict[str, float]  # 模態 -> 重要性分數
    interaction_scores: Dict[Tuple[str, str], float] = field(default_factory=dict) # 特徵交互重要性
    method: str = ""
    confidence: float = 0.0

@dataclass
class CrossModalAttention:
    """跨模態注意力結果"""
    attention_matrix: np.ndarray       # 注意力權重矩陣
    modality_attention: Dict[str, float] # 各模態注意力分數
    feature_attention: Dict[str, float]  # 各特徵注意力分數
    entropy: float = 0.0              # 注意力分佈熵

@dataclass
class FusionEngineResult:
    """融合引擎結果"""
    fusion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fused_features: np.ndarray         # 融合後的特徵向量
    feature_names: List[str] = field(default_factory=list)
    fusion_weights: Dict[str, float] = field(default_factory=dict)
    feature_importance: Optional[FeatureImportance] = None
    attention_results: Optional[CrossModalAttention] = None
    fusion_quality: float = 0.0
    processing_time: float = 0.0
    algorithm_used: FusionAlgorithm = FusionAlgorithm.WEIGHTED_AVERAGE
    metadata: Dict[str, Any] = field(default_factory=dict)

class FeatureFusionEngine:
    """特徵融合引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 融合配置
        self.default_algorithm = FusionAlgorithm(
            self.config.get('fusion_algorithm', 'attention_mechanism')
        )
        self.adaptive_weights = self.config.get('adaptive_weights', True)
        self.regularization_strength = self.config.get('regularization_strength', 0.1)
        
        # 特徵處理配置
        self.max_features = self.config.get('max_features', 500)
        self.min_feature_importance = self.config.get('min_feature_importance', 0.01)
        self.feature_selection_ratio = self.config.get('feature_selection_ratio', 0.8)
        
        # 標準化器
        self.scalers: Dict[str, Any] = {}
        self.scaler_type = self.config.get('scaler_type', 'standard')
        
        # 緩存和存儲
        self.feature_cache: Dict[str, FeatureGroup] = {}
        self.fusion_cache: Dict[str, FusionEngineResult] = {}
        self.importance_cache: Dict[str, FeatureImportance] = {}
        
        # 性能配置
        self.batch_size = self.config.get('batch_size', 1000)
        self.max_processing_time = self.config.get('max_processing_time', 60)
        
        # 優化器狀態
        self.optimization_history: List[Dict[str, Any]] = []
        self.weight_optimization_patience = self.config.get('weight_optimization_patience', 10)
        
        self.logger.info("FeatureFusionEngine initialized")
    
    async def add_feature_group(
        self,
        group_id: str,
        modality: str,
        features: Dict[str, Union[np.ndarray, List, pd.Series]],
        feature_types: Dict[str, str] = None
    ) -> bool:
        """添加特徵組"""
        try:
            # 標準化特徵格式
            standardized_features = {}
            for feature_name, feature_data in features.items():
                if isinstance(feature_data, (list, pd.Series)):
                    standardized_features[feature_name] = np.array(feature_data)
                elif isinstance(feature_data, np.ndarray):
                    standardized_features[feature_name] = feature_data
                else:
                    standardized_features[feature_name] = np.array([feature_data])
            
            # 推斷特徵類型
            if feature_types is None:
                feature_types = {}
                for name, data in standardized_features.items():
                    if np.issubdtype(data.dtype, np.number):
                        feature_types[name] = 'numerical'
                    else:
                        feature_types[name] = 'categorical'
            
            # 評估特徵品質
            quality_scores = {}
            for name, data in standardized_features.items():
                quality_scores[name] = await self._assess_feature_quality(data, feature_types[name])
            
            # 創建特徵組
            feature_group = FeatureGroup(
                group_id=group_id,
                modality=modality,
                features=standardized_features,
                feature_types=feature_types,
                quality_scores=quality_scores
            )
            
            # 預處理特徵
            await self._preprocess_feature_group(feature_group)
            
            # 存儲到緩存
            self.feature_cache[group_id] = feature_group
            
            self.logger.info(f"已添加特徵組: {group_id} ({modality}), {len(standardized_features)} 個特徵")
            return True
            
        except Exception as e:
            self.logger.error(f"添加特徵組失敗 {group_id}: {e}")
            return False
    
    async def fuse_features(
        self,
        feature_groups: List[str],
        target_variable: Optional[np.ndarray] = None,
        fusion_algorithm: FusionAlgorithm = None,
        custom_weights: Dict[str, float] = None
    ) -> FusionEngineResult:
        """融合多個特徵組"""
        start_time = time.time()
        
        if fusion_algorithm is None:
            fusion_algorithm = self.default_algorithm
        
        result = FusionEngineResult(algorithm_used=fusion_algorithm)
        
        try:
            # 檢查特徵組可用性
            available_groups = {}
            for group_id in feature_groups:
                if group_id in self.feature_cache:
                    available_groups[group_id] = self.feature_cache[group_id]
                else:
                    self.logger.warning(f"特徵組 {group_id} 不存在")
            
            if len(available_groups) < 2:
                raise ValueError("至少需要兩個特徵組進行融合")
            
            # 特徵對齊和預處理
            aligned_features = await self._align_feature_groups(available_groups)
            
            # 特徵選擇（如果有目標變量）
            if target_variable is not None:
                selected_features = await self._select_important_features(
                    aligned_features, target_variable
                )
                result.feature_importance = selected_features['importance']
            else:
                selected_features = {'features': aligned_features}
            
            # 計算融合權重
            if custom_weights is None:
                fusion_weights = await self._calculate_fusion_weights(
                    selected_features['features'], fusion_algorithm, target_variable
                )
            else:
                fusion_weights = custom_weights
            
            result.fusion_weights = fusion_weights
            
            # 執行特徵融合
            fused_result = await self._perform_feature_fusion(
                selected_features['features'],
                fusion_algorithm,
                fusion_weights,
                target_variable
            )
            
            result.fused_features = fused_result['features']
            result.feature_names = fused_result['names']
            
            # 跨模態注意力分析（如果適用）
            if fusion_algorithm in [FusionAlgorithm.ATTENTION_MECHANISM, FusionAlgorithm.CROSS_MODAL_ATTENTION]:
                result.attention_results = fused_result.get('attention_results')
            
            # 評估融合品質
            result.fusion_quality = await self._assess_fusion_quality(
                selected_features['features'],
                result.fused_features,
                target_variable
            )
            
            self.logger.info(
                f"特徵融合完成: {len(available_groups)} 個組, "
                f"融合品質: {result.fusion_quality:.3f}"
            )
            
        except Exception as e:
            self.logger.error(f"特徵融合失敗: {e}")
            result.fusion_quality = 0.0
            result.metadata['error'] = str(e)
        
        finally:
            result.processing_time = time.time() - start_time
            
            # 緩存結果
            cache_key = "_".join(sorted(feature_groups)) + f"_{fusion_algorithm.value}"
            self.fusion_cache[cache_key] = result
        
        return result
    
    async def _assess_feature_quality(self, feature_data: np.ndarray, feature_type: str) -> float:
        """評估特徵品質"""
        try:
            quality_score = 0.0
            
            # 基本有效性檢查
            if len(feature_data) == 0:
                return 0.0
            
            # 缺失值比例
            if feature_type == 'numerical':
                valid_ratio = np.sum(np.isfinite(feature_data)) / len(feature_data)
                quality_score += valid_ratio * 0.4
                
                # 變異性檢查
                if valid_ratio > 0.5:
                    valid_data = feature_data[np.isfinite(feature_data)]
                    if len(valid_data) > 1 and np.std(valid_data) > 0:
                        quality_score += 0.3
                
                # 分佈檢查
                if len(valid_data) > 10:
                    # 檢查是否過度集中
                    unique_ratio = len(np.unique(valid_data)) / len(valid_data)
                    quality_score += min(unique_ratio, 0.3)
            
            else:  # categorical
                non_null_ratio = np.sum(feature_data != '') / len(feature_data)
                quality_score += non_null_ratio * 0.7
                
                # 類別多樣性
                if non_null_ratio > 0.5:
                    unique_values = len(np.unique(feature_data[feature_data != '']))
                    diversity_score = min(unique_values / len(feature_data), 0.3)
                    quality_score += diversity_score
            
            return min(quality_score, 1.0)
            
        except Exception as e:
            self.logger.warning(f"特徵品質評估失敗: {e}")
            return 0.5
    
    async def _preprocess_feature_group(self, feature_group: FeatureGroup):
        """預處理特徵組"""
        try:
            for feature_name, feature_data in feature_group.features.items():
                feature_type = feature_group.feature_types[feature_name]
                
                if feature_type == 'numerical':
                    # 數值特徵處理
                    processed_data, norm_params = await self._normalize_numerical_feature(
                        feature_data, feature_name
                    )
                    feature_group.features[feature_name] = processed_data
                    feature_group.normalization_params[feature_name] = norm_params
                
                elif feature_type == 'categorical':
                    # 分類特徵處理
                    processed_data = await self._encode_categorical_feature(feature_data)
                    feature_group.features[feature_name] = processed_data
        
        except Exception as e:
            self.logger.warning(f"特徵組預處理失敗: {e}")
    
    async def _normalize_numerical_feature(
        self, 
        feature_data: np.ndarray, 
        feature_name: str
    ) -> Tuple[np.ndarray, Dict]:
        """標準化數值特徵"""
        try:
            # 處理缺失值
            valid_mask = np.isfinite(feature_data)
            valid_data = feature_data[valid_mask]
            
            if len(valid_data) == 0:
                return feature_data, {}
            
            # 選擇標準化方法
            if self.scaler_type == 'standard':
                mean_val = np.mean(valid_data)
                std_val = np.std(valid_data)
                
                if std_val > 0:
                    normalized = (feature_data - mean_val) / std_val
                else:
                    normalized = feature_data - mean_val
                
                norm_params = {'method': 'standard', 'mean': mean_val, 'std': std_val}
                
            elif self.scaler_type == 'minmax':
                min_val = np.min(valid_data)
                max_val = np.max(valid_data)
                
                if max_val > min_val:
                    normalized = (feature_data - min_val) / (max_val - min_val)
                else:
                    normalized = np.zeros_like(feature_data)
                
                norm_params = {'method': 'minmax', 'min': min_val, 'max': max_val}
                
            else:  # robust
                median_val = np.median(valid_data)
                mad = np.median(np.abs(valid_data - median_val))
                
                if mad > 0:
                    normalized = (feature_data - median_val) / mad
                else:
                    normalized = feature_data - median_val
                
                norm_params = {'method': 'robust', 'median': median_val, 'mad': mad}
            
            # 恢復缺失值位置
            normalized[~valid_mask] = feature_data[~valid_mask]
            
            return normalized, norm_params
            
        except Exception as e:
            self.logger.warning(f"數值特徵標準化失敗 {feature_name}: {e}")
            return feature_data, {}
    
    async def _encode_categorical_feature(self, feature_data: np.ndarray) -> np.ndarray:
        """編碼分類特徵"""
        try:
            # 簡單的標籤編碼
            unique_values = np.unique(feature_data)
            value_to_code = {val: i for i, val in enumerate(unique_values)}
            
            encoded = np.array([value_to_code.get(val, -1) for val in feature_data])
            return encoded.astype(float)
            
        except Exception as e:
            self.logger.warning(f"分類特徵編碼失敗: {e}")
            return np.zeros(len(feature_data))
    
    async def _align_feature_groups(
        self, 
        feature_groups: Dict[str, FeatureGroup]
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """對齊特徵組"""
        try:
            aligned_features = {}
            
            # 找到最小的樣本數量
            min_length = min(
                min(len(feature_data) for feature_data in group.features.values())
                for group in feature_groups.values()
            )
            
            # 對齊所有特徵到相同長度
            for group_id, feature_group in feature_groups.items():
                aligned_group = {}
                
                for feature_name, feature_data in feature_group.features.items():
                    # 截取或填充到統一長度
                    if len(feature_data) >= min_length:
                        aligned_data = feature_data[:min_length]
                    else:
                        # 重複填充
                        repeat_times = min_length // len(feature_data)
                        remainder = min_length % len(feature_data)
                        
                        aligned_data = np.concatenate([
                            np.tile(feature_data, repeat_times),
                            feature_data[:remainder]
                        ])
                    
                    full_feature_name = f"{feature_group.modality}_{feature_name}"
                    aligned_group[full_feature_name] = aligned_data
                
                aligned_features[group_id] = aligned_group
            
            return aligned_features
            
        except Exception as e:
            self.logger.error(f"特徵組對齊失敗: {e}")
            return {}
    
    async def _select_important_features(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        target_variable: np.ndarray
    ) -> Dict[str, Any]:
        """選擇重要特徵"""
        try:
            if not SKLEARN_AVAILABLE:
                return {
                    'features': aligned_features,
                    'importance': FeatureImportance(
                        feature_scores={},
                        modality_scores={},
                        method='unavailable'
                    )
                }
            
            # 合併所有特徵
            all_features = {}
            modality_map = {}
            
            for group_id, group_features in aligned_features.items():
                for feature_name, feature_data in group_features.items():
                    all_features[feature_name] = feature_data
                    modality_map[feature_name] = group_id
            
            if not all_features:
                raise ValueError("沒有可用特徵")
            
            # 構建特徵矩陣
            feature_names = list(all_features.keys())
            feature_matrix = np.column_stack([all_features[name] for name in feature_names])
            
            # 對齊目標變量長度
            target_aligned = target_variable[:len(feature_matrix)]
            
            # 特徵選擇
            selector = SelectKBest(
                score_func=mutual_info_regression,
                k=min(int(len(feature_names) * self.feature_selection_ratio), self.max_features)
            )
            
            selected_features_matrix = selector.fit_transform(feature_matrix, target_aligned)
            selected_indices = selector.get_support(indices=True)
            selected_feature_names = [feature_names[i] for i in selected_indices]
            
            # 計算特徵重要性
            feature_scores = dict(zip(feature_names, selector.scores_))
            
            # 計算模態重要性
            modality_scores = defaultdict(float)
            modality_counts = defaultdict(int)
            
            for feature_name, score in feature_scores.items():
                modality = modality_map[feature_name]
                modality_scores[modality] += score
                modality_counts[modality] += 1
            
            # 平均化模態分數
            for modality in modality_scores:
                if modality_counts[modality] > 0:
                    modality_scores[modality] /= modality_counts[modality]
            
            # 重構選定的特徵
            selected_aligned_features = {}
            for group_id in aligned_features.keys():
                selected_aligned_features[group_id] = {}
                
                for i, feature_name in enumerate(selected_feature_names):
                    if modality_map[feature_name] == group_id:
                        original_name = feature_name.replace(f"{group_id}_", "")
                        selected_aligned_features[group_id][original_name] = selected_features_matrix[:, i]
            
            importance = FeatureImportance(
                feature_scores=feature_scores,
                modality_scores=dict(modality_scores),
                method='mutual_info_regression',
                confidence=0.8
            )
            
            return {
                'features': selected_aligned_features,
                'importance': importance
            }
            
        except Exception as e:
            self.logger.warning(f"特徵選擇失敗: {e}")
            return {
                'features': aligned_features,
                'importance': FeatureImportance(
                    feature_scores={},
                    modality_scores={},
                    method='error'
                )
            }
    
    async def _calculate_fusion_weights(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        fusion_algorithm: FusionAlgorithm,
        target_variable: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """計算融合權重"""
        try:
            if fusion_algorithm == FusionAlgorithm.WEIGHTED_AVERAGE:
                # 等權重
                n_groups = len(aligned_features)
                return {group_id: 1.0 / n_groups for group_id in aligned_features.keys()}
            
            elif fusion_algorithm == FusionAlgorithm.ATTENTION_MECHANISM:
                return await self._calculate_attention_weights(aligned_features, target_variable)
            
            elif fusion_algorithm == FusionAlgorithm.ADAPTIVE_FUSION:
                return await self._calculate_adaptive_weights(aligned_features, target_variable)
            
            else:
                # 基於特徵數量的權重
                feature_counts = {
                    group_id: len(group_features) 
                    for group_id, group_features in aligned_features.items()
                }
                total_features = sum(feature_counts.values())
                
                return {
                    group_id: count / total_features 
                    for group_id, count in feature_counts.items()
                }
                
        except Exception as e:
            self.logger.warning(f"權重計算失敗: {e}")
            n_groups = len(aligned_features)
            return {group_id: 1.0 / n_groups for group_id in aligned_features.keys()}
    
    async def _calculate_attention_weights(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        target_variable: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """計算注意力權重"""
        try:
            attention_scores = {}
            
            for group_id, group_features in aligned_features.items():
                # 計算組內特徵的統計特性
                group_stats = []
                
                for feature_name, feature_data in group_features.items():
                    if len(feature_data) > 0:
                        valid_data = feature_data[np.isfinite(feature_data)]
                        if len(valid_data) > 0:
                            stats = {
                                'mean': np.mean(valid_data),
                                'std': np.std(valid_data),
                                'range': np.max(valid_data) - np.min(valid_data),
                                'variance': np.var(valid_data)
                            }
                            group_stats.append(stats)
                
                if group_stats:
                    # 基於變異性計算注意力分數
                    avg_variance = np.mean([stat['variance'] for stat in group_stats])
                    avg_range = np.mean([stat['range'] for stat in group_stats])
                    
                    # 結合變異性和範圍作為注意力指標
                    attention_score = np.log1p(avg_variance) + np.log1p(avg_range)
                    attention_scores[group_id] = max(attention_score, 0.1)
                else:
                    attention_scores[group_id] = 0.1
            
            # 軟最大標準化
            exp_scores = {k: np.exp(v) for k, v in attention_scores.items()}
            total_exp = sum(exp_scores.values())
            
            normalized_weights = {k: v / total_exp for k, v in exp_scores.items()}
            
            return normalized_weights
            
        except Exception as e:
            self.logger.warning(f"注意力權重計算失敗: {e}")
            n_groups = len(aligned_features)
            return {group_id: 1.0 / n_groups for group_id in aligned_features.keys()}
    
    async def _calculate_adaptive_weights(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        target_variable: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """計算自適應權重"""
        try:
            if target_variable is None or not SKLEARN_AVAILABLE:
                # 降級到注意力權重
                return await self._calculate_attention_weights(aligned_features, target_variable)
            
            adaptive_scores = {}
            
            for group_id, group_features in aligned_features.items():
                if not group_features:
                    adaptive_scores[group_id] = 0.1
                    continue
                
                # 構建組特徵矩陣
                feature_matrix = np.column_stack(list(group_features.values()))
                target_aligned = target_variable[:len(feature_matrix)]
                
                # 使用隨機森林評估組的預測能力
                rf = RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=1)
                rf.fit(feature_matrix, target_aligned)
                
                # 計算預測分數
                predictions = rf.predict(feature_matrix)
                r2 = r2_score(target_aligned, predictions)
                
                adaptive_scores[group_id] = max(r2, 0.0) + 0.1  # 確保最小權重
            
            # 標準化權重
            total_score = sum(adaptive_scores.values())
            normalized_weights = {k: v / total_score for k, v in adaptive_scores.items()}
            
            return normalized_weights
            
        except Exception as e:
            self.logger.warning(f"自適應權重計算失敗: {e}")
            n_groups = len(aligned_features)
            return {group_id: 1.0 / n_groups for group_id in aligned_features.keys()}
    
    async def _perform_feature_fusion(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        fusion_algorithm: FusionAlgorithm,
        fusion_weights: Dict[str, float],
        target_variable: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """執行特徵融合"""
        try:
            if fusion_algorithm == FusionAlgorithm.WEIGHTED_AVERAGE:
                return await self._weighted_average_fusion(aligned_features, fusion_weights)
            elif fusion_algorithm == FusionAlgorithm.ATTENTION_MECHANISM:
                return await self._attention_fusion(aligned_features, fusion_weights)
            elif fusion_algorithm == FusionAlgorithm.PCA_FUSION:
                return await self._pca_fusion(aligned_features)
            elif fusion_algorithm == FusionAlgorithm.HIERARCHICAL_FUSION:
                return await self._hierarchical_fusion(aligned_features, fusion_weights)
            else:
                # 默認加權平均
                return await self._weighted_average_fusion(aligned_features, fusion_weights)
                
        except Exception as e:
            self.logger.error(f"特徵融合執行失敗: {e}")
            return {'features': np.array([]), 'names': []}
    
    async def _weighted_average_fusion(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        fusion_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """加權平均融合"""
        try:
            all_weighted_features = []
            feature_names = []
            
            for group_id, group_features in aligned_features.items():
                weight = fusion_weights.get(group_id, 1.0)
                
                for feature_name, feature_data in group_features.items():
                    weighted_feature = feature_data * weight
                    all_weighted_features.append(weighted_feature)
                    feature_names.append(f"{group_id}_{feature_name}")
            
            if all_weighted_features:
                # 堆疊特徵
                fused_matrix = np.column_stack(all_weighted_features)
                
                return {
                    'features': fused_matrix,
                    'names': feature_names
                }
            else:
                return {'features': np.array([]), 'names': []}
                
        except Exception as e:
            self.logger.error(f"加權平均融合失敗: {e}")
            return {'features': np.array([]), 'names': []}
    
    async def _attention_fusion(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        fusion_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """注意力機制融合"""
        try:
            # 收集所有特徵
            all_features = []
            feature_names = []
            group_indices = []
            
            for group_idx, (group_id, group_features) in enumerate(aligned_features.items()):
                for feature_name, feature_data in group_features.items():
                    all_features.append(feature_data)
                    feature_names.append(f"{group_id}_{feature_name}")
                    group_indices.append(group_idx)
            
            if not all_features:
                return {'features': np.array([]), 'names': []}
            
            # 構建特徵矩陣
            feature_matrix = np.column_stack(all_features)
            
            # 計算注意力分數
            attention_scores = []
            
            for i, feature_data in enumerate(all_features):
                # 計算特徵與其他特徵的相關性
                correlations = []
                for j, other_feature in enumerate(all_features):
                    if i != j:
                        if SCIPY_AVAILABLE:
                            corr, _ = pearsonr(feature_data, other_feature)
                            correlations.append(abs(corr) if not np.isnan(corr) else 0)
                        else:
                            corr = np.corrcoef(feature_data, other_feature)[0, 1]
                            correlations.append(abs(corr) if not np.isnan(corr) else 0)
                
                # 注意力分數基於平均相關性
                attention_score = np.mean(correlations) if correlations else 0.0
                attention_scores.append(attention_score)
            
            # 軟最大標準化注意力分數
            attention_weights = np.exp(attention_scores)
            attention_weights = attention_weights / np.sum(attention_weights)
            
            # 應用注意力權重
            weighted_features = feature_matrix * attention_weights.reshape(1, -1)
            
            # 構建注意力結果
            attention_matrix = np.outer(attention_weights, attention_weights)
            
            modality_attention = {}
            for group_id in aligned_features.keys():
                group_mask = [group_indices[i] == list(aligned_features.keys()).index(group_id) 
                             for i in range(len(group_indices))]
                if any(group_mask):
                    modality_attention[group_id] = np.mean(attention_weights[group_mask])
            
            feature_attention = dict(zip(feature_names, attention_weights))
            
            attention_results = CrossModalAttention(
                attention_matrix=attention_matrix,
                modality_attention=modality_attention,
                feature_attention=feature_attention,
                entropy=-np.sum(attention_weights * np.log(attention_weights + 1e-8))
            )
            
            return {
                'features': weighted_features,
                'names': feature_names,
                'attention_results': attention_results
            }
            
        except Exception as e:
            self.logger.error(f"注意力融合失敗: {e}")
            return {'features': np.array([]), 'names': []}
    
    async def _pca_fusion(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]]
    ) -> Dict[str, Any]:
        """PCA融合"""
        try:
            if not SKLEARN_AVAILABLE:
                # 降級到加權平均
                weights = {k: 1.0/len(aligned_features) for k in aligned_features.keys()}
                return await self._weighted_average_fusion(aligned_features, weights)
            
            # 收集所有特徵
            all_features = []
            feature_names = []
            
            for group_id, group_features in aligned_features.items():
                for feature_name, feature_data in group_features.items():
                    all_features.append(feature_data)
                    feature_names.append(f"{group_id}_{feature_name}")
            
            if len(all_features) < 2:
                return {'features': np.array([]), 'names': []}
            
            # 構建特徵矩陣
            feature_matrix = np.column_stack(all_features)
            
            # 標準化
            scaler = StandardScaler()
            scaled_matrix = scaler.fit_transform(feature_matrix)
            
            # PCA
            n_components = min(len(all_features), max(1, int(len(all_features) * 0.8)))
            pca = PCA(n_components=n_components)
            pca_features = pca.fit_transform(scaled_matrix)
            
            # 生成PCA特徵名稱
            pca_names = [f"pca_component_{i}" for i in range(n_components)]
            
            return {
                'features': pca_features,
                'names': pca_names,
                'pca_explained_variance': pca.explained_variance_ratio_
            }
            
        except Exception as e:
            self.logger.error(f"PCA融合失敗: {e}")
            return {'features': np.array([]), 'names': []}
    
    async def _hierarchical_fusion(
        self,
        aligned_features: Dict[str, Dict[str, np.ndarray]],
        fusion_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """階層式融合"""
        try:
            # 第一層：組內融合
            group_representations = {}
            
            for group_id, group_features in aligned_features.items():
                if len(group_features) == 1:
                    # 單一特徵直接使用
                    feature_name, feature_data = next(iter(group_features.items()))
                    group_representations[group_id] = feature_data
                else:
                    # 多特徵組內融合（使用PCA或平均）
                    feature_matrix = np.column_stack(list(group_features.values()))
                    
                    if SKLEARN_AVAILABLE and feature_matrix.shape[1] > 1:
                        # 使用PCA降維
                        pca = PCA(n_components=1)
                        group_rep = pca.fit_transform(feature_matrix).flatten()
                    else:
                        # 使用平均
                        group_rep = np.mean(feature_matrix, axis=1)
                    
                    group_representations[group_id] = group_rep
            
            # 第二層：組間融合
            if len(group_representations) > 1:
                # 加權組合組表示
                weighted_representations = []
                group_names = []
                
                for group_id, group_rep in group_representations.items():
                    weight = fusion_weights.get(group_id, 1.0)
                    weighted_rep = group_rep * weight
                    weighted_representations.append(weighted_rep)
                    group_names.append(f"hierarchical_{group_id}")
                
                # 堆疊組表示
                final_features = np.column_stack(weighted_representations)
                
                return {
                    'features': final_features,
                    'names': group_names
                }
            else:
                # 只有一個組
                group_id, group_rep = next(iter(group_representations.items()))
                return {
                    'features': group_rep.reshape(-1, 1),
                    'names': [f"hierarchical_{group_id}"]
                }
                
        except Exception as e:
            self.logger.error(f"階層式融合失敗: {e}")
            return {'features': np.array([]), 'names': []}
    
    async def _assess_fusion_quality(
        self,
        original_features: Dict[str, Dict[str, np.ndarray]],
        fused_features: np.ndarray,
        target_variable: Optional[np.ndarray] = None
    ) -> float:
        """評估融合品質"""
        try:
            if fused_features.size == 0:
                return 0.0
            
            quality_factors = []
            
            # 1. 維度保留度
            original_dim = sum(len(group) for group in original_features.values())
            fused_dim = fused_features.shape[1] if len(fused_features.shape) > 1 else 1
            
            dimension_retention = min(fused_dim / original_dim, 1.0)
            quality_factors.append(dimension_retention)
            
            # 2. 信息保留度（基於方差）
            if len(fused_features.shape) > 1:
                fused_variance = np.mean(np.var(fused_features, axis=0))
            else:
                fused_variance = np.var(fused_features)
            
            original_variances = []
            for group_features in original_features.values():
                for feature_data in group_features.values():
                    if len(feature_data) > 1:
                        original_variances.append(np.var(feature_data))
            
            if original_variances:
                avg_original_variance = np.mean(original_variances)
                variance_retention = min(fused_variance / avg_original_variance, 1.0) if avg_original_variance > 0 else 0.5
                quality_factors.append(variance_retention)
            
            # 3. 預測能力（如果有目標變量）
            if target_variable is not None and SKLEARN_AVAILABLE:
                try:
                    target_aligned = target_variable[:len(fused_features)]
                    
                    if len(fused_features.shape) == 1:
                        feature_matrix = fused_features.reshape(-1, 1)
                    else:
                        feature_matrix = fused_features
                    
                    # 簡單的線性預測測試
                    from sklearn.linear_model import LinearRegression
                    lr = LinearRegression()
                    lr.fit(feature_matrix, target_aligned)
                    
                    predictions = lr.predict(feature_matrix)
                    r2 = r2_score(target_aligned, predictions)
                    
                    prediction_quality = max(r2, 0.0)
                    quality_factors.append(prediction_quality)
                    
                except Exception:
                    pass  # 忽略預測測試錯誤
            
            return np.mean(quality_factors) if quality_factors else 0.5
            
        except Exception as e:
            self.logger.warning(f"融合品質評估失敗: {e}")
            return 0.5
    
    def get_fusion_statistics(self) -> Dict[str, Any]:
        """獲取融合統計信息"""
        return {
            'cached_feature_groups': len(self.feature_cache),
            'cached_fusions': len(self.fusion_cache),
            'cached_importance_analyses': len(self.importance_cache),
            'available_algorithms': [algo.value for algo in FusionAlgorithm],
            'sklearn_available': SKLEARN_AVAILABLE,
            'scipy_available': SCIPY_AVAILABLE,
            'optimization_history_length': len(self.optimization_history)
        }
    
    def clear_caches(self):
        """清空緩存"""
        self.feature_cache.clear()
        self.fusion_cache.clear()
        self.importance_cache.clear()
        self.optimization_history.clear()
        self.logger.info("特徵融合緩存已清空")