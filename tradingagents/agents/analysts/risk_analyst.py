#!/usr/bin/env python3
"""
Risk Analyst - 風險分析師
天工 (TianGong) - 專業風險評估與管理智能分析師

此分析師專注於：
1. 波動率分析和 VaR (風險價值) 計算
2. 相關性分析和系統性風險評估
3. 停損停利建議和風險管理策略
4. 市場風險預警和投資組合優化建議
"""

import asyncio
import json
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import math

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType, AnalysisConfidenceLevel

# ART系統整合
try:
    from ...art.trajectory_collector import TrajectoryCollector, TrajectoryType, DecisionStep
    from ...art.ruler_reward_system import RULERRewardSystem, RewardType
    ART_AVAILABLE = True
    print("INFO: ART基礎系統可用")
    
    # 深度行為學習系統（可選）
    try:
        from ...art.deep_behavior_learning import AdaptiveLearningEngine
        DEEP_LEARNING_AVAILABLE = True
        print("INFO: 深度行為學習系統可用")
    except ImportError as e:
        DEEP_LEARNING_AVAILABLE = False
        print(f"WARNING: 深度行為學習系統不可用: {e}")
        AdaptiveLearningEngine = None
        
except ImportError as e:
    ART_AVAILABLE = False
    DEEP_LEARNING_AVAILABLE = False
    print(f"WARNING: ART系統不可用: {e}")

@dataclass
class RiskMetrics:
    """風險指標數據類"""
    volatility_daily: float         # 日波動率
    volatility_annual: float        # 年化波動率
    var_95: float                   # 95% 風險價值 (1天)
    var_99: float                   # 99% 風險價值 (1天)
    cvar_95: float                  # 95% 條件風險價值
    max_drawdown: float             # 最大回撤
    sharpe_ratio: Optional[float]    # 夏普比率
    beta: Optional[float]            # Beta值
    correlation_with_market: float   # 與大盤相關性
    downside_deviation: float       # 下行標準差
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class RiskScenario:
    """風險情境分析"""
    scenario_name: str              # 情境名稱
    probability: float              # 發生機率
    expected_loss: float            # 預期損失
    max_loss: float                 # 最大損失
    recovery_time_days: int         # 預期復原時間
    mitigation_strategies: List[str] # 風險緩解策略
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class RiskAnalyst(BaseAnalyst):
    """風險分析師 - 天工優化版"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.analyst_id = 'risk_analyst'
        
        # 風險分析參數
        self.confidence_levels = [0.90, 0.95, 0.99]
        self.risk_free_rate = config.get('risk_free_rate', 0.01)  # 無風險利率
        self.market_beta_benchmark = config.get('market_benchmark', 'TAIEX')
        
        # 風險閾值設定
        self.high_risk_thresholds = {
            'volatility_annual': 0.30,  # 年化波動率30%以上
            'var_95_pct': 0.05,         # VaR超過5%
            'max_drawdown': 0.20,       # 最大回撤20%以上
            'correlation': 0.80         # 與大盤相關性80%以上
        }
        
        # ART系統初始化
        if ART_AVAILABLE:
            try:
                self.trajectory_collector = TrajectoryCollector(
                    agent_id=self.analyst_id,
                    config=config.get('art_config', {})
                )
                self.reward_system = RULERRewardSystem(
                    config=config.get('reward_config', {})
                )
                
                # 深度行為學習系統（如果可用）
                if DEEP_LEARNING_AVAILABLE and AdaptiveLearningEngine:
                    self.behavior_engine = AdaptiveLearningEngine(
                        config=config.get('behavior_config', {})
                    )
                else:
                    self.behavior_engine = None
                self.art_enabled = True
                self.logger.info("ART系統整合完成")
            except Exception as e:
                self.logger.warning(f"ART系統初始化失敗: {e}")
                self.art_enabled = False
        else:
            self.art_enabled = False
            self.logger.info("ART系統未可用，使用標準模式")
        
        # 個人化風險偏好記錄
        self.user_risk_profiles: Dict[str, Dict[str, Any]] = {}
        self.risk_learning_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self.logger.info(f"風險分析師初始化完成: {self.analyst_id}")
    
    def get_analysis_type(self) -> AnalysisType:
        """獲取分析類型"""
        return AnalysisType.RISK_ASSESSMENT
    
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """生成風險分析提示詞"""
        stock_id = state.stock_id
        
        # 建構上下文資訊
        context_info = []
        if state.stock_data:
            context_info.append("股價歷史數據")
        if state.financial_data:
            context_info.append("財務數據")
        if state.market_data:
            context_info.append("市場數據")
        
        prompt = f"""
作為專業風險分析師，請針對股票 {stock_id} 進行全面風險評估。

可用數據: {', '.join(context_info) if context_info else '基本股價數據'}

請分析以下風險維度：
1. 市場風險：波動率、VaR、相關性分析
2. 流動性風險：交易量、買賣價差
3. 信用風險：財務健康度、債務風險
4. 營運風險：業務集中度、競爭風險
5. 系統性風險：產業風險、總經風險

輸出格式要求：
- 風險等級評估 (LOW/MEDIUM/HIGH/CRITICAL)
- 具體風險數值和指標
- 風險情境分析
- 停損停利建議
- 風險管理策略

