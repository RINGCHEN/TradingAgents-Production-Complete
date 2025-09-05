# GPT-OSS RTX 4070 8GB 設置指南

本指南專為 RTX 4070 8GB VRAM 環境優化，提供完整的開源模型配置和部署方案。

## 🎯 核心特色

- **記憶體優化**: 針對 8GB VRAM 精確調整
- **智能模型選擇**: 根據硬體自動選擇最適合的開源模型
- **中文金融專用**: 優化金融分析和中文對話能力
- **一鍵啟動**: 全自動環境檢測和配置
- **無需授權**: 完全使用開源模型，無需特殊授權

## 📋 推薦模型 (按記憶體需求排序)

| 模型 | VRAM需求 | 中文支持 | 金融領域 | 說明 |
|------|----------|----------|----------|------|
| **Qwen/Qwen2-1.5B-Instruct** | ~2GB | 優秀 | 良好 | **推薦選擇** - 最佳平衡 |
| microsoft/DialoGPT-large | ~1.5GB | 基礎 | 一般 | 穩定的對話模型 |
| microsoft/DialoGPT-medium | ~0.5GB | 基礎 | 一般 | 超輕量選擇 |
| THUDM/chatglm3-6b | ~4GB | 優秀 | 優秀 | 高性能中文模型 |

## 🚀 快速開始

### 1. 環境準備

確保已安裝必要依賴:

```bash
# 安裝依賴 (在 TradingAgents/gpt_oss 目錄下)
pip install -r requirements-gpt-oss.txt

# 或安裝CPU版本 (如果沒有GPU)
pip install -r requirements-gpt-oss-cpu.txt
```

### 2. 驗證配置

運行配置驗證腳本:

```bash
python validate_setup.py
```

此腳本會自動檢查:
- ✅ GPU/CPU 環境
- ✅ 依賴包完整性  
- ✅ 配置文件正確性
- ✅ 啟動腳本可用性

### 3. 下載和設置模型

```bash
# 自動下載最適合的模型
python setup_models.py
```

腳本會根據你的硬體配置自動:
- 🔍 檢測GPU記憶體大小
- 🎯 選擇最適合的模型
- 📥 自動下載模型文件
- 🧪 測試模型生成能力
- ⚙️ 生成優化配置

### 4. 啟動服務

#### Windows:
```cmd
start_gpt_oss.bat
```

#### Linux/Mac:
```bash
chmod +x start_gpt_oss.sh
./start_gpt_oss.sh
```

#### 直接Python:
```bash
python server.py
```

### 5. 測試服務

服務啟動後，測試健康檢查:

```bash
curl http://localhost:8080/health
```

預期返回:
```json
{
  "status": "healthy",
  "service": "gpt-oss",
  "version": "2.0.0",
  "device": "cuda",
  "model": "Qwen/Qwen2-1.5B-Instruct",
  "model_loaded": true
}
```

## ⚙️ 配置詳解

### config.yaml 主要配置項

```yaml
model:
  # 基礎模型 (自動選擇最佳)
  name: "Qwen/Qwen2-1.5B-Instruct"
  
  # 記憶體配置
  torch_dtype: "float16"     # 節省記憶體
  load_in_4bit: true         # 4-bit量化
  max_memory:
    0: "7GB"                 # 為8GB VRAM預留1GB

performance:
  # RTX 4070 8GB 優化設置
  max_memory_allocation: 0.85        # 保守的記憶體分配
  garbage_collection_threshold: 0.75  # 積極的垃圾回收
  use_flash_attention_2: true        # 使用高效注意力機制
  gradient_checkpointing: true       # 犧牲少許速度換取記憶體
```

### 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `BASE_MODEL` | Qwen/Qwen2-1.5B-Instruct | 基礎模型名稱 |
| `LOAD_IN_4BIT` | true | 是否使用4-bit量化 |
| `HOST` | 0.0.0.0 | 服務器綁定地址 |
| `PORT` | 8080 | 服務器端口 |
| `DEVICE` | auto | 計算設備 (auto/cuda/cpu) |

## 📊 性能調優

### RTX 4070 8GB 最佳配置

```yaml
# 記憶體優化配置
performance:
  max_memory_allocation: 0.85      # 不超過85%記憶體
  kv_cache_dtype: "float16"        # KV緩存使用float16
  attention_dropout: 0.0           # 關閉dropout節省記憶體
  dataloader_num_workers: 2        # 適中的數據載入並行數

# 量化配置  
quantization:
  bits: 4                          # 4-bit量化
  quant_type: "nf4"               # 使用NF4量化
  compute_dtype: "float16"         # 計算使用float16
  bnb_4bit_quant_storage: "uint8"  # 存儲進一步壓縮
```

