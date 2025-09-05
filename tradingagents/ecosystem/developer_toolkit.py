"""
Developer Toolkit
Comprehensive tools for developers building on the TradingAgents platform
Task 4.4.2: 開發者工具套件

Features:
- Multi-language SDK generation and management
- Interactive API testing and debugging tools
- Code generators and templates
- Local development environment setup
- Testing and validation frameworks
- Performance monitoring and analytics
- Version management and migration tools
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
import uuid
import os
import subprocess
import tempfile
from abc import ABC, abstractmethod

class ProgrammingLanguage(Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CSHARP = "csharp"
    GO = "go"
    PHP = "php"
    RUBY = "ruby"

class SDKVersion(Enum):
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    NIGHTLY = "nightly"

class ToolType(Enum):
    SDK = "sdk"
    CLI = "cli"
    IDE_PLUGIN = "ide_plugin"
    TESTING_FRAMEWORK = "testing_framework"
    CODE_GENERATOR = "code_generator"
    DEBUGGER = "debugger"

@dataclass
class SDKConfiguration:
    """SDK configuration and metadata"""
    sdk_id: str
    language: ProgrammingLanguage
    version: str
    version_type: SDKVersion
    features: List[str]
    dependencies: Dict[str, str]
    api_endpoints: List[str]
    documentation_url: str
    examples_included: bool
    testing_suite: bool
    created_at: datetime
    last_updated: datetime
    download_count: int = 0
    github_url: Optional[str] = None

@dataclass
class CodeTemplate:
    """Code template for different use cases"""
    template_id: str
    template_name: str
    language: ProgrammingLanguage
    category: str  # "basic_api_call", "trading_bot", "data_analysis", etc.
    description: str
    code_content: str
    required_dependencies: List[str]
    usage_examples: List[str]
    created_at: datetime
    popularity_score: float = 0.0

@dataclass
class DeveloperProject:
    """Developer project configuration"""
    project_id: str
    project_name: str
    developer_id: str
    language: ProgrammingLanguage
    sdk_version: str
    api_keys: List[str]
    endpoints_used: List[str]
    created_at: datetime
    last_activity: datetime
    status: str = "active"

class SDKGenerator:
    """Generates SDKs for different programming languages"""
    
    def __init__(self):
        self.templates = {}
        self.generated_sdks = {}
        self.api_specs = {}
        
    async def generate_sdk(
        self,
        language: ProgrammingLanguage,
        version: str,
        api_endpoints: List[str],
        features: Optional[List[str]] = None
    ) -> SDKConfiguration:
        """Generate SDK for specified language"""
        
        sdk_id = f"sdk_{language.value}_{uuid.uuid4().hex[:8]}"
        
        # Generate SDK code based on language
        sdk_code = await self._generate_language_specific_code(
            language, api_endpoints, features or []
        )
        
        # Create SDK package structure
        package_structure = self._create_package_structure(language, sdk_code)
        
        # Generate documentation
        documentation = self._generate_documentation(language, api_endpoints)
        
        # Create configuration
        sdk_config = SDKConfiguration(
            sdk_id=sdk_id,
            language=language,
            version=version,
            version_type=SDKVersion.STABLE,
            features=features or ["api_client", "authentication", "error_handling"],
            dependencies=self._get_language_dependencies(language),
            api_endpoints=api_endpoints,
            documentation_url=f"https://docs.tradingagents.com/sdks/{language.value}",
            examples_included=True,
            testing_suite=True,
            created_at=datetime.now(timezone.utc),
            last_updated=datetime.now(timezone.utc),
            github_url=f"https://github.com/tradingagents/sdk-{language.value}"
        )
        
        self.generated_sdks[sdk_id] = {
            "config": sdk_config,
            "code": sdk_code,
            "package_structure": package_structure,
            "documentation": documentation
        }
        
        return sdk_config
    
    async def _generate_language_specific_code(
        self,
        language: ProgrammingLanguage,
        endpoints: List[str],
        features: List[str]
    ) -> Dict[str, str]:
        """Generate language-specific SDK code"""
        
        if language == ProgrammingLanguage.PYTHON:
            return await self._generate_python_sdk(endpoints, features)
        elif language == ProgrammingLanguage.JAVASCRIPT:
            return await self._generate_javascript_sdk(endpoints, features)
        elif language == ProgrammingLanguage.JAVA:
            return await self._generate_java_sdk(endpoints, features)
        elif language == ProgrammingLanguage.CSHARP:
            return await self._generate_csharp_sdk(endpoints, features)
        else:
            return await self._generate_generic_sdk(language, endpoints, features)
    
    async def _generate_python_sdk(self, endpoints: List[str], features: List[str]) -> Dict[str, str]:
        """Generate Python SDK"""
        
        client_code = '''
"""TradingAgents Python SDK"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

