#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
會員權益配置中心 - 戰略級業務敏捷性架構
回應GOOGLE技術委員會戰略批判：將業務規則從代碼中剝離
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TierType(Enum):
    FREE = "free"
    GOLD = "gold" 
    DIAMOND = "diamond"
    PLATINUM = "platinum"  # Future expansion

@dataclass
class TierPrivileges:
    """會員等級權益定義"""
    cache_ttl_seconds: int
    api_quota_daily: int
    api_quota_hourly: int
    export_formats: List[str]
    export_size_limit_mb: int
    ai_analysts_count: int
    realtime_alerts: bool
    priority_support: bool
    custom_dashboards: bool
    historical_data_months: int

@dataclass 
class PromotionRule:
    """促銷活動規則"""
    name: str
    description: str
    target_tier: TierType
    start_date: str
    end_date: str
    override_privileges: Dict[str, Any]
    active: bool = True

class MemberPrivilegeService:
    """會員權益配置服務 - 支援動態業務策略調整"""
    
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), 'member_privileges.json')
        self.config_data = self._load_config()
        self.tier_privileges = self._parse_tier_privileges()
        self.promotions = self._parse_promotions()
    
    def _load_config(self) -> Dict:
        """載入配置文件，支援環境變數覆蓋"""
        try:
            # 嘗試從文件載入
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ 會員權益配置已從文件載入: {self.config_file}")
                return config
            else:
                logger.warning(f"⚠️ 配置文件不存在，使用預設配置: {self.config_file}")
                return self._get_default_config()
                
        except Exception as e:
            logger.error(f"❌ 配置載入失敗，使用預設配置: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """預設會員權益配置 - 可由環境變數覆蓋"""
        return {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "tiers": {
                "FREE": {
                    "cache_ttl_seconds": int(os.getenv('FREE_CACHE_TTL', 3600)),  # 60分鐘
                    "api_quota_daily": int(os.getenv('FREE_API_QUOTA_DAILY', 100)),
                    "api_quota_hourly": int(os.getenv('FREE_API_QUOTA_HOURLY', 20)),
                    "export_formats": ["csv"],
                    "export_size_limit_mb": 10,
                    "ai_analysts_count": 1,
                    "realtime_alerts": False,
                    "priority_support": False,
                    "custom_dashboards": False,
                    "historical_data_months": 1
                },
                "GOLD": {
                    "cache_ttl_seconds": int(os.getenv('GOLD_CACHE_TTL', 1800)),  # 30分鐘
                    "api_quota_daily": int(os.getenv('GOLD_API_QUOTA_DAILY', 1000)),
                    "api_quota_hourly": int(os.getenv('GOLD_API_QUOTA_HOURLY', 200)),
                    "export_formats": ["csv", "excel"],
                    "export_size_limit_mb": 100,
                    "ai_analysts_count": 6,
                    "realtime_alerts": True,
                    "priority_support": True,
                    "custom_dashboards": True,
                    "historical_data_months": 12
                },
                "DIAMOND": {
                    "cache_ttl_seconds": int(os.getenv('DIAMOND_CACHE_TTL', 900)),   # 15分鐘
                    "api_quota_daily": int(os.getenv('DIAMOND_API_QUOTA_DAILY', -1)),  # 無限制
                    "api_quota_hourly": int(os.getenv('DIAMOND_API_QUOTA_HOURLY', -1)),
                    "export_formats": ["csv", "excel", "pdf"],
                    "export_size_limit_mb": -1,  # 無限制
                    "ai_analysts_count": 9,
                    "realtime_alerts": True,
                    "priority_support": True,
                    "custom_dashboards": True,
                    "historical_data_months": 60
                },
                "PLATINUM": {
                    "cache_ttl_seconds": int(os.getenv('PLATINUM_CACHE_TTL', 300)),   # 5分鐘
                    "api_quota_daily": -1,
                    "api_quota_hourly": -1,
                    "export_formats": ["csv", "excel", "pdf", "api"],
                    "export_size_limit_mb": -1,
                    "ai_analysts_count": 12,
                    "realtime_alerts": True,
                    "priority_support": True,
                    "custom_dashboards": True,
                    "historical_data_months": 120
                }
            },
            "promotions": [
                {
                    "name": "welcome_boost",
                    "description": "新用戶首週享受金級會員權益",
                    "target_tier": "FREE",
                    "start_date": "2025-09-24T00:00:00Z",
                    "end_date": "2025-12-31T23:59:59Z",
                    "override_privileges": {
                        "cache_ttl_seconds": 1800,
                        "ai_analysts_count": 3,
                        "api_quota_daily": 300
                    },
                    "active": True
                }
            ]
        }
    
    def _parse_tier_privileges(self) -> Dict[TierType, TierPrivileges]:
        """解析會員等級權益"""
        privileges = {}
        
        for tier_name, tier_data in self.config_data.get("tiers", {}).items():
            try:
                tier_type = TierType(tier_name.lower())
                privileges[tier_type] = TierPrivileges(**tier_data)
            except Exception as e:
                logger.error(f"解析會員權益失敗 {tier_name}: {e}")
                
        return privileges
    
    def _parse_promotions(self) -> List[PromotionRule]:
        """解析促銷活動規則"""
        promotions = []
        
        for promo_data in self.config_data.get("promotions", []):
            try:
                promotion = PromotionRule(**promo_data)
                promotions.append(promotion)
            except Exception as e:
                logger.error(f"解析促銷規則失敗: {e}")
                
        return promotions
    
    def get_user_privilege(self, privilege_name: str, user_tier: str, user_id: Optional[str] = None) -> Any:
        """
        獲取用戶權益值 - 核心戰略方法
        
        Args:
            privilege_name: 權益名稱 (如 'cache_ttl_seconds', 'api_quota_daily')
            user_tier: 用戶等級 ('free', 'gold', 'diamond')
            user_id: 用戶ID (用於個別促銷規則)
            
        Returns:
            權益值，已應用促銷規則
        """
        try:
            tier_type = TierType(user_tier.lower())
        except ValueError:
            logger.warning(f"未知的會員等級: {user_tier}，使用免費會員權益")
            tier_type = TierType.FREE
        
        # 獲取基礎權益
        base_privileges = self.tier_privileges.get(tier_type)
        if not base_privileges:
            logger.error(f"無法找到會員等級權益: {tier_type}")
            return None
        
        base_value = getattr(base_privileges, privilege_name, None)
        if base_value is None:
            logger.warning(f"權益 {privilege_name} 不存在於 {tier_type}")
            return None
        
        # 檢查是否有適用的促銷規則
        current_time = datetime.now(timezone.utc)
        
        for promotion in self.promotions:
            if not promotion.active:
                continue
                
            # 檢查是否適用於此用戶等級
            if promotion.target_tier.lower() != user_tier.lower():
                continue
            
            # 檢查促銷時間
            try:
                start_date = datetime.fromisoformat(promotion.start_date.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(promotion.end_date.replace('Z', '+00:00'))
                
                if start_date <= current_time <= end_date:
                    # 促銷規則生效，檢查是否有覆蓋此權益
                    override_value = promotion.override_privileges.get(privilege_name)
                    if override_value is not None:
                        logger.info(f"🎁 促銷規則 '{promotion.name}' 生效: {user_tier} {privilege_name} {base_value} → {override_value}")
                        return override_value
                        
            except Exception as e:
                logger.error(f"解析促銷時間失敗 {promotion.name}: {e}")
        
        # 沒有適用促銷規則，返回基礎值
        return base_value
    
    def get_cache_ttl(self, user_tier: str, user_id: Optional[str] = None) -> int:
        """獲取用戶緩存TTL - Redis服務專用"""
        return self.get_user_privilege('cache_ttl_seconds', user_tier, user_id) or 3600
    
    def get_api_quota(self, user_tier: str, quota_type: str = 'daily', user_id: Optional[str] = None) -> int:
        """獲取API配額限制"""
        privilege_name = f'api_quota_{quota_type}'
        return self.get_user_privilege(privilege_name, user_tier, user_id) or 100
    
    def get_ai_analysts_count(self, user_tier: str, user_id: Optional[str] = None) -> int:
        """獲取可用AI分析師數量"""
        return self.get_user_privilege('ai_analysts_count', user_tier, user_id) or 1
    
    def get_export_formats(self, user_tier: str, user_id: Optional[str] = None) -> List[str]:
        """獲取支援的匯出格式"""
        return self.get_user_privilege('export_formats', user_tier, user_id) or ["csv"]
    
    def get_tier_summary(self, user_tier: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """獲取用戶完整權益摘要"""
        try:
            tier_type = TierType(user_tier.lower())
        except ValueError:
            tier_type = TierType.FREE
        
        base_privileges = self.tier_privileges.get(tier_type)
        if not base_privileges:
            return {}
        
        # 構建完整權益，包含促銷覆蓋
        summary = {}
        for attr_name in base_privileges.__dataclass_fields__.keys():
            summary[attr_name] = self.get_user_privilege(attr_name, user_tier, user_id)
        
        # 添加元數據
        summary['tier'] = user_tier
        summary['config_version'] = self.config_data.get('version', '1.0')
        summary['active_promotions'] = [
            promo.name for promo in self.promotions 
            if promo.active and promo.target_tier.lower() == user_tier.lower()
        ]
        
        return summary
    
    def reload_config(self) -> bool:
        """重新載入配置 - 支援熱更新"""
        try:
            self.config_data = self._load_config()
            self.tier_privileges = self._parse_tier_privileges()
            self.promotions = self._parse_promotions()
            logger.info("✅ 會員權益配置已重新載入")
            return True
        except Exception as e:
            logger.error(f"❌ 配置重新載入失敗: {e}")
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """獲取配置服務健康狀態"""
        return {
            "status": "healthy",
            "config_version": self.config_data.get('version', 'unknown'),
            "last_updated": self.config_data.get('last_updated', 'unknown'),
            "tiers_loaded": len(self.tier_privileges),
            "active_promotions": len([p for p in self.promotions if p.active]),
            "total_promotions": len(self.promotions)
        }

# 全域配置服務實例
member_privilege_service = MemberPrivilegeService()