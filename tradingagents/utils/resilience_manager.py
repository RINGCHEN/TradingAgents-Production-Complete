#!/usr/bin/env python3
"""
彈性管理器 (Resilience Manager)
天工開物系統的錯誤處理和容錯機制

此模組提供：
1. 智能重試機制
2. 斷路器模式
3. 超時控制
4. 錯誤恢復策略
5. 系統健康檢查
6. 故障轉移機制

由包拯(安全顧問)和墨子(運維工程師)聯合設計實現
"""

import asyncio
import functools
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from .logging_config import get_system_logger
from .error_handler import handle_error

logger = get_system_logger("resilience_manager")

class CircuitState(Enum):
    """斷路器狀態"""
    CLOSED = "closed"      # 正常狀態
    OPEN = "open"          # 斷開狀態
    HALF_OPEN = "half_open"  # 半開狀態

class RetryStrategy(Enum):
    """重試策略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    CUSTOM = "custom"

class HealthStatus(Enum):
    """健康狀態"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class RetryConfig:
    """重試配置"""
    max_attempts: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[type] = field(default_factory=lambda: [Exception])
    non_retryable_exceptions: List[type] = field(default_factory=list)

@dataclass
class CircuitBreakerConfig:
    """斷路器配置"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception
    success_threshold: int = 3  # 半開狀態下需要成功的次數

@dataclass
class TimeoutConfig:
    """超時配置"""
    operation_timeout: float = 30.0
    connection_timeout: float = 10.0
    read_timeout: float = 20.0

@dataclass
class FailureRecord:
    """故障記錄"""
    failure_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    exception_type: str = ""
    exception_message: str = ""
    operation: str = ""
    retry_count: int = 0
    recovery_action: Optional[str] = None
    resolved: bool = False

class CircuitBreaker:
    """斷路器實現"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state_change_listeners = []
    
    def add_state_change_listener(self, listener: Callable):
        """添加狀態變化監聽器"""
        self.state_change_listeners.append(listener)
    
    def _notify_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """通知狀態變化"""
        for listener in self.state_change_listeners:
            try:
                listener(old_state, new_state)
            except Exception as e:
                logger.error(f"斷路器狀態變化通知失敗: {e}")
    
    def _change_state(self, new_state: CircuitState):
        """改變斷路器狀態"""
        old_state = self.state
        self.state = new_state
        
        if old_state != new_state:
            logger.info(f"斷路器狀態變化: {old_state.value} -> {new_state.value}")
            self._notify_state_change(old_state, new_state)
    
    def _should_attempt_reset(self) -> bool:
        """檢查是否應該嘗試重置"""
        if self.last_failure_time is None:
            return False
        
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def call(self, func: Callable, *args, **kwargs):
        """執行受保護的調用"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._change_state(CircuitState.HALF_OPEN)
                self.success_count = 0
            else:
                raise Exception("斷路器開啟，拒絕請求")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    async def async_call(self, func: Callable, *args, **kwargs):
        """執行受保護的異步調用"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._change_state(CircuitState.HALF_OPEN)
                self.success_count = 0
            else:
                raise Exception("斷路器開啟，拒絕請求")
        
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """處理成功情況"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self._change_state(CircuitState.CLOSED)
                self.failure_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """處理失敗情況"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self._change_state(CircuitState.OPEN)
        elif self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
            self._change_state(CircuitState.OPEN)

class RetryManager:
    """重試管理器"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def _calculate_delay(self, attempt: int) -> float:
        """計算延遲時間"""
        if self.config.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.config.base_delay
        elif self.config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.backoff_multiplier ** (attempt - 1))
        elif self.config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt
        else:
            delay = self.config.base_delay
        
        # 限制最大延遲
        delay = min(delay, self.config.max_delay)
        
        # 添加抖動
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        return delay
    
    def _is_retryable_exception(self, exception: Exception) -> bool:
        """檢查異常是否可重試"""
        # 檢查不可重試的異常
        for non_retryable in self.config.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                return False
        
        # 檢查可重試的異常
        for retryable in self.config.retryable_exceptions:
            if isinstance(exception, retryable):
                return True
        
        return False
    
    async def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """執行帶重試的函數"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if not self._is_retryable_exception(e):
                    logger.error(f"遇到不可重試異常: {type(e).__name__}: {e}")
                    raise
                
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"執行失敗，第{attempt}次重試，{delay:.2f}秒後重試: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"重試{self.config.max_attempts}次後仍然失敗: {e}")
        
        raise last_exception

class HealthChecker:
    """健康檢查器"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, HealthStatus] = {}
        self.last_check_time: Dict[str, datetime] = {}
    
    def register_health_check(self, name: str, check_func: Callable, check_interval: float = 60.0):
        """註冊健康檢查"""
        self.health_checks[name] = check_func
        self.health_status[name] = HealthStatus.HEALTHY
        logger.info(f"已註冊健康檢查: {name}")
    
    async def check_health(self, component_name: str = None) -> Dict[str, HealthStatus]:
        """執行健康檢查"""
        if component_name:
            components = {component_name: self.health_checks[component_name]}
        else:
            components = self.health_checks
        
        results = {}
        
        for name, check_func in components.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    is_healthy = await check_func()
                else:
                    is_healthy = check_func()
                
                status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
                self.health_status[name] = status
                self.last_check_time[name] = datetime.now()
                results[name] = status
                
            except Exception as e:
                logger.error(f"健康檢查失敗 {name}: {e}")
                self.health_status[name] = HealthStatus.CRITICAL
                results[name] = HealthStatus.CRITICAL
        
        return results
    
    def get_overall_health(self) -> HealthStatus:
        """獲取總體健康狀態"""
        if not self.health_status:
            return HealthStatus.HEALTHY
        
        statuses = list(self.health_status.values())
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            return HealthStatus.CRITICAL
        elif any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY

class ResilienceManager:
    """彈性管理器 - 天工開物系統核心容錯組件"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_managers: Dict[str, RetryManager] = {}
        self.health_checker = HealthChecker()
        self.failure_records: List[FailureRecord] = []
        self.fallback_handlers: Dict[str, Callable] = {}
        
        # 默認配置
        self.default_retry_config = RetryConfig(**self.config.get('retry', {}))
        self.default_circuit_config = CircuitBreakerConfig(**self.config.get('circuit_breaker', {}))
        self.default_timeout_config = TimeoutConfig(**self.config.get('timeout', {}))
        
        logger.info("彈性管理器已初始化", extra={
            'default_retry_attempts': self.default_retry_config.max_attempts,
            'circuit_failure_threshold': self.default_circuit_config.failure_threshold,
            'default_timeout': self.default_timeout_config.operation_timeout
        })
    
    def get_circuit_breaker(self, name: str, config: Optional[CircuitBreakerConfig] = None) -> CircuitBreaker:
        """獲取或創建斷路器"""
        if name not in self.circuit_breakers:
            cb_config = config or self.default_circuit_config
            self.circuit_breakers[name] = CircuitBreaker(cb_config)
            logger.info(f"創建斷路器: {name}")
        
        return self.circuit_breakers[name]
    
    def get_retry_manager(self, name: str, config: Optional[RetryConfig] = None) -> RetryManager:
        """獲取或創建重試管理器"""
        if name not in self.retry_managers:
            retry_config = config or self.default_retry_config
            self.retry_managers[name] = RetryManager(retry_config)
            logger.info(f"創建重試管理器: {name}")
        
        return self.retry_managers[name]
    
    def register_fallback(self, operation_name: str, fallback_func: Callable):
        """註冊降級處理器"""
        self.fallback_handlers[operation_name] = fallback_func
        logger.info(f"已註冊降級處理器: {operation_name}")
    
    async def execute_with_resilience(self, 
                                    operation_name: str,
                                    func: Callable,
                                    *args,
                                    use_circuit_breaker: bool = True,
                                    use_retry: bool = True,
                                    timeout: Optional[float] = None,
                                    **kwargs) -> Any:
        """執行具有彈性機制的操作"""
        
        start_time = time.time()
        
        try:
            # 設置超時
            operation_timeout = timeout or self.default_timeout_config.operation_timeout
            
            async def _execute():
                result = None
                
                # 使用斷路器
                if use_circuit_breaker:
                    circuit_breaker = self.get_circuit_breaker(operation_name)
                    
                    # 使用重試機制
                    if use_retry:
                        retry_manager = self.get_retry_manager(operation_name)
                        result = await retry_manager.execute_with_retry(
                            lambda: circuit_breaker.async_call(func, *args, **kwargs)
                        )
                    else:
                        result = await circuit_breaker.async_call(func, *args, **kwargs)
                else:
                    # 只使用重試機制
                    if use_retry:
                        retry_manager = self.get_retry_manager(operation_name)
                        result = await retry_manager.execute_with_retry(func, *args, **kwargs)
                    else:
                        if asyncio.iscoroutinefunction(func):
                            result = await func(*args, **kwargs)
                        else:
                            result = func(*args, **kwargs)
                
                return result
            
            # 執行帶超時的操作
            result = await asyncio.wait_for(_execute(), timeout=operation_timeout)
            
            execution_time = time.time() - start_time
            logger.debug(f"操作 {operation_name} 成功執行，耗時 {execution_time:.3f}s")
            
            return result
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            error_msg = f"操作 {operation_name} 超時 ({execution_time:.3f}s > {operation_timeout}s)"
            
            # 記錄故障
            self._record_failure(operation_name, "TimeoutError", error_msg)
            
            # 嘗試降級處理
            if operation_name in self.fallback_handlers:
                logger.warning(f"{error_msg}，執行降級處理")
                try:
                    fallback_func = self.fallback_handlers[operation_name]
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    else:
                        return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"降級處理也失敗: {fallback_error}")
            
            raise asyncio.TimeoutError(error_msg)
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"操作 {operation_name} 執行失敗: {e}"
            
            # 記錄故障
            self._record_failure(operation_name, type(e).__name__, str(e))
            
            # 嘗試降級處理
            if operation_name in self.fallback_handlers:
                logger.warning(f"{error_msg}，執行降級處理")
                try:
                    fallback_func = self.fallback_handlers[operation_name]
                    if asyncio.iscoroutinefunction(fallback_func):
                        return await fallback_func(*args, **kwargs)
                    else:
                        return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"降級處理也失敗: {fallback_error}")
            
            logger.error(f"{error_msg}，執行時間 {execution_time:.3f}s")
            raise
    
    def _record_failure(self, operation: str, exception_type: str, exception_message: str):
        """記錄故障"""
        record = FailureRecord(
            operation=operation,
            exception_type=exception_type,
            exception_message=exception_message
        )
        
        self.failure_records.append(record)
        
        # 保持最近1000條記錄
        if len(self.failure_records) > 1000:
            self.failure_records = self.failure_records[-1000:]
        
        logger.error(f"記錄故障: {operation} - {exception_type}: {exception_message}")
    
    async def get_system_health_report(self) -> Dict[str, Any]:
        """獲取系統健康報告"""
        health_results = await self.health_checker.check_health()
        overall_health = self.health_checker.get_overall_health()
        
        # 統計故障記錄
        recent_failures = [f for f in self.failure_records 
                          if (datetime.now() - f.timestamp).total_seconds() < 3600]  # 最近1小時
        
        failure_stats = {}
        for failure in recent_failures:
            operation = failure.operation
            if operation not in failure_stats:
                failure_stats[operation] = {'count': 0, 'types': {}}
            failure_stats[operation]['count'] += 1
            
            exc_type = failure.exception_type
            if exc_type not in failure_stats[operation]['types']:
                failure_stats[operation]['types'][exc_type] = 0
            failure_stats[operation]['types'][exc_type] += 1
        
        # 斷路器狀態
        circuit_status = {}
        for name, cb in self.circuit_breakers.items():
            circuit_status[name] = {
                'state': cb.state.value,
                'failure_count': cb.failure_count,
                'success_count': cb.success_count,
                'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None
            }
        
        return {
            'overall_health': overall_health.value,
            'component_health': {name: status.value for name, status in health_results.items()},
            'circuit_breakers': circuit_status,
            'recent_failures': failure_stats,
            'total_failure_records': len(self.failure_records),
            'registered_fallbacks': list(self.fallback_handlers.keys()),
            'report_generated_at': datetime.now().isoformat()
        }

