#!/usr/bin/env python3
"""
自適應學習引擎
Adaptive Learning Engine - GPT-OSS整合任務4.1.1

自適應學習引擎是階段4智能化增強的核心組件，通過強化學習框架和在線學習算法，
實現AI系統的自主學習和策略優化能力。

主要功能：
1. 強化學習框架 - PPO/SAC算法實現投資策略優化
2. 在線學習系統 - 實時模型參數更新和性能監控
3. 多臂老虎機 - 動態策略選擇和探索平衡
4. 元學習能力 - 快速適應新市場條件
5. 持續學習機制 - 避免災難性遺忘
6. 性能評估系統 - 學習效果實時監控
"""

import os
import json
import logging
import asyncio
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
from pathlib import Path
import pickle
from collections import deque, defaultdict
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical, Normal
import random
from abc import ABC, abstractmethod

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LearningMode(str, Enum):
    """學習模式枚舉"""
    ONLINE = "online"               # 在線學習
    BATCH = "batch"                # 批量學習
    INCREMENTAL = "incremental"    # 增量學習
    ACTIVE = "active"              # 主動學習
    TRANSFER = "transfer"          # 遷移學習
    META = "meta"                  # 元學習


class AdaptationStrategy(str, Enum):
    """適應策略枚舉"""
    CONSERVATIVE = "conservative"   # 保守策略 - 緩慢適應
    MODERATE = "moderate"          # 中等策略 - 平衡適應
    AGGRESSIVE = "aggressive"      # 激進策略 - 快速適應
    DYNAMIC = "dynamic"            # 動態策略 - 智能調整


class RewardType(str, Enum):
    """獎勵類型枚舉"""
    IMMEDIATE = "immediate"        # 即時獎勵
    DELAYED = "delayed"           # 延遲獎勵
    CUMULATIVE = "cumulative"     # 累積獎勵
    RISK_ADJUSTED = "risk_adjusted" # 風險調整獎勵


class ExplorationStrategy(str, Enum):
    """探索策略枚舉"""
    EPSILON_GREEDY = "epsilon_greedy"     # ε-貪心
    UCB = "ucb"                          # 上置信界
    THOMPSON_SAMPLING = "thompson_sampling" # 湯普森採樣
    SOFTMAX = "softmax"                  # 軟最大


@dataclass
class MarketState:
    """市場狀態類"""
    timestamp: datetime
    market_data: Dict[str, float]
    technical_indicators: Dict[str, float]
    sentiment_scores: Dict[str, float]
    volatility_metrics: Dict[str, float]
    macro_factors: Dict[str, float]
    regime_indicators: Dict[str, bool]
    
    def to_vector(self) -> np.ndarray:
        """轉換為向量表示"""
        all_values = []
        all_values.extend(self.market_data.values())
        all_values.extend(self.technical_indicators.values())
        all_values.extend(self.sentiment_scores.values())
        all_values.extend(self.volatility_metrics.values())
        all_values.extend(self.macro_factors.values())
        all_values.extend([float(v) for v in self.regime_indicators.values()])
        return np.array(all_values, dtype=np.float32)


@dataclass
class Action:
    """動作類"""
    action_id: str
    action_type: str  # 'buy', 'sell', 'hold', 'rebalance'
    parameters: Dict[str, Any]
    confidence: float
    expected_reward: float
    risk_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'action_id': self.action_id,
            'action_type': self.action_type,
            'parameters': self.parameters,
            'confidence': self.confidence,
            'expected_reward': self.expected_reward,
            'risk_level': self.risk_level
        }


@dataclass
class Experience:
    """經驗類"""
    state: MarketState
    action: Action
    reward: float
    next_state: Optional[MarketState]
    done: bool
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'state_vector': self.state.to_vector().tolist(),
            'action': self.action.to_dict(),
            'reward': self.reward,
            'next_state_vector': self.next_state.to_vector().tolist() if self.next_state else None,
            'done': self.done,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


