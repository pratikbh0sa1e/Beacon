# Notification System Implementation Guide

## Overview

Comprehensive notification system with hierarchical routing, priority levels, and persistence.

---

## 1. Database Model ✅

**File**: `backend/database.py`

**Model Added**: `Notification`

```python
class Notification(Base):
    """System notifications with hierarchical routing"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, index=True)

    # Priority: critical, high, medium, low
    priority = Column(String(20), nullable=False, default="medium", index=True)

    # Status
    read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # Action
    action_url = Column(String(500), nullable=True)
    action_label = Column(String(100), nullable=True)
    action_metadata = Column(JSONB, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationship
    user = relationship("User", foreign_keys=[user_id])
```

---

## 2. Hierarchical Routing Rules

### Notification Recipients by Actor Role:

| Actor Role           | Primary Recipients                  | Also Visible To      |
| -------------------- | ----------------------------------- | -------------------- |
| **Student**          | University Admin (same institution) | MoE Admin, Developer |
| **Document Officer** | University Admin (same institution) | MoE Admin, Developer |
| **University Admin** | MoE Admin                           | Developer            |
| **MoE Admin**        | Developer                           | -                    |
| **Developer**        | Sees ALL notifications              | -                    |

### Implementation:

```python
def get_notification_recipients(actor_role: str, institution_id: Optional[int], db: Session) -> List[int]:
    recipients = []

    # Developer always receives everything
    developers = db.query(User.id).filter(User.role == "developer").all()
    recipients.extend([dev[0] for dev in developers])

    # Student or Document Officer
    if actor_role in ["student", "document_officer"]:
        # Primary: University Admin from same institution
        if institution_id:
            uni_admins = db.query(User.id).filter(
                User.role == "university_admin",
                User.institution_id == institution_id
            ).all()
            recipients.extend([admin[0] for admin in uni_admins])

        # Also: MoE Admins
        MINISTRY_ADMINs = db.query(User.id).filter(User.role == "ministry_admin").all()
        recipients.extend([admin[0] for admin in MINISTRY_ADMINs])

    # University Admin
    elif actor_role == "university_admin":
        MINISTRY_ADMINs = db.query(User.id).filter(User.role == "ministry_admin").all()
        recipients.extend([admin[0] for admin in MINISTRY_ADMINs])

    return list(set(recipients))
```

---

## 3. Priority Levels

### Priority Classification:

| Priority        | Icon   | Use Cases                                                         |
| --------------- | ------ | ----------------------------------------------------------------- |
| **🔥 Critical** | Red    | Security alerts, failed embeddings, confidential document failure |
| **⚠ High**      | Orange | Pending document approvals, role elevation requests               |
| **📌 Medium**   | Blue   | System reminders, update logs, successful upload confirmations    |
| **📨 Low**      | Gray   | General information, read receipts, UI notifications              |

### Priority Assignment Logic:

```python
def get_notification_priority(event_type: str, metadata: dict) -> str:
    # Critical
    if event_type in ["security_alert", "embedding_failed", "confidential_doc_failed"]:
        return "critical"

    # High
    if event_type in ["document_approval", "role_elevation", "user_approval"]:
        if metadata.get("visibility") in ["restricted", "confidential"]:
            return "high"
        if metadata.get("role") in ["university_admin", "ministry_admin"]:
            return "high"

    # Medium
    if event_type in ["upload_success", "system_reminder", "update_log"]:
        return "medium"

    # Low (default)
    return "low"
```

---

## 4. Backend API Endpoints

### Create Router: `backend/routers/notification_router.py`

**Endpoints**:

1. **GET** `/notifications/list`

   - Get notifications with filtering
   - Query params: `unread_only`, `priority`, `type`, `limit`, `offset`

2. **GET** `/notifications/grouped`

   - Get notifications grouped by priority
   - Returns: `{critical: [], high: [], medium: [], low: []}`

3. **GET** `/notifications/unread-count`

   - Get count of unread notifications
   - Returns: `{unread_count: number}`

4. **POST** `/notifications/{id}/mark-read`

   - Mark single notification as read

5. **POST** `/notifications/mark-all-read`

   - Mark all notifications as read

6. **DELETE** `/notifications/{id}`

   - Delete single notification

