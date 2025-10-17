#!/usr/bin/env python3
"""
Prometheus Metrics for TradingAgents
天工 (TianGong) - Prometheus 指標收集系統

此模組提供 Prometheus 指標收集功能，包含：
1. Token 刷新性能指標
2. Redis 緩存指標
3. API 端點性能指標
4. 系統健康指標
"""

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from typing import Dict, Any, Optional
from datetime import datetime
import time

# 創建自定義 registry（避免與其他 Prometheus 實例衝突）
registry = CollectorRegistry()

# ==================== Token Refresh Metrics ====================

# Token 刷新請求計數器
token_refresh_requests = Counter(
    'token_refresh_requests_total',
    'Total number of token refresh requests',
    ['endpoint', 'status'],  # endpoint: user/admin, status: success/failure
    registry=registry
)

# Token 刷新響應時間
token_refresh_duration = Histogram(
    'token_refresh_duration_seconds',
    'Token refresh request duration in seconds',
    ['endpoint', 'cache_status'],  # cache_status: hit/miss/disabled
    buckets=[0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0],
    registry=registry
)

# ==================== Redis Cache Metrics ====================

# Redis 緩存命中計數器
redis_cache_hits = Counter(
    'redis_cache_hits_total',
    'Total number of Redis cache hits',
    ['cache_key_prefix'],  # cache_key_prefix: refresh_token/admin_user/...
    registry=registry
)

# Redis 緩存未命中計數器
redis_cache_misses = Counter(
    'redis_cache_misses_total',
    'Total number of Redis cache misses',
    ['cache_key_prefix'],
    registry=registry
)

# Redis 緩存錯誤計數器
redis_cache_errors = Counter(
    'redis_cache_errors_total',
    'Total number of Redis cache errors',
    ['operation', 'error_type'],  # operation: get/set/delete, error_type: connection/timeout/...
    registry=registry
)

# Redis 連接狀態
redis_connection_status = Gauge(
    'redis_connection_status',
    'Redis connection status (1=connected, 0=disconnected)',
    registry=registry
)

# Redis 緩存大小（可選，如果 Redis 提供此資訊）
redis_cache_size = Gauge(
    'redis_cache_size_bytes',
    'Total size of Redis cache in bytes',
    registry=registry
)

# Redis 緩存鍵數量
redis_cache_keys = Gauge(
    'redis_cache_keys_total',
    'Total number of keys in Redis cache',
    registry=registry
)

# ==================== API Performance Metrics ====================

# API 請求計數器
api_requests = Counter(
    'api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

# API 請求響應時間
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

# API 錯誤計數器
api_errors = Counter(
    'api_errors_total',
    'Total number of API errors',
    ['method', 'endpoint', 'error_type'],
    registry=registry
)

# ==================== JWT Operations Metrics ====================

# JWT 解碼操作計數器
jwt_decode_operations = Counter(
    'jwt_decode_operations_total',
    'Total number of JWT decode operations',
    ['token_type', 'status'],  # token_type: access/refresh, status: success/failure
    registry=registry
)

# JWT 生成操作計數器
jwt_generate_operations = Counter(
    'jwt_generate_operations_total',
    'Total number of JWT generate operations',
    ['token_type'],  # token_type: access/refresh
    registry=registry
)

# JWT 操作耗時
jwt_operation_duration = Histogram(
    'jwt_operation_duration_seconds',
    'JWT operation duration in seconds',
    ['operation'],  # operation: decode/generate
    buckets=[0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1],
    registry=registry
)

# ==================== System Health Metrics ====================

# 活躍用戶會話數
active_user_sessions = Gauge(
    'active_user_sessions',
    'Number of active user sessions',
    registry=registry
)

# 活躍 API 密鑰數
active_api_keys = Gauge(
    'active_api_keys',
    'Number of active API keys',
    registry=registry
)

# 已撤銷令牌數
revoked_tokens = Gauge(
    'revoked_tokens_total',
    'Total number of revoked tokens',
    registry=registry
)

# 系統資訊
system_info = Info(
    'tradingagents_system',
    'TradingAgents system information',
    registry=registry
)

# ==================== Helper Functions ====================

class MetricsCollector:
    """指標收集器"""

    @staticmethod
    def record_token_refresh(
        endpoint: str,
        duration_seconds: float,
        cache_status: str,
        success: bool
    ):
        """
        記錄 Token 刷新指標

        Args:
            endpoint: 'user' or 'admin'
            duration_seconds: 請求耗時（秒）
            cache_status: 'hit', 'miss', or 'disabled'
            success: 是否成功
        """
        status = 'success' if success else 'failure'
        token_refresh_requests.labels(endpoint=endpoint, status=status).inc()
        token_refresh_duration.labels(
            endpoint=endpoint,
            cache_status=cache_status
        ).observe(duration_seconds)

    @staticmethod
    def record_cache_operation(
        operation: str,
        cache_key_prefix: str,
        hit: Optional[bool] = None,
        error_type: Optional[str] = None
    ):
        """
        記錄緩存操作指標

        Args:
            operation: 'get', 'set', 'delete'
            cache_key_prefix: 緩存鍵前綴
            hit: 是否命中（僅 get 操作）
            error_type: 錯誤類型（如有）
        """
        if error_type:
            redis_cache_errors.labels(
                operation=operation,
                error_type=error_type
            ).inc()
        elif operation == 'get':
            if hit:
                redis_cache_hits.labels(cache_key_prefix=cache_key_prefix).inc()
            else:
                redis_cache_misses.labels(cache_key_prefix=cache_key_prefix).inc()

    @staticmethod
    def record_api_request(
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        error_type: Optional[str] = None
    ):
        """
        記錄 API 請求指標

        Args:
            method: HTTP 方法
            endpoint: API 端點
            status_code: HTTP 狀態碼
            duration_seconds: 請求耗時（秒）
            error_type: 錯誤類型（如有）
        """
        api_requests.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_seconds)

        if error_type:
            api_errors.labels(
                method=method,
                endpoint=endpoint,
                error_type=error_type
            ).inc()

    @staticmethod
    def record_jwt_operation(
        operation: str,
        token_type: str,
        duration_seconds: float,
        success: bool = True
    ):
        """
        記錄 JWT 操作指標

        Args:
            operation: 'decode' or 'generate'
            token_type: 'access' or 'refresh'
            duration_seconds: 操作耗時（秒）
            success: 是否成功（僅 decode 操作）
        """
        if operation == 'decode':
            status = 'success' if success else 'failure'
            jwt_decode_operations.labels(
                token_type=token_type,
                status=status
            ).inc()
        elif operation == 'generate':
            jwt_generate_operations.labels(token_type=token_type).inc()

        jwt_operation_duration.labels(operation=operation).observe(duration_seconds)

    @staticmethod
    def update_redis_status(
        connected: bool,
        cache_size_bytes: Optional[int] = None,
        keys_count: Optional[int] = None
    ):
        """
        更新 Redis 狀態指標

        Args:
            connected: 是否連接
            cache_size_bytes: 緩存大小（字節）
            keys_count: 鍵數量
        """
        redis_connection_status.set(1 if connected else 0)

        if cache_size_bytes is not None:
            redis_cache_size.set(cache_size_bytes)

        if keys_count is not None:
            redis_cache_keys.set(keys_count)

    @staticmethod
    def update_system_metrics(
        active_sessions: int,
        active_keys: int,
        revoked_tokens_count: int
    ):
        """
        更新系統健康指標

        Args:
            active_sessions: 活躍會話數
            active_keys: 活躍 API 密鑰數
            revoked_tokens_count: 已撤銷令牌數
        """
        active_user_sessions.set(active_sessions)
        active_api_keys.set(active_keys)
        revoked_tokens.set(revoked_tokens_count)

    @staticmethod
    def set_system_info(info: Dict[str, str]):
        """
        設置系統資訊

        Args:
            info: 系統資訊字典
        """
        system_info.info(info)

# ==================== Metrics Endpoint ====================

def get_metrics() -> bytes:
    """
    獲取 Prometheus 格式的指標數據

    Returns:
        bytes: Prometheus 格式的指標數據
    """
    return generate_latest(registry)

def get_metrics_content_type() -> str:
    """
    獲取 Prometheus 指標的 Content-Type

    Returns:
        str: Content-Type header value
    """
    return CONTENT_TYPE_LATEST

# ==================== Usage Examples ====================

if __name__ == "__main__":
    """示例：如何使用指標收集器"""

    # 1. 記錄 Token 刷新
    collector = MetricsCollector()

    # 模擬用戶端 refresh（緩存命中）
    collector.record_token_refresh(
        endpoint='user',
        duration_seconds=0.008,
        cache_status='hit',
        success=True
    )

    # 模擬管理員端 refresh（緩存未命中）
    collector.record_token_refresh(
        endpoint='admin',
        duration_seconds=0.072,
        cache_status='miss',
        success=True
    )

    # 2. 記錄緩存操作
    collector.record_cache_operation(
        operation='get',
        cache_key_prefix='refresh_token',
        hit=True
    )

    collector.record_cache_operation(
        operation='get',
        cache_key_prefix='admin_user',
        hit=False
    )

    # 3. 記錄 API 請求
    collector.record_api_request(
        method='POST',
        endpoint='/api/auth/refresh',
        status_code=200,
        duration_seconds=0.045
    )

    # 4. 記錄 JWT 操作
    collector.record_jwt_operation(
        operation='decode',
        token_type='refresh',
        duration_seconds=0.003,
        success=True
    )

    collector.record_jwt_operation(
        operation='generate',
        token_type='access',
        duration_seconds=0.002
    )

    # 5. 更新 Redis 狀態
    collector.update_redis_status(
        connected=True,
        cache_size_bytes=1024000,
        keys_count=150
    )

    # 6. 更新系統指標
    collector.update_system_metrics(
        active_sessions=45,
        active_keys=12,
        revoked_tokens_count=8
    )

    # 7. 設置系統資訊
    collector.set_system_info({
        'version': '2.0.0',
        'environment': 'production',
        'deployment': 'digitalocean',
        'optimization_date': '2025-10-17'
    })

    # 8. 生成指標數據
    print("Prometheus Metrics:")
    print("=" * 50)
    print(get_metrics().decode('utf-8'))
