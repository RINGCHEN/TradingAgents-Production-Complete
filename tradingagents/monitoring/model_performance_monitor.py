#!/usr/bin/env python3
"""
模型性能监控和能力更新机制
GPT-OSS 整合任务 1.2.2 - 性能监控组件

提供实时性能跟踪、动态能力评分更新和智能警报功能。
支持多维度性能指标监控和自适应阈值调整。
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import uuid

from ..database.model_capability_db import ModelCapabilityDB, ModelCapabilityUpdate
from ..database.task_metadata_models import TaskPerformanceMetric
from ..utils.llm_client import LLMClient, LLMProvider, LLMResponse

# 设置日志
logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """性能指标类型"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    SUCCESS_RATE = "success_rate"
    QUALITY_SCORE = "quality_score"
    COST_PER_REQUEST = "cost_per_request"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"
    TOKEN_EFFICIENCY = "token_efficiency"

class AlertSeverity(str, Enum):
    """警报严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class TrendDirection(str, Enum):
    """趋势方向"""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    VOLATILE = "volatile"

@dataclass
class PerformanceMetric:
    """性能指标数据类"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    provider: str
    model_id: str
    task_type: Optional[str] = None
    user_tier: Optional[str] = None
    region: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceThreshold:
    """性能阈值配置"""
    metric_type: MetricType
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    direction: str  # "above" or "below"
    enabled: bool = True
    adaptive: bool = False  # 是否自适应调整

@dataclass
class PerformanceAlert:
    """性能警报"""
    id: str
    severity: AlertSeverity
    metric_type: MetricType
    provider: str
    model_id: str
    threshold_violated: float
    current_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    metric_type: MetricType
    provider: str
    model_id: str
    direction: TrendDirection
    trend_strength: float  # 0.0-1.0
    prediction_confidence: float  # 0.0-1.0
    projected_value: Optional[float] = None
    analysis_period_hours: int = 24
    data_points_count: int = 0

class ModelPerformanceMonitor:
    """模型性能监控器
    
    提供全面的模型性能监控功能，包括：
    - 实时性能指标收集
    - 动态阈值管理
    - 智能警报系统
    - 趋势分析和预测
    - 自动化能力评分更新
    - 性能报告生成
    """
    
    def __init__(
        self,
        model_capability_db: Optional[ModelCapabilityDB] = None,
        llm_client: Optional[LLMClient] = None
    ):
        """初始化性能监控器
        
        Args:
            model_capability_db: 模型能力数据库
            llm_client: LLM客户端
        """
        self.model_capability_db = model_capability_db or ModelCapabilityDB()
        self.llm_client = llm_client or LLMClient()
        
        # 性能数据存储 (内存缓存，生产环境应使用Redis或数据库)
        self.performance_data: Dict[str, List[PerformanceMetric]] = {}
        self.performance_thresholds: Dict[str, List[PerformanceThreshold]] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.trend_cache: Dict[str, TrendAnalysis] = {}
        
        # 监控配置
        self.monitoring_enabled = True
        self.collection_interval_seconds = 60
        self.data_retention_hours = 72  # 保留3天数据
        self.alert_cooldown_minutes = 15
        self.trend_analysis_interval_minutes = 30
        
        # 统计信息
        self.total_metrics_collected = 0
        self.total_alerts_generated = 0
        self.last_collection_time: Optional[datetime] = None
        self.last_trend_analysis_time: Optional[datetime] = None
        
        # 监控任务
        self._monitoring_task: Optional[asyncio.Task] = None
        self._trend_analysis_task: Optional[asyncio.Task] = None
        
        # 初始化默认阈值
        self._initialize_default_thresholds()
        
        logger.info("模型性能监控器初始化完成")
    
    def _initialize_default_thresholds(self):
        """初始化默认性能阈值"""
        default_thresholds = {
            "global": [
                # 延迟阈值 (毫秒)
                PerformanceThreshold(
                    metric_type=MetricType.LATENCY,
                    warning_threshold=3000,
                    error_threshold=5000,
                    critical_threshold=10000,
                    direction="above"
                ),
                # 成功率阈值 (百分比)
                PerformanceThreshold(
                    metric_type=MetricType.SUCCESS_RATE,
                    warning_threshold=95.0,
                    error_threshold=90.0,
                    critical_threshold=85.0,
                    direction="below"
                ),
                # 错误率阈值 (百分比)
                PerformanceThreshold(
                    metric_type=MetricType.ERROR_RATE,
                    warning_threshold=5.0,
                    error_threshold=10.0,
                    critical_threshold=15.0,
                    direction="above"
                ),
                # 质量评分阈值
                PerformanceThreshold(
                    metric_type=MetricType.QUALITY_SCORE,
                    warning_threshold=0.7,
                    error_threshold=0.6,
                    critical_threshold=0.5,
                    direction="below"
                ),
                # 可用性阈值 (百分比)
                PerformanceThreshold(
                    metric_type=MetricType.AVAILABILITY,
                    warning_threshold=99.0,
                    error_threshold=95.0,
                    critical_threshold=90.0,
                    direction="below"
                )
            ]
        }
        
        self.performance_thresholds = default_thresholds
        logger.info(f"已初始化 {len(default_thresholds['global'])} 个默认性能阈值")
    
    # ==================== 监控控制 ====================
    
    async def start_monitoring(self):
        """启动性能监控"""
        if self._monitoring_task and not self._monitoring_task.done():
            logger.warning("性能监控已在运行中")
            return
        
        self.monitoring_enabled = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._trend_analysis_task = asyncio.create_task(self._trend_analysis_loop())
        
        logger.info("性能监控已启动")
    
    async def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring_enabled = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self._trend_analysis_task:
            self._trend_analysis_task.cancel()
            try:
                await self._trend_analysis_task
            except asyncio.CancelledError:
                pass
        
        logger.info("性能监控已停止")
    
    async def _monitoring_loop(self):
        """监控主循环"""
        while self.monitoring_enabled:
            try:
                await self._collect_performance_metrics()
                await self._check_thresholds_and_alert()
                await self._cleanup_old_data()
                
                await asyncio.sleep(self.collection_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能监控循环错误: {e}")
                await asyncio.sleep(10)  # 错误时短暂休眠
    
    async def _trend_analysis_loop(self):
        """趋势分析循环"""
        while self.monitoring_enabled:
            try:
                await asyncio.sleep(self.trend_analysis_interval_minutes * 60)
                await self._analyze_performance_trends()
                await self._update_model_capabilities_from_trends()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"趋势分析循环错误: {e}")
                await asyncio.sleep(30)
    
    # ==================== 性能数据收集 ====================
    
    async def record_performance_metric(
        self,
        provider: str,
        model_id: str,
        metric_type: MetricType,
        value: float,
        task_type: Optional[str] = None,
        user_tier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录性能指标
        
        Args:
            provider: 提供商名称
            model_id: 模型ID
            metric_type: 指标类型
            value: 指标值
            task_type: 任务类型
            user_tier: 用户等级
            metadata: 额外元数据
        """
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(timezone.utc),
            provider=provider,
            model_id=model_id,
            task_type=task_type,
            user_tier=user_tier,
            metadata=metadata or {}
        )
        
        # 存储到内存缓存
        key = f"{provider}/{model_id}"
        if key not in self.performance_data:
            self.performance_data[key] = []
        
        self.performance_data[key].append(metric)
        self.total_metrics_collected += 1
        
        logger.debug(f"记录性能指标: {provider}/{model_id} - {metric_type.value}: {value}")
    
    async def record_llm_response_metrics(
        self,
        response: LLMResponse,
        task_type: Optional[str] = None,
        quality_score: Optional[float] = None
    ):
        """从LLM响应中记录性能指标
        
        Args:
            response: LLM响应对象
            task_type: 任务类型
            quality_score: 质量评分
        """
        provider = response.provider.value
        model = response.model
        
        # 记录延迟
        if response.response_time > 0:
            await self.record_performance_metric(
                provider=provider,
                model_id=model,
                metric_type=MetricType.LATENCY,
                value=response.response_time * 1000,  # 转换为毫秒
                task_type=task_type
            )
        
        # 记录成功率
        success_value = 1.0 if response.success else 0.0
        await self.record_performance_metric(
            provider=provider,
            model_id=model,
            metric_type=MetricType.SUCCESS_RATE,
            value=success_value * 100,  # 转换为百分比
            task_type=task_type
        )
        
        # 记录错误率
        error_value = 0.0 if response.success else 1.0
        await self.record_performance_metric(
            provider=provider,
            model_id=model,
            metric_type=MetricType.ERROR_RATE,
            value=error_value * 100,
            task_type=task_type
        )
        
        # 记录质量评分
        if quality_score is not None:
            await self.record_performance_metric(
                provider=provider,
                model_id=model,
                metric_type=MetricType.QUALITY_SCORE,
                value=quality_score,
                task_type=task_type
            )
        
        # 记录token效率
        if response.usage:
            total_tokens = response.usage.get('total_tokens', 0)
            if total_tokens > 0 and response.response_time > 0:
                tokens_per_second = total_tokens / response.response_time
                await self.record_performance_metric(
                    provider=provider,
                    model_id=model,
                    metric_type=MetricType.TOKEN_EFFICIENCY,
                    value=tokens_per_second,
                    task_type=task_type
                )
    
    async def _collect_performance_metrics(self):
        """收集系统性能指标"""
        self.last_collection_time = datetime.now(timezone.utc)
        
        # 从LLM客户端获取健康状态
        try:
            health_status = await self.llm_client.health_check()
            
            for provider_name, provider_info in health_status.get('providers', {}).items():
                if isinstance(provider_info, dict) and 'status' in provider_info:
                    availability = 100.0 if provider_info['status'] == 'healthy' else 0.0
                    
                    await self.record_performance_metric(
                        provider=provider_name,
                        model_id="default",  # 使用默认模型标识
                        metric_type=MetricType.AVAILABILITY,
                        value=availability
                    )
                elif isinstance(provider_info, str):
                    availability = 100.0 if provider_info == 'healthy' else 0.0
                    
                    await self.record_performance_metric(
                        provider=provider_name,
                        model_id="default",
                        metric_type=MetricType.AVAILABILITY,
                        value=availability
                    )
        except Exception as e:
            logger.error(f"收集健康状态指标失败: {e}")
        
        # 从数据库收集历史性能数据
        await self._collect_database_metrics()
    
    async def _collect_database_metrics(self):
        """从数据库收集历史性能指标"""
        try:
            # 获取所有模型的统计信息
            provider_stats = await self.model_capability_db.get_provider_statistics()
            
            for provider_name, stats in provider_stats.get('providers', {}).items():
                await self.record_performance_metric(
                    provider=provider_name,
                    model_id="aggregated",
                    metric_type=MetricType.LATENCY,
                    value=stats.get('avg_latency_ms', 0.0)
                )
                
                # 可用性指标基于可用模型比例
                if stats.get('model_count', 0) > 0:
                    availability_rate = (stats.get('available_count', 0) / stats.get('model_count', 1)) * 100
                    await self.record_performance_metric(
                        provider=provider_name,
                        model_id="aggregated",
                        metric_type=MetricType.AVAILABILITY,
                        value=availability_rate
                    )
        except Exception as e:
            logger.error(f"从数据库收集性能指标失败: {e}")
    
    # ==================== 阈值检查和警报 ====================
    
    async def _check_thresholds_and_alert(self):
        """检查阈值并生成警报"""
        current_time = datetime.now(timezone.utc)
        
        for model_key, metrics in self.performance_data.items():
            if not metrics:
                continue
            
            # 按指标类型分组最近的数据
            recent_metrics = self._get_recent_metrics(metrics, hours=1)
            if not recent_metrics:
                continue
            
            grouped_metrics = self._group_metrics_by_type(recent_metrics)
            
            for metric_type, metric_values in grouped_metrics.items():
                if not metric_values:
                    continue
                
                # 计算平均值
                avg_value = statistics.mean([m.value for m in metric_values])
                
                # 检查阈值
                await self._check_metric_thresholds(
                    model_key, metric_type, avg_value, current_time
                )
    
    async def _check_metric_thresholds(
        self,
        model_key: str,
        metric_type: MetricType,
        current_value: float,
        timestamp: datetime
    ):
        """检查特定指标的阈值"""
        provider, model_id = model_key.split('/', 1)
        
        # 获取适用的阈值
        thresholds = self._get_applicable_thresholds(provider, model_id, metric_type)
        if not thresholds:
            return
        
        for threshold in thresholds:
            if not threshold.enabled:
                continue
            
            severity = self._evaluate_threshold_violation(threshold, current_value)
            if severity:
                alert_id = f"{model_key}_{metric_type.value}_{severity.value}"
                
                # 检查是否已有活跃警报
                if alert_id in self.active_alerts:
                    existing_alert = self.active_alerts[alert_id]
                    # 检查冷却时间
                    if (timestamp - existing_alert.timestamp).seconds < self.alert_cooldown_minutes * 60:
                        continue
                
                # 生成新警报
                alert = await self._generate_alert(
                    severity=severity,
                    metric_type=metric_type,
                    provider=provider,
                    model_id=model_id,
                    threshold_violated=self._get_threshold_value(threshold, severity),
                    current_value=current_value,
                    timestamp=timestamp
                )
                
                self.active_alerts[alert_id] = alert
                self.total_alerts_generated += 1
                
                logger.warning(f"生成性能警报: {alert.message}")
    
    def _get_applicable_thresholds(
        self, 
        provider: str, 
        model_id: str, 
        metric_type: MetricType
    ) -> List[PerformanceThreshold]:
        """获取适用的阈值配置"""
        applicable_thresholds = []
        
        # 检查全局阈值
        global_thresholds = self.performance_thresholds.get("global", [])
        for threshold in global_thresholds:
            if threshold.metric_type == metric_type:
                applicable_thresholds.append(threshold)
        
        # 检查提供商特定阈值
        provider_thresholds = self.performance_thresholds.get(provider, [])
        for threshold in provider_thresholds:
            if threshold.metric_type == metric_type:
                applicable_thresholds.append(threshold)
        
        # 检查模型特定阈值
        model_key = f"{provider}/{model_id}"
        model_thresholds = self.performance_thresholds.get(model_key, [])
        for threshold in model_thresholds:
            if threshold.metric_type == metric_type:
                applicable_thresholds.append(threshold)
        
        return applicable_thresholds
    
    def _evaluate_threshold_violation(
        self, 
        threshold: PerformanceThreshold, 
        current_value: float
    ) -> Optional[AlertSeverity]:
        """评估阈值违反情况"""
        if threshold.direction == "above":
            if current_value >= threshold.critical_threshold:
                return AlertSeverity.CRITICAL
            elif current_value >= threshold.error_threshold:
                return AlertSeverity.ERROR
            elif current_value >= threshold.warning_threshold:
                return AlertSeverity.WARNING
        else:  # "below"
            if current_value <= threshold.critical_threshold:
                return AlertSeverity.CRITICAL
            elif current_value <= threshold.error_threshold:
                return AlertSeverity.ERROR
            elif current_value <= threshold.warning_threshold:
                return AlertSeverity.WARNING
        
        return None
    
    def _get_threshold_value(self, threshold: PerformanceThreshold, severity: AlertSeverity) -> float:
        """获取对应严重级别的阈值"""
        if severity == AlertSeverity.CRITICAL:
            return threshold.critical_threshold
        elif severity == AlertSeverity.ERROR:
            return threshold.error_threshold
        else:
            return threshold.warning_threshold
    
    async def _generate_alert(
        self,
        severity: AlertSeverity,
        metric_type: MetricType,
        provider: str,
        model_id: str,
        threshold_violated: float,
        current_value: float,
        timestamp: datetime
    ) -> PerformanceAlert:
        """生成性能警报"""
        alert_id = str(uuid.uuid4())
        
        message = self._format_alert_message(
            severity, metric_type, provider, model_id, 
            threshold_violated, current_value
        )
        
        alert = PerformanceAlert(
            id=alert_id,
            severity=severity,
            metric_type=metric_type,
            provider=provider,
            model_id=model_id,
            threshold_violated=threshold_violated,
            current_value=current_value,
            message=message,
            timestamp=timestamp
        )
        
        return alert
    
    def _format_alert_message(
        self,
        severity: AlertSeverity,
        metric_type: MetricType,
        provider: str,
        model_id: str,
        threshold: float,
        current_value: float
    ) -> str:
        """格式化警报消息"""
        metric_name = {
            MetricType.LATENCY: "延迟",
            MetricType.SUCCESS_RATE: "成功率",
            MetricType.ERROR_RATE: "错误率",
            MetricType.QUALITY_SCORE: "质量评分",
            MetricType.AVAILABILITY: "可用性"
        }.get(metric_type, metric_type.value)
        
        severity_name = {
            AlertSeverity.WARNING: "警告",
            AlertSeverity.ERROR: "错误",
            AlertSeverity.CRITICAL: "严重"
        }.get(severity, severity.value)
        
        unit = {
            MetricType.LATENCY: "ms",
            MetricType.SUCCESS_RATE: "%",
            MetricType.ERROR_RATE: "%",
            MetricType.AVAILABILITY: "%"
        }.get(metric_type, "")
        
        return (
            f"[{severity_name}] {provider}/{model_id} {metric_name}异常: "
            f"当前值 {current_value:.2f}{unit}, 阈值 {threshold:.2f}{unit}"
        )
    
    # ==================== 趋势分析 ====================
    
    async def _analyze_performance_trends(self):
        """分析性能趋势"""
        self.last_trend_analysis_time = datetime.now(timezone.utc)
        
        for model_key, metrics in self.performance_data.items():
            if not metrics:
                continue
            
            provider, model_id = model_key.split('/', 1)
            
            # 分析最近24小时的数据
            recent_metrics = self._get_recent_metrics(metrics, hours=24)
            if len(recent_metrics) < 10:  # 需要足够的数据点
                continue
            
            # 按指标类型分析趋势
            grouped_metrics = self._group_metrics_by_type(recent_metrics)
            
            for metric_type, metric_values in grouped_metrics.items():
                trend_analysis = self._calculate_trend(
                    provider, model_id, metric_type, metric_values
                )
                
                if trend_analysis:
                    cache_key = f"{model_key}_{metric_type.value}"
                    self.trend_cache[cache_key] = trend_analysis
    
    def _calculate_trend(
        self,
        provider: str,
        model_id: str,
        metric_type: MetricType,
        metrics: List[PerformanceMetric]
    ) -> Optional[TrendAnalysis]:
        """计算指标趋势"""
        if len(metrics) < 5:
            return None
        
        # 按时间排序
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        values = [m.value for m in sorted_metrics]
        
        # 简单的线性趋势计算
        n = len(values)
        x_values = list(range(n))
        
        # 计算线性回归斜率
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)
        
        numerator = sum((x_values[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return None
        
        slope = numerator / denominator
        
        # 判断趋势方向
        direction = TrendDirection.STABLE
        if abs(slope) > 0.1:  # 阈值可调整
            if slope > 0:
                direction = TrendDirection.IMPROVING if metric_type in [
                    MetricType.SUCCESS_RATE, MetricType.QUALITY_SCORE, 
                    MetricType.AVAILABILITY, MetricType.TOKEN_EFFICIENCY
                ] else TrendDirection.DEGRADING
            else:
                direction = TrendDirection.DEGRADING if metric_type in [
                    MetricType.SUCCESS_RATE, MetricType.QUALITY_SCORE, 
                    MetricType.AVAILABILITY, MetricType.TOKEN_EFFICIENCY
                ] else TrendDirection.IMPROVING
        
        # 计算趋势强度和变异性
        trend_strength = min(abs(slope), 1.0)
        value_variance = statistics.pvariance(values)
        
        # 判断是否波动较大
        if value_variance > statistics.mean(values) * 0.3:  # 30%的变异系数
            direction = TrendDirection.VOLATILE
        
        # 预测下一个值
        projected_value = values[-1] + slope
        
        return TrendAnalysis(
            metric_type=metric_type,
            provider=provider,
            model_id=model_id,
            direction=direction,
            trend_strength=trend_strength,
            prediction_confidence=max(0.0, min(1.0, 1.0 - value_variance / max(y_mean, 1.0))),
            projected_value=projected_value,
            analysis_period_hours=24,
            data_points_count=len(metrics)
        )
    
    async def _update_model_capabilities_from_trends(self):
        """基于趋势分析更新模型能力评分"""
        for trend_key, trend in self.trend_cache.items():
            if trend.direction in [TrendDirection.DEGRADING, TrendDirection.VOLATILE]:
                # 如果趋势下降或波动大，考虑降低能力评分
                await self._adjust_model_capability_score(trend, -0.05)
            elif trend.direction == TrendDirection.IMPROVING:
                # 如果趋势改善，考虑提升能力评分
                await self._adjust_model_capability_score(trend, +0.02)
    
    async def _adjust_model_capability_score(
        self, 
        trend: TrendAnalysis, 
        adjustment: float
    ):
        """调整模型能力评分"""
        try:
            # 获取现有模型记录
            existing_model = await self.model_capability_db.get_model_by_provider_id(
                trend.provider, trend.model_id
            )
            
            if not existing_model:
                return
            
            # 计算新的评分
            current_score = existing_model.capability_score
            new_score = max(0.0, min(1.0, current_score + adjustment))
            
            # 只有变化显著时才更新
            if abs(new_score - current_score) >= 0.01:
                update_data = ModelCapabilityUpdate(capability_score=new_score)
                
                await self.model_capability_db.update_model_capability(
                    existing_model.id, update_data
                )
                
                logger.info(f"基于趋势调整模型评分: {trend.provider}/{trend.model_id} "
                           f"{current_score:.3f} -> {new_score:.3f}")
                
        except Exception as e:
            logger.error(f"调整模型能力评分失败: {e}")
    
    # ==================== 数据管理 ====================
    
    def _get_recent_metrics(
        self, 
        metrics: List[PerformanceMetric], 
        hours: int = 24
    ) -> List[PerformanceMetric]:
        """获取最近指定小时内的指标"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [m for m in metrics if m.timestamp >= cutoff_time]
    
    def _group_metrics_by_type(
        self, 
        metrics: List[PerformanceMetric]
    ) -> Dict[MetricType, List[PerformanceMetric]]:
        """按指标类型分组"""
        groups = {}
        for metric in metrics:
            if metric.metric_type not in groups:
                groups[metric.metric_type] = []
            groups[metric.metric_type].append(metric)
        return groups
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.data_retention_hours)
        
        # 清理性能数据
        for model_key in list(self.performance_data.keys()):
            self.performance_data[model_key] = [
                m for m in self.performance_data[model_key] 
                if m.timestamp >= cutoff_time
            ]
            
            # 如果没有数据了，删除键
            if not self.performance_data[model_key]:
                del self.performance_data[model_key]
        
        # 清理已解决的警报
        resolved_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.resolved and alert.resolution_timestamp
            and (datetime.now(timezone.utc) - alert.resolution_timestamp).hours >= 24
        ]
        
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
    
    # ==================== 查询和报告 ====================
    
    def get_performance_summary(
        self, 
        provider: Optional[str] = None,
        model_id: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取性能摘要"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # 过滤数据
        relevant_data = {}
        for model_key, metrics in self.performance_data.items():
            model_provider, model_model_id = model_key.split('/', 1)
            
            if provider and model_provider != provider:
                continue
            if model_id and model_model_id != model_id:
                continue
            
            recent_metrics = [m for m in metrics if m.timestamp >= cutoff_time]
            if recent_metrics:
                relevant_data[model_key] = recent_metrics
        
        # 计算汇总统计
        summary = {
            'period_hours': hours,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'models_monitored': len(relevant_data),
            'total_metrics_collected': sum(len(metrics) for metrics in relevant_data.values()),
            'metric_summaries': {},
            'active_alerts_count': len(self.active_alerts),
            'trend_analyses': len(self.trend_cache)
        }
        
        # 按指标类型统计
        all_metrics = []
        for metrics in relevant_data.values():
            all_metrics.extend(metrics)
        
        grouped_all = self._group_metrics_by_type(all_metrics)
        
        for metric_type, metrics in grouped_all.items():
            values = [m.value for m in metrics]
            if values:
                summary['metric_summaries'][metric_type.value] = {
                    'count': len(values),
                    'average': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1] if values else None
                }
        
        return summary
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[PerformanceAlert]:
        """获取活跃警报"""
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_trend_analysis(
        self, 
        provider: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> List[TrendAnalysis]:
        """获取趋势分析结果"""
        trends = list(self.trend_cache.values())
        
        if provider:
            trends = [t for t in trends if t.provider == provider]
        if model_id:
            trends = [t for t in trends if t.model_id == model_id]
        
        return trends
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """解决警报"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_timestamp = datetime.now(timezone.utc)
            
            logger.info(f"警报已解决: {alert.message}")
            return True
        
        return False
    
    def get_monitoring_stats(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        return {
            'monitoring_enabled': self.monitoring_enabled,
            'collection_interval_seconds': self.collection_interval_seconds,
            'data_retention_hours': self.data_retention_hours,
            'total_metrics_collected': self.total_metrics_collected,
            'total_alerts_generated': self.total_alerts_generated,
            'active_alerts_count': len(self.active_alerts),
            'models_being_monitored': len(self.performance_data),
            'trend_analyses_cached': len(self.trend_cache),
            'last_collection_time': (
                self.last_collection_time.isoformat() 
                if self.last_collection_time else None
            ),
            'last_trend_analysis_time': (
                self.last_trend_analysis_time.isoformat() 
                if self.last_trend_analysis_time else None
            )
        }
    
    async def generate_performance_report(
        self, 
        hours: int = 24,
        include_trends: bool = True
    ) -> Dict[str, Any]:
        """生成性能报告"""
        summary = self.get_performance_summary(hours=hours)
        alerts = self.get_active_alerts()
        trends = self.get_trend_analysis() if include_trends else []
        
        report = {
            'report_metadata': {
                'generated_at': datetime.now(timezone.utc).isoformat(),
                'period_hours': hours,
                'report_type': 'performance_summary'
            },
            'performance_summary': summary,
            'active_alerts': [asdict(alert) for alert in alerts],
            'alert_analysis': self._analyze_alert_patterns(alerts),
            'monitoring_stats': self.get_monitoring_stats()
        }
        
        if include_trends:
            report['trend_analysis'] = [asdict(trend) for trend in trends]
            report['trend_insights'] = self._generate_trend_insights(trends)
        
        return report
    
    def _analyze_alert_patterns(self, alerts: List[PerformanceAlert]) -> Dict[str, Any]:
        """分析警报模式"""
        if not alerts:
            return {}
        
        # 按严重级别统计
        severity_counts = {}
        for alert in alerts:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
        
        # 按提供商统计
        provider_counts = {}
        for alert in alerts:
            provider_counts[alert.provider] = provider_counts.get(alert.provider, 0) + 1
        
        # 按指标类型统计
        metric_counts = {}
        for alert in alerts:
            metric_counts[alert.metric_type.value] = metric_counts.get(alert.metric_type.value, 0) + 1
        
        return {
            'total_active_alerts': len(alerts),
            'alerts_by_severity': severity_counts,
            'alerts_by_provider': provider_counts,
            'alerts_by_metric': metric_counts,
            'most_problematic_provider': max(provider_counts.items(), key=lambda x: x[1])[0] if provider_counts else None,
            'most_common_issue': max(metric_counts.items(), key=lambda x: x[1])[0] if metric_counts else None
        }
    
    def _generate_trend_insights(self, trends: List[TrendAnalysis]) -> List[str]:
        """生成趋势洞察"""
        insights = []
        
        if not trends:
            return ["无足够的趋势数据进行分析"]
        
        # 统计趋势方向
        direction_counts = {}
        for trend in trends:
            direction_counts[trend.direction.value] = direction_counts.get(trend.direction.value, 0) + 1
        
        total_trends = len(trends)
        
        for direction, count in direction_counts.items():
            percentage = (count / total_trends) * 100
            insights.append(f"{direction}趋势: {count}个指标 ({percentage:.1f}%)")
        
        # 识别需要关注的模型
        degrading_models = set()
        for trend in trends:
            if trend.direction == TrendDirection.DEGRADING:
                degrading_models.add(f"{trend.provider}/{trend.model_id}")
        
        if degrading_models:
            insights.append(f"需要关注的模型: {', '.join(degrading_models)}")
        
        return insights
    
    async def close(self):
        """关闭性能监控器，清理资源"""
        await self.stop_monitoring()
        
        if self.model_capability_db:
            self.model_capability_db.close()
        
        if self.llm_client:
            await self.llm_client.close()
        
        logger.info("模型性能监控器已关闭")

# ==================== 工具函数 ====================

def create_model_performance_monitor(
    model_capability_db: Optional[ModelCapabilityDB] = None,
    llm_client: Optional[LLMClient] = None
) -> ModelPerformanceMonitor:
    """创建模型性能监控器的便利函数"""
    return ModelPerformanceMonitor(model_capability_db, llm_client)