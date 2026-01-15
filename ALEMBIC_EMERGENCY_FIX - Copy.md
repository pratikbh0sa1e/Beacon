# 🚨 Alembic Emergency Fix Guide

## Your Situation

Your friend changed something in Alembic, and now:
- ❌ Getting Gemini API key exhausted error (unrelated to Alembic, but happening)
- ❌ Alembic is in a broken state
- ✅ You have working code on main branch
- ✅ You want to force your database to match your working code

---

## 🎯 Quick Fix (3 Steps)

### Step 1: Fix the Script Error

The script has been fixed! The issue was using `.commit()` on a Connection object. Now it uses `.begin()` which auto-commits.

### Step 2: Run the Fixed Script

```bash
python fix_alembic_now.py
```

**Expected Output:**
```
🔧 Alembic Emergency Fix
==================================================
❌ Current (broken) version: 9af9fd4fb543
🔨 Deleting broken version...
✅ Deleted broken version
📝 Setting version to: add_performance_indexes
✅ Version updated!
✅ New version: add_performance_indexes
==================================================
🎉 Alembic fixed! Now run: alembic current
```

### Step 3: Verify Fix

```bash
alembic current
```

**Should show:**
```
add_performance_indexes (head)
```

---

## 🔧 Alternative Manual Fix (If Script Fails)

### Option A: Direct SQL Fix

```bash
# 1. Connect to your database
psql -h YOUR_HOST -U YOUR_USER -d YOUR_DATABASE

# 2. Check current version
SELECT * FROM alembic_version;

# 3. Delete broken version
DELETE FROM alembic_version;

# 4. Insert correct version (use your latest migration)
INSERT INTO alembic_version (version_num) VALUES ('add_performance_indexes');

# 5. Verify
SELECT * FROM alembic_version;

# 6. Exit
\q
```

### Option B: Alembic Stamp Command

```bash
# This tells Alembic "pretend we're at this version"
alembic stamp head

# Or stamp to a specific revision
alembic stamp add_performance_indexes
```

---

## 🔍 Finding Your Latest Migration

To find what version to use:

```bash
# List all migrations
alembic history

# Or check your migration files
ls alembic/versions/

# The latest one should be at the bottom of history
```

**Your migrations (in order):**
```
002_add_document_metadata.py
add_email_verification_fields.py
add_document_chat_tables.py
add_document_workflow_fields.py
add_parent_ministry.py
remove_government_dept.py
add_performance_indexes.py  ← LATEST
```

So your latest revision is: `add_performance_indexes`

---

## 🚀 Complete Recovery Process

### If You Want to Start Fresh with Your Main Branch:

```bash
# 1. Backup your database (IMPORTANT!)
pg_dump -h HOST -U USER -d DATABASE > backup_before_fix.sql

# 2. Check what migrations exist in your code
alembic history

# 3. Check what version database thinks it's at
alembic current

# 4. If they don't match, stamp to correct version
alembic stamp head

# 5. Verify
alembic current

# 6. If you need to apply migrations
alembic upgrade head
```

---

## 🔥 Nuclear Option (Complete Reset)

**⚠️ WARNING: This will recreate all tables! Only use if you can lose data!**

```bash
# 1. Backup database
pg_dump -h HOST -U USER -d DATABASE > backup_nuclear.sql

# 2. Drop alembic_version table
psql -h HOST -U USER -d DATABASE -c "DROP TABLE IF EXISTS alembic_version;"

# 3. Recreate all tables from scratch
python -c "from backend.database import Base, engine; Base.metadata.drop_all(engine); Base.metadata.create_all(engine)"

# 4. Stamp Alembic to current version
alembic stamp head

# 5. Verify
alembic current
```

---

## 🐛 About the Gemini API Error

The "Gemini API key exhausted" error is **NOT related to Alembic**. It means:

### Possible Causes:

1. **Rate Limit Hit**
   - Free tier: 15 requests per minute
   - Solution: Wait a few minutes

2. **Quota Exhausted**
   - Free tier: 1,500 requests per day
   - Solution: Wait until tomorrow or upgrade

3. **Invalid API Key**
   - Key expired or revoked
   - Solution: Generate new key at https://makersuite.google.com/app/apikey

4. **Wrong API Key**
   - Using someone else's key
   - Solution: Check your `.env` file

### Quick Fix for Gemini Error:

```bash
# 1. Check your .env file
cat .env | grep GOOGLE_API_KEY

# 2. Test the API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY"

# 3. If invalid, get new key from:
# https://makersuite.google.com/app/apikey

# 4. Update .env
# GOOGLE_API_KEY=your_new_key_here
```

---

## 📋 Troubleshooting Checklist

### ✅ Alembic Issues:

- [ ] Run `python fix_alembic_now.py`
- [ ] Verify with `alembic current`
- [ ] Check migrations with `alembic history`
- [ ] If still broken, use `alembic stamp head`

### ✅ Gemini API Issues:

