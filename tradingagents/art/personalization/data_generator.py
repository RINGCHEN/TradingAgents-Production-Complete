#!/usr/bin/env python3
"""
Personalization Data Generator - 個人化學習數據生成器
天工 (TianGong) - 為ART系統生成個人化學習數據

此模組提供：
1. PersonalizationDataGenerator - 個人化數據生成核心
2. LearningDataPoint - 學習數據點結構
3. PersonalizationContext - 個人化上下文管理
4. DataGenerationConfig - 數據生成配置
5. LearningObjective - 學習目標定義
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Generator, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import hashlib
import os
import uuid
import numpy as np
from collections import defaultdict, deque
import random
import math

class LearningObjective(Enum):
    """學習目標"""
    RISK_MANAGEMENT = "risk_management"           # 風險管理
    PROFIT_OPTIMIZATION = "profit_optimization"   # 利潤優化
    MARKET_TIMING = "market_timing"               # 市場時機把握
    PORTFOLIO_DIVERSIFICATION = "portfolio_diversification"  # 投資組合多樣化
    BEHAVIORAL_IMPROVEMENT = "behavioral_improvement"  # 行為改善
    STRATEGY_REFINEMENT = "strategy_refinement"   # 策略優化
    DECISION_SPEED = "decision_speed"            # 決策速度
    EMOTIONAL_CONTROL = "emotional_control"      # 情緒控制

class PersonalizationStrategy(Enum):
    """個人化策略"""
    COLLABORATIVE_FILTERING = "collaborative_filtering"  # 協同過濾
    CONTENT_BASED = "content_based"                      # 基於內容
    HYBRID_APPROACH = "hybrid_approach"                  # 混合方法
    REINFORCEMENT_LEARNING = "reinforcement_learning"    # 強化學習
    BEHAVIORAL_CLONING = "behavioral_cloning"            # 行為克隆
    PREFERENCE_LEARNING = "preference_learning"          # 偏好學習

@dataclass
class LearningDataPoint:
    """學習數據點"""
    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    timestamp: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    action: Dict[str, Any] = field(default_factory=dict)
    outcome: Dict[str, Any] = field(default_factory=dict)
    reward: float = 0.0
    learning_objective: LearningObjective = LearningObjective.PROFIT_OPTIMIZATION
    personalization_features: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def feature_vector(self) -> List[float]:
        """提取特徵向量"""
        features = []
        
        # 基本特徵
        features.extend([
            self.reward,
            self.timestamp % 86400,  # 時間特徵
            hash(self.learning_objective.value) % 1000 / 1000.0
        ])
        
        # 個人化特徵
        if self.personalization_features:
            for key in sorted(self.personalization_features.keys()):
                value = self.personalization_features[key]
                if isinstance(value, (int, float)):
                    features.append(float(value))
                elif isinstance(value, bool):
                    features.append(1.0 if value else 0.0)
                elif isinstance(value, str):
                    features.append(hash(value) % 1000 / 1000.0)
        
        return features

@dataclass
class PersonalizationContext:
    """個人化上下文"""
    user_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    behavioral_patterns: Dict[str, Any] = field(default_factory=dict)
    historical_performance: Dict[str, float] = field(default_factory=dict)
    current_goals: List[LearningObjective] = field(default_factory=list)
    risk_tolerance: float = 0.5  # 0.0 (保守) 到 1.0 (激進)
    experience_level: float = 0.5  # 0.0 (新手) 到 1.0 (專家)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    contextual_factors: Dict[str, Any] = field(default_factory=dict)
    
    def get_personalization_score(self, data_point: LearningDataPoint) -> float:
        """計算個人化相關性分數"""
        score = 0.0
        
        # 目標相關性
        if data_point.learning_objective in self.current_goals:
            score += 0.3
        
        # 風險偏好匹配
        if 'risk_level' in data_point.personalization_features:
            risk_diff = abs(self.risk_tolerance - data_point.personalization_features['risk_level'])
            score += 0.2 * (1.0 - risk_diff)
        
        # 經驗水平匹配
        if 'complexity_level' in data_point.personalization_features:
            exp_diff = abs(self.experience_level - data_point.personalization_features['complexity_level'])
            score += 0.2 * (1.0 - exp_diff)
        
        # 行為模式匹配
        if self.behavioral_patterns and data_point.personalization_features:
            pattern_match = 0.0
            for pattern, value in self.behavioral_patterns.items():
                if pattern in data_point.personalization_features:
                    if isinstance(value, (int, float)) and isinstance(data_point.personalization_features[pattern], (int, float)):
                        similarity = 1.0 - abs(value - data_point.personalization_features[pattern])
                        pattern_match += similarity
            score += 0.3 * (pattern_match / max(len(self.behavioral_patterns), 1))
        
        return min(score, 1.0)

@dataclass
class DataGenerationConfig:
    """數據生成配置"""
    target_samples_per_user: int = 1000
    personalization_ratio: float = 0.7  # 個人化數據比例
    diversity_factor: float = 0.3        # 多樣性因子
    quality_threshold: float = 0.6       # 質量閾值
    temporal_window_days: int = 30       # 時間窗口
    feature_dimensions: int = 50         # 特徵維度
    augmentation_factor: float = 2.0     # 數據增強倍數
    noise_level: float = 0.1            # 噪聲水平
    balance_objectives: bool = True      # 平衡學習目標
    include_negative_examples: bool = True  # 包含負例
    metadata: Dict[str, Any] = field(default_factory=dict)

class PersonalizationDataGenerator:
    """個人化數據生成器"""
    
    def __init__(self, config: DataGenerationConfig):
        self.config = config
        self.user_contexts: Dict[str, PersonalizationContext] = {}
        self.data_cache: Dict[str, List[LearningDataPoint]] = {}
        self.generation_history: List[Dict[str, Any]] = []
        self.quality_metrics: Dict[str, float] = {}
        
        # 初始化隨機種子
        random.seed(42)
        np.random.seed(42)
        
        logging.info("PersonalizationDataGenerator initialized")
    
    async def generate_personalized_dataset(self, 
                                          user_contexts: List[PersonalizationContext],
                                          historical_data: Optional[List[LearningDataPoint]] = None) -> List[LearningDataPoint]:
        """生成個人化數據集"""
        generated_data = []
        
        # 更新用戶上下文
        for context in user_contexts:
            self.user_contexts[context.user_id] = context
        
        logging.info(f"Generating personalized dataset for {len(user_contexts)} users")
        
        for context in user_contexts:
            user_data = await self._generate_user_specific_data(context, historical_data)
            generated_data.extend(user_data)
        
        # 數據後處理
        processed_data = await self._post_process_data(generated_data)
        
        # 記錄生成歷史
        generation_record = {
            'timestamp': time.time(),
            'users_count': len(user_contexts),
            'generated_samples': len(processed_data),
            'config': self.config.__dict__.copy()
        }
        self.generation_history.append(generation_record)
        
        logging.info(f"Generated {len(processed_data)} personalized data points")
        return processed_data
    
    async def _generate_user_specific_data(self, 
                                         context: PersonalizationContext,
                                         historical_data: Optional[List[LearningDataPoint]] = None) -> List[LearningDataPoint]:
        """為特定用戶生成數據"""
        user_data = []
        
        # 基於歷史數據的模式學習
        if historical_data:
            user_historical = [dp for dp in historical_data if dp.user_id == context.user_id]
            patterns = await self._extract_user_patterns(user_historical)
            context.behavioral_patterns.update(patterns)
        
        # 生成目標樣本數
        target_samples = self.config.target_samples_per_user
        personalized_samples = int(target_samples * self.config.personalization_ratio)
        diverse_samples = target_samples - personalized_samples
        
        # 生成個人化樣本
        personalized_data = await self._generate_personalized_samples(
            context, personalized_samples
        )
        user_data.extend(personalized_data)
        
        # 生成多樣性樣本
        diverse_data = await self._generate_diverse_samples(
            context, diverse_samples
        )
        user_data.extend(diverse_data)
        
        # 數據增強
        if self.config.augmentation_factor > 1.0:
            augmented_data = await self._augment_user_data(user_data, context)
            user_data.extend(augmented_data)
        
        return user_data
    
    async def _extract_user_patterns(self, historical_data: List[LearningDataPoint]) -> Dict[str, Any]:
        """提取用戶行為模式"""
        patterns = {}
        
        if not historical_data:
            return patterns
        
        # 獎勵偏好
        rewards = [dp.reward for dp in historical_data]
        if rewards:
            patterns['avg_reward'] = np.mean(rewards)
            patterns['reward_volatility'] = np.std(rewards)
        
        # 時間偏好
        timestamps = [dp.timestamp % 86400 for dp in historical_data]  # 一天內的時間
        if timestamps:
            patterns['preferred_hour'] = np.mean(timestamps) / 3600
        
        # 學習目標偏好
        objectives = [dp.learning_objective for dp in historical_data]
        if objectives:
            objective_counts = defaultdict(int)
            for obj in objectives:
                objective_counts[obj.value] += 1
            patterns['preferred_objectives'] = dict(objective_counts)
        
        # 特徵偏好
        all_features = defaultdict(list)
        for dp in historical_data:
            for key, value in dp.personalization_features.items():
                if isinstance(value, (int, float)):
                    all_features[key].append(value)
        
        for feature, values in all_features.items():
            if values:
                patterns[f'{feature}_preference'] = np.mean(values)
                patterns[f'{feature}_variance'] = np.var(values)
        
        return patterns
    
    async def _generate_personalized_samples(self, 
                                           context: PersonalizationContext,
                                           num_samples: int) -> List[LearningDataPoint]:
        """生成個人化樣本"""
        samples = []
        
        for _ in range(num_samples):
            # 基於用戶偏好生成數據點
            data_point = LearningDataPoint(
                user_id=context.user_id,
                timestamp=time.time() + random.uniform(-self.config.temporal_window_days * 86400, 0)
            )
            
            # 選擇學習目標
            if context.current_goals:
                data_point.learning_objective = random.choice(context.current_goals)
            else:
                data_point.learning_objective = random.choice(list(LearningObjective))
            
            # 生成個人化特徵
            data_point.personalization_features = await self._generate_personalized_features(context)
            
            # 生成狀態、行為和結果
            data_point.state = await self._generate_state(context, data_point)
            data_point.action = await self._generate_action(context, data_point)
            data_point.outcome = await self._generate_outcome(context, data_point)
            data_point.reward = await self._calculate_reward(context, data_point)
            
            # 添加上下文信息
            data_point.context = {
                'market_conditions': context.market_conditions.copy(),
                'user_goals': [goal.value for goal in context.current_goals],
                'risk_tolerance': context.risk_tolerance,
                'experience_level': context.experience_level
            }
            
            samples.append(data_point)
        
        return samples
    
    async def _generate_diverse_samples(self, 
                                      context: PersonalizationContext,
                                      num_samples: int) -> List[LearningDataPoint]:
        """生成多樣性樣本"""
        samples = []
        
        for _ in range(num_samples):
            data_point = LearningDataPoint(
                user_id=context.user_id,
                timestamp=time.time() + random.uniform(-self.config.temporal_window_days * 86400, 0)
            )
            
            # 隨機選擇學習目標
            data_point.learning_objective = random.choice(list(LearningObjective))
            
            # 生成隨機特徵（與用戶偏好差異較大）
            data_point.personalization_features = await self._generate_diverse_features(context)
            
            # 生成狀態、行為和結果
            data_point.state = await self._generate_state(context, data_point)
            data_point.action = await self._generate_action(context, data_point)
            data_point.outcome = await self._generate_outcome(context, data_point)
            data_point.reward = await self._calculate_reward(context, data_point)
            
            # 添加多樣性標記
            data_point.metadata['diversity_sample'] = True
            
            samples.append(data_point)
        
        return samples
    
    async def _generate_personalized_features(self, context: PersonalizationContext) -> Dict[str, Any]:
        """生成個人化特徵"""
        features = {}
        
        # 風險相關特徵
        risk_noise = random.gauss(0, self.config.noise_level)
        features['risk_level'] = max(0.0, min(1.0, context.risk_tolerance + risk_noise))
        
        # 經驗相關特徵
        exp_noise = random.gauss(0, self.config.noise_level)
        features['complexity_level'] = max(0.0, min(1.0, context.experience_level + exp_noise))
        
        # 基於行為模式的特徵
        for pattern, value in context.behavioral_patterns.items():
            if isinstance(value, (int, float)):
                noise = random.gauss(0, self.config.noise_level)
                features[pattern] = value + noise
        
        # 時間偏好特徵
        if 'preferred_hour' in context.behavioral_patterns:
            hour_noise = random.gauss(0, 2)  # 2小時標準差
            preferred_hour = context.behavioral_patterns['preferred_hour'] + hour_noise
            features['time_preference'] = (preferred_hour % 24) / 24.0
        else:
            features['time_preference'] = random.uniform(0, 1)
        
        # 市場條件適應特徵
        if context.market_conditions:
            features['market_sentiment'] = context.market_conditions.get('sentiment', 0.5)
            features['volatility_preference'] = context.market_conditions.get('volatility', 0.5)
        
        # 隨機特徵填充
        for i in range(self.config.feature_dimensions - len(features)):
            features[f'feature_{i}'] = random.uniform(0, 1)
        
        return features
    
    async def _generate_diverse_features(self, context: PersonalizationContext) -> Dict[str, Any]:
        """生成多樣性特徵"""
        features = {}
        
        # 與用戶偏好相反的特徵
        features['risk_level'] = 1.0 - context.risk_tolerance + random.gauss(0, self.config.noise_level)
        features['complexity_level'] = 1.0 - context.experience_level + random.gauss(0, self.config.noise_level)
        
        # 隨機特徵
        for i in range(self.config.feature_dimensions):
            features[f'feature_{i}'] = random.uniform(0, 1)
        
        # 確保特徵在有效範圍內
        for key, value in features.items():
            if isinstance(value, (int, float)):
                features[key] = max(0.0, min(1.0, value))
        
        return features
    
    async def _generate_state(self, context: PersonalizationContext, data_point: LearningDataPoint) -> Dict[str, Any]:
        """生成狀態信息"""
        state = {
            'portfolio_value': random.uniform(10000, 1000000),
            'cash_ratio': random.uniform(0.1, 0.5),
            'position_count': random.randint(1, 20),
            'market_trend': random.choice(['bullish', 'bearish', 'sideways']),
            'volatility_index': random.uniform(0.1, 0.8),
            'time_of_day': data_point.timestamp % 86400,
            'day_of_week': int((data_point.timestamp / 86400) % 7),
            'economic_indicators': {
                'gdp_growth': random.uniform(-0.05, 0.05),
                'inflation_rate': random.uniform(0.01, 0.08),
                'interest_rate': random.uniform(0.0, 0.1)
            }
        }
        
        return state
    
    async def _generate_action(self, context: PersonalizationContext, data_point: LearningDataPoint) -> Dict[str, Any]:
        """生成行為信息"""
        action_types = ['buy', 'sell', 'hold', 'rebalance']
        
        action = {
            'type': random.choice(action_types),
            'symbol': f"STOCK_{random.randint(1, 100):03d}",
            'quantity': random.randint(1, 1000),
            'price': random.uniform(10, 500),
            'confidence': random.uniform(0.3, 0.9),
            'reasoning': data_point.learning_objective.value,
            'timing_factor': random.uniform(0.1, 1.0),
            'risk_adjustment': data_point.personalization_features.get('risk_level', 0.5)
        }
        
        return action
    
    async def _generate_outcome(self, context: PersonalizationContext, data_point: LearningDataPoint) -> Dict[str, Any]:
        """生成結果信息"""
        # 基於風險水平和市場條件模擬結果
        risk_level = data_point.personalization_features.get('risk_level', 0.5)
        market_factor = random.gauss(0, 0.1)
        
        if data_point.action['type'] == 'buy':
            base_return = random.gauss(0.02, 0.15)  # 2%平均收益，15%標準差
        elif data_point.action['type'] == 'sell':
            base_return = random.gauss(-0.01, 0.1)  # 避免虧損
        else:  # hold或rebalance
            base_return = random.gauss(0.005, 0.05)  # 小幅波動
        
        # 風險調整收益
        adjusted_return = base_return * (1 + risk_level * 0.5) + market_factor
        
        outcome = {
            'return_rate': adjusted_return,
            'absolute_return': adjusted_return * data_point.action['price'] * data_point.action['quantity'],
            'execution_time': random.uniform(0.1, 5.0),  # 執行時間（秒）
            'slippage': random.uniform(0.0, 0.02),        # 滑價
            'transaction_cost': random.uniform(1.0, 50.0), # 交易成本
            'market_impact': random.uniform(0.0, 0.001),   # 市場影響
            'success': adjusted_return > 0
        }
        
        return outcome
    
    async def _calculate_reward(self, context: PersonalizationContext, data_point: LearningDataPoint) -> float:
        """計算獎勵"""
        base_reward = data_point.outcome['return_rate']
        
        # 根據學習目標調整獎勵
        if data_point.learning_objective == LearningObjective.RISK_MANAGEMENT:
            # 風險管理：降低波動性的獎勵
            risk_penalty = abs(data_point.outcome['return_rate']) * 0.5
            base_reward -= risk_penalty
        elif data_point.learning_objective == LearningObjective.PROFIT_OPTIMIZATION:
            # 利潤優化：純粹基於收益
            pass
        elif data_point.learning_objective == LearningObjective.DECISION_SPEED:
            # 決策速度：快速決策的獎勵
            speed_bonus = 1.0 / (data_point.outcome['execution_time'] + 0.1)
            base_reward += speed_bonus * 0.1
        
        # 交易成本懲罰
        cost_penalty = data_point.outcome['transaction_cost'] / 10000.0
        base_reward -= cost_penalty
        
        # 個人化調整
        personalization_score = context.get_personalization_score(data_point)
        base_reward *= (0.5 + 0.5 * personalization_score)  # 0.5-1.0倍調整
        
        return base_reward
    
    async def _augment_user_data(self, 
                                original_data: List[LearningDataPoint],
                                context: PersonalizationContext) -> List[LearningDataPoint]:
        """數據增強"""
        augmented_data = []
        augment_count = int(len(original_data) * (self.config.augmentation_factor - 1.0))
        
        for _ in range(augment_count):
            # 隨機選擇原始數據點
            base_data = random.choice(original_data)
            
            # 創建增強版本
            augmented_point = LearningDataPoint(
                user_id=base_data.user_id,
                timestamp=base_data.timestamp + random.uniform(-3600, 3600),  # ±1小時
                learning_objective=base_data.learning_objective
            )
            
            # 特徵增強
            augmented_features = {}
            for key, value in base_data.personalization_features.items():
                if isinstance(value, (int, float)):
                    noise = random.gauss(0, self.config.noise_level * 0.5)
                    augmented_features[key] = max(0.0, min(1.0, value + noise))
                else:
                    augmented_features[key] = value
            
            augmented_point.personalization_features = augmented_features
            
            # 重新生成其他部分
            augmented_point.state = await self._generate_state(context, augmented_point)
            augmented_point.action = await self._generate_action(context, augmented_point)
            augmented_point.outcome = await self._generate_outcome(context, augmented_point)
            augmented_point.reward = await self._calculate_reward(context, augmented_point)
            
            augmented_point.metadata['augmented'] = True
            augmented_point.metadata['base_data_id'] = base_data.data_id
            
            augmented_data.append(augmented_point)
        
        return augmented_data
    
    async def _post_process_data(self, data: List[LearningDataPoint]) -> List[LearningDataPoint]:
        """數據後處理"""
        processed_data = []
        
        # 質量過濾
        for data_point in data:
            quality_score = await self._calculate_quality_score(data_point)
            if quality_score >= self.config.quality_threshold:
                processed_data.append(data_point)
        
        # 平衡學習目標
        if self.config.balance_objectives:
            processed_data = await self._balance_objectives(processed_data)
        
        # 添加負例
        if self.config.include_negative_examples:
            negative_examples = await self._generate_negative_examples(processed_data)
            processed_data.extend(negative_examples)
        
        # 更新質量指標
        await self._update_quality_metrics(processed_data)
        
        return processed_data
    
    async def _calculate_quality_score(self, data_point: LearningDataPoint) -> float:
        """計算數據質量分數"""
        score = 1.0
        
        # 完整性檢查
        required_fields = ['state', 'action', 'outcome', 'personalization_features']
        for field in required_fields:
            if not getattr(data_point, field):
                score *= 0.5
        
        # 合理性檢查
        if abs(data_point.reward) > 10.0:  # 極端獎勵
            score *= 0.7
        
        if data_point.outcome.get('return_rate', 0) > 1.0:  # 不合理的收益率
            score *= 0.6
        
        # 特徵質量
        features = data_point.personalization_features
        if features:
            invalid_features = sum(1 for v in features.values() 
                                 if isinstance(v, (int, float)) and (v < 0 or v > 1))
            if invalid_features > 0:
                score *= (1.0 - invalid_features / len(features) * 0.5)
        
        return max(0.0, min(1.0, score))
    
    async def _balance_objectives(self, data: List[LearningDataPoint]) -> List[LearningDataPoint]:
        """平衡學習目標"""
        # 統計各目標的數量
        objective_counts = defaultdict(list)
        for dp in data:
            objective_counts[dp.learning_objective].append(dp)
        
        if not objective_counts:
            return data
        
        # 計算目標數量
        target_count = min(len(data) // len(LearningObjective), 
                          max(len(samples) for samples in objective_counts.values()))
        
        balanced_data = []
        for objective, samples in objective_counts.items():
            # 如果樣本太多，隨機採樣
            if len(samples) > target_count:
                balanced_samples = random.sample(samples, target_count)
            else:
                balanced_samples = samples
            
            balanced_data.extend(balanced_samples)
        
        return balanced_data
    
    async def _generate_negative_examples(self, data: List[LearningDataPoint]) -> List[LearningDataPoint]:
        """生成負例"""
        negative_examples = []
        negative_count = int(len(data) * 0.1)  # 10%負例
        
        for _ in range(negative_count):
            base_data = random.choice(data)
            
            # 創建負例
            negative_example = LearningDataPoint(
                user_id=base_data.user_id,
                timestamp=base_data.timestamp,
                learning_objective=base_data.learning_objective,
                state=base_data.state.copy(),
                personalization_features=base_data.personalization_features.copy()
            )
            
            # 生成不當行為
            negative_example.action = await self._generate_negative_action(base_data)
            negative_example.outcome = await self._generate_negative_outcome(negative_example)
            negative_example.reward = -abs(base_data.reward) - 0.1  # 負獎勵
            
            negative_example.metadata['negative_example'] = True
            negative_examples.append(negative_example)
        
        return negative_examples
    
    async def _generate_negative_action(self, base_data: LearningDataPoint) -> Dict[str, Any]:
        """生成負面行為"""
        # 基於正面行為生成相反的不當行為
        base_action = base_data.action
        
        negative_action = base_action.copy()
        
        # 反向操作
        if base_action['type'] == 'buy':
            negative_action['type'] = 'sell'
        elif base_action['type'] == 'sell':
            negative_action['type'] = 'buy'
        
        # 過度自信
        negative_action['confidence'] = min(1.0, base_action.get('confidence', 0.5) + 0.3)
        
        # 忽略風險
        negative_action['risk_adjustment'] = 0.1
        
        return negative_action
    
    async def _generate_negative_outcome(self, data_point: LearningDataPoint) -> Dict[str, Any]:
        """生成負面結果"""
        outcome = {
            'return_rate': random.uniform(-0.5, -0.01),  # 負收益
            'execution_time': random.uniform(5.0, 30.0),  # 慢執行
            'slippage': random.uniform(0.02, 0.1),        # 高滑價
            'transaction_cost': random.uniform(50.0, 200.0), # 高成本
            'market_impact': random.uniform(0.001, 0.01),    # 高影響
            'success': False
        }
        
        outcome['absolute_return'] = (
            outcome['return_rate'] * 
            data_point.action.get('price', 100) * 
            data_point.action.get('quantity', 100)
        )
        
        return outcome
    
    async def _update_quality_metrics(self, data: List[LearningDataPoint]):
        """更新質量指標"""
        if not data:
            return
        
        # 基本統計
        rewards = [dp.reward for dp in data]
        self.quality_metrics['avg_reward'] = np.mean(rewards)
        self.quality_metrics['reward_std'] = np.std(rewards)
        
        # 目標分布
        objective_counts = defaultdict(int)
        for dp in data:
            objective_counts[dp.learning_objective.value] += 1
        
        self.quality_metrics['objective_distribution'] = dict(objective_counts)
        
        # 用戶分布
        user_counts = defaultdict(int)
        for dp in data:
            user_counts[dp.user_id] += 1
        
        self.quality_metrics['users_count'] = len(user_counts)
        self.quality_metrics['avg_samples_per_user'] = np.mean(list(user_counts.values()))
        
        # 特徵質量
        all_features = []
        for dp in data:
            if dp.personalization_features:
                all_features.extend(dp.feature_vector)
        
        if all_features:
            self.quality_metrics['feature_mean'] = np.mean(all_features)
            self.quality_metrics['feature_std'] = np.std(all_features)
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """獲取生成統計"""
        return {
            'generation_history': self.generation_history.copy(),
            'quality_metrics': self.quality_metrics.copy(),
            'cached_users': len(self.user_contexts),
            'cache_size': sum(len(data) for data in self.data_cache.values())
        }
    
    async def export_dataset(self, data: List[LearningDataPoint], 
                            filepath: str, format: str = 'json') -> bool:
        """導出數據集"""
        try:
            if format.lower() == 'json':
                dataset = {
                    'metadata': {
                        'generated_at': time.time(),
                        'samples_count': len(data),
                        'config': self.config.__dict__,
                        'quality_metrics': self.quality_metrics
                    },
                    'data': [
                        {
                            'data_id': dp.data_id,
                            'user_id': dp.user_id,
                            'timestamp': dp.timestamp,
                            'context': dp.context,
                            'state': dp.state,
                            'action': dp.action,
                            'outcome': dp.outcome,
                            'reward': dp.reward,
                            'learning_objective': dp.learning_objective.value,
                            'personalization_features': dp.personalization_features,
                            'feature_vector': dp.feature_vector,
                            'metadata': dp.metadata
                        }
                        for dp in data
                    ]
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(dataset, f, indent=2, ensure_ascii=False)
                
                logging.info(f"Dataset exported to {filepath}")
                return True
            
            else:
                logging.error(f"Unsupported export format: {format}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to export dataset: {e}")
            return False

# 工廠函數
def create_personalization_data_generator(config: Optional[DataGenerationConfig] = None) -> PersonalizationDataGenerator:
    """創建個人化數據生成器"""
    if config is None:
        config = DataGenerationConfig()
    
    return PersonalizationDataGenerator(config)