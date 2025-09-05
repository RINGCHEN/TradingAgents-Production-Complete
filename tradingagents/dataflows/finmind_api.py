#!/usr/bin/env python3
"""
TradingAgents FinMind API 整合
提供台灣股市數據獲取功能，支援會員權限控制和配額管理
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

from ..default_config import DEFAULT_CONFIG
from ..utils.user_context import UserContext

# 設置日誌
logger = logging.getLogger(__name__)

class DataType(Enum):
    """數據類型枚舉"""
    DAILY_PRICE = "TaiwanStockPrice"
    FINANCIAL_STATEMENT = "TaiwanStockFinancialStatements"
    BALANCE_SHEET = "TaiwanStockBalanceSheet"
    CASH_FLOW = "TaiwanStockCashFlowsStatement"
    MARKET_INDEX = "TaiwanStockIndex"
    INSTITUTIONAL_INVESTORS = "InstitutionalInvestors"

class StatementType(Enum):
    """財報類型枚舉"""
    INCOME = "income_statement"
    BALANCE_SHEET = "balance_sheet"
    CASH_FLOW = "cash_flow"

@dataclass
class FinMindRequest:
    """FinMind API 請求數據類"""
    dataset: str
    data_id: str
    start_date: str
    end_date: Optional[str] = None
    user_context: Optional[UserContext] = None
    
    def to_params(self) -> Dict[str, str]:
        """轉換為 API 參數"""
        params = {
            'dataset': self.dataset,
            'data_id': self.data_id,
            'start_date': self.start_date
        }
        if self.end_date:
            params['end_date'] = self.end_date
        return params

@dataclass
class FinMindResponse:
    """FinMind API 回應數據類"""
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    status_code: int = 200
    request_id: Optional[str] = None
    response_time: float = 0.0
    cached: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'status_code': self.status_code,
            'request_id': self.request_id,
            'response_time': self.response_time,
            'cached': self.cached
        }

class FinMindError(Exception):
    """FinMind 相關錯誤基類"""
    pass

class FinMindConfigError(FinMindError):
    """FinMind 配置錯誤"""
    pass

class FinMindAPIError(FinMindError):
    """FinMind API 錯誤"""
    pass

class FinMindPermissionError(FinMindError):
    """FinMind 權限錯誤"""
    pass

class FinMindQuotaError(FinMindError):
    """FinMind 配額錯誤"""
    pass

class FinMindAPI:
    """FinMind API 客戶端"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 FinMind API 客戶端
        
        Args:
            config: FinMind 配置，如果為 None 則使用預設配置
        """
        self.config = config or DEFAULT_CONFIG.get('data_sources', {}).get('finmind', {})
        self.base_url = self.config.get('base_url', 'https://api.finmindtrade.com/api/v4')
        self.api_token = self.config.get('api_token')
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)
        self.rate_limit = self.config.get('rate_limit', 100)  # 每分鐘請求數
        
        # 請求統計
        self.request_count = 0
        self.last_request_time: Optional[datetime] = None
        self.request_times: List[datetime] = []
        
        # 欄位映射（FinMind 原始欄位 -> 標準化欄位）
        self.field_mapping = {
            'max': 'high',
            'min': 'low',
            'Trading_Volume': 'volume',
            'Trading_money': 'amount',
            'open': 'open',
            'close': 'close',
            'date': 'date',
            'stock_id': 'stock_id'
        }
        
        # 快取過期時間（秒）
        self.cache_expiry = {
            'daily_price': 3600,      # 1小時
            'financial': 86400 * 7,   # 7天
            'market_index': 1800,     # 30分鐘
            'institutional': 3600     # 1小時
        }
    
    def _normalize_stock_id(self, stock_id: str) -> str:
        """標準化股票代號"""
        return stock_id.split('.')[0]
    
    def _check_permission(self, user_context: UserContext, data_type: str) -> bool:
        """檢查用戶權限"""
        if not user_context:
            return False
        
        # 基本股價數據所有會員都可以使用
        if data_type in ['daily_price', 'market_index']:
            return True
        
        # 財報數據需要黃金會員以上
        if data_type in ['financial', 'balance_sheet', 'cash_flow']:
            return user_context.membership_tier.value in ['GOLD', 'DIAMOND']
        
        # 法人數據需要鑽石會員
        if data_type == 'institutional':
            return user_context.membership_tier.value == 'DIAMOND'
        
        return False
    
    def _check_rate_limit(self) -> bool:
        """檢查速率限制"""
        now = datetime.now()
        
        # 清理一分鐘前的請求記錄
        cutoff_time = now - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # 檢查是否超過速率限制
        return len(self.request_times) < self.rate_limit
    
    def _update_request_stats(self):
        """更新請求統計"""
        now = datetime.now()
        self.request_count += 1
        self.last_request_time = now
        self.request_times.append(now)
    
    def _normalize_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """標準化數據格式"""
        normalized_data = []
        
        for item in raw_data:
            normalized_item = {}
            
            # 映射欄位名稱
            for raw_field, standard_field in self.field_mapping.items():
                if raw_field in item:
                    normalized_item[standard_field] = item[raw_field]
            
            # 保留未映射的欄位
            for field, value in item.items():
                if field not in self.field_mapping:
                    normalized_item[field] = value
            
            normalized_data.append(normalized_item)
        
        return normalized_data
    
    async def _make_request(self, request: FinMindRequest) -> FinMindResponse:
        """執行 API 請求"""
        start_time = time.time()
        
        # 檢查速率限制
        if not self._check_rate_limit():
            raise FinMindAPIError("API 請求速率超過限制，請稍後再試")
        
        # 構建請求參數
        params = request.to_params()
        if self.api_token:
            params['token'] = self.api_token
        
        # 執行請求（帶重試）
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                    async with session.get(f"{self.base_url}/data", params=params) as response:
                        response_data = await response.json()
                        
                        # 更新統計
                        self._update_request_stats()
                        
                        # 檢查回應狀態
                        if response.status == 200 and response_data.get('status') == 200:
                            data = response_data.get('data', [])
                            normalized_data = self._normalize_data(data)
                            
                            return FinMindResponse(
                                success=True,
                                data=normalized_data,
                                status_code=response.status,
                                response_time=time.time() - start_time
                            )
                        else:
                            error_msg = response_data.get('msg', f'HTTP {response.status}')
                            
                            # 檢查是否為權限錯誤
                            if 'permission' in error_msg.lower() or 'unauthorized' in error_msg.lower():
                                raise FinMindPermissionError(f"權限不足: {error_msg}")
                            
                            # 檢查是否為配額錯誤
                            if 'quota' in error_msg.lower() or 'limit' in error_msg.lower():
                                raise FinMindQuotaError(f"配額不足: {error_msg}")
                            
                            raise FinMindAPIError(f"API 錯誤: {error_msg}")
                
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"FinMind API 請求失敗，嘗試 {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # 指數退避
                    continue
                
                return FinMindResponse(
                    success=False,
                    error=f"網路錯誤: {str(e)}",
                    response_time=time.time() - start_time
                )
            
            except (FinMindPermissionError, FinMindQuotaError):
                # 權限和配額錯誤不重試
                raise
            
            except Exception as e:
                logger.error(f"FinMind API 未知錯誤，嘗試 {attempt + 1}/{self.max_retries}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                
                return FinMindResponse(
                    success=False,
                    error=f"未知錯誤: {str(e)}",
                    response_time=time.time() - start_time
                )
        
        # 所有重試都失敗
        return FinMindResponse(
            success=False,
            error="所有重試都失敗",
            response_time=time.time() - start_time
        )
    
    # ==================== 公開 API 方法 ====================
    
    async def get_daily_trading_info(
        self,
        user_context: UserContext,
        stock_id: str,
        date: str
    ) -> FinMindResponse:
        """
        獲取股票日成交資訊
        
        Args:
            user_context: 用戶上下文
            stock_id: 股票代號
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            FinMind 回應
        """
        # 檢查權限
        if not self._check_permission(user_context, 'daily_price'):
            raise FinMindPermissionError("獲取股價數據需要會員權限")
        
        # 標準化股票代號
        normalized_stock_id = self._normalize_stock_id(stock_id)
        
        # 構建請求
        request = FinMindRequest(
            dataset=DataType.DAILY_PRICE.value,
            data_id=normalized_stock_id,
            start_date=date,
            end_date=date,
            user_context=user_context
        )
        
        return await self._make_request(request)
    
    async def get_stock_price_history(
        self,
        user_context: UserContext,
        stock_id: str,
        start_date: str,
        end_date: str
    ) -> FinMindResponse:
        """
        獲取股票歷史價格數據
        
        Args:
            user_context: 用戶上下文
            stock_id: 股票代號
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)
            
        Returns:
            FinMind 回應
        """
        # 檢查權限
        if not self._check_permission(user_context, 'daily_price'):
            raise FinMindPermissionError("獲取股價數據需要會員權限")
        
        # 檢查歷史數據訪問權限
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        days_requested = (datetime.now() - start_dt).days
        
        can_access, reason = user_context.can_access_historical_data(days_requested)
        if not can_access:
            raise FinMindPermissionError(reason)
        
        # 標準化股票代號
        normalized_stock_id = self._normalize_stock_id(stock_id)
        
        # 構建請求
        request = FinMindRequest(
            dataset=DataType.DAILY_PRICE.value,
            data_id=normalized_stock_id,
            start_date=start_date,
            end_date=end_date,
            user_context=user_context
        )
        
        return await self._make_request(request)
    
    async def get_financial_statement(
        self,
        user_context: UserContext,
        stock_id: str,
        statement_type: str,
        year: int,
        quarter: int
    ) -> FinMindResponse:
        """
        獲取財報數據
        
        Args:
            user_context: 用戶上下文
            stock_id: 股票代號
            statement_type: 財報類型 ('income', 'balance_sheet', 'cash_flow')
            year: 年份
            quarter: 季度
            
        Returns:
            FinMind 回應
        """
        # 檢查權限
        if not self._check_permission(user_context, 'financial'):
            raise FinMindPermissionError("獲取財報數據需要黃金會員以上權限")
        
        # 映射財報類型到數據集
        dataset_mapping = {
            'income': DataType.FINANCIAL_STATEMENT.value,
            'balance_sheet': DataType.BALANCE_SHEET.value,
            'cash_flow': DataType.CASH_FLOW.value
        }
        
        if statement_type not in dataset_mapping:
            raise FinMindAPIError(f"不支援的財報類型: {statement_type}")
        
        # 標準化股票代號
        normalized_stock_id = self._normalize_stock_id(stock_id)
        
        # 構建日期（使用季度最後一個月的第一天）
        month = quarter * 3
        date = f"{year}-{month:02d}-01"
        
        # 構建請求
        request = FinMindRequest(
            dataset=dataset_mapping[statement_type],
            data_id=normalized_stock_id,
            start_date=date,
            user_context=user_context
        )
        
        return await self._make_request(request)
    
    async def get_market_index(
        self,
        user_context: UserContext,
        index_name: str = "TAIEX",
        date: str = None
    ) -> FinMindResponse:
        """
        獲取市場指數數據
        
        Args:
            user_context: 用戶上下文
            index_name: 指數名稱
            date: 日期 (YYYY-MM-DD)，預設為今天
            
        Returns:
            FinMind 回應
        """
        # 檢查權限
        if not self._check_permission(user_context, 'market_index'):
            raise FinMindPermissionError("獲取市場指數需要會員權限")
        
        # 預設日期為今天
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 構建請求
        request = FinMindRequest(
            dataset=DataType.MARKET_INDEX.value,
            data_id=index_name,
            start_date=date,
            end_date=date,
            user_context=user_context
        )
        
        return await self._make_request(request)
    
    async def get_institutional_investors(
        self,
        user_context: UserContext,
        stock_id: str,
        date: str
    ) -> FinMindResponse:
        """
        獲取三大法人買賣超數據
        
        Args:
            user_context: 用戶上下文
            stock_id: 股票代號
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            FinMind 回應
        """
        # 檢查權限
        if not self._check_permission(user_context, 'institutional'):
            raise FinMindPermissionError("獲取法人數據需要鑽石會員權限")
        
        # 標準化股票代號
        normalized_stock_id = self._normalize_stock_id(stock_id)
        
        # 構建請求
        request = FinMindRequest(
            dataset=DataType.INSTITUTIONAL_INVESTORS.value,
            data_id=normalized_stock_id,
            start_date=date,
            end_date=date,
            user_context=user_context
        )
        
        return await self._make_request(request)
    
    # ==================== 批次處理方法 ====================
    
    async def batch_get_stock_data(
        self,
        user_context: UserContext,
        stock_ids: List[str],
        date: str
    ) -> Dict[str, FinMindResponse]:
        """
        批次獲取多檔股票數據
        
        Args:
            user_context: 用戶上下文
            stock_ids: 股票代號列表
            date: 日期
            
        Returns:
            股票代號對應的回應字典
        """
        # 限制並發數量以避免超過速率限制
        semaphore = asyncio.Semaphore(5)
        
        async def get_single_stock(stock_id: str) -> tuple[str, FinMindResponse]:
            async with semaphore:
                try:
                    response = await self.get_daily_trading_info(user_context, stock_id, date)
                    return stock_id, response
                except Exception as e:
                    return stock_id, FinMindResponse(
                        success=False,
                        error=str(e)
                    )
        
        # 並行執行請求
        tasks = [get_single_stock(stock_id) for stock_id in stock_ids]
        results = await asyncio.gather(*tasks)
        
        return dict(results)
    
    # ==================== 工具方法 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            'request_count': self.request_count,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'rate_limit': self.rate_limit,
            'current_rate': len(self.request_times),
            'api_token_configured': bool(self.api_token),
            'base_url': self.base_url
        }
    
    def reset_stats(self):
        """重置統計信息"""
        self.request_count = 0
        self.last_request_time = None
        self.request_times = []
    
    async def health_check(self) -> Dict[str, Any]:
        """健康檢查"""
        try:
            # 使用簡單的市場指數請求進行健康檢查
            from ..utils.user_context import create_user_context
            test_context = create_user_context("health_check", "free")
            
            response = await self.get_market_index(test_context, "TAIEX")
            
            return {
                'status': 'healthy' if response.success else 'degraded',
                'api_accessible': response.success,
                'response_time': response.response_time,
                'error': response.error,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'api_accessible': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# ==================== 工具函數 ====================

def create_finmind_client(config: Optional[Dict[str, Any]] = None) -> FinMindAPI:
    """創建 FinMind 客戶端的便利函數"""
    return FinMindAPI(config)

def safe_get_field(data: Dict[str, Any], field_name: str, default: Any = None) -> Any:
    """安全獲取欄位值，處理欄位名稱變動"""
    possible_names = [field_name, field_name.lower(), field_name.upper()]
    for name in possible_names:
        if name in data:
            return data[name]
    return default

# ==================== 全局客戶端管理 ====================

_global_finmind_client: Optional[FinMindAPI] = None

def get_global_finmind_client() -> FinMindAPI:
    """獲取全局 FinMind 客戶端"""
    global _global_finmind_client
    if _global_finmind_client is None:
        _global_finmind_client = create_finmind_client()
    return _global_finmind_client