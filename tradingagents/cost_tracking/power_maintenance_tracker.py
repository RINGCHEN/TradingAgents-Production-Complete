#!/usr/bin/env python3
"""
Power and Maintenance Cost Tracker - 電力和維護成本追蹤系統
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級電力和維護成本追蹤引擎，提供：
- 實時電力消耗監控和成本計算
- 動態電價和峰谷電價處理
- 維護成本追蹤和預測性維護
- 環境成本分析（散熱、UPS等）
- 成本優化建議和能效分析
"""

import uuid
import logging
import asyncio
import aiofiles
from datetime import datetime, timezone, date, time, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, NamedTuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# ==================== 核心枚舉和數據類型 ====================

class PowerSource(Enum):
    """電力來源枚舉"""
    GRID = "grid"                    # 電網供電
    UPS = "ups"                      # UPS供電
    GENERATOR = "generator"          # 發電機
    SOLAR = "solar"                  # 太陽能
    BATTERY = "battery"              # 電池儲能

class ElectricityPriceType(Enum):
    """電價類型枚舉"""
    FLAT_RATE = "flat_rate"          # 平價
    TIME_OF_USE = "time_of_use"      # 分時電價
    DEMAND_BASED = "demand_based"    # 需量電價
    REAL_TIME = "real_time"          # 即時電價
    SEASONAL = "seasonal"            # 季節性電價

class MaintenanceType(Enum):
    """維護類型枚舉"""
    PREVENTIVE = "preventive"        # 預防性維護
    CORRECTIVE = "corrective"        # 修復性維護
    PREDICTIVE = "predictive"        # 預測性維護
    EMERGENCY = "emergency"          # 緊急維護
    ROUTINE = "routine"              # 例行維護

class MaintenanceStatus(Enum):
    """維護狀態枚舉"""
    SCHEDULED = "scheduled"          # 已排程
    IN_PROGRESS = "in_progress"      # 進行中
    COMPLETED = "completed"          # 已完成
    CANCELLED = "cancelled"          # 已取消
    OVERDUE = "overdue"             # 逾期

@dataclass
class PowerConsumptionRecord:
    """電力消耗記錄"""
    record_id: str
    asset_id: str
    timestamp: datetime
    
    # 電力消耗數據
    power_consumption_watts: float
    voltage: float = 0.0
    current_amperes: float = 0.0
    power_factor: float = 1.0
    
    # 環境數據
    temperature_celsius: Optional[float] = None
    humidity_percentage: Optional[float] = None
    
    # 工作負載數據
    cpu_utilization: Optional[float] = None
    gpu_utilization: Optional[float] = None
    memory_utilization: Optional[float] = None
    
    # 來源和元數據
    power_source: PowerSource = PowerSource.GRID
    measurement_device: Optional[str] = None
    measurement_accuracy: float = 0.95
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'record_id': self.record_id,
            'asset_id': self.asset_id,
            'timestamp': self.timestamp.isoformat(),
            'power_consumption_watts': self.power_consumption_watts,
            'voltage': self.voltage,
            'current_amperes': self.current_amperes,
            'power_factor': self.power_factor,
            'temperature_celsius': self.temperature_celsius,
            'humidity_percentage': self.humidity_percentage,
            'cpu_utilization': self.cpu_utilization,
            'gpu_utilization': self.gpu_utilization,
            'memory_utilization': self.memory_utilization,
            'power_source': self.power_source.value,
            'measurement_device': self.measurement_device,
            'measurement_accuracy': self.measurement_accuracy
        }

@dataclass
class ElectricityPriceSchedule:
    """電價時程表"""
    price_id: str
    name: str
    price_type: ElectricityPriceType
    currency: str = "USD"
    
    # 價格結構
    base_price_per_kwh: Decimal = Decimal('0')
    demand_charge_per_kw: Decimal = Decimal('0')
    
    # 分時電價（如果適用）
    peak_hours: List[Tuple[time, time]] = field(default_factory=list)
    off_peak_hours: List[Tuple[time, time]] = field(default_factory=list)
    peak_price_per_kwh: Decimal = Decimal('0')
    off_peak_price_per_kwh: Decimal = Decimal('0')
    
    # 季節性調整
    seasonal_multipliers: Dict[str, float] = field(default_factory=dict)
    
    # 需量費用
    demand_window_minutes: int = 15
    demand_threshold_kw: Decimal = Decimal('0')
    
    # 有效期間
    effective_start_date: date = field(default_factory=date.today)
    effective_end_date: Optional[date] = None
    
    def get_price_at_time(self, timestamp: datetime, demand_kw: Optional[Decimal] = None) -> Decimal:
        """獲取指定時間的電價"""
        base_price = self.base_price_per_kwh
        
        # 處理分時電價
        if self.price_type == ElectricityPriceType.TIME_OF_USE:
            current_time = timestamp.time()
            is_peak = any(start <= current_time <= end for start, end in self.peak_hours)
            
            if is_peak:
                base_price = self.peak_price_per_kwh
            else:
                base_price = self.off_peak_price_per_kwh
        
        # 處理季節性調整
        if self.seasonal_multipliers:
            month = timestamp.strftime('%m')
            multiplier = self.seasonal_multipliers.get(month, 1.0)
            base_price *= Decimal(str(multiplier))
        
        # 處理需量費用
        total_price = base_price
        if demand_kw and demand_kw > self.demand_threshold_kw:
            demand_charge = (demand_kw - self.demand_threshold_kw) * self.demand_charge_per_kw
            total_price += demand_charge
        
        return total_price.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

