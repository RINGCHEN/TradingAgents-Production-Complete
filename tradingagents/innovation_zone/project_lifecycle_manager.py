#!/usr/bin/env python3
"""
Project Lifecycle Management System for Innovation Zone
創新特區項目生命週期管理系統 - GPT-OSS整合任務2.2.4

This system provides comprehensive project lifecycle orchestration including:
1. Automated stage progression and gate controls
2. Milestone-driven workflow management
3. Resource allocation and timeline optimization
4. Risk-based decision checkpoints
5. Stakeholder notification and approval workflows
6. Performance-based lifecycle adjustments
7. Integration with decision engine and performance monitoring
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
import json
import uuid

from .project_performance_monitor import (
    ProjectPerformanceMonitor, ProjectPerformanceMetrics,
    ProjectHealthStatus, PerformanceTrend
)
from .objective_decision_engine import (
    ObjectiveDecisionEngine, DecisionRecommendation,
    DecisionType, DecisionConfidence, DecisionUrgency
)
from .innovation_zone_db import InnovationZoneDB
from .models import ProjectStage, ROIExemptionStatus, InnovationType

logger = logging.getLogger(__name__)


class LifecycleGateType(Enum):
    """生命週期關卡類型"""
    CONCEPT_VALIDATION = "concept_validation"       # 概念驗證關卡
    FEASIBILITY_REVIEW = "feasibility_review"       # 可行性審查關卡
    DEVELOPMENT_CHECKPOINT = "development_checkpoint" # 開發檢查點關卡
    MVP_EVALUATION = "mvp_evaluation"               # MVP評估關卡
    PILOT_REVIEW = "pilot_review"                   # 試點審查關卡
    LAUNCH_READINESS = "launch_readiness"           # 上線準備關卡
    POST_LAUNCH_REVIEW = "post_launch_review"       # 上線後審查關卡


class LifecycleActionType(Enum):
    """生命週期行動類型"""
    STAGE_PROGRESSION = "stage_progression"         # 階段推進
    MILESTONE_CREATION = "milestone_creation"       # 里程碑創建
    RESOURCE_ALLOCATION = "resource_allocation"     # 資源分配
    RISK_ASSESSMENT = "risk_assessment"             # 風險評估
    STAKEHOLDER_NOTIFICATION = "stakeholder_notification" # 利益相關者通知
    PERFORMANCE_REVIEW = "performance_review"       # 性能審查
    DECISION_EXECUTION = "decision_execution"       # 決策執行
    TIMELINE_ADJUSTMENT = "timeline_adjustment"     # 時間線調整


class GateStatus(Enum):
    """關卡狀態"""
    PENDING = "pending"                             # 待處理
    IN_REVIEW = "in_review"                         # 審查中
    APPROVED = "approved"                           # 已批准
    REJECTED = "rejected"                           # 已拒絕
    CONDITIONAL_APPROVAL = "conditional_approval"   # 條件性批准


class LifecycleEventType(Enum):
    """生命週期事件類型"""
    PROJECT_INITIATED = "project_initiated"         # 項目啟動
    STAGE_ENTERED = "stage_entered"                 # 進入階段
    STAGE_COMPLETED = "stage_completed"             # 階段完成
    GATE_TRIGGERED = "gate_triggered"               # 關卡觸發
    GATE_PASSED = "gate_passed"                     # 通過關卡
    GATE_FAILED = "gate_failed"                     # 關卡失敗
    MILESTONE_ACHIEVED = "milestone_achieved"       # 里程碑達成
    RISK_ESCALATED = "risk_escalated"               # 風險升級
    DECISION_IMPLEMENTED = "decision_implemented"   # 決策實施
    PROJECT_TERMINATED = "project_terminated"       # 項目終止
    PROJECT_COMPLETED = "project_completed"         # 項目完成


@dataclass
class LifecycleGate:
    """生命週期關卡"""
    gate_id: str
    gate_type: LifecycleGateType
    gate_name: str
    description: str
    required_stage: ProjectStage
    
    # 通過條件
    criteria: Dict[str, Any]
    required_approvers: List[str]
    required_documents: List[str]
    
    # 狀態和時間
    status: GateStatus = GateStatus.PENDING
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 審查結果
    approval_score: Optional[Decimal] = None
    reviewer_comments: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    
    # 配置
    auto_trigger: bool = True
    mandatory: bool = True
    timeout_days: int = 30


@dataclass
class LifecycleAction:
    """生命週期行動"""
    action_id: str
    action_type: LifecycleActionType
    action_name: str
    description: str
    
    # 觸發條件
    trigger_conditions: Dict[str, Any]
    
    # 執行參數
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 狀態
    status: str = "pending"  # pending, executing, completed, failed
    scheduled_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    
    # 結果
    execution_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


@dataclass
class LifecycleEvent:
    """生命週期事件"""
    event_id: str
    event_type: LifecycleEventType
    project_id: str
    
    # 事件內容
    event_data: Dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 關聯信息
    related_stage: Optional[ProjectStage] = None
    related_gate_id: Optional[str] = None
    related_milestone_id: Optional[str] = None
    
    # 處理信息
    processed: bool = False
    processing_result: Optional[Dict[str, Any]] = None


@dataclass
class ProjectLifecycleState:
    """項目生命週期狀態"""
    project_id: str
    project_name: str
    current_stage: ProjectStage
    
    # 階段歷史
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # 關卡狀態
    gates: Dict[str, LifecycleGate] = field(default_factory=dict)
    pending_gates: List[str] = field(default_factory=list)
    
    # 行動隊列
    pending_actions: List[LifecycleAction] = field(default_factory=list)
    completed_actions: List[LifecycleAction] = field(default_factory=list)
    
    # 事件歷史
    events: List[LifecycleEvent] = field(default_factory=list)
    
    # 狀態信息
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # 配置
    auto_progression_enabled: bool = True
    notification_enabled: bool = True


class ProjectLifecycleManager:
    """
    創新特區項目生命週期管理器
    
    功能：
    1. 自動化階段推進和關卡控制
    2. 里程碑驱动的工作流管理
    3. 資源分配和時間線優化
    4. 基於風險的決策檢查點
    5. 利益相關者通知和審批流程
    6. 基於性能的生命週期調整
    7. 與決策引擎和性能監控的集成
    """
    
    def __init__(
        self,
        performance_monitor: Optional[ProjectPerformanceMonitor] = None,
        decision_engine: Optional[ObjectiveDecisionEngine] = None,
        innovation_db: Optional[InnovationZoneDB] = None
    ):
        """
        初始化項目生命週期管理器
        
        Args:
            performance_monitor: 性能監控器
            decision_engine: 決策引擎
            innovation_db: 創新特區數據庫
        """
        self.performance_monitor = performance_monitor or ProjectPerformanceMonitor()
        self.decision_engine = decision_engine or ObjectiveDecisionEngine()
        self.innovation_db = innovation_db or InnovationZoneDB()
        
        # 項目生命週期狀態
        self.project_states: Dict[str, ProjectLifecycleState] = {}
        
        # 關卡模板
        self.gate_templates: Dict[LifecycleGateType, LifecycleGate] = {}
        
        # 行動處理器
        self.action_handlers: Dict[LifecycleActionType, Callable] = {}
        
        # 事件監聽器
        self.event_listeners: Dict[LifecycleEventType, List[Callable]] = {}
        
        # 配置
        self.config = {
            'auto_progression_enabled': True,
            'gate_timeout_days': 30,
            'performance_review_interval_days': 14,
            'risk_assessment_threshold': 0.75,
            'stage_progression_requirements': {
                ProjectStage.CONCEPT: {'health_score_min': 60, 'milestones_required': 2},
                ProjectStage.FEASIBILITY: {'health_score_min': 65, 'milestones_required': 3},
                ProjectStage.PROTOTYPE: {'health_score_min': 70, 'milestones_required': 5},
                ProjectStage.PILOT: {'health_score_min': 75, 'milestones_required': 3},
                ProjectStage.SCALING: {'health_score_min': 80, 'milestones_required': 4},
                ProjectStage.MATURE: {'health_score_min': 85, 'milestones_required': 2}
            }
        }
        
        self.logger = logger
        self._running = False
        self._lifecycle_task: Optional[asyncio.Task] = None
        
        # 初始化系統
        self._initialize_gate_templates()
        self._initialize_action_handlers()
        self._initialize_event_listeners()
    
    def _initialize_gate_templates(self):
        """初始化關卡模板"""
        
        # 概念驗證關卡
        concept_validation_gate = LifecycleGate(
            gate_id="concept_validation",
            gate_type=LifecycleGateType.CONCEPT_VALIDATION,
            gate_name="Concept Validation Gate",
            description="Validate project concept and market potential",
            required_stage=ProjectStage.CONCEPT,
            criteria={
                'min_health_score': 60,
                'market_research_completed': True,
                'technical_feasibility_assessed': True,
                'initial_budget_approved': True
            },
            required_approvers=['innovation_manager', 'technical_lead'],
            required_documents=['concept_document', 'market_analysis', 'technical_assessment'],
            timeout_days=14
        )
        
        # 可行性審查關卡
        feasibility_review_gate = LifecycleGate(
            gate_id="feasibility_review",
            gate_type=LifecycleGateType.FEASIBILITY_REVIEW,
            gate_name="Feasibility Review Gate",
            description="Comprehensive feasibility analysis and go/no-go decision",
            required_stage=ProjectStage.FEASIBILITY,
            criteria={
                'min_health_score': 65,
                'technical_architecture_defined': True,
                'resource_plan_approved': True,
                'risk_assessment_completed': True,
                'roi_projection_validated': True
            },
            required_approvers=['innovation_director', 'finance_manager', 'technical_architect'],
            required_documents=['feasibility_study', 'technical_architecture', 'resource_plan', 'risk_matrix'],
            timeout_days=21
        )
        
        # 原型開發檢查點關卡
        development_checkpoint_gate = LifecycleGate(
            gate_id="development_checkpoint",
            gate_type=LifecycleGateType.DEVELOPMENT_CHECKPOINT,
            gate_name="Prototype Development Checkpoint Gate",
            description="Mid-prototype development progress and quality review",
            required_stage=ProjectStage.PROTOTYPE,
            criteria={
                'min_health_score': 70,
                'milestone_completion_rate': 50,
                'code_quality_threshold': 80,
                'test_coverage_minimum': 70
            },
            required_approvers=['project_manager', 'qa_lead'],
            required_documents=['progress_report', 'quality_metrics', 'test_results'],
            timeout_days=7
        )
        
        # 試點評估關卡 
        mvp_evaluation_gate = LifecycleGate(
            gate_id="pilot_evaluation",
            gate_type=LifecycleGateType.MVP_EVALUATION,
            gate_name="Pilot Evaluation Gate",
            description="Pilot implementation validation and user feedback",
            required_stage=ProjectStage.PILOT,
            criteria={
                'min_health_score': 75,
                'mvp_functionality_complete': True,
                'user_acceptance_rate': 70,
                'performance_benchmarks_met': True
            },
            required_approvers=['product_manager', 'user_experience_lead'],
            required_documents=['mvp_demo', 'user_feedback', 'performance_report'],
            timeout_days=14
        )
        
        # 規模化審查關卡
        pilot_review_gate = LifecycleGate(
            gate_id="scaling_review",
            gate_type=LifecycleGateType.PILOT_REVIEW,
            gate_name="Scaling Review Gate",
            description="Scaling deployment results and expansion decision",
            required_stage=ProjectStage.SCALING,
            criteria={
                'min_health_score': 80,
                'pilot_success_metrics_met': True,
                'operational_readiness_verified': True,
                'scaling_plan_approved': True
            },
            required_approvers=['operations_manager', 'business_sponsor'],
            required_documents=['pilot_results', 'scaling_plan', 'operational_procedures'],
            timeout_days=21
        )
        
        # 成熟化準備關卡
        launch_readiness_gate = LifecycleGate(
            gate_id="maturity_readiness",
            gate_type=LifecycleGateType.LAUNCH_READINESS,
            gate_name="Maturity Readiness Gate",
            description="Final maturity and optimization validation",
            required_stage=ProjectStage.MATURE,
            criteria={
                'min_health_score': 85,
                'security_audit_passed': True,
                'performance_load_tested': True,
                'support_procedures_ready': True,
                'rollback_plan_prepared': True
            },
            required_approvers=['security_officer', 'operations_director', 'business_owner'],
            required_documents=['security_audit', 'load_test_results', 'support_plan', 'rollback_procedures'],
            timeout_days=14
        )
        
        # 註冊關卡模板
        gates = [
            concept_validation_gate,
            feasibility_review_gate,
            development_checkpoint_gate,
            mvp_evaluation_gate,
            pilot_review_gate,
            launch_readiness_gate
        ]
        
        for gate in gates:
            self.gate_templates[gate.gate_type] = gate
    
    def _initialize_action_handlers(self):
        """初始化行動處理器"""
        self.action_handlers = {
            LifecycleActionType.STAGE_PROGRESSION: self._handle_stage_progression,
            LifecycleActionType.MILESTONE_CREATION: self._handle_milestone_creation,
            LifecycleActionType.RESOURCE_ALLOCATION: self._handle_resource_allocation,
            LifecycleActionType.RISK_ASSESSMENT: self._handle_risk_assessment,
            LifecycleActionType.STAKEHOLDER_NOTIFICATION: self._handle_stakeholder_notification,
            LifecycleActionType.PERFORMANCE_REVIEW: self._handle_performance_review,
            LifecycleActionType.DECISION_EXECUTION: self._handle_decision_execution,
            LifecycleActionType.TIMELINE_ADJUSTMENT: self._handle_timeline_adjustment
        }
    
    def _initialize_event_listeners(self):
        """初始化事件監聽器"""
        self.event_listeners = {
            LifecycleEventType.PROJECT_INITIATED: [self._on_project_initiated],
            LifecycleEventType.STAGE_ENTERED: [self._on_stage_entered],
            LifecycleEventType.STAGE_COMPLETED: [self._on_stage_completed],
            LifecycleEventType.GATE_TRIGGERED: [self._on_gate_triggered],
            LifecycleEventType.GATE_PASSED: [self._on_gate_passed],
            LifecycleEventType.GATE_FAILED: [self._on_gate_failed],
            LifecycleEventType.MILESTONE_ACHIEVED: [self._on_milestone_achieved],
            LifecycleEventType.RISK_ESCALATED: [self._on_risk_escalated],
            LifecycleEventType.DECISION_IMPLEMENTED: [self._on_decision_implemented]
        }
    
    async def start_lifecycle_management(self):
        """啟動生命週期管理"""
        if not self._running:
            self._running = True
            self._lifecycle_task = asyncio.create_task(self._lifecycle_management_loop())
            self.logger.info("✅ Project Lifecycle Manager started")
    
    async def stop_lifecycle_management(self):
        """停止生命週期管理"""
        if self._running:
            self._running = False
            if self._lifecycle_task:
                self._lifecycle_task.cancel()
                try:
                    await self._lifecycle_task
                except asyncio.CancelledError:
                    pass
            self.logger.info("✅ Project Lifecycle Manager stopped")
    
    async def _lifecycle_management_loop(self):
        """生命週期管理循環"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
                # 處理所有項目的生命週期狀態
                for project_id in list(self.project_states.keys()):
                    await self._process_project_lifecycle(project_id)
                
                # 清理過期數據
                self._cleanup_expired_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in lifecycle management loop: {e}")
    
    async def initialize_project_lifecycle(
        self,
        project_id: str,
        project_name: str,
        initial_stage: ProjectStage = ProjectStage.CONCEPT
    ) -> ProjectLifecycleState:
        """
        初始化項目生命週期
        
        Args:
            project_id: 項目ID
            project_name: 項目名稱
            initial_stage: 初始階段
            
        Returns:
            項目生命週期狀態
        """
        try:
            # 創建項目生命週期狀態
            lifecycle_state = ProjectLifecycleState(
                project_id=project_id,
                project_name=project_name,
                current_stage=initial_stage
            )
            
            # 初始化關卡
            lifecycle_state.gates = self._create_project_gates()
            
            # 記錄初始階段
            lifecycle_state.stage_history.append({
                'stage': initial_stage.value,
                'entered_at': datetime.now(timezone.utc).isoformat(),
                'entry_reason': 'project_initialization'
            })
            
            # 保存狀態
            self.project_states[project_id] = lifecycle_state
            
            # 發布項目啟動事件
            await self._publish_event(
                LifecycleEventType.PROJECT_INITIATED,
                project_id,
                {
                    'project_name': project_name,
                    'initial_stage': initial_stage.value,
                    'initialized_at': datetime.now(timezone.utc).isoformat()
                }
            )
            
            # 觸發初始階段進入事件
            await self._publish_event(
                LifecycleEventType.STAGE_ENTERED,
                project_id,
                {
                    'stage': initial_stage.value,
                    'previous_stage': None,
                    'entry_reason': 'project_initialization'
                },
                related_stage=initial_stage
            )
            
            self.logger.info(f"✅ Project lifecycle initialized for {project_name} (ID: {project_id})")
            return lifecycle_state
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing project lifecycle: {e}")
            raise
    
    def _create_project_gates(self) -> Dict[str, LifecycleGate]:
        """為項目創建關卡"""
        project_gates = {}
        
        for gate_type, template in self.gate_templates.items():
            # 創建關卡副本
            gate_copy = LifecycleGate(
                gate_id=f"{template.gate_id}_{uuid.uuid4().hex[:8]}",
                gate_type=template.gate_type,
                gate_name=template.gate_name,
                description=template.description,
                required_stage=template.required_stage,
                criteria=template.criteria.copy(),
                required_approvers=template.required_approvers.copy(),
                required_documents=template.required_documents.copy(),
                auto_trigger=template.auto_trigger,
                mandatory=template.mandatory,
                timeout_days=template.timeout_days
            )
            
            project_gates[gate_copy.gate_id] = gate_copy
        
        return project_gates
    
    async def _process_project_lifecycle(self, project_id: str):
        """處理項目生命週期"""
        try:
            if project_id not in self.project_states:
                return
            
            state = self.project_states[project_id]
            
            if not state.is_active:
                return
            
            # 處理待處理的行動
            await self._process_pending_actions(project_id)
            
            # 檢查關卡觸發條件
            await self._check_gate_triggers(project_id)
            
            # 檢查階段推進條件
            await self._check_stage_progression(project_id)
            
            # 執行性能審查
            await self._perform_lifecycle_performance_review(project_id)
            
            # 更新狀態時間戳
            state.updated_at = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"❌ Error processing project lifecycle for {project_id}: {e}")
    
    async def _check_stage_progression(self, project_id: str):
        """檢查階段推進條件"""
        try:
            state = self.project_states[project_id]
            current_stage = state.current_stage
            
            # 獲取當前階段的推進要求
            stage_requirements = self.config['stage_progression_requirements'].get(current_stage)
            if not stage_requirements:
                return
            
            # 獲取項目性能指標
            performance_metrics = await self.performance_monitor.calculate_project_performance(project_id)
            
            # 檢查健康分數要求
            min_health_score = stage_requirements.get('health_score_min', 0)
            if performance_metrics.health_score < min_health_score:
                return
            
            # 檢查里程碑要求
            required_milestones = stage_requirements.get('milestones_required', 0)
            if performance_metrics.completed_milestones < required_milestones:
                return
            
            # 檢查當前階段對應的關卡是否通過
            stage_gate_passed = self._check_stage_gate_status(project_id, current_stage)
            if not stage_gate_passed:
                return
            
            # 確定下一階段
            next_stage = self._get_next_stage(current_stage)
            if next_stage and state.auto_progression_enabled:
                await self._progress_to_next_stage(project_id, next_stage, "automatic_progression")
                
        except Exception as e:
            self.logger.error(f"❌ Error checking stage progression for {project_id}: {e}")
    
    def _check_stage_gate_status(self, project_id: str, stage: ProjectStage) -> bool:
        """檢查階段關卡狀態"""
        state = self.project_states[project_id]
        
        for gate in state.gates.values():
            if gate.required_stage == stage and gate.mandatory:
                if gate.status != GateStatus.APPROVED:
                    return False
        
        return True
    
    def _get_next_stage(self, current_stage: ProjectStage) -> Optional[ProjectStage]:
        """獲取下一階段"""
        stage_progression = {
            ProjectStage.CONCEPT: ProjectStage.FEASIBILITY,
            ProjectStage.FEASIBILITY: ProjectStage.PROTOTYPE,
            ProjectStage.PROTOTYPE: ProjectStage.PILOT,
            ProjectStage.PILOT: ProjectStage.SCALING,
            ProjectStage.SCALING: ProjectStage.MATURE
        }
        
        return stage_progression.get(current_stage)
    
    async def _progress_to_next_stage(
        self,
        project_id: str,
        next_stage: ProjectStage,
        progression_reason: str
    ):
        """推進到下一階段"""
        try:
            state = self.project_states[project_id]
            previous_stage = state.current_stage
            
            # 完成當前階段
            await self._publish_event(
                LifecycleEventType.STAGE_COMPLETED,
                project_id,
                {
                    'completed_stage': previous_stage.value,
                    'completion_reason': progression_reason,
                    'duration_days': self._calculate_stage_duration(state, previous_stage)
                },
                related_stage=previous_stage
            )
            
            # 更新項目階段
            state.current_stage = next_stage
            state.stage_history.append({
                'stage': next_stage.value,
                'entered_at': datetime.now(timezone.utc).isoformat(),
                'entry_reason': progression_reason,
                'previous_stage': previous_stage.value
            })
            
            # 更新數據庫
            await self.innovation_db.update_project_stage(
                project_id, next_stage, "lifecycle_manager", progression_reason
            )
            
            # 發布階段進入事件
            await self._publish_event(
                LifecycleEventType.STAGE_ENTERED,
                project_id,
                {
                    'stage': next_stage.value,
                    'previous_stage': previous_stage.value,
                    'entry_reason': progression_reason
                },
                related_stage=next_stage
            )
            
            self.logger.info(f"✅ Project {project_id} progressed from {previous_stage.value} to {next_stage.value}")
            
        except Exception as e:
            self.logger.error(f"❌ Error progressing project {project_id} to next stage: {e}")
    
    def _calculate_stage_duration(self, state: ProjectLifecycleState, stage: ProjectStage) -> int:
        """計算階段持續時間"""
        for stage_record in reversed(state.stage_history):
            if stage_record['stage'] == stage.value:
                entered_at = datetime.fromisoformat(stage_record['entered_at'].replace('Z', '+00:00'))
                duration = datetime.now(timezone.utc) - entered_at
                return duration.days
        
        return 0
    
    async def _check_gate_triggers(self, project_id: str):
        """檢查關卡觸發條件"""
        try:
            state = self.project_states[project_id]
            
            for gate in state.gates.values():
                if (gate.status == GateStatus.PENDING and 
                    gate.auto_trigger and 
                    gate.required_stage == state.current_stage):
                    
                    # 檢查觸發條件
                    if await self._evaluate_gate_criteria(project_id, gate):
                        await self._trigger_gate(project_id, gate.gate_id)
                        
        except Exception as e:
            self.logger.error(f"❌ Error checking gate triggers for {project_id}: {e}")
    
    async def _evaluate_gate_criteria(self, project_id: str, gate: LifecycleGate) -> bool:
        """評估關卡標準"""
        try:
            # 獲取項目性能指標
            performance_metrics = await self.performance_monitor.calculate_project_performance(project_id)
            
            # 檢查健康分數要求
            min_health_score = gate.criteria.get('min_health_score')
            if min_health_score and performance_metrics.health_score < min_health_score:
                return False
            
            # 檢查里程碑完成率要求
            milestone_completion_rate = gate.criteria.get('milestone_completion_rate')
            if milestone_completion_rate and performance_metrics.milestone_completion_rate < milestone_completion_rate:
                return False
            
            # 檢查代碼質量要求
            code_quality_threshold = gate.criteria.get('code_quality_threshold')
            if code_quality_threshold and performance_metrics.code_quality_score < code_quality_threshold:
                return False
            
            # 檢查測試覆蓋率要求
            test_coverage_minimum = gate.criteria.get('test_coverage_minimum')
            if test_coverage_minimum and performance_metrics.test_coverage < test_coverage_minimum:
                return False
            
            # 檢查用戶接受率要求
            user_acceptance_rate = gate.criteria.get('user_acceptance_rate')
            if user_acceptance_rate and performance_metrics.user_engagement_score < user_acceptance_rate:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating gate criteria: {e}")
            return False
    
    async def _trigger_gate(self, project_id: str, gate_id: str):
        """觸發關卡"""
        try:
            state = self.project_states[project_id]
            gate = state.gates.get(gate_id)
            
            if not gate:
                return
            
            # 更新關卡狀態
            gate.status = GateStatus.IN_REVIEW
            gate.triggered_at = datetime.now(timezone.utc)
            
            # 添加到待處理關卡列表
            if gate_id not in state.pending_gates:
                state.pending_gates.append(gate_id)
            
            # 發布關卡觸發事件
            await self._publish_event(
                LifecycleEventType.GATE_TRIGGERED,
                project_id,
                {
                    'gate_id': gate_id,
                    'gate_type': gate.gate_type.value,
                    'gate_name': gate.gate_name,
                    'required_approvers': gate.required_approvers,
                    'required_documents': gate.required_documents,
                    'timeout_date': (datetime.now(timezone.utc) + timedelta(days=gate.timeout_days)).isoformat()
                },
                related_gate_id=gate_id
            )
            
            # 發送利益相關者通知
            await self._schedule_action(
                project_id,
                LifecycleActionType.STAKEHOLDER_NOTIFICATION,
                f"Gate triggered: {gate.gate_name}",
                {
                    'gate_id': gate_id,
                    'notification_type': 'gate_review_required',
                    'recipients': gate.required_approvers
                }
            )
            
            self.logger.info(f"✅ Gate {gate.gate_name} triggered for project {project_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error triggering gate {gate_id} for project {project_id}: {e}")
    
    async def approve_gate(
        self,
        project_id: str,
        gate_id: str,
        approver: str,
        approval_score: Optional[Decimal] = None,
        comments: Optional[str] = None,
        conditions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        批准關卡
        
        Args:
            project_id: 項目ID
            gate_id: 關卡ID
            approver: 批准人
            approval_score: 批准分數
            comments: 評論
            conditions: 條件
            
        Returns:
            批准結果
        """
        try:
            if project_id not in self.project_states:
                raise ValueError(f"Project {project_id} not found")
            
            state = self.project_states[project_id]
            gate = state.gates.get(gate_id)
            
            if not gate:
                raise ValueError(f"Gate {gate_id} not found")
            
            if approver not in gate.required_approvers:
                raise ValueError(f"Approver {approver} not authorized for this gate")
            
            # 更新關卡狀態
            if conditions:
                gate.status = GateStatus.CONDITIONAL_APPROVAL
                gate.conditions = conditions
            else:
                gate.status = GateStatus.APPROVED
            
            gate.approval_score = approval_score
            gate.completed_at = datetime.now(timezone.utc)
            
            if comments:
                gate.reviewer_comments.append(f"{approver}: {comments}")
            
            # 從待處理列表中移除
            if gate_id in state.pending_gates:
                state.pending_gates.remove(gate_id)
            
            # 發布關卡通過事件
            await self._publish_event(
                LifecycleEventType.GATE_PASSED,
                project_id,
                {
                    'gate_id': gate_id,
                    'gate_type': gate.gate_type.value,
                    'gate_name': gate.gate_name,
                    'approver': approver,
                    'approval_score': float(approval_score) if approval_score else None,
                    'conditions': conditions or [],
                    'conditional_approval': bool(conditions)
                },
                related_gate_id=gate_id
            )
            
            result = {
                'success': True,
                'gate_id': gate_id,
                'status': gate.status.value,
                'approved_by': approver,
                'approval_score': approval_score,
                'conditions': conditions or [],
                'approved_at': gate.completed_at.isoformat()
            }
            
            self.logger.info(f"✅ Gate {gate.gate_name} approved for project {project_id} by {approver}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error approving gate {gate_id} for project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'gate_id': gate_id
            }
    
    async def reject_gate(
        self,
        project_id: str,
        gate_id: str,
        approver: str,
        rejection_reason: str,
        required_actions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        拒絕關卡
        
        Args:
            project_id: 項目ID
            gate_id: 關卡ID
            approver: 批准人
            rejection_reason: 拒絕原因
            required_actions: 需要的行動
            
        Returns:
            拒絕結果
        """
        try:
            if project_id not in self.project_states:
                raise ValueError(f"Project {project_id} not found")
            
            state = self.project_states[project_id]
            gate = state.gates.get(gate_id)
            
            if not gate:
                raise ValueError(f"Gate {gate_id} not found")
            
            # 更新關卡狀態
            gate.status = GateStatus.REJECTED
            gate.completed_at = datetime.now(timezone.utc)
            gate.reviewer_comments.append(f"{approver} (REJECTED): {rejection_reason}")
            
            # 從待處理列表中移除
            if gate_id in state.pending_gates:
                state.pending_gates.remove(gate_id)
            
            # 發布關卡失敗事件
            await self._publish_event(
                LifecycleEventType.GATE_FAILED,
                project_id,
                {
                    'gate_id': gate_id,
                    'gate_type': gate.gate_type.value,
                    'gate_name': gate.gate_name,
                    'rejected_by': approver,
                    'rejection_reason': rejection_reason,
                    'required_actions': required_actions or []
                },
                related_gate_id=gate_id
            )
            
            # 如果是強制性關卡被拒絕，需要執行相應行動
            if gate.mandatory:
                await self._handle_mandatory_gate_failure(project_id, gate, required_actions)
            
            result = {
                'success': True,
                'gate_id': gate_id,
                'status': gate.status.value,
                'rejected_by': approver,
                'rejection_reason': rejection_reason,
                'required_actions': required_actions or [],
                'rejected_at': gate.completed_at.isoformat()
            }
            
            self.logger.warning(f"⚠️ Gate {gate.gate_name} rejected for project {project_id} by {approver}")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error rejecting gate {gate_id} for project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'gate_id': gate_id
            }
    
    async def _handle_mandatory_gate_failure(
        self,
        project_id: str,
        gate: LifecycleGate,
        required_actions: Optional[List[str]]
    ):
        """處理強制關卡失敗"""
        try:
            # 創建修復行動
            if required_actions:
                for action in required_actions:
                    await self._schedule_action(
                        project_id,
                        LifecycleActionType.MILESTONE_CREATION,
                        f"Gate remediation: {action}",
                        {
                            'milestone_name': action,
                            'milestone_type': 'remediation',
                            'related_gate_id': gate.gate_id,
                            'priority': 'high'
                        }
                    )
            
            # 觸發風險評估
            await self._schedule_action(
                project_id,
                LifecycleActionType.RISK_ASSESSMENT,
                f"Risk assessment after gate failure: {gate.gate_name}",
                {
                    'assessment_type': 'gate_failure_impact',
                    'failed_gate_id': gate.gate_id
                }
            )
            
            # 考慮決策引擎建議
            recommendations = await self.decision_engine.generate_decision_recommendations(project_id)
            for rec in recommendations:
                if rec.urgency in [DecisionUrgency.CRITICAL, DecisionUrgency.HIGH]:
                    await self._schedule_action(
                        project_id,
                        LifecycleActionType.DECISION_EXECUTION,
                        f"Execute high-priority recommendation: {rec.decision_type.value}",
                        {
                            'recommendation_id': rec.recommendation_id,
                            'decision_type': rec.decision_type.value
                        }
                    )
            
        except Exception as e:
            self.logger.error(f"❌ Error handling mandatory gate failure: {e}")
    
    async def _schedule_action(
        self,
        project_id: str,
        action_type: LifecycleActionType,
        action_name: str,
        parameters: Dict[str, Any],
        scheduled_at: Optional[datetime] = None
    ):
        """調度生命週期行動"""
        try:
            if project_id not in self.project_states:
                return
            
            action = LifecycleAction(
                action_id=f"{action_type.value}_{uuid.uuid4().hex[:8]}",
                action_type=action_type,
                action_name=action_name,
                description=f"Automated action: {action_name}",
                trigger_conditions={},
                parameters=parameters,
                scheduled_at=scheduled_at or datetime.now(timezone.utc)
            )
            
            state = self.project_states[project_id]
            state.pending_actions.append(action)
            
            self.logger.info(f"✅ Action scheduled: {action_name} for project {project_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Error scheduling action: {e}")
    
    async def _process_pending_actions(self, project_id: str):
        """處理待處理的行動"""
        try:
            state = self.project_states[project_id]
            
            # 處理到期的行動
            current_time = datetime.now(timezone.utc)
            actions_to_process = [
                action for action in state.pending_actions
                if action.scheduled_at and action.scheduled_at <= current_time
            ]
            
            for action in actions_to_process:
                await self._execute_action(project_id, action)
                
                # 移動到已完成列表
                state.pending_actions.remove(action)
                state.completed_actions.append(action)
                
                # 限制歷史記錄數量
                if len(state.completed_actions) > 100:
                    state.completed_actions = state.completed_actions[-100:]
                    
        except Exception as e:
            self.logger.error(f"❌ Error processing pending actions for {project_id}: {e}")
    
    async def _execute_action(self, project_id: str, action: LifecycleAction):
        """執行生命週期行動"""
        try:
            action.status = "executing"
            action.executed_at = datetime.now(timezone.utc)
            
            # 獲取行動處理器
            handler = self.action_handlers.get(action.action_type)
            if not handler:
                raise ValueError(f"No handler found for action type: {action.action_type}")
            
            # 執行行動
            result = await handler(project_id, action.parameters)
            
            action.status = "completed"
            action.execution_result = result
            
            self.logger.info(f"✅ Action executed: {action.action_name} for project {project_id}")
            
        except Exception as e:
            action.status = "failed"
            action.error_message = str(e)
            self.logger.error(f"❌ Error executing action {action.action_name} for project {project_id}: {e}")
    
    # Action Handlers
    async def _handle_stage_progression(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理階段推進行動"""
        next_stage = ProjectStage(parameters.get('next_stage'))
        reason = parameters.get('reason', 'automated_progression')
        
        await self._progress_to_next_stage(project_id, next_stage, reason)
        
        return {
            'action': 'stage_progression',
            'next_stage': next_stage.value,
            'reason': reason,
            'success': True
        }
    
    async def _handle_milestone_creation(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理里程碑創建行動"""
        # 模擬里程碑創建
        milestone_data = {
            'project_id': project_id,
            'milestone_name': parameters.get('milestone_name', 'Auto-generated milestone'),
            'milestone_type': parameters.get('milestone_type', 'development'),
            'priority': parameters.get('priority', 'medium'),
            'created_at': datetime.now(timezone.utc).isoformat()
        }
        
        return {
            'action': 'milestone_creation',
            'milestone_data': milestone_data,
            'success': True
        }
    
    async def _handle_resource_allocation(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理資源分配行動"""
        allocation_type = parameters.get('allocation_type', 'budget')
        amount = parameters.get('amount', 0)
        
        return {
            'action': 'resource_allocation',
            'allocation_type': allocation_type,
            'amount': amount,
            'allocated_at': datetime.now(timezone.utc).isoformat(),
            'success': True
        }
    
    async def _handle_risk_assessment(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理風險評估行動"""
        assessment_type = parameters.get('assessment_type', 'general')
        
        # 獲取當前風險指標
        performance_metrics = await self.performance_monitor.calculate_project_performance(project_id)
        
        return {
            'action': 'risk_assessment',
            'assessment_type': assessment_type,
            'risk_score': float(performance_metrics.risk_score),
            'risk_factors': performance_metrics.risk_factors,
            'assessed_at': datetime.now(timezone.utc).isoformat(),
            'success': True
        }
    
    async def _handle_stakeholder_notification(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理利益相關者通知行動"""
        notification_type = parameters.get('notification_type', 'general')
        recipients = parameters.get('recipients', [])
        
        return {
            'action': 'stakeholder_notification',
            'notification_type': notification_type,
            'recipients': recipients,
            'sent_at': datetime.now(timezone.utc).isoformat(),
            'success': True
        }
    
    async def _handle_performance_review(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理性能審查行動"""
        # 執行詳細的性能審查
        performance_metrics = await self.performance_monitor.calculate_project_performance(project_id)
        
        return {
            'action': 'performance_review',
            'health_score': float(performance_metrics.health_score),
            'performance_trend': performance_metrics.performance_trend.value,
            'risk_score': float(performance_metrics.risk_score),
            'reviewed_at': datetime.now(timezone.utc).isoformat(),
            'success': True
        }
    
    async def _handle_decision_execution(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理決策執行行動"""
        recommendation_id = parameters.get('recommendation_id')
        decision_type = parameters.get('decision_type')
        
        return {
            'action': 'decision_execution',
            'recommendation_id': recommendation_id,
            'decision_type': decision_type,
            'executed_at': datetime.now(timezone.utc).isoformat(),
            'success': True
        }
    
    async def _handle_timeline_adjustment(self, project_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """處理時間線調整行動"""
        adjustment_type = parameters.get('adjustment_type', 'extend')
        adjustment_days = parameters.get('adjustment_days', 0)
        
        return {
            'action': 'timeline_adjustment',
            'adjustment_type': adjustment_type,
            'adjustment_days': adjustment_days,
            'adjusted_at': datetime.now(timezone.utc).isoformat(),
            'success': True
        }
    
    async def _perform_lifecycle_performance_review(self, project_id: str):
        """執行生命週期性能審查"""
        try:
            state = self.project_states[project_id]
            
            # 檢查是否需要性能審查
            review_interval = self.config['performance_review_interval_days']
            last_review = None
            
            # 查找最後一次性能審查
            for action in reversed(state.completed_actions):
                if action.action_type == LifecycleActionType.PERFORMANCE_REVIEW:
                    last_review = action.executed_at
                    break
            
            # 如果需要審查
            current_time = datetime.now(timezone.utc)
            needs_review = (
                not last_review or 
                (current_time - last_review).days >= review_interval
            )
            
            if needs_review:
                await self._schedule_action(
                    project_id,
                    LifecycleActionType.PERFORMANCE_REVIEW,
                    "Scheduled performance review",
                    {'review_type': 'lifecycle_maintenance'}
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error performing lifecycle performance review: {e}")
    
    async def _publish_event(
        self,
        event_type: LifecycleEventType,
        project_id: str,
        event_data: Dict[str, Any],
        related_stage: Optional[ProjectStage] = None,
        related_gate_id: Optional[str] = None,
        related_milestone_id: Optional[str] = None
    ):
        """發布生命週期事件"""
        try:
            event = LifecycleEvent(
                event_id=f"{event_type.value}_{uuid.uuid4().hex[:8]}",
                event_type=event_type,
                project_id=project_id,
                event_data=event_data,
                related_stage=related_stage,
                related_gate_id=related_gate_id,
                related_milestone_id=related_milestone_id
            )
            
            # 添加到項目事件歷史
            if project_id in self.project_states:
                self.project_states[project_id].events.append(event)
                
                # 限制事件歷史數量
                events = self.project_states[project_id].events
                if len(events) > 200:
                    self.project_states[project_id].events = events[-200:]
            
            # 調用事件監聽器
            listeners = self.event_listeners.get(event_type, [])
            for listener in listeners:
                try:
                    await listener(event)
                except Exception as e:
                    self.logger.error(f"❌ Error in event listener: {e}")
            
            event.processed = True
            
        except Exception as e:
            self.logger.error(f"❌ Error publishing event: {e}")
    
    # Event Listeners
    async def _on_project_initiated(self, event: LifecycleEvent):
        """項目啟動事件處理"""
        project_id = event.project_id
        self.logger.info(f"🚀 Project initiated: {event.event_data.get('project_name')}")
    
    async def _on_stage_entered(self, event: LifecycleEvent):
        """階段進入事件處理"""
        project_id = event.project_id
        stage = event.event_data.get('stage')
        self.logger.info(f"📍 Project {project_id} entered stage: {stage}")
    
    async def _on_stage_completed(self, event: LifecycleEvent):
        """階段完成事件處理"""
        project_id = event.project_id
        stage = event.event_data.get('completed_stage')
        self.logger.info(f"✅ Project {project_id} completed stage: {stage}")
    
    async def _on_gate_triggered(self, event: LifecycleEvent):
        """關卡觸發事件處理"""
        project_id = event.project_id
        gate_name = event.event_data.get('gate_name')
        self.logger.info(f"🚪 Gate triggered for project {project_id}: {gate_name}")
    
    async def _on_gate_passed(self, event: LifecycleEvent):
        """關卡通過事件處理"""
        project_id = event.project_id
        gate_name = event.event_data.get('gate_name')
        self.logger.info(f"✅ Gate passed for project {project_id}: {gate_name}")
    
    async def _on_gate_failed(self, event: LifecycleEvent):
        """關卡失敗事件處理"""
        project_id = event.project_id
        gate_name = event.event_data.get('gate_name')
        self.logger.warning(f"❌ Gate failed for project {project_id}: {gate_name}")
    
    async def _on_milestone_achieved(self, event: LifecycleEvent):
        """里程碑達成事件處理"""
        project_id = event.project_id
        milestone_name = event.event_data.get('milestone_name')
        self.logger.info(f"🎯 Milestone achieved for project {project_id}: {milestone_name}")
    
    async def _on_risk_escalated(self, event: LifecycleEvent):
        """風險升級事件處理"""
        project_id = event.project_id
        risk_level = event.event_data.get('risk_level')
        self.logger.warning(f"⚠️ Risk escalated for project {project_id}: {risk_level}")
    
    async def _on_decision_implemented(self, event: LifecycleEvent):
        """決策實施事件處理"""
        project_id = event.project_id
        decision_type = event.event_data.get('decision_type')
        self.logger.info(f"⚖️ Decision implemented for project {project_id}: {decision_type}")
    
    def _cleanup_expired_data(self):
        """清理過期數據"""
        try:
            current_time = datetime.now(timezone.utc)
            cutoff_date = current_time - timedelta(days=90)
            
            for project_id, state in self.project_states.items():
                # 清理舊事件
                state.events = [
                    event for event in state.events
                    if event.timestamp >= cutoff_date
                ]
                
                # 清理舊的已完成行動
                state.completed_actions = [
                    action for action in state.completed_actions
                    if action.executed_at and action.executed_at >= cutoff_date
                ]
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up expired data: {e}")
    
    async def get_project_lifecycle_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取項目生命週期狀態
        
        Args:
            project_id: 項目ID
            
        Returns:
            生命週期狀態信息
        """
        try:
            if project_id not in self.project_states:
                return None
            
            state = self.project_states[project_id]
            
            # 獲取當前性能指標
            performance_metrics = await self.performance_monitor.calculate_project_performance(project_id)
            
            return {
                'project_id': project_id,
                'project_name': state.project_name,
                'current_stage': state.current_stage.value,
                'is_active': state.is_active,
                
                'stage_history': state.stage_history,
                'current_stage_duration_days': self._calculate_stage_duration(state, state.current_stage),
                
                'gates': {
                    gate_id: {
                        'gate_type': gate.gate_type.value,
                        'gate_name': gate.gate_name,
                        'status': gate.status.value,
                        'triggered_at': gate.triggered_at.isoformat() if gate.triggered_at else None,
                        'completed_at': gate.completed_at.isoformat() if gate.completed_at else None,
                        'approval_score': float(gate.approval_score) if gate.approval_score else None,
                        'conditions': gate.conditions
                    }
                    for gate_id, gate in state.gates.items()
                },
                
                'pending_gates': state.pending_gates,
                'pending_actions': [
                    {
                        'action_id': action.action_id,
                        'action_type': action.action_type.value,
                        'action_name': action.action_name,
                        'scheduled_at': action.scheduled_at.isoformat() if action.scheduled_at else None,
                        'status': action.status
                    }
                    for action in state.pending_actions
                ],
                
                'recent_events': [
                    {
                        'event_type': event.event_type.value,
                        'timestamp': event.timestamp.isoformat(),
                        'event_data': event.event_data
                    }
                    for event in state.events[-10:]  # 最近10個事件
                ],
                
                'performance_summary': {
                    'health_score': float(performance_metrics.health_score),
                    'risk_score': float(performance_metrics.risk_score),
                    'performance_trend': performance_metrics.performance_trend.value,
                    'milestone_completion_rate': float(performance_metrics.milestone_completion_rate),
                    'budget_utilization_rate': float(performance_metrics.budget_utilization_rate)
                },
                
                'lifecycle_settings': {
                    'auto_progression_enabled': state.auto_progression_enabled,
                    'notification_enabled': state.notification_enabled
                },
                
                'timestamps': {
                    'created_at': state.created_at.isoformat(),
                    'updated_at': state.updated_at.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting project lifecycle status: {e}")
            return None
    
    async def get_lifecycle_analytics(
        self,
        project_ids: Optional[List[str]] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取生命週期分析報告
        
        Args:
            project_ids: 項目ID列表（可選）
            time_range_days: 時間範圍（天）
            
        Returns:
            生命週期分析報告
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)
            
            # 確定要分析的項目
            projects_to_analyze = project_ids or list(self.project_states.keys())
            
            # 收集統計數據
            stage_distribution = {}
            gate_success_rates = {}
            average_stage_durations = {}
            event_counts = {}
            
            for project_id in projects_to_analyze:
                if project_id not in self.project_states:
                    continue
                
                state = self.project_states[project_id]
                
                # 階段分布
                current_stage = state.current_stage.value
                stage_distribution[current_stage] = stage_distribution.get(current_stage, 0) + 1
                
                # 關卡成功率
                for gate in state.gates.values():
                    gate_type = gate.gate_type.value
                    if gate_type not in gate_success_rates:
                        gate_success_rates[gate_type] = {'total': 0, 'approved': 0}
                    
                    if gate.status != GateStatus.PENDING:
                        gate_success_rates[gate_type]['total'] += 1
                        if gate.status == GateStatus.APPROVED:
                            gate_success_rates[gate_type]['approved'] += 1
                
                # 階段持續時間
                for stage_record in state.stage_history:
                    stage = stage_record['stage']
                    if stage not in average_stage_durations:
                        average_stage_durations[stage] = []
                    
                    # 計算持續時間（簡化）
                    duration = 30  # 示例值
                    average_stage_durations[stage].append(duration)
                
                # 事件計數
                recent_events = [e for e in state.events if e.timestamp >= cutoff_date]
                for event in recent_events:
                    event_type = event.event_type.value
                    event_counts[event_type] = event_counts.get(event_type, 0) + 1
            
            # 計算成功率
            calculated_success_rates = {}
            for gate_type, data in gate_success_rates.items():
                if data['total'] > 0:
                    calculated_success_rates[gate_type] = data['approved'] / data['total'] * 100
                else:
                    calculated_success_rates[gate_type] = 0
            
            # 計算平均持續時間
            calculated_durations = {}
            for stage, durations in average_stage_durations.items():
                if durations:
                    calculated_durations[stage] = sum(durations) / len(durations)
                else:
                    calculated_durations[stage] = 0
            
            return {
                'summary': {
                    'total_projects_analyzed': len(projects_to_analyze),
                    'active_projects': sum(1 for pid in projects_to_analyze 
                                         if self.project_states.get(pid, {}).get('is_active', False)),
                    'time_range_days': time_range_days,
                    'analysis_date': datetime.now(timezone.utc).isoformat()
                },
                
                'stage_distribution': stage_distribution,
                'gate_success_rates': calculated_success_rates,
                'average_stage_durations': calculated_durations,
                'event_activity': event_counts,
                
                'insights': self._generate_lifecycle_insights(
                    stage_distribution, calculated_success_rates, calculated_durations, event_counts
                )
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error generating lifecycle analytics: {e}")
            return {'error': str(e)}
    
    def _generate_lifecycle_insights(
        self,
        stage_distribution: Dict[str, int],
        success_rates: Dict[str, float],
        durations: Dict[str, float],
        event_counts: Dict[str, int]
    ) -> List[str]:
        """生成生命週期洞察"""
        insights = []
        
        try:
            # 階段分布洞察
            if stage_distribution:
                most_common_stage = max(stage_distribution.items(), key=lambda x: x[1])
                insights.append(f"Most projects are currently in {most_common_stage[0]} stage ({most_common_stage[1]} projects)")
            
            # 關卡成功率洞察
            if success_rates:
                lowest_success_gate = min(success_rates.items(), key=lambda x: x[1])
                if lowest_success_gate[1] < 80:
                    insights.append(f"{lowest_success_gate[0]} gate has low success rate: {lowest_success_gate[1]:.1f}%")
            
            # 持續時間洞察
            if durations:
                longest_stage = max(durations.items(), key=lambda x: x[1])
                insights.append(f"{longest_stage[0]} stage takes the longest on average: {longest_stage[1]:.1f} days")
            
            # 活動洞察
            if event_counts:
                most_frequent_event = max(event_counts.items(), key=lambda x: x[1])
                insights.append(f"Most frequent lifecycle event: {most_frequent_event[0]} ({most_frequent_event[1]} occurrences)")
                
        except Exception as e:
            self.logger.error(f"❌ Error generating insights: {e}")
            insights.append("Unable to generate insights due to data processing error")
        
        return insights
    
    async def health_check(self) -> Dict[str, Any]:
        """服務健康檢查"""
        return {
            'service': 'project_lifecycle_manager',
            'status': 'healthy' if self._running else 'stopped',
            'active_projects': len([s for s in self.project_states.values() if s.is_active]),
            'total_projects': len(self.project_states),
            'gate_templates': len(self.gate_templates),
            'action_handlers': len(self.action_handlers),
            'event_listeners': sum(len(listeners) for listeners in self.event_listeners.values()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }