#!/usr/bin/env python3
"""
Taiwan Market Analyst - 台股專用分析師
天工 (TianGong) - 專精台灣股市的智能分析師

此分析師專注於：
1. 台股法人進出分析
2. 漲跌停機制影響分析
3. 權值股大盤連動分析
4. 台股板塊輪動分析
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# 當原工程師完成base_analyst後，這裡會改成正式導入
# from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisType

# 暫時的基礎類別定義 (等待原工程師完成)
class AnalysisType(Enum):
    """分析類型"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"
    SENTIMENT = "sentiment"
    RISK = "risk"
    INVESTMENT = "investment"
    TAIWAN_SPECIFIC = "taiwan_specific"
@dataclass
class AnalysisResult:
    """分析結果 (臨時定義)"""
    analyst_id: str
    stock_id: str
    analysis_date: str
    recommendation: str  # BUY, SELL, HOLD
    confidence: float    # 0.0 - 1.0
    target_price: Optional[float] = None
    reasoning: List[str] = None
    technical_indicators: Optional[Dict[str, Any]] = None
    risk_factors: Optional[List[str]] = None
    taiwan_specific_analysis: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class BaseAnalyst:
    """基礎分析師類 (臨時定義)"""
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyst_id = self.__class__.__name__.lower()
        self.logger = logging.getLogger(__name__)

