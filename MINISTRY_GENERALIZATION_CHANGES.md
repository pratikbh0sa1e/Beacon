# Ministry Generalization - Required Changes

## Overview

Change system from "MoE-specific" to "Multi-Ministry" support to accommodate any government ministry (Education, Health, Finance, etc.)

---

## 1. Database Changes

### **A. Users Table - Role Rename**

```sql
-- Update existing role
UPDATE users
SET role = 'ministry_admin'
WHERE role = 'MINISTRY_ADMIN';

-- Update any role checks in constraints
-- (Check if there are any ENUM constraints)
```

### **B. Institutions Table - Add Ministry Type**

```sql
-- Ensure type column supports 'ministry'
-- Current types: 'university', 'government_dept'
-- Add: 'ministry'

-- Example ministries to add:
INSERT INTO institutions (name, type, location) VALUES
('Ministry of Education', 'ministry', 'New Delhi'),
('Ministry of Health', 'ministry', 'New Delhi'),
('Ministry of Finance', 'ministry', 'New Delhi'),
('Department of Higher Education', 'government_dept', 'New Delhi');
```

### **C. Documents Table - Add Ministry Visibility**

```sql
-- Add new visibility type for ministry-only documents
-- Current: 'public', 'institutional', 'national'
-- Add: 'ministry_only'

-- This will be used for confidential ministry data
```

---

## 2. Backend Changes

### **A. Constants/Roles**

**File:** `backend/constants/roles.py`

```python
# BEFORE
MINISTRY_ADMIN = "ministry_admin"
ADMIN_ROLES = ["developer", "ministry_admin"]

# AFTER
MINISTRY_ADMIN = "ministry_admin"
ADMIN_ROLES = ["developer", "ministry_admin"]
```

### **B. All Router Files - Role Checks**

**Files to Update:**

- `backend/routers/auth_router.py`
- `backend/routers/user_router.py`
- `backend/routers/document_router.py`
- `backend/routers/approval_router.py`
- `backend/routers/notification_router.py`
- `backend/routers/data_source_router.py`
- `backend/routers/audit_router.py`

**Changes:**

```python
# BEFORE
if current_user.role != "ministry_admin":
    raise HTTPException(...)

if current_user.role in ["developer", "ministry_admin"]:
    # Allow access

# AFTER
if current_user.role != "ministry_admin":
    raise HTTPException(...)

if current_user.role in ["developer", "ministry_admin"]:
    # Allow access
```

**Search Pattern:** `"ministry_admin"` → Replace with `"ministry_admin"`

### **C. Document Access Control**

**File:** `backend/routers/document_router.py`

**Add Ministry-Only Visibility Logic:**

```python
# In document list/get endpoints
if user.role == "ministry_admin":
    # Can see:
    # 1. Public documents
    # 2. National documents
    # 3. Their ministry's confidential documents
    query = query.filter(
        (Document.visibility == "public") |
        (Document.visibility == "national") |
        (
            (Document.visibility == "ministry_only") &
            (Document.institution_id == user.institution_id)
        )
    )
```

### **D. Notification Helper**

**File:** `backend/utils/notification_helper.py`

**Update Notification Routing:**

```python
# BEFORE
def notify_MINISTRY_ADMINs(db, message):
    MINISTRY_ADMINs = db.query(User).filter(User.role == "ministry_admin").all()
    # ...

# AFTER
def notify_ministry_admins(db, message, ministry_id=None):
    """
    Notify ministry admins
    If ministry_id provided, notify only that ministry
    Otherwise notify all ministry admins
    """
    query = db.query(User).filter(User.role == "ministry_admin")
    if ministry_id:
        query = query.filter(User.institution_id == ministry_id)
    ministry_admins = query.all()
    # ...
```

### **E. Document Workflow**

**File:** `backend/routers/document_router.py`

**Update Auto-Approval Logic:**

```python
# BEFORE
if uploader.role == "ministry_admin":
    # Auto-approve MoE uploads
    new_document.approval_status = "approved"

# AFTER
if uploader.role == "ministry_admin":
    # Auto-approve ministry uploads
    new_document.approval_status = "approved"
```

---

## 3. Frontend Changes

### **A. Constants/Roles**

**File:** `frontend/src/constants/roles.js`

```javascript
// BEFORE
export const MINISTRY_ADMIN = "ministry_admin";
export const ADMIN_ROLES = ["developer", "ministry_admin"];

// AFTER
export const MINISTRY_ADMIN = "ministry_admin";
export const ADMIN_ROLES = ["developer", "ministry_admin"];
```

### **B. All Component Files - Role Checks**

**Files to Update:**

- `frontend/src/components/layout/Sidebar.jsx`
- `frontend/src/components/layout/Header.jsx`
- `frontend/src/pages/DashboardPage.jsx`
- `frontend/src/pages/documents/DocumentDetailPage.jsx`
- `frontend/src/pages/documents/DocumentExplorerPage.jsx`
- `frontend/src/pages/documents/ApprovalsPage.jsx`
- `frontend/src/pages/admin/*`

**Changes:**

```javascript
// BEFORE
{
  user?.role === "ministry_admin" && <Button>...</Button>;
}

// AFTER
{
  user?.role === "ministry_admin" && <Button>...</Button>;
}
```

**Search Pattern:** `"ministry_admin"` → Replace with `"ministry_admin"`

### **C. UI Text Updates**

**Files to Update:**

- All pages with "MoE" text
- Sidebar menu items
- Dashboard cards
- Approval pages

**Changes:**

```javascript
// BEFORE
<h1>MoE Admin Dashboard</h1>
<p>Ministry of Education Administrator</p>

// AFTER
<h1>Ministry Admin Dashboard</h1>
<p>Ministry Administrator</p>

// Show ministry name dynamically
<p>{user?.institution?.name} Administrator</p>
```

### **D. Registration Page**

**File:** `frontend/src/pages/auth/RegisterPage.jsx`

**Update Role Dropdown:**

```javascript
// BEFORE
<option value="ministry_admin">MoE Administrator</option>

// AFTER
<option value="ministry_admin">Ministry Administrator</option>
```

**Add Ministry Selection:**

```javascript
{
  selectedRole === "ministry_admin" && (
    <select name="institution_id">
      <option value="">Select Ministry</option>
      {ministries.map((ministry) => (
        <option value={ministry.id}>{ministry.name}</option>
      ))}
    </select>
  );
}
```

### **E. Document Upload Page**

**File:** `frontend/src/pages/documents/DocumentUploadPage.jsx`

**Update Auto-Approval Message:**

```javascript
// BEFORE
{
  user?.role === "ministry_admin" && (
    <Alert>Your documents will be auto-approved as MoE Admin</Alert>
  );
}

// AFTER
{
  user?.role === "ministry_admin" && (
    <Alert>
      Your documents will be auto-approved as Ministry Administrator
    </Alert>
  );
}
```

---

## 4. Search & Replace Summary

### **Backend Files:**

```bash
# Search for: "ministry_admin"
# Replace with: "ministry_admin"

# Files affected:
- backend/constants/roles.py
- backend/routers/*.py (all routers)
- backend/utils/notification_helper.py
- backend/database.py (if role is in comments)
```

### **Frontend Files:**

```bash
# Search for: "ministry_admin"
# Replace with: "ministry_admin"

# Search for: "MoE Admin"
# Replace with: "Ministry Admin"

# Search for: "Ministry of Education"
# Replace with: Dynamic institution name

# Files affected:
- frontend/src/constants/roles.js
- frontend/src/pages/**/*.jsx (all pages)
- frontend/src/components/**/*.jsx (all components)
```

---

## 5. Testing Checklist

### **Backend:**

- [ ] All API endpoints accept `ministry_admin` role
- [ ] Document access control works for ministry admins
- [ ] Auto-approval works for ministry uploads
- [ ] Notifications route to correct ministry admins
- [ ] Ministry-only visibility enforced

### **Frontend:**

- [ ] Registration shows "Ministry Administrator" option
- [ ] Ministry selection dropdown appears
- [ ] Dashboard shows ministry name dynamically
- [ ] Sidebar menu items visible to ministry admin
- [ ] Document upload works for ministry admin
- [ ] Approval page accessible to ministry admin

### **Database:**

- [ ] Existing `MINISTRY_ADMIN` users updated to `ministry_admin`
- [ ] Ministry institutions exist in database
- [ ] Users linked to correct ministry institution
- [ ] Documents have correct visibility

---

## 6. Migration Script

**File:** `alembic/versions/generalize_ministry_role.py`

