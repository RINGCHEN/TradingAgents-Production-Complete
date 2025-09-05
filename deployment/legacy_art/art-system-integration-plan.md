# ART 系統整合計劃
## TradingAgents + ART (Agent Reinforcement Trainer) 強化學習系統

> 由 DevOps Engineer 墨子 設計
> 目標：整合強化學習能力到 TradingAgents 交易決策系統

## 1. 系統架構概述

### ART 系統核心特性
- **GRPO 強化學習**：生成式強化策略優化
- **多階段 AI 代理訓練**：支持複雜交易決策鏈
- **RULER 獎勵機制**：零樣本獎勵生成
- **LoRA 微調**：低秩適應模型優化

### 整合架構設計
```
TradingAgents 主系統
├── 現有分析師代理
│   ├── fundamentals_analyst.py
│   ├── news_analyst.py
│   ├── sentiment_analyst.py
│   └── risk_analyst.py
├── ART 強化學習層 (新增)
│   ├── art_trainer/
│   ├── reward_models/
│   ├── policy_optimization/
│   └── trajectory_collector/
└── 整合決策引擎
    ├── traditional_analysis
    ├── reinforcement_decisions
    └── hybrid_recommendations
```

## 2. 基礎設施需求

### CPU 優化資源配置 (GPU → CPU 轉換)
```yaml
# CPU 密集型配置，支持 ART 系統
training_infrastructure:
  gcp_cloud_run:  # 改用 Cloud Run，更經濟
    cpu: "4"  # 4 vCPU
    memory: "8Gi"  # 8GB RAM
    concurrency: 4
    timeout: "3600s"  # 1小時訓練時間
    region: "asia-east1"  # 台灣區域
  
  alternative_compute_engine:  # 備選方案
    machine_type: "c2-standard-16"  # 16 vCPU, 64GB RAM
    disk_size: "100GB"
    zone: "asia-east1-a"
  
  memory_requirements:
    training: "8GB"  # CPU 模式降低需求
    inference: "4GB"
    
  storage_requirements:
    model_storage: "20GB"  # 壓縮模型
    trajectory_data: "10GB"
    logs_monitoring: "5GB"
```

### Docker 容器配置 (CPU 優化版)
```dockerfile
# ART 訓練容器 (CPU 優化)
FROM python:3.11-slim

# 安裝 CPU 優化的依賴
RUN apt-get update && apt-get install -y \
    python3.11 python3-pip git \
    libopenblas-dev liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY art-requirements-cpu.txt .
# CPU 版本的 PyTorch 和優化庫
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install numpy scipy scikit-learn numba
RUN pip install -r art-requirements-cpu.txt

WORKDIR /app/art_trainer
COPY art_integration/ .

# CPU 性能健康檢查
HEALTHCHECK --interval=60s --timeout=30s --retries=3 \
    CMD python -c "import torch; print(f'CPU cores: {torch.get_num_threads()}')" || exit 1
```

## 3. 整合實施計劃

### Phase 1: 基礎整合 (2-3 週)
1. **環境設置**
   - 設置 GCP Compute Engine GPU 實例
   - 安裝 ART 系統依賴
   - 配置 CUDA 和 PyTorch 環境

2. **數據管道建立**
   ```python
   # trajectory_collector.py
   class TradingTrajectoryCollector:
       def collect_trading_decisions(self):
           # 收集交易決策軌跡
           # 整合現有分析師輸出
           pass
       
       def assign_rewards(self, trajectory):
           # 基於實際交易結果分配獎勵
           # 整合台股市場數據
           pass
   ```

3. **獎勵模型設計**
   ```python
   # reward_models/trading_reward.py
   class TradingRewardModel:
       def calculate_reward(self, action, market_result):
           # 獲利率獎勵
           # 風險調整獎勵  
           # 市場時機獎勞
           pass
   ```

### Phase 2: 模型訓練 (3-4 週)
1. **訓練流程設計**
   - 收集歷史交易決策軌跡
   - 實施 GRPO 訓練循環
   - LoRA 微調現有模型

2. **監控和評估**
   - 整合 W&B 訓練監控
   - 設置模型性能指標
   - A/B 測試框架

### Phase 3: 生產部署 (2-3 週)
1. **混合決策系統**
   - 傳統分析 + 强化學習決策
   - 風險控制機制
   - 實時模型更新

## 4. Terraform 基礎設施配置

```hcl
# terraform/art-infrastructure.tf
resource "google_compute_instance" "art_trainer" {
  name         = "tradingagents-art-trainer"
  machine_type = "n1-standard-8"
  zone         = "asia-east1-a"

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 100
    }
  }

  guest_accelerator {
    type  = "nvidia-tesla-t4"
    count = 1
  }

  network_interface {
    network = "default"
    access_config {}
  }

  scheduling {
    on_host_maintenance = "TERMINATE"
  }

  metadata_startup_script = file("${path.module}/art-setup.sh")

  service_account {
    scopes = ["cloud-platform"]
  }

  tags = ["art-trainer", "gpu-instance"]
}

resource "google_storage_bucket" "art_models" {
  name     = "tradingagents-art-models"
  location = "asia-east1"
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
}
```

## 5. 成本估算和優化

### 月度成本估算 (USD) - CPU 優化版
```
CPU 訓練配置對比:

Cloud Run (推薦):
- 計算: $50/月 (按需付費)
- 存儲: $15/月
- 網絡: $10/月
總計: ~$75/月 (節省 81%)

Compute Engine (備選):
- 計算: $120/月 (c2-standard-16)
- 存儲: $20/月
- 網絡: $15/月
總計: ~$155/月 (節省 61%)
```

### 成本優化策略
1. **按需訓練**：只在模型更新時啟動 GPU 實例
2. **預搶占實例**：使用 preemptible instances 降低 70% 成本
3. **模型壓縮**：使用 LoRA 減少存儲和計算需求
4. **批量處理**：累積軌跡數據批量訓練

## 6. 安全和監控配置

### 安全措施
```yaml
security_config:
  iam_roles:
    - "roles/compute.instanceAdmin"
    - "roles/storage.objectAdmin"
  
  firewall_rules:
    - allow_internal_art: "10.0.0.0/8"
    - deny_external: "0.0.0.0/0"
  
  data_encryption:
    - at_rest: "Google Cloud KMS"
    - in_transit: "TLS 1.3"
```

### 監控指標
```python
# monitoring/art_metrics.py
art_metrics = {
    "training_metrics": [
        "reward_improvement_rate",
        "policy_loss",
        "value_loss", 
        "training_time_per_epoch"
    ],
    "business_metrics": [
        "trading_accuracy_improvement",
        "risk_adjusted_returns",
        "decision_confidence_scores"
    ],
    "infrastructure_metrics": [
        "gpu_utilization",
        "memory_usage",
        "training_throughput"
    ]
}
```

## 7. 部署腳本

```bash
#!/bin/bash
# deploy-art-system.sh

set -e

echo "=== ART 系統部署開始 ==="

# 1. 創建 GPU 實例
gcloud compute instances create tradingagents-art-trainer \
    --zone=asia-east1-a \
    --machine-type=n1-standard-8 \
    --accelerator=type=nvidia-tesla-t4,count=1 \
    --maintenance-policy=TERMINATE \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=100GB

# 2. 等待實例啟動
echo "等待實例啟動..."
sleep 60

# 3. 安裝 ART 依賴
gcloud compute ssh tradingagents-art-trainer --zone=asia-east1-a --command="
    sudo apt update && sudo apt install -y python3.11 python3-pip git nvidia-driver-525
    git clone https://github.com/OpenPipe/ART.git
    cd ART && pip install -e .
"

# 4. 部署整合代碼
gcloud compute scp --recurse ./art_integration/ \
    tradingagents-art-trainer:~/ART/ --zone=asia-east1-a

echo "=== ART 系統部署完成 ==="
echo "GPU 實例地址: $(gcloud compute instances describe tradingagents-art-trainer --zone=asia-east1-a --format='value(networkInterfaces[0].accessConfigs[0].natIP)')"
```

## 8. 風險評估和緩解

### 技術風險
1. **GPU 資源成本**：預估月度成本 $400，需要 ROI 評估
2. **模型收斂問題**：強化學習可能不穩定，需要 baseline 比較
3. **數據品質**：台股歷史數據的標註和清洗工作量大

### 緩解策略
1. **漸進式部署**：先在模擬環境測試，再投入實際交易
2. **混合決策**：保留傳統分析作為 fallback
3. **持續監控**：設置性能閾值和自動回滾機制

## 9. 成功指標

### 技術指標
- 模型訓練收斂率 > 90%
- 推理延遲 < 100ms
- GPU 利用率 > 80%

### 業務指標  
- 交易決策準確率提升 > 5%
- 風險調整收益率改善 > 3%
- 用戶滿意度 > 4.5/5

---

**下一步行動**：
1. 獲得業務方 ART 整合的批准和預算
2. 設置 GCP GPU 環境和開發測試
3. 開始 Phase 1 基礎整合開發

*這個計劃為 TradingAgents 系統提供了世界級的 AI 強化學習能力，將顯著提升交易決策的智能化水平。*