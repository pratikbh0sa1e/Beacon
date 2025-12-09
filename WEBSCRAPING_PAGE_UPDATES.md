# Web Scraping Page Updates

## Overview

The WebScrapingPage has been updated to include new features for document limit configuration, pagination settings, and integrated scraping logs viewer.

## New Features

### 1. **View Toggle**
- Two main views: "Sources & Configuration" and "Scraping Logs"
- Easy navigation between source management and log monitoring
- Icons for better visual identification

### 2. **Document Limit Configuration**
- Default limit: **1500 documents** per scrape
- Configurable per source
- Helpful description text explaining the setting
- Can be increased for larger scrapes

### 3. **Pagination Settings**
- **Enable/Disable Pagination** checkbox
- Automatically follow pagination links when enabled
- **Max Pages** setting (default: 100)
- Conditional display - only shows max pages when pagination is enabled

### 4. **Integrated Scraping Logs**
- Real-time log viewer built into the page
- Auto-refresh every 5 seconds
- Summary statistics dashboard
- Expandable log details
- Progress tracking for running scrapes

## Updated Form Fields

### Add Source Dialog
```
- Source Name
- URL
- Description (Optional)
- Keywords (Optional) - with filtering explanation
- Max Documents per Scrape (default: 1500)
- Enable Pagination (checkbox, default: true)
- Max Pages to Scrape (default: 100, shown only if pagination enabled)
```

### Edit Source Dialog
Same fields as Add Source, pre-populated with existing values

## UI Improvements

### View Toggle Buttons
- "Sources & Configuration" - Shows source management interface
- "Scraping Logs" - Shows real-time log viewer

### Enhanced Form Descriptions
- Clear explanations for each field
- Default values displayed
- Helpful hints for configuration

### Better Visual Feedback
- Icons for each view (Settings, Activity)
- Conditional field display
- Improved spacing and layout

## Usage

### Adding a Source with Custom Limits

1. Click "Add Source"
2. Fill in source details
3. Set "Max Documents per Scrape" (e.g., 2000 for larger scrapes)
4. Enable/disable pagination as needed
5. Set "Max Pages" if pagination is enabled
6. Click "Add Source"

### Viewing Scraping Logs

1. Click "Scraping Logs" button at the top
2. View real-time progress of running scrapes
3. See summary statistics
4. Expand logs for detailed information
5. Toggle auto-refresh on/off as needed

### Editing Source Configuration

1. Click the edit (pencil) icon on any source
2. Modify document limits, pagination settings, or keywords
3. Click "Update Source"
4. Changes take effect on next scrape

## Configuration Defaults

```javascript
{
  max_documents: 1500,      // Document limit per scrape
  pagination_enabled: true,  // Auto-follow pagination
  max_pages: 100            // Maximum pages to scrape
}
```

## Benefits

1. **Flexible Scraping** - Adjust limits per source
2. **Real-time Monitoring** - See scraping progress live
3. **Better Control** - Enable/disable pagination as needed
4. **Historical View** - Review past scraping activities
5. **Performance Tuning** - Optimize limits based on source size

## Technical Details

### State Management
- `activeView`: Controls which view is displayed
- `newSource`: Form state with all configuration fields
- Proper state reset on dialog close

### Component Integration
- `ScrapingLogs` component imported and integrated
- Conditional rendering based on `activeView`
- Maintains existing functionality while adding new features

### Backward Compatibility
- Existing sources work with default values
- Graceful handling of missing fields
- No breaking changes to API

## Next Steps

1. Test the updated UI with different configurations
2. Verify pagination settings work correctly
3. Monitor scraping logs for real-time updates
4. Adjust default limits based on usage patterns
