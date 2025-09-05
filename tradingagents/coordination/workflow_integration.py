#!/usr/bin/env python3
"""
工作流整合器 (Workflow Integration)
天工開物系統與TradingAgentsGraph工作流引擎的整合模組

此模組提供：
1. TradingAgentsGraph工作流引擎整合
2. 代理人工作流節點定義
3. 工作流執行協調
4. 任務狀態同步
5. 工作流監控和管理
6. 錯誤處理和重試機制

由梁(架構師)和魯班(工匠)聯合設計實現
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging

from .master_weaver import MasterWeaverCoordinator, TaskCoordination, TaskStatus, TaskPriority
from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error
from ..utils.resilience_manager import get_global_resilience_manager

logger = get_system_logger("workflow_integration")

class WorkflowNodeType(Enum):
    """工作流節點類型"""
    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"
    AGENT_TASK = "agent_task"
    CONDITION = "condition"
    LOOP = "loop"

class WorkflowStatus(Enum):
    """工作流狀態"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeExecutionStatus(Enum):
    """節點執行狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WAITING = "waiting"

@dataclass
class WorkflowNode:
    """工作流節點"""
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    node_type: WorkflowNodeType = WorkflowNodeType.TASK
    agent_type: Optional[str] = None  # 指定執行的代理人類型
    task_config: Dict[str, Any] = field(default_factory=dict)
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # 依賴的節點ID
    conditions: Dict[str, Any] = field(default_factory=dict)  # 執行條件
    retry_config: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class WorkflowEdge:
    """工作流邊"""
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_node: str = ""
    to_node: str = ""
    condition: Optional[str] = None  # 條件表達式
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowDefinition:
    """工作流定義"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    nodes: List[WorkflowNode] = field(default_factory=list)
    edges: List[WorkflowEdge] = field(default_factory=list)
    global_config: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = "天工開物系統"

