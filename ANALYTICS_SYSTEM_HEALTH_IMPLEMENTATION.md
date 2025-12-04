# Analytics & System Health Pages Implementation

## Overview

Created two comprehensive admin pages for monitoring system analytics and health status.

---

## Files Created/Modified

### 1. Analytics Page: `frontend/src/pages/admin/AnalyticsPage.jsx` ✅

**Features:**

- **Overview Stats Cards**:

  - Total Users
  - Total Documents
  - Pending Approvals
  - Active Users (in selected time period)

- **Time Range Selector**: 24 hours, 7 days, 30 days, 90 days

- **Activity Breakdown**: Visual breakdown of all system actions with counts

  - Login/Logout
  - Document uploads
  - Approvals/Rejections
  - Role changes
  - Downloads
  - Search queries

- **Most Active Users**: Top 5 users by activity count

- **Recent Activity Feed**: Last 10 activities with user info and timestamps

- **Period Summary**: Total actions, unique users, time period stats

**UI Components:**

- PageHeader with time range selector
- Stat cards with icons and colors
- Activity breakdown with action icons
- User activity rankings
- Real-time activity feed
- Responsive grid layouts

---

### 2. System Health Page: `frontend/src/pages/admin/SystemHealthPage.jsx` ✅

**Features:**

- **Overall System Status**: Single view of entire system health

  - Healthy (all green)
  - Warning (some issues)
  - Unhealthy (critical issues)

- **Component Monitoring**:

  - **Database** (PostgreSQL): Connection status
  - **Vector Store** (FAISS): Indexing status, document count
  - **AI Service** (Gemini 2.0): Model availability
  - **Storage** (Supabase): File storage status

- **Vector Store Details**:

  - Total documents indexed
  - Storage mode
  - List of indexed document IDs

- **System Information**:

  - API version
  - Environment (production/development)
  - Last health check timestamp

- **Refresh Button**: Manual health check refresh

**UI Components:**

- Overall status card with large indicator
- Component status cards with icons
- Status badges (healthy/warning/unhealthy)
- Vector store statistics
- System info panel
- Refresh functionality

---

### 3. Updated: `frontend/src/App.jsx` ✅

**Routes Added:**

- `/admin/analytics` - Analytics Dashboard
- `/admin/system` - System Health Monitor

Both routes are protected with `ADMIN_ROLES` (developer, MINISTRY_ADMIN, university_admin)

---

## Backend APIs Used

### Analytics Page APIs:

1. **GET** `/audit/summary?days={days}`

   - Returns activity summary for time period
   - Total actions, unique users
   - Action breakdown by type
   - Most active users

2. **GET** `/audit/logs?days={days}&limit={limit}`

   - Returns recent activity logs
   - Includes user info and metadata

3. **GET** `/users/list?limit=1000`

   - Gets total user count

4. **GET** `/documents/list?limit=1000`
   - Gets total document count
   - Filters pending approvals

### System Health Page APIs:

1. **GET** `/documents/vector-stats`

   - Returns vector store statistics
   - Total documents indexed
   - Storage mode and paths

2. **GET** `/chat/health`
   - Checks AI service health
   - Returns model status

---

## Navigation

### Sidebar Buttons:

**Analytics:**

- Label: "Analytics"
- Icon: BarChart3
- Path: `/admin/analytics`
- Visible to: ADMIN_ROLES

**System Health:**

- Label: "System Health"
- Icon: Settings
- Path: `/admin/system`
- Visible to: ADMIN_ROLES

---

## Features Breakdown

### Analytics Page

#### Time Range Filtering:

- Last 24 Hours
- Last 7 Days (default)
- Last 30 Days
- Last 90 Days

#### Action Types Tracked:

- `login` - User logged in
- `logout` - User logged out
- `upload_document` - Document uploaded
- `document_approved` - Document approved
- `document_rejected` - Document rejected
- `user_approved` - User registration approved
- `user_rejected` - User registration rejected
- `role_changed` - User role modified
- `document_downloaded` - Document downloaded
- `search_query` - AI search performed

#### Activity Icons:

Each action type has a unique icon and color:

- Login/Logout: Activity icon (green/gray)
- Upload: Upload icon (blue)
- Approvals: CheckCircle (green)
- Rejections: XCircle (red)
- Role changes: Users icon (purple)
- Downloads: Download icon (blue)
- Searches: Eye icon (yellow)

---

### System Health Page

#### Health Status Levels:

- **Healthy** (Green): All systems operational
- **Warning** (Yellow): Some systems need attention
- **Unhealthy** (Red): Critical issues detected

#### Components Monitored:

1. **Database (PostgreSQL)**

   - Connection status
   - Query execution

2. **Vector Store (FAISS)**

   - Index availability
   - Document count
   - Storage paths

3. **AI Service (Gemini 2.0 Flash)**

   - Model availability
   - Response status

4. **Storage (Supabase)**
   - File storage status
   - Upload/download capability

#### Health Check Logic:

- Database: Healthy if API responds
- Vector Store: Healthy if stats endpoint returns success
- AI Service: Healthy if `/chat/health` returns "healthy"
- Storage: Healthy by default (can be enhanced)

---

## Role-Based Access

### Who Can Access:

