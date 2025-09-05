#!/usr/bin/env python3
"""
TrajectoryCollector - ART軌跡收集器
天工 (TianGong) - 整合BaseAnalyst系統的決策軌跡收集器

此模組提供：
1. 完整的分析師決策軌跡收集功能
2. 與BaseAnalyst系統的無縫整合
3. 推理過程和中間狀態的結構化記錄
4. 支援多種分析師類型的軌跡收集
5. GRPO訓練準備的數據結構
6. 高效能的大量軌跡處理
"""

from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import os
import json
import logging
import asyncio
import hashlib
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from collections import defaultdict
import uuid

# Import existing base classes
try:
    from ..agents.analysts.base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType
    BASE_ANALYST_AVAILABLE = True
except ImportError:
    BASE_ANALYST_AVAILABLE = False
    # Define minimal compatibility classes
    class AnalysisType(Enum):
        TECHNICAL = "technical"
        FUNDAMENTAL = "fundamental"
        NEWS_SENTIMENT = "news_sentiment"
        MARKET_SENTIMENT = "market_sentiment"
        RISK_ASSESSMENT = "risk_assessment"
        INVESTMENT_PLANNING = "investment_planning"
        TAIWAN_SPECIFIC = "taiwan_specific"

class TrajectoryType(Enum):
    """軌跡步驟類型"""
    INITIALIZATION = "initialization"              # 初始化階段
    DATA_COLLECTION = "data_collection"            # 數據收集
    DATA_VALIDATION = "data_validation"            # 數據驗證
    DATA_INTERPRETATION = "data_interpretation"    # 數據解讀
    FINANCIAL_ANALYSIS = "financial_analysis"      # 財務分析
    TECHNICAL_ANALYSIS = "technical_analysis"      # 技術分析
    MARKET_SENTIMENT_ANALYSIS = "market_sentiment_analysis"  # 市場情緒分析
    RISK_ASSESSMENT = "risk_assessment"            # 風險評估
    VALUATION_CALCULATION = "valuation_calculation" # 估值計算
    PEER_COMPARISON = "peer_comparison"            # 同業比較
    REASONING_SYNTHESIS = "reasoning_synthesis"    # 推理綜合
    CONFIDENCE_CALIBRATION = "confidence_calibration" # 信心度校準
    RECOMMENDATION_LOGIC = "recommendation_logic"  # 建議邏輯
    FINAL_VALIDATION = "final_validation"          # 最終驗證
    ERROR_HANDLING = "error_handling"              # 錯誤處理

class TrajectoryStatus(Enum):
    """軌跡狀態"""
    ACTIVE = "active"        # 活躍收集中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 收集失敗
    CANCELLED = "cancelled"  # 已取消

@dataclass
class DecisionStep:
    """決策步驟詳細記錄"""
    step_id: str
    trajectory_id: str
    step_number: int
    timestamp: str
    trajectory_type: TrajectoryType
    
    # 輸入數據
    input_data: Dict[str, Any]
    input_data_hash: str = ""
    
    # 推理過程
    reasoning_process: List[str] = field(default_factory=list)
    reasoning_depth_score: float = 0.0
    
    # 中間結果
    intermediate_result: Any = None
    intermediate_confidence: float = 0.0
    
    # 計算過程
    computation_method: str = "default"
    computation_time_ms: float = 0.0
    model_used: Optional[str] = None
    
    # 數據依賴
    data_dependencies: List[str] = field(default_factory=list)
    external_api_calls: List[str] = field(default_factory=list)
    
    # 質量指標
    confidence_score: float = 0.0
    uncertainty_factors: List[str] = field(default_factory=list)
    validation_checks: Dict[str, bool] = field(default_factory=dict)
    
    # 性能指標
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    
    def __post_init__(self):
        # 計算輸入數據的哈希值
        if not self.input_data_hash:
            self.input_data_hash = self._calculate_data_hash(self.input_data)
        
        # 計算推理深度分數
        if not self.reasoning_depth_score:
            self.reasoning_depth_score = self._calculate_reasoning_depth()
    
    def _calculate_data_hash(self, data: Dict[str, Any]) -> str:
        """計算數據的唯一哈希值"""
        try:
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()[:16]
        except:
            return str(hash(str(data)))[:16]
    
    def _calculate_reasoning_depth(self) -> float:
        """計算推理深度分數"""
        if not self.reasoning_process:
            return 0.0
        
        # 基於推理步驟數量和內容質量計算分數
        step_count = len(self.reasoning_process)
        avg_length = sum(len(step) for step in self.reasoning_process) / step_count
        
        # 標準化分數
        depth_score = min(1.0, (step_count * avg_length) / 500.0)
        return round(depth_score, 3)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = asdict(self)
        result['trajectory_type'] = self.trajectory_type.value
        return result

