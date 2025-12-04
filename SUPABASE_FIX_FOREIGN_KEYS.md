# Fix Foreign Keys on Supabase

## Issue

Supabase SQL Editor has a timeout limit. The ALTER TABLE commands are timing out because of table locks.

---

## ✅ Solution: Run Commands One at a Time

### Step 1: Fix audit_logs (Most Important)

Run this **alone** in Supabase SQL Editor:

```sql
-- Step 1a: Drop the constraint
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey CASCADE;
```

Wait for it to complete, then run:

```sql
-- Step 1b: Make column nullable
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
```

Wait for it to complete, then run:

```sql
-- Step 1c: Add new constraint with SET NULL
ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

---

### Step 2: Fix documents uploader_id

Run this **alone**:

```sql
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_uploader_id_fkey CASCADE;
```

Then:

```sql
ALTER TABLE documents ADD CONSTRAINT documents_uploader_id_fkey
    FOREIGN KEY (uploader_id) REFERENCES users(id) ON DELETE SET NULL;
```

---

### Step 3: Fix documents approved_by

Run this **alone**:

```sql
ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_approved_by_fkey CASCADE;
```

Then:

```sql
ALTER TABLE documents ADD CONSTRAINT documents_approved_by_fkey
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL;
```

---

### Step 4: Fix bookmarks

Run this **alone**:

```sql
ALTER TABLE bookmarks DROP CONSTRAINT IF EXISTS bookmarks_user_id_fkey CASCADE;
```

Then:

```sql
ALTER TABLE bookmarks ADD CONSTRAINT bookmarks_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

---

## 🔍 Alternative: Check Current Constraints First

Before making changes, see what constraints exist:

```sql
SELECT
    tc.constraint_name,
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

This will show you which constraints need to be fixed.

---

## 🚨 If Still Timing Out

### Option 1: Kill Active Connections

```sql
-- See active connections
SELECT pid, usename, application_name, state, query
FROM pg_stat_activity
WHERE datname = current_database()
AND state = 'active';

-- Kill a specific connection (if needed)
-- SELECT pg_terminate_backend(pid) WHERE pid = <pid_number>;
```

---

### Option 2: Use Supabase Dashboard

1. Go to **Supabase Dashboard**
2. Click **Database** → **Tables**
3. Find `audit_logs` table
4. Click on the table
5. Go to **Constraints** tab
6. Delete `audit_logs_user_id_fkey` constraint
7. Add new constraint with ON DELETE SET NULL

---

### Option 3: Connect Directly with psql

Get your connection string from Supabase:

1. Go to **Project Settings** → **Database**
2. Copy **Connection string** (URI format)
3. Use psql:

```bash
psql "postgresql://postgres:[YOUR-PASSWORD]@[YOUR-PROJECT-REF].supabase.co:5432/postgres"
```

Then run the SQL commands.

---

## 🎯 Minimal Fix (Just to Delete Users)

If you just want to be able to delete users, run **only this**:

```sql
-- Drop the problematic constraint
ALTER TABLE audit_logs DROP CONSTRAINT audit_logs_user_id_fkey CASCADE;
```

Then:

```sql
-- Make user_id nullable
ALTER TABLE audit_logs ALTER COLUMN user_id DROP NOT NULL;
```

Then:

```sql
-- Add back with SET NULL
ALTER TABLE audit_logs ADD CONSTRAINT audit_logs_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

**Run each command separately, waiting for each to complete.**

---

## 🧪 Test After Each Step

After fixing audit_logs, test:

```sql
-- Try deleting a test user
DELETE FROM users WHERE email = 'test@example.com';
```

If this works, the main issue is fixed!

---

## 📊 Verify What's Fixed

```sql
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
    AND tc.table_name = 'audit_logs'
    AND kcu.column_name = 'user_id';
```

Should show: `delete_rule = 'SET NULL'`

---

## ⚡ Pro Tip: Increase Timeout

In Supabase SQL Editor, you can increase timeout:

```sql
-- Set statement timeout to 5 minutes
SET statement_timeout = '300000';

-- Then run your ALTER TABLE commands
ALTER TABLE audit_logs DROP CONSTRAINT IF EXISTS audit_logs_user_id_fkey CASCADE;
-- ... etc
```

---

## ✅ Summary

**For Supabase:**

1. Run commands **one at a time**
2. Wait for each to complete
3. Start with audit_logs (most important)
4. Test after each table
5. If timeout persists, use Supabase Dashboard UI

**Priority order:**

1. audit_logs ← **Start here!**
2. documents (uploader_id)
3. documents (approved_by)
4. bookmarks

Once audit_logs is fixed, you can delete users!
