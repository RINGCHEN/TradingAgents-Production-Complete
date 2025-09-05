#!/usr/bin/env python3
"""
TradingAgents 預設配置文件
包含 AI 分析師系統的所有配置參數
"""

import os
from typing import Dict, Any, List
from enum import Enum
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class LLMProvider(Enum):
    """LLM 提供商枚舉"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GPT_OSS = "gpt_oss"

class AnalysisMode(Enum):
    """分析模式枚舉"""
    BASIC = "basic"          # 基礎分析
    STANDARD = "standard"    # 標準分析
    COMPREHENSIVE = "comprehensive"  # 全面分析

class MembershipTier(Enum):
    """會員等級枚舉"""
    FREE = "free"
    GOLD = "gold"
    DIAMOND = "diamond"

# 核心系統配置
DEFAULT_CONFIG: Dict[str, Any] = {
    
    # ==================== LLM 配置 ====================
    'llm_config': {
        'provider': LLMProvider.GPT_OSS.value,  # 優先使用本地 GPT-OSS
        'model': 'gpt-3.5-turbo',
        'temperature': 0.3,
        'max_tokens': 1000,
        'timeout': 30,
        'max_retries': 3,
        'retry_delay': 1,
        
        # API Keys (從環境變數讀取)
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY'),
        
        # GPT-OSS 本地推理配置
        'gpt_oss_url': os.getenv('GPT_OSS_URL', 'http://localhost:8080'),
        'gpt_oss_api_key': os.getenv('GPT_OSS_API_KEY'),
        'gpt_oss_model': 'gpt-oss',
        'gpt_oss_max_retries': 3,
        'gpt_oss_retry_delay': 1,
        'gpt_oss_timeout': 300,  # 本地推理可能較慢
        'gpt_oss_max_connections': 10,
        'gpt_oss_max_connections_per_host': 5,
        'gpt_oss_extra_params': {},  # 額外的 GPT-OSS 特定參數
        
        # 智能路由配置
        'enable_intelligent_routing': True,
        'provider_priority': ['gpt_oss', 'openai', 'anthropic'],  # 優先順序
        'fallback_on_error': True,
        'health_check_interval': 60,  # 健康檢查間隔（秒）
        
        # 模型配置
        'models': {
            'openai': {
                'gpt-3.5-turbo': {'max_tokens': 4096, 'cost_per_1k': 0.002},
                'gpt-4': {'max_tokens': 8192, 'cost_per_1k': 0.03},
                'gpt-4-turbo': {'max_tokens': 128000, 'cost_per_1k': 0.01}
            },
            'anthropic': {
                'claude-3-haiku': {'max_tokens': 200000, 'cost_per_1k': 0.00025},
                'claude-3-sonnet': {'max_tokens': 200000, 'cost_per_1k': 0.003},
                'claude-3-opus': {'max_tokens': 200000, 'cost_per_1k': 0.015}
            },
            'gpt_oss': {
                'gpt-oss': {'max_tokens': 4096, 'cost_per_1k': 0.000},  # 本地推理無成本
                'llama-3-8b': {'max_tokens': 8192, 'cost_per_1k': 0.000},
                'llama-3-8b-instruct': {'max_tokens': 8192, 'cost_per_1k': 0.000}
            }
        }
    },
    
    # ==================== 分析師配置 ====================
    'analysts_config': {
        'enabled_analysts': [
            'market_analyst',
            'fundamentals_analyst', 
            'news_analyst',
            'sentiment_analyst',
            'risk_analyst',
            'investment_planner'
        ],
        
        # 分析師權重配置
        'analyst_weights': {
            'market_analyst': 0.25,
            'fundamentals_analyst': 0.25,
            'news_analyst': 0.15,
            'sentiment_analyst': 0.15,
            'risk_analyst': 0.10,
            'investment_planner': 0.10
        },
        
        # 分析師專業領域
        'analyst_specialties': {
            'market_analyst': ['technical_analysis', 'price_trends', 'volume_analysis'],
            'fundamentals_analyst': ['financial_statements', 'valuation', 'growth_analysis'],
            'news_analyst': ['news_events', 'market_sentiment', 'event_impact'],
            'sentiment_analyst': ['social_media', 'investor_sentiment', 'market_psychology'],
            'risk_analyst': ['volatility', 'risk_assessment', 'portfolio_risk'],
            'investment_planner': ['strategy', 'portfolio_allocation', 'timing']
        }
    },
    
    # ==================== 多代理人協作配置 ====================
    'collaboration_config': {
        'max_debate_rounds': 2,
        'min_consensus_threshold': 0.6,
        'max_analysis_time': 300,  # 5分鐘
        'enable_debate': True,
        'enable_consensus_building': True,
        'debate_timeout': 60,  # 每輪辯論最大時間
        
        # 衝突解決策略
        'conflict_resolution': {
            'strategy': 'weighted_voting',  # weighted_voting, majority_rule, expert_override
            'uncertainty_threshold': 0.4,
            'conservative_fallback': True
        }
    },
    
    # ==================== 數據源配置 ====================
    'data_sources': {
        'finmind': {
            'enabled': True,
            'api_token': os.getenv('FINMIND_API_TOKEN'),
            'base_url': 'https://api.finmindtrade.com/api/v4',
            'timeout': 30,
            'max_retries': 3,
            'rate_limit': 100  # 每分鐘請求數
        },
        
        'finnhub': {
            'enabled': True,
            'api_token': os.getenv('FINNHUB_API_TOKEN'),
            'base_url': 'https://finnhub.io/api/v1',
            'timeout': 30,
            'max_retries': 3,
            'rate_limit': 60,  # 免費版每分鐘60次請求
            'cache_expiry': {
                'stock_candles': 300,     # 5分鐘
                'company_profile': 86400, # 1天
                'company_news': 1800,     # 30分鐘
                'earnings': 86400,        # 1天
                'financials': 86400 * 7,  # 7天
                'quote': 60               # 1分鐘
            }
        },
        
        'cache': {
            'enabled': True,
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'default_ttl': 300,  # 5分鐘
            'ttl_by_data_type': {
                'stock_price': 60,      # 1分鐘
                'financial_data': 3600, # 1小時
                'news_data': 1800,      # 30分鐘
                'analysis_result': 1800 # 30分鐘
            }
        }
    },
    
    # ==================== 會員權限配置 ====================
    'membership_limits': {
        MembershipTier.FREE.value.upper(): {
            'max_analysts': 3,
            'max_daily_analyses': 10,
            'max_concurrent_analyses': 1,
            'analysis_timeout': 60,
            'available_analysts': [
                'market_analyst', 
                'fundamentals_analyst', 
                'news_analyst'
            ],
            'features': {
                'basic_analysis': True,
                'technical_indicators': True,
                'financial_data': False,
                'news_analysis': True,
                'sentiment_analysis': False,
                'risk_analysis': False,
                'debate_mode': False,
                'historical_data_days': 30
            }
        },
        
        MembershipTier.GOLD.value.upper(): {
            'max_analysts': 5,
            'max_daily_analyses': 100,
            'max_concurrent_analyses': 3,
            'analysis_timeout': 180,
            'available_analysts': [
                'market_analyst',
                'fundamentals_analyst', 
                'news_analyst',
                'sentiment_analyst',
                'risk_analyst'
            ],
            'features': {
                'basic_analysis': True,
                'technical_indicators': True,
                'financial_data': True,
                'news_analysis': True,
                'sentiment_analysis': True,
                'risk_analysis': True,
                'debate_mode': True,
                'historical_data_days': 365
            }
        },
        
        MembershipTier.DIAMOND.value.upper(): {
            'max_analysts': 6,
            'max_daily_analyses': -1,  # 無限制
            'max_concurrent_analyses': 10,
            'analysis_timeout': 300,
            'available_analysts': 'all',
            'features': {
                'basic_analysis': True,
                'technical_indicators': True,
                'financial_data': True,
                'news_analysis': True,
                'sentiment_analysis': True,
                'risk_analysis': True,
                'debate_mode': True,
                'investment_planning': True,
                'custom_strategies': True,
                'historical_data_days': -1  # 無限制
            }
        }
    },
    
    # ==================== 技術指標配置 ====================
    'technical_indicators': {
        'enabled_indicators': [
            'sma', 'ema', 'rsi', 'macd', 'bollinger_bands',
            'stochastic', 'williams_r', 'cci', 'atr', 'obv'
        ],
        
        'default_periods': {
            'sma': [5, 10, 20, 50, 200],
            'ema': [12, 26],
            'rsi': 14,
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'bollinger_bands': {'period': 20, 'std_dev': 2},
            'stochastic': {'k_period': 14, 'd_period': 3},
            'williams_r': 14,
            'cci': 20,
            'atr': 14
        },
        
        'signal_thresholds': {
            'rsi': {'oversold': 30, 'overbought': 70},
            'stochastic': {'oversold': 20, 'overbought': 80},
            'williams_r': {'oversold': -80, 'overbought': -20},
            'cci': {'oversold': -100, 'overbought': 100}
        }
    },
    
    # ==================== 風險管理配置 ====================
    'risk_management': {
        'enabled': True,
        'max_position_size': 0.1,  # 最大部位比例
        'stop_loss_percentage': 0.05,  # 5% 停損
        'take_profit_percentage': 0.15,  # 15% 停利
        'max_portfolio_risk': 0.02,  # 2% VaR
        'correlation_threshold': 0.7,  # 相關性閾值
        
        'risk_levels': {
            'low': {'volatility_threshold': 0.15, 'max_leverage': 1.0},
            'medium': {'volatility_threshold': 0.25, 'max_leverage': 1.5},
            'high': {'volatility_threshold': 0.40, 'max_leverage': 2.0}
        }
    },
    
    # ==================== 系統性能配置 ====================
    'performance': {
        'max_concurrent_requests': 100,
        'request_timeout': 30,
        'database_pool_size': 20,
        'redis_pool_size': 10,
        'worker_threads': 4,
        
        # 快取策略
        'cache_strategy': {
            'enable_preloading': True,
            'preload_popular_stocks': ['2330', '2317', '2454', '2881'],
            'cache_warming_schedule': '0 8 * * 1-5',  # 工作日早上8點
            'max_cache_size': '1GB'
        }
    },
    
    # ==================== 監控和日誌配置 ====================
    'monitoring': {
        'enable_metrics': True,
        'metrics_port': 9090,
        'health_check_interval': 30,
        'alert_thresholds': {
            'response_time': 5.0,
            'error_rate': 0.05,
            'memory_usage': 0.8,
            'cpu_usage': 0.8
        },
        
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file_path': 'logs/tradingagents.log',
            'max_file_size': '10MB',
            'backup_count': 5,
            'enable_structured_logging': True
        }
    },
    
    # ==================== 安全配置 ====================
    'security': {
        'enable_rate_limiting': True,
        'rate_limit_per_minute': 60,
        'enable_input_validation': True,
        'max_input_length': 1000,
        'allowed_stock_symbols': r'^[A-Z0-9]{1,10}$',
        'enable_audit_logging': True,
        
        'jwt': {
            'secret_key': os.getenv('JWT_SECRET_KEY'),
            'algorithm': 'HS256',
            'access_token_expire_minutes': 30,
            'refresh_token_expire_days': 7
        }
    },
    
    # ==================== 調試配置 ====================
    'debug': {
        'enabled': os.getenv('ENVIRONMENT', 'development') == 'development',
        'log_llm_requests': False,
        'log_analysis_steps': True,
        'save_debug_data': False,
        'mock_external_apis': False,
        'enable_profiling': False
    },
    
    # ==================== 國際化配置 ====================
    'i18n': {
        'default_language': 'zh-TW',
        'supported_languages': ['zh-TW', 'zh-CN', 'en-US'],
        'timezone': 'Asia/Taipei',
        'currency': 'TWD',
        'date_format': '%Y-%m-%d',
        'time_format': '%H:%M:%S'
    }
}

# ==================== 配置驗證函數 ====================

def validate_config(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    驗證配置的完整性和正確性
    
    Args:
        config: 要驗證的配置，預設使用 DEFAULT_CONFIG
        
    Returns:
        驗證後的配置
        
    Raises:
        ValueError: 配置驗證失敗
    """
    if config is None:
        config = DEFAULT_CONFIG.copy()
    
    # 檢查必要的 API Keys 或本地服務
    llm_config = config.get('llm_config', {})
    has_openai = bool(llm_config.get('openai_api_key'))
    has_anthropic = bool(llm_config.get('anthropic_api_key'))
    has_gpt_oss = bool(llm_config.get('gpt_oss_url'))
    
    if not (has_openai or has_anthropic or has_gpt_oss):
        raise ValueError("至少需要設定一個 LLM 提供商 (OpenAI API Key、Anthropic API Key 或 GPT-OSS URL)")
    
    # 驗證 GPT-OSS 配置
    if has_gpt_oss:
        gpt_oss_url = llm_config.get('gpt_oss_url')
        if not gpt_oss_url or not isinstance(gpt_oss_url, str):
            raise ValueError("GPT-OSS URL 必須是有效的字符串")
        
        # 檢查智能路由配置
        if llm_config.get('enable_intelligent_routing', False):
            priority = llm_config.get('provider_priority', [])
            if not isinstance(priority, list) or len(priority) == 0:
                raise ValueError("啟用智能路由時，provider_priority 必須是非空列表")
    
    # 檢查數據源配置
    data_sources = config.get('data_sources', {})
    finmind_config = data_sources.get('finmind', {})
    if finmind_config.get('enabled') and not finmind_config.get('api_token'):
        print("警告: FinMind API Token 未設定，將使用免費額度")
    
    # 檢查會員權限配置
    membership_limits = config.get('membership_limits', {})
    for tier in [MembershipTier.FREE.value.upper(), MembershipTier.GOLD.value.upper(), MembershipTier.DIAMOND.value.upper()]:
        if tier not in membership_limits:
            raise ValueError(f"缺少會員等級配置: {tier}")
    
    # 檢查分析師配置
    analysts_config = config.get('analysts_config', {})
    enabled_analysts = analysts_config.get('enabled_analysts', [])
    if len(enabled_analysts) == 0:
        raise ValueError("至少需要啟用一個分析師")
    
    return config

def get_config_for_environment(env: str = None) -> Dict[str, Any]:
    """
    根據環境獲取配置
    
    Args:
        env: 環境名稱 ('development', 'testing', 'production')
        
    Returns:
        環境特定的配置
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    config = DEFAULT_CONFIG.copy()
    
    if env == 'development':
        # 開發環境配置調整
        config['debug']['enabled'] = True
        config['debug']['log_analysis_steps'] = True
        config['llm_config']['temperature'] = 0.5
        config['monitoring']['logging']['level'] = 'DEBUG'
        
    elif env == 'testing':
        # 測試環境配置調整
        config['debug']['mock_external_apis'] = True
        config['data_sources']['cache']['default_ttl'] = 60
        config['collaboration_config']['max_analysis_time'] = 60
        
    elif env == 'production':
        # 生產環境配置調整
        config['debug']['enabled'] = False
        config['debug']['log_llm_requests'] = False
        config['security']['enable_rate_limiting'] = True
        config['monitoring']['enable_metrics'] = True
        config['performance']['max_concurrent_requests'] = 200
    
    return validate_config(config)

def get_analyst_config(analyst_id: str) -> Dict[str, Any]:
    """
    獲取特定分析師的配置
    
    Args:
        analyst_id: 分析師 ID
        
    Returns:
        分析師配置
    """
    config = DEFAULT_CONFIG['analysts_config']
    
    if analyst_id not in config['enabled_analysts']:
        raise ValueError(f"分析師 {analyst_id} 未啟用")
    
    return {
        'weight': config['analyst_weights'].get(analyst_id, 0.1),
        'specialties': config['analyst_specialties'].get(analyst_id, []),
        'llm_config': DEFAULT_CONFIG['llm_config'].copy()
    }

def get_membership_config(tier: str) -> Dict[str, Any]:
    """
    獲取會員等級配置
    
    Args:
        tier: 會員等級
        
    Returns:
        會員配置
    """
    membership_limits = DEFAULT_CONFIG['membership_limits']
    tier_upper = tier.upper()
    
    if tier_upper not in membership_limits:
        raise ValueError(f"不支援的會員等級: {tier}")
    
    return membership_limits[tier_upper].copy()

# ==================== 配置常數 ====================

# 支援的股票市場
SUPPORTED_MARKETS = {
    'TW': 'Taiwan Stock Exchange',
    'US': 'US Stock Market', 
    'HK': 'Hong Kong Stock Exchange'
}

# 分析結果信心度等級
CONFIDENCE_LEVELS = {
    'very_low': (0.0, 0.2),
    'low': (0.2, 0.4),
    'medium': (0.4, 0.6),
    'high': (0.6, 0.8),
    'very_high': (0.8, 1.0)
}

# 投資建議類型
RECOMMENDATION_TYPES = {
    'STRONG_BUY': 'strong_buy',
    'BUY': 'buy',
    'HOLD': 'hold',
    'SELL': 'sell',
    'STRONG_SELL': 'strong_sell'
}

# 風險等級
RISK_LEVELS = {
    'VERY_LOW': 'very_low',
    'LOW': 'low', 
    'MEDIUM': 'medium',
    'HIGH': 'high',
    'VERY_HIGH': 'very_high'
}

if __name__ == "__main__":
    # 配置驗證測試
    try:
        config = get_config_for_environment()
        print("✅ 配置驗證通過")
        print(f"📊 啟用的分析師: {config['analysts_config']['enabled_analysts']}")
        print(f"🔧 LLM 提供商: {config['llm_config']['provider']}")
        print(f"🌍 環境: {os.getenv('ENVIRONMENT', 'development')}")
    except Exception as e:
        print(f"❌ 配置驗證失敗: {e}")