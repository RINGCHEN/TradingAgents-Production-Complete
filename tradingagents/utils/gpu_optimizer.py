"""
GPU Memory Optimizer
GPU記憶體優化工具

專為RTX 4070/4090優化的記憶體管理工具
"""

import gc
import torch
import logging
from typing import Dict, Any, Optional
import psutil
import nvidia_ml_py3 as nvml

logger = logging.getLogger(__name__)


class GPUMemoryOptimizer:
    """GPU記憶體優化器"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.gpu_initialized = False
        
        if torch.cuda.is_available():
            try:
                nvml.nvmlInit()
                self.gpu_initialized = True
                logger.info("GPU memory optimizer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize NVML: {e}")
    
    def cleanup_memory(self):
        """清理GPU記憶體"""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # 強制垃圾回收
        gc.collect()
    
    def get_memory_info(self) -> Dict[str, Any]:
        """獲取記憶體信息"""
        info = {
            'cpu_memory': {
                'total': psutil.virtual_memory().total / (1024**3),
                'available': psutil.virtual_memory().available / (1024**3),
                'used_percent': psutil.virtual_memory().percent
            }
        }
        
        if torch.cuda.is_available():
            info['gpu_memory'] = {
                'total': torch.cuda.get_device_properties(0).total_memory / (1024**3),
                'allocated': torch.cuda.memory_allocated(0) / (1024**3),
                'reserved': torch.cuda.memory_reserved(0) / (1024**3),
                'free': (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / (1024**3)
            }
        
        return info
    
    def optimize_for_training(self):
        """為訓練優化GPU設置"""
        if not torch.cuda.is_available():
            return
        
        # 設置記憶體分配策略
        torch.cuda.set_per_process_memory_fraction(0.90)
        
        # 啟用記憶體池
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        logger.info("GPU optimized for training")