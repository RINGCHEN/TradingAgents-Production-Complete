#!/usr/bin/env python3
"""
User Profile Analyzer - 用戶行為分析器
天工 (TianGong) - 為ART系統提供用戶行為分析和建模

此模組提供：
1. UserProfileAnalyzer - 用戶檔案分析核心
2. UserBehaviorModel - 用戶行為模型
3. PreferenceProfile - 偏好檔案
4. TradingStyleAnalyzer - 交易風格分析器
5. BehaviorPattern - 行為模式識別
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import numpy as np
from collections import defaultdict, deque
import uuid
import math
import statistics
from scipy import stats
import scipy.cluster.hierarchy as sch
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

class BehaviorPattern(Enum):
    """行為模式"""
    CONSERVATIVE = "conservative"           # 保守型
    AGGRESSIVE = "aggressive"              # 激進型
    BALANCED = "balanced"                  # 平衡型
    MOMENTUM = "momentum"                  # 趨勢追隨型
    CONTRARIAN = "contrarian"             # 逆向投資型
    DAY_TRADER = "day_trader"             # 日內交易型
    SWING_TRADER = "swing_trader"         # 波段交易型
    LONG_TERM = "long_term"               # 長期投資型
    DIVERSIFIED = "diversified"           # 分散投資型
    CONCENTRATED = "concentrated"         # 集中投資型

class PersonalityMetrics(Enum):
    """性格指標"""
    RISK_TOLERANCE = "risk_tolerance"          # 風險承受度
    PATIENCE_LEVEL = "patience_level"          # 耐心水平
    DISCIPLINE_SCORE = "discipline_score"      # 紀律性
    EMOTIONAL_CONTROL = "emotional_control"    # 情緒控制
    DECISION_SPEED = "decision_speed"          # 決策速度
    LEARNING_RATE = "learning_rate"           # 學習速度
    ADAPTABILITY = "adaptability"             # 適應性
    CONFIDENCE_LEVEL = "confidence_level"     # 信心水平
    ANALYTICAL_THINKING = "analytical_thinking"  # 分析思維
    INTUITIVE_THINKING = "intuitive_thinking"    # 直覺思維

@dataclass
class UserBehaviorModel:
    """用戶行為模型"""
    user_id: str
    behavior_patterns: List[BehaviorPattern] = field(default_factory=list)
    personality_scores: Dict[PersonalityMetrics, float] = field(default_factory=dict)
    trading_frequency: float = 0.0           # 交易頻率
    average_holding_period: float = 0.0      # 平均持倉時間
    portfolio_turnover: float = 0.0          # 組合周轉率
    profit_taking_tendency: float = 0.0      # 獲利了結傾向
    loss_cutting_discipline: float = 0.0     # 止損紀律性
    market_timing_skill: float = 0.0         # 市場時機把握能力
    diversification_preference: float = 0.0  # 分散偏好
    leverage_usage: float = 0.0              # 槓桿使用
    reaction_to_volatility: float = 0.0      # 波動反應
    news_sensitivity: float = 0.0            # 消息敏感度
    peer_influence: float = 0.0              # 同儕影響
    overconfidence_bias: float = 0.0         # 過度自信偏誤
    herding_tendency: float = 0.0            # 從眾傾向
    loss_aversion: float = 0.0               # 損失厭惡
    model_confidence: float = 0.0            # 模型置信度
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PreferenceProfile:
    """偏好檔案"""
    user_id: str
    preferred_sectors: List[str] = field(default_factory=list)
    preferred_market_cap: str = "mixed"      # small, mid, large, mixed
    preferred_volatility_range: Tuple[float, float] = (0.1, 0.3)
    preferred_return_range: Tuple[float, float] = (0.05, 0.15)
    preferred_holding_period: str = "medium" # short, medium, long
    preferred_analysis_type: str = "mixed"   # fundamental, technical, mixed
    preferred_information_sources: List[str] = field(default_factory=list)
    risk_budget: float = 0.2                 # 風險預算
    return_target: float = 0.1               # 回報目標
    max_drawdown_tolerance: float = 0.15     # 最大回撤承受度
    preferred_trading_times: List[int] = field(default_factory=list)  # 小時
    preferred_rebalancing_frequency: str = "monthly"  # daily, weekly, monthly, quarterly
    esg_preference: float = 0.0              # ESG偏好
    dividend_preference: float = 0.0         # 股息偏好
    growth_vs_value: float = 0.5             # 成長vs價值偏好 (0=價值, 1=成長)
    domestic_vs_international: float = 0.7   # 國內vs國際偏好
    active_vs_passive: float = 0.6           # 主動vs被動偏好
    complexity_tolerance: float = 0.5        # 複雜度容忍度
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class TradingStyleAnalyzer:
    """交易風格分析器"""
    
    def __init__(self):
        self.style_signatures: Dict[BehaviorPattern, Dict[str, float]] = {
            BehaviorPattern.CONSERVATIVE: {
                'trading_frequency': 0.2, 'risk_tolerance': 0.3, 'volatility_preference': 0.2,
                'diversification': 0.8, 'leverage_usage': 0.1, 'holding_period': 0.8
            },
            BehaviorPattern.AGGRESSIVE: {
                'trading_frequency': 0.8, 'risk_tolerance': 0.8, 'volatility_preference': 0.8,
                'diversification': 0.3, 'leverage_usage': 0.7, 'holding_period': 0.2
            },
            BehaviorPattern.BALANCED: {
                'trading_frequency': 0.5, 'risk_tolerance': 0.5, 'volatility_preference': 0.5,
                'diversification': 0.6, 'leverage_usage': 0.3, 'holding_period': 0.5
            },
            BehaviorPattern.MOMENTUM: {
                'trading_frequency': 0.7, 'market_timing': 0.7, 'trend_following': 0.8,
                'news_sensitivity': 0.8, 'holding_period': 0.4
            },
            BehaviorPattern.CONTRARIAN: {
                'trading_frequency': 0.4, 'market_timing': 0.6, 'trend_following': 0.2,
                'contrarian_signals': 0.8, 'patience': 0.7
            },
            BehaviorPattern.DAY_TRADER: {
                'trading_frequency': 0.9, 'holding_period': 0.1, 'decision_speed': 0.9,
                'volatility_preference': 0.7, 'leverage_usage': 0.6
            },
            BehaviorPattern.SWING_TRADER: {
                'trading_frequency': 0.6, 'holding_period': 0.4, 'technical_analysis': 0.7,
                'market_timing': 0.6, 'volatility_preference': 0.6
            },
            BehaviorPattern.LONG_TERM: {
                'trading_frequency': 0.2, 'holding_period': 0.9, 'fundamental_analysis': 0.8,
                'patience': 0.8, 'diversification': 0.7
            }
        }
    
    async def analyze_trading_style(self, user_data: List[Dict[str, Any]]) -> List[BehaviorPattern]:
        """分析交易風格"""
        if not user_data:
            return []
        
        # 計算用戶特徵
        user_features = await self._calculate_user_features(user_data)
        
        # 計算與各種風格的相似度
        style_scores = {}
        for pattern, signature in self.style_signatures.items():
            score = await self._calculate_style_similarity(user_features, signature)
            style_scores[pattern] = score
        
        # 返回最匹配的風格
        sorted_styles = sorted(style_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 返回相似度超過閾值的風格
        threshold = 0.6
        matching_styles = [style for style, score in sorted_styles if score >= threshold]
        
        # 至少返回最匹配的一個風格
        if not matching_styles and sorted_styles:
            matching_styles = [sorted_styles[0][0]]
        
        return matching_styles[:3]  # 最多返回3個風格
    
    async def _calculate_user_features(self, user_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算用戶特徵"""
        features = {}
        
        if not user_data:
            return features
        
        # 交易頻率
        time_span = max(d.get('timestamp', 0) for d in user_data) - min(d.get('timestamp', 0) for d in user_data)
        if time_span > 0:
            features['trading_frequency'] = len(user_data) / (time_span / 86400)  # 每天交易次數
        else:
            features['trading_frequency'] = 0
        
        # 持倉時間
        holding_periods = []
        for data in user_data:
            if 'holding_period' in data:
                holding_periods.append(data['holding_period'])
        
        if holding_periods:
            avg_holding = np.mean(holding_periods)
            # 標準化到0-1範圍 (假設最長持倉365天)
            features['holding_period'] = min(1.0, avg_holding / 365.0)
        
        # 風險承受度
        returns = [d.get('return_rate', 0) for d in user_data if 'return_rate' in d]
        if returns:
            volatility = np.std(returns)
            features['risk_tolerance'] = min(1.0, volatility / 0.5)  # 標準化
            features['volatility_preference'] = features['risk_tolerance']
        
        # 多樣化程度
        symbols = set(d.get('symbol', '') for d in user_data if 'symbol' in d)
        if len(user_data) > 0:
            features['diversification'] = len(symbols) / min(len(user_data), 20)
        
        # 槓桿使用
        leverage_usage = [d.get('leverage', 0) for d in user_data if 'leverage' in d]
        if leverage_usage:
            features['leverage_usage'] = min(1.0, np.mean(leverage_usage) / 3.0)
        
        # 市場時機把握
        if returns:
            # 計算夏普比率作為市場時機指標
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            if std_return > 0:
                sharpe_ratio = mean_return / std_return
                features['market_timing'] = min(1.0, max(0.0, (sharpe_ratio + 2) / 4))
        
        # 消息敏感度（基於交易時機與市場事件的相關性）
        timestamps = [d.get('timestamp', 0) for d in user_data]
        if timestamps:
            # 簡化計算：交易集中度
            hourly_trades = defaultdict(int)
            for ts in timestamps:
                hour = int((ts % 86400) / 3600)
                hourly_trades[hour] += 1
            
            if hourly_trades:
                max_trades = max(hourly_trades.values())
                total_trades = sum(hourly_trades.values())
                features['news_sensitivity'] = max_trades / total_trades if total_trades > 0 else 0
        
        # 技術分析vs基本面分析偏好
        technical_indicators = sum(1 for d in user_data if d.get('analysis_type') == 'technical')
        fundamental_indicators = sum(1 for d in user_data if d.get('analysis_type') == 'fundamental')
        total_indicators = technical_indicators + fundamental_indicators
        
        if total_indicators > 0:
            features['technical_analysis'] = technical_indicators / total_indicators
            features['fundamental_analysis'] = fundamental_indicators / total_indicators
        
        # 趨勢跟隨vs逆向投資
        trend_following_trades = sum(1 for d in user_data if d.get('strategy_type') == 'momentum')
        contrarian_trades = sum(1 for d in user_data if d.get('strategy_type') == 'contrarian')
        strategy_trades = trend_following_trades + contrarian_trades
        
        if strategy_trades > 0:
            features['trend_following'] = trend_following_trades / strategy_trades
            features['contrarian_signals'] = contrarian_trades / strategy_trades
        
        # 決策速度
        decision_times = [d.get('decision_time', 0) for d in user_data if 'decision_time' in d]
        if decision_times:
            avg_decision_time = np.mean(decision_times)
            # 假設快速決策在1分鐘內，標準化到0-1
            features['decision_speed'] = max(0.0, 1.0 - avg_decision_time / 60.0)
        
        # 耐心水平（基於持倉時間和交易頻率）
        if 'holding_period' in features and 'trading_frequency' in features:
            features['patience'] = features['holding_period'] * (1 - features['trading_frequency'])
        
        return features
    
    async def _calculate_style_similarity(self, user_features: Dict[str, float], 
                                        style_signature: Dict[str, float]) -> float:
        """計算風格相似度"""
        similarities = []
        
        for feature, target_value in style_signature.items():
            if feature in user_features:
                user_value = user_features[feature]
                # 計算相似度（1 - 差異）
                similarity = 1.0 - abs(user_value - target_value)
                similarities.append(similarity)
        
        # 返回平均相似度
        return np.mean(similarities) if similarities else 0.0

