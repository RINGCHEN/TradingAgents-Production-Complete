#!/usr/bin/env python3
"""
自動資料庫遷移
在應用啟動時自動執行
"""

import os
import logging
from sqlalchemy import text
from ..database.database import SessionLocal
import bcrypt

logger = logging.getLogger(__name__)

def run_migrations():
    """執行所有待執行的遷移"""

    db = SessionLocal()
    try:
        logger.info("🔄 開始檢查資料庫遷移...")

        # Migration 001: Add password_hash to admin_users
        if needs_migration_001(db):
            logger.info("📋 執行 Migration 001: Add password_hash to admin_users")
            run_migration_001(db)
            logger.info("✅ Migration 001 完成")
        else:
            logger.info("⏭️  Migration 001 已執行過，跳過")

        # Migration 002: Add authentication fields to users table
        if needs_migration_002(db):
            logger.info("📋 執行 Migration 002: Add authentication fields to users")
            run_migration_002(db)
            logger.info("✅ Migration 002 完成")
        else:
            logger.info("⏭️  Migration 002 已執行過，跳過")

        logger.info("✅ 所有遷移檢查完成")

    except Exception as e:
        logger.error(f"❌ 遷移失敗: {e}")
        raise
    finally:
        db.close()

def needs_migration_001(db) -> bool:
    """檢查是否需要執行 migration 001"""
    try:
        # 檢查 admin_users 表是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'admin_users'
            );
        """))
        table_exists = result.fetchone()[0]

        if not table_exists:
            return True  # 需要創建表

        # 檢查 password_hash 欄位是否存在
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'admin_users'
            AND column_name = 'password_hash';
        """))
        return result.fetchone() is None
    except:
        return True  # 出錯時保守處理，執行遷移

def run_migration_001(db):
    """Migration 001: Create admin_users table and add password_hash"""

    # 0. 確保 pgcrypto 擴展存在（gen_random_uuid 需要）
    db.execute(text("""
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
    """))
    logger.info("✅ pgcrypto 擴展已啟用")

    # 1. 創建 admin_users 表（如果不存在）
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            role VARCHAR(50) DEFAULT 'admin',
            permissions TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            password_hash VARCHAR(255)
        );
    """))
    logger.info("✅ admin_users 表已創建/確認存在")

    # 2. 添加 password_hash 欄位（如果表已存在但沒有此欄位）
    db.execute(text("""
        ALTER TABLE admin_users
        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
    """))
    logger.info("✅ password_hash 欄位已添加")

    # 2. 生成密碼 hash
    admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    manager_hash = bcrypt.hashpw('manager123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # 3. 創建測試管理員帳號
    db.execute(text("""
        INSERT INTO admin_users (email, name, role, permissions, password_hash, is_active)
        VALUES
            (:admin_email, :admin_name, :admin_role, :admin_perms, :admin_hash, true),
            (:manager_email, :manager_name, :manager_role, :manager_perms, :manager_hash, true)
        ON CONFLICT (email)
        DO UPDATE SET
            name = EXCLUDED.name,
            role = EXCLUDED.role,
            permissions = EXCLUDED.permissions,
            password_hash = EXCLUDED.password_hash,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP;
    """), {
        'admin_email': 'admin@example.com',
        'admin_name': 'Admin User',
        'admin_role': 'admin',
        'admin_perms': ['user_management', 'system_config', 'analytics', 'reports'],
        'admin_hash': admin_hash,
        'manager_email': 'manager@example.com',
        'manager_name': 'Manager User',
        'manager_role': 'manager',
        'manager_perms': ['user_management', 'analytics'],
        'manager_hash': manager_hash
    })

    db.commit()

    logger.info("✅ 測試管理員帳號已創建:")
    logger.info("   - admin@example.com / admin123")
    logger.info("   - manager@example.com / manager123")

def needs_migration_002(db) -> bool:
    """檢查是否需要執行 migration 002 - 添加用戶認證欄位"""
    try:
        # 檢查 users 表是否存在
        result = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'users'
            );
        """))
        table_exists = result.fetchone()[0]

        if not table_exists:
            logger.warning("⚠️  users 表不存在，跳過 Migration 002")
            return False  # 用戶表不存在，不執行遷移

        # 檢查必需的認證欄位是否存在
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name IN ('username', 'password_hash', 'uuid', 'membership_tier', 'status', 'email_verified')
        """))
        existing_columns = {row[0] for row in result.fetchall()}
        required_columns = {'username', 'password_hash', 'uuid', 'membership_tier', 'status', 'email_verified'}

        missing_columns = required_columns - existing_columns
        if missing_columns:
            logger.info(f"📋 發現缺失欄位: {', '.join(missing_columns)}")
            return True

        return False
    except Exception as e:
        logger.error(f"檢查 Migration 002 時出錯: {e}")
        return True  # 出錯時保守處理，執行遷移

def run_migration_002(db):
    """Migration 002: Add authentication fields to users table"""

    logger.info("開始執行 Migration 002: 添加用戶認證欄位")

    # 1. 添加缺失的欄位
    db.execute(text("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS username VARCHAR(100),
        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
        ADD COLUMN IF NOT EXISTS uuid UUID DEFAULT gen_random_uuid(),
        ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(20) DEFAULT 'free',
        ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
        ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;
    """))
    logger.info("✅ 認證欄位已添加")

    # 2. 創建索引（如果不存在）
    try:
        db.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
        """))
        logger.info("✅ username 唯一索引已創建")
    except Exception as e:
        if "already exists" not in str(e).lower():
            logger.warning(f"創建 username 索引失敗: {e}")

    try:
        db.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);
        """))
        logger.info("✅ uuid 索引已創建")
    except Exception as e:
        if "already exists" not in str(e).lower():
            logger.warning(f"創建 uuid 索引失敗: {e}")

    # 3. 更新現有用戶的數據
    db.execute(text("""
        UPDATE users
        SET uuid = id
        WHERE uuid IS NULL;
    """))
    logger.info("✅ 現有用戶的 UUID 已更新")

    db.execute(text("""
        UPDATE users
        SET membership_tier = LOWER(tier_type)
        WHERE membership_tier IS NULL OR membership_tier = 'free';
    """))
    logger.info("✅ 現有用戶的 membership_tier 已更新")

    db.execute(text("""
        UPDATE users
        SET status = 'active'
        WHERE status IS NULL;
    """))
    logger.info("✅ 現有用戶的 status 已更新")

    # 4. 添加列註釋
    try:
        db.execute(text("""
            COMMENT ON COLUMN users.username IS 'User login username (3-50 characters)';
        """))
        db.execute(text("""
            COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
        """))
        db.execute(text("""
            COMMENT ON COLUMN users.uuid IS 'User UUID for API identification';
        """))
        db.execute(text("""
            COMMENT ON COLUMN users.membership_tier IS 'User membership level: free, gold, diamond';
        """))
        db.execute(text("""
            COMMENT ON COLUMN users.status IS 'Account status: active, suspended, deleted';
        """))
        db.execute(text("""
            COMMENT ON COLUMN users.email_verified IS 'Email verification status';
        """))
        logger.info("✅ 列註釋已添加")
    except Exception as e:
        logger.warning(f"添加列註釋失敗（非關鍵）: {e}")

    db.commit()
    logger.info("✅ Migration 002 執行完成")
