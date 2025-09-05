#!/usr/bin/env python3
"""
Reinforcement Learning Agent - 強化學習智能體
天工 (TianGong) - 為深度行為學習提供強化學習反饋和策略優化

此模組提供：
1. Q-Learning智能體
2. Deep Q-Network (DQN) 智能體
3. Actor-Critic智能體
4. 多智能體協調
5. 自適應策略優化
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
import random
from pathlib import Path
import pickle

# Deep Learning imports
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import warnings
warnings.filterwarnings('ignore')

class ActionType(Enum):
    """動作類型"""
    ANALYZE_FUNDAMENTAL = "analyze_fundamental"      # 基本面分析
    ANALYZE_TECHNICAL = "analyze_technical"          # 技術分析
    INCREASE_POSITION = "increase_position"          # 增加倉位
    DECREASE_POSITION = "decrease_position"          # 減少倉位
    HOLD_POSITION = "hold_position"                  # 持有倉位
    SET_STOP_LOSS = "set_stop_loss"                 # 設置止損
    TAKE_PROFIT = "take_profit"                     # 獲利了結
    DIVERSIFY_PORTFOLIO = "diversify_portfolio"     # 分散投資組合
    FOCUS_STRATEGY = "focus_strategy"               # 集中策略
    SEEK_INFORMATION = "seek_information"           # 尋求信息
    WAIT_SIGNAL = "wait_signal"                     # 等待信號
    REVIEW_PERFORMANCE = "review_performance"        # 回顧績效

class StateSpace(Enum):
    """狀態空間維度"""
    MARKET_CONDITION = "market_condition"            # 市場狀況
    PORTFOLIO_STATE = "portfolio_state"              # 投資組合狀態
    USER_EMOTION = "user_emotion"                    # 用戶情緒
    RISK_LEVEL = "risk_level"                       # 風險水平
    PERFORMANCE_TREND = "performance_trend"          # 績效趨勢
    INFORMATION_AVAILABILITY = "information_availability"  # 信息可用性
    VOLATILITY_REGIME = "volatility_regime"          # 波動狀態
    TREND_STRENGTH = "trend_strength"                # 趨勢強度

class RewardType(Enum):
    """獎勵類型"""
    PERFORMANCE_REWARD = "performance_reward"        # 績效獎勵
    RISK_PENALTY = "risk_penalty"                   # 風險懲罰
    CONSISTENCY_BONUS = "consistency_bonus"          # 一致性獎勵
    LEARNING_REWARD = "learning_reward"             # 學習獎勵
    ADAPTATION_BONUS = "adaptation_bonus"            # 適應性獎勵
    EFFICIENCY_REWARD = "efficiency_reward"          # 效率獎勵
    DIVERSIFICATION_BONUS = "diversification_bonus" # 分散化獎勵

@dataclass
class RLState:
    """強化學習狀態"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    timestamp: float = field(default_factory=time.time)
    
    # 市場狀態
    market_conditions: Dict[str, float] = field(default_factory=dict)
    volatility_level: float = 0.0
    trend_strength: float = 0.0
    liquidity_score: float = 0.0
    
    # 投資組合狀態
    portfolio_value: float = 0.0
    position_sizes: Dict[str, float] = field(default_factory=dict)
    diversification_ratio: float = 0.0
    risk_exposure: float = 0.0
    
    # 用戶狀態
    emotional_state: float = 0.0           # -1 (恐懼) 到 1 (貪婪)
    confidence_level: float = 0.0          # 0 到 1
    experience_factor: float = 0.0         # 0 到 1
    fatigue_level: float = 0.0            # 0 到 1
    
    # 績效狀態
    recent_returns: List[float] = field(default_factory=list)
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    # 信息狀態
    information_quality: float = 0.0       # 可用信息的品質
    analysis_completeness: float = 0.0     # 分析的完整性
    
    # 時間狀態
    time_pressure: float = 0.0             # 時間壓力 0 到 1
    market_hours: bool = True              # 是否在交易時間
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass 
class RLAction:
    """強化學習動作"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.HOLD_POSITION
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 動作執行信息
    execution_timestamp: float = field(default_factory=time.time)
    execution_confidence: float = 0.0
    expected_outcome: Dict[str, float] = field(default_factory=dict)
    
    # 動作結果
    actual_outcome: Optional[Dict[str, float]] = None
    execution_success: bool = True
    execution_delay: float = 0.0
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RLReward:
    """強化學習獎勵"""
    reward_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    state_id: str = ""
    action_id: str = ""
    
    # 獎勵組成
    total_reward: float = 0.0
    reward_components: Dict[RewardType, float] = field(default_factory=dict)
    
    # 獎勵計算
    immediate_reward: float = 0.0          # 即時獎勵
    delayed_reward: float = 0.0            # 延遲獎勵
    normalized_reward: float = 0.0         # 標準化獎勵
    
    # 獎勵元數據
    calculation_method: str = ""
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class DQN(nn.Module):
    """Deep Q-Network"""
    
    def __init__(self, state_size: int, action_size: int, hidden_sizes: List[int] = [256, 128, 64]):
        super(DQN, self).__init__()
        
        self.state_size = state_size
        self.action_size = action_size
        
        # 構建網絡層
        layers = []
        prev_size = state_size
        
        for hidden_size in hidden_sizes:
            layers.extend([
                nn.Linear(prev_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(0.2)
            ])
            prev_size = hidden_size
        
        layers.append(nn.Linear(prev_size, action_size))
        
        self.network = nn.Sequential(*layers)
        
        # 優勢網絡和價值網絡(Dueling DQN)
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_sizes[-1], hidden_sizes[-1] // 2),
            nn.ReLU(),
            nn.Linear(hidden_sizes[-1] // 2, action_size)
        )
        
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_sizes[-1], hidden_sizes[-1] // 2),
            nn.ReLU(),
            nn.Linear(hidden_sizes[-1] // 2, 1)
        )
        
        # 共享特徵提取
        self.feature_extractor = nn.Sequential(*layers[:-1])
        
    def forward(self, x):
        # 特徵提取
        features = self.feature_extractor(x)
        
        # Dueling網絡結構
        advantage = self.advantage_stream(features)
        value = self.value_stream(features)
        
        # Q值計算
        q_values = value + (advantage - advantage.mean(dim=1, keepdim=True))
        
        return q_values

class ActorCritic(nn.Module):
    """Actor-Critic網絡"""
    
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 128):
        super(ActorCritic, self).__init__()
        
        # 共享特徵層
        self.shared_layers = nn.Sequential(
            nn.Linear(state_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU()
        )
        
        # Actor網絡
        self.actor = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, action_size),
            nn.Softmax(dim=-1)
        )
        
        # Critic網絡
        self.critic = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Linear(hidden_size // 2, 1)
        )
        
    def forward(self, x):
        shared_features = self.shared_layers(x)
        
        action_probs = self.actor(shared_features)
        state_value = self.critic(shared_features)
        
        return action_probs, state_value

class ReinforcementLearningAgent:
    """強化學習智能體"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 環境配置
        self.state_size = self.config.get('state_size', 20)
        self.action_size = len(ActionType)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.discount_factor = self.config.get('discount_factor', 0.99)
        self.exploration_rate = self.config.get('exploration_rate', 1.0)
        self.exploration_decay = self.config.get('exploration_decay', 0.995)
        self.min_exploration_rate = self.config.get('min_exploration_rate', 0.01)
        
        # 模型存儲
        self.model_storage_path = Path(self.config.get('model_storage_path', './rl_models'))
        self.model_storage_path.mkdir(exist_ok=True)
        
        # 網絡模型
        self.dqn_online = DQN(self.state_size, self.action_size)
        self.dqn_target = DQN(self.state_size, self.action_size)
        self.actor_critic = ActorCritic(self.state_size, self.action_size)
        
        # 優化器
        self.dqn_optimizer = optim.Adam(self.dqn_online.parameters(), lr=self.learning_rate)
        self.ac_optimizer = optim.Adam(self.actor_critic.parameters(), lr=self.learning_rate)
        
        # 經驗回放緩衝區
        self.replay_buffer = deque(maxlen=self.config.get('replay_buffer_size', 10000))
        self.batch_size = self.config.get('batch_size', 32)
        
        # 學習記錄
        self.learning_history: Dict[str, List[float]] = defaultdict(list)
        self.reward_history: Dict[str, List[RLReward]] = defaultdict(list)
        self.state_action_history: List[Tuple[RLState, RLAction, RLReward]] = []
        
        # 用戶特定的Q表和策略
        self.user_q_tables: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(float))
        )
        self.user_policies: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )
        
        # 配置參數
        self.rl_config = {
            'update_target_frequency': self.config.get('update_target_frequency', 1000),
            'reward_scaling': self.config.get('reward_scaling', 1.0),
            'experience_replay_start': self.config.get('experience_replay_start', 1000),
            'double_dqn': self.config.get('double_dqn', True),
            'prioritized_replay': self.config.get('prioritized_replay', False)
        }
        
        # 同步目標網絡
        self.update_target_network()
        self.training_step = 0
        
        self.logger.info("ReinforcementLearningAgent initialized")

    def state_to_tensor(self, state: RLState) -> torch.Tensor:
        """將狀態轉換為張量"""
        
        features = [
            # 市場條件特徵
            state.volatility_level,
            state.trend_strength,
            state.liquidity_score,
            
            # 投資組合特徵
            min(state.portfolio_value / 1000000, 1.0),  # 標準化到百萬
            state.diversification_ratio,
            state.risk_exposure,
            
            # 用戶狀態特徵
            state.emotional_state,
            state.confidence_level,
            state.experience_factor,
            state.fatigue_level,
            
            # 績效特徵
            np.mean(state.recent_returns) if state.recent_returns else 0.0,
            state.sharpe_ratio,
            state.max_drawdown,
            state.win_rate,
            
            # 信息特徵
            state.information_quality,
            state.analysis_completeness,
            
            # 時間特徵
            state.time_pressure,
            float(state.market_hours),
            
            # 額外特徵(填充到state_size)
            0.0, 0.0  # 如果需要更多特徵可以添加
        ]
        
        # 確保特徵數量匹配
        features = features[:self.state_size]
        while len(features) < self.state_size:
            features.append(0.0)
        
        return torch.FloatTensor(features).unsqueeze(0)

    def select_action(
        self, 
        state: RLState, 
        user_id: str, 
        exploration: bool = True
    ) -> RLAction:
        """選擇動作"""
        
        # 探索vs利用決策
        if exploration and random.random() < self.exploration_rate:
            # 探索：隨機選擇動作
            action_type = random.choice(list(ActionType))
        else:
            # 利用：使用Q網絡選擇動作
            state_tensor = self.state_to_tensor(state)
            
            with torch.no_grad():
                q_values = self.dqn_online(state_tensor)
                action_idx = q_values.argmax().item()
                action_type = list(ActionType)[action_idx]
        
        # 創建動作
        action = RLAction(
            action_type=action_type,
            execution_confidence=1.0 - self.exploration_rate,
            action_parameters=self._generate_action_parameters(action_type, state)
        )
        
        return action

    def _generate_action_parameters(
        self, 
        action_type: ActionType, 
        state: RLState
    ) -> Dict[str, Any]:
        """生成動作參數"""
        
        parameters = {}
        
        if action_type == ActionType.INCREASE_POSITION:
            # 基於風險水平和信心度決定增加倉位的大小
            base_size = 0.1
            risk_adjustment = (1.0 - state.risk_exposure) * 0.1
            confidence_adjustment = state.confidence_level * 0.05
            parameters['size_increase'] = min(base_size + risk_adjustment + confidence_adjustment, 0.2)
            
        elif action_type == ActionType.DECREASE_POSITION:
            # 基於風險水平決定減少倉位的大小
            risk_factor = state.risk_exposure
            parameters['size_decrease'] = min(0.05 + risk_factor * 0.15, 0.3)
            
        elif action_type == ActionType.SET_STOP_LOSS:
            # 基於波動率設置止損水平
            base_stop = 0.05
            volatility_adjustment = state.volatility_level * 0.03
            parameters['stop_loss_level'] = min(base_stop + volatility_adjustment, 0.15)
            
        elif action_type == ActionType.TAKE_PROFIT:
            # 基於趨勢強度設置獲利目標
            base_target = 0.08
            trend_adjustment = state.trend_strength * 0.05
            parameters['profit_target'] = min(base_target + trend_adjustment, 0.2)
            
        elif action_type == ActionType.DIVERSIFY_PORTFOLIO:
            # 基於當前分散度決定分散化程度
            target_diversification = 0.8
            current_div = state.diversification_ratio
            parameters['diversification_increase'] = max(0, target_diversification - current_div)
            
        return parameters

    def calculate_reward(
        self, 
        state: RLState, 
        action: RLAction, 
        next_state: RLState,
        user_id: str
    ) -> RLReward:
        """計算獎勵"""
        
        reward = RLReward(
            user_id=user_id,
            state_id=state.state_id,
            action_id=action.action_id
        )
        
        reward_components = {}
        
        # 1. 績效獎勵
        portfolio_change = next_state.portfolio_value - state.portfolio_value
        if state.portfolio_value > 0:
            return_rate = portfolio_change / state.portfolio_value
            performance_reward = return_rate * 100  # 放大獎勵信號
        else:
            performance_reward = 0.0
        
        reward_components[RewardType.PERFORMANCE_REWARD] = performance_reward
        
        # 2. 風險懲罰
        risk_increase = next_state.risk_exposure - state.risk_exposure
        if risk_increase > 0:
            risk_penalty = -risk_increase * 50  # 風險增加的懲罰
        else:
            risk_penalty = abs(risk_increase) * 10  # 風險降低的獎勵
        
        reward_components[RewardType.RISK_PENALTY] = risk_penalty
        
        # 3. 一致性獎勵
        if len(next_state.recent_returns) >= 3:
            returns_std = np.std(next_state.recent_returns[-3:])
            consistency_bonus = max(0, 10 - returns_std * 100)  # 一致性獎勵
        else:
            consistency_bonus = 0.0
        
        reward_components[RewardType.CONSISTENCY_BONUS] = consistency_bonus
        
        # 4. 學習獎勵(基於信息利用)
        info_improvement = next_state.information_quality - state.information_quality
        learning_reward = info_improvement * 20
        reward_components[RewardType.LEARNING_REWARD] = learning_reward
        
        # 5. 效率獎勵(基於夏普比率)
        sharpe_improvement = next_state.sharpe_ratio - state.sharpe_ratio
        efficiency_reward = sharpe_improvement * 30
        reward_components[RewardType.EFFICIENCY_REWARD] = efficiency_reward
        
        # 6. 分散化獎勵
        diversification_improvement = next_state.diversification_ratio - state.diversification_ratio
        if action.action_type == ActionType.DIVERSIFY_PORTFOLIO and diversification_improvement > 0:
            diversification_bonus = diversification_improvement * 25
        else:
            diversification_bonus = 0.0
        
        reward_components[RewardType.DIVERSIFICATION_BONUS] = diversification_bonus
        
        # 計算總獎勵
        total_reward = sum(reward_components.values())
        normalized_reward = np.tanh(total_reward / 100.0)  # 標準化到[-1, 1]
        
        reward.reward_components = reward_components
        reward.total_reward = total_reward
        reward.normalized_reward = normalized_reward
        reward.immediate_reward = normalized_reward
        
        return reward

    def store_experience(
        self, 
        state: RLState, 
        action: RLAction, 
        reward: RLReward, 
        next_state: RLState, 
        done: bool = False
    ):
        """存儲經驗"""
        
        experience = (
            self.state_to_tensor(state),
            list(ActionType).index(action.action_type),
            reward.normalized_reward,
            self.state_to_tensor(next_state),
            done
        )
        
        self.replay_buffer.append(experience)
        self.state_action_history.append((state, action, reward))
        
        # 記錄獎勵歷史
        self.reward_history[reward.user_id].append(reward)

    async def train_dqn(self):
        """訓練DQN模型"""
        
        if len(self.replay_buffer) < self.rl_config['experience_replay_start']:
            return
        
        # 採樣批次
        batch = random.sample(self.replay_buffer, min(self.batch_size, len(self.replay_buffer)))
        
        states = torch.cat([experience[0] for experience in batch])
        actions = torch.LongTensor([experience[1] for experience in batch])
        rewards = torch.FloatTensor([experience[2] for experience in batch])
        next_states = torch.cat([experience[3] for experience in batch])
        dones = torch.BoolTensor([experience[4] for experience in batch])
        
        # 當前Q值
        current_q_values = self.dqn_online(states).gather(1, actions.unsqueeze(1))
        
        # 目標Q值
        with torch.no_grad():
            if self.rl_config['double_dqn']:
                # Double DQN
                next_actions = self.dqn_online(next_states).argmax(1)
                next_q_values = self.dqn_target(next_states).gather(1, next_actions.unsqueeze(1))
            else:
                # 標準DQN
                next_q_values = self.dqn_target(next_states).max(1)[0].unsqueeze(1)
            
            target_q_values = rewards.unsqueeze(1) + \
                              (self.discount_factor * next_q_values * ~dones.unsqueeze(1))
        
        # 計算損失
        loss = F.mse_loss(current_q_values, target_q_values)
        
        # 反向傳播
        self.dqn_optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.dqn_online.parameters(), 1.0)
        self.dqn_optimizer.step()
        
        # 記錄學習指標
        self.learning_history['dqn_loss'].append(loss.item())
        
        # 更新目標網絡
        self.training_step += 1
        if self.training_step % self.rl_config['update_target_frequency'] == 0:
            self.update_target_network()
        
        # 衰減探索率
        self.exploration_rate = max(
            self.min_exploration_rate,
            self.exploration_rate * self.exploration_decay
        )

    async def train_actor_critic(self):
        """訓練Actor-Critic模型"""
        
        if len(self.state_action_history) < self.batch_size:
            return
        
        # 準備訓練數據
        batch = self.state_action_history[-self.batch_size:]
        
        states = torch.cat([self.state_to_tensor(exp[0]) for exp in batch])
        actions = torch.LongTensor([list(ActionType).index(exp[1].action_type) for exp in batch])
        rewards = torch.FloatTensor([exp[2].normalized_reward for exp in batch])
        
        # 前向傳播
        action_probs, state_values = self.actor_critic(states)
        
        # 計算優勢函數
        returns = []
        discounted_return = 0
        for reward in reversed(rewards):
            discounted_return = reward + self.discount_factor * discounted_return
            returns.insert(0, discounted_return)
        
        returns = torch.FloatTensor(returns)
        advantages = returns - state_values.squeeze()
        
        # Actor損失(策略梯度)
        log_probs = torch.log(action_probs + 1e-8)
        selected_log_probs = log_probs.gather(1, actions.unsqueeze(1)).squeeze()
        actor_loss = -(selected_log_probs * advantages.detach()).mean()
        
        # Critic損失(價值函數)
        critic_loss = F.mse_loss(state_values.squeeze(), returns)
        
        # 熵獎勵(鼓勵探索)
        entropy_bonus = -(action_probs * log_probs).sum(dim=1).mean()
        
        # 總損失
        total_loss = actor_loss + 0.5 * critic_loss - 0.01 * entropy_bonus
        
        # 反向傳播
        self.ac_optimizer.zero_grad()
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.actor_critic.parameters(), 1.0)
        self.ac_optimizer.step()
        
        # 記錄學習指標
        self.learning_history['ac_loss'].append(total_loss.item())
        self.learning_history['actor_loss'].append(actor_loss.item())
        self.learning_history['critic_loss'].append(critic_loss.item())

    def update_target_network(self):
        """更新目標網絡"""
        self.dqn_target.load_state_dict(self.dqn_online.state_dict())

    async def update_user_policy(self, user_id: str):
        """更新用戶特定策略"""
        
        user_rewards = self.reward_history[user_id]
        if len(user_rewards) < 10:
            return
        
        # 分析用戶的行為偏好
        recent_rewards = user_rewards[-20:]
        
        # 統計動作-獎勵關聯
        action_rewards = defaultdict(list)
        for reward in recent_rewards:
            # 找到對應的動作
            for state, action, r in self.state_action_history:
                if r.reward_id == reward.reward_id:
                    action_rewards[action.action_type].append(reward.normalized_reward)
                    break
        
        # 更新用戶策略
        for action_type, rewards_list in action_rewards.items():
            if rewards_list:
                avg_reward = np.mean(rewards_list)
                self.user_policies[user_id][action_type.value] = avg_reward

    def get_user_performance_metrics(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶性能指標"""
        
        user_rewards = self.reward_history[user_id]
        if not user_rewards:
            return {'total_rewards': 0, 'average_reward': 0, 'reward_trend': 'stable'}
        
        total_rewards = sum(r.normalized_reward for r in user_rewards)
        average_reward = total_rewards / len(user_rewards)
        
        # 計算趨勢
        if len(user_rewards) >= 10:
            recent_avg = np.mean([r.normalized_reward for r in user_rewards[-10:]])
            earlier_avg = np.mean([r.normalized_reward for r in user_rewards[-20:-10]]) \
                          if len(user_rewards) >= 20 else average_reward
            
            if recent_avg > earlier_avg * 1.1:
                trend = 'improving'
            elif recent_avg < earlier_avg * 0.9:
                trend = 'declining'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        # 獎勵組成分析
        component_stats = defaultdict(list)
        for reward in user_rewards[-50:]:  # 最近50個獎勵
            for reward_type, value in reward.reward_components.items():
                component_stats[reward_type.value].append(value)
        
        component_averages = {
            comp: np.mean(values) for comp, values in component_stats.items()
        }
        
        return {
            'total_rewards': total_rewards,
            'average_reward': average_reward,
            'reward_count': len(user_rewards),
            'reward_trend': trend,
            'component_averages': component_averages,
            'learning_progress': self._calculate_learning_progress(user_id)
        }

    def _calculate_learning_progress(self, user_id: str) -> float:
        """計算學習進度"""
        
        user_rewards = self.reward_history[user_id]
        if len(user_rewards) < 20:
            return 0.0
        
        # 比較早期和最近的性能
        early_rewards = [r.normalized_reward for r in user_rewards[:10]]
        recent_rewards = [r.normalized_reward for r in user_rewards[-10:]]
        
        early_avg = np.mean(early_rewards)
        recent_avg = np.mean(recent_rewards)
        
        # 學習進度 = (最近表現 - 早期表現) / 早期表現的標準差
        early_std = np.std(early_rewards)
        if early_std > 0:
            progress = (recent_avg - early_avg) / early_std
            return max(-2.0, min(progress, 2.0))  # 限制在[-2, 2]範圍
        else:
            return 0.0

    async def save_models(self, user_id: Optional[str] = None):
        """保存模型"""
        
        try:
            # 保存DQN模型
            torch.save(self.dqn_online.state_dict(), 
                      self.model_storage_path / 'dqn_online.pth')
            torch.save(self.dqn_target.state_dict(), 
                      self.model_storage_path / 'dqn_target.pth')
            torch.save(self.actor_critic.state_dict(), 
                      self.model_storage_path / 'actor_critic.pth')
            
            # 保存用戶策略
            if user_id:
                policy_file = self.model_storage_path / f'user_policy_{user_id}.pkl'
                with open(policy_file, 'wb') as f:
                    pickle.dump(self.user_policies[user_id], f)
            else:
                # 保存所有用戶策略
                with open(self.model_storage_path / 'all_user_policies.pkl', 'wb') as f:
                    pickle.dump(dict(self.user_policies), f)
            
            # 保存學習歷史
            with open(self.model_storage_path / 'learning_history.json', 'w') as f:
                serializable_history = {
                    k: v[-1000:] for k, v in self.learning_history.items()  # 只保存最近1000個記錄
                }
                json.dump(serializable_history, f)
            
            self.logger.info("模型保存完成")
            
        except Exception as e:
            self.logger.error(f"模型保存失敗: {e}")

    async def load_models(self, user_id: Optional[str] = None):
        """加載模型"""
        
        try:
            # 加載DQN模型
            dqn_online_path = self.model_storage_path / 'dqn_online.pth'
            if dqn_online_path.exists():
                self.dqn_online.load_state_dict(torch.load(dqn_online_path))
                
            dqn_target_path = self.model_storage_path / 'dqn_target.pth'
            if dqn_target_path.exists():
                self.dqn_target.load_state_dict(torch.load(dqn_target_path))
                
            ac_path = self.model_storage_path / 'actor_critic.pth'
            if ac_path.exists():
                self.actor_critic.load_state_dict(torch.load(ac_path))
            
            # 加載用戶策略
            if user_id:
                policy_file = self.model_storage_path / f'user_policy_{user_id}.pkl'
                if policy_file.exists():
                    with open(policy_file, 'rb') as f:
                        self.user_policies[user_id] = pickle.load(f)
            else:
                # 加載所有用戶策略
                policy_file = self.model_storage_path / 'all_user_policies.pkl'
                if policy_file.exists():
                    with open(policy_file, 'rb') as f:
                        loaded_policies = pickle.load(f)
                        self.user_policies.update(loaded_policies)
            
            # 加載學習歷史
            history_file = self.model_storage_path / 'learning_history.json'
            if history_file.exists():
                with open(history_file, 'r') as f:
                    loaded_history = json.load(f)
                    for k, v in loaded_history.items():
                        self.learning_history[k] = v
            
            self.logger.info("模型加載完成")
            
        except Exception as e:
            self.logger.error(f"模型加載失敗: {e}")

    def reset_exploration(self, exploration_rate: float = None):
        """重置探索率"""
        if exploration_rate is not None:
            self.exploration_rate = exploration_rate
        else:
            self.exploration_rate = self.config.get('exploration_rate', 1.0)

    def get_learning_statistics(self) -> Dict[str, Any]:
        """獲取學習統計信息"""
        
        stats = {
            'training_steps': self.training_step,
            'exploration_rate': self.exploration_rate,
            'replay_buffer_size': len(self.replay_buffer),
            'total_experiences': len(self.state_action_history),
            'active_users': len(self.user_policies)
        }
        
        # 學習曲線統計
        if self.learning_history:
            for metric, values in self.learning_history.items():
                if values:
                    stats[f'{metric}_current'] = values[-1]
                    stats[f'{metric}_average'] = np.mean(values[-100:])  # 最近100個值的平均
        
        return stats