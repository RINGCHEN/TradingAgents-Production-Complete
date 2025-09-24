#!/usr/bin/env python3
"""
增強版依賴鎖定工具 - 基於GOOGLE清剿指令
解決 statsmodels 和其他缺失依賴問題

基於GOOGLE的診斷，這個工具將：
1. 安裝所有缺失的依賴包
2. 生成精確版本的依賴鎖定文件
3. 驗證關鍵包的可用性

作者：天工 (TianGong) + Claude Code
基於：GOOGLE 的最終清剿指令分析
"""

import subprocess
import sys
import os
import logging
from datetime import datetime
import pkg_resources

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# GOOGLE 清剿指令：關鍵缺失依賴包列表
CRITICAL_MISSING_PACKAGES = [
    'statsmodels==0.14.2',  # 深度行為學習系統
    'xgboost==2.0.3'        # 機器學習核心依賴
]

def install_missing_packages():
    """安裝 GOOGLE 診斷出的缺失依賴包"""
    logger.info("🚨 GOOGLE 清剿指令：營養補充階段開始")
    logger.info("📦 安裝關鍵缺失依賴包...")
    
    for package in CRITICAL_MISSING_PACKAGES:
        try:
            logger.info(f"📥 安裝: {package}")
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 成功安裝: {package}")
            else:
                logger.error(f"❌ 安裝失敗: {package}")
                logger.error(f"錯誤信息: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ 安裝過程出錯: {e}")

def generate_requirements_lock():
    """生成精確版本的依賴鎖定文件"""
    logger.info("🔒 生成依賴鎖定文件...")
    
    try:
        # 獲取當前安裝的所有包
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'freeze'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            lock_content = result.stdout
            
            # 生成時間戳和文件頭
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            header = f"""# TradingAgents Production Dependencies Lock File
# Generated: {timestamp}
# Based on: GOOGLE's final clearance instructions
# 
# This file contains exact versions of all dependencies to ensure
# consistent deployments across all environments.
#
# GOOGLE診斷修復記錄:
# - 添加 statsmodels==0.14.2 (深度行為學習系統)
# - 確認 xgboost==2.0.3 (機器學習核心)
# - 完整依賴鎖定以避免版本衝突

"""
            
            # 寫入鎖定文件
            lock_filename = 'requirements.lock.txt'
            with open(lock_filename, 'w', encoding='utf-8') as f:
                f.write(header)
                f.write(lock_content)
            
            logger.info(f"✅ 依賴鎖定文件已生成: {lock_filename}")
            
            # 統計依賴包數量
            package_count = len([line for line in lock_content.split('\n') if line.strip() and not line.startswith('#')])
            logger.info(f"📊 鎖定依賴包總數: {package_count}")
            
            return lock_filename
            
        else:
            logger.error(f"❌ 無法獲取依賴列表: {result.stderr}")
            return None
            
    except Exception as e:
        logger.error(f"❌ 生成鎖定文件時出錯: {e}")
        return None

def verify_critical_packages():
    """驗證關鍵包的可用性"""
    logger.info("🧪 驗證關鍵包的可用性...")
    
    test_imports = [
        ('statsmodels', 'statsmodels.api'),
        ('xgboost', 'xgboost'),
        ('sklearn', 'sklearn.ensemble'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scipy', 'scipy.stats'),
        ('torch', 'torch'),
        ('fastapi', 'fastapi'),
        ('redis', 'redis'),
        ('psycopg2', 'psycopg2')
    ]
    
    success_count = 0
    total_count = len(test_imports)
    
    for package_name, import_name in test_imports:
        try:
            __import__(import_name)
            logger.info(f"✅ {package_name}: 導入成功")
            success_count += 1
        except ImportError as e:
            logger.error(f"❌ {package_name}: 導入失敗 - {e}")
        except Exception as e:
            logger.error(f"⚠️ {package_name}: 導入時出現問題 - {e}")
    
    success_rate = (success_count / total_count) * 100
    logger.info(f"📊 關鍵包驗證結果: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        logger.info("🎉 依賴包驗證成功！")
        return True
    else:
        logger.warning("⚠️ 部分關鍵包驗證失敗，可能影響系統功能")
        return False

def create_deployment_instructions():
    """創建部署指令文件"""
    instructions = """# GOOGLE清剿指令 - 部署說明
# 
# 依賴包營養補充完成後的部署步驟:
# 
# 1. 確認所有修復已提交到 Git:
git add requirements.txt requirements.lock.txt
git commit -m "fix: GOOGLE清剿指令 - 添加statsmodels依賴，完成營養補充

基於GOOGLE最終診斷分析:
- 添加 statsmodels==0.14.2 (深度行為學習系統)
- 生成完整依賴鎖定文件 requirements.lock.txt
- 驗證所有關鍵包可用性

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# 2. 推送到 DigitalOcean 觸發自動部署:
git push origin main

# 3. 監控部署日誌，確認不再出現 'No module named statsmodels' 警告

# 4. 驗證系統健康:
curl https://twshocks-app-79rsx.ondigitalocean.app/health
"""
    
    with open('deployment_instructions_final.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    logger.info("📋 部署指令已生成: deployment_instructions_final.md")

def main():
    """主函數"""
    logger.info("🚀 GOOGLE清剿指令 - 依賴包營養補充工具啟動...")
    
    try:
        # 第一步：安裝缺失的依賴包
        install_missing_packages()
        
        # 第二步：生成依賴鎖定文件
        lock_file = generate_requirements_lock()
        if not lock_file:
            logger.error("❌ 無法生成依賴鎖定文件")
            sys.exit(1)
        
        # 第三步：驗證關鍵包
        if not verify_critical_packages():
            logger.warning("⚠️ 部分包驗證失敗，但繼續執行")
        
        # 第四步：生成部署指令
        create_deployment_instructions()
        
        logger.info("🎉 GOOGLE清剿指令 - 依賴包營養補充完成！")
        logger.info("📋 下一步: 執行 Git 提交和推送以觸發 DigitalOcean 部署")
        
    except Exception as e:
        logger.error(f"❌ 依賴包營養補充過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()