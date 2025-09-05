@echo off
REM GPT-OSS 本地推理服務啟動腳本 (Windows)
REM 支援 RTX 4070/4090 自動配置

echo 🚀 啟動 GPT-OSS 本地推理服務...

REM 檢查 CUDA 可用性
where nvidia-smi >nul 2>nul
if %errorlevel% == 0 (
    echo ✅ 檢測到 NVIDIA GPU:
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits
    
    REM 檢查 VRAM 大小並調整模型
    for /f "tokens=2" %%i in ('nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits') do (
        if %%i LSS 10000 (
            echo 🎯 檢測到低 VRAM GPU (%%i MB)，使用輕量模型
            set BASE_MODEL=microsoft/DialoGPT-medium
            set MAX_MEMORY=%%i*0.8/1024GB
        )
    )
    set DEVICE=auto
) else (
    echo ⚠️  未檢測到 NVIDIA GPU，使用 CPU 模式
    set BASE_MODEL=microsoft/DialoGPT-medium
    set DEVICE=cpu
)

REM 設置默認環境變數 (RTX 4070 8GB 優化)
if not defined BASE_MODEL set BASE_MODEL=Qwen/Qwen2-1.5B-Instruct
if not defined LOAD_IN_4BIT set LOAD_IN_4BIT=true
if not defined HOST set HOST=0.0.0.0
if not defined PORT set PORT=8080
if not defined WORKERS set WORKERS=1
if not defined MAX_MEMORY set MAX_MEMORY=7GB

REM 檢查模型是否存在
if defined LORA_ADAPTER (
    if not exist "%LORA_ADAPTER%" (
        echo ❌ LoRA adapter 路徑不存在: %LORA_ADAPTER%
        exit /b 1
    )
)

REM 創建日誌目錄
if not exist logs mkdir logs

echo 📋 配置信息:
echo   - 基礎模型: %BASE_MODEL%
if defined LORA_ADAPTER (
    echo   - LoRA Adapter: %LORA_ADAPTER%
) else (
    echo   - LoRA Adapter: 無
)
echo   - 4-bit 量化: %LOAD_IN_4BIT%
echo   - 設備: %DEVICE%
echo   - 主機: %HOST%
echo   - 端口: %PORT%
echo   - 工作進程: %WORKERS%

REM 啟動服務
echo 🔥 啟動服務器...
python server.py --host %HOST% --port %PORT% --device %DEVICE% --workers %WORKERS% %BASE_MODEL_ARG% %LORA_ADAPTER_ARG% %LOAD_IN_4BIT_ARG%