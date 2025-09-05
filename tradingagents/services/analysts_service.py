#!/usr/bin/env python3
"""
Analysts Service - 完全獨立的分析師服務架構
天工 (TianGong) - 世界級智能分析師系統核心服務

此模組提供：
1. 完全獨立的分析師服務架構
2. ART (OpenPipe) 強化學習整合
3. 可插拔的分析師註冊和發現機制
4. 多 LLM 提供商支持 (OpenAI, Anthropic, etc.)
5. Taiwan 市場專業分析師支持
"""

import asyncio
import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

# ART (OpenPipe) Integration
try:
    import openpipe_art as art
    ART_AVAILABLE = True
except ImportError:
    ART_AVAILABLE = False
    art = None

from ..agents.analysts.base_analyst import (
    BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType, 
    AnalysisConfidenceLevel, create_analysis_state
)


class AnalysisQuality(Enum):
    """分析品質等級"""
    POOR = "poor"           # 0.0-0.3
    FAIR = "fair"           # 0.3-0.5
    GOOD = "good"           # 0.5-0.7
    EXCELLENT = "excellent" # 0.7-0.9
    OUTSTANDING = "outstanding" # 0.9-1.0


class TrainingStatus(Enum):
    """訓練狀態"""
    NOT_STARTED = "not_started"
    COLLECTING_DATA = "collecting_data"
    TRAINING = "training"
    EVALUATING = "evaluating"
    DEPLOYED = "deployed"
    FAILED = "failed"


@dataclass
class AnalystPerformanceMetrics:
    """分析師性能指標"""
    analyst_id: str
    total_analyses: int = 0
    accuracy_rate: float = 0.0
    average_confidence: float = 0.0
    average_response_time: float = 0.0
    success_rate: float = 0.0
    
    # 強化學習相關指標
    cumulative_reward: float = 0.0
    avg_reward_per_analysis: float = 0.0
    improvement_rate: float = 0.0
    
    # 成本效益指標
    total_cost: float = 0.0
    cost_per_analysis: float = 0.0
    roi_score: float = 0.0
    
    # 時間追蹤
    last_analysis_time: Optional[datetime] = None
    first_analysis_time: Optional[datetime] = None
    
    def __post_init__(self):
        if self.first_analysis_time is None:
            self.first_analysis_time = datetime.now()


@dataclass
class TrainingTrajectory:
    """訓練軌跡數據"""
    trajectory_id: str
    analyst_id: str
    timestamp: datetime
    
    # 輸入數據
    analysis_state: AnalysisState
    prompt: str
    context: Dict[str, Any]
    
    # 輸出數據
    analysis_result: AnalysisResult
    model_response: Dict[str, Any]
    
    # 獎勵信號
    reward_score: float = 0.0
    market_validation: Optional[float] = None  # 市場後驗證分數
    user_feedback: Optional[float] = None      # 用戶反饋分數
    
    # 元數據
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp') or self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AnalystConfig:
    """分析師配置"""
    analyst_class: str
    module_path: str
    config: Dict[str, Any] = field(default_factory=dict)
    
    # ART 配置
    art_enabled: bool = False
    training_config: Dict[str, Any] = field(default_factory=dict)
    
    # 性能配置
    max_concurrent_analyses: int = 5
    timeout_seconds: int = 120
    
    # 品質控制
    min_confidence_threshold: float = 0.3
    quality_gates: List[str] = field(default_factory=list)


