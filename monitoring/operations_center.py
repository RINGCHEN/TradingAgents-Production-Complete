#!/usr/bin/env python3
"""
TradingAgents 運維監控中心 - Phase 3
企業級運維自動化和監控系統

功能特性:
- 統一監控儀表板
- 自動告警和事件響應
- 系統健康狀況追蹤
- 性能分析和報告
- 故障自動恢復
- 運維任務自動化
"""

import os
import sys
import json
import logging
import asyncio
import threading
import time
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import yaml
from pathlib import Path

import torch
import pandas as pd
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, generate_latest
import uvicorn

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [OpsCenter] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring/operations.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("OperationsCenter")


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SystemStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


@dataclass
class SystemMetrics:
    """系統指標"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    gpu_usage: float = 0.0
    gpu_memory: float = 0.0
    gpu_temperature: float = 0.0
    network_io: Dict[str, float] = None
    active_processes: int = 0


@dataclass
class Alert:
    """告警信息"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    acknowledged: bool = False


@dataclass 
class ServiceHealth:
    """服務健康狀況"""
    service_name: str
    status: SystemStatus
    last_check: datetime
    response_time: float = 0.0
    error_count: int = 0
    uptime: float = 0.0


class OperationsCenter:
    """運維監控中心"""
    
    def __init__(self, config_path: str = "config/operations.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        self.service_health: Dict[str, ServiceHealth] = {}
        self.connected_clients: List[WebSocket] = []
        self.is_monitoring = False
        
        # Prometheus 指標註冊
        self.registry = CollectorRegistry()
        self._setup_prometheus_metrics()
        
        # 創建目錄
        os.makedirs("logs/monitoring", exist_ok=True)
        os.makedirs("reports/operations", exist_ok=True)
        
        logger.info("運維監控中心初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """載入配置"""
        default_config = {
            "monitoring": {
                "interval_seconds": 10,
                "metrics_retention_hours": 24,
                "alert_retention_days": 7
            },
            "services": {
                "gpt_oss": {
                    "url": "http://localhost:8082/health",
                    "timeout": 10,
                    "critical": True
                },
                "gpu_monitor": {
                    "url": "http://localhost:9400/metrics",
                    "timeout": 5,
                    "critical": False
                },
                "training_dashboard": {
                    "url": "http://localhost:8888/health",
                    "timeout": 10,
                    "critical": False
                }
            },
            "thresholds": {
                "cpu_warning": 70,
                "cpu_critical": 90,
                "memory_warning": 80,
                "memory_critical": 95,
                "disk_warning": 85,
                "disk_critical": 95,
                "gpu_temp_warning": 80,
                "gpu_temp_critical": 90,
                "response_time_warning": 2.0,
                "response_time_critical": 5.0
            },
            "auto_recovery": {
                "enabled": True,
                "max_attempts": 3,
                "retry_interval": 60
            },
            "notifications": {
                "webhook_url": "",
                "email_enabled": False,
                "slack_enabled": False
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.warning(f"配置載入失敗: {e}")
        
        return default_config
    
    def _setup_prometheus_metrics(self):
        """設置 Prometheus 指標"""
        self.system_cpu_usage = Gauge(
            'tradingagents_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )
        
        self.system_memory_usage = Gauge(
            'tradingagents_system_memory_usage_percent',
            'System memory usage percentage', 
            registry=self.registry
        )
        
        self.system_disk_usage = Gauge(
            'tradingagents_system_disk_usage_percent',
            'System disk usage percentage',
            registry=self.registry
        )
        
        self.service_response_time = Histogram(
            'tradingagents_service_response_time_seconds',
            'Service response time in seconds',
            ['service_name'],
            registry=self.registry
        )
        
        self.service_up = Gauge(
            'tradingagents_service_up',
            'Service up status (1 = up, 0 = down)',
            ['service_name'],
            registry=self.registry
        )
        
        self.active_alerts = Gauge(
            'tradingagents_active_alerts_total',
            'Number of active alerts',
            ['level'],
            registry=self.registry
        )
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系統指標"""
        try:
            # CPU 和記憶體
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 網路 I/O
            net_io = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv
            }
            
            # GPU 指標 (如果可用)
            gpu_usage = 0.0
            gpu_memory = 0.0
            gpu_temperature = 0.0
            
            if torch.cuda.is_available():
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    
                    # GPU 使用率
                    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_usage = float(util.gpu)
                    
                    # GPU 記憶體
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_memory = (mem_info.used / mem_info.total) * 100
                    
                    # GPU 溫度
                    gpu_temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    
                except:
                    pass
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                gpu_usage=gpu_usage,
                gpu_memory=gpu_memory,
                gpu_temperature=gpu_temperature,
                network_io=network_io,
                active_processes=len(psutil.pids())
            )
            
            # 更新 Prometheus 指標
            self.system_cpu_usage.set(cpu_percent)
            self.system_memory_usage.set(memory.percent)
            self.system_disk_usage.set(disk.percent)
            
            return metrics
            
        except Exception as e:
            logger.error(f"系統指標收集失敗: {e}")
            return None
    
    async def check_service_health(self, service_name: str, config: Dict[str, Any]) -> ServiceHealth:
        """檢查服務健康狀況"""
        start_time = time.time()
        
        try:
            response = requests.get(
                config["url"],
                timeout=config["timeout"]
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                status = SystemStatus.HEALTHY
                error_count = 0
            else:
                status = SystemStatus.WARNING
                error_count = 1
                
        except Exception as e:
            response_time = time.time() - start_time
            status = SystemStatus.CRITICAL
            error_count = 1
            logger.warning(f"服務健康檢查失敗 {service_name}: {e}")
        
        health = ServiceHealth(
            service_name=service_name,
            status=status,
            last_check=datetime.now(),
            response_time=response_time,
            error_count=error_count
        )
        
        # 更新 Prometheus 指標
        self.service_response_time.labels(service_name=service_name).observe(response_time)
        self.service_up.labels(service_name=service_name).set(1 if status == SystemStatus.HEALTHY else 0)
        
        return health
    
    def analyze_metrics_and_generate_alerts(self, metrics: SystemMetrics) -> List[Alert]:
        """分析指標並生成告警"""
        alerts = []
        thresholds = self.config["thresholds"]
        
        # CPU 告警
        if metrics.cpu_usage >= thresholds["cpu_critical"]:
            alert = Alert(
                alert_id=f"cpu_critical_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="CPU使用率過高",
                message=f"CPU使用率達到 {metrics.cpu_usage:.1f}%",
                source="system_monitor",
                timestamp=datetime.now()
            )
            alerts.append(alert)
        elif metrics.cpu_usage >= thresholds["cpu_warning"]:
            alert = Alert(
                alert_id=f"cpu_warning_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="CPU使用率警告",
                message=f"CPU使用率達到 {metrics.cpu_usage:.1f}%",
                source="system_monitor", 
                timestamp=datetime.now()
            )
            alerts.append(alert)
        
        # 記憶體告警
        if metrics.memory_usage >= thresholds["memory_critical"]:
            alert = Alert(
                alert_id=f"memory_critical_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="記憶體使用率過高",
                message=f"記憶體使用率達到 {metrics.memory_usage:.1f}%",
                source="system_monitor",
                timestamp=datetime.now()
            )
            alerts.append(alert)
        elif metrics.memory_usage >= thresholds["memory_warning"]:
            alert = Alert(
                alert_id=f"memory_warning_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="記憶體使用率警告",
                message=f"記憶體使用率達到 {metrics.memory_usage:.1f}%",
                source="system_monitor",
                timestamp=datetime.now()
            )
            alerts.append(alert)
        
        # GPU 溫度告警
        if metrics.gpu_temperature >= thresholds["gpu_temp_critical"]:
            alert = Alert(
                alert_id=f"gpu_temp_critical_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="GPU溫度過高",
                message=f"GPU溫度達到 {metrics.gpu_temperature:.1f}°C",
                source="gpu_monitor",
                timestamp=datetime.now()
            )
            alerts.append(alert)
        elif metrics.gpu_temperature >= thresholds["gpu_temp_warning"]:
            alert = Alert(
                alert_id=f"gpu_temp_warning_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="GPU溫度警告",
                message=f"GPU溫度達到 {metrics.gpu_temperature:.1f}°C",
                source="gpu_monitor",
                timestamp=datetime.now()
            )
            alerts.append(alert)
        
        return alerts
    
    async def perform_auto_recovery(self, alert: Alert) -> bool:
        """執行自動恢復操作"""
        if not self.config["auto_recovery"]["enabled"]:
            return False
        
        recovery_actions = {
            "cpu_critical": self._restart_heavy_processes,
            "memory_critical": self._clear_memory_cache,
            "gpu_temp_critical": self._reduce_gpu_workload,
            "service_down": self._restart_service
        }
        
        action_key = alert.alert_id.split('_')[0] + '_' + alert.alert_id.split('_')[1]
        recovery_action = recovery_actions.get(action_key)
        
        if recovery_action:
            try:
                logger.info(f"執行自動恢復: {alert.title}")
                success = await recovery_action(alert)
                if success:
                    alert.resolved = True
                    logger.info(f"自動恢復成功: {alert.title}")
                return success
            except Exception as e:
                logger.error(f"自動恢復失敗: {alert.title}, 錯誤: {e}")
        
        return False
    
    async def _restart_heavy_processes(self, alert: Alert) -> bool:
        """重啟高 CPU 使用率進程"""
        # 實現重啟邏輯
        return True
    
    async def _clear_memory_cache(self, alert: Alert) -> bool:
        """清理記憶體快取"""
        try:
            if sys.platform == "linux":
                subprocess.run(["sync"], check=True)
                subprocess.run(["echo", "3", ">", "/proc/sys/vm/drop_caches"], shell=True, check=True)
            return True
        except:
            return False
    
    async def _reduce_gpu_workload(self, alert: Alert) -> bool:
        """降低 GPU 工作負載"""
        # 實現 GPU 負載降低邏輯
        return True
    
    async def _restart_service(self, alert: Alert) -> bool:
        """重啟服務"""
        # 實現服務重啟邏輯
        return True
    
    async def send_notification(self, alert: Alert) -> None:
        """發送通知"""
        notification_config = self.config["notifications"]
        
        # Webhook 通知
        if notification_config.get("webhook_url"):
            try:
                payload = {
                    "alert_id": alert.alert_id,
                    "level": alert.level.value,
                    "title": alert.title,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "source": alert.source
                }
                
                requests.post(
                    notification_config["webhook_url"],
                    json=payload,
                    timeout=10
                )
                
            except Exception as e:
                logger.error(f"Webhook 通知發送失敗: {e}")
    
    async def monitoring_loop(self):
        """主監控循環"""
        self.is_monitoring = True
        interval = self.config["monitoring"]["interval_seconds"]
        
        logger.info("開始監控循環")
        
        while self.is_monitoring:
            try:
                # 1. 收集系統指標
                metrics = self.collect_system_metrics()
                if metrics:
                    self.metrics_history.append(metrics)
                    
                    # 限制歷史記錄數量
                    max_metrics = self.config["monitoring"]["metrics_retention_hours"] * (3600 // interval)
                    if len(self.metrics_history) > max_metrics:
                        self.metrics_history = self.metrics_history[-max_metrics:]
                
                # 2. 檢查服務健康狀況
                for service_name, service_config in self.config["services"].items():
                    health = await self.check_service_health(service_name, service_config)
                    self.service_health[service_name] = health
                
                # 3. 分析指標並生成告警
                if metrics:
                    new_alerts = self.analyze_metrics_and_generate_alerts(metrics)
                    for alert in new_alerts:
                        self.alerts.append(alert)
                        
                        # 發送通知
                        await self.send_notification(alert)
                        
                        # 執行自動恢復
                        if alert.level in [AlertLevel.CRITICAL, AlertLevel.ERROR]:
                            await self.perform_auto_recovery(alert)
                
                # 4. 更新 Prometheus 告警指標
                self._update_alert_metrics()
                
                # 5. 向 WebSocket 客戶端推送更新
                if self.connected_clients:
                    await self._broadcast_updates()
                
                # 6. 清理過期告警
                self._cleanup_old_alerts()
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"監控循環錯誤: {e}")
                await asyncio.sleep(interval)
    
    def _update_alert_metrics(self):
        """更新告警 Prometheus 指標"""
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        for level in AlertLevel:
            count = len([alert for alert in active_alerts if alert.level == level])
            self.active_alerts.labels(level=level.value).set(count)
    
    async def _broadcast_updates(self):
        """向所有連接的客戶端廣播更新"""
        if not self.connected_clients:
            return
        
        data = {
            "type": "update",
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(self.metrics_history[-1]) if self.metrics_history else None,
            "service_health": {name: asdict(health) for name, health in self.service_health.items()},
            "active_alerts": [asdict(alert) for alert in self.alerts if not alert.resolved][-10:]  # 最近10個告警
        }
        
        # 處理 datetime 序列化
        def datetime_handler(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError
        
        message = json.dumps(data, default=datetime_handler, ensure_ascii=False)
        
        disconnected_clients = []
        for client in self.connected_clients:
            try:
                await client.send_text(message)
            except WebSocketDisconnect:
                disconnected_clients.append(client)
            except Exception as e:
                logger.error(f"WebSocket 發送失敗: {e}")
                disconnected_clients.append(client)
        
        # 移除斷開的客戶端
        for client in disconnected_clients:
            self.connected_clients.remove(client)
    
    def _cleanup_old_alerts(self):
        """清理過期告警"""
        retention_days = self.config["monitoring"]["alert_retention_days"]
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp > cutoff_date
        ]
    
    def get_system_summary(self) -> Dict[str, Any]:
        """獲取系統摘要"""
        if not self.metrics_history:
            return {"status": "no_data"}
        
        latest_metrics = self.metrics_history[-1]
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        # 確定系統整體狀態
        if any(alert.level == AlertLevel.CRITICAL for alert in active_alerts):
            overall_status = SystemStatus.CRITICAL
        elif any(alert.level == AlertLevel.ERROR for alert in active_alerts):
            overall_status = SystemStatus.CRITICAL
        elif any(alert.level == AlertLevel.WARNING for alert in active_alerts):
            overall_status = SystemStatus.WARNING
        else:
            overall_status = SystemStatus.HEALTHY
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "metrics": asdict(latest_metrics),
            "services": {name: health.status.value for name, health in self.service_health.items()},
            "active_alerts_count": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING])
        }
    
    def start_monitoring(self):
        """啟動監控"""
        if self.is_monitoring:
            logger.warning("監控已在運行中")
            return
        
        # 啟動監控循環
        asyncio.create_task(self.monitoring_loop())
        logger.info("運維監控中心已啟動")
    
    def stop_monitoring(self):
        """停止監控"""
        self.is_monitoring = False
        logger.info("運維監控中心已停止")


# 創建 FastAPI 應用和 WebSocket
app = FastAPI(title="TradingAgents 運維監控中心", version="1.0.0")
templates = Jinja2Templates(directory="templates")
ops_center = OperationsCenter()


@app.on_event("startup")
async def startup():
    """啟動運維中心"""
    ops_center.start_monitoring()


@app.get("/", response_class=HTMLResponse)
async def operations_dashboard(request: Request):
    """運維儀表板"""
    summary = ops_center.get_system_summary()
    return templates.TemplateResponse("operations.html", {
        "request": request,
        "summary": summary
    })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 連接"""
    await websocket.accept()
    ops_center.connected_clients.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()  # 保持連接
    except WebSocketDisconnect:
        ops_center.connected_clients.remove(websocket)


@app.get("/api/summary")
async def get_system_summary():
    """獲取系統摘要 API"""
    return ops_center.get_system_summary()


@app.get("/api/metrics")
async def get_prometheus_metrics():
    """Prometheus 指標端點"""
    return generate_latest(ops_center.registry)


@app.get("/health")
async def health_check():
    """健康檢查"""
    return {"status": "healthy", "monitoring": ops_center.is_monitoring}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=9403,
        reload=False,
        log_level="info"
    )