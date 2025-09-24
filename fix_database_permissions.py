#!/usr/bin/env python3
"""
數據庫權限修復工具
解決 DigitalOcean PostgreSQL 權限問題

基於GOOGLE的分析，這是導致系統啟動失敗的根本原因。
此腳本將檢查並修復數據庫權限問題。

使用方法:
1. 確保 DATABASE_URL 環境變數已設置
2. 運行此腳本: python fix_database_permissions.py
3. 重新部署應用程序

作者：天工 (TianGong) + Claude Code
基於：GOOGLE 的生產環境診斷分析
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

def check_database_permissions(conn, app_user):
    """檢查當前數據庫權限"""
    logger.info(f"🔍 檢查用戶 '{app_user}' 的數據庫權限...")
    
    with conn.cursor() as cur:
        # 檢查用戶是否存在
        cur.execute("""
            SELECT EXISTS(
                SELECT 1 FROM pg_roles WHERE rolname = %s
            )
        """, (app_user,))
        user_exists = cur.fetchone()[0]
        
        if not user_exists:
            logger.error(f"❌ 用戶 '{app_user}' 不存在！")
            return False
        
        # 檢查對 public schema 的權限
        cur.execute("""
            SELECT 
                has_schema_privilege(%s, 'public', 'CREATE') as can_create,
                has_schema_privilege(%s, 'public', 'USAGE') as can_use
        """, (app_user, app_user))
        
        permissions = cur.fetchone()
        can_create = permissions[0]
        can_use = permissions[1]
        
        logger.info(f"📋 權限檢查結果:")
        logger.info(f"  - 可以使用 public schema: {'✅' if can_use else '❌'}")
        logger.info(f"  - 可以在 public schema 中創建對象: {'✅' if can_create else '❌'}")
        
        return can_create and can_use

def fix_database_permissions(conn, app_user):
    """修復數據庫權限 - 基於 GOOGLE 最終診斷的徹底解決方案"""
    logger.info(f"🔧 修復用戶 '{app_user}' 的數據庫權限...")
    logger.info("🏥 執行 GOOGLE 建議的根治性修復：ALTER SCHEMA public OWNER")
    
    with conn.cursor() as cur:
        try:
            # GOOGLE 診斷建議：最徹底的解決方案 - 將 schema 所有權轉移
            logger.info("🏥 GOOGLE 診斷建議：將 public schema 的所有權赋予應用用戶")
            permission_commands = [
                f"ALTER SCHEMA public OWNER TO {app_user}",
                f"GRANT ALL ON SCHEMA public TO {app_user}",
                f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {app_user}",
                f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {app_user}",
                f"GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {app_user}",
                f"GRANT ALL PRIVILEGES ON ALL TYPES IN SCHEMA public TO {app_user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {app_user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {app_user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {app_user}",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO {app_user}"
            ]
            
            for cmd in permission_commands:
                logger.info(f"執行: {cmd}")
                cur.execute(cmd)
            
            conn.commit()
            logger.info("✅ 權限修復成功！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 權限修復失敗: {e}")
            conn.rollback()
            return False

def test_table_creation(conn, app_user):
    """測試表創建權限"""
    logger.info("🧪 測試表創建權限...")
    
    with conn.cursor() as cur:
        try:
            # 嘗試創建測試表
            test_table_name = f"permission_test_{int(datetime.now().timestamp())}"
            cur.execute(f"""
                CREATE TABLE {test_table_name} (
                    id SERIAL PRIMARY KEY,
                    test_data TEXT
                );
            """)
            
            # 插入測試數據
            cur.execute(f"INSERT INTO {test_table_name} (test_data) VALUES ('test');")
            
            # 清理測試表
            cur.execute(f"DROP TABLE {test_table_name};")
            
            conn.commit()
            logger.info("✅ 表創建測試成功！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 表創建測試失敗: {e}")
            conn.rollback()
            return False

def main():
    """主函數"""
    logger.info("🚀 數據庫權限修復工具啟動...")
    logger.info("📊 基於 GOOGLE 的生產環境診斷分析")
    
    # 獲取數據庫連接信息
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("❌ DATABASE_URL 環境變數未設置")
        logger.info("請設置 DATABASE_URL 環境變數，例如:")
        logger.info("export DATABASE_URL='postgresql://username:password@host:port/dbname'")
        sys.exit(1)
    
    try:
        # 解析數據庫 URL
        db_config = parse_database_url(database_url)
        app_user = db_config['user']
        
        logger.info(f"📡 連接到數據庫:")
        logger.info(f"  - 主機: {db_config['host']}")
        logger.info(f"  - 端口: {db_config['port']}")
        logger.info(f"  - 數據庫: {db_config['database']}")
        logger.info(f"  - 用戶: {app_user}")
        
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
        logger.info("✅ 數據庫連接成功")
        
        # 檢查當前權限
        if check_database_permissions(conn, app_user):
            logger.info("✅ 數據庫權限已經正常，無需修復")
        else:
            logger.info("⚠️ 發現權限問題，開始修復...")
            
            # 嘗試修復權限
            if fix_database_permissions(conn, app_user):
                # 再次檢查權限
                if check_database_permissions(conn, app_user):
                    logger.info("✅ 權限修復並驗證成功！")
                else:
                    logger.error("❌ 權限修復後驗證失敗")
                    sys.exit(1)
            else:
                logger.error("❌ 權限修復失敗")
                sys.exit(1)
        
        # 最終測試
        if test_table_creation(conn, app_user):
            logger.info("🎉 數據庫權限修復完成！系統現在應該可以正常創建表了。")
            logger.info("📋 接下來的步驟:")
            logger.info("  1. 重新部署 TradingAgents 應用")
            logger.info("  2. 檢查啟動日誌，確認沒有 'permission denied' 錯誤")
            logger.info("  3. 驗證 API 端點正常工作")
        else:
            logger.error("❌ 最終測試失敗，請檢查數據庫配置")
            sys.exit(1)
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 數據庫權限修復過程中發生錯誤: {e}")
        logger.error("請檢查:")
        logger.error("  1. DATABASE_URL 是否正確")
        logger.error("  2. 數據庫是否可以訪問")
        logger.error("  3. 用戶是否有足夠的權限執行 GRANT 操作")
        sys.exit(1)

if __name__ == "__main__":
    main()