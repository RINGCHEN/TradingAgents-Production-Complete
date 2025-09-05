#!/usr/bin/env python3
"""
天工開物測試框架 (TianGong Test Framework)
專為天工開物協調系統設計的綜合測試和驗證機制

此模組提供：
1. 代理人功能測試
2. 協調系統整合測試
3. 工作流執行測試
4. 性能壓力測試
5. 安全性測試
6. 容錯機制測試
7. 自動化測試報告

由狄仁傑(品質守護者)設計實現
"""

import asyncio
import pytest
import unittest
import time
import threading
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json
import logging
import traceback
import statistics
from contextlib import asynccontextmanager

from ..coordination import (
    TianGongCoordinationService,
    create_tiangong_service,
    create_project_context,
    ProjectType,
    TaskPriority,
    setup_coordination_system
)
from ..utils.logging_config import get_system_logger
from ..utils.performance_monitor import PerformanceCollector, PerformanceAnalyzer
from ..utils.resilience_manager import ResilienceManager

logger = get_system_logger("tiangong_test_framework")

class TestType(Enum):
    """測試類型"""
    UNIT = "unit"
    INTEGRATION = "integration"
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STRESS = "stress"
    SMOKE = "smoke"
    REGRESSION = "regression"

class TestStatus(Enum):
    """測試狀態"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

class TestSeverity(Enum):
    """測試嚴重性"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class TestCase:
    """測試用例"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    test_type: TestType = TestType.UNIT
    severity: TestSeverity = TestSeverity.MEDIUM
    test_function: Optional[Callable] = None
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    timeout_seconds: int = 30
    expected_result: Optional[Any] = None
    test_data: Dict[str, Any] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TestResult:
    """測試結果"""
    test_id: str = ""
    test_name: str = ""
    status: TestStatus = TestStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0
    actual_result: Optional[Any] = None
    expected_result: Optional[Any] = None
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'test_id': self.test_id,
            'test_name': self.test_name,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'execution_time': self.execution_time,
            'actual_result': str(self.actual_result) if self.actual_result is not None else None,
            'expected_result': str(self.expected_result) if self.expected_result is not None else None,
            'error_message': self.error_message,
            'assertions_passed': self.assertions_passed,
            'assertions_failed': self.assertions_failed,
            'performance_metrics': self.performance_metrics,
            'logs_count': len(self.logs)
        }

@dataclass
class TestSuite:
    """測試套件"""
    suite_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    test_cases: List[TestCase] = field(default_factory=list)
    setup_suite: Optional[Callable] = None
    teardown_suite: Optional[Callable] = None
    parallel_execution: bool = False
    max_parallel_tests: int = 3
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TestReport:
    """測試報告"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_session_id: str = ""
    suite_name: str = ""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    success_rate: float = 0.0
    total_execution_time: float = 0.0
    test_results: List[TestResult] = field(default_factory=list)
    performance_summary: Dict[str, Any] = field(default_factory=dict)
    coverage_data: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

class TestAssertion:
    """測試斷言"""
    
    def __init__(self, test_result: TestResult):
        self.test_result = test_result
    
    def assert_equal(self, actual, expected, message: str = ""):
        """斷言相等"""
        try:
            assert actual == expected, message or f"Expected {expected}, but got {actual}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_not_equal(self, actual, expected, message: str = ""):
        """斷言不相等"""
        try:
            assert actual != expected, message or f"Expected {actual} != {expected}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_true(self, condition, message: str = ""):
        """斷言為真"""
        try:
            assert condition is True, message or f"Expected True, but got {condition}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_false(self, condition, message: str = ""):
        """斷言為假"""
        try:
            assert condition is False, message or f"Expected False, but got {condition}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_is_none(self, value, message: str = ""):
        """斷言為None"""
        try:
            assert value is None, message or f"Expected None, but got {value}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_is_not_none(self, value, message: str = ""):
        """斷言不為None"""
        try:
            assert value is not None, message or f"Expected not None, but got None"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_in(self, item, container, message: str = ""):
        """斷言包含"""
        try:
            assert item in container, message or f"Expected {item} in {container}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_greater(self, actual, expected, message: str = ""):
        """斷言大於"""
        try:
            assert actual > expected, message or f"Expected {actual} > {expected}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise
    
    def assert_less(self, actual, expected, message: str = ""):
        """斷言小於"""
        try:
            assert actual < expected, message or f"Expected {actual} < {expected}"
            self.test_result.assertions_passed += 1
            return True
        except AssertionError as e:
            self.test_result.assertions_failed += 1
            self.test_result.logs.append(f"斷言失敗: {str(e)}")
            raise

