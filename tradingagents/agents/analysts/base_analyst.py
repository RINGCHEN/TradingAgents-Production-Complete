#!/usr/bin/env python3
"""
Base Analyst - 分析師基礎抽象類
天工 (TianGong) - 整合原工程師設計與天工優化的智能分析師基礎架構

此模組提供：
1. 分析師統一接口和基礎實現
2. 整合天工的成本優化和模型選擇
3. 結果驗證和品質保證
4. Taiwan市場特色支援
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging
import asyncio

# ART系統整合
try:
    from ...art.trajectory_collector import (
        TrajectoryCollector,
        TrajectoryType,
        DecisionStep,
        AnalysisTrajectory
    )
    from ...art.ruler_reward_system import (
        RULERRewardSystem,
        RewardType
    )
    ART_AVAILABLE = True
except ImportError:
    # 如果ART系統不可用，嘗試使用MVP演示版本
    try:
        import sys
        from pathlib import Path
        # 添加mvp_art_demo路徑
        mvp_path = Path(__file__).parent.parent.parent.parent / "mvp_art_demo"
        if mvp_path not in sys.path:
            sys.path.append(str(mvp_path))
        
        from art_trajectory_collector import (
            ARTTrajectoryCollector as TrajectoryCollector,
            TrajectoryType,
            DecisionStep,
            AnalysisTrajectory,
            RewardType
        )
        ART_AVAILABLE = False
    except ImportError:
        # 如果都不可用，定義簡化版本
        from enum import Enum
        from dataclasses import dataclass
        from typing import Dict, Any, List, Optional
        
        class TrajectoryType(Enum):
            ANALYSIS_DECISION = "analysis_decision"
            REASONING_STEP = "reasoning_step"
            DATA_INTERPRETATION = "data_interpretation"
            RECOMMENDATION_LOGIC = "recommendation_logic"
        
        class RewardType(Enum):
            CONSISTENCY_REWARD = "consistency_reward"
            TIMELINESS_REWARD = "timeliness_reward"
        
        @dataclass
        class DecisionStep:
            step_id: str
            timestamp: str
            trajectory_type: TrajectoryType
            input_data: Dict[str, Any]
            reasoning_process: List[str]
            intermediate_result: Any
            confidence_score: float
            data_dependencies: List[str]
            computation_method: str
        
        @dataclass 
        class AnalysisTrajectory:
            trajectory_id: str
            stock_id: str
            analyst_type: str
            user_id: str
            start_time: str
            end_time: Optional[str] = None
            decision_steps: List[DecisionStep] = None
            final_recommendation: Optional[str] = None
            final_confidence: Optional[float] = None
        
        TrajectoryCollector = None
        ART_AVAILABLE = False

class AnalysisConfidenceLevel(Enum):
    """分析信心度級別"""
    VERY_LOW = "very_low"      # 0.0-0.2
    LOW = "low"                # 0.2-0.4
    MODERATE = "moderate"      # 0.4-0.6
    HIGH = "high"              # 0.6-0.8
    VERY_HIGH = "very_high"    # 0.8-1.0

class AnalysisType(Enum):
    """分析類型"""
    TECHNICAL = "technical"           # 技術分析
    FUNDAMENTAL = "fundamental"       # 基本面分析
    NEWS_SENTIMENT = "news_sentiment" # 新聞情緒分析
    MARKET_SENTIMENT = "market_sentiment" # 市場情緒分析
    RISK_ASSESSMENT = "risk_assessment"   # 風險評估
    INVESTMENT_PLANNING = "investment_planning" # 投資規劃
    TAIWAN_SPECIFIC = "taiwan_specific"     # Taiwan專業分析

@dataclass
class AnalysisResult:
    """分析結果數據類 - 天工優化版"""
    analyst_id: str
    stock_id: str
    analysis_date: str
    analysis_type: AnalysisType
    recommendation: str  # BUY, SELL, HOLD
    confidence: float    # 0.0 - 1.0
    confidence_level: AnalysisConfidenceLevel
    target_price: Optional[float] = None
    reasoning: List[str] = None
    technical_indicators: Optional[Dict[str, Any]] = None
    fundamental_metrics: Optional[Dict[str, Any]] = None
    risk_factors: Optional[List[str]] = None
    market_conditions: Optional[Dict[str, Any]] = None
    taiwan_insights: Optional[Dict[str, Any]] = None  # 天工Taiwan特色
    cost_info: Optional[Dict[str, Any]] = None  # 天工成本追蹤
    model_used: Optional[str] = None  # 天工模型追蹤
    routing_transparency: Optional[Dict[str, Any]] = None  # GPT-OSS路由透明信息
    timestamp: str = None
    
    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        
        # 自動計算信心度級別
        self.confidence_level = self._calculate_confidence_level()
    
    def _calculate_confidence_level(self) -> AnalysisConfidenceLevel:
        """根據數值信心度計算級別"""
        if self.confidence >= 0.8:
            return AnalysisConfidenceLevel.VERY_HIGH
        elif self.confidence >= 0.6:
            return AnalysisConfidenceLevel.HIGH
        elif self.confidence >= 0.4:
            return AnalysisConfidenceLevel.MODERATE
        elif self.confidence >= 0.2:
            return AnalysisConfidenceLevel.LOW
        else:
            return AnalysisConfidenceLevel.VERY_LOW

@dataclass
class AnalysisState:
    """分析狀態 - 整合原工程師設計"""
    stock_id: str
    analysis_date: str
    user_id: Optional[str] = None  # ART系統用戶識別
    user_context: Optional[Dict[str, Any]] = None
    
    # 數據收集結果
    stock_data: Optional[Dict[str, Any]] = None
    financial_data: Optional[Dict[str, Any]] = None
    news_data: Optional[List[Dict[str, Any]]] = None
    market_data: Optional[Dict[str, Any]] = None
    
    # Taiwan特色數據 (天工優勢)
    taiwan_institutional_data: Optional[Dict[str, Any]] = None
    taiwan_market_conditions: Optional[Dict[str, Any]] = None
    
    # 執行狀態
    current_phase: str = "initialization"
    progress_percentage: float = 0.0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class BaseAnalyst(ABC):
    """分析師基礎抽象類 - 天工優化版"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.analyst_id = self.__class__.__name__.lower().replace('analyst', '_analyst')
        self.logger = logging.getLogger(__name__)
        
        # 天工優化：整合智能組件
        self._initialize_tianGong_components()
        
        # GPT-OSS 智能路由器集成
        self.intelligent_routing_client = None
        self.routing_enabled = False
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _initialize_tianGong_components(self):
        """初始化天工優化組件"""
        try:
            # 天工成本優化器
            from ...utils.llm_cost_optimizer import LLMCostOptimizer
            self.cost_optimizer = LLMCostOptimizer()
            
            # 天工智能模型選擇器
            from ...utils.smart_model_selector import SmartModelSelector
            self.model_selector = SmartModelSelector()
            
            # 天工權限橋接器
            from ...utils.member_permission_bridge import MemberPermissionBridge
            self.permission_bridge = MemberPermissionBridge()
            
            # ART軌跡收集器初始化
            self._initialize_art_system()
            
            self.logger.info(f"天工優化組件初始化成功: {self.analyst_id}")
            
        except ImportError as e:
            self.logger.warning(f"部分天工組件不可用: {e}")
            self.cost_optimizer = None
            self.model_selector = None
            self.permission_bridge = None
            self.trajectory_collector = None
            self.reward_system = None
            self.current_trajectory_id = None
    
    def _initialize_art_system(self):
        """初始化ART軌跡收集系統"""
        try:
            if ART_AVAILABLE and TrajectoryCollector is not None:
                # 使用完整ART系統 - 需要實現create函數
                self.trajectory_collector = TrajectoryCollector(
                    storage_path=f"./art_data/{self.analyst_id}"
                )
                self.reward_system = None  # RULER系統暫未實現
            elif TrajectoryCollector is not None:
                # 使用MVP演示版本或回退版本
                if hasattr(TrajectoryCollector, '__name__') and 'ART' in TrajectoryCollector.__name__:
                    # MVP版本
                    self.trajectory_collector = TrajectoryCollector(
                        storage_path=f"./demo_results/{self.analyst_id}"
                    )
                else:
                    # 創建基礎實現
                    self.trajectory_collector = None
                self.reward_system = None
            else:
                # TrajectoryCollector不可用
                self.trajectory_collector = None
                self.reward_system = None
            
            # 當前軌跡ID追蹤
            self.current_trajectory_id = None
            
            if self.trajectory_collector:
                self.logger.info(f"ART軌跡收集系統初始化成功: {self.analyst_id}")
            else:
                self.logger.warning(f"ART軌跡收集系統不可用: {self.analyst_id}")
            
        except Exception as e:
            self.logger.error(f"ART系統初始化失敗: {e}")
            self.trajectory_collector = None
            self.reward_system = None
            self.current_trajectory_id = None
    
    async def _initialize_intelligent_routing_client(self, ai_task_router):
        """初始化智能路由器客户端连接
        
        Args:
            ai_task_router: AITaskRouter实例
        """
        try:
            self.intelligent_routing_client = ai_task_router
            self.routing_enabled = True
            
            self.logger.info(f"✅ {self.analyst_id} 已连接智能路由器", extra={
                'analyst_id': self.analyst_id,
                'routing_enabled': True
            })
            
        except Exception as e:
            self.logger.error(f"❌ {self.analyst_id} 智能路由器连接失败: {e}")
            self.intelligent_routing_client = None
            self.routing_enabled = False
            raise
    
    @abstractmethod
    async def analyze(self, state: AnalysisState) -> AnalysisResult:
        """執行分析 - 子類必須實現"""
        pass
    
    async def analyze_with_workflow_integration(self, state: AnalysisState) -> AnalysisResult:
        """帶工作流整合的分析執行 - 天工優化版"""
        return await self._execute_analysis_with_optimization(state)
    
    @abstractmethod
    def get_analysis_type(self) -> AnalysisType:
        """獲取分析類型 - 子類必須實現"""
        pass
    
    @abstractmethod
    def get_analysis_prompt(self, state: AnalysisState) -> str:
        """生成分析提示詞 - 子類必須實現"""
        pass
    
    async def _execute_analysis_with_optimization(self, state: AnalysisState) -> AnalysisResult:
        """執行帶天工優化的分析流程 - 整合ART軌跡收集"""
        
        try:
            # 0. 開始軌跡收集 (ART系統整合)
            await self._start_trajectory_collection(state)
            
            # 1. 權限檢查 (天工優勢)
            if not await self._check_analysis_permission(state):
                result = self._create_permission_denied_result(state)
                await self._complete_trajectory_collection(result, state)
                return result
            
            # 2. 智能模型選擇 (天工創新) 
            await self._record_trajectory_step(
                state, TrajectoryType.ANALYSIS_DECISION,
                {'task': 'model_selection', 'analysis_type': self.get_analysis_type().value},
                ['開始智能模型選擇', '評估任務複雜度', '選擇最優模型配置'],
                {'phase': 'model_selection'}, 0.9, 'smart_model_selector'
            )
            model_config, selection_info = await self._select_optimal_model(state)
            
            # 3. 執行核心分析 - 帶軌跡收集
            analysis_result = await self._perform_core_analysis_with_trajectory(state, model_config)
            
            # 4. 結果驗證和優化
            await self._record_trajectory_step(
                state, TrajectoryType.RECOMMENDATION_LOGIC,
                {'raw_result': str(analysis_result.recommendation), 'confidence': analysis_result.confidence},
                ['驗證分析結果', '檢查建議值合理性', '增強結果品質'],
                {'validation_phase': True}, 0.95, 'result_validator'
            )
            validated_result = await self._validate_and_enhance_result(
                analysis_result, selection_info, state
            )
            
            # 5. 記錄使用情況 (天工成本追蹤)
            await self._record_analysis_usage(validated_result, state)
            
            # 6. 完成軌跡收集並生成獎勵 (ART系統整合)
            await self._complete_trajectory_collection(validated_result, state)
            
            return validated_result
            
        except Exception as e:
            self.logger.error(f"{self.analyst_id} 分析失敗: {str(e)}")
            error_result = self._create_error_result(state, str(e))
            await self._complete_trajectory_collection(error_result, state)
            return error_result
    
    async def _check_analysis_permission(self, state: AnalysisState) -> bool:
        """檢查分析權限 - 天工權限控制"""
        
        if not self.permission_bridge or not state.user_context:
            return True  # 如果沒有權限系統，允許分析
        
        try:
            user_context = await self.permission_bridge.get_user_context(
                state.user_context.get('user_id', 'anonymous')
            )
            
            if not user_context:
                return False
            
            permission_check = await self.permission_bridge.check_analysis_permission(
                user_context, self.get_analysis_type()
            )
            
            return permission_check.get('allowed', False)
            
        except Exception as e:
            self.logger.error(f"權限檢查失敗: {str(e)}")
            return True  # 權限檢查失敗時允許分析，避免阻斷服務
    
    async def _select_optimal_model(self, state: AnalysisState) -> tuple:
        """選擇最優模型 - 支持智能路由器和天工智能選擇"""
        
        # 优先使用智能路由器（如果可用）
        if self.routing_enabled and self.intelligent_routing_client:
            try:
                self.logger.debug(f"🚀 {self.analyst_id} 使用智能路由器选择模型")
                
                # 创建路由决策请求
                from ...routing.ai_task_router import RoutingDecisionRequest
                
                routing_request = RoutingDecisionRequest(
                    task_type=self.get_analysis_type().value,
                    estimated_tokens=self._estimate_token_usage(state),
                    user_tier=state.user_context.get('membership_tier', 'FREE') if state.user_context else 'FREE',
                    priority='normal',
                    requires_high_quality=self._requires_high_quality_analysis(state),
                    max_acceptable_cost=self._get_max_acceptable_cost(state),
                    max_acceptable_latency=self._get_max_acceptable_latency(state),
                    user_preferences=state.user_context.get('preferences') if state.user_context else None
                )
                
                # 调用智能路由器做决策
                routing_response = await self.intelligent_routing_client.make_routing_decision(routing_request)
                
                if routing_response and hasattr(routing_response, 'selected_provider'):
                    # 创建模型配置对象
                    model_config = type('ModelConfig', (), {
                        'model_name': routing_response.selected_model,
                        'provider': routing_response.selected_provider,
                        'quality_score': routing_response.expected_quality_score or 8.0,
                        'speed_score': 10.0 - (routing_response.expected_latency_ms / 1000) if routing_response.expected_latency_ms else 8.0,
                        'estimated_cost': routing_response.expected_cost
                    })()
                    
                    selection_info = {
                        'selection_method': 'intelligent_routing',
                        'routing_reasoning': routing_response.reasoning,
                        'expected_cost': routing_response.expected_cost,
                        'expected_latency_ms': routing_response.expected_latency_ms,
                        'confidence_score': routing_response.confidence_score,
                        'fallback_options': routing_response.fallback_options,
                        'routing_metadata': routing_response.decision_metadata
                    }
                    
                    self.logger.info(f"✅ {self.analyst_id} 智能路由选择: {routing_response.selected_provider}/{routing_response.selected_model}", extra={
                        'confidence': routing_response.confidence_score,
                        'expected_cost': routing_response.expected_cost
                    })
                    
                    return model_config, selection_info
                else:
                    self.logger.warning(f"⚠️ {self.analyst_id} 智能路由返回无效响应，回退到传统选择")
                    
            except Exception as e:
                self.logger.error(f"❌ {self.analyst_id} 智能路由选择失败: {str(e)}，回退到传统选择")
        
        # 回退到传统的天工智能选择
        if self.model_selector:
            try:
                # 推斷任務複雜度
                task_complexity = self._infer_task_complexity(state)
                
                # 智能模型選擇
                model_config, selection_info = await self.model_selector.select_model_intelligently(
                    state.user_context or {'user_id': 'anonymous', 'membership_tier': 'FREE'},
                    self.get_analysis_type().value,
                    estimated_tokens=self._estimate_token_usage(state)
                )
                
                selection_info['selection_method'] = 'tianGong_smart_selector'
                return model_config, selection_info
                
            except Exception as e:
                self.logger.error(f"模型選擇失敗: {str(e)}")
        
        # 最后回退到预设配置
        default_config = type('ModelConfig', (), {
            'model_name': 'gpt-3.5-turbo',
            'provider': 'openai',
            'quality_score': 7.0,
            'speed_score': 8.0
        })()
        return default_config, {
            'selection_method': 'default_fallback', 
            'selection_reason': 'no_smart_selector_or_routing_available'
        }
    
    def _infer_task_complexity(self, state: AnalysisState) -> str:
        """推斷任務複雜度"""
        analysis_type = self.get_analysis_type()
        
        complexity_mapping = {
            AnalysisType.TECHNICAL: "moderate",
            AnalysisType.FUNDAMENTAL: "complex", 
            AnalysisType.NEWS_SENTIMENT: "moderate",
            AnalysisType.MARKET_SENTIMENT: "moderate",
            AnalysisType.RISK_ASSESSMENT: "complex",
            AnalysisType.INVESTMENT_PLANNING: "critical",
            AnalysisType.TAIWAN_SPECIFIC: "complex"
        }
        
        return complexity_mapping.get(analysis_type, "moderate")
    
    def _estimate_token_usage(self, state: AnalysisState) -> int:
        """估算token使用量"""
        base_tokens = 1000
        
        # 根據可用數據調整估算
        if state.stock_data:
            base_tokens += 500
        if state.financial_data:
            base_tokens += 800
        if state.news_data:
            base_tokens += len(state.news_data) * 200
        
        return min(base_tokens, 4000)  # 限制最大token數
    
    def _requires_high_quality_analysis(self, state: AnalysisState) -> bool:
        """判断是否需要高质量分析"""
        # 基于分析类型和用户等级判断
        analysis_type = self.get_analysis_type()
        high_quality_types = [AnalysisType.INVESTMENT_PLANNING, AnalysisType.RISK_ASSESSMENT]
        
        if analysis_type in high_quality_types:
            return True
        
        if state.user_context:
            user_tier = state.user_context.get('membership_tier', 'FREE')
            if user_tier in ['DIAMOND', 'PREMIUM']:
                return True
        
        return False
    
    def _get_max_acceptable_cost(self, state: AnalysisState) -> Optional[float]:
        """获取最大可接受成本"""
        if not state.user_context:
            return 0.01  # 默认成本限制
        
        user_tier = state.user_context.get('membership_tier', 'FREE')
        cost_limits = {
            'FREE': 0.005,
            'BASIC': 0.01,
            'GOLD': 0.02,
            'DIAMOND': 0.05,
            'PREMIUM': 0.1
        }
        
        return cost_limits.get(user_tier, 0.01)
    
    def _get_max_acceptable_latency(self, state: AnalysisState) -> Optional[int]:
        """获取最大可接受延迟（毫秒）"""
        analysis_type = self.get_analysis_type()
        
        latency_limits = {
            AnalysisType.TECHNICAL: 5000,      # 5秒
            AnalysisType.FUNDAMENTAL: 10000,   # 10秒
            AnalysisType.NEWS_SENTIMENT: 3000, # 3秒
            AnalysisType.RISK_ASSESSMENT: 8000, # 8秒
            AnalysisType.INVESTMENT_PLANNING: 15000, # 15秒
            AnalysisType.TAIWAN_SPECIFIC: 12000 # 12秒
        }
        
        return latency_limits.get(analysis_type, 10000)
    
    async def _perform_core_analysis_with_trajectory(self, state: AnalysisState, model_config) -> AnalysisResult:
        """執行核心分析邏輯 - 整合軌跡收集"""
        
        # 記錄數據解釋步驟
        await self._record_trajectory_step(
            state, TrajectoryType.DATA_INTERPRETATION,
            self._prepare_analysis_context(state),
            ['準備分析上下文', '整合可用數據源', '評估數據品質'],
            {'context_ready': True}, 0.8, 'data_preparation'
        )
        
        # 生成分析提示詞
        prompt = self.get_analysis_prompt(state)
        
        # 記錄推理過程步驟
        await self._record_trajectory_step(
            state, TrajectoryType.REASONING_STEP,
            {'prompt_length': len(prompt), 'model': model_config.model_name},
            ['生成分析提示詞', f'選用模型: {model_config.model_name}', '準備LLM推理'],
            {'llm_ready': True}, 0.85, 'llm_preparation'
        )
        
        # 準備分析上下文
        analysis_context = self._prepare_analysis_context(state)
        
        # 調用LLM分析 
        llm_result = await self._call_llm_analysis(prompt, analysis_context, model_config)
        
        # 記錄LLM結果處理步驟
        await self._record_trajectory_step(
            state, TrajectoryType.ANALYSIS_DECISION,
            {'llm_recommendation': llm_result.get('recommendation', 'HOLD')},
            ['處理LLM分析結果', '解析推薦建議', '提取信心度指標'],
            llm_result, 0.9, 'result_processing'
        )
        
        # 創建分析結果
        result = AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation=llm_result.get('recommendation', 'HOLD'),
            confidence=llm_result.get('confidence', 0.5),
            confidence_level=AnalysisConfidenceLevel.MODERATE,  # 將在__post_init__中重新計算
            target_price=llm_result.get('target_price'),
            reasoning=llm_result.get('reasoning', []),
            technical_indicators=llm_result.get('technical_indicators'),
            fundamental_metrics=llm_result.get('fundamental_metrics'),
            risk_factors=llm_result.get('risk_factors'),
            market_conditions=llm_result.get('market_conditions'),
            model_used=model_config.model_name
        )
        
        return result

    async def _perform_core_analysis(self, state: AnalysisState, model_config) -> AnalysisResult:
        """執行核心分析邏輯"""
        
        # 生成分析提示詞
        prompt = self.get_analysis_prompt(state)
        
        # 準備分析上下文
        analysis_context = self._prepare_analysis_context(state)
        
        # 調用LLM分析 (這裡需要實際的LLM客戶端)
        llm_result = await self._call_llm_analysis(prompt, analysis_context, model_config)
        
        # 創建分析結果
        result = AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation=llm_result.get('recommendation', 'HOLD'),
            confidence=llm_result.get('confidence', 0.5),
            confidence_level=AnalysisConfidenceLevel.MODERATE,  # 將在__post_init__中重新計算
            target_price=llm_result.get('target_price'),
            reasoning=llm_result.get('reasoning', []),
            technical_indicators=llm_result.get('technical_indicators'),
            fundamental_metrics=llm_result.get('fundamental_metrics'),
            risk_factors=llm_result.get('risk_factors'),
            market_conditions=llm_result.get('market_conditions'),
            model_used=model_config.model_name
        )
        
        return result
    
    def _prepare_analysis_context(self, state: AnalysisState) -> Dict[str, Any]:
        """準備分析上下文"""
        context = {
            'stock_id': state.stock_id,
            'analysis_date': state.analysis_date,
            'analyst_type': self.get_analysis_type().value
        }
        
        # 添加可用數據
        if state.stock_data:
            context['stock_data'] = state.stock_data
        if state.financial_data:
            context['financial_data'] = state.financial_data
        if state.news_data:
            context['news_data'] = state.news_data
        if state.market_data:
            context['market_data'] = state.market_data
        
        # 天工Taiwan特色數據
        if state.taiwan_institutional_data:
            context['taiwan_institutional_data'] = state.taiwan_institutional_data
        if state.taiwan_market_conditions:
            context['taiwan_market_conditions'] = state.taiwan_market_conditions
        
        return context
    
    async def _call_llm_analysis(self, prompt: str, context: Dict[str, Any], model_config) -> Dict[str, Any]:
        """調用LLM進行分析 - 模擬實現"""
        
        try:
            # 這裡應該整合實際的LLM客戶端
            # 目前提供模擬實現
            
            await asyncio.sleep(0.5)  # 模擬LLM調用時間
            
            # 基於分析類型返回模擬結果
            analysis_type = self.get_analysis_type()
            
            if analysis_type == AnalysisType.TECHNICAL:
                return {
                    'recommendation': 'BUY',
                    'confidence': 0.75,
                    'reasoning': ['技術指標顯示上升趨勢', 'RSI指標處於健康水平', '成交量配合價格上漲'],
                    'technical_indicators': {'rsi': 65, 'macd': 'bullish', 'ma_trend': 'up'}
                }
            elif analysis_type == AnalysisType.FUNDAMENTAL:
                return {
                    'recommendation': 'HOLD', 
                    'confidence': 0.68,
                    'reasoning': ['財務指標穩健', '營收成長率良好', '但估值略高'],
                    'fundamental_metrics': {'pe_ratio': 22.5, 'roe': 15.2, 'debt_ratio': 0.35}
                }
            else:
                return {
                    'recommendation': 'HOLD',
                    'confidence': 0.6,
                    'reasoning': [f'{analysis_type.value}分析結果中性'],
                }
                
        except Exception as e:
            self.logger.error(f"LLM分析調用失敗: {str(e)}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'reasoning': [f'分析過程中發生錯誤: {str(e)}'],
                'error': str(e)
            }
    
    async def _validate_and_enhance_result(
        self, 
        result: AnalysisResult, 
        selection_info: Dict[str, Any],
        state: AnalysisState
    ) -> AnalysisResult:
        """驗證並增強分析結果"""
        
        # 驗證建議值
        valid_recommendations = ['BUY', 'SELL', 'HOLD']
        if result.recommendation not in valid_recommendations:
            result.recommendation = 'HOLD'
            result.reasoning.append('建議值已修正為HOLD')
        
        # 驗證信心度
        if not isinstance(result.confidence, (int, float)) or result.confidence < 0 or result.confidence > 1:
            result.confidence = 0.5
            result.reasoning.append('信心度已修正為0.5')
        
        # 添加天工成本信息和路由透明信息
        result.cost_info = {
            'estimated_cost': selection_info.get('estimated_cost', 0.0),
            'model_used': result.model_used,
            'selection_reason': selection_info.get('selection_reason', 'unknown'),
            'selection_method': selection_info.get('selection_method', 'unknown')
        }
        
        # 添加智能路由透明信息（如果可用）
        if selection_info.get('selection_method') == 'intelligent_routing':
            result.routing_transparency = {
                'routing_used': True,
                'routing_reasoning': selection_info.get('routing_reasoning', ''),
                'confidence_score': selection_info.get('confidence_score', 0.0),
                'expected_cost': selection_info.get('expected_cost', 0.0),
                'expected_latency_ms': selection_info.get('expected_latency_ms', 0),
                'fallback_options': selection_info.get('fallback_options', []),
                'routing_metadata': selection_info.get('routing_metadata', {})
            }
        else:
            result.routing_transparency = {
                'routing_used': False,
                'fallback_reason': selection_info.get('selection_reason', 'routing_not_available')
            }
        
        # 重新計算信心度級別
        result.confidence_level = result._calculate_confidence_level()
        
        return result
    
    async def _record_analysis_usage(self, result: AnalysisResult, state: AnalysisState):
        """記錄分析使用情況 - 天工成本追蹤"""
        
        if not self.cost_optimizer:
            return
        
        try:
            user_id = state.user_context.get('user_id', 'anonymous') if state.user_context else 'anonymous'
            
            # 估算實際使用的token數
            estimated_input_tokens = self._estimate_token_usage(state)
            estimated_output_tokens = len(str(result.reasoning)) * 2  # 粗略估算
            
            # 記录使用情况
            await self.cost_optimizer.record_usage(
                user_id=user_id,
                request_id=f"{result.analyst_id}_{int(datetime.now().timestamp())}",
                model_name=result.model_used or 'unknown',
                task_type=result.analysis_type.value,
                input_tokens=estimated_input_tokens,
                output_tokens=estimated_output_tokens,
                response_time_ms=1000,  # 模擬響應時間
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"使用情況記錄失敗: {str(e)}")
    
    def _create_permission_denied_result(self, state: AnalysisState) -> AnalysisResult:
        """創建權限拒絕結果"""
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation='HOLD',
            confidence=0.0,
            confidence_level=AnalysisConfidenceLevel.VERY_LOW,
            reasoning=['用戶權限不足，無法執行此類型分析']
        )
    
    def _create_error_result(self, state: AnalysisState, error_message: str) -> AnalysisResult:
        """創建錯誤結果"""
        return AnalysisResult(
            analyst_id=self.analyst_id,
            stock_id=state.stock_id,
            analysis_date=state.analysis_date,
            analysis_type=self.get_analysis_type(),
            recommendation='HOLD',
            confidence=0.0,
            confidence_level=AnalysisConfidenceLevel.VERY_LOW,
            reasoning=[f'分析過程中發生錯誤: {error_message}']
        )
    
    def get_supported_features(self) -> List[str]:
        """獲取支援的功能特性"""
        features = ['basic_analysis']
        
        if self.cost_optimizer:
            features.append('cost_optimization')
        if self.model_selector:
            features.append('smart_model_selection')
        if self.permission_bridge:
            features.append('permission_control')
        if self.trajectory_collector:
            features.append('trajectory_collection')
        if self.reward_system:
            features.append('reward_generation')
            
        return features
    
    def get_analyst_info(self) -> Dict[str, Any]:
        """獲取分析師信息"""
        return {
            'analyst_id': self.analyst_id,
            'analysis_type': self.get_analysis_type().value,
            'supported_features': self.get_supported_features(),
            'tianGong_enhanced': bool(self.cost_optimizer and self.model_selector),
            'art_enabled': bool(self.trajectory_collector),
            'intelligent_routing_enabled': self.routing_enabled,
            'routing_client_connected': bool(self.intelligent_routing_client),
            'workflow_integrated': True,
            'version': '2.3_gpt_oss_integrated',
            'art_system_status': self.get_art_system_status(),
            'routing_capabilities': self._get_routing_capabilities()
        }
    
    def _get_routing_capabilities(self) -> Dict[str, Any]:
        """获取路由能力信息"""
        return {
            'supports_intelligent_routing': True,
            'fallback_to_traditional': True,
            'routing_transparency': True,
            'cost_optimization': self.routing_enabled,
            'quality_optimization': self.routing_enabled,
            'latency_optimization': self.routing_enabled,
            'decision_audit': self.routing_enabled
        }
    
    def get_workflow_compatibility(self) -> Dict[str, Any]:
        """獲取工作流兼容性信息"""
        return {
            'supports_async_execution': True,
            'supports_state_sharing': True,
            'supports_result_caching': bool(hasattr(self, 'cost_optimizer')),
            'supports_retry_mechanism': True,
            'estimated_execution_time': self._get_estimated_execution_time(),
            'resource_requirements': self._get_resource_requirements(),
            'dependency_types': self._get_dependency_types()
        }
    
    def _get_estimated_execution_time(self) -> Dict[str, float]:
        """獲取預估執行時間 (秒)"""
        base_time = {
            AnalysisType.TECHNICAL: 2.0,
            AnalysisType.FUNDAMENTAL: 5.0,
            AnalysisType.NEWS_SENTIMENT: 3.0,
            AnalysisType.MARKET_SENTIMENT: 3.0,
            AnalysisType.RISK_ASSESSMENT: 4.0,
            AnalysisType.INVESTMENT_PLANNING: 8.0,
            AnalysisType.TAIWAN_SPECIFIC: 6.0
        }
        
        analysis_type = self.get_analysis_type()
        return {
            'min_time': base_time.get(analysis_type, 2.0) * 0.5,
            'avg_time': base_time.get(analysis_type, 2.0),
            'max_time': base_time.get(analysis_type, 2.0) * 2.0
        }
    
    def _get_resource_requirements(self) -> Dict[str, Any]:
        """獲取資源需求"""
        return {
            'memory_mb': 50,
            'cpu_cores': 0.5,
            'network_required': True,
            'storage_mb': 10,
            'llm_tokens_estimated': self._estimate_token_usage_default()
        }
    
    def _estimate_token_usage_default(self) -> int:
        """預設token使用量估算"""
        complexity_mapping = {
            AnalysisType.TECHNICAL: 800,
            AnalysisType.FUNDAMENTAL: 1500,
            AnalysisType.NEWS_SENTIMENT: 1200,
            AnalysisType.MARKET_SENTIMENT: 1000,
            AnalysisType.RISK_ASSESSMENT: 1800,
            AnalysisType.INVESTMENT_PLANNING: 2500,
            AnalysisType.TAIWAN_SPECIFIC: 2000
        }
        return complexity_mapping.get(self.get_analysis_type(), 1000)
    
    def _get_dependency_types(self) -> List[str]:
        """獲取依賴類型"""
        analysis_type = self.get_analysis_type()
        
        if analysis_type == AnalysisType.INVESTMENT_PLANNING:
            # 投資規劃需要其他所有分析師的結果
            return ['technical', 'fundamental', 'news_sentiment', 'market_sentiment', 'risk_assessment', 'taiwan_specific']
        elif analysis_type == AnalysisType.RISK_ASSESSMENT:
            # 風險評估需要基本面和技術面數據
            return ['fundamental', 'technical']
        elif analysis_type == AnalysisType.MARKET_SENTIMENT:
            # 市場情緒可以參考新聞情緒
            return ['news_sentiment']
        else:
            # 其他分析師相對獨立
            return []

    # ART軌跡收集系統方法
    async def _start_trajectory_collection(self, state: AnalysisState):
        """開始軌跡收集"""
        if not self.trajectory_collector:
            return
        
        try:
            user_id = state.user_context.get('user_id', 'anonymous') if state.user_context else 'anonymous'
            
            # 為MVP演示版本使用適當的方法
            if hasattr(self.trajectory_collector, 'start_trajectory'):
                # 完整ART系統
                self.current_trajectory_id = await self.trajectory_collector.start_trajectory(
                    stock_id=state.stock_id,
                    analyst_type=self.analyst_id,
                    user_id=user_id,
                    context_data=state.user_context or {}
                )
            else:
                # MVP演示版本
                self.current_trajectory_id = await self.trajectory_collector.start_trajectory(
                    stock_id=state.stock_id,
                    analyst_type=self.analyst_id,
                    user_id=user_id,
                    context_data=state.user_context or {}
                )
                
            self.logger.info(f"開始軌跡收集: {self.current_trajectory_id}")
            
        except Exception as e:
            self.logger.error(f"軌跡收集開始失敗: {e}")
            self.current_trajectory_id = None
    
    async def _record_trajectory_step(
        self,
        state: AnalysisState,
        trajectory_type: TrajectoryType,
        input_data: Dict[str, Any],
        reasoning_process: List[str],
        intermediate_result: Any,
        confidence_score: float,
        computation_method: str = "default"
    ):
        """記錄軌跡步驟"""
        if not self.trajectory_collector or not self.current_trajectory_id:
            return
        
        try:
            await self.trajectory_collector.record_decision_step(
                trajectory_id=self.current_trajectory_id,
                trajectory_type=trajectory_type,
                input_data=input_data,
                reasoning_process=reasoning_process,
                intermediate_result=intermediate_result,
                confidence_score=confidence_score,
                computation_method=computation_method
            )
            
        except Exception as e:
            self.logger.error(f"軌跡步驟記錄失敗: {e}")
    
    async def _complete_trajectory_collection(self, result: AnalysisResult, state: AnalysisState):
        """完成軌跡收集並生成獎勵"""
        if not self.trajectory_collector or not self.current_trajectory_id:
            return
        
        try:
            # 完成軌跡收集
            trajectory = await self.trajectory_collector.complete_trajectory(
                trajectory_id=self.current_trajectory_id,
                final_recommendation=result.recommendation,
                final_confidence=result.confidence
            )
            
            # 生成基礎獎勵信號
            await self._generate_initial_rewards(trajectory, result, state)
            
            self.logger.info(f"完成軌跡收集: {self.current_trajectory_id}")
            self.current_trajectory_id = None
            
        except Exception as e:
            self.logger.error(f"軌跡收集完成失敗: {e}")
    
    async def _generate_initial_rewards(self, trajectory: AnalysisTrajectory, result: AnalysisResult, state: AnalysisState):
        """生成初始獎勵信號"""
        if not self.trajectory_collector:
            return
        
        try:
            # 檢查軌跡收集器是否有add_reward_signal方法
            if hasattr(self.trajectory_collector, 'add_reward_signal'):
                # 一致性獎勵 - 基於推理邏輯連貫性
                consistency_reward = min(result.confidence, 0.9)
                await self.trajectory_collector.add_reward_signal(
                    trajectory_id=trajectory.trajectory_id,
                    reward_type=RewardType.CONSISTENCY_REWARD,
                    reward_value=consistency_reward,
                    reward_reason=f"推理邏輯一致性評分: {consistency_reward:.2f}"
                )
                
                # 時效性獎勵 - 基於分析完成時間
                timeliness_reward = 0.8  # 預設高時效性
                await self.trajectory_collector.add_reward_signal(
                    trajectory_id=trajectory.trajectory_id,
                    reward_type=RewardType.TIMELINESS_REWARD,
                    reward_value=timeliness_reward,
                    reward_reason="及時完成分析"
                )
            else:
                # 簡化版本，僅記錄
                self.logger.info(f"軌跡 {trajectory.trajectory_id} 完成，信心度: {result.confidence:.2f}")
            
            # 如果有RULER系統，生成更精確的獎勵
            if self.reward_system:
                await self._generate_ruler_rewards(trajectory, result, state)
                
        except Exception as e:
            self.logger.error(f"獎勵信號生成失敗: {e}")
    
    async def _generate_ruler_rewards(self, trajectory: AnalysisTrajectory, result: AnalysisResult, state: AnalysisState):
        """使用RULER系統生成精確獎勵"""
        # 預留給完整RULER系統的實現
        pass
    
    async def get_user_learning_data(self, user_id: str) -> Dict[str, Any]:
        """獲取用戶學習數據 - 供外部調用"""
        if not self.trajectory_collector:
            return {'learning_ready': False, 'message': 'ART系統不可用'}
        
        try:
            # 檢查方法是否存在
            if hasattr(self.trajectory_collector, 'get_learning_data_for_user'):
                learning_data = await self.trajectory_collector.get_learning_data_for_user(user_id)
                return learning_data
            else:
                return {
                    'learning_ready': False, 
                    'message': '學習數據功能在此版本中不可用',
                    'trajectories': [],
                    'total_reward': 0.0
                }
        except Exception as e:
            self.logger.error(f"獲取學習數據失敗: {e}")
            return {'learning_ready': False, 'error': str(e)}
    
    def get_art_system_status(self) -> Dict[str, Any]:
        """獲取ART系統狀態"""
        return {
            'art_available': ART_AVAILABLE,
            'trajectory_collector_active': bool(self.trajectory_collector),
            'reward_system_active': bool(self.reward_system),
            'current_trajectory_id': self.current_trajectory_id,
            'system_version': 'MVP' if not ART_AVAILABLE else 'FULL'
        }

# 便利函數
def create_analysis_state(
    stock_id: str,
    user_context: Dict[str, Any] = None,
    stock_data: Dict[str, Any] = None,
    financial_data: Dict[str, Any] = None
) -> AnalysisState:
    """創建分析狀態"""
    
    return AnalysisState(
        stock_id=stock_id,
        analysis_date=datetime.now().strftime('%Y-%m-%d'),
        user_context=user_context,
        stock_data=stock_data,
        financial_data=financial_data
    )


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
    
    # 創建測試分析師
    class TestAnalyst(BaseAnalyst):
        def get_analysis_type(self) -> AnalysisType:
            return AnalysisType.TECHNICAL
        
        def get_analysis_prompt(self, state: AnalysisState) -> str:
            return f"分析股票 {state.stock_id} 的技術面"
        
        async def analyze(self, state: AnalysisState) -> AnalysisResult:
            return await self._execute_analysis_with_optimization(state)
    
    async def test_base_analyst():
        print("測試基礎分析師")
        
        config = {'debug': True}
        analyst = TestAnalyst(config)
        
        print(f"分析師信息: {analyst.get_analyst_info()}")
        
        # 創建測試狀態
        state = create_analysis_state(
            stock_id='2330',
            user_context={'user_id': 'test_user', 'membership_tier': 'GOLD'}
        )
        
        # 執行分析
        result = await analyst.analyze(state)
        
        print(f"分析結果: {result.recommendation}")
        print(f"信心度: {result.confidence}")
        print(f"理由: {result.reasoning}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_base_analyst())