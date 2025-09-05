#!/usr/bin/env python3
"""
Innovation Zone Management Service
創新特區管理服務

GPT-OSS整合任務2.2.1 - 創新特區機制核心服務
提供創新特區的完整管理功能，包括：
- 創新項目准入評估和生命週期管理
- 預算分配和ROI豁免機制管理
- 技術里程碑追蹤和用戶行為分析
- 異常檢測和預警系統
- 創新項目績效評估和優化建議
"""

import asyncio
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
import uuid
import statistics
from dataclasses import dataclass, asdict

from .models import (
    InnovationType, ProjectStage, ROIExemptionStatus, MilestoneType,
    AnomalyType, AdmissionCriteria, InnovationZoneCreate, InnovationProjectCreate,
    TechnicalMilestoneCreate, UserBehaviorMetricsCreate, AnomalyDetectionCreate,
    InnovationAnalyticsRequest, InnovationAnalyticsResponse
)
from .innovation_zone_db import InnovationZoneDB, InnovationZoneDBError
from .milestone_tracker import TechnicalMilestoneTracker
from .project_admission_evaluator import ProjectAdmissionEvaluator
from .budget_roi_manager import BudgetROIManager
from .anomaly_detector import InnovationAnomalyDetector

logger = logging.getLogger(__name__)

@dataclass
class InnovationProjectHealthScore:
    """創新項目健康評分"""
    project_id: uuid.UUID
    overall_score: float
    budget_health_score: float
    milestone_progress_score: float
    user_engagement_score: float
    risk_score: float
    recommendations: List[str]
    calculated_at: datetime

@dataclass
class ROIExemptionReview:
    """ROI豁免審查"""
    project_id: uuid.UUID
    current_status: str
    exemption_remaining_days: int
    should_continue_exemption: bool
    transition_recommendation: str
    key_metrics_summary: Dict[str, Any]
    review_date: datetime