class TianGongTestRunner:
    """天工開物測試運行器"""
    
    def __init__(self):
        self.test_suites: Dict[str, TestSuite] = {}
        self.test_results: Dict[str, List[TestResult]] = {}
        self.performance_collector = PerformanceCollector(collection_interval=1.0)
        self.current_session_id = None
    
    def register_test_suite(self, test_suite: TestSuite):
        """註冊測試套件"""
        self.test_suites[test_suite.suite_id] = test_suite
        logger.info(f"註冊測試套件: {test_suite.name} ({len(test_suite.test_cases)} 個測試用例)")
    
    async def run_test_suite(self, suite_id: str) -> TestReport:
        """運行測試套件"""
        
        if suite_id not in self.test_suites:
            raise ValueError(f"測試套件不存在: {suite_id}")
        
        test_suite = self.test_suites[suite_id]
        self.current_session_id = str(uuid.uuid4())
        
        logger.info(f"開始運行測試套件: {test_suite.name}")
        
        # 啟動性能監控
        await self.performance_collector.start_collection()
        
        suite_start_time = time.time()
        test_results = []
        
        try:
            # 執行套件設置
            if test_suite.setup_suite:
                try:
                    if asyncio.iscoroutinefunction(test_suite.setup_suite):
                        await test_suite.setup_suite()
                    else:
                        test_suite.setup_suite()
                    logger.info("套件設置完成")
                except Exception as e:
                    logger.error(f"套件設置失敗: {e}")
                    raise
            
            # 執行測試用例
            if test_suite.parallel_execution:
                test_results = await self._run_tests_parallel(test_suite.test_cases, test_suite.max_parallel_tests)
            else:
                test_results = await self._run_tests_sequential(test_suite.test_cases)
            
            # 執行套件清理
            if test_suite.teardown_suite:
                try:
                    if asyncio.iscoroutinefunction(test_suite.teardown_suite):
                        await test_suite.teardown_suite()
                    else:
                        test_suite.teardown_suite()
                    logger.info("套件清理完成")
                except Exception as e:
                    logger.error(f"套件清理失敗: {e}")
        
        finally:
            # 停止性能監控
            await self.performance_collector.stop_collection()
        
        suite_execution_time = time.time() - suite_start_time
        
        # 生成測試報告
        report = self._generate_test_report(
            session_id=self.current_session_id,
            suite_name=test_suite.name,
            test_results=test_results,
            total_execution_time=suite_execution_time
        )
        
        # 保存測試結果
        self.test_results[self.current_session_id] = test_results
        
        logger.info(f"測試套件執行完成: {test_suite.name}", extra={
            'session_id': self.current_session_id,
            'total_tests': report.total_tests,
            'passed_tests': report.passed_tests,
            'failed_tests': report.failed_tests,
            'success_rate': report.success_rate,
            'execution_time': suite_execution_time
        })
        
        return report
    
    async def _run_tests_sequential(self, test_cases: List[TestCase]) -> List[TestResult]:
        """順序執行測試用例"""
        results = []
        
        for test_case in test_cases:
            result = await self._run_single_test(test_case)
            results.append(result)
        
        return results
    
    async def _run_tests_parallel(self, test_cases: List[TestCase], max_parallel: int) -> List[TestResult]:
        """並行執行測試用例"""
        results = []
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def run_with_semaphore(test_case):
            async with semaphore:
                return await self._run_single_test(test_case)
        
        tasks = [run_with_semaphore(test_case) for test_case in test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = TestResult(
                    test_id=test_cases[i].test_id,
                    test_name=test_cases[i].name,
                    status=TestStatus.ERROR,
                    error_message=str(result),
                    error_traceback=traceback.format_exc()
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _run_single_test(self, test_case: TestCase) -> TestResult:
        """執行單個測試用例"""
        
        result = TestResult(
            test_id=test_case.test_id,
            test_name=test_case.name,
            expected_result=test_case.expected_result
        )
        
        assertion = TestAssertion(result)
        
        try:
            result.start_time = datetime.now()
            result.status = TestStatus.RUNNING
            
            # 執行測試設置
            if test_case.setup_function:
                if asyncio.iscoroutinefunction(test_case.setup_function):
                    await test_case.setup_function()
                else:
                    test_case.setup_function()
            
            # 執行測試函數
            if test_case.test_function:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(test_case.test_function):
                    result.actual_result = await asyncio.wait_for(
                        test_case.test_function(assertion, test_case.test_data),
                        timeout=test_case.timeout_seconds
                    )
                else:
                    result.actual_result = test_case.test_function(assertion, test_case.test_data)
                
                execution_time = time.time() - start_time
                result.performance_metrics['execution_time'] = execution_time
            
            # 檢查測試結果
            if result.assertions_failed > 0:
                result.status = TestStatus.FAILED
            else:
                result.status = TestStatus.PASSED
            
            # 執行測試清理
            if test_case.teardown_function:
                if asyncio.iscoroutinefunction(test_case.teardown_function):
                    await test_case.teardown_function()
                else:
                    test_case.teardown_function()
        
        except asyncio.TimeoutError:
            result.status = TestStatus.FAILED
            result.error_message = f"測試超時 ({test_case.timeout_seconds}s)"
        
        except Exception as e:
            result.status = TestStatus.ERROR
            result.error_message = str(e)
            result.error_traceback = traceback.format_exc()
        
        finally:
            result.end_time = datetime.now()
            if result.start_time:
                result.execution_time = (result.end_time - result.start_time).total_seconds()
        
        return result
    
    def _generate_test_report(self, 
                            session_id: str,
                            suite_name: str, 
                            test_results: List[TestResult], 
                            total_execution_time: float) -> TestReport:
        """生成測試報告"""
        
        # 統計測試結果
        total_tests = len(test_results)
        passed_tests = len([r for r in test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in test_results if r.status == TestStatus.FAILED])
        skipped_tests = len([r for r in test_results if r.status == TestStatus.SKIPPED])
        error_tests = len([r for r in test_results if r.status == TestStatus.ERROR])
        
        success_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        # 性能摘要
        execution_times = [r.execution_time for r in test_results if r.execution_time > 0]
        performance_summary = {}
        
        if execution_times:
            performance_summary = {
                'avg_execution_time': statistics.mean(execution_times),
                'min_execution_time': min(execution_times),
                'max_execution_time': max(execution_times),
                'total_execution_time': total_execution_time
            }
        
        # 生成建議
        recommendations = self._generate_recommendations(test_results, performance_summary)
        
        return TestReport(
            test_session_id=session_id,
            suite_name=suite_name,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            skipped_tests=skipped_tests,
            error_tests=error_tests,
            success_rate=success_rate,
            total_execution_time=total_execution_time,
            test_results=test_results,
            performance_summary=performance_summary,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, 
                                test_results: List[TestResult], 
                                performance_summary: Dict[str, Any]) -> List[str]:
        """生成測試建議"""
        recommendations = []
        
        # 失敗率分析
        failed_tests = [r for r in test_results if r.status in [TestStatus.FAILED, TestStatus.ERROR]]
        if len(failed_tests) > len(test_results) * 0.1:  # 失敗率超過10%
            recommendations.append("測試失敗率較高，建議檢查代碼品質和測試用例設計")
        
        # 性能分析
        if performance_summary and performance_summary.get('avg_execution_time', 0) > 10:
            recommendations.append("平均測試執行時間較長，建議優化測試用例或系統性能")
        
        # 斷言分析
        total_assertions = sum(r.assertions_passed + r.assertions_failed for r in test_results)
        if total_assertions < len(test_results) * 2:  # 平均每個測試少於2個斷言
            recommendations.append("測試覆蓋度可能不足，建議增加更多斷言和測試場景")
        
        # 錯誤模式分析
        error_messages = [r.error_message for r in failed_tests if r.error_message]
        common_errors = {}
        for error in error_messages:
            error_type = error.split(':')[0] if ':' in error else error
            common_errors[error_type] = common_errors.get(error_type, 0) + 1
        
        if common_errors:
            most_common_error = max(common_errors, key=common_errors.get)
            if common_errors[most_common_error] > 1:
                recommendations.append(f"常見錯誤模式: {most_common_error}，建議重點關注此類問題")
        
        return recommendations

class TianGongAgentTestSuite:
    """天工開物代理人測試套件"""
    
    @staticmethod
    def create_agent_functionality_tests() -> TestSuite:
        """創建代理人功能測試套件"""
        
        test_cases = []
        
        # 協調器測試
        test_cases.append(TestCase(
            name="天工協調器初始化測試",
            description="測試主協調器是否能正確初始化",
            test_type=TestType.UNIT,
            severity=TestSeverity.CRITICAL,
            test_function=TianGongAgentTestSuite._test_coordinator_initialization,
            timeout_seconds=10
        ))
        
        # 代理人註冊測試
        test_cases.append(TestCase(
            name="代理人註冊測試",
            description="測試代理人是否能正確註冊到協調器",
            test_type=TestType.INTEGRATION,
            severity=TestSeverity.HIGH,
            test_function=TianGongAgentTestSuite._test_agent_registration,
            timeout_seconds=15
        ))
        
        # 任務協調測試
        test_cases.append(TestCase(
            name="任務協調執行測試",
            description="測試任務是否能正確分配和執行",
            test_type=TestType.INTEGRATION,
            severity=TestSeverity.HIGH,
            test_function=TianGongAgentTestSuite._test_task_coordination,
            timeout_seconds=30
        ))
        
        # 工作總結測試
        test_cases.append(TestCase(
            name="工作總結生成測試",
            description="測試是否能正確生成工作總結報告",
            test_type=TestType.INTEGRATION,
            severity=TestSeverity.MEDIUM,
            test_function=TianGongAgentTestSuite._test_work_summary_generation,
            timeout_seconds=20
        ))
        
        return TestSuite(
            name="天工開物代理人功能測試套件",
            description="測試所有代理人的基本功能和協調機制",
            test_cases=test_cases,
            parallel_execution=False
        )
    
    @staticmethod
    async def _test_coordinator_initialization(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試協調器初始化"""
        from ..coordination.master_weaver import MasterWeaverCoordinator
        
        coordinator = MasterWeaverCoordinator()
        
        assertion.assert_is_not_none(coordinator, "協調器應該成功初始化")
        assertion.assert_is_not_none(coordinator.coordinator_id, "協調器應該有唯一ID")
        assertion.assert_equal(coordinator.name, "天工 (TianGong) - 主協調者", "協調器名稱應該正確")
        
        return {"coordinator_id": coordinator.coordinator_id}
    
    @staticmethod
    async def _test_agent_registration(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試代理人註冊"""
        coordinator, agents = await setup_coordination_system()
        
        assertion.assert_is_not_none(coordinator, "協調器應該成功初始化")
        assertion.assert_greater(len(agents), 0, "應該註冊至少一個代理人")
        assertion.assert_equal(len(agents), 6, "應該註冊6個專業代理人")
        
        # 檢查特定代理人
        expected_agents = [
            'code_architect_liang',
            'code_artisan_luban',
            'qa_guardian_direnjie',
            'doc_scribe_sima',
            'devops_engineer_mozi',
            'security_advisor_baozhen'
        ]
        
        for agent_name in expected_agents:
            assertion.assert_in(agent_name, agents, f"應該包含代理人: {agent_name}")
        
        return {"registered_agents": len(agents)}
    
    @staticmethod
    async def _test_task_coordination(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試任務協調"""
        from ..coordination.master_weaver import TaskCoordination, TaskPriority
        
        coordinator, agents = await setup_coordination_system()
        
        # 創建測試任務
        task = TaskCoordination(
            name="測試任務",
            description="用於測試的簡單任務",
            task_type="test_task",
            priority=TaskPriority.MEDIUM,
            estimated_hours=1
        )
        
        # 協調執行任務
        result = await coordinator.coordinate_task(task)
        
        assertion.assert_is_not_none(result, "任務協調應該返回結果")
        assertion.assert_true(hasattr(result, 'task_id'), "結果應該包含任務ID")
        
        return {"task_executed": True, "result": str(result)}
    
    @staticmethod
    async def _test_work_summary_generation(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試工作總結生成"""
        coordinator, agents = await setup_coordination_system()
        
        # 執行一個簡單任務以生成工作數據
        from ..coordination.master_weaver import TaskCoordination, TaskPriority
        
        task = TaskCoordination(
            name="總結測試任務",
            description="用於測試總結生成的任務",
            task_type="summary_test",
            priority=TaskPriority.LOW,
            estimated_hours=0.5
        )
        
        await coordinator.coordinate_task(task)
        
        # 生成工作總結
        summary = await coordinator.generate_work_summary()
        
        assertion.assert_is_not_none(summary, "應該生成工作總結")
        assertion.assert_is_not_none(summary.report_id, "總結應該有報告ID")
        assertion.assert_greater(len(summary.achievements), 0, "總結應該包含成就")
        
        return {"summary_generated": True, "report_id": summary.report_id}

class TianGongSystemTestSuite:
    """天工開物系統測試套件"""
    
    @staticmethod
    def create_system_integration_tests() -> TestSuite:
        """創建系統整合測試套件"""
        
        test_cases = []
        
        # 協調服務測試
        test_cases.append(TestCase(
            name="協調服務完整流程測試",
            description="測試天工開物協調服務的完整專案執行流程",
            test_type=TestType.SYSTEM,
            severity=TestSeverity.CRITICAL,
            test_function=TianGongSystemTestSuite._test_coordination_service_full_flow,
            timeout_seconds=60
        ))
        
        # 性能測試
        test_cases.append(TestCase(
            name="並行任務處理性能測試",
            description="測試系統處理多個並行任務的性能",
            test_type=TestType.PERFORMANCE,
            severity=TestSeverity.HIGH,
            test_function=TianGongSystemTestSuite._test_parallel_task_performance,
            timeout_seconds=45
        ))
        
        # 容錯測試
        test_cases.append(TestCase(
            name="系統容錯機制測試",
            description="測試系統在異常情況下的容錯能力",
            test_type=TestType.STRESS,
            severity=TestSeverity.HIGH,
            test_function=TianGongSystemTestSuite._test_fault_tolerance,
            timeout_seconds=30
        ))
        
        return TestSuite(
            name="天工開物系統整合測試套件",
            description="測試整個天工開物系統的整合功能和性能",
            test_cases=test_cases,
            parallel_execution=False
        )
    
    @staticmethod
    async def _test_coordination_service_full_flow(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試協調服務完整流程"""
        
        # 初始化服務
        service = await create_tiangong_service()
        
        assertion.assert_is_not_none(service, "協調服務應該成功初始化")
        
        # 創建測試專案
        project = create_project_context(
            name="系統測試專案",
            project_type=ProjectType.WEB_APPLICATION,
            requirements=["基本功能", "測試覆蓋", "文檔完整"]
        )
        
        assertion.assert_is_not_none(project, "專案上下文應該成功創建")
        
        # 執行專案協調
        result = await service.execute_project(project)
        
        assertion.assert_is_not_none(result, "專案執行應該返回結果")
        assertion.assert_true(result.overall_success, "專案應該執行成功")
        assertion.assert_greater(result.tasks_completed, 0, "應該完成至少一個任務")
        
        # 關閉服務
        await service.shutdown()
        
        return {
            "project_executed": True,
            "tasks_completed": result.tasks_completed,
            "execution_time": result.execution_time
        }
    
    @staticmethod
    async def _test_parallel_task_performance(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試並行任務性能"""
        
        service = await create_tiangong_service()
        
        # 創建多個並行專案
        projects = []
        for i in range(3):
            project = create_project_context(
                name=f"並行測試專案{i+1}",
                project_type=ProjectType.API_SERVICE,
                requirements=[f"需求{i+1}"]
            )
            projects.append(project)
        
        # 記錄開始時間
        start_time = time.time()
        
        # 並行執行專案
        tasks = [service.execute_project(project) for project in projects]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        execution_time = time.time() - start_time
        
        # 檢查結果
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assertion.assert_equal(len(successful_results), 3, "所有並行專案應該成功執行")
        assertion.assert_less(execution_time, 30, "並行執行時間應該在合理範圍內")
        
        await service.shutdown()
        
        return {
            "parallel_projects": len(projects),
            "successful_executions": len(successful_results),
            "total_execution_time": execution_time
        }
    
    @staticmethod
    async def _test_fault_tolerance(assertion: TestAssertion, test_data: Dict[str, Any]):
        """測試容錯機制"""
        
        service = await create_tiangong_service()
        
        # 創建一個可能失敗的專案
        project = create_project_context(
            name="容錯測試專案",
            project_type=ProjectType.TRADING_SYSTEM,
            requirements=["複雜需求", "高風險操作"]
        )
        
        try:
            # 執行專案（可能會有部分失敗）
            result = await service.execute_project(project)
            
            # 檢查系統是否優雅處理了問題
            assertion.assert_is_not_none(result, "即使有失敗，系統也應該返回結果")
            assertion.assert_greater_equal(result.tasks_completed + result.tasks_failed, 1, "應該嘗試執行任務")
            
            # 檢查系統狀態
            status = await service.get_service_status()
            assertion.assert_equal(status['status'], 'ready', "服務應該保持可用狀態")
            
        except Exception as e:
            # 如果有異常，檢查是否被正確處理
            assertion.assert_true(isinstance(e, (ValueError, RuntimeError)), f"應該是預期的異常類型: {type(e)}")
        
        await service.shutdown()
        
        return {"fault_tolerance_tested": True}

# 便利函數
async def run_agent_tests() -> TestReport:
    """運行代理人測試"""
    runner = TianGongTestRunner()
    test_suite = TianGongAgentTestSuite.create_agent_functionality_tests()
    runner.register_test_suite(test_suite)
    return await runner.run_test_suite(test_suite.suite_id)

async def run_system_tests() -> TestReport:
    """運行系統測試"""
    runner = TianGongTestRunner()
    test_suite = TianGongSystemTestSuite.create_system_integration_tests()
    runner.register_test_suite(test_suite)
    return await runner.run_test_suite(test_suite.suite_id)

async def run_all_tests() -> Dict[str, TestReport]:
    """運行所有測試"""
    results = {}
    
    # 運行代理人測試
    agent_report = await run_agent_tests()
    results['agent_tests'] = agent_report
    
    # 運行系統測試  
    system_report = await run_system_tests()
    results['system_tests'] = system_report
    
    return results

if __name__ == "__main__":
    # 測試腳本
    async def main():
        print("🧪 天工開物測試框架演示")
        print("=" * 50)
        
        try:
            # 運行所有測試
            test_results = await run_all_tests()
            
            print("\n📊 測試結果摘要:")
            print("-" * 30)
            
            for test_type, report in test_results.items():
                print(f"\n{test_type.upper()}:")
                print(f"  總測試數: {report.total_tests}")
                print(f"  通過: {report.passed_tests}")
                print(f"  失敗: {report.failed_tests}")
                print(f"  錯誤: {report.error_tests}")
                print(f"  成功率: {report.success_rate:.1%}")
                print(f"  執行時間: {report.total_execution_time:.2f}s")
                
                if report.recommendations:
                    print(f"  建議:")
                    for rec in report.recommendations:
                        print(f"    - {rec}")
            
            print("\n✅ 測試框架演示完成")
            
        except Exception as e:
            print(f"❌ 測試執行失敗: {e}")
            return 1
        
        return 0
    
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)