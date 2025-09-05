#!/usr/bin/env python3
"""
Budget and ROI Exemption Manager
預算分配和ROI豁免管理器

專門管理創新特區的預算分配和ROI豁免機制：
- 創新特區預算分配（5-10% 研發預算）
- ROI豁免權規則（前四季度免考核）
- 預算使用監控和預警
- ROI豁免期管理和評估
- 預算效率分析和優化建議
- 與虛擬損益表系統整合
"""

import asyncio
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import uuid
import statistics
from dataclasses import dataclass, field
from enum import Enum

from .models import ROIExemptionStatus
from .innovation_zone_db import InnovationZoneDB

logger = logging.getLogger(__name__)

class BudgetCategory(str, Enum):
    """預算類別枚舉"""
    RESEARCH = "research"
    DEVELOPMENT = "development"
    PROTOTYPING = "prototyping"
    TESTING = "testing"
    MARKET_VALIDATION = "market_validation"
    TALENT_ACQUISITION = "talent_acquisition"
    INFRASTRUCTURE = "infrastructure"
    CONTINGENCY = "contingency"

class BudgetStatus(str, Enum):
    """預算狀態枚舉"""
    ACTIVE = "active"
    FROZEN = "frozen"
    EXHAUSTED = "exhausted"
    CLOSED = "closed"

class ROIExemptionReason(str, Enum):
    """ROI豁免原因枚舉"""
    INITIAL_PERIOD = "initial_period"
    HIGH_INNOVATION_RISK = "high_innovation_risk"
    STRATEGIC_IMPORTANCE = "strategic_importance"
    MARKET_DEVELOPMENT = "market_development"
    REGULATORY_REQUIREMENTS = "regulatory_requirements"

@dataclass
class BudgetAllocationRequest:
    """預算分配請求"""
    project_id: uuid.UUID
    requested_amount: Decimal
    category: BudgetCategory
    justification: str
    urgency_level: str = "medium"
    expected_outcomes: List[str] = field(default_factory=list)
    timeline: str = "quarterly"
    requested_by: str = "system"

@dataclass
class BudgetAllocationResult:
    """預算分配結果"""
    allocation_id: uuid.UUID
    project_id: uuid.UUID
    approved_amount: Decimal
    requested_amount: Decimal
    category: BudgetCategory
    approval_status: str
    approval_reason: str
    conditions: List[str] = field(default_factory=list)
    allocated_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expiry_date: Optional[datetime] = None

@dataclass
class ROIExemptionEvaluation:
    """ROI豁免評估"""
    project_id: uuid.UUID
    current_exemption_status: ROIExemptionStatus
    exemption_start_date: date
    exemption_end_date: Optional[date]
    quarters_used: int
    quarters_remaining: int
    should_continue: bool
    continuation_reason: str
    performance_indicators: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendation: str
    next_review_date: date

@dataclass
class BudgetUtilizationReport:
    """預算使用報告"""
    project_id: uuid.UUID
    reporting_period: str
    total_allocated: Decimal
    total_spent: Decimal
    total_committed: Decimal
    utilization_rate: float
    burn_rate: Decimal
    runway_months: Optional[float]
    budget_efficiency_score: float
    category_breakdown: Dict[str, Decimal]
    variance_analysis: Dict[str, Any]
    recommendations: List[str]

