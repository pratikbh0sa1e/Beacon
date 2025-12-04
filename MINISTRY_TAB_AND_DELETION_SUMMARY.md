# Ministry Tab Visibility & Deletion - Summary

## ✅ Changes Implemented

### 1. Ministry Tab Visibility

**Before:**

```
All users see:
[Institutions] [Ministries]
```

**After:**

```
Developer sees:
[Institutions] [Ministries]

Ministry Admin sees:
[Institutions]  (only 1 tab)

University Admin sees:
[Institutions]  (only 1 tab)
```

**Why?**

- Ministry admins can't create/edit/delete ministries
- They only manage institutions under their ministry
- Showing a tab with only 1 item (their ministry) is confusing
- Cleaner, focused UI

---

### 2. Soft Delete System

**Added to Database:**

```sql
ALTER TABLE institutions ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE institutions ADD COLUMN deleted_by INTEGER REFERENCES users(id);
CREATE INDEX idx_institutions_deleted_at ON institutions(deleted_at);
```

**Benefits:**

- ✅ Can restore if mistake
- ✅ Maintains audit trail
- ✅ Preserves historical data
- ✅ Users can be reassigned later

---

### 3. Deletion Permissions

| Role             | Delete Ministries? | Delete Institutions?               |
| ---------------- | ------------------ | ---------------------------------- |
| Developer        | ✅ Yes             | ✅ Yes (all)                       |
| Ministry Admin   | ❌ No              | ✅ Yes (only under their ministry) |
| University Admin | ❌ No              | ❌ No                              |
| Others           | ❌ No              | ❌ No                              |

---

### 4. User Handling on Deletion

**When deleting an institution with users, admin must choose:**

#### Option 1: Convert to Public Viewer

```
Before: 50 students at IIT Delhi
After:  50 public viewers (no institution)
        - role = "public_viewer"
        - institution_id = NULL
        - approved = false (need re-approval)
```

#### Option 2: Transfer to Another Institution

```
Before: 50 students at IIT Delhi
After:  50 students at IIT Mumbai
        - role = unchanged
        - institution_id = IIT Mumbai
        - approved = false (need re-approval)
```

---

### 5. Ministry Deletion Restrictions

**Cannot delete ministry if:**

- ❌ Has active child institutions
- Must delete/transfer children first

**Example:**

```
❌ Cannot delete Ministry of Education
Reason: Has 3 active institutions
Action: Delete or transfer IIT Delhi, IIT Mumbai, Delhi University first
```

---

## 📁 Files Modified

### Backend:

1. `backend/database.py`:

   - ✅ Added `deleted_at` column
   - ✅ Added `deleted_by` column

2. `backend/routers/institution_router.py`:

   - ✅ Filter deleted institutions in `/list` endpoint
   - ✅ Filter deleted institutions in `/public` endpoint

3. `alembic/versions/add_soft_delete_to_institutions.py`:
   - ✅ Migration to add soft delete columns

### Frontend:

1. `frontend/src/pages/admin/InstitutionsPage.jsx`:
   - ✅ Hide Ministries tab for non-developers
   - ✅ Dynamic grid layout (1 or 2 columns based on role)

---

## 🧪 Testing

### Test 1: Ministry Tab Visibility

**As Developer:**

1. Login as developer
2. Go to: Admin → Institutions
3. ✅ Should see 2 tabs: [Institutions] [Ministries]

**As Ministry Admin:**

1. Login as ministry admin
2. Go to: Admin → Institutions
3. ✅ Should see 1 tab: [Institutions]
4. ❌ Should NOT see Ministries tab

---

### Test 2: Filtered Institution List

**As Ministry of Education Admin:**

1. Login
2. Go to: Admin → Institutions
3. ✅ Should see only institutions under Ministry of Education
4. ❌ Should NOT see AIIMS, DRDO, etc.

---

### Test 3: Soft Delete (After Full Implementation)

**Delete Institution:**

1. Login as developer
2. Delete IIT Delhi
3. Choose user action (convert or transfer)
4. ✅ Institution marked as deleted
5. ✅ Users handled according to choice
6. ✅ Institution no longer appears in lists

---

## 🚀 Next Steps (Optional - Full Deletion Feature)

### To Complete Deletion Feature:

1. **Add Delete Endpoint:**

   ```python
   @router.delete("/{institution_id}")
   async def delete_institution(...)
   ```

2. **Add Delete Button in UI:**

   ```jsx
   <Button variant="destructive" onClick={handleDelete}>
     Delete Institution
   </Button>
   ```

3. **Add Confirmation Dialog:**

   ```jsx
   <DeleteInstitutionDialog
     institution={selectedInstitution}
     onConfirm={handleConfirm}
   />
   ```

4. **Add User Migration Logic:**
   - Show user count
   - Offer convert/transfer options
   - Handle user reassignment

---

## ✅ Current Status

**Completed:**

- ✅ Ministry tab hidden for ministry admins
- ✅ Soft delete columns added to database
- ✅ Deleted institutions filtered from queries
- ✅ Migration created

**Ready for Implementation:**

- 📋 Delete endpoint (see INSTITUTION_DELETION_STRATEGY.md)
- 📋 Delete button in UI
- 📋 Confirmation dialog
- 📋 User migration logic

---

## 📊 Summary

### Ministry Tab:

- **Developer:** Sees Ministries tab ✅
- **Ministry Admin:** Does NOT see Ministries tab ❌
- **Reason:** Cleaner UI, they can't manage ministries anyway

### Deletion:

- **Soft Delete:** Institutions marked as deleted, not removed
- **User Handling:** Convert to public_viewer OR transfer to another institution
- **Permissions:** Developer can delete all, ministry admin can delete under their ministry
- **Restrictions:** Cannot delete ministry with active child institutions

### Benefits:

- ✅ Better UX for ministry admins
- ✅ Data safety with soft delete
- ✅ Flexible user migration
- ✅ Clear audit trail
- ✅ Can restore if needed

---

**Run Migration:**

```bash
alembic upgrade head
```

**Test:**

1. Login as ministry admin
2. Verify only 1 tab visible
3. Verify filtered institution list
