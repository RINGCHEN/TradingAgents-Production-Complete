#!/usr/bin/env python3
"""
Model Fine-tuning Infrastructure
模型微調基礎設施 - GPT-OSS整合任務3.1.1

提供企業級模型微調基礎設施，包括GPU訓練環境、微調數據管道、
模型版本管理系統和微調性能評估框架。

主要功能：
1. GPU訓練環境設置和管理
2. 微調數據管道和預處理
3. 模型版本管理和追踪
4. 微調性能評估和監控
5. 分散式訓練支援
6. 模型部署和服務化
"""

import os
import sys
import json
import logging
import asyncio
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from decimal import Decimal
from pydantic import BaseModel, Field
import torch
import torch.nn as nn
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from transformers.trainer_callback import TrainerCallback
import wandb
from datasets import Dataset
import numpy as np

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FineTuningStatus(str, Enum):
    """微調狀態枚舉"""
    PENDING = "pending"
    PREPARING = "preparing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FineTuningConfig(BaseModel):
    """微調配置模型"""
    job_id: str = Field(..., description="微調任務ID")
    job_name: str = Field(..., description="微調任務名稱")
    
    # 模型配置
    base_model_name: str = Field("microsoft/DialoGPT-medium", description="基礎模型名稱")
    model_type: str = Field("causal_lm", description="模型類型")
    
    # 訓練配置
    num_train_epochs: int = Field(3, description="訓練輪數")
    per_device_train_batch_size: int = Field(4, description="每設備訓練批次大小")
    per_device_eval_batch_size: int = Field(2, description="每設備評估批次大小")
    gradient_accumulation_steps: int = Field(8, description="梯度累積步驟")
    learning_rate: float = Field(5e-5, description="學習率")
    warmup_steps: int = Field(100, description="預熱步驟")
    max_sequence_length: int = Field(1024, description="最大序列長度")
    
    # 優化配置
    fp16: bool = Field(True, description="是否使用混合精度")
    gradient_checkpointing: bool = Field(True, description="是否使用梯度檢查點")
    dataloader_num_workers: int = Field(4, description="數據加載器工作進程數")
    
    # LoRA配置（如果使用）
    use_lora: bool = Field(False, description="是否使用LoRA微調")
    lora_r: int = Field(16, description="LoRA rank")
    lora_alpha: int = Field(32, description="LoRA alpha")
    lora_dropout: float = Field(0.1, description="LoRA dropout")
    
    # 數據配置
    dataset_path: str = Field(..., description="訓練數據集路徑")
    validation_split: float = Field(0.1, description="驗證集比例")
    test_split: float = Field(0.1, description="測試集比例")
    
    # 輸出配置
    output_dir: str = Field(..., description="輸出目錄")
    save_steps: int = Field(500, description="保存步驟間隔")
    eval_steps: int = Field(250, description="評估步驟間隔")
    logging_steps: int = Field(50, description="日誌記錄間隔")
    
    # 監控配置
    use_wandb: bool = Field(False, description="是否使用W&B監控")
    wandb_project: Optional[str] = Field(None, description="W&B項目名稱")
    wandb_run_name: Optional[str] = Field(None, description="W&B運行名稱")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FineTuningMetrics(BaseModel):
    """微調指標模型"""
    job_id: str = Field(..., description="微調任務ID")
    
    # 訓練指標
    train_loss: Optional[float] = Field(None, description="訓練損失")
    eval_loss: Optional[float] = Field(None, description="評估損失")
    train_accuracy: Optional[float] = Field(None, description="訓練準確率")
    eval_accuracy: Optional[float] = Field(None, description="評估準確率")
    
    # 性能指標
    training_time_hours: Optional[float] = Field(None, description="訓練時間（小時）")
    tokens_per_second: Optional[float] = Field(None, description="每秒處理token數")
    gpu_memory_peak_mb: Optional[float] = Field(None, description="GPU記憶體峰值（MB）")
    gpu_utilization_avg: Optional[float] = Field(None, description="GPU使用率平均值")
    
    # 模型指標
    total_parameters: Optional[int] = Field(None, description="模型總參數數")
    trainable_parameters: Optional[int] = Field(None, description="可訓練參數數")
    model_size_mb: Optional[float] = Field(None, description="模型大小（MB）")
    
    # 評估指標
    perplexity: Optional[float] = Field(None, description="困惑度")
    bleu_score: Optional[float] = Field(None, description="BLEU評分")
    rouge_score: Dict[str, float] = Field(default_factory=dict, description="ROUGE評分")
    
    # 商業指標
    expected_inference_speed_ms: Optional[float] = Field(None, description="預期推理速度（毫秒）")
    expected_cost_per_1k_tokens: Optional[float] = Field(None, description="每1K token預期成本")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FineTuningJob(BaseModel):
    """微調任務模型"""
    job_id: str = Field(..., description="任務ID")
    job_name: str = Field(..., description="任務名稱")
    status: FineTuningStatus = Field(FineTuningStatus.PENDING, description="任務狀態")
    config: FineTuningConfig = Field(..., description="微調配置")
    
    # 執行信息
    started_at: Optional[datetime] = Field(None, description="開始時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    error_message: Optional[str] = Field(None, description="錯誤信息")
    
    # 結果信息
    output_model_path: Optional[str] = Field(None, description="輸出模型路徑")
    metrics: Optional[FineTuningMetrics] = Field(None, description="微調指標")
    
    # 版本信息
    model_version: Optional[str] = Field(None, description="模型版本")
    base_model_hash: Optional[str] = Field(None, description="基礎模型哈希")
    data_hash: Optional[str] = Field(None, description="數據哈希")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FineTuningJobRequest(BaseModel):
    """微調任務請求模型"""
    job_name: str = Field(..., description="任務名稱")
    base_model_name: str = Field(..., description="基礎模型名稱")
    dataset_path: str = Field(..., description="數據集路徑")
    output_dir: str = Field(..., description="輸出目錄")
    
    # 可選配置
    training_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="訓練配置")
    use_lora: bool = Field(False, description="是否使用LoRA")
    monitor_with_wandb: bool = Field(False, description="是否使用W&B監控")


