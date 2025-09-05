"""
Training Data Manager
訓練數據管理器

負責：
- 金融數據預處理
- 訓練數據集構建
- 數據版本控制
- 數據品質監控
"""

import os
import json
import logging
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import torch
from torch.utils.data import Dataset, DataLoader
from datasets import Dataset as HFDataset, load_dataset
import numpy as np

logger = logging.getLogger(__name__)


class FinancialTrainingDataset(Dataset):
    """金融訓練數據集"""
    
    def __init__(
        self,
        queries: List[str],
        responses: List[str],
        contexts: Optional[List[Dict[str, Any]]] = None,
        tokenizer=None,
        max_length: int = 1024
    ):
        self.queries = queries
        self.responses = responses
        self.contexts = contexts or [{}] * len(queries)
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        assert len(self.queries) == len(self.responses) == len(self.contexts)
    
    def __len__(self):
        return len(self.queries)
    
    def __getitem__(self, idx):
        query = self.queries[idx]
        response = self.responses[idx]
        context = self.contexts[idx]
        
        if self.tokenizer:
            # 組合查詢和回應
            full_text = f"{query} {self.tokenizer.eos_token} {response}"
            
            # 編碼
            encoded = self.tokenizer(
                full_text,
                max_length=self.max_length,
                truncation=True,
                padding="max_length",
                return_tensors="pt"
            )
            
            return {
                'input_ids': encoded['input_ids'].squeeze(0),
                'attention_mask': encoded['attention_mask'].squeeze(0),
                'query': query,
                'response': response,
                'context': context
            }
        else:
            return {
                'query': query,
                'response': response,
                'context': context
            }


