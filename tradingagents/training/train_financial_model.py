#!/usr/bin/env python3
"""
Financial Model Training Script
金融模型訓練腳本

完整的GRPO/PPO訓練流程，整合所有訓練組件
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent.parent.parent))

from tradingagents.training.grpo_trainer import GRPOTrainer
from tradingagents.training.ppo_trainer import PPOTrainer
from tradingagents.training.reward_models import create_reward_model
from tradingagents.training.training_config import (
    TrainingConfig, GRPOConfig, PPOConfig, ConfigManager
)
from tradingagents.training.data_manager import TrainingDataManager
from tradingagents.training.evaluator import ModelEvaluator

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class FinancialModelTrainer:
    """
    金融模型訓練器
    
    整合GRPO/PPO訓練流程的主要類別
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.data_manager = TrainingDataManager(config.dataset_path)
        self.evaluator = ModelEvaluator()
        
        # 創建輸出目錄
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 訓練統計
        self.training_stats = {
            'start_time': None,
            'end_time': None,
            'total_epochs': 0,
            'best_score': 0.0,
            'training_history': []
        }
        
    def prepare_data(self) -> tuple:
        """準備訓練數據"""
        logger.info("🔄 準備訓練數據...")
        
        # 檢查是否有現有數據
        dataset_path = Path(self.config.dataset_path)
        
        if not dataset_path.exists() or not any(dataset_path.glob("*.jsonl")):
            logger.info("未找到訓練數據，創建演示數據集...")
            demo_dir = self.data_manager.create_demo_dataset(str(dataset_path))
            logger.info(f"演示數據集已創建：{demo_dir}")
        
        # 載入數據
        data_files = list(dataset_path.glob("*.jsonl"))
        if not data_files:
            raise FileNotFoundError(f"在 {dataset_path} 中未找到 .jsonl 數據文件")
        
        queries, responses, contexts = self.data_manager.load_financial_data(
            str(data_files[0]), "jsonl"
        )
        
        logger.info(f"載入了 {len(queries)} 個訓練樣本")
        
        # 數據品質檢查
        quality_report = self.data_manager.validate_data_quality(queries, responses, contexts)
        logger.info(f"數據品質檢查完成：{len(quality_report['issues'])} 個問題")
        
        if quality_report['issues']:
            for issue in quality_report['issues']:
                logger.warning(f"數據品質問題：{issue}")
        
        # 分割數據
        train_data, val_data, test_data = self.data_manager.split_data(
            queries, responses, contexts,
            train_ratio=0.8, val_ratio=0.1, test_ratio=0.1
        )
        
        return train_data, val_data, test_data
    
    def setup_model_and_trainer(self):
        """設置模型和訓練器"""
        logger.info(f"🤖 設置模型和訓練器 (類型: {self.config.training_type})...")
        
        # 創建獎勵模型
        reward_model = create_reward_model(
            self.config.reward_model_type,
            self.config.reward_model_config
        )
        
        # 根據訓練類型創建訓練器
        if self.config.training_type == "grpo":
            grpo_config = self.config.get_algorithm_config()
            trainer = GRPOTrainer(
                config=grpo_config,
                model_name=self.config.model_name,
                reward_model=reward_model,
                device=self.config.device
            )
        elif self.config.training_type == "ppo":
            ppo_config = self.config.get_algorithm_config()
            trainer = PPOTrainer(
                config=ppo_config,
                model_name=self.config.model_name,
                reward_model=reward_model,
                device=self.config.device
            )
        else:
            raise ValueError(f"不支持的訓練類型: {self.config.training_type}")
        
        return trainer
    
    def train_model(self, trainer, train_data, val_data):
        """執行模型訓練"""
        logger.info("🚀 開始模型訓練...")
        
        self.training_stats['start_time'] = datetime.now().isoformat()
        
        train_queries, train_responses, train_contexts = train_data
        val_queries, val_responses, val_contexts = val_data
        
        best_val_score = 0.0
        patience_counter = 0
        
        for epoch in range(self.config.num_train_epochs):
            logger.info(f"📚 Epoch {epoch + 1}/{self.config.num_train_epochs}")
            
            # 訓練一個epoch
            if self.config.training_type == "grpo":
                # GRPO需要(query, response)對
                training_pairs = list(zip(train_queries, train_responses))
                epoch_stats = trainer.train_epoch(training_pairs, train_contexts)
            else:
                # PPO使用查詢生成回應
                epoch_stats = trainer.train_epoch(train_queries, train_contexts)
            
            # 記錄訓練統計
            self.training_stats['training_history'].append({
                'epoch': epoch + 1,
                'stats': epoch_stats,
                'timestamp': datetime.now().isoformat()
            })
            
            # 驗證評估
            if (epoch + 1) % self.config.eval_steps == 0:
                logger.info("📊 執行驗證評估...")
                
                val_result = self.evaluator.evaluate_model(
                    trainer.model,
                    trainer.tokenizer,
                    val_queries[:10],  # 使用前10個樣本快速評估
                    val_responses[:10],
                    val_contexts[:10] if val_contexts else None,
                    f"{self.config.model_name}_epoch_{epoch + 1}"
                )
                
                val_score = val_result.metrics.overall_score
                logger.info(f"驗證分數: {val_score:.3f}")
                
                # 檢查是否是最佳模型
                if val_score > best_val_score:
                    best_val_score = val_score
                    patience_counter = 0
                    
                    # 保存最佳模型
                    best_model_path = self.output_dir / "best_model"
                    trainer.save_checkpoint(str(best_model_path), epoch + 1, epoch_stats)
                    logger.info(f"💾 保存最佳模型 (分數: {val_score:.3f})")
                else:
                    patience_counter += 1
                
                # 早停檢查
                if hasattr(self.config, 'early_stopping_patience') and patience_counter >= self.config.early_stopping_patience:
                    logger.info(f"⏹️ 早停觸發 (patience: {patience_counter})")
                    break
            
            # 定期保存檢查點
            if (epoch + 1) % self.config.save_steps == 0:
                checkpoint_path = self.output_dir / f"checkpoint_epoch_{epoch + 1}"
                trainer.save_checkpoint(str(checkpoint_path), epoch + 1, epoch_stats)
                logger.info(f"💾 保存檢查點: epoch {epoch + 1}")
        
        self.training_stats['end_time'] = datetime.now().isoformat()
        self.training_stats['total_epochs'] = epoch + 1
        self.training_stats['best_score'] = best_val_score
        
        logger.info("✅ 訓練完成！")
        return trainer
    
    def evaluate_final_model(self, trainer, test_data):
        """評估最終模型"""
        logger.info("📈 執行最終模型評估...")
        
        test_queries, test_responses, test_contexts = test_data
        
        # 載入最佳模型進行評估
        best_model_path = self.output_dir / "best_model"
        if best_model_path.exists():
            logger.info("載入最佳模型進行評估...")
            trainer.load_checkpoint(str(best_model_path))
        
        # 執行完整評估
        final_result = self.evaluator.evaluate_model(
            trainer.model,
            trainer.tokenizer,
            test_queries,
            test_responses,
            test_contexts,
            f"{self.config.model_name}_final"
        )
        
        # 生成評估報告
        report_dir = self.output_dir / "evaluation_report"
        self.evaluator.generate_evaluation_report(
            final_result,
            str(report_dir),
            include_plots=True
        )
        
        logger.info(f"📊 最終評估分數: {final_result.metrics.overall_score:.3f}")
        logger.info(f"📄 評估報告已保存到: {report_dir}")
        
        return final_result
    
    def save_training_summary(self, final_result):
        """保存訓練總結"""
        summary = {
            'config': self.config.to_dict(),
            'training_stats': self.training_stats,
            'final_evaluation': {
                'overall_score': final_result.metrics.overall_score,
                'accuracy_score': final_result.metrics.accuracy_score,
                'relevance_score': final_result.metrics.relevance_score,
                'risk_awareness_score': final_result.metrics.risk_awareness_score,
                'actionability_score': final_result.metrics.actionability_score,
                'compliance_score': final_result.metrics.compliance_score
            },
            'recommendations': final_result.recommendations,
            'hardware_info': self._get_hardware_info()
        }
        
        summary_path = self.output_dir / "training_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📋 訓練總結已保存到: {summary_path}")
    
    def _get_hardware_info(self) -> Dict[str, Any]:
        """獲取硬體信息"""
        info = {
            'cuda_available': torch.cuda.is_available(),
            'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        
        if torch.cuda.is_available():
            info['gpu_name'] = torch.cuda.get_device_name(0)
            info['gpu_memory_total'] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        
        return info
    
    def run_full_training_pipeline(self):
        """執行完整的訓練流程"""
        try:
            logger.info("🎯 開始金融模型訓練流程...")
            
            # 1. 準備數據
            train_data, val_data, test_data = self.prepare_data()
            
            # 2. 設置模型和訓練器
            trainer = self.setup_model_and_trainer()
            
            # 3. 執行訓練
            trained_trainer = self.train_model(trainer, train_data, val_data)
            
            # 4. 最終評估
            final_result = self.evaluate_final_model(trained_trainer, test_data)
            
            # 5. 保存總結
            self.save_training_summary(final_result)
            
            logger.info("🎉 訓練流程完成！")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ 訓練過程中發生錯誤: {e}")
            raise


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="金融模型訓練腳本")
    parser.add_argument("--config", type=str, help="配置文件路徑")
    parser.add_argument("--training-type", choices=["grpo", "ppo"], default="grpo", help="訓練類型")
    parser.add_argument("--model-name", type=str, default="microsoft/DialoGPT-medium", help="基礎模型名稱")
    parser.add_argument("--dataset-path", type=str, default="./data/training_data", help="數據集路徑")
    parser.add_argument("--output-dir", type=str, default="./models/trained_model", help="輸出目錄")
    parser.add_argument("--num-epochs", type=int, default=3, help="訓練輪數")
    parser.add_argument("--batch-size", type=int, default=4, help="批次大小")
    parser.add_argument("--learning-rate", type=float, default=5e-5, help="學習率")
    parser.add_argument("--reward-model", choices=["financial", "trading", "risk_adjusted", "multi_factor"], 
                       default="financial", help="獎勵模型類型")
    
    args = parser.parse_args()
    
    # 載入或創建配置
    if args.config:
        config_manager = ConfigManager()
        config = config_manager.load_config(args.config)
    else:
        # 使用命令行參數創建配置
        config = TrainingConfig(
            training_type=args.training_type,
            model_name=args.model_name,
            dataset_path=args.dataset_path,
            output_dir=args.output_dir,
            num_train_epochs=args.num_epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            reward_model_type=args.reward_model
        )
    
    # 顯示配置信息
    logger.info("📋 訓練配置:")
    logger.info(f"  - 訓練類型: {config.training_type}")
    logger.info(f"  - 模型名稱: {config.model_name}")
    logger.info(f"  - 數據集路徑: {config.dataset_path}")
    logger.info(f"  - 輸出目錄: {config.output_dir}")
    logger.info(f"  - 訓練輪數: {config.num_train_epochs}")
    logger.info(f"  - 批次大小: {config.batch_size}")
    logger.info(f"  - 學習率: {config.learning_rate}")
    logger.info(f"  - 獎勵模型: {config.reward_model_type}")
    
    # 硬體建議
    hardware_rec = config.get_hardware_recommendations()
    logger.info("💻 硬體建議:")
    for key, value in hardware_rec.items():
        logger.info(f"  - {key}: {value}")
    
    # 創建訓練器並執行訓練
    trainer = FinancialModelTrainer(config)
    result = trainer.run_full_training_pipeline()
    
    logger.info(f"🏆 最終評估分數: {result.metrics.overall_score:.3f}")
    logger.info("🎯 訓練完成！檢查輸出目錄以獲取詳細結果。")



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
    main()