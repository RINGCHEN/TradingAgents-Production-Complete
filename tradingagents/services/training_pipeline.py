#!/usr/bin/env python3
"""
Training Pipeline - 軌跡收集和模型訓練管道
天工 (TianGong) - ART 強化學習訓練管道系統

此模組提供：
1. 訓練軌跡收集和管理
2. ART 模型訓練管道
3. 數據預處理和增強
4. 訓練過程監控
5. 模型版本管理和部署
"""

import asyncio
import logging
import json
import pickle
import gzip
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Callable, Iterator
from pathlib import Path
import uuid
import numpy as np
from collections import defaultdict, deque
import threading
import queue
import time

# ART Integration
try:
    import openpipe_art as art
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False
    art = None

from ..agents.analysts.base_analyst import AnalysisResult, AnalysisState, AnalysisType
from .analyst_evaluation import TrainingTrajectory, MarketValidation, UserFeedback


class TrainingStage(Enum):
    """訓練階段"""
    DATA_COLLECTION = "data_collection"
    DATA_PREPROCESSING = "data_preprocessing"
    MODEL_TRAINING = "model_training"
    MODEL_EVALUATION = "model_evaluation"
    MODEL_DEPLOYMENT = "model_deployment"
    COMPLETED = "completed"
    FAILED = "failed"


class DataQuality(Enum):
    """數據品質等級"""
    POOR = "poor"           # 品質差，不適合訓練
    FAIR = "fair"           # 品質一般，可以使用但需要清理
    GOOD = "good"           # 品質良好，適合訓練
    EXCELLENT = "excellent"  # 品質優秀，高價值訓練數據


@dataclass
class TrainingConfig:
    """訓練配置"""
    analyst_id: str
    model_name: str = "qwen2.5-7b-instruct"
    
    # 訓練參數
    training_steps: int = 1000
    learning_rate: float = 1e-5
    batch_size: int = 8
    warmup_steps: int = 100
    
    # 數據參數
    min_trajectory_count: int = 100
    max_trajectory_count: int = 10000
    validation_split: float = 0.2
    
    # 品質控制
    min_reward_threshold: float = -0.5
    max_sequence_length: int = 4096
    
    # 訓練策略
    use_grpo: bool = True
    use_data_augmentation: bool = True
    enable_early_stopping: bool = True
    patience: int = 10
    
    # 硬體設置
    use_gpu: bool = True
    mixed_precision: bool = True
    gradient_checkpointing: bool = True
    
    # 保存設置
    save_steps: int = 100
    eval_steps: int = 50
    max_checkpoints: int = 5


@dataclass
class TrainingJob:
    """訓練任務"""
    job_id: str
    analyst_id: str
    config: TrainingConfig
    
    # 狀態信息
    status: TrainingStage = TrainingStage.DATA_COLLECTION
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 進度信息
    progress: float = 0.0
    current_step: int = 0
    total_steps: int = 0
    
    # 結果信息
    best_metric: float = 0.0
    final_loss: float = float('inf')
    model_path: Optional[str] = None
    
    # 錯誤信息
    error_message: Optional[str] = None
    error_traceback: Optional[str] = None
    
    # 資源使用
    gpu_memory_used: float = 0.0
    training_time: float = 0.0
    
    def is_active(self) -> bool:
        """檢查任務是否活躍"""
        return self.status not in [TrainingStage.COMPLETED, TrainingStage.FAILED]
    
    def get_duration(self) -> Optional[timedelta]:
        """獲取任務持續時間"""
        if self.started_at:
            end_time = self.completed_at or datetime.now()
            return end_time - self.started_at
        return None


