"""
FinnHub API Client for International Stock Data

This module provides a comprehensive client for accessing FinnHub's financial data API,
supporting real-time and historical stock data, company profiles, news, and financial statements.

Features:
- Async HTTP client with session management
- Rate limiting and retry logic
- Error handling and logging
- Data normalization and validation
- Caching integration hooks
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import aiohttp
import json
from dataclasses import dataclass
from enum import Enum

# Configure logging
logger = logging.getLogger(__name__)


class FinnHubError(Exception):
    """Base exception for FinnHub API errors"""
    pass


class RateLimitError(FinnHubError):
    """Raised when API rate limit is exceeded"""
    pass


class AuthenticationError(FinnHubError):
    """Raised when API authentication fails"""
    pass


class DataNotFoundError(FinnHubError):
    """Raised when requested data is not found"""
    pass


@dataclass
class RateLimitInfo:
    """Rate limit information from API response headers"""
    limit: int
    remaining: int
    reset_time: int


class FinnHubAPIClient:
    """
    Async FinnHub API client with comprehensive error handling and rate limiting.
    
    This client provides access to FinnHub's financial data API with built-in
    rate limiting, retry logic, and error handling.
    """
    
    BASE_URL = "https://finnhub.io/api/v1"
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0  # Base delay in seconds
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize FinnHub API client.
        
        Args:
            api_key: FinnHub API key. If None, will try to get from environment
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or self._get_api_key_from_env()
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_info: Optional[RateLimitInfo] = None
        self._last_request_time = 0.0
        
        if not self.api_key:
            raise AuthenticationError("FinnHub API key is required")
    
    def _get_api_key_from_env(self) -> Optional[str]:
        """Get API key from environment variables"""
        return os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_TOKEN')
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'User-Agent': 'TradingAgents/1.0',
                    'Accept': 'application/json'
                }
            )
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full API URL"""
        return f"{self.BASE_URL}/{endpoint.lstrip('/')}"
    
    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, str]:
        """Prepare request parameters"""
        # Add API key to parameters
        params = params.copy()
        params['token'] = self.api_key
        
        # Convert all values to strings and filter None values
        return {k: str(v) for k, v in params.items() if v is not None}
    
    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Update rate limit information from response headers"""
        try:
            if 'X-Ratelimit-Limit' in headers:
                self.rate_limit_info = RateLimitInfo(
                    limit=int(headers.get('X-Ratelimit-Limit', 0)),
                    remaining=int(headers.get('X-Ratelimit-Remaining', 0)),
                    reset_time=int(headers.get('X-Ratelimit-Reset', 0))
                )
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse rate limit headers: {e}")
    
    async def _handle_rate_limiting(self):
        """Handle rate limiting with exponential backoff"""
        if self.rate_limit_info and self.rate_limit_info.remaining <= 1:
            current_time = time.time()
            if self.rate_limit_info.reset_time > current_time:
                sleep_time = self.rate_limit_info.reset_time - current_time + 1
                logger.warning(f"Rate limit reached, sleeping for {sleep_time} seconds")
                await asyncio.sleep(sleep_time)
        
        # Ensure minimum delay between requests
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:  # 100ms minimum delay
            await asyncio.sleep(0.1 - time_since_last)
        
        self._last_request_time = time.time()
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Make HTTP request to FinnHub API with error handling and retries.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
            retry_count: Current retry attempt
            
        Returns:
            JSON response data
            
        Raises:
            FinnHubError: For various API errors
        """
        await self._ensure_session()
        await self._handle_rate_limiting()
        
        url = self._build_url(endpoint)
        request_params = self._prepare_params(params or {})
        
        try:
            logger.debug(f"Making request to {endpoint} with params: {request_params}")
            
            async with self.session.get(url, params=request_params) as response:
                self._update_rate_limit_info(dict(response.headers))
                
                # Handle different HTTP status codes
                if response.status == 200:
                    data = await response.json()
                    logger.debug(f"Successful response from {endpoint}")
                    return data
                
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                
                elif response.status == 403:
                    raise AuthenticationError("API access forbidden")
                
                elif response.status == 404:
                    raise DataNotFoundError(f"Data not found for endpoint: {endpoint}")
                
                elif response.status == 429:
                    # Rate limit exceeded
                    if retry_count < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY * (2 ** retry_count)
                        logger.warning(f"Rate limit exceeded, retrying in {delay} seconds")
                        await asyncio.sleep(delay)
                        return await self._make_request(endpoint, params, retry_count + 1)
                    else:
                        raise RateLimitError("Rate limit exceeded, max retries reached")
                
                elif response.status >= 500:
                    # Server error - retry
                    if retry_count < self.MAX_RETRIES:
                        delay = self.RETRY_DELAY * (2 ** retry_count)
                        logger.warning(f"Server error {response.status}, retrying in {delay} seconds")
                        await asyncio.sleep(delay)
                        return await self._make_request(endpoint, params, retry_count + 1)
                    else:
                        raise FinnHubError(f"Server error {response.status}, max retries reached")
                
                else:
                    error_text = await response.text()
                    raise FinnHubError(f"HTTP {response.status}: {error_text}")
        
        except aiohttp.ClientError as e:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)
                logger.warning(f"Network error: {e}, retrying in {delay} seconds")
                await asyncio.sleep(delay)
                return await self._make_request(endpoint, params, retry_count + 1)
            else:
                raise FinnHubError(f"Network error: {e}")
        
        except asyncio.TimeoutError:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAY * (2 ** retry_count)
                logger.warning(f"Request timeout, retrying in {delay} seconds")
                await asyncio.sleep(delay)
                return await self._make_request(endpoint, params, retry_count + 1)
            else:
                raise FinnHubError("Request timeout, max retries reached")
    
    async def get_api_status(self) -> Dict[str, Any]:
        """
        Get API status and validate connection.
        
        Returns:
            API status information
        """
        try:
            # Use a simple endpoint to test connectivity
            data = await self._make_request('stock/symbol', {'exchange': 'US'})
            return {
                'status': 'connected',
                'rate_limit': self.rate_limit_info.__dict__ if self.rate_limit_info else None,
                'symbols_count': len(data) if isinstance(data, list) else 0
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'rate_limit': self.rate_limit_info.__dict__ if self.rate_limit_info else None
            }
    
    # Placeholder methods for core data retrieval - will be implemented in task 1.2
    async def get_stock_price(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """Get stock price data - to be implemented in task 1.2"""
        raise NotImplementedError("Will be implemented in task 1.2")
    
    async def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """Get company profile - to be implemented in task 1.2"""
        raise NotImplementedError("Will be implemented in task 1.2")
    
    async def get_company_news(self, symbol: str, **kwargs) -> List[Dict[str, Any]]:
        """Get company news - to be implemented in task 1.2"""
        raise NotImplementedError("Will be implemented in task 1.2")
    
    async def get_earnings(self, symbol: str) -> Dict[str, Any]:
        """Get earnings data - to be implemented in task 1.2"""
        raise NotImplementedError("Will be implemented in task 1.2")


# Utility functions for configuration and setup
def get_default_client() -> FinnHubAPIClient:
    """Get a default FinnHub client instance"""
    return FinnHubAPIClient()


async def test_connection(api_key: Optional[str] = None) -> bool:
    """
    Test FinnHub API connection.
    
    Args:
        api_key: Optional API key to test
        
    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with FinnHubAPIClient(api_key) as client:
            status = await client.get_api_status()
            return status['status'] == 'connected'
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


# Configuration validation
def validate_configuration() -> Dict[str, Any]:
    """
    Validate FinnHub API configuration.
    
    Returns:
        Configuration validation results
    """
    results = {
        'api_key_configured': False,
        'api_key_source': None,
        'environment_variables': {},
        'recommendations': []
    }
    
    # Check for API key in environment
    api_key = os.getenv('FINNHUB_API_KEY') or os.getenv('FINNHUB_TOKEN')
    if api_key:
        results['api_key_configured'] = True
        results['api_key_source'] = 'FINNHUB_API_KEY' if os.getenv('FINNHUB_API_KEY') else 'FINNHUB_TOKEN'
    else:
        results['recommendations'].append(
            "Set FINNHUB_API_KEY environment variable with your FinnHub API key"
        )
    
    # Record relevant environment variables
    env_vars = ['FINNHUB_API_KEY', 'FINNHUB_TOKEN']
    for var in env_vars:
        value = os.getenv(var)
        results['environment_variables'][var] = 'SET' if value else 'NOT_SET'
    
    return results


if __name__ == "__main__":
    # Basic configuration check when run directly
    import asyncio
    
    async def main():
        print("FinnHub API Client Configuration Check")
        print("=" * 40)
        
        config = validate_configuration()
        print(f"API Key Configured: {config['api_key_configured']}")
        if config['api_key_configured']:
            print(f"API Key Source: {config['api_key_source']}")
        
        print("\nEnvironment Variables:")
        for var, status in config['environment_variables'].items():
            print(f"  {var}: {status}")
        
        if config['recommendations']:
            print("\nRecommendations:")
            for rec in config['recommendations']:
                print(f"  - {rec}")
        
        if config['api_key_configured']:
            print("\nTesting connection...")
            success = await test_connection()
            print(f"Connection test: {'SUCCESS' if success else 'FAILED'}")
    
    asyncio.run(main())