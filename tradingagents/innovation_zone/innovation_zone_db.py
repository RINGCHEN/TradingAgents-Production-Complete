#!/usr/bin/env python3
"""
Innovation Zone Database Manager
創新特區資料庫管理器

提供創新特區相關的所有數據庫操作，包括：
- 創新特區和項目的 CRUD 操作
- 預算分配和追蹤管理
- 里程碑和指標數據管理
- 異常檢測數據管理
- 複雜查詢和分析功能
"""

import asyncio
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
import uuid
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import (
    select, insert, update, delete, and_, or_, func, 
    text, distinct, case, desc, asc
)
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import (
    InnovationZone, InnovationProject, InnovationBudgetAllocation,
    InnovationBudgetTracking, TechnicalMilestone, UserBehaviorMetrics,
    AnomalyDetection, InnovationType, ProjectStage, ROIExemptionStatus,
    MilestoneType, AnomalyType
)
from ..database.database import SessionLocal

logger = logging.getLogger(__name__)

@asynccontextmanager
async def get_database_session():
    """獲取數據庫會話的異步上下文管理器"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

class InnovationZoneDBError(Exception):
    """創新特區數據庫錯誤基類"""
    pass

class InnovationZoneDB:
    """
    創新特區數據庫管理器
    
    功能：
    1. 創新特區和項目的完整生命週期管理
    2. 預算分配和追蹤的精確控制
    3. 技術里程碑進度追蹤
    4. 用戶行為指標收集和分析
    5. 異常檢測和預警機制
    6. 複雜的分析查詢和報告生成
    """
    
    def __init__(self):
        """初始化創新特區數據庫管理器"""
        self.logger = logger
        self.logger.info("✅ Innovation Zone Database Manager initialized")
    
    # ==================== 創新特區管理 ====================
    
    async def create_innovation_zone(
        self,
        zone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """創建創新特區"""
        try:
            async with get_database_session() as session:
                # 檢查特區名稱和代碼是否已存在
                existing_zone = await session.execute(
                    select(InnovationZone)
                    .where(
                        or_(
                            InnovationZone.zone_name == zone_data['zone_name'],
                            InnovationZone.zone_code == zone_data['zone_code']
                        )
                    )
                )
                
                if existing_zone.scalar():
                    raise InnovationZoneDBError(
                        f"Innovation zone with name '{zone_data['zone_name']}' "
                        f"or code '{zone_data['zone_code']}' already exists"
                    )
                
                # 創建新的創新特區
                new_zone = InnovationZone(**zone_data)
                session.add(new_zone)
                
                await session.commit()
                await session.refresh(new_zone)
                
                zone_dict = self._innovation_zone_to_dict(new_zone)
                
                self.logger.info(f"✅ Created innovation zone: {new_zone.zone_name}")
                return zone_dict
                
        except IntegrityError as e:
            self.logger.error(f"❌ Integrity error creating innovation zone: {e}")
            raise InnovationZoneDBError(f"Database integrity error: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error creating innovation zone: {e}")
            raise InnovationZoneDBError(f"Failed to create innovation zone: {e}")
    
    async def get_innovation_zone(
        self,
        zone_id: uuid.UUID,
        include_projects: bool = False,
        include_budget: bool = False
    ) -> Optional[Dict[str, Any]]:
        """獲取創新特區詳情"""
        try:
            async with get_database_session() as session:
                query = select(InnovationZone).where(InnovationZone.id == zone_id)
                
                if include_projects:
                    query = query.options(selectinload(InnovationZone.innovation_projects))
                
                if include_budget:
                    query = query.options(selectinload(InnovationZone.budget_allocations))
                
                result = await session.execute(query)
                zone = result.scalar()
                
                if not zone:
                    return None
                
                zone_dict = self._innovation_zone_to_dict(zone)
                
                # 添加項目統計
                if include_projects:
                    zone_dict['projects'] = [
                        self._innovation_project_to_dict(project)
                        for project in zone.innovation_projects
                        if project.is_active
                    ]
                    zone_dict['active_projects_count'] = len(zone_dict['projects'])
                
                # 添加預算信息
                if include_budget:
                    zone_dict['budget_allocations'] = [
                        self._budget_allocation_to_dict(allocation)
                        for allocation in zone.budget_allocations
                    ]
                
                return zone_dict
                
        except Exception as e:
            self.logger.error(f"❌ Error getting innovation zone {zone_id}: {e}")
            raise InnovationZoneDBError(f"Failed to get innovation zone: {e}")
    
    async def list_innovation_zones(
        self,
        active_only: bool = True,
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """列出創新特區"""
        try:
            async with get_database_session() as session:
                query = select(InnovationZone)
                
                if active_only:
                    query = query.where(InnovationZone.is_active == True)
                
                query = query.order_by(InnovationZone.established_date.desc())
                
                result = await session.execute(query)
                zones = result.scalars().all()
                
                zones_list = []
                for zone in zones:
                    zone_dict = self._innovation_zone_to_dict(zone)
                    
                    if include_stats:
                        # 添加統計信息
                        stats = await self._get_zone_statistics(session, zone.id)
                        zone_dict.update(stats)
                    
                    zones_list.append(zone_dict)
                
                return zones_list
                
        except Exception as e:
            self.logger.error(f"❌ Error listing innovation zones: {e}")
            raise InnovationZoneDBError(f"Failed to list innovation zones: {e}")
    
    async def update_innovation_zone(
        self,
        zone_id: uuid.UUID,
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """更新創新特區"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(InnovationZone).where(InnovationZone.id == zone_id)
                )
                zone = result.scalar()
                
                if not zone:
                    raise InnovationZoneDBError(f"Innovation zone {zone_id} not found")
                
                # 更新字段
                for field, value in update_data.items():
                    if hasattr(zone, field):
                        setattr(zone, field, value)
                
                zone.updated_at = datetime.now(timezone.utc)
                
                await session.commit()
                await session.refresh(zone)
                
                zone_dict = self._innovation_zone_to_dict(zone)
                
                self.logger.info(f"✅ Updated innovation zone: {zone.zone_name}")
                return zone_dict
                
        except Exception as e:
            self.logger.error(f"❌ Error updating innovation zone {zone_id}: {e}")
            raise InnovationZoneDBError(f"Failed to update innovation zone: {e}")
    
    # ==================== 創新項目管理 ====================
    
    async def create_innovation_project(
        self,
        project_data: Dict[str, Any],
        admission_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """創建創新項目"""
        try:
            async with get_database_session() as session:
                # 驗證創新特區存在
                zone_result = await session.execute(
                    select(InnovationZone).where(
                        InnovationZone.id == project_data['innovation_zone_id']
                    )
                )
                zone = zone_result.scalar()
                
                if not zone:
                    raise InnovationZoneDBError(
                        f"Innovation zone {project_data['innovation_zone_id']} not found"
                    )
                
                # 檢查項目代碼是否已存在
                existing_project = await session.execute(
                    select(InnovationProject).where(
                        InnovationProject.project_code == project_data['project_code']
                    )
                )
                
                if existing_project.scalar():
                    raise InnovationZoneDBError(
                        f"Project code '{project_data['project_code']}' already exists"
                    )
                
                # 計算總准入評分
                total_score = sum(
                    zone.admission_criteria_weights.get(criterion, 0) * score
                    for criterion, score in admission_scores.items()
                )
                
                # 檢查是否符合准入標準
                if total_score < float(zone.minimum_admission_score):
                    raise InnovationZoneDBError(
                        f"Project admission score {total_score:.2f} is below minimum "
                        f"threshold {zone.minimum_admission_score}"
                    )
                
                # 創建項目
                project_data.update({
                    'admission_score': Decimal(str(total_score)),
                    'admission_criteria_scores': admission_scores,
                    'roi_exemption_end_date': (
                        project_data.get('start_date', date.today()) + 
                        timedelta(days=zone.roi_exemption_quarters * 90)
                    )
                })
                
                new_project = InnovationProject(**project_data)
                session.add(new_project)
                
                await session.commit()
                await session.refresh(new_project)
                
                project_dict = self._innovation_project_to_dict(new_project)
                
                self.logger.info(f"✅ Created innovation project: {new_project.project_name}")
                return project_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error creating innovation project: {e}")
            raise InnovationZoneDBError(f"Failed to create innovation project: {e}")
    
    async def get_innovation_project(
        self,
        project_id: uuid.UUID,
        include_milestones: bool = False,
        include_budget: bool = False,
        include_metrics: bool = False
    ) -> Optional[Dict[str, Any]]:
        """獲取創新項目詳情"""
        try:
            async with get_database_session() as session:
                query = select(InnovationProject).where(InnovationProject.id == project_id)
                
                if include_milestones:
                    query = query.options(selectinload(InnovationProject.milestones))
                
                if include_budget:
                    query = query.options(selectinload(InnovationProject.budget_tracking))
                
                if include_metrics:
                    query = query.options(selectinload(InnovationProject.user_behavior_metrics))
                
                result = await session.execute(query)
                project = result.scalar()
                
                if not project:
                    return None
                
                project_dict = self._innovation_project_to_dict(project)
                
                # 添加詳細信息
                if include_milestones:
                    project_dict['milestones'] = [
                        self._milestone_to_dict(milestone)
                        for milestone in project.milestones
                    ]
                    project_dict['milestones_count'] = len(project_dict['milestones'])
                    project_dict['completed_milestones_count'] = len([
                        m for m in project_dict['milestones'] if m['is_completed']
                    ])
                
                if include_budget:
                    project_dict['budget_tracking'] = [
                        self._budget_tracking_to_dict(tracking)
                        for tracking in project.budget_tracking
                    ]
                
                if include_metrics:
                    project_dict['user_behavior_metrics'] = [
                        self._user_metrics_to_dict(metrics)
                        for metrics in project.user_behavior_metrics
                    ]
                
                return project_dict
                
        except Exception as e:
            self.logger.error(f"❌ Error getting innovation project {project_id}: {e}")
            raise InnovationZoneDBError(f"Failed to get innovation project: {e}")
    
    async def list_innovation_projects(
        self,
        zone_id: Optional[uuid.UUID] = None,
        stage: Optional[ProjectStage] = None,
        active_only: bool = True,
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """列出創新項目"""
        try:
            async with get_database_session() as session:
                query = select(InnovationProject)
                
                if zone_id:
                    query = query.where(InnovationProject.innovation_zone_id == zone_id)
                
                if stage:
                    query = query.where(InnovationProject.current_stage == stage.value)
                
                if active_only:
                    query = query.where(InnovationProject.is_active == True)
                
                query = query.order_by(InnovationProject.created_at.desc())
                
                result = await session.execute(query)
                projects = result.scalars().all()
                
                projects_list = []
                for project in projects:
                    project_dict = self._innovation_project_to_dict(project)
                    
                    if include_stats:
                        # 添加統計信息
                        stats = await self._get_project_statistics(session, project.id)
                        project_dict.update(stats)
                    
                    projects_list.append(project_dict)
                
                return projects_list
                
        except Exception as e:
            self.logger.error(f"❌ Error listing innovation projects: {e}")
            raise InnovationZoneDBError(f"Failed to list innovation projects: {e}")
    
    async def update_project_stage(
        self,
        project_id: uuid.UUID,
        new_stage: ProjectStage,
        updated_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新項目階段"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(InnovationProject).where(InnovationProject.id == project_id)
                )
                project = result.scalar()
                
                if not project:
                    raise InnovationZoneDBError(f"Innovation project {project_id} not found")
                
                old_stage = project.current_stage
                project.current_stage = new_stage.value
                project.updated_at = datetime.now(timezone.utc)
                
                # 如果項目完成或停止，設置實際結束日期
                if new_stage in [ProjectStage.MATURE, ProjectStage.DISCONTINUED]:
                    project.actual_end_date = date.today()
                    project.roi_exemption_status = ROIExemptionStatus.EXPIRED.value
                
                await session.commit()
                await session.refresh(project)
                
                project_dict = self._innovation_project_to_dict(project)
                
                self.logger.info(
                    f"✅ Updated project stage: {project.project_name} "
                    f"from {old_stage} to {new_stage.value}"
                )
                
                return project_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error updating project stage {project_id}: {e}")
            raise InnovationZoneDBError(f"Failed to update project stage: {e}")
    
    # ==================== 預算管理 ====================
    
    async def allocate_budget(
        self,
        allocation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分配預算"""
        try:
            async with get_database_session() as session:
                # 檢查是否已有同期預算分配
                existing_allocation = await session.execute(
                    select(InnovationBudgetAllocation).where(
                        and_(
                            InnovationBudgetAllocation.innovation_zone_id == allocation_data['innovation_zone_id'],
                            InnovationBudgetAllocation.fiscal_year == allocation_data['fiscal_year'],
                            InnovationBudgetAllocation.quarter == allocation_data['quarter']
                        )
                    )
                )
                
                if existing_allocation.scalar():
                    raise InnovationZoneDBError(
                        f"Budget allocation for Q{allocation_data['quarter']} "
                        f"{allocation_data['fiscal_year']} already exists"
                    )
                
                # 設置預算計算
                allocation_data['allocated_budget'] = allocation_data['total_allocated_budget']
                allocation_data['remaining_budget'] = allocation_data['total_allocated_budget']
                
                new_allocation = InnovationBudgetAllocation(**allocation_data)
                session.add(new_allocation)
                
                await session.commit()
                await session.refresh(new_allocation)
                
                allocation_dict = self._budget_allocation_to_dict(new_allocation)
                
                self.logger.info(
                    f"✅ Allocated budget: {allocation_data['total_allocated_budget']} "
                    f"for Q{allocation_data['quarter']} {allocation_data['fiscal_year']}"
                )
                
                return allocation_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error allocating budget: {e}")
            raise InnovationZoneDBError(f"Failed to allocate budget: {e}")
    
    async def track_budget_expense(
        self,
        expense_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """追蹤預算支出"""
        try:
            async with get_database_session() as session:
                # 獲取項目信息
                project_result = await session.execute(
                    select(InnovationProject).where(
                        InnovationProject.id == expense_data['innovation_project_id']
                    )
                )
                project = project_result.scalar()
                
                if not project:
                    raise InnovationZoneDBError(
                        f"Innovation project {expense_data['innovation_project_id']} not found"
                    )
                
                # 計算項目當前預算狀況
                budget_stats = await self._calculate_project_budget_status(session, project.id)
                
                # 更新預算信息
                expense_data.update({
                    'project_total_budget': budget_stats['total_budget'],
                    'budget_utilized': budget_stats['utilized_budget'] + expense_data['amount'],
                    'budget_remaining': budget_stats['remaining_budget'] - expense_data['amount'],
                    'budget_utilization_rate': (
                        (budget_stats['utilized_budget'] + expense_data['amount']) / 
                        budget_stats['total_budget'] * 100
                        if budget_stats['total_budget'] > 0 else 0
                    )
                })
                
                # 檢查ROI豁免狀態
                expense_data['is_roi_exempt_period'] = (
                    project.roi_exemption_status in [
                        ROIExemptionStatus.EXEMPT.value,
                        ROIExemptionStatus.PARTIAL_EXEMPT.value
                    ] and (
                        project.roi_exemption_end_date is None or
                        project.roi_exemption_end_date >= date.today()
                    )
                )
                
                new_expense = InnovationBudgetTracking(**expense_data)
                session.add(new_expense)
                
                await session.commit()
                await session.refresh(new_expense)
                
                expense_dict = self._budget_tracking_to_dict(new_expense)
                
                self.logger.info(
                    f"✅ Tracked budget expense: {expense_data['amount']} "
                    f"for project {project.project_name}"
                )
                
                return expense_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error tracking budget expense: {e}")
            raise InnovationZoneDBError(f"Failed to track budget expense: {e}")
    
    # ==================== 里程碑管理 ====================
    
    async def create_milestone(
        self,
        milestone_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """創建技術里程碑"""
        try:
            async with get_database_session() as session:
                # 驗證項目存在
                project_result = await session.execute(
                    select(InnovationProject).where(
                        InnovationProject.id == milestone_data['innovation_project_id']
                    )
                )
                
                if not project_result.scalar():
                    raise InnovationZoneDBError(
                        f"Innovation project {milestone_data['innovation_project_id']} not found"
                    )
                
                new_milestone = TechnicalMilestone(**milestone_data)
                session.add(new_milestone)
                
                await session.commit()
                await session.refresh(new_milestone)
                
                milestone_dict = self._milestone_to_dict(new_milestone)
                
                self.logger.info(f"✅ Created milestone: {new_milestone.milestone_name}")
                return milestone_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error creating milestone: {e}")
            raise InnovationZoneDBError(f"Failed to create milestone: {e}")
    
    async def update_milestone_progress(
        self,
        milestone_id: uuid.UUID,
        completion_rate: Decimal,
        updated_metrics: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None,
        updated_by: str = "system"
    ) -> Dict[str, Any]:
        """更新里程碑進度"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(TechnicalMilestone).where(TechnicalMilestone.id == milestone_id)
                )
                milestone = result.scalar()
                
                if not milestone:
                    raise InnovationZoneDBError(f"Milestone {milestone_id} not found")
                
                # 更新進度
                milestone.completion_rate = completion_rate
                milestone.updated_at = datetime.now(timezone.utc)
                
                if updated_metrics:
                    milestone.technical_metrics.update(updated_metrics)
                
                if notes:
                    milestone.review_feedback = notes
                
                # 檢查是否完成
                if completion_rate >= 100:
                    milestone.is_completed = True
                    milestone.actual_date = date.today()
                    milestone.status = 'completed'
                elif completion_rate > 0:
                    milestone.status = 'in_progress'
                
                await session.commit()
                await session.refresh(milestone)
                
                milestone_dict = self._milestone_to_dict(milestone)
                
                self.logger.info(
                    f"✅ Updated milestone progress: {milestone.milestone_name} "
                    f"to {completion_rate}%"
                )
                
                return milestone_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error updating milestone progress {milestone_id}: {e}")
            raise InnovationZoneDBError(f"Failed to update milestone progress: {e}")
    
    # ==================== 用戶行為指標 ====================
    
    async def record_user_behavior_metrics(
        self,
        metrics_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """記錄用戶行為指標"""
        try:
            async with get_database_session() as session:
                # 檢查是否已有同日期的指標記錄
                existing_metrics = await session.execute(
                    select(UserBehaviorMetrics).where(
                        and_(
                            UserBehaviorMetrics.innovation_project_id == metrics_data['innovation_project_id'],
                            UserBehaviorMetrics.measurement_date == metrics_data['measurement_date'],
                            UserBehaviorMetrics.measurement_period == metrics_data['measurement_period']
                        )
                    )
                )
                
                if existing_metrics.scalar():
                    raise InnovationZoneDBError(
                        f"Metrics for {metrics_data['measurement_date']} "
                        f"({metrics_data['measurement_period']}) already exist"
                    )
                
                # 設置數據來源
                if 'data_sources' not in metrics_data:
                    metrics_data['data_sources'] = ['user_tracking_system', 'analytics_platform']
                
                new_metrics = UserBehaviorMetrics(**metrics_data)
                session.add(new_metrics)
                
                await session.commit()
                await session.refresh(new_metrics)
                
                metrics_dict = self._user_metrics_to_dict(new_metrics)
                
                self.logger.info(
                    f"✅ Recorded user behavior metrics for "
                    f"{metrics_data['measurement_date']}"
                )
                
                return metrics_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error recording user behavior metrics: {e}")
            raise InnovationZoneDBError(f"Failed to record user behavior metrics: {e}")
    
    # ==================== 異常檢測 ====================
    
    async def create_anomaly_detection(
        self,
        anomaly_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """創建異常檢測記錄"""
        try:
            async with get_database_session() as session:
                new_anomaly = AnomalyDetection(**anomaly_data)
                session.add(new_anomaly)
                
                await session.commit()
                await session.refresh(new_anomaly)
                
                anomaly_dict = self._anomaly_to_dict(new_anomaly)
                
                self.logger.info(
                    f"✅ Created anomaly detection: {new_anomaly.anomaly_title} "
                    f"({new_anomaly.anomaly_severity})"
                )
                
                return anomaly_dict
                
        except Exception as e:
            self.logger.error(f"❌ Error creating anomaly detection: {e}")
            raise InnovationZoneDBError(f"Failed to create anomaly detection: {e}")
    
    async def resolve_anomaly(
        self,
        anomaly_id: uuid.UUID,
        resolution_actions: List[str],
        resolved_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """解決異常"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(AnomalyDetection).where(AnomalyDetection.id == anomaly_id)
                )
                anomaly = result.scalar()
                
                if not anomaly:
                    raise InnovationZoneDBError(f"Anomaly {anomaly_id} not found")
                
                # 更新異常狀態
                anomaly.status = 'resolved'
                anomaly.resolution_actions = resolution_actions
                anomaly.resolved_at = datetime.now(timezone.utc)
                anomaly.resolved_by = resolved_by
                anomaly.updated_at = datetime.now(timezone.utc)
                
                if notes:
                    anomaly.investigation_notes = (anomaly.investigation_notes or '') + f"\nResolution: {notes}"
                
                await session.commit()
                await session.refresh(anomaly)
                
                anomaly_dict = self._anomaly_to_dict(anomaly)
                
                self.logger.info(f"✅ Resolved anomaly: {anomaly.anomaly_title}")
                
                return anomaly_dict
                
        except InnovationZoneDBError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error resolving anomaly {anomaly_id}: {e}")
            raise InnovationZoneDBError(f"Failed to resolve anomaly: {e}")
    
    # ==================== 分析查詢 ====================
    
    async def get_innovation_analytics(
        self,
        zone_ids: Optional[List[uuid.UUID]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """獲取創新分析數據"""
        try:
            async with get_database_session() as session:
                analytics = {
                    'analysis_period': {
                        'start_date': start_date.isoformat() if start_date else None,
                        'end_date': end_date.isoformat() if end_date else None
                    },
                    'zones_overview': {},
                    'projects_summary': {},
                    'budget_analysis': {},
                    'milestones_progress': {},
                    'user_engagement': {},
                    'anomalies_summary': {}
                }
                
                # 特區概覽
                zones_query = select(InnovationZone)
                if zone_ids:
                    zones_query = zones_query.where(InnovationZone.id.in_(zone_ids))
                
                zones_result = await session.execute(zones_query)
                zones = zones_result.scalars().all()
                
                analytics['zones_overview'] = {
                    'total_zones': len(zones),
                    'active_zones': len([z for z in zones if z.is_active]),
                    'total_budget_allocated': sum(z.total_budget_allocation for z in zones),
                    'zones_by_focus': self._group_by_field(zones, 'innovation_focus')
                }
                
                # 項目摘要
                projects_query = select(InnovationProject)
                if zone_ids:
                    projects_query = projects_query.where(
                        InnovationProject.innovation_zone_id.in_(zone_ids)
                    )
                
                if start_date and end_date:
                    projects_query = projects_query.where(
                        and_(
                            InnovationProject.start_date >= start_date,
                            InnovationProject.start_date <= end_date
                        )
                    )
                
                projects_result = await session.execute(projects_query)
                projects = projects_result.scalars().all()
                
                analytics['projects_summary'] = {
                    'total_projects': len(projects),
                    'active_projects': len([p for p in projects if p.is_active]),
                    'projects_by_stage': self._group_by_field(projects, 'current_stage'),
                    'projects_by_type': self._group_by_field(projects, 'innovation_type'),
                    'roi_exempt_projects': len([
                        p for p in projects 
                        if p.roi_exemption_status == ROIExemptionStatus.EXEMPT.value
                    ])
                }
                
                # 預算分析
                if projects:
                    project_ids = [p.id for p in projects]
                    budget_query = select(InnovationBudgetTracking).where(
                        InnovationBudgetTracking.innovation_project_id.in_(project_ids)
                    )
                    
                    if start_date and end_date:
                        budget_query = budget_query.where(
                            and_(
                                InnovationBudgetTracking.transaction_date >= start_date,
                                InnovationBudgetTracking.transaction_date <= end_date
                            )
                        )
                    
                    budget_result = await session.execute(budget_query)
                    budget_tracking = budget_result.scalars().all()
                    
                    total_expenses = sum(
                        float(bt.amount) for bt in budget_tracking 
                        if bt.transaction_type == 'expense'
                    )
                    
                    analytics['budget_analysis'] = {
                        'total_expenses': total_expenses,
                        'expenses_by_category': self._group_expenses_by_category(budget_tracking),
                        'roi_exempt_expenses': sum(
                            float(bt.amount) for bt in budget_tracking 
                            if bt.is_roi_exempt_period and bt.transaction_type == 'expense'
                        )
                    }
                
                return analytics
                
        except Exception as e:
            self.logger.error(f"❌ Error getting innovation analytics: {e}")
            raise InnovationZoneDBError(f"Failed to get innovation analytics: {e}")
    
    # ==================== 輔助方法 ====================
    
    def _innovation_zone_to_dict(self, zone: InnovationZone) -> Dict[str, Any]:
        """將InnovationZone對象轉換為字典"""
        return {
            'id': zone.id,
            'zone_name': zone.zone_name,
            'zone_code': zone.zone_code,
            'description': zone.description,
            'innovation_focus': zone.innovation_focus,
            'target_innovation_types': zone.target_innovation_types,
            'total_budget_allocation': zone.total_budget_allocation,
            'budget_percentage_of_rd': zone.budget_percentage_of_rd,
            'quarterly_budget_limit': zone.quarterly_budget_limit,
            'roi_exemption_quarters': zone.roi_exemption_quarters,
            'roi_exemption_threshold': zone.roi_exemption_threshold,
            'zone_manager': zone.zone_manager,
            'sponsor_department': zone.sponsor_department,
            'admission_criteria_weights': zone.admission_criteria_weights,
            'minimum_admission_score': zone.minimum_admission_score,
            'is_active': zone.is_active,
            'established_date': zone.established_date,
            'review_date': zone.review_date,
            'created_at': zone.created_at,
            'updated_at': zone.updated_at
        }
    
    def _innovation_project_to_dict(self, project: InnovationProject) -> Dict[str, Any]:
        """將InnovationProject對象轉換為字典"""
        return {
            'id': project.id,
            'project_code': project.project_code,
            'innovation_zone_id': project.innovation_zone_id,
            'project_name': project.project_name,
            'project_description': project.project_description,
            'innovation_type': project.innovation_type,
            'current_stage': project.current_stage,
            'project_lead': project.project_lead,
            'team_size': project.team_size,
            'team_members': project.team_members,
            'start_date': project.start_date,
            'planned_end_date': project.planned_end_date,
            'actual_end_date': project.actual_end_date,
            'roi_exemption_status': project.roi_exemption_status,
            'roi_exemption_start_date': project.roi_exemption_start_date,
            'roi_exemption_end_date': project.roi_exemption_end_date,
            'admission_score': project.admission_score,
            'admission_criteria_scores': project.admission_criteria_scores,
            'is_active': project.is_active,
            'priority_level': project.priority_level,
            'strategic_importance': project.strategic_importance,
            'project_tags': project.project_tags,
            'created_at': project.created_at,
            'updated_at': project.updated_at,
            'created_by': project.created_by
        }
    
    def _budget_allocation_to_dict(self, allocation: InnovationBudgetAllocation) -> Dict[str, Any]:
        """將預算分配對象轉換為字典"""
        return {
            'id': allocation.id,
            'innovation_zone_id': allocation.innovation_zone_id,
            'fiscal_year': allocation.fiscal_year,
            'quarter': allocation.quarter,
            'total_allocated_budget': allocation.total_allocated_budget,
            'allocated_budget': allocation.allocated_budget,
            'committed_budget': allocation.committed_budget,
            'spent_budget': allocation.spent_budget,
            'remaining_budget': allocation.remaining_budget,
            'allocation_status': allocation.allocation_status,
            'created_at': allocation.created_at,
            'updated_at': allocation.updated_at
        }
    
    def _budget_tracking_to_dict(self, tracking: InnovationBudgetTracking) -> Dict[str, Any]:
        """將預算追蹤對象轉換為字典"""
        return {
            'id': tracking.id,
            'innovation_project_id': tracking.innovation_project_id,
            'transaction_date': tracking.transaction_date,
            'transaction_type': tracking.transaction_type,
            'amount': tracking.amount,
            'expense_category': tracking.expense_category,
            'description': tracking.description,
            'budget_utilization_rate': tracking.budget_utilization_rate,
            'is_roi_exempt_period': tracking.is_roi_exempt_period,
            'created_at': tracking.created_at
        }
    
    def _milestone_to_dict(self, milestone: TechnicalMilestone) -> Dict[str, Any]:
        """將里程碑對象轉換為字典"""
        return {
            'id': milestone.id,
            'innovation_project_id': milestone.innovation_project_id,
            'milestone_name': milestone.milestone_name,
            'milestone_type': milestone.milestone_type,
            'planned_date': milestone.planned_date,
            'actual_date': milestone.actual_date,
            'is_completed': milestone.is_completed,
            'completion_rate': milestone.completion_rate,
            'status': milestone.status,
            'technical_metrics': milestone.technical_metrics,
            'success_criteria': milestone.success_criteria,
            'quality_score': milestone.quality_score,
            'created_at': milestone.created_at,
            'updated_at': milestone.updated_at
        }
    
    def _user_metrics_to_dict(self, metrics: UserBehaviorMetrics) -> Dict[str, Any]:
        """將用戶指標對象轉換為字典"""
        return {
            'id': metrics.id,
            'innovation_project_id': metrics.innovation_project_id,
            'measurement_date': metrics.measurement_date,
            'measurement_period': metrics.measurement_period,
            'total_users': metrics.total_users,
            'active_users': metrics.active_users,
            'engagement_score': metrics.engagement_score,
            'conversion_rate': metrics.conversion_rate,
            'user_satisfaction_score': metrics.user_satisfaction_score,
            'feature_usage_frequency': metrics.feature_usage_frequency,
            'created_at': metrics.created_at
        }
    
    def _anomaly_to_dict(self, anomaly: AnomalyDetection) -> Dict[str, Any]:
        """將異常檢測對象轉換為字典"""
        return {
            'id': anomaly.id,
            'innovation_project_id': anomaly.innovation_project_id,
            'anomaly_type': anomaly.anomaly_type,
            'anomaly_severity': anomaly.anomaly_severity,
            'anomaly_title': anomaly.anomaly_title,
            'confidence_score': anomaly.confidence_score,
            'status': anomaly.status,
            'detected_at': anomaly.detected_at,
            'resolved_at': anomaly.resolved_at,
            'impact_level': anomaly.impact_level,
            'affected_areas': anomaly.affected_areas
        }
    
    async def _get_zone_statistics(self, session: AsyncSession, zone_id: uuid.UUID) -> Dict[str, Any]:
        """獲取特區統計信息"""
        # 項目統計
        projects_result = await session.execute(
            select(func.count(InnovationProject.id))
            .where(
                and_(
                    InnovationProject.innovation_zone_id == zone_id,
                    InnovationProject.is_active == True
                )
            )
        )
        active_projects_count = projects_result.scalar() or 0
        
        # 預算統計
        budget_result = await session.execute(
            select(func.sum(InnovationBudgetAllocation.spent_budget))
            .where(InnovationBudgetAllocation.innovation_zone_id == zone_id)
        )
        total_spent = budget_result.scalar() or Decimal('0')
        
        return {
            'active_projects_count': active_projects_count,
            'total_budget_spent': total_spent
        }
    
    async def _get_project_statistics(self, session: AsyncSession, project_id: uuid.UUID) -> Dict[str, Any]:
        """獲取項目統計信息"""
        # 里程碑統計
        milestones_result = await session.execute(
            select(
                func.count(TechnicalMilestone.id),
                func.count(case((TechnicalMilestone.is_completed == True, 1)))
            )
            .where(TechnicalMilestone.innovation_project_id == project_id)
        )
        milestones_count, completed_count = milestones_result.first() or (0, 0)
        
        # 預算利用率
        budget_stats = await self._calculate_project_budget_status(session, project_id)
        
        return {
            'milestones_count': milestones_count,
            'completed_milestones_count': completed_count,
            'budget_utilization_rate': budget_stats.get('utilization_rate', 0)
        }
    
    async def _calculate_project_budget_status(
        self,
        session: AsyncSession,
        project_id: uuid.UUID
    ) -> Dict[str, Any]:
        """計算項目預算狀況"""
        # 獲取項目預算追蹤記錄
        budget_result = await session.execute(
            select(
                func.sum(case((InnovationBudgetTracking.transaction_type == 'allocation', InnovationBudgetTracking.amount), else_=0)),
                func.sum(case((InnovationBudgetTracking.transaction_type == 'expense', InnovationBudgetTracking.amount), else_=0))
            )
            .where(InnovationBudgetTracking.innovation_project_id == project_id)
        )
        
        allocated_budget, utilized_budget = budget_result.first() or (Decimal('0'), Decimal('0'))
        remaining_budget = allocated_budget - utilized_budget
        
        utilization_rate = (
            float(utilized_budget / allocated_budget * 100) 
            if allocated_budget > 0 else 0
        )
        
        return {
            'total_budget': allocated_budget,
            'utilized_budget': utilized_budget,
            'remaining_budget': remaining_budget,
            'utilization_rate': utilization_rate
        }
    
    def _group_by_field(self, items: List[Any], field: str) -> Dict[str, int]:
        """按字段分組統計"""
        groups = {}
        for item in items:
            value = getattr(item, field, 'unknown')
            groups[value] = groups.get(value, 0) + 1
        return groups
    
    def _group_expenses_by_category(self, budget_tracking: List[InnovationBudgetTracking]) -> Dict[str, float]:
        """按類別分組支出"""
        expenses = {}
        for bt in budget_tracking:
            if bt.transaction_type == 'expense':
                category = bt.expense_category
                expenses[category] = expenses.get(category, 0) + float(bt.amount)
        return expenses
    
    # ==================== 性能監控支持方法 ====================
    
    async def get_active_projects(self) -> List[Dict[str, Any]]:
        """獲取所有活躍的創新項目"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(InnovationProject)
                    .where(InnovationProject.is_active == True)
                    .options(selectinload(InnovationProject.innovation_zone))
                )
                
                projects = result.scalars().all()
                return [self._project_to_dict(project) for project in projects]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting active projects: {e}")
            raise InnovationZoneDBError(f"Failed to get active projects: {e}")
    
    async def get_project_milestones(self, project_id: str) -> List[Dict[str, Any]]:
        """獲取項目的所有里程碑"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(TechnicalMilestone)
                    .where(TechnicalMilestone.innovation_project_id == uuid.UUID(project_id))
                    .order_by(TechnicalMilestone.planned_date)
                )
                
                milestones = result.scalars().all()
                return [self._milestone_to_dict(milestone) for milestone in milestones]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting project milestones: {e}")
            raise InnovationZoneDBError(f"Failed to get project milestones: {e}")
    
    async def get_project_budget_tracking(self, project_id: str) -> List[Dict[str, Any]]:
        """獲取項目的預算追蹤記錄"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(InnovationBudgetTracking)
                    .where(InnovationBudgetTracking.innovation_project_id == uuid.UUID(project_id))
                    .order_by(InnovationBudgetTracking.transaction_date.desc())
                )
                
                tracking_records = result.scalars().all()
                return [self._budget_tracking_to_dict(record) for record in tracking_records]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting project budget tracking: {e}")
            raise InnovationZoneDBError(f"Failed to get project budget tracking: {e}")
    
    async def get_project_user_metrics(self, project_id: str) -> List[Dict[str, Any]]:
        """獲取項目的用戶行為指標"""
        try:
            async with get_database_session() as session:
                result = await session.execute(
                    select(UserBehaviorMetrics)
                    .where(UserBehaviorMetrics.innovation_project_id == uuid.UUID(project_id))
                    .order_by(UserBehaviorMetrics.measurement_date.desc())
                )
                
                metrics = result.scalars().all()
                return [self._user_metrics_to_dict(metric) for metric in metrics]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting project user metrics: {e}")
            raise InnovationZoneDBError(f"Failed to get project user metrics: {e}")
    
    async def get_project_performance_summary(self, project_id: str) -> Dict[str, Any]:
        """獲取項目性能摘要信息"""
        try:
            async with get_database_session() as session:
                # 獲取項目基本信息
                project_result = await session.execute(
                    select(InnovationProject)
                    .where(InnovationProject.id == uuid.UUID(project_id))
                    .options(selectinload(InnovationProject.innovation_zone))
                )
                
                project = project_result.scalar()
                if not project:
                    raise InnovationZoneDBError(f"Project {project_id} not found")
                
                # 獲取里程碑統計
                milestones_result = await session.execute(
                    select(
                        func.count(TechnicalMilestone.id).label('total_milestones'),
                        func.sum(case((TechnicalMilestone.is_completed == True, 1), else_=0)).label('completed_milestones'),
                        func.avg(TechnicalMilestone.quality_score).label('avg_quality_score')
                    )
                    .where(TechnicalMilestone.innovation_project_id == uuid.UUID(project_id))
                )
                
                milestone_stats = milestones_result.first()
                
                # 獲取預算統計
                budget_result = await session.execute(
                    select(
                        func.sum(case((InnovationBudgetTracking.transaction_type == 'allocation', InnovationBudgetTracking.amount), else_=0)).label('total_allocated'),
                        func.sum(case((InnovationBudgetTracking.transaction_type == 'expense', InnovationBudgetTracking.amount), else_=0)).label('total_spent')
                    )
                    .where(InnovationBudgetTracking.innovation_project_id == uuid.UUID(project_id))
                )
                
                budget_stats = budget_result.first()
                
                # 獲取最新用戶指標
                latest_metrics_result = await session.execute(
                    select(UserBehaviorMetrics)
                    .where(UserBehaviorMetrics.innovation_project_id == uuid.UUID(project_id))
                    .order_by(UserBehaviorMetrics.measurement_date.desc())
                    .limit(1)
                )
                
                latest_user_metrics = latest_metrics_result.scalar()
                
                return {
                    'project_id': project_id,
                    'project_name': project.project_name,
                    'current_stage': project.current_stage,
                    'team_size': project.team_size,
                    'is_active': project.is_active,
                    'roi_exemption_status': project.roi_exemption_status,
                    'roi_exemption_start_date': project.roi_exemption_start_date,
                    'milestone_stats': {
                        'total_milestones': milestone_stats.total_milestones or 0,
                        'completed_milestones': milestone_stats.completed_milestones or 0,
                        'avg_quality_score': float(milestone_stats.avg_quality_score or 0)
                    },
                    'budget_stats': {
                        'total_allocated': float(budget_stats.total_allocated or 0),
                        'total_spent': float(budget_stats.total_spent or 0)
                    },
                    'latest_user_metrics': (
                        self._user_metrics_to_dict(latest_user_metrics) 
                        if latest_user_metrics else None
                    )
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting project performance summary: {e}")
            raise InnovationZoneDBError(f"Failed to get project performance summary: {e}")
    
    async def get_projects_performance_batch(self, project_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """批量獲取多個項目的性能數據"""
        try:
            async with get_database_session() as session:
                project_uuids = [uuid.UUID(pid) for pid in project_ids]
                
                # 獲取所有項目的基本信息
                projects_result = await session.execute(
                    select(InnovationProject)
                    .where(InnovationProject.id.in_(project_uuids))
                    .options(selectinload(InnovationProject.innovation_zone))
                )
                
                projects = {str(p.id): self._project_to_dict(p) for p in projects_result.scalars().all()}
                
                # 獲取所有項目的里程碑統計
                milestones_result = await session.execute(
                    select(
                        TechnicalMilestone.innovation_project_id,
                        func.count(TechnicalMilestone.id).label('total_milestones'),
                        func.sum(case((TechnicalMilestone.is_completed == True, 1), else_=0)).label('completed_milestones'),
                        func.avg(TechnicalMilestone.quality_score).label('avg_quality_score')
                    )
                    .where(TechnicalMilestone.innovation_project_id.in_(project_uuids))
                    .group_by(TechnicalMilestone.innovation_project_id)
                )
                
                milestone_stats = {
                    str(row.innovation_project_id): {
                        'total_milestones': row.total_milestones or 0,
                        'completed_milestones': row.completed_milestones or 0,
                        'avg_quality_score': float(row.avg_quality_score or 0)
                    }
                    for row in milestones_result.all()
                }
                
                # 獲取所有項目的預算統計
                budget_result = await session.execute(
                    select(
                        InnovationBudgetTracking.innovation_project_id,
                        func.sum(case((InnovationBudgetTracking.transaction_type == 'allocation', InnovationBudgetTracking.amount), else_=0)).label('total_allocated'),
                        func.sum(case((InnovationBudgetTracking.transaction_type == 'expense', InnovationBudgetTracking.amount), else_=0)).label('total_spent')
                    )
                    .where(InnovationBudgetTracking.innovation_project_id.in_(project_uuids))
                    .group_by(InnovationBudgetTracking.innovation_project_id)
                )
                
                budget_stats = {
                    str(row.innovation_project_id): {
                        'total_allocated': float(row.total_allocated or 0),
                        'total_spent': float(row.total_spent or 0)
                    }
                    for row in budget_result.all()
                }
                
                # 組合結果
                performance_data = {}
                for project_id in project_ids:
                    performance_data[project_id] = {
                        'project': projects.get(project_id, {}),
                        'milestone_stats': milestone_stats.get(project_id, {
                            'total_milestones': 0,
                            'completed_milestones': 0,
                            'avg_quality_score': 0
                        }),
                        'budget_stats': budget_stats.get(project_id, {
                            'total_allocated': 0,
                            'total_spent': 0
                        })
                    }
                
                return performance_data
                
        except Exception as e:
            self.logger.error(f"❌ Error getting projects performance batch: {e}")
            raise InnovationZoneDBError(f"Failed to get projects performance batch: {e}")
    
    async def get_project_risk_indicators(self, project_id: str) -> Dict[str, Any]:
        """獲取項目風險指標"""
        try:
            async with get_database_session() as session:
                # 獲取延期里程碑
                overdue_milestones = await session.execute(
                    select(func.count(TechnicalMilestone.id))
                    .where(
                        and_(
                            TechnicalMilestone.innovation_project_id == uuid.UUID(project_id),
                            TechnicalMilestone.is_completed == False,
                            TechnicalMilestone.planned_date < datetime.now(timezone.utc).date()
                        )
                    )
                )
                
                # 獲取預算超支情況
                budget_overrun = await session.execute(
                    select(
                        func.sum(case((InnovationBudgetTracking.transaction_type == 'allocation', InnovationBudgetTracking.amount), else_=0)).label('allocated'),
                        func.sum(case((InnovationBudgetTracking.transaction_type == 'expense', InnovationBudgetTracking.amount), else_=0)).label('spent')
                    )
                    .where(InnovationBudgetTracking.innovation_project_id == uuid.UUID(project_id))
                )
                
                budget_data = budget_overrun.first()
                allocated = float(budget_data.allocated or 0)
                spent = float(budget_data.spent or 0)
                utilization_rate = spent / allocated if allocated > 0 else 0
                
                # 獲取活躍異常
                active_anomalies = await session.execute(
                    select(func.count(AnomalyDetection.id))
                    .where(
                        and_(
                            AnomalyDetection.innovation_project_id == uuid.UUID(project_id),
                            AnomalyDetection.status == 'active'
                        )
                    )
                )
                
                return {
                    'overdue_milestones': overdue_milestones.scalar() or 0,
                    'budget_utilization_rate': utilization_rate,
                    'is_budget_overrun': utilization_rate > 1.0,
                    'active_anomalies': active_anomalies.scalar() or 0
                }
                
        except Exception as e:
            self.logger.error(f"❌ Error getting project risk indicators: {e}")
            return {
                'overdue_milestones': 0,
                'budget_utilization_rate': 0,
                'is_budget_overrun': False,
                'active_anomalies': 0
            }

    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            async with get_database_session() as session:
                # 測試基本查詢
                result = await session.execute(select(func.count(InnovationZone.id)))
                zones_count = result.scalar()
                
                return {
                    'status': 'healthy',
                    'innovation_zones_count': zones_count,
                    'timestamp': datetime.now(timezone.utc),
                    'database_connection': 'active'
                }
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }