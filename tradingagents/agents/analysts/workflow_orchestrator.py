#!/usr/bin/env python3
"""
Analyst Workflow Orchestrator - 分析師工作流編排器
天工 (TianGong) - BaseAnalyst與不老傳說Graph的智能整合系統

此模組提供：
1. 分析師工作流智能編排
2. 依賴關係自動解析
3. 並行執行優化管理
4. 結果聚合和衝突解決
5. 錯誤恢復和重試機制
6. 實時監控和狀態推送
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid

from .base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType, AnalysisConfidenceLevel
from ...utils.logging_config import get_analysis_logger
from ...utils.error_handler import handle_error


class ExecutionPhase(Enum):
    """執行階段"""
    PLANNING = "planning"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    PARALLEL_EXECUTION = "parallel_execution"
    RESULT_AGGREGATION = "result_aggregation"
    CONFLICT_RESOLUTION = "conflict_resolution"
    FINALIZATION = "finalization"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStrategy(Enum):
    """執行策略"""
    SEQUENTIAL = "sequential"          # 序列執行
    PARALLEL = "parallel"              # 並行執行
    DEPENDENCY_DRIVEN = "dependency_driven"  # 依賴驅動執行
    ADAPTIVE = "adaptive"              # 自適應執行


@dataclass
class AnalystNode:
    """分析師節點"""
    analyst_id: str
    analyst: BaseAnalyst
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    execution_priority: int = 0
    is_critical: bool = False
    estimated_duration: float = 0.0
    resource_weight: float = 1.0
    
    def __post_init__(self):
        """初始化後處理"""
        if hasattr(self.analyst, 'get_workflow_compatibility'):
            compatibility = self.analyst.get_workflow_compatibility()
            time_info = compatibility.get('estimated_execution_time', {})
            self.estimated_duration = time_info.get('avg_time', 3.0)
            
            resource_info = compatibility.get('resource_requirements', {})
            self.resource_weight = resource_info.get('cpu_cores', 1.0)


@dataclass
class ExecutionPlan:
    """執行計劃"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_strategy: ExecutionStrategy = ExecutionStrategy.DEPENDENCY_DRIVEN
    execution_phases: List[List[str]] = field(default_factory=list)
    estimated_total_time: float = 0.0
    parallelism_factor: float = 1.0
    resource_allocation: Dict[str, float] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionResult:
    """執行結果"""
    session_id: str
    analyst_results: Dict[str, AnalysisResult] = field(default_factory=dict)
    execution_metadata: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    conflict_resolutions: List[Dict[str, Any]] = field(default_factory=list)
    final_integrated_result: Optional[AnalysisResult] = None
    success: bool = True
    error_message: Optional[str] = None


