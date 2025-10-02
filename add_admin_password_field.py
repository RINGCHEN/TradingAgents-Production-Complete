#!/usr/bin/env python3
"""
添加 admin_users 表的 password_hash 欄位

此腳本將：
1. 在 admin_users 表添加 password_hash 欄位
2. 創建測試管理員帳號
"""

import os
import psycopg2
import bcrypt
from dotenv import load_dotenv

load_dotenv()

def main():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()

    try:
        print("=== 添加 admin_users.password_hash 欄位 ===")

        # 1. 添加 password_hash 欄位
        cursor.execute("""
            ALTER TABLE admin_users
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
        """)
        print("✅ password_hash 欄位已添加")

        # 2. 創建測試管理員帳號
        test_admins = [
            {
                'email': 'admin@example.com',
                'name': 'Admin User',
                'password': 'admin123',
                'role': 'admin',
                'permissions': ['user_management', 'system_config', 'analytics', 'reports']
            },
            {
                'email': 'manager@example.com',
                'name': 'Manager User',
                'password': 'manager123',
                'role': 'manager',
                'permissions': ['user_management', 'analytics']
            }
        ]

        for admin in test_admins:
            # Hash 密碼
            password_hash = bcrypt.hashpw(admin['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # 插入或更新管理員
            cursor.execute("""
                INSERT INTO admin_users (email, name, role, permissions, password_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    role = EXCLUDED.role,
                    permissions = EXCLUDED.permissions,
                    password_hash = EXCLUDED.password_hash,
                    is_active = EXCLUDED.is_active,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                admin['email'],
                admin['name'],
                admin['role'],
                admin['permissions'],
                password_hash,
                True
            ))
            print(f"✅ 管理員帳號已創建/更新: {admin['email']}")

        conn.commit()

        # 3. 驗證結果
        print("\n=== 驗證 admin_users 表結構 ===")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'admin_users'
            ORDER BY ordinal_position;
        """)

        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]}")

        print("\n=== 驗證管理員帳號 ===")
        cursor.execute("SELECT email, name, role, is_active FROM admin_users;")
        for row in cursor.fetchall():
            print(f"  {row[0]} - {row[1]} ({row[2]}) - Active: {row[3]}")

        print("\n✅ 資料庫遷移完成！")
        print("\n測試帳號：")
        print("  admin@example.com / admin123")
        print("  manager@example.com / manager123")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