### 批處理設置

```yaml
generation:
  batch_size: 4           # 適中的批處理大小
  max_batch_size: 8       # 最大批處理
  stream: true            # 啟用流式輸出
```

## 🔧 故障排除

### 常見問題

#### 1. GPU記憶體不足 (OOM)

**錯誤**: `torch.cuda.OutOfMemoryError`

**解決方案**:
```bash
# 1. 使用更小的模型
export BASE_MODEL="microsoft/DialoGPT-medium"

# 2. 啟用4-bit量化
export LOAD_IN_4BIT="true"

# 3. 減少批處理大小 (修改config.yaml)
generation:
  batch_size: 1
  max_batch_size: 2
```

#### 2. 模型下載失敗

**錯誤**: 網路連接問題或權限錯誤

**解決方案**:
```bash
# 1. 檢查網路連接
ping huggingface.co

# 2. 使用備選模型
python setup_models.py

# 3. 手動設置代理 (如需要)
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

#### 3. 模型載入錯誤

**錯誤**: `trust_remote_code` 相關錯誤

**解決方案**: 腳本會自動回退到標準載入模式，無需手動處理。

#### 4. CPU模式性能差

**現象**: GPU不可用，使用CPU運行很慢

**解決方案**:
```bash
# 1. 檢查CUDA安裝
nvidia-smi

# 2. 檢查PyTorch CUDA支援
python -c "import torch; print(torch.cuda.is_available())"

# 3. 如果確實只能用CPU，選擇最小模型
export BASE_MODEL="microsoft/DialoGPT-medium"
```

### 性能監控

#### 檢查記憶體使用

```bash
# 實時監控GPU記憶體
watch -n 1 nvidia-smi

# 通過API查看服務器記憶體狀態
curl http://localhost:8080/memory
```

#### 檢查服務狀態

```bash
# 健康檢查
curl http://localhost:8080/health

# 服務器狀態
curl http://localhost:8080/status

# 可用模型列表
curl http://localhost:8080/models
```

## 🧪 測試和驗證

### API測試

```bash
# 測試聊天API
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "請分析台積電股票的投資價值",
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

### 金融分析測試

```python
import requests

# 測試金融分析能力
response = requests.post("http://localhost:8080/chat", json={
    "message": "根據以下資料分析台積電(2330): 股價450元，本益比25倍，請給出投資建議",
    "max_tokens": 300,
    "temperature": 0.3
})

print(response.json())
```

## 📈 與TradingAgents集成

### 配置TradingAgents使用GPT-OSS

在 `TradingAgents/config.py` 中:

```python
# GPT-OSS配置
GPT_OSS_CONFIG = {
    'base_url': 'http://localhost:8080',
    'model': 'llama-3-8b',  # 或實際配置的模型
    'timeout': 30,
    'max_retries': 3
}
```

### 測試集成

```python
# 測試TradingAgents與GPT-OSS集成
python test_gpt_oss_integration.py
```

## 📚 進階配置

### LoRA適配器支援

如果有微調的LoRA適配器:

```bash
# 啟動時指定LoRA適配器
export LORA_ADAPTER="/path/to/your/lora/adapter"
./start_gpt_oss.sh
```

### 多GPU支援

對於多GPU環境 (如RTX 4070 + RTX 4070):

```yaml
model:
  device_map: "auto"  # 自動分配到多個GPU
  max_memory:
    0: "7GB"         # 第一個GPU
    1: "7GB"         # 第二個GPU
```

### 生產環境配置

```yaml
server:
  workers: 2                    # 增加工作進程
  max_concurrent_requests: 16   # 增加並發請求數

monitoring:
  enable_metrics: true          # 啟用Prometheus指標
  metrics_port: 9090           # 指標端口

security:
  require_api_key: true        # 啟用API密鑰驗證
  api_key_header: "Authorization"
```

## 🆘 支援和社群

- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **討論**: [GitHub Discussions](https://github.com/your-repo/discussions)  
- **文件**: [完整文件](./docs/)

## 📄 授權

本項目使用開源模型，無需特殊授權。具體模型授權請參考各模型的許可證。

---

## ⚡ 快速總結

1. **驗證環境**: `python validate_setup.py`
2. **設置模型**: `python setup_models.py` 
3. **啟動服務**: `start_gpt_oss.bat` (Windows) 或 `./start_gpt_oss.sh` (Linux)
4. **測試服務**: `curl http://localhost:8080/health`
5. **開始使用**: 🎉

針對RTX 4070 8GB，推薦使用 **Qwen/Qwen2-1.5B-Instruct** 模型，既有優秀的中文支援，又能很好地適配8GB VRAM限制。