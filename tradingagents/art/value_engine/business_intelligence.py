#!/usr/bin/env python3
"""
Business Intelligence Dashboard - 商業智能儀表板
天工 (TianGong) - 為ART系統提供商業智能和數據洞察

此模組提供：
1. BusinessIntelligenceDashboard - 商業智能儀表板核心
2. KPITracker - 關鍵績效指標追蹤器
3. PerformanceAnalyzer - 績效分析器
4. TrendAnalyzer - 趨勢分析器
5. PredictiveAnalytics - 預測分析引擎
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import uuid
import numpy as np
from collections import defaultdict, deque
import math

class KPICategory(Enum):
    """KPI類別"""
    FINANCIAL = "financial"                # 財務KPI
    OPERATIONAL = "operational"            # 營運KPI
    CUSTOMER = "customer"                  # 客戶KPI
    GROWTH = "growth"                      # 增長KPI
    QUALITY = "quality"                    # 質量KPI
    EFFICIENCY = "efficiency"              # 效率KPI

class TrendDirection(Enum):
    """趨勢方向"""
    INCREASING = "increasing"              # 上升
    DECREASING = "decreasing"              # 下降
    STABLE = "stable"                      # 穩定
    VOLATILE = "volatile"                  # 波動

class AlertLevel(Enum):
    """警報等級"""
    INFO = "info"                          # 信息
    WARNING = "warning"                    # 警告
    CRITICAL = "critical"                  # 嚴重
    EMERGENCY = "emergency"                # 緊急

@dataclass
class KPIMetric:
    """KPI指標"""
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: KPICategory = KPICategory.OPERATIONAL
    current_value: float = 0.0
    target_value: float = 0.0
    unit: str = ""
    
    # 歷史數據
    historical_values: List[Tuple[float, float]] = field(default_factory=list)  # (timestamp, value)
    
    # 趨勢分析
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_strength: float = 0.0            # 趨勢強度 -1 到 1
    volatility: float = 0.0                # 波動性
    
    # 目標追蹤
    target_achievement_rate: float = 0.0   # 目標達成率
    days_to_target: Optional[int] = None   # 到達目標的天數
    confidence_in_target: float = 0.0      # 目標達成信心度
    
    # 警報設置
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    alert_enabled: bool = True
    
    # 元數據
    description: str = ""
    calculation_formula: str = ""
    data_source: str = ""
    owner: str = ""
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_performance_score(self) -> float:
        """計算績效分數 (0-100)"""
        if self.target_value == 0:
            return 50.0  # 無目標時返回中性分數
        
        achievement_rate = self.current_value / self.target_value
        
        # 根據指標特性調整分數計算
        if self.category in [KPICategory.FINANCIAL, KPICategory.GROWTH]:
            # 越高越好的指標
            score = min(achievement_rate * 100, 100)
        else:
            # 可能有最優範圍的指標
            if achievement_rate <= 1.0:
                score = achievement_rate * 100
            else:
                # 超過目標可能不一定更好
                score = max(100 - (achievement_rate - 1) * 50, 0)
        
        return max(0, min(100, score))

@dataclass
class BusinessInsight:
    """商業洞察"""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: str = "general"
    
    # 洞察內容
    key_findings: List[str] = field(default_factory=list)
    implications: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 支撐數據
    supporting_metrics: List[str] = field(default_factory=list)
    confidence_score: float = 0.0          # 洞察可信度
    impact_score: float = 0.0              # 影響力分數
    
    # 優先級和時效性
    priority: str = "medium"               # low, medium, high
    urgency: str = "normal"                # low, normal, high
    relevance_period: int = 30             # 相關期間（天）
    
    # 元數據
    generated_at: float = field(default_factory=time.time)
    generated_by: str = "system"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class KPITracker:
    """KPI追蹤器"""
    
    def __init__(self):
        self.kpis: Dict[str, KPIMetric] = {}
        self.tracking_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def add_kpi(self, kpi: KPIMetric):
        """添加KPI指標"""
        self.kpis[kpi.metric_id] = kpi
        self.logger.info(f"Added KPI: {kpi.name}")
    
    def update_kpi_value(self, metric_id: str, value: float, timestamp: Optional[float] = None):
        """更新KPI值"""
        if metric_id not in self.kpis:
            self.logger.warning(f"KPI {metric_id} not found")
            return
        
        kpi = self.kpis[metric_id]
        timestamp = timestamp or time.time()
        
        # 更新當前值
        kpi.current_value = value
        kpi.last_updated = timestamp
        
        # 添加歷史記錄
        kpi.historical_values.append((timestamp, value))
        
        # 保持歷史記錄長度
        if len(kpi.historical_values) > 1000:
            kpi.historical_values = kpi.historical_values[-1000:]
        
        # 更新目標達成率
        if kpi.target_value != 0:
            kpi.target_achievement_rate = (value / kpi.target_value) * 100
        
        # 更新趨勢分析
        self._update_trend_analysis(kpi)
        
        self.logger.debug(f"Updated KPI {kpi.name}: {value}")
    
    def _update_trend_analysis(self, kpi: KPIMetric):
        """更新趨勢分析"""
        if len(kpi.historical_values) < 3:
            return
        
        # 取最近的值計算趨勢
        recent_values = [v[1] for v in kpi.historical_values[-10:]]
        
        # 計算趨勢方向
        if len(recent_values) >= 3:
            # 使用線性回歸計算趨勢
            x = np.arange(len(recent_values))
            y = np.array(recent_values)
            
            if len(y) > 1 and np.std(y) > 0:
                trend_slope = np.polyfit(x, y, 1)[0]
                kpi.trend_strength = np.tanh(trend_slope / (np.mean(y) + 0.001))  # 標準化
                
                # 確定趨勢方向
                if abs(kpi.trend_strength) < 0.1:
                    kpi.trend_direction = TrendDirection.STABLE
                elif kpi.trend_strength > 0.1:
                    kpi.trend_direction = TrendDirection.INCREASING
                else:
                    kpi.trend_direction = TrendDirection.DECREASING
                
                # 計算波動性
                kpi.volatility = np.std(recent_values) / (np.mean(recent_values) + 0.001)
                
                if kpi.volatility > 0.2:  # 高波動性
                    kpi.trend_direction = TrendDirection.VOLATILE
    
    def get_kpi_alerts(self) -> List[Dict[str, Any]]:
        """獲取KPI警報"""
        alerts = []
        
        for kpi in self.kpis.values():
            if not kpi.alert_enabled:
                continue
            
            alert_level = None
            message = ""
            
            # 檢查臨界閾值
            if kpi.critical_threshold is not None:
                if kpi.current_value <= kpi.critical_threshold:
                    alert_level = AlertLevel.CRITICAL
                    message = f"{kpi.name} 已達到臨界水準 ({kpi.current_value} <= {kpi.critical_threshold})"
            
            # 檢查警告閾值
            if alert_level is None and kpi.warning_threshold is not None:
                if kpi.current_value <= kpi.warning_threshold:
                    alert_level = AlertLevel.WARNING
                    message = f"{kpi.name} 已達到警告水準 ({kpi.current_value} <= {kpi.warning_threshold})"
            
            # 檢查目標達成率
            if alert_level is None and kpi.target_achievement_rate < 80:
                alert_level = AlertLevel.WARNING
                message = f"{kpi.name} 目標達成率偏低 ({kpi.target_achievement_rate:.1f}%)"
            
            if alert_level:
                alerts.append({
                    'kpi_id': kpi.metric_id,
                    'kpi_name': kpi.name,
                    'level': alert_level.value,
                    'message': message,
                    'current_value': kpi.current_value,
                    'timestamp': time.time()
                })
        
        return alerts
    
    def calculate_overall_performance(self) -> Dict[str, Any]:
        """計算整體績效"""
        if not self.kpis:
            return {'overall_score': 0, 'category_scores': {}}
        
        category_scores = defaultdict(list)
        
        for kpi in self.kpis.values():
            score = kpi.calculate_performance_score()
            category_scores[kpi.category.value].append(score)
        
        # 計算各類別平均分數
        avg_category_scores = {
            category: np.mean(scores) 
            for category, scores in category_scores.items()
        }
        
        # 計算整體分數
        overall_score = np.mean(list(avg_category_scores.values()))
        
        return {
            'overall_score': overall_score,
            'category_scores': avg_category_scores,
            'total_kpis': len(self.kpis),
            'calculation_time': time.time()
        }

class PerformanceAnalyzer:
    """績效分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_performance_trends(self, kpis: Dict[str, KPIMetric], 
                                       period_days: int = 30) -> Dict[str, Any]:
        """分析績效趨勢"""
        analysis_result = {
            'period_days': period_days,
            'trend_summary': {},
            'performance_insights': [],
            'correlation_analysis': {}
        }
        
        # 趨勢摘要
        trend_counts = defaultdict(int)
        category_trends = defaultdict(list)
        
        for kpi in kpis.values():
            trend_counts[kpi.trend_direction.value] += 1
            category_trends[kpi.category.value].append(kpi.trend_direction.value)
        
        analysis_result['trend_summary'] = dict(trend_counts)
        
        # 績效洞察
        insights = []
        
        # 識別表現優異的KPI
        top_performers = sorted(kpis.values(), 
                               key=lambda k: k.calculate_performance_score(), 
                               reverse=True)[:3]
        
        if top_performers:
            insights.append(f"表現最佳的KPI: {', '.join([k.name for k in top_performers])}")
        
        # 識別需要關注的KPI
        underperformers = [k for k in kpis.values() if k.calculate_performance_score() < 60]
        if underperformers:
            insights.append(f"需要關注的KPI ({len(underperformers)}個): {', '.join([k.name for k in underperformers[:3]])}")
        
        # 趨勢洞察
        if trend_counts['increasing'] > trend_counts['decreasing']:
            insights.append("整體趨勢向好，大多數指標呈上升趨勢")
        elif trend_counts['decreasing'] > trend_counts['increasing']:
            insights.append("需要警惕，較多指標呈下降趨勢")
        
        analysis_result['performance_insights'] = insights
        
        # 相關性分析
        if len(kpis) > 1:
            correlation_analysis = await self._analyze_kpi_correlations(kpis)
            analysis_result['correlation_analysis'] = correlation_analysis
        
        return analysis_result
    
    async def _analyze_kpi_correlations(self, kpis: Dict[str, KPIMetric]) -> Dict[str, Any]:
        """分析KPI相關性"""
        correlations = {}
        kpi_list = list(kpis.values())
        
        for i in range(len(kpi_list)):
            for j in range(i + 1, len(kpi_list)):
                kpi1, kpi2 = kpi_list[i], kpi_list[j]
                
                if len(kpi1.historical_values) > 3 and len(kpi2.historical_values) > 3:
                    # 獲取重疊時間段的數據
                    values1 = [v[1] for v in kpi1.historical_values[-10:]]
                    values2 = [v[1] for v in kpi2.historical_values[-10:]]
                    
                    if len(values1) == len(values2) and len(values1) > 2:
                        correlation = np.corrcoef(values1, values2)[0, 1]
                        if not np.isnan(correlation):
                            correlations[f"{kpi1.name} vs {kpi2.name}"] = correlation
        
        # 找出強相關關係
        strong_correlations = {
            pair: corr for pair, corr in correlations.items() 
            if abs(corr) > 0.7
        }
        
        return {
            'total_pairs_analyzed': len(correlations),
            'strong_correlations': strong_correlations,
            'average_correlation': np.mean(list(correlations.values())) if correlations else 0
        }
    
    def benchmark_performance(self, kpis: Dict[str, KPIMetric], 
                            industry_benchmarks: Dict[str, float]) -> Dict[str, Any]:
        """績效基準比較"""
        benchmark_results = {
            'above_benchmark': [],
            'below_benchmark': [],
            'benchmark_score': 0.0
        }
        
        above_count = 0
        total_compared = 0
        
        for kpi in kpis.values():
            benchmark_value = industry_benchmarks.get(kpi.name)
            if benchmark_value is not None:
                total_compared += 1
                performance_ratio = kpi.current_value / benchmark_value
                
                if performance_ratio >= 1.0:
                    above_count += 1
                    benchmark_results['above_benchmark'].append({
                        'kpi_name': kpi.name,
                        'current_value': kpi.current_value,
                        'benchmark_value': benchmark_value,
                        'performance_ratio': performance_ratio
                    })
                else:
                    benchmark_results['below_benchmark'].append({
                        'kpi_name': kpi.name,
                        'current_value': kpi.current_value,
                        'benchmark_value': benchmark_value,
                        'performance_ratio': performance_ratio
                    })
        
        if total_compared > 0:
            benchmark_results['benchmark_score'] = (above_count / total_compared) * 100
        
        return benchmark_results

