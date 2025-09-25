#!/usr/bin/env python3
"""
Behavior Optimizer - 行為優化器
天工 (TianGong) - 基於深度學習的用戶行為優化系統

此模組提供：
1. 行為優化分析
2. 多目標優化
3. 行為改進建議
4. 優化結果追蹤
5. 適應性優化策略
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
import numpy as np
import pandas as pd
from collections import defaultdict, deque
import uuid
import time
import math

class OptimizationObjective(Enum):
    """優化目標"""
    MAXIMIZE_RETURNS = "maximize_returns"           # 最大化收益
    MINIMIZE_RISK = "minimize_risk"                # 最小化風險
    IMPROVE_ACCURACY = "improve_accuracy"          # 提高準確度
    REDUCE_DRAWDOWN = "reduce_drawdown"            # 減少回撤
    OPTIMIZE_TIMING = "optimize_timing"            # 優化時機
    BALANCE_PORTFOLIO = "balance_portfolio"        # 平衡投資組合
    INCREASE_EFFICIENCY = "increase_efficiency"    # 提高效率
    ADAPTIVE_LEARNING = "adaptive_learning"       # 自適應學習

@dataclass
class OptimizationResult:
    """優化結果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    optimization_objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_RETURNS
    
    # 優化前後對比
    before_metrics: Dict[str, float] = field(default_factory=dict)
    after_metrics: Dict[str, float] = field(default_factory=dict)
    improvement_percentage: float = 0.0
    
    # 優化建議
    optimization_suggestions: List[str] = field(default_factory=list)
    action_priorities: Dict[str, float] = field(default_factory=dict)
    expected_impact: Dict[str, float] = field(default_factory=dict)
    
    # 實施計劃
    implementation_steps: List[Dict[str, Any]] = field(default_factory=list)
    timeline: Dict[str, datetime] = field(default_factory=dict)
    risk_assessment: Dict[str, float] = field(default_factory=dict)
    
    # 追蹤信息
    optimization_timestamp: float = field(default_factory=time.time)
    implementation_status: str = "pending"
    actual_results: Optional[Dict[str, float]] = None
    validation_timestamp: Optional[float] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class BehaviorOptimizer:
    """行為優化器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 優化歷史
        self.optimization_history: Dict[str, List[OptimizationResult]] = defaultdict(list)
        
        # 優化策略配置
        self.optimizer_config = {
            'min_data_points': self.config.get('min_data_points', 30),
            'optimization_window_days': self.config.get('optimization_window_days', 90),
            'max_suggestions': self.config.get('max_suggestions', 5),
            'risk_tolerance': self.config.get('risk_tolerance', 0.7),
            'learning_rate': self.config.get('learning_rate', 0.1)
        }
        
        self.logger.info("BehaviorOptimizer initialized")

    async def optimize_behavior(
        self,
        user_id: str,
        objective: OptimizationObjective,
        historical_data: List[Dict[str, Any]],
        current_behavior: Dict[str, Any],
        constraints: Dict[str, Any] = None
    ) -> OptimizationResult:
        """優化用戶行為"""
        
        try:
            self.logger.info(f"開始行為優化 - 用戶: {user_id}, 目標: {objective.value}")
            
            # 分析當前行為表現
            current_metrics = await self._analyze_current_performance(
                historical_data, current_behavior
            )
            
            # 識別優化機會
            optimization_opportunities = await self._identify_optimization_opportunities(
                historical_data, current_behavior, objective
            )
            
            # 生成優化建議
            suggestions = await self._generate_optimization_suggestions(
                optimization_opportunities, objective, constraints
            )
            
            # 預測優化效果
            predicted_metrics = await self._predict_optimization_impact(
                current_metrics, suggestions, objective
            )
            
            # 創建實施計劃
            implementation_plan = await self._create_implementation_plan(
                suggestions, objective
            )
            
            # 構建優化結果
            result = OptimizationResult(
                user_id=user_id,
                optimization_objective=objective,
                before_metrics=current_metrics,
                after_metrics=predicted_metrics,
                improvement_percentage=self._calculate_improvement_percentage(
                    current_metrics, predicted_metrics, objective
                ),
                optimization_suggestions=[s['description'] for s in suggestions],
                action_priorities={s['description']: s['priority'] for s in suggestions},
                expected_impact={s['description']: s['expected_impact'] for s in suggestions},
                implementation_steps=implementation_plan,
                risk_assessment=await self._assess_optimization_risks(suggestions)
            )
            
            # 保存優化結果
            self.optimization_history[user_id].append(result)
            
            self.logger.info(f"行為優化完成 - 預期改善: {result.improvement_percentage:.1f}%")
            return result
            
        except Exception as e:
            self.logger.error(f"行為優化失敗: {e}")
            # 返回基本優化結果
            return OptimizationResult(
                user_id=user_id,
                optimization_objective=objective,
                optimization_suggestions=["數據不足，建議積累更多交易歷史"]
            )

    async def _analyze_current_performance(
        self,
        historical_data: List[Dict[str, Any]],
        current_behavior: Dict[str, Any]
    ) -> Dict[str, float]:
        """分析當前表現"""
        
        if not historical_data:
            return {'performance_score': 0.5}
        
        df = pd.DataFrame(historical_data)
        
        metrics = {}
        
        # 收益率分析
        if 'return' in df.columns:
            returns = df['return'].dropna()
            if len(returns) > 0:
                metrics['average_return'] = float(returns.mean())
                metrics['return_volatility'] = float(returns.std())
                metrics['sharpe_ratio'] = float(returns.mean() / returns.std()) if returns.std() > 0 else 0
                metrics['max_drawdown'] = float(returns.cumsum().expanding().max() - returns.cumsum()).max() if len(returns) > 1 else 0
        
        # 交易頻率分析
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], unit='s')
            if len(timestamps) > 1:
                time_diffs = timestamps.diff().dt.total_seconds() / 3600  # 小時
                metrics['avg_time_between_trades'] = float(time_diffs.mean())
                metrics['trading_frequency'] = float(len(timestamps) / ((timestamps.max() - timestamps.min()).total_seconds() / 86400))  # 每日交易次數
        
        # 準確度分析
        if 'prediction_accuracy' in df.columns:
            accuracies = df['prediction_accuracy'].dropna()
            if len(accuracies) > 0:
                metrics['prediction_accuracy'] = float(accuracies.mean())
        
        # 風險指標
        if 'risk_score' in df.columns:
            risk_scores = df['risk_score'].dropna()
            if len(risk_scores) > 0:
                metrics['average_risk'] = float(risk_scores.mean())
        
        return metrics

    async def _identify_optimization_opportunities(
        self,
        historical_data: List[Dict[str, Any]],
        current_behavior: Dict[str, Any],
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """識別優化機會"""
        
        opportunities = []
        
        if not historical_data:
            return opportunities
        
        df = pd.DataFrame(historical_data)
        
        # 基於目標識別機會
        if objective == OptimizationObjective.MAXIMIZE_RETURNS:
            # 尋找高收益交易模式
            if 'return' in df.columns and 'hour' in df.columns:
                hourly_returns = df.groupby('hour')['return'].mean()
                best_hours = hourly_returns.nlargest(3).index.tolist()
                opportunities.append({
                    'type': 'timing_optimization',
                    'description': f'在 {best_hours} 時段交易表現較佳',
                    'potential_improvement': 0.15,
                    'data_support': len(df)
                })
        
        elif objective == OptimizationObjective.MINIMIZE_RISK:
            # 尋找低風險策略
            if 'risk_score' in df.columns and 'return' in df.columns:
                low_risk_trades = df[df['risk_score'] < df['risk_score'].median()]
                if len(low_risk_trades) > 0 and low_risk_trades['return'].mean() > 0:
                    opportunities.append({
                        'type': 'risk_reduction',
                        'description': '專注於低風險高回報交易',
                        'potential_improvement': 0.20,
                        'data_support': len(low_risk_trades)
                    })
        
        elif objective == OptimizationObjective.IMPROVE_ACCURACY:
            # 尋找準確度改進機會
            if 'prediction_accuracy' in df.columns:
                low_accuracy_periods = df[df['prediction_accuracy'] < 0.6]
                if len(low_accuracy_periods) > 0:
                    opportunities.append({
                        'type': 'accuracy_improvement',
                        'description': '改進預測準確度較低的交易類型',
                        'potential_improvement': 0.25,
                        'data_support': len(low_accuracy_periods)
                    })
        
        # 通用優化機會
        # 交易頻率優化
        if 'timestamp' in df.columns and len(df) > 10:
            timestamps = pd.to_datetime(df['timestamp'], unit='s')
            time_diffs = timestamps.diff().dt.total_seconds() / 3600
            if time_diffs.mean() < 1:  # 交易過於頻繁
                opportunities.append({
                    'type': 'frequency_optimization',
                    'description': '減少過度交易，提高決策品質',
                    'potential_improvement': 0.12,
                    'data_support': len(df)
                })
        
        return opportunities

    async def _generate_optimization_suggestions(
        self,
        opportunities: List[Dict[str, Any]],
        objective: OptimizationObjective,
        constraints: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """生成優化建議"""
        
        suggestions = []
        constraints = constraints or {}
        
        for opp in opportunities:
            suggestion = {
                'type': opp['type'],
                'description': opp['description'],
                'expected_impact': opp['potential_improvement'],
                'priority': self._calculate_suggestion_priority(opp, objective),
                'implementation_difficulty': self._assess_implementation_difficulty(opp),
                'resource_requirements': self._estimate_resource_requirements(opp),
                'timeline_days': self._estimate_implementation_timeline(opp)
            }
            
            # 檢查約束條件
            if self._check_constraints(suggestion, constraints):
                suggestions.append(suggestion)
        
        # 按優先級排序
        suggestions.sort(key=lambda x: x['priority'], reverse=True)
        
        # 限制建議數量
        return suggestions[:self.optimizer_config['max_suggestions']]

    def _calculate_suggestion_priority(
        self,
        opportunity: Dict[str, Any],
        objective: OptimizationObjective
    ) -> float:
        """計算建議優先級"""
        
        base_priority = opportunity['potential_improvement']
        data_support = opportunity['data_support']
        
        # 根據數據支持度調整
        support_factor = min(data_support / 100, 1.0)  # 最多100個數據點為滿分
        
        # 根據目標類型調整
        objective_weights = {
            OptimizationObjective.MAXIMIZE_RETURNS: 1.2,
            OptimizationObjective.MINIMIZE_RISK: 1.1,
            OptimizationObjective.IMPROVE_ACCURACY: 1.0,
            OptimizationObjective.REDUCE_DRAWDOWN: 1.1,
            OptimizationObjective.OPTIMIZE_TIMING: 0.9
        }
        
        weight = objective_weights.get(objective, 1.0)
        
        return base_priority * support_factor * weight

    def _assess_implementation_difficulty(self, opportunity: Dict[str, Any]) -> float:
        """評估實施難度 (0-1, 1為最難)"""
        
        difficulty_map = {
            'timing_optimization': 0.3,
            'risk_reduction': 0.4,
            'accuracy_improvement': 0.7,
            'frequency_optimization': 0.2,
            'portfolio_rebalancing': 0.5
        }
        
        return difficulty_map.get(opportunity['type'], 0.5)

    def _estimate_resource_requirements(self, opportunity: Dict[str, Any]) -> Dict[str, str]:
        """估算資源需求"""
        
        resource_map = {
            'timing_optimization': {'time': 'low', 'technical': 'low', 'financial': 'none'},
            'risk_reduction': {'time': 'medium', 'technical': 'medium', 'financial': 'low'},
            'accuracy_improvement': {'time': 'high', 'technical': 'high', 'financial': 'medium'},
            'frequency_optimization': {'time': 'low', 'technical': 'low', 'financial': 'none'}
        }
        
        return resource_map.get(opportunity['type'], {'time': 'medium', 'technical': 'medium', 'financial': 'low'})

    def _estimate_implementation_timeline(self, opportunity: Dict[str, Any]) -> int:
        """估算實施時間（天）"""
        
        timeline_map = {
            'timing_optimization': 7,
            'risk_reduction': 14,
            'accuracy_improvement': 30,
            'frequency_optimization': 3,
            'portfolio_rebalancing': 14
        }
        
        return timeline_map.get(opportunity['type'], 14)

    def _check_constraints(
        self,
        suggestion: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> bool:
        """檢查約束條件"""
        
        # 檢查最大實施時間
        if 'max_timeline_days' in constraints:
            if suggestion['timeline_days'] > constraints['max_timeline_days']:
                return False
        
        # 檢查風險容忍度
        if 'max_risk_level' in constraints:
            if suggestion['implementation_difficulty'] > constraints['max_risk_level']:
                return False
        
        return True

    async def _predict_optimization_impact(
        self,
        current_metrics: Dict[str, float],
        suggestions: List[Dict[str, Any]],
        objective: OptimizationObjective
    ) -> Dict[str, float]:
        """預測優化影響"""
        
        predicted_metrics = current_metrics.copy()
        
        total_improvement = sum(s['expected_impact'] for s in suggestions)
        
        # 根據目標調整預測
        if objective == OptimizationObjective.MAXIMIZE_RETURNS:
            if 'average_return' in predicted_metrics:
                predicted_metrics['average_return'] *= (1 + total_improvement)
        
        elif objective == OptimizationObjective.MINIMIZE_RISK:
            if 'return_volatility' in predicted_metrics:
                predicted_metrics['return_volatility'] *= (1 - total_improvement * 0.5)
            if 'average_risk' in predicted_metrics:
                predicted_metrics['average_risk'] *= (1 - total_improvement)
        
        elif objective == OptimizationObjective.IMPROVE_ACCURACY:
            if 'prediction_accuracy' in predicted_metrics:
                predicted_metrics['prediction_accuracy'] = min(
                    predicted_metrics['prediction_accuracy'] * (1 + total_improvement), 1.0
                )
        
        return predicted_metrics

    async def _create_implementation_plan(
        self,
        suggestions: List[Dict[str, Any]],
        objective: OptimizationObjective
    ) -> List[Dict[str, Any]]:
        """創建實施計劃"""
        
        plan = []
        current_date = datetime.now()
        
        for i, suggestion in enumerate(suggestions):
            step = {
                'step_number': i + 1,
                'description': suggestion['description'],
                'type': suggestion['type'],
                'start_date': current_date + timedelta(days=i * 3),
                'duration_days': suggestion['timeline_days'],
                'resources_needed': suggestion['resource_requirements'],
                'success_metrics': self._define_success_metrics(suggestion, objective),
                'monitoring_points': self._define_monitoring_points(suggestion)
            }
            plan.append(step)
        
        return plan

    def _define_success_metrics(
        self,
        suggestion: Dict[str, Any],
        objective: OptimizationObjective
    ) -> List[str]:
        """定義成功指標"""
        
        base_metrics = ['implementation_completed', 'no_negative_side_effects']
        
        if objective == OptimizationObjective.MAXIMIZE_RETURNS:
            base_metrics.extend(['return_improvement', 'sharpe_ratio_improvement'])
        elif objective == OptimizationObjective.MINIMIZE_RISK:
            base_metrics.extend(['risk_reduction', 'volatility_decrease'])
        elif objective == OptimizationObjective.IMPROVE_ACCURACY:
            base_metrics.extend(['accuracy_increase', 'prediction_consistency'])
        
        return base_metrics

    def _define_monitoring_points(self, suggestion: Dict[str, Any]) -> List[str]:
        """定義監控點"""
        
        return [
            f"第3天: 初步效果評估",
            f"第7天: 中期進展檢查",
            f"第{suggestion['timeline_days']}天: 最終成果驗證"
        ]

    async def _assess_optimization_risks(
        self,
        suggestions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """評估優化風險"""
        
        risks = {
            'implementation_failure': 0.0,
            'negative_side_effects': 0.0,
            'resource_overrun': 0.0,
            'timeline_delay': 0.0
        }
        
        for suggestion in suggestions:
            difficulty = suggestion['implementation_difficulty']
            
            risks['implementation_failure'] = max(risks['implementation_failure'], difficulty * 0.3)
            risks['negative_side_effects'] = max(risks['negative_side_effects'], difficulty * 0.2)
            risks['resource_overrun'] = max(risks['resource_overrun'], difficulty * 0.4)
            risks['timeline_delay'] = max(risks['timeline_delay'], difficulty * 0.5)
        
        return risks

    def _calculate_improvement_percentage(
        self,
        before_metrics: Dict[str, float],
        after_metrics: Dict[str, float],
        objective: OptimizationObjective
    ) -> float:
        """計算改進百分比"""
        
        key_metric_map = {
            OptimizationObjective.MAXIMIZE_RETURNS: 'average_return',
            OptimizationObjective.MINIMIZE_RISK: 'average_risk',
            OptimizationObjective.IMPROVE_ACCURACY: 'prediction_accuracy',
            OptimizationObjective.REDUCE_DRAWDOWN: 'max_drawdown'
        }
        
        key_metric = key_metric_map.get(objective, 'average_return')
        
        if key_metric in before_metrics and key_metric in after_metrics:
            before = before_metrics[key_metric]
            after = after_metrics[key_metric]
            
            if before != 0:
                if objective in [OptimizationObjective.MINIMIZE_RISK, OptimizationObjective.REDUCE_DRAWDOWN]:
                    # 對於最小化目標，計算減少百分比
                    return ((before - after) / abs(before)) * 100
                else:
                    # 對於最大化目標，計算增加百分比
                    return ((after - before) / abs(before)) * 100
        
        return 0.0

    def get_optimization_history(self, user_id: str) -> List[OptimizationResult]:
        """獲取優化歷史"""
        return self.optimization_history.get(user_id, [])

    def get_optimization_summary(self, user_id: str) -> Dict[str, Any]:
        """獲取優化摘要"""
        
        history = self.optimization_history.get(user_id, [])
        
        if not history:
            return {'total_optimizations': 0}
        
        return {
            'total_optimizations': len(history),
            'avg_improvement': np.mean([r.improvement_percentage for r in history]),
            'most_common_objective': max(
                [r.optimization_objective for r in history],
                key=lambda x: [r.optimization_objective for r in history].count(x)
            ).value,
            'total_suggestions': sum(len(r.optimization_suggestions) for r in history),
            'latest_optimization': history[-1].optimization_timestamp
        }