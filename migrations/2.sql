-- Migration 2.sql
-- Add admin role system
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;

ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user';

UPDATE users SET role = 'admin'
END
WHERE id = (SELECT id FROM users ORDER BY created_at LIMIT 1);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

PRAGMA user_version=2;

COMMIT;

PRAGMA foreign_keys=ON;