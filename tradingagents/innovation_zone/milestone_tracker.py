#!/usr/bin/env python3
"""
Technical Milestone Tracker
技術里程碑追蹤引擎

專門用於追蹤創新項目的技術里程碑和用戶行為指標：
- 技術里程碑進度追蹤和質量評估
- 用戶行為指標收集和分析
- 里程碑依賴關係管理
- 智能進度預測和風險評估
- 里程碑成功標準驗證
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

from .models import MilestoneType, TechnicalMilestone
from .innovation_zone_db import InnovationZoneDB

logger = logging.getLogger(__name__)

class MilestoneStatus(str, Enum):
    """里程碑狀態枚舉"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELAYED = "delayed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class ProgressTrend(str, Enum):
    """進度趋势枚举"""
    AHEAD = "ahead"
    ON_TRACK = "on_track"
    SLIGHTLY_BEHIND = "slightly_behind"
    SIGNIFICANTLY_BEHIND = "significantly_behind"
    CRITICAL = "critical"

@dataclass
class MilestoneProgressUpdate:
    """里程碑進度更新"""
    milestone_id: uuid.UUID
    completion_rate: Decimal
    technical_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]
    blocking_issues: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    deliverables_completed: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    updated_by: str = "system"
    update_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

@dataclass
class MilestoneAnalytics:
    """里程碑分析數據"""
    milestone_id: uuid.UUID
    project_id: uuid.UUID
    current_status: str
    progress_trend: ProgressTrend
    completion_rate: Decimal
    days_remaining: int
    estimated_completion_date: Optional[date]
    quality_score: Optional[Decimal]
    risk_level: str
    success_probability: float
    dependencies_met: bool
    blocking_issues_count: int
    recommendations: List[str] = field(default_factory=list)

@dataclass
class ProjectMilestoneOverview:
    """項目里程碑概覽"""
    project_id: uuid.UUID
    total_milestones: int
    completed_milestones: int
    in_progress_milestones: int
    delayed_milestones: int
    overall_completion_rate: Decimal
    overall_progress_trend: ProgressTrend
    critical_path_milestones: List[uuid.UUID]
    next_milestone_due: Optional[Dict[str, Any]]
    estimated_project_completion: Optional[date]
    project_health_score: float

