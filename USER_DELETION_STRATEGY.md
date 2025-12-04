# User Deletion Strategy

## 🎯 Recommended Approach: Soft Delete for Users Too

### Why Soft Delete Users?

**Problems with Hard Delete:**

- ❌ Breaks audit trail (who did what?)
- ❌ Loses historical data
- ❌ Foreign key constraints everywhere
- ❌ Documents lose uploader/approver info
- ❌ Cannot restore if mistake

**Benefits of Soft Delete:**

- ✅ Preserves audit trail
- ✅ Maintains data integrity
- ✅ Can restore if needed
- ✅ No foreign key issues
- ✅ Historical data intact

---

## 📋 Implementation Strategy

### Option 1: Soft Delete (Recommended) ⭐

**Add to users table:**

```sql
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN deleted_by INTEGER REFERENCES users(id);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
```

**Benefits:**

- User account marked as deleted
- Cannot login
- Data preserved
- Can be restored
- Audit trail intact

---

### Option 2: Hard Delete with Proper Foreign Keys

**Fix all foreign key constraints:**

```sql
-- Preserve audit trail
ALTER TABLE audit_logs
  ALTER COLUMN user_id DROP NOT NULL,
  DROP CONSTRAINT audit_logs_user_id_fkey,
  ADD CONSTRAINT audit_logs_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE SET NULL;

-- Preserve documents
ALTER TABLE documents
  DROP CONSTRAINT documents_uploader_id_fkey,
  ADD CONSTRAINT documents_uploader_id_fkey
    FOREIGN KEY (uploader_id) REFERENCES users(id)
    ON DELETE SET NULL;

-- Delete user data
ALTER TABLE bookmarks
  DROP CONSTRAINT bookmarks_user_id_fkey,
  ADD CONSTRAINT bookmarks_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id)
    ON DELETE CASCADE;
```

---

## 🔧 Foreign Key Strategy

### Tables and Their ON DELETE Behavior:

| Table           | Column        | ON DELETE    | Reason                      |
| --------------- | ------------- | ------------ | --------------------------- |
| `audit_logs`    | `user_id`     | **SET NULL** | Preserve audit trail        |
| `documents`     | `uploader_id` | **SET NULL** | Preserve document           |
| `documents`     | `approved_by` | **SET NULL** | Preserve document           |
| `bookmarks`     | `user_id`     | **CASCADE**  | Delete user's bookmarks     |
| `chat_sessions` | `user_id`     | **CASCADE**  | Delete user's chats         |
| `chat_messages` | (via session) | **CASCADE**  | Delete with session         |
| `user_notes`    | `user_id`     | **CASCADE**  | Delete user's notes         |
| `notifications` | `user_id`     | **CASCADE**  | Delete user's notifications |

---

## 💻 Implementation

### Migration (Already Created):

```bash
# Run this migration to fix foreign keys
alembic upgrade head
```

This will:

- ✅ Fix `audit_logs` foreign key (SET NULL)
- ✅ Fix `documents` foreign keys (SET NULL)
- ✅ Fix `bookmarks` foreign key (CASCADE)
- ✅ Fix `chat_sessions` foreign key (CASCADE)
- ✅ Fix `user_notes` foreign key (CASCADE)

---

### After Migration, You Can:

#### Option A: Delete User Directly from Database

```sql
-- Now this will work!
DELETE FROM users WHERE id = 8;

-- What happens:
-- ✅ audit_logs.user_id = NULL (audit preserved)
-- ✅ documents.uploader_id = NULL (document preserved)
-- ✅ documents.approved_by = NULL (document preserved)
-- ✅ bookmarks deleted (CASCADE)
-- ✅ chat_sessions deleted (CASCADE)
-- ✅ user_notes deleted (CASCADE)
```

#### Option B: Soft Delete (Better)

```sql
-- Add soft delete columns first
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE users ADD COLUMN deleted_by INTEGER REFERENCES users(id);

-- Then "delete" user
UPDATE users
SET deleted_at = NOW(),
    deleted_by = 1  -- admin user id
WHERE id = 8;

-- Filter in queries
SELECT * FROM users WHERE deleted_at IS NULL;
```

---

## 🚫 No Delete Account Button (Good Decision!)

### Why No Self-Delete?

**Reasons to NOT allow users to delete their own accounts:**

