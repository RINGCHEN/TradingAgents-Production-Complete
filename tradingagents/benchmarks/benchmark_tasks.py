#!/usr/bin/env python3
"""
Benchmark Tasks Implementation
具體基準測試任務實現 - GPT-OSS整合任務1.2.2
"""

import json
import time
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .benchmark_framework import BenchmarkTask, BenchmarkResult, BenchmarkSuite

class ReasoningBenchmark(BenchmarkTask):
    """推理能力基準測試"""
    
    def __init__(self):
        super().__init__(
            name="reasoning",
            description="測試模型的邏輯推理和問題解決能力",
            weight=1.2,
            timeout_seconds=60
        )
        
        self.test_cases = [
            {
                "prompt": "如果所有的貓都是動物，而所有的動物都需要食物，那麼所有的貓都需要食物嗎？請解釋你的邏輯推理過程。",
                "expected_keywords": ["是", "需要", "邏輯", "三段論", "推理"],
                "difficulty": 1
            },
            {
                "prompt": "有三個盒子，一個裝金子，一個裝銀子，一個是空的。每個盒子上都有標籤，但所有標籤都是錯的。如果你只能打開一個盒子，怎樣才能確定哪個盒子裝什麼？",
                "expected_keywords": ["邏輯", "推理", "標籤", "錯誤", "確定"],
                "difficulty": 2
            },
            {
                "prompt": "在一個圓形跑道上，A跑得比B快，B跑得比C快。如果A追上了B，B追上了C，那麼A一定能追上C嗎？解釋原因。",
                "expected_keywords": ["圓形", "速度", "追上", "傳遞性", "必然"],
                "difficulty": 2
            }
        ]
    
    async def run(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> BenchmarkResult:
        """執行推理測試"""
        start_time = datetime.now(timezone.utc)
        
        total_score = 0.0
        responses = []
        latencies = []
        
        for i, test_case in enumerate(self.test_cases):
            case_start = time.time()
            
            try:
                # 調用LLM
                from ..utils.llm_client import LLMRequest, AnalysisType
                
                request = LLMRequest(
                    prompt=test_case["prompt"],
                    analysis_type=AnalysisType.REASONING,
                    max_tokens=500,
                    temperature=0.1
                )
                
                response = await llm_client._execute_request(request)
                case_latency = (time.time() - case_start) * 1000
                
                if response.success:
                    # 評估回應品質
                    score = self._evaluate_reasoning_response(
                        response.content,
                        test_case["expected_keywords"],
                        test_case["difficulty"]
                    )
                    
                    total_score += score
                    responses.append({
                        'case': i + 1,
                        'prompt': test_case["prompt"],
                        'response': response.content,
                        'score': score,
                        'latency_ms': case_latency
                    })
                    latencies.append(case_latency)
                    
                else:
                    self.logger.warning(f"Reasoning test case {i+1} failed: {response.error}")
                    responses.append({
                        'case': i + 1,
                        'prompt': test_case["prompt"],
                        'error': response.error,
                        'score': 0.0,
                        'latency_ms': case_latency
                    })
                    
            except Exception as e:
                self.logger.error(f"Error in reasoning test case {i+1}: {e}")
                responses.append({
                    'case': i + 1,
                    'error': str(e),
                    'score': 0.0
                })
        
        end_time = datetime.now(timezone.utc)
        avg_score = total_score / len(self.test_cases)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return BenchmarkResult(
            task_name=self.name,
            provider=provider,
            model_id=model_id,
            score=avg_score,
            latency_ms=avg_latency,
            success=len(responses) > 0,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'test_cases_completed': len(responses),
                'test_cases_total': len(self.test_cases),
                'detailed_results': responses
            }
        )
    
    def _evaluate_reasoning_response(
        self,
        response: str,
        expected_keywords: List[str],
        difficulty: int
    ) -> float:
        """評估推理回應品質"""
        if not response or len(response.strip()) < 20:
            return 0.0
        
        score = 0.0
        response_lower = response.lower()
        
        # 關鍵詞匹配 (40%)
        keyword_matches = sum(1 for keyword in expected_keywords 
                            if keyword.lower() in response_lower)
        keyword_score = keyword_matches / len(expected_keywords)
        score += keyword_score * 0.4
        
        # 邏輯結構評估 (30%)
        logic_score = self._assess_logical_structure(response)
        score += logic_score * 0.3
        
        # 回應完整性 (20%)
        completeness_score = self._assess_completeness(response)
        score += completeness_score * 0.2
        
        # 清晰度評估 (10%)
        clarity_score = self._assess_clarity(response)
        score += clarity_score * 0.1
        
        # 根據難度調整
        difficulty_multiplier = min(1.0, 0.5 + (0.25 * difficulty))
        final_score = score * difficulty_multiplier
        
        return min(1.0, final_score)
    
    def _assess_logical_structure(self, response: str) -> float:
        """評估邏輯結構"""
        structure_indicators = [
            "因為", "所以", "因此", "如果", "那麼",
            "首先", "其次", "然後", "最後", "總結",
            "because", "therefore", "if", "then", "first", "second"
        ]
        
        found_indicators = sum(1 for indicator in structure_indicators 
                              if indicator.lower() in response.lower())
        
        return min(1.0, found_indicators / 3.0)
    
    def _assess_completeness(self, response: str) -> float:
        """評估回應完整性"""
        # 基於長度和句子數量
        sentences = len(re.split(r'[.!?。！？]', response))
        words = len(response.split())
        
        completeness = 0.0
        if words >= 50:
            completeness += 0.5
        if sentences >= 3:
            completeness += 0.5
        
        return completeness
    
    def _assess_clarity(self, response: str) -> float:
        """評估清晰度"""
        # 簡單的清晰度指標
        clarity = 0.5  # 基礎分
        
        # 避免過度重複
        words = response.lower().split()
        if len(set(words)) / len(words) > 0.7:
            clarity += 0.3
        
        # 適當使用標點符號
        punctuation_ratio = sum(1 for char in response if char in '.,!?;:。，！？；：') / len(response)
        if 0.05 <= punctuation_ratio <= 0.15:
            clarity += 0.2
        
        return min(1.0, clarity)

class CreativityBenchmark(BenchmarkTask):
    """創造力基準測試"""
    
    def __init__(self):
        super().__init__(
            name="creativity",
            description="測試模型的創意思維和創新能力",
            weight=1.0,
            timeout_seconds=90
        )
        
        self.test_cases = [
            {
                "prompt": "請為一家賣雲朵的公司寫一個創意廣告標語，要求既有詩意又實用。",
                "type": "advertising",
                "creativity_factors": ["originality", "metaphor", "emotion", "practicality"]
            },
            {
                "prompt": "想像未來的股票交易是在虛擬現實中進行的，描述一個交易日的場景。",
                "type": "storytelling",
                "creativity_factors": ["imagination", "detail", "innovation", "narrative"]
            },
            {
                "prompt": "如果數字可以有情感，請寫一段對話：數字7和數字13在討論它們對人類的影響。",
                "type": "personification",
                "creativity_factors": ["anthropomorphism", "dialogue", "insight", "humor"]
            }
        ]
    
    async def run(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> BenchmarkResult:
        """執行創造力測試"""
        start_time = datetime.now(timezone.utc)
        
        total_score = 0.0
        responses = []
        latencies = []
        
        for i, test_case in enumerate(self.test_cases):
            case_start = time.time()
            
            try:
                from ..utils.llm_client import LLMRequest, AnalysisType
                
                request = LLMRequest(
                    prompt=test_case["prompt"],
                    analysis_type=AnalysisType.GENERATION,
                    max_tokens=300,
                    temperature=0.8  # 較高的溫度鼓勵創造力
                )
                
                response = await llm_client._execute_request(request)
                case_latency = (time.time() - case_start) * 1000
                
                if response.success:
                    score = self._evaluate_creativity_response(
                        response.content,
                        test_case["creativity_factors"],
                        test_case["type"]
                    )
                    
                    total_score += score
                    responses.append({
                        'case': i + 1,
                        'type': test_case["type"],
                        'prompt': test_case["prompt"],
                        'response': response.content,
                        'score': score,
                        'latency_ms': case_latency
                    })
                    latencies.append(case_latency)
                    
                else:
                    self.logger.warning(f"Creativity test case {i+1} failed: {response.error}")
                    responses.append({
                        'case': i + 1,
                        'error': response.error,
                        'score': 0.0
                    })
                    
            except Exception as e:
                self.logger.error(f"Error in creativity test case {i+1}: {e}")
                responses.append({
                    'case': i + 1,
                    'error': str(e),
                    'score': 0.0
                })
        
        end_time = datetime.now(timezone.utc)
        avg_score = total_score / len(self.test_cases)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return BenchmarkResult(
            task_name=self.name,
            provider=provider,
            model_id=model_id,
            score=avg_score,
            latency_ms=avg_latency,
            success=len(responses) > 0,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'test_cases_completed': len(responses),
                'test_cases_total': len(self.test_cases),
                'detailed_results': responses
            }
        )
    
    def _evaluate_creativity_response(
        self,
        response: str,
        creativity_factors: List[str],
        response_type: str
    ) -> float:
        """評估創造力回應品質"""
        if not response or len(response.strip()) < 30:
            return 0.0
        
        score = 0.0
        
        # 原創性評估 (30%)
        originality_score = self._assess_originality(response)
        score += originality_score * 0.3
        
        # 想像力評估 (25%)
        imagination_score = self._assess_imagination(response)
        score += imagination_score * 0.25
        
        # 表達流暢度 (20%)
        fluency_score = self._assess_fluency(response)
        score += fluency_score * 0.2
        
        # 內容相關性 (15%)
        relevance_score = self._assess_relevance(response, response_type)
        score += relevance_score * 0.15
        
        # 情感表達 (10%)
        emotional_score = self._assess_emotional_expression(response)
        score += emotional_score * 0.1
        
        return min(1.0, score)
    
    def _assess_originality(self, response: str) -> float:
        """評估原創性"""
        # 檢查是否使用了不常見的詞彙或表達
        unique_phrases = [
            "雲朵", "虛擬現實", "數字7", "數字13",  # 測試相關
            "詩意", "夢想", "想像", "創新", "未來"  # 創意相關
        ]
        
        originality = 0.3  # 基礎分
        
        # 使用隱喻和比喻
        metaphor_indicators = ["像", "如", "彷彿", "宛如", "似乎", "猶如"]
        if any(indicator in response for indicator in metaphor_indicators):
            originality += 0.3
        
        # 使用獨特表達
        response_lower = response.lower()
        unique_count = sum(1 for phrase in unique_phrases if phrase in response)
        originality += min(0.4, unique_count * 0.1)
        
        return min(1.0, originality)
    
    def _assess_imagination(self, response: str) -> float:
        """評估想像力"""
        imagination_keywords = [
            "想像", "夢幻", "奇妙", "神奇", "未來", "虛擬", 
            "創意", "創新", "超越", "幻想", "vision", "imagine"
        ]
        
        imagination = 0.2  # 基礎分
        
        response_lower = response.lower()
        keyword_count = sum(1 for keyword in imagination_keywords 
                           if keyword.lower() in response_lower)
        
        imagination += min(0.5, keyword_count * 0.1)
        
        # 檢查是否包含具體的想像場景描述
        if len(response) > 100 and ('場景' in response or '描述' in response):
            imagination += 0.3
        
        return min(1.0, imagination)
    
    def _assess_fluency(self, response: str) -> float:
        """評估表達流暢度"""
        # 基於語法結構和連貫性的簡單評估
        sentences = re.split(r'[.!?。！？]', response)
        words = response.split()
        
        fluency = 0.5  # 基礎分
        
        # 句子長度適中
        if sentences:
            avg_sentence_length = len(words) / len(sentences)
            if 8 <= avg_sentence_length <= 20:
                fluency += 0.3
        
        # 使用連接詞
        connectors = ["和", "但是", "然而", "同時", "因此", "而且", "不過"]
        if any(connector in response for connector in connectors):
            fluency += 0.2
        
        return min(1.0, fluency)
    
    def _assess_relevance(self, response: str, response_type: str) -> float:
        """評估內容相關性"""
        relevance = 0.5  # 基礎分
        
        type_keywords = {
            'advertising': ['廣告', '標語', '宣傳', '品牌', '推廣'],
            'storytelling': ['故事', '場景', '描述', '情節', '敘述'],
            'personification': ['對話', '情感', '性格', '人格化', '角色']
        }
        
        if response_type in type_keywords:
            keywords = type_keywords[response_type]
            keyword_count = sum(1 for keyword in keywords if keyword in response)
            relevance += min(0.5, keyword_count * 0.15)
        
        return min(1.0, relevance)
    
    def _assess_emotional_expression(self, response: str) -> float:
        """評估情感表達"""
        emotion_words = [
            "喜悦", "快樂", "興奮", "溫暖", "感動", "驚喜",
            "憂鬱", "擔心", "害怕", "緊張", "期待", "希望"
        ]
        
        emotion_count = sum(1 for word in emotion_words if word in response)
        return min(1.0, emotion_count * 0.3 + 0.2)

class AccuracyBenchmark(BenchmarkTask):
    """準確性基準測試"""
    
    def __init__(self):
        super().__init__(
            name="accuracy",
            description="測試模型回答的準確性和事實正確性",
            weight=1.3,
            timeout_seconds=45
        )
        
        self.test_cases = [
            {
                "prompt": "台積電(TSMC)的總部位於哪個城市？請提供準確的地理位置。",
                "expected_answer": "新竹",
                "type": "factual",
                "difficulty": 1
            },
            {
                "prompt": "什麼是PE比率？請簡要說明其計算公式和投資意義。",
                "expected_keywords": ["本益比", "股價", "每股盈餘", "估值", "價格"],
                "type": "definition",
                "difficulty": 2
            },
            {
                "prompt": "如果一支股票今天收盤價是100元，昨天是95元，請計算漲跌幅百分比。",
                "expected_answer": "5.26%",
                "calculation": "(100-95)/95*100",
                "type": "calculation",
                "difficulty": 1
            }
        ]
    
    async def run(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> BenchmarkResult:
        """執行準確性測試"""
        start_time = datetime.now(timezone.utc)
        
        total_score = 0.0
        responses = []
        latencies = []
        
        for i, test_case in enumerate(self.test_cases):
            case_start = time.time()
            
            try:
                from ..utils.llm_client import LLMRequest, AnalysisType
                
                request = LLMRequest(
                    prompt=test_case["prompt"],
                    analysis_type=AnalysisType.ANALYSIS,
                    max_tokens=200,
                    temperature=0.1  # 低溫度確保準確性
                )
                
                response = await llm_client._execute_request(request)
                case_latency = (time.time() - case_start) * 1000
                
                if response.success:
                    score = self._evaluate_accuracy_response(response.content, test_case)
                    
                    total_score += score
                    responses.append({
                        'case': i + 1,
                        'type': test_case["type"],
                        'prompt': test_case["prompt"],
                        'response': response.content,
                        'expected': test_case.get("expected_answer"),
                        'score': score,
                        'latency_ms': case_latency
                    })
                    latencies.append(case_latency)
                    
                else:
                    self.logger.warning(f"Accuracy test case {i+1} failed: {response.error}")
                    responses.append({
                        'case': i + 1,
                        'error': response.error,
                        'score': 0.0
                    })
                    
            except Exception as e:
                self.logger.error(f"Error in accuracy test case {i+1}: {e}")
                responses.append({
                    'case': i + 1,
                    'error': str(e),
                    'score': 0.0
                })
        
        end_time = datetime.now(timezone.utc)
        avg_score = total_score / len(self.test_cases)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return BenchmarkResult(
            task_name=self.name,
            provider=provider,
            model_id=model_id,
            score=avg_score,
            latency_ms=avg_latency,
            success=len(responses) > 0,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'test_cases_completed': len(responses),
                'test_cases_total': len(self.test_cases),
                'detailed_results': responses
            }
        )
    
    def _evaluate_accuracy_response(
        self,
        response: str,
        test_case: Dict[str, Any]
    ) -> float:
        """評估準確性回應"""
        if not response or len(response.strip()) < 5:
            return 0.0
        
        response_lower = response.lower()
        test_type = test_case["type"]
        
        if test_type == "factual":
            return self._evaluate_factual_accuracy(response_lower, test_case)
        elif test_type == "definition":
            return self._evaluate_definition_accuracy(response_lower, test_case)
        elif test_type == "calculation":
            return self._evaluate_calculation_accuracy(response, test_case)
        else:
            return self.validate_response(response)
    
    def _evaluate_factual_accuracy(self, response: str, test_case: Dict[str, Any]) -> float:
        """評估事實準確性"""
        expected = test_case["expected_answer"].lower()
        
        if expected in response:
            return 1.0
        
        # 檢查相關詞彙
        if test_case.get("expected_answer") == "新竹":
            if any(word in response for word in ["hsinchu", "科學園區", "竹科"]):
                return 0.8
        
        return 0.0
    
    def _evaluate_definition_accuracy(self, response: str, test_case: Dict[str, Any]) -> float:
        """評估定義準確性"""
        expected_keywords = test_case.get("expected_keywords", [])
        
        score = 0.0
        keyword_count = sum(1 for keyword in expected_keywords 
                           if keyword.lower() in response)
        
        # 關鍵詞匹配得分
        keyword_score = keyword_count / len(expected_keywords) if expected_keywords else 0
        score += keyword_score * 0.7
        
        # 結構完整性
        if len(response) > 50:
            score += 0.2
        
        # 邏輯清晰度
        if any(indicator in response for indicator in ["計算", "公式", "等於", "="]):
            score += 0.1
        
        return min(1.0, score)
    
    def _evaluate_calculation_accuracy(self, response: str, test_case: Dict[str, Any]) -> float:
        """評估計算準確性"""
        expected_answer = test_case["expected_answer"]
        
        # 提取數字
        numbers = re.findall(r'\d+\.?\d*%?', response)
        
        for number in numbers:
            # 處理百分比
            if '%' in number:
                number = number.replace('%', '')
                
            try:
                value = float(number)
                expected_value = float(expected_answer.replace('%', ''))
                
                # 允許小數點誤差
                if abs(value - expected_value) < 0.1:
                    return 1.0
                elif abs(value - expected_value) < 0.5:
                    return 0.8
                elif abs(value - expected_value) < 1.0:
                    return 0.5
                    
            except ValueError:
                continue
        
        return 0.0

class SpeedBenchmark(BenchmarkTask):
    """速度基準測試"""
    
    def __init__(self):
        super().__init__(
            name="speed",
            description="測試模型的回應速度和效率",
            weight=0.8,
            timeout_seconds=30
        )
        
        self.test_cases = [
            {
                "prompt": "請用一句話描述股票市場的基本概念。",
                "expected_tokens": 30,
                "max_time_ms": 2000
            },
            {
                "prompt": "什麼是技術分析？",
                "expected_tokens": 20,
                "max_time_ms": 1500
            },
            {
                "prompt": "列出三個主要的股票指數。",
                "expected_tokens": 15,
                "max_time_ms": 1000
            }
        ]
    
    async def run(
        self,
        llm_client,
        provider: str,
        model_id: str
    ) -> BenchmarkResult:
        """執行速度測試"""
        start_time = datetime.now(timezone.utc)
        
        total_score = 0.0
        responses = []
        latencies = []
        
        for i, test_case in enumerate(self.test_cases):
            case_start = time.time()
            
            try:
                from ..utils.llm_client import LLMRequest, AnalysisType
                
                request = LLMRequest(
                    prompt=test_case["prompt"],
                    analysis_type=AnalysisType.TECHNICAL,
                    max_tokens=100,
                    temperature=0.3
                )
                
                response = await llm_client._execute_request(request)
                case_latency = (time.time() - case_start) * 1000
                
                if response.success:
                    score = self._evaluate_speed_response(
                        response.content, 
                        case_latency, 
                        test_case["max_time_ms"]
                    )
                    
                    total_score += score
                    responses.append({
                        'case': i + 1,
                        'prompt': test_case["prompt"],
                        'response': response.content,
                        'latency_ms': case_latency,
                        'max_time_ms': test_case["max_time_ms"],
                        'score': score
                    })
                    latencies.append(case_latency)
                    
                else:
                    self.logger.warning(f"Speed test case {i+1} failed: {response.error}")
                    responses.append({
                        'case': i + 1,
                        'error': response.error,
                        'score': 0.0,
                        'latency_ms': case_latency
                    })
                    
            except Exception as e:
                self.logger.error(f"Error in speed test case {i+1}: {e}")
                responses.append({
                    'case': i + 1,
                    'error': str(e),
                    'score': 0.0
                })
        
        end_time = datetime.now(timezone.utc)
        avg_score = total_score / len(self.test_cases)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return BenchmarkResult(
            task_name=self.name,
            provider=provider,
            model_id=model_id,
            score=avg_score,
            latency_ms=avg_latency,
            success=len(responses) > 0,
            start_time=start_time,
            end_time=end_time,
            metadata={
                'test_cases_completed': len(responses),
                'test_cases_total': len(self.test_cases),
                'detailed_results': responses,
                'avg_latency_ms': avg_latency
            }
        )
    
    def _evaluate_speed_response(
        self,
        response: str,
        actual_latency_ms: float,
        max_time_ms: float
    ) -> float:
        """評估速度表現"""
        # 基本回應品質檢查
        quality_score = self.validate_response(response)
        if quality_score < 0.3:
            return 0.0
        
        # 速度評分
        if actual_latency_ms <= max_time_ms * 0.5:
            speed_score = 1.0
        elif actual_latency_ms <= max_time_ms:
            speed_score = 0.8
        elif actual_latency_ms <= max_time_ms * 1.5:
            speed_score = 0.6
        elif actual_latency_ms <= max_time_ms * 2:
            speed_score = 0.3
        else:
            speed_score = 0.1
        
        # 組合評分 (品質40% + 速度60%)
        return quality_score * 0.4 + speed_score * 0.6

class StandardBenchmarkSuite(BenchmarkSuite):
    """標準基準測試套件"""
    
    def __init__(self):
        super().__init__(
            name="standard",
            description="標準LLM能力基準測試套件",
            tasks=[
                ReasoningBenchmark(),
                CreativityBenchmark(),
                AccuracyBenchmark(),
                SpeedBenchmark()
            ]
        )