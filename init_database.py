#!/usr/bin/env python3
"""
資料庫初始化腳本
創建所有必要的資料表
"""

import sys
import os

# 設置正確的DATABASE_URL
DATABASE_URL = "postgresql://doadmin:AVNS_4O1Z8zVC5UDNdFw-0xK@app-f65ee22d-0465-4beb-9eef-7b1138793d6a-do-user-20425009-0.f.db.ondigitalocean.com:25060/tradingagents-complete-db?sslmode=require"
os.environ['DATABASE_URL'] = DATABASE_URL

print("=" * 70)
print("TradingAgents 資料庫初始化")
print("=" * 70)
print()
print(f"資料庫: tradingagents-complete-db")
print(f"主機: app-f65ee22d-0465-4beb-9eef-7b1138793d6a-do-user-20425009-0.f.db.ondigitalocean.com")
print()

try:
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.ext.declarative import declarative_base

    # 創建引擎
    print("正在連接資料庫...")
    engine = create_engine(DATABASE_URL)

    # 測試連接
    connection = engine.connect()
    print("[OK] 資料庫連接成功！")
    connection.close()
    print()

    # 檢查現有表
    print("=" * 70)
    print("檢查現有表...")
    print("=" * 70)
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"現有表數量: {len(existing_tables)}")
    for table in existing_tables:
        print(f"  - {table}")
    print()

    # 導入所有models
    print("=" * 70)
    print("導入模型定義...")
    print("=" * 70)

    # 首先導入database.py的Base
    from tradingagents.database.database import Base as DatabaseBase
    print("[OK] 導入 database.Base")

    # 導入config models（已經使用正確的Base）
    try:
        from tradingagents.database import config_models
        print("[OK] 導入 config_models")
    except Exception as e:
        print(f"[WARNING] config_models 導入失敗: {e}")

    # 對於user.py，我們需要修正它的Base
    # 先讀取並註冊User模型到正確的Base
    try:
        # 直接定義User模型（使用正確的Base）
        from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum as SQLEnum, JSON
        from datetime import datetime
        import uuid
        from enum import Enum

        class UserStatus(str, Enum):
            ACTIVE = "ACTIVE"
            INACTIVE = "INACTIVE"
            SUSPENDED = "SUSPENDED"
            DELETED = "DELETED"

        class MembershipTier(str, Enum):
            FREE = "FREE"
            GOLD = "GOLD"
            DIAMOND = "DIAMOND"

        class AuthProvider(str, Enum):
            GOOGLE = "GOOGLE"
            EMAIL = "EMAIL"
            FACEBOOK = "FACEBOOK"
            LINE = "LINE"

        class User(DatabaseBase):
            """用戶主表"""
            __tablename__ = "users"

            # 基本信息
            id = Column(Integer, primary_key=True, index=True)
            uuid = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), index=True)
            email = Column(String(255), unique=True, index=True, nullable=False)
            username = Column(String(100), unique=True, index=True)
            display_name = Column(String(100))

            # 認證信息
            auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.EMAIL, nullable=False)
            password_hash = Column(String(255), nullable=True)
            email_verified = Column(Boolean, default=False)

            # 會員等級和狀態
            membership_tier = Column(SQLEnum(MembershipTier), default=MembershipTier.FREE, nullable=False)
            status = Column(SQLEnum(UserStatus), default=UserStatus.ACTIVE, nullable=False)

            # API配額管理
            daily_api_quota = Column(Integer, default=100)
            monthly_api_quota = Column(Integer, default=3000)
            api_calls_today = Column(Integer, default=0)
            api_calls_month = Column(Integer, default=0)
            total_analyses = Column(Integer, default=0)

            # 登入和活動追蹤
            login_count = Column(Integer, default=0)
            last_login_at = Column(DateTime, nullable=True)
            last_active_at = Column(DateTime, nullable=True)

            # 時間戳記
            created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
            updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

        print("[OK] 定義 User 模型（使用正確的Base）")

    except Exception as e:
        print(f"[ERROR] User 模型定義失敗: {e}")
        import traceback
        traceback.print_exc()

    # 創建所有表
    print()
    print("=" * 70)
    print("創建資料表...")
    print("=" * 70)

    DatabaseBase.metadata.create_all(bind=engine)

    print("[OK] 資料表創建完成！")
    print()

    # 驗證創建結果
    print("=" * 70)
    print("驗證創建結果...")
    print("=" * 70)

    inspector = inspect(engine)
    new_tables = inspector.get_table_names()
    print(f"現在表數量: {len(new_tables)}")

    # 檢查users表
    if 'users' in new_tables:
        print("[OK] users 表創建成功！")

        # 顯示表結構
        columns = inspector.get_columns('users')
        print(f"\nusers 表結構 ({len(columns)} 個欄位):")
        for col in columns[:10]:  # 只顯示前10個
            print(f"  - {col['name']}: {col['type']}")
        if len(columns) > 10:
            print(f"  ... 還有 {len(columns) - 10} 個欄位")
    else:
        print("[ERROR] users 表未創建！")

    print()
    print("所有表:")
    for table in sorted(new_tables):
        status = "[NEW]" if table not in existing_tables else "     "
        print(f"  {status} {table}")

    print()
    print("=" * 70)
    print("資料庫初始化完成！")
    print("=" * 70)
    print()
    print("下一步:")
    print("1. 執行 create_test_account.py 創建測試帳號")
    print("2. 執行 auth-test.js 驗證登入功能")
    print()

    sys.exit(0)

except Exception as e:
    print(f"[ERROR] 初始化失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
