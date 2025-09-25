#!/usr/bin/env python3
"""
終極數據庫權限修復工具 - GOOGLE "奪取主權" 解決方案
基於GOOGLE深度診斷：解決CREATE TYPE權限問題

此工具將執行所有權轉移，讓應用用戶成為public schema的真正主人
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from datetime import datetime
import urllib.parse

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def execute_ultimate_permissions_fix(conn, app_user):
    """執行GOOGLE的終極權限修復 - 所有權轉移"""
    logger.info(f"🏥 執行GOOGLE終極手術：將public schema所有權轉移給 '{app_user}'")
    
    with conn.cursor() as cur:
        try:
            # GOOGLE指令一：最關鍵的所有權轉移
            logger.info("🎯 指令一：將 public schema 所有權正式移交給應用用戶")
            cur.execute(f'ALTER SCHEMA public OWNER TO "{app_user}";')
            logger.info(f"✅ 所有權轉移成功：public schema → {app_user}")
            
            # GOOGLE指令二：鞏固戰果
            logger.info("🎯 指令二：確保所有權限被授予")
            cur.execute(f'GRANT ALL PRIVILEGES ON SCHEMA public TO "{app_user}";')
            logger.info(f"✅ 全部權限授予成功")
            
            # GOOGLE指令三：預防未來，設置默認權限
            logger.info("🎯 指令三：設置未來新對象的自動權限")
            default_privilege_commands = [
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{app_user}";',
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{app_user}";',
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO "{app_user}";',
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO "{app_user}";'
            ]
            
            for cmd in default_privilege_commands:
                logger.info(f"執行: {cmd}")
                cur.execute(cmd)
            
            logger.info("✅ 未來權限設置完成")
            
            conn.commit()
            logger.info("🎉 GOOGLE終極手術完成！所有權已轉移！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 終極權限修復失敗: {e}")
            conn.rollback()
            return False

def verify_create_type_permission(conn, app_user):
    """驗證CREATE TYPE權限 - GOOGLE診斷的核心問題"""
    logger.info("🧪 測試CREATE TYPE權限 (GOOGLE診斷的關鍵測試)")
    
    with conn.cursor() as cur:
        try:
            # 測試創建枚舉類型（這是失敗的核心操作）
            test_type_name = f"test_enum_type_{int(datetime.now().timestamp())}"
            cur.execute(f"""
                CREATE TYPE {test_type_name} AS ENUM ('test_value_1', 'test_value_2');
            """)
            
            # 清理測試類型
            cur.execute(f"DROP TYPE {test_type_name};")
            
            conn.commit()
            logger.info("✅ CREATE TYPE權限測試成功！")
            logger.info("🎊 GOOGLE診斷問題已完全解決！")
            return True
            
        except Exception as e:
            logger.error(f"❌ CREATE TYPE權限測試失敗: {e}")
            logger.error("🚨 GOOGLE診斷問題仍然存在！")
            conn.rollback()
            return False

def parse_database_url(database_url):
    """解析數據庫 URL"""
    parsed = urllib.parse.urlparse(database_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],  # 移除開頭的 '/'
        'user': parsed.username,
        'password': parsed.password
    }

def main():
    """主函數 - 執行GOOGLE終極診斷修復"""
    logger.info("🚀 GOOGLE終極數據庫權限修復工具啟動...")
    logger.info("🏥 基於GOOGLE深度診斷：解決CREATE TYPE權限分層問題")
    
    # 獲取數據庫連接信息
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        try:
            with open('.env.temp', 'r') as f:
                line = f.read().strip()
                if line.startswith('DATABASE_URL='):
                    database_url = line.split('DATABASE_URL=', 1)[1]
                    logger.info("📄 從臨時配置文件讀取DATABASE_URL")
        except FileNotFoundError:
            pass
    
    if not database_url:
        logger.error("❌ DATABASE_URL 環境變數未設置")
        logger.info("請使用之前設置的DATABASE_URL環境變數")
        sys.exit(1)
    
    try:
        # 解析數據庫 URL
        db_config = parse_database_url(database_url)
        superuser = db_config['user']  # 應該是 doadmin
        
        logger.info(f"📡 使用超級用戶連接：{superuser}")
        logger.info(f"  - 主機: {db_config['host']}")
        logger.info(f"  - 數據庫: {db_config['database']}")
        
        if superuser != 'doadmin':
            logger.warning(f"⚠️ 警告：用戶 '{superuser}' 可能不是超級用戶")
            logger.warning("GOOGLE建議使用 doadmin 超級用戶執行所有權轉移")
        
        # 建立數據庫連接
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            sslmode='require'
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info("✅ 超級用戶數據庫連接成功")
        
        # 確定應用用戶名稱
        app_user = superuser  # 在DigitalOcean中，doadmin就是應用用戶
        logger.info(f"🎯 目標應用用戶: {app_user}")
        
        # 執行GOOGLE的終極權限修復
        if execute_ultimate_permissions_fix(conn, app_user):
            # 驗證CREATE TYPE權限
            if verify_create_type_permission(conn, app_user):
                logger.info("🏆 GOOGLE終極診斷修復完全成功！")
                logger.info("📋 下一步：重新部署TradingAgents應用")
                logger.info("🎯 預期結果：不再有任何 'permission denied' 錯誤")
                logger.info("✨ AI智能路由器和模型能力數據庫將正常初始化")
            else:
                logger.error("❌ CREATE TYPE權限驗證失敗，需要進一步診斷")
        else:
            logger.error("❌ 終極權限修復失敗")
            sys.exit(1)
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 終極權限修復過程中發生錯誤: {e}")
        logger.error("請確認：")
        logger.error("  1. 使用的是 doadmin 超級用戶")
        logger.error("  2. 數據庫連接正常")
        logger.error("  3. 具備執行DDL操作的權限")
        sys.exit(1)

if __name__ == "__main__":
    main()