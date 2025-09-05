#!/usr/bin/env python3
"""
Decision Tracking System - 決策追踪系統
天工 (TianGong) - 為深度行為學習提供精細化的用戶決策追踪和分析

此模組提供：
1. 實時決策事件捕獲
2. 決策路徑分析
3. 決策品質評估
4. 決策模式識別
5. 決策影響預測
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
import uuid
import time
import numpy as np
from collections import defaultdict, deque
import hashlib
from pathlib import Path

class DecisionType(Enum):
    """決策類型"""
    TRADE_EXECUTION = "trade_execution"          # 交易執行決策
    POSITION_SIZING = "position_sizing"          # 倉位大小決策
    RISK_MANAGEMENT = "risk_management"          # 風險管理決策
    PORTFOLIO_ALLOCATION = "portfolio_allocation" # 組合配置決策
    MARKET_TIMING = "market_timing"              # 市場時機決策
    INFORMATION_FILTERING = "information_filtering" # 信息篩選決策
    STRATEGY_SELECTION = "strategy_selection"     # 策略選擇決策
    ANALYSIS_FOCUS = "analysis_focus"            # 分析重點決策

class DecisionContext(Enum):
    """決策情境"""
    NORMAL_MARKET = "normal_market"              # 正常市場
    VOLATILE_MARKET = "volatile_market"          # 波動市場
    TRENDING_MARKET = "trending_market"          # 趨勢市場
    SIDEWAYS_MARKET = "sideways_market"          # 橫盤市場
    NEWS_EVENT = "news_event"                    # 新聞事件
    EARNINGS_SEASON = "earnings_season"          # 財報季
    REGULATORY_CHANGE = "regulatory_change"      # 監管變化
    ECONOMIC_INDICATOR = "economic_indicator"    # 經濟指標

class DecisionQuality(Enum):
    """決策品質"""
    EXCELLENT = "excellent"      # 優秀 (>90%)
    GOOD = "good"               # 良好 (70-90%)
    AVERAGE = "average"         # 一般 (50-70%)
    POOR = "poor"              # 不佳 (30-50%)
    VERY_POOR = "very_poor"    # 很差 (<30%)

@dataclass
class DecisionEvent:
    """決策事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    timestamp: float = field(default_factory=time.time)
    decision_type: DecisionType = DecisionType.TRADE_EXECUTION
    decision_context: DecisionContext = DecisionContext.NORMAL_MARKET
    
    # 決策輸入
    available_information: Dict[str, Any] = field(default_factory=dict)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    user_state: Dict[str, Any] = field(default_factory=dict)  # 情緒、風險承受度等
    portfolio_state: Dict[str, Any] = field(default_factory=dict)
    
    # 決策過程
    consideration_time: float = 0.0              # 考慮時間(秒)
    information_sources_consulted: List[str] = field(default_factory=list)
    analysis_methods_used: List[str] = field(default_factory=list)
    alternatives_considered: List[Dict[str, Any]] = field(default_factory=list)
    decision_confidence: float = 0.0             # 決策信心度
    
    # 決策輸出
    final_decision: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    
    # 決策執行
    execution_delay: float = 0.0                 # 執行延遲(秒)
    execution_quality: float = 0.0               # 執行品質
    execution_slippage: float = 0.0              # 執行滑點
    
    # 決策結果(事後填入)
    actual_outcome: Optional[Dict[str, Any]] = None
    outcome_timestamp: Optional[float] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    decision_quality_score: Optional[float] = None
    decision_quality_grade: Optional[DecisionQuality] = None
    
    # 學習數據
    lessons_learned: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # 元數據
    session_id: str = ""
    device_info: Dict[str, Any] = field(default_factory=dict)
    network_conditions: Dict[str, Any] = field(default_factory=dict)
    system_version: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionPattern:
    """決策模式"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_name: str = ""
    user_id: str = ""
    
    # 模式特徵
    decision_types: List[DecisionType] = field(default_factory=list)
    typical_contexts: List[DecisionContext] = field(default_factory=list)
    average_consideration_time: float = 0.0
    preferred_information_sources: List[str] = field(default_factory=list)
    common_analysis_methods: List[str] = field(default_factory=list)
    
    # 模式指標
    frequency: int = 0                           # 出現頻率
    success_rate: float = 0.0                   # 成功率
    average_performance: float = 0.0            # 平均表現
    risk_level: float = 0.0                     # 風險水平
    consistency_score: float = 0.0              # 一致性分數
    
    # 模式演化
    first_observed: float = field(default_factory=time.time)
    last_observed: float = field(default_factory=time.time)
    evolution_trend: str = "stable"             # stable, improving, declining
    adaptation_rate: float = 0.0                # 適應速度
    
    # 關聯模式
    related_patterns: List[str] = field(default_factory=list)
    triggering_conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DecisionPathway:
    """決策路徑"""
    pathway_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    start_timestamp: float = field(default_factory=time.time)
    end_timestamp: Optional[float] = None
    
    # 路徑組成
    decision_sequence: List[str] = field(default_factory=list)  # 決策事件ID序列
    pathway_type: str = "linear"                # linear, branched, cyclic
    complexity_score: float = 0.0              # 複雜度分數
    
    # 路徑特徵
    total_duration: float = 0.0                 # 總持續時間
    decision_count: int = 0                     # 決策數量
    information_gathering_ratio: float = 0.0    # 信息收集比重
    analysis_depth_score: float = 0.0          # 分析深度分數
    
    # 路徑效率
    efficiency_score: float = 0.0              # 效率分數
    redundancy_level: float = 0.0              # 冗余水平
    optimization_potential: float = 0.0        # 優化潛力
    
    # 路徑結果
    pathway_success: bool = False               # 路徑是否成功
    final_outcome: Dict[str, Any] = field(default_factory=dict)
    cumulative_performance: float = 0.0        # 累積績效
    
    metadata: Dict[str, Any] = field(default_factory=dict)

class DecisionTracker:
    """決策追踪器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 存儲配置
        self.storage_path = Path(self.config.get('storage_path', './decision_data'))
        self.storage_path.mkdir(exist_ok=True)
        
        # 追踪數據
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.decision_events: Dict[str, DecisionEvent] = {}
        self.decision_patterns: Dict[str, List[DecisionPattern]] = defaultdict(list)
        self.decision_pathways: Dict[str, List[DecisionPathway]] = defaultdict(list)
        
        # 追踪配置
        self.tracking_config = {
            'max_consideration_time': self.config.get('max_consideration_time', 3600),  # 1小時
            'min_confidence_threshold': self.config.get('min_confidence_threshold', 0.1),
            'pattern_recognition_window': self.config.get('pattern_recognition_window', 30),  # 30天
            'pathway_timeout': self.config.get('pathway_timeout', 7200),  # 2小時
            'auto_quality_assessment': self.config.get('auto_quality_assessment', True)
        }
        
        # 實時分析
        self.real_time_analysis = self.config.get('real_time_analysis', True)
        self.analysis_queue: deque = deque(maxlen=1000)
        
        self.logger.info("DecisionTracker initialized")

    async def start_decision_session(
        self, 
        user_id: str, 
        session_context: Dict[str, Any] = None
    ) -> str:
        """開始決策會話"""
        
        session_id = f"session_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        session_data = {
            'session_id': session_id,
            'user_id': user_id,
            'start_time': time.time(),
            'context': session_context or {},
            'active_decisions': [],
            'session_state': 'active'
        }
        
        self.active_sessions[session_id] = session_data
        
        self.logger.info(f"開始決策會話: {session_id} for user {user_id}")
        return session_id

    async def track_decision_event(
        self, 
        session_id: str,
        decision_type: DecisionType,
        decision_context: DecisionContext,
        decision_data: Dict[str, Any]
    ) -> str:
        """追踪決策事件"""
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found or inactive")
        
        session = self.active_sessions[session_id]
        user_id = session['user_id']
        
        # 創建決策事件
        event = DecisionEvent(
            user_id=user_id,
            decision_type=decision_type,
            decision_context=decision_context,
            session_id=session_id
        )
        
        # 填入決策數據
        event.available_information = decision_data.get('available_information', {})
        event.market_conditions = decision_data.get('market_conditions', {})
        event.user_state = decision_data.get('user_state', {})
        event.portfolio_state = decision_data.get('portfolio_state', {})
        
        event.consideration_time = decision_data.get('consideration_time', 0.0)
        event.information_sources_consulted = decision_data.get('information_sources', [])
        event.analysis_methods_used = decision_data.get('analysis_methods', [])
        event.alternatives_considered = decision_data.get('alternatives', [])
        event.decision_confidence = decision_data.get('confidence', 0.0)
        
        event.final_decision = decision_data.get('final_decision', {})
        event.expected_outcome = decision_data.get('expected_outcome', {})
        event.risk_assessment = decision_data.get('risk_assessment', {})
        
        event.execution_delay = decision_data.get('execution_delay', 0.0)
        event.execution_quality = decision_data.get('execution_quality', 0.0)
        event.execution_slippage = decision_data.get('execution_slippage', 0.0)
        
        # 存儲事件
        self.decision_events[event.event_id] = event
        session['active_decisions'].append(event.event_id)
        
        # 實時分析
        if self.real_time_analysis:
            self.analysis_queue.append(event.event_id)
            asyncio.create_task(self._analyze_decision_real_time(event.event_id))
        
        self.logger.info(f"追踪決策事件: {event.event_id} 類型: {decision_type.value}")
        return event.event_id

    async def update_decision_outcome(
        self, 
        event_id: str, 
        outcome_data: Dict[str, Any]
    ):
        """更新決策結果"""
        
        if event_id not in self.decision_events:
            raise ValueError(f"Decision event {event_id} not found")
        
        event = self.decision_events[event_id]
        
        # 更新結果數據
        event.actual_outcome = outcome_data.get('actual_outcome', {})
        event.outcome_timestamp = outcome_data.get('timestamp', time.time())
        event.performance_metrics = outcome_data.get('performance_metrics', {})
        
        # 自動品質評估
        if self.tracking_config['auto_quality_assessment']:
            quality_score = await self._assess_decision_quality(event)
            event.decision_quality_score = quality_score
            event.decision_quality_grade = self._score_to_grade(quality_score)
        
        # 生成學習建議
        lessons, improvements = await self._generate_learning_insights(event)
        event.lessons_learned = lessons
        event.improvement_suggestions = improvements
        
        # 模式更新
        await self._update_decision_patterns(event.user_id, event)
        
        self.logger.info(f"更新決策結果: {event_id} 品質分數: {event.decision_quality_score}")

    async def _assess_decision_quality(self, event: DecisionEvent) -> float:
        """評估決策品質"""
        
        quality_factors = []
        
        # 績效因子
        if event.performance_metrics:
            performance_score = event.performance_metrics.get('return_ratio', 0)
            risk_adjusted_score = event.performance_metrics.get('sharpe_ratio', 0)
            quality_factors.append(min(max(performance_score, 0), 1) * 0.4)
            quality_factors.append(min(max(risk_adjusted_score, 0), 1) * 0.2)
        
        # 執行品質因子
        if event.execution_quality > 0:
            quality_factors.append(event.execution_quality * 0.2)
        
        # 決策過程因子
        if event.decision_confidence > 0:
            quality_factors.append(event.decision_confidence * 0.1)
        
        # 風險管控因子
        if event.risk_assessment and event.actual_outcome:
            predicted_risk = event.risk_assessment.get('expected_risk', 0)
            actual_risk = event.actual_outcome.get('realized_risk', 0)
            risk_accuracy = 1 - abs(predicted_risk - actual_risk)
            quality_factors.append(max(risk_accuracy, 0) * 0.1)
        
        # 計算總分
        if quality_factors:
            total_score = sum(quality_factors)
            return min(max(total_score, 0), 1)
        else:
            return 0.5  # 默認中等分數

    def _score_to_grade(self, score: float) -> DecisionQuality:
        """分數轉品質等級"""
        if score >= 0.9:
            return DecisionQuality.EXCELLENT
        elif score >= 0.7:
            return DecisionQuality.GOOD
        elif score >= 0.5:
            return DecisionQuality.AVERAGE
        elif score >= 0.3:
            return DecisionQuality.POOR
        else:
            return DecisionQuality.VERY_POOR

    async def _generate_learning_insights(
        self, 
        event: DecisionEvent
    ) -> Tuple[List[str], List[str]]:
        """生成學習洞察"""
        
        lessons = []
        improvements = []
        
        # 基於決策品質的洞察
        if event.decision_quality_score:
            if event.decision_quality_score >= 0.8:
                lessons.append("決策執行良好，可以作為未來類似情況的參考")
                improvements.append("保持當前決策模式和風險控制水平")
            elif event.decision_quality_score < 0.4:
                lessons.append("此次決策存在明顯問題，需要深入分析原因")
                improvements.append("檢討決策依據和執行過程，加強風險評估")
        
        # 基於執行效率的洞察
        if event.consideration_time > 0:
            if event.consideration_time > 1800:  # 超過30分鐘
                lessons.append("決策考慮時間較長，可能存在分析過度的情況")
                improvements.append("建立決策時限和關鍵因素優先級")
            elif event.consideration_time < 60:  # 少於1分鐘
                lessons.append("決策時間較短，需要確認是否充分考慮風險")
                improvements.append("增加必要的分析環節和風險檢查")
        
        # 基於信心度的洞察
        if event.decision_confidence > 0:
            if event.decision_confidence < 0.3 and event.decision_quality_score and event.decision_quality_score > 0.7:
                lessons.append("低信心度但結果良好，可能存在過度謹慎")
                improvements.append("回顧分析過程，建立信心度標準")
            elif event.decision_confidence > 0.8 and event.decision_quality_score and event.decision_quality_score < 0.3:
                lessons.append("高信心度但結果不佳，可能存在過度自信")
                improvements.append("加強反向思考和風險評估環節")
        
        return lessons, improvements

    async def _update_decision_patterns(self, user_id: str, event: DecisionEvent):
        """更新決策模式"""
        
        # 查找匹配的現有模式
        user_patterns = self.decision_patterns[user_id]
        matching_pattern = None
        
        for pattern in user_patterns:
            if (event.decision_type in pattern.decision_types and
                event.decision_context in pattern.typical_contexts):
                matching_pattern = pattern
                break
        
        if matching_pattern:
            # 更新現有模式
            matching_pattern.frequency += 1
            matching_pattern.last_observed = event.timestamp
            
            # 更新性能指標
            if event.decision_quality_score is not None:
                current_avg = matching_pattern.average_performance
                count = matching_pattern.frequency
                new_avg = ((current_avg * (count - 1)) + event.decision_quality_score) / count
                matching_pattern.average_performance = new_avg
                
                # 更新成功率
                if event.decision_quality_score >= 0.6:  # 成功閾值
                    matching_pattern.success_rate = (
                        (matching_pattern.success_rate * (count - 1) + 1) / count
                    )
                else:
                    matching_pattern.success_rate = (
                        matching_pattern.success_rate * (count - 1) / count
                    )
        
        else:
            # 創建新模式
            new_pattern = DecisionPattern(
                pattern_name=f"{event.decision_type.value}_{event.decision_context.value}_pattern",
                user_id=user_id,
                decision_types=[event.decision_type],
                typical_contexts=[event.decision_context],
                frequency=1,
                first_observed=event.timestamp,
                last_observed=event.timestamp
            )
            
            if event.decision_quality_score is not None:
                new_pattern.average_performance = event.decision_quality_score
                new_pattern.success_rate = 1.0 if event.decision_quality_score >= 0.6 else 0.0
            
            user_patterns.append(new_pattern)

    async def _analyze_decision_real_time(self, event_id: str):
        """實時決策分析"""
        
        try:
            event = self.decision_events[event_id]
            
            # 異常決策檢測
            await self._detect_decision_anomalies(event)
            
            # 決策效率分析
            await self._analyze_decision_efficiency(event)
            
            # 風險預警
            await self._risk_early_warning(event)
            
        except Exception as e:
            self.logger.error(f"實時決策分析失敗: {e}")

    async def _detect_decision_anomalies(self, event: DecisionEvent):
        """檢測決策異常"""
        
        user_id = event.user_id
        user_patterns = self.decision_patterns[user_id]
        
        # 檢查決策時間異常
        if user_patterns:
            avg_consideration_time = np.mean([p.average_consideration_time for p in user_patterns if p.average_consideration_time > 0])
            if avg_consideration_time > 0:
                if event.consideration_time > avg_consideration_time * 3:
                    self.logger.warning(f"用戶 {user_id} 決策時間異常延長: {event.consideration_time:.1f}s")
                elif event.consideration_time < avg_consideration_time * 0.1:
                    self.logger.warning(f"用戶 {user_id} 決策時間異常縮短: {event.consideration_time:.1f}s")
        
        # 檢查信心度異常
        if event.decision_confidence < 0.1:
            self.logger.warning(f"用戶 {user_id} 決策信心度極低: {event.decision_confidence}")
        elif event.decision_confidence > 0.95:
            self.logger.warning(f"用戶 {user_id} 決策信心度異常高: {event.decision_confidence}")

    async def _analyze_decision_efficiency(self, event: DecisionEvent):
        """分析決策效率"""
        
        # 計算信息利用效率
        info_count = len(event.information_sources_consulted)
        analysis_count = len(event.analysis_methods_used)
        
        if info_count > 0 and event.consideration_time > 0:
            info_efficiency = info_count / event.consideration_time * 60  # 每分鐘信息量
            if info_efficiency < 0.5:
                self.logger.info(f"決策 {event.event_id} 信息處理效率較低: {info_efficiency:.2f}")

    async def _risk_early_warning(self, event: DecisionEvent):
        """風險預警"""
        
        # 檢查高風險決策
        if event.risk_assessment:
            estimated_risk = event.risk_assessment.get('estimated_risk', 0)
            if estimated_risk > 0.8:
                self.logger.warning(f"高風險決策警告: {event.event_id} 風險度: {estimated_risk}")
        
        # 檢查執行滑點
        if event.execution_slippage > 0.05:  # 5%以上滑點
            self.logger.warning(f"執行滑點過高: {event.event_id} 滑點: {event.execution_slippage:.2%}")

    async def end_decision_session(self, session_id: str):
        """結束決策會話"""
        
        if session_id not in self.active_sessions:
            return
        
        session = self.active_sessions[session_id]
        session['end_time'] = time.time()
        session['session_state'] = 'completed'
        session['duration'] = session['end_time'] - session['start_time']
        
        # 構建決策路徑
        if session['active_decisions']:
            pathway = await self._build_decision_pathway(session)
            self.decision_pathways[session['user_id']].append(pathway)
        
        # 存檔會話數據
        await self._archive_session(session_id)
        
        # 清理活躍會話
        del self.active_sessions[session_id]
        
        self.logger.info(f"結束決策會話: {session_id}")

    async def _build_decision_pathway(self, session: Dict[str, Any]) -> DecisionPathway:
        """構建決策路徑"""
        
        pathway = DecisionPathway(
            user_id=session['user_id'],
            start_timestamp=session['start_time'],
            end_timestamp=session['end_time'],
            decision_sequence=session['active_decisions'],
            decision_count=len(session['active_decisions']),
            total_duration=session['duration']
        )
        
        # 計算路徑特徵
        if session['active_decisions']:
            decision_events = [self.decision_events[event_id] for event_id in session['active_decisions']]
            
            # 分析深度分數
            total_analysis_methods = sum(len(event.analysis_methods_used) for event in decision_events)
            pathway.analysis_depth_score = total_analysis_methods / len(decision_events)
            
            # 信息收集比重
            total_info_sources = sum(len(event.information_sources_consulted) for event in decision_events)
            total_consideration_time = sum(event.consideration_time for event in decision_events)
            if total_consideration_time > 0:
                pathway.information_gathering_ratio = total_info_sources / total_consideration_time * 60
            
            # 效率分數
            avg_decision_time = total_consideration_time / len(decision_events)
            pathway.efficiency_score = 1.0 / (1.0 + avg_decision_time / 300)  # 基於5分鐘標準
        
        return pathway

    async def _archive_session(self, session_id: str):
        """存檔會話數據"""
        
        try:
            session_data = self.active_sessions[session_id]
            session_file = self.storage_path / f"session_{session_id}.json"
            
            # 準備存檔數據
            archive_data = {
                'session_info': session_data,
                'decision_events': {
                    event_id: self._serialize_decision_event(self.decision_events[event_id])
                    for event_id in session_data['active_decisions']
                    if event_id in self.decision_events
                }
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(archive_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"存檔會話數據失敗: {e}")

    def _serialize_decision_event(self, event: DecisionEvent) -> Dict[str, Any]:
        """序列化決策事件"""
        
        data = {
            'event_id': event.event_id,
            'user_id': event.user_id,
            'timestamp': event.timestamp,
            'decision_type': event.decision_type.value,
            'decision_context': event.decision_context.value,
            'available_information': event.available_information,
            'market_conditions': event.market_conditions,
            'user_state': event.user_state,
            'portfolio_state': event.portfolio_state,
            'consideration_time': event.consideration_time,
            'information_sources_consulted': event.information_sources_consulted,
            'analysis_methods_used': event.analysis_methods_used,
            'alternatives_considered': event.alternatives_considered,
            'decision_confidence': event.decision_confidence,
            'final_decision': event.final_decision,
            'expected_outcome': event.expected_outcome,
            'risk_assessment': event.risk_assessment,
            'execution_delay': event.execution_delay,
            'execution_quality': event.execution_quality,
            'execution_slippage': event.execution_slippage,
            'actual_outcome': event.actual_outcome,
            'outcome_timestamp': event.outcome_timestamp,
            'performance_metrics': event.performance_metrics,
            'decision_quality_score': event.decision_quality_score,
            'decision_quality_grade': event.decision_quality_grade.value if event.decision_quality_grade else None,
            'lessons_learned': event.lessons_learned,
            'improvement_suggestions': event.improvement_suggestions,
            'session_id': event.session_id,
            'metadata': event.metadata
        }
        
        return data

    def get_user_decision_patterns(self, user_id: str) -> List[DecisionPattern]:
        """獲取用戶決策模式"""
        return self.decision_patterns.get(user_id, [])

    def get_user_decision_pathways(self, user_id: str) -> List[DecisionPathway]:
        """獲取用戶決策路徑"""
        return self.decision_pathways.get(user_id, [])

    def get_decision_event(self, event_id: str) -> Optional[DecisionEvent]:
        """獲取決策事件"""
        return self.decision_events.get(event_id)