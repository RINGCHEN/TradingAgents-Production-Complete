#!/usr/bin/env python3
"""
TradingAgents Production Complete - 新資料庫初始化腳本

此腳本將在新的DigitalOcean PostgreSQL資料庫中創建所有必要的表和數據結構。

使用方法:
1. 創建新的DigitalOcean PostgreSQL資料庫
2. 更新 DATABASE_URL 環境變數
3. 執行此腳本進行初始化

作者：天工 (TianGong) + Claude Code
日期：2025-09-06
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from datetime import datetime
import json

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_url():
    """獲取資料庫連接URL"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL 環境變數未設置")
        sys.exit(1)
    return database_url

def create_database_tables(conn):
    """創建所有必要的資料庫表"""
    
    # 定義所有表的創建語句
    table_definitions = {
        # 用戶系統
        'users': '''
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                google_id VARCHAR(255) UNIQUE,
                tier_type VARCHAR(20) DEFAULT 'FREE' CHECK (tier_type IN ('FREE', 'GOLD', 'DIAMOND')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                api_quota_used INTEGER DEFAULT 0,
                api_quota_limit INTEGER DEFAULT 10
            )
        ''',
        
        # 管理員系統
        'admin_users': '''
            CREATE TABLE IF NOT EXISTS admin_users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'admin',
                permissions TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''',
        
        # 支付系統
        'payments': '''
            CREATE TABLE IF NOT EXISTS payments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                tier_type VARCHAR(20) NOT NULL CHECK (tier_type IN ('GOLD', 'DIAMOND')),
                amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'TWD',
                status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        # PayUni交易記錄
        'payment_transactions': '''
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                payment_id UUID REFERENCES payments(id),
                order_number VARCHAR(255) UNIQUE NOT NULL,
                merchant_order_no VARCHAR(255),
                trade_no VARCHAR(255),
                payuni_status VARCHAR(50),
                webhook_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        # API使用統計
        'api_usages': '''
            CREATE TABLE IF NOT EXISTS api_usages (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                endpoint VARCHAR(255) NOT NULL,
                method VARCHAR(10) NOT NULL,
                status_code INTEGER,
                response_time FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT,
                ip_address INET
            )
        ''',
        
        # AI分析歷史
        'analysis_history': '''
            CREATE TABLE IF NOT EXISTS analysis_history (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                stock_symbol VARCHAR(20) NOT NULL,
                analysis_type VARCHAR(50) NOT NULL,
                analyst_name VARCHAR(100),
                request_data JSONB,
                result_data JSONB,
                status VARCHAR(20) DEFAULT 'completed',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        # 交易信號
        'trading_signals': '''
            CREATE TABLE IF NOT EXISTS trading_signals (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                stock_symbol VARCHAR(20) NOT NULL,
                signal_type VARCHAR(20) NOT NULL CHECK (signal_type IN ('BUY', 'SELL', 'HOLD')),
                confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
                analyst_source VARCHAR(100),
                reasoning TEXT,
                target_price DECIMAL(10,2),
                stop_loss DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''',
        
        # 系統設定
        'system_settings': '''
            CREATE TABLE IF NOT EXISTS system_settings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                key VARCHAR(255) UNIQUE NOT NULL,
                value JSONB NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        
        # 審計日誌
        'audit_logs': '''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES users(id),
                admin_user_id UUID REFERENCES admin_users(id),
                action VARCHAR(100) NOT NULL,
                resource VARCHAR(100),
                resource_id VARCHAR(255),
                details JSONB,
                ip_address INET,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
    }
    
    cursor = conn.cursor()
    
    try:
        # 創建所有表
        for table_name, create_sql in table_definitions.items():
            logger.info(f"創建表: {table_name}")
            cursor.execute(create_sql)
            
        # 創建必要的索引
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_tier_type ON users(tier_type)",
            "CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)",
            "CREATE INDEX IF NOT EXISTS idx_payment_transactions_order_number ON payment_transactions(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_api_usages_user_id ON api_usages(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_api_usages_timestamp ON api_usages(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_user_id ON analysis_history(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_analysis_history_stock_symbol ON analysis_history(stock_symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_stock_symbol ON trading_signals(stock_symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trading_signals_created_at ON trading_signals(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp)"
        ]
        
        logger.info("創建索引...")
        for index_sql in indexes:
            cursor.execute(index_sql)
            
        # 插入預設系統設定
        default_settings = [
            ('payuni_merchant_id', '"U03823060"', 'PayUni商店代號'),
            ('api_rate_limits', '{"FREE": 10, "GOLD": 100, "DIAMOND": 1000}', 'API調用頻率限制'),
            ('system_maintenance', 'false', '系統維護模式'),
            ('ai_models_enabled', 'true', 'AI模型服務啟用狀態')
        ]
        
        logger.info("插入預設系統設定...")
        for key, value, description in default_settings:
            cursor.execute("""
                INSERT INTO system_settings (key, value, description) 
                VALUES (%s, %s, %s) 
                ON CONFLICT (key) DO UPDATE SET 
                value = EXCLUDED.value, 
                updated_at = CURRENT_TIMESTAMP
            """, (key, value, description))
            
        # 創建測試管理員帳戶
        logger.info("創建測試管理員帳戶...")
        cursor.execute("""
            INSERT INTO admin_users (email, name, role, permissions) 
            VALUES (%s, %s, %s, %s) 
            ON CONFLICT (email) DO NOTHING
        """, (
            'admin@tradingagents.com',
            'System Administrator', 
            'super_admin',
            ['all']
        ))
        
        conn.commit()
        logger.info("✅ 資料庫初始化完成！")
        
        # 驗證創建結果
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        logger.info(f"📊 成功創建 {len(tables)} 個資料表:")
        for table in tables:
            logger.info(f"  - {table[0]}")
            
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()

def verify_database_health(conn):
    """驗證資料庫健康狀態"""
    cursor = conn.cursor()
    try:
        # 檢查連接
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        logger.info(f"✅ PostgreSQL版本: {version}")
        
        # 檢查表數量
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        logger.info(f"✅ 資料表數量: {table_count}")
        
        # 檢查系統設定
        cursor.execute("SELECT COUNT(*) FROM system_settings")
        settings_count = cursor.fetchone()[0]
        logger.info(f"✅ 系統設定: {settings_count} 項")
        
        return True
        
    except Exception as e:
        logger.error(f"資料庫健康檢查失敗: {str(e)}")
        return False
    finally:
        cursor.close()

def main():
    """主函數"""
    logger.info("🚀 開始初始化 TradingAgents Production Complete 資料庫...")
    
    # 獲取資料庫連接
    database_url = get_database_url()
    logger.info(f"📡 連接資料庫: {database_url.split('@')[1] if '@' in database_url else '***'}")
    
    try:
        # 連接資料庫
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # 初始化資料庫結構
        create_database_tables(conn)
        
        # 驗證健康狀態
        if verify_database_health(conn):
            logger.info("🎉 資料庫初始化成功完成！")
            logger.info("📋 下一步:")
            logger.info("  1. 更新DigitalOcean App的環境變數")
            logger.info("  2. 重新部署應用")
            logger.info("  3. 執行 verify_deployment.py 驗證")
        else:
            logger.error("❌ 資料庫健康檢查失敗")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 初始化失敗: {str(e)}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()