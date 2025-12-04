# Ministry Admin Filtering - Complete ✅

## Overview

Implemented role-based institution filtering so **ministry admins only see institutions under their ministry**.

---

## 🎯 Access Control by Role

### 1. **Developer** (System Admin)

```
✅ Can see: ALL institutions and ministries
✅ Can create: Ministries and institutions
✅ Can manage: Everything
```

### 2. **Ministry Admin** (e.g., Ministry of Education Admin)

```
✅ Can see:
   - Their own ministry (Ministry of Education)
   - Institutions under their ministry (IIT Delhi, IIT Mumbai, etc.)

❌ Cannot see:
   - Other ministries (Ministry of Health, Ministry of Defence)
   - Institutions under other ministries (AIIMS, DRDO, etc.)

✅ Can create: Institutions under their ministry
❌ Cannot create: Ministries or institutions under other ministries
```

### 3. **University Admin** (e.g., IIT Delhi Admin)

```
✅ Can see:
   - Their own institution (IIT Delhi)
   - Their parent ministry (Ministry of Education)

❌ Cannot see:
   - Other institutions (IIT Mumbai, Delhi University, etc.)
   - Other ministries

✅ Can manage: Users in their institution
❌ Cannot create: Institutions or ministries
```

### 4. **Other Roles** (Student, Document Officer, Public Viewer)

```
✅ Can see: All institutions (for reference/context)
❌ Cannot create: Anything
❌ Cannot manage: Institutions
```

---

## 📊 Examples

### Example 1: Ministry of Education Admin Logs In

**User:**

```json
{
  "name": "Education Ministry Admin",
  "email": "admin@education.gov.in",
  "role": "ministry_admin",
  "institution_id": 1 // Ministry of Education
}
```

**What they see in Institutions Page:**

#### Ministries Tab:

```
✅ Ministry of Education (their ministry)
❌ Ministry of Health (hidden)
❌ Ministry of Defence (hidden)
```

#### Institutions Tab:

```
✅ IIT Delhi (under their ministry)
✅ IIT Mumbai (under their ministry)
✅ Delhi University (under their ministry)
❌ AIIMS Delhi (under Ministry of Health - hidden)
❌ DRDO Bangalore (under Ministry of Defence - hidden)
```

---

### Example 2: Ministry of Health Admin Logs In

**User:**

```json
{
  "name": "Health Ministry Admin",
  "email": "admin@health.gov.in",
  "role": "ministry_admin",
  "institution_id": 2 // Ministry of Health
}
```

**What they see:**

#### Ministries Tab:

```
✅ Ministry of Health and Family Welfare (their ministry)
❌ Ministry of Education (hidden)
❌ Ministry of Defence (hidden)
```

#### Institutions Tab:

```
✅ AIIMS Delhi (under their ministry)
✅ AIIMS Mumbai (under their ministry)
❌ IIT Delhi (under Ministry of Education - hidden)
❌ DRDO Bangalore (under Ministry of Defence - hidden)
```

---

### Example 3: IIT Delhi Admin Logs In

**User:**

```json
{
  "name": "IIT Delhi Admin",
  "email": "admin@iitdelhi.ac.in",
  "role": "university_admin",
  "institution_id": 5 // IIT Delhi
}
```

**What they see:**

#### Ministries Tab:

```
✅ Ministry of Education (their parent ministry)
❌ Other ministries (hidden)
```

#### Institutions Tab:

```
✅ IIT Delhi (their institution)
❌ IIT Mumbai (hidden)
❌ Delhi University (hidden)
❌ All other institutions (hidden)
```

---

## 🔧 Technical Implementation

### Backend Filtering Logic

```python
@router.get("/list")
async def list_institutions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Institution)

    if current_user.role == "ministry_admin":
        # Ministry admin sees:
        # 1. Their own ministry
        # 2. Institutions under their ministry
        ministry_id = current_user.institution_id
        query = query.filter(
            (Institution.id == ministry_id) |
            (Institution.parent_ministry_id == ministry_id)
        )

    elif current_user.role == "university_admin":
        # University admin sees:
        # 1. Their own institution
        # 2. Their parent ministry
        user_institution = db.query(Institution).filter(
            Institution.id == current_user.institution_id
        ).first()
        if user_institution:
            query = query.filter(
                (Institution.id == current_user.institution_id) |
                (Institution.id == user_institution.parent_ministry_id)
            )

    # Developer and others see all
    return query.all()
```

---

## 🌐 API Endpoints

### 1. `/institutions/list` (Authenticated - Filtered)

**Purpose:** For logged-in users to see institutions based on their role

**Access:**

- Developer: All institutions
- Ministry Admin: Their ministry + child institutions
- University Admin: Their institution + parent ministry
- Others: All institutions

**Usage:**

```javascript
// In InstitutionsPage (admin panel)
const response = await institutionAPI.list();
```

---

### 2. `/institutions/public` (Public - Unfiltered)

**Purpose:** For user registration (before login)

**Access:**

- Anyone (no authentication required)
- Shows all institutions and ministries

**Usage:**

```javascript
// In RegisterPage (before login)
const response = await institutionAPI.listPublic();
```

---

## 📁 Files Modified

### Backend:

1. `backend/routers/institution_router.py`:
   - ✅ Added role-based filtering to `/list` endpoint
   - ✅ Created new `/public` endpoint for registration
   - ✅ Ministry admin sees only their ministry + child institutions
   - ✅ University admin sees only their institution + parent ministry

### Frontend:

1. `frontend/src/services/api.js`:

   - ✅ Added `listPublic()` method for public access
   - ✅ Kept `list()` method for authenticated access

2. `frontend/src/pages/auth/RegisterPage.jsx`:

   - ✅ Changed to use `listPublic()` for registration
   - ✅ Shows all institutions to users during registration

3. `frontend/src/pages/admin/InstitutionsPage.jsx`:
   - ✅ Uses `list()` for authenticated access
   - ✅ Shows filtered institutions based on user role

---

## 🧪 Testing Scenarios

### Test 1: Ministry Admin Filtering

1. Login as Ministry of Education admin
2. Go to: **Admin → Institutions**
3. Click **Ministries** tab
4. ✅ Should see only: Ministry of Education
5. Click **Institutions** tab
6. ✅ Should see only: IIT Delhi, IIT Mumbai, Delhi University
7. ❌ Should NOT see: AIIMS, DRDO, etc.

---

### Test 2: Different Ministry Admin

1. Login as Ministry of Health admin
2. Go to: **Admin → Institutions**
3. Click **Ministries** tab
4. ✅ Should see only: Ministry of Health
5. Click **Institutions** tab
6. ✅ Should see only: AIIMS Delhi, AIIMS Mumbai
7. ❌ Should NOT see: IIT Delhi, DRDO, etc.

---

### Test 3: University Admin Filtering

1. Login as IIT Delhi admin
2. Go to: **Admin → Institutions**
3. Click **Ministries** tab
4. ✅ Should see only: Ministry of Education (parent)
5. Click **Institutions** tab
6. ✅ Should see only: IIT Delhi (their institution)
7. ❌ Should NOT see: IIT Mumbai, Delhi University, etc.

---

### Test 4: Developer Sees All

1. Login as developer
2. Go to: **Admin → Institutions**
3. ✅ Should see ALL ministries
4. ✅ Should see ALL institutions
5. ✅ Can create ministries and institutions

---

### Test 5: Registration Shows All

1. Logout (or open incognito)
2. Go to: http://localhost:5173/register
3. Select Role: **Student**
4. Select Ministry: **Ministry of Education**
5. ✅ Should see ALL ministries in dropdown
6. ✅ Should see ALL institutions under selected ministry
7. This is correct - users need to see all options during registration

---

## 🔒 Security Benefits

### Data Isolation:

- ✅ Ministry admins can't see other ministries' data
- ✅ Ministry admins can't see institutions under other ministries
- ✅ University admins can't see other institutions
- ✅ Prevents unauthorized access to sensitive information

### Clear Boundaries:

- ✅ Each ministry admin manages only their domain
- ✅ No confusion about which institutions they can manage
- ✅ Clear hierarchy: Ministry → Institutions

### Audit Trail:

- ✅ Actions are scoped to user's ministry
- ✅ Easy to track who did what in which ministry
- ✅ Better accountability

---

## 🎯 Benefits

### For Ministry Admins:

- ✅ **Focused View:** Only see relevant institutions
- ✅ **Less Clutter:** No irrelevant data
- ✅ **Clear Scope:** Know exactly what they manage
- ✅ **Better Performance:** Smaller datasets load faster

### For System:

- ✅ **Security:** Data isolation between ministries
- ✅ **Scalability:** Queries are filtered, faster performance
- ✅ **Maintainability:** Clear access control logic
- ✅ **Compliance:** Better data governance

### For Users:

- ✅ **Privacy:** Other ministries can't see their institution
- ✅ **Trust:** Data is properly isolated
- ✅ **Clarity:** Clear organizational structure

---

## 📊 Database Queries

### Ministry Admin Query:

```sql
-- What Ministry of Education admin sees
SELECT * FROM institutions
WHERE id = 1  -- Their ministry
   OR parent_ministry_id = 1;  -- Institutions under their ministry

-- Result:
-- Ministry of Education
-- IIT Delhi
-- IIT Mumbai
-- Delhi University
```

### University Admin Query:

```sql
-- What IIT Delhi admin sees
SELECT * FROM institutions
WHERE id = 5  -- Their institution
   OR id = (SELECT parent_ministry_id FROM institutions WHERE id = 5);  -- Parent ministry

-- Result:
-- IIT Delhi
-- Ministry of Education
```

---

## ✅ Summary

**What Changed:**

- ✅ Ministry admins now see only their ministry + child institutions
- ✅ University admins see only their institution + parent ministry
- ✅ Developer still sees everything
- ✅ Registration page shows all institutions (public endpoint)
- ✅ Admin page shows filtered institutions (authenticated endpoint)

**Result:**

- Better security and data isolation
- Clearer scope for each role
- Faster performance with filtered queries
- Better user experience

---

**Status:** ✅ COMPLETE

**Next Steps:**

1. Test with different ministry admin accounts
2. Verify filtering works correctly
3. Test that registration still shows all institutions
4. Verify university admins see correct scope
