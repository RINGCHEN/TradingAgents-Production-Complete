#!/usr/bin/env python3
"""
AI Analysis Optimizer - AI分析優化器
天工 (TianGong) - A/B測試驅動的AI分析品質優化系統

此模組負責：
1. A/B測試管理和執行
2. 分析品質追蹤和評估
3. 自動化優化建議
4. 性能指標監控
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import secrets  # 安全修復：使用加密安全的隨機數生成器替換random
import hashlib

from .smart_model_selector import SmartModelSelector, PerformanceMetric
from .llm_cost_optimizer import LLMCostOptimizer

class OptimizationDimension(Enum):
    """優化維度"""
    MODEL_SELECTION = "model_selection"     # 模型選擇
    PROMPT_ENGINEERING = "prompt_engineering"  # 提示詞工程
    ANALYSIS_DEPTH = "analysis_depth"       # 分析深度
    RESPONSE_FORMAT = "response_format"     # 回應格式
    CACHE_STRATEGY = "cache_strategy"       # 快取策略

class TestType(Enum):
    """測試類型"""
    MODEL_COMPARISON = "model_comparison"   # 模型對比
    PROMPT_VARIANT = "prompt_variant"       # 提示詞變體
    FEATURE_FLAG = "feature_flag"           # 功能開關
    ALGORITHM_VARIANT = "algorithm_variant" # 算法變體

class QualityMetric(Enum):
    """品質指標"""
    ACCURACY = "accuracy"                   # 準確性
    RELEVANCE = "relevance"                 # 相關性
    COMPLETENESS = "completeness"           # 完整性
    ACTIONABILITY = "actionability"         # 可操作性
    USER_SATISFACTION = "user_satisfaction" # 用戶滿意度

@dataclass
class ABTestExperiment:
    """A/B測試實驗"""
    experiment_id: str
    name: str
    description: str
    test_type: TestType
    optimization_dimension: OptimizationDimension
    control_variant: Dict[str, Any]         # 對照組
    treatment_variant: Dict[str, Any]       # 實驗組
    target_metrics: List[QualityMetric]
    traffic_allocation: float               # 實驗組流量比例
    start_date: str
    end_date: str
    minimum_sample_size: int
    significance_threshold: float = 0.05    # 統計顯著性閾值
    is_active: bool = True
    created_by: str = "ai_optimizer"

@dataclass
class AnalysisQualityRating:
    """分析品質評分"""
    analysis_id: str
    user_id: str
    experiment_id: Optional[str]
    variant_type: str                       # control/treatment
    quality_scores: Dict[QualityMetric, float]  # 各維度評分
    overall_score: float
    feedback_text: Optional[str]
    rating_timestamp: str
    task_type: str
    model_used: str

@dataclass
class OptimizationInsight:
    """優化洞察"""
    insight_id: str
    dimension: OptimizationDimension
    title: str
    description: str
    confidence_level: float
    potential_improvement: float
    recommendation: str
    supporting_data: Dict[str, Any]
    created_at: str

class AIAnalysisOptimizer:
    """AI分析優化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 依賴組件
        self.model_selector = SmartModelSelector()
        self.cost_optimizer = LLMCostOptimizer()
        
        # 實驗管理
        self.active_experiments: Dict[str, ABTestExperiment] = {}
        self.experiment_assignments: Dict[str, str] = {}  # user_session -> variant
        
        # 品質追蹤
        self.quality_ratings: List[AnalysisQualityRating] = []
        self.quality_baselines: Dict[str, float] = {}
        
        # 優化建議
        self.optimization_insights: List[OptimizationInsight] = []
        
        # 配置
        self.auto_optimization_enabled = True
        self.min_confidence_for_action = 0.8
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def create_experiment(
        self,
        name: str,
        description: str,
        test_type: TestType,
        dimension: OptimizationDimension,
        control_config: Dict[str, Any],
        treatment_config: Dict[str, Any],
        target_metrics: List[QualityMetric],
        duration_days: int = 14,
        traffic_allocation: float = 0.5,
        min_sample_size: int = 100
    ) -> str:
        """創建A/B測試實驗"""
        
        experiment_id = f"exp_{int(time.time())}_{secrets.randbelow(8999) + 1000}"  # 安全修復：使用secrets替換random
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
        
        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            test_type=test_type,
            optimization_dimension=dimension,
            control_variant=control_config,
            treatment_variant=treatment_config,
            target_metrics=target_metrics,
            traffic_allocation=traffic_allocation,
            start_date=start_date,
            end_date=end_date,
            minimum_sample_size=min_sample_size
        )
        
        self.active_experiments[experiment_id] = experiment
        
        self.logger.info(f"創建實驗: {name} (ID: {experiment_id})")
        
        return experiment_id
    
    async def get_experiment_variant(
        self,
        user_session_id: str,
        task_type: str,
        user_context: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """獲取實驗變體配置"""
        
        # 查找適用的實驗
        applicable_experiments = []
        
        for exp_id, experiment in self.active_experiments.items():
            if (experiment.is_active and 
                self._is_experiment_applicable(experiment, task_type, user_context)):
                applicable_experiments.append((exp_id, experiment))
        
        if not applicable_experiments:
            return "baseline", {}
        
        # 選擇優先級最高的實驗（這裡簡化為第一個）
        exp_id, experiment = applicable_experiments[0]
        
        # 檢查用戶分配
        assignment_key = f"{user_session_id}_{exp_id}"
        
        if assignment_key not in self.experiment_assignments:
            # 新用戶，進行分配
            is_treatment = (secrets.randbelow(10000) / 10000.0) < experiment.traffic_allocation  # 安全修復：使用secrets替換random
            self.experiment_assignments[assignment_key] = "treatment" if is_treatment else "control"
        
        variant_type = self.experiment_assignments[assignment_key]
        
        if variant_type == "treatment":
            return exp_id, experiment.treatment_variant
        else:
            return exp_id, experiment.control_variant
    
    def _is_experiment_applicable(
        self, 
        experiment: ABTestExperiment, 
        task_type: str, 
        user_context: Dict[str, Any]
    ) -> bool:
        """檢查實驗是否適用"""
        
        # 檢查時間範圍
        current_date = datetime.now().strftime('%Y-%m-%d')
        if not (experiment.start_date <= current_date <= experiment.end_date):
            return False
        
        # 檢查任務類型匹配（簡化實現）
        task_filter = experiment.control_variant.get('task_types')
        if task_filter and task_type not in task_filter:
            return False
        
        # 檢查用戶條件（簡化實現）
        user_filter = experiment.control_variant.get('user_conditions')
        if user_filter:
            membership_tier = user_context.get('membership_tier', 'FREE')
            if 'required_tier' in user_filter and membership_tier not in user_filter['required_tier']:
                return False
        
        return True
    
    async def record_analysis_quality(
        self,
        analysis_id: str,
        user_id: str,
        task_type: str,
        model_used: str,
        quality_scores: Dict[str, float],
        overall_score: float,
        feedback_text: Optional[str] = None,
        experiment_context: Optional[Dict[str, Any]] = None
    ):
        """記錄分析品質評分"""
        
        # 轉換品質分數格式
        quality_metric_scores = {}
        for metric_name, score in quality_scores.items():
            try:
                metric = QualityMetric(metric_name)
                quality_metric_scores[metric] = score
            except ValueError:
                self.logger.warning(f"未知品質指標: {metric_name}")
        
        # 確定實驗上下文
        experiment_id = None
        variant_type = "baseline"
        
        if experiment_context:
            experiment_id = experiment_context.get('experiment_id')
            variant_type = experiment_context.get('variant_type', 'baseline')
        
        # 創建品質評分記錄
        quality_rating = AnalysisQualityRating(
            analysis_id=analysis_id,
            user_id=user_id,
            experiment_id=experiment_id,
            variant_type=variant_type,
            quality_scores=quality_metric_scores,
            overall_score=overall_score,
            feedback_text=feedback_text,
            rating_timestamp=datetime.now().isoformat(),
            task_type=task_type,
            model_used=model_used
        )
        
        self.quality_ratings.append(quality_rating)
        
        # 觸發自動優化檢查
        if self.auto_optimization_enabled:
            await self._check_auto_optimization_triggers(quality_rating)
        
        self.logger.info(f"記錄品質評分: {analysis_id} - 總分: {overall_score:.2f}")
    
    async def _check_auto_optimization_triggers(self, new_rating: AnalysisQualityRating):
        """檢查自動優化觸發條件"""
        
        # 檢查品質下降
        task_type = new_rating.task_type
        recent_scores = [
            r.overall_score for r in self.quality_ratings[-50:]
            if r.task_type == task_type and r.experiment_id is None  # 只看基線數據
        ]
        
        if len(recent_scores) >= 10:
            recent_avg = statistics.mean(recent_scores[-10:])
            baseline_avg = self.quality_baselines.get(task_type, recent_avg)
            
            # 如果品質下降超過10%，觸發優化
            if recent_avg < baseline_avg * 0.9:
                await self._trigger_quality_improvement_experiment(task_type, baseline_avg, recent_avg)
    
    async def _trigger_quality_improvement_experiment(
        self, 
        task_type: str, 
        baseline_score: float, 
        current_score: float
    ):
        """觸發品質改善實驗"""
        
        self.logger.warning(f"檢測到品質下降: {task_type} - {baseline_score:.2f} -> {current_score:.2f}")
        
        # 自動創建改善實驗
        if task_type not in [exp.control_variant.get('task_types', []) for exp in self.active_experiments.values()]:
            
            # 創建模型升級實驗
            exp_id = self.create_experiment(
                name=f"Quality Recovery - {task_type}",
                description=f"自動觸發的品質改善實驗，目標恢復 {task_type} 分析品質",
                test_type=TestType.MODEL_COMPARISON,
                dimension=OptimizationDimension.MODEL_SELECTION,
                control_config={
                    "task_types": [task_type],
                    "model_strategy": "current_default"
                },
                treatment_config={
                    "task_types": [task_type],
                    "model_strategy": "quality_first"
                },
                target_metrics=[QualityMetric.ACCURACY, QualityMetric.OVERALL_QUALITY],
                duration_days=7,
                traffic_allocation=0.2,  # 保守的20%流量
                min_sample_size=30
            )
            
            self.logger.info(f"自動創建品質改善實驗: {exp_id}")
    
    def analyze_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """分析實驗結果"""
        
        if experiment_id not in self.active_experiments:
            return None
        
        experiment = self.active_experiments[experiment_id]
        
        # 收集實驗數據
        control_ratings = [
            r for r in self.quality_ratings
            if r.experiment_id == experiment_id and r.variant_type == "control"
        ]
        
        treatment_ratings = [
            r for r in self.quality_ratings
            if r.experiment_id == experiment_id and r.variant_type == "treatment"
        ]
        
        if not control_ratings or not treatment_ratings:
            return {
                "status": "insufficient_data",
                "control_samples": len(control_ratings),
                "treatment_samples": len(treatment_ratings),
                "minimum_required": experiment.minimum_sample_size
            }
        
        # 計算統計結果
        results = {}
        
        for metric in experiment.target_metrics:
            control_scores = [r.quality_scores.get(metric, 0) for r in control_ratings if metric in r.quality_scores]
            treatment_scores = [r.quality_scores.get(metric, 0) for r in treatment_ratings if metric in r.quality_scores]
            
            if control_scores and treatment_scores:
                control_mean = statistics.mean(control_scores)
                treatment_mean = statistics.mean(treatment_scores)
                
                # 簡化的統計檢驗
                improvement = (treatment_mean - control_mean) / control_mean if control_mean > 0 else 0
                
                # 基於樣本大小和效果量的簡化信心度計算
                min_samples = min(len(control_scores), len(treatment_scores))
                effect_size = abs(improvement)
                confidence = min(0.99, effect_size * min_samples / 50)
                
                results[metric.value] = {
                    "control_mean": control_mean,
                    "treatment_mean": treatment_mean,
                    "improvement_percent": improvement * 100,
                    "confidence": confidence,
                    "significant": confidence > (1 - experiment.significance_threshold),
                    "control_samples": len(control_scores),
                    "treatment_samples": len(treatment_scores)
                }
        
        # 整體分析評分
        control_overall = [r.overall_score for r in control_ratings]
        treatment_overall = [r.overall_score for r in treatment_ratings]
        
        overall_analysis = {
            "control_mean": statistics.mean(control_overall),
            "treatment_mean": statistics.mean(treatment_overall),
            "improvement_percent": ((statistics.mean(treatment_overall) - statistics.mean(control_overall)) / statistics.mean(control_overall)) * 100,
            "control_samples": len(control_overall),
            "treatment_samples": len(treatment_overall)
        }
        
        # 決策建議
        significant_improvements = sum(
            1 for metric_result in results.values()
            if metric_result.get("significant", False) and metric_result.get("improvement_percent", 0) > 0
        )
        
        if significant_improvements >= len(experiment.target_metrics) / 2:
            recommendation = "adopt_treatment"
        elif any(r.get("improvement_percent", 0) < -5 for r in results.values()):
            recommendation = "reject_treatment"
        else:
            recommendation = "continue_testing"
        
        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "status": "analysis_complete",
            "metric_results": results,
            "overall_analysis": overall_analysis,
            "recommendation": recommendation,
            "confidence_level": statistics.mean([r.get("confidence", 0) for r in results.values()]) if results else 0,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    async def generate_optimization_insights(self, days: int = 30) -> List[OptimizationInsight]:
        """生成優化洞察"""
        
        insights = []
        
        # 分析最近的品質數據
        recent_cutoff = datetime.now() - timedelta(days=days)
        recent_ratings = [
            r for r in self.quality_ratings
            if datetime.fromisoformat(r.rating_timestamp) >= recent_cutoff
        ]
        
        if not recent_ratings:
            return insights
        
        # 1. 模型性能洞察
        model_insights = await self._analyze_model_performance(recent_ratings)
        insights.extend(model_insights)
        
        # 2. 任務類型洞察
        task_insights = await self._analyze_task_performance(recent_ratings)
        insights.extend(task_insights)
        
        # 3. 用戶滿意度洞察
        satisfaction_insights = await self._analyze_user_satisfaction(recent_ratings)
        insights.extend(satisfaction_insights)
        
        # 4. 成本效益洞察
        cost_insights = await self._analyze_cost_effectiveness(recent_ratings)
        insights.extend(cost_insights)
        
        # 保存洞察
        self.optimization_insights.extend(insights)
        
        return insights
    
    async def _analyze_model_performance(self, ratings: List[AnalysisQualityRating]) -> List[OptimizationInsight]:
        """分析模型性能"""
        insights = []
        
        # 按模型分組分析
        model_performance = {}
        for rating in ratings:
            model = rating.model_used
            if model not in model_performance:
                model_performance[model] = {
                    "scores": [],
                    "count": 0
                }
            
            model_performance[model]["scores"].append(rating.overall_score)
            model_performance[model]["count"] += 1
        
        # 找出表現最好和最差的模型
        model_averages = {
            model: statistics.mean(data["scores"])
            for model, data in model_performance.items()
            if data["count"] >= 5  # 至少5個樣本
        }
        
        if len(model_averages) >= 2:
            best_model = max(model_averages, key=model_averages.get)
            worst_model = min(model_averages, key=model_averages.get)
            
            performance_gap = model_averages[best_model] - model_averages[worst_model]
            
            if performance_gap > 1.0:  # 顯著差異
                insights.append(OptimizationInsight(
                    insight_id=f"model_perf_{int(time.time())}",
                    dimension=OptimizationDimension.MODEL_SELECTION,
                    title=f"模型性能差異顯著",
                    description=f"{best_model} 比 {worst_model} 表現好 {performance_gap:.1f} 分",
                    confidence_level=0.8,
                    potential_improvement=performance_gap / 10.0,  # 轉換為百分比
                    recommendation=f"考慮更多使用 {best_model} 模型",
                    supporting_data={
                        "best_model": best_model,
                        "best_score": model_averages[best_model],
                        "worst_model": worst_model,
                        "worst_score": model_averages[worst_model],
                        "performance_gap": performance_gap
                    },
                    created_at=datetime.now().isoformat()
                ))
        
        return insights
    
    async def _analyze_task_performance(self, ratings: List[AnalysisQualityRating]) -> List[OptimizationInsight]:
        """分析任務性能"""
        insights = []
        
        # 按任務類型分析
        task_performance = {}
        for rating in ratings:
            task_type = rating.task_type
            if task_type not in task_performance:
                task_performance[task_type] = []
            task_performance[task_type].append(rating.overall_score)
        
        # 找出需要改善的任務類型
        for task_type, scores in task_performance.items():
            if len(scores) >= 10:  # 足夠樣本
                avg_score = statistics.mean(scores)
                if avg_score < 7.0:  # 低於7分需要改善
                    insights.append(OptimizationInsight(
                        insight_id=f"task_perf_{task_type}_{int(time.time())}",
                        dimension=OptimizationDimension.ANALYSIS_DEPTH,
                        title=f"{task_type} 分析品質需要改善",
                        description=f"{task_type} 平均評分僅 {avg_score:.1f}，低於期望水準",
                        confidence_level=0.7,
                        potential_improvement=(8.0 - avg_score) / 10.0,
                        recommendation=f"針對 {task_type} 優化分析流程和提示詞",
                        supporting_data={
                            "task_type": task_type,
                            "current_score": avg_score,
                            "target_score": 8.0,
                            "sample_size": len(scores)
                        },
                        created_at=datetime.now().isoformat()
                    ))
        
        return insights
    
    async def _analyze_user_satisfaction(self, ratings: List[AnalysisQualityRating]) -> List[OptimizationInsight]:
        """分析用戶滿意度"""
        insights = []
        
        # 分析滿意度趨勢
        satisfaction_scores = [
            r.quality_scores.get(QualityMetric.USER_SATISFACTION, r.overall_score)
            for r in ratings
            if QualityMetric.USER_SATISFACTION in r.quality_scores or r.overall_score > 0
        ]
        
        if len(satisfaction_scores) >= 20:
            recent_satisfaction = statistics.mean(satisfaction_scores[-10:])
            overall_satisfaction = statistics.mean(satisfaction_scores)
            
            if recent_satisfaction < overall_satisfaction * 0.9:
                insights.append(OptimizationInsight(
                    insight_id=f"satisfaction_trend_{int(time.time())}",
                    dimension=OptimizationDimension.RESPONSE_FORMAT,
                    title="用戶滿意度呈下降趨勢",
                    description=f"最近滿意度 {recent_satisfaction:.1f} 低於整體平均 {overall_satisfaction:.1f}",
                    confidence_level=0.6,
                    potential_improvement=(overall_satisfaction - recent_satisfaction) / 10.0,
                    recommendation="檢查回應格式和內容質量，可能需要調整輸出模板",
                    supporting_data={
                        "recent_satisfaction": recent_satisfaction,
                        "overall_satisfaction": overall_satisfaction,
                        "sample_size": len(satisfaction_scores)
                    },
                    created_at=datetime.now().isoformat()
                ))
        
        return insights
    
    async def _analyze_cost_effectiveness(self, ratings: List[AnalysisQualityRating]) -> List[OptimizationInsight]:
        """分析成本效益"""
        insights = []
        
        # 獲取成本數據
        cost_data = await self.cost_optimizer.get_cost_analytics(days=30)
        
        if cost_data.get("total_requests", 0) > 0:
            avg_cost = cost_data.get("average_cost_per_request", 0)
            avg_quality = statistics.mean([r.overall_score for r in ratings]) if ratings else 0
            
            # 成本效益評分
            cost_effectiveness = avg_quality / max(avg_cost * 1000, 0.001)  # 品質/千分之成本
            
            if cost_effectiveness < 500:  # 經驗閾值
                insights.append(OptimizationInsight(
                    insight_id=f"cost_effectiveness_{int(time.time())}",
                    dimension=OptimizationDimension.MODEL_SELECTION,
                    title="成本效益有改善空間",
                    description=f"當前成本效益評分 {cost_effectiveness:.0f}，可考慮優化模型選擇",
                    confidence_level=0.5,
                    potential_improvement=0.2,
                    recommendation="考慮使用更經濟的模型進行簡單分析任務",
                    supporting_data={
                        "cost_effectiveness_score": cost_effectiveness,
                        "avg_cost": avg_cost,
                        "avg_quality": avg_quality
                    },
                    created_at=datetime.now().isoformat()
                ))
        
        return insights
    
    def get_optimization_dashboard(self) -> Dict[str, Any]:
        """獲取優化儀表板數據"""
        
        # 活躍實驗統計
        active_count = len([exp for exp in self.active_experiments.values() if exp.is_active])
        
        # 最近品質趨勢
        recent_ratings = self.quality_ratings[-100:] if self.quality_ratings else []
        
        quality_trend = []
        if recent_ratings:
            # 按週計算平均品質
            for i in range(4):  # 最近4週
                week_start = datetime.now() - timedelta(weeks=i+1)
                week_end = datetime.now() - timedelta(weeks=i)
                
                week_ratings = [
                    r for r in recent_ratings
                    if week_start <= datetime.fromisoformat(r.rating_timestamp) < week_end
                ]
                
                if week_ratings:
                    week_avg = statistics.mean([r.overall_score for r in week_ratings])
                    quality_trend.append({
                        "week": f"Week {4-i}",
                        "avg_quality": week_avg,
                        "sample_size": len(week_ratings)
                    })
        
        # 實驗結果摘要
        experiment_results = []
        for exp_id in list(self.active_experiments.keys())[-5:]:  # 最近5個實驗
            result = self.analyze_experiment_results(exp_id)
            if result and result.get("status") != "insufficient_data":
                experiment_results.append({
                    "experiment_id": exp_id,
                    "name": self.active_experiments[exp_id].name,
                    "recommendation": result.get("recommendation"),
                    "confidence": result.get("confidence_level", 0)
                })
        
        # 優化洞察摘要
        recent_insights = self.optimization_insights[-10:] if self.optimization_insights else []
        
        return {
            "summary": {
                "active_experiments": active_count,
                "total_quality_ratings": len(self.quality_ratings),
                "avg_quality_last_week": statistics.mean([
                    r.overall_score for r in recent_ratings[-50:]
                ]) if recent_ratings else 0,
                "optimization_insights": len(recent_insights)
            },
            "quality_trend": quality_trend,
            "experiment_results": experiment_results,
            "recent_insights": [asdict(insight) for insight in recent_insights],
            "timestamp": datetime.now().isoformat()
        }

# 便利函數
async def create_model_comparison_experiment(
    model_a: str,
    model_b: str,
    task_types: List[str],
    duration_days: int = 14
) -> str:
    """創建模型對比實驗"""
    
    optimizer = AIAnalysisOptimizer()
    
    return optimizer.create_experiment(
        name=f"Model Comparison: {model_a} vs {model_b}",
        description=f"比較 {model_a} 和 {model_b} 在 {', '.join(task_types)} 任務上的表現",
        test_type=TestType.MODEL_COMPARISON,
        dimension=OptimizationDimension.MODEL_SELECTION,
        control_config={
            "model_name": model_a,
            "task_types": task_types
        },
        treatment_config={
            "model_name": model_b,
            "task_types": task_types
        },
        target_metrics=[QualityMetric.ACCURACY, QualityMetric.USER_SATISFACTION],
        duration_days=duration_days
    )

async def get_analysis_optimization_recommendations(task_type: str) -> List[Dict[str, Any]]:
    """獲取分析優化建議"""
    
    optimizer = AIAnalysisOptimizer()
    insights = await optimizer.generate_optimization_insights(days=30)
    
    # 過濾相關建議
    relevant_insights = [
        insight for insight in insights
        if task_type in insight.supporting_data.get("task_type", "")
    ]
    
    return [asdict(insight) for insight in relevant_insights]

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_ai_optimizer():
        print("🔬 測試AI分析優化器")
        
        optimizer = AIAnalysisOptimizer()
        
        # 創建測試實驗
        exp_id = optimizer.create_experiment(
            name="測試實驗",
            description="GPT-4 vs Gemini Pro 技術分析對比",
            test_type=TestType.MODEL_COMPARISON,
            dimension=OptimizationDimension.MODEL_SELECTION,
            control_config={"model_name": "gpt-4"},
            treatment_config={"model_name": "gemini-pro"},
            target_metrics=[QualityMetric.ACCURACY, QualityMetric.USER_SATISFACTION],
            duration_days=7
        )
        
        print(f"創建實驗: {exp_id}")
        
        # 模擬品質評分
        await optimizer.record_analysis_quality(
            analysis_id="test_001",
            user_id="test_user",
            task_type="technical_analysis",
            model_used="gpt-4",
            quality_scores={"accuracy": 8.5, "user_satisfaction": 7.8},
            overall_score=8.2,
            experiment_context={"experiment_id": exp_id, "variant_type": "control"}
        )
        
        # 生成優化洞察
        insights = await optimizer.generate_optimization_insights(days=7)
        print(f"生成洞察: {len(insights)} 個")
        
        # 獲取儀表板
        dashboard = optimizer.get_optimization_dashboard()
        print(f"活躍實驗: {dashboard['summary']['active_experiments']}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_ai_optimizer())