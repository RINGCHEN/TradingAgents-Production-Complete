#!/bin/bash

# GPT-OSS 本地推理服務快速啟動腳本
# 適用於 Linux/macOS 系統

set -e

echo "GPT-OSS 本地推理服務快速啟動"
echo "================================"
echo ""

echo "檢查系統需求..."
echo ""

# 檢查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝"
    echo "請先安裝 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✅ Docker 已安裝: $(docker --version)"

# 檢查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝"
    echo "請先安裝 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi
echo "✅ Docker Compose 已安裝: $(docker-compose --version)"

# 檢查 NVIDIA Docker (可選)
if docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu20.04 nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU 支援可用"
    GPU_AVAILABLE=true
else
    echo "⚠️  NVIDIA Docker 不可用，將使用 CPU 模式（性能較差）"
    echo "   如需 GPU 加速，請安裝 nvidia-docker2"
    GPU_AVAILABLE=false
fi

echo ""
echo "啟動 GPT-OSS 服務..."
echo ""

# 切換到 TradingAgents 目錄
cd TradingAgents

# 創建必要的目錄
mkdir -p logs/gpt_oss
mkdir -p gpt_oss/models
mkdir -p gpt_oss/cache

# 設置環境變量
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

echo "構建並啟動服務（首次運行可能需要 20-30 分鐘下載模型）..."

if [ "$GPU_AVAILABLE" = true ]; then
    echo "使用 GPU 加速模式"
    docker-compose up --build -d gpt-oss
else
    echo "使用 CPU 模式（性能有限）"
    # 可以在這裡添加 CPU 特定的配置
    docker-compose up --build -d gpt-oss
fi

echo ""
echo "等待服務啟動..."
sleep 30

echo ""
echo "檢查服務狀態..."
docker-compose ps

# 健康檢查
echo ""
echo "執行健康檢查..."
for i in {1..10}; do
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ GPT-OSS 服務健康檢查通過"
        break
    else
        echo "等待服務啟動... ($i/10)"
        sleep 10
    fi
    
    if [ $i -eq 10 ]; then
        echo "⚠️  服務可能還在啟動中，請稍後手動檢查"
    fi
done

echo ""
echo "===================================="
echo "GPT-OSS 服務啟動完成！"
echo "===================================="
echo ""
echo "服務端點:"
echo "- GPT-OSS API: http://localhost:8080"
echo "- 健康檢查:   http://localhost:8080/health"
echo "- 監控指標:   http://localhost:9091/metrics"
echo ""
echo "測試命令:"
echo "curl http://localhost:8080/health"
echo ""
echo "運行整合測試:"
echo "python test_gpt_oss_integration.py"
echo ""
echo "查看日誌:"
echo "docker logs -f tradingagents-gpt-oss"
echo ""
echo "停止服務:"
echo "docker-compose down"
echo "===================================="

# 提示下一步操作
echo ""
echo "建議的下一步操作:"
echo "1. 運行健康檢查: curl http://localhost:8080/health"
echo "2. 執行整合測試: python test_gpt_oss_integration.py"
echo "3. 查看監控界面: http://localhost:3000 (Grafana)"
echo "4. 配置智能路由器進行成本優化"