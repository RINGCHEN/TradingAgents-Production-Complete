#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Adversarial Performance Verification
GOOGLE Chief Risk Officer Extreme Scenario Testing

This script tests the system under adversarial conditions and extreme scenarios
to validate the effectiveness of defense mechanisms.
"""

import asyncio
import aiohttp
import time
import json
import random
import string
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
import statistics

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdversarialTestSuite:
    """
    Comprehensive adversarial testing for cache defense systems
    GOOGLE's recommendation for testing unknown scenarios
    """
    
    def __init__(self, base_url: str = "https://twshocks-app-79rsx.ondigitalocean.app"):
        self.base_url = base_url
        self.session = None
        self.test_results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "adversarial_tests": {},
            "defense_effectiveness": {},
            "vulnerability_assessment": "pending"
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={"User-Agent": "TradingAgents-Adversarial-Tester/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def test_cache_penetration_attack(self) -> Dict[str, Any]:
        """
        Test cache penetration attack scenario
        GOOGLE's Cache Penetration concern validation
        """
        logger.info("🚨 Testing Cache Penetration Attack...")
        
        test_results = {
            "test_name": "Cache Penetration Attack",
            "status": "pending",
            "attack_success": False,
            "system_response": [],
            "performance_degradation": 0.0
        }
        
        try:
            # Generate random, non-existent stock symbols to bypass cache
            fake_symbols = [
                ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) + '.TW'
                for _ in range(50)
            ]
            
            baseline_times = []
            attack_times = []
            
            # Baseline performance with valid symbols
            logger.info("Measuring baseline performance...")
            valid_symbols = ["2330.TW", "2317.TW", "2454.TW"]
            
            for symbol in valid_symbols[:5]:
                start_time = time.time()
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/v1/ai-analysis/cached",
                        json={
                            "stock_symbol": symbol,
                            "user_tier": "diamond",
                            "force_refresh": False
                        }
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        baseline_times.append(response_time)
                        
                        if response.status == 200:
                            data = await response.json()
                            logger.debug(f"Baseline: {symbol} - {response_time:.1f}ms")
                except Exception as e:
                    logger.error(f"Baseline test error: {e}")
            
            # Launch penetration attack
            logger.info("Launching penetration attack with fake symbols...")
            
            for i, fake_symbol in enumerate(fake_symbols[:20]):
                start_time = time.time()
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/v1/ai-analysis/cached",
                        json={
                            "stock_symbol": fake_symbol,
                            "user_tier": "diamond",
                            "force_refresh": False
                        }
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        attack_times.append(response_time)
                        
                        response_data = await response.json()
                        test_results["system_response"].append({
                            "fake_symbol": fake_symbol,
                            "status_code": response.status,
                            "response_time_ms": response_time,
                            "blocked": "error" in response_data or "not available" in str(response_data).lower()
                        })
                        
                        logger.debug(f"Attack {i+1}: {fake_symbol} - {response_time:.1f}ms - Status: {response.status}")
                        
                except Exception as e:
                    logger.error(f"Attack request error: {e}")
                    attack_times.append(30000)  # Assume timeout
            
            # Analyze results
            if baseline_times and attack_times:
                avg_baseline = statistics.mean(baseline_times)
                avg_attack = statistics.mean(attack_times)
                
                performance_degradation = ((avg_attack - avg_baseline) / avg_baseline) * 100
                
                blocked_requests = sum(1 for r in test_results["system_response"] if r["blocked"])
                total_requests = len(test_results["system_response"])
                block_rate = (blocked_requests / total_requests) * 100 if total_requests > 0 else 0
                
                test_results.update({
                    "status": "completed",
                    "attack_success": performance_degradation > 200,  # >200% degradation = successful attack
                    "baseline_avg_ms": round(avg_baseline, 1),
                    "attack_avg_ms": round(avg_attack, 1),
                    "performance_degradation_percent": round(performance_degradation, 1),
                    "blocked_requests": blocked_requests,
                    "total_attack_requests": total_requests,
                    "block_rate_percent": round(block_rate, 1)
                })
                
                if block_rate > 80:
                    logger.info(f"✅ Penetration attack BLOCKED: {block_rate:.1f}% blocked")
                else:
                    logger.warning(f"⚠️ Penetration attack partially successful: {block_rate:.1f}% blocked")
            
        except Exception as e:
            test_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Penetration attack test failed: {e}")
        
        return test_results
    
    async def test_cache_avalanche_scenario(self) -> Dict[str, Any]:
        """
        Test cache avalanche scenario
        GOOGLE's Cache Avalanche concern validation
        """
        logger.info("🌊 Testing Cache Avalanche Scenario...")
        
        test_results = {
            "test_name": "Cache Avalanche Scenario", 
            "status": "pending",
            "avalanche_triggered": False,
            "concurrent_requests": 0,
            "system_stability": "unknown"
        }
        
        try:
            # Simulate cache avalanche by making many requests simultaneously
            # for the same resource after clearing cache
            
            symbol = "2330.TW"
            concurrent_requests = 25
            
            logger.info(f"Launching {concurrent_requests} concurrent requests for {symbol}...")
            
            tasks = []
            start_time = time.time()
            
            # Create concurrent requests
            for i in range(concurrent_requests):
                task = asyncio.create_task(self._make_avalanche_request(symbol, i))
                tasks.append(task)
            
            # Wait for all requests to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            total_time = (time.time() - start_time) * 1000
            
            # Analyze results
            successful_requests = [r for r in results if isinstance(r, dict) and not isinstance(r, Exception)]
            failed_requests = [r for r in results if isinstance(r, Exception)]
            
            response_times = [r.get("response_time_ms", 0) for r in successful_requests]
            cache_hits = sum(1 for r in successful_requests if r.get("cache_hit", False))
            
            test_results.update({
                "status": "completed",
                "concurrent_requests": concurrent_requests,
                "successful_requests": len(successful_requests),
                "failed_requests": len(failed_requests),
                "total_time_ms": round(total_time, 1),
                "average_response_time_ms": round(statistics.mean(response_times), 1) if response_times else 0,
                "cache_hit_rate_percent": round((cache_hits / len(successful_requests)) * 100, 1) if successful_requests else 0,
                "system_stability": "stable" if len(failed_requests) < concurrent_requests * 0.1 else "unstable"
            })
            
            # Determine if avalanche was successfully prevented
            avalanche_prevented = (
                test_results["system_stability"] == "stable" and
                test_results["cache_hit_rate_percent"] > 50 and
                len(failed_requests) < concurrent_requests * 0.2
            )
            
            test_results["avalanche_triggered"] = not avalanche_prevented
            
            if avalanche_prevented:
                logger.info(f"✅ Cache avalanche PREVENTED: {test_results['cache_hit_rate_percent']:.1f}% hit rate")
            else:
                logger.warning(f"⚠️ Cache avalanche may have occurred: system instability detected")
            
        except Exception as e:
            test_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Cache avalanche test failed: {e}")
        
        return test_results
    
    async def _make_avalanche_request(self, symbol: str, request_id: int) -> Dict[str, Any]:
        """Make a single request for avalanche testing"""
        start_time = time.time()
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/ai-analysis/cached",
                json={
                    "stock_symbol": symbol,
                    "user_tier": "gold",
                    "force_refresh": False
                }
            ) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    cache_metadata = data.get("cache_metadata", {})
                    
                    return {
                        "request_id": request_id,
                        "response_time_ms": response_time,
                        "cache_hit": cache_metadata.get("cache_hit", False),
                        "status_code": response.status,
                        "success": True
                    }
                else:
                    return {
                        "request_id": request_id,
                        "response_time_ms": response_time,
                        "status_code": response.status,
                        "success": False
                    }
                    
        except Exception as e:
            return {
                "request_id": request_id,
                "response_time_ms": (time.time() - start_time) * 1000,
                "error": str(e),
                "success": False
            }
    
    async def test_rate_limiting_defense(self) -> Dict[str, Any]:
        """Test rate limiting and IP-based attack detection"""
        logger.info("🚦 Testing Rate Limiting Defense...")
        
        test_results = {
            "test_name": "Rate Limiting Defense",
            "status": "pending",
            "rate_limit_triggered": False,
            "requests_blocked": 0
        }
        
        try:
            # Simulate rapid requests from same source
            rapid_requests = 100
            blocked_count = 0
            successful_count = 0
            
            logger.info(f"Making {rapid_requests} rapid requests...")
            
            for i in range(rapid_requests):
                try:
                    async with self.session.post(
                        f"{self.base_url}/api/v1/ai-analysis/cached",
                        json={
                            "stock_symbol": "2330.TW",
                            "user_tier": "free",
                            "force_refresh": False
                        },
                        headers={"X-Real-IP": "192.168.1.100"}  # Simulate same IP
                    ) as response:
                        
                        if response.status == 429:  # Rate limited
                            blocked_count += 1
                        elif response.status == 200:
                            successful_count += 1
                        
                        if i % 20 == 0:
                            logger.debug(f"Rapid request {i}: Status {response.status}")
                            
                except Exception as e:
                    logger.debug(f"Rapid request {i} failed: {e}")
                    blocked_count += 1
                
                # Small delay to simulate realistic attack
                await asyncio.sleep(0.01)
            
            test_results.update({
                "status": "completed",
                "total_requests": rapid_requests,
                "requests_blocked": blocked_count,
                "requests_successful": successful_count,
                "block_rate_percent": round((blocked_count / rapid_requests) * 100, 1),
                "rate_limit_triggered": blocked_count > rapid_requests * 0.2
            })
            
            if test_results["block_rate_percent"] > 30:
                logger.info(f"✅ Rate limiting ACTIVE: {test_results['block_rate_percent']:.1f}% blocked")
            else:
                logger.warning(f"⚠️ Rate limiting may be insufficient: {test_results['block_rate_percent']:.1f}% blocked")
                
        except Exception as e:
            test_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Rate limiting test failed: {e}")
        
        return test_results
    
    async def test_defense_metrics_endpoint(self) -> Dict[str, Any]:
        """Test defense metrics endpoint functionality"""
        logger.info("📊 Testing Defense Metrics Endpoint...")
        
        test_results = {
            "test_name": "Defense Metrics Endpoint",
            "status": "pending",
            "endpoint_accessible": False,
            "metrics_valid": False
        }
        
        try:
            async with self.session.get(f"{self.base_url}/api/v1/cache/defense-metrics") as response:
                if response.status == 200:
                    metrics_data = await response.json()
                    
                    # Validate expected metrics structure
                    expected_sections = ["cache_performance", "defense_effectiveness", "system_health"]
                    sections_present = all(section in metrics_data for section in expected_sections)
                    
                    test_results.update({
                        "status": "completed",
                        "endpoint_accessible": True,
                        "metrics_valid": sections_present,
                        "metrics_data": metrics_data,
                        "response_time_ms": response.headers.get("X-Response-Time", "unknown")
                    })
                    
                    if sections_present:
                        logger.info("✅ Defense metrics endpoint is functional and valid")
                    else:
                        logger.warning("⚠️ Defense metrics endpoint missing expected data sections")
                        
                elif response.status == 404:
                    test_results.update({
                        "status": "completed",
                        "endpoint_accessible": False,
                        "error": "Defense metrics endpoint not implemented"
                    })
                    logger.warning("⚠️ Defense metrics endpoint not found (404)")
                    
                else:
                    test_results.update({
                        "status": "completed",
                        "endpoint_accessible": False,
                        "error": f"Unexpected status code: {response.status}"
                    })
                    
        except Exception as e:
            test_results.update({
                "status": "error",
                "error": str(e)
            })
            logger.error(f"Defense metrics test failed: {e}")
        
        return test_results
    
    async def run_comprehensive_adversarial_tests(self) -> Dict[str, Any]:
        """Run all adversarial tests"""
        logger.info("🎯 Starting Comprehensive Adversarial Testing Suite...")
        logger.info(f"Target system: {self.base_url}")
        
        # Define all adversarial tests
        adversarial_tests = [
            ("cache_penetration_attack", self.test_cache_penetration_attack),
            ("cache_avalanche_scenario", self.test_cache_avalanche_scenario),
            ("rate_limiting_defense", self.test_rate_limiting_defense),
            ("defense_metrics_endpoint", self.test_defense_metrics_endpoint)
        ]
        
        for test_name, test_func in adversarial_tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"Running {test_name} test...")
            
            try:
                result = await test_func()
                self.test_results["adversarial_tests"][test_name] = result
            except Exception as e:
                logger.error(f"Test {test_name} failed with error: {e}")
                self.test_results["adversarial_tests"][test_name] = {
                    "test_name": test_name,
                    "status": "error",
                    "error": str(e)
                }
        
        # Calculate overall defense effectiveness
        total_tests = len(self.test_results["adversarial_tests"])
        passed_tests = sum(1 for test in self.test_results["adversarial_tests"].values()
                          if test.get("status") == "completed" and not test.get("attack_success", True))
        
        defense_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Determine vulnerability assessment
        if defense_score >= 90:
            vulnerability_level = "LOW"
        elif defense_score >= 70:
            vulnerability_level = "MEDIUM"
        else:
            vulnerability_level = "HIGH"
        
        self.test_results.update({
            "defense_effectiveness": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "defense_score_percent": round(defense_score, 1),
                "vulnerability_level": vulnerability_level
            },
            "vulnerability_assessment": vulnerability_level
        })
        
        return self.test_results
    
    def generate_security_report(self) -> str:
        """Generate comprehensive security assessment report"""
        report_lines = [
            "TRADINGAGENTS ADVERSARIAL SECURITY ASSESSMENT",
            "=" * 60,
            f"Generated: {self.test_results['timestamp']}",
            f"Target System: {self.test_results['base_url']}",
            "",
            "VULNERABILITY ASSESSMENT:",
            "-" * 30,
            f"Overall Vulnerability Level: {self.test_results['vulnerability_assessment']}",
            f"Defense Score: {self.test_results['defense_effectiveness']['defense_score_percent']}%",
            f"Tests Passed: {self.test_results['defense_effectiveness']['passed_tests']}/{self.test_results['defense_effectiveness']['total_tests']}",
            "",
            "DETAILED TEST RESULTS:",
            "-" * 30
        ]
        
        for test_name, test_data in self.test_results["adversarial_tests"].items():
            status = test_data.get("status", "unknown").upper()
            
            if test_name == "cache_penetration_attack":
                block_rate = test_data.get("block_rate_percent", 0)
                report_lines.append(f"Cache Penetration Attack: {status} (Block Rate: {block_rate}%)")
                
            elif test_name == "cache_avalanche_scenario":
                stability = test_data.get("system_stability", "unknown")
                hit_rate = test_data.get("cache_hit_rate_percent", 0)
                report_lines.append(f"Cache Avalanche Test: {status} (Stability: {stability}, Hit Rate: {hit_rate}%)")
                
            elif test_name == "rate_limiting_defense":
                rate_limit = "ACTIVE" if test_data.get("rate_limit_triggered", False) else "INACTIVE"
                block_rate = test_data.get("block_rate_percent", 0)
                report_lines.append(f"Rate Limiting Defense: {status} ({rate_limit}, Block Rate: {block_rate}%)")
                
            elif test_name == "defense_metrics_endpoint":
                accessible = "ACCESSIBLE" if test_data.get("endpoint_accessible", False) else "INACCESSIBLE"
                report_lines.append(f"Defense Metrics Endpoint: {status} ({accessible})")
        
        report_lines.extend([
            "",
            "SECURITY RECOMMENDATIONS:",
            "-" * 30
        ])
        
        if self.test_results["vulnerability_assessment"] == "HIGH":
            report_lines.extend([
                "🚨 CRITICAL: High vulnerability level detected",
                "  - Implement stronger rate limiting",
                "  - Enhance cache penetration defenses", 
                "  - Add circuit breaker protection",
                "  - Monitor for attack patterns"
            ])
        elif self.test_results["vulnerability_assessment"] == "MEDIUM":
            report_lines.extend([
                "⚠️ WARNING: Medium vulnerability level",
                "  - Fine-tune defense parameters",
                "  - Add monitoring alerts",
                "  - Consider additional security layers"
            ])
        else:
            report_lines.extend([
                "✅ GOOD: Low vulnerability level",
                "  - Maintain current defense levels",
                "  - Continue monitoring and testing",
                "  - Consider advanced threat detection"
            ])
        
        report_lines.extend([
            "",
            "=" * 60,
            "ADVERSARIAL TESTING COMPLETE"
        ])
        
        return "\n".join(report_lines)


async def main():
    """Main execution function"""
    try:
        async with AdversarialTestSuite() as tester:
            # Run comprehensive adversarial tests
            results = await tester.run_comprehensive_adversarial_tests()
            
            # Generate and display report
            report = tester.generate_security_report()
            print("\n" + report)
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"adversarial_test_results_{timestamp}.json"
            
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"\nDetailed results saved to: {results_file}")
            
            # Return exit code based on vulnerability level
            vulnerability = results['vulnerability_assessment']
            return 0 if vulnerability == 'LOW' else 1 if vulnerability == 'MEDIUM' else 2
            
    except Exception as e:
        logger.error(f"Adversarial testing suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())