class TrendAnalyzer:
    """趨勢分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_seasonal_patterns(self, time_series_data: List[Tuple[float, float]], 
                                 period_length: int = 30) -> Dict[str, Any]:
        """分析季節性模式"""
        if len(time_series_data) < period_length * 2:
            return {'status': 'insufficient_data'}
        
        # 提取時間戳和值
        timestamps = [item[0] for item in time_series_data]
        values = [item[1] for item in time_series_data]
        
        # 簡單季節性檢測
        seasonal_analysis = {
            'seasonal_strength': 0.0,
            'period_detected': period_length,
            'seasonal_peaks': [],
            'seasonal_troughs': []
        }
        
        # 將數據分組為週期
        periods = []
        for i in range(0, len(values) - period_length + 1, period_length):
            period_data = values[i:i + period_length]
            periods.append(period_data)
        
        if len(periods) >= 2:
            # 計算期間的相關性
            correlations = []
            for i in range(len(periods) - 1):
                corr = np.corrcoef(periods[i], periods[i + 1])[0, 1]
                if not np.isnan(corr):
                    correlations.append(corr)
            
            seasonal_analysis['seasonal_strength'] = np.mean(correlations) if correlations else 0.0
            
            # 找出季節性峰值和谷值
            avg_pattern = np.mean(periods, axis=0)
            peak_indices = np.where(avg_pattern > np.mean(avg_pattern) + np.std(avg_pattern))[0]
            trough_indices = np.where(avg_pattern < np.mean(avg_pattern) - np.std(avg_pattern))[0]
            
            seasonal_analysis['seasonal_peaks'] = peak_indices.tolist()
            seasonal_analysis['seasonal_troughs'] = trough_indices.tolist()
        
        return seasonal_analysis
    
    def detect_anomalies(self, time_series_data: List[Tuple[float, float]], 
                        sensitivity: float = 2.0) -> List[Dict[str, Any]]:
        """檢測異常值"""
        if len(time_series_data) < 10:
            return []
        
        values = [item[1] for item in time_series_data]
        timestamps = [item[0] for item in time_series_data]
        
        # 使用Z-score方法檢測異常
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        anomalies = []
        for i, (timestamp, value) in enumerate(time_series_data):
            z_score = abs(value - mean_val) / (std_val + 0.0001)
            
            if z_score > sensitivity:
                anomaly_type = "spike" if value > mean_val else "dip"
                anomalies.append({
                    'timestamp': timestamp,
                    'value': value,
                    'z_score': z_score,
                    'type': anomaly_type,
                    'index': i
                })
        
        return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)

class PredictiveAnalytics:
    """預測分析"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def forecast_kpi_values(self, kpi: KPIMetric, periods_ahead: int = 30) -> Dict[str, Any]:
        """預測KPI值"""
        if len(kpi.historical_values) < 10:
            return {'status': 'insufficient_data'}
        
        # 提取歷史數據
        values = [item[1] for item in kpi.historical_values[-50:]]  # 使用最近50個數據點
        
        forecast_result = {
            'forecast_values': [],
            'confidence_intervals': [],
            'method': 'linear_trend',
            'periods_ahead': periods_ahead
        }
        
        # 簡單線性趨勢預測
        x = np.arange(len(values))
        y = np.array(values)
        
        # 線性回歸
        if len(y) > 1:
            coefficients = np.polyfit(x, y, 1)
            trend_line = np.poly1d(coefficients)
            
            # 計算預測誤差
            predicted = trend_line(x)
            residuals = y - predicted
            std_error = np.std(residuals)
            
            # 生成預測值
            for i in range(periods_ahead):
                future_x = len(values) + i
                predicted_value = trend_line(future_x)
                
                # 信心區間
                confidence_margin = 1.96 * std_error * math.sqrt(1 + 1/len(values))
                lower_bound = predicted_value - confidence_margin
                upper_bound = predicted_value + confidence_margin
                
                forecast_result['forecast_values'].append(predicted_value)
                forecast_result['confidence_intervals'].append({
                    'lower': lower_bound,
                    'upper': upper_bound,
                    'confidence_level': 0.95
                })
        
        return forecast_result
    
    def predict_target_achievement(self, kpi: KPIMetric) -> Dict[str, Any]:
        """預測目標達成"""
        if kpi.target_value <= 0 or len(kpi.historical_values) < 5:
            return {'status': 'insufficient_data'}
        
        # 計算達成目標所需的改進率
        current_value = kpi.current_value
        gap_to_target = kpi.target_value - current_value
        
        if gap_to_target <= 0:
            return {
                'status': 'target_achieved',
                'achievement_probability': 1.0,
                'days_to_achievement': 0
            }
        
        # 分析歷史改進率
        values = [item[1] for item in kpi.historical_values[-20:]]
        if len(values) > 1:
            daily_changes = np.diff(values)
            avg_daily_change = np.mean(daily_changes)
            std_daily_change = np.std(daily_changes)
            
            if avg_daily_change > 0:
                # 預計達成天數
                estimated_days = gap_to_target / avg_daily_change
                
                # 達成概率（基於變動性）
                if std_daily_change > 0:
                    coefficient_of_variation = std_daily_change / abs(avg_daily_change)
                    achievement_probability = max(0.1, 1.0 - coefficient_of_variation)
                else:
                    achievement_probability = 0.9
                
                return {
                    'status': 'prediction_available',
                    'achievement_probability': min(achievement_probability, 1.0),
                    'estimated_days_to_achievement': max(1, int(estimated_days)),
                    'required_daily_improvement': gap_to_target / 30  # 假設30天內達成
                }
        
        return {
            'status': 'negative_trend',
            'achievement_probability': 0.1,
            'recommendation': '需要改變策略以達成目標'
        }

