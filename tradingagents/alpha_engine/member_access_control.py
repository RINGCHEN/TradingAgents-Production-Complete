#!/usr/bin/env python3
"""
Member Access Control System
會員分級訪問控制系統 - GPT-OSS整合任務3.2.2

管理不同會員等級對AlphaEngine功能的訪問權限
"""

from enum import Enum
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
from pydantic import BaseModel, Field
from decimal import Decimal

class MembershipTier(str, Enum):
    """會員等級"""
    FREE = "free"
    BASIC = "basic"  
    PREMIUM = "premium"
    VIP = "vip"
    ENTERPRISE = "enterprise"

class AccessLevel(str, Enum):
    """訪問權限等級"""
    NONE = "none"
    READ_ONLY = "read_only"
    LIMITED = "limited"
    FULL = "full"
    UNLIMITED = "unlimited"

class FeatureType(str, Enum):
    """功能類型"""
    ALPHA_INSIGHTS = "alpha_insights"
    NEWS_ANALYSIS = "news_analysis"
    FINANCIAL_REPORTS = "financial_reports"
    TECHNICAL_ANALYSIS = "technical_analysis"
    REAL_TIME_DATA = "real_time_data"
    PORTFOLIO_TRACKING = "portfolio_tracking"
    CUSTOM_ALERTS = "custom_alerts"
    API_ACCESS = "api_access"
    PREMIUM_SUPPORT = "premium_support"
    ADVANCED_ANALYTICS = "advanced_analytics"

class QuotaType(str, Enum):
    """配額類型"""
    DAILY_INSIGHTS = "daily_insights"
    MONTHLY_REPORTS = "monthly_reports"
    API_CALLS_DAILY = "api_calls_daily"
    TRACKED_STOCKS = "tracked_stocks"
    CUSTOM_ALERTS = "custom_alerts"
    DATA_EXPORT = "data_export"

class MemberAccessQuota(BaseModel):
    """會員訪問配額"""
    quota_id: str = Field(..., description="配額ID")
    member_id: str = Field(..., description="會員ID")
    quota_type: QuotaType = Field(..., description="配額類型")
    limit: int = Field(..., description="配額限制")
    used: int = Field(0, description="已使用")
    reset_at: datetime = Field(..., description="重置時間")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FeatureAccess(BaseModel):
    """功能訪問權限"""
    feature_type: FeatureType = Field(..., description="功能類型")
    access_level: AccessLevel = Field(..., description="訪問等級")
    max_requests_per_day: Optional[int] = Field(None, description="每日最大請求數")
    max_requests_per_month: Optional[int] = Field(None, description="每月最大請求數")
    priority_weight: float = Field(1.0, description="優先級權重")
    enabled: bool = Field(True, description="是否啟用")

class MembershipTierConfig(BaseModel):
    """會員等級配置"""
    tier: MembershipTier = Field(..., description="會員等級")
    tier_name: str = Field(..., description="等級名稱")
    monthly_price: Decimal = Field(..., description="月費")
    yearly_price: Optional[Decimal] = Field(None, description="年費")
    features: List[FeatureAccess] = Field(default_factory=list, description="功能權限")
    quotas: Dict[QuotaType, int] = Field(default_factory=dict, description="配額限制")
    priority_support: bool = Field(False, description="是否有優先支援")
    trial_days: int = Field(0, description="試用天數")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MemberProfile(BaseModel):
    """會員檔案"""
    member_id: str = Field(..., description="會員ID")
    username: str = Field(..., description="用戶名")
    email: str = Field(..., description="電子郵件")
    membership_tier: MembershipTier = Field(..., description="會員等級")
    subscription_start: datetime = Field(..., description="訂閱開始時間")
    subscription_end: Optional[datetime] = Field(None, description="訂閱結束時間")
    trial_end: Optional[datetime] = Field(None, description="試用結束時間")
    is_active: bool = Field(True, description="是否活躍")
    last_login: Optional[datetime] = Field(None, description="最後登錄時間")
    total_requests: int = Field(0, description="總請求數")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AccessControlResult(BaseModel):
    """訪問控制結果"""
    allowed: bool = Field(..., description="是否允許")
    reason: str = Field(..., description="原因")
    feature_type: FeatureType = Field(..., description="功能類型")
    member_tier: MembershipTier = Field(..., description="會員等級")
    quota_remaining: Optional[int] = Field(None, description="剩餘配額")
    upgrade_required: bool = Field(False, description="是否需要升級")
    suggested_tier: Optional[MembershipTier] = Field(None, description="建議升級等級")
    retry_after: Optional[datetime] = Field(None, description="重試時間")