@dataclass
class NodeExecution:
    """節點執行記錄"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = ""
    workflow_instance_id: str = ""
    status: NodeExecutionStatus = NodeExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    assigned_agent: Optional[str] = None
    execution_logs: List[str] = field(default_factory=list)

@dataclass
class WorkflowInstance:
    """工作流實例"""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    name: str = ""
    status: WorkflowStatus = WorkflowStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    current_nodes: List[str] = field(default_factory=list)  # 當前執行的節點
    completed_nodes: List[str] = field(default_factory=list)  # 已完成的節點
    failed_nodes: List[str] = field(default_factory=list)  # 失敗的節點
    node_executions: Dict[str, NodeExecution] = field(default_factory=dict)
    context_variables: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    created_by: str = "天工開物系統"

class WorkflowNodeExecutor:
    """工作流節點執行器"""
    
    def __init__(self, coordinator: MasterWeaverCoordinator):
        self.coordinator = coordinator
        self.resilience_manager = get_global_resilience_manager()
        self.execution_handlers = {
            WorkflowNodeType.AGENT_TASK: self._execute_agent_task,
            WorkflowNodeType.TASK: self._execute_generic_task,
            WorkflowNodeType.DECISION: self._execute_decision,
            WorkflowNodeType.CONDITION: self._execute_condition,
            WorkflowNodeType.START: self._execute_start,
            WorkflowNodeType.END: self._execute_end
        }
    
    async def execute_node(self, 
                          node: WorkflowNode, 
                          instance: WorkflowInstance,
                          input_data: Dict[str, Any] = None) -> NodeExecution:
        """執行工作流節點"""
        
        execution = NodeExecution(
            node_id=node.node_id,
            workflow_instance_id=instance.instance_id,
            input_data=input_data or {},
            started_at=datetime.now()
        )
        
        try:
            execution.status = NodeExecutionStatus.RUNNING
            execution.execution_logs.append(f"開始執行節點: {node.name}")
            
            # 根據節點類型執行相應處理
            handler = self.execution_handlers.get(node.node_type, self._execute_generic_task)
            
            # 使用彈性機制執行
            output_data = await self.resilience_manager.execute_with_resilience(
                operation_name=f"workflow_node_{node.node_id}",
                func=handler,
                node=node,
                instance=instance,
                input_data=execution.input_data,
                timeout=node.timeout_seconds
            )
            
            execution.output_data = output_data or {}
            execution.status = NodeExecutionStatus.COMPLETED
            execution.completed_at = datetime.now()
            execution.execution_logs.append(f"節點執行完成: {node.name}")
            
            logger.info(f"工作流節點執行成功: {node.name}", extra={
                'node_id': node.node_id,
                'execution_id': execution.execution_id,
                'duration': (execution.completed_at - execution.started_at).total_seconds()
            })
            
        except Exception as e:
            execution.status = NodeExecutionStatus.FAILED
            execution.completed_at = datetime.now()
            execution.error_message = str(e)
            execution.execution_logs.append(f"節點執行失敗: {str(e)}")
            
            logger.error(f"工作流節點執行失敗: {node.name}", extra={
                'node_id': node.node_id,
                'execution_id': execution.execution_id,
                'error': str(e)
            })
            
            raise
        
        return execution
    
    async def _execute_agent_task(self, 
                                 node: WorkflowNode, 
                                 instance: WorkflowInstance, 
                                 input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行代理人任務節點"""
        
        # 創建任務協調對象
        task = TaskCoordination(
            task_id=f"workflow_{instance.instance_id}_{node.node_id}",
            name=node.name,
            description=f"工作流任務: {node.name}",
            task_type=node.task_config.get('task_type', 'general'),
            priority=TaskPriority(node.task_config.get('priority', 'medium')),
            estimated_hours=node.task_config.get('estimated_hours', 1),
            requirements=node.task_config.get('requirements', []),
            metadata={
                'workflow_instance_id': instance.instance_id,
                'workflow_node_id': node.node_id,
                'node_type': node.node_type.value,
                'agent_type_preference': node.agent_type,
                **input_data
            }
        )
        
        # 通過協調器執行任務
        result = await self.coordinator.coordinate_task(task)
        
        # 返回執行結果
        return {
            'task_result': result.to_dict() if hasattr(result, 'to_dict') else str(result),
            'success': result.success if hasattr(result, 'success') else True,
            'output': result.output if hasattr(result, 'output') else {},
            'execution_time': result.execution_time if hasattr(result, 'execution_time') else 0
        }
    
    async def _execute_generic_task(self, 
                                   node: WorkflowNode, 
                                   instance: WorkflowInstance, 
                                   input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行通用任務節點"""
        
        # 模擬任務執行
        await asyncio.sleep(0.1)
        
        return {
            'status': 'completed',
            'message': f'任務 {node.name} 執行完成',
            'processed_data': input_data,
            'timestamp': datetime.now().isoformat()
        }
    
    async def _execute_decision(self, 
                               node: WorkflowNode, 
                               instance: WorkflowInstance, 
                               input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行決策節點"""
        
        # 評估決策條件
        conditions = node.conditions
        decision_result = {}
        
        for condition_name, condition_expr in conditions.items():
            # 簡化的條件評估
            try:
                # 在實際實現中，這裡應該有更安全的表達式評估
                result = eval(condition_expr, {"input": input_data, "context": instance.context_variables})
                decision_result[condition_name] = result
            except Exception as e:
                logger.warning(f"條件評估失敗 {condition_name}: {e}")
                decision_result[condition_name] = False
        
        return {
            'decision_results': decision_result,
            'primary_decision': any(decision_result.values()),
            'evaluated_conditions': list(conditions.keys())
        }
    
    async def _execute_condition(self, 
                                node: WorkflowNode, 
                                instance: WorkflowInstance, 
                                input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行條件節點"""
        
        condition_expr = node.conditions.get('expression', 'True')
        
        try:
            result = eval(condition_expr, {"input": input_data, "context": instance.context_variables})
            return {
                'condition_result': bool(result),
                'expression': condition_expr,
                'evaluation_success': True
            }
        except Exception as e:
            logger.error(f"條件表達式評估失敗: {e}")
            return {
                'condition_result': False,
                'expression': condition_expr,
                'evaluation_success': False,
                'error': str(e)
            }
    
    async def _execute_start(self, 
                            node: WorkflowNode, 
                            instance: WorkflowInstance, 
                            input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行開始節點"""
        return {
            'status': 'started',
            'workflow_instance_id': instance.instance_id,
            'started_at': datetime.now().isoformat()
        }
    
    async def _execute_end(self, 
                          node: WorkflowNode, 
                          instance: WorkflowInstance, 
                          input_data: Dict[str, Any]) -> Dict[str, Any]:
        """執行結束節點"""
        return {
            'status': 'ended',
            'workflow_instance_id': instance.instance_id,
            'ended_at': datetime.now().isoformat(),
            'final_output': input_data
        }

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self, coordinator: MasterWeaverCoordinator):
        self.coordinator = coordinator
        self.node_executor = WorkflowNodeExecutor(coordinator)
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.workflow_instances: Dict[str, WorkflowInstance] = {}
        self.running_instances: Dict[str, asyncio.Task] = {}
    
    def register_workflow(self, workflow_def: WorkflowDefinition):
        """註冊工作流定義"""
        self.workflow_definitions[workflow_def.workflow_id] = workflow_def
        logger.info(f"註冊工作流定義: {workflow_def.name} ({workflow_def.workflow_id})")
    
    async def start_workflow(self, 
                           workflow_id: str, 
                           input_data: Dict[str, Any] = None,
                           instance_name: str = None) -> WorkflowInstance:
        """啟動工作流實例"""
        
        if workflow_id not in self.workflow_definitions:
            raise ValueError(f"工作流定義不存在: {workflow_id}")
        
        workflow_def = self.workflow_definitions[workflow_id]
        
        # 創建工作流實例
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            name=instance_name or f"{workflow_def.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            input_data=input_data or {},
            context_variables=workflow_def.variables.copy(),
            started_at=datetime.now()
        )
        
        # 初始化上下文變量
        instance.context_variables.update(input_data or {})
        
        self.workflow_instances[instance.instance_id] = instance
        
        # 開始執行工作流
        execution_task = asyncio.create_task(self._execute_workflow_instance(instance))
        self.running_instances[instance.instance_id] = execution_task
        
        logger.info(f"啟動工作流實例: {instance.name} ({instance.instance_id})")
        
        return instance
    
    async def _execute_workflow_instance(self, instance: WorkflowInstance):
        """執行工作流實例"""
        
        try:
            instance.status = WorkflowStatus.RUNNING
            workflow_def = self.workflow_definitions[instance.workflow_id]
            
            # 查找開始節點
            start_nodes = [node for node in workflow_def.nodes if node.node_type == WorkflowNodeType.START]
            if not start_nodes:
                start_nodes = [node for node in workflow_def.nodes if not node.dependencies]
            
            if not start_nodes:
                raise ValueError("工作流中找不到開始節點")
            
            # 初始化當前執行節點
            instance.current_nodes = [node.node_id for node in start_nodes]
            
            # 執行工作流
            await self._execute_workflow_nodes(instance, workflow_def)
            
            # 檢查完成狀態
            if instance.failed_nodes:
                instance.status = WorkflowStatus.FAILED
                instance.error_message = f"節點執行失敗: {', '.join(instance.failed_nodes)}"
            else:
                instance.status = WorkflowStatus.COMPLETED
            
            instance.completed_at = datetime.now()
            
            logger.info(f"工作流實例執行完成: {instance.name}", extra={
                'instance_id': instance.instance_id,
                'status': instance.status.value,
                'duration': (instance.completed_at - instance.started_at).total_seconds(),
                'completed_nodes': len(instance.completed_nodes),
                'failed_nodes': len(instance.failed_nodes)
            })
            
        except Exception as e:
            instance.status = WorkflowStatus.FAILED
            instance.error_message = str(e)
            instance.completed_at = datetime.now()
            
            logger.error(f"工作流實例執行失敗: {instance.name}", extra={
                'instance_id': instance.instance_id,
                'error': str(e)
            })
            
        finally:
            # 清理運行實例記錄
            if instance.instance_id in self.running_instances:
                del self.running_instances[instance.instance_id]
    
    async def _execute_workflow_nodes(self, instance: WorkflowInstance, workflow_def: WorkflowDefinition):
        """執行工作流節點"""
        
        nodes_map = {node.node_id: node for node in workflow_def.nodes}
        edges_map = {edge.from_node: [] for edge in workflow_def.edges}
        
        # 構建邊映射
        for edge in workflow_def.edges:
            if edge.from_node not in edges_map:
                edges_map[edge.from_node] = []
            edges_map[edge.from_node].append(edge)
        
        while instance.current_nodes and instance.status == WorkflowStatus.RUNNING:
            next_nodes = []
            
            # 並行執行當前節點
            current_executions = []
            for node_id in instance.current_nodes:
                if node_id not in nodes_map:
                    logger.warning(f"節點不存在: {node_id}")
                    continue
                
                node = nodes_map[node_id]
                
                # 檢查依賴是否滿足
                if self._check_dependencies_satisfied(node, instance):
                    execution_task = self._execute_single_node(node, instance)
                    current_executions.append((node_id, execution_task))
                else:
                    # 依賴未滿足，等待下一輪
                    next_nodes.append(node_id)
            
            # 等待當前節點執行完成
            execution_results = []
            if current_executions:
                tasks = [task for _, task in current_executions]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for (node_id, _), result in zip(current_executions, results):
                    if isinstance(result, Exception):
                        instance.failed_nodes.append(node_id)
                        logger.error(f"節點執行異常: {node_id} - {result}")
                    else:
                        instance.completed_nodes.append(node_id)
                        instance.node_executions[node_id] = result
                        
                        # 確定下一個節點
                        node_next = self._determine_next_nodes(node_id, result, edges_map, workflow_def)
                        next_nodes.extend(node_next)
            
            # 更新當前節點
            instance.current_nodes = list(set(next_nodes))
            
            # 檢查是否有結束節點
            end_nodes = [node for node in workflow_def.nodes if node.node_type == WorkflowNodeType.END]
            if end_nodes and any(node.node_id in instance.completed_nodes for node in end_nodes):
                break
            
            # 避免無限循環
            if not instance.current_nodes and not instance.failed_nodes:
                break
    
    def _check_dependencies_satisfied(self, node: WorkflowNode, instance: WorkflowInstance) -> bool:
        """檢查節點依賴是否滿足"""
        for dep_node_id in node.dependencies:
            if dep_node_id not in instance.completed_nodes:
                return False
        return True
    
    async def _execute_single_node(self, node: WorkflowNode, instance: WorkflowInstance) -> NodeExecution:
        """執行單個節點"""
        
        # 準備輸入數據
        input_data = self._prepare_node_input_data(node, instance)
        
        # 執行節點
        execution = await self.node_executor.execute_node(node, instance, input_data)
        
        # 更新上下文變量
        if execution.output_data:
            instance.context_variables.update(execution.output_data)
        
        return execution
    
    def _prepare_node_input_data(self, node: WorkflowNode, instance: WorkflowInstance) -> Dict[str, Any]:
        """準備節點輸入數據"""
        input_data = {}
        
        # 添加工作流輸入數據
        input_data.update(instance.input_data)
        
        # 添加上下文變量
        input_data.update(instance.context_variables)
        
        # 添加依賴節點的輸出
        for dep_node_id in node.dependencies:
            if dep_node_id in instance.node_executions:
                dep_execution = instance.node_executions[dep_node_id]
                input_data[f"dep_{dep_node_id}_output"] = dep_execution.output_data
        
        return input_data
    
    def _determine_next_nodes(self, 
                             current_node_id: str, 
                             execution: NodeExecution, 
                             edges_map: Dict[str, List[WorkflowEdge]], 
                             workflow_def: WorkflowDefinition) -> List[str]:
        """確定下一個執行節點"""
        
        next_nodes = []
        
        if current_node_id in edges_map:
            for edge in edges_map[current_node_id]:
                # 檢查邊條件
                if edge.condition:
                    try:
                        # 簡化的條件評估
                        condition_result = eval(edge.condition, {
                            "output": execution.output_data,
                            "success": execution.status == NodeExecutionStatus.COMPLETED
                        })
                        
                        if condition_result:
                            next_nodes.append(edge.to_node)
                    except Exception as e:
                        logger.warning(f"邊條件評估失敗 {edge.edge_id}: {e}")
                else:
                    next_nodes.append(edge.to_node)
        
        return next_nodes
    
    async def get_workflow_status(self, instance_id: str) -> Optional[WorkflowInstance]:
        """獲取工作流狀態"""
        return self.workflow_instances.get(instance_id)
    
    async def pause_workflow(self, instance_id: str):
        """暫停工作流"""
        if instance_id in self.workflow_instances:
            instance = self.workflow_instances[instance_id]
            instance.status = WorkflowStatus.PAUSED
            logger.info(f"暫停工作流實例: {instance_id}")
    
    async def resume_workflow(self, instance_id: str):
        """恢復工作流"""
        if instance_id in self.workflow_instances:
            instance = self.workflow_instances[instance_id]
            if instance.status == WorkflowStatus.PAUSED:
                instance.status = WorkflowStatus.RUNNING
                logger.info(f"恢復工作流實例: {instance_id}")
    
    async def cancel_workflow(self, instance_id: str):
        """取消工作流"""
        if instance_id in self.workflow_instances:
            instance = self.workflow_instances[instance_id]
            instance.status = WorkflowStatus.CANCELLED
            instance.completed_at = datetime.now()
            
            # 取消運行任務
            if instance_id in self.running_instances:
                task = self.running_instances[instance_id]
                task.cancel()
                del self.running_instances[instance_id]
            
            logger.info(f"取消工作流實例: {instance_id}")

