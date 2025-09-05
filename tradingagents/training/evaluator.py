"""
Model Evaluator
模型評估器

提供：
- 金融分析準確性評估
- 投資建議品質評估
- 風險評估準確性評估
- 自動化評估流程
- 評估報告生成
"""

import os
import json
import logging
import numpy as np
import torch
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import AutoTokenizer, AutoModelForCausalLM
from .reward_models import FinancialRewardModel, create_reward_model

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """評估指標結構"""
    accuracy_score: float = 0.0
    relevance_score: float = 0.0
    risk_awareness_score: float = 0.0
    actionability_score: float = 0.0
    compliance_score: float = 0.0
    overall_score: float = 0.0
    
    # 額外指標
    response_length_avg: float = 0.0
    response_time_avg: float = 0.0
    financial_terms_usage: float = 0.0
    risk_mentions: int = 0
    compliance_mentions: int = 0


@dataclass
class EvaluationResult:
    """評估結果結構"""
    model_name: str
    evaluation_date: str
    test_samples: int
    metrics: EvaluationMetrics
    detailed_scores: List[Dict[str, Any]]
    recommendations: List[str]
    comparison_baseline: Optional[Dict[str, float]] = None


class ModelEvaluator:
    """
    模型評估器
    
    提供全面的金融AI模型評估功能
    """
    
    def __init__(
        self,
        reward_model: Optional[FinancialRewardModel] = None,
        baseline_scores: Optional[Dict[str, float]] = None
    ):
        self.reward_model = reward_model or create_reward_model("financial")
        self.baseline_scores = baseline_scores or self._get_default_baseline()
        
        # 評估歷史
        self.evaluation_history = []
        
    def _get_default_baseline(self) -> Dict[str, float]:
        """獲取默認基準分數"""
        return {
            'accuracy_score': 0.6,
            'relevance_score': 0.7,
            'risk_awareness_score': 0.5,
            'actionability_score': 0.6,
            'compliance_score': 0.8,
            'overall_score': 0.64
        }
    
    def evaluate_model(
        self,
        model,
        tokenizer,
        test_queries: List[str],
        test_responses: List[str],
        test_contexts: Optional[List[Dict[str, Any]]] = None,
        model_name: str = "unknown_model"
    ) -> EvaluationResult:
        """
        評估模型性能
        
        Args:
            model: 要評估的模型
            tokenizer: 對應的tokenizer
            test_queries: 測試查詢列表
            test_responses: 預期回應列表（用於比較）
            test_contexts: 測試上下文列表
            model_name: 模型名稱
            
        Returns:
            評估結果
        """
        logger.info(f"Starting evaluation for model: {model_name}")
        
        # 生成模型回應
        generated_responses = self._generate_responses(
            model, tokenizer, test_queries
        )
        
        # 計算詳細評分
        detailed_scores = []
        all_metrics = []
        
        for i, (query, expected, generated) in enumerate(zip(test_queries, test_responses, generated_responses)):
            context = test_contexts[i] if test_contexts else {}
            
            # 使用獎勵模型評估
            reward_components = self.reward_model._compute_reward_components(
                query, generated, context
            )
            
            # 計算與預期回應的相似度
            similarity_score = self._compute_response_similarity(expected, generated)
            
            score_detail = {
                'query': query,
                'expected_response': expected,
                'generated_response': generated,
                'context': context,
                'accuracy_score': reward_components.accuracy_score,
                'relevance_score': reward_components.relevance_score,
                'risk_awareness_score': reward_components.risk_awareness_score,
                'actionability_score': reward_components.actionability_score,
                'compliance_score': reward_components.compliance_score,
                'similarity_score': similarity_score,
                'response_length': len(generated),
                'financial_terms_count': self._count_financial_terms(generated),
                'risk_mentions': self._count_risk_mentions(generated),
                'compliance_mentions': self._count_compliance_mentions(generated)
            }
            
            detailed_scores.append(score_detail)
            all_metrics.append(reward_components)
        
        # 計算平均指標
        avg_metrics = self._compute_average_metrics(all_metrics, detailed_scores)
        
        # 生成建議
        recommendations = self._generate_recommendations(avg_metrics, detailed_scores)
        
        # 創建評估結果
        result = EvaluationResult(
            model_name=model_name,
            evaluation_date=datetime.now().isoformat(),
            test_samples=len(test_queries),
            metrics=avg_metrics,
            detailed_scores=detailed_scores,
            recommendations=recommendations,
            comparison_baseline=self.baseline_scores
        )
        
        # 添加到歷史記錄
        self.evaluation_history.append(result)
        
        logger.info(f"Evaluation completed. Overall score: {avg_metrics.overall_score:.3f}")
        
        return result
    
    def _generate_responses(
        self,
        model,
        tokenizer,
        queries: List[str],
        max_length: int = 512,
        temperature: float = 0.7
    ) -> List[str]:
        """生成模型回應"""
        model.eval()
        responses = []
        
        with torch.no_grad():
            for query in queries:
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
                outputs = model.generate(
                    **inputs,
                    max_length=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    num_return_sequences=1
                )
                
                # 解碼回應
                response = tokenizer.decode(
                    outputs[0][inputs['input_ids'].shape[1]:],
                    skip_special_tokens=True
                ).strip()
                
                responses.append(response)
        
        return responses
    
    def _compute_response_similarity(self, expected: str, generated: str) -> float:
        """計算回應相似度（簡化版）"""
        # 簡單的詞彙重疊相似度
        expected_words = set(expected.lower().split())
        generated_words = set(generated.lower().split())
        
        if not expected_words and not generated_words:
            return 1.0
        
        intersection = expected_words.intersection(generated_words)
        union = expected_words.union(generated_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _count_financial_terms(self, text: str) -> int:
        """計算金融術語使用數量"""
        financial_terms = [
            '投資', '股票', '基金', '債券', '風險', '報酬', '獲利', '虧損',
            '市場', '經濟', '金融', '銀行', '保險', '證券', '期貨', '選擇權',
            '本益比', '股息', '殖利率', '現金流', '資產', '負債', '營收', '淨利'
        ]
        
        return sum(1 for term in financial_terms if term in text)
    
    def _count_risk_mentions(self, text: str) -> int:
        """計算風險提及次數"""
        risk_terms = ['風險', '不確定', '波動', '謹慎', '小心', '注意']
        return sum(1 for term in risk_terms if term in text)
    
    def _count_compliance_mentions(self, text: str) -> int:
        """計算合規提及次數"""
        compliance_terms = ['僅供參考', '投資有風險', '請謹慎', '非投資建議', '專業諮詢']
        return sum(1 for term in compliance_terms if term in text)
    
    def _compute_average_metrics(
        self,
        all_metrics: List,
        detailed_scores: List[Dict[str, Any]]
    ) -> EvaluationMetrics:
        """計算平均指標"""
        
        # 計算各項平均分數
        accuracy_scores = [m.accuracy_score for m in all_metrics]
        relevance_scores = [m.relevance_score for m in all_metrics]
        risk_awareness_scores = [m.risk_awareness_score for m in all_metrics]
        actionability_scores = [m.actionability_score for m in all_metrics]
        compliance_scores = [m.compliance_score for m in all_metrics]
        
        # 計算額外指標
        response_lengths = [s['response_length'] for s in detailed_scores]
        financial_terms_counts = [s['financial_terms_count'] for s in detailed_scores]
        risk_mentions_total = sum(s['risk_mentions'] for s in detailed_scores)
        compliance_mentions_total = sum(s['compliance_mentions'] for s in detailed_scores)
        
        # 計算總體分數
        overall_score = np.mean([
            np.mean(accuracy_scores),
            np.mean(relevance_scores),
            np.mean(risk_awareness_scores),
            np.mean(actionability_scores),
            np.mean(compliance_scores)
        ])
        
        return EvaluationMetrics(
            accuracy_score=np.mean(accuracy_scores),
            relevance_score=np.mean(relevance_scores),
            risk_awareness_score=np.mean(risk_awareness_scores),
            actionability_score=np.mean(actionability_scores),
            compliance_score=np.mean(compliance_scores),
            overall_score=overall_score,
            response_length_avg=np.mean(response_lengths),
            financial_terms_usage=np.mean(financial_terms_counts),
            risk_mentions=risk_mentions_total,
            compliance_mentions=compliance_mentions_total
        )
    
    def _generate_recommendations(
        self,
        metrics: EvaluationMetrics,
        detailed_scores: List[Dict[str, Any]]
    ) -> List[str]:
        """生成改進建議"""
        recommendations = []
        
        # 基於分數的建議
        if metrics.accuracy_score < 0.7:
            recommendations.append("準確性需要改進：考慮增加更多高品質的訓練數據，或調整訓練參數")
        
        if metrics.relevance_score < 0.7:
            recommendations.append("相關性需要提升：檢查訓練數據的查詢-回應匹配品質")
        
        if metrics.risk_awareness_score < 0.6:
            recommendations.append("風險意識不足：增加風險相關的訓練範例，強化風險提示")
        
        if metrics.actionability_score < 0.6:
            recommendations.append("可操作性有待加強：訓練模型提供更具體、可行的建議")
        
        if metrics.compliance_score < 0.8:
            recommendations.append("合規性需要改善：確保模型輸出包含適當的免責聲明和風險警告")
        
        # 基於統計的建議
        if metrics.response_length_avg < 50:
            recommendations.append("回應過於簡短：考慮訓練模型生成更詳細的回應")
        
        if metrics.response_length_avg > 500:
            recommendations.append("回應過於冗長：考慮訓練模型生成更簡潔的回應")
        
        if metrics.financial_terms_usage < 2:
            recommendations.append("金融術語使用不足：增加專業術語的使用訓練")
        
        if metrics.risk_mentions < len(detailed_scores) * 0.3:
            recommendations.append("風險提及頻率偏低：加強風險意識的訓練")
        
        # 與基準比較的建議
        if metrics.overall_score < self.baseline_scores['overall_score']:
            recommendations.append(f"整體表現低於基準({self.baseline_scores['overall_score']:.2f})：需要全面檢視訓練策略")
        
        return recommendations
    
    def compare_models(
        self,
        results: List[EvaluationResult]
    ) -> Dict[str, Any]:
        """比較多個模型的評估結果"""
        
        if len(results) < 2:
            raise ValueError("Need at least 2 evaluation results for comparison")
        
        comparison = {
            'models': [r.model_name for r in results],
            'metrics_comparison': {},
            'best_model': {},
            'recommendations': []
        }
        
        # 比較各項指標
        metrics_names = [
            'accuracy_score', 'relevance_score', 'risk_awareness_score',
            'actionability_score', 'compliance_score', 'overall_score'
        ]
        
        for metric in metrics_names:
            scores = [getattr(r.metrics, metric) for r in results]
            best_idx = np.argmax(scores)
            
            comparison['metrics_comparison'][metric] = {
                'scores': scores,
                'best_model': results[best_idx].model_name,
                'best_score': scores[best_idx],
                'score_range': max(scores) - min(scores)
            }
        
        # 確定最佳模型
        overall_scores = [r.metrics.overall_score for r in results]
        best_overall_idx = np.argmax(overall_scores)
        
        comparison['best_model'] = {
            'name': results[best_overall_idx].model_name,
            'overall_score': overall_scores[best_overall_idx],
            'advantages': []
        }
        
        # 分析最佳模型的優勢
        best_result = results[best_overall_idx]
        for metric in metrics_names:
            if getattr(best_result.metrics, metric) == comparison['metrics_comparison'][metric]['best_score']:
                comparison['best_model']['advantages'].append(metric)
        
        return comparison
    
    def generate_evaluation_report(
        self,
        result: EvaluationResult,
        output_path: str,
        include_plots: bool = True
    ):
        """生成評估報告"""
        
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成JSON報告
        report_data = {
            'model_name': result.model_name,
            'evaluation_date': result.evaluation_date,
            'test_samples': result.test_samples,
            'metrics': {
                'accuracy_score': result.metrics.accuracy_score,
                'relevance_score': result.metrics.relevance_score,
                'risk_awareness_score': result.metrics.risk_awareness_score,
                'actionability_score': result.metrics.actionability_score,
                'compliance_score': result.metrics.compliance_score,
                'overall_score': result.metrics.overall_score,
                'response_length_avg': result.metrics.response_length_avg,
                'financial_terms_usage': result.metrics.financial_terms_usage,
                'risk_mentions': result.metrics.risk_mentions,
                'compliance_mentions': result.metrics.compliance_mentions
            },
            'baseline_comparison': {},
            'recommendations': result.recommendations,
            'sample_evaluations': result.detailed_scores[:5]  # 前5個樣本
        }
        
        # 與基準比較
        if result.comparison_baseline:
            for key, baseline_value in result.comparison_baseline.items():
                current_value = getattr(result.metrics, key, 0)
                report_data['baseline_comparison'][key] = {
                    'current': current_value,
                    'baseline': baseline_value,
                    'improvement': current_value - baseline_value,
                    'improvement_percent': ((current_value - baseline_value) / baseline_value * 100) if baseline_value > 0 else 0
                }
        
        # 保存JSON報告
        with open(output_path / "evaluation_report.json", 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        # 生成圖表
        if include_plots:
            self._generate_evaluation_plots(result, output_path)
        
        # 生成Markdown報告
        self._generate_markdown_report(result, report_data, output_path)
        
        logger.info(f"Evaluation report generated in {output_path}")
    
    def _generate_evaluation_plots(self, result: EvaluationResult, output_path: Path):
        """生成評估圖表"""
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 指標雷達圖
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
        metrics_values += metrics_values[:1]  # 閉合圖形
        angles = np.concatenate((angles, [angles[0]]))
        
        ax.plot(angles, metrics_values, 'o-', linewidth=2, label=result.model_name)
        ax.fill(angles, metrics_values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metrics_names)
        ax.set_ylim(0, 1)
        ax.set_title(f'{result.model_name} 評估指標', size=16, pad=20)
        ax.legend()
        
        plt.savefig(output_path / "metrics_radar.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 分數分佈直方圖
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        score_types = ['accuracy_score', 'relevance_score', 'risk_awareness_score', 
                      'actionability_score', 'compliance_score', 'similarity_score']
        score_names = ['準確性', '相關性', '風險意識', '可操作性', '合規性', '相似度']
        
        for i, (score_type, score_name) in enumerate(zip(score_types, score_names)):
            scores = [s[score_type] for s in result.detailed_scores]
            axes[i].hist(scores, bins=20, alpha=0.7, edgecolor='black')
            axes[i].set_title(f'{score_name}分數分佈')
            axes[i].set_xlabel('分數')
            axes[i].set_ylabel('頻次')
            axes[i].axvline(np.mean(scores), color='red', linestyle='--', label=f'平均: {np.mean(scores):.2f}')
            axes[i].legend()
        
        plt.tight_layout()
        plt.savefig(output_path / "score_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def _generate_markdown_report(self, result: EvaluationResult, report_data: Dict, output_path: Path):
        """生成Markdown報告"""
        
        markdown_content = f"""# 模型評估報告

## 基本信息
- **模型名稱**: {result.model_name}
- **評估日期**: {result.evaluation_date}
- **測試樣本數**: {result.test_samples}

## 評估指標

### 核心指標
| 指標 | 分數 | 基準 | 改善 |
|------|------|------|------|
"""
        
        # 添加指標表格
        metrics_map = {
            'accuracy_score': '準確性',
            'relevance_score': '相關性', 
            'risk_awareness_score': '風險意識',
            'actionability_score': '可操作性',
            'compliance_score': '合規性',
            'overall_score': '總體分數'
        }
        
        for key, name in metrics_map.items():
            current = getattr(result.metrics, key)
            baseline = result.comparison_baseline.get(key, 0) if result.comparison_baseline else 0
            improvement = current - baseline if baseline > 0 else 0
            
            markdown_content += f"| {name} | {current:.3f} | {baseline:.3f} | {improvement:+.3f} |\n"
        
        markdown_content += f"""
### 額外統計
- **平均回應長度**: {result.metrics.response_length_avg:.1f} 字符
- **金融術語使用**: 平均 {result.metrics.financial_terms_usage:.1f} 個/回應
- **風險提及次數**: {result.metrics.risk_mentions} 次
- **合規提及次數**: {result.metrics.compliance_mentions} 次

## 改進建議

"""
        
        for i, recommendation in enumerate(result.recommendations, 1):
            markdown_content += f"{i}. {recommendation}\n"
        
        markdown_content += """
## 樣本評估示例

以下是前3個測試樣本的詳細評估：

"""
        
        for i, sample in enumerate(result.detailed_scores[:3], 1):
            markdown_content += f"""
### 樣本 {i}

**查詢**: {sample['query']}

**生成回應**: {sample['generated_response']}

**評分**:
- 準確性: {sample['accuracy_score']:.2f}
- 相關性: {sample['relevance_score']:.2f}
- 風險意識: {sample['risk_awareness_score']:.2f}
- 可操作性: {sample['actionability_score']:.2f}
- 合規性: {sample['compliance_score']:.2f}

---
"""
        
        # 保存Markdown報告
        with open(output_path / "evaluation_report.md", 'w', encoding='utf-8') as f:
            f.write(markdown_content)
    
    def get_evaluation_history(self) -> List[EvaluationResult]:
        """獲取評估歷史"""
        return self.evaluation_history.copy()
    
    def save_evaluation_history(self, output_path: str):
        """保存評估歷史"""
        history_data = []
        
        for result in self.evaluation_history:
            history_data.append({
                'model_name': result.model_name,
                'evaluation_date': result.evaluation_date,
                'test_samples': result.test_samples,
                'overall_score': result.metrics.overall_score,
                'metrics': {
                    'accuracy_score': result.metrics.accuracy_score,
                    'relevance_score': result.metrics.relevance_score,
                    'risk_awareness_score': result.metrics.risk_awareness_score,
                    'actionability_score': result.metrics.actionability_score,
                    'compliance_score': result.metrics.compliance_score
                }
            })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Evaluation history saved to {output_path}")