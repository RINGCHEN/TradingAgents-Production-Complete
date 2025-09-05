"""
AI Task Analyzer
AI任務分析器

任務6.1: AI任務分析和分類
負責人: 小k (AI訓練專家團隊)

功能：
- 智能分析AI任務特性
- 任務複雜度自動評估
- 資源需求預測
- 時間敏感度分析
- 任務類型自動分類
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任務類型枚舉"""
    TRAINING = "training"           # 模型訓練
    INFERENCE = "inference"         # 推理預測
    ANALYSIS = "analysis"           # 數據分析
    OPTIMIZATION = "optimization"   # 優化調整
    EVALUATION = "evaluation"       # 模型評估
    PREPROCESSING = "preprocessing" # 數據預處理
    DEPLOYMENT = "deployment"       # 模型部署
    MONITORING = "monitoring"       # 系統監控


class TaskComplexity(Enum):
    """任務複雜度枚舉"""
    SIMPLE = "simple"       # 簡單任務 (< 1小時)
    MODERATE = "moderate"   # 中等任務 (1-4小時)
    COMPLEX = "complex"     # 複雜任務 (4-12小時)
    ADVANCED = "advanced"   # 高級任務 (12小時+)


class ResourceType(Enum):
    """資源類型枚舉"""
    CPU = "cpu"
    GPU = "gpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"


class TimeSensitivity(Enum):
    """時間敏感度枚舉"""
    REAL_TIME = "real_time"     # 實時 (< 1秒)
    INTERACTIVE = "interactive" # 交互式 (< 10秒)
    BATCH = "batch"            # 批處理 (分鐘級)
    OFFLINE = "offline"        # 離線 (小時級)


@dataclass
class ResourceRequirement:
    """資源需求"""
    cpu_cores: int = 1
    gpu_memory_gb: float = 0.0
    system_memory_gb: float = 4.0
    storage_gb: float = 10.0
    network_bandwidth_mbps: float = 100.0
    estimated_duration_minutes: float = 60.0


@dataclass
class TaskClassification:
    """任務分類結果"""
    task_type: TaskType
    complexity: TaskComplexity
    time_sensitivity: TimeSensitivity
    resource_requirements: ResourceRequirement
    confidence_score: float = 0.0
    tags: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'task_type': self.task_type.value,
            'complexity': self.complexity.value,
            'time_sensitivity': self.time_sensitivity.value,
            'resource_requirements': {
                'cpu_cores': self.resource_requirements.cpu_cores,
                'gpu_memory_gb': self.resource_requirements.gpu_memory_gb,
                'system_memory_gb': self.resource_requirements.system_memory_gb,
                'storage_gb': self.resource_requirements.storage_gb,
                'network_bandwidth_mbps': self.resource_requirements.network_bandwidth_mbps,
                'estimated_duration_minutes': self.resource_requirements.estimated_duration_minutes
            },
            'confidence_score': self.confidence_score,
            'tags': self.tags,
            'recommendations': self.recommendations
        }


