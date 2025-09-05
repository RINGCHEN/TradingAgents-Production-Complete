#!/usr/bin/env python3
"""
Investment Planner - 投資規劃師
天工 (TianGong) - 整合所有分析師結果的智能投資策略規劃師

此分析師專注於：
1. 整合技術面、基本面、新聞、情緒、風險等所有分析師的結果
2. 制定綜合投資策略和目標價格計算
3. 投資組合建議和風險調整後報酬計算
4. 長短期策略區分和時機選擇建議
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType, AnalysisConfidenceLevel

class InvestmentHorizon(Enum):
    """投資期間"""
    SHORT_TERM = "short_term"       # 短期 (1-3個月)
    MEDIUM_TERM = "medium_term"     # 中期 (3-12個月)
    LONG_TERM = "long_term"         # 長期 (1年以上)

class StrategyType(Enum):
    """策略類型"""
    AGGRESSIVE = "aggressive"       # 積極型
    MODERATE = "moderate"          # 穩健型
    CONSERVATIVE = "conservative"   # 保守型
    DEFENSIVE = "defensive"        # 防禦型

@dataclass
class AnalystInput:
    """分析師輸入數據"""
    analyst_id: str
    recommendation: str             # BUY/SELL/HOLD
    confidence: float              # 信心度
    reasoning: List[str]           # 理由
    weight: float                  # 在最終決策中的權重
    technical_indicators: Optional[Dict[str, Any]] = None
    target_price: Optional[float] = None
    risk_factors: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class InvestmentStrategy:
    """投資策略"""
    strategy_type: StrategyType
    investment_horizon: InvestmentHorizon
    target_price: float
    confidence_level: float
    recommended_position_size: float    # 建議部位大小 (%)
    entry_strategy: Dict[str, Any]      # 進場策略
    exit_strategy: Dict[str, Any]       # 出場策略
    risk_management: Dict[str, Any]     # 風險管理
    monitoring_plan: List[str]          # 監控計劃
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['strategy_type'] = self.strategy_type.value
        result['investment_horizon'] = self.investment_horizon.value
        return result

@dataclass
class PortfolioRecommendation:
    """投資組合建議"""
    correlation_analysis: Dict[str, Any]
    diversification_score: float
    suggested_allocation: Dict[str, float]
    rebalancing_frequency: str
    portfolio_risk_level: str
    expected_return: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class InvestmentPlanner(BaseAnalyst):
    """投資規劃師 - 天工優化版"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.analyst_id = 'investment_planner'
        
        # 分析師權重配置
        self.analyst_weights = config.get('analyst_weights', {
            'market_analyst': 0.20,          # 技術分析師
            'fundamentals_analyst': 0.25,    # 基本面分析師
            'news_analyst': 0.15,           # 新聞分析師
            'sentiment_analyst': 0.15,       # 情緒分析師
            'risk_analyst': 0.15,           # 風險分析師
            'taiwan_market_analyst': 0.10    # 台股專業分析師
        })
        
        # 策略配置
        self.strategy_configs = {
            StrategyType.AGGRESSIVE: {
                'risk_tolerance': 0.8,
                'target_return': 0.15,
                'max_position_size': 0.15,
                'stop_loss_threshold': 0.12
            },
            StrategyType.MODERATE: {
                'risk_tolerance': 0.6,
                'target_return': 0.10,
                'max_position_size': 0.10,
                'stop_loss_threshold': 0.08
            },
            StrategyType.CONSERVATIVE: {
                'risk_tolerance': 0.4,
                'target_return': 0.06,
                'max_position_size': 0.05,
                'stop_loss_threshold': 0.05
            },
            StrategyType.DEFENSIVE: {
                'risk_tolerance': 0.2,
                'target_return': 0.03,
                'max_position_size': 0.03,
                'stop_loss_threshold': 0.03
            }
        }
        
        self.logger.info(f"投資規劃師初始化完成: {self.analyst_id}")
    
    def get_analysis_type(self) -> AnalysisType:
        """獲取分析類型"""
        return AnalysisType.INVESTMENT_PLANNING
    
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """生成投資規劃提示詞"""
        stock_id = state.stock_id
        
        prompt = f"""
作為資深投資規劃師，請針對股票 {stock_id} 制定綜合投資策略。

我已收集了以下分析師的意見：
- 技術分析師：技術指標和價格趨勢分析
- 基本面分析師：財務數據和企業價值分析
- 新聞分析師：市場事件和新聞影響分析
- 情緒分析師：市場情緒和投資人行為分析
- 風險分析師：風險評估和管理建議

請整合所有分析師意見，制定完整的投資策略，包括：

1. 綜合投資建議 (BUY/SELL/HOLD) 和信心度
2. 目標價格計算和達成時間預估
3. 建議投資策略類型 (積極/穩健/保守/防禦)
4. 適合的投資期間 (短期/中期/長期)
5. 進場和出場策略
6. 風險管理和停損停利設定
7. 投資組合配置建議
8. 監控指標和調整時機

請提供專業、實用的投資規劃建議。
"""
        return prompt.strip()
    
    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """執行投資規劃分析"""
        self.logger.info(f"開始投資規劃分析: {state.stock_id}")
        
        try:
            # 使用天工優化的分析流程
            return await self._execute_analysis_with_optimization(state)
            
        except Exception as e:
            self.logger.error(f"投資規劃分析失敗: {str(e)}")
            return self._create_error_result(state, str(e))
    
    async def _perform_core_analysis(self, state: AnalysisState, model_config) -> AnalysisResult:
        """執行核心投資規劃邏輯"""
        
        # 1. 收集所有分析師結果
        analyst_inputs = await self._collect_analyst_inputs(state)
        
        # 2. 權重調整和一致性檢查
        weighted_inputs = await self._apply_analyst_weights(analyst_inputs)
        
        # 3. 綜合決策計算
        integrated_decision = await self._integrate_analyst_decisions(weighted_inputs, state)
        
        # 4. 投資策略制定
        investment_strategy = await self._formulate_investment_strategy(
            integrated_decision, weighted_inputs, state
        )
        
        # 5. 投資組合建議
        portfolio_recommendation = await self._generate_portfolio_recommendation(
            investment_strategy, state
        )
        
        # 6. LLM 深度策略分析
        llm_analysis = await self._call_llm_strategy_analysis(
            state, integrated_decision, investment_strategy, portfolio_recommendation, model_config
        )
        
        # 7. 最終結果整合
        return await self._integrate_investment_planning_results(
            state, integrated_decision, investment_strategy, 
            portfolio_recommendation, llm_analysis, model_config
        )
    
    async def _collect_analyst_inputs(self, state: AnalysisState) -> List[AnalystInput]:
        """收集所有分析師的輸入結果"""
        self.logger.info("收集分析師輸入")
        
        # 模擬從其他分析師收集結果
        # 在實際實現中，這裡會調用其他分析師的分析結果
        analyst_inputs = []
        
        # 模擬技術分析師結果
        analyst_inputs.append(AnalystInput(
            analyst_id='market_analyst',
            recommendation='BUY',
            confidence=0.75,
            reasoning=['技術指標顯示上升趨勢', 'RSI指標健康', '成交量配合'],
            weight=self.analyst_weights.get('market_analyst', 0.2),
            target_price=620.0,
            technical_indicators={'rsi': 65, 'macd': 'bullish', 'trend': 'up'}
        ))
        
        # 模擬基本面分析師結果
        analyst_inputs.append(AnalystInput(
            analyst_id='fundamentals_analyst',
            recommendation='HOLD',
            confidence=0.68,
            reasoning=['財務指標穩健', 'PE略高但可接受', '營收成長良好'],
            weight=self.analyst_weights.get('fundamentals_analyst', 0.25),
            target_price=600.0,
            technical_indicators={'pe_ratio': 22.5, 'roe': 15.2, 'growth': 0.12}
        ))
        
        # 模擬新聞分析師結果
        analyst_inputs.append(AnalystInput(
            analyst_id='news_analyst',
            recommendation='BUY',
            confidence=0.72,
            reasoning=['產業正面消息', 'AI概念持續發酵', '國際訂單增加'],
            weight=self.analyst_weights.get('news_analyst', 0.15),
            target_price=630.0
        ))
        
        # 模擬情緒分析師結果
        analyst_inputs.append(AnalystInput(
            analyst_id='sentiment_analyst',
            recommendation='HOLD',
            confidence=0.65,
            reasoning=['市場情緒中性', '散戶參與度適中', '法人態度謹慎'],
            weight=self.analyst_weights.get('sentiment_analyst', 0.15),
            target_price=590.0
        ))
        
        # 模擬風險分析師結果
        analyst_inputs.append(AnalystInput(
            analyst_id='risk_analyst',
            recommendation='HOLD',
            confidence=0.85,
            reasoning=['風險指標處於中等水準', '波動率可控', '建議適度控制部位'],
            weight=self.analyst_weights.get('risk_analyst', 0.15),
            target_price=580.0,
            risk_factors=['高波動率風險', '與大盤相關性高']
        ))
        
        # 模擬台股專業分析師結果
        analyst_inputs.append(AnalystInput(
            analyst_id='taiwan_market_analyst',
            recommendation='BUY',
            confidence=0.70,
            reasoning=['外資持續買超', '權值股效應正面', '板塊輪動有利'],
            weight=self.analyst_weights.get('taiwan_market_analyst', 0.1),
            target_price=610.0
        ))
        
        return analyst_inputs
    
    async def _apply_analyst_weights(self, analyst_inputs: List[AnalystInput]) -> List[AnalystInput]:
        """應用分析師權重並進行調整"""
        self.logger.info("應用分析師權重")
        
        # 權重標準化
        total_weight = sum(input.weight for input in analyst_inputs)
        if total_weight > 0:
            for input in analyst_inputs:
                input.weight = input.weight / total_weight
        
        # 根據信心度調整權重
        for input in analyst_inputs:
            confidence_adjustment = input.confidence  # 信心度越高權重越大
            input.weight *= confidence_adjustment
        
        # 重新標準化
        total_adjusted_weight = sum(input.weight for input in analyst_inputs)
        if total_adjusted_weight > 0:
            for input in analyst_inputs:
                input.weight = input.weight / total_adjusted_weight
        
        return analyst_inputs
    
    async def _integrate_analyst_decisions(
        self, 
        weighted_inputs: List[AnalystInput], 
        state: AnalysisState
    ) -> Dict[str, Any]:
        """整合分析師決策"""
        self.logger.info("整合分析師決策")
        
        # 計算加權建議
        recommendation_scores = {'BUY': 0.0, 'SELL': 0.0, 'HOLD': 0.0}
        total_confidence = 0.0
        all_reasoning = []
        all_risk_factors = []
        target_prices = []
        
        for input in weighted_inputs:
            # 累計建議權重
            recommendation_scores[input.recommendation] += input.weight
            
            # 累計信心度 (加權)
            total_confidence += input.confidence * input.weight
            
            # 收集理由
            all_reasoning.extend([f"[{input.analyst_id}] {reason}" for reason in input.reasoning])
            
            # 收集風險因子
            if input.risk_factors:
                all_risk_factors.extend([f"[{input.analyst_id}] {risk}" for risk in input.risk_factors])
            
            # 收集目標價
            if input.target_price:
                target_prices.append({
                    'analyst': input.analyst_id,
                    'price': input.target_price,
                    'weight': input.weight
                })
        
        # 確定最終建議
        final_recommendation = max(recommendation_scores.items(), key=lambda x: x[1])[0]
        
        # 計算加權平均目標價
        if target_prices:
            weighted_target_price = sum(tp['price'] * tp['weight'] for tp in target_prices)
        else:
            # 如果沒有目標價，根據建議類型設定預設值
            current_price = 580.0  # 假設當前價格
            if final_recommendation == 'BUY':
                weighted_target_price = current_price * 1.08  # 上漲8%
            elif final_recommendation == 'SELL':
                weighted_target_price = current_price * 0.95  # 下跌5%
            else:
                weighted_target_price = current_price  # 持平
        
        # 計算決策一致性
        max_score = max(recommendation_scores.values())
        decision_consensus = max_score  # 最高得分即為一致性程度
        
        return {
            'final_recommendation': final_recommendation,
            'confidence': total_confidence,
            'target_price': weighted_target_price,
            'reasoning': all_reasoning[:10],  # 限制理由數量
            'risk_factors': all_risk_factors[:8],  # 限制風險因子數量
            'recommendation_scores': recommendation_scores,
            'decision_consensus': decision_consensus,
            'analyst_count': len(weighted_inputs),
            'target_price_range': {
                'min': min(tp['price'] for tp in target_prices) if target_prices else weighted_target_price * 0.95,
                'max': max(tp['price'] for tp in target_prices) if target_prices else weighted_target_price * 1.05,
                'avg': weighted_target_price
            }
        }
    
    async def _formulate_investment_strategy(
        self,
        integrated_decision: Dict[str, Any],
        weighted_inputs: List[AnalystInput],
        state: AnalysisState
    ) -> InvestmentStrategy:
        """制定投資策略"""
        self.logger.info("制定投資策略")
        
        # 確定策略類型
        strategy_type = self._determine_strategy_type(integrated_decision, weighted_inputs)
        
        # 確定投資期間
        investment_horizon = self._determine_investment_horizon(integrated_decision, weighted_inputs)
        
        # 獲取策略配置
        strategy_config = self.strategy_configs[strategy_type]
        
        # 計算建議部位大小
        position_size = self._calculate_position_size(
            integrated_decision, strategy_config, weighted_inputs
        )
        
        # 制定進場策略
        entry_strategy = self._create_entry_strategy(
            integrated_decision, strategy_type, investment_horizon
        )
        
        # 制定出場策略
        exit_strategy = self._create_exit_strategy(
            integrated_decision, strategy_config, investment_horizon
        )
        
        # 制定風險管理
        risk_management = self._create_risk_management(
            integrated_decision, strategy_config, weighted_inputs
        )
        
        # 制定監控計劃
        monitoring_plan = self._create_monitoring_plan(
            integrated_decision, strategy_type, investment_horizon
        )
        
        return InvestmentStrategy(
            strategy_type=strategy_type,
            investment_horizon=investment_horizon,
            target_price=integrated_decision['target_price'],
            confidence_level=integrated_decision['confidence'],
            recommended_position_size=position_size,
            entry_strategy=entry_strategy,
            exit_strategy=exit_strategy,
            risk_management=risk_management,
            monitoring_plan=monitoring_plan
        )
    
    def _determine_strategy_type(
        self, 
        integrated_decision: Dict[str, Any], 
        weighted_inputs: List[AnalystInput]
    ) -> StrategyType:
        """確定策略類型"""
        
        # 基於決策一致性和信心度確定策略類型
        consensus = integrated_decision['decision_consensus']
        confidence = integrated_decision['confidence']
        
        # 檢查風險分析師的建議
        risk_input = next((inp for inp in weighted_inputs if inp.analyst_id == 'risk_analyst'), None)
        high_risk = False
        if risk_input and risk_input.risk_factors:
            high_risk = len(risk_input.risk_factors) > 3
        
        # 策略類型決定邏輯
        if high_risk or confidence < 0.6:
            return StrategyType.CONSERVATIVE
        elif consensus > 0.7 and confidence > 0.8:
            return StrategyType.AGGRESSIVE
        elif consensus > 0.6 and confidence > 0.7:
            return StrategyType.MODERATE
        else:
            return StrategyType.DEFENSIVE
    
    def _determine_investment_horizon(
        self, 
        integrated_decision: Dict[str, Any], 
        weighted_inputs: List[AnalystInput]
    ) -> InvestmentHorizon:
        """確定投資期間"""
        
        # 檢查技術分析師建議
        technical_input = next((inp for inp in weighted_inputs if inp.analyst_id == 'market_analyst'), None)
        technical_trend = None
        if technical_input and technical_input.technical_indicators:
            technical_trend = technical_input.technical_indicators.get('trend', 'neutral')
        
        # 檢查基本面分析師建議
        fundamental_input = next((inp for inp in weighted_inputs if inp.analyst_id == 'fundamentals_analyst'), None)
        fundamental_growth = None
        if fundamental_input and fundamental_input.technical_indicators:
            fundamental_growth = fundamental_input.technical_indicators.get('growth', 0)
        
        # 投資期間決定邏輯
        if technical_trend == 'up' and integrated_decision['confidence'] > 0.8:
            return InvestmentHorizon.SHORT_TERM
        elif fundamental_growth and fundamental_growth > 0.1:
            return InvestmentHorizon.LONG_TERM
        else:
            return InvestmentHorizon.MEDIUM_TERM
    
    def _calculate_position_size(
        self,
        integrated_decision: Dict[str, Any],
        strategy_config: Dict[str, Any],
        weighted_inputs: List[AnalystInput]
    ) -> float:
        """計算建議部位大小"""
        
        base_position = strategy_config['max_position_size']
        confidence = integrated_decision['confidence']
        consensus = integrated_decision['decision_consensus']
        
        # 根據信心度和一致性調整部位
        confidence_multiplier = confidence
        consensus_multiplier = consensus
        
        # 檢查風險分析師的具體建議
        risk_input = next((inp for inp in weighted_inputs if inp.analyst_id == 'risk_analyst'), None)
        risk_multiplier = 1.0
        if risk_input and risk_input.technical_indicators:
            # 假設風險分析師在technical_indicators中提供了建議部位
            suggested_position = risk_input.technical_indicators.get('suggested_position', base_position)
            risk_multiplier = suggested_position / base_position
        
        # 綜合調整
        adjusted_position = base_position * confidence_multiplier * consensus_multiplier * risk_multiplier
        
        # 確保在合理範圍內
        return max(0.01, min(strategy_config['max_position_size'], adjusted_position))
    
    def _create_entry_strategy(
        self,
        integrated_decision: Dict[str, Any],
        strategy_type: StrategyType,
        investment_horizon: InvestmentHorizon
    ) -> Dict[str, Any]:
        """創建進場策略"""
        
        entry_strategy = {
            'strategy_type': strategy_type.value,
            'timing': 'immediate' if integrated_decision['confidence'] > 0.8 else 'gradual',
            'entry_method': 'market_order' if strategy_type == StrategyType.AGGRESSIVE else 'limit_order'
        }
        
        # 分批進場策略
        if integrated_decision['confidence'] < 0.7:
            entry_strategy.update({
                'scaling_strategy': 'dollar_cost_averaging',
                'scaling_periods': 3,
                'scaling_interval': '1_week'
            })
        
        # 技術面進場條件
        entry_strategy['technical_conditions'] = [
            '突破關鍵阻力位',
            'RSI < 70 (避免超買)',
            '成交量配合'
        ]
        
        # 基本面進場條件
        entry_strategy['fundamental_conditions'] = [
            'PE ratio 合理',
            '財報數據符合預期',
            '產業前景正面'
        ]
        
        return entry_strategy
    
    def _create_exit_strategy(
        self,
        integrated_decision: Dict[str, Any],
        strategy_config: Dict[str, Any],
        investment_horizon: InvestmentHorizon
    ) -> Dict[str, Any]:
        """創建出場策略"""
        
        target_price = integrated_decision['target_price']
        current_price = 580.0  # 假設當前價格
        
        exit_strategy = {
            'target_price': target_price,
            'stop_loss_pct': strategy_config['stop_loss_threshold'],
            'take_profit_strategy': 'scaled_exit'
        }
        
        # 分批出場策略
        if investment_horizon == InvestmentHorizon.LONG_TERM:
            exit_strategy.update({
                'scaling_out_levels': [
                    {'price_target_pct': 0.7, 'position_pct': 0.3},  # 達到70%目標時賣出30%
                    {'price_target_pct': 1.0, 'position_pct': 0.5},  # 達到100%目標時再賣出50%
                    {'price_target_pct': 1.3, 'position_pct': 1.0}   # 達到130%目標時全部賣出
                ]
            })
        
        # 時間停利
        exit_strategy['time_based_exit'] = {
            InvestmentHorizon.SHORT_TERM: '3_months',
            InvestmentHorizon.MEDIUM_TERM: '12_months',
            InvestmentHorizon.LONG_TERM: '24_months'
        }[investment_horizon]
        
        # 技術面出場條件
        exit_strategy['technical_exit_signals'] = [
            'RSI > 80 (超買)',
            '跌破重要支撐位',
            '成交量萎縮且價格下跌'
        ]
        
        return exit_strategy
    
    def _create_risk_management(
        self,
        integrated_decision: Dict[str, Any],
        strategy_config: Dict[str, Any],
        weighted_inputs: List[AnalystInput]
    ) -> Dict[str, Any]:
        """創建風險管理策略"""
        
        risk_management = {
            'position_sizing': {
                'max_position_pct': strategy_config['max_position_size'],
                'recommended_position_pct': integrated_decision.get('recommended_position_size', 0.05)
            },
            'stop_loss': {
                'initial_stop_pct': strategy_config['stop_loss_threshold'],
                'trailing_stop': True,
                'trailing_stop_distance': strategy_config['stop_loss_threshold'] * 0.7
            },
            'diversification': {
                'max_sector_exposure': 0.3,
                'max_single_stock_exposure': strategy_config['max_position_size'],
                'correlation_threshold': 0.7
            }
        }
        
        # 從風險分析師獲取具體風險管理建議
        risk_input = next((inp for inp in weighted_inputs if inp.analyst_id == 'risk_analyst'), None)
        if risk_input and risk_input.risk_factors:
            risk_management['specific_risks'] = risk_input.risk_factors
            risk_management['risk_mitigation'] = [
                '定期檢視投資組合相關性',
                '設定價格預警通知',
                '關注市場波動率變化'
            ]
        
        return risk_management
    
    def _create_monitoring_plan(
        self,
        integrated_decision: Dict[str, Any],
        strategy_type: StrategyType,
        investment_horizon: InvestmentHorizon
    ) -> List[str]:
        """創建監控計劃"""
        
        monitoring_plan = [
            '每日監控股價變化和技術指標',
            '每週檢視新聞和事件影響',
            '每月評估基本面變化',
            '每季度重新評估投資策略'
        ]
        
        # 根據策略類型調整監控頻率
        if strategy_type == StrategyType.AGGRESSIVE:
            monitoring_plan.insert(0, '即時監控重大市場動態')
        
        # 根據投資期間調整監控內容
        if investment_horizon == InvestmentHorizon.LONG_TERM:
            monitoring_plan.extend([
                '年度檢視公司營運策略變化',
                '關注產業長期趨勢發展'
            ])
        
        return monitoring_plan
    
    async def _generate_portfolio_recommendation(
        self,
        investment_strategy: InvestmentStrategy,
        state: AnalysisState
    ) -> PortfolioRecommendation:
        """生成投資組合建議"""
        self.logger.info("生成投資組合建議")
        
        # 模擬相關性分析
        correlation_analysis = {
            'market_correlation': 0.75,
            'sector_correlation': 0.85,
            'similar_stocks': ['2454', '2317', '3008'],
            'correlation_risk': 'medium'
        }
        
        # 計算分散化分數
        diversification_score = self._calculate_diversification_score(investment_strategy)
        
        # 建議配置
        suggested_allocation = {
            state.stock_id: investment_strategy.recommended_position_size,
            'sector_peers': 0.15,
            'international_stocks': 0.20,
            'bonds': 0.25,
            'cash': 0.10,
            'other_sectors': 0.30 - investment_strategy.recommended_position_size
        }
        
        # 重新平衡頻率
        rebalancing_frequency = {
            InvestmentHorizon.SHORT_TERM: '月度',
            InvestmentHorizon.MEDIUM_TERM: '季度',
            InvestmentHorizon.LONG_TERM: '半年度'
        }[investment_strategy.investment_horizon]
        
        # 投資組合風險等級
        portfolio_risk_level = {
            StrategyType.AGGRESSIVE: 'HIGH',
            StrategyType.MODERATE: 'MEDIUM',
            StrategyType.CONSERVATIVE: 'LOW',
            StrategyType.DEFENSIVE: 'VERY_LOW'
        }[investment_strategy.strategy_type]
        
        # 預期報酬
        expected_return = self.strategy_configs[investment_strategy.strategy_type]['target_return']
        
        return PortfolioRecommendation(
            correlation_analysis=correlation_analysis,
            diversification_score=diversification_score,
            suggested_allocation=suggested_allocation,
            rebalancing_frequency=rebalancing_frequency,
            portfolio_risk_level=portfolio_risk_level,
            expected_return=expected_return
        )
    
    def _calculate_diversification_score(self, investment_strategy: InvestmentStrategy) -> float:
        """計算分散化分數"""
        # 簡化的分散化分數計算
        position_size = investment_strategy.recommended_position_size
        
        if position_size <= 0.05:
            return 0.9  # 部位小，分散化佳
        elif position_size <= 0.10:
            return 0.7  # 部位中等
        else:
            return 0.5  # 部位較大，分散化較差
    
    async def _call_llm_strategy_analysis(
        self,
        state: AnalysisState,
        integrated_decision: Dict[str, Any],
        investment_strategy: InvestmentStrategy,
        portfolio_recommendation: PortfolioRecommendation,
        model_config
    ) -> Dict[str, Any]:
        """呼叫LLM進行深度策略分析"""
        
        try:
            # 模擬LLM分析
            await asyncio.sleep(1.5)  # 模擬處理時間
            
            # 基於整合決策生成LLM分析
            llm_analysis = {
                'strategic_assessment': self._generate_strategic_assessment(integrated_decision, investment_strategy),
                'investment_rationale': self._generate_investment_rationale(integrated_decision),
                'risk_reward_analysis': self._generate_risk_reward_analysis(investment_strategy, integrated_decision),
                'market_timing': self._assess_market_timing(integrated_decision),
                'alternative_scenarios': self._generate_alternative_scenarios(integrated_decision),
                'confidence': integrated_decision['confidence'],
                'recommendation_strength': self._assess_recommendation_strength(integrated_decision)
            }
            
            return llm_analysis
            
        except Exception as e:
            self.logger.error(f"LLM策略分析調用失敗: {str(e)}")
            return {
                'strategic_assessment': '無法完成深度策略分析',
                'investment_rationale': ['分析過程中發生錯誤'],
                'confidence': 0.5,
                'error': str(e)
            }
    
    def _generate_strategic_assessment(
        self, 
        integrated_decision: Dict[str, Any], 
        investment_strategy: InvestmentStrategy
    ) -> str:
        """生成策略評估"""
        
        recommendation = integrated_decision['final_recommendation']
        confidence = integrated_decision['confidence']
        strategy_type = investment_strategy.strategy_type.value
        
        if recommendation == 'BUY' and confidence > 0.7:
            return f"強烈建議買入，採用{strategy_type}策略，多項指標顯示正面投資機會"
        elif recommendation == 'BUY':
            return f"謹慎建議買入，採用{strategy_type}策略，需密切監控市場變化"
        elif recommendation == 'SELL':
            return f"建議減持或出清部位，風險因子增加，不符合當前市場環境"
        else:
            return f"建議持有觀望，採用{strategy_type}策略，等待更明確的市場信號"
    
    def _generate_investment_rationale(self, integrated_decision: Dict[str, Any]) -> List[str]:
        """生成投資理由"""
        return integrated_decision.get('reasoning', ['綜合多位分析師意見制定'])
    
    def _generate_risk_reward_analysis(
        self, 
        investment_strategy: InvestmentStrategy, 
        integrated_decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成風險報酬分析"""
        
        current_price = 580.0
        target_price = investment_strategy.target_price
        upside_potential = (target_price - current_price) / current_price
        
        return {
            'upside_potential': upside_potential,
            'downside_risk': investment_strategy.risk_management['stop_loss']['initial_stop_pct'],
            'risk_reward_ratio': upside_potential / investment_strategy.risk_management['stop_loss']['initial_stop_pct'],
            'expected_volatility': 'medium',
            'probability_of_success': integrated_decision['confidence']
        }
    
    def _assess_market_timing(self, integrated_decision: Dict[str, Any]) -> str:
        """評估市場時機"""
        
        consensus = integrated_decision['decision_consensus']
        
        if consensus > 0.8:
            return '市場時機佳，各項指標一致性高'
        elif consensus > 0.6:
            return '市場時機適中，需注意部分分歧意見'
        else:
            return '市場時機不明朗，建議等待更清晰信號'
    
    def _generate_alternative_scenarios(self, integrated_decision: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成替代情境"""
        
        scenarios = []
        
        # 樂觀情境
        scenarios.append({
            'scenario': '樂觀情境',
            'probability': 0.3,
            'key_drivers': ['技術創新突破', '市場需求強勁', '政策支持'],
            'price_target': integrated_decision['target_price'] * 1.15,
            'timeline': '6-12個月'
        })
        
        # 基準情境
        scenarios.append({
            'scenario': '基準情境',
            'probability': 0.5,
            'key_drivers': ['穩定營運', '市場環境平穩', '基本面支撐'],
            'price_target': integrated_decision['target_price'],
            'timeline': '3-9個月'
        })
        
        # 悲觀情境
        scenarios.append({
            'scenario': '悲觀情境',
            'probability': 0.2,
            'key_drivers': ['競爭加劇', '需求下滑', '總經逆風'],
            'price_target': integrated_decision['target_price'] * 0.85,
            'timeline': '1-6個月'
        })
        
        return scenarios
    
    def _assess_recommendation_strength(self, integrated_decision: Dict[str, Any]) -> str:
        """評估建議強度"""
        
        consensus = integrated_decision['decision_consensus']
        confidence = integrated_decision['confidence']
        
        if consensus > 0.8 and confidence > 0.8:
            return 'VERY_STRONG'
        elif consensus > 0.7 and confidence > 0.7:
            return 'STRONG'
        elif consensus > 0.6 and confidence > 0.6:
            return 'MODERATE'
        else:
            return 'WEAK'
    
    async def _integrate_investment_planning_results(
        self,
        state: AnalysisState,
        integrated_decision: Dict[str, Any],
        investment_strategy: InvestmentStrategy,
        portfolio_recommendation: PortfolioRecommendation,
        llm_analysis: Dict[str, Any],
        model_config
    ) -> AnalysisResult:
        """整合投資規劃結果"""
        
        # 最終建議和信心度
        recommendation = integrated_decision['final_recommendation']
        confidence = integrated_decision['confidence']
        
        # 整合所有理由
        reasoning = []
        reasoning.extend(llm_analysis.get('investment_rationale', []))
        reasoning.append(f"策略類型: {investment_strategy.strategy_type.value}")
        reasoning.append(f"投資期間: {investment_strategy.investment_horizon.value}")
        reasoning.append(f"建議部位: {investment_strategy.recommended_position_size:.1%}")
        
        # 整合風險因子
        risk_factors = integrated_decision.get('risk_factors', [])
        risk_factors.append(f"停損設定: {investment_strategy.risk_management['stop_loss']['initial_stop_pct']:.1%}")
        risk_factors.append(f"投資組合風險等級: {portfolio_recommendation.portfolio_risk_level}")
        
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation=recommendation,
            confidence=confidence,
            confidence_level=AnalysisConfidenceLevel.HIGH if confidence > 0.7 else AnalysisConfidenceLevel.MODERATE,
            target_price=investment_strategy.target_price,
            reasoning=reasoning,
            risk_factors=risk_factors,
            technical_indicators={
                'integrated_decision': integrated_decision,
                'investment_strategy': investment_strategy.to_dict(),
                'portfolio_recommendation': portfolio_recommendation.to_dict(),
                'llm_analysis': llm_analysis,
                'analyst_inputs_summary': {
                    'total_analysts': integrated_decision['analyst_count'],
                    'decision_consensus': integrated_decision['decision_consensus'],
                    'recommendation_scores': integrated_decision['recommendation_scores']
                }
            },
            model_used=model_config.model_name if hasattr(model_config, 'model_name') else 'investment_planning_model'
        )

