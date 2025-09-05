#!/usr/bin/env python3
"""
部署管理器 (Deployment Manager)
天工開物系統的核心部署配置和管理

此模組提供：
1. 多環境部署配置
2. 雲端部署自動化
3. 服務編排和協調
4. 部署狀態監控
5. 回滾和恢復機制
6. 安全配置管理

由墨子(DevOps工程師)設計實現
"""

import asyncio
import yaml
import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import logging
from pathlib import Path

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error
from ..utils.resilience_manager import get_global_resilience_manager

logger = get_system_logger("deployment_manager")

class EnvironmentType(Enum):
    """環境類型"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"

class CloudProvider(Enum):
    """雲端提供商"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    ALIBABA_CLOUD = "alibaba_cloud"
    LOCAL = "local"
    DOCKER = "docker"

class DeploymentStatus(Enum):
    """部署狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"

class ServiceType(Enum):
    """服務類型"""
    API = "api"
    DATABASE = "database"
    CACHE = "cache"
    MONITORING = "monitoring"
    LOGGING = "logging"
    PROXY = "proxy"
    QUEUE = "queue"

@dataclass
class ServiceConfiguration:
    """服務配置"""
    service_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    service_type: ServiceType = ServiceType.API
    image: str = ""
    version: str = "latest"
    replicas: int = 1
    cpu_limit: str = "500m"
    memory_limit: str = "512Mi"
    cpu_request: str = "250m"
    memory_request: str = "256Mi"
    environment_variables: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, str]] = field(default_factory=list)
    ports: List[Dict[str, Any]] = field(default_factory=list)
    health_check: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class DeploymentConfig:
    """部署配置"""
    deployment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    environment: EnvironmentType = EnvironmentType.DEVELOPMENT
    cloud_provider: CloudProvider = CloudProvider.LOCAL
    namespace: str = "default"
    services: List[ServiceConfiguration] = field(default_factory=list)
    ingress_config: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    logging_config: Dict[str, Any] = field(default_factory=dict)
    security_config: Dict[str, Any] = field(default_factory=dict)
    backup_config: Dict[str, Any] = field(default_factory=dict)
    scaling_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

@dataclass
class DeploymentResult:
    """部署結果"""
    deployment_id: str = ""
    status: DeploymentStatus = DeploymentStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: float = 0.0
    services_deployed: List[str] = field(default_factory=list)
    services_failed: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    deployment_logs: List[str] = field(default_factory=list)
    rollback_info: Optional[Dict[str, Any]] = None
    health_status: Dict[str, bool] = field(default_factory=dict)

class DeploymentManager:
    """部署管理器 - 天工開物系統部署核心組件"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.resilience_manager = get_global_resilience_manager()
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self.deployment_history: List[DeploymentResult] = []
        self.active_deployments: Dict[str, asyncio.Task] = {}
        
        # 部署工具配置
        self.tools_config = {
            'docker': self.config.get('docker', {}),
            'kubernetes': self.config.get('kubernetes', {}),
            'terraform': self.config.get('terraform', {}),
            'ansible': self.config.get('ansible', {})
        }
        
        # 預設部署配置
        self._setup_default_configurations()
        
        logger.info("部署管理器已初始化", extra={
            'supported_environments': [env.value for env in EnvironmentType],
            'supported_providers': [provider.value for provider in CloudProvider],
            'tools_configured': list(self.tools_config.keys())
        })
    
    def _setup_default_configurations(self):
        """設置預設部署配置"""
        
        # 開發環境配置
        dev_config = self._create_development_config()
        self.register_deployment_config(dev_config)
        
        # 生產環境配置
        prod_config = self._create_production_config()
        self.register_deployment_config(prod_config)
        
        # 測試環境配置
        test_config = self._create_testing_config()
        self.register_deployment_config(test_config)
    
    def _create_development_config(self) -> DeploymentConfig:
        """創建開發環境配置"""
        
        # TradingAgents API 服務
        api_service = ServiceConfiguration(
            name="tradingagents-api",
            service_type=ServiceType.API,
            image="tradingagents:dev",
            replicas=1,
            cpu_limit="1000m",
            memory_limit="1Gi",
            cpu_request="500m",
            memory_request="512Mi",
            ports=[{
                "name": "http",
                "container_port": 8000,
                "service_port": 8000,
                "protocol": "TCP"
            }],
            environment_variables={
                "ENVIRONMENT": "development",
                "DEBUG": "true",
                "LOG_LEVEL": "DEBUG",
                "DATABASE_URL": "postgresql://user:pass@postgres:5432/tradingagents_dev",
                "REDIS_URL": "redis://redis:6379/0"
            },
            health_check={
                "http_get": {
                    "path": "/health",
                    "port": 8000
                },
                "initial_delay_seconds": 30,
                "period_seconds": 10,
                "timeout_seconds": 5,
                "failure_threshold": 3
            },
            dependencies=["postgres", "redis"]
        )
        
        # PostgreSQL 服務
        postgres_service = ServiceConfiguration(
            name="postgres",
            service_type=ServiceType.DATABASE,
            image="postgres:15-alpine",
            replicas=1,
            cpu_limit="500m",
            memory_limit="512Mi",
            cpu_request="250m",
            memory_request="256Mi",
            ports=[{
                "name": "postgres",
                "container_port": 5432,
                "service_port": 5432,
                "protocol": "TCP"
            }],
            environment_variables={
                "POSTGRES_DB": "tradingagents_dev",
                "POSTGRES_USER": "user",
                "POSTGRES_PASSWORD": "pass"
            },
            volumes=[{
                "name": "postgres-data",
                "mount_path": "/var/lib/postgresql/data",
                "type": "persistent"
            }],
            health_check={
                "exec": {
                    "command": ["pg_isready", "-U", "user"]
                },
                "initial_delay_seconds": 15,
                "period_seconds": 10,
                "timeout_seconds": 5,
                "failure_threshold": 3
            }
        )
        
        # Redis 服務
        redis_service = ServiceConfiguration(
            name="redis",
            service_type=ServiceType.CACHE,
            image="redis:7-alpine",
            replicas=1,
            cpu_limit="250m",
            memory_limit="256Mi",
            cpu_request="100m",
            memory_request="128Mi",
            ports=[{
                "name": "redis",
                "container_port": 6379,
                "service_port": 6379,
                "protocol": "TCP"
            }],
            volumes=[{
                "name": "redis-data",
                "mount_path": "/data",
                "type": "persistent"
            }],
            health_check={
                "exec": {
                    "command": ["redis-cli", "ping"]
                },
                "initial_delay_seconds": 5,
                "period_seconds": 10,
                "timeout_seconds": 3,
                "failure_threshold": 3
            }
        )
        
        return DeploymentConfig(
            name="tradingagents-development",
            environment=EnvironmentType.DEVELOPMENT,
            cloud_provider=CloudProvider.LOCAL,
            namespace="tradingagents-dev",
            services=[api_service, postgres_service, redis_service],
            monitoring_config={
                "enabled": True,
                "prometheus": {
                    "enabled": True,
                    "port": 9090
                },
                "grafana": {
                    "enabled": True,
                    "port": 3000
                }
            },
            logging_config={
                "level": "DEBUG",
                "format": "json",
                "aggregation": False
            },
            security_config={
                "network_policies": False,
                "pod_security_policies": False,
                "ssl_termination": False
            }
        )
    
    def _create_production_config(self) -> DeploymentConfig:
        """創建生產環境配置"""
        
        # TradingAgents API 服務 - 生產環境
        api_service = ServiceConfiguration(
            name="tradingagents-api",
            service_type=ServiceType.API,
            image="tradingagents:stable",
            replicas=3,
            cpu_limit="2000m",
            memory_limit="4Gi",
            cpu_request="1000m",
            memory_request="2Gi",
            ports=[{
                "name": "http",
                "container_port": 8000,
                "service_port": 8000,
                "protocol": "TCP"
            }],
            environment_variables={
                "ENVIRONMENT": "production",
                "DEBUG": "false",
                "LOG_LEVEL": "INFO",
                "DATABASE_URL": "${DATABASE_URL}",
                "REDIS_URL": "${REDIS_URL}",
                "SECRET_KEY": "${SECRET_KEY}",
                "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
            },
            health_check={
                "http_get": {
                    "path": "/health",
                    "port": 8000
                },
                "initial_delay_seconds": 60,
                "period_seconds": 30,
                "timeout_seconds": 10,
                "failure_threshold": 3
            },
            dependencies=["postgres", "redis"],
            labels={
                "app": "tradingagents",
                "tier": "api",
                "environment": "production"
            }
        )
        
        # PostgreSQL 高可用性配置
        postgres_service = ServiceConfiguration(
            name="postgres",
            service_type=ServiceType.DATABASE,
            image="postgres:15-alpine",
            replicas=1,  # 生產環境應該使用外部管理的數據庫
            cpu_limit="4000m",
            memory_limit="8Gi",
            cpu_request="2000m",
            memory_request="4Gi",
            ports=[{
                "name": "postgres",
                "container_port": 5432,
                "service_port": 5432,
                "protocol": "TCP"
            }],
            environment_variables={
                "POSTGRES_DB": "tradingagents",
                "POSTGRES_USER": "${POSTGRES_USER}",
                "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD}"
            },
            volumes=[{
                "name": "postgres-data",
                "mount_path": "/var/lib/postgresql/data",
                "type": "persistent",
                "storage_class": "fast-ssd"
            }],
            health_check={
                "exec": {
                    "command": ["pg_isready", "-U", "${POSTGRES_USER}"]
                },
                "initial_delay_seconds": 30,
                "period_seconds": 10,
                "timeout_seconds": 5,
                "failure_threshold": 5
            }
        )
        
        # Redis 集群配置
        redis_service = ServiceConfiguration(
            name="redis",
            service_type=ServiceType.CACHE,
            image="redis:7-alpine",
            replicas=3,
            cpu_limit="1000m",
            memory_limit="2Gi",
            cpu_request="500m",
            memory_request="1Gi",
            ports=[{
                "name": "redis",
                "container_port": 6379,
                "service_port": 6379,
                "protocol": "TCP"
            }],
            volumes=[{
                "name": "redis-data",
                "mount_path": "/data",
                "type": "persistent",
                "storage_class": "fast-ssd"
            }],
            health_check={
                "exec": {
                    "command": ["redis-cli", "ping"]
                },
                "initial_delay_seconds": 10,
                "period_seconds": 10,
                "timeout_seconds": 5,
                "failure_threshold": 3
            }
        )
        
        # Nginx 反向代理
        nginx_service = ServiceConfiguration(
            name="nginx",
            service_type=ServiceType.PROXY,
            image="nginx:alpine",
            replicas=2,
            cpu_limit="500m",
            memory_limit="512Mi",
            cpu_request="250m",
            memory_request="256Mi",
            ports=[
                {
                    "name": "http",
                    "container_port": 80,
                    "service_port": 80,
                    "protocol": "TCP"
                },
                {
                    "name": "https",
                    "container_port": 443,
                    "service_port": 443,
                    "protocol": "TCP"
                }
            ],
            volumes=[
                {
                    "name": "nginx-config",
                    "mount_path": "/etc/nginx/nginx.conf",
                    "type": "config"
                },
                {
                    "name": "ssl-certs",
                    "mount_path": "/etc/nginx/ssl",
                    "type": "secret"
                }
            ],
            dependencies=["tradingagents-api"],
            health_check={
                "http_get": {
                    "path": "/health",
                    "port": 80
                },
                "initial_delay_seconds": 10,
                "period_seconds": 10,
                "timeout_seconds": 5,
                "failure_threshold": 3
            }
        )
        
        return DeploymentConfig(
            name="tradingagents-production",
            environment=EnvironmentType.PRODUCTION,
            cloud_provider=CloudProvider.AWS,  # 預設使用 AWS
            namespace="tradingagents-prod",
            services=[api_service, postgres_service, redis_service, nginx_service],
            ingress_config={
                "enabled": True,
                "host": "api.tradingagents.com",
                "ssl": True,
                "certificate_manager": "cert-manager",
                "load_balancer": "aws-nlb"
            },
            monitoring_config={
                "enabled": True,
                "prometheus": {
                    "enabled": True,
                    "retention": "30d",
                    "storage": "100Gi"
                },
                "grafana": {
                    "enabled": True,
                    "persistence": True
                },
                "alertmanager": {
                    "enabled": True,
                    "slack_webhook": "${SLACK_WEBHOOK_URL}"
                }
            },
            logging_config={
                "level": "INFO",
                "format": "json",
                "aggregation": True,
                "retention_days": 30,
                "elasticsearch": {
                    "enabled": True,
                    "cluster": "tradingagents-logs"
                }
            },
            security_config={
                "network_policies": True,
                "pod_security_policies": True,
                "ssl_termination": True,
                "secrets_encryption": True,
                "rbac": True
            },
            scaling_config={
                "horizontal_pod_autoscaler": {
                    "enabled": True,
                    "min_replicas": 3,
                    "max_replicas": 10,
                    "target_cpu_utilization": 70
                },
                "vertical_pod_autoscaler": {
                    "enabled": True,
                    "update_mode": "Auto"
                }
            },
            backup_config={
                "database": {
                    "enabled": True,
                    "schedule": "0 2 * * *",  # 每日 2AM
                    "retention_days": 30
                },
                "storage": {
                    "enabled": True,
                    "s3_bucket": "tradingagents-backups"
                }
            }
        )
    
    def _create_testing_config(self) -> DeploymentConfig:
        """創建測試環境配置"""
        
        # 複製開發環境配置並調整
        test_config = self._create_development_config()
        test_config.name = "tradingagents-testing"
        test_config.environment = EnvironmentType.TESTING
        test_config.namespace = "tradingagents-test"
        
        # 調整測試環境的資源配置
        for service in test_config.services:
            if service.name == "tradingagents-api":
                service.environment_variables["ENVIRONMENT"] = "testing"
                service.environment_variables["DATABASE_URL"] = "postgresql://user:pass@postgres:5432/tradingagents_test"
                service.replicas = 2
            elif service.name == "postgres":
                service.environment_variables["POSTGRES_DB"] = "tradingagents_test"
        
        test_config.monitoring_config["enabled"] = True
        test_config.logging_config["level"] = "INFO"
        
        return test_config
    
    def register_deployment_config(self, config: DeploymentConfig):
        """註冊部署配置"""
        self.deployment_configs[config.deployment_id] = config
        logger.info(f"已註冊部署配置: {config.name} ({config.environment.value})")
    
    async def deploy(self, 
                    deployment_id: str,
                    dry_run: bool = False,
                    force: bool = False) -> DeploymentResult:
        """執行部署"""
        
        if deployment_id not in self.deployment_configs:
            raise ValueError(f"部署配置不存在: {deployment_id}")
        
        config = self.deployment_configs[deployment_id]
        result = DeploymentResult(
            deployment_id=deployment_id,
            started_at=datetime.now()
        )
        
        logger.info(f"開始部署: {config.name}", extra={
            'deployment_id': deployment_id,
            'environment': config.environment.value,
            'dry_run': dry_run,
            'services_count': len(config.services)
        })
        
        try:
            result.status = DeploymentStatus.IN_PROGRESS
            
            # 檢查部署前置條件
            await self._validate_deployment_prerequisites(config, result)
            
            if dry_run:
                result.deployment_logs.append("執行 dry run 模式，不會實際部署")
                await self._simulate_deployment(config, result)
            else:
                # 執行實際部署
                await self._execute_deployment(config, result, force)
            
            # 驗證部署結果
            await self._verify_deployment(config, result)
            
            result.status = DeploymentStatus.COMPLETED
            result.completed_at = datetime.now()
            result.duration = (result.completed_at - result.started_at).total_seconds()
            
            logger.info(f"部署完成: {config.name}", extra={
                'deployment_id': deployment_id,
                'duration': result.duration,
                'services_deployed': len(result.services_deployed),
                'services_failed': len(result.services_failed)
            })
            
        except Exception as e:
            result.status = DeploymentStatus.FAILED
            result.completed_at = datetime.now()
            result.duration = (result.completed_at - result.started_at).total_seconds()
            result.error_message = str(e)
            
            logger.error(f"部署失敗: {config.name}", extra={
                'deployment_id': deployment_id,
                'error': str(e),
                'duration': result.duration
            })
            
            raise
        
        finally:
            self.deployment_history.append(result)
            
            # 清理活動部署記錄
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
        
        return result
    
    async def _validate_deployment_prerequisites(self, 
                                               config: DeploymentConfig, 
                                               result: DeploymentResult):
        """驗證部署前置條件"""
        
        result.deployment_logs.append("檢查部署前置條件...")
        
        # 檢查依賴服務
        services_map = {service.name: service for service in config.services}
        
        for service in config.services:
            for dep in service.dependencies:
                if dep not in services_map:
                    raise ValueError(f"服務 {service.name} 依賴的服務 {dep} 不存在")
        
        # 檢查資源配額
        await self._check_resource_quota(config, result)
        
        # 檢查網路配置
        await self._check_network_configuration(config, result)
        
        # 檢查存儲配置
        await self._check_storage_configuration(config, result)
        
        result.deployment_logs.append("✅ 前置條件檢查完成")
    
    async def _check_resource_quota(self, config: DeploymentConfig, result: DeploymentResult):
        """檢查資源配額"""
        
        total_cpu_request = 0
        total_memory_request = 0
        total_cpu_limit = 0
        total_memory_limit = 0
        
        for service in config.services:
            # 解析CPU請求 (例如: "500m" -> 0.5)
            cpu_request = self._parse_cpu_value(service.cpu_request)
            cpu_limit = self._parse_cpu_value(service.cpu_limit)
            
            # 解析記憶體請求 (例如: "512Mi" -> 512)
            memory_request = self._parse_memory_value(service.memory_request)
            memory_limit = self._parse_memory_value(service.memory_limit)
            
            total_cpu_request += cpu_request * service.replicas
            total_cpu_limit += cpu_limit * service.replicas
            total_memory_request += memory_request * service.replicas
            total_memory_limit += memory_limit * service.replicas
        
        result.deployment_logs.append(
            f"資源需求: CPU {total_cpu_request:.1f}核/{total_cpu_limit:.1f}核, "
            f"記憶體 {total_memory_request:.0f}Mi/{total_memory_limit:.0f}Mi"
        )
        
        # 這裡可以添加實際的資源配額檢查邏輯
        # 例如查詢 Kubernetes 叢集的可用資源
    
    def _parse_cpu_value(self, cpu_str: str) -> float:
        """解析CPU值"""
        if cpu_str.endswith('m'):
            return float(cpu_str[:-1]) / 1000
        return float(cpu_str)
    
    def _parse_memory_value(self, memory_str: str) -> float:
        """解析記憶體值"""
        if memory_str.endswith('Ki'):
            return float(memory_str[:-2]) / 1024
        elif memory_str.endswith('Mi'):
            return float(memory_str[:-2])
        elif memory_str.endswith('Gi'):
            return float(memory_str[:-2]) * 1024
        return float(memory_str)
    
    async def _check_network_configuration(self, config: DeploymentConfig, result: DeploymentResult):
        """檢查網路配置"""
        result.deployment_logs.append("檢查網路配置...")
        
        # 檢查端口衝突
        used_ports = set()
        for service in config.services:
            for port_config in service.ports:
                service_port = port_config.get('service_port')
                if service_port in used_ports:
                    raise ValueError(f"端口衝突: {service_port} 已被其他服務使用")
                used_ports.add(service_port)
        
        result.deployment_logs.append("✅ 網路配置檢查完成")
    
    async def _check_storage_configuration(self, config: DeploymentConfig, result: DeploymentResult):
        """檢查存儲配置"""
        result.deployment_logs.append("檢查存儲配置...")
        
        # 檢查持久化存儲需求
        storage_requirements = []
        for service in config.services:
            for volume in service.volumes:
                if volume.get('type') == 'persistent':
                    storage_requirements.append({
                        'service': service.name,
                        'volume': volume['name'],
                        'mount_path': volume['mount_path']
                    })
        
        if storage_requirements:
            result.deployment_logs.append(f"持久化存儲需求: {len(storage_requirements)} 個卷")
        
        result.deployment_logs.append("✅ 存儲配置檢查完成")
    
    async def _simulate_deployment(self, config: DeploymentConfig, result: DeploymentResult):
        """模擬部署 (Dry Run)"""
        
        result.deployment_logs.append("=== 開始 Dry Run 模式 ===")
        
        for service in config.services:
            result.deployment_logs.append(f"模擬部署服務: {service.name}")
            
            # 模擬部署時間
            await asyncio.sleep(0.5)
            
            result.services_deployed.append(service.name)
            result.deployment_logs.append(f"✅ 服務 {service.name} 模擬部署成功")
        
        result.deployment_logs.append("=== Dry Run 完成 ===")
    
    async def _execute_deployment(self, 
                                config: DeploymentConfig, 
                                result: DeploymentResult,
                                force: bool = False):
        """執行實際部署"""
        
        result.deployment_logs.append("=== 開始實際部署 ===")
        
        # 根據雲端提供商選擇部署策略
        if config.cloud_provider == CloudProvider.DOCKER:
            await self._deploy_with_docker_compose(config, result)
        elif config.cloud_provider in [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP]:
            await self._deploy_with_kubernetes(config, result)
        else:
            await self._deploy_locally(config, result)
        
        result.deployment_logs.append("=== 實際部署完成 ===")
    
    async def _deploy_with_docker_compose(self, config: DeploymentConfig, result: DeploymentResult):
        """使用 Docker Compose 部署"""
        
        result.deployment_logs.append("使用 Docker Compose 進行部署...")
        
        # 生成 docker-compose.yml
        compose_config = self._generate_docker_compose_config(config)
        
        # 寫入配置文件
        compose_file_path = f"docker-compose-{config.environment.value}.yml"
        with open(compose_file_path, 'w', encoding='utf-8') as f:
            yaml.dump(compose_config, f, default_flow_style=False, allow_unicode=True)
        
        result.deployment_logs.append(f"生成配置文件: {compose_file_path}")
        
        try:
            # 執行 docker-compose up
            cmd = ["docker-compose", "-f", compose_file_path, "up", "-d"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result.deployment_logs.append("✅ Docker Compose 部署成功")
                result.services_deployed = [service.name for service in config.services]
            else:
                error_msg = stderr.decode() if stderr else "未知錯誤"
                result.deployment_logs.append(f"❌ Docker Compose 部署失敗: {error_msg}")
                raise Exception(f"Docker Compose 部署失敗: {error_msg}")
                
        except Exception as e:
            result.deployment_logs.append(f"❌ 部署執行錯誤: {str(e)}")
            raise
    
    def _generate_docker_compose_config(self, config: DeploymentConfig) -> Dict[str, Any]:
        """生成 Docker Compose 配置"""
        
        compose_config = {
            'version': '3.8',
            'services': {},
            'volumes': {},
            'networks': {
                f"{config.namespace}-network": {
                    'driver': 'bridge'
                }
            }
        }
        
        for service in config.services:
            service_config = {
                'image': service.image,
                'container_name': f"{config.namespace}-{service.name}",
                'restart': 'unless-stopped',
                'environment': service.environment_variables,
                'networks': [f"{config.namespace}-network"]
            }
            
            # 端口映射
            if service.ports:
                service_config['ports'] = []
                for port in service.ports:
                    service_config['ports'].append(
                        f"{port['service_port']}:{port['container_port']}"
                    )
            
            # 卷映射
            if service.volumes:
                service_config['volumes'] = []
                for volume in service.volumes:
                    if volume['type'] == 'persistent':
                        volume_name = f"{service.name}-{volume['name']}"
                        compose_config['volumes'][volume_name] = {'driver': 'local'}
                        service_config['volumes'].append(
                            f"{volume_name}:{volume['mount_path']}"
                        )
            
            # 依賴關係
            if service.dependencies:
                service_config['depends_on'] = service.dependencies
            
            # 健康檢查
            if service.health_check:
                if 'http_get' in service.health_check:
                    http_check = service.health_check['http_get']
                    service_config['healthcheck'] = {
                        'test': [
                            'CMD', 'curl', '-f', 
                            f"http://localhost:{http_check['port']}{http_check['path']}"
                        ],
                        'interval': '30s',
                        'timeout': '10s',
                        'retries': 3,
                        'start_period': '40s'
                    }
                elif 'exec' in service.health_check:
                    service_config['healthcheck'] = {
                        'test': ['CMD'] + service.health_check['exec']['command'],
                        'interval': '30s',
                        'timeout': '10s',
                        'retries': 3
                    }
            
            compose_config['services'][service.name] = service_config
        
        return compose_config
    
    async def _deploy_with_kubernetes(self, config: DeploymentConfig, result: DeploymentResult):
        """使用 Kubernetes 部署"""
        
        result.deployment_logs.append("使用 Kubernetes 進行部署...")
        
        # 生成 Kubernetes 清單
        k8s_manifests = self._generate_kubernetes_manifests(config)
        
        # 應用清單
        for manifest_name, manifest_content in k8s_manifests.items():
            try:
                # 寫入臨時文件
                manifest_file = f"k8s-{manifest_name}.yaml"
                with open(manifest_file, 'w', encoding='utf-8') as f:
                    yaml.dump_all(manifest_content, f, default_flow_style=False, allow_unicode=True)
                
                # 應用清單
                cmd = ["kubectl", "apply", "-f", manifest_file]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    result.deployment_logs.append(f"✅ 已應用 {manifest_name}")
                else:
                    error_msg = stderr.decode() if stderr else "未知錯誤"
                    result.deployment_logs.append(f"❌ 應用 {manifest_name} 失敗: {error_msg}")
                    raise Exception(f"Kubernetes 部署失敗: {error_msg}")
                
                # 清理臨時文件
                os.remove(manifest_file)
                
            except Exception as e:
                result.deployment_logs.append(f"❌ 部署 {manifest_name} 錯誤: {str(e)}")
                raise
        
        result.services_deployed = [service.name for service in config.services]
        result.deployment_logs.append("✅ Kubernetes 部署完成")
    
    def _generate_kubernetes_manifests(self, config: DeploymentConfig) -> Dict[str, List[Dict]]:
        """生成 Kubernetes 清單"""
        
        manifests = {
            'namespace': [self._create_namespace_manifest(config)],
            'services': [],
            'deployments': [],
            'configmaps': [],
            'secrets': []
        }
        
        for service in config.services:
            # 創建 Deployment
            deployment = self._create_deployment_manifest(service, config)
            manifests['deployments'].append(deployment)
            
            # 創建 Service
            service_manifest = self._create_service_manifest(service, config)
            manifests['services'].append(service_manifest)
        
        # 創建 Ingress (如果啟用)
        if config.ingress_config.get('enabled'):
            ingress = self._create_ingress_manifest(config)
            manifests['ingress'] = [ingress]
        
        return manifests
    
    def _create_namespace_manifest(self, config: DeploymentConfig) -> Dict:
        """創建 Namespace 清單"""
        return {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': config.namespace,
                'labels': {
                    'environment': config.environment.value,
                    'managed-by': 'tianGong-deployment-manager'
                }
            }
        }
    
    def _create_deployment_manifest(self, service: ServiceConfiguration, config: DeploymentConfig) -> Dict:
        """創建 Deployment 清單"""
        
        container_spec = {
            'name': service.name,
            'image': service.image,
            'ports': [{'containerPort': port['container_port']} for port in service.ports],
            'env': [{'name': k, 'value': v} for k, v in service.environment_variables.items()],
            'resources': {
                'requests': {
                    'cpu': service.cpu_request,
                    'memory': service.memory_request
                },
                'limits': {
                    'cpu': service.cpu_limit,
                    'memory': service.memory_limit
                }
            }
        }
        
        # 添加健康檢查
        if service.health_check:
            if 'http_get' in service.health_check:
                http_check = service.health_check['http_get']
                container_spec['livenessProbe'] = {
                    'httpGet': {
                        'path': http_check['path'],
                        'port': http_check['port']
                    },
                    'initialDelaySeconds': service.health_check.get('initial_delay_seconds', 30),
                    'periodSeconds': service.health_check.get('period_seconds', 10),
                    'timeoutSeconds': service.health_check.get('timeout_seconds', 5),
                    'failureThreshold': service.health_check.get('failure_threshold', 3)
                }
                container_spec['readinessProbe'] = container_spec['livenessProbe'].copy()
        
        # 添加卷掛載
        if service.volumes:
            container_spec['volumeMounts'] = []
            for volume in service.volumes:
                container_spec['volumeMounts'].append({
                    'name': volume['name'],
                    'mountPath': volume['mount_path']
                })
        
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': service.name,
                'namespace': config.namespace,
                'labels': {
                    'app': service.name,
                    'environment': config.environment.value,
                    **service.labels
                }
            },
            'spec': {
                'replicas': service.replicas,
                'selector': {
                    'matchLabels': {
                        'app': service.name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': service.name,
                            **service.labels
                        },
                        'annotations': service.annotations
                    },
                    'spec': {
                        'containers': [container_spec]
                    }
                }
            }
        }
        
        # 添加卷定義
        if service.volumes:
            deployment['spec']['template']['spec']['volumes'] = []
            for volume in service.volumes:
                if volume['type'] == 'persistent':
                    deployment['spec']['template']['spec']['volumes'].append({
                        'name': volume['name'],
                        'persistentVolumeClaim': {
                            'claimName': f"{service.name}-{volume['name']}-pvc"
                        }
                    })
        
        return deployment
    
    def _create_service_manifest(self, service: ServiceConfiguration, config: DeploymentConfig) -> Dict:
        """創建 Service 清單"""
        
        return {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{service.name}-service",
                'namespace': config.namespace,
                'labels': {
                    'app': service.name,
                    'environment': config.environment.value
                }
            },
            'spec': {
                'selector': {
                    'app': service.name
                },
                'ports': [
                    {
                        'name': port.get('name', 'http'),
                        'port': port['service_port'],
                        'targetPort': port['container_port'],
                        'protocol': port.get('protocol', 'TCP')
                    }
                    for port in service.ports
                ],
                'type': 'ClusterIP'
            }
        }
    
    def _create_ingress_manifest(self, config: DeploymentConfig) -> Dict:
        """創建 Ingress 清單"""
        
        ingress_config = config.ingress_config
        
        return {
            'apiVersion': 'networking.k8s.io/v1',
            'kind': 'Ingress',
            'metadata': {
                'name': f"{config.namespace}-ingress",
                'namespace': config.namespace,
                'annotations': {
                    'nginx.ingress.kubernetes.io/rewrite-target': '/',
                    'cert-manager.io/cluster-issuer': 'letsencrypt-prod' if ingress_config.get('ssl') else ''
                }
            },
            'spec': {
                'rules': [
                    {
                        'host': ingress_config['host'],
                        'http': {
                            'paths': [
                                {
                                    'path': '/',
                                    'pathType': 'Prefix',
                                    'backend': {
                                        'service': {
                                            'name': 'tradingagents-api-service',
                                            'port': {
                                                'number': 8000
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    
    async def _deploy_locally(self, config: DeploymentConfig, result: DeploymentResult):
        """本地部署"""
        
        result.deployment_logs.append("執行本地部署...")
        
        # 模擬本地服務啟動
        for service in config.services:
            result.deployment_logs.append(f"啟動本地服務: {service.name}")
            
            # 這裡可以添加實際的本地服務啟動邏輯
            # 例如使用 systemd, PM2 等
            
            await asyncio.sleep(1)  # 模擬啟動時間
            
            result.services_deployed.append(service.name)
            result.deployment_logs.append(f"✅ 服務 {service.name} 啟動成功")
    
    async def _verify_deployment(self, config: DeploymentConfig, result: DeploymentResult):
        """驗證部署結果"""
        
        result.deployment_logs.append("驗證部署結果...")
        
        # 檢查服務健康狀態
        for service in config.services:
            try:
                # 這裡應該實現實際的健康檢查邏輯
                is_healthy = await self._check_service_health(service, config)
                result.health_status[service.name] = is_healthy
                
                if is_healthy:
                    result.deployment_logs.append(f"✅ 服務 {service.name} 健康檢查通過")
                else:
                    result.deployment_logs.append(f"❌ 服務 {service.name} 健康檢查失敗")
                    result.services_failed.append(service.name)
                    
            except Exception as e:
                result.deployment_logs.append(f"❌ 服務 {service.name} 健康檢查錯誤: {str(e)}")
                result.services_failed.append(service.name)
                result.health_status[service.name] = False
        
        if result.services_failed:
            raise Exception(f"部分服務部署失敗: {', '.join(result.services_failed)}")
        
        result.deployment_logs.append("✅ 部署驗證完成")
    
    async def _check_service_health(self, service: ServiceConfiguration, config: DeploymentConfig) -> bool:
        """檢查服務健康狀態"""
        
        # 這裡應該實現實際的健康檢查邏輯
        # 例如發送 HTTP 請求到健康檢查端點
        
        if service.health_check:
            if 'http_get' in service.health_check:
                # 模擬 HTTP 健康檢查
                return True
            elif 'exec' in service.health_check:
                # 模擬命令執行檢查
                return True
        
        return True  # 默認假設健康
    
    async def rollback(self, deployment_id: str, target_version: Optional[str] = None) -> DeploymentResult:
        """回滾部署"""
        
        logger.info(f"開始回滾部署: {deployment_id}", extra={
            'target_version': target_version
        })
        
        # 這裡實現回滾邏輯
        # 1. 找到目標版本
        # 2. 執行回滾操作
        # 3. 驗證回滾結果
        
        result = DeploymentResult(
            deployment_id=deployment_id,
            status=DeploymentStatus.ROLLING_BACK,
            started_at=datetime.now()
        )
        
        try:
            # 模擬回滾過程
            await asyncio.sleep(2)
            
            result.status = DeploymentStatus.ROLLED_BACK
            result.completed_at = datetime.now()
            result.duration = (result.completed_at - result.started_at).total_seconds()
            
            logger.info(f"回滾完成: {deployment_id}")
            
        except Exception as e:
            result.status = DeploymentStatus.FAILED
            result.error_message = str(e)
            logger.error(f"回滾失敗: {deployment_id} - {e}")
            raise
        
        return result
    
    async def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentResult]:
        """獲取部署狀態"""
        
        # 從歷史記錄中查找
        for result in reversed(self.deployment_history):
            if result.deployment_id == deployment_id:
                return result
        
        return None
    
    def list_deployment_configs(self) -> List[Dict[str, Any]]:
        """列出所有部署配置"""
        
        configs = []
        for config in self.deployment_configs.values():
            configs.append({
                'deployment_id': config.deployment_id,
                'name': config.name,
                'environment': config.environment.value,
                'cloud_provider': config.cloud_provider.value,
                'services_count': len(config.services),
                'created_at': config.created_at.isoformat(),
                'updated_at': config.updated_at.isoformat()
            })
        
        return configs
    
    def get_deployment_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """獲取部署歷史"""
        
        history = []
        for result in reversed(self.deployment_history[-limit:]):
            history.append({
                'deployment_id': result.deployment_id,
                'status': result.status.value,
                'started_at': result.started_at.isoformat() if result.started_at else None,
                'completed_at': result.completed_at.isoformat() if result.completed_at else None,
                'duration': result.duration,
                'services_deployed': len(result.services_deployed),
                'services_failed': len(result.services_failed),
                'error_message': result.error_message
            })
        
        return history

def create_deployment_manager(config: Optional[Dict[str, Any]] = None) -> DeploymentManager:
    """創建部署管理器實例"""
    return DeploymentManager(config)

if __name__ == "__main__":
    # 測試腳本
    async def test_deployment_manager():
        print("測試部署管理器...")
        
        # 創建管理器
        manager = create_deployment_manager({
            'docker': {'compose_version': '3.8'},
            'kubernetes': {'context': 'local'},
            'terraform': {'version': '1.0'},
            'ansible': {'inventory': 'local'}
        })
        
        # 列出可用配置
        configs = manager.list_deployment_configs()
        print(f"可用部署配置: {len(configs)}")
        
        for config in configs:
            print(f"  - {config['name']} ({config['environment']})")
        
        # 執行 dry run 部署
        if configs:
            config_id = configs[0]['deployment_id']
            print(f"\n執行 dry run 部署: {configs[0]['name']}")
            
            result = await manager.deploy(config_id, dry_run=True)
            
            print(f"部署結果:")
            print(f"  狀態: {result.status.value}")
            print(f"  持續時間: {result.duration:.2f}s")
            print(f"  部署服務: {len(result.services_deployed)}")
            print(f"  失敗服務: {len(result.services_failed)}")
        
        print("部署管理器測試完成")
    
    asyncio.run(test_deployment_manager())