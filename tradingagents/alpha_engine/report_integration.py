#!/usr/bin/env python3
"""
Analysis Report System Integration
分析報告系統集成 - GPT-OSS整合任務3.2.3

將AlphaEngine和會員訪問控制集成到分析報告系統
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from decimal import Decimal

class ReportType(str, Enum):
    """報告類型"""
    ALPHA_INSIGHTS_DAILY = "alpha_insights_daily"
    ALPHA_INSIGHTS_WEEKLY = "alpha_insights_weekly"
    MARKET_SENTIMENT_REPORT = "market_sentiment_report"
    FINANCIAL_HEALTH_REPORT = "financial_health_report"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    SECTOR_ANALYSIS = "sector_analysis"
    CUSTOM_ANALYSIS = "custom_analysis"

class ReportFormat(str, Enum):
    """報告格式"""
    PDF = "pdf"
    HTML = "html"
    JSON = "json"
    EXCEL = "excel"
    CSV = "csv"

class ReportStatus(str, Enum):
    """報告狀態"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class ReportPriority(str, Enum):
    """報告優先級"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class ReportDeliveryMethod(str, Enum):
    """報告交付方式"""
    DOWNLOAD = "download"
    EMAIL = "email"
    API = "api"
    WEBHOOK = "webhook"

class ReportTemplate(BaseModel):
    """報告模板"""
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名稱")
    report_type: ReportType = Field(..., description="報告類型")
    sections: List[str] = Field(default_factory=list, description="報告章節")
    required_data_sources: List[str] = Field(default_factory=list, description="必需數據源")
    supported_formats: List[ReportFormat] = Field(default_factory=list, description="支持格式")
    estimated_generation_time_minutes: int = Field(5, description="預估生成時間")
    member_tier_required: str = Field("free", description="所需會員等級")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReportConfiguration(BaseModel):
    """報告配置"""
    config_id: str = Field(..., description="配置ID")
    member_id: str = Field(..., description="會員ID")
    report_type: ReportType = Field(..., description="報告類型")
    template_id: str = Field(..., description="模板ID")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="報告參數")
    output_format: ReportFormat = Field(ReportFormat.PDF, description="輸出格式")
    delivery_method: ReportDeliveryMethod = Field(ReportDeliveryMethod.DOWNLOAD, description="交付方式")
    delivery_address: Optional[str] = Field(None, description="交付地址")
    schedule_type: Optional[str] = Field(None, description="排程類型")
    schedule_time: Optional[datetime] = Field(None, description="排程時間")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReportGenerationRequest(BaseModel):
    """報告生成請求"""
    request_id: str = Field(..., description="請求ID")
    member_id: str = Field(..., description="會員ID")
    report_configuration: ReportConfiguration = Field(..., description="報告配置")
    priority: ReportPriority = Field(ReportPriority.NORMAL, description="優先級")
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deadline: Optional[datetime] = Field(None, description="截止時間")

class ReportContent(BaseModel):
    """報告內容"""
    section_id: str = Field(..., description="章節ID")
    section_title: str = Field(..., description="章節標題")
    content_type: str = Field(..., description="內容類型")
    content_data: Dict[str, Any] = Field(default_factory=dict, description="內容數據")
    insights: List[Dict[str, Any]] = Field(default_factory=list, description="洞察內容")
    charts: List[Dict[str, Any]] = Field(default_factory=list, description="圖表數據")
    tables: List[Dict[str, Any]] = Field(default_factory=list, description="表格數據")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GeneratedReport(BaseModel):
    """生成的報告"""
    report_id: str = Field(..., description="報告ID")
    request_id: str = Field(..., description="請求ID")
    member_id: str = Field(..., description="會員ID")
    report_type: ReportType = Field(..., description="報告類型")
    title: str = Field(..., description="報告標題")
    summary: str = Field(..., description="報告摘要")
    content_sections: List[ReportContent] = Field(default_factory=list, description="內容章節")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元數據")
    file_path: Optional[str] = Field(None, description="文件路徑")
    file_size_bytes: int = Field(0, description="文件大小")
    generation_time_seconds: float = Field(0.0, description="生成時間")
    status: ReportStatus = Field(ReportStatus.COMPLETED, description="報告狀態")
    expires_at: Optional[datetime] = Field(None, description="過期時間")
    download_count: int = Field(0, description="下載次數")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ReportAnalysisIntegrator:
    """報告分析集成器"""
    
    def __init__(self, alpha_engine=None, access_controller=None):
        from .alpha_engine_core import AlphaEngine
        from .member_access_control import MemberAccessController, MembershipTier, FeatureType
        
        self.alpha_engine = alpha_engine
        self.access_controller = access_controller
        self.report_templates = self._initialize_report_templates()
        self.generated_reports: List[GeneratedReport] = []
        self.generation_queue: List[ReportGenerationRequest] = []
        
    def _initialize_report_templates(self) -> Dict[ReportType, ReportTemplate]:
        """初始化報告模板"""
        templates = {}
        
        # Alpha洞察日報模板
        templates[ReportType.ALPHA_INSIGHTS_DAILY] = ReportTemplate(
            template_id="alpha_daily_001",
            template_name="Alpha洞察日報",
            report_type=ReportType.ALPHA_INSIGHTS_DAILY,
            sections=[
                "executive_summary",
                "market_overview", 
                "alpha_insights",
                "risk_alerts",
                "recommended_actions"
            ],
            required_data_sources=["alpha_engine", "market_data", "news_analysis"],
            supported_formats=[ReportFormat.PDF, ReportFormat.HTML, ReportFormat.JSON],
            estimated_generation_time_minutes=8,
            member_tier_required="basic"
        )
        
        # Alpha洞察週報模板
        templates[ReportType.ALPHA_INSIGHTS_WEEKLY] = ReportTemplate(
            template_id="alpha_weekly_001",
            template_name="Alpha洞察週報",
            report_type=ReportType.ALPHA_INSIGHTS_WEEKLY,
            sections=[
                "executive_summary",
                "market_performance_review",
                "top_alpha_insights",
                "sector_analysis",
                "portfolio_recommendations",
                "risk_assessment",
                "outlook_and_strategy"
            ],
            required_data_sources=["alpha_engine", "market_data", "financial_reports", "technical_analysis"],
            supported_formats=[ReportFormat.PDF, ReportFormat.HTML, ReportFormat.EXCEL],
            estimated_generation_time_minutes=15,
            member_tier_required="premium"
        )
        
        # 市場情緒報告模板
        templates[ReportType.MARKET_SENTIMENT_REPORT] = ReportTemplate(
            template_id="sentiment_001",
            template_name="市場情緒分析報告",
            report_type=ReportType.MARKET_SENTIMENT_REPORT,
            sections=[
                "sentiment_overview",
                "news_impact_analysis",
                "social_media_sentiment",
                "institutional_sentiment",
                "sentiment_trends",
                "trading_implications"
            ],
            required_data_sources=["news_analysis", "social_sentiment", "institutional_data"],
            supported_formats=[ReportFormat.PDF, ReportFormat.HTML],
            estimated_generation_time_minutes=10,
            member_tier_required="premium"
        )
        
        # 財務健康報告模板
        templates[ReportType.FINANCIAL_HEALTH_REPORT] = ReportTemplate(
            template_id="financial_health_001",
            template_name="公司財務健康報告",
            report_type=ReportType.FINANCIAL_HEALTH_REPORT,
            sections=[
                "financial_overview",
                "profitability_analysis",
                "liquidity_assessment", 
                "leverage_analysis",
                "efficiency_metrics",
                "growth_trends",
                "peer_comparison",
                "investment_recommendation"
            ],
            required_data_sources=["financial_reports", "market_data", "peer_data"],
            supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL],
            estimated_generation_time_minutes=12,
            member_tier_required="premium"
        )
        
        # 投資組合分析模板
        templates[ReportType.PORTFOLIO_ANALYSIS] = ReportTemplate(
            template_id="portfolio_001",
            template_name="投資組合分析報告",
            report_type=ReportType.PORTFOLIO_ANALYSIS,
            sections=[
                "portfolio_overview",
                "performance_analysis",
                "risk_metrics",
                "sector_allocation",
                "alpha_contribution",
                "rebalancing_recommendations",
                "optimization_opportunities"
            ],
            required_data_sources=["portfolio_data", "market_data", "alpha_engine", "risk_models"],
            supported_formats=[ReportFormat.PDF, ReportFormat.EXCEL, ReportFormat.JSON],
            estimated_generation_time_minutes=18,
            member_tier_required="vip"
        )
        
        return templates
    
    async def check_report_access(self, member_id: str, report_type: ReportType, 
                                member_profile) -> Dict[str, Any]:
        """檢查報告訪問權限"""
        if not self.access_controller:
            return {"allowed": True, "reason": "Access controller not configured"}
        
        # 獲取報告模板
        template = self.report_templates.get(report_type)
        if not template:
            return {
                "allowed": False,
                "reason": "報告類型不存在",
                "template_required": None
            }
        
        # 檢查會員等級是否足夠
        from .member_access_control import MembershipTier, FeatureType
        
        required_tier = getattr(MembershipTier, template.member_tier_required.upper(), MembershipTier.FREE)
        member_tier = member_profile.membership_tier
        
        tier_hierarchy = [
            MembershipTier.FREE,
            MembershipTier.BASIC,
            MembershipTier.PREMIUM, 
            MembershipTier.VIP,
            MembershipTier.ENTERPRISE
        ]
        
        if tier_hierarchy.index(member_tier) < tier_hierarchy.index(required_tier):
            return {
                "allowed": False,
                "reason": "會員等級不足",
                "required_tier": required_tier.value,
                "current_tier": member_tier.value,
                "upgrade_required": True
            }
        
        # 檢查報告生成功能權限
        access_result = await self.access_controller.check_access(
            member_id, FeatureType.ALPHA_INSIGHTS, member_profile
        )
        
        return {
            "allowed": access_result.allowed,
            "reason": access_result.reason,
            "quota_remaining": access_result.quota_remaining,
            "template_info": {
                "name": template.template_name,
                "estimated_time": template.estimated_generation_time_minutes,
                "supported_formats": [fmt.value for fmt in template.supported_formats]
            }
        }
    
    async def generate_alpha_insights_report(self, request: ReportGenerationRequest) -> GeneratedReport:
        """生成Alpha洞察報告"""
        start_time = datetime.now(timezone.utc)
        
        # 獲取Alpha洞察數據
        alpha_insights = []
        if self.alpha_engine:
            try:
                from .alpha_engine_core import InsightGenerationRequest
                
                insight_request = InsightGenerationRequest(
                    request_id=f"report_{request.request_id}",
                    user_id=request.member_id,
                    stock_codes=request.report_configuration.parameters.get('stock_codes'),
                    max_results=request.report_configuration.parameters.get('max_insights', 10)
                )
                
                insight_response = await self.alpha_engine.generate_insights(insight_request)
                alpha_insights = [insight.dict() for insight in insight_response.insights]
                
            except Exception as e:
                # 使用模擬數據
                alpha_insights = self._generate_sample_alpha_insights()
        else:
            alpha_insights = self._generate_sample_alpha_insights()
        
        # 構建報告內容
        content_sections = []
        
        # 執行摘要
        exec_summary = ReportContent(
            section_id="exec_summary",
            section_title="執行摘要",
            content_type="summary",
            content_data={
                "total_insights": len(alpha_insights),
                "high_priority_insights": len([i for i in alpha_insights if i.get('priority') == 'high']),
                "average_confidence": sum(i.get('confidence_score', 0) for i in alpha_insights) / len(alpha_insights) if alpha_insights else 0,
                "key_highlights": [
                    "發現3個高價值投資機會",
                    "識別2個潛在風險警告",
                    "整體市場情緒偏向樂觀"
                ]
            }
        )
        content_sections.append(exec_summary)
        
        # Alpha洞察章節
        insights_section = ReportContent(
            section_id="alpha_insights",
            section_title="Alpha投資洞察",
            content_type="insights",
            insights=alpha_insights,
            content_data={
                "insight_types": list(set(i.get('insight_type') for i in alpha_insights)),
                "total_count": len(alpha_insights)
            }
        )
        content_sections.append(insights_section)
        
        # 風險評估章節
        risk_section = ReportContent(
            section_id="risk_assessment",
            section_title="風險評估",
            content_type="risk_analysis",
            content_data={
                "overall_risk_level": "中等",
                "risk_factors": [
                    "市場波動加劇",
                    "流動性風險上升",
                    "地緣政治不確定性"
                ],
                "risk_mitigation": [
                    "分散投資組合",
                    "保持適當現金比例",
                    "密切監控市場變化"
                ]
            }
        )
        content_sections.append(risk_section)
        
        # 計算生成時間
        generation_time = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        # 創建報告對象
        report = GeneratedReport(
            report_id=f"report_{request.request_id}_{int(datetime.now().timestamp())}",
            request_id=request.request_id,
            member_id=request.member_id,
            report_type=request.report_configuration.report_type,
            title=f"Alpha洞察報告 - {datetime.now().strftime('%Y-%m-%d')}",
            summary=f"本報告包含{len(alpha_insights)}個Alpha投資洞察，平均置信度{exec_summary.content_data['average_confidence']:.2f}",
            content_sections=content_sections,
            metadata={
                "generation_method": "alpha_engine_integration",
                "data_sources": ["alpha_engine", "market_data"],
                "insights_count": len(alpha_insights),
                "report_version": "1.0"
            },
            file_path=f"/reports/{request.member_id}/alpha_insights_{request.request_id}.pdf",
            file_size_bytes=1024768,  # 模擬文件大小
            generation_time_seconds=generation_time,
            status=ReportStatus.COMPLETED,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        return report
    
    def _generate_sample_alpha_insights(self) -> List[Dict[str, Any]]:
        """生成樣本Alpha洞察數據"""
        return [
            {
                "insight_id": "alpha_001",
                "insight_type": "fundamental_analysis",
                "title": "台積電基本面強勁，目標價上調",
                "summary": "受惠於AI晶片需求，營收持續成長",
                "stock_code": "2330",
                "priority": "high",
                "confidence_score": 0.89,
                "expected_impact": 0.82,
                "target_price": 520,
                "upside_potential": 15.3
            },
            {
                "insight_id": "alpha_002", 
                "insight_type": "technical_analysis",
                "title": "聯發科技術突破，短期看漲",
                "summary": "突破關鍵阻力位，成交量放大",
                "stock_code": "2454",
                "priority": "medium",
                "confidence_score": 0.76,
                "expected_impact": 0.65,
                "target_price": 780,
                "upside_potential": 8.7
            },
            {
                "insight_id": "alpha_003",
                "insight_type": "news_sentiment",
                "title": "電子股整體情緒轉正",
                "summary": "近期正面新聞增加，投資人信心回升",
                "stock_code": None,
                "priority": "medium",
                "confidence_score": 0.72,
                "expected_impact": 0.58,
                "target_price": None,
                "upside_potential": None
            }
        ]
    
    async def schedule_report_generation(self, request: ReportGenerationRequest) -> Dict[str, Any]:
        """排程報告生成"""
        # 添加到生成隊列
        self.generation_queue.append(request)
        
        # 估算完成時間
        template = self.report_templates.get(request.report_configuration.report_type)
        estimated_completion = datetime.now(timezone.utc) + timedelta(
            minutes=template.estimated_generation_time_minutes if template else 10
        )
        
        return {
            "request_id": request.request_id,
            "status": "scheduled",
            "queue_position": len(self.generation_queue),
            "estimated_completion": estimated_completion,
            "template_name": template.template_name if template else "Unknown"
        }
    
    async def get_report_by_id(self, report_id: str) -> Optional[GeneratedReport]:
        """根據ID獲取報告"""
        for report in self.generated_reports:
            if report.report_id == report_id:
                return report
        return None
    
    async def get_member_reports(self, member_id: str, 
                               report_type: Optional[ReportType] = None,
                               limit: int = 10) -> List[GeneratedReport]:
        """獲取會員的報告列表"""
        member_reports = [r for r in self.generated_reports if r.member_id == member_id]
        
        if report_type:
            member_reports = [r for r in member_reports if r.report_type == report_type]
        
        # 按生成時間排序
        member_reports.sort(key=lambda x: x.generated_at, reverse=True)
        
        return member_reports[:limit]
    
    async def delete_expired_reports(self) -> Dict[str, Any]:
        """刪除過期報告"""
        now = datetime.now(timezone.utc)
        expired_count = 0
        
        active_reports = []
        for report in self.generated_reports:
            if report.expires_at and now > report.expires_at:
                expired_count += 1
            else:
                active_reports.append(report)
        
        self.generated_reports = active_reports
        
        return {
            "deleted_count": expired_count,
            "active_reports": len(active_reports),
            "cleanup_time": now
        }
    
    def get_report_generation_statistics(self) -> Dict[str, Any]:
        """獲取報告生成統計"""
        total_reports = len(self.generated_reports)
        
        if total_reports == 0:
            return {
                "total_reports": 0,
                "average_generation_time": 0,
                "report_types_distribution": {},
                "success_rate": 0,
                "total_downloads": 0
            }
        
        # 按類型統計
        type_distribution = {}
        total_generation_time = 0
        total_downloads = 0
        successful_reports = 0
        
        for report in self.generated_reports:
            report_type = report.report_type.value
            type_distribution[report_type] = type_distribution.get(report_type, 0) + 1
            total_generation_time += report.generation_time_seconds
            total_downloads += report.download_count
            
            if report.status == ReportStatus.COMPLETED:
                successful_reports += 1
        
        return {
            "total_reports": total_reports,
            "average_generation_time_seconds": total_generation_time / total_reports,
            "report_types_distribution": type_distribution,
            "success_rate": successful_reports / total_reports,
            "total_downloads": total_downloads,
            "active_reports": len([r for r in self.generated_reports 
                                 if not r.expires_at or datetime.now(timezone.utc) <= r.expires_at])
        }

class ReportScheduler:
    """報告排程器"""
    
    def __init__(self, integrator: ReportAnalysisIntegrator):
        self.integrator = integrator
        self.scheduled_reports: List[Dict[str, Any]] = []
        
    async def create_recurring_report(self, member_id: str, report_type: ReportType,
                                    frequency: str, start_date: datetime,
                                    report_config: Dict[str, Any]) -> Dict[str, Any]:
        """創建循環報告排程"""
        schedule_id = f"schedule_{member_id}_{report_type.value}_{int(datetime.now().timestamp())}"
        
        schedule = {
            "schedule_id": schedule_id,
            "member_id": member_id,
            "report_type": report_type,
            "frequency": frequency,  # daily, weekly, monthly
            "start_date": start_date,
            "config": report_config,
            "active": True,
            "last_generated": None,
            "next_generation": self._calculate_next_generation(start_date, frequency),
            "total_generated": 0,
            "created_at": datetime.now(timezone.utc)
        }
        
        self.scheduled_reports.append(schedule)
        
        return {
            "schedule_id": schedule_id,
            "status": "created",
            "next_generation": schedule["next_generation"],
            "frequency": frequency
        }
    
    def _calculate_next_generation(self, start_date: datetime, frequency: str) -> datetime:
        """計算下次生成時間"""
        now = datetime.now(timezone.utc)
        
        if frequency == "daily":
            return max(start_date, now) + timedelta(days=1)
        elif frequency == "weekly":
            return max(start_date, now) + timedelta(weeks=1)
        elif frequency == "monthly":
            return max(start_date, now) + timedelta(days=30)
        else:
            return start_date
    
    async def process_scheduled_reports(self) -> Dict[str, Any]:
        """處理排程報告"""
        now = datetime.now(timezone.utc)
        processed = 0
        errors = 0
        
        for schedule in self.scheduled_reports:
            if not schedule["active"]:
                continue
                
            if schedule["next_generation"] <= now:
                try:
                    # 創建報告生成請求
                    config = ReportConfiguration(
                        config_id=f"scheduled_{schedule['schedule_id']}",
                        member_id=schedule["member_id"],
                        report_type=schedule["report_type"],
                        template_id="auto",
                        parameters=schedule["config"]
                    )
                    
                    request = ReportGenerationRequest(
                        request_id=f"scheduled_{schedule['schedule_id']}_{int(now.timestamp())}",
                        member_id=schedule["member_id"],
                        report_configuration=config,
                        priority=ReportPriority.NORMAL
                    )
                    
                    # 排程生成
                    await self.integrator.schedule_report_generation(request)
                    
                    # 更新排程
                    schedule["last_generated"] = now
                    schedule["next_generation"] = self._calculate_next_generation(
                        now, schedule["frequency"]
                    )
                    schedule["total_generated"] += 1
                    
                    processed += 1
                    
                except Exception as e:
                    errors += 1
                    print(f"Error processing scheduled report {schedule['schedule_id']}: {e}")
        
        return {
            "processed_schedules": processed,
            "errors": errors,
            "total_active_schedules": len([s for s in self.scheduled_reports if s["active"]]),
            "next_scheduled_time": min([s["next_generation"] for s in self.scheduled_reports if s["active"]], default=None)
        }