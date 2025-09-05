#!/usr/bin/env python3
"""
狄仁傑 (Direnjie) - QA Guardian Agent
品質保證守護者代理人

狄仁傑，唐代著名宰相，以公正嚴明、明察秋毫著稱。
本代理人專注於軟體品質保證、測試策略制定和缺陷預防。

專業領域：
1. 測試策略設計和執行
2. 代碼品質評估和改進
3. 缺陷分析和預防
4. 自動化測試實施
5. 品質標準制定和監控
6. 測試覆蓋率分析和優化
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import random

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error

logger = get_system_logger("qa_guardian")

class TestType(Enum):
    """測試類型"""
    UNIT = "unit_test"
    INTEGRATION = "integration_test"
    FUNCTIONAL = "functional_test"
    PERFORMANCE = "performance_test"
    SECURITY = "security_test"
    USABILITY = "usability_test"
    REGRESSION = "regression_test"
    API = "api_test"
    E2E = "end_to_end_test"

class TestPriority(Enum):
    """測試優先級"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class DefectSeverity(Enum):
    """缺陷嚴重程度"""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    TRIVIAL = "trivial"

class QualityMetric(Enum):
    """品質指標"""
    CODE_COVERAGE = "code_coverage"
    DEFECT_DENSITY = "defect_density"
    TEST_PASS_RATE = "test_pass_rate"
    AUTOMATION_RATE = "automation_rate"
    MEAN_TIME_TO_DETECT = "mean_time_to_detect"
    MEAN_TIME_TO_RESOLVE = "mean_time_to_resolve"

@dataclass
class TestPlan:
    """測試計劃"""
    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = ""
    test_scope: List[str] = field(default_factory=list)
    test_objectives: List[str] = field(default_factory=list)
    test_strategy: Dict[str, Any] = field(default_factory=dict)
    test_cases: List[Dict[str, Any]] = field(default_factory=list)
    test_schedule: Dict[str, Any] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: List[Dict[str, Any]] = field(default_factory=list)
    entry_criteria: List[str] = field(default_factory=list)
    exit_criteria: List[str] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    tools_and_environment: Dict[str, str] = field(default_factory=dict)
    approval_required: bool = True
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TestExecution:
    """測試執行結果"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_plan_id: str = ""
    test_suite: str = ""
    executed_by: str = ""
    execution_date: datetime = field(default_factory=datetime.now)
    test_results: Dict[str, Any] = field(default_factory=dict)
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    total_tests: int = 0
    execution_time: float = 0.0
    coverage_report: Dict[str, Any] = field(default_factory=dict)
    defects_found: List[Dict[str, Any]] = field(default_factory=list)
    test_environment: Dict[str, str] = field(default_factory=dict)
    notes: str = ""
    artifacts: List[str] = field(default_factory=list)

@dataclass
class QualityReport:
    """品質報告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = ""
    reporting_period: str = ""
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    test_summary: Dict[str, Any] = field(default_factory=dict)
    defect_analysis: Dict[str, Any] = field(default_factory=dict)
    coverage_analysis: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    action_items: List[Dict[str, Any]] = field(default_factory=list)
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    compliance_status: Dict[str, bool] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.now)

