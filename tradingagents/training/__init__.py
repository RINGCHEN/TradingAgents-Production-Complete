"""
TradingAgents Training Module
AI訓練專家團隊核心模組

提供完整的強化學習訓練系統：
- GRPO (Group Relative Policy Optimization) 訓練
- PPO (Proximal Policy Optimization) 訓練  
- 金融專業化獎勵模型
- 訓練配置管理
- 模型評估和驗證
"""

from .grpo_trainer import GRPOTrainer
from .ppo_trainer import PPOTrainer
from .reward_models import FinancialRewardModel, TradingRewardModel
from .training_config import TrainingConfig, GRPOConfig, PPOConfig
from .data_manager import TrainingDataManager
from .evaluator import ModelEvaluator

__all__ = [
    'GRPOTrainer',
    'PPOTrainer', 
    'FinancialRewardModel',
    'TradingRewardModel',
    'TrainingConfig',
    'GRPOConfig',
    'PPOConfig',
    'TrainingDataManager',
    'ModelEvaluator'
]

__version__ = "1.0.0"