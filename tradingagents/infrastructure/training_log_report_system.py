#!/usr/bin/env python3
"""
訓練日誌和報告系統 - 基礎設施團隊 Task 3.3
提供企業級訓練日誌收集、分析、報告生成和可視化功能

This system provides:
- Comprehensive training log collection and aggregation
- Real-time log analysis and pattern detection
- Automated report generation with multiple formats
- Performance trend analysis and visualization
- Integration with existing monitoring and alerting
- Training metrics dashboard and insights

Author: 小c (基礎設施團隊)
Version: 1.0.0
"""

import os
import sys
import json
import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union, Tuple, Generator
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
import queue
import subprocess
from concurrent.futures import ThreadPoolExecutor
import re
import sqlite3
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import matplotlib.pyplot as plt
import seaborn as sns
from jinja2 import Template
import yaml
import aiofiles
import aiohttp

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [訓練日誌報告] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/infrastructure/training_log_report.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TrainingLogReport")


class LogLevel(Enum):
    """日誌級別"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReportFormat(Enum):
    """報告格式"""
    HTML = "html"
    PDF = "pdf"
    JSON = "json"
    CSV = "csv"
    MARKDOWN = "markdown"


class TrainingPhase(Enum):
    """訓練階段"""
    PREPARATION = "preparation"
    TRAINING = "training"
    VALIDATION = "validation"
    EVALUATION = "evaluation"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrainingLogEntry:
    """訓練日誌條目"""
    log_id: str
    timestamp: datetime
    level: LogLevel
    message: str
    training_id: str
    phase: TrainingPhase
    component: str  # 組件名稱
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_file: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class TrainingSession:
    """訓練會話"""
    session_id: str
    training_id: str
    model_name: str
    training_type: str  # SFT, LoRA, GRPO
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "running"
    config: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    logs: List[TrainingLogEntry] = field(default_factory=list)
    performance_summary: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """性能指標"""
    metric_id: str
    training_id: str
    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    phase: TrainingPhase
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrainingReport:
    """訓練報告"""
    report_id: str
    training_id: str
    generated_at: datetime
    report_type: str
    format: ReportFormat
    content: str
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class LogCollector:
    """日誌收集器"""
    
    def __init__(self, log_directories: List[str] = None):
        self.log_directories = log_directories or [
            "/app/logs/training",
            "/app/logs/gpu_orchestrator",
            "/app/logs/infrastructure"
        ]
        self.log_patterns = {
            "training": r".*training.*\.log",
            "gpu": r".*gpu.*\.log",
            "system": r".*system.*\.log"
        }
        self.collected_logs: List[TrainingLogEntry] = []
        self.log_queue = asyncio.Queue()
        self.logger = logging.getLogger(f"{logger.name}.Collector")
    
    async def collect_existing_logs(self):
        """收集現有日誌"""
        for directory in self.log_directories:
            if os.path.exists(directory):
                await self._scan_directory(directory)
    
    async def _scan_directory(self, directory: str):
        """掃描目錄中的日誌文件"""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if any(re.match(pattern, file) for pattern in self.log_patterns.values()):
                        file_path = os.path.join(root, file)
                        await self._parse_log_file(file_path)
        except Exception as e:
            self.logger.error(f"掃描目錄失敗 {directory}: {str(e)}")
    
    async def _parse_log_file(self, file_path: str):
        """解析日誌文件"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                async for line in f:
                    log_entry = self._parse_log_line(line, file_path)
                    if log_entry:
                        self.collected_logs.append(log_entry)
        except Exception as e:
            self.logger.error(f"解析日誌文件失敗 {file_path}: {str(e)}")
    
    def _parse_log_line(self, line: str, source_file: str) -> Optional[TrainingLogEntry]:
        """解析單行日誌"""
        try:
            # 標準日誌格式: 2025-08-10 10:30:45 - [組件] - INFO - 消息
            pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - \[([^\]]+)\] - (\w+) - (.+)'
            match = re.match(pattern, line.strip())
            
            if match:
                timestamp_str, component, level_str, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                
                # 提取訓練相關信息
                training_info = self._extract_training_info(message, component)
                
                return TrainingLogEntry(
                    log_id=str(uuid.uuid4()),
                    timestamp=timestamp,
                    level=LogLevel(level_str.lower()),
                    message=message,
                    training_id=training_info.get('training_id', 'unknown'),
                    phase=training_info.get('phase', TrainingPhase.TRAINING),
                    component=component,
                    metrics=training_info.get('metrics', {}),
                    metadata=training_info.get('metadata', {}),
                    source_file=source_file
                )
        except Exception as e:
            self.logger.debug(f"解析日誌行失敗: {str(e)}")
        
        return None
    
    def _extract_training_info(self, message: str, component: str) -> Dict[str, Any]:
        """從日誌消息中提取訓練信息"""
        info = {
            'training_id': 'unknown',
            'phase': TrainingPhase.TRAINING,
            'metrics': {},
            'metadata': {}
        }
        
        # 提取訓練ID
        training_id_match = re.search(r'training_id[:\s]+([a-zA-Z0-9_-]+)', message)
        if training_id_match:
            info['training_id'] = training_id_match.group(1)
        
        # 提取階段信息
        if 'preparation' in message.lower():
            info['phase'] = TrainingPhase.PREPARATION
        elif 'validation' in message.lower():
            info['phase'] = TrainingPhase.VALIDATION
        elif 'evaluation' in message.lower():
            info['phase'] = TrainingPhase.EVALUATION
        elif 'completed' in message.lower():
            info['phase'] = TrainingPhase.COMPLETED
        elif 'failed' in message.lower():
            info['phase'] = TrainingPhase.FAILED
        
        # 提取指標
        metrics_patterns = {
            'loss': r'loss[:\s]+([0-9.]+)',
            'accuracy': r'accuracy[:\s]+([0-9.]+)',
            'reward': r'reward[:\s]+([0-9.]+)',
            'learning_rate': r'learning_rate[:\s]+([0-9.]+)',
            'epoch': r'epoch[:\s]+([0-9]+)',
            'step': r'step[:\s]+([0-9]+)'
        }
        
        for metric_name, pattern in metrics_patterns.items():
            match = re.search(pattern, message)
            if match:
                try:
                    info['metrics'][metric_name] = float(match.group(1))
                except ValueError:
                    info['metrics'][metric_name] = match.group(1)
        
        return info
    
    async def get_logs(self, 
                      training_id: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      level: Optional[LogLevel] = None,
                      component: Optional[str] = None) -> List[TrainingLogEntry]:
        """獲取日誌條目"""
        filtered_logs = self.collected_logs
        
        if training_id:
            filtered_logs = [log for log in filtered_logs if log.training_id == training_id]
        
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        
        if level:
            filtered_logs = [log for log in filtered_logs if log.level == level]
        
        if component:
            filtered_logs = [log for log in filtered_logs if log.component == component]
        
        return sorted(filtered_logs, key=lambda x: x.timestamp)


class LogAnalyzer:
    """日誌分析器"""
    
    def __init__(self):
        self.analysis_cache: Dict[str, Any] = {}
        self.patterns: Dict[str, re.Pattern] = {}
        self.logger = logging.getLogger(f"{logger.name}.Analyzer")
        
        self._setup_patterns()
    
    def _setup_patterns(self):
        """設置分析模式"""
        self.patterns = {
            'error_pattern': re.compile(r'error|exception|failed|failure', re.IGNORECASE),
            'performance_pattern': re.compile(r'performance|speed|throughput|latency', re.IGNORECASE),
            'resource_pattern': re.compile(r'memory|cpu|gpu|disk|network', re.IGNORECASE),
            'training_pattern': re.compile(r'epoch|step|loss|accuracy|reward', re.IGNORECASE)
        }
    
    def analyze_logs(self, logs: List[TrainingLogEntry]) -> Dict[str, Any]:
        """分析日誌"""
        analysis = {
            'total_logs': len(logs),
            'log_levels': defaultdict(int),
            'components': defaultdict(int),
            'phases': defaultdict(int),
            'error_count': 0,
            'warning_count': 0,
            'performance_issues': [],
            'resource_issues': [],
            'training_metrics': defaultdict(list),
            'timeline': [],
            'patterns': {}
        }
        
        for log in logs:
            # 統計日誌級別
            analysis['log_levels'][log.level.value] += 1
            
            # 統計組件
            analysis['components'][log.component] += 1
            
            # 統計階段
            analysis['phases'][log.phase.value] += 1
            
            # 檢查錯誤和警告
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                analysis['error_count'] += 1
            elif log.level == LogLevel.WARNING:
                analysis['warning_count'] += 1
            
            # 檢查性能問題
            if self.patterns['performance_pattern'].search(log.message):
                analysis['performance_issues'].append({
                    'timestamp': log.timestamp,
                    'message': log.message,
                    'component': log.component
                })
            
            # 檢查資源問題
            if self.patterns['resource_pattern'].search(log.message):
                analysis['resource_issues'].append({
                    'timestamp': log.timestamp,
                    'message': log.message,
                    'component': log.component
                })
            
            # 收集訓練指標
            for metric_name, value in log.metrics.items():
                analysis['training_metrics'][metric_name].append({
                    'timestamp': log.timestamp,
                    'value': value,
                    'phase': log.phase.value
                })
            
            # 時間線
            analysis['timeline'].append({
                'timestamp': log.timestamp,
                'level': log.level.value,
                'component': log.component,
                'phase': log.phase.value,
                'message': log.message[:100]  # 截斷長消息
            })
        
        # 分析模式
        analysis['patterns'] = self._analyze_patterns(logs)
        
        return analysis
    
    def _analyze_patterns(self, logs: List[TrainingLogEntry]) -> Dict[str, Any]:
        """分析日誌模式"""
        patterns = {
            'error_patterns': defaultdict(int),
            'common_messages': defaultdict(int),
            'component_interactions': defaultdict(int),
            'time_distribution': defaultdict(int)
        }
        
        for log in logs:
            # 錯誤模式
            if log.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                error_type = self._classify_error(log.message)
                patterns['error_patterns'][error_type] += 1
            
            # 常見消息
            message_key = log.message[:50]  # 前50個字符作為鍵
            patterns['common_messages'][message_key] += 1
            
            # 組件交互
            patterns['component_interactions'][log.component] += 1
            
            # 時間分布
            hour = log.timestamp.hour
            patterns['time_distribution'][hour] += 1
        
        return patterns
    
    def _classify_error(self, message: str) -> str:
        """分類錯誤類型"""
        if 'memory' in message.lower():
            return 'memory_error'
        elif 'gpu' in message.lower():
            return 'gpu_error'
        elif 'network' in message.lower():
            return 'network_error'
        elif 'timeout' in message.lower():
            return 'timeout_error'
        elif 'permission' in message.lower():
            return 'permission_error'
        else:
            return 'general_error'
    
    def generate_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 錯誤率分析
        total_logs = analysis['total_logs']
        error_rate = analysis['error_count'] / total_logs if total_logs > 0 else 0
        
        if error_rate > 0.1:
            insights.append(f"錯誤率較高: {error_rate:.2%}，建議檢查系統穩定性")
        
        # 性能問題
        if analysis['performance_issues']:
            insights.append(f"發現 {len(analysis['performance_issues'])} 個性能相關問題")
        
        # 資源問題
        if analysis['resource_issues']:
            insights.append(f"發現 {len(analysis['resource_issues'])} 個資源相關問題")
        
        # 組件分析
        component_counts = analysis['components']
        if component_counts:
            most_active = max(component_counts.items(), key=lambda x: x[1])
            insights.append(f"最活躍的組件: {most_active[0]} ({most_active[1]} 條日誌)")
        
        return insights


class TrainingLogReportSystem:
    """訓練日誌和報告系統主控制器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/app/config/training_log_report.yaml"
        self.sessions: Dict[str, TrainingSession] = {}
        self.reports: List[TrainingReport] = []
        
        # 初始化組件
        self.collector = LogCollector()
        self.analyzer = LogAnalyzer()
        
        # 監控狀態
        self.is_running = False
        self.monitor_task = None
        
        # 統計信息
        self.stats = {
            'total_sessions': 0,
            'active_sessions': 0,
            'total_reports': 0,
            'total_logs_collected': 0
        }
        
        self.logger = logging.getLogger(f"{logger.name}.System")
        
        # 加載配置
        self._load_configuration()
    
    def _load_configuration(self):
        """加載系統配置"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # 加載配置
                self.logger.info("配置加載成功")
        except Exception as e:
            self.logger.error(f"加載配置失敗: {str(e)}")
    
    async def start(self):
        """啟動系統"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 收集現有日誌
        await self.collector.collect_existing_logs()
        
        # 啟動監控任務
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
        self.logger.info("訓練日誌報告系統已啟動")
    
    async def stop(self):
        """停止系統"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("訓練日誌報告系統已停止")
    
    async def _monitor_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                # 更新統計信息
                self._update_stats()
                
                # 檢查新的訓練會話
                await self._check_new_sessions()
                
                # 等待下一次檢查
                await asyncio.sleep(60)  # 每分鐘檢查一次
                
            except Exception as e:
                self.logger.error(f"監控循環錯誤: {str(e)}")
                await asyncio.sleep(120)
    
    async def _check_new_sessions(self):
        """檢查新的訓練會話"""
        # 這裡可以實現檢查新訓練會話的邏輯
        pass
    
    def _update_stats(self):
        """更新統計信息"""
        self.stats['total_sessions'] = len(self.sessions)
        self.stats['active_sessions'] = len([s for s in self.sessions.values() if s.status == "running"])
        self.stats['total_reports'] = len(self.reports)
        self.stats['total_logs_collected'] = len(self.collector.collected_logs)
    
    async def create_session(self, training_id: str, model_name: str, training_type: str, config: Dict[str, Any]) -> TrainingSession:
        """創建訓練會話"""
        session = TrainingSession(
            session_id=str(uuid.uuid4()),
            training_id=training_id,
            model_name=model_name,
            training_type=training_type,
            start_time=datetime.now(),
            config=config
        )
        
        self.sessions[session.session_id] = session
        self.logger.info(f"創建訓練會話: {training_id}")
        
        return session
    
    async def end_session(self, session_id: str, status: str = "completed", metrics: Dict[str, Any] = None):
        """結束訓練會話"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.end_time = datetime.now()
            session.status = status
            if metrics:
                session.metrics.update(metrics)
            
            self.logger.info(f"結束訓練會話: {session.training_id} - {status}")
    
    async def add_log_entry(self, session_id: str, log_entry: TrainingLogEntry):
        """添加日誌條目"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.logs.append(log_entry)
            
            # 同時添加到收集器
            self.collector.collected_logs.append(log_entry)
    
    async def get_logs(self, 
                      session_id: Optional[str] = None,
                      training_id: Optional[str] = None,
                      start_time: Optional[datetime] = None,
                      end_time: Optional[datetime] = None,
                      level: Optional[LogLevel] = None,
                      component: Optional[str] = None) -> List[TrainingLogEntry]:
        """獲取日誌"""
        if session_id and session_id in self.sessions:
            logs = self.sessions[session_id].logs
        else:
            logs = self.collector.collected_logs
        
        return await self.collector.get_logs(
            training_id=training_id,
            start_time=start_time,
            end_time=end_time,
            level=level,
            component=component
        )
    
    def get_sessions(self, status: Optional[str] = None) -> List[TrainingSession]:
        """獲取會話列表"""
        sessions = list(self.sessions.values())
        
        if status:
            sessions = [s for s in sessions if s.status == status]
        
        return sorted(sessions, key=lambda x: x.start_time, reverse=True)
    
    def get_reports(self, training_id: Optional[str] = None) -> List[TrainingReport]:
        """獲取報告列表"""
        reports = self.reports
        
        if training_id:
            reports = [r for r in reports if r.training_id == training_id]
        
        return sorted(reports, key=lambda x: x.generated_at, reverse=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 創建系統實例的工廠函數
def create_training_log_report_system(config_path: Optional[str] = None) -> TrainingLogReportSystem:
    """創建訓練日誌報告系統實例"""
    return TrainingLogReportSystem(config_path)


if __name__ == "__main__":
    # 測試代碼
    async def test_system():
        system = create_training_log_report_system()
        await system.start()
        
        # 創建測試會話
        session = await system.create_session(
            training_id="test_training_001",
            model_name="test_model",
            training_type="GRPO",
            config={"epochs": 10, "batch_size": 32}
        )
        
        # 添加測試日誌
        test_log = TrainingLogEntry(
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            level=LogLevel.INFO,
            message="測試訓練開始",
            training_id="test_training_001",
            phase=TrainingPhase.TRAINING,
            component="test_component",
            metrics={"loss": 0.5, "accuracy": 0.85}
        )
        
        await system.add_log_entry(session.session_id, test_log)
        
        print("訓練日誌報告系統測試完成")
        
        # 運行一段時間
        await asyncio.sleep(30)
        await system.stop()
    
    asyncio.run(test_system())
