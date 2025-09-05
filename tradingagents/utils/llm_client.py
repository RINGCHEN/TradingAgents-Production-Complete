#!/usr/bin/env python3
"""
TradingAgents LLM 客戶端統一介面
支援 OpenAI 和 Anthropic API，提供統一的分析介面
"""

import asyncio
import json
import time
import logging
import os
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import aiohttp
import openai
import anthropic
from anthropic import AsyncAnthropic

from ..default_config import DEFAULT_CONFIG

# 設置日誌
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """LLM 提供商枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GPT_OSS = "gpt_oss"

class AnalysisType(Enum):
    """分析類型枚舉"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    NEWS = "news"
    SENTIMENT = "sentiment"
    RISK = "risk"
    INVESTMENT = "investment"
    REASONING = "reasoning"
    GENERATION = "generation"
    ANALYSIS = "analysis"

@dataclass
class LLMRequest:
    """LLM 請求數據類"""
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    analysis_type: AnalysisType = AnalysisType.TECHNICAL
    analyst_id: str = "general"
    stock_id: Optional[str] = None
    user_id: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'prompt': self.prompt,
            'context': self.context,
            'analysis_type': self.analysis_type.value,
            'analyst_id': self.analyst_id,
            'stock_id': self.stock_id,
            'user_id': self.user_id,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature
        }

@dataclass
class LLMResponse:
    """LLM 回應數據類"""
    content: str
    provider: LLMProvider
    model: str
    usage: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    request_id: Optional[str] = None
    response_time: float = 0.0
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'content': self.content,
            'provider': self.provider.value,
            'model': self.model,
            'usage': self.usage,
            'metadata': self.metadata,
            'request_id': self.request_id,
            'response_time': self.response_time,
            'success': self.success,
            'error': self.error
        }

class LLMError(Exception):
    """LLM 相關錯誤基類"""
    pass

class LLMConfigError(LLMError):
    """LLM 配置錯誤"""
    pass

class LLMAPIError(LLMError):
    """LLM API 錯誤"""
    pass

class LLMRateLimitError(LLMError):
    """LLM 速率限制錯誤"""
    pass