# 裝飾器和便利函數

def resilient(operation_name: str = None,
             retry_config: Optional[RetryConfig] = None,
             circuit_config: Optional[CircuitBreakerConfig] = None,
             timeout: Optional[float] = None,
             use_circuit_breaker: bool = True,
             use_retry: bool = True):
    """彈性操作裝飾器"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 獲取全局彈性管理器實例
            if not hasattr(wrapper, '_resilience_manager'):
                wrapper._resilience_manager = get_global_resilience_manager()
            
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            return await wrapper._resilience_manager.execute_with_resilience(
                operation_name=op_name,
                func=func,
                *args,
                use_circuit_breaker=use_circuit_breaker,
                use_retry=use_retry,
                timeout=timeout,
                **kwargs
            )
        
        return wrapper
    return decorator

# 全局彈性管理器實例
_global_resilience_manager = None

def get_global_resilience_manager() -> ResilienceManager:
    """獲取全局彈性管理器實例"""
    global _global_resilience_manager
    if _global_resilience_manager is None:
        _global_resilience_manager = ResilienceManager()
    return _global_resilience_manager

def initialize_resilience_manager(config: Dict[str, Any]) -> ResilienceManager:
    """初始化全局彈性管理器"""
    global _global_resilience_manager
    _global_resilience_manager = ResilienceManager(config)
    return _global_resilience_manager

if __name__ == "__main__":
    # 測試腳本
    async def test_resilience_manager():
        print("測試彈性管理器...")
        
        # 初始化管理器
        manager = ResilienceManager({
            'retry': {'max_attempts': 3, 'base_delay': 1.0},
            'circuit_breaker': {'failure_threshold': 2, 'recovery_timeout': 5.0},
            'timeout': {'operation_timeout': 10.0}
        })
        
        # 測試函數
        call_count = 0
        
        async def test_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"模擬失敗 {call_count}")
            return f"成功 {call_count}"
        
        # 註冊降級處理
        manager.register_fallback("test_operation", lambda: "降級回應")
        
        # 執行彈性操作
        try:
            result = await manager.execute_with_resilience(
                "test_operation",
                test_function
            )
            print(f"操作結果: {result}")
        except Exception as e:
            print(f"操作最終失敗: {e}")
        
        # 健康檢查
        manager.health_checker.register_health_check(
            "test_component",
            lambda: True
        )
        
        health_report = await manager.get_system_health_report()
        print(f"健康報告: {json.dumps(health_report, indent=2, ensure_ascii=False)}")
        
        print("彈性管理器測試完成")
    
    asyncio.run(test_resilience_manager())