class TrainingDataManager:
    """訓練數據管理器"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 數據統計
        self.data_stats = {
            'total_samples': 0,
            'train_samples': 0,
            'val_samples': 0,
            'test_samples': 0,
            'last_updated': None
        }
    
    def load_financial_data(
        self,
        data_path: str,
        data_format: str = "jsonl"
    ) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
        """
        載入金融訓練數據
        
        Args:
            data_path: 數據文件路徑
            data_format: 數據格式 ("jsonl", "csv", "json")
            
        Returns:
            (queries, responses, contexts) 元組
        """
        data_path = Path(data_path)
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        queries = []
        responses = []
        contexts = []
        
        if data_format == "jsonl":
            with open(data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    data = json.loads(line.strip())
                    
                    # 支持多種數據格式
                    if 'instruction' in data and 'output' in data:
                        query = data['instruction']
                        if 'input' in data and data['input'].strip():
                            query += f" {data['input']}"
                        response = data['output']
                    elif 'query' in data and 'response' in data:
                        query = data['query']
                        response = data['response']
                    elif 'question' in data and 'answer' in data:
                        query = data['question']
                        response = data['answer']
                    else:
                        continue
                    
                    queries.append(query)
                    responses.append(response)
                    
                    # 提取上下文信息
                    context = {k: v for k, v in data.items() 
                              if k not in ['instruction', 'input', 'output', 'query', 'response', 'question', 'answer']}
                    contexts.append(context)
        
        elif data_format == "csv":
            df = pd.read_csv(data_path)
            
            # 假設CSV有query和response列
            if 'query' in df.columns and 'response' in df.columns:
                queries = df['query'].tolist()
                responses = df['response'].tolist()
                
                # 其他列作為上下文
                context_columns = [col for col in df.columns if col not in ['query', 'response']]
                contexts = df[context_columns].to_dict('records')
            else:
                raise ValueError("CSV must contain 'query' and 'response' columns")
        
        elif data_format == "json":
            with open(data_path, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
            
            for data in data_list:
                if 'query' in data and 'response' in data:
                    queries.append(data['query'])
                    responses.append(data['response'])
                    
                    context = {k: v for k, v in data.items() if k not in ['query', 'response']}
                    contexts.append(context)
        
        logger.info(f"Loaded {len(queries)} samples from {data_path}")
        
        # 更新統計信息
        self.data_stats['total_samples'] = len(queries)
        self.data_stats['last_updated'] = datetime.now().isoformat()
        
        return queries, responses, contexts
    
    def create_financial_training_examples(self) -> List[Dict[str, Any]]:
        """
        創建金融訓練範例數據
        
        用於演示和測試
        """
        examples = [
            {
                "query": "分析台積電(2330)的投資前景",
                "response": "台積電作為全球半導體龍頭，具有以下投資亮點：1. 先進製程技術領先優勢明顯 2. AI晶片需求強勁帶動營收成長 3. 長期客戶關係穩固。不過需注意地緣政治風險和景氣循環影響。建議長期投資者可考慮分批布局，但請注意投資風險，建議諮詢專業投資顧問。",
                "context": {
                    "stock_code": "2330",
                    "company": "台積電",
                    "sector": "半導體",
                    "market_cap": "大型股"
                }
            },
            {
                "query": "現在適合買進金融股嗎？",
                "response": "金融股投資需考慮以下因素：1. 利率環境：升息週期有利銀行獲利 2. 經濟景氣：影響放款品質和需求 3. 法規變化：金融監理政策影響。目前建議關注體質健全的大型金控，如富邦金、國泰金等。投資前請評估個人風險承受度，並建議分散投資降低風險。此為個人觀點，非投資建議，投資有風險請謹慎評估。",
                "context": {
                    "sector": "金融",
                    "investment_type": "sector_analysis",
                    "risk_level": "medium"
                }
            },
            {
                "query": "如何評估一檔股票的合理價位？",
                "response": "評估股票合理價位可使用多種方法：1. 本益比(P/E)：股價除以每股盈餘，與同業比較 2. 股價淨值比(P/B)：適用於資產型公司 3. 現金流折現法：預估未來現金流並折現 4. 股息殖利率：年股息除以股價。建議綜合多種指標判斷，並考慮公司基本面、產業前景等因素。投資決策應基於充分研究，建議諮詢專業財務顧問。",
                "context": {
                    "topic": "valuation",
                    "difficulty": "intermediate",
                    "methods": ["PE", "PB", "DCF", "dividend_yield"]
                }
            }
        ]
        
        return examples
    
    def split_data(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[Dict[str, Any]],
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1,
        random_seed: int = 42
    ) -> Tuple[Tuple[List[str], List[str], List[Dict[str, Any]]], ...]:
        """
        分割數據為訓練/驗證/測試集
        
        Returns:
            ((train_queries, train_responses, train_contexts),
             (val_queries, val_responses, val_contexts),
             (test_queries, test_responses, test_contexts))
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, "Ratios must sum to 1.0"
        
        # 設置隨機種子
        np.random.seed(random_seed)
        
        # 創建索引並打亂
        indices = np.arange(len(queries))
        np.random.shuffle(indices)
        
        # 計算分割點
        n_total = len(queries)
        n_train = int(n_total * train_ratio)
        n_val = int(n_total * val_ratio)
        
        # 分割索引
        train_indices = indices[:n_train]
        val_indices = indices[n_train:n_train + n_val]
        test_indices = indices[n_train + n_val:]
        
        # 分割數據
        def split_by_indices(data_list, indices):
            return [data_list[i] for i in indices]
        
        train_data = (
            split_by_indices(queries, train_indices),
            split_by_indices(responses, train_indices),
            split_by_indices(contexts, train_indices)
        )
        
        val_data = (
            split_by_indices(queries, val_indices),
            split_by_indices(responses, val_indices),
            split_by_indices(contexts, val_indices)
        )
        
        test_data = (
            split_by_indices(queries, test_indices),
            split_by_indices(responses, test_indices),
            split_by_indices(contexts, test_indices)
        )
        
        # 更新統計信息
        self.data_stats.update({
            'train_samples': len(train_indices),
            'val_samples': len(val_indices),
            'test_samples': len(test_indices)
        })
        
        logger.info(f"Data split: Train={len(train_indices)}, Val={len(val_indices)}, Test={len(test_indices)}")
        
        return train_data, val_data, test_data
    
    def create_dataset(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[Dict[str, Any]],
        tokenizer=None,
        max_length: int = 1024
    ) -> FinancialTrainingDataset:
        """創建PyTorch數據集"""
        return FinancialTrainingDataset(
            queries=queries,
            responses=responses,
            contexts=contexts,
            tokenizer=tokenizer,
            max_length=max_length
        )
    
    def create_dataloader(
        self,
        dataset: FinancialTrainingDataset,
        batch_size: int = 4,
        shuffle: bool = True,
        num_workers: int = 4
    ) -> DataLoader:
        """創建數據載入器"""
        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            num_workers=num_workers,
            pin_memory=torch.cuda.is_available()
        )
    
    def validate_data_quality(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        驗證數據品質
        
        Returns:
            品質報告字典
        """
        quality_report = {
            'total_samples': len(queries),
            'issues': [],
            'statistics': {},
            'recommendations': []
        }
        
        # 檢查空值
        empty_queries = sum(1 for q in queries if not q.strip())
        empty_responses = sum(1 for r in responses if not r.strip())
        
        if empty_queries > 0:
            quality_report['issues'].append(f"Found {empty_queries} empty queries")
        
        if empty_responses > 0:
            quality_report['issues'].append(f"Found {empty_responses} empty responses")
        
        # 長度統計
        query_lengths = [len(q) for q in queries]
        response_lengths = [len(r) for r in responses]
        
        quality_report['statistics'] = {
            'query_length': {
                'mean': np.mean(query_lengths),
                'std': np.std(query_lengths),
                'min': np.min(query_lengths),
                'max': np.max(query_lengths)
            },
            'response_length': {
                'mean': np.mean(response_lengths),
                'std': np.std(response_lengths),
                'min': np.min(response_lengths),
                'max': np.max(response_lengths)
            }
        }
        
        # 檢查異常長度
        if np.max(query_lengths) > 1000:
            quality_report['issues'].append("Some queries are very long (>1000 chars)")
        
        if np.max(response_lengths) > 2000:
            quality_report['issues'].append("Some responses are very long (>2000 chars)")
        
        # 重複檢查
        unique_queries = len(set(queries))
        if unique_queries < len(queries):
            duplicates = len(queries) - unique_queries
            quality_report['issues'].append(f"Found {duplicates} duplicate queries")
        
        # 建議
        if len(queries) < 1000:
            quality_report['recommendations'].append("Consider collecting more training data (recommended: 1000+ samples)")
        
        if np.mean(response_lengths) < 50:
            quality_report['recommendations'].append("Responses seem short, consider more detailed responses")
        
        return quality_report
    
    def save_processed_data(
        self,
        queries: List[str],
        responses: List[str],
        contexts: List[Dict[str, Any]],
        output_path: str,
        format: str = "jsonl"
    ):
        """保存處理後的數據"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "jsonl":
            with open(output_path, 'w', encoding='utf-8') as f:
                for query, response, context in zip(queries, responses, contexts):
                    data = {
                        'query': query,
                        'response': response,
                        **context
                    }
                    f.write(json.dumps(data, ensure_ascii=False) + '\n')
        
        elif format == "json":
            data_list = []
            for query, response, context in zip(queries, responses, contexts):
                data = {
                    'query': query,
                    'response': response,
                    **context
                }
                data_list.append(data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved {len(queries)} samples to {output_path}")
    
    def get_data_stats(self) -> Dict[str, Any]:
        """獲取數據統計信息"""
        return self.data_stats.copy()
    
    def create_demo_dataset(self, output_dir: str = None):
        """創建演示數據集"""
        if output_dir is None:
            output_dir = self.data_dir / "demo"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 創建範例數據
        examples = self.create_financial_training_examples()
        
        queries = [ex['query'] for ex in examples]
        responses = [ex['response'] for ex in examples]
        contexts = [ex['context'] for ex in examples]
        
        # 保存數據
        self.save_processed_data(
            queries, responses, contexts,
            output_dir / "training_data.jsonl"
        )
        
        # 保存統計信息
        stats = {
            'total_samples': len(examples),
            'created_at': datetime.now().isoformat(),
            'data_type': 'demo',
            'description': 'Demonstration dataset for financial AI training'
        }
        
        with open(output_dir / "data_stats.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Created demo dataset in {output_dir}")
        return output_dir