"""配置管理服務"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigService:
    """統一配置管理服務"""
    
    def __init__(self):
        self._config_cache = {}
        self._config_history = []
        
    async def get_config(self, key: str, default: Any = None) -> Optional[Any]:
        """取得配置值
        
        Args:
            key: 配置鍵名
            default: 預設值
            
        Returns:
            配置值或預設值
        """
        try:
            # 首先檢查快取
            if key in self._config_cache:
                logger.debug(f"從快取取得配置: {key}")
                return self._config_cache[key]
                
            # 從資料庫取得配置
            config_value = await self._fetch_from_database(key)
            
            if config_value is not None:
                # 快取配置值
                self._config_cache[key] = config_value
                return config_value
                
            logger.warning(f"配置鍵 {key} 不存在，返回預設值: {default}")
            return default
            
        except Exception as e:
            logger.error(f"取得配置失敗 {key}: {e}")
            return default
    
    async def set_config(self, key: str, value: Any, user_id: str = "system") -> bool:
        """設定配置值
        
        Args:
            key: 配置鍵名
            value: 配置值
            user_id: 操作用戶ID
            
        Returns:
            設定是否成功
        """
        try:
            # 記錄變更歷史
            old_value = await self.get_config(key)
            
            # 儲存到資料庫
            success = await self._save_to_database(key, value)
            
            if success:
                # 更新快取
                self._config_cache[key] = value
                
                # 記錄變更歷史
                self._config_history.append({
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "user_id": user_id,
                    "timestamp": datetime.now()
                })
                
                logger.info(f"配置更新成功: {key} = {value} (by {user_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"設定配置失敗 {key}: {e}")
            return False
    
    async def list_configs(self, pattern: str = None) -> Dict[str, Any]:
        """列出所有配置
        
        Args:
            pattern: 過濾模式 (可選)
            
        Returns:
            配置字典
        """
        try:
            configs = await self._fetch_all_from_database()
            
            if pattern:
                # 簡單的模式匹配
                filtered_configs = {
                    k: v for k, v in configs.items() 
                    if pattern.lower() in k.lower()
                }
                return filtered_configs
                
            return configs
            
        except Exception as e:
            logger.error(f"列出配置失敗: {e}")
            return {}
    
    async def delete_config(self, key: str, user_id: str = "system") -> bool:
        """刪除配置
        
        Args:
            key: 配置鍵名
            user_id: 操作用戶ID
            
        Returns:
            刪除是否成功
        """
        try:
            # 記錄刪除前的值
            old_value = await self.get_config(key)
            
            # 從資料庫刪除
            success = await self._delete_from_database(key)
            
            if success:
                # 從快取移除
                self._config_cache.pop(key, None)
                
                # 記錄變更歷史
                self._config_history.append({
                    "key": key,
                    "old_value": old_value,
                    "new_value": None,
                    "action": "DELETE",
                    "user_id": user_id,
                    "timestamp": datetime.now()
                })
                
                logger.info(f"配置刪除成功: {key} (by {user_id})")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"刪除配置失敗 {key}: {e}")
            return False
    
    async def get_config_history(self, key: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """取得配置變更歷史
        
        Args:
            key: 特定配置鍵 (可選)
            limit: 限制筆數
            
        Returns:
            歷史記錄列表
        """
        try:
            history = self._config_history
            
            if key:
                history = [h for h in history if h["key"] == key]
                
            # 按時間倒序排列，取最近的記錄
            history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
            return history[:limit]
            
        except Exception as e:
            logger.error(f"取得配置歷史失敗: {e}")
            return []
    
    async def validate_config(self, key: str, value: Any) -> bool:
        """驗證配置值
        
        Args:
            key: 配置鍵名
            value: 配置值
            
        Returns:
            驗證是否通過
        """
        try:
            # 基本類型檢查
            if not isinstance(key, str) or not key.strip():
                return False
                
            # 特定配置的驗證規則
            validation_rules = {
                "max_analysis_requests": lambda v: isinstance(v, int) and v > 0,
                "api_timeout": lambda v: isinstance(v, (int, float)) and v > 0,
                "enable_debug": lambda v: isinstance(v, bool),
                "admin_email": lambda v: isinstance(v, str) and "@" in v,
            }
            
            if key in validation_rules:
                return validation_rules[key](value)
                
            # 預設驗證：允許基本類型
            return isinstance(value, (str, int, float, bool, list, dict)) or value is None
            
        except Exception as e:
            logger.error(f"配置驗證失敗 {key}: {e}")
            return False
    
    # 私有方法 - 資料庫操作 (模擬實作)
    async def _fetch_from_database(self, key: str) -> Optional[Any]:
        """從資料庫取得配置 (待實作)"""
        # TODO: 實作實際的資料庫查詢
        logger.debug(f"模擬從資料庫取得配置: {key}")
        return None
    
    async def _save_to_database(self, key: str, value: Any) -> bool:
        """儲存配置到資料庫 (待實作)"""
        # TODO: 實作實際的資料庫儲存
        logger.debug(f"模擬儲存配置到資料庫: {key} = {value}")
        return True
    
    async def _delete_from_database(self, key: str) -> bool:
        """從資料庫刪除配置 (待實作)"""
        # TODO: 實作實際的資料庫刪除
        logger.debug(f"模擬從資料庫刪除配置: {key}")
        return True
    
    async def _fetch_all_from_database(self) -> Dict[str, Any]:
        """從資料庫取得所有配置 (待實作)"""
        # TODO: 實作實際的資料庫查詢
        logger.debug("模擬從資料庫取得所有配置")
        return {}