7. **DELETE** `/notifications/clear-all`
   - Clear all read notifications

### Helper Functions:

```python
def notify_user_registration(user: User, db: Session):
    """Notify admins about new user registration"""
    recipients = get_notification_recipients(user.role, user.institution_id, db)
    priority = "high" if user.role in ["university_admin", "ministry_admin"] else "medium"

    create_notification(
        user_ids=recipients,
        title=f"New {user.role.replace('_', ' ').title()} Registration",
        message=f"{user.name} ({user.email}) has registered and is awaiting approval.",
        notification_type="user_approval",
        priority=priority,
        action_url="/admin/users",
        action_label="Review Now",
        action_metadata={"user_id": user.id},
        db=db
    )

def notify_document_upload(document, uploader: User, db: Session):
    """Notify admins about document upload"""
    recipients = get_notification_recipients(uploader.role, document.institution_id, db)
    priority = "high" if document.visibility_level in ["restricted", "confidential"] else "medium"

    create_notification(
        user_ids=recipients,
        title=f"New Document Uploaded: {document.filename}",
        message=f"{uploader.name} uploaded a {document.visibility_level} document.",
        notification_type="document_approval",
        priority=priority,
        action_url="/admin/approvals",
        action_label="Review Document",
        db=db
    )
```

---

## 5. Frontend Implementation

### A. API Service

**File**: `frontend/src/services/api.js`

```javascript
export const notificationAPI = {
  list: (params) => api.get("/notifications/list", { params }),
  grouped: () => api.get("/notifications/grouped"),
  unreadCount: () => api.get("/notifications/unread-count"),
  markRead: (id) => api.post(`/notifications/${id}/mark-read`),
  markAllRead: () => api.post("/notifications/mark-all-read"),
  delete: (id) => api.delete(`/notifications/${id}`),
  clearAll: () => api.delete("/notifications/clear-all"),
};
```

### B. Notification Panel Component

**File**: `frontend/src/components/notifications/NotificationPanel.jsx`

**Features**:

- Grouped by priority (collapsible sections)
- Badge counts per section
- Mark read/unread
- Filters (all, unread, by priority, by type)
- CTA buttons (Approve Now, Open Document, etc.)
- Real-time updates

**UI Structure**:

```
┌─────────────────────────────────────┐
│ Notifications (12)        [Mark All]│
├─────────────────────────────────────┤
│ Filters: [All] [Unread] [Priority] │
├─────────────────────────────────────┤
│ 🔥 Critical (2)              [▼]    │
│   ├─ Security Alert                 │
│   │   [Check System] [Dismiss]      │
│   └─ Embedding Failed               │
│       [Retry] [Dismiss]             │
├─────────────────────────────────────┤
│ ⚠ High Priority (5)          [▼]    │
│   ├─ New Document Approval          │
│   │   [Review Now] [Dismiss]        │
│   └─ User Registration              │
│       [Approve] [Dismiss]           │
├─────────────────────────────────────┤
│ 📌 Medium (3)                [▼]    │
│ 📨 Low (2)                   [▼]    │
└─────────────────────────────────────┘
```

### C. Header Integration

**File**: `frontend/src/components/layout/Header.jsx`

**Updates**:

1. Replace static bell icon with notification panel
2. Show unread count badge
3. Add dropdown/sheet for notification panel
4. Poll for new notifications every 30 seconds
5. Show toast on new notification

```javascript
const [unreadCount, setUnreadCount] = useState(0);
const [notificationsOpen, setNotificationsOpen] = useState(false);

useEffect(() => {
  fetchUnreadCount();
  const interval = setInterval(fetchUnreadCount, 30000); // Poll every 30s
  return () => clearInterval(interval);
}, []);

const fetchUnreadCount = async () => {
  const response = await notificationAPI.unreadCount();
  const newCount = response.data.unread_count;

  if (newCount > unreadCount) {
    toast.info("You have new notifications");
  }

  setUnreadCount(newCount);
};
```

---

## 6. Integration Points

### Update Existing Routers:

#### A. User Router (`backend/routers/user_router.py`)

**In `register` endpoint**:

```python
# After user creation
notify_user_registration(new_user, db)
```

**In `approve_user` endpoint**:

