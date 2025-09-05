"""
Global CDN Deployment System
Handles worldwide content distribution for low-latency market data delivery
Task 4.2.4: 全球CDN部署

Features:
- Multi-region CDN deployment across US, Asia, Europe
- Real-time market data caching and distribution
- Edge computing for financial calculations
- Geographic load balancing
- Content optimization for financial data
- Performance monitoring and analytics
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
import logging
import os
from pathlib import Path
from abc import ABC, abstractmethod
import aiohttp
import os
from pathlib import Path

class CDNRegion(Enum):
    US_EAST = "us-east-1"
    US_WEST = "us-west-1"
    ASIA_PACIFIC = "ap-southeast-1"
    ASIA_NORTHEAST = "ap-northeast-1"
    EUROPE_WEST = "eu-west-1"
    EUROPE_CENTRAL = "eu-central-1"

class ContentType(Enum):
    MARKET_DATA = "market_data"
    STATIC_ASSETS = "static_assets"
    API_RESPONSES = "api_responses"
    ANALYTICS_DATA = "analytics_data"
    NEWS_CONTENT = "news_content"

class CacheStrategy(Enum):
    NO_CACHE = "no-cache"
    SHORT_TERM = "short-term"  # 1-5 minutes
    MEDIUM_TERM = "medium-term"  # 5-60 minutes
    LONG_TERM = "long-term"  # 1+ hours
    STATIC = "static"  # Days/weeks

@dataclass
class EdgeLocation:
    """CDN edge location configuration"""
    id: str
    region: CDNRegion
    city: str
    country: str
    latitude: float
    longitude: float
    capacity_gbps: float
    status: str = "active"
    provider: str = "cloudflare"
    
@dataclass
class CacheRule:
    """Content caching rule"""
    content_type: ContentType
    cache_strategy: CacheStrategy
    ttl_seconds: int
    compression_enabled: bool = True
    edge_side_includes: bool = False
    vary_headers: List[str] = field(default_factory=list)

@dataclass
class PerformanceMetrics:
    """CDN performance metrics"""
    region: CDNRegion
    timestamp: datetime
    avg_response_time_ms: float
    cache_hit_ratio: float
    bandwidth_utilization_percent: float
    error_rate_percent: float
    requests_per_second: float
    data_transferred_gb: float

class EdgeComputeManager:
    """Manages edge computing for financial calculations"""
    
    def __init__(self):
        self.edge_functions = {}
        
    def register_edge_function(self, function_name: str, code: str, regions: List[CDNRegion]):
        """Register edge computing function"""
        
        self.edge_functions[function_name] = {
            "code": code,
            "regions": regions,
            "created_at": datetime.now(timezone.utc),
            "version": "1.0"
        }
    
    async def execute_edge_function(
        self, 
        function_name: str, 
        region: CDNRegion, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute function at edge location"""
        
        if function_name not in self.edge_functions:
            raise ValueError(f"Edge function '{function_name}' not found")
        
        function_config = self.edge_functions[function_name]
        
        # Mock execution - in practice would deploy to CDN edge
        if function_name == "calculate_moving_average":
            prices = parameters.get("prices", [])
            window = parameters.get("window", 20)
            
            if len(prices) >= window:
                ma = sum(prices[-window:]) / window
                return {
                    "moving_average": ma,
                    "calculated_at": datetime.now(timezone.utc).isoformat(),
                    "region": region.value,
                    "execution_time_ms": 5
                }
        
        elif function_name == "format_market_data":
            data = parameters.get("data", {})
            format_type = parameters.get("format", "json")
            
            if format_type == "compact":
                # Compress market data for mobile clients
                compact_data = {
                    "s": data.get("symbol", ""),
                    "p": data.get("price", 0),
                    "c": data.get("change", 0),
                    "v": data.get("volume", 0),
                    "t": datetime.now(timezone.utc).isoformat()
                }
                return compact_data
        
        return {"error": "Function execution failed"}
    
    def get_edge_function_stats(self) -> Dict[str, Any]:
        """Get edge function statistics"""
        
        return {
            "total_functions": len(self.edge_functions),
            "functions": [
                {
                    "name": name,
                    "regions": [r.value for r in config["regions"]],
                    "version": config["version"],
                    "created": config["created_at"].isoformat()
                }
                for name, config in self.edge_functions.items()
            ]
        }

