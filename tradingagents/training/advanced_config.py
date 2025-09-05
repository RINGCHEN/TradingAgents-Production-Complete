"""
Advanced Training Configuration and Optimization
高級訓練配置和優化系統

任務4.4: 高級訓練配置和優化
負責人: 小k (AI訓練專家團隊)

提供：
- YAML配置文件支援
- 動態配置調整
- 超參數優化
- 訓練策略自動選擇
- 性能優化建議
"""

import os
import yaml
import json
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import numpy as np
import torch

from .training_config import TrainingConfig, GRPOConfig, PPOConfig

logger = logging.getLogger(__name__)


@dataclass
class HyperparameterRange:
    """超參數範圍定義"""
    min_value: float
    max_value: float
    step: Optional[float] = None
    scale: str = "linear"  # "linear", "log", "categorical"
    values: Optional[List[Any]] = None  # 用於categorical類型


@dataclass
class OptimizationConfig:
    """優化配置"""
    method: str = "grid_search"  # "grid_search", "random_search", "bayesian"
    max_trials: int = 20
    timeout_minutes: int = 60
    early_stopping_patience: int = 3
    optimization_metric: str = "overall_score"
    minimize: bool = False  # False表示最大化指標


@dataclass
class AdvancedTrainingConfig(TrainingConfig):
    """高級訓練配置"""
    
    # 超參數優化配置
    hyperparameter_optimization: bool = False
    optimization_config: OptimizationConfig = field(default_factory=OptimizationConfig)
    hyperparameter_ranges: Dict[str, HyperparameterRange] = field(default_factory=dict)
    
    # 動態調整配置
    dynamic_adjustment: bool = False
    adjustment_frequency: int = 100  # 每多少步檢查一次
    adjustment_metrics: List[str] = field(default_factory=lambda: ["loss", "accuracy"])
    
    # 高級優化策略
    mixed_precision_level: str = "O1"  # "O0", "O1", "O2", "O3"
    gradient_compression: bool = False
    gradient_clipping_type: str = "norm"  # "norm", "value"
    
    # 學習率調度策略
    lr_scheduler_type: str = "cosine"  # "cosine", "linear", "polynomial", "constant"
    lr_warmup_type: str = "linear"  # "linear", "constant"
    lr_scheduler_params: Dict[str, Any] = field(default_factory=dict)
    
    # 數據增強配置
    data_augmentation: bool = False
    augmentation_strategies: List[str] = field(default_factory=list)
    augmentation_probability: float = 0.5
    
    # 正則化配置
    dropout_rate: float = 0.1
    layer_dropout: bool = False
    attention_dropout: float = 0.1
    
    # 模型架構優化
    model_parallelism: bool = False
    pipeline_parallelism: bool = False
    tensor_parallelism: bool = False
    
    # 記憶體優化
    activation_checkpointing: bool = True
    cpu_offload: bool = False
    zero_optimization_stage: int = 1  # 0, 1, 2, 3
    
    # 實驗追蹤配置
    experiment_tracking: Dict[str, Any] = field(default_factory=dict)
    
    # 自動化配置
    auto_config: bool = False
    auto_config_target: str = "performance"  # "performance", "memory", "speed"
    
    def __post_init__(self):
        super().__post_init__()
        self._setup_advanced_defaults()
        self._validate_advanced_config()
    
    def _setup_advanced_defaults(self):
        """設置高級配置默認值"""
        
        # 設置默認超參數範圍
        if not self.hyperparameter_ranges and self.hyperparameter_optimization:
            self.hyperparameter_ranges = {
                'learning_rate': HyperparameterRange(1e-6, 1e-3, scale="log"),
                'batch_size': HyperparameterRange(2, 16, values=[2, 4, 8, 16]),
                'warmup_steps': HyperparameterRange(50, 500, step=50),
                'weight_decay': HyperparameterRange(0.0, 0.1, step=0.01)
            }
        
        # 設置默認學習率調度參數
        if not self.lr_scheduler_params:
            if self.lr_scheduler_type == "cosine":
                self.lr_scheduler_params = {
                    'T_max': self.max_steps if self.max_steps > 0 else 1000,
                    'eta_min': self.learning_rate * 0.1
                }
            elif self.lr_scheduler_type == "polynomial":
                self.lr_scheduler_params = {
                    'power': 1.0,
                    'total_iters': self.max_steps if self.max_steps > 0 else 1000
                }
        
        # 設置默認實驗追蹤
        if not self.experiment_tracking:
            self.experiment_tracking = {
                'enabled': False,
                'project_name': 'financial_ai_training',
                'experiment_name': f'training_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'tags': ['financial', 'ai', self.training_type],
                'log_frequency': 10
            }
    
    def _validate_advanced_config(self):
        """驗證高級配置"""
        
        # 驗證混合精度配置
        valid_precision_levels = ["O0", "O1", "O2", "O3"]
        if self.mixed_precision_level not in valid_precision_levels:
            raise ValueError(f"Invalid mixed_precision_level: {self.mixed_precision_level}")
        
        # 驗證學習率調度器
        valid_schedulers = ["cosine", "linear", "polynomial", "constant"]
        if self.lr_scheduler_type not in valid_schedulers:
            raise ValueError(f"Invalid lr_scheduler_type: {self.lr_scheduler_type}")
        
        # 驗證ZeRO優化階段
        if not 0 <= self.zero_optimization_stage <= 3:
            raise ValueError("zero_optimization_stage must be between 0 and 3")
        
        # 驗證dropout率
        if not 0 <= self.dropout_rate <= 1:
            raise ValueError("dropout_rate must be between 0 and 1")


class AdvancedConfigManager:
    """高級配置管理器"""
    
    def __init__(self, config_dir: str = "./configs/advanced"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 預定義配置模板
        self.config_templates = {
            'performance_optimized': self._create_performance_template(),
            'memory_optimized': self._create_memory_template(),
            'speed_optimized': self._create_speed_template(),
            'research_optimized': self._create_research_template()
        }
    
    def _create_performance_template(self) -> Dict[str, Any]:
        """創建性能優化模板"""
        return {
            'training_type': 'grpo',
            'batch_size': 8,
            'gradient_accumulation_steps': 4,
            'learning_rate': 3e-5,
            'mixed_precision_level': 'O2',
            'gradient_checkpointing': True,
            'lr_scheduler_type': 'cosine',
            'zero_optimization_stage': 2,
            'activation_checkpointing': True,
            'dynamic_adjustment': True,
            'adjustment_frequency': 50,
            'experiment_tracking': {
                'enabled': True,
                'log_frequency': 10
            }
        }
    
    def _create_memory_template(self) -> Dict[str, Any]:
        """創建記憶體優化模板"""
        return {
            'training_type': 'grpo',
            'batch_size': 2,
            'gradient_accumulation_steps': 16,
            'learning_rate': 5e-5,
            'mixed_precision_level': 'O3',
            'gradient_checkpointing': True,
            'cpu_offload': True,
            'zero_optimization_stage': 3,
            'activation_checkpointing': True,
            'model_parallelism': True,
            'experiment_tracking': {
                'enabled': True,
                'log_frequency': 20
            }
        }
    
    def _create_speed_template(self) -> Dict[str, Any]:
        """創建速度優化模板"""
        return {
            'training_type': 'ppo',
            'batch_size': 16,
            'gradient_accumulation_steps': 2,
            'learning_rate': 1e-4,
            'mixed_precision_level': 'O1',
            'gradient_checkpointing': False,
            'zero_optimization_stage': 1,
            'activation_checkpointing': False,
            'lr_scheduler_type': 'linear',
            'experiment_tracking': {
                'enabled': True,
                'log_frequency': 5
            }
        }
    
    def _create_research_template(self) -> Dict[str, Any]:
        """創建研究優化模板"""
        return {
            'training_type': 'grpo',
            'batch_size': 4,
            'gradient_accumulation_steps': 8,
            'learning_rate': 5e-5,
            'hyperparameter_optimization': True,
            'optimization_config': {
                'method': 'bayesian',
                'max_trials': 50,
                'timeout_minutes': 120
            },
            'dynamic_adjustment': True,
            'data_augmentation': True,
            'experiment_tracking': {
                'enabled': True,
                'log_frequency': 1
            }
        }
    
    def create_config_from_template(
        self,
        template_name: str,
        overrides: Optional[Dict[str, Any]] = None
    ) -> AdvancedTrainingConfig:
        """從模板創建配置"""
        
        if template_name not in self.config_templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        # 獲取模板配置
        template_config = self.config_templates[template_name].copy()
        
        # 應用覆蓋設置
        if overrides:
            template_config.update(overrides)
        
        return AdvancedTrainingConfig(**template_config)
    
    def save_config_yaml(self, config: AdvancedTrainingConfig, filename: str):
        """保存配置為YAML文件"""
        
        config_path = self.config_dir / filename
        config_dict = asdict(config)
        
        # 處理特殊對象
        config_dict = self._serialize_config(config_dict)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        logger.info(f"配置已保存到: {config_path}")
    
    def load_config_yaml(self, filename: str) -> AdvancedTrainingConfig:
        """從YAML文件載入配置"""
        
        config_path = self.config_dir / filename
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        
        # 反序列化特殊對象
        config_dict = self._deserialize_config(config_dict)
        
        return AdvancedTrainingConfig(**config_dict)
    
    def _serialize_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """序列化配置字典"""
        
        # 處理HyperparameterRange對象
        if 'hyperparameter_ranges' in config_dict:
            ranges = config_dict['hyperparameter_ranges']
            for key, range_obj in ranges.items():
                if hasattr(range_obj, '__dict__'):
                    ranges[key] = asdict(range_obj)
        
        # 處理OptimizationConfig對象
        if 'optimization_config' in config_dict:
            opt_config = config_dict['optimization_config']
            if hasattr(opt_config, '__dict__'):
                config_dict['optimization_config'] = asdict(opt_config)
        
        return config_dict
    
    def _deserialize_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """反序列化配置字典"""
        
        # 處理HyperparameterRange對象
        if 'hyperparameter_ranges' in config_dict:
            ranges = config_dict['hyperparameter_ranges']
            for key, range_dict in ranges.items():
                if isinstance(range_dict, dict):
                    ranges[key] = HyperparameterRange(**range_dict)
        
        # 處理OptimizationConfig對象
        if 'optimization_config' in config_dict:
            opt_config = config_dict['optimization_config']
            if isinstance(opt_config, dict):
                config_dict['optimization_config'] = OptimizationConfig(**opt_config)
        
        return config_dict
    
    def auto_configure(
        self,
        target: str = "performance",
        hardware_info: Optional[Dict[str, Any]] = None
    ) -> AdvancedTrainingConfig:
        """自動配置生成"""
        
        logger.info(f"🤖 自動配置生成 (目標: {target})")
        
        # 獲取硬體信息
        if hardware_info is None:
            hardware_info = self._detect_hardware()
        
        # 根據目標選擇基礎模板
        if target == "performance":
            base_config = self._create_performance_template()
        elif target == "memory":
            base_config = self._create_memory_template()
        elif target == "speed":
            base_config = self._create_speed_template()
        else:
            base_config = self._create_performance_template()
        
        # 根據硬體調整配置
        optimized_config = self._optimize_for_hardware(base_config, hardware_info)
        
        return AdvancedTrainingConfig(**optimized_config)
    
    def _detect_hardware(self) -> Dict[str, Any]:
        """檢測硬體配置"""
        
        hardware_info = {
            'gpu_available': torch.cuda.is_available(),
            'gpu_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
            'gpu_memory_gb': 0,
            'gpu_name': '',
            'cpu_cores': os.cpu_count(),
            'system_memory_gb': 0
        }
        
        if torch.cuda.is_available():
            gpu_props = torch.cuda.get_device_properties(0)
            hardware_info['gpu_memory_gb'] = gpu_props.total_memory / (1024**3)
            hardware_info['gpu_name'] = gpu_props.name
        
        # 獲取系統記憶體
        try:
            import psutil
            hardware_info['system_memory_gb'] = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            hardware_info['system_memory_gb'] = 16  # 默認值
        
        return hardware_info
    
    def _optimize_for_hardware(
        self,
        base_config: Dict[str, Any],
        hardware_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根據硬體優化配置"""
        
        config = base_config.copy()
        
        gpu_memory = hardware_info.get('gpu_memory_gb', 0)
        gpu_name = hardware_info.get('gpu_name', '').lower()
        
        # RTX 4070 優化
        if '4070' in gpu_name:
            config.update({
                'batch_size': 4,
                'gradient_accumulation_steps': 8,
                'mixed_precision_level': 'O2',
                'gradient_checkpointing': True,
                'zero_optimization_stage': 2
            })
            logger.info("🎯 RTX 4070 優化配置已應用")
        
        # RTX 4090 優化
        elif '4090' in gpu_name:
            config.update({
                'batch_size': 8,
                'gradient_accumulation_steps': 4,
                'mixed_precision_level': 'O1',
                'gradient_checkpointing': False,
                'zero_optimization_stage': 1
            })
            logger.info("🎯 RTX 4090 優化配置已應用")
        
        # 低記憶體GPU優化
        elif gpu_memory < 8:
            config.update({
                'batch_size': 2,
                'gradient_accumulation_steps': 16,
                'mixed_precision_level': 'O3',
                'cpu_offload': True,
                'zero_optimization_stage': 3
            })
            logger.info("🎯 低記憶體GPU優化配置已應用")
        
        # 高記憶體GPU優化
        elif gpu_memory > 20:
            config.update({
                'batch_size': 16,
                'gradient_accumulation_steps': 2,
                'mixed_precision_level': 'O1',
                'model_parallelism': True
            })
            logger.info("🎯 高記憶體GPU優化配置已應用")
        
        return config
    
    def generate_hyperparameter_sweep_config(
        self,
        base_config: AdvancedTrainingConfig,
        sweep_parameters: List[str]
    ) -> Dict[str, Any]:
        """生成超參數掃描配置"""
        
        sweep_config = {
            'method': base_config.optimization_config.method,
            'metric': {
                'name': base_config.optimization_config.optimization_metric,
                'goal': 'minimize' if base_config.optimization_config.minimize else 'maximize'
            },
            'parameters': {}
        }
        
        # 添加掃描參數
        for param_name in sweep_parameters:
            if param_name in base_config.hyperparameter_ranges:
                param_range = base_config.hyperparameter_ranges[param_name]
                
                if param_range.values:
                    # 分類參數
                    sweep_config['parameters'][param_name] = {
                        'values': param_range.values
                    }
                else:
                    # 數值參數
                    if param_range.scale == 'log':
                        sweep_config['parameters'][param_name] = {
                            'distribution': 'log_uniform',
                            'min': np.log(param_range.min_value),
                            'max': np.log(param_range.max_value)
                        }
                    else:
                        sweep_config['parameters'][param_name] = {
                            'distribution': 'uniform',
                            'min': param_range.min_value,
                            'max': param_range.max_value
                        }
        
        return sweep_config
    
    def validate_config_compatibility(
        self,
        config: AdvancedTrainingConfig
    ) -> Dict[str, Any]:
        """驗證配置兼容性"""
        
        validation_result = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # 檢查記憶體需求
        estimated_memory = self._estimate_memory_usage(config)
        available_memory = self._get_available_gpu_memory()
        
        if estimated_memory > available_memory * 0.9:
            validation_result['errors'].append(
                f"估計記憶體使用 ({estimated_memory:.1f}GB) 超過可用記憶體 ({available_memory:.1f}GB)"
            )
            validation_result['valid'] = False
        
        # 檢查批次大小和梯度累積
        effective_batch_size = config.batch_size * config.gradient_accumulation_steps
        if effective_batch_size < 8:
            validation_result['warnings'].append(
                "有效批次大小過小，可能影響訓練穩定性"
            )
        
        # 檢查學習率設置
        if config.learning_rate > 1e-3:
            validation_result['warnings'].append(
                "學習率較高，建議監控訓練穩定性"
            )
        
        # 檢查混合精度和ZeRO兼容性
        if config.mixed_precision_level == 'O3' and config.zero_optimization_stage < 2:
            validation_result['suggestions'].append(
                "O3混合精度建議配合ZeRO Stage 2+使用"
            )
        
        return validation_result
    
    def _estimate_memory_usage(self, config: AdvancedTrainingConfig) -> float:
        """估算記憶體使用量"""
        
        # 簡化的記憶體估算
        base_memory = 2.0  # 基礎記憶體 (GB)
        
        # 模型記憶體
        model_memory = 1.5  # 假設中等大小模型
        
        # 批次記憶體
        batch_memory = config.batch_size * 0.1
        
        # 優化器記憶體
        optimizer_memory = model_memory * 2  # Adam需要2倍模型參數
        
        # ZeRO優化減少
        if config.zero_optimization_stage >= 2:
            optimizer_memory *= 0.5
        if config.zero_optimization_stage >= 3:
            model_memory *= 0.5
        
        # 混合精度減少
        if config.mixed_precision_level in ['O2', 'O3']:
            model_memory *= 0.7
            batch_memory *= 0.7
        
        total_memory = base_memory + model_memory + batch_memory + optimizer_memory
        
        return total_memory
    
    def _get_available_gpu_memory(self) -> float:
        """獲取可用GPU記憶體"""
        
        if not torch.cuda.is_available():
            return 0.0
        
        gpu_props = torch.cuda.get_device_properties(0)
        total_memory = gpu_props.total_memory / (1024**3)
        
        return total_memory
    
    def create_all_templates(self):
        """創建所有配置模板文件"""
        
        for template_name, template_config in self.config_templates.items():
            config = AdvancedTrainingConfig(**template_config)
            filename = f"{template_name}_config.yaml"
            self.save_config_yaml(config, filename)
            logger.info(f"創建模板配置: {filename}")
    
    def get_config_recommendations(
        self,
        training_goal: str,
        dataset_size: int,
        time_budget_hours: int
    ) -> Dict[str, Any]:
        """獲取配置建議"""
        
        recommendations = {
            'suggested_template': 'performance_optimized',
            'config_adjustments': {},
            'training_strategy': '',
            'estimated_time_hours': 0
        }
        
        # 根據訓練目標選擇模板
        if training_goal == 'research':
            recommendations['suggested_template'] = 'research_optimized'
            recommendations['training_strategy'] = '研究導向：啟用超參數優化和詳細實驗追蹤'
        elif training_goal == 'production':
            recommendations['suggested_template'] = 'performance_optimized'
            recommendations['training_strategy'] = '生產導向：平衡性能和穩定性'
        elif training_goal == 'quick_test':
            recommendations['suggested_template'] = 'speed_optimized'
            recommendations['training_strategy'] = '快速測試：優化訓練速度'
        
        # 根據數據集大小調整
        if dataset_size < 1000:
            recommendations['config_adjustments']['num_train_epochs'] = 5
            recommendations['config_adjustments']['save_steps'] = 100
        elif dataset_size > 10000:
            recommendations['config_adjustments']['num_train_epochs'] = 2
            recommendations['config_adjustments']['save_steps'] = 1000
        
        # 根據時間預算調整
        if time_budget_hours < 2:
            recommendations['config_adjustments']['batch_size'] = 8
            recommendations['config_adjustments']['gradient_accumulation_steps'] = 2
        elif time_budget_hours > 12:
            recommendations['config_adjustments']['hyperparameter_optimization'] = True
        
        # 估算訓練時間
        base_time_per_epoch = dataset_size / 1000 * 0.5  # 簡化估算
        epochs = recommendations['config_adjustments'].get('num_train_epochs', 3)
        recommendations['estimated_time_hours'] = base_time_per_epoch * epochs
        
        return recommendations


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

