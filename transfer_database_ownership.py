#!/usr/bin/env python3
"""
轉移資料庫擁有權
使用 doadmin 將資料庫擁有權轉移給應用用戶
基於您的指導：pg_database_owner 成員身份通過成為資料庫擁有者獲得
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

def transfer_database_ownership(admin_conn, target_user, database_name):
    """轉移資料庫擁有權"""
    logger.info(f"🔄 轉移資料庫擁有權...")
    logger.info(f"  - 資料庫: {database_name}")
    logger.info(f"  - 新擁有者: {target_user}")
    
    with admin_conn.cursor() as cur:
        try:
            # 檢查當前管理用戶權限
            cur.execute("SELECT current_user, usesuper, usecreatedb FROM pg_user WHERE usename = current_user;")
            current_admin, is_super, can_create_db = cur.fetchone()
            logger.info(f"📋 當前管理用戶權限:")
            logger.info(f"  - 用戶: {current_admin}")
            logger.info(f"  - 超級用戶: {'✅' if is_super else '❌'}")
            logger.info(f"  - 創建數據庫: {'✅' if can_create_db else '❌'}")
            
            if not (is_super or can_create_db):
                logger.error("❌ 當前用戶沒有足夠權限執行 ALTER DATABASE")
                return False
            
            # 檢查目標用戶是否存在
            cur.execute("SELECT usename FROM pg_user WHERE usename = %s;", (target_user,))
            user_exists = cur.fetchone()
            
            if not user_exists:
                logger.error(f"❌ 目標用戶 '{target_user}' 不存在")
                return False
            
            logger.info(f"✅ 目標用戶 '{target_user}' 存在")
            
            # 執行擁有權轉移
            logger.info("🎯 執行 ALTER DATABASE OWNER TO...")
            alter_sql = f'ALTER DATABASE "{database_name}" OWNER TO "{target_user}";'
            logger.info(f"📝 SQL: {alter_sql}")
            
            cur.execute(alter_sql)
            admin_conn.commit()
            
            logger.info("✅ 資料庫擁有權轉移成功！")
            
            # 驗證轉移結果
            logger.info("🔍 驗證擁有權轉移結果...")
            cur.execute("""
                SELECT datname, pg_catalog.pg_get_userbyid(datdba) AS owner 
                FROM pg_database 
                WHERE datname = %s;
            """, (database_name,))
            
            result = cur.fetchone()
            if result:
                db_name, new_owner = result
                logger.info(f"📊 驗證結果:")
                logger.info(f"  - 資料庫: {db_name}")
                logger.info(f"  - 新擁有者: {new_owner}")
                
                if new_owner == target_user:
                    logger.info("🎊 擁有權轉移驗證成功！")
                    logger.info(f"✅ {target_user} 現在是 pg_database_owner 的隱含成員")
                    return True
                else:
                    logger.error(f"❌ 擁有權轉移驗證失敗，實際擁有者: {new_owner}")
                    return False
            else:
                logger.error("❌ 無法查詢資料庫擁有者")
                return False
                
        except Exception as e:
            logger.error(f"❌ 轉移資料庫擁有權失敗: {e}")
            admin_conn.rollback()
            return False

def test_create_type_with_new_owner(app_conn):
    """使用新擁有者身份測試 CREATE TYPE"""
    logger.info("🧪 測試新擁有者的 CREATE TYPE 權限...")
    
    with app_conn.cursor() as cur:
        try:
            # 檢查當前用戶和權限
            cur.execute("SELECT current_user;")
            current_user = cur.fetchone()[0]
            logger.info(f"📋 當前測試用戶: {current_user}")
            
            # 檢查 schema 權限
            cur.execute("""
                SELECT 
                    has_schema_privilege(current_user, 'public', 'CREATE') as can_create,
                    has_schema_privilege(current_user, 'public', 'USAGE') as can_use
            """)
            perms = cur.fetchone()
            logger.info(f"  - CREATE權限: {'✅' if perms[0] else '❌'}")
            logger.info(f"  - USAGE權限: {'✅' if perms[1] else '❌'}")
            
            # 測試 CREATE TYPE
            test_type_name = f"test_enum_owner_{int(datetime.now().timestamp())}"
            logger.info(f"🎯 創建測試類型: {test_type_name}")
            
            cur.execute(f"CREATE TYPE {test_type_name} AS ENUM ('owner_test', 'success');")
            logger.info("✅ CREATE TYPE 成功執行！")
            
            # 清理測試類型
            cur.execute(f"DROP TYPE {test_type_name};")
            app_conn.commit()
            
            logger.info("🎊 CREATE TYPE 權限測試完全成功！")
            logger.info("🏆 GOOGLE 診斷問題已完全解決！")
            return True
            
        except Exception as e:
            logger.error(f"❌ CREATE TYPE 權限測試失敗: {e}")
            app_conn.rollback()
            return False

def main():
    """主函數"""
    logger.info("🚀 資料庫擁有權轉移工具啟動...")
    logger.info("🎯 基於您的指導：通過成為資料庫擁有者獲得 pg_database_owner 身份")
    
    # 讀取 doadmin 連接資訊
    admin_database_url = None
    try:
        with open('.env.doadmin.new', 'r') as f:
            line = f.read().strip()
            if line.startswith('DATABASE_URL='):
                admin_database_url = line.split('DATABASE_URL=', 1)[1]
                logger.info("📄 從 doadmin 配置文件讀取 DATABASE_URL")
    except FileNotFoundError:
        logger.error("❌ 找不到 doadmin 配置文件")
        sys.exit(1)
    
    # 讀取應用用戶連接資訊
    app_database_url = None
    try:
        with open('.env.temp', 'r') as f:
            line = f.read().strip()
            if line.startswith('DATABASE_URL='):
                app_database_url = line.split('DATABASE_URL=', 1)[1]
                logger.info("📄 從應用用戶配置文件讀取 DATABASE_URL")
    except FileNotFoundError:
        logger.error("❌ 找不到應用用戶配置文件")
        sys.exit(1)
    
    if not admin_database_url or not app_database_url:
        logger.error("❌ 無法讀取必要的 DATABASE_URL")
        sys.exit(1)
    
    try:
        # 解析配置
        admin_config = parse_database_url(admin_database_url)
        app_config = parse_database_url(app_database_url)
        
        admin_user = admin_config['user']
        target_user = app_config['user']
        database_name = app_config['database']
        
        logger.info(f"📋 轉移配置:")
        logger.info(f"  - 管理用戶: {admin_user}")
        logger.info(f"  - 目標用戶: {target_user}")
        logger.info(f"  - 目標資料庫: {database_name}")
        
        # 連接到管理用戶
        logger.info("🔌 建立管理用戶連接...")
        admin_conn = psycopg2.connect(
            host=admin_config['host'],
            port=admin_config['port'],
            database=admin_config['database'],
            user=admin_config['user'],
            password=admin_config['password'],
            sslmode='require'
        )
        admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        logger.info(f"✅ {admin_user} 連接成功")
        
        # 執行擁有權轉移
        if transfer_database_ownership(admin_conn, target_user, database_name):
            logger.info("🔄 切換到應用用戶進行權限驗證...")
            admin_conn.close()
            
            # 連接到應用用戶
            app_conn = psycopg2.connect(
                host=app_config['host'],
                port=app_config['port'],
                database=app_config['database'],
                user=app_config['user'],
                password=app_config['password'],
                sslmode='require'
            )
            app_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info(f"✅ {target_user} 連接成功")
            
            # 測試 CREATE TYPE 權限
            if test_create_type_with_new_owner(app_conn):
                logger.info("\n" + "="*60)
                logger.info("🏆 完全成功！資料庫權限問題已解決！")
                logger.info("📋 後續步驟:")
                logger.info("1. 重新部署 TradingAgents 應用")
                logger.info("2. 驗證 AI 模型初始化正常")
                logger.info("3. 確認不再有 'permission denied' 錯誤")
                logger.info("✨ AI 智能路由器和模型能力資料庫將正常工作")
            else:
                logger.error("❌ CREATE TYPE 測試仍然失敗")
                
            app_conn.close()
        else:
            logger.error("❌ 資料庫擁有權轉移失敗")
            admin_conn.close()
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ 過程中發生錯誤: {e}")
        
        # 檢查是否是認證錯誤
        if "authentication failed" in str(e):
            logger.info("💡 doadmin 密碼可能不正確")
            logger.info("🔧 建議：")
            logger.info("  1. 檢查 DigitalOcean 控制台中的資料庫用戶密碼")
            logger.info("  2. 重新生成 doadmin 用戶密碼")
            logger.info("  3. 或使用其他具有管理權限的用戶")
        
        sys.exit(1)

if __name__ == "__main__":
    main()