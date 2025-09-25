#!/usr/bin/env python3
"""
查找應用程式實際使用的數據庫用戶
基於GOOGLE診斷：我們需要找到真正的應用用戶並修復其權限
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_database_url(database_url):
    """解析數據庫 URL"""
    parsed = urllib.parse.urlparse(database_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def check_current_user_and_permissions(conn):
    """檢查當前連接的用戶和權限"""
    logger.info("🔍 檢查當前數據庫用戶和權限...")
    
    with conn.cursor() as cur:
        # 檢查當前用戶
        cur.execute("SELECT current_user, session_user;")
        current_user, session_user = cur.fetchone()
        logger.info(f"📋 當前數據庫用戶資訊:")
        logger.info(f"  - Current User: {current_user}")
        logger.info(f"  - Session User: {session_user}")
        
        # 檢查是否是超級用戶
        cur.execute("SELECT usesuper FROM pg_user WHERE usename = current_user;")
        is_superuser = cur.fetchone()[0]
        logger.info(f"  - Is Superuser: {'✅ YES' if is_superuser else '❌ NO'}")
        
        # 檢查對public schema的權限
        cur.execute("""
            SELECT 
                has_schema_privilege(current_user, 'public', 'CREATE') as can_create,
                has_schema_privilege(current_user, 'public', 'USAGE') as can_use,
                has_schema_privilege(current_user, 'public', 'CREATE') as can_create_objects
        """)
        permissions = cur.fetchone()
        
        logger.info(f"📋 對 public schema 的權限:")
        logger.info(f"  - CREATE: {'✅' if permissions[0] else '❌'}")
        logger.info(f"  - USAGE: {'✅' if permissions[1] else '❌'}")
        
        # 測試CREATE TYPE權限
        try:
            test_type_name = "test_enum_diagnostic"
            cur.execute(f"CREATE TYPE {test_type_name} AS ENUM ('test1', 'test2');")
            cur.execute(f"DROP TYPE {test_type_name};")
            logger.info("  - CREATE TYPE: ✅ 成功")
            return current_user, True
        except Exception as e:
            logger.error(f"  - CREATE TYPE: ❌ 失敗 - {e}")
            return current_user, False

def list_all_database_users(conn):
    """列出所有數據庫用戶"""
    logger.info("👥 列出所有數據庫用戶:")
    
    with conn.cursor() as cur:
        # 檢查 public schema 的所有者
        cur.execute("""
            SELECT schema_owner.usename 
            FROM pg_namespace 
            JOIN pg_user schema_owner ON pg_namespace.nspowner = schema_owner.usesysid
            WHERE pg_namespace.nspname = 'public';
        """)
        public_owner = cur.fetchone()
        if public_owner:
            logger.info(f"🏠 public schema 所有者: {public_owner[0]}")
        
        cur.execute("""
            SELECT usename, usesuper, usecreatedb, 
                   has_schema_privilege(usename, 'public', 'CREATE') as can_create_in_public
            FROM pg_user 
            ORDER BY usename;
        """)
        
        users = cur.fetchall()
        for username, is_super, can_create_db, can_create_in_public in users:
            is_public_owner = public_owner and username == public_owner[0]
            logger.info(f"  👤 {username}:")
            logger.info(f"    - Superuser: {'✅' if is_super else '❌'}")
            logger.info(f"    - Create DB: {'✅' if can_create_db else '❌'}")
            logger.info(f"    - Create in public: {'✅' if can_create_in_public else '❌'}")
            logger.info(f"    - Public owner: {'✅' if is_public_owner else '❌'}")

def get_app_platform_connection_info():
    """獲取App Platform可能使用的連接信息"""
    logger.info("🔍 檢查App Platform環境變數...")
    
    # 檢查可能的數據庫環境變數
    db_env_vars = [
        'DATABASE_URL',
        'DB_URL', 
        'POSTGRES_URL',
        'POSTGRESQL_URL'
    ]
    
    for var_name in db_env_vars:
        value = os.getenv(var_name)
        if value:
            logger.info(f"✅ 找到環境變數 {var_name}")
            try:
                config = parse_database_url(value)
                logger.info(f"  - 用戶: {config['user']}")
                logger.info(f"  - 主機: {config['host']}")
                logger.info(f"  - 數據庫: {config['database']}")
                return config['user']
            except:
                logger.warning(f"  - 無法解析URL")
        else:
            logger.info(f"❌ 環境變數 {var_name} 未設置")
    
    return None

def main():
    """主函數"""
    logger.info("🚀 查找應用程式實際使用的數據庫用戶...")
    logger.info("🎯 基於GOOGLE診斷：找到真正需要權限的用戶")
    
    # 檢查環境變數
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
        sys.exit(1)
    
    try:
        # 解析並連接
        db_config = parse_database_url(database_url)
        logger.info(f"📡 使用URL中的用戶連接: {db_config['user']}")
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            sslmode='require'
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # 檢查當前用戶和權限
        actual_user, has_create_type = check_current_user_and_permissions(conn)
        
        # 列出所有用戶
        list_all_database_users(conn)
        
        # 獲取App可能使用的用戶信息
        app_user = get_app_platform_connection_info()
        
        logger.info("\n" + "="*60)
        logger.info("🎯 GOOGLE診斷結論:")
        logger.info(f"📋 當前連接用戶: {actual_user}")
        logger.info(f"🔑 CREATE TYPE權限: {'✅ 有' if has_create_type else '❌ 無'}")
        
        if not has_create_type:
            logger.error("🚨 問題確認：當前用戶沒有CREATE TYPE權限！")
            logger.info("💡 解決方案：需要對這個用戶執行權限修復：")
            logger.info(f"   ALTER SCHEMA public OWNER TO {actual_user};")
            logger.info(f"   GRANT CREATE ON SCHEMA public TO {actual_user};")
        else:
            logger.info("✅ 當前用戶有CREATE TYPE權限，問題可能在別處")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 診斷過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()