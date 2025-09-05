#!/usr/bin/env python3
"""
自动化基准测试框架
GPT-OSS 整合任务 1.2.2 - 自动化基准测试实现

提供对GPT-OSS、OpenAI、Anthropic等LLM提供商的自动化基准测试功能。
包含推理能力、创造力、准确性、速度等多维度评估。
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics

from ..database.model_capability_db import (
    ModelCapabilityDB, BenchmarkResult, BenchmarkType,
    ModelCapabilityCreate, ModelCapabilityUpdate
)
from ..utils.llm_client import LLMClient, LLMProvider, LLMRequest, AnalysisType

# 设置日志
logger = logging.getLogger(__name__)

class BenchmarkCategory(str, Enum):
    """基准测试分类"""
    REASONING = "reasoning"
    CREATIVITY = "creativity"
    ACCURACY = "accuracy"
    SPEED = "speed"
    LANGUAGE = "language"
    MATH = "math"
    CODE = "code"
    ANALYSIS = "analysis"
    SENTIMENT = "sentiment"
    SUMMARIZATION = "summarization"

class DifficultyLevel(str, Enum):
    """难度级别"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"

@dataclass
class BenchmarkTestCase:
    """基准测试用例"""
    id: str
    category: BenchmarkCategory
    difficulty: DifficultyLevel
    prompt: str
    expected_elements: List[str]  # 期望的回答要素
    evaluation_criteria: Dict[str, Any]  # 评估标准
    max_tokens: int = 2000
    timeout_seconds: int = 30
    weight: float = 1.0  # 测试用例权重
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class BenchmarkExecution:
    """基准测试执行记录"""
    test_case_id: str
    provider: str
    model_id: str
    response_content: str
    execution_time_ms: float
    tokens_used: int
    cost_estimate: float
    score: float
    passed: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class BenchmarkSuite:
    """基准测试套件"""
    name: str
    description: str
    test_cases: List[BenchmarkTestCase]
    suite_id: str
    version: str = "1.0"
    metadata: Optional[Dict[str, Any]] = None

