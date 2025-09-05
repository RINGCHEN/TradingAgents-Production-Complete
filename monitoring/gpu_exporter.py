#!/usr/bin/env python3
"""
GPU Metrics Exporter for Prometheus
專為 TradingAgents GPT-OSS Phase 2 設計
"""

import time
import logging
import threading
from typing import Dict, Optional
from dataclasses import dataclass
from prometheus_client import start_http_server, Gauge, Counter, Histogram
from prometheus_client.core import CollectorRegistry

try:
    import pynvml
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False
    logging.warning("pynvml not available, GPU metrics will not be collected")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available, system metrics will be limited")


@dataclass
class GPUMetrics:
    """GPU 指標數據結構"""
    gpu_id: int
    name: str
    temperature: float
    memory_total: int
    memory_used: int
    memory_free: int
    utilization_gpu: float
    utilization_memory: float
    power_draw: float
    power_limit: float
    fan_speed: Optional[float] = None
    clock_graphics: Optional[int] = None
    clock_memory: Optional[int] = None


class GPUExporter:
    """GPU Prometheus Exporter"""
    
    def __init__(self, port: int = 9400, interval: int = 5):
        self.port = port
        self.interval = interval
        self.registry = CollectorRegistry()
        
        # 初始化 GPU 監控
        self.gpu_available = False
        if NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.device_count = pynvml.nvmlDeviceGetCount()
                self.gpu_available = True
                logging.info(f"Found {self.device_count} GPU devices")
            except Exception as e:
                logging.error(f"Failed to initialize NVML: {e}")
        
        # Prometheus 指標定義
        self._setup_metrics()
        
        # 運行狀態
        self.running = False
        
    def _setup_metrics(self):
        """設置 Prometheus 指標"""
        
        # GPU 基礎指標
        self.gpu_temperature = Gauge(
            'gpu_temperature_celsius', 
            'GPU temperature in Celsius',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        self.gpu_memory_total = Gauge(
            'gpu_memory_total_bytes',
            'Total GPU memory in bytes',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        self.gpu_memory_used = Gauge(
            'gpu_memory_used_bytes',
            'Used GPU memory in bytes',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        self.gpu_memory_utilization = Gauge(
            'gpu_memory_utilization_percent',
            'GPU memory utilization percentage',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        self.gpu_utilization = Gauge(
            'gpu_utilization_percent',
            'GPU utilization percentage',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        self.gpu_power_draw = Gauge(
            'gpu_power_draw_watts',
            'GPU power consumption in watts',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        self.gpu_power_limit = Gauge(
            'gpu_power_limit_watts',
            'GPU power limit in watts',
            ['gpu_id', 'gpu_name'],
            registry=self.registry
        )
        
        # GPT-OSS 特定指標
        self.gpt_oss_inference_time = Histogram(
            'gpt_oss_inference_duration_seconds',
            'Time spent on inference',
            ['model_name'],
            registry=self.registry
        )
        
        self.gpt_oss_memory_peak = Gauge(
            'gpt_oss_memory_peak_bytes',
            'Peak memory usage during inference',
            ['model_name'],
            registry=self.registry
        )
        
        self.gpt_oss_active_requests = Gauge(
            'gpt_oss_active_requests',
            'Number of active inference requests',
            registry=self.registry
        )
        
        self.gpt_oss_queue_size = Gauge(
            'gpt_oss_queue_size',
            'Number of requests in queue',
            registry=self.registry
        )
        
        # 系統指標
        if PSUTIL_AVAILABLE:
            self.system_cpu_percent = Gauge(
                'system_cpu_percent',
                'System CPU usage percentage',
                registry=self.registry
            )
            
            self.system_memory_percent = Gauge(
                'system_memory_percent',
                'System memory usage percentage',
                registry=self.registry
            )
            
            self.system_disk_io_read = Counter(
                'system_disk_io_read_bytes_total',
                'Total disk read bytes',
                registry=self.registry
            )
            
            self.system_disk_io_write = Counter(
                'system_disk_io_write_bytes_total',
                'Total disk write bytes',
                registry=self.registry
            )
    
    def collect_gpu_metrics(self) -> Dict[int, GPUMetrics]:
        """收集 GPU 指標"""
        metrics = {}
        
        if not self.gpu_available:
            return metrics
            
        try:
            for i in range(self.device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # 基礎資訊
                name = pynvml.nvmlDeviceGetName(handle)
                if isinstance(name, bytes):
                    name = name.decode('utf-8')
                
                # 溫度
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    temp = 0.0
                
                # 記憶體資訊
                try:
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_total = mem_info.total
                    memory_used = mem_info.used
                    memory_free = mem_info.free
                except:
                    memory_total = memory_used = memory_free = 0
                
                # 使用率
                try:
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_util = float(util.gpu)
                    mem_util = float(util.memory)
                except:
                    gpu_util = mem_util = 0.0
                
                # 功耗
                try:
                    power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
                except:
                    power_draw = 0.0
                
                try:
                    power_limit = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[1] / 1000.0
                except:
                    power_limit = 0.0
                
                # 風扇轉速 (可選)
                try:
                    fan_speed = pynvml.nvmlDeviceGetFanSpeed(handle)
                except:
                    fan_speed = None
                
                # 時鐘頻率 (可選)
                try:
                    clock_graphics = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                    clock_memory = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                except:
                    clock_graphics = clock_memory = None
                
                metrics[i] = GPUMetrics(
                    gpu_id=i,
                    name=name,
                    temperature=temp,
                    memory_total=memory_total,
                    memory_used=memory_used,
                    memory_free=memory_free,
                    utilization_gpu=gpu_util,
                    utilization_memory=mem_util,
                    power_draw=power_draw,
                    power_limit=power_limit,
                    fan_speed=fan_speed,
                    clock_graphics=clock_graphics,
                    clock_memory=clock_memory
                )
                
        except Exception as e:
            logging.error(f"Error collecting GPU metrics: {e}")
            
        return metrics
    
    def collect_system_metrics(self):
        """收集系統指標"""
        if not PSUTIL_AVAILABLE:
            return
            
        try:
            # CPU 使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_percent.set(cpu_percent)
            
            # 記憶體使用率
            memory = psutil.virtual_memory()
            self.system_memory_percent.set(memory.percent)
            
            # 磁碟 I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                self.system_disk_io_read._value._value = disk_io.read_bytes
                self.system_disk_io_write._value._value = disk_io.write_bytes
                
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
    
    def update_metrics(self):
        """更新所有指標"""
        # 收集 GPU 指標
        gpu_metrics = self.collect_gpu_metrics()
        
        for gpu_id, metrics in gpu_metrics.items():
            labels = [str(gpu_id), metrics.name]
            
            self.gpu_temperature.labels(*labels).set(metrics.temperature)
            self.gpu_memory_total.labels(*labels).set(metrics.memory_total)
            self.gpu_memory_used.labels(*labels).set(metrics.memory_used)
            
            # 計算記憶體使用率百分比
            if metrics.memory_total > 0:
                mem_percent = (metrics.memory_used / metrics.memory_total) * 100
                self.gpu_memory_utilization.labels(*labels).set(mem_percent)
            
            self.gpu_utilization.labels(*labels).set(metrics.utilization_gpu)
            self.gpu_power_draw.labels(*labels).set(metrics.power_draw)
            self.gpu_power_limit.labels(*labels).set(metrics.power_limit)
        
        # 收集系統指標
        self.collect_system_metrics()
        
        logging.debug(f"Updated metrics for {len(gpu_metrics)} GPUs")
    
    def run_metrics_loop(self):
        """運行指標收集循環"""
        logging.info(f"Starting metrics collection loop (interval: {self.interval}s)")
        
        while self.running:
            try:
                self.update_metrics()
                time.sleep(self.interval)
            except Exception as e:
                logging.error(f"Error in metrics loop: {e}")
                time.sleep(self.interval)
    
    def start(self):
        """啟動 Exporter"""
        if self.running:
            logging.warning("Exporter is already running")
            return
            
        self.running = True
        
        # 啟動 Prometheus HTTP 服務器
        start_http_server(self.port, registry=self.registry)
        logging.info(f"GPU Exporter started on port {self.port}")
        
        # 啟動指標收集線程
        self.metrics_thread = threading.Thread(target=self.run_metrics_loop, daemon=True)
        self.metrics_thread.start()
        
        logging.info("GPU Exporter is running")
    
    def stop(self):
        """停止 Exporter"""
        self.running = False
        logging.info("GPU Exporter stopped")


def main():
    """主函數"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 創建並啟動 GPU Exporter
    exporter = GPUExporter(port=9400, interval=5)
    
    try:
        exporter.start()
        
        # 保持運行
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logging.info("Received interrupt signal")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        exporter.stop()


if __name__ == "__main__":
    main()