class AnalystsServiceRegistry:
    """分析師服務註冊表"""
    
    def __init__(self):
        self._analysts: Dict[str, Type[BaseAnalyst]] = {}
        self._configs: Dict[str, AnalystConfig] = {}
        self._instances: Dict[str, BaseAnalyst] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
    
    def register_analyst(
        self, 
        analyst_id: str, 
        analyst_class: Type[BaseAnalyst],
        config: AnalystConfig
    ) -> bool:
        """註冊分析師"""
        
        with self._lock:
            try:
                # 驗證分析師類
                if not issubclass(analyst_class, BaseAnalyst):
                    raise ValueError(f"分析師類必須繼承自 BaseAnalyst: {analyst_class}")
                
                # 檢查必要方法
                required_methods = ['analyze', 'get_analysis_type', 'get_analysis_prompt']
                for method in required_methods:
                    if not hasattr(analyst_class, method):
                        raise ValueError(f"分析師類缺少必要方法: {method}")
                
                self._analysts[analyst_id] = analyst_class
                self._configs[analyst_id] = config
                
                self.logger.info(f"分析師註冊成功: {analyst_id}")
                return True
                
            except Exception as e:
                self.logger.error(f"分析師註冊失敗 {analyst_id}: {str(e)}")
                return False
    
    def discover_analysts(self, search_paths: List[str]) -> int:
        """自動發現分析師"""
        
        discovered_count = 0
        
        for path in search_paths:
            try:
                path_obj = Path(path)
                if not path_obj.exists():
                    continue
                
                # 搜索 Python 文件
                for py_file in path_obj.rglob("*_analyst.py"):
                    try:
                        # 動態導入模組
                        module_name = py_file.stem
                        spec = importlib.util.spec_from_file_location(module_name, py_file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        # 查找分析師類
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, BaseAnalyst) and 
                                obj != BaseAnalyst and
                                name.endswith('Analyst')):
                                
                                analyst_id = name.lower().replace('analyst', '_analyst')
                                
                                # 創建默認配置
                                config = AnalystConfig(
                                    analyst_class=name,
                                    module_path=str(py_file),
                                    art_enabled=True  # 默認啟用 ART
                                )
                                
                                if self.register_analyst(analyst_id, obj, config):
                                    discovered_count += 1
                                    
                    except Exception as e:
                        self.logger.warning(f"無法加載分析師模組 {py_file}: {str(e)}")
                        
            except Exception as e:
                self.logger.error(f"搜索路徑錯誤 {path}: {str(e)}")
        
        self.logger.info(f"自動發現 {discovered_count} 個分析師")
        return discovered_count
    
    def get_analyst_instance(self, analyst_id: str) -> Optional[BaseAnalyst]:
        """獲取分析師實例"""
        
        with self._lock:
            # 檢查現有實例
            if analyst_id in self._instances:
                return self._instances[analyst_id]
            
            # 創建新實例
            if analyst_id in self._analysts:
                try:
                    analyst_class = self._analysts[analyst_id]
                    config = self._configs[analyst_id]
                    
                    instance = analyst_class(config.config)
                    self._instances[analyst_id] = instance
                    
                    return instance
                    
                except Exception as e:
                    self.logger.error(f"創建分析師實例失敗 {analyst_id}: {str(e)}")
                    return None
            
            return None
    
    def list_analysts(self) -> List[Dict[str, Any]]:
        """列出所有已註冊的分析師"""
        
        with self._lock:
            analysts_info = []
            
            for analyst_id in self._analysts:
                config = self._configs[analyst_id]
                instance = self.get_analyst_instance(analyst_id)
                
                info = {
                    'analyst_id': analyst_id,
                    'class_name': config.analyst_class,
                    'module_path': config.module_path,
                    'art_enabled': config.art_enabled,
                    'available': instance is not None
                }
                
                if instance:
                    info.update(instance.get_analyst_info())
                
                analysts_info.append(info)
            
            return analysts_info
    
    def unregister_analyst(self, analyst_id: str) -> bool:
        """註銷分析師"""
        
        with self._lock:
            if analyst_id in self._analysts:
                # 清理實例
                if analyst_id in self._instances:
                    del self._instances[analyst_id]
                
                # 清理註冊信息
                del self._analysts[analyst_id]
                del self._configs[analyst_id]
                
                self.logger.info(f"分析師註銷成功: {analyst_id}")
                return True
            
            return False


