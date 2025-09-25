#!/usr/bin/env python3
"""
創建專門的應用數據庫用戶
基於GOOGLE診斷：可能需要一個專門的應用用戶而不是使用doadmin
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
import urllib.parse
import secrets
import string

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_secure_password():
    """生成安全密碼"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(secrets.choice(alphabet) for i in range(16))
    return password

def create_application_user(conn):
    """創建專門的應用用戶"""
    logger.info("🔧 創建專門的TradingAgents應用用戶...")
    
    app_username = "tradingagents_app"
    app_password = generate_secure_password()
    
    with conn.cursor() as cur:
        try:
            # 創建用戶
            logger.info(f"📝 創建用戶: {app_username}")
            cur.execute(f"""
                CREATE USER {app_username} WITH PASSWORD '{app_password}';
            """)
            
            # 授予基本權限
            logger.info("🔑 授予基本數據庫權限...")
            cur.execute(f"GRANT CONNECT ON DATABASE defaultdb TO {app_username};")
            
            # 授予public schema的完整權限
            logger.info("🏠 授予public schema完整權限...")
            cur.execute(f"ALTER SCHEMA public OWNER TO {app_username};")
            cur.execute(f"GRANT ALL PRIVILEGES ON SCHEMA public TO {app_username};")
            cur.execute(f"GRANT CREATE ON SCHEMA public TO {app_username};")
            
            # 設置默認權限
            logger.info("⚙️ 設置默認權限...")
            default_privileges = [
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {app_username};",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {app_username};",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO {app_username};",
                f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {app_username};"
            ]
            
            for privilege in default_privileges:
                cur.execute(privilege)
            
            # 測試CREATE TYPE權限
            logger.info("🧪 測試CREATE TYPE權限...")
            test_type_name = "test_app_user_enum"
            cur.execute(f"CREATE TYPE {test_type_name} AS ENUM ('test1', 'test2');")
            cur.execute(f"DROP TYPE {test_type_name};")
            
            conn.commit()
            logger.info("✅ 應用用戶創建成功！")
            
            # 生成新的DATABASE_URL
            db_config = parse_database_url(os.getenv('DATABASE_URL'))
            new_database_url = f"postgresql://{app_username}:{app_password}@{db_config['host']}:{db_config['port']}/{db_config['database']}?sslmode=require"
            
            logger.info("\n" + "="*60)
            logger.info("🎯 新的應用數據庫配置:")
            logger.info(f"用戶名: {app_username}")
            logger.info(f"密碼: {app_password}")
            logger.info("\n🔧 請將以下DATABASE_URL設置到DigitalOcean App Platform:")
            logger.info(f"DATABASE_URL={new_database_url}")
            
            # 保存到文件
            with open('new_database_credentials.txt', 'w') as f:
                f.write(f"TradingAgents 專用數據庫用戶\n")
                f.write(f"創建時間: {logging.Formatter().formatTime(logging.LogRecord('', 0, '', 0, '', (), None))}\n\n")
                f.write(f"用戶名: {app_username}\n")
                f.write(f"密碼: {app_password}\n")
                f.write(f"DATABASE_URL: {new_database_url}\n\n")
                f.write("設置步驟:\n")
                f.write("1. 登入DigitalOcean控制台\n")
                f.write("2. Apps → twshocks-app → Settings → Environment Variables\n")
                f.write("3. 編輯DATABASE_URL，替換為上面的新URL\n")
                f.write("4. 保存並重新部署\n")
            
            logger.info("📄 憑證已保存到: new_database_credentials.txt")
            
            return app_username, app_password, new_database_url
            
        except Exception as e:
            logger.error(f"❌ 創建應用用戶失敗: {e}")
            conn.rollback()
            return None, None, None

def parse_database_url(database_url):
    """解析數據庫URL"""
    parsed = urllib.parse.urlparse(database_url)
    return {
        'host': parsed.hostname,
        'port': parsed.port,
        'database': parsed.path[1:] if parsed.path else 'defaultdb',
        'user': parsed.username,
        'password': parsed.password
    }

def main():
    """主函數"""
    logger.info("🚀 創建TradingAgents專用數據庫用戶...")
    logger.info("🎯 基於GOOGLE診斷：可能需要專門的應用用戶")
    
    # 嘗試從臨時文件讀取環境變數
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
        db_config = parse_database_url(database_url)
        logger.info(f"📡 使用超級用戶連接: {db_config['user']}")
        
        conn = psycopg2.connect(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            sslmode='require'
        )
        
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # 創建應用用戶
        username, password, new_url = create_application_user(conn)
        
        if username:
            logger.info("🎉 專用應用用戶創建完成！")
            logger.info("📋 下一步：將新的DATABASE_URL設置到App Platform")
        else:
            logger.error("❌ 用戶創建失敗")
            
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()