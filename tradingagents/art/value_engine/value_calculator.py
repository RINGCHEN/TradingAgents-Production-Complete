#!/usr/bin/env python3
"""
Value Calculator - 多維度價值計算器
天工 (TianGong) - 為ART系統提供多維度價值評估和計算

此模組提供：
1. ValueCalculator - 價值計算核心引擎
2. ValueDimension - 價值維度定義
3. ValueMetric - 價值指標管理
4. ValueResult - 價值評估結果
5. DimensionWeight - 維度權重管理
"""

from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import uuid
import numpy as np
from collections import defaultdict, deque
import math

class ValueDimension(Enum):
    """價值維度"""
    FINANCIAL = "financial"                 # 財務價值
    STRATEGIC = "strategic"                 # 戰略價值
    OPERATIONAL = "operational"             # 營運價值
    MARKET = "market"                       # 市場價值
    CUSTOMER = "customer"                   # 客戶價值
    INNOVATION = "innovation"               # 創新價值
    RISK = "risk"                          # 風險價值
    SOCIAL = "social"                      # 社會價值
    TECHNOLOGY = "technology"               # 技術價值
    BRAND = "brand"                        # 品牌價值

class ValueMetric(Enum):
    """價值指標"""
    # 財務指標
    ROI = "roi"                            # 投資回報率
    NPV = "npv"                            # 淨現值
    IRR = "irr"                            # 內部收益率
    PAYBACK_PERIOD = "payback_period"      # 回收期
    PROFIT_MARGIN = "profit_margin"        # 利潤率
    
    # 營運指標
    EFFICIENCY_GAIN = "efficiency_gain"    # 效率提升
    COST_REDUCTION = "cost_reduction"      # 成本削減
    TIME_SAVING = "time_saving"            # 時間節省
    QUALITY_IMPROVEMENT = "quality_improvement"  # 質量改善
    
    # 市場指標
    MARKET_SHARE = "market_share"          # 市場份額
    COMPETITIVE_ADVANTAGE = "competitive_advantage"  # 競爭優勢
    BRAND_VALUE = "brand_value"            # 品牌價值
    CUSTOMER_ACQUISITION = "customer_acquisition"  # 客戶獲取
    
    # 風險指標
    RISK_REDUCTION = "risk_reduction"      # 風險降低
    COMPLIANCE_VALUE = "compliance_value"  # 合規價值
    VOLATILITY_REDUCTION = "volatility_reduction"  # 波動性降低

class AggregationMethod(Enum):
    """聚合方法"""
    WEIGHTED_AVERAGE = "weighted_average"  # 加權平均
    GEOMETRIC_MEAN = "geometric_mean"      # 幾何平均
    HARMONIC_MEAN = "harmonic_mean"        # 調和平均
    MAX_VALUE = "max_value"                # 最大值
    MIN_VALUE = "min_value"                # 最小值
    SUM = "sum"                           # 求和

@dataclass
class DimensionWeight:
    """維度權重"""
    dimension: ValueDimension
    weight: float = 1.0                    # 權重值
    confidence: float = 1.0                # 權重信心度
    source: str = "default"                # 權重來源
    last_updated: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def normalize_weight(self, total_weight: float) -> float:
        """標準化權重"""
        if total_weight <= 0:
            return 0.0
        return self.weight / total_weight

