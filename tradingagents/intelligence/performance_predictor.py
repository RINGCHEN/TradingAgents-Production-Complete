"""
Performance Prediction and Routing Decision System
性能預測和路由決策系統

任務6.3: 性能預測和路由決策
負責人: 小k (AI訓練專家團隊)

提供：
- 性能預測模型
- 智能路由決策
- 負載預測和容量規劃
- 性能優化建議
- 動態資源分配
"""

import os
import json
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import pickle
from collections import deque, defaultdict
import threading
import time

from .task_analyzer import TaskAnalysisResult, TaskType, TaskComplexity, ResourceRequirement
from .cost_calculator import CostComparisonResult, DeploymentMode

logger = logging.getLogger(__name__)

class PerformanceMetric(Enum):
    """性能指標枚舉"""
    THROUGHPUT = "throughput"           # 吞吐量
    LATENCY = "latency"                # 延遲
    GPU_UTILIZATION = "gpu_utilization" # GPU利用率
    MEMORY_USAGE = "memory_usage"       # 記憶體使用率
    ENERGY_EFFICIENCY = "energy_efficiency"  # 能效
    COST_EFFICIENCY = "cost_efficiency"      # 成本效率
    QUALITY_SCORE = "quality_score"          # 質量評分

class PredictionModel(Enum):
    """預測模型類型枚舉"""
    LINEAR_REGRESSION = "linear_regression"
    POLYNOMIAL_REGRESSION = "polynomial_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ARIMA = "arima"
    NEURAL_NETWORK = "neural_network"

class RoutingStrategy(Enum):
    """路由策略枚舉"""
    COST_OPTIMAL = "cost_optimal"           # 成本最優
    PERFORMANCE_OPTIMAL = "performance_optimal"  # 性能最優
    BALANCED = "balanced"                   # 平衡策略
    ADAPTIVE = "adaptive"                   # 自適應策略
    LOAD_BALANCED = "load_balanced"         # 負載均衡

@dataclass
class PerformanceData:
    """性能數據結構"""
    timestamp: datetime
    task_type: TaskType
    deployment_mode: DeploymentMode
    throughput_requests_per_hour: float
    latency_seconds: float
    gpu_utilization_percent: float
    memory_usage_percent: float
    energy_consumption_watts: float
    cost_per_request: float
    quality_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        result['task_type'] = self.task_type.value
        result['deployment_mode'] = self.deployment_mode.value
        return result

@dataclass
class PerformancePrediction:
    """性能預測結果"""
    metric: PerformanceMetric
    predicted_value: float
    confidence_interval: Tuple[float, float]
    prediction_accuracy: float
    prediction_timestamp: datetime
    prediction_horizon_hours: float
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['metric'] = self.metric.value
        result['prediction_timestamp'] = self.prediction_timestamp.isoformat()
        return result

@dataclass
class RoutingDecision:
    """路由決策結果"""
    task_id: str
    recommended_deployment: DeploymentMode
    confidence_score: float
    expected_performance: Dict[str, float]
    expected_cost: float
    decision_factors: Dict[str, float]
    alternative_options: List[Dict[str, Any]]
    decision_timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['recommended_deployment'] = self.recommended_deployment.value
        result['decision_timestamp'] = self.decision_timestamp.isoformat()
        return result

@dataclass
class LoadForecast:
    """負載預測結果"""
    forecast_timestamp: datetime
    forecast_horizon_hours: float
    predicted_load: Dict[str, float]  # 各時間點的預測負載
    peak_load_time: datetime
    peak_load_value: float
    capacity_recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['forecast_timestamp'] = self.forecast_timestamp.isoformat()
        result['peak_load_time'] = self.peak_load_time.isoformat()
        return result