class UserProfileAnalyzer:
    """用戶檔案分析器"""
    
    def __init__(self):
        self.trading_style_analyzer = TradingStyleAnalyzer()
        self.user_profiles: Dict[str, UserBehaviorModel] = {}
        self.preference_profiles: Dict[str, PreferenceProfile] = {}
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        logging.info("UserProfileAnalyzer initialized")
    
    async def analyze_user_behavior(self, user_id: str, 
                                   historical_data: List[Dict[str, Any]]) -> UserBehaviorModel:
        """分析用戶行為"""
        logging.info(f"Analyzing behavior for user {user_id}")
        
        # 創建用戶行為模型
        behavior_model = UserBehaviorModel(user_id=user_id)
        
        if not historical_data:
            logging.warning(f"No historical data for user {user_id}")
            self.user_profiles[user_id] = behavior_model
            return behavior_model
        
        # 分析交易風格
        behavior_model.behavior_patterns = await self.trading_style_analyzer.analyze_trading_style(
            historical_data
        )
        
        # 計算性格指標
        behavior_model.personality_scores = await self._calculate_personality_scores(historical_data)
        
        # 計算交易統計指標
        trading_stats = await self._calculate_trading_statistics(historical_data)
        for key, value in trading_stats.items():
            setattr(behavior_model, key, value)
        
        # 計算行為偏誤
        behavioral_biases = await self._analyze_behavioral_biases(historical_data)
        for key, value in behavioral_biases.items():
            setattr(behavior_model, key, value)
        
        # 計算模型置信度
        behavior_model.model_confidence = await self._calculate_model_confidence(
            historical_data, behavior_model
        )
        
        behavior_model.last_updated = time.time()
        
        # 緩存結果
        self.user_profiles[user_id] = behavior_model
        
        logging.info(f"Behavior analysis completed for user {user_id}")
        return behavior_model
    
    async def _calculate_personality_scores(self, historical_data: List[Dict[str, Any]]) -> Dict[PersonalityMetrics, float]:
        """計算性格指標"""
        scores = {}
        
        if not historical_data:
            return scores
        
        returns = [d.get('return_rate', 0) for d in historical_data if 'return_rate' in d]
        
        # 風險承受度
        if returns:
            volatility = np.std(returns)
            scores[PersonalityMetrics.RISK_TOLERANCE] = min(1.0, volatility / 0.3)
        
        # 耐心水平
        holding_periods = [d.get('holding_period', 0) for d in historical_data if 'holding_period' in d]
        if holding_periods:
            avg_holding = np.mean(holding_periods)
            scores[PersonalityMetrics.PATIENCE_LEVEL] = min(1.0, avg_holding / 30.0)  # 30天為滿分
        
        # 紀律性（止損執行率）
        stop_losses = [d.get('stop_loss_executed', False) for d in historical_data]
        if stop_losses:
            discipline_rate = sum(stop_losses) / len(stop_losses)
            scores[PersonalityMetrics.DISCIPLINE_SCORE] = discipline_rate
        
        # 情緒控制（回撤期間的交易行為）
        drawdown_trades = [d for d in historical_data if d.get('during_drawdown', False)]
        if drawdown_trades and len(drawdown_trades) < len(historical_data):
            # 回撤期間的交易頻率相對正常期間
            normal_frequency = (len(historical_data) - len(drawdown_trades)) / max(1, len(historical_data) - len(drawdown_trades))
            drawdown_frequency = len(drawdown_trades) / max(1, len(drawdown_trades))
            
            if normal_frequency > 0:
                emotion_control = 1.0 - abs(drawdown_frequency - normal_frequency) / normal_frequency
                scores[PersonalityMetrics.EMOTIONAL_CONTROL] = max(0.0, min(1.0, emotion_control))
        
        # 決策速度
        decision_times = [d.get('decision_time', 0) for d in historical_data if 'decision_time' in d]
        if decision_times:
            avg_decision_time = np.mean(decision_times)
            # 快速決策得高分（假設1分鐘內為滿分）
            scores[PersonalityMetrics.DECISION_SPEED] = max(0.0, 1.0 - avg_decision_time / 60.0)
        
        # 學習速度（基於表現改善）
        if len(returns) >= 10:
            # 比較前半和後半的表現
            half_point = len(returns) // 2
            early_returns = returns[:half_point]
            late_returns = returns[half_point:]
            
            early_avg = np.mean(early_returns)
            late_avg = np.mean(late_returns)
            
            improvement = late_avg - early_avg
            scores[PersonalityMetrics.LEARNING_RATE] = min(1.0, max(0.0, improvement + 0.5))
        
        # 適應性（不同市場條件下的表現一致性）
        market_conditions = defaultdict(list)
        for d in historical_data:
            condition = d.get('market_condition', 'normal')
            return_rate = d.get('return_rate', 0)
            market_conditions[condition].append(return_rate)
        
        if len(market_conditions) > 1:
            condition_performances = []
            for condition, condition_returns in market_conditions.items():
                if condition_returns:
                    condition_performances.append(np.mean(condition_returns))
            
            if condition_performances:
                performance_std = np.std(condition_performances)
                # 標準差越小，適應性越強
                scores[PersonalityMetrics.ADAPTABILITY] = max(0.0, 1.0 - performance_std)
        
        # 信心水平（基於交易規模和頻率）
        trade_sizes = [d.get('trade_size', 0) for d in historical_data if 'trade_size' in d]
        if trade_sizes:
            avg_size = np.mean(trade_sizes)
            size_std = np.std(trade_sizes)
            
            # 一致的較大交易規模表示高信心
            if avg_size > 0:
                confidence = avg_size / (avg_size + size_std) if size_std > 0 else 1.0
                scores[PersonalityMetrics.CONFIDENCE_LEVEL] = min(1.0, confidence)
        
        # 分析思維（使用基本面分析的比例）
        analysis_types = [d.get('analysis_type', 'mixed') for d in historical_data]
        if analysis_types:
            analytical_ratio = sum(1 for a in analysis_types if a == 'fundamental') / len(analysis_types)
            scores[PersonalityMetrics.ANALYTICAL_THINKING] = analytical_ratio
        
        # 直覺思維（使用技術面分析或直覺決策的比例）
        if analysis_types:
            intuitive_ratio = sum(1 for a in analysis_types if a in ['technical', 'intuitive']) / len(analysis_types)
            scores[PersonalityMetrics.INTUITIVE_THINKING] = intuitive_ratio
        
        return scores
    
    async def _calculate_trading_statistics(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """計算交易統計指標"""
        stats = {}
        
        if not historical_data:
            return stats
        
        # 交易頻率（每天交易次數）
        timestamps = [d.get('timestamp', 0) for d in historical_data]
        if timestamps:
            time_span = max(timestamps) - min(timestamps)
            if time_span > 0:
                stats['trading_frequency'] = len(historical_data) / (time_span / 86400)
            else:
                stats['trading_frequency'] = 0.0
        
        # 平均持倉時間
        holding_periods = [d.get('holding_period', 0) for d in historical_data if 'holding_period' in d]
        if holding_periods:
            stats['average_holding_period'] = np.mean(holding_periods)
        
        # 組合周轉率
        trade_values = [d.get('trade_value', 0) for d in historical_data if 'trade_value' in d]
        portfolio_values = [d.get('portfolio_value', 0) for d in historical_data if 'portfolio_value' in d]
        
        if trade_values and portfolio_values:
            total_trade_value = sum(trade_values)
            avg_portfolio_value = np.mean(portfolio_values)
            
            if avg_portfolio_value > 0:
                stats['portfolio_turnover'] = total_trade_value / avg_portfolio_value
        
        # 獲利了結傾向
        profitable_trades = [d for d in historical_data if d.get('return_rate', 0) > 0]
        losing_trades = [d for d in historical_data if d.get('return_rate', 0) < 0]
        
        if profitable_trades and losing_trades:
            profit_holding = [d.get('holding_period', 0) for d in profitable_trades]
            loss_holding = [d.get('holding_period', 0) for d in losing_trades]
            
            if profit_holding and loss_holding:
                avg_profit_holding = np.mean(profit_holding)
                avg_loss_holding = np.mean(loss_holding)
                
                if avg_profit_holding + avg_loss_holding > 0:
                    # 獲利了結傾向：獲利持倉時間相對較短
                    stats['profit_taking_tendency'] = avg_loss_holding / (avg_profit_holding + avg_loss_holding)
        
        # 止損紀律性
        stop_loss_executions = [d.get('stop_loss_executed', False) for d in historical_data]
        if stop_loss_executions:
            stats['loss_cutting_discipline'] = sum(stop_loss_executions) / len(stop_loss_executions)
        
        # 市場時機把握能力
        returns = [d.get('return_rate', 0) for d in historical_data if 'return_rate' in d]
        if returns:
            avg_return = np.mean(returns)
            return_std = np.std(returns)
            
            if return_std > 0:
                # 夏普比率作為市場時機指標
                sharpe_ratio = avg_return / return_std
                stats['market_timing_skill'] = min(1.0, max(0.0, (sharpe_ratio + 1) / 2))
        
        # 分散偏好
        symbols = [d.get('symbol', '') for d in historical_data if d.get('symbol')]
        if symbols:
            unique_symbols = len(set(symbols))
            total_trades = len(symbols)
            stats['diversification_preference'] = unique_symbols / total_trades
        
        # 槓桿使用
        leverage_data = [d.get('leverage', 1.0) for d in historical_data if 'leverage' in d]
        if leverage_data:
            avg_leverage = np.mean(leverage_data)
            stats['leverage_usage'] = min(1.0, (avg_leverage - 1.0) / 2.0)  # 標準化到0-1
        
        # 波動反應
        volatilities = [d.get('market_volatility', 0) for d in historical_data if 'market_volatility' in d]
        trade_sizes = [d.get('trade_size', 0) for d in historical_data if 'trade_size' in d]
        
        if volatilities and trade_sizes and len(volatilities) == len(trade_sizes):
            # 計算波動率與交易規模的相關性
            correlation = np.corrcoef(volatilities, trade_sizes)[0, 1]
            if not np.isnan(correlation):
                stats['reaction_to_volatility'] = abs(correlation)
        
        # 消息敏感度
        news_driven_trades = [d for d in historical_data if d.get('news_driven', False)]
        if historical_data:
            stats['news_sensitivity'] = len(news_driven_trades) / len(historical_data)
        
        # 同儕影響
        peer_influenced_trades = [d for d in historical_data if d.get('peer_influenced', False)]
        if historical_data:
            stats['peer_influence'] = len(peer_influenced_trades) / len(historical_data)
        
        return stats
    
    async def _analyze_behavioral_biases(self, historical_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """分析行為偏誤"""
        biases = {}
        
        if not historical_data:
            return biases
        
        # 過度自信偏誤
        confidence_scores = [d.get('confidence_score', 0.5) for d in historical_data if 'confidence_score' in d]
        actual_outcomes = [d.get('return_rate', 0) for d in historical_data if 'return_rate' in d]
        
        if confidence_scores and actual_outcomes and len(confidence_scores) == len(actual_outcomes):
            # 計算預期與實際結果的差異
            overconfidence_indicators = []
            for confidence, outcome in zip(confidence_scores, actual_outcomes):
                # 高信心但負結果表示過度自信
                if confidence > 0.7 and outcome < 0:
                    overconfidence_indicators.append(1.0)
                elif confidence < 0.3 and outcome > 0:
                    overconfidence_indicators.append(0.0)  # 保守但成功
                else:
                    overconfidence_indicators.append(0.5)
            
            if overconfidence_indicators:
                biases['overconfidence_bias'] = np.mean(overconfidence_indicators)
        
        # 從眾傾向
        market_trends = [d.get('market_trend', 'neutral') for d in historical_data if 'market_trend' in d]
        user_actions = [d.get('action_type', 'hold') for d in historical_data if 'action_type' in d]
        
        if market_trends and user_actions and len(market_trends) == len(user_actions):
            herding_count = 0
            total_count = 0
            
            for trend, action in zip(market_trends, user_actions):
                total_count += 1
                # 牛市買入或熊市賣出表示從眾
                if (trend == 'bullish' and action == 'buy') or (trend == 'bearish' and action == 'sell'):
                    herding_count += 1
            
            if total_count > 0:
                biases['herding_tendency'] = herding_count / total_count
        
        # 損失厭惡
        profits = [d.get('return_rate', 0) for d in historical_data if d.get('return_rate', 0) > 0]
        losses = [abs(d.get('return_rate', 0)) for d in historical_data if d.get('return_rate', 0) < 0]
        
        if profits and losses:
            avg_profit = np.mean(profits)
            avg_loss = np.mean(losses)
            
            if avg_profit > 0:
                # 損失厭惡係數：損失的心理影響是收益的幾倍
                loss_aversion_ratio = avg_loss / avg_profit
                biases['loss_aversion'] = min(1.0, loss_aversion_ratio / 2.5)  # 標準化
        
        return biases
    
    async def _calculate_model_confidence(self, historical_data: List[Dict[str, Any]], 
                                        behavior_model: UserBehaviorModel) -> float:
        """計算模型置信度"""
        confidence_factors = []
        
        # 數據量充足性
        data_sufficiency = min(1.0, len(historical_data) / 100)  # 100筆交易為滿分
        confidence_factors.append(data_sufficiency)
        
        # 數據時間跨度
        timestamps = [d.get('timestamp', 0) for d in historical_data if 'timestamp' in d]
        if timestamps:
            time_span = max(timestamps) - min(timestamps)
            time_coverage = min(1.0, time_span / (365 * 86400))  # 一年為滿分
            confidence_factors.append(time_coverage)
        
        # 行為一致性
        if behavior_model.personality_scores:
            score_variance = np.var(list(behavior_model.personality_scores.values()))
            consistency = max(0.0, 1.0 - score_variance)  # 方差越小，一致性越高
            confidence_factors.append(consistency)
        
        # 交易多樣性
        symbols = set(d.get('symbol', '') for d in historical_data if d.get('symbol'))
        diversity = min(1.0, len(symbols) / 20)  # 20個不同標的為滿分
        confidence_factors.append(diversity)
        
        # 返回平均置信度
        return np.mean(confidence_factors) if confidence_factors else 0.5
    
    async def create_preference_profile(self, user_id: str, 
                                      historical_data: List[Dict[str, Any]],
                                      explicit_preferences: Dict[str, Any] = None) -> PreferenceProfile:
        """創建偏好檔案"""
        logging.info(f"Creating preference profile for user {user_id}")
        
        profile = PreferenceProfile(user_id=user_id)
        
        if explicit_preferences:
            # 使用明確偏好設置
            for key, value in explicit_preferences.items():
                if hasattr(profile, key):
                    setattr(profile, key, value)
        
        if historical_data:
            # 從歷史數據推斷偏好
            inferred_preferences = await self._infer_preferences_from_data(historical_data)
            for key, value in inferred_preferences.items():
                if hasattr(profile, key) and explicit_preferences.get(key) is None:
                    setattr(profile, key, value)
        
        profile.updated_at = time.time()
        
        # 緩存結果
        self.preference_profiles[user_id] = profile
        
        logging.info(f"Preference profile created for user {user_id}")
        return profile
    
    async def _infer_preferences_from_data(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """從數據推斷偏好"""
        preferences = {}
        
        # 偏好的股票類型
        symbols = [d.get('symbol', '') for d in historical_data if d.get('symbol')]
        sectors = [d.get('sector', '') for d in historical_data if d.get('sector')]
        market_caps = [d.get('market_cap', 'mixed') for d in historical_data if d.get('market_cap')]
        
        if sectors:
            # 統計最常交易的行業
            sector_counts = defaultdict(int)
            for sector in sectors:
                sector_counts[sector] += 1
            
            # 取前5個最常交易的行業
            top_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            preferences['preferred_sectors'] = [sector for sector, _ in top_sectors]
        
        if market_caps:
            # 統計最偏好的市值類型
            market_cap_counts = defaultdict(int)
            for cap in market_caps:
                market_cap_counts[cap] += 1
            
            most_common_cap = max(market_cap_counts.items(), key=lambda x: x[1])
            preferences['preferred_market_cap'] = most_common_cap[0]
        
        # 波動性偏好
        volatilities = [d.get('volatility', 0) for d in historical_data if 'volatility' in d]
        if volatilities:
            vol_range = (np.percentile(volatilities, 25), np.percentile(volatilities, 75))
            preferences['preferred_volatility_range'] = vol_range
        
        # 回報範圍偏好
        returns = [d.get('return_rate', 0) for d in historical_data if 'return_rate' in d]
        if returns:
            positive_returns = [r for r in returns if r > 0]
            if positive_returns:
                return_range = (np.percentile(positive_returns, 25), np.percentile(positive_returns, 75))
                preferences['preferred_return_range'] = return_range
        
        # 持倉期間偏好
        holding_periods = [d.get('holding_period', 0) for d in historical_data if 'holding_period' in d]
        if holding_periods:
            avg_holding = np.mean(holding_periods)
            if avg_holding < 1:
                preferences['preferred_holding_period'] = 'short'
            elif avg_holding < 30:
                preferences['preferred_holding_period'] = 'medium'
            else:
                preferences['preferred_holding_period'] = 'long'
        
        # 分析類型偏好
        analysis_types = [d.get('analysis_type', 'mixed') for d in historical_data if d.get('analysis_type')]
        if analysis_types:
            type_counts = defaultdict(int)
            for atype in analysis_types:
                type_counts[atype] += 1
            
            if type_counts:
                preferred_type = max(type_counts.items(), key=lambda x: x[1])
                preferences['preferred_analysis_type'] = preferred_type[0]
        
        # 交易時間偏好
        timestamps = [d.get('timestamp', 0) for d in historical_data if 'timestamp' in d]
        if timestamps:
            hours = [(int(ts) % 86400) // 3600 for ts in timestamps]  # 提取小時
            hour_counts = defaultdict(int)
            for hour in hours:
                hour_counts[hour] += 1
            
            # 取交易頻率最高的時段
            top_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            preferences['preferred_trading_times'] = [hour for hour, _ in top_hours]
        
        # 風險預算
        returns = [d.get('return_rate', 0) for d in historical_data if 'return_rate' in d]
        if returns:
            return_std = np.std(returns)
            preferences['risk_budget'] = min(0.5, return_std)  # 最大50%
        
        # 回報目標
        if returns:
            positive_returns = [r for r in returns if r > 0]
            if positive_returns:
                preferences['return_target'] = np.mean(positive_returns)
        
        # 最大回撤容忍度
        if returns:
            cumulative_returns = np.cumsum(returns)
            peak = np.maximum.accumulate(cumulative_returns)
            drawdowns = (peak - cumulative_returns) / np.maximum(peak, 1e-6)
            
            if len(drawdowns) > 0:
                max_drawdown = np.max(drawdowns)
                preferences['max_drawdown_tolerance'] = min(1.0, max_drawdown * 1.5)
        
        return preferences
    
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶洞察"""
        insights = {
            'user_id': user_id,
            'behavior_model': None,
            'preference_profile': None,
            'risk_assessment': {},
            'trading_style_summary': {},
            'improvement_suggestions': [],
            'personality_insights': {}
        }
        
        # 獲取行為模型
        if user_id in self.user_profiles:
            insights['behavior_model'] = self.user_profiles[user_id]
            
            # 生成交易風格總結
            patterns = insights['behavior_model'].behavior_patterns
            if patterns:
                insights['trading_style_summary'] = {
                    'primary_style': patterns[0].value,
                    'secondary_styles': [p.value for p in patterns[1:]],
                    'style_confidence': insights['behavior_model'].model_confidence
                }
        
        # 獲取偏好檔案
        if user_id in self.preference_profiles:
            insights['preference_profile'] = self.preference_profiles[user_id]
        
        # 風險評估
        if insights['behavior_model']:
            behavior = insights['behavior_model']
            risk_score = behavior.personality_scores.get(PersonalityMetrics.RISK_TOLERANCE, 0.5)
            
            insights['risk_assessment'] = {
                'risk_tolerance_score': risk_score,
                'risk_category': self._categorize_risk_level(risk_score),
                'volatility_comfort': behavior.reaction_to_volatility,
                'leverage_tendency': behavior.leverage_usage,
                'diversification_level': behavior.diversification_preference
            }
        
        # 性格洞察
        if insights['behavior_model'] and insights['behavior_model'].personality_scores:
            personality_scores = insights['behavior_model'].personality_scores
            
            # 找出最突出的性格特徵
            sorted_traits = sorted(personality_scores.items(), key=lambda x: x[1], reverse=True)
            
            insights['personality_insights'] = {
                'strongest_traits': [(trait.value, score) for trait, score in sorted_traits[:3]],
                'areas_for_development': [(trait.value, score) for trait, score in sorted_traits[-2:]],
                'overall_profile': await self._generate_personality_summary(personality_scores)
            }
        
        # 改進建議
        insights['improvement_suggestions'] = await self._generate_improvement_suggestions(
            insights['behavior_model'], insights['preference_profile']
        )
        
        return insights
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """分類風險水平"""
        if risk_score < 0.3:
            return "Conservative"
        elif risk_score < 0.7:
            return "Moderate"
        else:
            return "Aggressive"
    
    async def _generate_personality_summary(self, personality_scores: Dict[PersonalityMetrics, float]) -> str:
        """生成性格總結"""
        if not personality_scores:
            return "Insufficient data for personality analysis"
        
        summaries = []
        
        # 風險承受度
        risk_score = personality_scores.get(PersonalityMetrics.RISK_TOLERANCE, 0.5)
        if risk_score < 0.3:
            summaries.append("conservative investor with low risk tolerance")
        elif risk_score > 0.7:
            summaries.append("aggressive investor comfortable with high risk")
        else:
            summaries.append("balanced investor with moderate risk tolerance")
        
        # 決策風格
        analytical = personality_scores.get(PersonalityMetrics.ANALYTICAL_THINKING, 0.5)
        intuitive = personality_scores.get(PersonalityMetrics.INTUITIVE_THINKING, 0.5)
        
        if analytical > intuitive + 0.2:
            summaries.append("analytical decision maker who relies on data and research")
        elif intuitive > analytical + 0.2:
            summaries.append("intuitive decision maker who trusts instincts and market feel")
        else:
            summaries.append("balanced decision maker using both analysis and intuition")
        
        # 耐心水平
        patience = personality_scores.get(PersonalityMetrics.PATIENCE_LEVEL, 0.5)
        if patience > 0.7:
            summaries.append("patient long-term investor")
        elif patience < 0.3:
            summaries.append("action-oriented short-term trader")
        
        # 情緒控制
        emotional_control = personality_scores.get(PersonalityMetrics.EMOTIONAL_CONTROL, 0.5)
        if emotional_control > 0.7:
            summaries.append("excellent emotional discipline during market volatility")
        elif emotional_control < 0.3:
            summaries.append("may benefit from improved emotional control strategies")
        
        return "This user is a " + ", ".join(summaries)
    
    async def _generate_improvement_suggestions(self, behavior_model: Optional[UserBehaviorModel],
                                             preference_profile: Optional[PreferenceProfile]) -> List[str]:
        """生成改進建議"""
        suggestions = []
        
        if not behavior_model:
            return ["Insufficient behavioral data for personalized suggestions"]
        
        # 基於性格分析的建議
        personality = behavior_model.personality_scores
        
        # 風險管理建議
        risk_tolerance = personality.get(PersonalityMetrics.RISK_TOLERANCE, 0.5)
        discipline = personality.get(PersonalityMetrics.DISCIPLINE_SCORE, 0.5)
        
        if risk_tolerance > 0.7 and discipline < 0.5:
            suggestions.append("Consider implementing stricter stop-loss rules to manage high-risk positions")
        
        if risk_tolerance < 0.3 and behavior_model.diversification_preference < 0.5:
            suggestions.append("Increase portfolio diversification to better match your conservative risk profile")
        
        # 情緒控制建議
        emotional_control = personality.get(PersonalityMetrics.EMOTIONAL_CONTROL, 0.5)
        if emotional_control < 0.5:
            suggestions.append("Practice mindfulness and systematic decision-making during market volatility")
        
        # 學習速度建議
        learning_rate = personality.get(PersonalityMetrics.LEARNING_RATE, 0.5)
        if learning_rate < 0.4:
            suggestions.append("Keep a trading journal to accelerate learning from past decisions")
        
        # 決策速度建議
        decision_speed = personality.get(PersonalityMetrics.DECISION_SPEED, 0.5)
        patience = personality.get(PersonalityMetrics.PATIENCE_LEVEL, 0.5)
        
        if decision_speed > 0.8 and patience < 0.3:
            suggestions.append("Consider slowing down decision-making process to avoid impulsive trades")
        
        # 基於交易模式的建議
        if behavior_model.trading_frequency > 0.8:
            suggestions.append("High trading frequency may lead to increased costs - consider position sizing optimization")
        
        if behavior_model.profit_taking_tendency > 0.7:
            suggestions.append("You tend to cut profits short - consider letting winning positions run longer")
        
        if behavior_model.loss_cutting_discipline < 0.4:
            suggestions.append("Improve loss-cutting discipline with predetermined exit strategies")
        
        # 偏好相關建議
        if preference_profile:
            if preference_profile.preferred_holding_period == 'short' and risk_tolerance < 0.4:
                suggestions.append("Short-term trading may not suit your conservative risk profile - consider longer timeframes")
        
        return suggestions[:5]  # 限制建議數量
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """獲取分析總結"""
        return {
            'total_users_analyzed': len(self.user_profiles),
            'users_with_preferences': len(self.preference_profiles),
            'cache_size': len(self.analysis_cache),
            'most_common_patterns': self._get_pattern_statistics(),
            'average_model_confidence': self._calculate_average_confidence()
        }
    
    def _get_pattern_statistics(self) -> Dict[str, int]:
        """獲取模式統計"""
        pattern_counts = defaultdict(int)
        
        for profile in self.user_profiles.values():
            for pattern in profile.behavior_patterns:
                pattern_counts[pattern.value] += 1
        
        return dict(pattern_counts)
    
    def _calculate_average_confidence(self) -> float:
        """計算平均模型置信度"""
        if not self.user_profiles:
            return 0.0
        
        confidences = [profile.model_confidence for profile in self.user_profiles.values()]
        return np.mean(confidences) if confidences else 0.0

# 工廠函數
def create_user_profile_analyzer() -> UserProfileAnalyzer:
    """創建用戶檔案分析器"""
    return UserProfileAnalyzer()