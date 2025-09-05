#!/usr/bin/env python3
"""
Model Capability System Usage Example
模型能力系統使用示例 - GPT-OSS整合任務1.2.2

展示如何使用完整的模型能力系統進行智能路由和基準測試
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加 TradingAgents 到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "TradingAgents"))

from tradingagents.services.model_capability_service import ModelCapabilityService
from tradingagents.utils.llm_client import LLMClient

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def example_intelligent_analysis():
    """示例：使用智能路由進行分析"""
    logger.info("🎯 示例：智能路由分析")
    
    # 初始化服務
    service = ModelCapabilityService()
    await service.initialize()
    
    try:
        # 使用最優模型進行財務分析
        result = await service.analyze_with_optimal_model(
            prompt="請分析台積電(2330)的最新財務表現和投資前景",
            task_type="financial_summary",
            context={
                "stock_id": "2330",
                "market": "taiwan",
                "data_source": "finmind"
            },
            user_id="user_001",
            requires_high_quality=True,
            max_acceptable_latency=10000  # 10秒
        )
        
        if result['success']:
            logger.info(f"✅ 分析成功!")
            logger.info(f"   選用模型: {result['routing_decision']['selected_provider']}/{result['routing_decision']['selected_model']}")
            logger.info(f"   路由推理: {result['routing_decision']['reasoning']}")
            logger.info(f"   實際延遲: {result['performance']['actual_latency_ms']:.0f}ms")
            logger.info(f"   預期成本: ${result['routing_decision']['expected_cost']:.4f}")
            logger.info(f"   分析內容: {result['content'][:200]}...")
        else:
            logger.error(f"❌ 分析失敗: {result['error']}")
    
    finally:
        await service.shutdown()

async def example_model_benchmarking():
    """示例：模型基準測試"""
    logger.info("📊 示例：模型基準測試")
    
    service = ModelCapabilityService()
    await service.initialize()
    
    try:
        # 對所有模型進行基準測試
        logger.info("開始對所有註冊模型進行基準測試...")
        
        # 注意：這會使用模擬客戶端，實際使用時需要真實的LLM客戶端
        benchmark_result = await service.run_all_model_benchmarks(suite_name="standard")
        
        summary = benchmark_result.get('summary', {})
        logger.info(f"✅ 基準測試完成!")
        logger.info(f"   總模型數: {summary.get('total_models', 0)}")
        logger.info(f"   成功測試: {summary.get('successful_models', 0)}")
        logger.info(f"   平均評分: {summary.get('avg_overall_score', 0):.3f}")
        
        # 顯示最佳模型
        best_model = summary.get('best_model')
        if best_model:
            logger.info(f"   最佳模型: {best_model['name']} (評分: {best_model['score']:.3f})")
    
    finally:
        await service.shutdown()

async def example_model_recommendations():
    """示例：獲取模型推薦"""
    logger.info("💡 示例：模型推薦")
    
    service = ModelCapabilityService()
    await service.initialize()
    
    try:
        # 定義任務需求
        task_requirements = {
            'min_capability_score': 0.8,    # 最低能力要求
            'max_cost_per_1k': 0.02,       # 最大成本限制
            'max_latency_ms': 3000,         # 最大延遲要求
            'privacy_level': 'local',       # 隱私要求：本地處理
            'required_features': ['reasoning', 'analysis']  # 必需功能
        }
        
        recommendations = await service.get_model_recommendations(
            task_requirements=task_requirements,
            limit=5
        )
        
        logger.info(f"✅ 獲得 {len(recommendations)} 個模型推薦:")
        for i, rec in enumerate(recommendations, 1):
            model = rec['model']
            score = rec['match_score']
            reason = rec['recommendation_reason']
            
            logger.info(f"   {i}. {model['provider']}/{model['model_id']}")
            logger.info(f"      匹配度: {score:.3f}")
            logger.info(f"      推薦理由: {reason}")
            logger.info(f"      能力評分: {model['capability_score']:.3f}")
            logger.info(f"      平均延遲: {model['avg_latency_ms']:.0f}ms")
            logger.info(f"      隱私級別: {model['privacy_level']}")
            logger.info("")
    
    finally:
        await service.shutdown()

async def example_performance_monitoring():
    """示例：性能監控"""
    logger.info("📈 示例：性能監控")
    
    service = ModelCapabilityService()
    await service.initialize()
    
    try:
        # 獲取當前性能指標
        metrics = service.get_current_metrics()
        logger.info(f"✅ 當前監控 {len(metrics)} 個性能指標")
        
        for metric_key, stats in list(metrics.items())[:3]:  # 只顯示前3個
            if stats:
                logger.info(f"   {metric_key}:")
                logger.info(f"     平均值: {stats.get('mean', 0):.3f}")
                logger.info(f"     最大值: {stats.get('max', 0):.3f}")
                logger.info(f"     最小值: {stats.get('min', 0):.3f}")
                logger.info(f"     樣本數: {stats.get('count', 0)}")
        
        # 獲取性能報告
        report = await service.get_performance_report(hours_back=24)
        logger.info(f"✅ 性能報告生成完成")
        logger.info(f"   總指標數: {report['summary']['total_metrics']}")
        
        # 顯示建議
        recommendations = report.get('recommendations', [])
        if recommendations:
            logger.info("   📋 系統建議:")
            for rec in recommendations[:3]:
                logger.info(f"     - {rec}")
    
    finally:
        await service.shutdown()

async def example_system_health_check():
    """示例：系統健康檢查"""
    logger.info("🔍 示例：系統健康檢查")
    
    service = ModelCapabilityService()
    await service.initialize()
    
    try:
        # 執行健康檢查
        health = await service.health_check()
        
        logger.info(f"✅ 系統健康狀態: {health['overall_status']}")
        logger.info("   組件狀態:")
        
        for component, status in health.get('components', {}).items():
            if isinstance(status, dict):
                comp_status = status.get('status', 'unknown')
                logger.info(f"     {component}: {comp_status}")
                if 'error' in status:
                    logger.info(f"       錯誤: {status['error']}")
            else:
                logger.info(f"     {component}: {status}")
        
        # 獲取系統統計
        stats = await service.get_system_statistics()
        logger.info("   📊 系統統計:")
        logger.info(f"     註冊模型數: {stats['models']['total_models']}")
        logger.info(f"     任務類型數: {stats['tasks']['total_task_types']}")
        logger.info(f"     LLM請求數: {stats['llm_client']['request_count']}")
        logger.info(f"     基準測試數: {stats['benchmarks']['total_runs']}")
    
    finally:
        await service.shutdown()

async def main():
    """主函數 - 執行所有示例"""
    logger.info("🚀 Model Capability System 使用示例")
    logger.info("=" * 60)
    
    examples = [
        ("智能路由分析", example_intelligent_analysis),
        ("模型推薦", example_model_recommendations), 
        ("性能監控", example_performance_monitoring),
        ("系統健康檢查", example_system_health_check),
        # ("模型基準測試", example_model_benchmarking)  # 註釋掉避免長時間執行
    ]
    
    for name, example_func in examples:
        logger.info(f"\n{'='*60}")
        logger.info(f"執行示例: {name}")
        logger.info(f"{'='*60}")
        
        try:
            await example_func()
            logger.info(f"✅ {name} 示例執行成功")
        except Exception as e:
            logger.error(f"❌ {name} 示例執行失敗: {e}")
            import traceback
            traceback.print_exc()
    
    logger.info(f"\n{'='*60}")
    logger.info("🎉 所有示例執行完畢!")
    logger.info("💡 提示：實際使用時請確保：")
    logger.info("   1. 配置正確的LLM API金鑰")
    logger.info("   2. GPT-OSS本地服務正常運行")
    logger.info("   3. 數據庫連接正常")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 示例被用戶中斷")
    except Exception as e:
        logger.error(f"❌ 執行過程中出現錯誤: {e}")
        import traceback
        traceback.print_exc()