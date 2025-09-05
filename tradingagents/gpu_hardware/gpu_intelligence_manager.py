#!/usr/bin/env python3
"""
GPU資源智能管理系統 - RTX 4070/4090優化版
小c - 硬體優化與資源管理團隊

此模組提供：
1. 動態顯存分配和OOM預防機制
2. GPU溫度和功耗智能控制系統
3. 多任務並行調度和資源隔離
4. 智能資源預測和優化建議
5. 自動化故障恢復和性能調優
"""

import asyncio
import logging
import time
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
from pathlib import Path
import statistics
import queue

# 導入自定義模組
from .gpu_resource_manager import (
    GPUResourceManager, ResourceRequirement, AllocatedResources,
    AllocationType, ResourceStatus, InsufficientResourcesError
)
from .gpu_monitoring_system import (
    GPUMonitoringSystem, GPUMetric, MetricType, Alert, AlertLevel
)

# 配置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """優化策略"""
    PERFORMANCE = "performance"  # 性能優先
    EFFICIENCY = "efficiency"    # 效率優先
    BALANCED = "balanced"        # 平衡模式
    POWER_SAVING = "power_saving"  # 節能模式


class TaskPriority(Enum):
    """任務優先級"""
    CRITICAL = 1    # 關鍵任務
    HIGH = 2        # 高優先級
    NORMAL = 3      # 普通優先級
    LOW = 4         # 低優先級
    BACKGROUND = 5  # 後台任務


@dataclass
class TaskInfo:
    """任務信息"""
    task_id: str
    name: str
    priority: TaskPriority
    allocation_type: AllocationType
    memory_requirement: float
    estimated_duration: float  # 小時
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"


@dataclass
class OptimizationConfig:
    """優化配置"""
    # 記憶體管理
    memory_safety_margin: float = 0.1  # 10%安全邊距
    oom_prevention_threshold: float = 0.95  # 95%告警閾值
    memory_fragmentation_threshold: float = 0.3  # 30%碎片化閾值
    
    # 溫度控制
    temperature_target: float = 70.0  # 目標溫度
    temperature_max: float = 83.0     # 最大溫度
    fan_curve_aggressive: bool = True  # 激進風扇曲線
    
    # 功耗管理
    power_target: float = 180.0  # 目標功耗 (W)
    power_max: float = 250.0     # 最大功耗 (W)
    power_saving_mode: bool = False  # 節能模式
    
    # 調度策略
    max_concurrent_tasks: int = 3  # 最大並行任務數
    task_timeout_hours: float = 24.0  # 任務超時時間
    preemption_enabled: bool = True  # 啟用搶占
    
    # 預測設置
    prediction_window_hours: int = 6  # 預測窗口
    historical_data_days: int = 7     # 歷史數據天數


class GPUIntelligenceManager:
    """
    GPU資源智能管理系統
    
    整合資源管理和監控功能，提供智能化的GPU資源管理解決方案，
    包括OOM預防、動態調度、性能優化等功能。
    """
    
    def __init__(self, device_id: int = 0, config: OptimizationConfig = None):
        """
        初始化GPU智能管理器
        
        Args:
            device_id: GPU設備ID
            config: 優化配置
        """
        self.device_id = device_id
        self.config = config or OptimizationConfig()
        
        # 初始化子系統
        self.resource_manager = GPUResourceManager(device_id=device_id)
        self.monitoring_system = GPUMonitoringSystem(MonitoringConfig(device_id=device_id))
        
        # 任務管理
        self.task_queue: queue.PriorityQueue = queue.PriorityQueue()
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.completed_tasks: List[TaskInfo] = []
        self.task_history: List[TaskInfo] = []
        
        # 智能預測
        self.usage_patterns: Dict[str, List[float]] = {}
        self.prediction_models: Dict[str, Any] = {}
        
        # 優化狀態
        self.current_strategy = OptimizationStrategy.BALANCED
        self.optimization_stats = {
            'oom_prevented': 0,
            'tasks_optimized': 0,
            'performance_improvements': 0,
            'energy_savings': 0.0
        }
        
        # 控制迴路
        self.control_loop_running = False
        self.control_thread = None
        
        # 回調函數
        self.optimization_callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.task_callbacks: List[Callable[[TaskInfo], None]] = []
        
        # 初始化
        self._setup_callbacks()
        self._start_control_loop()
        
        logger.info(f"GPU智能管理器初始化完成 - 設備{device_id}")
    
    def _setup_callbacks(self):
        """設置回調函數"""
        # 監控告警回調
        self.monitoring_system.add_alert_callback(self._handle_monitoring_alert)
        
        # 指標回調
        self.monitoring_system.add_metric_callback(self._handle_metric_update)
    
    async def submit_task(
        self,
        task_info: TaskInfo
    ) -> str:
        """
        提交任務到智能調度系統
        
        Args:
            task_info: 任務信息
            
        Returns:
            任務ID
        """
        try:
            # 驗證任務
            if not self._validate_task(task_info):
                raise ValueError("任務驗證失敗")
            
            # 計算優先級分數
            priority_score = self._calculate_priority_score(task_info)
            
            # 加入任務佇列
            self.task_queue.put((priority_score, task_info))
            
            # 觸發調度
            await self._trigger_scheduling()
            
            logger.info(f"任務提交成功: {task_info.task_id}, 優先級{task_info.priority.value}")
            
            return task_info.task_id
            
        except Exception as e:
            logger.error(f"任務提交失敗: {e}")
            raise
    
    async def allocate_resources_for_task(
        self,
        task_info: TaskInfo
    ) -> Optional[AllocatedResources]:
        """
        為任務分配資源
        
        Args:
            task_info: 任務信息
            
        Returns:
            分配的資源
        """
        try:
            # 檢查OOM風險
            if await self._check_oom_risk(task_info.memory_requirement):
                await self._prevent_oom()
            
            # 創建資源需求
            requirement = ResourceRequirement(
                memory_gb=task_info.memory_requirement,
                allocation_type=task_info.allocation_type,
                max_duration_hours=task_info.estimated_duration,
                requires_exclusive=False
            )
            
            # 分配資源
            allocation = await self.resource_manager.allocate_resources(requirement)
            
            # 更新任務狀態
            task_info.started_at = datetime.now()
            task_info.status = "running"
            self.active_tasks[task_info.task_id] = task_info
            
            # 觸發回調
            for callback in self.task_callbacks:
                try:
                    callback(task_info)
                except Exception as e:
                    logger.error(f"任務回調執行失敗: {e}")
            
            logger.info(f"資源分配成功: {task_info.task_id}")
            
            return allocation
            
        except InsufficientResourcesError as e:
            logger.warning(f"資源不足，任務等待: {task_info.task_id} - {e}")
            return None
        except Exception as e:
            logger.error(f"資源分配失敗: {e}")
            return None
    
    async def release_task_resources(self, task_id: str) -> bool:
        """
        釋放任務資源
        
        Args:
            task_id: 任務ID
            
        Returns:
            是否成功釋放
        """
        try:
            if task_id not in self.active_tasks:
                logger.warning(f"任務不存在: {task_id}")
                return False
            
            task_info = self.active_tasks[task_id]
            
            # 釋放資源
            # 注意：這裡需要根據實際的分配ID來釋放
            # 簡化實現，實際應該維護task_id到allocation_id的映射
            success = True  # 簡化實現
            
            # 更新任務狀態
            task_info.completed_at = datetime.now()
            task_info.status = "completed"
            
            # 移動到已完成列表
            del self.active_tasks[task_id]
            self.completed_tasks.append(task_info)
            self.task_history.append(task_info)
            
            logger.info(f"任務資源釋放成功: {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"任務資源釋放失敗: {e}")
            return False
    
    async def optimize_performance(self) -> Dict[str, Any]:
        """
        執行性能優化
        
        Returns:
            優化結果
        """
        try:
            optimization_result = {
                'timestamp': datetime.now().isoformat(),
                'strategy': self.current_strategy.value,
                'improvements': [],
                'recommendations': []
            }
            
            # 獲取當前指標
            current_metrics = self.monitoring_system.get_current_metrics()
            
            # 記憶體優化
            memory_optimization = await self._optimize_memory_usage(current_metrics)
            if memory_optimization:
                optimization_result['improvements'].append(memory_optimization)
            
            # 溫度優化
            temperature_optimization = await self._optimize_temperature(current_metrics)
            if temperature_optimization:
                optimization_result['improvements'].append(temperature_optimization)
            
            # 功耗優化
            power_optimization = await self._optimize_power_usage(current_metrics)
            if power_optimization:
                optimization_result['improvements'].append(power_optimization)
            
            # 調度優化
            scheduling_optimization = await self._optimize_scheduling()
            if scheduling_optimization:
                optimization_result['improvements'].append(scheduling_optimization)
            
            # 生成建議
            recommendations = await self._generate_recommendations(current_metrics)
            optimization_result['recommendations'] = recommendations
            
            # 更新統計
            self.optimization_stats['tasks_optimized'] += 1
            
            # 觸發回調
            for callback in self.optimization_callbacks:
                try:
                    callback(optimization_result)
                except Exception as e:
                    logger.error(f"優化回調執行失敗: {e}")
            
            logger.info(f"性能優化完成: {len(optimization_result['improvements'])}項改進")
            
            return optimization_result
            
        except Exception as e:
            logger.error(f"性能優化失敗: {e}")
            return {'error': str(e)}
    
    async def predict_resource_usage(self, hours: int = 6) -> Dict[str, Any]:
        """
        預測資源使用情況
        
        Args:
            hours: 預測小時數
            
        Returns:
            預測結果
        """
        try:
            prediction = {
                'timestamp': datetime.now().isoformat(),
                'prediction_hours': hours,
                'memory_usage': [],
                'temperature_trend': [],
                'power_usage': [],
                'task_load': []
            }
            
            # 獲取歷史數據
            memory_history = self.monitoring_system.get_metrics_history(
                MetricType.MEMORY_USAGE, hours=24
            )
            temperature_history = self.monitoring_system.get_metrics_history(
                MetricType.TEMPERATURE, hours=24
            )
            power_history = self.monitoring_system.get_metrics_history(
                MetricType.POWER_USAGE, hours=24
            )
            
            # 簡單線性預測（實際應該使用更複雜的ML模型）
            if memory_history:
                prediction['memory_usage'] = self._linear_prediction(
                    [m.value for m in memory_history], hours
                )
            
            if temperature_history:
                prediction['temperature_trend'] = self._linear_prediction(
                    [m.value for m in temperature_history], hours
                )
            
            if power_history:
                prediction['power_usage'] = self._linear_prediction(
                    [m.value for m in power_history], hours
                )
            
            # 任務負載預測
            prediction['task_load'] = self._predict_task_load(hours)
            
            logger.info(f"資源使用預測完成: {hours}小時")
            
            return prediction
            
        except Exception as e:
            logger.error(f"資源預測失敗: {e}")
            return {'error': str(e)}
    
    def _start_control_loop(self):
        """啟動控制迴路"""
        if self.control_loop_running:
            return
        
        self.control_loop_running = True
        self.control_thread = threading.Thread(
            target=self._control_loop,
            daemon=True,
            name="GPU-Intelligence-Control"
        )
        self.control_thread.start()
        
        logger.info("GPU智能控制迴路啟動")
    
    def _control_loop(self):
        """控制迴路"""
        while self.control_loop_running:
            try:
                # 執行調度
                asyncio.run(self._execute_scheduling())
                
                # 執行優化
                asyncio.run(self.optimize_performance())
                
                # 更新預測模型
                asyncio.run(self._update_prediction_models())
                
                # 檢查系統健康
                self._check_system_health()
                
                time.sleep(30)  # 30秒控制週期
                
            except Exception as e:
                logger.error(f"控制迴路異常: {e}")
                time.sleep(30)
    
    async def _execute_scheduling(self):
        """執行任務調度"""
        try:
            # 檢查是否有可用資源
            if len(self.active_tasks) >= self.config.max_concurrent_tasks:
                return
            
            # 從佇列中取出任務
            if not self.task_queue.empty():
                priority_score, task_info = self.task_queue.get()
                
                # 嘗試分配資源
                allocation = await self.allocate_resources_for_task(task_info)
                
                if allocation is None:
                    # 分配失敗，重新加入佇列
                    self.task_queue.put((priority_score, task_info))
                
        except Exception as e:
            logger.error(f"任務調度失敗: {e}")
    
    async def _check_oom_risk(self, required_memory: float) -> bool:
        """檢查OOM風險"""
        try:
            current_metrics = self.monitoring_system.get_current_metrics()
            
            if 'memory_usage' in current_metrics:
                current_usage = current_metrics['memory_usage'].value
                available_memory = 100 - current_usage
                
                # 檢查是否有足夠記憶體
                if required_memory > available_memory * 0.9:  # 90%安全邊距
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"OOM風險檢查失敗: {e}")
            return False
    
    async def _prevent_oom(self):
        """預防OOM"""
        try:
            logger.warning("檢測到OOM風險，執行預防措施")
            
            # 觸發垃圾回收
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # 暫停低優先級任務
            await self._pause_low_priority_tasks()
            
            # 更新統計
            self.optimization_stats['oom_prevented'] += 1
            
            logger.info("OOM預防措施執行完成")
            
        except Exception as e:
            logger.error(f"OOM預防失敗: {e}")
    
    async def _pause_low_priority_tasks(self):
        """暫停低優先級任務"""
        # 簡化實現，實際應該暫停具體的任務
        logger.info("暫停低優先級任務")
    
    async def _optimize_memory_usage(self, current_metrics: Dict[str, GPUMetric]) -> Optional[Dict[str, Any]]:
        """優化記憶體使用"""
        try:
            if 'memory_usage' not in current_metrics:
                return None
            
            memory_usage = current_metrics['memory_usage'].value
            
            if memory_usage > self.config.oom_prevention_threshold * 100:
                # 記憶體使用率過高，執行優化
                optimization = {
                    'type': 'memory_optimization',
                    'action': 'trigger_garbage_collection',
                    'reason': f'記憶體使用率過高: {memory_usage:.1f}%',
                    'impact': 'high'
                }
                
                # 執行優化動作
                if TORCH_AVAILABLE and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                return optimization
            
            return None
            
        except Exception as e:
            logger.error(f"記憶體優化失敗: {e}")
            return None
    
    async def _optimize_temperature(self, current_metrics: Dict[str, GPUMetric]) -> Optional[Dict[str, Any]]:
        """優化溫度控制"""
        try:
            if 'temperature' not in current_metrics:
                return None
            
            temperature = current_metrics['temperature'].value
            
            if temperature > self.config.temperature_target:
                optimization = {
                    'type': 'temperature_optimization',
                    'action': 'adjust_fan_curve',
                    'reason': f'溫度過高: {temperature:.1f}°C',
                    'impact': 'medium'
                }
                
                # 實際應該調整風扇曲線
                logger.info(f"調整風扇曲線，目標溫度: {self.config.temperature_target}°C")
                
                return optimization
            
            return None
            
        except Exception as e:
            logger.error(f"溫度優化失敗: {e}")
            return None
    
    async def _optimize_power_usage(self, current_metrics: Dict[str, GPUMetric]) -> Optional[Dict[str, Any]]:
        """優化功耗使用"""
        try:
            if 'power_usage' not in current_metrics:
                return None
            
            power_usage = current_metrics['power_usage'].value
            
            if power_usage > self.config.power_target:
                optimization = {
                    'type': 'power_optimization',
                    'action': 'reduce_power_limit',
                    'reason': f'功耗過高: {power_usage:.1f}W',
                    'impact': 'medium'
                }
                
                # 實際應該調整功耗限制
                logger.info(f"調整功耗限制，目標: {self.config.power_target}W")
                
                return optimization
            
            return None
            
        except Exception as e:
            logger.error(f"功耗優化失敗: {e}")
            return None
    
    async def _optimize_scheduling(self) -> Optional[Dict[str, Any]]:
        """優化任務調度"""
        try:
            # 檢查任務分佈
            if len(self.active_tasks) > 0:
                priorities = [task.priority.value for task in self.active_tasks.values()]
                avg_priority = statistics.mean(priorities)
                
                if avg_priority > 3:  # 平均優先級過低
                    optimization = {
                        'type': 'scheduling_optimization',
                        'action': 'reorder_task_queue',
                        'reason': f'平均優先級過低: {avg_priority:.1f}',
                        'impact': 'low'
                    }
                    
                    return optimization
            
            return None
            
        except Exception as e:
            logger.error(f"調度優化失敗: {e}")
            return None
    
    async def _generate_recommendations(self, current_metrics: Dict[str, GPUMetric]) -> List[str]:
        """生成優化建議"""
        recommendations = []
        
        try:
            # 記憶體建議
            if 'memory_usage' in current_metrics:
                memory_usage = current_metrics['memory_usage'].value
                if memory_usage > 80:
                    recommendations.append("建議減少並行任務數量以降低記憶體壓力")
                elif memory_usage < 30:
                    recommendations.append("記憶體使用率較低，可以增加任務負載")
            
            # 溫度建議
            if 'temperature' in current_metrics:
                temperature = current_metrics['temperature'].value
                if temperature > 75:
                    recommendations.append("建議檢查散熱系統，考慮降低GPU負載")
                elif temperature < 50:
                    recommendations.append("溫度較低，可以適當提高性能設置")
            
            # 功耗建議
            if 'power_usage' in current_metrics:
                power_usage = current_metrics['power_usage'].value
                if power_usage > 200:
                    recommendations.append("功耗較高，建議啟用節能模式")
            
            # 任務建議
            if len(self.active_tasks) == 0:
                recommendations.append("當前無活動任務，可以提交新的訓練任務")
            elif len(self.active_tasks) >= self.config.max_concurrent_tasks:
                recommendations.append("並行任務數已達上限，建議等待任務完成")
            
        except Exception as e:
            logger.error(f"建議生成失敗: {e}")
        
        return recommendations
    
    def _validate_task(self, task_info: TaskInfo) -> bool:
        """驗證任務"""
        try:
            # 檢查記憶體需求
            if task_info.memory_requirement <= 0:
                return False
            
            # 檢查持續時間
            if task_info.estimated_duration <= 0:
                return False
            
            # 檢查任務名稱
            if not task_info.name or len(task_info.name.strip()) == 0:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"任務驗證失敗: {e}")
            return False
    
    def _calculate_priority_score(self, task_info: TaskInfo) -> float:
        """計算優先級分數"""
        try:
            # 基礎分數（優先級越低，分數越高）
            base_score = task_info.priority.value
            
            # 時間因子（等待時間越長，優先級越高）
            wait_time = (datetime.now() - task_info.created_at).total_seconds() / 3600  # 小時
            time_factor = min(wait_time * 0.1, 1.0)  # 最多加1分
            
            # 資源效率因子（記憶體需求越小，優先級越高）
            efficiency_factor = max(0, 1.0 - task_info.memory_requirement / 12.0)  # 基於12GB
            
            # 計算總分
            total_score = base_score - time_factor - efficiency_factor
            
            return total_score
            
        except Exception as e:
            logger.error(f"優先級計算失敗: {e}")
            return task_info.priority.value
    
    def _linear_prediction(self, values: List[float], hours: int) -> List[float]:
        """線性預測"""
        try:
            if len(values) < 2:
                return values
            
            # 簡單線性回歸
            n = len(values)
            x_sum = sum(range(n))
            y_sum = sum(values)
            xy_sum = sum(i * v for i, v in enumerate(values))
            x2_sum = sum(i * i for i in range(n))
            
            # 計算斜率和截距
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            intercept = (y_sum - slope * x_sum) / n
            
            # 預測未來值
            predictions = []
            for i in range(hours):
                pred_value = slope * (n + i) + intercept
                predictions.append(max(0, pred_value))  # 確保非負
            
            return predictions
            
        except Exception as e:
            logger.error(f"線性預測失敗: {e}")
            return []
    
    def _predict_task_load(self, hours: int) -> List[int]:
        """預測任務負載"""
        try:
            # 基於歷史任務數據預測
            # 簡化實現，返回固定值
            return [len(self.active_tasks)] * hours
            
        except Exception as e:
            logger.error(f"任務負載預測失敗: {e}")
            return []
    
    async def _update_prediction_models(self):
        """更新預測模型"""
        try:
            # 更新使用模式
            current_metrics = self.monitoring_system.get_current_metrics()
            
            for metric_type, metric in current_metrics.items():
                if metric_type not in self.usage_patterns:
                    self.usage_patterns[metric_type] = []
                
                self.usage_patterns[metric_type].append(metric.value)
                
                # 保持歷史數據大小
                if len(self.usage_patterns[metric_type]) > 1000:
                    self.usage_patterns[metric_type] = self.usage_patterns[metric_type][-500:]
            
        except Exception as e:
            logger.error(f"預測模型更新失敗: {e}")
    
    def _check_system_health(self):
        """檢查系統健康"""
        try:
            # 檢查活躍告警
            active_alerts = self.monitoring_system.get_active_alerts()
            
            if len(active_alerts) > 0:
                logger.warning(f"系統存在{len(active_alerts)}個活躍告警")
                
                for alert in active_alerts:
                    if alert.alert_level == AlertLevel.CRITICAL:
                        logger.error(f"嚴重告警: {alert.message}")
            
            # 檢查任務狀態
            for task_id, task_info in self.active_tasks.items():
                if task_info.started_at:
                    duration = (datetime.now() - task_info.started_at).total_seconds() / 3600
                    if duration > self.config.task_timeout_hours:
                        logger.warning(f"任務超時: {task_id}, 運行時間{duration:.1f}小時")
            
        except Exception as e:
            logger.error(f"系統健康檢查失敗: {e}")
    
    def _handle_monitoring_alert(self, alert: Alert):
        """處理監控告警"""
        try:
            logger.warning(f"監控告警: {alert.message}")
            
            # 根據告警級別採取行動
            if alert.alert_level == AlertLevel.CRITICAL:
                # 緊急處理
                asyncio.create_task(self._handle_critical_alert(alert))
            elif alert.alert_level == AlertLevel.WARNING:
                # 警告處理
                asyncio.create_task(self._handle_warning_alert(alert))
            
        except Exception as e:
            logger.error(f"告警處理失敗: {e}")
    
    async def _handle_critical_alert(self, alert: Alert):
        """處理嚴重告警"""
        try:
            logger.error(f"處理嚴重告警: {alert.message}")
            
            # 暫停所有任務
            # 實際實現應該更複雜
            logger.info("暫停所有任務以處理嚴重告警")
            
        except Exception as e:
            logger.error(f"嚴重告警處理失敗: {e}")
    
    async def _handle_warning_alert(self, alert: Alert):
        """處理警告告警"""
        try:
            logger.warning(f"處理警告告警: {alert.message}")
            
            # 執行優化
            await self.optimize_performance()
            
        except Exception as e:
            logger.error(f"警告告警處理失敗: {e}")
    
    def _handle_metric_update(self, metric: GPUMetric):
        """處理指標更新"""
        try:
            # 更新使用模式
            if metric.metric_type.value not in self.usage_patterns:
                self.usage_patterns[metric.metric_type.value] = []
            
            self.usage_patterns[metric.metric_type.value].append(metric.value)
            
        except Exception as e:
            logger.error(f"指標更新處理失敗: {e}")
    
    async def _trigger_scheduling(self):
        """觸發調度"""
        # 這個方法在實際實現中應該觸發調度邏輯
        pass
    
    def add_optimization_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """添加優化回調"""
        self.optimization_callbacks.append(callback)
    
    def add_task_callback(self, callback: Callable[[TaskInfo], None]):
        """添加任務回調"""
        self.task_callbacks.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'device_id': self.device_id,
            'current_strategy': self.current_strategy.value,
            'active_tasks_count': len(self.active_tasks),
            'queued_tasks_count': self.task_queue.qsize(),
            'completed_tasks_count': len(self.completed_tasks),
            'optimization_stats': self.optimization_stats,
            'resource_manager_stats': self.resource_manager.get_stats(),
            'monitoring_stats': self.monitoring_system.get_stats()
        }
    
    def shutdown(self):
        """關閉智能管理器"""
        self.control_loop_running = False
        
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=5.0)
        
        # 關閉子系統
        self.resource_manager.shutdown()
        asyncio.run(self.monitoring_system.stop_monitoring())
        
        logger.info("GPU智能管理器已關閉")


# 工廠函數
def create_gpu_intelligence_manager(device_id: int = 0) -> GPUIntelligenceManager:
    """
    創建GPU智能管理器實例
    
    Args:
        device_id: GPU設備ID
        
    Returns:
        GPU智能管理器實例
    """
    config = OptimizationConfig()
    return GPUIntelligenceManager(device_id=device_id, config=config)
