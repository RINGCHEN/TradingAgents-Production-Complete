"""
Cost-Benefit Calculation Engine
成本效益計算引擎

任務6.2: 成本效益計算引擎
負責人: 小k (AI訓練專家團隊)

提供：
- 本地GPU vs 雲端API成本對比
- ROI計算和投資回報分析
- 資源利用率成本分析
- 動態成本預測
- 成本優化建議
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import numpy as np
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class CostType(Enum):
    """成本類型枚舉"""
    HARDWARE = "hardware"           # 硬體成本
    ELECTRICITY = "electricity"     # 電力成本
    MAINTENANCE = "maintenance"     # 維護成本
    CLOUD_API = "cloud_api"        # 雲端API成本
    PERSONNEL = "personnel"         # 人力成本
    INFRASTRUCTURE = "infrastructure"  # 基礎設施成本
    OPPORTUNITY = "opportunity"     # 機會成本

class DeploymentMode(Enum):
    """部署模式枚舉"""
    LOCAL_GPU = "local_gpu"        # 本地GPU
    CLOUD_API = "cloud_api"        # 雲端API
    HYBRID = "hybrid"              # 混合模式

class TimeUnit(Enum):
    """時間單位枚舉"""
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"
    YEAR = "year"

@dataclass
class HardwareSpec:
    """硬體規格數據結構"""
    gpu_model: str
    gpu_memory_gb: float
    gpu_count: int
    cpu_cores: int
    system_memory_gb: float
    storage_gb: float
    purchase_price_usd: float
    power_consumption_watts: float
    expected_lifespan_years: float = 3.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CloudAPISpec:
    """雲端API規格數據結構"""
    provider: str
    model_name: str
    input_token_price_per_1k: Decimal
    output_token_price_per_1k: Decimal
    request_price: Decimal = Decimal('0')
    rate_limit_per_minute: int = 60
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # 轉換Decimal為字符串以便JSON序列化
        for key, value in result.items():
            if isinstance(value, Decimal):
                result[key] = str(value)
        return result

@dataclass
class TaskWorkload:
    """任務工作負載數據結構"""
    task_name: str
    input_tokens_per_request: int
    output_tokens_per_request: int
    requests_per_hour: int
    gpu_utilization_percent: float
    processing_time_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CostBreakdown:
    """成本分解數據結構"""
    hardware_cost: Decimal = Decimal('0')
    electricity_cost: Decimal = Decimal('0')
    maintenance_cost: Decimal = Decimal('0')
    cloud_api_cost: Decimal = Decimal('0')
    personnel_cost: Decimal = Decimal('0')
    infrastructure_cost: Decimal = Decimal('0')
    opportunity_cost: Decimal = Decimal('0')
    
    @property
    def total_cost(self) -> Decimal:
        return (
            self.hardware_cost + self.electricity_cost + self.maintenance_cost +
            self.cloud_api_cost + self.personnel_cost + self.infrastructure_cost +
            self.opportunity_cost
        )
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['total_cost'] = str(self.total_cost)
        # 轉換Decimal為字符串
        for key, value in result.items():
            if isinstance(value, Decimal):
                result[key] = str(value)
        return result

@dataclass
class ROIAnalysis:
    """ROI分析數據結構"""
    initial_investment: Decimal
    annual_savings: Decimal
    annual_revenue_increase: Decimal
    payback_period_months: float
    roi_percentage: float
    net_present_value: Decimal
    internal_rate_of_return: float
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        # 轉換Decimal為字符串
        for key, value in result.items():
            if isinstance(value, Decimal):
                result[key] = str(value)
        return result

@dataclass
class CostComparisonResult:
    """成本對比結果數據結構"""
    local_gpu_cost: CostBreakdown
    cloud_api_cost: CostBreakdown
    hybrid_cost: CostBreakdown
    cost_savings: Decimal
    cost_savings_percentage: float
    recommended_deployment: DeploymentMode
    roi_analysis: ROIAnalysis
    analysis_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['recommended_deployment'] = self.recommended_deployment.value
        result['cost_savings'] = str(self.cost_savings)
        return result

class HardwareCostCalculator:
    """硬體成本計算器"""
    
    def __init__(self):
        # 預定義硬體規格
        self.hardware_specs = {
            'rtx_4070': HardwareSpec(
                gpu_model='RTX 4070',
                gpu_memory_gb=12.0,
                gpu_count=1,
                cpu_cores=8,
                system_memory_gb=32.0,
                storage_gb=1000.0,
                purchase_price_usd=600.0,
                power_consumption_watts=200.0,
                expected_lifespan_years=3.0
            ),
            'rtx_4090': HardwareSpec(
                gpu_model='RTX 4090',
                gpu_memory_gb=24.0,
                gpu_count=1,
                cpu_cores=16,
                system_memory_gb=64.0,
                storage_gb=2000.0,
                purchase_price_usd=1600.0,
                power_consumption_watts=450.0,
                expected_lifespan_years=3.0
            ),
            'a100_40gb': HardwareSpec(
                gpu_model='A100 40GB',
                gpu_memory_gb=40.0,
                gpu_count=1,
                cpu_cores=32,
                system_memory_gb=128.0,
                storage_gb=4000.0,
                purchase_price_usd=10000.0,
                power_consumption_watts=400.0,
                expected_lifespan_years=4.0
            )
        }
        
        # 電力成本（每kWh美元）
        self.electricity_rate_per_kwh = Decimal('0.12')  # 美國平均電價
        
        # 維護成本係數（年度硬體成本的百分比）
        self.maintenance_cost_percentage = Decimal('0.05')  # 5%
    
    def calculate_hardware_cost(
        self,
        hardware_spec: HardwareSpec,
        time_period_hours: float
    ) -> Decimal:
        """計算硬體成本"""
        # 折舊成本（按小時計算）
        total_hours_lifespan = hardware_spec.expected_lifespan_years * 365 * 24
        depreciation_per_hour = Decimal(str(hardware_spec.purchase_price_usd)) / Decimal(str(total_hours_lifespan))
        
        return depreciation_per_hour * Decimal(str(time_period_hours))
    
    def calculate_electricity_cost(
        self,
        hardware_spec: HardwareSpec,
        time_period_hours: float,
        utilization_percentage: float = 100.0
    ) -> Decimal:
        """計算電力成本"""
        # 功耗（kW）
        power_kw = Decimal(str(hardware_spec.power_consumption_watts)) / Decimal('1000')
        
        # 實際使用功耗（考慮利用率）
        actual_power_kw = power_kw * Decimal(str(utilization_percentage)) / Decimal('100')
        
        # 電力成本
        electricity_cost = actual_power_kw * Decimal(str(time_period_hours)) * self.electricity_rate_per_kwh
        
        return electricity_cost
    
    def calculate_maintenance_cost(
        self,
        hardware_spec: HardwareSpec,
        time_period_hours: float
    ) -> Decimal:
        """計算維護成本"""
        # 年度維護成本
        annual_maintenance = Decimal(str(hardware_spec.purchase_price_usd)) * self.maintenance_cost_percentage
        
        # 按小時計算
        maintenance_per_hour = annual_maintenance / Decimal(str(365 * 24))
        
        return maintenance_per_hour * Decimal(str(time_period_hours))

class CloudAPICostCalculator:
    """雲端API成本計算器"""
    
    def __init__(self):
        # 預定義雲端API規格
        self.api_specs = {
            'openai_gpt4': CloudAPISpec(
                provider='OpenAI',
                model_name='GPT-4',
                input_token_price_per_1k=Decimal('0.03'),
                output_token_price_per_1k=Decimal('0.06'),
                rate_limit_per_minute=500
            ),
            'openai_gpt3_5': CloudAPISpec(
                provider='OpenAI',
                model_name='GPT-3.5-turbo',
                input_token_price_per_1k=Decimal('0.001'),
                output_token_price_per_1k=Decimal('0.002'),
                rate_limit_per_minute=3500
            ),
            'anthropic_claude': CloudAPISpec(
                provider='Anthropic',
                model_name='Claude-3',
                input_token_price_per_1k=Decimal('0.015'),
                output_token_price_per_1k=Decimal('0.075'),
                rate_limit_per_minute=1000
            ),
            'google_gemini': CloudAPISpec(
                provider='Google',
                model_name='Gemini Pro',
                input_token_price_per_1k=Decimal('0.001'),
                output_token_price_per_1k=Decimal('0.002'),
                rate_limit_per_minute=1000
            )
        }
    
    def calculate_api_cost(
        self,
        api_spec: CloudAPISpec,
        workload: TaskWorkload,
        time_period_hours: float
    ) -> Decimal:
        """計算API成本"""
        # 總請求數
        total_requests = Decimal(str(workload.requests_per_hour * time_period_hours))
        
        # 總輸入token數
        total_input_tokens = total_requests * Decimal(str(workload.input_tokens_per_request))
        
        # 總輸出token數
        total_output_tokens = total_requests * Decimal(str(workload.output_tokens_per_request))
        
        # 輸入token成本
        input_cost = (total_input_tokens / Decimal('1000')) * api_spec.input_token_price_per_1k
        
        # 輸出token成本
        output_cost = (total_output_tokens / Decimal('1000')) * api_spec.output_token_price_per_1k
        
        # 請求成本
        request_cost = total_requests * api_spec.request_price
        
        return input_cost + output_cost + request_cost
    
    def estimate_rate_limit_impact(
        self,
        api_spec: CloudAPISpec,
        workload: TaskWorkload
    ) -> Dict[str, Any]:
        """估算速率限制影響"""
        requests_per_minute = workload.requests_per_hour / 60
        
        if requests_per_minute > api_spec.rate_limit_per_minute:
            # 需要排隊等待
            queue_delay_factor = requests_per_minute / api_spec.rate_limit_per_minute
            additional_time_hours = (queue_delay_factor - 1) * workload.processing_time_seconds / 3600
            
            return {
                'rate_limited': True,
                'queue_delay_factor': queue_delay_factor,
                'additional_time_hours': additional_time_hours,
                'effective_throughput': api_spec.rate_limit_per_minute * 60  # 每小時
            }
        else:
            return {
                'rate_limited': False,
                'queue_delay_factor': 1.0,
                'additional_time_hours': 0.0,
                'effective_throughput': workload.requests_per_hour
            }

class CostCalculator:
    """成本效益計算引擎主類"""
    
    def __init__(self):
        self.hardware_calculator = HardwareCostCalculator()
        self.cloud_calculator = CloudAPICostCalculator()
        self.calculation_history = []
        
        # 人力成本（每小時美元）
        self.personnel_cost_per_hour = Decimal('50.0')  # AI工程師平均時薪
        
        # 基礎設施成本（每月美元）
        self.infrastructure_cost_per_month = Decimal('200.0')  # 網路、存儲等
    
    def calculate_local_gpu_cost(
        self,
        hardware_spec: HardwareSpec,
        workload: TaskWorkload,
        time_period_hours: float,
        personnel_hours: float = 0.0
    ) -> CostBreakdown:
        """計算本地GPU成本"""
        cost_breakdown = CostBreakdown()
        
        # 硬體成本
        cost_breakdown.hardware_cost = self.hardware_calculator.calculate_hardware_cost(
            hardware_spec, time_period_hours
        )
        
        # 電力成本
        cost_breakdown.electricity_cost = self.hardware_calculator.calculate_electricity_cost(
            hardware_spec, time_period_hours, workload.gpu_utilization_percent
        )
        
        # 維護成本
        cost_breakdown.maintenance_cost = self.hardware_calculator.calculate_maintenance_cost(
            hardware_spec, time_period_hours
        )
        
        # 人力成本
        cost_breakdown.personnel_cost = self.personnel_cost_per_hour * Decimal(str(personnel_hours))
        
        # 基礎設施成本（按小時分攤）
        hours_per_month = Decimal('730')  # 平均每月小時數
        cost_breakdown.infrastructure_cost = (
            self.infrastructure_cost_per_month * Decimal(str(time_period_hours)) / hours_per_month
        )
        
        return cost_breakdown
    
    def calculate_cloud_api_cost(
        self,
        api_spec: CloudAPISpec,
        workload: TaskWorkload,
        time_period_hours: float,
        personnel_hours: float = 0.0
    ) -> CostBreakdown:
        """計算雲端API成本"""
        cost_breakdown = CostBreakdown()
        
        # API成本
        cost_breakdown.cloud_api_cost = self.cloud_calculator.calculate_api_cost(
            api_spec, workload, time_period_hours
        )
        
        # 人力成本（通常較少，因為無需維護硬體）
        cost_breakdown.personnel_cost = self.personnel_cost_per_hour * Decimal(str(personnel_hours * 0.3))
        
        # 基礎設施成本（較少，主要是網路）
        hours_per_month = Decimal('730')
        cost_breakdown.infrastructure_cost = (
            self.infrastructure_cost_per_month * Decimal('0.2') * Decimal(str(time_period_hours)) / hours_per_month
        )
        
        return cost_breakdown
    
    def calculate_hybrid_cost(
        self,
        hardware_spec: HardwareSpec,
        api_spec: CloudAPISpec,
        workload: TaskWorkload,
        time_period_hours: float,
        local_gpu_percentage: float = 70.0,
        personnel_hours: float = 0.0
    ) -> CostBreakdown:
        """計算混合模式成本"""
        # 本地GPU處理的工作負載
        local_workload = TaskWorkload(
            task_name=workload.task_name,
            input_tokens_per_request=workload.input_tokens_per_request,
            output_tokens_per_request=workload.output_tokens_per_request,
            requests_per_hour=int(workload.requests_per_hour * local_gpu_percentage / 100),
            gpu_utilization_percent=workload.gpu_utilization_percent,
            processing_time_seconds=workload.processing_time_seconds
        )
        
        # 雲端API處理的工作負載
        cloud_workload = TaskWorkload(
            task_name=workload.task_name,
            input_tokens_per_request=workload.input_tokens_per_request,
            output_tokens_per_request=workload.output_tokens_per_request,
            requests_per_hour=int(workload.requests_per_hour * (100 - local_gpu_percentage) / 100),
            gpu_utilization_percent=0,
            processing_time_seconds=workload.processing_time_seconds
        )
        
        # 計算各部分成本
        local_cost = self.calculate_local_gpu_cost(
            hardware_spec, local_workload, time_period_hours, personnel_hours
        )
        
        cloud_cost = self.calculate_cloud_api_cost(
            api_spec, cloud_workload, time_period_hours, personnel_hours * 0.3
        )
        
        # 合併成本
        hybrid_cost = CostBreakdown(
            hardware_cost=local_cost.hardware_cost,
            electricity_cost=local_cost.electricity_cost,
            maintenance_cost=local_cost.maintenance_cost,
            cloud_api_cost=cloud_cost.cloud_api_cost,
            personnel_cost=local_cost.personnel_cost + cloud_cost.personnel_cost,
            infrastructure_cost=local_cost.infrastructure_cost + cloud_cost.infrastructure_cost
        )
        
        return hybrid_cost
    
    def calculate_roi_analysis(
        self,
        initial_investment: Decimal,
        annual_cost_savings: Decimal,
        annual_revenue_increase: Decimal = Decimal('0'),
        discount_rate: float = 0.1,
        analysis_years: int = 3
    ) -> ROIAnalysis:
        """計算ROI分析"""
        # 年度總收益
        annual_benefit = annual_cost_savings + annual_revenue_increase
        
        # 投資回收期（月）
        if annual_benefit > 0:
            payback_period_months = float(initial_investment / annual_benefit * 12)
        else:
            payback_period_months = float('inf')
        
        # ROI百分比
        if initial_investment > 0:
            roi_percentage = float(annual_benefit / initial_investment * 100)
        else:
            roi_percentage = 0.0
        
        # 淨現值計算
        npv = -initial_investment
        for year in range(1, analysis_years + 1):
            npv += annual_benefit / Decimal(str((1 + discount_rate) ** year))
        
        # 內部收益率（簡化計算）
        if initial_investment > 0:
            irr = float(annual_benefit / initial_investment - 1) * 100
        else:
            irr = 0.0
        
        return ROIAnalysis(
            initial_investment=initial_investment,
            annual_savings=annual_cost_savings,
            annual_revenue_increase=annual_revenue_increase,
            payback_period_months=payback_period_months,
            roi_percentage=roi_percentage,
            net_present_value=npv,
            internal_rate_of_return=irr
        )
    
    def compare_deployment_costs(
        self,
        hardware_spec: HardwareSpec,
        api_spec: CloudAPISpec,
        workload: TaskWorkload,
        time_period_hours: float = 8760,  # 一年
        personnel_hours: float = 40.0,    # 每年40小時維護
        hybrid_local_percentage: float = 70.0
    ) -> CostComparisonResult:
        """對比不同部署模式的成本"""
        logger.info(f"🔍 開始成本對比分析: {workload.task_name}")
        
        # 計算各種部署模式的成本
        local_gpu_cost = self.calculate_local_gpu_cost(
            hardware_spec, workload, time_period_hours, personnel_hours
        )
        
        cloud_api_cost = self.calculate_cloud_api_cost(
            api_spec, workload, time_period_hours, personnel_hours * 0.3
        )
        
        hybrid_cost = self.calculate_hybrid_cost(
            hardware_spec, api_spec, workload, time_period_hours,
            hybrid_local_percentage, personnel_hours
        )
        
        # 確定最佳部署模式
        costs = {
            DeploymentMode.LOCAL_GPU: local_gpu_cost.total_cost,
            DeploymentMode.CLOUD_API: cloud_api_cost.total_cost,
            DeploymentMode.HYBRID: hybrid_cost.total_cost
        }
        
        recommended_deployment = min(costs, key=costs.get)
        
        # 計算成本節省
        if recommended_deployment == DeploymentMode.LOCAL_GPU:
            cost_savings = cloud_api_cost.total_cost - local_gpu_cost.total_cost
            baseline_cost = cloud_api_cost.total_cost
        elif recommended_deployment == DeploymentMode.HYBRID:
            cost_savings = max(local_gpu_cost.total_cost, cloud_api_cost.total_cost) - hybrid_cost.total_cost
            baseline_cost = max(local_gpu_cost.total_cost, cloud_api_cost.total_cost)
        else:
            cost_savings = local_gpu_cost.total_cost - cloud_api_cost.total_cost
            baseline_cost = local_gpu_cost.total_cost
        
        # 成本節省百分比
        if baseline_cost > 0:
            cost_savings_percentage = float(cost_savings / baseline_cost * 100)
        else:
            cost_savings_percentage = 0.0
        
        # ROI分析（假設本地GPU需要初始投資）
        initial_investment = Decimal(str(hardware_spec.purchase_price_usd))
        annual_savings = cost_savings if time_period_hours >= 8760 else cost_savings * Decimal('8760') / Decimal(str(time_period_hours))
        
        roi_analysis = self.calculate_roi_analysis(
            initial_investment, annual_savings
        )
        
        # 創建對比結果
        result = CostComparisonResult(
            local_gpu_cost=local_gpu_cost,
            cloud_api_cost=cloud_api_cost,
            hybrid_cost=hybrid_cost,
            cost_savings=cost_savings,
            cost_savings_percentage=cost_savings_percentage,
            recommended_deployment=recommended_deployment,
            roi_analysis=roi_analysis,
            analysis_timestamp=datetime.now().isoformat()
        )
        
        # 添加到歷史記錄
        self.calculation_history.append(result)
        
        logger.info(f"✅ 成本對比完成: 推薦 {recommended_deployment.value}, 節省 {cost_savings_percentage:.1f}%")
        return result
    
    def generate_cost_optimization_suggestions(
        self,
        comparison_result: CostComparisonResult,
        workload: TaskWorkload
    ) -> List[str]:
        """生成成本優化建議"""
        suggestions = []
        
        # 基於推薦部署模式的建議
        if comparison_result.recommended_deployment == DeploymentMode.LOCAL_GPU:
            suggestions.append("建議使用本地GPU以獲得最佳成本效益")
            suggestions.append("考慮批量處理以提高GPU利用率")
            if workload.gpu_utilization_percent < 80:
                suggestions.append("當前GPU利用率較低，考慮並行處理多個任務")
        
        elif comparison_result.recommended_deployment == DeploymentMode.CLOUD_API:
            suggestions.append("建議使用雲端API以避免硬體投資")
            suggestions.append("考慮使用更便宜的API模型進行預處理")
            suggestions.append("實施智能緩存以減少重複API調用")
        
        elif comparison_result.recommended_deployment == DeploymentMode.HYBRID:
            suggestions.append("建議使用混合模式以平衡成本和性能")
            suggestions.append("將高頻任務分配給本地GPU，低頻任務使用雲端API")
            suggestions.append("實施智能路由以動態分配工作負載")
        
        # 基於成本結構的建議
        local_cost = comparison_result.local_gpu_cost
        if local_cost.electricity_cost > local_cost.hardware_cost:
            suggestions.append("電力成本較高，考慮使用更節能的硬體或優化運行時間")
        
        if local_cost.personnel_cost > local_cost.hardware_cost * Decimal('0.5'):
            suggestions.append("人力成本較高，考慮實施自動化運維以減少人工干預")
        
        # 基於ROI的建議
        roi = comparison_result.roi_analysis
        if roi.payback_period_months > 12:
            suggestions.append("投資回收期較長，考慮分階段投資或租賃硬體")
        
        if roi.roi_percentage < 50:
            suggestions.append("ROI較低，建議重新評估工作負載需求或考慮雲端方案")
        
        return suggestions
    
    def export_cost_analysis_report(
        self,
        comparison_result: CostComparisonResult,
        output_path: str,
        include_suggestions: bool = True
    ):
        """導出成本分析報告"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 準備報告數據
        report_data = {
            "analysis_summary": {
                "recommended_deployment": comparison_result.recommended_deployment.value,
                "cost_savings_usd": str(comparison_result.cost_savings),
                "cost_savings_percentage": comparison_result.cost_savings_percentage,
                "roi_percentage": comparison_result.roi_analysis.roi_percentage,
                "payback_period_months": comparison_result.roi_analysis.payback_period_months
            },
            "cost_breakdown": {
                "local_gpu": comparison_result.local_gpu_cost.to_dict(),
                "cloud_api": comparison_result.cloud_api_cost.to_dict(),
                "hybrid": comparison_result.hybrid_cost.to_dict()
            },
            "roi_analysis": comparison_result.roi_analysis.to_dict(),
            "analysis_timestamp": comparison_result.analysis_timestamp
        }
        
        # 添加優化建議
        if include_suggestions:
            suggestions = self.generate_cost_optimization_suggestions(
                comparison_result, 
                TaskWorkload("sample", 1000, 500, 100, 80.0, 2.0)  # 示例工作負載
            )
            report_data["optimization_suggestions"] = suggestions
        
        # 導出JSON報告
        with open(output_path / "cost_analysis_report.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        # 導出CSV摘要
        import csv
        with open(output_path / "cost_comparison_summary.csv", 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Deployment Mode', 'Total Cost (USD)', 'Hardware', 'Electricity', 'Cloud API', 'Personnel'])
            
            for mode, cost in [
                ('Local GPU', comparison_result.local_gpu_cost),
                ('Cloud API', comparison_result.cloud_api_cost),
                ('Hybrid', comparison_result.hybrid_cost)
            ]:
                writer.writerow([
                    mode,
                    str(cost.total_cost),
                    str(cost.hardware_cost),
                    str(cost.electricity_cost),
                    str(cost.cloud_api_cost),
                    str(cost.personnel_cost)
                ])
        
        logger.info(f"成本分析報告已導出到: {output_path}")

# 便利函數
def quick_cost_comparison(
    hardware_model: str = 'rtx_4070',
    api_model: str = 'openai_gpt3_5',
    requests_per_hour: int = 100,
    analysis_hours: float = 8760
) -> CostComparisonResult:
    """快速成本對比的便利函數"""
    calculator = CostCalculator()
    
    # 獲取硬體規格
    hardware_spec = calculator.hardware_calculator.hardware_specs.get(hardware_model)
    if not hardware_spec:
        raise ValueError(f"Unknown hardware model: {hardware_model}")
    
    # 獲取API規格
    api_spec = calculator.cloud_calculator.api_specs.get(api_model)
    if not api_spec:
        raise ValueError(f"Unknown API model: {api_model}")
    
    # 創建示例工作負載
    workload = TaskWorkload(
        task_name="sample_task",
        input_tokens_per_request=1000,
        output_tokens_per_request=500,
        requests_per_hour=requests_per_hour,
        gpu_utilization_percent=80.0,
        processing_time_seconds=2.0
    )
    
    return calculator.compare_deployment_costs(
        hardware_spec, api_spec, workload, analysis_hours
    )

def calculate_break_even_point(
    hardware_model: str = 'rtx_4070',
    api_model: str = 'openai_gpt3_5',
    requests_per_hour: int = 100
) -> Dict[str, Any]:
    """計算盈虧平衡點的便利函數"""
    calculator = CostCalculator()
    
    # 獲取規格
    hardware_spec = calculator.hardware_calculator.hardware_specs.get(hardware_model)
    api_spec = calculator.cloud_calculator.api_specs.get(api_model)
    
    if not hardware_spec or not api_spec:
        raise ValueError("Invalid hardware or API model")
    
    # 創建工作負載
    workload = TaskWorkload(
        task_name="break_even_analysis",
        input_tokens_per_request=1000,
        output_tokens_per_request=500,
        requests_per_hour=requests_per_hour,
        gpu_utilization_percent=80.0,
        processing_time_seconds=2.0
    )
    
    # 計算每小時成本差異
    local_cost_1h = calculator.calculate_local_gpu_cost(hardware_spec, workload, 1.0)
    cloud_cost_1h = calculator.calculate_cloud_api_cost(api_spec, workload, 1.0)
    
    hourly_savings = cloud_cost_1h.total_cost - local_cost_1h.total_cost
    
    # 計算盈虧平衡點
    initial_investment = Decimal(str(hardware_spec.purchase_price_usd))
    
    if hourly_savings > 0:
        break_even_hours = float(initial_investment / hourly_savings)
        break_even_days = break_even_hours / 24
        break_even_months = break_even_days / 30
    else:
        break_even_hours = float('inf')
        break_even_days = float('inf')
        break_even_months = float('inf')
    
    return {
        "initial_investment_usd": str(initial_investment),
        "hourly_savings_usd": str(hourly_savings),
        "break_even_hours": break_even_hours,
        "break_even_days": break_even_days,
        "break_even_months": break_even_months,
        "is_profitable": hourly_savings > 0
    }