#!/usr/bin/env python3
"""
天工 (TianGong) - Master Weaver Coordinator
主協調者 - 專業軟體開發團隊的總指揮官

天工，中國古代神話中的工匠之神，擅長協調各類專業技能。
本模組將天工的協調智慧應用於現代軟體開發團隊管理。

功能特色：
1. 多專業代理人協調管理
2. 任務分解和分配
3. 工作流程優化
4. 工作總結報告生成
5. 品質控制和進度追蹤
6. 自動化決策支援
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error

# 配置日誌
logger = get_system_logger("master_weaver")

class TaskStatus(Enum):
    """任務狀態"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """任務優先級"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentType(Enum):
    """代理人類型"""
    ARCHITECT = "code-architect-liang"
    ARTISAN = "code-artisan-luban"
    QA_GUARDIAN = "qa-guardian-direnjie"
    DOC_SCRIBE = "doc-scribe-sima"
    DEVOPS_ENGINEER = "devops-engineer-mozi"
    SECURITY_ADVISOR = "security-advisor-baozhen"

@dataclass
class TaskCoordination:
    """任務協調資訊"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    assigned_agent: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    feedback: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        data = asdict(self)
        data['status'] = self.status.value
        data['priority'] = self.priority.value
        data['created_at'] = self.created_at.isoformat()
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data

@dataclass 
class WorkSummaryReport:
    """工作總結報告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    coordinator: str = "天工 (TianGong Master Weaver)"
    project_overview: str = ""
    tasks_completed: List[Dict[str, Any]] = field(default_factory=list)
    team_performance: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)
    challenges_faced: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    resource_utilization: Dict[str, Any] = field(default_factory=dict)
    timeline_analysis: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        return data
    
    def to_markdown(self) -> str:
        """生成Markdown格式報告"""
        md = f"""# 工作總結報告
**報告ID**: {self.report_id}  
**會話ID**: {self.session_id}  
**生成時間**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}  
**協調者**: {self.coordinator}

## 專案概述
{self.project_overview}

## 完成任務統計
"""
        for i, task in enumerate(self.tasks_completed, 1):
            md += f"""
### {i}. {task.get('title', '未命名任務')}
- **負責人**: {task.get('assigned_agent', '未指定')}
- **狀態**: {task.get('status', '未知')}
- **完成時間**: {task.get('completed_at', '未知')}
- **工作時數**: {task.get('actual_hours', '未記錄')}小時
"""

        md += f"""
## 團隊績效分析
- **總任務數**: {self.team_performance.get('total_tasks', 0)}
- **完成任務數**: {self.team_performance.get('completed_tasks', 0)}
- **成功率**: {self.team_performance.get('success_rate', 0):.1%}
- **平均完成時間**: {self.team_performance.get('avg_completion_time', 0):.1f}小時

## 品質指標
- **程式碼品質評分**: {self.quality_metrics.get('code_quality_score', 0)}/100
- **測試覆蓋率**: {self.quality_metrics.get('test_coverage', 0):.1%}
- **安全評分**: {self.quality_metrics.get('security_score', 0)}/100
- **文檔完整度**: {self.quality_metrics.get('documentation_completeness', 0):.1%}

## 主要成就
"""
        for achievement in self.achievements:
            md += f"- ✅ {achievement}\n"

        md += "\n## 遭遇挑戰\n"
        for challenge in self.challenges_faced:
            md += f"- ⚠️ {challenge}\n"

        md += "\n## 經驗教訓\n"
        for lesson in self.lessons_learned:
            md += f"- 💡 {lesson}\n"

        md += "\n## 改進建議\n"
        for recommendation in self.recommendations:
            md += f"- 📋 {recommendation}\n"

        md += "\n## 後續步驟\n"
        for step in self.next_steps:
            md += f"- 🎯 {step}\n"

        md += f"""
## 資源使用分析
- **開發時間**: {self.resource_utilization.get('development_hours', 0):.1f}小時
- **測試時間**: {self.resource_utilization.get('testing_hours', 0):.1f}小時
- **部署時間**: {self.resource_utilization.get('deployment_hours', 0):.1f}小時
- **文檔時間**: {self.resource_utilization.get('documentation_hours', 0):.1f}小時

## 時程分析
- **計劃總時間**: {self.timeline_analysis.get('planned_hours', 0):.1f}小時
- **實際總時間**: {self.timeline_analysis.get('actual_hours', 0):.1f}小時
- **時程偏差**: {self.timeline_analysis.get('schedule_variance', 0):.1%}

---
*本報告由天工 (TianGong Master Weaver) 自動生成*  
*生成時間: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return md

class MasterWeaverCoordinator:
    """
    天工 - 主協調器
    
    負責協調整個軟體開發團隊，包含任務分配、進度追蹤、
    品質控制和工作總結報告生成。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.session_id = str(uuid.uuid4())
        self.agents: Dict[str, Any] = {}
        self.tasks: Dict[str, TaskCoordination] = {}
        self.active_tasks: Dict[str, TaskCoordination] = {}
        self.completed_tasks: Dict[str, TaskCoordination] = {}
        self.work_session_start = datetime.now()
        
        # 配置參數
        self.max_parallel_tasks = self.config.get('max_parallel_tasks', 3)
        self.task_timeout_minutes = self.config.get('task_timeout_minutes', 30)
        self.enable_work_summaries = self.config.get('enable_work_summaries', True)
        self.summary_detail_level = self.config.get('summary_detail_level', 'comprehensive')
        
        logger.info("天工主協調器已初始化", extra={
            'session_id': self.session_id,
            'max_parallel_tasks': self.max_parallel_tasks,
            'coordinator': 'master_weaver'
        })
    
    def register_agent(self, agent: Any) -> bool:
        """註冊專業代理人"""
        try:
            agent_id = getattr(agent, 'agent_id', str(uuid.uuid4()))
            agent_type = getattr(agent, 'agent_type', 'unknown')
            
            self.agents[agent_id] = {
                'instance': agent,
                'type': agent_type,
                'status': 'available',
                'current_task': None,
                'total_tasks': 0,
                'completed_tasks': 0,
                'registered_at': datetime.now()
            }
            
            logger.info(f"代理人已註冊: {agent_type}", extra={
                'agent_id': agent_id,
                'agent_type': agent_type,
                'coordinator': 'master_weaver'
            })
            
            return True
            
        except Exception as e:
            logger.error(f"代理人註冊失敗: {str(e)}")
            return False
    
    async def coordinate_task(self, 
                            title: str,
                            description: str,
                            requirements: List[str] = None,
                            priority: TaskPriority = TaskPriority.MEDIUM,
                            estimated_hours: Optional[float] = None,
                            preferred_agent_type: Optional[AgentType] = None) -> str:
        """協調任務執行"""
        
        task = TaskCoordination(
            title=title,
            description=description,
            requirements=requirements or [],
            priority=priority,
            estimated_hours=estimated_hours
        )
        
        # 選擇最適合的代理人
        selected_agent = self._select_optimal_agent(preferred_agent_type, task)
        
        if not selected_agent:
            logger.warning("沒有可用的代理人執行任務", extra={
                'task_id': task.task_id,
                'title': title,
                'preferred_type': preferred_agent_type.value if preferred_agent_type else None
            })
            task.status = TaskStatus.FAILED
            self.tasks[task.task_id] = task
            return task.task_id
        
        # 分配任務
        task.assigned_agent = selected_agent
        task.status = TaskStatus.ASSIGNED
        task.started_at = datetime.now()
        
        self.tasks[task.task_id] = task
        self.active_tasks[task.task_id] = task
        self.agents[selected_agent]['status'] = 'busy'
        self.agents[selected_agent]['current_task'] = task.task_id
        self.agents[selected_agent]['total_tasks'] += 1
        
        logger.info(f"任務已分配: {title}", extra={
            'task_id': task.task_id,
            'assigned_agent': selected_agent,
            'priority': priority.value,
            'coordinator': 'master_weaver'
        })
        
        # 異步執行任務
        asyncio.create_task(self._execute_task(task))
        
        return task.task_id
    
    async def _execute_task(self, task: TaskCoordination):
        """執行任務"""
        try:
            task.status = TaskStatus.IN_PROGRESS
            
            # 模擬任務執行（實際實現中會調用相應代理人的執行方法）
            execution_time = task.estimated_hours or 1.0
            await asyncio.sleep(min(execution_time * 60, 300))  # 最多等待5分鐘
            
            # 任務完成
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.actual_hours = (task.completed_at - task.started_at).total_seconds() / 3600
            
            # 更新代理人狀態
            if task.assigned_agent:
                agent = self.agents[task.assigned_agent]
                agent['status'] = 'available'
                agent['current_task'] = None
                agent['completed_tasks'] += 1
            
            # 移動到完成任務列表
            if task.task_id in self.active_tasks:
                del self.active_tasks[task.task_id]
            self.completed_tasks[task.task_id] = task
            
            logger.info(f"任務已完成: {task.title}", extra={
                'task_id': task.task_id,
                'actual_hours': task.actual_hours,
                'assigned_agent': task.assigned_agent,
                'coordinator': 'master_weaver'
            })
            
            # 如果啟用了工作總結，檢查是否需要生成報告
            if self.enable_work_summaries:
                await self._check_and_generate_summary()
                
        except Exception as e:
            task.status = TaskStatus.FAILED
            logger.error(f"任務執行失敗: {task.title} - {str(e)}", extra={
                'task_id': task.task_id,
                'error': str(e),
                'coordinator': 'master_weaver'
            })
            
            # 釋放代理人
            if task.assigned_agent:
                self.agents[task.assigned_agent]['status'] = 'available'
                self.agents[task.assigned_agent]['current_task'] = None
    
    def _select_optimal_agent(self, preferred_type: Optional[AgentType], task: TaskCoordination) -> Optional[str]:
        """選擇最適合的代理人"""
        available_agents = [
            agent_id for agent_id, agent_info in self.agents.items()
            if agent_info['status'] == 'available'
        ]
        
        if not available_agents:
            return None
        
        # 如果指定了偏好類型，優先選擇
        if preferred_type:
            for agent_id in available_agents:
                if self.agents[agent_id]['type'] == preferred_type.value:
                    return agent_id
        
        # 根據任務特性自動選擇
        task_keywords = (task.title + " " + task.description).lower()
        
        # 關鍵字映射
        type_mappings = {
            AgentType.ARCHITECT: ['architecture', 'design', 'system', 'structure', '架構', '設計', '系統'],
            AgentType.ARTISAN: ['implement', 'code', 'develop', 'build', '實現', '程式碼', '開發'],
            AgentType.QA_GUARDIAN: ['test', 'quality', 'bug', 'validation', '測試', '品質', '驗證'],
            AgentType.DOC_SCRIBE: ['document', 'readme', 'doc', 'specification', '文檔', '說明'],
            AgentType.DEVOPS_ENGINEER: ['deploy', 'infrastructure', 'ci/cd', 'docker', '部署', '基礎設施'],
            AgentType.SECURITY_ADVISOR: ['security', 'auth', 'permission', 'vulnerability', '安全', '認證', '權限']
        }
        
        # 計算匹配分數
        best_agent = None
        best_score = 0
        
        for agent_id in available_agents:
            agent_type_str = self.agents[agent_id]['type']
            
            # 找到對應的AgentType
            agent_type = None
            for at in AgentType:
                if at.value == agent_type_str:
                    agent_type = at
                    break
            
            if agent_type and agent_type in type_mappings:
                keywords = type_mappings[agent_type]
                score = sum(1 for keyword in keywords if keyword in task_keywords)
                
                if score > best_score:
                    best_score = score
                    best_agent = agent_id
        
        # 如果沒有匹配，選擇工作負載最輕的
        if not best_agent:
            best_agent = min(available_agents, 
                           key=lambda x: self.agents[x]['total_tasks'])
        
        return best_agent
    
    async def _check_and_generate_summary(self):
        """檢查並生成工作總結"""
        # 檢查是否滿足生成總結的條件
        total_completed = len(self.completed_tasks)
        
        # 條件：完成5個以上任務，或工作會話超過2小時
        session_duration = datetime.now() - self.work_session_start
        
        if total_completed >= 5 or session_duration > timedelta(hours=2):
            summary = await self.generate_work_summary()
            
            # 保存總結報告
            await self._save_work_summary(summary)
            
            logger.info("工作總結報告已生成", extra={
                'report_id': summary.report_id,
                'session_id': self.session_id,
                'completed_tasks': total_completed,
                'session_duration_hours': session_duration.total_seconds() / 3600,
                'coordinator': 'master_weaver'
            })
    
    async def generate_work_summary(self) -> WorkSummaryReport:
        """生成工作總結報告"""
        
        # 分析團隊績效
        total_tasks = len(self.tasks)
        completed_tasks = len(self.completed_tasks)
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        avg_completion_time = 0
        if self.completed_tasks:
            total_hours = sum(task.actual_hours or 0 for task in self.completed_tasks.values())
            avg_completion_time = total_hours / len(self.completed_tasks)
        
        team_performance = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'success_rate': success_rate,
            'avg_completion_time': avg_completion_time
        }
        
        # 分析品質指標（模擬數據）
        quality_metrics = {
            'code_quality_score': 85,
            'test_coverage': 0.78,
            'security_score': 92,
            'documentation_completeness': 0.85
        }
        
        # 生成主要成就
        achievements = []
        if completed_tasks > 0:
            achievements.append(f"成功完成 {completed_tasks} 個開發任務")
        if success_rate > 0.8:
            achievements.append(f"任務成功率達到 {success_rate:.1%}")
        if avg_completion_time > 0:
            achievements.append(f"平均任務完成時間為 {avg_completion_time:.1f} 小時")
        
        # 分析挑戰和建議
        challenges_faced = []
        lessons_learned = []
        recommendations = []
        
        if success_rate < 0.9:
            challenges_faced.append("部分任務執行遇到困難，需要改進流程")
            recommendations.append("加強任務前期需求分析和風險評估")
        
        if avg_completion_time > 3:
            challenges_faced.append("任務完成時間較長，可能存在效率問題")
            lessons_learned.append("複雜任務需要更細緻的分解和規劃")
            recommendations.append("實施敏捷開發方法，提高迭代效率")
        
        # 資源使用分析
        total_hours = sum(task.actual_hours or 0 for task in self.completed_tasks.values())
        resource_utilization = {
            'development_hours': total_hours * 0.6,
            'testing_hours': total_hours * 0.2,
            'deployment_hours': total_hours * 0.1,
            'documentation_hours': total_hours * 0.1
        }
        
        # 時程分析
        estimated_total = sum(task.estimated_hours or 1 for task in self.completed_tasks.values())
        schedule_variance = (total_hours - estimated_total) / estimated_total if estimated_total > 0 else 0
        
        timeline_analysis = {
            'planned_hours': estimated_total,
            'actual_hours': total_hours,
            'schedule_variance': schedule_variance
        }
        
        # 後續步驟
        next_steps = [
            "持續監控團隊表現和任務品質",
            "優化工作流程和協調機制",
            "加強各專業代理人之間的協作",
            "定期回顧和改進開發流程"
        ]
        
        if success_rate < 0.9:
            next_steps.append("重點關注失敗任務的原因分析")
        
        if avg_completion_time > 2:
            next_steps.append("研究任務分解和並行處理策略")
        
        # 創建工作總結報告
        summary_report = WorkSummaryReport(
            session_id=self.session_id,
            period_start=self.work_session_start,
            period_end=datetime.now(),
            team_performance=team_performance,
            quality_metrics=quality_metrics,
            achievements=achievements,
            challenges_faced=challenges_faced,
            lessons_learned=lessons_learned,
            resource_utilization=resource_utilization,
            timeline_analysis=timeline_analysis,
            recommendations=recommendations,
            next_steps=next_steps
        )
        
        # 添加代理人績效分析
        summary_report.agent_performance = await self._analyze_agent_performance()
        
        # 添加任務分析
        summary_report.task_analysis = await self._analyze_completed_tasks()
        
        logger.info("工作總結報告生成完成", extra={
            'report_id': summary_report.report_id,
            'session_id': self.session_id,
            'tasks_analyzed': len(self.completed_tasks),
            'achievements_count': len(achievements),
            'recommendations_count': len(recommendations)
        })
        
        return summary_report
    
    async def _analyze_agent_performance(self) -> Dict[str, Any]:
        """分析代理人績效"""
        agent_performance = {}
        
        for agent_id, agent_info in self.agents.items():
            performance_data = {
                'total_tasks': agent_info['total_tasks'],
                'completed_tasks': agent_info['completed_tasks'],
                'success_rate': agent_info['completed_tasks'] / max(agent_info['total_tasks'], 1),
                'avg_task_time': 0,
                'expertise_areas': agent_info['expertise'],
                'current_status': agent_info['status'],
                'efficiency_score': 0,
                'quality_contributions': []
            }
            
            # 計算平均任務時間
            agent_tasks = [task for task in self.completed_tasks.values() 
                          if task.assigned_agent == agent_id]
            
            if agent_tasks:
                total_time = sum(task.actual_hours or 0 for task in agent_tasks)
                performance_data['avg_task_time'] = total_time / len(agent_tasks)
                
                # 計算效率分數
                total_estimated = sum(task.estimated_hours or 1 for task in agent_tasks)
                efficiency = total_estimated / max(total_time, 0.1)
                performance_data['efficiency_score'] = min(efficiency, 2.0)  # 最高2.0
                
                # 分析品質貢獻
                for task in agent_tasks:
                    if task.task_type in ['code_development', 'code_review']:
                        performance_data['quality_contributions'].append('代碼品質提升')
                    elif task.task_type in ['testing', 'qa_review']:
                        performance_data['quality_contributions'].append('測試覆蓋率改善')
                    elif task.task_type in ['documentation', 'api_docs']:
                        performance_data['quality_contributions'].append('文檔完整性增強')
                    elif task.task_type in ['deployment', 'infrastructure']:
                        performance_data['quality_contributions'].append('部署穩定性提升')
                    elif task.task_type in ['security_review', 'vulnerability_scan']:
                        performance_data['quality_contributions'].append('安全性強化')
            
            agent_performance[agent_id] = performance_data
        
        return agent_performance
    
    async def _analyze_completed_tasks(self) -> Dict[str, Any]:
        """分析已完成任務"""
        if not self.completed_tasks:
            return {}
        
        # 任務類型分佈
        task_type_distribution = {}
        for task in self.completed_tasks.values():
            task_type = task.task_type
            task_type_distribution[task_type] = task_type_distribution.get(task_type, 0) + 1
        
        # 任務複雜度分析
        complexity_distribution = {}
        for task in self.completed_tasks.values():
            complexity = getattr(task, 'complexity', 'medium')
            complexity_distribution[complexity] = complexity_distribution.get(complexity, 0) + 1
        
        # 時間估算準確性
        estimation_accuracy = []
        for task in self.completed_tasks.values():
            if task.estimated_hours and task.actual_hours:
                accuracy = 1 - abs(task.actual_hours - task.estimated_hours) / task.estimated_hours
                estimation_accuracy.append(max(0, accuracy))
        
        avg_estimation_accuracy = sum(estimation_accuracy) / len(estimation_accuracy) if estimation_accuracy else 0
        
        # 任務依賴分析
        dependency_impact = {
            'tasks_with_dependencies': len([t for t in self.completed_tasks.values() 
                                          if getattr(t, 'dependencies', [])]),
            'avg_dependency_delay': 0  # 簡化為0，實際可以更詳細計算
        }
        
        return {
            'task_type_distribution': task_type_distribution,
            'complexity_distribution': complexity_distribution,
            'estimation_accuracy': avg_estimation_accuracy,
            'dependency_impact': dependency_impact,
            'total_task_count': len(self.completed_tasks),
            'avg_task_duration': sum(task.actual_hours or 0 for task in self.completed_tasks.values()) / len(self.completed_tasks)
        }
    
    async def _save_work_summary(self, summary: WorkSummaryReport) -> None:
        """保存工作總結報告"""
        try:
            # 將報告保存到工作總結歷史中
            self.work_summary_history.append(summary)
            
            # 生成報告文件內容
            report_content = self._format_summary_report(summary)
            
            # 這裡可以添加實際的文件保存邏輯
            logger.info("工作總結報告已保存", extra={
                'report_id': summary.report_id,
                'file_size': len(report_content),
                'achievements_count': len(summary.achievements),
                'recommendations_count': len(summary.recommendations)
            })
            
        except Exception as e:
            logger.error(f"保存工作總結報告失敗: {str(e)}", extra={
                'report_id': summary.report_id,
                'error': str(e)
            })
    
    def _format_summary_report(self, summary: WorkSummaryReport) -> str:
        """格式化總結報告為可讀文本"""
        report_lines = [
            f"# 天工開物 - 工作總結報告",
            f"",
            f"**報告編號:** {summary.report_id}",
            f"**工作會話:** {summary.session_id}",
            f"**時間期間:** {summary.period_start.strftime('%Y-%m-%d %H:%M')} - {summary.period_end.strftime('%Y-%m-%d %H:%M')}",
            f"**生成時間:** {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
            f"## 團隊績效概覽",
            f"",
            f"- **總任務數:** {summary.team_performance['total_tasks']}",
            f"- **完成任務數:** {summary.team_performance['completed_tasks']}",
            f"- **成功率:** {summary.team_performance['success_rate']:.1%}",
            f"- **平均完成時間:** {summary.team_performance['avg_completion_time']:.1f} 小時",
            f"",
            f"## 品質指標",
            f"",
            f"- **代碼品質評分:** {summary.quality_metrics['code_quality_score']}/100",
            f"- **測試覆蓋率:** {summary.quality_metrics['test_coverage']:.1%}",
            f"- **安全評分:** {summary.quality_metrics['security_score']}/100",
            f"- **文檔完整性:** {summary.quality_metrics['documentation_completeness']:.1%}",
            f"",
            f"## 主要成就",
            f""
        ]
        
        for achievement in summary.achievements:
            report_lines.append(f"- {achievement}")
        
        report_lines.extend([
            f"",
            f"## 面臨挑戰",
            f""
        ])
        
        for challenge in summary.challenges_faced:
            report_lines.append(f"- {challenge}")
        
        report_lines.extend([
            f"",
            f"## 經驗教訓",
            f""
        ])
        
        for lesson in summary.lessons_learned:
            report_lines.append(f"- {lesson}")
        
        report_lines.extend([
            f"",
            f"## 資源使用分析",
            f"",
            f"- **開發時間:** {summary.resource_utilization['development_hours']:.1f} 小時",
            f"- **測試時間:** {summary.resource_utilization['testing_hours']:.1f} 小時",
            f"- **部署時間:** {summary.resource_utilization['deployment_hours']:.1f} 小時",
            f"- **文檔時間:** {summary.resource_utilization['documentation_hours']:.1f} 小時",
            f"",
            f"## 時程分析",
            f"",
            f"- **計劃工時:** {summary.timeline_analysis['planned_hours']:.1f} 小時",
            f"- **實際工時:** {summary.timeline_analysis['actual_hours']:.1f} 小時",
            f"- **時程偏差:** {summary.timeline_analysis['schedule_variance']:.1%}",
            f"",
            f"## 改進建議",
            f""
        ])
        
        for recommendation in summary.recommendations:
            report_lines.append(f"- {recommendation}")
        
        report_lines.extend([
            f"",
            f"## 後續步驟",
            f""
        ])
        
        for step in summary.next_steps:
            report_lines.append(f"- {step}")
        
        if hasattr(summary, 'agent_performance') and summary.agent_performance:
            report_lines.extend([
                f"",
                f"## 代理人績效分析",
                f""
            ])
            
            for agent_id, performance in summary.agent_performance.items():
                agent_name = self.agents.get(agent_id, {}).get('name', agent_id)
                report_lines.extend([
                    f"### {agent_name}",
                    f"- 完成任務: {performance['completed_tasks']}/{performance['total_tasks']}",
                    f"- 成功率: {performance['success_rate']:.1%}",
                    f"- 效率分數: {performance['efficiency_score']:.2f}",
                    f"- 平均任務時間: {performance['avg_task_time']:.1f} 小時",
                    f""
                ])
        
        if hasattr(summary, 'task_analysis') and summary.task_analysis:
            report_lines.extend([
                f"",
                f"## 任務分析",
                f"",
                f"- **任務總數:** {summary.task_analysis['total_task_count']}",
                f"- **平均任務時長:** {summary.task_analysis['avg_task_duration']:.1f} 小時",
                f"- **時間估算準確性:** {summary.task_analysis['estimation_accuracy']:.1%}",
                f""
            ])
        
        report_lines.extend([
            f"",
            f"---",
            f"",
            f"*此報告由天工 (TianGong) 主協調者自動生成*",
            f"*Generated by TianGong Master Weaver Coordinator*"
        ])
        
        return "\n".join(report_lines)
    
    def get_coordination_status(self) -> Dict[str, Any]:
        """獲取協調狀態"""
        session_duration = datetime.now() - self.work_session_start
        
        return {
            'session_id': self.session_id,
            'coordinator': '天工 (TianGong Master Weaver)',
            'session_duration_hours': session_duration.total_seconds() / 3600,
            'registered_agents': len(self.agents),
            'total_tasks': len(self.tasks),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'agents_status': {
                agent_id: {
                    'type': info['type'],
                    'status': info['status'],
                    'total_tasks': info['total_tasks'],
                    'completed_tasks': info['completed_tasks']
                }
                for agent_id, info in self.agents.items()
            },
            'configuration': {
                'max_parallel_tasks': self.max_parallel_tasks,
                'enable_work_summaries': self.enable_work_summaries,
                'summary_detail_level': self.summary_detail_level
            },
            'timestamp': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 測試腳本
    async def test_master_weaver():
        print("測試天工主協調器...")
        
        coordinator = MasterWeaverCoordinator({
            'max_parallel_tasks': 2,
            'enable_work_summaries': True,
            'summary_detail_level': 'comprehensive'
        })
        
        # 模擬代理人註冊
        class MockAgent:
            def __init__(self, agent_id: str, agent_type: str):
                self.agent_id = agent_id
                self.agent_type = agent_type
        
        # 註冊代理人
        coordinator.register_agent(MockAgent("arch-001", AgentType.ARCHITECT.value))
        coordinator.register_agent(MockAgent("artisan-001", AgentType.ARTISAN.value))
        coordinator.register_agent(MockAgent("qa-001", AgentType.QA_GUARDIAN.value))
        
        # 協調任務
        task1 = await coordinator.coordinate_task(
            title="設計系統架構",
            description="為新功能設計系統架構",
            requirements=["高可用性", "可擴展性", "安全性"],
            priority=TaskPriority.HIGH,
            estimated_hours=4.0,
            preferred_agent_type=AgentType.ARCHITECT
        )
        
        task2 = await coordinator.coordinate_task(
            title="實現核心功能",
            description="根據架構設計實現核心功能模組",
            requirements=["程式碼品質", "測試覆蓋", "文檔完整"],
            priority=TaskPriority.MEDIUM,
            estimated_hours=6.0,
            preferred_agent_type=AgentType.ARTISAN
        )
        
        # 等待任務完成
        await asyncio.sleep(2)
        
        # 獲取狀態
        status = coordinator.get_coordination_status()
        print(f"協調狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 生成工作總結
        summary = await coordinator.generate_work_summary()
        print(f"\n工作總結報告:\n{summary.to_markdown()}")
        
        print("天工主協調器測試完成")
    
    asyncio.run(test_master_weaver())