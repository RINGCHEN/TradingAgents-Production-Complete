#!/usr/bin/env python3
"""
FinMind API Adapter - 適配器模式封裝
提供統一的財務數據接口，簡化分析師對FinMind API的調用
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

from .finmind_api import FinMindAPI, FinMindResponse, FinMindError
from ..utils.user_context import UserContext, create_user_context

logger = logging.getLogger(__name__)

class FinMindAdapter:
    """FinMind API 適配器 - 為分析師提供簡化的數據獲取接口"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化適配器
        
        Args:
            config: 配置字典，如果為None則使用預設配置
        """
        self.finmind_api = FinMindAPI(config)
        self.logger = logging.getLogger(__name__)
        
        # 預設用戶上下文（當沒有提供時使用）
        self.default_user_context = create_user_context("system", "gold")
        
    async def get_stock_price(
        self, 
        stock_id: str, 
        start_date: str, 
        end_date: str,
        user_context: Optional[UserContext] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取股價數據
        
        Args:
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            user_context: 用戶上下文，如果為None則使用預設
            
        Returns:
            股價數據列表
        """
        try:
            context = user_context or self.default_user_context
            response = await self.finmind_api.get_stock_price_history(
                context, stock_id, start_date, end_date
            )
            
            if response.success:
                return response.data
            else:
                self.logger.warning(f"獲取股價數據失敗: {response.error}")
                return []
                
        except Exception as e:
            self.logger.error(f"股價數據獲取異常: {str(e)}")
            return []
    
    async def get_financial_statement(
        self,
        stock_id: str,
        statement_type: str,
        start_date: str,
        end_date: str,
        user_context: Optional[UserContext] = None
    ) -> List[Dict[str, Any]]:
        """
        獲取財報數據
        
        Args:
            stock_id: 股票代號
            statement_type: 財報類型 ('income', 'balance', 'cashflow')
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            user_context: 用戶上下文
            
        Returns:
            財報數據列表
        """
        try:
            context = user_context or self.default_user_context
            
            # 解析日期來獲取年份和季度
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            all_data = []
            
            # 獲取時間範圍內的所有季度數據
            current_dt = start_dt
            while current_dt <= end_dt:
                year = current_dt.year
                quarter = (current_dt.month - 1) // 3 + 1
                
                try:
                    response = await self.finmind_api.get_financial_statement(
                        context, stock_id, statement_type, year, quarter
                    )
                    
                    if response.success and response.data:
                        all_data.extend(response.data)
                    
                except FinMindError as e:
                    self.logger.warning(f"獲取{year}Q{quarter}財報失敗: {str(e)}")
                
                # 移動到下一季
                if quarter == 4:
                    current_dt = current_dt.replace(year=year+1, month=1)
                else:
                    current_dt = current_dt.replace(month=quarter*3+1)
            
            return all_data
            
        except Exception as e:
            self.logger.error(f"財報數據獲取異常: {str(e)}")
            return []
    
    async def get_latest_financial_data(
        self,
        stock_id: str,
        user_context: Optional[UserContext] = None
    ) -> Dict[str, Any]:
        """
        獲取最新的完整財務數據
        
        Args:
            stock_id: 股票代號
            user_context: 用戶上下文
            
        Returns:
            包含損益表、資產負債表、現金流量表的字典
        """
        try:
            context = user_context or self.default_user_context
            
            # 計算最近兩年的日期範圍
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
            
            # 並行獲取三種財報
            tasks = [
                self.get_financial_statement(stock_id, 'income', start_date, end_date, context),
                self.get_financial_statement(stock_id, 'balance_sheet', start_date, end_date, context),
                self.get_financial_statement(stock_id, 'cash_flow', start_date, end_date, context)
            ]
            
            income_data, balance_data, cashflow_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 處理異常結果
            if isinstance(income_data, Exception):
                income_data = []
            if isinstance(balance_data, Exception):
                balance_data = []
            if isinstance(cashflow_data, Exception):
                cashflow_data = []
            
            return {
                'income_statement': income_data,
                'balance_sheet': balance_data,
                'cash_flow': cashflow_data
            }
            
        except Exception as e:
            self.logger.error(f"獲取最新財務數據異常: {str(e)}")
            return {
                'income_statement': [],
                'balance_sheet': [],
                'cash_flow': []
            }
    
    async def get_stock_basic_info(
        self,
        stock_id: str,
        date: Optional[str] = None,
        user_context: Optional[UserContext] = None
    ) -> Dict[str, Any]:
        """
        獲取股票基本資訊
        
        Args:
            stock_id: 股票代號
            date: 指定日期，如果為None則使用今天
            user_context: 用戶上下文
            
        Returns:
            股票基本資訊字典
        """
        try:
            context = user_context or self.default_user_context
            
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            
            # 獲取當日交易資訊
            response = await self.finmind_api.get_daily_trading_info(
                context, stock_id, date
            )
            
            if response.success and response.data:
                latest_data = response.data[0] if response.data else {}
                return {
                    'stock_id': stock_id,
                    'date': date,
                    'current_price': latest_data.get('close', 0),
                    'volume': latest_data.get('volume', 0),
                    'high': latest_data.get('high', 0),
                    'low': latest_data.get('low', 0),
                    'open': latest_data.get('open', 0)
                }
            else:
                return {'stock_id': stock_id, 'error': response.error}
                
        except Exception as e:
            self.logger.error(f"獲取股票基本資訊異常: {str(e)}")
            return {'stock_id': stock_id, 'error': str(e)}
    
    async def get_market_index_data(
        self,
        index_name: str = "TAIEX",
        date: Optional[str] = None,
        user_context: Optional[UserContext] = None
    ) -> Dict[str, Any]:
        """
        獲取市場指數數據
        
        Args:
            index_name: 指數名稱
            date: 指定日期
            user_context: 用戶上下文
            
        Returns:
            市場指數數據
        """
        try:
            context = user_context or self.default_user_context
            
            response = await self.finmind_api.get_market_index(
                context, index_name, date
            )
            
            if response.success and response.data:
                return response.data[0] if response.data else {}
            else:
                return {'error': response.error}
                
        except Exception as e:
            self.logger.error(f"獲取市場指數異常: {str(e)}")
            return {'error': str(e)}
    
    async def batch_get_stocks_data(
        self,
        stock_ids: List[str],
        date: str,
        user_context: Optional[UserContext] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        批次獲取多檔股票數據
        
        Args:
            stock_ids: 股票代號列表
            date: 日期
            user_context: 用戶上下文
            
        Returns:
            股票代號對應數據的字典
        """
        try:
            context = user_context or self.default_user_context
            
            responses = await self.finmind_api.batch_get_stock_data(
                context, stock_ids, date
            )
            
            result = {}
            for stock_id, response in responses.items():
                if response.success and response.data:
                    result[stock_id] = response.data[0] if response.data else {}
                else:
                    result[stock_id] = {'error': response.error}
            
            return result
            
        except Exception as e:
            self.logger.error(f"批次獲取股票數據異常: {str(e)}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取API統計信息"""
        return self.finmind_api.get_stats()
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        return await self.finmind_api.health_check()

# 便利函數
def create_finmind_adapter(config: Optional[Dict[str, Any]] = None) -> FinMindAdapter:
    """創建FinMind適配器的便利函數"""
    return FinMindAdapter(config)

# 全局適配器實例
_global_adapter: Optional[FinMindAdapter] = None

def get_global_finmind_adapter() -> FinMindAdapter:
    """獲取全局FinMind適配器"""
    global _global_adapter
    if _global_adapter is None:
        _global_adapter = create_finmind_adapter()
    return _global_adapter