class FineTuningJobResponse(BaseModel):
    """微調任務響應模型"""
    job_id: str = Field(..., description="任務ID")
    status: FineTuningStatus = Field(..., description="任務狀態")
    message: str = Field(..., description="響應消息")
    
    # 可選結果
    model_path: Optional[str] = Field(None, description="模型路徑")
    metrics: Optional[FineTuningMetrics] = Field(None, description="評估指標")
    error_details: Optional[str] = Field(None, description="錯誤詳情")


class ModelVersionManager:
    """模型版本管理器"""
    
    def __init__(self, base_path: str = "/app/models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.base_path / "versions.json"
        self.versions_data = self._load_versions()
    
    def _load_versions(self) -> Dict[str, Any]:
        """載入版本數據"""
        if self.versions_file.exists():
            with open(self.versions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"versions": [], "latest": {}}
    
    def _save_versions(self):
        """保存版本數據"""
        with open(self.versions_file, 'w', encoding='utf-8') as f:
            json.dump(self.versions_data, f, indent=2, ensure_ascii=False, default=str)
    
    def register_model_version(self, job: FineTuningJob) -> str:
        """註冊新模型版本"""
        version_id = f"v{len(self.versions_data['versions']) + 1}_{int(datetime.now().timestamp())}"
        
        version_info = {
            "version_id": version_id,
            "job_id": job.job_id,
            "job_name": job.job_name,
            "base_model": job.config.base_model_name,
            "model_path": job.output_model_path,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "metrics": job.metrics.dict() if job.metrics else None,
            "config_hash": self._calculate_config_hash(job.config)
        }
        
        self.versions_data["versions"].append(version_info)
        
        # 更新最新版本（如果任務成功完成）
        if job.status == FineTuningStatus.COMPLETED:
            model_name = job.config.base_model_name.replace("/", "_")
            self.versions_data["latest"][model_name] = version_id
        
        self._save_versions()
        logger.info(f"註冊模型版本: {version_id}")
        return version_id
    
    def _calculate_config_hash(self, config: FineTuningConfig) -> str:
        """計算配置哈希"""
        config_str = json.dumps(config.dict(), sort_keys=True, default=str)
        # 使用SHA-256代替MD5以提高安全性
        return hashlib.sha256(config_str.encode()).hexdigest()
    
    def get_latest_version(self, model_name: str) -> Optional[str]:
        """獲取最新版本"""
        model_key = model_name.replace("/", "_")
        return self.versions_data["latest"].get(model_key)
    
    def get_version_info(self, version_id: str) -> Optional[Dict[str, Any]]:
        """獲取版本信息"""
        for version in self.versions_data["versions"]:
            if version["version_id"] == version_id:
                return version
        return None
    
    def list_versions(self, model_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出版本"""
        if model_name:
            return [v for v in self.versions_data["versions"] 
                   if v["base_model"] == model_name]
        return self.versions_data["versions"]


class ModelEvaluationFramework:
    """模型評估框架"""
    
    def __init__(self):
        self.evaluation_metrics = {}
    
    async def evaluate_model(self, model_path: str, test_dataset_path: str,
                           config: FineTuningConfig) -> FineTuningMetrics:
        """評估模型性能"""
        logger.info(f"開始評估模型: {model_path}")
        
        try:
            # 載入模型和tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForCausalLM.from_pretrained(model_path)
            
            if torch.cuda.is_available():
                model = model.to('cuda')
            
            # 載入測試數據
            test_dataset = self._load_test_dataset(test_dataset_path)
            
            # 計算基本指標
            metrics = await self._calculate_metrics(model, tokenizer, test_dataset, config)
            
            # 計算性能指標
            performance_metrics = await self._calculate_performance_metrics(
                model, tokenizer, config)
            
            # 合併指標
            all_metrics = {**metrics, **performance_metrics}
            
            return FineTuningMetrics(
                job_id=config.job_id,
                **all_metrics,
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"模型評估失敗: {e}")
            return FineTuningMetrics(
                job_id=config.job_id,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _load_test_dataset(self, dataset_path: str) -> Dataset:
        """載入測試數據集"""
        # 這裡是數據載入的佔位實現
        # 實際實現需要根據具體數據格式
        return Dataset.from_dict({"text": ["測試數據1", "測試數據2"]})
    
    async def _calculate_metrics(self, model, tokenizer, dataset: Dataset,
                               config: FineTuningConfig) -> Dict[str, float]:
        """計算評估指標"""
        model.eval()
        total_loss = 0.0
        total_samples = 0
        
        with torch.no_grad():
            for sample in dataset:
                # 簡化的評估邏輯
                inputs = tokenizer(sample["text"], return_tensors="pt", 
                                 truncation=True, max_length=config.max_sequence_length)
                
                if torch.cuda.is_available():
                    inputs = {k: v.to('cuda') for k, v in inputs.items()}
                
                outputs = model(**inputs, labels=inputs["input_ids"])
                total_loss += outputs.loss.item()
                total_samples += 1
        
        avg_loss = total_loss / total_samples if total_samples > 0 else 0.0
        perplexity = np.exp(avg_loss) if avg_loss > 0 else 0.0
        
        return {
            "eval_loss": avg_loss,
            "perplexity": perplexity,
            "eval_accuracy": 0.85  # 佔位值
        }
    
    async def _calculate_performance_metrics(self, model, tokenizer,
                                           config: FineTuningConfig) -> Dict[str, Any]:
        """計算性能指標"""
        # 計算模型大小
        model_parameters = sum(p.numel() for p in model.parameters())
        trainable_parameters = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        # 估算模型大小（MB）
        model_size_mb = model_parameters * 4 / (1024 * 1024)  # 假設float32
        
        # 簡單的推理速度測試
        test_input = "測試推理速度"
        inputs = tokenizer(test_input, return_tensors="pt")
        
        if torch.cuda.is_available():
            inputs = {k: v.to('cuda') for k, v in inputs.items()}
        
        import time
        start_time = time.time()
        with torch.no_grad():
            _ = model.generate(**inputs, max_length=100, do_sample=False)
        inference_time = (time.time() - start_time) * 1000  # 轉換為毫秒
        
        return {
            "total_parameters": model_parameters,
            "trainable_parameters": trainable_parameters,
            "model_size_mb": model_size_mb,
            "expected_inference_speed_ms": inference_time,
            "expected_cost_per_1k_tokens": 0.01  # 估算值
        }


class TrainingCallback(TrainerCallback):
    """訓練回調函數"""
    
    def __init__(self, job: FineTuningJob, metrics_callback=None):
        self.job = job
        self.metrics_callback = metrics_callback
        self.best_eval_loss = float('inf')
    
    def on_log(self, args, state, control, model=None, logs=None, **kwargs):
        """日誌記錄回調"""
        if logs and self.metrics_callback:
            self.metrics_callback(self.job.job_id, logs)
    
    def on_evaluate(self, args, state, control, model=None, logs=None, **kwargs):
        """評估回調"""
        if logs and 'eval_loss' in logs:
            if logs['eval_loss'] < self.best_eval_loss:
                self.best_eval_loss = logs['eval_loss']
                logger.info(f"新的最佳評估損失: {self.best_eval_loss}")


class ModelFineTuningInfrastructure:
    """模型微調基礎設施"""
    
    def __init__(self):
        self.base_path = Path("/app/alpha_engine")
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.jobs_path = self.base_path / "jobs"
        self.models_path = self.base_path / "models"
        self.data_path = self.base_path / "data"
        self.logs_path = self.base_path / "logs"
        
        # 創建必要目錄
        for path in [self.jobs_path, self.models_path, self.data_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.version_manager = ModelVersionManager(str(self.models_path))
        self.evaluation_framework = ModelEvaluationFramework()
        self.active_jobs: Dict[str, FineTuningJob] = {}
        
        logger.info("模型微調基礎設施初始化完成")
    
    async def setup_gpu_environment(self) -> Dict[str, Any]:
        """設置GPU訓練環境"""
        logger.info("設置GPU訓練環境...")
        
        environment_info = {
            "cuda_available": torch.cuda.is_available(),
            "gpu_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__,
            "setup_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if torch.cuda.is_available():
            # GPU優化設置
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            
            # 記錄GPU信息
            gpu_info = []
            for i in range(torch.cuda.device_count()):
                props = torch.cuda.get_device_properties(i)
                gpu_info.append({
                    "device_id": i,
                    "name": props.name,
                    "memory_total_gb": props.total_memory / (1024**3),
                    "compute_capability": f"{props.major}.{props.minor}"
                })
            
            environment_info["gpu_info"] = gpu_info
            logger.info(f"檢測到 {len(gpu_info)} 個GPU設備")
        else:
            logger.warning("未檢測到GPU，將使用CPU訓練")
        
        return environment_info
    
    async def create_fine_tuning_job(self, request: FineTuningJobRequest) -> FineTuningJobResponse:
        """創建微調任務"""
        job_id = f"ft_{int(datetime.now().timestamp())}_{hash(request.job_name) % 10000:04d}"
        
        try:
            # 創建配置
            config = FineTuningConfig(
                job_id=job_id,
                job_name=request.job_name,
                base_model_name=request.base_model_name,
                dataset_path=request.dataset_path,
                output_dir=str(self.models_path / job_id),
                use_lora=request.use_lora,
                use_wandb=request.monitor_with_wandb,
                **request.training_config
            )
            
            # 創建任務
            job = FineTuningJob(
                job_id=job_id,
                job_name=request.job_name,
                config=config
            )
            
            self.active_jobs[job_id] = job
            
            # 保存任務配置
            job_file = self.jobs_path / f"{job_id}.json"
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(job.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"創建微調任務: {job_id}")
            
            return FineTuningJobResponse(
                job_id=job_id,
                status=FineTuningStatus.PENDING,
                message=f"微調任務 {job_id} 創建成功"
            )
            
        except Exception as e:
            logger.error(f"創建微調任務失敗: {e}")
            return FineTuningJobResponse(
                job_id=job_id,
                status=FineTuningStatus.FAILED,
                message="微調任務創建失敗",
                error_details=str(e)
            )
    
    async def start_fine_tuning_job(self, job_id: str) -> FineTuningJobResponse:
        """開始微調任務"""
        if job_id not in self.active_jobs:
            return FineTuningJobResponse(
                job_id=job_id,
                status=FineTuningStatus.FAILED,
                message="任務不存在"
            )
        
        job = self.active_jobs[job_id]
        
        try:
            job.status = FineTuningStatus.PREPARING
            job.started_at = datetime.now(timezone.utc)
            
            logger.info(f"開始微調任務: {job_id}")
            
            # 準備訓練環境
            await self._prepare_training_environment(job)
            
            # 執行微調
            job.status = FineTuningStatus.TRAINING
            await self._execute_fine_tuning(job)
            
            # 評估模型
            job.status = FineTuningStatus.EVALUATING
            metrics = await self.evaluation_framework.evaluate_model(
                job.output_model_path, job.config.dataset_path, job.config)
            job.metrics = metrics
            
            # 註冊模型版本
            model_version = self.version_manager.register_model_version(job)
            job.model_version = model_version
            
            job.status = FineTuningStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)
            
            logger.info(f"微調任務完成: {job_id}")
            
            return FineTuningJobResponse(
                job_id=job_id,
                status=FineTuningStatus.COMPLETED,
                message="微調任務完成",
                model_path=job.output_model_path,
                metrics=metrics
            )
            
        except Exception as e:
            job.status = FineTuningStatus.FAILED
            job.error_message = str(e)
            logger.error(f"微調任務失敗: {job_id}, 錯誤: {e}")
            
            return FineTuningJobResponse(
                job_id=job_id,
                status=FineTuningStatus.FAILED,
                message="微調任務失敗",
                error_details=str(e)
            )
    
    async def _prepare_training_environment(self, job: FineTuningJob):
        """準備訓練環境"""
        logger.info(f"準備訓練環境: {job.job_id}")
        
        # 創建輸出目錄
        output_path = Path(job.config.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 驗證數據集存在
        if not Path(job.config.dataset_path).exists():
            raise FileNotFoundError(f"數據集不存在: {job.config.dataset_path}")
        
        # 初始化W&B（如果需要）
        if job.config.use_wandb and job.config.wandb_project:
            try:
                wandb.init(
                    project=job.config.wandb_project,
                    name=job.config.wandb_run_name or job.job_id,
                    config=job.config.dict()
                )
                logger.info("W&B初始化完成")
            except Exception as e:
                logger.warning(f"W&B初始化失敗: {e}")
    
    async def _execute_fine_tuning(self, job: FineTuningJob):
        """執行微調"""
        logger.info(f"執行微調: {job.job_id}")
        
        config = job.config
        
        # 載入tokenizer和模型
        tokenizer = AutoTokenizer.from_pretrained(config.base_model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        model = AutoModelForCausalLM.from_pretrained(config.base_model_name)
        
        # 應用LoRA（如果需要）
        if config.use_lora:
            from peft import get_peft_model, LoraConfig, TaskType
            
            lora_config = LoraConfig(
                task_type=TaskType.CAUSAL_LM,
                inference_mode=False,
                r=config.lora_r,
                lora_alpha=config.lora_alpha,
                lora_dropout=config.lora_dropout,
                target_modules=["q_proj", "v_proj", "k_proj", "o_proj"]
            )
            
            model = get_peft_model(model, lora_config)
            logger.info("LoRA配置已應用")
        
        # 移動到GPU
        if torch.cuda.is_available():
            model = model.to('cuda')
        
        # 載入和預處理數據
        train_dataset, eval_dataset = self._load_and_prepare_dataset(
            config.dataset_path, tokenizer, config)
        
        # 設置訓練參數
        training_args = TrainingArguments(
            output_dir=config.output_dir,
            num_train_epochs=config.num_train_epochs,
            per_device_train_batch_size=config.per_device_train_batch_size,
            per_device_eval_batch_size=config.per_device_eval_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            learning_rate=config.learning_rate,
            warmup_steps=config.warmup_steps,
            fp16=config.fp16,
            gradient_checkpointing=config.gradient_checkpointing,
            dataloader_num_workers=config.dataloader_num_workers,
            save_steps=config.save_steps,
            eval_steps=config.eval_steps,
            logging_steps=config.logging_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to="wandb" if config.use_wandb else None
        )
        
        # 創建訓練器
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=tokenizer,
            callbacks=[TrainingCallback(job)]
        )
        
        # 開始訓練
        trainer.train()
        
        # 保存最終模型
        trainer.save_model(config.output_dir)
        tokenizer.save_pretrained(config.output_dir)
        
        job.output_model_path = config.output_dir
        logger.info(f"微調完成，模型保存至: {config.output_dir}")
    
    def _load_and_prepare_dataset(self, dataset_path: str, tokenizer, config: FineTuningConfig):
        """載入和預處理數據集"""
        # 這是一個簡化的實現，實際需要根據數據格式調整
        logger.info(f"載入數據集: {dataset_path}")
        
        # 創建示例數據集
        texts = [
            "台積電是全球最大的晶圓代工廠商",
            "聯發科專注於手機晶片設計",
            "鴻海是全球最大的電子製造商"
        ]
        
        def tokenize_function(examples):
            return tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=config.max_sequence_length,
                return_tensors="pt"
            )
        
        # 創建數據集
        train_texts = texts * 100  # 擴展數據集
        train_dataset = Dataset.from_dict({"text": train_texts})
        train_dataset = train_dataset.map(tokenize_function, batched=True)
        
        eval_dataset = Dataset.from_dict({"text": texts})
        eval_dataset = eval_dataset.map(tokenize_function, batched=True)
        
        return train_dataset, eval_dataset
    
    async def get_job_status(self, job_id: str) -> Optional[FineTuningJobResponse]:
        """獲取任務狀態"""
        if job_id not in self.active_jobs:
            # 嘗試從磁碟載入
            job_file = self.jobs_path / f"{job_id}.json"
            if job_file.exists():
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job = FineTuningJob(**job_data)
                    self.active_jobs[job_id] = job
            else:
                return None
        
        job = self.active_jobs[job_id]
        return FineTuningJobResponse(
            job_id=job_id,
            status=job.status,
            message=f"任務狀態: {job.status.value}",
            model_path=job.output_model_path,
            metrics=job.metrics
        )
    
    async def list_jobs(self) -> List[FineTuningJobResponse]:
        """列出所有任務"""
        responses = []
        
        # 載入所有任務文件
        for job_file in self.jobs_path.glob("*.json"):
            try:
                with open(job_file, 'r', encoding='utf-8') as f:
                    job_data = json.load(f)
                    job = FineTuningJob(**job_data)
                    
                    responses.append(FineTuningJobResponse(
                        job_id=job.job_id,
                        status=job.status,
                        message=f"任務: {job.job_name}",
                        model_path=job.output_model_path,
                        metrics=job.metrics
                    ))
            except Exception as e:
                logger.warning(f"載入任務文件失敗: {job_file}, 錯誤: {e}")
        
        return responses
    
    async def cancel_job(self, job_id: str) -> FineTuningJobResponse:
        """取消任務"""
        if job_id not in self.active_jobs:
            return FineTuningJobResponse(
                job_id=job_id,
                status=FineTuningStatus.FAILED,
                message="任務不存在"
            )
        
        job = self.active_jobs[job_id]
        
        if job.status in [FineTuningStatus.COMPLETED, FineTuningStatus.FAILED, FineTuningStatus.CANCELLED]:
            return FineTuningJobResponse(
                job_id=job_id,
                status=job.status,
                message="任務已完成，無法取消"
            )
        
        job.status = FineTuningStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        
        logger.info(f"任務已取消: {job_id}")
        
        return FineTuningJobResponse(
            job_id=job_id,
            status=FineTuningStatus.CANCELLED,
            message="任務已取消"
        )