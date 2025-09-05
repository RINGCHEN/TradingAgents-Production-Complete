"""
Validation System for Financial AI Training
金融AI訓練驗證系統

任務4.3: 驗證集和評估指標系統
負責人: 小k (AI訓練專家團隊)

提供：
- 驗證集管理
- 多維度評估指標
- 自動化驗證流程
- 性能基準測試
- 驗證報告生成
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import torch

from .reward_models import create_reward_model, FinancialRewardModel
from .data_manager import TrainingDataManager

logger = logging.getLogger(__name__)


@dataclass
class ValidationMetrics:
    """驗證指標數據結構"""
    
    # 核心評估指標
    accuracy_score: float = 0.0
    relevance_score: float = 0.0
    risk_awareness_score: float = 0.0
    actionability_score: float = 0.0
    compliance_score: float = 0.0
    overall_score: float = 0.0
    
    # 語言品質指標
    fluency_score: float = 0.0
    coherence_score: float = 0.0
    informativeness_score: float = 0.0
    
    # 金融專業指標
    financial_accuracy: float = 0.0
    risk_assessment_quality: float = 0.0
    investment_logic_score: float = 0.0
    
    # 統計指標
    response_length_avg: float = 0.0
    response_length_std: float = 0.0
    financial_terms_density: float = 0.0
    risk_mentions_ratio: float = 0.0
    compliance_coverage: float = 0.0
    
    # 性能指標
    inference_time_avg: float = 0.0
    tokens_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """轉換為字典格式"""
        return asdict(self)


@dataclass
class ValidationResult:
    """驗證結果數據結構"""
    
    model_name: str
    validation_date: str
    dataset_name: str
    sample_count: int
    metrics: ValidationMetrics
    detailed_scores: List[Dict[str, Any]]
    benchmark_comparison: Dict[str, float]
    recommendations: List[str]
    validation_config: Dict[str, Any]


class ValidationDatasetManager:
    """驗證數據集管理器"""
    
    def __init__(self, validation_dir: str = "./data/validation"):
        self.validation_dir = Path(validation_dir)
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        # 預定義的驗證數據集
        self.validation_datasets = {
            'financial_analysis': self._create_financial_analysis_dataset(),
            'investment_advice': self._create_investment_advice_dataset(),
            'risk_assessment': self._create_risk_assessment_dataset(),
            'market_commentary': self._create_market_commentary_dataset()
        }
    
    def _create_financial_analysis_dataset(self) -> List[Dict[str, Any]]:
        """創建金融分析驗證數據集"""
        return [
            {
                'query': '分析台積電(2330)的投資價值',
                'expected_response': '台積電作為全球半導體龍頭，具有先進製程技術優勢和穩定客戶關係。投資亮點包括AI晶片需求增長和長期技術領先地位。風險因素需考慮地緣政治影響和景氣循環。建議長期投資者可分批布局，但請注意投資風險，建議諮詢專業投資顧問。',
                'context': {
                    'stock_code': '2330',
                    'company': '台積電',
                    'sector': '半導體',
                    'analysis_type': 'fundamental'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.3,
                    'risk_awareness_weight': 0.25,
                    'actionability_weight': 0.25,
                    'compliance_weight': 0.2
                }
            },
            {
                'query': '鴻海(2317)的財務狀況如何？',
                'expected_response': '鴻海為全球最大電子代工廠，營收規模龐大但毛利率相對較低。近年積極轉型發展電動車、半導體等新事業。財務體質穩健，現金流充沛，但需關注轉型成效和競爭壓力。投資前請詳細評估個人風險承受度，此為分析觀點非投資建議。',
                'context': {
                    'stock_code': '2317',
                    'company': '鴻海',
                    'sector': '電子代工',
                    'analysis_type': 'financial'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.35,
                    'risk_awareness_weight': 0.2,
                    'actionability_weight': 0.25,
                    'compliance_weight': 0.2
                }
            },
            {
                'query': '聯發科(2454)與高通的競爭優勢比較',
                'expected_response': '聯發科在中低階晶片市場具有成本優勢，高通在高階處理器和專利技術領先。聯發科近年在5G和AI晶片領域快速追趕，但高通在旗艦手機市場仍占主導地位。兩家公司各有優勢，投資需考慮技術發展趨勢和市場競爭變化。投資有風險，請謹慎評估。',
                'context': {
                    'stock_code': '2454',
                    'company': '聯發科',
                    'sector': '半導體',
                    'analysis_type': 'competitive'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.3,
                    'risk_awareness_weight': 0.2,
                    'actionability_weight': 0.3,
                    'compliance_weight': 0.2
                }
            }
        ]
    
    def _create_investment_advice_dataset(self) -> List[Dict[str, Any]]:
        """創建投資建議驗證數據集"""
        return [
            {
                'query': '現在適合投資台股嗎？',
                'expected_response': '台股投資需考慮多項因素：經濟基本面、國際情勢、資金流向等。建議分散投資、定期定額、長期持有的策略。投資前應評估個人財務狀況和風險承受度，建議諮詢專業財務顧問。此為一般性分析，非個人化投資建議，投資有風險請謹慎評估。',
                'context': {
                    'market': '台股',
                    'investment_type': 'general_advice',
                    'risk_level': 'medium'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.25,
                    'risk_awareness_weight': 0.3,
                    'actionability_weight': 0.25,
                    'compliance_weight': 0.2
                }
            },
            {
                'query': '新手投資者應該如何開始？',
                'expected_response': '新手投資建議：1.建立緊急預備金 2.學習基本投資知識 3.從低風險產品開始 4.分散投資降低風險 5.定期檢視調整。可考慮ETF、定期定額等方式入門。最重要是風險管理，不要投入無法承受損失的資金。建議尋求專業理財顧問協助制定個人化投資計劃。',
                'context': {
                    'investor_type': 'beginner',
                    'investment_type': 'education',
                    'risk_level': 'low'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.2,
                    'risk_awareness_weight': 0.35,
                    'actionability_weight': 0.3,
                    'compliance_weight': 0.15
                }
            }
        ]
    
    def _create_risk_assessment_dataset(self) -> List[Dict[str, Any]]:
        """創建風險評估驗證數據集"""
        return [
            {
                'query': '投資高股息股票有什麼風險？',
                'expected_response': '高股息股票風險包括：1.股息削減風險-公司獲利下降可能減少配息 2.股價波動風險-高股息不保證股價穩定 3.產業集中風險-傳統高股息多集中特定產業 4.利率風險-升息時吸引力下降。投資前需評估公司基本面、股息穩定性和個人風險承受度。建議分散投資，諮詢專業意見。',
                'context': {
                    'investment_type': 'dividend_stocks',
                    'risk_focus': 'comprehensive',
                    'analysis_depth': 'detailed'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.25,
                    'risk_awareness_weight': 0.4,
                    'actionability_weight': 0.2,
                    'compliance_weight': 0.15
                }
            }
        ]
    
    def _create_market_commentary_dataset(self) -> List[Dict[str, Any]]:
        """創建市場評論驗證數據集"""
        return [
            {
                'query': '如何看待當前的市場波動？',
                'expected_response': '市場波動是正常現象，反映投資者對經濟、政策、地緣政治等因素的反應。面對波動建議：1.保持冷靜理性 2.堅持長期投資策略 3.適度分散風險 4.避免情緒化決策。短期波動難以預測，重要的是基於基本面做投資決策。市場波動也創造投資機會，但需謹慎評估風險。',
                'context': {
                    'market_condition': 'volatile',
                    'commentary_type': 'general',
                    'time_horizon': 'mixed'
                },
                'evaluation_criteria': {
                    'accuracy_weight': 0.3,
                    'risk_awareness_weight': 0.25,
                    'actionability_weight': 0.25,
                    'compliance_weight': 0.2
                }
            }
        ]
    
    def get_validation_dataset(self, dataset_name: str) -> List[Dict[str, Any]]:
        """獲取指定的驗證數據集"""
        if dataset_name not in self.validation_datasets:
            raise ValueError(f"未知的驗證數據集: {dataset_name}")
        
        return self.validation_datasets[dataset_name]
    
    def get_all_datasets(self) -> Dict[str, List[Dict[str, Any]]]:
        """獲取所有驗證數據集"""
        return self.validation_datasets.copy()
    
    def save_validation_dataset(self, dataset_name: str, output_path: Optional[str] = None):
        """保存驗證數據集到文件"""
        if output_path is None:
            output_path = self.validation_dir / f"{dataset_name}_validation.json"
        
        dataset = self.get_validation_dataset(dataset_name)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        
        logger.info(f"驗證數據集已保存: {output_path}")


class FinancialValidationSystem:
    """金融AI模型驗證系統"""
    
    def __init__(
        self,
        reward_model: Optional[FinancialRewardModel] = None,
        validation_dir: str = "./data/validation"
    ):
        self.reward_model = reward_model or create_reward_model("financial")
        self.dataset_manager = ValidationDatasetManager(validation_dir)
        self.validation_history = []
        
        # 基準分數（用於比較）
        self.benchmark_scores = {
            'accuracy_score': 0.70,
            'relevance_score': 0.75,
            'risk_awareness_score': 0.65,
            'actionability_score': 0.70,
            'compliance_score': 0.80,
            'overall_score': 0.72
        }
    
    def validate_model(
        self,
        model,
        tokenizer,
        dataset_name: str = 'financial_analysis',
        model_name: str = 'unknown_model',
        validation_config: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        執行模型驗證
        
        Args:
            model: 要驗證的模型
            tokenizer: 對應的tokenizer
            dataset_name: 驗證數據集名稱
            model_name: 模型名稱
            validation_config: 驗證配置
            
        Returns:
            ValidationResult: 驗證結果
        """
        logger.info(f"🔍 開始驗證模型: {model_name} (數據集: {dataset_name})")
        
        # 獲取驗證數據集
        validation_data = self.dataset_manager.get_validation_dataset(dataset_name)
        
        # 默認驗證配置
        if validation_config is None:
            validation_config = {
                'max_length': 512,
                'temperature': 0.7,
                'do_sample': True,
                'num_return_sequences': 1
            }
        
        # 執行驗證
        detailed_scores = []
        all_metrics = []
        performance_metrics = []
        
        model.eval()
        
        for i, item in enumerate(validation_data):
            logger.info(f"處理驗證樣本 {i+1}/{len(validation_data)}")
            
            query = item['query']
            expected_response = item['expected_response']
            context = item.get('context', {})
            evaluation_criteria = item.get('evaluation_criteria', {})
            
            # 生成模型回應並測量性能
            generated_response, performance = self._generate_with_performance_tracking(
                model, tokenizer, query, validation_config
            )
            
            # 計算評估分數
            scores = self._compute_detailed_scores(
                query, generated_response, expected_response, context, evaluation_criteria
            )
            
            # 記錄詳細結果
            detailed_result = {
                'sample_id': i + 1,
                'query': query,
                'expected_response': expected_response,
                'generated_response': generated_response,
                'context': context,
                'scores': scores,
                'performance': performance
            }
            
            detailed_scores.append(detailed_result)
            all_metrics.append(scores)
            performance_metrics.append(performance)
        
        # 計算平均指標
        avg_metrics = self._compute_average_metrics(all_metrics, performance_metrics)
        
        # 與基準比較
        benchmark_comparison = self._compare_with_benchmark(avg_metrics)
        
        # 生成建議
        recommendations = self._generate_validation_recommendations(avg_metrics, detailed_scores)
        
        # 創建驗證結果
        result = ValidationResult(
            model_name=model_name,
            validation_date=datetime.now().isoformat(),
            dataset_name=dataset_name,
            sample_count=len(validation_data),
            metrics=avg_metrics,
            detailed_scores=detailed_scores,
            benchmark_comparison=benchmark_comparison,
            recommendations=recommendations,
            validation_config=validation_config
        )
        
        # 添加到歷史記錄
        self.validation_history.append(result)
        
        logger.info(f"✅ 驗證完成 - 總體分數: {avg_metrics.overall_score:.3f}")
        
        return result
    
    def _generate_with_performance_tracking(
        self,
        model,
        tokenizer,
        query: str,
        config: Dict[str, Any]
    ) -> Tuple[str, Dict[str, float]]:
        """生成回應並追蹤性能指標"""
        
        import time
        import psutil
        import os
        
        # 記錄開始狀態
        start_time = time.time()
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 編碼輸入
        inputs = tokenizer(
            query,
            return_tensors="pt",
            max_length=256,
            truncation=True
        )
        
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}
        
        # 生成回應
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=config.get('max_length', 512),
                temperature=config.get('temperature', 0.7),
                do_sample=config.get('do_sample', True),
                num_return_sequences=config.get('num_return_sequences', 1),
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # 解碼回應
        response = tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        ).strip()
        
        # 計算性能指標
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        inference_time = end_time - start_time
        tokens_generated = len(outputs[0]) - inputs['input_ids'].shape[1]
        tokens_per_second = tokens_generated / inference_time if inference_time > 0 else 0
        memory_usage = end_memory - start_memory
        
        performance = {
            'inference_time': inference_time,
            'tokens_per_second': tokens_per_second,
            'memory_usage_mb': memory_usage,
            'tokens_generated': tokens_generated
        }
        
        return response, performance
    
    def _compute_detailed_scores(
        self,
        query: str,
        generated_response: str,
        expected_response: str,
        context: Dict[str, Any],
        evaluation_criteria: Dict[str, float]
    ) -> Dict[str, float]:
        """計算詳細評估分數"""
        
        # 使用獎勵模型計算基礎分數
        reward_components = self.reward_model._compute_reward_components(
            query, generated_response, context
        )
        
        # 計算與期望回應的相似度
        similarity_score = self._compute_response_similarity(expected_response, generated_response)
        
        # 計算語言品質分數
        fluency_score = self._evaluate_fluency(generated_response)
        coherence_score = self._evaluate_coherence(generated_response)
        informativeness_score = self._evaluate_informativeness(generated_response)
        
        # 計算金融專業分數
        financial_accuracy = self._evaluate_financial_accuracy(generated_response, context)
        risk_assessment_quality = self._evaluate_risk_assessment_quality(generated_response)
        investment_logic_score = self._evaluate_investment_logic(generated_response)
        
        # 統計指標
        response_length = len(generated_response)
        financial_terms_count = self._count_financial_terms(generated_response)
        financial_terms_density = financial_terms_count / len(generated_response.split()) if generated_response else 0
        risk_mentions = self._count_risk_mentions(generated_response)
        risk_mentions_ratio = risk_mentions / len(generated_response.split()) if generated_response else 0
        compliance_mentions = self._count_compliance_mentions(generated_response)
        compliance_coverage = min(compliance_mentions / 2, 1.0)  # 假設需要至少2個合規提及
        
        return {
            'accuracy_score': reward_components.accuracy_score,
            'relevance_score': reward_components.relevance_score,
            'risk_awareness_score': reward_components.risk_awareness_score,
            'actionability_score': reward_components.actionability_score,
            'compliance_score': reward_components.compliance_score,
            'similarity_score': similarity_score,
            'fluency_score': fluency_score,
            'coherence_score': coherence_score,
            'informativeness_score': informativeness_score,
            'financial_accuracy': financial_accuracy,
            'risk_assessment_quality': risk_assessment_quality,
            'investment_logic_score': investment_logic_score,
            'response_length': response_length,
            'financial_terms_density': financial_terms_density,
            'risk_mentions_ratio': risk_mentions_ratio,
            'compliance_coverage': compliance_coverage
        }
    
    def _compute_response_similarity(self, expected: str, generated: str) -> float:
        """計算回應相似度"""
        expected_words = set(expected.lower().split())
        generated_words = set(generated.lower().split())
        
        if not expected_words and not generated_words:
            return 1.0
        
        intersection = expected_words.intersection(generated_words)
        union = expected_words.union(generated_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _evaluate_fluency(self, text: str) -> float:
        """評估語言流暢度"""
        # 簡化的流暢度評估
        score = 0.5
        
        # 檢查句子結構
        sentences = text.split('。')
        if len(sentences) >= 2:
            score += 0.2
        
        # 檢查標點符號使用
        punctuation_count = sum(1 for char in text if char in '，。！？；：')
        if punctuation_count >= len(sentences):
            score += 0.2
        
        # 檢查重複詞語
        words = text.split()
        unique_words = set(words)
        if len(unique_words) / len(words) > 0.8:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_coherence(self, text: str) -> float:
        """評估邏輯連貫性"""
        score = 0.5
        
        # 檢查邏輯連接詞
        logical_connectors = ['因為', '所以', '但是', '然而', '此外', '另外', '因此', '由於']
        connector_count = sum(1 for connector in logical_connectors if connector in text)
        if connector_count >= 2:
            score += 0.3
        elif connector_count >= 1:
            score += 0.2
        
        # 檢查主題一致性（簡化版）
        if len(text) > 50 and not any(word in text for word in ['突然', '忽然', '莫名']):
            score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_informativeness(self, text: str) -> float:
        """評估信息豐富度"""
        score = 0.3
        
        # 檢查具體數據
        import re
        numbers = re.findall(r'\d+', text)
        if len(numbers) >= 3:
            score += 0.3
        elif len(numbers) >= 1:
            score += 0.2
        
        # 檢查具體事實
        fact_indicators = ['根據', '數據顯示', '研究表明', '統計', '報告', '分析師']
        fact_count = sum(1 for indicator in fact_indicators if indicator in text)
        if fact_count >= 2:
            score += 0.2
        elif fact_count >= 1:
            score += 0.1
        
        # 檢查詳細程度
        if len(text) >= 100:
            score += 0.2
        elif len(text) >= 50:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_financial_accuracy(self, text: str, context: Dict[str, Any]) -> float:
        """評估金融準確性"""
        score = 0.5
        
        # 檢查是否提及相關公司/股票
        if 'stock_code' in context:
            stock_code = context['stock_code']
            if stock_code in text:
                score += 0.2
        
        if 'company' in context:
            company = context['company']
            if company in text:
                score += 0.2
        
        # 檢查行業相關術語
        if 'sector' in context:
            sector = context['sector']
            sector_terms = {
                '半導體': ['晶片', '製程', '代工', '封測'],
                '金融': ['銀行', '保險', '證券', '利率'],
                '電子': ['代工', '組裝', '供應鏈']
            }
            
            if sector in sector_terms:
                relevant_terms = sum(1 for term in sector_terms[sector] if term in text)
                if relevant_terms >= 2:
                    score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_risk_assessment_quality(self, text: str) -> float:
        """評估風險評估品質"""
        score = 0.3
        
        # 檢查風險類型提及
        risk_types = ['市場風險', '流動性風險', '信用風險', '操作風險', '政策風險', '匯率風險']
        risk_type_mentions = sum(1 for risk_type in risk_types if risk_type in text)
        
        if risk_type_mentions >= 2:
            score += 0.3
        elif risk_type_mentions >= 1:
            score += 0.2
        
        # 檢查風險量化
        quantitative_terms = ['波動', '下跌', '損失', '機率', '可能性']
        quant_mentions = sum(1 for term in quantitative_terms if term in text)
        
        if quant_mentions >= 2:
            score += 0.2
        elif quant_mentions >= 1:
            score += 0.1
        
        # 檢查風險管理建議
        management_terms = ['分散', '停損', '控制', '管理', '降低']
        mgmt_mentions = sum(1 for term in management_terms if term in text)
        
        if mgmt_mentions >= 2:
            score += 0.2
        elif mgmt_mentions >= 1:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_investment_logic(self, text: str) -> float:
        """評估投資邏輯"""
        score = 0.4
        
        # 檢查分析框架
        analysis_terms = ['基本面', '技術面', '估值', '成長性', '獲利能力']
        analysis_mentions = sum(1 for term in analysis_terms if term in text)
        
        if analysis_mentions >= 3:
            score += 0.3
        elif analysis_mentions >= 1:
            score += 0.2
        
        # 檢查投資建議邏輯
        logic_indicators = ['因為', '由於', '基於', '考慮到', '鑑於']
        logic_count = sum(1 for indicator in logic_indicators if indicator in text)
        
        if logic_count >= 2:
            score += 0.2
        elif logic_count >= 1:
            score += 0.1
        
        # 檢查時間框架
        time_frames = ['短期', '中期', '長期', '未來', '目前']
        time_mentions = sum(1 for frame in time_frames if frame in text)
        
        if time_mentions >= 2:
            score += 0.1
        
        return min(score, 1.0)
    
    def _count_financial_terms(self, text: str) -> int:
        """計算金融術語數量"""
        financial_terms = [
            '投資', '股票', '基金', '債券', '風險', '報酬', '獲利', '虧損',
            '市場', '經濟', '金融', '銀行', '保險', '證券', '期貨', '選擇權',
            '本益比', '股息', '殖利率', '現金流', '資產', '負債', '營收', '淨利',
            '成長', '價值', '動能', '趨勢', '支撐', '壓力', '突破', '整理'
        ]
        
        return sum(1 for term in financial_terms if term in text)
    
    def _count_risk_mentions(self, text: str) -> int:
        """計算風險提及次數"""
        risk_terms = ['風險', '不確定', '波動', '謹慎', '小心', '注意', '警告', '危險']
        return sum(1 for term in risk_terms if term in text)
    
    def _count_compliance_mentions(self, text: str) -> int:
        """計算合規提及次數"""
        compliance_terms = ['僅供參考', '投資有風險', '請謹慎', '非投資建議', '專業諮詢', '風險自負']
        return sum(1 for term in compliance_terms if term in text)
    
    def _compute_average_metrics(
        self,
        all_scores: List[Dict[str, float]],
        performance_metrics: List[Dict[str, float]]
    ) -> ValidationMetrics:
        """計算平均指標"""
        
        # 計算各項平均分數
        avg_scores = {}
        for key in all_scores[0].keys():
            if key != 'response_length':  # 長度單獨處理
                avg_scores[key] = np.mean([scores[key] for scores in all_scores])
        
        # 計算長度統計
        lengths = [scores['response_length'] for scores in all_scores]
        response_length_avg = np.mean(lengths)
        response_length_std = np.std(lengths)
        
        # 計算性能平均值
        avg_performance = {}
        for key in performance_metrics[0].keys():
            avg_performance[key] = np.mean([perf[key] for perf in performance_metrics])
        
        # 計算總體分數
        core_metrics = ['accuracy_score', 'relevance_score', 'risk_awareness_score', 
                       'actionability_score', 'compliance_score']
        overall_score = np.mean([avg_scores[metric] for metric in core_metrics])
        
        return ValidationMetrics(
            accuracy_score=avg_scores['accuracy_score'],
            relevance_score=avg_scores['relevance_score'],
            risk_awareness_score=avg_scores['risk_awareness_score'],
            actionability_score=avg_scores['actionability_score'],
            compliance_score=avg_scores['compliance_score'],
            overall_score=overall_score,
            fluency_score=avg_scores['fluency_score'],
            coherence_score=avg_scores['coherence_score'],
            informativeness_score=avg_scores['informativeness_score'],
            financial_accuracy=avg_scores['financial_accuracy'],
            risk_assessment_quality=avg_scores['risk_assessment_quality'],
            investment_logic_score=avg_scores['investment_logic_score'],
            response_length_avg=response_length_avg,
            response_length_std=response_length_std,
            financial_terms_density=avg_scores['financial_terms_density'],
            risk_mentions_ratio=avg_scores['risk_mentions_ratio'],
            compliance_coverage=avg_scores['compliance_coverage'],
            inference_time_avg=avg_performance['inference_time'],
            tokens_per_second=avg_performance['tokens_per_second'],
            memory_usage_mb=avg_performance['memory_usage_mb']
        )
    
    def _compare_with_benchmark(self, metrics: ValidationMetrics) -> Dict[str, float]:
        """與基準分數比較"""
        comparison = {}
        
        for key, benchmark_value in self.benchmark_scores.items():
            current_value = getattr(metrics, key)
            improvement = current_value - benchmark_value
            comparison[key] = {
                'current': current_value,
                'benchmark': benchmark_value,
                'improvement': improvement,
                'improvement_percent': (improvement / benchmark_value * 100) if benchmark_value > 0 else 0
            }
        
        return comparison
    
    def _generate_validation_recommendations(
        self,
        metrics: ValidationMetrics,
        detailed_scores: List[Dict[str, Any]]
    ) -> List[str]:
        """生成驗證建議"""
        recommendations = []
        
        # 基於分數的建議
        if metrics.accuracy_score < 0.7:
            recommendations.append("準確性需要改進：建議增加更多高品質訓練數據，特別是金融專業內容")
        
        if metrics.risk_awareness_score < 0.6:
            recommendations.append("風險意識不足：需要強化風險提示和警告的訓練")
        
        if metrics.compliance_score < 0.8:
            recommendations.append("合規性需要提升：確保輸出包含適當的免責聲明")
        
        if metrics.fluency_score < 0.7:
            recommendations.append("語言流暢度有待改善：建議改進語言模型的表達能力")
        
        if metrics.financial_accuracy < 0.7:
            recommendations.append("金融專業準確性不足：需要更多領域專業知識訓練")
        
        # 基於性能的建議
        if metrics.inference_time_avg > 2.0:
            recommendations.append("推理速度較慢：考慮模型優化或硬體升級")
        
        if metrics.tokens_per_second < 10:
            recommendations.append("生成效率偏低：建議檢查模型配置和硬體性能")
        
        # 基於統計的建議
        if metrics.response_length_avg < 50:
            recommendations.append("回應過於簡短：訓練模型生成更詳細的回應")
        
        if metrics.financial_terms_density < 0.1:
            recommendations.append("金融術語使用不足：增加專業術語的使用訓練")
        
        return recommendations
    
    def generate_validation_report(
        self,
        result: ValidationResult,
        output_dir: str,
        include_plots: bool = True
    ):
        """生成驗證報告"""
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成JSON報告
        report_data = {
            'model_name': result.model_name,
            'validation_date': result.validation_date,
            'dataset_name': result.dataset_name,
            'sample_count': result.sample_count,
            'metrics': result.metrics.to_dict(),
            'benchmark_comparison': result.benchmark_comparison,
            'recommendations': result.recommendations,
            'validation_config': result.validation_config,
            'detailed_scores': result.detailed_scores[:3]  # 只保存前3個詳細結果
        }
        
        with open(output_dir / "validation_report.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        # 生成圖表
        if include_plots:
            self._generate_validation_plots(result, output_dir)
        
        # 生成Markdown報告
        self._generate_validation_markdown_report(result, output_dir)
        
        logger.info(f"驗證報告已生成: {output_dir}")
    
    def _generate_validation_plots(self, result: ValidationResult, output_dir: Path):
        """生成驗證圖表"""
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 核心指標雷達圖
        fig, ax = plt.subplots(figsize=(10, 8), subplot_kw=dict(projection='polar'))
        
        metrics_names = ['準確性', '相關性', '風險意識', '可操作性', '合規性']
        metrics_values = [
            result.metrics.accuracy_score,
            result.metrics.relevance_score,
            result.metrics.risk_awareness_score,
            result.metrics.actionability_score,
            result.metrics.compliance_score
        ]
        
        angles = np.linspace(0, 2 * np.pi, len(metrics_names), endpoint=False)
        metrics_values += metrics_values[:1]
        angles = np.concatenate((angles, [angles[0]]))
        
        ax.plot(angles, metrics_values, 'o-', linewidth=2, label='當前模型')
        ax.fill(angles, metrics_values, alpha=0.25)
        
        # 添加基準線
        benchmark_values = [
            self.benchmark_scores['accuracy_score'],
            self.benchmark_scores['relevance_score'],
            self.benchmark_scores['risk_awareness_score'],
            self.benchmark_scores['actionability_score'],
            self.benchmark_scores['compliance_score']
        ]
        benchmark_values += benchmark_values[:1]
        
        ax.plot(angles, benchmark_values, '--', linewidth=2, label='基準線', alpha=0.7)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics_names)
        ax.set_ylim(0, 1)
        ax.set_title(f'{result.model_name} 驗證結果', size=16, pad=20)
        ax.legend()
        
        plt.savefig(output_dir / "validation_radar.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 詳細指標對比圖
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 語言品質指標
        language_metrics = ['流暢度', '連貫性', '信息量']
        language_scores = [
            result.metrics.fluency_score,
            result.metrics.coherence_score,
            result.metrics.informativeness_score
        ]
        
        axes[0, 0].bar(language_metrics, language_scores, color='skyblue', alpha=0.7)
        axes[0, 0].set_title('語言品質指標')
        axes[0, 0].set_ylim(0, 1)
        
        # 金融專業指標
        financial_metrics = ['金融準確性', '風險評估', '投資邏輯']
        financial_scores = [
            result.metrics.financial_accuracy,
            result.metrics.risk_assessment_quality,
            result.metrics.investment_logic_score
        ]
        
        axes[0, 1].bar(financial_metrics, financial_scores, color='lightgreen', alpha=0.7)
        axes[0, 1].set_title('金融專業指標')
        axes[0, 1].set_ylim(0, 1)
        
        # 性能指標
        performance_metrics = ['推理時間(秒)', 'Token/秒', '記憶體使用(MB)']
        performance_values = [
            result.metrics.inference_time_avg,
            result.metrics.tokens_per_second,
            result.metrics.memory_usage_mb / 100  # 縮放以便顯示
        ]
        
        axes[1, 0].bar(performance_metrics, performance_values, color='orange', alpha=0.7)
        axes[1, 0].set_title('性能指標')
        
        # 統計指標
        stats_metrics = ['平均長度', '金融術語密度', '風險提及比例', '合規覆蓋率']
        stats_values = [
            result.metrics.response_length_avg / 100,  # 縮放
            result.metrics.financial_terms_density,
            result.metrics.risk_mentions_ratio,
            result.metrics.compliance_coverage
        ]
        
        axes[1, 1].bar(stats_metrics, stats_values, color='purple', alpha=0.7)
        axes[1, 1].set_title('統計指標')
        
        plt.tight_layout()
        plt.savefig(output_dir / "detailed_metrics.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_validation_markdown_report(self, result: ValidationResult, output_dir: Path):
        """生成Markdown驗證報告"""
        
        markdown_content = f"""# 模型驗證報告

## 基本信息
- **模型名稱**: {result.model_name}
- **驗證日期**: {result.validation_date}
- **驗證數據集**: {result.dataset_name}
- **樣本數量**: {result.sample_count}

## 核心指標

| 指標 | 分數 | 基準 | 改善 | 改善率 |
|------|------|------|------|--------|
| 準確性 | {result.metrics.accuracy_score:.3f} | {self.benchmark_scores['accuracy_score']:.3f} | {result.benchmark_comparison['accuracy_score']['improvement']:+.3f} | {result.benchmark_comparison['accuracy_score']['improvement_percent']:+.1f}% |
| 相關性 | {result.metrics.relevance_score:.3f} | {self.benchmark_scores['relevance_score']:.3f} | {result.benchmark_comparison['relevance_score']['improvement']:+.3f} | {result.benchmark_comparison['relevance_score']['improvement_percent']:+.1f}% |
| 風險意識 | {result.metrics.risk_awareness_score:.3f} | {self.benchmark_scores['risk_awareness_score']:.3f} | {result.benchmark_comparison['risk_awareness_score']['improvement']:+.3f} | {result.benchmark_comparison['risk_awareness_score']['improvement_percent']:+.1f}% |
| 可操作性 | {result.metrics.actionability_score:.3f} | {self.benchmark_scores['actionability_score']:.3f} | {result.benchmark_comparison['actionability_score']['improvement']:+.3f} | {result.benchmark_comparison['actionability_score']['improvement_percent']:+.1f}% |
| 合規性 | {result.metrics.compliance_score:.3f} | {self.benchmark_scores['compliance_score']:.3f} | {result.benchmark_comparison['compliance_score']['improvement']:+.3f} | {result.benchmark_comparison['compliance_score']['improvement_percent']:+.1f}% |
| **總體分數** | **{result.metrics.overall_score:.3f}** | **{self.benchmark_scores['overall_score']:.3f}** | **{result.benchmark_comparison['overall_score']['improvement']:+.3f}** | **{result.benchmark_comparison['overall_score']['improvement_percent']:+.1f}%** |

## 詳細指標

### 語言品質
- **流暢度**: {result.metrics.fluency_score:.3f}
- **連貫性**: {result.metrics.coherence_score:.3f}
- **信息量**: {result.metrics.informativeness_score:.3f}

### 金融專業
- **金融準確性**: {result.metrics.financial_accuracy:.3f}
- **風險評估品質**: {result.metrics.risk_assessment_quality:.3f}
- **投資邏輯**: {result.metrics.investment_logic_score:.3f}

### 性能指標
- **平均推理時間**: {result.metrics.inference_time_avg:.2f} 秒
- **生成速度**: {result.metrics.tokens_per_second:.1f} tokens/秒
- **記憶體使用**: {result.metrics.memory_usage_mb:.1f} MB

### 統計指標
- **平均回應長度**: {result.metrics.response_length_avg:.0f} 字符 (±{result.metrics.response_length_std:.0f})
- **金融術語密度**: {result.metrics.financial_terms_density:.3f}
- **風險提及比例**: {result.metrics.risk_mentions_ratio:.3f}
- **合規覆蓋率**: {result.metrics.compliance_coverage:.3f}

## 改進建議

"""
        
        for i, recommendation in enumerate(result.recommendations, 1):
            markdown_content += f"{i}. {recommendation}\n"
        
        markdown_content += f"""
## 驗證樣本示例

以下是前2個驗證樣本的詳細結果：

"""
        
        for i, sample in enumerate(result.detailed_scores[:2], 1):
            markdown_content += f"""
### 樣本 {i}

**查詢**: {sample['query']}

**期望回應**: {sample['expected_response'][:100]}...

**生成回應**: {sample['generated_response'][:100]}...

**評分**:
- 準確性: {sample['scores']['accuracy_score']:.2f}
- 相關性: {sample['scores']['relevance_score']:.2f}
- 風險意識: {sample['scores']['risk_awareness_score']:.2f}
- 可操作性: {sample['scores']['actionability_score']:.2f}
- 合規性: {sample['scores']['compliance_score']:.2f}

**性能**:
- 推理時間: {sample['performance']['inference_time']:.2f}秒
- 生成速度: {sample['performance']['tokens_per_second']:.1f} tokens/秒

---
"""
        
        with open(output_dir / "validation_report.md", 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def get_validation_history(self) -> List[ValidationResult]:
        """獲取驗證歷史"""
        return self.validation_history.copy()
    
    def compare_validation_results(
        self,
        results: List[ValidationResult]
    ) -> Dict[str, Any]:
        """比較多個驗證結果"""
        
        if len(results) < 2:
            raise ValueError("需要至少2個驗證結果進行比較")
        
        comparison = {
            'models': [r.model_name for r in results],
            'metrics_comparison': {},
            'best_model': {},
            'performance_trends': {}
        }
        
        # 比較核心指標
        core_metrics = ['accuracy_score', 'relevance_score', 'risk_awareness_score',
                       'actionability_score', 'compliance_score', 'overall_score']
        
        for metric in core_metrics:
            scores = [getattr(r.metrics, metric) for r in results]
            best_idx = np.argmax(scores)
            
            comparison['metrics_comparison'][metric] = {
                'scores': scores,
                'best_model': results[best_idx].model_name,
                'best_score': scores[best_idx],
                'improvement_range': max(scores) - min(scores)
            }
        
        # 確定最佳模型
        overall_scores = [r.metrics.overall_score for r in results]
        best_overall_idx = np.argmax(overall_scores)
        
        comparison['best_model'] = {
            'name': results[best_overall_idx].model_name,
            'overall_score': overall_scores[best_overall_idx],
            'validation_date': results[best_overall_idx].validation_date
        }
        
        return comparison


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

