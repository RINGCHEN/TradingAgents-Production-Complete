"""
AI Task Analysis and Classification System
AI任務分析和分類系統

任務6.1: AI任務分析和分類
負責人: 小k (AI訓練專家團隊)

提供：
- AI任務自動分析
- 任務類型分類
- 複雜度評估
- 資源需求預測
- 優先級建議
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """任務類型枚舉"""
    TRAINING = "training"           # 訓練任務
    INFERENCE = "inference"         # 推理任務
    EVALUATION = "evaluation"       # 評估任務
    DATA_PROCESSING = "data_processing"  # 數據處理任務
    MODEL_OPTIMIZATION = "model_optimization"  # 模型優化任務
    SYSTEM_MAINTENANCE = "system_maintenance"  # 系統維護任務
    RESEARCH = "research"           # 研究任務
    DEPLOYMENT = "deployment"       # 部署任務

class TaskComplexity(Enum):
    """任務複雜度枚舉"""
    LOW = "low"                    # 低複雜度
    MEDIUM = "medium"              # 中等複雜度
    HIGH = "high"                  # 高複雜度
    CRITICAL = "critical"          # 關鍵複雜度

class TaskPriority(Enum):
    """任務優先級枚舉"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

@dataclass
class ResourceRequirement:
    """資源需求數據結構"""
    gpu_memory_gb: float = 0.0
    cpu_cores: int = 1
    system_memory_gb: float = 4.0
    storage_gb: float = 10.0
    estimated_time_hours: float = 1.0
    network_bandwidth_mbps: float = 100.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class TaskAnalysisResult:
    """任務分析結果數據結構"""
    task_id: str
    task_name: str
    task_type: TaskType
    complexity: TaskComplexity
    priority: TaskPriority
    resource_requirements: ResourceRequirement
    dependencies: List[str]
    estimated_duration: float  # 小時
    risk_factors: List[str]
    optimization_suggestions: List[str]
    analysis_confidence: float  # 0-1之間
    analysis_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['task_type'] = self.task_type.value
        result['complexity'] = self.complexity.value
        result['priority'] = self.priority.value
        return result

