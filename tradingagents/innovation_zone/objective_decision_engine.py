#!/usr/bin/env python3
"""
Objective Decision Engine for Innovation Zone
創新特區客觀決策引擎 - GPT-OSS整合任務2.2.3

This engine provides automated, data-driven decision-making capabilities for innovation zone
project management, including:
1. Project continuation/termination decisions
2. Budget reallocation recommendations  
3. Resource optimization decisions
4. Risk mitigation strategies
5. Performance intervention triggers
6. Strategic pivot recommendations
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
import json
import math

from .project_performance_monitor import (
    ProjectPerformanceMonitor, ProjectPerformanceMetrics,
    ProjectHealthStatus, PerformanceTrend
)
from .innovation_zone_db import InnovationZoneDB
from .models import ProjectStage, ROIExemptionStatus, InnovationType

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """決策類型"""
    PROJECT_CONTINUATION = "project_continuation"        # 項目繼續/終止決策
    BUDGET_REALLOCATION = "budget_reallocation"         # 預算重新分配決策
    RESOURCE_OPTIMIZATION = "resource_optimization"     # 資源優化決策
    RISK_MITIGATION = "risk_mitigation"                 # 風險緩解決策
    PERFORMANCE_INTERVENTION = "performance_intervention" # 性能干預決策
    STRATEGIC_PIVOT = "strategic_pivot"                 # 戰略轉向決策
    TEAM_ADJUSTMENT = "team_adjustment"                 # 團隊調整決策
    MILESTONE_REVISION = "milestone_revision"           # 里程碑修訂決策


class DecisionConfidence(Enum):
    """決策置信度"""
    VERY_HIGH = "very_high"     # 95%+ 置信度
    HIGH = "high"               # 85-95% 置信度  
    MEDIUM = "medium"           # 70-85% 置信度
    LOW = "low"                 # 50-70% 置信度
    VERY_LOW = "very_low"       # <50% 置信度


class DecisionUrgency(Enum):
    """決策緊急程度"""
    CRITICAL = "critical"       # 立即執行（24小時內）
    HIGH = "high"               # 高優先級（3天內）
    MEDIUM = "medium"           # 中等優先級（1週內）
    LOW = "low"                 # 低優先級（1個月內）


class DecisionImpact(Enum):
    """決策影響程度"""
    STRATEGIC = "strategic"     # 戰略級影響
    OPERATIONAL = "operational" # 運營級影響  
    TACTICAL = "tactical"       # 戰術級影響
    MINOR = "minor"             # 輕微影響


@dataclass
class DecisionCriteria:
    """決策標準"""
    criteria_id: str
    criteria_name: str
    weight: Decimal  # 權重 (0-1)
    threshold_value: Optional[Decimal] = None
    comparison_operator: str = ">"  # >, <, =, >=, <=
    description: str = ""
    is_mandatory: bool = False  # 是否為強制性標準


@dataclass
class DecisionContext:
    """決策上下文"""
    project_id: str
    project_name: str
    current_metrics: ProjectPerformanceMetrics
    historical_metrics: List[ProjectPerformanceMetrics]
    market_context: Dict[str, Any] = field(default_factory=dict)
    stakeholder_input: Dict[str, Any] = field(default_factory=dict)
    external_factors: Dict[str, Any] = field(default_factory=dict)
    decision_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DecisionRecommendation:
    """決策建議"""
    recommendation_id: str
    decision_type: DecisionType
    recommendation: str
    rationale: str
    confidence: DecisionConfidence
    urgency: DecisionUrgency
    impact: DecisionImpact
    
    # 量化指標
    expected_roi_impact: Optional[Decimal] = None
    risk_reduction: Optional[Decimal] = None
    cost_impact: Optional[Decimal] = None
    timeline_impact_days: Optional[int] = None
    
    # 實施細節
    implementation_steps: List[str] = field(default_factory=list)
    required_resources: Dict[str, Any] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)
    monitoring_checkpoints: List[str] = field(default_factory=list)
    
    # 風險和依賴
    implementation_risks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    rollback_plan: Optional[str] = None
    
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DecisionRule:
    """決策規則"""
    rule_id: str
    rule_name: str
    decision_type: DecisionType
    criteria: List[DecisionCriteria]
    conditions: Dict[str, Any]
    recommendation_template: str
    is_active: bool = True
    priority: int = 100  # 1-100, 數字越小優先級越高


class ObjectiveDecisionEngine:
    """
    創新特區客觀決策引擎
    
    功能：
    1. 基於多維度數據的自動決策建議
    2. 可配置的決策規則和標準  
    3. 置信度和風險評估
    4. 決策影響預測和量化
    5. 實施計劃和監控機制
    6. 決策歷史跟踪和學習
    """
    
    def __init__(
        self,
        performance_monitor: Optional[ProjectPerformanceMonitor] = None,
        innovation_db: Optional[InnovationZoneDB] = None
    ):
        """
        初始化客觀決策引擎
        
        Args:
            performance_monitor: 性能監控器
            innovation_db: 創新特區數據庫
        """
        self.performance_monitor = performance_monitor or ProjectPerformanceMonitor()
        self.innovation_db = innovation_db or InnovationZoneDB()
        
        # 決策規則庫
        self.decision_rules: Dict[str, DecisionRule] = {}
        
        # 決策歷史
        self.decision_history: Dict[str, List[DecisionRecommendation]] = {}
        
        # 配置
        self.config = {
            'decision_evaluation_weights': {
                'performance_metrics': 0.35,
                'trend_analysis': 0.25, 
                'risk_assessment': 0.20,
                'resource_utilization': 0.15,
                'stakeholder_alignment': 0.05
            },
            'confidence_thresholds': {
                'very_high': 0.95,
                'high': 0.85,
                'medium': 0.70,
                'low': 0.50
            },
            'urgency_criteria': {
                'critical_health_threshold': 30,  # 健康分數低於30為危急
                'high_risk_threshold': 0.80,      # 風險分數高於80為高風險
                'budget_overrun_threshold': 1.20   # 預算超支20%以上
            }
        }
        
        self.logger = logger
        
        # 初始化預設決策規則
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """初始化預設決策規則"""
        
        # 項目終止規則
        project_termination_rule = DecisionRule(
            rule_id="terminate_failing_project",
            rule_name="Terminate Failing Project",
            decision_type=DecisionType.PROJECT_CONTINUATION,
            criteria=[
                DecisionCriteria("health_score", "Overall Health Score", Decimal("0.4"), Decimal("40"), "<"),
                DecisionCriteria("consecutive_decline", "Consecutive Decline Periods", Decimal("0.3"), Decimal("3"), ">="),
                DecisionCriteria("roi_performance", "ROI Performance", Decimal("0.3"), Decimal("-20"), "<")
            ],
            conditions={
                'min_project_duration_days': 90,  # 項目至少運行90天
                'exclude_strategic_projects': True
            },
            recommendation_template="Recommend project termination due to consistently poor performance"
        )
        
        # 預算重新分配規則
        budget_reallocation_rule = DecisionRule(
            rule_id="reallocate_budget_high_performer",
            rule_name="Reallocate Budget to High Performer",
            decision_type=DecisionType.BUDGET_REALLOCATION,
            criteria=[
                DecisionCriteria("health_score", "Overall Health Score", Decimal("0.4"), Decimal("85"), ">"),
                DecisionCriteria("roi_trend", "ROI Trend", Decimal("0.3"), Decimal("10"), ">"),
                DecisionCriteria("resource_utilization", "Resource Utilization", Decimal("0.3"), Decimal("90"), ">")
            ],
            conditions={
                'available_budget_threshold': 50000
            },
            recommendation_template="Recommend additional budget allocation due to exceptional performance"
        )
        
        # 風險緩解規則
        risk_mitigation_rule = DecisionRule(
            rule_id="mitigate_high_risk",
            rule_name="Mitigate High Risk Project",
            decision_type=DecisionType.RISK_MITIGATION,
            criteria=[
                DecisionCriteria("risk_score", "Risk Score", Decimal("0.5"), Decimal("75"), ">"),
                DecisionCriteria("budget_utilization", "Budget Utilization", Decimal("0.3"), Decimal("85"), ">"),
                DecisionCriteria("milestone_delays", "Milestone Delays", Decimal("0.2"), Decimal("2"), ">")
            ],
            conditions={},
            recommendation_template="Recommend immediate risk mitigation actions"
        )
        
        # 性能干預規則
        performance_intervention_rule = DecisionRule(
            rule_id="intervene_declining_performance",
            rule_name="Intervene on Declining Performance", 
            decision_type=DecisionType.PERFORMANCE_INTERVENTION,
            criteria=[
                DecisionCriteria("performance_trend", "Performance Trend", Decimal("0.4"), None),
                DecisionCriteria("health_decline", "Health Score Decline", Decimal("0.3"), Decimal("15"), ">"),
                DecisionCriteria("user_engagement", "User Engagement", Decimal("0.3"), Decimal("60"), "<")
            ],
            conditions={
                'trend_must_be_declining': True
            },
            recommendation_template="Recommend performance intervention to reverse declining trend"
        )
        
        # 戰略轉向規則
        strategic_pivot_rule = DecisionRule(
            rule_id="strategic_pivot_opportunity",
            rule_name="Strategic Pivot Opportunity",
            decision_type=DecisionType.STRATEGIC_PIVOT,
            criteria=[
                DecisionCriteria("market_opportunity", "Market Opportunity Score", Decimal("0.4"), Decimal("80"), ">"),
                DecisionCriteria("current_progress", "Current Progress", Decimal("0.3"), Decimal("40"), "<"),
                DecisionCriteria("pivot_feasibility", "Pivot Feasibility", Decimal("0.3"), Decimal("70"), ">")
            ],
            conditions={
                'innovation_type': ['disruptive', 'breakthrough']
            },
            recommendation_template="Recommend strategic pivot to capture new opportunity"
        )
        
        # 註冊規則
        rules = [
            project_termination_rule,
            budget_reallocation_rule, 
            risk_mitigation_rule,
            performance_intervention_rule,
            strategic_pivot_rule
        ]
        
        for rule in rules:
            self.decision_rules[rule.rule_id] = rule
    
    async def generate_decision_recommendations(
        self,
        project_id: str,
        include_context: bool = True
    ) -> List[DecisionRecommendation]:
        """
        為指定項目生成決策建議
        
        Args:
            project_id: 項目ID
            include_context: 是否包含決策上下文信息
            
        Returns:
            決策建議列表
        """
        try:
            # 獲取項目性能指標
            current_metrics = await self.performance_monitor.calculate_project_performance(project_id)
            
            # 獲取歷史指標
            historical_metrics = self.performance_monitor.performance_history.get(project_id, [])
            
            # 構建決策上下文
            context = DecisionContext(
                project_id=project_id,
                project_name=current_metrics.project_name,
                current_metrics=current_metrics,
                historical_metrics=historical_metrics[-10:]  # 最近10次記錄
            )
            
            if include_context:
                await self._enrich_decision_context(context)
            
            # 評估所有活躍的決策規則
            recommendations = []
            
            for rule_id, rule in self.decision_rules.items():
                if not rule.is_active:
                    continue
                
                recommendation = await self._evaluate_decision_rule(rule, context)
                if recommendation:
                    recommendations.append(recommendation)
            
            # 按優先級和置信度排序
            recommendations.sort(key=lambda r: (
                r.urgency.value,
                -self._confidence_to_score(r.confidence),
                r.impact.value
            ))
            
            # 保存決策歷史
            if project_id not in self.decision_history:
                self.decision_history[project_id] = []
            
            for rec in recommendations:
                self.decision_history[project_id].append(rec)
                # 限制歷史記錄數量
                if len(self.decision_history[project_id]) > 50:
                    self.decision_history[project_id] = self.decision_history[project_id][-50:]
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ Error generating decision recommendations for project {project_id}: {e}")
            return []
    
    async def _enrich_decision_context(self, context: DecisionContext):
        """豐富決策上下文信息"""
        try:
            # 獲取市場環境信息（模擬）
            context.market_context = {
                'market_volatility': 'medium',
                'innovation_funding_climate': 'favorable',
                'competitive_pressure': 'high',
                'regulatory_environment': 'stable'
            }
            
            # 獲取利益相關者意見（模擬）
            context.stakeholder_input = {
                'sponsor_satisfaction': 0.75,
                'team_morale': 0.80,
                'customer_feedback_score': 0.70,
                'executive_priority_level': 'medium'
            }
            
            # 獲取外部因素（模擬）
            context.external_factors = {
                'technology_readiness': 0.85,
                'market_timing_score': 0.75,
                'resource_availability': 0.90,
                'strategic_alignment': 0.80
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error enriching decision context: {e}")
    
    async def _evaluate_decision_rule(
        self,
        rule: DecisionRule,
        context: DecisionContext
    ) -> Optional[DecisionRecommendation]:
        """評估單個決策規則"""
        try:
            # 檢查條件是否滿足
            if not self._check_rule_conditions(rule, context):
                return None
            
            # 評估所有決策標準
            criteria_scores = []
            total_weight = Decimal('0')
            
            for criteria in rule.criteria:
                score, meets_threshold = self._evaluate_criteria(criteria, context)
                if score is not None:
                    criteria_scores.append({
                        'criteria': criteria,
                        'score': score,
                        'meets_threshold': meets_threshold,
                        'weight': criteria.weight
                    })
                    total_weight += criteria.weight
            
            if not criteria_scores:
                return None
            
            # 計算綜合評分
            weighted_score = sum(
                cs['score'] * cs['weight'] for cs in criteria_scores
            ) / total_weight if total_weight > 0 else Decimal('0')
            
            # 檢查強制性標準
            mandatory_met = all(
                cs['meets_threshold'] for cs in criteria_scores
                if cs['criteria'].is_mandatory
            )
            
            # 確定是否應該生成建議
            confidence_score = float(weighted_score)
            if confidence_score < 0.5 or not mandatory_met:
                return None
            
            # 生成決策建議
            recommendation = self._create_recommendation(
                rule, context, criteria_scores, confidence_score
            )
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating decision rule {rule.rule_id}: {e}")
            return None
    
    def _check_rule_conditions(self, rule: DecisionRule, context: DecisionContext) -> bool:
        """檢查規則條件是否滿足"""
        try:
            conditions = rule.conditions
            metrics = context.current_metrics
            
            # 檢查最小項目運行時間
            if 'min_project_duration_days' in conditions:
                min_days = conditions['min_project_duration_days']
                # 簡化實現，假設項目已運行足夠時間
                pass
            
            # 檢查是否排除戰略項目
            if conditions.get('exclude_strategic_projects', False):
                if context.external_factors.get('strategic_alignment', 0) > 0.9:
                    return False
            
            # 檢查創新類型
            if 'innovation_type' in conditions:
                # 簡化實現，假設符合條件
                pass
            
            # 檢查趨勢條件
            if conditions.get('trend_must_be_declining', False):
                if metrics.performance_trend != PerformanceTrend.DECLINING:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error checking rule conditions: {e}")
            return False
    
    def _evaluate_criteria(
        self,
        criteria: DecisionCriteria,
        context: DecisionContext
    ) -> Tuple[Optional[Decimal], bool]:
        """評估單個決策標準"""
        try:
            metrics = context.current_metrics
            
            # 獲取標準值
            if criteria.criteria_id == "health_score":
                value = metrics.health_score
            elif criteria.criteria_id == "risk_score":
                value = metrics.risk_score
            elif criteria.criteria_id == "roi_performance":
                value = metrics.roi_percentage or Decimal('0')
            elif criteria.criteria_id == "consecutive_decline":
                # 計算連續下降期數
                value = self._calculate_consecutive_decline_periods(context.historical_metrics)
            elif criteria.criteria_id == "roi_trend":
                value = self._calculate_roi_trend(context.historical_metrics)
            elif criteria.criteria_id == "resource_utilization":
                value = metrics.budget_utilization_rate
            elif criteria.criteria_id == "budget_utilization":
                value = metrics.budget_utilization_rate
            elif criteria.criteria_id == "milestone_delays":
                value = Decimal(str(metrics.milestones_behind_schedule))
            elif criteria.criteria_id == "performance_trend":
                # 特殊處理趨勢標準
                if metrics.performance_trend == PerformanceTrend.DECLINING:
                    return Decimal('1.0'), True
                else:
                    return Decimal('0.0'), False
            elif criteria.criteria_id == "health_decline":
                value = self._calculate_health_decline(context.historical_metrics)
            elif criteria.criteria_id == "user_engagement":
                value = metrics.user_engagement_score
            else:
                # 處理外部因素
                value = self._get_external_criteria_value(criteria.criteria_id, context)
            
            if value is None:
                return None, False
            
            # 評估閾值
            meets_threshold = True
            if criteria.threshold_value is not None:
                threshold = criteria.threshold_value
                operator = criteria.comparison_operator
                
                if operator == ">":
                    meets_threshold = value > threshold
                elif operator == "<":
                    meets_threshold = value < threshold
                elif operator == ">=":
                    meets_threshold = value >= threshold
                elif operator == "<=":
                    meets_threshold = value <= threshold
                elif operator == "=":
                    meets_threshold = abs(value - threshold) < Decimal('0.01')
            
            # 標準化分數 (0-1)
            normalized_score = self._normalize_criteria_score(criteria.criteria_id, value)
            
            return normalized_score, meets_threshold
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating criteria {criteria.criteria_id}: {e}")
            return None, False
    
    def _calculate_consecutive_decline_periods(self, historical_metrics: List[ProjectPerformanceMetrics]) -> Decimal:
        """計算連續下降期數"""
        if len(historical_metrics) < 2:
            return Decimal('0')
        
        consecutive_count = 0
        for i in range(len(historical_metrics) - 1, 0, -1):
            current = historical_metrics[i]
            previous = historical_metrics[i - 1]
            
            if current.health_score < previous.health_score:
                consecutive_count += 1
            else:
                break
        
        return Decimal(str(consecutive_count))
    
    def _calculate_roi_trend(self, historical_metrics: List[ProjectPerformanceMetrics]) -> Decimal:
        """計算ROI趨勢"""
        if len(historical_metrics) < 2:
            return Decimal('0')
        
        recent_roi = []
        for metric in historical_metrics[-5:]:  # 最近5期
            if metric.roi_percentage is not None:
                recent_roi.append(float(metric.roi_percentage))
        
        if len(recent_roi) < 2:
            return Decimal('0')
        
        # 簡單線性趨勢計算
        n = len(recent_roi)
        x_mean = (n - 1) / 2
        y_mean = sum(recent_roi) / n
        
        numerator = sum((i - x_mean) * (roi - y_mean) for i, roi in enumerate(recent_roi))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return Decimal('0')
        
        slope = numerator / denominator
        return Decimal(str(slope))
    
    def _calculate_health_decline(self, historical_metrics: List[ProjectPerformanceMetrics]) -> Decimal:
        """計算健康分數下降幅度"""
        if len(historical_metrics) < 2:
            return Decimal('0')
        
        current_health = historical_metrics[-1].health_score
        previous_health = historical_metrics[-2].health_score
        
        decline = previous_health - current_health
        return max(Decimal('0'), decline)
    
    def _get_external_criteria_value(self, criteria_id: str, context: DecisionContext) -> Optional[Decimal]:
        """獲取外部標準值"""
        if criteria_id == "market_opportunity":
            return Decimal('80')  # 模擬市場機會分數
        elif criteria_id == "current_progress":
            return context.current_metrics.milestone_completion_rate
        elif criteria_id == "pivot_feasibility":
            return Decimal('75')  # 模擬轉向可行性分數
        
        return None
    
    def _normalize_criteria_score(self, criteria_id: str, value: Decimal) -> Decimal:
        """標準化標準分數"""
        # 簡化的標準化實現
        if criteria_id in ["health_score", "user_engagement", "resource_utilization"]:
            # 百分比類型，已經在0-100範圍內
            return value / 100
        elif criteria_id == "risk_score":
            # 風險分數，反向標準化
            return (100 - value) / 100
        elif criteria_id == "roi_performance":
            # ROI，映射到0-1範圍
            return max(Decimal('0'), min(Decimal('1'), (value + 50) / 100))
        else:
            # 其他類型，簡單映射
            return min(Decimal('1'), max(Decimal('0'), value / 100))
    
    def _create_recommendation(
        self,
        rule: DecisionRule,
        context: DecisionContext,
        criteria_scores: List[Dict],
        confidence_score: float
    ) -> DecisionRecommendation:
        """創建決策建議"""
        
        # 確定置信度等級
        confidence = self._score_to_confidence(confidence_score)
        
        # 確定緊急程度
        urgency = self._determine_urgency(rule, context, criteria_scores)
        
        # 確定影響程度
        impact = self._determine_impact(rule, context)
        
        # 生成建議內容
        recommendation_text = self._generate_recommendation_text(rule, context, criteria_scores)
        
        # 生成理由
        rationale = self._generate_rationale(rule, context, criteria_scores)
        
        # 創建建議對象
        recommendation = DecisionRecommendation(
            recommendation_id=f"{rule.rule_id}_{context.project_id}_{int(datetime.now().timestamp())}",
            decision_type=rule.decision_type,
            recommendation=recommendation_text,
            rationale=rationale,
            confidence=confidence,
            urgency=urgency,
            impact=impact
        )
        
        # 計算量化指標
        self._calculate_quantitative_impacts(recommendation, rule, context)
        
        # 生成實施細節
        self._generate_implementation_details(recommendation, rule, context)
        
        return recommendation
    
    def _confidence_to_score(self, confidence: DecisionConfidence) -> float:
        """置信度轉換為分數"""
        mapping = {
            DecisionConfidence.VERY_HIGH: 0.95,
            DecisionConfidence.HIGH: 0.85,
            DecisionConfidence.MEDIUM: 0.75,
            DecisionConfidence.LOW: 0.60,
            DecisionConfidence.VERY_LOW: 0.40
        }
        return mapping.get(confidence, 0.50)
    
    def _score_to_confidence(self, score: float) -> DecisionConfidence:
        """分數轉換為置信度"""
        thresholds = self.config['confidence_thresholds']
        
        if score >= thresholds['very_high']:
            return DecisionConfidence.VERY_HIGH
        elif score >= thresholds['high']:
            return DecisionConfidence.HIGH
        elif score >= thresholds['medium']:
            return DecisionConfidence.MEDIUM
        elif score >= thresholds['low']:
            return DecisionConfidence.LOW
        else:
            return DecisionConfidence.VERY_LOW
    
    def _determine_urgency(
        self,
        rule: DecisionRule,
        context: DecisionContext,
        criteria_scores: List[Dict]
    ) -> DecisionUrgency:
        """確定緊急程度"""
        metrics = context.current_metrics
        urgency_config = self.config['urgency_criteria']
        
        # 危急健康分數
        if metrics.health_score < urgency_config['critical_health_threshold']:
            return DecisionUrgency.CRITICAL
        
        # 高風險分數
        if metrics.risk_score > urgency_config['high_risk_threshold'] * 100:
            return DecisionUrgency.HIGH
        
        # 嚴重預算超支
        if metrics.budget_utilization_rate > urgency_config['budget_overrun_threshold'] * 100:
            return DecisionUrgency.HIGH
        
        # 根據決策類型確定默認緊急程度
        if rule.decision_type == DecisionType.PROJECT_CONTINUATION:
            return DecisionUrgency.HIGH
        elif rule.decision_type == DecisionType.RISK_MITIGATION:
            return DecisionUrgency.HIGH
        elif rule.decision_type == DecisionType.PERFORMANCE_INTERVENTION:
            return DecisionUrgency.MEDIUM
        else:
            return DecisionUrgency.LOW
    
    def _determine_impact(self, rule: DecisionRule, context: DecisionContext) -> DecisionImpact:
        """確定影響程度"""
        if rule.decision_type in [DecisionType.PROJECT_CONTINUATION, DecisionType.STRATEGIC_PIVOT]:
            return DecisionImpact.STRATEGIC
        elif rule.decision_type in [DecisionType.BUDGET_REALLOCATION, DecisionType.RESOURCE_OPTIMIZATION]:
            return DecisionImpact.OPERATIONAL
        elif rule.decision_type in [DecisionType.PERFORMANCE_INTERVENTION, DecisionType.TEAM_ADJUSTMENT]:
            return DecisionImpact.TACTICAL
        else:
            return DecisionImpact.MINOR
    
    def _generate_recommendation_text(
        self,
        rule: DecisionRule,
        context: DecisionContext,
        criteria_scores: List[Dict]
    ) -> str:
        """生成建議文本"""
        metrics = context.current_metrics
        
        if rule.decision_type == DecisionType.PROJECT_CONTINUATION:
            if any(cs['meets_threshold'] for cs in criteria_scores):
                return f"Recommend terminating project '{context.project_name}' due to consistently poor performance (Health Score: {metrics.health_score}, Risk Score: {metrics.risk_score})"
            else:
                return f"Recommend continuing project '{context.project_name}' with enhanced monitoring"
        
        elif rule.decision_type == DecisionType.BUDGET_REALLOCATION:
            return f"Recommend allocating additional budget to high-performing project '{context.project_name}' (Current utilization: {metrics.budget_utilization_rate}%)"
        
        elif rule.decision_type == DecisionType.RISK_MITIGATION:
            return f"Recommend immediate risk mitigation for project '{context.project_name}' (Risk Score: {metrics.risk_score}, {metrics.milestones_behind_schedule} delayed milestones)"
        
        elif rule.decision_type == DecisionType.PERFORMANCE_INTERVENTION:
            return f"Recommend performance intervention for project '{context.project_name}' showing declining trend (Health decline from {metrics.health_score})"
        
        else:
            return rule.recommendation_template.format(
                project_name=context.project_name,
                health_score=metrics.health_score,
                risk_score=metrics.risk_score
            )
    
    def _generate_rationale(
        self,
        rule: DecisionRule,
        context: DecisionContext,
        criteria_scores: List[Dict]
    ) -> str:
        """生成決策理由"""
        metrics = context.current_metrics
        
        rationale_parts = [
            f"Based on analysis of project '{context.project_name}':",
        ]
        
        # 添加關鍵指標
        rationale_parts.extend([
            f"• Overall Health Score: {metrics.health_score}/100",
            f"• Risk Score: {metrics.risk_score}/100",
            f"• Performance Trend: {metrics.performance_trend.value}",
            f"• Budget Utilization: {metrics.budget_utilization_rate}%",
            f"• Milestone Completion: {metrics.milestone_completion_rate}%"
        ])
        
        # 添加滿足的標準
        met_criteria = [cs for cs in criteria_scores if cs['meets_threshold']]
        if met_criteria:
            rationale_parts.append("Key decision criteria met:")
            for cs in met_criteria:
                rationale_parts.append(f"• {cs['criteria'].criteria_name}: {cs['criteria'].description}")
        
        return "\n".join(rationale_parts)
    
    def _calculate_quantitative_impacts(
        self,
        recommendation: DecisionRecommendation,
        rule: DecisionRule,
        context: DecisionContext
    ):
        """計算量化影響"""
        metrics = context.current_metrics
        
        if rule.decision_type == DecisionType.PROJECT_CONTINUATION:
            # 項目終止的成本節省
            recommendation.cost_impact = -metrics.budget_remaining
            recommendation.timeline_impact_days = 0  # 立即終止
            
        elif rule.decision_type == DecisionType.BUDGET_REALLOCATION:
            # 預算重新分配的ROI影響
            recommendation.expected_roi_impact = Decimal('15')  # 預期15%的ROI提升
            recommendation.cost_impact = Decimal('50000')  # 額外投資
            
        elif rule.decision_type == DecisionType.RISK_MITIGATION:
            # 風險緩解的風險降低
            recommendation.risk_reduction = metrics.risk_score * Decimal('0.3')  # 預期降低30%風險
            recommendation.cost_impact = Decimal('20000')  # 風險緩解成本
            
        elif rule.decision_type == DecisionType.PERFORMANCE_INTERVENTION:
            # 性能干預的改進預期
            recommendation.expected_roi_impact = Decimal('10')  # 預期10%改進
            recommendation.timeline_impact_days = 30  # 30天見效
    
    def _generate_implementation_details(
        self,
        recommendation: DecisionRecommendation,
        rule: DecisionRule,
        context: DecisionContext
    ):
        """生成實施細節"""
        
        if rule.decision_type == DecisionType.PROJECT_CONTINUATION:
            recommendation.implementation_steps = [
                "Schedule stakeholder meeting to discuss termination",
                "Document lessons learned and project outcomes",
                "Reassign team members to other projects",
                "Archive project assets and documentation",
                "Release remaining budget for reallocation"
            ]
            recommendation.rollback_plan = "Projects cannot be un-terminated, ensure thorough evaluation"
            
        elif rule.decision_type == DecisionType.BUDGET_REALLOCATION:
            recommendation.implementation_steps = [
                "Assess current budget utilization and needs",
                "Prepare budget increase proposal with ROI projections",
                "Obtain stakeholder and finance approvals",
                "Update project budget allocations",
                "Establish enhanced monitoring and reporting"
            ]
            recommendation.rollback_plan = "Budget can be reallocated back if performance doesn't improve within 60 days"
            
        elif rule.decision_type == DecisionType.RISK_MITIGATION:
            recommendation.implementation_steps = [
                "Conduct detailed risk assessment and prioritization",
                "Develop specific mitigation plans for top risks",
                "Allocate additional resources for risk management",
                "Implement enhanced monitoring and early warning systems",
                "Schedule regular risk review meetings"
            ]
            
        elif rule.decision_type == DecisionType.PERFORMANCE_INTERVENTION:
            recommendation.implementation_steps = [
                "Analyze root causes of performance decline",
                "Develop targeted improvement action plan",
                "Provide additional training or resources to team",
                "Implement weekly performance check-ins",
                "Adjust project scope or timeline if necessary"
            ]
        
        # 通用成功指標
        recommendation.success_metrics = [
            "Health score improvement within 30 days",
            "Risk score reduction within 60 days", 
            "Milestone completion rate improvement",
            "Team satisfaction and morale metrics"
        ]
        
        # 通用監控檢查點
        recommendation.monitoring_checkpoints = [
            "Week 1: Initial implementation review",
            "Week 2: Early results assessment", 
            "Month 1: Comprehensive progress evaluation",
            "Month 3: Long-term impact assessment"
        ]
    
    async def get_decision_analytics(
        self,
        project_id: Optional[str] = None,
        decision_type: Optional[DecisionType] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        獲取決策分析報告
        
        Args:
            project_id: 項目ID（可選，為空則分析所有項目）
            decision_type: 決策類型（可選）
            time_range_days: 時間範圍（天）
            
        Returns:
            決策分析報告
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_range_days)
            
            # 收集決策數據
            all_decisions = []
            projects_to_analyze = [project_id] if project_id else list(self.decision_history.keys())
            
            for pid in projects_to_analyze:
                project_decisions = self.decision_history.get(pid, [])
                
                # 過濾時間範圍和決策類型
                filtered_decisions = [
                    d for d in project_decisions
                    if d.created_at >= cutoff_date
                    and (not decision_type or d.decision_type == decision_type)
                ]
                
                all_decisions.extend(filtered_decisions)
            
            if not all_decisions:
                return {
                    'summary': {'total_decisions': 0},
                    'message': 'No decisions found for the specified criteria'
                }
            
            # 生成分析
            analytics = {
                'summary': {
                    'total_decisions': len(all_decisions),
                    'time_range_days': time_range_days,
                    'projects_analyzed': len(projects_to_analyze)
                },
                'decision_breakdown': self._analyze_decision_breakdown(all_decisions),
                'confidence_distribution': self._analyze_confidence_distribution(all_decisions),
                'urgency_distribution': self._analyze_urgency_distribution(all_decisions),
                'impact_distribution': self._analyze_impact_distribution(all_decisions),
                'trends': self._analyze_decision_trends(all_decisions),
                'effectiveness': self._analyze_decision_effectiveness(all_decisions)
            }
            
            return analytics
            
        except Exception as e:
            self.logger.error(f"❌ Error generating decision analytics: {e}")
            return {'error': str(e)}
    
    def _analyze_decision_breakdown(self, decisions: List[DecisionRecommendation]) -> Dict[str, int]:
        """分析決策類型分布"""
        breakdown = {}
        for decision in decisions:
            decision_type = decision.decision_type.value
            breakdown[decision_type] = breakdown.get(decision_type, 0) + 1
        return breakdown
    
    def _analyze_confidence_distribution(self, decisions: List[DecisionRecommendation]) -> Dict[str, int]:
        """分析置信度分布"""
        distribution = {}
        for decision in decisions:
            confidence = decision.confidence.value
            distribution[confidence] = distribution.get(confidence, 0) + 1
        return distribution
    
    def _analyze_urgency_distribution(self, decisions: List[DecisionRecommendation]) -> Dict[str, int]:
        """分析緊急程度分布"""
        distribution = {}
        for decision in decisions:
            urgency = decision.urgency.value
            distribution[urgency] = distribution.get(urgency, 0) + 1
        return distribution
    
    def _analyze_impact_distribution(self, decisions: List[DecisionRecommendation]) -> Dict[str, int]:
        """分析影響程度分布"""
        distribution = {}
        for decision in decisions:
            impact = decision.impact.value
            distribution[impact] = distribution.get(impact, 0) + 1
        return distribution
    
    def _analyze_decision_trends(self, decisions: List[DecisionRecommendation]) -> Dict[str, Any]:
        """分析決策趨勢"""
        if not decisions:
            return {}
        
        # 按日期排序
        sorted_decisions = sorted(decisions, key=lambda d: d.created_at)
        
        # 計算每日決策數量
        daily_counts = {}
        for decision in sorted_decisions:
            date_key = decision.created_at.date().isoformat()
            daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
        
        return {
            'daily_decision_counts': daily_counts,
            'peak_decision_date': max(daily_counts.items(), key=lambda x: x[1])[0],
            'avg_decisions_per_day': len(decisions) / max(1, len(daily_counts))
        }
    
    def _analyze_decision_effectiveness(self, decisions: List[DecisionRecommendation]) -> Dict[str, Any]:
        """分析決策有效性"""
        # 簡化的有效性分析
        high_confidence_decisions = [d for d in decisions if d.confidence in [DecisionConfidence.HIGH, DecisionConfidence.VERY_HIGH]]
        critical_urgent_decisions = [d for d in decisions if d.urgency == DecisionUrgency.CRITICAL]
        
        return {
            'high_confidence_percentage': len(high_confidence_decisions) / len(decisions) * 100 if decisions else 0,
            'critical_decisions_count': len(critical_urgent_decisions),
            'avg_expected_roi_impact': sum(
                float(d.expected_roi_impact or 0) for d in decisions
            ) / len(decisions) if decisions else 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """服務健康檢查"""
        return {
            'service': 'objective_decision_engine',
            'status': 'healthy',
            'decision_rules_count': len(self.decision_rules),
            'active_rules_count': sum(1 for rule in self.decision_rules.values() if rule.is_active),
            'projects_with_decisions': len(self.decision_history),
            'total_decisions_made': sum(len(decisions) for decisions in self.decision_history.values()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }