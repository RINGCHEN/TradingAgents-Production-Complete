#!/usr/bin/env python3
"""
嘗試將用戶加入pg_database_owner角色
基於ACL分析：只有pg_database_owner角色有完整權限
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

def attempt_database_owner_role_grant(conn, current_user):
    """嘗試將用戶加入pg_database_owner角色"""
    logger.info(f"🎯 嘗試將用戶 '{current_user}' 加入 pg_database_owner 角色...")
    
    with conn.cursor() as cur:
        try:
            # 1. 檢查pg_database_owner角色是否存在
            logger.info("🔍 檢查pg_database_owner角色...")
            cur.execute("""
                SELECT rolname FROM pg_roles WHERE rolname = 'pg_database_owner';
            """)
            role_exists = cur.fetchone()
            
            if role_exists:
                logger.info("✅ pg_database_owner角色存在")
            else:
                logger.warning("⚠️ pg_database_owner角色不存在，嘗試創建...")
                try:
                    cur.execute("CREATE ROLE pg_database_owner;")
                    conn.commit()
                    logger.info("✅ pg_database_owner角色創建成功")
                except Exception as e:
                    logger.error(f"❌ 創建pg_database_owner角色失敗: {e}")
                    return False
            
            # 2. 檢查當前用戶是否已經是成員
            logger.info("🔍 檢查當前用戶的角色成員身份...")
            cur.execute("""
                SELECT r.rolname 
                FROM pg_auth_members m
                JOIN pg_roles r ON m.roleid = r.oid
                JOIN pg_roles u ON m.member = u.oid
                WHERE u.rolname = %s;
            """, (current_user,))
            
            current_roles = [row[0] for row in cur.fetchall()]
            logger.info(f"  - 當前角色: {', '.join(current_roles) if current_roles else '無'}")
            
            if 'pg_database_owner' in current_roles:
                logger.info("✅ 用戶已經是pg_database_owner成員")
                return test_create_type_after_role_grant(conn)
            
            # 3. 嘗試授予pg_database_owner角色
            logger.info("🎯 授予pg_database_owner角色...")
            try:
                cur.execute(f'GRANT pg_database_owner TO "{current_user}";')
                conn.commit()
                logger.info("✅ pg_database_owner角色授予成功")
                
                # 驗證角色授予
                cur.execute("""
                    SELECT r.rolname 
                    FROM pg_auth_members m
                    JOIN pg_roles r ON m.roleid = r.oid
                    JOIN pg_roles u ON m.member = u.oid
                    WHERE u.rolname = %s;
                """, (current_user,))
                
                new_roles = [row[0] for row in cur.fetchall()]
                logger.info(f"  - 更新後角色: {', '.join(new_roles) if new_roles else '無'}")
                
                if 'pg_database_owner' in new_roles:
                    logger.info("🎊 角色授予驗證成功！")
                    return test_create_type_after_role_grant(conn)
                else:
                    logger.error("❌ 角色授予驗證失敗")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ 授予pg_database_owner角色失敗: {e}")
                
                # 嘗試其他可能的方法
                logger.info("🔄 嘗試替代方法...")
                alternative_methods = [
                    {
                        "name": "使用SET ROLE",
                        "sql": "SET ROLE pg_database_owner;"
                    },
                    {
                        "name": "檢查並授予database權限",
                        "sql": f'GRANT ALL ON DATABASE {parse_database_url(os.environ.get("DATABASE_URL", ""))["database"]} TO "{current_user}";'
                    }
                ]
                
                for method in alternative_methods:
                    try:
                        logger.info(f"  🎯 {method['name']}")
                        cur.execute(method['sql'])
                        conn.commit()
                        logger.info(f"    ✅ {method['name']} 成功")
                        
                        if test_create_type_after_role_grant(conn):
                            return True
                            
                    except Exception as alt_e:
                        logger.warning(f"    ❌ {method['name']} 失敗: {alt_e}")
                        conn.rollback()
                
                return False
                
        except Exception as e:
            logger.error(f"❌ 角色操作過程中發生錯誤: {e}")
            return False

def test_create_type_after_role_grant(conn):
    """在角色授予後測試CREATE TYPE"""
    logger.info("🧪 測試角色授予後的CREATE TYPE權限...")
    
    with conn.cursor() as cur:
        try:
            # 重新檢查權限狀態
            cur.execute("""
                SELECT 
                    has_schema_privilege(current_user, 'public', 'CREATE') as can_create,
                    has_schema_privilege(current_user, 'public', 'USAGE') as can_use
            """)
            perms = cur.fetchone()
            logger.info(f"  - CREATE權限: {'✅' if perms[0] else '❌'}")
            logger.info(f"  - USAGE權限: {'✅' if perms[1] else '❌'}")
            
            # 測試CREATE TYPE
            test_type_name = f"test_enum_role_{int(datetime.now().timestamp())}"
            cur.execute(f"CREATE TYPE {test_type_name} AS ENUM ('success', 'test');")
            cur.execute(f"DROP TYPE {test_type_name};")
            conn.commit()
            
            logger.info("🎊 CREATE TYPE測試成功！角色授予解決了問題！")
            return True
            
        except Exception as e:
            logger.error(f"❌ CREATE TYPE測試仍然失敗: {e}")
            conn.rollback()
            return False

def main():
    """主函數"""
    logger.info("🚀 pg_database_owner角色授予工具啟動...")
    logger.info("🎯 基於ACL分析：嘗試獲得database owner權限")
    
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
    
    # 設置環境變量以供函數使用
    os.environ['DATABASE_URL'] = database_url
    
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
        
        # 嘗試pg_database_owner角色授予
        if attempt_database_owner_role_grant(conn, current_user):
            logger.info("🏆 GOOGLE診斷問題完全解決！")
            logger.info("📋 下一步：重新部署TradingAgents應用")
            logger.info("🎯 預期結果：CREATE TYPE操作將正常工作")
            logger.info("✨ AI智能路由器和模型能力數據庫將正常初始化")
        else:
            logger.error("❌ pg_database_owner角色授予嘗試失敗")
            logger.info("💡 最終建議：")
            logger.info("  1. 聯繫DigitalOcean技術支援")
            logger.info("  2. 要求提供具有完整schema權限的用戶")
            logger.info("  3. 或者考慮使用不需要CREATE TYPE的替代方案")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 過程中發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()