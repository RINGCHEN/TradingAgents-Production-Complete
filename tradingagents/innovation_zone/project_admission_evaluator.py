#!/usr/bin/env python3
"""
Project Admission Evaluator
項目准入評估系統

專門用於評估創新項目是否符合創新特區准入標準：
- 多維度評估標準（創新潛力、市場顛覆性、技術可行性等）
- 智能評分算法和權重配置
- 競爭分析和市場機會評估
- 團隊能力和資源需求分析
- 戰略一致性和風險評估
- 綜合評分和准入決策建議
"""

import asyncio
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import uuid
import statistics
from dataclasses import dataclass, field
from enum import Enum

from .models import AdmissionCriteria, InnovationType

logger = logging.getLogger(__name__)

class EvaluationMethod(str, Enum):
    """評估方法枚舉"""
    EXPERT_PANEL = "expert_panel"
    ALGORITHMIC = "algorithmic"
    HYBRID = "hybrid"
    PEER_REVIEW = "peer_review"
    MARKET_RESEARCH = "market_research"

class ConfidenceLevel(str, Enum):
    """信心度等級"""
    VERY_HIGH = "very_high"  # >90%
    HIGH = "high"            # 80-90%
    MEDIUM = "medium"        # 60-80%
    LOW = "low"              # 40-60%
    VERY_LOW = "very_low"    # <40%

@dataclass
class CriteriaEvaluation:
    """單項標準評估結果"""
    criterion: str
    score: float
    weight: float
    weighted_score: float
    evaluation_method: EvaluationMethod
    confidence_level: ConfidenceLevel
    evidence: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)

@dataclass
class AdmissionEvaluationResult:
    """准入評估結果"""
    project_id: Optional[str]
    evaluation_id: uuid.UUID
    evaluation_date: datetime
    total_score: float
    minimum_threshold: float
    passed: bool
    confidence_level: ConfidenceLevel
    criteria_evaluations: List[CriteriaEvaluation]
    overall_strengths: List[str] = field(default_factory=list)
    overall_weaknesses: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    next_review_date: Optional[date] = None
    evaluator_notes: Optional[str] = None

@dataclass
class MarketOpportunityAnalysis:
    """市場機會分析"""
    market_size: float
    growth_rate: float
    competition_intensity: str
    entry_barriers: List[str]
    differentiation_opportunities: List[str]
    target_customer_segments: List[str]
    revenue_potential: str
    market_timing_score: float
    disruption_potential: float

@dataclass
class TeamCapabilityAssessment:
    """團隊能力評估"""
    technical_expertise_score: float
    domain_knowledge_score: float
    execution_track_record_score: float
    leadership_score: float
    team_composition_score: float
    missing_capabilities: List[str]
    strength_areas: List[str]
    development_needs: List[str]
    recommended_hires: List[str]

