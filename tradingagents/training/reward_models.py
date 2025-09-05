"""
Reward Models for Financial Trading Agent Training
金融交易代理訓練的獎勵模型

包含：
- FinancialRewardModel: 基礎金融獎勵模型
- TradingRewardModel: 交易專用獎勵模型
- RiskAdjustedRewardModel: 風險調整獎勵模型
- MultiFactorRewardModel: 多因子獎勵模型
"""

import re
import json
import logging
import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class RewardComponents:
    """獎勵組件結構"""
    accuracy_score: float = 0.0
    relevance_score: float = 0.0
    risk_awareness_score: float = 0.0
    actionability_score: float = 0.0
    compliance_score: float = 0.0
    total_score: float = 0.0


class BaseRewardModel(ABC):
    """獎勵模型基類"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.weights = self._get_default_weights()
        
    @abstractmethod
    def compute_rewards(
        self, 
        queries: List[str], 
        responses: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> torch.Tensor:
        """計算獎勵分數"""
        pass
    
    @abstractmethod
    def _get_default_weights(self) -> Dict[str, float]:
        """獲取默認權重"""
        pass


class FinancialRewardModel(BaseRewardModel):
    """
    金融分析獎勵模型
    
    評估標準：
    1. 準確性 (Accuracy): 分析的準確性和邏輯性
    2. 相關性 (Relevance): 回應與查詢的相關程度
    3. 風險意識 (Risk Awareness): 風險提示和警告
    4. 可操作性 (Actionability): 提供具體可行的建議
    5. 合規性 (Compliance): 符合金融法規要求
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 金融關鍵詞字典
        self.financial_keywords = {
            'positive': [
                '成長', '獲利', '營收', '股息', '投資價值', '買進', '看好',
                '上漲', '突破', '強勢', '績優', '潛力', '機會'
            ],
            'negative': [
                '風險', '下跌', '虧損', '賣出', '避免', '謹慎', '警告',
                '危險', '不確定', '波動', '衰退', '困難'
            ],
            'neutral': [
                '持有', '觀察', '等待', '分析', '評估', '考慮', '建議',
                '可能', '預期', '估計', '預測'
            ],
            'risk_terms': [
                '風險', '不確定性', '波動', '損失', '謹慎', '小心',
                '風險控制', '停損', '分散投資', '風險管理'
            ],
            'compliance_terms': [
                '僅供參考', '投資有風險', '請謹慎評估', '非投資建議',
                '自行判斷', '風險自負', '專業諮詢'
            ]
        }
        
        # 數值模式
        self.number_patterns = {
            'percentage': r'(\d+(?:\.\d+)?)\s*%',
            'price': r'(\d+(?:\.\d+)?)\s*元',
            'ratio': r'(\d+(?:\.\d+)?)\s*倍',
            'target_price': r'目標價.*?(\d+(?:\.\d+)?)'
        }
        
    def _get_default_weights(self) -> Dict[str, float]:
        """獲取默認權重配置"""
        return {
            'accuracy': 0.25,      # 準確性權重
            'relevance': 0.20,     # 相關性權重
            'risk_awareness': 0.20, # 風險意識權重
            'actionability': 0.20,  # 可操作性權重
            'compliance': 0.15     # 合規性權重
        }
    
    def compute_rewards(
        self, 
        queries: List[str], 
        responses: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> torch.Tensor:
        """
        計算金融分析獎勵分數
        
        Args:
            queries: 查詢列表
            responses: 回應列表
            contexts: 上下文信息列表
            
        Returns:
            獎勵分數張量
        """
        rewards = []
        
        for i, (query, response) in enumerate(zip(queries, responses)):
            context = contexts[i] if contexts else {}
            
            # 計算各個組件分數
            components = self._compute_reward_components(query, response, context)
            
            # 加權總分
            total_reward = (
                self.weights['accuracy'] * components.accuracy_score +
                self.weights['relevance'] * components.relevance_score +
                self.weights['risk_awareness'] * components.risk_awareness_score +
                self.weights['actionability'] * components.actionability_score +
                self.weights['compliance'] * components.compliance_score
            )
            
            rewards.append(total_reward)
        
        return torch.tensor(rewards, dtype=torch.float32)
    
    def _compute_reward_components(
        self, 
        query: str, 
        response: str, 
        context: Dict[str, Any]
    ) -> RewardComponents:
        """計算獎勵組件分數"""
        
        components = RewardComponents()
        
        # 1. 準確性評分
        components.accuracy_score = self._evaluate_accuracy(query, response, context)
        
        # 2. 相關性評分
        components.relevance_score = self._evaluate_relevance(query, response)
        
        # 3. 風險意識評分
        components.risk_awareness_score = self._evaluate_risk_awareness(response)
        
        # 4. 可操作性評分
        components.actionability_score = self._evaluate_actionability(response)
        
        # 5. 合規性評分
        components.compliance_score = self._evaluate_compliance(response)
        
        # 計算總分
        components.total_score = (
            self.weights['accuracy'] * components.accuracy_score +
            self.weights['relevance'] * components.relevance_score +
            self.weights['risk_awareness'] * components.risk_awareness_score +
            self.weights['actionability'] * components.actionability_score +
            self.weights['compliance'] * components.compliance_score
        )
        
        return components
    
    def _evaluate_accuracy(
        self, 
        query: str, 
        response: str, 
        context: Dict[str, Any]
    ) -> float:
        """
        評估回應的準確性
        
        考慮因素：
        - 數據引用的準確性
        - 邏輯推理的合理性
        - 專業術語的正確使用
        """
        score = 0.5  # 基礎分數
        
        # 檢查是否包含具體數據
        has_numbers = bool(re.search(r'\d+', response))
        if has_numbers:
            score += 0.2
        
        # 檢查專業術語使用
        financial_terms_count = sum(
            1 for term_list in self.financial_keywords.values()
            for term in term_list
            if term in response
        )
        
        if financial_terms_count >= 3:
            score += 0.2
        elif financial_terms_count >= 1:
            score += 0.1
        
        # 檢查邏輯結構
        logical_indicators = ['因為', '所以', '由於', '因此', '基於', '根據']
        has_logic = any(indicator in response for indicator in logical_indicators)
        if has_logic:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_relevance(self, query: str, response: str) -> float:
        """
        評估回應與查詢的相關性
        
        使用關鍵詞匹配和語義相似度
        """
        score = 0.3  # 基礎分數
        
        # 提取查詢中的關鍵詞
        query_keywords = self._extract_keywords(query)
        response_keywords = self._extract_keywords(response)
        
        # 計算關鍵詞重疊度
        if query_keywords and response_keywords:
            overlap = len(query_keywords.intersection(response_keywords))
            overlap_ratio = overlap / len(query_keywords)
            score += 0.4 * overlap_ratio
        
        # 檢查是否直接回答了問題
        question_indicators = ['什麼', '如何', '為什麼', '是否', '會不會', '?', '？']
        is_question = any(indicator in query for indicator in question_indicators)
        
        if is_question:
            # 檢查回應是否提供了答案
            answer_indicators = ['是', '不是', '會', '不會', '因為', '建議', '認為']
            has_answer = any(indicator in response for indicator in answer_indicators)
            if has_answer:
                score += 0.3
        
        return min(score, 1.0)
    
    def _evaluate_risk_awareness(self, response: str) -> float:
        """
        評估風險意識
        
        檢查是否提及風險、不確定性等
        """
        score = 0.0
        
        # 檢查風險相關詞彙
        risk_mentions = sum(
            1 for term in self.financial_keywords['risk_terms']
            if term in response
        )
        
        if risk_mentions >= 3:
            score += 0.5
        elif risk_mentions >= 1:
            score += 0.3
        
        # 檢查具體風險描述
        risk_descriptions = [
            '市場風險', '流動性風險', '信用風險', '操作風險',
            '政策風險', '匯率風險', '利率風險'
        ]
        
        specific_risks = sum(
            1 for risk in risk_descriptions
            if risk in response
        )
        
        if specific_risks >= 2:
            score += 0.3
        elif specific_risks >= 1:
            score += 0.2
        
        # 檢查風險管理建議
        risk_management = [
            '分散投資', '停損', '風險控制', '謹慎評估',
            '小額投資', '定期檢視'
        ]
        
        has_risk_management = any(term in response for term in risk_management)
        if has_risk_management:
            score += 0.2
        
        return min(score, 1.0)
    
    def _evaluate_actionability(self, response: str) -> float:
        """
        評估可操作性
        
        檢查是否提供具體可行的建議
        """
        score = 0.2  # 基礎分數
        
        # 檢查行動建議
        action_words = [
            '建議', '可以', '應該', '考慮', '買進', '賣出',
            '持有', '觀察', '等待', '增持', '減持'
        ]
        
        action_count = sum(1 for word in action_words if word in response)
        if action_count >= 3:
            score += 0.4
        elif action_count >= 1:
            score += 0.2
        
        # 檢查具體數值建議
        has_target_price = bool(re.search(self.number_patterns['target_price'], response))
        has_percentage = bool(re.search(self.number_patterns['percentage'], response))
        
        if has_target_price:
            score += 0.2
        if has_percentage:
            score += 0.1
        
        # 檢查時間框架
        time_frames = ['短期', '中期', '長期', '一週', '一個月', '一年']
        has_timeframe = any(frame in response for frame in time_frames)
        if has_timeframe:
            score += 0.1
        
        return min(score, 1.0)
    
    def _evaluate_compliance(self, response: str) -> float:
        """
        評估合規性
        
        檢查是否包含必要的免責聲明和風險提示
        """
        score = 0.3  # 基礎分數
        
        # 檢查免責聲明
        compliance_mentions = sum(
            1 for term in self.financial_keywords['compliance_terms']
            if term in response
        )
        
        if compliance_mentions >= 2:
            score += 0.4
        elif compliance_mentions >= 1:
            score += 0.2
        
        # 檢查是否避免絕對化表述
        absolute_terms = ['一定', '絕對', '肯定', '必然', '保證']
        has_absolute = any(term in response for term in absolute_terms)
        if has_absolute:
            score -= 0.2  # 扣分
        
        # 檢查是否提醒專業諮詢
        professional_advice = ['專業諮詢', '財務顧問', '投資顧問', '專業意見']
        mentions_professional = any(term in response for term in professional_advice)
        if mentions_professional:
            score += 0.3
        
        return max(min(score, 1.0), 0.0)
    
    def _extract_keywords(self, text: str) -> set:
        """提取文本關鍵詞"""
        # 簡單的關鍵詞提取（可以用更複雜的NLP方法）
        keywords = set()
        
        # 提取所有金融關鍵詞
        for term_list in self.financial_keywords.values():
            for term in term_list:
                if term in text:
                    keywords.add(term)
        
        # 提取股票代碼
        stock_codes = re.findall(r'\b\d{4}\b', text)
        keywords.update(stock_codes)
        
        # 提取公司名稱（簡化版）
        company_patterns = [r'台積電', r'鴻海', r'聯發科', r'台塑', r'中華電']
        for pattern in company_patterns:
            if re.search(pattern, text):
                keywords.add(pattern)
        
        return keywords


class TradingRewardModel(FinancialRewardModel):
    """
    交易專用獎勵模型
    
    專注於交易決策的評估：
    - 進出場時機
    - 風險報酬比
    - 交易策略合理性
    """
    
    def _get_default_weights(self) -> Dict[str, float]:
        """交易專用權重配置"""
        return {
            'accuracy': 0.30,      # 提高準確性權重
            'relevance': 0.15,     # 降低相關性權重
            'risk_awareness': 0.25, # 提高風險意識權重
            'actionability': 0.25,  # 提高可操作性權重
            'compliance': 0.05     # 降低合規性權重（交易場景）
        }
    
    def _evaluate_actionability(self, response: str) -> float:
        """
        交易專用可操作性評估
        
        重點評估交易決策的具體性
        """
        score = super()._evaluate_actionability(response)
        
        # 交易專用加分項
        trading_actions = [
            '買進', '賣出', '加碼', '減碼', '停損', '停利',
            '進場', '出場', '建倉', '平倉'
        ]
        
        trading_action_count = sum(1 for action in trading_actions if action in response)
        if trading_action_count >= 2:
            score += 0.2
        elif trading_action_count >= 1:
            score += 0.1
        
        # 檢查具體價位
        price_levels = re.findall(r'(\d+(?:\.\d+)?)\s*元', response)
        if len(price_levels) >= 2:  # 至少兩個價位（如進場和停損）
            score += 0.15
        elif len(price_levels) >= 1:
            score += 0.1
        
        return min(score, 1.0)


class RiskAdjustedRewardModel(FinancialRewardModel):
    """
    風險調整獎勵模型
    
    特別強調風險管理和風險調整後的收益評估
    """
    
    def _get_default_weights(self) -> Dict[str, float]:
        """風險調整權重配置"""
        return {
            'accuracy': 0.20,
            'relevance': 0.15,
            'risk_awareness': 0.40,  # 大幅提高風險意識權重
            'actionability': 0.15,
            'compliance': 0.10
        }
    
    def _evaluate_risk_awareness(self, response: str) -> float:
        """
        增強版風險意識評估
        
        更詳細的風險評估標準
        """
        score = super()._evaluate_risk_awareness(response)
        
        # 風險量化評估
        risk_metrics = [
            '夏普比率', '最大回撤', '波動率', 'VaR', '貝塔值',
            '標準差', '風險調整報酬', '下行風險'
        ]
        
        risk_metric_count = sum(1 for metric in risk_metrics if metric in response)
        if risk_metric_count >= 2:
            score += 0.2
        elif risk_metric_count >= 1:
            score += 0.1
        
        # 情境分析
        scenario_terms = [
            '最好情況', '最壞情況', '基本情況', '壓力測試',
            '敏感性分析', '情境分析'
        ]
        
        has_scenario = any(term in response for term in scenario_terms)
        if has_scenario:
            score += 0.15
        
        return min(score, 1.0)


class MultiFactorRewardModel(FinancialRewardModel):
    """
    多因子獎勵模型
    
    整合多個評估維度，提供更全面的獎勵評估
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 子模型
        self.trading_model = TradingRewardModel(config)
        self.risk_model = RiskAdjustedRewardModel(config)
        
        # 模型權重
        self.model_weights = {
            'base': 0.4,
            'trading': 0.3,
            'risk': 0.3
        }
    
    def compute_rewards(
        self, 
        queries: List[str], 
        responses: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> torch.Tensor:
        """
        多因子獎勵計算
        
        結合基礎模型、交易模型和風險模型的評分
        """
        # 獲取各模型的獎勵
        base_rewards = super().compute_rewards(queries, responses, contexts)
        trading_rewards = self.trading_model.compute_rewards(queries, responses, contexts)
        risk_rewards = self.risk_model.compute_rewards(queries, responses, contexts)
        
        # 加權平均
        multi_factor_rewards = (
            self.model_weights['base'] * base_rewards +
            self.model_weights['trading'] * trading_rewards +
            self.model_weights['risk'] * risk_rewards
        )
        
        return multi_factor_rewards
    
    def get_detailed_rewards(
        self, 
        queries: List[str], 
        responses: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, torch.Tensor]:
        """
        獲取詳細的獎勵分解
        
        Returns:
            包含各模型獎勵的字典
        """
        return {
            'base_rewards': super().compute_rewards(queries, responses, contexts),
            'trading_rewards': self.trading_model.compute_rewards(queries, responses, contexts),
            'risk_rewards': self.risk_model.compute_rewards(queries, responses, contexts),
            'multi_factor_rewards': self.compute_rewards(queries, responses, contexts)
        }


# 工廠函數
def create_reward_model(model_type: str = "financial", config: Optional[Dict[str, Any]] = None) -> BaseRewardModel:
    """
    創建獎勵模型的工廠函數
    
    Args:
        model_type: 模型類型 ("financial", "trading", "risk_adjusted", "multi_factor")
        config: 配置參數
        
    Returns:
        對應的獎勵模型實例
    """
    model_map = {
        "financial": FinancialRewardModel,
        "trading": TradingRewardModel,
        "risk_adjusted": RiskAdjustedRewardModel,
        "multi_factor": MultiFactorRewardModel
    }
    
    if model_type not in model_map:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return model_map[model_type](config)