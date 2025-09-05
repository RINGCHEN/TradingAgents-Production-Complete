#!/usr/bin/env python3
"""
FinMind 實時台股數據適配器 - TradingAgents 商業化增強版
提供即時股價、技術指標、財報分析等專業數據服務

功能特色：
1. 即時台股數據流
2. 技術指標自動計算
3. 財報數據解析
4. 市場情緒指標
5. 法人進出分析
"""

import asyncio
import aiohttp
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import json
import os
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class StockData(BaseModel):
    """股票數據模型"""
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    timestamp: datetime

class TechnicalIndicators(BaseModel):
    """技術指標模型"""
    symbol: str
    sma_5: Optional[float] = None
    sma_20: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_lower: Optional[float] = None
    timestamp: datetime

class FinancialMetrics(BaseModel):
    """財務指標模型"""
    symbol: str
    revenue: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None
    roe: Optional[float] = None
    debt_ratio: Optional[float] = None
    current_ratio: Optional[float] = None
    quarter: str
    year: int

class MarketSentiment(BaseModel):
    """市場情緒模型"""
    symbol: str
    institutional_buy: float
    institutional_sell: float
    net_institutional_flow: float
    foreign_investment: float
    sentiment_score: float  # -1 to 1
    confidence_level: float  # 0 to 1
    timestamp: datetime

