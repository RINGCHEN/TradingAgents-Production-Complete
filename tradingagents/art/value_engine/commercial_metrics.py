#!/usr/bin/env python3
"""
Commercial Metrics Engine - 商業價值計量引擎
天工 (TianGong) - 為ART系統提供商業價值計量和ROI分析

此模組提供：
1. CommercialMetricsEngine - 商業指標核心引擎
2. BusinessValue - 商業價值模型
3. ROIAnalyzer - 投資回報分析器
4. RevenueTracker - 收入追蹤器
5. CostAnalyzer - 成本分析器
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

class RevenueType(Enum):
    """收入類型"""
    SUBSCRIPTION = "subscription"           # 訂閱收入
    TRANSACTION = "transaction"             # 交易收入
    LICENSING = "licensing"                 # 授權收入
    CONSULTING = "consulting"               # 諮詢收入
    ADVERTISING = "advertising"             # 廣告收入
    PREMIUM_FEATURES = "premium_features"   # 付費功能
    DATA_MONETIZATION = "data_monetization" # 數據變現
    PARTNERSHIP = "partnership"             # 合作夥伴收入

class CostCategory(Enum):
    """成本類別"""
    INFRASTRUCTURE = "infrastructure"       # 基礎設施成本
    DEVELOPMENT = "development"             # 開發成本
    OPERATIONS = "operations"               # 運營成本
    MARKETING = "marketing"                 # 行銷成本
    CUSTOMER_ACQUISITION = "customer_acquisition"  # 客戶獲取成本
    SUPPORT = "support"                     # 支援成本
    COMPLIANCE = "compliance"               # 合規成本
    RESEARCH = "research"                   # 研發成本

class MetricPeriod(Enum):
    """指標週期"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

@dataclass
class BusinessValue:
    """商業價值模型"""
    value_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # 財務指標
    revenue: float = 0.0                    # 收入
    cost: float = 0.0                       # 成本
    profit: float = 0.0                     # 利潤
    roi: float = 0.0                        # 投資回報率
    payback_period: float = 0.0             # 回收期
    
    # 市場指標
    market_share: float = 0.0               # 市場份額
    customer_count: int = 0                 # 客戶數量
    retention_rate: float = 0.0             # 客戶保留率
    acquisition_cost: float = 0.0           # 客戶獲取成本
    lifetime_value: float = 0.0             # 客戶終身價值
    
    # 營運指標
    conversion_rate: float = 0.0            # 轉化率
    churn_rate: float = 0.0                 # 流失率
    engagement_score: float = 0.0           # 參與度分數
    utilization_rate: float = 0.0           # 使用率
    
    # 增長指標
    growth_rate: float = 0.0                # 增長率
    user_growth: float = 0.0                # 用戶增長
    revenue_growth: float = 0.0             # 收入增長
    market_penetration: float = 0.0         # 市場滲透率
    
    # 時間和質量指標
    period: MetricPeriod = MetricPeriod.MONTHLY
    confidence_level: float = 0.0           # 信心水準
    data_quality_score: float = 0.0         # 數據質量分數
    timestamp: float = field(default_factory=time.time)
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def calculate_profit_margin(self) -> float:
        """計算利潤率"""
        if self.revenue <= 0:
            return 0.0
        return (self.profit / self.revenue) * 100
    
    def calculate_roas(self) -> float:
        """計算廣告投資回報率"""
        marketing_cost = self.metadata.get('marketing_cost', 0)
        if marketing_cost <= 0:
            return 0.0
        return self.revenue / marketing_cost
    
    def calculate_ltv_cac_ratio(self) -> float:
        """計算LTV/CAC比率"""
        if self.acquisition_cost <= 0:
            return 0.0
        return self.lifetime_value / self.acquisition_cost

