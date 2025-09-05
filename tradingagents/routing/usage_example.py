#!/usr/bin/env python3
"""
AI Task Router 使用示例
GPT-OSS整合任務1.3.1 - 完整系統使用指南

展示如何使用企業級AI任務智能路由系統的所有功能
"""

import asyncio
import logging
from typing import Dict, Any

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from .llm_client_integration import EnhancedLLMClient, create_enhanced_llm_client
from .ai_task_router import RoutingStrategy, RoutingWeights
from ..utils.llm_client import AnalysisType

async def basic_usage_example():
    """基礎使用示例"""
    logger.info("🚀 基礎AI路由使用示例")
    
    # 1. 創建增強版LLM客戶端（啟用AI路由）
    client = create_enhanced_llm_client(
        llm_config={
            'openai_api_key': 'your_openai_key',
            'anthropic_api_key': 'your_anthropic_key',
            'gpt_oss_url': 'http://localhost:8080'
        },
        enable_ai_routing=True
    )
    
    try:
        # 2. 初始化AI路由功能
        await client.initialize_ai_routing()
        
        # 3. 執行分析（AI路由自動選擇最優模型）
        response = await client.analyze(
            prompt="請分析台積電(2330)的投資前景",
            context={
                "stock_data": {"price": 500, "volume": 1000000},
                "market_condition": "bull_market"
            },
            analysis_type=AnalysisType.INVESTMENT,
            stock_id="2330",
            user_id="user123",
            user_tier="premium",  # AI路由參數
            priority="standard"   # AI路由參數
        )
        
        if response.success:
            logger.info(f"✅ 分析成功完成")
            logger.info(f"   選擇的模型: {response.provider.value}")
            logger.info(f"   響應時間: {response.response_time:.2f}秒")
            
            # 檢查AI路由決策信息
            if 'ai_routing_decision' in response.metadata:
                routing_info = response.metadata['ai_routing_decision']
                logger.info(f"   路由決策信心度: {routing_info['confidence_score']:.3f}")
                logger.info(f"   預期成本: ${routing_info['expected_cost']:.6f}")
                logger.info(f"   決策理由: {routing_info['reasoning']}")
        else:
            logger.error(f"❌ 分析失敗: {response.error}")
    
    finally:
        await client.close()

async def advanced_routing_strategies_example():
    """高級路由策略示例"""
    logger.info("🎯 高級路由策略示例")
    
    client = create_enhanced_llm_client(enable_ai_routing=True)
    await client.initialize_ai_routing()
    
    try:
        # 不同策略的使用示例
        strategies_to_test = [
            (RoutingStrategy.COST_OPTIMIZED, "成本優化策略"),
            (RoutingStrategy.QUALITY_FIRST, "品質優先策略"),
            (RoutingStrategy.LATENCY_FIRST, "延遲優先策略"),
            (RoutingStrategy.PRIVACY_FIRST, "隱私優先策略")
        ]
        
        for strategy, description in strategies_to_test:
            logger.info(f"\n   測試 {description}")
            
            response = await client.analyze(
                prompt="分析這季度的財務表現",
                analysis_type=AnalysisType.FUNDAMENTAL,
                routing_strategy=strategy,  # 指定路由策略
                user_tier="enterprise",
                priority="standard"
            )
            
            if response.success and 'ai_routing_decision' in response.metadata:
                routing_info = response.metadata['ai_routing_decision']
                logger.info(f"     選擇: {routing_info['selected_provider']}/{routing_info['selected_model']}")
                logger.info(f"     預期成本: ${routing_info['expected_cost']:.6f}")
                logger.info(f"     預期延遲: {routing_info['expected_latency_ms']}ms")
    
    finally:
        await client.close()

async def custom_weights_example():
    """自定義權重配置示例"""
    logger.info("⚖️ 自定義權重配置示例")
    
    client = create_enhanced_llm_client(enable_ai_routing=True)
    await client.initialize_ai_routing()
    
    try:
        # 創建自定義權重（極端重視成本和隱私）
        custom_weights = RoutingWeights(
            cost=0.4,           # 40% 權重給成本
            latency=0.1,        # 10% 權重給延遲
            quality=0.2,        # 20% 權重給品質
            availability=0.15,  # 15% 權重給可用性
            privacy=0.35,       # 35% 權重給隱私
            user_preference=0.0 # 0% 權重給用戶偏好
        )
        
        response = await client.analyze(
            prompt="處理機密的財務數據分析",
            analysis_type=AnalysisType.FUNDAMENTAL,
            custom_weights=custom_weights,  # 使用自定義權重
            user_tier="enterprise",
            priority="high"
        )
        
        if response.success and 'ai_routing_decision' in response.metadata:
            routing_info = response.metadata['ai_routing_decision']
            logger.info(f"   自定義權重路由選擇: {routing_info['selected_provider']}/{routing_info['selected_model']}")
            logger.info(f"   決策理由: {routing_info['reasoning']}")
    
    finally:
        await client.close()

async def performance_feedback_example():
    """性能反饋和優化示例"""
    logger.info("📈 性能反饋和優化示例")
    
    client = create_enhanced_llm_client(
        enable_ai_routing=True,
        feedback_config={
            'enable_auto_adjustment': True,
            'min_feedback_for_adjustment': 5
        }
    )
    await client.initialize_ai_routing()
    
    try:
        # 執行多個請求以生成性能數據
        for i in range(10):
            response = await client.analyze(
                prompt=f"分析投資組合第{i+1}部分",
                analysis_type=AnalysisType.INVESTMENT,
                user_tier="standard",
                enable_feedback_collection=True  # 啟用反饋收集
            )
            
            logger.info(f"   請求 {i+1} 完成: {'成功' if response.success else '失敗'}")
        
        # 獲取性能統計
        stats = client.get_ai_routing_statistics()
        logger.info(f"\n   AI路由統計:")
        logger.info(f"     總請求數: {stats.get('total_ai_routed_requests', 0)}")
        logger.info(f"     回退到傳統路由: {stats.get('fallback_to_legacy_routing', 0)}")
        logger.info(f"     性能反饋記錄: {stats.get('performance_feedback_records', 0)}")
        
        # 嘗試優化路由權重
        optimization_result = await client.optimize_routing_weights(
            strategy=RoutingStrategy.BALANCED,
            analysis_hours=1
        )
        
        logger.info(f"\n   權重優化結果: {optimization_result.get('status', 'unknown')}")
        if 'reasons' in optimization_result:
            for reason in optimization_result['reasons']:
                logger.info(f"     • {reason}")
    
    finally:
        await client.close()

async def monitoring_and_analytics_example():
    """監控和分析示例"""
    logger.info("📊 監控和分析示例")
    
    client = create_enhanced_llm_client(enable_ai_routing=True)
    await client.initialize_ai_routing()
    
    try:
        # 執行一些請求
        for i in range(5):
            await client.analyze(
                prompt=f"市場分析報告 #{i+1}",
                analysis_type=AnalysisType.TECHNICAL,
                user_tier="premium"
            )
        
        # 獲取決策歷史
        history = client.get_routing_decision_history(limit=10)
        logger.info(f"\n   最近決策歷史 ({len(history)} 條記錄):")
        for decision in history[-3:]:  # 顯示最近3條
            logger.info(f"     時間: {decision.get('timestamp', 'N/A')}")
            logger.info(f"     選擇: {decision.get('selected_provider', 'N/A')}/{decision.get('selected_model', 'N/A')}")
            logger.info(f"     信心度: {decision.get('confidence_score', 'N/A')}")
            logger.info(f"     ----")
        
        # 獲取模型性能報告
        performance_report = client.get_model_performance_report(hours_back=24)
        logger.info(f"\n   模型性能報告狀態: {performance_report.get('status', 'unknown')}")
        if performance_report.get('status') == 'success':
            summary = performance_report.get('summary', {})
            for model_key, model_data in summary.items():
                logger.info(f"     {model_key}: 成功率 {model_data.get('success_rate', 0):.2%}")
        
        # 健康檢查
        health = await client.health_check()
        ai_routing_health = health.get('ai_routing', {})
        logger.info(f"\n   AI路由健康狀態:")
        logger.info(f"     啟用: {ai_routing_health.get('enabled', False)}")
        logger.info(f"     初始化: {ai_routing_health.get('initialized', False)}")
        logger.info(f"     路由器狀態: {ai_routing_health.get('router_status', 'unknown')}")
        logger.info(f"     反饋狀態: {ai_routing_health.get('feedback_status', 'unknown')}")
    
    finally:
        await client.close()

