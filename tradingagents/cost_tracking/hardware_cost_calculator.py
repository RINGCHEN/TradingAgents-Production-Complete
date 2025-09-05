#!/usr/bin/env python3
"""
Hardware Cost Calculator - 硬體成本計算模組
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級硬體成本計算引擎，提供：
- GPU硬體攤銷和折舊計算
- 動態定價模型和成本分攤
- 硬體資源使用率分析
- 多種折舊和攤銷算法
- 實時成本監控和預測
"""

import uuid
import logging
import asyncio
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, NamedTuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from enum import Enum
import statistics
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# ==================== 核心枚舉和數據類型 ====================

class DepreciationMethod(Enum):
    """折舊方法枚舉"""
    STRAIGHT_LINE = "straight_line"           # 直線法
    DECLINING_BALANCE = "declining_balance"    # 餘額遞減法
    UNITS_OF_PRODUCTION = "units_of_production"  # 工作量法
    SUM_OF_YEARS_DIGITS = "sum_of_years_digits"  # 年數總和法
    ACCELERATED = "accelerated"               # 加速折舊法

class AmortizationMethod(Enum):
    """攤銷方法枚舉"""
    STRAIGHT_LINE = "straight_line"           # 直線攤銷
    USAGE_BASED = "usage_based"              # 基於使用量攤銷
    PERFORMANCE_BASED = "performance_based"   # 基於性能攤銷
    TIME_BASED = "time_based"                # 基於時間攤銷

class CostAllocationMethod(Enum):
    """成本分攤方法枚舉"""
    TOKEN_COUNT = "token_count"              # 按Token數量分攤
    COMPUTE_TIME = "compute_time"            # 按計算時間分攤
    REQUEST_COUNT = "request_count"          # 按請求數量分攤
    BANDWIDTH_USAGE = "bandwidth_usage"      # 按頻寬使用分攤
    MEMORY_USAGE = "memory_usage"           # 按記憶體使用分攤
    FIXED_RATIO = "fixed_ratio"             # 固定比例分攤

class HardwareCategory(Enum):
    """硬體類別枚舉"""
    GPU_INFERENCE = "gpu_inference"          # GPU推理硬體
    GPU_TRAINING = "gpu_training"           # GPU訓練硬體
    CPU_COMPUTE = "cpu_compute"             # CPU計算硬體
    MEMORY = "memory"                       # 記憶體
    STORAGE = "storage"                     # 存儲設備
    NETWORK = "network"                     # 網路設備
    COOLING = "cooling"                     # 散熱設備
    POWER_SUPPLY = "power_supply"           # 電源設備

@dataclass
class HardwareAsset:
    """硬體資產配置"""
    asset_id: str
    name: str
    category: HardwareCategory
    model: str
    manufacturer: str
    
    # 成本信息
    acquisition_cost: Decimal
    installation_cost: Decimal = Decimal('0')
    maintenance_cost_annual: Decimal = Decimal('0')
    
    # 技術規格
    specifications: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    # 生命週期
    acquisition_date: date = field(default_factory=date.today)
    warranty_end_date: Optional[date] = None
    expected_useful_life_years: int = 5
    salvage_value: Decimal = Decimal('0')
    
    # 使用統計
    total_compute_hours: float = 0.0
    total_tokens_processed: int = 0
    utilization_rate: float = 0.0
    
    # 狀態
    is_active: bool = True
    location: Optional[str] = None
    assigned_cost_center_id: Optional[uuid.UUID] = None

@dataclass
class DepreciationSchedule:
    """折舊計劃"""
    asset_id: str
    method: DepreciationMethod
    schedule: List[Tuple[date, Decimal]] = field(default_factory=list)
    total_depreciation: Decimal = Decimal('0')
    accumulated_depreciation: Decimal = Decimal('0')
    book_value: Decimal = Decimal('0')
    
    def get_depreciation_for_period(self, start_date: date, end_date: date) -> Decimal:
        """獲取指定期間的折舊金額"""
        period_depreciation = Decimal('0')
        for sched_date, amount in self.schedule:
            if start_date <= sched_date <= end_date:
                period_depreciation += amount
        return period_depreciation

