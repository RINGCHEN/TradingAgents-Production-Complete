#!/usr/bin/env python3
"""
完整的GRPO/PPO訓練實現
為小k（AI訓練專家團隊）提供的完整GRPO訓練系統

This implementation provides:
- Complete GRPO training loop with financial reward model
- RTX 4070 optimized configuration
- Financial domain-specific reward calculations
- Comprehensive error handling and recovery
- Integration with TradingAgents ecosystem

Author: TradingAgents Team (天工開物) - 支援AI訓練專家團隊
Version: 1.0.0
"""

import os
import sys
import json
import logging
import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import random
from tqdm import tqdm
import warnings

# TRL和Transformers相關導入
from transformers import (
    AutoTokenizer, 
    AutoModelForCausalLM,
    TrainingArguments,
    BitsAndBytesConfig
)
from trl import (
    PPOConfig, 
    PPOTrainer, 
    AutoModelForCausalLMWithValueHead,
    create_reference_model
)
from datasets import Dataset
import wandb

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [GRPO訓練師] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/training/grpo_trainer.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("GRPOTrainer")


@dataclass
class FinancialRewardConfig:
    """金融領域獎勵模型配置"""
    # 分析準確性權重
    accuracy_weight: float = 0.4
    # 風險評估權重
    risk_assessment_weight: float = 0.3
    # 投資建議合理性權重
    recommendation_weight: float = 0.2
    # 語言品質權重
    language_quality_weight: float = 0.1
    
    # 獎勵範圍
    max_reward: float = 1.0
    min_reward: float = -1.0
    
    # 金融關鍵詞獎勵
    financial_keywords_bonus: float = 0.1
    # 風險警告獎勵
    risk_warning_bonus: float = 0.15


@dataclass
class GRPOTrainingConfig:
    """GRPO訓練配置"""
    # 模型配置
    model_name: str = "microsoft/DialoGPT-medium"
    max_length: int = 512
    
    # PPO配置
    learning_rate: float = 1.4e-5
    batch_size: int = 4  # RTX 4070優化
    mini_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    ppo_epochs: int = 4
    max_grad_norm: float = 1.0
    
    # 獎勵模型配置
    kl_penalty: str = "kl"  # 或 "abs", "mse"
    adaptive_kl: bool = True
    target_kl: float = 0.1
    kl_beta: float = 0.1
    
    # 訓練配置
    num_train_epochs: int = 3
    save_freq: int = 100
    eval_freq: int = 50
    log_freq: int = 10
    
    # RTX 4070優化
    use_fp16: bool = True
    gradient_checkpointing: bool = True
    dataloader_num_workers: int = 4
    
    # W&B配置
    use_wandb: bool = True
    wandb_project: str = "tradingagents-grpo"