class TradingAgentsClient:
    """Main client for TradingAgents API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.tradingagents.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TradingAgents-Python-SDK/1.0.0"
        })
        self.logger = logging.getLogger(__name__)
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for a symbol"""
        url = f"{self.base_url}/market-data/{symbol}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_ai_analysis(self, symbol: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Get AI analysis for a symbol"""
        url = f"{self.base_url}/ai-analysis/{symbol}"
        params = {"type": analysis_type}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_trading_signals(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get trading signals for symbols"""
        url = f"{self.base_url}/trading-signals"
        data = {"symbols": symbols}
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_portfolio_analysis(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create portfolio analysis"""
        url = f"{self.base_url}/portfolio-analysis"
        data = {"holdings": holdings}
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()

class MarketData:
    """Market data utilities"""
    
    def __init__(self, client: TradingAgentsClient):
        self.client = client
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return self.client.get_market_data(symbol)
    
    def get_historical(self, symbol: str, period: str = "1y") -> List[Dict[str, Any]]:
        """Get historical data"""
        url = f"{self.client.base_url}/market-data/{symbol}/history"
        params = {"period": period}
        response = self.client.session.get(url, params=params)
        response.raise_for_status()
        return response.json()

class AIAnalytics:
    """AI analytics utilities"""
    
    def __init__(self, client: TradingAgentsClient):
        self.client = client
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        return self.client.get_ai_analysis(symbol, "stock_analysis")
    
    def sentiment_analysis(self, symbol: str) -> Dict[str, Any]:
        return self.client.get_ai_analysis(symbol, "sentiment")
    
    def price_prediction(self, symbol: str, horizon: str = "1w") -> Dict[str, Any]:
        url = f"{self.client.base_url}/ai-analysis/{symbol}/prediction"
        params = {"horizon": horizon}
        response = self.client.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
'''
        
        examples_code = '''
"""TradingAgents Python SDK Examples"""

from tradingagents import TradingAgentsClient, MarketData, AIAnalytics

# Initialize client
client = TradingAgentsClient(api_key="your_api_key_here")

# Example 1: Get market data
market_data = client.get_market_data("AAPL")
print(f"AAPL Price: ${market_data['price']}")

# Example 2: Get AI analysis
ai_analysis = client.get_ai_analysis("AAPL")
print(f"AI Recommendation: {ai_analysis['recommendation']}")

# Example 3: Get trading signals
signals = client.get_trading_signals(["AAPL", "TSLA", "MSFT"])
for signal in signals:
    print(f"{signal['symbol']}: {signal['signal']} (confidence: {signal['confidence']})")

# Example 4: Portfolio analysis
holdings = [
    {"symbol": "AAPL", "quantity": 100, "purchase_price": 140.00},
    {"symbol": "TSLA", "quantity": 50, "purchase_price": 200.00}
]
portfolio_analysis = client.create_portfolio_analysis(holdings)
print(f"Portfolio Performance: {portfolio_analysis['total_return_percent']:.2f}%")

# Example 5: Using utility classes
market = MarketData(client)
analytics = AIAnalytics(client)

quote = market.get_quote("AAPL")
historical = market.get_historical("AAPL", "6m")
prediction = analytics.price_prediction("AAPL", "1w")

print(f"Current: ${quote['price']}, Predicted (1w): ${prediction['predicted_price']}")
'''
        
        return {
            "client.py": client_code,
            "examples.py": examples_code,
            "setup.py": self._generate_python_setup(),
            "requirements.txt": "requests>=2.25.0\\ntyping>=3.7.0",
            "README.md": self._generate_readme("python")
        }
    
    async def _generate_javascript_sdk(self, endpoints: List[str], features: List[str]) -> Dict[str, str]:
        """Generate JavaScript/Node.js SDK"""
        
        client_code = '''
/**
 * TradingAgents JavaScript SDK
 */

const axios = require('axios');

class TradingAgentsClient {
    constructor(apiKey, baseUrl = 'https://api.tradingagents.com') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
                'User-Agent': 'TradingAgents-JS-SDK/1.0.0'
            }
        });
    }

    async getMarketData(symbol) {
        try {
            const response = await this.client.get(`/market-data/${symbol}`);
            return response.data;
        } catch (error) {
            throw new Error(`Failed to get market data: ${error.message}`);
        }
    }

    async getAIAnalysis(symbol, analysisType = 'comprehensive') {
        try {
            const response = await this.client.get(`/ai-analysis/${symbol}`, {
                params: { type: analysisType }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to get AI analysis: ${error.message}`);
        }
    }

    async getTradingSignals(symbols) {
        try {
            const response = await this.client.post('/trading-signals', {
                symbols: symbols
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to get trading signals: ${error.message}`);
        }
    }

    async createPortfolioAnalysis(holdings) {
        try {
            const response = await this.client.post('/portfolio-analysis', {
                holdings: holdings
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to create portfolio analysis: ${error.message}`);
        }
    }
}

class MarketData {
    constructor(client) {
        this.client = client;
    }

    async getQuote(symbol) {
        return await this.client.getMarketData(symbol);
    }

    async getHistorical(symbol, period = '1y') {
        try {
            const response = await this.client.client.get(`/market-data/${symbol}/history`, {
                params: { period: period }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to get historical data: ${error.message}`);
        }
    }
}

class AIAnalytics {
    constructor(client) {
        this.client = client;
    }

    async analyzeStock(symbol) {
        return await this.client.getAIAnalysis(symbol, 'stock_analysis');
    }

    async sentimentAnalysis(symbol) {
        return await this.client.getAIAnalysis(symbol, 'sentiment');
    }

    async pricePrediction(symbol, horizon = '1w') {
        try {
            const response = await this.client.client.get(`/ai-analysis/${symbol}/prediction`, {
                params: { horizon: horizon }
            });
            return response.data;
        } catch (error) {
            throw new Error(`Failed to get price prediction: ${error.message}`);
        }
    }
}

module.exports = {
    TradingAgentsClient,
    MarketData,
    AIAnalytics
};
'''
        
        examples_code = '''
/**
 * TradingAgents JavaScript SDK Examples
 */

const { TradingAgentsClient, MarketData, AIAnalytics } = require('tradingagents-sdk');

async function examples() {
    // Initialize client
    const client = new TradingAgentsClient('your_api_key_here');

    try {
        // Example 1: Get market data
        const marketData = await client.getMarketData('AAPL');
        console.log(`AAPL Price: $${marketData.price}`);

        // Example 2: Get AI analysis
        const aiAnalysis = await client.getAIAnalysis('AAPL');
        console.log(`AI Recommendation: ${aiAnalysis.recommendation}`);

        // Example 3: Get trading signals
        const signals = await client.getTradingSignals(['AAPL', 'TSLA', 'MSFT']);
        signals.forEach(signal => {
            console.log(`${signal.symbol}: ${signal.signal} (confidence: ${signal.confidence})`);
        });

        // Example 4: Portfolio analysis
        const holdings = [
            { symbol: 'AAPL', quantity: 100, purchase_price: 140.00 },
            { symbol: 'TSLA', quantity: 50, purchase_price: 200.00 }
        ];
        const portfolioAnalysis = await client.createPortfolioAnalysis(holdings);
        console.log(`Portfolio Performance: ${portfolioAnalysis.total_return_percent.toFixed(2)}%`);

        // Example 5: Using utility classes
        const market = new MarketData(client);
        const analytics = new AIAnalytics(client);

        const quote = await market.getQuote('AAPL');
        const historical = await market.getHistorical('AAPL', '6m');
        const prediction = await analytics.pricePrediction('AAPL', '1w');

        console.log(`Current: $${quote.price}, Predicted (1w): $${prediction.predicted_price}`);

    } catch (error) {
        console.error('Error:', error.message);
    }
}

examples();
'''
        
        package_json = '''{
    "name": "tradingagents-sdk",
    "version": "1.0.0",
    "description": "Official JavaScript SDK for TradingAgents API",
    "main": "index.js",
    "scripts": {
        "test": "jest",
        "build": "webpack",
        "dev": "nodemon examples/basic.js"
    },
    "keywords": ["trading", "finance", "ai", "api", "sdk"],
    "author": "TradingAgents",
    "license": "MIT",
    "dependencies": {
        "axios": "^1.0.0"
    },
    "devDependencies": {
        "jest": "^29.0.0",
        "nodemon": "^2.0.0",
        "webpack": "^5.0.0"
    },
    "repository": {
        "type": "git",
        "url": "https://github.com/tradingagents/sdk-javascript.git"
    }
}'''
        
        return {
            "index.js": client_code,
            "examples/basic.js": examples_code,
            "package.json": package_json,
            "README.md": self._generate_readme("javascript")
        }
    
    async def _generate_java_sdk(self, endpoints: List[str], features: List[str]) -> Dict[str, str]:
        """Generate Java SDK"""
        
        client_code = '''
package com.tradingagents.sdk;

import com.fasterxml.jackson.databind.ObjectMapper;
import okhttp3.*;
import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * TradingAgents Java SDK
 */
public class TradingAgentsClient {
    private static final String DEFAULT_BASE_URL = "https://api.tradingagents.com";
    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");
    
    private final String apiKey;
    private final String baseUrl;
    private final OkHttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    public TradingAgentsClient(String apiKey) {
        this(apiKey, DEFAULT_BASE_URL);
    }
    
    public TradingAgentsClient(String apiKey, String baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.objectMapper = new ObjectMapper();
        
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(60, TimeUnit.SECONDS)
                .addInterceptor(chain -> {
                    Request original = chain.request();
                    Request request = original.newBuilder()
                            .header("Authorization", "Bearer " + apiKey)
                            .header("Content-Type", "application/json")
                            .header("User-Agent", "TradingAgents-Java-SDK/1.0.0")
                            .build();
                    return chain.proceed(request);
                })
                .build();
    }
    
    public MarketDataResponse getMarketData(String symbol) throws IOException {
        String url = baseUrl + "/market-data/" + symbol;
        Request request = new Request.Builder().url(url).build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected response: " + response);
            }
            
            String responseBody = response.body().string();
            return objectMapper.readValue(responseBody, MarketDataResponse.class);
        }
    }
    
    public AIAnalysisResponse getAIAnalysis(String symbol, String analysisType) throws IOException {
        HttpUrl url = HttpUrl.parse(baseUrl + "/ai-analysis/" + symbol)
                .newBuilder()
                .addQueryParameter("type", analysisType)
                .build();
        
        Request request = new Request.Builder().url(url).build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected response: " + response);
            }
            
            String responseBody = response.body().string();
            return objectMapper.readValue(responseBody, AIAnalysisResponse.class);
        }
    }
    
    public List<TradingSignal> getTradingSignals(List<String> symbols) throws IOException {
        String url = baseUrl + "/trading-signals";
        String jsonBody = objectMapper.writeValueAsString(Map.of("symbols", symbols));
        
        RequestBody body = RequestBody.create(jsonBody, JSON);
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();
        
        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new IOException("Unexpected response: " + response);
            }
            
            String responseBody = response.body().string();
            return objectMapper.readValue(responseBody, 
                    objectMapper.getTypeFactory().constructCollectionType(List.class, TradingSignal.class));
        }
    }
}

// Data classes
class MarketDataResponse {
    private String symbol;
    private double price;
    private double change;
    private long volume;
    private String timestamp;
    
    // Getters and setters
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    
    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }
    
    public double getChange() { return change; }
    public void setChange(double change) { this.change = change; }
    
    public long getVolume() { return volume; }
    public void setVolume(long volume) { this.volume = volume; }
    
    public String getTimestamp() { return timestamp; }
    public void setTimestamp(String timestamp) { this.timestamp = timestamp; }
}

class AIAnalysisResponse {
    private String symbol;
    private String recommendation;
    private double confidence;
    private List<String> factors;
    
    // Getters and setters
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    
    public String getRecommendation() { return recommendation; }
    public void setRecommendation(String recommendation) { this.recommendation = recommendation; }
    
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }
    
    public List<String> getFactors() { return factors; }
    public void setFactors(List<String> factors) { this.factors = factors; }
}

class TradingSignal {
    private String symbol;
    private String signal;
    private double confidence;
    
    // Getters and setters
    public String getSymbol() { return symbol; }
    public void setSymbol(String symbol) { this.symbol = symbol; }
    
    public String getSignal() { return signal; }
    public void setSignal(String signal) { this.signal = signal; }
    
    public double getConfidence() { return confidence; }
    public void setConfidence(double confidence) { this.confidence = confidence; }
}
'''
        
        return {
            "src/main/java/com/tradingagents/sdk/TradingAgentsClient.java": client_code,
            "pom.xml": self._generate_java_pom(),
            "README.md": self._generate_readme("java")
        }
    
    async def _generate_csharp_sdk(self, endpoints: List[str], features: List[str]) -> Dict[str, str]:
        """Generate C# SDK"""
        
        client_code = '''
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace TradingAgents.SDK
{
    /// <summary>
    /// TradingAgents C# SDK Client
    /// </summary>
    public class TradingAgentsClient
    {
        private readonly HttpClient _httpClient;
        private readonly string _baseUrl;
        private readonly JsonSerializerOptions _jsonOptions;

        public TradingAgentsClient(string apiKey, string baseUrl = "https://api.tradingagents.com")
        {
            _baseUrl = baseUrl;
            _httpClient = new HttpClient();
            _httpClient.DefaultRequestHeaders.Add("Authorization", $"Bearer {apiKey}");
            _httpClient.DefaultRequestHeaders.Add("User-Agent", "TradingAgents-CSharp-SDK/1.0.0");
            
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase
            };
        }

        public async Task<MarketDataResponse> GetMarketDataAsync(string symbol)
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/market-data/{symbol}");
            response.EnsureSuccessStatusCode();
            
            var content = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<MarketDataResponse>(content, _jsonOptions);
        }

        public async Task<AIAnalysisResponse> GetAIAnalysisAsync(string symbol, string analysisType = "comprehensive")
        {
            var response = await _httpClient.GetAsync($"{_baseUrl}/ai-analysis/{symbol}?type={analysisType}");
            response.EnsureSuccessStatusCode();
            
            var content = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<AIAnalysisResponse>(content, _jsonOptions);
        }

        public async Task<List<TradingSignal>> GetTradingSignalsAsync(List<string> symbols)
        {
            var requestBody = new { symbols = symbols };
            var json = JsonSerializer.Serialize(requestBody, _jsonOptions);
            var content = new StringContent(json, Encoding.UTF8, "application/json");

            var response = await _httpClient.PostAsync($"{_baseUrl}/trading-signals", content);
            response.EnsureSuccessStatusCode();
            
            var responseContent = await response.Content.ReadAsStringAsync();
            return JsonSerializer.Deserialize<List<TradingSignal>>(responseContent, _jsonOptions);
        }

        public void Dispose()
        {
            _httpClient?.Dispose();
        }
    }

    // Data models
    public class MarketDataResponse
    {
        public string Symbol { get; set; }
        public double Price { get; set; }
        public double Change { get; set; }
        public long Volume { get; set; }
        public string Timestamp { get; set; }
    }

    public class AIAnalysisResponse
    {
        public string Symbol { get; set; }
        public string Recommendation { get; set; }
        public double Confidence { get; set; }
        public List<string> Factors { get; set; }
    }

    public class TradingSignal
    {
        public string Symbol { get; set; }
        public string Signal { get; set; }
        public double Confidence { get; set; }
    }
}
'''
        
        return {
            "TradingAgents.SDK/TradingAgentsClient.cs": client_code,
            "TradingAgents.SDK/TradingAgents.SDK.csproj": self._generate_csharp_project(),
            "README.md": self._generate_readme("csharp")
        }
    
    async def _generate_generic_sdk(
        self,
        language: ProgrammingLanguage,
        endpoints: List[str],
        features: List[str]
    ) -> Dict[str, str]:
        """Generate generic SDK template"""
        
        return {
            "client": f"// {language.value.upper()} SDK implementation",
            "README.md": self._generate_readme(language.value)
        }
    
    def _create_package_structure(self, language: ProgrammingLanguage, code: Dict[str, str]) -> Dict[str, Any]:
        """Create package structure for SDK"""
        
        structure = {
            "language": language.value,
            "files": list(code.keys()),
            "directories": [],
            "build_files": [],
            "test_files": []
        }
        
        if language == ProgrammingLanguage.PYTHON:
            structure["directories"] = ["tradingagents", "tests", "examples", "docs"]
            structure["build_files"] = ["setup.py", "requirements.txt", "MANIFEST.in"]
            structure["test_files"] = ["tests/test_client.py", "tests/test_market_data.py"]
            
        elif language == ProgrammingLanguage.JAVASCRIPT:
            structure["directories"] = ["lib", "test", "examples", "docs"]
            structure["build_files"] = ["package.json", "webpack.config.js", ".babelrc"]
            structure["test_files"] = ["test/client.test.js", "test/market-data.test.js"]
            
        elif language == ProgrammingLanguage.JAVA:
            structure["directories"] = ["src/main/java", "src/test/java", "src/main/resources"]
            structure["build_files"] = ["pom.xml", "build.gradle"]
            structure["test_files"] = ["src/test/java/ClientTest.java"]
            
        elif language == ProgrammingLanguage.CSHARP:
            structure["directories"] = ["TradingAgents.SDK", "TradingAgents.SDK.Tests", "Examples"]
            structure["build_files"] = ["TradingAgents.SDK.sln", "TradingAgents.SDK.csproj"]
            structure["test_files"] = ["TradingAgents.SDK.Tests/ClientTests.cs"]
        
        return structure
    
    def _generate_documentation(self, language: ProgrammingLanguage, endpoints: List[str]) -> Dict[str, str]:
        """Generate SDK documentation"""
        
        return {
            "api_reference": f"API Reference for {language.value} SDK",
            "getting_started": f"Getting Started with {language.value} SDK",
            "examples": f"Code examples for {language.value} SDK",
            "changelog": f"Changelog for {language.value} SDK"
        }
    
    def _get_language_dependencies(self, language: ProgrammingLanguage) -> Dict[str, str]:
        """Get language-specific dependencies"""
        
        dependencies = {
            ProgrammingLanguage.PYTHON: {
                "requests": ">=2.25.0",
                "typing": ">=3.7.0",
                "dataclasses": ">=0.6.0"
            },
            ProgrammingLanguage.JAVASCRIPT: {
                "axios": "^1.0.0",
                "@types/node": "^18.0.0"
            },
            ProgrammingLanguage.JAVA: {
                "okhttp": "4.10.0",
                "jackson-databind": "2.14.0"
            },
            ProgrammingLanguage.CSHARP: {
                "System.Text.Json": "7.0.0",
                "Microsoft.Extensions.Http": "7.0.0"
            }
        }
        
        return dependencies.get(language, {})
    
    def _generate_python_setup(self) -> str:
        """Generate Python setup.py"""
        return '''
