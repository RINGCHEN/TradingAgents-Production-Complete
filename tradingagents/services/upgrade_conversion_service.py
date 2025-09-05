#!/usr/bin/env python3
"""
TradingAgents 會員升級轉換服務
處理國際數據訪問時的會員升級提示、試用機制和轉換追蹤
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib

from ..models.membership import TierType
from ..utils.user_context import UserContext
from ..default_config import DEFAULT_CONFIG

# 設置日誌
logger = logging.getLogger(__name__)

class UpgradePromptType(Enum):
    """升級提示類型"""
    TRIAL_OFFER = "trial_offer"           # 試用優惠
    FEATURE_LOCKED = "feature_locked"     # 功能鎖定
    QUOTA_EXCEEDED = "quota_exceeded"     # 配額超限
    VALUE_PROPOSITION = "value_proposition" # 價值主張

class ConversionEventType(Enum):
    """轉換事件類型"""
    PROMPT_SHOWN = "prompt_shown"         # 提示顯示
    TRIAL_STARTED = "trial_started"       # 開始試用
    UPGRADE_CLICKED = "upgrade_clicked"   # 點擊升級
    UPGRADE_COMPLETED = "upgrade_completed" # 完成升級
    TRIAL_CONVERTED = "trial_converted"   # 試用轉換

@dataclass
class UpgradePrompt:
    """升級提示"""
    prompt_id: str
    user_id: str
    prompt_type: UpgradePromptType
    current_tier: TierType
    target_tier: TierType
    title: str
    message: str
    benefits: List[str]
    cta_text: str  # Call to Action 文字
    trial_offer: Optional[Dict[str, Any]] = None
    discount_offer: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'prompt_id': self.prompt_id,
            'prompt_type': self.prompt_type.value,
            'current_tier': self.current_tier.value,
            'target_tier': self.target_tier.value,
            'title': self.title,
            'message': self.message,
            'benefits': self.benefits,
            'cta_text': self.cta_text,
            'trial_offer': self.trial_offer,
            'discount_offer': self.discount_offer,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

@dataclass
class TrialUsage:
    """試用使用記錄"""
    user_id: str
    feature_type: str  # 'international_data'
    usage_count: int = 0
    max_usage: int = 3
    first_used_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    trial_expired: bool = False
    
    def can_use_trial(self) -> bool:
        """檢查是否可以使用試用"""
        return self.usage_count < self.max_usage and not self.trial_expired
    
    def use_trial(self) -> bool:
        """使用一次試用"""
        if not self.can_use_trial():
            return False
        
        self.usage_count += 1
        self.last_used_at = datetime.now()
        
        if self.first_used_at is None:
            self.first_used_at = datetime.now()
        
        return True
    
    def get_remaining_trials(self) -> int:
        """獲取剩餘試用次數"""
        return max(0, self.max_usage - self.usage_count)

@dataclass
class ConversionEvent:
    """轉換事件"""
    event_id: str
    user_id: str
    event_type: ConversionEventType
    prompt_id: Optional[str] = None
    current_tier: Optional[TierType] = None
    target_tier: Optional[TierType] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'event_id': self.event_id,
            'user_id': self.user_id,
            'event_type': self.event_type.value,
            'prompt_id': self.prompt_id,
            'current_tier': self.current_tier.value if self.current_tier else None,
            'target_tier': self.target_tier.value if self.target_tier else None,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

class UpgradeConversionService:
    """會員升級轉換服務"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化服務"""
        self.config = config or DEFAULT_CONFIG
        
        # 試用使用記錄（實際應該存儲在數據庫中）
        self.trial_usage: Dict[str, TrialUsage] = {}
        
        # 轉換事件記錄
        self.conversion_events: List[ConversionEvent] = []
        
        # 升級提示模板
        self.prompt_templates = self._initialize_prompt_templates()
        
        # A/B 測試配置
        self.ab_test_config = self.config.get('upgrade_conversion', {}).get('ab_testing', {})
        
        logger.info("會員升級轉換服務初始化完成")
    
    def _initialize_prompt_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化升級提示模板"""
        return {
            'international_data_trial': {
                'title': '🌍 解鎖全球市場數據',
                'message': '您正在嘗試訪問國際股票數據。我們為您提供 3 次免費體驗機會！',
                'benefits': [
                    '實時美股、港股、日股等全球市場數據',
                    '跨市場投資組合分析和風險評估',
                    '全球經濟事件影響分析',
                    '國際同業公司比較分析'
                ],
                'cta_text': '開始免費體驗',
                'trial_offer': {
                    'trial_count': 3,
                    'feature': 'international_data',
                    'expires_days': 7
                }
            },
            'international_data_upgrade': {
                'title': '🚀 升級至 Gold 會員',
                'message': '您的免費體驗已用完。升級至 Gold 會員，享受無限制的全球市場數據！',
                'benefits': [
                    '無限制訪問全球股票數據',
                    '高級技術分析工具',
                    '個人化投資建議',
                    '優先客戶支持'
                ],
                'cta_text': '立即升級 Gold 會員',
                'discount_offer': {
                    'discount_percent': 20,
                    'expires_days': 3,
                    'promo_code': 'GLOBAL20'
                }
            },
            'feature_value_proposition': {
                'title': '💎 發現全球投資機會',
                'message': '加入超過 10,000 位投資者，使用我們的國際數據功能獲得更好的投資回報！',
                'benefits': [
                    '平均投資回報提升 15%',
                    '風險分散效果提升 30%',
                    '發現隱藏的投資機會',
                    '專業級市場分析工具'
                ],
                'cta_text': '查看成功案例',
                'success_stories': [
                    {
                        'user': '張先生',
                        'story': '通過國際數據分析，發現了美股科技股的投資機會，3個月獲得25%回報',
                        'return': '25%'
                    },
                    {
                        'user': '李女士',
                        'story': '利用跨市場分析，成功規避了單一市場風險，保護了投資組合',
                        'return': '風險降低40%'
                    }
                ]
            }
        }
    
    async def check_international_data_access(self, user_context: UserContext, symbol: str) -> Tuple[bool, Optional[UpgradePrompt]]:
        """
        檢查國際數據訪問權限
        
        Args:
            user_context: 用戶上下文
            symbol: 股票代號
            
        Returns:
            (是否允許訪問, 升級提示)
        """
        # 檢查是否為國際股票
        if not self._is_international_symbol(symbol):
            return True, None
        
        # 檢查用戶等級
        if user_context.membership_tier in [TierType.GOLD, TierType.DIAMOND]:
            return True, None
        
        # 檢查試用使用情況
        trial_key = f"{user_context.user_id}_international_data"
        trial_usage = self.trial_usage.get(trial_key)
        
        if trial_usage is None:
            # 首次訪問，創建試用記錄並顯示試用提示
            trial_usage = TrialUsage(
                user_id=user_context.user_id,
                feature_type='international_data'
            )
            self.trial_usage[trial_key] = trial_usage
            
            prompt = await self._create_trial_offer_prompt(user_context)
            return False, prompt
        
        elif trial_usage.can_use_trial():
            # 還有試用次數，使用試用
            trial_usage.use_trial()
            
            # 記錄試用使用事件
            await self._track_conversion_event(
                user_context.user_id,
                ConversionEventType.TRIAL_STARTED,
                metadata={
                    'symbol': symbol,
                    'remaining_trials': trial_usage.get_remaining_trials()
                }
            )
            
            return True, None
        
        else:
            # 試用已用完，顯示升級提示
            prompt = await self._create_upgrade_prompt(user_context, trial_usage)
            return False, prompt
    
    async def _create_trial_offer_prompt(self, user_context: UserContext) -> UpgradePrompt:
        """創建試用優惠提示"""
        template = self.prompt_templates['international_data_trial']
        
        prompt_id = self._generate_prompt_id(user_context.user_id, 'trial_offer')
        
        prompt = UpgradePrompt(
            prompt_id=prompt_id,
            user_id=user_context.user_id,
            prompt_type=UpgradePromptType.TRIAL_OFFER,
            current_tier=user_context.membership_tier,
            target_tier=TierType.GOLD,
            title=template['title'],
            message=template['message'],
            benefits=template['benefits'],
            cta_text=template['cta_text'],
            trial_offer=template['trial_offer'],
            expires_at=datetime.now() + timedelta(days=7)
        )
        
        # 記錄提示顯示事件
        await self._track_conversion_event(
            user_context.user_id,
            ConversionEventType.PROMPT_SHOWN,
            prompt_id=prompt_id,
            current_tier=user_context.membership_tier,
            target_tier=TierType.GOLD,
            metadata={'prompt_type': 'trial_offer'}
        )
        
        return prompt
    
    async def _create_upgrade_prompt(self, user_context: UserContext, trial_usage: TrialUsage) -> UpgradePrompt:
        """創建升級提示"""
        template = self.prompt_templates['international_data_upgrade']
        
        prompt_id = self._generate_prompt_id(user_context.user_id, 'upgrade')
        
        prompt = UpgradePrompt(
            prompt_id=prompt_id,
            user_id=user_context.user_id,
            prompt_type=UpgradePromptType.FEATURE_LOCKED,
            current_tier=user_context.membership_tier,
            target_tier=TierType.GOLD,
            title=template['title'],
            message=template['message'],
            benefits=template['benefits'],
            cta_text=template['cta_text'],
            discount_offer=template['discount_offer'],
            expires_at=datetime.now() + timedelta(days=3)
        )
        
        # 記錄提示顯示事件
        await self._track_conversion_event(
            user_context.user_id,
            ConversionEventType.PROMPT_SHOWN,
            prompt_id=prompt_id,
            current_tier=user_context.membership_tier,
            target_tier=TierType.GOLD,
            metadata={
                'prompt_type': 'upgrade',
                'trial_usage_count': trial_usage.usage_count,
                'trial_first_used': trial_usage.first_used_at.isoformat() if trial_usage.first_used_at else None
            }
        )
        
        return prompt
    
    async def get_value_proposition_content(self, user_context: UserContext) -> Dict[str, Any]:
        """獲取價值主張內容"""
        template = self.prompt_templates['feature_value_proposition']
        
        return {
            'title': template['title'],
            'message': template['message'],
            'benefits': template['benefits'],
            'success_stories': template.get('success_stories', []),
            'statistics': {
                'active_users': 10000,
                'average_return_improvement': '15%',
                'risk_reduction': '30%',
                'satisfaction_rate': '95%'
            },
            'pricing': await self._get_pricing_info(user_context)
        }
    
    async def _get_pricing_info(self, user_context: UserContext) -> Dict[str, Any]:
        """獲取定價信息"""
        base_pricing = {
            TierType.GOLD: {
                'monthly': 299,
                'yearly': 2999,
                'features': [
                    '無限制全球股票數據',
                    '高級技術分析',
                    '個人化建議',
                    '優先支持'
                ]
            },
            TierType.DIAMOND: {
                'monthly': 899,
                'yearly': 8999,
                'features': [
                    'Gold 會員所有功能',
                    '機構級數據',
                    '專屬投資顧問',
                    '定制化報告'
                ]
            }
        }
        
        # 檢查是否有折扣
        discount = await self._get_user_discount(user_context.user_id)
        
        if discount:
            for tier_info in base_pricing.values():
                tier_info['original_monthly'] = tier_info['monthly']
                tier_info['original_yearly'] = tier_info['yearly']
                tier_info['monthly'] = int(tier_info['monthly'] * (1 - discount['percent'] / 100))
                tier_info['yearly'] = int(tier_info['yearly'] * (1 - discount['percent'] / 100))
                tier_info['discount'] = discount
        
        return base_pricing
    
    async def _get_user_discount(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶折扣信息"""
        # 檢查是否為新用戶折扣
        trial_key = f"{user_id}_international_data"
        trial_usage = self.trial_usage.get(trial_key)
        
        if trial_usage and trial_usage.usage_count > 0:
            return {
                'percent': 20,
                'code': 'GLOBAL20',
                'expires_at': (datetime.now() + timedelta(days=3)).isoformat(),
                'description': '首次升級專享 20% 折扣'
            }
        
        return None
    
    async def track_upgrade_click(self, user_id: str, prompt_id: str, target_tier: TierType) -> bool:
        """追蹤升級點擊事件"""
        await self._track_conversion_event(
            user_id,
            ConversionEventType.UPGRADE_CLICKED,
            prompt_id=prompt_id,
            target_tier=target_tier,
            metadata={'source': 'upgrade_prompt'}
        )
        
        return True
    
    async def track_upgrade_completion(self, user_id: str, old_tier: TierType, new_tier: TierType, prompt_id: str = None) -> bool:
        """追蹤升級完成事件"""
        await self._track_conversion_event(
            user_id,
            ConversionEventType.UPGRADE_COMPLETED,
            prompt_id=prompt_id,
            current_tier=old_tier,
            target_tier=new_tier,
            metadata={
                'conversion_source': 'international_data_prompt' if prompt_id else 'direct',
                'upgrade_value': self._calculate_upgrade_value(old_tier, new_tier)
            }
        )
        
        # 檢查是否為試用轉換
        trial_key = f"{user_id}_international_data"
        trial_usage = self.trial_usage.get(trial_key)
        
        if trial_usage and trial_usage.usage_count > 0:
            await self._track_conversion_event(
                user_id,
                ConversionEventType.TRIAL_CONVERTED,
                current_tier=old_tier,
                target_tier=new_tier,
                metadata={
                    'trial_usage_count': trial_usage.usage_count,
                    'days_to_conversion': (datetime.now() - trial_usage.first_used_at).days if trial_usage.first_used_at else 0
                }
            )
        
        return True
    
    async def get_conversion_analytics(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """獲取轉換分析數據"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # 過濾時間範圍內的事件
        filtered_events = [
            event for event in self.conversion_events
            if start_date <= event.timestamp <= end_date
        ]
        
        # 統計各類事件
        event_counts = {}
        for event_type in ConversionEventType:
            event_counts[event_type.value] = len([
                e for e in filtered_events if e.event_type == event_type
            ])
        
        # 計算轉換率
        prompts_shown = event_counts.get('prompt_shown', 0)
        upgrades_completed = event_counts.get('upgrade_completed', 0)
        trials_started = event_counts.get('trial_started', 0)
        trials_converted = event_counts.get('trial_converted', 0)
        
        conversion_rate = (upgrades_completed / prompts_shown * 100) if prompts_shown > 0 else 0
        trial_conversion_rate = (trials_converted / trials_started * 100) if trials_started > 0 else 0
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'event_counts': event_counts,
            'metrics': {
                'conversion_rate': round(conversion_rate, 2),
                'trial_conversion_rate': round(trial_conversion_rate, 2),
                'total_revenue': self._calculate_total_revenue(filtered_events),
                'average_time_to_conversion': self._calculate_average_conversion_time(filtered_events)
            },
            'trial_usage_stats': self._get_trial_usage_stats()
        }
    
    def _is_international_symbol(self, symbol: str) -> bool:
        """檢查是否為國際股票代號"""
        # 台股代號通常是4位數字
        if symbol.isdigit() and len(symbol) == 4:
            return False
        
        # 美股代號通常是字母
        if symbol.isalpha():
            return True
        
        # 其他格式的國際股票代號
        international_patterns = [
            '.HK',  # 港股
            '.T',   # 日股
            '.L',   # 英股
        ]
        
        return any(symbol.endswith(pattern) for pattern in international_patterns)
    
    def _generate_prompt_id(self, user_id: str, prompt_type: str) -> str:
        """生成提示ID"""
        timestamp = int(datetime.now().timestamp())
        content = f"{user_id}_{prompt_type}_{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]  # 安全修復：使用SHA256替換MD5
    
    async def _track_conversion_event(
        self,
        user_id: str,
        event_type: ConversionEventType,
        prompt_id: str = None,
        current_tier: TierType = None,
        target_tier: TierType = None,
        metadata: Dict[str, Any] = None
    ):
        """追蹤轉換事件"""
        event_id = hashlib.sha256(f"{user_id}_{event_type.value}_{datetime.now().timestamp()}".encode()).hexdigest()[:16]  # 安全修復：使用SHA256替換MD5
        
        event = ConversionEvent(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            prompt_id=prompt_id,
            current_tier=current_tier,
            target_tier=target_tier,
            metadata=metadata or {}
        )
        
        self.conversion_events.append(event)
        
        logger.info(f"轉換事件追蹤: {event_type.value} - 用戶 {user_id}")
    
    def _calculate_upgrade_value(self, old_tier: TierType, new_tier: TierType) -> float:
        """計算升級價值"""
        tier_values = {
            TierType.FREE: 0,
            TierType.GOLD: 299,
            TierType.DIAMOND: 899
        }
        
        return tier_values.get(new_tier, 0) - tier_values.get(old_tier, 0)
    
    def _calculate_total_revenue(self, events: List[ConversionEvent]) -> float:
        """計算總收入"""
        total = 0
        for event in events:
            if event.event_type == ConversionEventType.UPGRADE_COMPLETED:
                total += event.metadata.get('upgrade_value', 0)
        return total
    
    def _calculate_average_conversion_time(self, events: List[ConversionEvent]) -> float:
        """計算平均轉換時間（小時）"""
        conversion_times = []
        
        # 按用戶分組事件
        user_events = {}
        for event in events:
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)
        
        # 計算每個用戶的轉換時間
        for user_id, user_event_list in user_events.items():
            user_event_list.sort(key=lambda x: x.timestamp)
            
            first_prompt = None
            upgrade_completion = None
            
            for event in user_event_list:
                if event.event_type == ConversionEventType.PROMPT_SHOWN and first_prompt is None:
                    first_prompt = event
                elif event.event_type == ConversionEventType.UPGRADE_COMPLETED:
                    upgrade_completion = event
                    break
            
            if first_prompt and upgrade_completion:
                time_diff = upgrade_completion.timestamp - first_prompt.timestamp
                conversion_times.append(time_diff.total_seconds() / 3600)  # 轉換為小時
        
        return sum(conversion_times) / len(conversion_times) if conversion_times else 0
    
    def _get_trial_usage_stats(self) -> Dict[str, Any]:
        """獲取試用使用統計"""
        total_trials = len(self.trial_usage)
        active_trials = len([t for t in self.trial_usage.values() if t.can_use_trial()])
        completed_trials = len([t for t in self.trial_usage.values() if not t.can_use_trial()])
        
        if total_trials == 0:
            return {
                'total_trials': 0,
                'active_trials': 0,
                'completed_trials': 0,
                'average_usage': 0
            }
        
        total_usage = sum(t.usage_count for t in self.trial_usage.values())
        average_usage = total_usage / total_trials
        
        return {
            'total_trials': total_trials,
            'active_trials': active_trials,
            'completed_trials': completed_trials,
            'average_usage': round(average_usage, 2)
        }