# 便利函數
async def create_investment_plan(
    stock_id: str,
    analyst_results: List[AnalysisResult] = None,
    user_context: Dict[str, Any] = None,
    config: Dict[str, Any] = None
) -> AnalysisResult:
    """快速創建投資計劃"""
    
    if config is None:
        config = {
            'analyst_weights': {
                'market_analyst': 0.20,
                'fundamentals_analyst': 0.25,
                'news_analyst': 0.15,
                'sentiment_analyst': 0.15,
                'risk_analyst': 0.15,
                'taiwan_market_analyst': 0.10
            }
        }
    
    planner = InvestmentPlanner(config)
    
    # 創建分析狀態
    state = AnalysisState(
        stock_id=stock_id,
        analysis_date=datetime.now().strftime('%Y-%m-%d'),
        user_context=user_context
    )
    
    # 如果提供了其他分析師結果，可以在這裡整合
    # TODO: 實現從analyst_results參數整合真實分析師結果
    
    return await planner.analyze(state)

if __name__ == "__main__":
    # 測試腳本
    async def test_investment_planner():
        print("測試投資規劃師")
        
        # 測試台積電投資規劃
        result = await create_investment_plan(
            "2330", 
            user_context={'user_id': 'test_user', 'membership_tier': 'DIAMOND'}
        )
        
        print(f"股票: {result.stock_id}")
        print(f"投資建議: {result.recommendation}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"目標價: ${result.target_price:.2f}")
        
        print(f"投資策略:")
        for reason in result.reasoning:
            print(f"  - {reason}")
        
        print(f"風險管理:")
        for risk in result.risk_factors:
            print(f"  - {risk}")
        
        if result.technical_indicators:
            strategy = result.technical_indicators.get('investment_strategy', {})
            print(f"\n策略詳情:")
            print(f"  策略類型: {strategy.get('strategy_type', 'UNKNOWN')}")
            print(f"  投資期間: {strategy.get('investment_horizon', 'UNKNOWN')}")
            print(f"  建議部位: {strategy.get('recommended_position_size', 0):.1%}")
            
            portfolio = result.technical_indicators.get('portfolio_recommendation', {})
            print(f"  組合風險: {portfolio.get('portfolio_risk_level', 'UNKNOWN')}")
            print(f"  預期報酬: {portfolio.get('expected_return', 0):.1%}")
        
        print("投資規劃師測試完成!")
    
    asyncio.run(test_investment_planner())