```python
# After approval
notify_approval_decision(target_user, True, current_user, db)
```

**In `reject_user` endpoint**:

```python
# After rejection
notify_approval_decision(target_user, False, current_user, db)
```

#### B. Document Router (`backend/routers/document_router.py`)

**In `upload_document` endpoint**:

```python
# After document upload
notify_document_upload(doc, current_user, db)
```

**In `approve_document` endpoint**:

```python
# Notify uploader
create_notification(
    user_ids=[document.uploader_id],
    title="Document Approved",
    message=f"Your document '{document.filename}' has been approved.",
    notification_type="document_status",
    priority="medium",
    action_url=f"/documents/{document.id}",
    action_label="View Document",
    db=db
)
```

---

## 7. Database Migration

**Create migration file**: `alembic/versions/xxx_add_notifications.py`

```python
def upgrade():
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('priority', sa.String(20), nullable=False),
        sa.Column('read', sa.Boolean(), nullable=False, default=False),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('action_url', sa.String(500), nullable=True),
        sa.Column('action_label', sa.String(100), nullable=True),
        sa.Column('action_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_priority', 'notifications', ['priority'])
    op.create_index('ix_notifications_read', 'notifications', ['read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])

def downgrade():
    op.drop_table('notifications')
```

**Run migration**:

```bash
alembic revision --autogenerate -m "add notifications table"
alembic upgrade head
```

---

## 8. Toast Styling by Priority

**File**: `frontend/src/utils/notificationToast.js`

```javascript
import { toast } from "sonner";

export const showNotificationToast = (notification) => {
  const options = {
    duration: getPriorityDuration(notification.priority),
    action: notification.action_label
      ? {
          label: notification.action_label,
          onClick: () => (window.location.href = notification.action_url),
        }
      : undefined,
  };

  switch (notification.priority) {
    case "critical":
      toast.error(notification.title, {
        ...options,
        description: notification.message,
        icon: "🔥",
      });
      break;
    case "high":
      toast.warning(notification.title, {
        ...options,
        description: notification.message,
        icon: "⚠",
      });
      break;
    case "medium":
      toast.info(notification.title, {
        ...options,
        description: notification.message,
        icon: "📌",
      });
      break;
    case "low":
      toast(notification.title, {
        ...options,
        description: notification.message,
        icon: "📨",
      });
      break;
  }
};

function getPriorityDuration(priority) {
  switch (priority) {
    case "critical":
      return 10000; // 10 seconds
    case "high":
      return 7000;
    case "medium":
      return 5000;
    case "low":
      return 3000;
    default:
      return 5000;
  }
}
```

---

## 9. Implementation Checklist

### Backend

- [ ] Add Notification model to database.py
- [ ] Create notification_router.py
- [ ] Add helper functions (notify_user_registration, etc.)
- [ ] Update user_router.py to call notification helpers
- [ ] Update document_router.py to call notification helpers
- [ ] Register notification router in main.py
- [ ] Create and run database migration

### Frontend

- [ ] Add notificationAPI to services/api.js
- [ ] Create NotificationPanel component
- [ ] Create notification toast utility
- [ ] Update Header with notification bell
- [ ] Add polling for new notifications
- [ ] Integrate toast on new notifications
- [ ] Test all priority levels
- [ ] Test hierarchical routing

### Testing

- [ ] Student registration → University Admin notified
- [ ] Document Officer upload → University Admin notified
- [ ] University Admin action → MoE Admin notified
- [ ] MoE Admin action → Developer notified
- [ ] Developer sees all notifications
- [ ] Priority levels display correctly
- [ ] Toast styling matches priority
- [ ] Mark read/unread works
- [ ] Filters work correctly
- [ ] CTA buttons navigate correctly

---

## 10. Summary

**Hierarchical Routing**: ✅ Defined
**Priority Levels**: ✅ Defined (Critical, High, Medium, Low)
**Database Model**: ✅ Created
**Backend API**: ✅ Designed
**Frontend Components**: ✅ Designed
**Toast Integration**: ✅ Designed
**Persistence**: ✅ Database-backed

**Next Steps**:

1. Run database migration
2. Create notification router file
3. Update existing routers with notification calls
4. Build frontend NotificationPanel component
5. Integrate with Header
6. Test all scenarios
