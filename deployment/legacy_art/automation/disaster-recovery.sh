#!/bin/bash

# ART系統災難恢復和自動化腳本
# DevOps Engineer 墨子 - 完整的災難恢復解決方案

set -euo pipefail

# 配置變數
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/disaster-recovery.log"
BACKUP_DIR="${SCRIPT_DIR}/backups"
DATE=$(date +"%Y%m%d_%H%M%S")

# 日誌函數
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$LOG_FILE" >&2
}

# 檢查必要工具
check_prerequisites() {
    log "檢查必要工具和權限..."
    
    local tools=("docker" "docker-compose" "kubectl" "gcloud" "gsutil" "pg_dump" "redis-cli")
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            error "缺少必要工具: $tool"
            exit 1
        fi
    done
    
    # 檢查Docker是否運行
    if ! docker info &> /dev/null; then
        error "Docker服務未運行"
        exit 1
    fi
    
    # 檢查GCP認證
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        error "未找到活動的GCP認證"
        exit 1
    fi
    
    log "✅ 先決條件檢查完成"
}

# 創建備份目錄
create_backup_dirs() {
    log "創建備份目錄結構..."
    
    mkdir -p "${BACKUP_DIR}/${DATE}"/{models,data,configs,logs}
    
    log "✅ 備份目錄創建完成: ${BACKUP_DIR}/${DATE}"
}

# 備份本地模型和數據
backup_local_data() {
    log "開始備份本地數據..."
    
    # 備份模型
    if [ -d "./models" ]; then
        log "備份本地模型..."
        tar -czf "${BACKUP_DIR}/${DATE}/models/local_models_${DATE}.tar.gz" -C . models/
    fi
    
    # 備份數據集
    if [ -d "./datasets" ]; then
        log "備份數據集..."
        tar -czf "${BACKUP_DIR}/${DATE}/data/datasets_${DATE}.tar.gz" -C . datasets/
    fi
    
    # 備份配置文件
    log "備份配置文件..."
    tar -czf "${BACKUP_DIR}/${DATE}/configs/configs_${DATE}.tar.gz" \
        docker-compose.yml \
        deployment/ \
        monitoring/ \
        --exclude='deployment/backups' \
        --exclude='*.log' 2>/dev/null || true
    
    # 備份日誌
    if [ -d "./logs" ]; then
        log "備份日誌文件..."
        tar -czf "${BACKUP_DIR}/${DATE}/logs/logs_${DATE}.tar.gz" -C . logs/
    fi
    
    log "✅ 本地數據備份完成"
}

# 備份數據庫
backup_databases() {
    log "開始備份數據庫..."
    
    # 備份PostgreSQL (MLFlow)
    if docker ps --format "table {{.Names}}" | grep -q postgres-mlflow; then
        log "備份MLFlow PostgreSQL數據庫..."
        docker exec art-postgres-mlflow pg_dump -U mlflow mlflow | \
            gzip > "${BACKUP_DIR}/${DATE}/data/mlflow_db_${DATE}.sql.gz"
    fi
    
    # 備份Redis數據
    if docker ps --format "table {{.Names}}" | grep -q redis-training; then
        log "備份Redis數據..."
        docker exec art-redis-training redis-cli --rdb - | \
            gzip > "${BACKUP_DIR}/${DATE}/data/redis_${DATE}.rdb.gz"
    fi
    
    log "✅ 數據庫備份完成"
}

# 上傳備份到雲端
upload_to_cloud() {
    log "上傳備份到Google Cloud Storage..."
    
    local project_id=$(gcloud config get-value project)
    local bucket_name="${project_id}-art-disaster-recovery"
    
    # 創建備份桶（如果不存在）
    if ! gsutil ls "gs://${bucket_name}" &>/dev/null; then
        log "創建災難恢復存儲桶..."
        gsutil mb -p "$project_id" -c STANDARD -l asia-east1 "gs://${bucket_name}"
        
        # 設置生命週期政策
        cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
        gsutil lifecycle set lifecycle.json "gs://${bucket_name}"
        rm lifecycle.json
    fi
    
    # 上傳備份
    log "上傳備份文件到雲端..."
    gsutil -m cp -r "${BACKUP_DIR}/${DATE}" "gs://${bucket_name}/backups/"
    
    log "✅ 雲端備份完成"
}

