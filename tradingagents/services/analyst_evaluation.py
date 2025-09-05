#!/usr/bin/env python3
"""
Analyst Evaluation - 分析師能力評估和獎勵機制
天工 (TianGong) - 智能分析師性能評估與強化學習獎勵系統

此模組提供：
1. 多維度分析師能力評估
2. 市場後驗證獎勵機制
3. 用戶反饋整合
4. 適應性獎勵函數
5. 分析師排名和選擇優化
"""

import asyncio
import logging
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Callable
import json
import math
from collections import defaultdict, deque

from ..agents.analysts.base_analyst import AnalysisResult, AnalysisType, AnalysisConfidenceLevel


class EvaluationMetric(Enum):
    """評估指標類型"""
    ACCURACY = "accuracy"                    # 準確性
    PRECISION = "precision"                  # 精確度
    RECALL = "recall"                       # 召回率
    F1_SCORE = "f1_score"                   # F1分數
    CONFIDENCE_CALIBRATION = "conf_calibration"  # 信心度校準
    MARKET_TIMING = "market_timing"         # 市場時機
    RISK_ASSESSMENT = "risk_assessment"     # 風險評估
    COST_EFFICIENCY = "cost_efficiency"     # 成本效益
    RESPONSE_TIME = "response_time"         # 響應時間
    USER_SATISFACTION = "user_satisfaction" # 用戶滿意度


class RewardComponent(Enum):
    """獎勵組件"""
    BASE_PERFORMANCE = "base_performance"    # 基礎性能
    MARKET_VALIDATION = "market_validation"  # 市場驗證
    USER_FEEDBACK = "user_feedback"         # 用戶反饋
    TIMING_BONUS = "timing_bonus"           # 時機獎勵
    CONSISTENCY_BONUS = "consistency_bonus"  # 一致性獎勵
    INNOVATION_BONUS = "innovation_bonus"    # 創新獎勵
    EFFICIENCY_PENALTY = "efficiency_penalty" # 效率懲罰
    RISK_PENALTY = "risk_penalty"           # 風險懲罰


@dataclass
class MarketValidation:
    """市場驗證數據"""
    analyst_id: str
    stock_id: str
    prediction_date: datetime
    validation_date: datetime
    
    # 預測數據
    predicted_direction: str  # BUY, SELL, HOLD
    predicted_confidence: float
    predicted_target_price: Optional[float] = None
    
    # 實際市場數據
    actual_price_change: float  # 價格變化百分比
    actual_direction: str       # 實際方向
    market_return: float        # 市場整體回報
    
    # 驗證期間
    validation_period_days: int = 30
    
    # 計算結果
    direction_correct: bool = field(init=False)
    price_accuracy: float = field(init=False)
    relative_performance: float = field(init=False)
    
    def __post_init__(self):
        # 計算方向正確性
        self.direction_correct = self._calculate_direction_correctness()
        
        # 計算價格準確性
        self.price_accuracy = self._calculate_price_accuracy()
        
        # 計算相對市場表現
        self.relative_performance = self.actual_price_change - self.market_return
    
    def _calculate_direction_correctness(self) -> bool:
        """計算方向正確性"""
        
        # 簡化的方向判斷邏輯
        if self.predicted_direction == "BUY" and self.actual_price_change > 0.02:  # >2%
            return True
        elif self.predicted_direction == "SELL" and self.actual_price_change < -0.02:  # <-2%
            return True
        elif self.predicted_direction == "HOLD" and abs(self.actual_price_change) <= 0.02:  # ±2%
            return True
        
        return False
    
    def _calculate_price_accuracy(self) -> float:
        """計算價格準確性"""
        
        if self.predicted_target_price is None:
            return 0.5  # 中性分數
        
        # 計算價格預測準確性（1 - 相對誤差）
        if self.predicted_target_price > 0:
            relative_error = abs(self.actual_price_change - 
                               (self.predicted_target_price - 100) / 100) / 100
            accuracy = max(0.0, 1.0 - relative_error)
        else:
            accuracy = 0.0
        
        return min(1.0, accuracy)