請提供專業、量化的風險分析報告。
"""
        return prompt.strip()
    
    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """執行風險分析"""
        self.logger.info(f"開始風險分析: {state.stock_id}")
        
        try:
            # 使用天工優化的分析流程
            return await self._execute_analysis_with_optimization(state)
            
        except Exception as e:
            self.logger.error(f"風險分析失敗: {str(e)}")
            return self._create_error_result(state, str(e))
    
    async def _perform_core_analysis(self, state: AnalysisState, model_config) -> AnalysisResult:
        """執行核心風險分析邏輯 - ART增強版"""
        
        # ART: 記錄分析開始軌跡
        if self.art_enabled:
            await self._record_analysis_start(state)
        
        # 1. 收集和處理數據
        risk_data = await self._collect_risk_data(state)
        
        # ART: 應用個人化風險偏好
        if self.art_enabled and state.user_id:
            risk_data = await self._apply_personalized_risk_preferences(state.user_id, risk_data)
        
        # 2. 計算風險指標
        risk_metrics = await self._calculate_risk_metrics(risk_data)
        
        # 3. 風險情境分析
        risk_scenarios = await self._analyze_risk_scenarios(risk_data, risk_metrics)
        
        # 4. 生成風險管理建議
        risk_management = await self._generate_risk_management_strategies(risk_metrics, risk_scenarios)
        
        # ART: 個人化風險建議調整
        if self.art_enabled and state.user_id:
            risk_management = await self._personalize_risk_recommendations(state.user_id, risk_management, risk_metrics)
        
        # 5. 呼叫 LLM 進行深度分析
        llm_analysis = await self._call_llm_risk_analysis(state, risk_metrics, risk_scenarios, model_config)
        
        # 6. 整合分析結果
        result = await self._integrate_risk_analysis_results(
            state, risk_metrics, risk_scenarios, risk_management, llm_analysis, model_config
        )
        
        # ART: 記錄分析完成並學習
        if self.art_enabled:
            await self._record_analysis_completion(state, result)
        
        return result
    
    async def _collect_risk_data(self, state: AnalysisState) -> Dict[str, Any]:
        """收集風險分析所需數據"""
        self.logger.info("收集風險分析數據")
        
        risk_data = {
            'stock_id': state.stock_id,
            'analysis_date': state.analysis_date,
            'price_history': [],
            'volume_history': [],
            'market_data': {},
            'financial_ratios': {},
        }
        
        try:
            # 處理股價數據
            if state.stock_data:
                risk_data.update(self._process_stock_data_for_risk(state.stock_data))
            
            # 處理財務數據
            if state.financial_data:
                risk_data['financial_ratios'] = self._extract_financial_risk_ratios(state.financial_data)
            
            # 處理市場數據
            if state.market_data:
                risk_data['market_data'] = state.market_data
                
            # 補充缺失數據（模擬）
            if not risk_data['price_history']:
                risk_data.update(await self._simulate_price_data(state.stock_id))
                
        except Exception as e:
            self.logger.error(f"數據收集失敗: {str(e)}")
            # 使用模擬數據
            risk_data.update(await self._simulate_price_data(state.stock_id))
        
        return risk_data
    
    def _process_stock_data_for_risk(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """處理股價數據用於風險分析"""
        processed_data = {}
        
        # 提取價格序列
        if 'price_history' in stock_data:
            prices = stock_data['price_history']
            processed_data['price_history'] = [p.get('close', p.get('price', 0)) for p in prices]
            processed_data['volume_history'] = [p.get('volume', 0) for p in prices]
            processed_data['dates'] = [p.get('date', '') for p in prices]
        
        # 提取當前價格
        if 'current_price' in stock_data:
            processed_data['current_price'] = stock_data['current_price']
        
        return processed_data
    
    def _extract_financial_risk_ratios(self, financial_data: Dict[str, Any]) -> Dict[str, float]:
        """提取財務風險相關比率"""
        ratios = {}
        
        try:
            # 債務相關比率
            ratios['debt_to_equity'] = financial_data.get('debt_to_equity_ratio', 0.0)
            ratios['debt_to_assets'] = financial_data.get('debt_to_assets_ratio', 0.0)
            ratios['interest_coverage'] = financial_data.get('interest_coverage_ratio', 0.0)
            
            # 流動性比率
            ratios['current_ratio'] = financial_data.get('current_ratio', 0.0)
            ratios['quick_ratio'] = financial_data.get('quick_ratio', 0.0)
            
            # 獲利能力比率
            ratios['roe'] = financial_data.get('roe', 0.0)
            ratios['roa'] = financial_data.get('roa', 0.0)
            ratios['profit_margin'] = financial_data.get('net_profit_margin', 0.0)
            
        except Exception as e:
            self.logger.warning(f"財務比率提取失敗: {str(e)}")
        
        return ratios
    
    async def _simulate_price_data(self, stock_id: str) -> Dict[str, Any]:
        """模擬價格數據（當真實數據不可用時）"""
        self.logger.info("使用模擬數據進行風險分析")
        
        # 模擬60天的價格數據
        np.random.seed(hash(stock_id) % 1000)  # 根據股票代碼設定種子，確保一致性
        
        base_price = 100.0
        returns = np.random.normal(0.001, 0.02, 60)  # 平均日報酬0.1%，波動率2%
        
        prices = [base_price]
        for r in returns:
            prices.append(prices[-1] * (1 + r))
        
        # 模擬交易量
        volumes = np.random.randint(100000, 1000000, 61).tolist()
        
        return {
            'price_history': prices,
            'volume_history': volumes,
            'current_price': prices[-1],
            'dates': [(datetime.now() - timedelta(days=60-i)).strftime('%Y-%m-%d') for i in range(61)]
        }
    
    async def _calculate_risk_metrics(self, risk_data: Dict[str, Any]) -> RiskMetrics:
        """計算風險指標"""
        self.logger.info("計算風險指標")
        
        prices = risk_data.get('price_history', [])
        if len(prices) < 2:
            # 返回預設風險指標
            return RiskMetrics(
                volatility_daily=0.02,
                volatility_annual=0.02 * math.sqrt(252),
                var_95=0.03,
                var_99=0.05,
                cvar_95=0.04,
                max_drawdown=0.10,
                sharpe_ratio=0.5,
                beta=1.0,
                correlation_with_market=0.7,
                downside_deviation=0.015
            )
        
        # 計算日報酬率
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0:
                daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(daily_return)
        
        if not returns:
            returns = [0.0]
        
        returns = np.array(returns)
        
        # 基本統計
        daily_vol = np.std(returns)
        annual_vol = daily_vol * math.sqrt(252)
        
        # VaR 計算
        var_95 = np.percentile(returns, 5) * -1  # 95% VaR
        var_99 = np.percentile(returns, 1) * -1  # 99% VaR
        
        # CVaR (條件風險價值)
        tail_losses = returns[returns <= -var_95]
        cvar_95 = np.mean(tail_losses) * -1 if len(tail_losses) > 0 else var_95
        
        # 最大回撤
        max_drawdown = self._calculate_max_drawdown(prices)
        
        # 夏普比率
        excess_returns = returns - self.risk_free_rate / 252
        sharpe_ratio = np.mean(excess_returns) / np.std(excess_returns) if np.std(excess_returns) > 0 else 0.0
        
        # Beta值（模擬市場數據）
        market_returns = np.random.normal(0.0005, 0.015, len(returns))
        beta = np.cov(returns, market_returns)[0,1] / np.var(market_returns) if np.var(market_returns) > 0 else 1.0
        
        # 與市場相關性
        correlation = np.corrcoef(returns, market_returns)[0,1] if len(returns) > 1 else 0.7
        
        # 下行標準差
        negative_returns = returns[returns < 0]
        downside_deviation = np.std(negative_returns) if len(negative_returns) > 0 else daily_vol * 0.7
        
        return RiskMetrics(
            volatility_daily=daily_vol,
            volatility_annual=annual_vol,
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            beta=beta,
            correlation_with_market=correlation,
            downside_deviation=downside_deviation
        )
    
    def _calculate_max_drawdown(self, prices: List[float]) -> float:
        """計算最大回撤"""
        if len(prices) < 2:
            return 0.0
        
        peak = prices[0]
        max_dd = 0.0
        
        for price in prices[1:]:
            if price > peak:
                peak = price
            else:
                drawdown = (peak - price) / peak
                if drawdown > max_dd:
                    max_dd = drawdown
        
        return max_dd
    
    async def _analyze_risk_scenarios(
        self, 
        risk_data: Dict[str, Any], 
        risk_metrics: RiskMetrics
    ) -> List[RiskScenario]:
        """風險情境分析"""
        self.logger.info("進行風險情境分析")
        
        scenarios = []
        current_price = risk_data.get('current_price', 100.0)
        
        # 情境 1: 市場修正情境
        market_correction = RiskScenario(
            scenario_name="市場修正情境",
            probability=0.15,  # 15%機率
            expected_loss=current_price * 0.10,  # 預期下跌10%
            max_loss=current_price * 0.20,       # 最大下跌20%
            recovery_time_days=60,
            mitigation_strategies=[
                "設定停損點於8-10%",
                "分散投資降低集中風險",
                "考慮避險工具如選擇權"
            ]
        )
        scenarios.append(market_correction)
        
        # 情境 2: 黑天鵝事件
        black_swan = RiskScenario(
            scenario_name="黑天鵝事件",
            probability=0.05,  # 5%機率
            expected_loss=current_price * 0.25,  # 預期下跌25%
            max_loss=current_price * 0.40,       # 最大下跌40%
            recovery_time_days=180,
            mitigation_strategies=[
                "嚴格控制單一標的投資比重",
                "建立緊急停損機制",
                "保持充足現金部位"
            ]
        )
        scenarios.append(black_swan)
        
        # 情境 3: 高波動情境
        high_volatility = RiskScenario(
            scenario_name="高波動情境",
            probability=0.25,  # 25%機率
            expected_loss=current_price * 0.05,  # 預期下跌5%
            max_loss=current_price * 0.15,       # 最大下跌15%
            recovery_time_days=30,
            mitigation_strategies=[
                "降低部位規模",
                "使用移動停損策略",
                "關注技術面支撐位"
            ]
        )
        scenarios.append(high_volatility)
        
        # 根據股票特性調整情境
        if risk_metrics.volatility_annual > 0.30:
            # 高波動股票，增加風險情境機率
            for scenario in scenarios:
                scenario.probability *= 1.2
                scenario.expected_loss *= 1.1
                scenario.max_loss *= 1.1
        
        return scenarios
    
    async def _generate_risk_management_strategies(
        self,
        risk_metrics: RiskMetrics,
        risk_scenarios: List[RiskScenario]
    ) -> Dict[str, Any]:
        """生成風險管理策略"""
        self.logger.info("生成風險管理策略")
        
        strategies = {
            'position_sizing': self._calculate_optimal_position_size(risk_metrics),
            'stop_loss_suggestions': self._generate_stop_loss_suggestions(risk_metrics, risk_scenarios),
            'take_profit_suggestions': self._generate_take_profit_suggestions(risk_metrics),
            'portfolio_diversification': self._generate_diversification_advice(risk_metrics),
            'hedging_strategies': self._generate_hedging_strategies(risk_metrics),
            'monitoring_alerts': self._generate_monitoring_alerts(risk_metrics)
        }
        
        return strategies
    
    def _calculate_optimal_position_size(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """計算最佳部位大小"""
        # 基於 VaR 和波動率的部位規模建議
        base_position = 0.05  # 基礎部位 5%
        
        # 根據波動率調整
        if risk_metrics.volatility_annual > 0.30:
            volatility_adjustment = 0.7  # 高波動降低部位
        elif risk_metrics.volatility_annual < 0.15:
            volatility_adjustment = 1.3  # 低波動可增加部位
        else:
            volatility_adjustment = 1.0
        
        # 根據 VaR 調整
        var_adjustment = max(0.5, min(1.5, 1 - (risk_metrics.var_95 - 0.02) * 5))
        
        optimal_position = base_position * volatility_adjustment * var_adjustment
        optimal_position = max(0.01, min(0.10, optimal_position))  # 限制在 1-10%
        
        return {
            'recommended_position_pct': optimal_position,
            'max_position_pct': optimal_position * 1.5,
            'conservative_position_pct': optimal_position * 0.7,
            'rationale': f"基於年化波動率 {risk_metrics.volatility_annual:.1%} 和 VaR {risk_metrics.var_95:.1%} 的部位建議"
        }
    
    def _generate_stop_loss_suggestions(
        self,
        risk_metrics: RiskMetrics,
        risk_scenarios: List[RiskScenario]
    ) -> Dict[str, Any]:
        """生成停損建議"""
        # 基於 VaR 的停損點
        var_based_stop = risk_metrics.var_95 * 1.2  # VaR的1.2倍
        
        # 基於波動率的停損點
        volatility_based_stop = risk_metrics.volatility_daily * 2  # 2倍日波動率
        
        # 基於最大回撤的停損點
        drawdown_based_stop = risk_metrics.max_drawdown * 0.6  # 歷史最大回撤的60%
        
        # 綜合建議
        suggested_stop = max(0.03, min(0.15, (var_based_stop + volatility_based_stop + drawdown_based_stop) / 3))
        
        return {
            'suggested_stop_loss_pct': suggested_stop,
            'conservative_stop_loss_pct': suggested_stop * 0.7,
            'aggressive_stop_loss_pct': suggested_stop * 1.3,
            'var_based_stop': var_based_stop,
            'volatility_based_stop': volatility_based_stop,
            'trailing_stop_suggestion': suggested_stop * 0.8,
            'rationale': "基於 VaR、波動率和歷史回撤的綜合停損建議"
        }
    
    def _generate_take_profit_suggestions(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """生成停利建議"""
        # 基於風險報酬比的停利點
        stop_loss = 0.08  # 假設停損8%
        risk_reward_ratios = [1.5, 2.0, 3.0]  # 不同風險報酬比
        
        take_profit_levels = []
        for ratio in risk_reward_ratios:
            take_profit_levels.append({
                'risk_reward_ratio': ratio,
                'take_profit_pct': stop_loss * ratio,
                'probability': 0.7 / ratio  # 報酬比越高機率越低
            })
        
        return {
            'take_profit_levels': take_profit_levels,
            'preferred_take_profit_pct': stop_loss * 2.0,  # 2:1風險報酬比
            'scaling_out_strategy': {
                'first_target': stop_loss * 1.5,
                'second_target': stop_loss * 2.5,
                'third_target': stop_loss * 4.0
            },
            'rationale': "基於2:1風險報酬比的分批停利策略"
        }
    
    def _generate_diversification_advice(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """生成分散投資建議"""
        # 基於相關性的分散建議
        if risk_metrics.correlation_with_market > 0.8:
            diversification_importance = "high"
            suggested_positions = 20  # 建議持有20個不同標的
        elif risk_metrics.correlation_with_market > 0.6:
            diversification_importance = "medium"
            suggested_positions = 15
        else:
            diversification_importance = "low"
            suggested_positions = 10
        
        return {
            'diversification_importance': diversification_importance,
            'suggested_number_of_positions': suggested_positions,
            'max_single_position_pct': 100 / suggested_positions,
            'sector_diversification': "建議分散至少3-5個不同產業",
            'geographic_diversification': "考慮加入國際市場標的",
            'correlation_concern': risk_metrics.correlation_with_market > 0.75
        }
    
    def _generate_hedging_strategies(self, risk_metrics: RiskMetrics) -> List[str]:
        """生成避險策略"""
        strategies = []
        
        if risk_metrics.beta > 1.2:
            strategies.append("考慮使用指數期貨或ETF進行Beta避險")
        
        if risk_metrics.volatility_annual > 0.30:
            strategies.append("考慮買入賣權選擇權進行下檔保護")
        
        if risk_metrics.correlation_with_market > 0.8:
            strategies.append("增加與市場低相關性的資產")
        
        strategies.append("保持5-10%現金部位作為機會基金")
        strategies.append("定期檢視並調整避險比例")
        
        return strategies
    
    def _generate_monitoring_alerts(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """生成監控預警設定"""
        return {
            'price_alerts': {
                'stop_loss_alert': f"跌幅達到 {risk_metrics.var_95 * 100:.1f}% 時預警",
                'volatility_alert': "單日波動超過歷史90分位數時預警",
                'volume_alert': "成交量異常放大或萎縮時預警"
            },
            'portfolio_alerts': {
                'correlation_alert': "與大盤相關性突然改變時預警",
                'concentration_alert': "單一標的部位超過建議上限時預警",
                'drawdown_alert': f"組合回撤超過 {risk_metrics.max_drawdown * 100:.1f}% 時預警"
            },
            'market_alerts': {
                'vix_alert': "市場恐慌指數VIX突破關鍵水準時預警",
                'sector_alert': "所屬產業出現系統性風險時預警"
            }
        }
    
    async def _call_llm_risk_analysis(
        self,
        state: AnalysisState,
        risk_metrics: RiskMetrics,
        risk_scenarios: List[RiskScenario],
        model_config
    ) -> Dict[str, Any]:
        """呼叫LLM進行深度風險分析"""
        
        # 準備風險分析上下文
        risk_context = {
            'stock_id': state.stock_id,
            'risk_metrics': risk_metrics.to_dict(),
            'risk_scenarios': [scenario.to_dict() for scenario in risk_scenarios],
            'analysis_focus': 'comprehensive_risk_assessment'
        }
        
        # 生成風險分析提示詞
        prompt = self.get_analysis_prompt(state)
        
        # 呼叫LLM（這裡整合實際的LLM客戶端）
        try:
            # 模擬LLM回應
            await asyncio.sleep(1.0)  # 模擬LLM處理時間
            
            # 基於風險指標生成智能回應
            risk_level = self._determine_risk_level(risk_metrics)
            
            llm_response = {
                'overall_risk_assessment': risk_level,
                'confidence': 0.85,
                'key_risk_factors': self._identify_key_risk_factors(risk_metrics),
                'investment_recommendation': self._generate_investment_recommendation(risk_level, risk_metrics),
                'reasoning': self._generate_llm_reasoning(risk_level, risk_metrics, risk_scenarios),
                'risk_adjusted_target_price': self._calculate_risk_adjusted_target(state, risk_metrics),
            }
            
            return llm_response
            
        except Exception as e:
            self.logger.error(f"LLM風險分析調用失敗: {str(e)}")
            return {
                'overall_risk_assessment': 'MEDIUM',
                'confidence': 0.5,
                'key_risk_factors': ['數據不足', '分析過程中發生錯誤'],
                'investment_recommendation': 'HOLD',
                'reasoning': [f'風險分析過程中發生錯誤: {str(e)}'],
                'error': str(e)
            }
    
    def _determine_risk_level(self, risk_metrics: RiskMetrics) -> str:
        """判定整體風險等級"""
        high_risk_count = 0
        
        # 檢查各項風險指標
        if risk_metrics.volatility_annual > self.high_risk_thresholds['volatility_annual']:
            high_risk_count += 1
            
        if risk_metrics.var_95 > self.high_risk_thresholds['var_95_pct']:
            high_risk_count += 1
            
        if risk_metrics.max_drawdown > self.high_risk_thresholds['max_drawdown']:
            high_risk_count += 1
            
        if abs(risk_metrics.correlation_with_market) > self.high_risk_thresholds['correlation']:
            high_risk_count += 1
        
        # 判定風險等級
        if high_risk_count >= 3:
            return 'CRITICAL'
        elif high_risk_count >= 2:
            return 'HIGH'
        elif high_risk_count >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _identify_key_risk_factors(self, risk_metrics: RiskMetrics) -> List[str]:
        """識別關鍵風險因子"""
        risk_factors = []
        
        if risk_metrics.volatility_annual > 0.30:
            risk_factors.append(f"高波動率風險 (年化{risk_metrics.volatility_annual:.1%})")
            
        if risk_metrics.var_95 > 0.05:
            risk_factors.append(f"高VaR風險 (95% VaR達{risk_metrics.var_95:.1%})")
            
        if risk_metrics.max_drawdown > 0.20:
            risk_factors.append(f"高回撤風險 (最大回撤{risk_metrics.max_drawdown:.1%})")
            
        if abs(risk_metrics.correlation_with_market) > 0.8:
            risk_factors.append(f"高市場相關性風險 (相關性{risk_metrics.correlation_with_market:.2f})")
            
        if risk_metrics.sharpe_ratio and risk_metrics.sharpe_ratio < 0.5:
            risk_factors.append(f"低風險調整報酬 (Sharpe ratio {risk_metrics.sharpe_ratio:.2f})")
            
        if risk_metrics.beta and abs(risk_metrics.beta) > 1.5:
            risk_factors.append(f"高Beta風險 (Beta {risk_metrics.beta:.2f})")
        
        return risk_factors if risk_factors else ["整體風險在可接受範圍內"]
    
    def _generate_investment_recommendation(self, risk_level: str, risk_metrics: RiskMetrics) -> str:
        """基於風險評估生成投資建議"""
        if risk_level == 'CRITICAL':
            return 'SELL'  # 風險過高，建議出場
        elif risk_level == 'HIGH':
            return 'HOLD'  # 高風險，建議持有觀望
        elif risk_level == 'MEDIUM':
            # 根據風險調整後的報酬決定
            if risk_metrics.sharpe_ratio and risk_metrics.sharpe_ratio > 1.0:
                return 'BUY'   # 風險適中但報酬佳
            else:
                return 'HOLD'  # 風險適中，建議持有
        else:  # LOW risk
            return 'BUY'   # 低風險，可以買入
    
    def _generate_llm_reasoning(
        self,
        risk_level: str,
        risk_metrics: RiskMetrics,
        risk_scenarios: List[RiskScenario]
    ) -> List[str]:
        """生成LLM風格的分析理由"""
        reasoning = []
        
        # 風險等級說明
        risk_level_explanations = {
            'CRITICAL': '風險指標顯示投資風險極高，建議立即檢視持倉',
            'HIGH': '多項風險指標超出安全範圍，需謹慎管理風險',
            'MEDIUM': '風險指標處於中等水準，建議適度控制部位',
            'LOW': '整體風險可控，符合一般投資風險承受度'
        }
        reasoning.append(risk_level_explanations[risk_level])
        
        # 具體風險分析
        if risk_metrics.volatility_annual > 0.25:
            reasoning.append(f"年化波動率{risk_metrics.volatility_annual:.1%}偏高，需注意價格劇烈波動風險")
        
        if risk_metrics.var_95 > 0.04:
            reasoning.append(f"VaR值{risk_metrics.var_95:.1%}顯示單日損失風險較大")
        
        if risk_metrics.max_drawdown > 0.15:
            reasoning.append(f"歷史最大回撤{risk_metrics.max_drawdown:.1%}，需設定適當停損點")
        
        # 情境分析說明
        high_prob_scenarios = [s for s in risk_scenarios if s.probability > 0.2]
        if high_prob_scenarios:
            scenario_names = [s.scenario_name for s in high_prob_scenarios]
            reasoning.append(f"需特別關注{', '.join(scenario_names)}等風險情境")
        
        return reasoning
    
    def _calculate_risk_adjusted_target(self, state: AnalysisState, risk_metrics: RiskMetrics) -> Optional[float]:
        """計算風險調整後目標價"""
        current_price = 100.0  # 預設價格，實際應從state.stock_data獲取
        
        if state.stock_data and 'current_price' in state.stock_data:
            current_price = state.stock_data['current_price']
        
        # 基於風險調整目標價
        if risk_metrics.sharpe_ratio and risk_metrics.sharpe_ratio > 0:
            # 根據夏普比率調整期望報酬
            expected_return = risk_metrics.sharpe_ratio * risk_metrics.volatility_annual
            risk_adjusted_return = expected_return * 0.7  # 保守調整
            target_price = current_price * (1 + risk_adjusted_return)
        else:
            # 預設5%目標報酬，根據風險調整
            base_return = 0.05
            risk_adjustment = 1 - (risk_metrics.volatility_annual - 0.2) / 0.3
            risk_adjustment = max(0.3, min(1.2, risk_adjustment))
            target_price = current_price * (1 + base_return * risk_adjustment)
        
        return round(target_price, 2)
    
    async def _integrate_risk_analysis_results(
        self,
        state: AnalysisState,
        risk_metrics: RiskMetrics,
        risk_scenarios: List[RiskScenario],
        risk_management: Dict[str, Any],
        llm_analysis: Dict[str, Any],
        model_config
    ) -> AnalysisResult:
        """整合風險分析結果"""
        
        # 確定最終建議和信心度
        recommendation = llm_analysis.get('investment_recommendation', 'HOLD')
        confidence = llm_analysis.get('confidence', 0.6)
        
        # 生成綜合風險因子
        risk_factors = llm_analysis.get('key_risk_factors', [])
        if not risk_factors:
            risk_factors = []
        
        # 添加風險管理建議
        try:
            if 'stop_loss_suggestions' in risk_management:
                stop_loss_pct = risk_management['stop_loss_suggestions'].get('suggested_stop_loss_pct', 0.08)
                risk_factors.append(f"建議停損點: {stop_loss_pct:.1%}")
            
            if 'position_sizing' in risk_management:
                position_pct = risk_management['position_sizing'].get('recommended_position_pct', 0.05)
                risk_factors.append(f"建議部位規模: {position_pct:.1%}")
        except Exception as e:
            self.logger.warning(f"添加風險管理建議失敗: {str(e)}")
            
        # 確保至少有一個風險因子
        if not risk_factors:
            risk_factors = ["整體風險在可接受範圍內"]
        
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation=recommendation,
            confidence=confidence,
            confidence_level=AnalysisConfidenceLevel.HIGH if confidence > 0.7 else AnalysisConfidenceLevel.MODERATE,
            target_price=llm_analysis.get('risk_adjusted_target_price'),
            reasoning=llm_analysis.get('reasoning', []),
            risk_factors=risk_factors,
            technical_indicators={
                'risk_metrics': risk_metrics.to_dict(),
                'risk_level': llm_analysis.get('overall_risk_assessment', 'MEDIUM'),
                'risk_scenarios': [s.to_dict() for s in risk_scenarios],
                'risk_management_strategies': risk_management
            },
            model_used=model_config.model_name if hasattr(model_config, 'model_name') else 'risk_analysis_model'
        )
    
    # ==============================================
    # ART系統整合方法
    # ==============================================
    
    async def _record_analysis_start(self, state: AnalysisState):
        """記錄風險分析開始軌跡"""
        try:
            if hasattr(self, 'trajectory_collector'):
                decision_step = DecisionStep(
                    step_type='analysis_start',
                    step_data={
                        'analyst_id': self.analyst_id,
                        'stock_id': state.stock_id,
                        'analysis_type': 'risk_assessment',
                        'timestamp': datetime.now().isoformat(),
                        'user_id': getattr(state, 'user_id', None)
                    },
                    reasoning=['開始執行個人化風險分析'],
                    confidence=1.0
                )
                
                await self.trajectory_collector.collect_decision_step(
                    user_id=getattr(state, 'user_id', 'anonymous'),
                    trajectory_type=TrajectoryType.ANALYSIS,
                    decision_step=decision_step
                )
        except Exception as e:
            self.logger.warning(f"記錄分析開始軌跡失敗: {e}")
    
    async def _apply_personalized_risk_preferences(self, user_id: str, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """應用個人化風險偏好設定"""
        try:
            # 獲取用戶風險檔案
            if user_id not in self.user_risk_profiles:
                # 創建默認風險檔案
                self.user_risk_profiles[user_id] = {
                    'risk_tolerance': 0.5,  # 0-1, 預設中等風險承受度
                    'preferred_var_level': 0.95,  # 偏好的VaR信心水準
                    'max_acceptable_drawdown': 0.15,  # 最大可接受回撤
                    'position_sizing_preference': 'moderate',  # conservative, moderate, aggressive
                    'stop_loss_preference': 0.08,  # 偏好停損水準
                    'analysis_focus': ['market_risk', 'liquidity_risk'],  # 關注的風險類型
                    'learning_rate': 0.1  # 學習速度
                }
            
            user_profile = self.user_risk_profiles[user_id]
            
            # 根據用戶偏好調整分析參數
            if user_profile['risk_tolerance'] < 0.3:
                # 保守型用戶
                risk_data['analysis_params'] = {
                    'var_confidence_levels': [0.99, 0.95, 0.90],
                    'stress_test_severity': 'high',
                    'focus_downside_risk': True
                }
            elif user_profile['risk_tolerance'] > 0.7:
                # 積極型用戶
                risk_data['analysis_params'] = {
                    'var_confidence_levels': [0.95, 0.90, 0.85],
                    'stress_test_severity': 'moderate',
                    'include_upside_potential': True
                }
            else:
                # 穩健型用戶
                risk_data['analysis_params'] = {
                    'var_confidence_levels': [0.95, 0.90],
                    'stress_test_severity': 'moderate',
                    'balanced_analysis': True
                }
            
            # 添加個人化標記
            risk_data['personalized'] = True
            risk_data['user_profile'] = user_profile
            
            self.logger.info(f"已應用用戶 {user_id} 的個人化風險偏好")
            
        except Exception as e:
            self.logger.warning(f"應用個人化風險偏好失敗: {e}")
        
        return risk_data
    
    async def _personalize_risk_recommendations(self, user_id: str, risk_management: Dict[str, Any], risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """個人化風險建議調整"""
        try:
            if user_id not in self.user_risk_profiles:
                return risk_management
            
            user_profile = self.user_risk_profiles[user_id]
            
            # 調整停損建議
            if 'stop_loss_suggestions' in risk_management:
                base_stop_loss = risk_management['stop_loss_suggestions'].get('suggested_stop_loss_pct', 0.08)
                
                # 根據風險承受度調整
                if user_profile['risk_tolerance'] < 0.3:
                    # 保守用戶，提前停損
                    adjusted_stop_loss = min(base_stop_loss * 0.8, user_profile['stop_loss_preference'])
                elif user_profile['risk_tolerance'] > 0.7:
                    # 積極用戶，放寬停損
                    adjusted_stop_loss = base_stop_loss * 1.2
                else:
                    adjusted_stop_loss = base_stop_loss
                
                risk_management['stop_loss_suggestions']['personalized_stop_loss'] = adjusted_stop_loss
                risk_management['stop_loss_suggestions']['adjustment_reason'] = f"基於用戶風險承受度 {user_profile['risk_tolerance']:.1f} 調整"
            
            # 調整倉位建議
            if 'position_sizing' in risk_management:
                base_position = risk_management['position_sizing'].get('recommended_position_pct', 0.05)
                
                # 根據用戶偏好調整倉位大小
                position_multiplier = {
                    'conservative': 0.6,
                    'moderate': 1.0,
                    'aggressive': 1.4
                }.get(user_profile.get('position_sizing_preference', 'moderate'), 1.0)
                
                # 考慮當前風險水準
                if risk_metrics.volatility_annual > self.high_risk_thresholds['volatility_annual']:
                    position_multiplier *= 0.7  # 高波動時減少倉位
                
                adjusted_position = base_position * position_multiplier
                risk_management['position_sizing']['personalized_position_pct'] = min(adjusted_position, 0.15)  # 最大15%
                risk_management['position_sizing']['adjustment_factor'] = position_multiplier
            
            # 添加個人化標記
            risk_management['personalized'] = True
            risk_management['user_id'] = user_id
            
            self.logger.info(f"已為用戶 {user_id} 個人化風險建議")
            
        except Exception as e:
            self.logger.warning(f"個人化風險建議失敗: {e}")
        
        return risk_management
    
    async def _record_analysis_completion(self, state: AnalysisState, result: AnalysisResult):
        """記錄分析完成並進行學習"""
        try:
            user_id = getattr(state, 'user_id', None)
            if not user_id:
                return
            
            # 記錄分析結果到軌跡收集器
            if hasattr(self, 'trajectory_collector'):
                decision_step = DecisionStep(
                    step_type='analysis_completion',
                    step_data={
                        'analyst_id': self.analyst_id,
                        'stock_id': state.stock_id,
                        'recommendation': result.recommendation,
                        'confidence': result.confidence,
                        'risk_level': result.technical_indicators.get('risk_level', 'MEDIUM'),
                        'timestamp': datetime.now().isoformat()
                    },
                    reasoning=result.reasoning,
                    confidence=result.confidence
                )
                
                await self.trajectory_collector.collect_decision_step(
                    user_id=user_id,
                    trajectory_type=TrajectoryType.ANALYSIS,
                    decision_step=decision_step
                )
            
            # 記錄到學習歷史
            if user_id not in self.risk_learning_history:
                self.risk_learning_history[user_id] = []
            
            learning_record = {
                'timestamp': datetime.now().isoformat(),
                'stock_id': state.stock_id,
                'analysis_result': {
                    'recommendation': result.recommendation,
                    'confidence': result.confidence,
                    'risk_level': result.technical_indicators.get('risk_level', 'MEDIUM')
                },
                'user_interaction': None  # 將在用戶反饋時更新
            }
            
            self.risk_learning_history[user_id].append(learning_record)
            
            # 保持歷史記錄在合理範圍內
            if len(self.risk_learning_history[user_id]) > 100:
                self.risk_learning_history[user_id] = self.risk_learning_history[user_id][-50:]
            
            # 觸發行為學習引擎
            if hasattr(self, 'behavior_engine'):
                behavior_data = {
                    'user_id': user_id,
                    'analyst_type': 'risk_analyst',
                    'analysis_data': {
                        'stock_id': state.stock_id,
                        'recommendation': result.recommendation,
                        'confidence': result.confidence,
                        'risk_metrics': result.technical_indicators.get('risk_metrics', {})
                    },
                    'timestamp': datetime.now().timestamp()
                }
                
                # 異步處理，不影響主要分析流程
                asyncio.create_task(self._process_behavior_learning(user_id, behavior_data))
            
            self.logger.info(f"已記錄用戶 {user_id} 的風險分析完成軌跡")
            
        except Exception as e:
            self.logger.warning(f"記錄分析完成軌跡失敗: {e}")
    
    async def _process_behavior_learning(self, user_id: str, behavior_data: Dict[str, Any]):
        """處理行為學習"""
        try:
            # 創建行為學習互動資料
            interaction_data = {
                'behavior_data': [behavior_data],
                'prediction_request': {
                    'historical_data': self.risk_learning_history.get(user_id, [])[-10:],  # 最近10次記錄
                    'context': {
                        'analyst_type': 'risk_analyst',
                        'current_analysis': behavior_data['analysis_data']
                    }
                }
            }
            
            # 處理用戶互動
            result = await self.behavior_engine.process_user_interaction(user_id, interaction_data)
            
            # 根據學習結果更新用戶風險檔案
            if 'analysis' in result and user_id in self.user_risk_profiles:
                await self._update_user_risk_profile(user_id, result['analysis'])
            
        except Exception as e:
            self.logger.warning(f"行為學習處理失敗: {e}")
    
    async def _update_user_risk_profile(self, user_id: str, analysis_result: Dict[str, Any]):
        """更新用戶風險檔案"""
        try:
            if user_id not in self.user_risk_profiles:
                return
            
            user_profile = self.user_risk_profiles[user_id]
            learning_rate = user_profile.get('learning_rate', 0.1)
            
            # 根據分析洞察調整風險偏好
            behavior_score = analysis_result.get('behavior_score', 0.5)
            insights = analysis_result.get('insights', [])
            
            # 分析用戶的風險承受度變化
            for insight in insights:
                if insight.get('type') == 'bias_detection':
                    if '高風險' in insight.get('message', ''):
                        # 用戶顯示高風險偏好
                        user_profile['risk_tolerance'] = min(1.0, user_profile['risk_tolerance'] + learning_rate * 0.1)
                    elif '保守' in insight.get('message', ''):
                        # 用戶顯示保守傾向
                        user_profile['risk_tolerance'] = max(0.0, user_profile['risk_tolerance'] - learning_rate * 0.1)
            
            # 更新學習記錄
            user_profile['last_update'] = datetime.now().isoformat()
            user_profile['total_analyses'] = user_profile.get('total_analyses', 0) + 1
            
            self.logger.info(f"已更新用戶 {user_id} 風險檔案")
            
        except Exception as e:
            self.logger.warning(f"更新用戶風險檔案失敗: {e}")
    
    def get_user_risk_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶風險檔案"""
        return self.user_risk_profiles.get(user_id)
    
    def get_user_learning_history(self, user_id: str) -> List[Dict[str, Any]]:
        """獲取用戶學習歷史"""
        return self.risk_learning_history.get(user_id, [])

