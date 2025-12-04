# Institution Filtering by Role - Implementation Complete ✅

## Overview

Updated registration form to show **role-appropriate institutions** in the dropdown.

---

## 🎯 Problem Solved

### Before:

- All users saw ALL institutions (universities + ministries mixed together)
- Ministry Admin could accidentally select a university
- University Admin could accidentally select a ministry
- Confusing user experience

### After:

- **Ministry Admin** → Sees only ministries (type='ministry')
- **University Admin** → Sees only universities (type='university')
- **Students/Officers** → Sees only universities (type='university')
- **Public Viewer** → No institution dropdown (not needed)

---

## 📋 Implementation Details

### 1. **Role Configuration Updated**

```javascript
const availableRoles = [
  {
    value: "student",
    label: "Student",
    needsInstitution: true,
    institutionType: "university", // ← NEW
  },
  {
    value: "document_officer",
    label: "Document Officer",
    needsInstitution: true,
    institutionType: "university", // ← NEW
  },
  {
    value: "university_admin",
    label: "University Admin",
    needsInstitution: true,
    institutionType: "university", // ← NEW
  },
  {
    value: "ministry_admin",
    label: "Ministry Admin",
    needsInstitution: true, // ← CHANGED from false
    institutionType: "ministry", // ← NEW
  },
  {
    value: "public_viewer",
    label: "Public Viewer",
    needsInstitution: false,
  },
];
```

### 2. **Institution Filtering Logic**

```javascript
// Filter institutions based on selected role
const filteredInstitutions = selectedRole?.institutionType
  ? institutions.filter((inst) => inst.type === selectedRole.institutionType)
  : institutions;
```

### 3. **Dynamic Label & Placeholder**

```javascript
// Label changes based on role
{selectedRole?.institutionType === "ministry"
  ? "Ministry"
  : "Institution"}

// Placeholder changes based on role
placeholder={
  selectedRole?.institutionType === "ministry"
    ? "Select ministry"
    : "Select institution"
}
```

### 4. **Auto-Reset on Role Change**

```javascript
const handleChange = (field, value) => {
  // If role changes, reset institution selection
  if (field === "role") {
    setFormData((prev) => ({ ...prev, [field]: value, institution_id: null }));
  } else {
    setFormData((prev) => ({ ...prev, [field]: value }));
  }
};
```

### 5. **Empty State Handling**

```javascript
{
  filteredInstitutions.length === 0 && (
    <p className="text-xs text-muted-foreground">
      No{" "}
      {selectedRole?.institutionType === "ministry"
        ? "ministries"
        : "institutions"}{" "}
      found. Please contact administrator.
    </p>
  );
}
```

---

## 🎨 User Experience Flow

### Scenario 1: Registering as Ministry Admin

```
1. User selects role: "Ministry Admin"
2. Institution dropdown appears
3. Label shows: "Ministry *"
4. Placeholder shows: "Select ministry"
5. Dropdown shows ONLY:
   - Ministry of Education
   - Ministry of Health
   - Ministry of Finance
   (No universities shown)
```

### Scenario 2: Registering as University Admin

```
1. User selects role: "University Admin"
2. Institution dropdown appears
3. Label shows: "Institution *"
4. Placeholder shows: "Select institution"
5. Dropdown shows ONLY:
   - IIT Delhi
   - Delhi University
   - MIT
   (No ministries shown)
```

### Scenario 3: Registering as Student

```
1. User selects role: "Student"
2. Institution dropdown appears
3. Label shows: "Institution *"
4. Placeholder shows: "Select institution"
5. Dropdown shows ONLY universities
```

### Scenario 4: Registering as Public Viewer

```
1. User selects role: "Public Viewer"
2. No institution dropdown (not needed)
3. Can register without selecting institution
```

### Scenario 5: Changing Role Mid-Registration

```
1. User selects "Ministry Admin"
2. Selects "Ministry of Education"
3. Changes role to "University Admin"
4. Institution selection is RESET (cleared)
5. Dropdown now shows only universities
6. User must select again
```

---

## 🔍 Validation Rules

### Ministry Admin:

- ✅ Must select a ministry
- ❌ Cannot select a university
- ✅ Institution is required

### University Admin:

- ✅ Must select a university
- ❌ Cannot select a ministry
- ✅ Institution is required

### Student/Document Officer:

- ✅ Must select a university
- ❌ Cannot select a ministry
- ✅ Institution is required

### Public Viewer:

- ✅ No institution needed
- ✅ Can register without institution

---

## 📊 Database Schema

### Institutions Table:

```sql
institutions:
- id
- name
- type: 'university' | 'ministry' | 'government_dept'
- location
```

### Example Data:

```sql
-- Ministries
INSERT INTO institutions (name, type, location) VALUES
('Ministry of Education', 'ministry', 'New Delhi'),
('Ministry of Health', 'ministry', 'New Delhi'),
('Ministry of Finance', 'ministry', 'New Delhi');

-- Universities
INSERT INTO institutions (name, type, location) VALUES
('IIT Delhi', 'university', 'Delhi'),
('Delhi University', 'university', 'Delhi'),
('MIT', 'university', 'Manipal');
```

---

## ✅ Benefits

1. **Clearer UX** - Users only see relevant options
2. **Prevents Errors** - Can't select wrong institution type
3. **Better Organization** - Separates ministries from universities
4. **Scalability** - Easy to add more institution types
5. **Validation** - Ensures data integrity

---

## 🧪 Testing Checklist

- [ ] Select "Ministry Admin" → See only ministries
- [ ] Select "University Admin" → See only universities
- [ ] Select "Student" → See only universities
- [ ] Select "Public Viewer" → No institution dropdown
- [ ] Change role → Institution selection resets
- [ ] Submit with ministry admin + ministry → Success
- [ ] Submit with university admin + university → Success
- [ ] Empty state shows when no institutions of type exist

---

## 🔄 Related Changes Needed

### Backend (Already Supports This):

- ✅ Institution type field exists
- ✅ API returns institution type
- ✅ Validation allows ministry_admin with ministry

### Frontend (Completed):

- ✅ RegisterPage filters institutions
- ⚠️ **TODO:** Update other forms if they exist:
  - User management page (admin editing users)
  - Profile page (if users can change institution)

---

## 📝 Future Enhancements

1. **Add Government Departments:**

   ```javascript
   {
     value: "govt_officer",
     label: "Government Officer",
     needsInstitution: true,
     institutionType: "government_dept"
   }
   ```

2. **Multi-Institution Support:**

   - Allow users to belong to multiple institutions
   - Useful for collaborative roles

3. **Institution Search:**

   - Add search/filter in dropdown
   - Useful when many institutions exist

4. **Institution Hierarchy:**
   - Show parent-child relationships
   - E.g., "Department of Higher Education" under "Ministry of Education"

---

## 🎯 Summary

**What Changed:**

- ❌ Before: All users saw all institutions
- ✅ After: Users see only relevant institutions based on role

**Files Modified:**

- `frontend/src/pages/auth/RegisterPage.jsx`

**Impact:**

- Better UX
- Prevents data entry errors
- Clearer separation between ministries and universities

---

**Status:** ✅ COMPLETE

**Next:** Test registration with different roles