class WorkflowOrchestrator:
    """工作流編排器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = get_analysis_logger("workflow_orchestrator")
        
        # 分析師註冊表
        self.analysts: Dict[str, BaseAnalyst] = {}
        self.analyst_nodes: Dict[str, AnalystNode] = {}
        
        # 執行配置
        self.max_parallelism = self.config.get('max_parallelism', 4)
        self.execution_timeout = self.config.get('execution_timeout', 300)  # 5分鐘
        self.retry_attempts = self.config.get('retry_attempts', 2)
        self.conflict_resolution_enabled = self.config.get('conflict_resolution_enabled', True)
        
        # 狀態管理
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.execution_history: Dict[str, ExecutionResult] = {}
        
        self.logger.info("WorkflowOrchestrator 初始化完成", extra={
            'max_parallelism': self.max_parallelism,
            'execution_timeout': self.execution_timeout,
            'conflict_resolution_enabled': self.conflict_resolution_enabled
        })
    
    def register_analyst(self, analyst: BaseAnalyst) -> str:
        """註冊分析師"""
        analyst_id = analyst.analyst_id
        
        # 創建分析師節點
        node = AnalystNode(
            analyst_id=analyst_id,
            analyst=analyst
        )
        
        # 獲取依賴關係
        if hasattr(analyst, 'get_workflow_compatibility'):
            compatibility = analyst.get_workflow_compatibility()
            dependency_types = compatibility.get('dependency_types', [])
            
            # 將依賴類型轉換為分析師ID
            for dep_type in dependency_types:
                dep_analyst_id = f"{dep_type}_analyst"
                if dep_analyst_id != analyst_id:  # 避免自依賴
                    node.dependencies.add(dep_analyst_id)
        
        # 設定執行優先級和關鍵性
        analysis_type = analyst.get_analysis_type()
        if analysis_type == AnalysisType.INVESTMENT_PLANNING:
            node.execution_priority = 100  # 最高優先級
            node.is_critical = True
        elif analysis_type == AnalysisType.RISK_ASSESSMENT:
            node.execution_priority = 80
            node.is_critical = True
        elif analysis_type == AnalysisType.FUNDAMENTAL:
            node.execution_priority = 70
        elif analysis_type == AnalysisType.TAIWAN_SPECIFIC:
            node.execution_priority = 60
        else:
            node.execution_priority = 50
        
        self.analysts[analyst_id] = analyst
        self.analyst_nodes[analyst_id] = node
        
        # 更新依賴關係圖
        self._update_dependency_graph()
        
        self.logger.info(f"註冊分析師: {analyst_id}", extra={
            'analysis_type': analysis_type.value,
            'dependencies': list(node.dependencies),
            'priority': node.execution_priority,
            'is_critical': node.is_critical
        })
        
        return analyst_id
    
    def _update_dependency_graph(self):
        """更新依賴關係圖"""
        # 重置所有依賴者關係
        for node in self.analyst_nodes.values():
            node.dependents.clear()
        
        # 重建依賴者關係
        for node in self.analyst_nodes.values():
            for dep_id in node.dependencies:
                if dep_id in self.analyst_nodes:
                    self.analyst_nodes[dep_id].dependents.add(node.analyst_id)
    
    def create_execution_plan(
        self, 
        selected_analysts: List[str] = None,
        strategy: ExecutionStrategy = ExecutionStrategy.DEPENDENCY_DRIVEN
    ) -> ExecutionPlan:
        """創建執行計劃"""
        
        # 確定要執行的分析師
        if selected_analysts:
            analysts_to_execute = [aid for aid in selected_analysts if aid in self.analysts]
        else:
            analysts_to_execute = list(self.analysts.keys())
        
        plan = ExecutionPlan(execution_strategy=strategy)
        
        if strategy == ExecutionStrategy.SEQUENTIAL:
            # 序列執行：按優先級排序
            sorted_analysts = sorted(
                analysts_to_execute,
                key=lambda aid: self.analyst_nodes[aid].execution_priority,
                reverse=True
            )
            plan.execution_phases = [[aid] for aid in sorted_analysts]
            plan.estimated_total_time = sum(
                self.analyst_nodes[aid].estimated_duration for aid in sorted_analysts
            )
            plan.parallelism_factor = 1.0
            
        elif strategy == ExecutionStrategy.PARALLEL:
            # 並行執行：所有分析師同時執行
            plan.execution_phases = [analysts_to_execute]
            plan.estimated_total_time = max(
                self.analyst_nodes[aid].estimated_duration for aid in analysts_to_execute
            )
            plan.parallelism_factor = len(analysts_to_execute)
            
        elif strategy == ExecutionStrategy.DEPENDENCY_DRIVEN:
            # 依賴驅動執行：基於依賴關係的拓撲排序
            plan.execution_phases = self._create_dependency_phases(analysts_to_execute)
            plan.estimated_total_time = self._estimate_dependency_execution_time(plan.execution_phases)
            plan.parallelism_factor = self._calculate_parallelism_factor(plan.execution_phases)
            
        elif strategy == ExecutionStrategy.ADAPTIVE:
            # 自適應執行：根據系統狀態動態調整
            plan = self._create_adaptive_plan(analysts_to_execute)
        
        # 資源分配
        plan.resource_allocation = self._allocate_resources(plan.execution_phases)
        
        # 風險評估
        plan.risk_assessment = self._assess_execution_risks(plan)
        
        self.logger.info(f"創建執行計劃: {plan.plan_id}", extra={
            'strategy': strategy.value,
            'phases_count': len(plan.execution_phases),
            'estimated_time': plan.estimated_total_time,
            'parallelism_factor': plan.parallelism_factor
        })
        
        return plan
    
    def _create_dependency_phases(self, analysts_to_execute: List[str]) -> List[List[str]]:
        """基於依賴關係創建執行階段"""
        phases = []
        remaining_analysts = set(analysts_to_execute)
        executed_analysts = set()
        
        while remaining_analysts:
            # 找到所有依賴已滿足的分析師
            ready_analysts = []
            for analyst_id in remaining_analysts:
                node = self.analyst_nodes[analyst_id]
                dependencies_satisfied = all(
                    dep_id in executed_analysts or dep_id not in analysts_to_execute
                    for dep_id in node.dependencies
                )
                if dependencies_satisfied:
                    ready_analysts.append(analyst_id)
            
            if not ready_analysts:
                # 檢測循環依賴
                self.logger.warning("檢測到循環依賴，強制執行剩餘分析師")
                ready_analysts = list(remaining_analysts)
            
            # 按優先級排序
            ready_analysts.sort(
                key=lambda aid: self.analyst_nodes[aid].execution_priority,
                reverse=True
            )
            
            phases.append(ready_analysts)
            executed_analysts.update(ready_analysts)
            remaining_analysts -= set(ready_analysts)
        
        return phases
    
    def _estimate_dependency_execution_time(self, phases: List[List[str]]) -> float:
        """估算依賴驅動執行時間"""
        total_time = 0.0
        for phase in phases:
            # 每個階段的時間是該階段最長執行時間
            phase_time = max(
                self.analyst_nodes[aid].estimated_duration for aid in phase
            ) if phase else 0.0
            total_time += phase_time
        return total_time
    
    def _calculate_parallelism_factor(self, phases: List[List[str]]) -> float:
        """計算並行度因子"""
        if not phases:
            return 1.0
        
        total_analysts = sum(len(phase) for phase in phases)
        max_parallel = max(len(phase) for phase in phases)
        
        return total_analysts / (len(phases) * max_parallel) if max_parallel > 0 else 1.0
    
    def _create_adaptive_plan(self, analysts_to_execute: List[str]) -> ExecutionPlan:
        """創建自適應執行計劃"""
        # 自適應策略：結合依賴和並行優化
        dependency_phases = self._create_dependency_phases(analysts_to_execute)
        
        # 優化併行度
        optimized_phases = []
        for phase in dependency_phases:
            if len(phase) > self.max_parallelism:
                # 分割大階段
                chunks = [phase[i:i+self.max_parallelism] 
                         for i in range(0, len(phase), self.max_parallelism)]
                optimized_phases.extend(chunks)
            else:
                optimized_phases.append(phase)
        
        plan = ExecutionPlan(
            execution_strategy=ExecutionStrategy.ADAPTIVE,
            execution_phases=optimized_phases,
            estimated_total_time=self._estimate_dependency_execution_time(optimized_phases),
            parallelism_factor=self._calculate_parallelism_factor(optimized_phases)
        )
        
        return plan
    
    def _allocate_resources(self, phases: List[List[str]]) -> Dict[str, float]:
        """分配資源"""
        allocation = {}
        
        for phase in phases:
            total_weight = sum(
                self.analyst_nodes[aid].resource_weight for aid in phase
            )
            
            for analyst_id in phase:
                weight = self.analyst_nodes[analyst_id].resource_weight
                allocation[analyst_id] = weight / total_weight if total_weight > 0 else 1.0
        
        return allocation
    
    def _assess_execution_risks(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """評估執行風險"""
        risks = {
            'high_parallelism_risk': plan.parallelism_factor > self.max_parallelism,
            'long_execution_risk': plan.estimated_total_time > self.execution_timeout * 0.8,
            'critical_path_risk': self._has_critical_path_risk(plan),
            'resource_contention_risk': self._has_resource_contention_risk(plan),
            'dependency_complexity': len(plan.execution_phases)
        }
        
        # 計算總體風險分數 (0-1)
        risk_factors = [
            0.3 if risks['high_parallelism_risk'] else 0.0,
            0.4 if risks['long_execution_risk'] else 0.0,
            0.2 if risks['critical_path_risk'] else 0.0,
            0.1 if risks['resource_contention_risk'] else 0.0
        ]
        
        risks['overall_risk_score'] = sum(risk_factors)
        
        return risks
    
    def _has_critical_path_risk(self, plan: ExecutionPlan) -> bool:
        """檢查是否存在關鍵路徑風險"""
        for phase in plan.execution_phases:
            for analyst_id in phase:
                if self.analyst_nodes[analyst_id].is_critical:
                    return True
        return False
    
    def _has_resource_contention_risk(self, plan: ExecutionPlan) -> bool:
        """檢查是否存在資源競爭風險"""
        for phase in plan.execution_phases:
            total_resource_demand = sum(
                self.analyst_nodes[aid].resource_weight for aid in phase
            )
            if total_resource_demand > self.max_parallelism:
                return True
        return False
    
    async def execute_workflow(
        self,
        state: AnalysisState,
        execution_plan: ExecutionPlan = None,
        selected_analysts: List[str] = None
    ) -> ExecutionResult:
        """執行工作流"""
        
        session_id = str(uuid.uuid4())
        
        # 創建執行計劃
        if not execution_plan:
            execution_plan = self.create_execution_plan(
                selected_analysts=selected_analysts,
                strategy=ExecutionStrategy.DEPENDENCY_DRIVEN
            )
        
        # 初始化執行結果
        result = ExecutionResult(session_id=session_id)
        result.execution_metadata = {
            'plan_id': execution_plan.plan_id,
            'strategy': execution_plan.execution_strategy.value,
            'phases_count': len(execution_plan.execution_phases),
            'start_time': datetime.now().isoformat()
        }
        
        # 記錄會話
        self.active_sessions[session_id] = {
            'state': state,
            'plan': execution_plan,
            'result': result,
            'current_phase': 0,
            'start_time': datetime.now()
        }
        
        try:
            # 執行所有階段
            for phase_idx, phase_analysts in enumerate(execution_plan.execution_phases):
                self.active_sessions[session_id]['current_phase'] = phase_idx
                
                self.logger.info(f"執行階段 {phase_idx + 1}/{len(execution_plan.execution_phases)}", extra={
                    'session_id': session_id,
                    'phase_analysts': phase_analysts
                })
                
                # 並行執行當前階段的分析師
                await self._execute_phase(session_id, phase_analysts, state, result)
            
            # 結果聚合和衝突解決
            if self.conflict_resolution_enabled:
                await self._resolve_conflicts(result)
            
            # 最終整合
            result.final_integrated_result = await self._integrate_final_result(result)
            
            result.success = True
            result.execution_metadata['end_time'] = datetime.now().isoformat()
            result.execution_metadata['total_duration'] = (
                datetime.now() - self.active_sessions[session_id]['start_time']
            ).total_seconds()
            
            self.logger.info(f"工作流執行完成: {session_id}", extra={
                'successful_analyses': len(result.analyst_results),
                'total_duration': result.execution_metadata['total_duration']
            })
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.execution_metadata['end_time'] = datetime.now().isoformat()
            
            self.logger.error(f"工作流執行失敗: {session_id}", extra={
                'error': str(e)
            })
        
        finally:
            # 清理會話
            if session_id in self.active_sessions:
                del self.active_sessions[session_id]
            
            # 記錄執行歷史
            self.execution_history[session_id] = result
        
        return result
    
    async def _execute_phase(
        self,
        session_id: str,
        phase_analysts: List[str],
        state: AnalysisState,
        result: ExecutionResult
    ):
        """執行單個階段"""
        
        # 創建分析任務
        tasks = []
        for analyst_id in phase_analysts:
            if analyst_id in self.analysts:
                task = self._execute_single_analyst(analyst_id, state, result)
                tasks.append(task)
        
        # 並行執行任務
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_single_analyst(
        self,
        analyst_id: str,
        state: AnalysisState,
        result: ExecutionResult
    ):
        """執行單個分析師"""
        
        analyst = self.analysts[analyst_id]
        start_time = datetime.now()
        
        try:
            # 使用工作流整合的分析方法
            if hasattr(analyst, 'analyze_with_workflow_integration'):
                analysis_result = await analyst.analyze_with_workflow_integration(state)
            else:
                analysis_result = await analyst.analyze(state)
            
            # 記錄結果
            result.analyst_results[analyst_id] = analysis_result
            execution_time = (datetime.now() - start_time).total_seconds()
            result.performance_metrics[f"{analyst_id}_execution_time"] = execution_time
            
            self.logger.info(f"分析師執行成功: {analyst_id}", extra={
                'execution_time': execution_time,
                'recommendation': analysis_result.recommendation,
                'confidence': analysis_result.confidence
            })
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            result.performance_metrics[f"{analyst_id}_execution_time"] = execution_time
            result.performance_metrics[f"{analyst_id}_error"] = str(e)
            
            self.logger.error(f"分析師執行失敗: {analyst_id}", extra={
                'error': str(e),
                'execution_time': execution_time
            })
    
    async def _resolve_conflicts(self, result: ExecutionResult):
        """解決衝突"""
        
        successful_results = list(result.analyst_results.values())
        if len(successful_results) < 2:
            return
        
        # 檢查建議衝突
        recommendations = [r.recommendation for r in successful_results]
        unique_recommendations = set(recommendations)
        
        if len(unique_recommendations) > 1:
            # 存在衝突，需要解決
            conflict_resolution = {
                'conflict_type': 'recommendation_disagreement',
                'conflicting_recommendations': list(unique_recommendations),
                'resolution_method': 'weighted_voting',
                'timestamp': datetime.now().isoformat()
            }
            
            # 加權投票解決衝突
            recommendation_weights = {}
            for analyst_result in successful_results:
                rec = analyst_result.recommendation
                weight = analyst_result.confidence
                
                if rec not in recommendation_weights:
                    recommendation_weights[rec] = 0
                recommendation_weights[rec] += weight
            
            # 選擇權重最高的建議
            resolved_recommendation = max(
                recommendation_weights.items(), 
                key=lambda x: x[1]
            )[0]
            
            conflict_resolution['resolved_recommendation'] = resolved_recommendation
            conflict_resolution['recommendation_weights'] = recommendation_weights
            
            result.conflict_resolutions.append(conflict_resolution)
            
            self.logger.info("解決建議衝突", extra=conflict_resolution)
    
    async def _integrate_final_result(self, result: ExecutionResult) -> AnalysisResult:
        """整合最終結果"""
        
        successful_results = list(result.analyst_results.values())
        if not successful_results:
            # 沒有成功的結果
            return AnalysisResult(
                analyst_id='workflow_orchestrator',
                stock_id='unknown',
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                analysis_type=AnalysisType.INVESTMENT_PLANNING,
                recommendation='HOLD',
                confidence=0.0,
                confidence_level=AnalysisConfidenceLevel.VERY_LOW,
                reasoning=['所有分析師執行失敗']
            )
        
        # 如果有投資規劃師的結果，優先使用
        investment_planner_result = None
        for analyst_id, analyst_result in result.analyst_results.items():
            if 'investment_planner' in analyst_id:
                investment_planner_result = analyst_result
                break
        
        if investment_planner_result:
            return investment_planner_result
        
        # 否則進行簡單整合
        # 使用解決衝突後的建議或多數表決
        if result.conflict_resolutions:
            final_recommendation = result.conflict_resolutions[-1].get(
                'resolved_recommendation', 'HOLD'
            )
        else:
            recommendations = [r.recommendation for r in successful_results]
            final_recommendation = max(set(recommendations), key=recommendations.count)
        
        # 計算平均信心度
        avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results)
        
        # 收集所有理由
        all_reasoning = []
        for result_item in successful_results:
            if result_item.reasoning:
                all_reasoning.extend([
                    f"[{result_item.analyst_id}] {reason}" 
                    for reason in result_item.reasoning[:3]  # 限制每個分析師最多3個理由
                ])
        
        return AnalysisResult(
            analyst_id='workflow_orchestrator_integrated',
            stock_id=successful_results[0].stock_id,
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            analysis_type=AnalysisType.INVESTMENT_PLANNING,
            recommendation=final_recommendation,
            confidence=avg_confidence,
            confidence_level=AnalysisConfidenceLevel.HIGH if avg_confidence > 0.7 else AnalysisConfidenceLevel.MODERATE,
            reasoning=all_reasoning[:10],  # 限制總理由數量
            risk_factors=[f"整合了{len(successful_results)}個分析師的結果"]
        )
    
    def get_registered_analysts(self) -> Dict[str, Dict[str, Any]]:
        """獲取已註冊的分析師信息"""
        return {
            analyst_id: {
                'analyst_info': analyst.get_analyst_info(),
                'workflow_compatibility': (
                    analyst.get_workflow_compatibility() 
                    if hasattr(analyst, 'get_workflow_compatibility') 
                    else {}
                ),
                'node_info': {
                    'dependencies': list(self.analyst_nodes[analyst_id].dependencies),
                    'dependents': list(self.analyst_nodes[analyst_id].dependents),
                    'priority': self.analyst_nodes[analyst_id].execution_priority,
                    'is_critical': self.analyst_nodes[analyst_id].is_critical
                }
            }
            for analyst_id, analyst in self.analysts.items()
        }
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取執行歷史"""
        history = list(self.execution_history.values())
        history.sort(key=lambda x: x.execution_metadata.get('start_time', ''), reverse=True)
        
        return [
            {
                'session_id': result.session_id,
                'success': result.success,
                'analysts_count': len(result.analyst_results),
                'execution_metadata': result.execution_metadata,
                'performance_metrics': result.performance_metrics,
                'has_conflicts': len(result.conflict_resolutions) > 0
            }
            for result in history[:limit]
        ]


