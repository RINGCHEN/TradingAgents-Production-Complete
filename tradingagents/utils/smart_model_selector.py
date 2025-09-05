#!/usr/bin/env python3
"""
Smart Model Selector - 智能模型選擇器
天工 (TianGong) - 基於AI的動態模型選擇和性能優化系統

此模組負責：
1. 動態模型選擇策略
2. 性能學習和優化
3. A/B測試整合
4. 個性化模型推薦
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import secrets  # 安全修復：使用加密安全的隨機數生成器替換random

from .llm_cost_optimizer import LLMCostOptimizer, ModelConfig, TaskComplexity, UsageRecord

class SelectionStrategy(Enum):
    """選擇策略"""
    COST_FIRST = "cost_first"           # 成本優先
    QUALITY_FIRST = "quality_first"     # 質量優先
    BALANCED = "balanced"               # 平衡選擇
    SPEED_FIRST = "speed_first"         # 速度優先
    ADAPTIVE = "adaptive"               # 自適應
    AB_TEST = "ab_test"                 # A/B測試

class PerformanceMetric(Enum):
    """性能指標"""
    COST_EFFICIENCY = "cost_efficiency"
    QUALITY_SCORE = "quality_score"
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    USER_SATISFACTION = "user_satisfaction"

@dataclass
class ModelPerformance:
    """模型性能記錄"""
    model_name: str
    task_type: str
    user_segment: str
    avg_cost: float
    avg_quality: float
    avg_response_time: float
    success_rate: float
    sample_size: int
    last_updated: str
    confidence_score: float = 0.0

@dataclass
class ABTestConfig:
    """A/B測試配置"""
    test_id: str
    name: str
    model_a: str
    model_b: str
    traffic_split: float  # A組流量比例 (0.0-1.0)
    target_metric: PerformanceMetric
    minimum_samples: int
    start_date: str
    end_date: str
    is_active: bool = True

@dataclass
class UserPreference:
    """用戶偏好"""
    user_id: str
    preferred_strategy: SelectionStrategy
    quality_tolerance: float    # 可接受的最低質量
    cost_sensitivity: float     # 成本敏感度 (0-1)
    speed_importance: float     # 速度重要性 (0-1)
    learned_from_feedback: bool = False

class SmartModelSelector:
    """智能模型選擇器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cost_optimizer = LLMCostOptimizer()
        
        # 性能追蹤
        self.model_performances: Dict[str, ModelPerformance] = {}
        self.user_preferences: Dict[str, UserPreference] = {}
        
        # A/B測試
        self.active_ab_tests: Dict[str, ABTestConfig] = {}
        self.ab_test_assignments: Dict[str, str] = {}  # user_id -> test_group
        
        # 學習參數
        self.learning_rate = 0.1
        self.min_samples_for_learning = 10
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def select_model_intelligently(
        self,
        user_context: Dict[str, Any],
        task_type: str,
        estimated_tokens: int = 1000,
        force_strategy: SelectionStrategy = None
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """智能選擇模型"""
        
        user_id = user_context.get('user_id', 'anonymous')
        
        # 獲取用戶偏好
        user_preference = self._get_user_preference(user_id)
        strategy = force_strategy or user_preference.preferred_strategy
        
        # 檢查是否在A/B測試中
        ab_test_result = await self._check_ab_test_assignment(user_id, task_type)
        if ab_test_result:
            return ab_test_result
        
        # 根據策略選擇模型
        if strategy == SelectionStrategy.ADAPTIVE:
            return await self._adaptive_selection(user_context, task_type, estimated_tokens)
        elif strategy == SelectionStrategy.COST_FIRST:
            return await self._cost_first_selection(user_context, task_type, estimated_tokens)
        elif strategy == SelectionStrategy.QUALITY_FIRST:
            return await self._quality_first_selection(user_context, task_type, estimated_tokens)
        elif strategy == SelectionStrategy.SPEED_FIRST:
            return await self._speed_first_selection(user_context, task_type, estimated_tokens)
        elif strategy == SelectionStrategy.BALANCED:
            return await self._balanced_selection(user_context, task_type, estimated_tokens)
        else:
            # 預設使用成本優化器
            complexity = self._infer_task_complexity(task_type)
            return await self.cost_optimizer.select_optimal_model(
                complexity, user_context, estimated_tokens
            )
    
    def _get_user_preference(self, user_id: str) -> UserPreference:
        """獲取用戶偏好"""
        if user_id not in self.user_preferences:
            # 為新用戶創建預設偏好
            self.user_preferences[user_id] = UserPreference(
                user_id=user_id,
                preferred_strategy=SelectionStrategy.ADAPTIVE,
                quality_tolerance=7.0,
                cost_sensitivity=0.5,
                speed_importance=0.3
            )
        
        return self.user_preferences[user_id]
    
    async def _check_ab_test_assignment(
        self, 
        user_id: str, 
        task_type: str
    ) -> Optional[Tuple[ModelConfig, Dict[str, Any]]]:
        """檢查A/B測試分配"""
        
        # 查找適用的A/B測試
        applicable_tests = []
        for test_id, test_config in self.active_ab_tests.items():
            if (test_config.is_active and 
                self._is_test_applicable(test_config, task_type)):
                applicable_tests.append((test_id, test_config))
        
        if not applicable_tests:
            return None
        
        # 選擇最高優先級的測試（這裡簡化為第一個）
        test_id, test_config = applicable_tests[0]
        
        # 檢查用戶是否已分配到組別
        assignment_key = f"{user_id}_{test_id}"
        if assignment_key not in self.ab_test_assignments:
            # 新用戶，進行分配
            is_group_a = (secrets.randbelow(10000) / 10000.0) < test_config.traffic_split  # 安全修復：使用secrets替換random
            self.ab_test_assignments[assignment_key] = "A" if is_group_a else "B"
        
        group = self.ab_test_assignments[assignment_key]
        model_name = test_config.model_a if group == "A" else test_config.model_b
        
        # 獲取模型配置
        model_config = self.cost_optimizer.model_configs.get(model_name)
        if not model_config:
            self.logger.warning(f"A/B測試模型不存在: {model_name}")
            return None
        
        return model_config, {
            "selection_reason": "ab_test",
            "test_id": test_id,
            "test_group": group,
            "model_name": model_name,
            "target_metric": test_config.target_metric.value
        }
    
    def _is_test_applicable(self, test_config: ABTestConfig, task_type: str) -> bool:
        """檢查A/B測試是否適用"""
        # 簡化實現：所有測試都適用於所有任務
        # 實際實現可以根據任務類型、用戶特徵等進行過濾
        
        current_date = datetime.now().strftime('%Y-%m-%d')
        return (test_config.start_date <= current_date <= test_config.end_date)
    
    async def _adaptive_selection(
        self, 
        user_context: Dict[str, Any], 
        task_type: str, 
        estimated_tokens: int
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """自適應選擇"""
        
        user_id = user_context.get('user_id', 'anonymous')
        user_preference = self._get_user_preference(user_id)
        
        # 獲取歷史性能數據
        performance_data = self._get_task_performance_data(task_type, user_id)
        
        if not performance_data:
            # 沒有歷史數據，使用平衡策略
            return await self._balanced_selection(user_context, task_type, estimated_tokens)
        
        # 根據歷史性能和用戶偏好計算模型評分
        model_scores = {}
        
        for model_name, performance in performance_data.items():
            if performance.sample_size < 3:  # 樣本太少，降低權重
                confidence_penalty = 0.5
            else:
                confidence_penalty = 1.0
            
            # 綜合評分計算
            cost_score = max(0, (0.1 - performance.avg_cost) / 0.1)  # 成本越低越好
            quality_score = performance.avg_quality / 10.0  # 質量評分
            speed_score = max(0, (5000 - performance.avg_response_time) / 5000)  # 速度評分
            
            # 根據用戶偏好加權
            composite_score = (
                cost_score * user_preference.cost_sensitivity +
                quality_score * (1 - user_preference.cost_sensitivity) * 0.7 +
                speed_score * user_preference.speed_importance * 0.3
            ) * confidence_penalty
            
            model_scores[model_name] = composite_score
        
        # 選擇評分最高的模型
        best_model_name = max(model_scores, key=model_scores.get)
        best_model_config = self.cost_optimizer.model_configs.get(best_model_name)
        
        if not best_model_config:
            # 後備方案
            return await self._balanced_selection(user_context, task_type, estimated_tokens)
        
        return best_model_config, {
            "selection_reason": "adaptive_learning",
            "composite_score": model_scores[best_model_name],
            "performance_based": True,
            "sample_size": performance_data[best_model_name].sample_size
        }
    
    async def _cost_first_selection(
        self, 
        user_context: Dict[str, Any], 
        task_type: str, 
        estimated_tokens: int
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """成本優先選擇"""
        
        membership_tier = user_context.get('membership_tier', 'FREE')
        
        # 獲取所有可用模型並按成本排序
        available_models = []
        
        for model_name, config in self.cost_optimizer.model_configs.items():
            if self.cost_optimizer._is_model_allowed_for_tier(config, membership_tier):
                estimated_cost = self.cost_optimizer._calculate_estimated_cost(config, estimated_tokens)
                available_models.append((config, estimated_cost))
        
        # 按成本排序，選擇最便宜的
        available_models.sort(key=lambda x: x[1])
        
        if not available_models:
            # 後備方案
            complexity = self._infer_task_complexity(task_type)
            return await self.cost_optimizer.select_optimal_model(
                complexity, user_context, estimated_tokens
            )
        
        best_model, best_cost = available_models[0]
        
        return best_model, {
            "selection_reason": "cost_optimization",
            "estimated_cost": best_cost,
            "cost_rank": 1,
            "alternatives": len(available_models) - 1
        }
    
    async def _quality_first_selection(
        self, 
        user_context: Dict[str, Any], 
        task_type: str, 
        estimated_tokens: int
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """質量優先選擇"""
        
        membership_tier = user_context.get('membership_tier', 'FREE')
        
        # 獲取所有可用模型並按質量排序
        available_models = []
        
        for model_name, config in self.cost_optimizer.model_configs.items():
            if self.cost_optimizer._is_model_allowed_for_tier(config, membership_tier):
                available_models.append(config)
        
        # 按質量排序，選擇質量最高的
        available_models.sort(key=lambda x: x.quality_score, reverse=True)
        
        if not available_models:
            # 後備方案
            complexity = self._infer_task_complexity(task_type)
            return await self.cost_optimizer.select_optimal_model(
                complexity, user_context, estimated_tokens
            )
        
        best_model = available_models[0]
        estimated_cost = self.cost_optimizer._calculate_estimated_cost(best_model, estimated_tokens)
        
        return best_model, {
            "selection_reason": "quality_optimization",
            "quality_score": best_model.quality_score,
            "estimated_cost": estimated_cost,
            "quality_rank": 1
        }
    
    async def _speed_first_selection(
        self, 
        user_context: Dict[str, Any], 
        task_type: str, 
        estimated_tokens: int
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """速度優先選擇"""
        
        membership_tier = user_context.get('membership_tier', 'FREE')
        
        # 獲取所有可用模型並按速度排序
        available_models = []
        
        for model_name, config in self.cost_optimizer.model_configs.items():
            if self.cost_optimizer._is_model_allowed_for_tier(config, membership_tier):
                available_models.append(config)
        
        # 按速度排序，選擇速度最快的
        available_models.sort(key=lambda x: x.speed_score, reverse=True)
        
        if not available_models:
            # 後備方案
            complexity = self._infer_task_complexity(task_type)
            return await self.cost_optimizer.select_optimal_model(
                complexity, user_context, estimated_tokens
            )
        
        best_model = available_models[0]
        estimated_cost = self.cost_optimizer._calculate_estimated_cost(best_model, estimated_tokens)
        
        return best_model, {
            "selection_reason": "speed_optimization",
            "speed_score": best_model.speed_score,
            "estimated_cost": estimated_cost,
            "speed_rank": 1
        }
    
    async def _balanced_selection(
        self, 
        user_context: Dict[str, Any], 
        task_type: str, 
        estimated_tokens: int
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """平衡選擇"""
        
        # 使用成本優化器的預設邏輯，這已經是一個平衡的選擇
        complexity = self._infer_task_complexity(task_type)
        return await self.cost_optimizer.select_optimal_model(
            complexity, user_context, estimated_tokens
        )
    
    def _infer_task_complexity(self, task_type: str) -> TaskComplexity:
        """推斷任務複雜度"""
        complexity_mapping = {
            "basic_analysis": TaskComplexity.SIMPLE,
            "quick_summary": TaskComplexity.SIMPLE,
            "technical_analysis": TaskComplexity.MODERATE,
            "fundamental_analysis": TaskComplexity.MODERATE,
            "news_analysis": TaskComplexity.MODERATE,
            "comprehensive_analysis": TaskComplexity.COMPLEX,
            "portfolio_analysis": TaskComplexity.COMPLEX,
            "investment_advice": TaskComplexity.CRITICAL,
            "risk_assessment": TaskComplexity.CRITICAL
        }
        
        return complexity_mapping.get(task_type, TaskComplexity.MODERATE)
    
    def _get_task_performance_data(self, task_type: str, user_segment: str) -> Dict[str, ModelPerformance]:
        """獲取任務性能數據"""
        performance_data = {}
        
        for key, performance in self.model_performances.items():
            if (performance.task_type == task_type and 
                (performance.user_segment == user_segment or performance.user_segment == "all")):
                performance_data[performance.model_name] = performance
        
        return performance_data
    
    async def learn_from_feedback(
        self,
        user_id: str,
        model_name: str,
        task_type: str,
        actual_cost: float,
        actual_quality: float,
        actual_response_time: float,
        success: bool,
        user_rating: Optional[float] = None
    ):
        """從反饋中學習"""
        
        # 更新模型性能記錄
        performance_key = f"{model_name}_{task_type}_all"  # 暫時使用"all"作為用戶段
        
        if performance_key not in self.model_performances:
            self.model_performances[performance_key] = ModelPerformance(
                model_name=model_name,
                task_type=task_type,
                user_segment="all",
                avg_cost=actual_cost,
                avg_quality=actual_quality,
                avg_response_time=actual_response_time,
                success_rate=1.0 if success else 0.0,
                sample_size=1,
                last_updated=datetime.now().isoformat()
            )
        else:
            # 更新現有記錄（使用移動平均）
            perf = self.model_performances[performance_key]
            
            # 計算新的移動平均
            alpha = self.learning_rate
            perf.avg_cost = (1 - alpha) * perf.avg_cost + alpha * actual_cost
            perf.avg_quality = (1 - alpha) * perf.avg_quality + alpha * actual_quality
            perf.avg_response_time = (1 - alpha) * perf.avg_response_time + alpha * actual_response_time
            
            # 更新成功率
            total_attempts = perf.sample_size + 1
            current_successes = perf.success_rate * perf.sample_size
            new_successes = current_successes + (1 if success else 0)
            perf.success_rate = new_successes / total_attempts
            
            perf.sample_size += 1
            perf.last_updated = datetime.now().isoformat()
            
            # 計算信心度
            perf.confidence_score = min(1.0, perf.sample_size / 50.0)  # 50個樣本達到最高信心度
        
        # 更新用戶偏好
        if user_rating is not None:
            await self._update_user_preference(user_id, model_name, user_rating, actual_cost)
        
        self.logger.info(f"學習更新: {model_name} - {task_type} - 樣本數: {self.model_performances[performance_key].sample_size}")
    
    async def _update_user_preference(self, user_id: str, model_name: str, rating: float, cost: float):
        """更新用戶偏好"""
        user_pref = self._get_user_preference(user_id)
        
        # 根據用戶評分和成本調整偏好
        if rating >= 8.0:  # 高分
            if cost < 0.01:  # 低成本
                # 用戶喜歡低成本高質量，提高成本敏感度
                user_pref.cost_sensitivity = min(1.0, user_pref.cost_sensitivity + 0.1)
            else:  # 高成本
                # 用戶為質量願意付費，降低成本敏感度
                user_pref.cost_sensitivity = max(0.0, user_pref.cost_sensitivity - 0.1)
        elif rating <= 5.0:  # 低分
            # 用戶不滿意，調整偏好
            model_config = self.cost_optimizer.model_configs.get(model_name)
            if model_config and model_config.quality_score < 8.0:
                # 低質量模型得低分，提高質量要求
                user_pref.quality_tolerance = min(10.0, user_pref.quality_tolerance + 0.5)
        
        user_pref.learned_from_feedback = True
        
        self.logger.debug(f"更新用戶偏好: {user_id} - 成本敏感度: {user_pref.cost_sensitivity:.2f}")
    
    def create_ab_test(
        self,
        test_name: str,
        model_a: str,
        model_b: str,
        target_metric: PerformanceMetric,
        duration_days: int = 7,
        traffic_split: float = 0.5
    ) -> str:
        """創建A/B測試"""
        
        test_id = f"ab_test_{int(time.time())}"
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=duration_days)).strftime('%Y-%m-%d')
        
        test_config = ABTestConfig(
            test_id=test_id,
            name=test_name,
            model_a=model_a,
            model_b=model_b,
            traffic_split=traffic_split,
            target_metric=target_metric,
            minimum_samples=50,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )
        
        self.active_ab_tests[test_id] = test_config
        
        self.logger.info(f"創建A/B測試: {test_name} ({model_a} vs {model_b})")
        
        return test_id
    
    def get_ab_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """獲取A/B測試結果"""
        
        if test_id not in self.active_ab_tests:
            return None
        
        test_config = self.active_ab_tests[test_id]
        
        # 統計各組結果
        group_a_results = []
        group_b_results = []
        
        for assignment_key, group in self.ab_test_assignments.items():
            if assignment_key.endswith(f"_{test_id}"):
                user_id = assignment_key.replace(f"_{test_id}", "")
                
                # 查找該用戶在測試期間的使用記錄
                user_records = [
                    r for r in self.cost_optimizer.usage_records
                    if (r.user_id == user_id and
                        test_config.start_date <= r.timestamp[:10] <= test_config.end_date)
                ]
                
                for record in user_records:
                    if group == "A" and record.model_name == test_config.model_a:
                        group_a_results.append(record)
                    elif group == "B" and record.model_name == test_config.model_b:
                        group_b_results.append(record)
        
        # 計算統計結果
        def calculate_group_stats(records: List[UsageRecord]) -> Dict[str, Any]:
            if not records:
                return {"sample_size": 0}
            
            return {
                "sample_size": len(records),
                "avg_cost": statistics.mean(r.cost_usd for r in records),
                "avg_response_time": statistics.mean(r.response_time_ms for r in records),
                "success_rate": sum(1 for r in records if r.success) / len(records),
                "total_cost": sum(r.cost_usd for r in records)
            }
        
        group_a_stats = calculate_group_stats(group_a_results)
        group_b_stats = calculate_group_stats(group_b_results)
        
        # 計算統計顯著性（簡化版本）
        statistical_significance = self._calculate_significance(group_a_stats, group_b_stats, test_config.target_metric)
        
        return {
            "test_id": test_id,
            "test_name": test_config.name,
            "status": "completed" if datetime.now().strftime('%Y-%m-%d') > test_config.end_date else "running",
            "target_metric": test_config.target_metric.value,
            "group_a": {
                "model": test_config.model_a,
                "stats": group_a_stats
            },
            "group_b": {
                "model": test_config.model_b,
                "stats": group_b_stats
            },
            "statistical_significance": statistical_significance,
            "winner": self._determine_winner(group_a_stats, group_b_stats, test_config.target_metric),
            "confidence_level": statistical_significance.get("confidence", 0.0)
        }
    
    def _calculate_significance(self, group_a: Dict, group_b: Dict, metric: PerformanceMetric) -> Dict[str, Any]:
        """計算統計顯著性（簡化版本）"""
        
        if group_a["sample_size"] < 10 or group_b["sample_size"] < 10:
            return {"significant": False, "confidence": 0.0, "reason": "insufficient_samples"}
        
        # 簡化的顯著性檢驗
        if metric == PerformanceMetric.COST_EFFICIENCY:
            metric_a = group_a.get("avg_cost", float('inf'))
            metric_b = group_b.get("avg_cost", float('inf'))
        elif metric == PerformanceMetric.RESPONSE_TIME:
            metric_a = group_a.get("avg_response_time", float('inf'))
            metric_b = group_b.get("avg_response_time", float('inf'))
        elif metric == PerformanceMetric.SUCCESS_RATE:
            metric_a = group_a.get("success_rate", 0.0)
            metric_b = group_b.get("success_rate", 0.0)
        else:
            return {"significant": False, "confidence": 0.0, "reason": "unsupported_metric"}
        
        # 簡化的效果量計算
        effect_size = abs(metric_a - metric_b) / max(metric_a, metric_b, 0.001)
        
        # 基於樣本數和效果量的信心度
        min_samples = min(group_a["sample_size"], group_b["sample_size"])
        confidence = min(0.95, effect_size * min_samples / 100)
        
        return {
            "significant": confidence > 0.8,
            "confidence": confidence,
            "effect_size": effect_size,
            "metric_a": metric_a,
            "metric_b": metric_b
        }
    
    def _determine_winner(self, group_a: Dict, group_b: Dict, metric: PerformanceMetric) -> str:
        """確定獲勝者"""
        
        if group_a["sample_size"] == 0 and group_b["sample_size"] == 0:
            return "inconclusive"
        elif group_a["sample_size"] == 0:
            return "group_b"
        elif group_b["sample_size"] == 0:
            return "group_a"
        
        if metric == PerformanceMetric.COST_EFFICIENCY:
            return "group_a" if group_a.get("avg_cost", float('inf')) < group_b.get("avg_cost", float('inf')) else "group_b"
        elif metric == PerformanceMetric.RESPONSE_TIME:
            return "group_a" if group_a.get("avg_response_time", float('inf')) < group_b.get("avg_response_time", float('inf')) else "group_b"
        elif metric == PerformanceMetric.SUCCESS_RATE:
            return "group_a" if group_a.get("success_rate", 0.0) > group_b.get("success_rate", 0.0) else "group_b"
        else:
            return "inconclusive"
    
    def get_selection_analytics(self, user_id: str = None) -> Dict[str, Any]:
        """獲取選擇分析"""
        
        # 模型使用統計
        model_usage = {}
        total_requests = 0
        
        for record in self.cost_optimizer.usage_records:
            if user_id and record.user_id != user_id:
                continue
            
            model_name = record.model_name
            if model_name not in model_usage:
                model_usage[model_name] = {
                    "requests": 0,
                    "total_cost": 0.0,
                    "avg_response_time": 0.0,
                    "success_rate": 0.0
                }
            
            stats = model_usage[model_name]
            stats["requests"] += 1
            stats["total_cost"] += record.cost_usd
            stats["avg_response_time"] += record.response_time_ms
            stats["success_rate"] += 1 if record.success else 0
            total_requests += 1
        
        # 計算平均值和使用比例
        for model_name, stats in model_usage.items():
            requests = stats["requests"]
            stats["usage_percentage"] = (requests / total_requests * 100) if total_requests > 0 else 0
            stats["avg_cost_per_request"] = stats["total_cost"] / requests
            stats["avg_response_time"] = stats["avg_response_time"] / requests
            stats["success_rate"] = (stats["success_rate"] / requests * 100) if requests > 0 else 0
        
        # 性能趨勢分析
        performance_trends = {}
        for key, performance in self.model_performances.items():
            model_name = performance.model_name
            if model_name not in performance_trends:
                performance_trends[model_name] = []
            
            performance_trends[model_name].append({
                "task_type": performance.task_type,
                "avg_quality": performance.avg_quality,
                "sample_size": performance.sample_size,
                "confidence": performance.confidence_score
            })
        
        return {
            "model_usage": model_usage,
            "performance_trends": performance_trends,
            "active_ab_tests": len(self.active_ab_tests),
            "total_requests": total_requests,
            "learning_samples": sum(p.sample_size for p in self.model_performances.values()),
            "timestamp": datetime.now().isoformat()
        }

# 便利函數
async def intelligent_model_selection(
    user_context: Dict[str, Any],
    task_type: str,
    estimated_tokens: int = 1000,
    strategy: SelectionStrategy = None
) -> Dict[str, Any]:
    """智能模型選擇"""
    
    selector = SmartModelSelector()
    
    selected_model, selection_info = await selector.select_model_intelligently(
        user_context, task_type, estimated_tokens, strategy
    )
    
    return {
        "selected_model": selected_model.model_name,
        "provider": selected_model.provider,
        "tier": selected_model.tier.value,
        "quality_score": selected_model.quality_score,
        "speed_score": selected_model.speed_score,
        "selection_info": selection_info,
        "estimated_cost": selection_info.get("estimated_cost", 0.0)
    }

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_smart_selector():
        print("🧠 測試智能模型選擇器")
        
        selector = SmartModelSelector()
        
        # 測試模型選擇
        user_context = {
            "user_id": "smart_test_user",
            "membership_tier": "GOLD"
        }
        
        selected_model, selection_info = await selector.select_model_intelligently(
            user_context, "technical_analysis", 1200
        )
        
        print(f"智能選擇: {selected_model.model_name}")
        print(f"選擇原因: {selection_info.get('selection_reason')}")
        
        # 測試A/B測試
        test_id = selector.create_ab_test(
            "GPT-4 vs Gemini Pro",
            "gpt-4",
            "gemini-pro",
            PerformanceMetric.COST_EFFICIENCY,
            duration_days=3
        )
        
        print(f"創建A/B測試: {test_id}")
        
        # 模擬學習
        await selector.learn_from_feedback(
            user_id="smart_test_user",
            model_name=selected_model.model_name,
            task_type="technical_analysis",
            actual_cost=0.025,
            actual_quality=8.5,
            actual_response_time=2800,
            success=True,
            user_rating=8.0
        )
        
        print("✅ 測試完成")
    
    asyncio.run(test_smart_selector())