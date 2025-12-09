# Unicode Logging & 403 Error Fixes

## Issues Fixed

### 1. Unicode Encoding Errors in Logs
**Problem**: Windows console (cp1252) couldn't display Hindi/Unicode characters in logs
**Solution**: 
- Configured Python logging to use UTF-8 encoding
- Added Windows-specific console reconfiguration
- Added safe fallback logging for Unicode titles

### 2. 403 Forbidden Download Errors
**Problem**: Government websites blocking direct document downloads
**Solution**:
- Added retry logic with exponential backoff (3 attempts)
- Rotating user agents to avoid bot detection
- Added proper HTTP headers (Accept, Referer, Accept-Language)
- Better error messages for users

## Changes Made

### 1. `backend/main.py`
- Configured UTF-8 encoding for stdout/stderr on Windows
- Prevents UnicodeEncodeError when logging non-ASCII characters

### 2. `Agent/web_scraping/pdf_downloader.py`
- Added `retry_count` parameter (default: 3 attempts)
- Implemented exponential backoff between retries
- Added `_get_user_agent()` method with rotating user agents
- Enhanced HTTP headers to mimic real browsers
- Better error tracking across retry attempts

### 3. `backend/routers/web_scraping_router_temp.py`
- Added try-catch for Unicode logging errors
- Safe fallback to character count when Unicode fails

## How It Works

### Unicode Fix
```python
# Before: Crashes on Hindi text
logger.info(f"Stored document: हमसे संपर्क करें...")

# After: Handles gracefully
try:
    logger.info(f"Stored document: {title}...")
except UnicodeEncodeError:
    logger.info(f"Stored document: [Unicode title - {len(title)} chars]")
```

### 403 Retry Logic
```python
# Attempt 1: Chrome user agent
# Wait 1 second
# Attempt 2: Firefox user agent  
# Wait 2 seconds
# Attempt 3: Safari user agent
# If all fail: Return error with helpful message
```

## Testing

### Test Unicode Logging
1. Start backend: `python -m uvicorn backend.main:app --reload`
2. Scrape MOE website (has Hindi documents)
3. Check logs - should see either:
   - Hindi text (if console supports UTF-8)
   - "[Unicode title - X chars]" (safe fallback)
4. No more UnicodeEncodeError crashes

### Test 403 Retry
1. Try downloading a blocked document
2. System will:
   - Attempt 3 times with different user agents
   - Wait between attempts (1s, 2s)
   - Return helpful error if all fail
3. Frontend shows: "Source website blocks downloads. Open URL directly."

## Benefits

1. **No More Log Crashes**: Unicode characters handled gracefully
2. **Better Success Rate**: Retry logic increases download success
3. **User-Friendly**: Clear error messages when downloads fail
4. **Production Ready**: Handles real-world government website quirks

## Notes

- The Unicode logging errors were **harmless** - functionality worked fine
- The 403 errors are **expected** - some sites block automated downloads
- These fixes make the system more robust and user-friendly
- Retry logic respects rate limits with exponential backoff

## Future Enhancements

Consider adding:
- Proxy rotation for heavily blocked sites
- Session cookies for authenticated downloads
- Selenium/Playwright for JavaScript-heavy sites
- Rate limiting per domain
