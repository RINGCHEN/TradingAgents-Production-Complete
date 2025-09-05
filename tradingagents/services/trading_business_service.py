"""統一交易業務服務
基於 .kiro 規格整合設計
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from enum import Enum

from .config_service import ConfigService
from .user_management_service import UserManagementService, UserRole
from .analyst_coordinator import AnalystCoordinator, AnalysisType

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服務狀態"""
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    DISABLED = "disabled"

class TradingBusinessService:
    """統一業務邏輯服務層
    
    基於 .kiro 規格整合：
    - tradingagents-finmind-migration (完成)
    - tradingagents-subscription-payment (80%完成)
    - tradingagents-ai-system (整合中)
    - tradingagents-data-integration (規劃中)
    """
    
    def __init__(self):
        # 初始化核心服務
        self.config_service = ConfigService()
        self.user_service = UserManagementService()
        self.analyst_coordinator = AnalystCoordinator()
        
        # 服務狀態追蹤
        self.service_status = {
            "config": ServiceStatus.ACTIVE,
            "user_management": ServiceStatus.ACTIVE,
            "analyst_coordination": ServiceStatus.ACTIVE,
            "finmind_integration": ServiceStatus.ACTIVE,  # 基於規格：完成
            "subscription_payment": ServiceStatus.ACTIVE,  # 基於規格：80%完成
            "data_integration": ServiceStatus.MAINTENANCE,  # 基於規格：進行中
            "ai_system": ServiceStatus.MAINTENANCE,  # 基於規格：等待
        }
        
        # 業務指標追蹤
        self.business_metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "error_count": 0,
            "average_response_time": 0.0,
            "last_updated": datetime.now()
        }
        
        logger.info("TradingBusinessService 初始化完成")
    
    async def perform_analysis(
        self, 
        user_id: str, 
        symbol: str,
        analysis_type: str = "comprehensive",
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """執行完整分析流程
        
        整合 .kiro 規格中的分析流程：
        1. 用戶權限驗證
        2. 使用量檢查
        3. 分析師協調執行
        4. 結果處理和記錄
        
        Args:
            user_id: 用戶ID
            symbol: 股票代碼
            analysis_type: 分析類型
            options: 額外選項
        
        Returns:
            分析結果
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"開始執行分析: {user_id} -> {symbol} ({analysis_type})")
            
            # 1. 驗證用戶權限和取得用戶資料
            user_data = await self.user_service.get_user_profile(user_id)
            if not user_data:
                return self._create_error_response(
                    "USER_NOT_FOUND",
                    "用戶不存在",
                    symbol,
                    analysis_type
                )
            
            # 2. 檢查用戶使用限制
            usage_check = await self.user_service.check_usage_limit(
                user_id, "analysis_requests_per_day"
            )
            
            if not usage_check["allowed"]:
                return self._create_error_response(
                    "USAGE_LIMIT_EXCEEDED",
                    f"已達每日分析次數上限 ({usage_check.get('limit', 0)})",
                    symbol,
                    analysis_type,
                    usage_info=usage_check
                )
            
            # 3. 驗證股票代碼和分析類型
            if not self._validate_symbol(symbol):
                return self._create_error_response(
                    "INVALID_SYMBOL",
                    f"無效的股票代碼: {symbol}",
                    symbol,
                    analysis_type
                )
            
            # 4. 將分析類型轉換為枚舉
            try:
                analysis_enum = AnalysisType(analysis_type.lower())
            except ValueError:
                return self._create_error_response(
                    "INVALID_ANALYSIS_TYPE",
                    f"不支援的分析類型: {analysis_type}",
                    symbol,
                    analysis_type
                )
            
            # 5. 執行分析師協調分析
            coordination_result = await self.analyst_coordinator.coordinate_analysis(
                symbol=symbol,
                analysis_type=analysis_enum,
                user_permissions=user_data.get("permissions", {})
            )
            
            if not coordination_result["success"]:
                return self._create_error_response(
                    "ANALYSIS_FAILED",
                    coordination_result.get("error", "分析執行失敗"),
                    symbol,
                    analysis_type
                )
            
            # 6. 記錄使用量
            await self.user_service.record_usage(
                user_id, "analysis_requests_per_day", 1
            )
            
            # 7. 處理和豐富分析結果
            enhanced_result = await self._enhance_analysis_result(
                coordination_result["result"],
                user_data,
                symbol,
                analysis_type,
                options
            )
            
            # 8. 記錄業務指標
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._update_business_metrics("success", execution_time)
            
            # 9. 建立最終回應
            final_result = {
                "success": True,
                "data": enhanced_result,
                "metadata": {
                    "user_id": user_id,
                    "symbol": symbol,
                    "analysis_type": analysis_type,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "usage_remaining": usage_check["remaining"] - 1,
                    "analysts_used": coordination_result["metadata"]["analysts_used"]
                }
            }
            
            logger.info(f"分析執行成功: {user_id} -> {symbol} ({execution_time:.2f}s)")
            return final_result
            
        except Exception as e:
            # 記錄錯誤指標
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._update_business_metrics("error", execution_time)
            
            logger.error(f"分析執行異常 {user_id} -> {symbol}: {e}")
            return self._create_error_response(
                "SYSTEM_ERROR",
                f"系統異常: {str(e)}",
                symbol,
                analysis_type
            )
    
    async def get_analysis_history(
        self, 
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        symbol_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """取得用戶分析歷史
        
        基於 .kiro 規格中的歷史管理需求
        """
        try:
            # 驗證用戶存在
            user_data = await self.user_service.get_user_profile(user_id)
            if not user_data:
                return {
                    "success": False,
                    "error": "用戶不存在"
                }
            
            # 檢查歷史查看權限
            permissions = user_data.get("permissions", {})
            history_days = permissions.get("analysis_history_days", 0)
            
            if history_days == 0:
                return {
                    "success": False,
                    "error": "無歷史查看權限"
                }
            
            # 模擬取得歷史記錄 (實際應從資料庫查詢)
            history_data = await self._fetch_analysis_history(
                user_id, limit, offset, symbol_filter, history_days
            )
            
            return {
                "success": True,
                "data": history_data,
                "metadata": {
                    "user_id": user_id,
                    "history_days_available": history_days,
                    "total_count": len(history_data),
                    "limit": limit,
                    "offset": offset
                }
            }
            
        except Exception as e:
            logger.error(f"取得分析歷史失敗 {user_id}: {e}")
            return {
                "success": False,
                "error": f"取得歷史失敗: {str(e)}"
            }
    
    async def get_user_dashboard_data(self, user_id: str) -> Dict[str, Any]:
        """取得用戶儀表板數據
        
        整合 .kiro 規格中的儀表板需求
        """
        try:
            # 取得用戶基本資料和分析數據
            user_data = await self.user_service.get_user_profile(user_id)
            if not user_data:
                return {"success": False, "error": "用戶不存在"}
            
            user_analytics = await self.user_service.get_user_analytics(user_id)
            
            # 取得今日使用狀況
            daily_usage = await self.user_service.check_usage_limit(
                user_id, "analysis_requests_per_day"
            )
            
            # 取得最近分析歷史 (最近5筆)
            recent_history = await self.get_analysis_history(
                user_id, limit=5, offset=0
            )
            
            # 組合儀表板數據
            dashboard_data = {
                "user_profile": {
                    "user_id": user_id,
                    "role": user_data.get("role"),
                    "status": user_data.get("status"),
                    "permissions": user_data.get("permissions", {})
                },
                "usage_summary": {
                    "daily_limit": daily_usage.get("limit", 0),
                    "daily_used": daily_usage.get("used", 0),
                    "daily_remaining": daily_usage.get("remaining", 0),
                    "reset_at": daily_usage.get("reset_at")
                },
                "analytics": user_analytics,
                "recent_analyses": recent_history.get("data", []),
                "system_status": self._get_system_status_summary(),
                "generated_at": datetime.now().isoformat()
            }
            
            return {
                "success": True,
                "data": dashboard_data
            }
            
        except Exception as e:
            logger.error(f"取得儀表板數據失敗 {user_id}: {e}")
            return {
                "success": False,
                "error": f"取得儀表板數據失敗: {str(e)}"
            }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """取得系統健康狀態
        
        基於 .kiro/hooks 中的系統監控需求
        """
        try:
            # 檢查各個服務狀態
            service_health = {}
            for service_name, status in self.service_status.items():
                service_health[service_name] = {
                    "status": status.value,
                    "last_check": datetime.now().isoformat()
                }
            
            # 取得業務指標
            health_data = {
                "overall_status": "healthy" if all(
                    status in [ServiceStatus.ACTIVE, ServiceStatus.MAINTENANCE] 
                    for status in self.service_status.values()
                ) else "unhealthy",
                "services": service_health,
                "business_metrics": self.business_metrics,
                "system_info": {
                    "version": "1.0.0-MVP",
                    "environment": "production",
                    "uptime": "運行中",
                    "last_updated": datetime.now().isoformat()
                }
            }
            
            return {
                "success": True,
                "data": health_data
            }
            
        except Exception as e:
            logger.error(f"取得系統健康狀態失敗: {e}")
            return {
                "success": False,
                "error": f"系統健康檢查失敗: {str(e)}"
            }
    
    # 私有輔助方法
    def _create_error_response(
        self, 
        error_code: str, 
        error_message: str,
        symbol: str,
        analysis_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """建立錯誤回應"""
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "symbol": symbol,
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat(),
                **kwargs
            }
        }
    
    def _validate_symbol(self, symbol: str) -> bool:
        """驗證股票代碼"""
        if not symbol or not isinstance(symbol, str):
            return False
        
        # 基本格式檢查
        symbol = symbol.strip().upper()
        
        # 台股代碼格式 (4位數字)
        if symbol.isdigit() and len(symbol) == 4:
            return True
        
        # 美股代碼格式 (1-5個字母)
        if symbol.isalpha() and 1 <= len(symbol) <= 5:
            return True
        
        return False
    
    async def _enhance_analysis_result(
        self,
        base_result: Dict[str, Any],
        user_data: Dict[str, Any],
        symbol: str,
        analysis_type: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """增強分析結果
        
        根據用戶等級和 .kiro 規格增加額外資訊
        """
        enhanced = base_result.copy()
        
        # 根據用戶角色提供不同層級的資訊
        user_role = UserRole(user_data.get("role", "guest"))
        
        if user_role in [UserRole.GOLD, UserRole.DIAMOND, UserRole.ADMIN]:
            # 高級用戶獲得更詳細的分析
            enhanced["detailed_metrics"] = {
                "volatility_analysis": "詳細波動率分析",
                "sector_comparison": "同業比較分析", 
                "risk_breakdown": "風險因子分解"
            }
        
        if user_role in [UserRole.DIAMOND, UserRole.ADMIN]:
            # 鑽石用戶獲得投資建議
            enhanced["investment_recommendations"] = {
                "position_sizing": "建議持倉比例",
                "entry_exit_strategy": "進出場策略",
                "portfolio_impact": "組合影響分析"
            }
        
        # 添加免責聲明和使用條款
        enhanced["disclaimer"] = {
            "risk_warning": "投資有風險，請謹慎決策",
            "data_source": "資料來源：FinMind API",
            "update_frequency": "數據更新頻率：每日"
        }
        
        return enhanced
    
    async def _fetch_analysis_history(
        self,
        user_id: str,
        limit: int,
        offset: int,
        symbol_filter: Optional[str],
        history_days: int
    ) -> List[Dict[str, Any]]:
        """取得分析歷史 (模擬實作)"""
        # TODO: 實作實際的資料庫查詢
        logger.debug(f"模擬取得分析歷史: {user_id}")
        return []
    
    async def _update_business_metrics(self, result_type: str, execution_time: float):
        """更新業務指標"""
        self.business_metrics["total_analyses"] += 1
        
        if result_type == "success":
            self.business_metrics["successful_analyses"] += 1
        elif result_type == "error":
            self.business_metrics["error_count"] += 1
        
        # 更新平均回應時間
        total_time = (self.business_metrics["average_response_time"] * 
                     (self.business_metrics["total_analyses"] - 1) + execution_time)
        self.business_metrics["average_response_time"] = (
            total_time / self.business_metrics["total_analyses"]
        )
        
        self.business_metrics["last_updated"] = datetime.now()
    
    def _get_system_status_summary(self) -> Dict[str, Any]:
        """取得系統狀態摘要"""
        active_services = sum(
            1 for status in self.service_status.values() 
            if status == ServiceStatus.ACTIVE
        )
        total_services = len(self.service_status)
        
        return {
            "active_services": active_services,
            "total_services": total_services,
            "health_percentage": (active_services / total_services) * 100,
            "last_check": datetime.now().isoformat()
        }