#!/usr/bin/env python3
"""
中間件系統 (Middleware)
天工 (TianGong) - 統一的請求處理和監控中間件

此模組提供各種中間件組件，包含請求日誌、錯誤處理、
性能監控、安全檢查和使用量追蹤等功能。

功能特色：
1. 自動請求日誌記錄
2. 請求性能監控
3. 安全檢查和過濾
4. 使用量統計追蹤
5. 錯誤追蹤和恢復
6. Taiwan市場專用檢查
"""

import time
import json
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import asyncio

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging_config import get_api_logger, get_security_logger, get_system_logger
from .error_handler import handle_error, get_user_friendly_message

# 配置日誌
api_logger = get_api_logger("middleware")
security_logger = get_security_logger("middleware")
system_logger = get_system_logger("middleware")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """請求日誌中間件"""
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.log_body = self.config.get('log_body', False)
        self.log_headers = self.config.get('log_headers', True)
        self.sensitive_headers = {
            'authorization', 'cookie', 'x-api-key', 'x-auth-token'
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        start_time = time.time()
        request_id = str(uuid.uuid4())
        
        # 添加請求ID到請求狀態
        request.state.request_id = request_id
        
        # 準備日誌資料
        log_data = {
            'request_id': request_id,
            'method': request.method,
            'url': str(request.url),
            'path': request.url.path,
            'query_params': dict(request.query_params),
            'client_host': request.client.host if request.client else None,
            'user_agent': request.headers.get('user-agent', ''),
            'request_time': datetime.now().isoformat()
        }
        
        # 添加請求頭 (過濾敏感資訊)
        if self.log_headers:
            headers = {}
            for key, value in request.headers.items():
                if key.lower() in self.sensitive_headers:
                    headers[key] = "***MASKED***"
                else:
                    headers[key] = value
            log_data['headers'] = headers
        
        # 記錄請求開始
        api_logger.info("API請求開始", extra=log_data)
        
        try:
            # 處理請求
            response = await call_next(request)
            
            # 計算處理時間
            process_time = time.time() - start_time
            
            # 更新日誌資料
            log_data.update({
                'status_code': response.status_code,
                'process_time': process_time,
                'response_time': datetime.now().isoformat()
            })
            
            # 添加處理時間到響應頭
            response.headers["X-Process-Time"] = str(process_time)
            response.headers["X-Request-ID"] = request_id
            
            # 記錄請求完成
            if response.status_code >= 400:
                api_logger.warning("API請求完成 (錯誤)", extra=log_data)
            else:
                api_logger.info("API請求完成", extra=log_data)
            
            return response
            
        except Exception as e:
            # 處理異常
            process_time = time.time() - start_time
            
            log_data.update({
                'status_code': 500,
                'process_time': process_time,
                'error': str(e),
                'response_time': datetime.now().isoformat()
            })
            
            api_logger.error("API請求異常", extra=log_data)
            
            # 重新拋出異常，讓全局異常處理器處理
            raise

class SecurityMiddleware(BaseHTTPMiddleware):
    """安全檢查中間件"""
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.rate_limit_enabled = self.config.get('rate_limit_enabled', True)
        self.max_requests_per_minute = self.config.get('max_requests_per_minute', 60)
        self.blocked_ips = set(self.config.get('blocked_ips', []))
        self.request_counts: Dict[str, list] = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        client_ip = request.client.host if request.client else "unknown"
        
        # 檢查IP封鎖
        if client_ip in self.blocked_ips:
            security_logger.warning("已封鎖IP嘗試訪問", extra={
                'client_ip': client_ip,
                'url': str(request.url),
                'user_agent': request.headers.get('user-agent', ''),
                'security_event': 'blocked_ip_access'
            })
            
            return JSONResponse(
                status_code=403,
                content={"detail": "Access denied"}
            )
        
        # 速率限制檢查
        if self.rate_limit_enabled:
            current_time = time.time()
            
            # 初始化或清理過期記錄
            if client_ip not in self.request_counts:
                self.request_counts[client_ip] = []
            
            # 清理一分鐘前的記錄
            self.request_counts[client_ip] = [
                t for t in self.request_counts[client_ip] 
                if current_time - t < 60
            ]
            
            # 檢查是否超過限制
            if len(self.request_counts[client_ip]) >= self.max_requests_per_minute:
                security_logger.warning("速率限制觸發", extra={
                    'client_ip': client_ip,
                    'request_count': len(self.request_counts[client_ip]),
                    'limit': self.max_requests_per_minute,
                    'url': str(request.url),
                    'security_event': 'rate_limit_exceeded'
                })
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later.",
                        "retry_after": 60
                    }
                )
            
            # 記錄當前請求
            self.request_counts[client_ip].append(current_time)
        
        # 檢查可疑行為
        await self._check_suspicious_activity(request)
        
        # 繼續處理請求
        return await call_next(request)
    
    async def _check_suspicious_activity(self, request: Request):
        """檢查可疑活動"""
        client_ip = request.client.host if request.client else "unknown"
        url = str(request.url)
        user_agent = request.headers.get('user-agent', '')
        
        # 檢查常見攻擊模式
        suspicious_patterns = [
            'admin', 'wp-admin', 'phpmyadmin', '.env', 'config',
            'sql', 'script', 'eval', 'exec'
        ]
        
        for pattern in suspicious_patterns:
            if pattern in url.lower():
                security_logger.warning("偵測到可疑請求模式", extra={
                    'client_ip': client_ip,
                    'url': url,
                    'pattern': pattern,
                    'user_agent': user_agent,
                    'security_event': 'suspicious_pattern'
                })
                break
        
        # 檢查異常User-Agent
        if not user_agent or len(user_agent) < 10:
            security_logger.info("異常User-Agent", extra={
                'client_ip': client_ip,
                'url': url,
                'user_agent': user_agent,
                'security_event': 'unusual_user_agent'
            })

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能監控中間件"""
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.slow_request_threshold = self.config.get('slow_request_threshold', 2.0)  # 2秒
        self.memory_check_enabled = self.config.get('memory_check_enabled', True)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        start_time = time.time()
        start_memory = self._get_memory_usage() if self.memory_check_enabled else 0
        
        try:
            response = await call_next(request)
            
            # 計算性能指標
            end_time = time.time()
            process_time = end_time - start_time
            end_memory = self._get_memory_usage() if self.memory_check_enabled else 0
            
            # 記錄性能資料
            performance_data = {
                'url': str(request.url),
                'method': request.method,
                'process_time': process_time,
                'status_code': response.status_code,
                'memory_start': start_memory,
                'memory_end': end_memory,
                'memory_delta': end_memory - start_memory,
                'performance_metric': True
            }
            
            # 檢查慢請求
            if process_time > self.slow_request_threshold:
                system_logger.warning("偵測到慢請求", extra=performance_data)
            else:
                system_logger.debug("請求性能", extra=performance_data)
            
            return response
            
        except Exception as e:
            # 記錄異常性能資料
            end_time = time.time()
            process_time = end_time - start_time
            
            system_logger.error("請求處理異常", extra={
                'url': str(request.url),
                'method': request.method,
                'process_time': process_time,
                'error': str(e),
                'performance_metric': True
            })
            
            raise
    
    def _get_memory_usage(self) -> float:
        """獲取當前記憶體使用量 (MB)"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # 轉換為MB
        except ImportError:
            return 0.0

class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """使用量追蹤中間件"""
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.usage_stats: Dict[str, Dict[str, Any]] = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        # 從請求中提取用戶資訊
        user_id = None
        try:
            # 簡化的用戶提取邏輯
            auth_header = request.headers.get('authorization', '')
            if auth_header:
                # 在實際實現中，這裡應該解析JWT token
                user_id = f"user_{auth_header[-8:]}"  # 簡化實現
        except:
            pass
        
        # 記錄使用量
        if user_id:
            self._record_usage(user_id, request.url.path, request.method)
        
        # 繼續處理請求
        response = await call_next(request)
        
        return response
    
    def _record_usage(self, user_id: str, endpoint: str, method: str):
        """記錄用戶使用量"""
        current_time = datetime.now()
        
        if user_id not in self.usage_stats:
            self.usage_stats[user_id] = {
                'total_requests': 0,
                'endpoints': {},
                'last_access': current_time.isoformat(),
                'daily_count': 0
            }
        
        # 更新統計
        self.usage_stats[user_id]['total_requests'] += 1
        self.usage_stats[user_id]['last_access'] = current_time.isoformat()
        
        endpoint_key = f"{method} {endpoint}"
        if endpoint_key not in self.usage_stats[user_id]['endpoints']:
            self.usage_stats[user_id]['endpoints'][endpoint_key] = 0
        self.usage_stats[user_id]['endpoints'][endpoint_key] += 1
        
        # 記錄使用量日誌
        api_logger.debug("用戶使用量記錄", extra={
            'user_id': user_id,
            'endpoint': endpoint,
            'method': method,
            'total_requests': self.usage_stats[user_id]['total_requests'],
            'usage_tracking': True
        })
    
    def get_usage_stats(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶使用量統計"""
        return self.usage_stats.get(user_id)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能監控中間件"""
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.slow_request_threshold = self.config.get('slow_request_threshold', 2.0)
        self.memory_check_enabled = self.config.get('memory_check_enabled', True)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        start_time = time.time()
        
        # 記錄內存使用（如果啟用）
        if self.memory_check_enabled:
            import psutil
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            response = await call_next(request)
            
            # 計算處理時間
            process_time = time.time() - start_time
            
            # 檢查慢請求
            if process_time > self.slow_request_threshold:
                system_logger.warning("慢請求檢測", extra={
                    'url': str(request.url),
                    'method': request.method,
                    'process_time': process_time,
                    'threshold': self.slow_request_threshold,
                    'performance_issue': True
                })
            
            # 記錄內存變化
            if self.memory_check_enabled:
                memory_after = process.memory_info().rss / 1024 / 1024  # MB
                memory_diff = memory_after - memory_before
                
                if memory_diff > 50:  # 如果內存增加超過50MB
                    system_logger.warning("內存使用異常", extra={
                        'url': str(request.url),
                        'method': request.method,
                        'memory_before': memory_before,
                        'memory_after': memory_after,
                        'memory_diff': memory_diff,
                        'performance_issue': True
                    })
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            system_logger.error("請求處理異常", extra={
                'url': str(request.url),
                'method': request.method,
                'process_time': process_time,
                'error': str(e),
                'performance_issue': True
            })
            raise

class ErrorRecoveryMiddleware(BaseHTTPMiddleware):
    """錯誤恢復中間件"""
    
    def __init__(self, app: ASGIApp, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.auto_recovery_enabled = self.config.get('auto_recovery_enabled', True)
        self.circuit_breaker_enabled = self.config.get('circuit_breaker_enabled', True)
        self.failure_counts: Dict[str, int] = {}
        self.circuit_breaker_threshold = self.config.get('circuit_breaker_threshold', 5)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """處理請求"""
        endpoint = f"{request.method} {request.url.path}"
        
        # 檢查熔斷器狀態
        if self.circuit_breaker_enabled and self._is_circuit_open(endpoint):
            system_logger.warning("熔斷器開啟，拒絕請求", extra={
                'endpoint': endpoint,
                'failure_count': self.failure_counts.get(endpoint, 0),
                'circuit_breaker': True
            })
            
            return JSONResponse(
                status_code=503,
                content={
                    "detail": "Service temporarily unavailable",
                    "retry_after": 30
                }
            )
        
        try:
            response = await call_next(request)
            
            # 請求成功，重置失敗計數
            if endpoint in self.failure_counts:
                self.failure_counts[endpoint] = 0
            
            return response
            
        except Exception as e:
            # 記錄失敗
            self.failure_counts[endpoint] = self.failure_counts.get(endpoint, 0) + 1
            
            # 處理錯誤
            error_info = await handle_error(e, {
                'endpoint': endpoint,
                'middleware': 'error_recovery'
            })
            
            system_logger.error("請求處理失敗", extra={
                'endpoint': endpoint,
                'error_id': error_info.error_id,
                'failure_count': self.failure_counts[endpoint],
                'circuit_breaker_threshold': self.circuit_breaker_threshold
            })
            
            # 如果啟用自動恢復，嘗試降級處理
            if self.auto_recovery_enabled:
                fallback_response = await self._get_fallback_response(request, error_info)
                if fallback_response:
                    return fallback_response
            
            # 重新拋出異常
            raise
    
    def _is_circuit_open(self, endpoint: str) -> bool:
        """檢查熔斷器是否開啟"""
        return self.failure_counts.get(endpoint, 0) >= self.circuit_breaker_threshold
    
    async def _get_fallback_response(self, request: Request, error_info) -> Optional[JSONResponse]:
        """獲取降級響應"""
        # 簡化的降級邏輯
        if request.url.path.startswith('/analysis/'):
            return JSONResponse(
                status_code=202,
                content={
                    "message": "服務暫時不可用，請稍後再試",
                    "fallback": True,
                    "error_id": error_info.error_id
                }
            )
        
        return None

# 便利函數
def setup_middleware(app, config: Optional[Dict[str, Any]] = None):
    """設置所有中間件"""
    config = config or {}
    
    # 按順序添加中間件
    if config.get('enable_error_recovery', True):
        app.add_middleware(ErrorRecoveryMiddleware, config=config.get('error_recovery', {}))
    
    if config.get('enable_usage_tracking', True):
        app.add_middleware(UsageTrackingMiddleware, config=config.get('usage_tracking', {}))
    
    if config.get('enable_performance_monitoring', True):
        app.add_middleware(PerformanceMiddleware, config=config.get('performance', {}))
    
    if config.get('enable_security', True):
        app.add_middleware(SecurityMiddleware, config=config.get('security', {}))
    
    if config.get('enable_request_logging', True):
        app.add_middleware(RequestLoggingMiddleware, config=config.get('logging', {}))
    
    system_logger.info("中間件設置完成", extra={
        'enabled_middleware': [
            name for name, enabled in [
                ('error_recovery', config.get('enable_error_recovery', True)),
                ('usage_tracking', config.get('enable_usage_tracking', True)),
                ('performance_monitoring', config.get('enable_performance_monitoring', True)),
                ('security', config.get('enable_security', True)),
                ('request_logging', config.get('enable_request_logging', True))
            ] if enabled
        ]
    })
    
    app.add_middleware(ErrorRecoveryMiddleware, config=config.get('error_recovery', {}))
    
    if config.get('enable_usage_tracking', True):
        app.add_middleware(UsageTrackingMiddleware, config=config.get('usage_tracking', {}))
    
    if config.get('enable_performance_monitoring', True):
        app.add_middleware(PerformanceMiddleware, config=config.get('performance', {}))
    
    if config.get('enable_security', True):
        app.add_middleware(SecurityMiddleware, config=config.get('security', {}))
    
    if config.get('enable_request_logging', True):
        app.add_middleware(RequestLoggingMiddleware, config=config.get('logging', {}))
    
    system_logger.info("中間件設置完成", extra={
        'middlewares': [
            name for name, enabled in [
                ('ErrorRecoveryMiddleware', config.get('enable_error_recovery', True)),
                ('UsageTrackingMiddleware', config.get('enable_usage_tracking', True)),
                ('PerformanceMiddleware', config.get('enable_performance_monitoring', True)),
                ('SecurityMiddleware', config.get('enable_security', True)),
                ('RequestLoggingMiddleware', config.get('enable_request_logging', True))
            ] if enabled
        ]
    })

if __name__ == "__main__":
    # 測試腳本
    print("中間件系統準備就緒")