@dataclass
class TrajectoryMetrics:
    """軌跡質量指標"""
    trajectory_id: str
    
    # 基本指標
    total_steps: int = 0
    total_duration_ms: float = 0.0
    
    # 質量指標
    avg_confidence: float = 0.0
    confidence_consistency: float = 0.0
    reasoning_depth: float = 0.0
    data_utilization_score: float = 0.0
    
    # 效率指標
    avg_step_duration: float = 0.0
    memory_efficiency: float = 0.0
    api_efficiency: float = 0.0
    
    # 完整性指標
    completion_rate: float = 0.0
    error_rate: float = 0.0
    validation_pass_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class AnalysisTrajectory:
    """完整的分析軌跡記錄"""
    trajectory_id: str
    stock_id: str
    analyst_type: str
    analyst_version: str
    user_id: str
    
    # 時間信息
    start_time: str
    end_time: Optional[str] = None
    total_duration_ms: float = 0.0
    
    # 決策步驟
    decision_steps: List[DecisionStep] = field(default_factory=list)
    
    # 最終結果
    final_recommendation: Optional[str] = None
    final_confidence: Optional[float] = None
    final_target_price: Optional[float] = None
    final_reasoning: List[str] = field(default_factory=list)
    
    # 上下文數據
    context_data: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, Any] = field(default_factory=dict)
    market_context: Dict[str, Any] = field(default_factory=dict)
    
    # 系統信息
    system_version: str = "1.0.0"
    model_versions: Dict[str, str] = field(default_factory=dict)
    
    # 軌跡狀態
    status: TrajectoryStatus = TrajectoryStatus.ACTIVE
    error_message: Optional[str] = None
    
    # 質量指標
    metrics: Optional[TrajectoryMetrics] = None
    
    # 版本控制
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_decision_step(self, step: DecisionStep):
        """添加決策步驟"""
        step.step_number = len(self.decision_steps) + 1
        step.trajectory_id = self.trajectory_id
        self.decision_steps.append(step)
        self.updated_at = datetime.now().isoformat()
    
    def complete_trajectory(self, recommendation: str, confidence: float, 
                          target_price: Optional[float] = None, 
                          reasoning: List[str] = None):
        """完成軌跡收集"""
        self.end_time = datetime.now().isoformat()
        self.final_recommendation = recommendation
        self.final_confidence = confidence
        self.final_target_price = target_price
        self.final_reasoning = reasoning or []
        self.status = TrajectoryStatus.COMPLETED
        self.updated_at = datetime.now().isoformat()
        
        # 計算總持續時間
        if self.start_time and self.end_time:
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
            self.total_duration_ms = (end - start).total_seconds() * 1000
        
        # 計算質量指標
        self.metrics = self._calculate_metrics()
    
    def fail_trajectory(self, error_message: str):
        """標記軌跡失敗"""
        self.status = TrajectoryStatus.FAILED
        self.error_message = error_message
        self.end_time = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def _calculate_metrics(self) -> TrajectoryMetrics:
        """計算軌跡質量指標"""
        if not self.decision_steps:
            return TrajectoryMetrics(trajectory_id=self.trajectory_id)
        
        # 基本指標
        total_steps = len(self.decision_steps)
        
        # 質量指標
        confidences = [step.confidence_score for step in self.decision_steps if step.confidence_score > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        confidence_consistency = 1.0 - np.std(confidences) if len(confidences) > 1 else 1.0
        
        reasoning_depths = [step.reasoning_depth_score for step in self.decision_steps]
        avg_reasoning_depth = sum(reasoning_depths) / len(reasoning_depths) if reasoning_depths else 0.0
        
        # 數據利用率
        all_dependencies = set()
        for step in self.decision_steps:
            all_dependencies.update(step.data_dependencies)
        data_utilization_score = min(1.0, len(all_dependencies) / 10.0)  # 假設最多10種數據源
        
        # 效率指標
        durations = [step.computation_time_ms for step in self.decision_steps if step.computation_time_ms > 0]
        avg_step_duration = sum(durations) / len(durations) if durations else 0.0
        
        # 完整性指標
        validation_results = []
        for step in self.decision_steps:
            if step.validation_checks:
                validation_results.extend(step.validation_checks.values())
        validation_pass_rate = sum(validation_results) / len(validation_results) if validation_results else 1.0
        
        return TrajectoryMetrics(
            trajectory_id=self.trajectory_id,
            total_steps=total_steps,
            total_duration_ms=self.total_duration_ms,
            avg_confidence=avg_confidence,
            confidence_consistency=max(0.0, confidence_consistency),
            reasoning_depth=avg_reasoning_depth,
            data_utilization_score=data_utilization_score,
            avg_step_duration=avg_step_duration,
            completion_rate=1.0 if self.status == TrajectoryStatus.COMPLETED else 0.0,
            validation_pass_rate=validation_pass_rate
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = asdict(self)
        result['status'] = self.status.value
        result['decision_steps'] = [step.to_dict() for step in self.decision_steps]
        if self.metrics:
            result['metrics'] = self.metrics.to_dict()
        return result
    
    def get_grpo_training_data(self) -> Dict[str, Any]:
        """獲取GRPO訓練用的數據格式"""
        return {
            'trajectory_id': self.trajectory_id,
            'stock_id': self.stock_id,
            'analyst_type': self.analyst_type,
            'user_id': self.user_id,
            'steps': [
                {
                    'step_number': step.step_number,
                    'input': step.input_data,
                    'reasoning': step.reasoning_process,
                    'output': step.intermediate_result,
                    'confidence': step.confidence_score,
                    'method': step.computation_method
                }
                for step in self.decision_steps
            ],
            'final_output': {
                'recommendation': self.final_recommendation,
                'confidence': self.final_confidence,
                'target_price': self.final_target_price,
                'reasoning': self.final_reasoning
            },
            'context': {
                'user_context': self.user_context,
                'market_context': self.market_context
            },
            'quality_metrics': self.metrics.to_dict() if self.metrics else {}
        }

class TrajectoryCollector:
    """ART軌跡收集器 - 生產級實現"""
    
    def __init__(self, 
                 storage_path: str = None,
                 max_active_trajectories: int = 1000,
                 auto_save_interval: int = 300,
                 enable_performance_monitoring: bool = True):
        
        # 存儲配置
        self.storage_path = Path(storage_path) if storage_path else Path("./art_data/trajectories")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 軌跡管理
        self.active_trajectories: Dict[str, AnalysisTrajectory] = {}
        self.completed_trajectories: Dict[str, AnalysisTrajectory] = {}
        self.max_active_trajectories = max_active_trajectories
        
        # 性能監控
        self.enable_performance_monitoring = enable_performance_monitoring
        self.performance_stats = {
            'total_trajectories_created': 0,
            'total_trajectories_completed': 0,
            'total_steps_recorded': 0,
            'avg_trajectory_duration': 0.0,
            'memory_usage_mb': 0.0
        }
        
        # 配置
        self.config = {
            'min_trajectory_length': 3,
            'max_step_reasoning_length': 1000,
            'auto_save_interval': auto_save_interval,
            'compression_enabled': True,
            'versioning_enabled': True
        }
        
        # 日誌記錄
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
        # 線程池
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ART-Collector")
        
        # 自動保存
        self._last_save_time = datetime.now()
        self._auto_save_task = None
        
        # 統計信息
        self.collection_stats = defaultdict(int)
        self._stats_lock = threading.Lock()
        
        self.logger.info(f"TrajectoryCollector initialized with storage: {self.storage_path}")
    
    def _setup_logging(self):
        """設置專用日誌記錄"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - ART-TrajectoryCollector - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def start_trajectory(self, 
                              stock_id: str,
                              analyst: 'BaseAnalyst',
                              user_context: Dict[str, Any] = None,
                              market_context: Dict[str, Any] = None,
                              additional_context: Dict[str, Any] = None) -> str:
        """開始軌跡收集 - 與BaseAnalyst整合"""
        
        # 檢查活躍軌跡限制
        if len(self.active_trajectories) >= self.max_active_trajectories:
            await self._cleanup_old_trajectories()
        
        # 生成軌跡ID
        trajectory_id = self._generate_trajectory_id(stock_id, analyst, user_context)
        
        # 獲取分析師信息
        analyst_info = analyst.get_analyst_info() if hasattr(analyst, 'get_analyst_info') else {}
        analyst_type = getattr(analyst, 'analyst_id', analyst.__class__.__name__)
        analyst_version = analyst_info.get('version', '1.0.0')
        
        # 創建軌跡記錄
        trajectory = AnalysisTrajectory(
            trajectory_id=trajectory_id,
            stock_id=stock_id,
            analyst_type=analyst_type,
            analyst_version=analyst_version,
            user_id=user_context.get('user_id', 'anonymous') if user_context else 'anonymous',
            start_time=datetime.now().isoformat(),
            user_context=user_context or {},
            market_context=market_context or {},
            context_data=additional_context or {},
            model_versions=analyst_info.get('model_versions', {})
        )
        
        # 添加到活躍軌跡
        self.active_trajectories[trajectory_id] = trajectory
        
        # 更新統計
        with self._stats_lock:
            self.collection_stats['trajectories_started'] += 1
            self.performance_stats['total_trajectories_created'] += 1
        
        self.logger.info(f"Started trajectory collection: {trajectory_id} for {analyst_type} on {stock_id}")
        return trajectory_id
    
    def _generate_trajectory_id(self, stock_id: str, analyst: Any, user_context: Dict[str, Any] = None) -> str:
        """生成唯一的軌跡ID"""
        user_id = user_context.get('user_id', 'anonymous') if user_context else 'anonymous'
        analyst_type = getattr(analyst, 'analyst_id', analyst.__class__.__name__)
        timestamp = str(int(datetime.now().timestamp() * 1000))  # 毫秒級時間戳
        unique_suffix = str(uuid.uuid4())[:8]
        
        return f"{analyst_type}_{stock_id}_{user_id}_{timestamp}_{unique_suffix}"
    
    async def record_step(self,
                         trajectory_id: str,
                         trajectory_type: TrajectoryType,
                         input_data: Dict[str, Any],
                         reasoning_process: List[str],
                         intermediate_result: Any = None,
                         confidence_score: float = 0.0,
                         computation_method: str = "default",
                         model_used: Optional[str] = None,
                         computation_time_ms: float = 0.0,
                         uncertainty_factors: List[str] = None,
                         validation_checks: Dict[str, bool] = None) -> str:
        """記錄決策步驟 - 增強版本"""
        
        if trajectory_id not in self.active_trajectories:
            raise ValueError(f"Trajectory not found or not active: {trajectory_id}")
        
        trajectory = self.active_trajectories[trajectory_id]
        
        # 生成步驟ID
        step_id = f"{trajectory_id}_step_{len(trajectory.decision_steps) + 1}"
        
        # 性能監控
        memory_usage = 0.0
        cpu_usage = 0.0
        if self.enable_performance_monitoring:
            try:
                import psutil
                process = psutil.Process()
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                cpu_usage = process.cpu_percent()
            except ImportError:
                pass
        
        # 分析數據依賴
        data_dependencies = self._analyze_data_dependencies(input_data)
        external_api_calls = self._extract_api_calls(input_data)
        
        # 創建決策步驟
        step = DecisionStep(
            step_id=step_id,
            trajectory_id=trajectory_id,
            step_number=len(trajectory.decision_steps) + 1,
            timestamp=datetime.now().isoformat(),
            trajectory_type=trajectory_type,
            input_data=input_data,
            reasoning_process=reasoning_process[:self.config['max_step_reasoning_length']],  # 限制長度
            intermediate_result=intermediate_result,
            intermediate_confidence=confidence_score,
            computation_method=computation_method,
            model_used=model_used,
            computation_time_ms=computation_time_ms,
            data_dependencies=data_dependencies,
            external_api_calls=external_api_calls,
            confidence_score=confidence_score,
            uncertainty_factors=uncertainty_factors or [],
            validation_checks=validation_checks or {},
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
        
        # 添加到軌跡
        trajectory.add_decision_step(step)
        
        # 更新統計
        with self._stats_lock:
            self.collection_stats['steps_recorded'] += 1
            self.performance_stats['total_steps_recorded'] += 1
        
        self.logger.debug(f"Recorded step: {step_id} ({trajectory_type.value})")
        return step_id
    
    def _analyze_data_dependencies(self, input_data: Dict[str, Any]) -> List[str]:
        """分析數據依賴關係"""
        dependencies = []
        
        # 檢查常見數據類型
        dependency_mapping = {
            'stock_price': 'market_data',
            'financial_data': 'financial_statements',
            'income_statement': 'financial_statements',
            'balance_sheet': 'financial_statements',
            'cash_flow': 'financial_statements',
            'news_data': 'news_sources',
            'sentiment_data': 'sentiment_analysis',
            'technical_indicators': 'technical_analysis',
            'sector_comparison': 'industry_data',
            'peer_analysis': 'industry_data',
            'market_data': 'market_data',
            'macro_data': 'macroeconomic_data',
            'taiwan_institutional_data': 'institutional_data',
            'taiwan_market_conditions': 'taiwan_market_data'
        }
        
        for key in input_data.keys():
            for pattern, dependency in dependency_mapping.items():
                if pattern in key.lower():
                    if dependency not in dependencies:
                        dependencies.append(dependency)
                    break
        
        return dependencies
    
    def _extract_api_calls(self, input_data: Dict[str, Any]) -> List[str]:
        """提取API調用記錄"""
        api_calls = []
        
        # 檢查數據來源標記
        if isinstance(input_data, dict):
            if input_data.get('source') == 'finmind_api':
                api_calls.append('FinMind API')
            elif input_data.get('source') == 'finnhub_api':
                api_calls.append('Finnhub API')
            elif 'api_source' in input_data:
                api_calls.append(input_data['api_source'])
        
        return api_calls
    
    async def complete_trajectory(self,
                                trajectory_id: str,
                                final_recommendation: str,
                                final_confidence: float,
                                final_target_price: Optional[float] = None,
                                final_reasoning: List[str] = None) -> AnalysisTrajectory:
        """完成軌跡收集"""
        
        if trajectory_id not in self.active_trajectories:
            raise ValueError(f"Active trajectory not found: {trajectory_id}")
        
        trajectory = self.active_trajectories[trajectory_id]
        
        # 完成軌跡
        trajectory.complete_trajectory(
            recommendation=final_recommendation,
            confidence=final_confidence,
            target_price=final_target_price,
            reasoning=final_reasoning
        )
        
        # 移動到完成軌跡
        self.completed_trajectories[trajectory_id] = trajectory
        del self.active_trajectories[trajectory_id]
        
        # 保存軌跡
        await self._save_trajectory(trajectory)
        
        # 更新統計
        with self._stats_lock:
            self.collection_stats['trajectories_completed'] += 1
            self.performance_stats['total_trajectories_completed'] += 1
        
        self.logger.info(f"Completed trajectory: {trajectory_id}")
        return trajectory
    
    async def fail_trajectory(self, trajectory_id: str, error_message: str) -> AnalysisTrajectory:
        """標記軌跡失敗"""
        
        if trajectory_id not in self.active_trajectories:
            raise ValueError(f"Active trajectory not found: {trajectory_id}")
        
        trajectory = self.active_trajectories[trajectory_id]
        trajectory.fail_trajectory(error_message)
        
        # 移動到完成軌跡（失敗也算完成）
        self.completed_trajectories[trajectory_id] = trajectory
        del self.active_trajectories[trajectory_id]
        
        # 保存軌跡
        await self._save_trajectory(trajectory)
        
        # 更新統計
        with self._stats_lock:
            self.collection_stats['trajectories_failed'] += 1
        
        self.logger.warning(f"Failed trajectory: {trajectory_id} - {error_message}")
        return trajectory
    
    async def get_trajectory(self, trajectory_id: str) -> Optional[AnalysisTrajectory]:
        """獲取軌跡記錄"""
        
        # 首先檢查活躍軌跡
        if trajectory_id in self.active_trajectories:
            return self.active_trajectories[trajectory_id]
        
        # 然後檢查完成軌跡
        if trajectory_id in self.completed_trajectories:
            return self.completed_trajectories[trajectory_id]
        
        # 最後嘗試從存儲加載
        try:
            trajectory = await self._load_trajectory(trajectory_id)
            if trajectory:
                self.completed_trajectories[trajectory_id] = trajectory
            return trajectory
        except Exception as e:
            self.logger.error(f"Failed to load trajectory {trajectory_id}: {e}")
            return None
    
    async def get_user_trajectories(self, 
                                  user_id: str,
                                  limit: int = 100,
                                  analyst_type: Optional[str] = None,
                                  status: Optional[TrajectoryStatus] = None) -> List[AnalysisTrajectory]:
        """獲取用戶的軌跡記錄"""
        
        trajectories = []
        
        # 搜尋完成軌跡
        for trajectory in self.completed_trajectories.values():
            if trajectory.user_id == user_id:
                if analyst_type and trajectory.analyst_type != analyst_type:
                    continue
                if status and trajectory.status != status:
                    continue
                trajectories.append(trajectory)
        
        # 搜尋活躍軌跡
        for trajectory in self.active_trajectories.values():
            if trajectory.user_id == user_id:
                if analyst_type and trajectory.analyst_type != analyst_type:
                    continue
                if status and trajectory.status != status:
                    continue
                trajectories.append(trajectory)
        
        # 按時間排序並限制數量
        trajectories.sort(key=lambda x: x.start_time, reverse=True)
        return trajectories[:limit]
    
    async def get_grpo_training_data(self, 
                                   user_id: str,
                                   min_quality_score: float = 0.5,
                                   limit: int = 500) -> List[Dict[str, Any]]:
        """獲取GRPO訓練數據"""
        
        user_trajectories = await self.get_user_trajectories(
            user_id=user_id,
            status=TrajectoryStatus.COMPLETED,
            limit=limit * 2  # 獲取更多以便過濾
        )
        
        training_data = []
        for trajectory in user_trajectories:
            # 檢查軌跡質量
            if trajectory.metrics and self._calculate_trajectory_quality_score(trajectory.metrics) >= min_quality_score:
                # 檢查最小步驟數
                if len(trajectory.decision_steps) >= self.config['min_trajectory_length']:
                    training_data.append(trajectory.get_grpo_training_data())
        
        return training_data[:limit]
    
    def _calculate_trajectory_quality_score(self, metrics: TrajectoryMetrics) -> float:
        """計算軌跡綜合質量分數"""
        weights = {
            'avg_confidence': 0.3,
            'confidence_consistency': 0.2,
            'reasoning_depth': 0.2,
            'data_utilization_score': 0.15,
            'completion_rate': 0.1,
            'validation_pass_rate': 0.05
        }
        
        score = 0.0
        for metric, weight in weights.items():
            score += getattr(metrics, metric, 0.0) * weight
        
        return min(1.0, score)
    
    async def _save_trajectory(self, trajectory: AnalysisTrajectory):
        """保存軌跡到存儲"""
        try:
            trajectory_file = self.storage_path / f"trajectory_{trajectory.trajectory_id}.json"
            
            # 使用線程池進行異步保存
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.thread_pool,
                self._sync_save_trajectory,
                trajectory_file,
                trajectory.to_dict()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save trajectory {trajectory.trajectory_id}: {e}")
    
    def _sync_save_trajectory(self, file_path: Path, trajectory_data: Dict[str, Any]):
        """同步保存軌跡數據"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(trajectory_data, f, ensure_ascii=False, indent=2)
    
    async def _load_trajectory(self, trajectory_id: str) -> Optional[AnalysisTrajectory]:
        """從存儲加載軌跡"""
        try:
            trajectory_file = self.storage_path / f"trajectory_{trajectory_id}.json"
            if not trajectory_file.exists():
                return None
            
            # 使用線程池進行異步加載
            loop = asyncio.get_event_loop()
            trajectory_data = await loop.run_in_executor(
                self.thread_pool,
                self._sync_load_trajectory,
                trajectory_file
            )
            
            if trajectory_data:
                return self._deserialize_trajectory(trajectory_data)
            
        except Exception as e:
            self.logger.error(f"Failed to load trajectory {trajectory_id}: {e}")
        
        return None
    
    def _sync_load_trajectory(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """同步加載軌跡數據"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    
    def _deserialize_trajectory(self, data: Dict[str, Any]) -> AnalysisTrajectory:
        """反序列化軌跡數據"""
        # 重建決策步驟
        decision_steps = []
        for step_data in data.get('decision_steps', []):
            step = DecisionStep(
                step_id=step_data['step_id'],
                trajectory_id=step_data['trajectory_id'],
                step_number=step_data['step_number'],
                timestamp=step_data['timestamp'],
                trajectory_type=TrajectoryType(step_data['trajectory_type']),
                input_data=step_data['input_data'],
                reasoning_process=step_data['reasoning_process'],
                intermediate_result=step_data.get('intermediate_result'),
                confidence_score=step_data['confidence_score'],
                computation_method=step_data['computation_method'],
                data_dependencies=step_data.get('data_dependencies', []),
                model_used=step_data.get('model_used')
            )
            decision_steps.append(step)
        
        # 重建軌跡
        trajectory = AnalysisTrajectory(
            trajectory_id=data['trajectory_id'],
            stock_id=data['stock_id'],
            analyst_type=data['analyst_type'],
            analyst_version=data.get('analyst_version', '1.0.0'),
            user_id=data['user_id'],
            start_time=data['start_time'],
            end_time=data.get('end_time'),
            decision_steps=decision_steps,
            final_recommendation=data.get('final_recommendation'),
            final_confidence=data.get('final_confidence'),
            final_target_price=data.get('final_target_price'),
            final_reasoning=data.get('final_reasoning', []),
            context_data=data.get('context_data', {}),
            user_context=data.get('user_context', {}),
            market_context=data.get('market_context', {}),
            status=TrajectoryStatus(data.get('status', 'completed'))
        )
        
        # 重建質量指標
        if data.get('metrics'):
            metrics_data = data['metrics']
            trajectory.metrics = TrajectoryMetrics(
                trajectory_id=metrics_data['trajectory_id'],
                total_steps=metrics_data.get('total_steps', 0),
                total_duration_ms=metrics_data.get('total_duration_ms', 0.0),
                avg_confidence=metrics_data.get('avg_confidence', 0.0),
                confidence_consistency=metrics_data.get('confidence_consistency', 0.0),
                reasoning_depth=metrics_data.get('reasoning_depth', 0.0),
                data_utilization_score=metrics_data.get('data_utilization_score', 0.0),
                completion_rate=metrics_data.get('completion_rate', 0.0),
                validation_pass_rate=metrics_data.get('validation_pass_rate', 0.0)
            )
        
        return trajectory
    
    async def _cleanup_old_trajectories(self):
        """清理舊的活躍軌跡"""
        current_time = datetime.now()
        trajectories_to_remove = []
        
        for trajectory_id, trajectory in self.active_trajectories.items():
            start_time = datetime.fromisoformat(trajectory.start_time)
            if (current_time - start_time) > timedelta(hours=24):  # 超過24小時的活躍軌跡
                trajectories_to_remove.append(trajectory_id)
        
        for trajectory_id in trajectories_to_remove:
            await self.fail_trajectory(trajectory_id, "Trajectory timeout - auto cleanup")
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """獲取收集統計信息"""
        with self._stats_lock:
            stats = self.collection_stats.copy()
            stats.update(self.performance_stats)
        
        stats.update({
            'active_trajectories': len(self.active_trajectories),
            'completed_trajectories': len(self.completed_trajectories),
            'storage_path': str(self.storage_path),
            'system_status': 'active'
        })
        
        return stats
    
    async def cleanup(self):
        """清理資源"""
        # 保存所有活躍軌跡
        for trajectory_id in list(self.active_trajectories.keys()):
            await self.fail_trajectory(trajectory_id, "System shutdown")
        
        # 關閉線程池
        self.thread_pool.shutdown(wait=True)
        
        self.logger.info("TrajectoryCollector cleanup completed")

# 工廠函數和便利函數
async def create_trajectory_collector(
    storage_path: str = None,
    max_active_trajectories: int = 1000,
    auto_save_interval: int = 300,
    enable_performance_monitoring: bool = True
) -> TrajectoryCollector:
    """創建軌跡收集器實例"""
    
    collector = TrajectoryCollector(
        storage_path=storage_path,
        max_active_trajectories=max_active_trajectories,
        auto_save_interval=auto_save_interval,
        enable_performance_monitoring=enable_performance_monitoring
    )
    
    return collector

async def create_trajectory_collector_with_base_analyst_integration() -> TrajectoryCollector:
    """創建與BaseAnalyst完全整合的軌跡收集器"""
    
    if not BASE_ANALYST_AVAILABLE:
        raise RuntimeError("BaseAnalyst not available. Cannot create integrated trajectory collector.")
    
    # 使用優化設置
    collector = TrajectoryCollector(
        storage_path="./art_data/trajectories",
        max_active_trajectories=2000,  # 更大的容量
        auto_save_interval=180,        # 更頻繁的自動保存
        enable_performance_monitoring=True
    )
    
    return collector


# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_trajectory_collector():
        print("🚀 測試TrajectoryCollector")
        
        # 創建收集器
        collector = await create_trajectory_collector("./test_trajectories")
        
        # 模擬分析師
        class MockAnalyst:
            analyst_id = "test_analyst"
            
            def get_analyst_info(self):
                return {'version': '1.0.0', 'type': 'fundamental'}
        
        analyst = MockAnalyst()
        
        # 開始軌跡
        trajectory_id = await collector.start_trajectory(
            stock_id="2330",
            analyst=analyst,
            user_context={'user_id': 'test_user', 'membership_tier': 'GOLD'}
        )
        
        print(f"📊 開始軌跡: {trajectory_id}")
        
        # 記錄步驟
        await collector.record_step(
            trajectory_id=trajectory_id,
            trajectory_type=TrajectoryType.DATA_COLLECTION,
            input_data={'stock_price': 580, 'pe_ratio': 22.5},
            reasoning_process=['收集股價數據', '分析本益比'],
            intermediate_result={'data_quality': 'good'},
            confidence_score=0.9,
            computation_time_ms=150.0
        )
        
        await collector.record_step(
            trajectory_id=trajectory_id,
            trajectory_type=TrajectoryType.RECOMMENDATION_LOGIC,
            input_data={'financial_score': 8.5, 'technical_score': 7.2},
            reasoning_process=['綜合財務指標', '考慮技術面', '給出建議'],
            intermediate_result={'recommendation': 'BUY'},
            confidence_score=0.85,
            computation_time_ms=300.0
        )
        
        # 完成軌跡
        completed_trajectory = await collector.complete_trajectory(
            trajectory_id=trajectory_id,
            final_recommendation='BUY',
            final_confidence=0.87,
            final_target_price=650.0,
            final_reasoning=['財務指標優異', '技術面支撐', '建議買入']
        )
        
        print(f"✅ 完成軌跡，質量分數: {collector._calculate_trajectory_quality_score(completed_trajectory.metrics):.3f}")
        
        # 獲取統計
        stats = collector.get_collection_statistics()
        print(f"📈 統計信息: {stats}")
        
        # 獲取GRPO數據
        grpo_data = await collector.get_grpo_training_data('test_user')
        print(f"🎯 GRPO訓練數據: {len(grpo_data)} 條記錄")
        
        # 清理
        await collector.cleanup()
        
        print("✅ TrajectoryCollector測試完成")
    
    asyncio.run(test_trajectory_collector())