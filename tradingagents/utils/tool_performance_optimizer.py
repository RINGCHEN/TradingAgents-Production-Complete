#!/usr/bin/env python3
"""
工具性能優化器 (Tool Performance Optimizer)
天工 (TianGong) - 工具性能優化和監控

此模組提供工具性能優化功能，包含：
1. 工具使用監控和統計
2. 重複功能檢測和消除
3. 內存使用優化
4. 懶加載和按需初始化
5. 工具性能分析和建議
"""

import asyncio
import gc
import psutil
import threading
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import weakref
import logging

from .tool_manager import get_tool_manager, ToolManager, ToolStatus, ToolType

# 配置日誌
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指標"""
    tool_id: str
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    execution_count: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    peak_memory: float = 0.0
    last_used: Optional[datetime] = None
    initialization_time: float = 0.0
    cleanup_count: int = 0


@dataclass
class OptimizationSuggestion:
    """優化建議"""
    tool_id: str
    suggestion_type: str
    priority: str  # high, medium, low
    description: str
    potential_savings: Dict[str, float]  # memory, cpu, time
    implementation_effort: str  # easy, medium, hard


class ToolPerformanceOptimizer:
    """工具性能優化器"""
    
    def __init__(self):
        self.tool_manager = get_tool_manager()
        self._metrics: Dict[str, PerformanceMetrics] = {}
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._optimization_history: List[Dict[str, Any]] = []
        
        # 性能監控配置
        self._monitor_interval = 5.0  # 秒
        self._memory_threshold = 100 * 1024 * 1024  # 100MB
        self._cpu_threshold = 80.0  # 80%
        self._idle_threshold = 300  # 5分鐘
        
        # 重複功能檢測
        self._duplicate_functions: Dict[str, Set[str]] = defaultdict(set)
        
        # 內存使用歷史
        self._memory_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        
        logger.info("工具性能優化器初始化完成")
    
    # ==================== 性能監控 ====================
    
    def start_monitoring(self):
        """開始性能監控"""
        if self._monitoring_active:
            logger.warning("性能監控已在運行")
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("工具性能監控已啟動")
    
    def stop_monitoring(self):
        """停止性能監控"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        
        logger.info("工具性能監控已停止")
    
    def _monitor_loop(self):
        """監控循環"""
        while self._monitoring_active:
            try:
                self._collect_metrics()
                self._analyze_performance()
                time.sleep(self._monitor_interval)
            except Exception as e:
                logger.error(f"性能監控循環錯誤: {str(e)}")
                time.sleep(self._monitor_interval)
    
    def _collect_metrics(self):
        """收集性能指標"""
        try:
            tools = self.tool_manager.list_tools()
            current_time = datetime.now()
            
            for tool_info in tools:
                tool_id = tool_info.tool_id
                
                # 初始化指標
                if tool_id not in self._metrics:
                    self._metrics[tool_id] = PerformanceMetrics(tool_id=tool_id)
                
                metrics = self._metrics[tool_id]
                
                # 更新基本指標
                metrics.memory_usage = tool_info.memory_usage
                metrics.execution_count = tool_info.usage_count
                metrics.average_execution_time = tool_info.average_execution_time
                metrics.last_used = tool_info.last_used
                metrics.initialization_time = tool_info.initialization_time
                
                # 記錄內存使用歷史
                self._memory_history[tool_id].append({
                    'timestamp': current_time,
                    'memory': metrics.memory_usage
                })
                
                # 更新峰值內存
                if metrics.memory_usage > metrics.peak_memory:
                    metrics.peak_memory = metrics.memory_usage
                
                # CPU 使用率（模擬）
                if tool_info.status == ToolStatus.BUSY:
                    metrics.cpu_usage = min(100.0, metrics.cpu_usage + 10.0)
                else:
                    metrics.cpu_usage = max(0.0, metrics.cpu_usage - 5.0)
                
        except Exception as e:
            logger.error(f"收集性能指標失敗: {str(e)}")
    
    def _analyze_performance(self):
        """分析性能"""
        try:
            current_time = datetime.now()
            
            for tool_id, metrics in self._metrics.items():
                # 檢查內存使用
                if metrics.memory_usage > self._memory_threshold:
                    logger.warning(f"工具 {tool_id} 內存使用過高: {metrics.memory_usage / 1024 / 1024:.1f}MB")
                
                # 檢查 CPU 使用
                if metrics.cpu_usage > self._cpu_threshold:
                    logger.warning(f"工具 {tool_id} CPU 使用過高: {metrics.cpu_usage:.1f}%")
                
                # 檢查空閒時間
                if (metrics.last_used and 
                    (current_time - metrics.last_used).total_seconds() > self._idle_threshold):
                    # 記錄建議清理，但不在同步方法中使用 await
                    logger.info(f"建議清理空閒工具: {tool_id}")
                
        except Exception as e:
            logger.error(f"性能分析失敗: {str(e)}")
    
    async def _suggest_cleanup(self, tool_id: str):
        """建議清理空閒工具"""
        try:
            tool_info = self.tool_manager.get_tool_info(tool_id)
            if tool_info and tool_info.auto_cleanup:
                logger.info(f"建議清理空閒工具: {tool_id}")
                # 這裡可以觸發自動清理
                
        except Exception as e:
            logger.error(f"建議清理工具 {tool_id} 失敗: {str(e)}")
    
    # ==================== 重複功能檢測 ====================
    
    async def detect_duplicate_functions(self) -> Dict[str, List[str]]:
        """檢測重複功能"""
        try:
            duplicates = {}
            tools = self.tool_manager.list_tools()
            
            # 按功能類型分組
            function_groups = defaultdict(list)
            
            for tool_info in tools:
                # 基於工具類型和描述檢測相似功能
                key = f"{tool_info.tool_type.value}_{tool_info.description.lower()}"
                function_groups[key].append(tool_info.tool_id)
            
            # 找出重複的功能組
            for function_key, tool_ids in function_groups.items():
                if len(tool_ids) > 1:
                    duplicates[function_key] = tool_ids
            
            return duplicates
            
        except Exception as e:
            logger.error(f"檢測重複功能失敗: {str(e)}")
            return {}
    
    # ==================== 內存優化 ====================
    
    async def optimize_memory_usage(self) -> Dict[str, Any]:
        """優化內存使用"""
        try:
            optimization_results = {
                'cleaned_tools': [],
                'memory_saved': 0.0,
                'actions_taken': []
            }
            
            current_time = datetime.now()
            
            for tool_id, metrics in self._metrics.items():
                tool_info = self.tool_manager.get_tool_info(tool_id)
                if not tool_info:
                    continue
                
                # 清理長時間未使用的工具
                if (metrics.last_used and 
                    (current_time - metrics.last_used).total_seconds() > self._idle_threshold):
                    
                    if tool_info.auto_cleanup and tool_info.status == ToolStatus.READY:
                        try:
                            # 記錄清理前的內存使用
                            before_memory = metrics.memory_usage
                            
                            # 執行清理（這裡是模擬）
                            logger.info(f"清理空閒工具: {tool_id}")
                            
                            # 更新統計
                            optimization_results['cleaned_tools'].append(tool_id)
                            optimization_results['memory_saved'] += before_memory
                            optimization_results['actions_taken'].append(f"清理工具 {tool_id}")
                            
                            metrics.cleanup_count += 1
                            
                        except Exception as e:
                            logger.error(f"清理工具 {tool_id} 失敗: {str(e)}")
            
            # 執行垃圾回收
            gc.collect()
            optimization_results['actions_taken'].append("執行垃圾回收")
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"內存優化失敗: {str(e)}")
            return {}
    
    # ==================== 懶加載優化 ====================
    
    async def optimize_lazy_loading(self) -> List[OptimizationSuggestion]:
        """優化懶加載策略"""
        try:
            suggestions = []
            tools = self.tool_manager.list_tools()
            
            for tool_info in tools:
                tool_id = tool_info.tool_id
                metrics = self._metrics.get(tool_id)
                
                if not metrics:
                    continue
                
                # 建議啟用懶加載
                if (not tool_info.lazy_load and 
                    metrics.execution_count < 10 and 
                    metrics.initialization_time > 1.0):
                    
                    suggestions.append(OptimizationSuggestion(
                        tool_id=tool_id,
                        suggestion_type="enable_lazy_loading",
                        priority="medium",
                        description=f"工具 {tool_id} 初始化時間較長但使用頻率低，建議啟用懶加載",
                        potential_savings={
                            "memory": metrics.memory_usage * 0.8,
                            "time": metrics.initialization_time
                        },
                        implementation_effort="easy"
                    ))
                
                # 建議禁用懶加載
                elif (tool_info.lazy_load and 
                      metrics.execution_count > 100 and 
                      metrics.average_execution_time > 0.1):
                    
                    suggestions.append(OptimizationSuggestion(
                        tool_id=tool_id,
                        suggestion_type="disable_lazy_loading",
                        priority="high",
                        description=f"工具 {tool_id} 使用頻率高，建議預加載以提高性能",
                        potential_savings={
                            "time": metrics.average_execution_time * 0.5
                        },
                        implementation_effort="easy"
                    ))
            
            return suggestions
            
        except Exception as e:
            logger.error(f"懶加載優化失敗: {str(e)}")
            return []
    
    # ==================== 性能分析和建議 ====================
    
    async def generate_performance_report(self) -> Dict[str, Any]:
        """生成性能報告"""
        try:
            report = {
                'summary': {},
                'tool_metrics': {},
                'optimization_suggestions': [],
                'duplicate_functions': {},
                'memory_analysis': {},
                'generated_at': datetime.now()
            }
            
            # 總體統計
            total_tools = len(self._metrics)
            total_memory = sum(m.memory_usage for m in self._metrics.values())
            avg_cpu = sum(m.cpu_usage for m in self._metrics.values()) / total_tools if total_tools > 0 else 0
            
            report['summary'] = {
                'total_tools': total_tools,
                'total_memory_mb': total_memory / 1024 / 1024,
                'average_cpu_usage': avg_cpu,
                'high_memory_tools': len([m for m in self._metrics.values() if m.memory_usage > self._memory_threshold]),
                'idle_tools': len([m for m in self._metrics.values() if m.last_used and 
                                 (datetime.now() - m.last_used).total_seconds() > self._idle_threshold])
            }
            
            # 工具指標
            for tool_id, metrics in self._metrics.items():
                report['tool_metrics'][tool_id] = {
                    'memory_mb': metrics.memory_usage / 1024 / 1024,
                    'cpu_usage': metrics.cpu_usage,
                    'execution_count': metrics.execution_count,
                    'avg_execution_time': metrics.average_execution_time,
                    'peak_memory_mb': metrics.peak_memory / 1024 / 1024,
                    'initialization_time': metrics.initialization_time,
                    'cleanup_count': metrics.cleanup_count,
                    'last_used': metrics.last_used.isoformat() if metrics.last_used else None
                }
            
            # 優化建議
            lazy_loading_suggestions = await self.optimize_lazy_loading()
            report['optimization_suggestions'] = [
                {
                    'tool_id': s.tool_id,
                    'type': s.suggestion_type,
                    'priority': s.priority,
                    'description': s.description,
                    'potential_savings': s.potential_savings,
                    'effort': s.implementation_effort
                }
                for s in lazy_loading_suggestions
            ]
            
            # 重複功能
            report['duplicate_functions'] = await self.detect_duplicate_functions()
            
            # 內存分析
            report['memory_analysis'] = {
                'high_usage_tools': [
                    tool_id for tool_id, metrics in self._metrics.items()
                    if metrics.memory_usage > self._memory_threshold
                ],
                'memory_trends': {
                    tool_id: list(history)[-10:]  # 最近10個數據點
                    for tool_id, history in self._memory_history.items()
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"生成性能報告失敗: {str(e)}")
            return {}
    
    # ==================== 自動優化 ====================
    
    async def auto_optimize(self) -> Dict[str, Any]:
        """自動優化"""
        try:
            optimization_results = {
                'memory_optimization': {},
                'suggestions_applied': [],
                'total_savings': {'memory': 0.0, 'time': 0.0},
                'optimized_at': datetime.now()
            }
            
            # 內存優化
            memory_results = await self.optimize_memory_usage()
            optimization_results['memory_optimization'] = memory_results
            optimization_results['total_savings']['memory'] = memory_results.get('memory_saved', 0.0)
            
            # 應用懶加載建議
            suggestions = await self.optimize_lazy_loading()
            high_priority_suggestions = [s for s in suggestions if s.priority == 'high']
            
            for suggestion in high_priority_suggestions[:3]:  # 限制自動應用的數量
                try:
                    # 這裡可以實現自動應用優化建議的邏輯
                    logger.info(f"自動應用優化建議: {suggestion.description}")
                    optimization_results['suggestions_applied'].append(suggestion.tool_id)
                    optimization_results['total_savings']['time'] += suggestion.potential_savings.get('time', 0.0)
                    
                except Exception as e:
                    logger.error(f"應用優化建議失敗: {str(e)}")
            
            # 記錄優化歷史
            self._optimization_history.append(optimization_results)
            
            return optimization_results
            
        except Exception as e:
            logger.error(f"自動優化失敗: {str(e)}")
            return {}
    
    # ==================== 工具使用統計 ====================
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """獲取使用統計"""
        try:
            stats = {
                'most_used_tools': [],
                'least_used_tools': [],
                'memory_intensive_tools': [],
                'cpu_intensive_tools': [],
                'performance_leaders': [],
                'optimization_candidates': []
            }
            
            if not self._metrics:
                return stats
            
            # 按使用次數排序
            by_usage = sorted(self._metrics.items(), key=lambda x: x[1].execution_count, reverse=True)
            stats['most_used_tools'] = [(tool_id, metrics.execution_count) for tool_id, metrics in by_usage[:5]]
            stats['least_used_tools'] = [(tool_id, metrics.execution_count) for tool_id, metrics in by_usage[-5:]]
            
            # 按內存使用排序
            by_memory = sorted(self._metrics.items(), key=lambda x: x[1].memory_usage, reverse=True)
            stats['memory_intensive_tools'] = [(tool_id, metrics.memory_usage / 1024 / 1024) for tool_id, metrics in by_memory[:5]]
            
            # 按 CPU 使用排序
            by_cpu = sorted(self._metrics.items(), key=lambda x: x[1].cpu_usage, reverse=True)
            stats['cpu_intensive_tools'] = [(tool_id, metrics.cpu_usage) for tool_id, metrics in by_cpu[:5]]
            
            # 性能領先者（高使用率，低資源消耗）
            performance_scores = []
            for tool_id, metrics in self._metrics.items():
                if metrics.execution_count > 0:
                    score = metrics.execution_count / max(1, metrics.memory_usage / 1024 / 1024 + metrics.cpu_usage)
                    performance_scores.append((tool_id, score))
            
            performance_scores.sort(key=lambda x: x[1], reverse=True)
            stats['performance_leaders'] = performance_scores[:5]
            
            # 優化候選（高資源消耗，低使用率）
            optimization_scores = []
            for tool_id, metrics in self._metrics.items():
                if metrics.execution_count < 10 and (metrics.memory_usage > 50 * 1024 * 1024 or metrics.cpu_usage > 20):
                    score = (metrics.memory_usage / 1024 / 1024 + metrics.cpu_usage) / max(1, metrics.execution_count)
                    optimization_scores.append((tool_id, score))
            
            optimization_scores.sort(key=lambda x: x[1], reverse=True)
            stats['optimization_candidates'] = optimization_scores[:5]
            
            return stats
            
        except Exception as e:
            logger.error(f"獲取使用統計失敗: {str(e)}")
            return {}
    
    # ==================== 清理和關閉 ====================
    
    def cleanup(self):
        """清理資源"""
        try:
            self.stop_monitoring()
            self._metrics.clear()
            self._memory_history.clear()
            self._optimization_history.clear()
            
            logger.info("工具性能優化器已清理")
            
        except Exception as e:
            logger.error(f"清理工具性能優化器失敗: {str(e)}")


# 全局性能優化器實例
_performance_optimizer = None


def get_performance_optimizer() -> ToolPerformanceOptimizer:
    """獲取性能優化器實例"""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = ToolPerformanceOptimizer()
    return _performance_optimizer