#!/usr/bin/env python3
"""
GPU資源管理器 - RTX 4070優化版
小c - 硬體優化與資源管理團隊

此模組提供：
1. RTX 4070 12GB VRAM智能資源分配
2. 動態記憶體管理和OOM預防
3. GPU溫度監控和自動調節
4. CUDA優化配置和性能調優
5. 多任務並行資源隔離
"""

import os
import time
import logging
import asyncio
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import uuid
import json
from pathlib import Path

# GPU相關庫
try:
    import torch
    import torch.cuda
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available, GPU functionality limited")

try:
    import pynvml
    pynvml.nvmlInit()
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logging.warning("NVML not available, using fallback monitoring")

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceStatus(Enum):
    """資源狀態"""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    OVERLOADED = "overloaded"
    ERROR = "error"


class AllocationType(Enum):
    """分配類型"""
    ART_TRAINING = "art_training"
    GPT_OSS_INFERENCE = "gpt_oss_inference"
    LORA_FINETUNE = "lora_finetune"
    SYSTEM_RESERVE = "system_reserve"


@dataclass
class GPUInfo:
    """GPU信息"""
    device_id: int
    name: str
    total_memory_gb: float
    available_memory_gb: float
    temperature: float
    utilization: float
    power_usage_w: float
    memory_usage_percent: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ResourceRequirement:
    """資源需求"""
    memory_gb: float
    compute_units: int = 1
    priority: int = 1
    allocation_type: AllocationType = AllocationType.ART_TRAINING
    max_duration_hours: float = 24.0
    requires_exclusive: bool = False


@dataclass
class AllocatedResources:
    """已分配資源"""
    allocation_id: str
    memory_gb: float
    compute_units: int
    allocation_type: AllocationType
    device_id: int
    cuda_config: Dict[str, Any]
    timestamp: datetime
    expires_at: datetime
    status: ResourceStatus = ResourceStatus.ALLOCATED


@dataclass
class CudaConfig:
    """CUDA配置"""
    device_id: int
    memory_fraction: float
    allow_growth: bool = True
    mixed_precision: bool = True
    compile_mode: bool = True
    optimization_level: str = "O2"
    max_memory_allocated: Optional[float] = None


class InsufficientResourcesError(Exception):
    """資源不足異常"""
    pass


class GPUResourceManager:
    """
    GPU資源管理器 - RTX 4070優化版
    
    專為RTX 4070 12GB VRAM設計的智能資源管理系統，
    提供動態記憶體分配、溫度監控、OOM預防等功能。
    """
    
    def __init__(self, device_id: int = 0, max_memory_gb: float = 12.0):
        """
        初始化GPU資源管理器
        
        Args:
            device_id: GPU設備ID
            max_memory_gb: 最大可用記憶體GB
        """
        self.device_id = device_id
        self.total_memory_gb = max_memory_gb
        self.reserved_memory_gb = 1.0  # 系統保留1GB
        self.available_memory_gb = max_memory_gb - self.reserved_memory_gb
        
        # 資源追蹤
        self.current_allocations: Dict[str, AllocatedResources] = {}
        self.allocation_history: List[AllocatedResources] = []
        
        # 性能配置
        self.temperature_threshold = 83  # RTX 4070安全溫度
        self.memory_threshold = 0.95  # 記憶體使用閾值
        self.utilization_threshold = 0.90  # GPU利用率閾值
        
        # 監控狀態
        self.last_monitor_time = datetime.now()
        self.monitor_interval = 5.0  # 監控間隔秒數
        self.health_status = ResourceStatus.AVAILABLE
        
        # 線程安全
        self._lock = threading.RLock()
        self._monitor_thread = None
        self._monitor_running = False
        
        # 統計信息
        self.stats = {
            'total_allocations': 0,
            'failed_allocations': 0,
            'oom_events': 0,
            'temperature_alerts': 0,
            'avg_allocation_time': 0.0
        }
        
        # 初始化
        self._initialize_gpu_environment()
        self._start_monitoring()
        
        logger.info(f"GPU資源管理器初始化完成 - 設備{device_id}, 總記憶體{max_memory_gb}GB")
    
    def _initialize_gpu_environment(self):
        """初始化GPU環境"""
        try:
            if TORCH_AVAILABLE and torch.cuda.is_available():
                # 設置CUDA環境變數
                os.environ.update({
                    'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:512',
                    'CUDA_LAUNCH_BLOCKING': '0',
                    'TORCH_CUDNN_V8_API_ENABLED': '1'
                })
                
                # PyTorch優化設置
                torch.backends.cudnn.benchmark = True
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                
                # 設置記憶體分配策略
                torch.cuda.set_per_process_memory_fraction(0.90, self.device_id)
                
                logger.info("CUDA環境初始化成功")
            else:
                logger.warning("CUDA不可用，將使用模擬模式")
                
        except Exception as e:
            logger.error(f"GPU環境初始化失敗: {e}")
            self.health_status = ResourceStatus.ERROR
    
    async def allocate_resources(
        self,
        requirement: ResourceRequirement
    ) -> AllocatedResources:
        """
        智能資源分配
        
        Args:
            requirement: 資源需求
            
        Returns:
            分配的資源
            
        Raises:
            InsufficientResourcesError: 資源不足
        """
        async with asyncio.Lock():
            start_time = time.time()
            
            try:
                # 檢查資源可用性
                if not await self._check_resource_availability(requirement):
                    self.stats['failed_allocations'] += 1
                    raise InsufficientResourcesError(
                        f"資源不足: 需要{requirement.memory_gb}GB，"
                        f"可用{self.available_memory_gb:.2f}GB"
                    )
                
                # 檢查GPU健康狀態
                if not await self._check_gpu_health():
                    raise InsufficientResourcesError("GPU健康狀態異常")
                
                # 分配記憶體
                allocated_memory = min(requirement.memory_gb, self.available_memory_gb)
                
                # 配置CUDA設置
                cuda_config = self._configure_cuda_settings(allocated_memory)
                
                # 創建分配記錄
                allocation_id = str(uuid.uuid4())
                expires_at = datetime.now() + timedelta(hours=requirement.max_duration_hours)
                
                allocation = AllocatedResources(
                    allocation_id=allocation_id,
                    memory_gb=allocated_memory,
                    compute_units=requirement.compute_units,
                    allocation_type=requirement.allocation_type,
                    device_id=self.device_id,
                    cuda_config=cuda_config,
                    timestamp=datetime.now(),
                    expires_at=expires_at,
                    status=ResourceStatus.ALLOCATED
                )
                
                # 更新資源狀態
                self.available_memory_gb -= allocated_memory
                self.current_allocations[allocation_id] = allocation
                self.allocation_history.append(allocation)
                
                # 更新統計
                self.stats['total_allocations'] += 1
                allocation_time = time.time() - start_time
                self.stats['avg_allocation_time'] = (
                    (self.stats['avg_allocation_time'] * (self.stats['total_allocations'] - 1) + allocation_time) /
                    self.stats['total_allocations']
                )
                
                logger.info(f"資源分配成功: {allocation_id}, "
                           f"記憶體{allocated_memory:.2f}GB, "
                           f"類型{requirement.allocation_type.value}")
                
                return allocation
                
            except Exception as e:
                logger.error(f"資源分配失敗: {e}")
                raise
    
    async def release_resources(self, allocation_id: str) -> bool:
        """
        釋放資源
        
        Args:
            allocation_id: 分配ID
            
        Returns:
            是否成功釋放
        """
        async with asyncio.Lock():
            try:
                if allocation_id not in self.current_allocations:
                    logger.warning(f"分配ID不存在: {allocation_id}")
                    return False
                
                allocation = self.current_allocations[allocation_id]
                
                # 釋放記憶體
                self.available_memory_gb += allocation.memory_gb
                
                # 更新狀態
                allocation.status = ResourceStatus.AVAILABLE
                
                # 從當前分配中移除
                del self.current_allocations[allocation_id]
                
                logger.info(f"資源釋放成功: {allocation_id}, "
                           f"釋放記憶體{allocation.memory_gb:.2f}GB")
                
                return True
                
            except Exception as e:
                logger.error(f"資源釋放失敗: {e}")
                return False
    
    async def get_gpu_info(self) -> GPUInfo:
        """獲取GPU信息"""
        try:
            if NVML_AVAILABLE:
                handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_id)
                
                # 記憶體信息
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                total_memory_gb = memory_info.total / (1024**3)
                available_memory_gb = memory_info.free / (1024**3)
                memory_usage_percent = (memory_info.used / memory_info.total) * 100
                
                # 溫度
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                # 利用率
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_utilization = utilization.gpu
                
                # 功耗
                power_usage_w = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                
                # 設備名稱
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                
            else:
                # 模擬數據
                total_memory_gb = self.total_memory_gb
                available_memory_gb = self.available_memory_gb
                memory_usage_percent = ((total_memory_gb - available_memory_gb) / total_memory_gb) * 100
                temperature = 65.0  # 模擬溫度
                gpu_utilization = 50.0  # 模擬利用率
                power_usage_w = 150.0  # 模擬功耗
                name = f"RTX_4070_Simulated"
            
            return GPUInfo(
                device_id=self.device_id,
                name=name,
                total_memory_gb=total_memory_gb,
                available_memory_gb=available_memory_gb,
                temperature=temperature,
                utilization=gpu_utilization,
                power_usage_w=power_usage_w,
                memory_usage_percent=memory_usage_percent,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"獲取GPU信息失敗: {e}")
            return GPUInfo(
                device_id=self.device_id,
                name="Unknown",
                total_memory_gb=self.total_memory_gb,
                available_memory_gb=self.available_memory_gb,
                temperature=0.0,
                utilization=0.0,
                power_usage_w=0.0,
                memory_usage_percent=0.0,
                timestamp=datetime.now()
            )
    
    async def optimize_for_rtx4070(self):
        """RTX 4070特定優化"""
        try:
            # 設置環境變數
            os.environ.update({
                'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:512',
                'CUDA_LAUNCH_BLOCKING': '0',
                'TORCH_CUDNN_V8_API_ENABLED': '1'
            })
            
            if TORCH_AVAILABLE:
                # PyTorch優化
                torch.backends.cudnn.benchmark = True
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
                
                # 設置記憶體分配策略
                torch.cuda.set_per_process_memory_fraction(0.90, self.device_id)
                
                logger.info("RTX 4070優化配置完成")
            
        except Exception as e:
            logger.error(f"RTX 4070優化失敗: {e}")
    
    async def _check_resource_availability(self, requirement: ResourceRequirement) -> bool:
        """檢查資源可用性"""
        # 檢查記憶體
        if requirement.memory_gb > self.available_memory_gb:
            return False
        
        # 檢查獨占需求
        if requirement.requires_exclusive and len(self.current_allocations) > 0:
            return False
        
        return True
    
    async def _check_gpu_health(self) -> bool:
        """檢查GPU健康狀態"""
        try:
            gpu_info = await self.get_gpu_info()
            
            # 檢查溫度
            if gpu_info.temperature > self.temperature_threshold:
                self.stats['temperature_alerts'] += 1
                logger.warning(f"GPU溫度過高: {gpu_info.temperature}°C")
                return False
            
            # 檢查記憶體使用率
            if gpu_info.memory_usage_percent > (self.memory_threshold * 100):
                logger.warning(f"GPU記憶體使用率過高: {gpu_info.memory_usage_percent:.1f}%")
                return False
            
            # 檢查利用率
            if gpu_info.utilization > (self.utilization_threshold * 100):
                logger.warning(f"GPU利用率過高: {gpu_info.utilization:.1f}%")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"GPU健康檢查失敗: {e}")
            return False
    
    def _configure_cuda_settings(self, memory_gb: float) -> CudaConfig:
        """配置CUDA設置"""
        memory_fraction = memory_gb / self.total_memory_gb
        
        return CudaConfig(
            device_id=self.device_id,
            memory_fraction=memory_fraction,
            allow_growth=True,
            mixed_precision=True,
            compile_mode=True,
            optimization_level="O2",
            max_memory_allocated=memory_gb * (1024**3)  # 轉換為字節
        )
    
    def _start_monitoring(self):
        """啟動監控線程"""
        if self._monitor_thread is None or not self._monitor_thread.is_alive():
            self._monitor_running = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="GPU-Monitor"
            )
            self._monitor_thread.start()
            logger.info("GPU監控線程啟動")
    
    def _monitor_loop(self):
        """監控循環"""
        while self._monitor_running:
            try:
                # 清理過期分配
                self._cleanup_expired_allocations()
                
                # 檢查OOM風險
                self._check_oom_risk()
                
                # 更新健康狀態
                self._update_health_status()
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"監控循環異常: {e}")
                time.sleep(self.monitor_interval)
    
    def _cleanup_expired_allocations(self):
        """清理過期分配"""
        current_time = datetime.now()
        expired_ids = []
        
        for allocation_id, allocation in self.current_allocations.items():
            if current_time > allocation.expires_at:
                expired_ids.append(allocation_id)
        
        for allocation_id in expired_ids:
            logger.warning(f"強制釋放過期分配: {allocation_id}")
            asyncio.create_task(self.release_resources(allocation_id))
    
    def _check_oom_risk(self):
        """檢查OOM風險"""
        try:
            if TORCH_AVAILABLE and torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated(self.device_id)
                reserved = torch.cuda.memory_reserved(self.device_id)
                total = torch.cuda.get_device_properties(self.device_id).total_memory
                
                usage_ratio = reserved / total
                
                if usage_ratio > 0.95:
                    self.stats['oom_events'] += 1
                    logger.warning(f"OOM風險警告: 記憶體使用率{usage_ratio:.2%}")
                    
                    # 觸發垃圾回收
                    torch.cuda.empty_cache()
                    
        except Exception as e:
            logger.error(f"OOM檢查失敗: {e}")
    
    def _update_health_status(self):
        """更新健康狀態"""
        try:
            gpu_info = asyncio.run(self.get_gpu_info())
            
            if gpu_info.temperature > self.temperature_threshold:
                self.health_status = ResourceStatus.OVERLOADED
            elif gpu_info.memory_usage_percent > (self.memory_threshold * 100):
                self.health_status = ResourceStatus.OVERLOADED
            else:
                self.health_status = ResourceStatus.AVAILABLE
                
        except Exception as e:
            logger.error(f"健康狀態更新失敗: {e}")
            self.health_status = ResourceStatus.ERROR
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            **self.stats,
            'current_allocations': len(self.current_allocations),
            'available_memory_gb': self.available_memory_gb,
            'health_status': self.health_status.value,
            'last_monitor_time': self.last_monitor_time.isoformat()
        }
    
    def shutdown(self):
        """關閉資源管理器"""
        self._monitor_running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5.0)
        
        # 釋放所有資源
        for allocation_id in list(self.current_allocations.keys()):
            asyncio.create_task(self.release_resources(allocation_id))
        
        logger.info("GPU資源管理器已關閉")


# 工廠函數
def create_gpu_resource_manager(device_id: int = 0, max_memory_gb: float = 12.0) -> GPUResourceManager:
    """
    創建GPU資源管理器實例
    
    Args:
        device_id: GPU設備ID
        max_memory_gb: 最大可用記憶體GB
        
    Returns:
        GPU資源管理器實例
    """
    return GPUResourceManager(device_id=device_id, max_memory_gb=max_memory_gb)
