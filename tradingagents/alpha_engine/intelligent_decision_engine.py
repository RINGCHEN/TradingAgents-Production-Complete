#!/usr/bin/env python3
"""
智能決策引擎
Intelligent Decision Engine - GPT-OSS整合任務4.1.3

智能決策引擎是階段4智能化增強的核心組件，通過決策樹優化和自動交易信號生成，
實現高度自動化的投資決策和執行能力。

主要功能：
1. 智能決策框架 - 多因子決策模型
2. 自動交易信號生成 - 買賣時機智能判斷
3. 投資組合再平衡 - 動態權重調整
4. 風險管理自動化 - 止損止盈智能設置
5. 資金管理系統 - 倉位控制和風險分散
6. 決策執行監控 - 實時決策效果追蹤
"""

import os
import json
import logging
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, validator
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict, deque
import pickle
import warnings
from abc import ABC, abstractmethod
import math

# 引入已有的組件
from .alpha_engine_core import AlphaInsight, AlphaInsightType, AlphaInsightPriority, MarketDirection, TimeHorizon
from .adaptive_learning_engine import AdaptiveLearningEngine, Experience, MarketState, Action
from .predictive_analytics_platform import PredictionResult, PredictionType, PredictionHorizon

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 忽略警告
warnings.filterwarnings("ignore")


class DecisionType(str, Enum):
    """決策類型枚舉"""
    BUY = "buy"                         # 買入
    SELL = "sell"                       # 賣出
    HOLD = "hold"                       # 持有
    REBALANCE = "rebalance"            # 再平衡
    HEDGE = "hedge"                     # 對沖
    STOP_LOSS = "stop_loss"            # 止損
    TAKE_PROFIT = "take_profit"        # 止盈
    INCREASE_POSITION = "increase_position"  # 加倉
    REDUCE_POSITION = "reduce_position"      # 減倉
    CLOSE_POSITION = "close_position"        # 平倉


class DecisionConfidence(str, Enum):
    """決策信心等級枚舉"""
    VERY_HIGH = "very_high"            # 極高信心 (90-100%)
    HIGH = "high"                      # 高信心 (75-90%)
    MEDIUM = "medium"                  # 中等信心 (60-75%)
    LOW = "low"                        # 低信心 (40-60%)
    VERY_LOW = "very_low"              # 很低信心 (0-40%)


class RiskLevel(str, Enum):
    """風險等級枚舉"""
    VERY_LOW = "very_low"              # 極低風險
    LOW = "low"                        # 低風險
    MEDIUM = "medium"                  # 中等風險
    HIGH = "high"                      # 高風險
    VERY_HIGH = "very_high"            # 極高風險


class ExecutionUrgency(str, Enum):
    """執行緊急程度枚舉"""
    IMMEDIATE = "immediate"            # 立即執行
    HIGH = "high"                      # 高優先級
    NORMAL = "normal"                  # 正常優先級
    LOW = "low"                        # 低優先級
    SCHEDULED = "scheduled"            # 定時執行


class PositionSizingMethod(str, Enum):
    """倉位規模方法枚舉"""
    FIXED_AMOUNT = "fixed_amount"      # 固定金額
    FIXED_PERCENTAGE = "fixed_percentage"  # 固定百分比
    KELLY_CRITERION = "kelly_criterion"    # 凱利公式
    RISK_PARITY = "risk_parity"           # 風險平價
    VOLATILITY_ADJUSTED = "volatility_adjusted"  # 波動率調整
    ADAPTIVE = "adaptive"                 # 自適應


@dataclass
class MarketCondition:
    """市場條件類"""
    timestamp: datetime
    market_regime: str  # 'bull', 'bear', 'sideways', 'volatile'
    volatility_level: float
    liquidity_level: float
    sentiment_score: float
    trend_strength: float
    support_resistance: Dict[str, float]
    economic_indicators: Dict[str, float]
    sector_performance: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'market_regime': self.market_regime,
            'volatility_level': self.volatility_level,
            'liquidity_level': self.liquidity_level,
            'sentiment_score': self.sentiment_score,
            'trend_strength': self.trend_strength,
            'support_resistance': self.support_resistance,
            'economic_indicators': self.economic_indicators,
            'sector_performance': self.sector_performance
        }


@dataclass
class Portfolio:
    """投資組合類"""
    portfolio_id: str
    total_value: Decimal
    cash_balance: Decimal
    positions: Dict[str, Dict[str, Any]]
    target_allocations: Dict[str, float]
    risk_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    last_updated: datetime
    
    def get_position_value(self, symbol: str) -> Decimal:
        """獲取持倉價值"""
        if symbol not in self.positions:
            return Decimal('0')
        
        position = self.positions[symbol]
        return Decimal(str(position.get('quantity', 0))) * Decimal(str(position.get('current_price', 0)))
    
    def get_allocation(self, symbol: str) -> float:
        """獲取資產配置比例"""
        position_value = float(self.get_position_value(symbol))
        total_value = float(self.total_value)
        
        return position_value / total_value if total_value > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'portfolio_id': self.portfolio_id,
            'total_value': float(self.total_value),
            'cash_balance': float(self.cash_balance),
            'positions': self.positions,
            'target_allocations': self.target_allocations,
            'risk_metrics': self.risk_metrics,
            'performance_metrics': self.performance_metrics,
            'last_updated': self.last_updated.isoformat()
        }


@dataclass
class TradingSignal:
    """交易信號類"""
    signal_id: str
    symbol: str
    signal_type: DecisionType
    strength: float  # 0-1
    confidence: DecisionConfidence
    price_target: Optional[Decimal]
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    position_size: float
    time_horizon: TimeHorizon
    urgency: ExecutionUrgency
    generated_at: datetime
    expires_at: Optional[datetime]
    reasoning: str
    supporting_data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'signal_id': self.signal_id,
            'symbol': self.symbol,
            'signal_type': self.signal_type.value,
            'strength': self.strength,
            'confidence': self.confidence.value,
            'price_target': float(self.price_target) if self.price_target else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss else None,
            'take_profit': float(self.take_profit) if self.take_profit else None,
            'position_size': self.position_size,
            'time_horizon': self.time_horizon.value,
            'urgency': self.urgency.value,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'reasoning': self.reasoning,
            'supporting_data': self.supporting_data
        }


@dataclass
class InvestmentDecision:
    """投資決策類"""
    decision_id: str
    decision_type: DecisionType
    target_symbol: str
    quantity: Decimal
    price: Optional[Decimal]
    confidence: DecisionConfidence
    risk_level: RiskLevel
    expected_return: float
    expected_risk: float
    time_horizon: TimeHorizon
    reasoning: str
    supporting_insights: List[str]
    market_conditions: MarketCondition
    portfolio_impact: Dict[str, Any]
    execution_plan: Dict[str, Any]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'decision_id': self.decision_id,
            'decision_type': self.decision_type.value,
            'target_symbol': self.target_symbol,
            'quantity': float(self.quantity),
            'price': float(self.price) if self.price else None,
            'confidence': self.confidence.value,
            'risk_level': self.risk_level.value,
            'expected_return': self.expected_return,
            'expected_risk': self.expected_risk,
            'time_horizon': self.time_horizon.value,
            'reasoning': self.reasoning,
            'supporting_insights': self.supporting_insights,
            'market_conditions': self.market_conditions.to_dict(),
            'portfolio_impact': self.portfolio_impact,
            'execution_plan': self.execution_plan,
            'created_at': self.created_at.isoformat()
        }


