#!/usr/bin/env python3
"""
Cost Calculation Service - 成本計算服務層和API
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級成本計算服務，提供：
- 統一成本計算API和服務接口
- 多維度成本聚合和分析
- 成本預算管理和控制
- 成本優化建議和自動化
- 高性能成本計算引擎
- 完整的成本追蹤和審計
"""

import uuid
import logging
import asyncio
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
from contextlib import asynccontextmanager

from ..database.virtual_pnl_db import VirtualPnLDB, VirtualPnLDBError
from ..database.virtual_pnl_models import (
    CostTrackingCreate, RevenueAttributionCreate, BudgetAllocationCreate,
    CostCategory, CostType, RevenueSource, BudgetPeriodType, AllocationMethod
)
from .hardware_cost_calculator import HardwareCostCalculator
from .power_maintenance_tracker import PowerMaintenanceTracker
from .labor_cost_allocator import LaborCostAllocator
from .realtime_cost_monitor import RealtimeCostMonitor

logger = logging.getLogger(__name__)

# ==================== 核心數據類型 ====================

class CalculationScope(Enum):
    """計算範圍"""
    ASSET = "asset"
    PROJECT = "project"
    COST_CENTER = "cost_center"
    DEPARTMENT = "department"
    ORGANIZATION = "organization"

class ReportType(Enum):
    """報告類型"""
    COST_SUMMARY = "cost_summary"
    COST_BREAKDOWN = "cost_breakdown"
    COST_TREND = "cost_trend"
    BUDGET_ANALYSIS = "budget_analysis"
    ROI_ANALYSIS = "roi_analysis"
    OPTIMIZATION_REPORT = "optimization_report"

@dataclass
class CostCalculationRequest:
    """成本計算請求"""
    calculation_id: str
    scope: CalculationScope
    target_ids: List[str]
    
    # 時間範圍
    start_date: date
    end_date: date
    
    # 計算選項
    include_hardware_costs: bool = True
    include_power_costs: bool = True
    include_maintenance_costs: bool = True
    include_labor_costs: bool = True
    include_overhead_costs: bool = True
    
    # 分攤選項
    allocation_method: Optional[str] = None
    allocation_rules: List[str] = field(default_factory=list)
    
    # 分析選項
    include_trends: bool = False
    include_predictions: bool = False
    include_optimizations: bool = False
    
    # 格式選項
    currency: str = "USD"
    precision_digits: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'calculation_id': self.calculation_id,
            'scope': self.scope.value,
            'target_ids': self.target_ids,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'include_hardware_costs': self.include_hardware_costs,
            'include_power_costs': self.include_power_costs,
            'include_maintenance_costs': self.include_maintenance_costs,
            'include_labor_costs': self.include_labor_costs,
            'include_overhead_costs': self.include_overhead_costs,
            'allocation_method': self.allocation_method,
            'allocation_rules': self.allocation_rules,
            'include_trends': self.include_trends,
            'include_predictions': self.include_predictions,
            'include_optimizations': self.include_optimizations,
            'currency': self.currency,
            'precision_digits': self.precision_digits
        }

