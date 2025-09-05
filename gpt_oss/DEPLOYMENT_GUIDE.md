# GPT-OSS 本地推理服務部署指南

> 重要：本地 GPU 使用與操作細節，請參考《TradingAgents/gpt_oss/LOCAL_GPU_GUIDE.md》作為統一作業手冊。

## 重要說明：無需額外安裝Ollama

**GPT-OSS 是一個自包含的本地推理服務，不需要 Ollama。** 本方案使用 Hugging Face Transformers 直接載入和運行模型。

## 系統需求

### 硬體需求
- **GPU**: NVIDIA RTX 4070 或更高 (12GB+ VRAM)
- **RAM**: 16GB+ 系統記憶體
- **存儲**: 50GB+ 可用空間（用於模型存儲）
- **CUDA**: 版本 11.7（推理映像）/ 12.1（訓練映像）

### 軟體需求
- Docker 和 Docker Compose
- NVIDIA Docker 支援（nvidia-container-toolkit / nvidia-docker2）
- NVIDIA 驅動程式 (版本 535+)

## 快速部署流程

### 步驟 1: 檢查系統環境

```bash
# 檢查 NVIDIA 驅動
nvidia-smi

# 檢查 Docker 是否支援 GPU（與 GPT-OSS 容器一致，CUDA 11.7）
docker run --rm --gpus all pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime nvidia-smi
```

### 步驟 2: 首次模型下載（可選）

如果網絡速度較慢，可以預先下載模型：

```bash
# 運行模型設置腳本
cd TradingAgents
python gpt_oss/setup_models.py
```

**注意**: 此步驟是可選的，Docker 容器會自動下載模型。

### 步驟 3: 啟動服務

```bash
# 啟動完整的 TradingAgents + GPT-OSS 服務
docker-compose up -d

# 或者只啟動 GPT-OSS 服務
docker-compose up -d gpt-oss
```

### 步驟 4: 驗證部署

```bash
# 檢查服務狀態
docker-compose ps

# 檢查 GPT-OSS 健康狀態
curl http://localhost:8080/health

# 運行整合測試
python test_gpt_oss_integration.py
```

## 服務架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ TradingAgents   │───▶│    GPT-OSS       │───▶│  Llama-3-8B     │
│ API (8000)      │    │  Service (8080)  │    │  Model (GPU)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│               Docker Network (tradingagents-network)           │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  ┌──────────────────┐   │
│  │ Nginx   │  │ Redis   │  │ PostgreSQL│  │ Prometheus/      │   │
│  │ (80)    │  │ (6379)  │  │ (5432) │  │ Grafana          │   │
│  └─────────┘  └─────────┘  └────────┘  │ (9090/3000)      │   │
│                                        └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 配置說明

### GPT-OSS 核心配置

**模型配置**（`gpt_oss/config.yaml`）節選：
```yaml
model:
  name: "meta-llama/Meta-Llama-3-8B-Instruct"
  load_in_4bit: true      # 4-bit 量化節省顯存
  max_memory:
    0: "10GB"             # RTX 4070 優化設置
```

**服務配置**：
```yaml
server:
  host: "0.0.0.0"
  port: 8080
  max_concurrent_requests: 8  # RTX 4070 適中並發
```

### Docker 容器配置

**GPU 配置**（compose 內）：
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**記憶體配置**：
```yaml
shm_size: 2g              # 共享記憶體
mem_limit: 16g            # 容器記憶體限制
```

## 監控與維護

### 監控端點
- Prometheus 指標: `http://localhost:9091/metrics`
- 健康檢查: `http://localhost:8080/health`
- Grafana 儀表板: `http://localhost:3000`

### 日誌查看
```bash
# GPT-OSS 服務日誌
docker logs -f tradingagents-gpt-oss

# 所有服務日誌
docker-compose logs -f
```

### 性能調優（節選）
- 4-bit 量化（`load_in_4bit: true`）
- 控制並發避免 OOM（`max_concurrent_requests`）
- 可啟用 Flash Attention 2（`use_flash_attention_2: true`）

## 故障排除

詳見《TradingAgents/gpt_oss/LOCAL_GPU_GUIDE.md》的 FAQ 與操作手冊。

---

文檔索引：
- 本地 GPU 使用統一手冊：`TradingAgents/gpt_oss/LOCAL_GPU_GUIDE.md`
- 整合架構：`TradingAgents/GPT_OSS_INTEGRATION_ARCHITECTURE.md`
- 訓練環境（如需）：`TradingAgents/gpu_training/README.md`


## 重要說明：無需額外安裝Ollama

**GPT-OSS 是一個自包含的本地推理服務，不需要 Ollama。** 本方案使用 Hugging Face Transformers 直接載入和運行模型。

## 系統需求

### 硬體需求
- **GPU**: NVIDIA RTX 4070 或更高 (12GB+ VRAM)
- **RAM**: 16GB+ 系統記憶體
- **存儲**: 50GB+ 可用空間（用於模型存儲）
- **CUDA**: 版本 12.1+

### 軟體需求
- Docker 和 Docker Compose
- NVIDIA Docker 支援 (`nvidia-docker2`)
- NVIDIA 驅動程式 (版本 535+)

## 快速部署流程

### 步驟 1: 檢查系統環境

```bash
# 檢查 NVIDIA 驅動
nvidia-smi

# 檢查 Docker 是否支援 GPU
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu20.04 nvidia-smi
```

### 步驟 2: 首次模型下載（可選）

如果網絡速度較慢，可以預先下載模型：

```bash
# 運行模型設置腳本
cd TradingAgents
python gpt_oss/setup_models.py
```

**注意**: 此步驟是可選的，Docker 容器會自動下載模型。

### 步驟 3: 啟動服務

```bash
# 啟動完整的 TradingAgents + GPT-OSS 服務
docker-compose up -d

# 或者只啟動 GPT-OSS 服務
docker-compose up -d gpt-oss
```

### 步驟 4: 驗證部署

```bash
# 檢查服務狀態
docker-compose ps

# 檢查 GPT-OSS 健康狀態
curl http://localhost:8080/health

# 運行整合測試
python test_gpt_oss_integration.py
```

## 服務架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ TradingAgents   │───▶│    GPT-OSS       │───▶│  Llama-3-8B     │
│ API (8000)      │    │  Service (8080)  │    │  Model (GPU)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│               Docker Network (tradingagents-network)           │
│  ┌─────────┐  ┌─────────┐  ┌────────┐  ┌──────────────────┐   │
│  │ Nginx   │  │ Redis   │  │ PostgreSQL│  │ Prometheus/      │   │
│  │ (80)    │  │ (6379)  │  │ (5432) │  │ Grafana          │   │
│  └─────────┘  └─────────┘  └────────┘  │ (9090/3000)      │   │
│                                        └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## 配置說明

### GPT-OSS 核心配置

**模型配置** (`gpt_oss/config.yaml`):
```yaml
model:
  name: "meta-llama/Meta-Llama-3-8B-Instruct"
  load_in_4bit: true      # 4-bit 量化節省顯存
  max_memory:
    0: "10GB"             # RTX 4070 優化設置
```

**服務配置**:
```yaml
server:
  host: "0.0.0.0"
  port: 8080
  max_concurrent_requests: 8  # RTX 4070 適中並發
```

### Docker 容器配置

**GPU 配置**:
```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

**記憶體配置**:
```yaml
shm_size: 2g              # 共享記憶體
mem_limit: 16g            # 容器記憶體限制
```

## 監控與維護

### 監控端點
- **Prometheus 指標**: `http://localhost:9091/metrics`
- **健康檢查**: `http://localhost:8080/health`
- **Grafana 儀表板**: `http://localhost:3000`

### 日誌查看
```bash
# GPT-OSS 服務日誌
docker logs -f tradingagents-gpt-oss

# 所有服務日誌
docker-compose logs -f
```

### 性能調優

**GPU 記憶體優化**:
1. 使用 4-bit 量化 (`load_in_4bit: true`)
2. 設置適當的 `max_memory` 限制
3. 調整 `max_concurrent_requests` 避免 OOM

**推理速度優化**:
1. 啟用 Flash Attention 2 (`use_flash_attention_2: true`)
2. 使用 BetterTransformer (`use_bettertransformer: true`)
3. 適當的批次大小設置

## 故障排除

### 常見問題

**1. GPU 不可用**
```bash
# 檢查 NVIDIA 驅動
nvidia-smi

# 檢查 Docker GPU 支援
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu20.04 nvidia-smi
```

**2. 顯存不足 (CUDA OOM)**
```yaml
# 在 config.yaml 中調整
model:
  load_in_4bit: true
  max_memory:
    0: "8GB"  # 減少記憶體分配
```

**3. 模型下載失敗**
```bash
# 手動下載模型
python -c "
from huggingface_hub import snapshot_download
snapshot_download('meta-llama/Meta-Llama-3-8B-Instruct', 
                  local_dir='./models/Meta-Llama-3-8B-Instruct')
"
```

**4. 服務無回應**
```bash
# 檢查容器狀態
docker-compose ps

# 重啟 GPT-OSS 服務
docker-compose restart gpt-oss
```

### 日誌分析

**關鍵日誌位置**:
- GPT-OSS 服務: `./logs/gpt_oss/`
- 系統監控: `docker-compose logs prometheus`

**重要指標監控**:
- GPU 記憶體使用率 < 95%
- GPU 溫度 < 85°C
- 平均回應時間 < 10s
- 錯誤率 < 5%

## 生產部署建議

### 安全配置
1. 設置 API 密鑰驗證
2. 配置防火牆規則
3. 啟用 TLS/SSL 加密

### 高可用性
1. 實施健康檢查和自動重啟
2. 設置監控告警
3. 定期備份模型和配置

### 成本優化
1. 合理設置並發限制
2. 實施請求排隊機制
3. 監控 GPU 使用率

## 下一步操作

部署完成後，建議按以下順序進行：

1. **驗證基本功能**: 運行 `test_gpt_oss_integration.py`
2. **配置智能路由器**: 整合到 TradingAgents 的路由系統
3. **實施監控告警**: 配置 Grafana 告警規則
4. **性能調優**: 基於實際使用情況調整參數
5. **生產部署**: 移至生產環境並實施安全措施

---

**重要提醒**: 
- 無需安裝 Ollama，GPT-OSS 是獨立的推理服務
- 首次啟動可能需要 10-30 分鐘下載模型
- RTX 4070 12GB 足以運行 Llama-3-8B 的 4-bit 量化版本