class IntelligentDecisionConfig(BaseModel):
    """智能決策引擎配置"""
    engine_id: str = Field(..., description="引擎ID")
    engine_name: str = Field(..., description="引擎名稱")
    
    # 決策框架配置
    decision_framework: str = Field("multi_factor", description="決策框架類型")
    max_concurrent_decisions: int = Field(10, description="最大並發決策數")
    decision_timeout_seconds: int = Field(30, description="決策超時秒數")
    
    # 風險管理配置
    max_position_size: float = Field(0.1, description="最大單一持倉比例")
    max_portfolio_risk: float = Field(0.15, description="最大投資組合風險")
    default_stop_loss: float = Field(0.05, description="默認止損比例")
    default_take_profit: float = Field(0.15, description="默認止盈比例")
    risk_free_rate: float = Field(0.02, description="無風險利率")
    
    # 倉位管理配置
    position_sizing_method: PositionSizingMethod = Field(PositionSizingMethod.ADAPTIVE, description="倉位規模方法")
    kelly_fraction: float = Field(0.25, description="凱利公式分數")
    max_leverage: float = Field(1.0, description="最大槓桿倍數")
    rebalance_threshold: float = Field(0.05, description="再平衡閾值")
    
    # 信號生成配置
    signal_generation_enabled: bool = Field(True, description="是否啟用信號生成")
    min_signal_strength: float = Field(0.6, description="最小信號強度")
    signal_expiry_hours: int = Field(24, description="信號過期小時數")
    max_signals_per_symbol: int = Field(3, description="每個標的最大信號數")
    
    # 自動執行配置
    auto_execution_enabled: bool = Field(False, description="是否啟用自動執行")
    execution_confidence_threshold: float = Field(0.8, description="執行置信度閾值")
    max_daily_trades: int = Field(20, description="每日最大交易次數")
    slippage_tolerance: float = Field(0.001, description="滑點容忍度")
    
    # 學習和適應配置
    learning_enabled: bool = Field(True, description="是否啟用學習")
    adaptation_frequency: int = Field(100, description="適應頻率（決策次數）")
    performance_tracking_window: int = Field(30, description="性能追蹤窗口（天）")
    
    # 多因子模型配置
    technical_weight: float = Field(0.3, description="技術面權重")
    fundamental_weight: float = Field(0.25, description="基本面權重")
    sentiment_weight: float = Field(0.2, description="情緒面權重")
    macro_weight: float = Field(0.15, description="宏觀面權重")
    momentum_weight: float = Field(0.1, description="動能面權重")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DecisionNode:
    """決策節點類"""
    
    def __init__(self, node_id: str, condition: Callable[[Dict[str, Any]], bool],
                 action: Callable[[Dict[str, Any]], Any], 
                 children: Optional[List['DecisionNode']] = None):
        self.node_id = node_id
        self.condition = condition
        self.action = action
        self.children = children or []
        self.execution_count = 0
        self.success_count = 0
        self.total_return = 0.0
        
    def evaluate(self, context: Dict[str, Any]) -> Any:
        """評估決策節點"""
        self.execution_count += 1
        
        if self.condition(context):
            # 執行當前節點的動作
            result = self.action(context)
            
            # 評估子節點
            child_results = []
            for child in self.children:
                child_result = child.evaluate(context)
                if child_result is not None:
                    child_results.append(child_result)
            
            return result if not child_results else (result, child_results)
        
        # 如果條件不滿足，評估子節點
        for child in self.children:
            result = child.evaluate(context)
            if result is not None:
                return result
        
        return None
    
    def update_performance(self, return_value: float, success: bool):
        """更新性能統計"""
        if success:
            self.success_count += 1
        self.total_return += return_value
    
    def get_success_rate(self) -> float:
        """獲取成功率"""
        return self.success_count / max(1, self.execution_count)
    
    def get_average_return(self) -> float:
        """獲取平均收益率"""
        return self.total_return / max(1, self.execution_count)


