#!/usr/bin/env python3
"""
環境管理器 (Environment Manager)
天工開物系統的環境配置和設定管理

此模組提供：
1. 多環境配置管理
2. 配置模板系統
3. 環境變數管理
4. 配置驗證和校驗
5. 動態配置更新
6. 配置版本控制

由墨子(DevOps工程師)和包拯(安全顧問)聯合設計實現
"""

import os
import json
import yaml
import toml
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime
from pathlib import Path
import logging
from jinja2 import Template, Environment as Jinja2Environment, FileSystemLoader
import asyncio

from ..utils.logging_config import get_system_logger
from ..utils.error_handler import handle_error

logger = get_system_logger("environment_manager")

class ConfigFormat(Enum):
    """配置格式"""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    ENV = "env"
    INI = "ini"

class EnvironmentTier(Enum):
    """環境級別"""
    LOCAL = "local"
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class ConfigScope(Enum):
    """配置範圍"""
    GLOBAL = "global"
    SERVICE = "service"
    COMPONENT = "component"
    FEATURE = "feature"

@dataclass
class ConfigurationTemplate:
    """配置模板"""
    template_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    scope: ConfigScope = ConfigScope.GLOBAL
    template_content: str = ""
    variables: Dict[str, Any] = field(default_factory=dict)
    required_variables: List[str] = field(default_factory=list)
    format: ConfigFormat = ConfigFormat.YAML
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class EnvironmentConfig:
    """環境配置"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    environment_name: str = ""
    tier: EnvironmentTier = EnvironmentTier.DEVELOPMENT
    variables: Dict[str, Any] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    feature_flags: Dict[str, bool] = field(default_factory=dict)
    service_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    resource_limits: Dict[str, Any] = field(default_factory=dict)
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    logging_config: Dict[str, Any] = field(default_factory=dict)
    security_config: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

@dataclass
class ConfigValidationResult:
    """配置驗證結果"""
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    missing_required: List[str] = field(default_factory=list)
    validation_time: datetime = field(default_factory=datetime.now)

class EnvironmentManager:
    """環境管理器 - 天工開物系統環境配置核心組件"""
    
    def __init__(self, config_dir: str = "./config", templates_dir: str = "./templates"):
        self.config_dir = Path(config_dir)
        self.templates_dir = Path(templates_dir)
        self.environments: Dict[str, EnvironmentConfig] = {}
        self.templates: Dict[str, ConfigurationTemplate] = {}
        
        # 創建目錄
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        # Jinja2 模板環境 - 安全修復：啟用自動轉義防止XSS
        self.jinja_env = Jinja2Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,  # 安全修復：啟用自動轉義
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # 載入預設配置
        self._load_default_templates()
        self._load_environments()
        
        logger.info("環境管理器已初始化", extra={
            'config_dir': str(self.config_dir),
            'templates_dir': str(self.templates_dir),
            'environments_loaded': len(self.environments),
            'templates_loaded': len(self.templates)
        })
    
    def _load_default_templates(self):
        """載入預設配置模板"""
        
        # TradingAgents API 配置模板
        api_template = ConfigurationTemplate(
            name="tradingagents-api",
            description="TradingAgents API 服務配置模板",
            scope=ConfigScope.SERVICE,
            format=ConfigFormat.YAML,
            template_content="""
# TradingAgents API 配置
app:
  name: "{{ app_name | default('TradingAgents') }}"
  version: "{{ app_version | default('1.0.0') }}"
  environment: "{{ environment | default('development') }}"
  debug: {{ debug | default(false) | lower }}
  
server:
  host: "{{ server_host | default('0.0.0.0') }}"
  port: {{ server_port | default(8000) }}
  workers: {{ server_workers | default(1) }}
  reload: {{ server_reload | default(false) | lower }}
  
database:
  url: "{{ database_url | default('sqlite:///./tradingagents.db') }}"
  pool_size: {{ database_pool_size | default(10) }}
  max_overflow: {{ database_max_overflow | default(20) }}
  pool_timeout: {{ database_pool_timeout | default(30) }}
  
redis:
  url: "{{ redis_url | default('redis://localhost:6379/0') }}"
  max_connections: {{ redis_max_connections | default(100) }}
  
logging:
  level: "{{ log_level | default('INFO') }}"
  format: "{{ log_format | default('json') }}"
  file: "{{ log_file | default('logs/app.log') }}"
  max_size: "{{ log_max_size | default('100MB') }}"
  backup_count: {{ log_backup_count | default(5) }}
  
security:
  secret_key: "{{ secret_key | mandatory }}"
  algorithm: "{{ jwt_algorithm | default('HS256') }}"
  access_token_expire_minutes: {{ access_token_expire_minutes | default(30) }}
  
apis:
  openai:
    api_key: "{{ openai_api_key | default('') }}"
    model: "{{ openai_model | default('gpt-3.5-turbo') }}"
  
  anthropic:
    api_key: "{{ anthropic_api_key | default('') }}"
    model: "{{ anthropic_model | default('claude-3-sonnet-20240229') }}"
  
  finnhub:
    api_key: "{{ finnhub_api_key | default('') }}"
  
  finmind:
    token: "{{ finmind_token | default('') }}"

monitoring:
  enabled: {{ monitoring_enabled | default(true) | lower }}
  prometheus:
    enabled: {{ prometheus_enabled | default(true) | lower }}
    port: {{ prometheus_port | default(9090) }}
  
  health_check:
    enabled: {{ health_check_enabled | default(true) | lower }}
    interval: {{ health_check_interval | default(30) }}
""",
            variables={
                "app_name": "TradingAgents",
                "app_version": "1.0.0",
                "environment": "development",
                "debug": False,
                "server_host": "0.0.0.0",
                "server_port": 8000,
                "server_workers": 1,
                "server_reload": False,
                "database_url": "sqlite:///./tradingagents.db",
                "redis_url": "redis://localhost:6379/0",
                "log_level": "INFO",
                "log_format": "json"
            },
            required_variables=["secret_key"]
        )
        
        # Docker Compose 配置模板
        docker_compose_template = ConfigurationTemplate(
            name="docker-compose",
            description="Docker Compose 配置模板",
            scope=ConfigScope.GLOBAL,
            format=ConfigFormat.YAML,
            template_content="""
version: '3.8'

services:
  # TradingAgents API 服務
  tradingagents-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: "{{ app_name | default('tradingagents') }}-api"
    ports:
      - "{{ api_port | default(8000) }}:8000"
    environment:
      - ENVIRONMENT={{ environment | default('development') }}
      - DATABASE_URL={{ database_url | default('postgresql://user:pass@postgres:5432/tradingagents') }}
      - REDIS_URL={{ redis_url | default('redis://redis:6379/0') }}
      - SECRET_KEY={{ secret_key | mandatory }}
      {% if openai_api_key -%}
      - OPENAI_API_KEY={{ openai_api_key }}
      {% endif -%}
      {% if anthropic_api_key -%}
      - ANTHROPIC_API_KEY={{ anthropic_api_key }}
      {% endif -%}
      {% if finnhub_api_key -%}
      - FINNHUB_API_KEY={{ finnhub_api_key }}
      {% endif -%}
      {% if finmind_token -%}
      - FINMIND_TOKEN={{ finmind_token }}
      {% endif %}
    depends_on:
      - postgres
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - tradingagents-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # PostgreSQL 數據庫
  postgres:
    image: postgres:{{ postgres_version | default('15-alpine') }}
    container_name: "{{ app_name | default('tradingagents') }}-postgres"
    environment:
      POSTGRES_DB: {{ postgres_db | default('tradingagents') }}
      POSTGRES_USER: {{ postgres_user | default('user') }}
      POSTGRES_PASSWORD: {{ postgres_password | default('pass') }}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - tradingagents-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {{ postgres_user | default('user') }}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 緩存服務
  redis:
    image: redis:{{ redis_version | default('7-alpine') }}
    container_name: "{{ app_name | default('tradingagents') }}-redis"
    volumes:
      - redis_data:/data
    networks:
      - tradingagents-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  {% if nginx_enabled | default(false) -%}
  # Nginx 反向代理
  nginx:
    image: nginx:{{ nginx_version | default('alpine') }}
    container_name: "{{ app_name | default('tradingagents') }}-nginx"
    ports:
      - "{{ nginx_http_port | default(80) }}:80"
      - "{{ nginx_https_port | default(443) }}:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - tradingagents-api
    networks:
      - tradingagents-network
    restart: unless-stopped
  {% endif %}

  {% if monitoring_enabled | default(false) -%}
  # Prometheus 監控
  prometheus:
    image: prom/prometheus:{{ prometheus_version | default('latest') }}
    container_name: "{{ app_name | default('tradingagents') }}-prometheus"
    ports:
      - "{{ prometheus_port | default(9090) }}:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    networks:
      - tradingagents-network
    restart: unless-stopped

  # Grafana 可視化
  grafana:
    image: grafana/grafana:{{ grafana_version | default('latest') }}
    container_name: "{{ app_name | default('tradingagents') }}-grafana"
    ports:
      - "{{ grafana_port | default(3000) }}:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD={{ grafana_admin_password | default('admin') }}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources
    depends_on:
      - prometheus
    networks:
      - tradingagents-network
    restart: unless-stopped
  {% endif %}

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  {% if monitoring_enabled | default(false) -%}
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  {% endif %}

networks:
  tradingagents-network:
    driver: bridge
""",
            variables={
                "app_name": "tradingagents",
                "environment": "development",
                "api_port": 8000,
                "postgres_version": "15-alpine",
                "postgres_db": "tradingagents",
                "postgres_user": "user",
                "postgres_password": "pass",
                "redis_version": "7-alpine",
                "nginx_enabled": False,
                "monitoring_enabled": False
            },
            required_variables=["secret_key"]
        )
        
        # Kubernetes 配置模板
        k8s_template = ConfigurationTemplate(
            name="kubernetes-deployment",
            description="Kubernetes 部署配置模板",
            scope=ConfigScope.GLOBAL,
            format=ConfigFormat.YAML,
            template_content="""
# Namespace
apiVersion: v1
kind: Namespace
metadata:
  name: {{ namespace | default('tradingagents') }}
  labels:
    environment: {{ environment | default('development') }}
    managed-by: tianGong-environment-manager

---
# TradingAgents API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tradingagents-api
  namespace: {{ namespace | default('tradingagents') }}
  labels:
    app: tradingagents-api
    environment: {{ environment | default('development') }}
spec:
  replicas: {{ api_replicas | default(1) }}
  selector:
    matchLabels:
      app: tradingagents-api
  template:
    metadata:
      labels:
        app: tradingagents-api
    spec:
      containers:
      - name: tradingagents-api
        image: {{ api_image | default('tradingagents:latest') }}
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "{{ environment | default('development') }}"
        - name: DATABASE_URL
          value: "{{ database_url | mandatory }}"
        - name: REDIS_URL
          value: "{{ redis_url | mandatory }}"
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: tradingagents-secrets
              key: secret-key
        {% if openai_api_key -%}
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: tradingagents-secrets
              key: openai-api-key
        {% endif -%}
        {% if anthropic_api_key -%}
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: tradingagents-secrets
              key: anthropic-api-key
        {% endif %}
        resources:
          requests:
            cpu: {{ api_cpu_request | default('250m') }}
            memory: {{ api_memory_request | default('512Mi') }}
          limits:
            cpu: {{ api_cpu_limit | default('1000m') }}
            memory: {{ api_memory_limit | default('2Gi') }}
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

---
# TradingAgents API Service
apiVersion: v1
kind: Service
metadata:
  name: tradingagents-api-service
  namespace: {{ namespace | default('tradingagents') }}
  labels:
    app: tradingagents-api
spec:
  selector:
    app: tradingagents-api
  ports:
  - name: http
    port: 8000
    targetPort: 8000
    protocol: TCP
  type: ClusterIP

---
# Secrets
apiVersion: v1
kind: Secret
metadata:
  name: tradingagents-secrets
  namespace: {{ namespace | default('tradingagents') }}
type: Opaque
data:
  secret-key: {{ secret_key_base64 | mandatory }}
  {% if openai_api_key_base64 -%}
  openai-api-key: {{ openai_api_key_base64 }}
  {% endif -%}
  {% if anthropic_api_key_base64 -%}
  anthropic-api-key: {{ anthropic_api_key_base64 }}
  {% endif %}

{% if ingress_enabled | default(false) -%}
---
# Ingress
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: tradingagents-ingress
  namespace: {{ namespace | default('tradingagents') }}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    {% if ssl_enabled | default(false) -%}
    cert-manager.io/cluster-issuer: letsencrypt-prod
    {% endif %}
spec:
  {% if ssl_enabled | default(false) -%}
  tls:
  - hosts:
    - {{ ingress_host | mandatory }}
    secretName: tradingagents-tls
  {% endif -%}
  rules:
  - host: {{ ingress_host | mandatory }}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: tradingagents-api-service
            port:
              number: 8000
{% endif %}
""",
            variables={
                "namespace": "tradingagents",
                "environment": "development",
                "api_replicas": 1,
                "api_image": "tradingagents:latest",
                "api_cpu_request": "250m",
                "api_memory_request": "512Mi",
                "api_cpu_limit": "1000m",
                "api_memory_limit": "2Gi",
                "ingress_enabled": False,
                "ssl_enabled": False
            },
            required_variables=["database_url", "redis_url", "secret_key_base64"]
        )
        
        # 註冊模板
        self.register_template(api_template)
        self.register_template(docker_compose_template)
        self.register_template(k8s_template)
        
        # 保存模板到文件
        self._save_templates_to_files()
    
    def _save_templates_to_files(self):
        """保存模板到文件"""
        for template in self.templates.values():
            template_file = self.templates_dir / f"{template.name}.j2"
            with open(template_file, 'w', encoding='utf-8') as f:
                f.write(template.template_content)
    
    def _load_environments(self):
        """載入環境配置"""
        
        # 創建預設環境配置
        environments = [
            self._create_local_environment(),
            self._create_development_environment(),
            self._create_testing_environment(),
            self._create_staging_environment(),
            self._create_production_environment()
        ]
        
        for env in environments:
            self.environments[env.config_id] = env
            
            # 保存到文件
            env_file = self.config_dir / f"{env.environment_name}.yaml"
            with open(env_file, 'w', encoding='utf-8') as f:
                yaml.dump(env.to_dict(), f, default_flow_style=False, allow_unicode=True)
    
    def _create_local_environment(self) -> EnvironmentConfig:
        """創建本地環境配置"""
        return EnvironmentConfig(
            environment_name="local",
            tier=EnvironmentTier.LOCAL,
            variables={
                "app_name": "TradingAgents",
                "app_version": "dev",
                "environment": "local",
                "debug": True,
                "server_host": "127.0.0.1",
                "server_port": 8000,
                "server_workers": 1,
                "server_reload": True,
                "database_url": "sqlite:///./tradingagents_local.db",
                "redis_url": "redis://localhost:6379/0",
                "log_level": "DEBUG",
                "log_format": "console",
                "monitoring_enabled": False,
                "nginx_enabled": False
            },
            secrets={
                "secret_key": "dev-secret-key-not-for-production",
                "openai_api_key": "",
                "anthropic_api_key": "",
                "finnhub_api_key": "",
                "finmind_token": ""
            },
            feature_flags={
                "enable_ai_agents": True,
                "enable_real_trading": False,
                "enable_paper_trading": True,
                "enable_analytics": True,
                "enable_alerts": False
            },
            resource_limits={
                "max_memory_mb": 2048,
                "max_cpu_cores": 2,
                "max_connections": 100
            },
            monitoring_config={
                "enabled": False,
                "metrics_collection": False,
                "health_checks": True
            },
            logging_config={
                "level": "DEBUG",
                "format": "console",
                "file_enabled": False
            },
            security_config={
                "ssl_enabled": False,
                "cors_enabled": True,
                "rate_limiting": False
            }
        )
    
    def _create_development_environment(self) -> EnvironmentConfig:
        """創建開發環境配置"""
        return EnvironmentConfig(
            environment_name="development",
            tier=EnvironmentTier.DEVELOPMENT,
            variables={
                "app_name": "TradingAgents",
                "app_version": "dev",
                "environment": "development",
                "debug": True,
                "server_host": "0.0.0.0",
                "server_port": 8000,
                "server_workers": 2,
                "server_reload": False,
                "database_url": "postgresql://dev_user:dev_pass@localhost:5432/tradingagents_dev",
                "redis_url": "redis://localhost:6379/1",
                "log_level": "DEBUG",
                "log_format": "json",
                "monitoring_enabled": True,
                "nginx_enabled": False,
                "postgres_db": "tradingagents_dev",
                "postgres_user": "dev_user",
                "postgres_password": "dev_pass"
            },
            secrets={
                "secret_key": "${DEV_SECRET_KEY}",
                "openai_api_key": "${DEV_OPENAI_API_KEY}",
                "anthropic_api_key": "${DEV_ANTHROPIC_API_KEY}",
                "finnhub_api_key": "${DEV_FINNHUB_API_KEY}",
                "finmind_token": "${DEV_FINMIND_TOKEN}"
            },
            feature_flags={
                "enable_ai_agents": True,
                "enable_real_trading": False,
                "enable_paper_trading": True,
                "enable_analytics": True,
                "enable_alerts": True,
                "enable_caching": True
            },
            resource_limits={
                "max_memory_mb": 4096,
                "max_cpu_cores": 4,
                "max_connections": 200
            },
            monitoring_config={
                "enabled": True,
                "metrics_collection": True,
                "health_checks": True,
                "prometheus_enabled": True,
                "grafana_enabled": True
            },
            logging_config={
                "level": "DEBUG",
                "format": "json",
                "file_enabled": True,
                "max_size": "100MB",
                "backup_count": 5
            },
            security_config={
                "ssl_enabled": False,
                "cors_enabled": True,
                "rate_limiting": True,
                "api_key_required": False
            }
        )
    
    def _create_testing_environment(self) -> EnvironmentConfig:
        """創建測試環境配置"""
        return EnvironmentConfig(
            environment_name="testing",
            tier=EnvironmentTier.TESTING,
            variables={
                "app_name": "TradingAgents",
                "app_version": "test",
                "environment": "testing",
                "debug": False,
                "server_host": "0.0.0.0",
                "server_port": 8000,
                "server_workers": 2,
                "server_reload": False,
                "database_url": "postgresql://test_user:test_pass@postgres-test:5432/tradingagents_test",
                "redis_url": "redis://redis-test:6379/0",
                "log_level": "INFO",
                "log_format": "json",
                "monitoring_enabled": True,
                "nginx_enabled": True
            },
            secrets={
                "secret_key": "${TEST_SECRET_KEY}",
                "openai_api_key": "${TEST_OPENAI_API_KEY}",
                "anthropic_api_key": "${TEST_ANTHROPIC_API_KEY}",
                "finnhub_api_key": "${TEST_FINNHUB_API_KEY}",
                "finmind_token": "${TEST_FINMIND_TOKEN}"
            },
            feature_flags={
                "enable_ai_agents": True,
                "enable_real_trading": False,
                "enable_paper_trading": True,
                "enable_analytics": True,
                "enable_alerts": True,
                "enable_caching": True,
                "enable_load_testing": True
            },
            resource_limits={
                "max_memory_mb": 8192,
                "max_cpu_cores": 6,
                "max_connections": 500
            },
            monitoring_config={
                "enabled": True,
                "metrics_collection": True,
                "health_checks": True,
                "prometheus_enabled": True,
                "grafana_enabled": True,
                "alerting_enabled": True
            },
            logging_config={
                "level": "INFO",
                "format": "json",
                "file_enabled": True,
                "aggregation_enabled": True,
                "retention_days": 7
            },
            security_config={
                "ssl_enabled": True,
                "cors_enabled": True,
                "rate_limiting": True,
                "api_key_required": True,
                "security_scanning": True
            }
        )
    
    def _create_staging_environment(self) -> EnvironmentConfig:
        """創建預發布環境配置"""
        return EnvironmentConfig(
            environment_name="staging",
            tier=EnvironmentTier.STAGING,
            variables={
                "app_name": "TradingAgents",
                "app_version": "staging",
                "environment": "staging",
                "debug": False,
                "server_host": "0.0.0.0",
                "server_port": 8000,
                "server_workers": 4,
                "server_reload": False,
                "database_url": "postgresql://staging_user:${STAGING_DB_PASSWORD}@postgres-staging:5432/tradingagents_staging",
                "redis_url": "redis://redis-staging:6379/0",
                "log_level": "INFO",
                "log_format": "json",
                "monitoring_enabled": True,
                "nginx_enabled": True,
                "api_replicas": 2,
                "api_cpu_request": "500m",
                "api_memory_request": "1Gi",
                "api_cpu_limit": "2000m",
                "api_memory_limit": "4Gi"
            },
            secrets={
                "secret_key": "${STAGING_SECRET_KEY}",
                "openai_api_key": "${STAGING_OPENAI_API_KEY}",
                "anthropic_api_key": "${STAGING_ANTHROPIC_API_KEY}",
                "finnhub_api_key": "${STAGING_FINNHUB_API_KEY}",
                "finmind_token": "${STAGING_FINMIND_TOKEN}"
            },
            feature_flags={
                "enable_ai_agents": True,
                "enable_real_trading": False,
                "enable_paper_trading": True,
                "enable_analytics": True,
                "enable_alerts": True,
                "enable_caching": True,
                "enable_performance_monitoring": True
            },
            resource_limits={
                "max_memory_mb": 16384,
                "max_cpu_cores": 8,
                "max_connections": 1000
            },
            monitoring_config={
                "enabled": True,
                "metrics_collection": True,
                "health_checks": True,
                "prometheus_enabled": True,
                "grafana_enabled": True,
                "alerting_enabled": True,
                "log_aggregation": True
            },
            logging_config={
                "level": "INFO",
                "format": "json",
                "file_enabled": True,
                "aggregation_enabled": True,
                "retention_days": 14,
                "elasticsearch_enabled": True
            },
            security_config={
                "ssl_enabled": True,
                "cors_enabled": True,
                "rate_limiting": True,
                "api_key_required": True,
                "security_scanning": True,
                "vulnerability_monitoring": True
            }
        )
    
    def _create_production_environment(self) -> EnvironmentConfig:
        """創建生產環境配置"""
        return EnvironmentConfig(
            environment_name="production",
            tier=EnvironmentTier.PRODUCTION,
            variables={
                "app_name": "TradingAgents",
                "app_version": "stable",
                "environment": "production",
                "debug": False,
                "server_host": "0.0.0.0",
                "server_port": 8000,
                "server_workers": 8,
                "server_reload": False,
                "database_url": "postgresql://prod_user:${PROD_DB_PASSWORD}@postgres-prod:5432/tradingagents",
                "redis_url": "redis://redis-prod:6379/0",
                "log_level": "INFO",
                "log_format": "json",
                "monitoring_enabled": True,
                "nginx_enabled": True,
                "api_replicas": 5,
                "api_cpu_request": "1000m",
                "api_memory_request": "2Gi",
                "api_cpu_limit": "4000m",
                "api_memory_limit": "8Gi",
                "ingress_enabled": True,
                "ssl_enabled": True,
                "ingress_host": "api.tradingagents.com"
            },
            secrets={
                "secret_key": "${PROD_SECRET_KEY}",
                "openai_api_key": "${PROD_OPENAI_API_KEY}",
                "anthropic_api_key": "${PROD_ANTHROPIC_API_KEY}",
                "finnhub_api_key": "${PROD_FINNHUB_API_KEY}",
                "finmind_token": "${PROD_FINMIND_TOKEN}",
                "database_password": "${PROD_DB_PASSWORD}",
                "grafana_admin_password": "${PROD_GRAFANA_PASSWORD}"
            },
            feature_flags={
                "enable_ai_agents": True,
                "enable_real_trading": True,
                "enable_paper_trading": True,
                "enable_analytics": True,
                "enable_alerts": True,
                "enable_caching": True,
                "enable_performance_monitoring": True,
                "enable_auto_scaling": True
            },
            resource_limits={
                "max_memory_mb": 32768,
                "max_cpu_cores": 16,
                "max_connections": 5000
            },
            monitoring_config={
                "enabled": True,
                "metrics_collection": True,
                "health_checks": True,
                "prometheus_enabled": True,
                "grafana_enabled": True,
                "alerting_enabled": True,
                "log_aggregation": True,
                "performance_monitoring": True,
                "uptime_monitoring": True
            },
            logging_config={
                "level": "INFO",
                "format": "json",
                "file_enabled": True,
                "aggregation_enabled": True,
                "retention_days": 90,
                "elasticsearch_enabled": True,
                "log_backup": True
            },
            security_config={
                "ssl_enabled": True,
                "cors_enabled": True,
                "rate_limiting": True,
                "api_key_required": True,
                "security_scanning": True,
                "vulnerability_monitoring": True,
                "compliance_monitoring": True,
                "access_logging": True
            }
        )
    
    def register_template(self, template: ConfigurationTemplate):
        """註冊配置模板"""
        self.templates[template.template_id] = template
        logger.info(f"已註冊配置模板: {template.name} ({template.scope.value})")
    
    def register_environment(self, environment: EnvironmentConfig):
        """註冊環境配置"""
        self.environments[environment.config_id] = environment
        logger.info(f"已註冊環境配置: {environment.environment_name} ({environment.tier.value})")
    
    def get_environment(self, environment_name: str) -> Optional[EnvironmentConfig]:
        """獲取環境配置"""
        for env in self.environments.values():
            if env.environment_name == environment_name:
                return env
        return None
    
    def get_template(self, template_name: str) -> Optional[ConfigurationTemplate]:
        """獲取配置模板"""
        for template in self.templates.values():
            if template.name == template_name:
                return template
        return None
    
    def generate_config(self, 
                       template_name: str, 
                       environment_name: str,
                       variables: Optional[Dict[str, Any]] = None,
                       output_format: Optional[ConfigFormat] = None) -> str:
        """生成配置文件"""
        
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        
        environment = self.get_environment(environment_name)
        if not environment:
            raise ValueError(f"環境不存在: {environment_name}")
        
        # 合併變數
        merged_variables = {}
        merged_variables.update(template.variables)
        merged_variables.update(environment.variables)
        merged_variables.update(environment.secrets)
        if variables:
            merged_variables.update(variables)
        
        # 驗證必需變數
        validation_result = self.validate_template_variables(template, merged_variables)
        if not validation_result.is_valid:
            raise ValueError(f"模板變數驗證失敗: {', '.join(validation_result.missing_required)}")
        
        # 渲染模板
        try:
            jinja_template = self.jinja_env.from_string(template.template_content)
            
            # 添加自定義過濾器
            jinja_template.environment.filters['mandatory'] = self._mandatory_filter
            
            rendered_content = jinja_template.render(**merged_variables)
            
            # 根據輸出格式處理
            if output_format and output_format != template.format:
                rendered_content = self._convert_config_format(
                    rendered_content, template.format, output_format
                )
            
            logger.info(f"已生成配置: {template_name} for {environment_name}")
            
            return rendered_content
            
        except Exception as e:
            logger.error(f"配置生成失敗: {template_name} for {environment_name} - {e}")
            raise
    
    def _mandatory_filter(self, value):
        """Jinja2 mandatory 過濾器"""
        if value is None or value == "":
            raise ValueError("必需變數缺失或為空")
        return value
    
    def _convert_config_format(self, content: str, from_format: ConfigFormat, to_format: ConfigFormat) -> str:
        """轉換配置格式"""
        
        # 解析源格式
        if from_format == ConfigFormat.YAML:
            data = yaml.safe_load(content)
        elif from_format == ConfigFormat.JSON:
            data = json.loads(content)
        elif from_format == ConfigFormat.TOML:
            data = toml.loads(content)
        else:
            raise ValueError(f"不支援的源格式: {from_format.value}")
        
        # 輸出目標格式
        if to_format == ConfigFormat.YAML:
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        elif to_format == ConfigFormat.JSON:
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif to_format == ConfigFormat.TOML:
            return toml.dumps(data)
        else:
            raise ValueError(f"不支援的目標格式: {to_format.value}")
    
    def validate_template_variables(self, 
                                  template: ConfigurationTemplate, 
                                  variables: Dict[str, Any]) -> ConfigValidationResult:
        """驗證模板變數"""
        
        result = ConfigValidationResult()
        
        # 檢查必需變數
        for required_var in template.required_variables:
            if required_var not in variables or variables[required_var] is None or variables[required_var] == "":
                result.missing_required.append(required_var)
        
        # 檢查變數類型
        for var_name, var_value in variables.items():
            if var_name in template.variables:
                expected_type = type(template.variables[var_name])
                if not isinstance(var_value, expected_type) and var_value is not None:
                    result.warnings.append(
                        f"變數 {var_name} 類型不匹配: 期望 {expected_type.__name__}, 實際 {type(var_value).__name__}"
                    )
        
        result.is_valid = len(result.missing_required) == 0
        
        return result
    
    def save_generated_config(self, 
                            content: str, 
                            filename: str, 
                            environment_name: str,
                            config_format: ConfigFormat = ConfigFormat.YAML):
        """保存生成的配置文件"""
        
        # 創建環境目錄
        env_dir = self.config_dir / environment_name
        env_dir.mkdir(exist_ok=True)
        
        # 確定文件擴展名
        extensions = {
            ConfigFormat.YAML: '.yaml',
            ConfigFormat.JSON: '.json',
            ConfigFormat.TOML: '.toml',
            ConfigFormat.ENV: '.env',
            ConfigFormat.INI: '.ini'
        }
        
        if not filename.endswith(extensions[config_format]):
            filename += extensions[config_format]
        
        # 保存文件
        config_file = env_dir / filename
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"已保存配置文件: {config_file}")
        
        return str(config_file)
    
    def load_environment_variables(self, environment_name: str) -> Dict[str, str]:
        """載入環境變數"""
        
        environment = self.get_environment(environment_name)
        if not environment:
            raise ValueError(f"環境不存在: {environment_name}")
        
        env_vars = {}
        
        # 添加環境變數
        for key, value in environment.variables.items():
            if isinstance(value, str):
                env_vars[key.upper()] = value
            else:
                env_vars[key.upper()] = str(value)
        
        # 添加機密變數 (需要從環境變數或密鑰管理器獲取)
        for key, value in environment.secrets.items():
            if value.startswith('${') and value.endswith('}'):
                # 從環境變數獲取
                env_var_name = value[2:-1]
                actual_value = os.getenv(env_var_name, '')
                env_vars[key.upper()] = actual_value
            else:
                env_vars[key.upper()] = value
        
        return env_vars
    
    def update_environment_variable(self, 
                                  environment_name: str, 
                                  key: str, 
                                  value: Any, 
                                  is_secret: bool = False):
        """更新環境變數"""
        
        environment = self.get_environment(environment_name)
        if not environment:
            raise ValueError(f"環境不存在: {environment_name}")
        
        if is_secret:
            environment.secrets[key] = value
        else:
            environment.variables[key] = value
        
        environment.updated_at = datetime.now()
        
        # 保存到文件
        env_file = self.config_dir / f"{environment_name}.yaml"
        with open(env_file, 'w', encoding='utf-8') as f:
            yaml.dump(environment.to_dict(), f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已更新環境變數: {environment_name}.{key}")
    
    def list_environments(self) -> List[Dict[str, Any]]:
        """列出所有環境"""
        
        environments = []
        for env in self.environments.values():
            environments.append({
                'config_id': env.config_id,
                'environment_name': env.environment_name,
                'tier': env.tier.value,
                'variables_count': len(env.variables),
                'secrets_count': len(env.secrets),
                'feature_flags_count': len(env.feature_flags),
                'created_at': env.created_at.isoformat(),
                'updated_at': env.updated_at.isoformat()
            })
        
        return environments
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有模板"""
        
        templates = []
        for template in self.templates.values():
            templates.append({
                'template_id': template.template_id,
                'name': template.name,
                'description': template.description,
                'scope': template.scope.value,
                'format': template.format.value,
                'version': template.version,
                'variables_count': len(template.variables),
                'required_variables': template.required_variables,
                'created_at': template.created_at.isoformat(),
                'updated_at': template.updated_at.isoformat()
            })
        
        return templates
    
    async def deploy_environment_configs(self, environment_name: str, target_dir: str = "./deploy"):
        """部署環境配置文件"""
        
        environment = self.get_environment(environment_name)
        if not environment:
            raise ValueError(f"環境不存在: {environment_name}")
        
        deploy_dir = Path(target_dir) / environment_name
        deploy_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"開始部署環境配置: {environment_name} 到 {deploy_dir}")
        
        # 生成所有相關配置文件
        configs_generated = []
        
        # 1. 應用配置
        app_config = self.generate_config("tradingagents-api", environment_name)
        app_config_file = self.save_generated_config(
            app_config, "app-config", environment_name, ConfigFormat.YAML
        )
        configs_generated.append(app_config_file)
        
        # 2. Docker Compose 配置
        if environment.tier in [EnvironmentTier.LOCAL, EnvironmentTier.DEVELOPMENT]:
            compose_config = self.generate_config("docker-compose", environment_name)
            compose_config_file = self.save_generated_config(
                compose_config, "docker-compose", environment_name, ConfigFormat.YAML
            )
            configs_generated.append(compose_config_file)
        
        # 3. Kubernetes 配置
        if environment.tier in [EnvironmentTier.TESTING, EnvironmentTier.STAGING, EnvironmentTier.PRODUCTION]:
            try:
                k8s_config = self.generate_config("kubernetes-deployment", environment_name)
                k8s_config_file = self.save_generated_config(
                    k8s_config, "k8s-deployment", environment_name, ConfigFormat.YAML
                )
                configs_generated.append(k8s_config_file)
            except ValueError as e:
                logger.warning(f"無法生成 Kubernetes 配置: {e}")
        
        # 4. 環境變數文件
        env_vars = self.load_environment_variables(environment_name)
        env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items() if not k.endswith('_PASSWORD') and not k.endswith('_KEY')])
        env_file = self.save_generated_config(
            env_content, ".env", environment_name, ConfigFormat.ENV
        )
        configs_generated.append(env_file)
        
        logger.info(f"環境配置部署完成: {environment_name}", extra={
            'configs_generated': len(configs_generated),
            'files': configs_generated
        })
        
        return configs_generated