class TaskPatternMatcher:
    """任務模式匹配器"""
    
    def __init__(self):
        # 任務類型關鍵詞模式
        self.type_patterns = {
            TaskType.TRAINING: [
                r'train|training|訓練|學習',
                r'grpo|ppo|sft|fine.*tun',
                r'model.*train|訓練.*模型',
                r'epoch|batch|gradient'
            ],
            TaskType.INFERENCE: [
                r'infer|inference|推理|預測',
                r'predict|generate|生成',
                r'model.*run|運行.*模型',
                r'api.*call|調用.*api'
            ],
            TaskType.EVALUATION: [
                r'eval|evaluation|評估|測試',
                r'benchmark|基準|驗證',
                r'metric|指標|performance',
                r'validate|validation'
            ],
            TaskType.DATA_PROCESSING: [
                r'data.*process|數據.*處理',
                r'preprocess|預處理|清洗',
                r'transform|轉換|格式化',
                r'dataset|數據集'
            ],
            TaskType.MODEL_OPTIMIZATION: [
                r'optim|optimization|優化',
                r'hyperparameter|超參數',
                r'tune|tuning|調優',
                r'compress|壓縮|量化'
            ],
            TaskType.SYSTEM_MAINTENANCE: [
                r'maintain|maintenance|維護',
                r'update|更新|升級',
                r'backup|備份|恢復',
                r'monitor|監控|檢查'
            ],
            TaskType.RESEARCH: [
                r'research|研究|實驗',
                r'experiment|試驗|探索',
                r'analysis|分析|調研',
                r'prototype|原型|概念驗證'
            ],
            TaskType.DEPLOYMENT: [
                r'deploy|deployment|部署',
                r'release|發布|上線',
                r'production|生產環境',
                r'docker|container|容器'
            ]
        }
        
        # 複雜度關鍵詞模式
        self.complexity_patterns = {
            TaskComplexity.LOW: [
                r'simple|簡單|基礎|basic',
                r'quick|快速|輕量|light',
                r'test|測試|demo|演示'
            ],
            TaskComplexity.MEDIUM: [
                r'standard|標準|normal|正常',
                r'moderate|中等|regular',
                r'typical|典型|常規'
            ],
            TaskComplexity.HIGH: [
                r'complex|複雜|advanced|高級',
                r'sophisticated|精密|詳細',
                r'comprehensive|全面|完整'
            ],
            TaskComplexity.CRITICAL: [
                r'critical|關鍵|核心|core',
                r'mission.*critical|任務關鍵',
                r'production.*critical|生產關鍵',
                r'system.*critical|系統關鍵'
            ]
        }
        
        # 優先級關鍵詞模式
        self.priority_patterns = {
            TaskPriority.LOW: [
                r'low.*priority|低優先級',
                r'optional|可選|非必需',
                r'nice.*to.*have|錦上添花'
            ],
            TaskPriority.MEDIUM: [
                r'medium.*priority|中等優先級',
                r'normal|正常|標準',
                r'regular|常規'
            ],
            TaskPriority.HIGH: [
                r'high.*priority|高優先級',
                r'important|重要|關鍵',
                r'must.*have|必須'
            ],
            TaskPriority.URGENT: [
                r'urgent|緊急|急迫',
                r'asap|盡快|立即',
                r'time.*critical|時間關鍵'
            ],
            TaskPriority.CRITICAL: [
                r'critical.*priority|關鍵優先級',
                r'blocker|阻塞|blocking',
                r'emergency|緊急情況'
            ]
        }
    
    def match_task_type(self, task_description: str) -> Tuple[TaskType, float]:
        """匹配任務類型"""
        scores = {}
        for task_type, patterns in self.type_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, task_description, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[task_type] = score / len(patterns)
        
        if not scores:
            return TaskType.SYSTEM_MAINTENANCE, 0.1
        
        best_type = max(scores, key=scores.get)
        confidence = min(scores[best_type], 1.0)
        return best_type, confidence
    
    def match_complexity(self, task_description: str) -> Tuple[TaskComplexity, float]:
        """匹配任務複雜度"""
        scores = {}
        for complexity, patterns in self.complexity_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, task_description, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[complexity] = score / len(patterns)
        
        # 根據任務描述長度和技術詞彙密度調整複雜度
        tech_terms = [
            'algorithm', 'optimization', 'neural', 'deep', 'learning',
            'transformer', 'attention', 'gradient', 'backprop',
            '算法', '優化', '神經', '深度', '學習', '注意力', '梯度'
        ]
        tech_score = sum(1 for term in tech_terms if term.lower() in task_description.lower())
        length_score = len(task_description) / 100  # 每100字符增加複雜度
        
        # 如果沒有明確的複雜度關鍵詞，根據技術複雜度推斷
        if not scores:
            if tech_score >= 3 or length_score >= 2:
                return TaskComplexity.HIGH, 0.6
            elif tech_score >= 1 or length_score >= 1:
                return TaskComplexity.MEDIUM, 0.5
            else:
                return TaskComplexity.LOW, 0.4
        
        best_complexity = max(scores, key=scores.get)
        confidence = min(scores[best_complexity] + tech_score * 0.1, 1.0)
        return best_complexity, confidence
    
    def match_priority(self, task_description: str) -> Tuple[TaskPriority, float]:
        """匹配任務優先級"""
        scores = {}
        for priority, patterns in self.priority_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, task_description, re.IGNORECASE))
                score += matches
            if score > 0:
                scores[priority] = score / len(patterns)
        
        if not scores:
            return TaskPriority.MEDIUM, 0.3
        
        best_priority = max(scores, key=scores.get)
        confidence = min(scores[best_priority], 1.0)
        return best_priority, confidence

