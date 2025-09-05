#!/usr/bin/env python3
"""
Performance Feedback System - 性能反饋和動態策略調整
GPT-OSS整合任務1.3.1 - 性能反饋機制

基於實際執行結果優化路由決策：
- 性能反饋收集和分析
- 動態權重調整算法
- 自適應策略優化
- A/B測試支持
"""

import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .ai_task_router import (
    RoutingStrategy, RoutingWeights, DecisionFactor,
    ModelScore, RoutingContext, DecisionAudit
)

logger = logging.getLogger(__name__)

# ==================== 性能反饋數據結構 ====================

class FeedbackType(Enum):
    """反饋類型枚舉"""
    COST_ACTUAL = "cost_actual"           # 實際成本反饋
    LATENCY_ACTUAL = "latency_actual"     # 實際延遲反饋  
    QUALITY_ACTUAL = "quality_actual"     # 實際品質反饋
    SUCCESS_FAILURE = "success_failure"   # 成功失敗反饋
    USER_SATISFACTION = "user_satisfaction"  # 用戶滿意度

@dataclass
class PerformanceFeedback:
    """性能反饋記錄"""
    feedback_id: str
    decision_id: str
    request_id: str
    provider: str
    model_id: str
    task_type: str
    feedback_type: FeedbackType
    predicted_value: float
    actual_value: float
    variance: float = field(init=False)
    accuracy_score: float = field(init=False)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """計算方差和準確度"""
        self.variance = abs(self.actual_value - self.predicted_value)
        
        # 準確度計算（避免除零）
        if self.predicted_value == 0:
            self.accuracy_score = 1.0 if self.actual_value == 0 else 0.0
        else:
            # 相對誤差轉換為準確度分數 (0-1)
            relative_error = abs(self.variance) / abs(self.predicted_value)
            self.accuracy_score = max(0.0, 1.0 - relative_error)

@dataclass
class ModelPerformanceProfile:
    """模型性能檔案"""
    provider: str
    model_id: str
    cost_prediction_accuracy: float = 0.8
    latency_prediction_accuracy: float = 0.8
    quality_prediction_accuracy: float = 0.8
    success_rate: float = 0.95
    total_feedback_count: int = 0
    recent_feedback_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 預測誤差統計
    cost_variance_stats: Dict[str, float] = field(default_factory=dict)
    latency_variance_stats: Dict[str, float] = field(default_factory=dict)
    quality_variance_stats: Dict[str, float] = field(default_factory=dict)

# ==================== 性能反饋系統 ====================

