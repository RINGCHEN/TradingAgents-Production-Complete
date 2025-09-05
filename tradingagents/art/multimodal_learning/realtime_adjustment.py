#!/usr/bin/env python3
"""
Real-time Adjustment Mechanism - 實時調整機制
天工 (TianGong) - 動態自適應多模態學習調整系統

此模組提供：
1. 實時性能監控
2. 動態權重調整
3. 閾值自適應優化
4. 模型參數實時更新
5. 異常檢測和處理
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
import json
import time
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor

class AdjustmentTrigger(Enum):
    """調整觸發條件"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ACCURACY_THRESHOLD = "accuracy_threshold"
    PREDICTION_VARIANCE = "prediction_variance"
    DATA_DRIFT = "data_drift"
    USER_FEEDBACK = "user_feedback"
    SCHEDULED_UPDATE = "scheduled_update"
    ANOMALY_DETECTION = "anomaly_detection"

class AdjustmentAction(Enum):
    """調整動作類型"""
    WEIGHT_ADJUSTMENT = "weight_adjustment"
    THRESHOLD_UPDATE = "threshold_update"
    MODEL_RETRAIN = "model_retrain"
    FEATURE_SELECTION = "feature_selection"
    PARAMETER_TUNING = "parameter_tuning"
    CACHE_REFRESH = "cache_refresh"

@dataclass
class PerformanceMetric:
    """性能指標"""
    metric_name: str
    current_value: float
    historical_average: float
    threshold: float
    trend: str  # "improving", "stable", "degrading"
    timestamp: float = field(default_factory=time.time)
    
    def is_below_threshold(self) -> bool:
        return self.current_value < self.threshold
    
    def get_deviation_percentage(self) -> float:
        if self.historical_average == 0:
            return 0.0
        return abs(self.current_value - self.historical_average) / self.historical_average

@dataclass
class AdjustmentRecord:
    """調整記錄"""
    adjustment_id: str
    trigger: AdjustmentTrigger
    action: AdjustmentAction
    parameters_before: Dict[str, Any]
    parameters_after: Dict[str, Any]
    performance_before: Dict[str, float]
    performance_after: Optional[Dict[str, float]] = None
    timestamp: float = field(default_factory=time.time)
    success: bool = False
    error_message: str = ""

