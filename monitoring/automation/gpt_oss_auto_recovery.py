#!/usr/bin/env python3
"""
GPT-OSS 自動化運維和恢復腳本
TradingAgents AI Phase 2 - 智能運維系統
"""

import os
import time
import logging
import subprocess
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


@dataclass
class HealthCheckResult:
    """健康檢查結果"""
    service_name: str
    status: str  # 'healthy', 'unhealthy', 'critical'
    response_time: Optional[float]
    error_message: Optional[str]
    metrics: Dict[str, float]
    timestamp: datetime


@dataclass
class AutomationConfig:
    """自動化配置"""
    check_interval: int = 30  # 檢查間隔(秒)
    max_restart_attempts: int = 3  # 最大重啟次數
    restart_cooldown: int = 300  # 重啟冷卻時間(秒)
    critical_memory_threshold: float = 95.0  # 關鍵記憶體閾值(%)
    critical_temperature_threshold: float = 85.0  # 關鍵溫度閾值(°C)
    max_response_time: float = 15.0  # 最大響應時間(秒)
    notification_enabled: bool = True
    auto_restart_enabled: bool = True
    backup_model_enabled: bool = True


class GPTOSSAutomation:
    """GPT-OSS 自動化運維系統"""
    
    def __init__(self, config: AutomationConfig):
        self.config = config
        self.restart_history: Dict[str, List[datetime]] = {}
        self.last_check_time = datetime.now()
        self.service_states: Dict[str, str] = {}
        
        # 設置日誌
        self.setup_logging()
        
        # 服務端點配置
        self.endpoints = {
            'gpt-oss': 'http://localhost:8080',
            'prometheus': 'http://localhost:9090',
            'grafana': 'http://localhost:3000'
        }
        
        # 通知配置
        self.notification_config = self.load_notification_config()
    
    def setup_logging(self):
        """設置日誌系統"""
        log_dir = Path("C:/Users/Ring/Documents/GitHub/twstock/TradingAgents/logs/automation")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("GPT-OSS Automation System initialized")
    
    def load_notification_config(self) -> Dict:
        """載入通知配置"""
        config_path = Path("C:/Users/Ring/Documents/GitHub/twstock/TradingAgents/monitoring/notification_config.json")
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load notification config: {e}")
        
        # 默認配置
        return {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipients": []
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "headers": {}
            }
        }
    
    def check_service_health(self, service_name: str, endpoint: str) -> HealthCheckResult:
        """檢查服務健康狀態"""
        start_time = time.time()
        
        try:
            if service_name == 'gpt-oss':
                return self.check_gpt_oss_health(endpoint, start_time)
            elif service_name == 'prometheus':
                return self.check_prometheus_health(endpoint, start_time)
            elif service_name == 'grafana':
                return self.check_grafana_health(endpoint, start_time)
            else:
                return self.check_generic_health(service_name, endpoint, start_time)
                
        except Exception as e:
            response_time = time.time() - start_time
            return HealthCheckResult(
                service_name=service_name,
                status='critical',
                response_time=response_time,
                error_message=str(e),
                metrics={},
                timestamp=datetime.now()
            )
    
    def check_gpt_oss_health(self, endpoint: str, start_time: float) -> HealthCheckResult:
        """檢查 GPT-OSS 服務健康狀態"""
        health_url = f"{endpoint}/health"
        metrics_url = f"{endpoint}/metrics"
        
        # 檢查健康端點
        response = requests.get(health_url, timeout=10)
        response_time = time.time() - start_time
        
        if response.status_code != 200:
            return HealthCheckResult(
                service_name='gpt-oss',
                status='unhealthy',
                response_time=response_time,
                error_message=f"HTTP {response.status_code}",
                metrics={},
                timestamp=datetime.now()
            )\n        \n        # 獲取詳細指標\n        metrics = {}\n        try:\n            metrics_response = requests.get(metrics_url, timeout=5)\n            if metrics_response.status_code == 200:\n                # 解析 Prometheus 格式指標\n                metrics = self.parse_prometheus_metrics(metrics_response.text)\n        except:\n            pass\n        \n        # 檢查關鍵指標\n        status = 'healthy'\n        error_message = None\n        \n        # 檢查響應時間\n        if response_time > self.config.max_response_time:\n            status = 'unhealthy'\n            error_message = f\"Response time too high: {response_time:.2f}s\"\n        \n        # 檢查 GPU 記憶體\n        if 'gpu_memory_utilization_percent' in metrics:\n            gpu_memory = metrics['gpu_memory_utilization_percent']\n            if gpu_memory > self.config.critical_memory_threshold:\n                status = 'critical'\n                error_message = f\"GPU memory critical: {gpu_memory:.1f}%\"\n        \n        # 檢查 GPU 溫度\n        if 'gpu_temperature_celsius' in metrics:\n            gpu_temp = metrics['gpu_temperature_celsius']\n            if gpu_temp > self.config.critical_temperature_threshold:\n                status = 'critical'\n                error_message = f\"GPU temperature critical: {gpu_temp:.1f}°C\"\n        \n        return HealthCheckResult(\n            service_name='gpt-oss',\n            status=status,\n            response_time=response_time,\n            error_message=error_message,\n            metrics=metrics,\n            timestamp=datetime.now()\n        )\n    \n    def check_prometheus_health(self, endpoint: str, start_time: float) -> HealthCheckResult:\n        \"\"\"檢查 Prometheus 健康狀態\"\"\"\n        health_url = f\"{endpoint}/-/healthy\"\n        \n        response = requests.get(health_url, timeout=10)\n        response_time = time.time() - start_time\n        \n        status = 'healthy' if response.status_code == 200 else 'unhealthy'\n        error_message = None if status == 'healthy' else f\"HTTP {response.status_code}\"\n        \n        return HealthCheckResult(\n            service_name='prometheus',\n            status=status,\n            response_time=response_time,\n            error_message=error_message,\n            metrics={},\n            timestamp=datetime.now()\n        )\n    \n    def check_grafana_health(self, endpoint: str, start_time: float) -> HealthCheckResult:\n        \"\"\"檢查 Grafana 健康狀態\"\"\"\n        health_url = f\"{endpoint}/api/health\"\n        \n        response = requests.get(health_url, timeout=10)\n        response_time = time.time() - start_time\n        \n        status = 'healthy' if response.status_code == 200 else 'unhealthy'\n        error_message = None if status == 'healthy' else f\"HTTP {response.status_code}\"\n        \n        return HealthCheckResult(\n            service_name='grafana',\n            status=status,\n            response_time=response_time,\n            error_message=error_message,\n            metrics={},\n            timestamp=datetime.now()\n        )\n    \n    def check_generic_health(self, service_name: str, endpoint: str, start_time: float) -> HealthCheckResult:\n        \"\"\"通用服務健康檢查\"\"\"\n        response = requests.get(endpoint, timeout=10)\n        response_time = time.time() - start_time\n        \n        status = 'healthy' if response.status_code == 200 else 'unhealthy'\n        error_message = None if status == 'healthy' else f\"HTTP {response.status_code}\"\n        \n        return HealthCheckResult(\n            service_name=service_name,\n            status=status,\n            response_time=response_time,\n            error_message=error_message,\n            metrics={},\n            timestamp=datetime.now()\n        )\n    \n    def parse_prometheus_metrics(self, metrics_text: str) -> Dict[str, float]:\n        \"\"\"解析 Prometheus 格式的指標\"\"\"\n        metrics = {}\n        \n        for line in metrics_text.split('\\n'):\n            line = line.strip()\n            if not line or line.startswith('#'):\n                continue\n            \n            try:\n                if ' ' in line:\n                    metric_name, value = line.rsplit(' ', 1)\n                    # 移除標籤\n                    if '{' in metric_name:\n                        metric_name = metric_name.split('{')[0]\n                    metrics[metric_name] = float(value)\n            except:\n                continue\n        \n        return metrics\n    \n    def restart_service(self, service_name: str) -> bool:\n        \"\"\"重啟服務\"\"\"\n        if not self.config.auto_restart_enabled:\n            self.logger.info(f\"Auto restart disabled, skipping restart for {service_name}\")\n            return False\n        \n        # 檢查重啟歷史\n        now = datetime.now()\n        if service_name not in self.restart_history:\n            self.restart_history[service_name] = []\n        \n        # 清理舊的重啟記錄\n        cutoff_time = now - timedelta(hours=1)\n        self.restart_history[service_name] = [\n            restart_time for restart_time in self.restart_history[service_name]\n            if restart_time > cutoff_time\n        ]\n        \n        # 檢查是否超過最大重啟次數\n        if len(self.restart_history[service_name]) >= self.config.max_restart_attempts:\n            self.logger.error(f\"Max restart attempts reached for {service_name}\")\n            return False\n        \n        # 檢查冷卻時間\n        if self.restart_history[service_name]:\n            last_restart = self.restart_history[service_name][-1]\n            if (now - last_restart).total_seconds() < self.config.restart_cooldown:\n                self.logger.info(f\"Service {service_name} is in restart cooldown\")\n                return False\n        \n        self.logger.info(f\"Attempting to restart {service_name}\")\n        \n        try:\n            if service_name == 'gpt-oss':\n                result = self.restart_gpt_oss()\n            elif service_name == 'prometheus':\n                result = self.restart_prometheus()\n            elif service_name == 'grafana':\n                result = self.restart_grafana()\n            else:\n                result = False\n            \n            if result:\n                self.restart_history[service_name].append(now)\n                self.logger.info(f\"Successfully restarted {service_name}\")\n            else:\n                self.logger.error(f\"Failed to restart {service_name}\")\n            \n            return result\n            \n        except Exception as e:\n            self.logger.error(f\"Error restarting {service_name}: {e}\")\n            return False\n    \n    def restart_gpt_oss(self) -> bool:\n        \"\"\"重啟 GPT-OSS 服務\"\"\"\n        try:\n            # 停止現有服務\n            subprocess.run([\"taskkill\", \"/f\", \"/im\", \"python.exe\", \"/fi\", \"WINDOWTITLE eq GPT-OSS*\"], \n                         capture_output=True, check=False)\n            \n            # 等待服務完全停止\n            time.sleep(5)\n            \n            # 啟動新服務\n            gpt_oss_dir = Path(\"C:/Users/Ring/Documents/GitHub/twstock/TradingAgents/gpt_oss\")\n            start_script = gpt_oss_dir / \"start_gpt_oss.bat\"\n            \n            if start_script.exists():\n                subprocess.Popen([str(start_script)], cwd=str(gpt_oss_dir), shell=True)\n                return True\n            else:\n                # 使用 Python 直接啟動\n                subprocess.Popen([\"python\", \"server.py\"], cwd=str(gpt_oss_dir))\n                return True\n                \n        except Exception as e:\n            self.logger.error(f\"Failed to restart GPT-OSS: {e}\")\n            return False\n    \n    def restart_prometheus(self) -> bool:\n        \"\"\"重啟 Prometheus 服務\"\"\"\n        try:\n            # 使用 Docker Compose 重啟\n            monitoring_dir = Path(\"C:/Users/Ring/Documents/GitHub/twstock/TradingAgents/monitoring\")\n            subprocess.run([\"docker-compose\", \"-f\", \"docker-compose.monitoring.yml\", \n                          \"restart\", \"prometheus\"], cwd=str(monitoring_dir), check=True)\n            return True\n        except:\n            return False\n    \n    def restart_grafana(self) -> bool:\n        \"\"\"重啟 Grafana 服務\"\"\"\n        try:\n            monitoring_dir = Path(\"C:/Users/Ring/Documents/GitHub/twstock/TradingAgents/monitoring\")\n            subprocess.run([\"docker-compose\", \"-f\", \"docker-compose.monitoring.yml\", \n                          \"restart\", \"grafana\"], cwd=str(monitoring_dir), check=True)\n            return True\n        except:\n            return False\n    \n    def send_notification(self, health_result: HealthCheckResult):\n        \"\"\"發送通知\"\"\"\n        if not self.config.notification_enabled:\n            return\n        \n        message = self.format_notification_message(health_result)\n        \n        # 發送郵件通知\n        if self.notification_config[\"email\"][\"enabled\"]:\n            self.send_email_notification(message, health_result)\n        \n        # 發送 Webhook 通知\n        if self.notification_config[\"webhook\"][\"enabled\"]:\n            self.send_webhook_notification(message, health_result)\n    \n    def format_notification_message(self, health_result: HealthCheckResult) -> str:\n        \"\"\"格式化通知訊息\"\"\"\n        status_emoji = {\n            'healthy': '✅',\n            'unhealthy': '⚠️',\n            'critical': '🚨'\n        }\n        \n        emoji = status_emoji.get(health_result.status, '❓')\n        \n        message = f\"\"\"\n{emoji} TradingAgents AI Phase 2 - 服務狀態通知\n\n服務名稱: {health_result.service_name}\n狀態: {health_result.status.upper()}\n檢查時間: {health_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n響應時間: {health_result.response_time:.3f}s\n\"\"\"\n        \n        if health_result.error_message:\n            message += f\"錯誤訊息: {health_result.error_message}\\n\"\n        \n        if health_result.metrics:\n            message += \"\\n關鍵指標:\\n\"\n            for key, value in health_result.metrics.items():\n                if 'temperature' in key.lower():\n                    message += f\"  {key}: {value:.1f}°C\\n\"\n                elif 'memory' in key.lower() and 'percent' in key.lower():\n                    message += f\"  {key}: {value:.1f}%\\n\"\n                elif 'utilization' in key.lower():\n                    message += f\"  {key}: {value:.1f}%\\n\"\n                else:\n                    message += f\"  {key}: {value:.3f}\\n\"\n        \n        return message\n    \n    def send_email_notification(self, message: str, health_result: HealthCheckResult):\n        \"\"\"發送郵件通知\"\"\"\n        try:\n            config = self.notification_config[\"email\"]\n            \n            msg = MIMEMultipart()\n            msg['From'] = config[\"sender_email\"]\n            msg['To'] = \", \".join(config[\"recipients\"])\n            msg['Subject'] = f\"TradingAgents AI - {health_result.service_name} {health_result.status.upper()}\"\n            \n            msg.attach(MIMEText(message, 'plain', 'utf-8'))\n            \n            server = smtplib.SMTP(config[\"smtp_server\"], config[\"smtp_port\"])\n            server.starttls()\n            server.login(config[\"sender_email\"], config[\"sender_password\"])\n            server.send_message(msg)\n            server.quit()\n            \n            self.logger.info(\"Email notification sent successfully\")\n            \n        except Exception as e:\n            self.logger.error(f\"Failed to send email notification: {e}\")\n    \n    def send_webhook_notification(self, message: str, health_result: HealthCheckResult):\n        \"\"\"發送 Webhook 通知\"\"\"\n        try:\n            config = self.notification_config[\"webhook\"]\n            \n            payload = {\n                \"service\": health_result.service_name,\n                \"status\": health_result.status,\n                \"timestamp\": health_result.timestamp.isoformat(),\n                \"response_time\": health_result.response_time,\n                \"error_message\": health_result.error_message,\n                \"metrics\": health_result.metrics,\n                \"message\": message\n            }\n            \n            headers = {\"Content-Type\": \"application/json\"}\n            headers.update(config.get(\"headers\", {}))\n            \n            response = requests.post(config[\"url\"], json=payload, headers=headers, timeout=10)\n            response.raise_for_status()\n            \n            self.logger.info(\"Webhook notification sent successfully\")\n            \n        except Exception as e:\n            self.logger.error(f\"Failed to send webhook notification: {e}\")\n    \n    def run_health_check_cycle(self):\n        \"\"\"執行一輪健康檢查循環\"\"\"\n        self.logger.info(\"Starting health check cycle\")\n        \n        for service_name, endpoint in self.endpoints.items():\n            try:\n                health_result = self.check_service_health(service_name, endpoint)\n                \n                # 記錄結果\n                self.logger.info(\n                    f\"{service_name}: {health_result.status} \"\n                    f\"({health_result.response_time:.3f}s)\"\n                )\n                \n                # 檢查是否需要採取行動\n                previous_status = self.service_states.get(service_name)\n                self.service_states[service_name] = health_result.status\n                \n                # 狀態變化或處於不健康狀態時發送通知\n                if (health_result.status != 'healthy' and \n                    (previous_status != health_result.status or health_result.status == 'critical')):\n                    self.send_notification(health_result)\n                \n                # 自動重啟邏輯\n                if health_result.status in ['unhealthy', 'critical']:\n                    if service_name == 'gpt-oss':  # 只自動重啟 GPT-OSS 服務\n                        restart_success = self.restart_service(service_name)\n                        if restart_success:\n                            # 重啟後等待並再次檢查\n                            time.sleep(30)\n                            recheck_result = self.check_service_health(service_name, endpoint)\n                            if recheck_result.status == 'healthy':\n                                self.logger.info(f\"Service {service_name} recovered after restart\")\n                            else:\n                                self.logger.warning(f\"Service {service_name} still unhealthy after restart\")\n                \n            except Exception as e:\n                self.logger.error(f\"Error checking {service_name}: {e}\")\n    \n    def run(self):\n        \"\"\"運行自動化系統\"\"\"\n        self.logger.info(\"Starting GPT-OSS Automation System\")\n        \n        try:\n            while True:\n                self.run_health_check_cycle()\n                time.sleep(self.config.check_interval)\n                \n        except KeyboardInterrupt:\n            self.logger.info(\"Automation system stopped by user\")\n        except Exception as e:\n            self.logger.error(f\"Unexpected error in automation system: {e}\")\n            raise\n\n\ndef main():\n    \"\"\"主函數\"\"\"\n    config = AutomationConfig(\n        check_interval=30,\n        max_restart_attempts=3,\n        restart_cooldown=300,\n        critical_memory_threshold=95.0,\n        critical_temperature_threshold=85.0,\n        max_response_time=15.0,\n        notification_enabled=True,\n        auto_restart_enabled=True,\n        backup_model_enabled=True\n    )\n    \n    automation = GPTOSSAutomation(config)\n    automation.run()\n\n\nif __name__ == \"__main__\":\n    main()