class UsageLog(BaseModel):
    """使用記錄"""
    log_id: str = Field(..., description="記錄ID")
    member_id: str = Field(..., description="會員ID")
    feature_type: FeatureType = Field(..., description="功能類型")
    request_count: int = Field(1, description="請求次數")
    success: bool = Field(..., description="是否成功")
    response_time_ms: float = Field(0.0, description="響應時間")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MemberAccessController:
    """會員訪問控制器"""
    
    def __init__(self):
        self.tier_configs = self._initialize_tier_configs()
        self.member_quotas: Dict[str, List[MemberAccessQuota]] = {}
        self.usage_logs: List[UsageLog] = []
        
    def _initialize_tier_configs(self) -> Dict[MembershipTier, MembershipTierConfig]:
        """初始化會員等級配置"""
        configs = {}
        
        # 免費會員
        configs[MembershipTier.FREE] = MembershipTierConfig(
            tier=MembershipTier.FREE,
            tier_name="免費會員",
            monthly_price=Decimal('0'),
            features=[
                FeatureAccess(
                    feature_type=FeatureType.ALPHA_INSIGHTS,
                    access_level=AccessLevel.LIMITED,
                    max_requests_per_day=5,
                    priority_weight=0.1
                ),
                FeatureAccess(
                    feature_type=FeatureType.NEWS_ANALYSIS,
                    access_level=AccessLevel.LIMITED,
                    max_requests_per_day=10,
                    priority_weight=0.1
                ),
                FeatureAccess(
                    feature_type=FeatureType.TECHNICAL_ANALYSIS,
                    access_level=AccessLevel.READ_ONLY,
                    max_requests_per_day=3,
                    priority_weight=0.1
                )
            ],
            quotas={
                QuotaType.DAILY_INSIGHTS: 5,
                QuotaType.MONTHLY_REPORTS: 2,
                QuotaType.API_CALLS_DAILY: 50,
                QuotaType.TRACKED_STOCKS: 3
            },
            trial_days=7
        )
        
        # 基礎會員
        configs[MembershipTier.BASIC] = MembershipTierConfig(
            tier=MembershipTier.BASIC,
            tier_name="基礎會員",
            monthly_price=Decimal('299'),
            yearly_price=Decimal('2990'),
            features=[
                FeatureAccess(
                    feature_type=FeatureType.ALPHA_INSIGHTS,
                    access_level=AccessLevel.LIMITED,
                    max_requests_per_day=25,
                    priority_weight=0.3
                ),
                FeatureAccess(
                    feature_type=FeatureType.NEWS_ANALYSIS,
                    access_level=AccessLevel.FULL,
                    max_requests_per_day=50,
                    priority_weight=0.3
                ),
                FeatureAccess(
                    feature_type=FeatureType.FINANCIAL_REPORTS,
                    access_level=AccessLevel.LIMITED,
                    max_requests_per_day=10,
                    priority_weight=0.3
                ),
                FeatureAccess(
                    feature_type=FeatureType.TECHNICAL_ANALYSIS,
                    access_level=AccessLevel.FULL,
                    max_requests_per_day=20,
                    priority_weight=0.3
                )
            ],
            quotas={
                QuotaType.DAILY_INSIGHTS: 25,
                QuotaType.MONTHLY_REPORTS: 10,
                QuotaType.API_CALLS_DAILY: 200,
                QuotaType.TRACKED_STOCKS: 10,
                QuotaType.CUSTOM_ALERTS: 5
            },
            trial_days=14
        )
        
        # 高級會員
        configs[MembershipTier.PREMIUM] = MembershipTierConfig(
            tier=MembershipTier.PREMIUM,
            tier_name="高級會員",
            monthly_price=Decimal('899'),
            yearly_price=Decimal('8990'),
            features=[
                FeatureAccess(
                    feature_type=FeatureType.ALPHA_INSIGHTS,
                    access_level=AccessLevel.FULL,
                    max_requests_per_day=100,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.NEWS_ANALYSIS,
                    access_level=AccessLevel.FULL,
                    max_requests_per_day=200,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.FINANCIAL_REPORTS,
                    access_level=AccessLevel.FULL,
                    max_requests_per_day=50,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.TECHNICAL_ANALYSIS,
                    access_level=AccessLevel.FULL,
                    max_requests_per_day=100,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.REAL_TIME_DATA,
                    access_level=AccessLevel.FULL,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.PORTFOLIO_TRACKING,
                    access_level=AccessLevel.FULL,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.CUSTOM_ALERTS,
                    access_level=AccessLevel.FULL,
                    priority_weight=0.7
                ),
                FeatureAccess(
                    feature_type=FeatureType.API_ACCESS,
                    access_level=AccessLevel.LIMITED,
                    priority_weight=0.7
                )
            ],
            quotas={
                QuotaType.DAILY_INSIGHTS: 100,
                QuotaType.MONTHLY_REPORTS: 50,
                QuotaType.API_CALLS_DAILY: 1000,
                QuotaType.TRACKED_STOCKS: 50,
                QuotaType.CUSTOM_ALERTS: 25,
                QuotaType.DATA_EXPORT: 10
            },
            priority_support=True,
            trial_days=30
        )
        
        # VIP會員
        configs[MembershipTier.VIP] = MembershipTierConfig(
            tier=MembershipTier.VIP,
            tier_name="VIP會員",
            monthly_price=Decimal('2499'),
            yearly_price=Decimal('24990'),
            features=[
                FeatureAccess(
                    feature_type=FeatureType.ALPHA_INSIGHTS,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.NEWS_ANALYSIS,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.FINANCIAL_REPORTS,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.TECHNICAL_ANALYSIS,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.REAL_TIME_DATA,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.PORTFOLIO_TRACKING,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.CUSTOM_ALERTS,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.API_ACCESS,
                    access_level=AccessLevel.FULL,
                    priority_weight=0.9
                ),
                FeatureAccess(
                    feature_type=FeatureType.ADVANCED_ANALYTICS,
                    access_level=AccessLevel.FULL,
                    priority_weight=0.9
                )
            ],
            quotas={
                QuotaType.DAILY_INSIGHTS: 500,
                QuotaType.MONTHLY_REPORTS: 200,
                QuotaType.API_CALLS_DAILY: 5000,
                QuotaType.TRACKED_STOCKS: 200,
                QuotaType.CUSTOM_ALERTS: 100,
                QuotaType.DATA_EXPORT: 50
            },
            priority_support=True,
            trial_days=30
        )
        
        # 企業會員
        configs[MembershipTier.ENTERPRISE] = MembershipTierConfig(
            tier=MembershipTier.ENTERPRISE,
            tier_name="企業會員",
            monthly_price=Decimal('9999'),
            yearly_price=Decimal('99990'),
            features=[
                FeatureAccess(
                    feature_type=feature_type,
                    access_level=AccessLevel.UNLIMITED,
                    priority_weight=1.0
                ) for feature_type in FeatureType
            ],
            quotas={
                QuotaType.DAILY_INSIGHTS: 2000,
                QuotaType.MONTHLY_REPORTS: 1000,
                QuotaType.API_CALLS_DAILY: 50000,
                QuotaType.TRACKED_STOCKS: 1000,
                QuotaType.CUSTOM_ALERTS: 500,
                QuotaType.DATA_EXPORT: 200
            },
            priority_support=True,
            trial_days=60
        )
        
        return configs
    
    async def check_access(self, member_id: str, feature_type: FeatureType, 
                          member_profile: MemberProfile) -> AccessControlResult:
        """檢查會員訪問權限"""
        
        # 檢查會員狀態
        if not member_profile.is_active:
            return AccessControlResult(
                allowed=False,
                reason="會員帳號未啟用",
                feature_type=feature_type,
                member_tier=member_profile.membership_tier
            )
        
        # 檢查訂閱狀態
        now = datetime.now(timezone.utc)
        if member_profile.subscription_end and now > member_profile.subscription_end:
            # 檢查是否在試用期內
            if member_profile.trial_end and now <= member_profile.trial_end:
                pass  # 試用期內可以使用
            else:
                return AccessControlResult(
                    allowed=False,
                    reason="訂閱已過期",
                    feature_type=feature_type,
                    member_tier=member_profile.membership_tier,
                    upgrade_required=True,
                    suggested_tier=member_profile.membership_tier
                )
        
        # 獲取會員等級配置
        tier_config = self.tier_configs.get(member_profile.membership_tier)
        if not tier_config:
            return AccessControlResult(
                allowed=False,
                reason="無效的會員等級",
                feature_type=feature_type,
                member_tier=member_profile.membership_tier
            )
        
        # 檢查功能權限
        feature_access = None
        for feature in tier_config.features:
            if feature.feature_type == feature_type:
                feature_access = feature
                break
        
        if not feature_access or not feature_access.enabled:
            # 建議升級等級
            suggested_tier = self._suggest_upgrade_tier(feature_type)
            return AccessControlResult(
                allowed=False,
                reason="功能權限不足",
                feature_type=feature_type,
                member_tier=member_profile.membership_tier,
                upgrade_required=True,
                suggested_tier=suggested_tier
            )
        
        # 檢查訪問等級
        if feature_access.access_level == AccessLevel.NONE:
            return AccessControlResult(
                allowed=False,
                reason="功能不可用",
                feature_type=feature_type,
                member_tier=member_profile.membership_tier
            )
        
        # 檢查每日配額
        if feature_access.max_requests_per_day:
            quota_used = await self._get_daily_usage(member_id, feature_type)
            if quota_used >= feature_access.max_requests_per_day:
                reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                return AccessControlResult(
                    allowed=False,
                    reason="每日配額已用完",
                    feature_type=feature_type,
                    member_tier=member_profile.membership_tier,
                    quota_remaining=0,
                    retry_after=reset_time
                )
            
            quota_remaining = feature_access.max_requests_per_day - quota_used
        else:
            quota_remaining = None
        
        return AccessControlResult(
            allowed=True,
            reason="訪問允許",
            feature_type=feature_type,
            member_tier=member_profile.membership_tier,
            quota_remaining=quota_remaining
        )
    
    async def _get_daily_usage(self, member_id: str, feature_type: FeatureType) -> int:
        """獲取每日使用量"""
        today = datetime.now(timezone.utc).date()
        
        usage_count = 0
        for log in self.usage_logs:
            if (log.member_id == member_id and 
                log.feature_type == feature_type and
                log.timestamp.date() == today and
                log.success):
                usage_count += log.request_count
        
        return usage_count
    
    def _suggest_upgrade_tier(self, feature_type: FeatureType) -> Optional[MembershipTier]:
        """建議升級等級"""
        tier_order = [MembershipTier.FREE, MembershipTier.BASIC, 
                     MembershipTier.PREMIUM, MembershipTier.VIP, MembershipTier.ENTERPRISE]
        
        for tier in tier_order:
            config = self.tier_configs.get(tier)
            if config:
                for feature in config.features:
                    if (feature.feature_type == feature_type and 
                        feature.enabled and 
                        feature.access_level != AccessLevel.NONE):
                        return tier
        
        return None
    
    async def log_usage(self, member_id: str, feature_type: FeatureType, 
                       success: bool, response_time_ms: float = 0.0) -> None:
        """記錄使用情況"""
        log = UsageLog(
            log_id=f"log_{member_id}_{feature_type.value}_{int(datetime.now().timestamp())}",
            member_id=member_id,
            feature_type=feature_type,
            success=success,
            response_time_ms=response_time_ms
        )
        
        self.usage_logs.append(log)
    
    def get_tier_config(self, tier: MembershipTier) -> Optional[MembershipTierConfig]:
        """獲取會員等級配置"""
        return self.tier_configs.get(tier)
    
    def get_all_tiers(self) -> List[MembershipTierConfig]:
        """獲取所有會員等級配置"""
        return list(self.tier_configs.values())
    
    async def get_member_usage_statistics(self, member_id: str) -> Dict[str, Any]:
        """獲取會員使用統計"""
        today = datetime.now(timezone.utc).date()
        this_month = datetime.now(timezone.utc).replace(day=1).date()
        
        stats = {
            'member_id': member_id,
            'daily_usage': {},
            'monthly_usage': {},
            'total_requests': 0,
            'success_rate': 0.0,
            'avg_response_time_ms': 0.0,
            'most_used_features': []
        }
        
        member_logs = [log for log in self.usage_logs if log.member_id == member_id]
        
        if not member_logs:
            return stats
        
        # 每日使用統計
        daily_usage = {}
        monthly_usage = {}
        response_times = []
        success_count = 0
        
        for log in member_logs:
            feature = log.feature_type.value
            
            # 每日統計
            if log.timestamp.date() == today:
                if feature not in daily_usage:
                    daily_usage[feature] = 0
                daily_usage[feature] += log.request_count
            
            # 每月統計
            if log.timestamp.date() >= this_month:
                if feature not in monthly_usage:
                    monthly_usage[feature] = 0
                monthly_usage[feature] += log.request_count
            
            # 響應時間
            if log.response_time_ms > 0:
                response_times.append(log.response_time_ms)
            
            # 成功率
            if log.success:
                success_count += 1
        
        stats['daily_usage'] = daily_usage
        stats['monthly_usage'] = monthly_usage
        stats['total_requests'] = len(member_logs)
        stats['success_rate'] = success_count / len(member_logs) if member_logs else 0.0
        stats['avg_response_time_ms'] = sum(response_times) / len(response_times) if response_times else 0.0
        
        # 最常使用的功能
        feature_counts = {}
        for log in member_logs:
            feature = log.feature_type.value
            if feature not in feature_counts:
                feature_counts[feature] = 0
            feature_counts[feature] += log.request_count
        
        stats['most_used_features'] = sorted(
            feature_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return stats

class MembershipUpgradeAnalyzer:
    """會員升級分析器"""
    
    def __init__(self, access_controller: MemberAccessController):
        self.access_controller = access_controller
    
    async def analyze_upgrade_benefits(self, current_tier: MembershipTier, 
                                     target_tier: MembershipTier) -> Dict[str, Any]:
        """分析升級好處"""
        current_config = self.access_controller.get_tier_config(current_tier)
        target_config = self.access_controller.get_tier_config(target_tier)
        
        if not current_config or not target_config:
            return {}
        
        benefits = {
            'tier_upgrade': {
                'from': current_tier.value,
                'to': target_tier.value
            },
            'price_difference': {
                'monthly': float(target_config.monthly_price - current_config.monthly_price),
                'yearly': float(target_config.yearly_price - current_config.yearly_price) if target_config.yearly_price and current_config.yearly_price else None
            },
            'feature_upgrades': [],
            'quota_increases': {},
            'new_features': [],
            'priority_improvements': {}
        }
        
        # 功能升級分析
        current_features = {f.feature_type: f for f in current_config.features}
        target_features = {f.feature_type: f for f in target_config.features}
        
        for feature_type, target_feature in target_features.items():
            current_feature = current_features.get(feature_type)
            
            if not current_feature:
                # 新功能
                benefits['new_features'].append({
                    'feature': feature_type.value,
                    'access_level': target_feature.access_level.value,
                    'daily_limit': target_feature.max_requests_per_day
                })
            elif current_feature.access_level != target_feature.access_level:
                # 功能升級
                benefits['feature_upgrades'].append({
                    'feature': feature_type.value,
                    'from_level': current_feature.access_level.value,
                    'to_level': target_feature.access_level.value,
                    'daily_limit_increase': (target_feature.max_requests_per_day or 0) - (current_feature.max_requests_per_day or 0)
                })
            
            # 優先級改善
            if current_feature and target_feature.priority_weight > current_feature.priority_weight:
                benefits['priority_improvements'][feature_type.value] = {
                    'from': current_feature.priority_weight,
                    'to': target_feature.priority_weight
                }
        
        # 配額增加分析
        for quota_type in target_config.quotas:
            current_quota = current_config.quotas.get(quota_type, 0)
            target_quota = target_config.quotas[quota_type]
            if target_quota > current_quota:
                benefits['quota_increases'][quota_type.value] = {
                    'from': current_quota,
                    'to': target_quota,
                    'increase': target_quota - current_quota
                }
        
        return benefits
    
    async def recommend_tier_for_usage(self, member_id: str, 
                                     usage_stats: Dict[str, Any]) -> Dict[str, Any]:
        """根據使用情況推薦會員等級"""
        recommendation = {
            'current_usage': usage_stats,
            'recommended_tier': None,
            'reasons': [],
            'cost_benefit_analysis': {},
            'upgrade_urgency': 'low'
        }
        
        daily_usage = usage_stats.get('daily_usage', {})
        monthly_usage = usage_stats.get('monthly_usage', {})
        
        # 分析使用模式
        high_usage_features = []
        for feature, usage in daily_usage.items():
            if usage > 20:  # 每日使用超過20次
                high_usage_features.append(feature)
        
        # 根據使用模式推薦等級
        if len(high_usage_features) >= 3:
            recommendation['recommended_tier'] = MembershipTier.VIP
            recommendation['reasons'].append("多功能高頻使用，建議升級至VIP")
            recommendation['upgrade_urgency'] = 'high'
        elif len(high_usage_features) >= 1:
            recommendation['recommended_tier'] = MembershipTier.PREMIUM
            recommendation['reasons'].append("部分功能高頻使用，建議升級至高級會員")
            recommendation['upgrade_urgency'] = 'medium'
        elif sum(daily_usage.values()) > 30:
            recommendation['recommended_tier'] = MembershipTier.BASIC
            recommendation['reasons'].append("整體使用量較高，建議升級至基礎會員")
            recommendation['upgrade_urgency'] = 'medium'
        else:
            recommendation['recommended_tier'] = MembershipTier.FREE
            recommendation['reasons'].append("目前使用量適中，免費會員即可滿足需求")
        
        return recommendation