# 便利函數
async def analyze_stock_risk(
    stock_id: str,
    user_context: Dict[str, Any] = None,
    config: Dict[str, Any] = None
) -> AnalysisResult:
    """快速股票風險分析"""
    
    if config is None:
        config = {
            'risk_free_rate': 0.01,
            'market_benchmark': 'TAIEX',
            'debug': False
        }
    
    analyst = RiskAnalyst(config)
    
    # 創建分析狀態
    state = AnalysisState(
        stock_id=stock_id,
        analysis_date=datetime.now().strftime('%Y-%m-%d'),
        user_context=user_context
    )
    
    return await analyst.analyze(state)

if __name__ == "__main__":
    # 測試腳本
    async def test_risk_analyst():
        print("🛡️ 測試風險分析師")
        
        # 測試台積電風險分析
        result = await analyze_stock_risk("2330", {'user_id': 'test_user', 'membership_tier': 'DIAMOND'})
        
        print(f"股票: {result.stock_id}")
        print(f"風險評估建議: {result.recommendation}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"目標價: ${result.target_price}")
        print(f"分析理由:")
        for reason in result.reasoning:
            print(f"  - {reason}")
        print(f"風險因子:")
        for risk in result.risk_factors:
            print(f"  ⚠️ {risk}")
        
        if result.technical_indicators:
            risk_metrics = result.technical_indicators.get('risk_metrics', {})
            print(f"\n📊 風險指標:")
            print(f"  年化波動率: {risk_metrics.get('volatility_annual', 0):.1%}")
            print(f"  VaR (95%): {risk_metrics.get('var_95', 0):.1%}")
            print(f"  最大回撤: {risk_metrics.get('max_drawdown', 0):.1%}")
            print(f"  風險等級: {result.technical_indicators.get('risk_level', 'UNKNOWN')}")
        
        print("✅ 風險分析師測試完成")
    
    asyncio.run(test_risk_analyst())