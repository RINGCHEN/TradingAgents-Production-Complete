#!/usr/bin/env python3
"""
Capability Monitoring Dashboard
能力監控儀表板 - GPT-OSS整合任務1.2.3
"""

import asyncio
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from ..database.model_capability_db import ModelCapabilityDB
from ..monitoring.performance_monitor import PerformanceMonitor
from .model_version_control import ModelVersionControl
from .dynamic_capability_updater import DynamicCapabilityUpdater
from .capability_alert_system import CapabilityAlertSystem, AlertSeverity
from .ab_testing_system import ABTestingSystem, ExperimentStatus

logger = logging.getLogger(__name__)

class DashboardMetricType(Enum):
    """儀表板指標類型"""
    CAPABILITY_SCORE = "capability_score"
    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    COST = "cost"
    USAGE = "usage"
    ALERTS = "alerts"
    EXPERIMENTS = "experiments"
    VERSIONS = "versions"

class ReportType(Enum):
    """報告類型"""
    DAILY_SUMMARY = "daily_summary"
    WEEKLY_ANALYSIS = "weekly_analysis"
    MONTHLY_OVERVIEW = "monthly_overview"
    CAPABILITY_TREND = "capability_trend"
    PERFORMANCE_BENCHMARK = "performance_benchmark"
    ALERT_SUMMARY = "alert_summary"
    EXPERIMENT_RESULTS = "experiment_results"

@dataclass
class DashboardWidget:
    """儀表板組件"""
    widget_id: str
    widget_type: str
    title: str
    description: str
    data_source: str
    refresh_interval_seconds: int = 60
    configuration: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, int] = field(default_factory=dict)  # x, y, width, height

@dataclass
class DashboardLayout:
    """儀表板佈局"""
    layout_id: str
    layout_name: str
    widgets: List[DashboardWidget]
    created_by: str = "system"
    is_default: bool = False

