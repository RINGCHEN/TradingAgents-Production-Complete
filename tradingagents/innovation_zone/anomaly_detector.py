#!/usr/bin/env python3
"""
Innovation Anomaly Detector
創新項目異常檢測器

專門檢測創新項目中的各種異常情況：
- 預算超支和異常支出模式
- 里程碑延遲和進度異常
- 用戶參與度下降異常
- 團隊效能異常
- 技術指標異常
- 市場反饋異常
"""

import asyncio
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import uuid
import statistics
import numpy as np
from dataclasses import dataclass, field
from enum import Enum

from .models import AnomalyType

logger = logging.getLogger(__name__)

class AnomalySeverity(str, Enum):
    """異常嚴重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class DetectionMethod(str, Enum):
    """檢測方法"""
    STATISTICAL = "statistical"
    THRESHOLD_BASED = "threshold_based"
    TREND_ANALYSIS = "trend_analysis"
    PATTERN_MATCHING = "pattern_matching"
    MACHINE_LEARNING = "machine_learning"

@dataclass
class AnomalyDetectionResult:
    """異常檢測結果"""
    anomaly_id: uuid.UUID
    project_id: uuid.UUID
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    confidence_score: float
    detected_at: datetime
    detection_method: DetectionMethod
    
    # 異常描述
    title: str
    description: str
    affected_areas: List[str] = field(default_factory=list)
    
    # 數值信息
    baseline_value: Optional[float] = None
    actual_value: float = 0.0
    deviation_percentage: float = 0.0
    threshold_value: float = 0.0
    
    # 影響評估
    impact_level: str = "moderate"
    potential_consequences: List[str] = field(default_factory=list)
    
    # 上下文信息
    related_metrics: Dict[str, Any] = field(default_factory=dict)
    historical_context: Dict[str, Any] = field(default_factory=dict)
    external_factors: List[str] = field(default_factory=list)
    
    # 建議行動
    immediate_actions: List[str] = field(default_factory=list)
    investigation_steps: List[str] = field(default_factory=list)
    prevention_measures: List[str] = field(default_factory=list)

@dataclass
class AnomalyDetectionConfig:
    """異常檢測配置"""
    # 預算異常閾值
    budget_overrun_threshold: float = 0.15  # 15% 超支
    budget_burn_rate_threshold: float = 2.0  # 2倍正常燒錢率
    budget_category_variance_threshold: float = 0.25
    
    # 里程碑異常閾值
    milestone_delay_threshold_days: int = 14
    milestone_quality_threshold: float = 70.0
    milestone_completion_rate_threshold: float = 0.8
    
    # 用戶參與異常閾值
    engagement_decline_threshold: float = 0.20  # 20% 下降
    user_churn_threshold: float = 0.15
    satisfaction_drop_threshold: float = 0.30
    
    # 團隊效能異常閾值
    productivity_decline_threshold: float = 0.25
    team_turnover_threshold: float = 0.30
    
    # 統計異常閾值
    statistical_significance_level: float = 0.05
    outlier_detection_std_threshold: float = 2.5
    
    # 檢測頻率
    detection_interval_hours: int = 24
    real_time_detection_enabled: bool = True

class InnovationAnomalyDetector:
    """
    創新項目異常檢測器
    
    功能：
    1. 多維度異常檢測（預算、里程碑、用戶參與等）
    2. 智能閾值設定和自適應調整
    3. 統計方法和機器學習檢測
    4. 異常嚴重程度評估
    5. 根因分析和影響評估
    6. 自動預警和行動建議
    """
    
    def __init__(self, config: Optional[AnomalyDetectionConfig] = None):
        """初始化異常檢測器"""
        self.logger = logger
        self.config = config or AnomalyDetectionConfig()
        
        # 檢測統計
        self.detection_stats = {
            'total_detections': 0,
            'budget_anomalies': 0,
            'milestone_anomalies': 0,
            'engagement_anomalies': 0,
            'team_anomalies': 0,
            'false_positives': 0,
            'confirmed_anomalies': 0
        }
        
        # 異常檢測歷史
        self.detection_history: List[AnomalyDetectionResult] = []
        self.max_history_size = 10000
        
        # 基線數據緩存
        self.baseline_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger.info("✅ Innovation Anomaly Detector initialized")
    
    # ==================== 主要檢測方法 ====================
    
    async def detect_budget_anomalies(
        self,
        project: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """檢測預算異常"""
        anomalies = []
        project_id = uuid.UUID(project['id'])
        budget_tracking = project.get('budget_tracking', [])
        
        if not budget_tracking:
            return anomalies
        
        try:
            # 1. 預算超支檢測
            overrun_anomaly = await self._detect_budget_overrun(project_id, budget_tracking)
            if overrun_anomaly:
                anomalies.append(overrun_anomaly)
            
            # 2. 異常燒錢率檢測
            burn_rate_anomaly = await self._detect_abnormal_burn_rate(project_id, budget_tracking)
            if burn_rate_anomaly:
                anomalies.append(burn_rate_anomaly)
            
            # 3. 類別支出異常檢測
            category_anomalies = await self._detect_category_spending_anomalies(project_id, budget_tracking)
            anomalies.extend(category_anomalies)
            
            # 4. 支出模式異常檢測
            pattern_anomalies = await self._detect_spending_pattern_anomalies(project_id, budget_tracking)
            anomalies.extend(pattern_anomalies)
            
            self.detection_stats['budget_anomalies'] += len(anomalies)
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting budget anomalies: {e}")
        
        return anomalies
    
    async def detect_milestone_anomalies(
        self,
        project: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """檢測里程碑異常"""
        anomalies = []
        project_id = uuid.UUID(project['id'])
        milestones = project.get('milestones', [])
        
        if not milestones:
            return anomalies
        
        try:
            # 1. 里程碑延遲檢測
            delay_anomalies = await self._detect_milestone_delays(project_id, milestones)
            anomalies.extend(delay_anomalies)
            
            # 2. 質量異常檢測
            quality_anomalies = await self._detect_milestone_quality_issues(project_id, milestones)
            anomalies.extend(quality_anomalies)
            
            # 3. 進度異常檢測
            progress_anomalies = await self._detect_milestone_progress_anomalies(project_id, milestones)
            anomalies.extend(progress_anomalies)
            
            # 4. 依賴關係異常檢測
            dependency_anomalies = await self._detect_milestone_dependency_issues(project_id, milestones)
            anomalies.extend(dependency_anomalies)
            
            self.detection_stats['milestone_anomalies'] += len(anomalies)
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting milestone anomalies: {e}")
        
        return anomalies
    
    async def detect_user_engagement_anomalies(
        self,
        project: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """檢測用戶參與異常"""
        anomalies = []
        project_id = uuid.UUID(project['id'])
        user_metrics = project.get('user_behavior_metrics', [])
        
        if not user_metrics:
            return anomalies
        
        try:
            # 1. 參與度下降檢測
            engagement_anomalies = await self._detect_engagement_decline(project_id, user_metrics)
            anomalies.extend(engagement_anomalies)
            
            # 2. 用戶流失異常檢測
            churn_anomalies = await self._detect_abnormal_churn(project_id, user_metrics)
            anomalies.extend(churn_anomalies)
            
            # 3. 滿意度下降檢測
            satisfaction_anomalies = await self._detect_satisfaction_drop(project_id, user_metrics)
            anomalies.extend(satisfaction_anomalies)
            
            # 4. 使用模式異常檢測
            usage_anomalies = await self._detect_usage_pattern_anomalies(project_id, user_metrics)
            anomalies.extend(usage_anomalies)
            
            self.detection_stats['engagement_anomalies'] += len(anomalies)
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting user engagement anomalies: {e}")
        
        return anomalies
    
    # ==================== 具體檢測實現 ====================
    
    async def _detect_budget_overrun(
        self,
        project_id: uuid.UUID,
        budget_tracking: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """檢測預算超支"""
        try:
            # 計算總預算和支出
            total_allocated = sum(
                float(bt['amount']) for bt in budget_tracking
                if bt['transaction_type'] == 'allocation'
            )
            total_spent = sum(
                float(bt['amount']) for bt in budget_tracking
                if bt['transaction_type'] == 'expense'
            )
            
            if total_allocated == 0:
                return None
            
            overrun_rate = (total_spent - total_allocated) / total_allocated
            
            if overrun_rate > self.config.budget_overrun_threshold:
                severity = self._determine_overrun_severity(overrun_rate)
                
                anomaly_data = {
                    'innovation_project_id': project_id,
                    'anomaly_type': AnomalyType.BUDGET_OVERRUN.value,
                    'anomaly_severity': severity.value,
                    'anomaly_title': f"Budget Overrun Detected ({overrun_rate:.1%})",
                    'anomaly_description': f"Project has exceeded allocated budget by {overrun_rate:.1%}",
                    'detection_method': DetectionMethod.THRESHOLD_BASED.value,
                    'confidence_score': min(95, 70 + overrun_rate * 100),
                    'baseline_value': total_allocated,
                    'actual_value': total_spent,
                    'deviation_percentage': overrun_rate * 100,
                    'anomaly_threshold': self.config.budget_overrun_threshold * total_allocated,
                    'impact_level': 'significant' if overrun_rate > 0.3 else 'moderate',
                    'affected_areas': ['budget_management', 'financial_planning'],
                    'potential_consequences': [
                        'Funding shortfall risk',
                        'Project timeline impact',
                        'Resource reallocation needed'
                    ] if overrun_rate > 0.3 else [
                        'Budget monitoring required',
                        'Spending review needed'
                    ]
                }
                
                return anomaly_data
                
        except Exception as e:
            self.logger.error(f"❌ Error detecting budget overrun: {e}")
        
        return None
    
    async def _detect_abnormal_burn_rate(
        self,
        project_id: uuid.UUID,
        budget_tracking: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """檢測異常燒錢率"""
        try:
            # 計算最近30天的燒錢率
            thirty_days_ago = date.today() - timedelta(days=30)
            recent_expenses = [
                bt for bt in budget_tracking
                if (bt['transaction_type'] == 'expense' and
                    date.fromisoformat(bt['transaction_date']) >= thirty_days_ago)
            ]
            
            if len(recent_expenses) < 3:  # 樣本太少
                return None
            
            current_burn_rate = sum(float(bt['amount']) for bt in recent_expenses) / 30
            
            # 計算歷史平均燒錢率
            historical_expenses = [
                bt for bt in budget_tracking
                if (bt['transaction_type'] == 'expense' and
                    date.fromisoformat(bt['transaction_date']) < thirty_days_ago)
            ]
            
            if not historical_expenses:
                return None
            
            historical_burn_rate = sum(float(bt['amount']) for bt in historical_expenses) / len(historical_expenses) * 30
            
            if historical_burn_rate == 0:
                return None
            
            burn_rate_ratio = current_burn_rate / historical_burn_rate
            
            if burn_rate_ratio > self.config.budget_burn_rate_threshold:
                severity = AnomalySeverity.HIGH if burn_rate_ratio > 3.0 else AnomalySeverity.MEDIUM
                
                anomaly_data = {
                    'innovation_project_id': project_id,
                    'anomaly_type': AnomalyType.BUDGET_OVERRUN.value,
                    'anomaly_severity': severity.value,
                    'anomaly_title': f"Abnormal Burn Rate Detected ({burn_rate_ratio:.1f}x)",
                    'anomaly_description': f"Current burn rate is {burn_rate_ratio:.1f}x higher than historical average",
                    'detection_method': DetectionMethod.TREND_ANALYSIS.value,
                    'confidence_score': min(90, 60 + burn_rate_ratio * 10),
                    'baseline_value': historical_burn_rate,
                    'actual_value': current_burn_rate,
                    'deviation_percentage': (burn_rate_ratio - 1) * 100,
                    'anomaly_threshold': historical_burn_rate * self.config.budget_burn_rate_threshold,
                    'impact_level': 'significant' if burn_rate_ratio > 3.0 else 'moderate',
                    'affected_areas': ['budget_management', 'resource_allocation'],
                    'potential_consequences': [
                        'Budget depletion risk',
                        'Project sustainability concerns',
                        'Resource optimization needed'
                    ]
                }
                
                return anomaly_data
                
        except Exception as e:
            self.logger.error(f"❌ Error detecting abnormal burn rate: {e}")
        
        return None
    
    async def _detect_category_spending_anomalies(
        self,
        project_id: uuid.UUID,
        budget_tracking: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測類別支出異常"""
        anomalies = []
        
        try:
            # 按類別統計支出
            category_spending = {}
            total_spending = 0
            
            for bt in budget_tracking:
                if bt['transaction_type'] == 'expense':
                    category = bt.get('expense_category', 'other')
                    amount = float(bt['amount'])
                    category_spending[category] = category_spending.get(category, 0) + amount
                    total_spending += amount
            
            if total_spending == 0:
                return anomalies
            
            # 檢查每個類別的支出比例
            expected_ratios = {
                'development': 0.40,
                'research': 0.25,
                'testing': 0.15,
                'infrastructure': 0.10,
                'other': 0.10
            }
            
            for category, spending in category_spending.items():
                spending_ratio = spending / total_spending
                expected_ratio = expected_ratios.get(category, 0.10)
                
                if abs(spending_ratio - expected_ratio) > self.config.budget_category_variance_threshold:
                    severity = AnomalySeverity.MEDIUM if spending_ratio > expected_ratio else AnomalySeverity.LOW
                    
                    anomaly_data = {
                        'innovation_project_id': project_id,
                        'anomaly_type': AnomalyType.BUDGET_OVERRUN.value,
                        'anomaly_severity': severity.value,
                        'anomaly_title': f"Unusual {category} spending pattern",
                        'anomaly_description': f"{category} spending is {spending_ratio:.1%} of total (expected ~{expected_ratio:.1%})",
                        'detection_method': DetectionMethod.STATISTICAL.value,
                        'confidence_score': 75,
                        'baseline_value': expected_ratio * total_spending,
                        'actual_value': spending,
                        'deviation_percentage': abs(spending_ratio - expected_ratio) * 100,
                        'anomaly_threshold': expected_ratio * total_spending * (1 + self.config.budget_category_variance_threshold),
                        'impact_level': 'moderate',
                        'affected_areas': [f'{category}_spending', 'budget_allocation'],
                        'potential_consequences': [
                            f'Imbalanced {category} resource allocation',
                            'Budget optimization opportunity'
                        ]
                    }
                    
                    anomalies.append(anomaly_data)
                    
        except Exception as e:
            self.logger.error(f"❌ Error detecting category spending anomalies: {e}")
        
        return anomalies
    
    async def _detect_milestone_delays(
        self,
        project_id: uuid.UUID,
        milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測里程碑延遲"""
        anomalies = []
        
        try:
            current_date = date.today()
            
            for milestone in milestones:
                planned_date = milestone.get('planned_date')
                is_completed = milestone.get('is_completed', False)
                completion_rate = milestone.get('completion_rate', 0)
                
                if planned_date and not is_completed:
                    if isinstance(planned_date, str):
                        planned_date = date.fromisoformat(planned_date)
                    
                    days_overdue = (current_date - planned_date).days
                    
                    if days_overdue > self.config.milestone_delay_threshold_days:
                        severity = self._determine_delay_severity(days_overdue, completion_rate)
                        
                        anomaly_data = {
                            'innovation_project_id': project_id,
                            'anomaly_type': AnomalyType.MILESTONE_DELAY.value,
                            'anomaly_severity': severity.value,
                            'anomaly_title': f"Milestone Delay: {milestone.get('milestone_name', 'Unknown')}",
                            'anomaly_description': f"Milestone is {days_overdue} days overdue with {completion_rate}% completion",
                            'detection_method': DetectionMethod.THRESHOLD_BASED.value,
                            'confidence_score': 95,
                            'baseline_value': 0,
                            'actual_value': days_overdue,
                            'deviation_percentage': (days_overdue / self.config.milestone_delay_threshold_days - 1) * 100,
                            'anomaly_threshold': self.config.milestone_delay_threshold_days,
                            'impact_level': 'significant' if days_overdue > 30 else 'moderate',
                            'affected_areas': ['project_timeline', 'milestone_management'],
                            'potential_consequences': [
                                'Project schedule impact',
                                'Resource reallocation needed',
                                'Stakeholder communication required'
                            ] if days_overdue > 30 else [
                                'Timeline adjustment needed',
                                'Progress review required'
                            ],
                            'related_metrics': {
                                'milestone_id': milestone.get('id'),
                                'milestone_name': milestone.get('milestone_name'),
                                'planned_date': planned_date.isoformat(),
                                'completion_rate': completion_rate
                            }
                        }
                        
                        anomalies.append(anomaly_data)
                        
        except Exception as e:
            self.logger.error(f"❌ Error detecting milestone delays: {e}")
        
        return anomalies
    
    async def _detect_engagement_decline(
        self,
        project_id: uuid.UUID,
        user_metrics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測用戶參與度下降"""
        anomalies = []
        
        try:
            if len(user_metrics) < 2:
                return anomalies
            
            # 按日期排序獲取最新數據
            sorted_metrics = sorted(user_metrics, key=lambda x: x['measurement_date'], reverse=True)
            current_metrics = sorted_metrics[0]
            previous_metrics = sorted_metrics[1]
            
            current_engagement = float(current_metrics.get('engagement_score', 0))
            previous_engagement = float(previous_metrics.get('engagement_score', 0))
            
            if previous_engagement == 0:
                return anomalies
            
            decline_rate = (previous_engagement - current_engagement) / previous_engagement
            
            if decline_rate > self.config.engagement_decline_threshold:
                severity = AnomalySeverity.HIGH if decline_rate > 0.4 else AnomalySeverity.MEDIUM
                
                anomaly_data = {
                    'innovation_project_id': project_id,
                    'anomaly_type': AnomalyType.LOW_USER_ENGAGEMENT.value,
                    'anomaly_severity': severity.value,
                    'anomaly_title': f"User Engagement Decline ({decline_rate:.1%})",
                    'anomaly_description': f"User engagement dropped by {decline_rate:.1%} from previous measurement",
                    'detection_method': DetectionMethod.TREND_ANALYSIS.value,
                    'confidence_score': min(90, 70 + decline_rate * 100),
                    'baseline_value': previous_engagement,
                    'actual_value': current_engagement,
                    'deviation_percentage': decline_rate * 100,
                    'anomaly_threshold': previous_engagement * (1 - self.config.engagement_decline_threshold),
                    'impact_level': 'significant' if decline_rate > 0.4 else 'moderate',
                    'affected_areas': ['user_experience', 'product_adoption'],
                    'potential_consequences': [
                        'User retention risk',
                        'Product-market fit concerns',
                        'Feature optimization needed'
                    ],
                    'related_metrics': {
                        'current_date': current_metrics['measurement_date'],
                        'previous_date': previous_metrics['measurement_date'],
                        'current_active_users': current_metrics.get('active_users', 0),
                        'previous_active_users': previous_metrics.get('active_users', 0)
                    }
                }
                
                anomalies.append(anomaly_data)
                
        except Exception as e:
            self.logger.error(f"❌ Error detecting engagement decline: {e}")
        
        return anomalies
    
    # ==================== 輔助方法 ====================
    
    def _determine_overrun_severity(self, overrun_rate: float) -> AnomalySeverity:
        """確定超支嚴重程度"""
        if overrun_rate > 0.5:  # 超支50%以上
            return AnomalySeverity.CRITICAL
        elif overrun_rate > 0.3:  # 超支30%以上
            return AnomalySeverity.HIGH
        elif overrun_rate > 0.15:  # 超支15%以上
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    def _determine_delay_severity(self, days_overdue: int, completion_rate: float) -> AnomalySeverity:
        """確定延遲嚴重程度"""
        if days_overdue > 60 or completion_rate < 30:
            return AnomalySeverity.CRITICAL
        elif days_overdue > 30 or completion_rate < 50:
            return AnomalySeverity.HIGH
        elif days_overdue > 14 or completion_rate < 70:
            return AnomalySeverity.MEDIUM
        else:
            return AnomalySeverity.LOW
    
    async def _detect_spending_pattern_anomalies(
        self,
        project_id: uuid.UUID,
        budget_tracking: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測支出模式異常（占位符實現）"""
        # 這裡可以實現更複雜的模式檢測邏輯
        return []
    
    async def _detect_milestone_quality_issues(
        self,
        project_id: uuid.UUID,
        milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測里程碑質量問題（占位符實現）"""
        anomalies = []
        
        for milestone in milestones:
            quality_score = milestone.get('quality_score')
            if quality_score and float(quality_score) < self.config.milestone_quality_threshold:
                # 創建質量異常
                pass
        
        return anomalies
    
    async def _detect_milestone_progress_anomalies(
        self,
        project_id: uuid.UUID,
        milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測里程碑進度異常（占位符實現）"""
        return []
    
    async def _detect_milestone_dependency_issues(
        self,
        project_id: uuid.UUID,
        milestones: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測里程碑依賴關係問題（占位符實現）"""
        return []
    
    async def _detect_abnormal_churn(
        self,
        project_id: uuid.UUID,
        user_metrics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測異常用戶流失（占位符實現）"""
        return []
    
    async def _detect_satisfaction_drop(
        self,
        project_id: uuid.UUID,
        user_metrics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測滿意度下降（占位符實現）"""
        return []
    
    async def _detect_usage_pattern_anomalies(
        self,
        project_id: uuid.UUID,
        user_metrics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """檢測使用模式異常（占位符實現）"""
        return []
    
    # ==================== 管理和配置方法 ====================
    
    async def update_detection_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新檢測配置"""
        try:
            for key, value in new_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
            
            self.logger.info("✅ Updated anomaly detection configuration")
            
            return {
                'success': True,
                'updated_config': {
                    'budget_overrun_threshold': self.config.budget_overrun_threshold,
                    'milestone_delay_threshold_days': self.config.milestone_delay_threshold_days,
                    'engagement_decline_threshold': self.config.engagement_decline_threshold
                },
                'message': 'Configuration updated successfully'
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error updating detection config: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to update configuration'
            }
    
    async def get_detection_statistics(self) -> Dict[str, Any]:
        """獲取檢測統計信息"""
        return {
            'detection_stats': self.detection_stats.copy(),
            'config_summary': {
                'budget_overrun_threshold': self.config.budget_overrun_threshold,
                'milestone_delay_threshold_days': self.config.milestone_delay_threshold_days,
                'engagement_decline_threshold': self.config.engagement_decline_threshold,
                'detection_interval_hours': self.config.detection_interval_hours
            },
            'history_size': len(self.detection_history),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            return {
                'component': 'innovation_anomaly_detector',
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc),
                'detection_stats': self.detection_stats,
                'configuration': {
                    'detection_interval_hours': self.config.detection_interval_hours,
                    'real_time_detection_enabled': self.config.real_time_detection_enabled
                },
                'cache_status': {
                    'baseline_cache_size': len(self.baseline_cache),
                    'history_size': len(self.detection_history)
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                'component': 'innovation_anomaly_detector',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }