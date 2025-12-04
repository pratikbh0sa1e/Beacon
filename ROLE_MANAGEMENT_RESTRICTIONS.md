# Role Management Restrictions - Implementation Summary

## Overview

Implemented proper role-based restrictions for user management to ensure admins can only manage users within their authority.

---

## Changes Made

### 1. **New Constants** (`frontend/src/constants/roles.js`)

Added `MANAGEABLE_ROLES` constant:

```javascript
export const MANAGEABLE_ROLES = [
  ROLES.MINISTRY_ADMIN,
  ROLES.UNIVERSITY_ADMIN,
  ROLES.DOCUMENT_OFFICER,
  ROLES.STUDENT,
  ROLES.PUBLIC_VIEWER,
];
```

- Excludes "developer" from role management
- Used for role selection dropdowns

### 2. **User Management Page** (`frontend/src/pages/admin/UserManagementPage.jsx`)

#### Added Helper Functions:

**`getAssignableRoles(targetUser)`**:

- **Developer**: Can assign any manageable role
- **Ministry Admin**: Can assign any manageable role
- **University Admin**: Can only assign Document Officer and Student (same institution only)

**`canChangeRole(targetUser)`**:

- Checks if current user can change a specific user's role
- Developer role is always protected
- University Admin can only change roles for users in same institution

**`canManageUser(targetUser)`**:

- Checks if current user can perform actions (approve/reject/delete) on target user
- Developer accounts are protected
- Ministry Admin cannot manage other Ministry Admins or Developers
- University Admin can only manage Document Officers and Students in same institution

#### UI Changes:

**Role Column**:

- Developer role shows as "Developer (Protected)" badge (not editable)
- Users that can be managed show dropdown with appropriate roles
- Users that cannot be managed show role as read-only badge

**Actions Column**:

- Developer accounts show "Protected" badge
- Users outside management scope show "No Access" badge
- Only manageable users show approve/reject/delete actions

---

## Permission Matrix

### Developer

| Can Manage        | Roles                                                                      |
| ----------------- | -------------------------------------------------------------------------- |
| ✅ Change Role    | Ministry Admin, University Admin, Document Officer, Student, Public Viewer |
| ✅ Approve/Reject | All except Developer                                                       |
| ✅ Delete         | All except Developer                                                       |

### Ministry Admin

| Can Manage        | Roles                                                      |
| ----------------- | ---------------------------------------------------------- |
| ✅ Change Role    | University Admin, Document Officer, Student, Public Viewer |
| ✅ Approve/Reject | University Admin, Document Officer, Student, Public Viewer |
| ✅ Delete         | University Admin, Document Officer, Student, Public Viewer |
| ❌ Cannot Manage  | Developer, other Ministry Admins                           |

### University Admin

| Can Manage        | Roles (Same Institution Only)                                              |
| ----------------- | -------------------------------------------------------------------------- |
| ✅ Change Role    | Document Officer, Student                                                  |
| ✅ Approve/Reject | Document Officer, Student                                                  |
| ✅ Delete         | Document Officer, Student                                                  |
| ❌ Cannot Manage  | Developer, Ministry Admin, University Admin, users from other institutions |

---

## Business Rules Enforced

### 1. **Developer Protection**

- Developer role cannot be changed
- Developer accounts cannot be deleted
- Developer accounts cannot have approval revoked
- **Developer accounts are hidden from non-developers** (security measure)
- Only 1 Developer account system-wide

### 2. **Ministry Admin Restrictions**

- Cannot manage other Ministry Admins
- **Cannot promote users to Ministry Admin role** (cannot assign their own level)
- Cannot manage Developer
- Can manage all University Admins and below
- Maximum 5 active Ministry Admins

### 3. **University Admin Restrictions**

- Can only manage users in their own institution
- Can only assign Document Officer and Student roles
- Cannot manage University Admins (even in same institution)
- Cannot manage Ministry Admins or Developer
- 1 University Admin per institution

### 4. **Role Assignment Rules**

- Developer can assign any manageable role
- Ministry Admin can assign any manageable role
- University Admin can only assign Document Officer and Student
- Role dropdown only shows roles that can be assigned

### 5. **Institution Boundaries**

- University Admins cannot see/manage users from other institutions
- Ministry Admins can manage users across all institutions
- Developer can manage all users

---

## UI Indicators

### Role Column

- **"Developer (Protected)"** - Developer account (not editable)
- **Dropdown** - User can be managed, shows assignable roles
- **Badge (read-only)** - User cannot be managed by current admin

### Actions Column

- **"Protected"** - Developer account
- **"No Access"** - User outside management scope
- **Approve/Reject buttons** - For pending users that can be managed
- **Actions menu** - For approved users that can be managed

---

## Testing Scenarios

### As Developer:

- ✅ Can change any user's role (except developer)
- ✅ Can approve/reject/delete any user (except developer)
- ✅ Sees all users in the list

### As Ministry Admin:

- ✅ Can change University Admin, Document Officer, Student roles
- ✅ Can approve/reject/delete University Admins and below
- ❌ **Cannot promote users to Ministry Admin role**
- ❌ Cannot change other Ministry Admin roles
- ❌ Cannot delete Developer or other Ministry Admins
- ❌ **Cannot see Developer accounts** (hidden for security)
- ✅ Sees all other users in the list

### As University Admin:

- ✅ Can change Document Officer and Student roles (same institution)
- ✅ Can approve/reject/delete Document Officers and Students (same institution)
- ❌ Cannot change University Admin roles
- ❌ Cannot manage users from other institutions
- ❌ Cannot manage Ministry Admins or Developer
- ❌ **Cannot see Developer accounts** (hidden for security)
- ✅ Sees all other users but can only manage some

---

## Backend Validation

**Note**: Frontend restrictions are in place, but backend should also validate:

- Role change permissions in `/users/change-role/{user_id}`
- User approval permissions in `/users/approve/{user_id}`
- User deletion permissions in `/users/delete/{user_id}`

Backend already has some validation, but should be reviewed to match frontend rules.

---

## Summary

**What Changed**:

1. ✅ Developer role is fully protected
2. ✅ Ministry Admins cannot manage each other
3. ✅ University Admins can only manage Document Officers and Students in their institution
4. ✅ Role dropdowns show only assignable roles
5. ✅ Action buttons only appear for manageable users
6. ✅ Clear UI indicators for protected/inaccessible users

**Result**: Proper hierarchical role management with institution boundaries enforced! 🎯