class BusinessIntelligenceDashboard:
    """商業智能儀表板"""
    
    def __init__(self):
        self.kpi_tracker = KPITracker()
        self.performance_analyzer = PerformanceAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.predictive_analytics = PredictiveAnalytics()
        self.insights: List[BusinessInsight] = []
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("BusinessIntelligenceDashboard initialized")
    
    async def generate_dashboard_report(self) -> Dict[str, Any]:
        """生成儀表板報告"""
        report = {
            'generation_timestamp': time.time(),
            'kpi_summary': {},
            'performance_analysis': {},
            'alerts': [],
            'insights': [],
            'forecasts': {}
        }
        
        try:
            # KPI摘要
            report['kpi_summary'] = self.kpi_tracker.calculate_overall_performance()
            
            # 績效分析
            report['performance_analysis'] = await self.performance_analyzer.analyze_performance_trends(
                self.kpi_tracker.kpis
            )
            
            # 警報
            report['alerts'] = self.kpi_tracker.get_kpi_alerts()
            
            # 生成洞察
            insights = await self._generate_business_insights()
            report['insights'] = [
                {
                    'title': insight.title,
                    'description': insight.description,
                    'key_findings': insight.key_findings,
                    'recommendations': insight.recommendations,
                    'priority': insight.priority
                }
                for insight in insights[:5]  # 前5個洞察
            ]
            
            # 預測
            forecasts = {}
            for kpi_id, kpi in list(self.kpi_tracker.kpis.items())[:3]:  # 前3個KPI的預測
                forecast = self.predictive_analytics.forecast_kpi_values(kpi, 7)  # 7天預測
                if forecast.get('status') != 'insufficient_data':
                    forecasts[kpi.name] = forecast
            
            report['forecasts'] = forecasts
            
            self.logger.info("Dashboard report generated successfully")
            return report
            
        except Exception as e:
            self.logger.error(f"Dashboard report generation failed: {e}")
            raise
    
    async def _generate_business_insights(self) -> List[BusinessInsight]:
        """生成商業洞察"""
        insights = []
        
        # 基於KPI表現的洞察
        performance_data = self.kpi_tracker.calculate_overall_performance()
        overall_score = performance_data.get('overall_score', 0)
        
        if overall_score < 60:
            insight = BusinessInsight(
                title="整體績效需要改進",
                description=f"當前整體績效分數為{overall_score:.1f}，低於預期水準",
                category="performance",
                key_findings=[f"整體績效分數: {overall_score:.1f}/100"],
                implications=["可能影響業務目標達成", "需要識別關鍵改進領域"],
                recommendations=["分析表現不佳的具體KPI", "制定改進行動計劃"],
                priority="high",
                confidence_score=0.8
            )
            insights.append(insight)
        
        elif overall_score > 85:
            insight = BusinessInsight(
                title="績效表現優異",
                description=f"當前整體績效分數為{overall_score:.1f}，表現優秀",
                category="performance",
                key_findings=[f"整體績效分數: {overall_score:.1f}/100"],
                implications=["業務運營狀態良好", "可考慮擴展業務規模"],
                recommendations=["保持現有優勢", "探索新的增長機會"],
                priority="medium",
                confidence_score=0.9
            )
            insights.append(insight)
        
        # 基於趨勢的洞察
        trend_analysis = await self.performance_analyzer.analyze_performance_trends(
            self.kpi_tracker.kpis
        )
        
        trend_summary = trend_analysis.get('trend_summary', {})
        if trend_summary.get('decreasing', 0) > trend_summary.get('increasing', 0):
            insight = BusinessInsight(
                title="多項指標呈下降趨勢",
                description="檢測到較多KPI呈下降趨勢，需要密切關注",
                category="trend",
                key_findings=[f"下降趨勢KPI: {trend_summary.get('decreasing', 0)}個"],
                implications=["可能存在系統性問題", "業務可能面臨挑戰"],
                recommendations=["深入分析下降原因", "制定扭轉策略"],
                priority="high",
                urgency="high",
                confidence_score=0.7
            )
            insights.append(insight)
        
        # 基於警報的洞察
        alerts = self.kpi_tracker.get_kpi_alerts()
        critical_alerts = [a for a in alerts if a['level'] == 'critical']
        
        if critical_alerts:
            insight = BusinessInsight(
                title="發現嚴重績效警報",
                description=f"有{len(critical_alerts)}個KPI觸發了嚴重警報",
                category="alert",
                key_findings=[f"嚴重警報數量: {len(critical_alerts)}"],
                implications=["可能影響業務運營", "需要立即采取行動"],
                recommendations=["立即處理嚴重警報", "分析根本原因"],
                priority="high",
                urgency="high",
                confidence_score=1.0
            )
            insights.append(insight)
        
        return sorted(insights, key=lambda x: {'high': 3, 'medium': 2, 'low': 1}.get(x.priority, 1), reverse=True)
    
    def add_kpi(self, kpi: KPIMetric):
        """添加KPI"""
        self.kpi_tracker.add_kpi(kpi)
    
    def update_kpi_value(self, metric_id: str, value: float):
        """更新KPI值"""
        self.kpi_tracker.update_kpi_value(metric_id, value)
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """獲取儀表板摘要"""
        performance = self.kpi_tracker.calculate_overall_performance()
        alerts = self.kpi_tracker.get_kpi_alerts()
        
        return {
            'total_kpis': len(self.kpi_tracker.kpis),
            'overall_performance_score': performance.get('overall_score', 0),
            'total_alerts': len(alerts),
            'critical_alerts': len([a for a in alerts if a['level'] == 'critical']),
            'warning_alerts': len([a for a in alerts if a['level'] == 'warning']),
            'last_updated': max([kpi.last_updated for kpi in self.kpi_tracker.kpis.values()]) if self.kpi_tracker.kpis else time.time()
        }

# 工廠函數
def create_business_intelligence_dashboard() -> BusinessIntelligenceDashboard:
    """創建商業智能儀表板"""
    return BusinessIntelligenceDashboard()

def create_kpi_metric(name: str, category: KPICategory, target_value: float = 0, **kwargs) -> KPIMetric:
    """創建KPI指標"""
    return KPIMetric(name=name, category=category, target_value=target_value, **kwargs)

def create_business_insight(title: str, description: str = "", **kwargs) -> BusinessInsight:
    """創建商業洞察"""
    return BusinessInsight(title=title, description=description, **kwargs)