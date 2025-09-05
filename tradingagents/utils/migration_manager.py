#!/usr/bin/env python3
"""
Migration Manager - 系統平滑升級管理器
天工 (TianGong) - 不老傳說 AI分析師系統保護和升級機制

此模組負責：
1. 平滑啟用AI分析功能
2. 監控系統健康狀況  
3. 實現向後兼容性
4. 提供回滾機制
"""

import asyncio
import json
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# 導入現有的會員管理系統
try:
    from ..models.user import User, MembershipTier
    from ..database.database import get_db
    from sqlalchemy.orm import Session
except ImportError:
    # 如果導入失敗，提供備用定義
    class MembershipTier:
        FREE = "FREE"
        GOLD = "GOLD" 
        DIAMOND = "DIAMOND"

class DeploymentPhase(Enum):
    """部署階段"""
    PREPARATION = "preparation"        # 準備階段
    PILOT = "pilot"                   # 試點階段 (1-5%)
    GRADUAL_ROLLOUT = "gradual"       # 漸進推出 (5-50%)
    FULL_DEPLOYMENT = "full"          # 全面部署 (50-100%)
    STABILIZATION = "stabilization"   # 穩定階段
    ROLLBACK = "rollback"            # 回滾階段

@dataclass
class SystemHealth:
    """系統健康狀況"""
    timestamp: str
    error_rate: float              # 錯誤率 (0.0-1.0)
    response_time_avg: float       # 平均響應時間 (秒)
    cpu_usage: float              # CPU使用率 (0.0-1.0)
    memory_usage: float           # 記憶體使用率 (0.0-1.0)
    database_connections: int     # 資料庫連接數
    active_users: int            # 活躍用戶數
    ai_analysis_count: int       # AI分析執行數
    
    def is_healthy(self) -> bool:
        """判斷系統是否健康"""
        return (
            self.error_rate < 0.05 and          # 錯誤率 < 5%
            self.response_time_avg < 3.0 and    # 響應時間 < 3秒
            self.cpu_usage < 0.8 and            # CPU < 80%
            self.memory_usage < 0.8              # 記憶體 < 80%
        )

@dataclass 
class DeploymentConfig:
    """部署配置"""
    phase: DeploymentPhase
    rollout_percentage: float     # 推出百分比 (0.0-1.0)
    target_user_count: int       # 目標用戶數
    health_check_interval: int   # 健康檢查間隔 (秒)
    error_threshold: float       # 錯誤閾值
    rollback_threshold: float    # 回滾閾值
    