@dataclass
class CostAllocationRule:
    """成本分攤規則"""
    rule_id: str
    name: str
    method: CostAllocationMethod
    allocation_factors: Dict[str, float] = field(default_factory=dict)
    
    # 分攤目標
    target_cost_centers: List[uuid.UUID] = field(default_factory=list)
    target_services: List[str] = field(default_factory=list)
    
    # 權重和比例
    fixed_percentages: Dict[str, float] = field(default_factory=dict)
    minimum_allocation: Decimal = Decimal('0')
    maximum_allocation: Optional[Decimal] = None
    
    is_active: bool = True
    effective_start_date: date = field(default_factory=date.today)
    effective_end_date: Optional[date] = None

@dataclass
class HardwareCostCalculationResult:
    """硬體成本計算結果"""
    asset_id: str
    calculation_date: date
    period_start: date
    period_end: date
    
    # 成本組成
    depreciation_cost: Decimal = Decimal('0')
    amortization_cost: Decimal = Decimal('0')
    maintenance_cost: Decimal = Decimal('0')
    insurance_cost: Decimal = Decimal('0')
    facility_cost: Decimal = Decimal('0')
    
    # 總成本
    total_cost: Decimal = Decimal('0')
    cost_per_hour: Decimal = Decimal('0')
    cost_per_token: Decimal = Decimal('0')
    cost_per_request: Decimal = Decimal('0')
    
    # 分攤結果
    allocation_results: Dict[str, Decimal] = field(default_factory=dict)
    
    # 使用統計
    utilization_hours: float = 0.0
    tokens_processed: int = 0
    requests_served: int = 0
    utilization_rate: float = 0.0
    
    # 計算元數據
    calculation_method: str = ""
    assumptions: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0

# ==================== 核心計算引擎 ====================

