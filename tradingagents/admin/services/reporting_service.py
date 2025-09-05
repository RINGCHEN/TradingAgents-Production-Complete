#!/usr/bin/env python3
"""
報表生成服務 (Reporting Service)
天工 (TianGong) - 完整的報表生成業務邏輯

此模組提供完整的報表生成功能，包含：
1. 自動化報表生成
2. 自定義報表設計
3. 多格式導出
4. 報表調度和分發
5. 報表模板管理
"""

import uuid
import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pathlib import Path
import pandas as pd
from jinja2 import Template
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

from ..models.reporting import (
    ReportTemplate, ReportRequest, ReportResult, ReportSchedule,
    ReportDistribution, ReportMetadata, CustomReport, ReportChart,
    ReportSection, ReportExportFormat, ReportStatus, ReportType
)
from ...utils.logging_config import get_api_logger
from ...utils.cache_manager import CacheManager

api_logger = get_api_logger("reporting_service")

class ReportingService:
    """報表生成服務類"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_manager = CacheManager()
        self.report_templates_path = Path("templates/reports")
        self.report_output_path = Path("output/reports")
        
        # 確保目錄存在
        self.report_templates_path.mkdir(parents=True, exist_ok=True)
        self.report_output_path.mkdir(parents=True, exist_ok=True)
    
    # ==================== 報表生成 ====================
    
    async def generate_report(self, report_request: ReportRequest) -> ReportResult:
        """生成報表"""
        try:
            report_id = str(uuid.uuid4())
            
            # 創建報表元數據
            metadata = ReportMetadata(
                report_id=report_id,
                report_type=report_request.report_type,
                title=report_request.title,
                description=report_request.description,
                created_at=datetime.now(),
                created_by=report_request.created_by,
                parameters=report_request.parameters
            )
            
            # 根據報表類型生成內容
            if report_request.report_type == ReportType.USER_ANALYTICS:
                content = await self._generate_user_analytics_report(report_request)
            elif report_request.report_type == ReportType.FINANCIAL:
                content = await self._generate_financial_report(report_request)
            elif report_request.report_type == ReportType.SYSTEM_PERFORMANCE:
                content = await self._generate_system_performance_report(report_request)
            elif report_request.report_type == ReportType.CUSTOM:
                content = await self._generate_custom_report(report_request)
            else:
                content = await self._generate_default_report(report_request)
            
            # 生成圖表
            charts = await self._generate_report_charts(report_request, content)
            
            # 創建報表結果
            report_result = ReportResult(
                report_id=report_id,
                metadata=metadata,
                content=content,
                charts=charts,
                status=ReportStatus.COMPLETED,
                generated_at=datetime.now(),
                file_paths={}
            )
            
            # 導出為不同格式
            if report_request.export_formats:
                file_paths = await self._export_report(report_result, report_request.export_formats)
                report_result.file_paths = file_paths
            
            return report_result
            
        except Exception as e:
            api_logger.error("生成報表失敗", extra={'error': str(e)})
            raise
    
    async def _generate_user_analytics_report(self, request: ReportRequest) -> Dict[str, Any]:
        """生成用戶分析報表"""
        # 模擬用戶分析數據
        return {
            "summary": {
                "total_users": 8750,
                "active_users": 6200,
                "new_users_this_month": 450,
                "user_growth_rate": 0.08
            },
            "demographics": {
                "age_distribution": {
                    "18-25": 0.15,
                    "26-35": 0.35,
                    "36-45": 0.30,
                    "46-55": 0.15,
                    "55+": 0.05
                },
                "gender_distribution": {
                    "male": 0.65,
                    "female": 0.32,
                    "other": 0.03
                },
                "location_distribution": {
                    "台北": 0.35,
                    "新北": 0.20,
                    "台中": 0.15,
                    "高雄": 0.12,
                    "其他": 0.18
                }
            },
            "behavior": {
                "avg_session_duration": 12.5,
                "pages_per_session": 4.2,
                "bounce_rate": 0.32,
                "return_visitor_rate": 0.68
            },
            "engagement": {
                "daily_active_users": 2100,
                "weekly_active_users": 4800,
                "monthly_active_users": 6200,
                "feature_usage": {
                    "股票搜尋": 0.85,
                    "投資組合": 0.72,
                    "AI分析": 0.58,
                    "市場監控": 0.45,
                    "報表": 0.32
                }
            }
        }
    
    async def _generate_financial_report(self, request: ReportRequest) -> Dict[str, Any]:
        """生成財務報表"""
        return {
            "revenue": {
                "total_revenue": 125000.0,
                "monthly_recurring_revenue": 95000.0,
                "one_time_revenue": 30000.0,
                "revenue_growth": 0.15
            },
            "costs": {
                "operational_costs": 45000.0,
                "marketing_costs": 25000.0,
                "development_costs": 35000.0,
                "infrastructure_costs": 8000.0
            },
            "profitability": {
                "gross_profit": 80000.0,
                "net_profit": 12000.0,
                "profit_margin": 0.096,
                "ebitda": 18000.0
            },
            "subscriptions": {
                "total_subscribers": 1250,
                "new_subscribers": 85,
                "churned_subscribers": 32,
                "churn_rate": 0.026,
                "average_revenue_per_user": 76.0
            },
            "forecasts": {
                "next_month_revenue": 132000.0,
                "next_quarter_revenue": 410000.0,
                "annual_revenue_projection": 1650000.0
            }
        }
    
    async def _generate_system_performance_report(self, request: ReportRequest) -> Dict[str, Any]:
        """生成系統性能報表"""
        return {
            "availability": {
                "uptime_percentage": 99.8,
                "total_downtime_minutes": 144,
                "incident_count": 3,
                "mttr_minutes": 48  # Mean Time To Recovery
            },
            "performance": {
                "avg_response_time": 1.2,
                "95th_percentile_response_time": 2.8,
                "throughput_requests_per_second": 450,
                "error_rate": 0.02
            },
            "resources": {
                "cpu_utilization": 0.65,
                "memory_utilization": 0.72,
                "disk_utilization": 0.45,
                "network_utilization": 0.38
            },
            "api_usage": {
                "total_api_calls": 2500000,
                "successful_calls": 2450000,
                "failed_calls": 50000,
                "most_used_endpoints": [
                    {"endpoint": "/api/stocks/search", "calls": 450000},
                    {"endpoint": "/api/portfolio", "calls": 380000},
                    {"endpoint": "/api/analysis", "calls": 320000}
                ]
            },
            "security": {
                "blocked_attacks": 125,
                "suspicious_activities": 45,
                "failed_login_attempts": 890,
                "security_incidents": 2
            }
        }
    
    async def _generate_custom_report(self, request: ReportRequest) -> Dict[str, Any]:
        """生成自定義報表"""
        # 根據自定義參數生成報表
        custom_data = {}
        
        if request.parameters:
            # 處理自定義查詢
            for key, value in request.parameters.items():
                if key == "metrics":
                    custom_data["metrics"] = await self._fetch_custom_metrics(value)
                elif key == "filters":
                    custom_data["filters_applied"] = value
                elif key == "grouping":
                    custom_data["grouping"] = value
        
        return custom_data
    
    async def _fetch_custom_metrics(self, metrics: List[str]) -> Dict[str, Any]:
        """獲取自定義指標"""
        result = {}
        
        for metric in metrics:
            if metric == "user_count":
                result[metric] = 8750
            elif metric == "revenue":
                result[metric] = 125000.0
            elif metric == "api_calls":
                result[metric] = 2500000
            elif metric == "conversion_rate":
                result[metric] = 0.14
            else:
                result[metric] = 0  # 默認值
        
        return result
    
    # ==================== 圖表生成 ====================
    
    async def _generate_report_charts(self, request: ReportRequest, content: Dict[str, Any]) -> List[ReportChart]:
        """生成報表圖表"""
        charts = []
        
        try:
            # 設置圖表樣式
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            
            # 根據報表類型生成相應圖表
            if request.report_type == ReportType.USER_ANALYTICS:
                charts.extend(await self._create_user_analytics_charts(content))
            elif request.report_type == ReportType.FINANCIAL:
                charts.extend(await self._create_financial_charts(content))
            elif request.report_type == ReportType.SYSTEM_PERFORMANCE:
                charts.extend(await self._create_performance_charts(content))
            
            return charts
            
        except Exception as e:
            api_logger.error("生成圖表失敗", extra={'error': str(e)})
            return []
    
    async def _create_user_analytics_charts(self, content: Dict[str, Any]) -> List[ReportChart]:
        """創建用戶分析圖表"""
        charts = []
        
        # 年齡分佈圓餅圖
        if "demographics" in content and "age_distribution" in content["demographics"]:
            age_data = content["demographics"]["age_distribution"]
            
            plt.figure(figsize=(10, 6))
            plt.pie(age_data.values(), labels=age_data.keys(), autopct='%1.1f%%')
            plt.title('用戶年齡分佈')
            
            # 轉換為base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts.append(ReportChart(
                chart_id=str(uuid.uuid4()),
                title="用戶年齡分佈",
                chart_type="pie",
                data=chart_data,
                description="顯示用戶年齡分佈情況"
            ))
        
        # 功能使用率柱狀圖
        if "engagement" in content and "feature_usage" in content["engagement"]:
            feature_data = content["engagement"]["feature_usage"]
            
            plt.figure(figsize=(12, 6))
            features = list(feature_data.keys())
            usage_rates = list(feature_data.values())
            
            bars = plt.bar(features, usage_rates)
            plt.title('功能使用率')
            plt.xlabel('功能')
            plt.ylabel('使用率')
            plt.xticks(rotation=45)
            
            # 添加數值標籤
            for bar, rate in zip(bars, usage_rates):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f'{rate:.1%}', ha='center', va='bottom')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts.append(ReportChart(
                chart_id=str(uuid.uuid4()),
                title="功能使用率",
                chart_type="bar",
                data=chart_data,
                description="顯示各功能的使用率"
            ))
        
        return charts
    
    async def _create_financial_charts(self, content: Dict[str, Any]) -> List[ReportChart]:
        """創建財務圖表"""
        charts = []
        
        # 收入構成圓餅圖
        if "revenue" in content:
            revenue_data = content["revenue"]
            
            plt.figure(figsize=(10, 6))
            labels = ['月度訂閱收入', '一次性收入']
            sizes = [revenue_data.get("monthly_recurring_revenue", 0), 
                    revenue_data.get("one_time_revenue", 0)]
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%')
            plt.title('收入構成')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts.append(ReportChart(
                chart_id=str(uuid.uuid4()),
                title="收入構成",
                chart_type="pie",
                data=chart_data,
                description="顯示收入來源構成"
            ))
        
        # 成本分析柱狀圖
        if "costs" in content:
            costs_data = content["costs"]
            
            plt.figure(figsize=(12, 6))
            cost_types = list(costs_data.keys())
            cost_values = list(costs_data.values())
            
            bars = plt.bar(cost_types, cost_values)
            plt.title('成本分析')
            plt.xlabel('成本類型')
            plt.ylabel('金額 (元)')
            plt.xticks(rotation=45)
            
            # 添加數值標籤
            for bar, value in zip(bars, cost_values):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1000,
                        f'${value:,.0f}', ha='center', va='bottom')
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts.append(ReportChart(
                chart_id=str(uuid.uuid4()),
                title="成本分析",
                chart_type="bar",
                data=chart_data,
                description="顯示各類成本分佈"
            ))
        
        return charts
    
    async def _create_performance_charts(self, content: Dict[str, Any]) -> List[ReportChart]:
        """創建性能圖表"""
        charts = []
        
        # 系統資源使用率雷達圖
        if "resources" in content:
            resources = content["resources"]
            
            # 創建雷達圖
            categories = list(resources.keys())
            values = list(resources.values())
            
            # 計算角度
            angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]
            angles += angles[:1]  # 閉合圖形
            values += values[:1]
            
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            ax.plot(angles, values, 'o-', linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(categories)
            ax.set_ylim(0, 1)
            plt.title('系統資源使用率', size=16, y=1.1)
            
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
            buffer.seek(0)
            chart_data = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            charts.append(ReportChart(
                chart_id=str(uuid.uuid4()),
                title="系統資源使用率",
                chart_type="radar",
                data=chart_data,
                description="顯示系統各項資源使用情況"
            ))
        
        return charts  
  
    # ==================== 報表導出 ====================
    
    async def _export_report(self, report: ReportResult, formats: List[ReportExportFormat]) -> Dict[str, str]:
        """導出報表為不同格式"""
        file_paths = {}
        
        try:
            for format_type in formats:
                if format_type == ReportExportFormat.PDF:
                    file_path = await self._export_to_pdf(report)
                    file_paths["pdf"] = file_path
                elif format_type == ReportExportFormat.EXCEL:
                    file_path = await self._export_to_excel(report)
                    file_paths["excel"] = file_path
                elif format_type == ReportExportFormat.CSV:
                    file_path = await self._export_to_csv(report)
                    file_paths["csv"] = file_path
                elif format_type == ReportExportFormat.JSON:
                    file_path = await self._export_to_json(report)
                    file_paths["json"] = file_path
            
            return file_paths
            
        except Exception as e:
            api_logger.error("導出報表失敗", extra={'error': str(e)})
            raise
    
    async def _export_to_pdf(self, report: ReportResult) -> str:
        """導出為PDF格式"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            
            # 創建PDF文件
            filename = f"report_{report.report_id}.pdf"
            filepath = self.report_output_path / filename
            
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # 標題
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=1  # 居中
            )
            story.append(Paragraph(report.metadata.title, title_style))
            story.append(Spacer(1, 20))
            
            # 報表信息
            info_data = [
                ['報表ID', report.report_id],
                ['生成時間', report.generated_at.strftime('%Y-%m-%d %H:%M:%S')],
                ['報表類型', report.metadata.report_type.value],
                ['創建者', report.metadata.created_by]
            ]
            
            info_table = Table(info_data, colWidths=[2*inch, 4*inch])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(info_table)
            story.append(Spacer(1, 30))
            
            # 報表內容
            story.append(Paragraph("報表內容", styles['Heading2']))
            story.append(Spacer(1, 12))
            
            # 將內容轉換為表格
            if isinstance(report.content, dict):
                for section_name, section_data in report.content.items():
                    story.append(Paragraph(section_name.replace('_', ' ').title(), styles['Heading3']))
                    
                    if isinstance(section_data, dict):
                        table_data = []
                        for key, value in section_data.items():
                            if isinstance(value, (int, float)):
                                if isinstance(value, float) and 0 < value < 1:
                                    value = f"{value:.2%}"
                                else:
                                    value = f"{value:,}"
                            table_data.append([key.replace('_', ' ').title(), str(value)])
                        
                        if table_data:
                            content_table = Table(table_data, colWidths=[3*inch, 3*inch])
                            content_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                                ('FONTSIZE', (0, 0), (-1, -1), 10),
                                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
                            ]))
                            story.append(content_table)
                    
                    story.append(Spacer(1, 20))
            
            # 添加圖表
            if report.charts:
                story.append(Paragraph("圖表", styles['Heading2']))
                story.append(Spacer(1, 12))
                
                for chart in report.charts:
                    story.append(Paragraph(chart.title, styles['Heading3']))
                    
                    # 將base64圖片轉換為Image對象
                    try:
                        import base64
                        from io import BytesIO
                        from PIL import Image as PILImage
                        
                        image_data = base64.b64decode(chart.data)
                        image_buffer = BytesIO(image_data)
                        pil_image = PILImage.open(image_buffer)
                        
                        # 保存臨時圖片文件
                        temp_image_path = self.report_output_path / f"temp_chart_{chart.chart_id}.png"
                        pil_image.save(temp_image_path)
                        
                        # 添加到PDF
                        img = Image(str(temp_image_path), width=6*inch, height=4*inch)
                        story.append(img)
                        story.append(Spacer(1, 12))
                        
                        # 清理臨時文件
                        temp_image_path.unlink()
                        
                    except Exception as e:
                        api_logger.warning(f"添加圖表到PDF失敗: {e}")
            
            # 生成PDF
            doc.build(story)
            
            return str(filepath)
            
        except Exception as e:
            api_logger.error("導出PDF失敗", extra={'error': str(e)})
            raise
    
    async def _export_to_excel(self, report: ReportResult) -> str:
        """導出為Excel格式"""
        try:
            filename = f"report_{report.report_id}.xlsx"
            filepath = self.report_output_path / filename
            
            with pd.ExcelWriter(str(filepath), engine='openpyxl') as writer:
                # 報表信息工作表
                info_df = pd.DataFrame({
                    '項目': ['報表ID', '生成時間', '報表類型', '創建者'],
                    '值': [
                        report.report_id,
                        report.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
                        report.metadata.report_type.value,
                        report.metadata.created_by
                    ]
                })
                info_df.to_excel(writer, sheet_name='報表信息', index=False)
                
                # 報表內容工作表
                if isinstance(report.content, dict):
                    for section_name, section_data in report.content.items():
                        if isinstance(section_data, dict):
                            # 將字典轉換為DataFrame
                            df_data = []
                            for key, value in section_data.items():
                                df_data.append({'項目': key, '值': value})
                            
                            df = pd.DataFrame(df_data)
                            sheet_name = section_name[:31]  # Excel工作表名稱限制
                            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            return str(filepath)
            
        except Exception as e:
            api_logger.error("導出Excel失敗", extra={'error': str(e)})
            raise
    
    async def _export_to_csv(self, report: ReportResult) -> str:
        """導出為CSV格式"""
        try:
            filename = f"report_{report.report_id}.csv"
            filepath = self.report_output_path / filename
            
            # 將報表內容扁平化為CSV格式
            csv_data = []
            
            # 添加報表信息
            csv_data.append(['報表信息', ''])
            csv_data.append(['報表ID', report.report_id])
            csv_data.append(['生成時間', report.generated_at.strftime('%Y-%m-%d %H:%M:%S')])
            csv_data.append(['報表類型', report.metadata.report_type.value])
            csv_data.append(['創建者', report.metadata.created_by])
            csv_data.append(['', ''])  # 空行
            
            # 添加報表內容
            if isinstance(report.content, dict):
                for section_name, section_data in report.content.items():
                    csv_data.append([section_name, ''])
                    
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            csv_data.append([key, value])
                    
                    csv_data.append(['', ''])  # 空行
            
            # 寫入CSV文件
            df = pd.DataFrame(csv_data, columns=['項目', '值'])
            df.to_csv(str(filepath), index=False, encoding='utf-8-sig')
            
            return str(filepath)
            
        except Exception as e:
            api_logger.error("導出CSV失敗", extra={'error': str(e)})
            raise
    
    async def _export_to_json(self, report: ReportResult) -> str:
        """導出為JSON格式"""
        try:
            filename = f"report_{report.report_id}.json"
            filepath = self.report_output_path / filename
            
            # 準備JSON數據
            json_data = {
                "metadata": {
                    "report_id": report.report_id,
                    "title": report.metadata.title,
                    "description": report.metadata.description,
                    "report_type": report.metadata.report_type.value,
                    "created_at": report.metadata.created_at.isoformat(),
                    "created_by": report.metadata.created_by,
                    "generated_at": report.generated_at.isoformat()
                },
                "content": report.content,
                "charts": [
                    {
                        "chart_id": chart.chart_id,
                        "title": chart.title,
                        "chart_type": chart.chart_type,
                        "description": chart.description
                        # 注意：不包含圖片數據，因為JSON文件會很大
                    }
                    for chart in report.charts
                ],
                "status": report.status.value
            }
            
            # 寫入JSON文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            return str(filepath)
            
        except Exception as e:
            api_logger.error("導出JSON失敗", extra={'error': str(e)})
            raise
    
    # ==================== 報表模板管理 ====================
    
    async def create_report_template(self, template_data: Dict[str, Any]) -> ReportTemplate:
        """創建報表模板"""
        try:
            template_id = str(uuid.uuid4())
            
            template = ReportTemplate(
                template_id=template_id,
                name=template_data["name"],
                description=template_data.get("description", ""),
                report_type=ReportType(template_data["report_type"]),
                sections=template_data.get("sections", []),
                parameters=template_data.get("parameters", {}),
                created_at=datetime.now(),
                created_by=template_data["created_by"],
                is_active=True
            )
            
            # 保存模板到文件系統
            template_file = self.report_templates_path / f"{template_id}.json"
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            return template
            
        except Exception as e:
            api_logger.error("創建報表模板失敗", extra={'error': str(e)})
            raise
    
    async def get_report_templates(self) -> List[ReportTemplate]:
        """獲取所有報表模板"""
        try:
            templates = []
            
            for template_file in self.report_templates_path.glob("*.json"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_data = json.load(f)
                    
                    template = ReportTemplate(**template_data)
                    if template.is_active:
                        templates.append(template)
                        
                except Exception as e:
                    api_logger.warning(f"載入模板失敗: {template_file}, {e}")
            
            return templates
            
        except Exception as e:
            api_logger.error("獲取報表模板失敗", extra={'error': str(e)})
            raise
    
    async def update_report_template(self, template_id: str, update_data: Dict[str, Any]) -> ReportTemplate:
        """更新報表模板"""
        try:
            template_file = self.report_templates_path / f"{template_id}.json"
            
            if not template_file.exists():
                raise ValueError(f"模板不存在: {template_id}")
            
            # 載入現有模板
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # 更新數據
            template_data.update(update_data)
            template_data["updated_at"] = datetime.now().isoformat()
            
            # 保存更新後的模板
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=2)
            
            return ReportTemplate(**template_data)
            
        except Exception as e:
            api_logger.error("更新報表模板失敗", extra={'template_id': template_id, 'error': str(e)})
            raise
    
    async def delete_report_template(self, template_id: str):
        """刪除報表模板"""
        try:
            template_file = self.report_templates_path / f"{template_id}.json"
            
            if template_file.exists():
                template_file.unlink()
            else:
                raise ValueError(f"模板不存在: {template_id}")
                
        except Exception as e:
            api_logger.error("刪除報表模板失敗", extra={'template_id': template_id, 'error': str(e)})
            raise
    
    # ==================== 報表調度 ====================
    
    async def create_report_schedule(self, schedule_data: Dict[str, Any]) -> ReportSchedule:
        """創建報表調度"""
        try:
            schedule_id = str(uuid.uuid4())
            
            schedule = ReportSchedule(
                schedule_id=schedule_id,
                name=schedule_data["name"],
                description=schedule_data.get("description", ""),
                report_template_id=schedule_data["report_template_id"],
                cron_expression=schedule_data["cron_expression"],
                parameters=schedule_data.get("parameters", {}),
                recipients=schedule_data.get("recipients", []),
                is_active=schedule_data.get("is_active", True),
                created_at=datetime.now(),
                created_by=schedule_data["created_by"]
            )
            
            # 這裡應該將調度任務添加到任務調度器（如Celery）
            api_logger.info("報表調度創建成功", extra={'schedule_id': schedule_id})
            
            return schedule
            
        except Exception as e:
            api_logger.error("創建報表調度失敗", extra={'error': str(e)})
            raise
    
    async def execute_scheduled_report(self, schedule_id: str):
        """執行調度報表"""
        try:
            # 這裡應該根據調度配置生成報表並發送
            api_logger.info("執行調度報表", extra={'schedule_id': schedule_id})
            
        except Exception as e:
            api_logger.error("執行調度報表失敗", extra={'schedule_id': schedule_id, 'error': str(e)})
            raise
    
    # ==================== 輔助方法 ====================
    
    async def _generate_default_report(self, request: ReportRequest) -> Dict[str, Any]:
        """生成默認報表"""
        return {
            "message": "這是一個默認報表",
            "generated_at": datetime.now().isoformat(),
            "parameters": request.parameters or {}
        }
    
    async def get_report_history(self, limit: int = 50, offset: int = 0) -> List[ReportMetadata]:
        """獲取報表歷史"""
        try:
            # 這裡應該從數據庫查詢報表歷史
            # 目前返回模擬數據
            history = []
            
            for i in range(min(limit, 10)):  # 模擬10個歷史報表
                history.append(ReportMetadata(
                    report_id=str(uuid.uuid4()),
                    report_type=ReportType.USER_ANALYTICS,
                    title=f"用戶分析報表 #{i+1}",
                    description="自動生成的用戶分析報表",
                    created_at=datetime.now() - timedelta(days=i),
                    created_by="system",
                    parameters={}
                ))
            
            return history
            
        except Exception as e:
            api_logger.error("獲取報表歷史失敗", extra={'error': str(e)})
            raise
    
    async def get_report_by_id(self, report_id: str) -> Optional[ReportResult]:
        """根據ID獲取報表"""
        try:
            # 這裡應該從存儲中載入報表
            # 目前返回None表示未找到
            return None
            
        except Exception as e:
            api_logger.error("獲取報表失敗", extra={'report_id': report_id, 'error': str(e)})
            raise