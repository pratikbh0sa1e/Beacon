# Registration and Permissions Fixes

## Issues to Fix:

### 1. User Registration - Add Ministry Filter for University Users

**Current:** University users see ALL universities
**Target:** University users select ministry first, then see only that ministry's universities

### 2. Institution Registration Button Visibility

**Current:** All admins can see button
**Target:**

- Only **Developer** can register ministries
- **Developer + Ministry Admin** can register universities/departments

### 3. Backend Permission Check

**Current:** Developer + Ministry Admin can create any institution type
**Target:**

- **Developer** → Can create ministries, universities, departments
- **Ministry Admin** → Can ONLY create universities/departments (NOT ministries)

---

## Implementation Plan:

### Fix 1: User Registration - Two-Step Selection

For university roles (student, document_officer, university_admin):

```javascript
Step 1: Select Ministry
┌─────────────────────────────┐
│ Governing Ministry *        │
│ [Ministry of Education ▼]   │
└─────────────────────────────┘

Step 2: Select University (filtered by ministry)
┌─────────────────────────────┐
│ University *                │
│ [IIT Delhi ▼]              │
│ [IIT Bombay ▼]             │
│ [Delhi University ▼]        │
└─────────────────────────────┘
```

### Fix 2: Button Visibility

**InstitutionsPage:**

```javascript
// Show button based on role and active tab
const canAddInstitution = () => {
  if (activeTab === "ministry") {
    return user?.role === "developer"; // Only dev can add ministries
  }
  return ["developer", "ministry_admin"].includes(user?.role); // Both can add universities/depts
};

<Button disabled={!canAddInstitution()}>
  + Add {activeTab === "university" ? "University" : ...}
</Button>
```

### Fix 3: Backend Validation

**institution_router.py:**

```python
# Check permissions based on type
if request.type == "ministry":
    # Only developer can create ministries
    if current_user.role != "developer":
        raise HTTPException(403, "Only developers can create ministries")
elif request.type in ["university", "government_dept"]:
    # Developer or ministry admin can create
    if current_user.role not in ["developer", "ministry_admin"]:
        raise HTTPException(403, "Insufficient permissions")
```

---

## Should I Implement These Fixes?

**Fix 1:** User Registration - Two-step selection (ministry → university)
**Fix 2:** Button visibility based on role and tab
**Fix 3:** Backend permission validation

Let me know which ones to implement!