class QAGuardianDirenjie:
    """
    狄仁傑 - 品質保證守護者代理人
    
    專注於軟體品質保證、測試策略制定和品質監控。
    確保軟體產品達到最高品質標準。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.agent_id = str(uuid.uuid4())
        self.agent_type = "qa-guardian-direnjie"
        self.config = config or {}
        self.name = "狄仁傑 (Direnjie) - 品質保證守護者"
        self.expertise_areas = [
            "測試策略設計",
            "自動化測試實施",
            "品質標準制定",
            "缺陷分析預防",
            "測試覆蓋率優化",
            "性能品質評估"
        ]
        
        # 工作統計
        self.test_plans_created = 0
        self.test_executions_conducted = 0
        self.defects_analyzed = 0
        self.quality_reports_generated = 0
        
        # 品質標準配置
        self.coverage_threshold = self.config.get('coverage_threshold', 0.8)
        self.defect_density_threshold = self.config.get('defect_density_threshold', 0.1)
        self.test_automation_goal = self.config.get('test_automation_goal', 0.7)
        
        logger.info("品質保證守護者狄仁傑已初始化", extra={
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'expertise_areas': self.expertise_areas,
            'quality_thresholds': {
                'coverage': self.coverage_threshold,
                'defect_density': self.defect_density_threshold,
                'automation': self.test_automation_goal
            }
        })
    
    async def create_test_plan(self,
                             project_name: str,
                             requirements: List[str],
                             test_scope: List[str],
                             constraints: Optional[List[str]] = None) -> TestPlan:
        """創建測試計劃"""
        
        plan = TestPlan(
            project_name=project_name,
            test_scope=test_scope
        )
        
        try:
            # 模擬測試計劃制定過程
            await asyncio.sleep(1.2)
            
            # 分析需求制定測試目標
            plan.test_objectives = self._define_test_objectives(requirements, test_scope)
            
            # 制定測試策略
            plan.test_strategy = self._design_test_strategy(requirements, constraints)
            
            # 設計測試用例
            plan.test_cases = self._design_test_cases(requirements, test_scope)
            
            # 制定測試時程
            plan.test_schedule = self._create_test_schedule(plan.test_cases)
            
            # 評估資源需求
            plan.resource_requirements = self._assess_resource_requirements(plan.test_strategy)
            
            # 風險評估
            plan.risk_assessment = self._assess_testing_risks(project_name, constraints)
            
            # 定義進入和退出標準
            plan.entry_criteria = self._define_entry_criteria(requirements)
            plan.exit_criteria = self._define_exit_criteria(plan.test_objectives)
            
            # 確定交付物
            plan.deliverables = self._define_test_deliverables(plan.test_strategy)
            
            # 配置工具和環境
            plan.tools_and_environment = self._configure_test_environment(plan.test_strategy)
            
            self.test_plans_created += 1
            
            logger.info("測試計劃創建完成", extra={
                'plan_id': plan.plan_id,
                'project_name': project_name,
                'test_cases_count': len(plan.test_cases),
                'test_objectives_count': len(plan.test_objectives),
                'agent': self.agent_type
            })
            
            return plan
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'create_test_plan',
                'project': project_name
            })
            logger.error(f"測試計劃創建失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def execute_tests(self,
                          test_plan_id: str,
                          test_suite: str,
                          test_environment: Optional[Dict[str, str]] = None) -> TestExecution:
        """執行測試"""
        
        execution = TestExecution(
            test_plan_id=test_plan_id,
            test_suite=test_suite,
            executed_by=self.name,
            test_environment=test_environment or {}
        )
        
        try:
            # 模擬測試執行過程
            await asyncio.sleep(0.8)
            
            # 執行測試套件
            execution.test_results = self._execute_test_suite(test_suite)
            
            # 統計測試結果
            self._calculate_test_statistics(execution)
            
            # 生成覆蓋率報告
            execution.coverage_report = self._generate_coverage_report(test_suite)
            
            # 分析發現的缺陷
            execution.defects_found = self._analyze_test_failures(execution.test_results)
            
            # 生成測試工件
            execution.artifacts = self._generate_test_artifacts(execution)
            
            # 添加執行備註
            execution.notes = self._generate_execution_notes(execution)
            
            self.test_executions_conducted += 1
            self.defects_analyzed += len(execution.defects_found)
            
            logger.info("測試執行完成", extra={
                'execution_id': execution.execution_id,
                'test_suite': test_suite,
                'passed_tests': execution.passed_tests,
                'failed_tests': execution.failed_tests,
                'total_tests': execution.total_tests,
                'defects_found': len(execution.defects_found),
                'agent': self.agent_type
            })
            
            return execution
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'execute_tests',
                'test_suite': test_suite
            })
            logger.error(f"測試執行失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def generate_quality_report(self,
                                    project_name: str,
                                    test_executions: List[TestExecution],
                                    reporting_period: str = "monthly") -> QualityReport:
        """生成品質報告"""
        
        report = QualityReport(
            project_name=project_name,
            reporting_period=reporting_period
        )
        
        try:
            # 模擬報告生成過程
            await asyncio.sleep(1.0)
            
            # 計算品質指標
            report.quality_metrics = self._calculate_quality_metrics(test_executions)
            
            # 測試摘要分析
            report.test_summary = self._generate_test_summary(test_executions)
            
            # 缺陷分析
            report.defect_analysis = self._analyze_defects(test_executions)
            
            # 覆蓋率分析
            report.coverage_analysis = self._analyze_coverage(test_executions)
            
            # 風險評估
            report.risk_assessment = self._assess_quality_risks(report.quality_metrics)
            
            # 改進建議
            report.recommendations = self._generate_quality_recommendations(report)
            
            # 行動項目
            report.action_items = self._generate_quality_action_items(report)
            
            # 趨勢分析
            report.trend_analysis = self._analyze_quality_trends(test_executions)
            
            # 合規性狀態
            report.compliance_status = self._check_quality_compliance(report.quality_metrics)
            
            self.quality_reports_generated += 1
            
            logger.info("品質報告生成完成", extra={
                'report_id': report.report_id,
                'project_name': project_name,
                'reporting_period': reporting_period,
                'quality_score': report.quality_metrics.get('overall_quality_score', 0),
                'agent': self.agent_type
            })
            
            return report
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'generate_quality_report',
                'project': project_name
            })
            logger.error(f"品質報告生成失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    async def analyze_defects(self,
                            defects: List[Dict[str, Any]],
                            analysis_scope: List[str] = None) -> Dict[str, Any]:
        """分析缺陷"""
        
        try:
            # 模擬缺陷分析過程
            await asyncio.sleep(0.6)
            
            analysis_result = {
                'analysis_id': str(uuid.uuid4()),
                'analyzed_at': datetime.now().isoformat(),
                'analyzer': self.name,
                'total_defects': len(defects),
                'severity_distribution': self._analyze_defect_severity_distribution(defects),
                'root_cause_analysis': self._perform_root_cause_analysis(defects),
                'category_analysis': self._categorize_defects(defects),
                'trend_analysis': self._analyze_defect_trends(defects),
                'impact_assessment': self._assess_defect_impact(defects),
                'prevention_strategies': self._suggest_prevention_strategies(defects),
                'fix_priority_ranking': self._rank_defect_priorities(defects),
                'resource_impact': self._estimate_fix_resources(defects),
                'quality_improvement_actions': self._suggest_quality_improvements(defects)
            }
            
            logger.info("缺陷分析完成", extra={
                'analysis_id': analysis_result['analysis_id'],
                'total_defects': len(defects),
                'critical_defects': analysis_result['severity_distribution'].get('critical', 0),
                'agent': self.agent_type
            })
            
            return analysis_result
            
        except Exception as e:
            error_info = await handle_error(e, {
                'agent': self.agent_type,
                'operation': 'analyze_defects'
            })
            logger.error(f"缺陷分析失敗: {str(e)}", extra={'error_id': error_info.error_id})
            raise
    
    def _define_test_objectives(self, requirements: List[str], test_scope: List[str]) -> List[str]:
        """定義測試目標"""
        objectives = [
            "驗證功能需求的正確性和完整性",
            "確保系統性能符合預期標準",
            "驗證系統安全性和穩定性",
            "確保用戶體驗符合設計要求"
        ]
        
        # 基於需求添加特定目標
        requirements_text = " ".join(requirements).lower()
        if "api" in requirements_text:
            objectives.append("驗證API接口的正確性和穩定性")
        if "database" in requirements_text:
            objectives.append("驗證數據完整性和一致性")
        if "security" in requirements_text:
            objectives.append("執行全面的安全測試")
        
        return objectives
    
    def _design_test_strategy(self, requirements: List[str], constraints: Optional[List[str]]) -> Dict[str, Any]:
        """設計測試策略"""
        strategy = {
            'approach': 'risk-based testing',
            'test_levels': [
                TestType.UNIT.value,
                TestType.INTEGRATION.value,
                TestType.FUNCTIONAL.value,
                TestType.REGRESSION.value
            ],
            'automation_strategy': {
                'target_automation_rate': self.test_automation_goal,
                'automation_tools': ['pytest', 'selenium', 'postman'],
                'ci_cd_integration': True
            },
            'test_data_strategy': {
                'data_generation': 'automated',
                'test_data_management': 'version_controlled',
                'data_privacy_compliance': True
            },
            'environment_strategy': {
                'test_environments': ['dev', 'staging', 'production-like'],
                'environment_provisioning': 'automated',
                'data_refresh_strategy': 'weekly'
            },
            'risk_mitigation': {
                'high_risk_areas': self._identify_high_risk_areas(requirements),
                'mitigation_approaches': ['intensive_testing', 'pair_testing', 'exploratory_testing']
            }
        }
        
        return strategy
    
    def _design_test_cases(self, requirements: List[str], test_scope: List[str]) -> List[Dict[str, Any]]:
        """設計測試用例"""
        test_cases = []
        
        for i, requirement in enumerate(requirements, 1):
            # 正面測試用例
            test_cases.append({
                'test_case_id': f"TC_{i:03d}_POSITIVE",
                'test_name': f"驗證{requirement} - 正面流程",
                'test_type': TestType.FUNCTIONAL.value,
                'priority': TestPriority.HIGH.value,
                'preconditions': ["系統正常運行", "測試數據已準備"],
                'test_steps': [
                    f"準備符合{requirement}的測試數據",
                    "執行功能操作",
                    "驗證結果符合期望"
                ],
                'expected_result': f"{requirement}功能正常工作",
                'automation_candidate': True
            })
            
            # 負面測試用例
            test_cases.append({
                'test_case_id': f"TC_{i:03d}_NEGATIVE",
                'test_name': f"驗證{requirement} - 異常處理",
                'test_type': TestType.FUNCTIONAL.value,
                'priority': TestPriority.MEDIUM.value,
                'preconditions': ["系統正常運行"],
                'test_steps': [
                    f"準備無效的{requirement}測試數據",
                    "執行功能操作",
                    "驗證錯誤處理機制"
                ],
                'expected_result': "系統正確處理異常情況",
                'automation_candidate': True
            })
        
        # 邊界測試用例
        test_cases.append({
            'test_case_id': "TC_BOUNDARY_001",
            'test_name': "邊界值測試",
            'test_type': TestType.FUNCTIONAL.value,
            'priority': TestPriority.HIGH.value,
            'preconditions': ["系統正常運行"],
            'test_steps': [
                "測試最小邊界值",
                "測試最大邊界值",
                "測試邊界值±1"
            ],
            'expected_result': "邊界值處理正確",
            'automation_candidate': True
        })
        
        return test_cases
    
    def _create_test_schedule(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """創建測試時程"""
        total_test_cases = len(test_cases)
        
        # 估算測試執行時間
        execution_estimates = {
            'unit_testing': total_test_cases * 0.1,  # 每個測試用例0.1小時
            'integration_testing': total_test_cases * 0.2,
            'functional_testing': total_test_cases * 0.3,
            'regression_testing': total_test_cases * 0.15,
            'test_planning': 8,
            'test_environment_setup': 4,
            'test_reporting': 6
        }
        
        total_hours = sum(execution_estimates.values())
        
        schedule = {
            'total_estimated_hours': total_hours,
            'total_estimated_days': total_hours / 8,  # 假設每天8小時
            'phases': {
                'planning': {'duration_days': 1, 'dependencies': []},
                'environment_setup': {'duration_days': 0.5, 'dependencies': ['planning']},
                'unit_testing': {'duration_days': execution_estimates['unit_testing'] / 8, 'dependencies': ['environment_setup']},
                'integration_testing': {'duration_days': execution_estimates['integration_testing'] / 8, 'dependencies': ['unit_testing']},
                'functional_testing': {'duration_days': execution_estimates['functional_testing'] / 8, 'dependencies': ['integration_testing']},
                'regression_testing': {'duration_days': execution_estimates['regression_testing'] / 8, 'dependencies': ['functional_testing']},
                'reporting': {'duration_days': 0.75, 'dependencies': ['regression_testing']}
            },
            'milestones': [
                {'name': '測試計劃完成', 'date': 'Day 1'},
                {'name': '單元測試完成', 'date': f'Day {2 + execution_estimates["unit_testing"] / 8:.1f}'},
                {'name': '功能測試完成', 'date': f'Day {4 + (execution_estimates["unit_testing"] + execution_estimates["integration_testing"] + execution_estimates["functional_testing"]) / 8:.1f}'},
                {'name': '測試執行完成', 'date': f'Day {total_hours / 8:.1f}'}
            ]
        }
        
        return schedule
    
    def _assess_resource_requirements(self, test_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """評估資源需求"""
        return {
            'human_resources': {
                'test_engineers': 2,
                'automation_engineers': 1,
                'performance_testers': 1,
                'test_manager': 0.5
            },
            'infrastructure': {
                'test_servers': 3,
                'test_databases': 2,
                'test_data_storage': '100GB',
                'network_bandwidth': '100Mbps'
            },
            'tools_and_licenses': {
                'test_automation_tools': ['pytest', 'selenium'],
                'performance_testing_tools': ['locust', 'jmeter'],
                'test_management_tools': ['testlink', 'jira'],
                'ci_cd_tools': ['jenkins', 'gitlab-ci']
            },
            'budget_estimate': {
                'personnel_cost': 50000,
                'infrastructure_cost': 5000,
                'tools_and_licenses': 3000,
                'total_budget': 58000
            }
        }
    
    def _assess_testing_risks(self, project_name: str, constraints: Optional[List[str]]) -> List[Dict[str, Any]]:
        """評估測試風險"""
        risks = [
            {
                'risk_id': 'RISK_001',
                'description': '測試環境不穩定導致測試執行延遲',
                'probability': 'medium',
                'impact': 'high',
                'mitigation_strategy': '建立備用測試環境，實施環境監控'
            },
            {
                'risk_id': 'RISK_002',
                'description': '測試數據準備不充分',
                'probability': 'low',
                'impact': 'medium',
                'mitigation_strategy': '自動化測試數據生成，建立數據管理流程'
            },
            {
                'risk_id': 'RISK_003',
                'description': '關鍵缺陷在生產環境發現',
                'probability': 'low',
                'impact': 'critical',
                'mitigation_strategy': '加強生產環境類似測試，實施風險導向測試'
            }
        ]
        
        # 基於約束條件添加特定風險
        if constraints:
            for constraint in constraints:
                if 'time' in constraint.lower():
                    risks.append({
                        'risk_id': 'RISK_TIME_001',
                        'description': '時間約束導致測試覆蓋不足',
                        'probability': 'high',
                        'impact': 'medium',
                        'mitigation_strategy': '優先測試關鍵功能，實施風險導向測試'
                    })
        
        return risks
    
    def _define_entry_criteria(self, requirements: List[str]) -> List[str]:
        """定義進入標準"""
        return [
            "需求文檔已完成並經過審查",
            "測試環境已搭建並驗證可用",
            "測試數據已準備並驗證",
            "代碼已通過基本的單元測試",
            "構建版本已部署到測試環境",
            "測試用例已設計並通過審查"
        ]
    
    def _define_exit_criteria(self, test_objectives: List[str]) -> List[str]:
        """定義退出標準"""
        return [
            f"代碼覆蓋率達到{self.coverage_threshold * 100}%以上",
            "所有高優先級測試用例執行完成",
            "無阻塞性(Blocker)和關鍵性(Critical)缺陷",
            "系統性能符合預期標準",
            "安全測試通過所有檢查點",
            "測試報告已生成並經過審查"
        ]
    
    def _define_test_deliverables(self, test_strategy: Dict[str, Any]) -> List[str]:
        """定義測試交付物"""
        return [
            "測試計劃文檔",
            "測試用例規格說明",
            "測試執行報告",
            "缺陷分析報告",
            "測試覆蓋率報告",
            "性能測試報告",
            "自動化測試腳本",
            "測試環境配置文檔"
        ]
    
    def _configure_test_environment(self, test_strategy: Dict[str, Any]) -> Dict[str, str]:
        """配置測試環境"""
        return {
            'test_framework': 'pytest',
            'automation_tool': 'selenium',
            'api_testing_tool': 'postman',
            'performance_testing_tool': 'locust',
            'database': 'postgresql',
            'ci_cd_platform': 'gitlab-ci',
            'test_reporting_tool': 'allure',
            'container_platform': 'docker',
            'monitoring_tool': 'prometheus'
        }
    
    def _execute_test_suite(self, test_suite: str) -> Dict[str, Any]:
        """執行測試套件"""
        # 模擬測試執行結果
        test_results = {
            'unit_tests': {
                'total': 45,
                'passed': 42,
                'failed': 3,
                'skipped': 0,
                'execution_time': 12.5
            },
            'integration_tests': {
                'total': 28,
                'passed': 26,
                'failed': 1,
                'skipped': 1,
                'execution_time': 45.2
            },
            'functional_tests': {
                'total': 35,
                'passed': 33,
                'failed': 2,
                'skipped': 0,
                'execution_time': 78.3
            },
            'api_tests': {
                'total': 22,
                'passed': 21,
                'failed': 1,
                'skipped': 0,
                'execution_time': 15.7
            }
        }
        
        return test_results
    
    def _calculate_test_statistics(self, execution: TestExecution) -> None:
        """計算測試統計"""
        execution.passed_tests = 0
        execution.failed_tests = 0
        execution.skipped_tests = 0
        execution.execution_time = 0.0
        
        for test_type, results in execution.test_results.items():
            execution.passed_tests += results.get('passed', 0)
            execution.failed_tests += results.get('failed', 0)
            execution.skipped_tests += results.get('skipped', 0)
            execution.execution_time += results.get('execution_time', 0)
        
        execution.total_tests = execution.passed_tests + execution.failed_tests + execution.skipped_tests
    
    def _generate_coverage_report(self, test_suite: str) -> Dict[str, Any]:
        """生成覆蓋率報告"""
        return {
            'line_coverage': 0.85,
            'branch_coverage': 0.78,
            'function_coverage': 0.92,
            'class_coverage': 0.88,
            'overall_coverage': 0.86,
            'uncovered_files': [
                'utils/legacy_helper.py',
                'config/deprecated_settings.py'
            ],
            'coverage_by_module': {
                'core': 0.95,
                'api': 0.88,
                'utils': 0.72,
                'models': 0.91,
                'services': 0.83
            }
        }
    
    def _analyze_test_failures(self, test_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析測試失敗"""
        defects = []
        defect_id = 1
        
        for test_type, results in test_results.items():
            failed_count = results.get('failed', 0)
            
            for i in range(failed_count):
                defects.append({
                    'defect_id': f"DEF_{defect_id:03d}",
                    'test_type': test_type,
                    'severity': random.choice([DefectSeverity.CRITICAL.value, DefectSeverity.MAJOR.value, DefectSeverity.MINOR.value]),
                    'description': f"{test_type}中發現的功能缺陷",
                    'reproduction_steps': [
                        "執行測試用例",
                        "輸入測試數據",
                        "驗證結果"
                    ],
                    'expected_behavior': "功能正常工作",
                    'actual_behavior': "功能異常或錯誤",
                    'environment': "測試環境",
                    'priority': TestPriority.HIGH.value,
                    'assigned_to': "development_team",
                    'found_by': self.name,
                    'found_date': datetime.now().isoformat()
                })
                defect_id += 1
        
        return defects
    
    def _generate_test_artifacts(self, execution: TestExecution) -> List[str]:
        """生成測試工件"""
        return [
            f"test_execution_report_{execution.execution_id}.html",
            f"coverage_report_{execution.execution_id}.html",
            f"test_results_{execution.execution_id}.xml",
            f"performance_metrics_{execution.execution_id}.json",
            f"defect_report_{execution.execution_id}.pdf"
        ]
    
    def _generate_execution_notes(self, execution: TestExecution) -> str:
        """生成執行備註"""
        pass_rate = (execution.passed_tests / execution.total_tests * 100) if execution.total_tests > 0 else 0
        
        notes = f"""測試執行摘要:
- 通過率: {pass_rate:.1f}%
- 執行時間: {execution.execution_time:.1f}秒
- 發現缺陷: {len(execution.defects_found)}個
- 測試環境: {execution.test_environment.get('platform', '未指定')}

關鍵發現:
"""
        
        if execution.failed_tests > 0:
            notes += f"- 發現{execution.failed_tests}個測試失敗，需要開發團隊檢查\n"
        
        if execution.coverage_report.get('overall_coverage', 0) < self.coverage_threshold:
            notes += "- 代碼覆蓋率未達到標準，建議增加測試用例\n"
        
        if not execution.defects_found:
            notes += "- 所有測試通過，品質狀況良好\n"
        
        return notes
    
    def _calculate_quality_metrics(self, test_executions: List[TestExecution]) -> Dict[str, float]:
        """計算品質指標"""
        if not test_executions:
            return {}
        
        total_tests = sum(execution.total_tests for execution in test_executions)
        total_passed = sum(execution.passed_tests for execution in test_executions)
        total_defects = sum(len(execution.defects_found) for execution in test_executions)
        
        # 計算各項指標
        test_pass_rate = (total_passed / total_tests) if total_tests > 0 else 0
        defect_density = total_defects / total_tests if total_tests > 0 else 0
        
        # 平均覆蓋率
        avg_coverage = sum(
            execution.coverage_report.get('overall_coverage', 0) 
            for execution in test_executions
        ) / len(test_executions)
        
        # 自動化率（模擬）
        automation_rate = 0.75
        
        # 平均檢測時間（模擬）
        mean_time_to_detect = 2.5  # 小時
        
        # 平均解決時間（模擬）
        mean_time_to_resolve = 8.0  # 小時
        
        # 綜合品質評分
        overall_quality_score = (
            test_pass_rate * 0.3 +
            avg_coverage * 0.25 +
            (1 - defect_density) * 0.2 +
            automation_rate * 0.15 +
            (1 - mean_time_to_detect / 24) * 0.05 +
            (1 - mean_time_to_resolve / 48) * 0.05
        )
        
        return {
            QualityMetric.TEST_PASS_RATE.value: test_pass_rate,
            QualityMetric.CODE_COVERAGE.value: avg_coverage,
            QualityMetric.DEFECT_DENSITY.value: defect_density,
            QualityMetric.AUTOMATION_RATE.value: automation_rate,
            QualityMetric.MEAN_TIME_TO_DETECT.value: mean_time_to_detect,
            QualityMetric.MEAN_TIME_TO_RESOLVE.value: mean_time_to_resolve,
            'overall_quality_score': overall_quality_score
        }
    
    def _generate_test_summary(self, test_executions: List[TestExecution]) -> Dict[str, Any]:
        """生成測試摘要"""
        total_executions = len(test_executions)
        total_tests = sum(execution.total_tests for execution in test_executions)
        total_passed = sum(execution.passed_tests for execution in test_executions)
        total_failed = sum(execution.failed_tests for execution in test_executions)
        total_defects = sum(len(execution.defects_found) for execution in test_executions)
        
        return {
            'total_test_executions': total_executions,
            'total_test_cases': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_defects_found': total_defects,
            'pass_rate': (total_passed / total_tests) if total_tests > 0 else 0,
            'execution_summary': {
                'fastest_execution': min(execution.execution_time for execution in test_executions),
                'slowest_execution': max(execution.execution_time for execution in test_executions),
                'average_execution_time': sum(execution.execution_time for execution in test_executions) / total_executions
            }
        }
    
    def _analyze_defects(self, test_executions: List[TestExecution]) -> Dict[str, Any]:
        """分析缺陷"""
        all_defects = []
        for execution in test_executions:
            all_defects.extend(execution.defects_found)
        
        if not all_defects:
            return {'total_defects': 0, 'severity_distribution': {}}
        
        severity_counts = {}
        for defect in all_defects:
            severity = defect.get('severity', 'unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_defects': len(all_defects),
            'severity_distribution': severity_counts,
            'defect_trends': {
                'new_defects': len(all_defects),
                'resolved_defects': 0,
                'open_defects': len(all_defects)
            },
            'defect_categories': self._categorize_defects(all_defects),
            'top_defect_areas': self._identify_top_defect_areas(all_defects)
        }
    
    def _analyze_coverage(self, test_executions: List[TestExecution]) -> Dict[str, Any]:
        """分析覆蓋率"""
        if not test_executions:
            return {}
        
        coverage_data = []
        for execution in test_executions:
            coverage_report = execution.coverage_report
            if coverage_report:
                coverage_data.append(coverage_report)
        
        if not coverage_data:
            return {}
        
        avg_coverage = sum(report.get('overall_coverage', 0) for report in coverage_data) / len(coverage_data)
        
        return {
            'average_coverage': avg_coverage,
            'coverage_trend': 'improving' if avg_coverage > 0.8 else 'needs_improvement',
            'uncovered_areas': self._identify_uncovered_areas(coverage_data),
            'coverage_goals_met': avg_coverage >= self.coverage_threshold,
            'recommendations': self._generate_coverage_recommendations(avg_coverage)
        }
    
    def _assess_quality_risks(self, quality_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """評估品質風險"""
        risks = []
        
        # 測試通過率風險
        pass_rate = quality_metrics.get(QualityMetric.TEST_PASS_RATE.value, 0)
        if pass_rate < 0.9:
            risks.append({
                'risk_type': 'low_test_pass_rate',
                'severity': 'high' if pass_rate < 0.8 else 'medium',
                'description': f'測試通過率僅為{pass_rate:.1%}，存在品質風險',
                'impact': '可能影響產品穩定性和用戶體驗',
                'recommendation': '增加測試覆蓋，修復失敗的測試用例'
            })
        
        # 覆蓋率風險
        coverage = quality_metrics.get(QualityMetric.CODE_COVERAGE.value, 0)
        if coverage < self.coverage_threshold:
            risks.append({
                'risk_type': 'insufficient_coverage',
                'severity': 'medium',
                'description': f'代碼覆蓋率僅為{coverage:.1%}，低於標準{self.coverage_threshold:.1%}',
                'impact': '可能存在未測試的代碼路徑',
                'recommendation': '增加測試用例，提高關鍵功能的覆蓋率'
            })
        
        # 缺陷密度風險
        defect_density = quality_metrics.get(QualityMetric.DEFECT_DENSITY.value, 0)
        if defect_density > self.defect_density_threshold:
            risks.append({
                'risk_type': 'high_defect_density',
                'severity': 'high',
                'description': f'缺陷密度為{defect_density:.3f}，超過標準{self.defect_density_threshold:.3f}',
                'impact': '代碼品質可能存在問題，影響系統穩定性',
                'recommendation': '加強代碼審查，改進開發流程'
            })
        
        return risks
    
    def _generate_quality_recommendations(self, report: QualityReport) -> List[str]:
        """生成品質改進建議"""
        recommendations = []
        
        # 基於品質指標生成建議
        quality_metrics = report.quality_metrics
        
        if quality_metrics.get(QualityMetric.TEST_PASS_RATE.value, 0) < 0.9:
            recommendations.append("提高測試通過率，分析和修復失敗的測試用例")
        
        if quality_metrics.get(QualityMetric.CODE_COVERAGE.value, 0) < self.coverage_threshold:
            recommendations.append("增加測試覆蓋率，重點關注核心業務邏輯")
        
        if quality_metrics.get(QualityMetric.AUTOMATION_RATE.value, 0) < self.test_automation_goal:
            recommendations.append("提高測試自動化率，減少手動測試工作量")
        
        # 通用建議
        recommendations.extend([
            "實施持續集成，確保每次提交都經過測試",
            "建立測試左移策略，在開發早期發現問題",
            "定期進行代碼審查，提高代碼品質",
            "建立品質門檻，確保達標才能部署"
        ])
        
        return recommendations
    
    def _generate_quality_action_items(self, report: QualityReport) -> List[Dict[str, Any]]:
        """生成品質行動項目"""
        action_items = []
        
        # 基於風險評估生成行動項目
        for risk in report.risk_assessment:
            if risk.get('severity') in ['high', 'critical']:
                action_items.append({
                    'action_id': f"ACTION_{len(action_items) + 1:03d}",
                    'title': f"解決{risk['risk_type']}風險",
                    'description': risk['recommendation'],
                    'priority': 'high',
                    'assigned_to': 'qa_team',
                    'due_date': '2 weeks',
                    'success_criteria': f"改善{risk['risk_type']}指標"
                })
        
        # 常規改進項目
        action_items.extend([
            {
                'action_id': f"ACTION_{len(action_items) + 1:03d}",
                'title': '建立自動化測試框架',
                'description': '設計和實施統一的自動化測試框架',
                'priority': 'medium',
                'assigned_to': 'automation_team',
                'due_date': '1 month',
                'success_criteria': '自動化率達到70%以上'
            },
            {
                'action_id': f"ACTION_{len(action_items) + 1:03d}",
                'title': '建立品質監控儀表板',
                'description': '實施實時品質指標監控',
                'priority': 'low',
                'assigned_to': 'devops_team',
                'due_date': '3 weeks',
                'success_criteria': '儀表板正常運行並提供即時數據'
            }
        ])
        
        return action_items
    
    def _analyze_quality_trends(self, test_executions: List[TestExecution]) -> Dict[str, Any]:
        """分析品質趨勢"""
        if len(test_executions) < 2:
            return {'trend_analysis': '數據不足，無法分析趨勢'}
        
        # 計算趨勢（簡化實現）
        latest_execution = test_executions[-1]
        previous_execution = test_executions[-2]
        
        latest_pass_rate = latest_execution.passed_tests / latest_execution.total_tests if latest_execution.total_tests > 0 else 0
        previous_pass_rate = previous_execution.passed_tests / previous_execution.total_tests if previous_execution.total_tests > 0 else 0
        
        pass_rate_trend = 'improving' if latest_pass_rate > previous_pass_rate else 'declining' if latest_pass_rate < previous_pass_rate else 'stable'
        
        return {
            'pass_rate_trend': pass_rate_trend,
            'defect_trend': 'stable',  # 簡化
            'coverage_trend': 'improving',  # 簡化
            'overall_trend': 'improving' if pass_rate_trend == 'improving' else 'stable',
            'trend_summary': f'品質趨勢整體{pass_rate_trend}，建議持續監控'
        }
    
    def _check_quality_compliance(self, quality_metrics: Dict[str, float]) -> Dict[str, bool]:
        """檢查品質合規性"""
        return {
            'coverage_compliance': quality_metrics.get(QualityMetric.CODE_COVERAGE.value, 0) >= self.coverage_threshold,
            'pass_rate_compliance': quality_metrics.get(QualityMetric.TEST_PASS_RATE.value, 0) >= 0.9,
            'defect_density_compliance': quality_metrics.get(QualityMetric.DEFECT_DENSITY.value, 1) <= self.defect_density_threshold,
            'automation_compliance': quality_metrics.get(QualityMetric.AUTOMATION_RATE.value, 0) >= self.test_automation_goal,
            'overall_compliance': all([
                quality_metrics.get(QualityMetric.CODE_COVERAGE.value, 0) >= self.coverage_threshold,
                quality_metrics.get(QualityMetric.TEST_PASS_RATE.value, 0) >= 0.9,
                quality_metrics.get(QualityMetric.DEFECT_DENSITY.value, 1) <= self.defect_density_threshold
            ])
        }
    
    def _analyze_defect_severity_distribution(self, defects: List[Dict[str, Any]]) -> Dict[str, int]:
        """分析缺陷嚴重程度分佈"""
        distribution = {}
        for defect in defects:
            severity = defect.get('severity', 'unknown')
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def _perform_root_cause_analysis(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """執行根本原因分析"""
        return {
            'common_root_causes': [
                '需求理解不清晰',
                '代碼審查不充分',
                '測試覆蓋不足',
                '環境配置問題'
            ],
            'primary_cause': '需求理解不清晰',
            'contributing_factors': [
                '溝通不足',
                '文檔不完整',
                '時間壓力'
            ],
            'prevention_measures': [
                '加強需求澄清流程',
                '實施配對程式設計',
                '增加代碼審查強度'
            ]
        }
    
    def _categorize_defects(self, defects: List[Dict[str, Any]]) -> Dict[str, int]:
        """分類缺陷"""
        categories = {
            'functional': 0,
            'performance': 0,
            'usability': 0,
            'security': 0,
            'compatibility': 0,
            'other': 0
        }
        
        for defect in defects:
            # 簡化的分類邏輯
            description = defect.get('description', '').lower()
            if 'functional' in description or 'function' in description:
                categories['functional'] += 1
            elif 'performance' in description or 'slow' in description:
                categories['performance'] += 1
            elif 'security' in description or 'auth' in description:
                categories['security'] += 1
            else:
                categories['functional'] += 1  # 默認為功能缺陷
        
        return categories
    
    def _analyze_defect_trends(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析缺陷趨勢"""
        return {
            'trend_direction': 'increasing',
            'weekly_defect_count': len(defects),
            'severity_trend': {
                'critical_increasing': True,
                'major_stable': True,
                'minor_decreasing': False
            },
            'resolution_time_trend': 'improving'
        }
    
    def _assess_defect_impact(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """評估缺陷影響"""
        critical_defects = len([d for d in defects if d.get('severity') == DefectSeverity.CRITICAL.value])
        major_defects = len([d for d in defects if d.get('severity') == DefectSeverity.MAJOR.value])
        
        return {
            'business_impact': 'medium' if critical_defects > 0 else 'low',
            'user_experience_impact': 'high' if critical_defects > 2 else 'medium',
            'system_stability_impact': 'medium' if major_defects > 5 else 'low',
            'estimated_fix_effort': f'{len(defects) * 2} hours',
            'risk_to_release': 'medium' if critical_defects > 0 else 'low'
        }
    
    def _suggest_prevention_strategies(self, defects: List[Dict[str, Any]]) -> List[str]:
        """建議預防策略"""
        return [
            "實施測試驅動開發(TDD)",
            "加強代碼審查流程",
            "建立自動化品質門檻",
            "定期進行技術債務清理",
            "實施配對程式設計",
            "加強需求澄清和驗證"
        ]
    
    def _rank_defect_priorities(self, defects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """排序缺陷優先級"""
        severity_weights = {
            DefectSeverity.BLOCKER.value: 5,
            DefectSeverity.CRITICAL.value: 4,
            DefectSeverity.MAJOR.value: 3,
            DefectSeverity.MINOR.value: 2,
            DefectSeverity.TRIVIAL.value: 1
        }
        
        ranked_defects = sorted(
            defects,
            key=lambda x: severity_weights.get(x.get('severity', 'trivial'), 1),
            reverse=True
        )
        
        return ranked_defects[:10]  # 返回前10個高優先級缺陷
    
    def _estimate_fix_resources(self, defects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """估算修復資源"""
        severity_hours = {
            DefectSeverity.BLOCKER.value: 8,
            DefectSeverity.CRITICAL.value: 6,
            DefectSeverity.MAJOR.value: 4,
            DefectSeverity.MINOR.value: 2,
            DefectSeverity.TRIVIAL.value: 1
        }
        
        total_hours = 0
        for defect in defects:
            severity = defect.get('severity', DefectSeverity.TRIVIAL.value)
            total_hours += severity_hours.get(severity, 1)
        
        return {
            'total_estimated_hours': total_hours,
            'total_estimated_days': total_hours / 8,
            'required_developers': max(1, total_hours // 40),  # 假設每個開發者每週40小時
            'estimated_cost': total_hours * 100,  # 假設每小時100元
            'critical_path_items': len([d for d in defects if d.get('severity') in [DefectSeverity.BLOCKER.value, DefectSeverity.CRITICAL.value]])
        }
    
    def _suggest_quality_improvements(self, defects: List[Dict[str, Any]]) -> List[str]:
        """建議品質改進"""
        return [
            "建立缺陷預防檢查清單",
            "實施靜態代碼分析",
            "加強單元測試覆蓋率",
            "建立品質度量儀表板",
            "定期進行品質回顧會議",
            "實施持續改進流程"
        ]
    
    def _identify_high_risk_areas(self, requirements: List[str]) -> List[str]:
        """識別高風險區域"""
        high_risk_areas = []
        
        requirements_text = " ".join(requirements).lower()
        
        if "payment" in requirements_text or "financial" in requirements_text:
            high_risk_areas.append("支付和金融功能")
        
        if "authentication" in requirements_text or "auth" in requirements_text:
            high_risk_areas.append("認證和授權系統")
        
        if "database" in requirements_text or "data" in requirements_text:
            high_risk_areas.append("數據處理和存儲")
        
        if "api" in requirements_text:
            high_risk_areas.append("API接口")
        
        high_risk_areas.append("核心業務邏輯")
        
        return high_risk_areas
    
    def _identify_uncovered_areas(self, coverage_data: List[Dict[str, Any]]) -> List[str]:
        """識別未覆蓋區域"""
        uncovered_areas = []
        
        for coverage_report in coverage_data:
            uncovered_files = coverage_report.get('uncovered_files', [])
            uncovered_areas.extend(uncovered_files)
        
        # 去重並返回
        return list(set(uncovered_areas))
    
    def _generate_coverage_recommendations(self, avg_coverage: float) -> List[str]:
        """生成覆蓋率改進建議"""
        recommendations = []
        
        if avg_coverage < 0.6:
            recommendations.append("覆蓋率過低，需要大幅增加測試用例")
            recommendations.append("優先為核心功能編寫測試")
        elif avg_coverage < 0.8:
            recommendations.append("覆蓋率尚可，建議持續改進")
            recommendations.append("關注邊界條件和異常處理的測試")
        else:
            recommendations.append("覆蓋率良好，保持現有水準")
            recommendations.append("重點關注測試品質而非數量")
        
        recommendations.extend([
            "定期檢查和更新測試用例",
            "實施測試驅動開發(TDD)",
            "建立覆蓋率監控機制"
        ])
        
        return recommendations
    
    def _identify_top_defect_areas(self, defects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """識別主要缺陷區域"""
        area_counts = {}
        
        for defect in defects:
            test_type = defect.get('test_type', 'unknown')
            area_counts[test_type] = area_counts.get(test_type, 0) + 1
        
        # 排序並返回前5個區域
        sorted_areas = sorted(area_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'area': area, 'defect_count': count, 'percentage': count / len(defects) * 100}
            for area, count in sorted_areas[:5]
        ]
    
    def get_agent_status(self) -> Dict[str, Any]:
        """獲取代理人狀態"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'name': self.name,
            'expertise_areas': self.expertise_areas,
            'statistics': {
                'test_plans_created': self.test_plans_created,
                'test_executions_conducted': self.test_executions_conducted,
                'defects_analyzed': self.defects_analyzed,
                'quality_reports_generated': self.quality_reports_generated
            },
            'quality_standards': {
                'coverage_threshold': self.coverage_threshold,
                'defect_density_threshold': self.defect_density_threshold,
                'test_automation_goal': self.test_automation_goal
            },
            'status': 'active',
            'last_updated': datetime.now().isoformat()
        }

if __name__ == "__main__":
    # 測試腳本
    async def test_qa_guardian():
        print("測試品質保證守護者狄仁傑...")
        
        guardian = QAGuardianDirenjie({
            'coverage_threshold': 0.8,
            'defect_density_threshold': 0.1,
            'test_automation_goal': 0.7
        })
        
        # 測試創建測試計劃
        test_plan = await guardian.create_test_plan(
            "TradingAgents系統",
            ['用戶認證', 'AI分析', '數據處理', 'API接口'],
            ['功能測試', '性能測試', '安全測試'],
            ['時間限制', '資源限制']
        )
        
        print(f"測試計劃創建完成: {test_plan.plan_id}")
        print(f"測試目標數量: {len(test_plan.test_objectives)}")
        print(f"測試用例數量: {len(test_plan.test_cases)}")
        
        # 測試執行測試
        test_execution = await guardian.execute_tests(
            test_plan.plan_id,
            "comprehensive_test_suite",
            {'platform': 'linux', 'python_version': '3.11'}
        )
        
        print(f"測試執行完成: {test_execution.execution_id}")
        print(f"通過測試: {test_execution.passed_tests}")
        print(f"失敗測試: {test_execution.failed_tests}")
        print(f"發現缺陷: {len(test_execution.defects_found)}")
        
        # 測試缺陷分析
        if test_execution.defects_found:
            defect_analysis = await guardian.analyze_defects(test_execution.defects_found)
            print(f"缺陷分析完成: {defect_analysis['analysis_id']}")
            print(f"總缺陷數: {defect_analysis['total_defects']}")
        
        # 測試生成品質報告
        quality_report = await guardian.generate_quality_report(
            "TradingAgents系統",
            [test_execution],
            "weekly"
        )
        
        print(f"品質報告生成完成: {quality_report.report_id}")
        print(f"品質評分: {quality_report.quality_metrics.get('overall_quality_score', 0):.2f}")
        print(f"建議數量: {len(quality_report.recommendations)}")
        
        # 獲取代理人狀態
        status = guardian.get_agent_status()
        print(f"代理人狀態: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        print("品質保證守護者狄仁傑測試完成")
    
    asyncio.run(test_qa_guardian())