
# 生產環境數據庫連接調試腳本
# 將此腳本內容添加到應用啟動時執行

import os
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def debug_production_db():
    database_url = os.getenv('DATABASE_URL')
    logger.info(f"🔍 生產環境DATABASE_URL: {database_url[:50] if database_url else 'None'}...")
    
    if database_url:
        parsed = urllib.parse.urlparse(database_url)
        logger.info(f"🎯 生產環境數據庫用戶: {parsed.username}")
        
        # 測試實際連接
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            with conn.cursor() as cur:
                cur.execute("SELECT current_user, session_user;")
                current_user, session_user = cur.fetchone()
                logger.info(f"✅ 實際連接用戶: {current_user}")
                
                # 測試CREATE TYPE權限
                cur.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE');")
                can_create = cur.fetchone()[0]
                logger.info(f"🔑 CREATE權限: {'✅' if can_create else '❌'}")
            conn.close()
        except Exception as e:
            logger.error(f"❌ 連接測試失敗: {e}")

# 在應用啟動時調用
debug_production_db()