class FinancialRewardModel:
    """
    金融領域專用獎勵模型
    評估AI生成的金融分析品質
    """
    
    def __init__(self, config: FinancialRewardConfig):
        self.config = config
        
        # 金融關鍵詞庫
        self.financial_keywords = [
            "投資", "風險", "報酬", "股價", "市值", "本益比", "殖利率",
            "技術分析", "基本面分析", "趨勢", "支撐", "壓力", "突破",
            "財報", "營收", "獲利", "現金流", "負債比", "ROE", "ROA",
            "市場", "產業", "景氣", "通膨", "利率", "匯率", "原物料"
        ]
        
        # 風險相關關鍵詞
        self.risk_keywords = [
            "風險", "謹慎", "小心", "注意", "警告", "不確定", "波動",
            "下跌", "虧損", "套牢", "停損", "風控", "分散投資"
        ]
        
        # 負面關鍵詞（降低獎勵）
        self.negative_keywords = [
            "保證", "穩賺", "必漲", "必跌", "內線", "明牌", "飆股"
        ]
        
    def calculate_reward(self, query: str, response: str, context: Optional[Dict] = None) -> float:
        """
        計算金融分析回應的獎勵分數
        
        Args:
            query: 用戶問題
            response: AI回應
            context: 額外上下文信息
        
        Returns:
            獎勵分數 (-1.0 到 1.0)
        """
        try:
            total_score = 0.0
            
            # 1. 分析準確性評分
            accuracy_score = self._evaluate_accuracy(query, response)
            total_score += accuracy_score * self.config.accuracy_weight
            
            # 2. 風險評估評分
            risk_score = self._evaluate_risk_assessment(response)
            total_score += risk_score * self.config.risk_assessment_weight
            
            # 3. 投資建議合理性評分
            recommendation_score = self._evaluate_recommendation(response)
            total_score += recommendation_score * self.config.recommendation_weight
            
            # 4. 語言品質評分
            language_score = self._evaluate_language_quality(response)
            total_score += language_score * self.config.language_quality_weight
            
            # 5. 獎勵調整
            total_score = self._apply_bonus_penalties(response, total_score)
            
            # 限制獎勵範圍
            reward = max(self.config.min_reward, 
                        min(self.config.max_reward, total_score))
            
            return float(reward)
            
        except Exception as e:
            logger.error(f"獎勵計算失敗: {e}")
            return 0.0
    
    def _evaluate_accuracy(self, query: str, response: str) -> float:
        """評估分析準確性"""
        score = 0.5  # 基礎分數
        
        # 檢查是否包含金融關鍵詞
        financial_keyword_count = sum(1 for keyword in self.financial_keywords 
                                    if keyword in response)
        
        # 根據關鍵詞數量給分
        if financial_keyword_count >= 5:
            score += 0.3
        elif financial_keyword_count >= 3:
            score += 0.2
        elif financial_keyword_count >= 1:
            score += 0.1
        
        # 檢查回應長度合理性
        if 100 <= len(response) <= 800:
            score += 0.1
        elif len(response) < 50:
            score -= 0.2
        
        # 檢查是否回答了問題
        if any(q_word in response for q_word in query.split() if len(q_word) > 2):
            score += 0.1
        
        return min(1.0, score)
    
    def _evaluate_risk_assessment(self, response: str) -> float:
        """評估風險評估品質"""
        score = 0.3  # 基礎分數
        
        # 檢查風險相關詞彙
        risk_keyword_count = sum(1 for keyword in self.risk_keywords 
                               if keyword in response)
        
        if risk_keyword_count >= 2:
            score += 0.4
        elif risk_keyword_count >= 1:
            score += 0.2
        
        # 檢查是否有風險警告
        risk_phrases = ["投資有風險", "請謹慎評估", "建議分散投資", "注意風控"]
        if any(phrase in response for phrase in risk_phrases):
            score += self.config.risk_warning_bonus
        
        # 懲罰過於絕對的表述
        absolute_phrases = ["100%", "絕對", "肯定", "保證"]
        if any(phrase in response for phrase in absolute_phrases):
            score -= 0.3
        
        return min(1.0, max(0.0, score))
    
    def _evaluate_recommendation(self, response: str) -> float:
        """評估投資建議合理性"""
        score = 0.4  # 基礎分數
        
        # 檢查是否有具體建議
        recommendation_indicators = ["建議", "推薦", "可考慮", "適合", "不適合"]
        if any(indicator in response for indicator in recommendation_indicators):
            score += 0.2
        
        # 檢查建議的具體性
        specific_terms = ["買進", "賣出", "持有", "觀望", "加碼", "減碼"]
        if any(term in response for term in specific_terms):
            score += 0.2
        
        # 檢查是否有理由支撐
        reasoning_indicators = ["因為", "由於", "基於", "考量", "分析"]
        if any(indicator in response for indicator in reasoning_indicators):
            score += 0.2
        
        return min(1.0, score)
    
    def _evaluate_language_quality(self, response: str) -> float:
        """評估語言品質"""
        score = 0.5  # 基礎分數
        
        # 檢查語句完整性
        if response.count('。') >= 2:  # 至少兩個完整句子
            score += 0.2
        
        # 檢查專業術語使用
        professional_terms = ["投資組合", "資產配置", "市場趨勢", "財務指標"]
        professional_count = sum(1 for term in professional_terms if term in response)
        score += min(0.2, professional_count * 0.1)
        
        # 檢查邏輯連貫性（簡單檢查）
        connectors = ["然而", "因此", "另外", "此外", "綜合來看"]
        if any(connector in response for connector in connectors):
            score += 0.1
        
        return min(1.0, score)
    
    def _apply_bonus_penalties(self, response: str, base_score: float) -> float:
        """應用獎勵和懲罰"""
        score = base_score
        
        # 金融關鍵詞獎勵
        financial_density = sum(1 for keyword in self.financial_keywords 
                              if keyword in response) / max(1, len(response.split()))
        if financial_density > 0.1:
            score += self.config.financial_keywords_bonus
        
        # 負面關鍵詞懲罰
        negative_count = sum(1 for keyword in self.negative_keywords 
                           if keyword in response)
        score -= negative_count * 0.2
        
        return score