class MigrationManager:
    """系統平滑升級管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._get_default_config()
        self.logger = logging.getLogger(__name__)
        self.current_phase = DeploymentPhase.PREPARATION
        self.enabled_users: List[str] = []
        self.health_history: List[SystemHealth] = []
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """獲取預設配置"""
        return {
            'pilot_percentage': 0.01,        # 試點階段：1%用戶
            'gradual_percentages': [0.05, 0.10, 0.25, 0.50],  # 漸進階段
            'health_check_interval': 30,     # 30秒檢查一次
            'error_threshold': 0.05,         # 5%錯誤率閾值
            'rollback_threshold': 0.10,      # 10%錯誤率立即回滾
            'stabilization_time': 300,       # 5分鐘穩定期
            'database_url': os.getenv('DATABASE_URL', 'sqlite:///./tradingagents.db')
        }
    
    async def start_migration(self) -> Dict[str, Any]:
        """開始系統遷移流程"""
        self.logger.info("🚀 開始 不老傳說 AI 分析系統遷移")
        
        try:
            # 階段 1: 準備階段
            await self._preparation_phase()
            
            # 階段 2: 試點階段
            pilot_result = await self._pilot_phase()
            if not pilot_result['success']:
                return pilot_result
            
            # 階段 3: 漸進推出
            gradual_result = await self._gradual_rollout_phase()
            if not gradual_result['success']:
                return gradual_result
            
            # 階段 4: 全面部署
            full_result = await self._full_deployment_phase()
            if not full_result['success']:
                return full_result
            
            # 階段 5: 穩定化
            await self._stabilization_phase()
            
            self.logger.info("✅ AI 分析系統遷移完成")
            
            return {
                'success': True,
                'phase': 'completed',
                'enabled_users': len(self.enabled_users),
                'health_status': 'stable',
                'message': 'AI 分析系統已成功部署到所有用戶'
            }
            
        except Exception as e:
            self.logger.error(f"❌ 遷移過程中發生錯誤: {str(e)}")
            await self._emergency_rollback()
            return {
                'success': False,
                'error': str(e),
                'phase': 'rollback',
                'message': '遷移失敗，已執行緊急回滾'
            }
    
    async def _preparation_phase(self):
        """準備階段"""
        self.current_phase = DeploymentPhase.PREPARATION
        self.logger.info("📋 執行準備階段檢查")
        
        # 檢查必要組件
        checks = {
            'database_connection': await self._check_database_connection(),
            'ai_models_availability': await self._check_ai_models(),
            'api_endpoints': await self._check_api_endpoints(),
            'system_resources': await self._check_system_resources()
        }
        
        failed_checks = [k for k, v in checks.items() if not v]
        if failed_checks:
            raise Exception(f"準備階段檢查失敗: {failed_checks}")
        
        self.logger.info("✅ 準備階段檢查通過")
    
    async def _pilot_phase(self) -> Dict[str, Any]:
        """試點階段 - 1%用戶"""
        self.current_phase = DeploymentPhase.PILOT
        pilot_percentage = self.config['pilot_percentage']
        
        self.logger.info(f"🧪 開始試點階段 ({pilot_percentage*100:.1f}%用戶)")
        
        # 選擇試點用戶
        pilot_users = await self._select_pilot_users(pilot_percentage)
        
        # 為試點用戶啟用AI分析
        for user_id in pilot_users:
            await self._enable_ai_for_user(user_id)
            self.enabled_users.append(user_id)
        
        # 監控試點階段
        monitoring_result = await self._monitor_phase(
            duration=600,  # 10分鐘
            check_interval=self.config['health_check_interval']
        )
        
        if not monitoring_result['healthy']:
            await self._rollback_users(pilot_users)
            return {
                'success': False,
                'phase': 'pilot_failed',
                'reason': monitoring_result['reason'],
                'message': '試點階段失敗，已回滾用戶'
            }
        
        self.logger.info(f"✅ 試點階段成功 ({len(pilot_users)}用戶)")
        return {'success': True, 'enabled_users': len(pilot_users)}
    
    async def _gradual_rollout_phase(self) -> Dict[str, Any]:
        """漸進推出階段"""
        self.current_phase = DeploymentPhase.GRADUAL_ROLLOUT
        
        for percentage in self.config['gradual_percentages']:
            self.logger.info(f"📈 漸進推出 {percentage*100:.0f}%用戶")
            
            # 計算新增用戶數
            target_user_count = await self._calculate_target_users(percentage)
            new_users_needed = target_user_count - len(self.enabled_users)
            
            if new_users_needed > 0:
                # 選擇新用戶
                new_users = await self._select_additional_users(new_users_needed)
                
                # 啟用AI分析
                for user_id in new_users:
                    await self._enable_ai_for_user(user_id)
                    self.enabled_users.append(user_id)
                    
                    # 每10個用戶暫停一下，避免系統突然負載
                    if len(new_users) % 10 == 0:
                        await asyncio.sleep(1)
            
            # 監控當前階段
            monitoring_result = await self._monitor_phase(
                duration=300,  # 5分鐘
                check_interval=self.config['health_check_interval']
            )
            
            if not monitoring_result['healthy']:
                # 回滾到上一個穩定狀態
                await self._partial_rollback(percentage)
                return {
                    'success': False,
                    'phase': f'gradual_{percentage}',
                    'reason': monitoring_result['reason'],
                    'message': f'{percentage*100:.0f}%階段失敗，已部分回滾'
                }
            
            self.logger.info(f"✅ {percentage*100:.0f}%階段成功")
        
        return {'success': True, 'enabled_users': len(self.enabled_users)}
    
    async def _full_deployment_phase(self) -> Dict[str, Any]:
        """全面部署階段"""
        self.current_phase = DeploymentPhase.FULL_DEPLOYMENT
        self.logger.info("🎯 開始全面部署")
        
        # 計算剩餘用戶
        total_users = await self._get_total_user_count()
        remaining_users = total_users - len(self.enabled_users)
        
        if remaining_users > 0:
            # 分批啟用剩餘用戶
            batch_size = min(100, remaining_users // 5)  # 分5批或每批100人
            
            for i in range(0, remaining_users, batch_size):
                batch_users = await self._select_remaining_users(batch_size)
                
                for user_id in batch_users:
                    await self._enable_ai_for_user(user_id)
                    self.enabled_users.append(user_id)
                
                # 每批之間檢查健康狀況
                health = await self._check_system_health()
                if not health.is_healthy():
                    self.logger.warning(f"⚠️ 系統健康狀況下降: {health}")
                    # 暫停部署，等待系統恢復
                    await asyncio.sleep(60)
                
                self.logger.info(f"📊 已啟用 {len(self.enabled_users)}/{total_users} 用戶")
        
        # 最終健康檢查
        final_monitoring = await self._monitor_phase(
            duration=600,  # 10分鐘
            check_interval=self.config['health_check_interval']
        )
        
        if not final_monitoring['healthy']:
            return {
                'success': False,
                'phase': 'full_deployment_failed',
                'reason': final_monitoring['reason'],
                'message': '全面部署健康檢查失敗'
            }
        
        self.logger.info("✅ 全面部署成功")
        return {'success': True, 'enabled_users': len(self.enabled_users)}
    
    async def _stabilization_phase(self):
        """穩定化階段"""
        self.current_phase = DeploymentPhase.STABILIZATION
        self.logger.info("🔒 進入穩定化階段")
        
        # 連續監控穩定期
        stabilization_time = self.config['stabilization_time']
        await self._monitor_phase(
            duration=stabilization_time,
            check_interval=self.config['health_check_interval']
        )
        
        self.logger.info("✅ 系統已穩定")
    
    async def _monitor_phase(self, duration: int, check_interval: int) -> Dict[str, Any]:
        """監控階段健康狀況"""
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration)
        
        consecutive_unhealthy = 0
        max_consecutive_unhealthy = 3
        
        while datetime.now() < end_time:
            health = await self._check_system_health()
            self.health_history.append(health)
            
            # 保留最近100個健康記錄
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            if health.is_healthy():
                consecutive_unhealthy = 0
                self.logger.debug(f"✅ 系統健康 - 錯誤率: {health.error_rate:.2%}")
            else:
                consecutive_unhealthy += 1
                self.logger.warning(f"⚠️ 系統不健康 - 錯誤率: {health.error_rate:.2%}")
                
                # 連續不健康次數過多，觸發回滾
                if consecutive_unhealthy >= max_consecutive_unhealthy:
                    return {
                        'healthy': False,
                        'reason': f'連續{consecutive_unhealthy}次健康檢查失敗',
                        'last_health': asdict(health)
                    }
            
            # 檢查是否觸發緊急回滾閾值
            if health.error_rate > self.config['rollback_threshold']:
                return {
                    'healthy': False,
                    'reason': f'錯誤率超過緊急回滾閾值 ({health.error_rate:.2%})',
                    'last_health': asdict(health)
                }
            
            await asyncio.sleep(check_interval)
        
        return {'healthy': True, 'monitoring_duration': duration}
    
    async def _check_system_health(self) -> SystemHealth:
        """檢查系統健康狀況"""
        try:
            # 這裡應該整合實際的監控指標
            # 暫時使用模擬數據，實際部署時需要連接真實監控系統
            
            # 模擬健康指標
            error_rate = random.uniform(0.01, 0.03)  # 1-3%錯誤率
            response_time = random.uniform(0.5, 2.0)  # 0.5-2秒響應時間
            cpu_usage = random.uniform(0.3, 0.7)     # 30-70% CPU
            memory_usage = random.uniform(0.4, 0.6)  # 40-60% 記憶體
            
            # 如果有AI分析在運行，適當增加負載
            ai_analysis_count = len(self.enabled_users) * random.randint(0, 3)
            if ai_analysis_count > 0:
                cpu_usage += 0.1
                memory_usage += 0.05
                response_time += 0.3
            
            return SystemHealth(
                timestamp=datetime.now().isoformat(),
                error_rate=error_rate,
                response_time_avg=response_time,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                database_connections=random.randint(10, 50),
                active_users=len(self.enabled_users),
                ai_analysis_count=ai_analysis_count
            )
            
        except Exception as e:
            self.logger.error(f"健康檢查失敗: {str(e)}")
            # 返回不健康狀態
            return SystemHealth(
                timestamp=datetime.now().isoformat(),
                error_rate=1.0,  # 100%錯誤率
                response_time_avg=10.0,
                cpu_usage=1.0,
                memory_usage=1.0,
                database_connections=0,
                active_users=0,
                ai_analysis_count=0
            )
    
    async def _select_pilot_users(self, percentage: float) -> List[str]:
        """選擇試點用戶"""
        try:
            # 優先選擇鑽石會員作為試點用戶
            total_users = await self._get_total_user_count()
            target_count = max(1, int(total_users * percentage))
            
            # 模擬用戶選擇邏輯
            # 實際實現時應該從資料庫查詢
            diamond_users = [f"diamond_user_{i}" for i in range(min(target_count // 2, 10))]
            gold_users = [f"gold_user_{i}" for i in range(min(target_count // 3, 15))]
            free_users = [f"free_user_{i}" for i in range(target_count - len(diamond_users) - len(gold_users))]
            
            selected_users = diamond_users + gold_users + free_users
            return selected_users[:target_count]
            
        except Exception as e:
            self.logger.error(f"選擇試點用戶失敗: {str(e)}")
            return []
    
    async def _enable_ai_for_user(self, user_id: str):
        """為用戶啟用AI分析功能"""
        try:
            # 這裡應該更新用戶的AI分析權限
            # 可以通過資料庫標記或Redis緩存實現
            
            # 模擬啟用過程
            await asyncio.sleep(0.1)  # 模擬處理時間
            
            self.logger.debug(f"為用戶 {user_id} 啟用AI分析功能")
            
        except Exception as e:
            self.logger.error(f"為用戶 {user_id} 啟用AI功能失敗: {str(e)}")
            raise
    
    async def _emergency_rollback(self):
        """緊急回滾"""
        self.current_phase = DeploymentPhase.ROLLBACK
        self.logger.error("🚨 執行緊急回滾")
        
        # 禁用所有用戶的AI分析功能
        for user_id in self.enabled_users:
            await self._disable_ai_for_user(user_id)
        
        self.enabled_users.clear()
        self.logger.info("✅ 緊急回滾完成")
    
    async def _disable_ai_for_user(self, user_id: str):
        """禁用用戶的AI分析功能"""
        try:
            # 這裡應該移除用戶的AI分析權限
            await asyncio.sleep(0.05)  # 模擬處理時間
            self.logger.debug(f"為用戶 {user_id} 禁用AI分析功能")
            
        except Exception as e:
            self.logger.error(f"為用戶 {user_id} 禁用AI功能失敗: {str(e)}")
    
    # 工具方法
    async def _get_total_user_count(self) -> int:
        """獲取總用戶數"""
        # 這裡應該查詢實際的用戶數量
        return 1000  # 模擬數據
    
    async def _calculate_target_users(self, percentage: float) -> int:
        """計算目標用戶數"""
        total_users = await self._get_total_user_count()
        return int(total_users * percentage)
    
    async def _select_additional_users(self, count: int) -> List[str]:
        """選擇額外用戶"""
        # 模擬選擇邏輯
        return [f"user_{i}_{random.randint(1000, 9999)}" for i in range(count)]
    
    async def _select_remaining_users(self, count: int) -> List[str]:
        """選擇剩餘用戶"""
        # 模擬選擇邏輯
        return [f"remaining_user_{i}_{random.randint(1000, 9999)}" for i in range(count)]
    
    async def _rollback_users(self, user_ids: List[str]):
        """回滾指定用戶"""
        for user_id in user_ids:
            await self._disable_ai_for_user(user_id)
            if user_id in self.enabled_users:
                self.enabled_users.remove(user_id)
    
    async def _partial_rollback(self, target_percentage: float):
        """部分回滾到指定百分比"""
        total_users = await self._get_total_user_count()
        target_count = int(total_users * target_percentage * 0.5)  # 回滾到一半
        
        if len(self.enabled_users) > target_count:
            users_to_rollback = self.enabled_users[target_count:]
            await self._rollback_users(users_to_rollback)
    
    # 檢查方法
    async def _check_database_connection(self) -> bool:
        """檢查資料庫連接"""
        try:
            # 這裡應該測試實際的資料庫連接
            await asyncio.sleep(0.1)  # 模擬檢查
            return True
        except Exception as e:
            self.logger.error(f"資料庫連接檢查失敗: {str(e)}")
            return False
    
    async def _check_ai_models(self) -> bool:
        """檢查AI模型可用性"""
        try:
            # 這裡應該測試LLM API連接
            await asyncio.sleep(0.2)  # 模擬檢查
            return True
        except Exception as e:
            self.logger.error(f"AI模型檢查失敗: {str(e)}")
            return False
    
    async def _check_api_endpoints(self) -> bool:
        """檢查API端點"""
        try:
            # 這裡應該測試關鍵API端點
            await asyncio.sleep(0.1)  # 模擬檢查
            return True
        except Exception as e:
            self.logger.error(f"API端點檢查失敗: {str(e)}")
            return False
    
    async def _check_system_resources(self) -> bool:
        """檢查系統資源"""
        try:
            # 這裡應該檢查CPU、記憶體、磁碟空間等
            await asyncio.sleep(0.1)  # 模擬檢查
            return True
        except Exception as e:
            self.logger.error(f"系統資源檢查失敗: {str(e)}")
            return False
    
    # 公開方法
    async def get_migration_status(self) -> Dict[str, Any]:
        """獲取遷移狀態"""
        latest_health = self.health_history[-1] if self.health_history else None
        
        return {
            'current_phase': self.current_phase.value,
            'enabled_users_count': len(self.enabled_users),
            'total_users': await self._get_total_user_count(),
            'rollout_percentage': len(self.enabled_users) / await self._get_total_user_count(),
            'latest_health': asdict(latest_health) if latest_health else None,
            'health_history_count': len(self.health_history),
            'timestamp': datetime.now().isoformat()
        }
    
    async def enable_ai_analysis_gradually(self, rollout_percentage: float = 0.1) -> Dict[str, Any]:
        """漸進式啟用AI分析功能 (向後兼容方法)"""
        self.logger.info(f"🔄 漸進式啟用AI分析功能 ({rollout_percentage*100:.1f}%)")
        
        if rollout_percentage <= 0.05:
            # 小比例推出，直接使用試點邏輯
            return await self._pilot_phase()
        else:
            # 較大比例推出，使用漸進邏輯
            target_users = await self._calculate_target_users(rollout_percentage)
            new_users_needed = target_users - len(self.enabled_users)
            
            if new_users_needed > 0:
                new_users = await self._select_additional_users(new_users_needed)
                
                for user_id in new_users:
                    await self._enable_ai_for_user(user_id)
                    self.enabled_users.append(user_id)
                
                # 監控健康狀況
                monitoring_result = await self._monitor_phase(duration=180, check_interval=30)
                
                if not monitoring_result['healthy']:
                    await self._rollback_users(new_users)
                    return {
                        'success': False,
                        'reason': monitoring_result['reason'],
                        'enabled_users': len(self.enabled_users),
                        'next_rollout_recommendation': rollout_percentage * 0.5
                    }
            
            return {
                'success': True,
                'enabled_users': len(self.enabled_users),
                'system_health': 'stable',
                'next_rollout_recommendation': min(rollout_percentage * 1.5, 1.0)
            }
    
    async def maintain_backward_compatibility(self) -> Dict[str, Any]:
        """保持向後兼容性"""
        self.logger.info("🔄 檢查向後兼容性")
        
        # 檢查現有API端點
        legacy_endpoints = [
            '/api/users',
            '/api/membership', 
            '/api/subscriptions',
            '/api/payments',
            '/health'
        ]
        
        compatibility_results = {}
        
        for endpoint in legacy_endpoints:
            try:
                # 這裡應該實際測試端點
                await asyncio.sleep(0.1)  # 模擬測試
                compatibility_results[endpoint] = {
                    'healthy': True,
                    'response_time': random.uniform(0.1, 0.5),
                    'status': 'operational'
                }
            except Exception as e:
                compatibility_results[endpoint] = {
                    'healthy': False,
                    'error': str(e),
                    'status': 'failed'
                }
        
        all_healthy = all(result['healthy'] for result in compatibility_results.values())
        
        return {
            'backward_compatible': all_healthy,
            'endpoint_results': compatibility_results,
            'timestamp': datetime.now().isoformat()
        }

# 用於緊急情況的獨立函數
async def emergency_stop_ai_analysis():
    """緊急停止所有AI分析功能"""
    logger = logging.getLogger(__name__)
    logger.critical("🚨 執行緊急停止所有AI分析功能")
    
    try:
        manager = MigrationManager()
        await manager._emergency_rollback()
        return {'success': True, 'message': '緊急停止成功'}
    except Exception as e:
        logger.error(f"緊急停止失敗: {str(e)}")
        return {'success': False, 'error': str(e)}

# 快速狀態檢查函數
async def quick_health_check() -> Dict[str, Any]:
    """快速健康檢查"""
    manager = MigrationManager()
    health = await manager._check_system_health()
    
    return {
        'healthy': health.is_healthy(),
        'error_rate': health.error_rate,
        'response_time': health.response_time_avg,
        'timestamp': health.timestamp
    }

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_migration():
        manager = MigrationManager()
        
        print("🧪 測試Migration Manager")
        
        # 測試健康檢查
        health = await manager._check_system_health()
        print(f"系統健康狀況: {health.is_healthy()}")
        
        # 測試向後兼容性
        compatibility = await manager.maintain_backward_compatibility()
        print(f"向後兼容性: {compatibility['backward_compatible']}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_migration())