@dataclass
class UserFeedback:
    """用戶反饋數據"""
    analyst_id: str
    stock_id: str
    feedback_date: datetime
    user_id: str
    
    # 反饋分數
    overall_rating: float       # 1-5 分
    usefulness_rating: float    # 1-5 分
    clarity_rating: float       # 1-5 分
    actionability_rating: float # 1-5 分
    
    # 文本反饋
    comments: Optional[str] = None
    
    # 行為數據
    followed_recommendation: bool = False
    time_spent_reading: float = 0.0  # 秒
    shared_analysis: bool = False
    
    def get_normalized_rating(self) -> float:
        """獲取歸一化評分 (0-1)"""
        return (self.overall_rating - 1) / 4


@dataclass
class AnalystEvaluation:
    """分析師評估結果"""
    analyst_id: str
    evaluation_date: datetime
    evaluation_period: timedelta
    
    # 核心指標
    metrics: Dict[EvaluationMetric, float] = field(default_factory=dict)
    
    # 獎勵組件
    reward_components: Dict[RewardComponent, float] = field(default_factory=dict)
    
    # 總分
    total_reward: float = 0.0
    normalized_score: float = 0.0  # 0-100分
    
    # 統計數據
    total_analyses: int = 0
    market_validations: int = 0
    user_feedbacks: int = 0
    
    # 改進建議
    improvement_suggestions: List[str] = field(default_factory=list)
    
    def get_grade(self) -> str:
        """獲取評級"""
        if self.normalized_score >= 90:
            return "A+"
        elif self.normalized_score >= 85:
            return "A"
        elif self.normalized_score >= 80:
            return "A-"
        elif self.normalized_score >= 75:
            return "B+"
        elif self.normalized_score >= 70:
            return "B"
        elif self.normalized_score >= 65:
            return "B-"
        elif self.normalized_score >= 60:
            return "C+"
        elif self.normalized_score >= 55:
            return "C"
        elif self.normalized_score >= 50:
            return "C-"
        else:
            return "D"