class ARTIntegration:
    """ART (OpenPipe) 強化學習整合"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.is_available = ART_AVAILABLE
        
        if self.is_available:
            self._initialize_art_client()
        else:
            self.logger.warning("ART 不可用，將使用模擬模式")
    
    def _initialize_art_client(self):
        """初始化 ART 客戶端"""
        
        try:
            # 初始化 ART 客戶端
            self.client = art.ARTClient(
                base_url=self.config.get('art_server_url', 'http://localhost:8000'),
                api_key=self.config.get('art_api_key')
            )
            
            self.logger.info("ART 客戶端初始化成功")
            
        except Exception as e:
            self.logger.error(f"ART 客戶端初始化失敗: {str(e)}")
            self.is_available = False
    
    async def collect_trajectory(self, trajectory: TrainingTrajectory) -> bool:
        """收集訓練軌跡"""
        
        if not self.is_available:
            # 模擬模式：只記錄軌跡
            self.logger.debug(f"模擬收集軌跡: {trajectory.trajectory_id}")
            return True
        
        try:
            # 準備軌跡數據
            trajectory_data = {
                'trajectory_id': trajectory.trajectory_id,
                'analyst_id': trajectory.analyst_id,
                'timestamp': trajectory.timestamp.isoformat(),
                'prompt': trajectory.prompt,
                'response': trajectory.model_response,
                'reward': trajectory.reward_score,
                'context': trajectory.context
            }
            
            # 發送到 ART 服務器
            result = await self.client.collect_trajectory(trajectory_data)
            
            self.logger.debug(f"軌跡收集成功: {trajectory.trajectory_id}")
            return result.get('success', False)
            
        except Exception as e:
            self.logger.error(f"軌跡收集失敗: {str(e)}")
            return False
    
    async def start_training(self, analyst_id: str, training_config: Dict[str, Any]) -> str:
        """啟動模型訓練"""
        
        if not self.is_available:
            # 模擬模式
            training_id = f"sim_training_{analyst_id}_{int(datetime.now().timestamp())}"
            self.logger.info(f"模擬訓練啟動: {training_id}")
            return training_id
        
        try:
            # 準備訓練配置
            config = {
                'analyst_id': analyst_id,
                'model_name': training_config.get('model_name', 'qwen2.5-7b-instruct'),
                'training_steps': training_config.get('training_steps', 1000),
                'learning_rate': training_config.get('learning_rate', 1e-5),
                'batch_size': training_config.get('batch_size', 8)
            }
            
            # 啟動訓練
            result = await self.client.start_training(config)
            training_id = result.get('training_id')
            
            self.logger.info(f"ART 訓練啟動: {training_id}")
            return training_id
            
        except Exception as e:
            self.logger.error(f"訓練啟動失敗: {str(e)}")
            return None
    
    async def get_training_status(self, training_id: str) -> Dict[str, Any]:
        """獲取訓練狀態"""
        
        if not self.is_available:
            # 模擬狀態
            return {
                'training_id': training_id,
                'status': 'completed',
                'progress': 1.0,
                'metrics': {
                    'loss': 0.15,
                    'reward': 0.75,
                    'steps': 1000
                }
            }
        
        try:
            result = await self.client.get_training_status(training_id)
            return result
            
        except Exception as e:
            self.logger.error(f"獲取訓練狀態失敗: {str(e)}")
            return {'status': 'error', 'error': str(e)}
    
    def calculate_reward(self, trajectory: TrainingTrajectory) -> float:
        """計算獎勵分數"""
        
        reward = 0.0
        
        # 基礎分數：基於信心度
        confidence_score = trajectory.analysis_result.confidence
        reward += confidence_score * 0.3
        
        # 市場驗證分數
        if trajectory.market_validation is not None:
            reward += trajectory.market_validation * 0.5
        
        # 用戶反饋分數
        if trajectory.user_feedback is not None:
            reward += trajectory.user_feedback * 0.2
        
        # 執行效率懲罰/獎勵
        if trajectory.execution_time_ms > 10000:  # 超過10秒
            reward -= 0.1
        elif trajectory.execution_time_ms < 3000:  # 少於3秒
            reward += 0.1
        
        # 成本效益考量
        if trajectory.cost > 0:
            cost_efficiency = min(1.0, 0.01 / trajectory.cost)  # 成本越低分數越高
            reward += cost_efficiency * 0.1
        
        # 確保獎勵在合理範圍內
        reward = max(-1.0, min(1.0, reward))
        
        return reward


class AnalystsService:
    """分析師服務主類"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化組件
        self.registry = AnalystsServiceRegistry()
        self.art_integration = ARTIntegration(config.get('art', {}))
        
        # 性能指標存儲
        self.performance_metrics: Dict[str, AnalystPerformanceMetrics] = {}
        self.trajectories: List[TrainingTrajectory] = []
        
        # 執行器
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('max_workers', 10),
            thread_name_prefix='AnalystsService'
        )
        
        # 狀態追蹤
        self.active_analyses: Dict[str, asyncio.Task] = {}
        
        self.logger.info("分析師服務初始化完成")
    
    async def initialize(self, discover_paths: List[str] = None):
        """初始化服務"""
        
        # 自動發現分析師
        if discover_paths:
            discovered = self.registry.discover_analysts(discover_paths)
            self.logger.info(f"發現 {discovered} 個分析師")
        
        # 預熱關鍵分析師
        key_analysts = ['fundamentals_analyst', 'technical_analyst', 'risk_analyst']
        for analyst_id in key_analysts:
            instance = self.registry.get_analyst_instance(analyst_id)
            if instance:
                self.logger.info(f"預熱分析師: {analyst_id}")
    
    async def analyze(
        self, 
        analyst_id: str, 
        analysis_state: AnalysisState,
        enable_training: bool = True
    ) -> AnalysisResult:
        """執行分析"""
        
        # 獲取分析師實例
        analyst = self.registry.get_analyst_instance(analyst_id)
        if not analyst:
            raise ValueError(f"未找到分析師: {analyst_id}")
        
        # 創建分析任務
        analysis_id = f"{analyst_id}_{int(datetime.now().timestamp())}"
        
        try:
            # 記錄開始時間
            start_time = datetime.now()
            
            # 執行分析
            result = await analyst.analyze(analysis_state)
            
            # 計算執行時間
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # 更新性能指標
            await self._update_performance_metrics(analyst_id, result, execution_time)
            
            # 收集訓練軌跡
            if enable_training:
                await self._collect_training_trajectory(
                    analyst, analysis_state, result, execution_time
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"分析執行失敗 {analysis_id}: {str(e)}")
            raise
    
    async def analyze_batch(
        self, 
        requests: List[Dict[str, Any]]
    ) -> List[AnalysisResult]:
        """批量分析"""
        
        tasks = []
        for request in requests:
            analyst_id = request['analyst_id']
            analysis_state = request['analysis_state']
            enable_training = request.get('enable_training', True)
            
            task = asyncio.create_task(
                self.analyze(analyst_id, analysis_state, enable_training)
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常結果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # 創建錯誤結果
                request = requests[i]
                error_result = AnalysisResult(
                    analyst_id=request['analyst_id'],
                    stock_id=request['analysis_state'].stock_id,
                    analysis_date=request['analysis_state'].analysis_date,
                    analysis_type=AnalysisType.TECHNICAL,  # 預設類型
                    recommendation='HOLD',
                    confidence=0.0,
                    confidence_level=AnalysisConfidenceLevel.VERY_LOW,
                    reasoning=[f'批量分析失敗: {str(result)}']
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _update_performance_metrics(
        self, 
        analyst_id: str, 
        result: AnalysisResult, 
        execution_time_ms: float
    ):
        """更新性能指標"""
        
        if analyst_id not in self.performance_metrics:
            self.performance_metrics[analyst_id] = AnalystPerformanceMetrics(analyst_id=analyst_id)
        
        metrics = self.performance_metrics[analyst_id]
        
        # 更新基本統計
        metrics.total_analyses += 1
        metrics.last_analysis_time = datetime.now()
        
        # 更新平均值
        total = metrics.total_analyses
        metrics.average_confidence = (
            (metrics.average_confidence * (total - 1) + result.confidence) / total
        )
        metrics.average_response_time = (
            (metrics.average_response_time * (total - 1) + execution_time_ms) / total
        )
        
        # 更新成功率
        is_success = result.confidence > 0.3  # 簡單的成功判斷
        current_success_rate = metrics.success_rate * (total - 1)
        if is_success:
            current_success_rate += 1
        metrics.success_rate = current_success_rate / total
        
        # 更新成本信息
        if result.cost_info:
            cost = result.cost_info.get('estimated_cost', 0.0)
            metrics.total_cost += cost
            metrics.cost_per_analysis = metrics.total_cost / total
    
    async def _collect_training_trajectory(
        self, 
        analyst: BaseAnalyst, 
        analysis_state: AnalysisState, 
        result: AnalysisResult,
        execution_time_ms: float
    ):
        """收集訓練軌跡"""
        
        try:
            # 生成軌跡ID
            trajectory_id = f"traj_{analyst.analyst_id}_{int(datetime.now().timestamp())}"
            
            # 創建軌跡對象
            trajectory = TrainingTrajectory(
                trajectory_id=trajectory_id,
                analyst_id=analyst.analyst_id,
                timestamp=datetime.now(),
                analysis_state=analysis_state,
                prompt=analyst.get_analysis_prompt(analysis_state),
                context=analyst._prepare_analysis_context(analysis_state),
                analysis_result=result,
                model_response={
                    'recommendation': result.recommendation,
                    'confidence': result.confidence,
                    'reasoning': result.reasoning
                },
                execution_time_ms=execution_time_ms,
                cost=result.cost_info.get('estimated_cost', 0.0) if result.cost_info else 0.0
            )
            
            # 計算獎勵分數
            trajectory.reward_score = self.art_integration.calculate_reward(trajectory)
            
            # 收集軌跡
            success = await self.art_integration.collect_trajectory(trajectory)
            
            if success:
                self.trajectories.append(trajectory)
                
                # 限制軌跡數量
                if len(self.trajectories) > 10000:
                    self.trajectories = self.trajectories[-5000:]  # 保留最新的5000條
            
        except Exception as e:
            self.logger.error(f"軌跡收集失敗: {str(e)}")
    
    async def train_analyst(
        self, 
        analyst_id: str, 
        training_config: Dict[str, Any] = None
    ) -> str:
        """訓練分析師"""
        
        if not training_config:
            training_config = {
                'training_steps': 1000,
                'learning_rate': 1e-5,
                'batch_size': 8
            }
        
        # 啟動訓練
        training_id = await self.art_integration.start_training(analyst_id, training_config)
        
        if training_id:
            self.logger.info(f"分析師訓練啟動: {analyst_id} -> {training_id}")
        
        return training_id
    
    async def get_training_status(self, training_id: str) -> Dict[str, Any]:
        """獲取訓練狀態"""
        return await self.art_integration.get_training_status(training_id)
    
    def get_performance_metrics(self, analyst_id: str = None) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """獲取性能指標"""
        
        if analyst_id:
            if analyst_id in self.performance_metrics:
                metrics = self.performance_metrics[analyst_id]
                return {
                    'analyst_id': metrics.analyst_id,
                    'total_analyses': metrics.total_analyses,
                    'accuracy_rate': metrics.accuracy_rate,
                    'average_confidence': metrics.average_confidence,
                    'average_response_time': metrics.average_response_time,
                    'success_rate': metrics.success_rate,
                    'cumulative_reward': metrics.cumulative_reward,
                    'total_cost': metrics.total_cost,
                    'cost_per_analysis': metrics.cost_per_analysis,
                    'last_analysis_time': metrics.last_analysis_time.isoformat() if metrics.last_analysis_time else None
                }
            return None
        else:
            # 返回所有分析師的指標
            all_metrics = []
            for analyst_id, metrics in self.performance_metrics.items():
                all_metrics.append(self.get_performance_metrics(analyst_id))
            return all_metrics
    
    def list_analysts(self) -> List[Dict[str, Any]]:
        """列出所有分析師"""
        return self.registry.list_analysts()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        
        health_status = {
            'service_status': 'healthy',
            'registered_analysts': len(self.registry._analysts),
            'active_analyses': len(self.active_analyses),
            'art_available': self.art_integration.is_available,
            'total_trajectories': len(self.trajectories),
            'timestamp': datetime.now().isoformat()
        }
        
        # 檢查關鍵分析師
        key_analysts = ['fundamentals_analyst', 'technical_analyst', 'risk_analyst']
        analyst_health = {}
        
        for analyst_id in key_analysts:
            instance = self.registry.get_analyst_instance(analyst_id)
            analyst_health[analyst_id] = {
                'available': instance is not None,
                'metrics': self.get_performance_metrics(analyst_id)
            }
        
        health_status['analysts_health'] = analyst_health
        
        return health_status
    
    async def cleanup(self):
        """清理資源"""
        
        # 停止活動分析
        for analysis_id, task in self.active_analyses.items():
            if not task.done():
                task.cancel()
        
        # 關閉執行器
        self.executor.shutdown(wait=True)
        
        self.logger.info("分析師服務清理完成")


# 全局服務實例
_analysts_service: Optional[AnalystsService] = None


def get_analysts_service() -> AnalystsService:
    """獲取全局分析師服務實例"""
    global _analysts_service
    
    if _analysts_service is None:
        # 默認配置
        default_config = {
            'max_workers': 10,
            'art': {
                'art_server_url': 'http://localhost:8000',
                'art_api_key': None
            }
        }
        _analysts_service = AnalystsService(default_config)
    
    return _analysts_service


async def initialize_analysts_service(
    config: Dict[str, Any] = None,
    discover_paths: List[str] = None
) -> AnalystsService:
    """初始化分析師服務"""
    global _analysts_service
    
    if config:
        _analysts_service = AnalystsService(config)
    else:
        _analysts_service = get_analysts_service()
    
    if discover_paths is None:
        # 默認搜索路徑
        discover_paths = [
            str(Path(__file__).parent.parent / 'agents' / 'analysts'),
        ]
    
    await _analysts_service.initialize(discover_paths)
    return _analysts_service


if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_analysts_service():
        print("測試分析師服務")
        
        # 初始化服務
        service = await initialize_analysts_service()
        
        # 健康檢查
        health = await service.health_check()
        print(f"服務健康狀態: {health}")
        
        # 列出分析師
        analysts = service.list_analysts()
        print(f"可用分析師: {len(analysts)}")
        for analyst in analysts:
            print(f"  - {analyst['analyst_id']}: {analyst['available']}")
        
        # 測試分析
        if analysts:
            analyst_id = analysts[0]['analyst_id']
            analysis_state = create_analysis_state(
                stock_id='2330',
                user_context={'user_id': 'test_user'}
            )
            
            try:
                result = await service.analyze(analyst_id, analysis_state)
                print(f"分析結果: {result.recommendation} (信心度: {result.confidence})")
            except Exception as e:
                print(f"分析失敗: {str(e)}")
        
        # 清理
        await service.cleanup()
        print("✅ 測試完成")
    
    asyncio.run(test_analysts_service())