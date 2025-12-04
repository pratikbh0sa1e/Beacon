# User Deletion Workaround Guide

## Current Status

### ✅ Fixed:

- **audit_logs** - Foreign key constraint fixed with `ON DELETE SET NULL`
- Users can be deleted if they only have audit logs

### ⏸️ Pending (Supabase Timeout Issues):

- **documents** (uploader_id, approved_by) - Not fixed yet
- **bookmarks** - Not fixed yet
- **chat_sessions** - Not fixed yet
- **user_notes** - Not fixed yet

---

## When Can You Delete Users?

### ✅ Can Delete If User Has:

- Audit logs only
- No documents uploaded
- No documents approved
- No bookmarks
- No chat sessions
- No notes

### ❌ Cannot Delete If User Has:

- Documents they uploaded
- Documents they approved
- Bookmarks
- Chat sessions
- Notes

**Error you'll get:**

```
ERROR: update or delete on table "users" violates foreign key constraint
DETAIL: Key (id)=(X) is still referenced from table "documents"
```

---

## Workaround: Manual Cleanup Before Deletion

When a developer needs to delete a user, use this script:

### Step-by-Step Deletion Script

```sql
-- ============================================
-- USER DELETION SCRIPT
-- Replace X with the actual user ID to delete
-- ============================================

-- Step 1: Check what the user has
SELECT
    'Documents uploaded' as type, COUNT(*) as count
FROM documents WHERE uploader_id = X
UNION ALL
SELECT
    'Documents approved' as type, COUNT(*) as count
FROM documents WHERE approved_by = X
UNION ALL
SELECT
    'Bookmarks' as type, COUNT(*) as count
FROM bookmarks WHERE user_id = X
UNION ALL
SELECT
    'Chat sessions' as type, COUNT(*) as count
FROM chat_sessions WHERE user_id = X
UNION ALL
SELECT
    'Notes' as type, COUNT(*) as count
FROM user_notes WHERE user_id = X;

-- Step 2: Clean up bookmarks (delete them)
DELETE FROM bookmarks WHERE user_id = X;

-- Step 3: Clean up chat sessions (delete them)
DELETE FROM chat_sessions WHERE user_id = X;

-- Step 4: Clean up notes (delete them)
DELETE FROM user_notes WHERE user_id = X;

-- Step 5: Clean up documents (preserve documents, remove user reference)
UPDATE documents
SET uploader_id = NULL
WHERE uploader_id = X;

UPDATE documents
SET approved_by = NULL
WHERE approved_by = X;

-- Step 6: Now delete the user
DELETE FROM users WHERE id = X;

-- Step 7: Verify deletion
SELECT * FROM users WHERE id = X;
-- Should return no rows
```

---

## Quick Copy-Paste Script

```sql
-- Replace X with user ID
DO $$
DECLARE
    user_id_to_delete INTEGER := X;  -- ← Change this!
BEGIN
    -- Clean up
    DELETE FROM bookmarks WHERE user_id = user_id_to_delete;
    DELETE FROM chat_sessions WHERE user_id = user_id_to_delete;
    DELETE FROM user_notes WHERE user_id = user_id_to_delete;

    -- Preserve documents, remove user reference
    UPDATE documents SET uploader_id = NULL WHERE uploader_id = user_id_to_delete;
    UPDATE documents SET approved_by = NULL WHERE approved_by = user_id_to_delete;

    -- Delete user
    DELETE FROM users WHERE id = user_id_to_delete;

    RAISE NOTICE 'User % deleted successfully', user_id_to_delete;
END $$;
```

---

## Example: Delete User ID 8

```sql
-- Check what user 8 has
SELECT
    'Documents uploaded' as type, COUNT(*) as count
FROM documents WHERE uploader_id = 8
UNION ALL
SELECT
    'Documents approved' as type, COUNT(*) as count
FROM documents WHERE approved_by = 8
UNION ALL
SELECT
    'Bookmarks' as type, COUNT(*) as count
FROM bookmarks WHERE user_id = 8;

-- Result:
-- Documents uploaded: 5
-- Documents approved: 12
-- Bookmarks: 3

-- Clean up and delete
DELETE FROM bookmarks WHERE user_id = 8;
UPDATE documents SET uploader_id = NULL WHERE uploader_id = 8;
UPDATE documents SET approved_by = NULL WHERE approved_by = 8;
DELETE FROM users WHERE id = 8;

-- Success! User deleted, documents preserved
```

---

## What Happens to Data?

### Documents:

