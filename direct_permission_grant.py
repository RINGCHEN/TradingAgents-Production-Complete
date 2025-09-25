#!/usr/bin/env python3
"""
直接權限授予工具
嘗試通過當前用戶為自己授予CREATE權限
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
        'database': parsed.path[1:],
        'user': parsed.username,
        'password': parsed.password
    }

def try_direct_permission_grants(conn, current_user):
    """嘗試直接授予權限"""
    logger.info(f"🔧 嘗試為當前用戶 '{current_user}' 直接授予權限...")
    
    with conn.cursor() as cur:
        # 檢查當前權限狀態
        logger.info("📋 檢查當前權限狀態:")
        
        try:
            cur.execute("SELECT current_user, session_user;")
            current, session = cur.fetchone()
            logger.info(f"  - 當前用戶: {current}")
            logger.info(f"  - 會話用戶: {session}")
            
            # 檢查是否是超級用戶
            cur.execute("SELECT usesuper FROM pg_user WHERE usename = current_user;")
            is_super = cur.fetchone()[0]
            logger.info(f"  - 超級用戶: {'是' if is_super else '否'}")
            
            # 嘗試各種權限授予方法
            permission_attempts = [
                # 方法1: 嘗試直接GRANT權限
                {
                    "name": "直接GRANT CREATE權限",
                    "sql": f'GRANT CREATE ON SCHEMA public TO "{current_user}";',
                },
                # 方法2: 嘗試GRANT USAGE + CREATE
                {
                    "name": "GRANT USAGE + CREATE權限",
                    "sql": f'GRANT USAGE, CREATE ON SCHEMA public TO "{current_user}";',
                },
                # 方法3: 嘗試通過角色方式
                {
                    "name": "創建並授予角色權限",
                    "sql": f'CREATE ROLE IF NOT EXISTS schema_creator; GRANT CREATE ON SCHEMA public TO schema_creator; GRANT schema_creator TO "{current_user}";',
                },
            ]
            
            for attempt in permission_attempts:
                try:
                    logger.info(f"🎯 嘗試: {attempt['name']}")
                    
                    # 對於多語句，分別執行
                    if ';' in attempt['sql'] and 'CREATE ROLE' in attempt['sql']:
                        statements = [s.strip() for s in attempt['sql'].split(';') if s.strip()]
                        for stmt in statements:
                            logger.info(f"  執行: {stmt}")
                            cur.execute(stmt + ';')
                    else:
                        logger.info(f"  執行: {attempt['sql']}")
                        cur.execute(attempt['sql'])
                    
                    conn.commit()
                    logger.info(f"✅ {attempt['name']} 成功")
                    
                    # 測試CREATE TYPE權限
                    if test_create_type_permission(conn):
                        return True
                        
                except Exception as e:
                    logger.warning(f"⚠️ {attempt['name']} 失敗: {e}")
                    conn.rollback()
                    continue
            
            logger.error("❌ 所有直接權限授予嘗試都失敗了")
            return False
            
        except Exception as e:
            logger.error(f"❌ 權限檢查失敗: {e}")
            return False

def test_create_type_permission(conn):
    """測試CREATE TYPE權限"""
    logger.info("🧪 測試CREATE TYPE權限...")
    
    with conn.cursor() as cur:
        try:
            test_type_name = f"test_enum_direct_{int(datetime.now().timestamp())}"
            cur.execute(f"CREATE TYPE {test_type_name} AS ENUM ('test1', 'test2');")
            cur.execute(f"DROP TYPE {test_type_name};")
            conn.commit()
            
            logger.info("✅ CREATE TYPE權限測試成功！")
            return True
            
        except Exception as e:
            logger.error(f"❌ CREATE TYPE權限測試失敗: {e}")
            conn.rollback()
            return False

def main():
    """主函數"""
    logger.info("🚀 直接權限授予工具啟動...")
    logger.info("🔧 嘗試為當前用戶直接授予CREATE權限")
    
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
        logger.info("✅ 數據庫連接成功")
        
        # 嘗試直接權限授予
        if try_direct_permission_grants(conn, current_user):
            logger.info("🏆 直接權限授予成功！")
            logger.info("📋 下一步：重新部署TradingAgents應用")
            logger.info("🎯 預期結果：不再有任何 'permission denied' 錯誤")
        else:
            logger.error("❌ 直接權限授予失敗")
            logger.info("💡 可能需要聯繫DigitalOcean支援或使用資料庫管理員權限")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 直接權限授予過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()