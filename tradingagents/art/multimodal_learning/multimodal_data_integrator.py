#!/usr/bin/env python3
"""
Multi-modal Data Integrator - 多模態數據整合器
天工 (TianGong) - 統一多種數據模態的整合處理系統

此模組提供：
1. 多種數據模態的統一接入
2. 數據預處理和標準化
3. 模態間的對齊和同步
4. 數據品質評估和過濾
5. 智能數據增強
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import json
import uuid
import time

class DataModality(Enum):
    """數據模態類型"""
    TEXT = "text"                          # 文本數據（新聞、財報、評論）
    NUMERICAL = "numerical"                # 數值數據（價格、成交量）
    TIME_SERIES = "time_series"           # 時間序列數據
    CATEGORICAL = "categorical"           # 分類數據（行業、評級）
    FINANCIAL_RATIOS = "financial_ratios" # 財務比率
    MARKET_DATA = "market_data"           # 市場數據（技術指標）
    NEWS_SENTIMENT = "news_sentiment"     # 新聞情感分析
    SOCIAL_MEDIA = "social_media"         # 社群媒體數據
    INSTITUTIONAL = "institutional"       # 法人數據
    TECHNICAL_INDICATORS = "technical_indicators" # 技術指標

class IntegrationStrategy(Enum):
    """整合策略"""
    EARLY_FUSION = "early_fusion"         # 早期融合
    LATE_FUSION = "late_fusion"           # 後期融合
    HYBRID_FUSION = "hybrid_fusion"       # 混合融合
    ADAPTIVE_FUSION = "adaptive_fusion"   # 自適應融合

@dataclass
class ModalityData:
    """單一模態數據包裝"""
    modality: DataModality
    data: Any
    timestamp: float
    source: str
    quality_score: float = 0.0
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.timestamp == 0:
            self.timestamp = time.time()

@dataclass 
class ModalityWeights:
    """模態權重配置"""
    weights: Dict[DataModality, float] = field(default_factory=dict)
    adaptive_weights: bool = True
    weight_decay: float = 0.95
    min_weight: float = 0.1
    max_weight: float = 1.0
    
    def normalize_weights(self):
        """標準化權重"""
        if not self.weights:
            return
            
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}

@dataclass
class IntegrationResult:
    """整合結果"""
    integration_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    integrated_features: Dict[str, Any] = field(default_factory=dict)
    modality_contributions: Dict[DataModality, float] = field(default_factory=dict)
    integration_quality: float = 0.0
    alignment_success: bool = True
    processing_time: float = 0.0
    error_messages: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

class MultiModalDataIntegrator:
    """多模態數據整合器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 整合策略配置
        self.integration_strategy = IntegrationStrategy(
            self.config.get('integration_strategy', 'hybrid_fusion')
        )
        
        # 模態權重管理
        self.modality_weights = ModalityWeights()
        if 'modality_weights' in self.config:
            self.modality_weights.weights = self.config['modality_weights']
            self.modality_weights.normalize_weights()
        
        # 數據緩存和管理
        self.modality_buffers: Dict[DataModality, deque] = defaultdict(
            lambda: deque(maxlen=self.config.get('buffer_size', 1000))
        )
        self.integration_history: List[IntegrationResult] = []
        
        # 數據品質管理
        self.quality_thresholds = {
            DataModality.TEXT: 0.7,
            DataModality.NUMERICAL: 0.9,
            DataModality.TIME_SERIES: 0.8,
            DataModality.FINANCIAL_RATIOS: 0.85,
            DataModality.NEWS_SENTIMENT: 0.75
        }
        self.quality_thresholds.update(
            self.config.get('quality_thresholds', {})
        )
        
        # 對齊和同步配置
        self.temporal_window = self.config.get('temporal_window', 3600)  # 秒
        self.max_lag_tolerance = self.config.get('max_lag_tolerance', 1800)  # 秒
        
        # 性能配置
        self.max_integration_time = self.config.get('max_integration_time', 30)  # 秒
        self.cache_enabled = self.config.get('cache_enabled', True)
        self.cache_ttl = self.config.get('cache_ttl', 300)  # 秒
        
        self.logger.info("MultiModalDataIntegrator initialized")
    
    async def add_modality_data(
        self, 
        modality: DataModality,
        data: Any,
        source: str = "unknown",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """添加單一模態數據"""
        try:
            # 數據品質檢查
            quality_score = await self._assess_data_quality(modality, data)
            
            if quality_score < self.quality_thresholds.get(modality, 0.5):
                self.logger.warning(f"數據品質不符標準: {modality.value}, 分數: {quality_score}")
                return False
            
            # 創建模態數據對象
            modality_data = ModalityData(
                modality=modality,
                data=data,
                timestamp=time.time(),
                source=source,
                quality_score=quality_score,
                metadata=metadata or {}
            )
            
            # 添加到緩衝區
            self.modality_buffers[modality].append(modality_data)
            
            # 更新模態權重（如果啟用自適應）
            if self.modality_weights.adaptive_weights:
                await self._update_adaptive_weights(modality, quality_score)
            
            self.logger.debug(f"已添加 {modality.value} 數據，品質分數: {quality_score}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加模態數據失敗: {e}")
            return False
    
    async def integrate_multimodal_data(
        self,
        target_modalities: List[DataModality] = None,
        time_window: float = None
    ) -> IntegrationResult:
        """整合多模態數據"""
        start_time = time.time()
        result = IntegrationResult()
        
        try:
            # 確定要整合的模態
            if target_modalities is None:
                target_modalities = list(self.modality_buffers.keys())
            
            # 設定時間窗口
            window = time_window or self.temporal_window
            current_time = time.time()
            window_start = current_time - window
            
            # 收集時間窗口內的數據
            aligned_data = await self._collect_aligned_data(
                target_modalities, window_start, current_time
            )
            
            if not aligned_data:
                result.error_messages.append("沒有可用於整合的對齊數據")
                return result
            
            # 執行數據整合
            integration_success = await self._perform_integration(aligned_data, result)
            
            if integration_success:
                # 計算整合品質
                result.integration_quality = await self._calculate_integration_quality(
                    aligned_data, result
                )
                
                # 更新模態貢獻度
                await self._calculate_modality_contributions(aligned_data, result)
                
                result.alignment_success = True
                self.logger.info(f"多模態數據整合成功，品質分數: {result.integration_quality}")
            else:
                result.error_messages.append("數據整合過程失敗")
            
        except Exception as e:
            self.logger.error(f"多模態數據整合失敗: {e}")
            result.error_messages.append(str(e))
            result.alignment_success = False
        
        finally:
            result.processing_time = time.time() - start_time
            self.integration_history.append(result)
            
            # 保持歷史記錄在合理範圍內
            if len(self.integration_history) > 100:
                self.integration_history = self.integration_history[-50:]
        
        return result
    
    async def _assess_data_quality(self, modality: DataModality, data: Any) -> float:
        """評估數據品質"""
        try:
            if modality == DataModality.TEXT:
                return await self._assess_text_quality(data)
            elif modality == DataModality.NUMERICAL:
                return await self._assess_numerical_quality(data)
            elif modality == DataModality.TIME_SERIES:
                return await self._assess_timeseries_quality(data)
            else:
                # 默認品質評估
                if data is None:
                    return 0.0
                if isinstance(data, (list, dict, pd.DataFrame)) and len(data) == 0:
                    return 0.0
                return 0.8  # 默認品質分數
                
        except Exception as e:
            self.logger.warning(f"品質評估失敗: {e}")
            return 0.5
    
    async def _assess_text_quality(self, text_data: Any) -> float:
        """評估文本數據品質"""
        if not isinstance(text_data, str):
            return 0.0
        
        text = text_data.strip()
        if len(text) == 0:
            return 0.0
        
        quality_score = 0.0
        
        # 長度檢查
        if len(text) >= 10:
            quality_score += 0.3
        
        # 編碼檢查
        try:
            text.encode('utf-8')
            quality_score += 0.2
        except UnicodeEncodeError:
            pass
        
        # 內容豐富度檢查
        unique_chars = len(set(text.lower()))
        if unique_chars >= 10:
            quality_score += 0.3
        
        # 格式檢查（不全是特殊字符）
        alphanumeric_ratio = sum(c.isalnum() for c in text) / len(text)
        if alphanumeric_ratio >= 0.5:
            quality_score += 0.2
        
        return min(quality_score, 1.0)
    
    async def _assess_numerical_quality(self, numerical_data: Any) -> float:
        """評估數值數據品質"""
        try:
            if isinstance(numerical_data, (int, float)):
                return 1.0 if not np.isnan(numerical_data) and np.isfinite(numerical_data) else 0.0
            
            if isinstance(numerical_data, (list, np.ndarray)):
                arr = np.array(numerical_data)
                if len(arr) == 0:
                    return 0.0
                
                # 檢查NaN和infinite值
                valid_ratio = np.sum(np.isfinite(arr)) / len(arr)
                return float(valid_ratio)
            
            if isinstance(numerical_data, pd.DataFrame):
                total_cells = numerical_data.size
                if total_cells == 0:
                    return 0.0
                
                valid_cells = numerical_data.count().sum()
                return float(valid_cells / total_cells)
            
            return 0.5  # 未知格式，給予中等分數
            
        except Exception:
            return 0.0
    
    async def _assess_timeseries_quality(self, timeseries_data: Any) -> float:
        """評估時間序列數據品質"""
        try:
            if isinstance(timeseries_data, pd.DataFrame):
                df = timeseries_data
            elif isinstance(timeseries_data, list):
                df = pd.DataFrame(timeseries_data)
            else:
                return 0.0
            
            if df.empty:
                return 0.0
            
            quality_score = 0.0
            
            # 數據完整性
            completeness = df.count().sum() / df.size
            quality_score += completeness * 0.4
            
            # 時間序列連續性（如果有時間戳）
            if 'timestamp' in df.columns or 'date' in df.columns:
                time_col = 'timestamp' if 'timestamp' in df.columns else 'date'
                try:
                    time_series = pd.to_datetime(df[time_col])
                    gaps = (time_series.diff().dt.total_seconds() > 86400).sum()  # 超過1天的間隔
                    continuity = max(0, 1 - gaps / len(time_series))
                    quality_score += continuity * 0.3
                except:
                    quality_score += 0.15  # 部分分數
            else:
                quality_score += 0.15
            
            # 數據變異性
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                variance_scores = []
                for col in numeric_cols:
                    if df[col].std() > 0:
                        variance_scores.append(1.0)
                    else:
                        variance_scores.append(0.0)
                
                if variance_scores:
                    quality_score += np.mean(variance_scores) * 0.3
            
            return min(quality_score, 1.0)
            
        except Exception:
            return 0.0
    
    async def _collect_aligned_data(
        self,
        modalities: List[DataModality],
        window_start: float,
        window_end: float
    ) -> Dict[DataModality, List[ModalityData]]:
        """收集時間窗口內的對齊數據"""
        aligned_data = {}
        
        for modality in modalities:
            if modality not in self.modality_buffers:
                continue
            
            # 收集時間窗口內的數據
            modality_data = []
            for data_point in self.modality_buffers[modality]:
                if window_start <= data_point.timestamp <= window_end:
                    modality_data.append(data_point)
            
            if modality_data:
                aligned_data[modality] = modality_data
        
        return aligned_data
    
    async def _perform_integration(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ) -> bool:
        """執行數據整合"""
        try:
            if self.integration_strategy == IntegrationStrategy.EARLY_FUSION:
                return await self._early_fusion(aligned_data, result)
            elif self.integration_strategy == IntegrationStrategy.LATE_FUSION:
                return await self._late_fusion(aligned_data, result)
            elif self.integration_strategy == IntegrationStrategy.HYBRID_FUSION:
                return await self._hybrid_fusion(aligned_data, result)
            else:  # ADAPTIVE_FUSION
                return await self._adaptive_fusion(aligned_data, result)
                
        except Exception as e:
            self.logger.error(f"數據整合執行失敗: {e}")
            return False
    
    async def _early_fusion(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ) -> bool:
        """早期融合：在特徵級別進行融合"""
        try:
            integrated_features = {}
            
            for modality, data_list in aligned_data.items():
                # 提取該模態的特徵
                modality_features = await self._extract_modality_features(modality, data_list)
                
                # 加權融合到整合特徵中
                weight = self.modality_weights.weights.get(modality, 1.0)
                
                for feature_name, feature_value in modality_features.items():
                    if feature_name not in integrated_features:
                        integrated_features[feature_name] = 0.0
                    
                    integrated_features[feature_name] += feature_value * weight
            
            result.integrated_features = integrated_features
            return True
            
        except Exception as e:
            self.logger.error(f"早期融合失敗: {e}")
            return False
    
    async def _late_fusion(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ) -> bool:
        """後期融合：在決策級別進行融合"""
        try:
            modality_decisions = {}
            
            # 為每個模態生成獨立決策
            for modality, data_list in aligned_data.items():
                modality_decision = await self._generate_modality_decision(modality, data_list)
                modality_decisions[modality.value] = modality_decision
                
                weight = self.modality_weights.weights.get(modality, 1.0)
                modality_decisions[f"{modality.value}_weight"] = weight
            
            # 加權組合決策
            final_decision = await self._combine_modality_decisions(modality_decisions)
            
            result.integrated_features = {
                'modality_decisions': modality_decisions,
                'final_decision': final_decision
            }
            return True
            
        except Exception as e:
            self.logger.error(f"後期融合失敗: {e}")
            return False
    
    async def _hybrid_fusion(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ) -> bool:
        """混合融合：結合早期和後期融合"""
        try:
            # 執行早期融合
            early_result = IntegrationResult()
            early_success = await self._early_fusion(aligned_data, early_result)
            
            # 執行後期融合
            late_result = IntegrationResult()
            late_success = await self._late_fusion(aligned_data, late_result)
            
            if early_success and late_success:
                # 組合兩種結果
                result.integrated_features = {
                    'early_fusion_features': early_result.integrated_features,
                    'late_fusion_features': late_result.integrated_features,
                    'hybrid_confidence': (early_result.integration_quality + late_result.integration_quality) / 2
                }
                return True
            elif early_success:
                result.integrated_features = early_result.integrated_features
                return True
            elif late_success:
                result.integrated_features = late_result.integrated_features
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"混合融合失敗: {e}")
            return False
    
    async def _adaptive_fusion(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ) -> bool:
        """自適應融合：根據數據品質動態選擇融合策略"""
        try:
            # 評估各模態數據品質
            modality_qualities = {}
            for modality, data_list in aligned_data.items():
                avg_quality = np.mean([data.quality_score for data in data_list])
                modality_qualities[modality] = avg_quality
            
            # 根據品質選擇融合策略
            high_quality_count = sum(1 for q in modality_qualities.values() if q > 0.8)
            
            if high_quality_count >= 3:
                # 多個高品質模態，使用混合融合
                return await self._hybrid_fusion(aligned_data, result)
            elif high_quality_count >= 2:
                # 中等品質，使用早期融合
                return await self._early_fusion(aligned_data, result)
            else:
                # 品質較低，使用後期融合
                return await self._late_fusion(aligned_data, result)
                
        except Exception as e:
            self.logger.error(f"自適應融合失敗: {e}")
            return False
    
    async def _extract_modality_features(
        self,
        modality: DataModality,
        data_list: List[ModalityData]
    ) -> Dict[str, float]:
        """提取特定模態的特徵"""
        features = {}
        
        try:
            if modality == DataModality.TEXT:
                # 文本特徵提取
                all_text = " ".join([str(data.data) for data in data_list])
                features['text_length'] = len(all_text)
                features['text_count'] = len(data_list)
                features['avg_quality'] = np.mean([data.quality_score for data in data_list])
                
            elif modality == DataModality.NUMERICAL:
                # 數值特徵提取
                values = []
                for data in data_list:
                    if isinstance(data.data, (int, float)):
                        values.append(data.data)
                    elif isinstance(data.data, list):
                        values.extend(data.data)
                
                if values:
                    features['numerical_mean'] = np.mean(values)
                    features['numerical_std'] = np.std(values)
                    features['numerical_min'] = np.min(values)
                    features['numerical_max'] = np.max(values)
                    features['numerical_count'] = len(values)
                
            elif modality == DataModality.TIME_SERIES:
                # 時間序列特徵提取
                all_values = []
                for data in data_list:
                    if isinstance(data.data, dict) and 'values' in data.data:
                        all_values.extend(data.data['values'])
                    elif isinstance(data.data, list):
                        all_values.extend(data.data)
                
                if all_values:
                    features['ts_mean'] = np.mean(all_values)
                    features['ts_volatility'] = np.std(all_values)
                    features['ts_trend'] = self._calculate_trend(all_values)
                    features['ts_length'] = len(all_values)
            
            # 通用特徵
            features['modality_weight'] = self.modality_weights.weights.get(modality, 1.0)
            features['data_freshness'] = time.time() - max(data.timestamp for data in data_list)
            
        except Exception as e:
            self.logger.warning(f"特徵提取失敗 {modality.value}: {e}")
        
        return features
    
    def _calculate_trend(self, values: List[float]) -> float:
        """計算趨勢斜率"""
        if len(values) < 2:
            return 0.0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # 計算線性回歸斜率
        slope = np.polyfit(x, y, 1)[0]
        return float(slope)
    
    async def _generate_modality_decision(
        self,
        modality: DataModality,
        data_list: List[ModalityData]
    ) -> Dict[str, Any]:
        """為特定模態生成決策"""
        decision = {
            'modality': modality.value,
            'confidence': 0.5,
            'recommendation': 'neutral',
            'supporting_evidence': []
        }
        
        try:
            if modality == DataModality.NEWS_SENTIMENT:
                # 基於新聞情感的決策
                sentiments = []
                for data in data_list:
                    if isinstance(data.data, dict) and 'sentiment' in data.data:
                        sentiments.append(data.data['sentiment'])
                
                if sentiments:
                    avg_sentiment = np.mean(sentiments)
                    if avg_sentiment > 0.6:
                        decision['recommendation'] = 'positive'
                        decision['confidence'] = min(avg_sentiment, 0.9)
                    elif avg_sentiment < 0.4:
                        decision['recommendation'] = 'negative'
                        decision['confidence'] = min(1 - avg_sentiment, 0.9)
                    
                    decision['supporting_evidence'].append(f"平均情感分數: {avg_sentiment:.2f}")
            
            elif modality == DataModality.TECHNICAL_INDICATORS:
                # 基於技術指標的決策
                signals = []
                for data in data_list:
                    if isinstance(data.data, dict):
                        # 簡單的技術信號評估
                        if 'rsi' in data.data:
                            rsi = data.data['rsi']
                            if rsi > 70:
                                signals.append(-1)  # 超買
                            elif rsi < 30:
                                signals.append(1)   # 超賣
                            else:
                                signals.append(0)
                
                if signals:
                    avg_signal = np.mean(signals)
                    if avg_signal > 0.3:
                        decision['recommendation'] = 'positive'
                        decision['confidence'] = min(abs(avg_signal), 0.8)
                    elif avg_signal < -0.3:
                        decision['recommendation'] = 'negative'
                        decision['confidence'] = min(abs(avg_signal), 0.8)
        
        except Exception as e:
            self.logger.warning(f"模態決策生成失敗 {modality.value}: {e}")
        
        return decision
    
    async def _combine_modality_decisions(
        self,
        modality_decisions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """組合多模態決策"""
        try:
            recommendations = []
            confidences = []
            weights = []
            
            for key, decision in modality_decisions.items():
                if key.endswith('_weight'):
                    continue
                
                if isinstance(decision, dict):
                    rec = decision.get('recommendation', 'neutral')
                    conf = decision.get('confidence', 0.5)
                    weight = modality_decisions.get(f"{key}_weight", 1.0)
                    
                    recommendations.append(rec)
                    confidences.append(conf)
                    weights.append(weight)
            
            # 加權投票
            weighted_scores = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            for rec, conf, weight in zip(recommendations, confidences, weights):
                weighted_scores[rec] += conf * weight
            
            # 最終決策
            final_recommendation = max(weighted_scores.keys(), key=lambda x: weighted_scores[x])
            final_confidence = weighted_scores[final_recommendation] / sum(weights) if weights else 0.5
            
            return {
                'recommendation': final_recommendation,
                'confidence': min(final_confidence, 1.0),
                'modality_count': len(recommendations),
                'weighted_scores': weighted_scores
            }
            
        except Exception as e:
            self.logger.error(f"決策組合失敗: {e}")
            return {'recommendation': 'neutral', 'confidence': 0.5}
    
    async def _update_adaptive_weights(self, modality: DataModality, quality_score: float):
        """更新自適應權重"""
        try:
            current_weight = self.modality_weights.weights.get(modality, 1.0)
            
            # 基於品質分數調整權重
            quality_adjustment = (quality_score - 0.5) * 0.1
            new_weight = current_weight + quality_adjustment
            
            # 應用衰減和限制
            new_weight *= self.modality_weights.weight_decay
            new_weight = max(self.modality_weights.min_weight, 
                           min(new_weight, self.modality_weights.max_weight))
            
            self.modality_weights.weights[modality] = new_weight
            
            # 重新標準化所有權重
            self.modality_weights.normalize_weights()
            
        except Exception as e:
            self.logger.warning(f"自適應權重更新失敗: {e}")
    
    async def _calculate_integration_quality(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ) -> float:
        """計算整合品質分數"""
        try:
            quality_factors = []
            
            # 數據覆蓋度
            coverage = len(aligned_data) / len(DataModality)
            quality_factors.append(coverage)
            
            # 平均數據品質
            all_quality_scores = []
            for data_list in aligned_data.values():
                all_quality_scores.extend([data.quality_score for data in data_list])
            
            if all_quality_scores:
                avg_quality = np.mean(all_quality_scores)
                quality_factors.append(avg_quality)
            
            # 時間對齊品質
            timestamps = []
            for data_list in aligned_data.values():
                timestamps.extend([data.timestamp for data in data_list])
            
            if len(timestamps) > 1:
                time_variance = np.var(timestamps)
                time_quality = max(0, 1 - time_variance / self.temporal_window**2)
                quality_factors.append(time_quality)
            
            # 特徵豐富度
            feature_count = len(result.integrated_features)
            feature_quality = min(feature_count / 10, 1.0)  # 10個特徵為滿分
            quality_factors.append(feature_quality)
            
            return np.mean(quality_factors)
            
        except Exception as e:
            self.logger.warning(f"品質計算失敗: {e}")
            return 0.5
    
    async def _calculate_modality_contributions(
        self,
        aligned_data: Dict[DataModality, List[ModalityData]],
        result: IntegrationResult
    ):
        """計算各模態的貢獻度"""
        try:
            total_data_points = sum(len(data_list) for data_list in aligned_data.values())
            
            for modality, data_list in aligned_data.items():
                # 基於數據量的貢獻
                data_contribution = len(data_list) / total_data_points
                
                # 基於品質的貢獻
                avg_quality = np.mean([data.quality_score for data in data_list])
                quality_contribution = avg_quality
                
                # 基於權重的貢獻
                weight_contribution = self.modality_weights.weights.get(modality, 1.0)
                
                # 綜合貢獻度
                final_contribution = (data_contribution + quality_contribution + weight_contribution) / 3
                result.modality_contributions[modality] = final_contribution
                
        except Exception as e:
            self.logger.warning(f"貢獻度計算失敗: {e}")
    
    def get_integration_statistics(self) -> Dict[str, Any]:
        """獲取整合統計信息"""
        if not self.integration_history:
            return {'total_integrations': 0}
        
        recent_results = self.integration_history[-20:]  # 最近20次整合
        
        return {
            'total_integrations': len(self.integration_history),
            'recent_integrations': len(recent_results),
            'average_quality': np.mean([r.integration_quality for r in recent_results]),
            'average_processing_time': np.mean([r.processing_time for r in recent_results]),
            'success_rate': sum(1 for r in recent_results if r.alignment_success) / len(recent_results),
            'modality_coverage': len(self.modality_buffers),
            'current_weights': dict(self.modality_weights.weights)
        }
    
    def get_modality_status(self) -> Dict[str, Any]:
        """獲取各模態狀態"""
        status = {}
        
        for modality, buffer in self.modality_buffers.items():
            if buffer:
                recent_data = list(buffer)[-10:]  # 最近10個數據點
                avg_quality = np.mean([data.quality_score for data in recent_data])
                last_update = max(data.timestamp for data in recent_data)
                
                status[modality.value] = {
                    'buffer_size': len(buffer),
                    'recent_quality': avg_quality,
                    'last_update': last_update,
                    'staleness': time.time() - last_update,
                    'weight': self.modality_weights.weights.get(modality, 1.0)
                }
        
        return status