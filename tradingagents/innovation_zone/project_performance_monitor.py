#!/usr/bin/env python3
"""
Project Performance Monitoring System for Innovation Zone
創新特區項目性能監控系統 - GPT-OSS整合任務2.2.2

This system provides comprehensive performance monitoring specifically for innovation zone projects,
including:
1. Automatic ROI calculation (excluding innovation zone exemptions)
2. Project health assessment
3. Performance trend analysis
4. Resource utilization tracking
5. Milestone completion monitoring
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field

from .models import (
    InnovationProject, ProjectStage, ROIExemptionStatus,
    TechnicalMilestone, UserBehaviorMetrics, InnovationBudgetAllocation
)
from .innovation_zone_db import InnovationZoneDB

logger = logging.getLogger(__name__)


class ProjectHealthStatus(Enum):
    """項目健康狀況"""
    EXCELLENT = "excellent"      # 優秀
    GOOD = "good"               # 良好
    WARNING = "warning"         # 警告
    CRITICAL = "critical"       # 危急
    FAILED = "failed"           # 失敗


class PerformanceTrend(Enum):
    """性能趨勢"""
    IMPROVING = "improving"      # 改善中
    STABLE = "stable"           # 穩定
    DECLINING = "declining"     # 下降中
    VOLATILE = "volatile"       # 波動大


@dataclass
class ProjectPerformanceMetrics:
    """項目性能指標"""
    project_id: str
    project_name: str
    current_stage: ProjectStage
    
    # ROI 相關指標
    total_investment: Decimal = Decimal('0')
    total_return: Decimal = Decimal('0')
    roi_percentage: Optional[Decimal] = None
    is_roi_exempt: bool = False
    exemption_quarters_remaining: int = 0
    
    # 里程碑進度指標
    total_milestones: int = 0
    completed_milestones: int = 0
    milestone_completion_rate: Decimal = Decimal('0')
    average_milestone_quality: Decimal = Decimal('0')
    milestones_behind_schedule: int = 0
    
    # 預算指標
    budget_utilization_rate: Decimal = Decimal('0')
    budget_remaining: Decimal = Decimal('0')
    spending_velocity: Decimal = Decimal('0')  # 每月支出速度
    
    # 用戶參與度指標
    user_engagement_score: Decimal = Decimal('0')
    user_satisfaction_score: Decimal = Decimal('0')
    active_users_count: int = 0
    
    # 團隊效率指標
    team_productivity_score: Decimal = Decimal('0')
    team_size: int = 0
    developer_velocity: Decimal = Decimal('0')
    
    # 質量指標
    code_quality_score: Decimal = Decimal('0')
    bug_density: Decimal = Decimal('0')
    test_coverage: Decimal = Decimal('0')
    
    # 健康狀況
    overall_health: ProjectHealthStatus = ProjectHealthStatus.GOOD
    health_score: Decimal = Decimal('75')  # 0-100
    
    # 趨勢分析
    performance_trend: PerformanceTrend = PerformanceTrend.STABLE
    trend_confidence: Decimal = Decimal('0.5')  # 0-1
    
    # 風險指標
    risk_score: Decimal = Decimal('0')  # 0-100, 越高風險越大
    risk_factors: List[str] = field(default_factory=list)
    
    # 預測指標
    estimated_completion_date: Optional[datetime] = None
    success_probability: Decimal = Decimal('0.5')  # 0-1
    
    # 時間戳
    calculated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    

@dataclass
class ProjectPerformanceAlert:
    """項目性能警告"""
    project_id: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    details: Dict[str, Any]
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False


class ProjectPerformanceMonitor:
    """
    創新特區項目性能監控器
    
    功能：
    1. 自動ROI計算（排除創新特區豁免項目）
    2. 項目健康評估
    3. 性能趨勢分析
    4. 預算和資源使用監控
    5. 里程碑完成監控
    6. 團隊效率分析
    7. 用戶參與度追蹤
    8. 風險預測和告警
    """
    
    def __init__(
        self,
        innovation_db: Optional[InnovationZoneDB] = None
    ):
        """
        初始化項目性能監控器
        
        Args:
            innovation_db: 創新特區數據庫
        """
        self.innovation_db = innovation_db or InnovationZoneDB()
        
        # 配置項
        self.config = {
            'roi_calculation_enabled': True,
            'health_check_interval_minutes': 30,
            'trend_analysis_window_days': 30,
            'alert_thresholds': {
                'budget_utilization_high': 0.85,
                'milestone_delay_days': 7,
                'user_engagement_low': 0.6,
                'roi_negative_threshold': -0.1,
                'risk_score_high': 0.8
            },
            'performance_weights': {
                'milestone_progress': 0.25,
                'budget_efficiency': 0.20,
                'user_engagement': 0.20,
                'team_productivity': 0.15,
                'code_quality': 0.10,
                'roi_performance': 0.10
            }
        }
        
        # 性能歷史記錄
        self.performance_history: Dict[str, List[ProjectPerformanceMetrics]] = {}
        
        # 活躍告警
        self.active_alerts: Dict[str, List[ProjectPerformanceAlert]] = {}
        
        self.logger = logger
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start_monitoring(self):
        """開始性能監控"""
        if not self._running:
            self._running = True
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.logger.info("✅ Project Performance Monitor started")
    
    async def stop_monitoring(self):
        """停止性能監控"""
        if self._running:
            self._running = False
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            self.logger.info("✅ Project Performance Monitor stopped")
    
    async def _monitoring_loop(self):
        """監控循環"""
        while self._running:
            try:
                interval_minutes = self.config['health_check_interval_minutes']
                await asyncio.sleep(interval_minutes * 60)
                
                # 獲取所有活躍項目並計算性能指標
                await self._calculate_all_project_performance()
                
                # 執行健康檢查和告警
                await self._perform_health_checks()
                
                # 清理過期數據
                self._cleanup_old_data()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"❌ Error in performance monitoring loop: {e}")
    
    async def calculate_project_performance(
        self,
        project_id: str
    ) -> ProjectPerformanceMetrics:
        """
        計算單個項目的性能指標
        
        Args:
            project_id: 項目ID
            
        Returns:
            項目性能指標
        """
        try:
            # 獲取項目基本信息
            project = await self.innovation_db.get_innovation_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # 獲取相關數據
            milestones = await self.innovation_db.get_project_milestones(project_id)
            budget_allocations = await self.innovation_db.get_project_budget_tracking(project_id)
            user_metrics = await self.innovation_db.get_project_user_metrics(project_id)
            
            # 初始化性能指標對象
            metrics = ProjectPerformanceMetrics(
                project_id=project_id,
                project_name=project['project_name'],
                current_stage=ProjectStage(project['current_stage'])
            )
            
            # 計算ROI相關指標
            await self._calculate_roi_metrics(metrics, project, budget_allocations)
            
            # 計算里程碑進度指標
            await self._calculate_milestone_metrics(metrics, milestones)
            
            # 計算預算指標
            await self._calculate_budget_metrics(metrics, budget_allocations)
            
            # 計算用戶參與度指標
            await self._calculate_user_engagement_metrics(metrics, user_metrics)
            
            # 計算團隊效率指標
            await self._calculate_team_efficiency_metrics(metrics, project)
            
            # 計算質量指標
            await self._calculate_quality_metrics(metrics, project_id)
            
            # 計算整體健康狀況
            await self._calculate_overall_health(metrics)
            
            # 計算性能趨勢
            await self._calculate_performance_trend(metrics)
            
            # 計算風險指標
            await self._calculate_risk_indicators(metrics)
            
            # 預測項目完成
            await self._predict_project_completion(metrics)
            
            # 保存歷史記錄
            self._save_performance_history(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating project performance for {project_id}: {e}")
            raise
    
    async def _calculate_roi_metrics(
        self,
        metrics: ProjectPerformanceMetrics,
        project: Dict[str, Any],
        budget_allocations: List[Dict[str, Any]]
    ):
        """計算ROI相關指標"""
        try:
            # 檢查ROI豁免狀態
            roi_exemption_status = project.get('roi_exemption_status', 'active')
            metrics.is_roi_exempt = roi_exemption_status == 'active'
            
            if metrics.is_roi_exempt:
                # 計算剩餘豁免季度
                exemption_start = project.get('roi_exemption_start_date')
                if exemption_start:
                    exemption_start_dt = datetime.fromisoformat(exemption_start.replace('Z', '+00:00'))
                    months_elapsed = (datetime.now(timezone.utc) - exemption_start_dt).days // 30
                    quarters_elapsed = months_elapsed // 3
                    metrics.exemption_quarters_remaining = max(0, 4 - quarters_elapsed)
            
            # 計算總投資
            total_investment = Decimal('0')
            for allocation in budget_allocations:
                if allocation['transaction_type'] == 'allocation':
                    total_investment += Decimal(str(allocation['amount']))
            
            metrics.total_investment = total_investment
            
            # 計算總回報（如果非豁免項目）
            if not metrics.is_roi_exempt and self.config['roi_calculation_enabled']:
                # 這裡需要根據實際業務邏輯計算回報
                # 暫時使用模擬計算
                total_return = await self._calculate_project_return(project['id'])
                metrics.total_return = total_return
                
                # 計算ROI百分比
                if total_investment > 0:
                    roi = (total_return - total_investment) / total_investment * 100
                    metrics.roi_percentage = roi
                    
        except Exception as e:
            self.logger.error(f"❌ Error calculating ROI metrics: {e}")
    
    async def _calculate_milestone_metrics(
        self,
        metrics: ProjectPerformanceMetrics,
        milestones: List[Dict[str, Any]]
    ):
        """計算里程碑進度指標"""
        try:
            if not milestones:
                return
            
            metrics.total_milestones = len(milestones)
            
            completed_count = 0
            quality_scores = []
            behind_schedule = 0
            
            for milestone in milestones:
                if milestone.get('is_completed', False):
                    completed_count += 1
                
                # 質量評分
                quality_score = milestone.get('quality_score', 0)
                if quality_score > 0:
                    quality_scores.append(float(quality_score))
                
                # 檢查是否落後進度
                expected_date = milestone.get('expected_completion_date')
                actual_date = milestone.get('actual_completion_date')
                
                if expected_date and not milestone.get('is_completed', False):
                    expected_dt = datetime.fromisoformat(expected_date.replace('Z', '+00:00'))
                    if datetime.now(timezone.utc) > expected_dt:
                        behind_schedule += 1
            
            metrics.completed_milestones = completed_count
            metrics.milestone_completion_rate = Decimal(completed_count) / Decimal(len(milestones)) * 100
            metrics.milestones_behind_schedule = behind_schedule
            
            if quality_scores:
                metrics.average_milestone_quality = Decimal(str(sum(quality_scores) / len(quality_scores)))
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating milestone metrics: {e}")
    
    async def _calculate_budget_metrics(
        self,
        metrics: ProjectPerformanceMetrics,
        budget_allocations: List[Dict[str, Any]]
    ):
        """計算預算指標"""
        try:
            if not budget_allocations:
                return
            
            total_allocated = Decimal('0')
            total_spent = Decimal('0')
            monthly_expenses = []
            
            for allocation in budget_allocations:
                amount = Decimal(str(allocation['amount']))
                
                if allocation['transaction_type'] == 'allocation':
                    total_allocated += amount
                elif allocation['transaction_type'] == 'expense':
                    total_spent += amount
                    
                    # 計算月度支出
                    transaction_date = allocation.get('transaction_date')
                    if transaction_date:
                        # 簡化的月度支出計算
                        monthly_expenses.append({
                            'amount': amount,
                            'date': transaction_date
                        })
            
            if total_allocated > 0:
                metrics.budget_utilization_rate = total_spent / total_allocated * 100
                metrics.budget_remaining = total_allocated - total_spent
            
            # 計算支出速度（簡化版本）
            if monthly_expenses:
                recent_expenses = [exp for exp in monthly_expenses 
                                 if self._is_recent_transaction(exp['date'], days=30)]
                if recent_expenses:
                    total_recent = sum(exp['amount'] for exp in recent_expenses)
                    metrics.spending_velocity = total_recent
                    
        except Exception as e:
            self.logger.error(f"❌ Error calculating budget metrics: {e}")
    
    async def _calculate_user_engagement_metrics(
        self,
        metrics: ProjectPerformanceMetrics,
        user_metrics: List[Dict[str, Any]]
    ):
        """計算用戶參與度指標"""
        try:
            if not user_metrics:
                return
            
            engagement_scores = []
            satisfaction_scores = []
            total_active_users = 0
            
            for metric in user_metrics:
                engagement_score = metric.get('engagement_score')
                if engagement_score is not None:
                    engagement_scores.append(float(engagement_score))
                
                satisfaction_score = metric.get('user_satisfaction_score')
                if satisfaction_score is not None:
                    satisfaction_scores.append(float(satisfaction_score))
                
                active_users = metric.get('active_users_count', 0)
                total_active_users += active_users
            
            if engagement_scores:
                metrics.user_engagement_score = Decimal(str(sum(engagement_scores) / len(engagement_scores)))
            
            if satisfaction_scores:
                metrics.user_satisfaction_score = Decimal(str(sum(satisfaction_scores) / len(satisfaction_scores)))
            
            metrics.active_users_count = total_active_users
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating user engagement metrics: {e}")
    
    async def _calculate_team_efficiency_metrics(
        self,
        metrics: ProjectPerformanceMetrics,
        project: Dict[str, Any]
    ):
        """計算團隊效率指標"""
        try:
            metrics.team_size = project.get('team_size', 0)
            
            # 這裡需要根據實際的團隊效率數據進行計算
            # 暫時使用模擬值
            if metrics.milestone_completion_rate > 0:
                # 基於里程碑完成率計算團隊生產力
                base_productivity = min(100, metrics.milestone_completion_rate)
                metrics.team_productivity_score = base_productivity
                
                # 計算開發者速度（每人每月完成的里程碑）
                if metrics.team_size > 0:
                    velocity = float(metrics.completed_milestones) / metrics.team_size
                    metrics.developer_velocity = Decimal(str(velocity))
                    
        except Exception as e:
            self.logger.error(f"❌ Error calculating team efficiency metrics: {e}")
    
    async def _calculate_quality_metrics(
        self,
        metrics: ProjectPerformanceMetrics,
        project_id: str
    ):
        """計算質量指標"""
        try:
            # 這裡需要整合代碼質量分析工具的數據
            # 暫時使用基於里程碑質量的近似值
            if metrics.average_milestone_quality > 0:
                metrics.code_quality_score = metrics.average_milestone_quality
                
                # 基於質量評分估算其他指標
                quality_ratio = float(metrics.average_milestone_quality) / 100
                metrics.bug_density = Decimal(str(max(0, 10 * (1 - quality_ratio))))
                metrics.test_coverage = Decimal(str(min(100, quality_ratio * 100)))
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating quality metrics: {e}")
    
    async def _calculate_overall_health(self, metrics: ProjectPerformanceMetrics):
        """計算整體健康狀況"""
        try:
            weights = self.config['performance_weights']
            
            # 計算各個維度的得分
            milestone_score = float(metrics.milestone_completion_rate)
            
            budget_score = 100 - min(100, float(metrics.budget_utilization_rate))
            if metrics.budget_utilization_rate <= 85:
                budget_score = 100  # 預算使用合理
            
            engagement_score = float(metrics.user_engagement_score) * 100
            productivity_score = float(metrics.team_productivity_score)
            quality_score = float(metrics.code_quality_score)
            
            roi_score = 50  # 默認中性分數
            if metrics.roi_percentage is not None and not metrics.is_roi_exempt:
                if metrics.roi_percentage > 0:
                    roi_score = min(100, 50 + float(metrics.roi_percentage))
                else:
                    roi_score = max(0, 50 + float(metrics.roi_percentage))
            
            # 加權計算總分
            total_score = (
                milestone_score * weights['milestone_progress'] +
                budget_score * weights['budget_efficiency'] +
                engagement_score * weights['user_engagement'] +
                productivity_score * weights['team_productivity'] +
                quality_score * weights['code_quality'] +
                roi_score * weights['roi_performance']
            )
            
            metrics.health_score = Decimal(str(round(total_score, 2)))
            
            # 確定健康狀況等級
            if total_score >= 90:
                metrics.overall_health = ProjectHealthStatus.EXCELLENT
            elif total_score >= 75:
                metrics.overall_health = ProjectHealthStatus.GOOD
            elif total_score >= 60:
                metrics.overall_health = ProjectHealthStatus.WARNING
            elif total_score >= 40:
                metrics.overall_health = ProjectHealthStatus.CRITICAL
            else:
                metrics.overall_health = ProjectHealthStatus.FAILED
                
        except Exception as e:
            self.logger.error(f"❌ Error calculating overall health: {e}")
            metrics.health_score = Decimal('50')
            metrics.overall_health = ProjectHealthStatus.WARNING
    
    async def _calculate_performance_trend(self, metrics: ProjectPerformanceMetrics):
        """計算性能趨勢"""
        try:
            project_id = metrics.project_id
            
            if project_id not in self.performance_history:
                metrics.performance_trend = PerformanceTrend.STABLE
                metrics.trend_confidence = Decimal('0.5')
                return
            
            history = self.performance_history[project_id]
            if len(history) < 3:
                metrics.performance_trend = PerformanceTrend.STABLE
                metrics.trend_confidence = Decimal('0.5')
                return
            
            # 分析最近的健康分數趨勢
            recent_scores = [float(h.health_score) for h in history[-5:]]  # 最近5次記錄
            
            if len(recent_scores) >= 3:
                # 計算斜率來判斷趨勢
                n = len(recent_scores)
                x = list(range(n))
                y = recent_scores
                
                # 簡單線性回歸
                x_mean = sum(x) / n
                y_mean = sum(y) / n
                
                numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
                denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
                
                if denominator != 0:
                    slope = numerator / denominator
                    
                    # 計算變異係數來判斷穩定性
                    variance = sum((score - y_mean) ** 2 for score in recent_scores) / n
                    std_dev = variance ** 0.5
                    cv = std_dev / y_mean if y_mean != 0 else 0
                    
                    # 判斷趨勢
                    if cv > 0.15:  # 變異係數過大
                        metrics.performance_trend = PerformanceTrend.VOLATILE
                        metrics.trend_confidence = Decimal('0.8')
                    elif slope > 2:
                        metrics.performance_trend = PerformanceTrend.IMPROVING
                        metrics.trend_confidence = Decimal('0.8')
                    elif slope < -2:
                        metrics.performance_trend = PerformanceTrend.DECLINING
                        metrics.trend_confidence = Decimal('0.8')
                    else:
                        metrics.performance_trend = PerformanceTrend.STABLE
                        metrics.trend_confidence = Decimal('0.7')
                        
        except Exception as e:
            self.logger.error(f"❌ Error calculating performance trend: {e}")
            metrics.performance_trend = PerformanceTrend.STABLE
            metrics.trend_confidence = Decimal('0.5')
    
    async def _calculate_risk_indicators(self, metrics: ProjectPerformanceMetrics):
        """計算風險指標"""
        try:
            risk_factors = []
            risk_score = 0
            
            # 預算風險
            if metrics.budget_utilization_rate > 90:
                risk_factors.append("High budget utilization")
                risk_score += 20
            
            # 里程碑風險
            if metrics.milestones_behind_schedule > 2:
                risk_factors.append("Multiple milestones behind schedule")
                risk_score += 25
            
            # ROI風險
            if (metrics.roi_percentage is not None and 
                not metrics.is_roi_exempt and 
                metrics.roi_percentage < -10):
                risk_factors.append("Negative ROI performance")
                risk_score += 30
            
            # 用戶參與度風險
            if metrics.user_engagement_score < 60:
                risk_factors.append("Low user engagement")
                risk_score += 15
            
            # 團隊效率風險
            if metrics.team_productivity_score < 50:
                risk_factors.append("Low team productivity")
                risk_score += 20
            
            # 代碼質量風險
            if metrics.code_quality_score < 60:
                risk_factors.append("Poor code quality")
                risk_score += 15
            
            # 趨勢風險
            if metrics.performance_trend == PerformanceTrend.DECLINING:
                risk_factors.append("Declining performance trend")
                risk_score += 25
            
            metrics.risk_score = Decimal(str(min(100, risk_score)))
            metrics.risk_factors = risk_factors
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating risk indicators: {e}")
            metrics.risk_score = Decimal('50')
    
    async def _predict_project_completion(self, metrics: ProjectPerformanceMetrics):
        """預測項目完成"""
        try:
            if metrics.milestone_completion_rate <= 0:
                return
            
            # 基於當前進度預測完成時間
            remaining_progress = 100 - float(metrics.milestone_completion_rate)
            
            if remaining_progress <= 0:
                metrics.estimated_completion_date = datetime.now(timezone.utc)
                metrics.success_probability = Decimal('0.95')
                return
            
            # 估算剩餘時間（簡化模型）
            # 假設線性進度，基於團隊生產力調整
            productivity_factor = max(0.1, float(metrics.team_productivity_score) / 100)
            
            # 基礎完成時間（天）
            base_days = remaining_progress / productivity_factor * 30  # 假設每月10%進度
            
            # 根據風險調整
            risk_factor = 1 + float(metrics.risk_score) / 200  # 風險越高，時間越長
            adjusted_days = base_days * risk_factor
            
            estimated_date = datetime.now(timezone.utc) + timedelta(days=int(adjusted_days))
            metrics.estimated_completion_date = estimated_date
            
            # 計算成功概率
            health_factor = float(metrics.health_score) / 100
            trend_factor = {
                PerformanceTrend.IMPROVING: 1.2,
                PerformanceTrend.STABLE: 1.0,
                PerformanceTrend.DECLINING: 0.8,
                PerformanceTrend.VOLATILE: 0.7
            }.get(metrics.performance_trend, 1.0)
            
            success_prob = min(0.95, health_factor * trend_factor * 0.8)
            metrics.success_probability = Decimal(str(round(success_prob, 3)))
            
        except Exception as e:
            self.logger.error(f"❌ Error predicting project completion: {e}")
    
    def _save_performance_history(self, metrics: ProjectPerformanceMetrics):
        """保存性能歷史記錄"""
        try:
            project_id = metrics.project_id
            
            if project_id not in self.performance_history:
                self.performance_history[project_id] = []
            
            # 添加新記錄
            self.performance_history[project_id].append(metrics)
            
            # 限制歷史記錄數量
            max_history = 100
            if len(self.performance_history[project_id]) > max_history:
                self.performance_history[project_id] = self.performance_history[project_id][-max_history:]
                
        except Exception as e:
            self.logger.error(f"❌ Error saving performance history: {e}")
    
    async def _calculate_all_project_performance(self):
        """計算所有項目的性能指標"""
        try:
            # 獲取所有活躍項目
            active_projects = await self.innovation_db.get_active_projects()
            
            for project in active_projects:
                project_id = project['id']
                try:
                    await self.calculate_project_performance(project_id)
                except Exception as e:
                    self.logger.error(f"❌ Error calculating performance for project {project_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"❌ Error in calculate_all_project_performance: {e}")
    
    async def _perform_health_checks(self):
        """執行健康檢查和告警"""
        try:
            thresholds = self.config['alert_thresholds']
            
            for project_id, history in self.performance_history.items():
                if not history:
                    continue
                
                latest_metrics = history[-1]
                project_alerts = []
                
                # 檢查各種告警條件
                # 預算使用率高
                if latest_metrics.budget_utilization_rate > thresholds['budget_utilization_high'] * 100:
                    project_alerts.append(ProjectPerformanceAlert(
                        project_id=project_id,
                        alert_type="budget_high_utilization",
                        severity="high",
                        message=f"Budget utilization is {latest_metrics.budget_utilization_rate:.1f}%",
                        details={'utilization_rate': float(latest_metrics.budget_utilization_rate)}
                    ))
                
                # 里程碑延期
                if latest_metrics.milestones_behind_schedule > 0:
                    severity = "critical" if latest_metrics.milestones_behind_schedule > 3 else "medium"
                    project_alerts.append(ProjectPerformanceAlert(
                        project_id=project_id,
                        alert_type="milestone_delays",
                        severity=severity,
                        message=f"{latest_metrics.milestones_behind_schedule} milestones behind schedule",
                        details={'delayed_milestones': latest_metrics.milestones_behind_schedule}
                    ))
                
                # 用戶參與度低
                if latest_metrics.user_engagement_score < thresholds['user_engagement_low'] * 100:
                    project_alerts.append(ProjectPerformanceAlert(
                        project_id=project_id,
                        alert_type="low_user_engagement",
                        severity="medium",
                        message=f"User engagement score is {latest_metrics.user_engagement_score:.1f}",
                        details={'engagement_score': float(latest_metrics.user_engagement_score)}
                    ))
                
                # 負ROI（非豁免項目）
                if (not latest_metrics.is_roi_exempt and 
                    latest_metrics.roi_percentage is not None and
                    latest_metrics.roi_percentage < thresholds['roi_negative_threshold'] * 100):
                    project_alerts.append(ProjectPerformanceAlert(
                        project_id=project_id,
                        alert_type="negative_roi",
                        severity="high",
                        message=f"ROI is {latest_metrics.roi_percentage:.1f}%",
                        details={'roi_percentage': float(latest_metrics.roi_percentage)}
                    ))
                
                # 高風險分數
                if latest_metrics.risk_score > thresholds['risk_score_high'] * 100:
                    project_alerts.append(ProjectPerformanceAlert(
                        project_id=project_id,
                        alert_type="high_risk_score",
                        severity="high",
                        message=f"Risk score is {latest_metrics.risk_score:.1f}",
                        details={
                            'risk_score': float(latest_metrics.risk_score),
                            'risk_factors': latest_metrics.risk_factors
                        }
                    ))
                
                # 更新活躍告警
                if project_alerts:
                    self.active_alerts[project_id] = project_alerts
                    
                    # 記錄告警
                    for alert in project_alerts:
                        self.logger.warning(
                            f"⚠️ Project Alert [{alert.severity.upper()}] "
                            f"{latest_metrics.project_name}: {alert.message}"
                        )
                        
        except Exception as e:
            self.logger.error(f"❌ Error performing health checks: {e}")
    
    def _cleanup_old_data(self):
        """清理過期數據"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=90)
            
            for project_id, history in self.performance_history.items():
                # 保留最近90天的數據
                self.performance_history[project_id] = [
                    metrics for metrics in history
                    if metrics.calculated_at >= cutoff_date
                ]
                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old data: {e}")
    
    def _is_recent_transaction(self, transaction_date: str, days: int = 30) -> bool:
        """檢查交易是否在指定天數內"""
        try:
            trans_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            return trans_date >= cutoff_date
        except:
            return False
    
    async def _calculate_project_return(self, project_id: str) -> Decimal:
        """計算項目回報（需要根據實際業務邏輯實現）"""
        # 這是一個模擬實現
        # 實際中需要根據項目類型、收益模型等計算實際回報
        return Decimal('0')
    
    async def get_project_performance_report(
        self,
        project_id: Optional[str] = None,
        include_history: bool = True
    ) -> Dict[str, Any]:
        """
        獲取項目性能報告
        
        Args:
            project_id: 項目ID，為空則返回所有項目
            include_history: 是否包含歷史數據
            
        Returns:
            性能報告
        """
        try:
            report = {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'projects': {}
            }
            
            if project_id:
                # 單個項目報告
                if project_id in self.performance_history and self.performance_history[project_id]:
                    latest_metrics = self.performance_history[project_id][-1]
                    project_report = {
                        'latest_metrics': self._metrics_to_dict(latest_metrics),
                        'active_alerts': [
                            self._alert_to_dict(alert) 
                            for alert in self.active_alerts.get(project_id, [])
                        ]
                    }
                    
                    if include_history:
                        project_report['history'] = [
                            self._metrics_to_dict(metrics)
                            for metrics in self.performance_history[project_id][-10:]  # 最近10次記錄
                        ]
                    
                    report['projects'][project_id] = project_report
            else:
                # 所有項目報告
                for pid, history in self.performance_history.items():
                    if not history:
                        continue
                    
                    latest_metrics = history[-1]
                    project_report = {
                        'latest_metrics': self._metrics_to_dict(latest_metrics),
                        'active_alerts': [
                            self._alert_to_dict(alert)
                            for alert in self.active_alerts.get(pid, [])
                        ]
                    }
                    
                    if include_history:
                        project_report['history'] = [
                            self._metrics_to_dict(metrics)
                            for metrics in history[-5:]  # 最近5次記錄
                        ]
                    
                    report['projects'][pid] = project_report
            
            # 添加摘要統計
            report['summary'] = self._generate_summary_statistics()
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating performance report: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
    
    def _metrics_to_dict(self, metrics: ProjectPerformanceMetrics) -> Dict[str, Any]:
        """將性能指標轉換為字典"""
        return {
            'project_id': metrics.project_id,
            'project_name': metrics.project_name,
            'current_stage': metrics.current_stage.value,
            'roi_metrics': {
                'total_investment': float(metrics.total_investment),
                'total_return': float(metrics.total_return),
                'roi_percentage': float(metrics.roi_percentage) if metrics.roi_percentage else None,
                'is_roi_exempt': metrics.is_roi_exempt,
                'exemption_quarters_remaining': metrics.exemption_quarters_remaining
            },
            'milestone_metrics': {
                'total_milestones': metrics.total_milestones,
                'completed_milestones': metrics.completed_milestones,
                'completion_rate': float(metrics.milestone_completion_rate),
                'average_quality': float(metrics.average_milestone_quality),
                'behind_schedule': metrics.milestones_behind_schedule
            },
            'budget_metrics': {
                'utilization_rate': float(metrics.budget_utilization_rate),
                'budget_remaining': float(metrics.budget_remaining),
                'spending_velocity': float(metrics.spending_velocity)
            },
            'user_metrics': {
                'engagement_score': float(metrics.user_engagement_score),
                'satisfaction_score': float(metrics.user_satisfaction_score),
                'active_users_count': metrics.active_users_count
            },
            'team_metrics': {
                'productivity_score': float(metrics.team_productivity_score),
                'team_size': metrics.team_size,
                'developer_velocity': float(metrics.developer_velocity)
            },
            'quality_metrics': {
                'code_quality_score': float(metrics.code_quality_score),
                'bug_density': float(metrics.bug_density),
                'test_coverage': float(metrics.test_coverage)
            },
            'health': {
                'overall_health': metrics.overall_health.value,
                'health_score': float(metrics.health_score),
                'performance_trend': metrics.performance_trend.value,
                'trend_confidence': float(metrics.trend_confidence)
            },
            'risk': {
                'risk_score': float(metrics.risk_score),
                'risk_factors': metrics.risk_factors
            },
            'predictions': {
                'estimated_completion_date': metrics.estimated_completion_date.isoformat() if metrics.estimated_completion_date else None,
                'success_probability': float(metrics.success_probability)
            },
            'calculated_at': metrics.calculated_at.isoformat()
        }
    
    def _alert_to_dict(self, alert: ProjectPerformanceAlert) -> Dict[str, Any]:
        """將告警轉換為字典"""
        return {
            'project_id': alert.project_id,
            'alert_type': alert.alert_type,
            'severity': alert.severity,
            'message': alert.message,
            'details': alert.details,
            'triggered_at': alert.triggered_at.isoformat(),
            'resolved': alert.resolved
        }
    
    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """生成摘要統計"""
        try:
            total_projects = len(self.performance_history)
            active_alerts_count = sum(len(alerts) for alerts in self.active_alerts.values())
            
            if total_projects == 0:
                return {
                    'total_projects': 0,
                    'active_alerts': 0,
                    'average_health_score': 0,
                    'health_distribution': {}
                }
            
            # 計算平均健康分數
            health_scores = []
            health_distribution = {status.value: 0 for status in ProjectHealthStatus}
            
            for history in self.performance_history.values():
                if history:
                    latest = history[-1]
                    health_scores.append(float(latest.health_score))
                    health_distribution[latest.overall_health.value] += 1
            
            avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
            
            return {
                'total_projects': total_projects,
                'active_alerts': active_alerts_count,
                'average_health_score': round(avg_health, 2),
                'health_distribution': health_distribution
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error generating summary statistics: {e}")
            return {
                'total_projects': len(self.performance_history),
                'active_alerts': sum(len(alerts) for alerts in self.active_alerts.values()),
                'error': str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """服務健康檢查"""
        return {
            'service': 'project_performance_monitor',
            'status': 'healthy' if self._running else 'stopped',
            'total_projects_monitored': len(self.performance_history),
            'active_alerts': sum(len(alerts) for alerts in self.active_alerts.values()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }