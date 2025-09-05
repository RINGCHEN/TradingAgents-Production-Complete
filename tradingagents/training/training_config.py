"""
Training Configuration Management
訓練配置管理模組

提供：
- TrainingConfig: 基礎訓練配置
- GRPOConfig: GRPO專用配置
- PPOConfig: PPO專用配置
- 配置驗證和優化建議
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from pathlib import Path
import torch


@dataclass
class BaseTrainingConfig:
    """基礎訓練配置"""
    
    # 模型配置
    model_name: str = "microsoft/DialoGPT-medium"
    max_length: int = 1024
    max_query_length: int = 512
    max_response_length: int = 512
    
    # 訓練超參數
    learning_rate: float = 5e-5
    batch_size: int = 4
    gradient_accumulation_steps: int = 8
    num_train_epochs: int = 3
    max_steps: int = -1
    warmup_steps: int = 100
    
    # 優化器配置
    weight_decay: float = 0.01
    adam_epsilon: float = 1e-8
    max_grad_norm: float = 1.0
    
    # 精度和設備配置
    fp16: bool = True
    bf16: bool = False
    device: str = "auto"
    
    # 保存和日誌配置
    save_steps: int = 500
    logging_steps: int = 50
    eval_steps: int = 250
    output_dir: str = "./models/trained_model"
    logging_dir: str = "./logs/training"
    
    # 數據配置
    dataloader_num_workers: int = 4
    remove_unused_columns: bool = False
    
    # 評估配置
    evaluation_strategy: str = "steps"
    save_strategy: str = "steps"
    load_best_model_at_end: bool = True
    metric_for_best_model: str = "eval_loss"
    greater_is_better: bool = False
    
    # GPU優化配置
    gradient_checkpointing: bool = True
    dataloader_pin_memory: bool = True
    
    def __post_init__(self):
        """配置後處理和驗證"""
        self._validate_config()
        self._optimize_for_hardware()
    
    def _validate_config(self):
        """驗證配置參數"""
        if self.batch_size <= 0:
            raise ValueError("batch_size must be positive")
        
        if self.learning_rate <= 0:
            raise ValueError("learning_rate must be positive")
        
        if self.max_length <= 0:
            raise ValueError("max_length must be positive")
        
        if self.max_query_length + self.max_response_length > self.max_length:
            raise ValueError("max_query_length + max_response_length cannot exceed max_length")
    
    def _optimize_for_hardware(self):
        """根據硬體配置優化參數"""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            
            # RTX 4070 優化
            if "4070" in gpu_name:
                if self.batch_size > 4:
                    self.batch_size = 4
                    print("Optimized batch_size for RTX 4070: 4")
                
                if not self.fp16:
                    self.fp16 = True
                    print("Enabled FP16 for RTX 4070 memory optimization")
                
                if not self.gradient_checkpointing:
                    self.gradient_checkpointing = True
                    print("Enabled gradient checkpointing for RTX 4070")
            
            # RTX 4090 優化
            elif "4090" in gpu_name:
                if self.batch_size < 8:
                    self.batch_size = 8
                    print("Optimized batch_size for RTX 4090: 8")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return asdict(self)
    
    def save(self, path: str):
        """保存配置到文件"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if path.suffix == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        elif path.suffix in ['.yml', '.yaml']:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError("Unsupported file format. Use .json, .yml, or .yaml")
    
    @classmethod
    def load(cls, path: str):
        """從文件載入配置"""
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
        elif path.suffix in ['.yml', '.yaml']:
            with open(path, 'r', encoding='utf-8') as f:
                config_dict = yaml.safe_load(f)
        else:
            raise ValueError("Unsupported file format. Use .json, .yml, or .yaml")
        
        return cls(**config_dict)


@dataclass
class GRPOConfig(BaseTrainingConfig):
    """GRPO (Group Relative Policy Optimization) 專用配置"""
    
    # PPO基礎參數
    ppo_epochs: int = 3
    mini_batch_size: int = 2
    cliprange: float = 0.2
    cliprange_value: float = 0.2
    vf_coef: float = 0.5
    entropy_coef: float = 0.01
    
    # GRPO特有參數
    relative_weight: float = 0.3  # 群組相對優勢權重
    stability_coef: float = 0.1   # 穩定性正則化係數
    target_kl: float = 0.01       # 目標KL散度
    
    # GAE參數
    gamma: float = 0.99           # 折扣因子
    gae_lambda: float = 0.95      # GAE lambda參數
    
    # 獎勵處理
    use_score_scaling: bool = True
    use_score_norm: bool = True
    score_clip: float = 0.5
    
    # 溫度參數
    temperature: float = 0.7
    
    def __post_init__(self):
        super().__post_init__()
        self._validate_grpo_config()
    
    def _validate_grpo_config(self):
        """驗證GRPO特有配置"""
        if not 0 <= self.relative_weight <= 1:
            raise ValueError("relative_weight must be between 0 and 1")
        
        if self.cliprange <= 0:
            raise ValueError("cliprange must be positive")
        
        if not 0 <= self.gamma <= 1:
            raise ValueError("gamma must be between 0 and 1")
        
        if not 0 <= self.gae_lambda <= 1:
            raise ValueError("gae_lambda must be between 0 and 1")


@dataclass
class PPOConfig(BaseTrainingConfig):
    """PPO (Proximal Policy Optimization) 專用配置"""
    
    # PPO核心參數
    ppo_epochs: int = 4
    mini_batch_size: int = 2
    cliprange: float = 0.2
    cliprange_value: float = 0.2
    vf_coef: float = 0.5
    entropy_coef: float = 0.01
    
    # 價值函數配置
    clip_value_loss: bool = True
    normalize_advantage: bool = True
    
    # GAE參數
    gamma: float = 0.99
    gae_lambda: float = 0.95
    
    # 經驗緩衝區
    buffer_size: int = 10000
    
    # 生成參數
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9
    
    # 早停配置
    early_stopping_patience: int = 3
    early_stopping_threshold: float = 0.01
    
    def __post_init__(self):
        super().__post_init__()
        self._validate_ppo_config()
    
    def _validate_ppo_config(self):
        """驗證PPO特有配置"""
        if self.ppo_epochs <= 0:
            raise ValueError("ppo_epochs must be positive")
        
        if self.mini_batch_size <= 0:
            raise ValueError("mini_batch_size must be positive")
        
        if self.mini_batch_size > self.batch_size:
            raise ValueError("mini_batch_size cannot exceed batch_size")
        
        if not 0 <= self.cliprange <= 1:
            raise ValueError("cliprange must be between 0 and 1")


@dataclass
class TrainingConfig(BaseTrainingConfig):
    """通用訓練配置，包含所有訓練類型的參數"""
    
    # 訓練類型
    training_type: str = "grpo"  # "grpo", "ppo", "sft"
    
    # 獎勵模型配置
    reward_model_type: str = "financial"  # "financial", "trading", "risk_adjusted", "multi_factor"
    reward_model_config: Dict[str, Any] = field(default_factory=dict)
    
    # 數據配置
    dataset_path: str = "./data/training_data"
    validation_split: float = 0.1
    test_split: float = 0.1
    
    # 檢查點配置
    save_total_limit: int = 3
    resume_from_checkpoint: Optional[str] = None
    
    # 分散式訓練
    local_rank: int = -1
    world_size: int = 1
    
    # 實驗追蹤
    wandb_project: Optional[str] = None
    wandb_run_name: Optional[str] = None
    tensorboard_log_dir: Optional[str] = None
    
    # 金融專用配置
    financial_context: Dict[str, Any] = field(default_factory=dict)
    
    def get_algorithm_config(self):
        """根據訓練類型獲取對應的算法配置"""
        if self.training_type == "grpo":
            return GRPOConfig(**{k: v for k, v in self.to_dict().items() 
                               if k in GRPOConfig.__dataclass_fields__})
        elif self.training_type == "ppo":
            return PPOConfig(**{k: v for k, v in self.to_dict().items() 
                              if k in PPOConfig.__dataclass_fields__})
        else:
            return self
    
    def get_hardware_recommendations(self) -> Dict[str, Any]:
        """獲取硬體配置建議"""
        recommendations = {
            "gpu_memory_required": "8GB+",
            "recommended_gpu": "RTX 4070 or better",
            "cpu_cores": "8+",
            "ram": "32GB+",
            "storage": "100GB+ SSD"
        }
        
        # 根據配置調整建議
        total_batch_size = self.batch_size * self.gradient_accumulation_steps
        
        if total_batch_size >= 32:
            recommendations["gpu_memory_required"] = "24GB+"
            recommendations["recommended_gpu"] = "RTX 4090 or A100"
        elif total_batch_size >= 16:
            recommendations["gpu_memory_required"] = "12GB+"
            recommendations["recommended_gpu"] = "RTX 4070 Ti or RTX 4080"
        
        if self.max_length >= 2048:
            recommendations["gpu_memory_required"] = "16GB+"
            recommendations["ram"] = "64GB+"
        
        return recommendations
    
    def get_training_time_estimate(self, num_samples: int) -> Dict[str, str]:
        """估算訓練時間"""
        # 基於經驗的估算公式
        steps_per_epoch = num_samples // (self.batch_size * self.gradient_accumulation_steps)
        total_steps = steps_per_epoch * self.num_train_epochs
        
        # RTX 4070 基準：約2步/秒
        seconds_per_step = 0.5
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            if "4090" in gpu_name:
                seconds_per_step = 0.3
            elif "4080" in gpu_name:
                seconds_per_step = 0.4
        
        total_seconds = total_steps * seconds_per_step
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        
        return {
            "total_steps": str(total_steps),
            "estimated_time": f"{hours}h {minutes}m",
            "steps_per_epoch": str(steps_per_epoch)
        }


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "./configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def create_default_configs(self):
        """創建默認配置文件"""
        configs = {
            "grpo_default.yaml": GRPOConfig(),
            "ppo_default.yaml": PPOConfig(),
            "training_default.yaml": TrainingConfig()
        }
        
        for filename, config in configs.items():
            config_path = self.config_dir / filename
            config.save(str(config_path))
            print(f"Created default config: {config_path}")
    
    def load_config(self, config_name: str) -> BaseTrainingConfig:
        """載入配置"""
        config_path = self.config_dir / config_name
        
        if not config_path.exists():
            # 嘗試添加擴展名
            for ext in ['.yaml', '.yml', '.json']:
                test_path = self.config_dir / f"{config_name}{ext}"
                if test_path.exists():
                    config_path = test_path
                    break
            else:
                raise FileNotFoundError(f"Config file not found: {config_name}")
        
        # 根據文件名判斷配置類型
        if 'grpo' in config_name.lower():
            return GRPOConfig.load(str(config_path))
        elif 'ppo' in config_name.lower():
            return PPOConfig.load(str(config_path))
        else:
            return TrainingConfig.load(str(config_path))
    
    def list_configs(self) -> List[str]:
        """列出所有配置文件"""
        config_files = []
        for ext in ['*.yaml', '*.yml', '*.json']:
            config_files.extend(self.config_dir.glob(ext))
        
        return [f.name for f in config_files]
    
    def validate_config(self, config: BaseTrainingConfig) -> Dict[str, Any]:
        """驗證配置並提供建議"""
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        try:
            # 基本驗證已在__post_init__中完成
            pass
        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(str(e))
        
        # 性能建議
        if config.batch_size * config.gradient_accumulation_steps < 16:
            validation_result["suggestions"].append(
                "Consider increasing effective batch size (batch_size * gradient_accumulation_steps) to 16+ for better training stability"
            )
        
        if config.learning_rate > 1e-4:
            validation_result["warnings"].append(
                "Learning rate seems high, consider using 5e-5 or lower for fine-tuning"
            )
        
        if not config.fp16 and torch.cuda.is_available():
            validation_result["suggestions"].append(
                "Enable FP16 for better GPU memory efficiency"
            )
        
        return validation_result


# 便利函數
def create_grpo_config(**kwargs) -> GRPOConfig:
    """創建GRPO配置"""
    return GRPOConfig(**kwargs)


def create_ppo_config(**kwargs) -> PPOConfig:
    """創建PPO配置"""
    return PPOConfig(**kwargs)


def create_training_config(**kwargs) -> TrainingConfig:
    """創建通用訓練配置"""
    return TrainingConfig(**kwargs)


def load_config_from_file(path: str) -> BaseTrainingConfig:
    """從文件載入配置"""
    path = Path(path)
    
    if 'grpo' in path.name.lower():
        return GRPOConfig.load(str(path))
    elif 'ppo' in path.name.lower():
        return PPOConfig.load(str(path))
    else:
        return TrainingConfig.load(str(path))


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