class TradingAgentsWorkflowBuilder:
    """交易系統工作流構建器"""
    
    @staticmethod
    def create_trading_enhancement_workflow() -> WorkflowDefinition:
        """創建交易系統增強工作流"""
        
        # 定義節點
        nodes = [
            # 開始節點
            WorkflowNode(
                node_id="start",
                name="開始",
                node_type=WorkflowNodeType.START
            ),
            
            # 架構分析節點
            WorkflowNode(
                node_id="architecture_analysis",
                name="系統架構分析",
                node_type=WorkflowNodeType.AGENT_TASK,
                agent_type="code_architect_liang",
                task_config={
                    "task_type": "architecture_analysis",
                    "priority": "high",
                    "estimated_hours": 2
                },
                dependencies=["start"]
            ),
            
            # 代碼實現節點
            WorkflowNode(
                node_id="code_implementation",
                name="代碼實現",
                node_type=WorkflowNodeType.AGENT_TASK,
                agent_type="code_artisan_luban",
                task_config={
                    "task_type": "code_implementation",
                    "priority": "high",
                    "estimated_hours": 6
                },
                dependencies=["architecture_analysis"]
            ),
            
            # 測試節點
            WorkflowNode(
                node_id="quality_testing",
                name="品質測試",
                node_type=WorkflowNodeType.AGENT_TASK,
                agent_type="qa_guardian_direnjie",
                task_config={
                    "task_type": "testing",
                    "priority": "high",
                    "estimated_hours": 3
                },
                dependencies=["code_implementation"]
            ),
            
            # 安全審計節點
            WorkflowNode(
                node_id="security_audit",
                name="安全審計",
                node_type=WorkflowNodeType.AGENT_TASK,
                agent_type="security_advisor_baozhen",
                task_config={
                    "task_type": "security_audit",
                    "priority": "high",
                    "estimated_hours": 2
                },
                dependencies=["code_implementation"]
            ),
            
            # 決策節點 - 檢查測試和安全結果
            WorkflowNode(
                node_id="quality_gate",
                name="品質門檻",
                node_type=WorkflowNodeType.DECISION,
                conditions={
                    "tests_passed": "input.get('test_success', False)",
                    "security_passed": "input.get('security_success', False)"
                },
                dependencies=["quality_testing", "security_audit"]
            ),
            
            # 文檔編寫節點
            WorkflowNode(
                node_id="documentation",
                name="文檔編寫",
                node_type=WorkflowNodeType.AGENT_TASK,
                agent_type="doc_scribe_sima",
                task_config={
                    "task_type": "documentation",
                    "priority": "medium",
                    "estimated_hours": 2
                },
                dependencies=["quality_gate"]
            ),
            
            # 部署準備節點
            WorkflowNode(
                node_id="deployment_preparation",
                name="部署準備",
                node_type=WorkflowNodeType.AGENT_TASK,
                agent_type="devops_engineer_mozi",
                task_config={
                    "task_type": "deployment_preparation",
                    "priority": "high",
                    "estimated_hours": 2
                },
                dependencies=["quality_gate"]
            ),
            
            # 結束節點
            WorkflowNode(
                node_id="end",
                name="完成",
                node_type=WorkflowNodeType.END,
                dependencies=["documentation", "deployment_preparation"]
            )
        ]
        
        # 定義邊
        edges = [
            WorkflowEdge(from_node="start", to_node="architecture_analysis"),
            WorkflowEdge(from_node="architecture_analysis", to_node="code_implementation"),
            WorkflowEdge(from_node="code_implementation", to_node="quality_testing"),
            WorkflowEdge(from_node="code_implementation", to_node="security_audit"),
            WorkflowEdge(from_node="quality_testing", to_node="quality_gate"),
            WorkflowEdge(from_node="security_audit", to_node="quality_gate"),
            WorkflowEdge(
                from_node="quality_gate", 
                to_node="documentation",
                condition="output.get('decision_results', {}).get('tests_passed', False) and output.get('decision_results', {}).get('security_passed', False)"
            ),
            WorkflowEdge(
                from_node="quality_gate", 
                to_node="deployment_preparation",
                condition="output.get('decision_results', {}).get('tests_passed', False) and output.get('decision_results', {}).get('security_passed', False)"
            ),
            WorkflowEdge(from_node="documentation", to_node="end"),
            WorkflowEdge(from_node="deployment_preparation", to_node="end")
        ]
        
        return WorkflowDefinition(
            name="交易系統增強工作流",
            description="完整的交易系統增強開發流程，包含架構設計、代碼實現、測試、安全審計、文檔和部署",
            nodes=nodes,
            edges=edges,
            global_config={
                "max_retry_attempts": 3,
                "timeout_minutes": 30,
                "enable_parallel_execution": True
            },
            variables={
                "project_name": "TradingAgents增強",
                "target_environment": "production",
                "quality_threshold": 0.9
            }
        )