# 健康檢查
health_check() {
    log "執行系統健康檢查..."
    
    local failed_services=()
    
    # 檢查Docker容器
    local containers=("art-gpu-trainer" "art-mlflow-server" "art-redis-training" "art-jupyter-lab")
    
    for container in "${containers[@]}"; do
        if ! docker ps --format "table {{.Names}}" | grep -q "$container"; then
            failed_services+=("Docker容器: $container")
        else
            if [ "$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null)" = "unhealthy" ]; then
                failed_services+=("不健康的容器: $container")
            fi
        fi
    done
    
    # 檢查GPU可用性
    if command -v nvidia-smi &> /dev/null; then
        if ! nvidia-smi &>/dev/null; then
            failed_services+=("NVIDIA GPU驅動程序")
        fi
    fi
    
    # 檢查磁碟空間
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 85 ]; then
        failed_services+=("磁碟空間不足: ${disk_usage}%")
    fi
    
    # 檢查記憶體使用
    local mem_usage=$(free | awk 'NR==2 {printf "%.0f", $3*100/$2}')
    if [ "$mem_usage" -gt 90 ]; then
        failed_services+=("記憶體使用過高: ${mem_usage}%")
    fi
    
    # 報告結果
    if [ ${#failed_services[@]} -eq 0 ]; then
        log "✅ 所有系統健康檢查通過"
        return 0
    else
        error "❌ 檢測到系統問題:"
        for service in "${failed_services[@]}"; do
            error "  - $service"
        done
        return 1
    fi
}

# 自動修復
auto_heal() {
    log "嘗試自動修復系統問題..."
    
    # 重啟不健康的容器
    local unhealthy_containers=$(docker ps --filter "health=unhealthy" --format "{{.Names}}")
    
    if [ -n "$unhealthy_containers" ]; then
        log "重啟不健康的容器..."
        echo "$unhealthy_containers" | while read container; do
            log "重啟容器: $container"
            docker restart "$container"
        done
    fi
    
    # 清理系統資源
    log "清理Docker系統資源..."
    docker system prune -f
    
    # 清理臨時文件
    log "清理臨時文件..."
    find /tmp -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
    
    log "✅ 自動修復完成"
}

# 災難恢復
disaster_recovery() {
    log "開始災難恢復程序..."
    
    # 停止所有服務
    log "停止所有ART服務..."
    docker-compose -f deployment/art-gpu-training-environment.yml down || true
    docker-compose -f deployment/monitoring/art-monitoring-stack.yml down || true
    
    # 從最新備份恢復
    log "尋找最新的備份..."
    local latest_backup=$(gsutil ls "gs://${project_id}-art-disaster-recovery/backups/" | \
                         sort -r | head -1 | sed 's|.*/||')
    
    if [ -n "$latest_backup" ]; then
        log "從備份恢復: $latest_backup"
        
        # 下載備份
        gsutil -m cp -r "gs://${project_id}-art-disaster-recovery/backups/${latest_backup}" \
               "${BACKUP_DIR}/recovery/"
        
        # 恢復數據
        if [ -f "${BACKUP_DIR}/recovery/${latest_backup}/data/mlflow_db_${latest_backup}.sql.gz" ]; then
            log "恢復MLFlow數據庫..."
            # 先啟動數據庫容器
            docker-compose -f deployment/art-gpu-training-environment.yml up -d postgres-mlflow
            sleep 30
            
            # 恢復數據
            gunzip -c "${BACKUP_DIR}/recovery/${latest_backup}/data/mlflow_db_${latest_backup}.sql.gz" | \
                docker exec -i art-postgres-mlflow psql -U mlflow -d mlflow
        fi
        
        # 恢復Redis數據
        if [ -f "${BACKUP_DIR}/recovery/${latest_backup}/data/redis_${latest_backup}.rdb.gz" ]; then
            log "恢復Redis數據..."
            docker-compose -f deployment/art-gpu-training-environment.yml up -d redis-training
            sleep 10
            
            gunzip -c "${BACKUP_DIR}/recovery/${latest_backup}/data/redis_${latest_backup}.rdb.gz" | \
                docker exec -i art-redis-training redis-cli --pipe
        fi
        
        # 恢復模型和配置
        if [ -f "${BACKUP_DIR}/recovery/${latest_backup}/models/local_models_${latest_backup}.tar.gz" ]; then
            log "恢復模型文件..."
            tar -xzf "${BACKUP_DIR}/recovery/${latest_backup}/models/local_models_${latest_backup}.tar.gz"
        fi
        
        log "✅ 災難恢復完成"
    else
        error "未找到可用的備份"
        return 1
    fi
}

# Prometheus告警整合
setup_prometheus_alerts() {
    log "設置Prometheus告警規則..."
    
    cat > "${SCRIPT_DIR}/../monitoring/prometheus/alert-rules/art-disaster-recovery.yml" << 'EOF'
groups:
  - name: art-disaster-recovery
    rules:
      - alert: GPUTrainingDown
        expr: up{job="art-gpu-trainer"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "ART GPU訓練服務不可用"
          description: "GPU訓練服務已離線超過5分鐘"
          
      - alert: HighDiskUsage
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 15
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "磁碟空間不足"
          description: "可用磁碟空間低於15%"
          
      - alert: HighMemoryUsage
        expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 < 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "記憶體使用過高"
          description: "可用記憶體低於10%"
          
      - alert: GPUTemperatureHigh
        expr: nvidia_gpu_temperature_celsius > 85
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "GPU溫度過高"
          description: "GPU溫度超過85°C"
EOF
    
    log "✅ Prometheus告警規則設置完成"
}

# 主函數
main() {
    local command="${1:-health_check}"
    
    log "====== ART災難恢復系統啟動 ======"
    log "命令: $command"
    
    check_prerequisites
    
    case "$command" in
        "backup")
            create_backup_dirs
            backup_local_data
            backup_databases
            upload_to_cloud
            ;;
        "health_check")
            if ! health_check; then
                log "健康檢查失敗，嘗試自動修復..."
                auto_heal
                sleep 30
                health_check
            fi
            ;;
        "auto_heal")
            auto_heal
            ;;
        "disaster_recovery")
            disaster_recovery
            ;;
        "setup_alerts")
            setup_prometheus_alerts
            ;;
        "full_backup")
            create_backup_dirs
            backup_local_data
            backup_databases
            upload_to_cloud
            health_check
            ;;
        *)
            echo "使用方法: $0 {backup|health_check|auto_heal|disaster_recovery|setup_alerts|full_backup}"
            exit 1
            ;;
    esac
    
    log "====== 操作完成 ======"
}

# 捕獲信號並清理
cleanup() {
    log "接收到終止信號，正在清理..."
    exit 0
}

trap cleanup SIGINT SIGTERM

# 執行主函數
main "$@"