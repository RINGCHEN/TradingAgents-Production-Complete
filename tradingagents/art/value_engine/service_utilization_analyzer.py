#!/usr/bin/env python3
"""
Service Utilization Analyzer - 服務使用效益分析器
天工 (TianGong) - 為ART系統提供服務使用效益分析和優化建議

此模組提供：
1. ServiceUtilizationAnalyzer - 服務使用效益分析核心
2. UtilizationMetrics - 使用效益模型
3. ValueRealizationTracker - 價值實現追蹤器
4. ROIBenchmarking - ROI基準分析
5. UsageOptimizer - 使用優化建議器
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
import statistics
from scipy import stats

# 導入個人化系統組件
from ..personalization.user_profile_analyzer import (
    UserProfileAnalyzer, UserBehaviorModel, PreferenceProfile, 
    BehaviorPattern, PersonalityMetrics
)
from .commercial_metrics import BusinessValue, CommercialMetricsEngine

class UtilizationStatus(Enum):
    """使用狀態"""
    UNDER_UTILIZED = "under_utilized"     # 使用不足
    OPTIMAL = "optimal"                   # 最佳使用
    OVER_UTILIZED = "over_utilized"       # 過度使用
    INEFFICIENT = "inefficient"           # 低效使用
    
class ValueRealizationStage(Enum):
    """價值實現階段"""
    ONBOARDING = "onboarding"            # 入門階段
    ADOPTION = "adoption"                # 採用階段
    OPTIMIZATION = "optimization"        # 優化階段
    MASTERY = "mastery"                  # 精通階段
    EXPANSION = "expansion"              # 擴展階段

class EfficiencyMetric(Enum):
    """效率指標"""
    TIME_TO_VALUE = "time_to_value"            # 價值實現時間
    FEATURE_ADOPTION_RATE = "feature_adoption_rate"  # 功能採用率
    OUTCOME_ACHIEVEMENT = "outcome_achievement"       # 結果達成率
    ENGAGEMENT_DEPTH = "engagement_depth"             # 參與深度
    RETENTION_QUALITY = "retention_quality"           # 保留質量

@dataclass
class UtilizationMetrics:
    """使用效益指標"""
    user_id: str
    service_id: str
    
    # 基礎使用指標
    total_usage_time: float = 0.0         # 總使用時間
    session_count: int = 0                # 會話數量
    feature_usage_count: Dict[str, int] = field(default_factory=dict)  # 功能使用次數
    
    # 價值實現指標
    realized_value: float = 0.0           # 已實現價值
    expected_value: float = 0.0           # 期望價值
    value_realization_rate: float = 0.0   # 價值實現率
    
    # 效率指標
    time_to_first_value: float = 0.0      # 首次價值實現時間
    average_session_duration: float = 0.0 # 平均會話時長
    task_completion_rate: float = 0.0     # 任務完成率
    
    # 品質指標
    user_satisfaction_score: float = 0.0  # 用戶滿意度
    outcome_success_rate: float = 0.0     # 結果成功率
    error_rate: float = 0.0               # 錯誤率
    
    # 參與度指標
    daily_active_usage: float = 0.0       # 日活躍使用
    weekly_active_usage: float = 0.0      # 週活躍使用
    monthly_active_usage: float = 0.0     # 月活躍使用
    
    # 進階指標
    learning_curve_slope: float = 0.0     # 學習曲線斜率
    expertise_level: float = 0.0          # 專業水平
    innovation_usage: float = 0.0         # 創新使用
    
    # 財務效益
    cost_savings_realized: float = 0.0    # 已實現成本節省
    revenue_impact: float = 0.0           # 收入影響
    productivity_gain: float = 0.0        # 生產力提升
    
    # 狀態和階段
    utilization_status: UtilizationStatus = UtilizationStatus.UNDER_UTILIZED
    realization_stage: ValueRealizationStage = ValueRealizationStage.ONBOARDING
    
    # 時間戳記
    measurement_period_start: float = field(default_factory=time.time)
    measurement_period_end: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class ValueRealizationTracker:
    """價值實現追蹤器"""
    user_id: str
    service_id: str
    
    # 價值追蹤
    baseline_metrics: Dict[str, float] = field(default_factory=dict)
    current_metrics: Dict[str, float] = field(default_factory=dict)
    target_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 實現歷程
    value_milestones: List[Dict[str, Any]] = field(default_factory=list)
    realization_timeline: List[Dict[str, Any]] = field(default_factory=list)
    
    # 影響因素
    success_factors: List[str] = field(default_factory=list)
    blocking_factors: List[str] = field(default_factory=list)
    
    # 預測指標
    projected_value: float = 0.0
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    time_to_target: float = 0.0
    
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

class ServiceUtilizationAnalyzer:
    """服務使用效益分析器"""
    
    def __init__(self):
        self.utilization_data: Dict[str, UtilizationMetrics] = {}
        self.value_trackers: Dict[str, ValueRealizationTracker] = {}
        self.benchmark_data: Dict[str, Dict[str, Any]] = {}
        self.commercial_metrics_engine = CommercialMetricsEngine()
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("ServiceUtilizationAnalyzer initialized")
    
    async def analyze_service_utilization(self, user_id: str, service_id: str,
                                        usage_data: List[Dict[str, Any]],
                                        user_behavior: Optional[UserBehaviorModel] = None) -> UtilizationMetrics:
        """分析服務使用效益"""
        try:
            metrics_key = f"{user_id}_{service_id}"
            
            # 創建或獲取使用效益指標
            if metrics_key not in self.utilization_data:
                self.utilization_data[metrics_key] = UtilizationMetrics(
                    user_id=user_id,
                    service_id=service_id
                )
            
            metrics = self.utilization_data[metrics_key]
            
            # 計算基礎使用指標
            await self._calculate_basic_usage_metrics(metrics, usage_data)
            
            # 計算價值實現指標
            await self._calculate_value_realization_metrics(metrics, usage_data, user_behavior)
            
            # 計算效率指標
            await self._calculate_efficiency_metrics(metrics, usage_data)
            
            # 分析使用狀態
            await self._analyze_utilization_status(metrics, usage_data, user_behavior)
            
            # 確定價值實現階段
            await self._determine_realization_stage(metrics, usage_data)
            
            # 計算財務效益
            await self._calculate_financial_benefits(metrics, usage_data)
            
            metrics.last_updated = time.time()
            
            self.logger.info(f"Analyzed service utilization for user {user_id}, service {service_id}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"Service utilization analysis failed: {e}")
            raise
    
    async def _calculate_basic_usage_metrics(self, metrics: UtilizationMetrics, 
                                           usage_data: List[Dict[str, Any]]):
        """計算基礎使用指標"""
        if not usage_data:
            return
        
        # 總使用時間
        session_durations = [d.get('session_duration', 0) for d in usage_data]
        metrics.total_usage_time = sum(session_durations)
        
        # 會話數量
        metrics.session_count = len(usage_data)
        
        # 平均會話時長
        if metrics.session_count > 0:
            metrics.average_session_duration = metrics.total_usage_time / metrics.session_count
        
        # 功能使用統計
        feature_usage = defaultdict(int)
        for data in usage_data:
            features_used = data.get('features_used', [])
            for feature in features_used:
                feature_usage[feature] += 1
        metrics.feature_usage_count = dict(feature_usage)
        
        # 活躍使用計算
        current_time = time.time()
        day_ago = current_time - 86400
        week_ago = current_time - 604800
        month_ago = current_time - 2592000
        
        daily_sessions = [d for d in usage_data if d.get('timestamp', 0) > day_ago]
        weekly_sessions = [d for d in usage_data if d.get('timestamp', 0) > week_ago]
        monthly_sessions = [d for d in usage_data if d.get('timestamp', 0) > month_ago]
        
        metrics.daily_active_usage = len(daily_sessions)
        metrics.weekly_active_usage = len(weekly_sessions)
        metrics.monthly_active_usage = len(monthly_sessions)
    
    async def _calculate_value_realization_metrics(self, metrics: UtilizationMetrics,
                                                 usage_data: List[Dict[str, Any]],
                                                 user_behavior: Optional[UserBehaviorModel]):
        """計算價值實現指標"""
        # 已實現價值計算
        realized_values = [d.get('realized_value', 0) for d in usage_data]
        metrics.realized_value = sum(realized_values)
        
        # 期望價值（基於用戶行為模型估算）
        if user_behavior:
            base_expectation = 1000  # 基礎期望價值
            risk_multiplier = user_behavior.personality_scores.get(PersonalityMetrics.RISK_TOLERANCE, 0.5) + 0.5
            learning_multiplier = user_behavior.personality_scores.get(PersonalityMetrics.LEARNING_RATE, 0.5) + 0.5
            metrics.expected_value = base_expectation * risk_multiplier * learning_multiplier
        else:
            metrics.expected_value = 1000  # 默認期望值
        
        # 價值實現率
        if metrics.expected_value > 0:
            metrics.value_realization_rate = min(1.0, metrics.realized_value / metrics.expected_value)
        
        # 首次價值實現時間
        value_timestamps = [d.get('timestamp', 0) for d in usage_data if d.get('realized_value', 0) > 0]
        if value_timestamps:
            first_value_time = min(value_timestamps)
            start_time = min(d.get('timestamp', 0) for d in usage_data)
            metrics.time_to_first_value = first_value_time - start_time
    
    async def _calculate_efficiency_metrics(self, metrics: UtilizationMetrics, 
                                          usage_data: List[Dict[str, Any]]):
        """計算效率指標"""
        # 任務完成率
        completed_tasks = [d for d in usage_data if d.get('task_completed', False)]
        total_tasks = [d for d in usage_data if 'task_completed' in d]
        if total_tasks:
            metrics.task_completion_rate = len(completed_tasks) / len(total_tasks)
        
        # 用戶滿意度
        satisfaction_scores = [d.get('satisfaction_score', 0) for d in usage_data if 'satisfaction_score' in d]
        if satisfaction_scores:
            metrics.user_satisfaction_score = np.mean(satisfaction_scores)
        
        # 結果成功率
        successful_outcomes = [d for d in usage_data if d.get('outcome_successful', False)]
        total_outcomes = [d for d in usage_data if 'outcome_successful' in d]
        if total_outcomes:
            metrics.outcome_success_rate = len(successful_outcomes) / len(total_outcomes)
        
        # 錯誤率
        error_sessions = [d for d in usage_data if d.get('error_count', 0) > 0]
        if usage_data:
            metrics.error_rate = len(error_sessions) / len(usage_data)
        
        # 學習曲線分析
        if len(usage_data) > 5:
            # 使用任務完成時間作為學習指標
            completion_times = []
            timestamps = []
            for i, data in enumerate(usage_data):
                if 'task_completion_time' in data:
                    completion_times.append(data['task_completion_time'])
                    timestamps.append(i)
            
            if len(completion_times) > 3:
                # 計算學習曲線斜率（完成時間隨時間的變化）
                slope, _, _, _, _ = stats.linregress(timestamps, completion_times)
                metrics.learning_curve_slope = -slope  # 負斜率表示改進
        
        # 專業水平評估
        advanced_features_used = sum(1 for d in usage_data if d.get('advanced_features_used', False))
        if usage_data:
            metrics.expertise_level = advanced_features_used / len(usage_data)
    
    async def _analyze_utilization_status(self, metrics: UtilizationMetrics,
                                        usage_data: List[Dict[str, Any]],
                                        user_behavior: Optional[UserBehaviorModel]):
        """分析使用狀態"""
        # 基於多個指標綜合判斷使用狀態
        indicators = []
        
        # 使用頻率指標
        if metrics.daily_active_usage > 0.7:
            indicators.append('high_frequency')
        elif metrics.daily_active_usage < 0.3:
            indicators.append('low_frequency')
        
        # 價值實現指標
        if metrics.value_realization_rate > 0.8:
            indicators.append('high_value_realization')
        elif metrics.value_realization_rate < 0.4:
            indicators.append('low_value_realization')
        
        # 效率指標
        if metrics.task_completion_rate > 0.8:
            indicators.append('high_efficiency')
        elif metrics.task_completion_rate < 0.5:
            indicators.append('low_efficiency')
        
        # 滿意度指標
        if metrics.user_satisfaction_score > 4.0:
            indicators.append('high_satisfaction')
        elif metrics.user_satisfaction_score < 3.0:
            indicators.append('low_satisfaction')
        
        # 綜合判斷狀態
        positive_indicators = sum(1 for i in indicators if 'high' in i)
        negative_indicators = sum(1 for i in indicators if 'low' in i)
        
        if positive_indicators >= 3:
            metrics.utilization_status = UtilizationStatus.OPTIMAL
        elif positive_indicators >= 2 and negative_indicators <= 1:
            metrics.utilization_status = UtilizationStatus.OPTIMAL
        elif negative_indicators >= 2:
            if 'low_frequency' in indicators:
                metrics.utilization_status = UtilizationStatus.UNDER_UTILIZED
            else:
                metrics.utilization_status = UtilizationStatus.INEFFICIENT
        else:
            metrics.utilization_status = UtilizationStatus.OPTIMAL
    
    async def _determine_realization_stage(self, metrics: UtilizationMetrics,
                                         usage_data: List[Dict[str, Any]]):
        """確定價值實現階段"""
        # 基於使用時間和價值實現率確定階段
        days_since_start = (time.time() - metrics.measurement_period_start) / 86400
        
        if days_since_start <= 7:
            metrics.realization_stage = ValueRealizationStage.ONBOARDING
        elif days_since_start <= 30:
            if metrics.value_realization_rate > 0.3:
                metrics.realization_stage = ValueRealizationStage.ADOPTION
            else:
                metrics.realization_stage = ValueRealizationStage.ONBOARDING
        elif days_since_start <= 90:
            if metrics.value_realization_rate > 0.6:
                metrics.realization_stage = ValueRealizationStage.OPTIMIZATION
            else:
                metrics.realization_stage = ValueRealizationStage.ADOPTION
        else:
            if metrics.value_realization_rate > 0.8 and metrics.expertise_level > 0.6:
                if metrics.innovation_usage > 0.3:
                    metrics.realization_stage = ValueRealizationStage.EXPANSION
                else:
                    metrics.realization_stage = ValueRealizationStage.MASTERY
            else:
                metrics.realization_stage = ValueRealizationStage.OPTIMIZATION
    
    async def _calculate_financial_benefits(self, metrics: UtilizationMetrics,
                                          usage_data: List[Dict[str, Any]]):
        """計算財務效益"""
        # 成本節省
        cost_savings = [d.get('cost_savings', 0) for d in usage_data]
        metrics.cost_savings_realized = sum(cost_savings)
        
        # 收入影響
        revenue_impacts = [d.get('revenue_impact', 0) for d in usage_data]
        metrics.revenue_impact = sum(revenue_impacts)
        
        # 生產力提升（基於時間節省）
        time_savings = [d.get('time_saved_hours', 0) for d in usage_data]
        hourly_value = 50  # 假設每小時價值50元
        metrics.productivity_gain = sum(time_savings) * hourly_value
    
    async def track_value_realization(self, user_id: str, service_id: str,
                                    baseline_metrics: Dict[str, float],
                                    target_metrics: Dict[str, float]) -> ValueRealizationTracker:
        """追蹤價值實現"""
        tracker_key = f"{user_id}_{service_id}"
        
        if tracker_key not in self.value_trackers:
            self.value_trackers[tracker_key] = ValueRealizationTracker(
                user_id=user_id,
                service_id=service_id,
                baseline_metrics=baseline_metrics,
                target_metrics=target_metrics
            )
        
        tracker = self.value_trackers[tracker_key]
        
        # 獲取當前使用效益數據
        utilization_metrics = self.utilization_data.get(tracker_key)
        if utilization_metrics:
            tracker.current_metrics = {
                'realized_value': utilization_metrics.realized_value,
                'value_realization_rate': utilization_metrics.value_realization_rate,
                'task_completion_rate': utilization_metrics.task_completion_rate,
                'satisfaction_score': utilization_metrics.user_satisfaction_score
            }
            
            # 預測未來價值實現
            await self._predict_value_realization(tracker, utilization_metrics)
            
            # 識別成功和阻礙因素
            await self._identify_realization_factors(tracker, utilization_metrics)
        
        tracker.updated_at = time.time()
        return tracker
    
    async def _predict_value_realization(self, tracker: ValueRealizationTracker,
                                       metrics: UtilizationMetrics):
        """預測價值實現"""
        current_rate = metrics.value_realization_rate
        target_value = tracker.target_metrics.get('realized_value', metrics.expected_value)
        
        # 基於當前進度和學習曲線預測
        if metrics.learning_curve_slope > 0:
            # 正向學習曲線，價值實現會加速
            acceleration_factor = 1 + metrics.learning_curve_slope * 0.1
            projected_rate = min(1.0, current_rate * acceleration_factor)
        else:
            # 負向或無學習曲線，保守預測
            projected_rate = current_rate
        
        tracker.projected_value = target_value * projected_rate
        
        # 計算信心區間
        confidence_range = abs(tracker.projected_value * 0.2)  # ±20%
        tracker.confidence_interval = (
            tracker.projected_value - confidence_range,
            tracker.projected_value + confidence_range
        )
        
        # 估算達到目標的時間
        if current_rate > 0 and projected_rate > current_rate:
            improvement_rate = projected_rate - current_rate
            remaining_progress = 1.0 - current_rate
            tracker.time_to_target = remaining_progress / improvement_rate * 30  # 天數
        else:
            tracker.time_to_target = 90  # 默認90天
    
    async def _identify_realization_factors(self, tracker: ValueRealizationTracker,
                                          metrics: UtilizationMetrics):
        """識別價值實現因素"""
        success_factors = []
        blocking_factors = []
        
        # 基於指標識別成功因素
        if metrics.task_completion_rate > 0.8:
            success_factors.append("高任務完成率")
        if metrics.user_satisfaction_score > 4.0:
            success_factors.append("高用戶滿意度")
        if metrics.expertise_level > 0.6:
            success_factors.append("高專業水平")
        if metrics.learning_curve_slope > 0:
            success_factors.append("持續學習改進")
        
        # 識別阻礙因素
        if metrics.error_rate > 0.2:
            blocking_factors.append("高錯誤率")
        if metrics.time_to_first_value > 604800:  # 7天
            blocking_factors.append("價值實現時間過長")
        if metrics.daily_active_usage < 0.3:
            blocking_factors.append("使用頻率不足")
        if metrics.value_realization_rate < 0.4:
            blocking_factors.append("價值實現率低")
        
        tracker.success_factors = success_factors
        tracker.blocking_factors = blocking_factors
    
    async def generate_optimization_recommendations(self, user_id: str, service_id: str) -> List[Dict[str, Any]]:
        """生成優化建議"""
        recommendations = []
        
        metrics_key = f"{user_id}_{service_id}"
        metrics = self.utilization_data.get(metrics_key)
        tracker = self.value_trackers.get(metrics_key)
        
        if not metrics:
            return [{"type": "data_collection", "message": "需要更多使用數據進行分析"}]
        
        # 基於使用狀態的建議
        if metrics.utilization_status == UtilizationStatus.UNDER_UTILIZED:
            recommendations.append({
                "type": "engagement",
                "priority": "high",
                "message": "使用不足，建議增加使用頻率",
                "actions": ["設置使用提醒", "參與入門培訓", "探索核心功能"]
            })
        
        elif metrics.utilization_status == UtilizationStatus.INEFFICIENT:
            recommendations.append({
                "type": "efficiency",
                "priority": "high", 
                "message": "使用效率低，需要優化使用方式",
                "actions": ["檢查工作流程", "學習最佳實踐", "尋求專業指導"]
            })
        
        # 基於價值實現階段的建議
        if metrics.realization_stage == ValueRealizationStage.ONBOARDING:
            recommendations.append({
                "type": "onboarding",
                "priority": "medium",
                "message": "仍在入門階段，建議加強基礎學習",
                "actions": ["完成入門教程", "建立使用習慣", "設定學習目標"]
            })
        
        # 基於具體指標的建議
        if metrics.task_completion_rate < 0.6:
            recommendations.append({
                "type": "task_completion",
                "priority": "medium",
                "message": "任務完成率較低，需要提升執行能力",
                "actions": ["分解復雜任務", "設定完成時限", "追蹤進度"]
            })
        
        if metrics.error_rate > 0.15:
            recommendations.append({
                "type": "error_reduction",
                "priority": "high",
                "message": "錯誤率偏高，需要改善操作準確性",
                "actions": ["檢視常見錯誤", "加強操作訓練", "使用輔助工具"]
            })
        
        # 基於價值追蹤器的建議
        if tracker:
            if tracker.projected_value < tracker.target_metrics.get('realized_value', 0) * 0.8:
                recommendations.append({
                    "type": "value_acceleration",
                    "priority": "high",
                    "message": "價值實現進度落後，需要加速",
                    "actions": ["重新評估目標", "調整使用策略", "尋求支援"]
                })
        
        return recommendations
    
    def get_utilization_summary(self, user_id: str = None) -> Dict[str, Any]:
        """獲取使用效益總結"""
        if user_id:
            # 特定用戶的總結
            user_metrics = {k: v for k, v in self.utilization_data.items() if k.startswith(user_id)}
            if not user_metrics:
                return {"error": f"No data found for user {user_id}"}
            
            total_realized_value = sum(m.realized_value for m in user_metrics.values())
            avg_realization_rate = np.mean([m.value_realization_rate for m in user_metrics.values()])
            
            return {
                "user_id": user_id,
                "services_count": len(user_metrics),
                "total_realized_value": total_realized_value,
                "average_realization_rate": avg_realization_rate,
                "utilization_status_distribution": self._get_status_distribution(user_metrics.values())
            }
        else:
            # 全系統總結
            if not self.utilization_data:
                return {"message": "No utilization data available"}
            
            return {
                "total_users": len(set(k.split('_')[0] for k in self.utilization_data.keys())),
                "total_services": len(set(k.split('_')[1] for k in self.utilization_data.keys())),
                "total_realized_value": sum(m.realized_value for m in self.utilization_data.values()),
                "average_realization_rate": np.mean([m.value_realization_rate for m in self.utilization_data.values()]),
                "utilization_status_distribution": self._get_status_distribution(self.utilization_data.values())
            }
    
    def _get_status_distribution(self, metrics_collection) -> Dict[str, int]:
        """獲取狀態分布"""
        distribution = defaultdict(int)
        for metrics in metrics_collection:
            distribution[metrics.utilization_status.value] += 1
        return dict(distribution)

# 工廠函數
def create_service_utilization_analyzer() -> ServiceUtilizationAnalyzer:
    """創建服務使用效益分析器"""
    return ServiceUtilizationAnalyzer()

def create_utilization_metrics(user_id: str, service_id: str, **kwargs) -> UtilizationMetrics:
    """創建使用效益指標"""
    return UtilizationMetrics(user_id=user_id, service_id=service_id, **kwargs)

def create_value_realization_tracker(user_id: str, service_id: str, **kwargs) -> ValueRealizationTracker:
    """創建價值實現追蹤器"""
    return ValueRealizationTracker(user_id=user_id, service_id=service_id, **kwargs)