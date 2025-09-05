#!/usr/bin/env python3
"""
TradingAgents 用戶體驗和留存率優化服務
提供智能推薦、個人化建議、學習中心、社群功能等
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import statistics
from collections import defaultdict, deque

from ..utils.user_context import UserContext
from ..models.membership import TierType
from ..default_config import DEFAULT_CONFIG

# 設置日誌
logger = logging.getLogger(__name__)

class RecommendationType(Enum):
    """推薦類型"""
    STOCK_PICK = "stock_pick"           # 個股推薦
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"  # 組合優化
    RISK_MANAGEMENT = "risk_management"  # 風險管理
    MARKET_OPPORTUNITY = "market_opportunity"  # 市場機會
    EDUCATIONAL = "educational"         # 教育內容

class RiskProfile(Enum):
    """風險偏好"""
    CONSERVATIVE = "conservative"       # 保守型
    MODERATE = "moderate"              # 穩健型
    AGGRESSIVE = "aggressive"          # 積極型
    SPECULATIVE = "speculative"        # 投機型

class InvestmentGoal(Enum):
    """投資目標"""
    CAPITAL_PRESERVATION = "capital_preservation"  # 資本保值
    INCOME_GENERATION = "income_generation"        # 收益生成
    CAPITAL_GROWTH = "capital_growth"              # 資本增長
    SPECULATION = "speculation"                    # 投機交易

@dataclass
class UserProfile:
    """用戶投資檔案"""
    user_id: str
    risk_profile: RiskProfile
    investment_goals: List[InvestmentGoal]
    investment_horizon: str  # short_term, medium_term, long_term
    preferred_markets: List[str]
    preferred_sectors: List[str]
    portfolio_size: float
    experience_level: str  # beginner, intermediate, advanced, expert
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'risk_profile': self.risk_profile.value,
            'investment_goals': [goal.value for goal in self.investment_goals],
            'investment_horizon': self.investment_horizon,
            'preferred_markets': self.preferred_markets,
            'preferred_sectors': self.preferred_sectors,
            'portfolio_size': self.portfolio_size,
            'experience_level': self.experience_level,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

@dataclass
class SmartRecommendation:
    """智能推薦"""
    recommendation_id: str
    user_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    symbols: List[str]
    reasoning: str
    confidence_score: float
    expected_return: Optional[float] = None
    risk_level: Optional[str] = None
    time_horizon: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'recommendation_id': self.recommendation_id,
            'recommendation_type': self.recommendation_type.value,
            'title': self.title,
            'description': self.description,
            'symbols': self.symbols,
            'reasoning': self.reasoning,
            'confidence_score': self.confidence_score,
            'expected_return': self.expected_return,
            'risk_level': self.risk_level,
            'time_horizon': self.time_horizon,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

class UserExperienceService:
    """用戶體驗和留存率優化服務"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化服務"""
        self.config = config or DEFAULT_CONFIG
        
        # 用戶檔案存儲
        self.user_profiles: Dict[str, UserProfile] = {}
        
        # 推薦記錄
        self.recommendations: Dict[str, List[SmartRecommendation]] = defaultdict(list)
        
        # 學習內容庫
        self.learning_content = self._initialize_learning_content()
        
        # 社群內容
        self.community_posts = []
        self.user_interactions = defaultdict(list)
        
        # 績效追蹤
        self.performance_tracking = defaultdict(dict)
        
        logger.info("用戶體驗和留存率優化服務初始化完成")
    
    def _initialize_learning_content(self) -> Dict[str, Any]:
        """初始化學習內容庫"""
        return {
            'beginner': {
                'title': '國際投資入門指南',
                'modules': [
                    {
                        'id': 'intro_international_markets',
                        'title': '國際市場基礎知識',
                        'content': '了解全球主要股票市場的特點和交易時間',
                        'duration': '15分鐘',
                        'difficulty': 'beginner'
                    },
                    {
                        'id': 'currency_basics',
                        'title': '匯率風險入門',
                        'content': '學習匯率如何影響國際投資收益',
                        'duration': '20分鐘',
                        'difficulty': 'beginner'
                    }
                ]
            },
            'intermediate': {
                'title': '進階國際投資策略',
                'modules': [
                    {
                        'id': 'portfolio_diversification',
                        'title': '全球投資組合分散',
                        'content': '掌握跨市場、跨行業的分散投資技巧',
                        'duration': '30分鐘',
                        'difficulty': 'intermediate'
                    },
                    {
                        'id': 'correlation_analysis',
                        'title': '市場相關性分析',
                        'content': '學習如何分析不同市場間的相關性',
                        'duration': '25分鐘',
                        'difficulty': 'intermediate'
                    }
                ]
            },
            'advanced': {
                'title': '專業國際投資技術',
                'modules': [
                    {
                        'id': 'hedging_strategies',
                        'title': '高級避險策略',
                        'content': '掌握複雜的匯率和市場風險對沖技術',
                        'duration': '45分鐘',
                        'difficulty': 'advanced'
                    },
                    {
                        'id': 'global_macro_analysis',
                        'title': '全球宏觀分析',
                        'content': '學習分析全球經濟事件對投資的影響',
                        'duration': '40分鐘',
                        'difficulty': 'advanced'
                    }
                ]
            }
        }    

    async def create_user_profile(self, user_context: UserContext, profile_data: Dict[str, Any]) -> UserProfile:
        """
        創建用戶投資檔案
        
        Args:
            user_context: 用戶上下文
            profile_data: 檔案數據
            
        Returns:
            用戶投資檔案
        """
        profile = UserProfile(
            user_id=user_context.user_id,
            risk_profile=RiskProfile(profile_data.get('risk_profile', 'moderate')),
            investment_goals=[InvestmentGoal(goal) for goal in profile_data.get('investment_goals', ['capital_growth'])],
            investment_horizon=profile_data.get('investment_horizon', 'medium_term'),
            preferred_markets=profile_data.get('preferred_markets', ['taiwan', 'us']),
            preferred_sectors=profile_data.get('preferred_sectors', ['technology']),
            portfolio_size=profile_data.get('portfolio_size', 100000),
            experience_level=profile_data.get('experience_level', 'intermediate')
        )
        
        self.user_profiles[user_context.user_id] = profile
        
        logger.info(f"創建用戶投資檔案: {user_context.user_id}")
        return profile
    
    async def generate_smart_recommendations(self, user_context: UserContext, limit: int = 5) -> List[SmartRecommendation]:
        """
        生成智能推薦
        
        Args:
            user_context: 用戶上下文
            limit: 推薦數量限制
            
        Returns:
            智能推薦列表
        """
        user_profile = self.user_profiles.get(user_context.user_id)
        if not user_profile:
            # 創建默認檔案
            user_profile = await self.create_user_profile(user_context, {})
        
        recommendations = []
        
        # 基於風險偏好生成推薦
        if user_profile.risk_profile == RiskProfile.CONSERVATIVE:
            recommendations.extend(await self._generate_conservative_recommendations(user_profile))
        elif user_profile.risk_profile == RiskProfile.MODERATE:
            recommendations.extend(await self._generate_moderate_recommendations(user_profile))
        elif user_profile.risk_profile == RiskProfile.AGGRESSIVE:
            recommendations.extend(await self._generate_aggressive_recommendations(user_profile))
        
        # 基於投資目標生成推薦
        for goal in user_profile.investment_goals:
            if goal == InvestmentGoal.INCOME_GENERATION:
                recommendations.extend(await self._generate_income_recommendations(user_profile))
            elif goal == InvestmentGoal.CAPITAL_GROWTH:
                recommendations.extend(await self._generate_growth_recommendations(user_profile))
        
        # 按信心分數排序並限制數量
        recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        final_recommendations = recommendations[:limit]
        
        # 存儲推薦記錄
        self.recommendations[user_context.user_id].extend(final_recommendations)
        
        return final_recommendations
    
    async def _generate_conservative_recommendations(self, profile: UserProfile) -> List[SmartRecommendation]:
        """生成保守型推薦"""
        recommendations = []
        
        # 推薦穩定的大型股
        rec = SmartRecommendation(
            recommendation_id=self._generate_recommendation_id(profile.user_id, "conservative_large_cap"),
            user_id=profile.user_id,
            recommendation_type=RecommendationType.STOCK_PICK,
            title="穩健大型股投資組合",
            description="推薦具有穩定股息和低波動性的大型藍籌股",
            symbols=["2330", "AAPL", "MSFT", "JNJ"],
            reasoning="這些公司具有穩定的現金流、持續的股息支付和較低的價格波動，適合保守型投資者",
            confidence_score=0.85,
            expected_return=0.08,
            risk_level="low",
            time_horizon="long_term",
            expires_at=datetime.now() + timedelta(days=30)
        )
        recommendations.append(rec)
        
        return recommendations
    
    async def _generate_moderate_recommendations(self, profile: UserProfile) -> List[SmartRecommendation]:
        """生成穩健型推薦"""
        recommendations = []
        
        # 推薦平衡型投資組合
        rec = SmartRecommendation(
            recommendation_id=self._generate_recommendation_id(profile.user_id, "moderate_balanced"),
            user_id=profile.user_id,
            recommendation_type=RecommendationType.PORTFOLIO_OPTIMIZATION,
            title="平衡型全球投資組合",
            description="結合成長股和價值股的平衡配置，分散投資於台股和美股",
            symbols=["2330", "2317", "AAPL", "GOOGL", "TSLA"],
            reasoning="通過結合台股龍頭和美股成長股，在追求合理回報的同時控制風險",
            confidence_score=0.78,
            expected_return=0.12,
            risk_level="medium",
            time_horizon="medium_term",
            expires_at=datetime.now() + timedelta(days=21)
        )
        recommendations.append(rec)
        
        return recommendations
    
    async def _generate_aggressive_recommendations(self, profile: UserProfile) -> List[SmartRecommendation]:
        """生成積極型推薦"""
        recommendations = []
        
        # 推薦高成長潛力股票
        rec = SmartRecommendation(
            recommendation_id=self._generate_recommendation_id(profile.user_id, "aggressive_growth"),
            user_id=profile.user_id,
            recommendation_type=RecommendationType.MARKET_OPPORTUNITY,
            title="高成長科技股機會",
            description="聚焦於AI、電動車等新興科技領域的高成長潛力股票",
            symbols=["NVDA", "TSLA", "PLTR", "2454"],
            reasoning="這些公司處於快速成長的新興科技領域，具有顛覆性創新潛力和高成長預期",
            confidence_score=0.72,
            expected_return=0.25,
            risk_level="high",
            time_horizon="short_term",
            expires_at=datetime.now() + timedelta(days=14)
        )
        recommendations.append(rec)
        
        return recommendations
    
    async def _generate_income_recommendations(self, profile: UserProfile) -> List[SmartRecommendation]:
        """生成收益型推薦"""
        recommendations = []
        
        rec = SmartRecommendation(
            recommendation_id=self._generate_recommendation_id(profile.user_id, "income_dividend"),
            user_id=profile.user_id,
            recommendation_type=RecommendationType.STOCK_PICK,
            title="高股息收益股票",
            description="精選具有穩定高股息的優質股票，提供持續現金流",
            symbols=["2881", "2882", "VZ", "T"],
            reasoning="這些公司具有穩定的業務模式和持續的股息支付歷史，適合追求收益的投資者",
            confidence_score=0.80,
            expected_return=0.06,
            risk_level="low",
            time_horizon="long_term"
        )
        recommendations.append(rec)
        
        return recommendations
    
    async def _generate_growth_recommendations(self, profile: UserProfile) -> List[SmartRecommendation]:
        """生成成長型推薦"""
        recommendations = []
        
        rec = SmartRecommendation(
            recommendation_id=self._generate_recommendation_id(profile.user_id, "growth_tech"),
            user_id=profile.user_id,
            recommendation_type=RecommendationType.STOCK_PICK,
            title="科技成長股精選",
            description="挑選具有強勁成長動能的科技股，把握數位轉型趨勢",
            symbols=["2330", "AAPL", "GOOGL", "AMZN"],
            reasoning="這些科技巨頭在各自領域具有領導地位，受益於數位化趨勢和創新能力",
            confidence_score=0.75,
            expected_return=0.15,
            risk_level="medium",
            time_horizon="medium_term"
        )
        recommendations.append(rec)
        
        return recommendations
    
    def _generate_recommendation_id(self, user_id: str, rec_type: str) -> str:
        """生成推薦ID"""
        timestamp = int(datetime.now().timestamp())
        content = f"{user_id}_{rec_type}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]  # 安全修復：使用SHA256替換MD5
    
    async def get_personalized_learning_path(self, user_context: UserContext) -> Dict[str, Any]:
        """
        獲取個人化學習路徑
        
        Args:
            user_context: 用戶上下文
            
        Returns:
            個人化學習路徑
        """
        user_profile = self.user_profiles.get(user_context.user_id)
        experience_level = user_profile.experience_level if user_profile else 'beginner'
        
        # 獲取對應等級的學習內容
        learning_path = self.learning_content.get(experience_level, self.learning_content['beginner'])
        
        # 基於用戶偏好調整內容
        if user_profile:
            # 添加市場特定內容
            if 'us' in user_profile.preferred_markets:
                learning_path['modules'].append({
                    'id': 'us_market_specifics',
                    'title': '美股市場特色',
                    'content': '深入了解美股市場的交易規則和投資機會',
                    'duration': '25分鐘',
                    'difficulty': experience_level
                })
            
            # 添加行業特定內容
            if 'technology' in user_profile.preferred_sectors:
                learning_path['modules'].append({
                    'id': 'tech_investment_analysis',
                    'title': '科技股投資分析',
                    'content': '學習如何評估科技公司的投資價值',
                    'duration': '35分鐘',
                    'difficulty': experience_level
                })
        
        return {
            'user_id': user_context.user_id,
            'experience_level': experience_level,
            'learning_path': learning_path,
            'progress': self._get_learning_progress(user_context.user_id),
            'recommended_next_steps': self._get_next_learning_steps(user_context.user_id, experience_level)
        }
    
    def _get_learning_progress(self, user_id: str) -> Dict[str, Any]:
        """獲取學習進度"""
        # 模擬學習進度數據
        return {
            'completed_modules': 3,
            'total_modules': 8,
            'completion_rate': 37.5,
            'study_time_hours': 2.5,
            'last_activity': (datetime.now() - timedelta(days=2)).isoformat()
        }
    
    def _get_next_learning_steps(self, user_id: str, experience_level: str) -> List[Dict[str, Any]]:
        """獲取下一步學習建議"""
        next_steps = []
        
        if experience_level == 'beginner':
            next_steps = [
                {
                    'title': '完成國際市場基礎課程',
                    'description': '建議先完成基礎知識學習',
                    'priority': 'high'
                },
                {
                    'title': '開始模擬投資',
                    'description': '使用虛擬資金練習國際投資',
                    'priority': 'medium'
                }
            ]
        elif experience_level == 'intermediate':
            next_steps = [
                {
                    'title': '學習高級分析技術',
                    'description': '掌握技術分析和基本面分析',
                    'priority': 'high'
                },
                {
                    'title': '參與投資社群討論',
                    'description': '與其他投資者交流經驗',
                    'priority': 'medium'
                }
            ]
        
        return next_steps
    
    async def create_community_post(self, user_context: UserContext, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建社群貼文
        
        Args:
            user_context: 用戶上下文
            post_data: 貼文數據
            
        Returns:
            創建的貼文
        """
        post = {
            'post_id': hashlib.sha256(f"{user_context.user_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:12],  # 安全修復：使用SHA256替換MD5
            'user_id': user_context.user_id,
            'title': post_data.get('title', ''),
            'content': post_data.get('content', ''),
            'category': post_data.get('category', 'general'),  # general, analysis, question, experience
            'tags': post_data.get('tags', []),
            'symbols_mentioned': post_data.get('symbols_mentioned', []),
            'created_at': datetime.now().isoformat(),
            'likes': 0,
            'comments': [],
            'views': 0
        }
        
        self.community_posts.append(post)
        
        # 記錄用戶互動
        self.user_interactions[user_context.user_id].append({
            'type': 'post_created',
            'post_id': post['post_id'],
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"創建社群貼文: {user_context.user_id} - {post['title']}")
        return post
    
    async def get_community_feed(self, user_context: UserContext, category: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        獲取社群動態
        
        Args:
            user_context: 用戶上下文
            category: 分類過濾
            limit: 返回數量限制
            
        Returns:
            社群貼文列表
        """
        # 過濾貼文
        filtered_posts = self.community_posts
        
        if category:
            filtered_posts = [post for post in filtered_posts if post['category'] == category]
        
        # 按時間排序
        filtered_posts.sort(key=lambda x: x['created_at'], reverse=True)
        
        # 限制數量
        return filtered_posts[:limit]
    
    async def add_comment_to_post(self, user_context: UserContext, post_id: str, comment_content: str) -> bool:
        """
        為貼文添加評論
        
        Args:
            user_context: 用戶上下文
            post_id: 貼文ID
            comment_content: 評論內容
            
        Returns:
            是否成功添加
        """
        # 找到對應貼文
        post = None
        for p in self.community_posts:
            if p['post_id'] == post_id:
                post = p
                break
        
        if not post:
            return False
        
        comment = {
            'comment_id': hashlib.sha256(f"{user_context.user_id}_{post_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:8],  # 安全修復：使用SHA256替換MD5
            'user_id': user_context.user_id,
            'content': comment_content,
            'created_at': datetime.now().isoformat(),
            'likes': 0
        }
        
        post['comments'].append(comment)
        
        # 記錄用戶互動
        self.user_interactions[user_context.user_id].append({
            'type': 'comment_added',
            'post_id': post_id,
            'comment_id': comment['comment_id'],
            'timestamp': datetime.now().isoformat()
        })
        
        return True
    
    async def track_portfolio_performance(self, user_context: UserContext, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        追蹤投資組合績效
        
        Args:
            user_context: 用戶上下文
            portfolio_data: 投資組合數據
            
        Returns:
            績效追蹤結果
        """
        user_id = user_context.user_id
        
        # 存儲投資組合快照
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'portfolio': portfolio_data,
            'total_value': portfolio_data.get('total_value', 0),
            'positions': portfolio_data.get('positions', [])
        }
        
        if 'snapshots' not in self.performance_tracking[user_id]:
            self.performance_tracking[user_id]['snapshots'] = []
        
        self.performance_tracking[user_id]['snapshots'].append(snapshot)
        
        # 計算績效指標
        performance_metrics = self._calculate_performance_metrics(user_id)
        
        return {
            'user_id': user_id,
            'current_snapshot': snapshot,
            'performance_metrics': performance_metrics,
            'benchmark_comparison': self._compare_with_benchmarks(performance_metrics),
            'recommendations': self._generate_performance_recommendations(performance_metrics)
        }
    
    def _calculate_performance_metrics(self, user_id: str) -> Dict[str, Any]:
        """計算績效指標"""
        snapshots = self.performance_tracking[user_id].get('snapshots', [])
        
        if len(snapshots) < 2:
            return {'error': '需要至少兩個時間點的數據來計算績效'}
        
        # 計算總回報率
        initial_value = snapshots[0]['total_value']
        current_value = snapshots[-1]['total_value']
        total_return = (current_value - initial_value) / initial_value if initial_value > 0 else 0
        
        # 計算時間加權回報率（簡化版）
        time_periods = len(snapshots) - 1
        annualized_return = ((1 + total_return) ** (365 / (time_periods * 30))) - 1  # 假設每月一個快照
        
        # 計算波動率（簡化版）
        returns = []
        for i in range(1, len(snapshots)):
            prev_value = snapshots[i-1]['total_value']
            curr_value = snapshots[i]['total_value']
            if prev_value > 0:
                returns.append((curr_value - prev_value) / prev_value)
        
        volatility = statistics.stdev(returns) if len(returns) > 1 else 0
        
        # 計算夏普比率（假設無風險利率為2%）
        risk_free_rate = 0.02
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_value': max(s['total_value'] for s in snapshots),
            'min_value': min(s['total_value'] for s in snapshots),
            'tracking_period_days': time_periods * 30
        }
    
    def _compare_with_benchmarks(self, performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """與基準指數比較"""
        # 模擬基準指數數據
        benchmarks = {
            'taiwan_weighted_index': {
                'name': '台灣加權指數',
                'return': 0.08,
                'volatility': 0.15
            },
            'sp500': {
                'name': 'S&P 500',
                'return': 0.10,
                'volatility': 0.12
            },
            'msci_world': {
                'name': 'MSCI 世界指數',
                'return': 0.09,
                'volatility': 0.13
            }
        }
        
        user_return = performance_metrics.get('annualized_return', 0)
        user_volatility = performance_metrics.get('volatility', 0)
        
        comparisons = {}
        for benchmark_id, benchmark in benchmarks.items():
            excess_return = user_return - benchmark['return']
            risk_adjusted_excess = excess_return / benchmark['volatility'] if benchmark['volatility'] > 0 else 0
            
            comparisons[benchmark_id] = {
                'name': benchmark['name'],
                'benchmark_return': benchmark['return'],
                'excess_return': excess_return,
                'risk_adjusted_excess': risk_adjusted_excess,
                'outperformed': excess_return > 0
            }
        
        return comparisons
    
    def _generate_performance_recommendations(self, performance_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成績效改善建議"""
        recommendations = []
        
        total_return = performance_metrics.get('total_return', 0)
        volatility = performance_metrics.get('volatility', 0)
        sharpe_ratio = performance_metrics.get('sharpe_ratio', 0)
        
        # 基於績效生成建議
        if total_return < 0:
            recommendations.append({
                'type': 'performance_improvement',
                'title': '投資組合表現需要改善',
                'description': '考慮重新評估投資策略和資產配置',
                'priority': 'high',
                'actions': [
                    '檢視持股品質和基本面',
                    '考慮分散投資降低風險',
                    '評估是否需要停損'
                ]
            })
        
        if volatility > 0.2:
            recommendations.append({
                'type': 'risk_management',
                'title': '投資組合波動性過高',
                'description': '建議增加穩定性資產以降低整體風險',
                'priority': 'medium',
                'actions': [
                    '增加債券或穩定股息股票',
                    '減少高風險投機性投資',
                    '考慮定期定額投資策略'
                ]
            })
        
        if sharpe_ratio < 0.5:
            recommendations.append({
                'type': 'efficiency_improvement',
                'title': '風險調整後回報偏低',
                'description': '投資組合的風險回報效率有改善空間',
                'priority': 'medium',
                'actions': [
                    '優化資產配置比例',
                    '考慮低成本指數基金',
                    '定期檢視和再平衡'
                ]
            })
        
        return recommendations
    
    async def generate_vip_research_report(self, user_context: UserContext, report_type: str = "weekly") -> Dict[str, Any]:
        """
        生成VIP用戶專屬研究報告
        
        Args:
            user_context: 用戶上下文
            report_type: 報告類型 (weekly, monthly, quarterly)
            
        Returns:
            研究報告
        """
        # 檢查用戶等級
        if user_context.membership_tier not in [TierType.DIAMOND]:
            return {
                'error': '此功能僅限 Diamond 會員使用',
                'upgrade_prompt': {
                    'title': '🔬 專屬研究報告',
                    'message': '升級至 Diamond 會員，獲得專業投資研究團隊的獨家報告',
                    'benefits': [
                        '每週專業市場分析報告',
                        '獨家投資機會發掘',
                        '深度行業研究分析',
                        '個人化投資策略建議'
                    ]
                }
            }
        
        # 生成報告內容
        report = {
            'report_id': hashlib.sha256(f"vip_report_{user_context.user_id}_{datetime.now().timestamp()}".encode()).hexdigest()[:12],  # 安全修復：使用SHA256替換MD5
            'user_id': user_context.user_id,
            'report_type': report_type,
            'title': f'VIP 專屬{report_type}市場研究報告',
            'generated_at': datetime.now().isoformat(),
            'sections': [
                {
                    'title': '市場概況',
                    'content': '本週全球股市表現分析，重點關注美股科技股和台股半導體類股的表現',
                    'key_points': [
                        '美股科技股受AI概念推動持續上漲',
                        '台股半導體族群受惠於AI晶片需求',
                        '地緣政治風險對市場情緒的影響'
                    ]
                },
                {
                    'title': '投資機會分析',
                    'content': '基於當前市場環境，我們識別出以下投資機會',
                    'opportunities': [
                        {
                            'symbol': '2330',
                            'name': '台積電',
                            'recommendation': 'BUY',
                            'target_price': 600,
                            'reasoning': 'AI晶片需求強勁，先進製程技術領先'
                        },
                        {
                            'symbol': 'NVDA',
                            'name': 'NVIDIA',
                            'recommendation': 'HOLD',
                            'target_price': 500,
                            'reasoning': 'AI領域龍頭地位穩固，但估值偏高'
                        }
                    ]
                },
                {
                    'title': '風險提醒',
                    'content': '投資者需要關注的主要風險因素',
                    'risks': [
                        '美聯儲貨幣政策變化風險',
                        '中美科技競爭加劇風險',
                        '全球經濟衰退風險'
                    ]
                },
                {
                    'title': '個人化建議',
                    'content': '基於您的投資檔案，我們提供以下個人化建議',
                    'personalized_advice': await self._generate_personalized_advice(user_context)
                }
            ],
            'disclaimer': '本報告僅供參考，不構成投資建議。投資有風險，請謹慎決策。'
        }
        
        return report
    
    async def _generate_personalized_advice(self, user_context: UserContext) -> List[str]:
        """生成個人化建議"""
        user_profile = self.user_profiles.get(user_context.user_id)
        
        advice = []
        
        if user_profile:
            if user_profile.risk_profile == RiskProfile.CONSERVATIVE:
                advice.extend([
                    '建議維持較高的現金比例以應對市場波動',
                    '可考慮增加高股息股票的配置',
                    '避免過度集中於單一市場或行業'
                ])
            elif user_profile.risk_profile == RiskProfile.AGGRESSIVE:
                advice.extend([
                    '可適度增加成長股的配置比例',
                    '關注新興科技領域的投資機會',
                    '建議設定停損點控制下檔風險'
                ])
            
            if 'technology' in user_profile.preferred_sectors:
                advice.append('科技股波動較大，建議分批建倉降低成本')
        
        return advice or ['建議完善投資檔案以獲得更精準的個人化建議']
    
    async def get_user_engagement_stats(self, user_context: UserContext) -> Dict[str, Any]:
        """獲取用戶參與度統計"""
        user_id = user_context.user_id
        
        # 統計用戶互動
        interactions = self.user_interactions.get(user_id, [])
        
        # 按類型統計
        interaction_counts = defaultdict(int)
        for interaction in interactions:
            interaction_counts[interaction['type']] += 1
        
        # 計算活躍度分數
        activity_score = (
            interaction_counts['post_created'] * 10 +
            interaction_counts['comment_added'] * 5 +
            interaction_counts.get('recommendation_viewed', 0) * 2 +
            interaction_counts.get('learning_completed', 0) * 8
        )
        
        return {
            'user_id': user_id,
            'total_interactions': len(interactions),
            'interaction_breakdown': dict(interaction_counts),
            'activity_score': activity_score,
            'engagement_level': self._categorize_engagement_level(activity_score),
            'last_activity': interactions[-1]['timestamp'] if interactions else None,
            'recommendations_count': len(self.recommendations.get(user_id, [])),
            'community_contributions': interaction_counts['post_created'] + interaction_counts['comment_added']
        }
    
    def _categorize_engagement_level(self, activity_score: int) -> str:
        """分類參與度等級"""
        if activity_score >= 100:
            return "highly_engaged"
        elif activity_score >= 50:
            return "moderately_engaged"
        elif activity_score >= 20:
            return "lightly_engaged"
        else:
            return "inactive"
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """獲取服務統計信息"""
        return {
            'total_users': len(self.user_profiles),
            'total_recommendations': sum(len(recs) for recs in self.recommendations.values()),
            'community_posts': len(self.community_posts),
            'total_interactions': sum(len(interactions) for interactions in self.user_interactions.values()),
            'learning_modules': sum(len(content['modules']) for content in self.learning_content.values()),
            'performance_tracking_users': len(self.performance_tracking),
            'service_uptime': datetime.now().isoformat()
        }