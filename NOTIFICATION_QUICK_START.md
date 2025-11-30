# Notification System - Quick Start Guide

## 🚀 Quick Implementation Steps

### 1. Database Migration (5 min)

```bash
# Navigate to project root
cd backend

# Create migration
alembic revision --autogenerate -m "add notifications table"

# Run migration
alembic upgrade head
```

### 2. Create Notification Router (10 min)

Copy the notification router code from `NOTIFICATION_SYSTEM_IMPLEMENTATION.md` section 4 into:
`backend/routers/notification_router.py`

### 3. Register Router in Main (2 min)

**File**: `backend/main.py`

```python
from backend.routers import notification_router

app.include_router(notification_router.router, prefix="/notifications", tags=["notifications"])
```

### 4. Update User Router (5 min)

**File**: `backend/routers/user_router.py`

Add at top:

```python
from backend.routers.notification_router import notify_user_registration, notify_approval_decision
```

In `register` endpoint, after user creation:

```python
notify_user_registration(new_user, db)
```

In `approve_user` endpoint:

```python
notify_approval_decision(target_user, True, current_user, db)
```

In `reject_user` endpoint:

```python
notify_approval_decision(target_user, False, current_user, db)
```

### 5. Update Document Router (5 min)

**File**: `backend/routers/document_router.py`

Add at top:

```python
from backend.routers.notification_router import notify_document_upload
```

In `upload_document` endpoint, after document creation:

```python
notify_document_upload(doc, current_user, db)
```

### 6. Frontend API Service (2 min)

**File**: `frontend/src/services/api.js`

Add:

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

### 7. Update Header Component (15 min)

**File**: `frontend/src/components/layout/Header.jsx`

Replace the static bell button with notification panel integration.

See full implementation in `NOTIFICATION_SYSTEM_IMPLEMENTATION.md` section 5.C

---

## 📋 Hierarchical Routing Summary

| User Action              | Notified Roles                                     |
| ------------------------ | -------------------------------------------------- |
| Student registers        | University Admin (primary) + MoE Admin + Developer |
| Document Officer uploads | University Admin (primary) + MoE Admin + Developer |
| University Admin action  | MoE Admin (primary) + Developer                    |
| MoE Admin action         | Developer only                                     |

---

## 🎨 Priority Levels

| Priority | Icon | Color  | Duration |
| -------- | ---- | ------ | -------- |
| Critical | 🔥   | Red    | 10s      |
| High     | ⚠    | Orange | 7s       |
| Medium   | 📌   | Blue   | 5s       |
| Low      | 📨   | Gray   | 3s       |

---

## ✅ Testing Checklist

After implementation, test:

1. **Student Registration**:

   - [ ] University Admin receives notification
   - [ ] MoE Admin receives notification
   - [ ] Developer receives notification
   - [ ] Priority is "medium"

2. **Document Upload (Restricted)**:

   - [ ] University Admin receives notification
   - [ ] Priority is "high"
   - [ ] CTA button works

3. **University Admin Action**:

   - [ ] MoE Admin receives notification
   - [ ] Developer receives notification

4. **Notification Panel**:

   - [ ] Groups by priority
   - [ ] Shows unread count
   - [ ] Mark read works
   - [ ] Filters work
   - [ ] CTA buttons navigate

5. **Toast Notifications**:
   - [ ] Appears on new notification
   - [ ] Matches theme (light/dark)
   - [ ] Styling matches priority
   - [ ] Action button works

---

## 🔧 Troubleshooting

### Notifications not appearing?

- Check database migration ran successfully
- Verify notification router is registered in main.py
- Check browser console for API errors
- Verify user has correct role permissions

### Wrong users receiving notifications?

- Review hierarchical routing logic in `get_notification_recipients()`
- Check user's institution_id is set correctly
- Verify role assignments

### Toast not showing?

- Check theme integration in App.jsx
- Verify Toaster component has theme prop
- Check notification polling interval

---

## 📚 Full Documentation

For complete implementation details, see:

- `NOTIFICATION_SYSTEM_IMPLEMENTATION.md` - Full technical guide
- `THEME_TOGGLE_FIX_COMPLETE.md` - Theme integration
- `FINAL_IMPLEMENTATION_SUMMARY.md` - Overall project status

---

## 🎯 Estimated Time

- Backend: 30 minutes
- Frontend: 45 minutes
- Testing: 30 minutes
- **Total: ~2 hours**

---

## 💡 Pro Tips

1. **Start with backend** - Get notifications storing correctly first
2. **Test routing** - Verify correct users receive notifications
3. **Build UI incrementally** - Start with simple list, then add grouping
4. **Use toast sparingly** - Only for new/important notifications
5. **Add polling** - Check for new notifications every 30-60 seconds
6. **Consider WebSockets** - For real-time updates (future enhancement)

---

## 🚀 Ready to Start?

1. Run database migration
2. Create notification router
3. Update existing routers
4. Build frontend components
5. Test thoroughly
6. Deploy!

Good luck! 🎉