class ResourceEstimator:
    """資源需求估算器"""
    
    def __init__(self):
        # 基於任務類型的基礎資源需求
        self.base_requirements = {
            TaskType.TRAINING: ResourceRequirement(
                gpu_memory_gb=8.0,
                cpu_cores=4,
                system_memory_gb=16.0,
                storage_gb=50.0,
                estimated_time_hours=4.0,
                network_bandwidth_mbps=100.0
            ),
            TaskType.INFERENCE: ResourceRequirement(
                gpu_memory_gb=4.0,
                cpu_cores=2,
                system_memory_gb=8.0,
                storage_gb=10.0,
                estimated_time_hours=0.5,
                network_bandwidth_mbps=50.0
            ),
            TaskType.EVALUATION: ResourceRequirement(
                gpu_memory_gb=6.0,
                cpu_cores=2,
                system_memory_gb=12.0,
                storage_gb=20.0,
                estimated_time_hours=2.0,
                network_bandwidth_mbps=100.0
            ),
            TaskType.DATA_PROCESSING: ResourceRequirement(
                gpu_memory_gb=2.0,
                cpu_cores=4,
                system_memory_gb=16.0,
                storage_gb=100.0,
                estimated_time_hours=3.0,
                network_bandwidth_mbps=200.0
            ),
            TaskType.MODEL_OPTIMIZATION: ResourceRequirement(
                gpu_memory_gb=12.0,
                cpu_cores=6,
                system_memory_gb=24.0,
                storage_gb=30.0,
                estimated_time_hours=8.0,
                network_bandwidth_mbps=100.0
            ),
            TaskType.SYSTEM_MAINTENANCE: ResourceRequirement(
                gpu_memory_gb=1.0,
                cpu_cores=2,
                system_memory_gb=4.0,
                storage_gb=20.0,
                estimated_time_hours=1.0,
                network_bandwidth_mbps=50.0
            ),
            TaskType.RESEARCH: ResourceRequirement(
                gpu_memory_gb=10.0,
                cpu_cores=4,
                system_memory_gb=20.0,
                storage_gb=40.0,
                estimated_time_hours=12.0,
                network_bandwidth_mbps=100.0
            ),
            TaskType.DEPLOYMENT: ResourceRequirement(
                gpu_memory_gb=4.0,
                cpu_cores=2,
                system_memory_gb=8.0,
                storage_gb=30.0,
                estimated_time_hours=2.0,
                network_bandwidth_mbps=500.0
            )
        }
        
        # 複雜度調整係數
        self.complexity_multipliers = {
            TaskComplexity.LOW: 0.5,
            TaskComplexity.MEDIUM: 1.0,
            TaskComplexity.HIGH: 2.0,
            TaskComplexity.CRITICAL: 3.0
        }
    
    def estimate_resources(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        task_description: str
    ) -> ResourceRequirement:
        """估算資源需求"""
        # 獲取基礎需求
        base_req = self.base_requirements.get(task_type, self.base_requirements[TaskType.SYSTEM_MAINTENANCE])
        
        # 複雜度調整
        multiplier = self.complexity_multipliers[complexity]
        
        # 創建調整後的資源需求
        estimated_req = ResourceRequirement(
            gpu_memory_gb=base_req.gpu_memory_gb * multiplier,
            cpu_cores=max(1, int(base_req.cpu_cores * multiplier)),
            system_memory_gb=base_req.system_memory_gb * multiplier,
            storage_gb=base_req.storage_gb * multiplier,
            estimated_time_hours=base_req.estimated_time_hours * multiplier,
            network_bandwidth_mbps=base_req.network_bandwidth_mbps
        )
        
        # 基於任務描述的特殊調整
        estimated_req = self._adjust_for_specific_requirements(estimated_req, task_description)
        
        return estimated_req
    
    def _adjust_for_specific_requirements(
        self,
        base_req: ResourceRequirement,
        task_description: str
    ) -> ResourceRequirement:
        """基於任務描述調整特殊需求"""
        adjusted_req = ResourceRequirement(**asdict(base_req))
        
        # 大模型相關調整
        large_model_terms = ['large.*model', 'llm', 'gpt', 'bert', 'transformer']
        if any(re.search(term, task_description, re.IGNORECASE) for term in large_model_terms):
            adjusted_req.gpu_memory_gb *= 1.5
            adjusted_req.system_memory_gb *= 1.3
        
        # 批量處理調整
        batch_terms = ['batch', 'bulk', '批量', '大量']
        if any(term in task_description.lower() for term in batch_terms):
            adjusted_req.cpu_cores = max(adjusted_req.cpu_cores, 4)
            adjusted_req.system_memory_gb *= 1.2
        
        # 實時處理調整
        realtime_terms = ['real.*time', 'realtime', '實時', 'streaming']
        if any(re.search(term, task_description, re.IGNORECASE) for term in realtime_terms):
            adjusted_req.network_bandwidth_mbps *= 2
            adjusted_req.cpu_cores = max(adjusted_req.cpu_cores, 4)
        
        # 分散式處理調整
        distributed_terms = ['distributed', 'parallel', '分散式', '並行']
        if any(term in task_description.lower() for term in distributed_terms):
            adjusted_req.gpu_memory_gb *= 0.8  # 分散式可以減少單機需求
            adjusted_req.network_bandwidth_mbps *= 3
        
        return adjusted_req