```
Before deletion:
Document: "Annual Report.pdf"
Uploaded by: John Doe (user_id: 8)
Approved by: Admin User (user_id: 8)

After deletion:
Document: "Annual Report.pdf"  ← Still exists!
Uploaded by: [Deleted User] (uploader_id: NULL)
Approved by: [Deleted User] (approved_by: NULL)
```

### Bookmarks:

```
Before deletion:
User 8 has 3 bookmarks

After deletion:
Bookmarks deleted (CASCADE behavior)
```

### Audit Logs:

```
Before deletion:
Audit Log: User 8 uploaded document X

After deletion:
Audit Log: [Deleted User] uploaded document X
(user_id: NULL, but log preserved)
```

---

## Future: Proper Fix

When Supabase isn't timing out, run these to fix permanently:

```sql
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

-- Fix chat_sessions
ALTER TABLE chat_sessions DROP CONSTRAINT IF EXISTS chat_sessions_user_id_fkey CASCADE;
ALTER TABLE chat_sessions ADD CONSTRAINT chat_sessions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Fix user_notes
ALTER TABLE user_notes DROP CONSTRAINT IF EXISTS fk_user_notes_user_id CASCADE;
ALTER TABLE user_notes ADD CONSTRAINT fk_user_notes_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

After this, you can delete users with a simple:

```sql
DELETE FROM users WHERE id = X;
```

---

## Best Practices

### Before Deleting a User:

1. **Check if they're a developer** - Don't delete developers!

   ```sql
   SELECT role FROM users WHERE id = X;
   ```

2. **Check their activity**

   ```sql
   SELECT
       COUNT(DISTINCT d1.id) as docs_uploaded,
       COUNT(DISTINCT d2.id) as docs_approved,
       COUNT(DISTINCT b.id) as bookmarks
   FROM users u
   LEFT JOIN documents d1 ON u.id = d1.uploader_id
   LEFT JOIN documents d2 ON u.id = d2.approved_by
   LEFT JOIN bookmarks b ON u.id = b.user_id
   WHERE u.id = X
   GROUP BY u.id;
   ```

3. **Backup important data** (if needed)

   ```sql
   -- Export user's documents list
   SELECT id, filename, created_at
   FROM documents
   WHERE uploader_id = X;
   ```

4. **Run the cleanup script**

5. **Verify deletion**
   ```sql
   SELECT * FROM users WHERE id = X;
   -- Should return nothing
   ```

---

## Alternative: Soft Delete (Recommended)

Instead of hard deleting, consider soft delete:

### Add columns to users table:

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN deleted_by INTEGER REFERENCES users(id);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
```

### Soft delete a user:

```sql
UPDATE users
SET deleted_at = NOW(),
    deleted_by = 1  -- Developer user ID
WHERE id = X;
```

### Filter deleted users in queries:

```sql
SELECT * FROM users WHERE deleted_at IS NULL;
```

### Benefits:

- ✅ Can restore if mistake
- ✅ No foreign key issues
- ✅ Preserves all data
- ✅ Audit trail intact
- ✅ No complex cleanup needed

---

## Summary

### Current Situation:

- ✅ audit_logs fixed - user deletion works for users with only audit logs
- ⏸️ Other tables pending - need manual cleanup before deletion

### Workaround:

- Use the cleanup script before deleting users
- Takes 30 seconds per user
- Preserves documents, deletes personal data

### Future Fix:

- Run the ALTER TABLE commands when Supabase isn't busy
- Then user deletion becomes one simple command

### Best Practice:

- Consider implementing soft delete instead
- Easier, safer, reversible

---

## Quick Reference

**Delete user with cleanup:**

```sql
-- Replace 8 with user ID
DELETE FROM bookmarks WHERE user_id = 8;
UPDATE documents SET uploader_id = NULL WHERE uploader_id = 8;
UPDATE documents SET approved_by = NULL WHERE approved_by = 8;
DELETE FROM users WHERE id = 8;
```

**Check before deleting:**

```sql
SELECT role, email, institution_id FROM users WHERE id = 8;
```

**Verify after deleting:**

```sql
SELECT * FROM users WHERE id = 8;  -- Should be empty
SELECT COUNT(*) FROM documents WHERE uploader_id IS NULL;  -- Shows preserved docs
```

---

**Status:** ✅ Workaround documented and ready to use

**Next Steps:**

1. Use workaround script when needed
2. Fix foreign keys properly when Supabase allows
3. Consider implementing soft delete for better UX
