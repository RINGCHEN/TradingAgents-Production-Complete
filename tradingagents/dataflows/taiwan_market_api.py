#!/usr/bin/env python3
"""
Taiwan Market API - 台灣股市數據API整合
天工 (TianGong) - 專為台灣股市設計的數據獲取和處理系統

此模組負責：
1. FinMind API 深度整合
2. 台股特有數據處理
3. 法人進出數據分析
4. 權值股影響分析
"""

import asyncio
import aiohttp
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd

class DataCategory(Enum):
    """數據類別"""
    STOCK_PRICE = "TaiwanStockPrice"              # 股價數據
    STOCK_INFO = "TaiwanStockInfo"                # 股票基本資訊
    FINANCIAL_STATEMENT = "TaiwanStockFinancialStatements"  # 財報
    BALANCE_SHEET = "TaiwanStockBalanceSheet"     # 資產負債表
    CASH_FLOW = "TaiwanStockCashFlowsStatement"   # 現金流量表
    INSTITUTIONAL_INVESTORS = "TaiwanStockInstitutionalInvestors"  # 法人進出
    MARGIN_PURCHASE = "TaiwanStockMarginPurchaseShort"  # 融資融券
    SHAREHOLDING = "TaiwanStockShareholding"      # 股權分布
    DIVIDEND = "TaiwanStockDividend"              # 股利資訊
    MARKET_INDEX = "TaiwanStockPrice"             # 修復：基於GOOGLE診斷，使用正確的FinMind API參數

class InstitutionalType(Enum):
    """法人類型"""
    FOREIGN_INVESTOR = "外資"
    INVESTMENT_TRUST = "投信"
    DEALER = "自營商"

@dataclass
class TaiwanStockData:
    """台股數據基礎類"""
    stock_id: str
    date: str
    source: str = "FinMind"
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class StockPriceData(TaiwanStockData):
    """股價數據"""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: int = 0
    trading_money: float = 0.0

@dataclass
class InstitutionalData(TaiwanStockData):
    """法人進出數據"""
    foreign_buy: float = 0.0
    foreign_sell: float = 0.0
    foreign_net: float = 0.0
    trust_buy: float = 0.0
    trust_sell: float = 0.0
    trust_net: float = 0.0
    dealer_buy: float = 0.0
    dealer_sell: float = 0.0
    dealer_net: float = 0.0

@dataclass
class MarketIndexData:
    """大盤指數數據"""
    index_name: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    change: float
    change_percent: float