def create_environment_manager(config_dir: str = "./config", templates_dir: str = "./templates") -> EnvironmentManager:
    """創建環境管理器實例"""
    return EnvironmentManager(config_dir, templates_dir)

if __name__ == "__main__":
    # 測試腳本
    async def test_environment_manager():
        print("測試環境管理器...")
        
        # 創建管理器
        manager = create_environment_manager()
        
        # 列出環境和模板
        environments = manager.list_environments()
        templates = manager.list_templates()
        
        print(f"可用環境: {len(environments)}")
        for env in environments:
            print(f"  - {env['environment_name']} ({env['tier']})")
        
        print(f"\n可用模板: {len(templates)}")
        for template in templates:
            print(f"  - {template['name']} ({template['scope']})")
        
        # 生成開發環境配置
        print(f"\n生成開發環境配置...")
        
        try:
            # 生成應用配置
            app_config = manager.generate_config("tradingagents-api", "development")
            print("✅ 應用配置生成成功")
            
            # 生成 Docker Compose 配置
            compose_config = manager.generate_config("docker-compose", "development")
            print("✅ Docker Compose 配置生成成功")
            
            # 部署配置文件
            deployed_files = await manager.deploy_environment_configs("development")
            print(f"✅ 配置文件已部署: {len(deployed_files)} 個文件")
            
        except Exception as e:
            print(f"❌ 配置生成失敗: {e}")
        
        print("環境管理器測試完成")
    
    asyncio.run(test_environment_manager())