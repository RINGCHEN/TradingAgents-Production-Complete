#!/usr/bin/env python3
"""
Group Intelligence Learning - 群體智慧學習系統
天工 (TianGong) - 集體智慧驅動的多模態學習優化系統

此模組提供：
1. 集體學習和知識共享
2. 群體決策優化
3. 分散式模型訓練
4. 共識機制和投票系統
5. 知識蒸餾和模型融合
"""

from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import numpy as np
import pandas as pd
import json
import time
import uuid
from collections import defaultdict, deque, Counter
import pickle
import hashlib
from concurrent.futures import ThreadPoolExecutor
import threading

class LearningMode(Enum):
    """學習模式"""
    FEDERATED = "federated"         # 聯邦學習
    ENSEMBLE = "ensemble"           # 集成學習
    COLLABORATIVE = "collaborative" # 協作學習
    COMPETITIVE = "competitive"     # 競爭學習
    SWARM = "swarm"                # 群體智能

class ConsensusMethod(Enum):
    """共識方法"""
    MAJORITY_VOTE = "majority_vote"         # 多數投票
    WEIGHTED_VOTE = "weighted_vote"         # 權重投票
    BAYESIAN_CONSENSUS = "bayesian_consensus" # 貝葉斯共識
    DELPHI_METHOD = "delphi_method"         # 德爾菲法
    WISDOM_OF_CROWDS = "wisdom_of_crowds"   # 群眾智慧

class ParticipantRole(Enum):
    """參與者角色"""
    LEARNER = "learner"             # 學習者
    TEACHER = "teacher"             # 教師
    VALIDATOR = "validator"         # 驗證者
    COORDINATOR = "coordinator"     # 協調者
    OBSERVER = "observer"           # 觀察者

@dataclass
class LearningParticipant:
    """學習參與者"""
    participant_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    participant_name: str = ""
    role: ParticipantRole = ParticipantRole.LEARNER
    expertise_domains: List[str] = field(default_factory=list)
    
    # 性能指標
    accuracy_history: List[float] = field(default_factory=list)
    contribution_score: float = 0.0
    trust_score: float = 1.0
    reputation: float = 0.5
    
    # 參與統計
    total_predictions: int = 0
    correct_predictions: int = 0
    participation_count: int = 0
    last_active: datetime = field(default_factory=datetime.now)
    
    # 學習狀態
    model_version: str = "v1.0"
    knowledge_base: Dict[str, Any] = field(default_factory=dict)
    learning_rate: float = 0.01
    
    def update_accuracy(self, prediction_result: bool):
        """更新準確率"""
        self.total_predictions += 1
        if prediction_result:
            self.correct_predictions += 1
        
        current_accuracy = self.correct_predictions / self.total_predictions
        self.accuracy_history.append(current_accuracy)
        
        # 保持歷史記錄在合理範圍內
        if len(self.accuracy_history) > 100:
            self.accuracy_history = self.accuracy_history[-50:]
    
    def get_current_accuracy(self) -> float:
        """獲取當前準確率"""
        if self.total_predictions == 0:
            return 0.5
        return self.correct_predictions / self.total_predictions
    
    def calculate_expertise_weight(self, domain: str) -> float:
        """計算領域專業度權重"""
        if domain in self.expertise_domains:
            return min(self.trust_score * self.reputation, 1.0)
        return self.reputation * 0.5

