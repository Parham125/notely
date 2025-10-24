-- migrations/v1_to_v2.sql
-- Add admin role system
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

-- Add role column to users table
ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';

-- Make the first user admin (if users exist)
UPDATE users SET role = 'admin' WHERE id = (SELECT id FROM users ORDER BY created_at LIMIT 1);

-- Create index for role queries
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- Update database version
PRAGMA user_version=2;

COMMIT;
PRAGMA foreign_keys=ON;