#!/usr/bin/env python3
"""
檢查資料庫擁有者
基於您的指導：pg_database_owner 是隱含的資料庫擁有者角色
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

def check_database_ownership(conn):
    """檢查資料庫擁有者"""
    logger.info("🔍 檢查資料庫擁有者 (pg_database_owner 隱含成員)...")
    
    with conn.cursor() as cur:
        try:
            # 查詢所有資料庫及其擁有者
            logger.info("📋 所有資料庫及其擁有者:")
            cur.execute("""
                SELECT datname, pg_catalog.pg_get_userbyid(datdba) AS owner 
                FROM pg_database
                ORDER BY datname;
            """)
            
            all_databases = cur.fetchall()
            target_database = None
            
            for db_name, owner in all_databases:
                is_target = db_name == 'tradingagents-complete-db'
                status = "🎯 [目標資料庫]" if is_target else ""
                logger.info(f"  📁 {db_name}: 擁有者 = {owner} {status}")
                
                if is_target:
                    target_database = (db_name, owner)
            
            if target_database:
                db_name, current_owner = target_database
                logger.info(f"\n🎯 目標資料庫分析:")
                logger.info(f"  - 資料庫: {db_name}")
                logger.info(f"  - 當前擁有者: {current_owner}")
                logger.info(f"  - pg_database_owner 成員: {current_owner} (隱含)")
                
                # 檢查當前用戶
                cur.execute("SELECT current_user;")
                current_user = cur.fetchone()[0]
                logger.info(f"  - 當前連接用戶: {current_user}")
                
                if current_owner == current_user:
                    logger.info("✅ 當前用戶就是資料庫擁有者！")
                    logger.info("✅ 當前用戶應該有完整的 schema 權限")
                    return True, current_owner, current_user
                else:
                    logger.warning("⚠️ 當前用戶不是資料庫擁有者")
                    logger.info(f"💡 需要將擁有權從 {current_owner} 轉移到 {current_user}")
                    return False, current_owner, current_user
            else:
                logger.error("❌ 找不到目標資料庫")
                return False, None, None
                
        except Exception as e:
            logger.error(f"❌ 檢查資料庫擁有者失敗: {e}")
            return False, None, None

def check_available_superusers(conn):
    """檢查可用的超級用戶"""
    logger.info("\n🔍 檢查可用的超級用戶...")
    
    with conn.cursor() as cur:
        try:
            cur.execute("""
                SELECT usename, usesuper, usecreatedb,
                       CASE WHEN usesuper THEN '🔑 超級用戶'
                            WHEN usecreatedb THEN '📊 數據庫創建者'
                            ELSE '👤 普通用戶' END as user_type
                FROM pg_user 
                WHERE usesuper = true OR usecreatedb = true
                ORDER BY usesuper DESC, usecreatedb DESC;
            """)
            
            privileged_users = cur.fetchall()
            logger.info("📋 具有特權的用戶:")
            
            superusers = []
            db_creators = []
            
            for username, is_super, can_create_db, user_type in privileged_users:
                logger.info(f"  {user_type}: {username}")
                if is_super:
                    superusers.append(username)
                elif can_create_db:
                    db_creators.append(username)
            
            logger.info(f"\n💡 ALTER DATABASE 操作需要:")
            logger.info(f"  - 超級用戶: {', '.join(superusers) if superusers else '無'}")
            logger.info(f"  - 或數據庫創建者: {', '.join(db_creators) if db_creators else '無'}")
            
            return superusers, db_creators
            
        except Exception as e:
            logger.error(f"❌ 檢查超級用戶失敗: {e}")
            return [], []

def main():
    """主函數"""
    logger.info("🚀 資料庫擁有者檢查工具啟動...")
    logger.info("🎯 基於您的指導：pg_database_owner 是隱含的資料庫擁有者")
    
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
        
        # 檢查資料庫擁有者
        is_owner, current_owner, current_user = check_database_ownership(conn)
        
        # 檢查可用的超級用戶
        superusers, db_creators = check_available_superusers(conn)
        
        # 生成解決方案建議
        logger.info("\n" + "="*60)
        logger.info("🎯 解決方案分析:")
        
        if is_owner:
            logger.info("✅ 當前用戶已經是資料庫擁有者")
            logger.info("🧪 建議：直接測試 CREATE TYPE 權限")
        else:
            logger.info("❌ 需要變更資料庫擁有者")
            logger.info(f"🎯 解決方案：ALTER DATABASE \"tradingagents-complete-db\" OWNER TO \"{current_user}\";")
            
            if superusers or db_creators:
                logger.info("💡 可用的執行用戶:")
                for su in superusers:
                    logger.info(f"  - {su} (超級用戶)")
                for dc in db_creators:
                    logger.info(f"  - {dc} (數據庫創建者)")
                    
                logger.info("\n📋 建議執行步驟:")
                logger.info("1. 使用 doadmin 或其他超級用戶連接")
                logger.info("2. 執行 ALTER DATABASE 命令")
                logger.info("3. 驗證 CREATE TYPE 權限")
            else:
                logger.warning("⚠️ 沒有找到可用的超級用戶")
                logger.info("💡 建議聯繫 DigitalOcean 支援")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()