@dataclass
class GroupLearningTask:
    """群體學習任務"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_name: str = ""
    description: str = ""
    domain: str = ""
    
    # 任務配置
    learning_mode: LearningMode = LearningMode.COLLABORATIVE
    consensus_method: ConsensusMethod = ConsensusMethod.WEIGHTED_VOTE
    min_participants: int = 3
    max_participants: int = 50
    
    # 數據和目標
    training_data: List[Dict[str, Any]] = field(default_factory=list)
    target_metrics: Dict[str, float] = field(default_factory=dict)
    success_criteria: Dict[str, float] = field(default_factory=dict)
    
    # 參與者管理
    participants: List[str] = field(default_factory=list)  # participant_ids
    participant_weights: Dict[str, float] = field(default_factory=dict)
    
    # 任務狀態
    status: str = "created"  # created, active, completed, failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # 結果追蹤
    group_predictions: List[Dict[str, Any]] = field(default_factory=list)
    individual_predictions: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    consensus_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # 學習進度
    learning_iterations: int = 0
    convergence_threshold: float = 0.01
    has_converged: bool = False

@dataclass
class ConsensusResult:
    """共識結果"""
    task_id: str
    prediction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 共識決策
    final_prediction: Any = None
    confidence: float = 0.0
    agreement_level: float = 0.0
    
    # 參與者貢獻
    participant_votes: Dict[str, Any] = field(default_factory=dict)
    participant_weights: Dict[str, float] = field(default_factory=dict)
    dissenting_opinions: List[Dict[str, Any]] = field(default_factory=list)
    
    # 統計信息
    voting_participants: int = 0
    consensus_method_used: ConsensusMethod = ConsensusMethod.MAJORITY_VOTE
    computation_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

class GroupIntelligenceSystem:
    """群體智慧學習系統"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 參與者管理
        self.participants: Dict[str, LearningParticipant] = {}
        self.participant_connections: Dict[str, List[str]] = defaultdict(list)  # 參與者網絡
        
        # 任務管理
        self.active_tasks: Dict[str, GroupLearningTask] = {}
        self.completed_tasks: List[GroupLearningTask] = []
        
        # 知識庫
        self.collective_knowledge: Dict[str, Any] = {}
        self.domain_expertise: Dict[str, Dict[str, float]] = defaultdict(dict)  # domain -> participant -> expertise
        
        # 共識機制
        self.consensus_history: List[ConsensusResult] = []
        self.disagreement_patterns: Dict[str, int] = defaultdict(int)
        
        # 學習配置
        self.learning_modes = {
            LearningMode.FEDERATED: self._federated_learning,
            LearningMode.ENSEMBLE: self._ensemble_learning,
            LearningMode.COLLABORATIVE: self._collaborative_learning,
            LearningMode.COMPETITIVE: self._competitive_learning,
            LearningMode.SWARM: self._swarm_intelligence
        }
        
        self.consensus_methods = {
            ConsensusMethod.MAJORITY_VOTE: self._majority_vote_consensus,
            ConsensusMethod.WEIGHTED_VOTE: self._weighted_vote_consensus,
            ConsensusMethod.BAYESIAN_CONSENSUS: self._bayesian_consensus,
            ConsensusMethod.WISDOM_OF_CROWDS: self._wisdom_of_crowds_consensus
        }
        
        # 性能監控
        self.system_metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.performance_history: Dict[str, List[float]] = defaultdict(list)
        
        # 執行器
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.learning_tasks: Dict[str, asyncio.Task] = {}
        
        # 同步機制
        self.learning_lock = threading.Lock()
        
        self.logger.info("GroupIntelligenceSystem initialized")
    
    async def register_participant(
        self,
        participant_name: str,
        role: ParticipantRole = ParticipantRole.LEARNER,
        expertise_domains: List[str] = None,
        initial_config: Dict[str, Any] = None
    ) -> str:
        """
        註冊新參與者
        
        Args:
            participant_name: 參與者名稱
            role: 參與者角色
            expertise_domains: 專業領域列表
            initial_config: 初始配置
            
        Returns:
            參與者ID
        """
        try:
            participant = LearningParticipant(
                participant_name=participant_name,
                role=role,
                expertise_domains=expertise_domains or []
            )
            
            # 應用初始配置
            if initial_config:
                for key, value in initial_config.items():
                    if hasattr(participant, key):
                        setattr(participant, key, value)
            
            # 註冊參與者
            self.participants[participant.participant_id] = participant
            
            # 初始化專業度記錄
            for domain in participant.expertise_domains:
                self.domain_expertise[domain][participant.participant_id] = 0.5
            
            self.logger.info(f"參與者註冊成功: {participant_name} ({participant.participant_id})")
            return participant.participant_id
            
        except Exception as e:
            self.logger.error(f"參與者註冊失敗: {e}")
            raise
    
    async def create_learning_task(
        self,
        task_name: str,
        description: str,
        domain: str,
        learning_mode: LearningMode = LearningMode.COLLABORATIVE,
        consensus_method: ConsensusMethod = ConsensusMethod.WEIGHTED_VOTE,
        task_config: Dict[str, Any] = None
    ) -> str:
        """
        創建群體學習任務
        
        Args:
            task_name: 任務名稱
            description: 任務描述
            domain: 任務領域
            learning_mode: 學習模式
            consensus_method: 共識方法
            task_config: 任務配置
            
        Returns:
            任務ID
        """
        try:
            task = GroupLearningTask(
                task_name=task_name,
                description=description,
                domain=domain,
                learning_mode=learning_mode,
                consensus_method=consensus_method
            )
            
            # 應用配置
            if task_config:
                for key, value in task_config.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
            
            # 自動選擇合適的參與者
            suitable_participants = await self._select_participants_for_task(task)
            task.participants = suitable_participants
            
            # 計算參與者權重
            task.participant_weights = await self._calculate_participant_weights(task)
            
            # 註冊任務
            self.active_tasks[task.task_id] = task
            
            self.logger.info(f"學習任務創建成功: {task_name} ({task.task_id})")
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"學習任務創建失敗: {e}")
            raise
    
    async def _select_participants_for_task(self, task: GroupLearningTask) -> List[str]:
        """為任務選擇合適的參與者"""
        suitable_participants = []
        
        try:
            # 按領域專業度排序參與者
            domain_experts = []
            for participant_id, participant in self.participants.items():
                if task.domain in participant.expertise_domains:
                    expertise_score = self.domain_expertise[task.domain].get(participant_id, 0.5)
                    domain_experts.append((participant_id, expertise_score * participant.trust_score))
            
            # 如果領域專家不足，添加通用參與者
            if len(domain_experts) < task.min_participants:
                general_participants = [
                    (participant_id, participant.reputation * participant.trust_score)
                    for participant_id, participant in self.participants.items()
                    if participant_id not in [p[0] for p in domain_experts]
                ]
                
                # 按信譽分數排序
                general_participants.sort(key=lambda x: x[1], reverse=True)
                domain_experts.extend(general_participants[:task.min_participants - len(domain_experts)])
            
            # 按分數排序並選擇前N個
            domain_experts.sort(key=lambda x: x[1], reverse=True)
            suitable_participants = [p[0] for p in domain_experts[:task.max_participants]]
            
            return suitable_participants
            
        except Exception as e:
            self.logger.warning(f"參與者選擇失敗: {e}")
            return list(self.participants.keys())[:task.max_participants]
    
    async def _calculate_participant_weights(self, task: GroupLearningTask) -> Dict[str, float]:
        """計算參與者權重"""
        weights = {}
        
        try:
            total_weight = 0.0
            
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 基礎權重：準確率 × 信任度 × 聲譽
                base_weight = (
                    participant.get_current_accuracy() * 0.4 +
                    participant.trust_score * 0.3 +
                    participant.reputation * 0.3
                )
                
                # 領域專業度加權
                domain_weight = participant.calculate_expertise_weight(task.domain)
                
                # 角色權重
                role_weights = {
                    ParticipantRole.TEACHER: 1.2,
                    ParticipantRole.VALIDATOR: 1.1,
                    ParticipantRole.LEARNER: 1.0,
                    ParticipantRole.OBSERVER: 0.5
                }
                
                role_weight = role_weights.get(participant.role, 1.0)
                
                # 最終權重
                final_weight = base_weight * domain_weight * role_weight
                weights[participant_id] = final_weight
                total_weight += final_weight
            
            # 標準化權重
            if total_weight > 0:
                for participant_id in weights:
                    weights[participant_id] /= total_weight
            
        except Exception as e:
            self.logger.error(f"權重計算失敗: {e}")
            # 均等權重作為備選
            num_participants = len(task.participants)
            if num_participants > 0:
                equal_weight = 1.0 / num_participants
                weights = {pid: equal_weight for pid in task.participants}
        
        return weights
    
    async def start_learning_task(self, task_id: str) -> bool:
        """啟動學習任務"""
        try:
            if task_id not in self.active_tasks:
                raise ValueError(f"任務不存在: {task_id}")
            
            task = self.active_tasks[task_id]
            
            if task.status != "created":
                raise ValueError(f"任務狀態錯誤: {task.status}")
            
            # 檢查參與者數量
            if len(task.participants) < task.min_participants:
                raise ValueError(f"參與者數量不足: {len(task.participants)} < {task.min_participants}")
            
            # 更新任務狀態
            task.status = "active"
            task.start_time = datetime.now()
            
            # 啟動學習循環
            learning_task = asyncio.create_task(self._run_learning_loop(task_id))
            self.learning_tasks[task_id] = learning_task
            
            self.logger.info(f"學習任務啟動: {task.task_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"學習任務啟動失敗: {e}")
            return False
    
    async def _run_learning_loop(self, task_id: str):
        """運行學習循環"""
        try:
            task = self.active_tasks[task_id]
            
            while task.status == "active" and not task.has_converged:
                # 執行學習迭代
                iteration_success = await self._execute_learning_iteration(task)
                
                if not iteration_success:
                    self.logger.warning(f"學習迭代失敗: {task_id}")
                    break
                
                task.learning_iterations += 1
                
                # 檢查收斂條件
                has_converged = await self._check_convergence(task)
                if has_converged:
                    task.has_converged = True
                    break
                
                # 檢查是否達到最大迭代次數
                max_iterations = self.config.get('max_learning_iterations', 100)
                if task.learning_iterations >= max_iterations:
                    break
                
                # 等待下一次迭代
                await asyncio.sleep(self.config.get('learning_iteration_interval', 5))
            
            # 完成任務
            await self._complete_learning_task(task_id)
            
        except Exception as e:
            self.logger.error(f"學習循環錯誤: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = "failed"
    
    async def _execute_learning_iteration(self, task: GroupLearningTask) -> bool:
        """執行學習迭代"""
        try:
            # 根據學習模式執行不同的學習策略
            learning_method = self.learning_modes.get(task.learning_mode)
            
            if not learning_method:
                self.logger.error(f"未知的學習模式: {task.learning_mode}")
                return False
            
            # 執行學習方法
            iteration_results = await learning_method(task)
            
            # 如果有新的預測數據，進行共識決策
            if iteration_results.get('predictions'):
                consensus_result = await self._reach_consensus(
                    task, iteration_results['predictions']
                )
                task.consensus_results.append(consensus_result.__dict__)
            
            # 更新參與者性能
            await self._update_participant_performance(task, iteration_results)
            
            # 記錄系統指標
            self._record_system_metrics(task, iteration_results)
            
            return True
            
        except Exception as e:
            self.logger.error(f"學習迭代執行失敗: {e}")
            return False
    
    async def _federated_learning(self, task: GroupLearningTask) -> Dict[str, Any]:
        """聯邦學習"""
        try:
            results = {
                'method': 'federated_learning',
                'predictions': {},
                'model_updates': {},
                'aggregated_model': None
            }
            
            # 模擬聯邦學習過程
            participant_models = {}
            
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 模擬本地訓練（實際應用中會是真實的模型訓練）
                local_model_update = await self._simulate_local_training(
                    participant, task
                )
                
                participant_models[participant_id] = local_model_update
                results['model_updates'][participant_id] = local_model_update
            
            # 模型聚合
            if participant_models:
                aggregated_model = await self._aggregate_models(
                    participant_models, task.participant_weights
                )
                results['aggregated_model'] = aggregated_model
                
                # 更新集體知識
                await self._update_collective_knowledge(task.domain, aggregated_model)
            
            return results
            
        except Exception as e:
            self.logger.error(f"聯邦學習失敗: {e}")
            return {'method': 'federated_learning', 'error': str(e)}
    
    async def _ensemble_learning(self, task: GroupLearningTask) -> Dict[str, Any]:
        """集成學習"""
        try:
            results = {
                'method': 'ensemble_learning',
                'predictions': {},
                'individual_models': {},
                'ensemble_prediction': None
            }
            
            individual_predictions = {}
            
            # 獲取每個參與者的預測
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 模擬個體預測
                prediction = await self._get_participant_prediction(
                    participant, task
                )
                
                individual_predictions[participant_id] = prediction
                results['predictions'][participant_id] = prediction
            
            # 集成預測
            if individual_predictions:
                ensemble_prediction = await self._ensemble_predictions(
                    individual_predictions, task.participant_weights
                )
                results['ensemble_prediction'] = ensemble_prediction
            
            return results
            
        except Exception as e:
            self.logger.error(f"集成學習失敗: {e}")
            return {'method': 'ensemble_learning', 'error': str(e)}
    
    async def _collaborative_learning(self, task: GroupLearningTask) -> Dict[str, Any]:
        """協作學習"""
        try:
            results = {
                'method': 'collaborative_learning',
                'predictions': {},
                'knowledge_sharing': {},
                'collaborative_insights': []
            }
            
            # 知識分享階段
            shared_knowledge = {}
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 分享知識
                participant_knowledge = await self._extract_participant_knowledge(
                    participant, task.domain
                )
                shared_knowledge[participant_id] = participant_knowledge
                results['knowledge_sharing'][participant_id] = participant_knowledge
            
            # 協作預測階段
            collaborative_predictions = {}
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 結合共享知識進行預測
                prediction = await self._collaborative_prediction(
                    participant, shared_knowledge, task
                )
                
                collaborative_predictions[participant_id] = prediction
                results['predictions'][participant_id] = prediction
            
            # 生成協作洞察
            insights = await self._generate_collaborative_insights(
                shared_knowledge, collaborative_predictions
            )
            results['collaborative_insights'] = insights
            
            return results
            
        except Exception as e:
            self.logger.error(f"協作學習失敗: {e}")
            return {'method': 'collaborative_learning', 'error': str(e)}
    
    async def _competitive_learning(self, task: GroupLearningTask) -> Dict[str, Any]:
        """競爭學習"""
        try:
            results = {
                'method': 'competitive_learning',
                'predictions': {},
                'competition_scores': {},
                'winners': []
            }
            
            # 競爭預測階段
            predictions = {}
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 競爭性預測
                prediction = await self._competitive_prediction(
                    participant, task
                )
                
                predictions[participant_id] = prediction
                results['predictions'][participant_id] = prediction
            
            # 評估競爭結果
            if predictions:
                competition_scores = await self._evaluate_competition(
                    predictions, task
                )
                results['competition_scores'] = competition_scores
                
                # 確定獲勝者
                sorted_scores = sorted(
                    competition_scores.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                winners = [participant_id for participant_id, score in sorted_scores[:3]]
                results['winners'] = winners
                
                # 更新參與者聲譽
                await self._update_reputation_from_competition(
                    competition_scores, task.participants
                )
            
            return results
            
        except Exception as e:
            self.logger.error(f"競爭學習失敗: {e}")
            return {'method': 'competitive_learning', 'error': str(e)}
    
    async def _swarm_intelligence(self, task: GroupLearningTask) -> Dict[str, Any]:
        """群體智能"""
        try:
            results = {
                'method': 'swarm_intelligence',
                'predictions': {},
                'swarm_behavior': {},
                'emergent_patterns': []
            }
            
            # 群體行為模擬
            swarm_predictions = {}
            behavior_patterns = {}
            
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 群體智能預測（考慮鄰居影響）
                neighbors = self.participant_connections.get(participant_id, [])
                prediction, behavior = await self._swarm_prediction(
                    participant, neighbors, task
                )
                
                swarm_predictions[participant_id] = prediction
                behavior_patterns[participant_id] = behavior
                
                results['predictions'][participant_id] = prediction
            
            results['swarm_behavior'] = behavior_patterns
            
            # 識別湧現模式
            if swarm_predictions:
                emergent_patterns = await self._identify_emergent_patterns(
                    swarm_predictions, behavior_patterns
                )
                results['emergent_patterns'] = emergent_patterns
            
            return results
            
        except Exception as e:
            self.logger.error(f"群體智能失敗: {e}")
            return {'method': 'swarm_intelligence', 'error': str(e)}
    
    async def _reach_consensus(
        self,
        task: GroupLearningTask,
        predictions: Dict[str, Any]
    ) -> ConsensusResult:
        """達成共識"""
        try:
            consensus_method = self.consensus_methods.get(task.consensus_method)
            
            if not consensus_method:
                self.logger.error(f"未知的共識方法: {task.consensus_method}")
                # 使用默認的多數投票
                consensus_method = self._majority_vote_consensus
            
            # 執行共識決策
            consensus_result = await consensus_method(
                task, predictions
            )
            
            # 記錄共識歷史
            self.consensus_history.append(consensus_result)
            
            # 分析分歧模式
            await self._analyze_disagreement_patterns(consensus_result)
            
            return consensus_result
            
        except Exception as e:
            self.logger.error(f"共識達成失敗: {e}")
            return ConsensusResult(
                task_id=task.task_id,
                final_prediction=None,
                confidence=0.0,
                agreement_level=0.0
            )
    
    async def _majority_vote_consensus(
        self,
        task: GroupLearningTask,
        predictions: Dict[str, Any]
    ) -> ConsensusResult:
        """多數投票共識"""
        try:
            start_time = time.time()
            
            # 統計投票
            vote_counts = Counter()
            participant_votes = {}
            
            for participant_id, prediction in predictions.items():
                # 簡化處理：將預測轉換為投票
                vote = self._prediction_to_vote(prediction)
                vote_counts[vote] += 1
                participant_votes[participant_id] = vote
            
            # 確定多數決結果
            if vote_counts:
                majority_vote = vote_counts.most_common(1)[0][0]
                total_votes = sum(vote_counts.values())
                agreement_level = vote_counts[majority_vote] / total_votes
            else:
                majority_vote = "neutral"
                agreement_level = 0.0
            
            return ConsensusResult(
                task_id=task.task_id,
                final_prediction=majority_vote,
                confidence=agreement_level,
                agreement_level=agreement_level,
                participant_votes=participant_votes,
                voting_participants=len(predictions),
                consensus_method_used=ConsensusMethod.MAJORITY_VOTE,
                computation_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"多數投票共識失敗: {e}")
            return ConsensusResult(task_id=task.task_id)
    
    async def _weighted_vote_consensus(
        self,
        task: GroupLearningTask,
        predictions: Dict[str, Any]
    ) -> ConsensusResult:
        """權重投票共識"""
        try:
            start_time = time.time()
            
            # 權重投票統計
            weighted_votes = defaultdict(float)
            participant_votes = {}
            participant_weights = {}
            
            for participant_id, prediction in predictions.items():
                if participant_id not in task.participant_weights:
                    continue
                
                vote = self._prediction_to_vote(prediction)
                weight = task.participant_weights[participant_id]
                
                weighted_votes[vote] += weight
                participant_votes[participant_id] = vote
                participant_weights[participant_id] = weight
            
            # 確定加權結果
            if weighted_votes:
                final_vote = max(weighted_votes.keys(), key=lambda x: weighted_votes[x])
                total_weight = sum(weighted_votes.values())
                confidence = weighted_votes[final_vote] / total_weight
            else:
                final_vote = "neutral"
                confidence = 0.0
            
            return ConsensusResult(
                task_id=task.task_id,
                final_prediction=final_vote,
                confidence=confidence,
                agreement_level=confidence,
                participant_votes=participant_votes,
                participant_weights=participant_weights,
                voting_participants=len(predictions),
                consensus_method_used=ConsensusMethod.WEIGHTED_VOTE,
                computation_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"權重投票共識失敗: {e}")
            return ConsensusResult(task_id=task.task_id)
    
    async def _bayesian_consensus(
        self,
        task: GroupLearningTask,
        predictions: Dict[str, Any]
    ) -> ConsensusResult:
        """貝葉斯共識"""
        try:
            start_time = time.time()
            
            # 貝葉斯更新過程（簡化實現）
            prior_beliefs = {"positive": 0.33, "neutral": 0.34, "negative": 0.33}
            
            for participant_id, prediction in predictions.items():
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                vote = self._prediction_to_vote(prediction)
                reliability = participant.get_current_accuracy()
                
                # 貝葉斯更新
                likelihood = {
                    vote: reliability,
                    "positive": (1 - reliability) / 2 if vote != "positive" else reliability,
                    "neutral": (1 - reliability) / 2 if vote != "neutral" else reliability,
                    "negative": (1 - reliability) / 2 if vote != "negative" else reliability
                }
                
                # 計算後驗概率
                evidence = sum(prior_beliefs[outcome] * likelihood[outcome] 
                             for outcome in prior_beliefs)
                
                for outcome in prior_beliefs:
                    prior_beliefs[outcome] = (prior_beliefs[outcome] * likelihood[outcome]) / evidence
            
            # 選擇最高後驗概率的結果
            final_prediction = max(prior_beliefs.keys(), key=lambda x: prior_beliefs[x])
            confidence = prior_beliefs[final_prediction]
            
            return ConsensusResult(
                task_id=task.task_id,
                final_prediction=final_prediction,
                confidence=confidence,
                agreement_level=confidence,
                voting_participants=len(predictions),
                consensus_method_used=ConsensusMethod.BAYESIAN_CONSENSUS,
                computation_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"貝葉斯共識失敗: {e}")
            return ConsensusResult(task_id=task.task_id)
    
    async def _wisdom_of_crowds_consensus(
        self,
        task: GroupLearningTask,
        predictions: Dict[str, Any]
    ) -> ConsensusResult:
        """群眾智慧共識"""
        try:
            start_time = time.time()
            
            # 收集數值預測（如果適用）
            numerical_predictions = []
            categorical_votes = defaultdict(int)
            participant_contributions = {}
            
            for participant_id, prediction in predictions.items():
                if isinstance(prediction, (int, float)):
                    numerical_predictions.append(prediction)
                    participant_contributions[participant_id] = prediction
                else:
                    vote = self._prediction_to_vote(prediction)
                    categorical_votes[vote] += 1
                    participant_contributions[participant_id] = vote
            
            # 群眾智慧結果
            if numerical_predictions:
                # 數值預測：使用平均值（群眾智慧的經典應用）
                crowd_wisdom = np.mean(numerical_predictions)
                confidence = 1.0 / (1.0 + np.std(numerical_predictions))  # 標準差越小，信心度越高
            else:
                # 分類預測：使用多數投票
                if categorical_votes:
                    crowd_wisdom = max(categorical_votes.keys(), key=lambda x: categorical_votes[x])
                    total_votes = sum(categorical_votes.values())
                    confidence = categorical_votes[crowd_wisdom] / total_votes
                else:
                    crowd_wisdom = "neutral"
                    confidence = 0.0
            
            return ConsensusResult(
                task_id=task.task_id,
                final_prediction=crowd_wisdom,
                confidence=confidence,
                agreement_level=confidence,
                participant_votes=participant_contributions,
                voting_participants=len(predictions),
                consensus_method_used=ConsensusMethod.WISDOM_OF_CROWDS,
                computation_time=time.time() - start_time
            )
            
        except Exception as e:
            self.logger.error(f"群眾智慧共識失敗: {e}")
            return ConsensusResult(task_id=task.task_id)
    
    def _prediction_to_vote(self, prediction: Any) -> str:
        """將預測轉換為投票"""
        try:
            if isinstance(prediction, str):
                return prediction.lower()
            elif isinstance(prediction, (int, float)):
                if prediction > 0.1:
                    return "positive"
                elif prediction < -0.1:
                    return "negative"
                else:
                    return "neutral"
            elif isinstance(prediction, dict):
                if 'recommendation' in prediction:
                    return prediction['recommendation'].lower()
                elif 'decision' in prediction:
                    return prediction['decision'].lower()
            
            return "neutral"
            
        except Exception:
            return "neutral"
    
    # 簡化的模擬方法（實際實現中這些會是更複雜的機器學習邏輯）
    
    async def _simulate_local_training(self, participant: LearningParticipant, task: GroupLearningTask) -> Dict[str, Any]:
        """模擬本地訓練"""
        return {
            "model_weights": np.random.normal(0, 0.1, 10).tolist(),
            "training_loss": np.random.exponential(0.5),
            "accuracy": participant.get_current_accuracy() + np.random.normal(0, 0.05)
        }
    
    async def _aggregate_models(self, models: Dict[str, Dict], weights: Dict[str, float]) -> Dict[str, Any]:
        """聚合模型"""
        # 簡化的模型聚合
        aggregated_weights = np.zeros(10)
        total_weight = sum(weights.values())
        
        for participant_id, model in models.items():
            weight = weights.get(participant_id, 0.0) / total_weight
            model_weights = np.array(model.get("model_weights", np.zeros(10)))
            aggregated_weights += model_weights * weight
        
        return {
            "aggregated_weights": aggregated_weights.tolist(),
            "participants": len(models),
            "aggregation_method": "weighted_average"
        }
    
    async def _get_participant_prediction(self, participant: LearningParticipant, task: GroupLearningTask) -> Dict[str, Any]:
        """獲取參與者預測"""
        # 模擬預測邏輯
        base_accuracy = participant.get_current_accuracy()
        noise = np.random.normal(0, 0.1)
        
        prediction_score = base_accuracy + noise
        
        if prediction_score > 0.6:
            recommendation = "positive"
        elif prediction_score < 0.4:
            recommendation = "negative"
        else:
            recommendation = "neutral"
        
        return {
            "recommendation": recommendation,
            "confidence": abs(prediction_score - 0.5) * 2,
            "prediction_score": prediction_score,
            "participant_id": participant.participant_id
        }
    
    async def _update_collective_knowledge(self, domain: str, knowledge: Dict[str, Any]):
        """更新集體知識"""
        if domain not in self.collective_knowledge:
            self.collective_knowledge[domain] = {}
        
        # 簡化的知識更新
        self.collective_knowledge[domain].update({
            "last_update": datetime.now().isoformat(),
            "model_version": knowledge.get("aggregation_method", "unknown"),
            "participants_count": knowledge.get("participants", 0)
        })
    
    # ... 其他輔助方法的簡化實現 ...
    
    async def _check_convergence(self, task: GroupLearningTask) -> bool:
        """檢查收斂條件"""
        if len(task.consensus_results) < 3:
            return False
        
        # 檢查最近幾次共識的一致性
        recent_results = task.consensus_results[-3:]
        predictions = [r.get('final_prediction') for r in recent_results if r.get('final_prediction')]
        
        if len(set(predictions)) <= 1:  # 預測結果一致
            return True
        
        return False
    
    async def _complete_learning_task(self, task_id: str):
        """完成學習任務"""
        try:
            task = self.active_tasks[task_id]
            task.status = "completed"
            task.end_time = datetime.now()
            
            # 移動到完成列表
            self.completed_tasks.append(task)
            del self.active_tasks[task_id]
            
            # 清理學習任務
            if task_id in self.learning_tasks:
                del self.learning_tasks[task_id]
            
            # 更新參與者最終表現
            await self._finalize_participant_performance(task)
            
            self.logger.info(f"學習任務完成: {task.task_name}")
            
        except Exception as e:
            self.logger.error(f"任務完成處理失敗: {e}")
    
    async def _update_participant_performance(self, task: GroupLearningTask, results: Dict[str, Any]):
        """更新參與者性能"""
        try:
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                participant.participation_count += 1
                participant.last_active = datetime.now()
                
                # 模擬性能更新（實際應用中會基於真實結果）
                if 'predictions' in results and participant_id in results['predictions']:
                    # 假設預測正確性（實際中需要真實標籤）
                    prediction_correct = np.random.choice([True, False], p=[0.7, 0.3])
                    participant.update_accuracy(prediction_correct)
        
        except Exception as e:
            self.logger.error(f"參與者性能更新失敗: {e}")
    
    async def _finalize_participant_performance(self, task: GroupLearningTask):
        """完成參與者最終性能評估"""
        try:
            for participant_id in task.participants:
                if participant_id not in self.participants:
                    continue
                
                participant = self.participants[participant_id]
                
                # 更新領域專業度
                current_expertise = self.domain_expertise[task.domain].get(participant_id, 0.5)
                performance_boost = (participant.get_current_accuracy() - 0.5) * 0.1
                new_expertise = min(1.0, current_expertise + performance_boost)
                self.domain_expertise[task.domain][participant_id] = new_expertise
                
                # 更新貢獻分數
                participant.contribution_score += 1.0 / len(task.participants)
                
        except Exception as e:
            self.logger.error(f"最終性能評估失敗: {e}")
    
    def _record_system_metrics(self, task: GroupLearningTask, results: Dict[str, Any]):
        """記錄系統指標"""
        try:
            # 記錄參與度
            self.system_metrics['participation_rate'].append(len(task.participants))
            
            # 記錄共識品質（如果有的話）
            if 'consensus_quality' in results:
                self.system_metrics['consensus_quality'].append(results['consensus_quality'])
            
            # 記錄學習效果
            if 'learning_effectiveness' in results:
                self.system_metrics['learning_effectiveness'].append(results['learning_effectiveness'])
                
        except Exception as e:
            self.logger.warning(f"系統指標記錄失敗: {e}")
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """獲取系統統計信息"""
        try:
            active_participants = sum(1 for p in self.participants.values() 
                                    if (datetime.now() - p.last_active).days <= 7)
            
            avg_accuracy = np.mean([p.get_current_accuracy() 
                                  for p in self.participants.values()]) if self.participants else 0.0
            
            return {
                'total_participants': len(self.participants),
                'active_participants': active_participants,
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'average_accuracy': avg_accuracy,
                'consensus_decisions': len(self.consensus_history),
                'knowledge_domains': len(self.collective_knowledge),
                'system_uptime': 'running'
            }
            
        except Exception as e:
            self.logger.error(f"統計信息獲取失敗: {e}")
            return {'error': str(e)}
    
    # 佔位符方法（完整實現會更複雜）
    async def _extract_participant_knowledge(self, participant: LearningParticipant, domain: str) -> Dict[str, Any]:
        return {"domain": domain, "expertise_level": participant.calculate_expertise_weight(domain)}
    
    async def _collaborative_prediction(self, participant: LearningParticipant, shared_knowledge: Dict, task: GroupLearningTask) -> Dict[str, Any]:
        return await self._get_participant_prediction(participant, task)
    
    async def _generate_collaborative_insights(self, knowledge: Dict, predictions: Dict) -> List[Dict[str, Any]]:
        return [{"insight": "collaborative_pattern_detected", "confidence": 0.7}]
    
    async def _competitive_prediction(self, participant: LearningParticipant, task: GroupLearningTask) -> Dict[str, Any]:
        return await self._get_participant_prediction(participant, task)
    
    async def _evaluate_competition(self, predictions: Dict, task: GroupLearningTask) -> Dict[str, float]:
        return {pid: np.random.random() for pid in predictions.keys()}
    
    async def _update_reputation_from_competition(self, scores: Dict[str, float], participants: List[str]):
        for pid in participants:
            if pid in self.participants and pid in scores:
                score_boost = (scores[pid] - 0.5) * 0.1
                self.participants[pid].reputation = min(1.0, self.participants[pid].reputation + score_boost)
    
    async def _swarm_prediction(self, participant: LearningParticipant, neighbors: List[str], task: GroupLearningTask) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        prediction = await self._get_participant_prediction(participant, task)
        behavior = {"neighbor_influence": len(neighbors), "swarm_cohesion": 0.5}
        return prediction, behavior
    
    async def _identify_emergent_patterns(self, predictions: Dict, behaviors: Dict) -> List[Dict[str, Any]]:
        return [{"pattern": "swarm_alignment", "strength": 0.6}]
    
    async def _ensemble_predictions(self, predictions: Dict, weights: Dict) -> Dict[str, Any]:
        # 簡化的集成預測
        recommendations = [pred.get('recommendation', 'neutral') for pred in predictions.values()]
        most_common = Counter(recommendations).most_common(1)[0][0]
        return {"ensemble_recommendation": most_common, "agreement": 0.7}
    
    async def _analyze_disagreement_patterns(self, consensus_result: ConsensusResult):
        """分析分歧模式"""
        if consensus_result.agreement_level < 0.6:
            pattern_key = f"{consensus_result.consensus_method_used.value}_low_agreement"
            self.disagreement_patterns[pattern_key] += 1