class TrajectoryBuffer:
    """軌跡緩衝區"""
    
    def __init__(self, max_size: int = 50000):
        self.max_size = max_size
        self.trajectories: deque = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # 索引
        self.analyst_index: Dict[str, List[int]] = defaultdict(list)
        self.reward_index: Dict[str, List[int]] = defaultdict(list)  # 按獎勵範圍索引
    
    def add_trajectory(self, trajectory: TrainingTrajectory) -> bool:
        """添加軌跡"""
        
        with self.lock:
            try:
                # 驗證軌跡
                if not self._validate_trajectory(trajectory):
                    return False
                
                # 添加到緩衝區
                index = len(self.trajectories)
                self.trajectories.append(trajectory)
                
                # 更新索引
                self.analyst_index[trajectory.analyst_id].append(index)
                
                # 按獎勵範圍索引
                reward_range = self._get_reward_range(trajectory.reward_score)
                self.reward_index[reward_range].append(index)
                
                # 清理過期索引
                if len(self.trajectories) >= self.max_size:
                    self._cleanup_indices()
                
                return True
                
            except Exception as e:
                self.logger.error(f"添加軌跡失敗: {str(e)}")
                return False
    
    def get_trajectories(
        self, 
        analyst_id: str = None,
        min_reward: float = None,
        max_reward: float = None,
        limit: int = None
    ) -> List[TrainingTrajectory]:
        """獲取軌跡"""
        
        with self.lock:
            results = []
            
            if analyst_id:
                # 按分析師過濾
                indices = self.analyst_index.get(analyst_id, [])
                trajectories = [self.trajectories[i] for i in indices if i < len(self.trajectories)]
            else:
                trajectories = list(self.trajectories)
            
            # 按獎勵過濾
            for trajectory in trajectories:
                if min_reward is not None and trajectory.reward_score < min_reward:
                    continue
                if max_reward is not None and trajectory.reward_score > max_reward:
                    continue
                
                results.append(trajectory)
            
            # 限制數量
            if limit and len(results) > limit:
                results = results[-limit:]  # 取最新的
            
            return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        
        with self.lock:
            stats = {
                'total_trajectories': len(self.trajectories),
                'analysts': len(self.analyst_index),
                'analyst_distribution': {
                    analyst_id: len(indices) 
                    for analyst_id, indices in self.analyst_index.items()
                },
                'reward_distribution': {},
                'quality_distribution': {}
            }
            
            if self.trajectories:
                rewards = [t.reward_score for t in self.trajectories]
                stats['reward_distribution'] = {
                    'mean': np.mean(rewards),
                    'std': np.std(rewards),
                    'min': np.min(rewards),
                    'max': np.max(rewards),
                    'median': np.median(rewards)
                }
                
                # 品質分佈
                quality_counts = defaultdict(int)
                for trajectory in self.trajectories:
                    quality = self._assess_trajectory_quality(trajectory)
                    quality_counts[quality.value] += 1
                
                stats['quality_distribution'] = dict(quality_counts)
            
            return stats
    
    def _validate_trajectory(self, trajectory: TrainingTrajectory) -> bool:
        """驗證軌跡"""
        
        # 基本必填字段檢查
        if not trajectory.trajectory_id or not trajectory.analyst_id:
            return False
        
        # 獎勵分數範圍檢查
        if not (-1.0 <= trajectory.reward_score <= 1.0):
            return False
        
        # 提示詞長度檢查
        if not trajectory.prompt or len(trajectory.prompt) > 10000:
            return False
        
        return True
    
    def _get_reward_range(self, reward: float) -> str:
        """獲取獎勵範圍"""
        if reward >= 0.8:
            return "excellent"
        elif reward >= 0.5:
            return "good"
        elif reward >= 0.0:
            return "fair"
        else:
            return "poor"
    
    def _assess_trajectory_quality(self, trajectory: TrainingTrajectory) -> DataQuality:
        """評估軌跡品質"""
        
        quality_score = 0.0
        
        # 獎勵分數權重
        if trajectory.reward_score >= 0.8:
            quality_score += 0.4
        elif trajectory.reward_score >= 0.5:
            quality_score += 0.3
        elif trajectory.reward_score >= 0.0:
            quality_score += 0.2
        
        # 市場驗證權重
        if trajectory.market_validation is not None:
            quality_score += 0.3
        
        # 用戶反饋權重
        if trajectory.user_feedback is not None:
            quality_score += 0.2
        
        # 執行時間權重（適中最佳）
        if 1000 <= trajectory.execution_time_ms <= 10000:
            quality_score += 0.1
        
        # 分類品質
        if quality_score >= 0.8:
            return DataQuality.EXCELLENT
        elif quality_score >= 0.6:
            return DataQuality.GOOD
        elif quality_score >= 0.4:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR
    
    def _cleanup_indices(self):
        """清理過期索引"""
        
        # 重建索引
        self.analyst_index.clear()
        self.reward_index.clear()
        
        for i, trajectory in enumerate(self.trajectories):
            self.analyst_index[trajectory.analyst_id].append(i)
            reward_range = self._get_reward_range(trajectory.reward_score)
            self.reward_index[reward_range].append(i)


