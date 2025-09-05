@echo off
REM Node.js環境自動設置腳本
REM 天工(TianGong) - 為小k和小c團隊生成
REM 生成時間: 2025-08-14 09:30:00

echo ========================================
echo TradingAgents Node.js環境設置
echo ========================================

REM 檢查Node.js
echo 檢查Node.js安裝狀態...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js未安裝
    echo 請從以下網址下載並安裝Node.js 18+ LTS版本:
    echo https://nodejs.org/
    pause
    exit /b 1
) else (
    echo [OK] Node.js已安裝
    node --version
)

REM 檢查npm
echo 檢查npm可用性...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm不可用
    pause
    exit /b 1
) else (
    echo [OK] npm可用
    npm --version
)

REM 進入前端目錄
cd /d "C:\Users\Ring\Documents\GitHub\twstock\TradingAgents\frontend"
if %errorlevel% neq 0 (
    echo [ERROR] 前端目錄不存在
    pause
    exit /b 1
)

REM 安裝依賴
echo 安裝前端依賴...
if not exist "node_modules" (
    echo 執行npm install...
    npm install
    if %errorlevel% neq 0 (
        echo [ERROR] npm install失敗
        pause
        exit /b 1
    )
) else (
    echo [SKIP] node_modules已存在
)

REM 執行測試
echo 執行TypeScript類型檢查...
npx tsc --noEmit
if %errorlevel% neq 0 (
    echo [WARN] TypeScript檢查有問題
) else (
    echo [OK] TypeScript檢查通過
)

echo ========================================
echo Node.js環境設置完成
echo ========================================
pause