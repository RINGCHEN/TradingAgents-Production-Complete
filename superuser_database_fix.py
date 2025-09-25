#!/usr/bin/env python3
"""
超級用戶權限修復工具
基於GOOGLE診斷：使用postgres超級用戶執行所有權轉移
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

def execute_superuser_permissions_fix(conn, target_user):
    """使用超級用戶執行權限修復"""
    logger.info(f"🏥 使用超級用戶執行：將public schema所有權轉移給 '{target_user}'")
    
    with conn.cursor() as cur:
        try:
            # 步驟1：將 public schema 所有權轉移給目標用戶
            logger.info("🎯 步驟1：將 public schema 所有權轉移給應用用戶")
            cur.execute(f'ALTER SCHEMA public OWNER TO "{target_user}";')
            logger.info(f"✅ 所有權轉移成功：public schema → {target_user}")
            
            # 步驟2：授予所有權限
            logger.info("🎯 步驟2：確保所有權限被授予")
            cur.execute(f'GRANT ALL PRIVILEGES ON SCHEMA public TO "{target_user}";')
            cur.execute(f'GRANT CREATE ON SCHEMA public TO "{target_user}";')
            logger.info(f"✅ 全部權限授予成功")
            
            # 步驟3：設置默認權限
            logger.info("🎯 步驟3：設置未來新對象的自動權限")
            default_privilege_commands = [
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "{target_user}";',
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "{target_user}";',
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO "{target_user}";',
                f'ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO "{target_user}";'
            ]
            
            for cmd in default_privilege_commands:
                logger.info(f"執行: {cmd}")
                cur.execute(cmd)
            
            logger.info("✅ 未來權限設置完成")
            
            conn.commit()
            logger.info("🎉 超級用戶權限修復完成！所有權已轉移！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 超級用戶權限修復失敗: {e}")
            conn.rollback()
            return False

def verify_create_type_permission(conn, target_user):
    """驗證CREATE TYPE權限"""
    logger.info("🧪 測試CREATE TYPE權限（GOOGLE診斷的核心問題）")
    
    with conn.cursor() as cur:
        try:
            # 測試創建枚舉類型
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
            conn.rollback()
            return False

def main():
    """主函數"""
    logger.info("🚀 超級用戶數據庫權限修復工具啟動...")
    logger.info("🏥 使用postgres超級用戶執行GOOGLE診斷修復")
    
    # 讀取超級用戶連接資訊 - 嘗試doadmin
    database_url = None
    try:
        with open('.env.doadmin', 'r') as f:
            line = f.read().strip()
            if line.startswith('DATABASE_URL='):
                database_url = line.split('DATABASE_URL=', 1)[1]
                logger.info("📄 從doadmin配置文件讀取DATABASE_URL")
    except FileNotFoundError:
        try:
            with open('.env.superuser', 'r') as f:
                line = f.read().strip()
                if line.startswith('DATABASE_URL='):
                    database_url = line.split('DATABASE_URL=', 1)[1]
                    logger.info("📄 從超級用戶配置文件讀取DATABASE_URL")
        except FileNotFoundError:
            logger.error("❌ 找不到超級用戶配置文件")
            sys.exit(1)
    
    if not database_url:
        logger.error("❌ 無法讀取超級用戶DATABASE_URL")
        sys.exit(1)
    
    try:
        # 解析數據庫 URL
        db_config = parse_database_url(database_url)
        superuser = db_config['user']  # 應該是 postgres
        
        logger.info(f"📡 使用超級用戶連接：{superuser}")
        logger.info(f"  - 主機: {db_config['host']}")
        logger.info(f"  - 數據庫: {db_config['database']}")
        
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
        
        # 目標用戶是原來的應用用戶
        target_user = "tradingagents-complete-db"
        logger.info(f"🎯 目標應用用戶: {target_user}")
        
        # 執行超級用戶權限修復
        if execute_superuser_permissions_fix(conn, target_user):
            # 切換回目標用戶連接進行驗證
            logger.info("🔄 切換回應用用戶進行權限驗證...")
            conn.close()
            
            # 使用應用用戶重新連接
            with open('.env.temp', 'r') as f:
                app_line = f.read().strip()
                app_database_url = app_line.split('DATABASE_URL=', 1)[1]
            
            app_config = parse_database_url(app_database_url)
            app_conn = psycopg2.connect(
                host=app_config['host'],
                port=app_config['port'],
                database=app_config['database'],
                user=app_config['user'],
                password=app_config['password'],
                sslmode='require'
            )
            app_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            # 驗證CREATE TYPE權限
            if verify_create_type_permission(app_conn, target_user):
                logger.info("🏆 GOOGLE終極診斷修復完全成功！")
                logger.info("📋 下一步：重新部署TradingAgents應用")
                logger.info("🎯 預期結果：不再有任何 'permission denied' 錯誤")
                logger.info("✨ AI智能路由器和模型能力數據庫將正常初始化")
            else:
                logger.error("❌ CREATE TYPE權限驗證失敗")
                
            app_conn.close()
        else:
            logger.error("❌ 超級用戶權限修復失敗")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ 超級用戶權限修復過程中發生錯誤: {e}")
        logger.error("請確認：")
        logger.error("  1. postgres 超級用戶連接正常")
        logger.error("  2. 具備執行DDL操作的權限")
        logger.error("  3. 目標用戶存在於資料庫中")
        sys.exit(1)

if __name__ == "__main__":
    main()