@dataclass
class MaintenanceRecord:
    """維護記錄"""
    maintenance_id: str
    asset_id: str
    maintenance_type: MaintenanceType
    status: MaintenanceStatus
    
    # 時間信息
    scheduled_date: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 成本信息
    labor_cost: Decimal = Decimal('0')
    parts_cost: Decimal = Decimal('0')
    contractor_cost: Decimal = Decimal('0')
    downtime_cost: Decimal = Decimal('0')
    
    # 維護詳情
    description: str = ""
    parts_replaced: List[str] = field(default_factory=list)
    work_performed: List[str] = field(default_factory=list)
    
    # 性能影響
    performance_impact: Dict[str, Any] = field(default_factory=dict)
    estimated_life_extension_months: Optional[int] = None
    
    # 人員信息
    technician_ids: List[str] = field(default_factory=list)
    contractor_name: Optional[str] = None
    
    # 質量信息
    quality_rating: Optional[int] = None  # 1-10評分
    follow_up_required: bool = False
    warranty_period_days: Optional[int] = None
    
    @property
    def total_cost(self) -> Decimal:
        """總維護成本"""
        return self.labor_cost + self.parts_cost + self.contractor_cost + self.downtime_cost
    
    @property
    def duration_hours(self) -> Optional[float]:
        """維護持續時間（小時）"""
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
            return duration.total_seconds() / 3600
        return None

@dataclass
class CostCalculationResult:
    """成本計算結果"""
    asset_id: str
    calculation_period_start: datetime
    calculation_period_end: datetime
    
    # 電力成本
    total_electricity_cost: Decimal = Decimal('0')
    total_energy_consumption_kwh: Decimal = Decimal('0')
    average_power_consumption_watts: float = 0.0
    peak_demand_kw: Decimal = Decimal('0')
    
    # 維護成本
    total_maintenance_cost: Decimal = Decimal('0')
    maintenance_records_count: int = 0
    preventive_maintenance_cost: Decimal = Decimal('0')
    corrective_maintenance_cost: Decimal = Decimal('0')
    
    # 環境成本
    cooling_cost: Decimal = Decimal('0')
    ups_cost: Decimal = Decimal('0')
    facility_overhead_cost: Decimal = Decimal('0')
    
    # 總成本
    total_cost: Decimal = Decimal('0')
    
    # 效率指標
    power_usage_effectiveness: Optional[float] = None  # PUE值
    cost_per_kwh: Decimal = Decimal('0')
    cost_per_compute_hour: Decimal = Decimal('0')
    
    # 成本分解
    cost_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    
    def calculate_totals(self):
        """計算總計"""
        self.total_cost = (
            self.total_electricity_cost +
            self.total_maintenance_cost +
            self.cooling_cost +
            self.ups_cost +
            self.facility_overhead_cost
        )
        
        self.cost_breakdown = {
            'electricity': self.total_electricity_cost,
            'maintenance': self.total_maintenance_cost,
            'cooling': self.cooling_cost,
            'ups': self.ups_cost,
            'facility': self.facility_overhead_cost
        }

# ==================== 核心追蹤引擎 ====================