class TaskAnalyzer:
    """AI任務分析器"""
    
    def __init__(self):
        self.pattern_matcher = TaskPatternMatcher()
        self.resource_estimator = ResourceEstimator()
        self.analysis_history = []
        
        # 依賴關係模式
        self.dependency_patterns = {
            'data_dependency': [
                r'需要.*數據|require.*data',
                r'依賴.*數據集|depend.*dataset',
                r'基於.*數據|based.*on.*data'
            ],
            'model_dependency': [
                r'需要.*模型|require.*model',
                r'依賴.*模型|depend.*model',
                r'基於.*模型|based.*on.*model'
            ],
            'system_dependency': [
                r'需要.*系統|require.*system',
                r'依賴.*服務|depend.*service',
                r'需要.*環境|require.*environment'
            ]
        }
        
        # 風險因素模式
        self.risk_patterns = {
            'resource_risk': [
                r'大量.*資源|large.*resource',
                r'高.*記憶體|high.*memory',
                r'長時間.*運行|long.*running'
            ],
            'complexity_risk': [
                r'複雜.*算法|complex.*algorithm',
                r'實驗性|experimental',
                r'未經.*測試|untested'
            ],
            'dependency_risk': [
                r'多個.*依賴|multiple.*depend',
                r'外部.*服務|external.*service',
                r'第三方.*api|third.*party.*api'
            ]
        }
    
    def analyze_task(
        self,
        task_id: str,
        task_name: str,
        task_description: str,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> TaskAnalysisResult:
        """分析AI任務"""
        logger.info(f"🔍 開始分析任務: {task_name}")
        
        # 任務類型分析
        task_type, type_confidence = self.pattern_matcher.match_task_type(task_description)
        
        # 複雜度分析
        complexity, complexity_confidence = self.pattern_matcher.match_complexity(task_description)
        
        # 優先級分析
        priority, priority_confidence = self.pattern_matcher.match_priority(task_description)
        
        # 資源需求估算
        resource_requirements = self.resource_estimator.estimate_resources(
            task_type, complexity, task_description
        )
        
        # 依賴關係分析
        dependencies = self._analyze_dependencies(task_description, additional_context)
        
        # 風險因素分析
        risk_factors = self._analyze_risk_factors(task_description, task_type, complexity)
        
        # 優化建議生成
        optimization_suggestions = self._generate_optimization_suggestions(
            task_type, complexity, resource_requirements, risk_factors
        )
        
        # 計算總體分析信心度
        analysis_confidence = np.mean([
            type_confidence,
            complexity_confidence,
            priority_confidence
        ])
        
        # 創建分析結果
        result = TaskAnalysisResult(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            complexity=complexity,
            priority=priority,
            resource_requirements=resource_requirements,
            dependencies=dependencies,
            estimated_duration=resource_requirements.estimated_time_hours,
            risk_factors=risk_factors,
            optimization_suggestions=optimization_suggestions,
            analysis_confidence=analysis_confidence,
            analysis_timestamp=datetime.now().isoformat()
        )
        
        # 添加到歷史記錄
        self.analysis_history.append(result)
        
        logger.info(f"✅ 任務分析完成: {task_type.value}, 複雜度: {complexity.value}, 信心度: {analysis_confidence:.2f}")
        return result
    
    def _analyze_dependencies(
        self,
        task_description: str,
        additional_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """分析任務依賴關係"""
        dependencies = []
        
        # 基於模式匹配的依賴分析
        for dep_type, patterns in self.dependency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_description, re.IGNORECASE):
                    dependencies.append(dep_type)
                    break
        
        # 基於上下文的依賴分析
        if additional_context:
            if 'prerequisites' in additional_context:
                dependencies.extend(additional_context['prerequisites'])
            if 'required_services' in additional_context:
                dependencies.extend(additional_context['required_services'])
        
        # 去重並返回
        return list(set(dependencies))
    
    def _analyze_risk_factors(
        self,
        task_description: str,
        task_type: TaskType,
        complexity: TaskComplexity
    ) -> List[str]:
        """分析風險因素"""
        risk_factors = []
        
        # 基於模式匹配的風險分析
        for risk_type, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_description, re.IGNORECASE):
                    risk_factors.append(risk_type)
                    break
        
        # 基於任務類型的風險
        if task_type == TaskType.TRAINING:
            risk_factors.append("training_instability")
        elif task_type == TaskType.DEPLOYMENT:
            risk_factors.append("production_impact")
        elif task_type == TaskType.RESEARCH:
            risk_factors.append("uncertain_outcome")
        
        # 基於複雜度的風險
        if complexity in [TaskComplexity.HIGH, TaskComplexity.CRITICAL]:
            risk_factors.append("high_complexity_risk")
        
        return list(set(risk_factors))
    
    def _generate_optimization_suggestions(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        resource_requirements: ResourceRequirement,
        risk_factors: List[str]
    ) -> List[str]:
        """生成優化建議"""
        suggestions = []
        
        # 基於任務類型的建議
        if task_type == TaskType.TRAINING:
            suggestions.append("考慮使用混合精度訓練減少GPU記憶體使用")
            suggestions.append("實施檢查點保存機制防止訓練中斷")
            if complexity == TaskComplexity.HIGH:
                suggestions.append("考慮分階段訓練策略")
        elif task_type == TaskType.INFERENCE:
            suggestions.append("考慮模型量化以提高推理速度")
            suggestions.append("實施批量推理以提高吞吐量")
        elif task_type == TaskType.DATA_PROCESSING:
            suggestions.append("考慮並行處理以提高數據處理速度")
            suggestions.append("實施數據管道優化")
        
        # 基於資源需求的建議
        if resource_requirements.gpu_memory_gb > 16:
            suggestions.append("考慮使用模型並行化或梯度檢查點")
        if resource_requirements.estimated_time_hours > 8:
            suggestions.append("建議分解為多個子任務並行執行")
        
        # 基於風險因素的建議
        if "high_complexity_risk" in risk_factors:
            suggestions.append("建議先進行小規模原型驗證")
        if "resource_risk" in risk_factors:
            suggestions.append("建議實施資源監控和自動擴縮容")
        if "dependency_risk" in risk_factors:
            suggestions.append("建議實施依賴健康檢查和容錯機制")
        
        return suggestions
    
    def batch_analyze_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[TaskAnalysisResult]:
        """批量分析任務"""
        results = []
        for task in tasks:
            result = self.analyze_task(
                task_id=task.get('id', ''),
                task_name=task.get('name', ''),
                task_description=task.get('description', ''),
                additional_context=task.get('context')
            )
            results.append(result)
        return results
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """獲取分析摘要"""
        if not self.analysis_history:
            return {"message": "No analysis history available"}
        
        # 統計各種任務類型
        type_counts = {}
        complexity_counts = {}
        priority_counts = {}
        total_gpu_memory = 0
        total_estimated_time = 0
        
        for result in self.analysis_history:
            # 任務類型統計
            task_type = result.task_type.value
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
            
            # 複雜度統計
            complexity = result.complexity.value
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
            
            # 優先級統計
            priority = result.priority.value
            priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            # 資源統計
            total_gpu_memory += result.resource_requirements.gpu_memory_gb
            total_estimated_time += result.estimated_duration
        
        return {
            "total_tasks_analyzed": len(self.analysis_history),
            "task_type_distribution": type_counts,
            "complexity_distribution": complexity_counts,
            "priority_distribution": priority_counts,
            "resource_summary": {
                "total_gpu_memory_gb": total_gpu_memory,
                "average_gpu_memory_gb": total_gpu_memory / len(self.analysis_history),
                "total_estimated_time_hours": total_estimated_time,
                "average_estimated_time_hours": total_estimated_time / len(self.analysis_history)
            },
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def export_analysis_results(self, output_path: str):
        """導出分析結果"""
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 導出詳細結果
        detailed_results = [result.to_dict() for result in self.analysis_history]
        with open(output_path / "task_analysis_results.json", 'w', encoding='utf-8') as f:
            json.dump(detailed_results, f, ensure_ascii=False, indent=2)
        
        # 導出摘要
        summary = self.get_analysis_summary()
        with open(output_path / "task_analysis_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"分析結果已導出到: {output_path}")

# 便利函數
def analyze_single_task(
    task_name: str,
    task_description: str,
    task_id: Optional[str] = None
) -> TaskAnalysisResult:
    """分析單個任務的便利函數"""
    analyzer = TaskAnalyzer()
    if task_id is None:
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return analyzer.analyze_task(task_id, task_name, task_description)

def create_task_analysis_report(
    tasks: List[Dict[str, Any]],
    output_path: str = "./task_analysis_report"
) -> Dict[str, Any]:
    """創建任務分析報告的便利函數"""
    analyzer = TaskAnalyzer()
    results = analyzer.batch_analyze_tasks(tasks)
    
    # 導出結果
    analyzer.export_analysis_results(output_path)
    
    # 返回摘要
    return analyzer.get_analysis_summary()