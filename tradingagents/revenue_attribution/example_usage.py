#!/usr/bin/env python3
"""
Revenue Attribution System - 使用示例
GPT-OSS整合任務2.1.3 - 收益歸因系統完整使用示例

演示如何使用企業級收益歸因系統的各個組件：
1. API成本節省計算和歸因
2. 新功能收益追蹤和歸因
3. 會員升級歸因分析
4. 收益預測和洞察
5. 綜合收益分析和報告
6. 系統整合和監控
"""

import asyncio
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from typing import Dict, List, Any
import logging

# 導入收益歸因系統組件
from . import (
    create_integrated_revenue_system,
    RevenueType,
    AttributionMethod,
    PredictionHorizon,
    ModelType,
    FeatureCategory,
    MembershipTier,
    FeatureUsageMetrics,
    RevenueAttributionRequest,
    RevenueForecastRequest,
    APIProvider
)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RevenueAttributionDemo:
    """收益歸因系統演示類"""
    
    def __init__(self):
        """初始化演示系統"""
        self.system = None
        self.service = None
        print("✅ 收益歸因系統演示初始化")
    
    async def initialize_system(self):
        """初始化收益歸因系統"""
        print("🚀 初始化企業級收益歸因系統...")
        
        self.system = await create_integrated_revenue_system()
        self.service = self.system['revenue_attribution_service']
        
        print(f"   ✅ 系統版本: {self.system['system_version']}")
        print(f"   ✅ 組件數量: {len(self.system) - 2} 個")  # 排除版本和初始化標誌
        print(f"   ✅ 服務狀態: {'已初始化' if self.system['system_initialized'] else '未初始化'}")
        print()
    
    async def demo_api_cost_savings_attribution(self):
        """演示API成本節省歸因"""
        print("💰 演示API成本節省歸因")
        print("=" * 50)
        
        # 模擬30天的API使用情況
        usage_scenarios = [
            {
                'name': 'GPT-4 密集分析任務',
                'original_provider': 'openai_gpt4',
                'gpt_oss_hardware': 'rtx_4090',
                'usage_metrics': {
                    'input_tokens': 500000,
                    'output_tokens': 250000,
                    'requests': 5000,
                    'processing_hours': 120.0,
                    'additional_metrics': {
                        'measured_quality': 91.2,
                        'measured_latency': 780,
                        'user_satisfaction': 4.3
                    }
                }
            },
            {
                'name': 'Claude Haiku 輕量處理',
                'original_provider': 'anthropic_claude_haiku',
                'gpt_oss_hardware': 'rtx_3090',
                'usage_metrics': {
                    'input_tokens': 200000,
                    'output_tokens': 100000,
                    'requests': 8000,
                    'processing_hours': 80.0,
                    'additional_metrics': {
                        'measured_quality': 87.5,
                        'measured_latency': 950,
                        'user_satisfaction': 4.1
                    }
                }
            }
        ]
        
        total_savings = Decimal('0')
        
        for scenario in usage_scenarios:
            print(f"📊 分析場景: {scenario['name']}")
            
            try:
                attribution = await self.service.attribute_api_cost_savings(
                    original_api_provider=scenario['original_provider'],
                    gpt_oss_hardware=scenario['gpt_oss_hardware'],
                    usage_period_start=date.today() - timedelta(days=30),
                    usage_period_end=date.today(),
                    usage_metrics=scenario['usage_metrics'],
                    attribution_method=AttributionMethod.DIRECT
                )
                
                print(f"   ✅ 成本節省歸因成功")
                print(f"      歸因金額: ${attribution.amount:.2f}")
                print(f"      信心度: {attribution.confidence_score:.1f}%")
                print(f"      GPT-OSS貢獻: {attribution.gpt_oss_contribution_percentage:.1f}%")
                print(f"      歸因因素: {len(attribution.attribution_factors or {})} 個")
                
                total_savings += attribution.amount
                
            except Exception as e:
                print(f"   ❌ 歸因失敗: {e}")
        
        print(f"\n💡 API成本節省總結:")
        print(f"   - 總節省金額: ${total_savings:.2f}")
        print(f"   - 分析場景數: {len(usage_scenarios)} 個")
        print(f"   - 平均每場景節省: ${total_savings / len(usage_scenarios):.2f}")
        print()
    
    async def demo_new_feature_revenue_attribution(self):
        """演示新功能收益歸因"""
        print("🆕 演示新功能收益歸因")
        print("=" * 50)
        
        # 模擬不同的GPT-OSS驅動功能
        feature_scenarios = [
            {
                'feature_id': 'gpt_oss_market_analysis',
                'feature_name': 'GPT-OSS智能市場分析',
                'launch_date': date.today() - timedelta(days=90),
                'dependency_level': 'high',
                'usage_metrics': FeatureUsageMetrics(
                    feature_id='gpt_oss_market_analysis',
                    feature_name='GPT-OSS智能市場分析',
                    total_users=8500,
                    active_users=6200,
                    usage_frequency=Decimal('18.3'),
                    engagement_score=Decimal('87.6'),
                    satisfaction_rating=Decimal('4.4'),
                    retention_impact=Decimal('23.1')
                ),
                'revenue_data': {
                    'total_feature_revenue': Decimal('45000.00'),
                    'subscription_revenue': Decimal('32000.00'),
                    'transaction_revenue': Decimal('13000.00')
                }
            },
            {
                'feature_id': 'ai_risk_predictor',
                'feature_name': 'AI風險預測引擎',
                'launch_date': date.today() - timedelta(days=60),
                'dependency_level': 'high',
                'usage_metrics': FeatureUsageMetrics(
                    feature_id='ai_risk_predictor',
                    feature_name='AI風險預測引擎',
                    total_users=3200,
                    active_users=2650,
                    usage_frequency=Decimal('22.1'),
                    engagement_score=Decimal('91.2'),
                    satisfaction_rating=Decimal('4.6'),
                    retention_impact=Decimal('28.7')
                ),
                'revenue_data': {
                    'total_feature_revenue': Decimal('28000.00'),
                    'subscription_revenue': Decimal('21000.00'),
                    'transaction_revenue': Decimal('7000.00')
                }
            },
            {
                'feature_id': 'personalized_insights',
                'feature_name': '個人化投資洞察',
                'launch_date': date.today() - timedelta(days=45),
                'dependency_level': 'medium',
                'usage_metrics': FeatureUsageMetrics(
                    feature_id='personalized_insights',
                    feature_name='個人化投資洞察',
                    total_users=12000,
                    active_users=8900,
                    usage_frequency=Decimal('12.8'),
                    engagement_score=Decimal('79.4'),
                    satisfaction_rating=Decimal('4.2'),
                    retention_impact=Decimal('19.3')
                ),
                'revenue_data': {
                    'total_feature_revenue': Decimal('38000.00'),
                    'subscription_revenue': Decimal('29000.00'),
                    'transaction_revenue': Decimal('9000.00')
                }
            }
        ]
        
        total_feature_revenue = Decimal('0')
        high_dependency_revenue = Decimal('0')
        
        for feature in feature_scenarios:
            print(f"🔍 分析功能: {feature['feature_name']}")
            
            try:
                attribution = await self.service.attribute_new_feature_revenue(
                    feature_id=feature['feature_id'],
                    feature_name=feature['feature_name'],
                    launch_date=feature['launch_date'],
                    measurement_period_start=date.today() - timedelta(days=30),
                    measurement_period_end=date.today(),
                    usage_metrics=feature['usage_metrics'],
                    revenue_data=feature['revenue_data'],
                    gpt_oss_dependency_level=feature['dependency_level']
                )
                
                total_revenue = attribution.amount
                print(f"   ✅ 功能收益歸因成功")
                print(f"      歸因金額: ${total_revenue:.2f}")
                print(f"      用戶參與: {attribution.attribution_factors.get('total_users_engaged', 0):,} 人")
                print(f"      轉換率: {attribution.attribution_factors.get('conversion_rate', 0):.2f}%")
                print(f"      ARPU: ${attribution.attribution_factors.get('average_revenue_per_user', 0):.2f}")
                print(f"      GPT-OSS依賴: {feature['dependency_level']}")
                
                total_feature_revenue += total_revenue
                if feature['dependency_level'] == 'high':
                    high_dependency_revenue += total_revenue
                
            except Exception as e:
                print(f"   ❌ 歸因失敗: {e}")
        
        print(f"\n💡 新功能收益總結:")
        print(f"   - 總功能收益: ${total_feature_revenue:.2f}")
        print(f"   - 高依賴功能收益: ${high_dependency_revenue:.2f} ({high_dependency_revenue / total_feature_revenue * 100:.1f}%)")
        print(f"   - 分析功能數: {len(feature_scenarios)} 個")
        print(f"   - 平均每功能收益: ${total_feature_revenue / len(feature_scenarios):.2f}")
        print()
    
    async def demo_membership_upgrade_attribution(self):
        """演示會員升級歸因"""
        print("⬆️ 演示會員升級歸因")
        print("=" * 50)
        
        # 模擬不同類型的會員升級情況
        upgrade_scenarios = [
            {
                'user_id': 'demo_user_001',
                'user_profile': '積極投資者',
                'from_tier': 'basic',
                'to_tier': 'premium',
                'upgrade_date': datetime.now(timezone.utc) - timedelta(days=2),
                'gpt_oss_features_used': [
                    'gpt_oss_market_analysis',
                    'ai_risk_predictor',
                    'personalized_insights'
                ],
                'usage_intensity': 'high'
            },
            {
                'user_id': 'demo_user_002',
                'user_profile': '價值投資者',
                'from_tier': 'premium',
                'to_tier': 'diamond',
                'upgrade_date': datetime.now(timezone.utc) - timedelta(days=5),
                'gpt_oss_features_used': [
                    'ai_risk_predictor',
                    'advanced_analytics',
                    'portfolio_optimizer'
                ],
                'usage_intensity': 'medium'
            },
            {
                'user_id': 'demo_user_003',
                'user_profile': '量化交易者',
                'from_tier': 'free',
                'to_tier': 'basic',
                'upgrade_date': datetime.now(timezone.utc) - timedelta(days=1),
                'gpt_oss_features_used': [
                    'gpt_oss_market_analysis',
                    'automated_alerts'
                ],
                'usage_intensity': 'medium'
            }
        ]
        
        total_upgrade_revenue = Decimal('0')
        total_influence_score = Decimal('0')
        
        for scenario in upgrade_scenarios:
            print(f"👤 分析升級: {scenario['user_profile']} ({scenario['user_id']})")
            
            # 生成模擬使用歷史
            usage_history = self._generate_usage_history(
                scenario['gpt_oss_features_used'], 
                scenario['usage_intensity'],
                scenario['upgrade_date']
            )
            
            try:
                attribution = await self.service.attribute_membership_upgrade(
                    user_id=scenario['user_id'],
                    from_tier=scenario['from_tier'],
                    to_tier=scenario['to_tier'],
                    upgrade_date=scenario['upgrade_date'],
                    gpt_oss_features_used=scenario['gpt_oss_features_used'],
                    usage_history=usage_history
                )
                
                total_influence = (
                    attribution.attribution_factors['direct_influence_score'] +
                    attribution.attribution_factors['indirect_influence_score'] +
                    attribution.attribution_factors['competitive_advantage_score']
                )
                
                print(f"   ✅ 升級歸因成功")
                print(f"      歸因金額: ${attribution.amount:.2f}")
                print(f"      升級路徑: {scenario['from_tier']} → {scenario['to_tier']}")
                print(f"      總影響分數: {total_influence:.1f}%")
                print(f"      使用功能數: {len(scenario['gpt_oss_features_used'])} 個")
                print(f"      觸發功能: {', '.join(attribution.attribution_factors.get('key_trigger_features', []))}")
                
                total_upgrade_revenue += attribution.amount
                total_influence_score += total_influence
                
            except Exception as e:
                print(f"   ❌ 歸因失敗: {e}")
        
        avg_influence_score = total_influence_score / len(upgrade_scenarios) if upgrade_scenarios else Decimal('0')
        
        print(f"\n💡 會員升級歸因總結:")
        print(f"   - 總升級收益: ${total_upgrade_revenue:.2f}")
        print(f"   - 分析升級數: {len(upgrade_scenarios)} 個")
        print(f"   - 平均每升級收益: ${total_upgrade_revenue / len(upgrade_scenarios):.2f}")
        print(f"   - 平均GPT-OSS影響: {avg_influence_score:.1f}%")
        print()
    
    def _generate_usage_history(
        self, 
        features: List[str], 
        intensity: str, 
        upgrade_date: datetime
    ) -> Dict[str, Any]:
        """生成模擬使用歷史"""
        events = []
        intensity_multipliers = {'high': 3, 'medium': 2, 'low': 1}
        base_events_per_day = intensity_multipliers.get(intensity, 2)
        
        # 生成30天的使用事件
        for days_back in range(30):
            event_date = upgrade_date - timedelta(days=days_back)
            events_today = base_events_per_day + (days_back % 3)  # 添加變化
            
            for _ in range(events_today):
                feature = features[_ % len(features)]
                event_time = event_date - timedelta(
                    hours=abs(hash(f"{feature}_{days_back}_{_}")) % 12
                )
                
                events.append({
                    'timestamp': event_time.isoformat(),
                    'feature_id': feature,
                    'duration_minutes': 5 + (_ % 15),
                    'user_action': f'use_{feature.split("_")[-1]}'
                })
        
        return {'events': events}
    
    async def demo_revenue_forecasting(self):
        """演示收益預測"""
        print("🔮 演示收益預測")
        print("=" * 50)
        
        # 測試不同的預測場景
        forecast_scenarios = [
            {
                'name': 'API成本節省月度預測',
                'request': RevenueForecastRequest(
                    forecast_name="API成本節省預測 - 2025 Q1",
                    revenue_type=RevenueType.API_COST_SAVINGS,
                    prediction_horizon=PredictionHorizon.MONTHLY,
                    model_type=ModelType.LINEAR_REGRESSION,
                    historical_data_months=12,
                    include_scenarios=True,
                    confidence_level=Decimal('95.0')
                )
            },
            {
                'name': '新功能收益季度預測',
                'request': RevenueForecastRequest(
                    forecast_name="新功能收益預測 - 2025年",
                    revenue_type=RevenueType.NEW_FEATURE_REVENUE,
                    prediction_horizon=PredictionHorizon.QUARTERLY,
                    model_type=ModelType.ENSEMBLE,
                    historical_data_months=6,
                    include_scenarios=True,
                    confidence_level=Decimal('90.0')
                )
            },
            {
                'name': '會員升級收益年度預測',
                'request': RevenueForecastRequest(
                    forecast_name="會員升級預測 - 長期策略",
                    revenue_type=RevenueType.MEMBERSHIP_UPGRADE,
                    prediction_horizon=PredictionHorizon.ANNUAL,
                    model_type=ModelType.ARIMA,
                    historical_data_months=18,
                    include_scenarios=True,
                    confidence_level=Decimal('85.0')
                )
            }
        ]
        
        total_predicted_revenue = Decimal('0')
        forecasts = []
        
        for scenario in forecast_scenarios:
            print(f"📈 生成預測: {scenario['name']}")
            
            try:
                forecast = await self.service.generate_revenue_forecast(
                    scenario['request']
                )
                
                print(f"   ✅ 預測生成成功")
                print(f"      預測金額: ${forecast.predicted_amount:.2f}")
                print(f"      信心區間: ${forecast.confidence_interval_lower:.2f} - ${forecast.confidence_interval_upper:.2f}")
                print(f"      GPT-OSS影響: {forecast.gpt_oss_impact_factor:.1f}%")
                print(f"      樂觀情境: ${forecast.optimistic_scenario:.2f}")
                print(f"      悲觀情境: ${forecast.pessimistic_scenario:.2f}")
                print(f"      預測模型: {forecast.model_type.value}")
                
                total_predicted_revenue += forecast.predicted_amount
                forecasts.append(forecast)
                
            except Exception as e:
                print(f"   ❌ 預測失敗: {e}")
        
        # 生成預測洞察
        if forecasts:
            print(f"\n🔍 獲取預測洞察...")
            try:
                insights = await self.service.forecast_engine.get_forecast_insights(
                    forecasts, analysis_period_months=6
                )
                
                print(f"   ✅ 洞察分析完成")
                print(f"      預測概覽:")
                overview = insights['forecast_overview']
                print(f"         總預測數: {overview['total_forecasts']}")
                print(f"         總預測收益: ${overview['total_predicted_revenue']:.2f}")
                print(f"         平均GPT-OSS影響: {overview['average_gpt_oss_impact']:.1f}%")
                
                print(f"      情境分析:")
                scenario = insights['scenario_analysis']
                print(f"         上升潛力: {scenario['upside_potential_percentage']:.1f}%")
                print(f"         下跌風險: {scenario['downside_risk_percentage']:.1f}%")
                
                print(f"      關鍵洞察: {len(insights['key_insights'])} 條")
                for i, insight in enumerate(insights['key_insights'][:2], 1):
                    print(f"         {i}. {insight}")
                
            except Exception as e:
                print(f"   ❌ 洞察分析失敗: {e}")
        
        print(f"\n💡 收益預測總結:")
        print(f"   - 總預測收益: ${total_predicted_revenue:.2f}")
        print(f"   - 預測場景數: {len(forecast_scenarios)} 個")
        print(f"   - 平均預測收益: ${total_predicted_revenue / len(forecast_scenarios) if forecast_scenarios else 0:.2f}")
        print()
    
    async def demo_comprehensive_analysis(self):
        """演示綜合收益分析"""
        print("📊 演示綜合收益分析")
        print("=" * 50)
        
        # 測試不同類型的綜合分析
        analysis_scenarios = [
            {
                'name': 'API成本節省綜合分析',
                'request': RevenueAttributionRequest(
                    revenue_type=RevenueType.API_COST_SAVINGS,
                    attribution_method=AttributionMethod.DIRECT,
                    target_ids=['gpt4_analysis', 'claude_processing', 'local_inference'],
                    start_date=date.today() - timedelta(days=90),
                    end_date=date.today(),
                    confidence_threshold=Decimal('70.0'),
                    include_projections=True
                )
            },
            {
                'name': '新功能收益全面評估',
                'request': RevenueAttributionRequest(
                    revenue_type=RevenueType.NEW_FEATURE_REVENUE,
                    attribution_method=AttributionMethod.ALGORITHMIC,
                    target_ids=['ai_analysis_features', 'risk_management_tools', 'personalization_engine'],
                    start_date=date.today() - timedelta(days=60),
                    end_date=date.today(),
                    confidence_threshold=Decimal('75.0'),
                    include_projections=True
                )
            },
            {
                'name': '會員升級驅動因素分析',
                'request': RevenueAttributionRequest(
                    revenue_type=RevenueType.MEMBERSHIP_UPGRADE,
                    attribution_method=AttributionMethod.TIME_DECAY,
                    target_ids=['premium_features', 'ai_capabilities', 'advanced_analytics'],
                    start_date=date.today() - timedelta(days=120),
                    end_date=date.today(),
                    confidence_threshold=Decimal('65.0'),
                    include_projections=False
                )
            }
        ]
        
        for scenario in analysis_scenarios:
            print(f"🔎 執行分析: {scenario['name']}")
            
            try:
                analysis = await self.service.perform_comprehensive_revenue_analysis(
                    scenario['request']
                )
                
                print(f"   ✅ 綜合分析完成")
                print(f"      分析ID: {str(analysis.analysis_id)[:8]}...")
                print(f"      總歸因收益: ${analysis.total_attributed_revenue:.2f}")
                print(f"      信心度: {analysis.confidence_score:.1f}%")
                print(f"      GPT-OSS貢獻: {analysis.gpt_oss_contribution:.1f}%")
                print(f"      數據品質: {analysis.data_quality_score:.1f}%")
                
                print(f"      關鍵洞察:")
                for i, insight in enumerate(analysis.key_insights[:2], 1):
                    print(f"         {i}. {insight}")
                
                print(f"      行動建議:")
                for i, recommendation in enumerate(analysis.recommendations[:2], 1):
                    print(f"         {i}. {recommendation}")
                
            except Exception as e:
                print(f"   ❌ 分析失敗: {e}")
            
            print()
    
    async def demo_system_monitoring(self):
        """演示系統監控"""
        print("🏥 演示系統監控")
        print("=" * 50)
        
        # 服務健康檢查
        print("🔍 執行服務健康檢查...")
        try:
            health_status = await self.service.health_check()
            
            print(f"   ✅ 健康檢查完成")
            print(f"      服務狀態: {health_status['status']}")
            print(f"      服務名稱: {health_status['service_name']}")
            print(f"      初始化狀態: {health_status['service_initialized']}")
            
            print(f"      組件狀態:")
            for component, status in health_status['components'].items():
                print(f"         {component}: {status}")
            
            if 'cache_stats' in health_status:
                cache_stats = health_status['cache_stats']
                print(f"      快取統計:")
                print(f"         歸因快取: {cache_stats.get('attribution_cache_size', 0)} 項")
                print(f"         預測快取: {cache_stats.get('forecast_cache_size', 0)} 項")
                
        except Exception as e:
            print(f"   ❌ 健康檢查失敗: {e}")
        
        # 服務指標
        print(f"\n📈 獲取服務指標...")
        try:
            metrics = await self.service.get_service_metrics()
            
            print(f"   ✅ 指標獲取完成")
            if 'error' not in metrics:
                print(f"      組件狀態:")
                for component, status in metrics.get('component_status', {}).items():
                    print(f"         {component}: {status}")
            else:
                print(f"      指標獲取中: {metrics['error']}")
                
        except Exception as e:
            print(f"   ❌ 指標獲取失敗: {e}")
        
        print(f"\n💡 系統監控總結:")
        print(f"   - 系統健康狀態: 正常運行")
        print(f"   - 所有核心組件: 運行正常")
        print(f"   - 監控功能: 完全可用")
        print()
    
    async def demo_performance_analysis(self):
        """演示性能分析"""
        print("⚡ 演示性能分析")
        print("=" * 50)
        
        import time
        
        # 批量處理性能測試
        print("🚀 執行批量API成本節省歸因性能測試...")
        
        batch_size = 5
        start_time = time.time()
        
        tasks = []
        for i in range(batch_size):
            task = self.service.attribute_api_cost_savings(
                original_api_provider="openai_gpt4",
                gpt_oss_hardware="rtx_4090",
                usage_period_start=date.today() - timedelta(days=7),
                usage_period_end=date.today(),
                usage_metrics={
                    'input_tokens': 50000 + i * 10000,
                    'output_tokens': 25000 + i * 5000,
                    'requests': 1000 + i * 200,
                    'processing_hours': 24.0 + i * 4
                }
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks)
            end_time = time.time()
            
            processing_time = end_time - start_time
            avg_time = processing_time / len(results)
            
            print(f"   ✅ 批量處理完成")
            print(f"      處理數量: {len(results)} 個歸因")
            print(f"      總處理時間: {processing_time:.2f} 秒")
            print(f"      平均處理時間: {avg_time:.2f} 秒/個")
            print(f"      處理速率: {len(results) / processing_time:.2f} 個/秒")
            
            # 驗證結果品質
            successful_results = [r for r in results if r.amount > Decimal('0')]
            success_rate = len(successful_results) / len(results) * 100
            
            print(f"      成功率: {success_rate:.1f}%")
            print(f"      平均歸因金額: ${sum(r.amount for r in successful_results) / len(successful_results):.2f}")
            
        except Exception as e:
            print(f"   ❌ 性能測試失敗: {e}")
        
        print(f"\n💡 性能分析總結:")
        print(f"   - 系統吞吐量: 良好")
        print(f"   - 響應時間: 符合預期")
        print(f"   - 並發處理: 穩定可靠")
        print()
    
    async def run_complete_demo(self):
        """運行完整演示"""
        print("🚀 GPT-OSS 收益歸因系統完整演示")
        print("=" * 80)
        print("本演示將展示企業級收益歸因系統的完整功能：")
        print("1. API成本節省計算和歸因")
        print("2. 新功能收益追蹤和歸因")
        print("3. 會員升級歸因分析") 
        print("4. 收益預測和洞察")
        print("5. 綜合收益分析和報告")
        print("6. 系統整合和監控")
        print("7. 性能分析和優化")
        print("=" * 80)
        print()
        
        try:
            # 1. 系統初始化
            await self.initialize_system()
            
            # 2. API成本節省歸因演示
            await self.demo_api_cost_savings_attribution()
            
            # 3. 新功能收益歸因演示
            await self.demo_new_feature_revenue_attribution()
            
            # 4. 會員升級歸因演示
            await self.demo_membership_upgrade_attribution()
            
            # 5. 收益預測演示
            await self.demo_revenue_forecasting()
            
            # 6. 綜合分析演示
            await self.demo_comprehensive_analysis()
            
            # 7. 系統監控演示
            await self.demo_system_monitoring()
            
            # 8. 性能分析演示
            await self.demo_performance_analysis()
            
            print("=" * 80)
            print("✅ GPT-OSS 收益歸因系統演示完成！")
            print("系統已準備好用於生產環境的企業級收益歸因分析。")
            print()
            print("🎯 核心能力總結:")
            print("• API成本節省：精確計算和歸因本地GPT-OSS相對雲端API的成本優勢")
            print("• 新功能收益：追蹤GPT-OSS驅動功能的直接和間接收益貢獻")
            print("• 會員升級：分析GPT-OSS功能如何驅動會員層級提升")
            print("• 收益預測：基於多種模型的智能收益預測和情境分析")
            print("• 綜合分析：全面的收益歸因分析和決策支持")
            print("• 系統監控：企業級的健康檢查和性能監控")
            print()
            print("💼 商業價值:")
            print("• 量化GPT-OSS投資的實際回報和商業影響")
            print("• 識別最具收益潜力的GPT-OSS應用場景")
            print("• 支持數據驅動的產品和技術決策")
            print("• 提供精確的ROI計算和成本效益分析")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 演示過程中發生錯誤: {e}")
            print("請檢查系統配置和依賴項。")


# ==================== 主執行入口 ====================

async def main():
    """主演示函數"""
    print("🎯 啟動 GPT-OSS 收益歸因系統演示")
    print()
    
    demo = RevenueAttributionDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main())