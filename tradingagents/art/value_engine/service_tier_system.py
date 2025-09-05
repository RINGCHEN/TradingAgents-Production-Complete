#!/usr/bin/env python3
"""
Service Tier System - 價值服務分層系統
天工 (TianGong) - 為ART系統提供價值服務分層和個人化推薦

此模組提供：
1. ServiceTierSystem - 服務分層系統核心
2. TierMatcher - 層級匹配器
3. PersonalizedRecommendationEngine - 個人化推薦引擎
4. ValueAlignmentAnalyzer - 價值對齊分析器
5. ServiceUpgradeAdvisor - 服務升級建議器
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
from collections import defaultdict
import math

# 導入價值引擎和個人化組件
from .value_service_engine import ServiceTier, ValueService, CustomerSegment, ValueProposition
from .service_utilization_analyzer import ServiceUtilizationAnalyzer, UtilizationMetrics
from ..personalization.user_profile_analyzer import (
    UserProfileAnalyzer, UserBehaviorModel, PreferenceProfile, 
    BehaviorPattern, PersonalityMetrics
)

class TierMatchingStrategy(Enum):
    """層級匹配策略"""
    VALUE_BASED = "value_based"           # 基於價值匹配
    BEHAVIOR_BASED = "behavior_based"     # 基於行為模式匹配
    PROGRESSIVE = "progressive"           # 漸進式匹配
    HYBRID = "hybrid"                     # 混合匹配策略

class RecommendationType(Enum):
    """推薦類型"""
    TIER_UPGRADE = "tier_upgrade"         # 層級升級
    FEATURE_ACTIVATION = "feature_activation"  # 功能激活
    USAGE_OPTIMIZATION = "usage_optimization"  # 使用優化
    VALUE_ENHANCEMENT = "value_enhancement"    # 價值提升
    COST_OPTIMIZATION = "cost_optimization"   # 成本優化

class AlignmentScore(Enum):
    """對齊分數等級"""
    EXCELLENT = "excellent"        # 優秀對齊 (90-100%)
    GOOD = "good"                 # 良好對齊 (70-89%)
    FAIR = "fair"                 # 一般對齊 (50-69%)
    POOR = "poor"                 # 較差對齊 (30-49%)
    MISALIGNED = "misaligned"     # 不對齊 (<30%)

@dataclass
class TierRecommendation:
    """層級推薦"""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # 推薦內容
    recommended_tier: ServiceTier = ServiceTier.BASIC
    current_tier: ServiceTier = ServiceTier.BASIC
    recommendation_type: RecommendationType = RecommendationType.TIER_UPGRADE
    
    # 推薦理由
    rationale: str = ""
    key_benefits: List[str] = field(default_factory=list)
    value_proposition: str = ""
    
    # 匹配分析
    alignment_score: float = 0.0
    alignment_grade: AlignmentScore = AlignmentScore.FAIR
    confidence_level: float = 0.0
    
    # 財務分析
    expected_value_increase: float = 0.0
    investment_required: float = 0.0
    roi_projection: float = 0.0
    payback_period_months: float = 0.0
    
    # 實施建議
    implementation_timeline: str = ""
    prerequisites: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    
    # 風險評估
    risks: List[str] = field(default_factory=list)
    risk_mitigation: List[str] = field(default_factory=list)
    
    # 時間戳記
    created_at: float = field(default_factory=time.time)
    valid_until: float = field(default_factory=lambda: time.time() + 604800)  # 7天有效
    
    # 元數據
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ServicePortfolio:
    """服務組合"""
    user_id: str
    portfolio_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 服務組合
    active_services: List[ValueService] = field(default_factory=list)
    recommended_services: List[ValueService] = field(default_factory=list)
    
    # 組合分析
    total_value: float = 0.0
    total_cost: float = 0.0
    portfolio_roi: float = 0.0
    
    # 個人化指標
    personalization_score: float = 0.0
    usage_efficiency: float = 0.0
    value_realization_rate: float = 0.0
    
    # 優化建議
    optimization_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    upgrade_recommendations: List[TierRecommendation] = field(default_factory=list)
    
    # 時間戳記
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)

class TierMatcher:
    """層級匹配器"""
    
    def __init__(self):
        self.matching_rules: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化匹配規則
        self._initialize_matching_rules()
    
    def _initialize_matching_rules(self):
        """初始化匹配規則"""
        self.matching_rules = {
            'value_thresholds': {
                ServiceTier.BASIC: {'min_value': 0, 'max_value': 5000},
                ServiceTier.PREMIUM: {'min_value': 5000, 'max_value': 15000},
                ServiceTier.ENTERPRISE: {'min_value': 15000, 'max_value': float('inf')},
                ServiceTier.CUSTOM: {'min_value': 50000, 'max_value': float('inf')}
            },
            'behavior_patterns': {
                ServiceTier.BASIC: [BehaviorPattern.CONSERVATIVE, BehaviorPattern.LONG_TERM],
                ServiceTier.PREMIUM: [BehaviorPattern.BALANCED, BehaviorPattern.SWING_TRADER],
                ServiceTier.ENTERPRISE: [BehaviorPattern.AGGRESSIVE, BehaviorPattern.DAY_TRADER],
                ServiceTier.CUSTOM: [BehaviorPattern.MOMENTUM, BehaviorPattern.CONTRARIAN]
            },
            'usage_criteria': {
                ServiceTier.BASIC: {'min_frequency': 0.0, 'complexity_tolerance': 0.3},
                ServiceTier.PREMIUM: {'min_frequency': 0.3, 'complexity_tolerance': 0.6},
                ServiceTier.ENTERPRISE: {'min_frequency': 0.6, 'complexity_tolerance': 0.8},
                ServiceTier.CUSTOM: {'min_frequency': 0.8, 'complexity_tolerance': 1.0}
            }
        }
    
    async def match_optimal_tier(self, user_behavior: UserBehaviorModel,
                               user_preferences: PreferenceProfile,
                               current_value: float,
                               strategy: TierMatchingStrategy = TierMatchingStrategy.HYBRID) -> Dict[str, Any]:
        """匹配最優服務層級"""
        try:
            matching_scores = {}
            
            if strategy in [TierMatchingStrategy.VALUE_BASED, TierMatchingStrategy.HYBRID]:
                value_scores = await self._calculate_value_based_scores(current_value)
                matching_scores.update(value_scores)
            
            if strategy in [TierMatchingStrategy.BEHAVIOR_BASED, TierMatchingStrategy.HYBRID]:
                behavior_scores = await self._calculate_behavior_based_scores(user_behavior)
                for tier, score in behavior_scores.items():
                    if tier in matching_scores:
                        matching_scores[tier] = (matching_scores[tier] + score) / 2
                    else:
                        matching_scores[tier] = score
            
            # 基於用戶偏好調整分數
            preference_adjustments = await self._calculate_preference_adjustments(user_preferences)
            for tier, adjustment in preference_adjustments.items():
                if tier in matching_scores:
                    matching_scores[tier] *= adjustment
            
            # 選擇最高分數的層級
            if matching_scores:
                optimal_tier = max(matching_scores.items(), key=lambda x: x[1])
                
                return {
                    'recommended_tier': optimal_tier[0],
                    'confidence_score': optimal_tier[1],
                    'all_scores': matching_scores,
                    'matching_rationale': await self._generate_matching_rationale(
                        optimal_tier[0], matching_scores, user_behavior, user_preferences
                    )
                }
            else:
                return {
                    'recommended_tier': ServiceTier.BASIC,
                    'confidence_score': 0.5,
                    'all_scores': {},
                    'matching_rationale': "默認基礎服務層級"
                }
                
        except Exception as e:
            self.logger.error(f"Tier matching failed: {e}")
            raise
    
    async def _calculate_value_based_scores(self, current_value: float) -> Dict[ServiceTier, float]:
        """計算基於價值的分數"""
        scores = {}
        thresholds = self.matching_rules['value_thresholds']
        
        for tier, bounds in thresholds.items():
            min_val = bounds['min_value']
            max_val = bounds['max_value']
            
            if min_val <= current_value < max_val:
                # 在範圍內給高分
                range_position = (current_value - min_val) / (max_val - min_val) if max_val != float('inf') else 0.8
                scores[tier] = 0.8 + (range_position * 0.2)
            elif current_value < min_val:
                # 低於範圍給較低分
                distance_factor = (min_val - current_value) / min_val if min_val > 0 else 0
                scores[tier] = max(0.2, 0.6 - distance_factor * 0.4)
            else:
                # 高於範圍的情況
                if max_val == float('inf'):
                    scores[tier] = 0.9  # 無上限層級給高分
                else:
                    excess_factor = (current_value - max_val) / max_val
                    scores[tier] = max(0.3, 0.7 - excess_factor * 0.2)
        
        return scores
    
    async def _calculate_behavior_based_scores(self, user_behavior: UserBehaviorModel) -> Dict[ServiceTier, float]:
        """計算基於行為的分數"""
        scores = {}
        pattern_rules = self.matching_rules['behavior_patterns']
        usage_rules = self.matching_rules['usage_criteria']
        
        for tier, expected_patterns in pattern_rules.items():
            score = 0.0
            
            # 基於行為模式匹配
            pattern_matches = sum(1 for pattern in user_behavior.behavior_patterns 
                                if pattern in expected_patterns)
            if user_behavior.behavior_patterns:
                pattern_score = pattern_matches / len(user_behavior.behavior_patterns)
                score += pattern_score * 0.4
            
            # 基於使用頻率匹配
            usage_criteria = usage_rules.get(tier, {})
            min_frequency = usage_criteria.get('min_frequency', 0)
            if user_behavior.trading_frequency >= min_frequency:
                frequency_score = min(1.0, user_behavior.trading_frequency / (min_frequency + 0.1))
                score += frequency_score * 0.3
            
            # 基於風險容忍度
            risk_tolerance = user_behavior.personality_scores.get(PersonalityMetrics.RISK_TOLERANCE, 0.5)
            if tier == ServiceTier.BASIC and risk_tolerance < 0.4:
                score += 0.2
            elif tier == ServiceTier.PREMIUM and 0.4 <= risk_tolerance < 0.7:
                score += 0.2
            elif tier == ServiceTier.ENTERPRISE and risk_tolerance >= 0.7:
                score += 0.2
            
            # 基於學習能力
            learning_rate = user_behavior.personality_scores.get(PersonalityMetrics.LEARNING_RATE, 0.5)
            complexity_tolerance = usage_criteria.get('complexity_tolerance', 0.5)
            if learning_rate >= complexity_tolerance:
                score += 0.1
            
            scores[tier] = score
        
        return scores
    
    async def _calculate_preference_adjustments(self, user_preferences: PreferenceProfile) -> Dict[ServiceTier, float]:
        """計算偏好調整因子"""
        adjustments = {tier: 1.0 for tier in ServiceTier}
        
        # 基於複雜度容忍度調整
        complexity_tolerance = user_preferences.complexity_tolerance
        if complexity_tolerance > 0.8:
            adjustments[ServiceTier.ENTERPRISE] *= 1.2
            adjustments[ServiceTier.CUSTOM] *= 1.1
        elif complexity_tolerance < 0.3:
            adjustments[ServiceTier.BASIC] *= 1.2
            adjustments[ServiceTier.PREMIUM] *= 0.9
        
        # 基於風險預算調整
        risk_budget = user_preferences.risk_budget
        if risk_budget > 0.3:
            adjustments[ServiceTier.PREMIUM] *= 1.1
            adjustments[ServiceTier.ENTERPRISE] *= 1.2
        elif risk_budget < 0.1:
            adjustments[ServiceTier.BASIC] *= 1.2
        
        # 基於主動vs被動偏好調整
        active_preference = user_preferences.active_vs_passive
        if active_preference > 0.7:
            adjustments[ServiceTier.PREMIUM] *= 1.1
            adjustments[ServiceTier.ENTERPRISE] *= 1.2
        elif active_preference < 0.3:
            adjustments[ServiceTier.BASIC] *= 1.1
        
        return adjustments
    
    async def _generate_matching_rationale(self, recommended_tier: ServiceTier,
                                         all_scores: Dict[ServiceTier, float],
                                         user_behavior: UserBehaviorModel,
                                         user_preferences: PreferenceProfile) -> str:
        """生成匹配理由"""
        rationale_parts = []
        
        # 主要推薦理由
        rationale_parts.append(f"推薦 {recommended_tier.value} 層級")
        
        # 基於行為模式的理由
        if user_behavior.behavior_patterns:
            primary_pattern = user_behavior.behavior_patterns[0]
            if primary_pattern in [BehaviorPattern.CONSERVATIVE, BehaviorPattern.LONG_TERM]:
                rationale_parts.append("基於您的保守投資風格")
            elif primary_pattern in [BehaviorPattern.AGGRESSIVE, BehaviorPattern.DAY_TRADER]:
                rationale_parts.append("基於您的積極交易風格")
            else:
                rationale_parts.append("基於您的平衡投資策略")
        
        # 基於偏好的理由
        if user_preferences.complexity_tolerance > 0.7:
            rationale_parts.append("您能接受複雜功能")
        elif user_preferences.complexity_tolerance < 0.3:
            rationale_parts.append("您偏好簡單易用的功能")
        
        # 基於分數差異的理由
        score_diff = all_scores.get(recommended_tier, 0) - max(
            [score for tier, score in all_scores.items() if tier != recommended_tier] + [0]
        )
        if score_diff > 0.2:
            rationale_parts.append("此層級與您的需求高度匹配")
        elif score_diff > 0.1:
            rationale_parts.append("此層級適合您的當前需求")
        
        return "，".join(rationale_parts)

class PersonalizedRecommendationEngine:
    """個人化推薦引擎"""
    
    def __init__(self):
        self.tier_matcher = TierMatcher()
        self.recommendation_history: Dict[str, List[TierRecommendation]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def generate_personalized_recommendations(self, user_id: str,
                                                  user_behavior: UserBehaviorModel,
                                                  user_preferences: PreferenceProfile,
                                                  current_services: List[ValueService],
                                                  utilization_metrics: Optional[UtilizationMetrics] = None) -> List[TierRecommendation]:
        """生成個人化推薦"""
        try:
            recommendations = []
            
            # 分析當前服務狀態
            current_analysis = await self._analyze_current_services(current_services, utilization_metrics)
            
            # 生成層級升級推薦
            tier_recommendations = await self._generate_tier_upgrade_recommendations(
                user_id, user_behavior, user_preferences, current_analysis
            )
            recommendations.extend(tier_recommendations)
            
            # 生成功能激活推薦
            feature_recommendations = await self._generate_feature_recommendations(
                user_id, user_behavior, user_preferences, current_services
            )
            recommendations.extend(feature_recommendations)
            
            # 生成使用優化推薦
            if utilization_metrics:
                optimization_recommendations = await self._generate_optimization_recommendations(
                    user_id, utilization_metrics, user_behavior
                )
                recommendations.extend(optimization_recommendations)
            
            # 排序推薦（按ROI和對齊分數）
            recommendations.sort(key=lambda r: (r.roi_projection, r.alignment_score), reverse=True)
            
            # 緩存推薦結果
            self.recommendation_history[user_id] = recommendations
            
            self.logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
            return recommendations[:5]  # 返回前5個推薦
            
        except Exception as e:
            self.logger.error(f"Personalized recommendation generation failed: {e}")
            raise
    
    async def _analyze_current_services(self, current_services: List[ValueService],
                                      utilization_metrics: Optional[UtilizationMetrics]) -> Dict[str, Any]:
        """分析當前服務狀態"""
        analysis = {
            'service_count': len(current_services),
            'tier_distribution': defaultdict(int),
            'total_value': 0.0,
            'total_cost': 0.0,
            'utilization_efficiency': 0.0,
            'value_gaps': []
        }
        
        for service in current_services:
            analysis['tier_distribution'][service.tier] += 1
            analysis['total_value'] += service.monthly_recurring_revenue
            # 假設成本為收入的30%
            analysis['total_cost'] += service.monthly_recurring_revenue * 0.3
        
        if utilization_metrics:
            analysis['utilization_efficiency'] = utilization_metrics.value_realization_rate
            
            # 識別價值缺口
            if utilization_metrics.value_realization_rate < 0.6:
                analysis['value_gaps'].append('low_value_realization')
            if utilization_metrics.task_completion_rate < 0.7:
                analysis['value_gaps'].append('low_task_completion')
            if utilization_metrics.user_satisfaction_score < 3.5:
                analysis['value_gaps'].append('low_satisfaction')
        
        return analysis
    
    async def _generate_tier_upgrade_recommendations(self, user_id: str,
                                                   user_behavior: UserBehaviorModel,
                                                   user_preferences: PreferenceProfile,
                                                   current_analysis: Dict[str, Any]) -> List[TierRecommendation]:
        """生成層級升級推薦"""
        recommendations = []
        
        # 獲取最優層級匹配
        matching_result = await self.tier_matcher.match_optimal_tier(
            user_behavior, user_preferences, current_analysis['total_value']
        )
        
        recommended_tier = matching_result['recommended_tier']
        current_tier = self._determine_dominant_tier(current_analysis['tier_distribution'])
        
        # 如果推薦層級高於當前層級，生成升級推薦
        if self._is_tier_upgrade(current_tier, recommended_tier):
            recommendation = TierRecommendation(
                user_id=user_id,
                recommended_tier=recommended_tier,
                current_tier=current_tier,
                recommendation_type=RecommendationType.TIER_UPGRADE,
                rationale=matching_result['matching_rationale'],
                alignment_score=matching_result['confidence_score'],
                confidence_level=matching_result['confidence_score']
            )
            
            # 計算升級效益
            await self._calculate_upgrade_benefits(recommendation, user_behavior, current_analysis)
            
            # 設置實施建議
            await self._set_implementation_guidance(recommendation, user_behavior, user_preferences)
            
            recommendations.append(recommendation)
        
        return recommendations
    
    def _determine_dominant_tier(self, tier_distribution: Dict[ServiceTier, int]) -> ServiceTier:
        """確定主導服務層級"""
        if not tier_distribution:
            return ServiceTier.BASIC
        
        # 返回數量最多的層級
        return max(tier_distribution.items(), key=lambda x: x[1])[0]
    
    def _is_tier_upgrade(self, current_tier: ServiceTier, recommended_tier: ServiceTier) -> bool:
        """判斷是否為層級升級"""
        tier_order = {
            ServiceTier.BASIC: 1,
            ServiceTier.PREMIUM: 2,
            ServiceTier.ENTERPRISE: 3,
            ServiceTier.CUSTOM: 4
        }
        
        return tier_order.get(recommended_tier, 1) > tier_order.get(current_tier, 1)
    
    async def _calculate_upgrade_benefits(self, recommendation: TierRecommendation,
                                        user_behavior: UserBehaviorModel,
                                        current_analysis: Dict[str, Any]):
        """計算升級效益"""
        # 估算價值增長
        current_value = current_analysis['total_value']
        
        # 基於層級估算價值增長倍數
        tier_multipliers = {
            ServiceTier.PREMIUM: 1.5,
            ServiceTier.ENTERPRISE: 2.5,
            ServiceTier.CUSTOM: 4.0
        }
        
        multiplier = tier_multipliers.get(recommendation.recommended_tier, 1.2)
        recommendation.expected_value_increase = current_value * (multiplier - 1)
        
        # 估算投資成本
        tier_costs = {
            ServiceTier.PREMIUM: 2000,
            ServiceTier.ENTERPRISE: 8000,
            ServiceTier.CUSTOM: 25000
        }
        
        recommendation.investment_required = tier_costs.get(recommendation.recommended_tier, 1000)
        
        # 計算ROI
        if recommendation.investment_required > 0:
            recommendation.roi_projection = (recommendation.expected_value_increase / 
                                           recommendation.investment_required) * 100
            
            # 計算回收期（月）
            monthly_value_increase = recommendation.expected_value_increase / 12
            if monthly_value_increase > 0:
                recommendation.payback_period_months = recommendation.investment_required / monthly_value_increase
        
        # 設置關鍵效益
        recommendation.key_benefits = await self._identify_tier_benefits(
            recommendation.recommended_tier, user_behavior
        )
    
    async def _identify_tier_benefits(self, tier: ServiceTier, 
                                    user_behavior: UserBehaviorModel) -> List[str]:
        """識別層級效益"""
        benefits = []
        
        if tier == ServiceTier.PREMIUM:
            benefits.extend([
                "高級分析工具",
                "實時市場數據",
                "個人化投資建議",
                "優先客戶支持"
            ])
            
            # 基於用戶行為添加特定效益
            if BehaviorPattern.DAY_TRADER in user_behavior.behavior_patterns:
                benefits.append("高頻交易優化工具")
            if user_behavior.personality_scores.get(PersonalityMetrics.ANALYTICAL_THINKING, 0) > 0.7:
                benefits.append("深度技術分析")
                
        elif tier == ServiceTier.ENTERPRISE:
            benefits.extend([
                "企業級API接入",
                "大量數據處理",
                "多用戶協作",
                "定制化儀表板",
                "專屬客戶經理"
            ])
            
        elif tier == ServiceTier.CUSTOM:
            benefits.extend([
                "完全定制化解決方案",
                "專屬開發團隊",
                "無限API調用",
                "24/7技術支持",
                "私有雲部署選項"
            ])
        
        return benefits
    
    async def _set_implementation_guidance(self, recommendation: TierRecommendation,
                                         user_behavior: UserBehaviorModel,
                                         user_preferences: PreferenceProfile):
        """設置實施指導"""
        # 基於學習能力設置時間線
        learning_rate = user_behavior.personality_scores.get(PersonalityMetrics.LEARNING_RATE, 0.5)
        if learning_rate > 0.7:
            recommendation.implementation_timeline = "1-2週內完成升級和適應"
        elif learning_rate > 0.4:
            recommendation.implementation_timeline = "2-4週內逐步升級"
        else:
            recommendation.implementation_timeline = "4-8週內穩步升級"
        
        # 設置前置條件
        if recommendation.recommended_tier in [ServiceTier.ENTERPRISE, ServiceTier.CUSTOM]:
            recommendation.prerequisites.extend([
                "完成高級功能培訓",
                "建立數據管理流程",
                "配置安全設置"
            ])
        
        # 設置成功指標
        recommendation.success_metrics.extend([
            "價值實現率提升30%",
            "任務完成效率提升25%",
            "用戶滿意度達到4.5以上"
        ])
        
        # 風險評估
        if recommendation.roi_projection < 200:
            recommendation.risks.append("投資回報率相對較低")
            recommendation.risk_mitigation.append("分階段實施以降低風險")
        
        if user_preferences.complexity_tolerance < 0.5:
            recommendation.risks.append("功能複雜度可能帶來學習負擔")
            recommendation.risk_mitigation.append("提供額外的培訓和支持")
    
    async def _generate_feature_recommendations(self, user_id: str,
                                              user_behavior: UserBehaviorModel,
                                              user_preferences: PreferenceProfile,
                                              current_services: List[ValueService]) -> List[TierRecommendation]:
        """生成功能推薦"""
        # 簡化版功能推薦邏輯
        recommendations = []
        
        # 基於行為模式推薦功能
        for pattern in user_behavior.behavior_patterns:
            if pattern == BehaviorPattern.DAY_TRADER:
                feature_rec = TierRecommendation(
                    user_id=user_id,
                    recommendation_type=RecommendationType.FEATURE_ACTIVATION,
                    rationale="基於您的日內交易模式，建議激活實時交易功能",
                    key_benefits=["實時價格追蹤", "快速執行交易", "風險監控"],
                    expected_value_increase=1000,
                    investment_required=300,
                    roi_projection=333
                )
                recommendations.append(feature_rec)
        
        return recommendations
    
    async def _generate_optimization_recommendations(self, user_id: str,
                                                   utilization_metrics: UtilizationMetrics,
                                                   user_behavior: UserBehaviorModel) -> List[TierRecommendation]:
        """生成優化推薦"""
        recommendations = []
        
        # 基於使用效率生成優化建議
        if utilization_metrics.value_realization_rate < 0.6:
            optimization_rec = TierRecommendation(
                user_id=user_id,
                recommendation_type=RecommendationType.USAGE_OPTIMIZATION,
                rationale="價值實現率偏低，建議優化使用方式",
                key_benefits=["提升價值實現率", "改善投資回報", "優化使用體驗"],
                expected_value_increase=utilization_metrics.expected_value * 0.3,
                implementation_timeline="2-3週內完成優化"
            )
            recommendations.append(optimization_rec)
        
        return recommendations

class ServiceTierSystem:
    """服務分層系統"""
    
    def __init__(self):
        self.tier_matcher = TierMatcher()
        self.recommendation_engine = PersonalizedRecommendationEngine()
        self.utilization_analyzer = ServiceUtilizationAnalyzer()
        self.user_portfolios: Dict[str, ServicePortfolio] = {}
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("ServiceTierSystem initialized")
    
    async def create_personalized_service_portfolio(self, user_id: str,
                                                  user_behavior: UserBehaviorModel,
                                                  user_preferences: PreferenceProfile,
                                                  current_services: List[ValueService] = None,
                                                  usage_data: List[Dict[str, Any]] = None) -> ServicePortfolio:
        """創建個人化服務組合"""
        try:
            # 分析服務使用效益
            utilization_metrics = None
            if usage_data:
                utilization_metrics = await self.utilization_analyzer.analyze_service_utilization(
                    user_id, "portfolio", usage_data, user_behavior
                )
            
            # 生成個人化推薦
            recommendations = await self.recommendation_engine.generate_personalized_recommendations(
                user_id, user_behavior, user_preferences, current_services or [], utilization_metrics
            )
            
            # 創建服務組合
            portfolio = ServicePortfolio(
                user_id=user_id,
                active_services=current_services or [],
                upgrade_recommendations=recommendations
            )
            
            # 計算組合指標
            await self._calculate_portfolio_metrics(portfolio, utilization_metrics)
            
            # 識別優化機會
            portfolio.optimization_opportunities = await self._identify_optimization_opportunities(
                portfolio, user_behavior, user_preferences
            )
            
            # 緩存組合
            self.user_portfolios[user_id] = portfolio
            
            self.logger.info(f"Created personalized service portfolio for user {user_id}")
            return portfolio
            
        except Exception as e:
            self.logger.error(f"Service portfolio creation failed: {e}")
            raise
    
    async def _calculate_portfolio_metrics(self, portfolio: ServicePortfolio,
                                         utilization_metrics: Optional[UtilizationMetrics]):
        """計算組合指標"""
        # 計算總價值和成本
        portfolio.total_value = sum(service.monthly_recurring_revenue for service in portfolio.active_services)
        portfolio.total_cost = portfolio.total_value * 0.3  # 假設成本為收入的30%
        
        # 計算ROI
        if portfolio.total_cost > 0:
            portfolio.portfolio_roi = (portfolio.total_value - portfolio.total_cost) / portfolio.total_cost * 100
        
        # 設置個人化指標
        if utilization_metrics:
            portfolio.value_realization_rate = utilization_metrics.value_realization_rate
            portfolio.usage_efficiency = utilization_metrics.task_completion_rate
        
        # 計算個人化分數（基於推薦匹配度）
        if portfolio.upgrade_recommendations:
            alignment_scores = [rec.alignment_score for rec in portfolio.upgrade_recommendations]
            portfolio.personalization_score = np.mean(alignment_scores)
        else:
            portfolio.personalization_score = 0.7  # 默認分數
    
    async def _identify_optimization_opportunities(self, portfolio: ServicePortfolio,
                                                 user_behavior: UserBehaviorModel,
                                                 user_preferences: PreferenceProfile) -> List[Dict[str, Any]]:
        """識別優化機會"""
        opportunities = []
        
        # 服務重疊檢查
        if len(portfolio.active_services) > 1:
            # 簡化的重疊檢查邏輯
            tier_counts = defaultdict(int)
            for service in portfolio.active_services:
                tier_counts[service.tier] += 1
            
            if tier_counts[ServiceTier.BASIC] > 1:
                opportunities.append({
                    'type': 'service_consolidation',
                    'description': '多個基礎服務可以整合為單一高級服務',
                    'potential_savings': 500,
                    'priority': 'medium'
                })
        
        # 使用不足檢查
        if portfolio.usage_efficiency < 0.6:
            opportunities.append({
                'type': 'usage_improvement',
                'description': '服務使用效率偏低，需要優化使用方式',
                'potential_value_increase': portfolio.total_value * 0.2,
                'priority': 'high'
            })
        
        # 升級機會
        if portfolio.personalization_score > 0.8 and portfolio.portfolio_roi > 300:
            opportunities.append({
                'type': 'tier_upgrade',
                'description': '高個人化匹配度和ROI，適合升級到更高層級',
                'potential_value_increase': portfolio.total_value * 0.5,
                'priority': 'high'
            })
        
        return opportunities
    
    def get_tier_system_analytics(self) -> Dict[str, Any]:
        """獲取分層系統分析"""
        if not self.user_portfolios:
            return {"message": "No portfolio data available"}
        
        analytics = {
            'total_users': len(self.user_portfolios),
            'tier_distribution': defaultdict(int),
            'average_portfolio_value': 0.0,
            'average_personalization_score': 0.0,
            'recommendation_types': defaultdict(int),
            'upgrade_conversion_potential': 0
        }
        
        total_value = 0
        total_personalization = 0
        
        for portfolio in self.user_portfolios.values():
            # 統計層級分布
            for service in portfolio.active_services:
                analytics['tier_distribution'][service.tier.value] += 1
            
            # 累計指標
            total_value += portfolio.total_value
            total_personalization += portfolio.personalization_score
            
            # 統計推薦類型
            for rec in portfolio.upgrade_recommendations:
                analytics['recommendation_types'][rec.recommendation_type.value] += 1
                if rec.roi_projection > 200:
                    analytics['upgrade_conversion_potential'] += 1
        
        # 計算平均值
        user_count = len(self.user_portfolios)
        analytics['average_portfolio_value'] = total_value / user_count
        analytics['average_personalization_score'] = total_personalization / user_count
        
        return analytics

# 工廠函數
def create_service_tier_system() -> ServiceTierSystem:
    """創建服務分層系統"""
    return ServiceTierSystem()

def create_tier_recommendation(user_id: str, **kwargs) -> TierRecommendation:
    """創建層級推薦"""
    return TierRecommendation(user_id=user_id, **kwargs)

def create_service_portfolio(user_id: str, **kwargs) -> ServicePortfolio:
    """創建服務組合"""
    return ServicePortfolio(user_id=user_id, **kwargs)