class DataPreprocessor:
    """數據預處理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
    
    def preprocess_trajectories(
        self, 
        trajectories: List[TrainingTrajectory],
        config: TrainingConfig
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """預處理軌跡數據"""
        
        processed_data = []
        stats = {
            'original_count': len(trajectories),
            'filtered_count': 0,
            'augmented_count': 0,
            'quality_distribution': defaultdict(int)
        }
        
        for trajectory in trajectories:
            # 品質過濾
            if trajectory.reward_score < config.min_reward_threshold:
                continue
            
            # 轉換為訓練格式
            training_sample = self._trajectory_to_training_sample(trajectory, config)
            if training_sample:
                processed_data.append(training_sample)
                stats['filtered_count'] += 1
                
                # 數據增強
                if config.use_data_augmentation:
                    augmented_samples = self._augment_sample(training_sample, trajectory)
                    processed_data.extend(augmented_samples)
                    stats['augmented_count'] += len(augmented_samples)
        
        # 打亂數據
        np.random.shuffle(processed_data)
        
        # 截斷到最大數量
        if len(processed_data) > config.max_trajectory_count:
            processed_data = processed_data[:config.max_trajectory_count]
        
        stats['final_count'] = len(processed_data)
        
        return processed_data, stats
    
    def _trajectory_to_training_sample(
        self, 
        trajectory: TrainingTrajectory,
        config: TrainingConfig
    ) -> Optional[Dict[str, Any]]:
        """將軌跡轉換為訓練樣本"""
        
        try:
            # 構建輸入序列
            prompt = trajectory.prompt
            
            # 添加上下文信息
            if trajectory.context:
                context_str = self._format_context(trajectory.context)
                prompt = f"{context_str}\n\n{prompt}"
            
            # 構建響應
            response = self._format_response(trajectory.analysis_result)
            
            # 檢查序列長度
            total_length = len(prompt) + len(response)
            if total_length > config.max_sequence_length:
                # 截斷提示詞
                max_prompt_length = config.max_sequence_length - len(response) - 100
                if max_prompt_length > 0:
                    prompt = prompt[:max_prompt_length] + "..."
                else:
                    return None
            
            return {
                'prompt': prompt,
                'response': response,
                'reward': trajectory.reward_score,
                'metadata': {
                    'trajectory_id': trajectory.trajectory_id,
                    'analyst_id': trajectory.analyst_id,
                    'timestamp': trajectory.timestamp.isoformat(),
                    'execution_time': trajectory.execution_time_ms,
                    'tokens_used': trajectory.tokens_used,
                    'cost': trajectory.cost
                }
            }
            
        except Exception as e:
            self.logger.error(f"轉換訓練樣本失敗: {str(e)}")
            return None
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """格式化上下文"""
        
        context_lines = []
        
        if 'stock_id' in context:
            context_lines.append(f"股票代號: {context['stock_id']}")
        
        if 'stock_data' in context:
            stock_data = context['stock_data']
            if isinstance(stock_data, dict):
                context_lines.append(f"當前價格: {stock_data.get('price', 'N/A')}")
                context_lines.append(f"成交量: {stock_data.get('volume', 'N/A')}")
        
        if 'financial_data' in context:
            financial_data = context['financial_data']
            if isinstance(financial_data, dict):
                context_lines.append(f"財務數據: {json.dumps(financial_data, ensure_ascii=False)}")
        
        return "\n".join(context_lines)
    
    def _format_response(self, analysis_result: AnalysisResult) -> str:
        """格式化響應"""
        
        response_parts = []
        
        # 建議
        response_parts.append(f"投資建議: {analysis_result.recommendation}")
        
        # 信心度
        response_parts.append(f"信心度: {analysis_result.confidence:.2f}")
        
        # 目標價格
        if analysis_result.target_price:
            response_parts.append(f"目標價格: {analysis_result.target_price}")
        
        # 分析理由
        if analysis_result.reasoning:
            response_parts.append("分析理由:")
            for i, reason in enumerate(analysis_result.reasoning, 1):
                response_parts.append(f"{i}. {reason}")
        
        # 技術指標
        if analysis_result.technical_indicators:
            response_parts.append("技術指標:")
            for indicator, value in analysis_result.technical_indicators.items():
                response_parts.append(f"- {indicator}: {value}")
        
        # 基本面指標
        if analysis_result.fundamental_metrics:
            response_parts.append("基本面指標:")
            for metric, value in analysis_result.fundamental_metrics.items():
                response_parts.append(f"- {metric}: {value}")
        
        return "\n".join(response_parts)
    
    def _augment_sample(
        self, 
        sample: Dict[str, Any], 
        trajectory: TrainingTrajectory
    ) -> List[Dict[str, Any]]:
        """數據增強"""
        
        augmented_samples = []
        
        # 同義詞替換增強
        if trajectory.reward_score > 0.5:  # 只對好的樣本進行增強
            augmented_sample = self._synonym_augmentation(sample)
            if augmented_sample:
                augmented_samples.append(augmented_sample)
        
        # 視角變換增強
        perspective_sample = self._perspective_augmentation(sample)
        if perspective_sample:
            augmented_samples.append(perspective_sample)
        
        return augmented_samples
    
    def _synonym_augmentation(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """同義詞替換增強"""
        
        # 簡單的同義詞替換表
        synonyms = {
            '建議': '推薦',
            '分析': '評估',
            '投資': '買進',
            '風險': '不確定性',
            '機會': '潛力'
        }
        
        try:
            augmented_response = sample['response']
            
            for original, synonym in synonyms.items():
                if original in augmented_response:
                    augmented_response = augmented_response.replace(original, synonym, 1)
            
            if augmented_response != sample['response']:
                augmented_sample = sample.copy()
                augmented_sample['response'] = augmented_response
                augmented_sample['metadata'] = sample['metadata'].copy()
                augmented_sample['metadata']['augmentation'] = 'synonym'
                return augmented_sample
            
        except Exception as e:
            self.logger.error(f"同義詞增強失敗: {str(e)}")
        
        return None
    
    def _perspective_augmentation(self, sample: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """視角變換增強"""
        
        try:
            # 在提示詞中添加不同的分析視角
            perspectives = [
                "從長期投資角度來看，",
                "考慮風險控制的前提下，",
                "結合市場整體趨勢，"
            ]
            
            import random
            perspective = random.choice(perspectives)
            
            augmented_prompt = perspective + sample['prompt']
            
            augmented_sample = sample.copy()
            augmented_sample['prompt'] = augmented_prompt
            augmented_sample['metadata'] = sample['metadata'].copy()
            augmented_sample['metadata']['augmentation'] = 'perspective'
            
            return augmented_sample
            
        except Exception as e:
            self.logger.error(f"視角增強失敗: {str(e)}")
            return None


class ARTTrainer:
    """ART 訓練器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.is_available = ART_AVAILABLE
        
        if self.is_available:
            self._initialize_art_client()
        else:
            self.logger.warning("ART 不可用，將使用模擬訓練")
    
    def _initialize_art_client(self):
        """初始化 ART 客戶端"""
        
        try:
            self.client = art.ARTClient(
                base_url=self.config.get('art_server_url', 'http://localhost:8000'),
                api_key=self.config.get('art_api_key')
            )
            self.logger.info("ART 訓練客戶端初始化成功")
        except Exception as e:
            self.logger.error(f"ART 訓練客戶端初始化失敗: {str(e)}")
            self.is_available = False
    
    async def start_training(
        self, 
        job: TrainingJob,
        training_data: List[Dict[str, Any]]
    ) -> bool:
        """開始訓練"""
        
        try:
            job.status = TrainingStage.MODEL_TRAINING
            job.started_at = datetime.now()
            job.total_steps = job.config.training_steps
            
            if self.is_available:
                return await self._train_with_art(job, training_data)
            else:
                return await self._simulate_training(job, training_data)
                
        except Exception as e:
            job.status = TrainingStage.FAILED
            job.error_message = str(e)
            self.logger.error(f"訓練開始失敗 {job.job_id}: {str(e)}")
            return False
    
    async def _train_with_art(
        self, 
        job: TrainingJob, 
        training_data: List[Dict[str, Any]]
    ) -> bool:
        """使用 ART 進行訓練"""
        
        try:
            # 準備訓練配置
            training_config = {
                'model_name': job.config.model_name,
                'training_steps': job.config.training_steps,
                'learning_rate': job.config.learning_rate,
                'batch_size': job.config.batch_size,
                'warmup_steps': job.config.warmup_steps,
                'use_grpo': job.config.use_grpo,
                'mixed_precision': job.config.mixed_precision,
                'gradient_checkpointing': job.config.gradient_checkpointing,
                'save_steps': job.config.save_steps,
                'eval_steps': job.config.eval_steps
            }
            
            # 啟動訓練
            result = await self.client.start_training(
                training_data=training_data,
                config=training_config,
                job_id=job.job_id
            )
            
            if result.get('success'):
                # 監控訓練過程
                await self._monitor_training(job, result.get('training_id'))
                return True
            else:
                job.error_message = result.get('error', '訓練啟動失敗')
                return False
                
        except Exception as e:
            job.error_message = str(e)
            self.logger.error(f"ART 訓練失敗: {str(e)}")
            return False
    
    async def _simulate_training(
        self, 
        job: TrainingJob, 
        training_data: List[Dict[str, Any]]
    ) -> bool:
        """模擬訓練過程"""
        
        try:
            total_steps = job.config.training_steps
            
            for step in range(1, total_steps + 1):
                # 模擬訓練步驟
                await asyncio.sleep(0.01)  # 模擬訓練時間
                
                # 更新進度
                job.current_step = step
                job.progress = step / total_steps
                
                # 模擬損失下降
                job.final_loss = max(0.1, 2.0 * (1 - job.progress))
                
                # 模擬最佳指標
                job.best_metric = min(0.95, job.progress * 1.2)
                
                # 模擬保存檢查點
                if step % job.config.save_steps == 0:
                    self.logger.info(f"模擬保存檢查點: step {step}")
                
                # 模擬早停檢查
                if (job.config.enable_early_stopping and 
                    step > job.config.patience * 10 and 
                    job.best_metric > 0.9):
                    self.logger.info(f"模擬早停: step {step}")
                    break
            
            # 模擬訓練完成
            job.status = TrainingStage.MODEL_EVALUATION
            job.model_path = f"/tmp/models/{job.job_id}/final_model"
            
            return True
            
        except Exception as e:
            job.error_message = str(e)
            self.logger.error(f"模擬訓練失敗: {str(e)}")
            return False
    
    async def _monitor_training(self, job: TrainingJob, training_id: str):
        """監控訓練過程"""
        
        while job.is_active():
            try:
                # 獲取訓練狀態
                status = await self.client.get_training_status(training_id)
                
                # 更新任務狀態
                job.current_step = status.get('current_step', 0)
                job.progress = status.get('progress', 0.0)
                job.final_loss = status.get('current_loss', job.final_loss)
                job.best_metric = status.get('best_metric', job.best_metric)
                
                # 檢查訓練是否完成
                if status.get('status') == 'completed':
                    job.status = TrainingStage.MODEL_EVALUATION
                    job.model_path = status.get('model_path')
                    break
                elif status.get('status') == 'failed':
                    job.status = TrainingStage.FAILED
                    job.error_message = status.get('error', '訓練失敗')
                    break
                
                # 等待下次檢查
                await asyncio.sleep(10)
                
            except Exception as e:
                self.logger.error(f"監控訓練過程失敗: {str(e)}")
                await asyncio.sleep(10)


