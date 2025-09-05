#!/usr/bin/env python3
"""
Learning Optimizer - 學習優化器
天工 (TianGong) - 為ART系統提供個人化學習路徑優化和推薦

此模組提供：
1. LearningOptimizer - 學習優化核心
2. OptimizationStrategy - 優化策略
3. LearningPath - 個人化學習路徑
4. ProgressTracker - 學習進度追蹤
5. PersonalizedRecommendation - 個人化推薦
"""

from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import time
import logging
import numpy as np
from collections import defaultdict, deque
import uuid
import math
import heapq
from scipy.optimize import minimize

class OptimizationStrategy(Enum):
    """優化策略"""
    REINFORCEMENT_LEARNING = "reinforcement_learning"    # 強化學習
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"      # 貝葉斯優化
    GENETIC_ALGORITHM = "genetic_algorithm"              # 遺傳算法
    GRADIENT_DESCENT = "gradient_descent"                # 梯度下降
    MULTI_ARMED_BANDIT = "multi_armed_bandit"           # 多臂老虎機
    ADAPTIVE_CURRICULUM = "adaptive_curriculum"          # 自適應課程
    COLLABORATIVE_FILTERING = "collaborative_filtering"   # 協同過濾

class AdaptiveLearning(Enum):
    """自適應學習類型"""
    DIFFICULTY_SCALING = "difficulty_scaling"            # 難度調整
    CONTENT_PERSONALIZATION = "content_personalization"  # 內容個人化
    TIMING_OPTIMIZATION = "timing_optimization"          # 時機優化
    FEEDBACK_ADAPTATION = "feedback_adaptation"          # 反饋適應
    STYLE_MATCHING = "style_matching"                   # 風格匹配

