#!/usr/bin/env python3
"""
日誌配置
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """獲取日誌記錄器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger

def get_api_logger(name: str) -> logging.Logger:
    """獲取API日誌記錄器"""
    return get_logger(f"api.{name}")

def get_security_logger(name: str) -> logging.Logger:
    """獲取安全日誌記錄器"""
    return get_logger(f"security.{name}")

def get_analysis_logger(name: str) -> logging.Logger:
    """獲取分析日誌記錄器"""
    return get_logger(f"analysis.{name}")

def get_system_logger(name: str) -> logging.Logger:
    """獲取系統日誌記錄器"""
    return get_logger(f"system.{name}")

def get_performance_logger(name: str) -> logging.Logger:
    """獲取性能日誌記錄器"""
    return get_logger(f"performance.{name}")

def log_performance(operation: str, duration: float, details: dict = None):
    """記錄性能日誌"""
    logger = get_performance_logger("system")
    details_str = f" - {details}" if details else ""
    logger.info(f"Performance: {operation} took {duration:.3f}s{details_str}")
