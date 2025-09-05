#!/usr/bin/env python3
"""
Cost Tracking System - 使用示例
GPT-OSS整合任務2.1.2 - 成本追蹤系統完整使用示例

演示如何使用企業級成本追蹤系統的各個組件：
1. 硬體成本計算和折舊管理
2. 電力和維護成本追蹤
3. 人力成本分攤機制
4. 實時成本監控和告警
5. 成本計算服務API
6. 成本分析和商業智能
"""

import asyncio
import uuid
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal

from . import (
    create_integrated_cost_system,
    HardwareAsset,
    HardwareCategory,
    DepreciationMethod,
    PowerSource,
    MaintenanceType,
    Employee,
    EmployeeRole,
    SkillLevel,
    ActivityType,
    AlertRule,
    AlertType,
    AlertSeverity,
    MonitoringScope,
    CostCalculationRequest,
    CalculationScope,
    AnalysisRequest,
    AnalysisType,
    AnalysisDimension,
    CostDataPoint,
    HardwareCostConfigurationFactory,
    PowerMaintenanceConfigurationFactory,
    LaborCostConfigurationFactory,
    AlertConfigurationFactory
)


class CostTrackingDemo:
    """成本追蹤系統演示類"""
    
    def __init__(self):
        """初始化演示系統"""
        self.system = create_integrated_cost_system()
        print("✅ 成本追蹤系統初始化完成")
        print(f"   - 系統組件: {len(self.system)} 個")
        print(f"   - 硬體計算器: {type(self.system['hardware_calculator']).__name__}")
        print(f"   - 電力追蹤器: {type(self.system['power_tracker']).__name__}")
        print(f"   - 人力分攤器: {type(self.system['labor_allocator']).__name__}")
        print(f"   - 實時監控器: {type(self.system['cost_monitor']).__name__}")
        print(f"   - 計算服務: {type(self.system['calculation_service']).__name__}")
        print(f"   - 分析引擎: {type(self.system['analytics']).__name__}")
        print()
    
    async def demo_hardware_cost_calculation(self):
        """演示硬體成本計算"""
        print("🔧 演示硬體成本計算")
        print("=" * 50)
        
        calculator = self.system['hardware_calculator']
        
        # 1. 創建GPU硬體資產
        gpu_asset = HardwareCostConfigurationFactory.create_gpu_inference_asset(
            asset_id="demo_gpu_001",
            model="RTX 4090",
            acquisition_cost=Decimal('2000.00'),
            expected_life_years=4
        )
        
        print(f"📦 創建GPU資產: {gpu_asset.name}")
        print(f"   - 資產ID: {gpu_asset.asset_id}")
        print(f"   - 採購成本: ${gpu_asset.acquisition_cost}")
        print(f"   - 預期壽命: {gpu_asset.expected_useful_life_years} 年")
        print(f"   - 年維護成本: ${gpu_asset.maintenance_cost_annual}")
        
        # 2. 註冊資產
        success = calculator.register_hardware_asset(gpu_asset)
        if success:
            print("✅ GPU資產註冊成功")
            
            # 3. 計算成本
            calculation_date = date.today()
            period_start = date.today() - timedelta(days=30)
            period_end = date.today()
            
            print(f"💰 計算期間: {period_start} 到 {period_end}")
            
            # 模擬使用數據
            usage_metrics = {
                'tokens_processed': 50000000,  # 5千萬tokens
                'compute_hours': 720.0,       # 720小時 (30天 * 24小時)
                'requests_served': 50000      # 5萬次請求
            }
            
            cost_result = await calculator.calculate_hardware_costs(
                gpu_asset.asset_id,
                calculation_date,
                period_start,
                period_end,
                usage_metrics
            )
            
            print(f"📊 成本計算結果:")
            print(f"   - 總成本: ${cost_result.total_cost:.2f}")
            print(f"   - 折舊成本: ${cost_result.depreciation_cost:.2f}")
            print(f"   - 維護成本: ${cost_result.maintenance_cost:.2f}")
            print(f"   - 設施成本: ${cost_result.facility_cost:.2f}")
            print(f"   - 保險成本: ${cost_result.insurance_cost:.2f}")
            print(f"   - 每Token成本: ${cost_result.cost_per_token:.8f}")
            print(f"   - 每小時成本: ${cost_result.cost_per_hour:.2f}")
            
            # 4. 生成優化建議
            recommendations = calculator.generate_cost_optimization_recommendations(
                gpu_asset.asset_id, cost_result
            )
            
            if recommendations:
                print(f"💡 優化建議 ({len(recommendations)} 項):")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec['type']}: {rec['description']}")
                    print(f"      潛在節省: ${rec['potential_savings']:.2f}")
        
        print()
    
    async def demo_power_maintenance_tracking(self):
        """演示電力和維護成本追蹤"""
        print("⚡ 演示電力和維護成本追蹤")
        print("=" * 50)
        
        tracker = self.system['power_tracker']
        
        # 1. 配置電價時程表
        price_schedule = PowerMaintenanceConfigurationFactory.create_standard_tou_price_schedule(
            price_id="demo_tou_pricing",
            peak_price=0.20,      # 峰時電價 $0.20/kWh
            off_peak_price=0.10,  # 離峰電價 $0.10/kWh
            demand_charge=20.0    # 需量費用 $20/kW
        )
        
        tracker.configure_electricity_price_schedule(price_schedule)
        print(f"💡 配置電價時程表: {price_schedule.name}")
        print(f"   - 峰時電價: ${price_schedule.peak_price_per_kwh}/kWh")
        print(f"   - 離峰電價: ${price_schedule.off_peak_price_per_kwh}/kWh")
        print(f"   - 需量費用: ${price_schedule.demand_charge_per_kw}/kW")
        
        # 2. 記錄電力消耗
        asset_id = "demo_gpu_001"
        
        print(f"🔌 模擬24小時電力消耗數據...")
        for hour in range(24):
            # 模擬不同時段的功耗變化
            base_power = 450.0  # 基礎功耗450W
            if 9 <= hour <= 17:  # 工作時間高負載
                power_consumption = base_power + 100.0
                utilization = 0.85
            elif 18 <= hour <= 22:  # 晚間中等負載
                power_consumption = base_power + 50.0
                utilization = 0.6
            else:  # 深夜低負載
                power_consumption = base_power
                utilization = 0.3
            
            await tracker.record_power_consumption(
                asset_id=asset_id,
                power_consumption_watts=power_consumption,
                voltage=230.0,
                current_amperes=power_consumption / 230.0,
                additional_data={
                    'temperature_celsius': 60.0 + utilization * 20,
                    'gpu_utilization': utilization,
                    'cpu_utilization': utilization * 0.5
                }
            )
        
        # 3. 記錄維護活動
        maintenance_schedule = PowerMaintenanceConfigurationFactory.create_preventive_maintenance_schedule(
            asset_id=asset_id,
            maintenance_interval_months=6
        )
        
        print(f"🔧 創建預防性維護計劃:")
        for i, maintenance_item in enumerate(maintenance_schedule[:3], 1):  # 只演示前3項
            maintenance_id = await tracker.record_maintenance(
                asset_id=maintenance_item['asset_id'],
                maintenance_type=maintenance_item['maintenance_type'],
                scheduled_date=maintenance_item['scheduled_date'],
                description=maintenance_item['description'],
                labor_cost=Decimal(str(maintenance_item['estimated_labor_cost'])),
                parts_cost=Decimal(str(maintenance_item['estimated_parts_cost']))
            )
            print(f"   {i}. {maintenance_item['description']}")
            print(f"      預計成本: ${maintenance_item['estimated_labor_cost'] + maintenance_item['estimated_parts_cost']}")
        
        # 4. 計算綜合成本
        start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        end_time = datetime.now(timezone.utc)
        
        cost_result = await tracker.calculate_comprehensive_costs(
            asset_id, start_time, end_time, "demo_tou_pricing"
        )
        
        print(f"📊 24小時綜合成本分析:")
        print(f"   - 總成本: ${cost_result.total_cost:.2f}")
        print(f"   - 電力成本: ${cost_result.total_electricity_cost:.2f}")
        print(f"   - 維護成本: ${cost_result.total_maintenance_cost:.2f}")
        print(f"   - 散熱成本: ${cost_result.cooling_cost:.2f}")
        print(f"   - UPS成本: ${cost_result.ups_cost:.2f}")
        print(f"   - 總耗電量: {cost_result.total_energy_consumption_kwh:.2f} kWh")
        print(f"   - 平均功耗: {cost_result.average_power_consumption_watts:.0f} W")
        print(f"   - 峰值需量: {cost_result.peak_demand_kw:.2f} kW")
        if cost_result.power_usage_effectiveness:
            print(f"   - PUE值: {cost_result.power_usage_effectiveness:.2f}")
        
        print()
    
    async def demo_labor_cost_allocation(self):
        """演示人力成本分攤"""
        print("👥 演示人力成本分攤")
        print("=" * 50)
        
        allocator = self.system['labor_allocator']
        
        # 1. 註冊員工
        employees_data = [
            {
                'id': 'demo_emp_001',
                'name': '張小明',
                'role': EmployeeRole.AI_ENGINEER,
                'skill': SkillLevel.SENIOR,
                'salary': 150000
            },
            {
                'id': 'demo_emp_002', 
                'name': '李小華',
                'role': EmployeeRole.DEVOPS_ENGINEER,
                'skill': SkillLevel.INTERMEDIATE,
                'salary': 120000
            },
            {
                'id': 'demo_emp_003',
                'name': '王小強',
                'role': EmployeeRole.SYSTEM_ADMINISTRATOR,
                'skill': SkillLevel.SENIOR,
                'salary': 110000
            }
        ]
        
        print(f"👤 註冊員工:")
        for emp_data in employees_data:
            employee = LaborCostConfigurationFactory.create_standard_employee(
                employee_id=emp_data['id'],
                name=emp_data['name'],
                role=emp_data['role'],
                skill_level=emp_data['skill'],
                base_salary=emp_data['salary']
            )
            
            success = allocator.register_employee(employee)
            if success:
                print(f"   ✅ {employee.name} ({employee.role.value})")
                print(f"      技能等級: {employee.skill_level.value}")
                print(f"      年度成本: ${employee.total_annual_cost:.2f}")
                print(f"      小時費率: ${employee.billable_hourly_rate:.2f}")
        
        # 2. 記錄工作活動
        cost_center_id = uuid.uuid4()
        print(f"\n📝 記錄工作活動 (成本中心: {cost_center_id})")
        
        activities = []
        for i, emp_data in enumerate(employees_data):
            # 為每個員工創建一週的工作活動
            for day in range(5):  # 工作日
                start_time = datetime.now(timezone.utc) - timedelta(days=7-day, hours=16)  # 8小時前
                end_time = datetime.now(timezone.utc) - timedelta(days=7-day, hours=8)    # 現在
                
                activity_types = [ActivityType.DEVELOPMENT, ActivityType.MAINTENANCE, ActivityType.TESTING]
                activity_type = activity_types[i % len(activity_types)]
                
                activity_id = await allocator.record_work_activity(
                    employee_id=emp_data['id'],
                    activity_type=activity_type,
                    start_time=start_time,
                    end_time=end_time,
                    description=f"{activity_type.value.replace('_', ' ').title()} work - Day {day+1}",
                    cost_center_id=cost_center_id,
                    additional_data={
                        'quality_score': 0.8 + (i * 0.05),  # 不同品質分數
                        'deliverables': [f'Report-{day+1}', f'Analysis-{day+1}'],
                        'impact_metrics': {
                            'performance_improvement': 0.1 + (day * 0.02),
                            'efficiency_gain': 0.05 + (i * 0.01)
                        }
                    }
                )
                
                # 審批活動
                await allocator.approve_work_activity(activity_id, "manager_demo")
                activities.append(activity_id)
        
        print(f"   記錄了 {len(activities)} 項工作活動")
        
        # 3. 創建分攤規則
        allocation_rule = LaborCostConfigurationFactory.create_time_based_allocation_rule(
            rule_id="demo_time_allocation",
            target_cost_centers=[cost_center_id]
        )
        
        allocator.create_allocation_rule(allocation_rule)
        print(f"📋 創建分攤規則: {allocation_rule.name}")
        
        # 4. 計算成本分攤
        print(f"\n💰 計算人力成本分攤:")
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        total_labor_cost = Decimal('0')
        for emp_data in employees_data:
            cost_result = await allocator.calculate_labor_cost_allocation(
                emp_data['id'], start_date, end_date, "demo_time_allocation"
            )
            
            print(f"   {emp_data['name']}:")
            print(f"      總成本: ${cost_result.total_cost:.2f}")
            print(f"      工作時數: {cost_result.total_hours_worked:.1f}h")
            print(f"      利用率: {cost_result.utilization_rate:.1%}")
            print(f"      生產力分數: {cost_result.productivity_score:.2f}")
            if cost_result.average_quality_score:
                print(f"      平均品質: {cost_result.average_quality_score:.2f}")
            
            total_labor_cost += cost_result.total_cost
        
        print(f"\n📊 人力成本摘要:")
        print(f"   - 總人力成本: ${total_labor_cost:.2f}")
        print(f"   - 平均每人成本: ${total_labor_cost / len(employees_data):.2f}")
        
        # 5. 生成分析報告
        analysis_result = allocator.generate_labor_cost_analysis(
            start_date, end_date, [emp['id'] for emp in employees_data]
        )
        
        if analysis_result:
            print(f"📈 人力成本分析:")
            summary = analysis_result['summary']
            print(f"   - 分析期間: {summary['total_hours']:.1f} 工作小時")
            print(f"   - 平均利用率: {summary['average_utilization_rate']:.1%}")
            print(f"   - 平均生產力: {summary['average_productivity_score']:.2f}")
        
        print()
    
    async def demo_realtime_monitoring(self):
        """演示實時成本監控"""
        print("📊 演示實時成本監控")
        print("=" * 50)
        
        monitor = self.system['cost_monitor']
        
        # 1. 創建告警規則
        cost_threshold_rule = AlertConfigurationFactory.create_cost_threshold_rule(
            rule_id="demo_cost_threshold",
            target_ids=["demo_gpu_001"],
            threshold_amount=100.0,
            severity=AlertSeverity.WARNING
        )
        
        utilization_rule = AlertConfigurationFactory.create_utilization_rule(
            rule_id="demo_utilization_alert", 
            target_ids=["demo_gpu_001"],
            minimum_utilization=0.5,
            severity=AlertSeverity.INFO
        )
        
        monitor.create_alert_rule(cost_threshold_rule)
        monitor.create_alert_rule(utilization_rule)
        
        print(f"⚠️ 創建告警規則:")
        print(f"   1. 成本閾值告警: ${cost_threshold_rule.threshold_value}")
        print(f"   2. 利用率告警: {utilization_rule.threshold_value:.0%} 最小利用率")
        
        # 2. 啟動監控
        print(f"\n🔍 啟動實時監控...")
        await monitor.start_monitoring()
        
        # 3. 模擬監控運行
        print(f"⏱️  監控運行中 (模擬5秒)...")
        await asyncio.sleep(5)
        
        # 4. 檢查健康狀態
        health_status = await monitor.health_check()
        print(f"💚 監控系統健康狀態: {health_status['status']}")
        print(f"   - 活躍告警數: {len(monitor.active_alerts)}")
        print(f"   - 告警規則數: {len(monitor.alert_rules)}")
        print(f"   - 指標歷史數: {len(monitor.metrics_history)}")
        
        # 5. 停止監控
        await monitor.stop_monitoring()
        print(f"⏹️  監控已停止")
        
        print()
    
    async def demo_cost_calculation_service(self):
        """演示成本計算服務"""
        print("🧮 演示成本計算服務")
        print("=" * 50)
        
        service = self.system['calculation_service']
        
        # 1. 快速成本摘要
        print(f"📋 快速成本摘要:")
        summary = await service.quick_cost_summary(
            target_ids=["demo_gpu_001"],
            days_back=7
        )
        
        if 'error' not in summary:
            print(f"   - 7天總成本: ${summary['total_cost']:.2f}")
            print(f"   - 日均成本: ${summary['daily_average']:.2f}")
            print(f"   - 成本分解: {len(summary['cost_breakdown'])} 個類別")
        else:
            print(f"   ⚠️ {summary['error']}")
        
        # 2. 成本比較分析
        print(f"\n📊 成本比較分析:")
        comparison = await service.cost_comparison(
            target_ids=["demo_gpu_001"],
            current_period_days=7,
            comparison_period_days=7
        )
        
        if 'error' not in comparison:
            print(f"   - 當前期間成本: ${comparison['current_period']['total_cost']:.2f}")
            print(f"   - 比較期間成本: ${comparison['comparison_period']['total_cost']:.2f}")
            print(f"   - 成本變化: ${comparison['cost_change']:.2f} ({comparison['change_percentage']:.1f}%)")
            print(f"   - 變化方向: {comparison['change_direction']}")
        
        # 3. 完整成本計算
        print(f"\n💰 完整成本計算:")
        request = CostCalculationRequest(
            calculation_id="demo_comprehensive_calc",
            scope=CalculationScope.ASSET,
            target_ids=["demo_gpu_001"],
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            include_hardware_costs=True,
            include_power_costs=True,
            include_maintenance_costs=True,
            include_labor_costs=True,
            include_trends=True,
            include_optimizations=True
        )
        
        result = await service.calculate_costs(request)
        
        print(f"   計算ID: {result.calculation_id}")
        print(f"   計算時間: {result.calculation_duration_ms:.2f}ms")
        print(f"   總成本: ${result.total_cost:.2f}")
        print(f"   成本分解:")
        print(f"      - 硬體: ${result.hardware_costs:.2f}")
        print(f"      - 電力: ${result.power_costs:.2f}")
        print(f"      - 維護: ${result.maintenance_costs:.2f}")
        print(f"      - 人力: ${result.labor_costs:.2f}")
        print(f"      - 其他: ${result.other_costs:.2f}")
        print(f"   信心度: {result.confidence_score:.2f}")
        
        if result.optimization_suggestions:
            print(f"   💡 優化建議: {len(result.optimization_suggestions)} 項")
            for i, suggestion in enumerate(result.optimization_suggestions[:2], 1):
                print(f"      {i}. {suggestion['description']}")
        
        print()
    
    async def demo_cost_analytics(self):
        """演示成本分析"""
        print("📈 演示成本分析")
        print("=" * 50)
        
        analytics = self.system['analytics']
        
        # 1. 添加模擬分析數據
        print(f"📊 添加模擬成本數據...")
        data_points = []
        
        # 生成30天的成本數據
        for i in range(30):
            timestamp = datetime.now(timezone.utc) - timedelta(days=30-i)
            
            # 模擬不同的成本模式
            base_cost = 100.0
            trend_factor = i * 2.0  # 線性增長趨勢
            noise = (i % 7) * 10.0  # 週期性變化
            
            for asset_id in ["demo_gpu_001", "demo_gpu_002"]:
                for category in ["hardware", "power", "maintenance"]:
                    cost_multiplier = {"hardware": 1.0, "power": 0.6, "maintenance": 0.3}[category]
                    
                    amount = base_cost * cost_multiplier + trend_factor + noise
                    
                    data_points.append(CostDataPoint(
                        timestamp=timestamp,
                        target_id=asset_id,
                        cost_category=category,
                        amount=Decimal(str(amount)),
                        units=50.0 if category == "power" else None
                    ))
        
        analytics.add_cost_data(data_points)
        print(f"   添加了 {len(data_points)} 個數據點")
        
        # 2. 成本差異分析
        print(f"\n📊 成本差異分析:")
        variance_request = AnalysisRequest(
            analysis_id="demo_variance_analysis",
            analysis_type=AnalysisType.COST_VARIANCE,
            dimensions=[AnalysisDimension.TIME, AnalysisDimension.COST_CATEGORY],
            target_ids=["demo_gpu_001", "demo_gpu_002"],
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            aggregation_level="daily"
        )
        
        variance_result = await analytics.perform_analysis(variance_request)
        
        if variance_result.summary_statistics:
            stats = variance_result.summary_statistics
            print(f"   - 平均成本: ${stats.get('mean_cost', 0):.2f}")
            print(f"   - 標準差: ${stats.get('std_deviation', 0):.2f}")
            print(f"   - 變異係數: {stats.get('coefficient_variation', 0):.3f}")
            print(f"   - 成本範圍: ${stats.get('cost_range', 0):.2f}")
        
        if variance_result.variances:
            print(f"   📈 發現 {len(variance_result.variances)} 個顯著差異")
            for var in variance_result.variances[:2]:  # 顯示前2個
                print(f"      期間 {var['period']}: {var['variance_percentage']:+.1f}%")
        
        # 3. 預測分析
        print(f"\n🔮 成本預測分析:")
        forecast_request = AnalysisRequest(
            analysis_id="demo_forecast_analysis",
            analysis_type=AnalysisType.FORECAST,
            dimensions=[AnalysisDimension.TIME],
            target_ids=["demo_gpu_001"],
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            include_predictions=True,
            prediction_horizon_days=15
        )
        
        forecast_result = await analytics.perform_analysis(forecast_request)
        
        if forecast_result.forecasts:
            forecasts = forecast_result.forecasts
            print(f"   預測模型: {forecasts.get('model', 'unknown')}")
            print(f"   歷史期間: {forecasts.get('historical_periods', 0)} 個")
            
            predictions = forecasts.get('predictions', [])[:3]  # 顯示前3個預測
            for pred in predictions:
                print(f"   第 {pred['period']} 期: ${pred['predicted_value']:.2f} (信心度: {pred['confidence']:.2f})")
        
        # 4. 洞察總結
        if variance_result.insights or forecast_result.insights:
            print(f"\n💡 自動洞察:")
            all_insights = variance_result.insights + forecast_result.insights
            for i, insight in enumerate(all_insights[:3], 1):  # 顯示前3個洞察
                print(f"   {i}. {insight['message']}")
        
        print()
    
    async def run_complete_demo(self):
        """運行完整演示"""
        print("🚀 GPT-OSS 成本追蹤系統完整演示")
        print("=" * 80)
        print("本演示將展示企業級成本追蹤系統的完整功能：")
        print("1. 硬體成本計算和折舊管理")
        print("2. 電力和維護成本追蹤") 
        print("3. 人力成本分攤機制")
        print("4. 實時成本監控和告警")
        print("5. 成本計算服務API")
        print("6. 成本分析和商業智能")
        print("=" * 80)
        print()
        
        try:
            # 依次執行各個演示
            await self.demo_hardware_cost_calculation()
            await self.demo_power_maintenance_tracking()
            await self.demo_labor_cost_allocation()
            await self.demo_realtime_monitoring()
            await self.demo_cost_calculation_service()
            await self.demo_cost_analytics()
            
            # 系統健康檢查
            print("🏥 系統健康檢查")
            print("=" * 50)
            
            total_components = len(self.system)
            healthy_components = 0
            
            for component_name, component in self.system.items():
                if hasattr(component, 'health_check'):
                    health = await component.health_check()
                    status = health.get('status', 'unknown')
                    print(f"   {component_name}: {status}")
                    if status == 'healthy':
                        healthy_components += 1
                else:
                    print(f"   {component_name}: not_checkable")
            
            print(f"\n📊 健康摘要: {healthy_components}/{total_components} 組件健康")
            
            print("\n" + "=" * 80)
            print("✅ GPT-OSS 成本追蹤系統演示完成！")
            print("系統已準備好用於生產環境的企業級成本管理。")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 演示過程中發生錯誤: {e}")
            print("請檢查系統配置和依賴項。")


# ==================== 主執行入口 ====================

async def main():
    """主演示函數"""
    print("🎯 啟動 GPT-OSS 成本追蹤系統演示")
    print()
    
    demo = CostTrackingDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # 運行演示
    asyncio.run(main())