#!/usr/bin/env python3
"""
Member Permission Bridge - 會員權限橋接器
天工 (TianGong) - 連接現有會員系統與AI分析功能的權限控制層

此模組負責：
1. 會員權限檢查和控制
2. AI分析配額管理
3. 功能權限映射
4. 使用量追蹤和限制
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# 導入現有會員系統
try:
    from ..models.user import User, MembershipTier
    from ..models.membership import TierType
    from ..database.database import get_db
    from sqlalchemy.orm import Session
except ImportError:
    # 如果導入失敗，提供備用定義
    class MembershipTier:
        FREE = "FREE"
        GOLD = "GOLD"
        DIAMOND = "DIAMOND"
    
    class TierType:
        FREE = "FREE"
        GOLD = "GOLD"
        DIAMOND = "DIAMOND"

class AnalysisType(Enum):
    """分析類型"""
    BASIC_TECHNICAL = "basic_technical"         # 基礎技術分析
    FUNDAMENTAL = "fundamental"                 # 基本面分析
    NEWS_SENTIMENT = "news_sentiment"           # 新聞情緒分析
    INSTITUTIONAL_FLOW = "institutional_flow"   # 法人進出分析
    RISK_ASSESSMENT = "risk_assessment"         # 風險評估
    COMPREHENSIVE = "comprehensive"             # 綜合分析
    TAIWAN_SPECIFIC = "taiwan_specific"         # 台股專業分析

class PermissionLevel(Enum):
    """權限級別"""
    DENIED = "denied"           # 拒絕存取
    LIMITED = "limited"         # 限制存取
    STANDARD = "standard"       # 標準存取
    PREMIUM = "premium"         # 進階存取
    UNLIMITED = "unlimited"     # 無限制存取

@dataclass
class AnalysisQuota:
    """分析配額"""
    daily_limit: int
    monthly_limit: int
    concurrent_limit: int
    daily_used: int = 0
    monthly_used: int = 0
    current_concurrent: int = 0
    last_reset_daily: str = ""
    last_reset_monthly: str = ""
    
    def __post_init__(self):
        today = datetime.now().strftime('%Y-%m-%d')
        if not self.last_reset_daily:
            self.last_reset_daily = today
        if not self.last_reset_monthly:
            self.last_reset_monthly = datetime.now().strftime('%Y-%m')

@dataclass
class AnalysisPermission:
    """分析權限"""
    analysis_type: AnalysisType
    permission_level: PermissionLevel
    quota: Optional[AnalysisQuota] = None
    features_enabled: List[str] = None
    restrictions: List[str] = None
    
    def __post_init__(self):
        if self.features_enabled is None:
            self.features_enabled = []
        if self.restrictions is None:
            self.restrictions = []

@dataclass
class UserContext:
    """用戶上下文 (與原工程師規劃兼容)"""
    user_id: str
    membership_tier: str
    email: Optional[str] = None
    subscription_status: str = "active"
    permissions: Optional[Dict[str, Any]] = None
    quota_info: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = {}
        if self.quota_info is None:
            self.quota_info = {}

class MemberPermissionBridge:
    """會員權限橋接器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 權限配置映射
        self.tier_permissions = self._initialize_tier_permissions()
        
        # 快取
        self.permission_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = 300  # 5分鐘快取
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _initialize_tier_permissions(self) -> Dict[str, Dict[str, Any]]:
        """初始化會員等級權限配置"""
        return {
            "FREE": {
                "analysis_quota": {
                    "daily_limit": 5,
                    "monthly_limit": 100,
                    "concurrent_limit": 1
                },
                "allowed_analysis_types": [
                    AnalysisType.BASIC_TECHNICAL.value,
                    AnalysisType.NEWS_SENTIMENT.value
                ],
                "features": [
                    "basic_charts",
                    "simple_recommendations",
                    "limited_history"
                ],
                "restrictions": [
                    "no_api_access",
                    "no_export",
                    "watermarked_reports",
                    "limited_data_depth"
                ],
                "max_analysis_complexity": 1
            },
            "GOLD": {
                "analysis_quota": {
                    "daily_limit": 25,
                    "monthly_limit": 500,
                    "concurrent_limit": 3
                },
                "allowed_analysis_types": [
                    AnalysisType.BASIC_TECHNICAL.value,
                    AnalysisType.FUNDAMENTAL.value,
                    AnalysisType.NEWS_SENTIMENT.value,
                    AnalysisType.INSTITUTIONAL_FLOW.value,
                    AnalysisType.TAIWAN_SPECIFIC.value
                ],
                "features": [
                    "advanced_charts",
                    "detailed_analysis",
                    "export_pdf",
                    "api_access",
                    "custom_alerts",
                    "extended_history"
                ],
                "restrictions": [
                    "no_bulk_export",
                    "limited_api_calls"
                ],
                "max_analysis_complexity": 3
            },
            "DIAMOND": {
                "analysis_quota": {
                    "daily_limit": -1,  # 無限制
                    "monthly_limit": -1,
                    "concurrent_limit": 10
                },
                "allowed_analysis_types": [
                    AnalysisType.BASIC_TECHNICAL.value,
                    AnalysisType.FUNDAMENTAL.value,
                    AnalysisType.NEWS_SENTIMENT.value,
                    AnalysisType.INSTITUTIONAL_FLOW.value,
                    AnalysisType.RISK_ASSESSMENT.value,
                    AnalysisType.COMPREHENSIVE.value,
                    AnalysisType.TAIWAN_SPECIFIC.value
                ],
                "features": [
                    "all_chart_types",
                    "comprehensive_analysis",
                    "all_export_formats",
                    "unlimited_api",
                    "priority_processing",
                    "custom_models",
                    "white_label",
                    "full_history",
                    "real_time_alerts"
                ],
                "restrictions": [],
                "max_analysis_complexity": 5
            }
        }
    
    async def get_user_context(self, user_id: str) -> Optional[UserContext]:
        """獲取用戶上下文"""
        try:
            # 檢查快取
            cache_key = f"user_context_{user_id}"
            if cache_key in self.permission_cache:
                cached_data = self.permission_cache[cache_key]
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_duration:
                    return UserContext(**cached_data['data'])
            
            # 從資料庫獲取用戶資訊
            user_data = await self._fetch_user_from_db(user_id)
            
            if not user_data:
                self.logger.warning(f"用戶不存在: {user_id}")
                return None
            
            # 創建用戶上下文
            user_context = UserContext(
                user_id=user_id,
                membership_tier=user_data.get('membership_tier', 'FREE'),
                email=user_data.get('email'),
                subscription_status=user_data.get('subscription_status', 'active'),
                permissions=await self._get_user_permissions(user_data),
                quota_info=await self._get_user_quota_info(user_id, user_data.get('membership_tier', 'FREE'))
            )
            
            # 快取結果
            self.permission_cache[cache_key] = {
                'data': asdict(user_context),
                'timestamp': datetime.now().timestamp()
            }
            
            return user_context
            
        except Exception as e:
            self.logger.error(f"獲取用戶上下文失敗: {str(e)}")
            return None
    
    async def _fetch_user_from_db(self, user_id: str) -> Optional[Dict[str, Any]]:
        """從資料庫獲取用戶資訊"""
        try:
            # 這裡應該與實際的資料庫整合
            # 暫時返回模擬數據
            
            # 模擬不同等級的用戶
            if user_id.startswith('diamond_'):
                return {
                    'user_id': user_id,
                    'email': f'{user_id}@example.com',
                    'membership_tier': 'DIAMOND',
                    'subscription_status': 'active'
                }
            elif user_id.startswith('gold_'):
                return {
                    'user_id': user_id,
                    'email': f'{user_id}@example.com',
                    'membership_tier': 'GOLD',
                    'subscription_status': 'active'
                }
            else:
                return {
                    'user_id': user_id,
                    'email': f'{user_id}@example.com',
                    'membership_tier': 'FREE',
                    'subscription_status': 'active'
                }
                
        except Exception as e:
            self.logger.error(f"資料庫查詢失敗: {str(e)}")
            return None
    
    async def _get_user_permissions(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """獲取用戶權限"""
        tier = user_data.get('membership_tier', 'FREE')
        tier_config = self.tier_permissions.get(tier, self.tier_permissions['FREE'])
        
        return {
            'allowed_analysis_types': tier_config['allowed_analysis_types'],
            'features': tier_config['features'],
            'restrictions': tier_config['restrictions'],
            'max_analysis_complexity': tier_config['max_analysis_complexity']
        }
    
    async def _get_user_quota_info(self, user_id: str, tier: str) -> Dict[str, Any]:
        """獲取用戶配額資訊"""
        tier_config = self.tier_permissions.get(tier, self.tier_permissions['FREE'])
        quota_config = tier_config['analysis_quota']
        
        # 這裡應該從資料庫或Redis獲取實際使用量
        # 暫時返回模擬數據
        
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        
        return {
            'daily_limit': quota_config['daily_limit'],
            'monthly_limit': quota_config['monthly_limit'],
            'concurrent_limit': quota_config['concurrent_limit'],
            'daily_used': 0,  # 應該從資料庫獲取
            'monthly_used': 0,  # 應該從資料庫獲取
            'current_concurrent': 0,  # 應該從Redis獲取
            'last_reset_daily': today,
            'last_reset_monthly': current_month
        }
    
    async def check_analysis_permission(
        self, 
        user_context: UserContext, 
        analysis_type: AnalysisType
    ) -> Dict[str, Any]:
        """檢查分析權限"""
        
        if not user_context:
            return {
                'allowed': False,
                'reason': 'user_not_found',
                'message': '用戶不存在或未登入'
            }
        
        # 檢查訂閱狀態
        if user_context.subscription_status != 'active':
            return {
                'allowed': False,
                'reason': 'subscription_inactive',
                'message': '訂閱狀態不活躍'
            }
        
        # 檢查分析類型權限
        allowed_types = user_context.permissions.get('allowed_analysis_types', [])
        if analysis_type.value not in allowed_types:
            return {
                'allowed': False,
                'reason': 'analysis_type_not_allowed',
                'message': f'您的會員等級不支援 {analysis_type.value} 分析',
                'required_tier': self._get_required_tier_for_analysis(analysis_type)
            }
        
        # 檢查配額
        quota_check = await self._check_quota(user_context)
        if not quota_check['available']:
            return {
                'allowed': False,
                'reason': 'quota_exceeded',
                'message': quota_check['message'],
                'quota_info': quota_check
            }
        
        return {
            'allowed': True,
            'permission_level': self._get_permission_level(user_context, analysis_type),
            'features_enabled': self._get_enabled_features(user_context, analysis_type),
            'restrictions': user_context.permissions.get('restrictions', [])
        }
    
    def _get_required_tier_for_analysis(self, analysis_type: AnalysisType) -> str:
        """獲取分析所需的最低會員等級"""
        type_tier_mapping = {
            AnalysisType.BASIC_TECHNICAL: 'FREE',
            AnalysisType.NEWS_SENTIMENT: 'FREE',
            AnalysisType.FUNDAMENTAL: 'GOLD',
            AnalysisType.INSTITUTIONAL_FLOW: 'GOLD',
            AnalysisType.TAIWAN_SPECIFIC: 'GOLD',
            AnalysisType.RISK_ASSESSMENT: 'DIAMOND',
            AnalysisType.COMPREHENSIVE: 'DIAMOND'
        }
        return type_tier_mapping.get(analysis_type, 'DIAMOND')
    
    async def _check_quota(self, user_context: UserContext) -> Dict[str, Any]:
        """檢查配額"""
        quota_info = user_context.quota_info
        
        if not quota_info:
            return {
                'available': False,
                'message': '無法獲取配額資訊'
            }
        
        daily_limit = quota_info.get('daily_limit', 0)
        monthly_limit = quota_info.get('monthly_limit', 0)
        concurrent_limit = quota_info.get('concurrent_limit', 1)
        
        daily_used = quota_info.get('daily_used', 0)
        monthly_used = quota_info.get('monthly_used', 0)
        current_concurrent = quota_info.get('current_concurrent', 0)
        
        # 檢查每日配額
        if daily_limit > 0 and daily_used >= daily_limit:
            return {
                'available': False,
                'message': f'今日分析次數已達上限 ({daily_used}/{daily_limit})',
                'type': 'daily_limit_exceeded'
            }
        
        # 檢查每月配額
        if monthly_limit > 0 and monthly_used >= monthly_limit:
            return {
                'available': False,
                'message': f'本月分析次數已達上限 ({monthly_used}/{monthly_limit})',
                'type': 'monthly_limit_exceeded'
            }
        
        # 檢查並發限制
        if current_concurrent >= concurrent_limit:
            return {
                'available': False,
                'message': f'同時進行的分析已達上限 ({current_concurrent}/{concurrent_limit})',
                'type': 'concurrent_limit_exceeded'
            }
        
        return {
            'available': True,
            'daily_remaining': daily_limit - daily_used if daily_limit > 0 else -1,
            'monthly_remaining': monthly_limit - monthly_used if monthly_limit > 0 else -1,
            'concurrent_available': concurrent_limit - current_concurrent
        }
    
    def _get_permission_level(self, user_context: UserContext, analysis_type: AnalysisType) -> PermissionLevel:
        """獲取權限級別"""
        tier = user_context.membership_tier
        
        if tier == 'DIAMOND':
            return PermissionLevel.UNLIMITED
        elif tier == 'GOLD':
            return PermissionLevel.PREMIUM
        elif tier == 'FREE':
            return PermissionLevel.LIMITED
        else:
            return PermissionLevel.DENIED
    
    def _get_enabled_features(self, user_context: UserContext, analysis_type: AnalysisType) -> List[str]:
        """獲取啟用的功能"""
        base_features = user_context.permissions.get('features', [])
        
        # 根據分析類型添加特定功能
        type_specific_features = {
            AnalysisType.BASIC_TECHNICAL: ['technical_charts', 'price_alerts'],
            AnalysisType.FUNDAMENTAL: ['financial_statements', 'ratio_analysis'],
            AnalysisType.NEWS_SENTIMENT: ['news_feed', 'sentiment_score'],
            AnalysisType.INSTITUTIONAL_FLOW: ['institutional_data', 'flow_analysis'],
            AnalysisType.TAIWAN_SPECIFIC: ['taiwan_market_data', 'sector_analysis'],
            AnalysisType.RISK_ASSESSMENT: ['risk_metrics', 'portfolio_analysis'],
            AnalysisType.COMPREHENSIVE: ['full_analysis', 'custom_reports']
        }
        
        specific_features = type_specific_features.get(analysis_type, [])
        
        return list(set(base_features + specific_features))
    
    async def record_analysis_usage(self, user_context: UserContext, analysis_type: AnalysisType) -> bool:
        """記錄分析使用量"""
        try:
            # 這裡應該更新資料庫或Redis中的使用量
            # 暫時只記錄日誌
            
            self.logger.info(f"用戶 {user_context.user_id} 使用了 {analysis_type.value} 分析")
            
            # 模擬更新快取中的使用量
            cache_key = f"user_context_{user_context.user_id}"
            if cache_key in self.permission_cache:
                cached_data = self.permission_cache[cache_key]
                quota_info = cached_data['data']['quota_info']
                quota_info['daily_used'] = quota_info.get('daily_used', 0) + 1
                quota_info['monthly_used'] = quota_info.get('monthly_used', 0) + 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"記錄使用量失敗: {str(e)}")
            return False
    
    async def start_concurrent_analysis(self, user_context: UserContext) -> bool:
        """開始並發分析 (增加並發計數)"""
        try:
            # 這裡應該更新Redis中的並發計數
            self.logger.debug(f"用戶 {user_context.user_id} 開始並發分析")
            
            # 模擬更新快取
            cache_key = f"user_context_{user_context.user_id}"
            if cache_key in self.permission_cache:
                cached_data = self.permission_cache[cache_key]
                quota_info = cached_data['data']['quota_info']
                quota_info['current_concurrent'] = quota_info.get('current_concurrent', 0) + 1
            
            return True
            
        except Exception as e:
            self.logger.error(f"開始並發分析失敗: {str(e)}")
            return False
    
    async def end_concurrent_analysis(self, user_context: UserContext) -> bool:
        """結束並發分析 (減少並發計數)"""
        try:
            # 這裡應該更新Redis中的並發計數
            self.logger.debug(f"用戶 {user_context.user_id} 結束並發分析")
            
            # 模擬更新快取
            cache_key = f"user_context_{user_context.user_id}"
            if cache_key in self.permission_cache:
                cached_data = self.permission_cache[cache_key]
                quota_info = cached_data['data']['quota_info']
                current = quota_info.get('current_concurrent', 0)
                quota_info['current_concurrent'] = max(0, current - 1)
            
            return True
            
        except Exception as e:
            self.logger.error(f"結束並發分析失敗: {str(e)}")
            return False
    
    async def get_user_analysis_stats(self, user_context: UserContext) -> Dict[str, Any]:
        """獲取用戶分析統計"""
        quota_info = user_context.quota_info
        
        return {
            'user_id': user_context.user_id,
            'membership_tier': user_context.membership_tier,
            'daily_usage': {
                'used': quota_info.get('daily_used', 0),
                'limit': quota_info.get('daily_limit', 0),
                'remaining': max(0, quota_info.get('daily_limit', 0) - quota_info.get('daily_used', 0)) if quota_info.get('daily_limit', 0) > 0 else -1
            },
            'monthly_usage': {
                'used': quota_info.get('monthly_used', 0),
                'limit': quota_info.get('monthly_limit', 0),
                'remaining': max(0, quota_info.get('monthly_limit', 0) - quota_info.get('monthly_used', 0)) if quota_info.get('monthly_limit', 0) > 0 else -1
            },
            'concurrent_usage': {
                'current': quota_info.get('current_concurrent', 0),
                'limit': quota_info.get('concurrent_limit', 1)
            },
            'available_analysis_types': user_context.permissions.get('allowed_analysis_types', []),
            'enabled_features': user_context.permissions.get('features', []),
            'restrictions': user_context.permissions.get('restrictions', [])
        }
    
    def clear_cache(self, user_id: str = None):
        """清理快取"""
        if user_id:
            cache_key = f"user_context_{user_id}"
            if cache_key in self.permission_cache:
                del self.permission_cache[cache_key]
        else:
            self.permission_cache.clear()
        
        self.logger.info(f"權限快取已清理 {'(用戶: ' + user_id + ')' if user_id else '(全部)'}")