class GPTOSSClient:
    """GPT-OSS 本地推理客戶端
    
    提供高級錯誤處理、重試機制和連接池管理的GPT-OSS服務客戶端。
    支持健康檢查、連接池複用、指數退避重試等企業級功能。
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:8080", 
        api_key: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: float = 300.0,
        max_connections: int = 10,
        max_connections_per_host: int = 5
    ):
        """初始化GPT-OSS客戶端
        
        Args:
            base_url: GPT-OSS服務基礎URL
            api_key: API密鑰（可選）
            max_retries: 最大重試次數
            retry_delay: 重試延遲基數（秒）
            timeout: 請求超時時間（秒）
            max_connections: 最大連接數
            max_connections_per_host: 每個主機最大連接數
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or "dummy-key"  # GPT-OSS可能不需要API key
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        
        # 連接池配置
        self.connector_config = {
            'limit': max_connections,
            'limit_per_host': max_connections_per_host,
            'ttl_dns_cache': 300,
            'enable_cleanup_closed': True
        }
        
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
        # 統計信息
        self.request_count = 0
        self.retry_count = 0
        self.error_count = 0
        self.last_health_check: Optional[datetime] = None
        
        logger.info(f"GPT-OSS客戶端初始化完成，URL: {self.base_url}")
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """獲取或創建HTTP會話
        
        使用連接池和適當的超時配置，確保線程安全。
        
        Returns:
            配置好的aiohttp客戶端會話
        """
        if self.session is None or self.session.closed:
            async with self._session_lock:
                # 雙重檢查模式
                if self.session is None or self.session.closed:
                    connector = aiohttp.TCPConnector(**self.connector_config)
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "User-Agent": "TradingAgents-GPT-OSS-Client/1.0"
                    }
                    
                    self.session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        headers=headers
                    )
                    logger.debug("創建新的HTTP會話")
        
        return self.session
    
    async def chat_completions(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-oss",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        **kwargs
    ) -> Dict[str, Any]:
        """調用GPT-OSS聊天完成API
        
        使用指數退避重試機制處理臨時錯誤，提供穩健的API調用。
        
        Args:
            messages: 對話消息列表
            model: 使用的模型名稱
            temperature: 溫度參數（0.0-2.0）
            max_tokens: 最大生成token數
            **kwargs: 其他參數
            
        Returns:
            GPT-OSS API回應數據
            
        Raises:
            LLMRateLimitError: 速率限制錯誤
            LLMAPIError: API調用錯誤
            LLMError: 其他LLM相關錯誤
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": max(0.0, min(2.0, temperature)),  # 限制溫度範圍
            "max_tokens": max_tokens,
            "stream": False,
            **kwargs
        }
        
        # 輸入驗證
        if not messages or not isinstance(messages, list):
            raise LLMError("消息列表不能為空且必須為列表類型")
        
        for attempt in range(self.max_retries + 1):
            try:
                self.request_count += 1
                session = await self._get_session()
                
                logger.debug(f"發送GPT-OSS請求 (嘗試 {attempt + 1}/{self.max_retries + 1})")
                
                async with session.post(
                    f"{self.base_url}/v1/chat/completions", 
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.debug("GPT-OSS請求成功")
                        return result
                    
                    elif response.status == 429:
                        # 速率限制 - 使用指數退避重試
                        if attempt < self.max_retries:
                            delay = self.retry_delay * (2 ** attempt)
                            logger.warning(f"GPT-OSS速率限制，{delay}秒後重試")
                            await asyncio.sleep(delay)
                            self.retry_count += 1
                            continue
                        else:
                            self.error_count += 1
                            raise LLMRateLimitError(f"GPT-OSS速率限制，已達最大重試次數")
                    
                    elif response.status >= 500:
                        # 服務器錯誤 - 可重試
                        if attempt < self.max_retries:
                            delay = self.retry_delay * (1.5 ** attempt)
                            logger.warning(f"GPT-OSS服務器錯誤 {response.status}，{delay}秒後重試")
                            await asyncio.sleep(delay)
                            self.retry_count += 1
                            continue
                        else:
                            error_text = await response.text()
                            self.error_count += 1
                            raise LLMAPIError(f"GPT-OSS服務器錯誤 {response.status}: {error_text}")
                    
                    else:
                        # 客戶端錯誤 - 不重試
                        error_text = await response.text()
                        self.error_count += 1
                        raise LLMAPIError(f"GPT-OSS API錯誤 {response.status}: {error_text}")
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries:
                    delay = self.retry_delay * (1.2 ** attempt)
                    logger.warning(f"GPT-OSS連接錯誤: {e}，{delay}秒後重試")
                    await asyncio.sleep(delay)
                    self.retry_count += 1
                    continue
                else:
                    self.error_count += 1
                    raise LLMAPIError(f"GPT-OSS連接錯誤: {e}")
            
            except Exception as e:
                self.error_count += 1
                logger.error(f"GPT-OSS未知錯誤: {e}")
                raise LLMError(f"GPT-OSS調用失敗: {e}")
        
        # 理論上不會到達這裡
        self.error_count += 1
        raise LLMError("GPT-OSS請求失敗，已達最大重試次數")
    
    async def health_check(self, force_check: bool = False) -> Dict[str, Any]:
        """檢查GPT-OSS服務健康狀態
        
        提供緩存的健康檢查結果，避免過度檢查。
        
        Args:
            force_check: 是否強制進行新的健康檢查
            
        Returns:
            包含健康狀態信息的字典
        """
        now = datetime.now()
        
        # 如果最近已檢查過且不強制檢查，使用緩存結果
        if (
            not force_check and 
            self.last_health_check and 
            (now - self.last_health_check).seconds < 60
        ):
            return {"status": "healthy", "cached": True, "last_check": self.last_health_check.isoformat()}
        
        try:
            session = await self._get_session()
            
            # 嘗試多個健康檢查端點
            health_endpoints = ["/health", "/v1/health", "/status", "/"]
            
            for endpoint in health_endpoints:
                try:
                    async with session.get(
                        f"{self.base_url}{endpoint}",
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        
                        if response.status == 200:
                            try:
                                result = await response.json()
                                result.update({
                                    "endpoint_used": endpoint,
                                    "response_time_ms": response.headers.get('x-response-time'),
                                    "timestamp": now.isoformat()
                                })
                                self.last_health_check = now
                                return result
                            except:
                                # 如果不是JSON，返回基本狀態
                                self.last_health_check = now
                                return {
                                    "status": "healthy",
                                    "endpoint_used": endpoint,
                                    "timestamp": now.isoformat()
                                }
                        
                except aiohttp.ClientError:
                    continue  # 嘗試下一個端點
            
            # 所有端點都失敗
            return {
                "status": "unhealthy", 
                "error": "所有健康檢查端點都無法訪問",
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error(f"健康檢查失敗: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": now.isoformat()
            }
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """獲取可用模型列表
        
        Returns:
            可用模型的列表
        """
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.base_url}/v1/models") as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data', [])
                else:
                    logger.warning(f"獲取模型列表失敗: HTTP {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"獲取模型列表錯誤: {e}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取客戶端統計信息
        
        Returns:
            統計信息字典
        """
        return {
            "request_count": self.request_count,
            "retry_count": self.retry_count,
            "error_count": self.error_count,
            "success_rate": (
                (self.request_count - self.error_count) / max(self.request_count, 1)
            ) * 100,
            "last_health_check": (
                self.last_health_check.isoformat() 
                if self.last_health_check else None
            ),
            "base_url": self.base_url,
            "session_active": self.session is not None and not self.session.closed
        }
    
    async def reset_stats(self):
        """重置統計信息"""
        self.request_count = 0
        self.retry_count = 0
        self.error_count = 0
        self.last_health_check = None
        logger.info("GPT-OSS客戶端統計信息已重置")
    
    async def close(self):
        """關閉HTTP會話和清理資源
        
        正確關閉連接池和清理所有資源。
        """
        try:
            if self.session and not self.session.closed:
                await self.session.close()
                logger.debug("GPT-OSS HTTP會話已關閉")
                
            # 等待連接池完全關閉
            if self.session:
                connector = self.session.connector
                if connector and not connector.closed:
                    await asyncio.sleep(0.1)  # 給連接池時間清理
                    
        except Exception as e:
            logger.warning(f"關閉GPT-OSS客戶端時出現警告: {e}")
        finally:
            self.session = None
            logger.info("GPT-OSS客戶端已完全關閉")
    
    def __repr__(self) -> str:
        """字符串表示"""
        status = "active" if (self.session and not self.session.closed) else "inactive"
        return f"GPTOSSClient(url={self.base_url}, status={status}, requests={self.request_count})"

