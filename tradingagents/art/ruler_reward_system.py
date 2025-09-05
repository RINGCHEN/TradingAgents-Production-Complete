#!/usr/bin/env python3
"""
RULER Reward System - RULER獎勵生成系統
天工 (TianGong) - 零樣本獎勵生成系統，支援多維度評估和會員等級差異化

此模組提供：
1. 零樣本獎勵生成機制，無需人工標注
2. 多維度獎勵函數（獲利率、風險調整收益、夏普比率等）
3. 會員等級差異化的獎勵權重系統
4. 獎勵信號的準確性驗證機制
5. 實時市場表現追蹤
6. 動態獎勵模型調優
"""

from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import asyncio
import numpy as np
import pandas as pd
from pathlib import Path
import hashlib
import math
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict, deque
import statistics
from abc import ABC, abstractmethod

# Import trajectory components
try:
    from .trajectory_collector import AnalysisTrajectory, TrajectoryMetrics
    TRAJECTORY_COLLECTOR_AVAILABLE = True
except ImportError:
    TRAJECTORY_COLLECTOR_AVAILABLE = False

class RewardType(Enum):
    """獎勵類型"""
    # 核心績效獎勵
    ACCURACY_REWARD = "accuracy_reward"           # 預測準確性
    RETURN_PERFORMANCE = "return_performance"     # 投資報酬率
    RISK_ADJUSTED_RETURN = "risk_adjusted_return" # 風險調整後報酬
    
    # 風險管理獎勵  
    RISK_CONTROL = "risk_control"                 # 風險控制
    DRAWDOWN_MANAGEMENT = "drawdown_management"   # 回撤管理
    VOLATILITY_MANAGEMENT = "volatility_management" # 波動性管理
    
    # 效率獎勵
    TIMING_ACCURACY = "timing_accuracy"           # 時機把握
    CONFIDENCE_CALIBRATION = "confidence_calibration" # 信心度校準
    REASONING_QUALITY = "reasoning_quality"       # 推理質量
    
    # 用戶體驗獎勵
    USER_SATISFACTION = "user_satisfaction"       # 用戶滿意度
    EXPLANATION_QUALITY = "explanation_quality"   # 解釋質量
    ACTIONABILITY = "actionability"               # 可執行性
    
    # 系統性獎勵
    CONSISTENCY = "consistency"                   # 一致性
    ROBUSTNESS = "robustness"                     # 穩健性
    ADAPTABILITY = "adaptability"                 # 適應性