- [ ] Check `.env` has valid `GOOGLE_API_KEY`
- [ ] Test API key with curl command above
- [ ] Wait if rate limited (15 req/min, 1500 req/day)
- [ ] Generate new key if needed

### ✅ Database Issues:

- [ ] Can connect to database?
- [ ] Check `.env` database credentials
- [ ] Test connection: `psql -h HOST -U USER -d DATABASE`

---

## 🎯 Step-by-Step Recovery (Recommended)

### Step 1: Fix Alembic

```bash
# Run the fixed script
python fix_alembic_now.py

# Verify
alembic current
```

**Expected:** Shows `add_performance_indexes (head)`

### Step 2: Fix Gemini API

```bash
# Check your API key
echo $GOOGLE_API_KEY  # Linux/Mac
echo %GOOGLE_API_KEY%  # Windows CMD

# Or check .env file
cat .env | grep GOOGLE_API_KEY  # Linux/Mac
type .env | findstr GOOGLE_API_KEY  # Windows CMD
```

**If key is invalid:**
1. Go to https://makersuite.google.com/app/apikey
2. Create new API key
3. Update `.env` file
4. Restart backend

### Step 3: Test Everything

```bash
# Start backend
uvicorn backend.main:app --reload

# In another terminal, test API
curl http://localhost:8000/health

# Test Alembic
alembic current
```

---

## 🔍 Common Errors & Solutions

### Error: "Can't locate revision identified by 'xxxxx'"

**Solution:**
```bash
alembic stamp head
```

### Error: "Multiple head revisions are present"

**Solution:**
```bash
alembic merge heads -m "merge branches"
alembic upgrade head
```

### Error: "Target database is not up to date"

**Solution:**
```bash
git pull  # Get latest migrations
alembic upgrade head
```

### Error: "FOREIGN KEY constraint failed"

**Solution:**
```bash
# Check migration order
alembic history

# Downgrade and re-upgrade
alembic downgrade -1
alembic upgrade head
```

---

## 📞 Still Stuck?

### Debug Information to Collect:

```bash
# 1. Alembic current version
alembic current

# 2. Alembic history
alembic history

# 3. Database version
psql -h HOST -U USER -d DATABASE -c "SELECT * FROM alembic_version;"

# 4. Migration files
ls -la alembic/versions/

# 5. Error messages
# Copy the full error output
```

### Quick Diagnostic Script:

```bash
# Create diagnostic.py
cat > diagnostic.py << 'EOF'
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DATABASE_USERNAME')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOSTNAME')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"

print("🔍 BEACON Diagnostic")
print("=" * 50)

# Check database connection
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"✅ Database: Connected")
        print(f"   Version: {result.fetchone()[0][:50]}...")
        
        # Check alembic_version
        result = conn.execute(text("SELECT * FROM alembic_version"))
        version = result.fetchone()
        if version:
            print(f"✅ Alembic: {version[0]}")
        else:
            print(f"⚠️  Alembic: No version found")
except Exception as e:
    print(f"❌ Database: {e}")

# Check Gemini API
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content("Hello")
    print(f"✅ Gemini API: Working")
except Exception as e:
    print(f"❌ Gemini API: {e}")

print("=" * 50)
EOF

# Run it
python diagnostic.py
```

---

## 🎉 Success Indicators

You'll know everything is fixed when:

✅ `alembic current` shows correct version  
✅ `python fix_alembic_now.py` runs without errors  
✅ Backend starts without Alembic errors  
✅ Gemini API responds to queries  
✅ No database connection errors  

---

## 💡 Prevention Tips

### To Avoid This in the Future:

1. **Always backup before Alembic changes**
   ```bash
   pg_dump -h HOST -U USER -d DATABASE > backup_$(date +%Y%m%d).sql
   ```

2. **Test migrations on development first**
   ```bash
   # Never run migrations directly on production
   alembic upgrade head  # Test locally first
   ```

3. **Use version control for migrations**
   ```bash
   git add alembic/versions/
   git commit -m "Add migration: description"
   ```

4. **Document migration dependencies**
   - Note which migrations depend on others
   - Keep migration order clear

5. **Use Alembic branches for parallel development**
   ```bash
   alembic revision -m "feature A" --head=base
   alembic revision -m "feature B" --head=base
   alembic merge heads -m "merge features"
   ```

---

## 🚀 Quick Commands Reference

```bash
# Check status
alembic current
alembic history

# Apply migrations
alembic upgrade head
alembic upgrade +1  # Apply one migration

# Rollback
alembic downgrade -1
alembic downgrade base  # Rollback all

# Create migration
alembic revision --autogenerate -m "description"

# Fix broken state
alembic stamp head
python fix_alembic_now.py

# Emergency reset
alembic stamp base
alembic upgrade head
```

---

**Good luck! You got this! 🚀**

If the script still fails, try the manual SQL fix or the stamp command. Both are safe and effective.
