#!/usr/bin/env python3
"""
Redis環境變數診斷工具
基於GOOGLE的分析，檢查DigitalOcean環境變數配置問題

作者：天工 (TianGong) + Claude Code  
基於：GOOGLE 的 Redis 連接診斷分析
"""

import os
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def diagnose_redis_environment():
    """診斷Redis環境變數配置 - 基於GOOGLE的分析指令"""
    logger.info("🔍 GOOGLE診斷指令：Redis環境變數配置檢查")
    logger.info("📋 檢查所有相關的環境變數...")
    
    # GOOGLE指出的關鍵環境變數
    redis_env_vars = {
        'REDIS_URL': os.getenv('REDIS_URL'),
        'REDIS_HOST': os.getenv('REDIS_HOST'),
        'REDIS_PORT': os.getenv('REDIS_PORT'),
        'REDIS_PASSWORD': os.getenv('REDIS_PASSWORD'),
        'REDIS_SSL': os.getenv('REDIS_SSL'),
        'REDIS_DB': os.getenv('REDIS_DB')
    }
    
    # 檢查雲端環境指標
    cloud_indicators = {
        'DATABASE_URL': bool(os.getenv('DATABASE_URL')),
        'PORT': bool(os.getenv('PORT')),
        'DYNO': bool(os.getenv('DYNO')),  # Heroku
        'DIGITALOCEAN_APP': bool(os.getenv('APP_NAME') or os.getenv('DIGITALOCEAN_APP')),
        'GCP_PROJECT': bool(os.getenv('GCP_PROJECT') or os.getenv('GOOGLE_CLOUD_PROJECT'))
    }
    
    is_cloud_env = any(cloud_indicators.values())
    
    logger.info("🌐 雲端環境檢測結果:")
    for indicator, detected in cloud_indicators.items():
        status = "✅ 檢測到" if detected else "❌ 未檢測到"
        logger.info(f"  - {indicator}: {status}")
    
    logger.info(f"\n📊 雲端環境總結: {'是' if is_cloud_env else '否'}")
    
    logger.info("\n🔧 Redis環境變數檢查結果:")
    critical_missing = []
    
    for var_name, var_value in redis_env_vars.items():
        if var_value is not None:
            # 對於敏感信息，只顯示前幾個字符
            if 'PASSWORD' in var_name or 'URL' in var_name:
                display_value = f"{var_value[:20]}..." if len(var_value) > 20 else var_value
            else:
                display_value = var_value
            logger.info(f"  ✅ {var_name}: {display_value}")
        else:
            logger.warning(f"  ❌ {var_name}: 未設置")
            if var_name == 'REDIS_URL' and is_cloud_env:
                critical_missing.append(var_name)
    
    # GOOGLE診斷重點：REDIS_URL在雲端環境中必須設置
    if is_cloud_env:
        logger.info("\n🚨 雲端環境Redis配置診斷:")
        if redis_env_vars['REDIS_URL']:
            logger.info("✅ REDIS_URL已設置 - 這是雲端部署的正確方式")
        else:
            logger.error("❌ CRITICAL: REDIS_URL未設置！")
            logger.error("📋 GOOGLE診斷結論：這就是Redis連接失敗的根本原因")
            logger.error("🔧 解決方案：在DigitalOcean App Platform中設置REDIS_URL環境變數")
            
        # 檢查回退配置
        if not redis_env_vars['REDIS_URL']:
            logger.warning("⚠️ 系統將使用回退配置:")
            logger.warning(f"  - Host: {redis_env_vars.get('REDIS_HOST', 'localhost')}")
            logger.warning(f"  - Port: {redis_env_vars.get('REDIS_PORT', '6379')}")
            logger.warning("❌ 在雲端環境中，localhost:6379不存在，連接必然失敗")
    
    # 生成診斷報告
    report = f"""
=== GOOGLE Redis環境變數診斷報告 ===
生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🌐 環境類型: {'雲端生產環境' if is_cloud_env else '本地開發環境'}
🔗 關鍵問題: {'REDIS_URL未設置' if not redis_env_vars['REDIS_URL'] and is_cloud_env else '配置正常'}

📋 修復指令（如果REDIS_URL未設置）:
1. 登入 DigitalOcean 控制台
2. 進入 twshocks-app → Settings → Components → API Component 
3. 編輯 Environment Variables
4. 添加: REDIS_URL = rediss://your-redis-connection-string
5. 確保 Scope 設為 "Run & Build Time"
6. 保存並重新部署

🎯 預期結果:
部署後日誌應該顯示:
INFO - 🔧 Redis 連接配置:
INFO -   - Redis URL: rediss://doadmin:PASSWORD@...  <-- 真實URL
INFO - ✅ Redis connection successful. Cache system is fully operational.

而不是:
INFO -   - Redis URL: 未設置  <-- 當前錯誤狀態
ERROR - ❌ Redis connection failed: Error 111
"""
    
    logger.info(report)
    
    # 保存診斷報告
    with open('redis_diagnosis_report.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info("📄 診斷報告已保存: redis_diagnosis_report.md")
    
    return not bool(critical_missing)

def main():
    """主函數"""
    logger.info("🚀 Redis環境變數診斷工具啟動...")
    
    try:
        success = diagnose_redis_environment()
        
        if success:
            logger.info("✅ 環境變數診斷完成，配置看起來正常")
        else:
            logger.error("❌ 發現關鍵環境變數缺失，需要修復")
            
    except Exception as e:
        logger.error(f"❌ 診斷過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()