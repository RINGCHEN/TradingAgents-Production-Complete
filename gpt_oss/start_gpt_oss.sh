#!/bin/bash
# GPT-OSS 本地推理服務啟動腳本
# 支援 RTX 4070/4090 自動配置

set -e

echo "🚀 啟動 GPT-OSS 本地推理服務..."

# 檢查 CUDA 可用性
if command -v nvidia-smi &> /dev/null; then
    echo "✅ 檢測到 NVIDIA GPU:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    export DEVICE="auto"
else
    echo "⚠️  未檢測到 NVIDIA GPU，使用 CPU 模式"
    export DEVICE="cpu"
fi

# 設置默認環境變數 (RTX 4070 8GB 優化)
export BASE_MODEL=${BASE_MODEL:-"Qwen/Qwen2-1.5B-Instruct"}
export LOAD_IN_4BIT=${LOAD_IN_4BIT:-"true"}
export HOST=${HOST:-"0.0.0.0"}
export PORT=${PORT:-"8080"}
export WORKERS=${WORKERS:-"1"}

# 檢查 VRAM 大小並調整模型 (Linux)
if command -v nvidia-smi &> /dev/null; then
    VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
    if [ "$VRAM_MB" -lt 10000 ]; then
        echo "🎯 檢測到低 VRAM GPU ($VRAM_MB MB)，使用輕量模型"
        export BASE_MODEL="microsoft/DialoGPT-medium"
    fi
fi

# 檢查模型是否存在
if [ ! -z "$LORA_ADAPTER" ] && [ ! -d "$LORA_ADAPTER" ]; then
    echo "❌ LoRA adapter 路徑不存在: $LORA_ADAPTER"
    exit 1
fi

# 創建日誌目錄
mkdir -p logs

echo "📋 配置信息:"
echo "  - 基礎模型: $BASE_MODEL"
echo "  - LoRA Adapter: ${LORA_ADAPTER:-"無"}"
echo "  - 4-bit 量化: $LOAD_IN_4BIT"
echo "  - 設備: $DEVICE"
echo "  - 主機: $HOST"
echo "  - 端口: $PORT"
echo "  - 工作進程: $WORKERS"

# 啟動服務
echo "🔥 啟動服務器..."
python3 server.py \
    --host "$HOST" \
    --port "$PORT" \
    --device "$DEVICE" \
    --workers "$WORKERS" \
    ${BASE_MODEL:+--base-model "$BASE_MODEL"} \
    ${LORA_ADAPTER:+--lora-adapter "$LORA_ADAPTER"} \
    ${LOAD_IN_4BIT:+--load-in-4bit} \
    2>&1 | tee logs/gpt_oss_$(date +%Y%m%d_%H%M%S).log