class TrainingPipeline:
    """訓練管道"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 組件
        self.trajectory_buffer = TrajectoryBuffer(
            max_size=self.config.get('buffer_size', 50000)
        )
        self.preprocessor = DataPreprocessor(self.config.get('preprocessing'))
        self.trainer = ARTTrainer(self.config.get('training'))
        
        # 任務管理
        self.active_jobs: Dict[str, TrainingJob] = {}
        self.job_history: List[TrainingJob] = []
        self.job_queue = queue.Queue()
        
        # 狀態
        self.is_running = False
        self.worker_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """啟動訓練管道"""
        
        if not self.is_running:
            self.is_running = True
            self.worker_task = asyncio.create_task(self._worker_loop())
            self.logger.info("訓練管道已啟動")
    
    async def stop(self):
        """停止訓練管道"""
        
        if self.is_running:
            self.is_running = False
            
            if self.worker_task:
                self.worker_task.cancel()
                try:
                    await self.worker_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("訓練管道已停止")
    
    def submit_training_job(
        self, 
        analyst_id: str, 
        config: TrainingConfig = None
    ) -> str:
        """提交訓練任務"""
        
        if not config:
            config = TrainingConfig(analyst_id=analyst_id)
        
        job_id = str(uuid.uuid4())
        job = TrainingJob(
            job_id=job_id,
            analyst_id=analyst_id,
            config=config
        )
        
        self.job_queue.put(job)
        self.logger.info(f"訓練任務已提交: {job_id}")
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """獲取任務狀態"""
        
        # 檢查活躍任務
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return self._job_to_dict(job)
        
        # 檢查歷史任務
        for job in self.job_history:
            if job.job_id == job_id:
                return self._job_to_dict(job)
        
        return None
    
    def list_jobs(
        self, 
        analyst_id: str = None,
        status: TrainingStage = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """列出任務"""
        
        all_jobs = list(self.active_jobs.values()) + self.job_history
        
        # 過濾
        filtered_jobs = []
        for job in all_jobs:
            if analyst_id and job.analyst_id != analyst_id:
                continue
            if status and job.status != status:
                continue
            
            filtered_jobs.append(job)
        
        # 按創建時間降序排列
        filtered_jobs.sort(key=lambda x: x.created_at, reverse=True)
        
        # 限制數量
        if limit:
            filtered_jobs = filtered_jobs[:limit]
        
        return [self._job_to_dict(job) for job in filtered_jobs]
    
    def add_trajectory(self, trajectory: TrainingTrajectory) -> bool:
        """添加訓練軌跡"""
        return self.trajectory_buffer.add_trajectory(trajectory)
    
    def get_buffer_statistics(self) -> Dict[str, Any]:
        """獲取緩衝區統計"""
        return self.trajectory_buffer.get_statistics()
    
    async def _worker_loop(self):
        """工作循環"""
        
        while self.is_running:
            try:
                # 檢查是否有新任務
                try:
                    job = self.job_queue.get_nowait()
                    await self._process_job(job)
                except queue.Empty:
                    pass
                
                # 清理完成的任務
                await self._cleanup_completed_jobs()
                
                # 等待下次循環
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"工作循環錯誤: {str(e)}")
                await asyncio.sleep(5)
    
    async def _process_job(self, job: TrainingJob):
        """處理訓練任務"""
        
        try:
            self.active_jobs[job.job_id] = job
            self.logger.info(f"開始處理訓練任務: {job.job_id}")
            
            # 階段1: 數據收集
            job.status = TrainingStage.DATA_COLLECTION
            trajectories = self.trajectory_buffer.get_trajectories(
                analyst_id=job.analyst_id,
                min_reward=job.config.min_reward_threshold
            )
            
            if len(trajectories) < job.config.min_trajectory_count:
                job.status = TrainingStage.FAILED
                job.error_message = f"軌跡數量不足: {len(trajectories)} < {job.config.min_trajectory_count}"
                return
            
            job.progress = 0.2
            
            # 階段2: 數據預處理
            job.status = TrainingStage.DATA_PREPROCESSING
            training_data, preprocessing_stats = self.preprocessor.preprocess_trajectories(
                trajectories, job.config
            )
            
            if not training_data:
                job.status = TrainingStage.FAILED
                job.error_message = "數據預處理後無有效數據"
                return
            
            job.progress = 0.4
            self.logger.info(f"預處理完成: {preprocessing_stats}")
            
            # 階段3: 模型訓練
            success = await self.trainer.start_training(job, training_data)
            
            if not success:
                job.status = TrainingStage.FAILED
                return
            
            # 訓練完成後的處理
            if job.status == TrainingStage.MODEL_EVALUATION:
                await self._evaluate_model(job)
                
                if job.status != TrainingStage.FAILED:
                    job.status = TrainingStage.COMPLETED
                    job.completed_at = datetime.now()
                    job.progress = 1.0
                    
                    self.logger.info(f"訓練任務完成: {job.job_id}")
        
        except Exception as e:
            job.status = TrainingStage.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            self.logger.error(f"訓練任務失敗 {job.job_id}: {str(e)}")
    
    async def _evaluate_model(self, job: TrainingJob):
        """評估模型"""
        
        try:
            # 簡單的模型評估
            # 在實際實現中，這裡應該包含更詳細的評估邏輯
            
            if job.best_metric > 0.7:
                self.logger.info(f"模型評估通過: {job.job_id} (指標: {job.best_metric})")
            else:
                job.status = TrainingStage.FAILED
                job.error_message = f"模型性能不佳: {job.best_metric}"
                
        except Exception as e:
            job.status = TrainingStage.FAILED
            job.error_message = f"模型評估失敗: {str(e)}"
    
    async def _cleanup_completed_jobs(self):
        """清理完成的任務"""
        
        completed_jobs = []
        
        for job_id, job in list(self.active_jobs.items()):
            if not job.is_active():
                completed_jobs.append(job)
                del self.active_jobs[job_id]
        
        # 移動到歷史記錄
        self.job_history.extend(completed_jobs)
        
        # 限制歷史記錄數量
        if len(self.job_history) > 1000:
            self.job_history = self.job_history[-500:]
    
    def _job_to_dict(self, job: TrainingJob) -> Dict[str, Any]:
        """將任務轉換為字典"""
        
        result = {
            'job_id': job.job_id,
            'analyst_id': job.analyst_id,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'current_step': job.current_step,
            'total_steps': job.total_steps,
            'best_metric': job.best_metric,
            'final_loss': job.final_loss,
            'model_path': job.model_path,
            'error_message': job.error_message,
            'training_time': job.training_time,
            'duration_seconds': job.get_duration().total_seconds() if job.get_duration() else None
        }
        
        return result


# 全局管道實例
_global_pipeline: Optional[TrainingPipeline] = None


def get_training_pipeline() -> TrainingPipeline:
    """獲取全局訓練管道"""
    global _global_pipeline
    
    if _global_pipeline is None:
        _global_pipeline = TrainingPipeline()
    
    return _global_pipeline



# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_training_pipeline():
        print("測試訓練管道")
        
        pipeline = get_training_pipeline()
        await pipeline.start()
        
        # 創建測試軌跡
        trajectory = TrainingTrajectory(
            trajectory_id="test_trajectory_1",
            analyst_id="test_analyst",
            timestamp=datetime.now(),
            analysis_state=None,  # 簡化測試
            prompt="分析股票2330的投資價值",
            context={'stock_id': '2330'},
            analysis_result=None,  # 簡化測試
            model_response={'recommendation': 'BUY', 'confidence': 0.8},
            reward_score=0.75
        )
        
        # 添加軌跡
        pipeline.add_trajectory(trajectory)
        
        # 獲取統計信息
        stats = pipeline.get_buffer_statistics()
        print(f"軌跡緩衝區統計: {stats}")
        
        # 提交訓練任務
        job_id = pipeline.submit_training_job("test_analyst")
        print(f"提交訓練任務: {job_id}")
        
        # 監控任務狀態
        for i in range(10):
            await asyncio.sleep(1)
            status = pipeline.get_job_status(job_id)
            if status:
                print(f"任務狀態: {status['status']} (進度: {status['progress']:.1%})")
                if status['status'] in ['completed', 'failed']:
                    break
        
        await pipeline.stop()
        print("✅ 測試完成")
    
    asyncio.run(test_training_pipeline())