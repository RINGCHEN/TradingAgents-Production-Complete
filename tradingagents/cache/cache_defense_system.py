#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cache Defense System
GOOGLE Chief Risk Officer Advanced Security Implementation

This module implements comprehensive cache defense mechanisms to protect against:
1. Cache Penetration Attacks (缓存穿透)
2. Cache Avalanche (缓存雪崩)  
3. Circuit Breaker Protection (熔断器保护)
4. Secondary Cache for High Availability (二级缓存)
"""

import asyncio
import time
import random
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import threading
import inspect

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"           # Blocking requests
    HALF_OPEN = "half_open" # Testing recovery

@dataclass
class CacheDefenseMetrics:
    """Cache defense system metrics"""
    
    # Cache operations
    cache_hits: int = 0
    cache_misses: int = 0
    negative_cache_hits: int = 0
    
    # Defense actions
    penetration_blocked: int = 0
    avalanche_prevented: int = 0
    circuit_breaker_triggered: int = 0
    
    # Performance
    avg_response_time_ms: float = 0.0
    peak_concurrent_requests: int = 0
    
    # Timestamps
    last_reset: datetime = field(default_factory=datetime.now)
    
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0.0
    
    def defense_effectiveness(self) -> float:
        """Calculate defense effectiveness percentage"""
        total_attacks = self.penetration_blocked + self.avalanche_prevented
        total_requests = self.cache_hits + self.cache_misses + total_attacks
        return (total_attacks / total_requests * 100) if total_requests > 0 else 0.0

class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation
    GOOGLE's recommendation for protecting backend services
    """
    
    def __init__(self, failure_threshold: int = 10, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.Lock()
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection - CODEX Async Fix"""
        
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                # Check if timeout has passed
                if (time.time() - self.last_failure_time) > self.timeout_seconds:
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.failure_count = 0
                    logger.info("🔄 Circuit breaker moved to HALF_OPEN state")
                else:
                    logger.warning("⚠️ Circuit breaker OPEN - request blocked")
                    raise Exception("Circuit breaker is OPEN")
            
        try:
            # CODEX Critical Fix: Proper async handling
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Success - reset if we were in half-open
            if self.state == CircuitBreakerState.HALF_OPEN:
                with self._lock:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    logger.info("✅ Circuit breaker CLOSED - service recovered")
            
            return result
            
        except Exception as e:
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitBreakerState.OPEN
                    logger.error(f"🚨 Circuit breaker OPENED after {self.failure_count} failures")
                
            logger.warning(f"⚡ Circuit breaker recorded failure: {str(e)}")
            raise e
    
    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
            "timeout_seconds": self.timeout_seconds
        }

class InMemoryCache:
    """
    In-memory secondary cache for high availability
    GOOGLE's secondary cache recommendation
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, Dict] = {}
        self.access_times: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from in-memory cache"""
        
        with self._lock:
            if key not in self.cache:
                return None
            
            cache_entry = self.cache[key]
            
            # Check expiration
            if time.time() > cache_entry["expires_at"]:
                del self.cache[key]
                if key in self.access_times:
                    del self.access_times[key]
                return None
            
            # Update access time for LRU
            self.access_times[key] = time.time()
            
            logger.debug(f"📱 In-memory cache HIT: {key}")
            return cache_entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in in-memory cache with LRU eviction"""
        
        with self._lock:
            # Evict expired entries first
            self._evict_expired()
            
            # If at capacity, evict LRU
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_lru()
            
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl
            
            self.cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time()
            }
            
            self.access_times[key] = time.time()
            
            logger.debug(f"📱 In-memory cache SET: {key} (TTL: {ttl}s)")
            return True
    
    def _evict_expired(self):
        """Evict expired entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, cache_entry in self.cache.items():
            if current_time > cache_entry["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.access_times:
            return
        
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def size(self) -> int:
        """Get current cache size"""
        return len(self.cache)
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()

class CacheDefenseSystem:
    """
    Comprehensive Cache Defense System
    Implements GOOGLE Chief Risk Officer recommendations
    """
    
    def __init__(self, redis_service=None):
        self.redis_service = redis_service
        self.circuit_breaker = CircuitBreaker(failure_threshold=10, timeout_seconds=60)
        self.secondary_cache = InMemoryCache(max_size=1000, default_ttl=300)
        self.metrics = CacheDefenseMetrics()
        
        # Defense configuration
        self.negative_cache_ttl = 300  # 5 minutes for negative results
        self.jitter_range = 0.1       # ±10% TTL jitter
        self.max_concurrent_requests = 100
        self.current_requests = 0
        self._request_lock = threading.Lock()
        
        # Penetration detection
        self.request_patterns: Dict[str, List[float]] = defaultdict(list)
        self.suspicious_ips: Dict[str, int] = defaultdict(int)
        
    def add_ttl_jitter(self, base_ttl: int) -> int:
        """
        Add random jitter to TTL to prevent cache avalanche
        GOOGLE's TTL Jitter recommendation
        """
        jitter_amount = int(base_ttl * self.jitter_range)
        jitter = random.randint(-jitter_amount, jitter_amount)
        final_ttl = max(60, base_ttl + jitter)  # Minimum 1 minute TTL
        
        logger.debug(f"🎲 TTL jitter applied: {base_ttl}s → {final_ttl}s (jitter: {jitter:+d}s)")
        return final_ttl
    
    async def get_with_defense(self, cache_key: str, 
                              fetch_function=None,
                              user_tier: str = "free",
                              user_ip: Optional[str] = None,
                              base_ttl: int = 1800) -> Dict[str, Any]:
        """
        Get cached value with comprehensive defense mechanisms
        """
        
        start_time = time.time()
        
        # 1. Rate limiting check
        if not self._check_rate_limit(user_ip):
            self.metrics.penetration_blocked += 1
            raise Exception("Rate limit exceeded - potential attack detected")
        
        # 2. Try Redis cache first
        try:
            cached_result = await self._get_from_redis_with_circuit_breaker(cache_key)
            if cached_result:
                self.metrics.cache_hits += 1
                
                # Check if it's a negative cache entry
                if cached_result.get("__negative_cache__"):
                    self.metrics.negative_cache_hits += 1
                    logger.info(f"🛡️ Negative cache HIT prevented penetration: {cache_key}")
                    return {
                        "error": "Resource not available",
                        "cache_metadata": {
                            "cache_hit": True,
                            "defense_type": "negative_cache",
                            "response_time_ms": (time.time() - start_time) * 1000
                        }
                    }
                
                logger.info(f"⚡ Redis cache HIT: {cache_key}")
                return cached_result
                
        except Exception as e:
            logger.warning(f"Redis cache failed: {e}")
        
        # 3. Try secondary in-memory cache
        secondary_result = self.secondary_cache.get(cache_key)
        if secondary_result:
            self.metrics.cache_hits += 1
            logger.info(f"📱 Secondary cache HIT: {cache_key}")
            return secondary_result
        
        # 4. Cache MISS - fetch data if function provided
        if not fetch_function:
            self.metrics.cache_misses += 1
            return {"error": "Cache miss and no fetch function provided"}
        
        try:
            # Fetch fresh data with circuit breaker protection
            fresh_data = await self.circuit_breaker.call(fetch_function)
            
            if not fresh_data or (isinstance(fresh_data, dict) and fresh_data.get("error")):
                # Store negative result to prevent cache penetration
                await self._store_negative_cache(cache_key, user_tier)
                self.metrics.cache_misses += 1
                
                return {
                    "error": "Data not available",
                    "cache_metadata": {
                        "cache_hit": False,
                        "defense_type": "negative_cache_stored",
                        "response_time_ms": (time.time() - start_time) * 1000
                    }
                }
            
            # Store in both cache layers
            final_ttl = self.add_ttl_jitter(base_ttl)
            
            await self._store_in_redis_with_defense(cache_key, fresh_data, final_ttl, user_tier)
            self.secondary_cache.set(cache_key, fresh_data, ttl=min(final_ttl, 600))  # Max 10min for secondary
            
            self.metrics.cache_misses += 1
            logger.info(f"💾 Fresh data cached with defense: {cache_key}")
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"Failed to fetch fresh data: {e}")
            
            # Store negative cache to prevent repeated failures
            await self._store_negative_cache(cache_key, user_tier)
            
            return {
                "error": f"Service temporarily unavailable: {str(e)}",
                "cache_metadata": {
                    "cache_hit": False,
                    "defense_type": "circuit_breaker_protection",
                    "response_time_ms": (time.time() - start_time) * 1000
                }
            }
    
    async def _get_from_redis_with_circuit_breaker(self, cache_key: str) -> Optional[Dict]:
        """Get from Redis with circuit breaker protection"""
        
        if not self.redis_service or not self.redis_service.is_connected:
            return None
        
        try:
            return await self.circuit_breaker.call(
                self.redis_service.get_cached_analysis,
                cache_key
            )
        except Exception as e:
            logger.warning(f"Redis circuit breaker activated: {e}")
            return None
    
    async def _store_in_redis_with_defense(self, cache_key: str, data: Dict, 
                                          ttl: int, user_tier: str):
        """Store in Redis with defense mechanisms"""
        
        if not self.redis_service or not self.redis_service.is_connected:
            return False
        
        try:
            return await self.circuit_breaker.call(
                self.redis_service.cache_analysis,
                cache_key,
                data,
                ttl=ttl,
                user_tier=user_tier
            )
        except Exception as e:
            logger.warning(f"Redis storage with circuit breaker failed: {e}")
            return False
    
    async def _store_negative_cache(self, cache_key: str, user_tier: str):
        """
        Store negative cache result to prevent penetration attacks
        GOOGLE's Negative Cache recommendation
        """
        
        negative_result = {
            "__negative_cache__": True,
            "cached_at": datetime.now().isoformat(),
            "message": "Resource not available",
            "user_tier": user_tier
        }
        
        jittered_ttl = self.add_ttl_jitter(self.negative_cache_ttl)
        
        # Store in both caches
        await self._store_in_redis_with_defense(cache_key, negative_result, jittered_ttl, user_tier)
        self.secondary_cache.set(cache_key, negative_result, ttl=jittered_ttl)
        
        logger.info(f"🛡️ Negative cache stored: {cache_key} (TTL: {jittered_ttl}s)")
    
    def _check_rate_limit(self, user_ip: Optional[str]) -> bool:
        """
        Check for potential penetration attacks based on request patterns
        Simple implementation of rate limiting
        """
        
        if not user_ip:
            return True  # Allow requests without IP
        
        current_time = time.time()
        
        # Clean old request records (older than 1 minute)
        self.request_patterns[user_ip] = [
            req_time for req_time in self.request_patterns[user_ip]
            if current_time - req_time < 60
        ]
        
        # Add current request
        self.request_patterns[user_ip].append(current_time)
        
        # Check if this IP is making too many requests
        requests_per_minute = len(self.request_patterns[user_ip])
        
        if requests_per_minute > 60:  # Max 60 requests per minute per IP
            self.suspicious_ips[user_ip] += 1
            logger.warning(f"🚨 Suspicious activity from IP {user_ip}: {requests_per_minute} req/min")
            return False
        
        return True
    
    def get_defense_metrics(self) -> Dict[str, Any]:
        """Get comprehensive defense system metrics"""
        
        # Update average response time (simplified)
        current_time = time.time()
        uptime_seconds = (current_time - self.metrics.last_reset.timestamp())
        
        return {
            "cache_performance": {
                "hit_rate_percent": round(self.metrics.hit_rate(), 2),
                "total_hits": self.metrics.cache_hits,
                "total_misses": self.metrics.cache_misses,
                "negative_cache_hits": self.metrics.negative_cache_hits
            },
            
            "defense_effectiveness": {
                "penetration_attacks_blocked": self.metrics.penetration_blocked,
                "avalanche_incidents_prevented": self.metrics.avalanche_prevented,
                "circuit_breaker_activations": self.metrics.circuit_breaker_triggered,
                "defense_effectiveness_percent": round(self.metrics.defense_effectiveness(), 2)
            },
            
            "system_health": {
                "secondary_cache_size": self.secondary_cache.size(),
                "circuit_breaker_state": self.circuit_breaker.get_state(),
                "suspicious_ips": len(self.suspicious_ips),
                "uptime_seconds": int(uptime_seconds)
            },
            
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """Reset defense metrics"""
        self.metrics = CacheDefenseMetrics()
        self.suspicious_ips.clear()
        logger.info("📊 Defense metrics reset")

# Global cache defense system instance
cache_defense = CacheDefenseSystem()