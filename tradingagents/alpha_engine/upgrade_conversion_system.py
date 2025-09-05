#!/usr/bin/env python3
"""
Upgrade Conversion System
升級轉換系統 - GPT-OSS整合任務3.3.1

智能化會員升級轉換系統，提升付費轉換率
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from decimal import Decimal

class ConversionTriggerType(str, Enum):
    """轉換觸發類型"""
    QUOTA_EXCEEDED = "quota_exceeded"
    FEATURE_BLOCKED = "feature_blocked"
    USAGE_THRESHOLD = "usage_threshold"
    TRIAL_EXPIRING = "trial_expiring"
    VALUE_DEMONSTRATION = "value_demonstration"
    PEER_COMPARISON = "peer_comparison"
    SEASONAL_PROMOTION = "seasonal_promotion"
    BEHAVIORAL_PATTERN = "behavioral_pattern"

class ConversionStrategy(str, Enum):
    """轉換策略"""
    IMMEDIATE_UPGRADE = "immediate_upgrade"
    GRADUAL_NURTURING = "gradual_nurturing"
    DISCOUNT_INCENTIVE = "discount_incentive"
    TRIAL_EXTENSION = "trial_extension"
    FEATURE_PREVIEW = "feature_preview"
    PEER_PRESSURE = "peer_pressure"
    URGENCY_CREATION = "urgency_creation"
    VALUE_REINFORCEMENT = "value_reinforcement"

class ConversionStatus(str, Enum):
    """轉換狀態"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONVERTED = "converted"
    DECLINED = "declined"
    EXPIRED = "expired"
    PAUSED = "paused"

class UpgradeIncentiveType(str, Enum):
    """升級激勵類型"""
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_AMOUNT_DISCOUNT = "fixed_amount_discount"
    FREE_TRIAL_EXTENSION = "free_trial_extension"
    BONUS_FEATURES = "bonus_features"
    PRIORITY_SUPPORT = "priority_support"
    EXCLUSIVE_CONTENT = "exclusive_content"
    CASHBACK_REWARD = "cashback_reward"

class ConversionEvent(BaseModel):
    """轉換事件"""
    event_id: str = Field(..., description="事件ID")
    member_id: str = Field(..., description="會員ID")
    trigger_type: ConversionTriggerType = Field(..., description="觸發類型")
    trigger_context: Dict[str, Any] = Field(default_factory=dict, description="觸發上下文")
    current_tier: str = Field(..., description="當前會員等級")
    suggested_tier: str = Field(..., description="建議升級等級")
    urgency_score: float = Field(..., ge=0.0, le=1.0, description="緊急程度分數")
    conversion_probability: float = Field(..., ge=0.0, le=1.0, description="轉換概率")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UpgradeIncentive(BaseModel):
    """升級激勵"""
    incentive_id: str = Field(..., description="激勵ID")
    incentive_type: UpgradeIncentiveType = Field(..., description="激勵類型")
    title: str = Field(..., description="激勵標題")
    description: str = Field(..., description="激勵描述")
    discount_percentage: Optional[float] = Field(None, description="折扣百分比")
    discount_amount: Optional[Decimal] = Field(None, description="折扣金額")
    bonus_features: List[str] = Field(default_factory=list, description="贈送功能")
    valid_until: datetime = Field(..., description="有效期限")
    max_usage_count: int = Field(1, description="最大使用次數")
    current_usage_count: int = Field(0, description="當前使用次數")
    target_tiers: List[str] = Field(default_factory=list, description="目標會員等級")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversionCampaign(BaseModel):
    """轉換活動"""
    campaign_id: str = Field(..., description="活動ID")
    campaign_name: str = Field(..., description="活動名稱")
    strategy: ConversionStrategy = Field(..., description="轉換策略")
    target_triggers: List[ConversionTriggerType] = Field(default_factory=list, description="目標觸發器")
    target_member_segments: List[str] = Field(default_factory=list, description="目標會員群體")
    incentives: List[UpgradeIncentive] = Field(default_factory=list, description="活動激勵")
    success_metrics: Dict[str, float] = Field(default_factory=dict, description="成功指標")
    start_date: datetime = Field(..., description="開始時間")
    end_date: datetime = Field(..., description="結束時間")
    budget_limit: Optional[Decimal] = Field(None, description="預算限制")
    current_cost: Decimal = Field(Decimal('0'), description="當前成本")
    is_active: bool = Field(True, description="是否啟用")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ConversionAttempt(BaseModel):
    """轉換嘗試"""
    attempt_id: str = Field(..., description="嘗試ID")
    event_id: str = Field(..., description="事件ID")
    member_id: str = Field(..., description="會員ID")
    campaign_id: Optional[str] = Field(None, description="活動ID")
    strategy_used: ConversionStrategy = Field(..., description="使用的策略")
    incentive_offered: Optional[UpgradeIncentive] = Field(None, description="提供的激勵")
    presentation_method: str = Field(..., description="展示方式")
    member_response: Optional[str] = Field(None, description="會員回應")
    conversion_status: ConversionStatus = Field(ConversionStatus.PENDING, description="轉換狀態")
    response_time_minutes: Optional[int] = Field(None, description="回應時間")
    conversion_value: Optional[Decimal] = Field(None, description="轉換價值")
    attempted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(None, description="完成時間")

