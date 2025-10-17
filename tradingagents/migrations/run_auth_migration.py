#!/usr/bin/env python3
"""
執行用戶認證欄位 Migration
Date: 2025-10-17
Purpose: 添加 password_hash, username 等欄位到 users 表
"""

import os
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tradingagents.database.database import SessionLocal
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """執行 migration"""
    db = SessionLocal()

    try:
        # 讀取 SQL migration 文件
        migration_file = Path(__file__).parent / "add_user_auth_fields.sql"

        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 分割成多個語句（以分號分隔）
        statements = [s.strip() for s in migration_sql.split(';') if s.strip() and not s.strip().startswith('--')]

        logger.info(f"開始執行 migration，共 {len(statements)} 個語句...")

        for i, statement in enumerate(statements, 1):
            try:
                logger.info(f"執行語句 {i}/{len(statements)}")
                db.execute(text(statement))
                db.commit()
            except Exception as e:
                # 如果是 "column already exists" 錯誤，繼續執行
                if "already exists" in str(e).lower():
                    logger.warning(f"欄位已存在，跳過: {str(e)}")
                    db.rollback()
                    continue
                else:
                    logger.error(f"執行失敗: {str(e)}")
                    db.rollback()
                    raise

        logger.info("✅ Migration 執行完成！")

        # 驗證欄位已添加
        result = db.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'users'
            AND column_name IN ('username', 'password_hash', 'uuid', 'membership_tier', 'status', 'email_verified')
        """))

        columns = [row[0] for row in result.fetchall()]
        logger.info(f"驗證欄位: {columns}")

        required_columns = ['username', 'password_hash', 'uuid', 'membership_tier', 'status', 'email_verified']
        missing_columns = [col for col in required_columns if col not in columns]

        if missing_columns:
            logger.error(f"❌ 以下欄位未成功添加: {missing_columns}")
            return False
        else:
            logger.info("✅ 所有必需欄位已成功添加！")
            return True

    except Exception as e:
        logger.error(f"❌ Migration 失敗: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