class BudgetROIManager:
    """
    預算分配和ROI豁免管理器
    
    功能：
    1. 創新特區預算分配管理
    2. ROI豁免期規則執行
    3. 預算使用監控和分析
    4. ROI豁免評估和延續決策
    5. 預算效率優化建議
    6. 與虛擬損益表系統整合
    """
    
    def __init__(self, innovation_db: Optional[InnovationZoneDB] = None):
        """初始化預算和ROI豁免管理器"""
        self.logger = logger
        self.innovation_db = innovation_db or InnovationZoneDB()
        
        # 預算配置
        self.budget_config = {
            'rd_budget_allocation_range': (0.05, 0.10),  # 5-10% 研發預算
            'quarterly_budget_limit_percentage': 0.30,    # 季度預算限制
            'emergency_budget_reserve': 0.15,             # 緊急預算儲備
            'budget_reallocation_threshold': 0.20,        # 預算重新分配閾值
            'budget_alert_thresholds': {
                'warning': 0.75,
                'critical': 0.90,
                'emergency': 0.95
            }
        }
        
        # ROI豁免配置
        self.roi_exemption_config = {
            'default_exemption_quarters': 4,
            'maximum_exemption_quarters': 8,
            'exemption_extension_threshold': 75.0,
            'performance_review_intervals': 'quarterly',
            'auto_transition_enabled': True,
            'exemption_reasons_weights': {
                ROIExemptionReason.INITIAL_PERIOD: 1.0,
                ROIExemptionReason.HIGH_INNOVATION_RISK: 0.8,
                ROIExemptionReason.STRATEGIC_IMPORTANCE: 0.9,
                ROIExemptionReason.MARKET_DEVELOPMENT: 0.7,
                ROIExemptionReason.REGULATORY_REQUIREMENTS: 0.6
            }
        }
        
        # 預算類別權重
        self.category_weights = {
            BudgetCategory.RESEARCH: 0.25,
            BudgetCategory.DEVELOPMENT: 0.30,
            BudgetCategory.PROTOTYPING: 0.20,
            BudgetCategory.TESTING: 0.10,
            BudgetCategory.MARKET_VALIDATION: 0.05,
            BudgetCategory.TALENT_ACQUISITION: 0.15,
            BudgetCategory.INFRASTRUCTURE: 0.10,
            BudgetCategory.CONTINGENCY: 0.10
        }
        
        # 管理統計
        self.management_stats = {
            'budgets_allocated': 0,
            'roi_exemptions_granted': 0,
            'roi_exemptions_extended': 0,
            'budget_alerts_generated': 0,
            'total_budget_managed': Decimal('0')
        }
        
        self.logger.info("✅ Budget and ROI Manager initialized")
    
    # ==================== 預算分配管理 ====================
    
    async def allocate_project_budget(
        self,
        project_id: uuid.UUID,
        requested_amount: float,
        category: str,
        justification: str,
        requested_by: str
    ) -> Dict[str, Any]:
        """為項目分配預算"""
        try:
            allocation_request = BudgetAllocationRequest(
                project_id=project_id,
                requested_amount=Decimal(str(requested_amount)),
                category=BudgetCategory(category),
                justification=justification,
                requested_by=requested_by
            )
            
            # 獲取項目信息
            project = await self.innovation_db.get_innovation_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found',
                    'message': f"Project {project_id} does not exist"
                }
            
            # 評估預算請求
            evaluation_result = await self._evaluate_budget_request(allocation_request, project)
            
            if not evaluation_result['approved']:
                return {
                    'success': False,
                    'evaluation_result': evaluation_result,
                    'message': f"Budget request rejected: {evaluation_result['reason']}"
                }
            
            # 執行預算分配
            allocation_result = await self._execute_budget_allocation(
                allocation_request, evaluation_result
            )
            
            # 更新管理統計
            self.management_stats['budgets_allocated'] += 1
            self.management_stats['total_budget_managed'] += allocation_result.approved_amount
            
            self.logger.info(
                f"✅ Allocated budget: {allocation_result.approved_amount} "
                f"to project {project_id} for {category}"
            )
            
            return {
                'success': True,
                'allocation_result': {
                    'allocation_id': str(allocation_result.allocation_id),
                    'approved_amount': float(allocation_result.approved_amount),
                    'category': allocation_result.category.value,
                    'approval_status': allocation_result.approval_status,
                    'conditions': allocation_result.conditions,
                    'allocated_date': allocation_result.allocated_date.isoformat()
                },
                'evaluation_details': evaluation_result,
                'message': f"Successfully allocated {allocation_result.approved_amount} for {category}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error allocating project budget {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to allocate project budget"
            }
    
    async def monitor_budget_utilization(
        self,
        project_id: uuid.UUID,
        reporting_period: str = "current_quarter"
    ) -> BudgetUtilizationReport:
        """監控預算使用情況"""
        try:
            # 獲取項目預算數據
            project = await self.innovation_db.get_innovation_project(
                project_id, include_budget=True
            )
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            budget_tracking = project.get('budget_tracking', [])
            
            # 計算預算統計
            total_allocated = sum(
                Decimal(str(bt['amount'])) for bt in budget_tracking
                if bt['transaction_type'] == 'allocation'
            )
            
            total_spent = sum(
                Decimal(str(bt['amount'])) for bt in budget_tracking
                if bt['transaction_type'] == 'expense'
            )
            
            total_committed = sum(
                Decimal(str(bt['amount'])) for bt in budget_tracking
                if bt.get('committed', False)
            )
            
            # 計算使用率
            utilization_rate = float(total_spent / total_allocated) if total_allocated > 0 else 0.0
            
            # 計算燒錢率（每月支出）
            burn_rate = await self._calculate_burn_rate(budget_tracking)
            
            # 計算剩余跑道
            remaining_budget = total_allocated - total_spent - total_committed
            runway_months = float(remaining_budget / burn_rate) if burn_rate > 0 else None
            
            # 計算預算效率分數
            efficiency_score = await self._calculate_budget_efficiency_score(
                project_id, total_allocated, total_spent, budget_tracking
            )
            
            # 按類別分解
            category_breakdown = await self._analyze_budget_by_category(budget_tracking)
            
            # 差異分析
            variance_analysis = await self._perform_variance_analysis(
                project_id, budget_tracking
            )
            
            # 生成建議
            recommendations = await self._generate_budget_recommendations(
                utilization_rate, burn_rate, runway_months, efficiency_score
            )
            
            report = BudgetUtilizationReport(
                project_id=project_id,
                reporting_period=reporting_period,
                total_allocated=total_allocated,
                total_spent=total_spent,
                total_committed=total_committed,
                utilization_rate=utilization_rate,
                burn_rate=burn_rate,
                runway_months=runway_months,
                budget_efficiency_score=efficiency_score,
                category_breakdown=category_breakdown,
                variance_analysis=variance_analysis,
                recommendations=recommendations
            )
            
            # 檢查是否需要發出預警
            await self._check_budget_alerts(project_id, report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error monitoring budget utilization {project_id}: {e}")
            raise
    
    # ==================== ROI豁免管理 ====================
    
    async def grant_roi_exemption(
        self,
        project_id: uuid.UUID,
        exemption_quarters: int = None,
        reason: ROIExemptionReason = ROIExemptionReason.INITIAL_PERIOD,
        additional_justification: str = ""
    ) -> Dict[str, Any]:
        """授予ROI豁免"""
        try:
            # 獲取項目信息
            project = await self.innovation_db.get_innovation_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found',
                    'message': f"Project {project_id} does not exist"
                }
            
            # 確定豁免期長度
            quarters = exemption_quarters or self.roi_exemption_config['default_exemption_quarters']
            max_quarters = self.roi_exemption_config['maximum_exemption_quarters']
            
            if quarters > max_quarters:
                return {
                    'success': False,
                    'error': 'Exceeds maximum exemption period',
                    'message': f"Requested {quarters} quarters exceeds maximum of {max_quarters}"
                }
            
            # 計算豁免結束日期
            exemption_start = project.get('roi_exemption_start_date', date.today())
            exemption_end = exemption_start + timedelta(days=quarters * 90)
            
            # 更新項目ROI豁免狀態
            updated_project = await self.innovation_db.update_innovation_project(
                project_id,
                {
                    'roi_exemption_status': ROIExemptionStatus.EXEMPT.value,
                    'roi_exemption_start_date': exemption_start,
                    'roi_exemption_end_date': exemption_end
                }
            )
            
            self.management_stats['roi_exemptions_granted'] += 1
            
            self.logger.info(
                f"✅ Granted ROI exemption: {project_id} for {quarters} quarters"
            )
            
            return {
                'success': True,
                'exemption_details': {
                    'project_id': str(project_id),
                    'exemption_status': ROIExemptionStatus.EXEMPT.value,
                    'exemption_quarters': quarters,
                    'exemption_start': exemption_start.isoformat(),
                    'exemption_end': exemption_end.isoformat(),
                    'reason': reason.value,
                    'justification': additional_justification
                },
                'message': f"ROI exemption granted for {quarters} quarters"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error granting ROI exemption {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to grant ROI exemption"
            }
    
    async def evaluate_roi_exemption_continuation(
        self,
        project_id: uuid.UUID
    ) -> Dict[str, Any]:
        """評估ROI豁免延續"""
        try:
            # 獲取項目詳細信息
            project = await self.innovation_db.get_innovation_project(
                project_id,
                include_milestones=True,
                include_budget=True,
                include_metrics=True
            )
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # 計算已使用的豁免期
            exemption_start = project.get('roi_exemption_start_date')
            exemption_end = project.get('roi_exemption_end_date')
            
            if not exemption_start or not exemption_end:
                return {
                    'should_continue': False,
                    'recommendation': 'No active ROI exemption found'
                }
            
            # 轉換日期格式
            if isinstance(exemption_start, str):
                exemption_start = date.fromisoformat(exemption_start)
            if isinstance(exemption_end, str):
                exemption_end = date.fromisoformat(exemption_end)
            
            total_days = (exemption_end - exemption_start).days
            used_days = (date.today() - exemption_start).days
            quarters_used = used_days // 90
            quarters_remaining = max(0, (total_days - used_days) // 90)
            
            # 評估項目表現
            performance_score = await self._evaluate_project_performance(project)
            
            # 評估創新風險
            risk_assessment = await self._assess_exemption_risk(project)
            
            # 決策邏輯
            should_continue = self._should_continue_exemption(
                performance_score, risk_assessment, quarters_used
            )
            
            # 生成建議
            recommendation = await self._generate_exemption_recommendation(
                should_continue, performance_score, risk_assessment, quarters_remaining
            )
            
            evaluation = ROIExemptionEvaluation(
                project_id=project_id,
                current_exemption_status=ROIExemptionStatus(project['roi_exemption_status']),
                exemption_start_date=exemption_start,
                exemption_end_date=exemption_end,
                quarters_used=quarters_used,
                quarters_remaining=quarters_remaining,
                should_continue=should_continue,
                continuation_reason=recommendation,
                performance_indicators=performance_score,
                risk_assessment=risk_assessment,
                recommendation=recommendation,
                next_review_date=date.today() + timedelta(days=90)
            )
            
            return {
                'should_continue': should_continue,
                'recommendation': recommendation,
                'evaluation_details': {
                    'quarters_used': quarters_used,
                    'quarters_remaining': quarters_remaining,
                    'performance_score': performance_score,
                    'risk_assessment': risk_assessment,
                    'next_review_date': evaluation.next_review_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating ROI exemption continuation {project_id}: {e}")
            raise
    
    async def transition_from_exemption(
        self,
        project_id: uuid.UUID,
        transition_type: str = "gradual"
    ) -> Dict[str, Any]:
        """從ROI豁免期轉換到正常評估"""
        try:
            project = await self.innovation_db.get_innovation_project(project_id)
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found'
                }
            
            # 確定轉換策略
            if transition_type == "immediate":
                new_status = ROIExemptionStatus.EVALUATION_REQUIRED
            elif transition_type == "gradual":
                new_status = ROIExemptionStatus.MONITORING
            else:
                new_status = ROIExemptionStatus.PARTIAL_EXEMPT
            
            # 設置轉換時間表
            transition_plan = await self._create_transition_plan(project, transition_type)
            
            # 更新項目狀態
            updated_project = await self.innovation_db.update_innovation_project(
                project_id,
                {
                    'roi_exemption_status': new_status.value,
                    'roi_exemption_end_date': date.today()
                }
            )
            
            self.logger.info(
                f"✅ Transitioned project {project_id} from ROI exemption to {new_status.value}"
            )
            
            return {
                'success': True,
                'transition_details': {
                    'project_id': str(project_id),
                    'new_status': new_status.value,
                    'transition_type': transition_type,
                    'transition_plan': transition_plan,
                    'transition_date': date.today().isoformat()
                },
                'message': f"Successfully transitioned to {new_status.value}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error transitioning from ROI exemption {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to transition from ROI exemption"
            }
    
    # ==================== 輔助方法 ====================
    
    async def _evaluate_budget_request(
        self,
        request: BudgetAllocationRequest,
        project: Dict[str, Any]
    ) -> Dict[str, Any]:
        """評估預算請求"""
        evaluation = {
            'approved': False,
            'reason': '',
            'approved_amount': Decimal('0'),
            'conditions': []
        }
        
        # 檢查項目狀態
        if not project.get('is_active', False):
            evaluation['reason'] = 'Project is not active'
            return evaluation
        
        # 檢查預算合理性
        if request.requested_amount <= 0:
            evaluation['reason'] = 'Invalid requested amount'
            return evaluation
        
        # 檢查項目當前預算狀況
        current_utilization = await self._get_current_budget_utilization(request.project_id)
        
        if current_utilization >= 0.95:
            evaluation['reason'] = 'Project budget nearly exhausted'
            return evaluation
        
        # 檢查類別合理性
        category_allocation = await self._get_category_allocation(request.project_id, request.category)
        category_limit = self.category_weights.get(request.category, 0.1) * 100000  # 假設項目總預算
        
        if category_allocation + request.requested_amount > category_limit:
            # 部分批准
            approved_amount = max(Decimal('0'), category_limit - category_allocation)
            evaluation['approved'] = approved_amount > 0
            evaluation['approved_amount'] = approved_amount
            evaluation['reason'] = f'Partial approval due to category limit'
            evaluation['conditions'].append('Monitor category spending closely')
        else:
            # 完全批准
            evaluation['approved'] = True
            evaluation['approved_amount'] = request.requested_amount
            evaluation['reason'] = 'Request approved based on evaluation criteria'
        
        return evaluation
    
    async def _execute_budget_allocation(
        self,
        request: BudgetAllocationRequest,
        evaluation: Dict[str, Any]
    ) -> BudgetAllocationResult:
        """執行預算分配"""
        allocation_id = uuid.uuid4()
        
        result = BudgetAllocationResult(
            allocation_id=allocation_id,
            project_id=request.project_id,
            approved_amount=evaluation['approved_amount'],
            requested_amount=request.requested_amount,
            category=request.category,
            approval_status='approved' if evaluation['approved'] else 'rejected',
            approval_reason=evaluation['reason'],
            conditions=evaluation.get('conditions', [])
        )
        
        return result
    
    async def _calculate_burn_rate(self, budget_tracking: List[Dict[str, Any]]) -> Decimal:
        """計算燒錢率"""
        # 獲取過去30天的支出
        thirty_days_ago = date.today() - timedelta(days=30)
        
        recent_expenses = [
            bt for bt in budget_tracking
            if (bt['transaction_type'] == 'expense' and
                date.fromisoformat(bt['transaction_date']) >= thirty_days_ago)
        ]
        
        if not recent_expenses:
            return Decimal('0')
        
        total_expenses = sum(Decimal(str(bt['amount'])) for bt in recent_expenses)
        return total_expenses / Decimal('30') * Decimal('30')  # 月平均
    
    async def _calculate_budget_efficiency_score(
        self,
        project_id: uuid.UUID,
        total_allocated: Decimal,
        total_spent: Decimal,
        budget_tracking: List[Dict[str, Any]]
    ) -> float:
        """計算預算效率分數"""
        if total_allocated == 0:
            return 0.0
        
        # 基礎效率分數
        utilization_score = min(100, float(total_spent / total_allocated * 100))
        
        # 調整因素
        # 1. 超支懲罰
        if total_spent > total_allocated:
            utilization_score *= 0.8
        
        # 2. 使用速度合理性
        expected_monthly_burn = total_allocated / Decimal('12')  # 假設12月項目
        actual_burn_rate = await self._calculate_burn_rate(budget_tracking)
        
        if actual_burn_rate > expected_monthly_burn * Decimal('1.5'):
            utilization_score *= 0.9  # 燒錢過快懲罰
        
        return min(100.0, utilization_score)
    
    async def _analyze_budget_by_category(
        self,
        budget_tracking: List[Dict[str, Any]]
    ) -> Dict[str, Decimal]:
        """按類別分析預算"""
        category_spending = {}
        
        for bt in budget_tracking:
            if bt['transaction_type'] == 'expense':
                category = bt.get('expense_category', 'other')
                amount = Decimal(str(bt['amount']))
                category_spending[category] = category_spending.get(category, Decimal('0')) + amount
        
        return category_spending
    
    async def _perform_variance_analysis(
        self,
        project_id: uuid.UUID,
        budget_tracking: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """執行差異分析"""
        # 這裡應該與計劃預算進行比較
        # 暫時返回基本分析
        
        return {
            'total_variance': 0.0,
            'category_variances': {},
            'variance_reasons': [],
            'corrective_actions': []
        }
    
    async def _generate_budget_recommendations(
        self,
        utilization_rate: float,
        burn_rate: Decimal,
        runway_months: Optional[float],
        efficiency_score: float
    ) -> List[str]:
        """生成預算建議"""
        recommendations = []
        
        if utilization_rate > 0.9:
            recommendations.append("Budget utilization is high - consider requesting additional allocation")
        elif utilization_rate < 0.5:
            recommendations.append("Low budget utilization - review spending plan and priorities")
        
        if runway_months and runway_months < 3:
            recommendations.append("Critical: Less than 3 months of budget remaining")
        elif runway_months and runway_months < 6:
            recommendations.append("Warning: Less than 6 months of budget remaining")
        
        if efficiency_score < 60:
            recommendations.append("Low budget efficiency detected - review spending effectiveness")
        
        if burn_rate > Decimal('10000'):  # 假設閾值
            recommendations.append("High burn rate detected - consider optimizing expenses")
        
        return recommendations
    
    async def _check_budget_alerts(
        self,
        project_id: uuid.UUID,
        report: BudgetUtilizationReport
    ):
        """檢查預算預警"""
        alert_thresholds = self.budget_config['budget_alert_thresholds']
        
        if report.utilization_rate >= alert_thresholds['emergency']:
            await self._trigger_budget_alert(project_id, 'emergency', report)
        elif report.utilization_rate >= alert_thresholds['critical']:
            await self._trigger_budget_alert(project_id, 'critical', report)
        elif report.utilization_rate >= alert_thresholds['warning']:
            await self._trigger_budget_alert(project_id, 'warning', report)
    
    async def _trigger_budget_alert(
        self,
        project_id: uuid.UUID,
        alert_level: str,
        report: BudgetUtilizationReport
    ):
        """觸發預算預警"""
        self.management_stats['budget_alerts_generated'] += 1
        
        self.logger.warning(
            f"🚨 Budget alert ({alert_level}) for project {project_id}: "
            f"Utilization rate {report.utilization_rate:.1%}"
        )
    
    def _should_continue_exemption(
        self,
        performance_score: Dict[str, Any],
        risk_assessment: Dict[str, Any],
        quarters_used: int
    ) -> bool:
        """判斷是否應該繼續豁免"""
        # 基本決策邏輯
        overall_performance = performance_score.get('overall_score', 50)
        risk_level = risk_assessment.get('risk_level', 'medium')
        
        # 如果已經使用超過6個季度，更嚴格的標準
        if quarters_used >= 6:
            return overall_performance >= 80 and risk_level in ['low', 'medium']
        
        # 如果表現良好且風險可控，可以繼續
        return overall_performance >= 60 and risk_level != 'critical'
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            db_health = await self.innovation_db.health_check()
            
            return {
                'component': 'budget_roi_manager',
                'status': 'healthy' if db_health['status'] == 'healthy' else 'degraded',
                'timestamp': datetime.now(timezone.utc),
                'management_stats': {
                    k: int(v) if isinstance(v, Decimal) else v 
                    for k, v in self.management_stats.items()
                },
                'configuration': {
                    'default_exemption_quarters': self.roi_exemption_config['default_exemption_quarters'],
                    'budget_alert_thresholds': self.budget_config['budget_alert_thresholds']
                },
                'database_status': db_health['status']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                'component': 'budget_roi_manager',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }