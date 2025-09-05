#!/usr/bin/env python3
"""
GPT-OSS 整合任務1.1全面測試腳本
完整驗證GPT-OSS與TradingAgents系統的整合
"""

import asyncio
import json
import logging
import sys
import os
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 添加項目路徑
project_root = Path(__file__).parent
sys.path.append(str(project_root / "TradingAgents"))

try:
    from tradingagents.utils.llm_client import (
        LLMClient, GPTOSSClient, LLMProvider, AnalysisType,
        LLMError, LLMAPIError, LLMRateLimitError
    )
except ImportError as e:
    print(f"導入錯誤: {e}")
    sys.exit(1)

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTOSSComprehensiveTester:
    """GPT-OSS全面測試器"""
    
    def __init__(self):
        self.results = {}
        self.test_summary = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'warnings': 0,
            'start_time': datetime.now()
        }
        self.base_url = "http://localhost:8080"
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", warning: bool = False):
        """記錄測試結果"""
        self.results[test_name] = {
            'success': success,
            'details': details,
            'warning': warning,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_summary['total_tests'] += 1
        if success:
            self.test_summary['passed_tests'] += 1
        else:
            self.test_summary['failed_tests'] += 1
        if warning:
            self.test_summary['warnings'] += 1
    
    # ==================== 基礎功能測試 ====================
    
    async def test_service_availability(self) -> bool:
        """測試1: 服務可用性"""
        logger.info("=== 測試1: 服務可用性 ===")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"健康狀態: {health_data}")
                self.log_test_result("服務可用性", True, f"狀態: {health_data.get('status')}")
                return True
            else:
                logger.error(f"健康檢查失敗: {response.status_code}")
                self.log_test_result("服務可用性", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"服務連接失敗: {e}")
            self.log_test_result("服務可用性", False, str(e))
            return False
    
    async def test_gptoss_client_basic(self) -> bool:
        """測試2: GPTOSSClient基本功能"""
        logger.info("=== 測試2: GPTOSSClient基本功能 ===")
        
        try:
            client = GPTOSSClient(base_url=self.base_url, timeout=30.0)
            
            # 健康檢查
            health = await client.health_check()
            logger.info(f"客戶端健康檢查: {health.get('status')}")
            
            # 獲取統計信息
            stats = await client.get_stats()
            logger.info(f"初始統計: {stats}")
            
            # 獲取模型列表
            models = await client.get_models()
            logger.info(f"可用模型: {len(models)} 個")
            
            await client.close()
            
            if health.get('status') == 'healthy':
                self.log_test_result("GPTOSSClient基本功能", True, "所有基本功能正常")
                return True
            else:
                self.log_test_result("GPTOSSClient基本功能", False, "健康檢查失敗")
                return False
                
        except Exception as e:
            logger.error(f"GPTOSSClient測試失敗: {e}")
            self.log_test_result("GPTOSSClient基本功能", False, str(e))
            return False
    
    async def test_chat_completions(self) -> bool:
        """測試3: 聊天完成API"""
        logger.info("=== 測試3: 聊天完成API ===")
        
        try:
            client = GPTOSSClient(base_url=self.base_url)
            
            messages = [
                {"role": "system", "content": "你是專業的金融分析師"},
                {"role": "user", "content": "簡單分析一下市場趨勢"}
            ]
            
            start_time = time.time()
            response = await client.chat_completions(
                messages=messages,
                temperature=0.3,
                max_tokens=100
            )
            end_time = time.time()
            
            response_time = end_time - start_time
            content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
            
            logger.info(f"回應時間: {response_time:.2f}秒")
            logger.info(f"回應內容: {content[:100]}...")
            
            await client.close()
            
            if content and len(content) > 10:
                self.log_test_result("聊天完成API", True, f"回應時間: {response_time:.2f}s")
                return True
            else:
                self.log_test_result("聊天完成API", False, "回應內容不足")
                return False
                
        except Exception as e:
            logger.error(f"聊天完成測試失敗: {e}")
            self.log_test_result("聊天完成API", False, str(e))
            return False
    
    # ==================== LLM客戶端整合測試 ====================
    
    async def test_llm_client_initialization(self) -> bool:
        """測試4: LLM客戶端初始化"""
        logger.info("=== 測試4: LLM客戶端初始化 ===")
        
        try:
            config = {
                'provider': 'gpt_oss',
                'gpt_oss_url': self.base_url,
                'model': 'gpt-oss',
                'enable_intelligent_routing': True,
                'provider_priority': ['gpt_oss', 'openai', 'anthropic'],
                'fallback_on_error': True
            }
            
            client = LLMClient(config)
            
            # 檢查客戶端狀態
            stats = client.get_stats()
            logger.info(f"LLM客戶端統計: {stats}")
            
            health_status = client.get_provider_health_status()
            logger.info(f"提供商健康狀態: {health_status}")
            
            await client.close()
            
            if client.gpt_oss_client is not None:
                self.log_test_result("LLM客戶端初始化", True, "GPT-OSS客戶端已初始化")
                return True
            else:
                self.log_test_result("LLM客戶端初始化", False, "GPT-OSS客戶端未初始化")
                return False
                
        except Exception as e:
            logger.error(f"LLM客戶端初始化失敗: {e}")
            self.log_test_result("LLM客戶端初始化", False, str(e))
            return False
    
    async def test_intelligent_routing(self) -> bool:
        """測試5: 智能路由機制"""
        logger.info("=== 測試5: 智能路由機制 ===")
        
        try:
            config = {
                'provider': 'gpt_oss',
                'gpt_oss_url': self.base_url,
                'enable_intelligent_routing': True,
                'provider_priority': ['gpt_oss'],
                'fallback_on_error': True
            }
            
            client = LLMClient(config)
            
            # 測試分析請求
            response = await client.analyze(
                prompt="分析股票市場當前狀況",
                analysis_type=AnalysisType.TECHNICAL,
                analyst_id="technical_analyst"
            )
            
            logger.info(f"智能路由結果: 提供商={response.provider.value}, 成功={response.success}")
            logger.info(f"回應時間: {response.response_time:.2f}秒")
            
            # 檢查健康狀態更新
            health_check = await client.force_provider_health_check()
            logger.info(f"強制健康檢查: {health_check}")
            
            await client.close()
            
            if response.success and response.provider == LLMProvider.GPT_OSS:
                self.log_test_result("智能路由機制", True, "成功路由到GPT-OSS")
                return True
            else:
                self.log_test_result("智能路由機制", False, f"路由失敗: {response.error}")
                return False
                
        except Exception as e:
            logger.error(f"智能路由測試失敗: {e}")
            self.log_test_result("智能路由機制", False, str(e))
            return False
    
    async def test_financial_analysis_integration(self) -> bool:
        """測試6: 金融分析整合"""
        logger.info("=== 測試6: 金融分析整合 ===")
        
        try:
            config = {
                'provider': 'gpt_oss',
                'gpt_oss_url': self.base_url,
                'model': 'gpt-oss'
            }
            
            client = LLMClient(config)
            
            # 技術分析測試
            technical_data = {
                "stock_code": "2330",
                "current_price": 580.0,
                "volume": 25000,
                "ma_5": 575.0,
                "ma_20": 570.0,
                "rsi": 65.5,
                "macd": 2.5
            }
            
            response = await client.analyze(
                prompt="基於技術指標分析台積電投資建議",
                context=technical_data,
                analysis_type=AnalysisType.TECHNICAL,
                analyst_id="technical_analyst",
                stock_id="2330"
            )
            
            logger.info(f"技術分析回應長度: {len(response.content)}")
            logger.info(f"分析用量: {response.usage}")
            
            # 檢查回應是否包含金融術語
            content_lower = response.content.lower()
            financial_terms = ['recommendation', 'buy', 'sell', 'hold', 'rsi', 'ma', 'price', '價格', '建議']
            has_financial_content = any(term in content_lower for term in financial_terms)
            
            await client.close()
            
            if response.success and has_financial_content:
                self.log_test_result("金融分析整合", True, "包含金融專業術語")
                return True
            else:
                self.log_test_result("金融分析整合", False, "缺乏金融專業內容")
                return False
                
        except Exception as e:
            logger.error(f"金融分析整合測試失敗: {e}")
            self.log_test_result("金融分析整合", False, str(e))
            return False
    
    # ==================== 性能和錯誤處理測試 ====================
    
    async def test_error_handling(self) -> bool:
        """測試7: 錯誤處理機制"""
        logger.info("=== 測試7: 錯誤處理機制 ===")
        
        try:
            # 測試無效URL
            invalid_client = GPTOSSClient(base_url="http://invalid-url:9999")
            
            try:
                await invalid_client.health_check()
                invalid_handled = False
            except Exception:
                invalid_handled = True
            finally:
                await invalid_client.close()
            
            # 測試空消息
            valid_client = GPTOSSClient(base_url=self.base_url)
            
            try:
                await valid_client.chat_completions(messages=[])
                empty_handled = False
            except LLMError:
                empty_handled = True
            except Exception:
                empty_handled = False
            finally:
                await valid_client.close()
            
            if invalid_handled and empty_handled:
                self.log_test_result("錯誤處理機制", True, "正確處理各種錯誤情況")
                return True
            else:
                self.log_test_result("錯誤處理機制", False, "錯誤處理不完整")
                return False
                
        except Exception as e:
            logger.error(f"錯誤處理測試失敗: {e}")
            self.log_test_result("錯誤處理機制", False, str(e))
            return False
    
    async def test_concurrent_requests(self) -> bool:
        """測試8: 併發請求處理"""
        logger.info("=== 測試8: 併發請求處理 ===")
        
        try:
            client = GPTOSSClient(base_url=self.base_url)
            
            # 創建多個併發請求
            tasks = []
            for i in range(3):
                messages = [
                    {"role": "user", "content": f"這是第{i+1}個併發請求測試"}
                ]
                task = client.chat_completions(messages=messages, max_tokens=50)
                tasks.append(task)
            
            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            successful_count = 0
            for i, response in enumerate(responses):
                if isinstance(response, Exception):
                    logger.error(f"併發請求{i+1}失敗: {response}")
                else:
                    successful_count += 1
                    logger.info(f"併發請求{i+1}成功")
            
            total_time = end_time - start_time
            logger.info(f"併發測試: {successful_count}/3成功, 總時間: {total_time:.2f}秒")
            
            await client.close()
            
            if successful_count >= 2:  # 至少2個成功
                self.log_test_result("併發請求處理", True, f"{successful_count}/3成功")
                return True
            else:
                self.log_test_result("併發請求處理", False, f"只有{successful_count}/3成功")
                return False
                
        except Exception as e:
            logger.error(f"併發請求測試失敗: {e}")
            self.log_test_result("併發請求處理", False, str(e))
            return False
    
    # ==================== 監控和健康檢查測試 ====================
    
    async def test_monitoring_capabilities(self) -> bool:
        """測試9: 監控能力"""
        logger.info("=== 測試9: 監控能力 ===")
        
        try:
            # 測試指標端點
            metrics_response = requests.get(f"{self.base_url}/metrics", timeout=10)
            
            if metrics_response.status_code == 200:
                metrics_data = metrics_response.json()
                logger.info(f"獲取指標成功: {type(metrics_data)}")
                
                # 測試客戶端統計
                client = GPTOSSClient(base_url=self.base_url)
                
                # 執行一個請求以產生統計數據
                await client.chat_completions([{"role": "user", "content": "測試統計"}], max_tokens=20)
                
                stats = await client.get_stats()
                logger.info(f"客戶端統計: {stats}")
                
                await client.close()
                
                if stats['request_count'] > 0:
                    self.log_test_result("監控能力", True, "指標和統計正常")
                    return True
                else:
                    self.log_test_result("監控能力", False, "統計數據異常")
                    return False
            else:
                self.log_test_result("監控能力", False, f"指標端點失敗: {metrics_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"監控能力測試失敗: {e}")
            self.log_test_result("監控能力", False, str(e))
            return False
    
    async def test_health_check_comprehensive(self) -> bool:
        """測試10: 綜合健康檢查"""
        logger.info("=== 測試10: 綜合健康檢查 ===")
        
        try:
            config = {
                'provider': 'gpt_oss',
                'gpt_oss_url': self.base_url,
                'enable_intelligent_routing': True
            }
            
            client = LLMClient(config)
            
            # LLM客戶端健康檢查
            health_status = await client.health_check()
            logger.info(f"LLM健康狀態: {health_status['status']}")
            
            # 提供商連接測試
            gpt_oss_test = await client.test_provider_connectivity(LLMProvider.GPT_OSS)
            logger.info(f"GPT-OSS連接測試: {gpt_oss_test}")
            
            # 強制健康檢查更新
            forced_health = await client.force_provider_health_check()
            logger.info(f"強制健康檢查: {forced_health}")
            
            await client.close()
            
            is_healthy = (
                health_status.get('status') in ['healthy', 'degraded'] and
                gpt_oss_test.get('connectivity_test', {}).get('healthy', False)
            )
            
            if is_healthy:
                self.log_test_result("綜合健康檢查", True, "所有健康檢查通過")
                return True
            else:
                self.log_test_result("綜合健康檢查", False, "部分健康檢查失敗")
                return False
                
        except Exception as e:
            logger.error(f"綜合健康檢查失敗: {e}")
            self.log_test_result("綜合健康檢查", False, str(e))
            return False
    
    # ==================== 測試執行和報告 ====================
    
    async def run_all_tests(self):
        """運行所有測試"""
        logger.info("開始GPT-OSS整合任務1.1全面測試...")
        
        test_methods = [
            self.test_service_availability,
            self.test_gptoss_client_basic,
            self.test_chat_completions,
            self.test_llm_client_initialization,
            self.test_intelligent_routing,
            self.test_financial_analysis_integration,
            self.test_error_handling,
            self.test_concurrent_requests,
            self.test_monitoring_capabilities,
            self.test_health_check_comprehensive
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(0.5)  # 測試間隔
            except Exception as e:
                logger.error(f"測試執行錯誤: {e}")
        
        self.generate_report()
    
    def generate_report(self):
        """生成測試報告"""
        end_time = datetime.now()
        duration = (end_time - self.test_summary['start_time']).total_seconds()
        
        print("\n" + "="*80)
        print("GPT-OSS 整合任務1.1 全面測試報告")
        print("="*80)
        print(f"測試時間: {self.test_summary['start_time'].strftime('%Y-%m-%d %H:%M:%S')} - {end_time.strftime('%H:%M:%S')}")
        print(f"測試時長: {duration:.1f} 秒")
        print(f"測試總數: {self.test_summary['total_tests']}")
        print(f"通過: {self.test_summary['passed_tests']}")
        print(f"失敗: {self.test_summary['failed_tests']}")
        print(f"警告: {self.test_summary['warnings']}")
        print("-"*80)
        
        for test_name, result in self.results.items():
            status_icon = "PASS" if result['success'] else "FAIL"
            warning_icon = " (WARNING)" if result['warning'] else ""
            print(f"[{status_icon}] {test_name:<25} | {result['details']}{warning_icon}")
        
        print("-"*80)
        success_rate = (self.test_summary['passed_tests'] / self.test_summary['total_tests']) * 100
        print(f"成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("結論: 優秀! GPT-OSS整合完全成功")
            return True
        elif success_rate >= 80:
            print("結論: 良好! GPT-OSS整合基本成功，有少數改進項目")
            return True
        elif success_rate >= 60:
            print("結論: 一般! GPT-OSS整合部分成功，需要解決一些問題")
            return False
        else:
            print("結論: 失敗! GPT-OSS整合存在重大問題，需要全面檢查")
            return False

async def main():
    """主函數"""
    print("GPT-OSS 整合任務1.1 全面測試")
    print("測試範圍:")
    print("1. 基礎功能測試 (服務可用性、客戶端功能、API調用)")
    print("2. LLM客戶端整合測試 (初始化、智能路由、金融分析)")
    print("3. 性能和錯誤處理測試 (錯誤處理、併發請求)")
    print("4. 監控和健康檢查測試 (監控能力、綜合健康檢查)")
    print("\n確保GPT-OSS測試服務運行在 http://localhost:8080\n")
    
    tester = GPTOSSComprehensiveTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())