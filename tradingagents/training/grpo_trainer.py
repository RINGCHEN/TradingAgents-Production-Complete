"""
GRPO (Group Relative Policy Optimization) Trainer
專為金融分析模型設計的強化學習訓練器

核心功能：
- 群組相對策略優化算法實現
- 金融專業化獎勵函數
- RTX 4070 記憶體優化
- 多GPU分散式訓練支援
- 實時訓練監控和檢查點管理
"""

import os
import json
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer
)
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer
from .reward_models import FinancialRewardModel
from .training_config import GRPOConfig
from ..utils.gpu_optimizer import GPUMemoryOptimizer

logger = logging.getLogger(__name__)


@dataclass
class GRPOBatch:
    """GRPO訓練批次數據結構"""
    queries: List[str]
    responses: List[str]
    rewards: torch.Tensor
    advantages: torch.Tensor
    old_log_probs: torch.Tensor
    values: torch.Tensor


class GRPOTrainer:
    """
    GRPO (Group Relative Policy Optimization) 訓練器
    
    GRPO是一種改進的PPO算法，特別適用於金融分析任務：
    - 群組相對比較：比較同組內不同回應的相對品質
    - 穩定性優化：減少訓練過程中的策略崩潰
    - 金融專業化：整合領域知識和風險評估
    """
    
    def __init__(
        self,
        config: GRPOConfig,
        model_name: str = "microsoft/DialoGPT-medium",
        reward_model: Optional[FinancialRewardModel] = None,
        device: str = "auto"
    ):
        self.config = config
        self.model_name = model_name
        self.device = self._setup_device(device)
        self.gpu_optimizer = GPUMemoryOptimizer()
        
        # 初始化模型和tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # 載入帶有價值頭的模型
        self.model = AutoModelForCausalLMWithValueHead.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
            device_map="auto" if device == "auto" else None
        )
        
        if device != "auto":
            self.model = self.model.to(self.device)
            
        # 初始化獎勵模型
        self.reward_model = reward_model or FinancialRewardModel()
        
        # 設置PPO配置（GRPO基於PPO）
        self.ppo_config = PPOConfig(
            model_name=model_name,
            learning_rate=config.learning_rate,
            batch_size=config.batch_size,
            mini_batch_size=config.mini_batch_size,
            gradient_accumulation_steps=config.gradient_accumulation_steps,
            ppo_epochs=config.ppo_epochs,
            max_grad_norm=config.max_grad_norm,
            cliprange=config.cliprange,
            cliprange_value=config.cliprange_value,
            vf_coef=config.vf_coef,
            use_score_scaling=config.use_score_scaling,
            use_score_norm=config.use_score_norm,
            score_clip=config.score_clip
        )
        
        # 初始化PPO訓練器
        self.ppo_trainer = PPOTrainer(
            config=self.ppo_config,
            model=self.model,
            tokenizer=self.tokenizer
        )
        
        # 訓練狀態
        self.training_stats = {
            'total_steps': 0,
            'total_episodes': 0,
            'average_reward': 0.0,
            'average_advantage': 0.0,
            'policy_loss': 0.0,
            'value_loss': 0.0,
            'entropy_loss': 0.0
        }
        
        logger.info(f"GRPO Trainer initialized with model: {model_name}")
        logger.info(f"Device: {self.device}, FP16: {config.fp16}")
        
    def _setup_device(self, device: str) -> torch.device:
        """設置訓練設備"""
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
                # RTX 4070 優化
                if "4070" in torch.cuda.get_device_name(0):
                    torch.cuda.set_per_process_memory_fraction(0.90)
                    logger.info("RTX 4070 memory optimization applied")
            else:
                device = "cpu"
                logger.warning("CUDA not available, using CPU")
        
        return torch.device(device)
    
    def prepare_training_data(
        self, 
        queries: List[str], 
        responses: List[str],
        financial_context: Optional[Dict[str, Any]] = None
    ) -> GRPOBatch:
        """
        準備GRPO訓練數據
        
        Args:
            queries: 輸入查詢列表
            responses: 對應回應列表  
            financial_context: 金融上下文信息
            
        Returns:
            GRPOBatch: 準備好的訓練批次
        """
        # 編碼輸入
        query_tensors = []
        response_tensors = []
        
        for query, response in zip(queries, responses):
            # 編碼查詢
            query_encoded = self.tokenizer.encode(
                query, 
                return_tensors="pt",
                max_length=self.config.max_query_length,
                truncation=True,
                padding=False
            ).squeeze(0)
            
            # 編碼回應
            response_encoded = self.tokenizer.encode(
                response,
                return_tensors="pt", 
                max_length=self.config.max_response_length,
                truncation=True,
                padding=False
            ).squeeze(0)
            
            query_tensors.append(query_encoded)
            response_tensors.append(response_encoded)
        
        # 計算獎勵
        rewards = self.reward_model.compute_rewards(
            queries, 
            responses, 
            financial_context
        )
        
        # 計算優勢和價值
        with torch.no_grad():
            # 獲取舊的log概率和價值
            old_log_probs = []
            values = []
            
            for query_tensor, response_tensor in zip(query_tensors, response_tensors):
                # 組合輸入
                input_ids = torch.cat([query_tensor, response_tensor], dim=0).unsqueeze(0)
                input_ids = input_ids.to(self.device)
                
                # 前向傳播
                outputs = self.model(input_ids)
                logits = outputs.logits
                value = outputs.value
                
                # 計算log概率
                log_probs = F.log_softmax(logits, dim=-1)
                response_log_probs = log_probs[0, len(query_tensor):len(query_tensor)+len(response_tensor)]
                response_log_prob = response_log_probs.gather(1, response_tensor.unsqueeze(1).to(self.device)).squeeze(1)
                
                old_log_probs.append(response_log_prob.sum().cpu())
                values.append(value[0, -1].cpu())
        
        old_log_probs = torch.stack(old_log_probs)
        values = torch.stack(values)
        
        # 計算優勢（使用GAE）
        advantages = self._compute_gae_advantages(rewards, values)
        
        return GRPOBatch(
            queries=queries,
            responses=responses,
            rewards=rewards,
            advantages=advantages,
            old_log_probs=old_log_probs,
            values=values
        )
    
    def _compute_gae_advantages(
        self, 
        rewards: torch.Tensor, 
        values: torch.Tensor
    ) -> torch.Tensor:
        """
        計算GAE (Generalized Advantage Estimation) 優勢
        
        Args:
            rewards: 獎勵張量
            values: 價值張量
            
        Returns:
            advantages: 優勢張量
        """
        advantages = torch.zeros_like(rewards)
        last_gae_lambda = 0
        
        for t in reversed(range(len(rewards))):
            if t == len(rewards) - 1:
                next_value = 0
            else:
                next_value = values[t + 1]
                
            delta = rewards[t] + self.config.gamma * next_value - values[t]
            advantages[t] = last_gae_lambda = delta + self.config.gamma * self.config.gae_lambda * last_gae_lambda
            
        return advantages
    
    def _compute_grpo_loss(self, batch: GRPOBatch) -> Dict[str, torch.Tensor]:
        """
        計算GRPO損失函數
        
        GRPO相比PPO的改進：
        1. 群組相對比較：在同一批次內比較回應品質
        2. 穩定性正則化：防止策略偏離過遠
        3. 價值函數改進：更準確的價值估計
        """
        # 重新計算當前策略的log概率和價值
        current_log_probs = []
        current_values = []
        
        for query, response in zip(batch.queries, batch.responses):
            # 編碼並前向傳播
            query_encoded = self.tokenizer.encode(query, return_tensors="pt").to(self.device)
            response_encoded = self.tokenizer.encode(response, return_tensors="pt").to(self.device)
            input_ids = torch.cat([query_encoded, response_encoded], dim=1)
            
            outputs = self.model(input_ids)
            logits = outputs.logits
            value = outputs.value
            
            # 計算response部分的log概率
            response_start = query_encoded.shape[1]
            response_logits = logits[0, response_start-1:response_start+response_encoded.shape[1]-1]
            response_log_probs = F.log_softmax(response_logits, dim=-1)
            
            # 獲取實際token的log概率
            response_log_prob = response_log_probs.gather(1, response_encoded.squeeze(0).unsqueeze(1)).squeeze(1)
            
            current_log_probs.append(response_log_prob.sum())
            current_values.append(value[0, -1])
        
        current_log_probs = torch.stack(current_log_probs)
        current_values = torch.stack(current_values)
        
        # 計算比率
        ratio = torch.exp(current_log_probs - batch.old_log_probs.to(self.device))
        
        # GRPO群組相對優勢
        group_advantages = self._compute_group_relative_advantages(batch.advantages)
        
        # PPO裁剪損失
        surr1 = ratio * group_advantages.to(self.device)
        surr2 = torch.clamp(ratio, 1 - self.config.cliprange, 1 + self.config.cliprange) * group_advantages.to(self.device)
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 價值函數損失
        value_targets = batch.rewards + self.config.gamma * batch.values
        value_loss = F.mse_loss(current_values, value_targets.to(self.device))
        
        # 熵損失（鼓勵探索）
        entropy = -(current_log_probs * torch.exp(current_log_probs)).sum()
        entropy_loss = -self.config.entropy_coef * entropy
        
        # GRPO穩定性正則化
        stability_loss = self._compute_stability_regularization(ratio)
        
        # 總損失
        total_loss = (
            policy_loss + 
            self.config.vf_coef * value_loss + 
            entropy_loss + 
            self.config.stability_coef * stability_loss
        )
        
        return {
            'total_loss': total_loss,
            'policy_loss': policy_loss,
            'value_loss': value_loss,
            'entropy_loss': entropy_loss,
            'stability_loss': stability_loss
        }
    
    def _compute_group_relative_advantages(self, advantages: torch.Tensor) -> torch.Tensor:
        """
        計算群組相對優勢
        
        GRPO的核心創新：在同一批次內進行相對比較
        """
        # 標準化優勢
        normalized_advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        # 群組內排序和相對評分
        sorted_indices = torch.argsort(advantages, descending=True)
        relative_advantages = torch.zeros_like(advantages)
        
        for i, idx in enumerate(sorted_indices):
            # 相對位置評分
            relative_score = (len(advantages) - i - 1) / (len(advantages) - 1)
            relative_advantages[idx] = relative_score
        
        # 結合原始優勢和相對優勢
        group_advantages = (
            self.config.relative_weight * relative_advantages + 
            (1 - self.config.relative_weight) * normalized_advantages
        )
        
        return group_advantages
    
    def _compute_stability_regularization(self, ratio: torch.Tensor) -> torch.Tensor:
        """
        計算穩定性正則化項
        
        防止策略更新過於激進
        """
        # KL散度正則化
        kl_div = torch.log(ratio) - (ratio - 1)
        
        # 限制策略變化幅度
        stability_penalty = torch.clamp(kl_div - self.config.target_kl, min=0) ** 2
        
        return stability_penalty.mean()
    
    def train_step(self, batch: GRPOBatch) -> Dict[str, float]:
        """
        執行一步GRPO訓練
        
        Args:
            batch: 訓練批次數據
            
        Returns:
            訓練統計信息
        """
        self.model.train()
        
        # 計算損失
        losses = self._compute_grpo_loss(batch)
        
        # 反向傳播
        losses['total_loss'].backward()
        
        # 梯度裁剪
        torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
        
        # 優化器步驟
        self.ppo_trainer.optimizer.step()
        self.ppo_trainer.optimizer.zero_grad()
        
        # 更新統計信息
        self.training_stats['total_steps'] += 1
        self.training_stats['policy_loss'] = losses['policy_loss'].item()
        self.training_stats['value_loss'] = losses['value_loss'].item()
        self.training_stats['entropy_loss'] = losses['entropy_loss'].item()
        self.training_stats['average_reward'] = batch.rewards.mean().item()
        self.training_stats['average_advantage'] = batch.advantages.mean().item()
        
        return {
            'total_loss': losses['total_loss'].item(),
            'policy_loss': losses['policy_loss'].item(),
            'value_loss': losses['value_loss'].item(),
            'entropy_loss': losses['entropy_loss'].item(),
            'stability_loss': losses['stability_loss'].item(),
            'average_reward': batch.rewards.mean().item(),
            'average_advantage': batch.advantages.mean().item()
        }
    
    def train_epoch(
        self, 
        training_data: List[Tuple[str, str]], 
        financial_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, float]:
        """
        訓練一個epoch
        
        Args:
            training_data: (query, response) 對的列表
            financial_contexts: 對應的金融上下文
            
        Returns:
            epoch統計信息
        """
        epoch_stats = {
            'total_loss': 0.0,
            'policy_loss': 0.0,
            'value_loss': 0.0,
            'entropy_loss': 0.0,
            'stability_loss': 0.0,
            'num_batches': 0
        }
        
        # 分批處理數據
        for i in range(0, len(training_data), self.config.batch_size):
            batch_data = training_data[i:i + self.config.batch_size]
            batch_contexts = financial_contexts[i:i + self.config.batch_size] if financial_contexts else None
            
            queries = [item[0] for item in batch_data]
            responses = [item[1] for item in batch_data]
            
            # 準備批次數據
            batch = self.prepare_training_data(queries, responses, batch_contexts)
            
            # 執行訓練步驟
            step_stats = self.train_step(batch)
            
            # 累積統計信息
            for key in epoch_stats:
                if key != 'num_batches':
                    epoch_stats[key] += step_stats.get(key, 0.0)
            epoch_stats['num_batches'] += 1
            
            # GPU記憶體管理
            if i % 10 == 0:
                self.gpu_optimizer.cleanup_memory()
        
        # 計算平均值
        for key in epoch_stats:
            if key != 'num_batches':
                epoch_stats[key] /= epoch_stats['num_batches']
        
        self.training_stats['total_episodes'] += 1
        
        return epoch_stats
    
    def save_checkpoint(self, checkpoint_path: str, epoch: int, stats: Dict[str, float]):
        """
        保存訓練檢查點
        
        Args:
            checkpoint_path: 檢查點保存路徑
            epoch: 當前epoch
            stats: 訓練統計信息
        """
        os.makedirs(checkpoint_path, exist_ok=True)
        
        # 保存模型
        self.model.save_pretrained(os.path.join(checkpoint_path, "model"))
        self.tokenizer.save_pretrained(os.path.join(checkpoint_path, "tokenizer"))
        
        # 保存訓練狀態
        checkpoint_data = {
            'epoch': epoch,
            'training_stats': self.training_stats,
            'epoch_stats': stats,
            'config': self.config.__dict__,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(os.path.join(checkpoint_path, "training_state.json"), 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        logger.info(f"Checkpoint saved to {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """
        載入訓練檢查點
        
        Args:
            checkpoint_path: 檢查點路徑
        """
        # 載入模型
        self.model = AutoModelForCausalLMWithValueHead.from_pretrained(
            os.path.join(checkpoint_path, "model")
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            os.path.join(checkpoint_path, "tokenizer")
        )
        
        # 載入訓練狀態
        with open(os.path.join(checkpoint_path, "training_state.json"), 'r') as f:
            checkpoint_data = json.load(f)
        
        self.training_stats = checkpoint_data['training_stats']
        
        logger.info(f"Checkpoint loaded from {checkpoint_path}")
        return checkpoint_data['epoch']
    
    def get_training_stats(self) -> Dict[str, Any]:
        """獲取訓練統計信息"""
        return {
            **self.training_stats,
            'model_name': self.model_name,
            'device': str(self.device),
            'config': self.config.__dict__
        }