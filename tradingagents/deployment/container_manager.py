#!/usr/bin/env python3
"""
容器管理器 (Container Manager)
天工開物系統的容器化部署和管理

此模組提供：
1. Docker 容器管理
2. Kubernetes 部署管理
3. 容器編排和協調
4. 容器監控和日誌
5. 容器安全配置
6. 容器網路管理

由墨子(DevOps工程師)設計實現
"""

import asyncio
import docker
import yaml
import json
import subprocess
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime
from pathlib import Path
import logging

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error
from ..utils.resilience_manager import get_global_resilience_manager

logger = get_system_logger("container_manager")

class ContainerPlatform(Enum):
    """容器平台"""
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    DOCKER_SWARM = "docker_swarm"
    PODMAN = "podman"

class ContainerStatus(Enum):
    """容器狀態"""
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"

class NetworkMode(Enum):
    """網路模式"""
    BRIDGE = "bridge"
    HOST = "host"
    NONE = "none"
    CONTAINER = "container"
    CUSTOM = "custom"

@dataclass
class DockerConfiguration:
    """Docker 配置"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    image_name: str = ""
    image_tag: str = "latest"
    container_name: str = ""
    ports: Dict[str, str] = field(default_factory=dict)  # host_port: container_port
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: Dict[str, str] = field(default_factory=dict)  # host_path: container_path
    network_mode: NetworkMode = NetworkMode.BRIDGE
    restart_policy: str = "unless-stopped"
    memory_limit: Optional[str] = None
    cpu_limit: Optional[str] = None
    health_check: Optional[Dict[str, Any]] = None
    labels: Dict[str, str] = field(default_factory=dict)
    command: Optional[List[str]] = None
    working_dir: Optional[str] = None
    user: Optional[str] = None
    privileged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['network_mode'] = self.network_mode.value
        return data

@dataclass
class KubernetesConfiguration:
    """Kubernetes 配置"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    namespace: str = "default"
    deployment_name: str = ""
    replicas: int = 1
    image: str = ""
    ports: List[Dict[str, Any]] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    resource_requests: Dict[str, str] = field(default_factory=dict)
    resource_limits: Dict[str, str] = field(default_factory=dict)
    health_checks: Dict[str, Any] = field(default_factory=dict)
    service_config: Dict[str, Any] = field(default_factory=dict)
    ingress_config: Optional[Dict[str, Any]] = None
    config_maps: List[Dict[str, Any]] = field(default_factory=list)
    secrets: List[Dict[str, Any]] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ContainerInfo:
    """容器資訊"""
    container_id: str = ""
    name: str = ""
    image: str = ""
    status: ContainerStatus = ContainerStatus.CREATED
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    ports: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    network_settings: Dict[str, Any] = field(default_factory=dict)
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    health_status: Optional[str] = None
    logs: List[str] = field(default_factory=list)

@dataclass
class DeploymentInfo:
    """部署資訊"""
    deployment_id: str = ""
    name: str = ""
    namespace: str = ""
    replicas: int = 0
    available_replicas: int = 0
    ready_replicas: int = 0
    updated_replicas: int = 0
    status: str = ""
    created_at: Optional[datetime] = None
    conditions: List[Dict[str, Any]] = field(default_factory=list)

class ContainerManager:
    """容器管理器 - 天工開物系統容器化部署核心組件"""
    
    def __init__(self, platform: ContainerPlatform = ContainerPlatform.DOCKER):
        self.platform = platform
        self.resilience_manager = get_global_resilience_manager()
        
        # Docker 客戶端
        self.docker_client = None
        if platform == ContainerPlatform.DOCKER:
            try:
                self.docker_client = docker.from_env()
                logger.info("Docker 客戶端連接成功")
            except Exception as e:
                logger.warning(f"Docker 客戶端連接失敗: {e}")
        
        # 容器追蹤
        self.managed_containers: Dict[str, ContainerInfo] = {}
        self.managed_deployments: Dict[str, DeploymentInfo] = {}
        
        logger.info(f"容器管理器已初始化", extra={
            'platform': platform.value,
            'docker_available': self.docker_client is not None
        })
    
    async def build_image(self, 
                         dockerfile_path: str,
                         image_name: str,
                         image_tag: str = "latest",
                         build_args: Optional[Dict[str, str]] = None,
                         no_cache: bool = False) -> str:
        """建置 Docker 映像"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        full_image_name = f"{image_name}:{image_tag}"
        
        logger.info(f"開始建置映像: {full_image_name}", extra={
            'dockerfile_path': dockerfile_path,
            'build_args': build_args,
            'no_cache': no_cache
        })
        
        try:
            # 建置映像
            image, build_logs = self.docker_client.images.build(
                path=dockerfile_path,
                tag=full_image_name,
                buildargs=build_args or {},
                nocache=no_cache,
                rm=True
            )
            
            # 處理建置日誌
            build_output = []
            for log in build_logs:
                if 'stream' in log:
                    build_output.append(log['stream'].strip())
            
            logger.info(f"映像建置成功: {full_image_name}", extra={
                'image_id': image.id,
                'image_size': image.attrs.get('Size', 0),
                'build_logs_count': len(build_output)
            })
            
            return image.id
            
        except Exception as e:
            logger.error(f"映像建置失敗: {full_image_name} - {e}")
            raise
    
    async def run_container(self, config: DockerConfiguration) -> ContainerInfo:
        """運行 Docker 容器"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        full_image_name = f"{config.image_name}:{config.image_tag}"
        
        logger.info(f"開始運行容器: {config.container_name}", extra={
            'image': full_image_name,
            'ports': config.ports,
            'environment_vars': len(config.environment)
        })
        
        try:
            # 準備容器配置
            container_kwargs = {
                'image': full_image_name,
                'name': config.container_name,
                'ports': config.ports,
                'environment': config.environment,
                'volumes': config.volumes,
                'network_mode': config.network_mode.value,
                'restart_policy': {"Name": config.restart_policy},
                'labels': config.labels,
                'detach': True
            }
            
            # 添加資源限制
            if config.memory_limit or config.cpu_limit:
                container_kwargs['mem_limit'] = config.memory_limit
                if config.cpu_limit:
                    container_kwargs['cpu_period'] = 100000
                    container_kwargs['cpu_quota'] = int(float(config.cpu_limit) * 100000)
            
            # 添加命令和工作目錄
            if config.command:
                container_kwargs['command'] = config.command
            if config.working_dir:
                container_kwargs['working_dir'] = config.working_dir
            if config.user:
                container_kwargs['user'] = config.user
            
            # 添加權限設置
            container_kwargs['privileged'] = config.privileged
            
            # 添加健康檢查
            if config.health_check:
                container_kwargs['healthcheck'] = config.health_check
            
            # 創建並啟動容器
            container = self.docker_client.containers.run(**container_kwargs)
            
            # 等待容器啟動
            await asyncio.sleep(1)
            container.reload()
            
            # 創建容器資訊
            container_info = self._create_container_info(container)
            self.managed_containers[container.id] = container_info
            
            logger.info(f"容器運行成功: {config.container_name}", extra={
                'container_id': container.id,
                'status': container_info.status.value
            })
            
            return container_info
            
        except Exception as e:
            logger.error(f"容器運行失敗: {config.container_name} - {e}")
            raise
    
    def _create_container_info(self, container) -> ContainerInfo:
        """創建容器資訊對象"""
        
        attrs = container.attrs
        
        # 解析時間
        created_at = None
        started_at = None
        if 'Created' in attrs:
            created_at = datetime.fromisoformat(attrs['Created'].replace('Z', '+00:00'))
        if 'State' in attrs and 'StartedAt' in attrs['State']:
            started_at_str = attrs['State']['StartedAt']
            if started_at_str != '0001-01-01T00:00:00Z':
                started_at = datetime.fromisoformat(started_at_str.replace('Z', '+00:00'))
        
        # 解析狀態
        status = ContainerStatus.CREATED
        if 'State' in attrs:
            state = attrs['State']['Status']
            try:
                status = ContainerStatus(state)
            except ValueError:
                status = ContainerStatus.CREATED
        
        # 解析端口
        ports = {}
        if 'NetworkSettings' in attrs and 'Ports' in attrs['NetworkSettings']:
            for container_port, host_configs in attrs['NetworkSettings']['Ports'].items():
                if host_configs:
                    for host_config in host_configs:
                        host_port = host_config.get('HostPort')
                        if host_port:
                            ports[host_port] = container_port
        
        # 解析環境變數
        environment = {}
        if 'Config' in attrs and 'Env' in attrs['Config']:
            for env_var in attrs['Config']['Env']:
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    environment[key] = value
        
        # 解析健康狀態
        health_status = None
        if 'State' in attrs and 'Health' in attrs['State']:
            health_status = attrs['State']['Health'].get('Status')
        
        return ContainerInfo(
            container_id=container.id,
            name=container.name,
            image=attrs.get('Config', {}).get('Image', ''),
            status=status,
            created_at=created_at,
            started_at=started_at,
            ports=ports,
            environment=environment,
            network_settings=attrs.get('NetworkSettings', {}),
            health_status=health_status
        )
    
    async def stop_container(self, container_name_or_id: str, timeout: int = 10) -> bool:
        """停止容器"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        try:
            container = self.docker_client.containers.get(container_name_or_id)
            container.stop(timeout=timeout)
            
            # 更新容器狀態
            await asyncio.sleep(1)
            container.reload()
            if container.id in self.managed_containers:
                self.managed_containers[container.id] = self._create_container_info(container)
            
            logger.info(f"容器已停止: {container_name_or_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止容器失敗: {container_name_or_id} - {e}")
            return False
    
    async def restart_container(self, container_name_or_id: str, timeout: int = 10) -> bool:
        """重啟容器"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        try:
            container = self.docker_client.containers.get(container_name_or_id)
            container.restart(timeout=timeout)
            
            # 更新容器狀態
            await asyncio.sleep(2)
            container.reload()
            if container.id in self.managed_containers:
                self.managed_containers[container.id] = self._create_container_info(container)
            
            logger.info(f"容器已重啟: {container_name_or_id}")
            return True
            
        except Exception as e:
            logger.error(f"重啟容器失敗: {container_name_or_id} - {e}")
            return False
    
    async def remove_container(self, container_name_or_id: str, force: bool = False) -> bool:
        """刪除容器"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        try:
            container = self.docker_client.containers.get(container_name_or_id)
            container.remove(force=force)
            
            # 從管理列表中移除
            if container.id in self.managed_containers:
                del self.managed_containers[container.id]
            
            logger.info(f"容器已刪除: {container_name_or_id}")
            return True
            
        except Exception as e:
            logger.error(f"刪除容器失敗: {container_name_or_id} - {e}")
            return False
    
    async def get_container_logs(self, 
                               container_name_or_id: str,
                               tail: int = 100,
                               follow: bool = False) -> List[str]:
        """獲取容器日誌"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        try:
            container = self.docker_client.containers.get(container_name_or_id)
            logs = container.logs(tail=tail, follow=follow, stream=follow)
            
            if follow:
                # 流式日誌
                log_lines = []
                for log_line in logs:
                    log_lines.append(log_line.decode('utf-8').strip())
                    if len(log_lines) >= tail:
                        break
                return log_lines
            else:
                # 一次性日誌
                return logs.decode('utf-8').strip().split('\n')
                
        except Exception as e:
            logger.error(f"獲取容器日誌失敗: {container_name_or_id} - {e}")
            return []
    
    async def get_container_stats(self, container_name_or_id: str) -> Dict[str, Any]:
        """獲取容器統計資訊"""
        
        if not self.docker_client:
            raise RuntimeError("Docker 客戶端未連接")
        
        try:
            container = self.docker_client.containers.get(container_name_or_id)
            stats = container.stats(stream=False)
            
            # 計算 CPU 使用率
            cpu_usage = 0
            if 'cpu_stats' in stats and 'precpu_stats' in stats:
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0:
                    cpu_usage = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100
            
            # 計算記憶體使用率
            memory_usage = 0
            memory_limit = 0
            if 'memory_stats' in stats:
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
            
            memory_percentage = 0
            if memory_limit > 0:
                memory_percentage = (memory_usage / memory_limit) * 100
            
            # 網路統計
            network_rx = 0
            network_tx = 0
            if 'networks' in stats:
                for interface, net_stats in stats['networks'].items():
                    network_rx += net_stats.get('rx_bytes', 0)
                    network_tx += net_stats.get('tx_bytes', 0)
            
            return {
                'cpu_percentage': round(cpu_usage, 2),
                'memory_usage_bytes': memory_usage,
                'memory_limit_bytes': memory_limit,
                'memory_percentage': round(memory_percentage, 2),
                'network_rx_bytes': network_rx,
                'network_tx_bytes': network_tx,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"獲取容器統計失敗: {container_name_or_id} - {e}")
            return {}
    
    async def deploy_to_kubernetes(self, config: KubernetesConfiguration) -> DeploymentInfo:
        """部署到 Kubernetes"""
        
        logger.info(f"開始 Kubernetes 部署: {config.deployment_name}", extra={
            'namespace': config.namespace,
            'replicas': config.replicas,
            'image': config.image
        })
        
        try:
            # 生成 Kubernetes 清單
            manifests = self._generate_k8s_manifests(config)
            
            # 應用清單
            for manifest_type, manifest_content in manifests.items():
                await self._apply_k8s_manifest(manifest_content, manifest_type)
            
            # 等待部署完成
            deployment_info = await self._wait_for_deployment(config)
            
            self.managed_deployments[config.deployment_name] = deployment_info
            
            logger.info(f"Kubernetes 部署成功: {config.deployment_name}", extra={
                'deployment_id': deployment_info.deployment_id,
                'available_replicas': deployment_info.available_replicas
            })
            
            return deployment_info
            
        except Exception as e:
            logger.error(f"Kubernetes 部署失敗: {config.deployment_name} - {e}")
            raise
    
    def _generate_k8s_manifests(self, config: KubernetesConfiguration) -> Dict[str, Dict]:
        """生成 Kubernetes 清單"""
        
        manifests = {}
        
        # Deployment 清單
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': config.deployment_name,
                'namespace': config.namespace,
                'labels': config.labels,
                'annotations': config.annotations
            },
            'spec': {
                'replicas': config.replicas,
                'selector': {
                    'matchLabels': {
                        'app': config.deployment_name
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': config.deployment_name,
                            **config.labels
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': config.deployment_name,
                            'image': config.image,
                            'ports': [{'containerPort': port['container_port']} for port in config.ports],
                            'env': [{'name': k, 'value': v} for k, v in config.environment.items()],
                            'resources': {
                                'requests': config.resource_requests,
                                'limits': config.resource_limits
                            }
                        }]
                    }
                }
            }
        }
        
        # 添加健康檢查
        if config.health_checks:
            container = deployment['spec']['template']['spec']['containers'][0]
            if 'liveness_probe' in config.health_checks:
                container['livenessProbe'] = config.health_checks['liveness_probe']
            if 'readiness_probe' in config.health_checks:
                container['readinessProbe'] = config.health_checks['readiness_probe']
        
        # 添加卷
        if config.volumes:
            deployment['spec']['template']['spec']['volumes'] = config.volumes
            deployment['spec']['template']['spec']['containers'][0]['volumeMounts'] = [
                {
                    'name': vol['name'],
                    'mountPath': vol['mount_path']
                }
                for vol in config.volumes
            ]
        
        manifests['deployment'] = deployment
        
        # Service 清單
        if config.service_config:
            service = {
                'apiVersion': 'v1',
                'kind': 'Service',
                'metadata': {
                    'name': f"{config.deployment_name}-service",
                    'namespace': config.namespace,
                    'labels': config.labels
                },
                'spec': {
                    'selector': {
                        'app': config.deployment_name
                    },
                    'ports': [
                        {
                            'name': port.get('name', 'http'),
                            'port': port['service_port'],
                            'targetPort': port['container_port'],
                            'protocol': port.get('protocol', 'TCP')
                        }
                        for port in config.ports
                    ],
                    'type': config.service_config.get('type', 'ClusterIP')
                }
            }
            manifests['service'] = service
        
        # Ingress 清單
        if config.ingress_config:
            ingress = {
                'apiVersion': 'networking.k8s.io/v1',
                'kind': 'Ingress',
                'metadata': {
                    'name': f"{config.deployment_name}-ingress",
                    'namespace': config.namespace,
                    'annotations': config.ingress_config.get('annotations', {})
                },
                'spec': {
                    'rules': [
                        {
                            'host': config.ingress_config['host'],
                            'http': {
                                'paths': [
                                    {
                                        'path': config.ingress_config.get('path', '/'),
                                        'pathType': 'Prefix',
                                        'backend': {
                                            'service': {
                                                'name': f"{config.deployment_name}-service",
                                                'port': {
                                                    'number': config.ports[0]['service_port']
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
            
            if config.ingress_config.get('tls'):
                ingress['spec']['tls'] = config.ingress_config['tls']
            
            manifests['ingress'] = ingress
        
        # ConfigMap 清單
        for config_map in config.config_maps:
            manifests[f"configmap-{config_map['name']}"] = {
                'apiVersion': 'v1',
                'kind': 'ConfigMap',
                'metadata': {
                    'name': config_map['name'],
                    'namespace': config.namespace
                },
                'data': config_map['data']
            }
        
        # Secret 清單
        for secret in config.secrets:
            manifests[f"secret-{secret['name']}"] = {
                'apiVersion': 'v1',
                'kind': 'Secret',
                'metadata': {
                    'name': secret['name'],
                    'namespace': config.namespace
                },
                'type': secret.get('type', 'Opaque'),
                'data': secret['data']
            }
        
        return manifests
    
    async def _apply_k8s_manifest(self, manifest: Dict, manifest_type: str):
        """應用 Kubernetes 清單"""
        
        # 將清單寫入臨時文件
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(manifest, f, default_flow_style=False)
            temp_file = f.name
        
        try:
            # 使用 kubectl apply
            cmd = ["kubectl", "apply", "-f", temp_file]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "未知錯誤"
                raise Exception(f"應用 {manifest_type} 清單失敗: {error_msg}")
            
            logger.info(f"已應用 {manifest_type} 清單")
            
        finally:
            # 清理臨時文件
            Path(temp_file).unlink(missing_ok=True)
    
    async def _wait_for_deployment(self, config: KubernetesConfiguration) -> DeploymentInfo:
        """等待部署完成"""
        
        max_wait_time = 300  # 5分鐘
        check_interval = 10   # 10秒
        
        for _ in range(max_wait_time // check_interval):
            try:
                # 獲取部署狀態
                cmd = [
                    "kubectl", "get", "deployment", config.deployment_name,
                    "-n", config.namespace,
                    "-o", "json"
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    deployment_data = json.loads(stdout.decode())
                    deployment_info = self._parse_deployment_info(deployment_data)
                    
                    # 檢查是否部署完成
                    if (deployment_info.available_replicas >= config.replicas and
                        deployment_info.ready_replicas >= config.replicas):
                        return deployment_info
                
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.warning(f"檢查部署狀態失敗: {e}")
                await asyncio.sleep(check_interval)
        
        raise Exception(f"部署 {config.deployment_name} 超時")
    
    def _parse_deployment_info(self, deployment_data: Dict) -> DeploymentInfo:
        """解析部署資訊"""
        
        metadata = deployment_data.get('metadata', {})
        status = deployment_data.get('status', {})
        
        # 解析創建時間
        created_at = None
        if 'creationTimestamp' in metadata:
            created_at = datetime.fromisoformat(
                metadata['creationTimestamp'].replace('Z', '+00:00')
            )
        
        return DeploymentInfo(
            deployment_id=metadata.get('uid', ''),
            name=metadata.get('name', ''),
            namespace=metadata.get('namespace', ''),
            replicas=status.get('replicas', 0),
            available_replicas=status.get('availableReplicas', 0),
            ready_replicas=status.get('readyReplicas', 0),
            updated_replicas=status.get('updatedReplicas', 0),
            status='Ready' if status.get('readyReplicas', 0) == status.get('replicas', 0) else 'Updating',
            created_at=created_at,
            conditions=status.get('conditions', [])
        )
    
    async def scale_deployment(self, 
                             deployment_name: str, 
                             namespace: str,
                             replicas: int) -> bool:
        """擴展部署"""
        
        try:
            cmd = [
                "kubectl", "scale", "deployment", deployment_name,
                "-n", namespace,
                "--replicas", str(replicas)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"部署擴展成功: {deployment_name} -> {replicas} 副本")
                return True
            else:
                error_msg = stderr.decode() if stderr else "未知錯誤"
                logger.error(f"部署擴展失敗: {deployment_name} - {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"部署擴展錯誤: {deployment_name} - {e}")
            return False
    
    async def delete_deployment(self, deployment_name: str, namespace: str) -> bool:
        """刪除部署"""
        
        try:
            cmd = [
                "kubectl", "delete", "deployment", deployment_name,
                "-n", namespace
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # 從管理列表中移除
                if deployment_name in self.managed_deployments:
                    del self.managed_deployments[deployment_name]
                
                logger.info(f"部署已刪除: {deployment_name}")
                return True
            else:
                error_msg = stderr.decode() if stderr else "未知錯誤"
                logger.error(f"刪除部署失敗: {deployment_name} - {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"刪除部署錯誤: {deployment_name} - {e}")
            return False
    
    def list_containers(self) -> List[ContainerInfo]:
        """列出所有管理的容器"""
        return list(self.managed_containers.values())
    
    def list_deployments(self) -> List[DeploymentInfo]:
        """列出所有管理的部署"""
        return list(self.managed_deployments.values())
    
    async def get_cluster_info(self) -> Dict[str, Any]:
        """獲取叢集資訊"""
        
        if self.platform != ContainerPlatform.KUBERNETES:
            return {}
        
        try:
            # 獲取節點資訊
            cmd = ["kubectl", "get", "nodes", "-o", "json"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                nodes_data = json.loads(stdout.decode())
                
                cluster_info = {
                    'nodes_count': len(nodes_data.get('items', [])),
                    'nodes': [],
                    'cluster_version': '',
                    'total_cpu': 0,
                    'total_memory': 0
                }
                
                for node in nodes_data.get('items', []):
                    node_info = {
                        'name': node['metadata']['name'],
                        'status': 'Ready' if any(
                            condition['type'] == 'Ready' and condition['status'] == 'True'
                            for condition in node['status']['conditions']
                        ) else 'NotReady',
                        'version': node['status']['nodeInfo']['kubeletVersion'],
                        'os': node['status']['nodeInfo']['operatingSystem'],
                        'architecture': node['status']['nodeInfo']['architecture']
                    }
                    
                    # 資源容量
                    capacity = node['status']['capacity']
                    node_info['cpu'] = capacity.get('cpu', '0')
                    node_info['memory'] = capacity.get('memory', '0Ki')
                    
                    cluster_info['nodes'].append(node_info)
                
                return cluster_info
            
        except Exception as e:
            logger.error(f"獲取叢集資訊失敗: {e}")
        
        return {}
    
    async def cleanup_resources(self, namespace: Optional[str] = None):
        """清理資源"""
        
        logger.info("開始清理容器資源", extra={
            'managed_containers': len(self.managed_containers),
            'managed_deployments': len(self.managed_deployments),
            'namespace': namespace
        })
        
        # 清理 Docker 容器
        if self.docker_client:
            for container_id in list(self.managed_containers.keys()):
                try:
                    await self.stop_container(container_id)
                    await self.remove_container(container_id)
                except Exception as e:
                    logger.warning(f"清理容器失敗 {container_id}: {e}")
        
        # 清理 Kubernetes 部署
        if self.platform == ContainerPlatform.KUBERNETES:
            for deployment_name in list(self.managed_deployments.keys()):
                deployment_namespace = namespace or "default"
                try:
                    await self.delete_deployment(deployment_name, deployment_namespace)
                except Exception as e:
                    logger.warning(f"清理部署失敗 {deployment_name}: {e}")
        
        logger.info("容器資源清理完成")

def create_container_manager(platform: ContainerPlatform = ContainerPlatform.DOCKER) -> ContainerManager:
    """創建容器管理器實例"""
    return ContainerManager(platform)

if __name__ == "__main__":
    # 測試腳本
    async def test_container_manager():
        print("測試容器管理器...")
        
        # 創建管理器
        manager = create_container_manager(ContainerPlatform.DOCKER)
        
        # 測試 Docker 配置
        docker_config = DockerConfiguration(
            image_name="nginx",
            image_tag="alpine",
            container_name="test-nginx",
            ports={"8080": "80"},
            environment={"NGINX_HOST": "localhost"},
            restart_policy="unless-stopped"
        )
        
        try:
            # 運行測試容器
            print("運行測試容器...")
            container_info = await manager.run_container(docker_config)
            print(f"✅ 容器運行成功: {container_info.name}")
            
            # 獲取容器狀態
            await asyncio.sleep(2)
            stats = await manager.get_container_stats(container_info.container_id)
            print(f"📊 容器統計: CPU {stats.get('cpu_percentage', 0):.1f}%, "
                  f"記憶體 {stats.get('memory_percentage', 0):.1f}%")
            
            # 獲取日誌
            logs = await manager.get_container_logs(container_info.container_id, tail=5)
            print(f"📝 容器日誌: {len(logs)} 行")
            
            # 停止容器
            await manager.stop_container(container_info.container_id)
            print("⏹️ 容器已停止")
            
            # 清理
            await manager.remove_container(container_info.container_id)
            print("🗑️ 容器已清理")
            
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
        
        print("容器管理器測試完成")
    
    asyncio.run(test_container_manager())