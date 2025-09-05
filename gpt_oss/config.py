#!/usr/bin/env python3
"""
GPT-OSS 配置文件
RTX 4070 優化配置
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class GPTOSSConfig:
    """GPT-OSS 配置類"""
    
    # 模型配置
    base_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    lora_adapter: Optional[str] = None
    load_in_4bit: bool = True
    device: str = "auto"
    
    # RTX 4070 優化配置
    max_memory_gb: float = 12.0
    memory_threshold: float = 0.9  # 90%
    batch_size: int = 1
    max_new_tokens: int = 512
    
    # 推理配置
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.1
    
    # 服務器配置
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 1
    timeout: int = 300  # 5分鐘超時
    
    # 安全配置
    enable_cors: bool = True
    max_requests_per_minute: int = 60
    
    @classmethod
    def from_env(cls) -> 'GPTOSSConfig':
        """從環境變數創建配置"""
        return cls(
            base_model=os.getenv("BASE_MODEL", cls.base_model),
            lora_adapter=os.getenv("LORA_ADAPTER"),
            load_in_4bit=os.getenv("LOAD_IN_4BIT", "true").lower() == "true",
            device=os.getenv("DEVICE", cls.device),
            max_memory_gb=float(os.getenv("MAX_MEMORY_GB", cls.max_memory_gb)),
            memory_threshold=float(os.getenv("MEMORY_THRESHOLD", cls.memory_threshold)),
            batch_size=int(os.getenv("BATCH_SIZE", cls.batch_size)),
            max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", cls.max_new_tokens)),
            temperature=float(os.getenv("TEMPERATURE", cls.temperature)),
            top_p=float(os.getenv("TOP_P", cls.top_p)),
            top_k=int(os.getenv("TOP_K", cls.top_k)),
            repetition_penalty=float(os.getenv("REPETITION_PENALTY", cls.repetition_penalty)),
            host=os.getenv("HOST", cls.host),
            port=int(os.getenv("PORT", cls.port)),
            workers=int(os.getenv("WORKERS", cls.workers)),
            timeout=int(os.getenv("TIMEOUT", cls.timeout)),
            enable_cors=os.getenv("ENABLE_CORS", "true").lower() == "true",
            max_requests_per_minute=int(os.getenv("MAX_REQUESTS_PER_MINUTE", cls.max_requests_per_minute))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            "base_model": self.base_model,
            "lora_adapter": self.lora_adapter,
            "load_in_4bit": self.load_in_4bit,
            "device": self.device,
            "max_memory_gb": self.max_memory_gb,
            "memory_threshold": self.memory_threshold,
            "batch_size": self.batch_size,
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "repetition_penalty": self.repetition_penalty,
            "host": self.host,
            "port": self.port,
            "workers": self.workers,
            "timeout": self.timeout,
            "enable_cors": self.enable_cors,
            "max_requests_per_minute": self.max_requests_per_minute
        }

# RTX 4070 專用優化配置
RTX_4070_CONFIG = GPTOSSConfig(
    max_memory_gb=12.0,
    memory_threshold=0.85,  # 更保守的記憶體使用
    batch_size=1,
    max_new_tokens=512,
    load_in_4bit=True,
    device="cuda"
)

# RTX 4090 專用優化配置
RTX_4090_CONFIG = GPTOSSConfig(
    max_memory_gb=24.0,
    memory_threshold=0.9,
    batch_size=2,
    max_new_tokens=1024,
    load_in_4bit=False,  # 4090可以不用量化
    device="cuda"
)

# CPU 配置
CPU_CONFIG = GPTOSSConfig(
    max_memory_gb=32.0,  # 系統RAM
    memory_threshold=0.8,
    batch_size=1,
    max_new_tokens=256,
    load_in_4bit=False,
    device="cpu"
)

def get_optimal_config() -> GPTOSSConfig:
    """根據硬體自動選擇最佳配置"""
    import torch
    
    if not torch.cuda.is_available():
        return CPU_CONFIG
    
    # 檢測GPU記憶體
    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    if gpu_memory_gb >= 20:  # RTX 4090 或更高
        return RTX_4090_CONFIG
    elif gpu_memory_gb >= 10:  # RTX 4070 或類似
        return RTX_4070_CONFIG
    else:  # 較低端GPU
        config = RTX_4070_CONFIG
        config.max_memory_gb = gpu_memory_gb
        config.memory_threshold = 0.8  # 更保守
        config.load_in_4bit = True
        return config