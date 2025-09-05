#!/usr/bin/env python3
"""
Behavior Predictor - 行為預測器
天工 (TianGong) - 基於深度學習的用戶行為預測系統

此模組提供：
1. 多模型行為預測
2. 時序行為建模
3. 個人化預測調整
4. 預測準確度評估
5. 適應性模型更新
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
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
import time
import math
import pickle
from pathlib import Path

# Machine Learning imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb

# Deep Learning imports
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import torch.nn.functional as F

# Time Series imports
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
import warnings
warnings.filterwarnings('ignore')

class ModelType(Enum):
    """預測模型類型"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting" 
    NEURAL_NETWORK = "neural_network"
    SVM = "svm"
    XGBOOST = "xgboost"
    LSTM = "lstm"
    TRANSFORMER = "transformer"
    ARIMA = "arima"
    ENSEMBLE = "ensemble"

class PredictionType(Enum):
    """預測類型"""
    NEXT_ACTION = "next_action"                    # 下一個行為
    ACTION_SEQUENCE = "action_sequence"            # 行為序列
    DECISION_QUALITY = "decision_quality"          # 決策品質
    RISK_LEVEL = "risk_level"                     # 風險水平
    PERFORMANCE_OUTCOME = "performance_outcome"    # 績效結果
    TRADING_FREQUENCY = "trading_frequency"        # 交易頻率
    POSITION_SIZING = "position_sizing"           # 倉位大小
    MARKET_TIMING = "market_timing"               # 市場時機

class PredictionHorizon(Enum):
    """預測時間跨度"""
    IMMEDIATE = "immediate"        # 立即 (1-5分鐘)
    SHORT_TERM = "short_term"      # 短期 (1小時-1天)
    MEDIUM_TERM = "medium_term"    # 中期 (1-7天)
    LONG_TERM = "long_term"        # 長期 (1-4週)

