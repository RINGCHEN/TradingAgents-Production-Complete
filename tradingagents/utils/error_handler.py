#!/usr/bin/env python3
"""
統一錯誤處理系統 (Error Handler)
天工 (TianGong) - 系統級錯誤處理和異常管理

此模組提供統一的錯誤處理機制，包含錯誤分類、自動恢復、
監控報告和用戶友好的錯誤回應系統。

功能特色：
1. 多層次錯誤分類和處理
2. 智能錯誤恢復機制
3. 錯誤監控和報告
4. 用戶友好的錯誤訊息
5. 系統健康狀態追蹤
6. Taiwan市場相關錯誤處理
"""

import traceback
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from collections import defaultdict, deque
import json
import uuid

# 配置日誌
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """錯誤嚴重程度"""
    CRITICAL = "critical"      # 系統無法運行
    HIGH = "high"             # 主要功能受影響
    MEDIUM = "medium"         # 部分功能受影響
    LOW = "low"               # 輕微影響
    INFO = "info"             # 資訊性錯誤

class ErrorCategory(Enum):
    """錯誤類別"""
    SYSTEM = "system"                    # 系統錯誤
    DATABASE = "database"                # 數據庫錯誤
    NETWORK = "network"                  # 網路錯誤
    API = "api"                         # API錯誤
    DATA_PROCESSING = "data_processing"  # 數據處理錯誤
    AI_MODEL = "ai_model"               # AI模型錯誤
    AUTHENTICATION = "authentication"   # 認證錯誤
    AUTHORIZATION = "authorization"     # 授權錯誤
    VALIDATION = "validation"           # 驗證錯誤
    BUSINESS_LOGIC = "business_logic"   # 業務邏輯錯誤
    EXTERNAL_SERVICE = "external_service" # 外部服務錯誤
    TAIWAN_MARKET = "taiwan_market"     # Taiwan市場特定錯誤

class ErrorAction(Enum):
    """錯誤處理動作"""
    RETRY = "retry"                     # 重試
    FALLBACK = "fallback"               # 降級處理
    IGNORE = "ignore"                   # 忽略
    ESCALATE = "escalate"               # 升級處理
    TERMINATE = "terminate"             # 終止執行
    NOTIFY = "notify"                   # 通知管理員

@dataclass
class ErrorInfo:
    """錯誤資訊"""
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ErrorCategory = ErrorCategory.SYSTEM
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    action_taken: Optional[ErrorAction] = None

@dataclass
class RecoveryStrategy:
    """恢復策略"""
    name: str
    handler: Callable
    max_attempts: int = 3
    delay_seconds: float = 1.0
    exponential_backoff: bool = True
    applicable_categories: List[ErrorCategory] = field(default_factory=list)
    applicable_severities: List[ErrorSeverity] = field(default_factory=list)