@dataclass
class RevenueStream:
    """收入流"""
    stream_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: RevenueType = RevenueType.SUBSCRIPTION
    amount: float = 0.0                     # 收入金額
    recurring: bool = False                 # 是否重複收入
    frequency: str = "monthly"              # 收入頻率
    growth_rate: float = 0.0                # 增長率
    risk_factor: float = 0.0                # 風險因子
    confidence: float = 0.9                 # 信心度
    start_date: float = field(default_factory=time.time)
    end_date: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CostItem:
    """成本項目"""
    cost_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: CostCategory = CostCategory.OPERATIONS
    amount: float = 0.0                     # 成本金額
    fixed: bool = True                      # 是否固定成本
    scalable: bool = False                  # 是否可擴展
    optimization_potential: float = 0.0     # 優化潜力
    allocation_method: str = "direct"       # 分攤方法
    department: str = ""                    # 所屬部門
    period: MetricPeriod = MetricPeriod.MONTHLY
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ROIAnalyzer:
    """投資回報分析器"""
    
    def __init__(self):
        self.analysis_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def calculate_simple_roi(self, investment: float, returns: float) -> float:
        """計算簡單ROI"""
        if investment <= 0:
            return 0.0
        return ((returns - investment) / investment) * 100
    
    def calculate_annualized_roi(self, investment: float, returns: float, years: float) -> float:
        """計算年化ROI"""
        if investment <= 0 or years <= 0:
            return 0.0
        
        total_return = returns / investment
        return (math.pow(total_return, 1/years) - 1) * 100
    
    def calculate_risk_adjusted_roi(self, roi: float, risk_factor: float, risk_free_rate: float = 0.03) -> float:
        """計算風險調整後ROI"""
        if risk_factor <= 0:
            return roi
        
        # 使用Sharpe比率的簡化版本
        excess_return = (roi / 100) - risk_free_rate
        return (excess_return / risk_factor) * 100
    
    def calculate_incremental_roi(self, baseline_roi: float, incremental_investment: float, 
                                 incremental_returns: float) -> float:
        """計算增量ROI"""
        if incremental_investment <= 0:
            return 0.0
        
        incremental_roi = ((incremental_returns - incremental_investment) / incremental_investment) * 100
        return incremental_roi
    
    async def perform_roi_analysis(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行ROI分析"""
        analysis_result = {
            'analysis_id': str(uuid.uuid4()),
            'timestamp': time.time(),
            'roi_metrics': {},
            'risk_assessment': {},
            'recommendations': []
        }
        
        try:
            # 基本ROI計算
            investment = business_data.get('total_investment', 0)
            returns = business_data.get('total_returns', 0)
            
            if investment > 0:
                simple_roi = self.calculate_simple_roi(investment, returns)
                analysis_result['roi_metrics']['simple_roi'] = simple_roi
                
                # 年化ROI
                years = business_data.get('investment_period_years', 1)
                annualized_roi = self.calculate_annualized_roi(investment, returns, years)
                analysis_result['roi_metrics']['annualized_roi'] = annualized_roi
                
                # 風險調整ROI
                risk_factor = business_data.get('risk_factor', 0.1)
                risk_adjusted_roi = self.calculate_risk_adjusted_roi(simple_roi, risk_factor)
                analysis_result['roi_metrics']['risk_adjusted_roi'] = risk_adjusted_roi
            
            # 增量ROI分析
            incremental_data = business_data.get('incremental_investment', {})
            if incremental_data:
                baseline_roi = analysis_result['roi_metrics'].get('simple_roi', 0)
                inc_investment = incremental_data.get('investment', 0)
                inc_returns = incremental_data.get('returns', 0)
                
                incremental_roi = self.calculate_incremental_roi(baseline_roi, inc_investment, inc_returns)
                analysis_result['roi_metrics']['incremental_roi'] = incremental_roi
            
            # 風險評估
            analysis_result['risk_assessment'] = await self._assess_investment_risk(business_data)
            
            # 生成建議
            analysis_result['recommendations'] = self._generate_roi_recommendations(analysis_result)
            
            self.analysis_history.append(analysis_result)
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"ROI analysis failed: {e}")
            raise
    
    async def _assess_investment_risk(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """評估投資風險"""
        risk_assessment = {
            'overall_risk_level': 'medium',
            'risk_factors': {},
            'mitigation_strategies': []
        }
        
        # 市場風險
        market_volatility = business_data.get('market_volatility', 0.2)
        risk_assessment['risk_factors']['market_risk'] = min(market_volatility, 1.0)
        
        # 技術風險
        technology_maturity = business_data.get('technology_maturity', 0.8)
        risk_assessment['risk_factors']['technology_risk'] = 1.0 - technology_maturity
        
        # 競爭風險
        competitive_intensity = business_data.get('competitive_intensity', 0.5)
        risk_assessment['risk_factors']['competitive_risk'] = competitive_intensity
        
        # 營運風險
        operational_complexity = business_data.get('operational_complexity', 0.3)
        risk_assessment['risk_factors']['operational_risk'] = operational_complexity
        
        # 總體風險等級
        avg_risk = np.mean(list(risk_assessment['risk_factors'].values()))
        if avg_risk < 0.3:
            risk_assessment['overall_risk_level'] = 'low'
        elif avg_risk > 0.7:
            risk_assessment['overall_risk_level'] = 'high'
        
        return risk_assessment
    
    def _generate_roi_recommendations(self, analysis_result: Dict[str, Any]) -> List[str]:
        """生成ROI優化建議"""
        recommendations = []
        roi_metrics = analysis_result.get('roi_metrics', {})
        
        # 基於ROI水準的建議
        simple_roi = roi_metrics.get('simple_roi', 0)
        if simple_roi < 10:
            recommendations.append("ROI偏低，建議重新評估投資策略或尋找成本優化機會")
        elif simple_roi > 50:
            recommendations.append("ROI表現優異，考慮擴大投資規模")
        
        # 基於風險調整ROI的建議
        risk_adjusted_roi = roi_metrics.get('risk_adjusted_roi', 0)
        if risk_adjusted_roi < simple_roi * 0.5:
            recommendations.append("風險調整後ROI顯著降低，建議實施風險管理措施")
        
        # 基於增量ROI的建議
        incremental_roi = roi_metrics.get('incremental_roi')
        if incremental_roi is not None and incremental_roi < simple_roi:
            recommendations.append("增量投資ROI低於平均水準，建議重新評估追加投資")
        
        return recommendations

class RevenueTracker:
    """收入追蹤器"""
    
    def __init__(self):
        self.revenue_streams: List[RevenueStream] = []
        self.revenue_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def add_revenue_stream(self, stream: RevenueStream):
        """添加收入流"""
        self.revenue_streams.append(stream)
        self.logger.info(f"Added revenue stream: {stream.name}")
    
    def calculate_total_revenue(self, period: MetricPeriod = MetricPeriod.MONTHLY) -> float:
        """計算總收入"""
        total_revenue = 0.0
        
        for stream in self.revenue_streams:
            if stream.recurring:
                # 重複收入按週期計算
                period_multiplier = self._get_period_multiplier(stream.frequency, period)
                total_revenue += stream.amount * period_multiplier
            else:
                # 一次性收入
                total_revenue += stream.amount
        
        return total_revenue
    
    def calculate_arr(self) -> float:
        """計算年度重複收入(ARR)"""
        arr = 0.0
        for stream in self.revenue_streams:
            if stream.recurring:
                # 轉換為年度收入
                if stream.frequency == "monthly":
                    arr += stream.amount * 12
                elif stream.frequency == "quarterly":
                    arr += stream.amount * 4
                elif stream.frequency == "yearly":
                    arr += stream.amount
                elif stream.frequency == "weekly":
                    arr += stream.amount * 52
        
        return arr
    
    def calculate_mrr(self) -> float:
        """計算月度重複收入(MRR)"""
        return self.calculate_arr() / 12
    
    def calculate_revenue_growth(self, periods: int = 12) -> float:
        """計算收入增長率"""
        if len(self.revenue_history) < periods:
            return 0.0
        
        current_revenue = self.revenue_history[-1].get('total_revenue', 0)
        past_revenue = self.revenue_history[-periods].get('total_revenue', 0)
        
        if past_revenue <= 0:
            return 0.0
        
        return ((current_revenue - past_revenue) / past_revenue) * 100
    
    def forecast_revenue(self, periods: int, confidence_interval: float = 0.95) -> Dict[str, Any]:
        """預測收入"""
        forecast_result = {
            'periods': periods,
            'forecasted_values': [],
            'confidence_interval': confidence_interval,
            'methodology': 'linear_trend'
        }
        
        if len(self.revenue_history) < 3:
            return forecast_result
        
        # 提取歷史收入數據
        historical_values = [h.get('total_revenue', 0) for h in self.revenue_history[-12:]]
        
        # 簡單線性趨勢預測
        x = np.arange(len(historical_values))
        y = np.array(historical_values)
        
        # 線性回歸
        z = np.polyfit(x, y, 1)
        trend = np.poly1d(z)
        
        # 預測未來值
        for i in range(periods):
            future_x = len(historical_values) + i
            predicted_value = trend(future_x)
            
            # 添加一些隨機性
            std_dev = np.std(historical_values) * 0.1
            lower_bound = predicted_value - (std_dev * 1.96)
            upper_bound = predicted_value + (std_dev * 1.96)
            
            forecast_result['forecasted_values'].append({
                'period': i + 1,
                'predicted_value': max(0, predicted_value),
                'lower_bound': max(0, lower_bound),
                'upper_bound': upper_bound
            })
        
        return forecast_result
    
    def _get_period_multiplier(self, frequency: str, period: MetricPeriod) -> float:
        """獲取週期乘數"""
        frequency_map = {
            "daily": 1,
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90,
            "yearly": 365
        }
        
        period_map = {
            MetricPeriod.DAILY: 1,
            MetricPeriod.WEEKLY: 7,
            MetricPeriod.MONTHLY: 30,
            MetricPeriod.QUARTERLY: 90,
            MetricPeriod.YEARLY: 365
        }
        
        freq_days = frequency_map.get(frequency, 30)
        period_days = period_map.get(period, 30)
        
        return period_days / freq_days
    
    def track_revenue_performance(self, actual_revenue: float, period: MetricPeriod) -> Dict[str, Any]:
        """追蹤收入表現"""
        performance_data = {
            'timestamp': time.time(),
            'period': period.value,
            'actual_revenue': actual_revenue,
            'forecasted_revenue': 0.0,
            'variance': 0.0,
            'variance_percentage': 0.0,
            'performance_rating': 'on_track'
        }
        
        # 與預測比較
        if self.revenue_history:
            last_forecast = self.revenue_history[-1].get('forecast', {})
            forecasted_revenue = last_forecast.get('predicted_value', actual_revenue)
            
            performance_data['forecasted_revenue'] = forecasted_revenue
            variance = actual_revenue - forecasted_revenue
            performance_data['variance'] = variance
            
            if forecasted_revenue > 0:
                performance_data['variance_percentage'] = (variance / forecasted_revenue) * 100
                
                # 評級
                if performance_data['variance_percentage'] > 10:
                    performance_data['performance_rating'] = 'exceeding'
                elif performance_data['variance_percentage'] < -10:
                    performance_data['performance_rating'] = 'underperforming'
        
        self.revenue_history.append(performance_data)
        return performance_data

class CostAnalyzer:
    """成本分析器"""
    
    def __init__(self):
        self.cost_items: List[CostItem] = []
        self.cost_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
    
    def add_cost_item(self, cost_item: CostItem):
        """添加成本項目"""
        self.cost_items.append(cost_item)
        self.logger.info(f"Added cost item: {cost_item.name}")
    
    def calculate_total_cost(self, period: MetricPeriod = MetricPeriod.MONTHLY) -> float:
        """計算總成本"""
        return sum(item.amount for item in self.cost_items)
    
    def calculate_cost_by_category(self) -> Dict[CostCategory, float]:
        """按類別計算成本"""
        cost_by_category = defaultdict(float)
        for item in self.cost_items:
            cost_by_category[item.category] += item.amount
        return dict(cost_by_category)
    
    def calculate_fixed_variable_split(self) -> Dict[str, float]:
        """計算固定/可變成本分割"""
        fixed_cost = sum(item.amount for item in self.cost_items if item.fixed)
        variable_cost = sum(item.amount for item in self.cost_items if not item.fixed)
        
        return {
            'fixed_cost': fixed_cost,
            'variable_cost': variable_cost,
            'total_cost': fixed_cost + variable_cost,
            'fixed_percentage': (fixed_cost / (fixed_cost + variable_cost) * 100) if (fixed_cost + variable_cost) > 0 else 0
        }
    
    def identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """識別成本優化機會"""
        opportunities = []
        
        for item in self.cost_items:
            if item.optimization_potential > 0.1:  # 10%以上優化潜力
                opportunity = {
                    'cost_item': item.name,
                    'category': item.category.value,
                    'current_cost': item.amount,
                    'optimization_potential': item.optimization_potential,
                    'potential_savings': item.amount * item.optimization_potential,
                    'priority': 'high' if item.optimization_potential > 0.3 else 'medium'
                }
                opportunities.append(opportunity)
        
        # 按節省潛力排序
        opportunities.sort(key=lambda x: x['potential_savings'], reverse=True)
        return opportunities
    
    def analyze_cost_trends(self, periods: int = 12) -> Dict[str, Any]:
        """分析成本趨勢"""
        if len(self.cost_history) < periods:
            return {'status': 'insufficient_data'}
        
        recent_costs = [h.get('total_cost', 0) for h in self.cost_history[-periods:]]
        
        # 計算趨勢
        x = np.arange(len(recent_costs))
        y = np.array(recent_costs)
        
        if len(y) > 1:
            trend_slope = np.polyfit(x, y, 1)[0]
            trend_direction = 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable'
        else:
            trend_slope = 0
            trend_direction = 'stable'
        
        return {
            'trend_direction': trend_direction,
            'trend_slope': trend_slope,
            'average_cost': np.mean(recent_costs),
            'cost_volatility': np.std(recent_costs),
            'min_cost': np.min(recent_costs),
            'max_cost': np.max(recent_costs),
            'periods_analyzed': len(recent_costs)
        }

class ProfitabilityMetrics:
    """盈利能力指標"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_gross_profit(self, revenue: float, cogs: float) -> Dict[str, float]:
        """計算毛利"""
        gross_profit = revenue - cogs
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        
        return {
            'gross_profit': gross_profit,
            'gross_margin_percentage': gross_margin,
            'cogs_ratio': (cogs / revenue * 100) if revenue > 0 else 0
        }
    
    def calculate_ebitda(self, gross_profit: float, operating_expenses: float, 
                        depreciation: float = 0, amortization: float = 0) -> Dict[str, float]:
        """計算EBITDA"""
        ebitda = gross_profit - operating_expenses + depreciation + amortization
        
        return {
            'ebitda': ebitda,
            'operating_expenses': operating_expenses,
            'depreciation_amortization': depreciation + amortization
        }
    
    def calculate_unit_economics(self, revenue_per_unit: float, cost_per_unit: float) -> Dict[str, float]:
        """計算單位經濟效益"""
        unit_profit = revenue_per_unit - cost_per_unit
        unit_margin = (unit_profit / revenue_per_unit * 100) if revenue_per_unit > 0 else 0
        
        return {
            'revenue_per_unit': revenue_per_unit,
            'cost_per_unit': cost_per_unit,
            'unit_profit': unit_profit,
            'unit_margin_percentage': unit_margin
        }

class MarketValueMetrics:
    """市場價值指標"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_customer_metrics(self, customer_data: Dict[str, Any]) -> Dict[str, float]:
        """計算客戶指標"""
        total_customers = customer_data.get('total_customers', 0)
        new_customers = customer_data.get('new_customers', 0)
        churned_customers = customer_data.get('churned_customers', 0)
        
        # 客戶增長率
        customer_growth_rate = 0
        if total_customers > 0:
            customer_growth_rate = ((new_customers - churned_customers) / total_customers) * 100
        
        # 流失率
        churn_rate = (churned_customers / total_customers * 100) if total_customers > 0 else 0
        
        # 保留率
        retention_rate = 100 - churn_rate
        
        return {
            'customer_growth_rate': customer_growth_rate,
            'churn_rate': churn_rate,
            'retention_rate': retention_rate,
            'net_customer_adds': new_customers - churned_customers
        }
    
    def calculate_market_penetration(self, customer_base: int, target_market_size: int) -> float:
        """計算市場滲透率"""
        if target_market_size <= 0:
            return 0.0
        return (customer_base / target_market_size) * 100

class CommercialMetricsEngine:
    """商業指標引擎"""
    
    def __init__(self):
        self.roi_analyzer = ROIAnalyzer()
        self.revenue_tracker = RevenueTracker()
        self.cost_analyzer = CostAnalyzer()
        self.profitability_metrics = ProfitabilityMetrics()
        self.market_metrics = MarketValueMetrics()
        self.metrics_history: List[BusinessValue] = []
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("CommercialMetricsEngine initialized")
    
    async def calculate_comprehensive_metrics(self, business_data: Dict[str, Any]) -> BusinessValue:
        """計算綜合商業指標"""
        try:
            business_value = BusinessValue(
                name=business_data.get('name', 'Business Metrics'),
                description=business_data.get('description', 'Comprehensive business metrics analysis')
            )
            
            # 基本財務數據
            revenue = business_data.get('revenue', 0)
            costs = business_data.get('costs', 0)
            investment = business_data.get('investment', 0)
            
            business_value.revenue = revenue
            business_value.cost = costs
            business_value.profit = revenue - costs
            
            # ROI計算
            if investment > 0:
                roi_analysis = await self.roi_analyzer.perform_roi_analysis({
                    'total_investment': investment,
                    'total_returns': revenue,
                    'investment_period_years': business_data.get('period_years', 1)
                })
                business_value.roi = roi_analysis['roi_metrics'].get('simple_roi', 0)
            
            # 客戶指標
            customer_data = business_data.get('customer_metrics', {})
            if customer_data:
                customer_metrics = self.market_metrics.calculate_customer_metrics(customer_data)
                business_value.retention_rate = customer_metrics['retention_rate']
                business_value.churn_rate = customer_metrics['churn_rate']
                business_value.customer_count = customer_data.get('total_customers', 0)
            
            # 市場指標
            target_market = business_data.get('target_market_size', 0)
            if target_market > 0:
                business_value.market_share = self.market_metrics.calculate_market_penetration(
                    business_value.customer_count, target_market
                )
            
            # 營運指標
            business_value.conversion_rate = business_data.get('conversion_rate', 0)
            business_value.engagement_score = business_data.get('engagement_score', 0)
            business_value.utilization_rate = business_data.get('utilization_rate', 0)
            
            # 增長指標
            business_value.growth_rate = business_data.get('growth_rate', 0)
            business_value.user_growth = business_data.get('user_growth', 0)
            business_value.revenue_growth = business_data.get('revenue_growth', 0)
            
            # 質量指標
            business_value.confidence_level = business_data.get('confidence_level', 0.8)
            business_value.data_quality_score = business_data.get('data_quality_score', 0.9)
            
            # 保存歷史
            self.metrics_history.append(business_value)
            
            self.logger.info(f"Comprehensive metrics calculated for {business_value.name}")
            return business_value
            
        except Exception as e:
            self.logger.error(f"Comprehensive metrics calculation failed: {e}")
            raise
    
    def get_metrics_dashboard(self, limit: int = 10) -> Dict[str, Any]:
        """獲取指標儀表板"""
        dashboard = {
            'summary': {},
            'recent_metrics': [],
            'trends': {},
            'alerts': []
        }
        
        if not self.metrics_history:
            return dashboard
        
        recent_metrics = self.metrics_history[-limit:]
        dashboard['recent_metrics'] = [
            {
                'name': bv.name,
                'revenue': bv.revenue,
                'profit': bv.profit,
                'roi': bv.roi,
                'customer_count': bv.customer_count,
                'retention_rate': bv.retention_rate,
                'timestamp': bv.timestamp
            }
            for bv in recent_metrics
        ]
        
        # 摘要統計
        latest = recent_metrics[-1]
        dashboard['summary'] = {
            'total_revenue': latest.revenue,
            'total_profit': latest.profit,
            'roi_percentage': latest.roi,
            'customer_count': latest.customer_count,
            'retention_rate': latest.retention_rate,
            'profit_margin': latest.calculate_profit_margin()
        }
        
        # 趨勢分析
        if len(recent_metrics) > 1:
            revenue_trend = (recent_metrics[-1].revenue - recent_metrics[0].revenue) / len(recent_metrics)
            profit_trend = (recent_metrics[-1].profit - recent_metrics[0].profit) / len(recent_metrics)
            
            dashboard['trends'] = {
                'revenue_trend': 'increasing' if revenue_trend > 0 else 'decreasing',
                'profit_trend': 'increasing' if profit_trend > 0 else 'decreasing',
                'revenue_change': revenue_trend,
                'profit_change': profit_trend
            }
        
        # 警報
        if latest.churn_rate > 20:
            dashboard['alerts'].append('High churn rate detected')
        if latest.roi < 10:
            dashboard['alerts'].append('ROI below target threshold')
        if latest.calculate_profit_margin() < 5:
            dashboard['alerts'].append('Low profit margin')
        
        return dashboard
    
    def export_metrics(self, business_value: BusinessValue, format: str = 'json') -> str:
        """導出指標"""
        if format.lower() == 'json':
            return json.dumps({
                'value_id': business_value.value_id,
                'name': business_value.name,
                'revenue': business_value.revenue,
                'cost': business_value.cost,
                'profit': business_value.profit,
                'roi': business_value.roi,
                'customer_count': business_value.customer_count,
                'retention_rate': business_value.retention_rate,
                'churn_rate': business_value.churn_rate,
                'profit_margin': business_value.calculate_profit_margin(),
                'timestamp': business_value.timestamp
            }, indent=2)
        else:
            return str(business_value)

# 工廠函數
def create_commercial_metrics_engine() -> CommercialMetricsEngine:
    """創建商業指標引擎"""
    return CommercialMetricsEngine()

def create_business_value(name: str = "", **kwargs) -> BusinessValue:
    """創建商業價值模型"""
    return BusinessValue(name=name, **kwargs)

def create_revenue_stream(name: str, type: RevenueType, amount: float, **kwargs) -> RevenueStream:
    """創建收入流"""
    return RevenueStream(name=name, type=type, amount=amount, **kwargs)

def create_cost_item(name: str, category: CostCategory, amount: float, **kwargs) -> CostItem:
    """創建成本項目"""
    return CostItem(name=name, category=category, amount=amount, **kwargs)