class MultiFactorDecisionModel:
    """多因子決策模型"""
    
    def __init__(self, config: IntelligentDecisionConfig):
        self.config = config
        self.factor_weights = {
            'technical': config.technical_weight,
            'fundamental': config.fundamental_weight,
            'sentiment': config.sentiment_weight,
            'macro': config.macro_weight,
            'momentum': config.momentum_weight
        }
        
        # 因子評分函數
        self.factor_scorers = {
            'technical': self._score_technical_factors,
            'fundamental': self._score_fundamental_factors,
            'sentiment': self._score_sentiment_factors,
            'macro': self._score_macro_factors,
            'momentum': self._score_momentum_factors
        }
        
        # 因子歷史表現
        self.factor_performance = defaultdict(list)
        
    def evaluate_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """評估投資決策"""
        
        factor_scores = {}
        weighted_score = 0.0
        
        # 計算各因子分數
        for factor_name, weight in self.factor_weights.items():
            if factor_name in self.factor_scorers:
                score = self.factor_scorers[factor_name](context)
                factor_scores[factor_name] = score
                weighted_score += score * weight
        
        # 決策置信度
        confidence = self._calculate_confidence(factor_scores, weighted_score)
        
        # 決策類型和強度
        decision_type, strength = self._determine_decision(weighted_score, factor_scores)
        
        return {
            'weighted_score': weighted_score,
            'factor_scores': factor_scores,
            'decision_type': decision_type,
            'strength': strength,
            'confidence': confidence,
            'supporting_factors': self._get_supporting_factors(factor_scores),
            'risk_assessment': self._assess_risk(factor_scores, context)
        }
    
    def _score_technical_factors(self, context: Dict[str, Any]) -> float:
        """評分技術面因子"""
        score = 0.0
        
        market_data = context.get('market_data', {})
        
        # RSI評分
        rsi = market_data.get('rsi', 50)
        if rsi < 30:  # 超賣
            score += 0.3
        elif rsi > 70:  # 超買
            score -= 0.3
        
        # MACD評分
        macd_signal = market_data.get('macd_signal', 'neutral')
        if macd_signal == 'golden_cross':
            score += 0.25
        elif macd_signal == 'death_cross':
            score -= 0.25
        
        # 移動平均線評分
        ma_trend = market_data.get('ma_trend', 'neutral')
        if ma_trend == 'bullish':
            score += 0.2
        elif ma_trend == 'bearish':
            score -= 0.2
        
        # 支撐阻力評分
        price = market_data.get('current_price', 0)
        support = market_data.get('support_level', 0)
        resistance = market_data.get('resistance_level', 0)
        
        if support > 0 and resistance > 0:
            if price <= support * 1.02:  # 接近支撐
                score += 0.15
            elif price >= resistance * 0.98:  # 接近阻力
                score -= 0.15
        
        # 成交量評分
        volume_ratio = market_data.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:  # 放量
            score += 0.1 if score > 0 else -0.1
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_fundamental_factors(self, context: Dict[str, Any]) -> float:
        """評分基本面因子"""
        score = 0.0
        
        fundamental_data = context.get('fundamental_data', {})
        
        # P/E比評分
        pe_ratio = fundamental_data.get('pe_ratio', 20)
        industry_pe = fundamental_data.get('industry_pe', 20)
        if pe_ratio > 0 and industry_pe > 0:
            pe_relative = pe_ratio / industry_pe
            if pe_relative < 0.8:  # 低估
                score += 0.3
            elif pe_relative > 1.2:  # 高估
                score -= 0.2
        
        # ROE評分
        roe = fundamental_data.get('roe', 0.1)
        if roe > 0.15:  # 高ROE
            score += 0.25
        elif roe < 0.05:  # 低ROE
            score -= 0.2
        
        # 收入成長率評分
        revenue_growth = fundamental_data.get('revenue_growth', 0)
        if revenue_growth > 0.1:  # 10%以上成長
            score += 0.2
        elif revenue_growth < -0.05:  # 負成長
            score -= 0.25
        
        # 債務比率評分
        debt_ratio = fundamental_data.get('debt_ratio', 0.5)
        if debt_ratio < 0.3:  # 低負債
            score += 0.15
        elif debt_ratio > 0.7:  # 高負債
            score -= 0.2
        
        # 現金流評分
        fcf_yield = fundamental_data.get('fcf_yield', 0.05)
        if fcf_yield > 0.08:  # 高現金流收益率
            score += 0.1
        elif fcf_yield < 0:  # 負現金流
            score -= 0.15
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_sentiment_factors(self, context: Dict[str, Any]) -> float:
        """評分情緒面因子"""
        score = 0.0
        
        sentiment_data = context.get('sentiment_data', {})
        
        # 新聞情緒評分
        news_sentiment = sentiment_data.get('news_sentiment', 0.5)
        if news_sentiment > 0.7:  # 正面情緒
            score += 0.3
        elif news_sentiment < 0.3:  # 負面情緒
            score -= 0.3
        
        # 社媒情緒評分
        social_sentiment = sentiment_data.get('social_sentiment', 0.5)
        if social_sentiment > 0.75:
            score += 0.25
        elif social_sentiment < 0.25:
            score -= 0.25
        
        # 分析師評級評分
        analyst_rating = sentiment_data.get('analyst_rating', 3)  # 1-5, 5最好
        if analyst_rating >= 4:
            score += 0.2
        elif analyst_rating <= 2:
            score -= 0.2
        
        # 機構持倉變化評分
        institutional_flow = sentiment_data.get('institutional_flow', 0)
        if institutional_flow > 0.05:  # 機構增持
            score += 0.15
        elif institutional_flow < -0.05:  # 機構減持
            score -= 0.15
        
        # 內部人交易評分
        insider_trading = sentiment_data.get('insider_trading', 0)
        if insider_trading > 0:  # 內部人買入
            score += 0.1
        elif insider_trading < 0:  # 內部人賣出
            score -= 0.1
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_macro_factors(self, context: Dict[str, Any]) -> float:
        """評分宏觀面因子"""
        score = 0.0
        
        macro_data = context.get('macro_data', {})
        
        # 利率環境評分
        interest_rate_trend = macro_data.get('interest_rate_trend', 'neutral')
        if interest_rate_trend == 'declining':
            score += 0.3
        elif interest_rate_trend == 'rising':
            score -= 0.2
        
        # GDP成長率評分
        gdp_growth = macro_data.get('gdp_growth', 0.02)
        if gdp_growth > 0.03:
            score += 0.25
        elif gdp_growth < 0:
            score -= 0.3
        
        # 通膨率評分
        inflation_rate = macro_data.get('inflation_rate', 0.02)
        if 0.02 <= inflation_rate <= 0.04:  # 溫和通膨
            score += 0.2
        elif inflation_rate > 0.06:  # 高通膨
            score -= 0.25
        
        # 失業率評分
        unemployment_rate = macro_data.get('unemployment_rate', 0.05)
        if unemployment_rate < 0.04:  # 低失業率
            score += 0.15
        elif unemployment_rate > 0.08:  # 高失業率
            score -= 0.2
        
        # 匯率評分（對出口導向公司）
        currency_strength = macro_data.get('currency_strength', 'neutral')
        export_ratio = context.get('company_data', {}).get('export_ratio', 0.3)
        if export_ratio > 0.5:  # 出口導向公司
            if currency_strength == 'weak':
                score += 0.1
            elif currency_strength == 'strong':
                score -= 0.1
        
        return np.clip(score, -1.0, 1.0)
    
    def _score_momentum_factors(self, context: Dict[str, Any]) -> float:
        """評分動能面因子"""
        score = 0.0
        
        momentum_data = context.get('momentum_data', {})
        
        # 價格動能評分
        price_momentum = momentum_data.get('price_momentum_20d', 0)
        if price_momentum > 0.05:  # 強勢動能
            score += 0.4
        elif price_momentum < -0.05:  # 弱勢動能
            score -= 0.4
        
        # 相對強弱評分
        relative_strength = momentum_data.get('relative_strength', 50)
        if relative_strength > 80:
            score += 0.25
        elif relative_strength < 20:
            score -= 0.25
        
        # 資金流向評分
        money_flow = momentum_data.get('money_flow', 0)
        if money_flow > 0.1:  # 資金流入
            score += 0.2
        elif money_flow < -0.1:  # 資金流出
            score -= 0.2
        
        # 板塊動能評分
        sector_momentum = momentum_data.get('sector_momentum', 0)
        if sector_momentum > 0.03:
            score += 0.15
        elif sector_momentum < -0.03:
            score -= 0.15
        
        return np.clip(score, -1.0, 1.0)
    
    def _calculate_confidence(self, factor_scores: Dict[str, float], weighted_score: float) -> float:
        """計算決策置信度"""
        
        # 因子一致性（因子方向是否一致）
        positive_factors = sum(1 for score in factor_scores.values() if score > 0.1)
        negative_factors = sum(1 for score in factor_scores.values() if score < -0.1)
        total_factors = len(factor_scores)
        
        consistency = max(positive_factors, negative_factors) / total_factors if total_factors > 0 else 0
        
        # 信號強度
        signal_strength = abs(weighted_score)
        
        # 綜合置信度
        confidence = (consistency * 0.6 + signal_strength * 0.4)
        
        return np.clip(confidence, 0.0, 1.0)
    
    def _determine_decision(self, weighted_score: float, 
                           factor_scores: Dict[str, float]) -> Tuple[DecisionType, float]:
        """確定決策類型和強度"""
        
        strength = abs(weighted_score)
        
        if weighted_score > 0.3:
            return DecisionType.BUY, strength
        elif weighted_score < -0.3:
            return DecisionType.SELL, strength
        elif -0.1 <= weighted_score <= 0.1:
            return DecisionType.HOLD, strength
        elif weighted_score > 0.1:
            return DecisionType.INCREASE_POSITION, strength
        elif weighted_score < -0.1:
            return DecisionType.REDUCE_POSITION, strength
        else:
            return DecisionType.HOLD, strength
    
    def _get_supporting_factors(self, factor_scores: Dict[str, float]) -> List[str]:
        """獲取支撐因子"""
        supporting_factors = []
        
        for factor, score in factor_scores.items():
            if abs(score) > 0.2:
                direction = "正面" if score > 0 else "負面"
                supporting_factors.append(f"{factor}面{direction}({score:.2f})")
        
        return supporting_factors
    
    def _assess_risk(self, factor_scores: Dict[str, float], context: Dict[str, Any]) -> Dict[str, float]:
        """評估風險"""
        
        # 基礎風險評估
        volatility = context.get('market_data', {}).get('volatility', 0.2)
        beta = context.get('market_data', {}).get('beta', 1.0)
        
        # 因子風險
        factor_risk = np.std(list(factor_scores.values()))
        
        # 綜合風險評分
        systematic_risk = volatility * beta
        idiosyncratic_risk = factor_risk
        total_risk = systematic_risk + idiosyncratic_risk
        
        return {
            'systematic_risk': systematic_risk,
            'idiosyncratic_risk': idiosyncratic_risk,
            'total_risk': total_risk,
            'risk_level': self._categorize_risk(total_risk)
        }
    
    def _categorize_risk(self, risk_score: float) -> str:
        """分類風險等級"""
        if risk_score < 0.1:
            return RiskLevel.VERY_LOW.value
        elif risk_score < 0.2:
            return RiskLevel.LOW.value
        elif risk_score < 0.3:
            return RiskLevel.MEDIUM.value
        elif risk_score < 0.4:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.VERY_HIGH.value
    
    def update_factor_weights(self, performance_data: Dict[str, float]):
        """更新因子權重"""
        
        # 基於歷史表現調整權重
        for factor, performance in performance_data.items():
            if factor in self.factor_weights:
                # 簡單的權重調整邏輯
                current_weight = self.factor_weights[factor]
                adjustment = 0.01 if performance > 0 else -0.01
                new_weight = max(0.05, min(0.5, current_weight + adjustment))
                self.factor_weights[factor] = new_weight
        
        # 重新歸一化權重
        total_weight = sum(self.factor_weights.values())
        if total_weight > 0:
            for factor in self.factor_weights:
                self.factor_weights[factor] /= total_weight