class ErrorHandler:
    """統一錯誤處理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化錯誤處理器
        
        Args:
            config: 配置參數
        """
        self.config = config or {}
        
        # 錯誤記錄
        self.error_history: deque = deque(maxlen=1000)  # 保留最近1000個錯誤
        self.error_counts: Dict[ErrorCategory, int] = defaultdict(int)
        self.error_trends: Dict[str, List[datetime]] = defaultdict(list)
        
        # 恢復策略
        self.recovery_strategies: List[RecoveryStrategy] = []
        self._setup_default_strategies()
        
        # 監控配置
        self.monitoring_enabled = self.config.get('monitoring_enabled', True)
        self.notification_enabled = self.config.get('notification_enabled', True)
        self.auto_recovery_enabled = self.config.get('auto_recovery_enabled', True)
        
        # 錯誤閾值
        self.error_thresholds = {
            ErrorSeverity.CRITICAL: 1,     # 立即處理
            ErrorSeverity.HIGH: 5,         # 5分鐘內超過5次
            ErrorSeverity.MEDIUM: 20,      # 15分鐘內超過20次
            ErrorSeverity.LOW: 100         # 1小時內超過100次
        }
        
        logger.info("錯誤處理器初始化完成")
    
    def _setup_default_strategies(self):
        """設置默認恢復策略"""
        # 網路錯誤重試策略
        self.recovery_strategies.append(
            RecoveryStrategy(
                name="network_retry",
                handler=self._network_retry_handler,
                max_attempts=3,
                delay_seconds=2.0,
                exponential_backoff=True,
                applicable_categories=[ErrorCategory.NETWORK, ErrorCategory.API],
                applicable_severities=[ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
            )
        )
        
        # 數據庫連接重試策略
        self.recovery_strategies.append(
            RecoveryStrategy(
                name="database_retry",
                handler=self._database_retry_handler,
                max_attempts=5,
                delay_seconds=1.0,
                exponential_backoff=True,
                applicable_categories=[ErrorCategory.DATABASE],
                applicable_severities=[ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]
            )
        )
        
        # AI模型降級策略
        self.recovery_strategies.append(
            RecoveryStrategy(
                name="ai_model_fallback",
                handler=self._ai_model_fallback_handler,
                max_attempts=1,
                applicable_categories=[ErrorCategory.AI_MODEL],
                applicable_severities=[ErrorSeverity.MEDIUM, ErrorSeverity.HIGH]
            )
        )
        
        # Taiwan市場數據備用源策略
        self.recovery_strategies.append(
            RecoveryStrategy(
                name="taiwan_market_fallback",
                handler=self._taiwan_market_fallback_handler,
                max_attempts=2,
                delay_seconds=0.5,
                applicable_categories=[ErrorCategory.TAIWAN_MARKET],
                applicable_severities=[ErrorSeverity.LOW, ErrorSeverity.MEDIUM]
            )
        )
    
    async def handle_error(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auto_recover: bool = True
    ) -> ErrorInfo:
        """
        處理錯誤
        
        Args:
            exception: 異常對象
            context: 錯誤上下文
            user_id: 用戶ID
            session_id: 會話ID
            auto_recover: 是否自動恢復
            
        Returns:
            錯誤資訊對象
        """
        # 分析錯誤
        error_info = self._analyze_error(exception, context, user_id, session_id)
        
        # 記錄錯誤
        self._record_error(error_info)
        
        # 記錄日誌
        self._log_error(error_info)
        
        # 自動恢復嘗試
        if auto_recover and self.auto_recovery_enabled:
            await self._attempt_recovery(error_info)
        
        # 監控檢查
        if self.monitoring_enabled:
            await self._check_error_patterns(error_info)
        
        # 通知機制
        if self.notification_enabled:
            await self._notify_if_needed(error_info)
        
        return error_info
    
    def _analyze_error(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]],
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> ErrorInfo:
        """分析錯誤並分類"""
        error_info = ErrorInfo(
            message=str(exception),
            stack_trace=traceback.format_exc(),
            context=context or {},
            user_id=user_id,
            session_id=session_id
        )
        
        # 根據異常類型和訊息分類
        exception_type = type(exception).__name__
        error_message = str(exception).lower()
        
        # 分類錯誤
        if "connection" in error_message or "timeout" in error_message:
            error_info.category = ErrorCategory.NETWORK
            error_info.severity = ErrorSeverity.MEDIUM
        elif "database" in error_message or "sql" in error_message:
            error_info.category = ErrorCategory.DATABASE
            error_info.severity = ErrorSeverity.HIGH
        elif "unauthorized" in error_message or "authentication" in error_message:
            error_info.category = ErrorCategory.AUTHENTICATION
            error_info.severity = ErrorSeverity.MEDIUM
        elif "permission" in error_message or "forbidden" in error_message:
            error_info.category = ErrorCategory.AUTHORIZATION
            error_info.severity = ErrorSeverity.MEDIUM
        elif "validation" in error_message or "invalid" in error_message:
            error_info.category = ErrorCategory.VALIDATION
            error_info.severity = ErrorSeverity.LOW
        elif "api" in error_message or "request" in error_message:
            error_info.category = ErrorCategory.API
            error_info.severity = ErrorSeverity.MEDIUM
        elif "model" in error_message or "llm" in error_message:
            error_info.category = ErrorCategory.AI_MODEL
            error_info.severity = ErrorSeverity.MEDIUM
        elif "taiwan" in error_message or "twse" in error_message or "tpex" in error_message:
            error_info.category = ErrorCategory.TAIWAN_MARKET
            error_info.severity = ErrorSeverity.MEDIUM
        else:
            error_info.category = ErrorCategory.SYSTEM
            error_info.severity = ErrorSeverity.MEDIUM
        
        # 根據異常類型調整嚴重程度
        if exception_type in ['SystemExit', 'KeyboardInterrupt']:
            error_info.severity = ErrorSeverity.CRITICAL
        elif exception_type in ['MemoryError', 'RecursionError']:
            error_info.severity = ErrorSeverity.CRITICAL
        elif exception_type in ['ConnectionError', 'TimeoutError']:
            error_info.severity = ErrorSeverity.HIGH
        
        return error_info
    
    def _record_error(self, error_info: ErrorInfo):
        """記錄錯誤到歷史記錄"""
        self.error_history.append(error_info)
        self.error_counts[error_info.category] += 1
        
        # 記錄趨勢
        trend_key = f"{error_info.category.value}_{error_info.severity.value}"
        self.error_trends[trend_key].append(error_info.timestamp)
        
        # 清理過舊的趨勢數據 (保留24小時)
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.error_trends[trend_key] = [
            t for t in self.error_trends[trend_key] if t > cutoff_time
        ]
    
    def _log_error(self, error_info: ErrorInfo):
        """記錄錯誤到日誌"""
        log_data = {
            'error_id': error_info.error_id,
            'category': error_info.category.value,
            'severity': error_info.severity.value,
            'message': error_info.message,
            'context': error_info.context,
            'user_id': error_info.user_id,
            'session_id': error_info.session_id,
            'timestamp': error_info.timestamp.isoformat()
        }
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical Error: {json.dumps(log_data)}")
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(f"High Severity Error: {json.dumps(log_data)}")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium Severity Error: {json.dumps(log_data)}")
        else:
            logger.info(f"Low Severity Error: {json.dumps(log_data)}")
        
        # 詳細堆疊追蹤
        if error_info.stack_trace and error_info.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"Stack Trace for {error_info.error_id}:\n{error_info.stack_trace}")
    
    async def _attempt_recovery(self, error_info: ErrorInfo):
        """嘗試自動恢復"""
        applicable_strategies = [
            strategy for strategy in self.recovery_strategies
            if (not strategy.applicable_categories or error_info.category in strategy.applicable_categories)
            and (not strategy.applicable_severities or error_info.severity in strategy.applicable_severities)
        ]
        
        for strategy in applicable_strategies:
            try:
                error_info.recovery_attempted = True
                
                for attempt in range(strategy.max_attempts):
                    try:
                        # 執行恢復策略
                        success = await strategy.handler(error_info, attempt)
                        
                        if success:
                            error_info.recovery_successful = True
                            error_info.action_taken = ErrorAction.RETRY
                            logger.info(f"恢復成功: {strategy.name} for {error_info.error_id}")
                            return
                        
                        # 等待後重試
                        if attempt < strategy.max_attempts - 1:
                            delay = strategy.delay_seconds
                            if strategy.exponential_backoff:
                                delay *= (2 ** attempt)
                            await asyncio.sleep(delay)
                            
                    except Exception as e:
                        logger.warning(f"恢復策略 {strategy.name} 失敗: {str(e)}")
                        
            except Exception as e:
                logger.error(f"恢復策略執行失敗: {strategy.name}, 錯誤: {str(e)}")
    
    async def _check_error_patterns(self, error_info: ErrorInfo):
        """檢查錯誤模式和趨勢"""
        trend_key = f"{error_info.category.value}_{error_info.severity.value}"
        recent_errors = self.error_trends[trend_key]
        
        # 檢查錯誤頻率
        threshold = self.error_thresholds.get(error_info.severity, 50)
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            # 嚴重錯誤立即檢查
            pass
        elif error_info.severity == ErrorSeverity.HIGH:
            # 檢查5分鐘內的錯誤
            cutoff = datetime.now() - timedelta(minutes=5)
            recent_count = len([t for t in recent_errors if t > cutoff])
            if recent_count >= threshold:
                await self._handle_error_spike(error_info, recent_count, "5分鐘")
        elif error_info.severity == ErrorSeverity.MEDIUM:
            # 檢查15分鐘內的錯誤
            cutoff = datetime.now() - timedelta(minutes=15)
            recent_count = len([t for t in recent_errors if t > cutoff])
            if recent_count >= threshold:
                await self._handle_error_spike(error_info, recent_count, "15分鐘")
        else:
            # 檢查1小時內的錯誤
            cutoff = datetime.now() - timedelta(hours=1)
            recent_count = len([t for t in recent_errors if t > cutoff])
            if recent_count >= threshold:
                await self._handle_error_spike(error_info, recent_count, "1小時")
    
    async def _handle_error_spike(self, error_info: ErrorInfo, count: int, timeframe: str):
        """處理錯誤激增"""
        logger.warning(f"偵測到錯誤激增: {count}次 {error_info.category.value} 錯誤在 {timeframe} 內")
        
        # 可以在這裡實施緊急措施，如：
        # - 啟用降級模式
        # - 增加緩存時間
        # - 限制並發請求
        # - 通知運維團隊
        
        # 記錄錯誤激增事件
        spike_info = {
            'category': error_info.category.value,
            'severity': error_info.severity.value,
            'count': count,
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.warning(f"錯誤激增事件: {json.dumps(spike_info)}")
    
    async def _notify_if_needed(self, error_info: ErrorInfo):
        """根據需要發送通知"""
        # 嚴重錯誤立即通知
        if error_info.severity == ErrorSeverity.CRITICAL:
            await self._send_notification(error_info, urgent=True)
        # 高嚴重程度錯誤在恢復失敗時通知
        elif error_info.severity == ErrorSeverity.HIGH and not error_info.recovery_successful:
            await self._send_notification(error_info, urgent=False)
    
    async def _send_notification(self, error_info: ErrorInfo, urgent: bool = False):
        """發送通知"""
        # 這裡可以實施各種通知機制：
        # - 郵件通知
        # - Slack/Teams通知
        # - SMS通知
        # - 監控系統警報
        
        notification_data = {
            'error_id': error_info.error_id,
            'category': error_info.category.value,
            'severity': error_info.severity.value,
            'message': error_info.message,
            'urgent': urgent,
            'timestamp': error_info.timestamp.isoformat()
        }
        
        if urgent:
            logger.critical(f"緊急通知: {json.dumps(notification_data)}")
        else:
            logger.warning(f"錯誤通知: {json.dumps(notification_data)}")
    
    # ==================== 恢復策略處理器 ====================
    
    async def _network_retry_handler(self, error_info: ErrorInfo, attempt: int) -> bool:
        """網路重試處理器"""
        # 實施網路重試邏輯
        logger.info(f"執行網路重試 (嘗試 {attempt + 1})")
        
        # 這裡可以實施具體的網路重試邏輯
        # 例如：重新建立連接、檢查網路狀態等
        
        # 模擬重試成功 (實際實現應該有真實的重試邏輯)
        return attempt < 2  # 前兩次嘗試模擬失敗，第三次成功
    
    async def _database_retry_handler(self, error_info: ErrorInfo, attempt: int) -> bool:
        """數據庫重試處理器"""
        # 實施數據庫重試邏輯
        logger.info(f"執行數據庫重試 (嘗試 {attempt + 1})")
        
        # 這裡可以實施具體的數據庫重試邏輯
        # 例如：重新建立連接、檢查連接池等
        
        return attempt < 3  # 模擬重試邏輯
    
    async def _ai_model_fallback_handler(self, error_info: ErrorInfo, attempt: int) -> bool:
        """AI模型降級處理器"""
        # 實施AI模型降級邏輯
        logger.info(f"執行AI模型降級處理")
        
        # 這裡可以實施具體的降級邏輯
        # 例如：切換到備用模型、使用緩存結果等
        
        error_info.action_taken = ErrorAction.FALLBACK
        return True
    
    async def _taiwan_market_fallback_handler(self, error_info: ErrorInfo, attempt: int) -> bool:
        """Taiwan市場數據備用源處理器"""
        # 實施Taiwan市場數據備用源邏輯
        logger.info(f"執行Taiwan市場數據備用源處理")
        
        # 這裡可以實施具體的備用數據源邏輯
        # 例如：切換到其他數據提供商、使用歷史數據等
        
        error_info.action_taken = ErrorAction.FALLBACK
        return True
    
    # ==================== 查詢和統計 ====================
    
    def get_error_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """獲取錯誤統計"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_errors = [e for e in self.error_history if e.timestamp > cutoff_time]
        
        # 按類別統計
        category_stats = defaultdict(int)
        severity_stats = defaultdict(int)
        recovery_stats = {'attempted': 0, 'successful': 0}
        
        for error in recent_errors:
            category_stats[error.category.value] += 1
            severity_stats[error.severity.value] += 1
            
            if error.recovery_attempted:
                recovery_stats['attempted'] += 1
                if error.recovery_successful:
                    recovery_stats['successful'] += 1
        
        return {
            'timeframe_hours': hours,
            'total_errors': len(recent_errors),
            'category_breakdown': dict(category_stats),
            'severity_breakdown': dict(severity_stats),
            'recovery_statistics': recovery_stats,
            'recovery_success_rate': (
                recovery_stats['successful'] / recovery_stats['attempted']
                if recovery_stats['attempted'] > 0 else 0
            ),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """獲取系統健康狀態"""
        recent_errors = [
            e for e in self.error_history 
            if e.timestamp > datetime.now() - timedelta(hours=1)
        ]
        
        critical_errors = [e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL]
        high_errors = [e for e in recent_errors if e.severity == ErrorSeverity.HIGH]
        
        # 計算健康分數 (0-100)
        health_score = 100
        health_score -= len(critical_errors) * 25  # 每個嚴重錯誤扣25分
        health_score -= len(high_errors) * 10      # 每個高嚴重程度錯誤扣10分
        health_score -= max(0, len(recent_errors) - 10) * 2  # 超過10個錯誤每個扣2分
        health_score = max(0, health_score)
        
        if health_score >= 90:
            status = "healthy"
        elif health_score >= 70:
            status = "warning"
        elif health_score >= 50:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            'status': status,
            'health_score': health_score,
            'recent_errors_1h': len(recent_errors),
            'critical_errors_1h': len(critical_errors),
            'high_errors_1h': len(high_errors),
            'timestamp': datetime.now().isoformat()
        }

# 便利函數
_global_error_handler: Optional[ErrorHandler] = None

def get_error_handler(config: Optional[Dict[str, Any]] = None) -> ErrorHandler:
    """獲取全局錯誤處理器實例"""
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(config)
    
    return _global_error_handler

async def handle_error(
    exception: Exception,
    context: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    auto_recover: bool = True
) -> ErrorInfo:
    """便利函數：處理錯誤"""
    handler = get_error_handler()
    return await handler.handle_error(exception, context, user_id, session_id, auto_recover)

def get_user_friendly_message(error_info: ErrorInfo) -> str:
    """獲取用戶友好的錯誤訊息"""
    if error_info.category == ErrorCategory.NETWORK:
        return "網路連接異常，請檢查您的網路連接後重試"
    elif error_info.category == ErrorCategory.DATABASE:
        return "數據服務暫時不可用，請稍後再試"
    elif error_info.category == ErrorCategory.AUTHENTICATION:
        return "身份驗證失敗，請重新登入"
    elif error_info.category == ErrorCategory.AUTHORIZATION:
        return "您沒有權限執行此操作"
    elif error_info.category == ErrorCategory.VALIDATION:
        return "輸入的資料格式不正確，請檢查後重新輸入"
    elif error_info.category == ErrorCategory.AI_MODEL:
        return "AI分析服務暫時不可用，正在嘗試使用備用服務"
    elif error_info.category == ErrorCategory.TAIWAN_MARKET:
        return "Taiwan股市數據服務暫時不可用，正在使用備用數據源"
    else:
        return "系統暫時發生問題，我們正在處理中，請稍後再試"

if __name__ == "__main__":
    # 測試腳本
    async def test_error_handler():
        print("測試錯誤處理器...")
        
        # 創建錯誤處理器
        handler = ErrorHandler()
        
        # 測試不同類型的錯誤
        test_errors = [
            ConnectionError("Database connection failed"),
            ValueError("Invalid stock symbol"),
            TimeoutError("API request timeout"),
            Exception("Unknown error")
        ]
        
        for i, error in enumerate(test_errors):
            print(f"\n處理錯誤 {i+1}: {error}")
            
            error_info = await handler.handle_error(
                error,
                context={'test': True, 'error_index': i},
                user_id=f"test_user_{i}",
                session_id=f"test_session_{i}"
            )
            
            print(f"錯誤ID: {error_info.error_id}")
            print(f"類別: {error_info.category.value}")
            print(f"嚴重程度: {error_info.severity.value}")
            print(f"恢復嘗試: {error_info.recovery_attempted}")
            print(f"恢復成功: {error_info.recovery_successful}")
            print(f"用戶友好訊息: {get_user_friendly_message(error_info)}")
        
        # 獲取統計資訊
        stats = handler.get_error_statistics()
        print(f"\n錯誤統計: {stats}")
        
        health = handler.get_system_health()
        print(f"系統健康: {health}")
        
        print("錯誤處理器測試完成")
    
    asyncio.run(test_error_handler())