@dataclass
class CostCalculationResult:
    """成本計算結果"""
    calculation_id: str
    request: CostCalculationRequest
    
    # 計算時間
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    calculation_duration_ms: float = 0.0
    
    # 總體成本
    total_cost: Decimal = Decimal('0')
    
    # 成本分解
    hardware_costs: Decimal = Decimal('0')
    power_costs: Decimal = Decimal('0')
    maintenance_costs: Decimal = Decimal('0')
    labor_costs: Decimal = Decimal('0')
    overhead_costs: Decimal = Decimal('0')
    other_costs: Decimal = Decimal('0')
    
    # 按目標分組的成本
    costs_by_target: Dict[str, Decimal] = field(default_factory=dict)
    
    # 按類別分組的成本
    costs_by_category: Dict[str, Decimal] = field(default_factory=dict)
    
    # 按時間段的成本
    costs_by_period: Dict[str, Decimal] = field(default_factory=dict)
    
    # 效率指標
    cost_per_unit: Optional[Decimal] = None
    utilization_rates: Dict[str, float] = field(default_factory=dict)
    efficiency_scores: Dict[str, float] = field(default_factory=dict)
    
    # 預算比較
    budget_allocated: Optional[Decimal] = None
    budget_utilized: Optional[Decimal] = None
    budget_remaining: Optional[Decimal] = None
    budget_utilization_rate: Optional[float] = None
    
    # 趨勢分析
    cost_trends: Dict[str, Any] = field(default_factory=dict)
    
    # 預測結果
    cost_predictions: Dict[str, Any] = field(default_factory=dict)
    
    # 優化建議
    optimization_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 計算元數據
    data_sources: List[str] = field(default_factory=list)
    calculation_method: str = ""
    confidence_score: float = 1.0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'calculation_id': self.calculation_id,
            'request': self.request.to_dict(),
            'calculated_at': self.calculated_at.isoformat(),
            'calculation_duration_ms': self.calculation_duration_ms,
            'total_cost': float(self.total_cost),
            'hardware_costs': float(self.hardware_costs),
            'power_costs': float(self.power_costs),
            'maintenance_costs': float(self.maintenance_costs),
            'labor_costs': float(self.labor_costs),
            'overhead_costs': float(self.overhead_costs),
            'other_costs': float(self.other_costs),
            'costs_by_target': {k: float(v) for k, v in self.costs_by_target.items()},
            'costs_by_category': {k: float(v) for k, v in self.costs_by_category.items()},
            'costs_by_period': {k: float(v) for k, v in self.costs_by_period.items()},
            'cost_per_unit': float(self.cost_per_unit) if self.cost_per_unit else None,
            'utilization_rates': self.utilization_rates,
            'efficiency_scores': self.efficiency_scores,
            'budget_allocated': float(self.budget_allocated) if self.budget_allocated else None,
            'budget_utilized': float(self.budget_utilized) if self.budget_utilized else None,
            'budget_remaining': float(self.budget_remaining) if self.budget_remaining else None,
            'budget_utilization_rate': self.budget_utilization_rate,
            'cost_trends': self.cost_trends,
            'cost_predictions': self.cost_predictions,
            'optimization_suggestions': self.optimization_suggestions,
            'data_sources': self.data_sources,
            'calculation_method': self.calculation_method,
            'confidence_score': self.confidence_score,
            'warnings': self.warnings,
            'errors': self.errors
        }

# ==================== 核心服務引擎 ====================

