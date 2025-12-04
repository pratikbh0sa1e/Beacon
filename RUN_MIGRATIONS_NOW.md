# Run Pending Migrations

## Current Situation

You have pending migrations that need to be run:

1. `add_soft_delete_001` - Adds `deleted_at` and `deleted_by` to institutions table
2. `fix_fk_constraints_001` - Fixes foreign key constraints (already stamped but not executed)

---

## Step 1: Check Current Migration Status

```bash
alembic current
```

This shows which migration you're currently on.

---

## Step 2: Check Pending Migrations

```bash
alembic heads
```

This shows all head migrations.

---

## Step 3: Run All Pending Migrations

```bash
alembic upgrade head
```

This will run all pending migrations.

---

## What Will Happen

### Migration 1: add_soft_delete_001

```sql
-- Adds soft delete columns to institutions table
ALTER TABLE institutions ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE institutions ADD COLUMN deleted_by INTEGER REFERENCES users(id);
CREATE INDEX idx_institutions_deleted_at ON institutions(deleted_at);
```

**Result:**

- ✅ Institutions can be soft deleted
- ✅ Track who deleted the institution
- ✅ Track when it was deleted

---

### Migration 2: fix_fk_constraints_001

This was already stamped but might not have executed. It fixes foreign key constraints for user deletion.

---

## If Migration Fails

### Option 1: Already Applied?

If you get an error that columns already exist:

```bash
# Check if columns exist
psql -U postgres -d your_database -c "\d institutions"
```

If `deleted_at` and `deleted_by` already exist, just stamp the migration:

```bash
alembic stamp add_soft_delete_001
```

---

### Option 2: Run Manually in Supabase

If alembic times out, run this SQL in Supabase SQL Editor:

```sql
-- Add soft delete columns
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP NULL;
ALTER TABLE institutions ADD COLUMN IF NOT EXISTS deleted_by INTEGER;

-- Add foreign key
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_institutions_deleted_by'
    ) THEN
        ALTER TABLE institutions
        ADD CONSTRAINT fk_institutions_deleted_by
        FOREIGN KEY (deleted_by) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add index
CREATE INDEX IF NOT EXISTS idx_institutions_deleted_at ON institutions(deleted_at);
```

Then stamp the migration:

```bash
alembic stamp add_soft_delete_001
```

---

## Quick Commands

```bash
# 1. Check current status
alembic current

# 2. Run all pending migrations
alembic upgrade head

# 3. Restart backend
# Stop with Ctrl+C, then:
uvicorn backend.main:app --reload
```

---

## Expected Result

After running migrations:

```bash
alembic current
```

Should show:

```
add_soft_delete_001 (head)
```

Or:

```
fix_fk_constraints_001 (head)
```

---

## Verify Columns Were Added

```sql
-- Check institutions table structure
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'institutions'
ORDER BY ordinal_position;
```

Should show:

```
...
deleted_at    | timestamp | YES
deleted_by    | integer   | YES
```

---

## Summary

**Run this now:**

```bash
alembic upgrade head
```

**If it works:**

- ✅ Columns added
- ✅ Restart backend
- ✅ Test deletion feature

**If it times out:**

- Run SQL manually in Supabase
- Stamp the migration
- Restart backend

---

**After migrations are done, restart your backend and the SQLAlchemy error will be gone!** ✅
