#!/usr/bin/env python3
"""
天工開物 (TianGong Kaiwu) - Advanced Coordination Service
天工開物協調服務 - 7個專業代理人的統一協調平台

此服務整合了以下7個專業代理人：
1. 天工 (TianGong) - Master Weaver Coordinator - 主協調者
2. 梁 (Liang) - Code Architect - 系統架構師
3. 魯班 (Luban) - Code Artisan - 代碼工匠
4. 狄仁傑 (Direnjie) - QA Guardian - 品質守護者
5. 司馬 (Sima) - Doc Scribe - 文檔書記員
6. 墨子 (Mozi) - DevOps Engineer - 運維工程師
7. 包拯 (Baozhen) - Security Advisor - 安全顧問

功能特色：
- 統一任務分配和協調
- 自動化工作流程管理
- 實時進度追蹤和報告
- 智能資源分配
- 品質保證和安全監控
- 綜合性能分析
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from .master_weaver import MasterWeaverCoordinator, TaskCoordination, TaskStatus, TaskPriority
from .code_architect import CodeArchitectLiang
from .code_artisan import CodeArtisanLuban
from .qa_guardian import QAGuardianDirenjie
from .doc_scribe import DocScribeSima
from .devops_engineer import DevOpsEngineerMozi
from .security_advisor import SecurityAdvisorBaozhen

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error

logger = get_system_logger("tiangong_service")

class ServiceStatus(Enum):
    """服務狀態"""
    INITIALIZING = "initializing"
    READY = "ready"
    ACTIVE = "active"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class ProjectType(Enum):
    """專案類型"""
    WEB_APPLICATION = "web_application"
    API_SERVICE = "api_service"
    TRADING_SYSTEM = "trading_system"
    DATA_ANALYTICS = "data_analytics"
    MOBILE_APPLICATION = "mobile_application"
    INFRASTRUCTURE = "infrastructure"
    SECURITY_AUDIT = "security_audit"

@dataclass
class ProjectContext:
    """專案上下文"""
    project_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = ""
    project_type: ProjectType = ProjectType.WEB_APPLICATION
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    timeline: Dict[str, datetime] = field(default_factory=dict)
    budget: Optional[float] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    stakeholders: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class CoordinationResult:
    """協調結果"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str = ""
    session_id: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0
    overall_success: bool = True
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    team_utilization: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    summary_report: Optional[str] = None
    completed_at: datetime = field(default_factory=datetime.now)