@dataclass
class LearningPath:
    """個人化學習路徑"""
    path_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    name: str = ""
    description: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    recommended_actions: List[Dict[str, Any]] = field(default_factory=list)
    current_stage: int = 0
    difficulty_level: float = 0.5           # 0.0 (簡單) 到 1.0 (困難)
    estimated_duration: float = 0.0         # 估計學習時間（小時）
    success_probability: float = 0.0        # 成功概率
    personalization_score: float = 0.0     # 個人化分數
    prerequisites: List[str] = field(default_factory=list)
    learning_resources: List[Dict[str, Any]] = field(default_factory=list)
    assessment_criteria: Dict[str, Any] = field(default_factory=dict)
    adaptive_parameters: Dict[str, float] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProgressTracker:
    """學習進度追蹤"""
    user_id: str
    path_id: str
    current_progress: float = 0.0           # 0.0 到 1.0
    completed_milestones: List[str] = field(default_factory=list)
    skill_improvements: Dict[str, float] = field(default_factory=dict)
    time_spent: float = 0.0                 # 學習時間（小時）
    engagement_score: float = 0.0           # 參與度分數
    retention_rate: float = 0.0             # 知識保持率
    application_success: float = 0.0        # 應用成功率
    feedback_scores: List[float] = field(default_factory=list)
    learning_velocity: float = 0.0          # 學習速度
    difficulty_preference: float = 0.5      # 難度偏好
    last_activity: float = field(default_factory=time.time)
    streak_days: int = 0                    # 連續學習天數
    total_sessions: int = 0                 # 總學習會話數
    average_session_duration: float = 0.0   # 平均會話時長
    performance_trends: Dict[str, List[float]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PersonalizedRecommendation:
    """個人化推薦"""
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    recommendation_type: str = "learning_action"  # learning_action, resource, strategy
    title: str = ""
    description: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    priority_score: float = 0.0             # 優先級分數
    confidence_score: float = 0.0           # 推薦置信度
    expected_impact: float = 0.0            # 預期影響
    difficulty_level: float = 0.5           # 難度級別
    estimated_time: float = 0.0             # 估計完成時間
    prerequisites: List[str] = field(default_factory=list)
    success_factors: List[str] = field(default_factory=list)
    personalization_reasons: List[str] = field(default_factory=list)
    expiry_time: Optional[float] = None     # 推薦過期時間
    feedback_received: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

class LearningOptimizer:
    """學習優化器"""
    
    def __init__(self, optimization_strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE_CURRICULUM):
        self.optimization_strategy = optimization_strategy
        self.learning_paths: Dict[str, LearningPath] = {}
        self.progress_trackers: Dict[str, ProgressTracker] = {}
        self.recommendations: Dict[str, List[PersonalizedRecommendation]] = {}
        self.user_performance_history: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # 優化參數
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.discount_factor = 0.95
        self.temperature = 1.0
        
        # 性能指標
        self.optimization_metrics: Dict[str, float] = {}
        self.algorithm_performance: Dict[str, List[float]] = defaultdict(list)
        
        logging.info(f"LearningOptimizer initialized with {optimization_strategy.value} strategy")
    
    async def create_personalized_learning_path(self, 
                                              user_id: str,
                                              user_profile: Dict[str, Any],
                                              learning_objectives: List[str],
                                              constraints: Dict[str, Any] = None) -> LearningPath:
        """創建個人化學習路徑"""
        logging.info(f"Creating personalized learning path for user {user_id}")
        
        constraints = constraints or {}
        
        # 分析用戶能力和偏好
        user_analysis = await self._analyze_user_capabilities(user_id, user_profile)
        
        # 生成候選路徑
        candidate_paths = await self._generate_candidate_paths(
            user_analysis, learning_objectives, constraints
        )
        
        # 優化路徑選擇
        optimal_path = await self._optimize_path_selection(
            candidate_paths, user_analysis, constraints
        )
        
        # 個人化路徑內容
        personalized_path = await self._personalize_learning_content(
            optimal_path, user_profile, user_analysis
        )
        
        # 設置自適應參數
        personalized_path.adaptive_parameters = await self._calculate_adaptive_parameters(
            user_profile, user_analysis
        )
        
        # 緩存路徑
        self.learning_paths[personalized_path.path_id] = personalized_path
        
        # 初始化進度追蹤器
        progress_tracker = ProgressTracker(
            user_id=user_id,
            path_id=personalized_path.path_id
        )
        self.progress_trackers[f"{user_id}_{personalized_path.path_id}"] = progress_tracker
        
        logging.info(f"Learning path created: {personalized_path.path_id}")
        return personalized_path
    
    async def _analyze_user_capabilities(self, user_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """分析用戶能力"""
        analysis = {
            'current_skill_level': 0.5,
            'learning_preferences': {},
            'strengths': [],
            'improvement_areas': [],
            'learning_style': 'mixed',
            'motivation_factors': [],
            'time_constraints': {}
        }
        
        # 從用戶檔案提取信息
        if 'personality_scores' in user_profile:
            personality = user_profile['personality_scores']
            
            # 學習速度
            if 'learning_rate' in personality:
                analysis['learning_speed'] = personality['learning_rate']
            
            # 分析思維vs直覺思維
            analytical = personality.get('analytical_thinking', 0.5)
            intuitive = personality.get('intuitive_thinking', 0.5)
            
            if analytical > intuitive + 0.2:
                analysis['learning_style'] = 'analytical'
            elif intuitive > analytical + 0.2:
                analysis['learning_style'] = 'intuitive'
            else:
                analysis['learning_style'] = 'mixed'
            
            # 耐心水平影響學習偏好
            patience = personality.get('patience_level', 0.5)
            if patience > 0.7:
                analysis['learning_preferences']['long_form_content'] = 0.8
                analysis['learning_preferences']['detailed_explanations'] = 0.9
            elif patience < 0.3:
                analysis['learning_preferences']['quick_tips'] = 0.8
                analysis['learning_preferences']['interactive_content'] = 0.9
            
            # 自信水平
            confidence = personality.get('confidence_level', 0.5)
            analysis['confidence_level'] = confidence
            
            # 適應性
            adaptability = personality.get('adaptability', 0.5)
            analysis['adaptability'] = adaptability
        
        # 從行為模式提取信息
        if 'behavior_patterns' in user_profile:
            patterns = user_profile['behavior_patterns']
            
            # 根據交易風格推斷學習偏好
            if 'ANALYTICAL' in [p.upper() for p in patterns]:
                analysis['strengths'].append('systematic_analysis')
                analysis['learning_preferences']['data_driven_content'] = 0.9
            
            if 'AGGRESSIVE' in [p.upper() for p in patterns]:
                analysis['learning_preferences']['fast_paced_learning'] = 0.8
                analysis['motivation_factors'].append('quick_results')
            
            if 'CONSERVATIVE' in [p.upper() for p in patterns]:
                analysis['learning_preferences']['gradual_progression'] = 0.8
                analysis['motivation_factors'].append('risk_management')
        
        # 從歷史表現推斷能力
        if user_id in self.user_performance_history:
            history = self.user_performance_history[user_id]
            
            if history:
                # 計算平均表現
                recent_performance = history[-10:]  # 最近10次記錄
                if recent_performance:
                    avg_performance = np.mean([h.get('performance_score', 0.5) for h in recent_performance])
                    analysis['current_skill_level'] = avg_performance
                
                # 識別改進趨勢
                if len(history) >= 5:
                    early_performance = np.mean([h.get('performance_score', 0.5) for h in history[:5]])
                    recent_performance = np.mean([h.get('performance_score', 0.5) for h in history[-5:]])
                    
                    if recent_performance > early_performance + 0.1:
                        analysis['learning_trend'] = 'improving'
                    elif recent_performance < early_performance - 0.1:
                        analysis['learning_trend'] = 'declining'
                    else:
                        analysis['learning_trend'] = 'stable'
        
        return analysis
    
    async def _generate_candidate_paths(self, user_analysis: Dict[str, Any],
                                      learning_objectives: List[str],
                                      constraints: Dict[str, Any]) -> List[LearningPath]:
        """生成候選學習路徑"""
        candidate_paths = []
        
        # 基礎路徑模板
        path_templates = {
            'beginner_comprehensive': {
                'difficulty_progression': [0.2, 0.4, 0.6, 0.8],
                'focus_areas': ['basics', 'fundamentals', 'practice', 'application'],
                'estimated_duration': 40.0
            },
            'intermediate_focused': {
                'difficulty_progression': [0.4, 0.6, 0.8, 0.9],
                'focus_areas': ['review', 'advanced_concepts', 'specialization', 'mastery'],
                'estimated_duration': 25.0
            },
            'advanced_specialized': {
                'difficulty_progression': [0.6, 0.8, 0.9, 1.0],
                'focus_areas': ['expert_techniques', 'cutting_edge', 'innovation', 'leadership'],
                'estimated_duration': 15.0
            },
            'rapid_learning': {
                'difficulty_progression': [0.3, 0.7, 0.9],
                'focus_areas': ['essentials', 'key_skills', 'application'],
                'estimated_duration': 12.0
            },
            'comprehensive_mastery': {
                'difficulty_progression': [0.1, 0.3, 0.5, 0.7, 0.9, 1.0],
                'focus_areas': ['foundation', 'building', 'integration', 'optimization', 'expertise', 'mastery'],
                'estimated_duration': 60.0
            }
        }
        
        # 根據用戶分析選擇合適的模板
        skill_level = user_analysis.get('current_skill_level', 0.5)
        learning_preferences = user_analysis.get('learning_preferences', {})
        
        # 選擇路徑模板
        suitable_templates = []
        
        if skill_level < 0.3:
            suitable_templates.extend(['beginner_comprehensive', 'rapid_learning'])
        elif skill_level < 0.7:
            suitable_templates.extend(['intermediate_focused', 'comprehensive_mastery'])
        else:
            suitable_templates.extend(['advanced_specialized', 'comprehensive_mastery'])
        
        # 考慮時間約束
        max_duration = constraints.get('max_duration', 50.0)
        suitable_templates = [
            template for template in suitable_templates
            if path_templates[template]['estimated_duration'] <= max_duration
        ]
        
        # 如果沒有合適的模板，選擇最接近的
        if not suitable_templates:
            suitable_templates = [
                min(path_templates.keys(), 
                    key=lambda x: abs(path_templates[x]['estimated_duration'] - max_duration))
            ]
        
        # 為每個合適的模板生成候選路徑
        for template_name in suitable_templates:
            template = path_templates[template_name]
            
            candidate_path = LearningPath(
                name=f"Personalized {template_name.replace('_', ' ').title()} Path",
                description=f"A {template_name.replace('_', ' ')} learning path tailored to your needs",
                learning_objectives=learning_objectives,
                difficulty_level=np.mean(template['difficulty_progression']),
                estimated_duration=template['estimated_duration']
            )
            
            # 生成里程碑
            candidate_path.milestones = await self._generate_milestones(
                template, learning_objectives, user_analysis
            )
            
            # 生成推薦行動
            candidate_path.recommended_actions = await self._generate_recommended_actions(
                template, learning_objectives, user_analysis
            )
            
            # 生成學習資源
            candidate_path.learning_resources = await self._generate_learning_resources(
                template, learning_objectives, user_analysis
            )
            
            candidate_paths.append(candidate_path)
        
        return candidate_paths
    
    async def _optimize_path_selection(self, candidate_paths: List[LearningPath],
                                     user_analysis: Dict[str, Any],
                                     constraints: Dict[str, Any]) -> LearningPath:
        """優化路徑選擇"""
        if not candidate_paths:
            raise ValueError("No candidate paths provided")
        
        if len(candidate_paths) == 1:
            return candidate_paths[0]
        
        # 根據優化策略選擇最佳路徑
        if self.optimization_strategy == OptimizationStrategy.BAYESIAN_OPTIMIZATION:
            return await self._bayesian_path_selection(candidate_paths, user_analysis)
        elif self.optimization_strategy == OptimizationStrategy.MULTI_ARMED_BANDIT:
            return await self._bandit_path_selection(candidate_paths, user_analysis)
        else:
            return await self._heuristic_path_selection(candidate_paths, user_analysis, constraints)
    
    async def _heuristic_path_selection(self, candidate_paths: List[LearningPath],
                                      user_analysis: Dict[str, Any],
                                      constraints: Dict[str, Any]) -> LearningPath:
        """啟發式路徑選擇"""
        path_scores = []
        
        for path in candidate_paths:
            score = 0.0
            
            # 難度匹配度
            skill_level = user_analysis.get('current_skill_level', 0.5)
            difficulty_match = 1.0 - abs(path.difficulty_level - skill_level - 0.1)  # 略高於當前水平
            score += difficulty_match * 0.3
            
            # 時間匹配度
            preferred_duration = constraints.get('preferred_duration', path.estimated_duration)
            time_match = 1.0 - abs(path.estimated_duration - preferred_duration) / max(preferred_duration, path.estimated_duration)
            score += time_match * 0.2
            
            # 學習偏好匹配度
            learning_preferences = user_analysis.get('learning_preferences', {})
            preference_match = 0.0
            
            # 基於路徑特徵計算偏好匹配
            if 'quick_tips' in learning_preferences and path.estimated_duration < 20:
                preference_match += learning_preferences['quick_tips'] * 0.3
            
            if 'detailed_explanations' in learning_preferences and len(path.milestones) > 4:
                preference_match += learning_preferences['detailed_explanations'] * 0.3
            
            if 'gradual_progression' in learning_preferences and len(path.milestones) > 3:
                preference_match += learning_preferences['gradual_progression'] * 0.4
            
            score += preference_match * 0.25
            
            # 成功概率（基於歷史數據或模型預測）
            success_probability = await self._predict_success_probability(path, user_analysis)
            score += success_probability * 0.25
            
            path_scores.append((score, path))
        
        # 選擇得分最高的路徑
        best_score, best_path = max(path_scores, key=lambda x: x[0])
        best_path.personalization_score = best_score
        
        return best_path
    
    async def _bayesian_path_selection(self, candidate_paths: List[LearningPath],
                                     user_analysis: Dict[str, Any]) -> LearningPath:
        """貝葉斯優化路徑選擇"""
        # 簡化的貝葉斯優化實現
        # 在實際應用中，這裡會使用更複雜的貝葉斯優化算法
        
        path_utilities = []
        
        for path in candidate_paths:
            # 計算預期效用
            expected_utility = await self._calculate_expected_utility(path, user_analysis)
            uncertainty = await self._calculate_uncertainty(path, user_analysis)
            
            # 考慮探索-利用權衡
            exploration_bonus = self.exploration_rate * uncertainty
            total_utility = expected_utility + exploration_bonus
            
            path_utilities.append((total_utility, path))
        
        # 選擇效用最高的路徑
        best_utility, best_path = max(path_utilities, key=lambda x: x[0])
        best_path.success_probability = await self._predict_success_probability(best_path, user_analysis)
        
        return best_path
    
    async def _bandit_path_selection(self, candidate_paths: List[LearningPath],
                                   user_analysis: Dict[str, Any]) -> LearningPath:
        """多臂老虎機路徑選擇"""
        # 使用Upper Confidence Bound (UCB) 算法
        
        path_ucb_scores = []
        total_trials = sum(self.algorithm_performance.get(f"path_{i}", [0])[-1] if self.algorithm_performance.get(f"path_{i}") else 0 
                         for i in range(len(candidate_paths)))
        
        for i, path in enumerate(candidate_paths):
            path_key = f"path_{i}"
            path_trials = self.algorithm_performance.get(path_key, [0])
            n_trials = path_trials[-1] if path_trials else 0
            
            if n_trials == 0:
                # 優先選擇未嘗試的路徑
                ucb_score = float('inf')
            else:
                # 計算平均回報
                avg_reward = np.mean(path_trials) if path_trials else 0.0
                
                # 計算置信區間
                confidence_interval = math.sqrt(2 * math.log(total_trials + 1) / n_trials)
                
                ucb_score = avg_reward + confidence_interval
            
            path_ucb_scores.append((ucb_score, path))
        
        # 選擇UCB分數最高的路徑
        best_score, best_path = max(path_ucb_scores, key=lambda x: x[0])
        return best_path
    
    async def _calculate_expected_utility(self, path: LearningPath, user_analysis: Dict[str, Any]) -> float:
        """計算預期效用"""
        # 基於多個因素計算預期效用
        utility = 0.0
        
        # 學習效果預期
        learning_effectiveness = await self._predict_learning_effectiveness(path, user_analysis)
        utility += learning_effectiveness * 0.4
        
        # 時間效率
        time_efficiency = 1.0 / (path.estimated_duration + 1)  # 時間越短效率越高
        utility += time_efficiency * 0.2
        
        # 個人化匹配度
        personalization_match = await self._calculate_personalization_match(path, user_analysis)
        utility += personalization_match * 0.3
        
        # 實用性
        practicality = await self._assess_practicality(path, user_analysis)
        utility += practicality * 0.1
        
        return utility
    
    async def _calculate_uncertainty(self, path: LearningPath, user_analysis: Dict[str, Any]) -> float:
        """計算不確定性"""
        # 基於歷史數據的稀缺性和模型置信度計算不確定性
        uncertainty = 1.0
        
        # 路徑使用歷史
        similar_paths_count = len([p for p in self.learning_paths.values() 
                                 if abs(p.difficulty_level - path.difficulty_level) < 0.2])
        if similar_paths_count > 0:
            uncertainty *= 0.8
        
        # 用戶相似性
        user_confidence = user_analysis.get('confidence_level', 0.5)
        uncertainty *= (1.0 - user_confidence * 0.3)
        
        return min(1.0, uncertainty)
    
    async def _predict_success_probability(self, path: LearningPath, user_analysis: Dict[str, Any]) -> float:
        """預測成功概率"""
        probability = 0.5  # 基準概率
        
        # 難度適配性
        skill_level = user_analysis.get('current_skill_level', 0.5)
        difficulty_gap = abs(path.difficulty_level - skill_level)
        
        if difficulty_gap < 0.2:  # 適中難度
            probability += 0.2
        elif difficulty_gap > 0.5:  # 過度困難
            probability -= 0.3
        
        # 學習偏好匹配
        learning_preferences = user_analysis.get('learning_preferences', {})
        if learning_preferences:
            # 簡化的偏好匹配評分
            preference_score = sum(learning_preferences.values()) / len(learning_preferences)
            probability += (preference_score - 0.5) * 0.2
        
        # 動機因素
        motivation_factors = user_analysis.get('motivation_factors', [])
        if 'quick_results' in motivation_factors and path.estimated_duration < 20:
            probability += 0.1
        
        # 歷史表現
        learning_trend = user_analysis.get('learning_trend', 'stable')
        if learning_trend == 'improving':
            probability += 0.15
        elif learning_trend == 'declining':
            probability -= 0.1
        
        # 自信水平
        confidence = user_analysis.get('confidence_level', 0.5)
        probability += (confidence - 0.5) * 0.1
        
        # 適應性
        adaptability = user_analysis.get('adaptability', 0.5)
        probability += (adaptability - 0.5) * 0.1
        
        return max(0.1, min(0.95, probability))
    
    async def _personalize_learning_content(self, path: LearningPath,
                                          user_profile: Dict[str, Any],
                                          user_analysis: Dict[str, Any]) -> LearningPath:
        """個人化學習內容"""
        personalized_path = LearningPath(
            user_id=user_profile.get('user_id', ''),
            name=f"Personalized: {path.name}",
            description=path.description,
            learning_objectives=path.learning_objectives.copy(),
            difficulty_level=path.difficulty_level,
            estimated_duration=path.estimated_duration
        )
        
        # 個人化里程碑
        personalized_path.milestones = await self._personalize_milestones(
            path.milestones, user_analysis
        )
        
        # 個人化推薦行動
        personalized_path.recommended_actions = await self._personalize_actions(
            path.recommended_actions, user_analysis
        )
        
        # 個人化學習資源
        personalized_path.learning_resources = await self._personalize_resources(
            path.learning_resources, user_analysis
        )
        
        # 設置評估標準
        personalized_path.assessment_criteria = await self._create_assessment_criteria(
            user_profile, user_analysis
        )
        
        # 計算個人化分數
        personalized_path.personalization_score = await self._calculate_personalization_score(
            personalized_path, user_profile, user_analysis
        )
        
        return personalized_path
    
    async def _calculate_adaptive_parameters(self, user_profile: Dict[str, Any],
                                           user_analysis: Dict[str, Any]) -> Dict[str, float]:
        """計算自適應參數"""
        parameters = {}
        
        # 難度調整參數
        learning_speed = user_analysis.get('learning_speed', 0.5)
        parameters['difficulty_adjustment_rate'] = learning_speed * 0.2
        
        # 內容個人化參數
        personalization_preference = user_profile.get('personalization_preference', 0.7)
        parameters['content_personalization_weight'] = personalization_preference
        
        # 反饋適應參數
        adaptability = user_analysis.get('adaptability', 0.5)
        parameters['feedback_sensitivity'] = adaptability * 0.3
        
        # 學習節奏參數
        patience = user_profile.get('personality_scores', {}).get('patience_level', 0.5)
        parameters['pacing_flexibility'] = patience * 0.4
        
        # 探索vs利用參數
        confidence = user_analysis.get('confidence_level', 0.5)
        parameters['exploration_rate'] = (1.0 - confidence) * 0.3
        
        return parameters
    
    async def update_learning_progress(self, user_id: str, path_id: str,
                                     progress_data: Dict[str, Any]) -> ProgressTracker:
        """更新學習進度"""
        tracker_key = f"{user_id}_{path_id}"
        
        if tracker_key not in self.progress_trackers:
            # 創建新的進度追蹤器
            self.progress_trackers[tracker_key] = ProgressTracker(
                user_id=user_id,
                path_id=path_id
            )
        
        tracker = self.progress_trackers[tracker_key]
        
        # 更新進度信息
        if 'progress_percentage' in progress_data:
            tracker.current_progress = progress_data['progress_percentage']
        
        if 'completed_milestone' in progress_data:
            milestone = progress_data['completed_milestone']
            if milestone not in tracker.completed_milestones:
                tracker.completed_milestones.append(milestone)
        
        if 'skill_improvement' in progress_data:
            for skill, improvement in progress_data['skill_improvement'].items():
                tracker.skill_improvements[skill] = improvement
        
        if 'time_spent' in progress_data:
            tracker.time_spent += progress_data['time_spent']
        
        if 'engagement_score' in progress_data:
            tracker.engagement_score = progress_data['engagement_score']
        
        if 'feedback_score' in progress_data:
            tracker.feedback_scores.append(progress_data['feedback_score'])
        
        # 更新學習速度
        if tracker.time_spent > 0 and tracker.current_progress > 0:
            tracker.learning_velocity = tracker.current_progress / tracker.time_spent
        
        # 更新會話統計
        if 'session_duration' in progress_data:
            tracker.total_sessions += 1
            session_duration = progress_data['session_duration']
            
            if tracker.total_sessions == 1:
                tracker.average_session_duration = session_duration
            else:
                # 計算移動平均
                alpha = 0.1  # 平滑因子
                tracker.average_session_duration = (
                    (1 - alpha) * tracker.average_session_duration + 
                    alpha * session_duration
                )
        
        # 更新性能趨勢
        if 'performance_metrics' in progress_data:
            for metric, value in progress_data['performance_metrics'].items():
                if metric not in tracker.performance_trends:
                    tracker.performance_trends[metric] = []
                tracker.performance_trends[metric].append(value)
                
                # 保持最近20個數據點
                if len(tracker.performance_trends[metric]) > 20:
                    tracker.performance_trends[metric] = tracker.performance_trends[metric][-20:]
        
        # 更新連續學習天數
        current_time = time.time()
        last_activity = tracker.last_activity
        time_diff = current_time - last_activity
        
        if time_diff <= 86400 * 1.5:  # 1.5天內
            if time_diff >= 86400 * 0.8:  # 超過20小時
                tracker.streak_days += 1
        else:
            tracker.streak_days = 1  # 重置連續天數
        
        tracker.last_activity = current_time
        
        # 觸發自適應調整
        await self._adaptive_adjustment(user_id, path_id, tracker)
        
        return tracker
    
    async def _adaptive_adjustment(self, user_id: str, path_id: str, tracker: ProgressTracker):
        """自適應調整"""
        path = self.learning_paths.get(path_id)
        if not path:
            return
        
        # 根據學習進度調整難度
        if tracker.current_progress > 0.3:  # 達到30%進度後開始調整
            recent_feedback = tracker.feedback_scores[-5:] if len(tracker.feedback_scores) >= 5 else tracker.feedback_scores
            
            if recent_feedback:
                avg_feedback = np.mean(recent_feedback)
                
                # 如果表現太好，增加難度
                if avg_feedback > 0.8 and tracker.learning_velocity > 0.1:
                    difficulty_increase = path.adaptive_parameters.get('difficulty_adjustment_rate', 0.1)
                    path.difficulty_level = min(1.0, path.difficulty_level + difficulty_increase)
                
                # 如果表現不佳，降低難度
                elif avg_feedback < 0.4:
                    difficulty_decrease = path.adaptive_parameters.get('difficulty_adjustment_rate', 0.1)
                    path.difficulty_level = max(0.1, path.difficulty_level - difficulty_decrease)
        
        # 根據參與度調整內容
        if tracker.engagement_score < 0.5:
            # 生成更個人化的推薦
            new_recommendations = await self._generate_engagement_recommendations(user_id, tracker)
            
            user_recommendations = self.recommendations.get(user_id, [])
            user_recommendations.extend(new_recommendations)
            self.recommendations[user_id] = user_recommendations
    
    async def generate_personalized_recommendations(self, user_id: str,
                                                  max_recommendations: int = 5) -> List[PersonalizedRecommendation]:
        """生成個人化推薦"""
        recommendations = []
        
        # 獲取用戶的進度追蹤器
        user_trackers = [tracker for key, tracker in self.progress_trackers.items() 
                        if key.startswith(user_id)]
        
        if not user_trackers:
            # 新用戶推薦
            recommendations.extend(await self._generate_new_user_recommendations(user_id))
        else:
            # 基於當前進度的推薦
            recommendations.extend(await self._generate_progress_based_recommendations(user_id, user_trackers))
        
        # 基於歷史表現的推薦
        if user_id in self.user_performance_history:
            recommendations.extend(await self._generate_performance_based_recommendations(user_id))
        
        # 協同過濾推薦
        recommendations.extend(await self._generate_collaborative_recommendations(user_id))
        
        # 排序和篩選推薦
        ranked_recommendations = await self._rank_recommendations(recommendations, user_id)
        
        return ranked_recommendations[:max_recommendations]
    
    async def _generate_new_user_recommendations(self, user_id: str) -> List[PersonalizedRecommendation]:
        """為新用戶生成推薦"""
        recommendations = []
        
        # 基礎入門推薦
        intro_recommendation = PersonalizedRecommendation(
            user_id=user_id,
            recommendation_type="learning_action",
            title="開始你的投資學習之旅",
            description="完成基礎投資概念的學習模組",
            content={
                "action": "start_basic_course",
                "modules": ["投資基礎", "風險管理", "市場分析"],
                "estimated_completion": "2-3 hours"
            },
            priority_score=0.9,
            confidence_score=0.8,
            expected_impact=0.7,
            difficulty_level=0.2,
            estimated_time=2.5,
            personalization_reasons=["新用戶推薦", "建立基礎知識"]
        )
        recommendations.append(intro_recommendation)
        
        # 評估推薦
        assessment_recommendation = PersonalizedRecommendation(
            user_id=user_id,
            recommendation_type="assessment",
            title="完成投資風格評估",
            description="了解你的投資偏好和風險承受度",
            content={
                "action": "take_assessment",
                "assessment_type": "investment_style",
                "questions": 20
            },
            priority_score=0.85,
            confidence_score=0.9,
            expected_impact=0.8,
            difficulty_level=0.1,
            estimated_time=0.5,
            personalization_reasons=["個人化學習路徑", "了解投資偏好"]
        )
        recommendations.append(assessment_recommendation)
        
        return recommendations
    
    async def _generate_progress_based_recommendations(self, user_id: str,
                                                     trackers: List[ProgressTracker]) -> List[PersonalizedRecommendation]:
        """基於進度生成推薦"""
        recommendations = []
        
        for tracker in trackers:
            path = self.learning_paths.get(tracker.path_id)
            if not path:
                continue
            
            # 根據當前進度推薦下一步
            if tracker.current_progress < 0.3:
                # 早期階段推薦
                recommendation = PersonalizedRecommendation(
                    user_id=user_id,
                    recommendation_type="learning_action",
                    title="繼續當前學習路徑",
                    description=f"完成 {path.name} 的下一個里程碑",
                    content={
                        "action": "continue_learning",
                        "path_id": tracker.path_id,
                        "next_milestone": tracker.completed_milestones[-1] if tracker.completed_milestones else "開始第一個模組"
                    },
                    priority_score=0.8,
                    confidence_score=0.9,
                    expected_impact=0.6,
                    difficulty_level=path.difficulty_level,
                    estimated_time=2.0,
                    personalization_reasons=["延續當前學習", "保持學習動力"]
                )
                recommendations.append(recommendation)
            
            elif tracker.current_progress > 0.8:
                # 接近完成時推薦
                recommendation = PersonalizedRecommendation(
                    user_id=user_id,
                    recommendation_type="achievement",
                    title="即將完成學習路徑！",
                    description="完成最後的挑戰並獲得成就",
                    content={
                        "action": "final_challenge",
                        "path_id": tracker.path_id,
                        "completion_percentage": tracker.current_progress * 100
                    },
                    priority_score=0.95,
                    confidence_score=0.85,
                    expected_impact=0.8,
                    difficulty_level=path.difficulty_level + 0.1,
                    estimated_time=1.5,
                    personalization_reasons=["完成成就感", "鞏固學習成果"]
                )
                recommendations.append(recommendation)
            
            # 基於學習速度的推薦
            if tracker.learning_velocity > 0.15:  # 學習速度快
                recommendation = PersonalizedRecommendation(
                    user_id=user_id,
                    recommendation_type="challenge",
                    title="挑戰進階內容",
                    description="你的學習進度很快，嘗試更有挑戰性的內容",
                    content={
                        "action": "advanced_challenge",
                        "difficulty_increase": 0.2,
                        "topics": ["進階策略", "複雜分析", "實戰應用"]
                    },
                    priority_score=0.7,
                    confidence_score=0.75,
                    expected_impact=0.7,
                    difficulty_level=min(1.0, path.difficulty_level + 0.3),
                    estimated_time=3.0,
                    personalization_reasons=["快速學習者", "提供更大挑戰"]
                )
                recommendations.append(recommendation)
            
            elif tracker.learning_velocity < 0.05 and tracker.engagement_score < 0.5:  # 學習緩慢且參與度低
                recommendation = PersonalizedRecommendation(
                    user_id=user_id,
                    recommendation_type="motivation",
                    title="重燃學習熱情",
                    description="嘗試不同的學習方式來提高參與度",
                    content={
                        "action": "motivation_boost",
                        "suggested_changes": ["互動練習", "實戰案例", "同儕學習"],
                        "break_suggestion": "考慮短暫休息後重新開始"
                    },
                    priority_score=0.6,
                    confidence_score=0.7,
                    expected_impact=0.5,
                    difficulty_level=max(0.1, path.difficulty_level - 0.2),
                    estimated_time=1.0,
                    personalization_reasons=["提高參與度", "重建學習動力"]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    async def _rank_recommendations(self, recommendations: List[PersonalizedRecommendation],
                                  user_id: str) -> List[PersonalizedRecommendation]:
        """排序推薦"""
        # 計算每個推薦的綜合分數
        for rec in recommendations:
            score = (
                rec.priority_score * 0.4 +
                rec.confidence_score * 0.3 +
                rec.expected_impact * 0.3
            )
            rec.priority_score = score
        
        # 按優先級排序
        ranked = sorted(recommendations, key=lambda x: x.priority_score, reverse=True)
        
        # 去重（基於內容相似性）
        unique_recommendations = []
        seen_actions = set()
        
        for rec in ranked:
            action = rec.content.get('action', rec.title)
            if action not in seen_actions:
                unique_recommendations.append(rec)
                seen_actions.add(action)
        
        return unique_recommendations
    
    def get_optimization_metrics(self) -> Dict[str, Any]:
        """獲取優化指標"""
        return {
            'total_learning_paths': len(self.learning_paths),
            'active_progress_trackers': len(self.progress_trackers),
            'total_recommendations': sum(len(recs) for recs in self.recommendations.values()),
            'optimization_strategy': self.optimization_strategy.value,
            'algorithm_performance': dict(self.algorithm_performance),
            'average_path_success_rate': self._calculate_average_success_rate(),
            'user_engagement_metrics': self._calculate_engagement_metrics(),
            'learning_velocity_distribution': self._calculate_velocity_distribution()
        }
    
    def _calculate_average_success_rate(self) -> float:
        """計算平均成功率"""
        completed_paths = [
            tracker for tracker in self.progress_trackers.values()
            if tracker.current_progress >= 0.8
        ]
        
        total_paths = len(self.progress_trackers)
        if total_paths == 0:
            return 0.0
        
        return len(completed_paths) / total_paths
    
    def _calculate_engagement_metrics(self) -> Dict[str, float]:
        """計算參與度指標"""
        if not self.progress_trackers:
            return {}
        
        engagement_scores = [t.engagement_score for t in self.progress_trackers.values()]
        session_durations = [t.average_session_duration for t in self.progress_trackers.values()]
        streak_days = [t.streak_days for t in self.progress_trackers.values()]
        
        return {
            'average_engagement': np.mean(engagement_scores) if engagement_scores else 0.0,
            'average_session_duration': np.mean(session_durations) if session_durations else 0.0,
            'average_streak_days': np.mean(streak_days) if streak_days else 0.0,
            'high_engagement_users': len([s for s in engagement_scores if s > 0.7]) / len(engagement_scores) if engagement_scores else 0.0
        }
    
    def _calculate_velocity_distribution(self) -> Dict[str, float]:
        """計算學習速度分佈"""
        velocities = [t.learning_velocity for t in self.progress_trackers.values() if t.learning_velocity > 0]
        
        if not velocities:
            return {}
        
        return {
            'fast_learners': len([v for v in velocities if v > 0.15]) / len(velocities),
            'medium_learners': len([v for v in velocities if 0.05 <= v <= 0.15]) / len(velocities),
            'slow_learners': len([v for v in velocities if v < 0.05]) / len(velocities),
            'average_velocity': np.mean(velocities)
        }
    
    # 輔助方法的簡化實現
    async def _generate_milestones(self, template: Dict[str, Any], objectives: List[str], user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成里程碑"""
        milestones = []
        focus_areas = template['focus_areas']
        difficulty_progression = template['difficulty_progression']
        
        for i, (area, difficulty) in enumerate(zip(focus_areas, difficulty_progression)):
            milestone = {
                'id': f"milestone_{i+1}",
                'name': f"{area.replace('_', ' ').title()}",
                'description': f"Complete {area.replace('_', ' ')} learning activities",
                'difficulty_level': difficulty,
                'estimated_hours': template['estimated_duration'] / len(focus_areas),
                'objectives': [obj for obj in objectives if area in obj.lower()] or objectives[:1],
                'success_criteria': {
                    'completion_rate': 0.8,
                    'understanding_score': 0.7,
                    'practical_application': 0.6
                }
            }
            milestones.append(milestone)
        
        return milestones
    
    async def _generate_recommended_actions(self, template: Dict[str, Any], objectives: List[str], user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成推薦行動"""
        actions = []
        focus_areas = template['focus_areas']
        
        for area in focus_areas:
            action = {
                'action_type': 'study',
                'content_area': area,
                'description': f"Study {area.replace('_', ' ')} materials and complete exercises",
                'estimated_time': template['estimated_duration'] / len(focus_areas),
                'resources_needed': ['study_materials', 'practice_exercises'],
                'prerequisites': []
            }
            actions.append(action)
        
        return actions
    
    async def _generate_learning_resources(self, template: Dict[str, Any], objectives: List[str], user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成學習資源"""
        resources = []
        focus_areas = template['focus_areas']
        
        for area in focus_areas:
            resource = {
                'resource_type': 'course_module',
                'title': f"{area.replace('_', ' ').title()} Course",
                'description': f"Comprehensive materials for {area.replace('_', ' ')}",
                'format': 'interactive',
                'difficulty_level': template['difficulty_progression'][0],  # 簡化
                'estimated_time': template['estimated_duration'] / len(focus_areas)
            }
            resources.append(resource)
        
        return resources
    
    async def _personalize_milestones(self, milestones: List[Dict[str, Any]], user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個人化里程碑"""
        # 簡化實現：基於用戶偏好調整里程碑
        personalized = milestones.copy()
        
        learning_preferences = user_analysis.get('learning_preferences', {})
        
        if 'quick_tips' in learning_preferences:
            # 為喜歡快速學習的用戶調整
            for milestone in personalized:
                milestone['quick_reference'] = True
                milestone['estimated_hours'] *= 0.8
        
        return personalized
    
    async def _personalize_actions(self, actions: List[Dict[str, Any]], user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個人化行動"""
        return actions.copy()  # 簡化實現
    
    async def _personalize_resources(self, resources: List[Dict[str, Any]], user_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個人化資源"""
        return resources.copy()  # 簡化實現
    
    async def _create_assessment_criteria(self, user_profile: Dict[str, Any], user_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """創建評估標準"""
        return {
            'completion_threshold': 0.8,
            'understanding_threshold': 0.7,
            'application_threshold': 0.6,
            'personalized_adjustments': True
        }
    
    async def _calculate_personalization_score(self, path: LearningPath, user_profile: Dict[str, Any], user_analysis: Dict[str, Any]) -> float:
        """計算個人化分數"""
        return 0.75  # 簡化實現
    
    async def _predict_learning_effectiveness(self, path: LearningPath, user_analysis: Dict[str, Any]) -> float:
        """預測學習效果"""
        return 0.7  # 簡化實現
    
    async def _calculate_personalization_match(self, path: LearningPath, user_analysis: Dict[str, Any]) -> float:
        """計算個人化匹配度"""
        return 0.6  # 簡化實現
    
    async def _assess_practicality(self, path: LearningPath, user_analysis: Dict[str, Any]) -> float:
        """評估實用性"""
        return 0.8  # 簡化實現
    
    async def _generate_engagement_recommendations(self, user_id: str, tracker: ProgressTracker) -> List[PersonalizedRecommendation]:
        """生成參與度推薦"""
        return []  # 簡化實現
    
    async def _generate_performance_based_recommendations(self, user_id: str) -> List[PersonalizedRecommendation]:
        """基於表現生成推薦"""
        return []  # 簡化實現
    
    async def _generate_collaborative_recommendations(self, user_id: str) -> List[PersonalizedRecommendation]:
        """協同過濾推薦"""
        return []  # 簡化實現

# 工廠函數
def create_learning_optimizer(strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE_CURRICULUM) -> LearningOptimizer:
    """創建學習優化器"""
    return LearningOptimizer(strategy)