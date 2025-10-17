#!/usr/bin/env python3
"""
應用啟動時自動執行的 Migration 檢查器
Date: 2025-10-17
Purpose: 自動檢查並添加缺失的資料庫欄位

這個模組會在應用啟動時自動運行，確保資料庫結構與代碼需求一致。
"""

import logging
from typing import List, Tuple
from sqlalchemy import text
from pathlib import Path

logger = logging.getLogger(__name__)

class AutoMigrator:
    """自動 Migration 執行器"""

    REQUIRED_USER_COLUMNS = [
        ('username', 'VARCHAR(100)', True),  # (column_name, data_type, unique)
        ('password_hash', 'VARCHAR(255)', False),
        ('uuid', 'UUID', False),
        ('membership_tier', 'VARCHAR(20)', False),
        ('status', 'VARCHAR(20)', False),
        ('email_verified', 'BOOLEAN', False),
    ]

    def __init__(self, db_session):
        self.db = db_session

    def check_and_migrate(self) -> bool:
        """檢查並執行必要的 migration"""
        try:
            logger.info("開始檢查資料庫結構...")

            # 檢查 users 表是否存在
            if not self._table_exists('users'):
                logger.error("users 表不存在，無法執行 migration")
                return False

            # 檢查並添加缺失的欄位
            missing_columns = self._get_missing_columns()

            if not missing_columns:
                logger.info("✅ 所有必需欄位已存在")
                return True

            logger.info(f"發現 {len(missing_columns)} 個缺失欄位，開始添加...")

            for column_name, data_type, is_unique in missing_columns:
                self._add_column(column_name, data_type, is_unique)

            # 添加預設值
            self._set_default_values()

            logger.info("✅ Migration 完成")
            return True

        except Exception as e:
            logger.error(f"Migration 失敗: {str(e)}", exc_info=True)
            return False

    def _table_exists(self, table_name: str) -> bool:
        """檢查表是否存在"""
        try:
            result = self.db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = :table_name
                )
            """), {"table_name": table_name})

            return result.fetchone()[0]
        except Exception as e:
            logger.error(f"檢查表存在性失敗: {str(e)}")
            return False

    def _get_missing_columns(self) -> List[Tuple[str, str, bool]]:
        """獲取缺失的欄位列表"""
        try:
            # 獲取現有欄位
            result = self.db.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'users'
            """))

            existing_columns = {row[0] for row in result.fetchall()}

            # 找出缺失的欄位
            missing = [
                (name, dtype, unique)
                for name, dtype, unique in self.REQUIRED_USER_COLUMNS
                if name not in existing_columns
            ]

            return missing

        except Exception as e:
            logger.error(f"獲取欄位列表失敗: {str(e)}")
            return []

    def _add_column(self, column_name: str, data_type: str, is_unique: bool):
        """添加欄位"""
        try:
            # 構建 ALTER TABLE 語句
            sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {column_name} {data_type}"

            # 添加預設值
            if column_name == 'uuid':
                sql += " DEFAULT gen_random_uuid()"
            elif column_name == 'membership_tier':
                sql += " DEFAULT 'free'"
            elif column_name == 'status':
                sql += " DEFAULT 'active'"
            elif column_name == 'email_verified':
                sql += " DEFAULT false"

            logger.info(f"添加欄位: {column_name}")
            self.db.execute(text(sql))
            self.db.commit()

            # 如果需要唯一索引
            if is_unique:
                try:
                    index_sql = f"CREATE UNIQUE INDEX IF NOT EXISTS idx_users_{column_name} ON users({column_name})"
                    self.db.execute(text(index_sql))
                    self.db.commit()
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"創建唯一索引失敗: {str(e)}")
                    self.db.rollback()

            logger.info(f"✅ 欄位 {column_name} 添加成功")

        except Exception as e:
            logger.error(f"添加欄位 {column_name} 失敗: {str(e)}")
            self.db.rollback()
            raise

    def _set_default_values(self):
        """設置現有記錄的預設值"""
        try:
            # 為現有用戶設置 UUID (使用 id)
            self.db.execute(text("""
                UPDATE users
                SET uuid = id
                WHERE uuid IS NULL
            """))

            # 為現有用戶設置 membership_tier (從 tier_type)
            self.db.execute(text("""
                UPDATE users
                SET membership_tier = LOWER(tier_type)
                WHERE membership_tier IS NULL OR membership_tier = 'free'
            """))

            # 為現有用戶設置 status
            self.db.execute(text("""
                UPDATE users
                SET status = 'active'
                WHERE status IS NULL
            """))

            self.db.commit()
            logger.info("✅ 預設值設置完成")

        except Exception as e:
            logger.error(f"設置預設值失敗: {str(e)}")
            self.db.rollback()

def run_auto_migration():
    """運行自動 migration (應用啟動時調用)"""
    try:
        from tradingagents.database.database import SessionLocal

        db = SessionLocal()
        try:
            migrator = AutoMigrator(db)
            success = migrator.check_and_migrate()

            if success:
                logger.info("✅ 自動 Migration 完成")
            else:
                logger.warning("⚠️ 自動 Migration 未完成")

            return success

        finally:
            db.close()

    except Exception as e:
        logger.error(f"運行自動 Migration 失敗: {str(e)}", exc_info=True)
        return False

if __name__ == "__main__":
    # 可以獨立運行此腳本進行 migration
    logging.basicConfig(level=logging.INFO)
    success = run_auto_migration()
    exit(0 if success else 1)
