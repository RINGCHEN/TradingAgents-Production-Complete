"""
PPO (Proximal Policy Optimization) Trainer
標準PPO算法實現，專為金融分析模型優化

核心功能：
- 標準PPO算法實現
- Clipped Surrogate Objective
- GAE (Generalized Advantage Estimation)
- 經驗重播緩衝區
- RTX 4070 記憶體優化
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
from collections import deque
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    Trainer
)
from trl import AutoModelForCausalLMWithValueHead, PPOConfig, PPOTrainer as HFPPOTrainer
from .reward_models import FinancialRewardModel
from .training_config import PPOConfig as CustomPPOConfig
from ..utils.gpu_optimizer import GPUMemoryOptimizer

logger = logging.getLogger(__name__)


@dataclass
class PPOBatch:
    """PPO訓練批次數據結構"""
    queries: List[str]
    responses: List[str]
    rewards: torch.Tensor
    advantages: torch.Tensor
    returns: torch.Tensor
    old_log_probs: torch.Tensor
    old_values: torch.Tensor
    attention_masks: torch.Tensor


class ExperienceBuffer:
    """經驗重播緩衝區"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.buffer = deque(maxlen=max_size)
    
    def add(self, experience: Dict[str, Any]):
        """添加經驗到緩衝區"""
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Dict[str, Any]]:
        """從緩衝區採樣"""
        if len(self.buffer) < batch_size:
            return list(self.buffer)
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]
    
    def clear(self):
        """清空緩衝區"""
        self.buffer.clear()
    
    def __len__(self):
        return len(self.buffer)


