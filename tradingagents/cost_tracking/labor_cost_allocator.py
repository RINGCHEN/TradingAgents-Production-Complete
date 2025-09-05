#!/usr/bin/env python3
"""
Labor Cost Allocator - 人力成本分攤機制
GPT-OSS整合任務2.1.2 - 成本追蹤系統實現

企業級人力成本分攤引擎，提供：
- 多維度人力成本分攤算法
- 工時追蹤和項目分配
- 技能和角色成本差異化
- 動態成本分攤和調整
- 績效與成本關聯分析
"""

import uuid
import logging
import asyncio
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union, NamedTuple, Set
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# ==================== 核心枚舉和數據類型 ====================

class EmployeeRole(Enum):
    """員工角色枚舉"""
    AI_ENGINEER = "ai_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    SYSTEM_ADMINISTRATOR = "system_administrator"
    DATA_SCIENTIST = "data_scientist"
    SOFTWARE_DEVELOPER = "software_developer"
    PROJECT_MANAGER = "project_manager"
    TECHNICAL_LEAD = "technical_lead"
    SOLUTION_ARCHITECT = "solution_architect"
    QUALITY_ASSURANCE = "quality_assurance"
    SECURITY_SPECIALIST = "security_specialist"
    INFRASTRUCTURE_ENGINEER = "infrastructure_engineer"
    SUPPORT_ENGINEER = "support_engineer"

class SkillLevel(Enum):
    """技能水準枚舉"""
    JUNIOR = "junior"
    INTERMEDIATE = "intermediate"
    SENIOR = "senior"
    PRINCIPAL = "principal"
    ARCHITECT = "architect"

class ActivityType(Enum):
    """活動類型枚舉"""
    DEVELOPMENT = "development"         # 開發
    MAINTENANCE = "maintenance"         # 維護
    RESEARCH = "research"              # 研究
    TESTING = "testing"                # 測試
    DEPLOYMENT = "deployment"          # 部署
    MONITORING = "monitoring"          # 監控
    DOCUMENTATION = "documentation"    # 文件撰寫
    TRAINING = "training"              # 培訓
    CONSULTATION = "consultation"      # 諮詢
    PROJECT_MANAGEMENT = "project_management"  # 項目管理
    SUPPORT = "support"                # 技術支援
    PLANNING = "planning"              # 規劃

class AllocationMethod(Enum):
    """分攤方法枚舉"""
    TIME_BASED = "time_based"          # 基於工時
    PROJECT_BASED = "project_based"    # 基於項目
    VALUE_BASED = "value_based"        # 基於價值貢獻
    SKILL_WEIGHTED = "skill_weighted"  # 基於技能權重
    OUTCOME_BASED = "outcome_based"    # 基於成果
    HYBRID = "hybrid"                  # 混合方法

@dataclass
class Employee:
    """員工信息"""
    employee_id: str
    name: str
    role: EmployeeRole
    skill_level: SkillLevel
    
    # 成本信息
    base_salary_annual: Decimal
    benefits_annual: Decimal = Decimal('0')
    bonus_annual: Decimal = Decimal('0')
    overhead_multiplier: float = 1.5  # 間接成本倍數
    
    # 工作信息
    standard_hours_per_week: int = 40
    billable_hours_percentage: float = 0.75  # 可計費時間比例
    
    # 技能和認證
    skills: Set[str] = field(default_factory=set)
    certifications: List[str] = field(default_factory=list)
    
    # 績效和產出
    productivity_factor: float = 1.0  # 生產力因子
    quality_rating: float = 1.0  # 質量評級
    
    # 時間和可用性
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    is_active: bool = True
    
    # 地理位置（影響成本）
    location: Optional[str] = None
    cost_center_id: Optional[uuid.UUID] = None
    
    @property
    def total_annual_cost(self) -> Decimal:
        """總年度成本"""
        direct_cost = self.base_salary_annual + self.benefits_annual + self.bonus_annual
        return direct_cost * Decimal(str(self.overhead_multiplier))
    
    @property
    def hourly_rate(self) -> Decimal:
        """小時費率"""
        annual_hours = Decimal(str(self.standard_hours_per_week * 52))
        return self.total_annual_cost / annual_hours
    
    @property
    def billable_hourly_rate(self) -> Decimal:
        """可計費小時費率"""
        return self.hourly_rate / Decimal(str(self.billable_hours_percentage))