class PowerMaintenanceTracker:
    """
    電力和維護成本追蹤器
    
    功能：
    1. 實時電力消耗監控和成本計算
    2. 動態電價處理和峰谷電價優化
    3. 維護成本追蹤和預測性維護
    4. 環境成本分析（散熱、UPS等）
    5. 成本優化建議和能效分析
    6. 歷史數據分析和趨勢預測
    """
    
    def __init__(self, data_directory: str = "./data/cost_tracking"):
        """初始化電力和維護成本追蹤器"""
        self.logger = logger
        self.data_directory = data_directory
        
        # 內存數據存儲
        self.power_consumption_records: List[PowerConsumptionRecord] = []
        self.maintenance_records: List[MaintenanceRecord] = []
        self.price_schedules: Dict[str, ElectricityPriceSchedule] = {}
        
        # 配置
        self.config = {
            'max_records_in_memory': 10000,
            'data_retention_days': 90,
            'calculation_interval_minutes': 15,
            'auto_backup_enabled': True,
            'cooling_efficiency_ratio': 0.4,  # 散熱用電占IT用電比例
            'ups_efficiency': 0.95,  # UPS效率
            'facility_overhead_ratio': 0.1,  # 設施開銷比例
        }
        
        # 初始化
        self._ensure_data_directory()
        
        self.logger.info("✅ Power and Maintenance Cost Tracker initialized")
    
    def _ensure_data_directory(self):
        """確保數據目錄存在"""
        import os
        os.makedirs(self.data_directory, exist_ok=True)
        os.makedirs(f"{self.data_directory}/power", exist_ok=True)
        os.makedirs(f"{self.data_directory}/maintenance", exist_ok=True)
        os.makedirs(f"{self.data_directory}/backups", exist_ok=True)
    
    # ==================== 電力消耗追蹤 ====================
    
    async def record_power_consumption(
        self,
        asset_id: str,
        power_consumption_watts: float,
        voltage: float = 0.0,
        current_amperes: float = 0.0,
        power_factor: float = 1.0,
        power_source: PowerSource = PowerSource.GRID,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """記錄電力消耗數據"""
        try:
            record = PowerConsumptionRecord(
                record_id=str(uuid.uuid4()),
                asset_id=asset_id,
                timestamp=datetime.now(timezone.utc),
                power_consumption_watts=power_consumption_watts,
                voltage=voltage,
                current_amperes=current_amperes,
                power_factor=power_factor,
                power_source=power_source
            )
            
            # 添加額外數據
            if additional_data:
                if 'temperature_celsius' in additional_data:
                    record.temperature_celsius = additional_data['temperature_celsius']
                if 'humidity_percentage' in additional_data:
                    record.humidity_percentage = additional_data['humidity_percentage']
                if 'cpu_utilization' in additional_data:
                    record.cpu_utilization = additional_data['cpu_utilization']
                if 'gpu_utilization' in additional_data:
                    record.gpu_utilization = additional_data['gpu_utilization']
                if 'memory_utilization' in additional_data:
                    record.memory_utilization = additional_data['memory_utilization']
                if 'measurement_device' in additional_data:
                    record.measurement_device = additional_data['measurement_device']
            
            # 添加到內存
            self.power_consumption_records.append(record)
            
            # 管理內存使用
            if len(self.power_consumption_records) > self.config['max_records_in_memory']:
                # 保存舊記錄到文件並從內存中移除
                await self._archive_old_power_records()
            
            self.logger.debug(f"Recorded power consumption for {asset_id}: {power_consumption_watts}W")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error recording power consumption: {e}")
            return False
    
    async def batch_record_power_consumption(
        self,
        records: List[Dict[str, Any]]
    ) -> int:
        """批量記錄電力消耗數據"""
        successful_records = 0
        
        for record_data in records:
            try:
                success = await self.record_power_consumption(
                    asset_id=record_data['asset_id'],
                    power_consumption_watts=record_data['power_consumption_watts'],
                    voltage=record_data.get('voltage', 0.0),
                    current_amperes=record_data.get('current_amperes', 0.0),
                    power_factor=record_data.get('power_factor', 1.0),
                    power_source=PowerSource(record_data.get('power_source', 'grid')),
                    additional_data=record_data.get('additional_data')
                )
                
                if success:
                    successful_records += 1
                    
            except Exception as e:
                self.logger.error(f"❌ Error in batch record: {e}")
                continue
        
        self.logger.info(f"✅ Batch recorded {successful_records}/{len(records)} power consumption records")
        return successful_records
    
    # ==================== 電價管理 ====================
    
    def configure_electricity_price_schedule(
        self,
        schedule: ElectricityPriceSchedule
    ) -> bool:
        """配置電價時程表"""
        try:
            # 驗證電價配置
            if not self._validate_price_schedule(schedule):
                raise ValueError(f"Invalid price schedule: {schedule.price_id}")
            
            self.price_schedules[schedule.price_id] = schedule
            
            self.logger.info(f"✅ Configured electricity price schedule: {schedule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error configuring price schedule: {e}")
            return False
    
    def calculate_electricity_cost(
        self,
        asset_id: str,
        start_time: datetime,
        end_time: datetime,
        price_schedule_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """計算電力成本"""
        try:
            # 獲取電價時程表
            if not price_schedule_id:
                # 使用預設電價（如果有）
                if 'default' in self.price_schedules:
                    price_schedule = self.price_schedules['default']
                else:
                    # 使用固定電價
                    price_schedule = ElectricityPriceSchedule(
                        price_id='default',
                        name='Default Fixed Rate',
                        price_type=ElectricityPriceType.FLAT_RATE,
                        base_price_per_kwh=Decimal('0.12')  # $0.12/kWh
                    )
            else:
                if price_schedule_id not in self.price_schedules:
                    raise ValueError(f"Price schedule not found: {price_schedule_id}")
                price_schedule = self.price_schedules[price_schedule_id]
            
            # 獲取期間內的電力消耗記錄
            relevant_records = [
                record for record in self.power_consumption_records
                if (record.asset_id == asset_id and 
                    start_time <= record.timestamp <= end_time)
            ]
            
            if not relevant_records:
                return {
                    'asset_id': asset_id,
                    'period': f"{start_time} to {end_time}",
                    'total_cost': 0.0,
                    'total_energy_kwh': 0.0,
                    'average_power_w': 0.0,
                    'peak_demand_kw': 0.0,
                    'cost_breakdown': {}
                }
            
            # 計算總能耗
            total_energy_kwh = Decimal('0')
            peak_demand_kw = Decimal('0')
            cost_breakdown = {
                'base_cost': Decimal('0'),
                'peak_cost': Decimal('0'),
                'off_peak_cost': Decimal('0'),
                'demand_charges': Decimal('0')
            }
            
            # 按時間段計算成本
            for i in range(len(relevant_records) - 1):
                current_record = relevant_records[i]
                next_record = relevant_records[i + 1]
                
                # 計算時間間隔（小時）
                time_interval_hours = (next_record.timestamp - current_record.timestamp).total_seconds() / 3600
                
                # 計算能耗（kWh）
                energy_kwh = Decimal(str(current_record.power_consumption_watts)) * Decimal(str(time_interval_hours)) / Decimal('1000')
                total_energy_kwh += energy_kwh
                
                # 更新峰值需量
                demand_kw = Decimal(str(current_record.power_consumption_watts)) / Decimal('1000')
                if demand_kw > peak_demand_kw:
                    peak_demand_kw = demand_kw
                
                # 計算該時段的成本
                price_per_kwh = price_schedule.get_price_at_time(current_record.timestamp, demand_kw)
                period_cost = energy_kwh * price_per_kwh
                
                # 分類成本
                if price_schedule.price_type == ElectricityPriceType.TIME_OF_USE:
                    current_time = current_record.timestamp.time()
                    is_peak = any(start <= current_time <= end for start, end in price_schedule.peak_hours)
                    
                    if is_peak:
                        cost_breakdown['peak_cost'] += period_cost
                    else:
                        cost_breakdown['off_peak_cost'] += period_cost
                else:
                    cost_breakdown['base_cost'] += period_cost
            
            # 計算需量費用
            if price_schedule.demand_charge_per_kw > 0 and peak_demand_kw > price_schedule.demand_threshold_kw:
                demand_charges = (peak_demand_kw - price_schedule.demand_threshold_kw) * price_schedule.demand_charge_per_kw
                cost_breakdown['demand_charges'] = demand_charges
            
            total_cost = sum(cost_breakdown.values())
            average_power_w = sum(r.power_consumption_watts for r in relevant_records) / len(relevant_records)
            
            return {
                'asset_id': asset_id,
                'period': f"{start_time} to {end_time}",
                'price_schedule': price_schedule.name,
                'total_cost': float(total_cost),
                'total_energy_kwh': float(total_energy_kwh),
                'average_power_w': average_power_w,
                'peak_demand_kw': float(peak_demand_kw),
                'cost_breakdown': {k: float(v) for k, v in cost_breakdown.items()},
                'records_processed': len(relevant_records),
                'cost_per_kwh_average': float(total_cost / total_energy_kwh) if total_energy_kwh > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating electricity cost: {e}")
            return {}
    
    # ==================== 維護成本追蹤 ====================
    
    async def record_maintenance(
        self,
        asset_id: str,
        maintenance_type: MaintenanceType,
        scheduled_date: datetime,
        description: str,
        labor_cost: Decimal = Decimal('0'),
        parts_cost: Decimal = Decimal('0'),
        contractor_cost: Decimal = Decimal('0'),
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """記錄維護活動"""
        try:
            maintenance_record = MaintenanceRecord(
                maintenance_id=str(uuid.uuid4()),
                asset_id=asset_id,
                maintenance_type=maintenance_type,
                status=MaintenanceStatus.SCHEDULED,
                scheduled_date=scheduled_date,
                description=description,
                labor_cost=labor_cost,
                parts_cost=parts_cost,
                contractor_cost=contractor_cost
            )
            
            # 添加額外數據
            if additional_data:
                if 'parts_replaced' in additional_data:
                    maintenance_record.parts_replaced = additional_data['parts_replaced']
                if 'work_performed' in additional_data:
                    maintenance_record.work_performed = additional_data['work_performed']
                if 'technician_ids' in additional_data:
                    maintenance_record.technician_ids = additional_data['technician_ids']
                if 'contractor_name' in additional_data:
                    maintenance_record.contractor_name = additional_data['contractor_name']
                if 'estimated_life_extension_months' in additional_data:
                    maintenance_record.estimated_life_extension_months = additional_data['estimated_life_extension_months']
                if 'downtime_cost' in additional_data:
                    maintenance_record.downtime_cost = Decimal(str(additional_data['downtime_cost']))
            
            self.maintenance_records.append(maintenance_record)
            
            self.logger.info(f"✅ Recorded maintenance for {asset_id}: {maintenance_type.value}")
            return maintenance_record.maintenance_id
            
        except Exception as e:
            self.logger.error(f"❌ Error recording maintenance: {e}")
            return ""
    
    async def update_maintenance_status(
        self,
        maintenance_id: str,
        status: MaintenanceStatus,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新維護狀態"""
        try:
            # 找到維護記錄
            maintenance_record = None
            for record in self.maintenance_records:
                if record.maintenance_id == maintenance_id:
                    maintenance_record = record
                    break
            
            if not maintenance_record:
                raise ValueError(f"Maintenance record not found: {maintenance_id}")
            
            # 更新狀態
            maintenance_record.status = status
            
            # 根據狀態更新時間戳
            now = datetime.now(timezone.utc)
            if status == MaintenanceStatus.IN_PROGRESS:
                maintenance_record.started_at = now
            elif status == MaintenanceStatus.COMPLETED:
                maintenance_record.completed_at = now
                if not maintenance_record.started_at:
                    maintenance_record.started_at = now
            
            # 更新額外數據
            if additional_data:
                if 'labor_cost' in additional_data:
                    maintenance_record.labor_cost = Decimal(str(additional_data['labor_cost']))
                if 'parts_cost' in additional_data:
                    maintenance_record.parts_cost = Decimal(str(additional_data['parts_cost']))
                if 'contractor_cost' in additional_data:
                    maintenance_record.contractor_cost = Decimal(str(additional_data['contractor_cost']))
                if 'downtime_cost' in additional_data:
                    maintenance_record.downtime_cost = Decimal(str(additional_data['downtime_cost']))
                if 'quality_rating' in additional_data:
                    maintenance_record.quality_rating = additional_data['quality_rating']
                if 'follow_up_required' in additional_data:
                    maintenance_record.follow_up_required = additional_data['follow_up_required']
                if 'warranty_period_days' in additional_data:
                    maintenance_record.warranty_period_days = additional_data['warranty_period_days']
                if 'performance_impact' in additional_data:
                    maintenance_record.performance_impact = additional_data['performance_impact']
            
            self.logger.info(f"✅ Updated maintenance status: {maintenance_id} -> {status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating maintenance status: {e}")
            return False
    
    def calculate_maintenance_costs(
        self,
        asset_id: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """計算維護成本"""
        try:
            # 獲取期間內的維護記錄
            relevant_records = [
                record for record in self.maintenance_records
                if (record.asset_id == asset_id and 
                    start_date <= record.scheduled_date.date() <= end_date)
            ]
            
            if not relevant_records:
                return {
                    'asset_id': asset_id,
                    'period': f"{start_date} to {end_date}",
                    'total_cost': 0.0,
                    'maintenance_count': 0,
                    'cost_breakdown': {},
                    'maintenance_types': {}
                }
            
            # 計算成本分解
            cost_breakdown = {
                'labor_cost': Decimal('0'),
                'parts_cost': Decimal('0'),
                'contractor_cost': Decimal('0'),
                'downtime_cost': Decimal('0')
            }
            
            maintenance_types = {}
            
            for record in relevant_records:
                cost_breakdown['labor_cost'] += record.labor_cost
                cost_breakdown['parts_cost'] += record.parts_cost
                cost_breakdown['contractor_cost'] += record.contractor_cost
                cost_breakdown['downtime_cost'] += record.downtime_cost
                
                # 統計維護類型
                mtype = record.maintenance_type.value
                if mtype not in maintenance_types:
                    maintenance_types[mtype] = {
                        'count': 0,
                        'total_cost': Decimal('0'),
                        'average_cost': Decimal('0')
                    }
                
                maintenance_types[mtype]['count'] += 1
                maintenance_types[mtype]['total_cost'] += record.total_cost
            
            # 計算平均成本
            for mtype_data in maintenance_types.values():
                if mtype_data['count'] > 0:
                    mtype_data['average_cost'] = mtype_data['total_cost'] / mtype_data['count']
            
            total_cost = sum(cost_breakdown.values())
            
            return {
                'asset_id': asset_id,
                'period': f"{start_date} to {end_date}",
                'total_cost': float(total_cost),
                'maintenance_count': len(relevant_records),
                'cost_breakdown': {k: float(v) for k, v in cost_breakdown.items()},
                'maintenance_types': {
                    k: {
                        'count': v['count'],
                        'total_cost': float(v['total_cost']),
                        'average_cost': float(v['average_cost'])
                    }
                    for k, v in maintenance_types.items()
                },
                'average_cost_per_maintenance': float(total_cost / len(relevant_records)),
                'completed_maintenance_count': sum(
                    1 for r in relevant_records if r.status == MaintenanceStatus.COMPLETED
                )
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating maintenance costs: {e}")
            return {}
    
    # ==================== 綜合成本計算 ====================
    
    async def calculate_comprehensive_costs(
        self,
        asset_id: str,
        start_time: datetime,
        end_time: datetime,
        price_schedule_id: Optional[str] = None
    ) -> CostCalculationResult:
        """計算綜合成本（電力+維護+環境）"""
        try:
            result = CostCalculationResult(
                asset_id=asset_id,
                calculation_period_start=start_time,
                calculation_period_end=end_time
            )
            
            # 1. 計算電力成本
            electricity_analysis = self.calculate_electricity_cost(
                asset_id, start_time, end_time, price_schedule_id
            )
            
            if electricity_analysis:
                result.total_electricity_cost = Decimal(str(electricity_analysis['total_cost']))
                result.total_energy_consumption_kwh = Decimal(str(electricity_analysis['total_energy_kwh']))
                result.average_power_consumption_watts = electricity_analysis['average_power_w']
                result.peak_demand_kw = Decimal(str(electricity_analysis['peak_demand_kw']))
                
                if result.total_energy_consumption_kwh > 0:
                    result.cost_per_kwh = result.total_electricity_cost / result.total_energy_consumption_kwh
            
            # 2. 計算維護成本
            maintenance_analysis = self.calculate_maintenance_costs(
                asset_id, start_time.date(), end_time.date()
            )
            
            if maintenance_analysis:
                result.total_maintenance_cost = Decimal(str(maintenance_analysis['total_cost']))
                result.maintenance_records_count = maintenance_analysis['maintenance_count']
                
                # 分類維護成本
                for mtype, data in maintenance_analysis['maintenance_types'].items():
                    if mtype == 'preventive':
                        result.preventive_maintenance_cost = Decimal(str(data['total_cost']))
                    elif mtype == 'corrective':
                        result.corrective_maintenance_cost = Decimal(str(data['total_cost']))
            
            # 3. 計算環境成本（散熱、UPS等）
            result.cooling_cost = result.total_electricity_cost * Decimal(str(self.config['cooling_efficiency_ratio']))
            
            # UPS成本（假設UPS效率損失）
            ups_efficiency = Decimal(str(self.config['ups_efficiency']))
            if ups_efficiency < 1:
                ups_loss_ratio = (Decimal('1') - ups_efficiency) / ups_efficiency
                result.ups_cost = result.total_electricity_cost * ups_loss_ratio
            
            # 設施開銷
            result.facility_overhead_cost = (result.total_electricity_cost + result.total_maintenance_cost) * Decimal(str(self.config['facility_overhead_ratio']))
            
            # 4. 計算效率指標
            if result.total_energy_consumption_kwh > 0:
                # PUE計算（包含散熱和UPS損失）
                total_infrastructure_energy = result.total_energy_consumption_kwh + (result.total_energy_consumption_kwh * Decimal(str(self.config['cooling_efficiency_ratio'])))
                result.power_usage_effectiveness = float(total_infrastructure_energy / result.total_energy_consumption_kwh)
                
                # 計算每計算小時成本（假設）
                period_hours = (end_time - start_time).total_seconds() / 3600
                if period_hours > 0:
                    result.cost_per_compute_hour = result.total_cost / Decimal(str(period_hours))
            
            # 5. 計算總計
            result.calculate_totals()
            
            self.logger.info(f"✅ Calculated comprehensive costs for {asset_id}: ${result.total_cost}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating comprehensive costs: {e}")
            # 返回空結果
            return CostCalculationResult(asset_id=asset_id, calculation_period_start=start_time, calculation_period_end=end_time)
    
    # ==================== 優化建議 ====================
    
    def generate_cost_optimization_recommendations(
        self,
        asset_id: str,
        cost_result: CostCalculationResult
    ) -> List[Dict[str, Any]]:
        """生成成本優化建議"""
        recommendations = []
        
        try:
            # 1. 電力成本優化
            if cost_result.total_electricity_cost > 0:
                electricity_ratio = cost_result.total_electricity_cost / cost_result.total_cost
                
                if electricity_ratio > Decimal('0.6'):  # 電力成本占比過高
                    recommendations.append({
                        'type': 'power_optimization',
                        'priority': 'high',
                        'description': f'電力成本占總成本 {electricity_ratio:.1%}，建議優化用電效率',
                        'potential_savings': float(cost_result.total_electricity_cost * Decimal('0.15')),
                        'action_items': [
                            '實施動態電壓調節',
                            '優化工作負載調度避開峰電價',
                            '考慮更節能的硬體',
                            '實施智能電源管理'
                        ]
                    })
                
                # 檢查PUE值
                if cost_result.power_usage_effectiveness and cost_result.power_usage_effectiveness > 1.5:
                    recommendations.append({
                        'type': 'infrastructure_efficiency',
                        'priority': 'medium',
                        'description': f'PUE值偏高 ({cost_result.power_usage_effectiveness:.2f})，建議改善基礎設施效率',
                        'potential_savings': float(cost_result.cooling_cost * Decimal('0.3')),
                        'action_items': [
                            '優化散熱系統配置',
                            '改善空調效率',
                            '考慮液冷散熱',
                            '優化機房氣流設計'
                        ]
                    })
            
            # 2. 維護成本優化
            if cost_result.total_maintenance_cost > 0:
                maintenance_ratio = cost_result.total_maintenance_cost / cost_result.total_cost
                
                if maintenance_ratio > Decimal('0.3'):  # 維護成本占比過高
                    recommendations.append({
                        'type': 'maintenance_optimization',
                        'priority': 'medium',
                        'description': f'維護成本占總成本 {maintenance_ratio:.1%}，建議優化維護策略',
                        'potential_savings': float(cost_result.total_maintenance_cost * Decimal('0.2')),
                        'action_items': [
                            '實施預防性維護計劃',
                            '建立設備健康監控系統',
                            '優化備件庫存管理',
                            '培訓內部維護團隊'
                        ]
                    })
                
                # 檢查修復性維護比例
                if cost_result.corrective_maintenance_cost > cost_result.preventive_maintenance_cost:
                    recommendations.append({
                        'type': 'maintenance_strategy',
                        'priority': 'high',
                        'description': '修復性維護成本高於預防性維護，建議強化預防性維護',
                        'potential_savings': float(cost_result.corrective_maintenance_cost * Decimal('0.4')),
                        'action_items': [
                            '增加預防性維護頻率',
                            '實施預測性維護技術',
                            '建立設備生命週期管理',
                            '優化維護時程安排'
                        ]
                    })
            
            # 3. 能效優化
            if cost_result.average_power_consumption_watts > 0:
                # 假設理論最佳功耗（這裡需要根據實際硬體規格調整）
                theoretical_optimal_power = cost_result.average_power_consumption_watts * 0.7
                potential_power_savings = cost_result.average_power_consumption_watts - theoretical_optimal_power
                
                if potential_power_savings > cost_result.average_power_consumption_watts * 0.2:
                    recommendations.append({
                        'type': 'energy_efficiency',
                        'priority': 'medium',
                        'description': f'設備平均功耗 {cost_result.average_power_consumption_watts:.0f}W，存在節能空間',
                        'potential_savings': float(cost_result.total_electricity_cost * Decimal('0.2')),
                        'action_items': [
                            '啟用節能模式',
                            '優化工作負載分佈',
                            '調整系統性能設定',
                            '考慮硬體升級'
                        ]
                    })
            
            # 4. 成本結構優化
            if len(cost_result.cost_breakdown) > 0:
                # 找出最大成本項目
                max_cost_category = max(cost_result.cost_breakdown.items(), key=lambda x: x[1])
                if max_cost_category[1] > cost_result.total_cost * Decimal('0.5'):
                    recommendations.append({
                        'type': 'cost_structure_optimization',
                        'priority': 'low',
                        'description': f'{max_cost_category[0]}成本占比過高，建議重新評估成本結構',
                        'potential_savings': float(max_cost_category[1] * Decimal('0.1')),
                        'action_items': [
                            f'深入分析{max_cost_category[0]}成本構成',
                            '評估替代方案',
                            '考慮外包或內包策略',
                            '建立成本控制機制'
                        ]
                    })
            
        except Exception as e:
            self.logger.error(f"❌ Error generating optimization recommendations: {e}")
        
        return recommendations
    
    # ==================== 數據管理 ====================
    
    async def _archive_old_power_records(self):
        """歸檔舊的電力記錄"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config['data_retention_days'])
            
            # 找到需要歸檔的記錄
            old_records = [r for r in self.power_consumption_records if r.timestamp < cutoff_date]
            
            if old_records:
                # 保存到文件
                filename = f"{self.data_directory}/power/power_records_{cutoff_date.strftime('%Y%m%d')}.json"
                
                async with aiofiles.open(filename, 'w') as f:
                    records_data = [record.to_dict() for record in old_records]
                    await f.write(json.dumps(records_data, indent=2))
                
                # 從內存中移除
                self.power_consumption_records = [r for r in self.power_consumption_records if r.timestamp >= cutoff_date]
                
                self.logger.info(f"✅ Archived {len(old_records)} old power records")
            
        except Exception as e:
            self.logger.error(f"❌ Error archiving old power records: {e}")
    
    def _validate_price_schedule(self, schedule: ElectricityPriceSchedule) -> bool:
        """驗證電價時程表"""
        try:
            if not schedule.price_id or not schedule.name:
                return False
            
            if schedule.base_price_per_kwh < 0:
                return False
            
            if schedule.price_type == ElectricityPriceType.TIME_OF_USE:
                if not schedule.peak_hours or not schedule.off_peak_hours:
                    return False
                
                if schedule.peak_price_per_kwh <= 0 or schedule.off_peak_price_per_kwh <= 0:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error validating price schedule: {e}")
            return False
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """電力和維護成本追蹤器健康檢查"""
        health_status = {
            'system': 'power_maintenance_tracker',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # 檢查數據統計
            health_status['components']['power_records'] = {
                'total_count': len(self.power_consumption_records),
                'latest_record': max(r.timestamp for r in self.power_consumption_records).isoformat() if self.power_consumption_records else None,
                'assets_monitored': len(set(r.asset_id for r in self.power_consumption_records))
            }
            
            health_status['components']['maintenance_records'] = {
                'total_count': len(self.maintenance_records),
                'scheduled_count': sum(1 for r in self.maintenance_records if r.status == MaintenanceStatus.SCHEDULED),
                'completed_count': sum(1 for r in self.maintenance_records if r.status == MaintenanceStatus.COMPLETED),
                'in_progress_count': sum(1 for r in self.maintenance_records if r.status == MaintenanceStatus.IN_PROGRESS)
            }
            
            health_status['components']['price_schedules'] = {
                'total_count': len(self.price_schedules),
                'schedule_types': list(set(s.price_type.value for s in self.price_schedules.values()))
            }
            
            # 檢查數據目錄
            import os
            health_status['components']['data_directory'] = {
                'exists': os.path.exists(self.data_directory),
                'writable': os.access(self.data_directory, os.W_OK)
            }
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Power maintenance tracker health check failed: {e}")
        
        return health_status


# ==================== 預設配置工廠 ====================

class PowerMaintenanceConfigurationFactory:
    """電力和維護成本配置工廠"""
    
    @staticmethod
    def create_standard_tou_price_schedule(
        price_id: str = "standard_tou",
        peak_price: float = 0.18,
        off_peak_price: float = 0.08,
        demand_charge: float = 15.0
    ) -> ElectricityPriceSchedule:
        """創建標準分時電價時程表"""
        return ElectricityPriceSchedule(
            price_id=price_id,
            name="Standard Time-of-Use Pricing",
            price_type=ElectricityPriceType.TIME_OF_USE,
            peak_hours=[
                (time(9, 0), time(12, 0)),   # 上午峰時
                (time(18, 0), time(22, 0))   # 晚間峰時
            ],
            off_peak_hours=[
                (time(0, 0), time(9, 0)),    # 深夜離峰
                (time(12, 0), time(18, 0)),  # 下午離峰
                (time(22, 0), time(23, 59))  # 夜間離峰
            ],
            peak_price_per_kwh=Decimal(str(peak_price)),
            off_peak_price_per_kwh=Decimal(str(off_peak_price)),
            demand_charge_per_kw=Decimal(str(demand_charge)),
            demand_threshold_kw=Decimal('10'),
            seasonal_multipliers={
                '06': 1.2,  # 夏季加價
                '07': 1.2,
                '08': 1.2,
                '12': 1.1,  # 冬季小幅加價
                '01': 1.1,
                '02': 1.1
            }
        )
    
    @staticmethod
    def create_preventive_maintenance_schedule(
        asset_id: str,
        maintenance_interval_months: int = 6
    ) -> List[Dict[str, Any]]:
        """創建預防性維護計劃"""
        maintenance_items = [
            {
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'description': '清理散熱器和風扇',
                'estimated_labor_hours': 2,
                'estimated_parts_cost': 50,
                'frequency_months': 3
            },
            {
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'description': '更換熱傳導膏',
                'estimated_labor_hours': 4,
                'estimated_parts_cost': 30,
                'frequency_months': 12
            },
            {
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'description': '檢查電源供應器',
                'estimated_labor_hours': 1,
                'estimated_parts_cost': 0,
                'frequency_months': 6
            },
            {
                'maintenance_type': MaintenanceType.PREVENTIVE,
                'description': '軟體更新和驅動程式檢查',
                'estimated_labor_hours': 2,
                'estimated_parts_cost': 0,
                'frequency_months': 3
            }
        ]
        
        schedule = []
        base_date = datetime.now(timezone.utc)
        
        for item in maintenance_items:
            # 為每個維護項目創建未來12個月的排程
            for month_offset in range(0, 12, item['frequency_months']):
                scheduled_date = base_date + timedelta(days=30 * month_offset)
                
                schedule.append({
                    'asset_id': asset_id,
                    'maintenance_type': item['maintenance_type'],
                    'scheduled_date': scheduled_date,
                    'description': item['description'],
                    'estimated_labor_cost': item['estimated_labor_hours'] * 50,  # $50/hour
                    'estimated_parts_cost': item['estimated_parts_cost']
                })
        
        return schedule


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