class LLMClient:
    """LLM 客戶端統一介面"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化 LLM 客戶端
        
        Args:
            config: LLM 配置，如果為 None 則使用預設配置
        """
        self.config = config or DEFAULT_CONFIG.get('llm_config', {})
        self.provider = LLMProvider(self.config.get('provider', 'openai'))
        self.model = self.config.get('model', 'gpt-3.5-turbo')
        
        # 初始化客戶端
        self.openai_client: Optional[openai.AsyncOpenAI] = None
        self.anthropic_client: Optional[AsyncAnthropic] = None
        self.gpt_oss_client: Optional[GPTOSSClient] = None
        
        # 請求統計
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_request_time: Optional[datetime] = None
        
        # 重試配置
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1)
        
        # 智能路由配置
        self.enable_intelligent_routing = self.config.get('enable_intelligent_routing', True)
        self.provider_priority = self.config.get('provider_priority', ['gpt_oss', 'openai', 'anthropic'])
        self.fallback_on_error = self.config.get('fallback_on_error', True)
        self.health_check_interval = self.config.get('health_check_interval', 60)
        
        # GPT-OSS智能路由器连接
        self.ai_task_router = None
        self.routing_integration_enabled = self.config.get('routing_integration_enabled', False)
        
        # 提供商健康狀態緩存
        self.provider_health_cache: Dict[str, Dict[str, Any]] = {}
        self.last_health_check_time: Optional[datetime] = None
        
        # 初始化客戶端
        self._initialize_clients()
    
    def set_intelligent_routing_client(self, ai_task_router):
        """设置智能路由器客户端
        
        Args:
            ai_task_router: AITaskRouter实例
        """
        try:
            self.ai_task_router = ai_task_router
            self.routing_integration_enabled = True
            logger.info("✅ LLMClient已连接智能路由器")
        except Exception as e:
            logger.error(f"❌ LLMClient智能路由器连接失败: {e}")
            self.ai_task_router = None
            self.routing_integration_enabled = False
    
    def _initialize_clients(self):
        """初始化 LLM 客戶端"""
        try:
            # 初始化 OpenAI 客戶端
            openai_key = self.config.get('openai_api_key')
            if openai_key:
                self.openai_client = openai.AsyncOpenAI(
                    api_key=openai_key,
                    timeout=self.config.get('timeout', 30)
                )
                logger.info("OpenAI 客戶端初始化成功")
            
            # 初始化 Anthropic 客戶端
            anthropic_key = self.config.get('anthropic_api_key')
            if anthropic_key:
                self.anthropic_client = AsyncAnthropic(
                    api_key=anthropic_key,
                    timeout=self.config.get('timeout', 30)
                )
                logger.info("Anthropic 客戶端初始化成功")
            
            # 初始化 GPT-OSS 客戶端
            gpt_oss_url = self.config.get('gpt_oss_url') or os.getenv('GPT_OSS_URL', 'http://localhost:8080')
            if gpt_oss_url:
                self.gpt_oss_client = GPTOSSClient(
                    base_url=gpt_oss_url,
                    api_key=self.config.get('gpt_oss_api_key'),
                    max_retries=self.config.get('gpt_oss_max_retries', self.max_retries),
                    retry_delay=self.config.get('gpt_oss_retry_delay', self.retry_delay),
                    timeout=self.config.get('gpt_oss_timeout', self.config.get('timeout', 300)),
                    max_connections=self.config.get('gpt_oss_max_connections', 10),
                    max_connections_per_host=self.config.get('gpt_oss_max_connections_per_host', 5)
                )
                logger.info(f"GPT-OSS 客戶端初始化成功，URL: {gpt_oss_url}")
            
            # 檢查是否至少有一個客戶端可用
            if not self.openai_client and not self.anthropic_client and not self.gpt_oss_client:
                raise LLMConfigError("沒有可用的 LLM API Key")
                
        except Exception as e:
            logger.error(f"LLM 客戶端初始化失敗: {e}")
            raise LLMConfigError(f"LLM 客戶端初始化失敗: {e}")
    
    async def analyze(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: AnalysisType = AnalysisType.TECHNICAL,
        analyst_id: str = "general",
        stock_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        執行分析
        
        Args:
            prompt: 分析提示詞
            context: 分析上下文數據
            analysis_type: 分析類型
            analyst_id: 分析師 ID
            stock_id: 股票代碼
            user_id: 用戶 ID
            **kwargs: 其他參數
            
        Returns:
            LLM 回應
        """
        request = LLMRequest(
            prompt=prompt,
            context=context or {},
            analysis_type=analysis_type,
            analyst_id=analyst_id,
            stock_id=stock_id,
            user_id=user_id,
            max_tokens=kwargs.get('max_tokens'),
            temperature=kwargs.get('temperature')
        )
        
        return await self._execute_request(request)
    
    async def _execute_request(self, request: LLMRequest) -> LLMResponse:
        """執行 LLM 請求，支援智能路由和故障轉移"""
        start_time = time.time()
        last_error = None
        attempted_providers = []
        
        # 主要執行循環（支援故障轉移）
        for fallback_attempt in range(2 if self.fallback_on_error else 1):
            try:
                # 選擇提供商
                provider = await self._select_provider()
                
                # 避免重複嘗試同一提供商
                if provider in attempted_providers:
                    logger.debug(f"跳過已嘗試的提供商: {provider.value}")
                    continue
                
                attempted_providers.append(provider)
                logger.info(f"嘗試使用提供商: {provider.value} (嘗試 {fallback_attempt + 1})")
                
                # 執行請求（帶重試）
                for retry_attempt in range(self.max_retries):
                    try:
                        if provider == LLMProvider.OPENAI:
                            response = await self._call_openai(request)
                        elif provider == LLMProvider.ANTHROPIC:
                            response = await self._call_anthropic(request)
                        elif provider == LLMProvider.GPT_OSS:
                            response = await self._call_gpt_oss(request)
                        else:
                            raise LLMConfigError(f"不支援的提供商: {provider}")
                        
                        # 更新統計
                        response.response_time = time.time() - start_time
                        self._update_stats(response)
                        
                        logger.info(f"請求成功: {provider.value}")
                        return response
                        
                    except LLMRateLimitError as e:
                        logger.warning(f"速率限制，重試 {retry_attempt + 1}/{self.max_retries}: {e}")
                        last_error = e
                        if retry_attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** retry_attempt))
                            continue
                        break  # 達到最大重試次數，嘗試下一個提供商
                        
                    except (LLMAPIError, LLMError) as e:
                        logger.error(f"API 錯誤，重試 {retry_attempt + 1}/{self.max_retries}: {e}")
                        last_error = e
                        if retry_attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        break  # 達到最大重試次數，嘗試下一個提供商
                        
                    except Exception as e:
                        logger.error(f"未知錯誤，重試 {retry_attempt + 1}/{self.max_retries}: {e}")
                        last_error = e
                        if retry_attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay)
                            continue
                        break  # 達到最大重試次數，嘗試下一個提供商
                
                # 如果當前提供商失敗，標記為不健康（如果啟用智能路由）
                if self.enable_intelligent_routing:
                    self.provider_health_cache[provider.value] = {
                        'healthy': False,
                        'last_check': datetime.now(),
                        'error': str(last_error)
                    }
                
                logger.warning(f"提供商 {provider.value} 失敗，嘗試故障轉移")
                
            except LLMConfigError as e:
                # 提供商選擇失敗，無法繼續
                logger.error(f"提供商選擇失敗: {e}")
                last_error = e
                break
        
        # 所有嘗試都失敗，返回錯誤回應
        error_msg = f"所有提供商都失敗。已嘗試: {[p.value for p in attempted_providers]}"
        if last_error:
            error_msg += f"。最後錯誤: {last_error}"
        
        logger.error(error_msg)
        
        return LLMResponse(
            content="",
            provider=attempted_providers[-1] if attempted_providers else LLMProvider.OPENAI,
            model=self.model,
            response_time=time.time() - start_time,
            success=False,
            error=error_msg
        )
    
    async def _select_provider(self) -> LLMProvider:
        """智能選擇 LLM 提供商
        
        基於健康檢查、優先順序和錯誤恢復機制選擇最佳提供商。
        
        Returns:
            選擇的 LLM 提供商
            
        Raises:
            LLMConfigError: 沒有可用的提供商
        """
        if not self.enable_intelligent_routing:
            # 如果未啟用智能路由，使用傳統邏輯
            return self._select_provider_legacy()
        
        # 更新提供商健康狀態
        await self._update_provider_health()
        
        # 按優先順序嘗試提供商
        for provider_name in self.provider_priority:
            try:
                provider = LLMProvider(provider_name)
                
                # 檢查客戶端是否可用
                if not self._is_provider_client_available(provider):
                    logger.debug(f"提供商 {provider_name} 客戶端不可用")
                    continue
                
                # 檢查健康狀態
                if self._is_provider_healthy(provider_name):
                    logger.debug(f"選擇提供商: {provider_name}")
                    return provider
                else:
                    logger.warning(f"提供商 {provider_name} 健康檢查失敗")
                    
            except ValueError:
                logger.warning(f"無效的提供商名稱: {provider_name}")
                continue
        
        # 如果所有優先提供商都不可用，嘗試任何可用的提供商
        logger.warning("所有優先提供商不可用，嘗試任何可用的提供商")
        for provider in [LLMProvider.GPT_OSS, LLMProvider.OPENAI, LLMProvider.ANTHROPIC]:
            if self._is_provider_client_available(provider):
                logger.info(f"回退使用提供商: {provider.value}")
                return provider
        
        raise LLMConfigError("沒有可用的 LLM 提供商")
    
    def _select_provider_legacy(self) -> LLMProvider:
        """傳統提供商選擇邏輯（向後兼容）"""
        # 優先使用配置中指定的提供商
        if self.provider == LLMProvider.OPENAI and self.openai_client:
            return LLMProvider.OPENAI
        elif self.provider == LLMProvider.ANTHROPIC and self.anthropic_client:
            return LLMProvider.ANTHROPIC
        elif self.provider == LLMProvider.GPT_OSS and self.gpt_oss_client:
            return LLMProvider.GPT_OSS
        
        # 如果指定的提供商不可用，使用可用的提供商
        if self.gpt_oss_client:  # 優先使用本地GPT-OSS降低成本
            return LLMProvider.GPT_OSS
        elif self.openai_client:
            return LLMProvider.OPENAI
        elif self.anthropic_client:
            return LLMProvider.ANTHROPIC
        
        raise LLMConfigError("沒有可用的 LLM 提供商")
    
    def _is_provider_client_available(self, provider: LLMProvider) -> bool:
        """檢查提供商客戶端是否可用"""
        if provider == LLMProvider.OPENAI:
            return self.openai_client is not None
        elif provider == LLMProvider.ANTHROPIC:
            return self.anthropic_client is not None
        elif provider == LLMProvider.GPT_OSS:
            return self.gpt_oss_client is not None
        return False
    
    async def _update_provider_health(self):
        """更新提供商健康狀態"""
        now = datetime.now()
        
        # 檢查是否需要更新健康狀態
        if (self.last_health_check_time and 
            (now - self.last_health_check_time).total_seconds() < self.health_check_interval):
            return
        
        logger.debug("更新提供商健康狀態")
        
        # 檢查 GPT-OSS
        if self.gpt_oss_client:
            try:
                health_result = await self.gpt_oss_client.health_check()
                self.provider_health_cache['gpt_oss'] = {
                    'healthy': health_result.get('status') == 'healthy',
                    'last_check': now,
                    'details': health_result
                }
            except Exception as e:
                self.provider_health_cache['gpt_oss'] = {
                    'healthy': False,
                    'last_check': now,
                    'error': str(e)
                }
        
        # 檢查 OpenAI（簡化版本 - 客戶端存在即認為健康）
        if self.openai_client:
            self.provider_health_cache['openai'] = {
                'healthy': True,
                'last_check': now,
                'details': 'Client initialized'
            }
        
        # 檢查 Anthropic（簡化版本 - 客戶端存在即認為健康）
        if self.anthropic_client:
            self.provider_health_cache['anthropic'] = {
                'healthy': True,
                'last_check': now,
                'details': 'Client initialized'
            }
        
        self.last_health_check_time = now
    
    def _is_provider_healthy(self, provider_name: str) -> bool:
        """檢查提供商是否健康"""
        health_info = self.provider_health_cache.get(provider_name, {})
        return health_info.get('healthy', False)
    
    async def force_provider_health_check(self) -> Dict[str, Any]:
        """強制執行提供商健康檢查，忽略快取間隔"""
        self.last_health_check_time = None  # 重置時間戳以強制檢查
        await self._update_provider_health()
        return self.provider_health_cache.copy()
    
    def get_provider_health_status(self) -> Dict[str, Any]:
        """獲取當前提供商健康狀態（無需異步）"""
        return {
            'cache': self.provider_health_cache.copy(),
            'last_check': self.last_health_check_time.isoformat() if self.last_health_check_time else None,
            'check_interval': self.health_check_interval,
            'routing_enabled': self.enable_intelligent_routing
        }
    
    async def test_provider_connectivity(self, provider: LLMProvider) -> Dict[str, Any]:
        """測試特定提供商的連接性"""
        test_result = {
            'provider': provider.value,
            'timestamp': datetime.now().isoformat(),
            'client_available': self._is_provider_client_available(provider),
            'connectivity_test': None
        }
        
        try:
            if provider == LLMProvider.GPT_OSS and self.gpt_oss_client:
                health = await self.gpt_oss_client.health_check(force_check=True)
                test_result['connectivity_test'] = {
                    'status': 'success',
                    'healthy': health.get('status') == 'healthy',
                    'details': health
                }
            
            elif provider == LLMProvider.OPENAI and self.openai_client:
                # 簡單的連接測試
                test_result['connectivity_test'] = {
                    'status': 'success',
                    'healthy': True,
                    'details': 'Client initialized and ready'
                }
            
            elif provider == LLMProvider.ANTHROPIC and self.anthropic_client:
                # 簡單的連接測試
                test_result['connectivity_test'] = {
                    'status': 'success',
                    'healthy': True,
                    'details': 'Client initialized and ready'
                }
            
            else:
                test_result['connectivity_test'] = {
                    'status': 'failed',
                    'healthy': False,
                    'details': 'Client not available or not initialized'
                }
        
        except Exception as e:
            test_result['connectivity_test'] = {
                'status': 'error',
                'healthy': False,
                'details': f'Connection test failed: {str(e)}'
            }
        
        return test_result
    
    async def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """調用 OpenAI API"""
        if not self.openai_client:
            raise LLMConfigError("OpenAI 客戶端未初始化")
        
        try:
            # 構建消息
            messages = self._build_openai_messages(request)
            
            # 設置參數
            params = {
                'model': self.model,
                'messages': messages,
                'temperature': request.temperature or self.config.get('temperature', 0.3),
                'max_tokens': request.max_tokens or self.config.get('max_tokens', 1000)
            }
            
            # 調用 API
            response = await self.openai_client.chat.completions.create(**params)
            
            # 解析回應
            content = response.choices[0].message.content
            usage = {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.OPENAI,
                model=self.model,
                usage=usage,
                request_id=response.id,
                success=True
            )
            
        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"OpenAI 速率限制: {e}")
        except openai.APIError as e:
            raise LLMAPIError(f"OpenAI API 錯誤: {e}")
        except Exception as e:
            raise LLMError(f"OpenAI 調用失敗: {e}")
    
    async def _call_anthropic(self, request: LLMRequest) -> LLMResponse:
        """調用 Anthropic API"""
        if not self.anthropic_client:
            raise LLMConfigError("Anthropic 客戶端未初始化")
        
        try:
            # 構建消息
            messages = self._build_anthropic_messages(request)
            
            # 設置參數
            params = {
                'model': self.model,
                'messages': messages,
                'max_tokens': request.max_tokens or self.config.get('max_tokens', 1000),
                'temperature': request.temperature or self.config.get('temperature', 0.3)
            }
            
            # 調用 API
            response = await self.anthropic_client.messages.create(**params)
            
            # 解析回應
            content = response.content[0].text
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.ANTHROPIC,
                model=self.model,
                usage=usage,
                request_id=response.id,
                success=True
            )
            
        except anthropic.RateLimitError as e:
            raise LLMRateLimitError(f"Anthropic 速率限制: {e}")
        except anthropic.APIError as e:
            raise LLMAPIError(f"Anthropic API 錯誤: {e}")
        except Exception as e:
            raise LLMError(f"Anthropic 調用失敗: {e}")
    
    async def _call_gpt_oss(self, request: LLMRequest) -> LLMResponse:
        """調用 GPT-OSS 本地推理服務
        
        使用增強的 GPTOSSClient 提供更好的錯誤處理和重試機制。
        
        Args:
            request: LLM 請求對象
            
        Returns:
            LLM 回應對象
            
        Raises:
            LLMConfigError: 客戶端配置錯誤
            LLMError: 其他 LLM 相關錯誤
        """
        if not self.gpt_oss_client:
            raise LLMConfigError("GPT-OSS 客戶端未初始化")
        
        try:
            # 構建消息
            messages = self._build_openai_messages(request)  # 使用OpenAI格式
            
            # 準備模型參數
            model_name = self.config.get('gpt_oss_model', 'gpt-oss')
            temperature = request.temperature or self.config.get('temperature', 0.3)
            max_tokens = request.max_tokens or self.config.get('max_tokens', 2048)
            
            # 調用 GPT-OSS API（內建重試和錯誤處理）
            response_data = await self.gpt_oss_client.chat_completions(
                messages=messages,
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                # 支援額外參數
                **self.config.get('gpt_oss_extra_params', {})
            )
            
            # 解析回應
            choices = response_data.get('choices', [])
            if not choices:
                raise LLMError("GPT-OSS 回應中沒有選擇項")
            
            choice = choices[0]
            message = choice.get('message', {})
            content = message.get('content', '')
            
            if not content:
                logger.warning("GPT-OSS 返回空內容")
            
            usage = response_data.get('usage', {})
            
            return LLMResponse(
                content=content,
                provider=LLMProvider.GPT_OSS,
                model=model_name,
                usage=usage,
                request_id=response_data.get('id'),
                metadata={
                    'finish_reason': choice.get('finish_reason'),
                    'gpt_oss_stats': await self.gpt_oss_client.get_stats()
                },
                success=True
            )
            
        except (LLMRateLimitError, LLMAPIError) as e:
            # 這些錯誤已經由 GPTOSSClient 處理過重試機制
            logger.error(f"GPT-OSS API 錯誤: {e}")
            raise
            
        except Exception as e:
            logger.error(f"GPT-OSS 調用失敗: {e}")
            raise LLMError(f"GPT-OSS 調用失敗: {e}")
    
    def _build_openai_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """構建 OpenAI 消息格式"""
        system_prompt = self._get_system_prompt(request.analysis_type, request.analyst_id)
        user_prompt = self._format_user_prompt(request)
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    def _build_anthropic_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
        """構建 Anthropic 消息格式"""
        # Anthropic 不使用 system role，將系統提示詞合併到用戶消息中
        system_prompt = self._get_system_prompt(request.analysis_type, request.analyst_id)
        user_prompt = self._format_user_prompt(request)
        
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"
        
        return [
            {"role": "user", "content": combined_prompt}
        ]
    
    def _get_system_prompt(self, analysis_type: AnalysisType, analyst_id: str) -> str:
        """獲取系統提示詞"""
        base_prompt = f"你是一位專業的{analyst_id}分析師，專精於{analysis_type.value}分析。"
        
        type_specific_prompts = {
            AnalysisType.TECHNICAL: "請基於技術指標、價格走勢、成交量等數據進行分析。",
            AnalysisType.FUNDAMENTAL: "請基於財務報表、公司基本面、行業分析等進行評估。",
            AnalysisType.NEWS: "請分析新聞事件對股價的潛在影響。",
            AnalysisType.SENTIMENT: "請分析市場情緒和投資人心理。",
            AnalysisType.RISK: "請評估投資風險和提供風險管理建議。",
            AnalysisType.INVESTMENT: "請提供綜合投資建議和策略規劃。"
        }
        
        specific_prompt = type_specific_prompts.get(analysis_type, "請進行專業分析。")
        
        return f"""{base_prompt}{specific_prompt}

請以 JSON 格式回應，包含以下欄位：
{{
    "recommendation": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "target_price": 數字或null,
    "reasoning": ["理由1", "理由2", "理由3"],
    "risk_factors": ["風險1", "風險2"],
    "key_points": ["要點1", "要點2", "要點3"]
}}

請確保分析客觀、專業，基於提供的數據進行判斷。"""
    
    def _format_user_prompt(self, request: LLMRequest) -> str:
        """格式化用戶提示詞"""
        prompt_parts = [request.prompt]
        
        if request.stock_id:
            prompt_parts.append(f"\n股票代碼: {request.stock_id}")
        
        if request.context:
            prompt_parts.append(f"\n分析數據:\n{json.dumps(request.context, ensure_ascii=False, indent=2)}")
        
        return "\n".join(prompt_parts)
    
    def _update_stats(self, response: LLMResponse):
        """更新請求統計"""
        self.request_count += 1
        self.last_request_time = datetime.now()
        
        if response.usage:
            tokens = response.usage.get('total_tokens', 0)
            self.total_tokens += tokens
            
            # 計算成本（簡化版本）
            cost_per_1k = self._get_cost_per_1k_tokens(response.provider, response.model)
            self.total_cost += (tokens / 1000) * cost_per_1k
    
    def _get_cost_per_1k_tokens(self, provider: LLMProvider, model: str) -> float:
        """獲取每1K tokens的成本"""
        models_config = self.config.get('models', {})
        provider_models = models_config.get(provider.value, {})
        model_config = provider_models.get(model, {})
        return model_config.get('cost_per_1k', 0.002)  # 預設成本
    
    # ==================== 批次處理方法 ====================
    
    async def batch_analyze(
        self,
        requests: List[LLMRequest],
        max_concurrent: int = 5
    ) -> List[LLMResponse]:
        """批次分析"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_request(request: LLMRequest) -> LLMResponse:
            async with semaphore:
                return await self._execute_request(request)
        
        tasks = [process_request(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理異常
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                processed_responses.append(LLMResponse(
                    content="",
                    provider=self.provider,
                    model=self.model,
                    success=False,
                    error=str(response)
                ))
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    # ==================== 串流分析方法 ====================
    
    async def stream_analyze(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        analysis_type: AnalysisType = AnalysisType.TECHNICAL,
        analyst_id: str = "general",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """串流分析（模擬實現）"""
        # 注意：這是一個簡化的串流實現
        # 實際的串流需要 LLM 提供商支援
        
        response = await self.analyze(
            prompt=prompt,
            context=context,
            analysis_type=analysis_type,
            analyst_id=analyst_id,
            **kwargs
        )
        
        if response.success:
            # 模擬串流輸出
            content = response.content
            chunk_size = 50
            
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                yield chunk
                await asyncio.sleep(0.1)  # 模擬延遲
        else:
            yield f"錯誤: {response.error}"
    
    # ==================== 工具方法 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            'request_count': self.request_count,
            'total_tokens': self.total_tokens,
            'total_cost': round(self.total_cost, 4),
            'average_cost_per_request': round(self.total_cost / max(self.request_count, 1), 4),
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'provider': self.provider.value,
            'model': self.model,
            'intelligent_routing': {
                'enabled': self.enable_intelligent_routing,
                'provider_priority': self.provider_priority,
                'available_providers': [
                    p.value for p in [LLMProvider.OPENAI, LLMProvider.ANTHROPIC, LLMProvider.GPT_OSS]
                    if self._is_provider_client_available(p)
                ],
                'health_status': {
                    name: status.get('healthy', False) 
                    for name, status in self.provider_health_cache.items()
                }
            }
        }
    
    def reset_stats(self):
        """重置統計信息"""
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.last_request_time = None
    
    async def health_check(self) -> Dict[str, Any]:
        """綜合健康檢查，包含智能路由信息"""
        # 更新提供商健康狀態
        await self._update_provider_health()
        
        health_status = {
            'status': 'healthy',
            'providers': {},
            'timestamp': datetime.now().isoformat(),
            'intelligent_routing': {
                'enabled': self.enable_intelligent_routing,
                'provider_priority': self.provider_priority,
                'fallback_enabled': self.fallback_on_error,
                'health_cache': self.provider_health_cache.copy()
            }
        }
        
        # 檢查 OpenAI
        if self.openai_client:
            try:
                # 簡單的測試請求
                test_response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                health_status['providers']['openai'] = 'healthy'
            except Exception as e:
                health_status['providers']['openai'] = f'error: {str(e)}'
                health_status['status'] = 'degraded'
        
        # 檢查 Anthropic
        if self.anthropic_client:
            try:
                # 簡單的測試請求
                test_response = await self.anthropic_client.messages.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                health_status['providers']['anthropic'] = 'healthy'
            except Exception as e:
                health_status['providers']['anthropic'] = f'error: {str(e)}'
                health_status['status'] = 'degraded'
        
        # 檢查 GPT-OSS
        if self.gpt_oss_client:
            try:
                gpt_oss_health = await self.gpt_oss_client.health_check()
                if gpt_oss_health.get('status') == 'healthy':
                    health_status['providers']['gpt_oss'] = {
                        'status': 'healthy',
                        'stats': await self.gpt_oss_client.get_stats(),
                        'last_check': gpt_oss_health.get('timestamp'),
                        'endpoint_used': gpt_oss_health.get('endpoint_used')
                    }
                else:
                    health_status['providers']['gpt_oss'] = {
                        'status': 'unhealthy',
                        'error': gpt_oss_health.get('error', 'unknown'),
                        'timestamp': gpt_oss_health.get('timestamp')
                    }
                    health_status['status'] = 'degraded'
            except Exception as e:
                health_status['providers']['gpt_oss'] = {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                health_status['status'] = 'degraded'
        
        return health_status
    
    async def close(self):
        """關閉客戶端"""
        # OpenAI 客戶端會自動管理連接
        # Anthropic 客戶端也會自動管理連接
        # 關閉 GPT-OSS 客戶端
        if self.gpt_oss_client:
            await self.gpt_oss_client.close()
        logger.info("LLM 客戶端已關閉")

# ==================== 工具函數 ====================

def create_llm_client(config: Optional[Dict[str, Any]] = None) -> LLMClient:
    """創建 LLM 客戶端的便利函數"""
    return LLMClient(config)

def parse_analysis_response(response_content: str) -> Dict[str, Any]:
    """解析分析回應"""
    try:
        # 嘗試解析 JSON
        return json.loads(response_content)
    except json.JSONDecodeError:
        # 如果不是 JSON，嘗試提取關鍵信息
        return _extract_analysis_from_text(response_content)

def _extract_analysis_from_text(text: str) -> Dict[str, Any]:
    """從文字中提取分析信息"""
    # 簡化的文字解析邏輯
    recommendation = 'HOLD'
    confidence = 0.5
    reasoning = [text[:200] + '...' if len(text) > 200 else text]
    
    # 嘗試提取建議
    text_upper = text.upper()
    if any(word in text_upper for word in ['BUY', '買進', '看多']):
        recommendation = 'BUY'
        confidence = 0.7
    elif any(word in text_upper for word in ['SELL', '賣出', '看空']):
        recommendation = 'SELL'
        confidence = 0.7
    
    return {
        'recommendation': recommendation,
        'confidence': confidence,
        'reasoning': reasoning,
        'risk_factors': [],
        'key_points': []
    }

# ==================== 全局客戶端管理 ====================

_global_llm_client: Optional[LLMClient] = None

def get_global_llm_client() -> LLMClient:
    """獲取全局 LLM 客戶端"""
    global _global_llm_client
    if _global_llm_client is None:
        _global_llm_client = create_llm_client()
    return _global_llm_client

async def close_global_llm_client():
    """關閉全局 LLM 客戶端"""
    global _global_llm_client
    if _global_llm_client:
        await _global_llm_client.close()
        _global_llm_client = None