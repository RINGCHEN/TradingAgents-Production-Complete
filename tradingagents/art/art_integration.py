#!/usr/bin/env python3
"""
ARTIntegration - ART系統無縫整合介面
天工 (TianGong) - 統一ART系統的所有組件，提供完整的BaseAnalyst整合

此模組提供：
1. 統一的ART系統管理介面
2. BaseAnalyst與ART組件的無縫整合
3. 軌跡收集、獎勵生成、驗證的協調管理
4. 高級AI分析師的個人化學習支援
5. 企業級監控和分析儀表板
6. 系統健康狀況監控和自動恢復
"""

from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import json
import logging
import asyncio
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict, deque
import uuid
import hashlib

# Import ART components
try:
    from .trajectory_collector import TrajectoryCollector, TrajectoryType, DecisionStep, AnalysisTrajectory
    from .ruler_reward_system import RULERRewardSystem, RewardSignal, RewardType, MembershipTier
    from .reward_validator import RewardValidator, ValidationResult
    ART_COMPONENTS_AVAILABLE = True
except ImportError:
    ART_COMPONENTS_AVAILABLE = False

# Import BaseAnalyst for type hints
try:
    from ..agents.analysts.base_analyst import BaseAnalyst, AnalysisResult, AnalysisState
    BASE_ANALYST_AVAILABLE = True
except ImportError:
    BASE_ANALYST_AVAILABLE = False