class TechnicalMilestoneTracker:
    """
    技術里程碑追蹤引擎
    
    功能：
    1. 里程碑進度追蹤和狀態管理
    2. 技術指標和質量評估
    3. 依賴關係和阻塞問題管理
    4. 智能進度預測和風險評估
    5. 用戶行為指標收集和分析
    6. 里程碑成功標準驗證
    """
    
    def __init__(self, innovation_db: Optional[InnovationZoneDB] = None):
        """初始化技術里程碑追蹤引擎"""
        self.logger = logger
        self.innovation_db = innovation_db or InnovationZoneDB()
        
        # 配置參數
        self.config = {
            'quality_score_threshold': 80.0,
            'risk_escalation_threshold': 70.0,
            'delay_alert_days': 7,
            'progress_trend_window_days': 14,
            'success_prediction_confidence_threshold': 0.75,
            'critical_path_analysis_enabled': True,
            'automated_status_updates': True
        }
        
        # 里程碑類型權重（用於項目整體評估）
        self.milestone_weights = {
            MilestoneType.TECHNICAL: 0.35,
            MilestoneType.USER_ADOPTION: 0.25,
            MilestoneType.MARKET_VALIDATION: 0.20,
            MilestoneType.REVENUE: 0.15,
            MilestoneType.PARTNERSHIP: 0.10,
            MilestoneType.REGULATORY: 0.15,
            MilestoneType.SCALABILITY: 0.20
        }
        
        # 追蹤指標
        self.tracking_metrics = {
            'milestones_updated': 0,
            'quality_assessments_performed': 0,
            'risk_assessments_conducted': 0,
            'progress_predictions_generated': 0
        }
        
        self.logger.info("✅ Technical Milestone Tracker initialized")
    
    # ==================== 里程碑進度追蹤 ====================
    
    async def update_milestone_progress(
        self,
        milestone_id: uuid.UUID,
        completion_rate: Decimal,
        technical_metrics: Dict[str, Any],
        quality_metrics: Dict[str, Any],
        updated_by: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新里程碑進度"""
        try:
            # 創建進度更新記錄
            progress_update = MilestoneProgressUpdate(
                milestone_id=milestone_id,
                completion_rate=completion_rate,
                technical_metrics=technical_metrics,
                quality_metrics=quality_metrics,
                notes=notes,
                updated_by=updated_by
            )
            
            # 計算質量分數
            quality_score = await self._calculate_quality_score(quality_metrics)
            
            # 更新里程碑數據
            updated_milestone = await self.innovation_db.update_milestone_progress(
                milestone_id,
                completion_rate,
                technical_metrics,
                notes,
                updated_by
            )
            
            # 分析進度趨勢
            progress_analytics = await self._analyze_milestone_progress_trend(
                milestone_id, completion_rate
            )
            
            # 評估成功概率
            success_probability = await self._predict_milestone_success(
                milestone_id, completion_rate, quality_score, technical_metrics
            )
            
            # 檢查依賴關係
            dependencies_status = await self._check_milestone_dependencies(milestone_id)
            
            # 生成建議
            recommendations = await self._generate_milestone_recommendations(
                updated_milestone, progress_analytics, success_probability
            )
            
            self.tracking_metrics['milestones_updated'] += 1
            
            self.logger.info(
                f"✅ Updated milestone progress: {milestone_id} -> {completion_rate}%"
            )
            
            return {
                'milestone': updated_milestone,
                'progress_analytics': progress_analytics,
                'quality_score': quality_score,
                'success_probability': success_probability,
                'dependencies_status': dependencies_status,
                'recommendations': recommendations,
                'update_summary': {
                    'previous_completion': progress_analytics.get('previous_completion_rate', 0),
                    'current_completion': float(completion_rate),
                    'progress_delta': float(completion_rate) - progress_analytics.get('previous_completion_rate', 0),
                    'trend': progress_analytics.get('trend', 'unknown')
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error updating milestone progress {milestone_id}: {e}")
            raise
    
    async def get_milestone_analytics(
        self,
        milestone_id: uuid.UUID
    ) -> MilestoneAnalytics:
        """獲取里程碑分析數據"""
        try:
            # 獲取里程碑詳情
            milestone = await self.innovation_db.get_innovation_project(
                milestone_id, include_milestones=True
            )
            
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            # 計算進度趨勢
            progress_trend = await self._determine_progress_trend(milestone_id)
            
            # 計算剩餘天數
            planned_date = milestone.get('planned_date')
            days_remaining = 0
            if planned_date:
                if isinstance(planned_date, str):
                    planned_date = date.fromisoformat(planned_date)
                days_remaining = (planned_date - date.today()).days
            
            # 估算完成日期
            estimated_completion = await self._estimate_completion_date(
                milestone_id, milestone.get('completion_rate', 0)
            )
            
            # 評估成功概率
            success_probability = await self._predict_milestone_success(
                milestone_id,
                milestone.get('completion_rate', 0),
                milestone.get('quality_score'),
                milestone.get('technical_metrics', {})
            )
            
            # 檢查依賴關係
            dependencies_status = await self._check_milestone_dependencies(milestone_id)
            
            # 統計阻塞問題
            blocking_issues = milestone.get('blocking_issues', [])
            blocking_issues_count = len(blocking_issues) if blocking_issues else 0
            
            # 生成建議
            recommendations = await self._generate_milestone_recommendations(
                milestone, {'trend': progress_trend}, success_probability
            )
            
            analytics = MilestoneAnalytics(
                milestone_id=milestone_id,
                project_id=milestone['innovation_project_id'],
                current_status=milestone.get('status', 'unknown'),
                progress_trend=progress_trend,
                completion_rate=milestone.get('completion_rate', 0),
                days_remaining=days_remaining,
                estimated_completion_date=estimated_completion,
                quality_score=milestone.get('quality_score'),
                risk_level=milestone.get('risk_level', 'medium'),
                success_probability=success_probability,
                dependencies_met=dependencies_status.get('all_met', False),
                blocking_issues_count=blocking_issues_count,
                recommendations=recommendations
            )
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"❌ Error getting milestone analytics {milestone_id}: {e}")
            raise
    
    async def get_project_milestone_overview(
        self,
        project_id: uuid.UUID
    ) -> ProjectMilestoneOverview:
        """獲取項目里程碑概覽"""
        try:
            # 獲取項目所有里程碑
            project = await self.innovation_db.get_innovation_project(
                project_id, include_milestones=True
            )
            
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            milestones = project.get('milestones', [])
            
            # 統計里程碑狀態
            total_milestones = len(milestones)
            completed_milestones = len([m for m in milestones if m.get('is_completed', False)])
            in_progress_milestones = len([m for m in milestones if m.get('status') == 'in_progress'])
            delayed_milestones = len([m for m in milestones if self._is_milestone_delayed(m)])
            
            # 計算總體完成率
            if total_milestones > 0:
                overall_completion_rate = Decimal(str(completed_milestones / total_milestones * 100))
            else:
                overall_completion_rate = Decimal('0')
            
            # 確定總體進度趨勢
            overall_trend = await self._determine_project_progress_trend(milestones)
            
            # 識別關鍵路徑里程碑
            critical_path = await self._identify_critical_path_milestones(milestones)
            
            # 找到下一個到期的里程碑
            next_milestone_due = self._find_next_milestone_due(milestones)
            
            # 估算項目完成時間
            estimated_project_completion = await self._estimate_project_completion_date(milestones)
            
            # 計算項目健康分數
            project_health_score = await self._calculate_project_health_score(milestones)
            
            overview = ProjectMilestoneOverview(
                project_id=project_id,
                total_milestones=total_milestones,
                completed_milestones=completed_milestones,
                in_progress_milestones=in_progress_milestones,
                delayed_milestones=delayed_milestones,
                overall_completion_rate=overall_completion_rate,
                overall_progress_trend=overall_trend,
                critical_path_milestones=critical_path,
                next_milestone_due=next_milestone_due,
                estimated_project_completion=estimated_project_completion,
                project_health_score=project_health_score
            )
            
            return overview
            
        except Exception as e:
            self.logger.error(f"❌ Error getting project milestone overview {project_id}: {e}")
            raise
    
    # ==================== 里程碑質量評估 ====================
    
    async def assess_milestone_quality(
        self,
        milestone_id: uuid.UUID,
        quality_criteria: Dict[str, Any]
    ) -> Dict[str, Any]:
        """評估里程碑質量"""
        try:
            # 獲取里程碑信息
            milestone = await self.innovation_db.get_innovation_project(
                milestone_id, include_milestones=True
            )
            
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            # 執行質量評估
            quality_assessment = {
                'milestone_id': milestone_id,
                'assessment_date': datetime.now(timezone.utc),
                'quality_dimensions': {},
                'overall_quality_score': 0.0,
                'quality_grade': 'pending',
                'improvement_areas': [],
                'strengths': [],
                'recommendations': []
            }
            
            # 評估各個質量維度
            quality_dimensions = [
                'functionality',
                'reliability',
                'usability',
                'performance',
                'maintainability',
                'documentation'
            ]
            
            total_score = 0.0
            assessed_dimensions = 0
            
            for dimension in quality_dimensions:
                if dimension in quality_criteria:
                    dimension_score = await self._assess_quality_dimension(
                        dimension, quality_criteria[dimension], milestone
                    )
                    quality_assessment['quality_dimensions'][dimension] = dimension_score
                    total_score += dimension_score['score']
                    assessed_dimensions += 1
                    
                    if dimension_score['score'] < 70:
                        quality_assessment['improvement_areas'].append({
                            'dimension': dimension,
                            'score': dimension_score['score'],
                            'issues': dimension_score.get('issues', [])
                        })
                    elif dimension_score['score'] >= 90:
                        quality_assessment['strengths'].append({
                            'dimension': dimension,
                            'score': dimension_score['score'],
                            'highlights': dimension_score.get('highlights', [])
                        })
            
            # 計算總體質量分數
            if assessed_dimensions > 0:
                quality_assessment['overall_quality_score'] = total_score / assessed_dimensions
            
            # 確定質量等級
            score = quality_assessment['overall_quality_score']
            if score >= 90:
                quality_assessment['quality_grade'] = 'excellent'
            elif score >= 80:
                quality_assessment['quality_grade'] = 'good'
            elif score >= 70:
                quality_assessment['quality_grade'] = 'acceptable'
            elif score >= 60:
                quality_assessment['quality_grade'] = 'needs_improvement'
            else:
                quality_assessment['quality_grade'] = 'poor'
            
            # 生成改進建議
            quality_assessment['recommendations'] = await self._generate_quality_recommendations(
                quality_assessment
            )
            
            self.tracking_metrics['quality_assessments_performed'] += 1
            
            self.logger.info(
                f"✅ Assessed milestone quality: {milestone_id} -> "
                f"{quality_assessment['overall_quality_score']:.1f} ({quality_assessment['quality_grade']})"
            )
            
            return quality_assessment
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing milestone quality {milestone_id}: {e}")
            raise
    
    # ==================== 風險評估和預測 ====================
    
    async def assess_milestone_risks(
        self,
        milestone_id: uuid.UUID
    ) -> Dict[str, Any]:
        """評估里程碑風險"""
        try:
            # 獲取里程碑信息
            milestone = await self.innovation_db.get_innovation_project(
                milestone_id, include_milestones=True
            )
            
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            risk_assessment = {
                'milestone_id': milestone_id,
                'assessment_date': datetime.now(timezone.utc),
                'overall_risk_level': 'medium',
                'overall_risk_score': 0.0,
                'risk_categories': {},
                'high_risk_factors': [],
                'mitigation_recommendations': [],
                'risk_trend': 'stable'
            }
            
            # 評估各類風險
            risk_categories = {
                'schedule_risk': await self._assess_schedule_risk(milestone),
                'technical_risk': await self._assess_technical_risk(milestone),
                'resource_risk': await self._assess_resource_risk(milestone),
                'dependency_risk': await self._assess_dependency_risk(milestone),
                'quality_risk': await self._assess_quality_risk(milestone)
            }
            
            risk_assessment['risk_categories'] = risk_categories
            
            # 計算總體風險分數
            total_risk_score = sum(category['score'] for category in risk_categories.values())
            risk_assessment['overall_risk_score'] = total_risk_score / len(risk_categories)
            
            # 確定風險等級
            if risk_assessment['overall_risk_score'] >= 80:
                risk_assessment['overall_risk_level'] = 'critical'
            elif risk_assessment['overall_risk_score'] >= 60:
                risk_assessment['overall_risk_level'] = 'high'
            elif risk_assessment['overall_risk_level'] >= 40:
                risk_assessment['overall_risk_level'] = 'medium'
            else:
                risk_assessment['overall_risk_level'] = 'low'
            
            # 識別高風險因素
            for category, data in risk_categories.items():
                if data['score'] >= 70:
                    risk_assessment['high_risk_factors'].append({
                        'category': category,
                        'score': data['score'],
                        'factors': data.get('factors', [])
                    })
            
            # 生成緩解建議
            risk_assessment['mitigation_recommendations'] = await self._generate_risk_mitigation_recommendations(
                risk_assessment
            )
            
            self.tracking_metrics['risk_assessments_conducted'] += 1
            
            self.logger.info(
                f"✅ Assessed milestone risks: {milestone_id} -> "
                f"{risk_assessment['overall_risk_level']} ({risk_assessment['overall_risk_score']:.1f})"
            )
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"❌ Error assessing milestone risks {milestone_id}: {e}")
            raise
    
    # ==================== 進度預測 ====================
    
    async def predict_milestone_completion(
        self,
        milestone_id: uuid.UUID,
        prediction_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """預測里程碑完成情況"""
        try:
            # 獲取里程碑歷史進度數據
            milestone = await self.innovation_db.get_innovation_project(
                milestone_id, include_milestones=True
            )
            
            if not milestone:
                raise ValueError(f"Milestone {milestone_id} not found")
            
            prediction = {
                'milestone_id': milestone_id,
                'prediction_date': datetime.now(timezone.utc),
                'prediction_horizon_days': prediction_horizon_days,
                'current_completion_rate': milestone.get('completion_rate', 0),
                'predicted_completion_date': None,
                'completion_probability': 0.0,
                'confidence_level': 'low',
                'prediction_scenarios': {},
                'risk_factors': [],
                'acceleration_opportunities': []
            }
            
            # 計算進度速度
            progress_velocity = await self._calculate_progress_velocity(milestone_id)
            
            # 預測完成日期
            if progress_velocity > 0:
                remaining_progress = 100 - float(milestone.get('completion_rate', 0))
                days_to_completion = remaining_progress / progress_velocity
                
                prediction['predicted_completion_date'] = (
                    date.today() + timedelta(days=int(days_to_completion))
                )
            
            # 計算完成概率
            prediction['completion_probability'] = await self._calculate_completion_probability(
                milestone, progress_velocity, prediction_horizon_days
            )
            
            # 確定信心等級
            if prediction['completion_probability'] >= 0.8:
                prediction['confidence_level'] = 'high'
            elif prediction['completion_probability'] >= 0.6:
                prediction['confidence_level'] = 'medium'
            else:
                prediction['confidence_level'] = 'low'
            
            # 生成不同場景預測
            prediction['prediction_scenarios'] = await self._generate_prediction_scenarios(
                milestone, progress_velocity, prediction_horizon_days
            )
            
            # 識別風險因素
            prediction['risk_factors'] = await self._identify_completion_risk_factors(milestone)
            
            # 識別加速機會
            prediction['acceleration_opportunities'] = await self._identify_acceleration_opportunities(milestone)
            
            self.tracking_metrics['progress_predictions_generated'] += 1
            
            self.logger.info(
                f"✅ Generated milestone completion prediction: {milestone_id} -> "
                f"{prediction['completion_probability']:.2f} probability"
            )
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"❌ Error predicting milestone completion {milestone_id}: {e}")
            raise
    
    # ==================== 輔助方法 ====================
    
    async def _calculate_quality_score(self, quality_metrics: Dict[str, Any]) -> Optional[Decimal]:
        """計算質量分數"""
        if not quality_metrics:
            return None
        
        # 標準化質量指標
        score_factors = []
        
        # 功能完整性
        if 'functionality_score' in quality_metrics:
            score_factors.append(quality_metrics['functionality_score'])
        
        # 可靠性
        if 'reliability_score' in quality_metrics:
            score_factors.append(quality_metrics['reliability_score'])
        
        # 性能
        if 'performance_score' in quality_metrics:
            score_factors.append(quality_metrics['performance_score'])
        
        # 用戶體驗
        if 'user_experience_score' in quality_metrics:
            score_factors.append(quality_metrics['user_experience_score'])
        
        # 代碼質量
        if 'code_quality_score' in quality_metrics:
            score_factors.append(quality_metrics['code_quality_score'])
        
        if score_factors:
            return Decimal(str(statistics.mean(score_factors)))
        
        return Decimal('75')  # 預設分數
    
    async def _analyze_milestone_progress_trend(
        self,
        milestone_id: uuid.UUID,
        current_completion_rate: Decimal
    ) -> Dict[str, Any]:
        """分析里程碑進度趨勢"""
        # 這裡應該從歷史數據計算趨勢
        # 暫時返回模擬數據
        
        return {
            'trend': 'on_track',
            'previous_completion_rate': float(current_completion_rate) - 5.0,
            'progress_velocity': 5.0,  # 每天進度百分比
            'trend_confidence': 0.8
        }
    
    async def _predict_milestone_success(
        self,
        milestone_id: uuid.UUID,
        completion_rate: Decimal,
        quality_score: Optional[Decimal],
        technical_metrics: Dict[str, Any]
    ) -> float:
        """預測里程碑成功概率"""
        success_factors = []
        
        # 完成率因素
        success_factors.append(min(1.0, float(completion_rate) / 100))
        
        # 質量因素
        if quality_score:
            success_factors.append(min(1.0, float(quality_score) / 100))
        
        # 技術指標因素
        if technical_metrics:
            # 根據技術指標評估成功概率
            tech_score = 0.7  # 預設技術成功率
            success_factors.append(tech_score)
        
        return statistics.mean(success_factors) if success_factors else 0.5
    
    async def _check_milestone_dependencies(self, milestone_id: uuid.UUID) -> Dict[str, Any]:
        """檢查里程碑依賴關係"""
        # 這裡應該查詢依賴關係數據
        # 暫時返回模擬數據
        
        return {
            'total_dependencies': 2,
            'met_dependencies': 1,
            'pending_dependencies': 1,
            'all_met': False,
            'blocking_dependencies': ['dependency_1']
        }
    
    async def _generate_milestone_recommendations(
        self,
        milestone: Dict[str, Any],
        progress_analytics: Dict[str, Any],
        success_probability: float
    ) -> List[str]:
        """生成里程碑建議"""
        recommendations = []
        
        # 基於完成率的建議
        completion_rate = milestone.get('completion_rate', 0)
        if completion_rate < 50:
            recommendations.append("Consider increasing resource allocation to accelerate progress")
        elif completion_rate > 90:
            recommendations.append("Focus on quality assurance and final deliverables preparation")
        
        # 基於成功概率的建議
        if success_probability < 0.6:
            recommendations.append("High risk of milestone failure - implement risk mitigation strategies")
        
        # 基於進度趨勢的建議
        trend = progress_analytics.get('trend', 'unknown')
        if trend == 'significantly_behind':
            recommendations.append("Significantly behind schedule - consider scope adjustment or timeline extension")
        elif trend == 'ahead':
            recommendations.append("Ahead of schedule - consider advancing next milestone start date")
        
        return recommendations
    
    def _is_milestone_delayed(self, milestone: Dict[str, Any]) -> bool:
        """檢查里程碑是否延遲"""
        planned_date = milestone.get('planned_date')
        is_completed = milestone.get('is_completed', False)
        
        if planned_date and not is_completed:
            if isinstance(planned_date, str):
                planned_date = date.fromisoformat(planned_date)
            return planned_date < date.today()
        
        return False
    
    async def _determine_progress_trend(self, milestone_id: uuid.UUID) -> ProgressTrend:
        """確定進度趨勢"""
        # 這裡應該基於歷史數據分析趨勢
        # 暫時返回預設值
        return ProgressTrend.ON_TRACK
    
    async def _estimate_completion_date(
        self,
        milestone_id: uuid.UUID,
        current_completion_rate: Decimal
    ) -> Optional[date]:
        """估算完成日期"""
        if current_completion_rate >= 100:
            return date.today()
        
        # 基於進度速度估算
        progress_velocity = await self._calculate_progress_velocity(milestone_id)
        
        if progress_velocity > 0:
            remaining_progress = 100 - float(current_completion_rate)
            days_to_completion = remaining_progress / progress_velocity
            return date.today() + timedelta(days=int(days_to_completion))
        
        return None
    
    async def _calculate_progress_velocity(self, milestone_id: uuid.UUID) -> float:
        """計算進度速度"""
        # 這裡應該基於歷史進度數據計算速度
        # 暫時返回預設值（每天5%的進度）
        return 5.0
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            db_health = await self.innovation_db.health_check()
            
            return {
                'component': 'technical_milestone_tracker',
                'status': 'healthy' if db_health['status'] == 'healthy' else 'degraded',
                'timestamp': datetime.now(timezone.utc),
                'tracking_metrics': self.tracking_metrics,
                'configuration': {
                    'quality_threshold': self.config['quality_score_threshold'],
                    'risk_threshold': self.config['risk_escalation_threshold'],
                    'automated_updates': self.config['automated_status_updates']
                },
                'database_status': db_health['status']
            }
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                'component': 'technical_milestone_tracker',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }