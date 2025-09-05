#!/usr/bin/env python3
"""
Capability Update Manager
動態能力更新管理器 - GPT-OSS整合任務1.2.3
統一協調所有動態能力更新組件
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..database.model_capability_db import ModelCapabilityDB
from ..monitoring.performance_monitor import PerformanceMonitor
from .model_version_control import ModelVersionControl, VersionUpdateRequest, ChangeType
from .dynamic_capability_updater import DynamicCapabilityUpdater, UpdateRule, UpdateTrigger, UpdateStrategy
from .capability_alert_system import CapabilityAlertSystem, AlertSeverity, AlertCondition, AlertType
from .ab_testing_system import ABTestingSystem, ExperimentType, TrafficSplitConfig, TrafficSplitStrategy
from .capability_dashboard import CapabilityDashboard, ReportType

logger = logging.getLogger(__name__)

class CapabilityUpdateManager:
    """
    動態能力更新管理器
    
    統一管理和協調以下組件：
    1. 模型版本控制系統
    2. 動態能力更新器
    3. 能力變化告警系統
    4. A/B測試和灰度更新系統
    5. 監控儀表板和報告系統
    
    提供統一的API接口和生命週期管理
    """
    
    def __init__(
        self,
        model_db: Optional[ModelCapabilityDB] = None,
        performance_monitor: Optional[PerformanceMonitor] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化能力更新管理器
        
        Args:
            model_db: 模型能力數據庫
            performance_monitor: 性能監控器
            config: 配置參數
        """
        self.model_db = model_db or ModelCapabilityDB()
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        self.config = config or {}
        
        self.logger = logger
        
        # 初始化各個組件
        self.version_control = ModelVersionControl(self.model_db)
        
        self.capability_updater = DynamicCapabilityUpdater(
            model_db=self.model_db,
            performance_monitor=self.performance_monitor,
            version_control=self.version_control
        )
        
        self.alert_system = CapabilityAlertSystem(
            model_db=self.model_db,
            performance_monitor=self.performance_monitor,
            version_control=self.version_control
        )
        
        self.ab_testing_system = ABTestingSystem(
            model_db=self.model_db,
            performance_monitor=self.performance_monitor,
            version_control=self.version_control
        )
        
        self.dashboard = CapabilityDashboard(
            model_db=self.model_db,
            performance_monitor=self.performance_monitor,
            version_control=self.version_control,
            capability_updater=self.capability_updater,
            alert_system=self.alert_system,
            ab_testing_system=self.ab_testing_system
        )
        
        # 運行狀態
        self._initialized = False
        self._running = False
        
        # 統計信息
        self.manager_stats = {
            'initialization_time': None,
            'uptime_seconds': 0,
            'total_updates': 0,
            'total_experiments': 0,
            'total_alerts': 0
        }
    
    async def initialize(self) -> bool:
        """
        初始化所有組件
        
        Returns:
            是否初始化成功
        """
        try:
            start_time = datetime.now(timezone.utc)
            self.logger.info("🚀 Initializing Capability Update Manager...")
            
            # 按順序初始化各組件
            initialization_steps = [
                ("Version Control", self._initialize_version_control),
                ("Alert System", self._initialize_alert_system),
                ("Capability Updater", self._initialize_capability_updater),
                ("A/B Testing System", self._initialize_ab_testing_system),
                ("Dashboard", self._initialize_dashboard)
            ]
            
            for step_name, init_func in initialization_steps:
                try:
                    self.logger.info(f"🔧 Initializing {step_name}...")
                    success = await init_func()
                    if not success:
                        raise Exception(f"{step_name} initialization failed")
                    self.logger.info(f"✅ {step_name} initialized successfully")
                except Exception as e:
                    self.logger.error(f"❌ Failed to initialize {step_name}: {e}")
                    return False
            
            # 設置組件間的集成
            await self._setup_component_integration()
            
            # 記錄初始化時間
            initialization_time = datetime.now(timezone.utc) - start_time
            self.manager_stats['initialization_time'] = initialization_time.total_seconds()
            
            self._initialized = True
            self.logger.info(f"✅ Capability Update Manager initialized successfully in {initialization_time.total_seconds():.2f}s")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Capability Update Manager: {e}")
            return False
    
    async def _initialize_version_control(self) -> bool:
        """初始化版本控制系統"""
        try:
            # 版本控制系統在實例化時已初始化
            return True
        except Exception as e:
            self.logger.error(f"❌ Version control initialization failed: {e}")
            return False
    
    async def _initialize_alert_system(self) -> bool:
        """初始化告警系統"""
        try:
            # 可以在這裡添加自定義告警通道
            webhook_url = self.config.get('alert_webhook_url')
            if webhook_url:
                from .capability_alert_system import WebhookAlertChannel
                webhook_channel = WebhookAlertChannel(webhook_url)
                self.alert_system.add_alert_channel(webhook_channel)
                self.logger.info("Added webhook alert channel")
            
            # 添加自定義告警條件
            custom_conditions = self.config.get('custom_alert_conditions', [])
            for condition_config in custom_conditions:
                condition = AlertCondition(
                    condition_id=condition_config['condition_id'],
                    alert_type=AlertType(condition_config['alert_type']),
                    severity=AlertSeverity(condition_config['severity']),
                    conditions=condition_config['conditions'],
                    enabled=condition_config.get('enabled', True)
                )
                self.alert_system.add_alert_condition(condition)
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Alert system initialization failed: {e}")
            return False
    
    async def _initialize_capability_updater(self) -> bool:
        """初始化能力更新器"""
        try:
            # 添加自定義更新規則
            custom_rules = self.config.get('custom_update_rules', [])
            for rule_config in custom_rules:
                rule = UpdateRule(
                    rule_id=rule_config['rule_id'],
                    trigger_type=UpdateTrigger(rule_config['trigger_type']),
                    conditions=rule_config['conditions'],
                    strategy=UpdateStrategy(rule_config['strategy']),
                    enabled=rule_config.get('enabled', True),
                    priority=rule_config.get('priority', 2),
                    cooldown_minutes=rule_config.get('cooldown_minutes', 60)
                )
                self.capability_updater.add_update_rule(rule)
            
            return True
        except Exception as e:
            self.logger.error(f"❌ Capability updater initialization failed: {e}")
            return False
    
    async def _initialize_ab_testing_system(self) -> bool:
        """初始化A/B測試系統"""
        try:
            # A/B測試系統在實例化時已初始化
            return True
        except Exception as e:
            self.logger.error(f"❌ A/B testing system initialization failed: {e}")
            return False
    
    async def _initialize_dashboard(self) -> bool:
        """初始化儀表板"""
        try:
            # 儀表板在實例化時已初始化
            return True
        except Exception as e:
            self.logger.error(f"❌ Dashboard initialization failed: {e}")
            return False
    
    async def _setup_component_integration(self):
        """設置組件間集成"""
        try:
            # 設置告警系統回調到動態更新器
            self.alert_system.add_alert_channel(self.capability_updater)
            
            # 設置性能監控回調到告警系統
            if hasattr(self.performance_monitor, 'add_alert_callback'):
                self.performance_monitor.add_alert_callback(
                    self.alert_system._handle_performance_alert
                )
            
            self.logger.info("✅ Component integration setup completed")
            
        except Exception as e:
            self.logger.error(f"❌ Component integration setup failed: {e}")
            raise
    
    async def start(self) -> bool:
        """
        啟動所有組件
        
        Returns:
            是否啟動成功
        """
        if not self._initialized:
            self.logger.error("❌ Manager not initialized. Call initialize() first.")
            return False
        
        if self._running:
            self.logger.warning("⚠️ Manager is already running")
            return True
        
        try:
            self.logger.info("🚀 Starting Capability Update Manager components...")
            
            # 按順序啟動組件
            startup_components = [
                ("Performance Monitor", self.performance_monitor.start),
                ("Alert System", self.alert_system.start),
                ("Capability Updater", self.capability_updater.start),
                ("A/B Testing System", self.ab_testing_system.start),
                ("Dashboard", self.dashboard.start)
            ]
            
            for component_name, start_func in startup_components:
                try:
                    self.logger.info(f"🔧 Starting {component_name}...")
                    await start_func()
                    self.logger.info(f"✅ {component_name} started successfully")
                except Exception as e:
                    self.logger.error(f"❌ Failed to start {component_name}: {e}")
                    # 嘗試停止已啟動的組件
                    await self._emergency_stop()
                    return False
            
            self._running = True
            self.logger.info("✅ All Capability Update Manager components started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Capability Update Manager: {e}")
            return False
    
    async def stop(self) -> bool:
        """
        停止所有組件
        
        Returns:
            是否停止成功
        """
        if not self._running:
            self.logger.info("ℹ️ Manager is not running")
            return True
        
        try:
            self.logger.info("🔄 Stopping Capability Update Manager components...")
            
            # 按逆序停止組件
            shutdown_components = [
                ("Dashboard", self.dashboard.stop),
                ("A/B Testing System", self.ab_testing_system.stop),
                ("Capability Updater", self.capability_updater.stop),
                ("Alert System", self.alert_system.stop),
                ("Performance Monitor", self.performance_monitor.stop)
            ]
            
            for component_name, stop_func in shutdown_components:
                try:
                    self.logger.info(f"🔧 Stopping {component_name}...")
                    await stop_func()
                    self.logger.info(f"✅ {component_name} stopped successfully")
                except Exception as e:
                    self.logger.error(f"❌ Failed to stop {component_name}: {e}")
            
            self._running = False
            self.logger.info("✅ All Capability Update Manager components stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to stop Capability Update Manager: {e}")
            return False
    
    async def _emergency_stop(self):
        """緊急停止所有已啟動的組件"""
        try:
            self.logger.warning("⚠️ Performing emergency stop...")
            
            # 嘗試停止所有組件，忽略錯誤
            components = [
                self.dashboard,
                self.ab_testing_system,
                self.capability_updater,
                self.alert_system,
                self.performance_monitor
            ]
            
            for component in components:
                try:
                    if hasattr(component, 'stop'):
                        await component.stop()
                except Exception:
                    pass  # 忽略錯誤
            
            self._running = False
            
        except Exception as e:
            self.logger.error(f"❌ Emergency stop failed: {e}")
    
    # ==================== 統一API接口 ====================
    
    async def update_model_capability(
        self,
        provider: str,
        model_id: str,
        updates: Dict[str, Any],
        change_type: ChangeType = ChangeType.PERFORMANCE_UPDATE,
        change_summary: str = "",
        created_by: str = "api"
    ) -> Dict[str, Any]:
        """
        更新模型能力（帶版本控制）
        
        Args:
            provider: 提供商
            model_id: 模型ID
            updates: 更新內容
            change_type: 變更類型
            change_summary: 變更摘要
            created_by: 創建者
            
        Returns:
            更新結果
        """
        if not self._running:
            return {'success': False, 'error': 'Manager not running'}
        
        try:
            update_request = VersionUpdateRequest(
                provider=provider,
                model_id=model_id,
                changes=updates,
                change_type=change_type,
                change_summary=change_summary,
                created_by=created_by
            )
            
            result = await self.version_control.update_model_capability_with_versioning(
                update_request
            )
            
            # 更新統計
            if result.get('success'):
                self.manager_stats['total_updates'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Failed to update model capability: {e}")
            return {'success': False, 'error': str(e)}
    
    async def create_ab_experiment(
        self,
        experiment_name: str,
        control_model: Dict[str, str],
        test_models: List[Dict[str, str]],
        traffic_split_percentage: float = 10.0,
        duration_hours: int = 24
    ) -> Dict[str, Any]:
        """
        創建A/B測試實驗
        
        Args:
            experiment_name: 實驗名稱
            control_model: 控制組模型 {'provider': '', 'model_id': ''}
            test_models: 測試組模型列表
            traffic_split_percentage: 測試組流量百分比
            duration_hours: 實驗持續時間
            
        Returns:
            實驗創建結果
        """
        if not self._running:
            return {'success': False, 'error': 'Manager not running'}
        
        try:
            traffic_split = TrafficSplitConfig(
                strategy=TrafficSplitStrategy.RANDOM,
                control_percentage=100.0 - traffic_split_percentage,
                variant_percentage=traffic_split_percentage
            )
            
            experiment_id = await self.ab_testing_system.create_experiment(
                experiment_name=experiment_name,
                experiment_type=ExperimentType.AB_TEST,
                description=f"A/B test comparing {len(test_models)} model variants",
                control_variant=control_model,
                test_variants=test_models,
                traffic_split=traffic_split,
                primary_metrics=['capability_score', 'latency'],
                planned_duration_hours=duration_hours
            )
            
            # 啟動實驗
            success = await self.ab_testing_system.start_experiment(experiment_id)
            
            if success:
                self.manager_stats['total_experiments'] += 1
            
            return {
                'success': success,
                'experiment_id': experiment_id,
                'message': f"Experiment {'started' if success else 'created but failed to start'}"
            }
            
        except Exception as e:
            self.logger.error(f"❌ Failed to create A/B experiment: {e}")
            return {'success': False, 'error': str(e)}
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        獲取系統健康狀態
        
        Returns:
            系統健康狀態
        """
        try:
            health = {
                'manager': {
                    'initialized': self._initialized,
                    'running': self._running,
                    'uptime_seconds': self.manager_stats['uptime_seconds']
                },
                'components': {}
            }
            
            if self._running:
                # 獲取各組件狀態
                health['components']['version_control'] = {
                    'status': 'healthy'  # 版本控制沒有運行狀態
                }
                
                health['components']['capability_updater'] = self.capability_updater.get_update_status()
                health['components']['alert_system'] = self.alert_system.get_alert_statistics()
                health['components']['ab_testing_system'] = self.ab_testing_system.get_system_statistics()
                health['components']['dashboard'] = self.dashboard.get_dashboard_status()
                
                # 計算整體健康分數
                health['overall_score'] = self._calculate_health_score(health['components'])
            
            return health
            
        except Exception as e:
            self.logger.error(f"❌ Failed to get system health: {e}")
            return {
                'manager': {'error': str(e)},
                'overall_score': 0
            }
    
    def _calculate_health_score(self, components: Dict[str, Any]) -> int:
        """計算整體健康分數 (0-100)"""
        try:
            scores = []
            
            # 能力更新器得分
            updater = components.get('capability_updater', {})
            if updater.get('running'):
                success_rate = 100  # 默認
                if updater.get('total_updates', 0) > 0:
                    success_rate = (updater.get('successful_updates', 0) / updater['total_updates']) * 100
                scores.append(min(100, success_rate))
            
            # 告警系統得分
            alerts = components.get('alert_system', {})
            if alerts.get('running'):
                critical_alerts = alerts.get('active_alerts', 0)
                alert_score = max(0, 100 - (critical_alerts * 20))  # 每個活躍告警扣20分
                scores.append(alert_score)
            
            # A/B測試系統得分
            ab_testing = components.get('ab_testing_system', {})
            if ab_testing.get('running'):
                scores.append(90)  # A/B測試系統正常運行得90分
            
            # 儀表板得分
            dashboard = components.get('dashboard', {})
            if dashboard.get('running'):
                scores.append(85)  # 儀表板正常運行得85分
            
            return int(sum(scores) / len(scores)) if scores else 0
            
        except Exception:
            return 0
    
    async def generate_system_report(
        self,
        report_type: ReportType = ReportType.DAILY_SUMMARY,
        time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """
        生成系統報告
        
        Args:
            report_type: 報告類型
            time_range_hours: 時間範圍（小時）
            
        Returns:
            系統報告
        """
        if not self._running:
            return {'error': 'Manager not running'}
        
        try:
            # 使用儀表板生成報告
            report = await self.dashboard.generate_report(
                report_type=report_type,
                time_range_hours=time_range_hours,
                include_details=True
            )
            
            # 添加管理器級別的信息
            report['manager_info'] = {
                'version': '1.2.3',
                'initialization_time': self.manager_stats['initialization_time'],
                'total_updates': self.manager_stats['total_updates'],
                'total_experiments': self.manager_stats['total_experiments'],
                'generated_at': datetime.now(timezone.utc).isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Failed to generate system report: {e}")
            return {'error': str(e)}
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """獲取管理器統計信息"""
        stats = self.manager_stats.copy()
        
        if self._running and self.manager_stats['initialization_time']:
            # 計算運行時間
            init_time = datetime.now(timezone.utc) - timedelta(
                seconds=self.manager_stats['initialization_time']
            )
            stats['uptime_seconds'] = (datetime.now(timezone.utc) - init_time).total_seconds()
        
        stats.update({
            'initialized': self._initialized,
            'running': self._running,
            'components_count': 5,
            'active_components': self._count_active_components()
        })
        
        return stats
    
    def _count_active_components(self) -> int:
        """計算活躍組件數量"""
        if not self._running:
            return 0
        
        active_count = 0
        
        # 檢查各組件狀態
        if hasattr(self.performance_monitor, '_running') and self.performance_monitor._running:
            active_count += 1
        if hasattr(self.alert_system, '_running') and self.alert_system._running:
            active_count += 1
        if hasattr(self.capability_updater, '_running') and self.capability_updater._running:
            active_count += 1
        if hasattr(self.ab_testing_system, '_running') and self.ab_testing_system._running:
            active_count += 1
        if hasattr(self.dashboard, '_running') and self.dashboard._running:
            active_count += 1
        
        return active_count
    
    # ==================== 上下文管理器支援 ====================
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        await self.initialize()
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        await self.stop()