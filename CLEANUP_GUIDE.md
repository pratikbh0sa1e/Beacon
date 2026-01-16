# 🧹 Cleanup Guide - Remove Orphaned Files

## Problem

You have files in Supabase storage and session storage that don't exist in the database (no DB record).

**Current situation:**

- Session storage: 3258 documents
- Database: 299 documents
- **Gap:** ~2959 orphaned documents

## Solution

Use the cleanup script to remove orphaned files from:

1. **Supabase storage** - Files without database records
2. **Session storage** - Cached documents without database records

## Usage

### Step 1: Activate Virtual Environment

```bash
.\venv\Scripts\Activate.ps1
```

### Step 2: Run Cleanup Script

```bash
python cleanup_orphaned_files.py
```

### Step 3: Follow Prompts

The script will:

1. Show how many orphaned files found
2. Show sample of files to be deleted
3. Ask for confirmation
4. Delete orphaned files
5. Clean session storage
6. Show summary

## What Gets Deleted

### Supabase Storage:

- ❌ Files with no matching `s3_key` in database
- ✅ Files with matching `s3_key` in database (kept)

### Session Storage:

- ❌ Documents with no matching `source_url` or `s3_key` in database
- ✅ Documents with matching records in database (kept)

## Safety Features

✅ **Backup created** - Session storage backed up before cleaning  
✅ **Confirmation required** - Must type "yes" to delete  
✅ **Database untouched** - Only removes files, not DB records  
✅ **Dry-run info** - Shows what will be deleted before doing it

## Example Output

```
==============================================================
COMPREHENSIVE CLEANUP SCRIPT
==============================================================

This script will:
1. Remove orphaned files from Supabase storage
2. Remove orphaned documents from session storage

Continue? (y/n): y

==============================================================
CLEANING SUPABASE STORAGE
==============================================================

📦 Fetching files from bucket: Docs
📊 Found 3258 files in Supabase storage
📊 Database has 299 documents with S3 keys

📊 Found 2959 orphaned files (not in database)

🗑️  Sample of files to be deleted (first 10):
   1. scraped_20260115_181322_Public_Notice_regarding...
   2. scraped_20260115_181346_UGC_Public_Notice...
   ... and 2949 more

⚠️  WARNING: This will delete 2959 files from Supabase!
Continue with deletion? (yes/no): yes

🗑️  Deleting orphaned files...
   Deleted 10/2959 files...
   Deleted 20/2959 files...
   ...

✅ Supabase cleanup complete!
   Deleted: 2959 files
   Failed: 0 files

==============================================================
CLEANING SESSION STORAGE
==============================================================

📊 Session storage has 3258 documents
📊 Database has 299 documents

📊 Summary:
   Total in session storage: 3258
   Valid (in DB): 299
   Removed (not in DB): 2959

💾 Creating backup: data/web_scraping_sessions/scraped_documents.backup.json
💾 Saving cleaned data: data/web_scraping_sessions/scraped_documents.json

✅ Session storage cleanup complete!
   Session storage now has 299 documents

==============================================================
CLEANUP SUMMARY
==============================================================
Supabase files deleted: 2959
Session docs removed: 2959

✅ Cleanup complete!
```

## After Cleanup

**Expected results:**

- Supabase storage: 299 files (matches database)
- Session storage: 299 documents (matches database)
- Database: 299 documents (unchanged)

**Verify:**

1. Restart backend
2. Go to Web Scraping page
3. Check document count - should show 299

## Troubleshooting

### Issue: "Supabase credentials not found"

**Solution:** Check `.env` file has:

```env
SUPABASE_URL=your_url_here
SUPABASE_KEY=your_key_here
SUPABASE_BUCKET_NAME=Docs
```

### Issue: "Error accessing Supabase storage"

**Solution:** Check Supabase API key has storage permissions

### Issue: Script takes too long

**Expected:** Deleting 2959 files takes 5-10 minutes

### Issue: Some files fail to delete

**Normal:** Some files may be locked or in use. Check failed count in summary.

## Alternative: Clear Everything

If you want to start fresh and delete ALL files:

```bash
# WARNING: This deletes EVERYTHING from Supabase storage
python clear_session_storage.py
```

Then manually delete files from Supabase dashboard.

## Summary

✅ **Safe** - Creates backups before deleting  
✅ **Selective** - Only removes orphaned files  
✅ **Comprehensive** - Cleans both Supabase and session storage  
✅ **Verified** - Checks database before deleting

**Run the script to clean up your storage!** 🧹