class TaiwanMarketAPI:
    """台灣市場API客戶端"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.getenv('FINMIND_API_TOKEN')
        self.base_url = "https://api.finmindtrade.com/api/v4"
        self.logger = logging.getLogger(__name__)
        
        # HTTP客戶端設置
        self.session = None
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        # 快取設置
        self.cache_enabled = True
        self.cache_duration = 300  # 5分鐘快取
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # 設置日誌
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, dataset: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """發送API請求"""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        
        # 添加API token到參數
        if self.api_token:
            params['token'] = self.api_token
        
        # 檢查快取
        cache_key = f"{dataset}_{json.dumps(params, sort_keys=True)}"
        if self.cache_enabled and cache_key in self._cache:
            cached_data = self._cache[cache_key]
            if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_duration:
                self.logger.debug(f"快取命中: {dataset}")
                return cached_data['data']
        
        try:
            url = f"{self.base_url}/data"
            params['dataset'] = dataset
            
            self.logger.debug(f"請求 FinMind API: {dataset}")
            
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                # 快取成功的響應
                if data.get('status') == 200 and self.cache_enabled:
                    self._cache[cache_key] = {
                        'data': data,
                        'timestamp': datetime.now().timestamp()
                    }
                
                return data
                
        except aiohttp.ClientError as e:
            self.logger.error(f"FinMind API 請求失敗: {str(e)}")
            return {
                'status': 500,
                'msg': f'API 請求錯誤: {str(e)}',
                'data': []
            }
        except Exception as e:
            self.logger.error(f"未預期錯誤: {str(e)}")
            return {
                'status': 500,
                'msg': f'未預期錯誤: {str(e)}',
                'data': []
            }
    
    async def get_stock_price(self, stock_id: str, start_date: str, end_date: str = None) -> List[StockPriceData]:
        """獲取股價數據"""
        if not end_date:
            end_date = start_date
        
        params = {
            'data_id': stock_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        response = await self._make_request(DataCategory.STOCK_PRICE.value, params)
        
        if response['status'] != 200:
            self.logger.warning(f"獲取股價失敗: {response.get('msg', 'Unknown error')}")
            return []
        
        stock_prices = []
        for item in response.get('data', []):
            try:
                stock_price = StockPriceData(
                    stock_id=stock_id,
                    date=item.get('date', ''),
                    open=float(item.get('open', 0)),
                    high=float(item.get('max', 0)),  # FinMind 使用 'max' 而非 'high'
                    low=float(item.get('min', 0)),   # FinMind 使用 'min' 而非 'low'
                    close=float(item.get('close', 0)),
                    volume=int(item.get('Trading_Volume', 0)),
                    trading_money=float(item.get('Trading_money', 0))
                )
                stock_prices.append(stock_price)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"解析股價數據失敗: {str(e)}")
                continue
        
        return stock_prices
    
    async def get_institutional_investors(self, stock_id: str, start_date: str, end_date: str = None) -> List[InstitutionalData]:
        """獲取法人進出數據"""
        if not end_date:
            end_date = start_date
        
        params = {
            'data_id': stock_id,
            'start_date': start_date,
            'end_date': end_date
        }
        
        response = await self._make_request(DataCategory.INSTITUTIONAL_INVESTORS.value, params)
        
        if response['status'] != 200:
            self.logger.warning(f"獲取法人數據失敗: {response.get('msg', 'Unknown error')}")
            return []
        
        institutional_data = []
        for item in response.get('data', []):
            try:
                data = InstitutionalData(
                    stock_id=stock_id,
                    date=item.get('date', ''),
                    foreign_buy=float(item.get('Foreign_Investor_Buy', 0)),
                    foreign_sell=float(item.get('Foreign_Investor_Sell', 0)),
                    foreign_net=float(item.get('Foreign_Investor_Buy', 0)) - float(item.get('Foreign_Investor_Sell', 0)),
                    trust_buy=float(item.get('Investment_Trust_Buy', 0)),
                    trust_sell=float(item.get('Investment_Trust_Sell', 0)),
                    trust_net=float(item.get('Investment_Trust_Buy', 0)) - float(item.get('Investment_Trust_Sell', 0)),
                    dealer_buy=float(item.get('Dealer_self_Buy', 0)),
                    dealer_sell=float(item.get('Dealer_self_Sell', 0)),
                    dealer_net=float(item.get('Dealer_self_Buy', 0)) - float(item.get('Dealer_self_Sell', 0))
                )
                institutional_data.append(data)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"解析法人數據失敗: {str(e)}")
                continue
        
        return institutional_data
    
    async def get_market_index(self, index_name: str = "TAIEX", start_date: str = None, end_date: str = None) -> List[MarketIndexData]:
        """獲取大盤指數數據"""
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = start_date
        
        params = {
            'data_id': index_name,
            'start_date': start_date,
            'end_date': end_date
        }
        
        response = await self._make_request(DataCategory.MARKET_INDEX.value, params)
        
        if response['status'] != 200:
            self.logger.warning(f"獲取指數數據失敗: {response.get('msg', 'Unknown error')}")
            return []
        
        index_data = []
        for item in response.get('data', []):
            try:
                prev_close = float(item.get('close', 0))
                current_close = float(item.get('close', 0))
                change = current_close - prev_close if prev_close > 0 else 0
                change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                
                data = MarketIndexData(
                    index_name=index_name,
                    date=item.get('date', ''),
                    open=float(item.get('open', 0)),
                    high=float(item.get('max', 0)),
                    low=float(item.get('min', 0)),
                    close=current_close,
                    volume=int(item.get('Trading_Volume', 0)),
                    change=change,
                    change_percent=change_percent
                )
                index_data.append(data)
            except (ValueError, TypeError) as e:
                self.logger.warning(f"解析指數數據失敗: {str(e)}")
                continue
        
        return index_data
    
    async def get_stock_info(self, stock_id: str) -> Dict[str, Any]:
        """獲取股票基本資訊"""
        params = {'data_id': stock_id}
        
        response = await self._make_request(DataCategory.STOCK_INFO.value, params)
        
        if response['status'] != 200:
            self.logger.warning(f"獲取股票資訊失敗: {response.get('msg', 'Unknown error')}")
            return {}
        
        data = response.get('data', [])
        if not data:
            return {}
        
        stock_info = data[0]  # 取第一筆資料
        
        return {
            'stock_id': stock_info.get('stock_id', stock_id),
            'stock_name': stock_info.get('stock_name', ''),
            'industry_category': stock_info.get('industry_category', ''),
            'market_type': stock_info.get('type', ''),
            'listing_date': stock_info.get('date', ''),
            'source': 'FinMind'
        }
    
    async def analyze_institutional_trend(self, stock_id: str, days: int = 30) -> Dict[str, Any]:
        """分析法人進出趨勢"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        institutional_data = await self.get_institutional_investors(stock_id, start_date, end_date)
        
        if not institutional_data:
            return {
                'error': '無法獲取法人數據',
                'stock_id': stock_id,
                'analysis_period': f'{start_date} to {end_date}'
            }
        
        # 計算累計淨買超
        total_foreign_net = sum(data.foreign_net for data in institutional_data)
        total_trust_net = sum(data.trust_net for data in institutional_data)
        total_dealer_net = sum(data.dealer_net for data in institutional_data)
        
        # 分析趨勢
        def analyze_trend(net_values: List[float]) -> str:
            if not net_values:
                return 'neutral'
            
            positive_days = sum(1 for value in net_values if value > 0)
            negative_days = sum(1 for value in net_values if value < 0)
            
            if positive_days > negative_days * 1.5:
                return 'bullish'
            elif negative_days > positive_days * 1.5:
                return 'bearish'
            else:
                return 'neutral'
        
        foreign_trend = analyze_trend([data.foreign_net for data in institutional_data])
        trust_trend = analyze_trend([data.trust_net for data in institutional_data])
        dealer_trend = analyze_trend([data.dealer_net for data in institutional_data])
        
        # 計算平均每日交易量
        avg_foreign_volume = abs(total_foreign_net) / len(institutional_data) if institutional_data else 0
        avg_trust_volume = abs(total_trust_net) / len(institutional_data) if institutional_data else 0
        avg_dealer_volume = abs(total_dealer_net) / len(institutional_data) if institutional_data else 0
        
        return {
            'stock_id': stock_id,
            'analysis_period': f'{start_date} to {end_date}',
            'days_analyzed': len(institutional_data),
            'foreign_investor': {
                'total_net': total_foreign_net,
                'trend': foreign_trend,
                'avg_daily_volume': avg_foreign_volume,
                'impact': 'high' if abs(total_foreign_net) > 1000000 else 'medium' if abs(total_foreign_net) > 100000 else 'low'
            },
            'investment_trust': {
                'total_net': total_trust_net,
                'trend': trust_trend,
                'avg_daily_volume': avg_trust_volume,
                'impact': 'high' if abs(total_trust_net) > 500000 else 'medium' if abs(total_trust_net) > 50000 else 'low'
            },
            'dealer': {
                'total_net': total_dealer_net,
                'trend': dealer_trend,
                'avg_daily_volume': avg_dealer_volume,
                'impact': 'high' if abs(total_dealer_net) > 200000 else 'medium' if abs(total_dealer_net) > 20000 else 'low'
            },
            'overall_sentiment': self._calculate_overall_sentiment(foreign_trend, trust_trend, dealer_trend),
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_overall_sentiment(self, foreign: str, trust: str, dealer: str) -> str:
        """計算整體法人情緒"""
        bullish_count = sum(1 for trend in [foreign, trust, dealer] if trend == 'bullish')
        bearish_count = sum(1 for trend in [foreign, trust, dealer] if trend == 'bearish')
        
        if bullish_count >= 2:
            return 'bullish'
        elif bearish_count >= 2:
            return 'bearish'
        else:
            return 'neutral'
    
    async def check_price_limit_impact(self, stock_id: str, days: int = 5) -> Dict[str, Any]:
        """檢查漲跌停影響"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        price_data = await self.get_stock_price(stock_id, start_date, end_date)
        
        if not price_data:
            return {
                'error': '無法獲取股價數據',
                'stock_id': stock_id
            }
        
        limit_events = []
        
        for data in price_data:
            # 檢查漲停 (開盤 = 最高 = 收盤，或收盤接近10%漲幅)
            if data.open > 0 and data.close > 0:
                daily_change = (data.close - data.open) / data.open
                
                is_limit_up = (
                    abs(data.high - data.close) < data.close * 0.001 and  # 收盤接近最高
                    daily_change > 0.095  # 漲幅接近10%
                )
                
                is_limit_down = (
                    abs(data.low - data.close) < data.close * 0.001 and  # 收盤接近最低
                    daily_change < -0.095  # 跌幅接近10%
                )
                
                if is_limit_up or is_limit_down:
                    limit_events.append({
                        'date': data.date,
                        'type': 'limit_up' if is_limit_up else 'limit_down',
                        'open': data.open,
                        'high': data.high,
                        'low': data.low,
                        'close': data.close,
                        'volume': data.volume,
                        'change_percent': daily_change * 100
                    })
        
        return {
            'stock_id': stock_id,
            'analysis_period': f'{start_date} to {end_date}',
            'limit_events': limit_events,
            'limit_event_count': len(limit_events),
            'has_recent_limits': len(limit_events) > 0,
            'impact_assessment': 'high' if len(limit_events) >= 2 else 'medium' if len(limit_events) == 1 else 'low',
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """清理快取"""
        self._cache.clear()
        self.logger.info("API 快取已清理")
    
    async def get_taiwan_market_summary(self) -> Dict[str, Any]:
        """獲取台股市場總覽"""
        try:
            # 獲取大盤指數
            taiex_data = await self.get_market_index("TAIEX")
            
            # 獲取重要指數
            indices = ["TAIEX", "TPEx"]  # 加權指數、櫃買指數
            index_summary = {}
            
            for index_name in indices:
                index_data = await self.get_market_index(index_name)
                if index_data:
                    latest = index_data[-1]
                    index_summary[index_name] = {
                        'current': latest.close,
                        'change': latest.change,
                        'change_percent': latest.change_percent,
                        'volume': latest.volume
                    }
            
            return {
                'market_status': 'open' if datetime.now().weekday() < 5 else 'closed',
                'indices': index_summary,
                'last_update': datetime.now().isoformat(),
                'source': 'FinMind'
            }
            
        except Exception as e:
            self.logger.error(f"獲取市場總覽失敗: {str(e)}")
            return {
                'error': str(e),
                'last_update': datetime.now().isoformat()
            }

# 便利函數
async def get_taiwan_stock_data(stock_id: str, days: int = 30) -> Dict[str, Any]:
    """獲取台股完整數據包"""
    async with TaiwanMarketAPI() as api:
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # 並行獲取各類數據
        tasks = [
            api.get_stock_price(stock_id, start_date, end_date),
            api.get_institutional_investors(stock_id, start_date, end_date),
            api.get_stock_info(stock_id),
            api.analyze_institutional_trend(stock_id, days),
            api.check_price_limit_impact(stock_id, min(days, 10))
        ]
        
        try:
            price_data, institutional_data, stock_info, institutional_trend, price_limit_impact = await asyncio.gather(*tasks)
            
            return {
                'stock_id': stock_id,
                'stock_info': stock_info,
                'price_data': [asdict(data) for data in price_data],
                'institutional_data': [asdict(data) for data in institutional_data],
                'institutional_trend': institutional_trend,
                'price_limit_impact': price_limit_impact,
                'data_period': f'{start_date} to {end_date}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'stock_id': stock_id,
                'timestamp': datetime.now().isoformat()
            }

if __name__ == "__main__":
    # 測試腳本
    import asyncio
    
    async def test_taiwan_market_api():
        print("🇹🇼 測試台灣市場API")
        
        # 測試台積電 (2330)
        stock_id = "2330"
        
        async with TaiwanMarketAPI() as api:
            # 測試股價數據
            print(f"測試股價數據獲取: {stock_id}")
            price_data = await api.get_stock_price(stock_id, "2025-08-01", "2025-08-02")
            print(f"  獲取 {len(price_data)} 筆股價數據")
            
            # 測試股票資訊
            print(f"測試股票資訊獲取: {stock_id}")
            stock_info = await api.get_stock_info(stock_id)
            print(f"  股票名稱: {stock_info.get('stock_name', 'N/A')}")
            
            # 測試法人分析
            print(f"測試法人趨勢分析: {stock_id}")
            institutional_trend = await api.analyze_institutional_trend(stock_id, 5)
            if 'error' not in institutional_trend:
                print(f"  外資趨勢: {institutional_trend['foreign_investor']['trend']}")
            
            # 測試市場總覽
            print("測試市場總覽")
            market_summary = await api.get_taiwan_market_summary()
            print(f"  市場狀態: {market_summary.get('market_status', 'unknown')}")
        
        print("✅ 測試完成")
    
    asyncio.run(test_taiwan_market_api())