class PPOTrainer:
    """
    PPO (Proximal Policy Optimization) 訓練器
    
    實現標準PPO算法，包含：
    - Clipped Surrogate Objective
    - 價值函數學習
    - GAE優勢估計
    - 經驗重播
    - 熵正則化
    """
    
    def __init__(
        self,
        config: CustomPPOConfig,
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
        
        # 設置優化器
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=config.learning_rate,
            weight_decay=config.weight_decay
        )
        
        # 學習率調度器
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            self.optimizer,
            T_max=config.max_steps,
            eta_min=config.learning_rate * 0.1
        )
        
        # 經驗緩衝區
        self.experience_buffer = ExperienceBuffer(config.buffer_size)
        
        # 訓練狀態
        self.training_stats = {
            'total_steps': 0,
            'total_episodes': 0,
            'average_reward': 0.0,
            'average_advantage': 0.0,
            'policy_loss': 0.0,
            'value_loss': 0.0,
            'entropy_loss': 0.0,
            'kl_divergence': 0.0,
            'clipfrac': 0.0
        }
        
        logger.info(f"PPO Trainer initialized with model: {model_name}")
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
    ) -> PPOBatch:
        """
        準備PPO訓練數據
        
        Args:
            queries: 輸入查詢列表
            responses: 對應回應列表  
            financial_context: 金融上下文信息
            
        Returns:
            PPOBatch: 準備好的訓練批次
        """
        # 編碼輸入
        encoded_inputs = []
        attention_masks = []
        
        for query, response in zip(queries, responses):
            # 組合查詢和回應
            full_text = f"{query} {self.tokenizer.eos_token} {response}"
            
            # 編碼
            encoded = self.tokenizer(
                full_text,
                return_tensors="pt",
                max_length=self.config.max_length,
                truncation=True,
                padding="max_length"
            )
            
            encoded_inputs.append(encoded['input_ids'].squeeze(0))
            attention_masks.append(encoded['attention_mask'].squeeze(0))
        
        # 轉換為張量
        input_ids = torch.stack(encoded_inputs).to(self.device)
        attention_masks = torch.stack(attention_masks).to(self.device)
        
        # 計算獎勵
        rewards = self.reward_model.compute_rewards(
            queries, 
            responses, 
            financial_context
        )
        
        # 獲取舊的log概率和價值
        with torch.no_grad():
            outputs = self.model(input_ids, attention_mask=attention_masks)
            logits = outputs.logits
            values = outputs.value.squeeze(-1)
            
            # 計算log概率
            log_probs = F.log_softmax(logits, dim=-1)
            
            # 獲取每個token的log概率
            old_log_probs = log_probs.gather(2, input_ids.unsqueeze(-1)).squeeze(-1)
            
            # 只考慮非padding token
            old_log_probs = old_log_probs * attention_masks
            old_log_probs = old_log_probs.sum(dim=1)  # 每個序列的總log概率
        
        # 計算returns和advantages
        returns, advantages = self._compute_gae(rewards, values, attention_masks)
        
        return PPOBatch(
            queries=queries,
            responses=responses,
            rewards=rewards,
            advantages=advantages,
            returns=returns,
            old_log_probs=old_log_probs,
            old_values=values,
            attention_masks=attention_masks
        )
    
    def _compute_gae(
        self, 
        rewards: torch.Tensor, 
        values: torch.Tensor,
        attention_masks: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        計算GAE (Generalized Advantage Estimation)
        
        Args:
            rewards: 獎勵張量 [batch_size]
            values: 價值張量 [batch_size, seq_len]
            attention_masks: 注意力掩碼 [batch_size, seq_len]
            
        Returns:
            returns: 回報張量
            advantages: 優勢張量
        """
        batch_size, seq_len = values.shape
        
        # 獲取每個序列的最後一個有效值
        last_values = []
        for i in range(batch_size):
            last_valid_idx = attention_masks[i].sum().item() - 1
            last_values.append(values[i, last_valid_idx])
        
        last_values = torch.stack(last_values)
        
        # 計算returns (使用序列最後的價值作為bootstrap)
        returns = rewards + self.config.gamma * last_values
        
        # 計算advantages
        advantages = returns - last_values
        
        # 標準化advantages
        if len(advantages) > 1:
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        
        return returns, advantages
    
    def _compute_ppo_loss(
        self, 
        input_ids: torch.Tensor,
        attention_masks: torch.Tensor,
        old_log_probs: torch.Tensor,
        old_values: torch.Tensor,
        advantages: torch.Tensor,
        returns: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        計算PPO損失函數
        
        包含：
        1. Clipped Surrogate Objective (策略損失)
        2. 價值函數損失
        3. 熵正則化損失
        """
        # 前向傳播
        outputs = self.model(input_ids, attention_mask=attention_masks)
        logits = outputs.logits
        values = outputs.value.squeeze(-1)
        
        # 計算當前log概率
        log_probs = F.log_softmax(logits, dim=-1)
        current_log_probs = log_probs.gather(2, input_ids.unsqueeze(-1)).squeeze(-1)
        current_log_probs = current_log_probs * attention_masks
        current_log_probs = current_log_probs.sum(dim=1)
        
        # 獲取每個序列的最後一個有效值
        batch_size, seq_len = values.shape
        current_values = []
        for i in range(batch_size):
            last_valid_idx = attention_masks[i].sum().item() - 1
            current_values.append(values[i, last_valid_idx])
        current_values = torch.stack(current_values)
        
        # 計算比率
        ratio = torch.exp(current_log_probs - old_log_probs)
        
        # PPO Clipped Surrogate Objective
        surr1 = ratio * advantages
        surr2 = torch.clamp(ratio, 1 - self.config.cliprange, 1 + self.config.cliprange) * advantages
        policy_loss = -torch.min(surr1, surr2).mean()
        
        # 價值函數損失
        if self.config.clip_value_loss:
            # 裁剪價值損失
            value_pred_clipped = old_values + torch.clamp(
                current_values - old_values,
                -self.config.cliprange_value,
                self.config.cliprange_value
            )
            value_loss1 = F.mse_loss(current_values, returns)
            value_loss2 = F.mse_loss(value_pred_clipped, returns)
            value_loss = torch.max(value_loss1, value_loss2)
        else:
            value_loss = F.mse_loss(current_values, returns)
        
        # 熵損失
        entropy = -(log_probs * torch.exp(log_probs)).sum(dim=-1)
        entropy = (entropy * attention_masks).sum(dim=1).mean()
        entropy_loss = -self.config.entropy_coef * entropy
        
        # 總損失
        total_loss = policy_loss + self.config.vf_coef * value_loss + entropy_loss
        
        # 計算統計信息
        with torch.no_grad():
            # KL散度
            kl_div = (old_log_probs - current_log_probs).mean()
            
            # 裁剪比例
            clipfrac = ((ratio - 1.0).abs() > self.config.cliprange).float().mean()
        
        return {
            'total_loss': total_loss,
            'policy_loss': policy_loss,
            'value_loss': value_loss,
            'entropy_loss': entropy_loss,
            'kl_divergence': kl_div,
            'clipfrac': clipfrac
        }
    
    def train_step(self, batch: PPOBatch) -> Dict[str, float]:
        """
        執行一步PPO訓練
        
        Args:
            batch: 訓練批次數據
            
        Returns:
            訓練統計信息
        """
        self.model.train()
        
        # 編碼輸入
        encoded_inputs = []
        attention_masks = []
        
        for query, response in zip(batch.queries, batch.responses):
            full_text = f"{query} {self.tokenizer.eos_token} {response}"
            encoded = self.tokenizer(
                full_text,
                return_tensors="pt",
                max_length=self.config.max_length,
                truncation=True,
                padding="max_length"
            )
            encoded_inputs.append(encoded['input_ids'].squeeze(0))
            attention_masks.append(encoded['attention_mask'].squeeze(0))
        
        input_ids = torch.stack(encoded_inputs).to(self.device)
        attention_masks = torch.stack(attention_masks).to(self.device)
        
        # 多次PPO更新
        total_stats = {}
        for epoch in range(self.config.ppo_epochs):
            # 計算損失
            losses = self._compute_ppo_loss(
                input_ids,
                attention_masks,
                batch.old_log_probs,
                batch.old_values,
                batch.advantages,
                batch.returns
            )
            
            # 反向傳播
            self.optimizer.zero_grad()
            losses['total_loss'].backward()
            
            # 梯度裁剪
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
            
            # 優化器步驟
            self.optimizer.step()
            
            # 累積統計信息
            for key, value in losses.items():
                if key not in total_stats:
                    total_stats[key] = 0.0
                total_stats[key] += value.item()
        
        # 計算平均值
        for key in total_stats:
            total_stats[key] /= self.config.ppo_epochs
        
        # 學習率調度
        self.scheduler.step()
        
        # 更新訓練統計
        self.training_stats['total_steps'] += 1
        self.training_stats['policy_loss'] = total_stats['policy_loss']
        self.training_stats['value_loss'] = total_stats['value_loss']
        self.training_stats['entropy_loss'] = total_stats['entropy_loss']
        self.training_stats['kl_divergence'] = total_stats['kl_divergence']
        self.training_stats['clipfrac'] = total_stats['clipfrac']
        self.training_stats['average_reward'] = batch.rewards.mean().item()
        self.training_stats['average_advantage'] = batch.advantages.mean().item()
        
        return total_stats
    
    def collect_experience(
        self, 
        queries: List[str], 
        financial_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        """
        收集經驗數據（生成回應）
        
        Args:
            queries: 輸入查詢列表
            financial_contexts: 金融上下文
            
        Returns:
            生成的回應列表
        """
        self.model.eval()
        responses = []
        
        with torch.no_grad():
            for i, query in enumerate(queries):
                # 編碼查詢
                inputs = self.tokenizer(
                    query,
                    return_tensors="pt",
                    max_length=self.config.max_query_length,
                    truncation=True
                ).to(self.device)
                
                # 生成回應
                outputs = self.model.generate(
                    **inputs,
                    max_length=self.config.max_length,
                    num_return_sequences=1,
                    temperature=self.config.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
                
                # 解碼回應
                response = self.tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:],
                    skip_special_tokens=True
                ).strip()
                
                responses.append(response)
                
                # 添加到經驗緩衝區
                experience = {
                    'query': query,
                    'response': response,
                    'context': financial_contexts[i] if financial_contexts else None,
                    'timestamp': datetime.now().isoformat()
                }
                self.experience_buffer.add(experience)
        
        return responses
    
    def train_epoch(
        self, 
        training_queries: List[str],
        financial_contexts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, float]:
        """
        訓練一個epoch
        
        Args:
            training_queries: 訓練查詢列表
            financial_contexts: 對應的金融上下文
            
        Returns:
            epoch統計信息
        """
        epoch_stats = {
            'total_loss': 0.0,
            'policy_loss': 0.0,
            'value_loss': 0.0,
            'entropy_loss': 0.0,
            'kl_divergence': 0.0,
            'clipfrac': 0.0,
            'num_batches': 0
        }
        
        # 收集經驗
        responses = self.collect_experience(training_queries, financial_contexts)
        
        # 分批訓練
        for i in range(0, len(training_queries), self.config.batch_size):
            batch_queries = training_queries[i:i + self.config.batch_size]
            batch_responses = responses[i:i + self.config.batch_size]
            batch_contexts = financial_contexts[i:i + self.config.batch_size] if financial_contexts else None
            
            # 準備批次數據
            batch = self.prepare_training_data(batch_queries, batch_responses, batch_contexts)
            
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
        
        # 保存優化器狀態
        torch.save({
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
        }, os.path.join(checkpoint_path, "optimizer.pt"))
        
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
        
        # 載入優化器狀態
        optimizer_path = os.path.join(checkpoint_path, "optimizer.pt")
        if os.path.exists(optimizer_path):
            checkpoint = torch.load(optimizer_path)
            self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        
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
            'config': self.config.__dict__,
            'experience_buffer_size': len(self.experience_buffer)
        }