class CDNProvider(ABC):
    """Abstract CDN provider interface"""
    
    @abstractmethod
    async def deploy_content(self, content_path: str, content_data: bytes, regions: List[CDNRegion]) -> bool:
        pass
    
    @abstractmethod
    async def purge_cache(self, content_path: str, regions: Optional[List[CDNRegion]] = None) -> bool:
        pass
    
    @abstractmethod
    async def get_performance_metrics(self, region: CDNRegion) -> PerformanceMetrics:
        pass

class CloudflareCDN(CDNProvider):
    """Cloudflare CDN implementation"""
    
    def __init__(self, api_token: str = "mock_token"):
        self.api_token = api_token
        self.base_url = "https://api.cloudflare.com/client/v4"
        
    async def deploy_content(self, content_path: str, content_data: bytes, regions: List[CDNRegion]) -> bool:
        """Deploy content to Cloudflare CDN"""
        
        # Mock deployment
        await asyncio.sleep(0.1)  # Simulate API call
        
        return True
    
    async def purge_cache(self, content_path: str, regions: Optional[List[CDNRegion]] = None) -> bool:
        """Purge cache for specific content"""
        
        # Mock cache purge
        await asyncio.sleep(0.05)
        
        return True
    
    async def get_performance_metrics(self, region: CDNRegion) -> PerformanceMetrics:
        """Get CDN performance metrics"""
        
        # Mock metrics
        base_latency = {
            CDNRegion.US_EAST: 20,
            CDNRegion.US_WEST: 25,
            CDNRegion.ASIA_PACIFIC: 30,
            CDNRegion.ASIA_NORTHEAST: 15,
            CDNRegion.EUROPE_WEST: 35,
            CDNRegion.EUROPE_CENTRAL: 28
        }
        
        return PerformanceMetrics(
            region=region,
            timestamp=datetime.now(timezone.utc),
            avg_response_time_ms=base_latency.get(region, 30),
            cache_hit_ratio=0.92,
            bandwidth_utilization_percent=65.0,
            error_rate_percent=0.02,
            requests_per_second=15000,
            data_transferred_gb=2.5
        )

class AWScloudfrontCDN(CDNProvider):
    """AWS CloudFront CDN implementation"""
    
    def __init__(self, access_key: str = "mock_key"):
        self.access_key = access_key
        
    async def deploy_content(self, content_path: str, content_data: bytes, regions: List[CDNRegion]) -> bool:
        """Deploy content to AWS CloudFront"""
        
        await asyncio.sleep(0.15)  # Simulate slower deployment
        return True
    
    async def purge_cache(self, content_path: str, regions: Optional[List[CDNRegion]] = None) -> bool:
        """Invalidate CloudFront cache"""
        
        await asyncio.sleep(0.08)
        return True
    
    async def get_performance_metrics(self, region: CDNRegion) -> PerformanceMetrics:
        """Get CloudFront performance metrics"""
        
        base_latency = {
            CDNRegion.US_EAST: 18,
            CDNRegion.US_WEST: 22,
            CDNRegion.ASIA_PACIFIC: 35,
            CDNRegion.ASIA_NORTHEAST: 18,
            CDNRegion.EUROPE_WEST: 32,
            CDNRegion.EUROPE_CENTRAL: 25
        }
        
        return PerformanceMetrics(
            region=region,
            timestamp=datetime.now(timezone.utc),
            avg_response_time_ms=base_latency.get(region, 28),
            cache_hit_ratio=0.89,
            bandwidth_utilization_percent=58.0,
            error_rate_percent=0.01,
            requests_per_second=12000,
            data_transferred_gb=3.1
        )

