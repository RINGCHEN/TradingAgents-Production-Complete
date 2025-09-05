# GRPO/PPO訓練完整實現使用指南

## 📋 給小k（AI訓練專家團隊）的使用說明

這是為Task 4.1專門開發的完整GRPO/PPO訓練實現，包含：
- 完整的金融領域獎勵模型
- RTX 4070優化配置
- 企業級錯誤處理和恢復機制
- W&B監控集成

## 🚀 快速開始

### 1. 環境準備
```bash
# 安裝必要的依賴
pip install transformers trl datasets torch accelerate bitsandbytes wandb tqdm numpy

# 設置環境變量
export WANDB_PROJECT="tradingagents-grpo"
export CUDA_VISIBLE_DEVICES=0
```

### 2. 創建示例數據集
```bash
# 創建100個示例樣本用於測試
python gpu_training/grpo_trainer.py --create-demo --dataset ./data/demo_grpo_dataset.jsonl --demo-samples 100
```

### 3. 開始訓練
```bash
# 使用默認配置訓練
python gpu_training/grpo_trainer.py \
    --dataset ./data/demo_grpo_dataset.jsonl \
    --output ./models/grpo_financial_model

# 使用自定義配置文件
python gpu_training/grpo_trainer.py \
    --dataset ./data/your_dataset.jsonl \
    --output ./models/your_model \
    --config ./configs/grpo_config.json
```

## 📊 數據格式

### 支持的數據格式

#### 格式1: GRPO專用格式
```json
{"query": "分析台積電的投資價值", "context": "台股投資分析", "reference": "參考回答"}
{"query": "如何評估鴻海的財務狀況", "context": "財務分析", "reference": "參考回答"}
```

#### 格式2: 標準指令格式（自動轉換）
```json
{"instruction": "分析台積電的投資價值", "input": "", "output": "台積電是全球領先的晶圓代工廠..."}
{"instruction": "評估風險", "input": "鴻海科技", "output": "需要考慮以下風險因素..."}
```

## ⚙️ 配置選項

### RTX 4070優化配置
```json
{
  "model_name": "microsoft/DialoGPT-medium",
  "max_length": 512,
  "learning_rate": 1.4e-5,
  "batch_size": 4,
  "mini_batch_size": 2,
  "gradient_accumulation_steps": 8,
  "ppo_epochs": 4,
  "num_train_epochs": 3,
  "use_fp16": true,
  "gradient_checkpointing": true,
  "use_wandb": true
}
```

### 獎勵模型配置
```json
{
  "accuracy_weight": 0.4,
  "risk_assessment_weight": 0.3,
  "recommendation_weight": 0.2,
  "language_quality_weight": 0.1,
  "max_reward": 1.0,
  "min_reward": -1.0
}
```

## 💡 金融獎勵模型特性

### 評估維度
1. **分析準確性 (40%)**
   - 金融關鍵詞使用
   - 回應長度合理性
   - 問題相關性

2. **風險評估 (30%)**
   - 風險詞彙使用
   - 風險警告提及
   - 避免絕對表述

3. **投資建議 (20%)**
   - 具體建議給出
   - 建議理由說明
   - 操作指導明確

4. **語言品質 (10%)**
   - 語句完整性
   - 專業術語使用
   - 邏輯連貫性

### 獎勵機制
- ✅ **正面獎勵**: 使用金融專業詞彙、提及風險控制
- ❌ **負面懲罰**: 使用"保證"、"穩賺"等不當表述
- 🎯 **特殊獎勵**: 風險警告、分散投資建議

## 📈 監控和調試

### W&B監控
訓練過程中會自動記錄：
- 平均獎勵分數
- KL散度
- 訓練損失
- GPU使用率

### 日誌文件
- 訓練日誌: `/app/logs/training/grpo_trainer.log`
- 模型配置: `{output_dir}/training_config.json`
- 訓練統計: `{output_dir}/training_stats.json`

## 🔧 常見問題解決

### 1. GPU記憶體不足
```bash
# 減少批次大小
--config '{"batch_size": 2, "mini_batch_size": 1}'

# 啟用梯度檢查點
--config '{"gradient_checkpointing": true}'
```

### 2. 訓練速度慢
```bash
# 增加梯度累積步驟
--config '{"gradient_accumulation_steps": 16}'

# 減少PPO epochs
--config '{"ppo_epochs": 2}'
```

### 3. 獎勵分數過低
- 檢查數據集質量
- 調整獎勵模型權重
- 增加金融關鍵詞

## 📝 進階使用

### 自定義獎勵模型
```python
from gpu_training.grpo_trainer import FinancialRewardModel, FinancialRewardConfig

# 創建自定義獎勵配置
custom_reward_config = FinancialRewardConfig(
    accuracy_weight=0.5,  # 提高準確性權重
    risk_assessment_weight=0.3,
    recommendation_weight=0.15,
    language_quality_weight=0.05
)

# 創建自定義獎勵模型
reward_model = FinancialRewardModel(custom_reward_config)
```

### 模型推理測試
```python
from transformers import AutoTokenizer, AutoModelForCausalLM

# 載入訓練好的模型
model_path = "./models/grpo_financial_model/best_model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# 測試推理
query = "分析台積電的投資價值"
inputs = tokenizer.encode(query, return_tensors="pt")
outputs = model.generate(inputs, max_length=200, do_sample=True)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

## 🎯 性能基準

### RTX 4070預期性能
- **批次大小**: 4 (最佳平衡)
- **訓練速度**: ~2-3 步/秒
- **記憶體使用**: ~8-10GB
- **推薦訓練時間**: 中等數據集 2-4小時

### 獎勵分數參考
- **優秀回應**: 0.7-1.0
- **良好回應**: 0.4-0.7
- **一般回應**: 0.1-0.4
- **需改進**: < 0.1

## 📞 技術支援

如遇問題請聯繫：
- **天工開物核心團隊**: 架構和集成問題
- **GPU硬體專家團隊**: 性能優化問題
- **基礎設施團隊**: 監控和部署問題

---

**祝小k訓練順利！** 🚀

*這個實現已經解決了Task 4.1中"缺少完整的GRPO實現範例"的問題*