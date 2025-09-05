#!/usr/bin/env python3
"""
監控配置管理器 (Monitoring Configuration Manager)
天工開物系統的監控、告警和日誌配置管理

此模組提供：
1. Prometheus 監控配置
2. Grafana 儀表板配置
3. 告警規則配置
4. 日誌聚合配置
5. 性能指標定義
6. 健康檢查配置

由狄仁傑(品質守護者)和墨子(運維工程師)聯合設計實現
"""

import yaml
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import logging

from ..utils.logging_config import get_system_logger

logger = get_system_logger("monitoring_config")

class MetricType(Enum):
    """指標類型"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

class AlertSeverity(Enum):
    """告警嚴重程度"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class LogLevel(Enum):
    """日誌級別"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class PrometheusConfig:
    """Prometheus 配置"""
    global_config: Dict[str, Any] = field(default_factory=dict)
    scrape_configs: List[Dict[str, Any]] = field(default_factory=list)
    rule_files: List[str] = field(default_factory=list)
    alerting: Dict[str, Any] = field(default_factory=dict)
    remote_write: List[Dict[str, Any]] = field(default_factory=list)
    remote_read: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'global': self.global_config,
            'scrape_configs': self.scrape_configs,
            'rule_files': self.rule_files,
            'alerting': self.alerting,
            'remote_write': self.remote_write,
            'remote_read': self.remote_read
        }

@dataclass
class AlertRule:
    """告警規則"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alert_name: str = ""
    expression: str = ""
    duration: str = "5m"
    severity: AlertSeverity = AlertSeverity.WARNING
    summary: str = ""
    description: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert': self.alert_name,
            'expr': self.expression,
            'for': self.duration,
            'labels': {
                'severity': self.severity.value,
                **self.labels
            },
            'annotations': {
                'summary': self.summary,
                'description': self.description,
                **self.annotations
            }
        }

@dataclass
class AlertingConfiguration:
    """告警配置"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    alertmanagers: List[Dict[str, Any]] = field(default_factory=list)
    alert_rules: List[AlertRule] = field(default_factory=list)
    notification_channels: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    routing_rules: Dict[str, Any] = field(default_factory=dict)
    inhibit_rules: List[Dict[str, Any]] = field(default_factory=list)
    templates: List[str] = field(default_factory=list)

@dataclass
class GrafanaDashboard:
    """Grafana 儀表板"""
    dashboard_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    panels: List[Dict[str, Any]] = field(default_factory=list)
    variables: List[Dict[str, Any]] = field(default_factory=list)
    time_range: Dict[str, str] = field(default_factory=lambda: {"from": "now-1h", "to": "now"})
    refresh: str = "5s"
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': None,
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'panels': self.panels,
            'templating': {
                'list': self.variables
            },
            'time': self.time_range,
            'refresh': self.refresh,
            'version': self.version,
            'schemaVersion': 30
        }

@dataclass
class LoggingConfiguration:
    """日誌配置"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    output_destinations: List[str] = field(default_factory=lambda: ["console"])
    file_config: Optional[Dict[str, Any]] = None
    elasticsearch_config: Optional[Dict[str, Any]] = None
    fluentd_config: Optional[Dict[str, Any]] = None
    retention_policy: Dict[str, Any] = field(default_factory=dict)
    aggregation_rules: List[Dict[str, Any]] = field(default_factory=list)

class MonitoringConfigManager:
    """監控配置管理器 - 天工開物系統監控配置核心組件"""
    
    def __init__(self, config_dir: str = "./monitoring"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置存儲
        self.prometheus_config: Optional[PrometheusConfig] = None
        self.alerting_config: Optional[AlertingConfiguration] = None
        self.grafana_dashboards: Dict[str, GrafanaDashboard] = {}
        self.logging_config: Optional[LoggingConfiguration] = None
        
        # 創建子目錄
        (self.config_dir / "prometheus").mkdir(exist_ok=True)
        (self.config_dir / "grafana" / "dashboards").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "grafana" / "datasources").mkdir(parents=True, exist_ok=True)
        (self.config_dir / "alertmanager").mkdir(exist_ok=True)
        (self.config_dir / "logging").mkdir(exist_ok=True)
        
        # 初始化預設配置
        self._initialize_default_configs()
        
        logger.info("監控配置管理器已初始化", extra={
            'config_dir': str(self.config_dir),
            'prometheus_enabled': self.prometheus_config is not None,
            'grafana_dashboards': len(self.grafana_dashboards),
            'alerting_enabled': self.alerting_config is not None
        })
    
    def _initialize_default_configs(self):
        """初始化預設配置"""
        
        # 初始化 Prometheus 配置
        self.prometheus_config = self._create_default_prometheus_config()
        
        # 初始化告警配置
        self.alerting_config = self._create_default_alerting_config()
        
        # 初始化 Grafana 儀表板
        self._create_default_grafana_dashboards()
        
        # 初始化日誌配置
        self.logging_config = self._create_default_logging_config()
    
    def _create_default_prometheus_config(self) -> PrometheusConfig:
        """創建預設 Prometheus 配置"""
        
        global_config = {
            'scrape_interval': '15s',
            'evaluation_interval': '15s',
            'scrape_timeout': '10s'
        }
        
        scrape_configs = [
            # Prometheus 自身監控
            {
                'job_name': 'prometheus',
                'static_configs': [
                    {
                        'targets': ['localhost:9090']
                    }
                ]
            },
            
            # TradingAgents API 監控
            {
                'job_name': 'tradingagents-api',
                'static_configs': [
                    {
                        'targets': ['tradingagents-api:8000']
                    }
                ],
                'metrics_path': '/metrics',
                'scrape_interval': '5s'
            },
            
            # Node Exporter (系統指標)
            {
                'job_name': 'node-exporter',
                'static_configs': [
                    {
                        'targets': ['node-exporter:9100']
                    }
                ]
            },
            
            # cAdvisor (容器指標)
            {
                'job_name': 'cadvisor',
                'static_configs': [
                    {
                        'targets': ['cadvisor:8080']
                    }
                ]
            },
            
            # PostgreSQL 指標
            {
                'job_name': 'postgres-exporter',
                'static_configs': [
                    {
                        'targets': ['postgres-exporter:9187']
                    }
                ]
            },
            
            # Redis 指標
            {
                'job_name': 'redis-exporter',
                'static_configs': [
                    {
                        'targets': ['redis-exporter:9121']
                    }
                ]
            }
        ]
        
        alerting = {
            'alertmanagers': [
                {
                    'static_configs': [
                        {
                            'targets': ['alertmanager:9093']
                        }
                    ]
                }
            ]
        }
        
        rule_files = [
            'alerts/*.yml'
        ]
        
        return PrometheusConfig(
            global_config=global_config,
            scrape_configs=scrape_configs,
            alerting=alerting,
            rule_files=rule_files
        )
    
    def _create_default_alerting_config(self) -> AlertingConfiguration:
        """創建預設告警配置"""
        
        # 告警規則
        alert_rules = [
            # 高 CPU 使用率告警
            AlertRule(
                alert_name="HighCPUUsage",
                expression="100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
                duration="5m",
                severity=AlertSeverity.WARNING,
                summary="High CPU usage detected",
                description="CPU usage is above 80% for more than 5 minutes on {{ $labels.instance }}"
            ),
            
            # 高記憶體使用率告警
            AlertRule(
                alert_name="HighMemoryUsage",
                expression="(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85",
                duration="5m",
                severity=AlertSeverity.WARNING,
                summary="High memory usage detected",
                description="Memory usage is above 85% for more than 5 minutes on {{ $labels.instance }}"
            ),
            
            # 磁碟空間不足告警
            AlertRule(
                alert_name="LowDiskSpace",
                expression="(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90",
                duration="5m",
                severity=AlertSeverity.CRITICAL,
                summary="Low disk space detected",
                description="Disk usage is above 90% on {{ $labels.instance }} {{ $labels.mountpoint }}"
            ),
            
            # 服務不可用告警
            AlertRule(
                alert_name="ServiceDown",
                expression="up == 0",
                duration="1m",
                severity=AlertSeverity.CRITICAL,
                summary="Service is down",
                description="Service {{ $labels.job }} on {{ $labels.instance }} is down"
            ),
            
            # API 高延遲告警
            AlertRule(
                alert_name="HighAPILatency",
                expression="histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5",
                duration="5m",
                severity=AlertSeverity.WARNING,
                summary="High API latency detected",
                description="95th percentile latency is above 500ms for {{ $labels.job }}"
            ),
            
            # API 高錯誤率告警
            AlertRule(
                alert_name="HighAPIErrorRate",
                expression="rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) > 0.05",
                duration="5m",
                severity=AlertSeverity.CRITICAL,
                summary="High API error rate detected",
                description="API error rate is above 5% for {{ $labels.job }}"
            ),
            
            # 資料庫連線數過高告警
            AlertRule(
                alert_name="HighDatabaseConnections",
                expression="pg_stat_activity_count > 80",
                duration="5m",
                severity=AlertSeverity.WARNING,
                summary="High database connection count",
                description="Database connection count is above 80 on {{ $labels.instance }}"
            ),
            
            # Redis 記憶體使用率過高告警
            AlertRule(
                alert_name="HighRedisMemoryUsage",
                expression="redis_memory_used_bytes / redis_memory_max_bytes * 100 > 90",
                duration="5m",
                severity=AlertSeverity.WARNING,
                summary="High Redis memory usage",
                description="Redis memory usage is above 90% on {{ $labels.instance }}"
            )
        ]
        
        # 通知渠道
        notification_channels = {
            'slack': {
                'api_url': '${SLACK_WEBHOOK_URL}',
                'channel': '#alerts',
                'username': 'TianGong-AlertManager',
                'title': 'TradingAgents Alert',
                'text': '{{ range .Alerts }}{{ .Annotations.summary }}\n{{ .Annotations.description }}{{ end }}'
            },
            
            'email': {
                'smtp_server': '${SMTP_SERVER}',
                'smtp_port': 587,
                'from': '${ALERT_EMAIL_FROM}',
                'to': ['${ALERT_EMAIL_TO}'],
                'subject': 'TradingAgents Alert: {{ .GroupLabels.alertname }}',
                'body': '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
            },
            
            'webhook': {
                'url': '${WEBHOOK_URL}',
                'http_config': {
                    'timeout': '10s'
                }
            }
        }
        
        # 路由規則
        routing_rules = {
            'group_by': ['alertname', 'cluster', 'service'],
            'group_wait': '10s',
            'group_interval': '10s',
            'repeat_interval': '1h',
            'receiver': 'default',
            'routes': [
                {
                    'match': {
                        'severity': 'critical'
                    },
                    'receiver': 'critical-alerts',
                    'group_wait': '5s',
                    'repeat_interval': '15m'
                },
                {
                    'match': {
                        'service': 'tradingagents-api'
                    },
                    'receiver': 'api-alerts',
                    'group_interval': '30s'
                }
            ]
        }
        
        return AlertingConfiguration(
            alert_rules=alert_rules,
            notification_channels=notification_channels,
            routing_rules=routing_rules
        )
    
    def _create_default_grafana_dashboards(self):
        """創建預設 Grafana 儀表板"""
        
        # TradingAgents 系統概覽儀表板
        system_overview = self._create_system_overview_dashboard()
        self.grafana_dashboards['system-overview'] = system_overview
        
        # API 性能儀表板
        api_performance = self._create_api_performance_dashboard()
        self.grafana_dashboards['api-performance'] = api_performance
        
        # 基礎設施監控儀表板
        infrastructure = self._create_infrastructure_dashboard()
        self.grafana_dashboards['infrastructure'] = infrastructure
        
        # 資料庫監控儀表板
        database = self._create_database_dashboard()
        self.grafana_dashboards['database'] = database
    
    def _create_system_overview_dashboard(self) -> GrafanaDashboard:
        """創建系統概覽儀表板"""
        
        panels = [
            # 系統狀態指示器
            {
                'id': 1,
                'title': 'Service Status',
                'type': 'stat',
                'targets': [
                    {
                        'expr': 'up{job="tradingagents-api"}',
                        'legendFormat': 'API Status'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'mappings': [
                            {'value': 1, 'text': 'UP', 'color': 'green'},
                            {'value': 0, 'text': 'DOWN', 'color': 'red'}
                        ]
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
            },
            
            # CPU 使用率
            {
                'id': 2,
                'title': 'CPU Usage',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)',
                        'legendFormat': '{{ instance }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'percent',
                        'max': 100,
                        'thresholds': {
                            'steps': [
                                {'color': 'green', 'value': 0},
                                {'color': 'yellow', 'value': 70},
                                {'color': 'red', 'value': 90}
                            ]
                        }
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
            },
            
            # 記憶體使用率
            {
                'id': 3,
                'title': 'Memory Usage',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100',
                        'legendFormat': '{{ instance }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'percent',
                        'max': 100,
                        'thresholds': {
                            'steps': [
                                {'color': 'green', 'value': 0},
                                {'color': 'yellow', 'value': 80},
                                {'color': 'red', 'value': 95}
                            ]
                        }
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
            },
            
            # 網路流量
            {
                'id': 4,
                'title': 'Network Traffic',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'rate(node_network_receive_bytes_total[5m])',
                        'legendFormat': 'RX {{ device }}'
                    },
                    {
                        'expr': 'rate(node_network_transmit_bytes_total[5m])',
                        'legendFormat': 'TX {{ device }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'binBps'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 8}
            }
        ]
        
        return GrafanaDashboard(
            title="TradingAgents - System Overview",
            description="整體系統監控概覽",
            tags=["tradingagents", "overview", "system"],
            panels=panels,
            refresh="5s"
        )
    
    def _create_api_performance_dashboard(self) -> GrafanaDashboard:
        """創建 API 性能儀表板"""
        
        panels = [
            # 請求率
            {
                'id': 1,
                'title': 'Request Rate',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'rate(http_requests_total[5m])',
                        'legendFormat': '{{ method }} {{ endpoint }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'reqps'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
            },
            
            # 回應時間
            {
                'id': 2,
                'title': 'Response Time',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))',
                        'legendFormat': 'p50'
                    },
                    {
                        'expr': 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
                        'legendFormat': 'p95'
                    },
                    {
                        'expr': 'histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))',
                        'legendFormat': 'p99'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 's'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
            },
            
            # 錯誤率
            {
                'id': 3,
                'title': 'Error Rate',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'rate(http_requests_total{status=~"4.."}[5m])',
                        'legendFormat': '4xx'
                    },
                    {
                        'expr': 'rate(http_requests_total{status=~"5.."}[5m])',
                        'legendFormat': '5xx'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'reqps'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
            },
            
            # 活躍連線數
            {
                'id': 4,
                'title': 'Active Connections',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'active_connections',
                        'legendFormat': 'Active Connections'
                    }
                ],
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 8}
            }
        ]
        
        return GrafanaDashboard(
            title="TradingAgents - API Performance",
            description="API 性能監控",
            tags=["tradingagents", "api", "performance"],
            panels=panels,
            refresh="5s"
        )
    
    def _create_infrastructure_dashboard(self) -> GrafanaDashboard:
        """創建基礎設施儀表板"""
        
        panels = [
            # 磁碟使用率
            {
                'id': 1,
                'title': 'Disk Usage',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': '(1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100',
                        'legendFormat': '{{ instance }} {{ mountpoint }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'percent',
                        'max': 100
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
            },
            
            # 磁碟 I/O
            {
                'id': 2,
                'title': 'Disk I/O',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'rate(node_disk_read_bytes_total[5m])',
                        'legendFormat': 'Read {{ device }}'
                    },
                    {
                        'expr': 'rate(node_disk_written_bytes_total[5m])',
                        'legendFormat': 'Write {{ device }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'binBps'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
            },
            
            # 負載平均
            {
                'id': 3,
                'title': 'Load Average',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'node_load1',
                        'legendFormat': '1m'
                    },
                    {
                        'expr': 'node_load5',
                        'legendFormat': '5m'
                    },
                    {
                        'expr': 'node_load15',
                        'legendFormat': '15m'
                    }
                ],
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
            },
            
            # 程序數量
            {
                'id': 4,
                'title': 'Process Count',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'node_procs_running',
                        'legendFormat': 'Running'
                    },
                    {
                        'expr': 'node_procs_blocked',
                        'legendFormat': 'Blocked'
                    }
                ],
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 8}
            }
        ]
        
        return GrafanaDashboard(
            title="TradingAgents - Infrastructure",
            description="基礎設施監控",
            tags=["tradingagents", "infrastructure", "system"],
            panels=panels,
            refresh="30s"
        )
    
    def _create_database_dashboard(self) -> GrafanaDashboard:
        """創建資料庫儀表板"""
        
        panels = [
            # 資料庫連線數
            {
                'id': 1,
                'title': 'Database Connections',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'pg_stat_activity_count',
                        'legendFormat': 'Active Connections'
                    },
                    {
                        'expr': 'pg_settings_max_connections',
                        'legendFormat': 'Max Connections'
                    }
                ],
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 0}
            },
            
            # 查詢執行時間
            {
                'id': 2,
                'title': 'Query Execution Time',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'pg_stat_activity_max_tx_duration',
                        'legendFormat': 'Max Transaction Duration'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 's'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 0}
            },
            
            # 資料庫大小
            {
                'id': 3,
                'title': 'Database Size',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'pg_database_size_bytes',
                        'legendFormat': '{{ datname }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'binBytes'
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 0, 'y': 8}
            },
            
            # 緩存命中率
            {
                'id': 4,
                'title': 'Cache Hit Ratio',
                'type': 'timeseries',
                'targets': [
                    {
                        'expr': 'pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) * 100',
                        'legendFormat': '{{ datname }}'
                    }
                ],
                'fieldConfig': {
                    'defaults': {
                        'unit': 'percent',
                        'max': 100
                    }
                },
                'gridPos': {'h': 8, 'w': 12, 'x': 12, 'y': 8}
            }
        ]
        
        return GrafanaDashboard(
            title="TradingAgents - Database",
            description="資料庫性能監控",
            tags=["tradingagents", "database", "postgresql"],
            panels=panels,
            refresh="10s"
        )
    
    def _create_default_logging_config(self) -> LoggingConfiguration:
        """創建預設日誌配置"""
        
        return LoggingConfiguration(
            log_level=LogLevel.INFO,
            log_format="json",
            output_destinations=["console", "file"],
            file_config={
                'filename': 'logs/tradingagents.log',
                'max_size': '100MB',
                'max_files': 10,
                'compress': True
            },
            elasticsearch_config={
                'enabled': False,
                'hosts': ['elasticsearch:9200'],
                'index_pattern': 'tradingagents-logs-%Y.%m.%d',
                'timeout': 30
            },
            retention_policy={
                'file_retention_days': 30,
                'elasticsearch_retention_days': 90
            },
            aggregation_rules=[
                {
                    'name': 'error_aggregation',
                    'pattern': 'ERROR',
                    'group_by': ['service', 'error_type'],
                    'window': '5m'
                }
            ]
        )
    
    def save_prometheus_config(self, output_file: Optional[str] = None) -> str:
        """保存 Prometheus 配置"""
        
        if not self.prometheus_config:
            raise ValueError("Prometheus 配置未初始化")
        
        config_file = output_file or str(self.config_dir / "prometheus" / "prometheus.yml")
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(self.prometheus_config.to_dict(), f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已保存 Prometheus 配置: {config_file}")
        return config_file
    
    def save_alert_rules(self, output_file: Optional[str] = None) -> str:
        """保存告警規則"""
        
        if not self.alerting_config or not self.alerting_config.alert_rules:
            raise ValueError("告警配置未初始化")
        
        config_file = output_file or str(self.config_dir / "prometheus" / "alerts.yml")
        
        groups = [{
            'name': 'tradingagents.rules',
            'rules': [rule.to_dict() for rule in self.alerting_config.alert_rules]
        }]
        
        alert_config = {'groups': groups}
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(alert_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已保存告警規則: {config_file}")
        return config_file
    
    def save_alertmanager_config(self, output_file: Optional[str] = None) -> str:
        """保存 Alertmanager 配置"""
        
        if not self.alerting_config:
            raise ValueError("告警配置未初始化")
        
        config_file = output_file or str(self.config_dir / "alertmanager" / "alertmanager.yml")
        
        # 構建 Alertmanager 配置
        alertmanager_config = {
            'global': {
                'smtp_smarthost': '${SMTP_SERVER}:587',
                'smtp_from': '${ALERT_EMAIL_FROM}'
            },
            'route': self.alerting_config.routing_rules,
            'receivers': [
                {
                    'name': 'default',
                    'slack_configs': [
                        self.alerting_config.notification_channels.get('slack', {})
                    ]
                },
                {
                    'name': 'critical-alerts',
                    'email_configs': [
                        self.alerting_config.notification_channels.get('email', {})
                    ],
                    'slack_configs': [
                        self.alerting_config.notification_channels.get('slack', {})
                    ]
                },
                {
                    'name': 'api-alerts',
                    'webhook_configs': [
                        self.alerting_config.notification_channels.get('webhook', {})
                    ]
                }
            ],
            'inhibit_rules': self.alerting_config.inhibit_rules,
            'templates': self.alerting_config.templates
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(alertmanager_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已保存 Alertmanager 配置: {config_file}")
        return config_file
    
    def save_grafana_dashboards(self, output_dir: Optional[str] = None) -> List[str]:
        """保存 Grafana 儀表板"""
        
        dashboard_dir = output_dir or str(self.config_dir / "grafana" / "dashboards")
        dashboard_files = []
        
        for dashboard_name, dashboard in self.grafana_dashboards.items():
            dashboard_file = f"{dashboard_dir}/{dashboard_name}.json"
            
            dashboard_data = {
                'dashboard': dashboard.to_dict(),
                'overwrite': True
            }
            
            with open(dashboard_file, 'w', encoding='utf-8') as f:
                json.dump(dashboard_data, f, indent=2, ensure_ascii=False)
            
            dashboard_files.append(dashboard_file)
        
        logger.info(f"已保存 Grafana 儀表板: {len(dashboard_files)} 個文件")
        return dashboard_files
    
    def save_grafana_datasource(self, datasource_config: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """保存 Grafana 數據源配置"""
        
        config_file = output_file or str(self.config_dir / "grafana" / "datasources" / "prometheus.yml")
        
        datasource_config_default = {
            'apiVersion': 1,
            'datasources': [
                {
                    'name': 'Prometheus',
                    'type': 'prometheus',
                    'access': 'proxy',
                    'url': 'http://prometheus:9090',
                    'isDefault': True,
                    'editable': True
                }
            ]
        }
        
        # 合併配置
        final_config = {**datasource_config_default, **datasource_config}
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(final_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已保存 Grafana 數據源配置: {config_file}")
        return config_file
    
    def save_logging_config(self, output_file: Optional[str] = None) -> str:
        """保存日誌配置"""
        
        if not self.logging_config:
            raise ValueError("日誌配置未初始化")
        
        config_file = output_file or str(self.config_dir / "logging" / "logging.yml")
        
        logging_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
                },
                'console': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'console' if self.logging_config.log_format == 'console' else 'json',
                    'level': self.logging_config.log_level.value.upper()
                }
            },
            'root': {
                'level': self.logging_config.log_level.value.upper(),
                'handlers': ['console']
            }
        }
        
        # 添加文件處理器
        if 'file' in self.logging_config.output_destinations and self.logging_config.file_config:
            logging_config['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': self.logging_config.file_config['filename'],
                'maxBytes': self._parse_size(self.logging_config.file_config['max_size']),
                'backupCount': self.logging_config.file_config['max_files'],
                'formatter': 'json',
                'level': self.logging_config.log_level.value.upper()
            }
            logging_config['root']['handlers'].append('file')
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(logging_config, f, default_flow_style=False, allow_unicode=True)
        
        logger.info(f"已保存日誌配置: {config_file}")
        return config_file
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)
    
    def deploy_monitoring_configs(self, environment: str = "production") -> Dict[str, str]:
        """部署所有監控配置"""
        
        deployed_files = {}
        
        logger.info(f"開始部署監控配置: {environment}")
        
        try:
            # 保存 Prometheus 配置
            prometheus_file = self.save_prometheus_config()
            deployed_files['prometheus_config'] = prometheus_file
            
            # 保存告警規則
            alerts_file = self.save_alert_rules()
            deployed_files['alert_rules'] = alerts_file
            
            # 保存 Alertmanager 配置
            alertmanager_file = self.save_alertmanager_config()
            deployed_files['alertmanager_config'] = alertmanager_file
            
            # 保存 Grafana 儀表板
            dashboard_files = self.save_grafana_dashboards()
            deployed_files['grafana_dashboards'] = dashboard_files
            
            # 保存 Grafana 數據源
            datasource_file = self.save_grafana_datasource({})
            deployed_files['grafana_datasource'] = datasource_file
            
            # 保存日誌配置
            logging_file = self.save_logging_config()
            deployed_files['logging_config'] = logging_file
            
            logger.info(f"監控配置部署完成: {environment}", extra={
                'deployed_files': len(deployed_files),
                'config_types': list(deployed_files.keys())
            })
            
        except Exception as e:
            logger.error(f"監控配置部署失敗: {e}")
            raise
        
        return deployed_files

def create_monitoring_config(config_dir: str = "./monitoring") -> MonitoringConfigManager:
    """創建監控配置管理器實例"""
    return MonitoringConfigManager(config_dir)

if __name__ == "__main__":
    # 測試腳本
    def test_monitoring_config():
        print("測試監控配置管理器...")
        
        # 創建管理器
        manager = create_monitoring_config()
        
        # 部署所有配置
        deployed_files = manager.deploy_monitoring_configs("development")
        
        print(f"部署結果:")
        for config_type, files in deployed_files.items():
            if isinstance(files, list):
                print(f"  {config_type}: {len(files)} 個文件")
            else:
                print(f"  {config_type}: {files}")
        
        print("監控配置管理器測試完成")
    
    test_monitoring_config()