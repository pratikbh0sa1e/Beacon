# Landing Page Authentication & Session Time Improvements

## Changes Made

### 1. Landing Page Authentication Redirect ✅

**Problem**: Authenticated users could still see the landing page with "Sign In" and "Get Started" buttons instead of being redirected to the dashboard.

**Solution**:

- Updated `LandingPage.jsx` to automatically redirect authenticated and approved users to the dashboard
- Updated `LandingHeader.jsx` to show a "Dashboard" button instead of "Sign In" and "Get Started" for logged-in users

**Files Modified**:

- `frontend/src/pages/LandingPage.jsx`
  - Added `useEffect` hook to check authentication status
  - Redirects to dashboard if user is authenticated and approved
- `frontend/src/components/landing/LandingHeader.jsx`
  - Added authentication state check
  - Conditionally renders "Dashboard" button for authenticated users
  - Shows "Sign In" and "Get Started" buttons for non-authenticated users

### 2. Session Timeout Increased ✅

**Problem**: Session timeout was set to 30 minutes, which was too short for users.

**Solution**: Increased session timeout to 24 hours to match the backend JWT token expiration.

**Files Modified**:

- `frontend/src/stores/authStore.js`
  - Changed `SESSION_TIMEOUT` from 30 minutes to 24 hours (24 _ 60 _ 60 \* 1000 ms)
  - Changed `WARNING_TIME` from 5 minutes to 10 minutes before timeout

**Configuration**:

- Frontend session timeout: **24 hours**
- Session warning: **10 minutes before expiration**
- Backend JWT token expiration: **7 days** (already configured)

## How It Works

### Landing Page Flow:

1. User visits the landing page (`/`)
2. If not authenticated → Shows landing page with "Sign In" and "Get Started" buttons
3. If authenticated and approved → Automatically redirects to dashboard
4. If authenticated but not approved → Redirects to pending approval page

### Session Management:

1. User logs in → Session timer starts (24 hours)
2. User activity resets the timer
3. 10 minutes before timeout → Warning modal appears
4. User can click "Stay Logged In" to extend session
5. After 24 hours of inactivity → Automatic logout

## Testing

### Test Landing Page Redirect:

1. Log out of the application
2. Visit the landing page - should see "Sign In" and "Get Started" buttons
3. Log in with valid credentials
4. Try to visit the landing page again - should automatically redirect to dashboard
5. Landing page header should now show "Dashboard" button instead of auth buttons

### Test Session Timeout:

1. Log in to the application
2. Session will remain active for 24 hours with activity
3. After 23 hours 50 minutes of inactivity, warning modal will appear
4. Click "Stay Logged In" to extend session
5. Or wait for automatic logout after 24 hours

## Benefits

✅ Better user experience - no confusion for logged-in users
✅ Longer session time - users don't get logged out frequently
✅ Consistent with Supabase-style authentication flow
✅ Maintains security with session warnings and automatic logout
