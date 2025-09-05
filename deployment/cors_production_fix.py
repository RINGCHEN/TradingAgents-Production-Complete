#!/usr/bin/env python3
"""
CORS Production Fix Script
Emergency fix for CORS wildcard issue in production
"""

import os
import subprocess
import json
import sys
from datetime import datetime

def log_message(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_gcloud_auth():
    """Check if gcloud is authenticated"""
    try:
        result = subprocess.run(['gcloud', 'auth', 'list'], 
                              capture_output=True, text=True, check=True)
        log_message("✅ gcloud 認證檢查通過")
        return True
    except subprocess.CalledProcessError:
        log_message("❌ gcloud 認證失敗")
        return False

def get_current_service_config():
    """Get current service configuration"""
    try:
        cmd = [
            'gcloud', 'run', 'services', 'describe', 'tradingagents',
            '--region=asia-east1',
            '--format=json'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        config = json.loads(result.stdout)
        log_message("✅ 成功獲取當前服務配置")
        return config
    except subprocess.CalledProcessError as e:
        log_message(f"❌ 獲取服務配置失敗: {e.stderr}")
        return None

def update_cors_environment():
    """Update environment variables to fix CORS"""
    log_message("🔧 開始修復 CORS 配置...")
    
    # Set environment to production to trigger specific CORS settings
    env_vars = {
        'ENVIRONMENT': 'production',
        'CORS_ORIGINS': 'https://admin.03king.com,https://03king.com,https://www.03king.com,https://tradingagents-main.web.app',
        'CORS_CREDENTIALS': 'true',
        'DEBUG': 'false'
    }
    
    # Build the gcloud command
    cmd = [
        'gcloud', 'run', 'services', 'update', 'tradingagents',
        '--region=asia-east1'
    ]
    
    # Add environment variables
    for key, value in env_vars.items():
        cmd.extend(['--set-env-vars', f'{key}={value}'])
    
    try:
        log_message("🚀 執行 CORS 修復部署...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        log_message("✅ CORS 配置更新成功")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"❌ CORS 配置更新失敗: {e.stderr}")
        return False

def restart_service():
    """Restart the service to apply changes"""
    try:
        log_message("🔄 重啟服務以應用更改...")
        cmd = [
            'gcloud', 'run', 'services', 'update', 'tradingagents',
            '--region=asia-east1',
            '--cpu=1',
            '--memory=2Gi'
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        log_message("✅ 服務重啟成功")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"❌ 服務重啟失敗: {e.stderr}")
        return False

def verify_cors_fix():
    """Verify CORS fix by testing the endpoint"""
    import requests
    
    try:
        log_message("🔍 驗證 CORS 修復...")
        
        # Test with admin.03king.com origin
        headers = {
            'Origin': 'https://admin.03king.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            'https://tradingagents-351731559902.asia-east1.run.app/health',
            headers=headers,
            timeout=10
        )
        
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        
        if cors_header == 'https://admin.03king.com':
            log_message("✅ CORS 修復驗證成功 - 正確返回特定域名")
            return True
        elif cors_header == '*':
            log_message("⚠️ CORS 仍返回通配符，需要進一步修復")
            return False
        else:
            log_message(f"⚠️ CORS 返回: {cors_header}")
            return False
            
    except Exception as e:
        log_message(f"❌ CORS 驗證失敗: {str(e)}")
        return False

def create_emergency_cors_patch():
    """Create emergency CORS patch file"""
    patch_content = '''
# Emergency CORS Fix for Production
# Apply this directly to the running container

import os
from fastapi.middleware.cors import CORSMiddleware

# Force production CORS settings
PRODUCTION_ORIGINS = [
    "https://admin.03king.com",
    "https://03king.com", 
    "https://www.03king.com",
    "https://tradingagents-main.web.app",
    "https://twstock-admin-466914.web.app"
]

# Apply CORS middleware with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=PRODUCTION_ORIGINS,  # No wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Range", "X-Request-ID"],
    max_age=86400
)
'''
    
    with open('emergency_cors_patch.py', 'w', encoding='utf-8') as f:
        f.write(patch_content)
    
    log_message("📝 創建緊急 CORS 修補文件: emergency_cors_patch.py")

def main():
    """Main execution function"""
    log_message("🚀 開始 CORS 生產環境緊急修復")
    
    # Check prerequisites
    if not check_gcloud_auth():
        log_message("請先運行: gcloud auth login")
        sys.exit(1)
    
    # Get current config
    current_config = get_current_service_config()
    if not current_config:
        log_message("無法獲取當前服務配置，將嘗試直接修復")
    
    # Update CORS environment
    if update_cors_environment():
        log_message("✅ 環境變量更新成功")
        
        # Wait a moment for the change to propagate
        import time
        log_message("⏱️ 等待配置生效...")
        time.sleep(30)
        
        # Verify fix
        if verify_cors_fix():
            log_message("🎉 CORS 修復完成！")
        else:
            log_message("⚠️ 修復可能需要更多時間生效，請稍後再測試")
    else:
        log_message("❌ 環境變量更新失敗")
        create_emergency_cors_patch()
        log_message("📋 已創建緊急修補文件，請手動應用")
    
    log_message("🏁 CORS 修復程序完成")

if __name__ == "__main__":
    main()