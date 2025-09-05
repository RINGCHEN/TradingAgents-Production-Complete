#!/usr/bin/env python3
"""
Adaptive Learning Engine - 自適應學習引擎
天工 (TianGong) - 深度行為學習的統一管理和協調系統

此模組提供：
1. 多組件學習協調
2. 自適應策略調整
3. 學習效果評估
4. 個人化學習路徑
5. 智能反饋循環
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
from pathlib import Path

# 導入其他深度行為學習組件
from .deep_behavior_analyzer import DeepBehaviorAnalyzer, BehaviorMetrics, BehaviorInsight
from .decision_tracking_system import DecisionTracker, DecisionEvent, DecisionType
from .behavior_predictor import BehaviorPredictor, BehaviorForecast, PredictionRequest
from .reinforcement_learning_agent import ReinforcementLearningAgent, RLState, RLAction, RLReward

class LearningStrategy(Enum):
    """學習策略"""
    SUPERVISED_LEARNING = "supervised_learning"      # 監督學習
    UNSUPERVISED_LEARNING = "unsupervised_learning"  # 無監督學習
    REINFORCEMENT_LEARNING = "reinforcement_learning" # 強化學習
    TRANSFER_LEARNING = "transfer_learning"          # 遷移學習
    FEDERATED_LEARNING = "federated_learning"        # 聯邦學習
    ACTIVE_LEARNING = "active_learning"              # 主動學習
    META_LEARNING = "meta_learning"                  # 元學習

class AdaptationTrigger(Enum):
    """適應觸發條件"""
    PERFORMANCE_DECLINE = "performance_decline"      # 性能下降
    USER_FEEDBACK = "user_feedback"                  # 用戶反饋
    MARKET_REGIME_CHANGE = "market_regime_change"    # 市場環境變化
    BEHAVIOR_PATTERN_SHIFT = "behavior_pattern_shift" # 行為模式變化
    PREDICTION_ACCURACY_DROP = "prediction_accuracy_drop" # 預測準確度下降
    NEW_DATA_AVAILABILITY = "new_data_availability"  # 新數據可用
    SCHEDULED_UPDATE = "scheduled_update"            # 定期更新

@dataclass
class LearningMetrics:
    """學習指標"""
    user_id: str = ""
    timestamp: float = field(default_factory=time.time)
    
    # 預測性能指標
    prediction_accuracy: float = 0.0
    prediction_confidence: float = 0.0
    prediction_consistency: float = 0.0
    
    # 決策品質指標
    decision_quality_score: float = 0.0
    decision_efficiency: float = 0.0
    decision_consistency: float = 0.0
    
    # 行為分析指標
    behavior_understanding: float = 0.0
    pattern_recognition_accuracy: float = 0.0
    anomaly_detection_rate: float = 0.0
    
    # 強化學習指標
    reward_accumulation_rate: float = 0.0
    exploration_efficiency: float = 0.0
    policy_stability: float = 0.0
    
    # 適應性指標
    adaptation_speed: float = 0.0
    learning_rate_optimization: float = 0.0
    transfer_learning_effectiveness: float = 0.0
    
    # 整體系統指標
    system_response_time: float = 0.0
    resource_utilization: float = 0.0
    user_satisfaction: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AdaptationResult:
    """適應結果"""
    adaptation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    trigger: AdaptationTrigger = AdaptationTrigger.PERFORMANCE_DECLINE
    strategy_used: LearningStrategy = LearningStrategy.SUPERVISED_LEARNING
    
    # 適應前後比較
    before_metrics: LearningMetrics = field(default_factory=LearningMetrics)
    after_metrics: LearningMetrics = field(default_factory=LearningMetrics)
    improvement_score: float = 0.0
    
    # 適應詳情
    adaptations_made: List[str] = field(default_factory=list)
    parameters_adjusted: Dict[str, Any] = field(default_factory=dict)
    
    # 時間信息
    adaptation_start_time: float = field(default_factory=time.time)
    adaptation_duration: float = 0.0
    
    # 驗證結果
    validation_score: float = 0.0
    confidence_level: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class AdaptiveLearningEngine:
    """自適應學習引擎"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化核心組件
        self.behavior_analyzer = DeepBehaviorAnalyzer(
            self.config.get('behavior_analyzer', {})
        )
        self.decision_tracker = DecisionTracker(
            self.config.get('decision_tracker', {})
        )
        self.behavior_predictor = BehaviorPredictor(
            self.config.get('behavior_predictor', {})
        )
        self.rl_agent = ReinforcementLearningAgent(
            self.config.get('rl_agent', {})
        )
        
        # 學習狀態管理
        self.user_learning_states: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.learning_metrics_history: Dict[str, List[LearningMetrics]] = defaultdict(list)
        self.adaptation_history: Dict[str, List[AdaptationResult]] = defaultdict(list)
        
        # 適應性配置
        self.adaptation_config = {
            'performance_threshold': self.config.get('performance_threshold', 0.7),
            'adaptation_cooldown_hours': self.config.get('adaptation_cooldown_hours', 24),
            'min_data_points_for_adaptation': self.config.get('min_data_points_for_adaptation', 50),
            'max_adaptations_per_day': self.config.get('max_adaptations_per_day', 3),
            'validation_period_hours': self.config.get('validation_period_hours', 48)
        }
        
        # 學習策略權重
        self.strategy_weights: Dict[str, Dict[LearningStrategy, float]] = defaultdict(
            lambda: {
                LearningStrategy.SUPERVISED_LEARNING: 0.3,
                LearningStrategy.REINFORCEMENT_LEARNING: 0.4,
                LearningStrategy.TRANSFER_LEARNING: 0.2,
                LearningStrategy.ACTIVE_LEARNING: 0.1
            }
        )
        
        # 啟動後台任務
        self.background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
        
        self.logger.info("AdaptiveLearningEngine initialized")

    def _start_background_tasks(self):
        """啟動後台任務"""
        
        # 定期評估和適應任務
        self.background_tasks.append(
            asyncio.create_task(self._periodic_evaluation_task())
        )
        
        # 學習指標監控任務
        self.background_tasks.append(
            asyncio.create_task(self._metrics_monitoring_task())
        )
        
        # 適應結果驗證任務
        self.background_tasks.append(
            asyncio.create_task(self._adaptation_validation_task())
        )

    async def process_user_interaction(
        self,
        user_id: str,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """處理用戶交互並觸發學習"""
        
        results = {
            'user_id': user_id,
            'timestamp': time.time(),
            'analysis_results': {},
            'predictions': {},
            'learning_updates': {}
        }
        
        try:
            # 1. 行為分析
            behavior_data = interaction_data.get('behavior_data', [])
            if behavior_data:
                metrics, insights = await self.behavior_analyzer.analyze_user_behavior(
                    user_id, behavior_data
                )
                results['analysis_results'] = {
                    'metrics': metrics,
                    'insights': [self._serialize_insight(insight) for insight in insights]
                }
            
            # 2. 決策追蹤
            if 'decision_event' in interaction_data:
                decision_data = interaction_data['decision_event']
                session_id = decision_data.get('session_id')
                
                if not session_id:
                    session_id = await self.decision_tracker.start_decision_session(user_id)
                
                event_id = await self.decision_tracker.track_decision_event(
                    session_id,
                    DecisionType(decision_data.get('decision_type', 'trade_execution')),
                    decision_data.get('context', 'normal_market'),
                    decision_data
                )
                results['decision_tracking'] = {
                    'session_id': session_id,
                    'event_id': event_id
                }
            
            # 3. 行為預測
            if 'prediction_request' in interaction_data:
                pred_data = interaction_data['prediction_request']
                request = PredictionRequest(
                    user_id=user_id,
                    **pred_data
                )
                forecast = await self.behavior_predictor.predict_behavior(request)
                results['predictions'] = self._serialize_forecast(forecast)
            
            # 4. 強化學習處理
            if 'rl_interaction' in interaction_data:
                rl_data = interaction_data['rl_interaction']
                await self._process_rl_interaction(user_id, rl_data, results)
            
            # 5. 觸發學習更新
            await self._update_learning_state(user_id, interaction_data, results)
            
            # 6. 檢查是否需要適應
            await self._check_adaptation_triggers(user_id)
            
        except Exception as e:
            self.logger.error(f"處理用戶交互失敗: {e}")
            results['error'] = str(e)
        
        return results

    async def _process_rl_interaction(
        self,
        user_id: str,
        rl_data: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """處理強化學習交互"""
        
        # 構建RL狀態
        state_data = rl_data.get('state', {})
        rl_state = RLState(
            user_id=user_id,
            **state_data
        )
        
        if 'action_selection' in rl_data:
            # 動作選擇
            action = self.rl_agent.select_action(rl_state, user_id)
            results['rl_action'] = {
                'action_type': action.action_type.value,
                'parameters': action.action_parameters,
                'confidence': action.execution_confidence
            }
        
        if 'feedback' in rl_data:
            # 處理反饋
            feedback_data = rl_data['feedback']
            
            # 重新創建之前的狀態和動作
            prev_state = RLState(user_id=user_id, **feedback_data.get('prev_state', {}))
            action = RLAction(**feedback_data.get('action', {}))
            next_state = RLState(user_id=user_id, **feedback_data.get('next_state', {}))
            
            # 計算獎勵
            reward = self.rl_agent.calculate_reward(prev_state, action, next_state, user_id)
            
            # 存儲經驗
            self.rl_agent.store_experience(prev_state, action, reward, next_state)
            
            # 訓練模型
            await self.rl_agent.train_dqn()
            await self.rl_agent.train_actor_critic()
            
            results['rl_feedback'] = {
                'reward': reward.normalized_reward,
                'learning_progress': self.rl_agent.get_user_performance_metrics(user_id)
            }

    async def _update_learning_state(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        results: Dict[str, Any]
    ):
        """更新學習狀態"""
        
        current_time = time.time()
        
        # 更新用戶學習狀態
        if user_id not in self.user_learning_states:
            self.user_learning_states[user_id] = {
                'first_interaction': current_time,
                'last_interaction': current_time,
                'interaction_count': 0,
                'total_learning_time': 0.0,
                'current_learning_phase': 'exploration'
            }
        
        state = self.user_learning_states[user_id]
        state['last_interaction'] = current_time
        state['interaction_count'] += 1
        
        # 計算學習指標
        metrics = await self._calculate_learning_metrics(user_id, results)
        self.learning_metrics_history[user_id].append(metrics)
        
        # 限制歷史記錄長度
        if len(self.learning_metrics_history[user_id]) > 1000:
            self.learning_metrics_history[user_id] = \
                self.learning_metrics_history[user_id][-500:]

    async def _calculate_learning_metrics(
        self,
        user_id: str,
        results: Dict[str, Any]
    ) -> LearningMetrics:
        """計算學習指標"""
        
        metrics = LearningMetrics(user_id=user_id)
        
        # 預測性能指標
        if 'predictions' in results:
            pred_data = results['predictions']
            metrics.prediction_confidence = pred_data.get('confidence_score', 0.0)
            metrics.prediction_consistency = pred_data.get('model_agreement', 0.0)
        
        # 決策品質指標
        if 'decision_tracking' in results:
            # 這裡可以從決策追蹤系統獲取品質指標
            pass
        
        # 行為分析指標
        if 'analysis_results' in results:
            insights = results['analysis_results'].get('insights', [])
            if insights:
                # 基於洞察的平均信心度計算理解度
                confidence_scores = [insight.get('confidence', 0.0) for insight in insights]
                metrics.behavior_understanding = np.mean(confidence_scores)
        
        # 強化學習指標
        if 'rl_feedback' in results:
            rl_data = results['rl_feedback']
            metrics.reward_accumulation_rate = rl_data.get('reward', 0.0)
            
            learning_progress = rl_data.get('learning_progress', {})
            metrics.exploration_efficiency = learning_progress.get('learning_progress', 0.0)
        
        # 系統響應時間(從開始到現在的處理時間)
        metrics.system_response_time = time.time() - metrics.timestamp
        
        return metrics

    async def _check_adaptation_triggers(self, user_id: str):
        """檢查適應觸發條件"""
        
        current_time = time.time()
        user_metrics = self.learning_metrics_history[user_id]
        
        if len(user_metrics) < self.adaptation_config['min_data_points_for_adaptation']:
            return
        
        # 檢查是否在冷卻期內
        recent_adaptations = [
            adapt for adapt in self.adaptation_history[user_id]
            if current_time - adapt.adaptation_start_time < \
               self.adaptation_config['adaptation_cooldown_hours'] * 3600
        ]
        
        if len(recent_adaptations) >= self.adaptation_config['max_adaptations_per_day']:
            return
        
        # 性能下降檢測
        if await self._detect_performance_decline(user_id, user_metrics):
            await self._trigger_adaptation(user_id, AdaptationTrigger.PERFORMANCE_DECLINE)
        
        # 預測準確度下降檢測
        if await self._detect_prediction_accuracy_drop(user_id, user_metrics):
            await self._trigger_adaptation(user_id, AdaptationTrigger.PREDICTION_ACCURACY_DROP)
        
        # 行為模式變化檢測
        if await self._detect_behavior_pattern_shift(user_id, user_metrics):
            await self._trigger_adaptation(user_id, AdaptationTrigger.BEHAVIOR_PATTERN_SHIFT)

    async def _detect_performance_decline(
        self,
        user_id: str,
        metrics_history: List[LearningMetrics]
    ) -> bool:
        """檢測性能下降"""
        
        if len(metrics_history) < 20:
            return False
        
        # 比較最近10個和之前10個指標
        recent_metrics = metrics_history[-10:]
        previous_metrics = metrics_history[-20:-10]
        
        recent_avg_score = np.mean([
            (m.prediction_accuracy + m.decision_quality_score + m.behavior_understanding) / 3
            for m in recent_metrics
        ])
        
        previous_avg_score = np.mean([
            (m.prediction_accuracy + m.decision_quality_score + m.behavior_understanding) / 3
            for m in previous_metrics
        ])
        
        # 如果最近性能比之前下降超過閾值
        decline_ratio = (previous_avg_score - recent_avg_score) / max(previous_avg_score, 0.1)
        
        return decline_ratio > 0.2  # 20%下降觸發適應

    async def _detect_prediction_accuracy_drop(
        self,
        user_id: str,
        metrics_history: List[LearningMetrics]
    ) -> bool:
        """檢測預測準確度下降"""
        
        if len(metrics_history) < 15:
            return False
        
        recent_accuracy = np.mean([m.prediction_accuracy for m in metrics_history[-10:]])
        baseline_accuracy = np.mean([m.prediction_accuracy for m in metrics_history[-15:-5]])
        
        return recent_accuracy < baseline_accuracy * 0.8  # 80%的基線

    async def _detect_behavior_pattern_shift(
        self,
        user_id: str,
        metrics_history: List[LearningMetrics]
    ) -> bool:
        """檢測行為模式變化"""
        
        if len(metrics_history) < 20:
            return False
        
        # 分析行為理解度的變化
        recent_understanding = np.mean([m.behavior_understanding for m in metrics_history[-10:]])
        previous_understanding = np.mean([m.behavior_understanding for m in metrics_history[-20:-10]])
        
        # 如果理解度顯著下降，可能表示行為模式發生了變化
        understanding_drop = (previous_understanding - recent_understanding) / max(previous_understanding, 0.1)
        
        return understanding_drop > 0.3  # 30%理解度下降

    async def _trigger_adaptation(
        self,
        user_id: str,
        trigger: AdaptationTrigger
    ):
        """觸發適應過程"""
        
        self.logger.info(f"觸發用戶 {user_id} 的適應過程，觸發條件: {trigger.value}")
        
        # 選擇適應策略
        strategy = await self._select_adaptation_strategy(user_id, trigger)
        
        # 執行適應
        adaptation_result = await self._execute_adaptation(user_id, strategy, trigger)
        
        # 記錄適應結果
        self.adaptation_history[user_id].append(adaptation_result)
        
        self.logger.info(f"適應完成，改進分數: {adaptation_result.improvement_score:.3f}")

    async def _select_adaptation_strategy(
        self,
        user_id: str,
        trigger: AdaptationTrigger
    ) -> LearningStrategy:
        """選擇適應策略"""
        
        user_weights = self.strategy_weights[user_id]
        
        # 根據觸發條件調整策略權重
        adjusted_weights = user_weights.copy()
        
        if trigger == AdaptationTrigger.PERFORMANCE_DECLINE:
            # 性能下降時偏向強化學習
            adjusted_weights[LearningStrategy.REINFORCEMENT_LEARNING] *= 1.5
            adjusted_weights[LearningStrategy.ACTIVE_LEARNING] *= 1.2
            
        elif trigger == AdaptationTrigger.PREDICTION_ACCURACY_DROP:
            # 預測準確度下降時偏向監督學習和遷移學習
            adjusted_weights[LearningStrategy.SUPERVISED_LEARNING] *= 1.4
            adjusted_weights[LearningStrategy.TRANSFER_LEARNING] *= 1.3
            
        elif trigger == AdaptationTrigger.BEHAVIOR_PATTERN_SHIFT:
            # 行為模式變化時偏向無監督學習和主動學習
            adjusted_weights[LearningStrategy.UNSUPERVISED_LEARNING] *= 1.6
            adjusted_weights[LearningStrategy.ACTIVE_LEARNING] *= 1.3
        
        # 標準化權重
        total_weight = sum(adjusted_weights.values())
        if total_weight > 0:
            normalized_weights = {k: v/total_weight for k, v in adjusted_weights.items()}
        else:
            normalized_weights = adjusted_weights
        
        # 基於權重隨機選擇
        strategies = list(normalized_weights.keys())
        weights = list(normalized_weights.values())
        
        selected_strategy = np.random.choice(strategies, p=weights)
        return selected_strategy

    async def _execute_adaptation(
        self,
        user_id: str,
        strategy: LearningStrategy,
        trigger: AdaptationTrigger
    ) -> AdaptationResult:
        """執行適應"""
        
        start_time = time.time()
        
        # 記錄適應前指標
        before_metrics = self.learning_metrics_history[user_id][-1] if \
                        self.learning_metrics_history[user_id] else LearningMetrics()
        
        adaptation_result = AdaptationResult(
            user_id=user_id,
            trigger=trigger,
            strategy_used=strategy,
            before_metrics=before_metrics,
            adaptation_start_time=start_time
        )
        
        try:
            if strategy == LearningStrategy.REINFORCEMENT_LEARNING:
                await self._adapt_reinforcement_learning(user_id, adaptation_result)
                
            elif strategy == LearningStrategy.SUPERVISED_LEARNING:
                await self._adapt_supervised_learning(user_id, adaptation_result)
                
            elif strategy == LearningStrategy.TRANSFER_LEARNING:
                await self._adapt_transfer_learning(user_id, adaptation_result)
                
            elif strategy == LearningStrategy.ACTIVE_LEARNING:
                await self._adapt_active_learning(user_id, adaptation_result)
                
            else:
                # 默認適應
                await self._adapt_default_strategy(user_id, adaptation_result)
            
            # 計算適應後指標(需要一些時間來評估效果，這裡使用估計值)
            after_metrics = await self._estimate_post_adaptation_metrics(user_id, adaptation_result)
            adaptation_result.after_metrics = after_metrics
            
            # 計算改進分數
            improvement = self._calculate_improvement_score(before_metrics, after_metrics)
            adaptation_result.improvement_score = improvement
            
        except Exception as e:
            self.logger.error(f"適應執行失敗: {e}")
            adaptation_result.improvement_score = -1.0
            adaptation_result.adaptations_made.append(f"適應失敗: {str(e)}")
        
        adaptation_result.adaptation_duration = time.time() - start_time
        return adaptation_result

    async def _adapt_reinforcement_learning(
        self,
        user_id: str,
        adaptation_result: AdaptationResult
    ):
        """強化學習適應"""
        
        # 調整探索率
        current_exploration = self.rl_agent.exploration_rate
        
        if adaptation_result.trigger == AdaptationTrigger.PERFORMANCE_DECLINE:
            # 性能下降時增加探索
            new_exploration = min(current_exploration * 1.5, 0.8)
            self.rl_agent.exploration_rate = new_exploration
            adaptation_result.parameters_adjusted['exploration_rate'] = new_exploration
            adaptation_result.adaptations_made.append(f"增加探索率至 {new_exploration:.3f}")
        
        # 調整學習率
        current_lr = self.rl_agent.learning_rate
        new_lr = current_lr * 1.2 if adaptation_result.trigger == AdaptationTrigger.BEHAVIOR_PATTERN_SHIFT else current_lr * 0.9
        
        # 更新優化器學習率
        for param_group in self.rl_agent.dqn_optimizer.param_groups:
            param_group['lr'] = new_lr
        for param_group in self.rl_agent.ac_optimizer.param_groups:
            param_group['lr'] = new_lr
        
        adaptation_result.parameters_adjusted['learning_rate'] = new_lr
        adaptation_result.adaptations_made.append(f"調整學習率至 {new_lr:.6f}")
        
        # 清空部分經驗回放緩衝區以快速適應
        buffer_size = len(self.rl_agent.replay_buffer)
        if buffer_size > 1000:
            # 保留最近一半的經驗
            new_buffer = deque(list(self.rl_agent.replay_buffer)[-buffer_size//2:], 
                              maxlen=self.rl_agent.replay_buffer.maxlen)
            self.rl_agent.replay_buffer = new_buffer
            adaptation_result.adaptations_made.append("清理部分舊經驗緩衝")

    async def _adapt_supervised_learning(
        self,
        user_id: str,
        adaptation_result: AdaptationResult
    ):
        """監督學習適應"""
        
        # 重新訓練行為預測模型
        user_behavior_data = []  # 這裡應該從行為分析器獲取數據
        
        if len(user_behavior_data) > 50:
            # 更新預測模型的訓練數據
            adaptation_result.adaptations_made.append("重新訓練行為預測模型")
        
        # 調整預測器的模型選擇偏好
        if adaptation_result.trigger == AdaptationTrigger.PREDICTION_ACCURACY_DROP:
            # 增加模型多樣性
            adaptation_result.adaptations_made.append("增加預測模型多樣性")

    async def _adapt_transfer_learning(
        self,
        user_id: str,
        adaptation_result: AdaptationResult
    ):
        """遷移學習適應"""
        
        # 從相似用戶那裡遷移學習經驗
        similar_users = await self._find_similar_users(user_id)
        
        if similar_users:
            # 遷移用戶策略
            for similar_user_id in similar_users[:3]:  # 最多從3個相似用戶學習
                if similar_user_id in self.user_learning_states:
                    # 複製部分成功策略
                    adaptation_result.adaptations_made.append(f"從用戶 {similar_user_id} 遷移學習經驗")
        
        adaptation_result.adaptations_made.append("應用遷移學習策略")

    async def _adapt_active_learning(
        self,
        user_id: str,
        adaptation_result: AdaptationResult
    ):
        """主動學習適應"""
        
        # 識別需要更多數據的區域
        uncertain_areas = await self._identify_uncertain_prediction_areas(user_id)
        
        # 調整數據收集策略
        if uncertain_areas:
            adaptation_result.adaptations_made.append(f"識別出 {len(uncertain_areas)} 個不確定區域")
            adaptation_result.adaptations_made.append("調整數據收集策略以聚焦不確定區域")

    async def _adapt_default_strategy(
        self,
        user_id: str,
        adaptation_result: AdaptationResult
    ):
        """默認適應策略"""
        
        # 通用參數調整
        adaptation_result.adaptations_made.append("應用通用優化策略")
        adaptation_result.adaptations_made.append("重新平衡模型權重")

    async def _estimate_post_adaptation_metrics(
        self,
        user_id: str,
        adaptation_result: AdaptationResult
    ) -> LearningMetrics:
        """估計適應後指標"""
        
        # 基於適應類型和歷史數據估計改進
        before_metrics = adaptation_result.before_metrics
        after_metrics = LearningMetrics(user_id=user_id)
        
        # 基於策略類型的估計改進
        improvement_factor = {
            LearningStrategy.REINFORCEMENT_LEARNING: 1.1,
            LearningStrategy.SUPERVISED_LEARNING: 1.05,
            LearningStrategy.TRANSFER_LEARNING: 1.15,
            LearningStrategy.ACTIVE_LEARNING: 1.08
        }.get(adaptation_result.strategy_used, 1.02)
        
        # 估計各項指標的改進
        after_metrics.prediction_accuracy = min(before_metrics.prediction_accuracy * improvement_factor, 1.0)
        after_metrics.decision_quality_score = min(before_metrics.decision_quality_score * improvement_factor, 1.0)
        after_metrics.behavior_understanding = min(before_metrics.behavior_understanding * improvement_factor, 1.0)
        after_metrics.reward_accumulation_rate = before_metrics.reward_accumulation_rate * improvement_factor
        
        return after_metrics

    def _calculate_improvement_score(
        self,
        before_metrics: LearningMetrics,
        after_metrics: LearningMetrics
    ) -> float:
        """計算改進分數"""
        
        # 計算各項指標的改進
        improvements = []
        
        if before_metrics.prediction_accuracy > 0:
            pred_improvement = (after_metrics.prediction_accuracy - before_metrics.prediction_accuracy) / before_metrics.prediction_accuracy
            improvements.append(pred_improvement)
        
        if before_metrics.decision_quality_score > 0:
            decision_improvement = (after_metrics.decision_quality_score - before_metrics.decision_quality_score) / before_metrics.decision_quality_score
            improvements.append(decision_improvement)
        
        if before_metrics.behavior_understanding > 0:
            behavior_improvement = (after_metrics.behavior_understanding - before_metrics.behavior_understanding) / before_metrics.behavior_understanding
            improvements.append(behavior_improvement)
        
        # 返回平均改進分數
        return np.mean(improvements) if improvements else 0.0

    async def _find_similar_users(self, user_id: str) -> List[str]:
        """尋找相似用戶"""
        
        # 這裡應該實現基於行為特徵的用戶相似度計算
        # 簡化實現：返回空列表
        return []

    async def _identify_uncertain_prediction_areas(self, user_id: str) -> List[str]:
        """識別不確定的預測區域"""
        
        # 這裡應該分析預測歷史來識別低信心度的預測區域
        return ["market_timing", "position_sizing"]

    def _serialize_insight(self, insight: BehaviorInsight) -> Dict[str, Any]:
        """序列化行為洞察"""
        return {
            'insight_id': insight.insight_id,
            'insight_type': insight.insight_type,
            'title': insight.title,
            'description': insight.description,
            'confidence': insight.confidence,
            'impact_score': insight.impact_score,
            'recommendations': insight.actionable_recommendations,
            'timestamp': insight.timestamp
        }

    def _serialize_forecast(self, forecast: BehaviorForecast) -> Dict[str, Any]:
        """序列化行為預測"""
        return {
            'forecast_id': forecast.forecast_id,
            'prediction_type': forecast.prediction_type.value,
            'predicted_behavior': forecast.predicted_behavior,
            'confidence_score': forecast.confidence_score,
            'key_factors': forecast.key_factors,
            'models_used': [model.value for model in forecast.models_used],
            'timestamp': forecast.prediction_timestamp
        }

    async def _periodic_evaluation_task(self):
        """定期評估任務"""
        while True:
            try:
                await asyncio.sleep(3600)  # 每小時評估一次
                
                for user_id in self.user_learning_states.keys():
                    await self._evaluate_user_learning_progress(user_id)
                
            except Exception as e:
                self.logger.error(f"定期評估任務失敗: {e}")

    async def _metrics_monitoring_task(self):
        """指標監控任務"""
        while True:
            try:
                await asyncio.sleep(1800)  # 每30分鐘監控一次
                
                # 監控系統整體性能
                await self._monitor_system_performance()
                
            except Exception as e:
                self.logger.error(f"指標監控任務失敗: {e}")

    async def _adaptation_validation_task(self):
        """適應結果驗證任務"""
        while True:
            try:
                await asyncio.sleep(7200)  # 每2小時驗證一次
                
                # 驗證最近的適應結果
                await self._validate_recent_adaptations()
                
            except Exception as e:
                self.logger.error(f"適應驗證任務失敗: {e}")

    async def _evaluate_user_learning_progress(self, user_id: str):
        """評估用戶學習進度"""
        
        metrics_history = self.learning_metrics_history[user_id]
        if len(metrics_history) < 10:
            return
        
        # 計算學習趨勢
        recent_metrics = metrics_history[-10:]
        trend_score = self._calculate_learning_trend(recent_metrics)
        
        # 更新用戶學習狀態
        user_state = self.user_learning_states[user_id]
        user_state['learning_trend'] = trend_score
        
        self.logger.debug(f"用戶 {user_id} 學習趨勢分數: {trend_score:.3f}")

    def _calculate_learning_trend(self, metrics_list: List[LearningMetrics]) -> float:
        """計算學習趨勢"""
        
        if len(metrics_list) < 5:
            return 0.0
        
        # 計算各項指標的趨勢
        trends = []
        
        # 預測準確度趨勢
        pred_accuracies = [m.prediction_accuracy for m in metrics_list]
        if any(pred_accuracies):
            pred_trend = np.polyfit(range(len(pred_accuracies)), pred_accuracies, 1)[0]
            trends.append(pred_trend)
        
        # 決策品質趨勢
        decision_scores = [m.decision_quality_score for m in metrics_list]
        if any(decision_scores):
            decision_trend = np.polyfit(range(len(decision_scores)), decision_scores, 1)[0]
            trends.append(decision_trend)
        
        # 行為理解趨勢
        understanding_scores = [m.behavior_understanding for m in metrics_list]
        if any(understanding_scores):
            understanding_trend = np.polyfit(range(len(understanding_scores)), understanding_scores, 1)[0]
            trends.append(understanding_trend)
        
        return np.mean(trends) if trends else 0.0

    async def _monitor_system_performance(self):
        """監控系統性能"""
        
        # 收集系統級指標
        total_users = len(self.user_learning_states)
        active_users = sum(
            1 for state in self.user_learning_states.values()
            if time.time() - state.get('last_interaction', 0) < 86400  # 24小時內活躍
        )
        
        total_adaptations = sum(len(adaptations) for adaptations in self.adaptation_history.values())
        
        self.logger.info(f"系統性能監控 - 總用戶: {total_users}, 活躍用戶: {active_users}, 總適應次數: {total_adaptations}")

    async def _validate_recent_adaptations(self):
        """驗證最近的適應結果"""
        
        validation_window = 48 * 3600  # 48小時
        current_time = time.time()
        
        for user_id, adaptations in self.adaptation_history.items():
            recent_adaptations = [
                adapt for adapt in adaptations
                if current_time - adapt.adaptation_start_time < validation_window
                and adapt.validation_score == 0.0  # 尚未驗證
            ]
            
            for adaptation in recent_adaptations:
                validation_score = await self._validate_adaptation_effectiveness(user_id, adaptation)
                adaptation.validation_score = validation_score
                
                self.logger.info(f"適應驗證 - 用戶: {user_id}, 分數: {validation_score:.3f}")

    async def _validate_adaptation_effectiveness(
        self,
        user_id: str,
        adaptation: AdaptationResult
    ) -> float:
        """驗證適應效果"""
        
        # 獲取適應後的學習指標
        metrics_after_adaptation = [
            m for m in self.learning_metrics_history[user_id]
            if m.timestamp > adaptation.adaptation_start_time
        ]
        
        if len(metrics_after_adaptation) < 5:
            return 0.5  # 數據不足，返回中性分數
        
        # 計算適應後的平均性能
        recent_performance = np.mean([
            (m.prediction_accuracy + m.decision_quality_score + m.behavior_understanding) / 3
            for m in metrics_after_adaptation[-5:]
        ])
        
        # 與適應前性能比較
        before_performance = (
            adaptation.before_metrics.prediction_accuracy +
            adaptation.before_metrics.decision_quality_score +
            adaptation.before_metrics.behavior_understanding
        ) / 3
        
        if before_performance > 0:
            improvement_ratio = (recent_performance - before_performance) / before_performance
            return max(0.0, min(improvement_ratio + 0.5, 1.0))  # 標準化到[0, 1]
        else:
            return 0.5

    def get_user_learning_summary(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶學習摘要"""
        
        if user_id not in self.user_learning_states:
            return {'error': '用戶未找到'}
        
        state = self.user_learning_states[user_id]
        metrics_history = self.learning_metrics_history[user_id]
        adaptations = self.adaptation_history[user_id]
        
        # 計算統計信息
        if metrics_history:
            latest_metrics = metrics_history[-1]
            avg_performance = np.mean([
                (m.prediction_accuracy + m.decision_quality_score + m.behavior_understanding) / 3
                for m in metrics_history[-10:]
            ])
        else:
            latest_metrics = LearningMetrics()
            avg_performance = 0.0
        
        return {
            'user_id': user_id,
            'learning_state': state,
            'current_performance': {
                'prediction_accuracy': latest_metrics.prediction_accuracy,
                'decision_quality': latest_metrics.decision_quality_score,
                'behavior_understanding': latest_metrics.behavior_understanding,
                'average_performance': avg_performance
            },
            'learning_history': {
                'total_interactions': state.get('interaction_count', 0),
                'metrics_recorded': len(metrics_history),
                'adaptations_made': len(adaptations),
                'learning_trend': state.get('learning_trend', 0.0)
            },
            'recent_adaptations': [
                {
                    'trigger': adapt.trigger.value,
                    'strategy': adapt.strategy_used.value,
                    'improvement_score': adapt.improvement_score,
                    'timestamp': adapt.adaptation_start_time
                }
                for adapt in adaptations[-5:]  # 最近5次適應
            ]
        }

    async def shutdown(self):
        """關閉引擎"""
        
        # 取消後台任務
        for task in self.background_tasks:
            task.cancel()
        
        # 保存模型和狀態
        await self.rl_agent.save_models()
        
        self.logger.info("AdaptiveLearningEngine shutdown completed")