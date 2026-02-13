# Quick Chart Help Registration Guide

This guide provides specific instructions for registering help tooltips on existing quick chart buttons and adding help for new charts and features.

## Current Quick Chart System

### Architecture Overview
- **QuickChartPanel** (`ui_pyside6/widgets/quick_chart_panel.py`) - Creates buttons dynamically based on snapshot type
- **BUTTONS_BY_TYPE** (`domain/constants.py`) - Defines button configurations for each snapshot type
- **Help Registration** (`ui_pyside6/main_window.py`) - Currently registers the entire panel, not individual buttons

### Current Registration
The system currently registers the entire quick chart panel as one widget:

```python
self._help_filter.register(
    self.quick_chart_panel,
    "One-click diagnostic charts for common analyses",
    "quick_charts.html"
)
```

## Registering Help on Individual Quick Chart Buttons

### Option 1: Modify QuickChartPanel to Expose Buttons (Recommended)

#### Step 1: Update QuickChartPanel to Store Button References

In `ui_pyside6/widgets/quick_chart_panel.py`, modify the `_clear_buttons` method to preserve button references:

```python
def __init__(self, parent=None):
    super().__init__(parent)
    self._buttons: List[QPushButton] = []
    self._button_registry: dict[str, QPushButton] = {}  # Add this line
    self._reference_button: Optional[QToolButton] = None
    self._current_snapshot_type: Optional[SnapType] = None
    self._setup_ui()

def set_snapshot_type(self, snapshot_type: Optional[SnapType]):
    """Update buttons based on snapshot type."""
    self._clear_buttons()
    self._current_snapshot_type = snapshot_type
    
    if snapshot_type is None or snapshot_type == SnapType.EMPTY:
        self._show_placeholder()
        return
    
    # Add reference button if available for this snapshot type
    self._add_reference_button_if_available(snapshot_type)
    
    # Get buttons for this snapshot type
    buttons_config = BUTTONS_BY_TYPE.get(snapshot_type, [])
    
    if not buttons_config:
        placeholder = QPushButton("No quick charts for this type")
        placeholder.setEnabled(False)
        self._button_layout.addWidget(placeholder)
        self._buttons.append(placeholder)
        return
    
    # Create compact buttons in 2-row grid
    col_offset = 1 if self._reference_button else 0
    num_buttons = len(buttons_config)
    num_cols = (num_buttons + 1) // 2
    
    for i, (name, action_id, tooltip) in enumerate(buttons_config):
        btn = QPushButton(name)
        btn.setToolTip(tooltip)
        btn.setProperty("action_id", action_id)
        btn.clicked.connect(self._on_button_clicked)
        btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        btn.setMaximumWidth(120)
        
        # Store button reference for help registration
        self._button_registry[action_id] = btn
        
        row = i % 2
        col = col_offset + (i // 2)
        self._button_layout.addWidget(btn, row, col)
        self._buttons.append(btn)

def get_button_by_action_id(self, action_id: str) -> Optional[QPushButton]:
    """Get button reference by action ID for help registration."""
    return self._button_registry.get(action_id)
```

#### Step 2: Update MainWindow to Register Individual Buttons

In `ui_pyside6/main_window.py`, modify `_setup_help_tooltips()`:

```python
def _setup_help_tooltips(self):
    """Register help tooltips on widgets throughout the UI."""
    self._help_filter = HelpEventFilter(self)
    self._help_filter.link_clicked.connect(self.help_browser_dock.navigate)
    
    # Register individual quick chart buttons
    self._register_quick_chart_help()
    
    # Other widget registrations...
    self._help_filter.register(
        self.header_panel,
        "Snapshot header info — file name, type, hours",
        "snapshot_header.html"
    )
    # ... rest of existing registrations

def _register_quick_chart_help(self):
    """Register help tooltips for individual quick chart buttons."""
    # Define help mappings for each action ID
    quick_chart_help = {
        # ECU V1 Charts
        "V1_BATTERY_TEST": ("Battery Test", "battery_voltage.html"),
        "V1_RAIL_PRESSURE": ("Rail Pressure Analysis", "rail_pressure.html"),
        "V1_RAIL_GAP": ("Rail Pressure Gap", "rail_pressure.html#gap-analysis"),
        "V1_IMV_CURRENT": ("IMV Current Control", "chart_controls.html#imv"),
        "V1_TURBO": ("Turbocharger Performance", "turbo.html"),
        "V1_EGR_FLOW": ("EGR Flow Analysis", "chart_controls.html#egr"),
        "V1_EGR_POSITION": ("EGR Position Control", "chart_controls.html#egr"),
        "V1_PISTON_DELTA": ("Piston Delta Analysis", "chart_controls.html#piston"),
        "V1_CAM_CRANK": ("Cam/Crank Synchronization", "chart_controls.html#timing"),
        "V1_START_AID": ("Start Aid System", "chart_controls.html#starting"),
        "V1_AIR_FUEL_RATIO": ("Air/Fuel Ratio Control", "chart_controls.html#fuel"),
        "V1_TORQUE_CONTROL": ("Torque Control System", "chart_controls.html#torque"),
        "V1_FUEL_COOLANT_TEMP": ("Temperature Analysis", "fuel_coolant_temp.html"),
        
        # ECU V2 Charts
        "V2_BATTERY_TEST": ("Battery Test", "battery_voltage.html"),
        "V2_RAIL_PRESSURE": ("Rail Pressure Analysis", "rail_pressure.html"),
        "V2_RAIL_GAP": ("Rail Pressure Gap", "rail_pressure.html#gap-analysis"),
        "V2_IMV_CURRENT": ("IMV Current Control", "chart_controls.html#imv"),
        "V2_TURBO": ("Turbocharger Performance", "turbo.html"),
        "V2_MISFIRE": ("Misfire Detection", "chart_controls.html#misfire"),
        "V2_THROTTLE_VALVE": ("Throttle Valve Control", "chart_controls.html#throttle"),
        "V2_ENGINE_LOAD": ("Engine Load Analysis", "chart_controls.html#load"),
        "V2_ENGINE_TORQUE_LIMITS": ("Torque Limits", "chart_controls.html#torque"),
        "V2_FUEL_COOLANT_TEMP": ("Temperature Analysis", "fuel_coolant_temp.html"),
        
        # EUD V1 Charts
        "V1EUD_SPEED_V_LOAD": ("Speed vs Load Analysis", "eud_speed_load.html"),
        "V1EUD_SPEED_BAND": ("Speed Band Analysis", "eud_speed_band.html"),
        "V1EUD_ELEVATION": ("Elevation Analysis", "eud_elevation.html"),
        "V1EUD_EGT": ("Exhaust Gas Temperature", "eud_egt.html"),
    }
    
    # Register help for each action ID
    for action_id, (tooltip_text, help_url) in quick_chart_help.items():
        button = self.quick_chart_panel.get_button_by_action_id(action_id)
        if button:
            self._help_filter.register(button, tooltip_text, help_url)
```

### Option 2: Event-Based Registration (Alternative)

If you prefer not to modify QuickChartPanel, use event filtering:

```python
def _setup_help_tooltips(self):
    """Register help tooltips on widgets throughout the UI."""
    self._help_filter = HelpEventFilter(self)
    self._help_filter.link_clicked.connect(self.help_browser_dock.navigate)
    
    # Install event filter on quick chart panel to catch button creation
    self.quick_chart_panel.installEventFilter(self)
    # ... rest of registrations

def eventFilter(self, obj, event):
    """Catch button creation events in quick chart panel."""
    if obj == self.quick_chart_panel and event.type() == QEvent.Type.ChildAdded:
        child = event.child()
        if isinstance(child, QPushButton) and child.property("action_id"):
            action_id = child.property("action_id")
            self._register_button_help(child, action_id)
    return super().eventFilter(obj, event)

def _register_button_help(self, button, action_id):
    """Register help for a specific button based on action ID."""
    help_mappings = {
        "V1_BATTERY_TEST": ("Battery Test", "battery_voltage.html"),
        # ... same mappings as Option 1
    }
    
    if action_id in help_mappings:
        tooltip_text, help_url = help_mappings[action_id]
        self._help_filter.register(button, tooltip_text, help_url)
```

## Adding Help for New Charts and Features

### Step 1: Define New Chart Configuration

In `domain/constants.py`, add your new chart to `BUTTONS_BY_TYPE`:

```python
SnapType.ECU_V2: [
    # ... existing buttons ...
    ("New Feature", "V2_NEW_FEATURE", 
    "Description of the new feature chart"),
],
```

### Step 2: Create Help Content

Create HTML file in `data/help/`:

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
    <title>New Feature Help</title>
</head>
<body>
    <h1>New Feature Analysis</h1>
    
    <h2>Overview</h2>
    <p>This chart displays...</p>
    
    <h2>How to Interpret</h2>
    <ul>
        <li>What the X-axis represents</li>
        <li>What the Y-axis represents</li>
        <li>What patterns to look for</li>
    </ul>
    
    <h2>Common Issues</h2>
    <div class="issue-box">
        <h3>Issue 1: Symptom</h3>
        <p>What to look for and what it means...</p>
    </div>
    
    <h2>Related Charts</h2>
    <p>See also: <a href="related_chart.html">Related Analysis</a></p>
</body>
</html>
```

### Step 3: Register Help for New Chart

Add the new chart to the help mappings in `MainWindow._register_quick_chart_help()`:

```python
quick_chart_help = {
    # ... existing mappings ...
    "V2_NEW_FEATURE": ("New Feature Analysis", "new_feature.html"),
}
```

## Help Content Templates

### Standard Chart Help Template

```html
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="styles.css">
    <title>[Chart Name] Help</title>
</head>
<body>
    <div class="help-header">
        <h1>[Chart Name]</h1>
        <p class="subtitle">[Brief description]</p>
    </div>
    
    <section class="overview">
        <h2>Overview</h2>
        <p>[What this chart shows and why it's important]</p>
    </section>
    
    <section class="interpretation">
        <h2>How to Interpret</h2>
        <ul>
            <li><strong>X-axis:</strong> [X-axis description]</li>
            <li><strong>Y-axis:</strong> [Y-axis description]</li>
            <li><strong>Normal pattern:</strong> [What to expect normally]</li>
            <li><strong>Problem indicators:</strong> [What indicates issues]</li>
        </ul>
    </section>
    
    <section class="troubleshooting">
        <h2>Common Issues</h2>
        <div class="issue">
            <h3>[Issue Name]</h3>
            <p><strong>Symptom:</strong> [What you see]</p>
            <p><strong>Cause:</strong> [Why it happens]</p>
            <p><strong>Solution:</strong> [How to fix]</p>
        </div>
    </section>
    
    <section class="related">
        <h2>Related Analysis</h2>
        <ul>
            <li><a href="related_chart1.html">Related Chart 1</a></li>
            <li><a href="related_chart2.html">Related Chart 2</a></li>
        </ul>
    </section>
</body>
</html>
```

### CSS Additions (add to styles.css)

```css
.issue {
    background-color: #fff8dc;
    border-left: 4px solid #ffa500;
    padding: 12px;
    margin: 10px 0;
    border-radius: 4px;
}

.issue h3 {
    color: #ff6600;
    margin-top: 0;
}

.help-header {
    border-bottom: 2px solid #0078d4;
    padding-bottom: 10px;
    margin-bottom: 20px;
}

.subtitle {
    color: #666;
    font-style: italic;
}
```

## Testing Your Help Registration

### Verification Steps

1. **Load a snapshot** of the appropriate type
2. **Hover over each button** to verify tooltips appear
3. **Click "more..."** on each tooltip to verify help pages load
4. **Test navigation** between related help pages
5. **Check new charts** after adding them to ensure help appears

### Debugging Help Registration

If help doesn't appear for a button:

1. **Check button creation**: Verify the button is being created with the correct action_id
2. **Check registration timing**: Ensure help registration happens after buttons are created
3. **Verify action ID**: Confirm the action_id matches your help mapping exactly
4. **Check help file**: Verify the HTML file exists and is accessible

```python
# Debug code to check button registration
def debug_quick_chart_buttons(self):
    """Print all registered buttons and their action IDs."""
    print("Quick Chart Buttons:")
    for action_id, button in self.quick_chart_panel._button_registry.items():
        print(f"  {action_id}: {button.text()}")
```

## Maintenance

### Adding New Snapshot Types

When adding new snapshot types:

1. Add buttons to `BUTTONS_BY_TYPE` in `constants.py`
2. Add help mappings in `MainWindow._register_quick_chart_help()`
3. Create corresponding HTML files in `data/help/`

### Updating Existing Help

1. Edit HTML files directly in `data/help/`
2. Changes take effect immediately (no rebuild needed)
3. Test after each update

### Bulk Updates

For bulk changes to help mappings:

```python
def update_all_quick_chart_help(self):
    """Re-register all quick chart help (useful for bulk updates)."""
    # Clear existing registrations
    for action_id in self.quick_chart_panel._button_registry:
        button = self.quick_chart_panel.get_button_by_action_id(action_id)
        if button:
            self._help_filter.unregister(button)
    
    # Re-register with updated mappings
    self._register_quick_chart_help()
```

This approach provides granular help for each quick chart button while maintaining the existing architecture and making it easy to extend for new features.
