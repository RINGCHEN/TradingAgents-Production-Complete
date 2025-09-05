#!/usr/bin/env python3
"""
TradingAgents 國際市場差異化功能服務
提供台股與美股同業配對、全球市場相關性分析、跨時區追蹤等功能
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import math
import statistics
from collections import defaultdict

from ..utils.user_context import UserContext
from ..default_config import DEFAULT_CONFIG

# 設置日誌
logger = logging.getLogger(__name__)

class MarketRegion(Enum):
    """市場區域"""
    TAIWAN = "taiwan"
    US = "us"
    HONG_KONG = "hong_kong"
    JAPAN = "japan"
    EUROPE = "europe"
    GLOBAL = "global"

class IndustryCategory(Enum):
    """行業分類"""
    TECHNOLOGY = "technology"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    ENERGY = "energy"
    MATERIALS = "materials"
    UTILITIES = "utilities"
    REAL_ESTATE = "real_estate"
    TELECOMMUNICATIONS = "telecommunications"

class CorrelationType(Enum):
    """相關性類型"""
    PRICE = "price"
    VOLUME = "volume"
    VOLATILITY = "volatility"
    SECTOR = "sector"
    MACRO = "macro"

@dataclass
class CompanyProfile:
    """公司基本資料"""
    symbol: str
    name: str
    market: MarketRegion
    industry: IndustryCategory
    market_cap: float
    revenue: float
    employees: int
    description: str
    business_segments: List[str] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'name': self.name,
            'market': self.market.value,
            'industry': self.industry.value,
            'market_cap': self.market_cap,
            'revenue': self.revenue,
            'employees': self.employees,
            'description': self.description,
            'business_segments': self.business_segments,
            'competitors': self.competitors
        }

@dataclass
class PeerComparison:
    """同業比較"""
    taiwan_company: CompanyProfile
    international_peers: List[CompanyProfile]
    similarity_score: float
    comparison_metrics: Dict[str, Any]
    analysis_summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'taiwan_company': self.taiwan_company.to_dict(),
            'international_peers': [peer.to_dict() for peer in self.international_peers],
            'similarity_score': self.similarity_score,
            'comparison_metrics': self.comparison_metrics,
            'analysis_summary': self.analysis_summary
        }

@dataclass
class MarketCorrelation:
    """市場相關性"""
    symbol1: str
    symbol2: str
    correlation_type: CorrelationType
    correlation_coefficient: float
    p_value: float
    time_period: str
    confidence_level: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol1': self.symbol1,
            'symbol2': self.symbol2,
            'correlation_type': self.correlation_type.value,
            'correlation_coefficient': self.correlation_coefficient,
            'p_value': self.p_value,
            'time_period': self.time_period,
            'confidence_level': self.confidence_level
        }

@dataclass
class RiskDiversificationAdvice:
    """風險分散建議"""
    portfolio_symbols: List[str]
    risk_level: str
    diversification_score: float
    recommendations: List[Dict[str, Any]]
    geographic_allocation: Dict[str, float]
    sector_allocation: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'portfolio_symbols': self.portfolio_symbols,
            'risk_level': self.risk_level,
            'diversification_score': self.diversification_score,
            'recommendations': self.recommendations,
            'geographic_allocation': self.geographic_allocation,
            'sector_allocation': self.sector_allocation
        }

@dataclass
class CrossTimezoneAlert:
    """跨時區預警"""
    alert_id: str
    symbol: str
    market: MarketRegion
    alert_type: str
    message: str
    severity: str
    created_at: datetime
    expires_at: datetime
    related_events: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'symbol': self.symbol,
            'market': self.market.value,
            'alert_type': self.alert_type,
            'message': self.message,
            'severity': self.severity,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'related_events': self.related_events
        }

class InternationalMarketService:
    """國際市場差異化功能服務"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化服務"""
        self.config = config or DEFAULT_CONFIG
        
        # 公司資料庫（實際應該從數據庫或API獲取）
        self.company_database = self._initialize_company_database()
        
        # 行業映射表
        self.industry_mapping = self._initialize_industry_mapping()
        
        # 市場相關性緩存
        self.correlation_cache = {}
        
        # 跨時區預警
        self.active_alerts = []
        
        logger.info("國際市場差異化功能服務初始化完成")
    
    def _initialize_company_database(self) -> Dict[str, CompanyProfile]:
        """初始化公司資料庫"""
        companies = {
            # 台股科技公司
            "2330": CompanyProfile(
                symbol="2330",
                name="台積電",
                market=MarketRegion.TAIWAN,
                industry=IndustryCategory.TECHNOLOGY,
                market_cap=500000000000,  # 5000億美元
                revenue=70000000000,      # 700億美元
                employees=73000,
                description="全球最大的晶圓代工廠",
                business_segments=["晶圓代工", "封裝測試", "太陽能"],
                competitors=["INTC", "NVDA", "AMD"]
            ),
            "2317": CompanyProfile(
                symbol="2317",
                name="鴻海",
                market=MarketRegion.TAIWAN,
                industry=IndustryCategory.TECHNOLOGY,
                market_cap=50000000000,   # 500億美元
                revenue=200000000000,     # 2000億美元
                employees=1300000,
                description="全球最大的電子製造服務商",
                business_segments=["電子製造", "雲端網路", "電動車"],
                competitors=["AAPL", "AMZN", "TSLA"]
            ),
            
            # 美股科技公司
            "AAPL": CompanyProfile(
                symbol="AAPL",
                name="Apple Inc.",
                market=MarketRegion.US,
                industry=IndustryCategory.TECHNOLOGY,
                market_cap=3000000000000,  # 3兆美元
                revenue=380000000000,      # 3800億美元
                employees=164000,
                description="全球領先的消費電子和軟體公司",
                business_segments=["iPhone", "Mac", "iPad", "Services"],
                competitors=["GOOGL", "MSFT", "AMZN"]
            ),
            "TSLA": CompanyProfile(
                symbol="TSLA",
                name="Tesla Inc.",
                market=MarketRegion.US,
                industry=IndustryCategory.TECHNOLOGY,
                market_cap=800000000000,   # 8000億美元
                revenue=96000000000,       # 960億美元
                employees=140000,
                description="電動車和清潔能源公司",
                business_segments=["電動車", "能源存儲", "太陽能"],
                competitors=["F", "GM", "NIO"]
            ),
            "NVDA": CompanyProfile(
                symbol="NVDA",
                name="NVIDIA Corporation",
                market=MarketRegion.US,
                industry=IndustryCategory.TECHNOLOGY,
                market_cap=1800000000000,  # 1.8兆美元
                revenue=60000000000,       # 600億美元
                employees=29600,
                description="GPU和AI晶片領導廠商",
                business_segments=["GPU", "AI晶片", "自動駕駛", "數據中心"],
                competitors=["AMD", "INTC", "QCOM"]
            )
        }
        
        return companies
    
    def _initialize_industry_mapping(self) -> Dict[str, List[str]]:
        """初始化行業映射表"""
        return {
            IndustryCategory.TECHNOLOGY.value: [
                "半導體", "軟體", "硬體", "電子製造", "通訊設備",
                "semiconductor", "software", "hardware", "electronics", "telecom"
            ],
            IndustryCategory.FINANCE.value: [
                "銀行", "保險", "證券", "金融服務",
                "banking", "insurance", "securities", "financial services"
            ],
            IndustryCategory.HEALTHCARE.value: [
                "製藥", "醫療器材", "生技", "醫療服務",
                "pharmaceutical", "medical devices", "biotechnology", "healthcare"
            ]
        }
    
    async def find_international_peers(self, taiwan_symbol: str, limit: int = 5) -> Optional[PeerComparison]:
        """
        尋找台股的國際同業公司
        
        Args:
            taiwan_symbol: 台股代號
            limit: 返回的同業公司數量限制
            
        Returns:
            同業比較結果
        """
        taiwan_company = self.company_database.get(taiwan_symbol)
        if not taiwan_company or taiwan_company.market != MarketRegion.TAIWAN:
            return None
        
        # 尋找同行業的國際公司
        international_peers = []
        for symbol, company in self.company_database.items():
            if (company.market != MarketRegion.TAIWAN and 
                company.industry == taiwan_company.industry):
                
                # 計算相似度分數
                similarity = self._calculate_company_similarity(taiwan_company, company)
                international_peers.append((company, similarity))
        
        # 按相似度排序並取前N個
        international_peers.sort(key=lambda x: x[1], reverse=True)
        top_peers = [peer[0] for peer in international_peers[:limit]]
        
        if not top_peers:
            return None
        
        # 生成比較指標
        comparison_metrics = self._generate_comparison_metrics(taiwan_company, top_peers)
        
        # 生成分析摘要
        analysis_summary = self._generate_peer_analysis_summary(taiwan_company, top_peers, comparison_metrics)
        
        return PeerComparison(
            taiwan_company=taiwan_company,
            international_peers=top_peers,
            similarity_score=international_peers[0][1] if international_peers else 0,
            comparison_metrics=comparison_metrics,
            analysis_summary=analysis_summary
        )
    
    def _calculate_company_similarity(self, company1: CompanyProfile, company2: CompanyProfile) -> float:
        """計算公司相似度"""
        score = 0.0
        
        # 行業相同 (40%)
        if company1.industry == company2.industry:
            score += 0.4
        
        # 市值相似度 (30%)
        if company1.market_cap > 0 and company2.market_cap > 0:
            ratio = min(company1.market_cap, company2.market_cap) / max(company1.market_cap, company2.market_cap)
            score += 0.3 * ratio
        
        # 營收相似度 (20%)
        if company1.revenue > 0 and company2.revenue > 0:
            ratio = min(company1.revenue, company2.revenue) / max(company1.revenue, company2.revenue)
            score += 0.2 * ratio
        
        # 業務重疊度 (10%)
        if company1.business_segments and company2.business_segments:
            overlap = len(set(company1.business_segments) & set(company2.business_segments))
            total = len(set(company1.business_segments) | set(company2.business_segments))
            if total > 0:
                score += 0.1 * (overlap / total)
        
        return min(score, 1.0)
    
    def _generate_comparison_metrics(self, taiwan_company: CompanyProfile, peers: List[CompanyProfile]) -> Dict[str, Any]:
        """生成比較指標"""
        peer_market_caps = [peer.market_cap for peer in peers if peer.market_cap > 0]
        peer_revenues = [peer.revenue for peer in peers if peer.revenue > 0]
        peer_employees = [peer.employees for peer in peers if peer.employees > 0]
        
        metrics = {
            'market_cap_comparison': {
                'taiwan_company': taiwan_company.market_cap,
                'peer_average': statistics.mean(peer_market_caps) if peer_market_caps else 0,
                'peer_median': statistics.median(peer_market_caps) if peer_market_caps else 0,
                'taiwan_rank': self._calculate_rank(taiwan_company.market_cap, peer_market_caps)
            },
            'revenue_comparison': {
                'taiwan_company': taiwan_company.revenue,
                'peer_average': statistics.mean(peer_revenues) if peer_revenues else 0,
                'peer_median': statistics.median(peer_revenues) if peer_revenues else 0,
                'taiwan_rank': self._calculate_rank(taiwan_company.revenue, peer_revenues)
            },
            'employee_comparison': {
                'taiwan_company': taiwan_company.employees,
                'peer_average': statistics.mean(peer_employees) if peer_employees else 0,
                'peer_median': statistics.median(peer_employees) if peer_employees else 0,
                'taiwan_rank': self._calculate_rank(taiwan_company.employees, peer_employees)
            },
            'geographic_presence': {
                'taiwan_focused': True,
                'international_peers_markets': list(set(peer.market.value for peer in peers))
            }
        }
        
        return metrics
    
    def _calculate_rank(self, value: float, peer_values: List[float]) -> int:
        """計算排名"""
        if not peer_values:
            return 1
        
        all_values = peer_values + [value]
        all_values.sort(reverse=True)
        return all_values.index(value) + 1
    
    def _generate_peer_analysis_summary(self, taiwan_company: CompanyProfile, peers: List[CompanyProfile], metrics: Dict[str, Any]) -> str:
        """生成同業分析摘要"""
        summary_parts = []
        
        # 基本比較
        summary_parts.append(f"{taiwan_company.name} 在 {taiwan_company.industry.value} 行業中")
        
        # 市值比較
        market_cap_rank = metrics['market_cap_comparison']['taiwan_rank']
        total_companies = len(peers) + 1
        if market_cap_rank <= total_companies // 3:
            summary_parts.append("市值規模位居前列")
        elif market_cap_rank <= 2 * total_companies // 3:
            summary_parts.append("市值規模處於中等水平")
        else:
            summary_parts.append("市值規模相對較小")
        
        # 營收比較
        revenue_rank = metrics['revenue_comparison']['taiwan_rank']
        if revenue_rank <= total_companies // 3:
            summary_parts.append("營收表現優異")
        elif revenue_rank <= 2 * total_companies // 3:
            summary_parts.append("營收表現中等")
        else:
            summary_parts.append("營收有提升空間")
        
        # 國際化程度
        international_markets = metrics['geographic_presence']['international_peers_markets']
        summary_parts.append(f"與來自 {', '.join(international_markets)} 市場的同業公司相比")
        
        # 投資建議
        if market_cap_rank <= 2 and revenue_rank <= 2:
            summary_parts.append("具有行業領導地位，適合長期投資")
        elif market_cap_rank <= total_companies // 2:
            summary_parts.append("具有成長潛力，值得關注")
        else:
            summary_parts.append("可能存在估值優勢，適合價值投資")
        
        return "，".join(summary_parts) + "。"
    
    async def analyze_market_correlation(self, symbols: List[str], correlation_type: CorrelationType = CorrelationType.PRICE, time_period: str = "1Y") -> List[MarketCorrelation]:
        """
        分析市場相關性
        
        Args:
            symbols: 股票代號列表
            correlation_type: 相關性類型
            time_period: 時間週期
            
        Returns:
            相關性分析結果
        """
        correlations = []
        
        # 模擬相關性計算（實際應該使用真實的價格數據）
        for i in range(len(symbols)):
            for j in range(i + 1, len(symbols)):
                symbol1, symbol2 = symbols[i], symbols[j]
                
                # 模擬相關性係數計算
                correlation_coeff = self._simulate_correlation_calculation(symbol1, symbol2, correlation_type)
                
                correlation = MarketCorrelation(
                    symbol1=symbol1,
                    symbol2=symbol2,
                    correlation_type=correlation_type,
                    correlation_coefficient=correlation_coeff,
                    p_value=0.05,  # 模擬p值
                    time_period=time_period,
                    confidence_level=0.95
                )
                
                correlations.append(correlation)
        
        return correlations
    
    def _simulate_correlation_calculation(self, symbol1: str, symbol2: str, correlation_type: CorrelationType) -> float:
        """模擬相關性計算"""
        # 基於公司特性模擬相關性
        company1 = self.company_database.get(symbol1)
        company2 = self.company_database.get(symbol2)
        
        if not company1 or not company2:
            return 0.0
        
        # 同行業相關性較高
        if company1.industry == company2.industry:
            base_correlation = 0.6
        else:
            base_correlation = 0.2
        
        # 同市場相關性較高
        if company1.market == company2.market:
            base_correlation += 0.2
        
        # 添加隨機波動
        import random
        random.seed(hash(symbol1 + symbol2))  # 確保結果一致
        noise = (random.random() - 0.5) * 0.4
        
        return max(-1.0, min(1.0, base_correlation + noise))
    
    async def generate_risk_diversification_advice(self, portfolio_symbols: List[str], target_risk_level: str = "moderate") -> RiskDiversificationAdvice:
        """
        生成風險分散建議
        
        Args:
            portfolio_symbols: 投資組合股票代號
            target_risk_level: 目標風險水平 (conservative, moderate, aggressive)
            
        Returns:
            風險分散建議
        """
        # 分析當前投資組合
        portfolio_analysis = self._analyze_portfolio_composition(portfolio_symbols)
        
        # 計算分散化分數
        diversification_score = self._calculate_diversification_score(portfolio_analysis)
        
        # 生成建議
        recommendations = self._generate_diversification_recommendations(
            portfolio_analysis, target_risk_level, diversification_score
        )
        
        return RiskDiversificationAdvice(
            portfolio_symbols=portfolio_symbols,
            risk_level=target_risk_level,
            diversification_score=diversification_score,
            recommendations=recommendations,
            geographic_allocation=portfolio_analysis['geographic_allocation'],
            sector_allocation=portfolio_analysis['sector_allocation']
        )
    
    def _analyze_portfolio_composition(self, symbols: List[str]) -> Dict[str, Any]:
        """分析投資組合組成"""
        geographic_count = defaultdict(int)
        sector_count = defaultdict(int)
        total_market_cap = 0
        
        for symbol in symbols:
            company = self.company_database.get(symbol)
            if company:
                geographic_count[company.market.value] += 1
                sector_count[company.industry.value] += 1
                total_market_cap += company.market_cap
        
        total_companies = len(symbols)
        
        # 計算分配比例
        geographic_allocation = {
            region: count / total_companies * 100 
            for region, count in geographic_count.items()
        }
        
        sector_allocation = {
            sector: count / total_companies * 100 
            for sector, count in sector_count.items()
        }
        
        return {
            'total_companies': total_companies,
            'geographic_allocation': geographic_allocation,
            'sector_allocation': sector_allocation,
            'total_market_cap': total_market_cap,
            'geographic_diversity': len(geographic_count),
            'sector_diversity': len(sector_count)
        }
    
    def _calculate_diversification_score(self, portfolio_analysis: Dict[str, Any]) -> float:
        """計算分散化分數 (0-100)"""
        score = 0.0
        
        # 地理分散性 (40%)
        geo_diversity = portfolio_analysis['geographic_diversity']
        max_geo_score = min(geo_diversity / 4, 1.0)  # 最多4個地區
        score += max_geo_score * 40
        
        # 行業分散性 (40%)
        sector_diversity = portfolio_analysis['sector_diversity']
        max_sector_score = min(sector_diversity / 6, 1.0)  # 最多6個行業
        score += max_sector_score * 40
        
        # 集中度風險 (20%)
        geo_allocation = portfolio_analysis['geographic_allocation']
        sector_allocation = portfolio_analysis['sector_allocation']
        
        # 計算赫芬達爾指數 (越低越分散)
        geo_hhi = sum([(pct/100)**2 for pct in geo_allocation.values()])
        sector_hhi = sum([(pct/100)**2 for pct in sector_allocation.values()])
        
        concentration_penalty = (geo_hhi + sector_hhi) * 10
        score -= concentration_penalty
        
        return max(0, min(100, score))
    
    def _generate_diversification_recommendations(self, portfolio_analysis: Dict[str, Any], target_risk_level: str, current_score: float) -> List[Dict[str, Any]]:
        """生成分散化建議"""
        recommendations = []
        
        # 地理分散建議
        geo_allocation = portfolio_analysis['geographic_allocation']
        if geo_allocation.get('taiwan', 0) > 60:
            recommendations.append({
                'type': 'geographic_diversification',
                'priority': 'high',
                'title': '增加國際市場配置',
                'description': '目前台股配置過高，建議增加美股、港股等國際市場投資',
                'suggested_allocation': {
                    'taiwan': 40,
                    'us': 35,
                    'hong_kong': 15,
                    'others': 10
                },
                'benefits': ['降低單一市場風險', '享受全球經濟成長', '匯率分散效果']
            })
        
        # 行業分散建議
        sector_allocation = portfolio_analysis['sector_allocation']
        dominant_sector = max(sector_allocation.items(), key=lambda x: x[1]) if sector_allocation else None
        
        if dominant_sector and dominant_sector[1] > 50:
            recommendations.append({
                'type': 'sector_diversification',
                'priority': 'high',
                'title': f'減少{dominant_sector[0]}行業集中度',
                'description': f'目前{dominant_sector[0]}行業配置達{dominant_sector[1]:.1f}%，建議分散至其他行業',
                'suggested_sectors': ['healthcare', 'finance', 'consumer', 'energy'],
                'benefits': ['降低行業週期風險', '平衡投資組合波動', '捕捉不同行業機會']
            })
        
        # 風險水平建議
        if target_risk_level == 'conservative' and current_score < 60:
            recommendations.append({
                'type': 'risk_reduction',
                'priority': 'medium',
                'title': '增加防禦性資產',
                'description': '建議增加公用事業、消費必需品等防禦性行業配置',
                'suggested_assets': ['utilities', 'consumer_staples', 'healthcare'],
                'benefits': ['降低投資組合波動', '提供穩定股息收入', '經濟衰退時的保護']
            })
        
        elif target_risk_level == 'aggressive' and current_score > 80:
            recommendations.append({
                'type': 'growth_focus',
                'priority': 'medium',
                'title': '集中優質成長股',
                'description': '可適度集中投資於高成長潛力的科技和新興行業',
                'suggested_focus': ['technology', 'biotechnology', 'renewable_energy'],
                'benefits': ['更高成長潛力', '把握趨勢機會', '長期超額報酬']
            })
        
        return recommendations
    
    async def create_cross_timezone_alert(self, symbol: str, alert_type: str, message: str, severity: str = "medium") -> CrossTimezoneAlert:
        """
        創建跨時區市場預警
        
        Args:
            symbol: 股票代號
            alert_type: 預警類型
            message: 預警訊息
            severity: 嚴重程度
            
        Returns:
            跨時區預警
        """
        company = self.company_database.get(symbol)
        market = company.market if company else MarketRegion.GLOBAL
        
        alert = CrossTimezoneAlert(
            alert_id=f"alert_{symbol}_{int(datetime.now().timestamp())}",
            symbol=symbol,
            market=market,
            alert_type=alert_type,
            message=message,
            severity=severity,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24),
            related_events=[]
        )
        
        self.active_alerts.append(alert)
        
        # 清理過期預警
        self._cleanup_expired_alerts()
        
        logger.info(f"創建跨時區預警: {symbol} - {alert_type}")
        
        return alert
    
    def _cleanup_expired_alerts(self):
        """清理過期預警"""
        now = datetime.now()
        self.active_alerts = [
            alert for alert in self.active_alerts 
            if alert.expires_at > now
        ]
    
    async def get_active_alerts(self, user_context: UserContext, symbols: List[str] = None) -> List[CrossTimezoneAlert]:
        """
        獲取活躍預警
        
        Args:
            user_context: 用戶上下文
            symbols: 關注的股票代號列表
            
        Returns:
            活躍預警列表
        """
        self._cleanup_expired_alerts()
        
        if symbols:
            return [
                alert for alert in self.active_alerts 
                if alert.symbol in symbols
            ]
        
        return self.active_alerts
    
    async def analyze_currency_impact(self, taiwan_symbol: str, currency_pairs: List[str] = None) -> Dict[str, Any]:
        """
        分析匯率影響
        
        Args:
            taiwan_symbol: 台股代號
            currency_pairs: 貨幣對列表
            
        Returns:
            匯率影響分析
        """
        if currency_pairs is None:
            currency_pairs = ["USD/TWD", "EUR/TWD", "JPY/TWD", "CNY/TWD"]
        
        company = self.company_database.get(taiwan_symbol)
        if not company:
            return {'error': '找不到公司資料'}
        
        # 模擬匯率影響分析
        currency_impact = {
            'company': company.to_dict(),
            'currency_exposure': {
                'USD': 0.6,  # 60% 美元曝險
                'EUR': 0.2,  # 20% 歐元曝險
                'JPY': 0.1,  # 10% 日圓曝險
                'CNY': 0.1   # 10% 人民幣曝險
            },
            'sensitivity_analysis': {
                'USD/TWD': {
                    'current_rate': 31.5,
                    'impact_per_1pct_change': 0.8,  # 美元升值1%，股價影響0.8%
                    'description': '美元為主要收入貨幣，升值有利股價'
                },
                'EUR/TWD': {
                    'current_rate': 34.2,
                    'impact_per_1pct_change': 0.3,
                    'description': '歐洲市場佔營收20%，影響中等'
                }
            },
            'hedging_recommendations': [
                {
                    'strategy': '自然避險',
                    'description': '增加海外生產基地，降低匯率風險',
                    'effectiveness': 'high'
                },
                {
                    'strategy': '金融避險',
                    'description': '使用外匯衍生品對沖主要貨幣風險',
                    'effectiveness': 'medium'
                }
            ]
        }
        
        return currency_impact
    
    async def predict_global_event_impact(self, event_type: str, taiwan_symbols: List[str]) -> Dict[str, Any]:
        """
        預測全球經濟事件對台股的影響
        
        Args:
            event_type: 事件類型 (fed_rate_change, trade_war, pandemic, etc.)
            taiwan_symbols: 台股代號列表
            
        Returns:
            影響預測分析
        """
        event_impact_models = {
            'fed_rate_change': {
                'description': '美聯儲利率變動',
                'impact_factors': {
                    'technology': -0.8,  # 科技股受負面影響較大
                    'finance': 0.3,      # 金融股受正面影響
                    'utilities': -0.2    # 公用事業受輕微負面影響
                },
                'transmission_channels': [
                    '資金成本變化',
                    '美元匯率波動',
                    '風險偏好調整',
                    '估值模型重估'
                ]
            },
            'trade_war': {
                'description': '貿易戰爭',
                'impact_factors': {
                    'technology': -1.2,  # 出口導向科技股受重創
                    'materials': -0.8,   # 原物料股受影響
                    'consumer': -0.4     # 內需股相對抗跌
                },
                'transmission_channels': [
                    '出口訂單減少',
                    '供應鏈重組',
                    '關稅成本上升',
                    '投資信心下降'
                ]
            }
        }
        
        model = event_impact_models.get(event_type, {})
        if not model:
            return {'error': f'不支援的事件類型: {event_type}'}
        
        # 分析各股票的預期影響
        stock_impacts = []
        for symbol in taiwan_symbols:
            company = self.company_database.get(symbol)
            if company:
                industry_impact = model['impact_factors'].get(company.industry.value, -0.1)
                
                stock_impacts.append({
                    'symbol': symbol,
                    'company_name': company.name,
                    'industry': company.industry.value,
                    'expected_impact': industry_impact,
                    'impact_level': self._categorize_impact_level(industry_impact),
                    'reasoning': f"{company.name}屬於{company.industry.value}行業，預期受到{abs(industry_impact)*100:.0f}%的{'負面' if industry_impact < 0 else '正面'}影響"
                })
        
        return {
            'event_type': event_type,
            'event_description': model['description'],
            'transmission_channels': model['transmission_channels'],
            'stock_impacts': stock_impacts,
            'overall_market_impact': statistics.mean([impact['expected_impact'] for impact in stock_impacts]),
            'recommendations': self._generate_event_response_recommendations(event_type, stock_impacts)
        }
    
    def _categorize_impact_level(self, impact: float) -> str:
        """分類影響程度"""
        if impact <= -1.0:
            return "重大負面"
        elif impact <= -0.5:
            return "中度負面"
        elif impact <= -0.1:
            return "輕微負面"
        elif impact <= 0.1:
            return "中性"
        elif impact <= 0.5:
            return "輕微正面"
        elif impact <= 1.0:
            return "中度正面"
        else:
            return "重大正面"
    
    def _generate_event_response_recommendations(self, event_type: str, stock_impacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成事件應對建議"""
        recommendations = []
        
        # 按影響程度分組
        negative_impacts = [s for s in stock_impacts if s['expected_impact'] < -0.5]
        positive_impacts = [s for s in stock_impacts if s['expected_impact'] > 0.3]
        
        if negative_impacts:
            recommendations.append({
                'type': 'risk_management',
                'title': '降低高風險持股',
                'description': f'建議減持受{event_type}重大負面影響的股票',
                'affected_stocks': [s['symbol'] for s in negative_impacts],
                'action': 'reduce_position',
                'urgency': 'high'
            })
        
        if positive_impacts:
            recommendations.append({
                'type': 'opportunity_capture',
                'title': '增持受益股票',
                'description': f'可考慮增持在{event_type}中受益的股票',
                'affected_stocks': [s['symbol'] for s in positive_impacts],
                'action': 'increase_position',
                'urgency': 'medium'
            })
        
        recommendations.append({
            'type': 'portfolio_rebalancing',
            'title': '投資組合再平衡',
            'description': '根據事件影響調整投資組合配置，降低整體風險',
            'action': 'rebalance',
            'urgency': 'medium'
        })
        
        return recommendations
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        return {
            'company_database_size': len(self.company_database),
            'active_alerts_count': len(self.active_alerts),
            'supported_markets': [market.value for market in MarketRegion],
            'supported_industries': [industry.value for industry in IndustryCategory],
            'correlation_cache_size': len(self.correlation_cache),
            'service_uptime': datetime.now().isoformat()
        }