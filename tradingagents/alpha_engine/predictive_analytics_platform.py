#!/usr/bin/env python3
"""
預測性分析平台
Predictive Analytics Platform - GPT-OSS整合任務4.1.2

預測性分析平台是階段4智能化增強的核心組件，通過時序預測模型和多模態融合，
實現高精度的市場預測和風險預警能力。

主要功能：
1. 時序預測模型 - Transformer-based長短期預測
2. 多模態融合 - 文本、圖表、數值數據融合分析
3. 不確定性量化 - 貝葉斯深度學習預測置信區間
4. 實時預警系統 - 毫秒級風險檢測
5. 多時間範圍預測 - 短期、中期、長期預測能力
6. 事件影響預測 - 財報、政策影響評估
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
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Normal, MultivariateNormal
import warnings
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from abc import ABC, abstractmethod
import pickle
from collections import deque, defaultdict
import math

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 忽略警告
warnings.filterwarnings("ignore")


class PredictionHorizon(str, Enum):
    """預測時間範圍枚舉"""
    INTRADAY = "intraday"           # 當日內 (1-6小時)
    SHORT_TERM = "short_term"       # 短期 (1-5日)
    MEDIUM_TERM = "medium_term"     # 中期 (1-4週)
    LONG_TERM = "long_term"         # 長期 (1-6個月)
    STRATEGIC = "strategic"         # 戰略 (6個月以上)


class PredictionType(str, Enum):
    """預測類型枚舉"""
    PRICE = "price"                 # 價格預測
    RETURN = "return"              # 收益率預測
    VOLATILITY = "volatility"       # 波動性預測
    VOLUME = "volume"              # 成交量預測
    TREND = "trend"                # 趋势預測
    REGIME = "regime"              # 市場狀態預測
    RISK = "risk"                  # 風險預測
    EVENT_IMPACT = "event_impact"   # 事件影響預測


class UncertaintyType(str, Enum):
    """不確定性類型枚舉"""
    ALEATORIC = "aleatoric"        # 偶然不確定性（數據噪音）
    EPISTEMIC = "epistemic"        # 認知不確定性（模型不確定性）
    COMBINED = "combined"          # 結合不確定性


class AlertSeverity(str, Enum):
    """預警嚴重程度枚舉"""
    CRITICAL = "critical"          # 緊急
    HIGH = "high"                 # 高
    MEDIUM = "medium"             # 中
    LOW = "low"                   # 低
    INFO = "info"                 # 信息


@dataclass
class TimeSeriesData:
    """時序數據類"""
    timestamps: List[datetime]
    values: np.ndarray
    features: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if len(self.timestamps) != len(self.values):
            raise ValueError("timestamps and values must have the same length")
    
    def to_tensor(self, device: str = 'cpu') -> Tuple[torch.Tensor, torch.Tensor]:
        """轉換為PyTorch張量"""
        values_tensor = torch.FloatTensor(self.values).to(device)
        
        if self.features is not None:
            features_tensor = torch.FloatTensor(self.features).to(device)
            return values_tensor, features_tensor
        
        return values_tensor, None
    
    def get_window(self, start_idx: int, window_size: int) -> 'TimeSeriesData':
        """獲取時間窗口數據"""
        end_idx = start_idx + window_size
        
        return TimeSeriesData(
            timestamps=self.timestamps[start_idx:end_idx],
            values=self.values[start_idx:end_idx],
            features=self.features[start_idx:end_idx] if self.features is not None else None,
            metadata=self.metadata.copy()
        )


@dataclass
class PredictionResult:
    """預測結果類"""
    prediction_id: str
    prediction_type: PredictionType
    horizon: PredictionHorizon
    target_timestamps: List[datetime]
    predictions: np.ndarray
    confidence_intervals: Optional[Tuple[np.ndarray, np.ndarray]]
    uncertainty_estimates: Optional[Dict[UncertaintyType, np.ndarray]]
    feature_importance: Optional[Dict[str, float]]
    model_confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'prediction_id': self.prediction_id,
            'prediction_type': self.prediction_type.value,
            'horizon': self.horizon.value,
            'target_timestamps': [ts.isoformat() for ts in self.target_timestamps],
            'predictions': self.predictions.tolist(),
            'confidence_intervals': [ci.tolist() for ci in self.confidence_intervals] if self.confidence_intervals else None,
            'uncertainty_estimates': {ut.value: ue.tolist() for ut, ue in self.uncertainty_estimates.items()} if self.uncertainty_estimates else None,
            'feature_importance': self.feature_importance,
            'model_confidence': self.model_confidence,
            'metadata': self.metadata
        }


@dataclass
class AlertEvent:
    """預警事件類"""
    alert_id: str
    severity: AlertSeverity
    alert_type: str
    title: str
    description: str
    target_symbol: Optional[str]
    probability: float
    expected_impact: float
    time_horizon: PredictionHorizon
    triggered_at: datetime
    expires_at: Optional[datetime]
    recommendations: List[str]
    supporting_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'alert_id': self.alert_id,
            'severity': self.severity.value,
            'alert_type': self.alert_type,
            'title': self.title,
            'description': self.description,
            'target_symbol': self.target_symbol,
            'probability': self.probability,
            'expected_impact': self.expected_impact,
            'time_horizon': self.time_horizon.value,
            'triggered_at': self.triggered_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'recommendations': self.recommendations,
            'supporting_data': self.supporting_data
        }


class PredictiveAnalyticsConfig(BaseModel):
    """預測性分析平台配置"""
    platform_id: str = Field(..., description="平台ID")
    platform_name: str = Field(..., description="平台名稱")
    
    # 模型配置
    model_type: str = Field("transformer", description="模型類型")
    sequence_length: int = Field(60, description="序列長度")
    prediction_length: int = Field(20, description="預測長度")
    feature_dim: int = Field(10, description="特徵維度")
    hidden_dim: int = Field(256, description="隱藏層維度")
    num_layers: int = Field(6, description="層數")
    num_heads: int = Field(8, description="注意力頭數")
    dropout_rate: float = Field(0.1, description="Dropout率")
    
    # 訓練配置
    learning_rate: float = Field(0.001, description="學習率")
    batch_size: int = Field(32, description="批量大小")
    num_epochs: int = Field(100, description="訓練輪次")
    early_stopping_patience: int = Field(10, description="早停耐心值")
    validation_split: float = Field(0.2, description="驗證集比例")
    
    # 不確定性量化配置
    uncertainty_enabled: bool = Field(True, description="是否啟用不確定性量化")
    monte_carlo_samples: int = Field(100, description="蒙特卡羅採樣次數")
    bayesian_enabled: bool = Field(True, description="是否啟用貝葉斯方法")
    
    # 多模態融合配置
    multimodal_enabled: bool = Field(True, description="是否啟用多模態融合")
    text_feature_dim: int = Field(768, description="文本特徵維度")
    image_feature_dim: int = Field(512, description="圖像特徵維度")
    fusion_method: str = Field("attention", description="融合方法")
    
    # 實時預警配置
    alert_enabled: bool = Field(True, description="是否啟用實時預警")
    alert_threshold: float = Field(0.8, description="預警閾值")
    alert_lookback_hours: int = Field(24, description="預警回望小時數")
    max_alerts_per_hour: int = Field(10, description="每小時最大預警數")
    
    # 性能配置
    device: str = Field("cpu", description="計算設備")
    parallel_processing: bool = Field(True, description="是否啟用並行處理")
    max_concurrent_predictions: int = Field(5, description="最大並發預測數")
    cache_enabled: bool = Field(True, description="是否啟用緩存")
    cache_ttl_minutes: int = Field(30, description="緩存TTL分鐘數")
    
    # 持久化配置
    model_save_path: str = Field("./models/predictive", description="模型保存路徑")
    checkpoint_frequency: int = Field(10, description="檢查點保存頻率")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TransformerPredictor(nn.Module):
    """基於Transformer的時序預測模型"""
    
    def __init__(self, config: PredictiveAnalyticsConfig):
        super(TransformerPredictor, self).__init__()
        
        self.config = config
        
        # 輸入嵌入
        self.input_projection = nn.Linear(config.feature_dim, config.hidden_dim)
        
        # 位置編碼
        self.positional_encoding = self._create_positional_encoding(
            config.sequence_length, config.hidden_dim
        )
        
        # Transformer編碼器層
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=config.hidden_dim,
            nhead=config.num_heads,
            dim_feedforward=config.hidden_dim * 4,
            dropout=config.dropout_rate,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer, 
            num_layers=config.num_layers
        )
        
        # 輸出層
        self.output_projection = nn.Sequential(
            nn.Linear(config.hidden_dim, config.hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate),
            nn.Linear(config.hidden_dim // 2, config.prediction_length)
        )
        
        # 不確定性估計層（如果啟用）
        if config.uncertainty_enabled:
            self.uncertainty_head = nn.Sequential(
                nn.Linear(config.hidden_dim, config.hidden_dim // 2),
                nn.ReLU(),
                nn.Dropout(config.dropout_rate),
                nn.Linear(config.hidden_dim // 2, config.prediction_length),
                nn.Softplus()  # 確保輸出為正
            )
        
        # 多模態融合（如果啟用）
        if config.multimodal_enabled:
            self.text_encoder = nn.Linear(config.text_feature_dim, config.hidden_dim)
            self.image_encoder = nn.Linear(config.image_feature_dim, config.hidden_dim)
            self.fusion_attention = nn.MultiheadAttention(
                config.hidden_dim, config.num_heads, batch_first=True
            )
        
        # 初始化權重
        self._initialize_weights()
        
        logger.info(f"TransformerPredictor initialized with {self._count_parameters()} parameters")
    
    def _create_positional_encoding(self, max_len: int, d_model: int) -> torch.Tensor:
        """創建位置編碼"""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        return pe.unsqueeze(0)  # [1, max_len, d_model]
    
    def _initialize_weights(self):
        """初始化模型權重"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)
    
    def _count_parameters(self) -> int:
        """計算模型參數數量"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def forward(self, x: torch.Tensor, 
                text_features: Optional[torch.Tensor] = None,
                image_features: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """前向傳播"""
        batch_size, seq_len, feature_dim = x.shape
        
        # 輸入嵌入
        x = self.input_projection(x)  # [batch_size, seq_len, hidden_dim]
        
        # 添加位置編碼
        if self.positional_encoding.size(1) >= seq_len:
            pos_encoding = self.positional_encoding[:, :seq_len, :].to(x.device)
            x = x + pos_encoding
        
        # 多模態融合（如果啟用且有額外特徵）
        if (self.config.multimodal_enabled and 
            (text_features is not None or image_features is not None)):
            
            additional_features = []
            
            if text_features is not None:
                text_encoded = self.text_encoder(text_features)  # [batch_size, hidden_dim]
                text_encoded = text_encoded.unsqueeze(1)  # [batch_size, 1, hidden_dim]
                additional_features.append(text_encoded)
            
            if image_features is not None:
                image_encoded = self.image_encoder(image_features)  # [batch_size, hidden_dim]
                image_encoded = image_encoded.unsqueeze(1)  # [batch_size, 1, hidden_dim]
                additional_features.append(image_encoded)
            
            if additional_features:
                # 融合額外特徵
                additional_tensor = torch.cat(additional_features, dim=1)  # [batch_size, n_features, hidden_dim]
                
                # 使用注意力機制融合
                fused_features, _ = self.fusion_attention(x, additional_tensor, additional_tensor)
                x = x + fused_features
        
        # Transformer編碼
        encoded = self.transformer_encoder(x)  # [batch_size, seq_len, hidden_dim]
        
        # 使用最後一個時間步的輸出進行預測
        last_hidden = encoded[:, -1, :]  # [batch_size, hidden_dim]
        
        # 預測輸出
        predictions = self.output_projection(last_hidden)  # [batch_size, prediction_length]
        
        # 不確定性估計（如果啟用）
        uncertainty = None
        if self.config.uncertainty_enabled and hasattr(self, 'uncertainty_head'):
            uncertainty = self.uncertainty_head(last_hidden)  # [batch_size, prediction_length]
        
        return predictions, uncertainty


class BayesianTransformerPredictor(TransformerPredictor):
    """貝葉斯Transformer預測模型"""
    
    def __init__(self, config: PredictiveAnalyticsConfig):
        super().__init__(config)
        
        # 貝葉斯線性層
        self.bayesian_output = nn.ModuleList([
            self._make_bayesian_linear(config.hidden_dim // 2, config.prediction_length)
            for _ in range(config.monte_carlo_samples)
        ])
        
    def _make_bayesian_linear(self, in_features: int, out_features: int) -> nn.Module:
        """創建貝葉斯線性層"""
        return nn.Sequential(
            nn.Linear(in_features, out_features),
            nn.Dropout(0.5)  # 蒙特卡羅Dropout
        )
    
    def monte_carlo_forward(self, x: torch.Tensor, n_samples: int = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """蒙特卡羅前向傳播"""
        if n_samples is None:
            n_samples = self.config.monte_carlo_samples
        
        predictions = []
        
        # 多次前向傳播
        for _ in range(n_samples):
            self.train()  # 啟用Dropout
            with torch.no_grad():
                pred, _ = self.forward(x)
                predictions.append(pred)
        
        predictions = torch.stack(predictions, dim=0)  # [n_samples, batch_size, prediction_length]
        
        # 計算均值和標準差
        mean_pred = predictions.mean(dim=0)
        std_pred = predictions.std(dim=0)
        
        return mean_pred, std_pred


class MultiModalFusionModule(nn.Module):
    """多模態融合模組"""
    
    def __init__(self, config: PredictiveAnalyticsConfig):
        super().__init__()
        
        self.config = config
        
        # 特徵編碼器
        self.numerical_encoder = nn.Sequential(
            nn.Linear(config.feature_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate)
        )
        
        self.text_encoder = nn.Sequential(
            nn.Linear(config.text_feature_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate)
        )
        
        self.image_encoder = nn.Sequential(
            nn.Linear(config.image_feature_dim, config.hidden_dim),
            nn.ReLU(),
            nn.Dropout(config.dropout_rate)
        )
        
        # 融合方法
        if config.fusion_method == "attention":
            self.fusion_layer = nn.MultiheadAttention(
                config.hidden_dim, config.num_heads, batch_first=True
            )
        elif config.fusion_method == "concatenation":
            self.fusion_layer = nn.Linear(config.hidden_dim * 3, config.hidden_dim)
        elif config.fusion_method == "gated":
            self.gate = nn.Sequential(
                nn.Linear(config.hidden_dim * 3, config.hidden_dim),
                nn.Sigmoid()
            )
        
    def forward(self, numerical_features: torch.Tensor,
                text_features: Optional[torch.Tensor] = None,
                image_features: Optional[torch.Tensor] = None) -> torch.Tensor:
        """多模態融合前向傳播"""
        
        # 編碼數值特徵
        encoded_numerical = self.numerical_encoder(numerical_features)
        
        encoded_features = [encoded_numerical]
        
        # 編碼文本特徵
        if text_features is not None:
            encoded_text = self.text_encoder(text_features)
            encoded_features.append(encoded_text)
        
        # 編碼圖像特徵
        if image_features is not None:
            encoded_image = self.image_encoder(image_features)
            encoded_features.append(encoded_image)
        
        # 融合特徵
        if self.config.fusion_method == "attention":
            # 使用注意力機制融合
            stacked_features = torch.stack(encoded_features, dim=1)  # [batch, n_modalities, hidden_dim]
            fused_features, _ = self.fusion_layer(
                stacked_features, stacked_features, stacked_features
            )
            return fused_features.mean(dim=1)  # 平均池化
            
        elif self.config.fusion_method == "concatenation":
            # 連接融合
            concatenated = torch.cat(encoded_features, dim=-1)
            return self.fusion_layer(concatenated)
            
        elif self.config.fusion_method == "gated":
            # 門控融合
            concatenated = torch.cat(encoded_features, dim=-1)
            gate_weights = self.gate(concatenated)
            return gate_weights * encoded_numerical
        
        return encoded_numerical


class RiskAlertSystem:
    """風險預警系統"""
    
    def __init__(self, config: PredictiveAnalyticsConfig):
        self.config = config
        self.alert_history = deque(maxlen=1000)
        self.alert_counters = defaultdict(int)
        self.last_alert_times = defaultdict(lambda: datetime.min.replace(tzinfo=timezone.utc))
        
    def evaluate_alerts(self, prediction_result: PredictionResult,
                       market_data: Dict[str, Any]) -> List[AlertEvent]:
        """評估預警事件"""
        alerts = []
        current_time = datetime.now(timezone.utc)
        
        try:
            # 檢查預測置信度
            if prediction_result.model_confidence < self.config.alert_threshold:
                return alerts
            
            # 價格異常預警
            price_alerts = self._check_price_anomalies(prediction_result, market_data, current_time)
            alerts.extend(price_alerts)
            
            # 波動性預警
            volatility_alerts = self._check_volatility_spikes(prediction_result, market_data, current_time)
            alerts.extend(volatility_alerts)
            
            # 趨勢轉折預警
            trend_alerts = self._check_trend_reversals(prediction_result, market_data, current_time)
            alerts.extend(trend_alerts)
            
            # 風險預警
            risk_alerts = self._check_risk_events(prediction_result, market_data, current_time)
            alerts.extend(risk_alerts)
            
            # 過濾重複和頻率限制
            filtered_alerts = self._filter_alerts(alerts, current_time)
            
            # 記錄預警歷史
            for alert in filtered_alerts:
                self.alert_history.append(alert)
            
            return filtered_alerts
            
        except Exception as e:
            logger.error(f"Alert evaluation failed: {e}")
            return []
    
    def _check_price_anomalies(self, prediction_result: PredictionResult,
                              market_data: Dict[str, Any], current_time: datetime) -> List[AlertEvent]:
        """檢查價格異常"""
        alerts = []
        
        if prediction_result.prediction_type != PredictionType.PRICE:
            return alerts
        
        predictions = prediction_result.predictions
        current_price = market_data.get('current_price', 0)
        
        # 計算預測變化幅度
        if len(predictions) > 0 and current_price > 0:
            predicted_change = (predictions[-1] - current_price) / current_price
            
            # 大幅上漲預警
            if predicted_change > 0.1:  # 10%以上上漲
                alert = AlertEvent(
                    alert_id=f"price_surge_{int(current_time.timestamp())}",
                    severity=AlertSeverity.HIGH,
                    alert_type="price_surge",
                    title=f"價格大幅上漲預警",
                    description=f"預測價格將上漲{predicted_change:.1%}",
                    target_symbol=market_data.get('symbol'),
                    probability=prediction_result.model_confidence,
                    expected_impact=abs(predicted_change),
                    time_horizon=prediction_result.horizon,
                    triggered_at=current_time,
                    expires_at=current_time + timedelta(hours=24),
                    recommendations=["考慮獲利了結", "監控成交量變化", "設置止損點"],
                    supporting_data={
                        'predicted_change': predicted_change,
                        'current_price': current_price,
                        'predicted_price': predictions[-1],
                        'confidence': prediction_result.model_confidence
                    }
                )
                alerts.append(alert)
            
            # 大幅下跌預警
            elif predicted_change < -0.1:  # 10%以上下跌
                alert = AlertEvent(
                    alert_id=f"price_drop_{int(current_time.timestamp())}",
                    severity=AlertSeverity.CRITICAL,
                    alert_type="price_drop",
                    title=f"價格大幅下跌預警",
                    description=f"預測價格將下跌{abs(predicted_change):.1%}",
                    target_symbol=market_data.get('symbol'),
                    probability=prediction_result.model_confidence,
                    expected_impact=abs(predicted_change),
                    time_horizon=prediction_result.horizon,
                    triggered_at=current_time,
                    expires_at=current_time + timedelta(hours=24),
                    recommendations=["考慮減倉", "設置止損", "關注市場消息"],
                    supporting_data={
                        'predicted_change': predicted_change,
                        'current_price': current_price,
                        'predicted_price': predictions[-1],
                        'confidence': prediction_result.model_confidence
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_volatility_spikes(self, prediction_result: PredictionResult,
                                market_data: Dict[str, Any], current_time: datetime) -> List[AlertEvent]:
        """檢查波動性突增"""
        alerts = []
        
        # 檢查不確定性估計
        if prediction_result.uncertainty_estimates:
            combined_uncertainty = prediction_result.uncertainty_estimates.get(UncertaintyType.COMBINED)
            if combined_uncertainty is not None:
                avg_uncertainty = np.mean(combined_uncertainty)
                
                # 高不確定性預警
                if avg_uncertainty > 0.5:  # 50%以上不確定性
                    alert = AlertEvent(
                        alert_id=f"volatility_spike_{int(current_time.timestamp())}",
                        severity=AlertSeverity.HIGH,
                        alert_type="volatility_spike",
                        title="市場波動性突增預警",
                        description=f"預測模型顯示高不確定性({avg_uncertainty:.1%})",
                        target_symbol=market_data.get('symbol'),
                        probability=avg_uncertainty,
                        expected_impact=avg_uncertainty,
                        time_horizon=prediction_result.horizon,
                        triggered_at=current_time,
                        expires_at=current_time + timedelta(hours=12),
                        recommendations=["降低倉位", "增加風險對沖", "密切監控"],
                        supporting_data={
                            'uncertainty_level': avg_uncertainty,
                            'uncertainty_type': UncertaintyType.COMBINED.value,
                            'prediction_spread': np.std(combined_uncertainty)
                        }
                    )
                    alerts.append(alert)
        
        return alerts
    
    def _check_trend_reversals(self, prediction_result: PredictionResult,
                              market_data: Dict[str, Any], current_time: datetime) -> List[AlertEvent]:
        """檢查趨勢轉折"""
        alerts = []
        
        predictions = prediction_result.predictions
        
        # 簡單趨勢轉折檢測
        if len(predictions) >= 5:
            early_trend = np.polyfit(range(len(predictions[:3])), predictions[:3], 1)[0]
            late_trend = np.polyfit(range(len(predictions[-3:])), predictions[-3:], 1)[0]
            
            # 趨勢轉折判斷
            if early_trend > 0 and late_trend < 0:  # 上升轉下降
                alert = AlertEvent(
                    alert_id=f"trend_reversal_down_{int(current_time.timestamp())}",
                    severity=AlertSeverity.MEDIUM,
                    alert_type="trend_reversal",
                    title="上升趨勢轉折預警",
                    description="預測顯示上升趨勢可能轉為下降",
                    target_symbol=market_data.get('symbol'),
                    probability=prediction_result.model_confidence,
                    expected_impact=0.6,
                    time_horizon=prediction_result.horizon,
                    triggered_at=current_time,
                    expires_at=current_time + timedelta(hours=48),
                    recommendations=["檢視持倉", "考慮部分獲利", "準備防守策略"],
                    supporting_data={
                        'early_trend': early_trend,
                        'late_trend': late_trend,
                        'reversal_strength': abs(early_trend - late_trend)
                    }
                )
                alerts.append(alert)
            
            elif early_trend < 0 and late_trend > 0:  # 下降轉上升
                alert = AlertEvent(
                    alert_id=f"trend_reversal_up_{int(current_time.timestamp())}",
                    severity=AlertSeverity.MEDIUM,
                    alert_type="trend_reversal",
                    title="下降趨勢轉折預警",
                    description="預測顯示下降趨勢可能轉為上升",
                    target_symbol=market_data.get('symbol'),
                    probability=prediction_result.model_confidence,
                    expected_impact=0.6,
                    time_horizon=prediction_result.horizon,
                    triggered_at=current_time,
                    expires_at=current_time + timedelta(hours=48),
                    recommendations=["考慮建倉機會", "逐步加倉", "設置合理目標"],
                    supporting_data={
                        'early_trend': early_trend,
                        'late_trend': late_trend,
                        'reversal_strength': abs(early_trend - late_trend)
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _check_risk_events(self, prediction_result: PredictionResult,
                          market_data: Dict[str, Any], current_time: datetime) -> List[AlertEvent]:
        """檢查風險事件"""
        alerts = []
        
        # 檢查置信區間
        if prediction_result.confidence_intervals:
            lower_ci, upper_ci = prediction_result.confidence_intervals
            predictions = prediction_result.predictions
            
            # 計算預測區間寬度
            interval_widths = upper_ci - lower_ci
            avg_width = np.mean(interval_widths)
            
            # 高風險預警（置信區間過寬）
            if avg_width > np.mean(predictions) * 0.2:  # 區間寬度超過預測值的20%
                alert = AlertEvent(
                    alert_id=f"high_risk_{int(current_time.timestamp())}",
                    severity=AlertSeverity.HIGH,
                    alert_type="high_risk",
                    title="高風險環境預警",
                    description=f"預測不確定性較高，投資風險增加",
                    target_symbol=market_data.get('symbol'),
                    probability=0.8,
                    expected_impact=avg_width / np.mean(predictions),
                    time_horizon=prediction_result.horizon,
                    triggered_at=current_time,
                    expires_at=current_time + timedelta(hours=72),
                    recommendations=["降低風險敞口", "增加多樣化", "謹慎操作"],
                    supporting_data={
                        'confidence_interval_width': avg_width,
                        'relative_uncertainty': avg_width / np.mean(predictions),
                        'prediction_volatility': np.std(predictions)
                    }
                )
                alerts.append(alert)
        
        return alerts
    
    def _filter_alerts(self, alerts: List[AlertEvent], current_time: datetime) -> List[AlertEvent]:
        """過濾預警"""
        filtered_alerts = []
        
        for alert in alerts:
            # 檢查頻率限制
            alert_key = f"{alert.alert_type}_{alert.target_symbol}"
            last_alert_time = self.last_alert_times[alert_key]
            
            # 如果距離上次預警不到1小時，跳過
            if current_time - last_alert_time < timedelta(hours=1):
                continue
            
            # 檢查每小時預警數量限制
            hour_key = current_time.strftime("%Y%m%d%H")
            if self.alert_counters[hour_key] >= self.config.max_alerts_per_hour:
                continue
            
            # 通過過濾器
            filtered_alerts.append(alert)
            self.last_alert_times[alert_key] = current_time
            self.alert_counters[hour_key] += 1
        
        return filtered_alerts
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """獲取預警統計信息"""
        if not self.alert_history:
            return {'total_alerts': 0}
        
        alerts = list(self.alert_history)
        
        # 按嚴重程度統計
        severity_counts = defaultdict(int)
        for alert in alerts:
            severity_counts[alert.severity.value] += 1
        
        # 按類型統計
        type_counts = defaultdict(int)
        for alert in alerts:
            type_counts[alert.alert_type] += 1
        
        # 最近24小時預警
        current_time = datetime.now(timezone.utc)
        recent_alerts = [
            alert for alert in alerts 
            if current_time - alert.triggered_at <= timedelta(hours=24)
        ]
        
        return {
            'total_alerts': len(alerts),
            'recent_24h_alerts': len(recent_alerts),
            'severity_distribution': dict(severity_counts),
            'type_distribution': dict(type_counts),
            'average_probability': np.mean([alert.probability for alert in alerts]),
            'average_impact': np.mean([alert.expected_impact for alert in alerts])
        }


class PredictiveAnalyticsPlatform:
    """預測性分析平台核心類"""
    
    def __init__(self, config: PredictiveAnalyticsConfig):
        self.config = config
        self.is_initialized = False
        
        # 核心組件
        self.transformer_model = None
        self.bayesian_model = None
        self.multimodal_fusion = None
        self.alert_system = None
        
        # 數據處理組件
        self.scalers = {}
        self.feature_extractors = {}
        
        # 預測緩存
        self.prediction_cache = {}
        self.cache_timestamps = {}
        
        # 性能統計
        self.prediction_stats = {
            'total_predictions': 0,
            'successful_predictions': 0,
            'average_accuracy': 0.0,
            'average_processing_time': 0.0,
            'model_performance_history': []
        }
        
        logger.info(f"PredictiveAnalyticsPlatform initialized: {config.platform_name}")
    
    async def initialize(self) -> bool:
        """初始化預測性分析平台"""
        try:
            logger.info("Initializing PredictiveAnalyticsPlatform...")
            
            # 1. 設置計算設備
            device = self.config.device
            if device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            self.device = device
            
            # 2. 初始化Transformer模型
            self.transformer_model = TransformerPredictor(self.config).to(self.device)
            
            # 3. 初始化貝葉斯模型（如果啟用）
            if self.config.bayesian_enabled:
                self.bayesian_model = BayesianTransformerPredictor(self.config).to(self.device)
            
            # 4. 初始化多模態融合（如果啟用）
            if self.config.multimodal_enabled:
                self.multimodal_fusion = MultiModalFusionModule(self.config).to(self.device)
            
            # 5. 初始化預警系統
            if self.config.alert_enabled:
                self.alert_system = RiskAlertSystem(self.config)
            
            # 6. 初始化數據處理組件
            self.scalers = {
                'robust': RobustScaler(),
                'standard': StandardScaler()
            }
            
            # 7. 創建模型保存目錄
            os.makedirs(self.config.model_save_path, exist_ok=True)
            
            # 8. 載入預訓練模型（如果存在）
            await self._load_pretrained_models()
            
            self.is_initialized = True
            logger.info("PredictiveAnalyticsPlatform initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"PredictiveAnalyticsPlatform initialization failed: {e}")
            return False
    
    async def make_prediction(self, time_series_data: TimeSeriesData,
                            prediction_type: PredictionType,
                            horizon: PredictionHorizon,
                            additional_features: Optional[Dict[str, np.ndarray]] = None) -> PredictionResult:
        """執行預測"""
        try:
            prediction_id = f"pred_{int(datetime.now().timestamp())}_{hash(str(time_series_data.metadata)) % 10000:04d}"
            start_time = datetime.now()
            
            logger.info(f"Making prediction: {prediction_id} - {prediction_type.value} - {horizon.value}")
            
            # 1. 檢查緩存
            cache_key = self._generate_cache_key(time_series_data, prediction_type, horizon)
            if self.config.cache_enabled and cache_key in self.prediction_cache:
                cache_time = self.cache_timestamps[cache_key]
                if datetime.now() - cache_time <= timedelta(minutes=self.config.cache_ttl_minutes):
                    logger.info(f"Returning cached prediction: {prediction_id}")
                    return self.prediction_cache[cache_key]
            
            # 2. 數據預處理
            processed_data = await self._preprocess_data(time_series_data, prediction_type)
            
            # 3. 特徵提取
            features_tensor, additional_tensors = await self._extract_features(
                processed_data, additional_features
            )
            
            # 4. 執行預測
            predictions, uncertainty = await self._perform_prediction(
                features_tensor, additional_tensors, prediction_type, horizon
            )
            
            # 5. 後處理預測結果
            processed_predictions = await self._postprocess_predictions(
                predictions, uncertainty, processed_data, prediction_type
            )
            
            # 6. 計算置信區間
            confidence_intervals = await self._calculate_confidence_intervals(
                processed_predictions, uncertainty, prediction_type
            )
            
            # 7. 估計不確定性
            uncertainty_estimates = await self._estimate_uncertainty(
                processed_predictions, uncertainty, features_tensor
            )
            
            # 8. 計算特徵重要性
            feature_importance = await self._calculate_feature_importance(
                features_tensor, processed_predictions
            )
            
            # 9. 生成目標時間戳
            target_timestamps = self._generate_target_timestamps(
                time_series_data.timestamps[-1], horizon
            )
            
            # 10. 計算模型置信度
            model_confidence = await self._calculate_model_confidence(
                processed_predictions, uncertainty_estimates, feature_importance
            )
            
            # 11. 創建預測結果
            prediction_result = PredictionResult(
                prediction_id=prediction_id,
                prediction_type=prediction_type,
                horizon=horizon,
                target_timestamps=target_timestamps,
                predictions=processed_predictions,
                confidence_intervals=confidence_intervals,
                uncertainty_estimates=uncertainty_estimates,
                feature_importance=feature_importance,
                model_confidence=model_confidence,
                metadata={
                    'processing_time_ms': (datetime.now() - start_time).total_seconds() * 1000,
                    'model_type': self.config.model_type,
                    'device_used': self.device,
                    'input_sequence_length': len(time_series_data.values),
                    'prediction_length': len(processed_predictions)
                }
            )
            
            # 12. 緩存預測結果
            if self.config.cache_enabled:
                self.prediction_cache[cache_key] = prediction_result
                self.cache_timestamps[cache_key] = datetime.now()
            
            # 13. 更新統計信息
            self._update_prediction_stats(prediction_result, start_time)
            
            logger.info(f"Prediction completed: {prediction_id} - Confidence: {model_confidence:.3f}")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            
            # 返回錯誤預測結果
            return PredictionResult(
                prediction_id=f"error_{int(datetime.now().timestamp())}",
                prediction_type=prediction_type,
                horizon=horizon,
                target_timestamps=[],
                predictions=np.array([]),
                confidence_intervals=None,
                uncertainty_estimates=None,
                feature_importance=None,
                model_confidence=0.0,
                metadata={'error': str(e)}
            )
    
    async def generate_alerts(self, prediction_result: PredictionResult,
                            market_data: Dict[str, Any]) -> List[AlertEvent]:
        """生成預警事件"""
        if not self.config.alert_enabled or not self.alert_system:
            return []
        
        try:
            alerts = self.alert_system.evaluate_alerts(prediction_result, market_data)
            logger.info(f"Generated {len(alerts)} alerts for prediction {prediction_result.prediction_id}")
            return alerts
            
        except Exception as e:
            logger.error(f"Alert generation failed: {e}")
            return []
    
    async def train_model(self, training_data: List[TimeSeriesData],
                         prediction_type: PredictionType,
                         validation_split: float = None) -> Dict[str, Any]:
        """訓練模型"""
        try:
            logger.info(f"Starting model training for {prediction_type.value}")
            
            if validation_split is None:
                validation_split = self.config.validation_split
            
            # 1. 數據準備
            processed_data = []
            for ts_data in training_data:
                processed = await self._preprocess_data(ts_data, prediction_type)
                processed_data.append(processed)
            
            # 2. 分割訓練和驗證數據
            split_idx = int(len(processed_data) * (1 - validation_split))
            train_data = processed_data[:split_idx]
            val_data = processed_data[split_idx:]
            
            # 3. 創建數據載入器
            train_loader = self._create_data_loader(train_data, batch_size=self.config.batch_size, shuffle=True)
            val_loader = self._create_data_loader(val_data, batch_size=self.config.batch_size, shuffle=False)
            
            # 4. 設置優化器和損失函數
            optimizer = optim.Adam(self.transformer_model.parameters(), lr=self.config.learning_rate)
            criterion = nn.MSELoss()
            scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
            
            # 5. 訓練循環
            train_losses = []
            val_losses = []
            best_val_loss = float('inf')
            patience_counter = 0
            
            for epoch in range(self.config.num_epochs):
                # 訓練階段
                self.transformer_model.train()
                train_loss = 0.0
                
                for batch in train_loader:
                    optimizer.zero_grad()
                    
                    inputs, targets = batch
                    inputs = inputs.to(self.device)
                    targets = targets.to(self.device)
                    
                    predictions, uncertainty = self.transformer_model(inputs)
                    loss = criterion(predictions, targets)
                    
                    # 添加不確定性正則化
                    if uncertainty is not None:
                        uncertainty_loss = torch.mean(uncertainty)
                        loss = loss + 0.1 * uncertainty_loss
                    
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.transformer_model.parameters(), 1.0)
                    optimizer.step()
                    
                    train_loss += loss.item()
                
                avg_train_loss = train_loss / len(train_loader)
                train_losses.append(avg_train_loss)
                
                # 驗證階段
                self.transformer_model.eval()
                val_loss = 0.0
                
                with torch.no_grad():
                    for batch in val_loader:
                        inputs, targets = batch
                        inputs = inputs.to(self.device)
                        targets = targets.to(self.device)
                        
                        predictions, _ = self.transformer_model(inputs)
                        loss = criterion(predictions, targets)
                        val_loss += loss.item()
                
                avg_val_loss = val_loss / len(val_loader)
                val_losses.append(avg_val_loss)
                
                # 學習率調度
                scheduler.step(avg_val_loss)
                
                # 早停檢查
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    patience_counter = 0
                    
                    # 保存最佳模型
                    await self._save_model_checkpoint(epoch, avg_val_loss)
                else:
                    patience_counter += 1
                
                if patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at epoch {epoch}")
                    break
                
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}: Train Loss = {avg_train_loss:.6f}, Val Loss = {avg_val_loss:.6f}")
            
            return {
                'training_completed': True,
                'final_train_loss': train_losses[-1],
                'final_val_loss': val_losses[-1],
                'best_val_loss': best_val_loss,
                'total_epochs': len(train_losses),
                'train_losses': train_losses,
                'val_losses': val_losses
            }
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return {
                'training_completed': False,
                'error': str(e)
            }
    
    def evaluate_performance(self) -> Dict[str, Any]:
        """評估平台性能"""
        try:
            # 基本統計
            basic_stats = {
                'total_predictions': self.prediction_stats['total_predictions'],
                'successful_predictions': self.prediction_stats['successful_predictions'],
                'success_rate': (
                    self.prediction_stats['successful_predictions'] / 
                    max(1, self.prediction_stats['total_predictions'])
                ),
                'average_processing_time_ms': self.prediction_stats['average_processing_time']
            }
            
            # 模型性能
            model_performance = {
                'average_accuracy': self.prediction_stats['average_accuracy'],
                'performance_history_length': len(self.prediction_stats['model_performance_history'])
            }
            
            # 預警系統統計
            alert_stats = {}
            if self.alert_system:
                alert_stats = self.alert_system.get_alert_statistics()
            
            # 緩存統計
            cache_stats = {
                'cache_enabled': self.config.cache_enabled,
                'cached_predictions': len(self.prediction_cache),
                'cache_hit_rate': self._calculate_cache_hit_rate()
            }
            
            # 系統狀態
            system_status = {
                'is_initialized': self.is_initialized,
                'device': self.device,
                'models_loaded': {
                    'transformer': self.transformer_model is not None,
                    'bayesian': self.bayesian_model is not None,
                    'multimodal': self.multimodal_fusion is not None
                }
            }
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'basic_statistics': basic_stats,
                'model_performance': model_performance,
                'alert_statistics': alert_stats,
                'cache_statistics': cache_stats,
                'system_status': system_status,
                'overall_health_score': self._calculate_health_score()
            }
            
        except Exception as e:
            logger.error(f"Performance evaluation failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _preprocess_data(self, time_series_data: TimeSeriesData, 
                              prediction_type: PredictionType) -> TimeSeriesData:
        """數據預處理"""
        # 複製數據以避免修改原始數據
        values = time_series_data.values.copy()
        
        # 根據預測類型進行不同的預處理
        if prediction_type == PredictionType.RETURN:
            # 計算收益率
            if len(values) > 1:
                returns = np.diff(values) / values[:-1]
                values = np.concatenate([[0], returns])  # 第一個值設為0
        
        elif prediction_type == PredictionType.VOLATILITY:
            # 計算滾動波動性
            window = min(20, len(values) // 4)
            if window > 1:
                rolling_std = pd.Series(values).rolling(window).std().fillna(method='bfill').values
                values = rolling_std
        
        # 標準化
        scaler_key = f"{prediction_type.value}_scaler"
        if scaler_key not in self.scalers:
            self.scalers[scaler_key] = StandardScaler()
        
        # 確保values是二維數組
        if values.ndim == 1:
            values = values.reshape(-1, 1)
        
        # 擬合並轉換數據
        if not hasattr(self.scalers[scaler_key], 'scale_'):
            self.scalers[scaler_key].fit(values)
        
        scaled_values = self.scalers[scaler_key].transform(values)
        
        return TimeSeriesData(
            timestamps=time_series_data.timestamps.copy(),
            values=scaled_values.flatten(),
            features=time_series_data.features.copy() if time_series_data.features is not None else None,
            metadata=time_series_data.metadata.copy()
        )
    
    async def _extract_features(self, time_series_data: TimeSeriesData,
                               additional_features: Optional[Dict[str, np.ndarray]]) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """特徵提取"""
        
        # 基本時序特徵
        values = time_series_data.values
        seq_len = min(self.config.sequence_length, len(values))
        
        # 創建滑動窗口特徵
        if len(values) < seq_len:
            # 如果數據不夠，進行填充
            padded_values = np.pad(values, (seq_len - len(values), 0), 'constant', constant_values=values[0])
            sequence_data = padded_values
        else:
            sequence_data = values[-seq_len:]
        
        # 創建多特徵輸入
        features = []
        
        # 價格特徵
        features.append(sequence_data)
        
        # 技術指標特徵（如果有額外特徵）
        if time_series_data.features is not None:
            for i in range(min(self.config.feature_dim - 1, time_series_data.features.shape[1])):
                feature_seq = time_series_data.features[-seq_len:, i]
                if len(feature_seq) < seq_len:
                    feature_seq = np.pad(feature_seq, (seq_len - len(feature_seq), 0), 'constant')
                features.append(feature_seq)
        
        # 填充到指定特徵維度
        while len(features) < self.config.feature_dim:
            # 添加移動平均特徵
            if len(features) == 1:
                ma_window = min(5, len(sequence_data))
                ma_feature = pd.Series(sequence_data).rolling(ma_window).mean().fillna(method='bfill').values
                features.append(ma_feature)
            elif len(features) == 2:
                # 添加波動性特徵
                vol_window = min(10, len(sequence_data))
                vol_feature = pd.Series(sequence_data).rolling(vol_window).std().fillna(method='bfill').values
                features.append(vol_feature)
            else:
                # 添加零特徵
                features.append(np.zeros_like(sequence_data))
        
        # 堆疊特徵
        feature_matrix = np.column_stack(features[:self.config.feature_dim])
        features_tensor = torch.FloatTensor(feature_matrix).unsqueeze(0).to(self.device)  # [1, seq_len, feature_dim]
        
        # 處理額外特徵
        additional_tensors = {}
        if additional_features:
            if 'text_features' in additional_features:
                text_tensor = torch.FloatTensor(additional_features['text_features']).unsqueeze(0).to(self.device)
                additional_tensors['text_features'] = text_tensor
            
            if 'image_features' in additional_features:
                image_tensor = torch.FloatTensor(additional_features['image_features']).unsqueeze(0).to(self.device)
                additional_tensors['image_features'] = image_tensor
        
        return features_tensor, additional_tensors
    
    async def _perform_prediction(self, features_tensor: torch.Tensor,
                                 additional_tensors: Dict[str, torch.Tensor],
                                 prediction_type: PredictionType,
                                 horizon: PredictionHorizon) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """執行預測"""
        
        self.transformer_model.eval()
        
        with torch.no_grad():
            # 標準預測
            predictions, uncertainty = self.transformer_model(
                features_tensor,
                text_features=additional_tensors.get('text_features'),
                image_features=additional_tensors.get('image_features')
            )
            
            # 貝葉斯預測（如果啟用）
            if self.config.bayesian_enabled and self.bayesian_model:
                bayesian_mean, bayesian_std = self.bayesian_model.monte_carlo_forward(
                    features_tensor, 
                    self.config.monte_carlo_samples
                )
                
                # 結合預測結果
                predictions = (predictions + bayesian_mean) / 2
                if uncertainty is not None:
                    uncertainty = (uncertainty + bayesian_std) / 2
                else:
                    uncertainty = bayesian_std
        
        # 轉換為numpy數組
        pred_numpy = predictions.cpu().numpy().flatten()
        uncertainty_numpy = uncertainty.cpu().numpy().flatten() if uncertainty is not None else None
        
        # 調整預測長度（根據時間範圍）
        horizon_lengths = {
            PredictionHorizon.INTRADAY: 6,
            PredictionHorizon.SHORT_TERM: 5,
            PredictionHorizon.MEDIUM_TERM: 20,
            PredictionHorizon.LONG_TERM: 120,
            PredictionHorizon.STRATEGIC: 252
        }
        
        target_length = horizon_lengths.get(horizon, self.config.prediction_length)
        
        if len(pred_numpy) > target_length:
            pred_numpy = pred_numpy[:target_length]
            if uncertainty_numpy is not None:
                uncertainty_numpy = uncertainty_numpy[:target_length]
        elif len(pred_numpy) < target_length:
            # 線性外推
            last_value = pred_numpy[-1] if len(pred_numpy) > 0 else 0
            extension = np.linspace(last_value, last_value, target_length - len(pred_numpy))
            pred_numpy = np.concatenate([pred_numpy, extension])
            
            if uncertainty_numpy is not None:
                last_uncertainty = uncertainty_numpy[-1] if len(uncertainty_numpy) > 0 else 0.1
                uncertainty_extension = np.full(target_length - len(uncertainty_numpy), last_uncertainty)
                uncertainty_numpy = np.concatenate([uncertainty_numpy, uncertainty_extension])
        
        return pred_numpy, uncertainty_numpy
    
    async def _postprocess_predictions(self, predictions: np.ndarray, uncertainty: Optional[np.ndarray],
                                     processed_data: TimeSeriesData, prediction_type: PredictionType) -> np.ndarray:
        """後處理預測結果"""
        
        # 反標準化
        scaler_key = f"{prediction_type.value}_scaler"
        if scaler_key in self.scalers and hasattr(self.scalers[scaler_key], 'scale_'):
            # 確保predictions是二維數組
            if predictions.ndim == 1:
                predictions_2d = predictions.reshape(-1, 1)
            else:
                predictions_2d = predictions
            
            # 反標準化
            predictions = self.scalers[scaler_key].inverse_transform(predictions_2d).flatten()
        
        # 根據預測類型進行後處理
        if prediction_type == PredictionType.RETURN:
            # 如果是收益率預測，轉換為價格
            last_price = processed_data.values[-1] if len(processed_data.values) > 0 else 100
            # 反標準化後的last_price
            if scaler_key in self.scalers:
                last_price_scaled = np.array([[last_price]])
                last_price = self.scalers[scaler_key].inverse_transform(last_price_scaled)[0, 0]
            
            prices = [last_price]
            for return_rate in predictions:
                next_price = prices[-1] * (1 + return_rate)
                prices.append(next_price)
            predictions = np.array(prices[1:])  # 排除初始價格
        
        elif prediction_type == PredictionType.PRICE:
            # 確保價格為正數
            predictions = np.maximum(predictions, 0.01)
        
        elif prediction_type == PredictionType.VOLATILITY:
            # 確保波動性為正數
            predictions = np.abs(predictions)
        
        return predictions
    
    async def _calculate_confidence_intervals(self, predictions: np.ndarray, 
                                            uncertainty: Optional[np.ndarray],
                                            prediction_type: PredictionType) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """計算置信區間"""
        
        if uncertainty is None:
            # 如果沒有不確定性估計，使用固定比例
            default_uncertainty = np.abs(predictions) * 0.1  # 10%不確定性
            lower_ci = predictions - 1.96 * default_uncertainty  # 95%置信區間
            upper_ci = predictions + 1.96 * default_uncertainty
        else:
            lower_ci = predictions - 1.96 * uncertainty
            upper_ci = predictions + 1.96 * uncertainty
        
        # 確保價格類型的置信區間為正數
        if prediction_type in [PredictionType.PRICE, PredictionType.VOLATILITY, PredictionType.VOLUME]:
            lower_ci = np.maximum(lower_ci, 0.01)
            upper_ci = np.maximum(upper_ci, 0.01)
        
        return (lower_ci, upper_ci)
    
    async def _estimate_uncertainty(self, predictions: np.ndarray, 
                                   uncertainty: Optional[np.ndarray],
                                   features_tensor: torch.Tensor) -> Dict[UncertaintyType, np.ndarray]:
        """估計不確定性"""
        
        uncertainty_estimates = {}
        
        if uncertainty is not None:
            # 偶然不確定性（數據噪音）
            aleatoric_uncertainty = uncertainty * 0.6  # 假設60%來自數據噪音
            
            # 認知不確定性（模型不確定性）
            epistemic_uncertainty = uncertainty * 0.4  # 假設40%來自模型不確定性
            
            # 結合不確定性
            combined_uncertainty = uncertainty
            
            uncertainty_estimates = {
                UncertaintyType.ALEATORIC: aleatoric_uncertainty,
                UncertaintyType.EPISTEMIC: epistemic_uncertainty,
                UncertaintyType.COMBINED: combined_uncertainty
            }
        else:
            # 如果沒有明確的不確定性估計，基於預測方差估計
            pred_std = np.std(predictions)
            default_uncertainty = np.full_like(predictions, pred_std)
            
            uncertainty_estimates = {
                UncertaintyType.COMBINED: default_uncertainty
            }
        
        return uncertainty_estimates
    
    async def _calculate_feature_importance(self, features_tensor: torch.Tensor, 
                                           predictions: np.ndarray) -> Dict[str, float]:
        """計算特徵重要性"""
        
        # 簡化的特徵重要性計算
        feature_names = [
            'price', 'moving_average_5', 'volatility_10', 'volume', 'rsi', 
            'macd', 'bollinger_upper', 'bollinger_lower', 'momentum', 'other'
        ]
        
        # 基於特徵值的標準差作為重要性的代理
        features_np = features_tensor.cpu().numpy().squeeze(0)  # [seq_len, feature_dim]
        feature_stds = np.std(features_np, axis=0)
        
        # 標準化重要性分數
        importance_scores = feature_stds / (np.sum(feature_stds) + 1e-8)
        
        # 創建特徵重要性字典
        feature_importance = {}
        for i, name in enumerate(feature_names[:len(importance_scores)]):
            feature_importance[name] = float(importance_scores[i])
        
        return feature_importance
    
    def _generate_target_timestamps(self, last_timestamp: datetime, 
                                   horizon: PredictionHorizon) -> List[datetime]:
        """生成目標時間戳"""
        
        # 時間間隔映射
        interval_mapping = {
            PredictionHorizon.INTRADAY: timedelta(hours=1),
            PredictionHorizon.SHORT_TERM: timedelta(days=1),
            PredictionHorizon.MEDIUM_TERM: timedelta(days=1),
            PredictionHorizon.LONG_TERM: timedelta(days=1),
            PredictionHorizon.STRATEGIC: timedelta(days=7)
        }
        
        # 預測點數映射
        points_mapping = {
            PredictionHorizon.INTRADAY: 6,
            PredictionHorizon.SHORT_TERM: 5,
            PredictionHorizon.MEDIUM_TERM: 20,
            PredictionHorizon.LONG_TERM: 120,
            PredictionHorizon.STRATEGIC: 52
        }
        
        interval = interval_mapping.get(horizon, timedelta(days=1))
        num_points = points_mapping.get(horizon, 20)
        
        timestamps = []
        current_time = last_timestamp
        
        for i in range(num_points):
            current_time += interval
            timestamps.append(current_time)
        
        return timestamps
    
    async def _calculate_model_confidence(self, predictions: np.ndarray,
                                         uncertainty_estimates: Optional[Dict[UncertaintyType, np.ndarray]],
                                         feature_importance: Optional[Dict[str, float]]) -> float:
        """計算模型置信度"""
        
        confidence_factors = []
        
        # 基於預測穩定性的置信度
        pred_stability = 1.0 - (np.std(predictions) / (np.mean(np.abs(predictions)) + 1e-8))
        confidence_factors.append(max(0.0, min(1.0, pred_stability)))
        
        # 基於不確定性的置信度
        if uncertainty_estimates and UncertaintyType.COMBINED in uncertainty_estimates:
            uncertainty = uncertainty_estimates[UncertaintyType.COMBINED]
            avg_uncertainty = np.mean(uncertainty)
            max_uncertainty = np.mean(np.abs(predictions)) * 0.5  # 最大合理不確定性
            uncertainty_confidence = 1.0 - (avg_uncertainty / max_uncertainty)
            confidence_factors.append(max(0.0, min(1.0, uncertainty_confidence)))
        
        # 基於特徵重要性分佈的置信度
        if feature_importance:
            importance_values = list(feature_importance.values())
            # 如果特徵重要性分佈均勻，置信度較低
            importance_entropy = -sum(p * np.log(p + 1e-8) for p in importance_values if p > 0)
            max_entropy = np.log(len(importance_values))
            entropy_confidence = 1.0 - (importance_entropy / max_entropy)
            confidence_factors.append(max(0.0, min(1.0, entropy_confidence)))
        
        # 綜合置信度
        overall_confidence = np.mean(confidence_factors) if confidence_factors else 0.5
        
        return float(overall_confidence)
    
    def _generate_cache_key(self, time_series_data: TimeSeriesData,
                           prediction_type: PredictionType, 
                           horizon: PredictionHorizon) -> str:
        """生成緩存鍵"""
        
        data_hash = hash((
            tuple(time_series_data.values[-10:]),  # 使用最後10個值
            prediction_type.value,
            horizon.value,
            str(time_series_data.metadata)
        ))
        
        return f"pred_cache_{abs(data_hash) % 100000:05d}"
    
    def _update_prediction_stats(self, prediction_result: PredictionResult, start_time: datetime):
        """更新預測統計信息"""
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        self.prediction_stats['total_predictions'] += 1
        
        # 判斷預測是否成功
        if prediction_result.model_confidence > 0.5:
            self.prediction_stats['successful_predictions'] += 1
        
        # 更新平均處理時間
        current_avg = self.prediction_stats['average_processing_time']
        total_preds = self.prediction_stats['total_predictions']
        
        new_avg = ((current_avg * (total_preds - 1)) + processing_time) / total_preds
        self.prediction_stats['average_processing_time'] = new_avg
        
        # 記錄性能歷史
        performance_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'confidence': prediction_result.model_confidence,
            'processing_time_ms': processing_time,
            'prediction_length': len(prediction_result.predictions)
        }
        
        self.prediction_stats['model_performance_history'].append(performance_record)
        
        # 保持歷史記錄大小
        if len(self.prediction_stats['model_performance_history']) > 1000:
            self.prediction_stats['model_performance_history'].pop(0)
    
    def _calculate_cache_hit_rate(self) -> float:
        """計算緩存命中率"""
        # 簡化的緩存命中率計算
        if self.prediction_stats['total_predictions'] == 0:
            return 0.0
        
        # 假設的緩存命中計算
        cache_hits = len(self.prediction_cache) * 0.3  # 假設30%的預測使用了緩存
        return cache_hits / self.prediction_stats['total_predictions']
    
    def _calculate_health_score(self) -> float:
        """計算系統健康分數"""
        scores = []
        
        # 成功率分數
        if self.prediction_stats['total_predictions'] > 0:
            success_rate = (
                self.prediction_stats['successful_predictions'] / 
                self.prediction_stats['total_predictions']
            )
            scores.append(success_rate)
        
        # 處理時間分數
        avg_time = self.prediction_stats['average_processing_time']
        time_score = max(0.0, 1.0 - (avg_time / 10000))  # 10秒以下為滿分
        scores.append(time_score)
        
        # 初始化分數
        if self.is_initialized:
            scores.append(1.0)
        else:
            scores.append(0.0)
        
        return np.mean(scores) if scores else 0.5
    
    def _create_data_loader(self, data: List[TimeSeriesData], batch_size: int, shuffle: bool):
        """創建數據載入器（簡化版本）"""
        # 這裡應該創建PyTorch DataLoader，簡化為返回數據列表
        return data
    
    async def _save_model_checkpoint(self, epoch: int, val_loss: float):
        """保存模型檢查點"""
        try:
            checkpoint = {
                'epoch': epoch,
                'model_state_dict': self.transformer_model.state_dict(),
                'val_loss': val_loss,
                'config': self.config.dict(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            checkpoint_path = os.path.join(
                self.config.model_save_path, 
                f"checkpoint_epoch_{epoch}_loss_{val_loss:.6f}.pt"
            )
            
            torch.save(checkpoint, checkpoint_path)
            logger.info(f"Model checkpoint saved: {checkpoint_path}")
            
        except Exception as e:
            logger.error(f"Failed to save model checkpoint: {e}")
    
    async def _load_pretrained_models(self):
        """載入預訓練模型"""
        try:
            model_path = Path(self.config.model_save_path)
            if not model_path.exists():
                return
            
            # 尋找最新的檢查點
            checkpoint_files = list(model_path.glob("checkpoint_*.pt"))
            if not checkpoint_files:
                return
            
            latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
            
            checkpoint = torch.load(latest_checkpoint, map_location=self.device)
            self.transformer_model.load_state_dict(checkpoint['model_state_dict'])
            
            logger.info(f"Pretrained model loaded: {latest_checkpoint}")
            
        except Exception as e:
            logger.warning(f"Failed to load pretrained model: {e}")
    
    def get_platform_statistics(self) -> Dict[str, Any]:
        """獲取平台統計信息"""
        return {
            'config': self.config.dict(),
            'is_initialized': self.is_initialized,
            'device': self.device,
            'prediction_statistics': self.prediction_stats,
            'cache_statistics': {
                'enabled': self.config.cache_enabled,
                'cached_items': len(self.prediction_cache),
                'cache_hit_rate': self._calculate_cache_hit_rate()
            },
            'model_statistics': {
                'transformer_parameters': self.transformer_model._count_parameters() if self.transformer_model else 0,
                'models_available': {
                    'transformer': self.transformer_model is not None,
                    'bayesian': self.bayesian_model is not None,
                    'multimodal': self.multimodal_fusion is not None
                }
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# 使用示例和測試函數
async def create_predictive_platform_example():
    """創建預測性分析平台示例"""
    
    # 創建配置
    config = PredictiveAnalyticsConfig(
        platform_id="predictive_v1",
        platform_name="TradingAgents預測性分析平台",
        model_type="transformer",
        sequence_length=30,
        prediction_length=10,
        feature_dim=8,
        hidden_dim=128,
        num_layers=4,
        learning_rate=0.001,
        uncertainty_enabled=True,
        multimodal_enabled=True,
        alert_enabled=True,
        device="cpu"
    )
    
    # 創建平台
    platform = PredictiveAnalyticsPlatform(config)
    
    # 初始化
    success = await platform.initialize()
    
    if success:
        logger.info("預測性分析平台創建成功")
        
        # 模擬時序數據
        timestamps = [datetime.now(timezone.utc) - timedelta(days=i) for i in range(50, 0, -1)]
        values = np.cumsum(np.random.randn(50) * 0.02) + 100  # 模擬股價
        
        time_series = TimeSeriesData(
            timestamps=timestamps,
            values=values,
            features=np.random.randn(50, 3),  # 模擬技術指標
            metadata={'symbol': 'TEST001', 'data_source': 'simulation'}
        )
        
        # 執行價格預測
        price_prediction = await platform.make_prediction(
            time_series_data=time_series,
            prediction_type=PredictionType.PRICE,
            horizon=PredictionHorizon.SHORT_TERM,
            additional_features={
                'text_features': np.random.randn(768),  # 模擬新聞文本特徵
                'image_features': np.random.randn(512)  # 模擬圖表特徵
            }
        )
        
        # 生成預警
        market_data = {
            'symbol': 'TEST001',
            'current_price': values[-1],
            'volume': 1000000,
            'market_cap': 10000000000
        }
        
        alerts = await platform.generate_alerts(price_prediction, market_data)
        
        # 評估性能
        performance = platform.evaluate_performance()
        
        # 獲取統計信息
        stats = platform.get_platform_statistics()
        
        return {
            'initialization_success': success,
            'price_prediction': price_prediction.to_dict(),
            'generated_alerts': [alert.to_dict() for alert in alerts],
            'performance_evaluation': performance,
            'platform_statistics': stats
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
        result = await create_predictive_platform_example()
        print("=== 預測性分析平台測試結果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    asyncio.run(main())