1. **Data Integrity:**

   - Documents they uploaded should remain
   - Audit trail must be preserved
   - Other users may reference their work

2. **Legal/Compliance:**

   - May need to retain data for audits
   - Government systems have retention policies
   - Cannot just delete historical records

3. **Better Alternative:**
   - **Deactivate** account instead
   - User cannot login
   - Data preserved
   - Can be reactivated if needed

---

## 🎯 Recommended User Management

### Instead of Delete, Implement:

#### 1. **Deactivate Account**

```python
@router.post("/deactivate")
async def deactivate_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User can deactivate their own account"""
    current_user.approved = False
    current_user.email_verified = False
    db.commit()

    return {"message": "Account deactivated. Contact admin to reactivate."}
```

#### 2. **Admin Soft Delete**

```python
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Only developers can soft delete users"""
    if current_user.role != "developer":
        raise HTTPException(403, "Only developers can delete users")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")

    # Soft delete
    user.deleted_at = datetime.utcnow()
    user.deleted_by = current_user.id
    db.commit()

    return {"message": f"User {user.email} deleted successfully"}
```

#### 3. **Filter Deleted Users**

```python
# In all queries
query = db.query(User).filter(User.deleted_at == None)
```

---

## 📊 What Happens When User is Deleted?

### Example: Delete Student User

**Before:**

```
User: john@iitdelhi.ac.in
├── 5 Documents uploaded
├── 10 Bookmarks
├── 3 Chat sessions
├── 50 Audit log entries
└── 2 Notes
```

**After Hard Delete (with fixed foreign keys):**

```
User: DELETED

Documents (preserved):
├── 5 Documents (uploader_id = NULL)
└── Shows "Uploaded by: [Deleted User]"

Deleted:
├── 10 Bookmarks (CASCADE)
├── 3 Chat sessions (CASCADE)
└── 2 Notes (CASCADE)

Preserved:
└── 50 Audit log entries (user_id = NULL)
    Shows: "[Deleted User] uploaded document X"
```

**After Soft Delete (recommended):**

```
User: john@iitdelhi.ac.in (deleted_at = 2024-12-04)
├── Cannot login
├── All data preserved
├── Can be restored
└── Audit trail intact
```

---

## 🎨 UI Considerations

### Profile/Settings Page

**Don't Show:**

- ❌ "Delete Account" button
- ❌ "Permanently Remove Data" button

**Do Show:**

- ✅ "Deactivate Account" button
- ✅ "Request Account Deletion" (sends request to admin)
- ✅ Clear explanation of what happens

**Example UI:**

```jsx
<Card>
  <CardHeader>
    <CardTitle>Account Management</CardTitle>
  </CardHeader>
  <CardContent>
    <Alert>
      <Info className="h-4 w-4" />
      <AlertDescription>
        To delete your account, please contact your institution administrator.
        Your data will be preserved for audit purposes.
      </AlertDescription>
    </Alert>

    <Button variant="outline" onClick={handleDeactivate}>
      Deactivate Account
    </Button>
  </CardContent>
</Card>
```

---

## ✅ Summary

### Foreign Key Fix:

- ✅ Migration created to fix all foreign key constraints
- ✅ `audit_logs`: SET NULL (preserve audit trail)
- ✅ `documents`: SET NULL (preserve documents)
- ✅ `bookmarks`: CASCADE (delete with user)
- ✅ `chat_sessions`: CASCADE (delete with user)
- ✅ `user_notes`: CASCADE (delete with user)

### User Deletion:

- ✅ **Recommended:** Soft delete (add deleted_at column)
- ✅ **Alternative:** Hard delete (now works with fixed foreign keys)
- ❌ **Not Recommended:** Allow users to self-delete

### No Delete Button:

- ✅ Good decision!
- ✅ Preserves data integrity
- ✅ Maintains audit trail
- ✅ Complies with retention policies
- ✅ Offer "Deactivate" instead

### Next Steps:

1. Run migration: `alembic upgrade head`
2. Test user deletion from database (should work now)
3. Optionally add soft delete columns to users table
4. Implement deactivate account feature
5. Add admin user management page

---

## 🚀 Run Migration Now

```bash
# This will fix all foreign key constraints
alembic upgrade head

# After this, you can delete users from database without errors
# But consider implementing soft delete instead!
```

**The foreign key error will be fixed!** ✅