@dataclass
class ValueMetricData:
    """價值指標數據"""
    metric: ValueMetric
    value: float
    unit: str = ""                         # 單位
    confidence: float = 1.0                # 數據信心度
    timestamp: float = field(default_factory=time.time)
    source: str = ""                       # 數據來源
    calculation_method: str = ""           # 計算方法
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValueCalculationConfig:
    """價值計算配置"""
    dimension_weights: Dict[ValueDimension, DimensionWeight] = field(default_factory=dict)
    aggregation_method: AggregationMethod = AggregationMethod.WEIGHTED_AVERAGE
    confidence_threshold: float = 0.5      # 信心度閾值
    time_horizon: int = 12                 # 時間範圍（月）
    discount_rate: float = 0.08           # 折現率
    risk_free_rate: float = 0.03          # 無風險利率
    inflation_rate: float = 0.02          # 通脹率
    currency: str = "TWD"                 # 貨幣單位
    calculation_precision: int = 4         # 計算精度
    enable_sensitivity_analysis: bool = True  # 敏感性分析
    enable_scenario_analysis: bool = True     # 情境分析
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValueResult:
    """價值評估結果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    total_value: float = 0.0              # 總價值
    dimension_values: Dict[ValueDimension, float] = field(default_factory=dict)
    metric_values: Dict[ValueMetric, float] = field(default_factory=dict)
    confidence_score: float = 0.0         # 結果信心度
    calculation_timestamp: float = field(default_factory=time.time)
    calculation_duration: float = 0.0     # 計算耗時
    
    # 詳細分析結果
    value_breakdown: Dict[str, Any] = field(default_factory=dict)
    sensitivity_analysis: Dict[str, float] = field(default_factory=dict)
    scenario_analysis: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # 元數據
    config_used: Optional[ValueCalculationConfig] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    assumptions: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_value_by_dimension(self, dimension: ValueDimension) -> float:
        """獲取指定維度的價值"""
        return self.dimension_values.get(dimension, 0.0)
    
    def get_normalized_values(self) -> Dict[ValueDimension, float]:
        """獲取標準化的維度價值"""
        if self.total_value <= 0:
            return {dim: 0.0 for dim in self.dimension_values.keys()}
        
        return {
            dim: value / self.total_value 
            for dim, value in self.dimension_values.items()
        }

class ValueCalculator:
    """多維度價值計算器"""
    
    def __init__(self, config: ValueCalculationConfig):
        self.config = config
        self.calculation_history: List[ValueResult] = []
        self.metric_cache: Dict[str, ValueMetricData] = {}
        self.dimension_calculators: Dict[ValueDimension, Any] = {}
        
        # 初始化日誌
        self.logger = logging.getLogger(__name__)
        self.logger.info("ValueCalculator initialized")
        
        # 設置默認維度權重
        self._setup_default_dimension_weights()
        
        # 初始化計算器
        self._initialize_dimension_calculators()
    
    def _setup_default_dimension_weights(self):
        """設置默認維度權重"""
        default_weights = {
            ValueDimension.FINANCIAL: DimensionWeight(ValueDimension.FINANCIAL, 0.3),
            ValueDimension.STRATEGIC: DimensionWeight(ValueDimension.STRATEGIC, 0.2),
            ValueDimension.OPERATIONAL: DimensionWeight(ValueDimension.OPERATIONAL, 0.15),
            ValueDimension.MARKET: DimensionWeight(ValueDimension.MARKET, 0.15),
            ValueDimension.CUSTOMER: DimensionWeight(ValueDimension.CUSTOMER, 0.1),
            ValueDimension.RISK: DimensionWeight(ValueDimension.RISK, 0.1)
        }
        
        # 合併用戶配置的權重
        for dimension, weight in default_weights.items():
            if dimension not in self.config.dimension_weights:
                self.config.dimension_weights[dimension] = weight
    
    def _initialize_dimension_calculators(self):
        """初始化各維度計算器"""
        self.dimension_calculators = {
            ValueDimension.FINANCIAL: self._create_financial_calculator(),
            ValueDimension.STRATEGIC: self._create_strategic_calculator(),
            ValueDimension.OPERATIONAL: self._create_operational_calculator(),
            ValueDimension.MARKET: self._create_market_calculator(),
            ValueDimension.CUSTOMER: self._create_customer_calculator(),
            ValueDimension.RISK: self._create_risk_calculator()
        }
    
    def _create_financial_calculator(self):
        """創建財務價值計算器"""
        class FinancialValueCalculator:
            def __init__(self, config):
                self.config = config
                self.discount_rate = config.discount_rate
                self.time_horizon = config.time_horizon
            
            def calculate_roi(self, investment: float, returns: List[float]) -> float:
                """計算投資回報率"""
                if investment <= 0 or not returns:
                    return 0.0
                total_return = sum(returns)
                return (total_return - investment) / investment
            
            def calculate_npv(self, initial_investment: float, cash_flows: List[float]) -> float:
                """計算淨現值"""
                if not cash_flows:
                    return -initial_investment
                
                npv = -initial_investment
                for i, cf in enumerate(cash_flows):
                    npv += cf / ((1 + self.discount_rate) ** (i + 1))
                return npv
            
            def calculate_irr(self, cash_flows: List[float], max_iterations: int = 100) -> float:
                """計算內部收益率"""
                if len(cash_flows) < 2:
                    return 0.0
                
                # 使用牛頓法求解IRR
                rate = 0.1  # 初始猜測值
                for _ in range(max_iterations):
                    npv = sum(cf / ((1 + rate) ** i) for i, cf in enumerate(cash_flows))
                    npv_derivative = sum(-i * cf / ((1 + rate) ** (i + 1)) for i, cf in enumerate(cash_flows[1:], 1))
                    
                    if abs(npv_derivative) < 1e-10:
                        break
                    
                    new_rate = rate - npv / npv_derivative
                    if abs(new_rate - rate) < 1e-6:
                        return new_rate
                    rate = new_rate
                
                return rate
        
        return FinancialValueCalculator(self.config)
    
    def _create_strategic_calculator(self):
        """創建戰略價值計算器"""
        class StrategicValueCalculator:
            def __init__(self, config):
                self.config = config
            
            def calculate_competitive_advantage(self, market_position: float, 
                                              innovation_score: float, 
                                              brand_strength: float) -> float:
                """計算競爭優勢價值"""
                return (market_position * 0.4 + innovation_score * 0.35 + brand_strength * 0.25)
            
            def calculate_strategic_options_value(self, future_opportunities: List[Dict]) -> float:
                """計算戰略選擇權價值"""
                if not future_opportunities:
                    return 0.0
                
                total_value = 0.0
                for opp in future_opportunities:
                    probability = opp.get('probability', 0.5)
                    potential_value = opp.get('potential_value', 0.0)
                    time_to_exercise = opp.get('time_to_exercise', 1.0)
                    
                    # 簡化的Black-Scholes選擇權定價
                    option_value = probability * potential_value * math.exp(-self.config.discount_rate * time_to_exercise)
                    total_value += option_value
                
                return total_value
        
        return StrategicValueCalculator(self.config)
    
    def _create_operational_calculator(self):
        """創建營運價值計算器"""
        class OperationalValueCalculator:
            def __init__(self, config):
                self.config = config
            
            def calculate_efficiency_value(self, time_saved: float, 
                                         cost_per_hour: float,
                                         volume: float) -> float:
                """計算效率提升價值"""
                if time_saved <= 0 or cost_per_hour <= 0:
                    return 0.0
                
                annual_savings = time_saved * cost_per_hour * volume * 12
                return self._present_value(annual_savings, self.config.time_horizon)
            
            def calculate_quality_value(self, defect_reduction: float,
                                      cost_per_defect: float,
                                      volume: float) -> float:
                """計算質量改善價值"""
                if defect_reduction <= 0 or cost_per_defect <= 0:
                    return 0.0
                
                annual_savings = defect_reduction * cost_per_defect * volume * 12
                return self._present_value(annual_savings, self.config.time_horizon)
            
            def _present_value(self, annual_value: float, years: int) -> float:
                """計算現值"""
                pv = 0.0
                for year in range(1, years + 1):
                    pv += annual_value / ((1 + self.config.discount_rate) ** year)
                return pv
        
        return OperationalValueCalculator(self.config)
    
    def _create_market_calculator(self):
        """創建市場價值計算器"""
        class MarketValueCalculator:
            def __init__(self, config):
                self.config = config
            
            def calculate_market_share_value(self, market_share_gain: float,
                                           market_size: float,
                                           profit_margin: float) -> float:
                """計算市場份額價值"""
                if market_share_gain <= 0 or market_size <= 0:
                    return 0.0
                
                additional_revenue = market_share_gain * market_size
                additional_profit = additional_revenue * profit_margin
                return self._present_value(additional_profit, self.config.time_horizon)
            
            def calculate_brand_value(self, brand_awareness: float,
                                    brand_preference: float,
                                    price_premium: float,
                                    customer_base: float) -> float:
                """計算品牌價值"""
                brand_strength = (brand_awareness + brand_preference) / 2
                brand_premium_value = price_premium * customer_base * brand_strength
                return self._present_value(brand_premium_value, self.config.time_horizon)
            
            def _present_value(self, annual_value: float, years: int) -> float:
                """計算現值"""
                pv = 0.0
                for year in range(1, years + 1):
                    pv += annual_value / ((1 + self.config.discount_rate) ** year)
                return pv
        
        return MarketValueCalculator(self.config)
    
    def _create_customer_calculator(self):
        """創建客戶價值計算器"""
        class CustomerValueCalculator:
            def __init__(self, config):
                self.config = config
            
            def calculate_clv(self, average_order_value: float,
                             purchase_frequency: float,
                             customer_lifespan: float,
                             profit_margin: float) -> float:
                """計算客戶終身價值"""
                if any(x <= 0 for x in [average_order_value, purchase_frequency, customer_lifespan, profit_margin]):
                    return 0.0
                
                annual_value = average_order_value * purchase_frequency * profit_margin
                clv = 0.0
                for year in range(1, int(customer_lifespan) + 1):
                    clv += annual_value / ((1 + self.config.discount_rate) ** year)
                
                return clv
            
            def calculate_customer_satisfaction_value(self, satisfaction_improvement: float,
                                                    retention_rate_improvement: float,
                                                    customer_base: float,
                                                    average_clv: float) -> float:
                """計算客戶滿意度價值"""
                if satisfaction_improvement <= 0 or customer_base <= 0:
                    return 0.0
                
                # 滿意度提升帶來的保留率改善
                additional_retained_customers = customer_base * retention_rate_improvement * satisfaction_improvement
                return additional_retained_customers * average_clv
        
        return CustomerValueCalculator(self.config)
    
    def _create_risk_calculator(self):
        """創建風險價值計算器"""
        class RiskValueCalculator:
            def __init__(self, config):
                self.config = config
            
            def calculate_risk_reduction_value(self, risk_probability_before: float,
                                             risk_probability_after: float,
                                             potential_loss: float) -> float:
                """計算風險降低價值"""
                if risk_probability_before <= risk_probability_after:
                    return 0.0
                
                risk_reduction = risk_probability_before - risk_probability_after
                return risk_reduction * potential_loss
            
            def calculate_volatility_reduction_value(self, volatility_before: float,
                                                   volatility_after: float,
                                                   portfolio_value: float,
                                                   risk_premium: float) -> float:
                """計算波動性降低價值"""
                if volatility_before <= volatility_after:
                    return 0.0
                
                volatility_reduction = volatility_before - volatility_after
                return portfolio_value * volatility_reduction * risk_premium
        
        return RiskValueCalculator(self.config)
    
    async def calculate_value(self, input_data: Dict[str, Any]) -> ValueResult:
        """計算多維度價值"""
        start_time = time.time()
        
        try:
            result = ValueResult(
                config_used=self.config,
                input_data=input_data.copy()
            )
            
            # 計算各維度價值
            for dimension in self.config.dimension_weights.keys():
                dimension_value = await self._calculate_dimension_value(dimension, input_data)
                result.dimension_values[dimension] = dimension_value
            
            # 聚合總價值
            result.total_value = self._aggregate_dimension_values(result.dimension_values)
            
            # 計算信心度
            result.confidence_score = self._calculate_confidence_score(result)
            
            # 價值分解分析
            result.value_breakdown = self._create_value_breakdown(result)
            
            # 敏感性分析
            if self.config.enable_sensitivity_analysis:
                result.sensitivity_analysis = await self._perform_sensitivity_analysis(input_data, result)
            
            # 情境分析
            if self.config.enable_scenario_analysis:
                result.scenario_analysis = await self._perform_scenario_analysis(input_data, result)
            
            # 生成建議
            result.recommendations = self._generate_recommendations(result)
            
            result.calculation_duration = time.time() - start_time
            
            # 保存計算歷史
            self.calculation_history.append(result)
            
            self.logger.info(f"Value calculation completed in {result.calculation_duration:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Value calculation failed: {e}")
            raise
    
    async def _calculate_dimension_value(self, dimension: ValueDimension, input_data: Dict[str, Any]) -> float:
        """計算單一維度價值"""
        calculator = self.dimension_calculators.get(dimension)
        if not calculator:
            return 0.0
        
        dimension_data = input_data.get(dimension.value, {})
        
        if dimension == ValueDimension.FINANCIAL:
            return await self._calculate_financial_value(calculator, dimension_data)
        elif dimension == ValueDimension.STRATEGIC:
            return await self._calculate_strategic_value(calculator, dimension_data)
        elif dimension == ValueDimension.OPERATIONAL:
            return await self._calculate_operational_value(calculator, dimension_data)
        elif dimension == ValueDimension.MARKET:
            return await self._calculate_market_value(calculator, dimension_data)
        elif dimension == ValueDimension.CUSTOMER:
            return await self._calculate_customer_value(calculator, dimension_data)
        elif dimension == ValueDimension.RISK:
            return await self._calculate_risk_value(calculator, dimension_data)
        else:
            return 0.0
    
    async def _calculate_financial_value(self, calculator, data: Dict[str, Any]) -> float:
        """計算財務價值"""
        total_value = 0.0
        
        # ROI計算
        investment = data.get('investment', 0)
        returns = data.get('returns', [])
        if investment > 0 and returns:
            roi = calculator.calculate_roi(investment, returns)
            total_value += roi * investment
        
        # NPV計算
        initial_investment = data.get('initial_investment', 0)
        cash_flows = data.get('cash_flows', [])
        if cash_flows:
            npv = calculator.calculate_npv(initial_investment, cash_flows)
            total_value += npv
        
        # 其他財務指標
        profit = data.get('annual_profit', 0)
        if profit > 0:
            total_value += profit * self.config.time_horizon * 0.5  # 簡化現值計算
        
        return max(0.0, total_value)
    
    async def _calculate_strategic_value(self, calculator, data: Dict[str, Any]) -> float:
        """計算戰略價值"""
        total_value = 0.0
        
        # 競爭優勢價值
        market_position = data.get('market_position', 0.5)
        innovation_score = data.get('innovation_score', 0.5)
        brand_strength = data.get('brand_strength', 0.5)
        
        competitive_advantage = calculator.calculate_competitive_advantage(
            market_position, innovation_score, brand_strength
        )
        
        strategic_multiplier = data.get('strategic_multiplier', 100000)
        total_value += competitive_advantage * strategic_multiplier
        
        # 戰略選擇權價值
        opportunities = data.get('future_opportunities', [])
        if opportunities:
            options_value = calculator.calculate_strategic_options_value(opportunities)
            total_value += options_value
        
        return max(0.0, total_value)
    
    async def _calculate_operational_value(self, calculator, data: Dict[str, Any]) -> float:
        """計算營運價值"""
        total_value = 0.0
        
        # 效率提升價值
        time_saved = data.get('time_saved_hours', 0)
        cost_per_hour = data.get('cost_per_hour', 100)
        volume = data.get('volume', 1)
        
        if time_saved > 0:
            efficiency_value = calculator.calculate_efficiency_value(time_saved, cost_per_hour, volume)
            total_value += efficiency_value
        
        # 質量改善價值
        defect_reduction = data.get('defect_reduction_percent', 0)
        cost_per_defect = data.get('cost_per_defect', 1000)
        
        if defect_reduction > 0:
            quality_value = calculator.calculate_quality_value(defect_reduction, cost_per_defect, volume)
            total_value += quality_value
        
        return max(0.0, total_value)
    
    async def _calculate_market_value(self, calculator, data: Dict[str, Any]) -> float:
        """計算市場價值"""
        total_value = 0.0
        
        # 市場份額價值
        market_share_gain = data.get('market_share_gain', 0)
        market_size = data.get('market_size', 0)
        profit_margin = data.get('profit_margin', 0.1)
        
        if market_share_gain > 0 and market_size > 0:
            market_value = calculator.calculate_market_share_value(market_share_gain, market_size, profit_margin)
            total_value += market_value
        
        # 品牌價值
        brand_awareness = data.get('brand_awareness', 0.5)
        brand_preference = data.get('brand_preference', 0.5)
        price_premium = data.get('price_premium', 0)
        customer_base = data.get('customer_base', 0)
        
        if price_premium > 0 and customer_base > 0:
            brand_value = calculator.calculate_brand_value(brand_awareness, brand_preference, price_premium, customer_base)
            total_value += brand_value
        
        return max(0.0, total_value)
    
    async def _calculate_customer_value(self, calculator, data: Dict[str, Any]) -> float:
        """計算客戶價值"""
        total_value = 0.0
        
        # 客戶終身價值
        aov = data.get('average_order_value', 0)
        frequency = data.get('purchase_frequency', 0)
        lifespan = data.get('customer_lifespan', 0)
        margin = data.get('profit_margin', 0.2)
        
        if all(x > 0 for x in [aov, frequency, lifespan]):
            clv = calculator.calculate_clv(aov, frequency, lifespan, margin)
            customer_count = data.get('customer_count', 1)
            total_value += clv * customer_count
        
        # 客戶滿意度價值
        satisfaction_improvement = data.get('satisfaction_improvement', 0)
        retention_improvement = data.get('retention_rate_improvement', 0)
        customer_base = data.get('customer_base', 0)
        average_clv = data.get('average_clv', 1000)
        
        if satisfaction_improvement > 0 and customer_base > 0:
            satisfaction_value = calculator.calculate_customer_satisfaction_value(
                satisfaction_improvement, retention_improvement, customer_base, average_clv
            )
            total_value += satisfaction_value
        
        return max(0.0, total_value)
    
    async def _calculate_risk_value(self, calculator, data: Dict[str, Any]) -> float:
        """計算風險價值"""
        total_value = 0.0
        
        # 風險降低價值
        risk_before = data.get('risk_probability_before', 0)
        risk_after = data.get('risk_probability_after', 0)
        potential_loss = data.get('potential_loss', 0)
        
        if risk_before > risk_after and potential_loss > 0:
            risk_value = calculator.calculate_risk_reduction_value(risk_before, risk_after, potential_loss)
            total_value += risk_value
        
        # 波動性降低價值
        vol_before = data.get('volatility_before', 0)
        vol_after = data.get('volatility_after', 0)
        portfolio_value = data.get('portfolio_value', 0)
        risk_premium = data.get('risk_premium', 0.05)
        
        if vol_before > vol_after and portfolio_value > 0:
            volatility_value = calculator.calculate_volatility_reduction_value(
                vol_before, vol_after, portfolio_value, risk_premium
            )
            total_value += volatility_value
        
        return max(0.0, total_value)
    
    def _aggregate_dimension_values(self, dimension_values: Dict[ValueDimension, float]) -> float:
        """聚合維度價值"""
        if not dimension_values:
            return 0.0
        
        if self.config.aggregation_method == AggregationMethod.WEIGHTED_AVERAGE:
            total_weighted_value = 0.0
            total_weight = 0.0
            
            for dimension, value in dimension_values.items():
                weight_data = self.config.dimension_weights.get(dimension)
                if weight_data:
                    total_weighted_value += value * weight_data.weight
                    total_weight += weight_data.weight
            
            return total_weighted_value / max(total_weight, 1.0)
        
        elif self.config.aggregation_method == AggregationMethod.SUM:
            return sum(dimension_values.values())
        
        elif self.config.aggregation_method == AggregationMethod.GEOMETRIC_MEAN:
            values = [max(v, 0.01) for v in dimension_values.values()]  # 避免零值
            return math.exp(sum(math.log(v) for v in values) / len(values))
        
        else:
            return sum(dimension_values.values()) / len(dimension_values)
    
    def _calculate_confidence_score(self, result: ValueResult) -> float:
        """計算結果信心度"""
        confidence_scores = []
        
        # 基於維度權重的信心度
        for dimension in result.dimension_values.keys():
            weight_data = self.config.dimension_weights.get(dimension)
            if weight_data:
                confidence_scores.append(weight_data.confidence)
        
        # 基於數據完整性的信心度
        data_completeness = len(result.dimension_values) / len(ValueDimension)
        confidence_scores.append(data_completeness)
        
        # 基於計算穩定性的信心度
        if len(self.calculation_history) > 1:
            recent_results = self.calculation_history[-5:]  # 最近5次計算
            values = [r.total_value for r in recent_results if r.total_value > 0]
            if len(values) > 1:
                cv = np.std(values) / np.mean(values) if np.mean(values) > 0 else 1.0
                stability_confidence = max(0.0, 1.0 - cv)
                confidence_scores.append(stability_confidence)
        
        return np.mean(confidence_scores) if confidence_scores else 0.5
    
    def _create_value_breakdown(self, result: ValueResult) -> Dict[str, Any]:
        """創建價值分解分析"""
        breakdown = {
            'total_value': result.total_value,
            'dimension_contributions': {},
            'value_sources': {},
            'relative_weights': {}
        }
        
        # 維度貢獻度
        for dimension, value in result.dimension_values.items():
            breakdown['dimension_contributions'][dimension.value] = {
                'absolute_value': value,
                'percentage': (value / result.total_value * 100) if result.total_value > 0 else 0,
                'weight_used': self.config.dimension_weights.get(dimension, DimensionWeight(dimension)).weight
            }
        
        # 相對權重
        total_weight = sum(w.weight for w in self.config.dimension_weights.values())
        for dimension, weight_data in self.config.dimension_weights.items():
            breakdown['relative_weights'][dimension.value] = weight_data.normalize_weight(total_weight)
        
        return breakdown
    
    async def _perform_sensitivity_analysis(self, input_data: Dict[str, Any], base_result: ValueResult) -> Dict[str, float]:
        """執行敏感性分析"""
        sensitivity_results = {}
        
        # 對關鍵參數進行±10%的敏感性測試
        test_parameters = [
            ('discount_rate', 0.1),
            ('time_horizon', 0.1),
            ('dimension_weights', 0.1)
        ]
        
        for param_name, variation in test_parameters:
            # 向上變化
            modified_config = self._modify_config_parameter(param_name, variation)
            temp_calculator = ValueCalculator(modified_config)
            temp_calculator.dimension_calculators = self.dimension_calculators
            
            try:
                up_result = await temp_calculator.calculate_value(input_data)
                up_sensitivity = (up_result.total_value - base_result.total_value) / base_result.total_value if base_result.total_value > 0 else 0
                sensitivity_results[f'{param_name}_up'] = up_sensitivity
            except:
                sensitivity_results[f'{param_name}_up'] = 0.0
            
            # 向下變化
            modified_config = self._modify_config_parameter(param_name, -variation)
            temp_calculator = ValueCalculator(modified_config)
            temp_calculator.dimension_calculators = self.dimension_calculators
            
            try:
                down_result = await temp_calculator.calculate_value(input_data)
                down_sensitivity = (down_result.total_value - base_result.total_value) / base_result.total_value if base_result.total_value > 0 else 0
                sensitivity_results[f'{param_name}_down'] = down_sensitivity
            except:
                sensitivity_results[f'{param_name}_down'] = 0.0
        
        return sensitivity_results
    
    def _modify_config_parameter(self, param_name: str, variation: float) -> ValueCalculationConfig:
        """修改配置參數用於敏感性分析"""
        import copy
        modified_config = copy.deepcopy(self.config)
        
        if param_name == 'discount_rate':
            modified_config.discount_rate *= (1 + variation)
        elif param_name == 'time_horizon':
            modified_config.time_horizon = int(modified_config.time_horizon * (1 + variation))
        elif param_name == 'dimension_weights':
            # 修改所有維度權重
            for dimension in modified_config.dimension_weights:
                modified_config.dimension_weights[dimension].weight *= (1 + variation)
        
        return modified_config
    
    async def _perform_scenario_analysis(self, input_data: Dict[str, Any], base_result: ValueResult) -> Dict[str, Dict[str, float]]:
        """執行情境分析"""
        scenarios = {
            'optimistic': {'factor': 1.2, 'description': '樂觀情境'},
            'pessimistic': {'factor': 0.8, 'description': '悲觀情境'},
            'conservative': {'factor': 0.9, 'description': '保守情境'}
        }
        
        scenario_results = {}
        
        for scenario_name, scenario_data in scenarios.items():
            factor = scenario_data['factor']
            
            # 修改輸入數據
            modified_input = self._apply_scenario_factor(input_data, factor)
            
            try:
                scenario_result = await self.calculate_value(modified_input)
                scenario_results[scenario_name] = {
                    'total_value': scenario_result.total_value,
                    'change_from_base': scenario_result.total_value - base_result.total_value,
                    'change_percentage': ((scenario_result.total_value - base_result.total_value) / base_result.total_value * 100) if base_result.total_value > 0 else 0,
                    'confidence_score': scenario_result.confidence_score
                }
            except:
                scenario_results[scenario_name] = {
                    'total_value': 0.0,
                    'change_from_base': 0.0,
                    'change_percentage': 0.0,
                    'confidence_score': 0.0
                }
        
        return scenario_results
    
    def _apply_scenario_factor(self, input_data: Dict[str, Any], factor: float) -> Dict[str, Any]:
        """應用情境因子到輸入數據"""
        import copy
        modified_data = copy.deepcopy(input_data)
        
        # 對數值型參數應用因子
        numeric_keys = [
            'investment', 'returns', 'annual_profit', 'market_size', 
            'customer_base', 'potential_loss', 'portfolio_value'
        ]
        
        for dimension_key, dimension_data in modified_data.items():
            if isinstance(dimension_data, dict):
                for key, value in dimension_data.items():
                    if key in numeric_keys and isinstance(value, (int, float)):
                        modified_data[dimension_key][key] = value * factor
                    elif isinstance(value, list) and all(isinstance(x, (int, float)) for x in value):
                        modified_data[dimension_key][key] = [x * factor for x in value]
        
        return modified_data
    
    def _generate_recommendations(self, result: ValueResult) -> List[str]:
        """生成價值優化建議"""
        recommendations = []
        
        # 基於維度價值分布的建議
        sorted_dimensions = sorted(result.dimension_values.items(), key=lambda x: x[1], reverse=True)
        
        if sorted_dimensions:
            top_dimension = sorted_dimensions[0][0]
            recommendations.append(f"重點關注{top_dimension.value}維度價值，這是當前最大的價值來源")
            
            if len(sorted_dimensions) > 1:
                bottom_dimension = sorted_dimensions[-1][0]
                recommendations.append(f"考慮加強{bottom_dimension.value}維度的投資，以實現更均衡的價值創造")
        
        # 基於信心度的建議
        if result.confidence_score < 0.7:
            recommendations.append("建議收集更多數據以提高價值評估的準確性")
        
        # 基於敏感性分析的建議
        if result.sensitivity_analysis:
            high_sensitivity = [k for k, v in result.sensitivity_analysis.items() if abs(v) > 0.2]
            if high_sensitivity:
                recommendations.append(f"需要特別關注以下高敏感性參數: {', '.join(high_sensitivity)}")
        
        # 基於情境分析的建議
        if result.scenario_analysis:
            pessimistic = result.scenario_analysis.get('pessimistic', {})
            if pessimistic.get('total_value', 0) < result.total_value * 0.5:
                recommendations.append("悲觀情境下價值大幅下降，建議制定風險緩解策略")
        
        return recommendations
    
    def get_calculation_history(self, limit: int = 10) -> List[ValueResult]:
        """獲取計算歷史"""
        return self.calculation_history[-limit:]
    
    def export_results(self, result: ValueResult, format: str = 'json') -> str:
        """導出計算結果"""
        if format.lower() == 'json':
            import json
            return json.dumps({
                'result_id': result.result_id,
                'total_value': result.total_value,
                'dimension_values': {k.value: v for k, v in result.dimension_values.items()},
                'confidence_score': result.confidence_score,
                'calculation_timestamp': result.calculation_timestamp,
                'value_breakdown': result.value_breakdown,
                'recommendations': result.recommendations
            }, indent=2)
        else:
            return str(result)

# 工廠函數
def create_value_calculator(config: Optional[ValueCalculationConfig] = None) -> ValueCalculator:
    """創建價值計算器"""
    if config is None:
        config = ValueCalculationConfig()
    
    return ValueCalculator(config)

def create_value_calculation_config(**kwargs) -> ValueCalculationConfig:
    """創建價值計算配置"""
    return ValueCalculationConfig(**kwargs)