class RealTimeAdjustmentManager:
    """實時調整管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 監控配置
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.monitoring_interval = self.config.get('monitoring_interval', 60)  # 秒
        self.performance_window = self.config.get('performance_window', 3600)  # 秒
        
        # 性能指標追蹤
        self.performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self.performance_thresholds = {
            'accuracy': 0.7,
            'processing_time': 30.0,
            'confidence': 0.6,
            'consistency': 0.8,
            'error_rate': 0.1
        }
        self.performance_thresholds.update(
            self.config.get('performance_thresholds', {})
        )
        
        # 調整策略配置
        self.adjustment_strategies = {
            AdjustmentTrigger.PERFORMANCE_DEGRADATION: self._handle_performance_degradation,
            AdjustmentTrigger.ACCURACY_THRESHOLD: self._handle_accuracy_threshold,
            AdjustmentTrigger.PREDICTION_VARIANCE: self._handle_prediction_variance,
            AdjustmentTrigger.DATA_DRIFT: self._handle_data_drift,
            AdjustmentTrigger.USER_FEEDBACK: self._handle_user_feedback,
            AdjustmentTrigger.ANOMALY_DETECTION: self._handle_anomaly_detection
        }
        
        # 調整歷史記錄
        self.adjustment_history: List[AdjustmentRecord] = []
        self.max_history_size = self.config.get('max_history_size', 1000)
        
        # 異步執行器
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.monitoring_task = None
        self.is_running = False
        
        # 回調函數
        self.adjustment_callbacks: List[Callable] = []
        self.performance_callbacks: List[Callable] = []
        
        # 緩存和狀態
        self.current_parameters: Dict[str, Any] = {}
        self.adjustment_lock = threading.Lock()
        
        self.logger.info("RealTimeAdjustmentManager initialized")
    
    async def start_monitoring(self, target_component: Any):
        """開始實時監控"""
        if self.is_running:
            self.logger.warning("監控已經在運行中")
            return
        
        self.target_component = target_component
        self.is_running = True
        
        # 啟動監控任務
        self.monitoring_task = asyncio.create_task(
            self._monitoring_loop()
        )
        
        self.logger.info("實時監控已啟動")
    
    async def stop_monitoring(self):
        """停止實時監控"""
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("實時監控已停止")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 收集性能指標
                current_metrics = await self._collect_performance_metrics()
                
                # 更新性能歷史
                for metric_name, metric in current_metrics.items():
                    self.performance_history[metric_name].append(metric)
                
                # 檢測是否需要調整
                triggers = await self._detect_adjustment_triggers(current_metrics)
                
                # 執行必要的調整
                for trigger, metric_data in triggers:
                    await self._execute_adjustment(trigger, metric_data)
                
                # 執行性能回調
                await self._execute_performance_callbacks(current_metrics)
                
                # 等待下一次監控
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_performance_metrics(self) -> Dict[str, PerformanceMetric]:
        """收集性能指標"""
        metrics = {}
        
        try:
            # 從目標組件獲取統計信息
            if hasattr(self.target_component, 'get_system_statistics'):
                stats = self.target_component.get_system_statistics()
                
                # 處理時間指標
                if 'average_processing_time' in stats:
                    current_time = stats['average_processing_time']
                    historical_avg = self._calculate_historical_average('processing_time')
                    
                    metrics['processing_time'] = PerformanceMetric(
                        metric_name='processing_time',
                        current_value=current_time,
                        historical_average=historical_avg,
                        threshold=self.performance_thresholds['processing_time'],
                        trend=self._calculate_trend('processing_time', current_time)
                    )
                
                # 緩存效率指標
                if 'cache_size' in stats:
                    cache_efficiency = min(stats['cache_size'] / 100, 1.0)  # 標準化
                    historical_avg = self._calculate_historical_average('cache_efficiency')
                    
                    metrics['cache_efficiency'] = PerformanceMetric(
                        metric_name='cache_efficiency',
                        current_value=cache_efficiency,
                        historical_average=historical_avg,
                        threshold=0.5,
                        trend=self._calculate_trend('cache_efficiency', cache_efficiency)
                    )
            
            # 從分析歷史獲取準確性指標
            if hasattr(self.target_component, 'analysis_history'):
                recent_analyses = list(self.target_component.analysis_history)[-50:]
                if recent_analyses:
                    # 信心度指標
                    confidences = [
                        a.confidence_metrics.overall_confidence 
                        for a in recent_analyses 
                        if a.confidence_metrics
                    ]
                    
                    if confidences:
                        avg_confidence = np.mean(confidences)
                        historical_avg = self._calculate_historical_average('confidence')
                        
                        metrics['confidence'] = PerformanceMetric(
                            metric_name='confidence',
                            current_value=avg_confidence,
                            historical_average=historical_avg,
                            threshold=self.performance_thresholds['confidence'],
                            trend=self._calculate_trend('confidence', avg_confidence)
                        )
                    
                    # 一致性指標
                    recommendations = [a.recommendation for a in recent_analyses]
                    consistency = self._calculate_recommendation_consistency(recommendations)
                    historical_avg = self._calculate_historical_average('consistency')
                    
                    metrics['consistency'] = PerformanceMetric(
                        metric_name='consistency',
                        current_value=consistency,
                        historical_average=historical_avg,
                        threshold=self.performance_thresholds['consistency'],
                        trend=self._calculate_trend('consistency', consistency)
                    )
            
        except Exception as e:
            self.logger.error(f"性能指標收集失敗: {e}")
        
        return metrics
    
    def _calculate_historical_average(self, metric_name: str) -> float:
        """計算歷史平均值"""
        if metric_name not in self.performance_history:
            return 0.0
        
        history = self.performance_history[metric_name]
        if not history:
            return 0.0
        
        # 取最近的指標值
        recent_values = [metric.current_value for metric in list(history)[-20:]]
        return np.mean(recent_values) if recent_values else 0.0
    
    def _calculate_trend(self, metric_name: str, current_value: float) -> str:
        """計算趨勢"""
        if metric_name not in self.performance_history:
            return "stable"
        
        history = self.performance_history[metric_name]
        if len(history) < 5:
            return "stable"
        
        # 比較最近幾個值的趨勢
        recent_values = [metric.current_value for metric in list(history)[-5:]]
        recent_values.append(current_value)
        
        # 計算線性趨勢
        x = np.arange(len(recent_values))
        slope = np.polyfit(x, recent_values, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "degrading"
        else:
            return "stable"
    
    def _calculate_recommendation_consistency(self, recommendations: List[str]) -> float:
        """計算推薦一致性"""
        if not recommendations:
            return 1.0
        
        # 計算連續相同推薦的比例
        consistent_count = 0
        for i in range(1, len(recommendations)):
            if recommendations[i] == recommendations[i-1]:
                consistent_count += 1
        
        return consistent_count / max(len(recommendations) - 1, 1)
    
    async def _detect_adjustment_triggers(
        self,
        current_metrics: Dict[str, PerformanceMetric]
    ) -> List[Tuple[AdjustmentTrigger, Dict[str, Any]]]:
        """檢測調整觸發條件"""
        triggers = []
        
        try:
            for metric_name, metric in current_metrics.items():
                # 性能下降觸發
                if metric.trend == "degrading" and metric.is_below_threshold():
                    triggers.append((
                        AdjustmentTrigger.PERFORMANCE_DEGRADATION,
                        {'metric': metric, 'severity': 'high'}
                    ))
                
                # 準確性閾值觸發
                if metric_name == 'confidence' and metric.is_below_threshold():
                    triggers.append((
                        AdjustmentTrigger.ACCURACY_THRESHOLD,
                        {'metric': metric, 'threshold_violation': True}
                    ))
                
                # 預測方差觸發
                if metric_name == 'consistency' and metric.current_value < 0.5:
                    triggers.append((
                        AdjustmentTrigger.PREDICTION_VARIANCE,
                        {'metric': metric, 'variance_level': 'high'}
                    ))
                
                # 異常檢測觸發
                deviation = metric.get_deviation_percentage()
                if deviation > 0.5:  # 50%以上的偏差
                    triggers.append((
                        AdjustmentTrigger.ANOMALY_DETECTION,
                        {'metric': metric, 'deviation': deviation}
                    ))
            
        except Exception as e:
            self.logger.error(f"觸發條件檢測失敗: {e}")
        
        return triggers
    
    async def _execute_adjustment(
        self,
        trigger: AdjustmentTrigger,
        trigger_data: Dict[str, Any]
    ):
        """執行調整"""
        with self.adjustment_lock:
            try:
                # 獲取調整策略
                if trigger not in self.adjustment_strategies:
                    self.logger.warning(f"未找到觸發條件 {trigger} 的調整策略")
                    return
                
                strategy = self.adjustment_strategies[trigger]
                
                # 記錄調整前的參數
                adjustment_record = AdjustmentRecord(
                    adjustment_id=f"adj_{int(time.time())}_{trigger.value}",
                    trigger=trigger,
                    action=AdjustmentAction.WEIGHT_ADJUSTMENT,  # 默認動作
                    parameters_before=self.current_parameters.copy(),
                    performance_before={
                        name: metric.current_value
                        for name, metric in self._get_current_metrics().items()
                    }
                )
                
                # 執行調整策略
                success = await strategy(trigger_data, adjustment_record)
                
                adjustment_record.success = success
                
                if success:
                    # 記錄調整後的參數
                    adjustment_record.parameters_after = self.current_parameters.copy()
                    
                    # 執行調整回調
                    await self._execute_adjustment_callbacks(adjustment_record)
                    
                    self.logger.info(f"成功執行調整: {trigger.value}")
                else:
                    self.logger.warning(f"調整執行失敗: {trigger.value}")
                
                # 記錄調整歷史
                self.adjustment_history.append(adjustment_record)
                
                # 保持歷史記錄在合理範圍內
                if len(self.adjustment_history) > self.max_history_size:
                    self.adjustment_history = self.adjustment_history[-self.max_history_size//2:]
                
            except Exception as e:
                self.logger.error(f"調整執行錯誤: {e}")
                if 'adjustment_record' in locals():
                    adjustment_record.success = False
                    adjustment_record.error_message = str(e)
    
    async def _handle_performance_degradation(
        self,
        trigger_data: Dict[str, Any],
        adjustment_record: AdjustmentRecord
    ) -> bool:
        """處理性能下降"""
        try:
            metric = trigger_data['metric']
            adjustment_record.action = AdjustmentAction.WEIGHT_ADJUSTMENT
            
            # 根據具體指標類型調整
            if metric.metric_name == 'processing_time':
                # 減少批次大小以提高響應時間
                if hasattr(self.target_component, 'batch_size'):
                    old_batch_size = self.target_component.batch_size
                    new_batch_size = max(1, int(old_batch_size * 0.8))
                    self.target_component.batch_size = new_batch_size
                    
                    self.current_parameters['batch_size'] = new_batch_size
                    self.logger.info(f"調整批次大小: {old_batch_size} -> {new_batch_size}")
                    
                return True
            
            elif metric.metric_name == 'cache_efficiency':
                # 清理緩存以提高效率
                if hasattr(self.target_component, 'analysis_cache'):
                    cache_size_before = len(self.target_component.analysis_cache)
                    self.target_component.analysis_cache.clear()
                    
                    self.logger.info(f"清理分析緩存: {cache_size_before} 項目")
                    
                return True
            
        except Exception as e:
            self.logger.error(f"性能下降處理失敗: {e}")
            adjustment_record.error_message = str(e)
        
        return False
    
    async def _handle_accuracy_threshold(
        self,
        trigger_data: Dict[str, Any],
        adjustment_record: AdjustmentRecord
    ) -> bool:
        """處理準確性閾值違反"""
        try:
            metric = trigger_data['metric']
            adjustment_record.action = AdjustmentAction.THRESHOLD_UPDATE
            
            # 調整信心度閾值
            if hasattr(self.target_component, 'adaptive_thresholds'):
                old_threshold = self.target_component.adaptive_thresholds['confidence_threshold']
                # 降低閾值以提高通過率
                new_threshold = max(0.4, old_threshold * 0.9)
                self.target_component.adaptive_thresholds['confidence_threshold'] = new_threshold
                
                self.current_parameters['confidence_threshold'] = new_threshold
                self.logger.info(f"調整信心度閾值: {old_threshold:.2f} -> {new_threshold:.2f}")
                
                return True
            
        except Exception as e:
            self.logger.error(f"準確性閾值處理失敗: {e}")
            adjustment_record.error_message = str(e)
        
        return False
    
    async def _handle_prediction_variance(
        self,
        trigger_data: Dict[str, Any],
        adjustment_record: AdjustmentRecord
    ) -> bool:
        """處理預測方差過大"""
        try:
            adjustment_record.action = AdjustmentAction.PARAMETER_TUNING
            
            # 增加模態權重的穩定性
            if hasattr(self.target_component, 'data_integrator'):
                integrator = self.target_component.data_integrator
                if hasattr(integrator, 'modality_weights'):
                    # 減少權重衰減以增加穩定性
                    old_decay = integrator.modality_weights.weight_decay
                    new_decay = min(0.99, old_decay * 1.05)
                    integrator.modality_weights.weight_decay = new_decay
                    
                    self.current_parameters['weight_decay'] = new_decay
                    self.logger.info(f"調整權重衰減: {old_decay:.3f} -> {new_decay:.3f}")
                    
                    return True
            
        except Exception as e:
            self.logger.error(f"預測方差處理失敗: {e}")
            adjustment_record.error_message = str(e)
        
        return False
    
    async def _handle_data_drift(
        self,
        trigger_data: Dict[str, Any],
        adjustment_record: AdjustmentRecord
    ) -> bool:
        """處理數據漂移"""
        try:
            adjustment_record.action = AdjustmentAction.CACHE_REFRESH
            
            # 清理所有緩存以適應新數據模式
            if hasattr(self.target_component, 'analysis_cache'):
                self.target_component.analysis_cache.clear()
            
            if hasattr(self.target_component, 'text_processor'):
                if hasattr(self.target_component.text_processor, 'clear_cache'):
                    self.target_component.text_processor.clear_cache()
            
            self.logger.info("執行數據漂移調整：清理所有緩存")
            return True
            
        except Exception as e:
            self.logger.error(f"數據漂移處理失敗: {e}")
            adjustment_record.error_message = str(e)
        
        return False
    
    async def _handle_user_feedback(
        self,
        trigger_data: Dict[str, Any],
        adjustment_record: AdjustmentRecord
    ) -> bool:
        """處理用戶反饋"""
        try:
            adjustment_record.action = AdjustmentAction.WEIGHT_ADJUSTMENT
            
            feedback = trigger_data.get('feedback', {})
            accuracy = feedback.get('accuracy', 0.5)
            
            # 根據用戶反饋調整自適應閾值
            if hasattr(self.target_component, 'update_adaptive_thresholds'):
                await self.target_component.update_adaptive_thresholds(feedback)
                
                self.current_parameters['user_feedback_accuracy'] = accuracy
                self.logger.info(f"根據用戶反饋調整參數，準確率: {accuracy}")
                
                return True
            
        except Exception as e:
            self.logger.error(f"用戶反饋處理失敗: {e}")
            adjustment_record.error_message = str(e)
        
        return False
    
    async def _handle_anomaly_detection(
        self,
        trigger_data: Dict[str, Any],
        adjustment_record: AdjustmentRecord
    ) -> bool:
        """處理異常檢測"""
        try:
            metric = trigger_data['metric']
            deviation = trigger_data['deviation']
            
            adjustment_record.action = AdjustmentAction.PARAMETER_TUNING
            
            # 根據異常程度決定調整幅度
            if deviation > 1.0:  # 100%以上偏差
                # 重置相關參數到默認值
                if metric.metric_name == 'processing_time':
                    if hasattr(self.target_component, 'batch_size'):
                        self.target_component.batch_size = 16  # 重置為合理默認值
                        self.current_parameters['batch_size'] = 16
                
                self.logger.warning(f"檢測到嚴重異常，重置參數: {metric.metric_name}")
                return True
            
            elif deviation > 0.5:  # 50%以上偏差
                # 溫和調整參數
                if metric.metric_name == 'confidence':
                    if hasattr(self.target_component, 'adaptive_thresholds'):
                        old_threshold = self.target_component.adaptive_thresholds['confidence_threshold']
                        new_threshold = 0.7  # 重置為中等水平
                        self.target_component.adaptive_thresholds['confidence_threshold'] = new_threshold
                        self.current_parameters['confidence_threshold'] = new_threshold
                
                self.logger.info(f"檢測到中等異常，調整參數: {metric.metric_name}")
                return True
            
        except Exception as e:
            self.logger.error(f"異常檢測處理失敗: {e}")
            adjustment_record.error_message = str(e)
        
        return False
    
    def _get_current_metrics(self) -> Dict[str, PerformanceMetric]:
        """獲取當前指標"""
        current_metrics = {}
        for metric_name, history in self.performance_history.items():
            if history:
                current_metrics[metric_name] = list(history)[-1]
        return current_metrics
    
    async def _execute_adjustment_callbacks(self, adjustment_record: AdjustmentRecord):
        """執行調整回調"""
        for callback in self.adjustment_callbacks:
            try:
                await callback(adjustment_record)
            except Exception as e:
                self.logger.warning(f"調整回調執行失敗: {e}")
    
    async def _execute_performance_callbacks(self, metrics: Dict[str, PerformanceMetric]):
        """執行性能回調"""
        for callback in self.performance_callbacks:
            try:
                await callback(metrics)
            except Exception as e:
                self.logger.warning(f"性能回調執行失敗: {e}")
    
    def add_adjustment_callback(self, callback: Callable):
        """添加調整回調"""
        self.adjustment_callbacks.append(callback)
    
    def add_performance_callback(self, callback: Callable):
        """添加性能回調"""
        self.performance_callbacks.append(callback)
    
    async def manual_adjustment(
        self,
        action: AdjustmentAction,
        parameters: Dict[str, Any],
        reason: str = "manual"
    ) -> bool:
        """手動調整"""
        try:
            adjustment_record = AdjustmentRecord(
                adjustment_id=f"manual_{int(time.time())}",
                trigger=AdjustmentTrigger.USER_FEEDBACK,
                action=action,
                parameters_before=self.current_parameters.copy(),
                performance_before={}
            )
            
            # 應用參數調整
            success = await self._apply_manual_parameters(parameters)
            
            if success:
                adjustment_record.success = True
                adjustment_record.parameters_after = self.current_parameters.copy()
                self.logger.info(f"手動調整成功: {reason}")
            else:
                adjustment_record.success = False
                adjustment_record.error_message = "參數應用失敗"
            
            self.adjustment_history.append(adjustment_record)
            return success
            
        except Exception as e:
            self.logger.error(f"手動調整失敗: {e}")
            return False
    
    async def _apply_manual_parameters(self, parameters: Dict[str, Any]) -> bool:
        """應用手動參數"""
        try:
            for param_name, param_value in parameters.items():
                if param_name == 'batch_size' and hasattr(self.target_component, 'batch_size'):
                    self.target_component.batch_size = param_value
                    self.current_parameters['batch_size'] = param_value
                
                elif param_name == 'confidence_threshold':
                    if hasattr(self.target_component, 'adaptive_thresholds'):
                        self.target_component.adaptive_thresholds['confidence_threshold'] = param_value
                        self.current_parameters['confidence_threshold'] = param_value
                
                elif param_name == 'cache_ttl':
                    if hasattr(self.target_component, 'cache_ttl'):
                        self.target_component.cache_ttl = param_value
                        self.current_parameters['cache_ttl'] = param_value
            
            return True
            
        except Exception as e:
            self.logger.error(f"參數應用失敗: {e}")
            return False
    
    def get_adjustment_statistics(self) -> Dict[str, Any]:
        """獲取調整統計信息"""
        if not self.adjustment_history:
            return {'total_adjustments': 0}
        
        recent_adjustments = self.adjustment_history[-20:]
        
        trigger_counts = defaultdict(int)
        action_counts = defaultdict(int)
        success_count = 0
        
        for record in recent_adjustments:
            trigger_counts[record.trigger.value] += 1
            action_counts[record.action.value] += 1
            if record.success:
                success_count += 1
        
        return {
            'total_adjustments': len(self.adjustment_history),
            'recent_adjustments': len(recent_adjustments),
            'success_rate': success_count / len(recent_adjustments) if recent_adjustments else 0,
            'trigger_distribution': dict(trigger_counts),
            'action_distribution': dict(action_counts),
            'is_monitoring': self.is_running,
            'current_parameters': self.current_parameters.copy()
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取性能摘要"""
        summary = {
            'metrics_tracked': list(self.performance_history.keys()),
            'monitoring_duration': len(list(self.performance_history.values())[0]) * self.monitoring_interval if self.performance_history else 0
        }
        
        # 添加每個指標的統計
        for metric_name, history in self.performance_history.items():
            if history:
                values = [metric.current_value for metric in list(history)[-20:]]
                summary[f'{metric_name}_stats'] = {
                    'current': values[-1] if values else 0,
                    'average': np.mean(values),
                    'std': np.std(values),
                    'trend': list(history)[-1].trend if history else 'unknown'
                }
        
        return summary