class GRPOTrainer:
    """
    完整的GRPO訓練器實現
    專為TradingAgents金融AI訓練優化
    """
    
    def __init__(self, config: GRPOTrainingConfig, reward_config: FinancialRewardConfig):
        self.config = config
        self.reward_model = FinancialRewardModel(reward_config)
        
        # 設備配置
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.gpu_device_id = 0
        
        # 模型和訓練器
        self.model = None
        self.ref_model = None
        self.tokenizer = None
        self.ppo_trainer = None
        
        # 訓練狀態
        self.current_epoch = 0
        self.global_step = 0
        self.best_reward = float('-inf')
        
        # 統計信息
        self.training_stats = {
            'total_episodes': 0,
            'average_reward': 0.0,
            'average_kl': 0.0,
            'training_loss': 0.0
        }
        
        logger.info("✅ GRPO訓練器初始化完成")
    
    def setup_models(self):
        """設置模型和tokenizer"""
        logger.info(f"🔧 設置模型: {self.config.model_name}")
        
        try:
            # 設置4位量化配置（RTX 4070優化）
            if self.config.use_fp16:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.bfloat16
                )
            else:
                bnb_config = None
            
            # 初始化tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
            
            # 初始化主模型（帶價值頭）
            self.model = AutoModelForCausalLMWithValueHead.from_pretrained(
                self.config.model_name,
                quantization_config=bnb_config,
                device_map="auto",
                torch_dtype=torch.bfloat16 if self.config.use_fp16 else torch.float32,
                low_cpu_mem_usage=True
            )
            
            # 初始化參考模型
            self.ref_model = create_reference_model(self.model)
            
            # 啟用梯度檢查點（節省內存）
            if self.config.gradient_checkpointing:
                self.model.gradient_checkpointing_enable()
            
            logger.info("✅ 模型設置完成")
            
        except Exception as e:
            logger.error(f"❌ 模型設置失敗: {e}")
            raise
    
    def setup_ppo_trainer(self):
        """設置PPO訓練器"""
        logger.info("🎯 設置PPO訓練器...")
        
        try:
            # PPO配置
            ppo_config = PPOConfig(
                model_name=self.config.model_name,
                learning_rate=self.config.learning_rate,
                log_with="wandb" if self.config.use_wandb else None,
                batch_size=self.config.batch_size,
                mini_batch_size=self.config.mini_batch_size,
                gradient_accumulation_steps=self.config.gradient_accumulation_steps,
                optimize_cuda_cache=True,
                early_stopping=True,
                target_kl=self.config.target_kl,
                ppo_epochs=self.config.ppo_epochs,
                seed=42,
                init_kl_coef=self.config.kl_beta,
                adap_kl_ctrl=self.config.adaptive_kl,
            )
            
            # 初始化PPO訓練器
            self.ppo_trainer = PPOTrainer(
                config=ppo_config,
                model=self.model,
                ref_model=self.ref_model,
                tokenizer=self.tokenizer,
            )
            
            logger.info("✅ PPO訓練器設置完成")
            
        except Exception as e:
            logger.error(f"❌ PPO訓練器設置失敗: {e}")
            raise
    
    def prepare_dataset(self, dataset_path: str) -> Dataset:
        """準備訓練數據集"""
        logger.info(f"📊 準備數據集: {dataset_path}")
        
        try:
            # 讀取JSONL數據
            data = []
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line.strip())
                    if 'query' in item:  # GRPO格式
                        data.append({
                            'query': item['query'],
                            'context': item.get('context', ''),
                            'reference': item.get('reference', '')
                        })
                    elif 'instruction' in item:  # 標準格式轉換
                        query = item['instruction']
                        if item.get('input'):
                            query += f" {item['input']}"
                        data.append({
                            'query': query,
                            'context': item.get('input', ''),
                            'reference': item.get('output', '')
                        })
            
            if not data:
                raise ValueError("數據集為空或格式不正確")
            
            # 過濾和清理數據
            filtered_data = []
            for item in data:
                if len(item['query']) > 10 and len(item['query']) < 1000:
                    filtered_data.append(item)
            
            logger.info(f"✅ 數據集準備完成: {len(filtered_data)} 個樣本")
            
            return Dataset.from_list(filtered_data)
            
        except Exception as e:
            logger.error(f"❌ 數據集準備失敗: {e}")
            raise
    
    def generate_response(self, query: str) -> str:
        """生成模型回應"""
        try:
            # 編碼輸入
            inputs = self.tokenizer.encode(query, return_tensors="pt").to(self.device)
            
            # 生成回應
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=self.config.max_length,
                    num_return_sequences=1,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                )
            
            # 解碼回應
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # 移除輸入部分，只保留生成的回應
            if query in response:
                response = response.replace(query, "").strip()
            
            return response
            
        except Exception as e:
            logger.error(f"回應生成失敗: {e}")
            return "抱歉，我無法處理這個問題。"
    
    def train_step(self, batch: Dict[str, Any]) -> Dict[str, float]:
        """執行一步訓練"""
        queries = batch['query']
        contexts = batch.get('context', [''] * len(queries))
        
        # 生成回應
        responses = []
        for query in queries:
            response = self.generate_response(query)
            responses.append(response)
        
        # 計算獎勵
        rewards = []
        for query, response, context in zip(queries, responses, contexts):
            reward = self.reward_model.calculate_reward(query, response, {'context': context})
            rewards.append(reward)
        
        # 轉換為tensor
        reward_tensors = [torch.tensor(reward) for reward in rewards]
        
        # 執行PPO更新
        query_tensors = [self.tokenizer.encode(q, return_tensors="pt")[0] for q in queries]
        response_tensors = [self.tokenizer.encode(r, return_tensors="pt")[0] for r in responses]
        
        try:
            # PPO訓練步驟
            stats = self.ppo_trainer.step(query_tensors, response_tensors, reward_tensors)
            
            # 更新統計信息
            self.training_stats['average_reward'] = np.mean(rewards)
            self.training_stats['average_kl'] = stats.get('objective/kl', 0.0)
            self.training_stats['training_loss'] = stats.get('ppo/loss/total', 0.0)
            
            return {
                'reward': np.mean(rewards),
                'kl_divergence': stats.get('objective/kl', 0.0),
                'loss': stats.get('ppo/loss/total', 0.0)
            }
            
        except Exception as e:
            logger.error(f"PPO更新失敗: {e}")
            return {'reward': 0.0, 'kl_divergence': 0.0, 'loss': float('inf')}
    
    def train(self, dataset_path: str, output_dir: str):
        """執行完整訓練"""
        logger.info("🚀 開始GRPO訓練...")
        
        # 設置模型和訓練器
        self.setup_models()
        self.setup_ppo_trainer()
        
        # 準備數據集
        dataset = self.prepare_dataset(dataset_path)
        
        # 創建輸出目錄
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化W&B
        if self.config.use_wandb:
            try:
                wandb.init(
                    project=self.config.wandb_project,
                    name=f"grpo-training-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    config=self.config.__dict__
                )
            except Exception as e:
                logger.warning(f"W&B初始化失敗: {e}")
        
        # 訓練循環
        total_steps = len(dataset) * self.config.num_train_epochs // self.config.batch_size
        
        logger.info(f"📈 開始訓練: {self.config.num_train_epochs} epochs, {total_steps} steps")
        
        for epoch in range(self.config.num_train_epochs):
            self.current_epoch = epoch
            epoch_rewards = []
            epoch_losses = []
            
            # 隨機打亂數據
            shuffled_indices = list(range(len(dataset)))
            random.shuffle(shuffled_indices)
            
            # 批次訓練
            for i in tqdm(range(0, len(dataset), self.config.batch_size), 
                         desc=f"Epoch {epoch+1}/{self.config.num_train_epochs}"):
                
                # 準備批次數據
                batch_indices = shuffled_indices[i:i+self.config.batch_size]
                batch = {
                    'query': [dataset[idx]['query'] for idx in batch_indices],
                    'context': [dataset[idx].get('context', '') for idx in batch_indices]
                }
                
                # 執行訓練步驟
                step_stats = self.train_step(batch)
                
                epoch_rewards.append(step_stats['reward'])
                epoch_losses.append(step_stats['loss'])
                
                self.global_step += 1
                
                # 記錄日誌
                if self.global_step % self.config.log_freq == 0:
                    avg_reward = np.mean(epoch_rewards[-10:])  # 最近10步平均
                    avg_loss = np.mean(epoch_losses[-10:])
                    
                    logger.info(f"Step {self.global_step}: Reward={avg_reward:.4f}, Loss={avg_loss:.4f}")
                    
                    # W&B記錄
                    if self.config.use_wandb and wandb.run:
                        wandb.log({
                            'reward': avg_reward,
                            'loss': avg_loss,
                            'kl_divergence': step_stats['kl_divergence'],
                            'epoch': epoch,
                            'step': self.global_step
                        })
                
                # 定期保存模型
                if self.global_step % self.config.save_freq == 0:
                    checkpoint_dir = output_path / f"checkpoint-{self.global_step}"
                    self.save_model(str(checkpoint_dir))
                
                # 內存清理
                if self.global_step % 50 == 0:
                    torch.cuda.empty_cache()
            
            # Epoch結束統計
            epoch_avg_reward = np.mean(epoch_rewards)
            epoch_avg_loss = np.mean(epoch_losses)
            
            logger.info(f"✅ Epoch {epoch+1} 完成: "
                       f"平均獎勵={epoch_avg_reward:.4f}, "
                       f"平均損失={epoch_avg_loss:.4f}")
            
            # 保存最佳模型
            if epoch_avg_reward > self.best_reward:
                self.best_reward = epoch_avg_reward
                best_model_path = output_path / "best_model"
                self.save_model(str(best_model_path))
                logger.info(f"💎 新的最佳模型已保存: {best_model_path}")
        
        # 保存最終模型
        final_model_path = output_path / "final_model"
        self.save_model(str(final_model_path))
        
        logger.info("🎉 GRPO訓練完成！")
        
        # 關閉W&B
        if self.config.use_wandb and wandb.run:
            wandb.finish()
    
    def save_model(self, output_dir: str):
        """保存模型"""
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 保存模型和tokenizer
            self.model.save_pretrained(output_dir)
            self.tokenizer.save_pretrained(output_dir)
            
            # 保存訓練配置
            with open(f"{output_dir}/training_config.json", 'w', encoding='utf-8') as f:
                json.dump(self.config.__dict__, f, indent=2, ensure_ascii=False)
            
            # 保存訓練統計
            with open(f"{output_dir}/training_stats.json", 'w', encoding='utf-8') as f:
                stats = self.training_stats.copy()
                stats.update({
                    'epoch': self.current_epoch,
                    'global_step': self.global_step,
                    'best_reward': self.best_reward
                })
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 模型已保存到: {output_dir}")
            
        except Exception as e:
            logger.error(f"❌ 模型保存失敗: {e}")


