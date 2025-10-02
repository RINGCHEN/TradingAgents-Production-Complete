-- Migration: 001_add_admin_password
-- Description: Add password_hash column to admin_users table
-- Date: 2025-10-02

-- 1. Add password_hash column
ALTER TABLE admin_users
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- 2. Create test admin accounts (password: admin123 and manager123)
-- Note: These password hashes are generated using bcrypt with cost factor 12

INSERT INTO admin_users (email, name, role, permissions, password_hash, is_active)
VALUES
    ('admin@example.com', 'Admin User', 'admin',
     ARRAY['user_management', 'system_config', 'analytics', 'reports'],
     '$2b$12$p2R7gQ5XxYoQBaTzVAhWfu.aYKZVA8gZeJ61S1cBbqFwEr9BWMuem', -- admin123
     true),
    ('manager@example.com', 'Manager User', 'manager',
     ARRAY['user_management', 'analytics'],
     '$2b$12$/3H7A989b8x9d1tEs6cZYOMVPYUuiEqSc4L17siu1aChxtuDP08AG', -- manager123
     true)
ON CONFLICT (email)
DO UPDATE SET
    name = EXCLUDED.name,
    role = EXCLUDED.role,
    permissions = EXCLUDED.permissions,
    password_hash = EXCLUDED.password_hash,
    is_active = EXCLUDED.is_active,
    updated_at = CURRENT_TIMESTAMP;

-- Verify migration
SELECT 'Migration 001 completed successfully' AS status;
SELECT email, name, role, is_active,
       CASE WHEN password_hash IS NOT NULL THEN 'SET' ELSE 'NULL' END AS password_status
FROM admin_users;
