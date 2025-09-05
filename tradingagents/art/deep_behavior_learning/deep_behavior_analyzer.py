#!/usr/bin/env python3
"""
Deep Behavior Analyzer - 深度行為分析器
天工 (TianGong) - 為ART系統提供深度用戶行為分析和洞察

此模組提供：
1. 深度用戶行為特徵提取
2. 多維度行為模式識別
3. 行為趨勢分析和預測
4. 異常行為檢測
5. 個人化洞察生成
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import uuid
import math
import statistics
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA, FastICA
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
import torch
import torch.nn as nn
import torch.optim as optim
from scipy.stats import entropy, zscore
from scipy.signal import find_peaks
import warnings
warnings.filterwarnings('ignore')

class BehaviorDimension(Enum):
    """行為維度"""
    TEMPORAL = "temporal"                    # 時間維度
    FREQUENCY = "frequency"                  # 頻率維度
    MAGNITUDE = "magnitude"                  # 幅度維度
    PATTERN = "pattern"                      # 模式維度
    CONSISTENCY = "consistency"              # 一致性維度
    COMPLEXITY = "complexity"                # 複雜性維度
    ADAPTABILITY = "adaptability"            # 適應性維度
    RATIONALITY = "rationality"              # 理性維度

class AnalysisMethod(Enum):
    """分析方法"""
    STATISTICAL = "statistical"             # 統計分析
    MACHINE_LEARNING = "machine_learning"    # 機器學習
    DEEP_LEARNING = "deep_learning"          # 深度學習
    TIME_SERIES = "time_series"              # 時序分析
    GRAPH_ANALYSIS = "graph_analysis"        # 圖形分析
    CAUSAL_INFERENCE = "causal_inference"    # 因果推斷

@dataclass
class BehaviorMetrics:
    """行為指標"""
    user_id: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    # 基礎行為指標
    action_count: int = 0
    session_duration: float = 0.0
    decision_latency: float = 0.0
    interaction_depth: int = 0
    
    # 交易行為指標
    trade_frequency: float = 0.0
    position_size_variance: float = 0.0
    holding_period_avg: float = 0.0
    profit_loss_ratio: float = 0.0
    win_rate: float = 0.0
    
    # 認知行為指標
    information_processing_speed: float = 0.0
    decision_confidence: float = 0.0
    risk_perception: float = 0.0
    uncertainty_tolerance: float = 0.0
    
    # 情緒行為指標
    emotional_volatility: float = 0.0
    stress_level: float = 0.0
    satisfaction_score: float = 0.0
    regret_tendency: float = 0.0
    
    # 社交行為指標
    social_influence_susceptibility: float = 0.0
    information_sharing_propensity: float = 0.0
    herd_behavior_tendency: float = 0.0
    
    # 學習行為指標
    learning_velocity: float = 0.0
    knowledge_retention: float = 0.0
    skill_adaptation_rate: float = 0.0
    feedback_responsiveness: float = 0.0
    
    # 個人化指標
    preference_stability: float = 0.0
    behavior_consistency: float = 0.0
    adaptation_flexibility: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehaviorInsight:
    """行為洞察"""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    insight_type: str = ""
    title: str = ""
    description: str = ""
    confidence: float = 0.0
    impact_score: float = 0.0
    actionable_recommendations: List[str] = field(default_factory=list)
    supporting_evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    expiry_timestamp: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class BehaviorCluster:
    """行為聚類"""
    cluster_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    cluster_label: str = ""
    user_ids: List[str] = field(default_factory=list)
    centroid: Dict[str, float] = field(default_factory=dict)
    characteristics: Dict[str, Any] = field(default_factory=dict)
    cluster_size: int = 0
    cohesion_score: float = 0.0
    separation_score: float = 0.0
    stability_score: float = 0.0
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())

class BehaviorSequenceEncoder(nn.Module):
    """行為序列編碼器 - 使用LSTM處理時序行為數據"""
    
    def __init__(self, input_size: int, hidden_size: int = 128, num_layers: int = 2):
        super(BehaviorSequenceEncoder, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=0.2)
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=8)
        self.layer_norm = nn.LayerNorm(hidden_size)
        
    def forward(self, x):
        # LSTM處理
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # 自注意力機制
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # 殘差連接和層歸一化
        output = self.layer_norm(lstm_out + attn_out)
        
        return output, hidden

class BehaviorAutoEncoder(nn.Module):
    """行為自編碼器 - 用於特徵降維和異常檢測"""
    
    def __init__(self, input_size: int, encoding_size: int = 64):
        super(BehaviorAutoEncoder, self).__init__()
        
        # 編碼器
        self.encoder = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(), 
            nn.Dropout(0.2),
            nn.Linear(128, encoding_size),
            nn.Tanh()
        )
        
        # 解碼器
        self.decoder = nn.Sequential(
            nn.Linear(encoding_size, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, input_size),
            nn.Sigmoid()
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded, encoded

class DeepBehaviorAnalyzer:
    """深度行為分析器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化組件
        self.scaler = StandardScaler()
        self.min_max_scaler = MinMaxScaler()
        self.pca = PCA(n_components=0.95)  # 保留95%的方差
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        
        # 深度學習模型
        self.sequence_encoder = None
        self.autoencoder = None
        
        # 聚類模型
        self.kmeans = None
        self.dbscan = None
        
        # 行為數據緩存
        self.behavior_cache = defaultdict(deque)
        self.metrics_cache = {}
        self.insight_cache = {}
        
        # 分析配置
        self.analysis_config = {
            'min_data_points': self.config.get('min_data_points', 10),
            'cache_size': self.config.get('cache_size', 1000),
            'insight_expiry_hours': self.config.get('insight_expiry_hours', 24),
            'anomaly_threshold': self.config.get('anomaly_threshold', 0.1),
            'clustering_min_samples': self.config.get('clustering_min_samples', 5)
        }
        
        self.logger.info("DeepBehaviorAnalyzer initialized")

    async def analyze_user_behavior(
        self, 
        user_id: str, 
        behavior_data: List[Dict[str, Any]],
        analysis_methods: List[AnalysisMethod] = None
    ) -> Tuple[BehaviorMetrics, List[BehaviorInsight]]:
        """分析用戶行為"""
        
        if analysis_methods is None:
            analysis_methods = [
                AnalysisMethod.STATISTICAL,
                AnalysisMethod.MACHINE_LEARNING,
                AnalysisMethod.TIME_SERIES
            ]
        
        try:
            # 數據預處理
            processed_data = await self._preprocess_behavior_data(user_id, behavior_data)
            
            # 計算基礎指標
            metrics = await self._calculate_behavior_metrics(user_id, processed_data)
            
            # 生成洞察
            insights = []
            for method in analysis_methods:
                method_insights = await self._generate_insights_by_method(
                    user_id, processed_data, metrics, method
                )
                insights.extend(method_insights)
            
            # 緩存結果
            self.metrics_cache[user_id] = metrics
            self.insight_cache[user_id] = insights
            
            self.logger.info(f"分析用戶 {user_id} 行為完成，生成 {len(insights)} 條洞察")
            
            return metrics, insights
            
        except Exception as e:
            self.logger.error(f"分析用戶行為失敗: {e}")
            return await self._create_default_metrics(user_id), []

    async def _preprocess_behavior_data(
        self, 
        user_id: str, 
        behavior_data: List[Dict[str, Any]]
    ) -> pd.DataFrame:
        """預處理行為數據"""
        
        if not behavior_data:
            return pd.DataFrame()
        
        df = pd.DataFrame(behavior_data)
        
        # 基礎清理
        df = df.dropna()
        df = df.drop_duplicates()
        
        # 時間序列處理
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            
            # 計算時間間隔
            df['time_delta'] = df['timestamp'].diff().dt.total_seconds()
        
        # 數值特徵標準化
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            df[numeric_columns] = self.scaler.fit_transform(df[numeric_columns])
        
        # 添加派生特徵
        df = await self._add_derived_features(df)
        
        return df

    async def _add_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加派生特徵"""
        
        if df.empty:
            return df
        
        # 滾動統計特徵
        for window in [5, 10, 20]:
            if len(df) > window:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if col != 'timestamp':
                        df[f'{col}_rolling_mean_{window}'] = df[col].rolling(window).mean()
                        df[f'{col}_rolling_std_{window}'] = df[col].rolling(window).std()
        
        # 趨勢特徵
        if 'time_delta' in df.columns and len(df) > 2:
            df['trend'] = np.gradient(df.index)
            df['acceleration'] = np.gradient(df['trend'])
        
        return df.fillna(0)

    async def _calculate_behavior_metrics(
        self, 
        user_id: str, 
        processed_data: pd.DataFrame
    ) -> BehaviorMetrics:
        """計算行為指標"""
        
        if processed_data.empty:
            return await self._create_default_metrics(user_id)
        
        metrics = BehaviorMetrics(user_id=user_id)
        
        # 基礎行為指標
        metrics.action_count = len(processed_data)
        
        if 'timestamp' in processed_data.columns:
            time_range = processed_data['timestamp'].max() - processed_data['timestamp'].min()
            metrics.session_duration = time_range.total_seconds()
        
        if 'decision_time' in processed_data.columns:
            metrics.decision_latency = processed_data['decision_time'].mean()
        
        # 交易行為指標（如果有交易數據）
        if 'trade_amount' in processed_data.columns:
            trade_data = processed_data[processed_data['trade_amount'] != 0]
            if not trade_data.empty:
                metrics.trade_frequency = len(trade_data) / max(metrics.session_duration / 86400, 1)  # 每天交易次數
                metrics.position_size_variance = trade_data['trade_amount'].var()
        
        if 'holding_period' in processed_data.columns:
            metrics.holding_period_avg = processed_data['holding_period'].mean()
        
        if 'profit_loss' in processed_data.columns:
            profits = processed_data[processed_data['profit_loss'] > 0]['profit_loss'].sum()
            losses = abs(processed_data[processed_data['profit_loss'] < 0]['profit_loss'].sum())
            if losses > 0:
                metrics.profit_loss_ratio = profits / losses
            
            total_trades = len(processed_data[processed_data['profit_loss'] != 0])
            winning_trades = len(processed_data[processed_data['profit_loss'] > 0])
            if total_trades > 0:
                metrics.win_rate = winning_trades / total_trades
        
        # 認知行為指標
        if 'information_view_time' in processed_data.columns:
            metrics.information_processing_speed = 1.0 / max(processed_data['information_view_time'].mean(), 0.1)
        
        if 'confidence_score' in processed_data.columns:
            metrics.decision_confidence = processed_data['confidence_score'].mean()
        
        # 情緒行為指標
        if 'emotion_score' in processed_data.columns:
            metrics.emotional_volatility = processed_data['emotion_score'].std()
        
        # 學習行為指標
        if len(processed_data) > 1:
            # 計算行為變化速率作為學習速度的代理指標
            behavior_change_rate = processed_data.diff().abs().mean().mean()
            metrics.learning_velocity = behavior_change_rate
        
        # 一致性指標
        numeric_cols = processed_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            consistency_scores = []
            for col in numeric_cols:
                if processed_data[col].std() > 0:
                    consistency_scores.append(1.0 / (1.0 + processed_data[col].std()))
            if consistency_scores:
                metrics.behavior_consistency = np.mean(consistency_scores)
        
        return metrics

    async def _generate_insights_by_method(
        self,
        user_id: str,
        processed_data: pd.DataFrame,
        metrics: BehaviorMetrics,
        method: AnalysisMethod
    ) -> List[BehaviorInsight]:
        """根據分析方法生成洞察"""
        
        insights = []
        
        try:
            if method == AnalysisMethod.STATISTICAL:
                insights.extend(await self._statistical_analysis_insights(user_id, processed_data, metrics))
            
            elif method == AnalysisMethod.MACHINE_LEARNING:
                insights.extend(await self._ml_analysis_insights(user_id, processed_data, metrics))
            
            elif method == AnalysisMethod.TIME_SERIES:
                insights.extend(await self._time_series_insights(user_id, processed_data, metrics))
            
        except Exception as e:
            self.logger.error(f"生成 {method.value} 洞察失敗: {e}")
        
        return insights

    async def _statistical_analysis_insights(
        self, 
        user_id: str, 
        data: pd.DataFrame, 
        metrics: BehaviorMetrics
    ) -> List[BehaviorInsight]:
        """統計分析洞察"""
        
        insights = []
        
        if data.empty:
            return insights
        
        # 異常行為檢測
        try:
            numeric_data = data.select_dtypes(include=[np.number])
            if not numeric_data.empty and len(numeric_data) > 5:
                
                # 使用Z分數檢測異常
                z_scores = np.abs(zscore(numeric_data, nan_policy='omit'))
                anomaly_threshold = 2.5
                anomaly_mask = (z_scores > anomaly_threshold).any(axis=1)
                
                if anomaly_mask.sum() > 0:
                    anomaly_ratio = anomaly_mask.sum() / len(data)
                    insight = BehaviorInsight(
                        user_id=user_id,
                        insight_type="anomaly_detection",
                        title="異常行為檢測",
                        description=f"檢測到 {anomaly_mask.sum()} 次異常行為，佔總行為的 {anomaly_ratio:.1%}",
                        confidence=0.8,
                        impact_score=anomaly_ratio,
                        actionable_recommendations=[
                            "建議檢查異常行為的觸發因素",
                            "考慮調整風險管理策略",
                            "加強行為監控和預警"
                        ],
                        supporting_evidence={
                            "anomaly_count": int(anomaly_mask.sum()),
                            "anomaly_ratio": float(anomaly_ratio),
                            "threshold": anomaly_threshold
                        },
                        tags=["anomaly", "statistical", "risk"]
                    )
                    insights.append(insight)
        
        except Exception as e:
            self.logger.warning(f"異常檢測失敗: {e}")
        
        # 行為穩定性分析
        if metrics.behavior_consistency > 0:
            stability_level = "高" if metrics.behavior_consistency > 0.8 else "中" if metrics.behavior_consistency > 0.5 else "低"
            insight = BehaviorInsight(
                user_id=user_id,
                insight_type="behavior_stability",
                title="行為穩定性分析",
                description=f"用戶行為穩定性為 {stability_level} ({metrics.behavior_consistency:.2f})",
                confidence=0.9,
                impact_score=metrics.behavior_consistency,
                actionable_recommendations=[
                    f"{'維持當前行為模式' if metrics.behavior_consistency > 0.7 else '建議提高行為一致性'}",
                    "定期回顧和調整交易策略",
                    "建立標準化的決策流程"
                ],
                supporting_evidence={
                    "consistency_score": metrics.behavior_consistency,
                    "stability_level": stability_level
                },
                tags=["stability", "consistency", "behavioral"]
            )
            insights.append(insight)
        
        return insights

    async def _ml_analysis_insights(
        self, 
        user_id: str, 
        data: pd.DataFrame, 
        metrics: BehaviorMetrics
    ) -> List[BehaviorInsight]:
        """機器學習分析洞察"""
        
        insights = []
        
        if data.empty or len(data) < self.analysis_config['min_data_points']:
            return insights
        
        # 聚類分析
        try:
            numeric_data = data.select_dtypes(include=[np.number]).dropna()
            
            if len(numeric_data) > 5 and numeric_data.shape[1] > 2:
                # K-means聚類
                optimal_k = min(5, len(numeric_data) // 2)
                kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(numeric_data)
                
                # 計算輪廓係數
                if len(set(cluster_labels)) > 1:
                    silhouette_avg = silhouette_score(numeric_data, cluster_labels)
                    
                    # 分析聚類結果
                    cluster_counts = pd.Series(cluster_labels).value_counts()
                    dominant_cluster = cluster_counts.index[0]
                    dominant_ratio = cluster_counts.iloc[0] / len(cluster_labels)
                    
                    insight = BehaviorInsight(
                        user_id=user_id,
                        insight_type="behavior_clustering",
                        title="行為模式聚類分析",
                        description=f"識別出 {optimal_k} 種行為模式，主要模式佔比 {dominant_ratio:.1%}",
                        confidence=silhouette_avg,
                        impact_score=1 - dominant_ratio,  # 多樣性分數
                        actionable_recommendations=[
                            f"主要行為模式已識別，建議{'多元化行為策略' if dominant_ratio > 0.8 else '保持當前多樣性'}",
                            "針對不同行為模式制定對應策略",
                            "監控行為模式的變化趨勢"
                        ],
                        supporting_evidence={
                            "num_clusters": optimal_k,
                            "silhouette_score": float(silhouette_avg),
                            "dominant_cluster_ratio": float(dominant_ratio),
                            "cluster_distribution": cluster_counts.to_dict()
                        },
                        tags=["clustering", "pattern", "diversity"]
                    )
                    insights.append(insight)
        
        except Exception as e:
            self.logger.warning(f"聚類分析失敗: {e}")
        
        return insights

    async def _time_series_insights(
        self, 
        user_id: str, 
        data: pd.DataFrame, 
        metrics: BehaviorMetrics
    ) -> List[BehaviorInsight]:
        """時序分析洞察"""
        
        insights = []
        
        if data.empty or 'timestamp' not in data.columns:
            return insights
        
        try:
            # 確保時間序列排序
            data_sorted = data.sort_values('timestamp')
            
            # 分析活躍時段
            if len(data_sorted) > 10:
                data_sorted['hour'] = data_sorted['timestamp'].dt.hour
                hourly_activity = data_sorted.groupby('hour').size()
                
                if len(hourly_activity) > 0:
                    peak_hour = hourly_activity.idxmax()
                    peak_activity = hourly_activity.max()
                    total_activity = hourly_activity.sum()
                    concentration_ratio = peak_activity / total_activity
                    
                    insight = BehaviorInsight(
                        user_id=user_id,
                        insight_type="activity_pattern",
                        title="活躍時段分析",
                        description=f"最活躍時段為 {peak_hour}:00，集中度 {concentration_ratio:.1%}",
                        confidence=0.85,
                        impact_score=concentration_ratio,
                        actionable_recommendations=[
                            f"在 {peak_hour}:00 左右安排重要決策",
                            f"{'考慮分散活躍時間' if concentration_ratio > 0.3 else '保持當前時間分布'}",
                            "根據活躍時段優化策略執行"
                        ],
                        supporting_evidence={
                            "peak_hour": int(peak_hour),
                            "concentration_ratio": float(concentration_ratio),
                            "hourly_distribution": hourly_activity.to_dict()
                        },
                        tags=["temporal", "activity", "optimization"]
                    )
                    insights.append(insight)
                    
            # 趨勢分析
            numeric_cols = data_sorted.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col not in ['hour'] and len(data_sorted[col]) > 5:
                    # 簡單線性趨勢
                    x = np.arange(len(data_sorted))
                    y = data_sorted[col].values
                    
                    if np.std(y) > 0:  # 避免常數序列
                        correlation = np.corrcoef(x, y)[0, 1]
                        
                        if abs(correlation) > 0.3:  # 顯著趨勢
                            trend_direction = "上升" if correlation > 0 else "下降"
                            
                            insight = BehaviorInsight(
                                user_id=user_id,
                                insight_type="behavior_trend",
                                title=f"{col} 行為趨勢",
                                description=f"{col} 呈現 {trend_direction} 趨勢，相關性 {abs(correlation):.2f}",
                                confidence=abs(correlation),
                                impact_score=abs(correlation),
                                actionable_recommendations=[
                                    f"關注 {col} 的{trend_direction}趨勢",
                                    "評估趨勢對整體表現的影響",
                                    "考慮調整相關策略參數"
                                ],
                                supporting_evidence={
                                    "metric": col,
                                    "correlation": float(correlation),
                                    "trend_direction": trend_direction
                                },
                                tags=["trend", "temporal", col]
                            )
                            insights.append(insight)
        
        except Exception as e:
            self.logger.warning(f"時序分析失敗: {e}")
        
        return insights

    async def _create_default_metrics(self, user_id: str) -> BehaviorMetrics:
        """創建默認指標"""
        return BehaviorMetrics(user_id=user_id)

    async def detect_behavior_anomalies(
        self, 
        user_id: str, 
        behavior_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測行為異常"""
        
        if not behavior_data:
            return []
        
        try:
            df = pd.DataFrame(behavior_data)
            numeric_data = df.select_dtypes(include=[np.number])
            
            if len(numeric_data) < 5:
                return []
            
            # 使用隔離森林檢測異常
            anomaly_scores = self.isolation_forest.fit_predict(numeric_data)
            
            anomalies = []
            for idx, score in enumerate(anomaly_scores):
                if score == -1:  # 異常點
                    anomaly_info = {
                        'index': idx,
                        'timestamp': behavior_data[idx].get('timestamp', 0),
                        'anomaly_score': float(self.isolation_forest.score_samples([numeric_data.iloc[idx]])[0]),
                        'data': behavior_data[idx]
                    }
                    anomalies.append(anomaly_info)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"異常檢測失敗: {e}")
            return []

    async def cluster_similar_behaviors(
        self, 
        users_behavior_data: Dict[str, List[Dict[str, Any]]]
    ) -> List[BehaviorCluster]:
        """聚類相似行為"""
        
        if not users_behavior_data:
            return []
        
        try:
            # 準備聚類數據
            user_features = []
            user_ids = []
            
            for user_id, behavior_data in users_behavior_data.items():
                if behavior_data:
                    df = pd.DataFrame(behavior_data)
                    numeric_data = df.select_dtypes(include=[np.number])
                    
                    if not numeric_data.empty:
                        # 計算用戶特徵向量（統計摘要）
                        features = {
                            'mean': numeric_data.mean().mean(),
                            'std': numeric_data.std().mean(),
                            'count': len(numeric_data),
                            'skew': numeric_data.skew().mean(),
                            'kurt': numeric_data.kurtosis().mean()
                        }
                        
                        user_features.append(list(features.values()))
                        user_ids.append(user_id)
            
            if len(user_features) < 3:
                return []
            
            # 執行聚類
            features_array = np.array(user_features)
            features_scaled = StandardScaler().fit_transform(features_array)
            
            optimal_k = min(5, len(user_features) // 2)
            kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(features_scaled)
            
            # 構建聚類結果
            clusters = []
            for cluster_id in range(optimal_k):
                cluster_users = [user_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                
                if cluster_users:
                    cluster_features = features_scaled[cluster_labels == cluster_id]
                    centroid = cluster_features.mean(axis=0)
                    
                    # 計算聚類特徵
                    cohesion = 1.0 / (1.0 + np.std(cluster_features))
                    separation = np.linalg.norm(centroid - features_scaled.mean(axis=0))
                    
                    cluster = BehaviorCluster(
                        cluster_label=f"行為群組_{cluster_id + 1}",
                        user_ids=cluster_users,
                        centroid={
                            'mean': float(centroid[0]),
                            'std': float(centroid[1]),
                            'count': float(centroid[2]),
                            'skew': float(centroid[3]),
                            'kurt': float(centroid[4])
                        },
                        cluster_size=len(cluster_users),
                        cohesion_score=float(cohesion),
                        separation_score=float(separation),
                        stability_score=float((cohesion + separation) / 2)
                    )
                    
                    clusters.append(cluster)
            
            return clusters
            
        except Exception as e:
            self.logger.error(f"行為聚類失敗: {e}")
            return []

    def get_user_insights(self, user_id: str) -> List[BehaviorInsight]:
        """獲取用戶洞察"""
        return self.insight_cache.get(user_id, [])

    def get_user_metrics(self, user_id: str) -> Optional[BehaviorMetrics]:
        """獲取用戶指標"""
        return self.metrics_cache.get(user_id)