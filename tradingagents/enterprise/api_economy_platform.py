"""
API Economy Platform
Developer ecosystem and API marketplace for TradingAgents platform
Task 4.3.3: API經濟平台

Features:
- Developer portal and documentation
- API marketplace and monetization
- SDK and developer tools
- Partner ecosystem management
- Usage analytics and billing
- API versioning and lifecycle management
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path
import logging
import os
from pathlib import Path
import uuid
import os
from pathlib import Path
from abc import ABC, abstractmethod

class APITier(Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class APICategory(Enum):
    MARKET_DATA = "market_data"
    AI_ANALYTICS = "ai_analytics"
    TRADING_SIGNALS = "trading_signals"
    RISK_MANAGEMENT = "risk_management"
    COMPLIANCE = "compliance"
    NOTIFICATIONS = "notifications"

class DeveloperTier(Enum):
    INDIVIDUAL = "individual"
    STARTUP = "startup"
    SME = "sme"
    ENTERPRISE = "enterprise"
    PARTNER = "partner"

class BillingModel(Enum):
    PAY_PER_CALL = "pay_per_call"
    SUBSCRIPTION = "subscription"
    REVENUE_SHARE = "revenue_share"
    FREEMIUM = "freemium"

@dataclass
class APIProduct:
    """API product definition"""
    product_id: str
    product_name: str
    category: APICategory
    description: str
    version: str
    endpoints: List[str]
    pricing_tiers: Dict[APITier, Dict[str, Any]]
    rate_limits: Dict[APITier, int]
    features: List[str]
    documentation_url: str
    created_at: datetime
    status: str = "active"
    provider: str = "TradingAgents"

@dataclass
class DeveloperAccount:
    """Developer account information"""
    developer_id: str
    email: str
    company_name: Optional[str]
    developer_tier: DeveloperTier
    api_keys: Dict[str, str]
    subscriptions: List[str]
    usage_quota: Dict[str, int]
    billing_info: Dict[str, Any]
    created_at: datetime
    status: str = "active"
    verification_status: str = "pending"

@dataclass
class APIUsageMetrics:
    """API usage tracking and analytics"""
    developer_id: str
    api_product_id: str
    period: str
    total_calls: int
    successful_calls: int
    error_calls: int
    average_response_time: float
    data_transferred_mb: float
    revenue_generated: float
    top_endpoints: List[Dict[str, Any]]
    timestamp: datetime

@dataclass
class PartnerIntegration:
    """Third-party partner integration"""
    partner_id: str
    partner_name: str
    integration_type: str  # "data_provider", "technology_partner", "reseller"
    api_products: List[str]
    revenue_share_percent: float
    technical_contact: str
    business_contact: str
    integration_status: str = "active"
    certification_level: str = "standard"

class APIDocumentationGenerator:
    """Generates API documentation and examples"""
    
    def __init__(self):
        self.templates = {}
        self.code_examples = {}
        
    def generate_api_docs(self, api_product: APIProduct) -> Dict[str, Any]:
        """Generate comprehensive API documentation"""
        
        documentation = {
            "api_name": api_product.product_name,
            "version": api_product.version,
            "category": api_product.category.value,
            "description": api_product.description,
            "base_url": f"https://api.tradingagents.com/{api_product.category.value}/v{api_product.version}",
            "authentication": {
                "type": "API Key",
                "header": "X-API-Key",
                "description": "Include your API key in the request header"
            },
            "rate_limits": api_product.rate_limits,
            "endpoints": self._generate_endpoint_docs(api_product.endpoints),
            "code_examples": self._generate_code_examples(api_product),
            "error_codes": self._get_standard_error_codes(),
            "changelog": self._get_changelog(api_product.product_id),
            "sdk_support": {
                "python": f"tradingagents-python-sdk=={api_product.version}",
                "javascript": f"tradingagents-js-sdk@{api_product.version}",
                "java": f"com.tradingagents:sdk:{api_product.version}",
                "csharp": f"TradingAgents.SDK.{api_product.version}"
            }
        }
        
        return documentation
    
    def _generate_endpoint_docs(self, endpoints: List[str]) -> List[Dict[str, Any]]:
        """Generate documentation for API endpoints"""
        
        endpoint_docs = []
        
        for endpoint in endpoints:
            # Mock endpoint documentation
            if "market-data" in endpoint:
                doc = {
                    "endpoint": endpoint,
                    "method": "GET",
                    "description": "Retrieve real-time market data",
                    "parameters": [
                        {"name": "symbol", "type": "string", "required": True, "description": "Stock symbol"},
                        {"name": "interval", "type": "string", "required": False, "description": "Data interval (1m, 5m, 1h, 1d)"}
                    ],
                    "response_example": {
                        "symbol": "AAPL",
                        "price": 150.25,
                        "change": 2.50,
                        "volume": 1000000,
                        "timestamp": "2025-08-10T15:30:00Z"
                    }
                }
            elif "ai-analysis" in endpoint:
                doc = {
                    "endpoint": endpoint,
                    "method": "POST",
                    "description": "Get AI-powered investment analysis",
                    "parameters": [
                        {"name": "symbol", "type": "string", "required": True, "description": "Stock symbol to analyze"},
                        {"name": "analysis_type", "type": "string", "required": False, "description": "Type of analysis (technical, fundamental, sentiment)"}
                    ],
                    "response_example": {
                        "symbol": "AAPL",
                        "analysis_score": 8.5,
                        "recommendation": "BUY",
                        "confidence": 0.92,
                        "key_factors": ["strong_earnings", "positive_sentiment", "technical_breakout"]
                    }
                }
            else:
                doc = {
                    "endpoint": endpoint,
                    "method": "GET",
                    "description": f"API endpoint for {endpoint}",
                    "parameters": [],
                    "response_example": {"status": "success", "data": {}}
                }
                
            endpoint_docs.append(doc)
        
        return endpoint_docs
    
    def _generate_code_examples(self, api_product: APIProduct) -> Dict[str, str]:
        """Generate code examples for different languages"""
        
        examples = {
            "python": f'''
import requests
import os
from pathlib import Path

# Initialize API client
api_key = "your_api_key_here"
base_url = "https://api.tradingagents.com/{api_product.category.value}/v{api_product.version}"

headers = {{
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}}

# Example API call
response = requests.get(f"{{base_url}}/market-data/AAPL", headers=headers)
data = response.json()
print(data)
            ''',
            "javascript": f'''
const axios = require('axios');

// Initialize API client
const apiKey = 'your_api_key_here';
const baseUrl = 'https://api.tradingagents.com/{api_product.category.value}/v{api_product.version}';

const headers = {{
    'X-API-Key': apiKey,
    'Content-Type': 'application/json'
}};

// Example API call
axios.get(`${{baseUrl}}/market-data/AAPL`, {{ headers }})
    .then(response => console.log(response.data))
    .catch(error => console.error(error));
            ''',
            "curl": f'''
curl -X GET "https://api.tradingagents.com/{api_product.category.value}/v{api_product.version}/market-data/AAPL" \\
  -H "X-API-Key: your_api_key_here" \\
  -H "Content-Type: application/json"
            '''
        }
        
        return examples
    
    def _get_standard_error_codes(self) -> Dict[str, str]:
        """Get standard API error codes"""
        
        return {
            "400": "Bad Request - Invalid parameters",
            "401": "Unauthorized - Invalid API key",
            "403": "Forbidden - Insufficient permissions",
            "404": "Not Found - Resource not found",
            "429": "Too Many Requests - Rate limit exceeded",
            "500": "Internal Server Error - Server error",
            "503": "Service Unavailable - Service temporarily unavailable"
        }
    
    def _get_changelog(self, product_id: str) -> List[Dict[str, Any]]:
        """Get API changelog"""
        
        return [
            {
                "version": "1.2.0",
                "date": "2025-08-10",
                "changes": ["Added AI sentiment analysis", "Improved response times", "New WebSocket support"]
            },
            {
                "version": "1.1.0", 
                "date": "2025-07-15",
                "changes": ["Multi-market support", "Enhanced error handling", "Rate limit improvements"]
            }
        ]

class DeveloperPortalManager:
    """Manages developer portal and onboarding"""
    
    def __init__(self):
        self.developers = {}
        self.api_keys = {}
        self.onboarding_flows = {}
        
    async def register_developer(
        self,
        email: str,
        company_name: Optional[str] = None,
        developer_tier: DeveloperTier = DeveloperTier.INDIVIDUAL
    ) -> DeveloperAccount:
        """Register new developer account"""
        
        developer_id = f"dev_{uuid.uuid4().hex[:8]}"
        api_key = f"ta_api_{secrets.token_urlsafe(32)}" if 'secrets' in globals() else f"ta_api_{uuid.uuid4().hex}"
        
        developer_account = DeveloperAccount(
            developer_id=developer_id,
            email=email,
            company_name=company_name,
            developer_tier=developer_tier,
            api_keys={"primary": api_key},
            subscriptions=[],
            usage_quota=self._get_default_quota(developer_tier),
            billing_info={},
            created_at=datetime.now(timezone.utc),
            verification_status="email_sent"
        )
        
        self.developers[developer_id] = developer_account
        self.api_keys[api_key] = developer_id
        
        # Trigger onboarding flow
        await self._start_onboarding_flow(developer_account)
        
        return developer_account
    
    def _get_default_quota(self, developer_tier: DeveloperTier) -> Dict[str, int]:
        """Get default usage quota based on tier"""
        
        quotas = {
            DeveloperTier.INDIVIDUAL: {"api_calls": 1000, "data_mb": 100},
            DeveloperTier.STARTUP: {"api_calls": 10000, "data_mb": 1000},
            DeveloperTier.SME: {"api_calls": 50000, "data_mb": 5000},
            DeveloperTier.ENTERPRISE: {"api_calls": 500000, "data_mb": 50000},
            DeveloperTier.PARTNER: {"api_calls": 1000000, "data_mb": 100000}
        }
        
        return quotas.get(developer_tier, quotas[DeveloperTier.INDIVIDUAL])
    
    async def _start_onboarding_flow(self, developer: DeveloperAccount):
        """Start developer onboarding flow"""
        
        onboarding_steps = [
            {
                "step": 1,
                "title": "Email Verification",
                "description": "Verify your email address",
                "status": "pending"
            },
            {
                "step": 2,
                "title": "API Key Setup",
                "description": "Configure your API keys and test authentication",
                "status": "pending"
            },
            {
                "step": 3,
                "title": "Choose API Products",
                "description": "Select the API products you want to use",
                "status": "pending"
            },
            {
                "step": 4,
                "title": "First API Call",
                "description": "Make your first successful API call",
                "status": "pending"
            }
        ]
        
        self.onboarding_flows[developer.developer_id] = {
            "steps": onboarding_steps,
            "current_step": 1,
            "started_at": datetime.now(timezone.utc),
            "completed": False
        }
    
    async def verify_developer(self, developer_id: str) -> bool:
        """Verify developer account"""
        
        if developer_id in self.developers:
            self.developers[developer_id].verification_status = "verified"
            
            # Update onboarding flow
            if developer_id in self.onboarding_flows:
                self.onboarding_flows[developer_id]["steps"][0]["status"] = "completed"
                self.onboarding_flows[developer_id]["current_step"] = 2
            
            return True
        
        return False
    
    def get_developer_dashboard(self, developer_id: str) -> Dict[str, Any]:
        """Get developer dashboard data"""
        
        developer = self.developers.get(developer_id)
        if not developer:
            return {"error": "Developer not found"}
        
        # Mock usage statistics
        current_month_usage = {
            "api_calls": 750,
            "data_transferred_mb": 45,
            "success_rate": 99.2,
            "avg_response_time_ms": 120
        }
        
        return {
            "developer_info": {
                "developer_id": developer.developer_id,
                "email": developer.email,
                "company": developer.company_name,
                "tier": developer.developer_tier.value,
                "verification_status": developer.verification_status
            },
            "api_keys": len(developer.api_keys),
            "active_subscriptions": len(developer.subscriptions),
            "current_usage": current_month_usage,
            "usage_limits": developer.usage_quota,
            "utilization": {
                "api_calls": (current_month_usage["api_calls"] / developer.usage_quota["api_calls"] * 100),
                "data_mb": (current_month_usage["data_transferred_mb"] / developer.usage_quota["data_mb"] * 100)
            },
            "onboarding_status": self.onboarding_flows.get(developer_id, {})
        }

class APIMarketplaceManager:
    """Manages API marketplace and monetization"""
    
    def __init__(self):
        self.api_products = {}
        self.subscriptions = {}
        self.billing_records = {}
        self.usage_analytics = {}
        
    def create_api_product(
        self,
        product_name: str,
        category: APICategory,
        description: str,
        endpoints: List[str],
        pricing_config: Dict[APITier, Dict[str, Any]]
    ) -> APIProduct:
        """Create new API product"""
        
        product_id = f"api_{category.value}_{uuid.uuid4().hex[:8]}"
        
        # Default rate limits
        rate_limits = {
            APITier.FREE: 100,      # 100 calls/hour
            APITier.BASIC: 1000,    # 1K calls/hour
            APITier.PRO: 10000,     # 10K calls/hour
            APITier.ENTERPRISE: 100000,  # 100K calls/hour
            APITier.CUSTOM: 1000000      # 1M calls/hour
        }
        
        api_product = APIProduct(
            product_id=product_id,
            product_name=product_name,
            category=category,
            description=description,
            version="1.0.0",
            endpoints=endpoints,
            pricing_tiers=pricing_config,
            rate_limits=rate_limits,
            features=self._get_product_features(category),
            documentation_url=f"https://docs.tradingagents.com/api/{product_id}",
            created_at=datetime.now(timezone.utc)
        )
        
        self.api_products[product_id] = api_product
        return api_product
    
    def _get_product_features(self, category: APICategory) -> List[str]:
        """Get features for API product category"""
        
        features_map = {
            APICategory.MARKET_DATA: [
                "Real-time market data",
                "Historical data access", 
                "Multiple market support",
                "WebSocket streaming"
            ],
            APICategory.AI_ANALYTICS: [
                "AI-powered analysis",
                "Sentiment analysis",
                "Price prediction",
                "Risk assessment"
            ],
            APICategory.TRADING_SIGNALS: [
                "Buy/sell signals",
                "Technical indicators",
                "Strategy backtesting",
                "Performance analytics"
            ]
        }
        
        return features_map.get(category, [])
    
    async def subscribe_to_product(
        self,
        developer_id: str,
        product_id: str,
        tier: APITier
    ) -> Dict[str, Any]:
        """Subscribe developer to API product"""
        
        if product_id not in self.api_products:
            return {"error": "Product not found"}
        
        subscription_id = f"sub_{uuid.uuid4().hex[:8]}"
        api_product = self.api_products[product_id]
        pricing = api_product.pricing_tiers.get(tier, {})
        
        subscription = {
            "subscription_id": subscription_id,
            "developer_id": developer_id,
            "product_id": product_id,
            "tier": tier.value,
            "pricing": pricing,
            "rate_limit": api_product.rate_limits[tier],
            "started_at": datetime.now(timezone.utc),
            "status": "active",
            "next_billing": datetime.now(timezone.utc) + timedelta(days=30)
        }
        
        self.subscriptions[subscription_id] = subscription
        
        return {
            "subscription_id": subscription_id,
            "status": "success",
            "message": f"Successfully subscribed to {api_product.product_name} ({tier.value} tier)",
            "rate_limit": api_product.rate_limits[tier],
            "billing_info": pricing
        }
    
    def get_marketplace_catalog(self, category: Optional[APICategory] = None) -> List[Dict[str, Any]]:
        """Get API marketplace catalog"""
        
        products = list(self.api_products.values())
        
        if category:
            products = [p for p in products if p.category == category]
        
        catalog = []
        for product in products:
            catalog.append({
                "product_id": product.product_id,
                "product_name": product.product_name,
                "category": product.category.value,
                "description": product.description,
                "version": product.version,
                "pricing_tiers": {
                    tier.value: pricing for tier, pricing in product.pricing_tiers.items()
                },
                "features": product.features,
                "documentation_url": product.documentation_url,
                "provider": product.provider
            })
        
        return catalog
    
    async def track_api_usage(
        self,
        developer_id: str,
        product_id: str,
        endpoint: str,
        response_time_ms: float,
        status_code: int,
        data_size_mb: float = 0.0
    ):
        """Track API usage for analytics and billing"""
        
        usage_key = f"{developer_id}_{product_id}_{datetime.now().strftime('%Y%m%d')}"
        
        if usage_key not in self.usage_analytics:
            self.usage_analytics[usage_key] = {
                "developer_id": developer_id,
                "product_id": product_id,
                "date": datetime.now().date().isoformat(),
                "total_calls": 0,
                "successful_calls": 0,
                "error_calls": 0,
                "total_response_time": 0.0,
                "data_transferred_mb": 0.0,
                "endpoint_usage": {}
            }
        
        usage = self.usage_analytics[usage_key]
        usage["total_calls"] += 1
        usage["total_response_time"] += response_time_ms
        usage["data_transferred_mb"] += data_size_mb
        
        if 200 <= status_code < 400:
            usage["successful_calls"] += 1
        else:
            usage["error_calls"] += 1
        
        # Track endpoint usage
        if endpoint not in usage["endpoint_usage"]:
            usage["endpoint_usage"][endpoint] = 0
        usage["endpoint_usage"][endpoint] += 1

class PartnerEcosystemManager:
    """Manages partner integrations and ecosystem"""
    
    def __init__(self):
        self.partners = {}
        self.integrations = {}
        self.certification_programs = {}
        
    def register_partner(
        self,
        partner_name: str,
        integration_type: str,
        technical_contact: str,
        business_contact: str
    ) -> PartnerIntegration:
        """Register new partner"""
        
        partner_id = f"partner_{uuid.uuid4().hex[:8]}"
        
        partner = PartnerIntegration(
            partner_id=partner_id,
            partner_name=partner_name,
            integration_type=integration_type,
            api_products=[],
            revenue_share_percent=20.0 if integration_type == "reseller" else 0.0,
            technical_contact=technical_contact,
            business_contact=business_contact
        )
        
        self.partners[partner_id] = partner
        return partner
    
    def get_partner_ecosystem_stats(self) -> Dict[str, Any]:
        """Get partner ecosystem statistics"""
        
        total_partners = len(self.partners)
        partner_types = {}
        
        for partner in self.partners.values():
            partner_type = partner.integration_type
            partner_types[partner_type] = partner_types.get(partner_type, 0) + 1
        
        return {
            "total_partners": total_partners,
            "partner_types": partner_types,
            "active_integrations": len([p for p in self.partners.values() if p.integration_status == "active"]),
            "certified_partners": len([p for p in self.partners.values() if p.certification_level in ["gold", "platinum"]])
        }

class APIEconomyPlatform:
    """Main API economy platform orchestrator"""
    
    def __init__(self):
        self.documentation_generator = APIDocumentationGenerator()
        self.developer_portal = DeveloperPortalManager()
        self.marketplace = APIMarketplaceManager()
        self.partner_ecosystem = PartnerEcosystemManager()
        self.logger = logging.getLogger(__name__)
        
        # Initialize platform
        self._initialize_platform()
        
    def _initialize_platform(self):
        """Initialize API economy platform"""
        
        # Create core API products
        self._create_core_api_products()
        
        # Setup partner ecosystem
        self._setup_partner_ecosystem()
        
    def _create_core_api_products(self):
        """Create core API products"""
        
        # Market Data API
        market_data_pricing = {
            APITier.FREE: {"price": 0, "billing_model": "freemium", "features": ["delayed_data"]},
            APITier.BASIC: {"price": 49, "billing_model": "subscription", "features": ["real_time_data", "basic_support"]},
            APITier.PRO: {"price": 199, "billing_model": "subscription", "features": ["real_time_data", "historical_data", "priority_support"]},
            APITier.ENTERPRISE: {"price": 999, "billing_model": "subscription", "features": ["all_features", "dedicated_support", "sla_99.9"]}
        }
        
        self.marketplace.create_api_product(
            "Market Data API",
            APICategory.MARKET_DATA,
            "Real-time and historical market data for global financial markets",
            ["/market-data/{symbol}", "/market-data/{symbol}/history", "/market-data/bulk"],
            market_data_pricing
        )
        
        # AI Analytics API
        ai_analytics_pricing = {
            APITier.FREE: {"price": 0, "billing_model": "freemium", "features": ["basic_analysis", "50_calls_month"]},
            APITier.BASIC: {"price": 99, "billing_model": "subscription", "features": ["advanced_analysis", "sentiment_analysis"]},
            APITier.PRO: {"price": 299, "billing_model": "subscription", "features": ["all_analysis", "custom_models", "backtesting"]},
            APITier.ENTERPRISE: {"price": 1499, "billing_model": "custom", "features": ["enterprise_models", "dedicated_infrastructure"]}
        }
        
        self.marketplace.create_api_product(
            "AI Analytics API",
            APICategory.AI_ANALYTICS,
            "AI-powered investment analysis and insights",
            ["/ai-analysis/{symbol}", "/ai-analysis/portfolio", "/ai-analysis/sentiment"],
            ai_analytics_pricing
        )
    
    def _setup_partner_ecosystem(self):
        """Setup initial partner ecosystem"""
        
        # Register sample partners
        self.partner_ecosystem.register_partner(
            "FinTech Solutions Inc",
            "technology_partner",
            "tech@fintech-solutions.com",
            "business@fintech-solutions.com"
        )
        
        self.partner_ecosystem.register_partner(
            "Market Data Pro",
            "data_provider",
            "api@marketdatapro.com",
            "partnerships@marketdatapro.com"
        )
    
    async def onboard_new_developer(
        self,
        email: str,
        company_name: Optional[str] = None,
        use_case: str = "general",
        developer_tier: DeveloperTier = DeveloperTier.INDIVIDUAL
    ) -> Dict[str, Any]:
        """Complete developer onboarding process"""
        
        # Register developer
        developer = await self.developer_portal.register_developer(
            email, company_name, developer_tier
        )
        
        # Generate documentation access
        api_products = list(self.marketplace.api_products.values())
        documentation_links = []
        
        for product in api_products:
            docs = self.documentation_generator.generate_api_docs(product)
            documentation_links.append({
                "product_name": product.product_name,
                "documentation_url": docs["base_url"] + "/docs",
                "code_examples": docs["code_examples"]
            })
        
        # Create onboarding package
        onboarding_package = {
            "developer_account": {
                "developer_id": developer.developer_id,
                "api_key": developer.api_keys["primary"],
                "tier": developer.developer_tier.value,
                "verification_status": developer.verification_status
            },
            "getting_started": {
                "quick_start_guide": "https://docs.tradingagents.com/quickstart",
                "api_documentation": documentation_links,
                "sdk_downloads": {
                    "python": "pip install tradingagents-sdk",
                    "javascript": "npm install tradingagents-sdk",
                    "java": "Maven/Gradle dependency available"
                }
            },
            "marketplace_access": {
                "available_products": len(self.marketplace.api_products),
                "free_tier_available": True,
                "recommended_products": self._get_recommended_products(use_case)
            },
            "support_resources": {
                "community_forum": "https://community.tradingagents.com",
                "support_email": "developers@tradingagents.com",
                "status_page": "https://status.tradingagents.com"
            }
        }
        
        return onboarding_package
    
    def _get_recommended_products(self, use_case: str) -> List[str]:
        """Get recommended API products based on use case"""
        
        recommendations = {
            "general": ["Market Data API"],
            "trading_bot": ["Market Data API", "AI Analytics API"],
            "portfolio_management": ["AI Analytics API", "Risk Management API"],
            "research_platform": ["Market Data API", "AI Analytics API"],
            "fintech_app": ["Market Data API", "Trading Signals API"]
        }
        
        return recommendations.get(use_case, ["Market Data API"])
    
    def get_platform_analytics(self) -> Dict[str, Any]:
        """Get comprehensive platform analytics"""
        
        # Developer metrics
        total_developers = len(self.developer_portal.developers)
        active_developers = len([d for d in self.developer_portal.developers.values() if d.status == "active"])
        verified_developers = len([d for d in self.developer_portal.developers.values() if d.verification_status == "verified"])
        
        # API product metrics
        total_products = len(self.marketplace.api_products)
        total_subscriptions = len(self.marketplace.subscriptions)
        
        # Usage analytics
        total_api_calls = sum(
            usage["total_calls"] for usage in self.marketplace.usage_analytics.values()
        )
        
        successful_calls = sum(
            usage["successful_calls"] for usage in self.marketplace.usage_analytics.values()
        )
        
        success_rate = (successful_calls / total_api_calls * 100) if total_api_calls > 0 else 0
        
        # Partner ecosystem metrics
        partner_stats = self.partner_ecosystem.get_partner_ecosystem_stats()
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "developer_metrics": {
                "total_developers": total_developers,
                "active_developers": active_developers,
                "verified_developers": verified_developers,
                "verification_rate": (verified_developers / total_developers * 100) if total_developers > 0 else 0
            },
            "api_metrics": {
                "total_products": total_products,
                "total_subscriptions": total_subscriptions,
                "total_api_calls": total_api_calls,
                "success_rate": success_rate,
                "avg_response_time": 125  # Mock value
            },
            "revenue_metrics": {
                "monthly_recurring_revenue": total_subscriptions * 150,  # Mock calculation
                "api_call_revenue": total_api_calls * 0.001,  # Mock per-call pricing
                "total_revenue": total_subscriptions * 150 + total_api_calls * 0.001
            },
            "partner_ecosystem": partner_stats
        }
    
    def generate_developer_sdk(self, language: str, api_products: List[str]) -> Dict[str, Any]:
        """Generate SDK for developers"""
        
        sdk_info = {
            "language": language,
            "version": "1.2.0",
            "api_products": api_products,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "installation": "",
            "documentation": f"https://docs.tradingagents.com/sdks/{language}",
            "examples": {},
            "changelog": [
                {"version": "1.2.0", "changes": ["Added async support", "Improved error handling"]},
                {"version": "1.1.0", "changes": ["Multi-product support", "Enhanced authentication"]}
            ]
        }
        
        if language == "python":
            sdk_info["installation"] = "pip install tradingagents-sdk"
            sdk_info["examples"] = {
                "basic_usage": '''
from tradingagents import TradingAgentsClient

client = TradingAgentsClient(api_key="your_api_key")
data = client.market_data.get_quote("AAPL")
print(data)
                '''
            }
        elif language == "javascript":
            sdk_info["installation"] = "npm install tradingagents-sdk"
            sdk_info["examples"] = {
                "basic_usage": '''
const TradingAgents = require('tradingagents-sdk');

const client = new TradingAgents.Client({ apiKey: 'your_api_key' });
client.marketData.getQuote('AAPL')
  .then(data => console.log(data))
  .catch(error => console.error(error));
                '''
            }
        
        return sdk_info

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
    async def test_api_economy_platform():
        platform = APIEconomyPlatform()
        
        print("Testing API Economy Platform...")
        
        # Test developer onboarding
        print("\n1. Testing Developer Onboarding:")
        onboarding_result = await platform.onboard_new_developer(
            "developer@startup.com",
            "StartupTech Inc",
            "trading_bot",
            DeveloperTier.STARTUP
        )
        
        print(f"Developer registered: {onboarding_result['developer_account']['developer_id']}")
        print(f"API Key provided: {onboarding_result['developer_account']['api_key'][:20]}...")
        print(f"Recommended products: {', '.join(onboarding_result['marketplace_access']['recommended_products'])}")
        
        # Test marketplace catalog
        print("\n2. Testing Marketplace Catalog:")
        catalog = platform.marketplace.get_marketplace_catalog()
        print(f"Available API products: {len(catalog)}")
        
        for product in catalog:
            print(f"  - {product['product_name']} ({product['category']})")
            print(f"    Pricing tiers: {list(product['pricing_tiers'].keys())}")
        
        # Test API subscription
        print("\n3. Testing API Subscription:")
        developer_id = onboarding_result['developer_account']['developer_id']
        product_id = catalog[0]['product_id']
        
        subscription_result = await platform.marketplace.subscribe_to_product(
            developer_id, product_id, APITier.BASIC
        )
        print(f"Subscription result: {subscription_result['status']}")
        print(f"Rate limit: {subscription_result['rate_limit']} calls/hour")
        
        # Test usage tracking
        print("\n4. Testing Usage Analytics:")
        await platform.marketplace.track_api_usage(
            developer_id, product_id, "/market-data/AAPL", 45.2, 200, 0.1
        )
        await platform.marketplace.track_api_usage(
            developer_id, product_id, "/market-data/TSLA", 38.1, 200, 0.08
        )
        
        print("API usage tracked successfully")
        
        # Test SDK generation
        print("\n5. Testing SDK Generation:")
        python_sdk = platform.generate_developer_sdk("python", [product_id])
        print(f"Python SDK v{python_sdk['version']} generated")
        print(f"Installation: {python_sdk['installation']}")
        
        # Get platform analytics
        print("\n6. Platform Analytics:")
        analytics = platform.get_platform_analytics()
        
        print(f"Total developers: {analytics['developer_metrics']['total_developers']}")
        print(f"API products: {analytics['api_metrics']['total_products']}")
        print(f"Total subscriptions: {analytics['api_metrics']['total_subscriptions']}")
        print(f"Monthly revenue: ${analytics['revenue_metrics']['monthly_recurring_revenue']:,.2f}")
        print(f"Partners: {analytics['partner_ecosystem']['total_partners']}")
        
        return platform
    
    # Run test
    platform = asyncio.run(test_api_economy_platform())
    print("\nAPI Economy Platform test completed successfully!")