# 全局編排器實例
_global_orchestrator: Optional[WorkflowOrchestrator] = None


def get_global_orchestrator(config: Dict[str, Any] = None) -> WorkflowOrchestrator:
    """獲取全局編排器實例"""
    global _global_orchestrator
    
    if _global_orchestrator is None:
        _global_orchestrator = WorkflowOrchestrator(config)
    
    return _global_orchestrator


def register_analyst_to_global(analyst: BaseAnalyst) -> str:
    """向全局編排器註冊分析師"""
    orchestrator = get_global_orchestrator()
    return orchestrator.register_analyst(analyst)


if __name__ == "__main__":
    # 測試腳本
    async def test_workflow_orchestrator():
        print("測試 WorkflowOrchestrator")
        
        # 創建編排器
        orchestrator = WorkflowOrchestrator({
            'max_parallelism': 3,
            'execution_timeout': 60,
            'conflict_resolution_enabled': True
        })
        
        # 創建模擬分析師
        from .base_analyst import AnalysisType
        
        class MockAnalyst(BaseAnalyst):
            def __init__(self, analyst_type: AnalysisType):
                super().__init__({})
                self._analysis_type = analyst_type
                self.analyst_id = f"{analyst_type.value}_analyst"
            
            def get_analysis_type(self) -> AnalysisType:
                return self._analysis_type
            
            def get_analysis_prompt(self, state) -> str:
                return f"分析 {state.stock_id}"
            
            async def analyze(self, state) -> AnalysisResult:
                await asyncio.sleep(0.1)  # 模擬執行時間
                return AnalysisResult(
                    analyst_id=self.analyst_id,
                    stock_id=state.stock_id,
                    analysis_date=state.analysis_date,
                    analysis_type=self._analysis_type,
                    recommendation='BUY',
                    confidence=0.8,
                    confidence_level=AnalysisConfidenceLevel.HIGH,
                    reasoning=[f"{self._analysis_type.value} 分析建議買入"]
                )
        
        # 註冊模擬分析師
        analysts = [
            MockAnalyst(AnalysisType.TECHNICAL),
            MockAnalyst(AnalysisType.FUNDAMENTAL),
            MockAnalyst(AnalysisType.RISK_ASSESSMENT),
            MockAnalyst(AnalysisType.INVESTMENT_PLANNING)
        ]
        
        for analyst in analysts:
            orchestrator.register_analyst(analyst)
        
        print(f"註冊了 {len(analysts)} 個分析師")
        
        # 創建執行計劃
        plan = orchestrator.create_execution_plan(
            strategy=ExecutionStrategy.DEPENDENCY_DRIVEN
        )
        
        print(f"執行計劃: {len(plan.execution_phases)} 個階段")
        for i, phase in enumerate(plan.execution_phases):
            print(f"  階段 {i+1}: {phase}")
        
        # 執行工作流
        from .base_analyst import AnalysisState
        state = AnalysisState(
            stock_id='2330',
            analysis_date=datetime.now().strftime('%Y-%m-%d')
        )
        
        result = await orchestrator.execute_workflow(state, plan)
        
        print(f"執行結果: {'成功' if result.success else '失敗'}")
        print(f"分析師結果數: {len(result.analyst_results)}")
        
        if result.final_integrated_result:
            final = result.final_integrated_result
            print(f"最終建議: {final.recommendation}")
            print(f"信心度: {final.confidence:.2f}")
        
        print("WorkflowOrchestrator 測試完成")
    
    asyncio.run(test_workflow_orchestrator())