class RiskManager:
    """風險管理器"""
    
    def __init__(self, config: IntelligentDecisionConfig):
        self.config = config
        self.risk_limits = {
            'max_position_size': config.max_position_size,
            'max_portfolio_risk': config.max_portfolio_risk,
            'max_leverage': config.max_leverage
        }
        
        self.risk_monitoring = {
            'portfolio_var': 0.0,
            'max_drawdown': 0.0,
            'sharpe_ratio': 0.0,
            'beta': 1.0
        }
    
    def assess_position_risk(self, symbol: str, proposed_position: float,
                           current_portfolio: Portfolio,
                           market_data: Dict[str, Any]) -> Dict[str, Any]:
        """評估持倉風險"""
        
        volatility = market_data.get('volatility', 0.2)
        beta = market_data.get('beta', 1.0)
        correlation = market_data.get('portfolio_correlation', 0.5)
        
        # 計算持倉風險
        position_var = proposed_position * volatility
        
        # 計算組合風險影響
        current_risk = current_portfolio.risk_metrics.get('portfolio_var', 0.0)
        new_risk = math.sqrt(current_risk**2 + position_var**2 + 
                           2 * current_risk * position_var * correlation)
        
        # 風險限制檢查
        risk_checks = {
            'position_size_ok': proposed_position <= self.config.max_position_size,
            'portfolio_risk_ok': new_risk <= self.config.max_portfolio_risk,
            'leverage_ok': True  # 簡化處理
        }
        
        return {
            'position_var': position_var,
            'portfolio_var_impact': new_risk - current_risk,
            'new_portfolio_var': new_risk,
            'risk_checks': risk_checks,
            'overall_risk_ok': all(risk_checks.values()),
            'risk_score': min(1.0, new_risk / self.config.max_portfolio_risk)
        }
    
    def calculate_position_size(self, symbol: str, signal_strength: float,
                              portfolio: Portfolio, market_data: Dict[str, Any],
                              method: PositionSizingMethod = None) -> float:
        """計算倉位大小"""
        
        if method is None:
            method = self.config.position_sizing_method
        
        if method == PositionSizingMethod.FIXED_PERCENTAGE:
            return self._fixed_percentage_sizing(signal_strength)
        
        elif method == PositionSizingMethod.KELLY_CRITERION:
            return self._kelly_sizing(symbol, signal_strength, market_data)
        
        elif method == PositionSizingMethod.VOLATILITY_ADJUSTED:
            return self._volatility_adjusted_sizing(signal_strength, market_data)
        
        elif method == PositionSizingMethod.RISK_PARITY:
            return self._risk_parity_sizing(symbol, portfolio, market_data)
        
        elif method == PositionSizingMethod.ADAPTIVE:
            return self._adaptive_sizing(signal_strength, portfolio, market_data)
        
        else:  # FIXED_AMOUNT
            return self._fixed_amount_sizing()
    
    def _fixed_percentage_sizing(self, signal_strength: float) -> float:
        """固定百分比倉位"""
        base_size = 0.05  # 5%
        return base_size * signal_strength
    
    def _kelly_sizing(self, symbol: str, signal_strength: float,
                     market_data: Dict[str, Any]) -> float:
        """凱利公式倉位"""
        
        win_prob = 0.5 + signal_strength * 0.3  # 基礎50%勝率
        win_loss_ratio = market_data.get('avg_win_loss_ratio', 1.5)
        
        kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        kelly_fraction = max(0, kelly_fraction)
        
        # 應用凱利分數限制
        position_size = kelly_fraction * self.config.kelly_fraction
        
        return min(position_size, self.config.max_position_size)
    
    def _volatility_adjusted_sizing(self, signal_strength: float,
                                   market_data: Dict[str, Any]) -> float:
        """波動率調整倉位"""
        
        volatility = market_data.get('volatility', 0.2)
        target_vol = 0.15  # 目標波動率
        
        vol_adjustment = target_vol / volatility if volatility > 0 else 1.0
        base_size = 0.1 * signal_strength
        
        return min(base_size * vol_adjustment, self.config.max_position_size)
    
    def _risk_parity_sizing(self, symbol: str, portfolio: Portfolio,
                           market_data: Dict[str, Any]) -> float:
        """風險平價倉位"""
        
        volatility = market_data.get('volatility', 0.2)
        target_risk_contribution = 1.0 / len(portfolio.positions) if portfolio.positions else 1.0
        
        portfolio_vol = portfolio.risk_metrics.get('portfolio_volatility', 0.15)
        position_size = (target_risk_contribution * portfolio_vol) / volatility
        
        return min(position_size, self.config.max_position_size)
    
    def _adaptive_sizing(self, signal_strength: float, portfolio: Portfolio,
                        market_data: Dict[str, Any]) -> float:
        """自適應倉位"""
        
        # 結合多種方法
        kelly_size = self._kelly_sizing("", signal_strength, market_data)
        vol_size = self._volatility_adjusted_sizing(signal_strength, market_data)
        fixed_size = self._fixed_percentage_sizing(signal_strength)
        
        # 加權平均
        weights = [0.4, 0.3, 0.3]
        sizes = [kelly_size, vol_size, fixed_size]
        
        adaptive_size = sum(w * s for w, s in zip(weights, sizes))
        
        return min(adaptive_size, self.config.max_position_size)
    
    def _fixed_amount_sizing(self) -> float:
        """固定金額倉位"""
        return 0.05  # 固定5%
    
    def set_stop_loss_take_profit(self, decision: InvestmentDecision,
                                  market_data: Dict[str, Any]) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """設置止損止盈"""
        
        current_price = market_data.get('current_price', 0)
        if current_price <= 0:
            return None, None
        
        current_price = Decimal(str(current_price))
        volatility = market_data.get('volatility', 0.2)
        
        # 動態止損止盈設置
        if decision.decision_type in [DecisionType.BUY, DecisionType.INCREASE_POSITION]:
            # 買入類決策
            stop_loss_pct = max(self.config.default_stop_loss, volatility * 0.5)
            take_profit_pct = max(self.config.default_take_profit, volatility * 1.5)
            
            stop_loss = current_price * (1 - Decimal(str(stop_loss_pct)))
            take_profit = current_price * (1 + Decimal(str(take_profit_pct)))
            
        elif decision.decision_type in [DecisionType.SELL, DecisionType.REDUCE_POSITION]:
            # 賣出類決策
            stop_loss_pct = max(self.config.default_stop_loss, volatility * 0.5)
            take_profit_pct = max(self.config.default_take_profit, volatility * 1.5)
            
            stop_loss = current_price * (1 + Decimal(str(stop_loss_pct)))
            take_profit = current_price * (1 - Decimal(str(take_profit_pct)))
        
        else:
            return None, None
        
        return stop_loss, take_profit


