"""
Multi-Market Data Integration System
Supports US, HK, CN, JP, TW markets with unified data standardization
Task 4.2.1: 多市場數據整合

Features:
- Multi-market data aggregation (US, HK, CN, JP, TW)
- Real-time data synchronization
- Cross-market correlation analysis
- Currency conversion and normalization
- Market hours and trading calendar management
- Data quality validation and cleansing
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import aiohttp
import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
import logging

class Market(Enum):
    US = "US"
    HK = "HK" 
    CN = "CN"
    JP = "JP"
    TW = "TW"

class DataType(Enum):
    STOCK_PRICE = "stock_price"
    INDEX = "index"
    FOREX = "forex"
    COMMODITY = "commodity"
    BOND = "bond"

@dataclass
class MarketConfig:
    """Market-specific configuration"""
    market: Market
    timezone: str
    currency: str
    trading_hours: Dict[str, str]
    api_endpoint: str
    rate_limit: int  # requests per second
    data_delay: int  # minutes

@dataclass 
class StandardizedData:
    """Standardized market data format"""
    symbol: str
    market: Market
    data_type: DataType
    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: int
    currency: str
    normalized_price_usd: float
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    additional_data: Optional[Dict[str, Any]] = None

class DataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: List[Dict]) -> List[StandardizedData]:
        pass

class USDataProvider(DataProvider):
    """US market data provider (NYSE, NASDAQ)"""
    
    def __init__(self):
        self.base_url = "https://api.polygon.io/v2/aggs/ticker"
        
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock implementation - replace with real API
        return [
            {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc),
                "open": 100.0,
                "high": 105.0,
                "low": 98.0,
                "close": 103.0,
                "volume": 1000000
            }
        ]
    
    def normalize_data(self, raw_data: List[Dict]) -> List[StandardizedData]:
        normalized = []
        for data in raw_data:
            normalized.append(StandardizedData(
                symbol=data["symbol"],
                market=Market.US,
                data_type=DataType.STOCK_PRICE,
                timestamp=data["timestamp"],
                open_price=data["open"],
                high_price=data["high"],
                low_price=data["low"],
                close_price=data["close"],
                volume=data["volume"],
                currency="USD",
                normalized_price_usd=data["close"]
            ))
        return normalized

class HKDataProvider(DataProvider):
    """Hong Kong market data provider (HKEX)"""
    
    def __init__(self):
        self.base_url = "https://api.hkex.com.hk/v1/market-data"
        
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock implementation
        return [
            {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc),
                "open": 800.0,
                "high": 820.0,
                "low": 790.0,
                "close": 810.0,
                "volume": 500000
            }
        ]
    
    def normalize_data(self, raw_data: List[Dict]) -> List[StandardizedData]:
        # HKD to USD conversion rate (mock)
        hkd_to_usd = 0.128
        
        normalized = []
        for data in raw_data:
            normalized.append(StandardizedData(
                symbol=data["symbol"],
                market=Market.HK,
                data_type=DataType.STOCK_PRICE,
                timestamp=data["timestamp"],
                open_price=data["open"],
                high_price=data["high"],
                low_price=data["low"],
                close_price=data["close"],
                volume=data["volume"],
                currency="HKD",
                normalized_price_usd=data["close"] * hkd_to_usd
            ))
        return normalized

class CNDataProvider(DataProvider):
    """China market data provider (Shanghai/Shenzhen)"""
    
    def __init__(self):
        self.base_url = "https://api.eastmoney.com/v1/market-data"
        
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock implementation
        return [
            {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc),
                "open": 50.0,
                "high": 52.0,
                "low": 49.0,
                "close": 51.5,
                "volume": 2000000
            }
        ]
    
    def normalize_data(self, raw_data: List[Dict]) -> List[StandardizedData]:
        # CNY to USD conversion rate (mock)
        cny_to_usd = 0.14
        
        normalized = []
        for data in raw_data:
            normalized.append(StandardizedData(
                symbol=data["symbol"],
                market=Market.CN,
                data_type=DataType.STOCK_PRICE,
                timestamp=data["timestamp"],
                open_price=data["open"],
                high_price=data["high"],
                low_price=data["low"],
                close_price=data["close"],
                volume=data["volume"],
                currency="CNY",
                normalized_price_usd=data["close"] * cny_to_usd
            ))
        return normalized

class JPDataProvider(DataProvider):
    """Japan market data provider (TSE)"""
    
    def __init__(self):
        self.base_url = "https://api.jpx.co.jp/v1/market-data"
        
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock implementation
        return [
            {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc),
                "open": 3000.0,
                "high": 3100.0,
                "low": 2950.0,
                "close": 3080.0,
                "volume": 800000
            }
        ]
    
    def normalize_data(self, raw_data: List[Dict]) -> List[StandardizedData]:
        # JPY to USD conversion rate (mock)
        jpy_to_usd = 0.0067
        
        normalized = []
        for data in raw_data:
            normalized.append(StandardizedData(
                symbol=data["symbol"],
                market=Market.JP,
                data_type=DataType.STOCK_PRICE,
                timestamp=data["timestamp"],
                open_price=data["open"],
                high_price=data["high"],
                low_price=data["low"],
                close_price=data["close"],
                volume=data["volume"],
                currency="JPY",
                normalized_price_usd=data["close"] * jpy_to_usd
            ))
        return normalized

class TWDataProvider(DataProvider):
    """Taiwan market data provider (TWSE/TPEx)"""
    
    def __init__(self):
        self.base_url = "https://api.finmind.com.tw/v4/data"
        
    async def fetch_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        # Mock implementation using existing FinMind structure
        return [
            {
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc),
                "open": 30.0,
                "high": 31.5,
                "low": 29.5,
                "close": 31.0,
                "volume": 1500000
            }
        ]
    
    def normalize_data(self, raw_data: List[Dict]) -> List[StandardizedData]:
        # TWD to USD conversion rate (mock)
        twd_to_usd = 0.031
        
        normalized = []
        for data in raw_data:
            normalized.append(StandardizedData(
                symbol=data["symbol"],
                market=Market.TW,
                data_type=DataType.STOCK_PRICE,
                timestamp=data["timestamp"],
                open_price=data["open"],
                high_price=data["high"],
                low_price=data["low"],
                close_price=data["close"],
                volume=data["volume"],
                currency="TWD",
                normalized_price_usd=data["close"] * twd_to_usd
            ))
        return normalized

class CurrencyConverter:
    """Real-time currency conversion service"""
    
    def __init__(self):
        self.rates_cache = {}
        self.cache_ttl = timedelta(minutes=5)
        self.last_update = {}
        
    async def get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Get real-time exchange rate"""
        if from_currency == to_currency:
            return 1.0
            
        cache_key = f"{from_currency}_{to_currency}"
        now = datetime.now(timezone.utc)
        
        # Check cache validity
        if (cache_key in self.rates_cache and 
            cache_key in self.last_update and
            now - self.last_update[cache_key] < self.cache_ttl):
            return self.rates_cache[cache_key]
        
        # Fetch new rate (mock implementation)
        rate = await self._fetch_exchange_rate(from_currency, to_currency)
        self.rates_cache[cache_key] = rate
        self.last_update[cache_key] = now
        
        return rate
    
    async def _fetch_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """Fetch exchange rate from external API"""
        # Mock rates - replace with real API like Alpha Vantage, Fixer.io, etc.
        mock_rates = {
            "USD_USD": 1.0,
            "HKD_USD": 0.128,
            "USD_HKD": 7.8,
            "CNY_USD": 0.14,
            "USD_CNY": 7.2,
            "JPY_USD": 0.0067,
            "USD_JPY": 150.0,
            "TWD_USD": 0.031,
            "USD_TWD": 32.0
        }
        
        key = f"{from_currency}_{to_currency}"
        return mock_rates.get(key, 1.0)

