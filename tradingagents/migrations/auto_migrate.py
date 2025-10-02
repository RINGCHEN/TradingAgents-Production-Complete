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

        logger.info("✅ 所有遷移檢查完成")

    except Exception as e:
        logger.error(f"❌ 遷移失敗: {e}")
        raise
    finally:
        db.close()

def needs_migration_001(db) -> bool:
    """檢查是否需要執行 migration 001"""
    try:
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'admin_users'
            AND column_name = 'password_hash';
        """))
        return result.fetchone() is None
    except:
        return False

def run_migration_001(db):
    """Migration 001: Add password_hash to admin_users"""

    # 1. 添加 password_hash 欄位
    db.execute(text("""
        ALTER TABLE admin_users
        ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
    """))

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
