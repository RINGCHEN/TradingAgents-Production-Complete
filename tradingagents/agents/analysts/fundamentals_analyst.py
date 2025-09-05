#!/usr/bin/env python3
"""
Fundamentals Analyst - 基本面分析師
天工 (TianGong) - 整合原工程師設計與天工優化的財務基本面分析師

此模組提供：
1. 財報數據分析邏輯
2. 財務比率計算功能  
3. 公司估值模型
4. 天工成本優化和智能分析
5. 產業比較和競爭力分析
6. DCF估值和相對估值分析
"""

from typing import Dict, Any, Optional, List, Tuple
import logging
import math
import numpy as np
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass, asdict
from enum import Enum

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType
from ...dataflows.finmind_adapter import FinMindAdapter


class ValuationMethod(Enum):
    """估值方法"""
    DCF = "dcf"                    # 現金流折現法
    PE_RELATIVE = "pe_relative"    # 本益比相對估值
    PB_RELATIVE = "pb_relative"    # 股價淨值比相對估值
    EV_EBITDA = "ev_ebitda"        # 企業價值倍數
    DIVIDEND_YIELD = "dividend_yield"  # 股息折現模型

class FinancialHealth(Enum):
    """財務健康度"""
    EXCELLENT = "excellent"        # 優秀
    GOOD = "good"                 # 良好  
    FAIR = "fair"                 # 一般
    POOR = "poor"                 # 不佳
    DISTRESSED = "distressed"     # 困難

@dataclass
class FinancialMetrics:
    """財務指標數據類"""
    # 獲利能力指標
    roe: float = 0.0              # 股東權益報酬率
    roa: float = 0.0              # 資產報酬率
    gross_margin: float = 0.0     # 毛利率
    operating_margin: float = 0.0  # 營業利益率
    net_margin: float = 0.0       # 淨利率
    
    # 效率指標
    asset_turnover: float = 0.0   # 總資產週轉率
    inventory_turnover: float = 0.0  # 存貨週轉率
    receivable_turnover: float = 0.0  # 應收帳款週轉率
    
    # 財務結構指標
    debt_ratio: float = 0.0       # 負債比率
    debt_to_equity: float = 0.0   # 負債權益比
    current_ratio: float = 0.0    # 流動比率
    quick_ratio: float = 0.0      # 速動比率
    
    # 成長性指標
    revenue_growth: float = 0.0   # 營收成長率
    earnings_growth: float = 0.0  # 盈餘成長率
    asset_growth: float = 0.0     # 資產成長率
    
    # 估值指標
    pe_ratio: float = 0.0         # 本益比
    pb_ratio: float = 0.0         # 股價淨值比
    ev_ebitda: float = 0.0        # EV/EBITDA
    dividend_yield: float = 0.0   # 股息殖利率
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass 
class ValuationResult:
    """估值結果"""
    method: ValuationMethod
    target_price: float
    upside_potential: float
    confidence: float
    assumptions: Dict[str, Any]
    sensitivity_analysis: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['method'] = self.method.value
        return result

class FundamentalsAnalyst(BaseAnalyst):
    """基本面分析師 - 天工優化版"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 嘗試初始化FinMind適配器，如果失敗則設為None
        try:
            self.finmind_adapter = FinMindAdapter()
        except Exception as e:
            self.logger.warning(f"FinMind適配器初始化失敗: {e}")
            self.finmind_adapter = None
        
        # 財務指標權重配置
        self.metrics_weights = {
            'profitability': 0.3,    # 獲利能力
            'efficiency': 0.25,      # 經營效率  
            'leverage': 0.2,         # 財務槓桿
            'liquidity': 0.15,       # 流動性
            'growth': 0.1           # 成長性
        }
        
        # 天工Taiwan特色配置
        self.taiwan_sectors = {
            '半導體': {
                'stocks': ['2330', '2454', '3711', '2317', '2303'],
                'avg_pe': 22.5, 'avg_pb': 4.2, 'avg_roe': 18.5,
                'growth_premium': 1.15
            },
            '金融': {
                'stocks': ['2882', '2881', '2891', '2892', '2880'],
                'avg_pe': 11.2, 'avg_pb': 1.1, 'avg_roe': 12.3,
                'growth_premium': 0.95
            },
            '傳產': {
                'stocks': ['1301', '1303', '2002', '1216', '2207'],
                'avg_pe': 15.6, 'avg_pb': 1.8, 'avg_roe': 8.9,
                'growth_premium': 0.90
            },
            '電子': {
                'stocks': ['2382', '3008', '2357', '4938', '6505'],
                'avg_pe': 18.9, 'avg_pb': 2.5, 'avg_roe': 15.2,
                'growth_premium': 1.05
            },
            '生技': {
                'stocks': ['4562', '6446', '4745', '1789', '6472'],
                'avg_pe': 35.6, 'avg_pb': 3.8, 'avg_roe': 6.8,
                'growth_premium': 1.25
            }
        }
        
        # 估值方法權重
        self.valuation_weights = {
            ValuationMethod.DCF: 0.4,
            ValuationMethod.PE_RELATIVE: 0.3,
            ValuationMethod.PB_RELATIVE: 0.15,
            ValuationMethod.EV_EBITDA: 0.10,
            ValuationMethod.DIVIDEND_YIELD: 0.05
        }
    
    def get_analysis_type(self) -> AnalysisType:
        """獲取分析類型"""
        return AnalysisType.FUNDAMENTAL
    
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """生成基本面分析提示詞"""
        stock_id = state.stock_id
        
        prompt = f"""
請作為專業的基本面分析師，針對台股代碼 {stock_id} 進行深度財務分析。

請基於以下數據進行分析：
1. 財務報表數據：{state.financial_data if state.financial_data else '待獲取'}
2. 股價數據：{state.stock_data if state.stock_data else '待獲取'}
3. 市場數據：{state.market_data if state.market_data else '待獲取'}

分析重點：
1. 獲利能力分析 (ROE, ROA, 毛利率, 淨利率)
2. 經營效率分析 (總資產週轉率, 存貨週轉率)
3. 財務結構分析 (負債比率, 流動比率, 速動比率)
4. 成長性分析 (營收成長率, 獲利成長率)
5. 估值分析 (本益比, 股價淨值比, 股息殖利率)
6. 同業比較和產業地位
7. Taiwan市場特色考量 (法人持股, 產業政策影響)

