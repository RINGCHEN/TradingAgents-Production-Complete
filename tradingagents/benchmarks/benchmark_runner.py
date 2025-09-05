#!/usr/bin/env python3
"""
Benchmark Runner
基準測試執行器 - GPT-OSS整合任務1.2.2
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .benchmark_framework import BenchmarkFramework, BenchmarkError
from .benchmark_tasks import StandardBenchmarkSuite
from ..database.model_capability_db import ModelCapabilityDB, ModelCapabilityDBError
from ..utils.llm_client import LLMClient

logger = logging.getLogger(__name__)

class BenchmarkRunner:
    """
    基準測試執行器
    
    功能：
    1. 統一管理基準測試執行
    2. 與模型能力數據庫集成
    3. 支持批量測試和調度
    4. 提供測試結果分析
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        model_db: Optional[ModelCapabilityDB] = None
    ):
        """
        初始化基準測試執行器
        
        Args:
            llm_client: LLM客戶端實例
            model_db: 模型能力數據庫實例
        """
        self.llm_client = llm_client
        self.model_db = model_db or ModelCapabilityDB()
        self.framework = BenchmarkFramework()
        self.logger = logger
        
        # 註冊標準測試套件
        self._register_standard_suites()
    
    def _register_standard_suites(self):
        """註冊標準測試套件"""
        try:
            standard_suite = StandardBenchmarkSuite()
            self.framework.register_suite(standard_suite)
            self.logger.info("✅ Standard benchmark suite registered")
        except Exception as e:
            self.logger.error(f"❌ Failed to register standard suite: {e}")
    
    async def run_model_benchmark(
        self,
        provider: str,
        model_id: str,
        suite_name: str = "standard",
        llm_client: Optional[LLMClient] = None,
        update_database: bool = True,
        parallel: bool = False,
        max_concurrent: int = 3
    ) -> Dict[str, Any]:
        """
        執行單個模型的基準測試
        
        Args:
            provider: 提供商名稱
            model_id: 模型標識符
            suite_name: 測試套件名稱
            llm_client: LLM客戶端（可選，使用實例變量）
            update_database: 是否更新數據庫
            parallel: 是否並行執行
            max_concurrent: 最大並發數
            
        Returns:
            基準測試結果
            
        Raises:
            BenchmarkError: 測試執行失敗
        """
        client = llm_client or self.llm_client
        if not client:
            raise BenchmarkError("No LLM client available for benchmarking")
        
        self.logger.info(f"🚀 Starting benchmark for {provider}/{model_id} with suite '{suite_name}'")
        
        try:
            # 執行基準測試
            result = await self.framework.run_suite(
                suite_name=suite_name,
                llm_client=client,
                provider=provider,
                model_id=model_id,
                parallel=parallel,
                max_concurrent=max_concurrent
            )
            
            # 處理測試結果
            processed_result = self._process_benchmark_result(result)
            
            # 更新數據庫
            if update_database:
                await self._update_model_database(provider, model_id, processed_result)
            
            self.logger.info(
                f"✅ Benchmark completed for {provider}/{model_id}: "
                f"score={processed_result['overall_score']:.3f}"
            )
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"❌ Benchmark failed for {provider}/{model_id}: {e}")
            raise BenchmarkError(f"Benchmark execution failed: {e}")
    
    async def run_batch_benchmarks(
        self,
        models: List[Tuple[str, str]],
        suite_name: str = "standard",
        llm_client: Optional[LLMClient] = None,
        update_database: bool = True,
        parallel_models: bool = False,
        parallel_tasks: bool = False,
        max_concurrent_models: int = 2,
        max_concurrent_tasks: int = 3
    ) -> Dict[str, Dict[str, Any]]:
        """
        批量執行多個模型的基準測試
        
        Args:
            models: 模型列表 [(provider, model_id), ...]
            suite_name: 測試套件名稱
            llm_client: LLM客戶端
            update_database: 是否更新數據庫
            parallel_models: 是否並行測試多個模型
            parallel_tasks: 是否並行執行測試任務
            max_concurrent_models: 最大並發模型數
            max_concurrent_tasks: 最大並發任務數
            
        Returns:
            所有模型的測試結果字典
        """
        if not models:
            self.logger.warning("No models specified for batch benchmarking")
            return {}
        
        self.logger.info(f"🚀 Starting batch benchmark for {len(models)} models")
        
        client = llm_client or self.llm_client
        if not client:
            raise BenchmarkError("No LLM client available for benchmarking")
        
        results = {}
        
        if parallel_models:
            # 並行測試多個模型
            semaphore = asyncio.Semaphore(max_concurrent_models)
            
            async def run_single_model(provider: str, model_id: str) -> Tuple[str, Dict[str, Any]]:
                async with semaphore:
                    try:
                        result = await self.run_model_benchmark(
                            provider=provider,
                            model_id=model_id,
                            suite_name=suite_name,
                            llm_client=client,
                            update_database=update_database,
                            parallel=parallel_tasks,
                            max_concurrent=max_concurrent_tasks
                        )
                        return f"{provider}/{model_id}", result
                    except Exception as e:
                        self.logger.error(f"❌ Failed to benchmark {provider}/{model_id}: {e}")
                        return f"{provider}/{model_id}", {"error": str(e), "success": False}
            
            # 執行所有模型測試
            tasks = [run_single_model(provider, model_id) for provider, model_id in models]
            completed_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理結果
            for result in completed_results:
                if isinstance(result, tuple):
                    model_key, model_result = result
                    results[model_key] = model_result
                else:
                    self.logger.error(f"❌ Unexpected result type: {result}")
        
        else:
            # 順序測試模型
            for provider, model_id in models:
                model_key = f"{provider}/{model_id}"
                
                try:
                    result = await self.run_model_benchmark(
                        provider=provider,
                        model_id=model_id,
                        suite_name=suite_name,
                        llm_client=client,
                        update_database=update_database,
                        parallel=parallel_tasks,
                        max_concurrent=max_concurrent_tasks
                    )
                    results[model_key] = result
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to benchmark {provider}/{model_id}: {e}")
                    results[model_key] = {"error": str(e), "success": False}
        
        # 生成批量測試總結
        summary = self._generate_batch_summary(results)
        
        self.logger.info(
            f"✅ Batch benchmark completed: "
            f"{summary['successful_models']}/{summary['total_models']} models successful"
        )
        
        return {
            "summary": summary,
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def run_all_registered_models(
        self,
        suite_name: str = "standard",
        llm_client: Optional[LLMClient] = None,
        update_database: bool = True,
        parallel_models: bool = False,
        parallel_tasks: bool = False,
        provider_filter: Optional[str] = None,
        privacy_level_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        對所有已註冊的模型執行基準測試
        
        Args:
            suite_name: 測試套件名稱
            llm_client: LLM客戶端
            update_database: 是否更新數據庫
            parallel_models: 是否並行測試模型
            parallel_tasks: 是否並行執行任務
            provider_filter: 提供商過濾
            privacy_level_filter: 隱私級別過濾
            
        Returns:
            所有模型的測試結果
        """
        try:
            # 獲取所有可用模型
            models = await self.model_db.list_model_capabilities(
                provider=provider_filter,
                privacy_level=privacy_level_filter,
                is_available=True
            )
            
            if not models:
                self.logger.warning("No registered models found for benchmarking")
                return {"error": "No models available", "results": {}}
            
            self.logger.info(f"Found {len(models)} registered models for benchmarking")
            
            # 轉換為批量測試格式
            model_list = [(model.provider, model.model_id) for model in models]
            
            # 執行批量測試
            return await self.run_batch_benchmarks(
                models=model_list,
                suite_name=suite_name,
                llm_client=llm_client,
                update_database=update_database,
                parallel_models=parallel_models,
                parallel_tasks=parallel_tasks
            )
            
        except ModelCapabilityDBError as e:
            self.logger.error(f"❌ Database error during model benchmarking: {e}")
            raise BenchmarkError(f"Database error: {e}")
        except Exception as e:
            self.logger.error(f"❌ Error during registered model benchmarking: {e}")
            raise BenchmarkError(f"Benchmarking error: {e}")
    
    def _process_benchmark_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """處理基準測試結果，提取關鍵指標"""
        processed = {
            "overall_score": result.get("overall_score", 0.0),
            "success_rate": result.get("success_rate", 0.0),
            "avg_latency_ms": result.get("avg_latency_ms", 0.0),
            "detailed_scores": result.get("detailed_scores", {}),
            "task_results": result.get("task_results", []),
            "timestamp": result.get("start_time"),
            "duration_ms": result.get("duration_ms", 0.0),
            "suite_name": result.get("suite_name"),
            "provider": result.get("provider"),
            "model_id": result.get("model_id")
        }
        
        # 確保詳細評分存在
        if not processed["detailed_scores"]:
            processed["detailed_scores"] = {
                "reasoning_score": None,
                "creativity_score": None,
                "accuracy_score": None,
                "speed_score": None
            }
        
        return processed
    
    async def _update_model_database(
        self,
        provider: str,
        model_id: str,
        benchmark_result: Dict[str, Any]
    ) -> bool:
        """更新模型數據庫中的基準測試結果"""
        try:
            # 構建基準測試結果數據
            benchmark_scores = {
                "overall_score": benchmark_result["overall_score"],
                "reasoning_score": benchmark_result["detailed_scores"].get("reasoning_score"),
                "creativity_score": benchmark_result["detailed_scores"].get("creativity_score"),
                "accuracy_score": benchmark_result["detailed_scores"].get("accuracy_score"),
                "speed_score": benchmark_result["detailed_scores"].get("speed_score"),
                "success_rate": benchmark_result["success_rate"],
                "avg_latency_ms": benchmark_result["avg_latency_ms"],
                "suite_name": benchmark_result["suite_name"],
                "timestamp": benchmark_result["timestamp"],
                "duration_ms": benchmark_result["duration_ms"],
                "task_count": len(benchmark_result["task_results"]),
                "detailed_results": benchmark_result["task_results"]
            }
            
            # 更新數據庫
            success = await self.model_db.update_benchmark_scores(
                provider=provider,
                model_id=model_id,
                benchmark_results=benchmark_scores
            )
            
            if success:
                self.logger.info(f"✅ Updated benchmark scores in database for {provider}/{model_id}")
            else:
                self.logger.warning(f"⚠️ Failed to update benchmark scores for {provider}/{model_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Error updating model database: {e}")
            return False
    
    def _generate_batch_summary(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """生成批量測試總結"""
        total_models = len(results)
        successful_models = sum(1 for r in results.values() if r.get("success", True) and "error" not in r)
        failed_models = total_models - successful_models
        
        # 計算成功模型的平均指標
        successful_results = [r for r in results.values() if r.get("success", True) and "error" not in r]
        
        if successful_results:
            avg_overall_score = sum(r.get("overall_score", 0) for r in successful_results) / len(successful_results)
            avg_success_rate = sum(r.get("success_rate", 0) for r in successful_results) / len(successful_results)
            avg_latency = sum(r.get("avg_latency_ms", 0) for r in successful_results) / len(successful_results)
        else:
            avg_overall_score = 0.0
            avg_success_rate = 0.0
            avg_latency = 0.0
        
        # 找出最佳和最差模型
        best_model = None
        worst_model = None
        best_score = -1.0
        worst_score = 2.0
        
        for model_key, result in results.items():
            if result.get("success", True) and "error" not in result:
                score = result.get("overall_score", 0)
                if score > best_score:
                    best_score = score
                    best_model = model_key
                if score < worst_score:
                    worst_score = score
                    worst_model = model_key
        
        return {
            "total_models": total_models,
            "successful_models": successful_models,
            "failed_models": failed_models,
            "success_rate": successful_models / max(total_models, 1),
            "avg_overall_score": avg_overall_score,
            "avg_success_rate": avg_success_rate,
            "avg_latency_ms": avg_latency,
            "best_model": {
                "name": best_model,
                "score": best_score
            } if best_model else None,
            "worst_model": {
                "name": worst_model,
                "score": worst_score
            } if worst_model else None,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_benchmark_report(
        self,
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        suite_name: Optional[str] = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        獲取基準測試報告
        
        Args:
            provider: 提供商過濾
            model_id: 模型過濾
            suite_name: 測試套件過濾
            days_back: 回溯天數
            
        Returns:
            基準測試報告
        """
        try:
            # 從框架獲取歷史數據
            framework_history = self.framework.get_history(
                provider=provider,
                model_id=model_id,
                suite_name=suite_name,
                limit=100
            )
            
            # 從數據庫獲取歷史數據
            db_history = await self.model_db.get_benchmark_history(
                provider=provider,
                model_id=model_id,
                days_back=days_back
            )
            
            # 生成統計報告
            report = {
                "summary": {
                    "total_framework_records": len(framework_history),
                    "total_db_records": len(db_history),
                    "date_range_days": days_back,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                },
                "framework_history": framework_history[:10],  # 最近10條
                "database_history": db_history[:10],  # 最近10條
                "statistics": self._calculate_report_statistics(framework_history, db_history)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating benchmark report: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _calculate_report_statistics(
        self,
        framework_history: List[Dict[str, Any]],
        db_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """計算報告統計信息"""
        stats = {
            "framework_stats": {},
            "database_stats": {}
        }
        
        # 框架統計
        if framework_history:
            scores = [h.get("overall_score", 0) for h in framework_history if h.get("overall_score")]
            if scores:
                stats["framework_stats"] = {
                    "avg_score": sum(scores) / len(scores),
                    "max_score": max(scores),
                    "min_score": min(scores),
                    "score_trend": "improving" if len(scores) > 1 and scores[0] > scores[-1] else "stable"
                }
        
        # 數據庫統計
        if db_history:
            capability_scores = [h.get("capability_score", 0) for h in db_history if h.get("capability_score")]
            if capability_scores:
                stats["database_stats"] = {
                    "avg_capability_score": sum(capability_scores) / len(capability_scores),
                    "max_capability_score": max(capability_scores),
                    "min_capability_score": min(capability_scores),
                    "models_benchmarked": len(set(f"{h.get('provider', '')}/{h.get('model_id', '')}" for h in db_history))
                }
        
        return stats
    
    async def cleanup_old_results(self, days_to_keep: int = 90):
        """清理舊的測試結果"""
        try:
            # 清理框架歷史（保留最近的記錄）
            all_history = self.framework.get_history(limit=1000)
            if len(all_history) > days_to_keep * 5:  # 假設每天5次測試
                self.framework.results_history = all_history[:days_to_keep * 5]
                self.logger.info(f"✅ Cleaned framework history, kept {len(self.framework.results_history)} records")
            
            self.logger.info(f"✅ Cleanup completed, keeping results from last {days_to_keep} days")
            
        except Exception as e:
            self.logger.error(f"❌ Error during cleanup: {e}")
    
    def get_registered_suites(self) -> List[str]:
        """獲取已註冊的測試套件列表"""
        return list(self.framework.suites.keys())
    
    def get_suite_info(self, suite_name: str) -> Optional[Dict[str, Any]]:
        """獲取測試套件信息"""
        if suite_name not in self.framework.suites:
            return None
        
        suite = self.framework.suites[suite_name]
        return {
            "name": suite.name,
            "description": suite.description,
            "task_count": len(suite.tasks),
            "tasks": [
                {
                    "name": task.name,
                    "description": task.description,
                    "weight": task.weight,
                    "timeout_seconds": task.timeout_seconds
                }
                for task in suite.tasks
            ]
        }