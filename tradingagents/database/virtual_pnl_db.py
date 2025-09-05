#!/usr/bin/env python3
"""
Virtual P&L Database Service
GPT-OSS虛擬損益表數據庫服務 - 任務2.1.1

企業級虛擬損益表數據庫服務，提供：
- 成本追蹤CRUD操作
- 收益歸因管理
- 預算管理和分析
- 內部計費處理
- P&L報告生成
- ROI和成本效益分析
"""

import uuid
import logging
import asyncio
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, desc, func, text, extract, case
from contextlib import contextmanager
import calendar

from .database import SessionLocal, engine
from .virtual_pnl_models import (
    CostCenter, CostTracking, RevenueAttribution, BudgetAllocation,
    InternalBilling, VirtualPnLSummary,
    CostTrackingCreate, RevenueAttributionCreate, BudgetAllocationCreate,
    VirtualPnLSummaryResponse, CostAnalysisRequest, ROIAnalysisRequest,
    CostCategory, CostType, RevenueSource, BudgetPeriodType, AllocationMethod
)

logger = logging.getLogger(__name__)

class VirtualPnLDBError(Exception):
    """虛擬損益表數據庫錯誤"""
    pass

class VirtualPnLDB:
    """
    虛擬損益表數據庫服務
    
    功能：
    1. 成本追蹤管理（CRUD、分類、分攤）
    2. 收益歸因處理（增量收益、歸因分析）
    3. 預算管理（分配、監控、預警）
    4. 內部計費（跨部門成本分攤）
    5. P&L報告生成（週期性、實時）
    6. ROI和成本效益分析
    """
    
    def __init__(self):
        """初始化虛擬損益表數據庫服務"""
        self.logger = logger
        self._ensure_tables()
        
        # 初始化標準成本中心
        asyncio.create_task(self._initialize_cost_centers())
    
    def _ensure_tables(self):
        """確保數據庫表存在"""
        try:
            from .virtual_pnl_models import Base
            Base.metadata.create_all(bind=engine)
            self.logger.info("✅ Virtual P&L tables created/verified successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to create virtual P&L tables: {e}")
            raise VirtualPnLDBError(f"Database initialization failed: {e}")
    
    @contextmanager
    def get_session(self):
        """獲取數據庫會話上下文管理器"""
        session = SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== 成本中心管理 ====================
    
    async def create_cost_center(
        self,
        code: str,
        name: str,
        description: Optional[str] = None,
        parent_id: Optional[uuid.UUID] = None,
        manager: Optional[str] = None,
        department: Optional[str] = None,
        budget_limit: Optional[Decimal] = None
    ) -> CostCenter:
        """創建成本中心"""
        try:
            with self.get_session() as session:
                # 計算層級和路徑
                level = 0
                path = f"/{code}"
                
                if parent_id:
                    parent = session.query(CostCenter).filter(CostCenter.id == parent_id).first()
                    if parent:
                        level = parent.level + 1
                        path = f"{parent.path}/{code}"
                
                cost_center = CostCenter(
                    code=code,
                    name=name,
                    description=description,
                    parent_id=parent_id,
                    level=level,
                    path=path,
                    manager=manager,
                    department=department,
                    budget_limit=budget_limit
                )
                
                session.add(cost_center)
                session.commit()
                session.refresh(cost_center)
                
                self.logger.info(f"✅ Created cost center: {code} - {name}")
                return cost_center
                
        except IntegrityError as e:
            self.logger.error(f"❌ Cost center creation failed (integrity): {e}")
            raise VirtualPnLDBError(f"Cost center with code '{code}' already exists")
        except Exception as e:
            self.logger.error(f"❌ Error creating cost center: {e}")
            raise VirtualPnLDBError(f"Failed to create cost center: {e}")
    
    async def _initialize_cost_centers(self):
        """初始化標準成本中心"""
        standard_cost_centers = [
            # 根級成本中心
            {
                'code': 'AI_SERVICES',
                'name': 'AI Services Division',
                'description': 'AI服務事業部',
                'department': 'Technology'
            },
            # GPT-OSS相關成本中心
            {
                'code': 'GPT_OSS',
                'name': 'GPT-OSS Local Inference',
                'description': 'GPT-OSS本地推理服務',
                'parent_code': 'AI_SERVICES',
                'department': 'AI Engineering'
            },
            {
                'code': 'GPT_HARDWARE',
                'name': 'GPT Hardware Infrastructure',
                'description': 'GPT硬體基礎設施',
                'parent_code': 'GPT_OSS',
                'department': 'Infrastructure'
            },
            {
                'code': 'GPT_OPERATIONS',
                'name': 'GPT Operations',
                'description': 'GPT運營維護',
                'parent_code': 'GPT_OSS',
                'department': 'Operations'
            },
            # 阿爾法引擎成本中心
            {
                'code': 'ALPHA_ENGINE',
                'name': 'Alpha Engine Premium',
                'description': '阿爾法引擎高級功能',
                'parent_code': 'AI_SERVICES',
                'department': 'Product'
            }
        ]
        
        try:
            with self.get_session() as session:
                # 創建成本中心映射
                created_centers = {}
                
                for center_data in standard_cost_centers:
                    code = center_data['code']
                    
                    # 檢查是否已存在
                    existing = session.query(CostCenter).filter(CostCenter.code == code).first()
                    if existing:
                        created_centers[code] = existing
                        continue
                    
                    # 處理父級關係
                    parent_id = None
                    if 'parent_code' in center_data:
                        parent_code = center_data['parent_code']
                        if parent_code in created_centers:
                            parent_id = created_centers[parent_code].id
                    
                    # 計算層級和路徑
                    level = 0
                    path = f"/{code}"
                    if parent_id:
                        parent = created_centers.get(center_data.get('parent_code'))
                        if parent:
                            level = parent.level + 1
                            path = f"{parent.path}/{code}"
                    
                    # 創建成本中心
                    cost_center = CostCenter(
                        code=code,
                        name=center_data['name'],
                        description=center_data.get('description'),
                        parent_id=parent_id,
                        level=level,
                        path=path,
                        department=center_data.get('department')
                    )
                    
                    session.add(cost_center)
                    session.flush()  # 獲取ID
                    created_centers[code] = cost_center
                
                session.commit()
                self.logger.info(f"✅ Initialized {len(created_centers)} cost centers")
                
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize cost centers: {e}")
    
    # ==================== 成本追蹤管理 ====================
    
    async def create_cost_tracking(
        self,
        cost_data: CostTrackingCreate,
        created_by: Optional[str] = None
    ) -> CostTracking:
        """創建成本追蹤記錄"""
        try:
            with self.get_session() as session:
                # 自動計算期間信息
                record_date = cost_data.record_date
                period_year = record_date.year
                period_quarter = (record_date.month - 1) // 3 + 1
                period_month = record_date.month
                
                cost_tracking = CostTracking(
                    cost_center_id=cost_data.cost_center_id,
                    record_date=record_date,
                    period_year=period_year,
                    period_quarter=period_quarter,
                    period_month=period_month,
                    cost_category=cost_data.cost_category.value,
                    cost_type=cost_data.cost_type.value,
                    cost_subcategory=cost_data.cost_subcategory,
                    amount=cost_data.amount,
                    currency=cost_data.currency,
                    description=cost_data.description,
                    cost_details=cost_data.cost_details,
                    allocation_method=cost_data.allocation_method.value if cost_data.allocation_method else None,
                    allocation_basis=cost_data.allocation_basis,
                    allocation_percentage=cost_data.allocation_percentage,
                    source_system=cost_data.source_system,
                    source_reference=cost_data.source_reference,
                    transaction_id=cost_data.transaction_id,
                    created_by=created_by
                )
                
                session.add(cost_tracking)
                session.commit()
                session.refresh(cost_tracking)
                
                # 觸發P&L匯總更新
                await self._update_pnl_summary_for_period(
                    cost_tracking.cost_center_id,
                    record_date,
                    session
                )
                
                self.logger.info(f"✅ Created cost tracking: {cost_data.cost_category.value} - ${cost_data.amount}")
                return cost_tracking
                
        except Exception as e:
            self.logger.error(f"❌ Error creating cost tracking: {e}")
            raise VirtualPnLDBError(f"Failed to create cost tracking: {e}")
    
    async def batch_create_cost_tracking(
        self,
        cost_records: List[CostTrackingCreate],
        created_by: Optional[str] = None
    ) -> List[CostTracking]:
        """批量創建成本追蹤記錄"""
        created_records = []
        
        try:
            with self.get_session() as session:
                for cost_data in cost_records:
                    record_date = cost_data.record_date
                    period_year = record_date.year
                    period_quarter = (record_date.month - 1) // 3 + 1
                    period_month = record_date.month
                    
                    cost_tracking = CostTracking(
                        cost_center_id=cost_data.cost_center_id,
                        record_date=record_date,
                        period_year=period_year,
                        period_quarter=period_quarter,
                        period_month=period_month,
                        cost_category=cost_data.cost_category.value,
                        cost_type=cost_data.cost_type.value,
                        cost_subcategory=cost_data.cost_subcategory,
                        amount=cost_data.amount,
                        currency=cost_data.currency,
                        description=cost_data.description,
                        cost_details=cost_data.cost_details,
                        allocation_method=cost_data.allocation_method.value if cost_data.allocation_method else None,
                        allocation_basis=cost_data.allocation_basis,
                        allocation_percentage=cost_data.allocation_percentage,
                        source_system=cost_data.source_system,
                        source_reference=cost_data.source_reference,
                        transaction_id=cost_data.transaction_id,
                        created_by=created_by
                    )
                    
                    session.add(cost_tracking)
                    created_records.append(cost_tracking)
                
                session.commit()
                
                # 批量刷新以獲取ID
                for record in created_records:
                    session.refresh(record)
                
                # 觸發相關P&L匯總更新
                affected_cost_centers = set()
                affected_dates = set()
                for record in created_records:
                    affected_cost_centers.add(record.cost_center_id)
                    affected_dates.add(record.record_date)
                
                for cost_center_id in affected_cost_centers:
                    for record_date in affected_dates:
                        await self._update_pnl_summary_for_period(
                            cost_center_id, record_date, session
                        )
                
                self.logger.info(f"✅ Batch created {len(created_records)} cost tracking records")
                return created_records
                
        except Exception as e:
            self.logger.error(f"❌ Error batch creating cost tracking: {e}")
            raise VirtualPnLDBError(f"Failed to batch create cost tracking: {e}")
    
    async def get_cost_analysis(
        self,
        request: CostAnalysisRequest
    ) -> Dict[str, Any]:
        """獲取成本分析報告"""
        try:
            with self.get_session() as session:
                query = session.query(CostTracking)
                
                # 時間過濾
                query = query.filter(
                    CostTracking.record_date >= request.start_date,
                    CostTracking.record_date <= request.end_date
                )
                
                # 成本中心過濾
                if request.cost_center_ids:
                    query = query.filter(CostTracking.cost_center_id.in_(request.cost_center_ids))
                
                # 成本類別過濾
                if request.cost_categories:
                    categories = [cat.value for cat in request.cost_categories]
                    query = query.filter(CostTracking.cost_category.in_(categories))
                
                # 貨幣過濾
                query = query.filter(CostTracking.currency == request.currency)
                
                # 獲取基礎數據
                cost_records = query.all()
                
                if not cost_records:
                    return {
                        'period': f"{request.start_date} to {request.end_date}",
                        'total_records': 0,
                        'total_cost': Decimal('0'),
                        'cost_by_category': {},
                        'cost_by_type': {},
                        'cost_by_period': {},
                        'trends': {}
                    }
                
                # 計算匯總統計
                total_cost = sum(record.amount for record in cost_records)
                
                # 按類別分組
                cost_by_category = {}
                for record in cost_records:
                    category = record.cost_category
                    if category not in cost_by_category:
                        cost_by_category[category] = {
                            'total': Decimal('0'),
                            'count': 0,
                            'percentage': 0
                        }
                    cost_by_category[category]['total'] += record.amount
                    cost_by_category[category]['count'] += 1
                
                # 計算百分比
                for category in cost_by_category:
                    if total_cost > 0:
                        cost_by_category[category]['percentage'] = float(
                            (cost_by_category[category]['total'] / total_cost) * 100
                        )
                
                # 按成本類型分組
                cost_by_type = {}
                for record in cost_records:
                    cost_type = record.cost_type
                    if cost_type not in cost_by_type:
                        cost_by_type[cost_type] = {
                            'total': Decimal('0'),
                            'count': 0
                        }
                    cost_by_type[cost_type]['total'] += record.amount
                    cost_by_type[cost_type]['count'] += 1
                
                # 按週期分組
                cost_by_period = {}
                if request.period_type == "monthly":
                    for record in cost_records:
                        period_key = f"{record.period_year}-{record.period_month:02d}"
                        if period_key not in cost_by_period:
                            cost_by_period[period_key] = Decimal('0')
                        cost_by_period[period_key] += record.amount
                elif request.period_type == "quarterly":
                    for record in cost_records:
                        period_key = f"{record.period_year}-Q{record.period_quarter}"
                        if period_key not in cost_by_period:
                            cost_by_period[period_key] = Decimal('0')
                        cost_by_period[period_key] += record.amount
                
                # 計算趨勢
                trends = self._calculate_cost_trends(cost_by_period)
                
                analysis_result = {
                    'period': f"{request.start_date} to {request.end_date}",
                    'total_records': len(cost_records),
                    'total_cost': float(total_cost),
                    'currency': request.currency,
                    'cost_by_category': {
                        k: {
                            'total': float(v['total']),
                            'count': v['count'],
                            'percentage': v['percentage']
                        }
                        for k, v in cost_by_category.items()
                    },
                    'cost_by_type': {
                        k: {
                            'total': float(v['total']),
                            'count': v['count']
                        }
                        for k, v in cost_by_type.items()
                    },
                    'cost_by_period': {
                        k: float(v) for k, v in cost_by_period.items()
                    },
                    'trends': trends,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
                
                return analysis_result
                
        except Exception as e:
            self.logger.error(f"❌ Error generating cost analysis: {e}")
            raise VirtualPnLDBError(f"Failed to generate cost analysis: {e}")
    
    # ==================== 收益歸因管理 ====================
    
    async def create_revenue_attribution(
        self,
        revenue_data: RevenueAttributionCreate,
        created_by: Optional[str] = None
    ) -> RevenueAttribution:
        """創建收益歸因記錄"""
        try:
            with self.get_session() as session:
                # 自動計算期間信息
                record_date = revenue_data.record_date
                period_year = record_date.year
                period_quarter = (record_date.month - 1) // 3 + 1
                period_month = record_date.month
                
                revenue_attribution = RevenueAttribution(
                    record_date=record_date,
                    period_year=period_year,
                    period_quarter=period_quarter,
                    period_month=period_month,
                    revenue_source=revenue_data.revenue_source.value,
                    revenue_subcategory=revenue_data.revenue_subcategory,
                    amount=revenue_data.amount,
                    currency=revenue_data.currency,
                    attribution_method=revenue_data.attribution_method,
                    attribution_confidence=revenue_data.attribution_confidence,
                    gpt_oss_contribution_ratio=revenue_data.gpt_oss_contribution_ratio,
                    customer_id=revenue_data.customer_id,
                    customer_tier=revenue_data.customer_tier,
                    product_feature=revenue_data.product_feature,
                    description=revenue_data.description,
                    revenue_details=revenue_data.revenue_details,
                    baseline_period=revenue_data.baseline_period,
                    baseline_amount=revenue_data.baseline_amount,
                    incremental_amount=revenue_data.incremental_amount,
                    created_by=created_by
                )
                
                session.add(revenue_attribution)
                session.commit()
                session.refresh(revenue_attribution)
                
                self.logger.info(f"✅ Created revenue attribution: {revenue_data.revenue_source.value} - ${revenue_data.amount}")
                return revenue_attribution
                
        except Exception as e:
            self.logger.error(f"❌ Error creating revenue attribution: {e}")
            raise VirtualPnLDBError(f"Failed to create revenue attribution: {e}")
    
    async def calculate_incremental_revenue(
        self,
        revenue_source: RevenueSource,
        current_period_start: date,
        current_period_end: date,
        baseline_period_start: date,
        baseline_period_end: date,
        gpt_oss_launch_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """計算增量收益"""
        try:
            with self.get_session() as session:
                # 獲取當前期間收益
                current_revenue = session.query(
                    func.sum(RevenueAttribution.amount).label('total_amount'),
                    func.count(RevenueAttribution.id).label('record_count')
                ).filter(
                    RevenueAttribution.revenue_source == revenue_source.value,
                    RevenueAttribution.record_date >= current_period_start,
                    RevenueAttribution.record_date <= current_period_end
                ).first()
                
                # 獲取基準期間收益
                baseline_revenue = session.query(
                    func.sum(RevenueAttribution.amount).label('total_amount'),
                    func.count(RevenueAttribution.id).label('record_count')
                ).filter(
                    RevenueAttribution.revenue_source == revenue_source.value,
                    RevenueAttribution.record_date >= baseline_period_start,
                    RevenueAttribution.record_date <= baseline_period_end
                ).first()
                
                current_total = current_revenue.total_amount or Decimal('0')
                baseline_total = baseline_revenue.total_amount or Decimal('0')
                
                # 計算增量
                absolute_increase = current_total - baseline_total
                percentage_increase = 0
                if baseline_total > 0:
                    percentage_increase = float((absolute_increase / baseline_total) * 100)
                
                # 歸因到GPT-OSS的部分
                gpt_oss_attributed_amount = Decimal('0')
                if gpt_oss_launch_date and current_period_start >= gpt_oss_launch_date:
                    # 如果當前期間在GPT-OSS啟動之後，更高比例歸因給GPT-OSS
                    gpt_oss_attributed_amount = absolute_increase * Decimal('0.8')
                elif absolute_increase > 0:
                    # 保守歸因
                    gpt_oss_attributed_amount = absolute_increase * Decimal('0.5')
                
                result = {
                    'revenue_source': revenue_source.value,
                    'analysis_period': {
                        'current': f"{current_period_start} to {current_period_end}",
                        'baseline': f"{baseline_period_start} to {baseline_period_end}"
                    },
                    'current_revenue': float(current_total),
                    'baseline_revenue': float(baseline_total),
                    'absolute_increase': float(absolute_increase),
                    'percentage_increase': percentage_increase,
                    'gpt_oss_attributed_amount': float(gpt_oss_attributed_amount),
                    'gpt_oss_attribution_ratio': float(gpt_oss_attributed_amount / absolute_increase) if absolute_increase > 0 else 0,
                    'confidence_score': 0.8 if gpt_oss_launch_date and current_period_start >= gpt_oss_launch_date else 0.6,
                    'calculated_at': datetime.now(timezone.utc).isoformat()
                }
                
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating incremental revenue: {e}")
            raise VirtualPnLDBError(f"Failed to calculate incremental revenue: {e}")
    
    # ==================== 預算管理 ====================
    
    async def create_budget_allocation(
        self,
        budget_data: BudgetAllocationCreate,
        created_by: Optional[str] = None
    ) -> BudgetAllocation:
        """創建預算分配"""
        try:
            with self.get_session() as session:
                budget_allocation = BudgetAllocation(
                    cost_center_id=budget_data.cost_center_id,
                    budget_year=budget_data.budget_year,
                    budget_period_type=budget_data.budget_period_type.value,
                    budget_period=budget_data.budget_period,
                    total_budget=budget_data.total_budget,
                    currency=budget_data.currency,
                    hardware_budget=budget_data.hardware_budget,
                    infrastructure_budget=budget_data.infrastructure_budget,
                    power_budget=budget_data.power_budget,
                    personnel_budget=budget_data.personnel_budget,
                    maintenance_budget=budget_data.maintenance_budget,
                    software_budget=budget_data.software_budget,
                    other_budget=budget_data.other_budget,
                    revenue_target=budget_data.revenue_target,
                    cost_savings_target=budget_data.cost_savings_target,
                    roi_target=budget_data.roi_target,
                    description=budget_data.description,
                    budget_details=budget_data.budget_details,
                    assumptions=budget_data.assumptions,
                    created_by=created_by
                )
                
                session.add(budget_allocation)
                session.commit()
                session.refresh(budget_allocation)
                
                self.logger.info(f"✅ Created budget allocation: {budget_data.budget_period_type.value} {budget_data.budget_year} - ${budget_data.total_budget}")
                return budget_allocation
                
        except IntegrityError as e:
            self.logger.error(f"❌ Budget allocation creation failed (integrity): {e}")
            raise VirtualPnLDBError("Budget allocation for this period already exists")
        except Exception as e:
            self.logger.error(f"❌ Error creating budget allocation: {e}")
            raise VirtualPnLDBError(f"Failed to create budget allocation: {e}")
    
    async def get_budget_utilization(
        self,
        cost_center_id: uuid.UUID,
        budget_year: int,
        budget_period_type: BudgetPeriodType,
        budget_period: Optional[int] = None
    ) -> Dict[str, Any]:
        """獲取預算使用率分析"""
        try:
            with self.get_session() as session:
                # 獲取預算分配
                budget_query = session.query(BudgetAllocation).filter(
                    BudgetAllocation.cost_center_id == cost_center_id,
                    BudgetAllocation.budget_year == budget_year,
                    BudgetAllocation.budget_period_type == budget_period_type.value
                )
                
                if budget_period is not None:
                    budget_query = budget_query.filter(BudgetAllocation.budget_period == budget_period)
                
                budget = budget_query.first()
                
                if not budget:
                    raise VirtualPnLDBError("Budget allocation not found")
                
                # 計算實際支出
                cost_query = session.query(CostTracking).filter(
                    CostTracking.cost_center_id == cost_center_id,
                    CostTracking.period_year == budget_year
                )
                
                # 根據預算週期類型調整查詢
                if budget_period_type == BudgetPeriodType.QUARTERLY and budget_period:
                    cost_query = cost_query.filter(CostTracking.period_quarter == budget_period)
                elif budget_period_type == BudgetPeriodType.MONTHLY and budget_period:
                    cost_query = cost_query.filter(CostTracking.period_month == budget_period)
                
                # 按類別統計實際支出
                actual_costs = {}
                category_mapping = {
                    CostCategory.HARDWARE: 'hardware_budget',
                    CostCategory.INFRASTRUCTURE: 'infrastructure_budget', 
                    CostCategory.POWER: 'power_budget',
                    CostCategory.PERSONNEL: 'personnel_budget',
                    CostCategory.MAINTENANCE: 'maintenance_budget',
                    CostCategory.SOFTWARE: 'software_budget'
                }
                
                for cost_category, budget_field in category_mapping.items():
                    category_costs = cost_query.filter(
                        CostTracking.cost_category == cost_category.value
                    ).all()
                    
                    total_actual = sum(cost.amount for cost in category_costs)
                    budget_allocated = getattr(budget, budget_field) or Decimal('0')
                    
                    utilization_rate = 0
                    if budget_allocated > 0:
                        utilization_rate = float((total_actual / budget_allocated) * 100)
                    
                    actual_costs[cost_category.value] = {
                        'budget_allocated': float(budget_allocated),
                        'actual_spent': float(total_actual),
                        'remaining_budget': float(budget_allocated - total_actual),
                        'utilization_rate': utilization_rate,
                        'is_over_budget': total_actual > budget_allocated
                    }
                
                # 總體預算使用率
                total_actual = sum(cost.amount for cost in cost_query.all())
                total_budget = budget.total_budget
                overall_utilization = float((total_actual / total_budget) * 100) if total_budget > 0 else 0
                
                result = {
                    'cost_center_id': str(cost_center_id),
                    'budget_period': {
                        'year': budget_year,
                        'type': budget_period_type.value,
                        'period': budget_period
                    },
                    'total_budget': float(total_budget),
                    'total_actual': float(total_actual),
                    'total_remaining': float(total_budget - total_actual),
                    'overall_utilization_rate': overall_utilization,
                    'is_over_budget': total_actual > total_budget,
                    'category_breakdown': actual_costs,
                    'budget_status': budget.budget_status,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
                
                return result
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating budget utilization: {e}")
            raise VirtualPnLDBError(f"Failed to calculate budget utilization: {e}")
    
    # ==================== P&L報告生成 ====================
    
    async def _update_pnl_summary_for_period(
        self,
        cost_center_id: uuid.UUID,
        record_date: date,
        session: Optional[Session] = None
    ):
        """更新指定期間的P&L匯總"""
        def _update_with_session(s: Session):
            period_year = record_date.year
            period_quarter = (record_date.month - 1) // 3 + 1
            period_month = record_date.month
            
            # 更新月度匯總
            self._update_monthly_pnl_summary(
                s, cost_center_id, record_date, period_year, period_quarter, period_month
            )
            
            # 更新季度匯總
            quarter_start = date(period_year, (period_quarter - 1) * 3 + 1, 1)
            self._update_quarterly_pnl_summary(
                s, cost_center_id, quarter_start, period_year, period_quarter
            )
            
            # 更新年度匯總
            year_start = date(period_year, 1, 1)
            self._update_annual_pnl_summary(
                s, cost_center_id, year_start, period_year
            )
        
        if session:
            _update_with_session(session)
        else:
            with self.get_session() as s:
                _update_with_session(s)
                s.commit()
    
    def _update_monthly_pnl_summary(
        self,
        session: Session,
        cost_center_id: uuid.UUID,
        summary_date: date,
        period_year: int,
        period_quarter: int,
        period_month: int
    ):
        """更新月度P&L匯總"""
        # 查找或創建月度匯總記錄
        pnl_summary = session.query(VirtualPnLSummary).filter(
            VirtualPnLSummary.cost_center_id == cost_center_id,
            VirtualPnLSummary.period_year == period_year,
            VirtualPnLSummary.period_quarter == period_quarter,
            VirtualPnLSummary.period_month == period_month,
            VirtualPnLSummary.period_type == 'monthly'
        ).first()
        
        if not pnl_summary:
            pnl_summary = VirtualPnLSummary(
                cost_center_id=cost_center_id,
                summary_date=summary_date,
                period_year=period_year,
                period_quarter=period_quarter,
                period_month=period_month,
                period_type='monthly'
            )
            session.add(pnl_summary)
        
        # 計算月度成本
        month_start = date(period_year, period_month, 1)
        if period_month == 12:
            month_end = date(period_year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(period_year, period_month + 1, 1) - timedelta(days=1)
        
        cost_query = session.query(CostTracking).filter(
            CostTracking.cost_center_id == cost_center_id,
            CostTracking.record_date >= month_start,
            CostTracking.record_date <= month_end
        )
        
        # 按類別統計成本
        cost_totals = {
            'total': Decimal('0'),
            'hardware': Decimal('0'),
            'infrastructure': Decimal('0'),
            'power': Decimal('0'),
            'personnel': Decimal('0'),
            'maintenance': Decimal('0'),
            'software': Decimal('0'),
            'cloud_fallback': Decimal('0'),
            'other': Decimal('0')
        }
        
        for cost in cost_query.all():
            cost_totals['total'] += cost.amount
            
            category = cost.cost_category.lower()
            if category in cost_totals:
                cost_totals[category] += cost.amount
            else:
                cost_totals['other'] += cost.amount
        
        # 更新成本字段
        pnl_summary.total_costs = cost_totals['total']
        pnl_summary.hardware_costs = cost_totals['hardware']
        pnl_summary.infrastructure_costs = cost_totals['infrastructure']
        pnl_summary.power_costs = cost_totals['power']
        pnl_summary.personnel_costs = cost_totals['personnel']
        pnl_summary.maintenance_costs = cost_totals['maintenance']
        pnl_summary.software_costs = cost_totals['software']
        pnl_summary.cloud_fallback_costs = cost_totals['cloud_fallback']
        pnl_summary.other_costs = cost_totals['other']
        
        # 計算月度收益
        revenue_query = session.query(RevenueAttribution).filter(
            RevenueAttribution.record_date >= month_start,
            RevenueAttribution.record_date <= month_end
        )
        
        revenue_totals = {
            'total': Decimal('0'),
            'membership_upgrade': Decimal('0'),
            'alpha_engine_premium': Decimal('0'),
            'api_usage_fees': Decimal('0'),
            'cost_savings': Decimal('0'),
            'other': Decimal('0')
        }
        
        for revenue in revenue_query.all():
            revenue_totals['total'] += revenue.amount
            
            source = revenue.revenue_source.lower()
            if source in revenue_totals:
                revenue_totals[source] += revenue.amount
            else:
                revenue_totals['other'] += revenue.amount
        
        # 更新收益字段
        pnl_summary.total_revenues = revenue_totals['total']
        pnl_summary.membership_revenue = revenue_totals['membership_upgrade']
        pnl_summary.alpha_engine_revenue = revenue_totals['alpha_engine_premium']
        pnl_summary.api_usage_revenue = revenue_totals['api_usage_fees']
        pnl_summary.cost_savings_revenue = revenue_totals['cost_savings']
        pnl_summary.other_revenue = revenue_totals['other']
        
        # 計算損益指標
        pnl_summary.gross_profit = pnl_summary.total_revenues - pnl_summary.total_costs
        pnl_summary.net_profit = pnl_summary.gross_profit  # 簡化處理
        
        if pnl_summary.total_revenues > 0:
            pnl_summary.profit_margin = (pnl_summary.net_profit / pnl_summary.total_revenues) * 100
        
        if pnl_summary.total_costs > 0:
            pnl_summary.roi = (pnl_summary.net_profit / pnl_summary.total_costs) * 100
        
        pnl_summary.last_updated = datetime.now(timezone.utc)
    
    def _update_quarterly_pnl_summary(
        self,
        session: Session,
        cost_center_id: uuid.UUID,
        summary_date: date,
        period_year: int,
        period_quarter: int
    ):
        """更新季度P&L匯總 - 簡化實現"""
        pass  # 類似月度邏輯，但統計整個季度的數據
    
    def _update_annual_pnl_summary(
        self,
        session: Session,
        cost_center_id: uuid.UUID,
        summary_date: date,
        period_year: int
    ):
        """更新年度P&L匯總 - 簡化實現"""
        pass  # 類似月度邏輯，但統計整年的數據
    
    async def get_pnl_report(
        self,
        cost_center_ids: Optional[List[uuid.UUID]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period_type: str = "monthly",
        include_consolidated: bool = False
    ) -> Dict[str, Any]:
        """生成P&L報告"""
        try:
            with self.get_session() as session:
                query = session.query(VirtualPnLSummary)
                
                # 過濾條件
                if cost_center_ids:
                    query = query.filter(VirtualPnLSummary.cost_center_id.in_(cost_center_ids))
                
                if start_date:
                    query = query.filter(VirtualPnLSummary.summary_date >= start_date)
                
                if end_date:
                    query = query.filter(VirtualPnLSummary.summary_date <= end_date)
                
                query = query.filter(VirtualPnLSummary.period_type == period_type)
                
                if not include_consolidated:
                    query = query.filter(VirtualPnLSummary.is_consolidated == False)
                
                pnl_records = query.order_by(
                    VirtualPnLSummary.summary_date.desc()
                ).all()
                
                if not pnl_records:
                    return {
                        'summary': {
                            'total_periods': 0,
                            'total_costs': 0,
                            'total_revenues': 0,
                            'net_profit': 0,
                            'average_roi': 0
                        },
                        'details': [],
                        'generated_at': datetime.now(timezone.utc).isoformat()
                    }
                
                # 計算匯總統計
                total_costs = sum(record.total_costs for record in pnl_records)
                total_revenues = sum(record.total_revenues for record in pnl_records)
                total_net_profit = sum(record.net_profit for record in pnl_records)
                
                roi_values = [record.roi for record in pnl_records if record.roi is not None]
                average_roi = sum(roi_values) / len(roi_values) if roi_values else 0
                
                # 轉換為響應格式
                details = []
                for record in pnl_records:
                    details.append({
                        'cost_center_id': str(record.cost_center_id),
                        'period': f"{record.period_year}-{record.period_quarter:02d}-{record.period_month:02d}",
                        'total_costs': float(record.total_costs),
                        'total_revenues': float(record.total_revenues),
                        'net_profit': float(record.net_profit),
                        'profit_margin': float(record.profit_margin) if record.profit_margin else None,
                        'roi': float(record.roi) if record.roi else None,
                        'cost_breakdown': {
                            'hardware': float(record.hardware_costs),
                            'infrastructure': float(record.infrastructure_costs),
                            'power': float(record.power_costs),
                            'personnel': float(record.personnel_costs),
                            'maintenance': float(record.maintenance_costs),
                            'software': float(record.software_costs),
                            'cloud_fallback': float(record.cloud_fallback_costs),
                            'other': float(record.other_costs)
                        },
                        'revenue_breakdown': {
                            'membership': float(record.membership_revenue),
                            'alpha_engine': float(record.alpha_engine_revenue),
                            'api_usage': float(record.api_usage_revenue),
                            'cost_savings': float(record.cost_savings_revenue),
                            'other': float(record.other_revenue)
                        }
                    })
                
                report = {
                    'summary': {
                        'total_periods': len(pnl_records),
                        'total_costs': float(total_costs),
                        'total_revenues': float(total_revenues),
                        'net_profit': float(total_net_profit),
                        'average_roi': average_roi,
                        'period_type': period_type
                    },
                    'details': details,
                    'generated_at': datetime.now(timezone.utc).isoformat()
                }
                
                return report
                
        except Exception as e:
            self.logger.error(f"❌ Error generating P&L report: {e}")
            raise VirtualPnLDBError(f"Failed to generate P&L report: {e}")
    
    # ==================== ROI和成本效益分析 ====================
    
    async def calculate_roi_analysis(
        self,
        request: ROIAnalysisRequest
    ) -> Dict[str, Any]:
        """計算ROI分析"""
        try:
            with self.get_session() as session:
                # 獲取分析期間的成本和收益
                analysis_costs = await self._get_period_costs(
                    session, request.cost_center_ids, 
                    request.analysis_period_start, request.analysis_period_end
                )
                
                analysis_revenues = await self._get_period_revenues(
                    session, request.analysis_period_start, request.analysis_period_end
                )
                
                # 獲取基準期間數據（如果提供）
                baseline_costs = Decimal('0')
                baseline_revenues = Decimal('0')
                
                if request.baseline_period_start and request.baseline_period_end:
                    baseline_costs = await self._get_period_costs(
                        session, request.cost_center_ids,
                        request.baseline_period_start, request.baseline_period_end
                    )
                    baseline_revenues = await self._get_period_revenues(
                        session, request.baseline_period_start, request.baseline_period_end
                    )
                
                # 計算ROI指標
                total_investment = analysis_costs
                total_return = analysis_revenues
                net_profit = total_return - total_investment
                
                # 基礎ROI
                roi_percentage = 0
                if total_investment > 0:
                    roi_percentage = float((net_profit / total_investment) * 100)
                
                # 增量ROI（如果有基準期間）
                incremental_roi = 0
                if baseline_costs > 0 and baseline_revenues > 0:
                    incremental_investment = analysis_costs - baseline_costs
                    incremental_return = analysis_revenues - baseline_revenues
                    incremental_profit = incremental_return - incremental_investment
                    
                    if incremental_investment > 0:
                        incremental_roi = float((incremental_profit / incremental_investment) * 100)
                
                # NPV計算（如果提供折現率）
                npv = float(net_profit)
                if request.discount_rate:
                    # 簡化NPV計算 - 假設單期
                    discount_factor = 1 / (1 + float(request.discount_rate))
                    npv = float(net_profit) * discount_factor
                
                # 回收期計算
                payback_months = None
                if analysis_revenues > analysis_costs:
                    monthly_net_cash_flow = (analysis_revenues - analysis_costs) / 12  # 假設均勻分佈
                    if monthly_net_cash_flow > 0:
                        payback_months = float(analysis_costs / monthly_net_cash_flow)
                
                # 成本節省分析
                cost_savings_analysis = await self._calculate_cost_savings_analysis(
                    session, request.analysis_period_start, request.analysis_period_end
                )
                
                roi_analysis = {
                    'analysis_period': f"{request.analysis_period_start} to {request.analysis_period_end}",
                    'baseline_period': f"{request.baseline_period_start} to {request.baseline_period_end}" if request.baseline_period_start else None,
                    'financial_metrics': {
                        'total_investment': float(total_investment),
                        'total_return': float(total_return),
                        'net_profit': float(net_profit),
                        'roi_percentage': roi_percentage,
                        'incremental_roi': incremental_roi,
                        'npv': npv,
                        'payback_months': payback_months
                    },
                    'cost_savings_analysis': cost_savings_analysis,
                    'soft_benefits': [] if not request.include_soft_benefits else [
                        {
                            'benefit': 'Data Privacy Enhancement',
                            'description': '本地推理提供更好的數據隱私保護',
                            'estimated_value': 'Qualitative'
                        },
                        {
                            'benefit': 'Service Reliability',
                            'description': '減少對外部API的依賴，提高服務可靠性',
                            'estimated_value': 'Qualitative'
                        }
                    ],
                    'recommendations': self._generate_roi_recommendations(roi_percentage, payback_months),
                    'calculated_at': datetime.now(timezone.utc).isoformat()
                }
                
                return roi_analysis
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating ROI analysis: {e}")
            raise VirtualPnLDBError(f"Failed to calculate ROI analysis: {e}")
    
    # ==================== 輔助方法 ====================
    
    async def _get_period_costs(
        self,
        session: Session,
        cost_center_ids: Optional[List[uuid.UUID]],
        start_date: date,
        end_date: date
    ) -> Decimal:
        """獲取指定期間的總成本"""
        query = session.query(func.sum(CostTracking.amount)).filter(
            CostTracking.record_date >= start_date,
            CostTracking.record_date <= end_date
        )
        
        if cost_center_ids:
            query = query.filter(CostTracking.cost_center_id.in_(cost_center_ids))
        
        result = query.scalar()
        return result or Decimal('0')
    
    async def _get_period_revenues(
        self,
        session: Session,
        start_date: date,
        end_date: date
    ) -> Decimal:
        """獲取指定期間的總收益"""
        result = session.query(func.sum(RevenueAttribution.amount)).filter(
            RevenueAttribution.record_date >= start_date,
            RevenueAttribution.record_date <= end_date
        ).scalar()
        
        return result or Decimal('0')
    
    async def _calculate_cost_savings_analysis(
        self,
        session: Session,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """計算成本節省分析"""
        # 獲取成本節省類型的收益
        cost_savings = session.query(func.sum(RevenueAttribution.amount)).filter(
            RevenueAttribution.record_date >= start_date,
            RevenueAttribution.record_date <= end_date,
            RevenueAttribution.revenue_source == RevenueSource.COST_SAVINGS.value
        ).scalar() or Decimal('0')
        
        # 獲取雲端後備成本
        cloud_costs = session.query(func.sum(CostTracking.amount)).filter(
            CostTracking.record_date >= start_date,
            CostTracking.record_date <= end_date,
            CostTracking.cost_category == CostCategory.CLOUD_FALLBACK.value
        ).scalar() or Decimal('0')
        
        return {
            'total_cost_savings': float(cost_savings),
            'cloud_fallback_costs': float(cloud_costs),
            'net_savings': float(cost_savings - cloud_costs),
            'savings_rate': float((cost_savings - cloud_costs) / cost_savings * 100) if cost_savings > 0 else 0
        }
    
    def _calculate_cost_trends(self, cost_by_period: Dict[str, Decimal]) -> Dict[str, Any]:
        """計算成本趨勢"""
        if len(cost_by_period) < 2:
            return {'trend': 'insufficient_data'}
        
        periods = sorted(cost_by_period.keys())
        values = [float(cost_by_period[period]) for period in periods]
        
        # 簡單線性趨勢計算
        if len(values) >= 2:
            recent_avg = sum(values[-3:]) / min(3, len(values))
            earlier_avg = sum(values[:-3]) / max(1, len(values) - 3) if len(values) > 3 else values[0]
            
            if earlier_avg > 0:
                trend_percentage = ((recent_avg - earlier_avg) / earlier_avg) * 100
            else:
                trend_percentage = 0
            
            return {
                'trend': 'increasing' if trend_percentage > 5 else 'decreasing' if trend_percentage < -5 else 'stable',
                'trend_percentage': trend_percentage,
                'recent_average': recent_avg,
                'earlier_average': earlier_avg
            }
        
        return {'trend': 'stable'}
    
    def _generate_roi_recommendations(
        self,
        roi_percentage: float,
        payback_months: Optional[float]
    ) -> List[str]:
        """生成ROI建議"""
        recommendations = []
        
        if roi_percentage > 50:
            recommendations.append("ROI表現優秀，建議擴大GPT-OSS部署規模")
        elif roi_percentage > 20:
            recommendations.append("ROI表現良好，建議持續優化運營效率")
        elif roi_percentage > 0:
            recommendations.append("ROI為正但偏低，建議分析成本結構尋找優化空間")
        else:
            recommendations.append("ROI為負，建議重新評估投資策略或改進收益模式")
        
        if payback_months and payback_months < 12:
            recommendations.append("投資回收期短於1年，投資風險較低")
        elif payback_months and payback_months > 24:
            recommendations.append("投資回收期較長，建議加強收益增長策略")
        
        return recommendations
    
    # ==================== 健康檢查 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """虛擬P&L系統健康檢查"""
        health_status = {
            'system': 'virtual_pnl',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'components': {}
        }
        
        try:
            with self.get_session() as session:
                # 檢查數據庫連接
                session.execute(text("SELECT 1"))
                health_status['components']['database'] = 'healthy'
                
                # 檢查核心表數據
                cost_center_count = session.query(CostCenter).count()
                cost_tracking_count = session.query(CostTracking).count()
                revenue_count = session.query(RevenueAttribution).count()
                budget_count = session.query(BudgetAllocation).count()
                pnl_count = session.query(VirtualPnLSummary).count()
                
                health_status['components']['data_counts'] = {
                    'cost_centers': cost_center_count,
                    'cost_tracking_records': cost_tracking_count,
                    'revenue_attributions': revenue_count,
                    'budget_allocations': budget_count,
                    'pnl_summaries': pnl_count
                }
                
                # 檢查最近的數據更新
                latest_cost = session.query(
                    func.max(CostTracking.created_at)
                ).scalar()
                
                latest_revenue = session.query(
                    func.max(RevenueAttribution.created_at)
                ).scalar()
                
                health_status['components']['latest_updates'] = {
                    'latest_cost_record': latest_cost.isoformat() if latest_cost else None,
                    'latest_revenue_record': latest_revenue.isoformat() if latest_revenue else None
                }
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Virtual P&L health check failed: {e}")
        
        return health_status