class MarketValidator:
    """市場驗證器"""
    
    def __init__(self, data_source):
        self.data_source = data_source
        self.logger = logging.getLogger(__name__)
    
    async def validate_prediction(
        self, 
        analysis_result: AnalysisResult,
        validation_period_days: int = 30
    ) -> Optional[MarketValidation]:
        """驗證預測結果"""
        
        try:
            # 獲取預測時間點的價格
            prediction_date = datetime.fromisoformat(analysis_result.analysis_date)
            validation_date = prediction_date + timedelta(days=validation_period_days)
            
            # 獲取市場數據
            market_data = await self._get_market_data(
                analysis_result.stock_id,
                prediction_date,
                validation_date
            )
            
            if not market_data:
                return None
            
            # 創建驗證對象
            validation = MarketValidation(
                analyst_id=analysis_result.analyst_id,
                stock_id=analysis_result.stock_id,
                prediction_date=prediction_date,
                validation_date=validation_date,
                predicted_direction=analysis_result.recommendation,
                predicted_confidence=analysis_result.confidence,
                predicted_target_price=analysis_result.target_price,
                actual_price_change=market_data['price_change'],
                actual_direction=market_data['direction'],
                market_return=market_data['market_return'],
                validation_period_days=validation_period_days
            )
            
            return validation
            
        except Exception as e:
            self.logger.error(f"市場驗證失敗: {str(e)}")
            return None
    
    async def _get_market_data(
        self, 
        stock_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[Dict[str, Any]]:
        """獲取市場數據"""
        
        try:
            # 這裡應該調用實際的數據源
            # 目前提供模擬數據
            
            # 模擬價格變化
            import random
            price_change = (random.random() - 0.5) * 0.2  # ±10%的變化
            market_return = (random.random() - 0.5) * 0.1  # ±5%的市場回報
            
            direction = "BUY" if price_change > 0.02 else "SELL" if price_change < -0.02 else "HOLD"
            
            return {
                'price_change': price_change,
                'direction': direction,
                'market_return': market_return,
                'start_price': 100.0,
                'end_price': 100.0 * (1 + price_change)
            }
            
        except Exception as e:
            self.logger.error(f"獲取市場數據失敗: {str(e)}")
            return None


class RewardFunction:
    """獎勵函數"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 獎勵權重配置
        self.component_weights = self.config.get('component_weights', {
            RewardComponent.BASE_PERFORMANCE: 0.3,
            RewardComponent.MARKET_VALIDATION: 0.4,
            RewardComponent.USER_FEEDBACK: 0.2,
            RewardComponent.TIMING_BONUS: 0.05,
            RewardComponent.CONSISTENCY_BONUS: 0.05,
            RewardComponent.EFFICIENCY_PENALTY: -0.1,
            RewardComponent.RISK_PENALTY: -0.1
        })
    
    def calculate_reward(
        self,
        analysis_result: AnalysisResult,
        market_validation: Optional[MarketValidation] = None,
        user_feedback: Optional[UserFeedback] = None,
        historical_performance: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[RewardComponent, float]]:
        """計算獎勵分數"""
        
        reward_components = {}
        
        # 1. 基礎性能獎勵
        reward_components[RewardComponent.BASE_PERFORMANCE] = self._calculate_base_performance(
            analysis_result
        )
        
        # 2. 市場驗證獎勵
        if market_validation:
            reward_components[RewardComponent.MARKET_VALIDATION] = self._calculate_market_validation_reward(
                market_validation
            )
        else:
            reward_components[RewardComponent.MARKET_VALIDATION] = 0.0
        
        # 3. 用戶反饋獎勵
        if user_feedback:
            reward_components[RewardComponent.USER_FEEDBACK] = self._calculate_user_feedback_reward(
                user_feedback
            )
        else:
            reward_components[RewardComponent.USER_FEEDBACK] = 0.0
        
        # 4. 時機獎勵
        reward_components[RewardComponent.TIMING_BONUS] = self._calculate_timing_bonus(
            analysis_result, market_validation
        )
        
        # 5. 一致性獎勵
        if historical_performance:
            reward_components[RewardComponent.CONSISTENCY_BONUS] = self._calculate_consistency_bonus(
                analysis_result, historical_performance
            )
        else:
            reward_components[RewardComponent.CONSISTENCY_BONUS] = 0.0
        
        # 6. 效率懲罰
        reward_components[RewardComponent.EFFICIENCY_PENALTY] = self._calculate_efficiency_penalty(
            analysis_result
        )
        
        # 7. 風險懲罰
        reward_components[RewardComponent.RISK_PENALTY] = self._calculate_risk_penalty(
            analysis_result, market_validation
        )
        
        # 計算總獎勵
        total_reward = 0.0
        for component, score in reward_components.items():
            weight = self.component_weights.get(component, 0.0)
            total_reward += score * weight
        
        # 確保獎勵在合理範圍內
        total_reward = max(-1.0, min(1.0, total_reward))
        
        return total_reward, reward_components
    
    def _calculate_base_performance(self, analysis_result: AnalysisResult) -> float:
        """計算基礎性能分數"""
        
        score = 0.0
        
        # 信心度貢獻
        confidence_score = analysis_result.confidence
        score += confidence_score * 0.4
        
        # 推理品質（基於推理條數和內容）
        reasoning_quality = 0.5  # 預設值
        if analysis_result.reasoning:
            reasoning_count = len(analysis_result.reasoning)
            reasoning_quality = min(1.0, reasoning_count / 5.0)  # 最多5條推理
        
        score += reasoning_quality * 0.3
        
        # 技術指標完整性
        if analysis_result.technical_indicators:
            indicator_completeness = min(1.0, len(analysis_result.technical_indicators) / 5.0)
            score += indicator_completeness * 0.15
        
        # 基本面指標完整性
        if analysis_result.fundamental_metrics:
            metrics_completeness = min(1.0, len(analysis_result.fundamental_metrics) / 5.0)
            score += metrics_completeness * 0.15
        
        return max(0.0, min(1.0, score))
    
    def _calculate_market_validation_reward(self, validation: MarketValidation) -> float:
        """計算市場驗證獎勵"""
        
        score = 0.0
        
        # 方向正確性獎勵
        if validation.direction_correct:
            score += 0.6
        
        # 價格準確性獎勵
        score += validation.price_accuracy * 0.3
        
        # 相對市場表現獎勵
        relative_performance = validation.relative_performance
        if relative_performance > 0.05:  # 超越市場5%
            score += 0.2
        elif relative_performance > 0.02:  # 超越市場2%
            score += 0.1
        elif relative_performance < -0.05:  # 落後市場5%
            score -= 0.2
        
        # 信心度校準獎勵
        confidence_calibration = self._calculate_confidence_calibration(
            validation.predicted_confidence,
            validation.direction_correct,
            validation.price_accuracy
        )
        score += confidence_calibration * 0.1
        
        return max(0.0, min(1.0, score))
    
    def _calculate_confidence_calibration(
        self, 
        predicted_confidence: float, 
        direction_correct: bool, 
        price_accuracy: float
    ) -> float:
        """計算信心度校準分數"""
        
        # 實際準確性
        actual_accuracy = (1.0 if direction_correct else 0.0) * 0.7 + price_accuracy * 0.3
        
        # 信心度校準誤差
        calibration_error = abs(predicted_confidence - actual_accuracy)
        
        # 校準分數（誤差越小分數越高）
        calibration_score = max(0.0, 1.0 - calibration_error * 2)
        
        return calibration_score
    
    def _calculate_user_feedback_reward(self, feedback: UserFeedback) -> float:
        """計算用戶反饋獎勵"""
        
        score = 0.0
        
        # 整體評分
        overall_score = feedback.get_normalized_rating()
        score += overall_score * 0.6
        
        # 各項評分的平均
        detail_ratings = [
            feedback.usefulness_rating,
            feedback.clarity_rating,
            feedback.actionability_rating
        ]
        avg_detail_rating = sum(detail_ratings) / len(detail_ratings)
        detail_score = (avg_detail_rating - 1) / 4  # 歸一化到0-1
        score += detail_score * 0.3
        
        # 行為獎勵
        if feedback.followed_recommendation:
            score += 0.1
        
        if feedback.shared_analysis:
            score += 0.05
        
        # 閱讀時間獎勵（適度時間最佳）
        if 30 <= feedback.time_spent_reading <= 300:  # 30秒到5分鐘
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _calculate_timing_bonus(
        self, 
        analysis_result: AnalysisResult, 
        market_validation: Optional[MarketValidation]
    ) -> float:
        """計算時機獎勵"""
        
        if not market_validation:
            return 0.0
        
        # 基於市場驗證期間的波動性給予時機獎勵
        price_change = abs(market_validation.actual_price_change)
        
        if price_change > 0.1:  # 大幅波動期間的正確預測
            return 0.3
        elif price_change > 0.05:  # 中等波動
            return 0.2
        elif price_change > 0.02:  # 小幅波動
            return 0.1
        else:
            return 0.0
    
    def _calculate_consistency_bonus(
        self, 
        analysis_result: AnalysisResult, 
        historical_performance: Dict[str, Any]
    ) -> float:
        """計算一致性獎勵"""
        
        try:
            # 歷史準確率
            historical_accuracy = historical_performance.get('accuracy_rate', 0.5)
            
            # 歷史信心度標準差（越小越一致）
            confidence_std = historical_performance.get('confidence_std', 0.5)
            
            # 一致性分數
            consistency_score = historical_accuracy * 0.7 + (1 - confidence_std) * 0.3
            
            return max(0.0, min(1.0, consistency_score))
            
        except Exception:
            return 0.0
    
    def _calculate_efficiency_penalty(self, analysis_result: AnalysisResult) -> float:
        """計算效率懲罰"""
        
        penalty = 0.0
        
        # 成本懲罰
        if analysis_result.cost_info:
            cost = analysis_result.cost_info.get('estimated_cost', 0.0)
            if cost > 0.1:  # 高成本懲罰
                penalty -= 0.3
            elif cost > 0.05:  # 中等成本懲罰
                penalty -= 0.15
        
        return penalty
    
    def _calculate_risk_penalty(
        self, 
        analysis_result: AnalysisResult, 
        market_validation: Optional[MarketValidation]
    ) -> float:
        """計算風險懲罰"""
        
        penalty = 0.0
        
        # 高信心度但錯誤預測的懲罰
        if (market_validation and 
            analysis_result.confidence > 0.8 and 
            not market_validation.direction_correct):
            penalty -= 0.5
        
        # 風險因子懲罰（如果有提供風險評估但仍然出錯）
        if (analysis_result.risk_factors and 
            market_validation and 
            not market_validation.direction_correct):
            penalty -= 0.2
        
        return penalty


class AnalystEvaluator:
    """分析師評估器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 組件
        self.market_validator = MarketValidator(self.config.get('data_source'))
        self.reward_function = RewardFunction(self.config.get('reward_config'))
        
        # 數據存儲
        self.market_validations: Dict[str, List[MarketValidation]] = defaultdict(list)
        self.user_feedbacks: Dict[str, List[UserFeedback]] = defaultdict(list)
        self.historical_evaluations: Dict[str, List[AnalystEvaluation]] = defaultdict(list)
    
    async def evaluate_analyst(
        self, 
        analyst_id: str,
        evaluation_period: timedelta = timedelta(days=30)
    ) -> AnalystEvaluation:
        """評估分析師"""
        
        try:
            evaluation_date = datetime.now()
            start_date = evaluation_date - evaluation_period
            
            # 收集評估期間的數據
            period_validations = self._get_validations_in_period(
                analyst_id, start_date, evaluation_date
            )
            period_feedbacks = self._get_feedbacks_in_period(
                analyst_id, start_date, evaluation_date
            )
            
            # 計算各項指標
            metrics = await self._calculate_metrics(
                analyst_id, period_validations, period_feedbacks
            )
            
            # 計算獎勵組件
            reward_components = await self._calculate_reward_components(
                analyst_id, period_validations, period_feedbacks
            )
            
            # 計算總分
            total_reward = sum(reward_components.values())
            normalized_score = self._normalize_score(total_reward) * 100
            
            # 生成改進建議
            improvement_suggestions = self._generate_improvement_suggestions(
                metrics, reward_components
            )
            
            # 創建評估結果
            evaluation = AnalystEvaluation(
                analyst_id=analyst_id,
                evaluation_date=evaluation_date,
                evaluation_period=evaluation_period,
                metrics=metrics,
                reward_components=reward_components,
                total_reward=total_reward,
                normalized_score=normalized_score,
                total_analyses=len(period_validations),
                market_validations=len(period_validations),
                user_feedbacks=len(period_feedbacks),
                improvement_suggestions=improvement_suggestions
            )
            
            # 保存評估結果
            self.historical_evaluations[analyst_id].append(evaluation)
            
            return evaluation
            
        except Exception as e:
            self.logger.error(f"分析師評估失敗 {analyst_id}: {str(e)}")
            raise
    
    async def batch_evaluate(
        self, 
        analyst_ids: List[str],
        evaluation_period: timedelta = timedelta(days=30)
    ) -> Dict[str, AnalystEvaluation]:
        """批量評估分析師"""
        
        results = {}
        
        # 並行評估
        tasks = []
        for analyst_id in analyst_ids:
            task = asyncio.create_task(
                self.evaluate_analyst(analyst_id, evaluation_period)
            )
            tasks.append((analyst_id, task))
        
        # 收集結果
        for analyst_id, task in tasks:
            try:
                evaluation = await task
                results[analyst_id] = evaluation
            except Exception as e:
                self.logger.error(f"批量評估失敗 {analyst_id}: {str(e)}")
        
        return results
    
    def add_market_validation(self, validation: MarketValidation):
        """添加市場驗證數據"""
        self.market_validations[validation.analyst_id].append(validation)
    
    def add_user_feedback(self, feedback: UserFeedback):
        """添加用戶反饋數據"""
        self.user_feedbacks[feedback.analyst_id].append(feedback)
    
    def get_analyst_ranking(
        self, 
        analyst_ids: List[str],
        ranking_criteria: str = 'overall'
    ) -> List[Tuple[str, float]]:
        """獲取分析師排名"""
        
        rankings = []
        
        for analyst_id in analyst_ids:
            if analyst_id in self.historical_evaluations:
                evaluations = self.historical_evaluations[analyst_id]
                if evaluations:
                    latest_evaluation = evaluations[-1]
                    
                    if ranking_criteria == 'overall':
                        score = latest_evaluation.normalized_score
                    elif ranking_criteria == 'market_validation':
                        score = latest_evaluation.reward_components.get(
                            RewardComponent.MARKET_VALIDATION, 0.0
                        ) * 100
                    elif ranking_criteria == 'user_feedback':
                        score = latest_evaluation.reward_components.get(
                            RewardComponent.USER_FEEDBACK, 0.0
                        ) * 100
                    else:
                        score = latest_evaluation.normalized_score
                    
                    rankings.append((analyst_id, score))
        
        # 按分數降序排列
        rankings.sort(key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def _get_validations_in_period(
        self, 
        analyst_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[MarketValidation]:
        """獲取評估期間的市場驗證數據"""
        
        validations = self.market_validations.get(analyst_id, [])
        period_validations = []
        
        for validation in validations:
            if start_date <= validation.prediction_date <= end_date:
                period_validations.append(validation)
        
        return period_validations
    
    def _get_feedbacks_in_period(
        self, 
        analyst_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[UserFeedback]:
        """獲取評估期間的用戶反饋數據"""
        
        feedbacks = self.user_feedbacks.get(analyst_id, [])
        period_feedbacks = []
        
        for feedback in feedbacks:
            if start_date <= feedback.feedback_date <= end_date:
                period_feedbacks.append(feedback)
        
        return period_feedbacks
    
    async def _calculate_metrics(
        self, 
        analyst_id: str,
        validations: List[MarketValidation],
        feedbacks: List[UserFeedback]
    ) -> Dict[EvaluationMetric, float]:
        """計算評估指標"""
        
        metrics = {}
        
        if validations:
            # 準確性指標
            correct_predictions = sum(1 for v in validations if v.direction_correct)
            metrics[EvaluationMetric.ACCURACY] = correct_predictions / len(validations)
            
            # 精確度和召回率（簡化版本）
            buy_predictions = [v for v in validations if v.predicted_direction == "BUY"]
            buy_correct = [v for v in buy_predictions if v.direction_correct]
            
            if buy_predictions:
                metrics[EvaluationMetric.PRECISION] = len(buy_correct) / len(buy_predictions)
            else:
                metrics[EvaluationMetric.PRECISION] = 0.0
            
            # 信心度校準
            confidence_errors = []
            for v in validations:
                actual_accuracy = 1.0 if v.direction_correct else 0.0
                error = abs(v.predicted_confidence - actual_accuracy)
                confidence_errors.append(error)
            
            if confidence_errors:
                avg_calibration_error = sum(confidence_errors) / len(confidence_errors)
                metrics[EvaluationMetric.CONFIDENCE_CALIBRATION] = max(0.0, 1.0 - avg_calibration_error)
            
            # 市場時機
            timing_scores = []
            for v in validations:
                if v.direction_correct and abs(v.actual_price_change) > 0.05:
                    timing_scores.append(1.0)
                elif v.direction_correct:
                    timing_scores.append(0.5)
                else:
                    timing_scores.append(0.0)
            
            if timing_scores:
                metrics[EvaluationMetric.MARKET_TIMING] = sum(timing_scores) / len(timing_scores)
        
        if feedbacks:
            # 用戶滿意度
            satisfaction_scores = [f.get_normalized_rating() for f in feedbacks]
            metrics[EvaluationMetric.USER_SATISFACTION] = sum(satisfaction_scores) / len(satisfaction_scores)
        
        return metrics
    
    async def _calculate_reward_components(
        self, 
        analyst_id: str,
        validations: List[MarketValidation],
        feedbacks: List[UserFeedback]
    ) -> Dict[RewardComponent, float]:
        """計算獎勵組件"""
        
        reward_components = defaultdict(float)
        
        if validations:
            for validation in validations:
                # 為每個驗證計算獎勵
                _, components = self.reward_function.calculate_reward(
                    analysis_result=None,  # 需要從別處獲取
                    market_validation=validation,
                    user_feedback=None,
                    historical_performance=None
                )
                
                # 累加各組件
                for component, score in components.items():
                    reward_components[component] += score
            
            # 取平均值
            for component in reward_components:
                reward_components[component] /= len(validations)
        
        return dict(reward_components)
    
    def _normalize_score(self, total_reward: float) -> float:
        """歸一化分數到0-1範圍"""
        
        # 將-1到1的獎勵範圍映射到0-1
        normalized = (total_reward + 1.0) / 2.0
        return max(0.0, min(1.0, normalized))
    
    def _generate_improvement_suggestions(
        self, 
        metrics: Dict[EvaluationMetric, float],
        reward_components: Dict[RewardComponent, float]
    ) -> List[str]:
        """生成改進建議"""
        
        suggestions = []
        
        # 基於指標的建議
        accuracy = metrics.get(EvaluationMetric.ACCURACY, 0.0)
        if accuracy < 0.6:
            suggestions.append("提高預測準確性：建議加強基本面和技術面分析能力")
        
        confidence_calibration = metrics.get(EvaluationMetric.CONFIDENCE_CALIBRATION, 0.0)
        if confidence_calibration < 0.6:
            suggestions.append("改善信心度校準：建議更準確地評估預測的不確定性")
        
        user_satisfaction = metrics.get(EvaluationMetric.USER_SATISFACTION, 0.0)
        if user_satisfaction < 0.6:
            suggestions.append("提升用戶體驗：建議提供更清晰、可操作的分析結果")
        
        # 基於獎勵組件的建議
        market_validation = reward_components.get(RewardComponent.MARKET_VALIDATION, 0.0)
        if market_validation < 0.5:
            suggestions.append("加強市場驗證表現：建議關注市場實際表現的後驗證")
        
        efficiency_penalty = reward_components.get(RewardComponent.EFFICIENCY_PENALTY, 0.0)
        if efficiency_penalty < -0.2:
            suggestions.append("優化成本效益：建議降低分析成本或提高分析價值")
        
        return suggestions


if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_analyst_evaluation():
        print("測試分析師評估系統")
        
        evaluator = AnalystEvaluator()
        
        # 創建測試數據
        validation = MarketValidation(
            analyst_id="test_analyst",
            stock_id="2330",
            prediction_date=datetime.now() - timedelta(days=30),
            validation_date=datetime.now(),
            predicted_direction="BUY",
            predicted_confidence=0.8,
            predicted_target_price=110.0,
            actual_price_change=0.05,  # 5%上漲
            actual_direction="BUY",
            market_return=0.02  # 市場2%回報
        )
        
        feedback = UserFeedback(
            analyst_id="test_analyst",
            stock_id="2330",
            feedback_date=datetime.now(),
            user_id="test_user",
            overall_rating=4.0,
            usefulness_rating=4.5,
            clarity_rating=4.0,
            actionability_rating=3.5,
            followed_recommendation=True
        )
        
        # 添加測試數據
        evaluator.add_market_validation(validation)
        evaluator.add_user_feedback(feedback)
        
        # 執行評估
        evaluation = await evaluator.evaluate_analyst("test_analyst")
        
        print(f"評估結果:")
        print(f"  總分: {evaluation.normalized_score:.1f}")
        print(f"  等級: {evaluation.get_grade()}")
        print(f"  準確率: {evaluation.metrics.get(EvaluationMetric.ACCURACY, 0):.2f}")
        print(f"  用戶滿意度: {evaluation.metrics.get(EvaluationMetric.USER_SATISFACTION, 0):.2f}")
        
        if evaluation.improvement_suggestions:
            print("  改進建議:")
            for suggestion in evaluation.improvement_suggestions:
                print(f"    - {suggestion}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_analyst_evaluation())