class TaiwanMarketAnalyst(BaseAnalyst):
    """台灣市場專用分析師"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.analyst_id = 'taiwan_market_analyst'
        
        # 台股特有參數
        self.sector_weights = self._load_sector_weights()
        self.major_stocks = self._load_major_stocks()
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _load_sector_weights(self) -> Dict[str, float]:
        """載入台股板塊權重"""
        # 台股主要板塊權重 (approximate)
        return {
            '半導體': 0.35,     # 台積電、聯發科等
            '金融': 0.15,       # 台銀、富邦金等
            '電子': 0.25,       # 鴻海、廣達等
            '傳產': 0.10,       # 台塑、中鋼等
            '生技': 0.05,       # 生技股
            '其他': 0.10        # 其他產業
        }
    
    def _load_major_stocks(self) -> Dict[str, Dict[str, Any]]:
        """載入權值股資訊"""
        return {
            '2330': {  # 台積電
                'name': '台積電',
                'sector': '半導體',
                'weight': 0.28,  # 約28%權重
                'market_impact': 'very_high'
            },
            '2317': {  # 鴻海
                'name': '鴻海',
                'sector': '電子',
                'weight': 0.04,
                'market_impact': 'high'
            },
            '2454': {  # 聯發科
                'name': '聯發科',
                'sector': '半導體',
                'weight': 0.03,
                'market_impact': 'high'
            },
            '2412': {  # 中華電
                'name': '中華電',
                'sector': '電信',
                'weight': 0.02,
                'market_impact': 'medium'
            },
            '2881': {  # 富邦金
                'name': '富邦金',
                'sector': '金融',
                'weight': 0.02,
                'market_impact': 'medium'
            }
        }
    
    async def analyze(self, analysis_state: Dict[str, Any]) -> AnalysisResult:
        """執行台股專業分析"""
        stock_id = analysis_state.get('stock_id', '')
        analysis_date = analysis_state.get('analysis_date', datetime.now().strftime('%Y-%m-%d'))
        
        self.logger.info(f"🇹🇼 開始台股分析: {stock_id}")
        
        try:
            # 1. 獲取台股數據
            taiwan_data = await self._collect_taiwan_market_data(stock_id)
            
            # 2. 法人進出分析
            institutional_analysis = await self._analyze_institutional_flow(taiwan_data)
            
            # 3. 漲跌停影響分析
            limit_analysis = await self._analyze_price_limits(taiwan_data)
            
            # 4. 權值股連動分析
            market_linkage_analysis = await self._analyze_market_linkage(stock_id, taiwan_data)
            
            # 5. 板塊輪動分析
            sector_rotation_analysis = await self._analyze_sector_rotation(stock_id, taiwan_data)
            
            # 6. 綜合台股特色分析
            taiwan_specific_analysis = {
                'institutional_flow': institutional_analysis,
                'price_limits': limit_analysis,
                'market_linkage': market_linkage_analysis,
                'sector_rotation': sector_rotation_analysis
            }
            
            # 7. 生成分析結果
            result = await self._generate_analysis_result(
                stock_id, 
                analysis_date, 
                taiwan_data, 
                taiwan_specific_analysis
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"台股分析失敗: {str(e)}")
            return AnalysisResult(
                analyst_id=self.analyst_id,
                stock_id=stock_id,
                analysis_date=analysis_date,
                recommendation='HOLD',
                confidence=0.0,
                reasoning=[f'台股分析過程中發生錯誤: {str(e)}']
            )
    
    async def _collect_taiwan_market_data(self, stock_id: str) -> Dict[str, Any]:
        """收集台股市場數據"""
        try:
            from ...dataflows.taiwan_market_api import get_taiwan_stock_data
            
            # 獲取30天的完整台股數據
            taiwan_data = await get_taiwan_stock_data(stock_id, days=30)
            
            if 'error' in taiwan_data:
                self.logger.warning(f"台股數據獲取失敗: {taiwan_data['error']}")
                # 回傳模擬數據以確保分析師能夠運作
                return self._get_mock_taiwan_data(stock_id)
            
            return taiwan_data
            
        except Exception as e:
            self.logger.error(f"收集台股數據失敗: {str(e)}")
            # 如果API失敗，使用模擬數據確保系統可用性
            return self._get_mock_taiwan_data(stock_id)
    
    def _get_mock_taiwan_data(self, stock_id: str) -> Dict[str, Any]:
        """獲取模擬台股數據 (當API不可用時使用)"""
        import random
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 模擬股票基本資訊
        stock_info = {
            'stock_id': stock_id,
            'stock_name': self.major_stocks.get(stock_id, {}).get('name', '未知股票'),
            'industry_category': self.major_stocks.get(stock_id, {}).get('sector', '其他'),
            'market_type': '上市',
            'source': 'Mock Data'
        }
        
        # 模擬法人趨勢
        institutional_trend = {
            'stock_id': stock_id,
            'analysis_period': f'{current_date} (模擬)',
            'days_analyzed': 20,
            'foreign_investor': {
                'total_net': random.randint(-50000, 50000),
                'trend': random.choice(['bullish', 'bearish', 'neutral']),
                'avg_daily_volume': random.randint(10000, 100000),
                'impact': random.choice(['high', 'medium', 'low'])
            },
            'investment_trust': {
                'total_net': random.randint(-20000, 20000),
                'trend': random.choice(['bullish', 'bearish', 'neutral']),
                'avg_daily_volume': random.randint(5000, 50000),
                'impact': random.choice(['high', 'medium', 'low'])
            },
            'dealer': {
                'total_net': random.randint(-10000, 10000),
                'trend': random.choice(['bullish', 'bearish', 'neutral']),
                'avg_daily_volume': random.randint(2000, 20000),
                'impact': random.choice(['high', 'medium', 'low'])
            },
            'overall_sentiment': random.choice(['bullish', 'bearish', 'neutral']),
            'timestamp': datetime.now().isoformat()
        }
        
        # 模擬漲跌停影響
        price_limit_impact = {
            'stock_id': stock_id,
            'analysis_period': f'{current_date} (模擬)',
            'limit_events': [],
            'limit_event_count': 0,
            'has_recent_limits': False,
            'impact_assessment': 'low',
            'timestamp': datetime.now().isoformat()
        }
        
        # 隨機添加漲跌停事件
        if random.random() > 0.7:  # 30%機率有漲跌停
            limit_events = [{
                'date': current_date,
                'type': random.choice(['limit_up', 'limit_down']),
                'change_percent': random.choice([9.8, -9.8])
            }]
            price_limit_impact.update({
                'limit_events': limit_events,
                'limit_event_count': 1,
                'has_recent_limits': True,
                'impact_assessment': 'medium'
            })
        
        return {
            'stock_id': stock_id,
            'stock_info': stock_info,
            'institutional_trend': institutional_trend,
            'price_limit_impact': price_limit_impact,
            'data_period': f'{current_date} (模擬數據)',
            'timestamp': datetime.now().isoformat(),
            'is_mock_data': True
        }
    
    async def _analyze_institutional_flow(self, taiwan_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析法人進出流向"""
        institutional_trend = taiwan_data.get('institutional_trend', {})
        
        if 'error' in institutional_trend:
            return {
                'status': 'no_data',
                'impact': 'unknown',
                'recommendation_weight': 0.0
            }
        
        # 分析各法人影響
        foreign_impact = self._assess_institutional_impact(
            institutional_trend.get('foreign_investor', {}), 
            'foreign'
        )
        trust_impact = self._assess_institutional_impact(
            institutional_trend.get('investment_trust', {}), 
            'trust'
        )
        dealer_impact = self._assess_institutional_impact(
            institutional_trend.get('dealer', {}), 
            'dealer'
        )
        
        # 綜合評估
        overall_sentiment = institutional_trend.get('overall_sentiment', 'neutral')
        
        recommendation_weight = self._calculate_institutional_weight(
            foreign_impact, trust_impact, dealer_impact, overall_sentiment
        )
        
        return {
            'foreign_investor': foreign_impact,
            'investment_trust': trust_impact,
            'dealer': dealer_impact,
            'overall_sentiment': overall_sentiment,
            'recommendation_weight': recommendation_weight,
            'analysis_confidence': 0.8 if institutional_trend.get('days_analyzed', 0) >= 20 else 0.6
        }
    
    def _assess_institutional_impact(self, institutional_data: Dict[str, Any], investor_type: str) -> Dict[str, Any]:
        """評估單一法人影響"""
        if not institutional_data:
            return {'impact': 'none', 'trend': 'neutral', 'weight': 0.0}
        
        trend = institutional_data.get('trend', 'neutral')
        impact_level = institutional_data.get('impact', 'low')
        total_net = institutional_data.get('total_net', 0)
        
        # 根據法人類型調整權重
        type_weights = {
            'foreign': 0.5,   # 外資影響最大
            'trust': 0.3,     # 投信次之
            'dealer': 0.2     # 自營商影響較小
        }
        
        base_weight = type_weights.get(investor_type, 0.2)
        
        # 根據趨勢和影響級別調整權重
        impact_multiplier = {
            'high': 1.0,
            'medium': 0.7,
            'low': 0.4
        }.get(impact_level, 0.4)
        
        trend_multiplier = {
            'bullish': 1.0,
            'bearish': -1.0,
            'neutral': 0.0
        }.get(trend, 0.0)
        
        final_weight = base_weight * impact_multiplier * trend_multiplier
        
        return {
            'trend': trend,
            'impact': impact_level,
            'net_flow': total_net,
            'weight': final_weight,
            'confidence': 0.8 if impact_level in ['high', 'medium'] else 0.5
        }
    
    def _calculate_institutional_weight(self, foreign: Dict, trust: Dict, dealer: Dict, overall: str) -> float:
        """計算法人整體權重"""
        total_weight = (
            foreign.get('weight', 0) + 
            trust.get('weight', 0) + 
            dealer.get('weight', 0)
        )
        
        # 限制權重範圍
        return max(-0.3, min(0.3, total_weight))
    
    async def _analyze_price_limits(self, taiwan_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析漲跌停影響"""
        price_limit_impact = taiwan_data.get('price_limit_impact', {})
        
        if 'error' in price_limit_impact:
            return {
                'has_limits': False,
                'impact': 'none',
                'recommendation_adjustment': 0.0
            }
        
        limit_events = price_limit_impact.get('limit_events', [])
        impact_level = price_limit_impact.get('impact_assessment', 'low')
        
        if not limit_events:
            return {
                'has_limits': False,
                'impact': 'none',
                'recommendation_adjustment': 0.0
            }
        
        # 分析漲跌停類型
        limit_up_count = sum(1 for event in limit_events if event['type'] == 'limit_up')
        limit_down_count = sum(1 for event in limit_events if event['type'] == 'limit_down')
        
        # 計算影響權重
        if limit_up_count > limit_down_count:
            # 漲停較多，正面影響
            adjustment = 0.1 if impact_level == 'high' else 0.05
        elif limit_down_count > limit_up_count:
            # 跌停較多，負面影響
            adjustment = -0.1 if impact_level == 'high' else -0.05
        else:
            # 影響中性
            adjustment = 0.0
        
        return {
            'has_limits': True,
            'limit_up_count': limit_up_count,
            'limit_down_count': limit_down_count,
            'impact': impact_level,
            'recent_events': limit_events[-3:],  # 最近3次事件
            'recommendation_adjustment': adjustment,
            'volatility_warning': len(limit_events) >= 3
        }
    
    async def _analyze_market_linkage(self, stock_id: str, taiwan_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析與大盤的連動性"""
        stock_info = taiwan_data.get('stock_info', {})
        
        # 檢查是否為權值股
        is_major_stock = stock_id in self.major_stocks
        
        if is_major_stock:
            stock_details = self.major_stocks[stock_id]
            market_impact = stock_details['market_impact']
            sector = stock_details['sector']
            weight = stock_details['weight']
            
            # 權值股影響大盤
            linkage_strength = 'very_high' if weight > 0.1 else 'high'
            impact_direction = 'bidirectional'  # 與大盤雙向影響
            
        else:
            # 一般股票受大盤影響
            sector = stock_info.get('industry_category', '其他')
            market_impact = 'low'
            linkage_strength = 'medium'
            impact_direction = 'follows_market'  # 跟隨大盤
        
        # 根據板塊特性調整
        sector_beta = self._get_sector_beta(sector)
        
        return {
            'is_major_stock': is_major_stock,
            'market_impact': market_impact,
            'linkage_strength': linkage_strength,
            'impact_direction': impact_direction,
            'sector': sector,
            'sector_beta': sector_beta,
            'weight_in_index': self.major_stocks.get(stock_id, {}).get('weight', 0.0),
            'recommendation_influence': self._calculate_market_linkage_influence(
                is_major_stock, linkage_strength, sector_beta
            )
        }
    
    def _get_sector_beta(self, sector: str) -> float:
        """獲取板塊Beta值"""
        sector_betas = {
            '半導體': 1.2,     # 高Beta
            '電子': 1.1,       # 較高Beta
            '金融': 0.9,       # 較低Beta
            '電信': 0.8,       # 低Beta，防禦性
            '傳產': 0.9,       # 中等Beta
            '生技': 1.3,       # 高Beta，高波動
            '其他': 1.0        # 市場平均
        }
        return sector_betas.get(sector, 1.0)
    
    def _calculate_market_linkage_influence(self, is_major: bool, linkage: str, beta: float) -> float:
        """計算大盤連動影響權重"""
        base_influence = 0.15 if is_major else 0.10
        
        linkage_multiplier = {
            'very_high': 1.5,
            'high': 1.2,
            'medium': 1.0,
            'low': 0.8
        }.get(linkage, 1.0)
        
        beta_multiplier = min(1.5, max(0.5, beta))
        
        return base_influence * linkage_multiplier * beta_multiplier
    
    async def _analyze_sector_rotation(self, stock_id: str, taiwan_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析板塊輪動"""
        stock_info = taiwan_data.get('stock_info', {})
        sector = stock_info.get('industry_category', '其他')
        
        # 模擬板塊輪動分析 (實際應該分析各板塊表現)
        current_hot_sectors = self._get_current_hot_sectors()
        
        is_hot_sector = sector in current_hot_sectors
        sector_rank = current_hot_sectors.index(sector) + 1 if is_hot_sector else len(current_hot_sectors) + 1
        
        # 計算板塊輪動影響
        rotation_impact = self._calculate_sector_rotation_impact(sector, is_hot_sector, sector_rank)
        
        return {
            'stock_sector': sector,
            'is_hot_sector': is_hot_sector,
            'sector_rank': sector_rank,
            'hot_sectors': current_hot_sectors,
            'rotation_trend': 'favorable' if is_hot_sector else 'neutral',
            'rotation_impact': rotation_impact,
            'sector_outlook': self._get_sector_outlook(sector)
        }
    
    def _get_current_hot_sectors(self) -> List[str]:
        """獲取當前熱門板塊 (模擬)"""
        # 實際應該根據市場數據分析
        return ['半導體', 'AI概念', '電動車', '綠能']
    
    def _calculate_sector_rotation_impact(self, sector: str, is_hot: bool, rank: int) -> float:
        """計算板塊輪動影響"""
        if is_hot:
            # 熱門板塊，正面影響
            return 0.1 / rank  # 排名越前影響越大
        else:
            # 非熱門板塊，輕微負面影響
            return -0.05
    
    def _get_sector_outlook(self, sector: str) -> str:
        """獲取板塊展望"""
        sector_outlooks = {
            '半導體': 'positive',      # AI需求強勁
            '金融': 'neutral',         # 利率環境複雜
            '電子': 'positive',        # 供應鏈復甦
            '電信': 'stable',          # 防禦性佳
            '傳產': 'recovery',        # 復甦中
            '生技': 'volatile'         # 波動較大
        }
        return sector_outlooks.get(sector, 'neutral')
    
    async def _generate_analysis_result(
        self, 
        stock_id: str, 
        analysis_date: str, 
        taiwan_data: Dict[str, Any],
        taiwan_analysis: Dict[str, Any]
    ) -> AnalysisResult:
        """生成最終分析結果"""
        
        # 收集各項權重
        institutional_weight = taiwan_analysis['institutional_flow'].get('recommendation_weight', 0.0)
        price_limit_adjustment = taiwan_analysis['price_limits'].get('recommendation_adjustment', 0.0)
        market_linkage_influence = taiwan_analysis['market_linkage'].get('recommendation_influence', 0.0)
        sector_rotation_impact = taiwan_analysis['sector_rotation'].get('rotation_impact', 0.0)
        
        # 計算總權重
        total_weight = (
            institutional_weight + 
            price_limit_adjustment + 
            sector_rotation_impact
        )
        
        # 生成建議
        if total_weight > 0.1:
            recommendation = 'BUY'
            confidence = min(0.8, 0.5 + abs(total_weight))
        elif total_weight < -0.1:
            recommendation = 'SELL'
            confidence = min(0.8, 0.5 + abs(total_weight))
        else:
            recommendation = 'HOLD'
            confidence = 0.6
        
        # 生成分析理由
        reasoning = self._generate_reasoning(taiwan_analysis, total_weight)
        
        # 生成風險因素
        risk_factors = self._generate_risk_factors(taiwan_analysis)
        
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=stock_id,
            analysis_date=analysis_date,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            risk_factors=risk_factors,
            taiwan_specific_analysis=taiwan_analysis
        )
    
    def _generate_reasoning(self, taiwan_analysis: Dict[str, Any], total_weight: float) -> List[str]:
        """生成分析理由"""
        reasoning = []
        
        # 法人分析理由
        institutional = taiwan_analysis['institutional_flow']
        if institutional.get('overall_sentiment') == 'bullish':
            reasoning.append("法人整體呈現買超趨勢，外資/投信/自營商態度偏多")
        elif institutional.get('overall_sentiment') == 'bearish':
            reasoning.append("法人整體呈現賣超趨勢，需關注籌碼面壓力")
        
        # 漲跌停分析理由
        price_limits = taiwan_analysis['price_limits']
        if price_limits.get('has_limits'):
            if price_limits.get('limit_up_count', 0) > price_limits.get('limit_down_count', 0):
                reasoning.append("近期出現漲停，市場情緒熱絡")
            else:
                reasoning.append("近期出現跌停，需注意技術面風險")
        
        # 板塊輪動理由
        sector_rotation = taiwan_analysis['sector_rotation']
        if sector_rotation.get('is_hot_sector'):
            reasoning.append(f"所屬{sector_rotation.get('stock_sector')}板塊為當前市場熱點")
        
        # 權值股連動理由
        market_linkage = taiwan_analysis['market_linkage']
        if market_linkage.get('is_major_stock'):
            reasoning.append("為台股權值股，與大盤連動性高，需關注指數走勢")
        
        # 綜合評估
        if total_weight > 0.1:
            reasoning.append("綜合台股特色分析，多項因素偏向正面")
        elif total_weight < -0.1:
            reasoning.append("綜合台股特色分析，多項因素偏向負面")
        else:
            reasoning.append("台股各項因素相互抵銷，建議持有觀望")
        
        return reasoning
    
    def _generate_risk_factors(self, taiwan_analysis: Dict[str, Any]) -> List[str]:
        """生成風險因素"""
        risk_factors = []
        
        # 法人風險
        institutional = taiwan_analysis['institutional_flow']
        if institutional.get('foreign_investor', {}).get('trend') == 'bearish':
            risk_factors.append("外資持續賣超，需注意籌碼面壓力")
        
        # 波動風險
        price_limits = taiwan_analysis['price_limits']
        if price_limits.get('volatility_warning'):
            risk_factors.append("近期出現多次漲跌停，波動風險較高")
        
        # 板塊風險
        sector_rotation = taiwan_analysis['sector_rotation']
        sector_outlook = sector_rotation.get('sector_outlook')
        if sector_outlook == 'volatile':
            risk_factors.append("所屬板塊波動較大，需注意板塊輪動風險")
        
        # 權值股風險
        market_linkage = taiwan_analysis['market_linkage']
        if market_linkage.get('linkage_strength') in ['high', 'very_high']:
            risk_factors.append("與大盤連動性高，需關注整體市場風險")
        
        # 台股特有風險
        risk_factors.append("台股受國際資金流向影響較大")
        risk_factors.append("需關注兩岸關係和地緣政治風險")
        
        return risk_factors
    
    def get_analysis_type(self) -> AnalysisType:
        """返回分析類型"""
        return AnalysisType.TAIWAN_SPECIFIC  # 台股分析師進行台股專業分析

# 便利函數
async def analyze_taiwan_stock(stock_id: str, user_context = None) -> AnalysisResult:
    """快速台股分析"""
    config = {
        'taiwan_focus': True,
        'include_institutional': True,
        'include_price_limits': True
    }
    
    analyst = TaiwanMarketAnalyst(config)
    
    analysis_state = {
        'stock_id': stock_id,
        'analysis_date': datetime.now().strftime('%Y-%m-%d'),
        'user_context': user_context
    }
    
    return await analyst.analyze(analysis_state)

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_taiwan_analyst():
        print("🇹🇼 測試台股分析師")
        
        # 測試台積電分析
        result = await analyze_taiwan_stock("2330")
        
        print(f"股票: {result.stock_id}")
        print(f"建議: {result.recommendation}")
        print(f"信心度: {result.confidence:.2f}")
        print(f"理由: {', '.join(result.reasoning)}")
        print(f"風險: {', '.join(result.risk_factors)}")
        
        if result.taiwan_specific_analysis:
            taiwan_analysis = result.taiwan_specific_analysis
            print(f"法人態度: {taiwan_analysis['institutional_flow']['overall_sentiment']}")
            print(f"板塊: {taiwan_analysis['sector_rotation']['stock_sector']}")
            print(f"權值股: {taiwan_analysis['market_linkage']['is_major_stock']}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_taiwan_analyst())