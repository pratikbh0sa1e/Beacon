# Fix Foreign Keys - Quick Guide

## The Issue

The migration was marked as complete but didn't actually run the SQL changes.
You still need to fix the foreign key constraints manually.

---

## ✅ Solution: Run SQL Script

### Option 1: Using psql Command Line

```bash
# Connect to your database
psql -U postgres -d your_database_name

# Then paste this SQL:
```

```sql
-- Fix audit_logs (the main one causing errors)
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey CASCADE;
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;

-- Fix documents uploader_id
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_uploader_id_fkey CASCADE;
ALTER TABLE documents ADD CONSTRAINT documents_uploader_id_fkey
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL;

-- Fix documents approved_by
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_approved_by_fkey CASCADE;
ALTER TABLE documents ADD CONSTRAINT documents_approved_by_fkey
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;

-- Fix bookmarks
ALTER TABLE bookmarks DROP CONSTRAINT IF EXISTS bookmarks_user_id_fkey CASCADE;
ALTER TABLE bookmarks ADD CONSTRAINT bookmarks_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Verify changes
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
    AND kcu.column_name IN ('user_id', 'uploader_id', 'approved_by')
ORDER BY tc.table_name;
```

---

### Option 2: Using pgAdmin

1. Open pgAdmin
2. Connect to your database
3. Right-click on your database → Query Tool
4. Paste the SQL above
5. Click Execute (F5)

---

### Option 3: Using DBeaver / DataGrip

1. Open your database tool
2. Connect to your database
3. Open SQL Console
4. Paste the SQL above
5. Execute

---

## 🧪 Test It Works

After running the SQL, try deleting a user from the database:

```sql
-- This should now work without errors!
DELETE FROM users WHERE id = 8;
```

**Expected behavior:**

- ✅ User deleted successfully
- ✅ audit_logs.user_id set to NULL (audit preserved)
- ✅ documents.uploader_id set to NULL (document preserved)
- ✅ bookmarks deleted (CASCADE)

---

## 📊 Verify Foreign Keys Are Fixed

Run this query to check:

```sql
SELECT
    tc.table_name,
    kcu.column_name,
    rc.delete_rule as on_delete_action
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND kcu.column_name IN ('user_id', 'uploader_id', 'approved_by')
ORDER BY tc.table_name;
```

**Expected results:**

```
table_name      | column_name  | on_delete_action
----------------|--------------|------------------
audit_logs      | user_id      | SET NULL
bookmarks       | user_id      | CASCADE
documents       | uploader_id  | SET NULL
documents       | approved_by  | SET NULL
chat_sessions   | user_id      | CASCADE (if exists)
user_notes      | user_id      | CASCADE (if exists)
```

---

## ✅ Summary

**What to do:**

1. Open your database tool (psql, pgAdmin, DBeaver, etc.)
2. Run the SQL script above
3. Verify with the test query
4. Try deleting a user - should work now!

**Result:**

- ✅ Can delete users without foreign key errors
- ✅ Audit trail preserved
- ✅ Documents preserved
- ✅ User data cleaned up properly

---

## 🚀 Quick Copy-Paste

**Minimal SQL (just fix the main error):**

```sql
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey CASCADE;
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

This alone will fix the error you were getting!
