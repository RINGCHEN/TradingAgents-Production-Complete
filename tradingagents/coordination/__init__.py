#!/usr/bin/env python3
"""
天工開物 (TianGong KaiWu) 協調系統
Master Weaver Coordinator - 開發團隊協調中心

此模組提供專業軟體開發團隊的協調管理功能：
1. Master Weaver Coordinator (天工) - 總協調師
2. Code Architect (梁) - 系統架構師
3. Code Artisan (魯班) - 程式碼工匠
4. QA Guardian (狄仁傑) - 品質保證守護者
5. Doc Scribe (司馬) - 文檔書記員
6. DevOps Engineer (墨子) - 運維工程師
7. Security Advisor (包拯) - 安全顧問

統一協調服務：
TianGongCoordinationService 提供了完整的專案協調和管理功能。

天工開物團隊致力於提供企業級軟體開發和系統整合解決方案。
"""

# 統一協調服務
from .tiangong_service import (
    TianGongCoordinationService,
    ProjectContext,
    ProjectType,
    CoordinationResult,
    ServiceStatus,
    create_tiangong_service,
    create_project_context
)

# 主協調者和基礎類型
from .master_weaver import (
    MasterWeaverCoordinator, 
    WorkSummaryReport, 
    TaskCoordination,
    TaskStatus,
    TaskPriority,
    AgentType
)

# 專業代理人
from .code_architect import (
    CodeArchitectLiang,
    ArchitectureAnalysis,
    ArchitectureDesign
)
from .code_artisan import (
    CodeArtisanLuban,
    CodeImplementation,
    RefactoringPlan,
    CodeReview
)
from .qa_guardian import (
    QAGuardianDirenjie,
    TestPlan,
    TestExecution,
    QualityReport
)
from .doc_scribe import (
    DocScribeSima,
    DocumentationTask,
    DocumentOutput,
    APIDocumentation
)
from .devops_engineer import (
    DevOpsEngineerMozi,
    InfrastructureConfig,
    DeploymentPlan,
    CIPipeline
)
from .security_advisor import (
    SecurityAdvisorBaozhen,
    SecurityVulnerability,
    SecurityAssessment,
    ComplianceReport
)

__all__ = [
    # 統一協調服務
    'TianGongCoordinationService',
    'ProjectContext',
    'ProjectType',
    'CoordinationResult',
    'ServiceStatus',
    'create_tiangong_service',
    'create_project_context',
    
    # Master Coordinator
    'MasterWeaverCoordinator',
    'WorkSummaryReport',
    'TaskCoordination',
    'TaskStatus',
    'TaskPriority',
    'AgentType',
    
    # Specialized Agents
    'CodeArchitectLiang',
    'CodeArtisanLuban', 
    'QAGuardianDirenjie',
    'DocScribeSima',
    'DevOpsEngineerMozi',
    'SecurityAdvisorBaozhen',
    
    # Data Models
    'ArchitectureAnalysis',
    'ArchitectureDesign',
    'CodeImplementation',
    'RefactoringPlan',
    'CodeReview',
    'TestPlan',
    'TestExecution',
    'QualityReport',
    'DocumentationTask',
    'DocumentOutput',
    'APIDocumentation',
    'InfrastructureConfig',
    'DeploymentPlan',
    'CIPipeline',
    'SecurityVulnerability',
    'SecurityAssessment',
    'ComplianceReport'
]

# 版本資訊
__version__ = "2.0.0"
__author__ = "天工開物 (TianGong KaiWu) Team"
__description__ = "專業軟體開發團隊協調系統 - 增強版"

# 快速配置函數
async def setup_coordination_system(config=None):
    """
    快速設置協調系統 (異步版本)
    
    Args:
        config: 協調系統配置字典
        
    Returns:
        tuple: (coordinator, agents_dict)
    """
    coordinator = MasterWeaverCoordinator(config or {})
    
    # 初始化專業團隊
    agents = {
        'code_architect_liang': CodeArchitectLiang(config.get('code_architect', {}) if config else {}),
        'code_artisan_luban': CodeArtisanLuban(config.get('code_artisan', {}) if config else {}),
        'qa_guardian_direnjie': QAGuardianDirenjie(config.get('qa_guardian', {}) if config else {}),
        'doc_scribe_sima': DocScribeSima(config.get('doc_scribe', {}) if config else {}),
        'devops_engineer_mozi': DevOpsEngineerMozi(config.get('devops_engineer', {}) if config else {}),
        'security_advisor_baozhen': SecurityAdvisorBaozhen(config.get('security_advisor', {}) if config else {})
    }
    
    # 註冊所有代理人到協調者
    for agent_id, agent in agents.items():
        await coordinator.register_agent(
            agent_id=agent_id,
            agent_type=agent.agent_type,
            capabilities=agent.expertise_areas,
            agent_instance=agent
        )
    
    return coordinator, agents

# 舊版同步配置函數 (保持向後兼容)
def setup_coordination_system_sync(config=None):
    """
    快速設置協調系統 (同步版本，僅用於向後兼容)
    
    Args:
        config: 協調系統配置字典
        
    Returns:
        MasterWeaverCoordinator: 配置完成的主協調器
    """
    import warnings
    warnings.warn(
        "setup_coordination_system_sync is deprecated. Use async setup_coordination_system instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    coordinator = MasterWeaverCoordinator(config or {})
    return coordinator

# 默認配置
DEFAULT_COORDINATION_CONFIG = {
    'max_parallel_tasks': 5,
    'task_timeout_minutes': 60,
    'enable_work_summaries': True,
    'summary_detail_level': 'comprehensive',
    'enable_quality_gates': True,
    'enable_security_checks': True,
    'enable_performance_monitoring': True,
    'auto_summary_threshold': 5,
    'summary_interval_hours': 2
}

if __name__ == "__main__":
    print("天工開物 (TianGong KaiWu) 協調系統")
    print(f"版本: {__version__}")
    print(f"開發團隊: {__author__}")
    print(f"描述: {__description__}")
    print("\n可用組件:")
    for component in __all__:
        print(f"  - {component}")