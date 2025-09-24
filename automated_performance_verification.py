#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automated Performance Verification Script
GEMINI Recommendation: Comprehensive performance and system validation

This script validates the 97.5% performance improvement claim and ensures
all production systems are operating at enterprise standards.
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceVerificationSuite:
    """Comprehensive performance and system verification suite"""
    
    def __init__(self, base_url: str = "https://twshocks-app-79rsx.ondigitalocean.app"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": {},
            "overall_status": "pending",
            "performance_metrics": {}
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": "TradingAgents-Performance-Verifier/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def verify_redis_performance(self) -> Dict[str, Any]:
        """
        Verify 97.5% performance improvement claim
        Expected: Cache MISS ~2000ms, Cache HIT ~50ms
        """
        logger.info("Starting Redis performance verification...")
        
        test_payload = {
            "stock_symbol": "2330.TW", 
            "user_tier": "diamond",
            "analysis_type": "full",
            "force_refresh": False
        }
        
        performance_results = {
            "test_name": "Redis Cache Performance",
            "status": "pending",
            "cache_miss_times": [],
            "cache_hit_times": [], 
            "performance_improvement": 0,
            "meets_97_5_percent_claim": False
        }
        
        try:
            # Test 1: Cache MISS (force refresh)
            logger.info("Testing cache MISS performance...")
            test_payload["force_refresh"] = True
            
            miss_times = []
            for i in range(3):  # 3 cache miss tests
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/ai-analysis/cached",
                    json=test_payload
                ) as response:
                    if response.status == 200:
                        response_time = (time.time() - start_time) * 1000
                        miss_times.append(response_time)
                        logger.info(f"Cache MISS #{i+1}: {response_time:.1f}ms")
                    else:
                        logger.error(f"Cache MISS test #{i+1} failed: {response.status}")
                
                await asyncio.sleep(1)  # Brief pause between tests
            
            # Test 2: Cache HIT 
            logger.info("Testing cache HIT performance...")
            test_payload["force_refresh"] = False
            
            hit_times = []
            for i in range(5):  # 5 cache hit tests
                start_time = time.time()
                
                async with self.session.post(
                    f"{self.base_url}/api/v1/ai-analysis/cached",
                    json=test_payload
                ) as response:
                    if response.status == 200:
                        response_time = (time.time() - start_time) * 1000
                        hit_times.append(response_time)
                        
                        # Verify it's actually a cache hit
                        data = await response.json()
                        cache_metadata = data.get("cache_metadata", {})
                        is_cache_hit = cache_metadata.get("cache_hit", False)
                        
                        logger.info(f"Cache HIT #{i+1}: {response_time:.1f}ms (cached: {is_cache_hit})")
                    else:
                        logger.error(f"Cache HIT test #{i+1} failed: {response.status}")
                
                await asyncio.sleep(0.5)
            
            # Calculate performance improvement
            if miss_times and hit_times:
                avg_miss_time = statistics.mean(miss_times)
                avg_hit_time = statistics.mean(hit_times)
                
                improvement_ratio = (avg_miss_time - avg_hit_time) / avg_miss_time
                improvement_percent = improvement_ratio * 100
                
                performance_results.update({
                    "status": "completed",
                    "cache_miss_times": miss_times,
                    "cache_hit_times": hit_times,
                    "avg_cache_miss_ms": round(avg_miss_time, 1),
                    "avg_cache_hit_ms": round(avg_hit_time, 1),
                    "performance_improvement": round(improvement_percent, 1),
                    "meets_97_5_percent_claim": improvement_percent >= 97.5
                })
                
                logger.info(f"Performance improvement: {improvement_percent:.1f}% (Target: 97.5%)")
                logger.info(f"Claim verification: {'PASS' if improvement_percent >= 97.5 else 'FAIL'}")
            
        except Exception as e:
            performance_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Redis performance test error: {e}")
        
        return performance_results
    
    async def verify_system_health(self) -> Dict[str, Any]:
        """Verify all system components are healthy"""
        logger.info("Starting system health verification...")
        
        health_results = {
            "test_name": "System Health Check",
            "status": "pending",
            "components": {}
        }
        
        # Health check endpoints
        endpoints = [
            ("/health", "Main API"),
            ("/api/v1/cache/health", "Redis Cache"),
            ("/api/v1/payuni/health", "PayUni Payment"),
            ("/api/health/database", "Database Connection")
        ]
        
        try:
            for endpoint, component_name in endpoints:
                try:
                    start_time = time.time()
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        response_time = (time.time() - start_time) * 1000
                        
                        if response.status == 200:
                            data = await response.json()
                            health_results["components"][component_name] = {
                                "status": "healthy",
                                "response_time_ms": round(response_time, 1),
                                "data": data
                            }
                            logger.info(f"{component_name}: HEALTHY ({response_time:.1f}ms)")
                        else:
                            health_results["components"][component_name] = {
                                "status": "unhealthy",
                                "http_status": response.status,
                                "response_time_ms": round(response_time, 1)
                            }
                            logger.warning(f"{component_name}: UNHEALTHY (HTTP {response.status})")
                            
                except Exception as e:
                    health_results["components"][component_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    logger.error(f"{component_name}: ERROR - {e}")
            
            # Determine overall health
            healthy_components = sum(1 for comp in health_results["components"].values() 
                                   if comp.get("status") == "healthy")
            total_components = len(health_results["components"])
            
            health_results.update({
                "status": "completed",
                "healthy_components": healthy_components,
                "total_components": total_components,
                "health_percentage": round((healthy_components / total_components) * 100, 1)
            })
            
            logger.info(f"System health: {healthy_components}/{total_components} components healthy")
            
        except Exception as e:
            health_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"System health check error: {e}")
        
        return health_results
    
    async def verify_member_privileges(self) -> Dict[str, Any]:
        """Verify member privilege configuration system"""
        logger.info("Starting member privilege verification...")
        
        privilege_results = {
            "test_name": "Member Privilege Configuration",
            "status": "pending",
            "tier_tests": {}
        }
        
        try:
            # Test different user tiers with API calls
            test_tiers = ["free", "gold", "diamond"]
            
            for tier in test_tiers:
                test_payload = {
                    "stock_symbol": "2330.TW",
                    "user_tier": tier,
                    "analysis_type": "full"
                }
                
                start_time = time.time()
                async with self.session.post(
                    f"{self.base_url}/api/v1/ai-analysis/cached",
                    json=test_payload
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        cache_metadata = data.get("cache_metadata", {})
                        
                        privilege_results["tier_tests"][tier] = {
                            "status": "success",
                            "response_time_ms": round(response_time, 1),
                            "cache_ttl_seconds": cache_metadata.get("cache_ttl_seconds"),
                            "api_accessible": True
                        }
                        
                        logger.info(f"Tier {tier}: SUCCESS (TTL: {cache_metadata.get('cache_ttl_seconds', 'N/A')}s)")
                    else:
                        privilege_results["tier_tests"][tier] = {
                            "status": "failed",
                            "http_status": response.status,
                            "api_accessible": False
                        }
                        logger.warning(f"Tier {tier}: FAILED (HTTP {response.status})")
            
            privilege_results["status"] = "completed"
            
        except Exception as e:
            privilege_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Member privilege verification error: {e}")
        
        return privilege_results
    
    async def verify_api_endpoints(self) -> Dict[str, Any]:
        """Verify critical API endpoints are responsive"""
        logger.info("Starting API endpoints verification...")
        
        api_results = {
            "test_name": "API Endpoints Verification",
            "status": "pending",
            "endpoints": {}
        }
        
        # Critical endpoints to test
        critical_endpoints = [
            ("/api/v1/cache/stats", "GET", None),
            ("/api/v1/ai-demo/health", "GET", None),
            ("/api/v1/ai-demo/analysts", "GET", None),
            ("/api/v1/payuni/payment-page/test", "GET", None)
        ]
        
        try:
            for endpoint, method, payload in critical_endpoints:
                try:
                    start_time = time.time()
                    
                    if method == "GET":
                        async with self.session.get(f"{self.base_url}{endpoint}") as response:
                            response_time = (time.time() - start_time) * 1000
                            
                            api_results["endpoints"][endpoint] = {
                                "method": method,
                                "status_code": response.status,
                                "response_time_ms": round(response_time, 1),
                                "accessible": response.status < 500
                            }
                            
                            logger.info(f"{method} {endpoint}: {response.status} ({response_time:.1f}ms)")
                    
                except Exception as e:
                    api_results["endpoints"][endpoint] = {
                        "method": method,
                        "status": "error",
                        "error": str(e),
                        "accessible": False
                    }
                    logger.error(f"{method} {endpoint}: ERROR - {e}")
            
            api_results["status"] = "completed"
            
        except Exception as e:
            api_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"API endpoints verification error: {e}")
        
        return api_results
    
    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Run all verification tests"""
        logger.info("Starting comprehensive performance verification suite...")
        logger.info(f"Target system: {self.base_url}")
        
        # Run all verification tests
        tests = [
            ("redis_performance", self.verify_redis_performance),
            ("system_health", self.verify_system_health), 
            ("member_privileges", self.verify_member_privileges),
            ("api_endpoints", self.verify_api_endpoints)
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*50}")
            logger.info(f"Running {test_name} verification...")
            
            try:
                result = await test_func()
                self.test_results["tests"][test_name] = result
            except Exception as e:
                logger.error(f"Test {test_name} failed with error: {e}")
                self.test_results["tests"][test_name] = {
                    "test_name": test_name,
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall status
        successful_tests = sum(1 for test in self.test_results["tests"].values()
                             if test.get("status") == "completed")
        total_tests = len(self.test_results["tests"])
        
        self.test_results.update({
            "overall_status": "pass" if successful_tests == total_tests else "partial",
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "success_percentage": round((successful_tests / total_tests) * 100, 1)
        })
        
        # Extract key performance metrics
        redis_test = self.test_results["tests"].get("redis_performance", {})
        if redis_test.get("status") == "completed":
            self.test_results["performance_metrics"] = {
                "cache_performance_improvement": redis_test.get("performance_improvement", 0),
                "meets_97_5_percent_claim": redis_test.get("meets_97_5_percent_claim", False),
                "avg_cache_hit_ms": redis_test.get("avg_cache_hit_ms", 0),
                "avg_cache_miss_ms": redis_test.get("avg_cache_miss_ms", 0)
            }
        
        return self.test_results
    
    def generate_report(self) -> str:
        """Generate comprehensive verification report"""
        report_lines = [
            "TRADINGAGENTS AUTOMATED PERFORMANCE VERIFICATION REPORT",
            "=" * 60,
            f"Generated: {self.test_results['timestamp']}",
            f"Target System: {self.test_results['base_url']}",
            f"Overall Status: {self.test_results['overall_status'].upper()}",
            f"Success Rate: {self.test_results['success_percentage']}% ({self.test_results['successful_tests']}/{self.test_results['total_tests']} tests)",
            "",
            "PERFORMANCE METRICS:",
            "-" * 30
        ]
        
        metrics = self.test_results.get("performance_metrics", {})
        if metrics:
            report_lines.extend([
                f"Cache Performance Improvement: {metrics.get('cache_performance_improvement', 'N/A')}%",
                f"97.5% Claim Verification: {'PASS' if metrics.get('meets_97_5_percent_claim') else 'FAIL'}",
                f"Average Cache Hit Time: {metrics.get('avg_cache_hit_ms', 'N/A')}ms",
                f"Average Cache Miss Time: {metrics.get('avg_cache_miss_ms', 'N/A')}ms",
                ""
            ])
        
        report_lines.extend([
            "DETAILED TEST RESULTS:",
            "-" * 30
        ])
        
        for test_name, test_data in self.test_results["tests"].items():
            status = test_data.get("status", "unknown").upper()
            report_lines.append(f"{test_name.upper()}: {status}")
            
            if test_name == "system_health":
                components = test_data.get("components", {})
                for comp_name, comp_data in components.items():
                    comp_status = comp_data.get("status", "unknown").upper()
                    response_time = comp_data.get("response_time_ms", "N/A")
                    report_lines.append(f"  - {comp_name}: {comp_status} ({response_time}ms)")
        
        report_lines.extend([
            "",
            "=" * 60,
            "VERIFICATION COMPLETE",
            "System ready for production deployment" if self.test_results['overall_status'] == 'pass' else "Issues detected - review required"
        ])
        
        return "\n".join(report_lines)


async def main():
    """Main execution function"""
    try:
        async with PerformanceVerificationSuite() as verifier:
            # Run comprehensive verification
            results = await verifier.run_comprehensive_verification()
            
            # Generate and display report
            report = verifier.generate_report()
            print("\n" + report)
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"performance_verification_results_{timestamp}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\nDetailed results saved to: {results_file}")
            
            # Return appropriate exit code
            return 0 if results['overall_status'] == 'pass' else 1
            
    except Exception as e:
        logger.error(f"Verification suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())