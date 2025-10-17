-- Migration: Add authentication fields to users table
-- Date: 2025-10-17
-- Purpose: Fix register/login password verification mismatch

-- Add missing columns to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS username VARCHAR(100) UNIQUE,
ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
ADD COLUMN IF NOT EXISTS uuid UUID DEFAULT gen_random_uuid(),
ADD COLUMN IF NOT EXISTS membership_tier VARCHAR(20) DEFAULT 'free',
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active',
ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE;

-- Create index on username
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Create index on uuid
CREATE INDEX IF NOT EXISTS idx_users_uuid ON users(uuid);

-- Update existing users with UUID if they don't have one
UPDATE users SET uuid = id WHERE uuid IS NULL;

-- Update existing users with membership_tier from tier_type if needed
UPDATE users SET membership_tier = LOWER(tier_type) WHERE membership_tier IS NULL OR membership_tier = 'free';

-- Add comments for documentation
COMMENT ON COLUMN users.username IS 'User login username (3-50 characters)';
COMMENT ON COLUMN users.password_hash IS 'Bcrypt hashed password';
COMMENT ON COLUMN users.uuid IS 'User UUID for API identification';
COMMENT ON COLUMN users.membership_tier IS 'User membership level: free, gold, diamond';
COMMENT ON COLUMN users.status IS 'Account status: active, suspended, deleted';
COMMENT ON COLUMN users.email_verified IS 'Email verification status';