from setuptools import setup, find_packages

setup(
    name="tradingagents-sdk",
    version="1.0.0",
    description="Official Python SDK for TradingAgents API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="TradingAgents",
    author_email="developers@tradingagents.com",
    url="https://github.com/tradingagents/sdk-python",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "typing>=3.7.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)
'''
    
    def _generate_java_pom(self) -> str:
        """Generate Java pom.xml"""
        return '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.tradingagents</groupId>
    <artifactId>tradingagents-sdk</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>
    
    <name>TradingAgents Java SDK</name>
    <description>Official Java SDK for TradingAgents API</description>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>com.squareup.okhttp3</groupId>
            <artifactId>okhttp</artifactId>
            <version>4.10.0</version>
        </dependency>
        
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.14.0</version>
        </dependency>
        
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>'''
    
    def _generate_csharp_project(self) -> str:
        """Generate C# project file"""
        return '''<Project Sdk="Microsoft.NET.Sdk">
    <PropertyGroup>
        <TargetFramework>net6.0</TargetFramework>
        <PackageId>TradingAgents.SDK</PackageId>
        <Version>1.0.0</Version>
        <Authors>TradingAgents</Authors>
        <Description>Official C# SDK for TradingAgents API</Description>
        <PackageProjectUrl>https://github.com/tradingagents/sdk-csharp</PackageProjectUrl>
        <RepositoryUrl>https://github.com/tradingagents/sdk-csharp</RepositoryUrl>
        <PackageLicenseExpression>MIT</PackageLicenseExpression>
    </PropertyGroup>
    
    <ItemGroup>
        <PackageReference Include="System.Text.Json" Version="7.0.0" />
        <PackageReference Include="Microsoft.Extensions.Http" Version="7.0.0" />
    </ItemGroup>
</Project>'''
    
    def _generate_readme(self, language: str) -> str:
        """Generate README file"""
        return f'''# TradingAgents {language.title()} SDK

Official {language.title()} SDK for the TradingAgents API.

## Installation

```bash
# Installation instructions for {language}
```

## Quick Start

```{language}
// Quick start example for {language}
```

## Documentation

- [API Reference](https://docs.tradingagents.com/sdks/{language}/api-reference)
- [Getting Started Guide](https://docs.tradingagents.com/sdks/{language}/getting-started)
- [Examples](https://docs.tradingagents.com/sdks/{language}/examples)

## Support

- [GitHub Issues](https://github.com/tradingagents/sdk-{language}/issues)
- [Documentation](https://docs.tradingagents.com)
- [Community Forum](https://community.tradingagents.com)

## License

MIT License - see LICENSE file for details.
'''

class CodeTemplateManager:
    """Manages code templates and generators"""
    
    def __init__(self):
        self.templates = {}
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize default code templates"""
        
        # Python templates
        self._create_template(
            "basic_api_call",
            ProgrammingLanguage.PYTHON,
            "Basic API Call",
            '''
from tradingagents import TradingAgentsClient

# Initialize client
client = TradingAgentsClient(api_key="your_api_key")

# Get market data
data = client.get_market_data("AAPL")
print(f"Price: ${data['price']}")
            ''',
            ["tradingagents-sdk"],
            ["Get real-time market data for any stock symbol"]
        )
        
        self._create_template(
            "trading_bot_basic",
            ProgrammingLanguage.PYTHON,
            "Basic Trading Bot",
            '''
from tradingagents import TradingAgentsClient
import time

class SimpleTradingBot:
    def __init__(self, api_key):
        self.client = TradingAgentsClient(api_key)
        self.positions = {}
    
    def run(self, symbols, check_interval=60):
        while True:
            for symbol in symbols:
                signals = self.client.get_trading_signals([symbol])
                signal = signals[0] if signals else None
                
                if signal and signal['confidence'] > 0.8:
                    if signal['signal'] == 'BUY':
                        print(f"Buy signal for {symbol}")
                        # Implement buy logic
                    elif signal['signal'] == 'SELL':
                        print(f"Sell signal for {symbol}")
                        # Implement sell logic
            
            time.sleep(check_interval)

# Usage
bot = SimpleTradingBot("your_api_key")
bot.run(["AAPL", "TSLA", "MSFT"])
            ''',
            ["tradingagents-sdk"],
            ["Create a simple automated trading bot"]
        )
        
        # JavaScript templates
        self._create_template(
            "portfolio_tracker",
            ProgrammingLanguage.JAVASCRIPT,
            "Portfolio Tracker",
            '''
const { TradingAgentsClient } = require('tradingagents-sdk');

class PortfolioTracker {
    constructor(apiKey) {
        this.client = new TradingAgentsClient(apiKey);
        this.holdings = [];
    }
    
    addHolding(symbol, quantity, purchasePrice) {
        this.holdings.push({
            symbol: symbol,
            quantity: quantity,
            purchase_price: purchasePrice
        });
    }
    
    async updatePortfolio() {
        const analysis = await this.client.createPortfolioAnalysis(this.holdings);
        console.log(`Portfolio Value: $${analysis.total_value}`);
        console.log(`Total Return: ${analysis.total_return_percent.toFixed(2)}%`);
        
        return analysis;
    }
}

// Usage
const tracker = new PortfolioTracker('your_api_key');
tracker.addHolding('AAPL', 100, 140.00);
tracker.addHolding('TSLA', 50, 200.00);
tracker.updatePortfolio();
            ''',
            ["tradingagents-sdk"],
            ["Track portfolio performance and returns"]
        )
    
    def _create_template(
        self,
        category: str,
        language: ProgrammingLanguage,
        name: str,
        code: str,
        dependencies: List[str],
        examples: List[str]
    ):
        """Create a code template"""
        
        template_id = f"{category}_{language.value}_{uuid.uuid4().hex[:8]}"
        
        template = CodeTemplate(
            template_id=template_id,
            template_name=name,
            language=language,
            category=category,
            description=f"{name} template for {language.value}",
            code_content=code.strip(),
            required_dependencies=dependencies,
            usage_examples=examples,
            created_at=datetime.now(timezone.utc)
        )
        
        self.templates[template_id] = template
    
    def get_templates_by_language(self, language: ProgrammingLanguage) -> List[CodeTemplate]:
        """Get templates for specific language"""
        return [t for t in self.templates.values() if t.language == language]
    
    def get_templates_by_category(self, category: str) -> List[CodeTemplate]:
        """Get templates by category"""
        return [t for t in self.templates.values() if t.category == category]
    
    def generate_project_from_template(
        self,
        template_id: str,
        project_name: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate project files from template"""
        
        if template_id not in self.templates:
            raise ValueError(f"Template {template_id} not found")
        
        template = self.templates[template_id]
        customizations = customizations or {}
        
        # Customize template code
        code = template.code_content
        for key, value in customizations.items():
            code = code.replace(f"{{{key}}}", str(value))
        
        # Generate project structure
        project_files = {
            "main": code,
            "README.md": f"# {project_name}\n\nGenerated from template: {template.template_name}",
            "requirements": "\n".join(template.required_dependencies)
        }
        
        return project_files

class DeveloperToolkit:
    """Main developer toolkit orchestrator"""
    
    def __init__(self):
        self.sdk_generator = SDKGenerator()
        self.template_manager = CodeTemplateManager()
        self.projects = {}
        self.tools_registry = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize toolkit
        self._initialize_toolkit()
    
    def _initialize_toolkit(self):
        """Initialize developer toolkit"""
        
        # Register built-in tools
        self.tools_registry.update({
            "sdk_generator": {
                "name": "SDK Generator",
                "type": ToolType.SDK,
                "description": "Generate SDKs for multiple programming languages",
                "status": "active"
            },
            "code_templates": {
                "name": "Code Templates",
                "type": ToolType.CODE_GENERATOR,
                "description": "Pre-built code templates for common use cases",
                "status": "active"
            },
            "api_tester": {
                "name": "API Tester",
                "type": ToolType.TESTING_FRAMEWORK,
                "description": "Interactive API testing and debugging",
                "status": "beta"
            }
        })
    
    async def generate_sdk_package(
        self,
        language: ProgrammingLanguage,
        version: str = "1.0.0",
        features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate complete SDK package"""
        
        # Generate SDK
        sdk_config = await self.sdk_generator.generate_sdk(
            language, version, ["market-data", "ai-analysis", "trading-signals"], features
        )
        
        # Get generated files
        sdk_data = self.sdk_generator.generated_sdks[sdk_config.sdk_id]
        
        return {
            "sdk_config": {
                "sdk_id": sdk_config.sdk_id,
                "language": sdk_config.language.value,
                "version": sdk_config.version,
                "features": sdk_config.features,
                "documentation_url": sdk_config.documentation_url,
                "github_url": sdk_config.github_url
            },
            "package_files": sdk_data["code"],
            "package_structure": sdk_data["package_structure"],
            "documentation": sdk_data["documentation"],
            "installation_guide": self._generate_installation_guide(language),
            "testing_instructions": self._generate_testing_instructions(language)
        }
    
    def get_code_templates(
        self, 
        language: Optional[ProgrammingLanguage] = None,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available code templates"""
        
        if language:
            templates = self.template_manager.get_templates_by_language(language)
        elif category:
            templates = self.template_manager.get_templates_by_category(category)
        else:
            templates = list(self.template_manager.templates.values())
        
        return [
            {
                "template_id": t.template_id,
                "name": t.template_name,
                "language": t.language.value,
                "category": t.category,
                "description": t.description,
                "dependencies": t.required_dependencies,
                "examples": t.usage_examples,
                "popularity": t.popularity_score
            }
            for t in templates
        ]
    
    async def create_project_from_template(
        self,
        template_id: str,
        project_name: str,
        developer_id: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> DeveloperProject:
        """Create new project from template"""
        
        # Generate project files
        project_files = self.template_manager.generate_project_from_template(
            template_id, project_name, customizations
        )
        
        # Get template info
        template = self.template_manager.templates[template_id]
        
        # Create project record
        project = DeveloperProject(
            project_id=f"proj_{uuid.uuid4().hex[:8]}",
            project_name=project_name,
            developer_id=developer_id,
            language=template.language,
            sdk_version="1.0.0",
            api_keys=[],
            endpoints_used=[],
            created_at=datetime.now(timezone.utc),
            last_activity=datetime.now(timezone.utc)
        )
        
        self.projects[project.project_id] = {
            "config": project,
            "files": project_files,
            "template_id": template_id
        }
        
        return project
    
    def get_developer_tools_catalog(self) -> List[Dict[str, Any]]:
        """Get catalog of available developer tools"""
        
        catalog = []
        
        for tool_id, tool_info in self.tools_registry.items():
            catalog.append({
                "tool_id": tool_id,
                "name": tool_info["name"],
                "type": tool_info["type"].value,
                "description": tool_info["description"],
                "status": tool_info["status"],
                "documentation_url": f"https://docs.tradingagents.com/tools/{tool_id}"
            })
        
        return catalog
    
    def _generate_installation_guide(self, language: ProgrammingLanguage) -> str:
        """Generate installation guide for SDK"""
        
        guides = {
            ProgrammingLanguage.PYTHON: """
## Installation

```bash
pip install tradingagents-sdk
```

## Quick Start

```python
from tradingagents import TradingAgentsClient

client = TradingAgentsClient("your_api_key")
data = client.get_market_data("AAPL")
print(data)
```
            """,
            ProgrammingLanguage.JAVASCRIPT: """
## Installation

```bash
npm install tradingagents-sdk
```

## Quick Start

```javascript
const { TradingAgentsClient } = require('tradingagents-sdk');

const client = new TradingAgentsClient('your_api_key');
client.getMarketData('AAPL').then(data => console.log(data));
```
            """
        }
        
        return guides.get(language, "Installation instructions not available")
    
    def _generate_testing_instructions(self, language: ProgrammingLanguage) -> str:
        """Generate testing instructions for SDK"""
        
        instructions = {
            ProgrammingLanguage.PYTHON: """
## Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=tradingagents tests/
```
            """,
            ProgrammingLanguage.JAVASCRIPT: """
## Testing

```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```
            """
        }
        
        return instructions.get(language, "Testing instructions not available")
    
    def get_toolkit_statistics(self) -> Dict[str, Any]:
        """Get developer toolkit statistics"""
        
        # Count SDKs by language
        generated_sdks = self.sdk_generator.generated_sdks
        sdks_by_language = {}
        
        for sdk_data in generated_sdks.values():
            lang = sdk_data["config"].language.value
            sdks_by_language[lang] = sdks_by_language.get(lang, 0) + 1
        
        # Count templates by category
        templates_by_category = {}
        for template in self.template_manager.templates.values():
            cat = template.category
            templates_by_category[cat] = templates_by_category.get(cat, 0) + 1
        
        # Count projects by language
        projects_by_language = {}
        for project_data in self.projects.values():
            lang = project_data["config"].language.value
            projects_by_language[lang] = projects_by_language.get(lang, 0) + 1
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sdk_statistics": {
                "total_sdks": len(generated_sdks),
                "sdks_by_language": sdks_by_language,
                "supported_languages": list(ProgrammingLanguage)
            },
            "template_statistics": {
                "total_templates": len(self.template_manager.templates),
                "templates_by_category": templates_by_category
            },
            "project_statistics": {
                "total_projects": len(self.projects),
                "projects_by_language": projects_by_language,
                "active_projects": len([p for p in self.projects.values() if p["config"].status == "active"])
            },
            "tools_available": len(self.tools_registry)
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
    async def test_developer_toolkit():
        toolkit = DeveloperToolkit()
        
        print("Testing Developer Toolkit...")
        
        # Test SDK generation
        print("\n1. Testing SDK Generation:")
        
        # Generate Python SDK
        python_sdk = await toolkit.generate_sdk_package(
            ProgrammingLanguage.PYTHON,
            "1.0.0",
            ["api_client", "authentication", "market_data", "ai_analytics"]
        )
        
        print(f"Generated Python SDK: {python_sdk['sdk_config']['sdk_id']}")
        print(f"Features: {', '.join(python_sdk['sdk_config']['features'])}")
        print(f"Files: {len(python_sdk['package_files'])} files generated")
        
        # Generate JavaScript SDK
        js_sdk = await toolkit.generate_sdk_package(
            ProgrammingLanguage.JAVASCRIPT,
            "1.0.0"
        )
        
        print(f"Generated JavaScript SDK: {js_sdk['sdk_config']['sdk_id']}")
        
        # Test code templates
        print("\n2. Testing Code Templates:")
        
        templates = toolkit.get_code_templates(language=ProgrammingLanguage.PYTHON)
        print(f"Available Python templates: {len(templates)}")
        
        for template in templates:
            print(f"  - {template['name']} ({template['category']})")
        
        # Test project creation from template
        print("\n3. Testing Project Creation:")
        
        if templates:
            template_id = templates[0]['template_id']
            project = await toolkit.create_project_from_template(
                template_id,
                "My Trading App",
                "dev_123",
                {"api_key": "test_key", "symbols": "AAPL,TSLA"}
            )
            
            print(f"Created project: {project.project_id}")
            print(f"Language: {project.language.value}")
            print(f"Project name: {project.project_name}")
        
        # Test tools catalog
        print("\n4. Testing Tools Catalog:")
        
        tools = toolkit.get_developer_tools_catalog()
        print(f"Available tools: {len(tools)}")
        
        for tool in tools:
            print(f"  - {tool['name']} ({tool['type']}) - {tool['status']}")
        
        # Get statistics
        print("\n5. Toolkit Statistics:")
        
        stats = toolkit.get_toolkit_statistics()
        print(f"Total SDKs: {stats['sdk_statistics']['total_sdks']}")
        print(f"Total templates: {stats['template_statistics']['total_templates']}")
        print(f"Total projects: {stats['project_statistics']['total_projects']}")
        print(f"Available tools: {stats['tools_available']}")
        
        # Show language distribution
        if stats['sdk_statistics']['sdks_by_language']:
            print("SDKs by language:")
            for lang, count in stats['sdk_statistics']['sdks_by_language'].items():
                print(f"  {lang}: {count}")
        
        return toolkit
    
    # Run test
    toolkit = asyncio.run(test_developer_toolkit())
    print("\nDeveloper Toolkit test completed successfully!")