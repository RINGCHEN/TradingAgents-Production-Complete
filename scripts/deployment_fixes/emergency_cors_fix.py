#!/usr/bin/env python3
"""
Emergency CORS Fix - Direct Service Update
立即修復 CORS 配置，不需要重新構建鏡像
"""

import subprocess
import json
import time
from datetime import datetime

def log_message(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_cors_headers():
    """Check current CORS headers"""
    import requests
    
    try:
        log_message("🔍 檢查當前 CORS 設置...")
        
        headers = {
            'Origin': 'https://admin.03king.com',
            'User-Agent': 'Mozilla/5.0 Emergency-Fix-Test'
        }
        
        response = requests.get(
            'https://tradingagents-351731559902.asia-east1.run.app/health',
            headers=headers,
            timeout=10
        )
        
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        log_message(f"當前 CORS 標頭: {cors_header}")
        
        if cors_header == 'https://admin.03king.com':
            return "FIXED"
        elif cors_header == '*':
            return "WILDCARD"
        else:
            return f"UNKNOWN: {cors_header}"
            
    except Exception as e:
        log_message(f"❌ 檢查失敗: {str(e)}")
        return "ERROR"

def force_service_restart():
    """Force service restart to apply environment changes"""
    try:
        log_message("🔄 強制重啟服務...")
        
        # Update with a dummy annotation to force restart
        cmd = [
            'gcloud', 'run', 'services', 'update', 'tradingagents',
            '--region=asia-east1',
            '--update-annotations', f'restart-time={int(time.time())}'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        log_message("✅ 服務重啟成功")
        return True
        
    except subprocess.CalledProcessError as e:
        log_message(f"❌ 重啟失敗: {e.stderr}")
        return False

def emergency_cors_fix():
    """Apply emergency CORS fix"""
    log_message("🚨 開始緊急 CORS 修復...")
    
    # Step 1: Check current status
    initial_status = check_cors_headers()
    log_message(f"初始狀態: {initial_status}")
    
    if initial_status == "FIXED":
        log_message("✅ CORS 已經修復！")
        return True
    
    # Step 2: Set environment variables for CORS fix
    try:
        log_message("🔧 設置 CORS 修復環境變數...")
        
        cmd = [
            'gcloud', 'run', 'services', 'update', 'tradingagents',
            '--region=asia-east1',
            '--set-env-vars', 'CORS_FIX=enabled,FORCE_PRODUCTION_CORS=true'
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        log_message("✅ 環境變數設置成功")
        
    except subprocess.CalledProcessError as e:
        log_message(f"❌ 環境變數設置失敗: {e.stderr}")
        return False
    
    # Step 3: Wait for changes to propagate
    log_message("⏱️ 等待變更生效...")
    time.sleep(60)
    
    # Step 4: Check if fix is working
    final_status = check_cors_headers()
    log_message(f"修復後狀態: {final_status}")
    
    if final_status == "FIXED":
        log_message("🎉 CORS 修復成功！")
        return True
    elif final_status == "WILDCARD":
        log_message("⚠️ 仍然返回通配符，需要重新部署代碼")
        return False
    else:
        log_message(f"⚠️ 未知狀態: {final_status}")
        return False

def create_deployment_solution():
    """Create temporary deployment solution"""
    log_message("📝 創建部署解決方案...")
    
    deployment_script = '''#!/bin/bash
# Emergency CORS Fix Deployment Script

echo "🚀 開始緊急 CORS 修復部署..."

# Build with Cloud Build (simplified)
gcloud builds submit \
  --tag=gcr.io/twstock-466914/tradingagents:cors-fix \
  --machine-type=e2-standard-4 \
  --disk-size=20GB \
  --timeout=1200s \
  .

if [ $? -eq 0 ]; then
    echo "✅ 鏡像構建成功"
    
    # Deploy the new image
    gcloud run deploy tradingagents \
      --image=gcr.io/twstock-466914/tradingagents:cors-fix \
      --region=asia-east1 \
      --set-env-vars=CORS_FIX=enabled,ENVIRONMENT=production \
      --cpu=1 \
      --memory=2Gi \
      --max-instances=2
      
    if [ $? -eq 0 ]; then
        echo "🎉 部署成功！"
        
        # Test CORS
        echo "🔍 測試 CORS..."
        curl -v -H "Origin: https://admin.03king.com" \
          https://tradingagents-351731559902.asia-east1.run.app/health
    else
        echo "❌ 部署失敗"
    fi
else
    echo "❌ 鏡像構建失敗"
fi
'''
    
    with open('emergency_deploy.sh', 'w') as f:
        f.write(deployment_script)
    
    log_message("📋 已創建 emergency_deploy.sh 腳本")

def main():
    """Main function"""
    log_message("🚨 緊急 CORS 修復程序啟動")
    
    # Try environment variable fix first
    if emergency_cors_fix():
        log_message("✅ 修復完成")
    else:
        log_message("⚠️ 環境變數修復失敗，創建部署解決方案...")
        create_deployment_solution()
        log_message("📋 請運行 emergency_deploy.sh 進行完整部署")

if __name__ == "__main__":
    main()