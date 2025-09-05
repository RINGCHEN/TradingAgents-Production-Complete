#!/usr/bin/env python3
"""
Revenue Tracker
收益追蹤器

GPT-OSS整合任務2.1.3 - 新功能收益追蹤和歸因系統
提供完整的GPT-OSS驅動功能收益追蹤和會員升級歸因功能
"""

import asyncio
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging
from uuid import UUID, uuid4

from .models import (
    NewFeatureRevenue, NewFeatureRevenueSchema,
    MembershipUpgradeAttribution, MembershipUpgradeAttributionSchema,
    RevenueAttributionRecord, RevenueAttributionRecordSchema,
    RevenueType, AttributionMethod, RevenueConfidence
)

logger = logging.getLogger(__name__)


# ==================== 配置和數據結構 ====================

class FeatureCategory(str, Enum):
    """功能類別"""
    AI_ANALYSIS = "ai_analysis"
    PREDICTION_MODEL = "prediction_model"
    AUTOMATED_TRADING = "automated_trading"
    RISK_MANAGEMENT = "risk_management"
    MARKET_INSIGHTS = "market_insights"
    PERSONALIZATION = "personalization"
    PREMIUM_ALERTS = "premium_alerts"


class MembershipTier(str, Enum):
    """會員等級"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    DIAMOND = "diamond"
    ENTERPRISE = "enterprise"


@dataclass
class FeatureUsageMetrics:
    """功能使用指標"""
    feature_id: str
    feature_name: str
    total_users: int
    active_users: int
    usage_frequency: Decimal  # 平均使用頻率
    engagement_score: Decimal  # 參與度分數
    satisfaction_rating: Decimal  # 滿意度評分
    retention_impact: Decimal  # 留存影響
    

@dataclass
class RevenueImpactModel:
    """收益影響模型"""
    feature_id: str
    direct_revenue_factor: Decimal  # 直接收益係數
    indirect_revenue_factor: Decimal  # 間接收益係數
    conversion_rate_impact: Decimal  # 轉換率影響
    retention_rate_impact: Decimal  # 留存率影響
    pricing_power_impact: Decimal  # 定價能力影響


class NewFeatureRevenueTracker:
    """新功能收益追蹤器"""
    
    def __init__(self):
        """初始化收益追蹤器"""
        self.feature_revenue_models = self._initialize_revenue_models()
        self.baseline_metrics = {}
        
    def _initialize_revenue_models(self) -> Dict[str, RevenueImpactModel]:
        """初始化收益影響模型"""
        return {
            "gpt_oss_market_analysis": RevenueImpactModel(
                feature_id="gpt_oss_market_analysis",
                direct_revenue_factor=Decimal('0.15'),
                indirect_revenue_factor=Decimal('0.08'),
                conversion_rate_impact=Decimal('0.12'),
                retention_rate_impact=Decimal('0.18'),
                pricing_power_impact=Decimal('0.10')
            ),
            "ai_risk_assessment": RevenueImpactModel(
                feature_id="ai_risk_assessment",
                direct_revenue_factor=Decimal('0.20'),
                indirect_revenue_factor=Decimal('0.10'),
                conversion_rate_impact=Decimal('0.15'),
                retention_rate_impact=Decimal('0.22'),
                pricing_power_impact=Decimal('0.12')
            ),
            "personalized_insights": RevenueImpactModel(
                feature_id="personalized_insights",
                direct_revenue_factor=Decimal('0.25'),
                indirect_revenue_factor=Decimal('0.12'),
                conversion_rate_impact=Decimal('0.18'),
                retention_rate_impact=Decimal('0.25'),
                pricing_power_impact=Decimal('0.15')
            ),
            "automated_alerts": RevenueImpactModel(
                feature_id="automated_alerts",
                direct_revenue_factor=Decimal('0.10'),
                indirect_revenue_factor=Decimal('0.06'),
                conversion_rate_impact=Decimal('0.08'),
                retention_rate_impact=Decimal('0.14'),
                pricing_power_impact=Decimal('0.07')
            )
        }
    
    async def track_new_feature_revenue(
        self,
        feature_id: str,
        feature_name: str,
        feature_category: FeatureCategory,
        launch_date: date,
        gpt_oss_dependency_level: str,
        usage_metrics: FeatureUsageMetrics,
        revenue_data: Dict[str, Decimal],
        measurement_period_start: date,
        measurement_period_end: date,
        tracking_methodology: str = "comprehensive_attribution_v1.0"
    ) -> NewFeatureRevenueSchema:
        """
        追蹤新功能收益
        
        Args:
            feature_id: 功能ID
            feature_name: 功能名稱
            feature_category: 功能類別
            launch_date: 上線日期
            gpt_oss_dependency_level: GPT-OSS依賴程度
            usage_metrics: 使用指標
            revenue_data: 收益數據
            measurement_period_start: 測量期間開始
            measurement_period_end: 測量期間結束
            tracking_methodology: 追蹤方法
            
        Returns:
            新功能收益記錄
        """
        try:
            # 計算各類收益
            revenue_breakdown = await self._calculate_feature_revenue_breakdown(
                feature_id, usage_metrics, revenue_data
            )
            
            # 計算用戶採用指標
            adoption_metrics = await self._calculate_adoption_metrics(usage_metrics)
            
            # 評估GPT-OSS貢獻
            gpt_oss_contribution = await self._assess_gpt_oss_contribution(
                feature_id, gpt_oss_dependency_level, usage_metrics
            )
            
            # 創建收益記錄
            feature_revenue = NewFeatureRevenueSchema(
                feature_name=feature_name,
                feature_category=feature_category.value,
                launch_date=launch_date,
                gpt_oss_dependency_level=gpt_oss_dependency_level,
                
                # 收益分解
                direct_revenue=revenue_breakdown['direct_revenue'],
                indirect_revenue=revenue_breakdown['indirect_revenue'],
                recurring_revenue=revenue_breakdown['recurring_revenue'],
                one_time_revenue=revenue_breakdown['one_time_revenue'],
                
                # 用戶採用指標
                total_users_engaged=adoption_metrics['total_users_engaged'],
                paid_conversions=adoption_metrics['paid_conversions'],
                conversion_rate=adoption_metrics['conversion_rate'],
                average_revenue_per_user=adoption_metrics['average_revenue_per_user'],
                
                # GPT-OSS貢獻
                performance_without_gpt_oss=gpt_oss_contribution['performance_without_gpt_oss'],
                unique_capabilities_enabled=gpt_oss_contribution['unique_capabilities_enabled'],
                cost_efficiency_gained=gpt_oss_contribution['cost_efficiency_gained'],
                
                # 測量期間
                measurement_period_start=measurement_period_start,
                measurement_period_end=measurement_period_end,
                
                # 方法和數據來源
                tracking_methodology=tracking_methodology,
                data_sources=[
                    "user_analytics", "payment_gateway", "feature_usage_logs", 
                    "customer_feedback", "a_b_testing_results"
                ],
                validation_notes=f"基於 {usage_metrics.total_users} 用戶數據的綜合分析"
            )
            
            logger.info(f"新功能收益追蹤完成: {feature_name} - 總收益 ${revenue_breakdown['total_revenue']:.2f}")
            return feature_revenue
            
        except Exception as e:
            logger.error(f"追蹤新功能收益失敗 {feature_name}: {e}")
            raise
    
    async def _calculate_feature_revenue_breakdown(
        self,
        feature_id: str,
        usage_metrics: FeatureUsageMetrics,
        revenue_data: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """計算功能收益分解"""
        # 獲取收益影響模型
        revenue_model = self.feature_revenue_models.get(feature_id)
        if not revenue_model:
            # 使用預設模型
            revenue_model = RevenueImpactModel(
                feature_id=feature_id,
                direct_revenue_factor=Decimal('0.12'),
                indirect_revenue_factor=Decimal('0.08'),
                conversion_rate_impact=Decimal('0.10'),
                retention_rate_impact=Decimal('0.15'),
                pricing_power_impact=Decimal('0.08')
            )
        
        # 從輸入數據中提取基礎收益
        base_revenue = revenue_data.get('total_feature_revenue', Decimal('0'))
        subscription_revenue = revenue_data.get('subscription_revenue', Decimal('0'))
        transaction_revenue = revenue_data.get('transaction_revenue', Decimal('0'))
        
        # 計算直接收益
        direct_revenue = base_revenue * revenue_model.direct_revenue_factor
        
        # 計算間接收益（通過提高整體平台價值）
        indirect_revenue = base_revenue * revenue_model.indirect_revenue_factor
        
        # 計算經常性收益和一次性收益
        recurring_revenue = subscription_revenue + (direct_revenue * Decimal('0.7'))
        one_time_revenue = transaction_revenue + (direct_revenue * Decimal('0.3'))
        
        total_revenue = direct_revenue + indirect_revenue
        
        return {
            'direct_revenue': direct_revenue,
            'indirect_revenue': indirect_revenue,
            'recurring_revenue': recurring_revenue,
            'one_time_revenue': one_time_revenue,
            'total_revenue': total_revenue
        }
    
    async def _calculate_adoption_metrics(
        self,
        usage_metrics: FeatureUsageMetrics
    ) -> Dict[str, Any]:
        """計算用戶採用指標"""
        # 基於使用指標計算採用率
        engagement_factor = usage_metrics.engagement_score / Decimal('100')
        satisfaction_factor = usage_metrics.satisfaction_rating / Decimal('10')
        
        # 估算付費轉換
        conversion_rate = engagement_factor * satisfaction_factor * Decimal('0.15')  # 基礎轉換率
        paid_conversions = int(usage_metrics.active_users * float(conversion_rate))
        
        # 計算ARPU
        if paid_conversions > 0:
            # 基於滿意度和參與度估算ARPU
            base_arpu = Decimal('50.0')  # 基礎ARPU
            arpu_multiplier = (satisfaction_factor + engagement_factor) / 2
            average_revenue_per_user = base_arpu * arpu_multiplier
        else:
            average_revenue_per_user = Decimal('0')
        
        return {
            'total_users_engaged': usage_metrics.total_users,
            'paid_conversions': paid_conversions,
            'conversion_rate': conversion_rate * 100,  # 轉為百分比
            'average_revenue_per_user': average_revenue_per_user
        }
    
    async def _assess_gpt_oss_contribution(
        self,
        feature_id: str,
        dependency_level: str,
        usage_metrics: FeatureUsageMetrics
    ) -> Dict[str, Any]:
        """評估GPT-OSS貢獻"""
        # 依賴程度影響係數
        dependency_factors = {
            'high': Decimal('0.85'),    # 高度依賴，沒有GPT-OSS功能無法實現
            'medium': Decimal('0.65'),  # 中等依賴，沒有GPT-OSS功能顯著下降
            'low': Decimal('0.35')      # 低依賴，GPT-OSS提供增強但非必需
        }
        
        dependency_factor = dependency_factors.get(dependency_level, Decimal('0.50'))
        
        # 估算沒有GPT-OSS的性能
        performance_without_gpt_oss = (Decimal('100') - (dependency_factor * 100)).quantize(Decimal('0.1'))
        
        # 識別獨特能力
        unique_capabilities = []
        if dependency_level == 'high':
            unique_capabilities = [
                "本地化智能分析", "即時風險評估", "個性化投資建議", "多語言市場分析"
            ]
        elif dependency_level == 'medium':
            unique_capabilities = [
                "增強預測準確性", "智能化風險控制", "自動化報告生成"
            ]
        else:
            unique_capabilities = [
                "輔助決策支持", "基礎智能化功能"
            ]
        
        # 計算成本效率提升
        # 基於使用頻率和參與度評估效率提升
        efficiency_base = usage_metrics.usage_frequency * usage_metrics.engagement_score / 1000
        cost_efficiency_gained = efficiency_base * dependency_factor
        
        return {
            'performance_without_gpt_oss': performance_without_gpt_oss,
            'unique_capabilities_enabled': unique_capabilities,
            'cost_efficiency_gained': cost_efficiency_gained
        }
    
    async def analyze_feature_portfolio_performance(
        self,
        feature_revenues: List[NewFeatureRevenueSchema],
        analysis_period_months: int = 6
    ) -> Dict[str, Any]:
        """分析功能組合表現"""
        if not feature_revenues:
            return {'error': '沒有功能收益數據用於分析'}
        
        # 計算總體指標
        total_direct_revenue = sum(f.direct_revenue for f in feature_revenues)
        total_indirect_revenue = sum(f.indirect_revenue for f in feature_revenues)
        total_users = sum(f.total_users_engaged for f in feature_revenues)
        total_conversions = sum(f.paid_conversions for f in feature_revenues)
        
        # 計算平均指標
        avg_conversion_rate = sum(f.conversion_rate for f in feature_revenues) / len(feature_revenues)
        avg_arpu = sum(f.average_revenue_per_user for f in feature_revenues) / len(feature_revenues)
        
        # 識別表現最佳的功能
        sorted_features = sorted(
            feature_revenues, 
            key=lambda f: f.direct_revenue + f.indirect_revenue, 
            reverse=True
        )
        
        top_performers = sorted_features[:3] if len(sorted_features) >= 3 else sorted_features
        
        # 分析GPT-OSS依賴影響
        dependency_analysis = {}
        for feature in feature_revenues:
            level = feature.gpt_oss_dependency_level
            if level not in dependency_analysis:
                dependency_analysis[level] = {
                    'count': 0,
                    'total_revenue': Decimal('0'),
                    'total_users': 0,
                    'avg_conversion_rate': Decimal('0')
                }
            
            dependency_analysis[level]['count'] += 1
            dependency_analysis[level]['total_revenue'] += (feature.direct_revenue + feature.indirect_revenue)
            dependency_analysis[level]['total_users'] += feature.total_users_engaged
            dependency_analysis[level]['avg_conversion_rate'] += feature.conversion_rate
        
        # 計算平均值
        for level_data in dependency_analysis.values():
            if level_data['count'] > 0:
                level_data['avg_conversion_rate'] /= level_data['count']
                level_data['avg_revenue_per_feature'] = level_data['total_revenue'] / level_data['count']
        
        return {
            'analysis_period_months': analysis_period_months,
            'portfolio_overview': {
                'total_features': len(feature_revenues),
                'total_direct_revenue': total_direct_revenue,
                'total_indirect_revenue': total_indirect_revenue,
                'total_revenue': total_direct_revenue + total_indirect_revenue,
                'total_users_engaged': total_users,
                'total_paid_conversions': total_conversions,
                'overall_conversion_rate': avg_conversion_rate,
                'average_arpu': avg_arpu
            },
            'top_performing_features': [
                {
                    'feature_name': f.feature_name,
                    'total_revenue': f.direct_revenue + f.indirect_revenue,
                    'conversion_rate': f.conversion_rate,
                    'users_engaged': f.total_users_engaged,
                    'gpt_oss_dependency': f.gpt_oss_dependency_level
                }
                for f in top_performers
            ],
            'gpt_oss_dependency_analysis': dependency_analysis,
            'revenue_insights': [
                f"高依賴GPT-OSS功能平均收益比低依賴功能高 {(dependency_analysis.get('high', {}).get('avg_revenue_per_feature', Decimal('0')) / dependency_analysis.get('low', {}).get('avg_revenue_per_feature', Decimal('1')) * 100 - 100):.1f}%" if 'high' in dependency_analysis and 'low' in dependency_analysis else "需要更多數據進行比較分析",
                f"總計 {len([f for f in feature_revenues if f.gpt_oss_dependency_level == 'high'])} 個高依賴功能貢獻了 {sum(f.direct_revenue + f.indirect_revenue for f in feature_revenues if f.gpt_oss_dependency_level == 'high'):.2f} 美元收益",
                f"平均功能轉換率為 {avg_conversion_rate:.2f}%，ARPU為 ${avg_arpu:.2f}"
            ],
            'analysis_timestamp': datetime.now(timezone.utc)
        }


class MembershipUpgradeAttributor:
    """會員升級歸因器"""
    
    def __init__(self):
        """初始化歸因器"""
        self.tier_values = self._initialize_tier_values()
        self.attribution_models = self._initialize_attribution_models()
    
    def _initialize_tier_values(self) -> Dict[str, Dict[str, Decimal]]:
        """初始化會員等級價值"""
        return {
            'free_to_basic': {
                'upgrade_revenue': Decimal('29.99'),
                'annual_value': Decimal('359.88'),
                'retention_probability': Decimal('0.75')
            },
            'basic_to_premium': {
                'upgrade_revenue': Decimal('49.99'),
                'annual_value': Decimal('599.88'),
                'retention_probability': Decimal('0.82')
            },
            'premium_to_diamond': {
                'upgrade_revenue': Decimal('99.99'),
                'annual_value': Decimal('1199.88'),
                'retention_probability': Decimal('0.88')
            },
            'any_to_enterprise': {
                'upgrade_revenue': Decimal('299.99'),
                'annual_value': Decimal('3599.88'),
                'retention_probability': Decimal('0.92')
            }
        }
    
    def _initialize_attribution_models(self) -> Dict[str, Dict[str, Decimal]]:
        """初始化歸因模型"""
        return {
            'direct_feature_trigger': {
                'direct_influence_weight': Decimal('0.80'),
                'indirect_influence_weight': Decimal('0.15'),
                'competitive_advantage_weight': Decimal('0.05')
            },
            'gradual_engagement': {
                'direct_influence_weight': Decimal('0.60'),
                'indirect_influence_weight': Decimal('0.30'),
                'competitive_advantage_weight': Decimal('0.10')
            },
            'competitive_response': {
                'direct_influence_weight': Decimal('0.40'),
                'indirect_influence_weight': Decimal('0.25'),
                'competitive_advantage_weight': Decimal('0.35')
            }
        }
    
    async def attribute_membership_upgrade(
        self,
        user_id: str,
        from_tier: MembershipTier,
        to_tier: MembershipTier,
        upgrade_date: datetime,
        gpt_oss_features_used: List[str],
        usage_history: Dict[str, Any],
        attribution_algorithm: str = "comprehensive_v1.0"
    ) -> MembershipUpgradeAttributionSchema:
        """
        會員升級歸因分析
        
        Args:
            user_id: 用戶ID
            from_tier: 原會員等級
            to_tier: 新會員等級
            upgrade_date: 升級日期
            gpt_oss_features_used: 使用的GPT-OSS功能列表
            usage_history: 使用歷史數據
            attribution_algorithm: 歸因算法
            
        Returns:
            會員升級歸因記錄
        """
        try:
            # 獲取升級價值信息
            upgrade_key = f"{from_tier.value}_to_{to_tier.value}"
            tier_info = self.tier_values.get(upgrade_key) or self.tier_values.get('any_to_enterprise')
            
            # 分析使用頻率
            usage_analysis = await self._analyze_usage_patterns(usage_history, upgrade_date)
            
            # 識別關鍵觸發功能
            trigger_features = await self._identify_trigger_features(
                gpt_oss_features_used, usage_history, upgrade_date
            )
            
            # 計算歸因權重
            attribution_scores = await self._calculate_attribution_scores(
                gpt_oss_features_used, usage_analysis, trigger_features, attribution_algorithm
            )
            
            # 執行觸點分析
            touchpoint_analysis = await self._perform_touchpoint_analysis(
                user_id, usage_history, gpt_oss_features_used, upgrade_date
            )
            
            # 執行行為分析
            behavioral_analysis = await self._perform_behavioral_analysis(
                usage_history, upgrade_date
            )
            
            # 創建歸因記錄
            upgrade_attribution = MembershipUpgradeAttributionSchema(
                user_id=user_id,
                from_tier=from_tier.value,
                to_tier=to_tier.value,
                upgrade_date=upgrade_date,
                
                # 收益信息
                upgrade_revenue=tier_info['upgrade_revenue'],
                projected_annual_value=tier_info['annual_value'],
                retention_probability=tier_info['retention_probability'],
                
                # GPT-OSS歸因分析
                gpt_oss_features_used=gpt_oss_features_used,
                usage_frequency_before_upgrade=usage_analysis['usage_frequency_before_upgrade'],
                key_trigger_features=trigger_features,
                
                # 歸因權重
                direct_influence_score=attribution_scores['direct_influence_score'],
                indirect_influence_score=attribution_scores['indirect_influence_score'],
                competitive_advantage_score=attribution_scores['competitive_advantage_score'],
                
                # 分析方法
                attribution_algorithm=attribution_algorithm,
                touchpoint_analysis=touchpoint_analysis,
                behavioral_analysis=behavioral_analysis,
                
                # 元數據
                analysis_date=datetime.now(timezone.utc),
                analyst_notes=f"基於 {len(gpt_oss_features_used)} 個GPT-OSS功能的綜合歸因分析",
                confidence_factors={
                    'data_completeness': float(min(usage_analysis.get('data_quality_score', Decimal('0.8')), Decimal('1.0'))),
                    'temporal_proximity': float(usage_analysis.get('temporal_proximity_score', Decimal('0.9'))),
                    'feature_relevance': float(len(trigger_features) / max(len(gpt_oss_features_used), 1))
                }
            )
            
            logger.info(f"會員升級歸因完成: {user_id} {from_tier.value}→{to_tier.value}")
            return upgrade_attribution
            
        except Exception as e:
            logger.error(f"會員升級歸因失敗 {user_id}: {e}")
            raise
    
    async def _analyze_usage_patterns(
        self,
        usage_history: Dict[str, Any],
        upgrade_date: datetime
    ) -> Dict[str, Any]:
        """分析使用模式"""
        # 計算升級前使用頻率
        pre_upgrade_days = 30  # 分析升級前30天
        upgrade_date_only = upgrade_date.date()
        analysis_start = upgrade_date_only - timedelta(days=pre_upgrade_days)
        
        # 從使用歷史中提取相關數據
        usage_events = usage_history.get('events', [])
        relevant_events = [
            event for event in usage_events
            if analysis_start <= datetime.fromisoformat(event['timestamp']).date() <= upgrade_date_only
        ]
        
        # 計算使用頻率
        usage_days = len(set(
            datetime.fromisoformat(event['timestamp']).date()
            for event in relevant_events
        ))
        
        # 計算數據品質分數
        expected_data_points = pre_upgrade_days * 2  # 預期每天至少2個數據點
        actual_data_points = len(relevant_events)
        data_quality_score = min(Decimal(str(actual_data_points / expected_data_points)), Decimal('1.0'))
        
        # 計算時間接近度分數
        if relevant_events:
            last_usage = max(datetime.fromisoformat(event['timestamp']) for event in relevant_events)
            days_to_upgrade = (upgrade_date - last_usage).days
            temporal_proximity_score = max(Decimal('0.1'), Decimal('1.0') - Decimal(str(days_to_upgrade / 30)))
        else:
            temporal_proximity_score = Decimal('0.1')
        
        return {
            'usage_frequency_before_upgrade': usage_days,
            'total_events': len(relevant_events),
            'data_quality_score': data_quality_score,
            'temporal_proximity_score': temporal_proximity_score,
            'analysis_period_days': pre_upgrade_days
        }
    
    async def _identify_trigger_features(
        self,
        gpt_oss_features_used: List[str],
        usage_history: Dict[str, Any],
        upgrade_date: datetime
    ) -> List[str]:
        """識別關鍵觸發功能"""
        # 分析升級前最後7天的功能使用
        trigger_window_days = 7
        trigger_start = upgrade_date - timedelta(days=trigger_window_days)
        
        usage_events = usage_history.get('events', [])
        trigger_events = [
            event for event in usage_events
            if trigger_start <= datetime.fromisoformat(event['timestamp']) <= upgrade_date
            and event.get('feature_id') in gpt_oss_features_used
        ]
        
        # 計算每個功能在觸發窗口內的使用頻率
        feature_usage_count = {}
        for event in trigger_events:
            feature_id = event.get('feature_id')
            if feature_id:
                feature_usage_count[feature_id] = feature_usage_count.get(feature_id, 0) + 1
        
        # 識別高使用頻率的功能作為觸發器
        total_usage = sum(feature_usage_count.values())
        if total_usage == 0:
            return gpt_oss_features_used[:2]  # 如果沒有觸發窗口數據，返回前兩個功能
        
        # 選擇使用頻率超過平均值的功能
        avg_usage = total_usage / len(feature_usage_count) if feature_usage_count else 0
        trigger_features = [
            feature for feature, count in feature_usage_count.items()
            if count > avg_usage
        ]
        
        # 確保至少有一個觸發功能
        if not trigger_features and gpt_oss_features_used:
            trigger_features = [gpt_oss_features_used[0]]
        
        return trigger_features
    
    async def _calculate_attribution_scores(
        self,
        gpt_oss_features_used: List[str],
        usage_analysis: Dict[str, Any],
        trigger_features: List[str],
        algorithm: str
    ) -> Dict[str, Decimal]:
        """計算歸因分數"""
        # 確定歸因模型
        if len(trigger_features) > 0 and usage_analysis['temporal_proximity_score'] > Decimal('0.8'):
            model_type = 'direct_feature_trigger'
        elif usage_analysis['usage_frequency_before_upgrade'] > 15:
            model_type = 'gradual_engagement'
        else:
            model_type = 'competitive_response'
        
        attribution_weights = self.attribution_models[model_type]
        
        # 基於使用模式調整分數
        usage_factor = min(
            Decimal(str(usage_analysis['usage_frequency_before_upgrade'] / 30)), 
            Decimal('1.0')
        )
        trigger_factor = Decimal(str(len(trigger_features) / max(len(gpt_oss_features_used), 1)))
        data_quality_factor = usage_analysis['data_quality_score']
        
        # 計算最終分數
        base_direct = attribution_weights['direct_influence_weight'] * usage_factor * data_quality_factor
        base_indirect = attribution_weights['indirect_influence_weight'] * trigger_factor
        base_competitive = attribution_weights['competitive_advantage_weight'] * (usage_factor + trigger_factor) / 2
        
        # 確保分數總和合理
        total_score = base_direct + base_indirect + base_competitive
        if total_score > Decimal('1.0'):
            # 正規化分數
            base_direct /= total_score
            base_indirect /= total_score
            base_competitive /= total_score
        
        return {
            'direct_influence_score': (base_direct * 100).quantize(Decimal('0.1')),
            'indirect_influence_score': (base_indirect * 100).quantize(Decimal('0.1')),
            'competitive_advantage_score': (base_competitive * 100).quantize(Decimal('0.1'))
        }
    
    async def _perform_touchpoint_analysis(
        self,
        user_id: str,
        usage_history: Dict[str, Any],
        gpt_oss_features: List[str],
        upgrade_date: datetime
    ) -> Dict[str, Any]:
        """執行觸點分析"""
        # 分析用戶與GPT-OSS功能的所有觸點
        usage_events = usage_history.get('events', [])
        gpt_oss_events = [
            event for event in usage_events
            if event.get('feature_id') in gpt_oss_features
        ]
        
        # 按時間排序事件
        sorted_events = sorted(
            gpt_oss_events, 
            key=lambda x: datetime.fromisoformat(x['timestamp'])
        )
        
        # 識別關鍵觸點時刻
        first_touch = sorted_events[0] if sorted_events else None
        last_touch = sorted_events[-1] if sorted_events else None
        
        # 計算觸點間隔
        if first_touch and last_touch:
            journey_duration = (
                datetime.fromisoformat(last_touch['timestamp']) - 
                datetime.fromisoformat(first_touch['timestamp'])
            ).days
        else:
            journey_duration = 0
        
        # 分析觸點密度
        if sorted_events:
            unique_dates = len(set(
                datetime.fromisoformat(event['timestamp']).date() 
                for event in sorted_events
            ))
            touchpoint_density = len(sorted_events) / max(unique_dates, 1)
        else:
            touchpoint_density = 0
        
        return {
            'total_touchpoints': len(sorted_events),
            'unique_feature_touchpoints': len(set(event.get('feature_id') for event in sorted_events)),
            'customer_journey_duration_days': journey_duration,
            'touchpoint_density': touchpoint_density,
            'first_touch_feature': first_touch.get('feature_id') if first_touch else None,
            'last_touch_feature': last_touch.get('feature_id') if last_touch else None,
            'engagement_consistency': 'high' if touchpoint_density > 2 else 'medium' if touchpoint_density > 1 else 'low'
        }
    
    async def _perform_behavioral_analysis(
        self,
        usage_history: Dict[str, Any],
        upgrade_date: datetime
    ) -> Dict[str, Any]:
        """執行行為分析"""
        usage_events = usage_history.get('events', [])
        
        # 分析使用模式趨勢
        pre_upgrade_30d = upgrade_date - timedelta(days=30)
        pre_upgrade_7d = upgrade_date - timedelta(days=7)
        
        events_30d = [
            event for event in usage_events
            if pre_upgrade_30d <= datetime.fromisoformat(event['timestamp']) <= upgrade_date
        ]
        
        events_7d = [
            event for event in usage_events
            if pre_upgrade_7d <= datetime.fromisoformat(event['timestamp']) <= upgrade_date
        ]
        
        # 計算使用強度變化
        intensity_30d = len(events_30d) / 30 if events_30d else 0
        intensity_7d = len(events_7d) / 7 if events_7d else 0
        
        intensity_trend = "increasing" if intensity_7d > intensity_30d else "decreasing" if intensity_7d < intensity_30d else "stable"
        
        # 分析功能探索行為
        unique_features_30d = len(set(event.get('feature_id') for event in events_30d if event.get('feature_id')))
        unique_features_7d = len(set(event.get('feature_id') for event in events_7d if event.get('feature_id')))
        
        exploration_behavior = "active" if unique_features_7d >= unique_features_30d * 0.7 else "focused"
        
        # 計算參與深度
        if events_30d:
            avg_session_length = sum(
                event.get('duration_minutes', 5) for event in events_30d
            ) / len(events_30d)
            engagement_depth = "deep" if avg_session_length > 10 else "medium" if avg_session_length > 5 else "shallow"
        else:
            avg_session_length = 0
            engagement_depth = "unknown"
        
        return {
            'usage_intensity_trend': intensity_trend,
            'intensity_30d': intensity_30d,
            'intensity_7d': intensity_7d,
            'feature_exploration_behavior': exploration_behavior,
            'unique_features_explored_30d': unique_features_30d,
            'unique_features_explored_7d': unique_features_7d,
            'engagement_depth': engagement_depth,
            'average_session_length_minutes': avg_session_length,
            'behavioral_score': min(
                (intensity_7d + unique_features_7d + avg_session_length) / 3, 
                10.0
            )
        }
    
    async def analyze_upgrade_attribution_trends(
        self,
        attributions: List[MembershipUpgradeAttributionSchema],
        analysis_period_months: int = 6
    ) -> Dict[str, Any]:
        """分析升級歸因趨勢"""
        if not attributions:
            return {'error': '沒有升級歸因數據用於分析'}
        
        # 計算總體指標
        total_upgrades = len(attributions)
        total_upgrade_revenue = sum(attr.upgrade_revenue for attr in attributions)
        total_projected_annual_value = sum(attr.projected_annual_value for attr in attributions)
        
        # 分析歸因分數分布
        avg_direct_influence = sum(attr.direct_influence_score for attr in attributions) / total_upgrades
        avg_indirect_influence = sum(attr.indirect_influence_score for attr in attributions) / total_upgrades
        avg_competitive_advantage = sum(attr.competitive_advantage_score for attr in attributions) / total_upgrades
        
        # 分析最有效的觸發功能
        feature_trigger_count = {}
        for attr in attributions:
            for feature in attr.key_trigger_features:
                feature_trigger_count[feature] = feature_trigger_count.get(feature, 0) + 1
        
        top_trigger_features = sorted(
            feature_trigger_count.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        # 分析升級路徑
        upgrade_paths = {}
        for attr in attributions:
            path = f"{attr.from_tier}_to_{attr.to_tier}"
            if path not in upgrade_paths:
                upgrade_paths[path] = {
                    'count': 0,
                    'total_revenue': Decimal('0'),
                    'avg_direct_influence': Decimal('0')
                }
            upgrade_paths[path]['count'] += 1
            upgrade_paths[path]['total_revenue'] += attr.upgrade_revenue
            upgrade_paths[path]['avg_direct_influence'] += attr.direct_influence_score
        
        # 計算平均值
        for path_data in upgrade_paths.values():
            path_data['avg_direct_influence'] /= path_data['count']
            path_data['avg_revenue_per_upgrade'] = path_data['total_revenue'] / path_data['count']
        
        return {
            'analysis_period_months': analysis_period_months,
            'upgrade_overview': {
                'total_upgrades': total_upgrades,
                'total_upgrade_revenue': total_upgrade_revenue,
                'total_projected_annual_value': total_projected_annual_value,
                'average_upgrade_revenue': total_upgrade_revenue / total_upgrades,
                'average_projected_annual_value': total_projected_annual_value / total_upgrades
            },
            'attribution_analysis': {
                'average_direct_influence_score': avg_direct_influence,
                'average_indirect_influence_score': avg_indirect_influence,
                'average_competitive_advantage_score': avg_competitive_advantage,
                'gpt_oss_attribution_strength': (avg_direct_influence + avg_indirect_influence) / 2
            },
            'top_trigger_features': [
                {'feature': feature, 'trigger_count': count, 'conversion_influence': count / total_upgrades * 100}
                for feature, count in top_trigger_features
            ],
            'upgrade_path_analysis': upgrade_paths,
            'key_insights': [
                f"GPT-OSS功能平均直接影響升級決定 {avg_direct_influence:.1f}%",
                f"最有效觸發功能：{top_trigger_features[0][0]} (影響 {top_trigger_features[0][1]} 次升級)" if top_trigger_features else "需要更多數據識別觸發功能",
                f"最有價值升級路徑：{max(upgrade_paths.keys(), key=lambda k: upgrade_paths[k]['avg_revenue_per_upgrade'])} (平均收益 ${upgrade_paths[max(upgrade_paths.keys(), key=lambda k: upgrade_paths[k]['avg_revenue_per_upgrade'])]['avg_revenue_per_upgrade']:.2f})" if upgrade_paths else "需要更多升級數據"
            ],
            'analysis_timestamp': datetime.now(timezone.utc)
        }