async def backward_compatibility_example():
    """向後兼容性示例"""
    logger.info("🔄 向後兼容性示例")
    
    # 1. 禁用AI路由，使用傳統模式
    legacy_client = create_enhanced_llm_client(
        enable_ai_routing=False  # 禁用AI路由
    )
    
    try:
        # 這些調用與原始LLMClient完全相同
        response = await legacy_client.analyze(
            prompt="傳統模式分析",
            analysis_type=AnalysisType.TECHNICAL
        )
        
        logger.info(f"   傳統模式分析: {'成功' if response.success else '失敗'}")
        logger.info(f"   使用的模型: {response.model}")
        
        # 檢查AI路由狀態
        stats = legacy_client.get_ai_routing_statistics()
        logger.info(f"   AI路由狀態: {stats.get('ai_routing_enabled', 'unknown')}")
    
    finally:
        await legacy_client.close()
    
    # 2. 啟用AI路由但保持API兼容
    enhanced_client = create_enhanced_llm_client(
        enable_ai_routing=True  # 啟用AI路由
    )
    
    try:
        await enhanced_client.initialize_ai_routing()
        
        # 相同的API調用，但內部使用AI路由
        response = await enhanced_client.analyze(
            prompt="增強模式分析",
            analysis_type=AnalysisType.TECHNICAL
        )
        
        logger.info(f"   增強模式分析: {'成功' if response.success else '失敗'}")
        logger.info(f"   使用的模型: {response.model}")
        
        # AI路由的額外信息
        if 'ai_routing_decision' in response.metadata:
            routing_info = response.metadata['ai_routing_decision']
            logger.info(f"   路由決策信心度: {routing_info['confidence_score']:.3f}")
    
    finally:
        await enhanced_client.close()

async def error_handling_and_fallback_example():
    """錯誤處理和回退機制示例"""
    logger.info("🛡️ 錯誤處理和回退機制示例")
    
    # 使用可能導致錯誤的配置
    client = create_enhanced_llm_client(
        llm_config={
            'openai_api_key': 'invalid_key',  # 無效的API密鑰
            'gpt_oss_url': 'http://invalid:8080'  # 無效的GPT-OSS URL
        },
        enable_ai_routing=True,
        router_config={
            'enable_audit_logging': True,
            'fallback_on_error': True
        }
    )
    
    try:
        # 嘗試初始化（可能失敗）
        init_success = await client.initialize_ai_routing()
        logger.info(f"   AI路由初始化: {'成功' if init_success else '失敗'}")
        
        # 執行請求（應該回退到可用的方法）
        response = await client.analyze(
            prompt="測試錯誤處理",
            analysis_type=AnalysisType.TECHNICAL,
            user_tier="standard"
        )
        
        logger.info(f"   請求結果: {'成功' if response.success else '失敗'}")
        
        if response.success:
            logger.info(f"   使用的模型: {response.model}")
            logger.info(f"   回退統計: {client.get_ai_routing_statistics().get('fallback_to_legacy_routing', 0)}")
        else:
            logger.info(f"   錯誤信息: {response.error}")
    
    finally:
        await client.close()

async def main():
    """主函數 - 運行所有示例"""
    logger.info("🎉 AI Task Router 完整使用示例開始")
    
    examples = [
        ("基礎使用示例", basic_usage_example),
        ("高級路由策略示例", advanced_routing_strategies_example),
        ("自定義權重配置示例", custom_weights_example),
        ("性能反饋和優化示例", performance_feedback_example),
        ("監控和分析示例", monitoring_and_analytics_example),
        ("向後兼容性示例", backward_compatibility_example),
        ("錯誤處理和回退機制示例", error_handling_and_fallback_example)
    ]
    
    for name, example_func in examples:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"運行 {name}")
            logger.info(f"{'='*60}")
            
            await example_func()
            
            logger.info(f"✅ {name} 完成")
            
        except Exception as e:
            logger.error(f"❌ {name} 失敗: {e}")
        
        # 短暫暫停
        await asyncio.sleep(1)
    
    logger.info(f"\n🎊 所有示例完成!")

if __name__ == "__main__":
    # 運行示例
    asyncio.run(main())