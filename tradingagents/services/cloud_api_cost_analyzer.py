#!/usr/bin/env python3
"""
雲端API成本對比分析器
CloudAPICostAnalyzer - 建立雲端API使用成本的追蹤和計算系統

功能特色：
1. 雲端API使用成本追蹤
2. 本地 vs 雲端成本實時對比分析
3. 成本節省量化計算和報告
4. 成本優化建議和決策支援
5. 多雲端服務商成本比較
"""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import aiohttp

# 配置日誌
logger = logging.getLogger(__name__)

class CloudProvider(Enum):
    """雲端服務提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"
    AWS_BEDROCK = "aws_bedrock"
    HUGGINGFACE = "huggingface"

@dataclass
class CloudAPIConfig:
    """雲端API配置"""
    provider: CloudProvider
    model_name: str
    input_token_price: float  # USD per 1K tokens
    output_token_price: float  # USD per 1K tokens
    request_price: float = 0.0  # USD per request
    
    # 性能參數
    avg_latency_ms: float = 1000.0
    max_tokens_per_request: int = 4096
    rate_limit_rpm: int = 60  # requests per minute

@dataclass
class APIUsageRecord:
    """API使用記錄"""
    record_id: str
    provider: CloudProvider
    model_name: str
    timestamp: datetime
    
    # 使用統計
    input_tokens: int
    output_tokens: int
    total_tokens: int
    request_count: int = 1
    
    # 成本計算
    input_cost: float = 0.0
    output_cost: float = 0.0
    request_cost: float = 0.0
    total_cost: float = 0.0
    
    # 性能統計
    latency_ms: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    
    # 任務信息
    task_type: str = "inference"
    session_id: Optional[str] = None

@dataclass
class CostComparison:
    """成本對比"""
    local_cost: float
    cloud_cost: float
    cost_savings: float
    savings_percentage: float
    
    local_duration_hours: float
    cloud_equivalent_requests: int
    
    # 性能對比
    local_avg_latency_ms: float
    cloud_avg_latency_ms: float
    
    # 建議
    recommendation: str
    confidence_score: float

# 預定義的雲端API配置
CLOUD_API_CONFIGS = {
    # OpenAI GPT-4
    "openai_gpt4": CloudAPIConfig(
        provider=CloudProvider.OPENAI,
        model_name="gpt-4",
        input_token_price=0.03,  # $0.03 per 1K tokens
        output_token_price=0.06,  # $0.06 per 1K tokens
        avg_latency_ms=2000.0,
        max_tokens_per_request=8192
    ),
    
    # OpenAI GPT-3.5 Turbo
    "openai_gpt35": CloudAPIConfig(
        provider=CloudProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        input_token_price=0.001,  # $0.001 per 1K tokens
        output_token_price=0.002,  # $0.002 per 1K tokens
        avg_latency_ms=1500.0,
        max_tokens_per_request=4096
    ),
    
    # Anthropic Claude
    "anthropic_claude": CloudAPIConfig(
        provider=CloudProvider.ANTHROPIC,
        model_name="claude-3-sonnet",
        input_token_price=0.003,  # $0.003 per 1K tokens
        output_token_price=0.015,  # $0.015 per 1K tokens
        avg_latency_ms=1800.0,
        max_tokens_per_request=4096
    ),
    
    # Google Gemini Pro
    "google_gemini": CloudAPIConfig(
        provider=CloudProvider.GOOGLE,
        model_name="gemini-pro",
        input_token_price=0.00025,  # $0.00025 per 1K tokens
        output_token_price=0.0005,  # $0.0005 per 1K tokens
        avg_latency_ms=1200.0,
        max_tokens_per_request=2048
    ),
    
    # Azure OpenAI
    "azure_gpt4": CloudAPIConfig(
        provider=CloudProvider.AZURE,
        model_name="gpt-4",
        input_token_price=0.03,
        output_token_price=0.06,
        avg_latency_ms=2200.0,
        max_tokens_per_request=8192
    ),
    
    # Hugging Face Inference API
    "huggingface_llama": CloudAPIConfig(
        provider=CloudProvider.HUGGINGFACE,
        model_name="meta-llama/Llama-2-7b-chat-hf",
        input_token_price=0.0002,
        output_token_price=0.0002,
        avg_latency_ms=800.0,
        max_tokens_per_request=2048
    )
}

class CloudAPICostAnalyzer:
    """雲端API成本對比分析器"""
    
    def __init__(self, db_path: str = "cloud_api_costs.db"):
        self.db_path = db_path
        self.api_configs = CLOUD_API_CONFIGS.copy()
        
        # 初始化數據庫
        self._init_database()
    
    def _init_database(self):
        """初始化數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_records (
                    record_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    total_tokens INTEGER,
                    request_count INTEGER,
                    input_cost REAL,
                    output_cost REAL,
                    request_cost REAL,
                    total_cost REAL,
                    latency_ms REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    task_type TEXT,
                    session_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_date TEXT NOT NULL,
                    local_cost REAL,
                    cloud_cost REAL,
                    cost_savings REAL,
                    savings_percentage REAL,
                    local_duration_hours REAL,
                    cloud_equivalent_requests INTEGER,
                    recommendation TEXT,
                    confidence_score REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cost_optimization_suggestions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    suggestion_date TEXT NOT NULL,
                    suggestion_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    potential_savings REAL,
                    implementation_effort TEXT,
                    priority_score INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    async def record_api_usage(self, 
                             provider: str,
                             model_name: str,
                             input_tokens: int,
                             output_tokens: int,
                             latency_ms: float = 0.0,
                             task_type: str = "inference",
                             session_id: Optional[str] = None,
                             success: bool = True,
                             error_message: Optional[str] = None) -> APIUsageRecord:
        """記錄API使用"""
        
        # 查找配置
        config_key = f"{provider}_{model_name.replace('-', '').replace('/', '_').lower()}"
        if config_key not in self.api_configs:
            # 使用默認配置
            config = CloudAPIConfig(
                provider=CloudProvider(provider),
                model_name=model_name,
                input_token_price=0.001,
                output_token_price=0.002
            )
        else:
            config = self.api_configs[config_key]
        
        # 創建記錄
        record = APIUsageRecord(
            record_id=f"{provider}_{int(datetime.now().timestamp() * 1000)}",
            provider=CloudProvider(provider),
            model_name=model_name,
            timestamp=datetime.now(),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            task_type=task_type,
            session_id=session_id,
            success=success,
            error_message=error_message
        )
        
        # 計算成本
        record.input_cost = (input_tokens / 1000.0) * config.input_token_price
        record.output_cost = (output_tokens / 1000.0) * config.output_token_price
        record.request_cost = config.request_price
        record.total_cost = record.input_cost + record.output_cost + record.request_cost
        
        # 保存到數據庫
        await self._save_usage_record(record)
        
        logger.info(f"記錄API使用: {provider}/{model_name}, 成本: ${record.total_cost:.4f}")
        return record
    
    async def _save_usage_record(self, record: APIUsageRecord):
        """保存使用記錄到數據庫"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO api_usage_records (
                    record_id, provider, model_name, timestamp, input_tokens,
                    output_tokens, total_tokens, request_count, input_cost,
                    output_cost, request_cost, total_cost, latency_ms,
                    success, error_message, task_type, session_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.record_id, record.provider.value, record.model_name,
                record.timestamp.isoformat(), record.input_tokens, record.output_tokens,
                record.total_tokens, record.request_count, record.input_cost,
                record.output_cost, record.request_cost, record.total_cost,
                record.latency_ms, record.success, record.error_message,
                record.task_type, record.session_id
            ))
            conn.commit()
    
    async def get_cloud_usage_summary(self, 
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """獲取雲端使用摘要"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    provider,
                    model_name,
                    COUNT(*) as request_count,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(total_tokens) as total_tokens,
                    SUM(total_cost) as total_cost,
                    AVG(latency_ms) as avg_latency,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests
                FROM api_usage_records
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY provider, model_name
                ORDER BY total_cost DESC
            """, (start_date.isoformat(), end_date.isoformat()))
            
            summary = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "providers": {},
                "totals": {
                    "total_cost": 0.0,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "avg_latency": 0.0
                }
            }
            
            total_cost = 0.0
            total_requests = 0
            total_tokens = 0
            total_latency = 0.0
            
            for row in cursor.fetchall():
                provider, model_name, request_count, input_tokens, output_tokens, tokens, cost, latency, successful = row
                
                if provider not in summary["providers"]:
                    summary["providers"][provider] = {
                        "models": {},
                        "total_cost": 0.0,
                        "total_requests": 0,
                        "total_tokens": 0
                    }
                
                summary["providers"][provider]["models"][model_name] = {
                    "request_count": request_count,
                    "input_tokens": input_tokens or 0,
                    "output_tokens": output_tokens or 0,
                    "total_tokens": tokens or 0,
                    "total_cost": cost or 0.0,
                    "avg_latency_ms": latency or 0.0,
                    "success_rate": (successful / request_count) if request_count else 0.0,
                    "cost_per_token": (cost / tokens) if tokens else 0.0
                }
                
                summary["providers"][provider]["total_cost"] += cost or 0.0
                summary["providers"][provider]["total_requests"] += request_count
                summary["providers"][provider]["total_tokens"] += tokens or 0
                
                total_cost += cost or 0.0
                total_requests += request_count
                total_tokens += tokens or 0
                total_latency += (latency or 0.0) * request_count
            
            summary["totals"]["total_cost"] = total_cost
            summary["totals"]["total_requests"] = total_requests
            summary["totals"]["total_tokens"] = total_tokens
            summary["totals"]["avg_latency"] = (total_latency / total_requests) if total_requests else 0.0
            
            return summary
    
    async def compare_local_vs_cloud_costs(self, 
                                         local_cost_tracker,
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> CostComparison:
        """對比本地和雲端成本"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 獲取本地成本
        local_breakdown = await local_cost_tracker.get_cost_breakdown(start_date, end_date)
        local_cost = local_breakdown.total_cost
        
        # 獲取雲端成本
        cloud_summary = await self.get_cloud_usage_summary(start_date, end_date)
        cloud_cost = cloud_summary["totals"]["total_cost"]
        
        # 計算節省
        cost_savings = cloud_cost - local_cost
        savings_percentage = (cost_savings / cloud_cost * 100) if cloud_cost > 0 else 0
        
        # 性能對比
        local_avg_latency = 500.0  # 假設本地推理500ms
        cloud_avg_latency = cloud_summary["totals"]["avg_latency"]
        
        # 生成建議
        recommendation, confidence = self._generate_cost_recommendation(
            local_cost, cloud_cost, savings_percentage, local_avg_latency, cloud_avg_latency
        )
        
        comparison = CostComparison(
            local_cost=local_cost,
            cloud_cost=cloud_cost,
            cost_savings=cost_savings,
            savings_percentage=savings_percentage,
            local_duration_hours=local_breakdown.cost_per_hour,
            cloud_equivalent_requests=cloud_summary["totals"]["total_requests"],
            local_avg_latency_ms=local_avg_latency,
            cloud_avg_latency_ms=cloud_avg_latency,
            recommendation=recommendation,
            confidence_score=confidence
        )
        
        # 保存對比結果
        await self._save_cost_comparison(comparison)
        
        return comparison
    
    def _generate_cost_recommendation(self, 
                                    local_cost: float,
                                    cloud_cost: float,
                                    savings_percentage: float,
                                    local_latency: float,
                                    cloud_latency: float) -> Tuple[str, float]:
        """生成成本建議"""
        
        if savings_percentage > 50:
            recommendation = "強烈建議使用本地GPU訓練，可節省超過50%成本"
            confidence = 0.9
        elif savings_percentage > 20:
            recommendation = "建議優先使用本地GPU訓練，有顯著成本優勢"
            confidence = 0.8
        elif savings_percentage > 0:
            recommendation = "本地GPU訓練有輕微成本優勢，建議根據任務特性選擇"
            confidence = 0.6
        elif savings_percentage > -20:
            recommendation = "本地和雲端成本相近，建議根據延遲需求選擇"
            confidence = 0.5
        else:
            recommendation = "雲端API在當前使用模式下更經濟，建議混合使用"
            confidence = 0.7
        
        # 考慮延遲因素
        if local_latency < cloud_latency * 0.5:
            recommendation += "，且本地推理有顯著延遲優勢"
            confidence += 0.1
        
        return recommendation, min(confidence, 1.0)
    
    async def _save_cost_comparison(self, comparison: CostComparison):
        """保存成本對比結果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cost_comparisons (
                    comparison_date, local_cost, cloud_cost, cost_savings,
                    savings_percentage, local_duration_hours, cloud_equivalent_requests,
                    recommendation, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), comparison.local_cost, comparison.cloud_cost,
                comparison.cost_savings, comparison.savings_percentage,
                comparison.local_duration_hours, comparison.cloud_equivalent_requests,
                comparison.recommendation, comparison.confidence_score
            ))
            conn.commit()
    
    async def generate_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """生成成本優化建議"""
        suggestions = []
        
        # 分析最近30天的使用模式
        cloud_summary = await self.get_cloud_usage_summary()
        
        # 建議1: 高頻任務本地化
        high_cost_models = []
        for provider, data in cloud_summary["providers"].items():
            for model, stats in data["models"].items():
                if stats["total_cost"] > 10.0 and stats["request_count"] > 100:
                    high_cost_models.append({
                        "provider": provider,
                        "model": model,
                        "cost": stats["total_cost"],
                        "requests": stats["request_count"]
                    })
        
        if high_cost_models:
            total_potential_savings = sum(m["cost"] * 0.6 for m in high_cost_models)
            suggestions.append({
                "type": "local_migration",
                "title": "高頻任務本地化",
                "description": f"將{len(high_cost_models)}個高成本模型遷移到本地GPU",
                "potential_savings": total_potential_savings,
                "implementation_effort": "中等",
                "priority_score": 8,
                "details": high_cost_models
            })
        
        # 建議2: 批量處理優化
        total_requests = cloud_summary["totals"]["total_requests"]
        if total_requests > 1000:
            batch_savings = total_requests * 0.001  # 假設每請求節省$0.001
            suggestions.append({
                "type": "batch_optimization",
                "title": "批量處理優化",
                "description": "將小批量請求合併為大批量處理",
                "potential_savings": batch_savings,
                "implementation_effort": "低",
                "priority_score": 6,
                "details": {
                    "current_requests": total_requests,
                    "estimated_batch_reduction": "30%"
                }
            })
        
        # 建議3: 模型選擇優化
        expensive_models = []
        for provider, data in cloud_summary["providers"].items():
            for model, stats in data["models"].items():
                cost_per_token = stats.get("cost_per_token", 0)
                if cost_per_token > 0.00005:  # 高於$0.00005/token
                    expensive_models.append({
                        "provider": provider,
                        "model": model,
                        "cost_per_token": cost_per_token,
                        "total_cost": stats["total_cost"]
                    })
        
        if expensive_models:
            model_savings = sum(m["total_cost"] * 0.3 for m in expensive_models)
            suggestions.append({
                "type": "model_optimization",
                "title": "模型選擇優化",
                "description": "使用更經濟的模型替代高成本模型",
                "potential_savings": model_savings,
                "implementation_effort": "低",
                "priority_score": 7,
                "details": expensive_models
            })
        
        # 保存建議到數據庫
        for suggestion in suggestions:
            await self._save_optimization_suggestion(suggestion)
        
        return suggestions
    
    async def _save_optimization_suggestion(self, suggestion: Dict[str, Any]):
        """保存優化建議"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO cost_optimization_suggestions (
                    suggestion_date, suggestion_type, description,
                    potential_savings, implementation_effort, priority_score
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(), suggestion["type"], suggestion["description"],
                suggestion["potential_savings"], suggestion["implementation_effort"],
                suggestion["priority_score"]
            ))
            conn.commit()
    
    async def get_cost_trends_comparison(self, days: int = 30) -> Dict[str, Any]:
        """獲取成本趨勢對比"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 獲取雲端成本趨勢
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    SUM(total_cost) as daily_cost,
                    COUNT(*) as daily_requests,
                    SUM(total_tokens) as daily_tokens
                FROM api_usage_records
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (start_date.isoformat(), end_date.isoformat()))
            
            cloud_trends = []
            for row in cursor.fetchall():
                date, cost, requests, tokens = row
                cloud_trends.append({
                    "date": date,
                    "cost": cost or 0.0,
                    "requests": requests,
                    "tokens": tokens or 0,
                    "cost_per_token": (cost / tokens) if tokens else 0.0
                })
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "cloud_trends": cloud_trends,
            "summary": {
                "total_cloud_cost": sum(t["cost"] for t in cloud_trends),
                "avg_daily_cost": sum(t["cost"] for t in cloud_trends) / len(cloud_trends) if cloud_trends else 0,
                "total_requests": sum(t["requests"] for t in cloud_trends),
                "total_tokens": sum(t["tokens"] for t in cloud_trends)
            }
        }
    
    async def export_cost_comparison_report(self, 
                                          local_cost_tracker,
                                          start_date: Optional[datetime] = None,
                                          end_date: Optional[datetime] = None) -> str:
        """導出成本對比報告"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        # 獲取各種分析數據
        comparison = await self.compare_local_vs_cloud_costs(local_cost_tracker, start_date, end_date)
        cloud_summary = await self.get_cloud_usage_summary(start_date, end_date)
        local_breakdown = await local_cost_tracker.get_cost_breakdown(start_date, end_date)
        optimization_suggestions = await self.generate_optimization_suggestions()
        trends = await self.get_cost_trends_comparison((end_date - start_date).days)
        
        report = {
            "report_title": "本地GPU vs 雲端API 成本對比分析報告",
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "executive_summary": {
                "cost_comparison": asdict(comparison),
                "key_findings": [
                    f"本地GPU成本: ${comparison.local_cost:.2f}",
                    f"雲端API成本: ${comparison.cloud_cost:.2f}",
                    f"成本節省: ${comparison.cost_savings:.2f} ({comparison.savings_percentage:.1f}%)",
                    f"建議: {comparison.recommendation}"
                ]
            },
            "detailed_analysis": {
                "local_cost_breakdown": asdict(local_breakdown),
                "cloud_usage_summary": cloud_summary,
                "cost_trends": trends
            },
            "optimization_recommendations": optimization_suggestions,
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0"
        }
        
        return json.dumps(report, indent=2, ensure_ascii=False)

# 使用示例
async def main():
    """使用示例"""
    analyzer = CloudAPICostAnalyzer()
    
    # 記錄API使用
    await analyzer.record_api_usage(
        provider="openai",
        model_name="gpt-4",
        input_tokens=1000,
        output_tokens=500,
        latency_ms=2000.0,
        task_type="analysis"
    )
    
    # 獲取使用摘要
    summary = await analyzer.get_cloud_usage_summary()
    print(f"雲端總成本: ${summary['totals']['total_cost']:.4f}")
    
    # 生成優化建議
    suggestions = await analyzer.generate_optimization_suggestions()
    for suggestion in suggestions:
        print(f"建議: {suggestion['title']} - 潛在節省: ${suggestion['potential_savings']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())