@dataclass
class WorkActivity:
    """工作活動記錄"""
    activity_id: str
    employee_id: str
    activity_type: ActivityType
    
    # 時間信息
    start_time: datetime
    end_time: datetime
    duration_hours: float
    
    # 項目和任務
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    cost_center_id: Optional[uuid.UUID] = None
    
    # 描述和標籤
    description: str = ""
    tags: Set[str] = field(default_factory=set)
    
    # 成果和影響
    deliverables: List[str] = field(default_factory=list)
    impact_metrics: Dict[str, float] = field(default_factory=dict)
    quality_score: Optional[float] = None
    
    # 分配權重
    allocation_weights: Dict[str, float] = field(default_factory=dict)
    
    # 審批狀態
    is_approved: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'activity_id': self.activity_id,
            'employee_id': self.employee_id,
            'activity_type': self.activity_type.value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_hours': self.duration_hours,
            'project_id': self.project_id,
            'task_id': self.task_id,
            'cost_center_id': str(self.cost_center_id) if self.cost_center_id else None,
            'description': self.description,
            'tags': list(self.tags),
            'deliverables': self.deliverables,
            'impact_metrics': self.impact_metrics,
            'quality_score': self.quality_score,
            'allocation_weights': self.allocation_weights,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }

@dataclass
class AllocationRule:
    """分攤規則"""
    rule_id: str
    name: str
    method: AllocationMethod
    
    # 目標和範圍
    target_cost_centers: List[uuid.UUID] = field(default_factory=list)
    target_projects: List[str] = field(default_factory=list)
    applicable_roles: List[EmployeeRole] = field(default_factory=list)
    applicable_activities: List[ActivityType] = field(default_factory=list)
    
    # 分攤參數
    allocation_factors: Dict[str, float] = field(default_factory=dict)
    skill_multipliers: Dict[SkillLevel, float] = field(default_factory=dict)
    activity_weights: Dict[ActivityType, float] = field(default_factory=dict)
    
    # 約束條件
    minimum_allocation_percentage: float = 0.0
    maximum_allocation_percentage: float = 1.0
    exclude_overhead: bool = False
    
    # 有效期間
    effective_start_date: date = field(default_factory=date.today)
    effective_end_date: Optional[date] = None
    is_active: bool = True

@dataclass
class CostAllocationResult:
    """成本分攤結果"""
    allocation_id: str
    employee_id: str
    calculation_period_start: date
    calculation_period_end: date
    
    # 基礎成本信息
    base_hourly_rate: Decimal = Decimal('0')
    total_hours_worked: float = 0.0
    billable_hours: float = 0.0
    
    # 成本分解
    direct_labor_cost: Decimal = Decimal('0')
    benefits_cost: Decimal = Decimal('0')
    overhead_cost: Decimal = Decimal('0')
    total_cost: Decimal = Decimal('0')
    
    # 分攤結果
    allocated_costs: Dict[str, Decimal] = field(default_factory=dict)  # cost_center_id -> amount
    project_allocations: Dict[str, Decimal] = field(default_factory=dict)  # project_id -> amount
    activity_breakdown: Dict[ActivityType, Decimal] = field(default_factory=dict)
    
    # 效率指標
    productivity_score: float = 1.0
    utilization_rate: float = 0.0
    cost_per_deliverable: Optional[Decimal] = None
    
    # 質量指標
    average_quality_score: Optional[float] = None
    deliverables_count: int = 0
    
    # 計算元數據
    allocation_method: str = ""
    calculation_confidence: float = 1.0
    assumptions: Dict[str, Any] = field(default_factory=dict)

# ==================== 核心分攤引擎 ====================

