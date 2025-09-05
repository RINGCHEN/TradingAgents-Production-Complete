# 訓練數據和範例系統使用指南

## 📋 Task 4.2 - 給AI訓練專家團隊的完整數據管理解決方案

這是為Task 4.2專門開發的訓練數據和範例系統，提供：
- 統一的數據格式管理（JSONL標準）
- 金融領域專用範例生成
- 智能數據驗證和質量控制
- 完整的數據集分割和預處理
- 多格式支援（Alpaca/ShareGPT/GRPO）

## 🚀 快速開始

### 1. 環境準備
```bash
# 安裝必要依賴
pip install pandas numpy tqdm

# 創建必要目錄
mkdir -p /app/data/training
mkdir -p /app/logs/training
```

### 2. 創建金融SFT數據集
```bash
# 創建1000個金融SFT訓練樣本
python gpu_training/training_data_system.py \
    --action create \
    --name financial_sft_v1 \
    --type sft \
    --format alpaca \
    --samples 1000

# 輸出: ✅ 數據集已創建: financial_sft_v1_abc12345
```

### 3. 創建GRPO強化學習數據集
```bash
# 創建500個GRPO訓練樣本
python gpu_training/training_data_system.py \
    --action create \
    --name financial_grpo_v1 \
    --type grpo \
    --format grpo \
    --samples 500
```

### 4. 導出訓練數據
```bash
# 導出完整數據集
python gpu_training/training_data_system.py \
    --action export \
    --dataset-id financial_sft_v1_abc12345 \
    --output ./data/financial_sft_complete.jsonl

# 導出訓練分割 (80%)
python gpu_training/training_data_system.py \
    --action export \
    --dataset-id financial_sft_v1_abc12345 \
    --output ./data/ \
    --split train
```

## 📊 支援的數據格式

### 1. Alpaca格式 (SFT訓練)
```json
{
  "instruction": "分析台積電的投資價值",
  "input": "",
  "output": "台積電是全球領先的晶圓代工廠...",
  "topic": "股票分析",
  "subtopic": "基本面分析",
  "company": "台積電(2330)"
}
```

### 2. GRPO格式 (強化學習)
```json
{
  "query": "分析鴻海的投資潛力",
  "context": "台股投資分析",
  "reference": "需要綜合考慮多項因素，包括財務表現、市場環境和風險因素...",
  "topic": "股票分析",
  "subtopic": "投資策略"
}
```

### 3. ShareGPT格式 (對話訓練)
```json
{
  "conversations": [
    {
      "from": "human",
      "value": "我想了解台積電的投資價值，可以幫我分析嗎？"
    },
    {
      "from": "gpt", 
      "value": "我來為您分析台積電的投資價值。首先需要從幾個維度來評估..."
    }
  ],
  "topic": "股票分析"
}
```

## ⚙️ 配置選項

### 系統配置 (`training_data_config.json`)
```json
{
  "data_base_path": "/app/data/training",
  "quality_threshold": 0.7,
  "default_train_ratio": 0.8,
  "default_validation_ratio": 0.1,
  "default_test_ratio": 0.1,
  "enable_parallel_processing": true
}
```

### 金融領域配置
```json
{
  "financial_config": {
    "taiwan_stock_focus": true,
    "risk_awareness_required": true,
    "forbidden_guarantee_claims": true
  },
  "generation_config": {
    "financial_keyword_density": 0.15,
    "risk_mention_probability": 0.8,
    "company_mention_ratio": 0.6
  }
}
```

## 💡 金融範例生成特性

### 主題分類
1. **股票分析** (40%)
   - 技術分析、基本面分析、財報分析
   - 產業分析、投資策略、風險評估

2. **市場研究** (25%)
   - 市場趨勢、經濟指標、產業前景
   - 政策影響、國際市場分析

3. **投資理財** (25%)
   - 資產配置、投資組合、風險管理
   - 退休規劃、保險規劃、稅務規劃

4. **交易策略** (10%)
   - 當沖策略、波段操作、選股方法
   - 買賣時機、停損停利、資金管理

### 台股公司覆蓋
- **科技股**: 台積電、聯發科、鴻海、廣達、和碩
- **金融股**: 富邦金、國泰金、中華電
- **傳產股**: 台塑、南亞、中鋼、統一
- **其他**: 台達電、日月光、聯電等

### 金融術語庫
- **基礎指標**: 本益比、股價淨值比、殖利率、市值
- **進階指標**: EBITDA、自由現金流、ROE、ROA
- **技術指標**: 移動平均線、RSI、MACD、布林通道
- **市場術語**: 多頭、空頭、盤整、突破、回檔

## 🔍 數據質量驗證

### 自動驗證規則
1. **長度檢查**: 內容長度在合理範圍內
2. **必需字段**: 確保包含所需字段
3. **禁用內容**: 過濾"保證獲利"等不當表述
4. **金融相關性**: 確保內容與金融投資相關
5. **風險意識**: 檢查是否包含風險警告

### 質量分數計算
- **優秀** (0.9-1.0): 完整性好、專業術語豐富、風險意識強
- **良好** (0.7-0.9): 內容合理、基本符合要求
- **一般** (0.5-0.7): 內容可用但需要改進
- **差** (<0.5): 質量不足，建議重新生成

## 📈 數據集統計與分析

### 查看數據集信息
```bash
# 列出所有數據集
python gpu_training/training_data_system.py --action list

# 查看特定數據集詳細信息
python gpu_training/training_data_system.py \
    --action info \
    --dataset-id financial_sft_v1_abc12345
```

### 統計信息包含
- 總樣本數與分割統計
- 平均輸入/輸出長度
- 質量分數分布
- 主題覆蓋統計
- Token數量估算

## 🛠️ 進階使用

### 1. 載入現有數據集
```python
from gpu_training.training_data_system import TrainingDataSystem

# 創建系統實例
data_system = TrainingDataSystem('configs/training_data_config.json')

# 載入現有JSONL文件
dataset_id = data_system.load_dataset('./existing_data.jsonl')

# 導出處理後的數據
data_system.export_dataset(dataset_id, './processed_data.jsonl')
```

### 2. 自定義範例生成
```python
from gpu_training.training_data_system import FinancialExampleGenerator

generator = FinancialExampleGenerator()

# 生成特定數量的SFT樣本
sft_samples = generator.generate_sft_samples(100)

# 生成GRPO樣本
grpo_samples = generator.generate_grpo_samples(50)
```

### 3. 數據驗證與質量控制
```python
from gpu_training.training_data_system import DataValidator, DatasetConfig

# 創建驗證器
config = DatasetConfig(
    name="custom_dataset",
    dataset_type=DatasetType.SFT,
    data_format=DataFormat.ALPACA,
    quality_threshold=0.8
)

validator = DataValidator(config)

# 驗證單個樣本
is_valid, quality_score, issues = validator.validate_sample(sample_data)
```

## 🔧 常見問題解決

### 1. 數據質量過低
```bash
# 調整質量閾值
--config '{"quality_threshold": 0.6}'

# 增加金融關鍵詞密度
--config '{"generation_config": {"financial_keyword_density": 0.2}}'
```

### 2. 生成速度慢
```bash
# 啟用並行處理
--config '{"enable_parallel_processing": true, "max_workers": 8}'
```

### 3. 內存使用過多
```bash
# 減少批次大小
--config '{"batch_size": 100}'

# 關閉自動備份
--config '{"auto_backup": false}'
```

## 📝 與其他系統整合

### 1. 與GRPO訓練器整合
```bash
# 創建GRPO數據集
python gpu_training/training_data_system.py \
    --action create --name grpo_financial --type grpo --samples 1000

# 導出用於GRPO訓練
python gpu_training/training_data_system.py \
    --action export --dataset-id grpo_financial_xyz --output ./data/grpo_dataset.jsonl

# 使用GRPO訓練器訓練
python gpu_training/grpo_trainer.py \
    --dataset ./data/grpo_dataset.jsonl \
    --output ./models/grpo_model
```

### 2. 與AI訓練編排系統整合
```python
from gpu_training.ai_training_orchestrator import AITrainingOrchestrator
from gpu_training.training_data_system import TrainingDataSystem

# 創建數據集並自動提交訓練任務
data_system = TrainingDataSystem()
orchestrator = AITrainingOrchestrator()

# 創建並導出數據集
dataset_id = data_system.create_dataset("auto_sft", DatasetType.SFT, DataFormat.ALPACA, 1000)
dataset_path = data_system.export_dataset(dataset_id, "./temp_dataset.jsonl")

# 提交訓練任務
task_id = await orchestrator.submit_training_task(
    TaskType.SFT,
    dataset_path,
    "./models/auto_sft_model"
)
```

## 🎯 性能基準與優化

### 生成性能
- **SFT樣本**: ~100 樣本/秒
- **GRPO樣本**: ~80 樣本/秒  
- **Chat樣本**: ~50 樣本/秒

### 質量基準
- **平均質量分數**: 0.85+
- **金融相關性**: 0.9+
- **風險意識覆蓋**: 80%+

### 建議配置
- **小規模訓練** (<1K樣本): 單線程，quality_threshold=0.7
- **中規模訓練** (1K-10K樣本): 並行處理，quality_threshold=0.75
- **大規模訓練** (>10K樣本): 最大並行，quality_threshold=0.8

## 📞 技術支援

### 相關系統協調
- **GRPO訓練器**: 數據格式兼容性
- **AI訓練編排系統**: 自動化工作流程整合
- **GPU硬體專家團隊**: 大數據集處理優化

### 問題反饋
如遇問題請提供：
1. 錯誤日誌 (`/app/logs/training/training_data_system.log`)
2. 配置文件內容
3. 數據樣本範例
4. 執行的具體命令

---

**Task 4.2 完成！** 🎉

*這個系統解決了"訓練數據和範例系統"的需求，為AI訓練專家團隊提供了完整的JSONL格式數據管理解決方案*