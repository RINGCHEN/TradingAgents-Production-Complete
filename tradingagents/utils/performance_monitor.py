#!/usr/bin/env python3
"""
性能監控工具 (Performance Monitoring Utilities)
天工 (TianGong) - 用於測量和記錄函數執行性能的工具
"""

import time
import functools
from .logging_config import get_api_logger, get_system_logger

performance_logger = get_api_logger("performance")

def log_performance(log_level=None):
    """一個裝飾器，用於測量函數執行時間並記錄性能"""
    if log_level is None:
        log_level = performance_logger.info
    elif isinstance(log_level, str):
        log_level = getattr(performance_logger, log_level.lower(), performance_logger.info)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            
            # 執行異步函數
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000  # 轉換為毫秒
            
            log_level(
                f"Function {func.__name__} executed in {execution_time:.2f} ms",
                extra={
                    'function_name': func.__name__,
                    'execution_time_ms': execution_time,
                    'component': 'performance_monitor'
                }
            )
            return result
        return wrapper
    return decorator

# 示例用法 (僅供參考，不會實際執行)
if __name__ == "__main__":
    import asyncio

    @log_performance(log_level="info")
    async def example_async_function():
        await asyncio.sleep(0.1)
        return "Async task done"

    @log_performance(log_level="debug")
    def example_sync_function():
        time.sleep(0.05)
        return "Sync task done"

    async def main():
        print(await example_async_function())
        print(example_sync_function())

    asyncio.run(main())
