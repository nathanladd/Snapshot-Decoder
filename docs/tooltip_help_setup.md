# Tooltip Help System Setup Guide

This guide explains how to register new custom tooltip help messages and link them to local and remote web pages in the Snapshot Decoder application.

## Overview

The application uses a custom tooltip system that provides:
- **Rich tooltips** with descriptive text
- **Clickable "more..." links** that open detailed help pages
- **Embedded help browser** for displaying local HTML files and remote URLs
- **Auto-registration** system for widgets

## Architecture

### Core Components

1. **`HelpEventFilter`** (`ui_pyside6/widgets/help_tooltip.py`)
   - Intercepts tooltip events on registered widgets
   - Shows custom tooltips with clickable links
   - Manages widget registry

2. **`HelpBrowserDock`** (`ui_pyside6/widgets/help_browser_dock.py`)
   - Embedded web browser for displaying help content
   - Handles local HTML files and remote URLs
   - Provides navigation controls (back, forward, home)

3. **Help Files Directory** (`data/help/`)
   - Contains local HTML help files
   - Supports CSS styling via `styles.css`
   - Organized by feature/topic

## Registering New Help Tooltips

### Step 1: Create Help Content

#### Option A: Local HTML File
Create an HTML file in `data/help/`:

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
    <title>My Feature Help</title>
</head>
<body>
    <h1>My Feature</h1>
    <p>Detailed description of how to use this feature...</p>
    
    <h2>Usage Steps</h2>
    <ol>
        <li>Step one description</li>
        <li>Step two description</li>
    </ol>
    
    <h2>Tips</h2>
    <ul>
        <li>Helpful tip 1</li>
        <li>Helpful tip 2</li>
    </ul>
</body>
</html>
```

#### Option B: Remote URL
Use an existing web page or create one on your website/documentation server.

### Step 2: Register the Widget

In `MainWindow._setup_help_tooltips()` method (`ui_pyside6/main_window.py`):

```python
def _setup_help_tooltips(self):
    """Register help tooltips on widgets throughout the UI."""
    self._help_filter = HelpEventFilter(self)
    self._help_filter.link_clicked.connect(self.help_browser_dock.navigate)
    
    # Register your new widget
    self._help_filter.register(
        self.my_widget,                    # Widget instance
        "Brief description of the widget", # Tooltip text
        "my_feature.html"                  # Help file or URL
    )
```

### Step 3: Access the Widget

Ensure the widget is accessible as `self.my_widget` in the MainWindow class. If it's nested inside another widget, use the full path:

```python
self._help_filter.register(
    self.settings_panel.my_button,
    "Button description",
    "button_help.html"
)
```

## Registration API Reference

### HelpEventFilter.register()

```python
def register(self, widget: QWidget, tooltip_text: str, help_url: str):
    """
    Register a widget to show a custom help tooltip on hover.
    
    Args:
        widget: The widget to attach help to
        tooltip_text: Descriptive tooltip text (shown in tooltip)
        help_url: Help page filename (e.g. 'quick_charts.html') or full URL
    """
```

### HelpBrowserDock.navigate()

```python
def navigate(self, url_or_filename: str):
    """
    Navigate to a help page.
    
    Args:
        url_or_filename: Either a full URL (http/https), a local file path,
                         or just a filename like 'quick_charts.html' which
                         is resolved relative to data/help/.
    """
```

## URL Resolution

The help system supports multiple URL formats:

### Local Files
- **Filename only**: `"my_feature.html"` → `data/help/my_feature.html`
- **Absolute path**: `"C:/path/to/help.html"` → Direct file access
- **Relative path**: `"../docs/help.html"` → Relative to application

### Remote URLs
- **HTTP**: `"http://example.com/help.html"`
- **HTTPS**: `"https://docs.example.com/feature.html"`

## Best Practices

### Tooltip Text
- Keep it concise (1-2 sentences)
- Focus on the widget's primary purpose
- Use action-oriented language
- Example: `"Search and select PIDs for custom charts"`

### Help Content
- Use consistent styling via `styles.css`
- Include navigation links to related topics
- Add screenshots/diagrams where helpful
- Structure with clear headings (`<h1>`, `<h2>`, etc.)

### File Organization
- Use descriptive, lowercase filenames
- Use underscores instead of spaces: `feature_name.html`
- Group related features together

## Examples

### Example 1: Simple Button
```python
# In MainWindow._setup_help_tooltips()
self._help_filter.register(
    self.export_button,
    "Export current chart data to CSV file",
    "export_data.html"
)
```

### Example 2: Complex Panel
```python
# In MainWindow._setup_help_tooltips()
self._help_filter.register(
    self.advanced_settings_panel,
    "Configure advanced analysis parameters and thresholds",
    "advanced_settings.html"
)
```

### Example 3: Remote Documentation
```python
# In MainWindow._setup_help_tooltips()
self._help_filter.register(
    self.documentation_link,
    "View complete API documentation online",
    "https://api.example.com/docs"
)
```

## Styling Help Content

### CSS Structure
All help files should link to the main stylesheet:

```html
<link rel="stylesheet" href="styles.css">
```

### Custom Styling
Add feature-specific styles in your HTML file:

```html
<style>
.feature-highlight {
    background-color: #f0f8ff;
    border-left: 4px solid #0078d4;
    padding: 10px;
    margin: 10px 0;
}
</style>
```

## Testing Your Help System

### Verification Steps
1. **Hover Test**: Hover over your widget to see the tooltip
2. **Link Test**: Click "more..." to verify help page opens
3. **Navigation Test**: Use back/forward buttons in help browser
4. **Content Test**: Verify help content displays correctly

### Debugging
- Check console for missing file errors
- Verify widget instance is accessible
- Ensure help file exists in `data/help/`
- Test URLs in browser first

## Maintenance

### Updating Help Content
- Edit HTML files directly in `data/help/`
- Changes take effect immediately (no rebuild needed)
- Test after each update

### Adding New Features
1. Create help content first
2. Register widget in `_setup_help_tooltips()`
3. Test the complete flow

### Removing Features
1. Remove registration call from `_setup_help_tooltips()`
2. Optionally delete help files if no longer needed

## Troubleshooting

### Common Issues

**Tooltip doesn't appear:**
- Verify widget is registered correctly
- Check widget instance is accessible
- Ensure `HelpEventFilter` is initialized

**"more..." link doesn't work:**
- Verify help file exists
- Check URL format
- Test help browser separately

**Help page doesn't load:**
- Check file path resolution
- Verify HTML syntax
- Test file in external browser

**Styling issues:**
- Ensure CSS link is correct
- Check for CSS conflicts
- Validate HTML structure

### Getting Help
- Check existing implementations in `MainWindow._setup_help_tooltips()`
- Review help files in `data/help/` for examples
- Test with simple content first, then add complexity
