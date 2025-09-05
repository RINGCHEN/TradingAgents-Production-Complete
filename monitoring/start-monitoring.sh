#!/bin/bash

# TradingAgents 監控系統啟動腳本
# 此腳本用於啟動完整的監控堆疊

echo "正在啟動 TradingAgents 監控系統..."

# 檢查 Docker 是否運行
if ! docker info > /dev/null 2>&1; then
    echo "錯誤: Docker 未運行，請先啟動 Docker"
    exit 1
fi

# 檢查主應用是否運行
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "警告: TradingAgents 主應用似乎未運行在 localhost:8000"
    echo "監控將啟動，但某些指標可能不可用"
fi

# 創建必要的目錄
echo "創建監控目錄結構..."
mkdir -p ./prometheus/rules
mkdir -p ./grafana/dashboards/json
mkdir -p ./grafana/datasources
mkdir -p ./alertmanager
mkdir -p ./loki
mkdir -p ./promtail

# 設置檔案權限
echo "設置檔案權限..."
chmod -R 755 ./prometheus
chmod -R 755 ./grafana
chmod -R 755 ./alertmanager
chmod -R 755 ./loki
chmod -R 755 ./promtail

# 啟動監控堆疊
echo "啟動監控容器..."
docker-compose -f docker-compose.monitoring.yml up -d

# 等待服務啟動
echo "等待服務啟動..."
sleep 30

# 檢查服務狀態
echo "檢查服務狀態..."
services=("prometheus" "grafana" "alertmanager" "node-exporter" "loki" "promtail")

all_healthy=true
for service in "${services[@]}"; do
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "$service.*Up"; then
        echo "✓ $service: 運行中"
    else
        echo "✗ $service: 未運行"
        all_healthy=false
    fi
done

if $all_healthy; then
    echo ""
    echo "🎉 監控系統啟動成功！"
    echo ""
    echo "訪問連結:"
    echo "  - Grafana 儀表板: http://localhost:3000 (admin/admin123)"
    echo "  - Prometheus: http://localhost:9090"
    echo "  - AlertManager: http://localhost:9093"
    echo "  - cAdvisor: http://localhost:8080"
    echo ""
    echo "下一步:"
    echo "1. 登入 Grafana 並導入儀表板"
    echo "2. 配置告警通知接收者"
    echo "3. 驗證指標收集是否正常"
else
    echo ""
    echo "⚠️ 部分服務未正常啟動，請檢查日誌："
    echo "docker-compose -f docker-compose.monitoring.yml logs"
fi

# 顯示有用的命令
echo ""
echo "常用命令:"
echo "  查看日誌: docker-compose -f docker-compose.monitoring.yml logs -f [service_name]"
echo "  停止監控: docker-compose -f docker-compose.monitoring.yml down"
echo "  重啟服務: docker-compose -f docker-compose.monitoring.yml restart [service_name]"