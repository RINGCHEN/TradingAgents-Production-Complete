@echo off
echo GPT-OSS 本地推理服務快速啟動
echo ================================
echo.

echo 檢查系統需求...
echo.

REM 檢查 Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未安裝或不可用
    echo 請先安裝 Docker Desktop
    pause
    exit /b 1
)
echo ✅ Docker 已安裝

REM 檢查 Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker Compose 未安裝或不可用
    pause
    exit /b 1
)
echo ✅ Docker Compose 已安裝

REM 檢查 NVIDIA Docker (可選)
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu20.04 nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  NVIDIA Docker 不可用，將使用 CPU 模式（性能較差）
) else (
    echo ✅ NVIDIA GPU 支援可用
)

echo.
echo 啟動 GPT-OSS 服務...
echo.

REM 切換到 TradingAgents 目錄
cd TradingAgents

REM 創建必要的目錄
if not exist "logs\gpt_oss" mkdir logs\gpt_oss
if not exist "gpt_oss\models" mkdir gpt_oss\models
if not exist "gpt_oss\cache" mkdir gpt_oss\cache

echo 構建並啟動服務（首次運行可能需要 20-30 分鐘下載模型）...
docker-compose up --build -d gpt-oss

echo.
echo 等待服務啟動...
timeout /t 30 /nobreak > nul

echo.
echo 檢查服務狀態...
docker-compose ps

echo.
echo ====================================
echo GPT-OSS 服務啟動完成！
echo ====================================
echo.
echo 服務端點:
echo - GPT-OSS API: http://localhost:8080
echo - 健康檢查:   http://localhost:8080/health
echo - 監控指標:   http://localhost:9091/metrics
echo.
echo 測試服務:
echo curl http://localhost:8080/health
echo.
echo 運行整合測試:
echo python test_gpt_oss_integration.py
echo.
echo 查看日誌:
echo docker logs -f tradingagents-gpt-oss
echo.
echo 停止服務:
echo docker-compose down
echo ====================================

pause