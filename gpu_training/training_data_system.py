#!/usr/bin/env python3
"""
訓練數據和範例系統 - Task 4.2實現
統一管理訓練數據集、範例生成、數據驗證和JSONL格式處理

This system provides:
- Unified training data management for SFT/LoRA/GRPO
- Financial example generation with domain expertise
- Data validation and quality assurance
- JSONL format standardization and conversion
- Dataset splitting and preprocessing utilities
- Integration with TradingAgents ecosystem

Author: TradingAgents Team (天工開物) - 支援AI訓練專家團隊
Version: 1.0.0
"""

import os
import sys
import json
import logging
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union, Generator
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import re
from concurrent.futures import ThreadPoolExecutor

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [訓練數據系統] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/training/training_data_system.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("TrainingDataSystem")


class DatasetType(Enum):
    """數據集類型枚舉"""
    SFT = "supervised_fine_tuning"      # 監督微調
    LORA = "lora_adaptation"           # LoRA適應
    GRPO = "grpo_reinforcement"        # GRPO強化學習
    CHAT = "chat_completion"           # 對話補全
    INSTRUCTION = "instruction_following"  # 指令跟隨


class DataFormat(Enum):
    """數據格式枚舉"""
    ALPACA = "alpaca"          # Alpaca格式
    SHAREGPT = "sharegpt"      # ShareGPT格式
    GRPO = "grpo"              # GRPO專用格式
    CUSTOM = "custom"          # 自定義格式


class DatasetSplit(Enum):
    """數據集分割類型"""
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


@dataclass
class DatasetConfig:
    """數據集配置"""
    name: str
    description: str
    dataset_type: DatasetType
    data_format: DataFormat
    total_samples: int = 0
    train_ratio: float = 0.8
    validation_ratio: float = 0.1
    test_ratio: float = 0.1
    min_length: int = 10
    max_length: int = 2048
    quality_threshold: float = 0.7
    enable_augmentation: bool = False
    augmentation_ratio: float = 0.2


@dataclass
class DataSample:
    """數據樣本定義"""
    sample_id: str
    dataset_type: DatasetType
    data_format: DataFormat
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    quality_score: float = 0.0
    created_at: str = ""
    validated: bool = False


@dataclass
class DatasetStats:
    """數據集統計信息"""
    total_samples: int
    train_samples: int
    validation_samples: int
    test_samples: int
    avg_input_length: float
    avg_output_length: float
    quality_distribution: Dict[str, int]
    token_count: int
    unique_topics: int