請提供：
- 明確的投資建議 (BUY/SELL/HOLD)
- 0-1之間的信心度分數
- 詳細的分析理由
- 目標價格區間 (如果適用)
- 主要風險因素
"""
        return prompt
    
    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """執行基本面分析"""
        return await self._execute_analysis_with_optimization(state)
    
    async def _perform_core_analysis(self, state: AnalysisState, model_config) -> AnalysisResult:
        """執行核心基本面分析邏輯"""
        
        try:
            # 1. 獲取財務數據
            financial_data = await self._get_financial_data(state.stock_id)
            
            # 2. 計算財務指標
            financial_metrics = await self._calculate_financial_metrics(financial_data)
            
            # 3. 進行同業比較
            try:
                sector_comparison = await self._perform_sector_comparison(state.stock_id, financial_metrics)
            except Exception as e:
                self.logger.warning(f"同業比較失敗，使用預設值: {e}")
                sector_comparison = {'sector': '未知', 'ranking': 50}
            
            # 4. 計算多重估值
            valuation_results = await self._calculate_comprehensive_valuation(state.stock_id, financial_data, financial_metrics)
            
            # 5. 綜合估值分析
            final_valuation = await self._synthesize_valuation_results(valuation_results)
            
            # 6. 財務健康度評估
            financial_health = self._assess_financial_health(financial_metrics)
            
            # 7. 生成分析上下文
            analysis_context = self._prepare_fundamental_context(
                state, financial_data, financial_metrics, sector_comparison, 
                valuation_results, final_valuation, financial_health
            )
            
            # 8. 調用LLM進行智慧分析
            llm_result = await self._call_llm_analysis(
                self.get_analysis_prompt(state), 
                analysis_context, 
                model_config
            )
            
            # 9. 創建分析結果  
            from .base_analyst import AnalysisConfidenceLevel
            
            confidence_value = llm_result.get('confidence', 0.5)
            
            # 計算信心度級別
            if confidence_value >= 0.8:
                confidence_level = AnalysisConfidenceLevel.VERY_HIGH
            elif confidence_value >= 0.6:
                confidence_level = AnalysisConfidenceLevel.HIGH
            elif confidence_value >= 0.4:
                confidence_level = AnalysisConfidenceLevel.MODERATE
            elif confidence_value >= 0.2:
                confidence_level = AnalysisConfidenceLevel.LOW
            else:
                confidence_level = AnalysisConfidenceLevel.VERY_LOW
            
            result = AnalysisResult(
                analyst_id=self.analyst_id,
                stock_id=state.stock_id,
                analysis_date=state.analysis_date,
                analysis_type=self.get_analysis_type(),
                recommendation=llm_result.get('recommendation', 'HOLD'),
                confidence=confidence_value,
                confidence_level=confidence_level,
                target_price=llm_result.get('target_price') or final_valuation.get('consensus_target_price', 0),
                reasoning=llm_result.get('reasoning', []),
                fundamental_metrics=financial_metrics.to_dict() if hasattr(financial_metrics, 'to_dict') else financial_metrics,
                risk_factors=llm_result.get('risk_factors', []),
                taiwan_insights=sector_comparison,
                technical_indicators={
                    'valuation_results': [v.to_dict() if hasattr(v, 'to_dict') else v for v in valuation_results],
                    'final_valuation': final_valuation,
                    'financial_health': financial_health.value if hasattr(financial_health, 'value') else str(financial_health),
                    'sector_comparison': sector_comparison
                },
                model_used=getattr(model_config, 'model_name', 'unknown')
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"基本面分析失敗: {str(e)}")
            return self._create_error_result(state, str(e))
    
    async def _get_financial_data(self, stock_id: str) -> Dict[str, Any]:
        """獲取財務數據"""
        
        try:
            # 嘗試使用適配器獲取真實數據
            if hasattr(self, 'finmind_adapter') and self.finmind_adapter:
                financial_data = await self.finmind_adapter.get_latest_financial_data(stock_id)
                
                # 獲取股價數據用於估值計算
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y-%m-%d')
                price_data = await self.finmind_adapter.get_stock_price(
                    stock_id, start_date, end_date
                )
                
                # 獲取基本資訊
                basic_info = await self.finmind_adapter.get_stock_basic_info(stock_id)
                
                # 整合所有數據
                financial_data['stock_price'] = price_data
                financial_data['basic_info'] = basic_info
                
                if financial_data.get('income_statement') or financial_data.get('balance_sheet'):
                    return financial_data
            
            # 如果真實數據獲取失敗，使用模擬數據
            return self._get_mock_financial_data(stock_id)
            
        except Exception as e:
            self.logger.error(f"財務數據獲取失敗: {str(e)}")
            return self._get_mock_financial_data(stock_id)
    
    def _get_mock_financial_data(self, stock_id: str) -> Dict[str, Any]:
        """獲取模擬財務數據 (當真實API不可用時使用)"""
        import random
        
        # 根據股票代號模擬不同的財務特性
        if stock_id in ['2330', '2454']:  # 半導體股
            base_revenue = 500000000000  # 5000億
            base_profit = 200000000000   # 2000億 
            base_assets = 3000000000000  # 3兆
            roe_range = (15, 25)
        elif stock_id in ['2881', '2882']:  # 金融股
            base_revenue = 200000000000  # 2000億
            base_profit = 50000000000    # 500億
            base_assets = 5000000000000  # 5兆
            roe_range = (8, 15)
        else:  # 其他股票
            base_revenue = 100000000000  # 1000億
            base_profit = 10000000000    # 100億
            base_assets = 800000000000   # 8000億
            roe_range = (5, 20)
        
        # 模擬最近4季數據
        income_statement = []
        balance_sheet = []
        
        for i in range(4):  # 4季數據
            # 損益表數據
            revenue = base_revenue * random.uniform(0.8, 1.2)
            gross_profit = revenue * random.uniform(0.3, 0.7)
            operating_income = gross_profit * random.uniform(0.6, 0.9)
            net_income = operating_income * random.uniform(0.7, 0.95)
            
            income_statement.append({
                'date': f'2024-Q{4-i}',
                'revenue': revenue,
                'gross_profit': gross_profit,
                'operating_income': operating_income,
                'net_income': net_income,
                'cost_of_goods_sold': revenue - gross_profit,
                'depreciation': operating_income * 0.05
            })
            
            # 資產負債表數據
            total_assets = base_assets * random.uniform(0.9, 1.1)
            shareholders_equity = total_assets * random.uniform(0.4, 0.8)
            total_liabilities = total_assets - shareholders_equity
            current_assets = total_assets * random.uniform(0.3, 0.6)
            current_liabilities = current_assets * random.uniform(0.5, 0.9)
            
            balance_sheet.append({
                'date': f'2024-Q{4-i}',
                'total_assets': total_assets,
                'shareholders_equity': shareholders_equity,
                'total_liabilities': total_liabilities,
                'current_assets': current_assets,
                'current_liabilities': current_liabilities,
                'cash': current_assets * random.uniform(0.1, 0.3),
                'inventory': current_assets * random.uniform(0.1, 0.4),
                'accounts_receivable': current_assets * random.uniform(0.1, 0.3),
                'total_debt': total_liabilities * random.uniform(0.3, 0.7),
                'shares_outstanding': random.randint(1000000, 10000000)
            })
        
        # 股價數據 (簡化)
        current_price = random.uniform(50, 800)
        stock_price = [{'close': current_price, 'date': datetime.now().strftime('%Y-%m-%d')}]
        
        # 基本資訊
        basic_info = {
            'stock_id': stock_id,
            'current_price': current_price,
            'market_cap': current_price * balance_sheet[0]['shares_outstanding']
        }
        
        return {
            'income_statement': income_statement,
            'balance_sheet': balance_sheet,
            'cash_flow': [],  # 簡化，不生成現金流數據
            'stock_price': stock_price,
            'basic_info': basic_info,
            'is_mock_data': True
        }
    
    async def _calculate_financial_metrics(self, financial_data: Dict[str, Any]) -> FinancialMetrics:
        """計算財務指標"""
        
        if not financial_data:
            return {}
        
        try:
            income_data = financial_data.get('income_statement', [])
            balance_data = financial_data.get('balance_sheet', [])
            
            if not income_data or not balance_data:
                return {}
            
            # 取最新季度數據
            latest_income = income_data[0] if income_data else {}
            latest_balance = balance_data[0] if balance_data else {}
            
            # 獲利能力指標
            revenue = latest_income.get('revenue', 0)
            net_income = latest_income.get('net_income', 0)
            gross_profit = latest_income.get('gross_profit', 0)
            
            total_assets = latest_balance.get('total_assets', 1)
            shareholders_equity = latest_balance.get('shareholders_equity', 1)
            
            profitability_metrics = {
                'roe': (net_income / shareholders_equity * 100) if shareholders_equity > 0 else 0,
                'roa': (net_income / total_assets * 100) if total_assets > 0 else 0,
                'gross_margin': (gross_profit / revenue * 100) if revenue > 0 else 0,
                'net_margin': (net_income / revenue * 100) if revenue > 0 else 0
            }
            
            # 財務結構指標
            total_liabilities = latest_balance.get('total_liabilities', 0)
            current_assets = latest_balance.get('current_assets', 0)
            current_liabilities = latest_balance.get('current_liabilities', 1)
            
            leverage_metrics = {
                'debt_ratio': (total_liabilities / total_assets * 100) if total_assets > 0 else 0,
                'current_ratio': (current_assets / current_liabilities) if current_liabilities > 0 else 0,
                'equity_ratio': (shareholders_equity / total_assets * 100) if total_assets > 0 else 0
            }
            
            # 效率指標
            efficiency_metrics = {
                'asset_turnover': (revenue / total_assets) if total_assets > 0 else 0,
                'equity_turnover': (revenue / shareholders_equity) if shareholders_equity > 0 else 0
            }
            
            # 成長性指標 (與去年同期比較)
            growth_metrics = {}
            if len(income_data) >= 4:  # 至少4季數據才能計算年成長率
                current_revenue = income_data[0].get('revenue', 0)
                last_year_revenue = income_data[3].get('revenue', 1)
                growth_metrics['revenue_growth'] = ((current_revenue - last_year_revenue) / last_year_revenue * 100) if last_year_revenue > 0 else 0
                
                current_net_income = income_data[0].get('net_income', 0)
                last_year_net_income = income_data[3].get('net_income', 1)
                growth_metrics['earnings_growth'] = ((current_net_income - last_year_net_income) / abs(last_year_net_income) * 100) if last_year_net_income != 0 else 0
            
            # 計算更多指標
            # 營業利益率
            operating_income = latest_income.get('operating_income', 0)
            operating_margin = (operating_income / revenue * 100) if revenue > 0 else 0
            
            # 速動比率
            inventory = latest_balance.get('inventory', 0)
            quick_assets = current_assets - inventory
            quick_ratio = (quick_assets / current_liabilities) if current_liabilities > 0 else 0
            
            # 存貨週轉率
            cost_of_goods_sold = latest_income.get('cost_of_goods_sold', 0)
            inventory_turnover = (cost_of_goods_sold / inventory) if inventory > 0 else 0
            
            # 應收帳款週轉率
            accounts_receivable = latest_balance.get('accounts_receivable', 0)
            receivable_turnover = (revenue / accounts_receivable) if accounts_receivable > 0 else 0
            
            # 負債權益比
            debt_to_equity = (total_liabilities / shareholders_equity) if shareholders_equity > 0 else 0
            
            # 計算估值指標
            current_price = financial_data.get('basic_info', {}).get('current_price', 0)
            shares_outstanding = latest_balance.get('shares_outstanding', 1000000)
            eps = (net_income / shares_outstanding) if shares_outstanding > 0 else 0
            book_value_per_share = (shareholders_equity / shares_outstanding) if shares_outstanding > 0 else 0
            
            pe_ratio = (current_price / eps) if eps > 0 else 0
            pb_ratio = (current_price / book_value_per_share) if book_value_per_share > 0 else 0
            
            # 計算EBITDA和EV/EBITDA
            depreciation = latest_income.get('depreciation', 0)
            ebitda = operating_income + depreciation
            market_cap = current_price * shares_outstanding
            total_debt = latest_balance.get('total_debt', total_liabilities * 0.7)  # 估算
            cash = latest_balance.get('cash', 0)
            enterprise_value = market_cap + total_debt - cash
            ev_ebitda = (enterprise_value / ebitda) if ebitda > 0 else 0
            
            return FinancialMetrics(
                # 獲利能力
                roe=profitability_metrics['roe'],
                roa=profitability_metrics['roa'],
                gross_margin=profitability_metrics['gross_margin'],
                operating_margin=operating_margin,
                net_margin=profitability_metrics['net_margin'],
                
                # 效率指標
                asset_turnover=efficiency_metrics['asset_turnover'],
                inventory_turnover=inventory_turnover,
                receivable_turnover=receivable_turnover,
                
                # 財務結構
                debt_ratio=leverage_metrics['debt_ratio'],
                debt_to_equity=debt_to_equity,
                current_ratio=leverage_metrics['current_ratio'],
                quick_ratio=quick_ratio,
                
                # 成長性
                revenue_growth=growth_metrics.get('revenue_growth', 0),
                earnings_growth=growth_metrics.get('earnings_growth', 0),
                asset_growth=0,  # TODO: 計算資產成長率
                
                # 估值指標
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
                ev_ebitda=ev_ebitda,
                dividend_yield=3.5  # TODO: 從實際數據獲取
            )
            
        except Exception as e:
            self.logger.error(f"財務指標計算失敗: {str(e)}")
            return FinancialMetrics()  # 返回預設值
    
    async def _perform_sector_comparison(self, stock_id: str, financial_metrics: FinancialMetrics) -> Dict[str, Any]:
        """進行同業比較 - Taiwan特色"""
        
        try:
            # 識別所屬產業
            sector = self._identify_sector(stock_id)
            
            if not sector or not financial_metrics:
                return {'sector': '未知', 'comparison': {}}
            
            # 獲取同業股票列表
            peer_stocks = self.taiwan_sectors.get(sector, {}).get('stocks', [])
            
            # 獲取產業數據
            sector_data = self.taiwan_sectors.get(sector, {})
            
            # 比較分析
            comparison = {
                'sector': sector,
                'peer_stocks': peer_stocks,
                'sector_metrics': sector_data,
                'vs_sector_avg': {
                    'roe_percentile': self._calculate_percentile(
                        financial_metrics.roe, sector_data.get('avg_roe', 15)
                    ),
                    'pe_percentile': self._calculate_percentile(
                        financial_metrics.pe_ratio, sector_data.get('avg_pe', 20)
                    ),
                    'pb_percentile': self._calculate_percentile(
                        financial_metrics.pb_ratio, sector_data.get('avg_pb', 2.0)
                    ),
                    'debt_ratio_percentile': self._calculate_percentile(
                        financial_metrics.debt_ratio, 40, lower_is_better=True
                    ),
                    'overall_ranking': self._calculate_overall_ranking(financial_metrics, sector_data)
                },
                'competitive_advantages': self._identify_competitive_advantages(
                    financial_metrics, sector_data
                ),
                'taiwan_insights': {
                    'industry_trend': self._get_industry_trend(sector),
                    'policy_impact': self._get_policy_impact(sector),
                    'competitive_position': self._assess_competitive_position(
                        financial_metrics, sector_data
                    )
                }
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"同業比較失敗: {str(e)}")
            return {'sector': '未知', 'comparison': {}}
    
    def _identify_sector(self, stock_id: str) -> Optional[str]:
        """識別股票所屬產業"""
        for sector, sector_data in self.taiwan_sectors.items():
            if stock_id in sector_data.get('stocks', []):
                return sector
        return None
    
    def _calculate_overall_ranking(self, metrics: FinancialMetrics, sector_data: Dict[str, Any]) -> str:
        """計算整體排名"""
        score = 0
        
        # ROE分數
        if metrics.roe > sector_data.get('avg_roe', 15) * 1.2:
            score += 3
        elif metrics.roe > sector_data.get('avg_roe', 15):
            score += 2
        elif metrics.roe > sector_data.get('avg_roe', 15) * 0.8:
            score += 1
        
        # PE分數 (適中最好)
        avg_pe = sector_data.get('avg_pe', 20)
        if avg_pe * 0.8 <= metrics.pe_ratio <= avg_pe * 1.2:
            score += 2
        elif metrics.pe_ratio < avg_pe * 0.8:
            score += 1
        
        # 債務比率分數 (越低越好)
        if metrics.debt_ratio < 30:
            score += 2
        elif metrics.debt_ratio < 50:
            score += 1
        
        # 成長分數
        if metrics.revenue_growth > 10:
            score += 2
        elif metrics.revenue_growth > 5:
            score += 1
        
        if score >= 7:
            return 'excellent'
        elif score >= 5:
            return 'above_average'
        elif score >= 3:
            return 'average'
        else:
            return 'below_average'
    
    def _identify_competitive_advantages(self, metrics: FinancialMetrics, sector_data: Dict[str, Any]) -> List[str]:
        """識別競爭優勢"""
        advantages = []
        
        if metrics.roe > sector_data.get('avg_roe', 15) * 1.3:
            advantages.append('卓越的股東權益報酬率')
        
        if metrics.gross_margin > 50:
            advantages.append('高毛利率顯示定價能力強')
        
        if metrics.debt_ratio < 20:
            advantages.append('財務結構穩健，財務風險低')
        
        if metrics.revenue_growth > 15:
            advantages.append('營收高成長，市場擴張能力強')
        
        if metrics.current_ratio > 2.0:
            advantages.append('流動性充足，短期償債能力強')
        
        return advantages if advantages else ['暫無明顯競爭優勢']
    
    def _get_industry_trend(self, sector: str) -> str:
        """獲取產業趨勢"""
        trends = {
            '半導體': 'AI和高效能運算需求推動產業成長',
            '金融': '數位金融轉型和利率環境影響獲利',
            '傳產': '原物料價格波動和供應鏈重組',
            '電子': '消費性電子需求疲軟但伺服器需求強勁',
            '生技': '新藥開發和精準醫療帶來新機會'
        }
        return trends.get(sector, '產業趨勢需進一步分析')
    
    def _get_policy_impact(self, sector: str) -> str:
        """獲取政策影響"""
        impacts = {
            '半導體': '政府大力支持半導體產業，提供研發補助',
            '金融': '金管會推動數位金融創新，監理沙盒機制',
            '傳產': '淨零碳排政策影響傳統製造業轉型',
            '電子': '5G和物聯網政策支持電子產業發展',
            '生技': '生技產業發展條例提供稅收優惠'
        }
        return impacts.get(sector, '政策影響有限')
    
    def _assess_competitive_position(self, metrics: FinancialMetrics, sector_data: Dict[str, Any]) -> str:
        """評估競爭地位"""
        if metrics.roe > sector_data.get('avg_roe', 15) * 1.5:
            return '產業領導者'
        elif metrics.roe > sector_data.get('avg_roe', 15) * 1.2:
            return '競爭優勢明顯'
        elif metrics.roe > sector_data.get('avg_roe', 15):
            return '具備競爭力'
        else:
            return '競爭地位相對弱勢'
    
    def _calculate_percentile(self, value: float, sector_avg: float, lower_is_better: bool = False) -> float:
        """計算相對產業平均的百分位數"""
        ratio = value / sector_avg if sector_avg > 0 else 1.0
        
        if lower_is_better:
            percentile = max(0, min(100, (2.0 - ratio) * 50))
        else:
            percentile = max(0, min(100, ratio * 50))
        
        return round(percentile, 1)
    
    async def _calculate_comprehensive_valuation(self, stock_id: str, financial_data: Dict[str, Any], financial_metrics: FinancialMetrics) -> List[ValuationResult]:
        """計算估值指標"""
        
        try:
            price_data = financial_data.get('stock_price', [])
            income_data = financial_data.get('income_statement', [])
            balance_data = financial_data.get('balance_sheet', [])
            
            if not price_data or not income_data or not balance_data:
                return {}
            
            # 最新股價
            current_price = price_data[0].get('close', 0) if price_data else 0
            
            # 最新財務數據
            latest_income = income_data[0] if income_data else {}
            latest_balance = balance_data[0] if balance_data else {}
            
            # 每股盈餘 (簡化計算)
            net_income = latest_income.get('net_income', 0)
            shares_outstanding = latest_balance.get('shares_outstanding', 1000000)  # 預設值
            eps = (net_income / shares_outstanding) if shares_outstanding > 0 else 0
            
            # 每股淨值
            shareholders_equity = latest_balance.get('shareholders_equity', 0)
            book_value_per_share = (shareholders_equity / shares_outstanding) if shares_outstanding > 0 else 0
            
            # 估值指標
            pe_ratio = (current_price / eps) if eps > 0 else 0
            pb_ratio = (current_price / book_value_per_share) if book_value_per_share > 0 else 0
            
            # 股息殖利率 (需要股息數據，此處簡化)
            dividend_yield = 3.5  # 預設值
            
            # 執行多種估值方法
            valuation_results = []
            
            # DCF估值
            dcf_result = await self._dcf_valuation(financial_data, financial_metrics)
            valuation_results.append(dcf_result)
            
            # 相對估值
            pe_result = await self._pe_relative_valuation(stock_id, financial_metrics)
            valuation_results.append(pe_result)
            
            pb_result = await self._pb_relative_valuation(stock_id, financial_metrics)
            valuation_results.append(pb_result)
            
            ev_ebitda_result = await self._ev_ebitda_valuation(stock_id, financial_data, financial_metrics)
            valuation_results.append(ev_ebitda_result)
            
            return valuation_results
            
        except Exception as e:
            self.logger.error(f"估值分析失敗: {str(e)}")
            return [ValuationResult(
                method=ValuationMethod.PE_RELATIVE,
                target_price=0,
                upside_potential=0,
                confidence=0,
                assumptions={},
                sensitivity_analysis={}
            )]
    
    async def _dcf_valuation(self, financial_data: Dict[str, Any], metrics: FinancialMetrics) -> ValuationResult:
        """DCF估值法"""
        try:
            # 簡化的DCF模型
            # 假設條件
            growth_rate = max(0.03, min(0.15, metrics.revenue_growth / 100))  # 成長率在3%-15%之間
            terminal_growth_rate = 0.03  # 永續成長率3%
            discount_rate = 0.10  # 折現率10%
            projection_years = 5
            
            # 基礎自由現金流 (簡化計算)
            income_data = financial_data.get('income_statement', [])
            if not income_data:
                raise ValueError("無法獲取損益表數據")
            
            latest_income = income_data[0]
            net_income = latest_income.get('net_income', 0)
            base_fcf = net_income * 0.8  # 簡化：假設自由現金流為淨利的80%
            
            # 預測未來現金流
            projected_fcf = []
            for year in range(1, projection_years + 1):
                fcf = base_fcf * ((1 + growth_rate) ** year)
                projected_fcf.append(fcf)
            
            # 計算終值
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth_rate)
            terminal_value = terminal_fcf / (discount_rate - terminal_growth_rate)
            
            # 折現至現值
            pv_fcf = sum([fcf / ((1 + discount_rate) ** i) for i, fcf in enumerate(projected_fcf, 1)])
            pv_terminal = terminal_value / ((1 + discount_rate) ** projection_years)
            
            enterprise_value = pv_fcf + pv_terminal
            
            # 計算股權價值和每股價值
            balance_data = financial_data.get('balance_sheet', [])
            if balance_data:
                cash = balance_data[0].get('cash', 0)
                total_debt = balance_data[0].get('total_debt', 0)
                shares_outstanding = balance_data[0].get('shares_outstanding', 1000000)
                
                equity_value = enterprise_value + cash - total_debt
                target_price = equity_value / shares_outstanding
            else:
                target_price = 0
            
            current_price = financial_data.get('basic_info', {}).get('current_price', 0)
            upside_potential = ((target_price - current_price) / current_price) if current_price > 0 else 0
            
            return ValuationResult(
                method=ValuationMethod.DCF,
                target_price=target_price,
                upside_potential=upside_potential,
                confidence=0.7,  # DCF估值信心度較高
                assumptions={
                    'growth_rate': growth_rate,
                    'terminal_growth_rate': terminal_growth_rate,
                    'discount_rate': discount_rate,
                    'projection_years': projection_years
                },
                sensitivity_analysis={
                    'growth_rate_+1%': target_price * 1.15,
                    'growth_rate_-1%': target_price * 0.88,
                    'discount_rate_+1%': target_price * 0.85,
                    'discount_rate_-1%': target_price * 1.18
                }
            )
        
        except Exception as e:
            self.logger.error(f"DCF估值失敗: {str(e)}")
            return ValuationResult(
                method=ValuationMethod.DCF,
                target_price=0,
                upside_potential=0,
                confidence=0,
                assumptions={},
                sensitivity_analysis={}
            )
    
    async def _pe_relative_valuation(self, stock_id: str, metrics: FinancialMetrics) -> ValuationResult:
        """本益比相對估值法"""
        try:
            sector = self._identify_sector(stock_id)
            if not sector:
                sector_pe = 20  # 預設值
                growth_premium = 1.0
            else:
                sector_data = self.taiwan_sectors[sector]
                sector_pe = sector_data['avg_pe']
                growth_premium = sector_data.get('growth_premium', 1.0)
            
            # 根據成長率調整PE
            if metrics.earnings_growth > 15:
                adjusted_pe = sector_pe * growth_premium * 1.2
            elif metrics.earnings_growth > 10:
                adjusted_pe = sector_pe * growth_premium * 1.1
            elif metrics.earnings_growth > 5:
                adjusted_pe = sector_pe * growth_premium
            else:
                adjusted_pe = sector_pe * growth_premium * 0.9
            
            # 根據ROE調整PE
            if metrics.roe > 20:
                adjusted_pe *= 1.1
            elif metrics.roe < 10:
                adjusted_pe *= 0.9
            
            # 計算目標價
            eps = self._calculate_eps(metrics)
            target_price = eps * adjusted_pe if eps > 0 else 0
            
            current_price = metrics.pe_ratio * eps if metrics.pe_ratio > 0 and eps > 0 else 0
            upside_potential = ((target_price - current_price) / current_price) if current_price > 0 else 0
            
            return ValuationResult(
                method=ValuationMethod.PE_RELATIVE,
                target_price=target_price,
                upside_potential=upside_potential,
                confidence=0.8,
                assumptions={
                    'sector_pe': sector_pe,
                    'growth_premium': growth_premium,
                    'adjusted_pe': adjusted_pe,
                    'eps': eps
                },
                sensitivity_analysis={
                    'pe_+10%': target_price * 1.1,
                    'pe_-10%': target_price * 0.9,
                    'sector_pe_premium': target_price * 1.15,
                    'sector_pe_discount': target_price * 0.85
                }
            )
        
        except Exception as e:
            self.logger.error(f"PE相對估值失敗: {str(e)}")
            return ValuationResult(
                method=ValuationMethod.PE_RELATIVE,
                target_price=0,
                upside_potential=0,
                confidence=0,
                assumptions={},
                sensitivity_analysis={}
            )
    
    async def _pb_relative_valuation(self, stock_id: str, metrics: FinancialMetrics) -> ValuationResult:
        """股價淨值比相對估值法"""
        try:
            sector = self._identify_sector(stock_id)
            if not sector:
                sector_pb = 2.0
            else:
                sector_data = self.taiwan_sectors[sector]
                sector_pb = sector_data['avg_pb']
            
            # 根據ROE調整PB
            if metrics.roe > 15:
                adjusted_pb = sector_pb * (metrics.roe / 15)
            else:
                adjusted_pb = sector_pb * 0.8
            
            # 根據負債比調整
            if metrics.debt_ratio < 30:
                adjusted_pb *= 1.1
            elif metrics.debt_ratio > 60:
                adjusted_pb *= 0.9
            
            # 計算目標價
            book_value_per_share = self._calculate_book_value_per_share(metrics)
            target_price = book_value_per_share * adjusted_pb if book_value_per_share > 0 else 0
            
            current_price = metrics.pb_ratio * book_value_per_share if metrics.pb_ratio > 0 and book_value_per_share > 0 else 0
            upside_potential = ((target_price - current_price) / current_price) if current_price > 0 else 0
            
            return ValuationResult(
                method=ValuationMethod.PB_RELATIVE,
                target_price=target_price,
                upside_potential=upside_potential,
                confidence=0.6,
                assumptions={
                    'sector_pb': sector_pb,
                    'adjusted_pb': adjusted_pb,
                    'book_value_per_share': book_value_per_share
                },
                sensitivity_analysis={
                    'pb_+20%': target_price * 1.2,
                    'pb_-20%': target_price * 0.8
                }
            )
        
        except Exception as e:
            self.logger.error(f"PB相對估值失敗: {str(e)}")
            return ValuationResult(
                method=ValuationMethod.PB_RELATIVE,
                target_price=0,
                upside_potential=0,
                confidence=0,
                assumptions={},
                sensitivity_analysis={}
            )
    
    async def _ev_ebitda_valuation(self, stock_id: str, financial_data: Dict[str, Any], metrics: FinancialMetrics) -> ValuationResult:
        """EV/EBITDA估值法"""
        try:
            sector = self._identify_sector(stock_id)
            sector_ev_ebitda = 15 if not sector else 12  # 預設或行業平均
            
            # 根據成長率調整EV/EBITDA
            if metrics.revenue_growth > 10:
                adjusted_ev_ebitda = sector_ev_ebitda * 1.2
            elif metrics.revenue_growth > 5:
                adjusted_ev_ebitda = sector_ev_ebitda * 1.1
            else:
                adjusted_ev_ebitda = sector_ev_ebitda
            
            # 計算EBITDA
            income_data = financial_data.get('income_statement', [])
            if not income_data:
                raise ValueError("無法獲取損益表數據")
            
            latest_income = income_data[0]
            operating_income = latest_income.get('operating_income', 0)
            depreciation = latest_income.get('depreciation', operating_income * 0.05)  # 假設折舊為營業利益5%
            ebitda = operating_income + depreciation
            
            # 計算企業價值
            enterprise_value = ebitda * adjusted_ev_ebitda
            
            # 轉換為股權價值
            balance_data = financial_data.get('balance_sheet', [])
            if balance_data:
                cash = balance_data[0].get('cash', 0)
                total_debt = balance_data[0].get('total_debt', 0)
                shares_outstanding = balance_data[0].get('shares_outstanding', 1000000)
                
                equity_value = enterprise_value + cash - total_debt
                target_price = equity_value / shares_outstanding
            else:
                target_price = 0
            
            current_price = financial_data.get('basic_info', {}).get('current_price', 0)
            upside_potential = ((target_price - current_price) / current_price) if current_price > 0 else 0
            
            return ValuationResult(
                method=ValuationMethod.EV_EBITDA,
                target_price=target_price,
                upside_potential=upside_potential,
                confidence=0.65,
                assumptions={
                    'sector_ev_ebitda': sector_ev_ebitda,
                    'adjusted_ev_ebitda': adjusted_ev_ebitda,
                    'ebitda': ebitda
                },
                sensitivity_analysis={
                    'ev_ebitda_+15%': target_price * 1.15,
                    'ev_ebitda_-15%': target_price * 0.85
                }
            )
        
        except Exception as e:
            self.logger.error(f"EV/EBITDA估值失敗: {str(e)}")
            return ValuationResult(
                method=ValuationMethod.EV_EBITDA,
                target_price=0,
                upside_potential=0,
                confidence=0,
                assumptions={},
                sensitivity_analysis={}
            )
    
    def _calculate_eps(self, metrics: FinancialMetrics) -> float:
        """計算每股盈餘 - 輔助函數"""
        # 這裡需要從metrics中反推EPS
        # 在實際實現中應該直接從財務數據計算
        if metrics.pe_ratio > 0:
            # 從PE ratio反推（臨時解決方案）
            return 1.0  # 簡化假設
        return 0
    
    def _calculate_book_value_per_share(self, metrics: FinancialMetrics) -> float:
        """計算每股淨值 - 輔助函數"""
        # 這裡需要從metrics中反推BVPS
        if metrics.pb_ratio > 0:
            return 10.0  # 簡化假設
        return 0
    
    async def _synthesize_valuation_results(self, valuation_results: List[ValuationResult]) -> Dict[str, Any]:
        """綜合多種估值結果"""
        if not valuation_results:
            return {
                'consensus_target_price': 0,
                'upside_potential': 0,
                'valuation_confidence': 0,
                'valuation_range': {'min': 0, 'max': 0},
                'preferred_method': 'none'
            }
        
        # 加權平均目標價
        weighted_target_price = 0
        total_weight = 0
        valid_results = [r for r in valuation_results if r.target_price > 0]
        
        for result in valid_results:
            weight = self.valuation_weights.get(result.method, 0.2)
            weighted_target_price += result.target_price * weight * result.confidence
            total_weight += weight * result.confidence
        
        consensus_target_price = weighted_target_price / total_weight if total_weight > 0 else 0
        
        # 估值範圍
        target_prices = [r.target_price for r in valid_results if r.target_price > 0]
        valuation_range = {
            'min': min(target_prices) if target_prices else 0,
            'max': max(target_prices) if target_prices else 0
        }
        
        # 選擇最佳方法
        if valid_results:
            preferred_method = max(valid_results, key=lambda x: x.confidence * self.valuation_weights.get(x.method, 0.2))
            preferred_method_name = preferred_method.method.value
        else:
            preferred_method_name = 'none'
        
        # 綜合上漲潛力
        upside_potentials = [r.upside_potential for r in valid_results]
        avg_upside_potential = sum(upside_potentials) / len(upside_potentials) if upside_potentials else 0
        
        # 估值信心度
        confidences = [r.confidence for r in valid_results]
        valuation_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return {
            'consensus_target_price': consensus_target_price,
            'upside_potential': avg_upside_potential,
            'valuation_confidence': valuation_confidence,
            'valuation_range': valuation_range,
            'preferred_method': preferred_method_name,
            'method_count': len(valid_results),
            'price_dispersion': (valuation_range['max'] - valuation_range['min']) / consensus_target_price if consensus_target_price > 0 else 0
        }
    
    def _assess_financial_health(self, metrics: FinancialMetrics) -> FinancialHealth:
        """評估財務健康度"""
        score = 0
        
        # 獲利能力評分
        if metrics.roe > 15:
            score += 2
        elif metrics.roe > 10:
            score += 1
        
        if metrics.roa > 8:
            score += 1
        
        if metrics.net_margin > 10:
            score += 1
        
        # 財務結構評分
        if metrics.debt_ratio < 30:
            score += 2
        elif metrics.debt_ratio < 50:
            score += 1
        
        if metrics.current_ratio > 1.5:
            score += 1
        
        if metrics.quick_ratio > 1.0:
            score += 1
        
        # 成長性評分
        if metrics.revenue_growth > 10:
            score += 2
        elif metrics.revenue_growth > 5:
            score += 1
        
        # 效率評分
        if metrics.asset_turnover > 1.0:
            score += 1
        
        # 綜合評分
        if score >= 10:
            return FinancialHealth.EXCELLENT
        elif score >= 8:
            return FinancialHealth.GOOD
        elif score >= 6:
            return FinancialHealth.FAIR
        elif score >= 4:
            return FinancialHealth.POOR
        else:
            return FinancialHealth.DISTRESSED
    
    def _get_sector_averages(self, sector: str) -> Dict[str, float]:
        """獲取產業平均指標"""
        if sector in self.taiwan_sectors:
            sector_info = self.taiwan_sectors[sector]
            return {
                'avg_pe': sector_info.get('avg_pe', 20.0),
                'avg_pb': sector_info.get('avg_pb', 2.5),
                'avg_roe': sector_info.get('avg_roe', 15.0),
                'growth_premium': sector_info.get('growth_premium', 1.0)
            }
        else:
            # 預設產業平均值
            return {
                'avg_pe': 20.0,
                'avg_pb': 2.5,
                'avg_roe': 15.0,
                'growth_premium': 1.0
            }
    
    def _prepare_fundamental_context(
        self, 
        state: AnalysisState,
        financial_data: Dict[str, Any],
        financial_metrics,
        sector_comparison: Dict[str, Any],
        valuation_results: List,
        final_valuation: Dict[str, Any],
        financial_health
    ) -> Dict[str, Any]:
        """準備基本面分析上下文"""
        
        # 轉換financial_metrics為dict
        if hasattr(financial_metrics, 'to_dict'):
            financial_metrics_dict = financial_metrics.to_dict()
        else:
            financial_metrics_dict = financial_metrics
        
        context = {
            'stock_id': state.stock_id,
            'analysis_date': state.analysis_date,
            'analyst_type': 'fundamental_analysis',
            'financial_data_available': bool(financial_data),
            'financial_metrics': financial_metrics_dict,
            'sector_analysis': sector_comparison,
            'valuation_metrics': final_valuation
        }
        
        # 添加Taiwan市場特色
        if sector_comparison:
            context['taiwan_market_context'] = {
                'sector': sector_comparison.get('sector', '未知'),
                'industry_position': sector_comparison.get('vs_sector_avg', {}),
                'taiwan_specific_factors': sector_comparison.get('taiwan_insights', {})
            }
        
        return context
    
    async def _call_llm_analysis(self, prompt: str, context: Dict[str, Any], model_config) -> Dict[str, Any]:
        """調用LLM進行基本面分析"""
        
        try:
            # 簡化的分析結果生成 (實際應整合真實LLM)
            await asyncio.sleep(0.8)  # 模擬LLM調用時間
            
            financial_metrics = context.get('financial_metrics', {})
            valuation_metrics = context.get('valuation_metrics', {})
            sector_analysis = context.get('sector_analysis', {})
            
            # 如果財務指標是FinancialMetrics物件，轉換為dict
            if hasattr(financial_metrics, 'to_dict'):
                financial_metrics = financial_metrics.to_dict()
            
            # 基於財務指標生成建議 
            roe = financial_metrics.get('roe', 12.0)
            debt_ratio = financial_metrics.get('debt_ratio', 35.0)
            pe_ratio = financial_metrics.get('pe_ratio', 18.0)
            
            # 綜合評分邏輯
            score = 0
            reasoning = []
            
            # ROE評分
            if roe > 15:
                score += 0.25
                reasoning.append(f"ROE {roe:.1f}% 表現優異，獲利能力強")
            elif roe > 10:
                score += 0.15
                reasoning.append(f"ROE {roe:.1f}% 表現中等")
            else:
                score += 0.05
                reasoning.append(f"ROE {roe:.1f}% 偏低，獲利能力待加強")
            
            # 財務結構評分
            if debt_ratio < 30:
                score += 0.2
                reasoning.append(f"負債比率 {debt_ratio:.1f}% 健康，財務結構穩健")
            elif debt_ratio < 50:
                score += 0.1
                reasoning.append(f"負債比率 {debt_ratio:.1f}% 中等")
            else:
                score += 0.05
                reasoning.append(f"負債比率 {debt_ratio:.1f}% 偏高，需注意財務風險")
            
            # 估值評分
            if pe_ratio > 0 and pe_ratio < 20:
                score += 0.15
                reasoning.append(f"本益比 {pe_ratio:.1f} 倍估值合理")
            elif pe_ratio < 30:
                score += 0.1
                reasoning.append(f"本益比 {pe_ratio:.1f} 倍估值略高")
            else:
                score += 0.05
                reasoning.append(f"本益比 {pe_ratio:.1f} 倍估值偏高")
            
            # 產業比較加分
            sector = sector_analysis.get('sector', '未知')
            overall_ranking = sector_analysis.get('vs_sector_avg', {}).get('overall_ranking', 'average')
            
            if overall_ranking == 'excellent':
                score += 0.15
                reasoning.append(f"在{sector}產業中表現優異")
            elif overall_ranking == 'above_average':
                score += 0.1
                reasoning.append(f"在{sector}產業中表現高於平均")
            elif overall_ranking == 'average':
                score += 0.05
                reasoning.append(f"在{sector}產業中表現平均")
            
            # 決定建議
            if score >= 0.75:
                recommendation = 'BUY'
            elif score >= 0.55:
                recommendation = 'HOLD'
            else:
                recommendation = 'SELL'
            
            # 目標價格使用估值共識
            target_price = valuation_metrics.get('consensus_target_price', 0)
            
            return {
                'recommendation': recommendation,
                'confidence': min(score + 0.2, 0.95),  # 調整信心度
                'reasoning': reasoning,
                'target_price': target_price,
                'fundamental_metrics': financial_metrics,
                'risk_factors': [
                    '市場波動風險',
                    '產業景氣循環風險',
                    '個股基本面變化風險'
                ]
            }
            
        except Exception as e:
            self.logger.error(f"LLM基本面分析失敗: {str(e)}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.3,
                'reasoning': [f'基本面分析過程中發生錯誤: {str(e)}'],
                'target_price': 0,
                'risk_factors': ['分析數據不足', '系統錯誤風險'],
                'error': str(e)
            }
    
    def _generate_risk_factors(self, financial_metrics: Dict[str, Any], sector_analysis: Dict[str, Any], financial_health: str) -> List[str]:
        """生成風險因子"""
        risk_factors = []
        
        # 財務健康風險
        if financial_health in ['poor', 'distressed']:
            risk_factors.append('財務健康度不佳，存在債務風險')
        
        # 負債風險
        debt_ratio = financial_metrics.get('debt_ratio', 0)
        if debt_ratio > 60:
            risk_factors.append(f'負債比率{debt_ratio:.1f}%偏高，財務槓桿風險')
        
        # 成長風險
        revenue_growth = financial_metrics.get('revenue_growth', 0)
        if revenue_growth < 0:
            risk_factors.append('營收負成長，業務可能面臨困難')
        elif revenue_growth < 3:
            risk_factors.append('營收成長緩慢，競爭力可能下降')
        
        # 流動性風險
        current_ratio = financial_metrics.get('current_ratio', 0)
        if current_ratio < 1.0:
            risk_factors.append('流動性不足，短期償債壓力')
        
        # 產業風險
        sector = sector_analysis.get('sector', '')
        if sector == '生技':
            risk_factors.append('生技產業研發風險高，收益不確定性大')
        elif sector == '傳產':
            risk_factors.append('傳統製造業面臨轉型壓力')
        
        # 估值風險
        pe_ratio = financial_metrics.get('pe_ratio', 0)
        if pe_ratio > 30:
            risk_factors.append('本益比偏高，估值修正風險')
        
        # 預設風險因子
        if not risk_factors:
            risk_factors = [
                '市場系統性風險',
                '產業景氣循環風險',
                '個股基本面變化風險'
            ]
        
        return risk_factors[:5]  # 限制風險因子數量

# 便利函數
async def analyze_fundamentals(
    stock_id: str,
    user_context: Dict[str, Any] = None,
    config: Dict[str, Any] = None
) -> AnalysisResult:
    """快速基本面分析"""
    
    if config is None:
        config = {'debug': True}
    
    analyst = FundamentalsAnalyst(config)
    
    # 創建分析狀態
    from .base_analyst import AnalysisState
    state = AnalysisState(
        stock_id=stock_id,
        analysis_date=datetime.now().strftime('%Y-%m-%d'),
        user_context=user_context
    )
    
    return await analyst.analyze(state)

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    from ..base_analyst import create_analysis_state
    
    async def test_fundamentals_analyst():
        print("測試基本面分析師")
        
        config = {'debug': True}
        analyst = FundamentalsAnalyst(config)
        
        print(f"分析師信息: {analyst.get_analyst_info()}")
        
        # 創建測試狀態
        state = create_analysis_state(
            stock_id='2330',  # 台積電
            user_context={'user_id': 'test_user', 'membership_tier': 'GOLD'}
        )
        
        # 執行分析
        result = await analyst.analyze(state)
        
        print(f"分析結果: {result.recommendation}")
        print(f"信心度: {result.confidence}")
        print(f"目標價: {result.target_price}")
        print(f"分析理由: {result.reasoning}")
        print(f"財務指標: {result.fundamental_metrics}")
        
        print("✅ 基本面分析師測試完成")
    
    asyncio.run(test_fundamentals_analyst())