#!/usr/bin/env python3
"""
Revenue Attribution Database Manager
GPT-OSS收益歸因數據庫管理器 - 任務2.1.3

企業級收益歸因數據庫管理系統，提供：
- 高性能收益歸因數據CRUD操作
- 複雜查詢和聚合分析
- 數據完整性和一致性保障
- 事務管理和錯誤處理
- 性能優化和緩存機制
- 審計追蹤和版本控制
"""

import uuid
import logging
import asyncio
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from contextlib import asynccontextmanager
from dataclasses import dataclass
import json

from sqlalchemy import (
    and_, or_, func, desc, asc, extract, 
    select, insert, update, delete, exists
)
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.dialects.postgresql import UUID

from .database import get_db_session, DatabaseError
from .revenue_attribution_models import (
    GPTOSSRevenueAttribution, APICostSavings, NewFeatureRevenue,
    MembershipUpgradeAttribution, RevenueForecast,
    GPTOSSRevenueAttributionCreate, APICostSavingsCreate,
    RevenueType, AttributionMethod, RevenueConfidence,
    CustomerSegment, FeatureCategory
)

logger = logging.getLogger(__name__)

# ==================== 異常定義 ====================

class RevenueAttributionDBError(DatabaseError):
    """收益歸因數據庫錯誤基類"""
    pass

class DuplicateAttributionError(RevenueAttributionDBError):
    """重複歸因記錄錯誤"""
    pass

class AttributionNotFoundError(RevenueAttributionDBError):
    """歸因記錄未找到錯誤"""
    pass

class InvalidAttributionDataError(RevenueAttributionDBError):
    """無效歸因數據錯誤"""
    pass

class AttributionValidationError(RevenueAttributionDBError):
    """歸因驗證錯誤"""
    pass

# ==================== 查詢結果數據類 ====================

@dataclass
class RevenueAttributionSummary:
    """收益歸因摘要"""
    period_start: date
    period_end: date
    total_attributed_revenue: Decimal
    total_incremental_revenue: Decimal
    attribution_count: int
    avg_confidence_score: float
    top_revenue_types: List[Dict[str, Any]]
    customer_segment_breakdown: Dict[str, Decimal]
    monthly_trend: List[Dict[str, Any]]

@dataclass
class APISavingsAnalysis:
    """API節省分析結果"""
    period_start: date
    period_end: date
    total_local_cost: Decimal
    total_cloud_cost: Decimal
    total_savings: Decimal
    savings_percentage: float
    avg_savings_per_request: Decimal
    requests_analyzed: int
    quality_improvement: Optional[float]

@dataclass
class FeatureRevenueImpact:
    """功能收益影響分析"""
    feature_name: str
    feature_category: str
    total_revenue: Decimal
    user_adoption_rate: float
    roi: Optional[float]
    launch_date: date
    revenue_growth_rate: Optional[float]

# ==================== 主要數據庫管理器 ====================