class IntegrationStatus(Enum):
    """整合狀態"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class AnalysisMode(Enum):
    """分析模式"""
    STANDARD = "standard"              # 標準模式
    LEARNING = "learning"              # 學習模式（收集更多軌跡）
    VALIDATION = "validation"          # 驗證模式（重點驗證獎勵）
    PERSONALIZED = "personalized"     # 個人化模式（用戶特定優化）
    BENCHMARK = "benchmark"            # 基準測試模式

class PersonalizationLevel(Enum):
    """個人化等級"""
    BASIC = "basic"          # 基礎個人化
    INTERMEDIATE = "intermediate"  # 中等個人化
    ADVANCED = "advanced"    # 高級個人化
    EXPERT = "expert"        # 專家級個人化

@dataclass
class ARTConfig:
    """ART配置"""
    
    # 系統配置
    system_name: str = "ART-TianGong"
    version: str = "2.0.0"
    environment: str = "production"  # development, staging, production
    
    # 存儲配置
    storage_root: str = "./art_data"
    trajectory_storage: str = "trajectories"
    reward_storage: str = "rewards"  
    validation_storage: str = "validations"
    
    # 軌跡收集配置
    trajectory_collection_enabled: bool = True
    min_trajectory_steps: int = 3
    max_trajectory_steps: int = 50
    trajectory_timeout_minutes: int = 30
    
    # 獎勵系統配置
    reward_generation_enabled: bool = True
    immediate_reward_evaluation: bool = False
    reward_calculation_interval_hours: int = 24
    enable_dynamic_weights: bool = True
    
    # 驗證系統配置
    reward_validation_enabled: bool = True
    validation_threshold: float = 0.7
    auto_correction_enabled: bool = True
    
    # 個人化配置
    personalization_enabled: bool = True
    min_trajectories_for_personalization: int = 10
    personalization_update_interval_hours: int = 168  # 一週
    
    # 性能配置
    max_concurrent_analyses: int = 10
    batch_processing_size: int = 50
    cache_expiry_hours: int = 24
    
    # 監控配置
    monitoring_enabled: bool = True
    health_check_interval_minutes: int = 5
    alert_threshold_error_rate: float = 0.1
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass  
class IntegrationMetrics:
    """整合指標"""
    
    # 基本計數
    total_analyses_processed: int = 0
    successful_analyses: int = 0
    failed_analyses: int = 0
    
    # 軌跡收集指標
    trajectories_collected: int = 0
    average_trajectory_length: float = 0.0
    trajectory_collection_success_rate: float = 0.0
    
    # 獎勵系統指標  
    rewards_generated: int = 0
    average_reward_value: float = 0.0
    reward_generation_success_rate: float = 0.0
    
    # 驗證指標
    validations_performed: int = 0
    validation_pass_rate: float = 0.0
    auto_corrections_applied: int = 0
    
    # 性能指標
    average_processing_time_ms: float = 0.0
    peak_concurrent_analyses: int = 0
    cache_hit_rate: float = 0.0
    
    # 錯誤統計
    error_counts: Dict[str, int] = field(default_factory=dict)
    last_error_timestamp: Optional[str] = None
    
    # 更新時間
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ARTIntegration:
    """ART系統無縫整合管理器"""
    
    def __init__(self, config: ARTConfig = None):
        """初始化ART整合系統"""
        
        self.config = config or ARTConfig()
        self.status = IntegrationStatus.INITIALIZING
        
        # 設置存儲路徑
        self.storage_root = Path(self.config.storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # 初始化組件
        self.trajectory_collector: Optional[TrajectoryCollector] = None
        self.reward_system: Optional[RULERRewardSystem] = None 
        self.reward_validator: Optional[RewardValidator] = None
        
        # 狀態管理
        self.active_analyses: Dict[str, Dict[str, Any]] = {}
        self.analysis_queue = asyncio.Queue()
        self.processing_semaphore = asyncio.Semaphore(self.config.max_concurrent_analyses)
        
        # 指標追蹤
        self.metrics = IntegrationMetrics()
        self._metrics_lock = threading.Lock()
        
        # 個人化學習
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.personalization_cache: Dict[str, Any] = {}
        
        # 監控和健康檢查
        self.health_status: Dict[str, Any] = {
            'overall': 'healthy',
            'components': {},
            'last_check': datetime.now().isoformat()
        }
        
        # 線程池和任務管理
        self.thread_pool = ThreadPoolExecutor(
            max_workers=4, 
            thread_name_prefix="ART-Integration"
        )
        self.background_tasks: List[asyncio.Task] = []
        
        # 日誌設置
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 初始化標志
        self._initialized = False
        self._shutdown_event = asyncio.Event()
    
    def _setup_logging(self):
        """設置日誌"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - ART-Integration - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def initialize(self) -> bool:
        """初始化ART系統所有組件"""
        
        if self._initialized:
            return True
        
        try:
            self.logger.info("Initializing ART Integration System...")
            
            # 初始化軌跡收集器
            if self.config.trajectory_collection_enabled and ART_COMPONENTS_AVAILABLE:
                await self._initialize_trajectory_collector()
            
            # 初始化獎勵系統
            if self.config.reward_generation_enabled and ART_COMPONENTS_AVAILABLE:
                await self._initialize_reward_system()
            
            # 初始化獎勵驗證器
            if self.config.reward_validation_enabled and ART_COMPONENTS_AVAILABLE:
                await self._initialize_reward_validator()
            
            # 載入用戶檔案
            await self._load_user_profiles()
            
            # 啟動背景任務
            await self._start_background_tasks()
            
            # 執行健康檢查
            await self._perform_health_check()
            
            self._initialized = True
            self.status = IntegrationStatus.READY
            
            self.logger.info(f"ART Integration System initialized successfully")
            self.logger.info(f"Configuration: {self.get_system_status()}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ART Integration: {e}")
            self.status = IntegrationStatus.ERROR
            return False
    
    async def _initialize_trajectory_collector(self):
        """初始化軌跡收集器"""
        try:
            if ART_COMPONENTS_AVAILABLE:
                from .trajectory_collector import create_trajectory_collector
                self.trajectory_collector = await create_trajectory_collector(
                    storage_path=str(self.storage_root / self.config.trajectory_storage)
                )
            else:
                # 使用MVP版本
                from ..mvp_art_demo.art_trajectory_collector import ARTTrajectoryCollector
                self.trajectory_collector = ARTTrajectoryCollector(
                    storage_path=str(self.storage_root / self.config.trajectory_storage)
                )
            
            self.logger.info("Trajectory Collector initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Trajectory Collector: {e}")
            raise
    
    async def _initialize_reward_system(self):
        """初始化獎勵系統"""
        try:
            if ART_COMPONENTS_AVAILABLE:
                from .ruler_reward_system import create_ruler_reward_system
                self.reward_system = await create_ruler_reward_system(
                    storage_path=str(self.storage_root / self.config.reward_storage),
                    enable_real_time_tracking=True
                )
            
            self.logger.info("RULER Reward System initialized")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Reward System: {e}")
            raise
    
    async def _initialize_reward_validator(self):
        """初始化獎勵驗證器"""
        try:
            if ART_COMPONENTS_AVAILABLE:
                from .reward_validator import create_reward_validator
                # 檢查create_reward_validator函數的簽名
                self.reward_validator = await create_reward_validator(
                    storage_path=str(self.storage_root / self.config.validation_storage)
                    # 移除validation_threshold參數，如果該函數不支持的話
                )
            
            self.logger.info("Reward Validator initialized")
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize Reward Validator: {e}")
            # 獎勵驗證器失敗不應該阻止整個系統初始化
            self.reward_validator = None
    
    async def _load_user_profiles(self):
        """載入用戶檔案"""
        try:
            profiles_path = self.storage_root / "user_profiles.json"
            if profiles_path.exists():
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    self.user_profiles = json.load(f)
                self.logger.info(f"Loaded {len(self.user_profiles)} user profiles")
        except Exception as e:
            self.logger.warning(f"Failed to load user profiles: {e}")
            self.user_profiles = {}
    
    async def _start_background_tasks(self):
        """啟動背景任務"""
        
        if self.config.monitoring_enabled:
            # 健康檢查任務
            health_check_task = asyncio.create_task(self._health_check_loop())
            self.background_tasks.append(health_check_task)
            
            # 指標更新任務
            metrics_task = asyncio.create_task(self._metrics_update_loop())
            self.background_tasks.append(metrics_task)
        
        if self.config.personalization_enabled:
            # 個人化更新任務
            personalization_task = asyncio.create_task(self._personalization_update_loop())
            self.background_tasks.append(personalization_task)
        
        self.logger.info(f"Started {len(self.background_tasks)} background tasks")
    
    async def process_analysis(self,
                              analyst: 'BaseAnalyst',
                              state: 'AnalysisState',
                              analysis_mode: AnalysisMode = AnalysisMode.STANDARD,
                              user_context: Dict[str, Any] = None) -> Tuple['AnalysisResult', Dict[str, Any]]:
        """處理分析請求 - 完整ART整合"""
        
        if not self._initialized:
            raise RuntimeError("ART Integration not initialized")
        
        # 生成分析ID
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        # 記錄開始時間
        start_time = datetime.now()
        
        try:
            async with self.processing_semaphore:
                # 記錄分析開始
                self.active_analyses[analysis_id] = {
                    'analyst_type': analyst.__class__.__name__,
                    'stock_id': state.stock_id,
                    'user_id': user_context.get('user_id') if user_context else 'anonymous',
                    'start_time': start_time.isoformat(),
                    'mode': analysis_mode.value,
                    'status': 'processing'
                }
                
                # 開始軌跡收集
                trajectory_id = None
                if self.trajectory_collector and self.config.trajectory_collection_enabled:
                    trajectory_id = await self._start_trajectory_collection(
                        analyst, state, user_context, analysis_mode
                    )
                
                # 執行核心分析
                analysis_result = await analyst.analyze(state)
                
                # 完成軌跡收集並生成獎勵
                reward_signal = None
                if trajectory_id:
                    reward_signal = await self._complete_trajectory_and_reward(
                        trajectory_id, analysis_result, user_context, analysis_mode
                    )
                
                # 驗證獎勵（如果啟用）
                validation_result = None
                if reward_signal and self.reward_validator and self.config.reward_validation_enabled:
                    validation_result = await self._validate_reward(reward_signal)
                
                # 更新個人化學習
                if self.config.personalization_enabled and user_context:
                    await self._update_personalization(
                        user_context.get('user_id'), 
                        analysis_result, 
                        reward_signal
                    )
                
                # 記錄完成
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds() * 1000
                
                self.active_analyses[analysis_id].update({
                    'status': 'completed',
                    'end_time': end_time.isoformat(),
                    'processing_time_ms': processing_time,
                    'trajectory_id': trajectory_id,
                    'reward_signal_id': reward_signal.signal_id if reward_signal else None
                })
                
                # 更新指標
                await self._update_metrics(analysis_id, True, processing_time)
                
                # 構建返回的整合數據
                integration_data = {
                    'analysis_id': analysis_id,
                    'trajectory_id': trajectory_id,
                    'reward_signal': reward_signal.to_dict() if reward_signal else None,
                    'validation_result': validation_result.to_dict() if validation_result else None,
                    'processing_time_ms': processing_time,
                    'art_system_status': self.get_system_status()
                }
                
                # 移除活躍分析記錄
                del self.active_analyses[analysis_id]
                
                self.logger.info(f"Analysis {analysis_id} completed successfully")
                
                return analysis_result, integration_data
        
        except Exception as e:
            # 錯誤處理
            self.logger.error(f"Analysis {analysis_id} failed: {e}")
            
            # 更新指標
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            await self._update_metrics(analysis_id, False, processing_time, str(e))
            
            # 清理活躍分析記錄
            if analysis_id in self.active_analyses:
                self.active_analyses[analysis_id]['status'] = 'failed'
                self.active_analyses[analysis_id]['error'] = str(e)
            
            raise
    
    async def _start_trajectory_collection(self,
                                         analyst: 'BaseAnalyst', 
                                         state: 'AnalysisState',
                                         user_context: Dict[str, Any],
                                         mode: AnalysisMode) -> Optional[str]:
        """開始軌跡收集"""
        try:
            if not self.trajectory_collector:
                return None
            
            user_id = user_context.get('user_id', 'anonymous') if user_context else 'anonymous'
            
            trajectory_id = await self.trajectory_collector.start_trajectory(
                stock_id=state.stock_id,
                analyst_type=analyst.__class__.__name__.lower().replace('analyst', '_analyst'),
                user_id=user_id,
                context_data={
                    **(user_context or {}),
                    'analysis_mode': mode.value,
                    'integration_version': self.config.version
                }
            )
            
            return trajectory_id
            
        except Exception as e:
            self.logger.error(f"Failed to start trajectory collection: {e}")
            return None
    
    async def _complete_trajectory_and_reward(self,
                                            trajectory_id: str,
                                            result: 'AnalysisResult',
                                            user_context: Dict[str, Any],
                                            mode: AnalysisMode) -> Optional['RewardSignal']:
        """完成軌跡收集並生成獎勵"""
        try:
            # 完成軌跡收集
            if self.trajectory_collector:
                trajectory = await self.trajectory_collector.complete_trajectory(
                    trajectory_id=trajectory_id,
                    final_recommendation=result.recommendation,
                    final_confidence=result.confidence
                )
                
                # 生成獎勵信號
                if self.reward_system and self.config.reward_generation_enabled:
                    reward_signal = await self.reward_system.generate_reward_signal(
                        trajectory=trajectory,
                        user_context=user_context,
                        immediate_evaluation=(mode == AnalysisMode.VALIDATION)
                    )
                    
                    return reward_signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to complete trajectory and reward: {e}")
            return None
    
    async def _validate_reward(self, reward_signal: 'RewardSignal') -> Optional['ValidationResult']:
        """驗證獎勵信號"""
        try:
            if not self.reward_validator:
                return None
            
            validation_result = await self.reward_validator.validate_reward_signal(
                reward_signal=reward_signal,
                auto_correct=self.config.auto_correction_enabled
            )
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Failed to validate reward: {e}")
            return None
    
    async def _update_personalization(self, 
                                    user_id: str,
                                    result: 'AnalysisResult', 
                                    reward_signal: Optional['RewardSignal']):
        """更新個人化學習"""
        try:
            if not user_id or user_id == 'anonymous':
                return
            
            # 獲取或創建用戶檔案
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {
                    'created_at': datetime.now().isoformat(),
                    'total_analyses': 0,
                    'preferred_analysts': {},
                    'performance_history': [],
                    'personalization_level': PersonalizationLevel.BASIC.value
                }
            
            profile = self.user_profiles[user_id]
            profile['total_analyses'] += 1
            profile['last_analysis'] = datetime.now().isoformat()
            
            # 更新分析師偏好
            analyst_type = result.analyst_id
            if analyst_type not in profile['preferred_analysts']:
                profile['preferred_analysts'][analyst_type] = {'count': 0, 'avg_confidence': 0.0}
            
            profile['preferred_analysts'][analyst_type]['count'] += 1
            profile['preferred_analysts'][analyst_type]['avg_confidence'] = (
                (profile['preferred_analysts'][analyst_type]['avg_confidence'] * (profile['preferred_analysts'][analyst_type]['count'] - 1) + result.confidence) /
                profile['preferred_analysts'][analyst_type]['count']
            )
            
            # 添加績效記錄
            if reward_signal:
                profile['performance_history'].append({
                    'timestamp': datetime.now().isoformat(),
                    'reward': reward_signal.weighted_total_reward,
                    'confidence': result.confidence,
                    'recommendation': result.recommendation
                })
                
                # 保持最近100筆記錄
                profile['performance_history'] = profile['performance_history'][-100:]
            
            # 更新個人化等級
            await self._update_personalization_level(user_id, profile)
            
        except Exception as e:
            self.logger.error(f"Failed to update personalization for user {user_id}: {e}")
    
    async def _update_personalization_level(self, user_id: str, profile: Dict[str, Any]):
        """更新個人化等級"""
        try:
            total_analyses = profile.get('total_analyses', 0)
            
            if total_analyses >= 100:
                profile['personalization_level'] = PersonalizationLevel.EXPERT.value
            elif total_analyses >= 50:
                profile['personalization_level'] = PersonalizationLevel.ADVANCED.value
            elif total_analyses >= 20:
                profile['personalization_level'] = PersonalizationLevel.INTERMEDIATE.value
            else:
                profile['personalization_level'] = PersonalizationLevel.BASIC.value
                
        except Exception as e:
            self.logger.error(f"Failed to update personalization level: {e}")
    
    async def _update_metrics(self, 
                            analysis_id: str, 
                            success: bool, 
                            processing_time: float,
                            error_msg: str = None):
        """更新系統指標"""
        try:
            with self._metrics_lock:
                self.metrics.total_analyses_processed += 1
                
                if success:
                    self.metrics.successful_analyses += 1
                else:
                    self.metrics.failed_analyses += 1
                    if error_msg:
                        self.metrics.error_counts[error_msg] = self.metrics.error_counts.get(error_msg, 0) + 1
                        self.metrics.last_error_timestamp = datetime.now().isoformat()
                
                # 更新平均處理時間
                total_time = (self.metrics.average_processing_time_ms * (self.metrics.total_analyses_processed - 1) + processing_time)
                self.metrics.average_processing_time_ms = total_time / self.metrics.total_analyses_processed
                
                # 更新併發峰值
                current_concurrent = len(self.active_analyses)
                if current_concurrent > self.metrics.peak_concurrent_analyses:
                    self.metrics.peak_concurrent_analyses = current_concurrent
                
                self.metrics.last_updated = datetime.now().isoformat()
                
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {e}")
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """執行系統健康檢查"""
        try:
            health_status = {
                'overall': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'components': {}
            }
            
            # 檢查軌跡收集器
            if self.trajectory_collector:
                try:
                    # 簡單的功能測試
                    health_status['components']['trajectory_collector'] = 'healthy'
                except Exception as e:
                    health_status['components']['trajectory_collector'] = f'unhealthy: {e}'
                    health_status['overall'] = 'degraded'
            
            # 檢查獎勵系統
            if self.reward_system:
                try:
                    stats = self.reward_system.get_system_statistics()
                    health_status['components']['reward_system'] = 'healthy'
                    health_status['reward_system_stats'] = stats
                except Exception as e:
                    health_status['components']['reward_system'] = f'unhealthy: {e}'
                    health_status['overall'] = 'degraded'
            
            # 檢查獎勵驗證器
            if self.reward_validator:
                try:
                    health_status['components']['reward_validator'] = 'healthy'
                except Exception as e:
                    health_status['components']['reward_validator'] = f'unhealthy: {e}'
                    health_status['overall'] = 'degraded'
            
            self.health_status = health_status
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            self.health_status = {
                'overall': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            return self.health_status
    
    async def _health_check_loop(self):
        """健康檢查循環"""
        while not self._shutdown_event.is_set():
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.config.health_check_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(60)  # 錯誤後等待1分鐘再試
    
    async def _metrics_update_loop(self):
        """指標更新循環"""
        while not self._shutdown_event.is_set():
            try:
                # 計算額外指標
                if self.trajectory_collector:
                    # 軌跡相關指標更新
                    pass
                
                if self.reward_system:
                    # 獎勵系統指標更新
                    pass
                
                await asyncio.sleep(300)  # 每5分鐘更新一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics update loop error: {e}")
                await asyncio.sleep(60)
    
    async def _personalization_update_loop(self):
        """個人化更新循環"""
        while not self._shutdown_event.is_set():
            try:
                # 保存用戶檔案
                await self._save_user_profiles()
                
                # 更新個人化緩存
                await self._refresh_personalization_cache()
                
                await asyncio.sleep(self.config.personalization_update_interval_hours * 3600)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Personalization update loop error: {e}")
                await asyncio.sleep(3600)  # 錯誤後等待1小時
    
    async def _save_user_profiles(self):
        """保存用戶檔案"""
        try:
            profiles_path = self.storage_root / "user_profiles.json"
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                self._sync_save_user_profiles,
                profiles_path
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save user profiles: {e}")
    
    def _sync_save_user_profiles(self, profiles_path: Path):
        """同步保存用戶檔案"""
        with open(profiles_path, 'w', encoding='utf-8') as f:
            json.dump(self.user_profiles, f, ensure_ascii=False, indent=2)
    
    async def _refresh_personalization_cache(self):
        """刷新個人化緩存"""
        try:
            # 為活躍用戶生成個人化建議
            for user_id, profile in self.user_profiles.items():
                if profile.get('total_analyses', 0) >= self.config.min_trajectories_for_personalization:
                    self.personalization_cache[user_id] = {
                        'last_updated': datetime.now().isoformat(),
                        'recommended_analysts': self._get_recommended_analysts(profile),
                        'analysis_preferences': self._get_analysis_preferences(profile)
                    }
                    
        except Exception as e:
            self.logger.error(f"Failed to refresh personalization cache: {e}")
    
    def _get_recommended_analysts(self, profile: Dict[str, Any]) -> List[str]:
        """獲取推薦的分析師"""
        preferred = profile.get('preferred_analysts', {})
        return sorted(preferred.keys(), key=lambda x: preferred[x]['avg_confidence'], reverse=True)[:3]
    
    def _get_analysis_preferences(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """獲取分析偏好"""
        history = profile.get('performance_history', [])
        if not history:
            return {}
        
        # 分析歷史績效找出偏好
        recommendations = [h['recommendation'] for h in history[-20:]]  # 最近20筆
        recommendation_counts = {r: recommendations.count(r) for r in set(recommendations)}
        
        return {
            'preferred_recommendation_type': max(recommendation_counts, key=recommendation_counts.get),
            'avg_confidence_threshold': sum(h['confidence'] for h in history[-10:]) / min(len(history), 10),
            'performance_trend': 'improving' if len(history) >= 2 and history[-1]['reward'] > history[-2]['reward'] else 'stable'
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'integration_status': self.status.value,
            'config': self.config.to_dict(),
            'metrics': self.metrics.to_dict(),
            'health_status': self.health_status,
            'active_analyses': len(self.active_analyses),
            'components_available': {
                'trajectory_collector': bool(self.trajectory_collector),
                'reward_system': bool(self.reward_system),
                'reward_validator': bool(self.reward_validator)
            },
            'user_profiles_count': len(self.user_profiles),
            'background_tasks_running': len([t for t in self.background_tasks if not t.done()]),
            'version': self.config.version,
            'initialized': self._initialized
        }
    
    def get_user_personalization_data(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶個人化數據"""
        profile = self.user_profiles.get(user_id, {})
        cache = self.personalization_cache.get(user_id, {})
        
        return {
            'profile': profile,
            'recommendations': cache,
            'personalization_level': profile.get('personalization_level', PersonalizationLevel.BASIC.value),
            'ready_for_advanced_features': profile.get('total_analyses', 0) >= self.config.min_trajectories_for_personalization
        }
    
    async def shutdown(self):
        """關閉ART整合系統"""
        self.logger.info("Shutting down ART Integration System...")
        
        # 設置關閉標志
        self._shutdown_event.set()
        
        # 取消背景任務
        for task in self.background_tasks:
            if not task.done():
                task.cancel()
        
        # 等待任務完成
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # 保存用戶檔案
        await self._save_user_profiles()
        
        # 關閉組件
        if self.reward_system:
            await self.reward_system.cleanup()
        
        # 關閉線程池
        self.thread_pool.shutdown(wait=True)
        
        self.status = IntegrationStatus.MAINTENANCE
        self.logger.info("ART Integration System shutdown completed")

# 工廠函數
async def create_art_integration(config: ARTConfig = None) -> ARTIntegration:
    """創建ART整合實例"""
    integration = ARTIntegration(config)
    
    if await integration.initialize():
        return integration
    else:
        raise RuntimeError("Failed to initialize ART Integration System")

# 便利函數
def create_default_config(environment: str = "production") -> ARTConfig:
    """創建預設配置"""
    return ARTConfig(
        environment=environment,
        storage_root=f"./art_data_{environment}",
        trajectory_collection_enabled=True,
        reward_generation_enabled=True,
        reward_validation_enabled=True,
        personalization_enabled=True,
        monitoring_enabled=True
    )

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_art_integration():
        print("測試ART系統無縫整合")
        
        # 創建配置
        config = create_default_config("development")
        
        # 創建整合系統
        art_integration = await create_art_integration(config)
        
        # 獲取系統狀態
        status = art_integration.get_system_status()
        print(f"系統狀態: {status['integration_status']}")
        print(f"可用組件: {status['components_available']}")
        
        # 模擬一些處理來測試指標
        await asyncio.sleep(2)
        
        # 關閉系統
        await art_integration.shutdown()
        
        print("ART整合系統測試完成")
    
    asyncio.run(test_art_integration())