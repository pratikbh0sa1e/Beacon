# Institution Deletion Strategy

## 🎯 Who Can Delete What?

### Deletion Permissions:

| Role                 | Can Delete Ministries? | Can Delete Institutions?           |
| -------------------- | ---------------------- | ---------------------------------- |
| **Developer**        | ✅ Yes                 | ✅ Yes                             |
| **Ministry Admin**   | ❌ No                  | ✅ Yes (only under their ministry) |
| **University Admin** | ❌ No                  | ❌ No                              |
| **Others**           | ❌ No                  | ❌ No                              |

---

## 🔄 Deletion Flow

### Option 1: Soft Delete (Recommended) ⭐

**Keep data but mark as deleted**

**Pros:**

- ✅ Can restore if mistake
- ✅ Maintains audit trail
- ✅ Preserves historical data
- ✅ Users can be reassigned later

**Cons:**

- ❌ Takes up database space
- ❌ Need to filter deleted items in queries

### Option 2: Hard Delete with User Migration

**Delete institution but migrate users**

**Pros:**

- ✅ Clean database
- ✅ Users are preserved
- ✅ Clear data removal

**Cons:**

- ❌ Cannot restore
- ❌ Loses historical data
- ❌ Complex migration logic

---

## 📋 Recommended Approach: Soft Delete + User Migration

### Step 1: Add `deleted_at` Column to Institutions

```sql
ALTER TABLE institutions
ADD COLUMN deleted_at TIMESTAMP NULL,
ADD COLUMN deleted_by INTEGER REFERENCES users(id);

CREATE INDEX idx_institutions_deleted_at ON institutions(deleted_at);
```

### Step 2: Deletion Process

#### When Deleting an Institution:

```
1. Check if institution has users
2. If yes, show warning with user count
3. Admin chooses action:
   a) Convert users to public_viewer + set institution_id = NULL
   b) Transfer users to another institution
   c) Cancel deletion
4. Mark institution as deleted (soft delete)
5. Log action in audit_logs
```

#### When Deleting a Ministry:

```
1. Check if ministry has child institutions
2. If yes, BLOCK deletion (must delete/transfer children first)
3. Check if ministry has users (ministry admins)
4. If yes, show warning
5. Admin chooses action for users:
   a) Convert to public_viewer + set institution_id = NULL
   b) Transfer to another ministry
   c) Cancel deletion
6. Mark ministry as deleted (soft delete)
7. Log action in audit_logs
```

---

## 🔧 Implementation

### Database Migration:

```python
"""add soft delete to institutions

Revision ID: add_soft_delete_001
Revises: merge_govt_dept_001
Create Date: 2024-12-04 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add soft delete columns
    op.add_column('institutions',
        sa.Column('deleted_at', sa.DateTime(), nullable=True)
    )
    op.add_column('institutions',
        sa.Column('deleted_by', sa.Integer(), nullable=True)
    )

    # Add foreign key
    op.create_foreign_key(
        'fk_institutions_deleted_by',
        'institutions', 'users',
        ['deleted_by'], ['id'],
        ondelete='SET NULL'
    )

    # Add index
    op.create_index(
        'idx_institutions_deleted_at',
        'institutions',
        ['deleted_at']
    )

def downgrade():
    op.drop_index('idx_institutions_deleted_at', 'institutions')
    op.drop_constraint('fk_institutions_deleted_by', 'institutions')
    op.drop_column('institutions', 'deleted_by')
    op.drop_column('institutions', 'deleted_at')
```

---

## 💻 Backend Implementation

### Delete Institution Endpoint:

```python
class DeleteInstitutionRequest(BaseModel):
    user_action: str  # "convert_to_public" or "transfer"
    target_institution_id: Optional[int] = None  # For transfer option

@router.delete("/{institution_id}")
async def delete_institution(
    institution_id: int,
    request: DeleteInstitutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete an institution

    - Only developers can delete ministries
    - Developers and ministry admins can delete institutions
    - Must handle users before deletion
    """
    # Get institution
    institution = db.query(Institution).filter(
        Institution.id == institution_id,
        Institution.deleted_at == None
    ).first()

    if not institution:
        raise HTTPException(404, "Institution not found")

    # Check permissions
    if institution.type == "ministry":
        # Only developer can delete ministries
        if current_user.role != "developer":
            raise HTTPException(403, "Only developers can delete ministries")

        # Check for child institutions
        child_count = db.query(Institution).filter(
            Institution.parent_ministry_id == institution_id,
            Institution.deleted_at == None
        ).count()

        if child_count > 0:
            raise HTTPException(
                400,
                f"Cannot delete ministry with {child_count} active institutions. "
                "Delete or transfer child institutions first."
            )

    elif institution.type == "university":
        # Developer or ministry admin can delete
        if current_user.role == "ministry_admin":
            # Must be under their ministry
            if institution.parent_ministry_id != current_user.institution_id:
                raise HTTPException(403, "Can only delete institutions under your ministry")
        elif current_user.role != "developer":
            raise HTTPException(403, "Insufficient permissions")

    # Get users in this institution
    users = db.query(User).filter(User.institution_id == institution_id).all()

    if users:
        if request.user_action == "convert_to_public":
            # Convert users to public_viewer
            for user in users:
                user.role = "public_viewer"
                user.institution_id = None
                user.approved = False  # Require re-approval

        elif request.user_action == "transfer":
            if not request.target_institution_id:
                raise HTTPException(400, "Target institution required for transfer")

            # Verify target institution exists
            target = db.query(Institution).filter(
                Institution.id == request.target_institution_id,
                Institution.deleted_at == None
            ).first()

            if not target:
                raise HTTPException(404, "Target institution not found")

            # Transfer users
            for user in users:
                user.institution_id = request.target_institution_id
                user.approved = False  # Require re-approval at new institution

        else:
            raise HTTPException(400, "Invalid user_action. Must be 'convert_to_public' or 'transfer'")

    # Soft delete institution
    institution.deleted_at = datetime.utcnow()
    institution.deleted_by = current_user.id

    db.commit()

    # Log action
    log = AuditLog(
        user_id=current_user.id,
        action="delete_institution",
        details={
            "institution_id": institution_id,
            "institution_name": institution.name,
            "institution_type": institution.type,
            "user_count": len(users),
            "user_action": request.user_action
        }
    )
    db.add(log)
    db.commit()

    return {
        "status": "success",
        "message": f"Institution '{institution.name}' deleted successfully",
        "users_affected": len(users),
        "user_action": request.user_action
    }
```

---

## 🎨 Frontend Implementation

### Delete Confirmation Dialog:

```jsx
const DeleteInstitutionDialog = ({ institution, onConfirm, onCancel }) => {
  const [userAction, setUserAction] = useState("convert_to_public");
  const [targetInstitution, setTargetInstitution] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setLoading(true);
    try {
      await institutionAPI.delete(institution.id, {
        user_action: userAction,
        target_institution_id: targetInstitution,
      });

      toast.success(`${institution.name} deleted successfully`);
      onConfirm();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open onOpenChange={onCancel}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete {institution.name}?</DialogTitle>
          <DialogDescription>
            This institution has {institution.user_count} users. What should
            happen to them?
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Option 1: Convert to Public Viewer */}
          <div className="flex items-start space-x-3">
            <input
              type="radio"
              id="convert"
              checked={userAction === "convert_to_public"}
              onChange={() => setUserAction("convert_to_public")}
            />
            <label htmlFor="convert" className="flex-1">
              <p className="font-medium">Convert to Public Viewers</p>
              <p className="text-sm text-muted-foreground">
                Users will become public viewers with no institution. They will
                need to re-register or be reassigned.
              </p>
            </label>
          </div>

          {/* Option 2: Transfer to Another Institution */}
          <div className="flex items-start space-x-3">
            <input
              type="radio"
              id="transfer"
              checked={userAction === "transfer"}
              onChange={() => setUserAction("transfer")}
            />
            <label htmlFor="transfer" className="flex-1">
              <p className="font-medium">Transfer to Another Institution</p>
              <p className="text-sm text-muted-foreground">
                Move all users to another institution.
              </p>

              {userAction === "transfer" && (
                <Select
                  value={targetInstitution}
                  onValueChange={setTargetInstitution}
                  className="mt-2"
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select target institution" />
                  </SelectTrigger>
                  <SelectContent>
                    {/* List of available institutions */}
                  </SelectContent>
                </Select>
              )}
            </label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={
              loading || (userAction === "transfer" && !targetInstitution)
            }
          >
            {loading ? "Deleting..." : "Delete Institution"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

---

## 🚫 Ministry Deletion Restrictions

### Cannot Delete Ministry If:

1. **Has Active Child Institutions**

   ```
   ❌ Cannot delete Ministry of Education
   Reason: Has 3 active institutions (IIT Delhi, IIT Mumbai, Delhi University)
   Action: Delete or transfer child institutions first
   ```

2. **Has Ministry Admins**
   ```
   ⚠️  Warning: Ministry has 2 ministry admins
   Options:
   - Convert to public viewers
   - Transfer to another ministry
   - Cancel deletion
   ```

---

## 📊 User Migration Examples

### Example 1: Delete IIT Delhi (Convert Users)

**Before:**

```
IIT Delhi (50 users)
├── 1 University Admin
├── 5 Document Officers
└── 44 Students
```

**After Deletion (Convert to Public):**

```
IIT Delhi (DELETED)