class AutomatedBenchmarking:
    """自动化基准测试框架
    
    提供全面的LLM能力评估功能，包括：
    - 多维度基准测试
    - 自动化评分机制
    - 性能监控和分析
    - 结果持久化存储
    - 跨提供商对比分析
    """
    
    def __init__(
        self, 
        llm_client: Optional[LLMClient] = None,
        model_capability_db: Optional[ModelCapabilityDB] = None
    ):
        """初始化自动化基准测试框架
        
        Args:
            llm_client: LLM客户端，如果为None则自动创建
            model_capability_db: 模型能力数据库，如果为None则自动创建
        """
        self.llm_client = llm_client or LLMClient()
        self.model_capability_db = model_capability_db or ModelCapabilityDB()
        
        # 基准测试套件
        self.benchmark_suites: Dict[str, BenchmarkSuite] = {}
        
        # 执行统计
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0
        
        # 初始化标准测试套件
        self._initialize_standard_suites()
        
        logger.info("自动化基准测试框架初始化完成")
    
    def _initialize_standard_suites(self):
        """初始化标准基准测试套件"""
        # 推理能力测试套件
        reasoning_suite = self._create_reasoning_suite()
        self.benchmark_suites[reasoning_suite.suite_id] = reasoning_suite
        
        # 创造力测试套件
        creativity_suite = self._create_creativity_suite()
        self.benchmark_suites[creativity_suite.suite_id] = creativity_suite
        
        # 准确性测试套件
        accuracy_suite = self._create_accuracy_suite()
        self.benchmark_suites[accuracy_suite.suite_id] = accuracy_suite
        
        # 分析能力测试套件
        analysis_suite = self._create_analysis_suite()
        self.benchmark_suites[analysis_suite.suite_id] = analysis_suite
        
        logger.info(f"已初始化 {len(self.benchmark_suites)} 个标准测试套件")
    
    def _create_reasoning_suite(self) -> BenchmarkSuite:
        """创建推理能力测试套件"""
        test_cases = [
            BenchmarkTestCase(
                id="reasoning_01",
                category=BenchmarkCategory.REASONING,
                difficulty=DifficultyLevel.EASY,
                prompt="如果所有的玫瑰都是花，所有的花都需要水，那么玫瑰需要水吗？请解释推理过程。",
                expected_elements=["需要水", "逻辑推理", "三段论"],
                evaluation_criteria={
                    "logic_correctness": 0.4,
                    "explanation_clarity": 0.3,
                    "conclusion_accuracy": 0.3
                },
                weight=1.0
            ),
            BenchmarkTestCase(
                id="reasoning_02",
                category=BenchmarkCategory.REASONING,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="有三个开关控制三盏灯，你在另一个房间看不到灯。你可以操作开关任意次，但只能进入房间观察一次。如何确定哪个开关控制哪盏灯？",
                expected_elements=["触摸温度", "开关状态", "逻辑推理"],
                evaluation_criteria={
                    "solution_correctness": 0.5,
                    "reasoning_process": 0.3,
                    "clarity": 0.2
                },
                weight=1.5
            ),
            BenchmarkTestCase(
                id="reasoning_03",
                category=BenchmarkCategory.REASONING,
                difficulty=DifficultyLevel.HARD,
                prompt="在一个岛上有两种人：总是说真话的人和总是说假话的人。你遇到三个人A、B、C。A说'B和C是同一种人'，B说'A和C不是同一种人'。请判断每个人的身份。",
                expected_elements=["逻辑分析", "矛盾检验", "身份推断"],
                evaluation_criteria={
                    "logical_analysis": 0.4,
                    "contradiction_handling": 0.3,
                    "final_conclusion": 0.3
                },
                weight=2.0
            )
        ]
        
        return BenchmarkSuite(
            name="推理能力测试套件",
            description="评估模型的逻辑推理和问题解决能力",
            test_cases=test_cases,
            suite_id="reasoning_v1"
        )
    
    def _create_creativity_suite(self) -> BenchmarkSuite:
        """创建创造力测试套件"""
        test_cases = [
            BenchmarkTestCase(
                id="creativity_01",
                category=BenchmarkCategory.CREATIVITY,
                difficulty=DifficultyLevel.EASY,
                prompt="为一家专门销售云朵的商店想5个创意广告语。",
                expected_elements=["创意性", "相关性", "吸引力"],
                evaluation_criteria={
                    "originality": 0.4,
                    "relevance": 0.3,
                    "appeal": 0.3
                },
                weight=1.0
            ),
            BenchmarkTestCase(
                id="creativity_02",
                category=BenchmarkCategory.CREATIVITY,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="编写一个关于时间旅行的短故事，但主人公只能向过去旅行5分钟，限制在200字内。",
                expected_elements=["故事情节", "创意约束", "文学表达"],
                evaluation_criteria={
                    "plot_creativity": 0.4,
                    "constraint_handling": 0.3,
                    "narrative_quality": 0.3
                },
                weight=1.5
            ),
            BenchmarkTestCase(
                id="creativity_03",
                category=BenchmarkCategory.CREATIVITY,
                difficulty=DifficultyLevel.HARD,
                prompt="设计一个解决城市交通拥堵的创新方案，要求考虑技术可行性、成本效益和环境影响。",
                expected_elements=["创新方案", "可行性分析", "多维思考"],
                evaluation_criteria={
                    "innovation": 0.4,
                    "feasibility": 0.3,
                    "comprehensive_thinking": 0.3
                },
                weight=2.0
            )
        ]
        
        return BenchmarkSuite(
            name="创造力测试套件",
            description="评估模型的创新思维和创意表达能力",
            test_cases=test_cases,
            suite_id="creativity_v1"
        )
    
    def _create_accuracy_suite(self) -> BenchmarkSuite:
        """创建准确性测试套件"""
        test_cases = [
            BenchmarkTestCase(
                id="accuracy_01",
                category=BenchmarkCategory.ACCURACY,
                difficulty=DifficultyLevel.EASY,
                prompt="请计算：123 + 456 - 789 + 321 = ?",
                expected_elements=["111"],
                evaluation_criteria={
                    "calculation_accuracy": 0.8,
                    "process_clarity": 0.2
                },
                weight=0.5
            ),
            BenchmarkTestCase(
                id="accuracy_02",
                category=BenchmarkCategory.MATH,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="一个正方形的面积是64平方厘米，求其周长。请给出计算步骤。",
                expected_elements=["边长8", "周长32", "计算步骤"],
                evaluation_criteria={
                    "formula_correctness": 0.4,
                    "calculation_accuracy": 0.4,
                    "step_clarity": 0.2
                },
                weight=1.0
            ),
            BenchmarkTestCase(
                id="accuracy_03",
                category=BenchmarkCategory.ACCURACY,
                difficulty=DifficultyLevel.HARD,
                prompt="北京的GDP在2023年是多少？请提供准确的数据来源。",
                expected_elements=["具体数据", "数据来源", "时间准确性"],
                evaluation_criteria={
                    "data_accuracy": 0.5,
                    "source_credibility": 0.3,
                    "timeliness": 0.2
                },
                weight=1.5
            )
        ]
        
        return BenchmarkSuite(
            name="准确性测试套件",
            description="评估模型回答的准确性和事实性",
            test_cases=test_cases,
            suite_id="accuracy_v1"
        )
    
    def _create_analysis_suite(self) -> BenchmarkSuite:
        """创建分析能力测试套件"""
        test_cases = [
            BenchmarkTestCase(
                id="analysis_01",
                category=BenchmarkCategory.ANALYSIS,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="""分析以下股票数据：
                股票A：价格100元，P/E比率15，ROE 12%，债务比率30%
                股票B：价格50元，P/E比率25，ROE 8%，债务比率60%
                请从投资角度分析哪个更值得投资。""",
                expected_elements=["财务指标分析", "风险评估", "投资建议"],
                evaluation_criteria={
                    "financial_analysis": 0.4,
                    "risk_assessment": 0.3,
                    "investment_logic": 0.3
                },
                weight=2.0
            ),
            BenchmarkTestCase(
                id="analysis_02",
                category=BenchmarkCategory.SENTIMENT,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="分析这条评论的情感倾向：'这部电影的视觉效果令人惊叹，但剧情有些拖沓，整体来说还是值得一看的。'",
                expected_elements=["情感分析", "正负面因素", "整体评价"],
                evaluation_criteria={
                    "sentiment_accuracy": 0.4,
                    "aspect_identification": 0.3,
                    "overall_assessment": 0.3
                },
                weight=1.0
            ),
            BenchmarkTestCase(
                id="analysis_03",
                category=BenchmarkCategory.SUMMARIZATION,
                difficulty=DifficultyLevel.MEDIUM,
                prompt="""请总结以下文章的主要观点（限制在100字内）：
                
                人工智能技术在近年来取得了显著进展，特别是在自然语言处理领域。大型语言模型如GPT系列展现了强大的文本生成和理解能力。然而，这些技术也带来了新的挑战，包括数据隐私、算法偏见和就业影响等问题。专家建议在推进AI技术发展的同时，需要加强伦理规范和监管措施，确保技术发展能够造福人类社会。""",
                expected_elements=["AI进展", "挑战问题", "监管建议", "字数控制"],
                evaluation_criteria={
                    "content_coverage": 0.4,
                    "conciseness": 0.3,
                    "coherence": 0.3
                },
                weight=1.5
            )
        ]
        
        return BenchmarkSuite(
            name="分析能力测试套件",
            description="评估模型的分析、情感识别和总结能力",
            test_cases=test_cases,
            suite_id="analysis_v1"
        )
    
    # ==================== 基准测试执行 ====================
    
    async def run_benchmark_suite(
        self,
        suite_id: str,
        provider: str,
        model_id: str,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """执行指定的基准测试套件
        
        Args:
            suite_id: 测试套件ID
            provider: 提供商名称
            model_id: 模型ID
            max_concurrent: 最大并发数
            
        Returns:
            基准测试结果汇总
        """
        if suite_id not in self.benchmark_suites:
            raise ValueError(f"未找到测试套件: {suite_id}")
        
        suite = self.benchmark_suites[suite_id]
        logger.info(f"开始执行基准测试套件: {suite.name} ({provider}/{model_id})")
        
        start_time = time.time()
        semaphore = asyncio.Semaphore(max_concurrent)
        
        # 并发执行测试用例
        async def execute_test_case(test_case: BenchmarkTestCase) -> BenchmarkExecution:
            async with semaphore:
                return await self._execute_single_test_case(test_case, provider, model_id)
        
        tasks = [execute_test_case(test_case) for test_case in suite.test_cases]
        executions = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理执行结果
        successful_executions = []
        failed_executions = []
        
        for i, execution in enumerate(executions):
            if isinstance(execution, Exception):
                logger.error(f"测试用例执行失败: {suite.test_cases[i].id} - {execution}")
                failed_executions.append({
                    'test_case_id': suite.test_cases[i].id,
                    'error': str(execution)
                })
            else:
                if execution.passed:
                    successful_executions.append(execution)
                else:
                    failed_executions.append(execution)
        
        # 计算汇总结果
        total_execution_time = time.time() - start_time
        results = await self._compile_benchmark_results(
            suite, successful_executions + [e for e in failed_executions if isinstance(e, BenchmarkExecution)], 
            total_execution_time
        )
        
        # 更新模型能力数据库
        await self._update_model_capabilities(provider, model_id, results)
        
        # 更新统计信息
        self.total_executions += len(suite.test_cases)
        self.successful_executions += len(successful_executions)
        self.failed_executions += len(failed_executions)
        self.total_execution_time += total_execution_time
        
        logger.info(f"基准测试完成: {len(successful_executions)}/{len(suite.test_cases)} 成功")
        
        return results
    
    async def _execute_single_test_case(
        self,
        test_case: BenchmarkTestCase,
        provider: str,
        model_id: str
    ) -> BenchmarkExecution:
        """执行单个测试用例
        
        Args:
            test_case: 测试用例
            provider: 提供商名称
            model_id: 模型ID
            
        Returns:
            测试执行结果
        """
        start_time = time.time()
        
        try:
            # 创建LLM请求
            llm_request = LLMRequest(
                prompt=test_case.prompt,
                context={},
                analysis_type=self._map_category_to_analysis_type(test_case.category),
                max_tokens=test_case.max_tokens
            )
            
            # 执行请求
            response = await self.llm_client.analyze(
                prompt=test_case.prompt,
                analysis_type=self._map_category_to_analysis_type(test_case.category),
                max_tokens=test_case.max_tokens
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            if not response.success:
                return BenchmarkExecution(
                    test_case_id=test_case.id,
                    provider=provider,
                    model_id=model_id,
                    response_content="",
                    execution_time_ms=execution_time_ms,
                    tokens_used=0,
                    cost_estimate=0.0,
                    score=0.0,
                    passed=False,
                    error_message=response.error
                )
            
            # 评估回答质量
            score = await self._evaluate_response(test_case, response.content)
            
            return BenchmarkExecution(
                test_case_id=test_case.id,
                provider=provider,
                model_id=model_id,
                response_content=response.content,
                execution_time_ms=execution_time_ms,
                tokens_used=response.usage.get('total_tokens', 0) if response.usage else 0,
                cost_estimate=self._estimate_cost(response, provider),
                score=score,
                passed=score >= 0.6,  # 60%作为通过门槛
                metadata={
                    'test_category': test_case.category.value,
                    'difficulty': test_case.difficulty.value,
                    'weight': test_case.weight
                }
            )
            
        except asyncio.TimeoutError:
            execution_time_ms = test_case.timeout_seconds * 1000
            return BenchmarkExecution(
                test_case_id=test_case.id,
                provider=provider,
                model_id=model_id,
                response_content="",
                execution_time_ms=execution_time_ms,
                tokens_used=0,
                cost_estimate=0.0,
                score=0.0,
                passed=False,
                error_message="执行超时"
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return BenchmarkExecution(
                test_case_id=test_case.id,
                provider=provider,
                model_id=model_id,
                response_content="",
                execution_time_ms=execution_time_ms,
                tokens_used=0,
                cost_estimate=0.0,
                score=0.0,
                passed=False,
                error_message=str(e)
            )
    
    def _map_category_to_analysis_type(self, category: BenchmarkCategory) -> AnalysisType:
        """将测试分类映射到分析类型"""
        mapping = {
            BenchmarkCategory.REASONING: AnalysisType.TECHNICAL,
            BenchmarkCategory.CREATIVITY: AnalysisType.INVESTMENT,
            BenchmarkCategory.ACCURACY: AnalysisType.TECHNICAL,
            BenchmarkCategory.ANALYSIS: AnalysisType.FUNDAMENTAL,
            BenchmarkCategory.SENTIMENT: AnalysisType.SENTIMENT,
            BenchmarkCategory.SUMMARIZATION: AnalysisType.NEWS,
            BenchmarkCategory.MATH: AnalysisType.TECHNICAL,
            BenchmarkCategory.CODE: AnalysisType.TECHNICAL,
        }
        return mapping.get(category, AnalysisType.TECHNICAL)
    
    async def _evaluate_response(
        self, 
        test_case: BenchmarkTestCase, 
        response_content: str
    ) -> float:
        """评估回答质量
        
        Args:
            test_case: 测试用例
            response_content: 回答内容
            
        Returns:
            评分 (0.0-1.0)
        """
        if not response_content or not response_content.strip():
            return 0.0
        
        total_score = 0.0
        response_lower = response_content.lower()
        
        # 基于期望要素的评分
        if test_case.expected_elements:
            element_scores = []
            for element in test_case.expected_elements:
                if element.lower() in response_lower:
                    element_scores.append(1.0)
                else:
                    # 模糊匹配评分
                    similarity = self._calculate_similarity(element.lower(), response_lower)
                    element_scores.append(similarity)
            
            if element_scores:
                total_score = sum(element_scores) / len(element_scores)
        
        # 基于评估标准的额外评分
        if test_case.evaluation_criteria:
            criteria_score = await self._evaluate_by_criteria(
                test_case.evaluation_criteria, 
                response_content, 
                test_case.category
            )
            total_score = (total_score + criteria_score) / 2
        
        return min(max(total_score, 0.0), 1.0)
    
    def _calculate_similarity(self, expected: str, actual: str) -> float:
        """计算文本相似度（简化实现）"""
        expected_words = set(expected.split())
        actual_words = set(actual.split())
        
        if not expected_words:
            return 0.0
        
        intersection = expected_words & actual_words
        return len(intersection) / len(expected_words)
    
    async def _evaluate_by_criteria(
        self, 
        criteria: Dict[str, float], 
        response_content: str,
        category: BenchmarkCategory
    ) -> float:
        """基于评估标准进行评分"""
        # 简化的评分逻辑，实际实现可以更复杂
        base_score = 0.5  # 基础分
        
        # 长度合理性
        content_length = len(response_content)
        if category in [BenchmarkCategory.SUMMARIZATION]:
            # 摘要类任务希望简洁
            if 50 <= content_length <= 200:
                base_score += 0.2
        else:
            # 其他任务希望详细
            if content_length >= 100:
                base_score += 0.2
        
        # 结构化程度
        if any(marker in response_content for marker in ['1.', '2.', '-', '*', '：']):
            base_score += 0.1
        
        # 专业术语使用（根据类别）
        if category == BenchmarkCategory.ANALYSIS:
            financial_terms = ['分析', '评估', '风险', '收益', '投资']
            if any(term in response_content for term in financial_terms):
                base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _estimate_cost(self, response, provider: str) -> float:
        """估算请求成本"""
        if not response.usage:
            return 0.0
        
        tokens = response.usage.get('total_tokens', 0)
        
        # 简化的成本估算
        cost_per_1k = {
            'openai': 0.002,
            'anthropic': 0.008,
            'gpt_oss': 0.0  # 本地免费
        }
        
        base_cost = cost_per_1k.get(provider, 0.001)
        return (tokens / 1000) * base_cost
    
    async def _compile_benchmark_results(
        self,
        suite: BenchmarkSuite,
        executions: List[BenchmarkExecution],
        total_execution_time: float
    ) -> Dict[str, Any]:
        """编译基准测试结果"""
        if not executions:
            return {
                'suite_name': suite.name,
                'suite_id': suite.suite_id,
                'total_cases': len(suite.test_cases),
                'passed_cases': 0,
                'failed_cases': len(suite.test_cases),
                'overall_score': 0.0,
                'execution_time_seconds': total_execution_time,
                'category_scores': {},
                'error': '所有测试用例都执行失败'
            }
        
        # 统计基础指标
        passed_executions = [e for e in executions if e.passed]
        failed_executions = [e for e in executions if not e.passed]
        
        # 计算加权总分
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for execution in executions:
            test_case = next((tc for tc in suite.test_cases if tc.id == execution.test_case_id), None)
            if test_case:
                weight = test_case.weight
                total_weighted_score += execution.score * weight
                total_weight += weight
        
        overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # 按类别统计分数
        category_scores = {}
        category_groups = {}
        
        for execution in executions:
            test_case = next((tc for tc in suite.test_cases if tc.id == execution.test_case_id), None)
            if test_case:
                category = test_case.category.value
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(execution.score)
        
        for category, scores in category_groups.items():
            category_scores[category] = {
                'average_score': statistics.mean(scores),
                'test_count': len(scores),
                'pass_rate': len([s for s in scores if s >= 0.6]) / len(scores)
            }
        
        # 性能统计
        execution_times = [e.execution_time_ms for e in executions if e.execution_time_ms > 0]
        total_tokens = sum(e.tokens_used for e in executions)
        total_cost = sum(e.cost_estimate for e in executions)
        
        results = {
            'suite_name': suite.name,
            'suite_id': suite.suite_id,
            'suite_version': suite.version,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            
            # 基础统计
            'total_cases': len(suite.test_cases),
            'executed_cases': len(executions),
            'passed_cases': len(passed_executions),
            'failed_cases': len(failed_executions),
            'pass_rate': len(passed_executions) / len(executions) if executions else 0.0,
            
            # 得分统计
            'overall_score': round(overall_score, 3),
            'category_scores': category_scores,
            
            # 性能统计
            'execution_time_seconds': round(total_execution_time, 2),
            'average_case_time_ms': round(statistics.mean(execution_times), 2) if execution_times else 0.0,
            'total_tokens_used': total_tokens,
            'total_cost_estimate': round(total_cost, 6),
            'average_cost_per_case': round(total_cost / len(executions), 6) if executions else 0.0,
            
            # 详细执行记录
            'executions': [asdict(execution) for execution in executions],
            
            # 错误分析
            'error_analysis': self._analyze_errors(failed_executions)
        }
        
        return results
    
    def _analyze_errors(self, failed_executions: List[BenchmarkExecution]) -> Dict[str, Any]:
        """分析失败执行的错误模式"""
        if not failed_executions:
            return {}
        
        error_types = {}
        timeout_count = 0
        low_score_count = 0
        
        for execution in failed_executions:
            if execution.error_message:
                if "超时" in execution.error_message:
                    timeout_count += 1
                else:
                    error_type = execution.error_message[:50]  # 截取前50字符作为错误类型
                    error_types[error_type] = error_types.get(error_type, 0) + 1
            else:
                low_score_count += 1
        
        return {
            'total_failures': len(failed_executions),
            'timeout_failures': timeout_count,
            'low_score_failures': low_score_count,
            'error_types': error_types,
            'failure_rate_by_category': self._calculate_failure_rate_by_category(failed_executions)
        }
    
    def _calculate_failure_rate_by_category(self, failed_executions: List[BenchmarkExecution]) -> Dict[str, float]:
        """按类别计算失败率"""
        category_failures = {}
        
        for execution in failed_executions:
            if execution.metadata and 'test_category' in execution.metadata:
                category = execution.metadata['test_category']
                category_failures[category] = category_failures.get(category, 0) + 1
        
        return category_failures
    
    async def _update_model_capabilities(
        self, 
        provider: str, 
        model_id: str, 
        benchmark_results: Dict[str, Any]
    ):
        """更新模型能力数据库"""
        try:
            # 获取现有模型记录
            existing_model = await self.model_capability_db.get_model_by_provider_id(provider, model_id)
            
            # 计算新的能力评分
            overall_score = benchmark_results.get('overall_score', 0.0)
            category_scores = benchmark_results.get('category_scores', {})
            
            # 从分类得分中提取具体能力评分
            reasoning_score = category_scores.get('reasoning', {}).get('average_score')
            creativity_score = category_scores.get('creativity', {}).get('average_score')
            accuracy_score = category_scores.get('accuracy', {}).get('average_score') or \
                           category_scores.get('math', {}).get('average_score')
            
            # 计算速度评分（基于平均响应时间）
            avg_time_ms = benchmark_results.get('average_case_time_ms', 0.0)
            speed_score = max(0.0, min(1.0, 1.0 - (avg_time_ms - 1000) / 10000)) if avg_time_ms > 0 else 0.5
            
            # 准备基准测试数据
            benchmark_data = {
                'suite_results': benchmark_results,
                'last_benchmark_date': datetime.now(timezone.utc).isoformat(),
                'benchmark_version': benchmark_results.get('suite_version', '1.0')
            }
            
            if existing_model:
                # 更新现有模型
                update_data = ModelCapabilityUpdate(
                    capability_score=overall_score,
                    reasoning_score=reasoning_score,
                    creativity_score=creativity_score,
                    accuracy_score=accuracy_score,
                    speed_score=speed_score,
                    avg_latency_ms=avg_time_ms,
                    benchmark_scores=benchmark_data
                )
                
                await self.model_capability_db.update_model_capability(
                    existing_model.id, update_data
                )
                
                logger.info(f"已更新模型能力记录: {provider}/{model_id}")
            else:
                logger.warning(f"模型不存在，无法更新基准测试结果: {provider}/{model_id}")
        
        except Exception as e:
            logger.error(f"更新模型能力数据库失败: {e}")
    
    # ==================== 批量和对比测试 ====================
    
    async def run_comprehensive_benchmark(
        self, 
        providers_models: List[Tuple[str, str]],
        suite_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """运行全面的基准测试
        
        Args:
            providers_models: (提供商, 模型ID) 的列表
            suite_ids: 要运行的测试套件ID列表，如果为None则运行所有套件
            
        Returns:
            综合基准测试结果
        """
        if suite_ids is None:
            suite_ids = list(self.benchmark_suites.keys())
        
        logger.info(f"开始综合基准测试: {len(providers_models)} 个模型, {len(suite_ids)} 个套件")
        
        start_time = time.time()
        all_results = {}
        
        # 为每个模型运行所有测试套件
        for provider, model_id in providers_models:
            model_key = f"{provider}/{model_id}"
            all_results[model_key] = {}
            
            for suite_id in suite_ids:
                try:
                    suite_result = await self.run_benchmark_suite(
                        suite_id, provider, model_id, max_concurrent=2
                    )
                    all_results[model_key][suite_id] = suite_result
                except Exception as e:
                    logger.error(f"基准测试失败 {model_key} - {suite_id}: {e}")
                    all_results[model_key][suite_id] = {
                        'error': str(e),
                        'overall_score': 0.0
                    }
        
        # 编译对比分析结果
        total_time = time.time() - start_time
        comparison_results = self._compile_comparison_results(all_results, total_time)
        
        logger.info(f"综合基准测试完成，耗时 {total_time:.2f} 秒")
        return comparison_results
    
    def _compile_comparison_results(
        self, 
        all_results: Dict[str, Dict[str, Any]], 
        total_time: float
    ) -> Dict[str, Any]:
        """编译对比分析结果"""
        
        # 计算每个模型的总体得分
        model_scores = {}
        suite_comparisons = {}
        
        for model_key, suite_results in all_results.items():
            total_score = 0.0
            valid_suites = 0
            
            for suite_id, result in suite_results.items():
                if 'overall_score' in result and result['overall_score'] > 0:
                    total_score += result['overall_score']
                    valid_suites += 1
                    
                    # 按套件统计
                    if suite_id not in suite_comparisons:
                        suite_comparisons[suite_id] = {}
                    suite_comparisons[suite_id][model_key] = result['overall_score']
            
            if valid_suites > 0:
                model_scores[model_key] = total_score / valid_suites
            else:
                model_scores[model_key] = 0.0
        
        # 排名
        model_rankings = sorted(
            model_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        # 分析最佳表现
        best_performers = {}
        for suite_id, scores in suite_comparisons.items():
            if scores:
                best_model = max(scores.items(), key=lambda x: x[1])
                best_performers[suite_id] = {
                    'model': best_model[0],
                    'score': best_model[1],
                    'lead_margin': best_model[1] - sorted(scores.values())[-2] if len(scores) > 1 else 0.0
                }
        
        return {
            'summary': {
                'total_models_tested': len(all_results),
                'total_suites_run': len(suite_comparisons),
                'total_execution_time_seconds': round(total_time, 2),
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            'model_rankings': model_rankings,
            'model_scores': model_scores,
            'suite_comparisons': suite_comparisons,
            'best_performers_by_suite': best_performers,
            'detailed_results': all_results,
            'insights': self._generate_benchmark_insights(model_scores, suite_comparisons)
        }
    
    def _generate_benchmark_insights(
        self, 
        model_scores: Dict[str, float], 
        suite_comparisons: Dict[str, Dict[str, float]]
    ) -> List[str]:
        """生成基准测试洞察"""
        insights = []
        
        if not model_scores:
            return ["无有效的基准测试结果"]
        
        # 最佳和最差模型
        best_model = max(model_scores.items(), key=lambda x: x[1])
        worst_model = min(model_scores.items(), key=lambda x: x[1])
        
        insights.append(f"最佳整体表现: {best_model[0]} (得分: {best_model[1]:.3f})")
        insights.append(f"最低整体表现: {worst_model[0]} (得分: {worst_model[1]:.3f})")
        
        # 得分分布
        scores = list(model_scores.values())
        avg_score = statistics.mean(scores)
        insights.append(f"平均得分: {avg_score:.3f}")
        
        # 特定领域强者
        for suite_id, scores in suite_comparisons.items():
            if scores:
                best_in_suite = max(scores.items(), key=lambda x: x[1])
                suite_name = self.benchmark_suites.get(suite_id, {}).name or suite_id
                insights.append(f"{suite_name}最佳: {best_in_suite[0]} (得分: {best_in_suite[1]:.3f})")
        
        return insights
    
    # ==================== 工具方法 ====================
    
    def get_benchmark_stats(self) -> Dict[str, Any]:
        """获取基准测试统计信息"""
        return {
            'available_suites': list(self.benchmark_suites.keys()),
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': (
                self.successful_executions / max(self.total_executions, 1)
            ) * 100,
            'total_execution_time_seconds': round(self.total_execution_time, 2),
            'average_execution_time': (
                self.total_execution_time / max(self.total_executions, 1)
            ) if self.total_executions > 0 else 0.0
        }
    
    def get_suite_info(self, suite_id: str) -> Optional[Dict[str, Any]]:
        """获取测试套件信息"""
        if suite_id not in self.benchmark_suites:
            return None
        
        suite = self.benchmark_suites[suite_id]
        
        return {
            'suite_id': suite.suite_id,
            'name': suite.name,
            'description': suite.description,
            'version': suite.version,
            'test_cases_count': len(suite.test_cases),
            'categories': list(set(tc.category.value for tc in suite.test_cases)),
            'difficulty_levels': list(set(tc.difficulty.value for tc in suite.test_cases)),
            'estimated_time_minutes': sum(tc.timeout_seconds for tc in suite.test_cases) / 60,
            'metadata': suite.metadata
        }
    
    async def close(self):
        """关闭基准测试框架，清理资源"""
        if self.llm_client:
            await self.llm_client.close()
        
        if self.model_capability_db:
            self.model_capability_db.close()
        
        logger.info("自动化基准测试框架已关闭")

# ==================== 工具函数 ====================

def create_automated_benchmarking(
    llm_client: Optional[LLMClient] = None,
    model_capability_db: Optional[ModelCapabilityDB] = None
) -> AutomatedBenchmarking:
    """创建自动化基准测试框架的便利函数"""
    return AutomatedBenchmarking(llm_client, model_capability_db)