class PerformanceFeedbackSystem:
    """
    性能反饋和動態策略調整系統
    
    功能：
    1. 收集和分析實際執行結果
    2. 計算預測準確度和偏差
    3. 動態調整路由權重
    4. 提供性能洞察和建議
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化性能反饋系統
        
        Args:
            config: 反饋系統配置
        """
        self.config = config or {}
        self._load_default_config()
        
        # 反饋記錄存儲
        self.feedback_history: List[PerformanceFeedback] = []
        self.max_feedback_history = self.config.get('max_feedback_history', 5000)
        
        # 模型性能檔案
        self.model_profiles: Dict[str, ModelPerformanceProfile] = {}
        
        # 權重調整歷史
        self.weight_adjustment_history: List[Dict[str, Any]] = []
        
        # 統計信息
        self.stats = {
            'total_feedback_received': 0,
            'weight_adjustments_made': 0,
            'average_prediction_accuracy': {},
            'best_performing_models': {},
            'worst_performing_models': {},
            'last_update': datetime.now(timezone.utc)
        }
        
        self.logger = logger
        self._initialized = False
    
    def _load_default_config(self):
        """載入預設配置"""
        defaults = {
            'enable_auto_adjustment': True,
            'adjustment_sensitivity': 0.1,      # 調整敏感度 (0.0-1.0)
            'min_feedback_for_adjustment': 20,  # 最少反饋數量才進行調整
            'max_weight_change_per_step': 0.05,  # 每次最大權重變化
            'prediction_accuracy_threshold': 0.7,  # 預測準確度閾值
            'performance_window_hours': 72,     # 性能評估時間窗口
            'auto_adjustment_interval': 3600,   # 自動調整間隔（秒）
            'variance_tolerance': {
                'cost': 0.15,      # 成本方差容忍度
                'latency': 0.20,   # 延遲方差容忍度  
                'quality': 0.10    # 品質方差容忍度
            }
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    async def initialize(self) -> bool:
        """初始化反饋系統"""
        try:
            self.logger.info("🚀 Initializing Performance Feedback System...")
            
            # 載入歷史性能數據（如果有的話）
            await self._load_historical_data()
            
            self._initialized = True
            self.logger.info("✅ Performance Feedback System initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Performance Feedback System: {e}")
            return False
    
    async def _load_historical_data(self):
        """載入歷史性能數據"""
        # 這裡可以從數據庫或檔案系統載入歷史數據
        # 目前作為空實現，可根據需要擴展
        pass
    
    # ==================== 反饋收集接口 ====================
    
    def record_execution_feedback(
        self,
        decision_id: str,
        request_id: str,
        provider: str,
        model_id: str,
        task_type: str,
        predicted_cost: float,
        actual_cost: float,
        predicted_latency: float,
        actual_latency: float,
        predicted_quality: float,
        actual_quality: float,
        execution_success: bool,
        user_satisfaction: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        記錄執行結果反饋
        
        Returns:
            反饋記錄ID列表
        """
        if not self._initialized:
            return []
        
        feedback_ids = []
        
        try:
            # 記錄成本反饋
            cost_feedback = PerformanceFeedback(
                feedback_id=f"cost_{decision_id}_{datetime.now().timestamp()}",
                decision_id=decision_id,
                request_id=request_id,
                provider=provider,
                model_id=model_id,
                task_type=task_type,
                feedback_type=FeedbackType.COST_ACTUAL,
                predicted_value=predicted_cost,
                actual_value=actual_cost,
                metadata=metadata or {}
            )
            
            # 記錄延遲反饋
            latency_feedback = PerformanceFeedback(
                feedback_id=f"latency_{decision_id}_{datetime.now().timestamp()}",
                decision_id=decision_id,
                request_id=request_id,
                provider=provider,
                model_id=model_id,
                task_type=task_type,
                feedback_type=FeedbackType.LATENCY_ACTUAL,
                predicted_value=predicted_latency,
                actual_value=actual_latency,
                metadata=metadata or {}
            )
            
            # 記錄品質反饋
            quality_feedback = PerformanceFeedback(
                feedback_id=f"quality_{decision_id}_{datetime.now().timestamp()}",
                decision_id=decision_id,
                request_id=request_id,
                provider=provider,
                model_id=model_id,
                task_type=task_type,
                feedback_type=FeedbackType.QUALITY_ACTUAL,
                predicted_value=predicted_quality,
                actual_value=actual_quality,
                metadata=metadata or {}
            )
            
            # 添加到歷史記錄
            feedbacks = [cost_feedback, latency_feedback, quality_feedback]
            
            for feedback in feedbacks:
                self.feedback_history.append(feedback)
                feedback_ids.append(feedback.feedback_id)
            
            # 記錄成功失敗反饋
            if not execution_success:
                failure_feedback = PerformanceFeedback(
                    feedback_id=f"failure_{decision_id}_{datetime.now().timestamp()}",
                    decision_id=decision_id,
                    request_id=request_id,
                    provider=provider,
                    model_id=model_id,
                    task_type=task_type,
                    feedback_type=FeedbackType.SUCCESS_FAILURE,
                    predicted_value=1.0,  # 預期成功
                    actual_value=0.0,     # 實際失敗
                    metadata=metadata or {}
                )
                self.feedback_history.append(failure_feedback)
                feedback_ids.append(failure_feedback.feedback_id)
            
            # 記錄用戶滿意度（如果提供）
            if user_satisfaction is not None:
                satisfaction_feedback = PerformanceFeedback(
                    feedback_id=f"satisfaction_{decision_id}_{datetime.now().timestamp()}",
                    decision_id=decision_id,
                    request_id=request_id,
                    provider=provider,
                    model_id=model_id,
                    task_type=task_type,
                    feedback_type=FeedbackType.USER_SATISFACTION,
                    predicted_value=0.8,  # 預期滿意度
                    actual_value=user_satisfaction,
                    metadata=metadata or {}
                )
                self.feedback_history.append(satisfaction_feedback)
                feedback_ids.append(satisfaction_feedback.feedback_id)
            
            # 更新模型性能檔案
            self._update_model_performance_profile(provider, model_id, feedbacks)
            
            # 更新統計
            self.stats['total_feedback_received'] += len(feedbacks)
            
            # 維護歷史記錄大小
            self._maintain_feedback_history()
            
            # 檢查是否需要自動調整權重
            if self.config.get('enable_auto_adjustment', True):
                # 移除 await，因為這是同步函數
                self._check_auto_adjustment_trigger_sync()
            
            self.logger.debug(f"✅ Recorded {len(feedbacks)} feedback records for {provider}/{model_id}")
            
            return feedback_ids
            
        except Exception as e:
            self.logger.error(f"❌ Failed to record execution feedback: {e}")
            return []
    
    def _update_model_performance_profile(
        self,
        provider: str,
        model_id: str,
        feedbacks: List[PerformanceFeedback]
    ):
        """更新模型性能檔案"""
        model_key = f"{provider}/{model_id}"
        
        if model_key not in self.model_profiles:
            self.model_profiles[model_key] = ModelPerformanceProfile(
                provider=provider,
                model_id=model_id
            )
        
        profile = self.model_profiles[model_key]
        
        # 更新各項指標
        for feedback in feedbacks:
            profile.total_feedback_count += 1
            profile.recent_feedback_count += 1
            
            if feedback.feedback_type == FeedbackType.COST_ACTUAL:
                # 更新成本預測準確度
                self._update_prediction_accuracy(
                    profile, 'cost_prediction_accuracy', feedback.accuracy_score
                )
                self._update_variance_stats(
                    profile.cost_variance_stats, feedback.variance
                )
            
            elif feedback.feedback_type == FeedbackType.LATENCY_ACTUAL:
                # 更新延遲預測準確度
                self._update_prediction_accuracy(
                    profile, 'latency_prediction_accuracy', feedback.accuracy_score
                )
                self._update_variance_stats(
                    profile.latency_variance_stats, feedback.variance
                )
            
            elif feedback.feedback_type == FeedbackType.QUALITY_ACTUAL:
                # 更新品質預測準確度
                self._update_prediction_accuracy(
                    profile, 'quality_prediction_accuracy', feedback.accuracy_score
                )
                self._update_variance_stats(
                    profile.quality_variance_stats, feedback.variance
                )
            
            elif feedback.feedback_type == FeedbackType.SUCCESS_FAILURE:
                # 更新成功率
                if feedback.actual_value == 0.0:  # 失敗
                    total_attempts = profile.total_feedback_count
                    success_count = profile.success_rate * (total_attempts - 1)
                    profile.success_rate = success_count / total_attempts
        
        profile.last_updated = datetime.now(timezone.utc)
    
    def _update_prediction_accuracy(
        self,
        profile: ModelPerformanceProfile,
        accuracy_field: str,
        new_accuracy: float
    ):
        """更新預測準確度（使用指數移動平均）"""
        current_accuracy = getattr(profile, accuracy_field)
        alpha = 0.1  # 學習率
        updated_accuracy = current_accuracy * (1 - alpha) + new_accuracy * alpha
        setattr(profile, accuracy_field, updated_accuracy)
    
    def _update_variance_stats(self, variance_stats: Dict[str, float], new_variance: float):
        """更新方差統計"""
        if 'count' not in variance_stats:
            variance_stats.update({
                'count': 0,
                'sum': 0.0,
                'sum_squares': 0.0,
                'mean': 0.0,
                'std': 0.0
            })
        
        # 更新統計數據
        variance_stats['count'] += 1
        variance_stats['sum'] += new_variance
        variance_stats['sum_squares'] += new_variance ** 2
        
        n = variance_stats['count']
        variance_stats['mean'] = variance_stats['sum'] / n
        
        if n > 1:
            variance = (variance_stats['sum_squares'] / n) - (variance_stats['mean'] ** 2)
            variance_stats['std'] = max(0.0, variance) ** 0.5
        else:
            variance_stats['std'] = 0.0
    
    def _maintain_feedback_history(self):
        """維護反饋歷史記錄大小"""
        if len(self.feedback_history) > self.max_feedback_history:
            # 保留最近的記錄
            self.feedback_history = self.feedback_history[-self.max_feedback_history:]
    
    def _check_auto_adjustment_trigger_sync(self):
        """檢查是否觸發自動調整 (同步版本)"""
        try:
            # 檢查是否有足夠的反饋數據
            recent_feedback_count = len([
                f for f in self.feedback_history
                if (datetime.now(timezone.utc) - f.timestamp).total_seconds() < 
                   self.config.get('performance_window_hours', 72) * 3600
            ])
            
            min_feedback = self.config.get('min_feedback_for_adjustment', 20)
            if recent_feedback_count >= min_feedback:
                self.logger.info(f"💡 Auto-adjustment trigger: {recent_feedback_count} recent feedback items")
                # 簡化版本，僅記錄觸發信息
                
        except Exception as e:
            self.logger.error(f"❌ Auto-adjustment trigger check failed: {e}")

    async def _check_auto_adjustment_trigger(self):
        """檢查是否觸發自動調整"""
        try:
            # 檢查是否有足夠的反饋數據
            recent_feedback_count = len([
                f for f in self.feedback_history
                if (datetime.now(timezone.utc) - f.timestamp).total_seconds() < 
                   self.config.get('performance_window_hours', 72) * 3600
            ])
            
            min_feedback = self.config.get('min_feedback_for_adjustment', 20)
            if recent_feedback_count >= min_feedback:
                # 分析性能並建議調整
                adjustments = await self._analyze_and_suggest_adjustments()
                
                if adjustments:
                    self.logger.info(f"💡 Auto-adjustment suggestions generated: {len(adjustments)} items")
                    # 這裡可以選擇自動應用調整或者僅記錄建議
                    for adjustment in adjustments:
                        self.logger.info(f"   • {adjustment['reasoning']}")
            
        except Exception as e:
            self.logger.error(f"❌ Auto adjustment check failed: {e}")
    
    # ==================== 性能分析和權重調整 ====================
    
    async def analyze_performance_trends(
        self,
        hours_back: int = 72,
        min_samples: int = 10
    ) -> Dict[str, Any]:
        """分析性能趨勢"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            recent_feedback = [
                f for f in self.feedback_history
                if f.timestamp >= cutoff_time
            ]
            
            if len(recent_feedback) < min_samples:
                return {
                    'status': 'insufficient_data',
                    'message': f'需要至少 {min_samples} 個樣本，目前只有 {len(recent_feedback)} 個',
                    'analysis': {}
                }
            
            analysis = {
                'overall_accuracy': {},
                'model_performance': {},
                'prediction_errors': {},
                'success_rates': {},
                'variance_analysis': {}
            }
            
            # 按模型分組分析
            model_groups = {}
            for feedback in recent_feedback:
                model_key = f"{feedback.provider}/{feedback.model_id}"
                if model_key not in model_groups:
                    model_groups[model_key] = []
                model_groups[model_key].append(feedback)
            
            # 分析各模型性能
            for model_key, model_feedback in model_groups.items():
                if len(model_feedback) < min_samples:
                    continue
                
                # 按反饋類型分組
                feedback_by_type = {}
                for feedback in model_feedback:
                    feedback_type = feedback.feedback_type
                    if feedback_type not in feedback_by_type:
                        feedback_by_type[feedback_type] = []
                    feedback_by_type[feedback_type].append(feedback)
                
                model_analysis = {}
                
                # 分析各類型反饋
                for feedback_type, type_feedback in feedback_by_type.items():
                    if len(type_feedback) < 3:  # 需要最少樣本
                        continue
                    
                    accuracies = [f.accuracy_score for f in type_feedback]
                    variances = [f.variance for f in type_feedback]
                    
                    model_analysis[feedback_type.value] = {
                        'sample_count': len(type_feedback),
                        'avg_accuracy': statistics.mean(accuracies),
                        'accuracy_std': statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0,
                        'avg_variance': statistics.mean(variances),
                        'variance_std': statistics.stdev(variances) if len(variances) > 1 else 0.0,
                        'accuracy_trend': self._calculate_trend([f.accuracy_score for f in type_feedback[-10:]]),
                        'variance_trend': self._calculate_trend([f.variance for f in type_feedback[-10:]])
                    }
                
                analysis['model_performance'][model_key] = model_analysis
            
            # 整體準確度分析
            for feedback_type in [FeedbackType.COST_ACTUAL, FeedbackType.LATENCY_ACTUAL, FeedbackType.QUALITY_ACTUAL]:
                type_feedback = [f for f in recent_feedback if f.feedback_type == feedback_type]
                if len(type_feedback) >= min_samples:
                    accuracies = [f.accuracy_score for f in type_feedback]
                    variances = [f.variance for f in type_feedback]
                    
                    analysis['overall_accuracy'][feedback_type.value] = {
                        'avg_accuracy': statistics.mean(accuracies),
                        'accuracy_std': statistics.stdev(accuracies) if len(accuracies) > 1 else 0.0,
                        'avg_variance': statistics.mean(variances),
                        'sample_count': len(type_feedback)
                    }
            
            # 成功率分析
            success_feedback = [f for f in recent_feedback if f.feedback_type == FeedbackType.SUCCESS_FAILURE]
            if success_feedback:
                total_attempts = len(success_feedback) + len([f for f in recent_feedback if f.feedback_type != FeedbackType.SUCCESS_FAILURE])
                failures = len(success_feedback)
                analysis['success_rates']['overall'] = {
                    'success_rate': (total_attempts - failures) / total_attempts,
                    'total_attempts': total_attempts,
                    'failures': failures
                }
            
            return {
                'status': 'success',
                'analysis_period_hours': hours_back,
                'total_samples': len(recent_feedback),
                'analysis': analysis,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Performance trend analysis failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """計算趨勢（上升/下降/平穩）"""
        if len(values) < 3:
            return 'insufficient_data'
        
        # 使用線性回歸斜率判斷趨勢
        n = len(values)
        x = list(range(n))
        
        # 計算斜率
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 'stable'
        
        slope = numerator / denominator
        
        # 趨勢判斷
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    async def _analyze_and_suggest_adjustments(self) -> List[Dict[str, Any]]:
        """分析性能並建議權重調整"""
        try:
            adjustments = []
            
            # 獲取性能分析結果
            performance_analysis = await self.analyze_performance_trends(
                hours_back=self.config.get('performance_window_hours', 72)
            )
            
            if performance_analysis['status'] != 'success':
                return adjustments
            
            analysis = performance_analysis['analysis']
            
            # 分析整體準確度問題
            overall_accuracy = analysis.get('overall_accuracy', {})
            variance_tolerance = self.config.get('variance_tolerance', {})
            
            # 成本預測調整建議
            if 'cost_actual' in overall_accuracy:
                cost_acc = overall_accuracy['cost_actual']['avg_accuracy']
                cost_var = overall_accuracy['cost_actual']['avg_variance']
                
                if cost_acc < self.config.get('prediction_accuracy_threshold', 0.7):
                    adjustments.append({
                        'type': 'weight_adjustment',
                        'factor': DecisionFactor.COST,
                        'current_importance': 'unknown',  # 需要從當前路由器獲取
                        'suggested_change': -0.05 if cost_var > variance_tolerance.get('cost', 0.15) else 0.02,
                        'reasoning': f"成本預測準確度 {cost_acc:.3f} 低於閾值，建議{'降低' if cost_var > variance_tolerance.get('cost', 0.15) else '微調'}成本權重"
                    })
            
            # 延遲預測調整建議
            if 'latency_actual' in overall_accuracy:
                latency_acc = overall_accuracy['latency_actual']['avg_accuracy']
                latency_var = overall_accuracy['latency_actual']['avg_variance']
                
                if latency_acc < self.config.get('prediction_accuracy_threshold', 0.7):
                    adjustments.append({
                        'type': 'weight_adjustment',
                        'factor': DecisionFactor.LATENCY,
                        'suggested_change': -0.03 if latency_var > variance_tolerance.get('latency', 0.20) else 0.02,
                        'reasoning': f"延遲預測準確度 {latency_acc:.3f} 低於閾值，建議調整延遲權重"
                    })
            
            # 品質預測調整建議
            if 'quality_actual' in overall_accuracy:
                quality_acc = overall_accuracy['quality_actual']['avg_accuracy']
                quality_var = overall_accuracy['quality_actual']['avg_variance']
                
                if quality_acc < self.config.get('prediction_accuracy_threshold', 0.7):
                    adjustments.append({
                        'type': 'weight_adjustment',
                        'factor': DecisionFactor.QUALITY,
                        'suggested_change': 0.03 if quality_var < variance_tolerance.get('quality', 0.10) else -0.02,
                        'reasoning': f"品質預測準確度 {quality_acc:.3f} 低於閾值，建議{'提高' if quality_var < variance_tolerance.get('quality', 0.10) else '降低'}品質權重"
                    })
            
            # 成功率問題調整建議
            success_rates = analysis.get('success_rates', {})
            if 'overall' in success_rates:
                success_rate = success_rates['overall']['success_rate']
                if success_rate < 0.9:
                    adjustments.append({
                        'type': 'strategy_adjustment',
                        'suggestion': 'increase_availability_weight',
                        'reasoning': f"整體成功率 {success_rate:.3f} 偏低，建議提高可用性權重"
                    })
            
            # 模型特定調整建議
            model_performance = analysis.get('model_performance', {})
            for model_key, model_analysis in model_performance.items():
                # 檢查模型是否有明顯的性能問題
                has_accuracy_issues = any(
                    metrics.get('avg_accuracy', 1.0) < 0.6
                    for metrics in model_analysis.values()
                    if isinstance(metrics, dict)
                )
                
                if has_accuracy_issues:
                    adjustments.append({
                        'type': 'model_recommendation',
                        'model': model_key,
                        'suggestion': 'reduce_selection_probability',
                        'reasoning': f"模型 {model_key} 預測準確度持續偏低，建議降低選擇概率"
                    })
            
            return adjustments
            
        except Exception as e:
            self.logger.error(f"❌ Adjustment analysis failed: {e}")
            return []
    
    def suggest_weight_adjustments(
        self,
        current_weights: RoutingWeights,
        strategy: RoutingStrategy,
        analysis_hours: int = 72
    ) -> Tuple[RoutingWeights, List[str]]:
        """
        基於性能分析建議權重調整
        
        Args:
            current_weights: 當前權重配置
            strategy: 當前路由策略
            analysis_hours: 分析時間窗口
            
        Returns:
            (建議的新權重, 調整原因列表)
        """
        try:
            # 複製當前權重作為基礎
            new_weights = RoutingWeights(
                cost=current_weights.cost,
                latency=current_weights.latency,
                quality=current_weights.quality,
                availability=current_weights.availability,
                privacy=current_weights.privacy,
                user_preference=current_weights.user_preference
            )
            
            adjustment_reasons = []
            max_change = self.config.get('max_weight_change_per_step', 0.05)
            
            # 獲取最近的性能數據
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=analysis_hours)
            recent_feedback = [
                f for f in self.feedback_history
                if f.timestamp >= cutoff_time
            ]
            
            if len(recent_feedback) < self.config.get('min_feedback_for_adjustment', 20):
                return current_weights, ['數據不足，無法進行權重調整建議']
            
            # 按反饋類型分析
            feedback_by_type = {}
            for feedback in recent_feedback:
                if feedback.feedback_type not in feedback_by_type:
                    feedback_by_type[feedback.feedback_type] = []
                feedback_by_type[feedback.feedback_type].append(feedback)
            
            # 成本權重調整
            cost_feedback = feedback_by_type.get(FeedbackType.COST_ACTUAL, [])
            if len(cost_feedback) >= 5:
                cost_accuracies = [f.accuracy_score for f in cost_feedback]
                avg_cost_accuracy = statistics.mean(cost_accuracies)
                cost_variance = statistics.mean([f.variance for f in cost_feedback])
                
                if avg_cost_accuracy < 0.7:
                    if cost_variance > self.config.get('variance_tolerance', {}).get('cost', 0.15):
                        # 成本預測不準且方差大，降低成本權重
                        adjustment = min(max_change, new_weights.cost * 0.1)
                        new_weights.cost = max(0.05, new_weights.cost - adjustment)
                        adjustment_reasons.append(f"成本預測準確度低 ({avg_cost_accuracy:.3f})，降低成本權重")
                    else:
                        # 成本預測不準但方差小，可能需要微調
                        adjustment = min(max_change * 0.5, 0.02)
                        new_weights.cost = min(0.6, new_weights.cost + adjustment)
                        adjustment_reasons.append(f"成本預測需要改進，微調成本權重")
            
            # 延遲權重調整
            latency_feedback = feedback_by_type.get(FeedbackType.LATENCY_ACTUAL, [])
            if len(latency_feedback) >= 5:
                latency_accuracies = [f.accuracy_score for f in latency_feedback]
                avg_latency_accuracy = statistics.mean(latency_accuracies)
                
                if avg_latency_accuracy < 0.7:
                    # 延遲預測不準確，根據策略調整
                    if strategy in [RoutingStrategy.LATENCY_FIRST, RoutingStrategy.PERFORMANCE_OPTIMIZED]:
                        # 對延遲敏感的策略，需要更準確的延遲預測
                        adjustment = min(max_change, 0.03)
                        new_weights.latency = min(0.6, new_weights.latency + adjustment)
                        adjustment_reasons.append(f"延遲預測準確度低，提高延遲權重以改善預測")
                    else:
                        # 非延遲敏感策略，可以降低延遲權重
                        adjustment = min(max_change, new_weights.latency * 0.1)
                        new_weights.latency = max(0.05, new_weights.latency - adjustment)
                        adjustment_reasons.append(f"延遲預測不準確，降低延遲權重")
            
            # 品質權重調整
            quality_feedback = feedback_by_type.get(FeedbackType.QUALITY_ACTUAL, [])
            if len(quality_feedback) >= 5:
                quality_accuracies = [f.accuracy_score for f in quality_feedback]
                avg_quality_accuracy = statistics.mean(quality_accuracies)
                
                if avg_quality_accuracy > 0.85:
                    # 品質預測很準確，可以增加品質權重
                    adjustment = min(max_change * 0.5, 0.02)
                    new_weights.quality = min(0.6, new_weights.quality + adjustment)
                    adjustment_reasons.append(f"品質預測準確度高 ({avg_quality_accuracy:.3f})，提高品質權重")
                elif avg_quality_accuracy < 0.6:
                    # 品質預測很不準確，降低品質權重
                    adjustment = min(max_change, new_weights.quality * 0.15)
                    new_weights.quality = max(0.1, new_weights.quality - adjustment)
                    adjustment_reasons.append(f"品質預測準確度低 ({avg_quality_accuracy:.3f})，降低品質權重")
            
            # 失敗率調整
            failure_feedback = feedback_by_type.get(FeedbackType.SUCCESS_FAILURE, [])
            total_requests = len(recent_feedback)
            failure_rate = len(failure_feedback) / max(total_requests, 1)
            
            if failure_rate > 0.1:  # 失敗率超過10%
                # 提高可用性權重
                adjustment = min(max_change, 0.03)
                new_weights.availability = min(0.4, new_weights.availability + adjustment)
                adjustment_reasons.append(f"失敗率偏高 ({failure_rate:.3f})，提高可用性權重")
            
            # 標準化權重
            new_weights.normalize()
            
            # 檢查調整是否有意義
            total_change = sum([
                abs(new_weights.cost - current_weights.cost),
                abs(new_weights.latency - current_weights.latency),
                abs(new_weights.quality - current_weights.quality),
                abs(new_weights.availability - current_weights.availability),
                abs(new_weights.privacy - current_weights.privacy),
                abs(new_weights.user_preference - current_weights.user_preference)
            ])
            
            if total_change < 0.01:  # 變化太小
                return current_weights, ['基於當前性能分析，權重配置已經相當合適']
            
            return new_weights, adjustment_reasons
            
        except Exception as e:
            self.logger.error(f"❌ Weight adjustment suggestion failed: {e}")
            return current_weights, [f'權重調整建議失敗: {str(e)}']
    
    def apply_weight_adjustments(
        self,
        router,  # AITaskRouter instance
        suggested_weights: RoutingWeights,
        strategy: RoutingStrategy,
        reasons: List[str]
    ) -> bool:
        """
        應用權重調整到路由器
        
        Args:
            router: AITaskRouter實例
            suggested_weights: 建議的新權重
            strategy: 路由策略
            reasons: 調整原因
            
        Returns:
            是否成功應用調整
        """
        try:
            # 記錄調整歷史
            adjustment_record = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'strategy': strategy.value,
                'old_weights': router.routing_strategies.get(strategy).__dict__.copy(),
                'new_weights': suggested_weights.__dict__.copy(),
                'reasons': reasons,
                'feedback_samples_used': len(self.feedback_history)
            }
            
            # 應用調整
            success = router.update_strategy_weights(strategy, suggested_weights)
            
            if success:
                self.weight_adjustment_history.append(adjustment_record)
                self.stats['weight_adjustments_made'] += 1
                self.stats['last_update'] = datetime.now(timezone.utc)
                
                self.logger.info(
                    f"✅ Applied weight adjustments for strategy {strategy.value}:\n"
                    f"   Reasons: {'; '.join(reasons)}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Failed to apply weight adjustments: {e}")
            return False
    
    # ==================== 查詢和報告接口 ====================
    
    def get_model_performance_summary(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        hours_back: int = 168  # 一周
    ) -> Dict[str, Any]:
        """獲取模型性能摘要"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            recent_feedback = [
                f for f in self.feedback_history
                if f.timestamp >= cutoff_time
            ]
            
            # 過濾特定模型
            if provider or model_id:
                filtered_feedback = []
                for feedback in recent_feedback:
                    if provider and feedback.provider != provider:
                        continue
                    if model_id and feedback.model_id != model_id:
                        continue
                    filtered_feedback.append(feedback)
                recent_feedback = filtered_feedback
            
            if not recent_feedback:
                return {'status': 'no_data', 'message': '指定條件下無性能數據'}
            
            # 按模型分組
            model_groups = {}
            for feedback in recent_feedback:
                model_key = f"{feedback.provider}/{feedback.model_id}"
                if model_key not in model_groups:
                    model_groups[model_key] = {
                        'cost': [], 'latency': [], 'quality': [],
                        'failures': 0, 'total': 0
                    }
                
                group = model_groups[model_key]
                group['total'] += 1
                
                if feedback.feedback_type == FeedbackType.COST_ACTUAL:
                    group['cost'].append({
                        'accuracy': feedback.accuracy_score,
                        'variance': feedback.variance,
                        'predicted': feedback.predicted_value,
                        'actual': feedback.actual_value
                    })
                elif feedback.feedback_type == FeedbackType.LATENCY_ACTUAL:
                    group['latency'].append({
                        'accuracy': feedback.accuracy_score,
                        'variance': feedback.variance,
                        'predicted': feedback.predicted_value,
                        'actual': feedback.actual_value
                    })
                elif feedback.feedback_type == FeedbackType.QUALITY_ACTUAL:
                    group['quality'].append({
                        'accuracy': feedback.accuracy_score,
                        'variance': feedback.variance,
                        'predicted': feedback.predicted_value,
                        'actual': feedback.actual_value
                    })
                elif feedback.feedback_type == FeedbackType.SUCCESS_FAILURE:
                    if feedback.actual_value == 0.0:
                        group['failures'] += 1
            
            # 計算摘要統計
            summary = {}
            for model_key, data in model_groups.items():
                model_summary = {
                    'total_samples': data['total'],
                    'success_rate': (data['total'] - data['failures']) / max(data['total'], 1)
                }
                
                # 成本性能
                if data['cost']:
                    model_summary['cost_performance'] = {
                        'avg_accuracy': statistics.mean([d['accuracy'] for d in data['cost']]),
                        'avg_variance': statistics.mean([d['variance'] for d in data['cost']]),
                        'sample_count': len(data['cost'])
                    }
                
                # 延遲性能
                if data['latency']:
                    model_summary['latency_performance'] = {
                        'avg_accuracy': statistics.mean([d['accuracy'] for d in data['latency']]),
                        'avg_variance': statistics.mean([d['variance'] for d in data['latency']]),
                        'sample_count': len(data['latency'])
                    }
                
                # 品質性能
                if data['quality']:
                    model_summary['quality_performance'] = {
                        'avg_accuracy': statistics.mean([d['accuracy'] for d in data['quality']]),
                        'avg_variance': statistics.mean([d['variance'] for d in data['quality']]),
                        'sample_count': len(data['quality'])
                    }
                
                summary[model_key] = model_summary
            
            return {
                'status': 'success',
                'analysis_period_hours': hours_back,
                'total_feedback_samples': len(recent_feedback),
                'models_analyzed': len(summary),
                'summary': summary,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Model performance summary failed: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_adjustment_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """獲取權重調整歷史"""
        try:
            recent_adjustments = self.weight_adjustment_history[-limit:] if limit else self.weight_adjustment_history
            return recent_adjustments
        except Exception as e:
            self.logger.error(f"❌ Failed to get adjustment history: {e}")
            return []
    
    def get_feedback_statistics(self) -> Dict[str, Any]:
        """獲取反饋統計信息"""
        try:
            stats = self.stats.copy()
            
            # 添加實時統計
            total_feedback = len(self.feedback_history)
            if total_feedback > 0:
                # 按類型統計反饋
                feedback_by_type = {}
                for feedback in self.feedback_history:
                    feedback_type = feedback.feedback_type.value
                    feedback_by_type[feedback_type] = feedback_by_type.get(feedback_type, 0) + 1
                
                stats.update({
                    'total_feedback_records': total_feedback,
                    'feedback_by_type': feedback_by_type,
                    'model_profiles_count': len(self.model_profiles),
                    'adjustment_history_count': len(self.weight_adjustment_history)
                })
                
                # 最近24小時的反饋統計
                recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
                recent_feedback = [f for f in self.feedback_history if f.timestamp >= recent_cutoff]
                stats['recent_24h_feedback_count'] = len(recent_feedback)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get feedback statistics: {e}")
            return self.stats.copy()
    
    async def health_check(self) -> Dict[str, Any]:
        """性能反饋系統健康檢查"""
        health_status = {
            'system_initialized': self._initialized,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'statistics': self.get_feedback_statistics(),
            'configuration': {
                'auto_adjustment_enabled': self.config.get('enable_auto_adjustment', True),
                'min_feedback_threshold': self.config.get('min_feedback_for_adjustment', 20),
                'max_history_size': self.max_feedback_history,
                'performance_window_hours': self.config.get('performance_window_hours', 72)
            }
        }
        
        # 數據健康檢查
        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_feedback_count = len([f for f in self.feedback_history if f.timestamp >= recent_cutoff])
        
        if recent_feedback_count == 0:
            health_status['data_status'] = 'no_recent_feedback'
        elif recent_feedback_count < 10:
            health_status['data_status'] = 'limited_feedback'
        else:
            health_status['data_status'] = 'sufficient_feedback'
        
        # 整體健康狀態
        if self._initialized and recent_feedback_count > 0:
            health_status['overall_status'] = 'healthy'
        elif self._initialized:
            health_status['overall_status'] = 'healthy_no_data'
        else:
            health_status['overall_status'] = 'not_initialized'
        
        return health_status