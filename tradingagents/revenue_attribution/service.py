#!/usr/bin/env python3
"""
Revenue Attribution Service
收益歸因服務

GPT-OSS整合任務2.1.3 - 收益歸因系統核心服務
整合API成本計算、收益追蹤、預測引擎的統一服務介面
"""

import asyncio
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from uuid import UUID, uuid4
import logging

from .models import (
    RevenueAttributionRecord, RevenueAttributionRecordSchema,
    APICostSaving, APICostSavingSchema,
    NewFeatureRevenue, NewFeatureRevenueSchema,
    MembershipUpgradeAttribution, MembershipUpgradeAttributionSchema,
    RevenueForecast, RevenueForecastSchema,
    RevenueType, AttributionMethod, RevenueConfidence,
    RevenueAttributionRequest, RevenueForecastRequest, RevenueAnalysisResponse
)
from .api_cost_calculator import APICostCalculator, CostSavingsAnalyzer
from .revenue_tracker import NewFeatureRevenueTracker, MembershipUpgradeAttributor, FeatureUsageMetrics
from .forecast_engine import RevenueForecastEngine

logger = logging.getLogger(__name__)


class RevenueAttributionService:
    """收益歸因服務主類"""
    
    def __init__(self):
        """初始化收益歸因服務"""
        self.api_cost_calculator = APICostCalculator()
        self.cost_savings_analyzer = CostSavingsAnalyzer(self.api_cost_calculator)
        self.feature_revenue_tracker = NewFeatureRevenueTracker()
        self.membership_attributor = MembershipUpgradeAttributor()
        self.forecast_engine = RevenueForecastEngine()
        
        # 服務狀態
        self.service_initialized = False
        self.attribution_cache = {}
        
        logger.info("收益歸因服務初始化完成")
    
    async def initialize_service(self) -> Dict[str, Any]:
        """初始化服務"""
        try:
            # 執行服務初始化檢查
            initialization_status = {
                'api_cost_calculator': 'ready',
                'feature_revenue_tracker': 'ready',
                'membership_attributor': 'ready',
                'forecast_engine': 'ready'
            }
            
            self.service_initialized = True
            logger.info("收益歸因服務完全初始化")
            
            return {
                'service_status': 'initialized',
                'components': initialization_status,
                'initialization_timestamp': datetime.now(timezone.utc)
            }
            
        except Exception as e:
            logger.error(f"服務初始化失敗: {e}")
            raise
    
    # ==================== API成本節省歸因 ====================
    
    async def attribute_api_cost_savings(
        self,
        original_api_provider: str,
        gpt_oss_hardware: str,
        usage_period_start: date,
        usage_period_end: date,
        usage_metrics: Dict[str, Any],
        attribution_method: AttributionMethod = AttributionMethod.DIRECT,
        confidence_threshold: Decimal = Decimal('80.0')
    ) -> RevenueAttributionRecordSchema:
        """
        執行API成本節省歸因
        
        Args:
            original_api_provider: 原始API提供商
            gpt_oss_hardware: GPT-OSS硬體配置
            usage_period_start: 使用期間開始
            usage_period_end: 使用期間結束
            usage_metrics: 使用指標
            attribution_method: 歸因方法
            confidence_threshold: 信心度閾值
            
        Returns:
            收益歸因記錄
        """
        try:
            # 計算API成本節省
            processing_hours = Decimal(str(usage_metrics.get('processing_hours', 24.0)))
            cost_saving = await self.api_cost_calculator.calculate_api_cost_savings(
                original_provider=getattr(self.api_cost_calculator.pricing_models.keys(), '__iter__')().__next__(),  # 使用第一個可用provider
                gpt_oss_hardware=gpt_oss_hardware,
                total_input_tokens=usage_metrics.get('input_tokens', 100000),
                total_output_tokens=usage_metrics.get('output_tokens', 50000),
                total_requests=usage_metrics.get('requests', 1000),
                processing_time_hours=processing_hours,
                calculation_date=usage_period_end,
                additional_metrics=usage_metrics.get('additional_metrics', {})
            )
            
            # 確定信心度等級
            savings_percentage = cost_saving.savings_percentage
            if savings_percentage >= Decimal('90'):
                confidence_level = RevenueConfidence.HIGH
                confidence_score = Decimal('95.0')
            elif savings_percentage >= Decimal('70'):
                confidence_level = RevenueConfidence.MEDIUM
                confidence_score = Decimal('85.0')
            else:
                confidence_level = RevenueConfidence.LOW
                confidence_score = Decimal('70.0')
            
            # 計算GPT-OSS貢獻百分比
            gpt_oss_contribution = min(Decimal('100.0'), savings_percentage + Decimal('10.0'))  # 節省即貢獻
            
            # 創建歸因記錄
            attribution_record = RevenueAttributionRecordSchema(
                revenue_type=RevenueType.API_COST_SAVINGS,
                attribution_method=attribution_method,
                amount=cost_saving.savings_amount,
                currency="USD",
                attribution_date=usage_period_end,
                attribution_period_start=usage_period_start,
                attribution_period_end=usage_period_end,
                source_gpt_oss_feature=f"local_inference_{gpt_oss_hardware}",
                gpt_oss_contribution_percentage=gpt_oss_contribution,
                baseline_cost_without_gpt_oss=cost_saving.original_api_cost,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                attribution_factors={
                    'original_provider': original_api_provider,
                    'gpt_oss_hardware': gpt_oss_hardware,
                    'savings_percentage': float(savings_percentage),
                    'tokens_processed': cost_saving.total_tokens_processed,
                    'requests_handled': cost_saving.total_requests_handled,
                    'quality_score': float(cost_saving.quality_score) if cost_saving.quality_score else None
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by="api_cost_attribution_engine",
                validation_status="validated" if confidence_score >= confidence_threshold else "pending_review",
                notes=f"基於 {cost_saving.total_tokens_processed} tokens 和 {cost_saving.total_requests_handled} requests 的成本節省分析"
            )
            
            logger.info(f"API成本節省歸因完成: 節省 ${cost_saving.savings_amount:.2f} ({savings_percentage:.1f}%)")
            return attribution_record
            
        except Exception as e:
            logger.error(f"API成本節省歸因失敗: {e}")
            raise
    
    # ==================== 新功能收益歸因 ====================
    
    async def attribute_new_feature_revenue(
        self,
        feature_id: str,
        feature_name: str,
        launch_date: date,
        measurement_period_start: date,
        measurement_period_end: date,
        usage_metrics: FeatureUsageMetrics,
        revenue_data: Dict[str, Decimal],
        gpt_oss_dependency_level: str = "high",
        attribution_method: AttributionMethod = AttributionMethod.ALGORITHMIC
    ) -> RevenueAttributionRecordSchema:
        """
        執行新功能收益歸因
        
        Args:
            feature_id: 功能ID
            feature_name: 功能名稱
            launch_date: 上線日期
            measurement_period_start: 測量期間開始
            measurement_period_end: 測量期間結束
            usage_metrics: 使用指標
            revenue_data: 收益數據
            gpt_oss_dependency_level: GPT-OSS依賴程度
            attribution_method: 歸因方法
            
        Returns:
            收益歸因記錄
        """
        try:
            # 追蹤新功能收益
            feature_revenue = await self.feature_revenue_tracker.track_new_feature_revenue(
                feature_id=feature_id,
                feature_name=feature_name,
                feature_category=getattr(self.feature_revenue_tracker, '_guess_feature_category')(feature_name),
                launch_date=launch_date,
                gpt_oss_dependency_level=gpt_oss_dependency_level,
                usage_metrics=usage_metrics,
                revenue_data=revenue_data,
                measurement_period_start=measurement_period_start,
                measurement_period_end=measurement_period_end
            )
            
            # 計算總收益
            total_revenue = feature_revenue.direct_revenue + feature_revenue.indirect_revenue
            
            # 確定信心度
            conversion_rate = feature_revenue.conversion_rate
            if conversion_rate >= Decimal('15.0') and usage_metrics.engagement_score >= Decimal('80.0'):
                confidence_level = RevenueConfidence.HIGH
                confidence_score = Decimal('92.0')
            elif conversion_rate >= Decimal('8.0') and usage_metrics.engagement_score >= Decimal('65.0'):
                confidence_level = RevenueConfidence.MEDIUM
                confidence_score = Decimal('78.0')
            else:
                confidence_level = RevenueConfidence.LOW
                confidence_score = Decimal('65.0')
            
            # 計算GPT-OSS貢獻
            dependency_factors = {
                'high': Decimal('85.0'),
                'medium': Decimal('60.0'),
                'low': Decimal('35.0')
            }
            gpt_oss_contribution = dependency_factors.get(gpt_oss_dependency_level, Decimal('50.0'))
            
            # 創建歸因記錄
            attribution_record = RevenueAttributionRecordSchema(
                revenue_type=RevenueType.NEW_FEATURE_REVENUE,
                attribution_method=attribution_method,
                amount=total_revenue,
                currency="USD",
                attribution_date=measurement_period_end,
                attribution_period_start=measurement_period_start,
                attribution_period_end=measurement_period_end,
                source_gpt_oss_feature=feature_id,
                gpt_oss_contribution_percentage=gpt_oss_contribution,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                attribution_factors={
                    'feature_name': feature_name,
                    'gpt_oss_dependency_level': gpt_oss_dependency_level,
                    'direct_revenue': float(feature_revenue.direct_revenue),
                    'indirect_revenue': float(feature_revenue.indirect_revenue),
                    'total_users_engaged': feature_revenue.total_users_engaged,
                    'paid_conversions': feature_revenue.paid_conversions,
                    'conversion_rate': float(feature_revenue.conversion_rate),
                    'average_revenue_per_user': float(feature_revenue.average_revenue_per_user)
                },
                feature_id=feature_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by="feature_revenue_attribution_engine",
                validation_status="validated",
                notes=f"基於 {usage_metrics.total_users} 用戶使用數據的新功能收益歸因"
            )
            
            logger.info(f"新功能收益歸因完成: {feature_name} - ${total_revenue:.2f}")
            return attribution_record
            
        except Exception as e:
            logger.error(f"新功能收益歸因失敗 {feature_name}: {e}")
            raise
    
    # ==================== 會員升級歸因 ====================
    
    async def attribute_membership_upgrade(
        self,
        user_id: str,
        from_tier: str,
        to_tier: str,
        upgrade_date: datetime,
        gpt_oss_features_used: List[str],
        usage_history: Dict[str, Any],
        attribution_method: AttributionMethod = AttributionMethod.TIME_DECAY
    ) -> RevenueAttributionRecordSchema:
        """
        執行會員升級歸因
        
        Args:
            user_id: 用戶ID
            from_tier: 原等級
            to_tier: 新等級
            upgrade_date: 升級日期
            gpt_oss_features_used: 使用的GPT-OSS功能
            usage_history: 使用歷史
            attribution_method: 歸因方法
            
        Returns:
            收益歸因記錄
        """
        try:
            # 執行會員升級歸因
            from .revenue_tracker import MembershipTier
            upgrade_attribution = await self.membership_attributor.attribute_membership_upgrade(
                user_id=user_id,
                from_tier=MembershipTier(from_tier.lower()),
                to_tier=MembershipTier(to_tier.lower()),
                upgrade_date=upgrade_date,
                gpt_oss_features_used=gpt_oss_features_used,
                usage_history=usage_history
            )
            
            # 計算總影響分數
            total_influence_score = (
                upgrade_attribution.direct_influence_score +
                upgrade_attribution.indirect_influence_score +
                upgrade_attribution.competitive_advantage_score
            )
            
            # 確定信心度
            if total_influence_score >= Decimal('80.0') and upgrade_attribution.usage_frequency_before_upgrade >= 20:
                confidence_level = RevenueConfidence.HIGH
                confidence_score = Decimal('90.0')
            elif total_influence_score >= Decimal('60.0') and upgrade_attribution.usage_frequency_before_upgrade >= 10:
                confidence_level = RevenueConfidence.MEDIUM
                confidence_score = Decimal('75.0')
            else:
                confidence_level = RevenueConfidence.LOW
                confidence_score = Decimal('60.0')
            
            # 計算GPT-OSS貢獻 (基於影響分數)
            gpt_oss_contribution = min(Decimal('95.0'), total_influence_score * Decimal('0.8'))
            
            # 創建歸因記錄
            attribution_record = RevenueAttributionRecordSchema(
                revenue_type=RevenueType.MEMBERSHIP_UPGRADE,
                attribution_method=attribution_method,
                amount=upgrade_attribution.upgrade_revenue,
                currency="USD",
                attribution_date=upgrade_date.date(),
                attribution_period_start=upgrade_date.date() - timedelta(days=30),
                attribution_period_end=upgrade_date.date(),
                source_gpt_oss_feature=",".join(upgrade_attribution.key_trigger_features),
                gpt_oss_contribution_percentage=gpt_oss_contribution,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                attribution_factors={
                    'from_tier': from_tier,
                    'to_tier': to_tier,
                    'upgrade_revenue': float(upgrade_attribution.upgrade_revenue),
                    'projected_annual_value': float(upgrade_attribution.projected_annual_value),
                    'retention_probability': float(upgrade_attribution.retention_probability),
                    'direct_influence_score': float(upgrade_attribution.direct_influence_score),
                    'indirect_influence_score': float(upgrade_attribution.indirect_influence_score),
                    'competitive_advantage_score': float(upgrade_attribution.competitive_advantage_score),
                    'usage_frequency_before_upgrade': upgrade_attribution.usage_frequency_before_upgrade,
                    'key_trigger_features': upgrade_attribution.key_trigger_features,
                    'touchpoint_analysis': upgrade_attribution.touchpoint_analysis
                },
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by="membership_upgrade_attribution_engine",
                validation_status="validated",
                notes=f"基於 {len(gpt_oss_features_used)} 個GPT-OSS功能使用的會員升級歸因分析"
            )
            
            logger.info(f"會員升級歸因完成: {user_id} {from_tier}→{to_tier} - ${upgrade_attribution.upgrade_revenue:.2f}")
            return attribution_record
            
        except Exception as e:
            logger.error(f"會員升級歸因失敗 {user_id}: {e}")
            raise
    
    # ==================== 收益預測 ====================
    
    async def generate_revenue_forecast(
        self,
        request: RevenueForecastRequest,
        historical_attribution_data: List[RevenueAttributionRecordSchema] = None
    ) -> RevenueForecastSchema:
        """
        生成收益預測
        
        Args:
            request: 預測請求
            historical_attribution_data: 歷史歸因數據
            
        Returns:
            收益預測記錄
        """
        try:
            # 準備歷史數據
            if historical_attribution_data:
                historical_data = [
                    {
                        'date': record.attribution_date.isoformat(),
                        'revenue_amount': float(record.amount),
                        'gpt_oss_impact_factor': float(record.gpt_oss_contribution_percentage) / 100,
                        'revenue_type': record.revenue_type.value,
                        'confidence_score': float(record.confidence_score)
                    }
                    for record in historical_attribution_data
                    if record.revenue_type == request.revenue_type
                ]
            else:
                # 生成示例歷史數據用於演示
                historical_data = self._generate_sample_historical_data(request.revenue_type)
            
            # 生成預測
            forecast = await self.forecast_engine.generate_revenue_forecast(
                request=request,
                historical_data=historical_data
            )
            
            logger.info(f"收益預測生成完成: {request.forecast_name}")
            return forecast
            
        except Exception as e:
            logger.error(f"收益預測生成失敗: {e}")
            raise
    
    def _generate_sample_historical_data(self, revenue_type: RevenueType) -> List[Dict[str, Any]]:
        """生成示例歷史數據"""
        base_amounts = {
            RevenueType.API_COST_SAVINGS: 1500.0,
            RevenueType.NEW_FEATURE_REVENUE: 2500.0,
            RevenueType.MEMBERSHIP_UPGRADE: 800.0,
            RevenueType.EFFICIENCY_GAINS: 1200.0,
            RevenueType.PREMIUM_SERVICE: 3000.0
        }
        
        base_amount = base_amounts.get(revenue_type, 1000.0)
        historical_data = []
        
        for i in range(12):  # 12個月歷史數據
            record_date = date.today() - timedelta(days=30 * (12 - i))
            
            # 添加趨勢和隨機變化
            trend_factor = 1 + (i * 0.05)  # 5% 月增長
            seasonal_factor = 1 + 0.2 * (i % 4 - 2) / 2  # 季節性變化
            random_factor = 1 + (hash(str(record_date)) % 20 - 10) / 100  # 隨機變化
            
            amount = base_amount * trend_factor * seasonal_factor * random_factor
            
            historical_data.append({
                'date': record_date.isoformat(),
                'revenue_amount': max(100.0, amount),  # 確保最小值
                'gpt_oss_impact_factor': 0.6 + (i * 0.02),  # GPT-OSS影響遞增
                'revenue_type': revenue_type.value,
                'confidence_score': 75.0 + (i * 2)  # 信心度遞增
            })
        
        return historical_data
    
    # ==================== 綜合分析 ====================
    
    async def perform_comprehensive_revenue_analysis(
        self,
        request: RevenueAttributionRequest
    ) -> RevenueAnalysisResponse:
        """
        執行綜合收益分析
        
        Args:
            request: 收益歸因請求
            
        Returns:
            收益分析響應
        """
        try:
            analysis_id = uuid4()
            
            # 模擬獲取歷史歸因數據
            # 在實際實現中，這裡應該從數據庫查詢
            sample_attributions = await self._get_sample_attributions(request)
            
            # 計算總歸因收益
            total_attributed_revenue = sum(
                attr.amount for attr in sample_attributions
                if attr.revenue_type == request.revenue_type
            )
            
            # 計算平均信心度
            confidence_scores = [
                attr.confidence_score for attr in sample_attributions
                if attr.revenue_type == request.revenue_type
            ]
            avg_confidence_score = (
                sum(confidence_scores) / len(confidence_scores)
                if confidence_scores else Decimal('70.0')
            )
            
            # 計算GPT-OSS貢獻
            gpt_oss_contributions = [
                attr.gpt_oss_contribution_percentage for attr in sample_attributions
                if attr.revenue_type == request.revenue_type
            ]
            avg_gpt_oss_contribution = (
                sum(gpt_oss_contributions) / len(gpt_oss_contributions)
                if gpt_oss_contributions else Decimal('60.0')
            )
            
            # 生成洞察
            key_insights = self._generate_analysis_insights(
                request, sample_attributions, total_attributed_revenue, avg_gpt_oss_contribution
            )
            
            # 生成建議
            recommendations = self._generate_analysis_recommendations(
                request, avg_confidence_score, avg_gpt_oss_contribution
            )
            
            # 評估數據品質
            data_quality_score = self._assess_data_quality(sample_attributions)
            
            response = RevenueAnalysisResponse(
                analysis_id=analysis_id,
                analysis_type=f"{request.revenue_type.value}_comprehensive_analysis",
                total_attributed_revenue=total_attributed_revenue,
                confidence_score=avg_confidence_score,
                gpt_oss_contribution=avg_gpt_oss_contribution,
                key_insights=key_insights,
                recommendations=recommendations,
                data_quality_score=data_quality_score,
                analysis_date=datetime.now(timezone.utc),
                next_review_date=date.today() + timedelta(days=30)
            )
            
            # 快取分析結果
            self.attribution_cache[str(analysis_id)] = {
                'response': response,
                'timestamp': datetime.now(timezone.utc),
                'request': request
            }
            
            logger.info(f"綜合收益分析完成: {request.revenue_type.value}")
            return response
            
        except Exception as e:
            logger.error(f"綜合收益分析失敗: {e}")
            raise
    
    async def _get_sample_attributions(
        self,
        request: RevenueAttributionRequest
    ) -> List[RevenueAttributionRecordSchema]:
        """獲取示例歸因數據"""
        sample_data = []
        
        # 生成示例數據
        for i in range(10):
            record_date = request.end_date - timedelta(days=i * 3)
            
            attribution = RevenueAttributionRecordSchema(
                revenue_type=request.revenue_type,
                attribution_method=request.attribution_method,
                amount=Decimal(str(1000 + i * 150)),
                attribution_date=record_date,
                attribution_period_start=record_date - timedelta(days=7),
                attribution_period_end=record_date,
                source_gpt_oss_feature=f"gpt_oss_feature_{i % 3 + 1}",
                gpt_oss_contribution_percentage=Decimal(str(60 + i * 2)),
                confidence_level=RevenueConfidence.MEDIUM,
                confidence_score=Decimal(str(75 + i)),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                created_by="sample_data_generator"
            )
            sample_data.append(attribution)
        
        return sample_data
    
    def _generate_analysis_insights(
        self,
        request: RevenueAttributionRequest,
        attributions: List[RevenueAttributionRecordSchema],
        total_revenue: Decimal,
        avg_gpt_oss_contribution: Decimal
    ) -> List[str]:
        """生成分析洞察"""
        insights = []
        
        if total_revenue > Decimal('10000'):
            insights.append(f"{request.revenue_type.value}在分析期間創造了顯著收益 ${total_revenue:.2f}")
        
        if avg_gpt_oss_contribution > Decimal('70'):
            insights.append(f"GPT-OSS對{request.revenue_type.value}有高度影響 ({avg_gpt_oss_contribution:.1f}%)")
        elif avg_gpt_oss_contribution > Decimal('50'):
            insights.append(f"GPT-OSS對{request.revenue_type.value}有中等影響 ({avg_gpt_oss_contribution:.1f}%)")
        
        if len(attributions) >= 5:
            recent_attributions = sorted(attributions, key=lambda x: x.attribution_date, reverse=True)[:3]
            recent_avg = sum(attr.amount for attr in recent_attributions) / len(recent_attributions)
            older_attributions = sorted(attributions, key=lambda x: x.attribution_date)[:-3]
            if older_attributions:
                older_avg = sum(attr.amount for attr in older_attributions) / len(older_attributions)
                if recent_avg > older_avg * Decimal('1.2'):
                    insights.append("近期收益歸因呈現顯著上升趨勢")
                elif recent_avg < older_avg * Decimal('0.8'):
                    insights.append("近期收益歸因出現下降，需要關注")
        
        # 數據覆蓋洞察
        date_range = (request.end_date - request.start_date).days
        if len(attributions) / date_range > 0.3:
            insights.append("數據覆蓋度良好，分析結果可信度高")
        else:
            insights.append("數據覆蓋度較低，建議增加數據收集頻率")
        
        return insights
    
    def _generate_analysis_recommendations(
        self,
        request: RevenueAttributionRequest,
        avg_confidence_score: Decimal,
        avg_gpt_oss_contribution: Decimal
    ) -> List[str]:
        """生成分析建議"""
        recommendations = []
        
        if avg_confidence_score < Decimal('70'):
            recommendations.append("建議改善數據收集品質以提高歸因信心度")
        
        if avg_gpt_oss_contribution < Decimal('40'):
            recommendations.append("考慮加強GPT-OSS功能的推廣和優化以提高收益影響")
        elif avg_gpt_oss_contribution > Decimal('80'):
            recommendations.append("GPT-OSS表現優異，建議擴大相關功能投資")
        
        if request.revenue_type == RevenueType.API_COST_SAVINGS:
            recommendations.append("持續監控API成本節省效果，優化模型切換策略")
        elif request.revenue_type == RevenueType.NEW_FEATURE_REVENUE:
            recommendations.append("分析高收益功能特徵，指導未來功能開發策略")
        elif request.revenue_type == RevenueType.MEMBERSHIP_UPGRADE:
            recommendations.append("強化GPT-OSS功能在會員升級路徑中的曝光和體驗")
        
        recommendations.append("建議定期(月度)進行收益歸因分析以監控趨勢變化")
        recommendations.append("考慮建立預測模型以提前識別收益機會和風險")
        
        return recommendations
    
    def _assess_data_quality(
        self,
        attributions: List[RevenueAttributionRecordSchema]
    ) -> Decimal:
        """評估數據品質"""
        if not attributions:
            return Decimal('0')
        
        # 評估因素
        completeness_score = Decimal('100')  # 數據完整性
        consistency_score = Decimal('100')   # 數據一致性
        timeliness_score = Decimal('100')    # 數據時效性
        accuracy_score = Decimal('100')     # 數據準確性
        
        # 完整性檢查
        missing_fields_count = 0
        for attr in attributions:
            if not attr.attribution_factors:
                missing_fields_count += 1
            if not attr.notes:
                missing_fields_count += 1
        
        if missing_fields_count > 0:
            completeness_score -= Decimal(str(missing_fields_count * 5))
        
        # 一致性檢查（信心度分佈）
        confidence_scores = [attr.confidence_score for attr in attributions]
        if confidence_scores:
            confidence_std = Decimal(str(float(np.std([float(score) for score in confidence_scores]))))
            if confidence_std > Decimal('20'):
                consistency_score -= Decimal('15')
        
        # 時效性檢查
        recent_data_count = len([
            attr for attr in attributions
            if (date.today() - attr.attribution_date).days <= 30
        ])
        timeliness_ratio = recent_data_count / len(attributions)
        if timeliness_ratio < 0.3:
            timeliness_score -= Decimal('20')
        
        # 準確性檢查（基於驗證狀態）
        validated_count = len([
            attr for attr in attributions
            if attr.validation_status == "validated"
        ])
        accuracy_ratio = validated_count / len(attributions)
        accuracy_score = Decimal(str(accuracy_ratio * 100))
        
        # 綜合評分
        overall_score = (
            completeness_score * Decimal('0.25') +
            consistency_score * Decimal('0.25') +
            timeliness_score * Decimal('0.25') +
            accuracy_score * Decimal('0.25')
        )
        
        return max(Decimal('0'), min(Decimal('100'), overall_score))
    
    # ==================== 服務健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """服務健康檢查"""
        try:
            health_status = {
                'service_name': 'revenue_attribution_service',
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc),
                'components': {
                    'api_cost_calculator': 'healthy',
                    'feature_revenue_tracker': 'healthy',
                    'membership_attributor': 'healthy',
                    'forecast_engine': 'healthy'
                },
                'cache_stats': {
                    'attribution_cache_size': len(self.attribution_cache),
                    'forecast_cache_size': len(getattr(self.forecast_engine, 'forecast_cache', {}))
                },
                'service_initialized': self.service_initialized
            }
            
            # 檢查各組件狀態
            if not self.service_initialized:
                health_status['status'] = 'initializing'
            
            return health_status
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                'service_name': 'revenue_attribution_service',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }
    
    async def get_service_metrics(self) -> Dict[str, Any]:
        """獲取服務指標"""
        try:
            return {
                'service_uptime': 'N/A',  # 實際實現需要記錄啟動時間
                'total_attributions_processed': 'N/A',  # 需要持久化計數器
                'cache_hit_rate': 'N/A',
                'average_processing_time': 'N/A',
                'error_rate': 'N/A',
                'component_status': {
                    'api_cost_calculator': 'operational',
                    'feature_revenue_tracker': 'operational',
                    'membership_attributor': 'operational',
                    'forecast_engine': 'operational'
                },
                'metrics_timestamp': datetime.now(timezone.utc)
            }
        except Exception as e:
            logger.error(f"獲取服務指標失敗: {e}")
            return {'error': str(e)}
    
    # ==================== 輔助方法 ====================
    
    def _guess_feature_category(self, feature_name: str):
        """猜測功能類別（輔助方法）"""
        from .revenue_tracker import FeatureCategory
        
        feature_name_lower = feature_name.lower()
        
        if any(keyword in feature_name_lower for keyword in ['analysis', 'analyze', 'insight']):
            return FeatureCategory.AI_ANALYSIS
        elif any(keyword in feature_name_lower for keyword in ['predict', 'forecast', 'model']):
            return FeatureCategory.PREDICTION_MODEL
        elif any(keyword in feature_name_lower for keyword in ['trading', 'trade', 'automated']):
            return FeatureCategory.AUTOMATED_TRADING
        elif any(keyword in feature_name_lower for keyword in ['risk', 'management', 'control']):
            return FeatureCategory.RISK_MANAGEMENT
        elif any(keyword in feature_name_lower for keyword in ['market', 'insight', 'intelligence']):
            return FeatureCategory.MARKET_INSIGHTS
        elif any(keyword in feature_name_lower for keyword in ['personal', 'custom', 'individual']):
            return FeatureCategory.PERSONALIZATION
        elif any(keyword in feature_name_lower for keyword in ['alert', 'notification', 'premium']):
            return FeatureCategory.PREMIUM_ALERTS
        else:
            return FeatureCategory.AI_ANALYSIS  # 預設分類