class FinMindRealtimeAdapter:
    """FinMind實時數據適配器"""
    
    def __init__(self, api_token: Optional[str] = None):
        self.base_url = "https://api.finmindtrade.com/api/v4"
        self.api_token = api_token or os.getenv("FINMIND_API_TOKEN", "")
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 熱門台股代號映射
        self.popular_stocks = {
            "2330": "台積電",
            "2317": "鴻海",  
            "2454": "聯發科",
            "2881": "富邦金",
            "6505": "台塑化",
            "2382": "廣達",
            "3711": "日月光投控",
            "2412": "中華電",
            "1303": "南亞",
            "1301": "台塑"
        }
    
    async def __aenter__(self):
        """異步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """發送API請求"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # 添加API token
        if self.api_token:
            params["token"] = self.api_token
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.error(f"API request failed: {response.status}")
                    return {"msg": "API request failed", "data": []}
        
        except Exception as e:
            logger.error(f"Request error: {e}")
            return {"msg": f"Request error: {e}", "data": []}
    
    async def get_realtime_stock_data(self, stock_id: str) -> Optional[StockData]:
        """獲取即時股票數據"""
        params = {
            "dataset": "TaiwanStockPrice",
            "data_id": stock_id,
            "start_date": datetime.now().strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d")
        }
        
        result = await self._make_request("data", params)
        
        if result.get("data"):
            data = result["data"][-1]  # 取最新數據
            
            return StockData(
                symbol=stock_id,
                name=self.popular_stocks.get(stock_id, stock_id),
                price=float(data.get("close", 0)),
                change=float(data.get("close", 0)) - float(data.get("open", 0)),
                change_percent=((float(data.get("close", 0)) - float(data.get("open", 0))) / float(data.get("open", 1))) * 100,
                volume=int(data.get("Trading_Volume", 0)),
                timestamp=datetime.now()
            )
        
        return None
    
    async def calculate_technical_indicators(self, stock_id: str, days: int = 60) -> Optional[TechnicalIndicators]:
        """計算技術指標"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        params = {
            "dataset": "TaiwanStockPrice",
            "data_id": stock_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        result = await self._make_request("data", params)
        
        if result.get("data") and len(result["data"]) > 20:
            df = pd.DataFrame(result["data"])
            df['close'] = pd.to_numeric(df['close'])
            
            # 計算技術指標
            sma_5 = df['close'].rolling(window=5).mean().iloc[-1] if len(df) >= 5 else None
            sma_20 = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
            
            # RSI計算
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if len(df) >= 14 else None
            
            # MACD計算
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            macd = (ema_12 - ema_26).iloc[-1] if len(df) >= 26 else None
            
            # 布林帶計算
            sma_20_series = df['close'].rolling(window=20).mean()
            std_20 = df['close'].rolling(window=20).std()
            bollinger_upper = (sma_20_series + (std_20 * 2)).iloc[-1] if len(df) >= 20 else None
            bollinger_lower = (sma_20_series - (std_20 * 2)).iloc[-1] if len(df) >= 20 else None
            
            return TechnicalIndicators(
                symbol=stock_id,
                sma_5=float(sma_5) if pd.notna(sma_5) else None,
                sma_20=float(sma_20) if pd.notna(sma_20) else None,
                rsi=float(rsi) if pd.notna(rsi) else None,
                macd=float(macd) if pd.notna(macd) else None,
                bollinger_upper=float(bollinger_upper) if pd.notna(bollinger_upper) else None,
                bollinger_lower=float(bollinger_lower) if pd.notna(bollinger_lower) else None,
                timestamp=datetime.now()
            )
        
        return None
    
    async def get_financial_statements(self, stock_id: str) -> Optional[FinancialMetrics]:
        """獲取財務報表數據"""
        current_year = datetime.now().year
        
        # 獲取最近的財報數據
        params = {
            "dataset": "TaiwanStockFinancialStatements",
            "data_id": stock_id,
            "start_date": f"{current_year-1}-01-01",
            "end_date": f"{current_year}-12-31"
        }
        
        result = await self._make_request("data", params)
        
        if result.get("data"):
            # 取最新季度數據
            latest_data = result["data"][-1]
            
            return FinancialMetrics(
                symbol=stock_id,
                revenue=float(latest_data.get("revenue", 0)) if latest_data.get("revenue") else None,
                net_income=float(latest_data.get("net_income", 0)) if latest_data.get("net_income") else None,
                eps=float(latest_data.get("EPS", 0)) if latest_data.get("EPS") else None,
                roe=float(latest_data.get("ROE", 0)) if latest_data.get("ROE") else None,
                debt_ratio=float(latest_data.get("debt_ratio", 0)) if latest_data.get("debt_ratio") else None,
                current_ratio=float(latest_data.get("current_ratio", 0)) if latest_data.get("current_ratio") else None,
                quarter=latest_data.get("quarter", "Q1"),
                year=int(latest_data.get("year", current_year))
            )
        
        return None
    
    async def get_institutional_investors_flow(self, stock_id: str) -> Optional[MarketSentiment]:
        """獲取法人進出數據"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # 取一週數據
        
        params = {
            "dataset": "TaiwanStockInstitutionalInvestorsBuySell",
            "data_id": stock_id,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d")
        }
        
        result = await self._make_request("data", params)
        
        if result.get("data"):
            # 計算最近的法人進出
            df = pd.DataFrame(result["data"])
            
            if len(df) > 0:
                # 計算買賣超
                institutional_buy = df['buy'].sum() if 'buy' in df.columns else 0
                institutional_sell = df['sell'].sum() if 'sell' in df.columns else 0
                net_flow = institutional_buy - institutional_sell
                
                # 計算外資投資
                foreign_investment = df['foreign_investment'].sum() if 'foreign_investment' in df.columns else 0
                
                # 計算情緒分數 (-1 to 1)
                max_volume = max(abs(net_flow), 1)  # 避免除零
                sentiment_score = net_flow / max_volume
                sentiment_score = max(-1, min(1, sentiment_score))  # 限制範圍
                
                # 信心水準基於數據完整度
                confidence_level = min(len(df) / 7, 1.0)  # 基於數據天數
                
                return MarketSentiment(
                    symbol=stock_id,
                    institutional_buy=float(institutional_buy),
                    institutional_sell=float(institutional_sell),
                    net_institutional_flow=float(net_flow),
                    foreign_investment=float(foreign_investment),
                    sentiment_score=float(sentiment_score),
                    confidence_level=float(confidence_level),
                    timestamp=datetime.now()
                )
        
        return None
    
    async def get_comprehensive_analysis(self, stock_id: str) -> Dict[str, Any]:
        """獲取股票綜合分析數據"""
        try:
            # 並發獲取所有數據
            tasks = [
                self.get_realtime_stock_data(stock_id),
                self.calculate_technical_indicators(stock_id),
                self.get_financial_statements(stock_id),
                self.get_institutional_investors_flow(stock_id)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            stock_data, technical, financial, sentiment = results
            
            # 構建綜合分析結果
            analysis = {
                "symbol": stock_id,
                "name": self.popular_stocks.get(stock_id, stock_id),
                "timestamp": datetime.now().isoformat(),
                "real_time_data": stock_data.dict() if stock_data else None,
                "technical_indicators": technical.dict() if technical else None,
                "financial_metrics": financial.dict() if financial else None,
                "market_sentiment": sentiment.dict() if sentiment else None,
                "analysis_summary": self._generate_analysis_summary(stock_data, technical, financial, sentiment)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Comprehensive analysis error for {stock_id}: {e}")
            return {
                "symbol": stock_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_analysis_summary(self, stock_data, technical, financial, sentiment) -> Dict[str, Any]:
        """生成分析摘要"""
        summary = {
            "overall_trend": "中性",
            "technical_signal": "觀望",
            "fundamental_health": "普通",
            "sentiment_outlook": "中性",
            "investment_recommendation": "觀望",
            "confidence_score": 0.5,
            "key_factors": []
        }
        
        try:
            key_factors = []
            confidence_factors = []
            
            # 技術面分析
            if technical:
                if technical.rsi and technical.rsi < 30:
                    summary["technical_signal"] = "買入"
                    key_factors.append("RSI顯示超賣")
                    confidence_factors.append(0.7)
                elif technical.rsi and technical.rsi > 70:
                    summary["technical_signal"] = "賣出"
                    key_factors.append("RSI顯示超買")
                    confidence_factors.append(0.7)
                
                if technical.macd and technical.macd > 0:
                    key_factors.append("MACD呈正向")
                    confidence_factors.append(0.6)
            
            # 基本面分析
            if financial:
                if financial.roe and financial.roe > 15:
                    summary["fundamental_health"] = "良好"
                    key_factors.append("ROE表現優異")
                    confidence_factors.append(0.8)
                
                if financial.debt_ratio and financial.debt_ratio < 0.3:
                    key_factors.append("負債比率健康")
                    confidence_factors.append(0.6)
            
            # 情緒面分析
            if sentiment:
                if sentiment.sentiment_score > 0.3:
                    summary["sentiment_outlook"] = "樂觀"
                    key_factors.append("法人淨買超")
                    confidence_factors.append(0.7)
                elif sentiment.sentiment_score < -0.3:
                    summary["sentiment_outlook"] = "悲觀"
                    key_factors.append("法人淨賣超")
                    confidence_factors.append(0.7)
            
            # 計算整體信心分數
            if confidence_factors:
                summary["confidence_score"] = sum(confidence_factors) / len(confidence_factors)
            
            # 設定投資建議
            positive_signals = sum(1 for factor in key_factors if any(word in factor for word in ["優異", "健康", "淨買超", "超賣"]))
            negative_signals = sum(1 for factor in key_factors if any(word in factor for word in ["超買", "淨賣超"]))
            
            if positive_signals > negative_signals:
                summary["investment_recommendation"] = "買入"
                summary["overall_trend"] = "看漲"
            elif negative_signals > positive_signals:
                summary["investment_recommendation"] = "賣出"
                summary["overall_trend"] = "看跌"
            
            summary["key_factors"] = key_factors
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
        
        return summary

# --- API端點集成功能 ---

class FinMindAPIService:
    """FinMind API服務封裝"""
    
    def __init__(self):
        self.adapter = None
    
    async def get_stock_analysis(self, stock_symbol: str) -> Dict[str, Any]:
        """獲取股票分析 - 供API端點使用"""
        stock_id = stock_symbol.replace(".TW", "")  # 移除.TW後綴
        
        async with FinMindRealtimeAdapter() as adapter:
            analysis = await adapter.get_comprehensive_analysis(stock_id)
            return analysis
    
    async def get_multiple_stocks_analysis(self, stock_symbols: List[str]) -> List[Dict[str, Any]]:
        """批次獲取多檔股票分析"""
        results = []
        
        async with FinMindRealtimeAdapter() as adapter:
            tasks = [
                adapter.get_comprehensive_analysis(symbol.replace(".TW", ""))
                for symbol in stock_symbols
            ]
            
            analyses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, analysis in zip(stock_symbols, analyses):
                if isinstance(analysis, Exception):
                    results.append({
                        "symbol": symbol,
                        "error": str(analysis),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    results.append(analysis)
        
        return results

# 全局服務實例
finmind_service = FinMindAPIService()