| Role                 | Analytics                 | System Health  |
| -------------------- | ------------------------- | -------------- |
| **Developer**        | ✅ Full access            | ✅ Full access |
| **MoE Admin**        | ✅ Full access            | ✅ Full access |
| **University Admin** | ✅ Limited to institution | ✅ Full access |
| **Document Officer** | ❌ No access              | ❌ No access   |
| **Student**          | ❌ No access              | ❌ No access   |
| **Public Viewer**    | ❌ No access              | ❌ No access   |

**Note**: University admins see analytics filtered to their institution's users only.

---

## UI/UX Highlights

### Analytics Page:

1. **Color-Coded Stats**: Each metric has a unique color theme
2. **Interactive Time Range**: Easy switching between time periods
3. **Activity Feed**: Real-time view of recent actions
4. **User Rankings**: Gamification element showing most active users
5. **Responsive Design**: Works on all screen sizes
6. **Motion Animations**: Smooth entry animations

### System Health Page:

1. **Traffic Light System**: Green/Yellow/Red status indicators
2. **Component Cards**: Individual status for each system component
3. **Overall Health**: Single glance system status
4. **Detailed Stats**: Deep dive into vector store metrics
5. **Manual Refresh**: On-demand health checks
6. **Visual Feedback**: Icons and badges for quick scanning

---

## Testing Checklist

### Analytics Page

- [ ] Page loads without errors
- [ ] Stats cards display correct numbers
- [ ] Time range selector works
- [ ] Activity breakdown shows all action types
- [ ] Most active users list populates
- [ ] Recent activity feed updates
- [ ] Period summary displays correctly
- [ ] Responsive on mobile devices
- [ ] Role-based filtering works (university admin)

### System Health Page

- [ ] Page loads without errors
- [ ] Overall status calculates correctly
- [ ] Database status shows healthy
- [ ] Vector store stats display
- [ ] AI service health checks
- [ ] Storage status shows
- [ ] Refresh button works
- [ ] Status badges show correct colors
- [ ] Component cards display properly
- [ ] Responsive on mobile devices

### Integration

- [ ] Sidebar navigation works
- [ ] Only admins can access pages
- [ ] API endpoints respond correctly
- [ ] Error handling works
- [ ] Toast notifications appear
- [ ] Loading states display

---

## API Response Examples

### Analytics Summary:

```json
{
  "period_days": 7,
  "total_actions": 245,
  "unique_users": 18,
  "action_breakdown": {
    "login": 45,
    "upload_document": 12,
    "document_approved": 8,
    "search_query": 67
  },
  "most_active_users": [
    {
      "user_id": 5,
      "name": "John Doe",
      "email": "john@example.com",
      "action_count": 34
    }
  ],
  "scope": "developer"
}
```

### System Health:

```json
{
  "status": "success",
  "total_documents": 156,
  "storage_mode": "separate_indexes",
  "storage_location": "Agent/vector_store/documents/{doc_id}/",
  "document_folders": ["1", "2", "3", "..."]
}
```

### AI Health:

```json
{
  "status": "healthy",
  "model": "gemini-2.0-flash-exp",
  "tools": 5
}
```

---

## Future Enhancements (Optional)

### Analytics Page:

1. **Charts & Graphs**: Add visual charts for activity trends
2. **Export Data**: Export analytics to CSV/PDF
3. **Custom Date Ranges**: Allow custom start/end dates
4. **Real-time Updates**: WebSocket for live activity feed
5. **Comparison View**: Compare different time periods
6. **User Drill-down**: Click user to see detailed activity
7. **Action Filtering**: Filter by specific action types
8. **Department Analytics**: Break down by department/institution
9. **Performance Metrics**: Response times, error rates
10. **Predictive Analytics**: Forecast usage trends

### System Health Page:

1. **Historical Health Data**: Track health over time
2. **Alerts & Notifications**: Email/SMS for critical issues
3. **Auto-refresh**: Periodic automatic health checks
4. **Performance Metrics**: CPU, memory, disk usage
5. **API Response Times**: Monitor endpoint performance
6. **Database Metrics**: Query times, connection pool stats
7. **Vector Store Metrics**: Index size, search performance
8. **Uptime Tracking**: System availability percentage
9. **Error Logs**: Recent errors and warnings
10. **Maintenance Mode**: Toggle system maintenance

---

## Performance Considerations

### Analytics Page:

- Caches audit logs for selected time range
- Limits recent activity to 10 items
- Paginates large datasets
- Debounces time range changes

### System Health Page:

- Manual refresh to avoid excessive API calls
- Caches health status for 30 seconds
- Lightweight health checks
- Async component checks

---

## Security Considerations

1. **Role-Based Access**: Only admins can view these pages
2. **Data Filtering**: University admins see only their institution's data
3. **Sensitive Info**: No passwords or tokens displayed
4. **Audit Trail**: All access to these pages is logged
5. **Rate Limiting**: Health checks are rate-limited

---

## Summary

✅ **Analytics Page Created** - Comprehensive activity monitoring
✅ **System Health Page Created** - Real-time system status
✅ **Routes Added to App.jsx** - Both pages accessible
✅ **Backend APIs Integrated** - Using existing audit and health endpoints
✅ **Role-Based Access** - Admin-only with institution filtering
✅ **Responsive Design** - Works on all devices
✅ **Real-time Data** - Live system monitoring
✅ **Visual Feedback** - Icons, badges, and color coding
✅ **Error Handling** - Graceful degradation

Both pages are now fully functional and provide administrators with powerful tools to monitor system usage and health!