class ProjectAdmissionEvaluator:
    """
    項目准入評估系統
    
    功能：
    1. 多維度評估標準體系
    2. 智能評分算法和權重系統
    3. 市場機會和競爭分析
    4. 團隊能力和資源評估
    5. 風險評估和成功因素識別
    6. 綜合決策支持和建議生成
    """
    
    def __init__(self):
        """初始化項目准入評估系統"""
        self.logger = logger
        
        # 評估標準權重配置（預設值）
        self.default_criteria_weights = {
            AdmissionCriteria.INNOVATION_POTENTIAL.value: 0.25,
            AdmissionCriteria.MARKET_DISRUPTION.value: 0.20,
            AdmissionCriteria.TECHNICAL_FEASIBILITY.value: 0.20,
            AdmissionCriteria.TEAM_CAPABILITY.value: 0.15,
            AdmissionCriteria.STRATEGIC_ALIGNMENT.value: 0.10,
            AdmissionCriteria.COMPETITIVE_ADVANTAGE.value: 0.10
        }
        
        # 評估配置
        self.config = {
            'minimum_admission_score': 75.0,
            'confidence_threshold': 0.8,
            'require_expert_panel_for_high_risk': True,
            'market_research_required_threshold': 80.0,
            'technical_validation_required_threshold': 85.0,
            'team_interview_required_threshold': 80.0
        }
        
        # 創新類型風險係數
        self.innovation_risk_factors = {
            InnovationType.DISRUPTIVE: 0.9,
            InnovationType.BREAKTHROUGH: 0.8,
            InnovationType.PLATFORM: 0.7,
            InnovationType.TECHNOLOGY: 0.6,
            InnovationType.BUSINESS_MODEL: 0.5,
            InnovationType.INCREMENTAL: 0.3,
            InnovationType.PROCESS: 0.2
        }
        
        # 市場規模評分標準
        self.market_size_scores = {
            'billion_plus': 100,
            'hundred_million_plus': 85,
            'ten_million_plus': 70,
            'million_plus': 55,
            'below_million': 30
        }
        
        # 評估統計
        self.evaluation_stats = {
            'total_evaluations': 0,
            'passed_evaluations': 0,
            'rejected_evaluations': 0,
            'pending_review_evaluations': 0
        }
        
        self.logger.info("✅ Project Admission Evaluator initialized")
    
    # ==================== 主要評估方法 ====================
    
    async def evaluate_project_admission(
        self,
        project_data: Dict[str, Any],
        zone_criteria: Dict[str, float],
        evaluation_data: Dict[str, Any],
        minimum_score: float = None
    ) -> Dict[str, Any]:
        """評估項目准入申請"""
        try:
            evaluation_id = uuid.uuid4()
            minimum_threshold = minimum_score or self.config['minimum_admission_score']
            
            self.logger.info(f"🔍 Starting project admission evaluation: {evaluation_id}")
            
            # 執行各項標準評估
            criteria_evaluations = []
            total_weighted_score = 0.0
            
            for criterion, weight in zone_criteria.items():
                if weight > 0:  # 只評估有權重的標準
                    evaluation = await self._evaluate_single_criterion(
                        criterion, project_data, evaluation_data, weight
                    )
                    criteria_evaluations.append(evaluation)
                    total_weighted_score += evaluation.weighted_score
            
            # 計算總分
            total_score = total_weighted_score
            passed = total_score >= minimum_threshold
            
            # 確定信心度
            confidence_level = self._determine_confidence_level(criteria_evaluations, total_score)
            
            # 分析優勢和劣勢
            strengths, weaknesses = self._analyze_overall_performance(criteria_evaluations)
            
            # 識別風險和成功因素
            risk_factors = await self._identify_risk_factors(project_data, criteria_evaluations)
            success_factors = await self._identify_success_factors(project_data, criteria_evaluations)
            
            # 生成建議
            recommendations = await self._generate_admission_recommendations(
                project_data, criteria_evaluations, total_score, passed
            )
            
            # 創建評估結果
            result = AdmissionEvaluationResult(
                project_id=project_data.get('project_code'),
                evaluation_id=evaluation_id,
                evaluation_date=datetime.now(timezone.utc),
                total_score=total_score,
                minimum_threshold=minimum_threshold,
                passed=passed,
                confidence_level=confidence_level,
                criteria_evaluations=criteria_evaluations,
                overall_strengths=strengths,
                overall_weaknesses=weaknesses,
                risk_factors=risk_factors,
                success_factors=success_factors,
                recommendations=recommendations
            )
            
            # 更新統計
            self.evaluation_stats['total_evaluations'] += 1
            if passed:
                self.evaluation_stats['passed_evaluations'] += 1
            else:
                self.evaluation_stats['rejected_evaluations'] += 1
            
            self.logger.info(
                f"✅ Completed admission evaluation: {evaluation_id} -> "
                f"{total_score:.2f} ({'PASSED' if passed else 'REJECTED'})"
            )
            
            # 轉換為字典格式返回
            return {
                'evaluation_id': str(evaluation_id),
                'total_score': total_score,
                'minimum_threshold': minimum_threshold,
                'passed': passed,
                'confidence_level': confidence_level.value,
                'criteria_scores': {
                    eval.criterion: eval.score for eval in criteria_evaluations
                },
                'strengths': strengths,
                'weaknesses': weaknesses,
                'risk_factors': risk_factors,
                'success_factors': success_factors,
                'recommendations': recommendations,
                'evaluation_date': result.evaluation_date.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating project admission: {e}")
            raise
    
    async def _evaluate_single_criterion(
        self,
        criterion: str,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any],
        weight: float
    ) -> CriteriaEvaluation:
        """評估單項標準"""
        try:
            if criterion == AdmissionCriteria.INNOVATION_POTENTIAL.value:
                evaluation = await self._evaluate_innovation_potential(project_data, evaluation_data)
            elif criterion == AdmissionCriteria.MARKET_DISRUPTION.value:
                evaluation = await self._evaluate_market_disruption(project_data, evaluation_data)
            elif criterion == AdmissionCriteria.TECHNICAL_FEASIBILITY.value:
                evaluation = await self._evaluate_technical_feasibility(project_data, evaluation_data)
            elif criterion == AdmissionCriteria.TEAM_CAPABILITY.value:
                evaluation = await self._evaluate_team_capability(project_data, evaluation_data)
            elif criterion == AdmissionCriteria.STRATEGIC_ALIGNMENT.value:
                evaluation = await self._evaluate_strategic_alignment(project_data, evaluation_data)
            elif criterion == AdmissionCriteria.COMPETITIVE_ADVANTAGE.value:
                evaluation = await self._evaluate_competitive_advantage(project_data, evaluation_data)
            else:
                # 預設評估方法
                evaluation = self._create_default_evaluation(criterion, 70.0)
            
            # 設置權重和加權分數
            evaluation.weight = weight
            evaluation.weighted_score = evaluation.score * weight
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"❌ Error evaluating criterion {criterion}: {e}")
            # 返回低分評估作為fallback
            return self._create_default_evaluation(criterion, 40.0, weight)
    
    # ==================== 具體標準評估方法 ====================
    
    async def _evaluate_innovation_potential(
        self,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> CriteriaEvaluation:
        """評估創新潛力"""
        score = 0.0
        evidence = []
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 創新類型評分
        innovation_type = project_data.get('innovation_type', '')
        if innovation_type:
            type_score = {
                InnovationType.DISRUPTIVE.value: 100,
                InnovationType.BREAKTHROUGH.value: 90,
                InnovationType.PLATFORM.value: 80,
                InnovationType.TECHNOLOGY.value: 75,
                InnovationType.BUSINESS_MODEL.value: 70,
                InnovationType.INCREMENTAL.value: 60,
                InnovationType.PROCESS.value: 50
            }.get(innovation_type, 60)
            
            score += type_score * 0.4
            evidence.append(f"Innovation type: {innovation_type}")
            
            if type_score >= 90:
                strengths.append(f"High-impact {innovation_type} innovation")
            elif type_score < 60:
                weaknesses.append(f"Limited innovation potential with {innovation_type}")
        
        # 技術先進性評估
        tech_advancement = evaluation_data.get('technology_advancement_score', 60)
        score += tech_advancement * 0.3
        
        if tech_advancement >= 80:
            strengths.append("Advanced technology with significant differentiation")
        elif tech_advancement < 60:
            weaknesses.append("Limited technological advancement")
            suggestions.append("Consider incorporating more advanced technologies")
        
        # 市場新颖性
        market_novelty = evaluation_data.get('market_novelty_score', 60)
        score += market_novelty * 0.2
        
        # IP和专利潜力
        ip_potential = evaluation_data.get('ip_potential_score', 50)
        score += ip_potential * 0.1
        
        if ip_potential >= 80:
            strengths.append("Strong intellectual property potential")
        else:
            suggestions.append("Develop stronger IP protection strategy")
        
        # 確定信心度
        confidence = self._determine_single_criterion_confidence(score, evidence)
        
        return CriteriaEvaluation(
            criterion=AdmissionCriteria.INNOVATION_POTENTIAL.value,
            score=min(100, score),
            weight=0.0,  # 將在上層設置
            weighted_score=0.0,  # 將在上層設置
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=confidence,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    async def _evaluate_market_disruption(
        self,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> CriteriaEvaluation:
        """評估市場顛覆性"""
        score = 0.0
        evidence = []
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 市場規模評分
        market_size = evaluation_data.get('target_market_size', 'million_plus')
        size_score = self.market_size_scores.get(market_size, 50)
        score += size_score * 0.3
        evidence.append(f"Target market size: {market_size}")
        
        if size_score >= 85:
            strengths.append("Large addressable market")
        elif size_score < 55:
            weaknesses.append("Limited market size")
            suggestions.append("Consider expanding market scope or targeting adjacent markets")
        
        # 市場增長率
        growth_rate = evaluation_data.get('market_growth_rate', 10)
        growth_score = min(100, growth_rate * 5)  # 20%增長率 = 100分
        score += growth_score * 0.25
        
        if growth_rate >= 20:
            strengths.append("High market growth rate")
        elif growth_rate < 5:
            weaknesses.append("Low market growth rate")
        
        # 競爭激烈程度（越低越好）
        competition_intensity = evaluation_data.get('competition_intensity', 'medium')
        competition_score = {
            'low': 90,
            'medium': 70,
            'high': 40,
            'very_high': 20
        }.get(competition_intensity, 60)
        score += competition_score * 0.2
        
        # 顛覆潛力
        disruption_potential = evaluation_data.get('disruption_potential_score', 60)
        score += disruption_potential * 0.25
        
        if disruption_potential >= 80:
            strengths.append("High market disruption potential")
        else:
            suggestions.append("Strengthen value proposition for market disruption")
        
        confidence = self._determine_single_criterion_confidence(score, evidence)
        
        return CriteriaEvaluation(
            criterion=AdmissionCriteria.MARKET_DISRUPTION.value,
            score=min(100, score),
            weight=0.0,
            weighted_score=0.0,
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=confidence,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    async def _evaluate_technical_feasibility(
        self,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> CriteriaEvaluation:
        """評估技術可行性"""
        score = 0.0
        evidence = []
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 技術成熟度
        tech_maturity = evaluation_data.get('technology_maturity_level', 5)  # TRL 1-9
        maturity_score = (tech_maturity / 9) * 100
        score += maturity_score * 0.3
        evidence.append(f"Technology Readiness Level: {tech_maturity}")
        
        if tech_maturity >= 7:
            strengths.append("Mature technology ready for deployment")
        elif tech_maturity < 4:
            weaknesses.append("Early-stage technology with high technical risk")
            suggestions.append("Develop proof-of-concept to demonstrate feasibility")
        
        # 開發複雜度
        dev_complexity = evaluation_data.get('development_complexity', 'medium')
        complexity_score = {
            'low': 90,
            'medium': 70,
            'high': 50,
            'very_high': 30
        }.get(dev_complexity, 60)
        score += complexity_score * 0.25
        
        # 技術風險評估
        tech_risks = evaluation_data.get('technical_risk_score', 50)
        risk_score = 100 - tech_risks  # 風險越低分數越高
        score += risk_score * 0.2
        
        # 資源需求合理性
        resource_feasibility = evaluation_data.get('resource_feasibility_score', 60)
        score += resource_feasibility * 0.15
        
        # 時間可行性
        timeline_feasibility = evaluation_data.get('timeline_feasibility_score', 60)
        score += timeline_feasibility * 0.1
        
        if timeline_feasibility < 60:
            weaknesses.append("Aggressive timeline may impact feasibility")
            suggestions.append("Consider extending development timeline")
        
        confidence = self._determine_single_criterion_confidence(score, evidence)
        
        return CriteriaEvaluation(
            criterion=AdmissionCriteria.TECHNICAL_FEASIBILITY.value,
            score=min(100, score),
            weight=0.0,
            weighted_score=0.0,
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=confidence,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    async def _evaluate_team_capability(
        self,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> CriteriaEvaluation:
        """評估團隊能力"""
        score = 0.0
        evidence = []
        strengths = []
        weaknesses = []
        suggestions = []
        
        team_size = project_data.get('team_size', 1)
        evidence.append(f"Team size: {team_size}")
        
        # 團隊規模合理性
        if 3 <= team_size <= 8:
            size_score = 85
            strengths.append("Optimal team size for innovation project")
        elif team_size < 3:
            size_score = 60
            weaknesses.append("Small team size may limit capability coverage")
            suggestions.append("Consider expanding team with key expertise")
        else:
            size_score = 70
        
        score += size_score * 0.2
        
        # 技術專長評估
        technical_expertise = evaluation_data.get('technical_expertise_score', 60)
        score += technical_expertise * 0.3
        
        if technical_expertise >= 80:
            strengths.append("Strong technical expertise")
        elif technical_expertise < 60:
            weaknesses.append("Limited technical expertise")
            suggestions.append("Recruit senior technical talent or advisors")
        
        # 領域知識
        domain_knowledge = evaluation_data.get('domain_knowledge_score', 60)
        score += domain_knowledge * 0.2
        
        # 執行經驗
        execution_experience = evaluation_data.get('execution_track_record_score', 60)
        score += execution_experience * 0.2
        
        if execution_experience >= 80:
            strengths.append("Proven execution track record")
        elif execution_experience < 60:
            weaknesses.append("Limited execution experience")
            suggestions.append("Engage experienced advisors or mentors")
        
        # 團隊完整性
        team_completeness = evaluation_data.get('team_completeness_score', 60)
        score += team_completeness * 0.1
        
        confidence = self._determine_single_criterion_confidence(score, evidence)
        
        return CriteriaEvaluation(
            criterion=AdmissionCriteria.TEAM_CAPABILITY.value,
            score=min(100, score),
            weight=0.0,
            weighted_score=0.0,
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=confidence,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    async def _evaluate_strategic_alignment(
        self,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> CriteriaEvaluation:
        """評估戰略一致性"""
        score = 0.0
        evidence = []
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 與組織戰略的一致性
        org_alignment = evaluation_data.get('organizational_alignment_score', 60)
        score += org_alignment * 0.4
        
        if org_alignment >= 80:
            strengths.append("Strong alignment with organizational strategy")
        elif org_alignment < 60:
            weaknesses.append("Limited strategic alignment")
            suggestions.append("Better articulate strategic value and alignment")
        
        # 與創新重點的匹配
        innovation_focus_match = evaluation_data.get('innovation_focus_match_score', 60)
        score += innovation_focus_match * 0.3
        
        # 資源協同效應
        resource_synergy = evaluation_data.get('resource_synergy_score', 60)
        score += resource_synergy * 0.2
        
        # 長期價值潛力
        long_term_value = evaluation_data.get('long_term_value_score', 60)
        score += long_term_value * 0.1
        
        confidence = self._determine_single_criterion_confidence(score, evidence)
        
        return CriteriaEvaluation(
            criterion=AdmissionCriteria.STRATEGIC_ALIGNMENT.value,
            score=min(100, score),
            weight=0.0,
            weighted_score=0.0,
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=confidence,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    async def _evaluate_competitive_advantage(
        self,
        project_data: Dict[str, Any],
        evaluation_data: Dict[str, Any]
    ) -> CriteriaEvaluation:
        """評估競爭優勢"""
        score = 0.0
        evidence = []
        strengths = []
        weaknesses = []
        suggestions = []
        
        # 差異化程度
        differentiation = evaluation_data.get('differentiation_score', 60)
        score += differentiation * 0.3
        
        if differentiation >= 80:
            strengths.append("Strong product/service differentiation")
        elif differentiation < 60:
            weaknesses.append("Limited differentiation from competitors")
            suggestions.append("Strengthen unique value proposition")
        
        # 進入壁壘
        entry_barriers = evaluation_data.get('entry_barrier_score', 60)
        score += entry_barriers * 0.25
        
        # 網絡效應潛力
        network_effects = evaluation_data.get('network_effects_score', 50)
        score += network_effects * 0.2
        
        # 可防禦性
        defensibility = evaluation_data.get('defensibility_score', 60)
        score += defensibility * 0.15
        
        # 先發優勢
        first_mover_advantage = evaluation_data.get('first_mover_score', 50)
        score += first_mover_advantage * 0.1
        
        confidence = self._determine_single_criterion_confidence(score, evidence)
        
        return CriteriaEvaluation(
            criterion=AdmissionCriteria.COMPETITIVE_ADVANTAGE.value,
            score=min(100, score),
            weight=0.0,
            weighted_score=0.0,
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=confidence,
            evidence=evidence,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
    
    # ==================== 輔助分析方法 ====================
    
    def _create_default_evaluation(
        self,
        criterion: str,
        score: float,
        weight: float = 0.0
    ) -> CriteriaEvaluation:
        """創建預設評估結果"""
        return CriteriaEvaluation(
            criterion=criterion,
            score=score,
            weight=weight,
            weighted_score=score * weight,
            evaluation_method=EvaluationMethod.ALGORITHMIC,
            confidence_level=ConfidenceLevel.MEDIUM,
            evidence=[f"Default evaluation for {criterion}"],
            improvement_suggestions=["Provide more detailed evaluation data"]
        )
    
    def _determine_confidence_level(
        self,
        criteria_evaluations: List[CriteriaEvaluation],
        total_score: float
    ) -> ConfidenceLevel:
        """確定總體信心度"""
        # 計算平均信心度
        confidence_scores = {
            ConfidenceLevel.VERY_HIGH: 95,
            ConfidenceLevel.HIGH: 85,
            ConfidenceLevel.MEDIUM: 70,
            ConfidenceLevel.LOW: 55,
            ConfidenceLevel.VERY_LOW: 40
        }
        
        avg_confidence = statistics.mean([
            confidence_scores[eval.confidence_level] 
            for eval in criteria_evaluations
        ])
        
        # 基於分數和信心度確定等級
        if avg_confidence >= 90 and total_score >= 85:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 80 and total_score >= 75:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 65 and total_score >= 60:
            return ConfidenceLevel.MEDIUM
        elif avg_confidence >= 50:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _determine_single_criterion_confidence(
        self,
        score: float,
        evidence: List[str]
    ) -> ConfidenceLevel:
        """確定單項標準信心度"""
        evidence_quality = len(evidence) * 10  # 簡單的證據質量評估
        
        if score >= 85 and evidence_quality >= 30:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 75 and evidence_quality >= 20:
            return ConfidenceLevel.HIGH
        elif score >= 60 and evidence_quality >= 10:
            return ConfidenceLevel.MEDIUM
        elif score >= 40:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def _analyze_overall_performance(
        self,
        criteria_evaluations: List[CriteriaEvaluation]
    ) -> Tuple[List[str], List[str]]:
        """分析總體表現的優勢和劣勢"""
        all_strengths = []
        all_weaknesses = []
        
        for evaluation in criteria_evaluations:
            all_strengths.extend(evaluation.strengths)
            all_weaknesses.extend(evaluation.weaknesses)
        
        return all_strengths, all_weaknesses
    
    async def _identify_risk_factors(
        self,
        project_data: Dict[str, Any],
        criteria_evaluations: List[CriteriaEvaluation]
    ) -> List[str]:
        """識別風險因素"""
        risk_factors = []
        
        # 基於創新類型的風險
        innovation_type = project_data.get('innovation_type', '')
        if innovation_type in [InnovationType.DISRUPTIVE.value, InnovationType.BREAKTHROUGH.value]:
            risk_factors.append("High innovation risk due to disruptive/breakthrough nature")
        
        # 基於評估分數的風險
        for evaluation in criteria_evaluations:
            if evaluation.score < 60:
                risk_factors.append(f"Low score in {evaluation.criterion} ({evaluation.score:.1f})")
        
        # 基於團隊規模的風險
        team_size = project_data.get('team_size', 1)
        if team_size < 3:
            risk_factors.append("Small team size may limit execution capability")
        
        return risk_factors
    
    async def _identify_success_factors(
        self,
        project_data: Dict[str, Any],
        criteria_evaluations: List[CriteriaEvaluation]
    ) -> List[str]:
        """識別成功因素"""
        success_factors = []
        
        # 高分標準作為成功因素
        for evaluation in criteria_evaluations:
            if evaluation.score >= 85:
                success_factors.append(f"Strong performance in {evaluation.criterion} ({evaluation.score:.1f})")
        
        # 戰略一致性
        strategic_eval = next(
            (e for e in criteria_evaluations if e.criterion == AdmissionCriteria.STRATEGIC_ALIGNMENT.value),
            None
        )
        if strategic_eval and strategic_eval.score >= 80:
            success_factors.append("Strong strategic alignment increases success probability")
        
        return success_factors
    
    async def _generate_admission_recommendations(
        self,
        project_data: Dict[str, Any],
        criteria_evaluations: List[CriteriaEvaluation],
        total_score: float,
        passed: bool
    ) -> List[str]:
        """生成准入建議"""
        recommendations = []
        
        if passed:
            recommendations.append("Recommended for admission to innovation zone")
            
            # 針對高分項目的建議
            if total_score >= 90:
                recommendations.append("Excellent candidate - consider fast-track admission")
            elif total_score >= 80:
                recommendations.append("Strong candidate - standard admission process")
            else:
                recommendations.append("Acceptable candidate - monitor progress closely")
        else:
            recommendations.append("Not recommended for admission at current state")
            
            # 改進建議
            low_score_areas = [
                eval.criterion for eval in criteria_evaluations if eval.score < 60
            ]
            
            if low_score_areas:
                recommendations.append(
                    f"Address weaknesses in: {', '.join(low_score_areas)}"
                )
            
            recommendations.append("Consider reapplying after addressing key concerns")
        
        # 收集具體改進建議
        for evaluation in criteria_evaluations:
            if evaluation.improvement_suggestions:
                recommendations.extend(evaluation.improvement_suggestions)
        
        return recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            return {
                'component': 'project_admission_evaluator',
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc),
                'evaluation_stats': self.evaluation_stats,
                'configuration': {
                    'minimum_admission_score': self.config['minimum_admission_score'],
                    'confidence_threshold': self.config['confidence_threshold']
                },
                'criteria_weights': self.default_criteria_weights
            }
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {e}")
            return {
                'component': 'project_admission_evaluator',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc)
            }