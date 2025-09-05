@echo off
REM TradingAgents 監控系統啟動腳本 (Windows 版本)

echo 正在啟動 TradingAgents 監控系統...

REM 檢查 Docker 是否運行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo 錯誤: Docker 未運行，請先啟動 Docker
    pause
    exit /b 1
)

REM 檢查主應用是否運行
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% neq 0 (
    echo 警告: TradingAgents 主應用似乎未運行在 localhost:8000
    echo 監控將啟動，但某些指標可能不可用
)

REM 創建必要的目錄
echo 創建監控目錄結構...
if not exist prometheus\rules mkdir prometheus\rules
if not exist grafana\dashboards\json mkdir grafana\dashboards\json
if not exist grafana\datasources mkdir grafana\datasources
if not exist alertmanager mkdir alertmanager
if not exist loki mkdir loki
if not exist promtail mkdir promtail

REM 啟動監控堆疊
echo 啟動監控容器...
docker-compose -f docker-compose.monitoring.yml up -d

REM 等待服務啟動
echo 等待服務啟動...
timeout /t 30 /nobreak >nul

REM 檢查服務狀態
echo 檢查服務狀態...
set all_healthy=true

docker-compose -f docker-compose.monitoring.yml ps | findstr "prometheus.*Up" >nul
if %errorlevel% equ 0 (
    echo ✓ prometheus: 運行中
) else (
    echo ✗ prometheus: 未運行
    set all_healthy=false
)

docker-compose -f docker-compose.monitoring.yml ps | findstr "grafana.*Up" >nul
if %errorlevel% equ 0 (
    echo ✓ grafana: 運行中
) else (
    echo ✗ grafana: 未運行
    set all_healthy=false
)

docker-compose -f docker-compose.monitoring.yml ps | findstr "alertmanager.*Up" >nul
if %errorlevel% equ 0 (
    echo ✓ alertmanager: 運行中
) else (
    echo ✗ alertmanager: 未運行
    set all_healthy=false
)

docker-compose -f docker-compose.monitoring.yml ps | findstr "node-exporter.*Up" >nul
if %errorlevel% equ 0 (
    echo ✓ node-exporter: 運行中
) else (
    echo ✗ node-exporter: 未運行
    set all_healthy=false
)

docker-compose -f docker-compose.monitoring.yml ps | findstr "loki.*Up" >nul
if %errorlevel% equ 0 (
    echo ✓ loki: 運行中
) else (
    echo ✗ loki: 未運行
    set all_healthy=false
)

docker-compose -f docker-compose.monitoring.yml ps | findstr "promtail.*Up" >nul
if %errorlevel% equ 0 (
    echo ✓ promtail: 運行中
) else (
    echo ✗ promtail: 未運行
    set all_healthy=false
)

echo.
if "%all_healthy%"=="true" (
    echo [SUCCESS] 監控系統啟動成功！
    echo.
    echo 訪問連結:
    echo   - Grafana 儀表板: http://localhost:3000 (admin/admin123)
    echo   - Prometheus: http://localhost:9090
    echo   - AlertManager: http://localhost:9093
    echo   - cAdvisor: http://localhost:8080
    echo.
    echo 下一步:
    echo 1. 登入 Grafana 並導入儀表板
    echo 2. 配置告警通知接收者
    echo 3. 驗證指標收集是否正常
) else (
    echo [WARNING] 部分服務未正常啟動，請檢查日誌：
    echo docker-compose -f docker-compose.monitoring.yml logs
)

echo.
echo 常用命令:
echo   查看日誌: docker-compose -f docker-compose.monitoring.yml logs -f [service_name]
echo   停止監控: docker-compose -f docker-compose.monitoring.yml down
echo   重啟服務: docker-compose -f docker-compose.monitoring.yml restart [service_name]
echo.

pause