# 便利函數
async def check_user_can_analyze(user_id: str, analysis_type: str) -> Dict[str, Any]:
    """快速檢查用戶是否可以進行分析"""
    bridge = MemberPermissionBridge()
    
    try:
        analysis_enum = AnalysisType(analysis_type)
    except ValueError:
        return {
            'allowed': False,
            'reason': 'invalid_analysis_type',
            'message': f'無效的分析類型: {analysis_type}'
        }
    
    user_context = await bridge.get_user_context(user_id)
    if not user_context:
        return {
            'allowed': False,
            'reason': 'user_not_found',
            'message': '用戶不存在'
        }
    
    return await bridge.check_analysis_permission(user_context, analysis_enum)

async def get_user_analysis_permissions(user_id: str) -> Dict[str, Any]:
    """獲取用戶分析權限概覽"""
    bridge = MemberPermissionBridge()
    
    user_context = await bridge.get_user_context(user_id)
    if not user_context:
        return {
            'error': 'user_not_found',
            'message': '用戶不存在'
        }
    
    return await bridge.get_user_analysis_stats(user_context)

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_permission_bridge():
        print("🔐 測試會員權限橋接器")
        
        bridge = MemberPermissionBridge()
        
        # 測試不同等級用戶
        test_users = ["free_user_1", "gold_user_1", "diamond_user_1"]
        
        for user_id in test_users:
            print(f"\n測試用戶: {user_id}")
            
            # 獲取用戶上下文
            user_context = await bridge.get_user_context(user_id)
            if user_context:
                print(f"  會員等級: {user_context.membership_tier}")
                
                # 測試分析權限
                permission_check = await bridge.check_analysis_permission(
                    user_context, 
                    AnalysisType.TAIWAN_SPECIFIC
                )
                print(f"  台股分析權限: {permission_check['allowed']}")
                
                # 獲取統計資訊
                stats = await bridge.get_user_analysis_stats(user_context)
                print(f"  每日配額: {stats['daily_usage']['limit']}")
                print(f"  可用分析: {len(stats['available_analysis_types'])}")
        
        print("\n✅ 測試完成")
    
    asyncio.run(test_permission_bridge())