class CapabilityDashboard:
    """
    能力監控儀表板
    
    功能：
    1. 實時數據聚合和展示
    2. 多種圖表和可視化
    3. 自定義儀表板佈局
    4. 報告生成和導出
    5. 趨勢分析和預測
    6. 告警集成和通知
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        version_control: Optional[ModelVersionControl] = None,
        capability_updater: Optional[DynamicCapabilityUpdater] = None,
        alert_system: Optional[CapabilityAlertSystem] = None,
        ab_testing_system: Optional[ABTestingSystem] = None
    ):
        """初始化儀表板"""
        self.model_db = model_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.version_control = version_control or ModelVersionControl()
        self.capability_updater = capability_updater or DynamicCapabilityUpdater()
        self.alert_system = alert_system or CapabilityAlertSystem()
        self.ab_testing_system = ab_testing_system or ABTestingSystem()
        
        self.logger = logger
        
        # 儀表板配置
        self.layouts: Dict[str, DashboardLayout] = {}
        self.data_cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # 運行時狀態
        self._running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # 初始化默認佈局
        self._initialize_default_layouts()
    
    def _initialize_default_layouts(self):
        """初始化默認儀表板佈局"""
        # 概覽儀表板
        overview_widgets = [
            DashboardWidget(
                widget_id="system_overview",
                widget_type="metrics_overview",
                title="System Overview",
                description="Key system metrics at a glance",
                data_source="system_metrics",
                position={"x": 0, "y": 0, "width": 12, "height": 4}
            ),
            DashboardWidget(
                widget_id="model_capabilities",
                widget_type="capability_chart",
                title="Model Capabilities",
                description="Capability scores by provider and model",
                data_source="model_capabilities",
                position={"x": 0, "y": 4, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="performance_trends",
                widget_type="time_series",
                title="Performance Trends",
                description="Performance metrics over time",
                data_source="performance_trends",
                position={"x": 6, "y": 4, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="active_alerts",
                widget_type="alert_list",
                title="Active Alerts",
                description="Current system alerts",
                data_source="active_alerts",
                position={"x": 0, "y": 10, "width": 12, "height": 4}
            )
        ]
        
        self.layouts["overview"] = DashboardLayout(
            layout_id="overview",
            layout_name="System Overview",
            widgets=overview_widgets,
            is_default=True
        )
        
        # 性能監控儀表板
        performance_widgets = [
            DashboardWidget(
                widget_id="latency_metrics",
                widget_type="latency_chart",
                title="Response Latency",
                description="Model response latency distribution",
                data_source="latency_metrics",
                position={"x": 0, "y": 0, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="throughput_metrics",
                widget_type="throughput_chart",
                title="Request Throughput",
                description="Requests per minute by model",
                data_source="throughput_metrics",
                position={"x": 6, "y": 0, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="error_rates",
                widget_type="error_chart",
                title="Error Rates",
                description="Error rates by model and error type",
                data_source="error_rates",
                position={"x": 0, "y": 6, "width": 6, "height": 6}
            ),
            DashboardWidget(
                widget_id="availability_status",
                widget_type="availability_grid",
                title="Model Availability",
                description="Current availability status of all models",
                data_source="availability_status",
                position={"x": 6, "y": 6, "width": 6, "height": 6}
            )
        ]
        
        self.layouts["performance"] = DashboardLayout(
            layout_id="performance",
            layout_name="Performance Monitoring",
            widgets=performance_widgets
        )
        
        # 實驗分析儀表板
        experiment_widgets = [
            DashboardWidget(
                widget_id="active_experiments",
                widget_type="experiment_list",
                title="Active Experiments",
                description="Currently running A/B tests and canary deployments",
                data_source="active_experiments",
                position={"x": 0, "y": 0, "width": 12, "height": 4}
            ),
            DashboardWidget(
                widget_id="experiment_results",
                widget_type="experiment_comparison",
                title="Experiment Results",
                description="Performance comparison between variants",
                data_source="experiment_results",
                position={"x": 0, "y": 4, "width": 12, "height": 8}
            )
        ]
        
        self.layouts["experiments"] = DashboardLayout(
            layout_id="experiments",
            layout_name="A/B Testing & Experiments",
            widgets=experiment_widgets
        )
    
    async def start(self):
        """啟動儀表板"""
        if not self._running:
            self._running = True
            self._update_task = asyncio.create_task(self._update_loop())
            self.logger.info("✅ Capability dashboard started")
    
    async def stop(self):
        """停止儀表板"""
        if self._running:
            self._running = False
            
            if self._update_task:
                self._update_task.cancel()
                try:
                    await self._update_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("✅ Capability dashboard stopped")
    
    async def _update_loop(self):
        """數據更新循環"""
        while self._running:
            try:
                await self._update_all_data_sources()
                await asyncio.sleep(30)  # 每30秒更新一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in dashboard update loop: {e}")
                await asyncio.sleep(10)
    
    async def _update_all_data_sources(self):
        """更新所有數據源"""
        try:
            # 並行更新各種數據源
            update_tasks = [
                self._update_system_metrics(),
                self._update_model_capabilities(),
                self._update_performance_trends(),
                self._update_active_alerts(),
                self._update_experiment_data(),
                self._update_version_data()
            ]
            
            await asyncio.gather(*update_tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating data sources: {e}")
    
    # ==================== 數據源更新 ====================
    
    async def _update_system_metrics(self):
        """更新系統指標"""
        try:
            # 獲取模型統計
            model_stats = await self.model_db.get_performance_statistics()
            
            # 獲取更新器統計
            updater_stats = self.capability_updater.get_update_status()
            
            # 獲取告警統計
            alert_stats = self.alert_system.get_alert_statistics()
            
            # 獲取實驗統計
            experiment_stats = self.ab_testing_system.get_system_statistics()
            
            system_metrics = {
                'total_models': model_stats.get('total_models', 0),
                'available_models': len(await self.model_db.list_model_capabilities(is_available=True)),
                'active_alerts': alert_stats.get('active_alerts', 0),
                'running_experiments': experiment_stats.get('active_experiments', 0),
                'update_queue_size': updater_stats.get('queued_tasks', 0),
                'total_updates': updater_stats.get('total_updates', 0),
                'success_rate': (
                    updater_stats.get('successful_updates', 0) / 
                    max(updater_stats.get('total_updates', 1), 1) * 100
                ),
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            self._cache_data('system_metrics', system_metrics)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating system metrics: {e}")
    
    async def _update_model_capabilities(self):
        """更新模型能力數據"""
        try:
            models = await self.model_db.list_model_capabilities(is_available=True)
            
            capabilities_data = {
                'by_provider': {},
                'by_capability_score': [],
                'top_performers': [],
                'cost_analysis': [],
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # 按提供商分組
            for model in models:
                if model.provider not in capabilities_data['by_provider']:
                    capabilities_data['by_provider'][model.provider] = []
                
                model_data = {
                    'model_id': model.model_id,
                    'model_name': model.model_name,
                    'capability_score': model.capability_score or 0.0,
                    'cost_per_1k': model.cost_per_1k_input_tokens or 0.0,
                    'avg_latency_ms': model.avg_latency_ms or 0.0,
                    'privacy_level': model.privacy_level
                }
                
                capabilities_data['by_provider'][model.provider].append(model_data)
                capabilities_data['by_capability_score'].append(model_data)
            
            # 按能力評分排序
            capabilities_data['by_capability_score'].sort(
                key=lambda x: x['capability_score'], reverse=True
            )
            
            # 取前10名
            capabilities_data['top_performers'] = capabilities_data['by_capability_score'][:10]
            
            # 成本分析
            capabilities_data['cost_analysis'] = [
                {
                    'model': f"{m.provider}/{m.model_id}",
                    'cost_per_1k': m.cost_per_1k_input_tokens or 0.0,
                    'capability_score': m.capability_score or 0.0,
                    'value_score': (m.capability_score or 0.0) / max(m.cost_per_1k_input_tokens or 0.001, 0.001)
                }
                for m in models
            ]
            
            capabilities_data['cost_analysis'].sort(
                key=lambda x: x['value_score'], reverse=True
            )
            
            self._cache_data('model_capabilities', capabilities_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating model capabilities: {e}")
    
    async def _update_performance_trends(self):
        """更新性能趨勢數據"""
        try:
            # 獲取過去24小時的性能數據
            current_metrics = self.performance_monitor.get_current_metrics()
            
            trends_data = {
                'latency_trends': [],
                'throughput_trends': [],
                'error_trends': [],
                'capability_trends': [],
                'time_range': '24h',
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # 處理延遲趨勢
            for metric_key, stats in current_metrics.items():
                if 'latency' in metric_key:
                    provider_model = '/'.join(metric_key.split('/')[:-1])
                    trends_data['latency_trends'].append({
                        'model': provider_model,
                        'mean_latency': stats.get('mean', 0),
                        'p95_latency': stats.get('p95', 0),
                        'sample_count': stats.get('count', 0)
                    })
            
            # 處理錯誤率趨勢
            for metric_key, stats in current_metrics.items():
                if 'error_rate' in metric_key:
                    provider_model = '/'.join(metric_key.split('/')[:-1])
                    trends_data['error_trends'].append({
                        'model': provider_model,
                        'error_rate': stats.get('mean', 0) * 100,  # 轉換為百分比
                        'sample_count': stats.get('count', 0)
                    })
            
            self._cache_data('performance_trends', trends_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating performance trends: {e}")
    
    async def _update_active_alerts(self):
        """更新活躍告警"""
        try:
            active_alerts = self.alert_system.get_active_alerts()
            
            alerts_data = {
                'alerts': active_alerts,
                'summary': {
                    'total': len(active_alerts),
                    'critical': len([a for a in active_alerts if a['severity'] == 'critical']),
                    'high': len([a for a in active_alerts if a['severity'] == 'high']),
                    'medium': len([a for a in active_alerts if a['severity'] == 'medium']),
                    'low': len([a for a in active_alerts if a['severity'] == 'low'])
                },
                'by_type': {},
                'by_model': {},
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # 按類型分組
            for alert in active_alerts:
                alert_type = alert.get('type', 'unknown')
                if alert_type not in alerts_data['by_type']:
                    alerts_data['by_type'][alert_type] = 0
                alerts_data['by_type'][alert_type] += 1
            
            # 按模型分組
            for alert in active_alerts:
                model_key = f"{alert.get('provider', 'unknown')}/{alert.get('model_id', 'unknown')}"
                if model_key not in alerts_data['by_model']:
                    alerts_data['by_model'][model_key] = 0
                alerts_data['by_model'][model_key] += 1
            
            self._cache_data('active_alerts', alerts_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating active alerts: {e}")
    
    async def _update_experiment_data(self):
        """更新實驗數據"""
        try:
            # 獲取活躍實驗
            active_experiments = self.ab_testing_system.list_experiments(status=ExperimentStatus.RUNNING)
            
            # 獲取最近完成的實驗
            completed_experiments = self.ab_testing_system.list_experiments(status=ExperimentStatus.COMPLETED)
            recent_completed = sorted(
                completed_experiments, 
                key=lambda x: x['created_at'], 
                reverse=True
            )[:10]
            
            experiment_data = {
                'active_experiments': active_experiments,
                'recent_completed': recent_completed,
                'summary': {
                    'active_count': len(active_experiments),
                    'completed_count': len(completed_experiments),
                    'success_rate': self._calculate_experiment_success_rate(completed_experiments)
                },
                'results_analysis': [],
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # 分析實驗結果
            for exp in recent_completed[:5]:  # 分析最近5個完成的實驗
                if exp.get('decision') == 'promote_variant':
                    analysis = await self.ab_testing_system.analyze_experiment_results(exp['experiment_id'])
                    if analysis and 'metric_comparisons' in analysis:
                        experiment_data['results_analysis'].append({
                            'experiment_name': exp['experiment_name'],
                            'decision': exp['decision'],
                            'key_improvements': self._extract_key_improvements(analysis)
                        })
            
            self._cache_data('experiment_data', experiment_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating experiment data: {e}")
    
    async def _update_version_data(self):
        """更新版本數據"""
        try:
            # 獲取所有模型的版本歷史摘要
            models = await self.model_db.list_model_capabilities(limit=20)
            
            version_data = {
                'version_summary': [],
                'recent_changes': [],
                'deployment_stages': {},
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            for model in models:
                try:
                    # 獲取版本歷史
                    history = await self.version_control.get_version_history(
                        model.provider, model.model_id, limit=5
                    )
                    
                    if history:
                        latest_version = history[0]
                        version_data['version_summary'].append({
                            'model': f"{model.provider}/{model.model_id}",
                            'latest_version': latest_version['version'],
                            'deployment_stage': latest_version['deployment_stage'],
                            'created_at': latest_version['created_at'],
                            'changes_count': latest_version['changes_count']
                        })
                        
                        # 收集部署階段統計
                        stage = latest_version['deployment_stage']
                        if stage not in version_data['deployment_stages']:
                            version_data['deployment_stages'][stage] = 0
                        version_data['deployment_stages'][stage] += 1
                        
                        # 收集最近變更
                        if len(history) > 1:
                            version_data['recent_changes'].append({
                                'model': f"{model.provider}/{model.model_id}",
                                'change_summary': latest_version.get('change_summary', ''),
                                'change_type': latest_version.get('change_type', ''),
                                'created_at': latest_version['created_at']
                            })
                
                except Exception as e:
                    self.logger.debug(f"Could not get version history for {model.provider}/{model.model_id}: {e}")
            
            # 按時間排序最近變更
            version_data['recent_changes'].sort(
                key=lambda x: x['created_at'], 
                reverse=True
            )
            version_data['recent_changes'] = version_data['recent_changes'][:20]
            
            self._cache_data('version_data', version_data)
            
        except Exception as e:
            self.logger.error(f"❌ Error updating version data: {e}")
    
    def _calculate_experiment_success_rate(self, experiments: List[Dict[str, Any]]) -> float:
        """計算實驗成功率"""
        if not experiments:
            return 0.0
        
        successful = len([exp for exp in experiments if exp.get('decision') == 'promote_variant'])
        return (successful / len(experiments)) * 100
    
    def _extract_key_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """提取關鍵改進點"""
        improvements = []
        
        try:
            metric_comparisons = analysis.get('metric_comparisons', {})
            
            for metric_name, metric_analysis in metric_comparisons.items():
                for comparison in metric_analysis.get('variant_comparisons', []):
                    improvement = comparison.get('improvement', {})
                    relative_improvement = improvement.get('relative_improvement_percent', 0)
                    
                    if relative_improvement > 5:
                        improvements.append(f"{metric_name}: +{relative_improvement:.1f}%")
        
        except Exception as e:
            self.logger.error(f"❌ Error extracting improvements: {e}")
        
        return improvements
    
    def _cache_data(self, data_source: str, data: Any):
        """緩存數據"""
        self.data_cache[data_source] = data
        self.cache_timestamps[data_source] = datetime.now(timezone.utc)
    
    def _get_cached_data(self, data_source: str, max_age_seconds: int = 300) -> Optional[Any]:
        """獲取緩存數據"""
        if data_source not in self.data_cache:
            return None
        
        cache_time = self.cache_timestamps.get(data_source)
        if not cache_time:
            return None
        
        age = (datetime.now(timezone.utc) - cache_time).total_seconds()
        if age > max_age_seconds:
            return None
        
        return self.data_cache[data_source]
    
    # ==================== 公共API ====================
    
    async def get_dashboard_data(
        self,
        layout_id: str = "overview",
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """獲取儀表板數據"""
        try:
            if layout_id not in self.layouts:
                raise ValueError(f"Layout {layout_id} not found")
            
            layout = self.layouts[layout_id]
            dashboard_data = {
                'layout': {
                    'layout_id': layout.layout_id,
                    'layout_name': layout.layout_name,
                    'widgets': [
                        {
                            'widget_id': w.widget_id,
                            'widget_type': w.widget_type,
                            'title': w.title,
                            'description': w.description,
                            'position': w.position,
                            'configuration': w.configuration
                        }
                        for w in layout.widgets
                    ]
                },
                'data': {},
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            # 獲取每個組件的數據
            for widget in layout.widgets:
                if force_refresh:
                    await self._update_widget_data(widget.data_source)
                
                widget_data = self._get_cached_data(widget.data_source)
                if widget_data:
                    dashboard_data['data'][widget.data_source] = widget_data
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting dashboard data: {e}")
            return {'error': str(e)}
    
    async def _update_widget_data(self, data_source: str):
        """更新特定組件數據"""
        if data_source == 'system_metrics':
            await self._update_system_metrics()
        elif data_source == 'model_capabilities':
            await self._update_model_capabilities()
        elif data_source == 'performance_trends':
            await self._update_performance_trends()
        elif data_source == 'active_alerts':
            await self._update_active_alerts()
        elif data_source == 'experiment_data':
            await self._update_experiment_data()
        elif data_source == 'version_data':
            await self._update_version_data()
    
    def list_layouts(self) -> List[Dict[str, Any]]:
        """列出所有佈局"""
        return [
            {
                'layout_id': layout.layout_id,
                'layout_name': layout.layout_name,
                'widget_count': len(layout.widgets),
                'created_by': layout.created_by,
                'is_default': layout.is_default
            }
            for layout in self.layouts.values()
        ]
    
    async def generate_report(
        self,
        report_type: ReportType,
        time_range_hours: int = 24,
        include_details: bool = True
    ) -> Dict[str, Any]:
        """生成報告"""
        try:
            if report_type == ReportType.DAILY_SUMMARY:
                return await self._generate_daily_summary_report(time_range_hours, include_details)
            elif report_type == ReportType.CAPABILITY_TREND:
                return await self._generate_capability_trend_report(time_range_hours, include_details)
            elif report_type == ReportType.ALERT_SUMMARY:
                return await self._generate_alert_summary_report(time_range_hours, include_details)
            elif report_type == ReportType.EXPERIMENT_RESULTS:
                return await self._generate_experiment_results_report(include_details)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
                
        except Exception as e:
            self.logger.error(f"❌ Error generating report: {e}")
            return {'error': str(e), 'report_type': report_type.value}
    
    async def _generate_daily_summary_report(
        self,
        time_range_hours: int,
        include_details: bool
    ) -> Dict[str, Any]:
        """生成每日摘要報告"""
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # 獲取基礎數據
            system_metrics = self._get_cached_data('system_metrics') or {}
            alerts_data = self._get_cached_data('active_alerts') or {}
            experiment_data = self._get_cached_data('experiment_data') or {}
            
            report = {
                'report_type': 'daily_summary',
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'hours': time_range_hours
                },
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'summary': {
                    'total_models': system_metrics.get('total_models', 0),
                    'available_models': system_metrics.get('available_models', 0),
                    'active_alerts': alerts_data.get('summary', {}).get('total', 0),
                    'critical_alerts': alerts_data.get('summary', {}).get('critical', 0),
                    'running_experiments': experiment_data.get('summary', {}).get('active_count', 0),
                    'system_availability': self._calculate_system_availability(),
                    'update_success_rate': system_metrics.get('success_rate', 0)
                },
                'key_metrics': await self._get_key_metrics_summary(),
                'alerts_breakdown': alerts_data.get('by_type', {}),
                'top_issues': await self._identify_top_issues(),
                'recommendations': await self._generate_daily_recommendations()
            }
            
            if include_details:
                report['detailed_metrics'] = await self._get_detailed_metrics()
                report['model_performance'] = await self._get_model_performance_details()
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating daily summary report: {e}")
            return {'error': str(e)}
    
    async def _generate_capability_trend_report(
        self,
        time_range_hours: int,
        include_details: bool
    ) -> Dict[str, Any]:
        """生成能力趨勢報告"""
        try:
            models = await self.model_db.list_model_capabilities(is_available=True)
            
            report = {
                'report_type': 'capability_trend',
                'time_range_hours': time_range_hours,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'models_analyzed': len(models),
                'capability_distribution': self._analyze_capability_distribution(models),
                'performance_trends': self._analyze_performance_trends(models),
                'improvement_opportunities': self._identify_improvement_opportunities(models)
            }
            
            if include_details:
                report['model_details'] = [
                    {
                        'provider': model.provider,
                        'model_id': model.model_id,
                        'capability_score': model.capability_score,
                        'avg_latency_ms': model.avg_latency_ms,
                        'cost_per_1k': model.cost_per_1k_input_tokens,
                        'last_updated': model.updated_at.isoformat() if model.updated_at else None
                    }
                    for model in models
                ]
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating capability trend report: {e}")
            return {'error': str(e)}
    
    async def _generate_alert_summary_report(
        self,
        time_range_hours: int,
        include_details: bool
    ) -> Dict[str, Any]:
        """生成告警摘要報告"""
        try:
            alerts_data = self._get_cached_data('active_alerts') or {}
            
            report = {
                'report_type': 'alert_summary',
                'time_range_hours': time_range_hours,
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'alert_summary': alerts_data.get('summary', {}),
                'alerts_by_type': alerts_data.get('by_type', {}),
                'alerts_by_model': alerts_data.get('by_model', {}),
                'severity_distribution': self._calculate_severity_distribution(alerts_data),
                'alert_trends': await self._analyze_alert_trends(),
                'resolution_recommendations': await self._generate_alert_recommendations()
            }
            
            if include_details:
                report['active_alerts'] = alerts_data.get('alerts', [])
                report['alert_patterns'] = await self._analyze_alert_patterns()
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating alert summary report: {e}")
            return {'error': str(e)}
    
    async def _generate_experiment_results_report(self, include_details: bool) -> Dict[str, Any]:
        """生成實驗結果報告"""
        try:
            experiment_data = self._get_cached_data('experiment_data') or {}
            
            report = {
                'report_type': 'experiment_results',
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'experiment_summary': experiment_data.get('summary', {}),
                'active_experiments': len(experiment_data.get('active_experiments', [])),
                'completed_experiments': len(experiment_data.get('recent_completed', [])),
                'key_results': experiment_data.get('results_analysis', []),
                'success_patterns': await self._analyze_experiment_success_patterns(),
                'recommendations': await self._generate_experiment_recommendations()
            }
            
            if include_details:
                report['active_experiment_details'] = experiment_data.get('active_experiments', [])
                report['completed_experiment_details'] = experiment_data.get('recent_completed', [])
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating experiment results report: {e}")
            return {'error': str(e)}
    
    # ==================== 分析輔助函數 ====================
    
    def _calculate_system_availability(self) -> float:
        """計算系統可用性"""
        try:
            system_metrics = self._get_cached_data('system_metrics') or {}
            total_models = system_metrics.get('total_models', 1)
            available_models = system_metrics.get('available_models', 0)
            
            return (available_models / total_models) * 100
            
        except Exception:
            return 0.0
    
    async def _get_key_metrics_summary(self) -> Dict[str, Any]:
        """獲取關鍵指標摘要"""
        try:
            models = await self.model_db.list_model_capabilities(is_available=True)
            
            if not models:
                return {}
            
            capability_scores = [m.capability_score for m in models if m.capability_score is not None]
            latencies = [m.avg_latency_ms for m in models if m.avg_latency_ms is not None]
            costs = [m.cost_per_1k_input_tokens for m in models if m.cost_per_1k_input_tokens is not None]
            
            return {
                'avg_capability_score': sum(capability_scores) / len(capability_scores) if capability_scores else 0,
                'avg_latency_ms': sum(latencies) / len(latencies) if latencies else 0,
                'avg_cost_per_1k': sum(costs) / len(costs) if costs else 0,
                'models_above_threshold': len([s for s in capability_scores if s > 0.8]),
                'high_performance_models': len([l for l in latencies if l < 2000])
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting key metrics summary: {e}")
            return {}
    
    async def _identify_top_issues(self) -> List[str]:
        """識別主要問題"""
        issues = []
        
        try:
            alerts_data = self._get_cached_data('active_alerts') or {}
            summary = alerts_data.get('summary', {})
            
            if summary.get('critical', 0) > 0:
                issues.append(f"{summary['critical']} critical alerts require immediate attention")
            
            if summary.get('high', 0) > 3:
                issues.append(f"{summary['high']} high-priority alerts detected")
            
            # 檢查系統可用性
            availability = self._calculate_system_availability()
            if availability < 95:
                issues.append(f"System availability is low ({availability:.1f}%)")
            
            # 檢查更新成功率
            system_metrics = self._get_cached_data('system_metrics') or {}
            success_rate = system_metrics.get('success_rate', 100)
            if success_rate < 90:
                issues.append(f"Update success rate is low ({success_rate:.1f}%)")
            
        except Exception as e:
            self.logger.error(f"❌ Error identifying top issues: {e}")
            issues.append("Error analyzing system issues")
        
        return issues[:5]  # 返回前5個問題
    
    async def _generate_daily_recommendations(self) -> List[str]:
        """生成每日建議"""
        recommendations = []
        
        try:
            # 基於告警生成建議
            alerts_data = self._get_cached_data('active_alerts') or {}
            by_type = alerts_data.get('by_type', {})
            
            if by_type.get('performance_degradation', 0) > 0:
                recommendations.append("Consider running performance benchmarks on affected models")
            
            if by_type.get('latency_spike', 0) > 0:
                recommendations.append("Review model configurations and optimize for latency")
            
            # 基於實驗數據生成建議
            experiment_data = self._get_cached_data('experiment_data') or {}
            if experiment_data.get('summary', {}).get('active_count', 0) == 0:
                recommendations.append("Consider starting A/B tests for model improvements")
            
            # 基於能力數據生成建議
            key_metrics = await self._get_key_metrics_summary()
            avg_capability = key_metrics.get('avg_capability_score', 0)
            
            if avg_capability < 0.7:
                recommendations.append("Overall capability scores are below target - consider model updates")
            
        except Exception as e:
            self.logger.error(f"❌ Error generating daily recommendations: {e}")
            recommendations.append("Error generating recommendations - manual review recommended")
        
        return recommendations[:5]
    
    def _analyze_capability_distribution(self, models) -> Dict[str, Any]:
        """分析能力分佈"""
        try:
            capability_scores = [m.capability_score for m in models if m.capability_score is not None]
            
            if not capability_scores:
                return {}
            
            import statistics
            
            return {
                'mean': statistics.mean(capability_scores),
                'median': statistics.median(capability_scores),
                'std': statistics.stdev(capability_scores) if len(capability_scores) > 1 else 0,
                'min': min(capability_scores),
                'max': max(capability_scores),
                'quartiles': {
                    'q1': statistics.quantiles(capability_scores, n=4)[0] if len(capability_scores) >= 4 else min(capability_scores),
                    'q3': statistics.quantiles(capability_scores, n=4)[2] if len(capability_scores) >= 4 else max(capability_scores)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing capability distribution: {e}")
            return {}
    
    # 其他分析函數的簡化實現...
    def _analyze_performance_trends(self, models) -> Dict[str, str]:
        return {"trend": "stable", "note": "Performance analysis requires historical data"}
    
    def _identify_improvement_opportunities(self, models) -> List[str]:
        return ["Enable more detailed performance tracking", "Implement automated benchmarking"]
    
    def _calculate_severity_distribution(self, alerts_data) -> Dict[str, int]:
        return alerts_data.get('summary', {})
    
    async def _analyze_alert_trends(self) -> Dict[str, str]:
        return {"trend": "stable", "note": "Alert trend analysis requires historical data"}
    
    async def _generate_alert_recommendations(self) -> List[str]:
        return ["Review alert thresholds", "Implement alert correlation"]
    
    async def _analyze_alert_patterns(self) -> Dict[str, str]:
        return {"patterns": "No significant patterns detected"}
    
    async def _analyze_experiment_success_patterns(self) -> Dict[str, str]:
        return {"patterns": "Limited historical data for pattern analysis"}
    
    async def _generate_experiment_recommendations(self) -> List[str]:
        return ["Plan more A/B tests", "Focus on performance improvements"]
    
    async def _get_detailed_metrics(self) -> Dict[str, Any]:
        return {"note": "Detailed metrics require extended implementation"}
    
    async def _get_model_performance_details(self) -> Dict[str, Any]:
        return {"note": "Performance details require historical tracking"}
    
    def get_dashboard_status(self) -> Dict[str, Any]:
        """獲取儀表板狀態"""
        return {
            'running': self._running,
            'layouts_count': len(self.layouts),
            'cached_data_sources': len(self.data_cache),
            'last_update': max(self.cache_timestamps.values()).isoformat() if self.cache_timestamps else None
        }