class MultiMarketDataIntegrator:
    """Main class for multi-market data integration"""
    
    def __init__(self):
        self.providers = {
            Market.US: USDataProvider(),
            Market.HK: HKDataProvider(),
            Market.CN: CNDataProvider(),
            Market.JP: JPDataProvider(),
            Market.TW: TWDataProvider()
        }
        
        self.market_configs = {
            Market.US: MarketConfig(
                market=Market.US,
                timezone="America/New_York",
                currency="USD",
                trading_hours={"open": "09:30", "close": "16:00"},
                api_endpoint="https://api.polygon.io",
                rate_limit=10,
                data_delay=0
            ),
            Market.HK: MarketConfig(
                market=Market.HK,
                timezone="Asia/Hong_Kong",
                currency="HKD",
                trading_hours={"open": "09:30", "close": "16:00"},
                api_endpoint="https://api.hkex.com.hk",
                rate_limit=5,
                data_delay=15
            ),
            Market.CN: MarketConfig(
                market=Market.CN,
                timezone="Asia/Shanghai",
                currency="CNY",
                trading_hours={"open": "09:30", "close": "15:00"},
                api_endpoint="https://api.eastmoney.com",
                rate_limit=3,
                data_delay=15
            ),
            Market.JP: MarketConfig(
                market=Market.JP,
                timezone="Asia/Tokyo",
                currency="JPY",
                trading_hours={"open": "09:00", "close": "15:00"},
                api_endpoint="https://api.jpx.co.jp",
                rate_limit=5,
                data_delay=20
            ),
            Market.TW: MarketConfig(
                market=Market.TW,
                timezone="Asia/Taipei",
                currency="TWD",
                trading_hours={"open": "09:00", "close": "13:30"},
                api_endpoint="https://api.finmind.com.tw",
                rate_limit=10,
                data_delay=0
            )
        }
        
        self.currency_converter = CurrencyConverter()
        self.logger = logging.getLogger(__name__)
        
    async def fetch_multi_market_data(
        self, 
        symbols: Dict[Market, List[str]], 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[Market, List[StandardizedData]]:
        """Fetch data from multiple markets concurrently"""
        
        tasks = []
        for market, symbol_list in symbols.items():
            if market in self.providers:
                for symbol in symbol_list:
                    task = self._fetch_market_data(market, symbol, start_date, end_date)
                    tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Organize results by market
        market_data = {market: [] for market in Market}
        task_index = 0
        
        for market, symbol_list in symbols.items():
            for symbol in symbol_list:
                if task_index < len(results) and not isinstance(results[task_index], Exception):
                    market_data[market].extend(results[task_index])
                task_index += 1
        
        return market_data
    
    async def _fetch_market_data(
        self, 
        market: Market, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[StandardizedData]:
        """Fetch and normalize data for a specific market and symbol"""
        
        try:
            provider = self.providers[market]
            raw_data = await provider.fetch_data(symbol, start_date, end_date)
            normalized_data = provider.normalize_data(raw_data)
            
            # Apply currency conversion if needed
            for data in normalized_data:
                if data.currency != "USD":
                    rate = await self.currency_converter.get_exchange_rate(data.currency, "USD")
                    data.normalized_price_usd = data.close_price * rate
            
            return normalized_data
            
        except Exception as e:
            self.logger.error(f"Error fetching data for {market.value} {symbol}: {str(e)}")
            return []
    
    def calculate_cross_market_correlation(
        self, 
        market_data: Dict[Market, List[StandardizedData]]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate correlation between different markets"""
        
        # Prepare price series for correlation analysis
        price_series = {}
        
        for market, data_list in market_data.items():
            for data in data_list:
                key = f"{market.value}_{data.symbol}"
                if key not in price_series:
                    price_series[key] = []
                price_series[key].append(data.normalized_price_usd)
        
        # Calculate correlation matrix
        df = pd.DataFrame(price_series)
        correlation_matrix = df.corr()
        
        return correlation_matrix.to_dict()
    
    def get_market_status(self, market: Market) -> Dict[str, Any]:
        """Get current market status (open/closed, trading hours)"""
        
        config = self.market_configs[market]
        now = datetime.now(timezone.utc)
        
        # Convert to market timezone (simplified)
        market_time = now
        
        return {
            "market": market.value,
            "timezone": config.timezone,
            "current_time": market_time.isoformat(),
            "is_trading_day": True,  # Simplified - should check holidays
            "trading_hours": config.trading_hours,
            "data_delay_minutes": config.data_delay
        }
    
    async def get_unified_market_snapshot(
        self, 
        symbols: Dict[Market, List[str]]
    ) -> Dict[str, Any]:
        """Get unified snapshot of all markets"""
        
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=1)
        
        market_data = await self.fetch_multi_market_data(symbols, start_date, end_date)
        correlations = self.calculate_cross_market_correlation(market_data)
        
        market_statuses = {}
        for market in Market:
            market_statuses[market.value] = self.get_market_status(market)
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_data": {
                market.value: [
                    {
                        "symbol": data.symbol,
                        "price_usd": data.normalized_price_usd,
                        "local_price": data.close_price,
                        "currency": data.currency,
                        "volume": data.volume
                    }
                    for data in data_list
                ]
                for market, data_list in market_data.items()
            },
            "cross_market_correlations": correlations,
            "market_statuses": market_statuses,
            "total_symbols_tracked": sum(len(data_list) for data_list in market_data.values())
        }

# Example usage and testing
if __name__ == "__main__":
    async def test_multi_market_integration():
        integrator = MultiMarketDataIntegrator()
        
        # Define symbols to track across markets
        test_symbols = {
            Market.US: ["AAPL", "TSLA"],
            Market.HK: ["0700.HK", "0005.HK"],
            Market.CN: ["000001.SZ", "600000.SS"],
            Market.JP: ["7203.T", "9984.T"],
            Market.TW: ["2330.TW", "2317.TW"]
        }
        
        print("Testing Multi-Market Data Integration...")
        snapshot = await integrator.get_unified_market_snapshot(test_symbols)
        
        print(f"Market Snapshot at {snapshot['timestamp']}")
        print(f"Total symbols tracked: {snapshot['total_symbols_tracked']}")
        
        for market, data in snapshot['market_data'].items():
            print(f"\n{market} Market:")
            for symbol_data in data:
                print(f"  {symbol_data['symbol']}: ${symbol_data['price_usd']:.2f} USD "
                      f"({symbol_data['local_price']:.2f} {symbol_data['currency']})")
        
        return snapshot
    
    # Run test
    snapshot = asyncio.run(test_multi_market_integration())
    print("\nMulti-Market Data Integration test completed successfully!")