@dataclass
class PredictionRequest:
    """預測請求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    prediction_type: PredictionType = PredictionType.NEXT_ACTION
    prediction_horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM
    context_data: Dict[str, Any] = field(default_factory=dict)
    historical_data: List[Dict[str, Any]] = field(default_factory=list)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    user_state: Dict[str, Any] = field(default_factory=dict)
    model_preferences: List[ModelType] = field(default_factory=list)
    confidence_threshold: float = 0.7
    timestamp: float = field(default_factory=time.time)

@dataclass
class BehaviorForecast:
    """行為預測結果"""
    forecast_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    user_id: str = ""
    prediction_type: PredictionType = PredictionType.NEXT_ACTION
    prediction_horizon: PredictionHorizon = PredictionHorizon.SHORT_TERM
    
    # 預測結果
    predicted_behavior: Dict[str, Any] = field(default_factory=dict)
    prediction_probabilities: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.0
    uncertainty_range: Tuple[float, float] = (0.0, 1.0)
    
    # 模型信息
    models_used: List[ModelType] = field(default_factory=list)
    model_agreement: float = 0.0                    # 模型間一致性
    ensemble_weight: Dict[str, float] = field(default_factory=dict)
    
    # 預測依據
    key_factors: List[str] = field(default_factory=list)
    factor_importance: Dict[str, float] = field(default_factory=dict)
    supporting_patterns: List[str] = field(default_factory=list)
    
    # 風險評估
    prediction_risk: float = 0.0                   # 預測風險
    alternative_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    
    # 時間信息
    prediction_timestamp: float = field(default_factory=time.time)
    expected_realization_time: Optional[float] = None
    
    # 驗證追蹤
    actual_outcome: Optional[Dict[str, Any]] = None
    prediction_accuracy: Optional[float] = None
    validation_timestamp: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class LSTMPredictor(nn.Module):
    """LSTM行為預測模型"""
    
    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, output_size: int = 10):
        super(LSTMPredictor, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=0.2)
        self.attention = nn.MultiheadAttention(hidden_size, num_heads=4)
        self.layer_norm = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        # LSTM處理
        lstm_out, (hidden, cell) = self.lstm(x)
        
        # 自注意力
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        
        # 殘差連接和歸一化
        combined = self.layer_norm(lstm_out + attn_out)
        
        # 取最後時步
        last_output = combined[:, -1, :]
        
        # 全連接層
        output = self.fc(self.dropout(last_output))
        
        return torch.softmax(output, dim=1)

class TransformerPredictor(nn.Module):
    """Transformer行為預測模型"""
    
    def __init__(self, input_size: int, d_model: int = 64, nhead: int = 8, 
                 num_layers: int = 3, output_size: int = 10):
        super(TransformerPredictor, self).__init__()
        
        self.input_projection = nn.Linear(input_size, d_model)
        self.positional_encoding = self._generate_positional_encoding(1000, d_model)
        
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dropout=0.2
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        self.layer_norm = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(d_model, output_size)
        
    def _generate_positional_encoding(self, max_len: int, d_model: int) -> torch.Tensor:
        """生成位置編碼"""
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len).unsqueeze(1).float()
        
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                            -(math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        return pe.unsqueeze(0)
    
    def forward(self, x):
        seq_len = x.size(1)
        
        # 輸入投影
        x = self.input_projection(x)
        
        # 位置編碼
        x = x + self.positional_encoding[:, :seq_len, :]
        
        # Transformer編碼
        x = x.transpose(0, 1)  # (seq_len, batch_size, d_model)
        encoded = self.transformer_encoder(x)
        
        # 取最後時步
        last_output = encoded[-1]  # (batch_size, d_model)
        
        # 全連接層
        output = self.fc(self.dropout(self.layer_norm(last_output)))
        
        return torch.softmax(output, dim=1)

class BehaviorPredictor:
    """行為預測器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 存儲配置
        self.model_storage_path = Path(self.config.get('model_storage_path', './behavior_models'))
        self.model_storage_path.mkdir(exist_ok=True)
        
        # 模型組件
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.encoders: Dict[str, LabelEncoder] = {}
        
        # 預測緩存
        self.prediction_cache: Dict[str, BehaviorForecast] = {}
        self.training_data_cache: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 配置
        self.predictor_config = {
            'min_training_samples': self.config.get('min_training_samples', 50),
            'retrain_interval_hours': self.config.get('retrain_interval_hours', 24),
            'cache_size': self.config.get('cache_size', 1000),
            'ensemble_threshold': self.config.get('ensemble_threshold', 0.8),
            'prediction_timeout': self.config.get('prediction_timeout', 30)
        }
        
        # 初始化模型
        asyncio.create_task(self._initialize_models())
        
        self.logger.info("BehaviorPredictor initialized")

    async def _initialize_models(self):
        """初始化預測模型"""
        
        try:
            # 傳統機器學習模型
            self.models['random_forest'] = RandomForestClassifier(
                n_estimators=100, random_state=42, n_jobs=-1
            )
            
            self.models['gradient_boosting'] = GradientBoostingClassifier(
                n_estimators=100, random_state=42
            )
            
            self.models['xgboost'] = xgb.XGBClassifier(
                n_estimators=100, random_state=42, n_jobs=-1
            )
            
            self.models['svm'] = SVC(
                kernel='rbf', probability=True, random_state=42
            )
            
            self.models['neural_network'] = MLPClassifier(
                hidden_layer_sizes=(100, 50), max_iter=500, random_state=42
            )
            
            # 深度學習模型將在需要時動態創建
            
            # 加載已訓練模型
            await self._load_trained_models()
            
        except Exception as e:
            self.logger.error(f"模型初始化失敗: {e}")

    async def _load_trained_models(self):
        """加載已訓練的模型"""
        
        for model_file in self.model_storage_path.glob("*.pkl"):
            try:
                model_name = model_file.stem
                with open(model_file, 'rb') as f:
                    self.models[model_name] = pickle.load(f)
                self.logger.info(f"加載模型: {model_name}")
            except Exception as e:
                self.logger.warning(f"加載模型失敗 {model_file}: {e}")

    async def predict_behavior(
        self, 
        prediction_request: PredictionRequest
    ) -> BehaviorForecast:
        """預測用戶行為"""
        
        try:
            # 數據預處理
            processed_data = await self._preprocess_prediction_data(prediction_request)
            
            # 選擇預測模型
            selected_models = self._select_prediction_models(prediction_request)
            
            # 執行預測
            predictions = {}
            model_confidences = {}
            
            for model_type in selected_models:
                try:
                    pred, confidence = await self._run_single_model_prediction(
                        model_type, processed_data, prediction_request
                    )
                    predictions[model_type.value] = pred
                    model_confidences[model_type.value] = confidence
                except Exception as e:
                    self.logger.warning(f"模型 {model_type.value} 預測失敗: {e}")
            
            # 集成預測結果
            if predictions:
                forecast = await self._ensemble_predictions(
                    prediction_request, predictions, model_confidences
                )
            else:
                forecast = await self._create_fallback_forecast(prediction_request)
            
            # 緩存預測結果
            self.prediction_cache[forecast.forecast_id] = forecast
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"行為預測失敗: {e}")
            return await self._create_fallback_forecast(prediction_request)

    async def _preprocess_prediction_data(
        self, 
        request: PredictionRequest
    ) -> Dict[str, Any]:
        """預處理預測數據"""
        
        processed = {
            'user_id': request.user_id,
            'prediction_type': request.prediction_type.value,
            'prediction_horizon': request.prediction_horizon.value,
            'features': [],
            'sequence_data': [],
            'context_features': {}
        }
        
        # 處理歷史數據
        if request.historical_data:
            df = pd.DataFrame(request.historical_data)
            
            # 數值特徵
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                # 標準化數值特徵
                scaler_key = f"{request.user_id}_{request.prediction_type.value}"
                if scaler_key not in self.scalers:
                    self.scalers[scaler_key] = StandardScaler()
                    self.scalers[scaler_key].fit(df[numeric_cols])
                
                scaled_features = self.scalers[scaler_key].transform(df[numeric_cols])
                processed['features'] = scaled_features.tolist()
                
                # 時序數據(用於LSTM/Transformer)
                if len(scaled_features) > 1:
                    processed['sequence_data'] = scaled_features
        
        # 處理上下文數據
        if request.context_data:
            processed['context_features'] = self._extract_context_features(request.context_data)
        
        # 處理市場條件
        if request.market_conditions:
            market_features = self._extract_market_features(request.market_conditions)
            processed['context_features'].update(market_features)
        
        # 處理用戶狀態
        if request.user_state:
            user_features = self._extract_user_state_features(request.user_state)
            processed['context_features'].update(user_features)
        
        return processed

    def _extract_context_features(self, context_data: Dict[str, Any]) -> Dict[str, float]:
        """提取上下文特徵"""
        
        features = {}
        
        # 時間特徵
        if 'timestamp' in context_data:
            timestamp = context_data['timestamp']
            dt = datetime.fromtimestamp(timestamp)
            features['hour'] = dt.hour / 24.0
            features['day_of_week'] = dt.weekday() / 7.0
            features['month'] = dt.month / 12.0
        
        # 會話特徵
        if 'session_duration' in context_data:
            features['session_duration'] = min(context_data['session_duration'] / 3600, 1.0)
        
        if 'actions_count' in context_data:
            features['actions_count'] = min(context_data['actions_count'] / 100, 1.0)
        
        return features

    def _extract_market_features(self, market_conditions: Dict[str, Any]) -> Dict[str, float]:
        """提取市場特徵"""
        
        features = {}
        
        # 波動率特徵
        if 'volatility' in market_conditions:
            features['market_volatility'] = min(market_conditions['volatility'], 1.0)
        
        # 趨勢特徵
        if 'trend_strength' in market_conditions:
            features['trend_strength'] = max(-1.0, min(market_conditions['trend_strength'], 1.0))
        
        # 流動性特徵
        if 'liquidity_score' in market_conditions:
            features['liquidity_score'] = min(market_conditions['liquidity_score'], 1.0)
        
        return features

    def _extract_user_state_features(self, user_state: Dict[str, Any]) -> Dict[str, float]:
        """提取用戶狀態特徵"""
        
        features = {}
        
        # 情緒特徵
        if 'emotional_state' in user_state:
            emotion = user_state['emotional_state']
            features['emotional_score'] = max(-1.0, min(emotion, 1.0))
        
        # 風險偏好特徵
        if 'risk_tolerance' in user_state:
            features['risk_tolerance'] = min(user_state['risk_tolerance'], 1.0)
        
        # 經驗水平特徵
        if 'experience_level' in user_state:
            features['experience_level'] = min(user_state['experience_level'], 1.0)
        
        return features

    def _select_prediction_models(
        self, 
        request: PredictionRequest
    ) -> List[ModelType]:
        """選擇預測模型"""
        
        # 如果指定了模型偏好
        if request.model_preferences:
            return request.model_preferences
        
        # 根據預測類型和數據量選擇模型
        data_size = len(request.historical_data)
        selected_models = []
        
        if data_size >= 100:  # 大數據量
            selected_models.extend([
                ModelType.XGBOOST,
                ModelType.RANDOM_FOREST,
                ModelType.NEURAL_NETWORK
            ])
            
            if data_size >= 200:  # 時序模型需要更多數據
                selected_models.extend([ModelType.LSTM])
        
        elif data_size >= 50:  # 中等數據量
            selected_models.extend([
                ModelType.RANDOM_FOREST,
                ModelType.GRADIENT_BOOSTING
            ])
        
        else:  # 小數據量
            selected_models.extend([
                ModelType.SVM,
                ModelType.NEURAL_NETWORK
            ])
        
        # 確保至少有一個模型
        if not selected_models:
            selected_models = [ModelType.RANDOM_FOREST]
        
        return selected_models

    async def _run_single_model_prediction(
        self,
        model_type: ModelType,
        processed_data: Dict[str, Any],
        request: PredictionRequest
    ) -> Tuple[Dict[str, Any], float]:
        """運行單個模型預測"""
        
        if model_type in [ModelType.LSTM, ModelType.TRANSFORMER]:
            return await self._run_deep_learning_prediction(model_type, processed_data, request)
        else:
            return await self._run_traditional_ml_prediction(model_type, processed_data, request)

    async def _run_traditional_ml_prediction(
        self,
        model_type: ModelType,
        processed_data: Dict[str, Any],
        request: PredictionRequest
    ) -> Tuple[Dict[str, Any], float]:
        """運行傳統機器學習模型預測"""
        
        model_key = model_type.value
        
        if model_key not in self.models:
            raise ValueError(f"模型 {model_key} 未找到")
        
        model = self.models[model_key]
        
        # 準備特徵向量
        features = processed_data.get('features', [])
        context_features = processed_data.get('context_features', {})
        
        if not features:
            # 如果沒有歷史特徵，只使用上下文特徵
            feature_vector = [list(context_features.values())]
        else:
            # 結合最新的歷史特徵和上下文特徵
            latest_features = features[-1] if isinstance(features[0], list) else features
            combined_features = latest_features + list(context_features.values())
            feature_vector = [combined_features]
        
        if not hasattr(model, 'predict_proba'):
            # 如果模型未訓練，返回隨機預測
            prediction = {'predicted_class': 'unknown', 'probability': 0.5}
            confidence = 0.5
        else:
            try:
                # 執行預測
                probabilities = model.predict_proba(feature_vector)[0]
                predicted_class_idx = np.argmax(probabilities)
                predicted_class = f"behavior_class_{predicted_class_idx}"
                
                prediction = {
                    'predicted_class': predicted_class,
                    'probability': float(probabilities[predicted_class_idx]),
                    'all_probabilities': {
                        f"behavior_class_{i}": float(prob) 
                        for i, prob in enumerate(probabilities)
                    }
                }
                
                confidence = float(probabilities[predicted_class_idx])
                
            except Exception as e:
                self.logger.warning(f"模型 {model_key} 預測異常: {e}")
                prediction = {'predicted_class': 'unknown', 'probability': 0.5}
                confidence = 0.5
        
        return prediction, confidence

    async def _run_deep_learning_prediction(
        self,
        model_type: ModelType,
        processed_data: Dict[str, Any],
        request: PredictionRequest
    ) -> Tuple[Dict[str, Any], float]:
        """運行深度學習模型預測"""
        
        sequence_data = processed_data.get('sequence_data', [])
        
        if not sequence_data or len(sequence_data) < 5:
            # 序列數據不足，返回默認預測
            prediction = {'predicted_class': 'insufficient_data', 'probability': 0.3}
            return prediction, 0.3
        
        try:
            # 準備序列數據
            sequence_array = np.array(sequence_data)
            if len(sequence_array.shape) == 1:
                sequence_array = sequence_array.reshape(1, -1, 1)
            elif len(sequence_array.shape) == 2:
                sequence_array = sequence_array.reshape(1, sequence_array.shape[0], sequence_array.shape[1])
            
            # 動態創建模型(如果不存在)
            model_key = f"{model_type.value}_{request.user_id}"
            
            if model_key not in self.models:
                input_size = sequence_array.shape[2]
                
                if model_type == ModelType.LSTM:
                    self.models[model_key] = LSTMPredictor(input_size=input_size)
                elif model_type == ModelType.TRANSFORMER:
                    self.models[model_key] = TransformerPredictor(input_size=input_size)
            
            model = self.models[model_key]
            
            # 轉換為tensor
            input_tensor = torch.FloatTensor(sequence_array)
            
            # 預測
            model.eval()
            with torch.no_grad():
                output = model(input_tensor)
                probabilities = output.numpy()[0]
            
            predicted_class_idx = np.argmax(probabilities)
            predicted_class = f"behavior_sequence_{predicted_class_idx}"
            
            prediction = {
                'predicted_class': predicted_class,
                'probability': float(probabilities[predicted_class_idx]),
                'sequence_probabilities': {
                    f"behavior_sequence_{i}": float(prob) 
                    for i, prob in enumerate(probabilities)
                }
            }
            
            confidence = float(probabilities[predicted_class_idx])
            
        except Exception as e:
            self.logger.warning(f"深度學習模型 {model_type.value} 預測失敗: {e}")
            prediction = {'predicted_class': 'model_error', 'probability': 0.4}
            confidence = 0.4
        
        return prediction, confidence

    async def _ensemble_predictions(
        self,
        request: PredictionRequest,
        predictions: Dict[str, Dict[str, Any]],
        confidences: Dict[str, float]
    ) -> BehaviorForecast:
        """集成多模型預測結果"""
        
        forecast = BehaviorForecast(
            request_id=request.request_id,
            user_id=request.user_id,
            prediction_type=request.prediction_type,
            prediction_horizon=request.prediction_horizon,
            models_used=[ModelType(model_name) for model_name in predictions.keys()]
        )
        
        # 計算加權平均
        total_weight = sum(confidences.values())
        if total_weight > 0:
            weights = {model: conf / total_weight for model, conf in confidences.items()}
        else:
            weights = {model: 1/len(predictions) for model in predictions.keys()}
        
        forecast.ensemble_weight = weights
        
        # 選擇最高置信度的預測作為主要預測
        best_model = max(confidences.keys(), key=lambda x: confidences[x])
        best_prediction = predictions[best_model]
        
        forecast.predicted_behavior = best_prediction
        forecast.confidence_score = confidences[best_model]
        
        # 計算模型間一致性
        prediction_classes = [pred.get('predicted_class', '') for pred in predictions.values()]
        unique_classes = set(prediction_classes)
        if len(unique_classes) == 1:
            forecast.model_agreement = 1.0
        else:
            # 計算最常見預測的比例
            most_common_count = max(prediction_classes.count(cls) for cls in unique_classes)
            forecast.model_agreement = most_common_count / len(prediction_classes)
        
        # 計算不確定性範圍
        conf_values = list(confidences.values())
        if conf_values:
            min_conf = min(conf_values)
            max_conf = max(conf_values)
            forecast.uncertainty_range = (min_conf, max_conf)
        
        # 提取關鍵因素
        forecast.key_factors = self._extract_key_prediction_factors(request, predictions)
        
        return forecast

    def _extract_key_prediction_factors(
        self, 
        request: PredictionRequest,
        predictions: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """提取關鍵預測因素"""
        
        factors = []
        
        # 基於請求上下文的因素
        if request.context_data:
            if request.context_data.get('session_duration', 0) > 3600:
                factors.append("長時間會話")
            if request.context_data.get('actions_count', 0) > 50:
                factors.append("高活躍度")
        
        # 基於市場條件的因素
        if request.market_conditions:
            if request.market_conditions.get('volatility', 0) > 0.5:
                factors.append("高市場波動")
            if request.market_conditions.get('trend_strength', 0) > 0.7:
                factors.append("強勢趨勢")
        
        # 基於用戶狀態的因素
        if request.user_state:
            if request.user_state.get('risk_tolerance', 0) > 0.8:
                factors.append("高風險偏好")
            if request.user_state.get('emotional_state', 0) < -0.5:
                factors.append("負面情緒狀態")
        
        # 基於歷史數據的因素
        if len(request.historical_data) > 100:
            factors.append("豐富歷史數據")
        elif len(request.historical_data) < 10:
            factors.append("有限歷史數據")
        
        return factors[:5]  # 限制為最多5個關鍵因素

    async def _create_fallback_forecast(
        self, 
        request: PredictionRequest
    ) -> BehaviorForecast:
        """創建後備預測結果"""
        
        forecast = BehaviorForecast(
            request_id=request.request_id,
            user_id=request.user_id,
            prediction_type=request.prediction_type,
            prediction_horizon=request.prediction_horizon,
            predicted_behavior={'predicted_class': 'default_behavior', 'probability': 0.5},
            confidence_score=0.5,
            models_used=[],
            key_factors=["數據不足或模型不可用"]
        )
        
        return forecast

    async def validate_prediction(
        self, 
        forecast_id: str, 
        actual_outcome: Dict[str, Any]
    ):
        """驗證預測準確性"""
        
        if forecast_id not in self.prediction_cache:
            self.logger.warning(f"預測記錄 {forecast_id} 未找到")
            return
        
        forecast = self.prediction_cache[forecast_id]
        
        # 更新實際結果
        forecast.actual_outcome = actual_outcome
        forecast.validation_timestamp = time.time()
        
        # 計算預測準確性
        predicted_class = forecast.predicted_behavior.get('predicted_class', '')
        actual_class = actual_outcome.get('actual_class', '')
        
        if predicted_class == actual_class:
            forecast.prediction_accuracy = 1.0
        else:
            # 根據預測概率計算部分準確性
            predicted_prob = forecast.predicted_behavior.get('probability', 0)
            actual_prob = actual_outcome.get('actual_probability', 0)
            
            if actual_prob > 0:
                accuracy = 1.0 - abs(predicted_prob - actual_prob)
                forecast.prediction_accuracy = max(accuracy, 0.0)
            else:
                forecast.prediction_accuracy = 0.0
        
        self.logger.info(f"預測驗證完成: {forecast_id} 準確性: {forecast.prediction_accuracy:.2f}")
        
        # 更新模型性能記錄
        await self._update_model_performance(forecast)

    async def _update_model_performance(self, forecast: BehaviorForecast):
        """更新模型性能記錄"""
        
        # 這裡可以實現模型性能追蹤和自動重訓練邏輯
        if forecast.prediction_accuracy is not None:
            for model_type in forecast.models_used:
                # 記錄模型表現
                performance_key = f"{model_type.value}_{forecast.user_id}_performance"
                # 可以存儲到數據庫或文件中以用於模型改進
                pass

    def get_prediction_history(self, user_id: str) -> List[BehaviorForecast]:
        """獲取用戶預測歷史"""
        return [
            forecast for forecast in self.prediction_cache.values()
            if forecast.user_id == user_id
        ]

    def get_model_performance(self, model_type: ModelType, user_id: str = None) -> Dict[str, Any]:
        """獲取模型性能統計"""
        
        relevant_forecasts = [
            forecast for forecast in self.prediction_cache.values()
            if model_type in forecast.models_used and 
            forecast.prediction_accuracy is not None and
            (user_id is None or forecast.user_id == user_id)
        ]
        
        if not relevant_forecasts:
            return {'accuracy': 0.0, 'count': 0}
        
        accuracies = [forecast.prediction_accuracy for forecast in relevant_forecasts]
        
        return {
            'accuracy': np.mean(accuracies),
            'count': len(relevant_forecasts),
            'std': np.std(accuracies),
            'min_accuracy': np.min(accuracies),
            'max_accuracy': np.max(accuracies)
        }