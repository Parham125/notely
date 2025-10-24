-- migrations/v1_to_v2.sql
-- Add admin role system
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- Add role column to users table if it doesn't exist
-- This will be ignored if column already exists, which is expected
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';

-- Make the first user admin (if users exist)
UPDATE users SET role = CASE
    WHEN role IS NULL THEN 'admin'
    WHEN role = '' THEN 'admin'
    ELSE role
END
WHERE id = (SELECT id FROM users ORDER BY created_at LIMIT 1);

-- Create index for role queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Create index for role queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Update database version immediately within transaction
PRAGMA user_version=2;

COMMIT;

-- Re-enable foreign keys after migration
PRAGMA foreign_keys=ON;