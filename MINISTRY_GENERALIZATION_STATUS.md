# Ministry Generalization - Implementation Status

## ✅ Completed

### 1. Database Migration

- ✅ Created `alembic/versions/generalize_ministry_role.py`
- ✅ Updates `MINISTRY_ADMIN` → `ministry_admin` in users table
- ✅ Adds Ministry of Education and other ministries to institutions
- ✅ Links existing ministry admins to MoE

### 2. Backend Constants

- ✅ Updated `backend/constants/roles.py`
- ✅ Changed `MINISTRY_ADMIN` → `MINISTRY_ADMIN`
- ✅ Updated role groups and display names
- ✅ Added backward compatibility alias

### 3. Frontend Constants

- ✅ Updated `frontend/src/constants/roles.js`
- ✅ Changed `MINISTRY_ADMIN` → `MINISTRY_ADMIN`
- ✅ Updated role groups and display names
- ✅ Added backward compatibility alias

### 4. Notification Helper

- ✅ Updated `backend/utils/notification_helper.py`
- ✅ Changed references from `MINISTRY_ADMIN` to `ministry_admin`
- ✅ Updated comments and variable names

## 🔄 Remaining Backend Files (Need Manual Update)

Due to the large number of occurrences (50+), these files need systematic updates:

### Critical Files:

1. `backend/routers/user_router.py` - 15 occurrences
2. `backend/routers/document_router.py` - 8 occurrences
3. `backend/routers/insights_router.py` - 12 occurrences
4. `backend/routers/institution_router.py` - 4 occurrences
5. `backend/routers/institution_domain_router.py` - 8 occurrences
6. `backend/utils/email_validator.py` - 6 occurrences

### Pattern to Replace:

```python
# Find: "ministry_admin"
# Replace with: "ministry_admin"

# Find: MINISTRY_ADMINs
# Replace with: ministry_admins

# Find: MoE Admin
# Replace with: Ministry Admin

# Find: MoE admin
# Replace with: Ministry admin
```

## 🔄 Remaining Frontend Files

### Files with Role Checks:

1. `frontend/src/components/layout/Sidebar.jsx`
2. `frontend/src/pages/auth/RegisterPage.jsx`
3. `frontend/src/pages/documents/DocumentDetailPage.jsx`
4. `frontend/src/pages/documents/DocumentUploadPage.jsx`
5. `frontend/src/pages/documents/ApprovalsPage.jsx`
6. All admin pages

### Pattern to Replace:

```javascript
// Find: "ministry_admin"
// Replace with: "ministry_admin"

// Find: MINISTRY_ADMIN
// Replace with: MINISTRY_ADMIN

// Find: "MoE Admin"
// Replace with: "Ministry Admin"
```

## 📝 Next Steps

### Option A: Manual Search & Replace (Recommended)

Use your IDE's global search & replace:

1. Search: `"ministry_admin"` → Replace: `"ministry_admin"` (in all .py files)
2. Search: `"ministry_admin"` → Replace: `"ministry_admin"` (in all .js/.jsx files)
3. Search: `MINISTRY_ADMIN` → Replace: `MINISTRY_ADMIN` (in all files)
4. Search: `MoE Admin` → Replace: `Ministry Admin` (in all files)

### Option B: Continue with Kiro

I can continue updating files one by one, but it will take many iterations.

## ⚠️ Important Notes

1. **Test After Changes:**

   - Run migration: `alembic upgrade head`
   - Restart backend
   - Test login with ministry admin
   - Test document upload/approval
   - Test notifications

2. **Backward Compatibility:**

   - Constants have aliases for backward compatibility
   - Database migration handles existing users
   - No data loss expected

3. **UI Text Updates:**
   - Some UI text still says "MoE" - needs manual review
   - Dashboard titles, page headers, etc.
   - Consider making these dynamic based on institution name

## 🎯 Completion Checklist

- [x] Database migration created
- [x] Backend constants updated
- [x] Frontend constants updated
- [x] Notification helper updated
- [ ] All backend routers updated
- [ ] All frontend components updated
- [ ] Migration tested
- [ ] End-to-end testing complete
- [ ] Documentation updated

## 🚀 Ready to Complete?

**Recommended Approach:**

1. Use IDE global search & replace for remaining files
2. Run migration
3. Test thoroughly
4. Then proceed with External Data Source implementation

**Estimated Time Remaining:** 30-60 minutes for search & replace + testing
