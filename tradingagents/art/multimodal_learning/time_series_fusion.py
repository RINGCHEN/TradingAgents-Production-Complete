#!/usr/bin/env python3
"""
Time Series Fusion - 時間序列融合系統
天工 (TianGong) - 多時間序列數據融合和分析系統

此模組提供：
1. 多時間序列數據對齊和同步
2. 時間序列特徵提取和工程
3. 多序列融合算法
4. 時間依賴性建模
5. 預測和異常檢測
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import time
import json
import uuid

# 統計和機器學習
try:
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.decomposition import PCA
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# 時間序列分析
try:
    from scipy import stats, signal
    from scipy.interpolate import interp1d
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

class FusionMethod(Enum):
    """融合方法"""
    SIMPLE_AVERAGE = "simple_average"           # 簡單平均
    WEIGHTED_AVERAGE = "weighted_average"       # 加權平均
    PCA_FUSION = "pca_fusion"                  # PCA融合
    CORRELATION_WEIGHTED = "correlation_weighted" # 相關性加權
    ATTENTION_WEIGHTED = "attention_weighted"    # 注意力加權
    DYNAMIC_TIME_WARPING = "dynamic_time_warping" # 動態時間規整
    KALMAN_FUSION = "kalman_fusion"            # 卡爾曼濾波融合

class TemporalAlignment(Enum):
    """時間對齊方法"""
    FORWARD_FILL = "forward_fill"              # 前向填充
    BACKWARD_FILL = "backward_fill"            # 後向填充
    LINEAR_INTERPOLATION = "linear_interpolation" # 線性插值
    SPLINE_INTERPOLATION = "spline_interpolation" # 樣條插值
    NEAREST_NEIGHBOR = "nearest_neighbor"       # 最近鄰
    TIME_WEIGHTED = "time_weighted"            # 時間加權

@dataclass
class SeriesMetadata:
    """時間序列元數據"""
    series_id: str
    name: str
    frequency: str                    # 'daily', 'hourly', 'minute'
    start_time: datetime
    end_time: datetime
    data_points: int
    missing_ratio: float = 0.0
    quality_score: float = 1.0
    source: str = ""
    
@dataclass
class SeriesPattern:
    """時間序列模式"""
    pattern_type: str                 # 'trend', 'seasonal', 'cyclical'
    strength: float                   # 模式強度 0-1
    period: Optional[int] = None      # 週期長度
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0

@dataclass
class FusionResult:
    """融合結果"""
    fusion_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fused_series: pd.DataFrame
    fusion_method: FusionMethod
    series_weights: Dict[str, float] = field(default_factory=dict)
    alignment_quality: float = 0.0
    fusion_quality: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class TimeSeriesFusion:
    """時間序列融合系統"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 融合配置
        self.default_fusion_method = FusionMethod(
            self.config.get('fusion_method', 'attention_weighted')
        )
        self.default_alignment = TemporalAlignment(
            self.config.get('alignment_method', 'linear_interpolation')
        )
        
        # 數據品質閾值
        self.min_quality_score = self.config.get('min_quality_score', 0.6)
        self.max_missing_ratio = self.config.get('max_missing_ratio', 0.2)
        self.min_overlap_ratio = self.config.get('min_overlap_ratio', 0.5)
        
        # 緩存和存儲
        self.series_cache: Dict[str, pd.DataFrame] = {}
        self.fusion_cache: Dict[str, FusionResult] = {}
        self.pattern_cache: Dict[str, List[SeriesPattern]] = {}
        
        # 處理配置
        self.max_series_length = self.config.get('max_series_length', 10000)
        self.interpolation_limit = self.config.get('interpolation_limit', 10)
        
        # 統計工具
        if SKLEARN_AVAILABLE:
            self.scaler = StandardScaler()
            self.pca = PCA()
        
        self.logger.info("TimeSeriesFusion initialized")
    
    async def add_time_series(
        self,
        series_id: str,
        data: Union[pd.DataFrame, pd.Series, List, np.ndarray],
        metadata: SeriesMetadata = None,
        time_column: str = None
    ) -> bool:
        """添加時間序列數據"""
        try:
            # 數據格式化
            series_df = await self._format_time_series(data, time_column)
            
            if series_df.empty:
                self.logger.warning(f"序列 {series_id} 為空")
                return False
            
            # 數據品質評估
            quality_score = await self._assess_series_quality(series_df)
            
            if quality_score < self.min_quality_score:
                self.logger.warning(f"序列 {series_id} 品質不符要求: {quality_score}")
                return False
            
            # 創建或更新元數據
            if metadata is None:
                metadata = await self._create_series_metadata(series_id, series_df)
            else:
                metadata.quality_score = quality_score
            
            # 數據預處理
            processed_series = await self._preprocess_series(series_df)
            
            # 存儲到緩存
            self.series_cache[series_id] = processed_series
            
            # 提取和緩存模式
            patterns = await self._extract_patterns(processed_series)
            self.pattern_cache[series_id] = patterns
            
            self.logger.info(f"已添加時間序列: {series_id}, 品質分數: {quality_score}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加時間序列失敗 {series_id}: {e}")
            return False
    
    async def fuse_series(
        self,
        series_ids: List[str],
        fusion_method: FusionMethod = None,
        alignment_method: TemporalAlignment = None,
        target_frequency: str = None,
        weights: Dict[str, float] = None
    ) -> FusionResult:
        """融合多個時間序列"""
        start_time = time.time()
        
        if fusion_method is None:
            fusion_method = self.default_fusion_method
        if alignment_method is None:
            alignment_method = self.default_alignment
        
        result = FusionResult(fusion_method=fusion_method)
        
        try:
            # 檢查序列可用性
            available_series = {}
            for series_id in series_ids:
                if series_id in self.series_cache:
                    available_series[series_id] = self.series_cache[series_id]
                else:
                    self.logger.warning(f"序列 {series_id} 不存在")
            
            if len(available_series) < 2:
                raise ValueError("至少需要兩個時間序列進行融合")
            
            # 時間對齊
            aligned_series = await self._align_time_series(
                available_series, alignment_method, target_frequency
            )
            
            # 評估對齊品質
            result.alignment_quality = await self._assess_alignment_quality(aligned_series)
            
            # 計算序列權重
            if weights is None:
                weights = await self._calculate_series_weights(
                    aligned_series, fusion_method
                )
            result.series_weights = weights
            
            # 執行融合
            fused_data = await self._perform_fusion(
                aligned_series, fusion_method, weights
            )
            
            result.fused_series = fused_data
            
            # 評估融合品質
            result.fusion_quality = await self._assess_fusion_quality(
                aligned_series, fused_data
            )
            
            # 添加元數據
            result.metadata = await self._create_fusion_metadata(
                aligned_series, fusion_method
            )
            
            self.logger.info(
                f"時間序列融合完成: {len(available_series)} 個序列, "
                f"融合品質: {result.fusion_quality:.3f}"
            )
            
        except Exception as e:
            self.logger.error(f"時間序列融合失敗: {e}")
            result.fused_series = pd.DataFrame()
            result.fusion_quality = 0.0
            result.metadata['error'] = str(e)
        
        finally:
            result.processing_time = time.time() - start_time
            
            # 緩存結果
            cache_key = "_".join(sorted(series_ids)) + f"_{fusion_method.value}"
            self.fusion_cache[cache_key] = result
        
        return result
    
    async def _format_time_series(
        self,
        data: Union[pd.DataFrame, pd.Series, List, np.ndarray],
        time_column: str = None
    ) -> pd.DataFrame:
        """格式化時間序列數據"""
        try:
            if isinstance(data, pd.DataFrame):
                df = data.copy()
                
                # 確保有時間索引
                if time_column and time_column in df.columns:
                    df.index = pd.to_datetime(df[time_column])
                    df.drop(columns=[time_column], inplace=True)
                elif not isinstance(df.index, pd.DatetimeIndex):
                    # 如果沒有時間索引，創建一個
                    df.index = pd.date_range(
                        start=datetime.now() - timedelta(days=len(df)),
                        periods=len(df),
                        freq='D'
                    )
                
            elif isinstance(data, pd.Series):
                df = data.to_frame()
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.date_range(
                        start=datetime.now() - timedelta(days=len(df)),
                        periods=len(df),
                        freq='D'
                    )
                
            elif isinstance(data, (list, np.ndarray)):
                df = pd.DataFrame({'value': data})
                df.index = pd.date_range(
                    start=datetime.now() - timedelta(days=len(df)),
                    periods=len(df),
                    freq='D'
                )
            else:
                raise ValueError(f"不支援的數據類型: {type(data)}")
            
            # 排序並去重
            df = df.sort_index()
            df = df[~df.index.duplicated(keep='first')]
            
            return df
            
        except Exception as e:
            self.logger.error(f"時間序列格式化失敗: {e}")
            return pd.DataFrame()
    
    async def _assess_series_quality(self, series_df: pd.DataFrame) -> float:
        """評估時間序列品質"""
        try:
            quality_factors = []
            
            # 完整性評估
            total_points = len(series_df)
            missing_points = series_df.isnull().sum().sum()
            completeness = 1 - (missing_points / total_points) if total_points > 0 else 0
            quality_factors.append(completeness)
            
            # 連續性評估
            time_diffs = series_df.index.to_series().diff().dt.total_seconds()
            if len(time_diffs) > 1:
                expected_freq = time_diffs.mode()[0] if not time_diffs.mode().empty else time_diffs.median()
                continuity = (time_diffs == expected_freq).sum() / len(time_diffs)
                quality_factors.append(continuity)
            
            # 變異性評估
            numeric_cols = series_df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                variance_scores = []
                for col in numeric_cols:
                    col_data = series_df[col].dropna()
                    if len(col_data) > 1 and col_data.std() > 0:
                        variance_scores.append(1.0)
                    else:
                        variance_scores.append(0.0)
                
                if variance_scores:
                    quality_factors.append(np.mean(variance_scores))
            
            # 異常值評估
            if len(numeric_cols) > 0:
                outlier_scores = []
                for col in numeric_cols:
                    col_data = series_df[col].dropna()
                    if len(col_data) > 10:
                        Q1 = col_data.quantile(0.25)
                        Q3 = col_data.quantile(0.75)
                        IQR = Q3 - Q1
                        outliers = ((col_data < Q1 - 1.5*IQR) | (col_data > Q3 + 1.5*IQR)).sum()
                        outlier_ratio = outliers / len(col_data)
                        outlier_scores.append(max(0, 1 - outlier_ratio * 2))  # 異常值越少品質越好
                
                if outlier_scores:
                    quality_factors.append(np.mean(outlier_scores))
            
            return np.mean(quality_factors) if quality_factors else 0.5
            
        except Exception as e:
            self.logger.warning(f"品質評估失敗: {e}")
            return 0.5
    
    async def _create_series_metadata(self, series_id: str, series_df: pd.DataFrame) -> SeriesMetadata:
        """創建序列元數據"""
        try:
            time_index = series_df.index
            
            # 推斷頻率
            if len(time_index) > 1:
                time_diff = time_index.to_series().diff().median()
                if time_diff <= pd.Timedelta(minutes=1):
                    frequency = 'minute'
                elif time_diff <= pd.Timedelta(hours=1):
                    frequency = 'hourly'
                else:
                    frequency = 'daily'
            else:
                frequency = 'unknown'
            
            # 計算缺失比例
            missing_ratio = series_df.isnull().sum().sum() / series_df.size
            
            return SeriesMetadata(
                series_id=series_id,
                name=series_id,
                frequency=frequency,
                start_time=time_index.min(),
                end_time=time_index.max(),
                data_points=len(series_df),
                missing_ratio=missing_ratio
            )
            
        except Exception as e:
            self.logger.warning(f"創建元數據失敗: {e}")
            return SeriesMetadata(
                series_id=series_id,
                name=series_id,
                frequency='unknown',
                start_time=datetime.now(),
                end_time=datetime.now(),
                data_points=0
            )
    
    async def _preprocess_series(self, series_df: pd.DataFrame) -> pd.DataFrame:
        """預處理時間序列"""
        try:
            processed_df = series_df.copy()
            
            # 限制序列長度
            if len(processed_df) > self.max_series_length:
                processed_df = processed_df.tail(self.max_series_length)
            
            # 處理缺失值
            numeric_cols = processed_df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                # 使用線性插值，但限制連續缺失值的數量
                processed_df[col] = processed_df[col].interpolate(
                    method='linear',
                    limit=self.interpolation_limit
                )
            
            # 去除異常值（使用IQR方法）
            for col in numeric_cols:
                Q1 = processed_df[col].quantile(0.25)
                Q3 = processed_df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                # 將異常值替換為邊界值
                processed_df[col] = processed_df[col].clip(lower_bound, upper_bound)
            
            return processed_df
            
        except Exception as e:
            self.logger.warning(f"序列預處理失敗: {e}")
            return series_df
    
    async def _extract_patterns(self, series_df: pd.DataFrame) -> List[SeriesPattern]:
        """提取時間序列模式"""
        patterns = []
        
        try:
            numeric_cols = series_df.select_dtypes(include=[np.number]).columns
            
            for col in numeric_cols:
                col_data = series_df[col].dropna()
                
                if len(col_data) < 10:
                    continue
                
                # 趨勢分析
                trend_pattern = await self._detect_trend(col_data)
                if trend_pattern:
                    patterns.append(trend_pattern)
                
                # 季節性分析
                seasonal_pattern = await self._detect_seasonality(col_data)
                if seasonal_pattern:
                    patterns.append(seasonal_pattern)
                
                # 週期性分析
                cyclical_pattern = await self._detect_cyclical(col_data)
                if cyclical_pattern:
                    patterns.append(cyclical_pattern)
        
        except Exception as e:
            self.logger.warning(f"模式提取失敗: {e}")
        
        return patterns
    
    async def _detect_trend(self, data: pd.Series) -> Optional[SeriesPattern]:
        """檢測趨勢"""
        try:
            x = np.arange(len(data))
            y = data.values
            
            # 線性回歸
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            
            # 判斷趨勢強度
            if abs(r_value) > 0.3 and p_value < 0.05:
                trend_type = "upward" if slope > 0 else "downward"
                return SeriesPattern(
                    pattern_type="trend",
                    strength=abs(r_value),
                    parameters={
                        "slope": slope,
                        "direction": trend_type,
                        "r_squared": r_value ** 2
                    },
                    confidence=1 - p_value
                )
        
        except Exception:
            pass
        
        return None
    
    async def _detect_seasonality(self, data: pd.Series) -> Optional[SeriesPattern]:
        """檢測季節性"""
        try:
            if len(data) < 24:  # 需要足夠的數據點
                return None
            
            # 簡單的FFT分析
            if SCIPY_AVAILABLE:
                fft = np.fft.fft(data.values)
                freqs = np.fft.fftfreq(len(data))
                
                # 找到主要頻率
                magnitude = np.abs(fft)
                main_freq_idx = np.argmax(magnitude[1:len(magnitude)//2]) + 1
                main_freq = freqs[main_freq_idx]
                
                if abs(main_freq) > 0:
                    period = int(1 / abs(main_freq))
                    strength = magnitude[main_freq_idx] / np.sum(magnitude)
                    
                    if strength > 0.1 and 2 <= period <= len(data) // 3:
                        return SeriesPattern(
                            pattern_type="seasonal",
                            strength=strength,
                            period=period,
                            parameters={"frequency": main_freq},
                            confidence=strength
                        )
        
        except Exception:
            pass
        
        return None
    
    async def _detect_cyclical(self, data: pd.Series) -> Optional[SeriesPattern]:
        """檢測週期性"""
        try:
            # 自相關函數分析
            if len(data) < 20:
                return None
            
            # 計算自相關
            max_lag = min(len(data) // 4, 50)
            autocorr = [data.autocorr(lag=lag) for lag in range(1, max_lag)]
            
            # 找到最強的自相關
            max_autocorr = max(autocorr)
            max_lag = autocorr.index(max_autocorr) + 1
            
            if max_autocorr > 0.3:
                return SeriesPattern(
                    pattern_type="cyclical",
                    strength=max_autocorr,
                    period=max_lag,
                    parameters={"autocorrelation": max_autocorr},
                    confidence=max_autocorr
                )
        
        except Exception:
            pass
        
        return None
    
    async def _align_time_series(
        self,
        series_dict: Dict[str, pd.DataFrame],
        alignment_method: TemporalAlignment,
        target_frequency: str = None
    ) -> Dict[str, pd.DataFrame]:
        """對齊時間序列"""
        try:
            if not series_dict:
                return {}
            
            # 確定時間範圍
            all_start_times = [df.index.min() for df in series_dict.values()]
            all_end_times = [df.index.max() for df in series_dict.values()]
            
            common_start = max(all_start_times)  # 最晚開始時間
            common_end = min(all_end_times)      # 最早結束時間
            
            if common_start >= common_end:
                raise ValueError("時間序列沒有重疊區間")
            
            # 確定目標頻率
            if target_frequency is None:
                # 使用最高頻率
                frequencies = []
                for df in series_dict.values():
                    if len(df) > 1:
                        freq = df.index.to_series().diff().median()
                        frequencies.append(freq)
                target_freq = min(frequencies) if frequencies else pd.Timedelta(days=1)
            else:
                target_freq = pd.Timedelta(target_frequency)
            
            # 創建目標時間索引
            target_index = pd.date_range(
                start=common_start,
                end=common_end,
                freq=target_freq
            )
            
            # 對齊每個序列
            aligned_series = {}
            for series_id, series_df in series_dict.items():
                aligned_df = await self._align_single_series(
                    series_df, target_index, alignment_method
                )
                aligned_series[series_id] = aligned_df
            
            return aligned_series
            
        except Exception as e:
            self.logger.error(f"時間序列對齊失敗: {e}")
            return series_dict
    
    async def _align_single_series(
        self,
        series_df: pd.DataFrame,
        target_index: pd.DatetimeIndex,
        alignment_method: TemporalAlignment
    ) -> pd.DataFrame:
        """對齊單個時間序列"""
        try:
            # 重新索引到目標時間
            aligned_df = series_df.reindex(target_index)
            
            # 根據對齊方法填充缺失值
            if alignment_method == TemporalAlignment.FORWARD_FILL:
                aligned_df = aligned_df.fillna(method='ffill')
            elif alignment_method == TemporalAlignment.BACKWARD_FILL:
                aligned_df = aligned_df.fillna(method='bfill')
            elif alignment_method == TemporalAlignment.LINEAR_INTERPOLATION:
                aligned_df = aligned_df.interpolate(method='linear')
            elif alignment_method == TemporalAlignment.SPLINE_INTERPOLATION:
                aligned_df = aligned_df.interpolate(method='spline', order=2)
            elif alignment_method == TemporalAlignment.NEAREST_NEIGHBOR:
                aligned_df = aligned_df.interpolate(method='nearest')
            
            return aligned_df
            
        except Exception as e:
            self.logger.warning(f"單序列對齊失敗: {e}")
            return series_df
    
    async def _calculate_series_weights(
        self,
        aligned_series: Dict[str, pd.DataFrame],
        fusion_method: FusionMethod
    ) -> Dict[str, float]:
        """計算序列權重"""
        try:
            if fusion_method == FusionMethod.SIMPLE_AVERAGE:
                # 等權重
                n_series = len(aligned_series)
                return {series_id: 1.0 / n_series for series_id in aligned_series.keys()}
            
            elif fusion_method == FusionMethod.CORRELATION_WEIGHTED:
                # 基於相互相關性的權重
                return await self._calculate_correlation_weights(aligned_series)
            
            elif fusion_method == FusionMethod.ATTENTION_WEIGHTED:
                # 基於注意力機制的權重
                return await self._calculate_attention_weights(aligned_series)
            
            else:
                # 默認等權重
                n_series = len(aligned_series)
                return {series_id: 1.0 / n_series for series_id in aligned_series.keys()}
                
        except Exception as e:
            self.logger.warning(f"權重計算失敗: {e}")
            n_series = len(aligned_series)
            return {series_id: 1.0 / n_series for series_id in aligned_series.keys()}
    
    async def _calculate_correlation_weights(
        self,
        aligned_series: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """基於相關性計算權重"""
        try:
            # 合併所有序列
            combined_df = pd.DataFrame()
            for series_id, series_df in aligned_series.items():
                if len(series_df.columns) == 1:
                    combined_df[series_id] = series_df.iloc[:, 0]
                else:
                    # 如果有多列，取平均
                    combined_df[series_id] = series_df.mean(axis=1)
            
            # 計算相關性矩陣
            corr_matrix = combined_df.corr().abs()
            
            # 基於平均相關性計算權重
            avg_corr = corr_matrix.mean()
            
            # 標準化權重
            total_corr = avg_corr.sum()
            weights = {series_id: float(corr / total_corr) for series_id, corr in avg_corr.items()}
            
            return weights
            
        except Exception as e:
            self.logger.warning(f"相關性權重計算失敗: {e}")
            n_series = len(aligned_series)
            return {series_id: 1.0 / n_series for series_id in aligned_series.keys()}
    
    async def _calculate_attention_weights(
        self,
        aligned_series: Dict[str, pd.DataFrame]
    ) -> Dict[str, float]:
        """基於注意力機制計算權重"""
        try:
            # 計算每個序列的特徵
            series_features = {}
            
            for series_id, series_df in aligned_series.items():
                # 提取統計特徵
                features = {}
                
                for col in series_df.select_dtypes(include=[np.number]).columns:
                    col_data = series_df[col].dropna()
                    if len(col_data) > 0:
                        features[f'{col}_mean'] = col_data.mean()
                        features[f'{col}_std'] = col_data.std()
                        features[f'{col}_skew'] = col_data.skew() if len(col_data) > 2 else 0
                        features[f'{col}_kurt'] = col_data.kurtosis() if len(col_data) > 3 else 0
                
                series_features[series_id] = features
            
            # 基於特徵變異性計算注意力分數
            attention_scores = {}
            
            for series_id, features in series_features.items():
                if features:
                    # 使用特徵的標準差作為注意力分數
                    feature_values = list(features.values())
                    attention_score = np.std(feature_values) if len(feature_values) > 1 else 1.0
                    attention_scores[series_id] = max(attention_score, 0.1)  # 最小分數
                else:
                    attention_scores[series_id] = 0.1
            
            # 軟最大化標準化
            exp_scores = {k: np.exp(v) for k, v in attention_scores.items()}
            total_exp = sum(exp_scores.values())
            
            weights = {k: v / total_exp for k, v in exp_scores.items()}
            
            return weights
            
        except Exception as e:
            self.logger.warning(f"注意力權重計算失敗: {e}")
            n_series = len(aligned_series)
            return {series_id: 1.0 / n_series for series_id in aligned_series.keys()}
    
    async def _perform_fusion(
        self,
        aligned_series: Dict[str, pd.DataFrame],
        fusion_method: FusionMethod,
        weights: Dict[str, float]
    ) -> pd.DataFrame:
        """執行融合操作"""
        try:
            if fusion_method == FusionMethod.SIMPLE_AVERAGE:
                return await self._simple_average_fusion(aligned_series)
            elif fusion_method == FusionMethod.WEIGHTED_AVERAGE:
                return await self._weighted_average_fusion(aligned_series, weights)
            elif fusion_method == FusionMethod.PCA_FUSION:
                return await self._pca_fusion(aligned_series)
            else:
                # 默認使用加權平均
                return await self._weighted_average_fusion(aligned_series, weights)
                
        except Exception as e:
            self.logger.error(f"融合操作失敗: {e}")
            # 返回空DataFrame
            return pd.DataFrame()
    
    async def _simple_average_fusion(
        self,
        aligned_series: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """簡單平均融合"""
        try:
            # 收集所有數值列
            all_data = []
            
            for series_id, series_df in aligned_series.items():
                numeric_cols = series_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    # 如果有多列，取平均
                    if len(numeric_cols) == 1:
                        series_values = series_df[numeric_cols[0]]
                    else:
                        series_values = series_df[numeric_cols].mean(axis=1)
                    
                    all_data.append(series_values)
            
            if all_data:
                # 對齊時間索引
                aligned_data = pd.concat(all_data, axis=1)
                fused_series = aligned_data.mean(axis=1)
                
                return pd.DataFrame({'fused_value': fused_series})
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"簡單平均融合失敗: {e}")
            return pd.DataFrame()
    
    async def _weighted_average_fusion(
        self,
        aligned_series: Dict[str, pd.DataFrame],
        weights: Dict[str, float]
    ) -> pd.DataFrame:
        """加權平均融合"""
        try:
            weighted_data = []
            
            for series_id, series_df in aligned_series.items():
                weight = weights.get(series_id, 1.0)
                numeric_cols = series_df.select_dtypes(include=[np.number]).columns
                
                if len(numeric_cols) > 0:
                    if len(numeric_cols) == 1:
                        series_values = series_df[numeric_cols[0]] * weight
                    else:
                        series_values = series_df[numeric_cols].mean(axis=1) * weight
                    
                    weighted_data.append(series_values)
            
            if weighted_data:
                aligned_data = pd.concat(weighted_data, axis=1)
                fused_series = aligned_data.sum(axis=1)
                
                return pd.DataFrame({'fused_value': fused_series})
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"加權平均融合失敗: {e}")
            return pd.DataFrame()
    
    async def _pca_fusion(
        self,
        aligned_series: Dict[str, pd.DataFrame]
    ) -> pd.DataFrame:
        """PCA融合"""
        try:
            if not SKLEARN_AVAILABLE:
                # 降級到加權平均
                weights = {k: 1.0/len(aligned_series) for k in aligned_series.keys()}
                return await self._weighted_average_fusion(aligned_series, weights)
            
            # 準備數據矩陣
            data_matrix = []
            
            for series_id, series_df in aligned_series.items():
                numeric_cols = series_df.select_dtypes(include=[np.number]).columns
                
                if len(numeric_cols) > 0:
                    if len(numeric_cols) == 1:
                        series_values = series_df[numeric_cols[0]]
                    else:
                        series_values = series_df[numeric_cols].mean(axis=1)
                    
                    data_matrix.append(series_values)
            
            if len(data_matrix) >= 2:
                # 構建數據矩陣
                combined_matrix = pd.concat(data_matrix, axis=1).fillna(0)
                
                # 標準化
                scaler = StandardScaler()
                scaled_data = scaler.fit_transform(combined_matrix)
                
                # PCA
                pca = PCA(n_components=1)
                pca_result = pca.fit_transform(scaled_data)
                
                # 創建結果DataFrame
                result_df = pd.DataFrame(
                    {'fused_value': pca_result.flatten()},
                    index=combined_matrix.index
                )
                
                return result_df
            else:
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"PCA融合失敗: {e}")
            return pd.DataFrame()
    
    async def _assess_alignment_quality(
        self,
        aligned_series: Dict[str, pd.DataFrame]
    ) -> float:
        """評估對齊品質"""
        try:
            quality_scores = []
            
            for series_id, series_df in aligned_series.items():
                # 計算完整性
                completeness = 1 - (series_df.isnull().sum().sum() / series_df.size)
                quality_scores.append(completeness)
            
            # 計算時間索引一致性
            if len(aligned_series) > 1:
                indices = [df.index for df in aligned_series.values()]
                reference_index = indices[0]
                
                consistency_scores = []
                for idx in indices[1:]:
                    consistency = len(reference_index.intersection(idx)) / len(reference_index.union(idx))
                    consistency_scores.append(consistency)
                
                if consistency_scores:
                    quality_scores.append(np.mean(consistency_scores))
            
            return np.mean(quality_scores) if quality_scores else 0.5
            
        except Exception as e:
            self.logger.warning(f"對齊品質評估失敗: {e}")
            return 0.5
    
    async def _assess_fusion_quality(
        self,
        aligned_series: Dict[str, pd.DataFrame],
        fused_data: pd.DataFrame
    ) -> float:
        """評估融合品質"""
        try:
            if fused_data.empty:
                return 0.0
            
            quality_factors = []
            
            # 數據完整性
            completeness = 1 - (fused_data.isnull().sum().sum() / fused_data.size)
            quality_factors.append(completeness)
            
            # 與原序列的相關性
            correlations = []
            fused_values = fused_data.select_dtypes(include=[np.number]).iloc[:, 0]
            
            for series_id, series_df in aligned_series.items():
                numeric_cols = series_df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    original_values = series_df[numeric_cols[0]] if len(numeric_cols) == 1 else series_df[numeric_cols].mean(axis=1)
                    
                    # 對齊長度
                    min_length = min(len(fused_values), len(original_values))
                    if min_length > 1:
                        corr = fused_values[:min_length].corr(original_values[:min_length])
                        if not np.isnan(corr):
                            correlations.append(abs(corr))
            
            if correlations:
                quality_factors.append(np.mean(correlations))
            
            # 平滑性檢查
            if len(fused_values) > 2:
                differences = fused_values.diff().dropna()
                if len(differences) > 0:
                    smoothness = 1 / (1 + differences.std())  # 變化越小越平滑
                    quality_factors.append(smoothness)
            
            return np.mean(quality_factors) if quality_factors else 0.5
            
        except Exception as e:
            self.logger.warning(f"融合品質評估失敗: {e}")
            return 0.5
    
    async def _create_fusion_metadata(
        self,
        aligned_series: Dict[str, pd.DataFrame],
        fusion_method: FusionMethod
    ) -> Dict[str, Any]:
        """創建融合元數據"""
        metadata = {
            'fusion_method': fusion_method.value,
            'input_series_count': len(aligned_series),
            'input_series_ids': list(aligned_series.keys()),
            'creation_timestamp': time.time()
        }
        
        try:
            # 統計信息
            total_data_points = sum(df.size for df in aligned_series.values())
            metadata['total_input_data_points'] = total_data_points
            
            # 時間範圍
            all_start_times = [df.index.min() for df in aligned_series.values() if not df.empty]
            all_end_times = [df.index.max() for df in aligned_series.values() if not df.empty]
            
            if all_start_times and all_end_times:
                metadata['time_range_start'] = min(all_start_times).isoformat()
                metadata['time_range_end'] = max(all_end_times).isoformat()
            
        except Exception as e:
            self.logger.warning(f"創建融合元數據失敗: {e}")
        
        return metadata
    
    def get_fusion_statistics(self) -> Dict[str, Any]:
        """獲取融合統計信息"""
        return {
            'cached_series_count': len(self.series_cache),
            'cached_fusions_count': len(self.fusion_cache),
            'cached_patterns_count': len(self.pattern_cache),
            'available_methods': [method.value for method in FusionMethod],
            'available_alignments': [alignment.value for alignment in TemporalAlignment],
            'sklearn_available': SKLEARN_AVAILABLE,
            'scipy_available': SCIPY_AVAILABLE
        }