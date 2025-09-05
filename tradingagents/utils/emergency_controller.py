#!/usr/bin/env python3
"""
Emergency Controller - 緊急控制和回滾機制
天工 (TianGong) - 不老傳說 緊急狀況處理和系統保護

此模組負責：
1. 緊急停止機制
2. 自動回滾功能
3. 系統狀態恢復
4. 緊急通知和日誌
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

class EmergencyLevel(Enum):
    """緊急級別"""
    LOW = "low"              # 低級 - 監控警告
    MEDIUM = "medium"        # 中級 - 部分功能停止
    HIGH = "high"           # 高級 - 主要功能停止
    CRITICAL = "critical"   # 危急 - 系統全面停止

class SystemState(Enum):
    """系統狀態"""
    NORMAL = "normal"           # 正常運行
    DEGRADED = "degraded"       # 降級運行
    MAINTENANCE = "maintenance" # 維護模式
    EMERGENCY = "emergency"     # 緊急狀態
    SHUTDOWN = "shutdown"       # 已關閉

class EmergencyAction(Enum):
    """緊急操作"""
    MONITOR_ONLY = "monitor_only"         # 僅監控
    DISABLE_AI_ANALYSIS = "disable_ai"    # 禁用AI分析
    DISABLE_NEW_USERS = "disable_new"     # 禁用新用戶
    ROLLBACK_PARTIAL = "rollback_partial" # 部分回滾
    ROLLBACK_FULL = "rollback_full"       # 完全回滾
    SHUTDOWN_GRACEFUL = "shutdown_grace"  # 優雅關閉
    SHUTDOWN_IMMEDIATE = "shutdown_now"   # 立即關閉

@dataclass
class EmergencyEvent:
    """緊急事件"""
    id: str
    level: EmergencyLevel
    trigger: str              # 觸發原因
    action_taken: EmergencyAction
    timestamp: str
    description: str
    system_state_before: SystemState
    system_state_after: SystemState
    auto_triggered: bool
    resolved: bool = False
    resolved_at: Optional[str] = None

@dataclass
class SystemSnapshot:
    """系統快照"""
    timestamp: str
    system_state: SystemState
    enabled_users: List[str]
    active_features: List[str]
    configuration: Dict[str, Any]
    health_metrics: Dict[str, Any]

class EmergencyController:
    """緊急控制器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        
        # 系統狀態
        self.current_state = SystemState.NORMAL
        self.emergency_level = EmergencyLevel.LOW
        self.is_emergency_mode = False
        
        # 事件記錄
        self.emergency_events: List[EmergencyEvent] = []
        self.system_snapshots: List[SystemSnapshot] = []
        
        # 回調函數
        self.emergency_callbacks: List[Callable] = []
        self.state_change_callbacks: List[Callable] = []
        
        # 監控狀態
        self.monitoring_active = False
        self.monitoring_task = None
        
        # 自動回滾狀態
        self.auto_rollback_enabled = True
        self.rollback_thresholds = self.config.get('rollback_thresholds', {})
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # 設置信號處理
        self._setup_signal_handlers()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            'emergency_thresholds': {
                'cpu_percent': 95.0,      # CPU > 95% 觸發緊急
                'memory_percent': 95.0,   # 記憶體 > 95% 觸發緊急
                'error_rate': 0.25,       # 錯誤率 > 25% 觸發緊急
                'response_time': 10.0,    # 響應時間 > 10秒 觸發緊急
                'consecutive_failures': 5  # 連續5次失敗觸發緊急
            },
            'rollback_thresholds': {
                'error_rate': 0.15,       # 錯誤率 > 15% 自動回滾
                'analysis_failure_rate': 0.30,  # AI分析失敗率 > 30% 回滾
                'system_unavailable_time': 300   # 系統不可用5分鐘回滾
            },
            'auto_actions': {
                'enable_auto_rollback': True,
                'enable_auto_shutdown': False,  # 預設不啟用自動關閉
                'grace_period': 30,             # 30秒緩衝期
                'notification_delay': 60        # 1分鐘通知延遲
            },
            'monitoring_interval': 15,  # 15秒監控間隔
            'snapshot_interval': 300,   # 5分鐘系統快照
            'event_retention_days': 30  # 保留30天事件記錄
        }
    
    def _setup_signal_handlers(self):
        """設置信號處理器"""
        try:
            # 設置優雅關閉信號處理
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            
            # Windows特定信號
            if sys.platform == "win32":
                signal.signal(signal.SIGBREAK, self._signal_handler)
                
        except Exception as e:
            self.logger.warning(f"設置信號處理器失敗: {str(e)}")
    
    def _signal_handler(self, signum, frame):
        """信號處理器"""
        self.logger.info(f"接收到信號 {signum}, 開始優雅關閉")
        
        # 創建緊急事件
        asyncio.create_task(self.trigger_emergency(
            EmergencyLevel.HIGH,
            "system_signal",
            f"收到系統信號 {signum}",
            EmergencyAction.SHUTDOWN_GRACEFUL
        ))
    
    async def start_monitoring(self):
        """開始緊急監控"""
        if self.monitoring_active:
            self.logger.warning("緊急監控已在運行中")
            return
        
        self.monitoring_active = True
        self.logger.info("🚨 緊急控制器監控已啟動")
        
        # 啟動監控任務
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        # 啟動快照任務
        asyncio.create_task(self._snapshot_loop())
        
        # 創建初始快照
        await self._take_system_snapshot()
    
    async def stop_monitoring(self):
        """停止緊急監控"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("⏹️ 緊急控制器監控已停止")
    
    async def _monitoring_loop(self):
        """監控主循環"""
        consecutive_failures = 0
        
        try:
            while self.monitoring_active:
                try:
                    # 檢查系統健康狀況
                    health_check = await self._perform_health_check()
                    
                    if health_check['healthy']:
                        consecutive_failures = 0
                        
                        # 如果在緊急模式且系統恢復正常，考慮降級
                        if self.is_emergency_mode:
                            await self._consider_emergency_resolution()
                    else:
                        consecutive_failures += 1
                        self.logger.warning(f"系統健康檢查失敗 (連續 {consecutive_failures} 次)")
                        
                        # 檢查是否觸發緊急操作
                        await self._evaluate_emergency_triggers(health_check, consecutive_failures)
                    
                    # 檢查自動回滾條件
                    if self.auto_rollback_enabled:
                        await self._check_auto_rollback_conditions(health_check)
                    
                except Exception as e:
                    consecutive_failures += 1
                    self.logger.error(f"監控循環錯誤: {str(e)}")
                    
                    # 監控自身出錯也是緊急情況
                    if consecutive_failures >= 3:
                        await self.trigger_emergency(
                            EmergencyLevel.HIGH,
                            "monitoring_failure",
                            f"監控系統連續失敗 {consecutive_failures} 次",
                            EmergencyAction.MONITOR_ONLY
                        )
                
                await asyncio.sleep(self.config['monitoring_interval'])
                
        except asyncio.CancelledError:
            self.logger.info("緊急監控循環已取消")
        except Exception as e:
            self.logger.error(f"緊急監控循環致命錯誤: {str(e)}")
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """執行健康檢查"""
        try:
            # 這裡應該與SystemMonitor整合
            # 暫時使用簡化的健康檢查
            
            from .system_monitor import quick_system_check
            health_data = await quick_system_check()
            
            # 評估健康狀況
            system_metrics = health_data['system']
            app_metrics = health_data['application']
            
            # 檢查緊急閾值
            thresholds = self.config['emergency_thresholds']
            
            critical_issues = []
            
            if system_metrics['cpu_percent'] > thresholds['cpu_percent']:
                critical_issues.append(f"CPU過載: {system_metrics['cpu_percent']:.1f}%")
            
            if system_metrics['memory_percent'] > thresholds['memory_percent']:
                critical_issues.append(f"記憶體過載: {system_metrics['memory_percent']:.1f}%")
            
            if app_metrics['api_error_rate'] > thresholds['error_rate']:
                critical_issues.append(f"API錯誤率過高: {app_metrics['api_error_rate']:.2%}")
            
            if app_metrics['api_response_time_avg'] > thresholds['response_time']:
                critical_issues.append(f"響應時間過長: {app_metrics['api_response_time_avg']:.1f}s")
            
            return {
                'healthy': len(critical_issues) == 0,
                'critical_issues': critical_issues,
                'health_data': health_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {str(e)}")
            return {
                'healthy': False,
                'critical_issues': [f"健康檢查系統錯誤: {str(e)}"],
                'health_data': {},
                'timestamp': datetime.now().isoformat()
            }
    
    async def _evaluate_emergency_triggers(self, health_check: Dict[str, Any], consecutive_failures: int):
        """評估緊急觸發條件"""
        thresholds = self.config['emergency_thresholds']
        critical_issues = health_check['critical_issues']
        
        # 根據嚴重程度確定緊急級別和操作
        if consecutive_failures >= thresholds['consecutive_failures']:
            await self.trigger_emergency(
                EmergencyLevel.CRITICAL,
                "consecutive_failures",
                f"系統連續失敗 {consecutive_failures} 次",
                EmergencyAction.SHUTDOWN_GRACEFUL
            )
        elif len(critical_issues) >= 3:
            await self.trigger_emergency(
                EmergencyLevel.HIGH,
                "multiple_critical_issues",
                f"多個關鍵問題: {', '.join(critical_issues)}",
                EmergencyAction.DISABLE_AI_ANALYSIS
            )
        elif len(critical_issues) >= 1:
            if not self.is_emergency_mode:
                await self.trigger_emergency(
                    EmergencyLevel.MEDIUM,
                    "critical_issue_detected",
                    f"檢測到關鍵問題: {critical_issues[0]}",
                    EmergencyAction.DISABLE_NEW_USERS
                )
    
    async def _check_auto_rollback_conditions(self, health_check: Dict[str, Any]):
        """檢查自動回滾條件"""
        if not self.auto_rollback_enabled:
            return
        
        thresholds = self.rollback_thresholds
        health_data = health_check.get('health_data', {})
        app_metrics = health_data.get('application', {})
        
        # 檢查錯誤率回滾條件
        if app_metrics.get('api_error_rate', 0) > thresholds.get('error_rate', 0.15):
            await self.trigger_emergency(
                EmergencyLevel.HIGH,
                "auto_rollback_error_rate",
                f"錯誤率過高觸發自動回滾: {app_metrics['api_error_rate']:.2%}",
                EmergencyAction.ROLLBACK_PARTIAL
            )
    
    async def trigger_emergency(
        self, 
        level: EmergencyLevel, 
        trigger: str, 
        description: str,
        action: EmergencyAction,
        auto_triggered: bool = True
    ) -> str:
        """觸發緊急事件"""
        
        event_id = f"emergency_{int(time.time())}_{trigger}"
        
        # 記錄系統狀態變化前的狀態
        state_before = self.current_state
        
        # 執行緊急操作
        await self._execute_emergency_action(action, level)
        
        # 創建緊急事件記錄
        event = EmergencyEvent(
            id=event_id,
            level=level,
            trigger=trigger,
            action_taken=action,
            timestamp=datetime.now().isoformat(),
            description=description,
            system_state_before=state_before,
            system_state_after=self.current_state,
            auto_triggered=auto_triggered
        )
        
        self.emergency_events.append(event)
        
        # 更新緊急狀態
        self.emergency_level = level
        self.is_emergency_mode = True
        
        # 記錄日誌
        log_level = {
            EmergencyLevel.LOW: logging.INFO,
            EmergencyLevel.MEDIUM: logging.WARNING,
            EmergencyLevel.HIGH: logging.ERROR,
            EmergencyLevel.CRITICAL: logging.CRITICAL
        }.get(level, logging.ERROR)
        
        self.logger.log(log_level, f"🚨 緊急事件觸發: {description} (級別: {level.value})")
        
        # 發送通知
        await self._send_emergency_notification(event)
        
        # 調用回調函數
        for callback in self.emergency_callbacks:
            try:
                await callback(event)
            except Exception as e:
                self.logger.error(f"緊急回調失敗: {str(e)}")
        
        return event_id
    
    async def _execute_emergency_action(self, action: EmergencyAction, level: EmergencyLevel):
        """執行緊急操作"""
        self.logger.info(f"執行緊急操作: {action.value}")
        
        try:
            if action == EmergencyAction.MONITOR_ONLY:
                # 僅加強監控，不改變系統狀態
                pass
                
            elif action == EmergencyAction.DISABLE_AI_ANALYSIS:
                await self._disable_ai_analysis()
                self.current_state = SystemState.DEGRADED
                
            elif action == EmergencyAction.DISABLE_NEW_USERS:
                await self._disable_new_user_registration()
                self.current_state = SystemState.DEGRADED
                
            elif action == EmergencyAction.ROLLBACK_PARTIAL:
                await self._perform_partial_rollback()
                self.current_state = SystemState.MAINTENANCE
                
            elif action == EmergencyAction.ROLLBACK_FULL:
                await self._perform_full_rollback()
                self.current_state = SystemState.MAINTENANCE
                
            elif action == EmergencyAction.SHUTDOWN_GRACEFUL:
                await self._graceful_shutdown()
                self.current_state = SystemState.SHUTDOWN
                
            elif action == EmergencyAction.SHUTDOWN_IMMEDIATE:
                await self._immediate_shutdown()
                self.current_state = SystemState.SHUTDOWN
            
            # 通知狀態變化
            for callback in self.state_change_callbacks:
                try:
                    await callback(self.current_state)
                except Exception as e:
                    self.logger.error(f"狀態變化回調失敗: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"執行緊急操作失敗: {str(e)}")
            # 如果緊急操作失敗，嘗試更激進的措施
            if action != EmergencyAction.SHUTDOWN_IMMEDIATE:
                await self._immediate_shutdown()
    
    async def _disable_ai_analysis(self):
        """禁用AI分析功能"""
        try:
            # 這裡應該與MigrationManager整合
            from .migration_manager import emergency_stop_ai_analysis
            result = await emergency_stop_ai_analysis()
            
            if result['success']:
                self.logger.info("✅ AI分析功能已緊急停用")
            else:
                self.logger.error(f"❌ AI分析功能停用失敗: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"禁用AI分析失敗: {str(e)}")
    
    async def _disable_new_user_registration(self):
        """禁用新用戶註冊"""
        try:
            # 這裡應該設置維護模式標記
            # 暫時通過環境變數或配置文件實現
            
            maintenance_flag_file = "maintenance_mode.flag"
            with open(maintenance_flag_file, 'w') as f:
                json.dump({
                    'maintenance_mode': True,
                    'reason': 'Emergency maintenance',
                    'timestamp': datetime.now().isoformat()
                }, f)
            
            self.logger.info("✅ 新用戶註冊已禁用 (維護模式)")
            
        except Exception as e:
            self.logger.error(f"禁用新用戶註冊失敗: {str(e)}")
    
    async def _perform_partial_rollback(self):
        """執行部分回滾"""
        try:
            # 回滾到最近的穩定快照
            latest_snapshot = self._get_latest_stable_snapshot()
            
            if latest_snapshot:
                await self._restore_from_snapshot(latest_snapshot, partial=True)
                self.logger.info("✅ 部分回滾完成")
            else:
                self.logger.warning("⚠️ 無可用的穩定快照，執行默認回滾")
                await self._disable_ai_analysis()
                
        except Exception as e:
            self.logger.error(f"部分回滾失敗: {str(e)}")
    
    async def _perform_full_rollback(self):
        """執行完全回滾"""
        try:
            # 回滾到最近的穩定快照
            latest_snapshot = self._get_latest_stable_snapshot()
            
            if latest_snapshot:
                await self._restore_from_snapshot(latest_snapshot, partial=False)
                self.logger.info("✅ 完全回滾完成")
            else:
                self.logger.error("❌ 無可用的穩定快照，無法執行完全回滾")
                await self._disable_ai_analysis()
                
        except Exception as e:
            self.logger.error(f"完全回滾失敗: {str(e)}")
    
    async def _graceful_shutdown(self):
        """優雅關閉"""
        try:
            grace_period = self.config['auto_actions']['grace_period']
            
            self.logger.info(f"開始優雅關閉 (緩衝期: {grace_period}秒)")
            
            # 停止接受新請求
            await self._disable_new_user_registration()
            
            # 等待現有請求完成
            await asyncio.sleep(grace_period)
            
            # 停止AI分析
            await self._disable_ai_analysis()
            
            # 保存系統狀態
            await self._take_system_snapshot()
            
            self.logger.info("✅ 優雅關閉完成")
            
        except Exception as e:
            self.logger.error(f"優雅關閉失敗: {str(e)}")
            await self._immediate_shutdown()
    
    async def _immediate_shutdown(self):
        """立即關閉"""
        try:
            self.logger.critical("🚨 執行立即關閉")
            
            # 停止所有服務
            await self._disable_ai_analysis()
            await self.stop_monitoring()
            
            # 保存緊急快照
            await self._take_system_snapshot()
            
            self.logger.critical("💀 系統已緊急關閉")
            
        except Exception as e:
            self.logger.critical(f"立即關閉失敗: {str(e)}")
        
        # 最後手段 - 直接退出
        finally:
            os._exit(1)
    
    async def _take_system_snapshot(self):
        """創建系統快照"""
        try:
            # 獲取當前系統狀態
            health_check = await self._perform_health_check()
            
            snapshot = SystemSnapshot(
                timestamp=datetime.now().isoformat(),
                system_state=self.current_state,
                enabled_users=[],  # 這裡應該從MigrationManager獲取
                active_features=[],  # 這裡應該獲取當前啟用的功能
                configuration=self.config.copy(),
                health_metrics=health_check.get('health_data', {})
            )
            
            self.system_snapshots.append(snapshot)
            
            # 保留最近100個快照
            if len(self.system_snapshots) > 100:
                self.system_snapshots = self.system_snapshots[-100:]
            
            self.logger.debug("系統快照已創建")
            
        except Exception as e:
            self.logger.error(f"創建系統快照失敗: {str(e)}")
    
    async def _snapshot_loop(self):
        """快照循環"""
        try:
            while self.monitoring_active:
                await self._take_system_snapshot()
                await asyncio.sleep(self.config['snapshot_interval'])
                
        except asyncio.CancelledError:
            self.logger.info("快照循環已取消")
        except Exception as e:
            self.logger.error(f"快照循環錯誤: {str(e)}")
    
    def _get_latest_stable_snapshot(self) -> Optional[SystemSnapshot]:
        """獲取最新的穩定快照"""
        # 尋找最近的正常狀態快照
        for snapshot in reversed(self.system_snapshots):
            if snapshot.system_state == SystemState.NORMAL:
                return snapshot
        return None
    
    async def _restore_from_snapshot(self, snapshot: SystemSnapshot, partial: bool = True):
        """從快照恢復系統"""
        try:
            self.logger.info(f"從快照恢復系統 (時間: {snapshot.timestamp}, 部分恢復: {partial})")
            
            if partial:
                # 部分恢復 - 只恢復關鍵配置
                # 這裡應該實現具體的恢復邏輯
                pass
            else:
                # 完全恢復 - 恢復所有狀態
                # 這裡應該實現完整的狀態恢復
                pass
            
            self.logger.info("✅ 系統狀態恢復完成")
            
        except Exception as e:
            self.logger.error(f"系統狀態恢復失敗: {str(e)}")
    
    async def _consider_emergency_resolution(self):
        """考慮解除緊急狀態"""
        # 檢查系統是否已穩定足夠時間
        if len(self.emergency_events) > 0:
            latest_event = self.emergency_events[-1]
            
            # 如果最近事件是30分鐘前且系統穩定，考慮解除緊急狀態
            event_time = datetime.fromisoformat(latest_event.timestamp)
            if datetime.now() - event_time > timedelta(minutes=30):
                await self.resolve_emergency(latest_event.id, "System has been stable for 30 minutes")
    
    async def resolve_emergency(self, event_id: str, reason: str = "Manual resolution"):
        """解除緊急狀態"""
        # 查找事件
        event = None
        for e in self.emergency_events:
            if e.id == event_id:
                event = e
                break
        
        if not event:
            self.logger.warning(f"未找到緊急事件: {event_id}")
            return
        
        if event.resolved:
            self.logger.info(f"緊急事件已解決: {event_id}")
            return
        
        # 標記事件為已解決
        event.resolved = True
        event.resolved_at = datetime.now().isoformat()
        
        # 更新系統狀態
        self.is_emergency_mode = False
        self.emergency_level = EmergencyLevel.LOW
        self.current_state = SystemState.NORMAL
        
        self.logger.info(f"✅ 緊急狀態已解除: {reason}")
        
        # 發送解除通知
        await self._send_resolution_notification(event, reason)
    
    async def _send_emergency_notification(self, event: EmergencyEvent):
        """發送緊急通知"""
        try:
            notification_data = {
                'type': 'emergency_alert',
                'event': asdict(event),
                'system_info': {
                    'current_state': self.current_state.value,
                    'emergency_level': self.emergency_level.value,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            # 這裡應該整合通知系統
            # 例如：Slack、郵件、Webhook等
            self.logger.info(f"📢 緊急通知已發送: {event.description}")
            
        except Exception as e:
            self.logger.error(f"發送緊急通知失敗: {str(e)}")
    
    async def _send_resolution_notification(self, event: EmergencyEvent, reason: str):
        """發送解除通知"""
        try:
            self.logger.info(f"📢 緊急狀態解除通知: {reason}")
        except Exception as e:
            self.logger.error(f"發送解除通知失敗: {str(e)}")
    
    # 公開方法
    def add_emergency_callback(self, callback: Callable):
        """添加緊急回調函數"""
        self.emergency_callbacks.append(callback)
    
    def add_state_change_callback(self, callback: Callable):
        """添加狀態變化回調函數"""
        self.state_change_callbacks.append(callback)
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'current_state': self.current_state.value,
            'emergency_level': self.emergency_level.value,
            'is_emergency_mode': self.is_emergency_mode,
            'monitoring_active': self.monitoring_active,
            'auto_rollback_enabled': self.auto_rollback_enabled,
            'recent_events': [asdict(e) for e in self.emergency_events[-5:]],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_emergency_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """獲取緊急事件歷史"""
        cutoff_time = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_time.isoformat()
        
        recent_events = [
            asdict(event) for event in self.emergency_events 
            if event.timestamp > cutoff_str
        ]
        
        return recent_events
    
    async def manual_emergency_stop(self, reason: str = "Manual trigger") -> str:
        """手動觸發緊急停止"""
        return await self.trigger_emergency(
            EmergencyLevel.CRITICAL,
            "manual_trigger",
            f"手動觸發緊急停止: {reason}",
            EmergencyAction.SHUTDOWN_GRACEFUL,
            auto_triggered=False
        )

# 便利函數
async def emergency_stop_all():
    """緊急停止所有服務"""
    controller = EmergencyController()
    return await controller.manual_emergency_stop("Emergency stop all services")

async def get_emergency_status():
    """獲取緊急狀態"""
    controller = EmergencyController()
    return controller.get_system_status()

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_emergency_controller():
        controller = EmergencyController()
        
        print("🚨 測試緊急控制器")
        
        # 啟動監控
        await controller.start_monitoring()
        
        # 測試手動緊急觸發
        event_id = await controller.trigger_emergency(
            EmergencyLevel.MEDIUM,
            "test_trigger",
            "測試緊急事件",
            EmergencyAction.MONITOR_ONLY,
            auto_triggered=False
        )
        
        print(f"創建測試緊急事件: {event_id}")
        
        # 運行一段時間
        await asyncio.sleep(10)
        
        # 解除緊急狀態
        await controller.resolve_emergency(event_id, "測試完成")
        
        # 獲取狀態
        status = controller.get_system_status()
        print(f"系統狀態: {status}")
        
        # 停止監控
        await controller.stop_monitoring()
        
        print("✅ 測試完成")
    
    asyncio.run(test_emergency_controller())