class FinancialExampleGenerator:
    """
    金融領域範例生成器
    專門生成高質量的金融AI訓練數據
    """
    
    def __init__(self):
        # 金融主題分類
        self.financial_topics = {
            "股票分析": [
                "技術分析", "基本面分析", "財報分析", "產業分析", 
                "投資策略", "風險評估", "價值投資", "成長股投資"
            ],
            "市場研究": [
                "市場趋勢", "經濟指標", "產業前景", "政策影響",
                "國際市場", "匯率分析", "商品期貨", "總體經濟"
            ],
            "投資理財": [
                "資產配置", "投資組合", "風險管理", "退休規劃",
                "保險規劃", "稅務規劃", "定期定額", "ETF投資"
            ],
            "交易策略": [
                "當沖策略", "波段操作", "長期投資", "選股方法",
                "買賣時機", "停損停利", "資金管理", "心理建設"
            ]
        }
        
        # 台股公司範例
        self.taiwan_companies = [
            "台積電(2330)", "鴻海(2317)", "聯發科(2454)", "台達電(2308)",
            "中華電(2412)", "富邦金(2881)", "國泰金(2882)", "台塑(1301)",
            "南亞(1303)", "中鋼(2002)", "統一(1216)", "永豐餘(1907)",
            "廣達(2382)", "和碩(4938)", "日月光(3711)", "聯電(2303)"
        ]
        
        # 金融術語庫
        self.financial_terms = {
            "基礎": ["本益比", "股價淨值比", "殖利率", "市值", "成交量", "週轉率"],
            "進階": ["EBITDA", "自由現金流", "ROE", "ROA", "毛利率", "負債比"],
            "技術": ["移動平均線", "相對強弱指標", "MACD", "布林通道", "KD指標", "威廉指標"],
            "市場": ["多頭", "空頭", "盤整", "突破", "回檔", "反彈", "整理"]
        }
        
    def generate_sft_samples(self, num_samples: int) -> List[Dict[str, Any]]:
        """生成SFT訓練樣本"""
        samples = []
        
        for i in range(num_samples):
            topic = random.choice(list(self.financial_topics.keys()))
            subtopic = random.choice(self.financial_topics[topic])
            company = random.choice(self.taiwan_companies)
            
            # 生成問題
            instruction = self._generate_instruction(topic, subtopic, company)
            
            # 生成回答
            output = self._generate_financial_answer(topic, subtopic, company, instruction)
            
            sample = {
                "instruction": instruction,
                "input": "",
                "output": output,
                "topic": topic,
                "subtopic": subtopic,
                "company": company
            }
            
            samples.append(sample)
            
        return samples
    
    def generate_grpo_samples(self, num_samples: int) -> List[Dict[str, Any]]:
        """生成GRPO訓練樣本"""
        samples = []
        
        for i in range(num_samples):
            topic = random.choice(list(self.financial_topics.keys()))
            subtopic = random.choice(self.financial_topics[topic])
            company = random.choice(self.taiwan_companies)
            
            query = self._generate_grpo_query(topic, subtopic, company)
            context = self._generate_context(topic, subtopic)
            reference = self._generate_reference_answer(topic, subtopic, company)
            
            sample = {
                "query": query,
                "context": context,
                "reference": reference,
                "topic": topic,
                "subtopic": subtopic
            }
            
            samples.append(sample)
            
        return samples
    
    def generate_chat_samples(self, num_samples: int) -> List[Dict[str, Any]]:
        """生成對話格式樣本"""
        samples = []
        
        for i in range(num_samples):
            conversation = self._generate_financial_conversation()
            
            sample = {
                "conversations": conversation,
                "topic": conversation[0].get("metadata", {}).get("topic", "general")
            }
            
            samples.append(sample)
            
        return samples
    
    def _generate_instruction(self, topic: str, subtopic: str, company: str) -> str:
        """生成指令"""
        templates = [
            f"請分析{company}的{subtopic}",
            f"如何評估{company}的{subtopic}？",
            f"從{subtopic}角度分析{company}的投資價值",
            f"請說明{company}在{subtopic}方面的表現",
            f"分析{company}的{subtopic}並給出投資建議",
        ]
        
        # 根據主題調整模板
        if topic == "市場研究":
            templates.extend([
                f"當前{subtopic}對{company}的影響如何？",
                f"請分析{subtopic}趨勢對{company}的潛在影響"
            ])
        
        return random.choice(templates)
    
    def _generate_financial_answer(self, topic: str, subtopic: str, company: str, instruction: str) -> str:
        """生成金融分析回答"""
        # 基礎回答結構
        analysis_points = []
        
        # 根據子主題添加分析要點
        if "技術分析" in subtopic:
            analysis_points.extend([
                f"{company}近期股價走勢顯示",
                f"從技術指標來看",
                f"支撐位和壓力位分析"
            ])
        elif "基本面分析" in subtopic:
            analysis_points.extend([
                f"{company}的財務數據顯示",
                f"營收成長性分析",
                f"獲利能力評估"
            ])
        elif "風險評估" in subtopic:
            analysis_points.extend([
                f"{company}面臨的主要風險包括",
                f"產業競爭風險",
                f"財務風險評估"
            ])
        
        # 構建回答
        answer_parts = []
        for point in analysis_points[:3]:  # 限制3個要點
            detail = self._generate_analysis_detail(topic, subtopic)
            answer_parts.append(f"{point}{detail}")
        
        # 添加風險警告
        risk_warning = "投資有風險，建議仔細評估並分散投資。"
        
        # 組合完整回答
        full_answer = "。".join(answer_parts) + "。" + risk_warning
        
        return full_answer
    
    def _generate_analysis_detail(self, topic: str, subtopic: str) -> str:
        """生成分析細節"""
        details = [
            "表現穩健，值得持續關注",
            "有一定上漲潛力，但需注意風險控制",
            "短期可能面臨調整壓力",
            "長期投資價值看好",
            "建議等待更好的買點",
            "適合定期定額投資策略"
        ]
        
        return random.choice(details)
    
    def _generate_grpo_query(self, topic: str, subtopic: str, company: str) -> str:
        """生成GRPO查詢"""
        queries = [
            f"分析{company}的投資潛力",
            f"{company}適合現在投資嗎？",
            f"請評估{company}的{subtopic}",
            f"{company}的風險和機會是什麼？",
            f"從{subtopic}角度看{company}怎麼樣？"
        ]
        
        return random.choice(queries)
    
    def _generate_context(self, topic: str, subtopic: str) -> str:
        """生成上下文"""
        contexts = {
            "股票分析": "台股投資分析",
            "市場研究": "市場研究報告",
            "投資理財": "投資理財諮詢",
            "交易策略": "交易策略分析"
        }
        
        return contexts.get(topic, "金融分析")
    
    def _generate_reference_answer(self, topic: str, subtopic: str, company: str) -> str:
        """生成參考答案"""
        return f"針對{company}的{subtopic}，需要綜合考慮多項因素，包括財務表現、市場環境和風險因素。建議投資人仔細研究相關資料後再做決定。"
    
    def _generate_financial_conversation(self) -> List[Dict[str, Any]]:
        """生成金融對話"""
        topic = random.choice(list(self.financial_topics.keys()))
        company = random.choice(self.taiwan_companies)
        
        conversation = [
            {
                "from": "human",
                "value": f"我想了解{company}的投資價值，可以幫我分析嗎？",
                "metadata": {"topic": topic}
            },
            {
                "from": "gpt",
                "value": f"我來為您分析{company}的投資價值。首先需要從幾個維度來評估：財務面、技術面和基本面。讓我詳細說明..."
            },
            {
                "from": "human", 
                "value": "那風險方面需要注意什麼？"
            },
            {
                "from": "gpt",
                "value": f"投資{company}需要注意以下風險：產業競爭加劇、市場波動風險、以及總體經濟變化的影響。建議分散投資並設定合理的停損點。"
            }
        ]
        
        return conversation