def create_demo_dataset(output_path: str, num_samples: int = 100):
    """創建示例訓練數據集"""
    logger.info(f"📝 創建示例數據集: {num_samples} 個樣本")
    
    demo_queries = [
        "分析台積電的投資價值",
        "如何評估鴻海的財務狀況",
        "台股目前的趨勢如何",
        "什麼是本益比",
        "如何分散投資風險",
        "聯電和台積電哪個更適合投資",
        "半導體產業的未來展望",
        "如何判斷股票的買賣時機",
        "什麼是技術分析",
        "基本面分析包含哪些要素"
    ]
    
    # 生成訓練樣本
    samples = []
    for i in range(num_samples):
        query = random.choice(demo_queries)
        if i % 10 == 0:  # 添加一些變化
            query = f"請分析 {query}"
        
        sample = {
            "query": query,
            "context": "台股投資分析",
            "reference": "這需要綜合考慮多個因素，包括財務數據、市場趨勢和風險評估。"
        }
        samples.append(sample)
    
    # 保存到文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for sample in samples:
            f.write(json.dumps(sample, ensure_ascii=False) + '\n')
    
    logger.info(f"✅ 示例數據集已創建: {output_path}")


def main():
    """主函數 - 為小k提供的訓練入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GRPO訓練器 - 支援AI訓練專家團隊(小k)')
    parser.add_argument('--dataset', type=str, required=True, help='訓練數據集路徑')
    parser.add_argument('--output', type=str, required=True, help='模型輸出路徑')
    parser.add_argument('--create-demo', action='store_true', help='創建示例數據集')
    parser.add_argument('--demo-samples', type=int, default=100, help='示例數據集樣本數')
    parser.add_argument('--config', type=str, help='配置文件路徑')
    
    args = parser.parse_args()
    
    try:
        # 創建示例數據集（如果需要）
        if args.create_demo:
            create_demo_dataset(args.dataset, args.demo_samples)
            logger.info("示例數據集創建完成，可以開始訓練了！")
            return
        
        # 加載配置
        if args.config and Path(args.config).exists():
            with open(args.config, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            training_config = GRPOTrainingConfig(**config_dict)
        else:
            training_config = GRPOTrainingConfig()
        
        reward_config = FinancialRewardConfig()
        
        # 創建訓練器
        trainer = GRPOTrainer(training_config, reward_config)
        
        # 開始訓練
        trainer.train(args.dataset, args.output)
        
        logger.info("🎉 GRPO訓練成功完成！")
        
    except KeyboardInterrupt:
        logger.info("👤 訓練被用戶中斷")
    except Exception as e:
        logger.error(f"❌ 訓練失敗: {e}")
        raise



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
    # 確保日誌目錄存在
    os.makedirs('/app/logs/training', exist_ok=True)
    
    # 運行訓練
    main()