class CostCalculationService:
    """
    成本計算服務
    
    功能：
    1. 統一成本計算API和服務接口
    2. 多維度成本聚合和分析
    3. 成本預算管理和控制
    4. 成本優化建議和自動化
    5. 高性能成本計算引擎
    6. 完整的成本追蹤和審計
    """
    
    def __init__(
        self,
        virtual_pnl_db: Optional[VirtualPnLDB] = None,
        hardware_calculator: Optional[HardwareCostCalculator] = None,
        power_tracker: Optional[PowerMaintenanceTracker] = None,
        labor_allocator: Optional[LaborCostAllocator] = None,
        cost_monitor: Optional[RealtimeCostMonitor] = None
    ):
        """初始化成本計算服務"""
        self.logger = logger
        
        # 數據庫和計算組件
        self.virtual_pnl_db = virtual_pnl_db or VirtualPnLDB()
        self.hardware_calculator = hardware_calculator or HardwareCostCalculator()
        self.power_tracker = power_tracker or PowerMaintenanceTracker()
        self.labor_allocator = labor_allocator or LaborCostAllocator()
        self.cost_monitor = cost_monitor
        
        # 計算結果緩存
        self.calculation_cache: Dict[str, CostCalculationResult] = {}
        self.cache_ttl_seconds = 3600  # 1小時緩存
        
        # 性能配置
        self.config = {
            'max_concurrent_calculations': 5,
            'calculation_timeout_seconds': 300,
            'cache_enabled': True,
            'parallel_calculation_enabled': True,
            'optimization_analysis_enabled': True,
            'trend_analysis_window_days': 30,
            'prediction_horizon_days': 90
        }
        
        # 計算任務信號量
        self._calculation_semaphore = asyncio.Semaphore(self.config['max_concurrent_calculations'])
        
        self.logger.info("✅ Cost Calculation Service initialized")
    
    # ==================== 核心計算API ====================
    
    async def calculate_costs(
        self,
        request: CostCalculationRequest
    ) -> CostCalculationResult:
        """計算成本（主要入口）"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # 檢查緩存
            cache_key = self._generate_cache_key(request)
            if self.config['cache_enabled'] and cache_key in self.calculation_cache:
                cached_result = self.calculation_cache[cache_key]
                # 檢查緩存是否過期
                if (start_time - cached_result.calculated_at).total_seconds() < self.cache_ttl_seconds:
                    self.logger.info(f"Returning cached result for {request.calculation_id}")
                    return cached_result
            
            # 獲取計算信號量
            async with self._calculation_semaphore:
                # 執行計算
                async with asyncio.timeout(self.config['calculation_timeout_seconds']):
                    result = await self._perform_calculation(request, start_time)
            
            # 緩存結果
            if self.config['cache_enabled']:
                self.calculation_cache[cache_key] = result
                
                # 清理過期緩存
                await self._cleanup_expired_cache()
            
            # 保存到數據庫
            await self._save_calculation_result(result)
            
            # 觸發實時監控更新
            if self.cost_monitor:
                await self._notify_cost_monitor(result)
            
            self.logger.info(f"✅ Cost calculation completed: {request.calculation_id} in {result.calculation_duration_ms:.2f}ms")
            return result
            
        except asyncio.TimeoutError:
            error_msg = f"Cost calculation timed out: {request.calculation_id}"
            self.logger.error(f"❌ {error_msg}")
            return self._create_error_result(request, start_time, error_msg)
            
        except Exception as e:
            error_msg = f"Error in cost calculation: {e}"
            self.logger.error(f"❌ {error_msg}")
            return self._create_error_result(request, start_time, error_msg)
    
    async def _perform_calculation(
        self,
        request: CostCalculationRequest,
        start_time: datetime
    ) -> CostCalculationResult:
        """執行成本計算"""
        result = CostCalculationResult(
            calculation_id=request.calculation_id,
            request=request
        )
        
        # 並行計算各類成本
        calculation_tasks = []
        
        if request.include_hardware_costs:
            calculation_tasks.append(self._calculate_hardware_costs(request, result))
        
        if request.include_power_costs or request.include_maintenance_costs:
            calculation_tasks.append(self._calculate_power_maintenance_costs(request, result))
        
        if request.include_labor_costs:
            calculation_tasks.append(self._calculate_labor_costs(request, result))
        
        # 執行並行計算
        if self.config['parallel_calculation_enabled'] and calculation_tasks:
            await asyncio.gather(*calculation_tasks, return_exceptions=True)
        else:
            for task in calculation_tasks:
                try:
                    await task
                except Exception as e:
                    result.errors.append(f"Calculation task error: {e}")
        
        # 計算總成本
        result.total_cost = (
            result.hardware_costs +
            result.power_costs +
            result.maintenance_costs +
            result.labor_costs +
            result.overhead_costs +
            result.other_costs
        )
        
        # 聚合成本分類
        result.costs_by_category = {
            'hardware': result.hardware_costs,
            'power': result.power_costs,
            'maintenance': result.maintenance_costs,
            'labor': result.labor_costs,
            'overhead': result.overhead_costs,
            'other': result.other_costs
        }
        
        # 計算預算比較
        await self._calculate_budget_comparison(request, result)
        
        # 趨勢分析
        if request.include_trends:
            await self._calculate_cost_trends(request, result)
        
        # 成本預測
        if request.include_predictions:
            await self._calculate_cost_predictions(request, result)
        
        # 優化建議
        if request.include_optimizations:
            await self._generate_optimization_suggestions(request, result)
        
        # 設置計算元數據
        result.calculated_at = datetime.now(timezone.utc)
        result.calculation_duration_ms = (result.calculated_at - start_time).total_seconds() * 1000
        result.calculation_method = "integrated_cost_calculation"
        result.data_sources = ['hardware_calculator', 'power_tracker', 'labor_allocator', 'virtual_pnl_db']
        result.confidence_score = self._calculate_confidence_score(result)
        
        return result
    
    # ==================== 個別成本計算 ====================
    
    async def _calculate_hardware_costs(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """計算硬體成本"""
        try:
            total_hardware_cost = Decimal('0')
            
            for target_id in request.target_ids:
                try:
                    # 計算期間硬體成本
                    hardware_result = await self.hardware_calculator.calculate_hardware_costs(
                        target_id,
                        request.end_date,
                        request.start_date,
                        request.end_date
                    )
                    
                    target_cost = hardware_result.total_cost
                    total_hardware_cost += target_cost
                    result.costs_by_target[target_id] = result.costs_by_target.get(target_id, Decimal('0')) + target_cost
                    
                    # 記錄利用率
                    if hardware_result.utilization_rate > 0:
                        result.utilization_rates[target_id] = hardware_result.utilization_rate
                    
                except Exception as e:
                    result.warnings.append(f"Hardware cost calculation failed for {target_id}: {e}")
                    continue
            
            result.hardware_costs = total_hardware_cost
            
        except Exception as e:
            result.errors.append(f"Hardware cost calculation error: {e}")
    
    async def _calculate_power_maintenance_costs(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """計算電力和維護成本"""
        try:
            total_power_cost = Decimal('0')
            total_maintenance_cost = Decimal('0')
            
            for target_id in request.target_ids:
                try:
                    # 計算期間電力和維護成本
                    start_datetime = datetime.combine(request.start_date, datetime.min.time())
                    end_datetime = datetime.combine(request.end_date, datetime.max.time())
                    
                    power_result = await self.power_tracker.calculate_comprehensive_costs(
                        target_id,
                        start_datetime,
                        end_datetime
                    )
                    
                    power_cost = power_result.total_electricity_cost
                    maintenance_cost = power_result.total_maintenance_cost
                    
                    total_power_cost += power_cost
                    total_maintenance_cost += maintenance_cost
                    
                    # 更新目標成本
                    target_total = power_cost + maintenance_cost
                    result.costs_by_target[target_id] = result.costs_by_target.get(target_id, Decimal('0')) + target_total
                    
                    # 記錄效率分數
                    if power_result.power_usage_effectiveness:
                        result.efficiency_scores[target_id] = 1.0 / power_result.power_usage_effectiveness
                    
                except Exception as e:
                    result.warnings.append(f"Power/maintenance cost calculation failed for {target_id}: {e}")
                    continue
            
            if request.include_power_costs:
                result.power_costs = total_power_cost
            
            if request.include_maintenance_costs:
                result.maintenance_costs = total_maintenance_cost
                
        except Exception as e:
            result.errors.append(f"Power/maintenance cost calculation error: {e}")
    
    async def _calculate_labor_costs(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """計算人力成本"""
        try:
            total_labor_cost = Decimal('0')
            
            # 獲取相關員工
            for employee_id in self.labor_allocator.employees.keys():
                employee = self.labor_allocator.employees[employee_id]
                if not employee.is_active:
                    continue
                
                # 檢查員工是否與目標ID相關
                should_include = (
                    request.scope == CalculationScope.ORGANIZATION or
                    employee_id in request.target_ids or
                    str(employee.cost_center_id) in request.target_ids
                )
                
                if not should_include:
                    continue
                
                try:
                    # 計算員工成本分攤
                    labor_result = await self.labor_allocator.calculate_labor_cost_allocation(
                        employee_id,
                        request.start_date,
                        request.end_date
                    )
                    
                    employee_cost = labor_result.total_cost
                    total_labor_cost += employee_cost
                    
                    # 分攤到相關目標
                    if labor_result.allocated_costs:
                        for target_id, allocated_cost in labor_result.allocated_costs.items():
                            if target_id in request.target_ids:
                                result.costs_by_target[target_id] = result.costs_by_target.get(target_id, Decimal('0')) + allocated_cost
                    else:
                        # 如果沒有具體分攤，平均分配到目標
                        cost_per_target = employee_cost / len(request.target_ids)
                        for target_id in request.target_ids:
                            result.costs_by_target[target_id] = result.costs_by_target.get(target_id, Decimal('0')) + cost_per_target
                    
                    # 記錄利用率和質量分數
                    if labor_result.utilization_rate > 0:
                        result.utilization_rates[f"employee_{employee_id}"] = labor_result.utilization_rate
                    
                    if labor_result.average_quality_score:
                        result.efficiency_scores[f"employee_{employee_id}"] = labor_result.average_quality_score
                    
                except Exception as e:
                    result.warnings.append(f"Labor cost calculation failed for {employee_id}: {e}")
                    continue
            
            result.labor_costs = total_labor_cost
            
        except Exception as e:
            result.errors.append(f"Labor cost calculation error: {e}")
    
    # ==================== 預算和趨勢分析 ====================
    
    async def _calculate_budget_comparison(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """計算預算比較"""
        try:
            # 這裡需要從虛擬損益表數據庫獲取預算數據
            # 暫時使用模擬數據
            
            # 假設月度預算
            if request.scope == CalculationScope.COST_CENTER and request.target_ids:
                period_days = (request.end_date - request.start_date).days + 1
                estimated_monthly_budget = Decimal('50000')  # 示例預算
                daily_budget = estimated_monthly_budget / Decimal('30')
                period_budget = daily_budget * Decimal(str(period_days))
                
                result.budget_allocated = period_budget
                result.budget_utilized = result.total_cost
                result.budget_remaining = period_budget - result.total_cost
                
                if period_budget > 0:
                    result.budget_utilization_rate = float(result.total_cost / period_budget)
            
        except Exception as e:
            result.warnings.append(f"Budget comparison calculation error: {e}")
    
    async def _calculate_cost_trends(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """計算成本趨勢"""
        try:
            # 獲取歷史成本數據
            trend_start = request.start_date - timedelta(days=self.config['trend_analysis_window_days'])
            
            # 這裡需要實現歷史數據獲取邏輯
            # 暫時返回模擬趨勢數據
            result.cost_trends = {
                'trend_direction': 'increasing',
                'trend_percentage': 5.2,
                'trend_confidence': 0.8,
                'historical_data_points': 30,
                'analysis_period_days': self.config['trend_analysis_window_days']
            }
            
        except Exception as e:
            result.warnings.append(f"Cost trend calculation error: {e}")
    
    async def _calculate_cost_predictions(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """計算成本預測"""
        try:
            # 基於歷史趨勢預測未來成本
            prediction_horizon = self.config['prediction_horizon_days']
            
            # 簡單線性預測模型
            daily_cost = result.total_cost / Decimal(str((request.end_date - request.start_date).days + 1))
            
            # 假設基於趨勢的增長
            growth_rate = Decimal('0.05')  # 5% 月增長
            monthly_growth = growth_rate / Decimal('30')
            
            predictions = []
            for days_ahead in [30, 60, 90]:
                if days_ahead <= prediction_horizon:
                    predicted_cost = daily_cost * (Decimal('1') + monthly_growth * Decimal(str(days_ahead))) * Decimal(str(days_ahead))
                    predictions.append({
                        'period': f"{days_ahead} days ahead",
                        'predicted_cost': float(predicted_cost),
                        'confidence': max(0.5, 1.0 - (days_ahead / prediction_horizon) * 0.5)
                    })
            
            result.cost_predictions = {
                'predictions': predictions,
                'model': 'linear_trend',
                'prediction_horizon_days': prediction_horizon
            }
            
        except Exception as e:
            result.warnings.append(f"Cost prediction calculation error: {e}")
    
    async def _generate_optimization_suggestions(
        self,
        request: CostCalculationRequest,
        result: CostCalculationResult
    ):
        """生成優化建議"""
        try:
            suggestions = []
            
            # 基於成本結構的建議
            total_cost = result.total_cost
            if total_cost > 0:
                # 硬體成本優化
                hardware_ratio = result.hardware_costs / total_cost
                if hardware_ratio > Decimal('0.6'):
                    suggestions.append({
                        'type': 'hardware_optimization',
                        'priority': 'high',
                        'description': f'硬體成本占總成本 {hardware_ratio:.1%}，建議優化硬體利用率',
                        'potential_savings': float(result.hardware_costs * Decimal('0.15')),
                        'actions': [
                            '檢查硬體利用率和負載平衡',
                            '考慮硬體整合和虛擬化',
                            '評估硬體升級的成本效益',
                            '實施自動化資源管理'
                        ]
                    })
                
                # 電力成本優化
                power_ratio = result.power_costs / total_cost
                if power_ratio > Decimal('0.3'):
                    suggestions.append({
                        'type': 'power_optimization',
                        'priority': 'medium',
                        'description': f'電力成本占總成本 {power_ratio:.1%}，建議改善能效',
                        'potential_savings': float(result.power_costs * Decimal('0.20')),
                        'actions': [
                            '實施動態電源管理',
                            '優化散熱系統效率',
                            '考慮節能硬體替換',
                            '分析電價時段優化'
                        ]
                    })
                
                # 人力成本優化
                labor_ratio = result.labor_costs / total_cost
                if labor_ratio > Decimal('0.5'):
                    suggestions.append({
                        'type': 'labor_optimization',
                        'priority': 'medium',
                        'description': f'人力成本占總成本 {labor_ratio:.1%}，建議提升人力效率',
                        'potential_savings': float(result.labor_costs * Decimal('0.10')),
                        'actions': [
                            '分析員工工作負載分佈',
                            '提供技能提升培訓',
                            '實施自動化工具',
                            '優化工作流程和協作'
                        ]
                    })
            
            # 基於利用率的建議
            low_utilization_targets = [
                target_id for target_id, utilization in result.utilization_rates.items()
                if utilization < 0.5
            ]
            
            if low_utilization_targets:
                suggestions.append({
                    'type': 'utilization_optimization',
                    'priority': 'high',
                    'description': f'發現 {len(low_utilization_targets)} 個低利用率資源',
                    'potential_savings': float(total_cost * Decimal('0.25')),
                    'actions': [
                        '重新分配工作負載',
                        '考慮資源整合',
                        '評估資源縮減可能性',
                        '改善資源調度算法'
                    ],
                    'affected_targets': low_utilization_targets
                })
            
            # 基於預算使用率的建議
            if result.budget_utilization_rate and result.budget_utilization_rate > 0.9:
                suggestions.append({
                    'type': 'budget_management',
                    'priority': 'critical',
                    'description': f'預算使用率 {result.budget_utilization_rate:.1%}，接近預算上限',
                    'potential_savings': float(result.total_cost * Decimal('0.05')),
                    'actions': [
                        '實施緊急成本控制措施',
                        '重新評估非必要支出',
                        '申請預算調整',
                        '加強成本監控頻率'
                    ]
                })
            
            result.optimization_suggestions = suggestions
            
        except Exception as e:
            result.warnings.append(f"Optimization suggestion generation error: {e}")
    
    # ==================== 快速計算API ====================
    
    async def quick_cost_summary(
        self,
        target_ids: List[str],
        scope: CalculationScope = CalculationScope.ASSET,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """快速成本摘要"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            request = CostCalculationRequest(
                calculation_id=f"quick_summary_{uuid.uuid4().hex[:8]}",
                scope=scope,
                target_ids=target_ids,
                start_date=start_date,
                end_date=end_date,
                include_trends=False,
                include_predictions=False,
                include_optimizations=False
            )
            
            result = await self.calculate_costs(request)
            
            return {
                'total_cost': float(result.total_cost),
                'daily_average': float(result.total_cost / Decimal(str(days_back))),
                'cost_breakdown': {k: float(v) for k, v in result.costs_by_category.items()},
                'target_costs': {k: float(v) for k, v in result.costs_by_target.items()},
                'period': f"{start_date} to {end_date}",
                'calculation_duration_ms': result.calculation_duration_ms
            }
            
        except Exception as e:
            self.logger.error(f"❌ Quick cost summary error: {e}")
            return {'error': str(e)}
    
    async def cost_comparison(
        self,
        target_ids: List[str],
        current_period_days: int = 30,
        comparison_period_days: int = 30,
        scope: CalculationScope = CalculationScope.ASSET
    ) -> Dict[str, Any]:
        """成本比較分析"""
        try:
            end_date = date.today()
            current_start = end_date - timedelta(days=current_period_days)
            comparison_start = current_start - timedelta(days=comparison_period_days)
            comparison_end = current_start - timedelta(days=1)
            
            # 當前期間計算
            current_request = CostCalculationRequest(
                calculation_id=f"comparison_current_{uuid.uuid4().hex[:8]}",
                scope=scope,
                target_ids=target_ids,
                start_date=current_start,
                end_date=end_date
            )
            
            # 比較期間計算
            comparison_request = CostCalculationRequest(
                calculation_id=f"comparison_baseline_{uuid.uuid4().hex[:8]}",
                scope=scope,
                target_ids=target_ids,
                start_date=comparison_start,
                end_date=comparison_end
            )
            
            # 並行執行計算
            current_result, comparison_result = await asyncio.gather(
                self.calculate_costs(current_request),
                self.calculate_costs(comparison_request)
            )
            
            # 計算變化
            cost_change = current_result.total_cost - comparison_result.total_cost
            change_percentage = 0.0
            if comparison_result.total_cost > 0:
                change_percentage = float((cost_change / comparison_result.total_cost) * 100)
            
            return {
                'current_period': {
                    'start_date': current_start.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_cost': float(current_result.total_cost),
                    'daily_average': float(current_result.total_cost / Decimal(str(current_period_days)))
                },
                'comparison_period': {
                    'start_date': comparison_start.isoformat(),
                    'end_date': comparison_end.isoformat(),
                    'total_cost': float(comparison_result.total_cost),
                    'daily_average': float(comparison_result.total_cost / Decimal(str(comparison_period_days)))
                },
                'cost_change': float(cost_change),
                'change_percentage': change_percentage,
                'change_direction': 'increase' if cost_change > 0 else 'decrease' if cost_change < 0 else 'no_change',
                'analysis': self._generate_cost_change_analysis(change_percentage, cost_change)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Cost comparison error: {e}")
            return {'error': str(e)}
    
    def _generate_cost_change_analysis(self, change_percentage: float, cost_change: Decimal) -> Dict[str, Any]:
        """生成成本變化分析"""
        analysis = {
            'severity': 'low',
            'interpretation': 'Normal cost variation',
            'recommendations': []
        }
        
        abs_change = abs(change_percentage)
        
        if abs_change > 50:
            analysis['severity'] = 'critical'
            analysis['interpretation'] = 'Significant cost change detected'
            analysis['recommendations'] = [
                'Immediately investigate the cause of cost change',
                'Review recent infrastructure changes',
                'Check for anomalies in usage patterns',
                'Consider implementing cost controls'
            ]
        elif abs_change > 20:
            analysis['severity'] = 'high'
            analysis['interpretation'] = 'Notable cost change requiring attention'
            analysis['recommendations'] = [
                'Analyze cost drivers for the change',
                'Review resource utilization patterns',
                'Consider optimization opportunities'
            ]
        elif abs_change > 10:
            analysis['severity'] = 'medium'
            analysis['interpretation'] = 'Moderate cost change'
            analysis['recommendations'] = [
                'Monitor cost trends closely',
                'Review cost allocation accuracy'
            ]
        
        if cost_change > 0:
            analysis['recommendations'].insert(0, 'Cost increase detected - identify reduction opportunities')
        else:
            analysis['recommendations'].insert(0, 'Cost decrease detected - verify accuracy and maintain efficiency')
        
        return analysis
    
    # ==================== 報告生成 ====================
    
    async def generate_cost_report(
        self,
        report_type: ReportType,
        target_ids: List[str],
        scope: CalculationScope,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> Dict[str, Any]:
        """生成成本報告"""
        try:
            report_id = f"{report_type.value}_{uuid.uuid4().hex[:8]}"
            
            if report_type == ReportType.COST_SUMMARY:
                return await self._generate_cost_summary_report(report_id, target_ids, scope, start_date, end_date, **kwargs)
            elif report_type == ReportType.COST_BREAKDOWN:
                return await self._generate_cost_breakdown_report(report_id, target_ids, scope, start_date, end_date, **kwargs)
            elif report_type == ReportType.COST_TREND:
                return await self._generate_cost_trend_report(report_id, target_ids, scope, start_date, end_date, **kwargs)
            elif report_type == ReportType.BUDGET_ANALYSIS:
                return await self._generate_budget_analysis_report(report_id, target_ids, scope, start_date, end_date, **kwargs)
            elif report_type == ReportType.ROI_ANALYSIS:
                return await self._generate_roi_analysis_report(report_id, target_ids, scope, start_date, end_date, **kwargs)
            elif report_type == ReportType.OPTIMIZATION_REPORT:
                return await self._generate_optimization_report(report_id, target_ids, scope, start_date, end_date, **kwargs)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
                
        except Exception as e:
            self.logger.error(f"❌ Report generation error: {e}")
            return {'error': str(e), 'report_type': report_type.value}
    
    async def _generate_cost_summary_report(
        self,
        report_id: str,
        target_ids: List[str],
        scope: CalculationScope,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> Dict[str, Any]:
        """生成成本摘要報告"""
        request = CostCalculationRequest(
            calculation_id=f"{report_id}_calc",
            scope=scope,
            target_ids=target_ids,
            start_date=start_date,
            end_date=end_date,
            include_trends=True,
            include_optimizations=True
        )
        
        result = await self.calculate_costs(request)
        
        return {
            'report_id': report_id,
            'report_type': 'cost_summary',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'period': f"{start_date} to {end_date}",
            'scope': scope.value,
            'target_count': len(target_ids),
            'summary': {
                'total_cost': float(result.total_cost),
                'daily_average': float(result.total_cost / Decimal(str((end_date - start_date).days + 1))),
                'cost_per_target': float(result.total_cost / Decimal(str(len(target_ids)))) if target_ids else 0,
                'budget_utilization': result.budget_utilization_rate
            },
            'cost_breakdown': result.costs_by_category,
            'target_costs': result.costs_by_target,
            'trends': result.cost_trends,
            'optimization_opportunities': len(result.optimization_suggestions),
            'top_cost_targets': sorted(
                [(k, float(v)) for k, v in result.costs_by_target.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    async def _generate_optimization_report(
        self,
        report_id: str,
        target_ids: List[str],
        scope: CalculationScope,
        start_date: date,
        end_date: date,
        **kwargs
    ) -> Dict[str, Any]:
        """生成優化報告"""
        request = CostCalculationRequest(
            calculation_id=f"{report_id}_calc",
            scope=scope,
            target_ids=target_ids,
            start_date=start_date,
            end_date=end_date,
            include_optimizations=True
        )
        
        result = await self.calculate_costs(request)
        
        # 計算總優化潛力
        total_savings_potential = sum(
            suggestion.get('potential_savings', 0)
            for suggestion in result.optimization_suggestions
        )
        
        # 按優先級分組建議
        suggestions_by_priority = {}
        for suggestion in result.optimization_suggestions:
            priority = suggestion.get('priority', 'low')
            if priority not in suggestions_by_priority:
                suggestions_by_priority[priority] = []
            suggestions_by_priority[priority].append(suggestion)
        
        return {
            'report_id': report_id,
            'report_type': 'optimization_report',
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'period': f"{start_date} to {end_date}",
            'current_cost': float(result.total_cost),
            'optimization_summary': {
                'total_opportunities': len(result.optimization_suggestions),
                'total_savings_potential': total_savings_potential,
                'savings_percentage': (total_savings_potential / float(result.total_cost) * 100) if result.total_cost > 0 else 0,
                'high_priority_count': len(suggestions_by_priority.get('critical', [])) + len(suggestions_by_priority.get('high', [])),
                'quick_wins_count': len([s for s in result.optimization_suggestions if s.get('potential_savings', 0) > 1000])
            },
            'suggestions_by_priority': suggestions_by_priority,
            'utilization_analysis': {
                'targets_analyzed': len(result.utilization_rates),
                'low_utilization_count': len([r for r in result.utilization_rates.values() if r < 0.5]),
                'average_utilization': statistics.mean(result.utilization_rates.values()) if result.utilization_rates else 0
            },
            'efficiency_analysis': {
                'efficiency_scores': result.efficiency_scores,
                'improvement_opportunities': len([s for s in result.efficiency_scores.values() if s < 0.8])
            }
        }
    
    # ==================== 輔助方法 ====================
    
    def _generate_cache_key(self, request: CostCalculationRequest) -> str:
        """生成緩存鍵"""
        key_data = {
            'scope': request.scope.value,
            'target_ids': sorted(request.target_ids),
            'start_date': request.start_date.isoformat(),
            'end_date': request.end_date.isoformat(),
            'include_flags': [
                request.include_hardware_costs,
                request.include_power_costs,
                request.include_maintenance_costs,
                request.include_labor_costs,
                request.include_overhead_costs
            ]
        }
        
        import hashlib
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _calculate_confidence_score(self, result: CostCalculationResult) -> float:
        """計算計算信心度"""
        score = 1.0
        
        # 基於錯誤和警告數量
        if result.errors:
            score *= 0.5
        
        if result.warnings:
            score *= max(0.7, 1.0 - len(result.warnings) * 0.1)
        
        # 基於數據源覆蓋率
        expected_sources = 4
        actual_sources = len(result.data_sources)
        coverage_score = actual_sources / expected_sources
        score *= coverage_score
        
        return max(0.1, min(1.0, score))
    
    def _create_error_result(
        self,
        request: CostCalculationRequest,
        start_time: datetime,
        error_message: str
    ) -> CostCalculationResult:
        """創建錯誤結果"""
        result = CostCalculationResult(
            calculation_id=request.calculation_id,
            request=request
        )
        
        result.calculated_at = datetime.now(timezone.utc)
        result.calculation_duration_ms = (result.calculated_at - start_time).total_seconds() * 1000
        result.errors = [error_message]
        result.confidence_score = 0.0
        
        return result
    
    async def _cleanup_expired_cache(self):
        """清理過期緩存"""
        try:
            current_time = datetime.now(timezone.utc)
            expired_keys = []
            
            for key, result in self.calculation_cache.items():
                if (current_time - result.calculated_at).total_seconds() > self.cache_ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.calculation_cache[key]
            
            if expired_keys:
                self.logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except Exception as e:
            self.logger.error(f"❌ Cache cleanup error: {e}")
    
    async def _save_calculation_result(self, result: CostCalculationResult):
        """保存計算結果到數據庫"""
        try:
            # 這裡可以實現將計算結果保存到虛擬損益表數據庫
            # 目前暫時跳過實際保存邏輯
            pass
            
        except Exception as e:
            self.logger.error(f"❌ Error saving calculation result: {e}")
    
    async def _notify_cost_monitor(self, result: CostCalculationResult):
        """通知實時成本監控器"""
        try:
            if self.cost_monitor and self.cost_monitor.is_monitoring:
                # 觸發監控更新
                pass
                
        except Exception as e:
            self.logger.error(f"❌ Error notifying cost monitor: {e}")
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """成本計算服務健康檢查"""
        health_status = {
            'system': 'cost_calculation_service',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # 檢查組件健康
            virtual_pnl_health = await self.virtual_pnl_db.health_check()
            hardware_health = await self.hardware_calculator.health_check()
            power_health = await self.power_tracker.health_check()
            labor_health = await self.labor_allocator.health_check()
            
            health_status['components'] = {
                'virtual_pnl_db': virtual_pnl_health['status'],
                'hardware_calculator': hardware_health['status'],
                'power_tracker': power_health['status'],
                'labor_allocator': labor_health['status']
            }
            
            if self.cost_monitor:
                monitor_health = await self.cost_monitor.health_check()
                health_status['components']['cost_monitor'] = monitor_health['status']
            
            # 檢查服務狀態
            health_status['service_info'] = {
                'cache_enabled': self.config['cache_enabled'],
                'cached_results': len(self.calculation_cache),
                'max_concurrent_calculations': self.config['max_concurrent_calculations'],
                'parallel_calculation_enabled': self.config['parallel_calculation_enabled']
            }
            
            # 檢查是否有不健康的組件
            unhealthy_components = [
                name for name, status in health_status['components'].items()
                if status != 'healthy'
            ]
            
            if unhealthy_components:
                health_status['status'] = 'degraded'
                health_status['warning'] = f"Some components are unhealthy: {', '.join(unhealthy_components)}"
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Cost calculation service health check failed: {e}")
        
        return health_status