class DataValidator:
    """
    數據驗證器
    確保訓練數據的質量和一致性
    """
    
    def __init__(self, config: DatasetConfig):
        self.config = config
        
        # 質量檢查規則
        self.quality_rules = {
            'min_length': config.min_length,
            'max_length': config.max_length,
            'required_fields': self._get_required_fields(),
            'forbidden_patterns': [
                r'內線消息', r'保證獲利', r'穩賺不賠', r'明牌',
                r'一定會漲', r'絕對安全'
            ]
        }
    
    def _get_required_fields(self) -> List[str]:
        """獲取必需字段"""
        if self.config.data_format == DataFormat.ALPACA:
            return ['instruction', 'output']
        elif self.config.data_format == DataFormat.GRPO:
            return ['query', 'reference']
        elif self.config.data_format == DataFormat.SHAREGPT:
            return ['conversations']
        else:
            return []
    
    def validate_sample(self, sample: Dict[str, Any]) -> Tuple[bool, float, List[str]]:
        """
        驗證單個樣本
        
        Returns:
            (是否有效, 質量分數, 問題列表)
        """
        issues = []
        quality_score = 1.0
        
        # 檢查必需字段
        for field in self.quality_rules['required_fields']:
            if field not in sample:
                issues.append(f"缺少必需字段: {field}")
                quality_score -= 0.3
        
        # 檢查內容長度
        content_text = self._extract_text_content(sample)
        if len(content_text) < self.quality_rules['min_length']:
            issues.append(f"內容過短: {len(content_text)} < {self.quality_rules['min_length']}")
            quality_score -= 0.2
        
        if len(content_text) > self.quality_rules['max_length']:
            issues.append(f"內容過長: {len(content_text)} > {self.quality_rules['max_length']}")
            quality_score -= 0.2
        
        # 檢查禁用模式
        for pattern in self.quality_rules['forbidden_patterns']:
            if re.search(pattern, content_text):
                issues.append(f"包含禁用內容: {pattern}")
                quality_score -= 0.4
        
        # 檢查金融相關性
        financial_relevance = self._check_financial_relevance(content_text)
        if financial_relevance < 0.3:
            issues.append("金融相關性不足")
            quality_score -= 0.3
        
        # 最終質量分數
        quality_score = max(0.0, min(1.0, quality_score))
        is_valid = quality_score >= self.config.quality_threshold and not any("缺少必需字段" in issue for issue in issues)
        
        return is_valid, quality_score, issues
    
    def _extract_text_content(self, sample: Dict[str, Any]) -> str:
        """提取樣本的文本內容"""
        content_parts = []
        
        if 'instruction' in sample:
            content_parts.append(sample['instruction'])
        if 'input' in sample and sample['input']:
            content_parts.append(sample['input'])
        if 'output' in sample:
            content_parts.append(sample['output'])
        if 'query' in sample:
            content_parts.append(sample['query'])
        if 'reference' in sample:
            content_parts.append(sample['reference'])
        if 'conversations' in sample:
            for turn in sample['conversations']:
                if 'value' in turn:
                    content_parts.append(turn['value'])
        
        return ' '.join(content_parts)
    
    def _check_financial_relevance(self, text: str) -> float:
        """檢查金融相關性"""
        financial_keywords = [
            '投資', '股票', '股價', '分析', '風險', '報酬', '市場',
            '財務', '獲利', '營收', '本益比', '殖利率', '技術分析',
            '基本面', '產業', '經濟', '資產', '配置', '理財'
        ]
        
        keyword_count = sum(1 for keyword in financial_keywords if keyword in text)
        relevance_score = min(1.0, keyword_count / 10)  # 10個關鍵詞得滿分
        
        return relevance_score


class TrainingDataSystem:
    """
    訓練數據和範例系統主類
    統一管理所有訓練相關的數據處理
    """
    
    def __init__(self, config_path: Optional[str] = None):
        logger.info("🗃️ 初始化訓練數據系統...")
        
        # 加載配置
        self.config = self._load_config(config_path)
        
        # 初始化組件
        self.example_generator = FinancialExampleGenerator()
        
        # 數據存儲
        self.datasets: Dict[str, List[DataSample]] = {}
        self.dataset_configs: Dict[str, DatasetConfig] = {}
        self.dataset_stats: Dict[str, DatasetStats] = {}
        
        # 數據路徑
        self.data_base_path = Path(self.config.get('data_base_path', '/app/data/training'))
        self.data_base_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ 訓練數據系統初始化完成")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """加載系統配置"""
        default_config = {
            'data_base_path': '/app/data/training',
            'supported_formats': ['alpaca', 'sharegpt', 'grpo'],
            'default_train_ratio': 0.8,
            'default_validation_ratio': 0.1,
            'default_test_ratio': 0.1,
            'quality_threshold': 0.7,
            'enable_parallel_processing': True,
            'max_workers': 4,
            'auto_backup': True,
            'backup_interval_hours': 24
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logger.info(f"📋 配置已從 {config_path} 載入")
            except Exception as e:
                logger.warning(f"⚠️ 配置載入失敗 {config_path}: {e}")
        
        return default_config
    
    def create_dataset(self, 
                      name: str,
                      dataset_type: DatasetType,
                      data_format: DataFormat,
                      num_samples: int,
                      **kwargs) -> str:
        """
        創建新的數據集
        
        Returns:
            數據集ID
        """
        dataset_id = f"{name}_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"📊 創建數據集: {name} (類型: {dataset_type.value}, 格式: {data_format.value})")
        
        # 創建數據集配置
        dataset_config = DatasetConfig(
            name=name,
            description=kwargs.get('description', f'{dataset_type.value}數據集'),
            dataset_type=dataset_type,
            data_format=data_format,
            total_samples=num_samples,
            **{k: v for k, v in kwargs.items() if k in DatasetConfig.__annotations__}
        )
        
        self.dataset_configs[dataset_id] = dataset_config
        
        # 生成數據樣本
        samples = self._generate_samples(dataset_config, num_samples)
        
        # 驗證數據質量
        validated_samples = self._validate_samples(samples, dataset_config)
        
        # 存儲數據集
        self.datasets[dataset_id] = validated_samples
        
        # 更新統計信息
        self._update_dataset_stats(dataset_id)
        
        # 保存到文件
        self._save_dataset(dataset_id)
        
        logger.info(f"✅ 數據集創建完成: {dataset_id} ({len(validated_samples)} 個有效樣本)")
        
        return dataset_id
    
    def _generate_samples(self, config: DatasetConfig, num_samples: int) -> List[DataSample]:
        """生成數據樣本"""
        logger.info(f"🔄 生成 {num_samples} 個 {config.dataset_type.value} 樣本...")
        
        samples = []
        
        if config.dataset_type == DatasetType.SFT:
            raw_samples = self.example_generator.generate_sft_samples(num_samples)
        elif config.dataset_type == DatasetType.GRPO:
            raw_samples = self.example_generator.generate_grpo_samples(num_samples)
        elif config.dataset_type == DatasetType.CHAT:
            raw_samples = self.example_generator.generate_chat_samples(num_samples)
        else:
            # 默認生成SFT樣本
            raw_samples = self.example_generator.generate_sft_samples(num_samples)
        
        # 轉換為DataSample對象
        for i, raw_sample in enumerate(raw_samples):
            sample = DataSample(
                sample_id=f"{config.name}_{i:06d}",
                dataset_type=config.dataset_type,
                data_format=config.data_format,
                content=raw_sample,
                metadata={
                    'created_at': datetime.now().isoformat(),
                    'generator': 'FinancialExampleGenerator',
                    'version': '1.0.0'
                },
                created_at=datetime.now().isoformat()
            )
            samples.append(sample)
        
        return samples
    
    def _validate_samples(self, samples: List[DataSample], config: DatasetConfig) -> List[DataSample]:
        """驗證數據樣本"""
        logger.info(f"🔍 驗證 {len(samples)} 個數據樣本...")
        
        validator = DataValidator(config)
        validated_samples = []
        validation_stats = {'valid': 0, 'invalid': 0, 'total_issues': 0}
        
        for sample in samples:
            is_valid, quality_score, issues = validator.validate_sample(sample.content)
            
            sample.quality_score = quality_score
            sample.validated = True
            
            if issues:
                sample.metadata['validation_issues'] = issues
                validation_stats['total_issues'] += len(issues)
            
            if is_valid:
                validated_samples.append(sample)
                validation_stats['valid'] += 1
            else:
                validation_stats['invalid'] += 1
        
        logger.info(f"✅ 驗證完成: {validation_stats['valid']} 有效, {validation_stats['invalid']} 無效")
        
        if validation_stats['total_issues'] > 0:
            logger.warning(f"⚠️ 發現 {validation_stats['total_issues']} 個數據質量問題")
        
        return validated_samples
    
    def split_dataset(self, dataset_id: str, 
                     train_ratio: Optional[float] = None,
                     validation_ratio: Optional[float] = None,
                     test_ratio: Optional[float] = None) -> Dict[str, List[DataSample]]:
        """分割數據集"""
        if dataset_id not in self.datasets:
            raise ValueError(f"數據集不存在: {dataset_id}")
        
        config = self.dataset_configs[dataset_id]
        samples = self.datasets[dataset_id]
        
        # 使用配置的比例
        train_ratio = train_ratio or config.train_ratio
        validation_ratio = validation_ratio or config.validation_ratio
        test_ratio = test_ratio or config.test_ratio
        
        # 確保比例總和為1
        total_ratio = train_ratio + validation_ratio + test_ratio
        if abs(total_ratio - 1.0) > 0.01:
            train_ratio /= total_ratio
            validation_ratio /= total_ratio
            test_ratio /= total_ratio
        
        # 隨機打亂樣本
        shuffled_samples = samples.copy()
        random.shuffle(shuffled_samples)
        
        total_samples = len(shuffled_samples)
        train_size = int(total_samples * train_ratio)
        val_size = int(total_samples * validation_ratio)
        
        # 分割數據
        splits = {
            'train': shuffled_samples[:train_size],
            'validation': shuffled_samples[train_size:train_size + val_size],
            'test': shuffled_samples[train_size + val_size:]
        }
        
        logger.info(f"📊 數據集分割完成: 訓練={len(splits['train'])}, "
                   f"驗證={len(splits['validation'])}, 測試={len(splits['test'])}")
        
        return splits
    
    def export_dataset(self, dataset_id: str, 
                      output_path: str,
                      split: Optional[str] = None,
                      export_format: str = 'jsonl') -> str:
        """導出數據集"""
        if dataset_id not in self.datasets:
            raise ValueError(f"數據集不存在: {dataset_id}")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if split:
            # 導出特定分割
            splits = self.split_dataset(dataset_id)
            if split not in splits:
                raise ValueError(f"分割不存在: {split}")
            samples_to_export = splits[split]
            export_file = output_path / f"{dataset_id}_{split}.{export_format}"
        else:
            # 導出完整數據集
            samples_to_export = self.datasets[dataset_id]
            export_file = output_path / f"{dataset_id}.{export_format}"
        
        logger.info(f"💾 導出數據集: {export_file} ({len(samples_to_export)} 個樣本)")
        
        if export_format == 'jsonl':
            with open(export_file, 'w', encoding='utf-8') as f:
                for sample in samples_to_export:
                    f.write(json.dumps(sample.content, ensure_ascii=False) + '\n')
        elif export_format == 'json':
            export_data = [sample.content for sample in samples_to_export]
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的導出格式: {export_format}")
        
        logger.info(f"✅ 數據集已導出: {export_file}")
        
        return str(export_file)
    
    def _update_dataset_stats(self, dataset_id: str):
        """更新數據集統計信息"""
        samples = self.datasets[dataset_id]
        config = self.dataset_configs[dataset_id]
        
        # 計算統計信息
        total_samples = len(samples)
        
        # 長度統計
        input_lengths = []
        output_lengths = []
        quality_scores = []
        
        for sample in samples:
            content = sample.content
            quality_scores.append(sample.quality_score)
            
            if 'instruction' in content:
                input_lengths.append(len(content['instruction']))
            if 'output' in content:
                output_lengths.append(len(content['output']))
            if 'query' in content:
                input_lengths.append(len(content['query']))
            if 'reference' in content:
                output_lengths.append(len(content['reference']))
        
        # 質量分布
        quality_distribution = {
            'excellent': sum(1 for s in quality_scores if s >= 0.9),
            'good': sum(1 for s in quality_scores if 0.7 <= s < 0.9),
            'fair': sum(1 for s in quality_scores if 0.5 <= s < 0.7),
            'poor': sum(1 for s in quality_scores if s < 0.5)
        }
        
        # 分割統計
        splits = self.split_dataset(dataset_id)
        
        stats = DatasetStats(
            total_samples=total_samples,
            train_samples=len(splits['train']),
            validation_samples=len(splits['validation']),
            test_samples=len(splits['test']),
            avg_input_length=np.mean(input_lengths) if input_lengths else 0,
            avg_output_length=np.mean(output_lengths) if output_lengths else 0,
            quality_distribution=quality_distribution,
            token_count=sum(input_lengths + output_lengths),
            unique_topics=len(set(s.content.get('topic', 'unknown') for s in samples))
        )
        
        self.dataset_stats[dataset_id] = stats
    
    def _save_dataset(self, dataset_id: str):
        """保存數據集到文件"""
        dataset_dir = self.data_base_path / dataset_id
        dataset_dir.mkdir(exist_ok=True)
        
        # 保存樣本數據
        samples_file = dataset_dir / 'samples.json'
        with open(samples_file, 'w', encoding='utf-8') as f:
            samples_data = [asdict(sample) for sample in self.datasets[dataset_id]]
            json.dump(samples_data, f, indent=2, ensure_ascii=False)
        
        # 保存配置
        config_file = dataset_dir / 'config.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.dataset_configs[dataset_id]), f, indent=2, ensure_ascii=False)
        
        # 保存統計信息
        if dataset_id in self.dataset_stats:
            stats_file = dataset_dir / 'stats.json'
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.dataset_stats[dataset_id]), f, indent=2, ensure_ascii=False)
    
    def load_dataset(self, dataset_path: str) -> str:
        """載入現有數據集"""
        dataset_path = Path(dataset_path)
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"數據集路徑不存在: {dataset_path}")
        
        logger.info(f"📥 載入數據集: {dataset_path}")
        
        # 生成數據集ID
        dataset_id = f"loaded_{dataset_path.stem}_{uuid.uuid4().hex[:8]}"
        
        # 載入JSONL格式數據
        samples = []
        with open(dataset_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                try:
                    data = json.loads(line.strip())
                    
                    # 推斷數據格式和類型
                    if 'conversations' in data:
                        data_format = DataFormat.SHAREGPT
                        dataset_type = DatasetType.CHAT
                    elif 'query' in data and 'reference' in data:
                        data_format = DataFormat.GRPO
                        dataset_type = DatasetType.GRPO
                    else:
                        data_format = DataFormat.ALPACA
                        dataset_type = DatasetType.SFT
                    
                    sample = DataSample(
                        sample_id=f"loaded_{i:06d}",
                        dataset_type=dataset_type,
                        data_format=data_format,
                        content=data,
                        metadata={'loaded_from': str(dataset_path)},
                        created_at=datetime.now().isoformat()
                    )
                    samples.append(sample)
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"⚠️ 跳過無效行 {i+1}: {e}")
        
        # 創建數據集配置
        config = DatasetConfig(
            name=dataset_path.stem,
            description=f"從 {dataset_path} 載入的數據集",
            dataset_type=dataset_type,
            data_format=data_format,
            total_samples=len(samples)
        )
        
        # 存儲數據集
        self.datasets[dataset_id] = samples
        self.dataset_configs[dataset_id] = config
        self._update_dataset_stats(dataset_id)
        
        logger.info(f"✅ 數據集載入完成: {dataset_id} ({len(samples)} 個樣本)")
        
        return dataset_id
    
    def get_dataset_info(self, dataset_id: str) -> Dict[str, Any]:
        """獲取數據集信息"""
        if dataset_id not in self.datasets:
            raise ValueError(f"數據集不存在: {dataset_id}")
        
        config = self.dataset_configs[dataset_id]
        stats = self.dataset_stats.get(dataset_id)
        
        info = {
            'dataset_id': dataset_id,
            'config': asdict(config),
            'stats': asdict(stats) if stats else None,
            'sample_count': len(self.datasets[dataset_id]),
            'created_at': datetime.now().isoformat()
        }
        
        return info
    
    def list_datasets(self) -> List[Dict[str, Any]]:
        """列出所有數據集"""
        return [self.get_dataset_info(dataset_id) for dataset_id in self.datasets.keys()]


def main():
    """主函數 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='訓練數據和範例系統')
    parser.add_argument('--action', type=str, required=True, 
                       choices=['create', 'load', 'export', 'info', 'list'],
                       help='操作類型')
    parser.add_argument('--name', type=str, help='數據集名稱')
    parser.add_argument('--type', type=str, default='sft',
                       choices=['sft', 'lora', 'grpo', 'chat'], 
                       help='數據集類型')
    parser.add_argument('--format', type=str, default='alpaca',
                       choices=['alpaca', 'sharegpt', 'grpo'],
                       help='數據格式')
    parser.add_argument('--samples', type=int, default=1000, help='樣本數量')
    parser.add_argument('--input', type=str, help='輸入文件路徑')
    parser.add_argument('--output', type=str, help='輸出文件路徑')
    parser.add_argument('--dataset-id', type=str, help='數據集ID')
    parser.add_argument('--config', type=str, help='配置文件路徑')
    
    args = parser.parse_args()
    
    try:
        # 創建數據系統
        data_system = TrainingDataSystem(args.config)
        
        if args.action == 'create':
            if not args.name:
                raise ValueError("創建數據集需要提供名稱 (--name)")
            
            dataset_type = DatasetType[args.type.upper()]
            data_format = DataFormat[args.format.upper()]
            
            dataset_id = data_system.create_dataset(
                name=args.name,
                dataset_type=dataset_type,
                data_format=data_format,
                num_samples=args.samples
            )
            
            print(f"✅ 數據集已創建: {dataset_id}")
            
        elif args.action == 'load':
            if not args.input:
                raise ValueError("載入數據集需要提供輸入路徑 (--input)")
            
            dataset_id = data_system.load_dataset(args.input)
            print(f"✅ 數據集已載入: {dataset_id}")
            
        elif args.action == 'export':
            if not args.dataset_id or not args.output:
                raise ValueError("導出數據集需要提供數據集ID和輸出路徑")
            
            export_file = data_system.export_dataset(args.dataset_id, args.output)
            print(f"✅ 數據集已導出: {export_file}")
            
        elif args.action == 'info':
            if not args.dataset_id:
                raise ValueError("查看數據集信息需要提供數據集ID")
            
            info = data_system.get_dataset_info(args.dataset_id)
            print(json.dumps(info, indent=2, ensure_ascii=False))
            
        elif args.action == 'list':
            datasets = data_system.list_datasets()
            print(json.dumps(datasets, indent=2, ensure_ascii=False))
            
    except Exception as e:
        logger.error(f"❌ 操作失敗: {e}")
        raise



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
    # 確保日誌目錄存在
    os.makedirs('/app/logs/training', exist_ok=True)
    
    # 運行主函數
    main()