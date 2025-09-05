#!/usr/bin/env python3
"""
API Cost Savings Calculator
API成本節省計算器

GPT-OSS整合任務2.1.3 - API成本節省計算服務
提供精確的本地GPT-OSS與雲端API成本比較和節省計算功能
"""

import asyncio
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

from .models import (
    APICostSaving, APICostSavingSchema,
    RevenueAttributionRecord, RevenueAttributionRecordSchema,
    RevenueType, AttributionMethod, RevenueConfidence
)

logger = logging.getLogger(__name__)


# ==================== 配置和常量 ====================

class APIProvider(str, Enum):
    """API提供商"""
    OPENAI_GPT4 = "openai_gpt4"
    OPENAI_GPT3_5 = "openai_gpt3_5"
    ANTHROPIC_CLAUDE = "anthropic_claude"
    ANTHROPIC_CLAUDE_HAIKU = "anthropic_claude_haiku"
    GPT_OSS_LOCAL = "gpt_oss_local"
    GPT_OSS_LLAMA_3_8B = "gpt_oss_llama_3_8b"


@dataclass
class APIPricingModel:
    """API定價模型"""
    provider: APIProvider
    input_price_per_1k_tokens: Decimal
    output_price_per_1k_tokens: Decimal
    request_base_cost: Decimal
    currency: str = "USD"
    effective_date: date = date.today()
    
    def calculate_cost(self, input_tokens: int, output_tokens: int, requests: int = 1) -> Decimal:
        """計算總成本"""
        input_cost = (Decimal(input_tokens) / 1000) * self.input_price_per_1k_tokens
        output_cost = (Decimal(output_tokens) / 1000) * self.output_price_per_1k_tokens
        request_cost = Decimal(requests) * self.request_base_cost
        
        return input_cost + output_cost + request_cost


@dataclass
class HardwareCostModel:
    """硬體成本模型"""
    hardware_name: str
    hourly_cost: Decimal  # 每小時成本包含折舊、電力、維護
    tokens_per_hour: int  # 每小時處理token數
    requests_per_hour: int  # 每小時處理請求數
    setup_cost: Decimal = Decimal('0')  # 設置成本
    
    def calculate_cost(self, tokens: int, requests: int, processing_hours: Decimal) -> Decimal:
        """計算硬體成本"""
        return self.hourly_cost * processing_hours + self.setup_cost