class HardwareCostCalculator:
    """
    硬體成本計算器
    
    功能：
    1. 多種折舊方法計算（直線法、餘額遞減法、工作量法等）
    2. 靈活的攤銷算法（基於使用量、性能、時間）
    3. 動態成本分攤（Token、計算時間、請求數等）
    4. 實時成本監控和預測
    5. 硬體資產生命週期管理
    6. 成本效益分析和優化建議
    """
    
    def __init__(self):
        """初始化硬體成本計算器"""
        self.logger = logger
        self.assets: Dict[str, HardwareAsset] = {}
        self.depreciation_schedules: Dict[str, DepreciationSchedule] = {}
        self.allocation_rules: Dict[str, CostAllocationRule] = {}
        
        # 預設配置
        self.default_settings = {
            'depreciation_method': DepreciationMethod.STRAIGHT_LINE,
            'amortization_method': AmortizationMethod.USAGE_BASED,
            'allocation_method': CostAllocationMethod.TOKEN_COUNT,
            'calculation_precision': 8,  # 小數位精度
            'update_frequency_hours': 1,  # 更新頻率
        }
        
        self.logger.info("✅ Hardware Cost Calculator initialized")
    
    # ==================== 資產管理 ====================
    
    def register_hardware_asset(
        self,
        asset: HardwareAsset,
        depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    ) -> bool:
        """註冊硬體資產"""
        try:
            # 驗證資產配置
            if not self._validate_asset(asset):
                raise ValueError(f"Invalid asset configuration: {asset.asset_id}")
            
            # 註冊資產
            self.assets[asset.asset_id] = asset
            
            # 生成折舊計劃
            schedule = self._generate_depreciation_schedule(asset, depreciation_method)
            self.depreciation_schedules[asset.asset_id] = schedule
            
            self.logger.info(f"✅ Registered hardware asset: {asset.name} ({asset.asset_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error registering hardware asset {asset.asset_id}: {e}")
            return False
    
    def update_asset_usage_statistics(
        self,
        asset_id: str,
        compute_hours: float = 0.0,
        tokens_processed: int = 0,
        utilization_rate: Optional[float] = None
    ) -> bool:
        """更新資產使用統計"""
        try:
            if asset_id not in self.assets:
                raise ValueError(f"Asset not found: {asset_id}")
            
            asset = self.assets[asset_id]
            asset.total_compute_hours += compute_hours
            asset.total_tokens_processed += tokens_processed
            
            if utilization_rate is not None:
                asset.utilization_rate = utilization_rate
            
            self.logger.debug(f"Updated usage stats for asset {asset_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating asset usage statistics: {e}")
            return False
    
    # ==================== 折舊計算 ====================
    
    def _generate_depreciation_schedule(
        self,
        asset: HardwareAsset,
        method: DepreciationMethod
    ) -> DepreciationSchedule:
        """生成折舊計劃"""
        schedule = DepreciationSchedule(
            asset_id=asset.asset_id,
            method=method
        )
        
        depreciable_amount = asset.acquisition_cost + asset.installation_cost - asset.salvage_value
        
        if method == DepreciationMethod.STRAIGHT_LINE:
            schedule.schedule = self._calculate_straight_line_depreciation(
                asset, depreciable_amount
            )
        elif method == DepreciationMethod.DECLINING_BALANCE:
            schedule.schedule = self._calculate_declining_balance_depreciation(
                asset, depreciable_amount
            )
        elif method == DepreciationMethod.UNITS_OF_PRODUCTION:
            schedule.schedule = self._calculate_units_of_production_depreciation(
                asset, depreciable_amount
            )
        elif method == DepreciationMethod.SUM_OF_YEARS_DIGITS:
            schedule.schedule = self._calculate_sum_of_years_digits_depreciation(
                asset, depreciable_amount
            )
        else:
            # 預設使用直線法
            schedule.schedule = self._calculate_straight_line_depreciation(
                asset, depreciable_amount
            )
        
        schedule.total_depreciation = sum(amount for _, amount in schedule.schedule)
        schedule.book_value = asset.acquisition_cost + asset.installation_cost - schedule.accumulated_depreciation
        
        return schedule
    
    def _calculate_straight_line_depreciation(
        self,
        asset: HardwareAsset,
        depreciable_amount: Decimal
    ) -> List[Tuple[date, Decimal]]:
        """直線法折舊計算"""
        schedule = []
        useful_life_months = asset.expected_useful_life_years * 12
        monthly_depreciation = (depreciable_amount / useful_life_months).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        current_date = asset.acquisition_date
        for month in range(useful_life_months):
            schedule.append((current_date, monthly_depreciation))
            # 移至下個月
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return schedule
    
    def _calculate_declining_balance_depreciation(
        self,
        asset: HardwareAsset,
        depreciable_amount: Decimal
    ) -> List[Tuple[date, Decimal]]:
        """餘額遞減法折舊計算（雙倍餘額遞減法）"""
        schedule = []
        straight_line_rate = Decimal('1') / Decimal(str(asset.expected_useful_life_years))
        declining_rate = straight_line_rate * Decimal('2')  # 雙倍
        
        book_value = asset.acquisition_cost + asset.installation_cost
        current_date = asset.acquisition_date
        
        for year in range(asset.expected_useful_life_years):
            annual_depreciation = (book_value * declining_rate).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # 確保不超過可折舊金額
            if book_value - annual_depreciation < asset.salvage_value:
                annual_depreciation = book_value - asset.salvage_value
            
            # 分攤到12個月
            monthly_depreciation = (annual_depreciation / 12).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            for month in range(12):
                schedule.append((current_date, monthly_depreciation))
                # 移至下個月
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            book_value -= annual_depreciation
            
            # 如果帳面價值已降至殘值，停止折舊
            if book_value <= asset.salvage_value:
                break
        
        return schedule
    
    def _calculate_units_of_production_depreciation(
        self,
        asset: HardwareAsset,
        depreciable_amount: Decimal
    ) -> List[Tuple[date, Decimal]]:
        """工作量法折舊計算"""
        # 估算總產能（以Token處理能力為例）
        estimated_total_tokens = asset.specifications.get('estimated_lifetime_tokens', 1e12)
        cost_per_token = depreciable_amount / Decimal(str(estimated_total_tokens))
        
        # 這裡返回空計劃，實際折舊將根據使用量動態計算
        return []
    
    def _calculate_sum_of_years_digits_depreciation(
        self,
        asset: HardwareAsset,
        depreciable_amount: Decimal
    ) -> List[Tuple[date, Decimal]]:
        """年數總和法折舊計算"""
        schedule = []
        useful_life = asset.expected_useful_life_years
        sum_of_years = sum(range(1, useful_life + 1))
        
        current_date = asset.acquisition_date
        
        for year in range(1, useful_life + 1):
            remaining_years = useful_life - year + 1
            annual_depreciation = (
                depreciable_amount * Decimal(str(remaining_years)) / Decimal(str(sum_of_years))
            ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # 分攤到12個月
            monthly_depreciation = (annual_depreciation / 12).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            for month in range(12):
                schedule.append((current_date, monthly_depreciation))
                # 移至下個月
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
        
        return schedule
    
    # ==================== 成本分攤 ====================
    
    def create_allocation_rule(
        self,
        rule: CostAllocationRule
    ) -> bool:
        """創建成本分攤規則"""
        try:
            # 驗證規則
            if not self._validate_allocation_rule(rule):
                raise ValueError(f"Invalid allocation rule: {rule.rule_id}")
            
            self.allocation_rules[rule.rule_id] = rule
            
            self.logger.info(f"✅ Created allocation rule: {rule.name} ({rule.rule_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating allocation rule: {e}")
            return False
    
    def calculate_cost_allocation(
        self,
        asset_id: str,
        total_cost: Decimal,
        allocation_rule_id: str,
        usage_metrics: Dict[str, Union[int, float]]
    ) -> Dict[str, Decimal]:
        """計算成本分攤"""
        try:
            if allocation_rule_id not in self.allocation_rules:
                raise ValueError(f"Allocation rule not found: {allocation_rule_id}")
            
            rule = self.allocation_rules[allocation_rule_id]
            allocation_result = {}
            
            if rule.method == CostAllocationMethod.TOKEN_COUNT:
                allocation_result = self._allocate_by_token_count(
                    total_cost, rule, usage_metrics
                )
            elif rule.method == CostAllocationMethod.COMPUTE_TIME:
                allocation_result = self._allocate_by_compute_time(
                    total_cost, rule, usage_metrics
                )
            elif rule.method == CostAllocationMethod.REQUEST_COUNT:
                allocation_result = self._allocate_by_request_count(
                    total_cost, rule, usage_metrics
                )
            elif rule.method == CostAllocationMethod.FIXED_RATIO:
                allocation_result = self._allocate_by_fixed_ratio(
                    total_cost, rule, usage_metrics
                )
            else:
                # 預設均勻分攤
                allocation_result = self._allocate_evenly(total_cost, rule)
            
            return allocation_result
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating cost allocation: {e}")
            return {}
    
    def _allocate_by_token_count(
        self,
        total_cost: Decimal,
        rule: CostAllocationRule,
        usage_metrics: Dict[str, Union[int, float]]
    ) -> Dict[str, Decimal]:
        """按Token數量分攤"""
        token_usage = {}
        total_tokens = 0
        
        # 收集Token使用量
        for target in rule.target_cost_centers:
            target_str = str(target)
            tokens = usage_metrics.get(f"tokens_{target_str}", 0)
            token_usage[target_str] = int(tokens)
            total_tokens += int(tokens)
        
        # 按比例分攤
        allocation = {}
        if total_tokens > 0:
            for target_str, tokens in token_usage.items():
                ratio = Decimal(str(tokens)) / Decimal(str(total_tokens))
                allocated_cost = (total_cost * ratio).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                allocation[target_str] = allocated_cost
        
        return allocation
    
    def _allocate_by_compute_time(
        self,
        total_cost: Decimal,
        rule: CostAllocationRule,
        usage_metrics: Dict[str, Union[int, float]]
    ) -> Dict[str, Decimal]:
        """按計算時間分攤"""
        time_usage = {}
        total_time = 0.0
        
        # 收集計算時間
        for target in rule.target_cost_centers:
            target_str = str(target)
            compute_time = usage_metrics.get(f"compute_time_{target_str}", 0.0)
            time_usage[target_str] = float(compute_time)
            total_time += float(compute_time)
        
        # 按比例分攤
        allocation = {}
        if total_time > 0:
            for target_str, compute_time in time_usage.items():
                ratio = Decimal(str(compute_time)) / Decimal(str(total_time))
                allocated_cost = (total_cost * ratio).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                allocation[target_str] = allocated_cost
        
        return allocation
    
    def _allocate_by_request_count(
        self,
        total_cost: Decimal,
        rule: CostAllocationRule,
        usage_metrics: Dict[str, Union[int, float]]
    ) -> Dict[str, Decimal]:
        """按請求數量分攤"""
        request_usage = {}
        total_requests = 0
        
        # 收集請求數量
        for target in rule.target_cost_centers:
            target_str = str(target)
            requests = usage_metrics.get(f"requests_{target_str}", 0)
            request_usage[target_str] = int(requests)
            total_requests += int(requests)
        
        # 按比例分攤
        allocation = {}
        if total_requests > 0:
            for target_str, requests in request_usage.items():
                ratio = Decimal(str(requests)) / Decimal(str(total_requests))
                allocated_cost = (total_cost * ratio).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                allocation[target_str] = allocated_cost
        
        return allocation
    
    def _allocate_by_fixed_ratio(
        self,
        total_cost: Decimal,
        rule: CostAllocationRule,
        usage_metrics: Dict[str, Union[int, float]]
    ) -> Dict[str, Decimal]:
        """按固定比例分攤"""
        allocation = {}
        
        for target in rule.target_cost_centers:
            target_str = str(target)
            ratio = rule.fixed_percentages.get(target_str, 0.0)
            allocated_cost = (total_cost * Decimal(str(ratio))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            allocation[target_str] = allocated_cost
        
        return allocation
    
    def _allocate_evenly(
        self,
        total_cost: Decimal,
        rule: CostAllocationRule
    ) -> Dict[str, Decimal]:
        """均勻分攤"""
        allocation = {}
        target_count = len(rule.target_cost_centers)
        
        if target_count > 0:
            cost_per_target = (total_cost / Decimal(str(target_count))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            for target in rule.target_cost_centers:
                allocation[str(target)] = cost_per_target
        
        return allocation
    
    # ==================== 成本計算 ====================
    
    async def calculate_hardware_costs(
        self,
        asset_id: str,
        calculation_date: date,
        period_start: date,
        period_end: date,
        usage_metrics: Optional[Dict[str, Union[int, float]]] = None
    ) -> HardwareCostCalculationResult:
        """計算硬體成本"""
        try:
            if asset_id not in self.assets:
                raise ValueError(f"Asset not found: {asset_id}")
            
            asset = self.assets[asset_id]
            schedule = self.depreciation_schedules.get(asset_id)
            
            if not schedule:
                raise ValueError(f"Depreciation schedule not found for asset: {asset_id}")
            
            result = HardwareCostCalculationResult(
                asset_id=asset_id,
                calculation_date=calculation_date,
                period_start=period_start,
                period_end=period_end
            )
            
            # 計算折舊成本
            result.depreciation_cost = schedule.get_depreciation_for_period(
                period_start, period_end
            )
            
            # 計算維護成本（按比例分攤到期間）
            period_days = (period_end - period_start).days + 1
            maintenance_daily = asset.maintenance_cost_annual / Decimal('365')
            result.maintenance_cost = (maintenance_daily * Decimal(str(period_days))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # 計算設施成本（假設占資產價值的5%年費率）
            facility_rate = Decimal('0.05')
            facility_daily = (asset.acquisition_cost * facility_rate) / Decimal('365')
            result.facility_cost = (facility_daily * Decimal(str(period_days))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # 計算保險成本（假設占資產價值的2%年費率）
            insurance_rate = Decimal('0.02')
            insurance_daily = (asset.acquisition_cost * insurance_rate) / Decimal('365')
            result.insurance_cost = (insurance_daily * Decimal(str(period_days))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            
            # 計算總成本
            result.total_cost = (
                result.depreciation_cost +
                result.maintenance_cost +
                result.facility_cost +
                result.insurance_cost
            )
            
            # 計算單位成本
            if usage_metrics:
                tokens = usage_metrics.get('tokens_processed', 0)
                compute_hours = usage_metrics.get('compute_hours', 0.0)
                requests = usage_metrics.get('requests_served', 0)
                
                result.tokens_processed = int(tokens)
                result.utilization_hours = float(compute_hours)
                result.requests_served = int(requests)
                
                if compute_hours > 0:
                    result.cost_per_hour = (result.total_cost / Decimal(str(compute_hours))).quantize(
                        Decimal('0.0001'), rounding=ROUND_HALF_UP
                    )
                
                if tokens > 0:
                    result.cost_per_token = (result.total_cost / Decimal(str(tokens))).quantize(
                        Decimal('0.00000001'), rounding=ROUND_HALF_UP
                    )
                
                if requests > 0:
                    result.cost_per_request = (result.total_cost / Decimal(str(requests))).quantize(
                        Decimal('0.0001'), rounding=ROUND_HALF_UP
                    )
            
            # 設置計算元數據
            result.calculation_method = f"Depreciation: {schedule.method.value}"
            result.assumptions = {
                'facility_cost_rate': float(facility_rate),
                'insurance_cost_rate': float(insurance_rate),
                'maintenance_cost_annual': float(asset.maintenance_cost_annual)
            }
            result.confidence_score = 0.9  # 基於數據質量的信心度
            
            self.logger.info(f"✅ Calculated hardware costs for {asset_id}: ${result.total_cost}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating hardware costs for {asset_id}: {e}")
            raise
    
    async def calculate_all_hardware_costs(
        self,
        calculation_date: date,
        period_start: date,
        period_end: date,
        usage_metrics_by_asset: Optional[Dict[str, Dict[str, Union[int, float]]]] = None
    ) -> Dict[str, HardwareCostCalculationResult]:
        """計算所有硬體資產的成本"""
        results = {}
        
        for asset_id in self.assets.keys():
            try:
                usage_metrics = None
                if usage_metrics_by_asset:
                    usage_metrics = usage_metrics_by_asset.get(asset_id)
                
                result = await self.calculate_hardware_costs(
                    asset_id, calculation_date, period_start, period_end, usage_metrics
                )
                results[asset_id] = result
                
            except Exception as e:
                self.logger.error(f"❌ Error calculating costs for asset {asset_id}: {e}")
                continue
        
        self.logger.info(f"✅ Calculated costs for {len(results)} hardware assets")
        return results
    
    # ==================== 預測和優化 ====================
    
    def predict_future_costs(
        self,
        asset_id: str,
        prediction_months: int = 12,
        usage_growth_rate: float = 0.1
    ) -> Dict[str, Any]:
        """預測未來成本"""
        try:
            if asset_id not in self.assets:
                raise ValueError(f"Asset not found: {asset_id}")
            
            asset = self.assets[asset_id]
            schedule = self.depreciation_schedules.get(asset_id)
            
            predictions = []
            current_date = date.today()
            
            for month in range(prediction_months):
                # 計算該月的日期範圍
                if month == 0:
                    month_start = current_date.replace(day=1)
                else:
                    if month_start.month == 12:
                        month_start = month_start.replace(year=month_start.year + 1, month=1)
                    else:
                        month_start = month_start.replace(month=month_start.month + 1)
                
                # 計算月末
                if month_start.month == 12:
                    month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
                else:
                    month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
                
                # 預測使用量（基於增長率）
                base_tokens = asset.total_tokens_processed / 12 if asset.total_tokens_processed > 0 else 1000000
                predicted_tokens = base_tokens * (1 + usage_growth_rate) ** month
                
                base_hours = asset.total_compute_hours / 12 if asset.total_compute_hours > 0 else 100
                predicted_hours = base_hours * (1 + usage_growth_rate) ** month
                
                # 模擬使用指標
                usage_metrics = {
                    'tokens_processed': int(predicted_tokens),
                    'compute_hours': predicted_hours,
                    'requests_served': int(predicted_tokens / 1000)  # 假設每請求1000 tokens
                }
                
                # 異步計算成本
                loop = asyncio.get_event_loop()
                cost_result = loop.run_until_complete(
                    self.calculate_hardware_costs(
                        asset_id, month_start, month_start, month_end, usage_metrics
                    )
                )
                
                predictions.append({
                    'month': month + 1,
                    'period': f"{month_start} to {month_end}",
                    'predicted_total_cost': float(cost_result.total_cost),
                    'predicted_tokens': int(predicted_tokens),
                    'predicted_hours': predicted_hours,
                    'cost_per_token': float(cost_result.cost_per_token),
                    'cost_per_hour': float(cost_result.cost_per_hour)
                })
            
            # 計算匯總統計
            total_predicted_cost = sum(p['predicted_total_cost'] for p in predictions)
            average_monthly_cost = total_predicted_cost / len(predictions)
            
            return {
                'asset_id': asset_id,
                'prediction_period_months': prediction_months,
                'usage_growth_rate': usage_growth_rate,
                'total_predicted_cost': total_predicted_cost,
                'average_monthly_cost': average_monthly_cost,
                'monthly_predictions': predictions,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error predicting future costs: {e}")
            return {}
    
    def generate_cost_optimization_recommendations(
        self,
        asset_id: str,
        cost_result: HardwareCostCalculationResult
    ) -> List[Dict[str, Any]]:
        """生成成本優化建議"""
        recommendations = []
        
        try:
            asset = self.assets[asset_id]
            
            # 檢查利用率
            if cost_result.utilization_rate < 0.5:
                recommendations.append({
                    'type': 'utilization_optimization',
                    'priority': 'high',
                    'description': f'硬體利用率過低 ({cost_result.utilization_rate:.1%})，建議提高使用效率或考慮資源重新配置',
                    'potential_savings': float(cost_result.total_cost * Decimal('0.3')),
                    'action_items': [
                        '分析低利用率原因',
                        '優化任務調度算法',
                        '考慮多租戶共享',
                        '評估資源縮減可能性'
                    ]
                })
            
            # 檢查每Token成本
            if cost_result.cost_per_token > Decimal('0.001'):
                recommendations.append({
                    'type': 'efficiency_optimization',
                    'priority': 'medium',
                    'description': f'每Token成本偏高 (${cost_result.cost_per_token:.6f})，建議優化模型推理效率',
                    'potential_savings': float(cost_result.total_cost * Decimal('0.15')),
                    'action_items': [
                        '評估模型量化可能性',
                        '優化批處理大小',
                        '考慮模型蒸餾技術',
                        '檢查推理框架效率'
                    ]
                })
            
            # 檢查維護成本比例
            maintenance_ratio = cost_result.maintenance_cost / cost_result.total_cost
            if maintenance_ratio > Decimal('0.2'):
                recommendations.append({
                    'type': 'maintenance_optimization',
                    'priority': 'medium',
                    'description': f'維護成本占總成本比例過高 ({maintenance_ratio:.1%})，建議優化維護策略',
                    'potential_savings': float(cost_result.maintenance_cost * Decimal('0.25')),
                    'action_items': [
                        '重新評估維護合約',
                        '考慮預防性維護',
                        '培養內部維護能力',
                        '評估設備升級需求'
                    ]
                })
            
            # 檢查折舊方法
            schedule = self.depreciation_schedules.get(asset_id)
            if schedule and schedule.method == DepreciationMethod.STRAIGHT_LINE:
                recommendations.append({
                    'type': 'depreciation_optimization',
                    'priority': 'low',
                    'description': '目前使用直線折舊法，可考慮加速折舊法以獲得稅務優勢',
                    'potential_savings': float(cost_result.depreciation_cost * Decimal('0.1')),
                    'action_items': [
                        '諮詢稅務專家',
                        '評估加速折舊法影響',
                        '考慮設備更新計劃',
                        '分析現金流影響'
                    ]
                })
            
        except Exception as e:
            self.logger.error(f"❌ Error generating optimization recommendations: {e}")
        
        return recommendations
    
    # ==================== 驗證和輔助方法 ====================
    
    def _validate_asset(self, asset: HardwareAsset) -> bool:
        """驗證資產配置"""
        if not asset.asset_id or not asset.name:
            return False
        
        if asset.acquisition_cost <= 0:
            return False
        
        if asset.expected_useful_life_years <= 0:
            return False
        
        return True
    
    def _validate_allocation_rule(self, rule: CostAllocationRule) -> bool:
        """驗證分攤規則"""
        if not rule.rule_id or not rule.name:
            return False
        
        if not rule.target_cost_centers:
            return False
        
        # 檢查固定比例總和
        if rule.method == CostAllocationMethod.FIXED_RATIO:
            total_percentage = sum(rule.fixed_percentages.values())
            if abs(total_percentage - 1.0) > 0.01:
                return False
        
        return True
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """硬體成本計算器健康檢查"""
        health_status = {
            'system': 'hardware_cost_calculator',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # 檢查資產數量
            health_status['components']['assets'] = {
                'total_count': len(self.assets),
                'active_count': sum(1 for a in self.assets.values() if a.is_active),
                'categories': {}
            }
            
            # 按類別統計
            for asset in self.assets.values():
                category = asset.category.value
                if category not in health_status['components']['assets']['categories']:
                    health_status['components']['assets']['categories'][category] = 0
                health_status['components']['assets']['categories'][category] += 1
            
            # 檢查折舊計劃
            health_status['components']['depreciation_schedules'] = {
                'total_count': len(self.depreciation_schedules),
                'methods': {}
            }
            
            for schedule in self.depreciation_schedules.values():
                method = schedule.method.value
                if method not in health_status['components']['depreciation_schedules']['methods']:
                    health_status['components']['depreciation_schedules']['methods'][method] = 0
                health_status['components']['depreciation_schedules']['methods'][method] += 1
            
            # 檢查分攤規則
            health_status['components']['allocation_rules'] = {
                'total_count': len(self.allocation_rules),
                'active_count': sum(1 for r in self.allocation_rules.values() if r.is_active)
            }
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Hardware cost calculator health check failed: {e}")
        
        return health_status


# ==================== 預設配置工廠 ====================

class HardwareCostConfigurationFactory:
    """硬體成本配置工廠"""
    
    @staticmethod
    def create_gpu_inference_asset(
        asset_id: str,
        model: str = "RTX 4090",
        acquisition_cost: Decimal = Decimal('1500'),
        expected_life_years: int = 4
    ) -> HardwareAsset:
        """創建GPU推理硬體資產配置"""
        return HardwareAsset(
            asset_id=asset_id,
            name=f"GPU Inference Card - {model}",
            category=HardwareCategory.GPU_INFERENCE,
            model=model,
            manufacturer="NVIDIA",
            acquisition_cost=acquisition_cost,
            installation_cost=acquisition_cost * Decimal('0.05'),
            maintenance_cost_annual=acquisition_cost * Decimal('0.1'),
            expected_useful_life_years=expected_life_years,
            salvage_value=acquisition_cost * Decimal('0.1'),
            specifications={
                'memory_gb': 24,
                'compute_capability': '8.9',
                'max_power_consumption_watts': 450,
                'estimated_lifetime_tokens': 5e11
            },
            performance_metrics={
                'tokens_per_second': 1000,
                'max_batch_size': 32,
                'memory_bandwidth_gb_s': 1008
            }
        )
    
    @staticmethod
    def create_token_based_allocation_rule(
        rule_id: str,
        target_cost_centers: List[uuid.UUID]
    ) -> CostAllocationRule:
        """創建基於Token的分攤規則"""
        return CostAllocationRule(
            rule_id=rule_id,
            name="Token-Based Cost Allocation",
            method=CostAllocationMethod.TOKEN_COUNT,
            target_cost_centers=target_cost_centers,
            minimum_allocation=Decimal('10.0')
        )