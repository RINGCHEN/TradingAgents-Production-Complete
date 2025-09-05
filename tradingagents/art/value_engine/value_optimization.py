#!/usr/bin/env python3
"""
Value Optimization Engine - 價值優化引擎
天工 (TianGong) - 為ART系統提供價值優化和效率最大化

此模組提供：
1. ValueOptimizer - 價值優化核心引擎
2. OptimizationObjective - 優化目標管理
3. ValueOptimizationStrategy - 優化策略
4. ValueMaximizer - 價值最大化器
5. EfficiencyOptimizer - 效率優化器
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import uuid
import numpy as np
from collections import defaultdict, deque
import math

class OptimizationObjective(Enum):
    """優化目標"""
    MAXIMIZE_VALUE = "maximize_value"              # 最大化價值
    MINIMIZE_COST = "minimize_cost"                # 最小化成本
    MAXIMIZE_EFFICIENCY = "maximize_efficiency"    # 最大化效率
    MAXIMIZE_ROI = "maximize_roi"                  # 最大化ROI
    MINIMIZE_RISK = "minimize_risk"                # 最小化風險
    OPTIMIZE_BALANCE = "optimize_balance"          # 優化平衡
    MAXIMIZE_GROWTH = "maximize_growth"            # 最大化增長
    MINIMIZE_TIME = "minimize_time"                # 最小化時間

class OptimizationMethod(Enum):
    """優化方法"""
    GENETIC_ALGORITHM = "genetic_algorithm"        # 遺傳算法
    GRADIENT_DESCENT = "gradient_descent"          # 梯度下降
    SIMULATED_ANNEALING = "simulated_annealing"    # 模擬退火
    PARTICLE_SWARM = "particle_swarm"              # 粒子群優化
    RANDOM_SEARCH = "random_search"                # 隨機搜索
    BAYESIAN_OPTIMIZATION = "bayesian_optimization" # 貝葉斯優化

class ConstraintType(Enum):
    """約束類型"""
    EQUALITY = "equality"                          # 等式約束
    INEQUALITY = "inequality"                      # 不等式約束
    BOUND = "bound"                               # 邊界約束
    LINEAR = "linear"                             # 線性約束
    NONLINEAR = "nonlinear"                       # 非線性約束

@dataclass
class OptimizationConstraint:
    """優化約束"""
    constraint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    constraint_type: ConstraintType = ConstraintType.INEQUALITY
    expression: str = ""                          # 約束表達式
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    penalty_weight: float = 1.0                   # 懲罰權重
    active: bool = True
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OptimizationResult:
    """優化結果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    objective_value: float = 0.0                 # 目標函數值
    optimal_parameters: Dict[str, float] = field(default_factory=dict)
    optimization_objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_VALUE
    method_used: OptimizationMethod = OptimizationMethod.RANDOM_SEARCH
    
    # 優化過程信息
    iterations: int = 0                           # 迭代次數
    convergence_achieved: bool = False            # 是否收斂
    execution_time: float = 0.0                   # 執行時間
    function_evaluations: int = 0                 # 函數評估次數
    
    # 結果質量
    confidence_score: float = 0.0                 # 結果信心度
    improvement_percentage: float = 0.0           # 改進百分比
    constraint_violations: List[str] = field(default_factory=list)
    
    # 敏感性分析
    parameter_sensitivity: Dict[str, float] = field(default_factory=dict)
    robustness_score: float = 0.0                # 魯棒性分數
    
    # 元數據
    optimization_timestamp: float = field(default_factory=time.time)
    initial_parameters: Dict[str, float] = field(default_factory=dict)
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValueOptimizationStrategy:
    """價值優化策略"""
    strategy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # 優化配置
    objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_VALUE
    method: OptimizationMethod = OptimizationMethod.RANDOM_SEARCH
    constraints: List[OptimizationConstraint] = field(default_factory=list)
    
    # 參數配置
    parameter_bounds: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    parameter_weights: Dict[str, float] = field(default_factory=dict)
    
    # 算法配置
    max_iterations: int = 100
    convergence_tolerance: float = 1e-6
    population_size: int = 50                     # 種群大小（GA、PSO）
    mutation_rate: float = 0.1                    # 突變率（GA）
    crossover_rate: float = 0.8                   # 交叉率（GA）
    
    # 多目標優化
    multi_objective: bool = False
    objective_weights: Dict[OptimizationObjective, float] = field(default_factory=dict)
    pareto_optimization: bool = False
    
    # 元數據
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class ObjectiveFunction:
    """目標函數"""
    
    def __init__(self, objective: OptimizationObjective):
        self.objective = objective
        self.logger = logging.getLogger(__name__)
    
    async def evaluate(self, parameters: Dict[str, float], 
                      business_data: Dict[str, Any]) -> float:
        """評估目標函數"""
        try:
            if self.objective == OptimizationObjective.MAXIMIZE_VALUE:
                return await self._calculate_total_value(parameters, business_data)
            
            elif self.objective == OptimizationObjective.MINIMIZE_COST:
                return -await self._calculate_total_cost(parameters, business_data)
            
            elif self.objective == OptimizationObjective.MAXIMIZE_ROI:
                return await self._calculate_roi(parameters, business_data)
            
            elif self.objective == OptimizationObjective.MAXIMIZE_EFFICIENCY:
                return await self._calculate_efficiency(parameters, business_data)
            
            elif self.objective == OptimizationObjective.MINIMIZE_RISK:
                return -await self._calculate_risk(parameters, business_data)
            
            elif self.objective == OptimizationObjective.OPTIMIZE_BALANCE:
                return await self._calculate_balanced_score(parameters, business_data)
            
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Objective function evaluation failed: {e}")
            return -float('inf')  # 返回極小值表示評估失敗
    
    async def _calculate_total_value(self, parameters: Dict[str, float], 
                                   business_data: Dict[str, Any]) -> float:
        """計算總價值"""
        total_value = 0.0
        
        # 收入價值
        revenue_multiplier = parameters.get('revenue_multiplier', 1.0)
        base_revenue = business_data.get('base_revenue', 0)
        total_value += base_revenue * revenue_multiplier
        
        # 效率價值
        efficiency_gain = parameters.get('efficiency_gain', 0.0)
        cost_base = business_data.get('operational_cost', 0)
        total_value += cost_base * efficiency_gain
        
        # 市場價值
        market_share_gain = parameters.get('market_share_gain', 0.0)
        market_size = business_data.get('market_size', 0)
        total_value += market_size * market_share_gain * 0.1
        
        return total_value
    
    async def _calculate_total_cost(self, parameters: Dict[str, float],
                                  business_data: Dict[str, Any]) -> float:
        """計算總成本"""
        total_cost = 0.0
        
        # 運營成本
        operational_efficiency = parameters.get('operational_efficiency', 1.0)
        base_operational_cost = business_data.get('operational_cost', 0)
        total_cost += base_operational_cost / operational_efficiency
        
        # 投資成本
        investment_level = parameters.get('investment_level', 0.0)
        total_cost += investment_level
        
        # 風險成本
        risk_level = parameters.get('risk_level', 0.0)
        risk_cost_factor = business_data.get('risk_cost_factor', 1000)
        total_cost += risk_level * risk_cost_factor
        
        return total_cost
    
    async def _calculate_roi(self, parameters: Dict[str, float],
                           business_data: Dict[str, Any]) -> float:
        """計算ROI"""
        value = await self._calculate_total_value(parameters, business_data)
        cost = await self._calculate_total_cost(parameters, business_data)
        
        if cost <= 0:
            return 0.0
        
        return (value - cost) / cost * 100
    
    async def _calculate_efficiency(self, parameters: Dict[str, float],
                                  business_data: Dict[str, Any]) -> float:
        """計算效率"""
        output = await self._calculate_total_value(parameters, business_data)
        input_resources = parameters.get('resource_usage', 1.0)
        
        if input_resources <= 0:
            return 0.0
        
        return output / input_resources
    
    async def _calculate_risk(self, parameters: Dict[str, float],
                            business_data: Dict[str, Any]) -> float:
        """計算風險"""
        # 市場風險
        market_exposure = parameters.get('market_exposure', 0.5)
        market_volatility = business_data.get('market_volatility', 0.2)
        market_risk = market_exposure * market_volatility
        
        # 運營風險
        operational_complexity = parameters.get('operational_complexity', 0.3)
        operational_risk = operational_complexity * 0.1
        
        # 財務風險
        leverage = parameters.get('leverage', 1.0)
        financial_risk = max(0, (leverage - 1) * 0.2)
        
        return market_risk + operational_risk + financial_risk
    
    async def _calculate_balanced_score(self, parameters: Dict[str, float],
                                      business_data: Dict[str, Any]) -> float:
        """計算平衡分數"""
        # 多目標權重平衡
        value_weight = 0.4
        cost_weight = 0.2
        risk_weight = 0.2
        efficiency_weight = 0.2
        
        value_score = await self._calculate_total_value(parameters, business_data)
        cost_score = -await self._calculate_total_cost(parameters, business_data)  # 成本越低越好
        risk_score = -await self._calculate_risk(parameters, business_data)       # 風險越低越好
        efficiency_score = await self._calculate_efficiency(parameters, business_data)
        
        # 標準化分數
        max_value = business_data.get('max_expected_value', 100000)
        max_cost = business_data.get('max_expected_cost', 50000)
        
        normalized_value = value_score / max_value
        normalized_cost = cost_score / max_cost
        normalized_risk = max(0, 1 + risk_score)  # 風險轉為正分數
        normalized_efficiency = min(efficiency_score / 10, 1.0)  # 效率上限
        
        balanced_score = (
            value_weight * normalized_value +
            cost_weight * normalized_cost +
            risk_weight * normalized_risk +
            efficiency_weight * normalized_efficiency
        )
        
        return balanced_score