class APICostCalculator:
    """API成本計算器"""
    
    def __init__(self):
        """初始化計算器"""
        self.pricing_models = self._initialize_pricing_models()
        self.hardware_models = self._initialize_hardware_models()
        
    def _initialize_pricing_models(self) -> Dict[APIProvider, APIPricingModel]:
        """初始化API定價模型"""
        return {
            APIProvider.OPENAI_GPT4: APIPricingModel(
                provider=APIProvider.OPENAI_GPT4,
                input_price_per_1k_tokens=Decimal('0.03'),
                output_price_per_1k_tokens=Decimal('0.06'),
                request_base_cost=Decimal('0.0001')
            ),
            APIProvider.OPENAI_GPT3_5: APIPricingModel(
                provider=APIProvider.OPENAI_GPT3_5,
                input_price_per_1k_tokens=Decimal('0.0015'),
                output_price_per_1k_tokens=Decimal('0.002'),
                request_base_cost=Decimal('0.00005')
            ),
            APIProvider.ANTHROPIC_CLAUDE: APIPricingModel(
                provider=APIProvider.ANTHROPIC_CLAUDE,
                input_price_per_1k_tokens=Decimal('0.008'),
                output_price_per_1k_tokens=Decimal('0.024'),
                request_base_cost=Decimal('0.0001')
            ),
            APIProvider.ANTHROPIC_CLAUDE_HAIKU: APIPricingModel(
                provider=APIProvider.ANTHROPIC_CLAUDE_HAIKU,
                input_price_per_1k_tokens=Decimal('0.0008'),
                output_price_per_1k_tokens=Decimal('0.004'),
                request_base_cost=Decimal('0.00005')
            ),
        }
    
    def _initialize_hardware_models(self) -> Dict[str, HardwareCostModel]:
        """初始化硬體成本模型"""
        return {
            "rtx_4090": HardwareCostModel(
                hardware_name="RTX 4090",
                hourly_cost=Decimal('0.85'),  # 包含折舊、電力、維護
                tokens_per_hour=50000,
                requests_per_hour=500
            ),
            "rtx_3090": HardwareCostModel(
                hardware_name="RTX 3090", 
                hourly_cost=Decimal('0.65'),
                tokens_per_hour=35000,
                requests_per_hour=350
            ),
            "a100": HardwareCostModel(
                hardware_name="A100",
                hourly_cost=Decimal('2.50'),
                tokens_per_hour=150000,
                requests_per_hour=1500
            ),
        }
    
    async def calculate_api_cost_savings(
        self,
        original_provider: APIProvider,
        gpt_oss_hardware: str,
        total_input_tokens: int,
        total_output_tokens: int,
        total_requests: int,
        processing_time_hours: Decimal,
        calculation_date: date = None,
        additional_metrics: Dict[str, Any] = None
    ) -> APICostSavingSchema:
        """
        計算API成本節省
        
        Args:
            original_provider: 原始API提供商
            gpt_oss_hardware: GPT-OSS硬體配置
            total_input_tokens: 總輸入token數
            total_output_tokens: 總輸出token數
            total_requests: 總請求數
            processing_time_hours: 處理時間(小時)
            calculation_date: 計算日期
            additional_metrics: 額外指標
            
        Returns:
            API成本節省記錄
        """
        try:
            if calculation_date is None:
                calculation_date = date.today()
            
            # 計算原始API成本
            original_cost = await self._calculate_original_api_cost(
                original_provider, total_input_tokens, total_output_tokens, total_requests
            )
            
            # 計算GPT-OSS成本
            gpt_oss_cost = await self._calculate_gpt_oss_cost(
                gpt_oss_hardware, total_input_tokens + total_output_tokens, 
                total_requests, processing_time_hours
            )
            
            # 計算節省
            savings_amount = original_cost - gpt_oss_cost
            savings_percentage = (savings_amount / original_cost * 100) if original_cost > 0 else Decimal('0')
            
            # 計算品質指標
            quality_metrics = await self._calculate_quality_metrics(
                original_provider, gpt_oss_hardware, additional_metrics
            )
            
            # 創建成本節省記錄
            cost_saving = APICostSavingSchema(
                original_api_provider=original_provider.value,
                gpt_oss_provider=f"gpt_oss_{gpt_oss_hardware}",
                total_tokens_processed=total_input_tokens + total_output_tokens,
                total_requests_handled=total_requests,
                processing_time_hours=processing_time_hours,
                original_api_cost=original_cost,
                gpt_oss_cost=gpt_oss_cost,
                savings_amount=savings_amount,
                savings_percentage=savings_percentage,
                quality_score=quality_metrics.get('quality_score'),
                latency_improvement=quality_metrics.get('latency_improvement'),
                accuracy_comparison=quality_metrics.get('accuracy_comparison'),
                calculation_date=calculation_date,
                period_start=datetime.combine(calculation_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                period_end=datetime.combine(calculation_date, datetime.max.time()).replace(tzinfo=timezone.utc),
                calculation_method="enterprise_cost_model_v1.0",
                pricing_model_version="2025_q1",
                additional_metrics=additional_metrics or {}
            )
            
            logger.info(f"計算API成本節省完成: 節省 ${savings_amount:.6f} ({savings_percentage:.2f}%)")
            return cost_saving
            
        except Exception as e:
            logger.error(f"計算API成本節省失敗: {e}")
            raise
    
    async def _calculate_original_api_cost(
        self, 
        provider: APIProvider, 
        input_tokens: int, 
        output_tokens: int, 
        requests: int
    ) -> Decimal:
        """計算原始API成本"""
        if provider not in self.pricing_models:
            raise ValueError(f"不支援的API提供商: {provider}")
        
        pricing_model = self.pricing_models[provider]
        return pricing_model.calculate_cost(input_tokens, output_tokens, requests)
    
    async def _calculate_gpt_oss_cost(
        self, 
        hardware: str, 
        total_tokens: int, 
        requests: int, 
        processing_hours: Decimal
    ) -> Decimal:
        """計算GPT-OSS成本"""
        if hardware not in self.hardware_models:
            raise ValueError(f"不支援的硬體配置: {hardware}")
        
        hardware_model = self.hardware_models[hardware]
        return hardware_model.calculate_cost(total_tokens, requests, processing_hours)
    
    async def _calculate_quality_metrics(
        self, 
        original_provider: APIProvider, 
        gpt_oss_hardware: str,
        additional_metrics: Dict[str, Any] = None
    ) -> Dict[str, Decimal]:
        """計算品質指標"""
        # 基於歷史數據和基準測試的品質評估
        quality_baselines = {
            APIProvider.OPENAI_GPT4: {'quality': 95, 'latency': 1200},
            APIProvider.OPENAI_GPT3_5: {'quality': 90, 'latency': 800},
            APIProvider.ANTHROPIC_CLAUDE: {'quality': 93, 'latency': 1000},
            APIProvider.ANTHROPIC_CLAUDE_HAIKU: {'quality': 88, 'latency': 600},
        }
        
        gpt_oss_performance = {
            'rtx_4090': {'quality': 87, 'latency': 900},
            'rtx_3090': {'quality': 85, 'latency': 1100}, 
            'a100': {'quality': 92, 'latency': 700},
        }
        
        baseline = quality_baselines.get(original_provider, {'quality': 90, 'latency': 1000})
        gpt_oss = gpt_oss_performance.get(gpt_oss_hardware, {'quality': 85, 'latency': 1000})
        
        # 從additional_metrics中獲取實際測量值（如果有）
        if additional_metrics:
            gpt_oss['quality'] = additional_metrics.get('measured_quality', gpt_oss['quality'])
            gpt_oss['latency'] = additional_metrics.get('measured_latency', gpt_oss['latency'])
        
        return {
            'quality_score': Decimal(str(gpt_oss['quality'])),
            'latency_improvement': Decimal(str(baseline['latency'] - gpt_oss['latency'])),
            'accuracy_comparison': Decimal(str((gpt_oss['quality'] - baseline['quality']) / baseline['quality'] * 100))
        }
    
    async def batch_calculate_cost_savings(
        self,
        calculations: List[Dict[str, Any]]
    ) -> List[APICostSavingSchema]:
        """批量計算成本節省"""
        results = []
        
        for calc_params in calculations:
            try:
                result = await self.calculate_api_cost_savings(**calc_params)
                results.append(result)
            except Exception as e:
                logger.error(f"批量計算失敗 for params {calc_params}: {e}")
                continue
        
        return results
    
    def update_pricing_model(self, provider: APIProvider, pricing_model: APIPricingModel):
        """更新定價模型"""
        self.pricing_models[provider] = pricing_model
        logger.info(f"更新 {provider.value} 定價模型")
    
    def update_hardware_model(self, hardware_id: str, hardware_model: HardwareCostModel):
        """更新硬體模型"""
        self.hardware_models[hardware_id] = hardware_model
        logger.info(f"更新硬體模型 {hardware_id}")
    
    async def get_cost_savings_summary(
        self,
        period_start: date,
        period_end: date,
        providers: List[APIProvider] = None,
        hardware_configs: List[str] = None
    ) -> Dict[str, Any]:
        """獲取成本節省摘要"""
        # 這裡應該從數據庫查詢實際數據
        # 目前返回示例摘要
        return {
            'total_savings': Decimal('15847.32'),
            'total_original_cost': Decimal('23456.78'),
            'total_gpt_oss_cost': Decimal('7609.46'),
            'savings_percentage': Decimal('67.58'),
            'total_tokens_processed': 45_678_901,
            'total_requests_handled': 123_456,
            'average_quality_score': Decimal('88.5'),
            'top_savings_providers': [
                {'provider': APIProvider.OPENAI_GPT4.value, 'savings': Decimal('8976.23')},
                {'provider': APIProvider.ANTHROPIC_CLAUDE.value, 'savings': Decimal('4532.11')},
                {'provider': APIProvider.OPENAI_GPT3_5.value, 'savings': Decimal('2338.98')}
            ],
            'period_start': period_start,
            'period_end': period_end,
            'calculation_date': datetime.now(timezone.utc)
        }


class CostSavingsAnalyzer:
    """成本節省分析器"""
    
    def __init__(self, calculator: APICostCalculator):
        """初始化分析器"""
        self.calculator = calculator
    
    async def analyze_cost_trends(
        self,
        cost_savings: List[APICostSavingSchema],
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """分析成本趋势"""
        if not cost_savings:
            return {'error': '沒有成本節省數據用於分析'}
        
        # 按日期排序
        sorted_savings = sorted(cost_savings, key=lambda x: x.calculation_date)
        
        # 計算趨勢
        total_savings = sum(saving.savings_amount for saving in sorted_savings)
        average_daily_savings = total_savings / len(sorted_savings)
        
        # 計算節省趨勢
        if len(sorted_savings) >= 2:
            recent_avg = sum(s.savings_amount for s in sorted_savings[-7:]) / min(7, len(sorted_savings))
            early_avg = sum(s.savings_amount for s in sorted_savings[:7]) / min(7, len(sorted_savings))
            trend_direction = "increasing" if recent_avg > early_avg else "decreasing"
            trend_percentage = abs((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else Decimal('0')
        else:
            trend_direction = "stable"
            trend_percentage = Decimal('0')
        
        # 最佳節省提供商
        provider_savings = {}
        for saving in sorted_savings:
            provider = saving.original_api_provider
            if provider not in provider_savings:
                provider_savings[provider] = Decimal('0')
            provider_savings[provider] += saving.savings_amount
        
        best_provider = max(provider_savings.keys(), key=lambda k: provider_savings[k]) if provider_savings else None
        
        return {
            'analysis_period_days': analysis_period_days,
            'total_cost_savings': total_savings,
            'average_daily_savings': average_daily_savings,
            'trend_direction': trend_direction,
            'trend_percentage': trend_percentage,
            'best_savings_provider': best_provider,
            'provider_savings_breakdown': provider_savings,
            'total_tokens_analyzed': sum(s.total_tokens_processed for s in sorted_savings),
            'average_savings_percentage': sum(s.savings_percentage for s in sorted_savings) / len(sorted_savings),
            'quality_impact': {
                'average_quality_score': sum(s.quality_score for s in sorted_savings if s.quality_score) / len([s for s in sorted_savings if s.quality_score]) if any(s.quality_score for s in sorted_savings) else None,
                'latency_improvements': [s.latency_improvement for s in sorted_savings if s.latency_improvement],
                'accuracy_comparisons': [s.accuracy_comparison for s in sorted_savings if s.accuracy_comparison]
            },
            'analysis_timestamp': datetime.now(timezone.utc)
        }
    
    async def identify_optimization_opportunities(
        self,
        cost_savings: List[APICostSavingSchema],
        target_savings_percentage: Decimal = Decimal('75.0')
    ) -> List[Dict[str, Any]]:
        """識別優化機會"""
        opportunities = []
        
        # 分析低效率的配置
        for saving in cost_savings:
            if saving.savings_percentage < target_savings_percentage:
                opportunities.append({
                    'type': 'hardware_upgrade',
                    'current_provider': saving.original_api_provider,
                    'current_hardware': saving.gpt_oss_provider,
                    'current_savings': saving.savings_percentage,
                    'target_savings': target_savings_percentage,
                    'estimated_improvement': target_savings_percentage - saving.savings_percentage,
                    'recommendation': f"考慮升級硬體配置以提高 {saving.original_api_provider} 的節省率"
                })
        
        # 分析品質問題
        quality_issues = [s for s in cost_savings if s.quality_score and s.quality_score < Decimal('85')]
        if quality_issues:
            opportunities.append({
                'type': 'quality_improvement',
                'affected_configs': [s.gpt_oss_provider for s in quality_issues],
                'average_quality': sum(s.quality_score for s in quality_issues) / len(quality_issues),
                'recommendation': "考慮調整模型參數或升級硬體以改善輸出品質"
            })
        
        # 分析延遲問題
        latency_issues = [s for s in cost_savings if s.latency_improvement and s.latency_improvement < Decimal('0')]
        if latency_issues:
            opportunities.append({
                'type': 'latency_optimization',
                'affected_configs': [s.gpt_oss_provider for s in latency_issues],
                'average_latency_degradation': sum(abs(s.latency_improvement) for s in latency_issues) / len(latency_issues),
                'recommendation': "優化推理配置或考慮更快的硬體以改善響應時間"
            })
        
        return opportunities
    
    async def generate_roi_report(
        self,
        cost_savings: List[APICostSavingSchema],
        hardware_investment: Decimal,
        analysis_period_months: int = 12
    ) -> Dict[str, Any]:
        """生成ROI報告"""
        if not cost_savings:
            return {'error': '無法計算ROI - 缺乏成本節省數據'}
        
        # 計算總節省
        total_savings = sum(s.savings_amount for s in cost_savings)
        
        # 計算月均節省
        monthly_savings = total_savings / analysis_period_months if analysis_period_months > 0 else total_savings
        
        # 計算ROI
        roi_percentage = (total_savings - hardware_investment) / hardware_investment * 100 if hardware_investment > 0 else Decimal('0')
        
        # 計算回收期
        payback_months = hardware_investment / monthly_savings if monthly_savings > 0 else float('inf')
        
        # 預測未來節省
        annual_projected_savings = monthly_savings * 12
        
        return {
            'analysis_period_months': analysis_period_months,
            'hardware_investment': hardware_investment,
            'total_cost_savings': total_savings,
            'monthly_average_savings': monthly_savings,
            'roi_percentage': roi_percentage,
            'payback_period_months': payback_months if payback_months != float('inf') else None,
            'annual_projected_savings': annual_projected_savings,
            'net_benefit': total_savings - hardware_investment,
            'cost_efficiency_metrics': {
                'savings_per_token': total_savings / sum(s.total_tokens_processed for s in cost_savings) if sum(s.total_tokens_processed for s in cost_savings) > 0 else Decimal('0'),
                'savings_per_request': total_savings / sum(s.total_requests_handled for s in cost_savings) if sum(s.total_requests_handled for s in cost_savings) > 0 else Decimal('0')
            },
            'risk_assessment': {
                'quality_risk': 'low' if all(s.quality_score and s.quality_score >= Decimal('85') for s in cost_savings if s.quality_score) else 'medium',
                'performance_risk': 'low' if all(s.latency_improvement and s.latency_improvement >= Decimal('0') for s in cost_savings if s.latency_improvement) else 'medium'
            },
            'report_generated': datetime.now(timezone.utc)
        }