class TaskAnalyzer:
    """
    AI任務分析器
    
    智能分析AI任務的特性，包括：
    - 任務類型識別
    - 複雜度評估
    - 資源需求預測
    - 時間敏感度分析
    """
    
    def __init__(self):
        # 任務類型關鍵詞映射
        self.task_type_keywords = {
            TaskType.TRAINING: [
                'train', 'training', '訓練', 'fine-tune', 'finetune', '微調',
                'learn', 'learning', '學習', 'fit', 'optimize', 'grpo', 'ppo',
                'rlhf', 'sft', 'lora', 'adapter'
            ],
            TaskType.INFERENCE: [
                'predict', 'prediction', '預測', 'inference', '推理', 'generate',
                'completion', '生成', 'chat', '對話', 'answer', '回答'
            ],
            TaskType.ANALYSIS: [
                'analyze', 'analysis', '分析', 'evaluate', '評估', 'assess',
                'review', '檢視', 'examine', '檢查', 'study', '研究'
            ],
            TaskType.OPTIMIZATION: [
                'optimize', 'optimization', '優化', 'tune', 'tuning', '調整',
                'improve', '改善', 'enhance', '增強', 'refine', '精煉'
            ],
            TaskType.EVALUATION: [
                'evaluate', 'evaluation', '評估', 'test', 'testing', '測試',
                'validate', 'validation', '驗證', 'benchmark', '基準測試'
            ],
            TaskType.PREPROCESSING: [
                'preprocess', 'preprocessing', '預處理', 'clean', 'cleaning', '清理',
                'transform', '轉換', 'normalize', '標準化', 'tokenize', '分詞'
            ],
            TaskType.DEPLOYMENT: [
                'deploy', 'deployment', '部署', 'serve', 'serving', '服務',
                'publish', '發布', 'release', '釋出', 'production', '生產'
            ],
            TaskType.MONITORING: [
                'monitor', 'monitoring', '監控', 'track', 'tracking', '追蹤',
                'observe', '觀察', 'watch', '監視', 'alert', '告警'
            ]
        }
        
        # 複雜度指標
        self.complexity_indicators = {
            'simple': [
                'simple', '簡單', 'basic', '基礎', 'quick', '快速',
                'small', '小型', 'lightweight', '輕量'
            ],
            'moderate': [
                'moderate', '中等', 'medium', '中型', 'standard', '標準',
                'regular', '常規', 'typical', '典型'
            ],
            'complex': [
                'complex', '複雜', 'advanced', '高級', 'sophisticated', '精密',
                'large', '大型', 'comprehensive', '全面'
            ],
            'advanced': [
                'enterprise', '企業級', 'production', '生產級', 'distributed', '分散式',
                'scalable', '可擴展', 'high-performance', '高性能'
            ]
        }
        
        # 時間敏感度指標
        self.time_sensitivity_indicators = {
            'real_time': [
                'real-time', '實時', 'realtime', 'instant', '即時',
                'immediate', '立即', 'live', '即時', 'streaming', '串流'
            ],
            'interactive': [
                'interactive', '交互', 'responsive', '響應式', 'fast', '快速',
                'quick', '迅速', 'user-facing', '面向用戶'
            ],
            'batch': [
                'batch', '批處理', 'scheduled', '定時', 'periodic', '週期性',
                'background', '後台', 'queue', '隊列'
            ],
            'offline': [
                'offline', '離線', 'asynchronous', '異步', 'delayed', '延遲',
                'non-urgent', '非緊急', 'bulk', '批量'
            ]
        }
        
        # 資源需求模式
        self.resource_patterns = {
            'gpu_intensive': [
                'gpu', 'cuda', 'training', '訓練', 'deep learning', '深度學習',
                'neural network', '神經網絡', 'transformer', 'llm'
            ],
            'cpu_intensive': [
                'cpu', 'compute', '計算', 'processing', '處理', 'analysis', '分析',
                'optimization', '優化', 'simulation', '模擬'
            ],
            'memory_intensive': [
                'large model', '大模型', 'big data', '大數據', 'cache', '緩存',
                'in-memory', '內存', 'embedding', '嵌入'
            ],
            'storage_intensive': [
                'dataset', '數據集', 'backup', '備份', 'archive', '歸檔',
                'checkpoint', '檢查點', 'model storage', '模型存儲'
            ]
        }
    
    def analyze_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskClassification:
        """
        分析AI任務並返回分類結果
        
        Args:
            task_description: 任務描述
            context: 額外上下文信息
            
        Returns:
            TaskClassification: 任務分類結果
        """
        logger.info(f"🔍 分析任務: {task_description[:50]}...")
        
        # 預處理任務描述
        processed_desc = self._preprocess_description(task_description)
        
        # 識別任務類型
        task_type = self._identify_task_type(processed_desc)
        
        # 評估複雜度
        complexity = self._assess_complexity(processed_desc, context)
        
        # 分析時間敏感度
        time_sensitivity = self._analyze_time_sensitivity(processed_desc, context)
        
        # 預測資源需求
        resource_requirements = self._predict_resource_requirements(
            processed_desc, task_type, complexity, context
        )
        
        # 生成標籤
        tags = self._generate_tags(processed_desc, task_type, complexity)
        
        # 生成建議
        recommendations = self._generate_recommendations(
            task_type, complexity, time_sensitivity, resource_requirements
        )
        
        # 計算信心分數
        confidence_score = self._calculate_confidence_score(
            processed_desc, task_type, complexity
        )
        
        classification = TaskClassification(
            task_type=task_type,
            complexity=complexity,
            time_sensitivity=time_sensitivity,
            resource_requirements=resource_requirements,
            confidence_score=confidence_score,
            tags=tags,
            recommendations=recommendations
        )
        
        logger.info(f"✅ 任務分析完成: {task_type.value}, {complexity.value}, 信心度: {confidence_score:.2f}")
        
        return classification
    
    def _preprocess_description(self, description: str) -> str:
        """預處理任務描述"""
        # 轉換為小寫
        processed = description.lower()
        
        # 移除特殊字符但保留中文
        processed = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', processed)
        
        # 標準化空白字符
        processed = re.sub(r'\s+', ' ', processed).strip()
        
        return processed
    
    def _identify_task_type(self, description: str) -> TaskType:
        """識別任務類型"""
        type_scores = {}
        
        for task_type, keywords in self.task_type_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in description:
                    # 完整匹配給更高分數
                    if f" {keyword} " in f" {description} ":
                        score += 2
                    else:
                        score += 1
            type_scores[task_type] = score
        
        # 返回得分最高的任務類型
        if type_scores:
            best_type = max(type_scores, key=type_scores.get)
            if type_scores[best_type] > 0:
                return best_type
        
        # 默認返回分析類型
        return TaskType.ANALYSIS
    
    def _assess_complexity(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskComplexity:
        """評估任務複雜度"""
        complexity_score = 0
        
        # 基於關鍵詞評估
        for complexity_level, keywords in self.complexity_indicators.items():
            for keyword in keywords:
                if keyword in description:
                    if complexity_level == 'simple':
                        complexity_score -= 1
                    elif complexity_level == 'moderate':
                        complexity_score += 0
                    elif complexity_level == 'complex':
                        complexity_score += 2
                    elif complexity_level == 'advanced':
                        complexity_score += 3
        
        # 基於描述長度評估
        if len(description) > 200:
            complexity_score += 1
        elif len(description) < 50:
            complexity_score -= 1
        
        # 基於上下文信息評估
        if context:
            if context.get('model_size', 0) > 1000000000:  # 10億參數以上
                complexity_score += 2
            if context.get('dataset_size', 0) > 1000000:   # 100萬樣本以上
                complexity_score += 1
            if context.get('distributed', False):
                complexity_score += 2
        
        # 基於技術關鍵詞評估
        advanced_keywords = [
            'distributed', 'multi-gpu', 'cluster', 'kubernetes',
            'microservices', 'pipeline', 'orchestration'
        ]
        for keyword in advanced_keywords:
            if keyword in description:
                complexity_score += 1
        
        # 映射到複雜度枚舉
        if complexity_score <= -1:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 1:
            return TaskComplexity.MODERATE
        elif complexity_score <= 3:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.ADVANCED
    
    def _analyze_time_sensitivity(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> TimeSensitivity:
        """分析時間敏感度"""
        sensitivity_scores = {}
        
        for sensitivity, keywords in self.time_sensitivity_indicators.items():
            score = 0
            for keyword in keywords:
                if keyword in description:
                    score += 1
            sensitivity_scores[sensitivity] = score
        
        # 基於上下文評估
        if context:
            if context.get('user_facing', False):
                sensitivity_scores['interactive'] = sensitivity_scores.get('interactive', 0) + 2
            if context.get('deadline_hours', 24) < 1:
                sensitivity_scores['real_time'] = sensitivity_scores.get('real_time', 0) + 3
            elif context.get('deadline_hours', 24) < 24:
                sensitivity_scores['interactive'] = sensitivity_scores.get('interactive', 0) + 1
        
        # 返回得分最高的敏感度
        if sensitivity_scores:
            best_sensitivity = max(sensitivity_scores, key=sensitivity_scores.get)
            if sensitivity_scores[best_sensitivity] > 0:
                return TimeSensitivity(best_sensitivity)
        
        # 默認返回批處理
        return TimeSensitivity.BATCH
    
    def _predict_resource_requirements(
        self,
        description: str,
        task_type: TaskType,
        complexity: TaskComplexity,
        context: Optional[Dict[str, Any]] = None
    ) -> ResourceRequirement:
        """預測資源需求"""
        
        # 基礎資源需求
        base_requirements = ResourceRequirement()
        
        # 根據任務類型調整
        if task_type == TaskType.TRAINING:
            base_requirements.gpu_memory_gb = 8.0
            base_requirements.system_memory_gb = 16.0
            base_requirements.estimated_duration_minutes = 120.0
        elif task_type == TaskType.INFERENCE:
            base_requirements.gpu_memory_gb = 4.0
            base_requirements.system_memory_gb = 8.0
            base_requirements.estimated_duration_minutes = 5.0
        elif task_type == TaskType.ANALYSIS:
            base_requirements.cpu_cores = 4
            base_requirements.system_memory_gb = 8.0
            base_requirements.estimated_duration_minutes = 30.0
        
        # 根據複雜度調整
        complexity_multipliers = {
            TaskComplexity.SIMPLE: 0.5,
            TaskComplexity.MODERATE: 1.0,
            TaskComplexity.COMPLEX: 2.0,
            TaskComplexity.ADVANCED: 4.0
        }
        
        multiplier = complexity_multipliers[complexity]
        base_requirements.gpu_memory_gb *= multiplier
        base_requirements.system_memory_gb *= multiplier
        base_requirements.estimated_duration_minutes *= multiplier
        
        # 基於關鍵詞調整
        for pattern_type, keywords in self.resource_patterns.items():
            if any(keyword in description for keyword in keywords):
                if pattern_type == 'gpu_intensive':
                    base_requirements.gpu_memory_gb *= 1.5
                elif pattern_type == 'cpu_intensive':
                    base_requirements.cpu_cores *= 2
                elif pattern_type == 'memory_intensive':
                    base_requirements.system_memory_gb *= 2
                elif pattern_type == 'storage_intensive':
                    base_requirements.storage_gb *= 5
        
        # 基於上下文調整
        if context:
            if context.get('model_size', 0) > 0:
                # 根據模型大小調整GPU記憶體需求
                model_size_gb = context['model_size'] / 1000000000 * 4  # 粗略估算
                base_requirements.gpu_memory_gb = max(base_requirements.gpu_memory_gb, model_size_gb)
            
            if context.get('batch_size', 0) > 0:
                # 根據批次大小調整記憶體需求
                batch_multiplier = max(1, context['batch_size'] / 4)
                base_requirements.gpu_memory_gb *= batch_multiplier
                base_requirements.system_memory_gb *= batch_multiplier
        
        # 確保最小值
        base_requirements.cpu_cores = max(1, base_requirements.cpu_cores)
        base_requirements.gpu_memory_gb = max(0, base_requirements.gpu_memory_gb)
        base_requirements.system_memory_gb = max(2, base_requirements.system_memory_gb)
        base_requirements.storage_gb = max(5, base_requirements.storage_gb)
        base_requirements.estimated_duration_minutes = max(1, base_requirements.estimated_duration_minutes)
        
        return base_requirements
    
    def _generate_tags(
        self,
        description: str,
        task_type: TaskType,
        complexity: TaskComplexity
    ) -> List[str]:
        """生成任務標籤"""
        tags = [task_type.value, complexity.value]
        
        # 技術標籤
        tech_tags = {
            'machine_learning': ['ml', 'machine learning', '機器學習', 'ai', '人工智能'],
            'deep_learning': ['deep learning', '深度學習', 'neural', 'transformer'],
            'nlp': ['nlp', 'natural language', '自然語言', 'text', 'language'],
            'computer_vision': ['cv', 'computer vision', '計算機視覺', 'image', 'vision'],
            'reinforcement_learning': ['rl', 'reinforcement', '強化學習', 'policy', 'reward'],
            'data_science': ['data science', '數據科學', 'analytics', '分析', 'statistics'],
            'gpu_computing': ['gpu', 'cuda', 'parallel', '並行', 'acceleration'],
            'cloud': ['cloud', '雲端', 'aws', 'gcp', 'azure', 'kubernetes'],
            'financial': ['financial', '金融', 'trading', '交易', 'investment', '投資']
        }
        
        for tag, keywords in tech_tags.items():
            if any(keyword in description for keyword in keywords):
                tags.append(tag)
        
        return list(set(tags))  # 去重
    
    def _generate_recommendations(
        self,
        task_type: TaskType,
        complexity: TaskComplexity,
        time_sensitivity: TimeSensitivity,
        resource_requirements: ResourceRequirement
    ) -> List[str]:
        """生成優化建議"""
        recommendations = []
        
        # 基於任務類型的建議
        if task_type == TaskType.TRAINING:
            recommendations.append("建議使用GPU加速訓練")
            recommendations.append("考慮使用混合精度訓練節省記憶體")
            if complexity in [TaskComplexity.COMPLEX, TaskComplexity.ADVANCED]:
                recommendations.append("建議使用檢查點保存機制")
                recommendations.append("考慮分散式訓練提高效率")
        
        elif task_type == TaskType.INFERENCE:
            if time_sensitivity == TimeSensitivity.REAL_TIME:
                recommendations.append("建議使用模型量化加速推理")
                recommendations.append("考慮使用TensorRT優化")
            recommendations.append("建議使用批量推理提高吞吐量")
        
        # 基於複雜度的建議
        if complexity == TaskComplexity.ADVANCED:
            recommendations.append("建議使用容器化部署")
            recommendations.append("考慮使用Kubernetes進行編排")
            recommendations.append("建議實施全面的監控和日誌")
        
        # 基於資源需求的建議
        if resource_requirements.gpu_memory_gb > 12:
            recommendations.append("建議使用RTX 4090或更高級GPU")
            recommendations.append("考慮使用模型並行化")
        elif resource_requirements.gpu_memory_gb > 8:
            recommendations.append("RTX 4070適合此任務")
        
        if resource_requirements.system_memory_gb > 32:
            recommendations.append("建議升級系統記憶體到64GB+")
        
        # 基於時間敏感度的建議
        if time_sensitivity == TimeSensitivity.REAL_TIME:
            recommendations.append("建議使用SSD存儲加速I/O")
            recommendations.append("考慮使用記憶體緩存")
        
        return recommendations
    
    def _calculate_confidence_score(
        self,
        description: str,
        task_type: TaskType,
        complexity: TaskComplexity
    ) -> float:
        """計算分類信心分數"""
        confidence = 0.5  # 基礎信心分數
        
        # 基於描述長度
        if len(description) > 100:
            confidence += 0.1
        elif len(description) < 20:
            confidence -= 0.1
        
        # 基於關鍵詞匹配度
        matched_keywords = 0
        total_keywords = 0
        
        for keywords in self.task_type_keywords.values():
            total_keywords += len(keywords)
            for keyword in keywords:
                if keyword in description:
                    matched_keywords += 1
        
        if total_keywords > 0:
            keyword_ratio = matched_keywords / total_keywords
            confidence += keyword_ratio * 0.3
        
        # 基於任務類型特定性
        type_keywords = self.task_type_keywords[task_type]
        type_matches = sum(1 for keyword in type_keywords if keyword in description)
        if type_matches > 0:
            confidence += min(type_matches * 0.1, 0.2)
        
        return min(max(confidence, 0.0), 1.0)
    
    def batch_analyze_tasks(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[TaskClassification]:
        """批量分析任務"""
        logger.info(f"🔄 批量分析 {len(tasks)} 個任務...")
        
        results = []
        for i, task in enumerate(tasks):
            description = task.get('description', '')
            context = task.get('context', {})
            
            try:
                classification = self.analyze_task(description, context)
                results.append(classification)
                logger.info(f"✅ 任務 {i+1}/{len(tasks)} 分析完成")
            except Exception as e:
                logger.error(f"❌ 任務 {i+1} 分析失敗: {e}")
                # 創建默認分類
                default_classification = TaskClassification(
                    task_type=TaskType.ANALYSIS,
                    complexity=TaskComplexity.MODERATE,
                    time_sensitivity=TimeSensitivity.BATCH,
                    resource_requirements=ResourceRequirement(),
                    confidence_score=0.1,
                    tags=['unknown'],
                    recommendations=['需要更詳細的任務描述']
                )
                results.append(default_classification)
        
        logger.info(f"🎉 批量分析完成，共處理 {len(results)} 個任務")
        return results
    
    def get_task_statistics(
        self,
        classifications: List[TaskClassification]
    ) -> Dict[str, Any]:
        """獲取任務統計信息"""
        if not classifications:
            return {}
        
        # 任務類型分佈
        type_counts = {}
        for classification in classifications:
            task_type = classification.task_type.value
            type_counts[task_type] = type_counts.get(task_type, 0) + 1
        
        # 複雜度分佈
        complexity_counts = {}
        for classification in classifications:
            complexity = classification.complexity.value
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        # 平均資源需求
        total_gpu_memory = sum(c.resource_requirements.gpu_memory_gb for c in classifications)
        total_system_memory = sum(c.resource_requirements.system_memory_gb for c in classifications)
        total_duration = sum(c.resource_requirements.estimated_duration_minutes for c in classifications)
        
        avg_gpu_memory = total_gpu_memory / len(classifications)
        avg_system_memory = total_system_memory / len(classifications)
        avg_duration = total_duration / len(classifications)
        
        # 平均信心分數
        avg_confidence = sum(c.confidence_score for c in classifications) / len(classifications)
        
        return {
            'total_tasks': len(classifications),
            'task_type_distribution': type_counts,
            'complexity_distribution': complexity_counts,
            'average_resources': {
                'gpu_memory_gb': round(avg_gpu_memory, 2),
                'system_memory_gb': round(avg_system_memory, 2),
                'estimated_duration_minutes': round(avg_duration, 2)
            },
            'average_confidence_score': round(avg_confidence, 3),
            'timestamp': datetime.now().isoformat()
        }