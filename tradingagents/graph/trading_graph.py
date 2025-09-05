#!/usr/bin/env python3
"""
TradingAgentsGraph - 交易代理人工作流引擎
天工 (TianGong) - 多代理人協作的智能分析系統核心

此工作流引擎協調多個專業分析師，實現：
1. 並行數據收集和初步分析
2. 多階段專業分析師執行
3. 結果辯論和共識建立
4. 最終投資決策整合
5. 即時狀態推送和監控
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import time
from collections import defaultdict

from ..agents.analysts.base_analyst import BaseAnalyst, AnalysisResult, AnalysisState, AnalysisType
from ..agents.analysts.workflow_orchestrator import WorkflowOrchestrator, ExecutionStrategy, get_global_orchestrator
from ..utils.user_context import UserContext
from ..dataflows.data_orchestrator import DataOrchestrator, DataRequest, DataType, DataSource
from ..utils.error_handler import handle_error, get_user_friendly_message
from ..utils.logging_config import get_analysis_logger
from ..utils.performance_monitor import log_performance
from ..default_config import DEFAULT_CONFIG
from .production_optimizations import ProductionOptimizer, create_production_optimizer, optimize_for_production
from ..routing.ai_task_router import AITaskRouter, RoutingDecisionRequest, RoutingStrategy
from ..database.task_metadata_db import TaskMetadataDB
from ..database.model_capability_db import ModelCapabilityDB

class AnalysisPhase(Enum):
    """分析階段"""
    INITIALIZATION = "initialization"           # 初始化階段
    DATA_COLLECTION = "data_collection"         # 數據收集階段
    PARALLEL_ANALYSIS = "parallel_analysis"     # 並行分析階段
    DEBATE_CONSENSUS = "debate_consensus"       # 辯論共識階段
    FINAL_INTEGRATION = "final_integration"     # 最終整合階段
    COMPLETED = "completed"                     # 完成階段
    ERROR = "error"                            # 錯誤階段

class AnalysisStatus(Enum):
    """分析狀態"""
    PENDING = "pending"                         # 等待中
    RUNNING = "running"                         # 執行中
    COMPLETED = "completed"                     # 已完成
    FAILED = "failed"                          # 失敗
    CANCELLED = "cancelled"                     # 已取消

@dataclass
class AnalysistExecution:
    """分析師執行狀態"""
    analyst_id: str
    analyst_type: AnalysisType
    status: AnalysisStatus = AnalysisStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        result_dict = asdict(self)
        result_dict['analyst_type'] = self.analyst_type.value
        result_dict['status'] = self.status.value
        if self.start_time:
            result_dict['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result_dict['end_time'] = self.end_time.isoformat()
        if self.result:
            result_dict['result'] = {
                'recommendation': self.result.recommendation,
                'confidence': self.result.confidence,
                'target_price': self.result.target_price,
                'reasoning': self.result.reasoning,
                'risk_factors': self.result.risk_factors
            }
        return result_dict

@dataclass
class WorkflowState:
    """工作流狀態"""
    session_id: str
    stock_id: str
    user_context: UserContext
    current_phase: AnalysisPhase = AnalysisPhase.INITIALIZATION
    overall_status: AnalysisStatus = AnalysisStatus.PENDING
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    progress_percentage: float = 0.0
    
    # 數據收集結果
    collected_data: Dict[str, Any] = field(default_factory=dict)
    data_collection_errors: List[str] = field(default_factory=list)
    
    # 分析師執行狀態
    analyst_executions: Dict[str, AnalysistExecution] = field(default_factory=dict)
    
    # 辯論和共識
    debate_rounds: List[Dict[str, Any]] = field(default_factory=list)
    consensus_result: Optional[Dict[str, Any]] = None
    
    # 最終結果
    final_result: Optional[AnalysisResult] = None
    integration_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 錯誤和監控
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str):
        """添加錯誤"""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")
    
    def add_warning(self, warning: str):
        """添加警告"""
        self.warnings.append(f"[{datetime.now().isoformat()}] {warning}")
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        result = asdict(self)
        result['current_phase'] = self.current_phase.value
        result['overall_status'] = self.overall_status.value
        result['start_time'] = self.start_time.isoformat()
        if self.end_time:
            result['end_time'] = self.end_time.isoformat()
        if self.user_context:
            result['user_context'] = {
                'user_id': self.user_context.user_id,
                'membership_tier': self.user_context.membership_tier.value,
                'permissions': asdict(self.user_context.permissions)
            }
        
        # 轉換分析師執行狀態
        result['analyst_executions'] = {
            analyst_id: execution.to_dict() 
            for analyst_id, execution in self.analyst_executions.items()
        }
        
        # 處理最終結果
        if self.final_result:
            result['final_result'] = {
                'analyst_id': self.final_result.analyst_id,
                'recommendation': self.final_result.recommendation,
                'confidence': self.final_result.confidence,
                'target_price': self.final_result.target_price,
                'reasoning': self.final_result.reasoning,
                'risk_factors': self.final_result.risk_factors,
                'timestamp': self.final_result.timestamp
            }
        
        return result

class TradingAgentsGraph:
    """交易代理人工作流引擎"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工作流引擎
        
        Args:
            config: 配置參數
        """
        self.config = config or DEFAULT_CONFIG
        self.logger = get_analysis_logger("trading_graph")
        
        # 工作流配置 (必須先設定)
        self.workflow_config = self.config.get('workflow', {
            'max_concurrent_sessions': 10,
            'session_timeout': 1800,  # 30分鐘
            'enable_debate': True,
            'min_consensus_threshold': 0.6,
            'max_debate_rounds': 3,
            'max_parallelism': 4,
            'enable_conflict_resolution': True,
            'retry_attempts': 2,
            'enable_intelligent_routing': True  # 默认启用智能路由
        })
        
        # 初始化組件
        self.data_orchestrator = None
        self.analysts = {}
        self.active_sessions = {}
        
        # GPT-OSS智能路由系统 (新增)
        self.ai_task_router = None
        self.enable_intelligent_routing = self.workflow_config.get('enable_intelligent_routing', True)
        self.routing_transparency = self.config.get('routing_transparency', {
            'enabled': True,
            'include_decision_details': True,
            'log_routing_decisions': True
        })
        
        # 工作流編排器
        self.workflow_orchestrator = WorkflowOrchestrator({
            'max_parallelism': self.workflow_config.get('max_parallelism', 4),
            'execution_timeout': self.workflow_config.get('session_timeout', 1800),
            'conflict_resolution_enabled': self.workflow_config.get('enable_conflict_resolution', True),
            'retry_attempts': self.workflow_config.get('retry_attempts', 2)
        })
        
        # 狀態推送回調
        self.status_callbacks: List[Callable] = []
        
        # 性能監控
        self.session_metrics = defaultdict(dict)
        
        # 生產環境優化器
        self.production_optimizer = None
        self.enable_production_optimization = self.config.get('enable_production_optimization', True)
        
        if self.enable_production_optimization:
            self.production_optimizer = create_production_optimizer(
                self.config.get('production_optimization', {})
            )
        
        self.logger.info("TradingAgentsGraph 工作流引擎初始化完成", extra={
            'production_optimization_enabled': self.enable_production_optimization,
            'intelligent_routing_enabled': self.enable_intelligent_routing,
            'max_concurrent_sessions': self.workflow_config['max_concurrent_sessions']
        })
    
    async def initialize(self):
        """異步初始化"""
        try:
            # 初始化數據編排器
            self.data_orchestrator = DataOrchestrator(self.config.get('data_orchestrator', {}))
            await self.data_orchestrator.initialize()
            
            # 初始化智能路由器 (GPT-OSS整合)
            if self.enable_intelligent_routing:
                await self._initialize_intelligent_routing()
            
            # 初始化分析師
            await self._initialize_analysts()
            
            # 啟動生產環境優化器
            if self.production_optimizer:
                await self.production_optimizer.start()
                self.logger.info("生產環境優化器已啟動")
            
            self.logger.info("工作流引擎異步初始化完成", extra={
                'analysts_count': len(self.analysts),
                'production_optimizer_running': self.production_optimizer is not None,
                'intelligent_routing_active': self.ai_task_router is not None
            })
            
        except Exception as e:
            self.logger.error(f"工作流引擎初始化失敗: {str(e)}")
            raise
    
    async def _initialize_intelligent_routing(self):
        """初始化智能路由器"""
        try:
            self.logger.info("🚀 初始化GPT-OSS智能路由器...")
            
            # 获取路由器配置
            router_config = self.config.get('ai_task_router', {})
            
            # 初始化数据库组件
            task_db = TaskMetadataDB()
            model_db = ModelCapabilityDB() 
            
            # 获取性能监控器（如果可用）
            performance_monitor = None
            if hasattr(self, 'production_optimizer') and self.production_optimizer:
                performance_monitor = getattr(self.production_optimizer, 'performance_monitor', None)
            
            # 创建路由器实例
            self.ai_task_router = AITaskRouter(
                task_db=task_db,
                model_db=model_db,
                performance_monitor=performance_monitor,
                config=router_config
            )
            
            # 初始化路由器
            router_ready = await self.ai_task_router.initialize()
            
            if router_ready:
                self.logger.info("✅ GPT-OSS智能路由器初始化成功")
                
                # 记录路由器状态
                if self.routing_transparency.get('log_routing_decisions', True):
                    router_stats = self.ai_task_router.get_routing_statistics()
                    self.logger.info("📊 路由器统计", extra={'router_stats': router_stats})
            else:
                self.logger.warning("⚠️ 智能路由器初始化失败，将使用传统路由")
                self.ai_task_router = None
                self.enable_intelligent_routing = False
            
        except Exception as e:
            self.logger.error(f"❌ 智能路由器初始化失败: {str(e)}")
            self.ai_task_router = None
            self.enable_intelligent_routing = False
            # 不抛出异常，允许系统继续使用传统路由
    
    async def _initialize_analysts(self):
        """初始化所有分析師"""
        analyst_configs = self.config.get('analysts_config', {})
        
        # 動態導入和初始化分析師
        try:
            # 台股市場分析師
            from ..agents.analysts.taiwan_market_analyst import TaiwanMarketAnalyst
            self.analysts['taiwan_market_analyst'] = TaiwanMarketAnalyst(
                analyst_configs.get('taiwan_market_analyst', {})
            )
            
            # 風險分析師
            from ..agents.analysts.risk_analyst import RiskAnalyst
            self.analysts['risk_analyst'] = RiskAnalyst(
                analyst_configs.get('risk_analyst', {})
            )
            
            # 投資規劃師
            from ..agents.analysts.investment_planner import InvestmentPlanner
            self.analysts['investment_planner'] = InvestmentPlanner(
                analyst_configs.get('investment_planner', {})
            )
            
            # 基本面分析師 (如果存在)
            try:
                from ..agents.analysts.fundamentals_analyst import FundamentalsAnalyst
                self.analysts['fundamentals_analyst'] = FundamentalsAnalyst(
                    analyst_configs.get('fundamentals_analyst', {})
                )
            except ImportError:
                self.logger.warning("基本面分析師未實現，跳過初始化")
            
            # 新聞分析師 (如果存在)
            try:
                from ..agents.analysts.news_analyst import NewsAnalyst
                self.analysts['news_analyst'] = NewsAnalyst(
                    analyst_configs.get('news_analyst', {})
                )
            except ImportError:
                self.logger.warning("新聞分析師未實現，跳過初始化")
            
            # 情緒分析師 (如果存在)
            try:
                from ..agents.analysts.sentiment_analyst import SentimentAnalyst
                self.analysts['sentiment_analyst'] = SentimentAnalyst(
                    analyst_configs.get('sentiment_analyst', {})
                )
            except ImportError:
                self.logger.warning("情緒分析師未實現，跳過初始化")
            
            # 將分析師註冊到工作流編排器
            for analyst_id, analyst in self.analysts.items():
                self.workflow_orchestrator.register_analyst(analyst)
                
                # 为分析师注入智能路由器（如果可用）
                if self.ai_task_router and hasattr(analyst, '_initialize_intelligent_routing_client'):
                    try:
                        await analyst._initialize_intelligent_routing_client(self.ai_task_router)
                        self.logger.debug(f"✅ 分析师 {analyst_id} 已连接智能路由器")
                    except Exception as e:
                        self.logger.warning(f"⚠️ 分析师 {analyst_id} 智能路由连接失败: {e}")
            
            self.logger.info(f"成功初始化 {len(self.analysts)} 個分析師，已註冊到工作流編排器", extra={
                'intelligent_routing_injected': self.ai_task_router is not None,
                'analysts': list(self.analysts.keys())
            })
            
        except Exception as e:
            self.logger.error(f"分析師初始化失敗: {str(e)}")
            raise
    
    def add_status_callback(self, callback: Callable[[WorkflowState], None]):
        """添加狀態推送回調"""
        self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable[[WorkflowState], None]):
        """移除狀態推送回調"""
        if callback in self.status_callbacks:
            self.status_callbacks.remove(callback)
    
    async def _notify_status_change(self, state: WorkflowState):
        """通知狀態變化"""
        for callback in self.status_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(state)
                else:
                    callback(state)
            except Exception as e:
                self.logger.error(f"狀態推送回調失敗: {str(e)}")
    
    @optimize_for_production
    @log_performance()
    async def analyze_stock(
        self,
        stock_id: str,
        user_context: UserContext,
        preferred_analysts: Optional[List[str]] = None,
        enable_debate: Optional[bool] = None
    ) -> str:
        """
        開始股票分析工作流
        
        Args:
            stock_id: 股票代號
            user_context: 用戶上下文
            preferred_analysts: 指定的分析師列表
            enable_debate: 是否啟用辯論機制
            
        Returns:
            會話ID
        """
        # 獲取會話槽位（如果啟用生產優化）
        if self.production_optimizer:
            slot_acquired = await self.production_optimizer.concurrency_optimizer.acquire_session_slot()
            if not slot_acquired:
                raise RuntimeError("無法獲取會話槽位，系統繁忙，請稍後再試")
        
        try:
            # 創建會話
            session_id = str(uuid.uuid4())
            
            # 檢查會話數量限制
            current_sessions = len(self.active_sessions)
            max_sessions = self.workflow_config['max_concurrent_sessions']
            
            if current_sessions >= max_sessions:
                self.logger.warning(f"會話數量達到限制: {current_sessions}/{max_sessions}")
                raise RuntimeError("超過最大並發會話數量限制")
            
            # 創建工作流狀態
            state = WorkflowState(
                session_id=session_id,
                stock_id=stock_id,
                user_context=user_context
            )
            
            self.active_sessions[session_id] = state
            
            # 記錄會話開始
            self.logger.info(f"開始股票分析工作流: {stock_id}, 會話ID: {session_id}", extra={
                'session_id': session_id,
                'stock_symbol': stock_id,
                'user_id': user_context.user_id,
                'membership_tier': user_context.membership_tier.value,
                'preferred_analysts': preferred_analysts,
                'enable_debate': enable_debate,
                'current_sessions': current_sessions + 1,
                'max_sessions': max_sessions
            })
            
            # 開始異步執行工作流
            asyncio.create_task(self._execute_workflow_with_cleanup(
                state, preferred_analysts, enable_debate
            ))
            
            return session_id
            
        except Exception:
            # 釋放會話槽位
            if self.production_optimizer:
                self.production_optimizer.concurrency_optimizer.release_session_slot()
            raise
    
    async def _execute_workflow_with_cleanup(
        self,
        state: WorkflowState,
        preferred_analysts: Optional[List[str]] = None,
        enable_debate: Optional[bool] = None
    ):
        """執行工作流並處理清理"""
        try:
            await self._execute_workflow(state, preferred_analysts, enable_debate)
        except Exception as e:
            # 處理錯誤
            error_info = await handle_error(e, {
                'session_id': state.session_id,
                'stock_symbol': state.stock_id,
                'user_id': state.user_context.user_id,
                'current_phase': state.current_phase.value,
                'component': 'trading_graph_workflow'
            }, user_id=state.user_context.user_id, session_id=state.session_id)
            
            # 更新狀態
            state.overall_status = AnalysisStatus.FAILED
            state.current_phase = AnalysisPhase.ERROR
            state.add_error(f"工作流執行失敗: {str(e)}")
            state.end_time = datetime.now()
            
            self.logger.error(f"工作流執行失敗: {state.session_id}", extra={
                'session_id': state.session_id,
                'stock_symbol': state.stock_id,
                'error_id': error_info.error_id,
                'error_message': str(e)
            })
            
            await self._notify_status_change(state)
        
        finally:
            # 釋放會話槽位
            if self.production_optimizer:
                self.production_optimizer.concurrency_optimizer.release_session_slot()
    
    @optimize_for_production
    async def _execute_workflow(
        self,
        state: WorkflowState,
        preferred_analysts: Optional[List[str]] = None,
        enable_debate: Optional[bool] = None
    ):
        """執行完整的分析工作流"""
        try:
            # 階段 1: 數據收集
            await self._phase_data_collection(state)
            
            # 階段 2: 並行分析
            await self._phase_parallel_analysis(state, preferred_analysts)
            
            # 階段 3: 辯論和共識（如果啟用）
            if enable_debate or (enable_debate is None and self.workflow_config.get('enable_debate', True)):
                await self._phase_debate_consensus(state)
            
            # 階段 4: 最終整合
            await self._phase_final_integration(state)
            
            # 標記完成
            state.current_phase = AnalysisPhase.COMPLETED
            state.overall_status = AnalysisStatus.COMPLETED
            state.end_time = datetime.now()
            state.progress_percentage = 100.0
            
            # 計算總執行時間
            total_time = (state.end_time - state.start_time).total_seconds()
            state.performance_metrics['total_execution_time'] = total_time
            
            await self._notify_status_change(state)
            
            self.logger.info(f"工作流完成: {state.session_id}, 執行時間: {total_time:.2f}秒")
            
        except Exception as e:
            # 處理工作流錯誤
            state.current_phase = AnalysisPhase.ERROR
            state.overall_status = AnalysisStatus.FAILED
            state.end_time = datetime.now()
            state.add_error(f"工作流執行失敗: {str(e)}")
            
            await self._notify_status_change(state)
            
            self.logger.error(f"工作流執行失敗: {state.session_id}, 錯誤: {str(e)}")
        
        finally:
            # 記錄會話指標
            self._record_session_metrics(state)
    
    async def _phase_data_collection(self, state: WorkflowState):
        """階段 1: 數據收集"""
        state.current_phase = AnalysisPhase.DATA_COLLECTION
        state.progress_percentage = 10.0
        await self._notify_status_change(state)
        
        self.logger.info(f"開始數據收集階段: {state.stock_id}")
        
        # 並行收集不同類型的數據
        data_tasks = []
        
        # 股價數據
        data_tasks.append(self._collect_data(
            state, DataType.STOCK_PRICE, "股價數據"
        ))
        
        # 公司資料
        data_tasks.append(self._collect_data(
            state, DataType.COMPANY_PROFILE, "公司資料"
        ))
        
        # 財務數據
        data_tasks.append(self._collect_data(
            state, DataType.FINANCIAL_DATA, "財務數據"
        ))
        
        # 新聞數據
        data_tasks.append(self._collect_data(
            state, DataType.COMPANY_NEWS, "新聞數據"
        ))
        
        # 等待所有數據收集完成
        await asyncio.gather(*data_tasks, return_exceptions=True)
        
        state.progress_percentage = 25.0
        await self._notify_status_change(state)
        
        self.logger.info(f"數據收集階段完成: {state.stock_id}")
    
    async def _collect_data(self, state: WorkflowState, data_type: DataType, description: str):
        """收集特定類型的數據"""
        try:
            request = DataRequest(
                symbol=state.stock_id,
                data_type=data_type,
                user_context=state.user_context
            )
            
            response = await self.data_orchestrator.get_data(request)
            
            if response.success:
                state.collected_data[data_type.value] = response.data
                self.logger.debug(f"{description}收集成功: {state.stock_id}")
            else:
                error_msg = f"{description}收集失敗: {response.error}"
                state.data_collection_errors.append(error_msg)
                self.logger.warning(error_msg)
                
        except Exception as e:
            error_msg = f"{description}收集異常: {str(e)}"
            state.data_collection_errors.append(error_msg)
            self.logger.error(error_msg)
    
    async def _phase_parallel_analysis(self, state: WorkflowState, preferred_analysts: Optional[List[str]]):
        """階段 2: 並行分析 - 使用WorkflowOrchestrator"""
        state.current_phase = AnalysisPhase.PARALLEL_ANALYSIS
        state.progress_percentage = 30.0
        await self._notify_status_change(state)
        
        self.logger.info(f"開始並行分析階段: {state.stock_id}")
        
        # 確定要執行的分析師
        analysts_to_run = self._select_analysts(state.user_context, preferred_analysts)
        
        # 創建分析師執行狀態（用於狀態追蹤）
        for analyst_id in analysts_to_run:
            if analyst_id in self.analysts:
                analyst = self.analysts[analyst_id]
                state.analyst_executions[analyst_id] = AnalysistExecution(
                    analyst_id=analyst_id,
                    analyst_type=analyst.get_analysis_type()
                )
        
        # 創建分析狀態
        analysis_state = AnalysisState(
            stock_id=state.stock_id,
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            user_context=asdict(state.user_context) if state.user_context else None,
            stock_data=state.collected_data.get('stock_price'),
            financial_data=state.collected_data.get('financial_data'),
            news_data=state.collected_data.get('company_news'),
            market_data=state.collected_data.get('market_data')
        )
        
        # 使用工作流編排器執行分析
        try:
            execution_result = await self.workflow_orchestrator.execute_workflow(
                state=analysis_state,
                selected_analysts=analysts_to_run
            )
            
            # 將編排器結果轉換為工作流狀態
            for analyst_id, analysis_result in execution_result.analyst_results.items():
                if analyst_id in state.analyst_executions:
                    execution = state.analyst_executions[analyst_id]
                    execution.status = AnalysisStatus.COMPLETED
                    execution.result = analysis_result
                    execution.start_time = datetime.now() - timedelta(
                        seconds=execution_result.performance_metrics.get(
                            f"{analyst_id}_execution_time", 1.0
                        )
                    )
                    execution.end_time = datetime.now()
                    execution.execution_time = execution_result.performance_metrics.get(
                        f"{analyst_id}_execution_time", 1.0
                    )
            
            # 記錄失敗的分析師
            for analyst_id in analysts_to_run:
                if (analyst_id not in execution_result.analyst_results and 
                    analyst_id in state.analyst_executions):
                    execution = state.analyst_executions[analyst_id]
                    execution.status = AnalysisStatus.FAILED
                    execution.error = execution_result.performance_metrics.get(
                        f"{analyst_id}_error", "未知錯誤"
                    )
            
            # 記錄衝突解決信息
            if execution_result.conflict_resolutions:
                for conflict in execution_result.conflict_resolutions:
                    state.add_warning(f"解決建議衝突: {conflict['conflict_type']} -> {conflict.get('resolved_recommendation')}")
            
            self.logger.info(f"工作流編排器執行完成", extra={
                'session_id': state.session_id,
                'successful_analyses': len(execution_result.analyst_results),
                'conflicts_resolved': len(execution_result.conflict_resolutions),
                'orchestrator_success': execution_result.success
            })
            
        except Exception as e:
            # 編排器執行失敗，標記所有分析師為失敗
            for analyst_id in analysts_to_run:
                if analyst_id in state.analyst_executions:
                    execution = state.analyst_executions[analyst_id]
                    execution.status = AnalysisStatus.FAILED
                    execution.error = f"工作流編排器執行失敗: {str(e)}"
            
            self.logger.error(f"工作流編排器執行失敗: {str(e)}", extra={
                'session_id': state.session_id,
                'analysts_to_run': analysts_to_run
            })
        
        state.progress_percentage = 70.0
        await self._notify_status_change(state)
        
        completed_count = sum(1 for exec in state.analyst_executions.values() 
                             if exec.status == AnalysisStatus.COMPLETED)
        
        self.logger.info(f"並行分析階段完成: {state.stock_id}, 完成 {completed_count}/{len(analysts_to_run)} 個分析師")
    
    def _select_analysts(self, user_context: UserContext, preferred_analysts: Optional[List[str]]) -> List[str]:
        """根據用戶權限和偏好選擇分析師"""
        available_analysts = list(self.analysts.keys())
        
        # 如果指定了偏好分析師，過濾可用的
        if preferred_analysts:
            analysts_to_run = [a for a in preferred_analysts if a in available_analysts]
        else:
            # 根據會員等級選擇分析師
            if user_context.membership_tier.value == 'FREE':
                # 免費會員：基礎分析師
                analysts_to_run = ['taiwan_market_analyst', 'risk_analyst']
            elif user_context.membership_tier.value == 'GOLD':
                # 黃金會員：增加基本面和新聞分析
                analysts_to_run = ['taiwan_market_analyst', 'risk_analyst', 'fundamentals_analyst', 'news_analyst']
            else:  # DIAMOND
                # 鑽石會員：所有分析師
                analysts_to_run = available_analysts
        
        # 過濾實際存在的分析師
        analysts_to_run = [a for a in analysts_to_run if a in self.analysts]
        
        # 投資規劃師總是最後執行
        if 'investment_planner' in analysts_to_run:
            analysts_to_run.remove('investment_planner')
            analysts_to_run.append('investment_planner')
        
        return analysts_to_run
    
    async def _execute_analyst(self, state: WorkflowState, analyst_id: str):
        """執行單個分析師"""
        execution = state.analyst_executions[analyst_id]
        analyst = self.analysts[analyst_id]
        
        try:
            execution.status = AnalysisStatus.RUNNING
            execution.start_time = datetime.now()
            
            # 創建分析狀態
            analysis_state = AnalysisState(
                stock_id=state.stock_id,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                user_context=asdict(state.user_context) if state.user_context else None,
                stock_data=state.collected_data.get('stock_price'),
                financial_data=state.collected_data.get('financial_data'),
                news_data=state.collected_data.get('company_news'),
                market_data=state.collected_data.get('market_data')
            )
            
            # 執行分析
            result = await analyst.analyze(analysis_state)
            
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.result = result
            execution.status = AnalysisStatus.COMPLETED
            
            self.logger.info(f"分析師 {analyst_id} 執行完成，耗時 {execution.execution_time:.2f}秒")
            
        except Exception as e:
            execution.end_time = datetime.now()
            execution.execution_time = (execution.end_time - execution.start_time).total_seconds()
            execution.status = AnalysisStatus.FAILED
            execution.error = str(e)
            
            state.add_error(f"分析師 {analyst_id} 執行失敗: {str(e)}")
            self.logger.error(f"分析師 {analyst_id} 執行失敗: {str(e)}")
        
        # 通知狀態變化
        await self._notify_status_change(state)
    
    async def _phase_debate_consensus(self, state: WorkflowState):
        """階段 3: 辯論和共識"""
        state.current_phase = AnalysisPhase.DEBATE_CONSENSUS
        state.progress_percentage = 75.0
        await self._notify_status_change(state)
        
        self.logger.info(f"開始辯論共識階段: {state.stock_id}")
        
        # 收集成功的分析結果
        successful_results = []
        for execution in state.analyst_executions.values():
            if execution.status == AnalysisStatus.COMPLETED and execution.result:
                successful_results.append(execution.result)
        
        if len(successful_results) < 2:
            state.add_warning("分析結果不足，跳過辯論階段")
            return
        
        # 檢查是否存在分歧
        consensus_score = self._calculate_consensus_score(successful_results)
        
        if consensus_score >= self.workflow_config.get('min_consensus_threshold', 0.6):
            # 共識度足夠，無需辯論
            state.consensus_result = {
                'consensus_achieved': True,
                'consensus_score': consensus_score,
                'debate_rounds': 0,
                'final_recommendation': self._get_majority_recommendation(successful_results)
            }
        else:
            # 需要進行辯論
            await self._conduct_debate(state, successful_results)
        
        state.progress_percentage = 85.0
        await self._notify_status_change(state)
        
        self.logger.info(f"辯論共識階段完成: {state.stock_id}")
    
    def _calculate_consensus_score(self, results: List[AnalysisResult]) -> float:
        """計算共識分數"""
        if not results:
            return 0.0
        
        recommendations = [r.recommendation for r in results]
        recommendation_counts = {}
        
        for rec in recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # 最多的建議數量 / 總建議數量
        max_count = max(recommendation_counts.values())
        return max_count / len(recommendations)
    
    def _get_majority_recommendation(self, results: List[AnalysisResult]) -> str:
        """獲取多數派建議"""
        recommendations = [r.recommendation for r in results]
        recommendation_counts = {}
        
        for rec in recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        return max(recommendation_counts.items(), key=lambda x: x[1])[0]
    
    async def _conduct_debate(self, state: WorkflowState, results: List[AnalysisResult]):
        """進行辯論過程"""
        max_rounds = self.workflow_config.get('max_debate_rounds', 3)
        
        for round_num in range(1, max_rounds + 1):
            debate_round = {
                'round': round_num,
                'timestamp': datetime.now().isoformat(),
                'participants': [],
                'consensus_score': 0.0
            }
            
            # 模擬辯論過程
            # 在實際實現中，這裡會讓分析師互相辯論
            await asyncio.sleep(0.5)  # 模擬辯論時間
            
            # 重新計算共識
            consensus_score = self._calculate_consensus_score(results)
            debate_round['consensus_score'] = consensus_score
            
            state.debate_rounds.append(debate_round)
            
            if consensus_score >= self.workflow_config.get('min_consensus_threshold', 0.6):
                # 達成共識
                state.consensus_result = {
                    'consensus_achieved': True,
                    'consensus_score': consensus_score,
                    'debate_rounds': round_num,
                    'final_recommendation': self._get_majority_recommendation(results)
                }
                break
        
        # 如果經過所有輪次仍未達成共識
        if not state.consensus_result:
            state.consensus_result = {
                'consensus_achieved': False,
                'consensus_score': consensus_score,
                'debate_rounds': max_rounds,
                'final_recommendation': self._get_majority_recommendation(results)
            }
    
    async def _phase_final_integration(self, state: WorkflowState):
        """階段 4: 最終整合"""
        state.current_phase = AnalysisPhase.FINAL_INTEGRATION
        state.progress_percentage = 90.0
        await self._notify_status_change(state)
        
        self.logger.info(f"開始最終整合階段: {state.stock_id}")
        
        # 如果有投資規劃師結果，直接使用
        investment_planner_result = None
        for execution in state.analyst_executions.values():
            if (execution.analyst_id == 'investment_planner' and 
                execution.status == AnalysisStatus.COMPLETED):
                investment_planner_result = execution.result
                break
        
        if investment_planner_result:
            # 使用投資規劃師的綜合結果
            state.final_result = investment_planner_result
        else:
            # 手動整合所有分析師結果
            state.final_result = await self._integrate_results(state)
        
        # 添加整合元數據
        state.integration_metadata = {
            'integration_method': 'investment_planner' if investment_planner_result else 'manual_integration',
            'analysts_used': list(state.analyst_executions.keys()),
            'successful_analyses': sum(1 for exec in state.analyst_executions.values() 
                                     if exec.status == AnalysisStatus.COMPLETED),
            'consensus_info': state.consensus_result,
            'data_sources_used': list(state.collected_data.keys())
        }
        
        state.progress_percentage = 95.0
        await self._notify_status_change(state)
        
        self.logger.info(f"最終整合階段完成: {state.stock_id}")
    
    async def _integrate_results(self, state: WorkflowState) -> AnalysisResult:
        """手動整合分析結果"""
        successful_results = []
        for execution in state.analyst_executions.values():
            if execution.status == AnalysisStatus.COMPLETED and execution.result:
                successful_results.append(execution.result)
        
        if not successful_results:
            # 沒有成功的分析結果
            from ..agents.analysts.base_analyst import AnalysisResult, AnalysisConfidenceLevel
            return AnalysisResult(
                analyst_id='trading_graph_integration',
                stock_id=state.stock_id,
                analysis_date=datetime.now().strftime('%Y-%m-%d'),
                analysis_type=AnalysisType.INVESTMENT_PLANNING,
                recommendation='HOLD',
                confidence=0.0,
                confidence_level=AnalysisConfidenceLevel.VERY_LOW,
                reasoning=['所有分析師執行失敗，無法提供建議'],
                risk_factors=['系統分析失敗風險']
            )
        
        # 簡單的投票機制
        recommendations = [r.recommendation for r in successful_results]
        recommendation_counts = {}
        for rec in recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        final_recommendation = max(recommendation_counts.items(), key=lambda x: x[1])[0]
        
        # 計算平均信心度
        avg_confidence = sum(r.confidence for r in successful_results) / len(successful_results)
        
        # 收集所有理由
        all_reasoning = []
        for result in successful_results:
            all_reasoning.extend([f"[{result.analyst_id}] {reason}" for reason in result.reasoning or []])
        
        # 收集所有風險因子
        all_risk_factors = []
        for result in successful_results:
            if result.risk_factors:
                all_risk_factors.extend([f"[{result.analyst_id}] {risk}" for risk in result.risk_factors])
        
        # 計算目標價
        target_prices = [r.target_price for r in successful_results if r.target_price]
        avg_target_price = sum(target_prices) / len(target_prices) if target_prices else None
        
        from ..agents.analysts.base_analyst import AnalysisResult, AnalysisConfidenceLevel
        return AnalysisResult(
            analyst_id='trading_graph_integration',
            stock_id=state.stock_id,
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            analysis_type=AnalysisType.INVESTMENT_PLANNING,
            recommendation=final_recommendation,
            confidence=avg_confidence,
            confidence_level=AnalysisConfidenceLevel.HIGH if avg_confidence > 0.7 else AnalysisConfidenceLevel.MODERATE,
            target_price=avg_target_price,
            reasoning=all_reasoning[:10],  # 限制理由數量
            risk_factors=all_risk_factors[:8]  # 限制風險因子數量
        )
    
    def _record_session_metrics(self, state: WorkflowState):
        """記錄會話指標"""
        metrics = {
            'session_id': state.session_id,
            'stock_id': state.stock_id,
            'user_tier': state.user_context.membership_tier.value,
            'total_execution_time': state.performance_metrics.get('total_execution_time', 0),
            'analysts_executed': len(state.analyst_executions),
            'successful_analyses': sum(1 for exec in state.analyst_executions.values() 
                                     if exec.status == AnalysisStatus.COMPLETED),
            'data_collection_errors': len(state.data_collection_errors),
            'final_status': state.overall_status.value,
            'timestamp': datetime.now().isoformat()
        }
        
        self.session_metrics[state.session_id] = metrics
    
    # ==================== 外部接口方法 ====================
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """獲取會話狀態"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id].to_dict()
        return None
    
    def get_all_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有活躍會話"""
        return {
            session_id: state.to_dict()
            for session_id, state in self.active_sessions.items()
        }
    
    def cancel_session(self, session_id: str) -> bool:
        """取消會話"""
        if session_id in self.active_sessions:
            state = self.active_sessions[session_id]
            state.overall_status = AnalysisStatus.CANCELLED
            state.end_time = datetime.now()
            state.add_warning("會話被用戶取消")
            return True
        return False
    
    def cleanup_completed_sessions(self, max_age_hours: int = 24):
        """清理已完成的會話"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, state in self.active_sessions.items():
            if state.overall_status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
                if state.end_time and (current_time - state.end_time).total_seconds() > max_age_hours * 3600:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
            self.logger.info(f"清理已完成會話: {session_id}")
        
        return len(sessions_to_remove)
    
    async def get_routing_decision_history(
        self, 
        limit: int = 50,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取路由决策历史（透明化功能）"""
        if not self.ai_task_router:
            return []
        
        try:
            return self.ai_task_router.get_decision_history(
                limit=limit, 
                task_type=task_type
            )
        except Exception as e:
            self.logger.error(f"获取路由决策历史失败: {e}")
            return []
    
    async def force_routing_health_check(self) -> Dict[str, Any]:
        """强制执行路由器健康检查"""
        if not self.ai_task_router:
            return {'error': '智能路由器未启用'}
        
        try:
            return await self.ai_task_router.health_check()
        except Exception as e:
            self.logger.error(f"路由器健康检查失败: {e}")
            return {'error': str(e)}
    
    def update_routing_strategy(
        self, 
        strategy: RoutingStrategy,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> bool:
        """动态更新路由策略"""
        if not self.ai_task_router:
            self.logger.warning("智能路由器未启用，无法更新策略")
            return False
        
        try:
            if custom_weights:
                from ..routing.ai_task_router import RoutingWeights
                weights = RoutingWeights(**custom_weights)
                return self.ai_task_router.update_strategy_weights(strategy, weights)
            return True
        except Exception as e:
            self.logger.error(f"更新路由策略失败: {e}")
            return False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """獲取系統指標"""
        active_count = len(self.active_sessions)
        completed_count = sum(1 for metrics in self.session_metrics.values() 
                             if metrics['final_status'] == 'completed')
        
        avg_execution_time = 0
        if self.session_metrics:
            total_time = sum(metrics.get('total_execution_time', 0) 
                           for metrics in self.session_metrics.values())
            avg_execution_time = total_time / len(self.session_metrics)
        
        # 獲取工作流編排器指標
        orchestrator_info = {
            'registered_analysts': self.workflow_orchestrator.get_registered_analysts(),
            'execution_history': self.workflow_orchestrator.get_execution_history(5)
        }
        
        # 获取智能路由器统计信息
        routing_info = {}
        if self.ai_task_router:
            try:
                routing_info = self.ai_task_router.get_routing_statistics()
                # 移除 await，因為這是同步函數
                routing_info['health_status'] = 'available'
            except Exception as e:
                routing_info = {'error': f'获取路由统计失败: {str(e)}'}
        
        return {
            'active_sessions': active_count,
            'completed_sessions': completed_count,
            'total_sessions': len(self.session_metrics),
            'average_execution_time': avg_execution_time,
            'available_analysts': list(self.analysts.keys()),
            'workflow_orchestrator': orchestrator_info,
            'intelligent_routing': {
                'enabled': self.enable_intelligent_routing,
                'router_active': self.ai_task_router is not None,
                'transparency_enabled': self.routing_transparency.get('enabled', True),
                'statistics': routing_info
            },
            'system_uptime': (datetime.now() - datetime.now()).total_seconds(),  # 實際應該記錄啟動時間
            'timestamp': datetime.now().isoformat()
        }

# 便利函數
async def create_trading_graph(config: Optional[Dict[str, Any]] = None) -> TradingAgentsGraph:
    """創建並初始化交易圖"""
    graph = TradingAgentsGraph(config)
    await graph.initialize()
    return graph

if __name__ == "__main__":
    # 測試腳本
    async def test_trading_graph():
        print("測試 TradingAgentsGraph 工作流引擎")
        
        # 創建工作流引擎
        graph = await create_trading_graph()
        
        # 模擬用戶上下文
        from ..utils.user_context import UserContext, TierType, UserPermissions
        user_context = UserContext(
            user_id='test_user',
            membership_tier=TierType.DIAMOND,
            permissions=UserPermissions()
        )
        
        # 添加狀態回調
        def status_callback(state):
            print(f"狀態更新: {state.current_phase.value} - {state.progress_percentage:.1f}%")
        
        graph.add_status_callback(status_callback)
        
        # 開始分析
        session_id = await graph.analyze_stock("2330", user_context)
        print(f"分析會話開始: {session_id}")
        
        # 等待分析完成
        while True:
            status = graph.get_session_status(session_id)
            if status and status['overall_status'] in ['completed', 'failed', 'cancelled']:
                break
            await asyncio.sleep(1)
        
        # 顯示最終結果
        final_status = graph.get_session_status(session_id)
        print(f"分析完成: {final_status['overall_status']}")
        
        if final_status.get('final_result'):
            result = final_status['final_result']
            print(f"最終建議: {result['recommendation']}")
            print(f"信心度: {result['confidence']:.2f}")
            print(f"目標價: {result.get('target_price')}")
        
        print("TradingAgentsGraph 測試完成")
    
    asyncio.run(test_trading_graph())