class OptimizationEngine:
    """優化引擎"""
    
    def __init__(self, strategy: ValueOptimizationStrategy):
        self.strategy = strategy
        self.objective_function = ObjectiveFunction(strategy.objective)
        self.logger = logging.getLogger(__name__)
    
    async def optimize(self, business_data: Dict[str, Any]) -> OptimizationResult:
        """執行優化"""
        start_time = time.time()
        
        try:
            if self.strategy.method == OptimizationMethod.RANDOM_SEARCH:
                result = await self._random_search_optimization(business_data)
            elif self.strategy.method == OptimizationMethod.GENETIC_ALGORITHM:
                result = await self._genetic_algorithm_optimization(business_data)
            elif self.strategy.method == OptimizationMethod.GRADIENT_DESCENT:
                result = await self._gradient_descent_optimization(business_data)
            elif self.strategy.method == OptimizationMethod.SIMULATED_ANNEALING:
                result = await self._simulated_annealing_optimization(business_data)
            else:
                result = await self._random_search_optimization(business_data)  # 默認方法
            
            result.execution_time = time.time() - start_time
            result.method_used = self.strategy.method
            
            # 計算改進百分比
            initial_value = await self.objective_function.evaluate(result.initial_parameters, business_data)
            if initial_value != 0:
                result.improvement_percentage = ((result.objective_value - initial_value) / abs(initial_value)) * 100
            
            # 敏感性分析
            result.parameter_sensitivity = await self._perform_sensitivity_analysis(
                result.optimal_parameters, business_data
            )
            
            self.logger.info(f"Optimization completed in {result.execution_time:.2f} seconds")
            return result
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            raise
    
    async def _random_search_optimization(self, business_data: Dict[str, Any]) -> OptimizationResult:
        """隨機搜索優化"""
        result = OptimizationResult(
            optimization_objective=self.strategy.objective,
            method_used=OptimizationMethod.RANDOM_SEARCH
        )
        
        best_value = -float('inf')
        best_parameters = {}
        
        # 生成初始參數
        initial_params = self._generate_random_parameters()
        result.initial_parameters = initial_params.copy()
        
        optimization_history = []
        
        for iteration in range(self.strategy.max_iterations):
            # 生成隨機參數
            parameters = self._generate_random_parameters()
            
            # 評估目標函數
            value = await self.objective_function.evaluate(parameters, business_data)
            
            # 檢查約束
            constraint_penalty = self._calculate_constraint_penalty(parameters)
            adjusted_value = value - constraint_penalty
            
            optimization_history.append({
                'iteration': iteration,
                'parameters': parameters.copy(),
                'objective_value': value,
                'adjusted_value': adjusted_value
            })
            
            if adjusted_value > best_value:
                best_value = adjusted_value
                best_parameters = parameters.copy()
                result.convergence_achieved = True
        
        result.objective_value = best_value
        result.optimal_parameters = best_parameters
        result.iterations = self.strategy.max_iterations
        result.function_evaluations = self.strategy.max_iterations
        result.optimization_history = optimization_history
        
        return result
    
    async def _genetic_algorithm_optimization(self, business_data: Dict[str, Any]) -> OptimizationResult:
        """遺傳算法優化"""
        result = OptimizationResult(
            optimization_objective=self.strategy.objective,
            method_used=OptimizationMethod.GENETIC_ALGORITHM
        )
        
        population_size = self.strategy.population_size
        crossover_rate = self.strategy.crossover_rate
        mutation_rate = self.strategy.mutation_rate
        
        # 初始化種群
        population = []
        for _ in range(population_size):
            individual = self._generate_random_parameters()
            fitness = await self.objective_function.evaluate(individual, business_data)
            population.append({'parameters': individual, 'fitness': fitness})
        
        result.initial_parameters = population[0]['parameters'].copy()
        
        best_individual = max(population, key=lambda x: x['fitness'])
        optimization_history = []
        
        for generation in range(self.strategy.max_iterations):
            # 選擇
            selected = self._tournament_selection(population, population_size // 2)
            
            # 交叉和突變
            new_population = []
            for i in range(0, len(selected), 2):
                parent1 = selected[i]
                parent2 = selected[i + 1] if i + 1 < len(selected) else selected[0]
                
                if np.random.random() < crossover_rate:
                    child1, child2 = self._crossover(parent1['parameters'], parent2['parameters'])
                else:
                    child1, child2 = parent1['parameters'].copy(), parent2['parameters'].copy()
                
                # 突變
                if np.random.random() < mutation_rate:
                    child1 = self._mutate(child1)
                if np.random.random() < mutation_rate:
                    child2 = self._mutate(child2)
                
                # 評估新個體
                fitness1 = await self.objective_function.evaluate(child1, business_data)
                fitness2 = await self.objective_function.evaluate(child2, business_data)
                
                new_population.extend([
                    {'parameters': child1, 'fitness': fitness1},
                    {'parameters': child2, 'fitness': fitness2}
                ])
            
            # 保留最佳個體
            population = sorted(new_population, key=lambda x: x['fitness'], reverse=True)[:population_size]
            
            current_best = population[0]
            if current_best['fitness'] > best_individual['fitness']:
                best_individual = current_best
            
            optimization_history.append({
                'generation': generation,
                'best_fitness': best_individual['fitness'],
                'avg_fitness': np.mean([ind['fitness'] for ind in population])
            })
        
        result.objective_value = best_individual['fitness']
        result.optimal_parameters = best_individual['parameters']
        result.iterations = self.strategy.max_iterations
        result.function_evaluations = self.strategy.max_iterations * population_size
        result.optimization_history = optimization_history
        
        return result
    
    async def _simulated_annealing_optimization(self, business_data: Dict[str, Any]) -> OptimizationResult:
        """模擬退火優化"""
        result = OptimizationResult(
            optimization_objective=self.strategy.objective,
            method_used=OptimizationMethod.SIMULATED_ANNEALING
        )
        
        # 初始化
        current_params = self._generate_random_parameters()
        result.initial_parameters = current_params.copy()
        
        current_value = await self.objective_function.evaluate(current_params, business_data)
        best_params = current_params.copy()
        best_value = current_value
        
        # 退火參數
        initial_temperature = 100.0
        cooling_rate = 0.95
        temperature = initial_temperature
        
        optimization_history = []
        
        for iteration in range(self.strategy.max_iterations):
            # 生成鄰域解
            new_params = self._generate_neighbor_solution(current_params)
            new_value = await self.objective_function.evaluate(new_params, business_data)
            
            # 接受準則
            delta = new_value - current_value
            if delta > 0 or np.random.random() < math.exp(delta / temperature):
                current_params = new_params
                current_value = new_value
                
                if new_value > best_value:
                    best_params = new_params.copy()
                    best_value = new_value
            
            # 降溫
            temperature *= cooling_rate
            
            optimization_history.append({
                'iteration': iteration,
                'temperature': temperature,
                'current_value': current_value,
                'best_value': best_value
            })
        
        result.objective_value = best_value
        result.optimal_parameters = best_params
        result.iterations = self.strategy.max_iterations
        result.function_evaluations = self.strategy.max_iterations
        result.optimization_history = optimization_history
        
        return result
    
    async def _gradient_descent_optimization(self, business_data: Dict[str, Any]) -> OptimizationResult:
        """梯度下降優化（數值梯度）"""
        result = OptimizationResult(
            optimization_objective=self.strategy.objective,
            method_used=OptimizationMethod.GRADIENT_DESCENT
        )
        
        # 初始化參數
        current_params = self._generate_random_parameters()
        result.initial_parameters = current_params.copy()
        
        learning_rate = 0.01
        optimization_history = []
        
        for iteration in range(self.strategy.max_iterations):
            # 計算數值梯度
            gradients = await self._calculate_numerical_gradient(current_params, business_data)
            
            # 更新參數
            for param_name in current_params:
                gradient = gradients.get(param_name, 0)
                current_params[param_name] += learning_rate * gradient
                
                # 確保參數在邊界內
                bounds = self.strategy.parameter_bounds.get(param_name)
                if bounds:
                    current_params[param_name] = max(bounds[0], min(bounds[1], current_params[param_name]))
            
            # 評估當前值
            current_value = await self.objective_function.evaluate(current_params, business_data)
            
            optimization_history.append({
                'iteration': iteration,
                'objective_value': current_value,
                'gradients': gradients.copy()
            })
            
            # 收斂檢查
            if iteration > 0 and abs(current_value - optimization_history[-2]['objective_value']) < self.strategy.convergence_tolerance:
                result.convergence_achieved = True
                break
        
        result.objective_value = current_value
        result.optimal_parameters = current_params
        result.iterations = iteration + 1
        result.function_evaluations = (iteration + 1) * (len(current_params) * 2 + 1)
        result.optimization_history = optimization_history
        
        return result
    
    def _generate_random_parameters(self) -> Dict[str, float]:
        """生成隨機參數"""
        parameters = {}
        for param_name, bounds in self.strategy.parameter_bounds.items():
            if bounds:
                lower, upper = bounds
                parameters[param_name] = np.random.uniform(lower, upper)
            else:
                parameters[param_name] = np.random.uniform(0, 1)
        
        return parameters
    
    def _generate_neighbor_solution(self, current_params: Dict[str, float]) -> Dict[str, float]:
        """生成鄰域解"""
        neighbor_params = current_params.copy()
        
        # 隨機選擇一個參數進行擾動
        param_name = np.random.choice(list(current_params.keys()))
        bounds = self.strategy.parameter_bounds.get(param_name, (0, 1))
        
        # 添加高斯擾動
        perturbation = np.random.normal(0, (bounds[1] - bounds[0]) * 0.1)
        new_value = current_params[param_name] + perturbation
        
        # 確保在邊界內
        neighbor_params[param_name] = max(bounds[0], min(bounds[1], new_value))
        
        return neighbor_params
    
    def _tournament_selection(self, population: List[Dict], tournament_size: int) -> List[Dict]:
        """錦標賽選擇"""
        selected = []
        for _ in range(tournament_size):
            tournament = np.random.choice(population, size=3, replace=False)
            winner = max(tournament, key=lambda x: x['fitness'])
            selected.append(winner)
        
        return selected
    
    def _crossover(self, parent1: Dict[str, float], parent2: Dict[str, float]) -> Tuple[Dict[str, float], Dict[str, float]]:
        """交叉操作"""
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        # 均勻交叉
        for param_name in parent1:
            if np.random.random() < 0.5:
                child1[param_name] = parent2[param_name]
                child2[param_name] = parent1[param_name]
        
        return child1, child2
    
    def _mutate(self, individual: Dict[str, float]) -> Dict[str, float]:
        """突變操作"""
        mutated = individual.copy()
        
        for param_name in individual:
            if np.random.random() < 0.1:  # 突變概率
                bounds = self.strategy.parameter_bounds.get(param_name, (0, 1))
                perturbation = np.random.normal(0, (bounds[1] - bounds[0]) * 0.1)
                new_value = individual[param_name] + perturbation
                mutated[param_name] = max(bounds[0], min(bounds[1], new_value))
        
        return mutated
    
    async def _calculate_numerical_gradient(self, parameters: Dict[str, float], 
                                          business_data: Dict[str, Any], 
                                          epsilon: float = 1e-6) -> Dict[str, float]:
        """計算數值梯度"""
        gradients = {}
        
        for param_name in parameters:
            # 前向差分
            params_plus = parameters.copy()
            params_plus[param_name] += epsilon
            value_plus = await self.objective_function.evaluate(params_plus, business_data)
            
            # 後向差分
            params_minus = parameters.copy()
            params_minus[param_name] -= epsilon
            value_minus = await self.objective_function.evaluate(params_minus, business_data)
            
            # 計算梯度
            gradients[param_name] = (value_plus - value_minus) / (2 * epsilon)
        
        return gradients
    
    def _calculate_constraint_penalty(self, parameters: Dict[str, float]) -> float:
        """計算約束懲罰"""
        total_penalty = 0.0
        
        for constraint in self.strategy.constraints:
            if not constraint.active:
                continue
            
            violation = 0.0
            
            if constraint.constraint_type == ConstraintType.BOUND:
                param_value = parameters.get(constraint.name, 0)
                if constraint.lower_bound is not None and param_value < constraint.lower_bound:
                    violation = constraint.lower_bound - param_value
                elif constraint.upper_bound is not None and param_value > constraint.upper_bound:
                    violation = param_value - constraint.upper_bound
            
            total_penalty += violation * constraint.penalty_weight
        
        return total_penalty
    
    async def _perform_sensitivity_analysis(self, optimal_parameters: Dict[str, float],
                                          business_data: Dict[str, Any]) -> Dict[str, float]:
        """執行敏感性分析"""
        sensitivity = {}
        base_value = await self.objective_function.evaluate(optimal_parameters, business_data)
        
        for param_name, param_value in optimal_parameters.items():
            # 參數變化±5%
            variation = abs(param_value) * 0.05 if param_value != 0 else 0.05
            
            # 正向變化
            params_plus = optimal_parameters.copy()
            params_plus[param_name] = param_value + variation
            value_plus = await self.objective_function.evaluate(params_plus, business_data)
            
            # 負向變化
            params_minus = optimal_parameters.copy()
            params_minus[param_name] = param_value - variation
            value_minus = await self.objective_function.evaluate(params_minus, business_data)
            
            # 計算敏感性
            if variation > 0 and base_value != 0:
                sensitivity[param_name] = abs((value_plus - value_minus) / (2 * variation) * param_value / base_value)
            else:
                sensitivity[param_name] = 0.0
        
        return sensitivity

class ValueMaximizer:
    """價值最大化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def maximize_portfolio_value(self, portfolio_data: Dict[str, Any]) -> OptimizationResult:
        """最大化投資組合價值"""
        strategy = ValueOptimizationStrategy(
            name="Portfolio Value Maximization",
            objective=OptimizationObjective.MAXIMIZE_VALUE,
            method=OptimizationMethod.GENETIC_ALGORITHM,
            max_iterations=50,
            population_size=30
        )
        
        # 設置參數邊界
        assets = portfolio_data.get('assets', [])
        for i, asset in enumerate(assets):
            strategy.parameter_bounds[f'weight_{i}'] = (0.0, 1.0)  # 權重範圍
        
        # 添加權重和約束
        weight_constraint = OptimizationConstraint(
            name="weight_sum",
            constraint_type=ConstraintType.EQUALITY,
            expression="sum(weights) = 1.0",
            penalty_weight=1000.0
        )
        strategy.constraints.append(weight_constraint)
        
        engine = OptimizationEngine(strategy)
        return await engine.optimize(portfolio_data)

class EfficiencyOptimizer:
    """效率優化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def optimize_operational_efficiency(self, operational_data: Dict[str, Any]) -> OptimizationResult:
        """優化營運效率"""
        strategy = ValueOptimizationStrategy(
            name="Operational Efficiency Optimization",
            objective=OptimizationObjective.MAXIMIZE_EFFICIENCY,
            method=OptimizationMethod.SIMULATED_ANNEALING,
            max_iterations=100
        )
        
        # 設置參數邊界
        strategy.parameter_bounds.update({
            'resource_allocation': (0.1, 2.0),
            'automation_level': (0.0, 1.0),
            'process_optimization': (0.0, 1.0),
            'technology_upgrade': (0.0, 1.0)
        })
        
        engine = OptimizationEngine(strategy)
        return await engine.optimize(operational_data)

class ValueOptimizer:
    """價值優化器"""
    
    def __init__(self):
        self.value_maximizer = ValueMaximizer()
        self.efficiency_optimizer = EfficiencyOptimizer()
        self.optimization_history: List[OptimizationResult] = []
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("ValueOptimizer initialized")
    
    async def optimize_comprehensive_value(self, business_data: Dict[str, Any], 
                                         strategy: Optional[ValueOptimizationStrategy] = None) -> OptimizationResult:
        """綜合價值優化"""
        if strategy is None:
            strategy = self._create_default_strategy()
        
        try:
            engine = OptimizationEngine(strategy)
            result = await engine.optimize(business_data)
            
            # 保存優化歷史
            self.optimization_history.append(result)
            
            self.logger.info(f"Comprehensive value optimization completed with objective value: {result.objective_value:.2f}")
            return result
            
        except Exception as e:
            self.logger.error(f"Comprehensive value optimization failed: {e}")
            raise
    
    def _create_default_strategy(self) -> ValueOptimizationStrategy:
        """創建默認優化策略"""
        strategy = ValueOptimizationStrategy(
            name="Default Comprehensive Optimization",
            objective=OptimizationObjective.OPTIMIZE_BALANCE,
            method=OptimizationMethod.GENETIC_ALGORITHM,
            max_iterations=100,
            population_size=50
        )
        
        # 默認參數邊界
        strategy.parameter_bounds.update({
            'revenue_multiplier': (0.8, 2.0),
            'cost_efficiency': (0.5, 1.5),
            'risk_tolerance': (0.1, 1.0),
            'investment_level': (0, 100000),
            'market_exposure': (0.1, 1.0),
            'innovation_investment': (0, 50000)
        })
        
        return strategy
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """獲取優化摘要"""
        if not self.optimization_history:
            return {'total_optimizations': 0}
        
        recent_results = self.optimization_history[-10:]  # 最近10次
        
        summary = {
            'total_optimizations': len(self.optimization_history),
            'average_objective_value': np.mean([r.objective_value for r in recent_results]),
            'average_execution_time': np.mean([r.execution_time for r in recent_results]),
            'convergence_rate': np.mean([1.0 if r.convergence_achieved else 0.0 for r in recent_results]),
            'most_common_method': max(set([r.method_used.value for r in recent_results]), 
                                    key=[r.method_used.value for r in recent_results].count),
            'latest_result': {
                'objective_value': recent_results[-1].objective_value,
                'improvement_percentage': recent_results[-1].improvement_percentage,
                'execution_time': recent_results[-1].execution_time
            }
        }
        
        return summary

# 工廠函數
def create_value_optimizer() -> ValueOptimizer:
    """創建價值優化器"""
    return ValueOptimizer()

def create_value_optimization_strategy(name: str = "", objective: OptimizationObjective = OptimizationObjective.MAXIMIZE_VALUE, **kwargs) -> ValueOptimizationStrategy:
    """創建價值優化策略"""
    return ValueOptimizationStrategy(name=name, objective=objective, **kwargs)

def create_optimization_constraint(name: str, constraint_type: ConstraintType = ConstraintType.INEQUALITY, **kwargs) -> OptimizationConstraint:
    """創建優化約束"""
    return OptimizationConstraint(name=name, constraint_type=constraint_type, **kwargs)