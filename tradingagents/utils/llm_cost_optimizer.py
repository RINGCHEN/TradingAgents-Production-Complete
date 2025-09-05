#!/usr/bin/env python3
"""
LLM Cost Optimizer - LLM成本優化器
天工 (TianGong) - 智能LLM成本控制和模型選擇系統

此模組負責：
1. 成本監控和預算控制
2. 智能模型選擇
3. 請求優化和快取策略
4. 成本效益分析
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp
import hashlib

class ModelTier(Enum):
    """模型等級"""
    BASIC = "basic"           # GPT-3.5、Gemini Flash - 便宜快速
    STANDARD = "standard"     # GPT-4、Gemini Pro - 平衡性能
    PREMIUM = "premium"       # GPT-4 Turbo、Claude Sonnet - 高質量
    ULTRA = "ultra"          # GPT-4o、Claude Opus - 最佳性能

class TaskComplexity(Enum):
    """任務複雜度"""
    SIMPLE = "simple"         # 基礎分析、簡單摘要
    MODERATE = "moderate"     # 技術分析、新聞整理
    COMPLEX = "complex"       # 綜合分析、深度研究
    CRITICAL = "critical"     # 投資建議、風險評估

class CostUnit(Enum):
    """成本單位"""
    TOKEN = "token"           # 按token計費
    REQUEST = "request"       # 按請求計費
    MINUTE = "minute"         # 按時間計費

@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    provider: str            # openai, google, anthropic
    tier: ModelTier
    cost_per_1k_input: float # 每1K輸入token成本 (USD)
    cost_per_1k_output: float # 每1K輸出token成本 (USD)
    max_context: int         # 最大上下文長度
    speed_score: float       # 速度評分 (1-10)
    quality_score: float     # 質量評分 (1-10)
    rate_limit: int         # 每分鐘請求限制
    supports_streaming: bool = True
    supports_json_mode: bool = False
    description: str = ""

@dataclass
class CostBudget:
    """成本預算"""
    user_id: str
    membership_tier: str
    daily_budget_usd: float
    monthly_budget_usd: float
    daily_used_usd: float = 0.0
    monthly_used_usd: float = 0.0
    last_reset_daily: str = ""
    last_reset_monthly: str = ""
    
    def __post_init__(self):
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        if not self.last_reset_daily:
            self.last_reset_daily = today
        if not self.last_reset_monthly:
            self.last_reset_monthly = current_month

@dataclass
class UsageRecord:
    """使用記錄"""
    user_id: str
    request_id: str
    model_name: str
    task_type: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    response_time_ms: int
    success: bool
    timestamp: str
    quality_rating: Optional[float] = None

class LLMCostOptimizer:
    """LLM成本優化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 模型配置
        self.model_configs = self._initialize_model_configs()
        
        # 成本追蹤
        self.usage_records: List[UsageRecord] = []
        self.user_budgets: Dict[str, CostBudget] = {}
        
        # 快取設置
        self.response_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = 1800  # 30分鐘快取
        
        # 優化設置
        self.cost_optimization_enabled = True
        self.quality_threshold = 7.0  # 最低質量要求
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _initialize_model_configs(self) -> Dict[str, ModelConfig]:
        """初始化模型配置"""
        configs = {}
        
        # OpenAI 模型
        configs["gpt-3.5-turbo"] = ModelConfig(
            model_name="gpt-3.5-turbo",
            provider="openai",
            tier=ModelTier.BASIC,
            cost_per_1k_input=0.0015,
            cost_per_1k_output=0.002,
            max_context=16385,
            speed_score=9.0,
            quality_score=7.0,
            rate_limit=3500,
            supports_json_mode=True,
            description="高速度、低成本的基礎模型"
        )
        
        configs["gpt-4"] = ModelConfig(
            model_name="gpt-4",
            provider="openai",
            tier=ModelTier.STANDARD,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            max_context=8192,
            speed_score=6.0,
            quality_score=9.0,
            rate_limit=500,
            supports_json_mode=True,
            description="高質量分析和推理模型"
        )
        
        configs["gpt-4-turbo"] = ModelConfig(
            model_name="gpt-4-turbo",
            provider="openai",
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.01,
            cost_per_1k_output=0.03,
            max_context=128000,
            speed_score=7.0,
            quality_score=9.5,
            rate_limit=800,
            supports_json_mode=True,
            description="高性價比的進階模型"
        )
        
        configs["gpt-4o"] = ModelConfig(
            model_name="gpt-4o",
            provider="openai",
            tier=ModelTier.ULTRA,
            cost_per_1k_input=0.005,
            cost_per_1k_output=0.015,
            max_context=128000,
            speed_score=8.0,
            quality_score=10.0,
            rate_limit=1000,
            supports_json_mode=True,
            description="最新最強的多模態模型"
        )
        
        # Google 模型
        configs["gemini-flash"] = ModelConfig(
            model_name="gemini-1.5-flash",
            provider="google",
            tier=ModelTier.BASIC,
            cost_per_1k_input=0.00075,
            cost_per_1k_output=0.003,
            max_context=1000000,
            speed_score=10.0,
            quality_score=7.5,
            rate_limit=2000,
            supports_json_mode=True,
            description="超高速度、超大上下文的經濟模型"
        )
        
        configs["gemini-pro"] = ModelConfig(
            model_name="gemini-1.5-pro",
            provider="google",
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.0035,
            cost_per_1k_output=0.0105,
            max_context=2000000,
            speed_score=7.0,
            quality_score=9.0,
            rate_limit=300,
            supports_json_mode=True,
            description="大上下文高質量模型"
        )
        
        # Anthropic 模型
        configs["claude-haiku"] = ModelConfig(
            model_name="claude-3-haiku",
            provider="anthropic",
            tier=ModelTier.BASIC,
            cost_per_1k_input=0.00025,
            cost_per_1k_output=0.00125,
            max_context=200000,
            speed_score=9.5,
            quality_score=8.0,
            rate_limit=1000,
            description="最經濟的Claude模型"
        )
        
        configs["claude-sonnet"] = ModelConfig(
            model_name="claude-3.5-sonnet",
            provider="anthropic",
            tier=ModelTier.PREMIUM,
            cost_per_1k_input=0.003,
            cost_per_1k_output=0.015,
            max_context=200000,
            speed_score=7.0,
            quality_score=9.5,
            rate_limit=500,
            description="平衡性能的Claude模型"
        )
        
        configs["claude-opus"] = ModelConfig(
            model_name="claude-3-opus",
            provider="anthropic",
            tier=ModelTier.ULTRA,
            cost_per_1k_input=0.015,
            cost_per_1k_output=0.075,
            max_context=200000,
            speed_score=5.0,
            quality_score=10.0,
            rate_limit=200,
            description="最高質量的Claude模型"
        )
        
        return configs
    
    async def get_user_budget(self, user_id: str, membership_tier: str) -> CostBudget:
        """獲取用戶預算"""
        if user_id not in self.user_budgets:
            # 根據會員等級設定預算
            budget_mapping = {
                "FREE": {"daily": 0.10, "monthly": 2.00},    # $0.10/天, $2/月
                "GOLD": {"daily": 1.00, "monthly": 25.00},   # $1/天, $25/月
                "DIAMOND": {"daily": 10.00, "monthly": 250.00}  # $10/天, $250/月
            }
            
            budget_config = budget_mapping.get(membership_tier, budget_mapping["FREE"])
            
            self.user_budgets[user_id] = CostBudget(
                user_id=user_id,
                membership_tier=membership_tier,
                daily_budget_usd=budget_config["daily"],
                monthly_budget_usd=budget_config["monthly"]
            )
        
        budget = self.user_budgets[user_id]
        
        # 檢查是否需要重置每日/每月使用量
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        
        if budget.last_reset_daily != today:
            budget.daily_used_usd = 0.0
            budget.last_reset_daily = today
            
        if budget.last_reset_monthly != current_month:
            budget.monthly_used_usd = 0.0
            budget.last_reset_monthly = current_month
        
        return budget
    
    def check_budget_availability(self, budget: CostBudget, estimated_cost: float) -> Dict[str, Any]:
        """檢查預算可用性"""
        daily_remaining = budget.daily_budget_usd - budget.daily_used_usd
        monthly_remaining = budget.monthly_budget_usd - budget.monthly_used_usd
        
        can_afford_daily = daily_remaining >= estimated_cost
        can_afford_monthly = monthly_remaining >= estimated_cost
        
        return {
            "can_afford": can_afford_daily and can_afford_monthly,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining,
            "estimated_cost": estimated_cost,
            "budget_tier": budget.membership_tier,
            "constraints": {
                "daily_limit_reached": not can_afford_daily,
                "monthly_limit_reached": not can_afford_monthly
            }
        }
    
    async def select_optimal_model(
        self,
        task_complexity: TaskComplexity,
        user_context: Dict[str, Any],
        estimated_tokens: int = 1000,
        quality_requirements: float = None
    ) -> Tuple[ModelConfig, Dict[str, Any]]:
        """選擇最優模型"""
        
        user_id = user_context.get('user_id', 'anonymous')
        membership_tier = user_context.get('membership_tier', 'FREE')
        
        # 獲取用戶預算
        budget = await self.get_user_budget(user_id, membership_tier)
        
        # 設定質量要求
        min_quality = quality_requirements or self._get_min_quality_for_task(task_complexity)
        
        # 篩選符合條件的模型
        candidate_models = []
        
        for model_name, config in self.model_configs.items():
            # 檢查質量要求
            if config.quality_score < min_quality:
                continue
            
            # 檢查會員等級限制
            if not self._is_model_allowed_for_tier(config, membership_tier):
                continue
            
            # 估算成本
            estimated_cost = self._calculate_estimated_cost(config, estimated_tokens)
            
            # 檢查預算
            budget_check = self.check_budget_availability(budget, estimated_cost)
            if not budget_check["can_afford"]:
                continue
            
            # 計算性價比評分
            cost_efficiency = self._calculate_cost_efficiency(config, estimated_cost, task_complexity)
            
            candidate_models.append({
                "config": config,
                "estimated_cost": estimated_cost,
                "cost_efficiency": cost_efficiency,
                "budget_impact": estimated_cost / budget.daily_budget_usd
            })
        
        if not candidate_models:
            # 沒有符合條件的模型，返回最便宜的基礎模型
            fallback_model = self._get_fallback_model(membership_tier)
            return fallback_model, {
                "selection_reason": "budget_constraints",
                "message": "已選擇最經濟的可用模型",
                "budget_warning": True
            }
        
        # 根據策略選擇最佳模型
        selected = self._apply_selection_strategy(candidate_models, task_complexity, user_context)
        
        return selected["config"], {
            "selection_reason": "optimized",
            "estimated_cost": selected["estimated_cost"],
            "cost_efficiency": selected["cost_efficiency"],
            "quality_score": selected["config"].quality_score,
            "alternatives_count": len(candidate_models) - 1
        }
    
    def _get_min_quality_for_task(self, complexity: TaskComplexity) -> float:
        """獲取任務所需最低質量"""
        quality_mapping = {
            TaskComplexity.SIMPLE: 6.0,      # 基礎分析可接受較低質量
            TaskComplexity.MODERATE: 7.0,    # 標準分析需要中等質量
            TaskComplexity.COMPLEX: 8.0,     # 複雜分析需要高質量
            TaskComplexity.CRITICAL: 9.0     # 關鍵決策需要最高質量
        }
        return quality_mapping.get(complexity, 7.0)
    
    def _is_model_allowed_for_tier(self, model_config: ModelConfig, membership_tier: str) -> bool:
        """檢查模型是否允許該會員等級使用"""
        tier_limits = {
            "FREE": [ModelTier.BASIC],
            "GOLD": [ModelTier.BASIC, ModelTier.STANDARD, ModelTier.PREMIUM],
            "DIAMOND": [ModelTier.BASIC, ModelTier.STANDARD, ModelTier.PREMIUM, ModelTier.ULTRA]
        }
        
        allowed_tiers = tier_limits.get(membership_tier, [ModelTier.BASIC])
        return model_config.tier in allowed_tiers
    
    def _calculate_estimated_cost(self, model_config: ModelConfig, estimated_tokens: int) -> float:
        """計算預估成本"""
        input_tokens = int(estimated_tokens * 0.7)  # 假設70%為輸入
        output_tokens = int(estimated_tokens * 0.3)  # 假設30%為輸出
        
        input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input
        output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output
        
        return input_cost + output_cost
    
    def _calculate_cost_efficiency(
        self, 
        model_config: ModelConfig, 
        estimated_cost: float, 
        task_complexity: TaskComplexity
    ) -> float:
        """計算成本效益評分"""
        # 基礎評分：質量 / 成本
        base_score = model_config.quality_score / max(estimated_cost * 1000, 0.001)
        
        # 根據任務複雜度調整
        complexity_multiplier = {
            TaskComplexity.SIMPLE: 1.2,      # 簡單任務更重視成本
            TaskComplexity.MODERATE: 1.0,    # 標準權重
            TaskComplexity.COMPLEX: 0.8,     # 複雜任務更重視質量
            TaskComplexity.CRITICAL: 0.6     # 關鍵任務最重視質量
        }
        
        multiplier = complexity_multiplier.get(task_complexity, 1.0)
        
        # 考慮速度因素
        speed_bonus = model_config.speed_score * 0.1
        
        return base_score * multiplier + speed_bonus
    
    def _get_fallback_model(self, membership_tier: str) -> ModelConfig:
        """獲取後備模型"""
        fallback_mapping = {
            "FREE": "gpt-3.5-turbo",
            "GOLD": "gpt-3.5-turbo", 
            "DIAMOND": "gpt-4"
        }
        
        model_name = fallback_mapping.get(membership_tier, "gpt-3.5-turbo")
        return self.model_configs[model_name]
    
    def _apply_selection_strategy(
        self, 
        candidates: List[Dict[str, Any]], 
        task_complexity: TaskComplexity,
        user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """應用選擇策略"""
        
        # 根據任務複雜度和用戶偏好選擇策略
        if task_complexity in [TaskComplexity.CRITICAL]:
            # 關鍵任務：優先質量
            return max(candidates, key=lambda x: x["config"].quality_score)
        elif task_complexity == TaskComplexity.SIMPLE:
            # 簡單任務：優先成本效益
            return max(candidates, key=lambda x: x["cost_efficiency"])
        else:
            # 平衡選擇：綜合評分
            for candidate in candidates:
                candidate["composite_score"] = (
                    candidate["cost_efficiency"] * 0.4 +
                    candidate["config"].quality_score * 0.4 +
                    candidate["config"].speed_score * 0.2
                )
            
            return max(candidates, key=lambda x: x["composite_score"])
    
    async def check_cache(self, request_hash: str) -> Optional[Dict[str, Any]]:
        """檢查快取"""
        if request_hash in self.response_cache:
            cached_data = self.response_cache[request_hash]
            
            # 檢查快取有效期
            cache_time = datetime.fromisoformat(cached_data["cached_at"])
            if datetime.now() - cache_time < timedelta(seconds=self.cache_duration):
                self.logger.debug(f"快取命中: {request_hash[:8]}...")
                return cached_data["response"]
        
        return None
    
    def save_to_cache(self, request_hash: str, response: Dict[str, Any]):
        """保存到快取"""
        self.response_cache[request_hash] = {
            "response": response,
            "cached_at": datetime.now().isoformat()
        }
        
        # 清理過期快取
        self._cleanup_expired_cache()
    
    def _cleanup_expired_cache(self):
        """清理過期快取"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, cached_data in self.response_cache.items():
            cache_time = datetime.fromisoformat(cached_data["cached_at"])
            if current_time - cache_time >= timedelta(seconds=self.cache_duration):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.response_cache[key]
    
    def generate_request_hash(self, prompt: str, model_name: str, parameters: Dict[str, Any]) -> str:
        """生成請求hash用於快取"""
        hash_input = f"{prompt}:{model_name}:{json.dumps(parameters, sort_keys=True)}"
        return hashlib.sha256(hash_input.encode()).hexdigest()  # 安全修復：使用SHA256替換MD5
    
    async def record_usage(
        self,
        user_id: str,
        request_id: str,
        model_name: str,
        task_type: str,
        input_tokens: int,
        output_tokens: int,
        response_time_ms: int,
        success: bool
    ) -> UsageRecord:
        """記錄使用情況"""
        
        model_config = self.model_configs.get(model_name)
        if not model_config:
            self.logger.warning(f"未知模型: {model_name}")
            cost_usd = 0.0
        else:
            input_cost = (input_tokens / 1000) * model_config.cost_per_1k_input
            output_cost = (output_tokens / 1000) * model_config.cost_per_1k_output
            cost_usd = input_cost + output_cost
        
        # 創建使用記錄
        record = UsageRecord(
            user_id=user_id,
            request_id=request_id,
            model_name=model_name,
            task_type=task_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            success=success,
            timestamp=datetime.now().isoformat()
        )
        
        self.usage_records.append(record)
        
        # 更新用戶預算使用量
        if user_id in self.user_budgets and success:
            budget = self.user_budgets[user_id]
            budget.daily_used_usd += cost_usd
            budget.monthly_used_usd += cost_usd
        
        self.logger.info(f"記錄使用: {user_id} - {model_name} - ${cost_usd:.4f}")
        
        return record
    
    async def get_cost_analytics(self, user_id: str = None, days: int = 30) -> Dict[str, Any]:
        """獲取成本分析"""
        
        # 篩選記錄
        start_date = datetime.now() - timedelta(days=days)
        filtered_records = [
            record for record in self.usage_records
            if datetime.fromisoformat(record.timestamp) >= start_date and
               (user_id is None or record.user_id == user_id)
        ]
        
        if not filtered_records:
            return {
                "total_cost": 0.0,
                "total_requests": 0,
                "average_cost_per_request": 0.0,
                "model_breakdown": {},
                "daily_costs": []
            }
        
        # 總成本統計
        total_cost = sum(record.cost_usd for record in filtered_records)
        total_requests = len(filtered_records)
        avg_cost = total_cost / total_requests if total_requests > 0 else 0.0
        
        # 按模型分組
        model_breakdown = {}
        for record in filtered_records:
            if record.model_name not in model_breakdown:
                model_breakdown[record.model_name] = {
                    "requests": 0,
                    "cost": 0.0,
                    "avg_response_time": 0.0,
                    "success_rate": 0.0
                }
            
            breakdown = model_breakdown[record.model_name]
            breakdown["requests"] += 1
            breakdown["cost"] += record.cost_usd
            breakdown["avg_response_time"] += record.response_time_ms
            breakdown["success_rate"] += 1 if record.success else 0
        
        # 計算平均值
        for model_name, breakdown in model_breakdown.items():
            requests = breakdown["requests"]
            breakdown["avg_response_time"] /= requests
            breakdown["success_rate"] = breakdown["success_rate"] / requests * 100
            breakdown["avg_cost_per_request"] = breakdown["cost"] / requests
        
        # 每日成本趨勢
        daily_costs = {}
        for record in filtered_records:
            date = record.timestamp[:10]  # YYYY-MM-DD
            if date not in daily_costs:
                daily_costs[date] = 0.0
            daily_costs[date] += record.cost_usd
        
        daily_costs_list = [
            {"date": date, "cost": cost}
            for date, cost in sorted(daily_costs.items())
        ]
        
        return {
            "analysis_period_days": days,
            "total_cost": total_cost,
            "total_requests": total_requests,
            "average_cost_per_request": avg_cost,
            "model_breakdown": model_breakdown,
            "daily_costs": daily_costs_list,
            "cost_efficiency_score": self._calculate_efficiency_score(filtered_records),
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_efficiency_score(self, records: List[UsageRecord]) -> float:
        """計算成本效益評分"""
        if not records:
            return 0.0
        
        # 基於成功率、成本和響應時間的綜合評分
        total_requests = len(records)
        successful_requests = sum(1 for r in records if r.success)
        success_rate = successful_requests / total_requests
        
        avg_cost = sum(r.cost_usd for r in records) / total_requests
        avg_response_time = sum(r.response_time_ms for r in records) / total_requests
        
        # 正規化評分 (0-100)
        efficiency_score = (
            success_rate * 40 +  # 成功率權重40%
            max(0, (0.1 - avg_cost) / 0.1) * 30 +  # 成本效益權重30%
            max(0, (5000 - avg_response_time) / 5000) * 30  # 響應速度權重30%
        ) * 100
        
        return min(100, max(0, efficiency_score))
    
    def get_optimization_recommendations(self, user_id: str) -> List[Dict[str, Any]]:
        """獲取優化建議"""
        recommendations = []
        
        # 分析用戶使用模式
        user_records = [r for r in self.usage_records if r.user_id == user_id]
        
        if not user_records:
            return [{
                "type": "no_data",
                "title": "暫無使用數據",
                "description": "開始使用AI分析功能後，系統將提供個性化優化建議",
                "priority": "info"
            }]
        
        # 成本優化建議
        total_cost = sum(r.cost_usd for r in user_records[-30:])  # 最近30筆
        if total_cost > 1.0:  # 如果成本較高
            recommendations.append({
                "type": "cost_optimization",
                "title": "考慮使用更經濟的模型",
                "description": f"最近30次分析成本為${total_cost:.2f}，可嘗試使用Gemini Flash或Claude Haiku等經濟型模型",
                "priority": "medium",
                "potential_savings": f"${total_cost * 0.3:.2f}"
            })
        
        # 模型選擇建議
        model_usage = {}
        for record in user_records[-50:]:  # 最近50筆
            model_usage[record.model_name] = model_usage.get(record.model_name, 0) + 1
        
        if len(model_usage) == 1:  # 只使用一個模型
            recommendations.append({
                "type": "model_diversity",
                "title": "嘗試多樣化的模型選擇",
                "description": "不同任務可使用不同模型獲得更好的成本效益，系統可自動為您選擇最適合的模型",
                "priority": "low"
            })
        
        # 快取使用建議
        cache_hits = len([r for r in user_records if hasattr(r, 'from_cache') and r.from_cache])
        cache_rate = cache_hits / len(user_records) if user_records else 0
        
        if cache_rate < 0.1:  # 快取命中率低
            recommendations.append({
                "type": "cache_optimization",
                "title": "增加重複查詢以提高效率",
                "description": "相似的分析請求會使用快取結果，可節省成本和時間",
                "priority": "low"
            })
        
        return recommendations
    
    def clear_cache(self):
        """清理全部快取"""
        self.response_cache.clear()
        self.logger.info("LLM成本優化器快取已清理")

# 便利函數
async def optimize_llm_request(
    user_context: Dict[str, Any],
    task_type: str,
    estimated_tokens: int = 1000,
    quality_requirements: float = None
) -> Dict[str, Any]:
    """優化LLM請求"""
    optimizer = LLMCostOptimizer()
    
    # 分析任務複雜度
    complexity_mapping = {
        "basic_analysis": TaskComplexity.SIMPLE,
        "technical_analysis": TaskComplexity.MODERATE,
        "fundamental_analysis": TaskComplexity.MODERATE,
        "comprehensive_analysis": TaskComplexity.COMPLEX,
        "investment_advice": TaskComplexity.CRITICAL,
        "risk_assessment": TaskComplexity.CRITICAL
    }
    
    task_complexity = complexity_mapping.get(task_type, TaskComplexity.MODERATE)
    
    # 選擇最優模型
    optimal_model, selection_info = await optimizer.select_optimal_model(
        task_complexity, user_context, estimated_tokens, quality_requirements
    )
    
    return {
        "recommended_model": optimal_model.model_name,
        "provider": optimal_model.provider,
        "estimated_cost": selection_info.get("estimated_cost", 0.0),
        "quality_score": optimal_model.quality_score,
        "selection_reason": selection_info.get("selection_reason"),
        "optimization_tips": selection_info
    }

async def get_user_cost_summary(user_id: str) -> Dict[str, Any]:
    """獲取用戶成本總覽"""
    optimizer = LLMCostOptimizer()
    
    # 獲取用戶預算
    budget = await optimizer.get_user_budget(user_id, "GOLD")  # 預設GOLD，實際應從用戶上下文獲取
    
    # 獲取成本分析
    analytics = await optimizer.get_cost_analytics(user_id, days=30)
    
    # 獲取優化建議
    recommendations = optimizer.get_optimization_recommendations(user_id)
    
    return {
        "budget_info": asdict(budget),
        "usage_analytics": analytics,
        "optimization_recommendations": recommendations,
        "cost_efficiency_score": analytics.get("cost_efficiency_score", 0),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_cost_optimizer():
        print("💰 測試LLM成本優化器")
        
        optimizer = LLMCostOptimizer()
        
        # 測試模型選擇
        user_context = {
            "user_id": "test_user",
            "membership_tier": "GOLD"
        }
        
        optimal_model, selection_info = await optimizer.select_optimal_model(
            TaskComplexity.MODERATE,
            user_context,
            estimated_tokens=1500
        )
        
        print(f"推薦模型: {optimal_model.model_name}")
        print(f"預估成本: ${selection_info.get('estimated_cost', 0):.4f}")
        print(f"質量評分: {optimal_model.quality_score}/10")
        
        # 測試使用記錄
        record = await optimizer.record_usage(
            user_id="test_user",
            request_id="test_001",
            model_name=optimal_model.model_name,
            task_type="test_analysis",
            input_tokens=1000,
            output_tokens=500,
            response_time_ms=2500,
            success=True
        )
        
        print(f"記錄使用: ${record.cost_usd:.4f}")
        
        # 測試成本分析
        analytics = await optimizer.get_cost_analytics("test_user")
        print(f"總成本: ${analytics['total_cost']:.4f}")
        print(f"效益評分: {analytics['cost_efficiency_score']:.1f}/100")
        
        print("✅ 測試完成")
    
    asyncio.run(test_cost_optimizer())