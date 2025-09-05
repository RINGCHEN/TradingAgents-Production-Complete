#!/usr/bin/env python3
"""
Benchmarking Framework Core
基準測試框架核心 - GPT-OSS整合任務1.2.2
"""

import time
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)

class BenchmarkStatus(Enum):
    """基準測試狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class BenchmarkError(Exception):
    """基準測試錯誤"""
    pass

@dataclass
class BenchmarkResult:
    """基準測試結果"""
    task_name: str
    provider: str
    model_id: str
    score: float = 0.0
    latency_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    raw_response: Optional[str] = None
    expected_output: Optional[str] = None
    
    def __post_init__(self):
        """初始化後處理"""
        if self.start_time is None:
            self.start_time = datetime.now(timezone.utc)
    
    @property
    def duration_ms(self) -> float:
        """獲取執行時長（毫秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return self.latency_ms
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'task_name': self.task_name,
            'provider': self.provider,
            'model_id': self.model_id,
            'score': self.score,
            'latency_ms': self.latency_ms,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_ms': self.duration_ms,
            'raw_response': self.raw_response,
            'expected_output': self.expected_output
        }

class BenchmarkTask(ABC):
    """基準測試任務抽象基類"""
    
    def __init__(
        self,
        name: str,
        description: str,
        weight: float = 1.0,
        timeout_seconds: int = 30,
        max_retries: int = 1
    ):
        """
        初始化基準測試任務
        
        Args:
            name: 任務名稱
            description: 任務描述
            weight: 任務權重
            timeout_seconds: 超時時間（秒）
            max_retries: 最大重試次數
        """
        self.name = name
        self.description = description
        self.weight = weight
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.logger = logger.getChild(self.__class__.__name__)
    
    @abstractmethod
    async def run(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> BenchmarkResult:
        """
        執行基準測試任務
        
        Args:
            llm_client: LLM客戶端
            provider: 提供商名稱
            model_id: 模型標識符
            
        Returns:
            基準測試結果
        """
        pass
    
    async def execute_with_timeout(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> BenchmarkResult:
        """
        帶超時執行基準測試
        
        Args:
            llm_client: LLM客戶端
            provider: 提供商名稱
            model_id: 模型標識符
            
        Returns:
            基準測試結果
        """
        result = BenchmarkResult(
            task_name=self.name,
            provider=provider,
            model_id=model_id,
            start_time=datetime.now(timezone.utc)
        )
        
        for attempt in range(self.max_retries + 1):
            try:
                # 使用asyncio.timeout執行任務
                async with asyncio.timeout(self.timeout_seconds):
                    result = await self.run(llm_client, provider, model_id)
                    result.end_time = datetime.now(timezone.utc)
                    result.success = True
                    return result
                    
            except asyncio.TimeoutError:
                error_msg = f"Task '{self.name}' timed out after {self.timeout_seconds} seconds"
                self.logger.warning(f"{error_msg} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if attempt >= self.max_retries:
                    result.success = False
                    result.error_message = error_msg
                    result.end_time = datetime.now(timezone.utc)
                    return result
                
                # 重試前等待
                await asyncio.sleep(1)
                
            except Exception as e:
                error_msg = f"Task '{self.name}' failed: {str(e)}"
                self.logger.error(f"{error_msg} (attempt {attempt + 1}/{self.max_retries + 1})")
                
                if attempt >= self.max_retries:
                    result.success = False
                    result.error_message = error_msg
                    result.end_time = datetime.now(timezone.utc)
                    return result
                
                # 重試前等待
                await asyncio.sleep(1)
        
        # 理論上不會到達這裡
        result.success = False
        result.error_message = "Unknown error"
        result.end_time = datetime.now(timezone.utc)
        return result
    
    def validate_response(
        self,
        response: str,
        expected: Optional[str] = None
    ) -> float:
        """
        驗證回應品質
        
        Args:
            response: 實際回應
            expected: 期望回應
            
        Returns:
            品質評分 (0.0-1.0)
        """
        if not response or not response.strip():
            return 0.0
        
        # 基本長度檢查
        if len(response.strip()) < 10:
            return 0.3
        
        # 如果有期望輸出，計算相似度
        if expected:
            return self._calculate_similarity(response, expected)
        
        # 否則基於回應品質給分
        return self._assess_response_quality(response)
    
    def _calculate_similarity(self, response: str, expected: str) -> float:
        """計算相似度（簡單實現）"""
        response_words = set(response.lower().split())
        expected_words = set(expected.lower().split())
        
        if not expected_words:
            return 1.0 if not response_words else 0.5
        
        intersection = response_words & expected_words
        union = response_words | expected_words
        
        # Jaccard 相似度
        jaccard = len(intersection) / len(union) if union else 0.0
        
        # 長度相似度
        length_ratio = min(len(response), len(expected)) / max(len(response), len(expected))
        
        # 組合評分
        return (jaccard * 0.7 + length_ratio * 0.3)
    
    def _assess_response_quality(self, response: str) -> float:
        """評估回應品質"""
        score = 0.5  # 基礎分
        
        # 長度檢查
        if len(response) > 50:
            score += 0.1
        if len(response) > 100:
            score += 0.1
        
        # 結構檢查
        if any(char in response for char in ['.', '。', '\n']):
            score += 0.1
        
        # JSON格式檢查
        if response.strip().startswith('{') and response.strip().endswith('}'):
            score += 0.2
        
        return min(1.0, score)

class BenchmarkSuite:
    """基準測試套件"""
    
    def __init__(
        self,
        name: str,
        description: str,
        tasks: List[BenchmarkTask] = None
    ):
        """
        初始化基準測試套件
        
        Args:
            name: 套件名稱
            description: 套件描述  
            tasks: 測試任務列表
        """
        self.name = name
        self.description = description
        self.tasks = tasks or []
        self.logger = logger.getChild(self.__class__.__name__)
    
    def add_task(self, task: BenchmarkTask):
        """添加測試任務"""
        self.tasks.append(task)
    
    def remove_task(self, task_name: str):
        """移除測試任務"""
        self.tasks = [task for task in self.tasks if task.name != task_name]
    
    async def run_all(
        self,
        llm_client,
        provider: str,
        model_id: str,
        parallel: bool = False,
        max_concurrent: int = 3
    ) -> List[BenchmarkResult]:
        """
        執行所有測試任務
        
        Args:
            llm_client: LLM客戶端
            provider: 提供商名稱
            model_id: 模型標識符
            parallel: 是否並行執行
            max_concurrent: 最大並發數
            
        Returns:
            所有測試結果列表
        """
        if not self.tasks:
            self.logger.warning("No benchmark tasks to run")
            return []
        
        self.logger.info(f"Running benchmark suite '{self.name}' with {len(self.tasks)} tasks")
        
        if parallel:
            return await self._run_parallel(llm_client, provider, model_id, max_concurrent)
        else:
            return await self._run_sequential(llm_client, provider, model_id)
    
    async def _run_sequential(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> List[BenchmarkResult]:
        """順序執行測試任務"""
        results = []
        
        for i, task in enumerate(self.tasks, 1):
            self.logger.info(f"Running task {i}/{len(self.tasks)}: {task.name}")
            
            try:
                result = await task.execute_with_timeout(llm_client, provider, model_id)
                results.append(result)
                
                if result.success:
                    self.logger.info(f"✅ Task '{task.name}' completed (score: {result.score:.3f})")
                else:
                    self.logger.warning(f"❌ Task '{task.name}' failed: {result.error_message}")
                    
            except Exception as e:
                self.logger.error(f"❌ Unexpected error in task '{task.name}': {e}")
                result = BenchmarkResult(
                    task_name=task.name,
                    provider=provider,
                    model_id=model_id,
                    success=False,
                    error_message=str(e),
                    end_time=datetime.now(timezone.utc)
                )
                results.append(result)
        
        return results
    
    async def _run_parallel(
        self,
        llm_client,
        provider: str,
        model_id: str,
        max_concurrent: int
    ) -> List[BenchmarkResult]:
        """並行執行測試任務"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_task_with_semaphore(task: BenchmarkTask) -> BenchmarkResult:
            async with semaphore:
                return await task.execute_with_timeout(llm_client, provider, model_id)
        
        # 創建所有任務
        task_coroutines = [run_task_with_semaphore(task) for task in self.tasks]
        
        # 並行執行
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # 處理異常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = BenchmarkResult(
                    task_name=self.tasks[i].name,
                    provider=provider,
                    model_id=model_id,
                    success=False,
                    error_message=str(result),
                    end_time=datetime.now(timezone.utc)
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def calculate_overall_score(self, results: List[BenchmarkResult]) -> float:
        """計算總體評分"""
        if not results:
            return 0.0
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for result in results:
            if result.success:
                task = next((t for t in self.tasks if t.name == result.task_name), None)
                if task:
                    weight = task.weight
                    total_weighted_score += result.score * weight
                    total_weight += weight
        
        return total_weighted_score / max(total_weight, 1.0)

class BenchmarkFramework:
    """基準測試框架主類"""
    
    def __init__(self):
        """初始化基準測試框架"""
        self.suites: Dict[str, BenchmarkSuite] = {}
        self.results_history: List[Dict[str, Any]] = []
        self.logger = logger
    
    def register_suite(self, suite: BenchmarkSuite):
        """註冊測試套件"""
        self.suites[suite.name] = suite
        self.logger.info(f"Registered benchmark suite: {suite.name}")
    
    def unregister_suite(self, suite_name: str):
        """取消註冊測試套件"""
        if suite_name in self.suites:
            del self.suites[suite_name]
            self.logger.info(f"Unregistered benchmark suite: {suite_name}")
    
    async def run_suite(
        self,
        suite_name: str,
        llm_client,
        provider: str,
        model_id: str,
        parallel: bool = False,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        執行指定測試套件
        
        Args:
            suite_name: 測試套件名稱
            llm_client: LLM客戶端
            provider: 提供商名稱
            model_id: 模型標識符
            parallel: 是否並行執行
            max_concurrent: 最大並發數
            
        Returns:
            測試結果詳情
        """
        if suite_name not in self.suites:
            raise BenchmarkError(f"Benchmark suite '{suite_name}' not found")
        
        suite = self.suites[suite_name]
        start_time = datetime.now(timezone.utc)
        
        self.logger.info(f"Starting benchmark suite '{suite_name}' for {provider}/{model_id}")
        
        try:
            # 執行測試套件
            results = await suite.run_all(
                llm_client=llm_client,
                provider=provider,
                model_id=model_id,
                parallel=parallel,
                max_concurrent=max_concurrent
            )
            
            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            # 計算綜合評分
            overall_score = suite.calculate_overall_score(results)
            
            # 統計成功率
            success_count = sum(1 for r in results if r.success)
            success_rate = success_count / len(results) if results else 0.0
            
            # 計算平均延迟
            latencies = [r.latency_ms for r in results if r.success and r.latency_ms > 0]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            
            # 構建結果
            suite_result = {
                'suite_name': suite_name,
                'provider': provider,
                'model_id': model_id,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat(),
                'duration_ms': duration_ms,
                'overall_score': overall_score,
                'success_rate': success_rate,
                'avg_latency_ms': avg_latency,
                'total_tasks': len(results),
                'successful_tasks': success_count,
                'failed_tasks': len(results) - success_count,
                'task_results': [r.to_dict() for r in results],
                'detailed_scores': {
                    'reasoning_score': self._extract_category_score(results, 'reasoning'),
                    'creativity_score': self._extract_category_score(results, 'creativity'),
                    'accuracy_score': self._extract_category_score(results, 'accuracy'),
                    'speed_score': self._calculate_speed_score(avg_latency)
                }
            }
            
            # 保存到歷史記錄
            self.results_history.append(suite_result)
            
            self.logger.info(
                f"✅ Benchmark suite '{suite_name}' completed: "
                f"score={overall_score:.3f}, success_rate={success_rate:.1%}"
            )
            
            return suite_result
            
        except Exception as e:
            self.logger.error(f"❌ Benchmark suite '{suite_name}' failed: {e}")
            raise BenchmarkError(f"Benchmark suite execution failed: {e}")
    
    def _extract_category_score(self, results: List[BenchmarkResult], category: str) -> Optional[float]:
        """提取特定類別的評分"""
        category_results = [
            r for r in results 
            if r.success and category.lower() in r.task_name.lower()
        ]
        
        if not category_results:
            return None
        
        return sum(r.score for r in category_results) / len(category_results)
    
    def _calculate_speed_score(self, avg_latency_ms: float) -> float:
        """計算速度評分"""
        if avg_latency_ms <= 0:
            return 1.0
        
        # 基於延遲計算速度評分（越快評分越高）
        # 假設1000ms為標準延遲
        standard_latency = 1000.0
        speed_score = standard_latency / max(avg_latency_ms, 100.0)
        
        return min(1.0, speed_score)
    
    async def run_all_suites(
        self,
        llm_client,
        provider: str,
        model_id: str,
        parallel: bool = False,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """執行所有測試套件"""
        if not self.suites:
            raise BenchmarkError("No benchmark suites registered")
        
        all_results = {}
        overall_start_time = datetime.now(timezone.utc)
        
        for suite_name in self.suites:
            try:
                result = await self.run_suite(
                    suite_name=suite_name,
                    llm_client=llm_client,
                    provider=provider,
                    model_id=model_id,
                    parallel=parallel,
                    max_concurrent=max_concurrent
                )
                all_results[suite_name] = result
                
            except Exception as e:
                self.logger.error(f"Failed to run suite '{suite_name}': {e}")
                all_results[suite_name] = {
                    'error': str(e),
                    'success': False
                }
        
        overall_end_time = datetime.now(timezone.utc)
        overall_duration = (overall_end_time - overall_start_time).total_seconds() * 1000
        
        # 計算總體統計
        successful_suites = [r for r in all_results.values() if 'error' not in r]
        if successful_suites:
            overall_score = sum(r['overall_score'] for r in successful_suites) / len(successful_suites)
            overall_success_rate = sum(r['success_rate'] for r in successful_suites) / len(successful_suites)
            overall_avg_latency = sum(r['avg_latency_ms'] for r in successful_suites) / len(successful_suites)
        else:
            overall_score = 0.0
            overall_success_rate = 0.0
            overall_avg_latency = 0.0
        
        return {
            'provider': provider,
            'model_id': model_id,
            'start_time': overall_start_time.isoformat(),
            'end_time': overall_end_time.isoformat(),
            'duration_ms': overall_duration,
            'overall_score': overall_score,
            'overall_success_rate': overall_success_rate,
            'overall_avg_latency_ms': overall_avg_latency,
            'suites_run': len(self.suites),
            'suites_successful': len(successful_suites),
            'suite_results': all_results
        }
    
    def get_history(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        suite_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """獲取測試歷史"""
        filtered_results = self.results_history
        
        # 應用過濾條件
        if provider:
            filtered_results = [r for r in filtered_results if r.get('provider') == provider]
        if model_id:
            filtered_results = [r for r in filtered_results if r.get('model_id') == model_id]
        if suite_name:
            filtered_results = [r for r in filtered_results if r.get('suite_name') == suite_name]
        
        # 按時間倒序排列並限制數量
        filtered_results.sort(key=lambda x: x.get('start_time', ''), reverse=True)
        return filtered_results[:limit]
    
    def clear_history(self):
        """清空測試歷史"""
        self.results_history.clear()
        self.logger.info("Benchmark history cleared")