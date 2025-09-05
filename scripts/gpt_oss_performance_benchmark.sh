#!/bin/bash
# GPT-OSS 性能基準測試腳本
# 用於測試Docker容器的啟動時間、推理性能和資源使用情況

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
CONTAINER_NAME="gpt-oss-benchmark"
IMAGE_NAME="tradingagents:gpt-oss"
PORT="8080"
TEST_RESULTS_DIR="./benchmark_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="${TEST_RESULTS_DIR}/benchmark_${TIMESTAMP}.json"

# 創建結果目錄
mkdir -p "$TEST_RESULTS_DIR"

echo -e "${BLUE}=== GPT-OSS 性能基準測試 ===${NC}"
echo "測試時間: $(date)"
echo "映像名稱: $IMAGE_NAME"
echo "結果文件: $RESULTS_FILE"
echo ""

# 初始化結果JSON
cat > "$RESULTS_FILE" << EOF
{
  "test_timestamp": "$(date -Iseconds)",
  "image_name": "$IMAGE_NAME",
  "tests": {}
}
EOF

# 清理函數
cleanup() {
    echo -e "${YELLOW}清理測試環境...${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# 設置清理陷阱
trap cleanup EXIT

# 測試1: 容器啟動時間
echo -e "${BLUE}測試1: 容器啟動時間${NC}"
start_time=$(date +%s.%N)

docker run -d --name "$CONTAINER_NAME" --gpus all -p "$PORT:$PORT" "$IMAGE_NAME" > /dev/null

# 等待服務就緒
echo "等待服務啟動..."
max_wait=120  # 最大等待2分鐘
wait_count=0

while ! curl -f "http://localhost:$PORT/health" > /dev/null 2>&1; do
    sleep 1
    wait_count=$((wait_count + 1))
    if [ $wait_count -ge $max_wait ]; then
        echo -e "${RED}錯誤: 服務啟動超時${NC}"
        exit 1
    fi
    if [ $((wait_count % 10)) -eq 0 ]; then
        echo "等待中... ${wait_count}s"
    fi
done

end_time=$(date +%s.%N)
startup_time=$(echo "$end_time - $start_time" | bc)

echo -e "${GREEN}✓ 容器啟動時間: ${startup_time}秒${NC}"

# 更新結果文件
jq --arg startup_time "$startup_time" '.tests.startup_time = ($startup_time | tonumber)' "$RESULTS_FILE" > tmp.$$.json && mv tmp.$$.json "$RESULTS_FILE"

# 測試2: 健康檢查響應時間
echo -e "${BLUE}測試2: 健康檢查響應時間${NC}"

health_times=()
for i in {1..5}; do
    start_time=$(date +%s.%N)
    curl -f "http://localhost:$PORT/health" > /dev/null 2>&1
    end_time=$(date +%s.%N)
    response_time=$(echo "$end_time - $start_time" | bc)
    health_times+=("$response_time")
    echo "健康檢查 $i: ${response_time}秒"
done

# 計算平均響應時間
avg_health_time=$(printf '%s\n' "${health_times[@]}" | awk '{sum+=$1} END {print sum/NR}')
echo -e "${GREEN}✓ 平均健康檢查響應時間: ${avg_health_time}秒${NC}"

# 更新結果文件
jq --arg avg_health_time "$avg_health_time" '.tests.avg_health_response_time = ($avg_health_time | tonumber)' "$RESULTS_FILE" > tmp.$$.json && mv tmp.$$.json "$RESULTS_FILE"

# 測試3: GPU檢測和記憶體狀態
echo -e "${BLUE}測試3: GPU檢測和記憶體狀態${NC}"

gpu_info=$(curl -s "http://localhost:$PORT/health" | jq -r '.cuda_available, .memory_info')
echo "GPU可用性: $(echo "$gpu_info" | head -1)"

# 獲取詳細的記憶體信息
memory_status=$(curl -s "http://localhost:$PORT/memory")
echo "記憶體狀態: $memory_status"

# 更新結果文件
jq --argjson memory_status "$memory_status" '.tests.memory_status = $memory_status' "$RESULTS_FILE" > tmp.$$.json && mv tmp.$$.json "$RESULTS_FILE"

# 測試4: 推理性能測試
echo -e "${BLUE}測試4: 推理性能測試${NC}"

# 測試不同長度的推理請求
test_messages=(
    "簡單測試"
    "分析AAPL股票的技術面和基本面，提供投資建議"
    "請詳細分析當前市場情緒，包括VIX指數、投資者信心指數、資金流向等關鍵指標，並預測未來一週的市場走勢"
)

inference_times=()
for i in "${!test_messages[@]}"; do
    message="${test_messages[$i]}"
    echo "推理測試 $((i+1)): ${#message} 字符"
    
    start_time=$(date +%s.%N)
    response=$(curl -s -X POST "http://localhost:$PORT/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\", \"max_tokens\": 100}")
    end_time=$(date +%s.%N)
    
    inference_time=$(echo "$end_time - $start_time" | bc)
    inference_times+=("$inference_time")
    
    # 檢查響應是否成功
    if echo "$response" | jq -e '.response' > /dev/null 2>&1; then
        tokens_used=$(echo "$response" | jq -r '.tokens_used // "N/A"')
        echo -e "${GREEN}✓ 推理時間: ${inference_time}秒, 使用tokens: $tokens_used${NC}"
    else
        echo -e "${RED}✗ 推理失敗: $response${NC}"
    fi
done

# 計算平均推理時間
avg_inference_time=$(printf '%s\n' "${inference_times[@]}" | awk '{sum+=$1} END {print sum/NR}')
echo -e "${GREEN}✓ 平均推理時間: ${avg_inference_time}秒${NC}"

# 更新結果文件
jq --arg avg_inference_time "$avg_inference_time" '.tests.avg_inference_time = ($avg_inference_time | tonumber)' "$RESULTS_FILE" > tmp.$$.json && mv tmp.$$.json "$RESULTS_FILE"

# 測試5: 並發性能測試
echo -e "${BLUE}測試5: 並發性能測試${NC}"

concurrent_requests=3
echo "執行 $concurrent_requests 個並發請求..."

pids=()
concurrent_times=()

for i in $(seq 1 $concurrent_requests); do
    (
        start_time=$(date +%s.%N)
        curl -s -X POST "http://localhost:$PORT/chat" \
            -H "Content-Type: application/json" \
            -d '{"message": "並發測試請求", "max_tokens": 50}' > /dev/null
        end_time=$(date +%s.%N)
        echo $(echo "$end_time - $start_time" | bc)
    ) &
    pids+=($!)
done

# 等待所有並發請求完成
for pid in "${pids[@]}"; do
    wait $pid
done

echo -e "${GREEN}✓ 並發測試完成${NC}"

# 測試6: 資源使用情況
echo -e "${BLUE}測試6: 資源使用情況${NC}"

# 獲取容器資源使用統計
container_stats=$(docker stats "$CONTAINER_NAME" --no-stream --format "table {{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}")
echo "容器資源使用:"
echo "$container_stats"

# 獲取GPU使用情況
if command -v nvidia-smi &> /dev/null; then
    echo "GPU使用情況:"
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader,nounits
fi

# 測試7: 壓力測試
echo -e "${BLUE}測試7: 壓力測試 (10個快速請求)${NC}"

stress_start_time=$(date +%s.%N)
stress_success=0
stress_total=10

for i in $(seq 1 $stress_total); do
    if curl -s -X POST "http://localhost:$PORT/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "壓力測試", "max_tokens": 20}' | jq -e '.response' > /dev/null 2>&1; then
        stress_success=$((stress_success + 1))
    fi
done

stress_end_time=$(date +%s.%N)
stress_duration=$(echo "$stress_end_time - $stress_start_time" | bc)
success_rate=$(echo "scale=2; $stress_success * 100 / $stress_total" | bc)

echo -e "${GREEN}✓ 壓力測試完成: $stress_success/$stress_total 成功 (${success_rate}%), 總時間: ${stress_duration}秒${NC}"

# 更新結果文件
jq --arg stress_success_rate "$success_rate" --arg stress_duration "$stress_duration" \
   '.tests.stress_test = {success_rate: ($stress_success_rate | tonumber), duration: ($stress_duration | tonumber)}' \
   "$RESULTS_FILE" > tmp.$$.json && mv tmp.$$.json "$RESULTS_FILE"

# 生成測試報告
echo -e "${BLUE}=== 測試報告 ===${NC}"
echo "啟動時間: ${startup_time}秒"
echo "平均健康檢查響應時間: ${avg_health_time}秒"
echo "平均推理時間: ${avg_inference_time}秒"
echo "壓力測試成功率: ${success_rate}%"
echo ""

# 性能評估
echo -e "${BLUE}=== 性能評估 ===${NC}"

# 啟動時間評估
if (( $(echo "$startup_time < 60" | bc -l) )); then
    echo -e "${GREEN}✓ 啟動時間: 優秀 (<60秒)${NC}"
elif (( $(echo "$startup_time < 120" | bc -l) )); then
    echo -e "${YELLOW}⚠ 啟動時間: 良好 (<120秒)${NC}"
else
    echo -e "${RED}✗ 啟動時間: 需要優化 (>120秒)${NC}"
fi

# 響應時間評估
if (( $(echo "$avg_health_time < 0.5" | bc -l) )); then
    echo -e "${GREEN}✓ 響應時間: 優秀 (<0.5秒)${NC}"
elif (( $(echo "$avg_health_time < 1.0" | bc -l) )); then
    echo -e "${YELLOW}⚠ 響應時間: 良好 (<1秒)${NC}"
else
    echo -e "${RED}✗ 響應時間: 需要優化 (>1秒)${NC}"
fi

# 推理性能評估
if (( $(echo "$avg_inference_time < 2.0" | bc -l) )); then
    echo -e "${GREEN}✓ 推理性能: 優秀 (<2秒)${NC}"
elif (( $(echo "$avg_inference_time < 5.0" | bc -l) )); then
    echo -e "${YELLOW}⚠ 推理性能: 良好 (<5秒)${NC}"
else
    echo -e "${RED}✗ 推理性能: 需要優化 (>5秒)${NC}"
fi

# 壓力測試評估
if (( $(echo "$success_rate >= 95" | bc -l) )); then
    echo -e "${GREEN}✓ 穩定性: 優秀 (≥95%)${NC}"
elif (( $(echo "$success_rate >= 90" | bc -l) )); then
    echo -e "${YELLOW}⚠ 穩定性: 良好 (≥90%)${NC}"
else
    echo -e "${RED}✗ 穩定性: 需要優化 (<90%)${NC}"
fi

echo ""
echo -e "${GREEN}測試完成！結果已保存到: $RESULTS_FILE${NC}"

# 生成HTML報告
HTML_REPORT="${TEST_RESULTS_DIR}/benchmark_${TIMESTAMP}.html"
cat > "$HTML_REPORT" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>GPT-OSS 性能基準測試報告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f0f0f0; padding: 20px; border-radius: 5px; }
        .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007cba; }
        .good { border-left-color: #28a745; }
        .warning { border-left-color: #ffc107; }
        .error { border-left-color: #dc3545; }
        table { border-collapse: collapse; width: 100%; margin: 20px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <div class="header">
        <h1>GPT-OSS 性能基準測試報告</h1>
        <p>測試時間: $(date)</p>
        <p>映像名稱: $IMAGE_NAME</p>
    </div>
    
    <h2>測試結果</h2>
    <table>
        <tr><th>測試項目</th><th>結果</th><th>評估</th></tr>
        <tr><td>容器啟動時間</td><td>${startup_time}秒</td><td>$([ $(echo "$startup_time < 60" | bc -l) -eq 1 ] && echo "優秀" || echo "需要優化")</td></tr>
        <tr><td>平均健康檢查響應時間</td><td>${avg_health_time}秒</td><td>$([ $(echo "$avg_health_time < 0.5" | bc -l) -eq 1 ] && echo "優秀" || echo "良好")</td></tr>
        <tr><td>平均推理時間</td><td>${avg_inference_time}秒</td><td>$([ $(echo "$avg_inference_time < 2.0" | bc -l) -eq 1 ] && echo "優秀" || echo "良好")</td></tr>
        <tr><td>壓力測試成功率</td><td>${success_rate}%</td><td>$([ $(echo "$success_rate >= 95" | bc -l) -eq 1 ] && echo "優秀" || echo "良好")</td></tr>
    </table>
    
    <h2>詳細數據</h2>
    <pre>$(cat "$RESULTS_FILE" | jq .)</pre>
</body>
</html>
EOF

echo -e "${GREEN}HTML報告已生成: $HTML_REPORT${NC}"