class InnovationZoneService:
    """
    創新特區管理服務
    
    功能：
    1. 創新特區和項目的全生命週期管理
    2. 預算分配和ROI豁免機制
    3. 技術里程碑和用戶行為追蹤
    4. 智能異常檢測和預警
    5. 項目健康評估和優化建議
    6. 創新績效分析和報告
    """
    
    def __init__(self):
        """初始化創新特區管理服務"""
        self.logger = logger
        
        # 核心組件
        self.innovation_db = InnovationZoneDB()
        self.milestone_tracker = TechnicalMilestoneTracker()
        self.admission_evaluator = ProjectAdmissionEvaluator()
        self.budget_roi_manager = BudgetROIManager()
        self.anomaly_detector = InnovationAnomalyDetector()
        
        # 服務配置
        self.config = {
            'default_roi_exemption_quarters': 4,
            'minimum_admission_score_threshold': 75.0,
            'budget_overrun_alert_threshold': 0.85,
            'milestone_delay_alert_days': 14,
            'user_engagement_decline_threshold': 0.20,
            'health_check_interval_days': 30,
            'anomaly_confidence_threshold': 80.0
        }
        
        # 性能監控
        self.performance_metrics = {
            'projects_created': 0,
            'milestones_tracked': 0,
            'anomalies_detected': 0,
            'budgets_allocated': 0
        }
        
        self.logger.info("✅ Innovation Zone Management Service initialized")
    
    # ==================== 創新特區管理 ====================
    
    async def create_innovation_zone(
        self,
        zone_request: InnovationZoneCreate
    ) -> Dict[str, Any]:
        """創建創新特區"""
        try:
            # 驗證請求數據
            zone_data = zone_request.dict()
            
            # 設置預設值
            zone_data.update({
                'established_date': date.today(),
                'is_active': True
            })
            
            # 創建創新特區
            zone = await self.innovation_db.create_innovation_zone(zone_data)
            
            # 初始化預算分配
            await self._initialize_zone_budget(zone['id'], zone_data)
            
            self.logger.info(f"✅ Created innovation zone: {zone['zone_name']}")
            
            return {
                'success': True,
                'innovation_zone': zone,
                'message': f"Innovation zone '{zone['zone_name']}' created successfully"
            }
            
        except InnovationZoneDBError as e:
            self.logger.error(f"❌ Database error creating innovation zone: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to create innovation zone due to database error"
            }
        except Exception as e:
            self.logger.error(f"❌ Error creating innovation zone: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to create innovation zone"
            }
    
    async def evaluate_and_admit_project(
        self,
        project_request: InnovationProjectCreate,
        evaluation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """評估並准入創新項目"""
        try:
            # 獲取創新特區信息
            zone = await self.innovation_db.get_innovation_zone(
                project_request.innovation_zone_id
            )
            
            if not zone:
                return {
                    'success': False,
                    'error': 'Innovation zone not found',
                    'message': f"Zone {project_request.innovation_zone_id} does not exist"
                }
            
            # 執行准入評估
            admission_result = await self.admission_evaluator.evaluate_project_admission(
                project_data=project_request.dict(),
                zone_criteria=zone['admission_criteria_weights'],
                evaluation_data=evaluation_data,
                minimum_score=float(zone['minimum_admission_score'])
            )
            
            if not admission_result['passed']:
                return {
                    'success': False,
                    'admission_result': admission_result,
                    'message': f"Project failed admission with score {admission_result['total_score']:.2f}"
                }
            
            # 創建項目
            project_data = project_request.dict()
            project = await self.innovation_db.create_innovation_project(
                project_data,
                admission_result['criteria_scores']
            )
            
            # 設置初始預算
            await self._setup_project_initial_budget(project['id'], zone['id'])
            
            # 創建初始里程碑
            await self._create_initial_milestones(project['id'], project_data)
            
            self.performance_metrics['projects_created'] += 1
            
            self.logger.info(f"✅ Admitted project: {project['project_name']}")
            
            return {
                'success': True,
                'innovation_project': project,
                'admission_result': admission_result,
                'message': f"Project '{project['project_name']}' admitted successfully"
            }
            
        except InnovationZoneDBError as e:
            self.logger.error(f"❌ Database error admitting project: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to admit project due to database error"
            }
        except Exception as e:
            self.logger.error(f"❌ Error admitting project: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to admit project"
            }
    
    # ==================== 項目生命週期管理 ====================
    
    async def advance_project_stage(
        self,
        project_id: uuid.UUID,
        new_stage: ProjectStage,
        justification: str,
        updated_by: str
    ) -> Dict[str, Any]:
        """推進項目階段"""
        try:
            # 獲取當前項目狀態
            project = await self.innovation_db.get_innovation_project(
                project_id,
                include_milestones=True,
                include_budget=True,
                include_metrics=True
            )
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found',
                    'message': f"Project {project_id} does not exist"
                }
            
            # 驗證階段轉換的合理性
            stage_validation = await self._validate_stage_transition(
                project, new_stage, justification
            )
            
            if not stage_validation['valid']:
                return {
                    'success': False,
                    'validation_result': stage_validation,
                    'message': f"Stage transition not valid: {stage_validation['reason']}"
                }
            
            # 執行階段轉換
            updated_project = await self.innovation_db.update_project_stage(
                project_id, new_stage, updated_by, justification
            )
            
            # 處理階段轉換的後續操作
            await self._handle_stage_transition_actions(
                project_id, project['current_stage'], new_stage.value
            )
            
            self.logger.info(
                f"✅ Advanced project stage: {project['project_name']} "
                f"from {project['current_stage']} to {new_stage.value}"
            )
            
            return {
                'success': True,
                'updated_project': updated_project,
                'stage_validation': stage_validation,
                'message': f"Project advanced to {new_stage.value} stage"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error advancing project stage {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to advance project stage"
            }
    
    async def update_milestone_progress(
        self,
        milestone_id: uuid.UUID,
        progress_data: Dict[str, Any],
        updated_by: str
    ) -> Dict[str, Any]:
        """更新里程碑進度"""
        try:
            # 更新里程碑
            milestone = await self.milestone_tracker.update_milestone_progress(
                milestone_id,
                progress_data.get('completion_rate', 0),
                progress_data.get('technical_metrics', {}),
                progress_data.get('quality_metrics', {}),
                updated_by
            )
            
            self.performance_metrics['milestones_tracked'] += 1
            
            # 檢查是否觸發異常
            await self._check_milestone_anomalies(milestone)
            
            # 更新項目整體進度
            await self._update_project_progress(milestone['innovation_project_id'])
            
            self.logger.info(f"✅ Updated milestone progress: {milestone['milestone_name']}")
            
            return {
                'success': True,
                'milestone': milestone,
                'message': f"Milestone progress updated to {progress_data.get('completion_rate', 0)}%"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error updating milestone progress {milestone_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to update milestone progress"
            }
    
    # ==================== 預算和ROI管理 ====================
    
    async def allocate_budget_to_project(
        self,
        project_id: uuid.UUID,
        budget_amount: Decimal,
        budget_category: str,
        allocation_justification: str,
        allocated_by: str
    ) -> Dict[str, Any]:
        """為項目分配預算"""
        try:
            # 執行預算分配
            allocation_result = await self.budget_roi_manager.allocate_project_budget(
                project_id,
                float(budget_amount),
                budget_category,
                allocation_justification,
                allocated_by
            )
            
            if not allocation_result['success']:
                return allocation_result
            
            # 記錄預算分配
            await self.innovation_db.track_budget_expense({
                'innovation_project_id': project_id,
                'transaction_date': date.today(),
                'transaction_type': 'allocation',
                'amount': budget_amount,
                'currency': 'USD',
                'expense_category': budget_category,
                'description': f"Budget allocation: {allocation_justification}",
                'created_by': allocated_by
            })
            
            self.performance_metrics['budgets_allocated'] += 1
            
            self.logger.info(f"✅ Allocated budget {budget_amount} to project {project_id}")
            
            return {
                'success': True,
                'allocation_result': allocation_result,
                'message': f"Successfully allocated {budget_amount} to {budget_category}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error allocating budget to project {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to allocate budget"
            }
    
    async def review_roi_exemption_status(
        self,
        project_id: uuid.UUID
    ) -> ROIExemptionReview:
        """審查ROI豁免狀態"""
        try:
            # 獲取項目信息
            project = await self.innovation_db.get_innovation_project(
                project_id,
                include_milestones=True,
                include_budget=True,
                include_metrics=True
            )
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # 計算豁免剩餘天數
            exemption_end = project.get('roi_exemption_end_date')
            remaining_days = 0
            if exemption_end:
                remaining_days = (exemption_end - date.today()).days
            
            # 評估是否應繼續豁免
            exemption_evaluation = await self.budget_roi_manager.evaluate_roi_exemption_continuation(
                project_id
            )
            
            # 生成關鍵指標摘要
            metrics_summary = await self._generate_roi_metrics_summary(project)
            
            review = ROIExemptionReview(
                project_id=project_id,
                current_status=project['roi_exemption_status'],
                exemption_remaining_days=max(0, remaining_days),
                should_continue_exemption=exemption_evaluation['should_continue'],
                transition_recommendation=exemption_evaluation['recommendation'],
                key_metrics_summary=metrics_summary,
                review_date=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"✅ Reviewed ROI exemption for project {project_id}")
            return review
            
        except Exception as e:
            self.logger.error(f"❌ Error reviewing ROI exemption {project_id}: {e}")
            raise
    
    # ==================== 用戶行為追蹤 ====================
    
    async def record_user_behavior_metrics(
        self,
        metrics_request: UserBehaviorMetricsCreate
    ) -> Dict[str, Any]:
        """記錄用戶行為指標"""
        try:
            # 記錄指標
            metrics = await self.innovation_db.record_user_behavior_metrics(
                metrics_request.dict()
            )
            
            # 分析用戶行為趨勢
            await self._analyze_user_behavior_trends(
                metrics_request.innovation_project_id,
                metrics
            )
            
            # 檢查用戶參與異常
            await self._check_user_engagement_anomalies(metrics)
            
            self.logger.info(
                f"✅ Recorded user behavior metrics for project "
                f"{metrics_request.innovation_project_id}"
            )
            
            return {
                'success': True,
                'metrics': metrics,
                'message': "User behavior metrics recorded successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error recording user behavior metrics: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to record user behavior metrics"
            }
    
    # ==================== 異常檢測和預警 ====================
    
    async def detect_project_anomalies(
        self,
        project_id: uuid.UUID,
        detection_scope: List[str] = None
    ) -> Dict[str, Any]:
        """檢測項目異常"""
        try:
            if detection_scope is None:
                detection_scope = ['budget', 'milestones', 'user_engagement', 'team_performance']
            
            # 獲取項目完整數據
            project = await self.innovation_db.get_innovation_project(
                project_id,
                include_milestones=True,
                include_budget=True,
                include_metrics=True
            )
            
            if not project:
                return {
                    'success': False,
                    'error': 'Project not found',
                    'message': f"Project {project_id} does not exist"
                }
            
            detected_anomalies = []
            
            # 預算異常檢測
            if 'budget' in detection_scope:
                budget_anomalies = await self.anomaly_detector.detect_budget_anomalies(project)
                detected_anomalies.extend(budget_anomalies)
            
            # 里程碑異常檢測
            if 'milestones' in detection_scope:
                milestone_anomalies = await self.anomaly_detector.detect_milestone_anomalies(project)
                detected_anomalies.extend(milestone_anomalies)
            
            # 用戶參與異常檢測
            if 'user_engagement' in detection_scope:
                engagement_anomalies = await self.anomaly_detector.detect_user_engagement_anomalies(project)
                detected_anomalies.extend(engagement_anomalies)
            
            # 保存檢測到的異常
            for anomaly in detected_anomalies:
                await self.innovation_db.create_anomaly_detection(anomaly)
            
            self.performance_metrics['anomalies_detected'] += len(detected_anomalies)
            
            self.logger.info(
                f"✅ Detected {len(detected_anomalies)} anomalies for project {project_id}"
            )
            
            return {
                'success': True,
                'project_id': project_id,
                'anomalies_detected': len(detected_anomalies),
                'anomalies': detected_anomalies,
                'detection_scope': detection_scope,
                'message': f"Anomaly detection completed, found {len(detected_anomalies)} anomalies"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting project anomalies {project_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to detect project anomalies"
            }
    
    async def resolve_anomaly(
        self,
        anomaly_id: uuid.UUID,
        resolution_plan: Dict[str, Any],
        resolved_by: str
    ) -> Dict[str, Any]:
        """解決異常"""
        try:
            # 執行異常解決
            resolved_anomaly = await self.innovation_db.resolve_anomaly(
                anomaly_id,
                resolution_plan.get('actions', []),
                resolved_by,
                resolution_plan.get('notes')
            )
            
            # 實施預防措施
            if resolution_plan.get('prevention_measures'):
                await self._implement_prevention_measures(
                    resolved_anomaly['innovation_project_id'],
                    resolution_plan['prevention_measures']
                )
            
            self.logger.info(f"✅ Resolved anomaly {anomaly_id}")
            
            return {
                'success': True,
                'resolved_anomaly': resolved_anomaly,
                'message': "Anomaly resolved successfully"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error resolving anomaly {anomaly_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': "Failed to resolve anomaly"
            }
    
    # ==================== 項目健康評估 ====================
    
    async def assess_project_health(
        self,
        project_id: uuid.UUID
    ) -> InnovationProjectHealthScore:
        """評估項目健康狀況"""
        try:
            # 獲取項目完整數據
            project = await self.innovation_db.get_innovation_project(
                project_id,
                include_milestones=True,
                include_budget=True,
                include_metrics=True
            )
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # 計算各項健康分數
            budget_score = await self._calculate_budget_health_score(project)
            milestone_score = await self._calculate_milestone_progress_score(project)
            engagement_score = await self._calculate_user_engagement_score(project)
            risk_score = await self._calculate_risk_score(project)
            
            # 計算總體健康分數
            overall_score = (
                budget_score * 0.25 +
                milestone_score * 0.30 +
                engagement_score * 0.25 +
                (100 - risk_score) * 0.20  # 風險分數越低越好
            )
            
            # 生成改進建議
            recommendations = await self._generate_health_recommendations(
                project, budget_score, milestone_score, engagement_score, risk_score
            )
            
            health_score = InnovationProjectHealthScore(
                project_id=project_id,
                overall_score=overall_score,
                budget_health_score=budget_score,
                milestone_progress_score=milestone_score,
                user_engagement_score=engagement_score,
                risk_score=risk_score,
                recommendations=recommendations,
                calculated_at=datetime.now(timezone.utc)
            )
            
            self.logger.info(f"✅ Assessed project health: {project_id} - Score: {overall_score:.2f}")
            return health_score
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing project health {project_id}: {e}")
            raise
    
    # ==================== 分析和報告 ====================
    
    async def generate_innovation_analytics(
        self,
        request: InnovationAnalyticsRequest
    ) -> InnovationAnalyticsResponse:
        """生成創新分析報告"""
        try:
            # 獲取基礎分析數據
            analytics_data = await self.innovation_db.get_innovation_analytics(
                zone_ids=request.innovation_zone_ids,
                start_date=request.start_date,
                end_date=request.end_date
            )
            
            # 增強分析數據
            enhanced_analytics = await self._enhance_analytics_data(
                analytics_data, request
            )
            
            # 生成洞察和建議
            insights = await self._generate_innovation_insights(enhanced_analytics)
            
            response = InnovationAnalyticsResponse(
                analysis_id=uuid.uuid4(),
                analysis_date=datetime.now(timezone.utc),
                analysis_period=f"{request.start_date} to {request.end_date}",
                **enhanced_analytics,
                innovation_trends=insights['trends'],
                recommendations=insights['recommendations']
            )
            
            self.logger.info("✅ Generated innovation analytics report")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error generating innovation analytics: {e}")
            raise
    
    # ==================== 輔助方法 ====================
    
    async def _initialize_zone_budget(
        self,
        zone_id: uuid.UUID,
        zone_data: Dict[str, Any]
    ):
        """初始化特區預算"""
        try:
            current_year = date.today().year
            current_quarter = (date.today().month - 1) // 3 + 1
            
            quarterly_budget = zone_data['total_budget_allocation'] / 4
            
            await self.innovation_db.allocate_budget({
                'innovation_zone_id': zone_id,
                'fiscal_year': current_year,
                'quarter': current_quarter,
                'total_allocated_budget': quarterly_budget,
                'allocated_budget': quarterly_budget,
                'remaining_budget': quarterly_budget,
                'created_by': 'system'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing zone budget: {e}")
    
    async def _setup_project_initial_budget(
        self,
        project_id: uuid.UUID,
        zone_id: uuid.UUID
    ):
        """設置項目初始預算"""
        try:
            # 從特區預算中分配初始項目預算
            initial_budget = Decimal('10000')  # 預設初始預算
            
            await self.innovation_db.track_budget_expense({
                'innovation_project_id': project_id,
                'transaction_date': date.today(),
                'transaction_type': 'allocation',
                'amount': initial_budget,
                'currency': 'USD',
                'expense_category': 'initial_allocation',
                'description': 'Initial project budget allocation',
                'created_by': 'system'
            })
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up project initial budget: {e}")
    
    async def _create_initial_milestones(
        self,
        project_id: uuid.UUID,
        project_data: Dict[str, Any]
    ):
        """創建初始里程碑"""
        try:
            start_date = project_data['start_date']
            
            # 創建標準里程碑
            initial_milestones = [
                {
                    'milestone_name': 'Project Kickoff',
                    'milestone_type': MilestoneType.TECHNICAL.value,
                    'planned_date': start_date,
                    'milestone_description': 'Project officially starts with team formation and initial planning'
                },
                {
                    'milestone_name': 'Proof of Concept',
                    'milestone_type': MilestoneType.TECHNICAL.value,
                    'planned_date': start_date + timedelta(days=30),
                    'milestone_description': 'Basic proof of concept demonstrating core functionality'
                },
                {
                    'milestone_name': 'User Feedback Collection',
                    'milestone_type': MilestoneType.USER_ADOPTION.value,
                    'planned_date': start_date + timedelta(days=60),
                    'milestone_description': 'Collect and analyze initial user feedback'
                }
            ]
            
            for milestone_data in initial_milestones:
                milestone_data.update({
                    'innovation_project_id': project_id,
                    'technical_metrics': {'completion_target': 100},
                    'success_criteria': {'basic_functionality': True},
                    'created_by': 'system'
                })
                
                await self.innovation_db.create_milestone(milestone_data)
                
        except Exception as e:
            self.logger.error(f"❌ Error creating initial milestones: {e}")
    
    async def _validate_stage_transition(
        self,
        project: Dict[str, Any],
        new_stage: ProjectStage,
        justification: str
    ) -> Dict[str, Any]:
        """驗證階段轉換"""
        current_stage = ProjectStage(project['current_stage'])
        
        # 定義有效的階段轉換
        valid_transitions = {
            ProjectStage.CONCEPT: [ProjectStage.FEASIBILITY, ProjectStage.DISCONTINUED],
            ProjectStage.FEASIBILITY: [ProjectStage.PROTOTYPE, ProjectStage.CONCEPT, ProjectStage.DISCONTINUED],
            ProjectStage.PROTOTYPE: [ProjectStage.PILOT, ProjectStage.FEASIBILITY, ProjectStage.DISCONTINUED],
            ProjectStage.PILOT: [ProjectStage.SCALING, ProjectStage.PROTOTYPE, ProjectStage.DISCONTINUED],
            ProjectStage.SCALING: [ProjectStage.MATURE, ProjectStage.PILOT],
            ProjectStage.MATURE: [ProjectStage.DISCONTINUED],
            ProjectStage.DISCONTINUED: []
        }
        
        if new_stage not in valid_transitions.get(current_stage, []):
            return {
                'valid': False,
                'reason': f"Cannot transition from {current_stage.value} to {new_stage.value}",
                'allowed_transitions': [s.value for s in valid_transitions.get(current_stage, [])]
            }
        
        # 檢查是否有足夠的進展支持轉換
        if new_stage in [ProjectStage.PILOT, ProjectStage.SCALING, ProjectStage.MATURE]:
            milestone_completion_rate = self._calculate_milestone_completion_rate(project)
            if milestone_completion_rate < 0.8:  # 80% 里程碑完成率
                return {
                    'valid': False,
                    'reason': f"Insufficient milestone completion ({milestone_completion_rate:.1%}) for stage transition",
                    'required_completion_rate': 0.8
                }
        
        return {
            'valid': True,
            'reason': 'Stage transition validated successfully',
            'justification': justification
        }
    
    def _calculate_milestone_completion_rate(self, project: Dict[str, Any]) -> float:
        """計算里程碑完成率"""
        milestones = project.get('milestones', [])
        if not milestones:
            return 0.0
        
        completed_milestones = len([m for m in milestones if m.get('is_completed', False)])
        return completed_milestones / len(milestones)
    
    async def _handle_stage_transition_actions(
        self,
        project_id: uuid.UUID,
        old_stage: str,
        new_stage: str
    ):
        """處理階段轉換的後續操作"""
        try:
            # 根據新階段執行相應操作
            if new_stage == ProjectStage.PILOT.value:
                # 進入試點階段，開始用戶行為追蹤
                await self._start_user_behavior_tracking(project_id)
            
            elif new_stage == ProjectStage.SCALING.value:
                # 進入規模化階段，增加預算監控
                await self._increase_budget_monitoring(project_id)
            
            elif new_stage == ProjectStage.MATURE.value:
                # 進入成熟階段，結束ROI豁免
                await self._end_roi_exemption(project_id)
            
            elif new_stage == ProjectStage.DISCONTINUED.value:
                # 項目停止，進行收尾工作
                await self._handle_project_discontinuation(project_id)
                
        except Exception as e:
            self.logger.error(f"❌ Error handling stage transition actions: {e}")
    
    async def _calculate_budget_health_score(self, project: Dict[str, Any]) -> float:
        """計算預算健康分數"""
        budget_tracking = project.get('budget_tracking', [])
        if not budget_tracking:
            return 50.0  # 中性分數
        
        # 計算預算利用率
        total_allocated = sum(
            float(bt['amount']) for bt in budget_tracking
            if bt['transaction_type'] == 'allocation'
        )
        total_spent = sum(
            float(bt['amount']) for bt in budget_tracking
            if bt['transaction_type'] == 'expense'
        )
        
        if total_allocated == 0:
            return 50.0
        
        utilization_rate = total_spent / total_allocated
        
        # 理想利用率為 70-85%
        if 0.7 <= utilization_rate <= 0.85:
            return 100.0
        elif utilization_rate < 0.7:
            return 80.0 - (0.7 - utilization_rate) * 100
        else:  # 超預算
            return max(0.0, 85.0 - (utilization_rate - 0.85) * 200)
    
    async def _calculate_milestone_progress_score(self, project: Dict[str, Any]) -> float:
        """計算里程碑進度分數"""
        milestones = project.get('milestones', [])
        if not milestones:
            return 50.0
        
        completion_rate = self._calculate_milestone_completion_rate(project)
        
        # 檢查延遲情況
        delayed_milestones = 0
        for milestone in milestones:
            planned_date = milestone.get('planned_date')
            is_completed = milestone.get('is_completed', False)
            
            if planned_date and not is_completed:
                if isinstance(planned_date, str):
                    planned_date = date.fromisoformat(planned_date)
                if planned_date < date.today():
                    delayed_milestones += 1
        
        delay_penalty = (delayed_milestones / len(milestones)) * 20
        
        return max(0.0, completion_rate * 100 - delay_penalty)
    
    async def _calculate_user_engagement_score(self, project: Dict[str, Any]) -> float:
        """計算用戶參與分數"""
        metrics = project.get('user_behavior_metrics', [])
        if not metrics:
            return 50.0
        
        # 使用最新的指標
        latest_metrics = max(metrics, key=lambda m: m['measurement_date'])
        
        engagement_score = float(latest_metrics.get('engagement_score', 50))
        satisfaction_score = float(latest_metrics.get('user_satisfaction_score', 3)) * 20  # 轉換為100分制
        
        return (engagement_score * 0.7 + satisfaction_score * 0.3)
    
    async def _calculate_risk_score(self, project: Dict[str, Any]) -> float:
        """計算風險分數"""
        risk_score = 0.0
        
        # 預算風險
        budget_health = await self._calculate_budget_health_score(project)
        if budget_health < 60:
            risk_score += 30
        
        # 進度風險
        milestone_score = await self._calculate_milestone_progress_score(project)
        if milestone_score < 60:
            risk_score += 25
        
        # 團隊風險（基於團隊規模）
        team_size = project.get('team_size', 1)
        if team_size < 3:
            risk_score += 15
        
        # 技術風險（基於創新類型）
        innovation_type = project.get('innovation_type', '')
        if innovation_type in ['disruptive', 'breakthrough']:
            risk_score += 20
        
        return min(100.0, risk_score)
    
    async def _generate_health_recommendations(
        self,
        project: Dict[str, Any],
        budget_score: float,
        milestone_score: float,
        engagement_score: float,
        risk_score: float
    ) -> List[str]:
        """生成健康改進建議"""
        recommendations = []
        
        if budget_score < 60:
            recommendations.append("Budget utilization needs attention - review spending patterns and reallocate resources")
        
        if milestone_score < 60:
            recommendations.append("Milestone progress is behind schedule - reassess timeline and resource allocation")
        
        if engagement_score < 60:
            recommendations.append("User engagement is low - conduct user research and improve feature adoption")
        
        if risk_score > 70:
            recommendations.append("High risk level detected - implement risk mitigation strategies")
        
        # 特定建議
        if project.get('current_stage') == 'concept' and len(project.get('milestones', [])) < 3:
            recommendations.append("Add more detailed milestones for better progress tracking")
        
        if project.get('team_size', 0) < 3:
            recommendations.append("Consider expanding team size for better capability coverage")
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """服務健康檢查"""
        try:
            db_health = await self.innovation_db.health_check()
            
            return {
                'service': 'innovation_zone_service',
                'status': 'healthy' if db_health['status'] == 'healthy' else 'degraded',
                'timestamp': datetime.now(timezone.utc),
                'components': {
                    'innovation_db': db_health['status'],
                    'milestone_tracker': 'healthy',
                    'admission_evaluator': 'healthy',
                    'budget_roi_manager': 'healthy',
                    'anomaly_detector': 'healthy'
                },
                'performance_metrics': self.performance_metrics,
                'configuration': {
                    'roi_exemption_quarters': self.config['default_roi_exemption_quarters'],
                    'minimum_admission_score': self.config['minimum_admission_score_threshold'],
                    'anomaly_confidence_threshold': self.config['anomaly_confidence_threshold']
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                'service': 'innovation_zone_service',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }