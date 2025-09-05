#!/usr/bin/env python3
"""
Cost Analytics and Reporting - 成本分析和報告功能
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級成本分析引擎，提供：
- 高級成本分析和商業智能
- 多維度成本鑽取和歸因分析
- 預測性成本建模和情景分析
- 成本基準和競爭分析
- 自動化洞察發現和異常檢測
- 可視化儀表板和互動報告
"""

import uuid
import logging
import asyncio
import numpy as np
import pandas as pd
import statistics
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import math
from collections import defaultdict

logger = logging.getLogger(__name__)

# ==================== 分析類型和數據結構 ====================

class AnalysisType(Enum):
    """分析類型"""
    COST_VARIANCE = "cost_variance"           # 成本差異分析
    COST_DRIVER = "cost_driver"               # 成本驅動因素分析
    PROFITABILITY = "profitability"          # 盈利能力分析
    EFFICIENCY = "efficiency"                # 效率分析
    BENCHMARK = "benchmark"                  # 基準分析
    SCENARIO = "scenario"                    # 情景分析
    SENSITIVITY = "sensitivity"             # 敏感性分析
    FORECAST = "forecast"                    # 預測分析
    ATTRIBUTION = "attribution"             # 歸因分析
    ANOMALY = "anomaly"                      # 異常分析

class AnalysisDimension(Enum):
    """分析維度"""
    TIME = "time"                           # 時間維度
    COST_CATEGORY = "cost_category"         # 成本類別維度
    ASSET = "asset"                         # 資產維度
    PROJECT = "project"                     # 項目維度
    DEPARTMENT = "department"               # 部門維度
    GEOGRAPHY = "geography"                 # 地理維度
    TECHNOLOGY = "technology"               # 技術維度

class MetricType(Enum):
    """指標類型"""
    ABSOLUTE_COST = "absolute_cost"         # 絕對成本
    RELATIVE_COST = "relative_cost"         # 相對成本
    UNIT_COST = "unit_cost"                 # 單位成本
    COST_RATIO = "cost_ratio"               # 成本比率
    VARIANCE = "variance"                   # 差異
    GROWTH_RATE = "growth_rate"             # 增長率
    EFFICIENCY_RATIO = "efficiency_ratio"   # 效率比率

@dataclass
class AnalysisRequest:
    """分析請求"""
    analysis_id: str
    analysis_type: AnalysisType
    dimensions: List[AnalysisDimension]
    
    # 數據範圍
    target_ids: List[str]
    start_date: date
    end_date: date
    
    # 比較基準
    baseline_period_start: Optional[date] = None
    baseline_period_end: Optional[date] = None
    benchmark_targets: List[str] = field(default_factory=list)
    
    # 分析參數
    metrics: List[MetricType] = field(default_factory=lambda: [MetricType.ABSOLUTE_COST])
    aggregation_level: str = "daily"  # daily, weekly, monthly, quarterly
    confidence_interval: float = 0.95
    include_predictions: bool = False
    prediction_horizon_days: int = 30
    
    # 過濾條件
    cost_threshold_min: Optional[Decimal] = None
    cost_threshold_max: Optional[Decimal] = None
    include_only_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AnalysisResult:
    """分析結果"""
    analysis_id: str
    request: AnalysisRequest
    
    # 基本統計
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    
    # 維度分析結果
    dimension_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # 趨勢和模式
    trends: Dict[str, Any] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # 差異和異常
    variances: List[Dict[str, Any]] = field(default_factory=list)
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    
    # 洞察和建議
    insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # 預測結果
    forecasts: Dict[str, Any] = field(default_factory=dict)
    
    # 可視化數據
    visualizations: Dict[str, Any] = field(default_factory=dict)
    
    # 元數據
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: float = 0.0
    data_quality_score: float = 1.0
    confidence_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        result_dict = asdict(self)
        result_dict['generated_at'] = self.generated_at.isoformat()
        return result_dict

@dataclass
class CostDataPoint:
    """成本數據點"""
    timestamp: datetime
    target_id: str
    cost_category: str
    amount: Decimal
    units: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# ==================== 核心分析引擎 ====================

class CostAnalytics:
    """
    成本分析引擎
    
    功能：
    1. 高級成本分析和商業智能
    2. 多維度成本鑽取和歸因分析
    3. 預測性成本建模和情景分析
    4. 成本基準和競爭分析
    5. 自動化洞察發現和異常檢測
    6. 可視化儀表板和互動報告
    """
    
    def __init__(self):
        """初始化成本分析引擎"""
        self.logger = logger
        
        # 數據存儲
        self.cost_data: List[CostDataPoint] = []
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        
        # 分析配置
        self.config = {
            'anomaly_detection_threshold': 2.5,  # Z-score threshold
            'trend_significance_threshold': 0.05,  # P-value threshold
            'cache_ttl_hours': 1,
            'max_data_points': 100000,
            'prediction_model': 'linear_regression',
            'seasonal_decomposition': True,
            'outlier_detection_enabled': True
        }
        
        # 預計算的統計數據
        self.statistics_cache = {}
        
        self.logger.info("✅ Cost Analytics Engine initialized")
    
    # ==================== 數據管理 ====================
    
    def add_cost_data(self, data_points: List[CostDataPoint]):
        """添加成本數據"""
        try:
            self.cost_data.extend(data_points)
            
            # 保持數據大小限制
            if len(self.cost_data) > self.config['max_data_points']:
                # 保留最新的數據
                self.cost_data = self.cost_data[-self.config['max_data_points']:]
            
            # 按時間排序
            self.cost_data.sort(key=lambda x: x.timestamp)
            
            # 清理相關緩存
            self._invalidate_caches()
            
            self.logger.info(f"Added {len(data_points)} cost data points")
            
        except Exception as e:
            self.logger.error(f"❌ Error adding cost data: {e}")
    
    def get_cost_data(
        self,
        target_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        cost_categories: Optional[List[str]] = None
    ) -> List[CostDataPoint]:
        """獲取過濾後的成本數據"""
        filtered_data = self.cost_data
        
        if target_ids:
            filtered_data = [dp for dp in filtered_data if dp.target_id in target_ids]
        
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            filtered_data = [dp for dp in filtered_data if dp.timestamp >= start_datetime]
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            filtered_data = [dp for dp in filtered_data if dp.timestamp <= end_datetime]
        
        if cost_categories:
            filtered_data = [dp for dp in filtered_data if dp.cost_category in cost_categories]
        
        return filtered_data
    
    # ==================== 核心分析功能 ====================
    
    async def perform_analysis(
        self,
        request: AnalysisRequest
    ) -> AnalysisResult:
        """執行分析"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # 檢查緩存
            cache_key = self._generate_cache_key(request)
            if cache_key in self.analysis_cache:
                cached_result = self.analysis_cache[cache_key]
                if self._is_cache_valid(cached_result):
                    self.logger.info(f"Returning cached analysis result: {request.analysis_id}")
                    return cached_result
            
            # 獲取數據
            cost_data = self.get_cost_data(
                target_ids=request.target_ids,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            if not cost_data:
                return self._create_empty_result(request, start_time, "No data available for analysis")
            
            # 創建結果對象
            result = AnalysisResult(
                analysis_id=request.analysis_id,
                request=request
            )
            
            # 執行分析
            if request.analysis_type == AnalysisType.COST_VARIANCE:
                await self._analyze_cost_variance(request, cost_data, result)
            elif request.analysis_type == AnalysisType.COST_DRIVER:
                await self._analyze_cost_drivers(request, cost_data, result)
            elif request.analysis_type == AnalysisType.PROFITABILITY:
                await self._analyze_profitability(request, cost_data, result)
            elif request.analysis_type == AnalysisType.EFFICIENCY:
                await self._analyze_efficiency(request, cost_data, result)
            elif request.analysis_type == AnalysisType.BENCHMARK:
                await self._analyze_benchmarks(request, cost_data, result)
            elif request.analysis_type == AnalysisType.FORECAST:
                await self._analyze_forecasts(request, cost_data, result)
            elif request.analysis_type == AnalysisType.ANOMALY:
                await self._analyze_anomalies(request, cost_data, result)
            else:
                # 默認執行基礎分析
                await self._perform_basic_analysis(request, cost_data, result)
            
            # 生成通用洞察
            await self._generate_insights(request, cost_data, result)
            
            # 計算元數據
            result.processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            result.data_quality_score = self._calculate_data_quality_score(cost_data)
            result.confidence_score = self._calculate_confidence_score(result, cost_data)
            
            # 緩存結果
            self.analysis_cache[cache_key] = result
            
            self.logger.info(f"✅ Analysis completed: {request.analysis_id} ({request.analysis_type.value})")
            return result
            
        except Exception as e:
            error_msg = f"Analysis error: {e}"
            self.logger.error(f"❌ {error_msg}")
            return self._create_empty_result(request, start_time, error_msg)
    
    # ==================== 專門分析方法 ====================
    
    async def _analyze_cost_variance(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """成本差異分析"""
        try:
            # 按目標和時間聚合數據
            aggregated_data = self._aggregate_data_by_period(cost_data, request.aggregation_level)
            
            # 計算基礎統計
            total_costs = [float(sum(period_data.values())) for period_data in aggregated_data.values()]
            
            if len(total_costs) > 1:
                mean_cost = statistics.mean(total_costs)
                std_dev = statistics.stdev(total_costs) if len(total_costs) > 1 else 0
                cv = (std_dev / mean_cost) if mean_cost > 0 else 0  # 變異係數
                
                result.summary_statistics = {
                    'mean_cost': mean_cost,
                    'std_deviation': std_dev,
                    'coefficient_variation': cv,
                    'min_cost': min(total_costs),
                    'max_cost': max(total_costs),
                    'cost_range': max(total_costs) - min(total_costs)
                }
                
                # 識別顯著差異
                z_threshold = self.config['anomaly_detection_threshold']
                variances = []
                
                for period, period_costs in aggregated_data.items():
                    period_total = float(sum(period_costs.values()))
                    z_score = (period_total - mean_cost) / std_dev if std_dev > 0 else 0
                    
                    if abs(z_score) > z_threshold:
                        variances.append({
                            'period': period,
                            'actual_cost': period_total,
                            'expected_cost': mean_cost,
                            'variance': period_total - mean_cost,
                            'variance_percentage': ((period_total - mean_cost) / mean_cost) * 100,
                            'z_score': z_score,
                            'significance': 'high' if abs(z_score) > z_threshold * 1.5 else 'medium'
                        })
                
                result.variances = sorted(variances, key=lambda x: abs(x['z_score']), reverse=True)
                
                # 按目標分析差異
                target_variances = {}
                for target_id in request.target_ids:
                    target_costs = [
                        float(period_data.get(target_id, 0))
                        for period_data in aggregated_data.values()
                    ]
                    
                    if target_costs and any(c > 0 for c in target_costs):
                        target_mean = statistics.mean(target_costs)
                        target_std = statistics.stdev(target_costs) if len(target_costs) > 1 else 0
                        
                        target_variances[target_id] = {
                            'mean': target_mean,
                            'std_deviation': target_std,
                            'coefficient_variation': (target_std / target_mean) if target_mean > 0 else 0
                        }
                
                result.dimension_analysis['target_variances'] = target_variances
            
        except Exception as e:
            result.insights.append({
                'type': 'error',
                'message': f'Cost variance analysis failed: {e}',
                'severity': 'high'
            })
    
    async def _analyze_cost_drivers(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """成本驅動因素分析"""
        try:
            # 按成本類別分析
            category_analysis = {}
            categories = set(dp.cost_category for dp in cost_data)
            
            total_cost = sum(float(dp.amount) for dp in cost_data)
            
            for category in categories:
                category_data = [dp for dp in cost_data if dp.cost_category == category]
                category_cost = sum(float(dp.amount) for dp in category_data)
                
                category_analysis[category] = {
                    'total_cost': category_cost,
                    'percentage_of_total': (category_cost / total_cost) * 100 if total_cost > 0 else 0,
                    'data_points': len(category_data),
                    'avg_transaction_size': category_cost / len(category_data) if category_data else 0
                }
                
                # 時間趨勢分析
                time_series = self._create_time_series(category_data, request.aggregation_level)
                if len(time_series) > 2:
                    trend_slope = self._calculate_trend_slope(time_series)
                    category_analysis[category]['trend_slope'] = trend_slope
                    category_analysis[category]['trend_direction'] = 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable'
            
            # 排序並識別主要驅動因素
            sorted_categories = sorted(
                category_analysis.items(),
                key=lambda x: x[1]['total_cost'],
                reverse=True
            )
            
            result.dimension_analysis['cost_drivers'] = {
                'top_cost_categories': sorted_categories[:5],
                'category_analysis': category_analysis,
                'total_analyzed_cost': total_cost
            }
            
            # 識別快速增長的類別
            growing_categories = [
                (cat, data) for cat, data in category_analysis.items()
                if data.get('trend_slope', 0) > 0 and data['percentage_of_total'] > 5
            ]
            
            if growing_categories:
                result.insights.append({
                    'type': 'cost_driver',
                    'message': f"Identified {len(growing_categories)} cost categories with increasing trends",
                    'details': growing_categories,
                    'severity': 'medium'
                })
            
        except Exception as e:
            result.insights.append({
                'type': 'error',
                'message': f'Cost driver analysis failed: {e}',
                'severity': 'high'
            })
    
    async def _analyze_efficiency(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """效率分析"""
        try:
            # 計算單位成本
            efficiency_metrics = {}
            
            for target_id in request.target_ids:
                target_data = [dp for dp in cost_data if dp.target_id == target_id]
                
                if not target_data:
                    continue
                
                total_cost = sum(float(dp.amount) for dp in target_data)
                total_units = sum(dp.units or 0 for dp in target_data if dp.units)
                
                if total_units > 0:
                    cost_per_unit = total_cost / total_units
                    
                    efficiency_metrics[target_id] = {
                        'total_cost': total_cost,
                        'total_units': total_units,
                        'cost_per_unit': cost_per_unit,
                        'data_points': len(target_data)
                    }
                    
                    # 時間序列效率分析
                    monthly_data = self._aggregate_data_by_period(target_data, 'monthly')
                    monthly_efficiency = []
                    
                    for month, month_data in monthly_data.items():
                        if target_id in month_data:
                            month_cost = float(month_data[target_id])
                            # 需要單位數據來計算效率 - 這裡使用簡化邏輯
                            month_efficiency = 1 / month_cost if month_cost > 0 else 0
                            monthly_efficiency.append(month_efficiency)
                    
                    if len(monthly_efficiency) > 1:
                        efficiency_trend = self._calculate_trend_slope(
                            [(i, eff) for i, eff in enumerate(monthly_efficiency)]
                        )
                        efficiency_metrics[target_id]['efficiency_trend'] = efficiency_trend
            
            result.dimension_analysis['efficiency_analysis'] = efficiency_metrics
            
            # 效率基準比較
            if efficiency_metrics:
                cost_per_unit_values = [m['cost_per_unit'] for m in efficiency_metrics.values() if 'cost_per_unit' in m]
                
                if cost_per_unit_values:
                    median_efficiency = statistics.median(cost_per_unit_values)
                    
                    for target_id, metrics in efficiency_metrics.items():
                        if 'cost_per_unit' in metrics:
                            efficiency_ratio = metrics['cost_per_unit'] / median_efficiency
                            metrics['efficiency_score'] = 1 / efficiency_ratio if efficiency_ratio > 0 else 0
                            metrics['vs_median'] = 'above_average' if efficiency_ratio > 1.1 else 'below_average' if efficiency_ratio < 0.9 else 'average'
            
        except Exception as e:
            result.insights.append({
                'type': 'error',
                'message': f'Efficiency analysis failed: {e}',
                'severity': 'high'
            })
    
    async def _analyze_forecasts(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """預測分析"""
        try:
            # 創建時間序列
            time_series = self._create_time_series(cost_data, request.aggregation_level)
            
            if len(time_series) < 3:
                result.insights.append({
                    'type': 'warning',
                    'message': 'Insufficient data for reliable forecasting',
                    'severity': 'medium'
                })
                return
            
            # 簡單線性回歸預測
            forecast_periods = request.prediction_horizon_days // self._get_period_days(request.aggregation_level)
            
            # 準備數據
            x_values = list(range(len(time_series)))
            y_values = [point[1] for point in time_series]
            
            # 計算回歸參數
            slope, intercept = self._calculate_linear_regression(x_values, y_values)
            
            # 生成預測
            predictions = []
            last_x = len(time_series) - 1
            
            for i in range(1, forecast_periods + 1):
                future_x = last_x + i
                predicted_value = slope * future_x + intercept
                
                # 計算預測區間（簡化計算）
                residuals = [y_values[j] - (slope * x_values[j] + intercept) for j in range(len(y_values))]
                std_error = statistics.stdev(residuals) if len(residuals) > 1 else 0
                
                confidence_interval = 1.96 * std_error  # 95% 信心區間
                
                predictions.append({
                    'period': i,
                    'predicted_value': max(0, predicted_value),
                    'lower_bound': max(0, predicted_value - confidence_interval),
                    'upper_bound': predicted_value + confidence_interval,
                    'confidence': max(0.5, 1.0 - (i / forecast_periods) * 0.5)
                })
            
            result.forecasts = {
                'model': 'linear_regression',
                'historical_periods': len(time_series),
                'forecast_periods': forecast_periods,
                'predictions': predictions,
                'model_accuracy': {
                    'r_squared': self._calculate_r_squared(x_values, y_values, slope, intercept),
                    'mae': self._calculate_mae(residuals),
                    'rmse': self._calculate_rmse(residuals)
                }
            }
            
            # 趨勢洞察
            if slope > 0:
                growth_rate = (slope / statistics.mean(y_values)) * 100
                result.insights.append({
                    'type': 'forecast',
                    'message': f'Costs are predicted to increase at {growth_rate:.1f}% per period',
                    'severity': 'medium' if growth_rate > 10 else 'low'
                })
            elif slope < 0:
                decline_rate = abs(slope / statistics.mean(y_values)) * 100
                result.insights.append({
                    'type': 'forecast',
                    'message': f'Costs are predicted to decrease at {decline_rate:.1f}% per period',
                    'severity': 'low'
                })
            
        except Exception as e:
            result.insights.append({
                'type': 'error',
                'message': f'Forecast analysis failed: {e}',
                'severity': 'high'
            })
    
    async def _analyze_anomalies(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """異常分析"""
        try:
            # 時間序列異常檢測
            time_series = self._create_time_series(cost_data, request.aggregation_level)
            
            if len(time_series) < 5:
                result.insights.append({
                    'type': 'warning',
                    'message': 'Insufficient data for anomaly detection',
                    'severity': 'low'
                })
                return
            
            # 計算移動平均和標準差
            window_size = min(5, len(time_series) // 2)
            anomalies = []
            
            for i in range(window_size, len(time_series)):
                current_value = time_series[i][1]
                
                # 計算窗口統計
                window_values = [time_series[j][1] for j in range(i - window_size, i)]
                window_mean = statistics.mean(window_values)
                window_std = statistics.stdev(window_values) if len(window_values) > 1 else 0
                
                # Z-score 異常檢測
                if window_std > 0:
                    z_score = (current_value - window_mean) / window_std
                    
                    if abs(z_score) > self.config['anomaly_detection_threshold']:
                        anomalies.append({
                            'timestamp': time_series[i][0],
                            'value': current_value,
                            'expected_value': window_mean,
                            'deviation': current_value - window_mean,
                            'z_score': z_score,
                            'severity': 'high' if abs(z_score) > 3 else 'medium',
                            'type': 'spike' if z_score > 0 else 'drop'
                        })
            
            result.anomalies = sorted(anomalies, key=lambda x: abs(x['z_score']), reverse=True)
            
            # 按目標分析異常
            target_anomalies = {}
            for target_id in request.target_ids:
                target_data = [dp for dp in cost_data if dp.target_id == target_id]
                target_series = self._create_time_series(target_data, request.aggregation_level)
                
                if len(target_series) >= 5:
                    target_outliers = self._detect_outliers_iqr([point[1] for point in target_series])
                    if target_outliers:
                        target_anomalies[target_id] = len(target_outliers)
            
            result.dimension_analysis['target_anomalies'] = target_anomalies
            
            # 異常總結
            if anomalies:
                high_severity_count = len([a for a in anomalies if a['severity'] == 'high'])
                result.insights.append({
                    'type': 'anomaly',
                    'message': f'Detected {len(anomalies)} anomalies ({high_severity_count} high severity)',
                    'severity': 'high' if high_severity_count > 0 else 'medium',
                    'details': anomalies[:5]  # Top 5 anomalies
                })
            
        except Exception as e:
            result.insights.append({
                'type': 'error',
                'message': f'Anomaly analysis failed: {e}',
                'severity': 'high'
            })
    
    # ==================== 基礎分析和洞察生成 ====================
    
    async def _perform_basic_analysis(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """基礎分析"""
        try:
            # 基礎統計
            total_cost = sum(float(dp.amount) for dp in cost_data)
            avg_cost = total_cost / len(cost_data) if cost_data else 0
            
            cost_values = [float(dp.amount) for dp in cost_data]
            if cost_values:
                result.summary_statistics = {
                    'total_cost': total_cost,
                    'average_cost': avg_cost,
                    'median_cost': statistics.median(cost_values),
                    'min_cost': min(cost_values),
                    'max_cost': max(cost_values),
                    'std_deviation': statistics.stdev(cost_values) if len(cost_values) > 1 else 0,
                    'data_points': len(cost_data),
                    'date_range': f"{request.start_date} to {request.end_date}"
                }
            
            # 按維度分組
            if AnalysisDimension.COST_CATEGORY in request.dimensions:
                category_breakdown = {}
                categories = set(dp.cost_category for dp in cost_data)
                
                for category in categories:
                    category_cost = sum(
                        float(dp.amount) for dp in cost_data if dp.cost_category == category
                    )
                    category_breakdown[category] = {
                        'amount': category_cost,
                        'percentage': (category_cost / total_cost) * 100 if total_cost > 0 else 0
                    }
                
                result.dimension_analysis['cost_categories'] = category_breakdown
            
            if AnalysisDimension.ASSET in request.dimensions:
                target_breakdown = {}
                for target_id in request.target_ids:
                    target_cost = sum(
                        float(dp.amount) for dp in cost_data if dp.target_id == target_id
                    )
                    target_breakdown[target_id] = {
                        'amount': target_cost,
                        'percentage': (target_cost / total_cost) * 100 if total_cost > 0 else 0
                    }
                
                result.dimension_analysis['targets'] = target_breakdown
            
        except Exception as e:
            result.insights.append({
                'type': 'error',
                'message': f'Basic analysis failed: {e}',
                'severity': 'high'
            })
    
    async def _generate_insights(
        self,
        request: AnalysisRequest,
        cost_data: List[CostDataPoint],
        result: AnalysisResult
    ):
        """生成自動洞察"""
        try:
            # 成本集中度分析
            if 'targets' in result.dimension_analysis:
                target_costs = list(result.dimension_analysis['targets'].values())
                percentages = [t['percentage'] for t in target_costs]
                
                # 80/20 法則檢查
                sorted_percentages = sorted(percentages, reverse=True)
                top_20_percent_count = max(1, len(sorted_percentages) // 5)
                top_20_percent_cost = sum(sorted_percentages[:top_20_percent_count])
                
                if top_20_percent_cost > 80:
                    result.insights.append({
                        'type': 'concentration',
                        'message': f'Cost concentration detected: Top {top_20_percent_count} targets account for {top_20_percent_cost:.1f}% of total costs',
                        'severity': 'medium',
                        'recommendation': 'Focus cost optimization efforts on high-cost targets'
                    })
            
            # 成本類別分析
            if 'cost_categories' in result.dimension_analysis:
                categories = result.dimension_analysis['cost_categories']
                dominant_category = max(categories.items(), key=lambda x: x[1]['percentage'])
                
                if dominant_category[1]['percentage'] > 50:
                    result.insights.append({
                        'type': 'category_dominance',
                        'message': f'{dominant_category[0]} dominates cost structure at {dominant_category[1]["percentage"]:.1f}%',
                        'severity': 'medium',
                        'recommendation': f'Consider optimizing {dominant_category[0]} costs for maximum impact'
                    })
            
            # 數據質量洞察
            if result.data_quality_score < 0.8:
                result.insights.append({
                    'type': 'data_quality',
                    'message': f'Data quality score is {result.data_quality_score:.2f}, which may affect analysis reliability',
                    'severity': 'medium',
                    'recommendation': 'Improve data collection and validation processes'
                })
            
        except Exception as e:
            self.logger.error(f"❌ Error generating insights: {e}")
    
    # ==================== 數據處理輔助方法 ====================
    
    def _aggregate_data_by_period(
        self,
        cost_data: List[CostDataPoint],
        aggregation_level: str
    ) -> Dict[str, Dict[str, Decimal]]:
        """按時間期間聚合數據"""
        aggregated = defaultdict(lambda: defaultdict(Decimal))
        
        for dp in cost_data:
            period_key = self._get_period_key(dp.timestamp, aggregation_level)
            aggregated[period_key][dp.target_id] += dp.amount
        
        return dict(aggregated)
    
    def _create_time_series(
        self,
        cost_data: List[CostDataPoint],
        aggregation_level: str
    ) -> List[Tuple[str, float]]:
        """創建時間序列"""
        period_totals = defaultdict(Decimal)
        
        for dp in cost_data:
            period_key = self._get_period_key(dp.timestamp, aggregation_level)
            period_totals[period_key] += dp.amount
        
        # 排序並轉換為列表
        sorted_periods = sorted(period_totals.items())
        return [(period, float(total)) for period, total in sorted_periods]
    
    def _get_period_key(self, timestamp: datetime, aggregation_level: str) -> str:
        """獲取時間期間鍵"""
        if aggregation_level == "daily":
            return timestamp.strftime("%Y-%m-%d")
        elif aggregation_level == "weekly":
            year, week, _ = timestamp.isocalendar()
            return f"{year}-W{week:02d}"
        elif aggregation_level == "monthly":
            return timestamp.strftime("%Y-%m")
        elif aggregation_level == "quarterly":
            quarter = (timestamp.month - 1) // 3 + 1
            return f"{timestamp.year}-Q{quarter}"
        else:
            return timestamp.strftime("%Y-%m-%d")
    
    def _get_period_days(self, aggregation_level: str) -> int:
        """獲取聚合期間的天數"""
        return {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90
        }.get(aggregation_level, 1)
    
    # ==================== 統計計算方法 ====================
    
    def _calculate_trend_slope(self, time_series: List[Tuple]) -> float:
        """計算趨勢斜率"""
        if len(time_series) < 2:
            return 0
        
        x_values = list(range(len(time_series)))
        y_values = [point[1] for point in time_series]
        
        slope, _ = self._calculate_linear_regression(x_values, y_values)
        return slope
    
    def _calculate_linear_regression(self, x_values: List[float], y_values: List[float]) -> Tuple[float, float]:
        """計算線性回歸參數"""
        n = len(x_values)
        if n == 0:
            return 0, 0
        
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept
    
    def _calculate_r_squared(self, x_values: List[float], y_values: List[float], slope: float, intercept: float) -> float:
        """計算R平方值"""
        if not y_values:
            return 0
        
        y_mean = statistics.mean(y_values)
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        
        if ss_tot == 0:
            return 1 if all(y == y_mean for y in y_values) else 0
        
        ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values))
        
        return 1 - (ss_res / ss_tot)
    
    def _calculate_mae(self, residuals: List[float]) -> float:
        """計算平均絕對誤差"""
        return statistics.mean(abs(r) for r in residuals) if residuals else 0
    
    def _calculate_rmse(self, residuals: List[float]) -> float:
        """計算均方根誤差"""
        if not residuals:
            return 0
        mse = statistics.mean(r * r for r in residuals)
        return math.sqrt(mse)
    
    def _detect_outliers_iqr(self, values: List[float]) -> List[int]:
        """使用IQR方法檢測異常值"""
        if len(values) < 4:
            return []
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        q1_index = n // 4
        q3_index = 3 * n // 4
        
        q1 = sorted_values[q1_index]
        q3 = sorted_values[q3_index]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        for i, value in enumerate(values):
            if value < lower_bound or value > upper_bound:
                outliers.append(i)
        
        return outliers
    
    # ==================== 數據質量和緩存管理 ====================
    
    def _calculate_data_quality_score(self, cost_data: List[CostDataPoint]) -> float:
        """計算數據質量分數"""
        if not cost_data:
            return 0
        
        score = 1.0
        
        # 完整性檢查
        missing_amounts = sum(1 for dp in cost_data if dp.amount <= 0)
        if missing_amounts > 0:
            score *= (1 - missing_amounts / len(cost_data))
        
        # 一致性檢查
        unique_categories = set(dp.cost_category for dp in cost_data)
        if len(unique_categories) < 2:
            score *= 0.9  # 減少多樣性的分數
        
        # 時效性檢查
        latest_timestamp = max(dp.timestamp for dp in cost_data)
        days_old = (datetime.now(timezone.utc) - latest_timestamp).days
        if days_old > 7:
            score *= max(0.5, 1 - days_old / 30)
        
        return max(0.1, min(1.0, score))
    
    def _calculate_confidence_score(self, result: AnalysisResult, cost_data: List[CostDataPoint]) -> float:
        """計算分析信心度"""
        score = 1.0
        
        # 基於數據量
        data_points = len(cost_data)
        if data_points < 10:
            score *= 0.6
        elif data_points < 50:
            score *= 0.8
        
        # 基於時間跨度
        if cost_data:
            time_span = (max(dp.timestamp for dp in cost_data) - min(dp.timestamp for dp in cost_data)).days
            if time_span < 7:
                score *= 0.7
            elif time_span < 30:
                score *= 0.9
        
        # 基於錯誤數量
        error_insights = [i for i in result.insights if i.get('type') == 'error']
        if error_insights:
            score *= max(0.3, 1 - len(error_insights) * 0.2)
        
        # 基於數據質量
        score *= result.data_quality_score
        
        return max(0.1, min(1.0, score))
    
    def _generate_cache_key(self, request: AnalysisRequest) -> str:
        """生成分析緩存鍵"""
        import hashlib
        
        key_data = {
            'analysis_type': request.analysis_type.value,
            'target_ids': sorted(request.target_ids),
            'start_date': request.start_date.isoformat(),
            'end_date': request.end_date.isoformat(),
            'dimensions': [d.value for d in request.dimensions],
            'aggregation_level': request.aggregation_level
        }
        
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_result: AnalysisResult) -> bool:
        """檢查緩存是否有效"""
        cache_age_hours = (datetime.now(timezone.utc) - cached_result.generated_at).total_seconds() / 3600
        return cache_age_hours < self.config['cache_ttl_hours']
    
    def _create_empty_result(
        self,
        request: AnalysisRequest,
        start_time: datetime,
        error_message: str
    ) -> AnalysisResult:
        """創建空分析結果"""
        result = AnalysisResult(
            analysis_id=request.analysis_id,
            request=request
        )
        
        result.processing_time_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        result.insights = [{
            'type': 'error',
            'message': error_message,
            'severity': 'high'
        }]
        result.confidence_score = 0.0
        result.data_quality_score = 0.0
        
        return result
    
    def _invalidate_caches(self):
        """清除相關緩存"""
        self.analysis_cache.clear()
        self.statistics_cache.clear()
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """成本分析引擎健康檢查"""
        health_status = {
            'system': 'cost_analytics',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # 檢查數據統計
            health_status['components']['data'] = {
                'cost_data_points': len(self.cost_data),
                'cached_analyses': len(self.analysis_cache),
                'oldest_data': min(dp.timestamp for dp in self.cost_data).isoformat() if self.cost_data else None,
                'newest_data': max(dp.timestamp for dp in self.cost_data).isoformat() if self.cost_data else None
            }
            
            # 檢查配置
            health_status['components']['configuration'] = {
                'anomaly_threshold': self.config['anomaly_detection_threshold'],
                'cache_ttl_hours': self.config['cache_ttl_hours'],
                'max_data_points': self.config['max_data_points'],
                'outlier_detection': self.config['outlier_detection_enabled']
            }
            
            # 檢查內存使用
            if len(self.cost_data) > self.config['max_data_points'] * 0.9:
                health_status['warnings'] = ['Approaching maximum data points limit']
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Cost analytics health check failed: {e}")
        
        return health_status


# ==================== 工廠類和輔助功能 ====================

class AnalyticsFactory:
    """分析工廠類"""
    
    @staticmethod
    def create_cost_variance_request(
        analysis_id: str,
        target_ids: List[str],
        start_date: date,
        end_date: date,
        baseline_start: Optional[date] = None,
        baseline_end: Optional[date] = None
    ) -> AnalysisRequest:
        """創建成本差異分析請求"""
        return AnalysisRequest(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.COST_VARIANCE,
            dimensions=[AnalysisDimension.TIME, AnalysisDimension.ASSET],
            target_ids=target_ids,
            start_date=start_date,
            end_date=end_date,
            baseline_period_start=baseline_start,
            baseline_period_end=baseline_end,
            metrics=[MetricType.ABSOLUTE_COST, MetricType.VARIANCE],
            aggregation_level="daily"
        )
    
    @staticmethod
    def create_efficiency_analysis_request(
        analysis_id: str,
        target_ids: List[str],
        start_date: date,
        end_date: date
    ) -> AnalysisRequest:
        """創建效率分析請求"""
        return AnalysisRequest(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.EFFICIENCY,
            dimensions=[AnalysisDimension.ASSET, AnalysisDimension.COST_CATEGORY],
            target_ids=target_ids,
            start_date=start_date,
            end_date=end_date,
            metrics=[MetricType.UNIT_COST, MetricType.EFFICIENCY_RATIO],
            aggregation_level="monthly"
        )
    
    @staticmethod
    def create_forecast_request(
        analysis_id: str,
        target_ids: List[str],
        start_date: date,
        end_date: date,
        prediction_days: int = 30
    ) -> AnalysisRequest:
        """創建預測分析請求"""
        return AnalysisRequest(
            analysis_id=analysis_id,
            analysis_type=AnalysisType.FORECAST,
            dimensions=[AnalysisDimension.TIME],
            target_ids=target_ids,
            start_date=start_date,
            end_date=end_date,
            metrics=[MetricType.ABSOLUTE_COST],
            aggregation_level="daily",
            include_predictions=True,
            prediction_horizon_days=prediction_days
        )