```python
"""generalize ministry role

Revision ID: generalize_ministry_001
Revises: add_user_notes_001
Create Date: 2024-12-03 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = 'generalize_ministry_001'
down_revision = 'add_user_notes_001'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Update role from MINISTRY_ADMIN to ministry_admin
    op.execute("""
        UPDATE users
        SET role = 'ministry_admin'
        WHERE role = 'MINISTRY_ADMIN'
    """)

    # 2. Ensure Ministry of Education exists
    op.execute("""
        INSERT INTO institutions (name, type, location, created_at)
        VALUES ('Ministry of Education', 'ministry', 'New Delhi', NOW())
        ON CONFLICT (name) DO NOTHING
    """)

    # 3. Link existing ministry_admin users to MoE if not linked
    op.execute("""
        UPDATE users
        SET institution_id = (
            SELECT id FROM institutions
            WHERE name = 'Ministry of Education'
            LIMIT 1
        )
        WHERE role = 'ministry_admin'
        AND institution_id IS NULL
    """)


def downgrade():
    # Revert changes
    op.execute("""
        UPDATE users
        SET role = 'MINISTRY_ADMIN'
        WHERE role = 'ministry_admin'
    """)
```

---

## 7. Implementation Steps

### **Step 1: Database Migration**

```bash
# Create migration
alembic revision -m "generalize_ministry_role"

# Edit migration file (see above)

# Run migration
alembic upgrade head
```

### **Step 2: Backend Updates**

1. Update `backend/constants/roles.py`
2. Search & replace `"ministry_admin"` → `"ministry_admin"` in all backend files
3. Update notification helper
4. Update document access control
5. Test all API endpoints

### **Step 3: Frontend Updates**

1. Update `frontend/src/constants/roles.js`
2. Search & replace `"ministry_admin"` → `"ministry_admin"` in all frontend files
3. Update UI text (MoE → Ministry)
4. Add dynamic institution name display
5. Update registration page
6. Test all pages

### **Step 4: Testing**

1. Test existing ministry admin users
2. Test registration with ministry selection
3. Test document upload/approval
4. Test access control
5. Test notifications

### **Step 5: Documentation**

1. Update README
2. Update API documentation
3. Update user guides

---

## 8. Affected Files List

### **Backend (Python):**

```
backend/constants/roles.py
backend/routers/auth_router.py
backend/routers/user_router.py
backend/routers/document_router.py
backend/routers/approval_router.py
backend/routers/notification_router.py
backend/routers/data_source_router.py
backend/routers/audit_router.py
backend/utils/notification_helper.py
alembic/versions/generalize_ministry_role.py (new)
```

### **Frontend (JavaScript/JSX):**

```
frontend/src/constants/roles.js
frontend/src/components/layout/Sidebar.jsx
frontend/src/components/layout/Header.jsx
frontend/src/pages/DashboardPage.jsx
frontend/src/pages/auth/RegisterPage.jsx
frontend/src/pages/auth/LoginPage.jsx
frontend/src/pages/documents/DocumentDetailPage.jsx
frontend/src/pages/documents/DocumentExplorerPage.jsx
frontend/src/pages/documents/DocumentUploadPage.jsx
frontend/src/pages/documents/ApprovalsPage.jsx
frontend/src/pages/admin/UserManagementPage.jsx
frontend/src/pages/admin/DocumentApprovalsPage.jsx
```

---

## 9. Backward Compatibility

### **Handling Existing Data:**

- Migration script updates all `MINISTRY_ADMIN` → `ministry_admin`
- Existing documents remain unchanged
- Existing notifications remain valid
- No data loss

### **API Compatibility:**

- Old API calls with `MINISTRY_ADMIN` will fail (intentional)
- Frontend must be updated simultaneously
- Consider adding deprecation warning

---

## 10. Post-Implementation

### **Add More Ministries:**

```sql
INSERT INTO institutions (name, type, location) VALUES
('Ministry of Health and Family Welfare', 'ministry', 'New Delhi'),
('Ministry of Finance', 'ministry', 'New Delhi'),
('Ministry of Home Affairs', 'ministry', 'New Delhi'),
('Ministry of Defence', 'ministry', 'New Delhi');
```

### **Create Ministry Admin Users:**

```sql
-- Example: Create Health Ministry Admin
INSERT INTO users (name, email, password_hash, role, institution_id, approved, email_verified)
VALUES (
    'Health Ministry Admin',
    'admin@health.gov.in',
    '<hashed_password>',
    'ministry_admin',
    (SELECT id FROM institutions WHERE name = 'Ministry of Health and Family Welfare'),
    true,
    true
);
```

---

## Estimated Time: 4-6 hours

- Database migration: 30 mins
- Backend updates: 2 hours
- Frontend updates: 2 hours
- Testing: 1-2 hours

---

**Status:** Ready to Implement

**Priority:** HIGH (Required before External Data Source feature)

**Last Updated:** December 3, 2024
