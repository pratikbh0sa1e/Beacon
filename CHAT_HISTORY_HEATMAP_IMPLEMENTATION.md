# Chat History & Analytics Heatmap Implementation Guide

## 1. Chat History Store Created ✅

**File**: `frontend/src/stores/chatStore.js`

**Features**:

- Session management (create, load, delete, rename)
- Message persistence using Zustand persist
- Automatic session initialization
- Session title auto-generation from first message
- LocalStorage persistence across page refreshes

**Usage**:

```javascript
import { useChatStore } from "../stores/chatStore";

const {
  sessions,
  currentSessionId,
  createSession,
  loadSession,
  addMessage,
  deleteSession,
} = useChatStore();
```

## 2. AI Chat Page Updates Needed

**File**: `frontend/src/pages/AIChatPage.jsx`

**Changes Required**:

1. Import `useChatStore`
2. Add History sidebar with Sheet component
3. Add "New Chat" button
4. Replace local messages state with store
5. Add session list UI
6. Add delete session functionality

**New Components Needed**:

- Sheet (sidebar for history)
- ScrollArea (for session list)

**UI Features**:

- History button showing session count
- New Chat button
- Session list with titles and timestamps
- Delete button for each session
- Active session highlighting
- Click to load session

## 3. Analytics Heatmap Addition

**File**: `frontend/src/pages/admin/AnalyticsPage.jsx`

**Library to Install**:

```bash
npm install react-calendar-heatmap
npm install d3-scale
```

**Heatmap Features**:

- Activity heatmap showing daily actions
- Color intensity based on activity level
- Tooltip showing exact count
- Last 90 days visualization
- GitHub-style contribution graph

**Implementation**:

```javascript
import CalendarHeatmap from "react-calendar-heatmap";
import "react-calendar-heatmap/dist/styles.css";

// Process audit logs into daily counts
const heatmapData = processLogsToHeatmap(logs);

<CalendarHeatmap
  startDate={new Date(Date.now() - 90 * 24 * 60 * 60 * 1000)}
  endDate={new Date()}
  values={heatmapData}
  classForValue={(value) => {
    if (!value) return "color-empty";
    return `color-scale-${Math.min(value.count, 4)}`;
  }}
  tooltipDataAttrs={(value) => ({
    "data-tip": value.date
      ? `${value.count} actions on ${value.date}`
      : "No activity",
  })}
/>;
```

## 4. System Health Role Restriction ✅

**Already Implemented**:

- Route restricted to `["developer"]` only
- Sidebar shows only for developer role
- Backend should also enforce this

**Backend Update Needed**:
Add role check in system health endpoints to ensure only developers can access.

## 5. Implementation Steps

### Step 1: Install Dependencies

```bash
cd frontend
npm install react-calendar-heatmap d3-scale
```

### Step 2: Update AIChatPage.jsx

Replace the current implementation with the chat history version that includes:

- useChatStore integration
- History sidebar
- New chat button
- Session management

### Step 3: Add Heatmap to Analytics

Add the heatmap component to AnalyticsPage.jsx showing:

- Daily activity for last 90 days
- Color-coded intensity
- Tooltips with counts

### Step 4: Backend Chat History API (Optional)

Create endpoints to sync chat history to backend:

```python
@router.post("/chat/sessions")
async def save_session(session_data, user: User = Depends(get_current_user))

@router.get("/chat/sessions")
async def get_sessions(user: User = Depends(get_current_user))

@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str, user: User = Depends(get_current_user))
```

## 6. Chat History UI Mockup

```
┌─────────────────────────────────────────────────────┐
│ AI Assistant                    [New Chat] [History]│
├─────────────────────────────────────────────────────┤
│                                                      │
│  🤖 Hello! I'm the BEACON AI Assistant...          │
│                                                      │
│                     What is policy X?  👤           │
│                                                      │
│  🤖 Policy X is...                                  │
│     Sources: [Document 1] [Document 2]              │
│                                                      │
│  [Type your message...]                    [Send]   │
└─────────────────────────────────────────────────────┘

History Sidebar:
┌──────────────────────────┐
│ Chat History             │
├──────────────────────────┤
│ 💬 What is policy X?     │
│    5 messages • 2h ago  🗑│
├──────────────────────────┤
│ 💬 Document requirements │
│    3 messages • 1d ago  🗑│
├──────────────────────────┤
│ 💬 New Chat              │
│    1 message • 3d ago   🗑│
└──────────────────────────┘
```

## 7. Analytics Heatmap UI Mockup

```
┌─────────────────────────────────────────────────────┐
│ Activity Heatmap (Last 90 Days)                     │
├─────────────────────────────────────────────────────┤
│ Mon │ ░ ░ ▓ ░ ░ ▓ ▓ ░ ░ ░ ▓ ░ ░                    │
│ Wed │ ░ ▓ ░ ░ ▓ ░ ░ ▓ ░ ░ ░ ▓ ░                    │
│ Fri │ ▓ ░ ░ ▓ ░ ░ ▓ ░ ░ ▓ ░ ░ ▓                    │
│ Sun │ ░ ░ ▓ ░ ░ ▓ ░ ░ ▓ ░ ░ ▓ ░                    │
│                                                      │
│ ░ Less ▓▓▓▓ More                                    │
└─────────────────────────────────────────────────────┘
```

## 8. Testing Checklist

### Chat History

- [ ] Create new chat session
- [ ] Messages persist across page refresh
- [ ] Load previous session
- [ ] Delete session
- [ ] Session title auto-generates
- [ ] History sidebar opens/closes
- [ ] Session count displays correctly
- [ ] Active session highlights

### Analytics Heatmap

- [ ] Heatmap displays last 90 days
- [ ] Colors represent activity levels
- [ ] Tooltips show exact counts
- [ ] Responsive on mobile
- [ ] Data updates with time range

### System Health

- [ ] Only developer can access
- [ ] Other roles get 403 error
- [ ] Sidebar hides for non-developers

## 9. Code Snippets

### Chat Store Usage in Component

```javascript
const AIChatPage = () => {
  const {
    sessions,
    currentSessionId,
    getCurrentSession,
    createSession,
    loadSession,
    addMessage,
    deleteSession,
  } = useChatStore();

  const currentSession = getCurrentSession();
  const messages = currentSession?.messages || [];

  const handleSend = async () => {
    const userMessage = { id: Date.now(), text: input, isUser: true };
    addMessage(userMessage);

    // ... API call

    const aiMessage = { id: Date.now() + 1, text: answer, isUser: false };
    addMessage(aiMessage);
  };
};
```

### Heatmap Data Processing

```javascript
const processLogsToHeatmap = (logs) => {
  const dailyCounts = {};

  logs.forEach((log) => {
    const date = new Date(log.timestamp).toISOString().split("T")[0];
    dailyCounts[date] = (dailyCounts[date] || 0) + 1;
  });

  return Object.entries(dailyCounts).map(([date, count]) => ({
    date,
    count,
  }));
};
```

## 10. Summary

✅ **Chat Store Created** - Persistent session management
⏳ **AI Chat Page Update** - Needs integration with store
⏳ **Heatmap Addition** - Needs library installation and component
✅ **System Health Restricted** - Developer-only access
⏳ **Theme Toggle Fix** - Next priority

**Next Steps**:

1. Fix theme toggle (URGENT)
2. Install heatmap library
3. Update AIChatPage with history
4. Add heatmap to Analytics
5. Test all features