class PerformancePredictor:
    """性能預測器"""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.performance_history = deque(maxlen=history_size)
        self.prediction_models = {}
        self.model_accuracy = defaultdict(float)
        self.lock = threading.Lock()
        
        # 預測模型參數
        self.smoothing_alpha = 0.3  # 指數平滑參數
        self.trend_beta = 0.1       # 趨勢平滑參數
        self.seasonal_gamma = 0.1   # 季節性平滑參數
    
    def add_performance_data(self, data: PerformanceData):
        """添加性能數據"""
        with self.lock:
            self.performance_history.append(data)
            logger.debug(f"添加性能數據: {data.task_type.value} - {data.deployment_mode.value}")
    
    def get_historical_data(
        self,
        task_type: Optional[TaskType] = None,
        deployment_mode: Optional[DeploymentMode] = None,
        hours_back: Optional[float] = None
    ) -> List[PerformanceData]:
        """獲取歷史數據"""
        with self.lock:
            filtered_data = list(self.performance_history)
        
        # 按任務類型過濾
        if task_type:
            filtered_data = [d for d in filtered_data if d.task_type == task_type]
        
        # 按部署模式過濾
        if deployment_mode:
            filtered_data = [d for d in filtered_data if d.deployment_mode == deployment_mode]
        
        # 按時間過濾
        if hours_back:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            filtered_data = [d for d in filtered_data if d.timestamp >= cutoff_time]
        
        return filtered_data
    
    def predict_performance(
        self,
        metric: PerformanceMetric,
        task_type: TaskType,
        deployment_mode: DeploymentMode,
        prediction_horizon_hours: float = 1.0,
        model_type: PredictionModel = PredictionModel.EXPONENTIAL_SMOOTHING
    ) -> PerformancePrediction:
        """預測性能指標"""
        # 獲取歷史數據
        historical_data = self.get_historical_data(task_type, deployment_mode, hours_back=168)  # 一週數據
        
        if len(historical_data) < 3:
            # 數據不足，使用默認預測
            return self._default_prediction(metric, task_type, deployment_mode, prediction_horizon_hours)
        
        # 提取指標值
        values = self._extract_metric_values(historical_data, metric)
        
        # 根據模型類型進行預測
        if model_type == PredictionModel.EXPONENTIAL_SMOOTHING:
            prediction = self._exponential_smoothing_prediction(values, prediction_horizon_hours)
        elif model_type == PredictionModel.LINEAR_REGRESSION:
            prediction = self._linear_regression_prediction(values, prediction_horizon_hours)
        elif model_type == PredictionModel.POLYNOMIAL_REGRESSION:
            prediction = self._polynomial_regression_prediction(values, prediction_horizon_hours)
        else:
            prediction = self._exponential_smoothing_prediction(values, prediction_horizon_hours)
        
        # 計算置信區間
        confidence_interval = self._calculate_confidence_interval(values, prediction, 0.95)
        
        # 評估預測準確性
        accuracy = self._evaluate_prediction_accuracy(metric, task_type, deployment_mode)
        
        return PerformancePrediction(
            metric=metric,
            predicted_value=prediction,
            confidence_interval=confidence_interval,
            prediction_accuracy=accuracy,
            prediction_timestamp=datetime.now(),
            prediction_horizon_hours=prediction_horizon_hours
        )
    
    def _extract_metric_values(self, data: List[PerformanceData], metric: PerformanceMetric) -> List[float]:
        """提取指標值"""
        if metric == PerformanceMetric.THROUGHPUT:
            return [d.throughput_requests_per_hour for d in data]
        elif metric == PerformanceMetric.LATENCY:
            return [d.latency_seconds for d in data]
        elif metric == PerformanceMetric.GPU_UTILIZATION:
            return [d.gpu_utilization_percent for d in data]
        elif metric == PerformanceMetric.MEMORY_USAGE:
            return [d.memory_usage_percent for d in data]
        elif metric == PerformanceMetric.ENERGY_EFFICIENCY:
            return [d.throughput_requests_per_hour / d.energy_consumption_watts if d.energy_consumption_watts > 0 else 0 for d in data]
        elif metric == PerformanceMetric.COST_EFFICIENCY:
            return [1 / d.cost_per_request if d.cost_per_request > 0 else 0 for d in data]
        elif metric == PerformanceMetric.QUALITY_SCORE:
            return [d.quality_score for d in data]
        else:
            return [0.0] * len(data)
    
    def _exponential_smoothing_prediction(self, values: List[float], horizon_hours: float) -> float:
        """指數平滑預測"""
        if not values:
            return 0.0
        
        # 簡單指數平滑
        smoothed = values[0]
        for value in values[1:]:
            smoothed = self.smoothing_alpha * value + (1 - self.smoothing_alpha) * smoothed
        
        # 考慮趨勢
        if len(values) >= 2:
            trend = (values[-1] - values[-2]) * self.trend_beta
            prediction = smoothed + trend * horizon_hours
        else:
            prediction = smoothed
        
        return max(0, prediction)  # 確保非負值
    
    def _linear_regression_prediction(self, values: List[float], horizon_hours: float) -> float:
        """線性回歸預測"""
        if len(values) < 2:
            return values[0] if values else 0.0
        
        # 簡單線性回歸
        n = len(values)
        x = np.arange(n)
        y = np.array(values)
        
        # 計算斜率和截距
        x_mean = np.mean(x)
        y_mean = np.mean(y)
        
        numerator = np.sum((x - x_mean) * (y - y_mean))
        denominator = np.sum((x - x_mean) ** 2)
        
        if denominator == 0:
            return y_mean
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # 預測
        future_x = n + horizon_hours - 1
        prediction = slope * future_x + intercept
        
        return max(0, prediction)
    
    def _polynomial_regression_prediction(self, values: List[float], horizon_hours: float) -> float:
        """多項式回歸預測"""
        if len(values) < 3:
            return self._linear_regression_prediction(values, horizon_hours)
        
        # 二次多項式擬合
        x = np.arange(len(values))
        y = np.array(values)
        
        try:
            coeffs = np.polyfit(x, y, 2)
            future_x = len(values) + horizon_hours - 1
            prediction = np.polyval(coeffs, future_x)
            return max(0, prediction)
        except:
            # 如果多項式擬合失敗，回退到線性回歸
            return self._linear_regression_prediction(values, horizon_hours)
    
    def _calculate_confidence_interval(
        self,
        values: List[float],
        prediction: float,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """計算置信區間"""
        if len(values) < 2:
            margin = prediction * 0.1  # 10%的邊際
            return (max(0, prediction - margin), prediction + margin)
        
        # 計算標準差
        std_dev = np.std(values)
        
        # 計算置信區間
        z_score = 1.96 if confidence_level == 0.95 else 2.58  # 95%或99%置信度
        margin = z_score * std_dev / np.sqrt(len(values))
        
        lower_bound = max(0, prediction - margin)
        upper_bound = prediction + margin
        
        return (lower_bound, upper_bound)
    
    def _evaluate_prediction_accuracy(
        self,
        metric: PerformanceMetric,
        task_type: TaskType,
        deployment_mode: DeploymentMode
    ) -> float:
        """評估預測準確性"""
        key = f"{metric.value}_{task_type.value}_{deployment_mode.value}"
        
        # 如果有歷史準確性記錄，返回該值
        if key in self.model_accuracy:
            return self.model_accuracy[key]
        
        # 否則返回默認準確性
        return 0.8  # 80%的默認準確性
    
    def _default_prediction(
        self,
        metric: PerformanceMetric,
        task_type: TaskType,
        deployment_mode: DeploymentMode,
        prediction_horizon_hours: float
    ) -> PerformancePrediction:
        """默認預測（當數據不足時）"""
        # 基於任務類型和部署模式的默認值
        default_values = {
            (PerformanceMetric.THROUGHPUT, TaskType.TRAINING, DeploymentMode.LOCAL_GPU): 50.0,
            (PerformanceMetric.THROUGHPUT, TaskType.INFERENCE, DeploymentMode.LOCAL_GPU): 200.0,
            (PerformanceMetric.LATENCY, TaskType.TRAINING, DeploymentMode.LOCAL_GPU): 2.0,
            (PerformanceMetric.LATENCY, TaskType.INFERENCE, DeploymentMode.LOCAL_GPU): 0.5,
            (PerformanceMetric.GPU_UTILIZATION, TaskType.TRAINING, DeploymentMode.LOCAL_GPU): 85.0,
            (PerformanceMetric.MEMORY_USAGE, TaskType.TRAINING, DeploymentMode.LOCAL_GPU): 70.0,
        }
        
        key = (metric, task_type, deployment_mode)
        default_value = default_values.get(key, 50.0)
        
        return PerformancePrediction(
            metric=metric,
            predicted_value=default_value,
            confidence_interval=(default_value * 0.8, default_value * 1.2),
            prediction_accuracy=0.6,  # 較低的準確性，因為是默認值
            prediction_timestamp=datetime.now(),
            prediction_horizon_hours=prediction_horizon_hours
        )

class LoadForecaster:
    """負載預測器"""
    
    def __init__(self):
        self.load_history = deque(maxlen=2000)  # 保存更多負載歷史
        self.seasonal_patterns = {}  # 季節性模式
        self.lock = threading.Lock()
    
    def add_load_data(self, timestamp: datetime, load_value: float, task_type: TaskType):
        """添加負載數據"""
        with self.lock:
            self.load_history.append({
                'timestamp': timestamp,
                'load': load_value,
                'task_type': task_type,
                'hour_of_day': timestamp.hour,
                'day_of_week': timestamp.weekday(),
                'day_of_month': timestamp.day
            })
    
    def forecast_load(
        self,
        forecast_horizon_hours: float = 24.0,
        task_type: Optional[TaskType] = None
    ) -> LoadForecast:
        """預測負載"""
        with self.lock:
            historical_data = list(self.load_history)
        
        # 過濾任務類型
        if task_type:
            historical_data = [d for d in historical_data if d['task_type'] == task_type]
        
        if len(historical_data) < 24:  # 至少需要24小時的數據
            return self._default_load_forecast(forecast_horizon_hours)
        
        # 分析季節性模式
        hourly_patterns = self._analyze_hourly_patterns(historical_data)
        daily_patterns = self._analyze_daily_patterns(historical_data)
        
        # 生成預測
        forecast_points = {}
        current_time = datetime.now()
        
        for i in range(int(forecast_horizon_hours)):
            future_time = current_time + timedelta(hours=i)
            
            # 基於小時模式預測
            hour_factor = hourly_patterns.get(future_time.hour, 1.0)
            
            # 基於星期模式預測
            day_factor = daily_patterns.get(future_time.weekday(), 1.0)
            
            # 基礎負載（最近的平均值）
            recent_loads = [d['load'] for d in historical_data[-24:]]  # 最近24小時
            base_load = np.mean(recent_loads) if recent_loads else 50.0
            
            # 組合預測
            predicted_load = base_load * hour_factor * day_factor
            forecast_points[future_time.isoformat()] = predicted_load
        
        # 找到峰值負載
        peak_load_value = max(forecast_points.values())
        peak_load_time = max(forecast_points.keys(), key=lambda k: forecast_points[k])
        peak_load_time = datetime.fromisoformat(peak_load_time)
        
        # 生成容量建議
        capacity_recommendations = self._generate_capacity_recommendations(
            forecast_points, peak_load_value
        )
        
        return LoadForecast(
            forecast_timestamp=datetime.now(),
            forecast_horizon_hours=forecast_horizon_hours,
            predicted_load=forecast_points,
            peak_load_time=peak_load_time,
            peak_load_value=peak_load_value,
            capacity_recommendations=capacity_recommendations
        )
    
    def _analyze_hourly_patterns(self, data: List[Dict]) -> Dict[int, float]:
        """分析小時模式"""
        hourly_loads = defaultdict(list)
        
        for record in data:
            hourly_loads[record['hour_of_day']].append(record['load'])
        
        # 計算每小時的平均負載係數
        overall_mean = np.mean([record['load'] for record in data])
        hourly_factors = {}
        
        for hour in range(24):
            if hour in hourly_loads:
                hour_mean = np.mean(hourly_loads[hour])
                hourly_factors[hour] = hour_mean / overall_mean if overall_mean > 0 else 1.0
            else:
                hourly_factors[hour] = 1.0
        
        return hourly_factors
    
    def _analyze_daily_patterns(self, data: List[Dict]) -> Dict[int, float]:
        """分析每日模式"""
        daily_loads = defaultdict(list)
        
        for record in data:
            daily_loads[record['day_of_week']].append(record['load'])
        
        # 計算每天的平均負載係數
        overall_mean = np.mean([record['load'] for record in data])
        daily_factors = {}
        
        for day in range(7):  # 0=Monday, 6=Sunday
            if day in daily_loads:
                day_mean = np.mean(daily_loads[day])
                daily_factors[day] = day_mean / overall_mean if overall_mean > 0 else 1.0
            else:
                daily_factors[day] = 1.0
        
        return daily_factors
    
    def _generate_capacity_recommendations(
        self,
        forecast_points: Dict[str, float],
        peak_load: float
    ) -> List[str]:
        """生成容量建議"""
        recommendations = []
        
        # 分析負載變化
        loads = list(forecast_points.values())
        avg_load = np.mean(loads)
        load_variance = np.var(loads)
        
        if peak_load > avg_load * 1.5:
            recommendations.append("檢測到高峰負載，建議增加計算資源")
        
        if load_variance > avg_load * 0.5:
            recommendations.append("負載波動較大，建議實施自動擴縮容")
        
        if peak_load > 100:  # 假設100是高負載閾值
            recommendations.append("預測負載較高，建議提前準備額外的GPU資源")
        
        if avg_load < 20:  # 假設20是低負載閾值
            recommendations.append("預測負載較低，可以考慮資源整合以節省成本")
        
        return recommendations
    
    def _default_load_forecast(self, forecast_horizon_hours: float) -> LoadForecast:
        """默認負載預測"""
        # 生成簡單的負載模式（工作時間高，非工作時間低）
        forecast_points = {}
        current_time = datetime.now()
        
        for i in range(int(forecast_horizon_hours)):
            future_time = current_time + timedelta(hours=i)
            
            # 簡單的工作時間模式
            if 9 <= future_time.hour <= 17:  # 工作時間
                load = 80.0
            elif 18 <= future_time.hour <= 22:  # 晚上
                load = 60.0
            else:  # 深夜和早晨
                load = 30.0
            
            forecast_points[future_time.isoformat()] = load
        
        peak_load_value = max(forecast_points.values())
        peak_load_time = max(forecast_points.keys(), key=lambda k: forecast_points[k])
        peak_load_time = datetime.fromisoformat(peak_load_time)
        
        return LoadForecast(
            forecast_timestamp=datetime.now(),
            forecast_horizon_hours=forecast_horizon_hours,
            predicted_load=forecast_points,
            peak_load_time=peak_load_time,
            peak_load_value=peak_load_value,
            capacity_recommendations=["使用默認負載模式，建議收集更多歷史數據以提高預測準確性"]
        )

class RoutingDecisionEngine:
    """路由決策引擎"""
    
    def __init__(self):
        self.performance_predictor = PerformancePredictor()
        self.load_forecaster = LoadForecaster()
        self.decision_history = deque(maxlen=1000)
        self.strategy_weights = {
            RoutingStrategy.COST_OPTIMAL: {'cost': 0.8, 'performance': 0.2},
            RoutingStrategy.PERFORMANCE_OPTIMAL: {'cost': 0.2, 'performance': 0.8},
            RoutingStrategy.BALANCED: {'cost': 0.5, 'performance': 0.5},
            RoutingStrategy.ADAPTIVE: {'cost': 0.4, 'performance': 0.4, 'load': 0.2}
        }
    
    def make_routing_decision(
        self,
        task_analysis: TaskAnalysisResult,
        cost_comparison: CostComparisonResult,
        strategy: RoutingStrategy = RoutingStrategy.BALANCED,
        current_load: Optional[float] = None
    ) -> RoutingDecision:
        """做出路由決策"""
        logger.info(f"🎯 開始路由決策: {task_analysis.task_name}")
        
        # 預測各部署模式的性能
        performance_predictions = self._predict_deployment_performance(task_analysis)
        
        # 計算決策因素
        decision_factors = self._calculate_decision_factors(
            task_analysis, cost_comparison, performance_predictions, current_load
        )
        
        # 根據策略計算評分
        deployment_scores = self._calculate_deployment_scores(
            decision_factors, strategy
        )
        
        # 選擇最佳部署模式
        recommended_deployment = max(deployment_scores, key=deployment_scores.get)
        confidence_score = deployment_scores[recommended_deployment]
        
        # 生成替代選項
        alternative_options = self._generate_alternatives(deployment_scores, decision_factors)
        
        # 預期性能和成本
        expected_performance = performance_predictions.get(recommended_deployment, {})
        expected_cost = self._get_expected_cost(cost_comparison, recommended_deployment)
        
        decision = RoutingDecision(
            task_id=task_analysis.task_id,
            recommended_deployment=recommended_deployment,
            confidence_score=confidence_score,
            expected_performance=expected_performance,
            expected_cost=expected_cost,
            decision_factors=decision_factors,
            alternative_options=alternative_options,
            decision_timestamp=datetime.now()
        )
        
        # 記錄決策歷史
        self.decision_history.append(decision)
        
        logger.info(f"✅ 路由決策完成: {recommended_deployment.value}, 信心度: {confidence_score:.2f}")
        return decision
    
    def _predict_deployment_performance(
        self,
        task_analysis: TaskAnalysisResult
    ) -> Dict[DeploymentMode, Dict[str, float]]:
        """預測各部署模式的性能"""
        predictions = {}
        
        for deployment_mode in [DeploymentMode.LOCAL_GPU, DeploymentMode.CLOUD_API, DeploymentMode.HYBRID]:
            mode_predictions = {}
            
            # 預測各項性能指標
            for metric in [PerformanceMetric.THROUGHPUT, PerformanceMetric.LATENCY, 
                          PerformanceMetric.GPU_UTILIZATION, PerformanceMetric.QUALITY_SCORE]:
                try:
                    prediction = self.performance_predictor.predict_performance(
                        metric, task_analysis.task_type, deployment_mode
                    )
                    mode_predictions[metric.value] = prediction.predicted_value
                except Exception as e:
                    logger.warning(f"性能預測失敗 {metric.value}: {e}")
                    mode_predictions[metric.value] = 0.0
            
            predictions[deployment_mode] = mode_predictions
        
        return predictions
    
    def _calculate_decision_factors(
        self,
        task_analysis: TaskAnalysisResult,
        cost_comparison: CostComparisonResult,
        performance_predictions: Dict[DeploymentMode, Dict[str, float]],
        current_load: Optional[float]
    ) -> Dict[str, float]:
        """計算決策因素"""
        factors = {}
        
        # 成本因素
        factors['local_gpu_cost'] = float(cost_comparison.local_gpu_cost.total_cost)
        factors['cloud_api_cost'] = float(cost_comparison.cloud_api_cost.total_cost)
        factors['hybrid_cost'] = float(cost_comparison.hybrid_cost.total_cost)
        factors['cost_savings'] = float(cost_comparison.cost_savings)
        
        # 性能因素
        for deployment_mode in performance_predictions:
            prefix = deployment_mode.value
            perf_data = performance_predictions[deployment_mode]
            
            factors[f'{prefix}_throughput'] = perf_data.get('throughput', 0.0)
            factors[f'{prefix}_latency'] = perf_data.get('latency', 0.0)
            factors[f'{prefix}_gpu_utilization'] = perf_data.get('gpu_utilization', 0.0)
            factors[f'{prefix}_quality_score'] = perf_data.get('quality_score', 0.0)
        
        # 任務特性因素
        factors['task_complexity'] = task_analysis.complexity.value
        factors['task_priority'] = task_analysis.priority.value
        factors['estimated_duration'] = task_analysis.estimated_duration
        factors['analysis_confidence'] = task_analysis.analysis_confidence
        
        # 資源需求因素
        req = task_analysis.resource_requirements
        factors['gpu_memory_requirement'] = req.gpu_memory_gb
        factors['cpu_cores_requirement'] = req.cpu_cores
        factors['estimated_time_requirement'] = req.estimated_time_hours
        
        # 當前負載因素
        factors['current_load'] = current_load if current_load is not None else 50.0
        
        # 風險因素
        factors['risk_count'] = len(task_analysis.risk_factors)
        factors['has_high_complexity_risk'] = 1.0 if 'high_complexity_risk' in task_analysis.risk_factors else 0.0
        factors['has_resource_risk'] = 1.0 if 'resource_risk' in task_analysis.risk_factors else 0.0
        
        return factors
    
    def _calculate_deployment_scores(
        self,
        factors: Dict[str, float],
        strategy: RoutingStrategy
    ) -> Dict[DeploymentMode, float]:
        """計算各部署模式的評分"""
        scores = {}
        
        for deployment_mode in [DeploymentMode.LOCAL_GPU, DeploymentMode.CLOUD_API, DeploymentMode.HYBRID]:
            score = 0.0
            
            if strategy == RoutingStrategy.COST_OPTIMAL:
                # 成本最優策略
                if deployment_mode == DeploymentMode.LOCAL_GPU:
                    score = 1.0 / (factors['local_gpu_cost'] + 1.0)
                elif deployment_mode == DeploymentMode.CLOUD_API:
                    score = 1.0 / (factors['cloud_api_cost'] + 1.0)
                else:  # HYBRID
                    score = 1.0 / (factors['hybrid_cost'] + 1.0)
                
                # 考慮成本節省
                if factors['cost_savings'] > 0:
                    score *= 1.2
            
            elif strategy == RoutingStrategy.PERFORMANCE_OPTIMAL:
                # 性能最優策略
                prefix = deployment_mode.value
                throughput = factors.get(f'{prefix}_throughput', 0.0)
                latency = factors.get(f'{prefix}_latency', 1.0)
                quality = factors.get(f'{prefix}_quality_score', 0.0)
                
                # 吞吐量越高越好，延遲越低越好，質量越高越好
                score = (throughput * 0.4) + (1.0 / (latency + 0.1) * 0.3) + (quality * 0.3)
            
            elif strategy == RoutingStrategy.BALANCED:
                # 平衡策略
                # 成本評分（成本越低評分越高）
                if deployment_mode == DeploymentMode.LOCAL_GPU:
                    cost_score = 1.0 / (factors['local_gpu_cost'] + 1.0)
                elif deployment_mode == DeploymentMode.CLOUD_API:
                    cost_score = 1.0 / (factors['cloud_api_cost'] + 1.0)
                else:
                    cost_score = 1.0 / (factors['hybrid_cost'] + 1.0)
                
                # 性能評分
                prefix = deployment_mode.value
                throughput = factors.get(f'{prefix}_throughput', 0.0)
                latency = factors.get(f'{prefix}_latency', 1.0)
                quality = factors.get(f'{prefix}_quality_score', 0.0)
                
                perf_score = (throughput * 0.4) + (1.0 / (latency + 0.1) * 0.3) + (quality * 0.3)
                
                # 平衡成本和性能
                score = cost_score * 0.5 + perf_score * 0.5
            
            elif strategy == RoutingStrategy.ADAPTIVE:
                # 自適應策略
                # 根據任務特性動態調整權重
                task_priority = factors['task_priority']
                current_load = factors['current_load']
                
                # 高優先級任務更注重性能
                if task_priority >= 4:  # URGENT或CRITICAL
                    perf_weight = 0.7
                    cost_weight = 0.3
                else:
                    perf_weight = 0.4
                    cost_weight = 0.6
                
                # 高負載時更注重成本效率
                if current_load > 80:
                    cost_weight += 0.1
                    perf_weight -= 0.1
                
                # 計算評分
                if deployment_mode == DeploymentMode.LOCAL_GPU:
                    cost_score = 1.0 / (factors['local_gpu_cost'] + 1.0)
                elif deployment_mode == DeploymentMode.CLOUD_API:
                    cost_score = 1.0 / (factors['cloud_api_cost'] + 1.0)
                else:
                    cost_score = 1.0 / (factors['hybrid_cost'] + 1.0)
                
                prefix = deployment_mode.value
                throughput = factors.get(f'{prefix}_throughput', 0.0)
                latency = factors.get(f'{prefix}_latency', 1.0)
                quality = factors.get(f'{prefix}_quality_score', 0.0)
                
                perf_score = (throughput * 0.4) + (1.0 / (latency + 0.1) * 0.3) + (quality * 0.3)
                
                score = cost_score * cost_weight + perf_score * perf_weight
            
            else:  # LOAD_BALANCED
                # 負載均衡策略
                current_load = factors['current_load']
                
                # 根據當前負載選擇部署模式
                if current_load < 30:  # 低負載
                    if deployment_mode == DeploymentMode.LOCAL_GPU:
                        score = 0.8
                    else:
                        score = 0.6
                elif current_load > 80:  # 高負載
                    if deployment_mode == DeploymentMode.HYBRID:
                        score = 0.9
                    elif deployment_mode == DeploymentMode.CLOUD_API:
                        score = 0.7
                    else:
                        score = 0.5
                else:  # 中等負載
                    if deployment_mode == DeploymentMode.HYBRID:
                        score = 0.8
                    else:
                        score = 0.7
            
            # 應用風險調整
            if factors['has_high_complexity_risk'] > 0:
                if deployment_mode == DeploymentMode.LOCAL_GPU:
                    score *= 0.9  # 本地GPU對高複雜度任務風險較高
            
            if factors['has_resource_risk'] > 0:
                if deployment_mode == DeploymentMode.CLOUD_API:
                    score *= 1.1  # 雲端API對資源風險更有彈性
            
            scores[deployment_mode] = max(0.0, min(1.0, score))  # 限制在0-1範圍內
        
        return scores
    
    def _generate_alternatives(
        self,
        deployment_scores: Dict[DeploymentMode, float],
        decision_factors: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """生成替代選項"""
        alternatives = []
        
        # 按評分排序
        sorted_deployments = sorted(deployment_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 生成前3個選項的詳細信息
        for i, (deployment_mode, score) in enumerate(sorted_deployments[:3]):
            if i == 0:
                continue  # 跳過推薦選項
            
            alternative = {
                'deployment_mode': deployment_mode.value,
                'score': score,
                'rank': i + 1,
                'pros': [],
                'cons': [],
                'use_cases': []
            }
            
            # 根據部署模式添加優缺點
            if deployment_mode == DeploymentMode.LOCAL_GPU:
                alternative['pros'] = ['低延遲', '數據隱私', '長期成本效益']
                alternative['cons'] = ['高初始投資', '維護成本', '硬體限制']
                alternative['use_cases'] = ['高頻訓練任務', '敏感數據處理', '長期運行項目']
            elif deployment_mode == DeploymentMode.CLOUD_API:
                alternative['pros'] = ['無初始投資', '彈性擴展', '免維護']
                alternative['cons'] = ['按使用付費', '網路延遲', '數據傳輸成本']
                alternative['use_cases'] = ['短期項目', '不定期任務', '快速原型開發']
            else:  # HYBRID
                alternative['pros'] = ['平衡成本性能', '風險分散', '彈性調配']
                alternative['cons'] = ['複雜管理', '雙重成本', '協調開銷']
                alternative['use_cases'] = ['混合工作負載', '峰值處理', '漸進式遷移']
            
            alternatives.append(alternative)
        
        return alternatives
    
    def _get_expected_cost(
        self,
        cost_comparison: CostComparisonResult,
        deployment_mode: DeploymentMode
    ) -> float:
        """獲取預期成本"""
        if deployment_mode == DeploymentMode.LOCAL_GPU:
            return float(cost_comparison.local_gpu_cost.total_cost)
        elif deployment_mode == DeploymentMode.CLOUD_API:
            return float(cost_comparison.cloud_api_cost.total_cost)
        else:  # HYBRID
            return float(cost_comparison.hybrid_cost.total_cost)
    
    def get_decision_analytics(self) -> Dict[str, Any]:
        """獲取決策分析"""
        if not self.decision_history:
            return {"message": "No decision history available"}
        
        # 統計決策分佈
        deployment_counts = defaultdict(int)
        strategy_performance = defaultdict(list)
        
        for decision in self.decision_history:
            deployment_counts[decision.recommended_deployment.value] += 1
            strategy_performance['confidence'].append(decision.confidence_score)
        
        # 計算平均信心度
        avg_confidence = np.mean(strategy_performance['confidence']) if strategy_performance['confidence'] else 0.0
        
        return {
            "total_decisions": len(self.decision_history),
            "deployment_distribution": dict(deployment_counts),
            "average_confidence": avg_confidence,
            "recent_decisions": [d.to_dict() for d in list(self.decision_history)[-5:]],
            "analysis_timestamp": datetime.now().isoformat()
        }

# 便利函數
def create_performance_data_sample(
    task_type: TaskType = TaskType.TRAINING,
    deployment_mode: DeploymentMode = DeploymentMode.LOCAL_GPU
) -> PerformanceData:
    """創建性能數據樣本"""
    return PerformanceData(
        timestamp=datetime.now(),
        task_type=task_type,
        deployment_mode=deployment_mode,
        throughput_requests_per_hour=100.0,
        latency_seconds=2.0,
        gpu_utilization_percent=85.0,
        memory_usage_percent=70.0,
        energy_consumption_watts=200.0,
        cost_per_request=0.05,
        quality_score=0.9
    )

def quick_routing_decision(
    task_name: str,
    task_description: str,
    strategy: RoutingStrategy = RoutingStrategy.BALANCED
) -> RoutingDecision:
    """快速路由決策的便利函數"""
    from .task_analyzer import analyze_single_task
    from .cost_calculator import quick_cost_comparison
    
    # 分析任務
    task_analysis = analyze_single_task(task_name, task_description)
    
    # 成本對比
    cost_comparison = quick_cost_comparison()
    
    # 路由決策
    decision_engine = RoutingDecisionEngine()
    return decision_engine.make_routing_decision(
        task_analysis, cost_comparison, strategy
    )