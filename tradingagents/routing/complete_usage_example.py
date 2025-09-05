#!/usr/bin/env python3
"""
AI Task Router 完整使用指南
GPT-OSS整合任務1.3.1 - 企業級部署和使用示例

完整的實戰指南，涵蓋：
- 從基礎到高級的所有使用模式
- 企業級配置和部署策略
- 性能監控和優化最佳實踐
- 實際業務場景整合
- 故障處理和運維指南
"""

import asyncio
import logging
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# 導入完整的路由系統
from .enhanced_llm_service import (
    EnhancedLLMService, create_enhanced_llm_service,
    CompatibleLLMClient, create_compatible_llm_client
)
from .ai_task_router import AITaskRouter, RoutingStrategy, RoutingWeights
from .routing_config import RoutingConfigManager, StrategyTemplate
from ..utils.llm_client import AnalysisType, LLMClient

# 配置詳細日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('ai_router_examples.log')
    ]
)
logger = logging.getLogger(__name__)

class AIRouterUsageGuide:
    """AI路由器使用指南類"""
    
    def __init__(self):
        self.examples_run = []
        self.service_instances = []
    
    async def cleanup(self):
        """清理資源"""
        for service in self.service_instances:
            try:
                await service.shutdown()
            except Exception as e:
                logger.warning(f"清理服務時發生錯誤: {e}")
        self.service_instances.clear()
    
    def track_service(self, service):
        """追蹤服務實例以便後續清理"""
        self.service_instances.append(service)
        return service

    # ==================== 基礎使用示例 ====================
    
    async def basic_usage_example(self):
        """1. 基礎使用示例 - 零配置快速開始"""
        logger.info("🚀 基礎使用示例 - 零配置快速開始")
        
        # 創建增強LLM服務（自動啟用智能路由）
        service = self.track_service(create_enhanced_llm_service(
            llm_config={
                # 'openai_api_key': 'your-openai-key',      # 可選
                # 'anthropic_api_key': 'your-anthropic-key', # 可選
                # 'gpt_oss_url': 'http://localhost:8080'     # 可選
            },
            enable_intelligent_routing=True
        ))
        
        try:
            # 初始化服務
            await service.initialize()
            
            # 執行分析 - AI路由會自動選擇最優模型
            response = await service.analyze(
                prompt="請分析台積電(2330)最近的財務表現和投資前景",
                context={
                    "stock_data": {
                        "symbol": "2330.TW",
                        "price": 500,
                        "volume": 1000000,
                        "pe_ratio": 15.2
                    },
                    "market_condition": "bull_market"
                },
                analysis_type=AnalysisType.FUNDAMENTAL,
                task_type="financial_summary",
                user_tier="standard",
                priority="standard"
            )
            
            self._log_analysis_result("基礎分析", response)
            
        except Exception as e:
            logger.error(f"❌ 基礎使用示例失敗: {e}")
    
    async def different_user_tiers_example(self):
        """2. 不同用戶等級示例"""
        logger.info("👥 不同用戶等級路由示例")
        
        service = self.track_service(create_enhanced_llm_service())
        await service.initialize()
        
        user_scenarios = [
            ("免費用戶", "free", "成本優先"),
            ("標準用戶", "standard", "平衡考量"),
            ("高級用戶", "premium", "品質和性能"),
            ("企業用戶", "enterprise", "最高品質和隱私")
        ]
        
        try:
            for user_type, tier, expectation in user_scenarios:
                logger.info(f"\n   測試 {user_type} ({tier}) - 預期: {expectation}")
                
                response = await service.analyze(
                    prompt="分析當前市場趨勢並給出投資建議",
                    analysis_type=AnalysisType.INVESTMENT,
                    task_type="investment_reasoning",
                    user_tier=tier,
                    priority="standard"
                )
                
                self._log_analysis_result(f"{user_type}分析", response)
                
        except Exception as e:
            logger.error(f"❌ 用戶等級示例失敗: {e}")

    async def priority_based_routing_example(self):
        """3. 基於優先級的路由示例"""
        logger.info("⚡ 優先級導向路由示例")
        
        service = self.track_service(create_enhanced_llm_service())
        await service.initialize()
        
        priority_scenarios = [
            ("低優先級", "low", "選擇成本最低的模型"),
            ("標準優先級", "standard", "平衡成本和性能"),
            ("高優先級", "high", "優先考慮性能"),
            ("緊急優先級", "urgent", "最快響應時間")
        ]
        
        try:
            for priority_name, priority, expected_behavior in priority_scenarios:
                logger.info(f"\n   測試 {priority_name} - {expected_behavior}")
                
                response = await service.analyze(
                    prompt="緊急：需要立即分析這個交易機會",
                    analysis_type=AnalysisType.RISK,
                    task_type="risk_assessment",
                    user_tier="premium",
                    priority=priority,
                    requires_high_quality=(priority in ["high", "urgent"])
                )
                
                self._log_analysis_result(f"{priority_name}處理", response)
                
        except Exception as e:
            logger.error(f"❌ 優先級示例失敗: {e}")

    # ==================== 高級配置示例 ====================

    async def custom_routing_configuration_example(self):
        """4. 自定義路由配置示例"""
        logger.info("⚙️ 自定義路由配置示例")
        
        # 創建自定義配置
        custom_config = {
            'default_routing_strategy': 'quality_first',
            'cost_optimization_enabled': True,
            'prefer_local_models': True,
            'routing_confidence_threshold': 0.8,
            'enable_dynamic_strategy_adjustment': True,
            'performance_cache_ttl': 1800,
            'max_routing_failures_before_fallback': 2
        }
        
        service = self.track_service(create_enhanced_llm_service(
            service_config=custom_config
        ))
        
        try:
            await service.initialize()
            
            # 執行分析以測試自定義配置
            response = await service.analyze(
                prompt="進行高精度的技術分析",
                analysis_type=AnalysisType.TECHNICAL,
                task_type="technical_analysis",
                user_tier="enterprise",
                priority="high",
                requires_high_quality=True
            )
            
            self._log_analysis_result("自定義配置分析", response)
            
            # 檢查配置是否生效
            stats = service.get_service_statistics()
            logger.info(f"   配置效果統計:")
            logger.info(f"     智能路由使用率: {stats.get('intelligent_routing_rate', 0):.2%}")
            logger.info(f"     總成本節省: ${stats.get('cost_savings_total', 0):.6f}")
            
        except Exception as e:
            logger.error(f"❌ 自定義配置示例失敗: {e}")

    async def advanced_strategy_management_example(self):
        """5. 高級策略管理示例"""
        logger.info("🎛️ 高級策略管理示例")
        
        # 創建臨時配置目錄
        with tempfile.TemporaryDirectory() as temp_dir:
            config_manager = RoutingConfigManager(Path(temp_dir))
            
            try:
                # 創建自定義策略
                custom_weights = RoutingWeights(
                    cost=0.5,           # 重視成本
                    latency=0.1,        # 不太關心延遲
                    quality=0.25,       # 適度重視品質
                    availability=0.1,   # 適度重視可用性
                    privacy=0.05,       # 一般重視隱私
                    user_preference=0.0 # 忽略用戶偏好
                )
                
                custom_strategy = config_manager.create_strategy_template(
                    name="cost_focused_custom",
                    display_name="成本導向自定義策略",
                    description="極度重視成本控制的自定義策略",
                    weights=custom_weights,
                    use_cases=["大批量處理", "開發測試", "成本敏感場景"],
                    performance_targets={"max_cost_per_1k": 0.003}
                )
                
                logger.info(f"   ✅ 創建自定義策略: {custom_strategy.name}")
                
                # 創建自定義路由政策
                custom_policy = config_manager.create_routing_policy(
                    name="cost_control_policy",
                    task_type_mappings={
                        "financial_summary": "cost_focused_custom",
                        "news_classification": "cost_optimized"
                    },
                    user_tier_mappings={
                        "free": "cost_focused_custom",
                        "basic": "cost_optimized"
                    },
                    priority_mappings={
                        "low": "cost_focused_custom"
                    },
                    fallback_strategy="cost_optimized"
                )
                
                logger.info(f"   ✅ 創建自定義政策: {custom_policy.name}")
                
                # 測試策略推薦
                recommended_strategy = config_manager.get_strategy_for_request(
                    task_type="financial_summary",
                    user_tier="free",
                    priority="low",
                    policy_name="cost_control_policy"
                )
                
                logger.info(f"   📊 推薦策略: {recommended_strategy}")
                
                # 驗證配置
                validation = config_manager.validate_configuration()
                logger.info(f"   ✅ 配置驗證: {'通過' if validation['valid'] else '失敗'}")
                if validation['warnings']:
                    logger.info(f"   ⚠️ 警告: {validation['warnings']}")
                
            except Exception as e:
                logger.error(f"❌ 策略管理示例失敗: {e}")

    # ==================== 性能監控和優化示例 ====================

    async def performance_monitoring_example(self):
        """6. 性能監控示例"""
        logger.info("📊 性能監控和分析示例")
        
        service = self.track_service(create_enhanced_llm_service(
            service_config={
                'performance_monitoring_enabled': True,
                'cost_tracking_enabled': True,
                'audit_logging_enabled': True
            }
        ))
        
        try:
            await service.initialize()
            
            # 執行一系列請求以產生監控數據
            test_requests = [
                ("技術分析", AnalysisType.TECHNICAL, "technical_analysis"),
                ("基本面分析", AnalysisType.FUNDAMENTAL, "financial_summary"), 
                ("市場情緒分析", AnalysisType.SENTIMENT, "market_sentiment"),
                ("風險評估", AnalysisType.RISK, "risk_assessment"),
                ("投資建議", AnalysisType.INVESTMENT, "investment_reasoning")
            ]
            
            logger.info("   執行測試請求以產生監控數據...")
            
            for request_name, analysis_type, task_type in test_requests:
                try:
                    response = await service.analyze(
                        prompt=f"執行{request_name}",
                        analysis_type=analysis_type,
                        task_type=task_type,
                        user_tier="standard",
                        priority="standard"
                    )
                    
                    status = "成功" if response.success else "失敗"
                    logger.info(f"     {request_name}: {status}")
                    
                    # 短暫延遲模擬真實使用
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"     {request_name}: 錯誤 - {e}")
            
            # 獲取詳細統計
            stats = service.get_service_statistics()
            logger.info(f"\n   📈 性能統計摘要:")
            logger.info(f"     總請求數: {stats.get('total_requests', 0)}")
            logger.info(f"     智能路由請求: {stats.get('intelligent_routed_requests', 0)}")
            logger.info(f"     降級請求: {stats.get('fallback_requests', 0)}")
            logger.info(f"     運行時間: {stats.get('uptime_hours', 0):.2f} 小時")
            logger.info(f"     成功率: {stats.get('success_rate', 0):.2%}")
            logger.info(f"     智能路由使用率: {stats.get('intelligent_routing_rate', 0):.2%}")
            
            # 服務健康檢查
            health = await service.health_check()
            logger.info(f"\n   🏥 健康狀態: {health.get('status', 'unknown')}")
            logger.info(f"     服務版本: {health.get('version', 'unknown')}")
            logger.info(f"     運行時間: {health.get('uptime_hours', 0):.2f} 小時")
            
        except Exception as e:
            logger.error(f"❌ 性能監控示例失敗: {e}")

    async def cost_analysis_example(self):
        """7. 成本分析和優化示例"""
        logger.info("💰 成本分析和優化示例")
        
        service = self.track_service(create_enhanced_llm_service(
            service_config={
                'cost_optimization_enabled': True,
                'cost_tracking_enabled': True,
                'prefer_local_models': True,  # 優先使用免費的本地模型
                'daily_cost_limit': 10.0     # 設置每日成本限制
            }
        ))
        
        try:
            await service.initialize()
            
            # 模擬不同成本敏感度的請求
            cost_scenarios = [
                ("高成本敏感", "free", "low"),
                ("中等成本敏感", "standard", "standard"), 
                ("低成本敏感", "premium", "high")
            ]
            
            for scenario, user_tier, priority in cost_scenarios:
                logger.info(f"\n   測試 {scenario} (用戶: {user_tier}, 優先級: {priority})")
                
                start_time = datetime.now()
                
                response = await service.analyze(
                    prompt="進行詳細的市場分析和投資建議",
                    analysis_type=AnalysisType.INVESTMENT,
                    task_type="investment_reasoning",
                    user_tier=user_tier,
                    priority=priority,
                    max_acceptable_cost=0.01 if scenario == "高成本敏感" else None
                )
                
                end_time = datetime.now()
                duration = (end_time - start_time).total_seconds()
                
                if response.success:
                    logger.info(f"     ✅ 分析成功")
                    logger.info(f"     執行時間: {duration:.2f}秒")
                    logger.info(f"     使用模型: {response.model}")
                    
                    if response.usage and 'total_tokens' in response.usage:
                        tokens = response.usage['total_tokens']
                        logger.info(f"     使用tokens: {tokens}")
                else:
                    logger.info(f"     ❌ 分析失敗: {response.error}")
            
            # 總體成本統計
            stats = service.get_service_statistics()
            logger.info(f"\n   💵 成本統計:")
            logger.info(f"     總成本節省: ${stats.get('cost_savings_total', 0):.6f}")
            logger.info(f"     性能改進次數: {stats.get('performance_improvements', 0)}")
            
        except Exception as e:
            logger.error(f"❌ 成本分析示例失敗: {e}")

    # ==================== 實際業務場景示例 ====================

    async def financial_analysis_workflow_example(self):
        """8. 金融分析工作流程示例"""
        logger.info("📈 完整金融分析工作流程示例")
        
        service = self.track_service(create_enhanced_llm_service())
        await service.initialize()
        
        try:
            # 模擬完整的金融分析工作流程
            stock_symbol = "2330.TW"
            analysis_workflow = [
                {
                    "step": "基本面分析",
                    "prompt": f"分析{stock_symbol}的財務狀況、營收成長和獲利能力",
                    "analysis_type": AnalysisType.FUNDAMENTAL,
                    "task_type": "financial_summary"
                },
                {
                    "step": "技術面分析", 
                    "prompt": f"分析{stock_symbol}的價格走勢、技術指標和交易量",
                    "analysis_type": AnalysisType.TECHNICAL,
                    "task_type": "technical_analysis"
                },
                {
                    "step": "市場情緒分析",
                    "prompt": f"分析市場對{stock_symbol}的情緒和新聞輿論",
                    "analysis_type": AnalysisType.SENTIMENT,
                    "task_type": "market_sentiment"
                },
                {
                    "step": "風險評估",
                    "prompt": f"評估投資{stock_symbol}的風險因子和風險等級",
                    "analysis_type": AnalysisType.RISK,
                    "task_type": "risk_assessment"
                },
                {
                    "step": "投資建議",
                    "prompt": f"綜合以上分析，給出{stock_symbol}的投資建議和目標價",
                    "analysis_type": AnalysisType.INVESTMENT,
                    "task_type": "investment_reasoning"
                }
            ]
            
            workflow_results = {}
            
            for step_info in analysis_workflow:
                logger.info(f"\n   📊 執行: {step_info['step']}")
                
                response = await service.analyze(
                    prompt=step_info["prompt"],
                    context={
                        "stock_symbol": stock_symbol,
                        "previous_analyses": workflow_results
                    },
                    analysis_type=step_info["analysis_type"],
                    task_type=step_info["task_type"],
                    user_tier="premium",
                    priority="high",
                    requires_high_quality=True
                )
                
                if response.success:
                    workflow_results[step_info["step"]] = response.content
                    logger.info(f"     ✅ {step_info['step']} 完成")
                    logger.info(f"     使用模型: {response.model}")
                    if response.response_time:
                        logger.info(f"     響應時間: {response.response_time:.2f}秒")
                else:
                    logger.error(f"     ❌ {step_info['step']} 失敗: {response.error}")
                    workflow_results[step_info["step"]] = f"分析失敗: {response.error}"
            
            # 生成最終報告
            logger.info(f"\n   📝 生成最終分析報告...")
            
            final_response = await service.analyze(
                prompt=f"基於以下分析結果，生成{stock_symbol}的完整投資分析報告",
                context={
                    "analyses": workflow_results,
                    "stock_symbol": stock_symbol
                },
                analysis_type=AnalysisType.GENERATION,
                task_type="report_generation",
                user_tier="premium",
                priority="standard"
            )
            
            if final_response.success:
                logger.info(f"   ✅ 最終報告生成完成")
                logger.info(f"   報告長度: {len(final_response.content)} 字符")
            else:
                logger.error(f"   ❌ 最終報告生成失敗: {final_response.error}")
            
        except Exception as e:
            logger.error(f"❌ 金融分析工作流程示例失敗: {e}")

    async def batch_processing_example(self):
        """9. 批量處理示例"""
        logger.info("🔄 批量處理示例")
        
        service = self.track_service(create_enhanced_llm_service(
            service_config={
                'cost_optimization_enabled': True,  # 批量處理時特別重要
                'enable_graceful_degradation': True
            }
        ))
        
        try:
            await service.initialize()
            
            # 模擬需要批量處理的股票列表
            stock_list = ["2330.TW", "2317.TW", "2454.TW", "2882.TW", "6505.TW"]
            
            logger.info(f"   批量分析 {len(stock_list)} 支股票")
            
            # 方法1: 順序處理
            logger.info("   📋 順序處理模式:")
            sequential_start = datetime.now()
            
            for stock in stock_list:
                response = await service.analyze(
                    prompt=f"快速分析{stock}的投資價值",
                    analysis_type=AnalysisType.FUNDAMENTAL,
                    task_type="financial_summary",
                    user_tier="standard",
                    priority="low"  # 批量處理使用低優先級
                )
                
                status = "成功" if response.success else "失敗"
                logger.info(f"     {stock}: {status}")
            
            sequential_time = (datetime.now() - sequential_start).total_seconds()
            logger.info(f"   順序處理總時間: {sequential_time:.2f}秒")
            
            # 方法2: 並發處理 (使用 asyncio.gather)
            logger.info("\n   ⚡ 並發處理模式:")
            concurrent_start = datetime.now()
            
            # 創建並發任務
            concurrent_tasks = [
                service.analyze(
                    prompt=f"快速分析{stock}的投資價值",
                    analysis_type=AnalysisType.FUNDAMENTAL,
                    task_type="financial_summary",
                    user_tier="standard",
                    priority="low"
                )
                for stock in stock_list
            ]
            
            # 執行並發分析
            concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            
            for i, (stock, result) in enumerate(zip(stock_list, concurrent_results)):
                if isinstance(result, Exception):
                    logger.info(f"     {stock}: 錯誤 - {result}")
                elif result.success:
                    logger.info(f"     {stock}: 成功")
                else:
                    logger.info(f"     {stock}: 失敗 - {result.error}")
            
            concurrent_time = (datetime.now() - concurrent_start).total_seconds()
            logger.info(f"   並發處理總時間: {concurrent_time:.2f}秒")
            
            # 性能比較
            speedup = sequential_time / concurrent_time if concurrent_time > 0 else 0
            logger.info(f"\n   ⚡ 性能提升: {speedup:.1f}x 倍速")
            
        except Exception as e:
            logger.error(f"❌ 批量處理示例失敗: {e}")

    # ==================== 故障處理和運維示例 ====================

    async def error_handling_example(self):
        """10. 錯誤處理和故障轉移示例"""
        logger.info("🛡️ 錯誤處理和故障轉移示例")
        
        # 創建可能有問題的配置
        problematic_config = {
            'intelligent_routing_enabled': True,
            'enable_graceful_degradation': True,
            'max_routing_failures_before_fallback': 2,
            'fallback_cooldown_minutes': 1,
            'enable_real_time_alerts': False
        }
        
        service = self.track_service(create_enhanced_llm_service(
            llm_config={
                'openai_api_key': 'invalid-key-for-testing',  # 故意使用無效密鑰
                'anthropic_api_key': 'invalid-key-for-testing'
            },
            service_config=problematic_config
        ))
        
        try:
            # 嘗試初始化（可能部分失敗）
            init_result = await service.initialize()
            logger.info(f"   服務初始化結果: {'成功' if init_result else '部分成功/降級'}")
            
            # 測試各種錯誤場景
            error_scenarios = [
                ("正常請求", "標準的分析請求"),
                ("高負載請求", "非常複雜的大量數據分析請求"),
                ("無效參數", None),  # 這會測試無效輸入處理
            ]
            
            for scenario_name, prompt in error_scenarios:
                logger.info(f"\n   測試場景: {scenario_name}")
                
                try:
                    if prompt is None:
                        # 測試無效參數
                        response = await service.analyze(
                            prompt="",  # 空提示詞
                            analysis_type=AnalysisType.TECHNICAL,
                            user_tier="invalid_tier"  # 無效用戶等級
                        )
                    else:
                        response = await service.analyze(
                            prompt=prompt,
                            analysis_type=AnalysisType.TECHNICAL,
                            task_type="technical_analysis",
                            user_tier="standard",
                            priority="standard"
                        )
                    
                    if response.success:
                        logger.info(f"     ✅ {scenario_name}: 成功處理")
                        logger.info(f"     使用模型: {response.model}")
                    else:
                        logger.info(f"     ⚠️ {scenario_name}: 失敗但已處理 - {response.error}")
                        
                except Exception as e:
                    logger.info(f"     ❌ {scenario_name}: 異常 - {e}")
            
            # 檢查錯誤統計
            stats = service.get_service_statistics()
            logger.info(f"\n   🔍 錯誤統計:")
            logger.info(f"     總請求數: {stats.get('total_requests', 0)}")
            logger.info(f"     降級請求數: {stats.get('fallback_requests', 0)}")
            logger.info(f"     服務健康狀態: {service._service_health.get('status', 'unknown')}")
            
            # 健康檢查
            health = await service.health_check()
            logger.info(f"\n   🏥 系統健康檢查:")
            logger.info(f"     整體狀態: {health.get('status', 'unknown')}")
            
            if 'components' in health:
                for component, status in health['components'].items():
                    if isinstance(status, dict):
                        comp_status = status.get('status', status.get('overall_status', 'unknown'))
                    else:
                        comp_status = status
                    logger.info(f"     {component}: {comp_status}")
            
        except Exception as e:
            logger.error(f"❌ 錯誤處理示例失敗: {e}")

    async def backward_compatibility_example(self):
        """11. 向後兼容性示例"""
        logger.info("🔄 向後兼容性示例")
        
        try:
            # 方式1: 使用兼容包裝器
            logger.info("   方式1: 使用兼容包裝器")
            
            compatible_client = create_compatible_llm_client(
                config={'enable_intelligent_routing': True}
            )
            
            # 這個API調用與原始LLMClient完全相同
            response = await compatible_client.analyze(
                prompt="使用兼容包裝器進行分析",
                analysis_type=AnalysisType.TECHNICAL
            )
            
            logger.info(f"     兼容包裝器結果: {'成功' if response.success else '失敗'}")
            
            await compatible_client.close()
            
            # 方式2: 直接使用增強服務但禁用智能路由
            logger.info("\n   方式2: 禁用智能路由模式")
            
            legacy_service = self.track_service(create_enhanced_llm_service(
                enable_intelligent_routing=False  # 禁用智能路由
            ))
            
            await legacy_service.initialize()
            
            response = await legacy_service.analyze(
                prompt="傳統模式分析",
                analysis_type=AnalysisType.FUNDAMENTAL
            )
            
            logger.info(f"     傳統模式結果: {'成功' if response.success else '失敗'}")
            
            # 方式3: 完全啟用但保持API兼容
            logger.info("\n   方式3: 完全增強但API兼容")
            
            enhanced_service = self.track_service(create_enhanced_llm_service(
                enable_intelligent_routing=True
            ))
            
            await enhanced_service.initialize()
            
            # 使用與原始LLMClient相同的參數
            response = await enhanced_service.analyze(
                prompt="增強但兼容的分析",
                analysis_type=AnalysisType.INVESTMENT
            )
            
            logger.info(f"     增強兼容結果: {'成功' if response.success else '失敗'}")
            
            # 但可以獲取額外的增強功能信息
            stats = enhanced_service.get_service_statistics()
            logger.info(f"     額外統計可用: {len(stats) > 0}")
            
        except Exception as e:
            logger.error(f"❌ 向後兼容性示例失敗: {e}")

    # ==================== 輔助方法 ====================
    
    def _log_analysis_result(self, analysis_name: str, response):
        """記錄分析結果"""
        if response.success:
            logger.info(f"   ✅ {analysis_name}成功")
            logger.info(f"     使用模型: {response.provider.value if hasattr(response.provider, 'value') else response.provider}/{response.model}")
            
            if response.response_time:
                logger.info(f"     響應時間: {response.response_time:.2f}秒")
            
            if response.usage and 'total_tokens' in response.usage:
                logger.info(f"     Token使用: {response.usage['total_tokens']}")
            
            # 檢查智能路由信息
            if hasattr(response, 'metadata') and response.metadata:
                if 'routing_used' in response.metadata:
                    logger.info(f"     路由類型: {response.metadata['routing_used']}")
        else:
            logger.error(f"   ❌ {analysis_name}失敗: {response.error}")
    
    async def run_all_examples(self):
        """運行所有示例"""
        examples = [
            ("基礎使用示例", self.basic_usage_example),
            ("不同用戶等級示例", self.different_user_tiers_example),
            ("優先級導向路由示例", self.priority_based_routing_example),
            ("自定義路由配置示例", self.custom_routing_configuration_example),
            ("高級策略管理示例", self.advanced_strategy_management_example),
            ("性能監控示例", self.performance_monitoring_example),
            ("成本分析優化示例", self.cost_analysis_example),
            ("金融分析工作流程示例", self.financial_analysis_workflow_example),
            ("批量處理示例", self.batch_processing_example),
            ("錯誤處理故障轉移示例", self.error_handling_example),
            ("向後兼容性示例", self.backward_compatibility_example)
        ]
        
        successful_examples = 0
        failed_examples = 0
        
        for name, example_func in examples:
            try:
                logger.info(f"\n{'='*80}")
                logger.info(f"🎯 執行: {name}")
                logger.info(f"{'='*80}")
                
                await example_func()
                
                successful_examples += 1
                self.examples_run.append((name, "成功"))
                logger.info(f"✅ {name} - 完成")
                
            except Exception as e:
                failed_examples += 1
                self.examples_run.append((name, f"失敗: {e}"))
                logger.error(f"❌ {name} - 失敗: {e}")
            
            # 示例間短暫暫停，模擬真實使用間隔
            await asyncio.sleep(0.5)
        
        # 最終總結
        logger.info(f"\n{'='*80}")
        logger.info(f"🎊 所有示例執行完成!")
        logger.info(f"   成功: {successful_examples}")
        logger.info(f"   失敗: {failed_examples}")
        logger.info(f"   總計: {successful_examples + failed_examples}")
        logger.info(f"{'='*80}")
        
        # 詳細結果
        logger.info("\n📋 詳細結果:")
        for name, result in self.examples_run:
            logger.info(f"   {name}: {result}")

async def main():
    """主函數"""
    guide = AIRouterUsageGuide()
    
    try:
        logger.info("🚀 AI Task Router 完整使用指南開始")
        logger.info("這個指南將展示所有功能和最佳實踐")
        logger.info("請注意：某些示例可能會因為缺少真實的API密鑰而降級運行")
        
        await guide.run_all_examples()
        
    except KeyboardInterrupt:
        logger.info("\n⏹️ 用戶中斷了示例執行")
    except Exception as e:
        logger.error(f"❌ 主程序執行失敗: {e}")
    finally:
        # 清理資源
        logger.info("\n🧹 清理資源...")
        await guide.cleanup()
        logger.info("✅ 資源清理完成")

if __name__ == "__main__":
    # 運行完整示例
    asyncio.run(main())