class SignalGenerator:
    """交易信號生成器"""
    
    def __init__(self, config: IntelligentDecisionConfig):
        self.config = config
        self.signal_history = deque(maxlen=1000)
        self.active_signals = {}
        
    def generate_trading_signals(self, market_data: Dict[str, Any],
                               predictions: Optional[PredictionResult] = None,
                               insights: Optional[List[AlphaInsight]] = None) -> List[TradingSignal]:
        """生成交易信號"""
        
        signals = []
        current_time = datetime.now(timezone.utc)
        
        try:
            # 基於預測生成信號
            if predictions:
                prediction_signals = self._generate_prediction_signals(predictions, market_data, current_time)
                signals.extend(prediction_signals)
            
            # 基於洞察生成信號
            if insights:
                insight_signals = self._generate_insight_signals(insights, market_data, current_time)
                signals.extend(insight_signals)
            
            # 技術指標信號
            technical_signals = self._generate_technical_signals(market_data, current_time)
            signals.extend(technical_signals)
            
            # 過濾和優化信號
            filtered_signals = self._filter_signals(signals, market_data)
            
            # 更新活躍信號
            self._update_active_signals(filtered_signals)
            
            return filtered_signals
            
        except Exception as e:
            logger.error(f"Signal generation failed: {e}")
            return []
    
    def _generate_prediction_signals(self, predictions: PredictionResult,
                                   market_data: Dict[str, Any],
                                   current_time: datetime) -> List[TradingSignal]:
        """基於預測生成信號"""
        
        signals = []
        
        if predictions.prediction_type == PredictionType.PRICE:
            current_price = market_data.get('current_price', 0)
            if current_price > 0 and len(predictions.predictions) > 0:
                
                predicted_price = predictions.predictions[-1]  # 最終預測價格
                price_change = (predicted_price - current_price) / current_price
                
                # 生成買賣信號
                if price_change > 0.05:  # 預期上漲5%以上
                    signal = TradingSignal(
                        signal_id=f"pred_buy_{int(current_time.timestamp())}",
                        symbol=market_data.get('symbol', 'UNKNOWN'),
                        signal_type=DecisionType.BUY,
                        strength=min(abs(price_change), 1.0),
                        confidence=self._map_confidence(predictions.model_confidence),
                        price_target=Decimal(str(predicted_price)),
                        stop_loss=None,
                        take_profit=None,
                        position_size=0.0,  # 將由風險管理器計算
                        time_horizon=predictions.horizon,
                        urgency=ExecutionUrgency.NORMAL,
                        generated_at=current_time,
                        expires_at=current_time + timedelta(hours=self.config.signal_expiry_hours),
                        reasoning=f"預測價格上漲至{predicted_price:.2f}({price_change:.1%})",
                        supporting_data={
                            'predicted_price': predicted_price,
                            'current_price': current_price,
                            'price_change_pct': price_change,
                            'model_confidence': predictions.model_confidence,
                            'prediction_id': predictions.prediction_id
                        }
                    )
                    signals.append(signal)
                
                elif price_change < -0.05:  # 預期下跌5%以上
                    signal = TradingSignal(
                        signal_id=f"pred_sell_{int(current_time.timestamp())}",
                        symbol=market_data.get('symbol', 'UNKNOWN'),
                        signal_type=DecisionType.SELL,
                        strength=min(abs(price_change), 1.0),
                        confidence=self._map_confidence(predictions.model_confidence),
                        price_target=Decimal(str(predicted_price)),
                        stop_loss=None,
                        take_profit=None,
                        position_size=0.0,
                        time_horizon=predictions.horizon,
                        urgency=ExecutionUrgency.NORMAL,
                        generated_at=current_time,
                        expires_at=current_time + timedelta(hours=self.config.signal_expiry_hours),
                        reasoning=f"預測價格下跌至{predicted_price:.2f}({price_change:.1%})",
                        supporting_data={
                            'predicted_price': predicted_price,
                            'current_price': current_price,
                            'price_change_pct': price_change,
                            'model_confidence': predictions.model_confidence,
                            'prediction_id': predictions.prediction_id
                        }
                    )
                    signals.append(signal)
        
        return signals
    
    def _generate_insight_signals(self, insights: List[AlphaInsight],
                                market_data: Dict[str, Any],
                                current_time: datetime) -> List[TradingSignal]:
        """基於洞察生成信號"""
        
        signals = []
        
        for insight in insights:
            if insight.priority in [AlphaInsightPriority.CRITICAL, AlphaInsightPriority.HIGH]:
                
                # 根據市場方向生成信號
                if insight.market_direction == MarketDirection.BULLISH:
                    signal_type = DecisionType.BUY
                elif insight.market_direction == MarketDirection.BEARISH:
                    signal_type = DecisionType.SELL
                else:
                    continue  # 中性或波動不生成信號
                
                signal = TradingSignal(
                    signal_id=f"insight_{insight.insight_id}_{int(current_time.timestamp())}",
                    symbol=insight.stock_code or market_data.get('symbol', 'UNKNOWN'),
                    signal_type=signal_type,
                    strength=insight.confidence_score,
                    confidence=self._map_confidence(insight.confidence_score),
                    price_target=insight.target_price,
                    stop_loss=insight.stop_loss,
                    take_profit=None,
                    position_size=0.0,
                    time_horizon=insight.time_horizon,
                    urgency=self._map_urgency(insight.priority),
                    generated_at=current_time,
                    expires_at=current_time + timedelta(hours=self.config.signal_expiry_hours),
                    reasoning=f"基於{insight.insight_type.value}洞察：{insight.summary}",
                    supporting_data={
                        'insight_id': insight.insight_id,
                        'insight_type': insight.insight_type.value,
                        'confidence_score': insight.confidence_score,
                        'expected_impact': insight.expected_impact,
                        'supporting_data': insight.supporting_data
                    }
                )
                signals.append(signal)
        
        return signals
    
    def _generate_technical_signals(self, market_data: Dict[str, Any],
                                  current_time: datetime) -> List[TradingSignal]:
        """生成技術指標信號"""
        
        signals = []
        symbol = market_data.get('symbol', 'UNKNOWN')
        
        # RSI信號
        rsi = market_data.get('rsi', 50)
        if rsi < 30:  # 超賣
            signal = TradingSignal(
                signal_id=f"rsi_buy_{symbol}_{int(current_time.timestamp())}",
                symbol=symbol,
                signal_type=DecisionType.BUY,
                strength=0.6,
                confidence=DecisionConfidence.MEDIUM,
                price_target=None,
                stop_loss=None,
                take_profit=None,
                position_size=0.0,
                time_horizon=TimeHorizon.SHORT_TERM,
                urgency=ExecutionUrgency.NORMAL,
                generated_at=current_time,
                expires_at=current_time + timedelta(hours=12),
                reasoning=f"RSI超賣信號({rsi:.1f})",
                supporting_data={'rsi': rsi, 'signal_type': 'oversold'}
            )
            signals.append(signal)
        
        elif rsi > 70:  # 超買
            signal = TradingSignal(
                signal_id=f"rsi_sell_{symbol}_{int(current_time.timestamp())}",
                symbol=symbol,
                signal_type=DecisionType.SELL,
                strength=0.6,
                confidence=DecisionConfidence.MEDIUM,
                price_target=None,
                stop_loss=None,
                take_profit=None,
                position_size=0.0,
                time_horizon=TimeHorizon.SHORT_TERM,
                urgency=ExecutionUrgency.NORMAL,
                generated_at=current_time,
                expires_at=current_time + timedelta(hours=12),
                reasoning=f"RSI超買信號({rsi:.1f})",
                supporting_data={'rsi': rsi, 'signal_type': 'overbought'}
            )
            signals.append(signal)
        
        # MACD信號
        macd_signal = market_data.get('macd_signal', 'neutral')
        if macd_signal == 'golden_cross':
            signal = TradingSignal(
                signal_id=f"macd_buy_{symbol}_{int(current_time.timestamp())}",
                symbol=symbol,
                signal_type=DecisionType.BUY,
                strength=0.7,
                confidence=DecisionConfidence.HIGH,
                price_target=None,
                stop_loss=None,
                take_profit=None,
                position_size=0.0,
                time_horizon=TimeHorizon.MEDIUM_TERM,
                urgency=ExecutionUrgency.HIGH,
                generated_at=current_time,
                expires_at=current_time + timedelta(hours=24),
                reasoning="MACD金叉信號",
                supporting_data={'macd_signal': macd_signal}
            )
            signals.append(signal)
        
        elif macd_signal == 'death_cross':
            signal = TradingSignal(
                signal_id=f"macd_sell_{symbol}_{int(current_time.timestamp())}",
                symbol=symbol,
                signal_type=DecisionType.SELL,
                strength=0.7,
                confidence=DecisionConfidence.HIGH,
                price_target=None,
                stop_loss=None,
                take_profit=None,
                position_size=0.0,
                time_horizon=TimeHorizon.MEDIUM_TERM,
                urgency=ExecutionUrgency.HIGH,
                generated_at=current_time,
                expires_at=current_time + timedelta(hours=24),
                reasoning="MACD死叉信號",
                supporting_data={'macd_signal': macd_signal}
            )
            signals.append(signal)
        
        return signals
    
    def _filter_signals(self, signals: List[TradingSignal],
                       market_data: Dict[str, Any]) -> List[TradingSignal]:
        """過濾和優化信號"""
        
        # 按強度和置信度排序
        signals.sort(key=lambda s: (s.strength * self._confidence_to_float(s.confidence)), reverse=True)
        
        # 移除弱信號
        strong_signals = [s for s in signals if s.strength >= self.config.min_signal_strength]
        
        # 移除重複信號（同一標的同一方向）
        unique_signals = []
        seen_combinations = set()
        
        for signal in strong_signals:
            combination = (signal.symbol, signal.signal_type)
            if combination not in seen_combinations:
                seen_combinations.add(combination)
                unique_signals.append(signal)
        
        # 限制每個標的的信號數量
        symbol_counts = defaultdict(int)
        filtered_signals = []
        
        for signal in unique_signals:
            if symbol_counts[signal.symbol] < self.config.max_signals_per_symbol:
                filtered_signals.append(signal)
                symbol_counts[signal.symbol] += 1
        
        return filtered_signals
    
    def _map_confidence(self, confidence_score: float) -> DecisionConfidence:
        """映射置信度分數到置信度等級"""
        if confidence_score >= 0.9:
            return DecisionConfidence.VERY_HIGH
        elif confidence_score >= 0.75:
            return DecisionConfidence.HIGH
        elif confidence_score >= 0.6:
            return DecisionConfidence.MEDIUM
        elif confidence_score >= 0.4:
            return DecisionConfidence.LOW
        else:
            return DecisionConfidence.VERY_LOW
    
    def _map_urgency(self, priority: AlphaInsightPriority) -> ExecutionUrgency:
        """映射洞察優先級到執行緊急程度"""
        if priority == AlphaInsightPriority.CRITICAL:
            return ExecutionUrgency.IMMEDIATE
        elif priority == AlphaInsightPriority.HIGH:
            return ExecutionUrgency.HIGH
        elif priority == AlphaInsightPriority.MEDIUM:
            return ExecutionUrgency.NORMAL
        else:
            return ExecutionUrgency.LOW
    
    def _confidence_to_float(self, confidence: DecisionConfidence) -> float:
        """置信度等級轉換為數值"""
        mapping = {
            DecisionConfidence.VERY_HIGH: 0.95,
            DecisionConfidence.HIGH: 0.8,
            DecisionConfidence.MEDIUM: 0.65,
            DecisionConfidence.LOW: 0.5,
            DecisionConfidence.VERY_LOW: 0.3
        }
        return mapping.get(confidence, 0.5)
    
    def _update_active_signals(self, signals: List[TradingSignal]):
        """更新活躍信號"""
        current_time = datetime.now(timezone.utc)
        
        # 移除過期信號
        expired_signals = []
        for signal_id, signal in self.active_signals.items():
            if signal.expires_at and current_time > signal.expires_at:
                expired_signals.append(signal_id)
        
        for signal_id in expired_signals:
            del self.active_signals[signal_id]
        
        # 添加新信號
        for signal in signals:
            self.active_signals[signal.signal_id] = signal
    
    def get_active_signals(self) -> List[TradingSignal]:
        """獲取活躍信號"""
        return list(self.active_signals.values())