class WorkflowIntegrationManager:
    """工作流整合管理器"""
    
    def __init__(self, coordinator: MasterWeaverCoordinator):
        self.coordinator = coordinator
        self.workflow_engine = WorkflowEngine(coordinator)
        self.predefined_workflows = {}
        
        # 註冊預定義工作流
        self._register_predefined_workflows()
    
    def _register_predefined_workflows(self):
        """註冊預定義工作流"""
        
        # 註冊交易系統增強工作流
        trading_workflow = TradingAgentsWorkflowBuilder.create_trading_enhancement_workflow()
        self.workflow_engine.register_workflow(trading_workflow)
        self.predefined_workflows["trading_enhancement"] = trading_workflow.workflow_id
        
        logger.info("已註冊預定義工作流", extra={
            'workflows_count': len(self.predefined_workflows),
            'workflows': list(self.predefined_workflows.keys())
        })
    
    async def execute_trading_enhancement_workflow(self, 
                                                 project_config: Dict[str, Any] = None) -> WorkflowInstance:
        """執行交易系統增強工作流"""
        
        workflow_id = self.predefined_workflows["trading_enhancement"]
        
        input_data = {
            "project_config": project_config or {},
            "enhancement_requirements": [
                "性能優化",
                "安全加強",
                "監控改善",
                "文檔完善"
            ],
            "target_metrics": {
                "performance_improvement": 0.3,
                "security_score": 0.95,
                "test_coverage": 0.9
            }
        }
        
        instance = await self.workflow_engine.start_workflow(
            workflow_id=workflow_id,
            input_data=input_data,
            instance_name=f"交易系統增強_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        logger.info(f"啟動交易系統增強工作流: {instance.instance_id}")
        
        return instance
    
    async def get_workflow_status(self, instance_id: str) -> Optional[WorkflowInstance]:
        """獲取工作流狀態"""
        return await self.workflow_engine.get_workflow_status(instance_id)
    
    async def create_custom_workflow(self, workflow_def: WorkflowDefinition) -> str:
        """創建自定義工作流"""
        self.workflow_engine.register_workflow(workflow_def)
        return workflow_def.workflow_id
    
    async def list_available_workflows(self) -> Dict[str, Dict[str, str]]:
        """列出可用工作流"""
        workflows = {}
        
        for name, workflow_id in self.predefined_workflows.items():
            workflow_def = self.workflow_engine.workflow_definitions[workflow_id]
            workflows[name] = {
                "workflow_id": workflow_id,
                "name": workflow_def.name,
                "description": workflow_def.description,
                "version": workflow_def.version,
                "nodes_count": len(workflow_def.nodes)
            }
        
        return workflows

if __name__ == "__main__":
    # 測試腳本
    async def test_workflow_integration():
        print("測試工作流整合...")
        
        # 創建模擬協調器
        from .master_weaver import MasterWeaverCoordinator
        coordinator = MasterWeaverCoordinator()
        
        # 創建工作流整合管理器
        workflow_manager = WorkflowIntegrationManager(coordinator)
        
        # 執行交易系統增強工作流
        project_config = {
            "project_name": "TradingAgents V2.0",
            "requirements": ["高性能", "高安全性", "易維護"],
            "timeline": "30天"
        }
        
        instance = await workflow_manager.execute_trading_enhancement_workflow(project_config)
        
        print(f"工作流實例已啟動: {instance.instance_id}")
        print(f"工作流名稱: {instance.name}")
        
        # 等待一段時間並檢查狀態
        await asyncio.sleep(2)
        
        status = await workflow_manager.get_workflow_status(instance.instance_id)
        if status:
            print(f"工作流狀態: {status.status.value}")
            print(f"已完成節點: {len(status.completed_nodes)}")
            print(f"當前執行節點: {status.current_nodes}")
        
        # 列出可用工作流
        available_workflows = await workflow_manager.list_available_workflows()
        print(f"可用工作流: {list(available_workflows.keys())}")
        
        print("工作流整合測試完成")
    
    asyncio.run(test_workflow_integration())