Users converted:
├── 1 Public Viewer (was University Admin)
├── 5 Public Viewers (were Document Officers)
└── 44 Public Viewers (were Students)

All users:
- institution_id = NULL
- role = "public_viewer"
- approved = false (need re-approval)
```

---

### Example 2: Delete IIT Delhi (Transfer Users)

**Before:**

```
IIT Delhi (50 users)
├── 1 University Admin
├── 5 Document Officers
└── 44 Students
```

**After Deletion (Transfer to IIT Mumbai):**

```
IIT Delhi (DELETED)

IIT Mumbai (now 120 users)
├── 2 University Admins (1 original + 1 transferred)
├── 12 Document Officers (7 original + 5 transferred)
└── 106 Students (62 original + 44 transferred)

All transferred users:
- institution_id = IIT Mumbai ID
- role = unchanged
- approved = false (need re-approval at new institution)
```

---

## 🔍 Filtering Deleted Institutions

### Update All Queries:

```python
# Always filter out deleted institutions
query = db.query(Institution).filter(Institution.deleted_at == None)
```

### List Endpoint:

```python
@router.get("/list")
async def list_institutions(...):
    query = db.query(Institution).filter(Institution.deleted_at == None)
    # ... rest of filtering
```

### Registration Endpoint:

```python
@router.get("/public")
async def list_institutions_public(...):
    query = db.query(Institution).filter(Institution.deleted_at == None)
    # ... rest of logic
```

---

## 🎯 Ministry Tab Visibility

### Update InstitutionsPage.jsx:

```jsx
// Show tabs based on role
const showMinistryTab = ["developer"].includes(user?.role);

return (
  <Tabs>
    <TabsList
      className={`grid w-full max-w-md ${
        showMinistryTab ? "grid-cols-2" : "grid-cols-1"
      }`}
    >
      <TabsTrigger value="university">
        <School className="h-4 w-4" />
        Institutions ({counts.university})
      </TabsTrigger>

      {showMinistryTab && (
        <TabsTrigger value="ministry">
          <Landmark className="h-4 w-4" />
          Ministries ({counts.ministry})
        </TabsTrigger>
      )}
    </TabsList>

    {/* Rest of component */}
  </Tabs>
);
```

---

## ✅ Summary

### Deletion Permissions:

- ✅ **Developer:** Can delete ministries and institutions
- ✅ **Ministry Admin:** Can delete institutions under their ministry only
- ❌ **Others:** Cannot delete anything

### User Handling:

- ✅ **Option 1:** Convert to public_viewer + set institution_id = NULL
- ✅ **Option 2:** Transfer to another institution
- ✅ All affected users require re-approval

### Ministry Deletion:

- ❌ Cannot delete if has active child institutions
- ⚠️ Must handle ministry admin users first

### Ministry Tab:

- ✅ **Developer:** Can see Ministries tab
- ❌ **Ministry Admin:** Cannot see Ministries tab (only 1 tab: Institutions)
- ❌ **Others:** Cannot see admin page

### Soft Delete:

- ✅ Institutions marked as deleted (not removed)
- ✅ Can be restored if needed
- ✅ Maintains audit trail
- ✅ Filtered from all queries

---

**Next Steps:**

1. Add `deleted_at` and `deleted_by` columns to institutions table
2. Implement delete endpoint with user migration
3. Update all queries to filter deleted institutions
4. Hide Ministries tab for ministry admins
5. Add delete button with confirmation dialog