class LaborCostAllocator:
    """
    人力成本分攤器
    
    功能：
    1. 多維度人力成本分攤算法
    2. 工時追蹤和項目分配
    3. 技能和角色成本差異化
    4. 動態成本分攤和調整
    5. 績效與成本關聯分析
    6. 成本優化建議和分析
    """
    
    def __init__(self):
        """初始化人力成本分攤器"""
        self.logger = logger
        
        # 數據存儲
        self.employees: Dict[str, Employee] = {}
        self.work_activities: List[WorkActivity] = []
        self.allocation_rules: Dict[str, AllocationRule] = {}
        self.allocation_results: List[CostAllocationResult] = []
        
        # 預設配置
        self.config = {
            'standard_working_days_per_month': 22,
            'standard_hours_per_day': 8,
            'overtime_multiplier': 1.5,
            'holiday_multiplier': 2.0,
            'default_overhead_rate': 1.5,
            'productivity_weight': 0.3,
            'quality_weight': 0.2,
            'delivery_weight': 0.5
        }
        
        self.logger.info("✅ Labor Cost Allocator initialized")
    
    # ==================== 員工管理 ====================
    
    def register_employee(self, employee: Employee) -> bool:
        """註冊員工"""
        try:
            # 驗證員工信息
            if not self._validate_employee(employee):
                raise ValueError(f"Invalid employee data: {employee.employee_id}")
            
            self.employees[employee.employee_id] = employee
            
            self.logger.info(f"✅ Registered employee: {employee.name} ({employee.employee_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error registering employee: {e}")
            return False
    
    def update_employee(self, employee_id: str, updates: Dict[str, Any]) -> bool:
        """更新員工信息"""
        try:
            if employee_id not in self.employees:
                raise ValueError(f"Employee not found: {employee_id}")
            
            employee = self.employees[employee_id]
            
            # 更新允許的欄位
            updatable_fields = [
                'base_salary_annual', 'benefits_annual', 'bonus_annual',
                'overhead_multiplier', 'productivity_factor', 'quality_rating',
                'billable_hours_percentage', 'is_active', 'location',
                'cost_center_id'
            ]
            
            for field, value in updates.items():
                if field in updatable_fields:
                    if hasattr(employee, field):
                        setattr(employee, field, value)
                    
                elif field == 'skills':
                    employee.skills = set(value) if isinstance(value, list) else value
                elif field == 'certifications':
                    employee.certifications = value
            
            self.logger.info(f"✅ Updated employee: {employee_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error updating employee: {e}")
            return False
    
    # ==================== 工作活動追蹤 ====================
    
    async def record_work_activity(
        self,
        employee_id: str,
        activity_type: ActivityType,
        start_time: datetime,
        end_time: datetime,
        description: str = "",
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        cost_center_id: Optional[uuid.UUID] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """記錄工作活動"""
        try:
            if employee_id not in self.employees:
                raise ValueError(f"Employee not found: {employee_id}")
            
            duration = (end_time - start_time).total_seconds() / 3600  # 小時
            
            activity = WorkActivity(
                activity_id=str(uuid.uuid4()),
                employee_id=employee_id,
                activity_type=activity_type,
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration,
                description=description,
                project_id=project_id,
                task_id=task_id,
                cost_center_id=cost_center_id
            )
            
            # 添加額外數據
            if additional_data:
                if 'tags' in additional_data:
                    activity.tags = set(additional_data['tags'])
                if 'deliverables' in additional_data:
                    activity.deliverables = additional_data['deliverables']
                if 'impact_metrics' in additional_data:
                    activity.impact_metrics = additional_data['impact_metrics']
                if 'quality_score' in additional_data:
                    activity.quality_score = additional_data['quality_score']
                if 'allocation_weights' in additional_data:
                    activity.allocation_weights = additional_data['allocation_weights']
            
            self.work_activities.append(activity)
            
            self.logger.info(f"✅ Recorded work activity for {employee_id}: {activity_type.value} ({duration:.1f}h)")
            return activity.activity_id
            
        except Exception as e:
            self.logger.error(f"❌ Error recording work activity: {e}")
            return ""
    
    async def approve_work_activity(
        self,
        activity_id: str,
        approved_by: str,
        quality_adjustments: Optional[Dict[str, Any]] = None
    ) -> bool:
        """審批工作活動"""
        try:
            # 找到活動
            activity = None
            for act in self.work_activities:
                if act.activity_id == activity_id:
                    activity = act
                    break
            
            if not activity:
                raise ValueError(f"Activity not found: {activity_id}")
            
            # 審批活動
            activity.is_approved = True
            activity.approved_by = approved_by
            activity.approved_at = datetime.now(timezone.utc)
            
            # 應用質量調整
            if quality_adjustments:
                if 'quality_score' in quality_adjustments:
                    activity.quality_score = quality_adjustments['quality_score']
                if 'impact_metrics' in quality_adjustments:
                    activity.impact_metrics.update(quality_adjustments['impact_metrics'])
            
            self.logger.info(f"✅ Approved work activity: {activity_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error approving work activity: {e}")
            return False
    
    # ==================== 分攤規則管理 ====================
    
    def create_allocation_rule(self, rule: AllocationRule) -> bool:
        """創建分攤規則"""
        try:
            # 驗證規則
            if not self._validate_allocation_rule(rule):
                raise ValueError(f"Invalid allocation rule: {rule.rule_id}")
            
            self.allocation_rules[rule.rule_id] = rule
            
            self.logger.info(f"✅ Created allocation rule: {rule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error creating allocation rule: {e}")
            return False
    
    # ==================== 成本分攤計算 ====================
    
    async def calculate_labor_cost_allocation(
        self,
        employee_id: str,
        calculation_start_date: date,
        calculation_end_date: date,
        allocation_rule_id: Optional[str] = None
    ) -> CostAllocationResult:
        """計算人力成本分攤"""
        try:
            if employee_id not in self.employees:
                raise ValueError(f"Employee not found: {employee_id}")
            
            employee = self.employees[employee_id]
            
            # 創建結果對象
            result = CostAllocationResult(
                allocation_id=str(uuid.uuid4()),
                employee_id=employee_id,
                calculation_period_start=calculation_start_date,
                calculation_period_end=calculation_end_date
            )
            
            # 獲取計算期間的工作活動
            period_activities = [
                activity for activity in self.work_activities
                if (activity.employee_id == employee_id and
                    activity.is_approved and
                    calculation_start_date <= activity.start_time.date() <= calculation_end_date)
            ]
            
            if not period_activities:
                self.logger.warning(f"No approved activities found for {employee_id} in period")
                return result
            
            # 計算基礎指標
            result.base_hourly_rate = employee.billable_hourly_rate
            result.total_hours_worked = sum(act.duration_hours for act in period_activities)
            result.billable_hours = result.total_hours_worked * employee.billable_hours_percentage
            
            # 計算成本組成
            period_days = (calculation_end_date - calculation_start_date).days + 1
            daily_cost = employee.total_annual_cost / Decimal('365')
            result.total_cost = daily_cost * Decimal(str(period_days))
            
            # 分解成本
            result.direct_labor_cost = result.total_cost / Decimal(str(employee.overhead_multiplier))
            result.benefits_cost = (employee.benefits_annual / Decimal('365')) * Decimal(str(period_days))
            result.overhead_cost = result.total_cost - result.direct_labor_cost - result.benefits_cost
            
            # 選擇分攤規則
            allocation_rule = None
            if allocation_rule_id and allocation_rule_id in self.allocation_rules:
                allocation_rule = self.allocation_rules[allocation_rule_id]
                result.allocation_method = allocation_rule.name
            
            # 執行分攤計算
            if allocation_rule:
                result = await self._apply_allocation_rule(result, employee, period_activities, allocation_rule)
            else:
                # 預設按時間分攤
                result = await self._apply_time_based_allocation(result, employee, period_activities)
            
            # 計算績效指標
            result.productivity_score = employee.productivity_factor
            standard_hours = period_days * self.config['standard_hours_per_day']
            result.utilization_rate = result.total_hours_worked / standard_hours if standard_hours > 0 else 0
            
            # 計算質量指標
            quality_scores = [act.quality_score for act in period_activities if act.quality_score is not None]
            if quality_scores:
                result.average_quality_score = sum(quality_scores) / len(quality_scores)
            
            result.deliverables_count = sum(len(act.deliverables) for act in period_activities)
            if result.deliverables_count > 0:
                result.cost_per_deliverable = result.total_cost / Decimal(str(result.deliverables_count))
            
            # 設置計算信心度
            result.calculation_confidence = self._calculate_confidence_score(period_activities, employee)
            
            self.allocation_results.append(result)
            
            self.logger.info(f"✅ Calculated labor cost allocation for {employee_id}: ${result.total_cost}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating labor cost allocation: {e}")
            # 返回空結果
            return CostAllocationResult(
                allocation_id=str(uuid.uuid4()),
                employee_id=employee_id,
                calculation_period_start=calculation_start_date,
                calculation_period_end=calculation_end_date
            )
    
    async def _apply_allocation_rule(
        self,
        result: CostAllocationResult,
        employee: Employee,
        activities: List[WorkActivity],
        rule: AllocationRule
    ) -> CostAllocationResult:
        """應用分攤規則"""
        if rule.method == AllocationMethod.TIME_BASED:
            return await self._apply_time_based_allocation(result, employee, activities)
        elif rule.method == AllocationMethod.PROJECT_BASED:
            return await self._apply_project_based_allocation(result, employee, activities, rule)
        elif rule.method == AllocationMethod.VALUE_BASED:
            return await self._apply_value_based_allocation(result, employee, activities, rule)
        elif rule.method == AllocationMethod.SKILL_WEIGHTED:
            return await self._apply_skill_weighted_allocation(result, employee, activities, rule)
        elif rule.method == AllocationMethod.OUTCOME_BASED:
            return await self._apply_outcome_based_allocation(result, employee, activities, rule)
        else:
            # 預設時間分攤
            return await self._apply_time_based_allocation(result, employee, activities)
    
    async def _apply_time_based_allocation(
        self,
        result: CostAllocationResult,
        employee: Employee,
        activities: List[WorkActivity]
    ) -> CostAllocationResult:
        """應用基於時間的分攤"""
        # 按成本中心分攤
        cost_center_hours = {}
        project_hours = {}
        activity_hours = {}
        
        for activity in activities:
            # 成本中心分攤
            if activity.cost_center_id:
                cc_id = str(activity.cost_center_id)
                cost_center_hours[cc_id] = cost_center_hours.get(cc_id, 0) + activity.duration_hours
            
            # 項目分攤
            if activity.project_id:
                project_hours[activity.project_id] = project_hours.get(activity.project_id, 0) + activity.duration_hours
            
            # 活動類型分攤
            activity_type = activity.activity_type
            activity_hours[activity_type] = activity_hours.get(activity_type, 0) + activity.duration_hours
        
        total_hours = sum(cost_center_hours.values()) if cost_center_hours else result.total_hours_worked
        
        # 分攤成本到成本中心
        if cost_center_hours and total_hours > 0:
            for cc_id, hours in cost_center_hours.items():
                ratio = Decimal(str(hours)) / Decimal(str(total_hours))
                allocated_cost = (result.total_cost * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                result.allocated_costs[cc_id] = allocated_cost
        
        # 分攤成本到項目
        if project_hours and total_hours > 0:
            for project_id, hours in project_hours.items():
                ratio = Decimal(str(hours)) / Decimal(str(total_hours))
                allocated_cost = (result.total_cost * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                result.project_allocations[project_id] = allocated_cost
        
        # 活動類型成本分解
        if activity_hours and total_hours > 0:
            for activity_type, hours in activity_hours.items():
                ratio = Decimal(str(hours)) / Decimal(str(total_hours))
                allocated_cost = (result.total_cost * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                result.activity_breakdown[activity_type] = allocated_cost
        
        return result
    
    async def _apply_project_based_allocation(
        self,
        result: CostAllocationResult,
        employee: Employee,
        activities: List[WorkActivity],
        rule: AllocationRule
    ) -> CostAllocationResult:
        """應用基於項目的分攤"""
        project_weights = {}
        total_weight = 0.0
        
        # 計算項目權重
        for activity in activities:
            if activity.project_id and activity.project_id in rule.target_projects:
                weight = rule.allocation_factors.get(activity.project_id, activity.duration_hours)
                project_weights[activity.project_id] = project_weights.get(activity.project_id, 0) + weight
                total_weight += weight
        
        # 分攤成本
        if project_weights and total_weight > 0:
            for project_id, weight in project_weights.items():
                ratio = Decimal(str(weight)) / Decimal(str(total_weight))
                allocated_cost = (result.total_cost * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                result.project_allocations[project_id] = allocated_cost
        
        return result
    
    async def _apply_value_based_allocation(
        self,
        result: CostAllocationResult,
        employee: Employee,
        activities: List[WorkActivity],
        rule: AllocationRule
    ) -> CostAllocationResult:
        """應用基於價值的分攤"""
        value_weights = {}
        total_value = 0.0
        
        # 計算價值權重
        for activity in activities:
            # 基於影響指標計算價值
            value = 1.0  # 基礎價值
            
            if activity.impact_metrics:
                # 使用影響指標調整價值
                for metric, metric_value in activity.impact_metrics.items():
                    metric_weight = rule.allocation_factors.get(metric, 1.0)
                    value *= (1 + metric_value * metric_weight)
            
            # 質量調整
            if activity.quality_score:
                value *= activity.quality_score
            
            # 可交付成果調整
            if activity.deliverables:
                value *= (1 + len(activity.deliverables) * 0.1)
            
            value_key = activity.cost_center_id or activity.project_id or 'default'
            value_weights[str(value_key)] = value_weights.get(str(value_key), 0) + value
            total_value += value
        
        # 分攤成本
        if value_weights and total_value > 0:
            for key, value in value_weights.items():
                ratio = Decimal(str(value)) / Decimal(str(total_value))
                allocated_cost = (result.total_cost * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                result.allocated_costs[key] = allocated_cost
        
        return result
    
    async def _apply_skill_weighted_allocation(
        self,
        result: CostAllocationResult,
        employee: Employee,
        activities: List[WorkActivity],
        rule: AllocationRule
    ) -> CostAllocationResult:
        """應用基於技能權重的分攤"""
        # 獲取技能倍數
        skill_multiplier = rule.skill_multipliers.get(employee.skill_level, 1.0)
        
        # 調整基礎費率
        adjusted_hourly_rate = result.base_hourly_rate * Decimal(str(skill_multiplier))
        adjusted_total_cost = adjusted_hourly_rate * Decimal(str(result.total_hours_worked))
        
        # 更新結果
        result.base_hourly_rate = adjusted_hourly_rate
        result.total_cost = adjusted_total_cost
        result.direct_labor_cost = adjusted_total_cost / Decimal(str(employee.overhead_multiplier))
        result.overhead_cost = adjusted_total_cost - result.direct_labor_cost - result.benefits_cost
        
        # 然後應用時間分攤
        return await self._apply_time_based_allocation(result, employee, activities)
    
    async def _apply_outcome_based_allocation(
        self,
        result: CostAllocationResult,
        employee: Employee,
        activities: List[WorkActivity],
        rule: AllocationRule
    ) -> CostAllocationResult:
        """應用基於成果的分攤"""
        outcome_weights = {}
        total_weight = 0.0
        
        # 計算成果權重
        for activity in activities:
            weight = 0.0
            
            # 基於可交付成果
            weight += len(activity.deliverables) * rule.allocation_factors.get('deliverables', 1.0)
            
            # 基於質量分數
            if activity.quality_score:
                weight += activity.quality_score * rule.allocation_factors.get('quality', 1.0)
            
            # 基於影響指標
            if activity.impact_metrics:
                for metric, value in activity.impact_metrics.items():
                    metric_weight = rule.allocation_factors.get(f"impact_{metric}", 0.5)
                    weight += value * metric_weight
            
            allocation_key = activity.cost_center_id or activity.project_id or 'default'
            outcome_weights[str(allocation_key)] = outcome_weights.get(str(allocation_key), 0) + weight
            total_weight += weight
        
        # 分攤成本
        if outcome_weights and total_weight > 0:
            for key, weight in outcome_weights.items():
                ratio = Decimal(str(weight)) / Decimal(str(total_weight))
                allocated_cost = (result.total_cost * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                result.allocated_costs[key] = allocated_cost
        
        return result
    
    # ==================== 分析和報告 ====================
    
    def generate_labor_cost_analysis(
        self,
        start_date: date,
        end_date: date,
        employee_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """生成人力成本分析報告"""
        try:
            # 過濾分攤結果
            relevant_results = [
                result for result in self.allocation_results
                if (start_date <= result.calculation_period_start <= end_date and
                    (not employee_ids or result.employee_id in employee_ids))
            ]
            
            if not relevant_results:
                return {
                    'period': f"{start_date} to {end_date}",
                    'employee_count': 0,
                    'total_cost': 0.0,
                    'analysis': {}
                }
            
            # 計算匯總指標
            total_cost = sum(result.total_cost for result in relevant_results)
            total_hours = sum(result.total_hours_worked for result in relevant_results)
            
            # 按員工分組
            employee_analysis = {}
            for result in relevant_results:
                emp_id = result.employee_id
                if emp_id not in employee_analysis:
                    employee = self.employees.get(emp_id)
                    employee_analysis[emp_id] = {
                        'employee_name': employee.name if employee else emp_id,
                        'role': employee.role.value if employee else 'unknown',
                        'skill_level': employee.skill_level.value if employee else 'unknown',
                        'total_cost': 0.0,
                        'total_hours': 0.0,
                        'utilization_rate': 0.0,
                        'productivity_score': 0.0,
                        'projects': set(),
                        'cost_centers': set()
                    }
                
                employee_analysis[emp_id]['total_cost'] += float(result.total_cost)
                employee_analysis[emp_id]['total_hours'] += result.total_hours_worked
                employee_analysis[emp_id]['utilization_rate'] += result.utilization_rate
                employee_analysis[emp_id]['productivity_score'] += result.productivity_score
                employee_analysis[emp_id]['projects'].update(result.project_allocations.keys())
                employee_analysis[emp_id]['cost_centers'].update(result.allocated_costs.keys())
            
            # 平均化指標
            for emp_data in employee_analysis.values():
                emp_data['utilization_rate'] /= len(relevant_results)
                emp_data['productivity_score'] /= len(relevant_results)
                emp_data['projects'] = list(emp_data['projects'])
                emp_data['cost_centers'] = list(emp_data['cost_centers'])
                emp_data['hourly_rate'] = emp_data['total_cost'] / emp_data['total_hours'] if emp_data['total_hours'] > 0 else 0
            
            # 按角色分析
            role_analysis = {}
            for result in relevant_results:
                employee = self.employees.get(result.employee_id)
                if employee:
                    role = employee.role.value
                    if role not in role_analysis:
                        role_analysis[role] = {
                            'employee_count': 0,
                            'total_cost': 0.0,
                            'total_hours': 0.0,
                            'average_hourly_rate': 0.0
                        }
                    
                    role_analysis[role]['employee_count'] += 1
                    role_analysis[role]['total_cost'] += float(result.total_cost)
                    role_analysis[role]['total_hours'] += result.total_hours_worked
            
            # 計算角色平均費率
            for role_data in role_analysis.values():
                if role_data['total_hours'] > 0:
                    role_data['average_hourly_rate'] = role_data['total_cost'] / role_data['total_hours']
            
            # 按項目分析
            project_analysis = {}
            for result in relevant_results:
                for project_id, cost in result.project_allocations.items():
                    if project_id not in project_analysis:
                        project_analysis[project_id] = {
                            'total_cost': 0.0,
                            'employee_count': 0,
                            'employees': set()
                        }
                    
                    project_analysis[project_id]['total_cost'] += float(cost)
                    project_analysis[project_id]['employees'].add(result.employee_id)
            
            # 轉換員工集合為數量
            for project_data in project_analysis.values():
                project_data['employee_count'] = len(project_data['employees'])
                project_data['employees'] = list(project_data['employees'])
            
            return {
                'period': f"{start_date} to {end_date}",
                'summary': {
                    'employee_count': len(set(r.employee_id for r in relevant_results)),
                    'total_cost': float(total_cost),
                    'total_hours': total_hours,
                    'average_hourly_rate': float(total_cost / Decimal(str(total_hours))) if total_hours > 0 else 0,
                    'average_utilization_rate': sum(r.utilization_rate for r in relevant_results) / len(relevant_results),
                    'average_productivity_score': sum(r.productivity_score for r in relevant_results) / len(relevant_results)
                },
                'employee_analysis': employee_analysis,
                'role_analysis': role_analysis,
                'project_analysis': project_analysis,
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error generating labor cost analysis: {e}")
            return {}
    
    def generate_optimization_recommendations(
        self,
        analysis_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成優化建議"""
        recommendations = []
        
        try:
            if 'summary' not in analysis_result:
                return recommendations
            
            summary = analysis_result['summary']
            
            # 利用率優化
            avg_utilization = summary.get('average_utilization_rate', 0)
            if avg_utilization < 0.7:
                recommendations.append({
                    'type': 'utilization_optimization',
                    'priority': 'high',
                    'description': f'團隊平均利用率 {avg_utilization:.1%}，建議優化工作分配和時間管理',
                    'potential_savings': summary['total_cost'] * 0.15,
                    'action_items': [
                        '分析低利用率員工的工作安排',
                        '優化項目調度和資源分配',
                        '提供時間管理培訓',
                        '考慮工作負載重新分配'
                    ]
                })
            
            # 生產力優化
            avg_productivity = summary.get('average_productivity_score', 1.0)
            if avg_productivity < 0.9:
                recommendations.append({
                    'type': 'productivity_optimization',
                    'priority': 'medium',
                    'description': f'團隊平均生產力分數 {avg_productivity:.2f}，建議提升工作效率',
                    'potential_savings': summary['total_cost'] * 0.1,
                    'action_items': [
                        '提供技能提升培訓',
                        '改善工作環境和工具',
                        '實施敏捷工作方法',
                        '建立績效激勵機制'
                    ]
                })
            
            # 角色成本分析
            if 'role_analysis' in analysis_result:
                role_costs = [(role, data['average_hourly_rate']) 
                             for role, data in analysis_result['role_analysis'].items()]
                role_costs.sort(key=lambda x: x[1], reverse=True)
                
                if len(role_costs) > 1:
                    highest_cost_role = role_costs[0]
                    if highest_cost_role[1] > summary['average_hourly_rate'] * 1.5:
                        recommendations.append({
                            'type': 'role_cost_optimization',
                            'priority': 'low',
                            'description': f'{highest_cost_role[0]}角色成本偏高 (${highest_cost_role[1]:.2f}/小時)，建議評估性價比',
                            'potential_savings': summary['total_cost'] * 0.05,
                            'action_items': [
                                '評估高成本角色的工作內容',
                                '考慮任務委派給較低成本角色',
                                '提供交叉培訓機會',
                                '優化團隊技能結構'
                            ]
                        })
            
            # 項目成本分析
            if 'project_analysis' in analysis_result:
                project_costs = [(proj, data['total_cost']) 
                               for proj, data in analysis_result['project_analysis'].items()]
                project_costs.sort(key=lambda x: x[1], reverse=True)
                
                if project_costs:
                    highest_cost_project = project_costs[0]
                    if highest_cost_project[1] > summary['total_cost'] * 0.4:
                        recommendations.append({
                            'type': 'project_cost_optimization',
                            'priority': 'medium',
                            'description': f'項目 {highest_cost_project[0]} 人力成本占比過高，建議優化資源配置',
                            'potential_savings': highest_cost_project[1] * 0.1,
                            'action_items': [
                                '重新評估項目範圍和需求',
                                '優化項目團隊配置',
                                '考慮外包部分工作',
                                '實施更嚴格的項目管理'
                            ]
                        })
            
        except Exception as e:
            self.logger.error(f"❌ Error generating optimization recommendations: {e}")
        
        return recommendations
    
    # ==================== 輔助方法 ====================
    
    def _validate_employee(self, employee: Employee) -> bool:
        """驗證員工信息"""
        if not employee.employee_id or not employee.name:
            return False
        
        if employee.base_salary_annual <= 0:
            return False
        
        if employee.overhead_multiplier <= 0:
            return False
        
        if not (0 < employee.billable_hours_percentage <= 1):
            return False
        
        return True
    
    def _validate_allocation_rule(self, rule: AllocationRule) -> bool:
        """驗證分攤規則"""
        if not rule.rule_id or not rule.name:
            return False
        
        if not (0 <= rule.minimum_allocation_percentage <= 1):
            return False
        
        if not (0 <= rule.maximum_allocation_percentage <= 1):
            return False
        
        if rule.minimum_allocation_percentage > rule.maximum_allocation_percentage:
            return False
        
        return True
    
    def _calculate_confidence_score(
        self,
        activities: List[WorkActivity],
        employee: Employee
    ) -> float:
        """計算計算信心度"""
        score = 1.0
        
        # 基於活動數量
        if len(activities) < 5:
            score *= 0.8
        elif len(activities) > 20:
            score *= 0.95
        
        # 基於審批狀態
        approved_count = sum(1 for act in activities if act.is_approved)
        approval_rate = approved_count / len(activities) if activities else 0
        score *= (0.5 + 0.5 * approval_rate)
        
        # 基於質量評分完整性
        quality_completeness = sum(1 for act in activities if act.quality_score is not None) / len(activities)
        score *= (0.7 + 0.3 * quality_completeness)
        
        # 基於員工數據完整性
        if employee.productivity_factor != 1.0 or employee.quality_rating != 1.0:
            score *= 1.1  # 有自定義績效數據
        
        return min(score, 1.0)
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """人力成本分攤器健康檢查"""
        health_status = {
            'system': 'labor_cost_allocator',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            # 檢查員工數據
            health_status['components']['employees'] = {
                'total_count': len(self.employees),
                'active_count': sum(1 for emp in self.employees.values() if emp.is_active),
                'roles': list(set(emp.role.value for emp in self.employees.values())),
                'skill_levels': list(set(emp.skill_level.value for emp in self.employees.values()))
            }
            
            # 檢查工作活動
            health_status['components']['work_activities'] = {
                'total_count': len(self.work_activities),
                'approved_count': sum(1 for act in self.work_activities if act.is_approved),
                'activity_types': list(set(act.activity_type.value for act in self.work_activities)),
                'latest_activity': max(act.end_time for act in self.work_activities).isoformat() if self.work_activities else None
            }
            
            # 檢查分攤規則
            health_status['components']['allocation_rules'] = {
                'total_count': len(self.allocation_rules),
                'active_count': sum(1 for rule in self.allocation_rules.values() if rule.is_active),
                'methods': list(set(rule.method.value for rule in self.allocation_rules.values()))
            }
            
            # 檢查分攤結果
            health_status['components']['allocation_results'] = {
                'total_count': len(self.allocation_results),
                'latest_calculation': max(res.calculation_period_end for res in self.allocation_results).isoformat() if self.allocation_results else None
            }
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Labor cost allocator health check failed: {e}")
        
        return health_status


# ==================== 預設配置工廠 ====================

class LaborCostConfigurationFactory:
    """人力成本配置工廠"""
    
    @staticmethod
    def create_standard_employee(
        employee_id: str,
        name: str,
        role: EmployeeRole,
        skill_level: SkillLevel,
        base_salary: float
    ) -> Employee:
        """創建標準員工配置"""
        # 基於角色和技能等級設定標準福利
        benefits_rate = {
            SkillLevel.JUNIOR: 0.25,
            SkillLevel.INTERMEDIATE: 0.30,
            SkillLevel.SENIOR: 0.35,
            SkillLevel.PRINCIPAL: 0.40,
            SkillLevel.ARCHITECT: 0.45
        }
        
        # 基於角色設定標準技能
        role_skills = {
            EmployeeRole.AI_ENGINEER: {'python', 'tensorflow', 'pytorch', 'machine_learning', 'deep_learning'},
            EmployeeRole.DEVOPS_ENGINEER: {'kubernetes', 'docker', 'terraform', 'aws', 'ci_cd'},
            EmployeeRole.SYSTEM_ADMINISTRATOR: {'linux', 'networking', 'security', 'monitoring', 'automation'},
            EmployeeRole.DATA_SCIENTIST: {'python', 'r', 'statistics', 'data_analysis', 'visualization'},
            EmployeeRole.SOFTWARE_DEVELOPER: {'programming', 'software_design', 'testing', 'debugging', 'api_development'}
        }
        
        return Employee(
            employee_id=employee_id,
            name=name,
            role=role,
            skill_level=skill_level,
            base_salary_annual=Decimal(str(base_salary)),
            benefits_annual=Decimal(str(base_salary)) * Decimal(str(benefits_rate.get(skill_level, 0.30))),
            bonus_annual=Decimal(str(base_salary)) * Decimal('0.1'),  # 10% 標準獎金
            skills=role_skills.get(role, set()),
            overhead_multiplier=1.5,
            billable_hours_percentage=0.75
        )
    
    @staticmethod
    def create_time_based_allocation_rule(
        rule_id: str,
        target_cost_centers: List[uuid.UUID]
    ) -> AllocationRule:
        """創建基於時間的分攤規則"""
        return AllocationRule(
            rule_id=rule_id,
            name="Time-Based Cost Allocation",
            method=AllocationMethod.TIME_BASED,
            target_cost_centers=target_cost_centers,
            allocation_factors={},
            skill_multipliers={
                SkillLevel.JUNIOR: 1.0,
                SkillLevel.INTERMEDIATE: 1.2,
                SkillLevel.SENIOR: 1.5,
                SkillLevel.PRINCIPAL: 1.8,
                SkillLevel.ARCHITECT: 2.0
            },
            activity_weights={
                ActivityType.DEVELOPMENT: 1.0,
                ActivityType.RESEARCH: 1.2,
                ActivityType.TESTING: 0.8,
                ActivityType.DOCUMENTATION: 0.6,
                ActivityType.MAINTENANCE: 0.7
            }
        )
    
    @staticmethod
    def create_value_based_allocation_rule(
        rule_id: str,
        target_cost_centers: List[uuid.UUID]
    ) -> AllocationRule:
        """創建基於價值的分攤規則"""
        return AllocationRule(
            rule_id=rule_id,
            name="Value-Based Cost Allocation",
            method=AllocationMethod.VALUE_BASED,
            target_cost_centers=target_cost_centers,
            allocation_factors={
                'deliverables': 2.0,
                'quality': 1.5,
                'impact_performance': 2.0,
                'impact_reliability': 1.8,
                'impact_security': 1.6,
                'impact_scalability': 1.4
            },
            skill_multipliers={
                SkillLevel.JUNIOR: 0.8,
                SkillLevel.INTERMEDIATE: 1.0,
                SkillLevel.SENIOR: 1.3,
                SkillLevel.PRINCIPAL: 1.6,
                SkillLevel.ARCHITECT: 2.0
            }
        )