class MemberConversionProfile(BaseModel):
    """會員轉換檔案"""
    member_id: str = Field(..., description="會員ID")
    conversion_score: float = Field(0.0, ge=0.0, le=1.0, description="轉換分數")
    preferred_strategies: List[ConversionStrategy] = Field(default_factory=list, description="偏好策略")
    successful_triggers: List[ConversionTriggerType] = Field(default_factory=list, description="成功觸發器")
    failed_attempts_count: int = Field(0, description="失敗嘗試次數")
    last_conversion_attempt: Optional[datetime] = Field(None, description="最後轉換嘗試時間")
    total_conversion_value: Decimal = Field(Decimal('0'), description="總轉換價值")
    behavioral_patterns: Dict[str, Any] = Field(default_factory=dict, description="行為模式")
    price_sensitivity: float = Field(0.5, ge=0.0, le=1.0, description="價格敏感度")
    feature_affinity: Dict[str, float] = Field(default_factory=dict, description="功能偏好")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UpgradeConversionSystem:
    """升級轉換系統"""
    
    def __init__(self, access_controller=None, report_integrator=None):
        self.access_controller = access_controller
        self.report_integrator = report_integrator
        self.conversion_events: List[ConversionEvent] = []
        self.conversion_attempts: List[ConversionAttempt] = []
        self.active_campaigns: List[ConversionCampaign] = []
        self.member_profiles: Dict[str, MemberConversionProfile] = {}
        self.conversion_rules = self._initialize_conversion_rules()
        self.incentive_templates = self._initialize_incentive_templates()
        
    def _initialize_conversion_rules(self) -> Dict[ConversionTriggerType, Dict[str, Any]]:
        """初始化轉換規則"""
        return {
            ConversionTriggerType.QUOTA_EXCEEDED: {
                "priority": 0.9,
                "strategies": [ConversionStrategy.IMMEDIATE_UPGRADE, ConversionStrategy.DISCOUNT_INCENTIVE],
                "timing": "immediate",
                "success_rate": 0.35
            },
            ConversionTriggerType.FEATURE_BLOCKED: {
                "priority": 0.8,
                "strategies": [ConversionStrategy.FEATURE_PREVIEW, ConversionStrategy.TRIAL_EXTENSION],
                "timing": "immediate",
                "success_rate": 0.28
            },
            ConversionTriggerType.USAGE_THRESHOLD: {
                "priority": 0.7,
                "strategies": [ConversionStrategy.GRADUAL_NURTURING, ConversionStrategy.VALUE_REINFORCEMENT],
                "timing": "delayed",
                "success_rate": 0.22
            },
            ConversionTriggerType.TRIAL_EXPIRING: {
                "priority": 0.85,
                "strategies": [ConversionStrategy.URGENCY_CREATION, ConversionStrategy.DISCOUNT_INCENTIVE],
                "timing": "scheduled",
                "success_rate": 0.42
            },
            ConversionTriggerType.VALUE_DEMONSTRATION: {
                "priority": 0.6,
                "strategies": [ConversionStrategy.VALUE_REINFORCEMENT, ConversionStrategy.PEER_COMPARISON],
                "timing": "contextual",
                "success_rate": 0.18
            }
        }
    
    def _initialize_incentive_templates(self) -> Dict[UpgradeIncentiveType, Dict[str, Any]]:
        """初始化激勵模板"""
        return {
            UpgradeIncentiveType.PERCENTAGE_DISCOUNT: {
                "default_percentage": 20.0,
                "max_percentage": 50.0,
                "duration_days": 30,
                "cost_factor": 0.2
            },
            UpgradeIncentiveType.FIXED_AMOUNT_DISCOUNT: {
                "default_amount": Decimal('100'),
                "max_amount": Decimal('500'),
                "duration_days": 30,
                "cost_factor": 0.15
            },
            UpgradeIncentiveType.FREE_TRIAL_EXTENSION: {
                "default_days": 14,
                "max_days": 30,
                "cost_factor": 0.05
            },
            UpgradeIncentiveType.BONUS_FEATURES: {
                "features": ["priority_support", "advanced_analytics", "custom_reports"],
                "duration_days": 90,
                "cost_factor": 0.1
            }
        }
    
    async def detect_conversion_opportunity(self, member_id: str, context: Dict[str, Any]) -> Optional[ConversionEvent]:
        """檢測轉換機會"""
        trigger_type = None
        urgency_score = 0.0
        conversion_probability = 0.0
        
        # 檢測配額超限
        if context.get('quota_exceeded'):
            trigger_type = ConversionTriggerType.QUOTA_EXCEEDED
            urgency_score = 0.9
            conversion_probability = 0.35
        
        # 檢測功能被阻擋
        elif context.get('feature_blocked'):
            trigger_type = ConversionTriggerType.FEATURE_BLOCKED
            urgency_score = 0.8
            conversion_probability = 0.28
        
        # 檢測使用量閾值
        elif context.get('usage_high'):
            trigger_type = ConversionTriggerType.USAGE_THRESHOLD
            urgency_score = 0.6
            conversion_probability = 0.22
        
        # 檢測試用期即將到期
        elif context.get('trial_expiring_days', 999) <= 3:
            trigger_type = ConversionTriggerType.TRIAL_EXPIRING
            urgency_score = 0.85
            conversion_probability = 0.42
        
        if trigger_type:
            # 獲取或創建會員轉換檔案
            member_profile = await self._get_or_create_member_profile(member_id)
            
            # 調整轉換概率基於歷史數據
            if member_profile.failed_attempts_count > 3:
                conversion_probability *= 0.6  # 降低概率
            elif member_profile.conversion_score > 0.7:
                conversion_probability *= 1.3  # 提高概率
            
            event = ConversionEvent(
                event_id=f"event_{member_id}_{int(datetime.now().timestamp())}",
                member_id=member_id,
                trigger_type=trigger_type,
                trigger_context=context,
                current_tier=context.get('current_tier', 'free'),
                suggested_tier=context.get('suggested_tier', 'premium'),
                urgency_score=min(urgency_score, 1.0),
                conversion_probability=min(conversion_probability, 1.0)
            )
            
            self.conversion_events.append(event)
            return event
        
        return None
    
    async def _get_or_create_member_profile(self, member_id: str) -> MemberConversionProfile:
        """獲取或創建會員轉換檔案"""
        if member_id not in self.member_profiles:
            self.member_profiles[member_id] = MemberConversionProfile(
                member_id=member_id,
                conversion_score=0.5,  # 默認中等轉換分數
                behavioral_patterns={
                    "avg_session_duration": 0,
                    "feature_usage_diversity": 0,
                    "peak_usage_hours": []
                }
            )
        return self.member_profiles[member_id]
    
    async def create_conversion_attempt(self, event: ConversionEvent, 
                                      strategy: Optional[ConversionStrategy] = None) -> ConversionAttempt:
        """創建轉換嘗試"""
        member_profile = await self._get_or_create_member_profile(event.member_id)
        
        # 選擇最佳策略
        if not strategy:
            strategy = await self._select_optimal_strategy(event, member_profile)
        
        # 選擇合適的激勵
        incentive = await self._select_incentive(event, strategy, member_profile)
        
        # 確定展示方式
        presentation_method = await self._determine_presentation_method(event, strategy, member_profile)
        
        attempt = ConversionAttempt(
            attempt_id=f"attempt_{event.event_id}_{int(datetime.now().timestamp())}",
            event_id=event.event_id,
            member_id=event.member_id,
            strategy_used=strategy,
            incentive_offered=incentive,
            presentation_method=presentation_method,
            conversion_status=ConversionStatus.PENDING
        )
        
        self.conversion_attempts.append(attempt)
        return attempt
    
    async def _select_optimal_strategy(self, event: ConversionEvent, 
                                     member_profile: MemberConversionProfile) -> ConversionStrategy:
        """選擇最佳轉換策略"""
        # 基於觸發類型的策略
        rule = self.conversion_rules.get(event.trigger_type)
        if not rule:
            return ConversionStrategy.GRADUAL_NURTURING
        
        available_strategies = rule["strategies"]
        
        # 基於會員偏好調整
        if member_profile.preferred_strategies:
            for strategy in member_profile.preferred_strategies:
                if strategy in available_strategies:
                    return strategy
        
        # 基於價格敏感度選擇
        if member_profile.price_sensitivity > 0.7:
            if ConversionStrategy.DISCOUNT_INCENTIVE in available_strategies:
                return ConversionStrategy.DISCOUNT_INCENTIVE
        
        # 基於緊急程度選擇
        if event.urgency_score > 0.8:
            if ConversionStrategy.IMMEDIATE_UPGRADE in available_strategies:
                return ConversionStrategy.IMMEDIATE_UPGRADE
        
        # 默認返回第一個策略
        return available_strategies[0] if available_strategies else ConversionStrategy.GRADUAL_NURTURING
    
    async def _select_incentive(self, event: ConversionEvent, strategy: ConversionStrategy,
                              member_profile: MemberConversionProfile) -> Optional[UpgradeIncentive]:
        """選擇合適的激勵"""
        # 基於策略類型選擇激勵
        incentive_type = None
        
        if strategy == ConversionStrategy.DISCOUNT_INCENTIVE:
            if member_profile.price_sensitivity > 0.6:
                incentive_type = UpgradeIncentiveType.PERCENTAGE_DISCOUNT
            else:
                incentive_type = UpgradeIncentiveType.FIXED_AMOUNT_DISCOUNT
        
        elif strategy == ConversionStrategy.TRIAL_EXTENSION:
            incentive_type = UpgradeIncentiveType.FREE_TRIAL_EXTENSION
        
        elif strategy == ConversionStrategy.FEATURE_PREVIEW:
            incentive_type = UpgradeIncentiveType.BONUS_FEATURES
        
        if not incentive_type:
            return None
        
        # 創建激勵
        template = self.incentive_templates.get(incentive_type)
        if not template:
            return None
        
        incentive = UpgradeIncentive(
            incentive_id=f"incentive_{event.event_id}_{incentive_type.value}",
            incentive_type=incentive_type,
            title=self._generate_incentive_title(incentive_type, event),
            description=self._generate_incentive_description(incentive_type, event, template),
            valid_until=datetime.now(timezone.utc) + timedelta(days=template.get("duration_days", 30)),
            target_tiers=[event.suggested_tier]
        )
        
        # 設置具體參數
        if incentive_type == UpgradeIncentiveType.PERCENTAGE_DISCOUNT:
            discount_percent = min(template["default_percentage"] * (1 + event.urgency_score), 
                                 template["max_percentage"])
            incentive.discount_percentage = discount_percent
        
        elif incentive_type == UpgradeIncentiveType.FIXED_AMOUNT_DISCOUNT:
            discount_amount = min(template["default_amount"] * Decimal(str(1 + event.urgency_score)), 
                                template["max_amount"])
            incentive.discount_amount = discount_amount
        
        elif incentive_type == UpgradeIncentiveType.BONUS_FEATURES:
            incentive.bonus_features = template["features"]
        
        return incentive
    
    def _generate_incentive_title(self, incentive_type: UpgradeIncentiveType, event: ConversionEvent) -> str:
        """生成激勵標題"""
        titles = {
            UpgradeIncentiveType.PERCENTAGE_DISCOUNT: "限時升級折扣優惠",
            UpgradeIncentiveType.FIXED_AMOUNT_DISCOUNT: "升級專享現金折扣",
            UpgradeIncentiveType.FREE_TRIAL_EXTENSION: "免費試用期延長",
            UpgradeIncentiveType.BONUS_FEATURES: "升級贈送高級功能"
        }
        return titles.get(incentive_type, "專屬升級優惠")
    
    def _generate_incentive_description(self, incentive_type: UpgradeIncentiveType, 
                                       event: ConversionEvent, template: Dict[str, Any]) -> str:
        """生成激勵描述"""
        if incentive_type == UpgradeIncentiveType.PERCENTAGE_DISCOUNT:
            return f"立即升級享受{template['default_percentage']:.0f}%折扣，限時{template['duration_days']}天"
        elif incentive_type == UpgradeIncentiveType.FIXED_AMOUNT_DISCOUNT:
            return f"升級即享現金折扣NT${template['default_amount']}，機會難得"
        elif incentive_type == UpgradeIncentiveType.FREE_TRIAL_EXTENSION:
            return f"免費延長試用期{template['default_days']}天，體驗更多高級功能"
        elif incentive_type == UpgradeIncentiveType.BONUS_FEATURES:
            return f"升級贈送{len(template['features'])}項高級功能，價值超值"
        else:
            return "專為您量身打造的升級優惠"
    
    async def _determine_presentation_method(self, event: ConversionEvent, 
                                           strategy: ConversionStrategy,
                                           member_profile: MemberConversionProfile) -> str:
        """確定展示方式"""
        # 基於觸發類型確定展示方式
        if event.trigger_type == ConversionTriggerType.QUOTA_EXCEEDED:
            return "blocking_modal"  # 阻擋式彈窗
        elif event.trigger_type == ConversionTriggerType.FEATURE_BLOCKED:
            return "inline_prompt"  # 行內提示
        elif event.trigger_type == ConversionTriggerType.TRIAL_EXPIRING:
            return "notification_banner"  # 通知橫幅
        else:
            return "gentle_suggestion"  # 溫和建議
    
    async def record_conversion_response(self, attempt_id: str, response: str, 
                                       converted: bool, conversion_value: Optional[Decimal] = None) -> bool:
        """記錄轉換回應"""
        for attempt in self.conversion_attempts:
            if attempt.attempt_id == attempt_id:
                attempt.member_response = response
                attempt.conversion_status = ConversionStatus.CONVERTED if converted else ConversionStatus.DECLINED
                attempt.completed_at = datetime.now(timezone.utc)
                
                if conversion_value:
                    attempt.conversion_value = conversion_value
                
                # 更新會員檔案
                member_profile = await self._get_or_create_member_profile(attempt.member_id)
                
                if converted:
                    member_profile.conversion_score = min(member_profile.conversion_score + 0.1, 1.0)
                    member_profile.total_conversion_value += conversion_value or Decimal('0')
                    if attempt.strategy_used not in member_profile.preferred_strategies:
                        member_profile.preferred_strategies.append(attempt.strategy_used)
                else:
                    member_profile.failed_attempts_count += 1
                    member_profile.conversion_score = max(member_profile.conversion_score - 0.05, 0.0)
                
                member_profile.last_conversion_attempt = datetime.now(timezone.utc)
                member_profile.updated_at = datetime.now(timezone.utc)
                
                return True
        
        return False
    
    async def analyze_conversion_performance(self) -> Dict[str, Any]:
        """分析轉換性能"""
        if not self.conversion_attempts:
            return {"total_attempts": 0, "conversion_rate": 0, "average_value": 0}
        
        total_attempts = len(self.conversion_attempts)
        converted_attempts = [a for a in self.conversion_attempts if a.conversion_status == ConversionStatus.CONVERTED]
        conversion_count = len(converted_attempts)
        
        conversion_rate = conversion_count / total_attempts if total_attempts > 0 else 0
        
        # 計算平均轉換價值
        total_value = sum(a.conversion_value for a in converted_attempts if a.conversion_value)
        average_value = total_value / conversion_count if conversion_count > 0 else Decimal('0')
        
        # 按觸發類型分析
        trigger_performance = {}
        for trigger in ConversionTriggerType:
            trigger_attempts = [a for a in self.conversion_attempts 
                              for e in self.conversion_events 
                              if e.event_id == a.event_id and e.trigger_type == trigger]
            trigger_conversions = [a for a in trigger_attempts if a.conversion_status == ConversionStatus.CONVERTED]
            
            if trigger_attempts:
                trigger_performance[trigger.value] = {
                    "attempts": len(trigger_attempts),
                    "conversions": len(trigger_conversions),
                    "rate": len(trigger_conversions) / len(trigger_attempts)
                }
        
        # 按策略分析
        strategy_performance = {}
        for strategy in ConversionStrategy:
            strategy_attempts = [a for a in self.conversion_attempts if a.strategy_used == strategy]
            strategy_conversions = [a for a in strategy_attempts if a.conversion_status == ConversionStatus.CONVERTED]
            
            if strategy_attempts:
                strategy_performance[strategy.value] = {
                    "attempts": len(strategy_attempts),
                    "conversions": len(strategy_conversions),
                    "rate": len(strategy_conversions) / len(strategy_attempts)
                }
        
        return {
            "total_attempts": total_attempts,
            "total_conversions": conversion_count,
            "conversion_rate": conversion_rate,
            "average_conversion_value": float(average_value),
            "total_revenue": float(total_value),
            "trigger_performance": trigger_performance,
            "strategy_performance": strategy_performance,
            "active_member_profiles": len(self.member_profiles)
        }
    
    async def get_member_conversion_insights(self, member_id: str) -> Dict[str, Any]:
        """獲取會員轉換洞察"""
        member_profile = self.member_profiles.get(member_id)
        if not member_profile:
            return {"member_id": member_id, "profile_exists": False}
        
        member_attempts = [a for a in self.conversion_attempts if a.member_id == member_id]
        member_events = [e for e in self.conversion_events if e.member_id == member_id]
        
        successful_attempts = [a for a in member_attempts if a.conversion_status == ConversionStatus.CONVERTED]
        
        return {
            "member_id": member_id,
            "profile_exists": True,
            "conversion_score": member_profile.conversion_score,
            "total_attempts": len(member_attempts),
            "successful_conversions": len(successful_attempts),
            "personal_conversion_rate": len(successful_attempts) / len(member_attempts) if member_attempts else 0,
            "total_conversion_value": float(member_profile.total_conversion_value),
            "preferred_strategies": [s.value for s in member_profile.preferred_strategies],
            "price_sensitivity": member_profile.price_sensitivity,
            "last_attempt": member_profile.last_conversion_attempt.isoformat() if member_profile.last_conversion_attempt else None,
            "behavioral_patterns": member_profile.behavioral_patterns,
            "feature_affinity": member_profile.feature_affinity
        }
    
    def create_conversion_campaign(self, campaign_config: Dict[str, Any]) -> ConversionCampaign:
        """創建轉換活動"""
        campaign = ConversionCampaign(
            campaign_id=f"campaign_{int(datetime.now().timestamp())}",
            campaign_name=campaign_config.get("name", "升級轉換活動"),
            strategy=ConversionStrategy(campaign_config.get("strategy", "gradual_nurturing")),
            target_triggers=campaign_config.get("target_triggers", []),
            target_member_segments=campaign_config.get("target_segments", []),
            start_date=datetime.fromisoformat(campaign_config.get("start_date", datetime.now(timezone.utc).isoformat())),
            end_date=datetime.fromisoformat(campaign_config.get("end_date", (datetime.now(timezone.utc) + timedelta(days=30)).isoformat())),
            budget_limit=Decimal(str(campaign_config.get("budget_limit", 10000))),
            success_metrics=campaign_config.get("success_metrics", {"target_conversion_rate": 0.15})
        )
        
        self.active_campaigns.append(campaign)
        return campaign