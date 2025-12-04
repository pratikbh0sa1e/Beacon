# Simplified Institution Deletion Flow

## 🎯 Recommended Approach: Convert to Public Viewer Only

### Why Remove Transfer Option?

**Problems with Transfer:**

- ❌ Target institution has no control
- ❌ Could overwhelm target institution
- ❌ Requires complex approval workflow
- ❌ What if target admin never responds?
- ❌ Users have no choice in where they go

**Benefits of Convert Only:**

- ✅ Simple and clean
- ✅ Users choose their new institution
- ✅ Target institutions approve individually
- ✅ No complex approval system needed
- ✅ Users have agency in the process

---

## 📋 Simplified Deletion Process

### Step 1: Admin Initiates Deletion

**UI:**

```
┌─────────────────────────────────────────────┐
│ Delete IIT Delhi?                           │
├─────────────────────────────────────────────┤
│                                             │
│ ⚠️  This institution has 50 users:          │
│   • 1 University Admin                      │
│   • 5 Document Officers                     │
│   • 44 Students                             │
│                                             │
│ What will happen to these users?            │
│                                             │
│ All users will be converted to Public       │
│ Viewers and can re-register at any         │
│ institution of their choice.                │
│                                             │
│ They will receive an email notification     │
│ with instructions on how to re-register.    │
│                                             │
│ [Cancel] [Delete Institution]               │
└─────────────────────────────────────────────┘
```

---

### Step 2: System Actions

**Automatic Actions:**

```python
1. Mark institution as deleted (soft delete)
2. For each user in institution:
   a. role = "public_viewer"
   b. institution_id = NULL
   c. approved = False
   d. Send email notification
3. Log action in audit_logs
4. Return success message
```

---

### Step 3: Email Notification to Users

**Email Template:**

```
Subject: Important: IIT Delhi Institution Closure

Dear [User Name],

We regret to inform you that IIT Delhi has been removed from the
BEACON system.

Your account has been converted to a Public Viewer account. To
continue accessing the system with full privileges, please:

1. Visit: https://beacon.gov.in/register
2. Select your new institution
3. Complete the registration process
4. Wait for approval from your new institution admin

Your previous data and bookmarks have been preserved.

If you have any questions, please contact support.

Best regards,
BEACON System
```

---

### Step 4: User Re-registration

**User Flow:**

```
1. User receives email
2. User goes to registration page
3. User selects new institution:
   - Ministry: Ministry of Education
   - Institution: IIT Mumbai
4. User completes registration
5. IIT Mumbai admin reviews and approves
6. User regains full access
```

---

## 💻 Implementation

### Backend Endpoint:

```python
class DeleteInstitutionRequest(BaseModel):
    confirm: bool  # Must be True to proceed

@router.delete("/{institution_id}")
async def delete_institution(
    institution_id: int,
    request: DeleteInstitutionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete an institution and convert users to public viewers

    - Only developers can delete ministries
    - Developers and ministry admins can delete institutions
    """
    if not request.confirm:
        raise HTTPException(400, "Confirmation required")

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
                "Delete child institutions first."
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

    # Convert all users to public viewers
    for user in users:
        user.role = "public_viewer"
        user.institution_id = None
        user.approved = False  # Require re-approval

        # Send email notification
        send_institution_closure_email(user, institution)

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
            "users_affected": len(users),
            "action": "converted_to_public_viewer"
        }
    )
    db.add(log)
    db.commit()

    return {
        "status": "success",
        "message": f"Institution '{institution.name}' deleted successfully",
        "users_affected": len(users),
        "action": "All users converted to public viewers and notified"
    }


def send_institution_closure_email(user: User, institution: Institution):
    """Send email notification to user about institution closure"""
    # TODO: Implement email sending
    # Use your email service (SendGrid, AWS SES, etc.)
    pass
```

---

### Frontend Dialog:

```jsx
const DeleteInstitutionDialog = ({ institution, onConfirm, onCancel }) => {
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setLoading(true);
    try {
      await institutionAPI.delete(institution.id, { confirm: true });

      toast.success(
        `${institution.name} deleted. ${institution.user_count} users notified.`
      );
      onConfirm();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to delete");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open onOpenChange={onCancel}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            Delete {institution.name}?
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* User Count Warning */}
          {institution.user_count > 0 && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>
                This institution has {institution.user_count} users
              </AlertTitle>
              <AlertDescription>
                All users will be converted to Public Viewers and notified via
                email.
              </AlertDescription>
            </Alert>
          )}

          {/* What Will Happen */}
          <div className="space-y-2">
            <p className="font-medium">What will happen:</p>
            <ul className="list-disc list-inside space-y-1 text-sm text-muted-foreground">
              <li>Institution will be marked as deleted</li>
              <li>All users converted to Public Viewers</li>
              <li>Users can re-register at any institution</li>
              <li>Email notifications sent to all users</li>
              <li>Data and bookmarks preserved</li>
            </ul>
          </div>

          {/* Confirmation */}
          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Users will receive instructions on how to re-register at a new
              institution.
            </AlertDescription>
          </Alert>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Deleting...
              </>
            ) : (
              <>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete Institution
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
```

---

## 🎯 User Journey After Deletion

### Example: IIT Delhi Student

**Before Deletion:**

```json
{
  "name": "John Doe",
  "email": "john@iitdelhi.ac.in",
  "role": "student",
  "institution_id": 5, // IIT Delhi
  "approved": true
}
```

**After Deletion:**

```json
{
  "name": "John Doe",
  "email": "john@iitdelhi.ac.in",
  "role": "public_viewer",
  "institution_id": null,
  "approved": false
}
```

**User Actions:**

1. Receives email notification
2. Goes to registration page
3. Selects new institution (e.g., IIT Mumbai)
4. Completes registration
5. Waits for IIT Mumbai admin approval
6. Regains full access

---

## 📊 Comparison: Before vs After

### Before (Complex Transfer):

```
Delete Institution
  ↓
Choose Action:
  • Convert to Public Viewer
  • Transfer to Another Institution ← Complex!
    ↓
  Select Target Institution
    ↓
  Send Approval Request
    ↓
  Wait for Target Admin Response
    ↓
  If Approved: Transfer Users
  If Rejected: What now?
```

### After (Simple Convert):

```
Delete Institution
  ↓
Convert All Users to Public Viewer
  ↓
Send Email Notifications
  ↓
Users Re-register at Institution of Choice
  ↓
New Institution Admin Approves
  ↓
Done!
```

---

## ✅ Benefits of Simplified Approach

### For System:

- ✅ **Simpler Code:** No complex approval workflow
- ✅ **Fewer Edge Cases:** No pending transfers, no rejections
- ✅ **Easier to Maintain:** Less code, less bugs
- ✅ **Better Performance:** No waiting for approvals

### For Users:

- ✅ **User Choice:** Pick their preferred institution
- ✅ **Clear Process:** Simple re-registration
- ✅ **No Surprises:** Know exactly what's happening
- ✅ **Data Preserved:** Bookmarks and history maintained

### For Target Institutions:

- ✅ **Control:** Approve users individually
- ✅ **Review:** Can properly vet each user
- ✅ **No Overwhelm:** Users trickle in over time
- ✅ **Preparation:** Can prepare for new users

### For Admins:

- ✅ **Fast:** Immediate action, no waiting
- ✅ **Clear:** Simple one-step process
- ✅ **Traceable:** Clear audit trail
- ✅ **Reversible:** Can restore institution if needed

---

## 🚫 Ministry Deletion

**Same simplified approach:**

```
1. Check for child institutions
2. If exists: Block deletion
3. If no children: Convert ministry admins to public viewers
4. Send notifications
5. Mark ministry as deleted
```

---

## ✅ Summary

**Recommendation:** Remove transfer option, keep only "Convert to Public Viewer"

**Why:**

- Simpler implementation
- Better user experience
- Better for target institutions
- No complex approval workflow
- Users have choice
- Natural re-registration process

**Implementation:**

- Single confirmation dialog
- Automatic conversion to public_viewer
- Email notifications
- Users re-register at institution of choice
- New institution approves individually

**Result:**

- Clean, simple, maintainable
- Better UX for everyone
- No complex edge cases
- Easy to understand and use

---

**Next Steps:**

1. Implement delete endpoint (convert only)
2. Add delete button in UI
3. Create confirmation dialog
4. Set up email notifications
5. Test deletion flow