class RevenueAttributionDB:
    """
    收益歸因數據庫管理器
    
    功能：
    1. 高性能收益歸因數據CRUD操作
    2. 複雜查詢和聚合分析
    3. 數據完整性和一致性保障
    4. 事務管理和錯誤處理
    5. 性能優化和緩存機制
    6. 審計追蹤和版本控制
    """
    
    def __init__(self):
        """初始化收益歸因數據庫管理器"""
        self.logger = logger
        
        # 性能配置
        self.config = {
            'default_page_size': 50,
            'max_page_size': 1000,
            'query_timeout_seconds': 30,
            'batch_insert_size': 100,
            'enable_query_cache': True,
            'cache_ttl_seconds': 300,
            'enable_metrics': True
        }
        
        # 查詢緩存
        self.query_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        self.logger.info("✅ Revenue Attribution DB initialized")
    
    # ==================== GPT-OSS收益歸因主表操作 ====================
    
    async def create_revenue_attribution(
        self,
        attribution_data: GPTOSSRevenueAttributionCreate,
        creator_id: Optional[str] = None
    ) -> GPTOSSRevenueAttribution:
        """創建收益歸因記錄"""
        try:
            async with get_db_session() as session:
                # 檢查重複記錄
                existing = await session.execute(
                    select(GPTOSSRevenueAttribution).where(
                        GPTOSSRevenueAttribution.attribution_id == attribution_data.attribution_id
                    )
                )
                if existing.scalar_one_or_none():
                    raise DuplicateAttributionError(f"Attribution ID already exists: {attribution_data.attribution_id}")
                
                # 計算期間信息
                period_start = attribution_data.attribution_period_start
                period_end = attribution_data.attribution_period_end
                
                # 創建新記錄
                new_attribution = GPTOSSRevenueAttribution(
                    attribution_id=attribution_data.attribution_id,
                    record_date=attribution_data.record_date,
                    attribution_period_start=period_start,
                    attribution_period_end=period_end,
                    period_year=period_start.year,
                    period_quarter=((period_start.month - 1) // 3) + 1,
                    period_month=period_start.month,
                    
                    # 收益信息
                    revenue_type=attribution_data.revenue_type.value,
                    revenue_category=attribution_data.revenue_category,
                    feature_category=attribution_data.feature_category.value if attribution_data.feature_category else None,
                    total_revenue_amount=attribution_data.total_revenue_amount,
                    gpt_oss_attributed_amount=attribution_data.gpt_oss_attributed_amount,
                    baseline_amount=attribution_data.baseline_amount,
                    incremental_amount=attribution_data.incremental_amount,
                    currency=attribution_data.currency,
                    
                    # 歸因信息
                    attribution_method=attribution_data.attribution_method.value,
                    attribution_confidence=attribution_data.attribution_confidence.value,
                    confidence_score=attribution_data.confidence_score,
                    gpt_oss_contribution_ratio=attribution_data.gpt_oss_contribution_ratio,
                    
                    # 客戶信息
                    customer_segment=attribution_data.customer_segment.value if attribution_data.customer_segment else None,
                    customer_count=attribution_data.customer_count,
                    affected_users=attribution_data.affected_users,
                    new_customers=attribution_data.new_customers,
                    upgraded_customers=attribution_data.upgraded_customers,
                    
                    # GPT-OSS信息
                    gpt_oss_model_used=attribution_data.gpt_oss_model_used,
                    gpt_oss_feature_used=attribution_data.gpt_oss_feature_used,
                    inference_count=attribution_data.inference_count,
                    tokens_processed=attribution_data.tokens_processed,
                    response_quality_score=attribution_data.response_quality_score,
                    
                    # 比較信息
                    baseline_period_start=attribution_data.baseline_period_start,
                    baseline_period_end=attribution_data.baseline_period_end,
                    comparison_metric=attribution_data.comparison_metric,
                    improvement_percentage=attribution_data.improvement_percentage,
                    
                    # 詳細信息
                    description=attribution_data.description,
                    attribution_details=attribution_data.attribution_details,
                    revenue_breakdown=attribution_data.revenue_breakdown,
                    supporting_metrics=attribution_data.supporting_metrics,
                    
                    # 來源信息
                    data_source=attribution_data.data_source,
                    source_reference=attribution_data.source_reference,
                    calculation_method=attribution_data.calculation_method,
                    
                    # 審計信息
                    created_by=creator_id
                )
                
                session.add(new_attribution)
                await session.commit()
                await session.refresh(new_attribution)
                
                self.logger.info(f"✅ Created revenue attribution: {attribution_data.attribution_id}")
                return new_attribution
                
        except IntegrityError as e:
            self.logger.error(f"❌ Integrity error creating revenue attribution: {e}")
            raise DuplicateAttributionError(f"Attribution creation failed due to constraint violation: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error creating revenue attribution: {e}")
            raise RevenueAttributionDBError(f"Failed to create revenue attribution: {e}")
    
    async def get_revenue_attribution(
        self,
        attribution_id: str
    ) -> Optional[GPTOSSRevenueAttribution]:
        """獲取收益歸因記錄"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    select(GPTOSSRevenueAttribution).where(
                        GPTOSSRevenueAttribution.attribution_id == attribution_id
                    )
                )
                return result.scalar_one_or_none()
                
        except Exception as e:
            self.logger.error(f"❌ Error getting revenue attribution {attribution_id}: {e}")
            raise RevenueAttributionDBError(f"Failed to get revenue attribution: {e}")
    
    async def update_revenue_attribution(
        self,
        attribution_id: str,
        update_data: Dict[str, Any],
        updater_id: Optional[str] = None
    ) -> bool:
        """更新收益歸因記錄"""
        try:
            async with get_db_session() as session:
                # 檢查記錄是否存在
                existing = await session.execute(
                    select(GPTOSSRevenueAttribution).where(
                        GPTOSSRevenueAttribution.attribution_id == attribution_id
                    )
                )
                attribution = existing.scalar_one_or_none()
                if not attribution:
                    raise AttributionNotFoundError(f"Attribution not found: {attribution_id}")
                
                # 更新字段
                update_data['updated_by'] = updater_id
                update_data['updated_at'] = datetime.now(timezone.utc)
                
                await session.execute(
                    update(GPTOSSRevenueAttribution)
                    .where(GPTOSSRevenueAttribution.attribution_id == attribution_id)
                    .values(**update_data)
                )
                
                await session.commit()
                self.logger.info(f"✅ Updated revenue attribution: {attribution_id}")
                return True
                
        except AttributionNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error updating revenue attribution {attribution_id}: {e}")
            raise RevenueAttributionDBError(f"Failed to update revenue attribution: {e}")
    
    async def delete_revenue_attribution(
        self,
        attribution_id: str
    ) -> bool:
        """刪除收益歸因記錄（軟刪除）"""
        try:
            return await self.update_revenue_attribution(
                attribution_id,
                {'status': 'inactive'},
                None
            )
        except Exception as e:
            self.logger.error(f"❌ Error deleting revenue attribution {attribution_id}: {e}")
            raise RevenueAttributionDBError(f"Failed to delete revenue attribution: {e}")
    
    # ==================== API成本節省操作 ====================
    
    async def create_api_cost_savings(
        self,
        savings_data: APICostSavingsCreate,
        creator_id: Optional[str] = None
    ) -> APICostSavings:
        """創建API成本節省記錄"""
        try:
            async with get_db_session() as session:
                # 驗證關聯的歸因記錄存在
                attribution_exists = await session.execute(
                    select(GPTOSSRevenueAttribution.id).where(
                        GPTOSSRevenueAttribution.id == savings_data.attribution_id
                    )
                )
                if not attribution_exists.scalar_one_or_none():
                    raise InvalidAttributionDataError(f"Attribution ID not found: {savings_data.attribution_id}")
                
                # 計算總成本和節省
                local_total = (
                    savings_data.local_compute_cost +
                    savings_data.local_power_cost +
                    savings_data.local_infrastructure_cost
                )
                
                cloud_total = (
                    savings_data.cloud_api_base_cost +
                    (savings_data.cloud_api_premium_cost or Decimal('0'))
                )
                
                gross_savings = cloud_total - local_total
                net_savings = max(Decimal('0'), gross_savings)
                savings_percentage = (gross_savings / cloud_total * 100) if cloud_total > 0 else Decimal('0')
                savings_per_request = net_savings / savings_data.local_inference_requests if savings_data.local_inference_requests > 0 else Decimal('0')
                savings_per_token = net_savings / savings_data.local_inference_tokens if savings_data.local_inference_tokens > 0 else Decimal('0')
                
                new_savings = APICostSavings(
                    attribution_id=savings_data.attribution_id,
                    calculation_date=savings_data.calculation_date,
                    period_start=savings_data.period_start,
                    period_end=savings_data.period_end,
                    
                    # 本地推理成本
                    local_inference_requests=savings_data.local_inference_requests,
                    local_inference_tokens=savings_data.local_inference_tokens,
                    local_compute_cost=savings_data.local_compute_cost,
                    local_power_cost=savings_data.local_power_cost,
                    local_infrastructure_cost=savings_data.local_infrastructure_cost,
                    local_total_cost=local_total,
                    
                    # 雲端API成本
                    equivalent_cloud_requests=savings_data.equivalent_cloud_requests,
                    equivalent_cloud_tokens=savings_data.equivalent_cloud_tokens,
                    cloud_api_rate_per_token=savings_data.cloud_api_rate_per_token,
                    cloud_api_base_cost=savings_data.cloud_api_base_cost,
                    cloud_api_premium_cost=savings_data.cloud_api_premium_cost,
                    cloud_api_total_cost=cloud_total,
                    
                    # 節省計算
                    gross_savings=gross_savings,
                    net_savings=net_savings,
                    savings_percentage=savings_percentage,
                    savings_per_request=savings_per_request,
                    savings_per_token=savings_per_token,
                    
                    # 性能數據
                    local_avg_response_time=savings_data.local_avg_response_time,
                    cloud_avg_response_time=savings_data.cloud_avg_response_time,
                    local_availability_rate=savings_data.local_availability_rate,
                    cloud_availability_rate=savings_data.cloud_availability_rate,
                    quality_score_difference=savings_data.quality_score_difference,
                    
                    # 分解數據
                    by_model_breakdown=savings_data.by_model_breakdown,
                    by_user_type_breakdown=savings_data.by_user_type_breakdown,
                    by_feature_breakdown=savings_data.by_feature_breakdown,
                    
                    # 計算方法
                    calculation_method=savings_data.calculation_method,
                    data_completeness_score=savings_data.data_completeness_score,
                    created_by=creator_id
                )
                
                session.add(new_savings)
                await session.commit()
                await session.refresh(new_savings)
                
                self.logger.info(f"✅ Created API cost savings for attribution: {savings_data.attribution_id}")
                return new_savings
                
        except InvalidAttributionDataError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error creating API cost savings: {e}")
            raise RevenueAttributionDBError(f"Failed to create API cost savings: {e}")
    
    # ==================== 查詢和分析方法 ====================
    
    async def get_revenue_attribution_summary(
        self,
        period_start: date,
        period_end: date,
        revenue_types: Optional[List[RevenueType]] = None,
        customer_segments: Optional[List[CustomerSegment]] = None,
        min_confidence_score: float = 0.0
    ) -> RevenueAttributionSummary:
        """獲取收益歸因摘要"""
        try:
            async with get_db_session() as session:
                # 構建基礎查詢
                query = select(GPTOSSRevenueAttribution).where(
                    and_(
                        GPTOSSRevenueAttribution.attribution_period_start >= period_start,
                        GPTOSSRevenueAttribution.attribution_period_end <= period_end,
                        GPTOSSRevenueAttribution.confidence_score >= min_confidence_score,
                        GPTOSSRevenueAttribution.status == 'active'
                    )
                )
                
                # 添加篩選條件
                if revenue_types:
                    query = query.where(
                        GPTOSSRevenueAttribution.revenue_type.in_([rt.value for rt in revenue_types])
                    )
                
                if customer_segments:
                    query = query.where(
                        GPTOSSRevenueAttribution.customer_segment.in_([cs.value for cs in customer_segments])
                    )
                
                result = await session.execute(query)
                attributions = result.scalars().all()
                
                if not attributions:
                    return RevenueAttributionSummary(
                        period_start=period_start,
                        period_end=period_end,
                        total_attributed_revenue=Decimal('0'),
                        total_incremental_revenue=Decimal('0'),
                        attribution_count=0,
                        avg_confidence_score=0.0,
                        top_revenue_types=[],
                        customer_segment_breakdown={},
                        monthly_trend=[]
                    )
                
                # 計算摘要統計
                total_attributed = sum(a.gpt_oss_attributed_amount for a in attributions)
                total_incremental = sum(a.incremental_amount for a in attributions)
                avg_confidence = sum(float(a.confidence_score) for a in attributions) / len(attributions)
                
                # 收益類型排名
                revenue_type_totals = {}
                for attribution in attributions:
                    rt = attribution.revenue_type
                    revenue_type_totals[rt] = revenue_type_totals.get(rt, Decimal('0')) + attribution.gpt_oss_attributed_amount
                
                top_revenue_types = [
                    {'revenue_type': rt, 'total_amount': float(amount)}
                    for rt, amount in sorted(revenue_type_totals.items(), key=lambda x: x[1], reverse=True)[:5]
                ]
                
                # 客戶群體分解
                segment_breakdown = {}
                for attribution in attributions:
                    segment = attribution.customer_segment or 'unknown'
                    segment_breakdown[segment] = segment_breakdown.get(segment, Decimal('0')) + attribution.gpt_oss_attributed_amount
                
                # 月度趨勢
                monthly_totals = {}
                for attribution in attributions:
                    month_key = f"{attribution.period_year}-{attribution.period_month:02d}"
                    if month_key not in monthly_totals:
                        monthly_totals[month_key] = {
                            'attributed_revenue': Decimal('0'),
                            'incremental_revenue': Decimal('0'),
                            'count': 0
                        }
                    monthly_totals[month_key]['attributed_revenue'] += attribution.gpt_oss_attributed_amount
                    monthly_totals[month_key]['incremental_revenue'] += attribution.incremental_amount
                    monthly_totals[month_key]['count'] += 1
                
                monthly_trend = [
                    {
                        'month': month,
                        'attributed_revenue': float(data['attributed_revenue']),
                        'incremental_revenue': float(data['incremental_revenue']),
                        'count': data['count']
                    }
                    for month, data in sorted(monthly_totals.items())
                ]
                
                return RevenueAttributionSummary(
                    period_start=period_start,
                    period_end=period_end,
                    total_attributed_revenue=total_attributed,
                    total_incremental_revenue=total_incremental,
                    attribution_count=len(attributions),
                    avg_confidence_score=avg_confidence,
                    top_revenue_types=top_revenue_types,
                    customer_segment_breakdown={k: float(v) for k, v in segment_breakdown.items()},
                    monthly_trend=monthly_trend
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error getting revenue attribution summary: {e}")
            raise RevenueAttributionDBError(f"Failed to get revenue attribution summary: {e}")
    
    async def get_api_savings_analysis(
        self,
        period_start: date,
        period_end: date,
        include_quality_metrics: bool = True
    ) -> APISavingsAnalysis:
        """獲取API節省分析"""
        try:
            async with get_db_session() as session:
                # 查詢API成本節省記錄
                query = select(APICostSavings).where(
                    and_(
                        APICostSavings.period_start >= period_start,
                        APICostSavings.period_end <= period_end
                    )
                )
                
                result = await session.execute(query)
                savings_records = result.scalars().all()
                
                if not savings_records:
                    return APISavingsAnalysis(
                        period_start=period_start,
                        period_end=period_end,
                        total_local_cost=Decimal('0'),
                        total_cloud_cost=Decimal('0'),
                        total_savings=Decimal('0'),
                        savings_percentage=0.0,
                        avg_savings_per_request=Decimal('0'),
                        requests_analyzed=0,
                        quality_improvement=None
                    )
                
                # 聚合統計
                total_local_cost = sum(r.local_total_cost for r in savings_records)
                total_cloud_cost = sum(r.cloud_api_total_cost for r in savings_records)
                total_savings = sum(r.net_savings for r in savings_records)
                total_requests = sum(r.local_inference_requests for r in savings_records)
                
                savings_percentage = float((total_savings / total_cloud_cost * 100)) if total_cloud_cost > 0 else 0.0
                avg_savings_per_request = total_savings / total_requests if total_requests > 0 else Decimal('0')
                
                # 質量改善分析
                quality_improvement = None
                if include_quality_metrics:
                    quality_scores = [float(r.quality_score_difference) for r in savings_records if r.quality_score_difference is not None]
                    if quality_scores:
                        quality_improvement = sum(quality_scores) / len(quality_scores)
                
                return APISavingsAnalysis(
                    period_start=period_start,
                    period_end=period_end,
                    total_local_cost=total_local_cost,
                    total_cloud_cost=total_cloud_cost,
                    total_savings=total_savings,
                    savings_percentage=savings_percentage,
                    avg_savings_per_request=avg_savings_per_request,
                    requests_analyzed=total_requests,
                    quality_improvement=quality_improvement
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error getting API savings analysis: {e}")
            raise RevenueAttributionDBError(f"Failed to get API savings analysis: {e}")
    
    async def get_top_revenue_features(
        self,
        period_start: date,
        period_end: date,
        limit: int = 10
    ) -> List[FeatureRevenueImpact]:
        """獲取頂級收益功能"""
        try:
            async with get_db_session() as session:
                # 查詢新功能收益記錄
                query = select(NewFeatureRevenue).where(
                    and_(
                        NewFeatureRevenue.measurement_period_start >= period_start,
                        NewFeatureRevenue.measurement_period_end <= period_end
                    )
                ).order_by(desc(NewFeatureRevenue.total_feature_revenue)).limit(limit)
                
                result = await session.execute(query)
                feature_records = result.scalars().all()
                
                return [
                    FeatureRevenueImpact(
                        feature_name=record.feature_name,
                        feature_category=record.feature_category,
                        total_revenue=record.total_feature_revenue,
                        user_adoption_rate=float(record.feature_adoption_rate),
                        roi=float(record.feature_roi) if record.feature_roi else None,
                        launch_date=record.feature_launch_date,
                        revenue_growth_rate=None  # 需要額外計算
                    )
                    for record in feature_records
                ]
                
        except Exception as e:
            self.logger.error(f"❌ Error getting top revenue features: {e}")
            raise RevenueAttributionDBError(f"Failed to get top revenue features: {e}")
    
    # ==================== 批量操作 ====================
    
    async def batch_create_attributions(
        self,
        attributions: List[GPTOSSRevenueAttributionCreate],
        creator_id: Optional[str] = None,
        batch_size: int = 100
    ) -> List[uuid.UUID]:
        """批量創建收益歸因記錄"""
        try:
            created_ids = []
            
            for i in range(0, len(attributions), batch_size):
                batch = attributions[i:i + batch_size]
                
                async with get_db_session() as session:
                    # 批量插入
                    new_records = []
                    for attr_data in batch:
                        period_start = attr_data.attribution_period_start
                        
                        new_record = GPTOSSRevenueAttribution(
                            attribution_id=attr_data.attribution_id,
                            record_date=attr_data.record_date,
                            attribution_period_start=period_start,
                            attribution_period_end=attr_data.attribution_period_end,
                            period_year=period_start.year,
                            period_quarter=((period_start.month - 1) // 3) + 1,
                            period_month=period_start.month,
                            revenue_type=attr_data.revenue_type.value,
                            total_revenue_amount=attr_data.total_revenue_amount,
                            gpt_oss_attributed_amount=attr_data.gpt_oss_attributed_amount,
                            incremental_amount=attr_data.incremental_amount,
                            attribution_method=attr_data.attribution_method.value,
                            attribution_confidence=attr_data.attribution_confidence.value,
                            confidence_score=attr_data.confidence_score,
                            gpt_oss_contribution_ratio=attr_data.gpt_oss_contribution_ratio,
                            description=attr_data.description,
                            data_source=attr_data.data_source,
                            created_by=creator_id
                        )
                        new_records.append(new_record)
                    
                    session.add_all(new_records)
                    await session.commit()
                    
                    # 獲取生成的ID
                    for record in new_records:
                        await session.refresh(record)
                        created_ids.append(record.id)
                
                self.logger.info(f"✅ Batch created {len(batch)} revenue attributions")
            
            return created_ids
            
        except Exception as e:
            self.logger.error(f"❌ Error in batch create attributions: {e}")
            raise RevenueAttributionDBError(f"Failed to batch create attributions: {e}")
    
    # ==================== 搜索和篩選 ====================
    
    async def search_attributions(
        self,
        search_params: Dict[str, Any],
        page: int = 1,
        page_size: int = 50,
        sort_by: str = 'created_at',
        sort_order: str = 'desc'
    ) -> Tuple[List[GPTOSSRevenueAttribution], int]:
        """搜索收益歸因記錄"""
        try:
            # 驗證分頁參數
            page = max(1, page)
            page_size = min(page_size, self.config['max_page_size'])
            offset = (page - 1) * page_size
            
            async with get_db_session() as session:
                # 構建查詢
                query = select(GPTOSSRevenueAttribution).where(
                    GPTOSSRevenueAttribution.status == 'active'
                )
                
                # 添加搜索條件
                if 'revenue_type' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.revenue_type == search_params['revenue_type'])
                
                if 'customer_segment' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.customer_segment == search_params['customer_segment'])
                
                if 'feature_category' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.feature_category == search_params['feature_category'])
                
                if 'period_start' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.attribution_period_start >= search_params['period_start'])
                
                if 'period_end' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.attribution_period_end <= search_params['period_end'])
                
                if 'min_confidence' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.confidence_score >= search_params['min_confidence'])
                
                if 'min_revenue' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.gpt_oss_attributed_amount >= search_params['min_revenue'])
                
                if 'attribution_method' in search_params:
                    query = query.where(GPTOSSRevenueAttribution.attribution_method == search_params['attribution_method'])
                
                # 全文搜索
                if 'search_text' in search_params and search_params['search_text']:
                    search_text = f"%{search_params['search_text']}%"
                    query = query.where(
                        or_(
                            GPTOSSRevenueAttribution.description.ilike(search_text),
                            GPTOSSRevenueAttribution.gpt_oss_feature_used.ilike(search_text),
                            GPTOSSRevenueAttribution.attribution_id.ilike(search_text)
                        )
                    )
                
                # 計算總數
                count_query = select(func.count()).select_from(query.alias())
                total_count = await session.scalar(count_query)
                
                # 排序
                if hasattr(GPTOSSRevenueAttribution, sort_by):
                    sort_column = getattr(GPTOSSRevenueAttribution, sort_by)
                    if sort_order.lower() == 'desc':
                        query = query.order_by(desc(sort_column))
                    else:
                        query = query.order_by(asc(sort_column))
                
                # 分頁
                query = query.offset(offset).limit(page_size)
                
                # 執行查詢
                result = await session.execute(query)
                attributions = result.scalars().all()
                
                return list(attributions), total_count
                
        except Exception as e:
            self.logger.error(f"❌ Error searching attributions: {e}")
            raise RevenueAttributionDBError(f"Failed to search attributions: {e}")
    
    # ==================== 驗證和審計 ====================
    
    async def verify_attribution(
        self,
        attribution_id: str,
        verification_method: str,
        verification_notes: Optional[str] = None,
        verifier_id: Optional[str] = None
    ) -> bool:
        """驗證收益歸因記錄"""
        try:
            update_data = {
                'is_verified': True,
                'verification_method': verification_method,
                'verification_date': datetime.now(timezone.utc),
                'verification_notes': verification_notes
            }
            
            return await self.update_revenue_attribution(
                attribution_id,
                update_data,
                verifier_id
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error verifying attribution {attribution_id}: {e}")
            raise RevenueAttributionDBError(f"Failed to verify attribution: {e}")
    
    async def get_attribution_audit_trail(
        self,
        attribution_id: str
    ) -> List[Dict[str, Any]]:
        """獲取歸因記錄審計軌跡"""
        try:
            async with get_db_session() as session:
                # 這裡可以實現完整的審計軌跡查詢
                # 目前返回基本信息
                attribution = await self.get_revenue_attribution(attribution_id)
                if not attribution:
                    raise AttributionNotFoundError(f"Attribution not found: {attribution_id}")
                
                audit_trail = [
                    {
                        'action': 'created',
                        'timestamp': attribution.created_at.isoformat(),
                        'user_id': attribution.created_by,
                        'details': {
                            'revenue_amount': float(attribution.gpt_oss_attributed_amount),
                            'confidence_score': float(attribution.confidence_score)
                        }
                    }
                ]
                
                if attribution.is_verified:
                    audit_trail.append({
                        'action': 'verified',
                        'timestamp': attribution.verification_date.isoformat() if attribution.verification_date else None,
                        'user_id': None,  # 驗證者信息
                        'details': {
                            'verification_method': attribution.verification_method,
                            'notes': attribution.verification_notes
                        }
                    })
                
                return audit_trail
                
        except AttributionNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"❌ Error getting audit trail for {attribution_id}: {e}")
            raise RevenueAttributionDBError(f"Failed to get audit trail: {e}")
    
    # ==================== 健康檢查和維護 ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """收益歸因數據庫健康檢查"""
        health_status = {
            'system': 'revenue_attribution_db',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'healthy',
            'metrics': {}
        }
        
        try:
            async with get_db_session() as session:
                # 檢查數據庫連接
                await session.execute(select(1))
                
                # 統計基本指標
                total_attributions = await session.scalar(
                    select(func.count(GPTOSSRevenueAttribution.id))
                )
                
                active_attributions = await session.scalar(
                    select(func.count(GPTOSSRevenueAttribution.id)).where(
                        GPTOSSRevenueAttribution.status == 'active'
                    )
                )
                
                recent_attributions = await session.scalar(
                    select(func.count(GPTOSSRevenueAttribution.id)).where(
                        GPTOSSRevenueAttribution.created_at >= datetime.now(timezone.utc) - timedelta(days=7)
                    )
                )
                
                health_status['metrics'] = {
                    'total_attributions': total_attributions,
                    'active_attributions': active_attributions,
                    'recent_attributions_7_days': recent_attributions,
                    'cache_hits': self.cache_stats['hits'],
                    'cache_misses': self.cache_stats['misses']
                }
                
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['error'] = str(e)
            self.logger.error(f"❌ Revenue attribution DB health check failed: {e}")
        
        return health_status
    
    async def cleanup_old_records(
        self,
        days_to_keep: int = 365,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """清理舊記錄"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
            
            async with get_db_session() as session:
                # 查找要清理的記錄
                old_records_query = select(func.count(GPTOSSRevenueAttribution.id)).where(
                    and_(
                        GPTOSSRevenueAttribution.created_at < cutoff_date,
                        GPTOSSRevenueAttribution.status == 'inactive'
                    )
                )
                
                records_to_cleanup = await session.scalar(old_records_query)
                
                cleanup_result = {
                    'cutoff_date': cutoff_date.isoformat(),
                    'records_found': records_to_cleanup,
                    'dry_run': dry_run,
                    'deleted': 0
                }
                
                if not dry_run and records_to_cleanup > 0:
                    # 實際刪除操作
                    delete_query = delete(GPTOSSRevenueAttribution).where(
                        and_(
                            GPTOSSRevenueAttribution.created_at < cutoff_date,
                            GPTOSSRevenueAttribution.status == 'inactive'
                        )
                    )
                    
                    result = await session.execute(delete_query)
                    await session.commit()
                    cleanup_result['deleted'] = result.rowcount
                
                self.logger.info(f"✅ Cleanup completed: {cleanup_result}")
                return cleanup_result
                
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
            raise RevenueAttributionDBError(f"Failed to cleanup old records: {e}")