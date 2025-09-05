"""用戶管理業務服務"""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

class UserRole(Enum):
    """用戶角色"""
    GUEST = "guest"
    FREE = "free"
    GOLD = "gold" 
    DIAMOND = "diamond"
    ADMIN = "admin"

class UserStatus(Enum):
    """用戶狀態"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BANNED = "banned"

class UserPermissions:
    """用戶權限類"""
    
    def __init__(self, role: UserRole):
        self.role = role
        self._permissions = self._get_permissions_by_role(role)
    
    def _get_permissions_by_role(self, role: UserRole) -> Dict[str, Any]:
        """根據角色取得權限配置"""
        permissions_map = {
            UserRole.GUEST: {
                "analysis_requests_per_day": 3,
                "analysis_history_days": 0,
                "advanced_features": False,
                "api_access": False,
                "export_data": False
            },
            UserRole.FREE: {
                "analysis_requests_per_day": 10,
                "analysis_history_days": 7,
                "advanced_features": False,
                "api_access": False,
                "export_data": False
            },
            UserRole.GOLD: {
                "analysis_requests_per_day": 50,
                "analysis_history_days": 30,
                "advanced_features": True,
                "api_access": True,
                "export_data": True
            },
            UserRole.DIAMOND: {
                "analysis_requests_per_day": 200,
                "analysis_history_days": 90,
                "advanced_features": True,
                "api_access": True,
                "export_data": True,
                "priority_support": True
            },
            UserRole.ADMIN: {
                "analysis_requests_per_day": -1,  # 無限制
                "analysis_history_days": -1,
                "advanced_features": True,
                "api_access": True,
                "export_data": True,
                "admin_access": True
            }
        }
        return permissions_map.get(role, permissions_map[UserRole.GUEST])
    
    def can_access(self, feature: str) -> bool:
        """檢查是否有權限存取特定功能"""
        return self._permissions.get(feature, False)
    
    def get_limit(self, resource: str) -> int:
        """取得資源使用限制"""
        return self._permissions.get(resource, 0)

class UserManagementService:
    """統一用戶管理服務"""
    
    def __init__(self):
        self._user_cache = {}
        self._usage_tracker = {}
        
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """取得用戶資料
        
        Args:
            user_id: 用戶ID
            
        Returns:
            用戶資料字典或 None
        """
        try:
            # 檢查快取
            if user_id in self._user_cache:
                logger.debug(f"從快取取得用戶資料: {user_id}")
                return self._user_cache[user_id]
            
            # 從資料庫取得用戶資料
            user_data = await self._fetch_user_from_database(user_id)
            
            if user_data:
                # 快取用戶資料
                self._user_cache[user_id] = user_data
                logger.info(f"成功取得用戶資料: {user_id}")
                return user_data
            
            logger.warning(f"用戶不存在: {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"取得用戶資料失敗 {user_id}: {e}")
            return None
    
    async def update_user_permissions(
        self, 
        user_id: str, 
        new_role: UserRole,
        admin_user_id: str = "system"
    ) -> bool:
        """更新用戶權限
        
        Args:
            user_id: 用戶ID
            new_role: 新角色
            admin_user_id: 管理員ID
            
        Returns:
            更新是否成功
        """
        try:
            # 取得現有用戶資料
            user_data = await self.get_user_profile(user_id)
            if not user_data:
                logger.error(f"用戶不存在，無法更新權限: {user_id}")
                return False
            
            old_role = user_data.get("role")
            
            # 更新角色
            user_data["role"] = new_role.value
            user_data["permissions"] = UserPermissions(new_role)._permissions
            user_data["updated_at"] = datetime.now()
            user_data["updated_by"] = admin_user_id
            
            # 儲存到資料庫
            success = await self._save_user_to_database(user_id, user_data)
            
            if success:
                # 更新快取
                self._user_cache[user_id] = user_data
                
                logger.info(f"用戶權限更新成功: {user_id} {old_role} -> {new_role.value} (by {admin_user_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新用戶權限失敗 {user_id}: {e}")
            return False
    
    async def get_user_analytics(self, user_id: str) -> Dict[str, Any]:
        """取得用戶分析數據
        
        Args:
            user_id: 用戶ID
            
        Returns:
            用戶分析數據
        """
        try:
            user_data = await self.get_user_profile(user_id)
            if not user_data:
                return {}
            
            # 取得使用統計
            usage_stats = await self._get_usage_statistics(user_id)
            
            # 取得訂閱狀態
            subscription_info = await self._get_subscription_info(user_id)
            
            analytics = {
                "user_info": {
                    "user_id": user_id,
                    "role": user_data.get("role"),
                    "status": user_data.get("status"),
                    "created_at": user_data.get("created_at"),
                    "last_login": user_data.get("last_login")
                },
                "usage_statistics": usage_stats,
                "subscription_info": subscription_info,
                "permissions": user_data.get("permissions", {}),
                "generated_at": datetime.now()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"取得用戶分析數據失敗 {user_id}: {e}")
            return {}
    
    async def check_usage_limit(self, user_id: str, resource: str) -> Dict[str, Any]:
        """檢查用戶使用限制
        
        Args:
            user_id: 用戶ID
            resource: 資源類型 (如 'analysis_requests_per_day')
            
        Returns:
            使用限制檢查結果
        """
        try:
            user_data = await self.get_user_profile(user_id)
            if not user_data:
                return {"allowed": False, "reason": "用戶不存在"}
            
            # 取得用戶權限
            permissions = user_data.get("permissions", {})
            limit = permissions.get(resource, 0)
            
            # 無限制
            if limit == -1:
                return {"allowed": True, "limit": -1, "used": 0, "remaining": -1}
            
            # 取得當前使用量
            current_usage = await self._get_current_usage(user_id, resource)
            
            # 檢查是否超過限制
            allowed = current_usage < limit
            remaining = max(0, limit - current_usage)
            
            return {
                "allowed": allowed,
                "limit": limit,
                "used": current_usage,
                "remaining": remaining,
                "reset_at": self._get_reset_time(resource)
            }
            
        except Exception as e:
            logger.error(f"檢查使用限制失敗 {user_id}: {e}")
            return {"allowed": False, "reason": "系統錯誤"}
    
    async def record_usage(self, user_id: str, resource: str, amount: int = 1) -> bool:
        """記錄資源使用
        
        Args:
            user_id: 用戶ID
            resource: 資源類型
            amount: 使用量
            
        Returns:
            記錄是否成功
        """
        try:
            # 取得當前使用記錄
            if user_id not in self._usage_tracker:
                self._usage_tracker[user_id] = {}
            
            if resource not in self._usage_tracker[user_id]:
                self._usage_tracker[user_id][resource] = {
                    "count": 0,
                    "last_reset": datetime.now().date(),
                    "history": []
                }
            
            # 檢查是否需要重置計數器
            today = datetime.now().date()
            usage_data = self._usage_tracker[user_id][resource]
            
            if usage_data["last_reset"] < today:
                usage_data["count"] = 0
                usage_data["last_reset"] = today
            
            # 記錄使用
            usage_data["count"] += amount
            usage_data["history"].append({
                "timestamp": datetime.now(),
                "amount": amount
            })
            
            # 保持歷史記錄不超過100筆
            if len(usage_data["history"]) > 100:
                usage_data["history"] = usage_data["history"][-100:]
            
            logger.debug(f"記錄用戶使用: {user_id} {resource} +{amount}")
            
            # 儲存到資料庫 (異步)
            await self._save_usage_to_database(user_id, resource, amount)
            
            return True
            
        except Exception as e:
            logger.error(f"記錄使用失敗 {user_id}: {e}")
            return False
    
    async def list_users(
        self, 
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出用戶
        
        Args:
            role: 過濾角色
            status: 過濾狀態
            limit: 限制筆數
            offset: 偏移量
            
        Returns:
            用戶列表
        """
        try:
            # 從資料庫取得用戶列表
            users = await self._fetch_users_from_database(role, status, limit, offset)
            
            logger.info(f"取得用戶列表: {len(users)} 筆")
            return users
            
        except Exception as e:
            logger.error(f"列出用戶失敗: {e}")
            return []
    
    # 私有方法 - 資料庫和外部服務操作 (模擬實作)
    async def _fetch_user_from_database(self, user_id: str) -> Optional[Dict[str, Any]]:
        """從資料庫取得用戶 (待實作)"""
        logger.debug(f"模擬從資料庫取得用戶: {user_id}")
        return None
    
    async def _save_user_to_database(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """儲存用戶到資料庫 (待實作)"""
        logger.debug(f"模擬儲存用戶到資料庫: {user_id}")
        return True
    
    async def _get_usage_statistics(self, user_id: str) -> Dict[str, Any]:
        """取得使用統計 (待實作)"""
        return {"analysis_requests_today": 0, "total_requests": 0}
    
    async def _get_subscription_info(self, user_id: str) -> Dict[str, Any]:
        """取得訂閱資訊 (待實作)"""
        return {"plan": "free", "expires_at": None}
    
    async def _get_current_usage(self, user_id: str, resource: str) -> int:
        """取得當前使用量"""
        if user_id not in self._usage_tracker:
            return 0
        
        usage_data = self._usage_tracker[user_id].get(resource)
        if not usage_data:
            return 0
        
        # 檢查是否需要重置
        today = datetime.now().date()
        if usage_data["last_reset"] < today:
            return 0
        
        return usage_data["count"]
    
    async def _save_usage_to_database(self, user_id: str, resource: str, amount: int) -> bool:
        """儲存使用記錄到資料庫 (待實作)"""
        logger.debug(f"模擬儲存使用記錄: {user_id} {resource} {amount}")
        return True
    
    async def _fetch_users_from_database(
        self, 
        role: Optional[UserRole], 
        status: Optional[UserStatus],
        limit: int, 
        offset: int
    ) -> List[Dict[str, Any]]:
        """從資料庫取得用戶列表 (待實作)"""
        logger.debug(f"模擬從資料庫取得用戶列表: role={role}, status={status}")
        return []
    
    def _get_reset_time(self, resource: str) -> datetime:
        """取得重置時間"""
        # 預設每日重置
        tomorrow = datetime.now() + timedelta(days=1)
        return tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)