class GlobalCDNDeploymentSystem:
    """Main global CDN deployment and management system"""
    
    def __init__(self):
        self.edge_locations = self._initialize_edge_locations()
        self.cache_rules = self._initialize_cache_rules()
        self.providers = {
            "cloudflare": CloudflareCDN(),
            "aws": AWScloudfrontCDN()
        }
        self.edge_compute = EdgeComputeManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize edge computing functions
        self._setup_edge_functions()
    
    def _initialize_edge_locations(self) -> List[EdgeLocation]:
        """Initialize global edge locations"""
        
        return [
            EdgeLocation(
                id="nyc-01",
                region=CDNRegion.US_EAST,
                city="New York",
                country="United States",
                latitude=40.7128,
                longitude=-74.0060,
                capacity_gbps=100.0,
                provider="cloudflare"
            ),
            EdgeLocation(
                id="sf-01",
                region=CDNRegion.US_WEST,
                city="San Francisco",
                country="United States",
                latitude=37.7749,
                longitude=-122.4194,
                capacity_gbps=80.0,
                provider="cloudflare"
            ),
            EdgeLocation(
                id="sg-01",
                region=CDNRegion.ASIA_PACIFIC,
                city="Singapore",
                country="Singapore",
                latitude=1.3521,
                longitude=103.8198,
                capacity_gbps=60.0,
                provider="cloudflare"
            ),
            EdgeLocation(
                id="tok-01",
                region=CDNRegion.ASIA_NORTHEAST,
                city="Tokyo",
                country="Japan",
                latitude=35.6762,
                longitude=139.6503,
                capacity_gbps=90.0,
                provider="aws"
            ),
            EdgeLocation(
                id="lon-01",
                region=CDNRegion.EUROPE_WEST,
                city="London",
                country="United Kingdom",
                latitude=51.5074,
                longitude=-0.1278,
                capacity_gbps=70.0,
                provider="cloudflare"
            ),
            EdgeLocation(
                id="fra-01",
                region=CDNRegion.EUROPE_CENTRAL,
                city="Frankfurt",
                country="Germany",
                latitude=50.1109,
                longitude=8.6821,
                capacity_gbps=75.0,
                provider="aws"
            )
        ]
    
    def _initialize_cache_rules(self) -> Dict[ContentType, CacheRule]:
        """Initialize content caching rules"""
        
        return {
            ContentType.MARKET_DATA: CacheRule(
                content_type=ContentType.MARKET_DATA,
                cache_strategy=CacheStrategy.SHORT_TERM,
                ttl_seconds=60,  # 1 minute for real-time data
                compression_enabled=True,
                vary_headers=["Accept-Encoding", "User-Agent"]
            ),
            ContentType.STATIC_ASSETS: CacheRule(
                content_type=ContentType.STATIC_ASSETS,
                cache_strategy=CacheStrategy.STATIC,
                ttl_seconds=86400 * 7,  # 1 week
                compression_enabled=True
            ),
            ContentType.API_RESPONSES: CacheRule(
                content_type=ContentType.API_RESPONSES,
                cache_strategy=CacheStrategy.MEDIUM_TERM,
                ttl_seconds=300,  # 5 minutes
                compression_enabled=True,
                edge_side_includes=True
            ),
            ContentType.ANALYTICS_DATA: CacheRule(
                content_type=ContentType.ANALYTICS_DATA,
                cache_strategy=CacheStrategy.LONG_TERM,
                ttl_seconds=3600,  # 1 hour
                compression_enabled=True
            ),
            ContentType.NEWS_CONTENT: CacheRule(
                content_type=ContentType.NEWS_CONTENT,
                cache_strategy=CacheStrategy.MEDIUM_TERM,
                ttl_seconds=900,  # 15 minutes
                compression_enabled=True
            )
        }
    
    def _setup_edge_functions(self):
        """Setup edge computing functions"""
        
        # Moving average calculation
        ma_code = """
        async function calculateMovingAverage(prices, window) {
            if (prices.length < window) return null;
            const slice = prices.slice(-window);
            return slice.reduce((sum, price) => sum + price, 0) / window;
        }
        """
        
        self.edge_compute.register_edge_function(
            "calculate_moving_average",
            ma_code,
            list(CDNRegion)
        )
        
        # Market data formatting
        format_code = """
        async function formatMarketData(data, format) {
            if (format === 'compact') {
                return {
                    s: data.symbol,
                    p: data.price,
                    c: data.change,
                    v: data.volume,
                    t: new Date().toISOString()
                };
            }
            return data;
        }
        """
        
        self.edge_compute.register_edge_function(
            "format_market_data",
            format_code,
            list(CDNRegion)
        )
    
    async def deploy_global_content(
        self, 
        content_path: str, 
        content_data: bytes, 
        content_type: ContentType,
        target_regions: Optional[List[CDNRegion]] = None
    ) -> Dict[str, Any]:
        """Deploy content globally across CDN network"""
        
        if target_regions is None:
            target_regions = list(CDNRegion)
        
        deployment_results = {}
        cache_rule = self.cache_rules.get(content_type)
        
        # Group regions by CDN provider
        provider_regions = {}
        for location in self.edge_locations:
            if location.region in target_regions:
                if location.provider not in provider_regions:
                    provider_regions[location.provider] = []
                provider_regions[location.provider].append(location.region)
        
        # Deploy to each provider
        for provider_name, regions in provider_regions.items():
            if provider_name in self.providers:
                try:
                    success = await self.providers[provider_name].deploy_content(
                        content_path, content_data, regions
                    )
                    deployment_results[provider_name] = {
                        "success": success,
                        "regions": [r.value for r in regions],
                        "cache_ttl": cache_rule.ttl_seconds if cache_rule else 3600
                    }
                except Exception as e:
                    self.logger.error(f"Deployment failed for {provider_name}: {str(e)}")
                    deployment_results[provider_name] = {
                        "success": False,
                        "error": str(e)
                    }
        
        return {
            "content_path": content_path,
            "content_type": content_type.value,
            "deployment_timestamp": datetime.now(timezone.utc).isoformat(),
            "target_regions": [r.value for r in target_regions],
            "deployment_results": deployment_results,
            "total_size_bytes": len(content_data)
        }
    
    async def purge_global_cache(
        self, 
        content_path: str, 
        regions: Optional[List[CDNRegion]] = None
    ) -> Dict[str, Any]:
        """Purge cache globally or for specific regions"""
        
        if regions is None:
            regions = list(CDNRegion)
        
        purge_results = {}
        
        # Group by provider
        provider_regions = {}
        for location in self.edge_locations:
            if location.region in regions:
                if location.provider not in provider_regions:
                    provider_regions[location.provider] = []
                provider_regions[location.provider].append(location.region)
        
        # Purge from each provider
        tasks = []
        for provider_name, provider_regions_list in provider_regions.items():
            if provider_name in self.providers:
                task = self._purge_provider_cache(provider_name, content_path, provider_regions_list)
                tasks.append((provider_name, task))
        
        # Execute purge tasks concurrently
        for provider_name, task in tasks:
            try:
                success = await task
                purge_results[provider_name] = {
                    "success": success,
                    "regions": [r.value for r in provider_regions.get(provider_name, [])]
                }
            except Exception as e:
                purge_results[provider_name] = {
                    "success": False,
                    "error": str(e)
                }
        
        return {
            "content_path": content_path,
            "purge_timestamp": datetime.now(timezone.utc).isoformat(),
            "target_regions": [r.value for r in regions],
            "purge_results": purge_results
        }
    
    async def _purge_provider_cache(
        self, 
        provider_name: str, 
        content_path: str, 
        regions: List[CDNRegion]
    ) -> bool:
        """Purge cache for specific provider"""
        
        provider = self.providers.get(provider_name)
        if provider:
            return await provider.purge_cache(content_path, regions)
        return False
    
    async def get_global_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from all regions"""
        
        metrics = {}
        tasks = []
        
        # Collect metrics from all regions
        for location in self.edge_locations:
            provider = self.providers.get(location.provider)
            if provider:
                task = provider.get_performance_metrics(location.region)
                tasks.append((location.region, task))
        
        # Execute metric collection concurrently
        for region, task in tasks:
            try:
                metric = await task
                metrics[region.value] = {
                    "avg_response_time_ms": metric.avg_response_time_ms,
                    "cache_hit_ratio": metric.cache_hit_ratio,
                    "bandwidth_utilization_percent": metric.bandwidth_utilization_percent,
                    "error_rate_percent": metric.error_rate_percent,
                    "requests_per_second": metric.requests_per_second,
                    "data_transferred_gb": metric.data_transferred_gb,
                    "timestamp": metric.timestamp.isoformat()
                }
            except Exception as e:
                self.logger.error(f"Failed to get metrics for {region.value}: {str(e)}")
                metrics[region.value] = {"error": str(e)}
        
        # Calculate global statistics
        response_times = [m["avg_response_time_ms"] for m in metrics.values() if "avg_response_time_ms" in m]
        cache_hit_ratios = [m["cache_hit_ratio"] for m in metrics.values() if "cache_hit_ratio" in m]
        
        global_stats = {
            "global_avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
            "global_cache_hit_ratio": sum(cache_hit_ratios) / len(cache_hit_ratios) if cache_hit_ratios else 0,
            "total_requests_per_second": sum(m.get("requests_per_second", 0) for m in metrics.values()),
            "total_data_transferred_gb": sum(m.get("data_transferred_gb", 0) for m in metrics.values()),
            "active_regions": len([m for m in metrics.values() if "error" not in m])
        }
        
        return {
            "collection_timestamp": datetime.now(timezone.utc).isoformat(),
            "regional_metrics": metrics,
            "global_statistics": global_stats
        }
    
    def find_optimal_regions_for_user(self, user_latitude: float, user_longitude: float) -> List[EdgeLocation]:
        """Find optimal CDN regions based on user location"""
        
        def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """Calculate great circle distance between two points"""
            from math import radians, cos, sin, asin, sqrt
            
            # Convert to radians
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            # Haversine formula
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Earth's radius in kilometers
            
            return c * r
        
        # Calculate distances to all edge locations
        distances = []
        for location in self.edge_locations:
            distance = calculate_distance(
                user_latitude, user_longitude,
                location.latitude, location.longitude
            )
            distances.append((distance, location))
        
        # Sort by distance and return top 3 closest
        distances.sort(key=lambda x: x[0])
        return [location for distance, location in distances[:3]]
    
    async def optimize_content_distribution(
        self, 
        content_type: ContentType, 
        usage_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize content distribution based on usage patterns"""
        
        optimization_results = {
            "content_type": content_type.value,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "current_cache_rule": self.cache_rules[content_type].__dict__ if content_type in self.cache_rules else None,
            "recommendations": []
        }
        
        # Analyze usage patterns
        if "geographic_distribution" in usage_patterns:
            geo_data = usage_patterns["geographic_distribution"]
            high_usage_regions = [region for region, usage in geo_data.items() if usage > 0.15]
            
            optimization_results["recommendations"].append({
                "type": "regional_prioritization",
                "description": f"Prioritize deployment in high-usage regions: {', '.join(high_usage_regions)}",
                "impact": "Reduce latency by 20-30% for 70% of users"
            })
        
        if "peak_hours" in usage_patterns:
            peak_hours = usage_patterns["peak_hours"]
            optimization_results["recommendations"].append({
                "type": "pre-warming",
                "description": f"Pre-warm cache before peak hours ({', '.join(map(str, peak_hours))})",
                "impact": "Reduce cache miss rate during peak times"
            })
        
        if "request_frequency" in usage_patterns:
            freq = usage_patterns["request_frequency"]
            if freq > 1000:  # High frequency
                optimization_results["recommendations"].append({
                    "type": "cache_optimization",
                    "description": "Increase cache TTL due to high request frequency",
                    "suggested_ttl": min(self.cache_rules[content_type].ttl_seconds * 2, 3600)
                })
        
        return optimization_results
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Get overall CDN deployment status"""
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "edge_locations": [
                {
                    "id": loc.id,
                    "region": loc.region.value,
                    "city": loc.city,
                    "country": loc.country,
                    "provider": loc.provider,
                    "status": loc.status,
                    "capacity_gbps": loc.capacity_gbps
                }
                for loc in self.edge_locations
            ],
            "total_locations": len(self.edge_locations),
            "active_locations": len([loc for loc in self.edge_locations if loc.status == "active"]),
            "total_capacity_gbps": sum(loc.capacity_gbps for loc in self.edge_locations),
            "providers": list(self.providers.keys()),
            "cache_rules": {
                content_type.value: {
                    "strategy": rule.cache_strategy.value,
                    "ttl_seconds": rule.ttl_seconds,
                    "compression": rule.compression_enabled
                }
                for content_type, rule in self.cache_rules.items()
            },
            "edge_functions": self.edge_compute.get_edge_function_stats()
        }

# Example usage and testing

# 自動檢測和切換到 TradingAgents 目錄
def ensure_tradingagents_directory():
    """確保當前工作目錄在 TradingAgents/ 下，以正確訪問配置文件"""
    current_dir = Path.cwd()
    
    # 如果當前目錄是 TradingAgents 的父目錄，切換到 TradingAgents
    if (current_dir / 'TradingAgents').exists():
        os.chdir(current_dir / 'TradingAgents')
        print(f"[DIR] 自動切換工作目錄到: {Path.cwd()}")
    
    # 驗證必要的目錄存在
    required_dirs = ['configs', 'training', 'tradingagents']
    missing_dirs = [d for d in required_dirs if not Path(d).exists()]
    
    if missing_dirs:
        raise FileNotFoundError(f"缺少必要目錄: {missing_dirs}. 請確保從 TradingAgents/ 目錄執行此腳本")

# 目錄檢查函數已準備好，但不在模組導入時自動執行
# 只在需要時手動調用 ensure_tradingagents_directory()

if __name__ == "__main__":
    async def test_global_cdn_deployment():
        cdn_system = GlobalCDNDeploymentSystem()
        
        print("Testing Global CDN Deployment System...")
        
        # Test content deployment
        print("\\n1. Testing Global Content Deployment:")
        test_content = b'{"symbol": "AAPL", "price": 150.00, "change": 2.50}'
        
        deployment_result = await cdn_system.deploy_global_content(
            "/api/market-data/AAPL",
            test_content,
            ContentType.MARKET_DATA,
            [CDNRegion.US_EAST, CDNRegion.ASIA_PACIFIC, CDNRegion.EUROPE_WEST]
        )
        
        print(f"Deployed to {len(deployment_result['target_regions'])} regions")
        print(f"Content size: {deployment_result['total_size_bytes']} bytes")
        
        # Test performance metrics
        print("\\n2. Testing Performance Metrics Collection:")
        metrics = await cdn_system.get_global_performance_metrics()
        
        print(f"Active regions: {metrics['global_statistics']['active_regions']}")
        print(f"Global avg response time: {metrics['global_statistics']['global_avg_response_time_ms']:.1f}ms")
        print(f"Global cache hit ratio: {metrics['global_statistics']['global_cache_hit_ratio']:.2%}")
        
        # Test optimal region finding
        print("\\n3. Testing Optimal Region Selection:")
        # Tokyo coordinates (for testing)
        optimal_regions = cdn_system.find_optimal_regions_for_user(35.6762, 139.6503)
        
        print(f"Optimal regions for Tokyo user:")
        for i, region in enumerate(optimal_regions, 1):
            print(f"  {i}. {region.city}, {region.country} ({region.region.value})")
        
        # Test cache purge
        print("\\n4. Testing Global Cache Purge:")
        purge_result = await cdn_system.purge_global_cache(
            "/api/market-data/AAPL",
            [CDNRegion.US_EAST, CDNRegion.ASIA_PACIFIC]
        )
        
        successful_purges = sum(1 for result in purge_result['purge_results'].values() if result.get('success'))
        print(f"Cache purged successfully in {successful_purges} provider(s)")
        
        # Test edge computing
        print("\\n5. Testing Edge Computing:")
        edge_result = await cdn_system.edge_compute.execute_edge_function(
            "calculate_moving_average",
            CDNRegion.US_EAST,
            {"prices": [100, 102, 101, 103, 105, 104, 106], "window": 5}
        )
        
        if "moving_average" in edge_result:
            print(f"Moving average calculated at edge: {edge_result['moving_average']:.2f}")
            print(f"Execution time: {edge_result['execution_time_ms']}ms")
        
        # Get deployment status
        print("\\n6. Overall Deployment Status:")
        status = cdn_system.get_deployment_status()
        print(f"Total edge locations: {status['total_locations']}")
        print(f"Total capacity: {status['total_capacity_gbps']} Gbps")
        print(f"Providers: {', '.join(status['providers'])}")
        
        return status
    
    # Run test
    result = asyncio.run(test_global_cdn_deployment())
    print("\\nGlobal CDN Deployment System test completed successfully!")