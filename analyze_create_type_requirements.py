#!/usr/bin/env python3
"""
分析CREATE TYPE權限要求
深入研究為什麼有CREATE權限但CREATE TYPE仍然失敗
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
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
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def analyze_create_type_requirements(conn):
    """分析CREATE TYPE的權限要求"""
    logger.info("🔬 深入分析CREATE TYPE權限要求...")
    
    with conn.cursor() as cur:
        try:
            # 1. 檢查當前用戶的所有權限
            logger.info("📋 當前用戶的詳細權限分析:")
            
            cur.execute("SELECT current_user;")
            current_user = cur.fetchone()[0]
            
            # 檢查schema權限
            cur.execute("""
                SELECT 
                    has_schema_privilege(current_user, 'public', 'CREATE') as can_create,
                    has_schema_privilege(current_user, 'public', 'USAGE') as can_use,
                    has_schema_privilege(current_user, 'public', 'CREATE') as can_create_objects
            """)
            schema_perms = cur.fetchone()
            logger.info(f"  - CREATE權限: {'✅' if schema_perms[0] else '❌'}")
            logger.info(f"  - USAGE權限: {'✅' if schema_perms[1] else '❌'}")
            
            # 2. 檢查schema所有者
            cur.execute("""
                SELECT n.nspname, u.usename as owner
                FROM pg_namespace n
                JOIN pg_user u ON n.nspowner = u.usesysid
                WHERE n.nspname = 'public';
            """)
            schema_info = cur.fetchone()
            if schema_info:
                logger.info(f"  - public schema所有者: {schema_info[1]}")
                logger.info(f"  - 當前用戶是所有者: {'✅' if schema_info[1] == current_user else '❌'}")
            
            # 3. 檢查ACL（訪問控制列表）
            cur.execute("""
                SELECT nspacl FROM pg_namespace WHERE nspname = 'public';
            """)
            acl = cur.fetchone()
            logger.info(f"  - public schema ACL: {acl[0] if acl and acl[0] else '預設'}")
            
            # 4. 嘗試不同的TYPE創建方式
            logger.info("\n🧪 測試不同的TYPE創建方式:")
            
            test_cases = [
                {
                    "name": "基本枚舉類型",
                    "sql": "CREATE TYPE test_enum_basic AS ENUM ('a', 'b', 'c');"
                },
                {
                    "name": "複合類型",
                    "sql": "CREATE TYPE test_composite AS (id integer, name text);"
                },
                {
                    "name": "域類型",
                    "sql": "CREATE DOMAIN test_domain AS integer CHECK (VALUE > 0);"
                },
                {
                    "name": "範圍類型（如果支持）",
                    "sql": "CREATE TYPE test_range AS RANGE (subtype = integer);"
                }
            ]
            
            successful_operations = []
            
            for test in test_cases:
                try:
                    logger.info(f"  🎯 測試: {test['name']}")
                    cur.execute(test['sql'])
                    conn.commit()
                    
                    # 嘗試清理
                    cleanup_sql = test['sql'].replace('CREATE TYPE', 'DROP TYPE').replace('CREATE DOMAIN', 'DROP DOMAIN').split(' AS ')[0] + ';'
                    cur.execute(cleanup_sql)
                    conn.commit()
                    
                    logger.info(f"    ✅ {test['name']} 成功")
                    successful_operations.append(test['name'])
                    
                except Exception as e:
                    logger.error(f"    ❌ {test['name']} 失敗: {e}")
                    conn.rollback()
            
            # 5. 檢查PostgreSQL版本和設置
            logger.info("\n📊 PostgreSQL環境信息:")
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            logger.info(f"  - PostgreSQL版本: {version}")
            
            # 檢查相關設置
            settings_to_check = [
                'shared_preload_libraries',
                'log_statement',
                'default_tablespace'
            ]
            
            for setting in settings_to_check:
                try:
                    cur.execute(f"SHOW {setting};")
                    value = cur.fetchone()[0]
                    logger.info(f"  - {setting}: {value}")
                except Exception as e:
                    logger.warning(f"  - {setting}: 無法查詢 ({e})")
            
            # 6. 嘗試權限提升策略
            logger.info("\n🚀 嘗試權限提升策略:")
            
            elevation_attempts = [
                {
                    "name": "明確授予TYPE權限",
                    "sql": f'GRANT CREATE ON SCHEMA public TO "{current_user}";'
                },
                {
                    "name": "授予所有schema權限",
                    "sql": f'GRANT ALL ON SCHEMA public TO "{current_user}";'
                },
                {
                    "name": "嘗試設置search_path",
                    "sql": "SET search_path TO public, pg_catalog;"
                }
            ]
            
            for attempt in elevation_attempts:
                try:
                    logger.info(f"  🎯 嘗試: {attempt['name']}")
                    cur.execute(attempt['sql'])
                    conn.commit()
                    logger.info(f"    ✅ {attempt['name']} 執行成功")
                    
                    # 測試CREATE TYPE
                    try:
                        cur.execute("CREATE TYPE test_after_elevation AS ENUM ('x', 'y');")
                        cur.execute("DROP TYPE test_after_elevation;")
                        conn.commit()
                        logger.info("    🎊 CREATE TYPE測試成功！")
                        return True
                    except Exception as e:
                        logger.info(f"    ⚠️ CREATE TYPE仍然失敗: {e}")
                        conn.rollback()
                        
                except Exception as e:
                    logger.warning(f"    ❌ {attempt['name']} 失敗: {e}")
                    conn.rollback()
            
            logger.info(f"\n📋 分析總結:")
            logger.info(f"  - 成功的操作: {len(successful_operations)} 個")
            logger.info(f"  - 權限提升嘗試: 全部失敗")
            logger.info(f"  - 可能原因: DigitalOcean管理資料庫的特殊限制")
            
            return False
            
        except Exception as e:
            logger.error(f"❌ CREATE TYPE權限分析失敗: {e}")
            return False

def main():
    """主函數"""
    logger.info("🚀 CREATE TYPE權限要求分析工具啟動...")
    
    # 讀取應用用戶連接資訊
    database_url = None
    try:
        with open('.env.temp', 'r') as f:
            line = f.read().strip()
            if line.startswith('DATABASE_URL='):
                database_url = line.split('DATABASE_URL=', 1)[1]
                logger.info("📄 從應用用戶配置文件讀取DATABASE_URL")
    except FileNotFoundError:
        logger.error("❌ 找不到應用用戶配置文件")
        sys.exit(1)
    
    if not database_url:
        logger.error("❌ 無法讀取DATABASE_URL")
        sys.exit(1)
    
    try:
        # 解析數據庫 URL
        db_config = parse_database_url(database_url)
        current_user = db_config['user']
        
        logger.info(f"📡 使用當前用戶連接：{current_user}")
        
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
        
        # 分析CREATE TYPE權限要求
        if analyze_create_type_requirements(conn):
            logger.info("🏆 CREATE TYPE權限問題已解決！")
        else:
            logger.error("❌ CREATE TYPE權限問題仍然存在")
            logger.info("💡 建議：可能需要聯繫DigitalOcean支援")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 分析過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()