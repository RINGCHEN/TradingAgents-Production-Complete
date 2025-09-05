#!/usr/bin/env python3
"""
CORS 修復部署腳本
直接從源代碼部署到 Google Cloud Run，修復 CORS 問題
"""

import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None):
    """執行命令並返回結果"""
    print(f"執行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"錯誤: {result.stderr}")
        return False, result.stderr
    print(f"成功: {result.stdout}")
    return True, result.stdout

def main():
    print("🚀 開始 CORS 修復部署...")
    
    # 定位到 TradingAgents 目錄
    current_dir = Path.cwd()
    trading_agents_dir = current_dir / "TradingAgents"
    
    if not trading_agents_dir.exists():
        print(f"❌ 找不到 TradingAgents 目錄: {trading_agents_dir}")
        return False
    
    print(f"📁 工作目錄: {trading_agents_dir}")
    
    # 清理可能有問題的文件
    exclude_patterns = [
        "*.log", "*.db", "__pycache__", ".cache", ".pytest_cache",
        "models", "cache", "*.safetensors", "*.bin", "*.model",
        "test_*", "tests", "logs", "node_modules"
    ]
    
    print("🧹 清理問題文件...")
    for pattern in exclude_patterns:
        cmd = f'find . -name "{pattern}" -type d -exec rm -rf {{}} + 2>/dev/null || true'
        run_command(cmd, cwd=trading_agents_dir)
        cmd = f'find . -name "{pattern}" -type f -delete 2>/dev/null || true'
        run_command(cmd, cwd=trading_agents_dir)
    
    # 使用 gcloud run deploy 直接部署
    print("☁️ 開始部署到 Google Cloud Run...")
    
    env_vars = [
        "ENVIRONMENT=production",
        "CORS_FIX=enabled",
        "FORCE_PRODUCTION_CORS=true"
    ]
    
    deploy_cmd = f"""gcloud run deploy tradingagents \\
        --source . \\
        --region=asia-east1 \\
        --allow-unauthenticated \\
        --memory=2Gi \\
        --cpu=1 \\
        --timeout=300 \\
        --max-instances=2 \\
        --set-env-vars {','.join(env_vars)}"""
    
    success, output = run_command(deploy_cmd, cwd=trading_agents_dir)
    
    if success:
        print("✅ 部署成功！")
        print("🔍 驗證 CORS 設置...")
        
        # 測試 CORS 
        test_cmd = 'curl -v -H "Origin: https://admin.03king.com" https://tradingagents-351731559902.asia-east1.run.app/health'
        success, output = run_command(test_cmd)
        
        if "access-control-allow-origin: https://admin.03king.com" in output.lower():
            print("✅ CORS 修復成功！")
            return True
        else:
            print("⚠️ CORS 可能尚未完全修復，檢查輸出...")
            print(output)
    else:
        print(f"❌ 部署失敗: {output}")
        return False
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)