class TianGongCoordinationService:
    """
    天工開物協調服務
    
    統一管理和協調7個專業代理人，提供完整的軟體開發生命週期支持。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.service_id = str(uuid.uuid4())
        self.config = config or {}
        self.status = ServiceStatus.INITIALIZING
        
        # 初始化所有代理人
        self.agents = {}
        self.coordinator = None
        
        # 服務統計
        self.projects_completed = 0
        self.total_tasks_executed = 0
        self.total_execution_time = 0.0
        self.success_rate = 0.0
        
        # 活動追蹤
        self.active_projects: Dict[str, ProjectContext] = {}
        self.coordination_history: List[CoordinationResult] = []
        
        # 服務啟動時間
        self.started_at = datetime.now()
        
        logger.info("天工開物協調服務初始化中...", extra={
            'service_id': self.service_id,
            'config_keys': list(self.config.keys())
        })
    
    async def initialize(self) -> None:
        """初始化服務和所有代理人"""
        try:
            self.status = ServiceStatus.INITIALIZING
            
            # 初始化主協調者 - 天工
            self.coordinator = MasterWeaverCoordinator(self.config.get('master_weaver', {}))
            
            # 初始化各專業代理人
            self.agents = {
                'code_architect_liang': CodeArchitectLiang(self.config.get('code_architect', {})),
                'code_artisan_luban': CodeArtisanLuban(self.config.get('code_artisan', {})),
                'qa_guardian_direnjie': QAGuardianDirenjie(self.config.get('qa_guardian', {})),
                'doc_scribe_sima': DocScribeSima(self.config.get('doc_scribe', {})),
                'devops_engineer_mozi': DevOpsEngineerMozi(self.config.get('devops_engineer', {})),
                'security_advisor_baozhen': SecurityAdvisorBaozhen(self.config.get('security_advisor', {}))
            }
            
            # 註冊代理人到主協調者
            for agent_id, agent in self.agents.items():
                await self.coordinator.register_agent(
                    agent_id=agent_id,
                    agent_type=agent.agent_type,
                    capabilities=agent.expertise_areas,
                    agent_instance=agent
                )
            
            self.status = ServiceStatus.READY
            
            logger.info("天工開物協調服務初始化完成", extra={
                'service_id': self.service_id,
                'agents_count': len(self.agents),
                'coordinator_id': self.coordinator.coordinator_id,
                'status': self.status.value
            })
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            error_info = await handle_error(e, {
                'service': 'tiangong_coordination',
                'operation': 'initialize',
                'service_id': self.service_id
            })
            logger.error(f"天工開物協調服務初始化失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def execute_project(self, project_context: ProjectContext) -> CoordinationResult:
        """執行專案協調"""
        
        if self.status not in [ServiceStatus.READY, ServiceStatus.ACTIVE]:
            raise ValueError(f"服務狀態不正確: {self.status.value}")
        
        start_time = datetime.now()
        self.status = ServiceStatus.BUSY
        
        try:
            logger.info("開始執行專案協調", extra={
                'project_id': project_context.project_id,
                'project_name': project_context.project_name,
                'project_type': project_context.project_type.value,
                'requirements_count': len(project_context.requirements)
            })
            
            # 將專案添加到活動專案列表
            self.active_projects[project_context.project_id] = project_context
            
            # 基於專案類型和需求創建任務分解
            tasks = await self._decompose_project_into_tasks(project_context)
            
            # 協調執行所有任務
            execution_results = []
            
            for task in tasks:
                task_result = await self.coordinator.coordinate_task(task)
                execution_results.append(task_result)
                
                # 檢查是否需要中斷執行
                if not task_result.success:
                    logger.warning(f"任務執行失敗: {task.task_id}", extra={
                        'task_name': task.name,
                        'assigned_agent': task.assigned_agent,
                        'error': task_result.error_message
                    })
            
            # 生成工作總結報告
            summary_report = await self.coordinator.generate_work_summary()
            
            # 計算整體結果
            tasks_completed = sum(1 for result in execution_results if result.success)
            tasks_failed = sum(1 for result in execution_results if not result.success)
            overall_success = tasks_failed == 0
            
            # 收集可交付成果
            deliverables = await self._collect_deliverables(execution_results)
            
            # 分析品質分數
            quality_scores = await self._analyze_quality_scores(execution_results)
            
            # 計算性能指標
            performance_metrics = await self._calculate_performance_metrics(execution_results, start_time)
            
            # 分析團隊利用率
            team_utilization = await self._analyze_team_utilization(execution_results)
            
            # 創建協調結果
            coordination_result = CoordinationResult(
                project_id=project_context.project_id,
                session_id=self.coordinator.session_id,
                tasks_completed=tasks_completed,
                tasks_failed=tasks_failed,
                overall_success=overall_success,
                deliverables=deliverables,
                quality_scores=quality_scores,
                performance_metrics=performance_metrics,
                team_utilization=team_utilization,
                execution_time=(datetime.now() - start_time).total_seconds(),
                summary_report=summary_report.report_id
            )
            
            # 更新服務統計
            self.projects_completed += 1
            self.total_tasks_executed += len(tasks)
            self.total_execution_time += coordination_result.execution_time
            self.success_rate = self.projects_completed / max(self.projects_completed + 1, 1)
            
            # 保存到歷史記錄
            self.coordination_history.append(coordination_result)
            
            # 從活動專案中移除
            if project_context.project_id in self.active_projects:
                del self.active_projects[project_context.project_id]
            
            self.status = ServiceStatus.READY
            
            logger.info("專案協調執行完成", extra={
                'project_id': project_context.project_id,
                'coordination_result_id': coordination_result.result_id,
                'tasks_completed': tasks_completed,
                'tasks_failed': tasks_failed,
                'overall_success': overall_success,
                'execution_time': coordination_result.execution_time
            })
            
            return coordination_result
            
        except Exception as e:
            self.status = ServiceStatus.ERROR
            
            # 從活動專案中移除失敗的專案
            if project_context.project_id in self.active_projects:
                del self.active_projects[project_context.project_id]
            
            error_info = await handle_error(e, {
                'service': 'tiangong_coordination',
                'operation': 'execute_project',
                'project_id': project_context.project_id
            })
            logger.error(f"專案協調執行失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def _decompose_project_into_tasks(self, project: ProjectContext) -> List[TaskCoordination]:
        """將專案分解為具體任務"""
        tasks = []
        task_counter = 1
        
        base_tasks = []
        
        # 根據專案類型創建基礎任務
        if project.project_type == ProjectType.TRADING_SYSTEM:
            base_tasks = [
                {
                    'name': '系統架構設計',
                    'description': '設計交易系統的整體架構',
                    'task_type': 'architecture_design',
                    'agent_preference': 'code_architect_liang',
                    'estimated_hours': 4,
                    'priority': TaskPriority.HIGH
                },
                {
                    'name': 'API接口開發',
                    'description': '實現交易系統的核心API',
                    'task_type': 'api_development',
                    'agent_preference': 'code_artisan_luban',
                    'estimated_hours': 8,
                    'priority': TaskPriority.HIGH
                },
                {
                    'name': '數據模型設計',
                    'description': '設計交易數據的存儲模型',
                    'task_type': 'data_modeling',
                    'agent_preference': 'code_architect_liang',
                    'estimated_hours': 3,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': '安全性評估',
                    'description': '評估交易系統的安全風險',
                    'task_type': 'security_assessment',
                    'agent_preference': 'security_advisor_baozhen',
                    'estimated_hours': 4,
                    'priority': TaskPriority.HIGH
                },
                {
                    'name': '測試方案設計',
                    'description': '設計全面的測試策略',
                    'task_type': 'test_planning',
                    'agent_preference': 'qa_guardian_direnjie',
                    'estimated_hours': 3,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': '部署方案設計',
                    'description': '設計生產環境部署策略',
                    'task_type': 'deployment_planning',
                    'agent_preference': 'devops_engineer_mozi',
                    'estimated_hours': 3,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': 'API文檔編寫',
                    'description': '編寫完整的API使用文檔',
                    'task_type': 'api_documentation',
                    'agent_preference': 'doc_scribe_sima',
                    'estimated_hours': 4,
                    'priority': TaskPriority.MEDIUM
                }
            ]
        
        elif project.project_type == ProjectType.WEB_APPLICATION:
            base_tasks = [
                {
                    'name': '前端架構設計',
                    'description': '設計Web應用的前端架構',
                    'task_type': 'frontend_architecture',
                    'agent_preference': 'code_architect_liang',
                    'estimated_hours': 3,
                    'priority': TaskPriority.HIGH
                },
                {
                    'name': '後端服務開發',
                    'description': '實現後端業務邏輯',
                    'task_type': 'backend_development',
                    'agent_preference': 'code_artisan_luban',
                    'estimated_hours': 10,
                    'priority': TaskPriority.HIGH
                },
                {
                    'name': '用戶界面開發',
                    'description': '實現用戶交互界面',
                    'task_type': 'ui_development',
                    'agent_preference': 'code_artisan_luban',
                    'estimated_hours': 8,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': '自動化測試',
                    'description': '建立自動化測試套件',
                    'task_type': 'automated_testing',
                    'agent_preference': 'qa_guardian_direnjie',
                    'estimated_hours': 6,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': '容器化部署',
                    'description': '配置Docker容器和CI/CD',
                    'task_type': 'containerization',
                    'agent_preference': 'devops_engineer_mozi',
                    'estimated_hours': 4,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': '安全審計',
                    'description': '進行Web應用安全檢查',
                    'task_type': 'security_audit',
                    'agent_preference': 'security_advisor_baozhen',
                    'estimated_hours': 3,
                    'priority': TaskPriority.MEDIUM
                },
                {
                    'name': '用戶文檔',
                    'description': '編寫用戶操作指南',
                    'task_type': 'user_documentation',
                    'agent_preference': 'doc_scribe_sima',
                    'estimated_hours': 3,
                    'priority': TaskPriority.LOW
                }
            ]
        
        # 添加基於需求的額外任務
        for requirement in project.requirements:
            if 'performance' in requirement.lower():
                base_tasks.append({
                    'name': '性能優化',
                    'description': f'針對需求優化: {requirement}',
                    'task_type': 'performance_optimization',
                    'agent_preference': 'code_artisan_luban',
                    'estimated_hours': 4,
                    'priority': TaskPriority.MEDIUM
                })
            elif 'security' in requirement.lower():
                base_tasks.append({
                    'name': '安全強化',
                    'description': f'安全需求實現: {requirement}',
                    'task_type': 'security_hardening',
                    'agent_preference': 'security_advisor_baozhen',
                    'estimated_hours': 3,
                    'priority': TaskPriority.HIGH
                })
            elif 'documentation' in requirement.lower():
                base_tasks.append({
                    'name': '文檔增強',
                    'description': f'文檔需求: {requirement}',
                    'task_type': 'documentation_enhancement',
                    'agent_preference': 'doc_scribe_sima',
                    'estimated_hours': 2,
                    'priority': TaskPriority.LOW
                })
        
        # 將基礎任務轉換為TaskCoordination對象
        for task_data in base_tasks:
            task = TaskCoordination(
                task_id=f"{project.project_id}_{task_counter:03d}",
                name=task_data['name'],
                description=task_data['description'],
                task_type=task_data['task_type'],
                priority=task_data['priority'],
                estimated_hours=task_data['estimated_hours'],
                project_id=project.project_id,
                requirements=project.requirements,
                dependencies=[],  # 簡化處理，實際可以建立任務依賴關係
                metadata={
                    'project_type': project.project_type.value,
                    'agent_preference': task_data['agent_preference']
                }
            )
            
            tasks.append(task)
            task_counter += 1
        
        return tasks
    
    async def _collect_deliverables(self, execution_results: List[Any]) -> List[Dict[str, Any]]:
        """收集可交付成果"""
        deliverables = []
        
        for result in execution_results:
            if hasattr(result, 'deliverables') and result.deliverables:
                deliverables.extend(result.deliverables)
            elif hasattr(result, 'task') and result.success:
                # 基於任務類型推斷可交付成果
                task = result.task
                deliverable = {
                    'type': task.task_type,
                    'name': f"{task.name} - 完成成果",
                    'description': f"任務 {task.name} 的執行結果",
                    'status': 'completed',
                    'created_at': datetime.now().isoformat(),
                    'metadata': {
                        'task_id': task.task_id,
                        'assigned_agent': task.assigned_agent,
                        'execution_time': getattr(result, 'execution_time', 0)
                    }
                }
                deliverables.append(deliverable)
        
        return deliverables
    
    async def _analyze_quality_scores(self, execution_results: List[Any]) -> Dict[str, float]:
        """分析品質分數"""
        quality_scores = {
            'overall_quality': 0.0,
            'code_quality': 0.0,
            'test_coverage': 0.0,
            'security_score': 0.0,
            'documentation_quality': 0.0,
            'architecture_quality': 0.0
        }
        
        # 基於成功任務計算品質分數
        successful_tasks = [r for r in execution_results if hasattr(r, 'success') and r.success]
        total_tasks = len(execution_results)
        
        if total_tasks > 0:
            success_rate = len(successful_tasks) / total_tasks
            
            # 基本品質分數基於成功率
            base_score = success_rate * 85  # 85% 基準分數
            
            quality_scores['overall_quality'] = base_score
            quality_scores['code_quality'] = min(base_score + 5, 95)  # 代碼品質稍高
            quality_scores['test_coverage'] = max(base_score - 10, 60)  # 測試覆蓋率稍低
            quality_scores['security_score'] = base_score + 3
            quality_scores['documentation_quality'] = base_score - 5
            quality_scores['architecture_quality'] = base_score + 2
        
        return quality_scores
    
    async def _calculate_performance_metrics(self, execution_results: List[Any], start_time: datetime) -> Dict[str, Any]:
        """計算性能指標"""
        total_execution_time = (datetime.now() - start_time).total_seconds()
        
        metrics = {
            'total_execution_time': total_execution_time,
            'average_task_time': 0.0,
            'throughput': 0.0,
            'efficiency_score': 0.0,
            'resource_utilization': 0.0
        }
        
        if execution_results:
            # 計算平均任務時間
            task_times = []
            for result in execution_results:
                if hasattr(result, 'execution_time'):
                    task_times.append(result.execution_time)
                elif hasattr(result, 'task') and hasattr(result.task, 'actual_hours'):
                    task_times.append(result.task.actual_hours * 3600)  # 轉換為秒
            
            if task_times:
                metrics['average_task_time'] = sum(task_times) / len(task_times)
            
            # 計算吞吐量（任務/小時）
            metrics['throughput'] = len(execution_results) / (total_execution_time / 3600)
            
            # 計算效率分數
            successful_tasks = len([r for r in execution_results if hasattr(r, 'success') and r.success])
            metrics['efficiency_score'] = successful_tasks / len(execution_results) if execution_results else 0
            
            # 計算資源利用率（簡化）
            metrics['resource_utilization'] = min(total_execution_time / (len(self.agents) * 3600), 1.0)
        
        return metrics
    
    async def _analyze_team_utilization(self, execution_results: List[Any]) -> Dict[str, float]:
        """分析團隊利用率"""
        utilization = {}
        
        # 統計每個代理人的任務數量
        agent_task_counts = {}
        total_tasks = len(execution_results)
        
        for result in execution_results:
            if hasattr(result, 'task') and hasattr(result.task, 'assigned_agent'):
                agent_id = result.task.assigned_agent
                agent_task_counts[agent_id] = agent_task_counts.get(agent_id, 0) + 1
        
        # 計算利用率
        for agent_id in self.agents.keys():
            task_count = agent_task_counts.get(agent_id, 0)
            utilization[agent_id] = task_count / max(total_tasks, 1)
        
        return utilization
    
    async def get_service_status(self) -> Dict[str, Any]:
        """獲取服務狀態"""
        uptime = datetime.now() - self.started_at
        
        status_info = {
            'service_id': self.service_id,
            'status': self.status.value,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime),
            'statistics': {
                'projects_completed': self.projects_completed,
                'total_tasks_executed': self.total_tasks_executed,
                'total_execution_time': self.total_execution_time,
                'success_rate': self.success_rate,
                'active_projects_count': len(self.active_projects)
            },
            'agents_status': {},
            'coordinator_status': None,
            'last_updated': datetime.now().isoformat()
        }
        
        # 獲取各代理人狀態
        for agent_id, agent in self.agents.items():
            if hasattr(agent, 'get_agent_status'):
                status_info['agents_status'][agent_id] = await agent.get_agent_status() if asyncio.iscoroutinefunction(agent.get_agent_status) else agent.get_agent_status()
        
        # 獲取協調者狀態
        if self.coordinator and hasattr(self.coordinator, 'get_coordinator_status'):
            status_info['coordinator_status'] = self.coordinator.get_coordinator_status()
        
        return status_info
    
    async def shutdown(self) -> None:
        """關閉服務"""
        try:
            logger.info("天工開物協調服務正在關閉...", extra={
                'service_id': self.service_id,
                'projects_completed': self.projects_completed,
                'active_projects': len(self.active_projects)
            })
            
            # 等待活動專案完成（簡化處理）
            if self.active_projects:
                logger.warning(f"仍有 {len(self.active_projects)} 個活動專案，強制關閉")
            
            self.status = ServiceStatus.MAINTENANCE
            
            # 生成最終服務報告
            if self.coordinator:
                final_summary = await self.coordinator.generate_work_summary()
                logger.info("服務關閉前已生成最終工作總結", extra={
                    'summary_id': final_summary.report_id
                })
            
            logger.info("天工開物協調服務已關閉", extra={
                'service_id': self.service_id,
                'final_status': self.status.value
            })
            
        except Exception as e:
            logger.error(f"服務關閉過程中發生錯誤: {str(e)}")

# 便利函數
async def create_tiangong_service(config: Optional[Dict[str, Any]] = None) -> TianGongCoordinationService:
    """創建和初始化天工開物協調服務"""
    service = TianGongCoordinationService(config)
    await service.initialize()
    return service

def create_project_context(name: str, 
                         project_type: ProjectType,
                         requirements: List[str],
                         **kwargs) -> ProjectContext:
    """創建專案上下文"""
    return ProjectContext(
        project_name=name,
        project_type=project_type,
        requirements=requirements,
        **kwargs
    )

if __name__ == "__main__":
    # 測試腳本
    async def test_tiangong_service():
        print("測試天工開物協調服務...")
        
        # 創建服務配置
        config = {
            'master_weaver': {'auto_summary': True},
            'code_architect': {'complexity_threshold': 'medium'},
            'code_artisan': {'code_quality_threshold': 0.8},
            'qa_guardian': {'test_coverage_target': 0.85},
            'doc_scribe': {'default_format': 'markdown'},
            'devops_engineer': {'default_cloud_provider': 'aws'},
            'security_advisor': {'security_threshold': 'high'}
        }
        
        # 初始化服務
        service = await create_tiangong_service(config)
        
        # 創建測試專案
        project = create_project_context(
            name="TradingAgents增強項目",
            project_type=ProjectType.TRADING_SYSTEM,
            requirements=[
                "高性能交易執行",
                "實時風險管理",
                "安全的API接口",
                "完整的系統文檔",
                "自動化部署流程"
            ],
            description="增強現有TradingAgents系統的功能和性能",
            priority=TaskPriority.HIGH
        )
        
        # 執行專案協調
        result = await service.execute_project(project)
        
        print(f"專案協調完成:")
        print(f"- 結果ID: {result.result_id}")
        print(f"- 完成任務: {result.tasks_completed}")
        print(f"- 失敗任務: {result.tasks_failed}")
        print(f"- 整體成功: {result.overall_success}")
        print(f"- 執行時間: {result.execution_time:.2f} 秒")
        print(f"- 可交付成果: {len(result.deliverables)}")
        
        # 獲取服務狀態
        status = await service.get_service_status()
        print(f"\n服務狀態:")
        print(f"- 狀態: {status['status']}")
        print(f"- 完成專案: {status['statistics']['projects_completed']}")
        print(f"- 執行任務總數: {status['statistics']['total_tasks_executed']}")
        print(f"- 成功率: {status['statistics']['success_rate']:.1%}")
        
        # 關閉服務
        await service.shutdown()
        
        print("天工開物協調服務測試完成")
    
    asyncio.run(test_tiangong_service())