class IntelligentDecisionEngine:
    """智能決策引擎核心類"""
    
    def __init__(self, config: IntelligentDecisionConfig):
        self.config = config
        self.is_initialized = False
        
        # 核心組件
        self.multi_factor_model = None
        self.risk_manager = None
        self.signal_generator = None
        
        # 決策樹
        self.decision_tree = None
        
        # 決策歷史
        self.decision_history = deque(maxlen=10000)
        self.execution_results = {}
        
        # 性能統計
        self.performance_stats = {
            'total_decisions': 0,
            'successful_decisions': 0,
            'total_return': 0.0,
            'average_return': 0.0,
            'win_rate': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0
        }
        
        # 學習組件
        self.adaptive_learner = None
        
        logger.info(f"IntelligentDecisionEngine initialized: {config.engine_name}")
    
    async def initialize(self) -> bool:
        """初始化智能決策引擎"""
        try:
            logger.info("Initializing IntelligentDecisionEngine...")
            
            # 1. 初始化多因子決策模型
            self.multi_factor_model = MultiFactorDecisionModel(self.config)
            
            # 2. 初始化風險管理器
            self.risk_manager = RiskManager(self.config)
            
            # 3. 初始化信號生成器
            if self.config.signal_generation_enabled:
                self.signal_generator = SignalGenerator(self.config)
            
            # 4. 構建決策樹
            await self._build_decision_tree()
            
            # 5. 初始化自適應學習器（如果啟用）
            if self.config.learning_enabled:
                from .adaptive_learning_engine import AdaptiveLearningConfig, AdaptiveLearningEngine
                
                learning_config = AdaptiveLearningConfig(
                    engine_id=f"{self.config.engine_id}_learner",
                    engine_name=f"{self.config.engine_name}學習器",
                    learning_rate=0.001,
                    buffer_size=1000,
                    batch_size=32
                )
                
                self.adaptive_learner = AdaptiveLearningEngine(learning_config)
                await self.adaptive_learner.initialize()
            
            self.is_initialized = True
            logger.info("IntelligentDecisionEngine initialization completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"IntelligentDecisionEngine initialization failed: {e}")
            return False
    
    async def generate_investment_decision(self, context: Dict[str, Any]) -> InvestmentDecision:
        """生成投資決策"""
        try:
            decision_id = f"decision_{int(datetime.now().timestamp())}_{hash(str(context)) % 10000:04d}"
            start_time = datetime.now()
            
            logger.info(f"Generating investment decision: {decision_id}")
            
            # 1. 解析上下文
            market_data = context.get('market_data', {})
            portfolio = context.get('portfolio')
            predictions = context.get('predictions')
            insights = context.get('insights', [])
            
            # 2. 創建市場條件
            market_conditions = await self._create_market_conditions(market_data)
            
            # 3. 多因子決策評估
            decision_evaluation = self.multi_factor_model.evaluate_decision(context)
            
            # 4. 決策樹評估
            tree_result = None
            if self.decision_tree:
                tree_result = self.decision_tree.evaluate(context)
            
            # 5. 確定決策類型和參數
            decision_type = decision_evaluation['decision_type']
            confidence = self._map_float_to_confidence(decision_evaluation['confidence'])
            
            # 6. 風險評估
            risk_assessment = decision_evaluation['risk_assessment']
            risk_level = self._map_risk_score_to_level(risk_assessment['total_risk'])
            
            # 7. 計算倉位大小
            position_size = 0.0
            if portfolio:
                position_size = self.risk_manager.calculate_position_size(
                    symbol=market_data.get('symbol', ''),
                    signal_strength=decision_evaluation['strength'],
                    portfolio=portfolio,
                    market_data=market_data
                )
            
            # 8. 計算預期收益和風險
            expected_return = decision_evaluation['strength'] * 0.1  # 簡化計算
            expected_risk = risk_assessment['total_risk']
            
            # 9. 確定時間範圍
            time_horizon = self._determine_time_horizon(decision_evaluation, market_conditions)
            
            # 10. 生成推理說明
            reasoning = self._generate_reasoning(decision_evaluation, risk_assessment)
            
            # 11. 創建投資決策
            decision = InvestmentDecision(
                decision_id=decision_id,
                decision_type=decision_type,
                target_symbol=market_data.get('symbol', 'UNKNOWN'),
                quantity=Decimal(str(position_size)) if position_size > 0 else Decimal('0'),
                price=Decimal(str(market_data.get('current_price', 0))) if market_data.get('current_price') else None,
                confidence=confidence,
                risk_level=risk_level,
                expected_return=expected_return,
                expected_risk=expected_risk,
                time_horizon=time_horizon,
                reasoning=reasoning,
                supporting_insights=[insight.insight_id for insight in insights],
                market_conditions=market_conditions,
                portfolio_impact=await self._calculate_portfolio_impact(decision_type, position_size, portfolio),
                execution_plan=await self._create_execution_plan(decision_type, market_conditions),
                created_at=datetime.now(timezone.utc)
            )
            
            # 12. 記錄決策歷史
            self.decision_history.append(decision)
            
            # 13. 更新統計信息
            self._update_performance_stats(decision)
            
            # 14. 自適應學習（如果啟用）
            if self.adaptive_learner:
                await self._perform_adaptive_learning(decision, context)
            
            logger.info(f"Investment decision generated: {decision_id} - {decision_type.value}")
            
            return decision
            
        except Exception as e:
            logger.error(f"Investment decision generation failed: {e}")
            
            # 返回保守決策
            return InvestmentDecision(
                decision_id=f"error_{int(datetime.now().timestamp())}",
                decision_type=DecisionType.HOLD,
                target_symbol=context.get('market_data', {}).get('symbol', 'UNKNOWN'),
                quantity=Decimal('0'),
                price=None,
                confidence=DecisionConfidence.LOW,
                risk_level=RiskLevel.HIGH,
                expected_return=0.0,
                expected_risk=0.5,
                time_horizon=TimeHorizon.SHORT_TERM,
                reasoning=f"決策生成失敗，採用保守策略: {str(e)}",
                supporting_insights=[],
                market_conditions=await self._create_market_conditions(context.get('market_data', {})),
                portfolio_impact={'error': True},
                execution_plan={'status': 'error'},
                created_at=datetime.now(timezone.utc)
            )
    
    async def generate_trading_signals(self, market_data: Dict[str, Any],
                                     predictions: Optional[PredictionResult] = None,
                                     insights: Optional[List[AlphaInsight]] = None) -> List[TradingSignal]:
        """生成交易信號"""
        
        if not self.config.signal_generation_enabled or not self.signal_generator:
            return []
        
        try:
            signals = self.signal_generator.generate_trading_signals(market_data, predictions, insights)
            logger.info(f"Generated {len(signals)} trading signals")
            return signals
            
        except Exception as e:
            logger.error(f"Trading signal generation failed: {e}")
            return []
    
    async def execute_portfolio_rebalance(self, portfolio: Portfolio,
                                        target_allocations: Dict[str, float],
                                        market_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """執行投資組合再平衡"""
        try:
            logger.info(f"Executing portfolio rebalance for {portfolio.portfolio_id}")
            
            rebalance_decisions = []
            total_adjustment_needed = 0.0
            
            # 計算每個持倉的調整需求
            for symbol, target_allocation in target_allocations.items():
                current_allocation = portfolio.get_allocation(symbol)
                allocation_diff = target_allocation - current_allocation
                
                if abs(allocation_diff) > self.config.rebalance_threshold:
                    # 需要調整
                    symbol_market_data = market_data.get(symbol, {})
                    current_price = symbol_market_data.get('current_price', 0)
                    
                    if current_price > 0:
                        # 計算需要調整的金額
                        adjustment_amount = float(portfolio.total_value) * allocation_diff
                        adjustment_shares = abs(adjustment_amount) / current_price
                        
                        decision_type = DecisionType.BUY if allocation_diff > 0 else DecisionType.SELL
                        
                        # 創建再平衡決策
                        rebalance_decision = InvestmentDecision(
                            decision_id=f"rebalance_{symbol}_{int(datetime.now().timestamp())}",
                            decision_type=decision_type,
                            target_symbol=symbol,
                            quantity=Decimal(str(adjustment_shares)),
                            price=Decimal(str(current_price)),
                            confidence=DecisionConfidence.HIGH,
                            risk_level=RiskLevel.LOW,
                            expected_return=0.0,
                            expected_risk=0.02,
                            time_horizon=TimeHorizon.MEDIUM_TERM,
                            reasoning=f"再平衡調整：目標配置{target_allocation:.1%}，當前配置{current_allocation:.1%}",
                            supporting_insights=[],
                            market_conditions=await self._create_market_conditions(symbol_market_data),
                            portfolio_impact={
                                'allocation_change': allocation_diff,
                                'amount_change': adjustment_amount
                            },
                            execution_plan={
                                'execution_type': 'market_order',
                                'urgency': 'low'
                            },
                            created_at=datetime.now(timezone.utc)
                        )
                        
                        rebalance_decisions.append(rebalance_decision)
                        total_adjustment_needed += abs(allocation_diff)
            
            return {
                'rebalance_completed': True,
                'decisions_generated': len(rebalance_decisions),
                'total_adjustment_needed': total_adjustment_needed,
                'rebalance_decisions': [decision.to_dict() for decision in rebalance_decisions],
                'execution_summary': {
                    'buy_orders': len([d for d in rebalance_decisions if d.decision_type == DecisionType.BUY]),
                    'sell_orders': len([d for d in rebalance_decisions if d.decision_type == DecisionType.SELL]),
                    'total_orders': len(rebalance_decisions)
                }
            }
            
        except Exception as e:
            logger.error(f"Portfolio rebalance failed: {e}")
            return {
                'rebalance_completed': False,
                'error': str(e)
            }
    
    def evaluate_decision_performance(self) -> Dict[str, Any]:
        """評估決策性能"""
        try:
            if not self.decision_history:
                return {'no_decisions': True}
            
            recent_decisions = list(self.decision_history)[-100:]  # 最近100個決策
            
            # 基本統計
            total_decisions = len(recent_decisions)
            decision_types = defaultdict(int)
            confidence_distribution = defaultdict(int)
            risk_distribution = defaultdict(int)
            
            for decision in recent_decisions:
                decision_types[decision.decision_type.value] += 1
                confidence_distribution[decision.confidence.value] += 1
                risk_distribution[decision.risk_level.value] += 1
            
            # 收益統計
            returns = []
            for decision in recent_decisions:
                if decision.decision_id in self.execution_results:
                    result = self.execution_results[decision.decision_id]
                    returns.append(result.get('return', 0.0))
            
            avg_return = np.mean(returns) if returns else 0.0
            return_std = np.std(returns) if len(returns) > 1 else 0.0
            win_rate = len([r for r in returns if r > 0]) / len(returns) if returns else 0.0
            
            # 風險調整收益
            sharpe_ratio = (avg_return - self.config.risk_free_rate) / return_std if return_std > 0 else 0.0
            
            # 多因子模型性能
            factor_performance = {}
            if self.multi_factor_model:
                for factor in self.multi_factor_model.factor_weights:
                    factor_performance[factor] = {
                        'weight': self.multi_factor_model.factor_weights[factor],
                        'recent_performance': np.mean(
                            self.multi_factor_model.factor_performance.get(factor, [0])[-10:]
                        )
                    }
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'evaluation_period': f"最近{total_decisions}個決策",
                'decision_statistics': {
                    'total_decisions': total_decisions,
                    'decision_types': dict(decision_types),
                    'confidence_distribution': dict(confidence_distribution),
                    'risk_distribution': dict(risk_distribution)
                },
                'return_statistics': {
                    'average_return': avg_return,
                    'return_volatility': return_std,
                    'win_rate': win_rate,
                    'sharpe_ratio': sharpe_ratio,
                    'total_returns_analyzed': len(returns)
                },
                'factor_performance': factor_performance,
                'overall_performance_score': self._calculate_performance_score(
                    avg_return, win_rate, sharpe_ratio
                )
            }
            
        except Exception as e:
            logger.error(f"Decision performance evaluation failed: {e}")
            return {
                'evaluation_failed': True,
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    async def _build_decision_tree(self):
        """構建決策樹"""
        
        # 根節點：市場條件檢查
        market_condition_node = DecisionNode(
            node_id="market_condition",
            condition=lambda ctx: ctx.get('market_data', {}).get('volatility', 0.2) < 0.3,
            action=lambda ctx: "low_volatility_market"
        )
        
        # 買入條件節點
        buy_condition_node = DecisionNode(
            node_id="buy_condition",
            condition=lambda ctx: ctx.get('decision_score', 0) > 0.3,
            action=lambda ctx: DecisionType.BUY
        )
        
        # 賣出條件節點
        sell_condition_node = DecisionNode(
            node_id="sell_condition",
            condition=lambda ctx: ctx.get('decision_score', 0) < -0.3,
            action=lambda ctx: DecisionType.SELL
        )
        
        # 持有條件節點
        hold_condition_node = DecisionNode(
            node_id="hold_condition",
            condition=lambda ctx: True,  # 默認條件
            action=lambda ctx: DecisionType.HOLD
        )
        
        # 構建樹結構
        market_condition_node.children = [buy_condition_node, sell_condition_node, hold_condition_node]
        
        self.decision_tree = market_condition_node
    
    async def _create_market_conditions(self, market_data: Dict[str, Any]) -> MarketCondition:
        """創建市場條件"""
        return MarketCondition(
            timestamp=datetime.now(timezone.utc),
            market_regime=market_data.get('market_regime', 'sideways'),
            volatility_level=market_data.get('volatility', 0.2),
            liquidity_level=market_data.get('liquidity', 1.0),
            sentiment_score=market_data.get('sentiment', 0.5),
            trend_strength=market_data.get('trend_strength', 0.0),
            support_resistance=market_data.get('support_resistance', {}),
            economic_indicators=market_data.get('economic_indicators', {}),
            sector_performance=market_data.get('sector_performance', {})
        )
    
    def _map_float_to_confidence(self, confidence_float: float) -> DecisionConfidence:
        """映射浮點數到置信度等級"""
        if confidence_float >= 0.9:
            return DecisionConfidence.VERY_HIGH
        elif confidence_float >= 0.75:
            return DecisionConfidence.HIGH
        elif confidence_float >= 0.6:
            return DecisionConfidence.MEDIUM
        elif confidence_float >= 0.4:
            return DecisionConfidence.LOW
        else:
            return DecisionConfidence.VERY_LOW
    
    def _map_risk_score_to_level(self, risk_score: float) -> RiskLevel:
        """映射風險分數到風險等級"""
        if risk_score < 0.1:
            return RiskLevel.VERY_LOW
        elif risk_score < 0.2:
            return RiskLevel.LOW
        elif risk_score < 0.3:
            return RiskLevel.MEDIUM
        elif risk_score < 0.4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.VERY_HIGH
    
    def _determine_time_horizon(self, decision_evaluation: Dict[str, Any],
                               market_conditions: MarketCondition) -> TimeHorizon:
        """確定時間範圍"""
        
        decision_strength = decision_evaluation.get('strength', 0.5)
        volatility = market_conditions.volatility_level
        
        if decision_strength > 0.8 and volatility < 0.15:
            return TimeHorizon.LONG_TERM
        elif decision_strength > 0.6:
            return TimeHorizon.MEDIUM_TERM
        elif decision_strength > 0.4:
            return TimeHorizon.SHORT_TERM
        else:
            return TimeHorizon.INTRADAY
    
    def _generate_reasoning(self, decision_evaluation: Dict[str, Any],
                           risk_assessment: Dict[str, float]) -> str:
        """生成決策推理"""
        
        decision_type = decision_evaluation['decision_type']
        strength = decision_evaluation.get('strength', 0.5)
        supporting_factors = decision_evaluation.get('supporting_factors', [])
        
        reasoning_parts = [
            f"決策類型：{decision_type.value}",
            f"決策強度：{strength:.2f}",
            f"總風險評估：{risk_assessment['total_risk']:.2f}"
        ]
        
        if supporting_factors:
            reasoning_parts.append(f"支撐因子：{', '.join(supporting_factors)}")
        
        return " | ".join(reasoning_parts)
    
    async def _calculate_portfolio_impact(self, decision_type: DecisionType,
                                        position_size: float,
                                        portfolio: Optional[Portfolio]) -> Dict[str, Any]:
        """計算投資組合影響"""
        
        if not portfolio:
            return {'no_portfolio': True}
        
        impact = {
            'position_size_change': position_size,
            'cash_impact': -position_size * 100000,  # 假設價格
            'allocation_change': position_size,
            'risk_impact': position_size * 0.2,  # 簡化風險計算
            'expected_return_impact': position_size * 0.1
        }
        
        return impact
    
    async def _create_execution_plan(self, decision_type: DecisionType,
                                   market_conditions: MarketCondition) -> Dict[str, Any]:
        """創建執行計劃"""
        
        execution_plan = {
            'execution_type': 'market_order',
            'urgency': 'normal',
            'time_in_force': 'day',
            'execution_conditions': {}
        }
        
        # 基於市場條件調整執行計劃
        if market_conditions.volatility_level > 0.3:
            execution_plan['execution_type'] = 'limit_order'
            execution_plan['urgency'] = 'low'
        
        if market_conditions.liquidity_level < 0.5:
            execution_plan['execution_conditions']['min_volume'] = 1000000
            execution_plan['time_in_force'] = 'good_till_cancelled'
        
        return execution_plan
    
    def _update_performance_stats(self, decision: InvestmentDecision):
        """更新性能統計"""
        self.performance_stats['total_decisions'] += 1
        
        # 其他統計將在決策執行結果返回時更新
        
    async def _perform_adaptive_learning(self, decision: InvestmentDecision, context: Dict[str, Any]):
        """執行自適應學習"""
        
        if not self.adaptive_learner:
            return
        
        try:
            # 創建學習經驗
            market_state = MarketState(
                timestamp=decision.created_at,
                market_data=context.get('market_data', {}),
                technical_indicators=context.get('technical_indicators', {}),
                sentiment_scores=context.get('sentiment_scores', {}),
                volatility_metrics=context.get('volatility_metrics', {}),
                macro_factors=context.get('macro_factors', {}),
                regime_indicators=context.get('regime_indicators', {})
            )
            
            action = Action(
                action_id=decision.decision_id,
                action_type=decision.decision_type.value,
                parameters=decision.execution_plan,
                confidence=float(decision.quantity),
                expected_reward=decision.expected_return,
                risk_level=decision.expected_risk
            )
            
            # 模擬獎勵（實際應用中應基於真實執行結果）
            reward = decision.expected_return * 0.8  # 假設實現80%的預期收益
            
            experience = Experience(
                state=market_state,
                action=action,
                reward=reward,
                next_state=None,
                done=False,
                timestamp=decision.created_at
            )
            
            # 執行學習
            await self.adaptive_learner.continuous_learning([experience.to_dict()])
            
        except Exception as e:
            logger.warning(f"Adaptive learning failed: {e}")
    
    def _calculate_performance_score(self, avg_return: float, win_rate: float, sharpe_ratio: float) -> float:
        """計算綜合性能分數"""
        
        # 歸一化各指標
        return_score = min(1.0, max(0.0, (avg_return + 0.1) / 0.2))  # -10% to +10% 映射到 0-1
        win_rate_score = win_rate  # 已經是0-1
        sharpe_score = min(1.0, max(0.0, (sharpe_ratio + 1) / 3))  # -1 to +2 映射到 0-1
        
        # 加權平均
        weights = [0.4, 0.3, 0.3]
        scores = [return_score, win_rate_score, sharpe_score]
        
        return sum(w * s for w, s in zip(weights, scores))
    
    def get_engine_statistics(self) -> Dict[str, Any]:
        """獲取引擎統計信息"""
        return {
            'config': self.config.dict(),
            'is_initialized': self.is_initialized,
            'performance_statistics': self.performance_stats,
            'decision_history_length': len(self.decision_history),
            'execution_results_count': len(self.execution_results),
            'components_status': {
                'multi_factor_model': self.multi_factor_model is not None,
                'risk_manager': self.risk_manager is not None,
                'signal_generator': self.signal_generator is not None,
                'decision_tree': self.decision_tree is not None,
                'adaptive_learner': self.adaptive_learner is not None
            },
            'active_signals_count': len(self.signal_generator.get_active_signals()) if self.signal_generator else 0,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# 使用示例和測試函數
async def create_intelligent_decision_engine_example():
    """創建智能決策引擎示例"""
    
    # 創建配置
    config = IntelligentDecisionConfig(
        engine_id="intelligent_decision_v1",
        engine_name="TradingAgents智能決策引擎",
        decision_framework="multi_factor",
        max_position_size=0.1,
        max_portfolio_risk=0.15,
        position_sizing_method=PositionSizingMethod.ADAPTIVE,
        signal_generation_enabled=True,
        auto_execution_enabled=False,
        learning_enabled=True
    )
    
    # 創建引擎
    engine = IntelligentDecisionEngine(config)
    
    # 初始化
    success = await engine.initialize()
    
    if success:
        logger.info("智能決策引擎創建成功")
        
        # 模擬市場數據
        market_data = {
            'symbol': 'TEST001',
            'current_price': 100.0,
            'volatility': 0.25,
            'beta': 1.2,
            'rsi': 35,
            'macd_signal': 'golden_cross',
            'volume_ratio': 1.8,
            'support_level': 95,
            'resistance_level': 105,
            'market_regime': 'bull',
            'liquidity': 0.8,
            'sentiment': 0.7,
            'trend_strength': 0.6
        }
        
        # 模擬基本面數據
        fundamental_data = {
            'pe_ratio': 18,
            'industry_pe': 22,
            'roe': 0.16,
            'revenue_growth': 0.12,
            'debt_ratio': 0.35,
            'fcf_yield': 0.08
        }
        
        # 模擬情緒數據
        sentiment_data = {
            'news_sentiment': 0.75,
            'social_sentiment': 0.68,
            'analyst_rating': 4,
            'institutional_flow': 0.08,
            'insider_trading': 0.02
        }
        
        # 模擬宏觀數據
        macro_data = {
            'interest_rate_trend': 'declining',
            'gdp_growth': 0.035,
            'inflation_rate': 0.025,
            'unemployment_rate': 0.042,
            'currency_strength': 'neutral'
        }
        
        # 模擬動能數據
        momentum_data = {
            'price_momentum_20d': 0.08,
            'relative_strength': 75,
            'money_flow': 0.12,
            'sector_momentum': 0.05
        }
        
        # 模擬投資組合
        portfolio = Portfolio(
            portfolio_id="test_portfolio",
            total_value=Decimal('1000000'),
            cash_balance=Decimal('200000'),
            positions={
                'TEST001': {
                    'quantity': 5000,
                    'current_price': 100.0,
                    'cost_basis': 95.0
                }
            },
            target_allocations={'TEST001': 0.5, 'CASH': 0.5},
            risk_metrics={'portfolio_var': 0.12, 'portfolio_volatility': 0.18},
            performance_metrics={'ytd_return': 0.15, 'sharpe_ratio': 1.2},
            last_updated=datetime.now(timezone.utc)
        )
        
        # 創建決策上下文
        context = {
            'market_data': market_data,
            'fundamental_data': fundamental_data,
            'sentiment_data': sentiment_data,
            'macro_data': macro_data,
            'momentum_data': momentum_data,
            'portfolio': portfolio,
            'decision_score': 0.4  # 模擬決策分數
        }
        
        # 生成投資決策
        decision = await engine.generate_investment_decision(context)
        
        # 生成交易信號
        signals = await engine.generate_trading_signals(market_data)
        
        # 執行投資組合再平衡
        target_allocations = {'TEST001': 0.6, 'CASH': 0.4}
        market_data_dict = {'TEST001': market_data}
        rebalance_result = await engine.execute_portfolio_rebalance(
            portfolio, target_allocations, market_data_dict
        )
        
        # 評估決策性能
        performance = engine.evaluate_decision_performance()
        
        # 獲取引擎統計信息
        stats = engine.get_engine_statistics()
        
        return {
            'initialization_success': success,
            'investment_decision': decision.to_dict(),
            'trading_signals': [signal.to_dict() for signal in signals],
            'rebalance_result': rebalance_result,
            'performance_evaluation': performance,
            'engine_statistics': stats
        }
    
    return {'initialization_success': False}


if __name__ == "__main__":
    # 運行示例
    import asyncio
    
    async def main():
        result = await create_intelligent_decision_engine_example()
        print("=== 智能決策引擎測試結果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    asyncio.run(main())