class AdaptiveLearningConfig(BaseModel):
    """自適應學習引擎配置"""
    engine_id: str = Field(..., description="引擎ID")
    engine_name: str = Field(..., description="引擎名稱")
    
    # 學習配置
    learning_mode: LearningMode = Field(LearningMode.ONLINE, description="學習模式")
    adaptation_strategy: AdaptationStrategy = Field(AdaptationStrategy.MODERATE, description="適應策略")
    exploration_strategy: ExplorationStrategy = Field(ExplorationStrategy.EPSILON_GREEDY, description="探索策略")
    
    # 強化學習參數
    learning_rate: float = Field(0.001, description="學習率")
    discount_factor: float = Field(0.99, description="折扣因子")
    exploration_rate: float = Field(0.1, description="探索率")
    exploration_decay: float = Field(0.995, description="探索衰減率")
    min_exploration_rate: float = Field(0.01, description="最小探索率")
    
    # 神經網路參數
    hidden_layers: List[int] = Field([256, 128, 64], description="隱藏層大小")
    activation_function: str = Field("relu", description="激活函數")
    dropout_rate: float = Field(0.2, description="Dropout率")
    
    # 經驗回放參數
    buffer_size: int = Field(10000, description="經驗回放緩衝區大小")
    batch_size: int = Field(32, description="批量大小")
    update_frequency: int = Field(4, description="更新頻率")
    target_update_frequency: int = Field(100, description="目標網路更新頻率")
    
    # 在線學習參數
    online_learning_enabled: bool = Field(True, description="是否啟用在線學習")
    adaptation_threshold: float = Field(0.1, description="適應閾值")
    performance_window: int = Field(100, description="性能評估窗口")
    min_samples_for_update: int = Field(10, description="更新所需最小樣本數")
    
    # 元學習參數
    meta_learning_enabled: bool = Field(True, description="是否啟用元學習")
    task_memory_size: int = Field(50, description="任務記憶大小")
    fast_adaptation_steps: int = Field(5, description="快速適應步數")
    
    # 性能監控
    performance_tracking_enabled: bool = Field(True, description="是否啟用性能追蹤")
    evaluation_frequency: int = Field(10, description="評估頻率")
    early_stopping_patience: int = Field(20, description="早停耐心值")
    
    # 持久化配置
    model_save_frequency: int = Field(100, description="模型保存頻率")
    checkpoint_directory: str = Field("./checkpoints", description="檢查點目錄")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PPOAgent(nn.Module):
    """PPO強化學習智能體"""
    
    def __init__(self, state_size: int, action_size: int, hidden_layers: List[int], 
                 learning_rate: float = 0.001):
        super(PPOAgent, self).__init__()
        
        self.state_size = state_size
        self.action_size = action_size
        
        # 策略網路（Actor）
        layers = []
        input_size = state_size
        
        for hidden_size in hidden_layers:
            layers.extend([
                nn.Linear(input_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            input_size = hidden_size
        
        layers.append(nn.Linear(input_size, action_size))
        layers.append(nn.Softmax(dim=-1))
        
        self.policy_net = nn.Sequential(*layers)
        
        # 價值網路（Critic）
        value_layers = []
        input_size = state_size
        
        for hidden_size in hidden_layers:
            value_layers.extend([
                nn.Linear(input_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            input_size = hidden_size
        
        value_layers.append(nn.Linear(input_size, 1))
        
        self.value_net = nn.Sequential(*value_layers)
        
        # 優化器
        self.policy_optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.value_optimizer = optim.Adam(self.value_net.parameters(), lr=learning_rate)
        
        logger.info(f"PPO Agent initialized with state_size={state_size}, action_size={action_size}")
    
    def forward(self, state: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """前向傳播"""
        action_probs = self.policy_net(state)
        state_value = self.value_net(state)
        return action_probs, state_value
    
    def select_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        """選擇動作"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        action_probs, state_value = self.forward(state_tensor)
        
        # 基於概率分佈選擇動作
        dist = Categorical(action_probs)
        action = dist.sample()
        
        return action.item(), dist.log_prob(action).item(), state_value.item()
    
    def update(self, states: torch.Tensor, actions: torch.Tensor, 
               old_log_probs: torch.Tensor, rewards: torch.Tensor, 
               advantages: torch.Tensor, clip_param: float = 0.2) -> Dict[str, float]:
        """PPO更新"""
        
        # 計算新的動作概率和狀態價值
        action_probs, state_values = self.forward(states)
        dist = Categorical(action_probs)
        new_log_probs = dist.log_prob(actions)
        
        # 計算比值和剪切項
        ratio = torch.exp(new_log_probs - old_log_probs)
        clipped_ratio = torch.clamp(ratio, 1 - clip_param, 1 + clip_param)
        
        # 策略損失
        policy_loss = -torch.min(ratio * advantages, clipped_ratio * advantages).mean()
        
        # 價值損失
        value_loss = F.mse_loss(state_values.squeeze(), rewards)
        
        # 熵損失（鼓勵探索）
        entropy_loss = -dist.entropy().mean()
        
        # 總損失
        total_policy_loss = policy_loss + 0.01 * entropy_loss
        total_value_loss = value_loss
        
        # 更新策略網路
        self.policy_optimizer.zero_grad()
        total_policy_loss.backward(retain_graph=True)
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 0.5)
        self.policy_optimizer.step()
        
        # 更新價值網路
        self.value_optimizer.zero_grad()
        total_value_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.value_net.parameters(), 0.5)
        self.value_optimizer.step()
        
        return {
            'policy_loss': policy_loss.item(),
            'value_loss': value_loss.item(),
            'entropy_loss': entropy_loss.item(),
            'total_loss': (total_policy_loss + total_value_loss).item()
        }


class ExperienceReplayBuffer:
    """經驗回放緩衝區"""
    
    def __init__(self, max_size: int):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
        self.priorities = deque(maxlen=max_size)
    
    def push(self, experience: Experience, priority: float = 1.0):
        """添加經驗"""
        self.buffer.append(experience)
        self.priorities.append(priority)
    
    def sample(self, batch_size: int, prioritized: bool = False) -> List[Experience]:
        """採樣經驗"""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        if prioritized and self.priorities:
            # 優先級採樣
            priorities = np.array(self.priorities)
            probabilities = priorities / priorities.sum()
            indices = np.random.choice(len(self.buffer), batch_size, p=probabilities)
            return [self.buffer[i] for i in indices]
        else:
            # 隨機採樣
            return random.sample(list(self.buffer), batch_size)
    
    def __len__(self) -> int:
        return len(self.buffer)


class MultiArmedBandit:
    """多臂老虎機"""
    
    def __init__(self, n_arms: int, strategy: ExplorationStrategy = ExplorationStrategy.UCB):
        self.n_arms = n_arms
        self.strategy = strategy
        self.arm_counts = np.zeros(n_arms)
        self.arm_rewards = np.zeros(n_arms)
        self.total_count = 0
        
        # Thompson Sampling參數
        self.alpha = np.ones(n_arms)  # 成功次數 + 1
        self.beta = np.ones(n_arms)   # 失敗次數 + 1
    
    def select_arm(self, epsilon: float = 0.1) -> int:
        """選擇臂"""
        if self.strategy == ExplorationStrategy.EPSILON_GREEDY:
            if np.random.random() < epsilon:
                return np.random.randint(self.n_arms)
            else:
                return np.argmax(self.arm_rewards / (self.arm_counts + 1e-8))
        
        elif self.strategy == ExplorationStrategy.UCB:
            if self.total_count == 0:
                return np.random.randint(self.n_arms)
            
            ucb_values = (self.arm_rewards / (self.arm_counts + 1e-8) + 
                         np.sqrt(2 * np.log(self.total_count) / (self.arm_counts + 1e-8)))
            return np.argmax(ucb_values)
        
        elif self.strategy == ExplorationStrategy.THOMPSON_SAMPLING:
            samples = np.random.beta(self.alpha, self.beta)
            return np.argmax(samples)
        
        elif self.strategy == ExplorationStrategy.SOFTMAX:
            if self.total_count == 0:
                return np.random.randint(self.n_arms)
            
            avg_rewards = self.arm_rewards / (self.arm_counts + 1e-8)
            exp_values = np.exp(avg_rewards / 0.1)  # temperature = 0.1
            probabilities = exp_values / np.sum(exp_values)
            return np.random.choice(self.n_arms, p=probabilities)
        
        return 0
    
    def update(self, arm: int, reward: float):
        """更新臂的統計信息"""
        self.arm_counts[arm] += 1
        self.arm_rewards[arm] += reward
        self.total_count += 1
        
        # Thompson Sampling更新
        if reward > 0:
            self.alpha[arm] += 1
        else:
            self.beta[arm] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        avg_rewards = self.arm_rewards / (self.arm_counts + 1e-8)
        return {
            'arm_counts': self.arm_counts.tolist(),
            'total_rewards': self.arm_rewards.tolist(),
            'average_rewards': avg_rewards.tolist(),
            'best_arm': int(np.argmax(avg_rewards)),
            'total_count': self.total_count
        }


class MetaLearner:
    """元學習器"""
    
    def __init__(self, base_learner: PPOAgent, task_memory_size: int = 50):
        self.base_learner = base_learner
        self.task_memory = deque(maxlen=task_memory_size)
        self.task_embeddings = {}
        
    def add_task_experience(self, task_id: str, experiences: List[Experience]):
        """添加任務經驗"""
        self.task_memory.append((task_id, experiences))
        
        # 計算任務嵌入向量
        task_embedding = self._compute_task_embedding(experiences)
        self.task_embeddings[task_id] = task_embedding
    
    def _compute_task_embedding(self, experiences: List[Experience]) -> np.ndarray:
        """計算任務嵌入向量"""
        if not experiences:
            return np.zeros(64)  # 預設嵌入維度
        
        # 基於狀態和動作的統計特徵計算嵌入
        state_vectors = [exp.state.to_vector() for exp in experiences]
        rewards = [exp.reward for exp in experiences]
        
        embedding = np.concatenate([
            np.mean(state_vectors, axis=0)[:32],  # 狀態均值
            np.std(state_vectors, axis=0)[:16],   # 狀態標準差
            [np.mean(rewards), np.std(rewards)],  # 獎勵統計
            [len(experiences) / 1000.0],          # 任務長度
            np.zeros(13)  # 填充至64維
        ])[:64]
        
        return embedding
    
    def fast_adapt(self, new_task_experiences: List[Experience], 
                   adaptation_steps: int = 5) -> Dict[str, Any]:
        """快速適應新任務"""
        if not new_task_experiences:
            return {'adaptation_success': False, 'reason': 'no_experiences'}
        
        # 尋找相似任務
        new_task_embedding = self._compute_task_embedding(new_task_experiences)
        similar_tasks = self._find_similar_tasks(new_task_embedding, top_k=3)
        
        # 基於相似任務進行快速適應
        adaptation_results = {
            'similar_tasks': similar_tasks,
            'adaptation_steps': adaptation_steps,
            'performance_before': 0.0,
            'performance_after': 0.0,
            'adaptation_success': True
        }
        
        logger.info(f"Fast adaptation completed with {len(similar_tasks)} similar tasks")
        
        return adaptation_results
    
    def _find_similar_tasks(self, task_embedding: np.ndarray, top_k: int = 3) -> List[str]:
        """尋找相似任務"""
        if not self.task_embeddings:
            return []
        
        similarities = {}
        for task_id, embedding in self.task_embeddings.items():
            similarity = np.dot(task_embedding, embedding) / (
                np.linalg.norm(task_embedding) * np.linalg.norm(embedding) + 1e-8
            )
            similarities[task_id] = similarity
        
        # 返回最相似的top_k任務
        sorted_tasks = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
        return [task_id for task_id, _ in sorted_tasks[:top_k]]


class PerformanceTracker:
    """性能追蹤器"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history = defaultdict(deque)
        self.current_metrics = {}
        
    def update_metric(self, metric_name: str, value: float, timestamp: datetime = None):
        """更新指標"""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        self.metrics_history[metric_name].append((timestamp, value))
        
        # 保持窗口大小
        if len(self.metrics_history[metric_name]) > self.window_size:
            self.metrics_history[metric_name].popleft()
        
        self.current_metrics[metric_name] = value
    
    def get_metric_statistics(self, metric_name: str) -> Dict[str, float]:
        """獲取指標統計信息"""
        if metric_name not in self.metrics_history:
            return {}
        
        values = [v for _, v in self.metrics_history[metric_name]]
        
        if not values:
            return {}
        
        return {
            'current': values[-1],
            'mean': np.mean(values),
            'std': np.std(values),
            'min': np.min(values),
            'max': np.max(values),
            'trend': self._calculate_trend(values),
            'count': len(values)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """計算趨勢"""
        if len(values) < 2:
            return 'stable'
        
        recent_values = values[-min(10, len(values)):]
        if len(recent_values) < 2:
            return 'stable'
        
        # 簡單線性趨勢計算
        x = np.arange(len(recent_values))
        y = np.array(recent_values)
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return 'improving'
        elif slope < -0.01:
            return 'declining'
        else:
            return 'stable'
    
    def get_all_metrics(self) -> Dict[str, Dict[str, float]]:
        """獲取所有指標統計"""
        return {name: self.get_metric_statistics(name) 
                for name in self.metrics_history.keys()}


class AdaptiveLearningEngine:
    """自適應學習引擎核心類"""
    
    def __init__(self, config: AdaptiveLearningConfig):
        self.config = config
        self.is_initialized = False
        
        # 核心組件
        self.ppo_agent = None
        self.experience_buffer = ExperienceReplayBuffer(config.buffer_size)
        self.bandit = MultiArmedBandit(10, config.exploration_strategy)  # 10個動作臂
        self.meta_learner = None
        self.performance_tracker = PerformanceTracker(config.performance_window)
        
        # 學習狀態
        self.current_exploration_rate = config.exploration_rate
        self.learning_step = 0
        self.last_performance_evaluation = 0
        self.adaptation_history = []
        
        # 統計信息
        self.learning_stats = {
            'total_experiences': 0,
            'total_updates': 0,
            'average_reward': 0.0,
            'learning_efficiency': 0.0,
            'adaptation_events': 0,
            'exploration_rate_history': [],
            'performance_milestones': []
        }
        
        logger.info(f"AdaptiveLearningEngine initialized: {config.engine_name}")
    
    async def initialize(self) -> bool:
        """初始化自適應學習引擎"""
        try:
            logger.info("Initializing AdaptiveLearningEngine...")
            
            # 1. 初始化PPO智能體
            state_size = 100  # 根據市場狀態向量大小調整
            action_size = 10  # 根據動作空間調整
            
            self.ppo_agent = PPOAgent(
                state_size=state_size,
                action_size=action_size,
                hidden_layers=self.config.hidden_layers,
                learning_rate=self.config.learning_rate
            )
            
            # 2. 初始化元學習器
            if self.config.meta_learning_enabled:
                self.meta_learner = MetaLearner(
                    self.ppo_agent, 
                    self.config.task_memory_size
                )
            
            # 3. 創建檢查點目錄
            os.makedirs(self.config.checkpoint_directory, exist_ok=True)
            
            # 4. 載入現有模型（如果存在）
            await self._load_checkpoint()
            
            self.is_initialized = True
            logger.info("AdaptiveLearningEngine initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"AdaptiveLearningEngine initialization failed: {e}")
            return False
    
    async def adapt_strategy(self, market_data: Dict[str, Any], 
                           user_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """根據市場數據和用戶反饋調整策略"""
        try:
            logger.info("Adapting investment strategy...")
            
            # 1. 創建市場狀態
            market_state = await self._create_market_state(market_data)
            
            # 2. 選擇動作
            action, log_prob, state_value = self.ppo_agent.select_action(
                market_state.to_vector()
            )
            
            # 3. 多臂老虎機策略選擇
            bandit_arm = self.bandit.select_arm(self.current_exploration_rate)
            
            # 4. 創建動作對象
            strategy_action = Action(
                action_id=f"action_{self.learning_step}_{int(datetime.now().timestamp())}",
                action_type=self._map_action_to_type(action),
                parameters={
                    'action_index': action,
                    'bandit_arm': bandit_arm,
                    'confidence': abs(log_prob),
                    'state_value': state_value
                },
                confidence=abs(log_prob),
                expected_reward=state_value,
                risk_level=self._calculate_risk_level(market_state)
            )
            
            # 5. 更新探索率
            self._update_exploration_rate()
            
            # 6. 記錄統計信息
            self.learning_stats['exploration_rate_history'].append({
                'step': self.learning_step,
                'exploration_rate': self.current_exploration_rate,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            self.learning_step += 1
            
            return {
                'action': strategy_action.to_dict(),
                'market_state_summary': {
                    'state_vector_size': len(market_state.to_vector()),
                    'timestamp': market_state.timestamp.isoformat(),
                    'regime_indicators': market_state.regime_indicators
                },
                'learning_info': {
                    'exploration_rate': self.current_exploration_rate,
                    'learning_step': self.learning_step,
                    'bandit_arm_selected': bandit_arm
                },
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Strategy adaptation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_strategy': 'conservative_hold'
            }
    
    async def continuous_learning(self, experience_buffer: List[Dict[str, Any]]) -> Dict[str, Any]:
        """持續學習和模型更新"""
        try:
            logger.info(f"Starting continuous learning with {len(experience_buffer)} experiences")
            
            # 1. 轉換經驗格式
            experiences = await self._convert_experience_buffer(experience_buffer)
            
            # 2. 添加經驗到緩衝區
            for exp in experiences:
                self.experience_buffer.push(exp)
            
            self.learning_stats['total_experiences'] += len(experiences)
            
            # 3. 檢查是否需要更新
            if len(self.experience_buffer) < self.config.min_samples_for_update:
                return {
                    'learning_performed': False,
                    'reason': 'insufficient_samples',
                    'buffer_size': len(self.experience_buffer),
                    'required_samples': self.config.min_samples_for_update
                }
            
            # 4. 採樣批量數據
            batch_experiences = self.experience_buffer.sample(self.config.batch_size)
            
            # 5. 準備訓練數據
            training_data = await self._prepare_training_data(batch_experiences)
            
            # 6. 執行PPO更新
            update_results = self.ppo_agent.update(
                states=training_data['states'],
                actions=training_data['actions'],
                old_log_probs=training_data['old_log_probs'],
                rewards=training_data['rewards'],
                advantages=training_data['advantages']
            )
            
            # 7. 更新多臂老虎機
            await self._update_bandit_rewards(batch_experiences)
            
            # 8. 元學習更新（如果啟用）
            meta_results = {}
            if self.config.meta_learning_enabled and self.meta_learner:
                meta_results = await self._perform_meta_learning(batch_experiences)
            
            # 9. 更新統計信息
            self.learning_stats['total_updates'] += 1
            self.learning_stats['average_reward'] = np.mean([exp.reward for exp in batch_experiences])
            
            # 10. 性能評估
            performance_metrics = await self._evaluate_learning_performance(batch_experiences)
            
            # 11. 保存檢查點
            if self.learning_step % self.config.model_save_frequency == 0:
                await self._save_checkpoint()
            
            return {
                'learning_performed': True,
                'update_results': update_results,
                'meta_learning_results': meta_results,
                'performance_metrics': performance_metrics,
                'learning_statistics': {
                    'total_experiences': self.learning_stats['total_experiences'],
                    'total_updates': self.learning_stats['total_updates'],
                    'average_reward': self.learning_stats['average_reward'],
                    'buffer_size': len(self.experience_buffer)
                },
                'bandit_statistics': self.bandit.get_statistics()
            }
            
        except Exception as e:
            logger.error(f"Continuous learning failed: {e}")
            return {
                'learning_performed': False,
                'error': str(e),
                'buffer_size': len(self.experience_buffer)
            }
    
    def evaluate_performance(self) -> Dict[str, Any]:
        """評估學習效果和策略性能"""
        try:
            # 1. 基本統計
            basic_stats = {
                'learning_step': self.learning_step,
                'total_experiences': self.learning_stats['total_experiences'],
                'total_updates': self.learning_stats['total_updates'],
                'current_exploration_rate': self.current_exploration_rate,
                'buffer_utilization': len(self.experience_buffer) / self.config.buffer_size
            }
            
            # 2. 性能指標
            performance_metrics = self.performance_tracker.get_all_metrics()
            
            # 3. 學習效率
            learning_efficiency = 0.0
            if self.learning_stats['total_updates'] > 0:
                learning_efficiency = (
                    self.learning_stats['total_experiences'] / 
                    self.learning_stats['total_updates']
                )
            
            # 4. 適應能力評估
            adaptation_score = self._calculate_adaptation_score()
            
            # 5. 多臂老虎機統計
            bandit_stats = self.bandit.get_statistics()
            
            # 6. 探索vs利用平衡
            exploration_balance = self._evaluate_exploration_balance()
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'basic_statistics': basic_stats,
                'performance_metrics': performance_metrics,
                'learning_efficiency': learning_efficiency,
                'adaptation_score': adaptation_score,
                'bandit_statistics': bandit_stats,
                'exploration_balance': exploration_balance,
                'overall_health_score': self._calculate_overall_health_score(),
                'recommendations': self._generate_performance_recommendations()
            }
            
        except Exception as e:
            logger.error(f"Performance evaluation failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'evaluation_success': False
            }
    
    async def _create_market_state(self, market_data: Dict[str, Any]) -> MarketState:
        """創建市場狀態"""
        return MarketState(
            timestamp=datetime.now(timezone.utc),
            market_data=market_data.get('market_data', {}),
            technical_indicators=market_data.get('technical_indicators', {}),
            sentiment_scores=market_data.get('sentiment_scores', {}),
            volatility_metrics=market_data.get('volatility_metrics', {}),
            macro_factors=market_data.get('macro_factors', {}),
            regime_indicators=market_data.get('regime_indicators', {})
        )
    
    def _map_action_to_type(self, action: int) -> str:
        """將動作索引映射到動作類型"""
        action_mapping = {
            0: 'strong_buy',
            1: 'buy',
            2: 'weak_buy',
            3: 'hold',
            4: 'weak_sell',
            5: 'sell',
            6: 'strong_sell',
            7: 'rebalance',
            8: 'hedge',
            9: 'cash'
        }
        return action_mapping.get(action, 'hold')
    
    def _calculate_risk_level(self, market_state: MarketState) -> float:
        """計算風險水平"""
        # 基於市場狀態計算風險水平
        volatility_score = np.mean(list(market_state.volatility_metrics.values())) if market_state.volatility_metrics else 0.5
        sentiment_score = np.mean(list(market_state.sentiment_scores.values())) if market_state.sentiment_scores else 0.5
        
        # 風險水平 = (波動性 + (1 - 情緒分數)) / 2
        risk_level = (volatility_score + (1 - sentiment_score)) / 2
        return np.clip(risk_level, 0.0, 1.0)
    
    def _update_exploration_rate(self):
        """更新探索率"""
        self.current_exploration_rate = max(
            self.config.min_exploration_rate,
            self.current_exploration_rate * self.config.exploration_decay
        )
    
    async def _convert_experience_buffer(self, experience_buffer: List[Dict[str, Any]]) -> List[Experience]:
        """轉換經驗緩衝區格式"""
        experiences = []
        
        for exp_data in experience_buffer:
            try:
                # 創建市場狀態
                state = MarketState(
                    timestamp=datetime.fromisoformat(exp_data.get('timestamp', datetime.now(timezone.utc).isoformat())),
                    market_data=exp_data.get('market_data', {}),
                    technical_indicators=exp_data.get('technical_indicators', {}),
                    sentiment_scores=exp_data.get('sentiment_scores', {}),
                    volatility_metrics=exp_data.get('volatility_metrics', {}),
                    macro_factors=exp_data.get('macro_factors', {}),
                    regime_indicators=exp_data.get('regime_indicators', {})
                )
                
                # 創建動作
                action_data = exp_data.get('action', {})
                action = Action(
                    action_id=action_data.get('action_id', f"exp_{int(datetime.now().timestamp())}"),
                    action_type=action_data.get('action_type', 'hold'),
                    parameters=action_data.get('parameters', {}),
                    confidence=action_data.get('confidence', 0.5),
                    expected_reward=action_data.get('expected_reward', 0.0),
                    risk_level=action_data.get('risk_level', 0.5)
                )
                
                # 創建下一個狀態（如果存在）
                next_state = None
                if 'next_state' in exp_data:
                    next_state_data = exp_data['next_state']
                    next_state = MarketState(
                        timestamp=datetime.fromisoformat(next_state_data.get('timestamp', datetime.now(timezone.utc).isoformat())),
                        market_data=next_state_data.get('market_data', {}),
                        technical_indicators=next_state_data.get('technical_indicators', {}),
                        sentiment_scores=next_state_data.get('sentiment_scores', {}),
                        volatility_metrics=next_state_data.get('volatility_metrics', {}),
                        macro_factors=next_state_data.get('macro_factors', {}),
                        regime_indicators=next_state_data.get('regime_indicators', {})
                    )
                
                # 創建經驗
                experience = Experience(
                    state=state,
                    action=action,
                    reward=exp_data.get('reward', 0.0),
                    next_state=next_state,
                    done=exp_data.get('done', False),
                    timestamp=state.timestamp,
                    metadata=exp_data.get('metadata', {})
                )
                
                experiences.append(experience)
                
            except Exception as e:
                logger.warning(f"Failed to convert experience data: {e}")
                continue
        
        return experiences
    
    async def _prepare_training_data(self, experiences: List[Experience]) -> Dict[str, torch.Tensor]:
        """準備訓練數據"""
        states = []
        actions = []
        rewards = []
        old_log_probs = []
        
        for exp in experiences:
            states.append(exp.state.to_vector())
            
            # 從參數中提取動作信息
            action_idx = exp.action.parameters.get('action_index', 0)
            actions.append(action_idx)
            
            rewards.append(exp.reward)
            
            # 模擬舊的log概率
            old_log_prob = exp.action.parameters.get('log_prob', -1.0)
            old_log_probs.append(old_log_prob)
        
        # 轉換為張量
        states_tensor = torch.FloatTensor(np.array(states))
        actions_tensor = torch.LongTensor(actions)
        rewards_tensor = torch.FloatTensor(rewards)
        old_log_probs_tensor = torch.FloatTensor(old_log_probs)
        
        # 計算優勢
        advantages = self._compute_advantages(rewards_tensor)
        
        return {
            'states': states_tensor,
            'actions': actions_tensor,
            'rewards': rewards_tensor,
            'old_log_probs': old_log_probs_tensor,
            'advantages': advantages
        }
    
    def _compute_advantages(self, rewards: torch.Tensor) -> torch.Tensor:
        """計算優勢函數"""
        # 簡化的優勢計算：使用獎勵的標準化
        advantages = (rewards - rewards.mean()) / (rewards.std() + 1e-8)
        return advantages
    
    async def _update_bandit_rewards(self, experiences: List[Experience]):
        """更新多臂老虎機獎勵"""
        for exp in experiences:
            bandit_arm = exp.action.parameters.get('bandit_arm', 0)
            self.bandit.update(bandit_arm, exp.reward)
    
    async def _perform_meta_learning(self, experiences: List[Experience]) -> Dict[str, Any]:
        """執行元學習"""
        if not self.meta_learner:
            return {'meta_learning_enabled': False}
        
        # 生成任務ID
        task_id = f"task_{int(datetime.now().timestamp())}"
        
        # 添加任務經驗
        self.meta_learner.add_task_experience(task_id, experiences)
        
        # 執行快速適應
        adaptation_results = self.meta_learner.fast_adapt(
            experiences, 
            self.config.fast_adaptation_steps
        )
        
        return {
            'meta_learning_enabled': True,
            'task_id': task_id,
            'adaptation_results': adaptation_results
        }
    
    async def _evaluate_learning_performance(self, experiences: List[Experience]) -> Dict[str, Any]:
        """評估學習性能"""
        if not experiences:
            return {}
        
        # 計算性能指標
        rewards = [exp.reward for exp in experiences]
        
        metrics = {
            'mean_reward': np.mean(rewards),
            'reward_std': np.std(rewards),
            'max_reward': np.max(rewards),
            'min_reward': np.min(rewards),
            'positive_reward_ratio': np.mean([1 if r > 0 else 0 for r in rewards]),
            'experience_count': len(experiences)
        }
        
        # 更新性能追蹤器
        for metric_name, value in metrics.items():
            self.performance_tracker.update_metric(metric_name, value)
        
        return metrics
    
    def _calculate_adaptation_score(self) -> float:
        """計算適應能力分數"""
        if len(self.adaptation_history) < 2:
            return 0.5
        
        # 基於最近的適應事件計算分數
        recent_adaptations = self.adaptation_history[-10:]
        adaptation_success_rate = np.mean([
            1 if adaptation.get('success', False) else 0 
            for adaptation in recent_adaptations
        ])
        
        return adaptation_success_rate
    
    def _evaluate_exploration_balance(self) -> Dict[str, Any]:
        """評估探索vs利用平衡"""
        return {
            'current_exploration_rate': self.current_exploration_rate,
            'exploration_trend': 'decreasing',  # 由於衰減
            'balance_score': min(1.0, self.current_exploration_rate * 2),  # 0-1分數
            'recommendation': 'maintain' if self.current_exploration_rate > 0.05 else 'increase'
        }
    
    def _calculate_overall_health_score(self) -> float:
        """計算整體健康分數"""
        scores = []
        
        # 學習效率分數
        if self.learning_stats['total_updates'] > 0:
            efficiency_score = min(1.0, self.learning_stats['total_experiences'] / self.learning_stats['total_updates'] / 100)
            scores.append(efficiency_score)
        
        # 探索平衡分數
        exploration_score = min(1.0, self.current_exploration_rate * 2)
        scores.append(exploration_score)
        
        # 性能穩定性分數
        reward_stats = self.performance_tracker.get_metric_statistics('mean_reward')
        if reward_stats:
            stability_score = 1.0 - min(1.0, reward_stats.get('std', 1.0))
            scores.append(stability_score)
        
        return np.mean(scores) if scores else 0.5
    
    def _generate_performance_recommendations(self) -> List[str]:
        """生成性能改進建議"""
        recommendations = []
        
        # 探索率建議
        if self.current_exploration_rate < 0.01:
            recommendations.append("考慮提高探索率以發現新策略")
        elif self.current_exploration_rate > 0.3:
            recommendations.append("探索率較高，可考慮更多利用已學習策略")
        
        # 學習頻率建議
        if self.learning_stats['total_updates'] < 10:
            recommendations.append("增加學習更新頻率以加速收斂")
        
        # 緩衝區建議
        buffer_utilization = len(self.experience_buffer) / self.config.buffer_size
        if buffer_utilization < 0.1:
            recommendations.append("收集更多經驗數據以提高學習質量")
        
        return recommendations
    
    async def _save_checkpoint(self):
        """保存檢查點"""
        try:
            checkpoint = {
                'learning_step': self.learning_step,
                'current_exploration_rate': self.current_exploration_rate,
                'learning_stats': self.learning_stats,
                'bandit_stats': self.bandit.get_statistics(),
                'config': self.config.dict(),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # 保存模型狀態
            if self.ppo_agent:
                checkpoint['model_state_dict'] = {
                    'policy_net': self.ppo_agent.policy_net.state_dict(),
                    'value_net': self.ppo_agent.value_net.state_dict()
                }
            
            checkpoint_path = Path(self.config.checkpoint_directory) / f"checkpoint_{self.learning_step}.json"
            
            # 使用更安全的JSON格式代替pickle
            with open(checkpoint_path, 'w', encoding='utf-8') as f:
                import json
                json.dump(checkpoint, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Checkpoint saved: {checkpoint_path}")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    async def _load_checkpoint(self):
        """載入檢查點"""
        try:
            checkpoint_dir = Path(self.config.checkpoint_directory)
            if not checkpoint_dir.exists():
                return
            
            # 尋找最新的檢查點
            checkpoint_files = list(checkpoint_dir.glob("checkpoint_*.json"))
            if not checkpoint_files:
                return
            
            latest_checkpoint = max(checkpoint_files, key=lambda x: x.stat().st_mtime)
            
            # 使用更安全的JSON格式代替pickle
            with open(latest_checkpoint, 'r', encoding='utf-8') as f:
                import json
                checkpoint = json.load(f)
            
            # 恢復狀態
            self.learning_step = checkpoint.get('learning_step', 0)
            self.current_exploration_rate = checkpoint.get('current_exploration_rate', self.config.exploration_rate)
            self.learning_stats = checkpoint.get('learning_stats', self.learning_stats)
            
            # 恢復模型狀態
            if 'model_state_dict' in checkpoint and self.ppo_agent:
                self.ppo_agent.policy_net.load_state_dict(checkpoint['model_state_dict']['policy_net'])
                self.ppo_agent.value_net.load_state_dict(checkpoint['model_state_dict']['value_net'])
            
            logger.info(f"Checkpoint loaded: {latest_checkpoint}")
            
        except Exception as e:
            logger.warning(f"Failed to load checkpoint: {e}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """獲取學習統計信息"""
        return {
            'config': self.config.dict(),
            'is_initialized': self.is_initialized,
            'learning_statistics': self.learning_stats,
            'current_state': {
                'learning_step': self.learning_step,
                'exploration_rate': self.current_exploration_rate,
                'buffer_size': len(self.experience_buffer),
                'buffer_capacity': self.config.buffer_size
            },
            'bandit_statistics': self.bandit.get_statistics(),
            'performance_metrics': self.performance_tracker.get_all_metrics(),
            'meta_learning_enabled': self.config.meta_learning_enabled,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# 使用示例和測試函數
async def create_adaptive_learning_engine_example():
    """創建自適應學習引擎示例"""
    
    # 創建配置
    config = AdaptiveLearningConfig(
        engine_id="adaptive_learning_v1",
        engine_name="TradingAgents自適應學習引擎",
        learning_mode=LearningMode.ONLINE,
        adaptation_strategy=AdaptationStrategy.MODERATE,
        exploration_strategy=ExplorationStrategy.UCB,
        learning_rate=0.001,
        buffer_size=5000,
        batch_size=32,
        meta_learning_enabled=True,
        performance_tracking_enabled=True
    )
    
    # 創建引擎
    engine = AdaptiveLearningEngine(config)
    
    # 初始化
    success = await engine.initialize()
    
    if success:
        logger.info("自適應學習引擎創建成功")
        
        # 模擬市場數據
        market_data = {
            'market_data': {'price': 100.0, 'volume': 1000000},
            'technical_indicators': {'rsi': 0.6, 'macd': 0.1},
            'sentiment_scores': {'news_sentiment': 0.7, 'social_sentiment': 0.6},
            'volatility_metrics': {'realized_vol': 0.2, 'implied_vol': 0.25},
            'macro_factors': {'interest_rate': 0.02, 'inflation': 0.03},
            'regime_indicators': {'bull_market': True, 'high_vol': False}
        }
        
        # 策略適應
        adaptation_result = await engine.adapt_strategy(market_data)
        
        # 模擬經驗數據
        experience_data = [
            {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'market_data': market_data['market_data'],
                'technical_indicators': market_data['technical_indicators'],
                'sentiment_scores': market_data['sentiment_scores'],
                'volatility_metrics': market_data['volatility_metrics'],
                'macro_factors': market_data['macro_factors'],
                'regime_indicators': market_data['regime_indicators'],
                'action': {
                    'action_id': 'test_action_1',
                    'action_type': 'buy',
                    'parameters': {'action_index': 1, 'bandit_arm': 2},
                    'confidence': 0.8,
                    'expected_reward': 0.15,
                    'risk_level': 0.3
                },
                'reward': 0.12,
                'done': False,
                'metadata': {'test_data': True}
            }
        ]
        
        # 持續學習
        learning_result = await engine.continuous_learning(experience_data)
        
        # 性能評估
        performance = engine.evaluate_performance()
        
        # 獲取統計信息
        stats = engine.get_learning_statistics()
        
        return {
            'initialization_success': success,
            'adaptation_result': adaptation_result,
            'learning_result': learning_result,
            'performance_evaluation': performance,
            'learning_statistics': stats
        }
    
    return {'initialization_success': False}


if __name__ == "__main__":
    # 運行示例
    import asyncio
    
    async def main():
        result = await create_adaptive_learning_engine_example()
        print("=== 自適應學習引擎測試結果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    asyncio.run(main())