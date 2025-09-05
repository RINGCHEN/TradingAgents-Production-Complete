@echo off
echo Setting up HuggingFace Token...
echo.
echo Please provide your HuggingFace token when prompted.
echo You can get it from: https://huggingface.co/settings/tokens
echo.

set /p HF_TOKEN="Enter your HuggingFace token: "

if "%HF_TOKEN%"=="" (
    echo No token provided. Exiting...
    pause
    exit /b 1
)

echo Setting environment variable...
set HUGGING_FACE_HUB_TOKEN=%HF_TOKEN%

echo Testing token...
python -c "import os; from huggingface_hub import login, whoami; login(token=os.environ.get('HUGGING_FACE_HUB_TOKEN')); user=whoami(); print(f'Login successful: {user[\"name\"]}')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Token setup successful!
    echo Now running LLaMA quick setup...
    python scripts\llama_quick_setup.py
) else (
    echo.
    echo Token setup failed. Please check your token and try again.
)

pause