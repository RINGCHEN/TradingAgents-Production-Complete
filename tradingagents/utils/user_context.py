#!/usr/bin/env python3
"""
TradingAgents 用戶上下文管理
提供用戶會話、權限檢查、使用量追蹤等功能
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json

# 導入現有的會員等級定義
from ..models.membership import TierType
from ..default_config import get_membership_config, DEFAULT_CONFIG

class AnalysisStatus(Enum):
    """分析狀態"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PermissionLevel(Enum):
    """權限等級"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

@dataclass
class UsageStats:
    """使用量統計"""
    daily_analyses: int = 0
    monthly_analyses: int = 0
    concurrent_analyses: int = 0
    last_analysis_time: Optional[datetime] = None
    total_analyses: int = 0
    
    # 按分析師類型統計
    analyst_usage: Dict[str, int] = field(default_factory=dict)
    
    # 重置統計
    last_daily_reset: Optional[datetime] = None
    last_monthly_reset: Optional[datetime] = None
    
    def reset_daily_stats(self):
        """重置每日統計"""
        self.daily_analyses = 0
        self.analyst_usage = {}
        self.last_daily_reset = datetime.now()
    
    def reset_monthly_stats(self):
        """重置每月統計"""
        self.monthly_analyses = 0
        self.last_monthly_reset = datetime.now()
    
    def should_reset_daily(self) -> bool:
        """檢查是否需要重置每日統計"""
        if not self.last_daily_reset:
            return True
        return datetime.now().date() > self.last_daily_reset.date()
    
    def should_reset_monthly(self) -> bool:
        """檢查是否需要重置每月統計"""
        if not self.last_monthly_reset:
            return True
        now = datetime.now()
        last_reset = self.last_monthly_reset
        return (now.year, now.month) > (last_reset.year, last_reset.month)

@dataclass
class AnalysisSession:
    """分析會話"""
    session_id: str
    stock_id: str
    status: AnalysisStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    analysts_used: List[str] = field(default_factory=list)
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    def duration(self) -> Optional[timedelta]:
        """獲取分析持續時間"""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def is_active(self) -> bool:
        """檢查會話是否活躍"""
        return self.status in [AnalysisStatus.PENDING, AnalysisStatus.RUNNING]

@dataclass
class UserPermissions:
    """用戶權限"""
    # 分析師權限
    available_analysts: List[str] = field(default_factory=list)
    max_analysts: int = 3
    
    # 使用量限制
    max_daily_analyses: int = 10
    max_concurrent_analyses: int = 1
    analysis_timeout: int = 60  # 秒
    
    # 功能權限
    features: Dict[str, bool] = field(default_factory=dict)
    
    # 數據訪問權限
    historical_data_days: int = 30
    
    # API 權限
    api_rate_limit: int = 60  # 每分鐘請求數
    
    def can_use_analyst(self, analyst_id: str) -> bool:
        """檢查是否可以使用特定分析師"""
        if self.available_analysts == 'all':
            return True
        return analyst_id in self.available_analysts
    
    def can_use_feature(self, feature_name: str) -> bool:
        """檢查是否可以使用特定功能"""
        return self.features.get(feature_name, False)
    
    def get_max_historical_days(self) -> int:
        """獲取最大歷史數據天數"""
        if self.historical_data_days == -1:
            return 365 * 10  # 10年
        return self.historical_data_days

class UserContext:
    """用戶上下文管理器"""
    
    def __init__(
        self,
        user_id: str,
        membership_tier: TierType,
        session_id: Optional[str] = None,
        permissions: Optional[UserPermissions] = None,
        usage_stats: Optional[UsageStats] = None
    ):
        self.user_id = user_id
        self.membership_tier = membership_tier
        self.session_id = session_id or f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        # 初始化權限
        if permissions:
            self.permissions = permissions
        else:
            self.permissions = self._load_permissions_from_tier()
        
        # 初始化使用量統計
        self.usage_stats = usage_stats or UsageStats()
        
        # 活躍分析會話
        self.active_sessions: Dict[str, AnalysisSession] = {}
        
        # 上下文創建時間
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        
        # 快取配置
        self._config_cache: Optional[Dict[str, Any]] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5分鐘
    
    def _load_permissions_from_tier(self) -> UserPermissions:
        """從會員等級載入權限"""
        try:
            tier_config = get_membership_config(self.membership_tier.value)
            
            return UserPermissions(
                available_analysts=tier_config.get('available_analysts', []),
                max_analysts=tier_config.get('max_analysts', 3),
                max_daily_analyses=tier_config.get('max_daily_analyses', 10),
                max_concurrent_analyses=tier_config.get('max_concurrent_analyses', 1),
                analysis_timeout=tier_config.get('analysis_timeout', 60),
                features=tier_config.get('features', {}),
                historical_data_days=tier_config.get('features', {}).get('historical_data_days', 30),
                api_rate_limit=tier_config.get('api_rate_limit', 60)
            )
        except Exception as e:
            # 如果載入失敗，使用預設的免費會員權限
            return UserPermissions()
    
    def update_activity(self):
        """更新最後活動時間"""
        self.last_activity = datetime.now()
    
    def is_session_expired(self, timeout_minutes: int = 30) -> bool:
        """檢查會話是否過期"""
        if not self.last_activity:
            return True
        
        timeout = timedelta(minutes=timeout_minutes)
        return datetime.now() - self.last_activity > timeout
    
    # ==================== 權限檢查方法 ====================
    
    def can_perform_analysis(self) -> tuple[bool, str]:
        """檢查是否可以執行分析"""
        # 檢查每日配額
        if not self._check_daily_quota():
            return False, f"已達每日分析上限 ({self.permissions.max_daily_analyses} 次)"
        
        # 檢查並發限制
        if not self._check_concurrent_limit():
            active_count = len([s for s in self.active_sessions.values() if s.is_active()])
            return False, f"已達並發分析上限 ({self.permissions.max_concurrent_analyses} 個，目前 {active_count} 個)"
        
        return True, "可以執行分析"
    
    def can_use_analyst(self, analyst_id: str) -> tuple[bool, str]:
        """檢查是否可以使用特定分析師"""
        if not self.permissions.can_use_analyst(analyst_id):
            return False, f"您的會員等級不支援使用 {analyst_id}"
        
        return True, "可以使用該分析師"
    
    def can_use_feature(self, feature_name: str) -> tuple[bool, str]:
        """檢查是否可以使用特定功能"""
        if not self.permissions.can_use_feature(feature_name):
            return False, f"您的會員等級不支援 {feature_name} 功能"
        
        return True, "可以使用該功能"
    
    def can_access_historical_data(self, days_requested: int) -> tuple[bool, str]:
        """檢查是否可以訪問歷史數據"""
        max_days = self.permissions.get_max_historical_days()
        
        if days_requested > max_days:
            return False, f"您的會員等級最多可訪問 {max_days} 天的歷史數據"
        
        return True, "可以訪問歷史數據"
    
    def _check_daily_quota(self) -> bool:
        """檢查每日配額"""
        # 自動重置每日統計
        if self.usage_stats.should_reset_daily():
            self.usage_stats.reset_daily_stats()
        
        if self.permissions.max_daily_analyses == -1:  # 無限制
            return True
        
        return self.usage_stats.daily_analyses < self.permissions.max_daily_analyses
    
    def _check_concurrent_limit(self) -> bool:
        """檢查並發限制"""
        active_count = len([s for s in self.active_sessions.values() if s.is_active()])
        return active_count < self.permissions.max_concurrent_analyses
    
    # ==================== 分析會話管理 ====================
    
    def start_analysis_session(
        self, 
        stock_id: str, 
        analysts: List[str]
    ) -> tuple[bool, str, Optional[AnalysisSession]]:
        """開始分析會話"""
        # 檢查權限
        can_analyze, reason = self.can_perform_analysis()
        if not can_analyze:
            return False, reason, None
        
        # 檢查分析師權限
        for analyst_id in analysts:
            can_use, reason = self.can_use_analyst(analyst_id)
            if not can_use:
                return False, reason, None
        
        # 創建會話
        session_id = f"analysis_{self.user_id}_{stock_id}_{int(datetime.now().timestamp())}"
        session = AnalysisSession(
            session_id=session_id,
            stock_id=stock_id,
            status=AnalysisStatus.PENDING,
            start_time=datetime.now(),
            analysts_used=analysts.copy()
        )
        
        # 添加到活躍會話
        self.active_sessions[session_id] = session
        
        # 更新使用量統計
        self._update_usage_stats(analysts)
        
        return True, "分析會話已開始", session
    
    def update_session_status(
        self, 
        session_id: str, 
        status: AnalysisStatus,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """更新會話狀態"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        session.status = status
        
        if status in [AnalysisStatus.COMPLETED, AnalysisStatus.FAILED, AnalysisStatus.CANCELLED]:
            session.end_time = datetime.now()
            
            if result:
                session.result = result
            
            if error_message:
                session.error_message = error_message
            
            # 更新並發計數
            self.usage_stats.concurrent_analyses = max(0, self.usage_stats.concurrent_analyses - 1)
        
        self.update_activity()
        return True
    
    def get_session(self, session_id: str) -> Optional[AnalysisSession]:
        """獲取分析會話"""
        return self.active_sessions.get(session_id)
    
    def get_active_sessions(self) -> List[AnalysisSession]:
        """獲取所有活躍會話"""
        return [s for s in self.active_sessions.values() if s.is_active()]
    
    def cleanup_expired_sessions(self, timeout_minutes: int = 30):
        """清理過期會話"""
        timeout = timedelta(minutes=timeout_minutes)
        now = datetime.now()
        
        expired_sessions = []
        for session_id, session in self.active_sessions.items():
            if session.is_active() and (now - session.start_time) > timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.update_session_status(session_id, AnalysisStatus.CANCELLED, 
                                     error_message="會話超時")
    
    def _update_usage_stats(self, analysts: List[str]):
        """更新使用量統計"""
        # 自動重置統計
        if self.usage_stats.should_reset_daily():
            self.usage_stats.reset_daily_stats()
        
        if self.usage_stats.should_reset_monthly():
            self.usage_stats.reset_monthly_stats()
        
        # 更新統計
        self.usage_stats.daily_analyses += 1
        self.usage_stats.monthly_analyses += 1
        self.usage_stats.total_analyses += 1
        self.usage_stats.concurrent_analyses += 1
        self.usage_stats.last_analysis_time = datetime.now()
        
        # 更新分析師使用統計
        for analyst_id in analysts:
            self.usage_stats.analyst_usage[analyst_id] = \
                self.usage_stats.analyst_usage.get(analyst_id, 0) + 1
    
    # ==================== 配置和狀態方法 ====================
    
    def get_available_analysts(self) -> List[str]:
        """獲取可用的分析師列表"""
        if self.permissions.available_analysts == 'all':
            return DEFAULT_CONFIG['analysts_config']['enabled_analysts'].copy()
        return self.permissions.available_analysts.copy()
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """獲取使用量摘要"""
        # 自動重置統計
        if self.usage_stats.should_reset_daily():
            self.usage_stats.reset_daily_stats()
        
        return {
            'daily_analyses': self.usage_stats.daily_analyses,
            'daily_limit': self.permissions.max_daily_analyses,
            'daily_remaining': max(0, self.permissions.max_daily_analyses - self.usage_stats.daily_analyses) 
                              if self.permissions.max_daily_analyses != -1 else -1,
            'concurrent_analyses': self.usage_stats.concurrent_analyses,
            'concurrent_limit': self.permissions.max_concurrent_analyses,
            'total_analyses': self.usage_stats.total_analyses,
            'last_analysis': self.usage_stats.last_analysis_time.isoformat() 
                           if self.usage_stats.last_analysis_time else None,
            'analyst_usage': self.usage_stats.analyst_usage.copy()
        }
    
    def get_permissions_summary(self) -> Dict[str, Any]:
        """獲取權限摘要"""
        return {
            'membership_tier': self.membership_tier.value,
            'available_analysts': self.get_available_analysts(),
            'max_analysts': self.permissions.max_analysts,
            'max_daily_analyses': self.permissions.max_daily_analyses,
            'max_concurrent_analyses': self.permissions.max_concurrent_analyses,
            'analysis_timeout': self.permissions.analysis_timeout,
            'features': self.permissions.features.copy(),
            'historical_data_days': self.permissions.historical_data_days,
            'api_rate_limit': self.permissions.api_rate_limit
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'user_id': self.user_id,
            'membership_tier': self.membership_tier.value,
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'permissions': self.get_permissions_summary(),
            'usage': self.get_usage_summary(),
            'active_sessions_count': len(self.get_active_sessions())
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserContext':
        """從字典創建用戶上下文"""
        user_context = cls(
            user_id=data['user_id'],
            membership_tier=TierType(data['membership_tier']),
            session_id=data.get('session_id')
        )
        
        # 恢復時間戳
        if 'created_at' in data:
            user_context.created_at = datetime.fromisoformat(data['created_at'])
        if 'last_activity' in data:
            user_context.last_activity = datetime.fromisoformat(data['last_activity'])
        
        return user_context

# ==================== 工具函數 ====================

def create_user_context(
    user_id: str,
    membership_tier: str,
    session_id: Optional[str] = None
) -> UserContext:
    """創建用戶上下文的便利函數"""
    try:
        tier = TierType(membership_tier.upper())
    except ValueError:
        tier = TierType.FREE  # 預設為免費會員
    
    return UserContext(
        user_id=user_id,
        membership_tier=tier,
        session_id=session_id
    )

def validate_user_context(user_context: UserContext) -> tuple[bool, str]:
    """驗證用戶上下文的有效性"""
    if not user_context.user_id:
        return False, "用戶 ID 不能為空"
    
    if user_context.is_session_expired():
        return False, "用戶會話已過期"
    
    if not isinstance(user_context.membership_tier, TierType):
        return False, "無效的會員等級"
    
    return True, "用戶上下文有效"

async def cleanup_expired_contexts(
    contexts: Dict[str, UserContext],
    timeout_minutes: int = 30
) -> int:
    """清理過期的用戶上下文"""
    expired_count = 0
    expired_keys = []
    
    for user_id, context in contexts.items():
        if context.is_session_expired(timeout_minutes):
            expired_keys.append(user_id)
            expired_count += 1
        else:
            # 清理過期的分析會話
            context.cleanup_expired_sessions(timeout_minutes)
    
    # 移除過期的上下文
    for key in expired_keys:
        del contexts[key]
    
    return expired_count

# ==================== 上下文管理器 ====================

class UserContextManager:
    """用戶上下文管理器"""
    
    def __init__(self):
        self.contexts: Dict[str, UserContext] = {}
        self.cleanup_interval = 300  # 5分鐘清理一次
        self.last_cleanup = datetime.now()
    
    def get_or_create_context(
        self,
        user_id: str,
        membership_tier: str,
        session_id: Optional[str] = None
    ) -> UserContext:
        """獲取或創建用戶上下文"""
        # 定期清理過期上下文
        self._periodic_cleanup()
        
        if user_id in self.contexts:
            context = self.contexts[user_id]
            context.update_activity()
            return context
        
        # 創建新的上下文
        context = create_user_context(user_id, membership_tier, session_id)
        self.contexts[user_id] = context
        return context
    
    def get_context(self, user_id: str) -> Optional[UserContext]:
        """獲取用戶上下文"""
        return self.contexts.get(user_id)
    
    def remove_context(self, user_id: str) -> bool:
        """移除用戶上下文"""
        if user_id in self.contexts:
            del self.contexts[user_id]
            return True
        return False
    
    def get_active_contexts_count(self) -> int:
        """獲取活躍上下文數量"""
        return len(self.contexts)
    
    def _periodic_cleanup(self):
        """定期清理"""
        now = datetime.now()
        if (now - self.last_cleanup).seconds > self.cleanup_interval:
            asyncio.create_task(cleanup_expired_contexts(self.contexts))
            self.last_cleanup = now

# 全局上下文管理器實例
_context_manager = UserContextManager()

def get_context_manager() -> UserContextManager:
    """獲取全局上下文管理器"""
    return _context_manager