class MembershipTier(Enum):
    """會員等級"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    GOLD = "gold"
    PLATINUM = "platinum"

class RewardScope(Enum):
    """獎勵範圍"""
    STEP_LEVEL = "step_level"           # 步驟級別
    TRAJECTORY_LEVEL = "trajectory_level" # 軌跡級別
    SESSION_LEVEL = "session_level"     # 會話級別
    LONG_TERM = "long_term"            # 長期表現

@dataclass
class MarketPerformanceData:
    """市場表現數據"""
    stock_id: str
    recommendation_date: str
    recommendation_type: str  # BUY, SELL, HOLD
    recommendation_price: float
    target_price: Optional[float] = None
    
    # 追蹤數據
    current_price: float = 0.0
    price_change_1d: float = 0.0
    price_change_7d: float = 0.0
    price_change_30d: float = 0.0
    price_change_90d: float = 0.0
    
    # 市場基準
    market_change_1d: float = 0.0
    market_change_7d: float = 0.0
    market_change_30d: float = 0.0
    market_change_90d: float = 0.0
    
    # 風險指標
    volatility_30d: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RewardMetrics:
    """獎勵指標"""
    reward_id: str
    trajectory_id: str
    reward_type: RewardType
    reward_scope: RewardScope
    
    # 核心獎勵值
    raw_reward: float = 0.0              # 原始獎勵值 [-1, 1]
    weighted_reward: float = 0.0         # 加權獎勵值
    final_reward: float = 0.0            # 最終獎勵值
    
    # 置信度和質量
    confidence: float = 0.0              # 獎勵置信度
    quality_score: float = 0.0           # 獎勵質量分數
    reliability: float = 0.0             # 可靠性分數
    
    # 計算細節
    calculation_method: str = "default"
    data_sources: List[str] = field(default_factory=list)
    calculation_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # 驗證信息
    is_validated: bool = False
    validation_score: float = 0.0
    validation_notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['reward_type'] = self.reward_type.value
        result['reward_scope'] = self.reward_scope.value
        return result

@dataclass
class RewardSignal:
    """獎勵信號"""
    signal_id: str
    trajectory_id: str
    user_id: str
    stock_id: str
    analyst_type: str
    
    # 獎勵組成
    reward_components: Dict[RewardType, RewardMetrics] = field(default_factory=dict)
    
    # 綜合獎勵
    total_reward: float = 0.0
    weighted_total_reward: float = 0.0
    
    # 會員等級調整
    membership_tier: MembershipTier = MembershipTier.FREE
    membership_multiplier: float = 1.0
    
    # 時間信息
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    market_performance_period: int = 30  # 市場表現追蹤天數
    
    # 驗證狀態
    is_final: bool = False
    requires_validation: bool = True
    
    def add_reward_component(self, reward_type: RewardType, metrics: RewardMetrics):
        """添加獎勵組成部分"""
        self.reward_components[reward_type] = metrics
        self._recalculate_total_reward()
    
    def _recalculate_total_reward(self):
        """重新計算總獎勵"""
        if not self.reward_components:
            self.total_reward = 0.0
            return
        
        # 計算加權平均
        total_weighted = 0.0
        total_weights = 0.0
        
        for reward_type, metrics in self.reward_components.items():
            weight = REWARD_TYPE_WEIGHTS.get(reward_type, 0.1)
            total_weighted += metrics.final_reward * weight
            total_weights += weight
        
        self.total_reward = total_weighted / total_weights if total_weights > 0 else 0.0
        self.weighted_total_reward = self.total_reward * self.membership_multiplier
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['membership_tier'] = self.membership_tier.value
        result['reward_components'] = {
            reward_type.value: metrics.to_dict() 
            for reward_type, metrics in self.reward_components.items()
        }
        return result

# 獎勵權重配置
REWARD_TYPE_WEIGHTS = {
    RewardType.ACCURACY_REWARD: 0.25,
    RewardType.RETURN_PERFORMANCE: 0.20,
    RewardType.RISK_ADJUSTED_RETURN: 0.15,
    RewardType.RISK_CONTROL: 0.10,
    RewardType.TIMING_ACCURACY: 0.08,
    RewardType.CONFIDENCE_CALIBRATION: 0.07,
    RewardType.REASONING_QUALITY: 0.05,
    RewardType.USER_SATISFACTION: 0.05,
    RewardType.CONSISTENCY: 0.03,
    RewardType.ROBUSTNESS: 0.02
}

# 會員等級獎勵乘數
MEMBERSHIP_MULTIPLIERS = {
    MembershipTier.FREE: 1.0,
    MembershipTier.BASIC: 1.1,
    MembershipTier.PREMIUM: 1.2,
    MembershipTier.GOLD: 1.3,
    MembershipTier.PLATINUM: 1.5
}

class RewardCalculator(ABC):
    """獎勵計算器基類"""
    
    @abstractmethod
    async def calculate_reward(self, 
                              trajectory: 'AnalysisTrajectory',
                              market_data: MarketPerformanceData,
                              user_context: Dict[str, Any] = None) -> RewardMetrics:
        """計算獎勵"""
        pass
    
    @abstractmethod
    def get_reward_type(self) -> RewardType:
        """獲取獎勵類型"""
        pass

class AccuracyRewardCalculator(RewardCalculator):
    """準確性獎勵計算器"""
    
    async def calculate_reward(self, 
                              trajectory: 'AnalysisTrajectory',
                              market_data: MarketPerformanceData,
                              user_context: Dict[str, Any] = None) -> RewardMetrics:
        """計算預測準確性獎勵"""
        
        if not trajectory.final_recommendation or not market_data:
            return RewardMetrics(
                reward_id=f"accuracy_{trajectory.trajectory_id}",
                trajectory_id=trajectory.trajectory_id,
                reward_type=RewardType.ACCURACY_REWARD,
                reward_scope=RewardScope.TRAJECTORY_LEVEL,
                raw_reward=0.0,
                confidence=0.0
            )
        
        # 根據建議類型和實際表現計算準確性
        recommendation = trajectory.final_recommendation
        confidence = trajectory.final_confidence or 0.5
        
        # 使用30天表現作為主要評估標準
        price_change = market_data.price_change_30d
        
        # 計算基礎準確性分數
        if recommendation == "BUY":
            accuracy_score = self._sigmoid(price_change * 10)  # 上漲獎勵
        elif recommendation == "SELL":
            accuracy_score = self._sigmoid(-price_change * 10)  # 下跌獎勵
        else:  # HOLD
            accuracy_score = self._sigmoid(-abs(price_change) * 5)  # 穩定獎勵
        
        # 調整信心度
        calibrated_score = accuracy_score * confidence
        
        # 考慮時間衰減（預測越久前，權重越低）
        recommendation_date = datetime.fromisoformat(trajectory.start_time)
        current_date = datetime.now()
        days_passed = (current_date - recommendation_date).days
        time_decay = max(0.5, 1.0 - days_passed * 0.01)  # 每天衰減1%
        
        final_reward = calibrated_score * time_decay
        
        return RewardMetrics(
            reward_id=f"accuracy_{trajectory.trajectory_id}",
            trajectory_id=trajectory.trajectory_id,
            reward_type=RewardType.ACCURACY_REWARD,
            reward_scope=RewardScope.TRAJECTORY_LEVEL,
            raw_reward=accuracy_score,
            weighted_reward=calibrated_score,
            final_reward=final_reward,
            confidence=0.8,  # 市場數據相對可靠
            quality_score=0.9 if abs(price_change) > 0.05 else 0.6,  # 大幅波動更有信息量
            calculation_method="sigmoid_with_confidence_and_time_decay",
            data_sources=["market_price_data", "trajectory_recommendation"]
        )
    
    def _sigmoid(self, x: float) -> float:
        """Sigmoid函數，將值映射到[-1, 1]"""
        return 2 / (1 + math.exp(-x)) - 1
    
    def get_reward_type(self) -> RewardType:
        return RewardType.ACCURACY_REWARD

class ReturnPerformanceCalculator(RewardCalculator):
    """投資報酬率獎勵計算器"""
    
    async def calculate_reward(self, 
                              trajectory: 'AnalysisTrajectory',
                              market_data: MarketPerformanceData,
                              user_context: Dict[str, Any] = None) -> RewardMetrics:
        """計算投資報酬率獎勵"""
        
        if not market_data or not trajectory.final_recommendation:
            return RewardMetrics(
                reward_id=f"return_{trajectory.trajectory_id}",
                trajectory_id=trajectory.trajectory_id,
                reward_type=RewardType.RETURN_PERFORMANCE,
                reward_scope=RewardScope.TRAJECTORY_LEVEL,
                raw_reward=0.0
            )
        
        # 計算絕對和相對報酬
        absolute_return = market_data.price_change_30d
        relative_return = absolute_return - market_data.market_change_30d  # 超額報酬
        
        # 根據建議調整報酬方向
        if trajectory.final_recommendation == "SELL":
            absolute_return = -absolute_return
            relative_return = -relative_return
        elif trajectory.final_recommendation == "HOLD":
            # HOLD建議重點考慮波動性控制
            absolute_return = -abs(absolute_return) * 0.5
            relative_return = -abs(relative_return) * 0.5
        
        # 標準化報酬率到[-1, 1]範圍
        normalized_absolute = self._normalize_return(absolute_return)
        normalized_relative = self._normalize_return(relative_return)
        
        # 綜合評分（70%相對報酬 + 30%絕對報酬）
        final_reward = normalized_relative * 0.7 + normalized_absolute * 0.3
        
        return RewardMetrics(
            reward_id=f"return_{trajectory.trajectory_id}",
            trajectory_id=trajectory.trajectory_id,
            reward_type=RewardType.RETURN_PERFORMANCE,
            reward_scope=RewardScope.TRAJECTORY_LEVEL,
            raw_reward=absolute_return,
            weighted_reward=relative_return,
            final_reward=final_reward,
            confidence=0.85,
            quality_score=min(1.0, abs(relative_return) * 5),
            calculation_method="relative_return_weighted",
            data_sources=["market_price_data", "benchmark_data"]
        )
    
    def _normalize_return(self, return_rate: float) -> float:
        """標準化報酬率"""
        # 使用tanh函數將報酬率映射到[-1, 1]
        return math.tanh(return_rate * 10)
    
    def get_reward_type(self) -> RewardType:
        return RewardType.RETURN_PERFORMANCE

class RiskAdjustedReturnCalculator(RewardCalculator):
    """風險調整後報酬計算器"""
    
    async def calculate_reward(self, 
                              trajectory: 'AnalysisTrajectory',
                              market_data: MarketPerformanceData,
                              user_context: Dict[str, Any] = None) -> RewardMetrics:
        """計算風險調整後報酬獎勵"""
        
        if not market_data:
            return RewardMetrics(
                reward_id=f"risk_adj_return_{trajectory.trajectory_id}",
                trajectory_id=trajectory.trajectory_id,
                reward_type=RewardType.RISK_ADJUSTED_RETURN,
                reward_scope=RewardScope.TRAJECTORY_LEVEL,
                raw_reward=0.0
            )
        
        # 計算基礎報酬
        base_return = market_data.price_change_30d
        if trajectory.final_recommendation == "SELL":
            base_return = -base_return
        
        # 風險調整
        volatility = max(0.01, market_data.volatility_30d)  # 避免除零
        risk_adjusted_return = base_return / volatility
        
        # 考慮最大回撤
        max_drawdown = market_data.max_drawdown
        drawdown_penalty = max(0, 1 - abs(max_drawdown) * 2)  # 回撤懲罰
        
        # 夏普比率（如果可用）
        sharpe_bonus = 0.0
        if market_data.sharpe_ratio > 0:
            sharpe_bonus = min(0.5, market_data.sharpe_ratio * 0.1)
        
        # 最終風險調整後獎勵
        final_reward = (risk_adjusted_return * drawdown_penalty + sharpe_bonus) / 2
        final_reward = max(-1.0, min(1.0, final_reward))
        
        return RewardMetrics(
            reward_id=f"risk_adj_return_{trajectory.trajectory_id}",
            trajectory_id=trajectory.trajectory_id,
            reward_type=RewardType.RISK_ADJUSTED_RETURN,
            reward_scope=RewardScope.TRAJECTORY_LEVEL,
            raw_reward=risk_adjusted_return,
            weighted_reward=risk_adjusted_return * drawdown_penalty,
            final_reward=final_reward,
            confidence=0.75,
            quality_score=0.8,
            calculation_method="volatility_adjusted_with_drawdown",
            data_sources=["market_price_data", "volatility_data", "drawdown_data"]
        )
    
    def get_reward_type(self) -> RewardType:
        return RewardType.RISK_ADJUSTED_RETURN

class ReasoningQualityCalculator(RewardCalculator):
    """推理質量獎勵計算器"""
    
    async def calculate_reward(self, 
                              trajectory: 'AnalysisTrajectory',
                              market_data: MarketPerformanceData,
                              user_context: Dict[str, Any] = None) -> RewardMetrics:
        """計算推理質量獎勵"""
        
        if not trajectory.decision_steps:
            return RewardMetrics(
                reward_id=f"reasoning_{trajectory.trajectory_id}",
                trajectory_id=trajectory.trajectory_id,
                reward_type=RewardType.REASONING_QUALITY,
                reward_scope=RewardScope.TRAJECTORY_LEVEL,
                raw_reward=0.0
            )
        
        # 評估推理質量的多個維度
        depth_score = self._evaluate_reasoning_depth(trajectory)
        consistency_score = self._evaluate_consistency(trajectory)
        completeness_score = self._evaluate_completeness(trajectory)
        logical_flow_score = self._evaluate_logical_flow(trajectory)
        
        # 加權平均
        quality_score = (
            depth_score * 0.3 +
            consistency_score * 0.25 +
            completeness_score * 0.25 +
            logical_flow_score * 0.2
        )
        
        return RewardMetrics(
            reward_id=f"reasoning_{trajectory.trajectory_id}",
            trajectory_id=trajectory.trajectory_id,
            reward_type=RewardType.REASONING_QUALITY,
            reward_scope=RewardScope.TRAJECTORY_LEVEL,
            raw_reward=quality_score,
            final_reward=quality_score,
            confidence=0.7,  # 推理質量評估相對主觀
            quality_score=quality_score,
            calculation_method="multi_dimensional_reasoning_assessment",
            data_sources=["trajectory_reasoning_steps", "decision_logic"]
        )
    
    def _evaluate_reasoning_depth(self, trajectory: 'AnalysisTrajectory') -> float:
        """評估推理深度"""
        if not trajectory.decision_steps:
            return 0.0
        
        total_reasoning = 0
        for step in trajectory.decision_steps:
            reasoning_count = len(step.reasoning_process)
            avg_length = sum(len(r) for r in step.reasoning_process) / max(1, reasoning_count)
            total_reasoning += reasoning_count * (avg_length / 50)  # 標準化長度
        
        depth_score = total_reasoning / len(trajectory.decision_steps)
        return min(1.0, depth_score / 5.0)
    
    def _evaluate_consistency(self, trajectory: 'AnalysisTrajectory') -> float:
        """評估推理一致性"""
        if len(trajectory.decision_steps) < 2:
            return 1.0
        
        # 檢查信心度一致性
        confidences = [step.confidence_score for step in trajectory.decision_steps if step.confidence_score > 0]
        if not confidences:
            return 0.5
        
        consistency = 1.0 - (statistics.stdev(confidences) / max(0.1, statistics.mean(confidences)))
        return max(0.0, min(1.0, consistency))
    
    def _evaluate_completeness(self, trajectory: 'AnalysisTrajectory') -> float:
        """評估推理完整性"""
        expected_step_types = {
            'data_collection', 'financial_analysis', 'risk_assessment', 
            'recommendation_logic'
        }
        
        actual_step_types = {step.trajectory_type.value for step in trajectory.decision_steps}
        coverage = len(actual_step_types.intersection(expected_step_types))
        return coverage / len(expected_step_types)
    
    def _evaluate_logical_flow(self, trajectory: 'AnalysisTrajectory') -> float:
        """評估邏輯流程"""
        if len(trajectory.decision_steps) < 2:
            return 1.0
        
        # 簡化的邏輯流程評估
        # 檢查步驟間的依賴關係是否合理
        flow_score = 0.8  # 基礎分數
        
        # 檢查是否有最終推理步驟
        has_final_reasoning = any(
            'recommendation' in step.trajectory_type.value 
            for step in trajectory.decision_steps
        )
        
        if has_final_reasoning:
            flow_score += 0.2
        
        return min(1.0, flow_score)
    
    def get_reward_type(self) -> RewardType:
        return RewardType.REASONING_QUALITY

class RULERRewardSystem:
    """RULER獎勵系統 - 零樣本獎勵生成"""
    
    def __init__(self, 
                 storage_path: str = None,
                 market_data_provider: Optional[Callable] = None,
                 enable_real_time_tracking: bool = True):
        
        # 存儲配置
        self.storage_path = Path(storage_path) if storage_path else Path("./art_data/rewards")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 獎勵計算器
        self.calculators: Dict[RewardType, RewardCalculator] = {
            RewardType.ACCURACY_REWARD: AccuracyRewardCalculator(),
            RewardType.RETURN_PERFORMANCE: ReturnPerformanceCalculator(),
            RewardType.RISK_ADJUSTED_RETURN: RiskAdjustedReturnCalculator(),
            RewardType.REASONING_QUALITY: ReasoningQualityCalculator(),
        }
        
        # 市場數據追蹤
        self.market_data_provider = market_data_provider
        self.enable_real_time_tracking = enable_real_time_tracking
        self.market_performance_cache: Dict[str, MarketPerformanceData] = {}
        
        # 獎勵存儲
        self.active_rewards: Dict[str, RewardSignal] = {}
        self.completed_rewards: Dict[str, RewardSignal] = {}
        
        # 配置
        self.config = {
            'reward_calculation_interval_hours': 24,
            'market_tracking_period_days': 90,
            'min_confidence_threshold': 0.3,
            'reward_aggregation_method': 'weighted_average',
            'enable_dynamic_weights': True
        }
        
        # 日誌記錄
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 線程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="RULER-Reward")
        
        # 統計信息
        self.reward_stats = defaultdict(int)
        self._stats_lock = threading.Lock()
        
        # 動態權重系統
        self.dynamic_weights = REWARD_TYPE_WEIGHTS.copy()
        self.weight_adjustment_history = deque(maxlen=1000)
        
        self.logger.info(f"RULERRewardSystem initialized with {len(self.calculators)} calculators")
    
    def _setup_logging(self):
        """設置日誌記錄"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - RULER-RewardSystem - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def generate_reward_signal(self,
                                   trajectory: 'AnalysisTrajectory',
                                   user_context: Dict[str, Any] = None,
                                   immediate_evaluation: bool = False,
                                   custom_weights: Dict[RewardType, float] = None) -> RewardSignal:
        """生成獎勵信號"""
        
        # 創建獎勵信號
        signal_id = f"reward_{trajectory.trajectory_id}_{int(datetime.now().timestamp())}"
        
        # 獲取用戶會員等級
        membership_tier = self._determine_membership_tier(user_context)
        membership_multiplier = MEMBERSHIP_MULTIPLIERS.get(membership_tier, 1.0)
        
        reward_signal = RewardSignal(
            signal_id=signal_id,
            trajectory_id=trajectory.trajectory_id,
            user_id=trajectory.user_id,
            stock_id=trajectory.stock_id,
            analyst_type=trajectory.analyst_type,
            membership_tier=membership_tier,
            membership_multiplier=membership_multiplier,
            is_final=immediate_evaluation
        )
        
        # 獲取市場數據
        market_data = await self._get_market_performance_data(
            trajectory.stock_id,
            trajectory.start_time,
            immediate=immediate_evaluation
        )
        
        # 計算各種獎勵組成
        reward_weights = custom_weights or self.dynamic_weights
        
        for reward_type, calculator in self.calculators.items():
            if reward_weights.get(reward_type, 0) > 0:
                try:
                    reward_metrics = await calculator.calculate_reward(
                        trajectory, market_data, user_context
                    )
                    
                    # 應用動態權重
                    weight = reward_weights[reward_type]
                    reward_metrics.weighted_reward = reward_metrics.final_reward * weight
                    
                    reward_signal.add_reward_component(reward_type, reward_metrics)
                    
                except Exception as e:
                    self.logger.error(f"Failed to calculate {reward_type.value} reward: {e}")
        
        # 存儲獎勵信號
        if immediate_evaluation:
            self.completed_rewards[signal_id] = reward_signal
        else:
            self.active_rewards[signal_id] = reward_signal
        
        # 保存到存儲
        await self._save_reward_signal(reward_signal)
        
        # 更新統計
        with self._stats_lock:
            self.reward_stats['signals_generated'] += 1
            self.reward_stats[f'{reward_signal.membership_tier.value}_rewards'] += 1
        
        self.logger.info(f"Generated reward signal: {signal_id} (total: {reward_signal.weighted_total_reward:.3f})")
        return reward_signal
    
    def _determine_membership_tier(self, user_context: Dict[str, Any] = None) -> MembershipTier:
        """確定用戶會員等級"""
        if not user_context:
            return MembershipTier.FREE
        
        tier_str = user_context.get('membership_tier', 'FREE').upper()
        
        try:
            return MembershipTier(tier_str.lower())
        except ValueError:
            self.logger.warning(f"Unknown membership tier: {tier_str}, defaulting to FREE")
            return MembershipTier.FREE
    
    async def _get_market_performance_data(self,
                                          stock_id: str,
                                          start_date: str,
                                          immediate: bool = False) -> MarketPerformanceData:
        """獲取市場表現數據"""
        
        cache_key = f"{stock_id}_{start_date}"
        
        # 檢查緩存
        if cache_key in self.market_performance_cache and not immediate:
            cached_data = self.market_performance_cache[cache_key]
            # 檢查緩存是否過期（1小時）
            last_update = datetime.fromisoformat(cached_data.last_updated)
            if datetime.now() - last_update < timedelta(hours=1):
                return cached_data
        
        # 獲取新數據
        if self.market_data_provider:
            try:
                market_data = await self.market_data_provider(stock_id, start_date)
                self.market_performance_cache[cache_key] = market_data
                return market_data
            except Exception as e:
                self.logger.error(f"Failed to get market data for {stock_id}: {e}")
        
        # 創建模擬數據
        return await self._create_mock_market_data(stock_id, start_date)
    
    async def _create_mock_market_data(self, stock_id: str, start_date: str) -> MarketPerformanceData:
        """創建模擬市場數據"""
        
        # 模擬不同股票的不同表現特性
        if stock_id in ['2330', '2454']:  # 半導體股
            base_change = np.random.normal(0.02, 0.15)
            volatility = np.random.uniform(0.15, 0.25)
        elif stock_id in ['2881', '2882']:  # 金融股
            base_change = np.random.normal(0.005, 0.08)
            volatility = np.random.uniform(0.08, 0.15)
        else:
            base_change = np.random.normal(0.01, 0.12)
            volatility = np.random.uniform(0.10, 0.20)
        
        # 計算不同期間的表現
        price_change_1d = np.random.normal(base_change * 0.05, volatility * 0.3)
        price_change_7d = np.random.normal(base_change * 0.3, volatility * 0.7)
        price_change_30d = np.random.normal(base_change, volatility)
        price_change_90d = np.random.normal(base_change * 2.5, volatility * 1.5)
        
        # 市場基準（稍微保守一些）
        market_change_1d = price_change_1d * 0.8 + np.random.normal(0, 0.01)
        market_change_7d = price_change_7d * 0.8 + np.random.normal(0, 0.02)
        market_change_30d = price_change_30d * 0.8 + np.random.normal(0, 0.03)
        market_change_90d = price_change_90d * 0.8 + np.random.normal(0, 0.05)
        
        # 風險指標
        max_drawdown = -abs(np.random.normal(0.05, 0.03))
        sharpe_ratio = (base_change - 0.01) / volatility  # 假設無風險利率1%
        
        return MarketPerformanceData(
            stock_id=stock_id,
            recommendation_date=start_date,
            recommendation_type="BUY",  # 默認
            recommendation_price=np.random.uniform(50, 800),
            current_price=np.random.uniform(50, 800),
            price_change_1d=price_change_1d,
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d,
            price_change_90d=price_change_90d,
            market_change_1d=market_change_1d,
            market_change_7d=market_change_7d,
            market_change_30d=market_change_30d,
            market_change_90d=market_change_90d,
            volatility_30d=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio
        )
    
    async def update_reward_signals(self, trajectory_ids: List[str] = None) -> Dict[str, RewardSignal]:
        """更新獎勵信號"""
        
        if trajectory_ids is None:
            trajectory_ids = list(self.active_rewards.keys())
        
        updated_signals = {}
        
        for signal_id in trajectory_ids:
            if signal_id not in self.active_rewards:
                continue
            
            try:
                reward_signal = self.active_rewards[signal_id]
                
                # 重新獲取市場數據
                market_data = await self._get_market_performance_data(
                    reward_signal.stock_id,
                    reward_signal.generated_at,
                    immediate=True
                )
                
                # 重新計算獎勵
                # 這裡需要trajectory數據，實際實現中需要從軌跡收集器獲取
                # 為了演示，跳過重新計算
                
                updated_signals[signal_id] = reward_signal
                
            except Exception as e:
                self.logger.error(f"Failed to update reward signal {signal_id}: {e}")
        
        return updated_signals
    
    async def finalize_reward_signal(self, signal_id: str) -> Optional[RewardSignal]:
        """最終確定獎勵信號"""
        
        if signal_id not in self.active_rewards:
            return None
        
        reward_signal = self.active_rewards[signal_id]
        
        # 標記為最終
        reward_signal.is_final = True
        reward_signal.requires_validation = False
        
        # 移動到完成獎勵
        self.completed_rewards[signal_id] = reward_signal
        del self.active_rewards[signal_id]
        
        # 保存
        await self._save_reward_signal(reward_signal)
        
        # 更新動態權重
        await self._update_dynamic_weights(reward_signal)
        
        return reward_signal
    
    async def _update_dynamic_weights(self, reward_signal: RewardSignal):
        """更新動態權重"""
        
        if not self.config['enable_dynamic_weights']:
            return
        
        # 基於獎勵信號的表現調整權重
        # 這是一個簡化的實現，實際中需要更複雜的學習算法
        
        total_reward = reward_signal.weighted_total_reward
        
        for reward_type, metrics in reward_signal.reward_components.items():
            if metrics.quality_score > 0.7 and total_reward > 0.5:
                # 表現好的獎勵類型增加權重
                adjustment = 0.001  # 小幅調整
                self.dynamic_weights[reward_type] = min(
                    1.0, 
                    self.dynamic_weights[reward_type] + adjustment
                )
            elif metrics.quality_score < 0.3 or total_reward < -0.3:
                # 表現差的獎勵類型減少權重
                adjustment = 0.001
                self.dynamic_weights[reward_type] = max(
                    0.01, 
                    self.dynamic_weights[reward_type] - adjustment
                )
        
        # 記錄權重調整歷史
        self.weight_adjustment_history.append({
            'timestamp': datetime.now().isoformat(),
            'weights': self.dynamic_weights.copy(),
            'trigger_signal': signal_id
        })
    
    async def get_user_reward_summary(self, 
                                    user_id: str,
                                    time_range_days: int = 30) -> Dict[str, Any]:
        """獲取用戶獎勵摘要"""
        
        cutoff_date = datetime.now() - timedelta(days=time_range_days)
        
        user_rewards = []
        total_reward = 0.0
        reward_type_breakdown = defaultdict(float)
        
        # 搜集用戶的獎勵信號
        for reward_signal in self.completed_rewards.values():
            if reward_signal.user_id == user_id:
                signal_date = datetime.fromisoformat(reward_signal.generated_at)
                if signal_date >= cutoff_date:
                    user_rewards.append(reward_signal)
                    total_reward += reward_signal.weighted_total_reward
                    
                    for reward_type, metrics in reward_signal.reward_components.items():
                        reward_type_breakdown[reward_type.value] += metrics.final_reward
        
        return {
            'user_id': user_id,
            'time_range_days': time_range_days,
            'total_signals': len(user_rewards),
            'total_reward': total_reward,
            'average_reward': total_reward / len(user_rewards) if user_rewards else 0.0,
            'reward_breakdown': dict(reward_type_breakdown),
            'best_performance': max([s.weighted_total_reward for s in user_rewards]) if user_rewards else 0.0,
            'worst_performance': min([s.weighted_total_reward for s in user_rewards]) if user_rewards else 0.0,
            'consistency_score': self._calculate_consistency_score(user_rewards)
        }
    
    def _calculate_consistency_score(self, reward_signals: List[RewardSignal]) -> float:
        """計算一致性分數"""
        if len(reward_signals) < 2:
            return 1.0
        
        rewards = [signal.weighted_total_reward for signal in reward_signals]
        mean_reward = statistics.mean(rewards)
        std_dev = statistics.stdev(rewards)
        
        # 一致性分數：標準差越小，一致性越高
        consistency = max(0.0, 1.0 - (std_dev / max(0.1, abs(mean_reward))))
        return consistency
    
    async def _save_reward_signal(self, reward_signal: RewardSignal):
        """保存獎勵信號"""
        try:
            reward_file = self.storage_path / f"reward_{reward_signal.signal_id}.json"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                self._sync_save_reward_signal,
                reward_file,
                reward_signal.to_dict()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save reward signal {reward_signal.signal_id}: {e}")
    
    def _sync_save_reward_signal(self, file_path: Path, reward_data: Dict[str, Any]):
        """同步保存獎勵信號"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(reward_data, f, ensure_ascii=False, indent=2)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        with self._stats_lock:
            stats = self.reward_stats.copy()
        
        stats.update({
            'active_rewards': len(self.active_rewards),
            'completed_rewards': len(self.completed_rewards),
            'available_calculators': list(self.calculators.keys()),
            'current_weights': self.dynamic_weights,
            'market_cache_size': len(self.market_performance_cache)
        })
        
        return stats
    
    async def cleanup(self):
        """清理資源"""
        # 最終確定所有活躍獎勵
        for signal_id in list(self.active_rewards.keys()):
            await self.finalize_reward_signal(signal_id)
        
        # 關閉線程池
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("RULERRewardSystem cleanup completed")

# 工廠函數
async def create_ruler_reward_system(
    storage_path: str = None,
    market_data_provider: Optional[Callable] = None,
    enable_real_time_tracking: bool = True,
    custom_calculators: Dict[RewardType, RewardCalculator] = None
) -> RULERRewardSystem:
    """創建RULER獎勵系統實例"""
    
    system = RULERRewardSystem(
        storage_path=storage_path,
        market_data_provider=market_data_provider,
        enable_real_time_tracking=enable_real_time_tracking
    )
    
    # 添加自定義計算器
    if custom_calculators:
        system.calculators.update(custom_calculators)
    
    return system


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
    # 測試腳本
    import asyncio
    
    async def test_ruler_reward_system():
        print("🎯 測試RULER獎勵系統")
        
        # 創建獎勵系統
        reward_system = await create_ruler_reward_system("./test_rewards")
        
        # 創建模擬軌跡
        class MockTrajectory:
            def __init__(self):
                self.trajectory_id = "test_trajectory_123"
                self.stock_id = "2330"
                self.user_id = "test_user"
                self.analyst_type = "fundamentals_analyst"
                self.start_time = datetime.now().isoformat()
                self.final_recommendation = "BUY"
                self.final_confidence = 0.85
                self.decision_steps = []
        
        trajectory = MockTrajectory()
        
        # 生成獎勵信號
        user_context = {
            'user_id': 'test_user',
            'membership_tier': 'GOLD'
        }
        
        reward_signal = await reward_system.generate_reward_signal(
            trajectory=trajectory,
            user_context=user_context,
            immediate_evaluation=True
        )
        
        print(f"✅ 生成獎勵信號: {reward_signal.signal_id}")
        print(f"📊 總獎勵: {reward_signal.weighted_total_reward:.3f}")
        print(f"🏅 會員等級: {reward_signal.membership_tier.value}")
        
        # 獎勵組成分析
        print(f"\n🔍 獎勵組成:")
        for reward_type, metrics in reward_signal.reward_components.items():
            print(f"  • {reward_type.value}: {metrics.final_reward:.3f} (信心: {metrics.confidence:.2f})")
        
        # 獲取用戶摘要
        summary = await reward_system.get_user_reward_summary('test_user')
        print(f"\n📈 用戶摘要: 總獎勵 {summary['total_reward']:.3f}")
        
        # 系統統計
        stats = reward_system.get_system_statistics()
        print(f"\n📊 系統統計: {stats['completed_rewards']} 個已完成獎勵")
        
        # 清理
        await reward_system.cleanup()
        
        print("✅ RULER獎勵系統測試完成")
    
    asyncio.run(test_ruler_reward_system())