-- Manual SQL Script to Fix Foreign Key Constraints
-- Run this directly in your PostgreSQL database if migration times out

-- ============================================
-- 1. Fix audit_logs foreign key (SET NULL)
-- ============================================
ALTER TABLE audit_logs 
DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey CASCADE;

ALTER TABLE audit_logs 
ALTER COLUMN user_id DROP NOT NULL;

ALTER TABLE audit_logs 
ADD CONSTRAINT audit_logs_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) 
ON DELETE SET NULL;

-- ============================================
-- 2. Fix documents uploader_id (SET NULL)
-- ============================================
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_uploader_id_fkey CASCADE;

ALTER TABLE documents 
ADD CONSTRAINT documents_uploader_id_fkey 
FOREIGN KEY (uploader_id) REFERENCES users(id) 
ON DELETE SET NULL;

-- ============================================
-- 3. Fix documents approved_by (SET NULL)
-- ============================================
ALTER TABLE documents 
DROP CONSTRAINT IF EXISTS documents_approved_by_fkey CASCADE;

ALTER TABLE documents 
ADD CONSTRAINT documents_approved_by_fkey 
FOREIGN KEY (approved_by) REFERENCES users(id) 
ON DELETE SET NULL;

-- ============================================
-- 4. Fix bookmarks (CASCADE)
-- ============================================
ALTER TABLE bookmarks 
DROP CONSTRAINT IF EXISTS bookmarks_user_id_fkey CASCADE;

ALTER TABLE bookmarks 
ADD CONSTRAINT bookmarks_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id) 
ON DELETE CASCADE;

-- ============================================
-- 5. Fix chat_sessions (CASCADE) - if exists
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_sessions') THEN
        ALTER TABLE chat_sessions 
        DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey CASCADE;
        
        ALTER TABLE chat_sessions 
        ADD CONSTRAINT chat_sessions_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================
-- 6. Fix user_notes (CASCADE) - if exists
-- ============================================
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_notes') THEN
        ALTER TABLE user_notes 
        DROP CONSTRAINT IF EXISTS fk_user_notes_user_id CASCADE;
        
        ALTER TABLE user_notes 
        ADD CONSTRAINT fk_user_notes_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================
-- Verify changes
-- ============================================
SELECT 
    tc.table_name, 
    kcu.column_name,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc 
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND kcu.column_name LIKE '%user_id%'
ORDER BY tc.table_name;

-- Expected results:
-- audit_logs.user_id -> SET NULL
-- documents.uploader_id -> SET NULL  
-- documents.approved_by -> SET NULL
-- bookmarks.user_id -> CASCADE
-- chat_sessions.user_id -> CASCADE
-- user_notes.user_id -> CASCADE
