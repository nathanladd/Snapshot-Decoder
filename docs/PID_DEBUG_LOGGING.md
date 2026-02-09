# PID Debug Logging System

This document explains the PID interpolation debug logging system that helps diagnose issues with live PID values in the time slider.

## Overview

The PID interpolation system includes comprehensive logging with **rate limiting** to help you understand how different PIDs behave with the time slider without overwhelming the logs. This logging captures:

- Data quality issues (NaN values, data types)
- Interpolation success/failure for each PID
- Card update status in the live values display
- Performance and caching information

## Configuration

### In-App Settings (Recommended)

The easiest way to configure PID debug logging is through the application menu:

1. **Main Window**: Go to `Debug → Debug Settings...`
2. **Pop-out Window**: Go to `Debug → Debug Settings...`

The settings dialog provides:
- **Enable/Disable** PID debug logging
- **Rate limiting** configuration
- **Real-time updates** to running widgets

### Manual Configuration

You can also edit `pid_debug_config.py` directly:

```python
# Set to True to enable detailed PID debugging
# Set to False to disable for production use
ENABLE_PID_DEBUG_LOGGING = True
```

### Rate Limiting Configuration

The logging system includes intelligent rate limiting to prevent log spam:

```python
# Rate limiting configuration for debug logs
LOG_INTERVAL_SECONDS = 1.0  # Minimum time between log entries (seconds)
LOG_ON_STOP = True  # Log when slider stops moving (even if interval hasn't passed)
POSITION_CHANGE_THRESHOLD = 0.01  # Minimum position change to consider as "moving"
```

### Runtime Control

You can also control logging programmatically:

```python
# In PIDInterpolator
interpolator = PIDInterpolator(enable_debug_logging=False)
interpolator.set_debug_logging(True)  # Enable at runtime

# In LiveValuesWidget  
live_widget.set_debug_logging(False)  # Disable logging
```

### Settings Dialog

The debug settings dialog provides an intuitive interface for configuring PID logging:

#### Main Settings
- **Enable PID debug logging**: Master on/off switch for all PID debugging
- **Log Interval**: Time between log entries (0.1-10.0 seconds)
- **Log when slider stops**: Capture final position when movement ends
- **Position Threshold**: Minimum movement to consider slider "active"

#### Real-time Updates
Settings take effect immediately when applied:
- Running widgets update instantly
- No application restart required
- Changes persist for future sessions

#### Dialog Controls
- **OK**: Apply settings and close
- **Cancel**: Discard changes and close  
- **Apply**: Apply settings without closing

## Rate Limiting Behavior

The logging system uses intelligent rate limiting to prevent log spam:

### When Logs Are Generated

1. **First Movement**: Always logs when slider starts moving
2. **Time-based**: Logs at most once per `LOG_INTERVAL_SECONDS` (default: 1 second)
3. **Stop Detection**: Logs when slider stops moving (if `LOG_ON_STOP` is True)
4. **Position Threshold**: Only considers movement if position changes by more than `POSITION_CHANGE_THRESHOLD`

### Example Behavior

```
[Slider starts moving] → LOG (first movement)
[Slider moves continuously] → LOG every 1 second
[Slider stops] → LOG (final position, even if < 1 second since last log)
[Slider moves slightly (< threshold)] → NO LOG (considered stopped)
[Slider moves significantly (> threshold)] → LOG (movement detected)
```

## Log Output

### PID Interpolation Logs

When enabled, you'll see detailed output like:

```
=== PID Interpolation Debug at X=12.345 ===
PID: BattU_u
  - Data shape: (684,)
  - Valid values: 683/684 (NaN: 1)
  - Data type: float64
  - Sample values: [12.1 12.2 12.3 12.4 12.5]
  - SUCCESS: Interpolated value = 12.34
PID: Epm_nEng
  - Data shape: (684,)
  - Valid values: 684/684 (NaN: 0)
  - Data type: float64
  - Sample values: [1800 1801 1802 1803 1804]
  - SUCCESS: Interpolated value = 1801.23
=== Interpolation Complete: 2/2 PIDs successful ===
```

### Live Values Update Logs

```
=== Live Values Update Debug ===
Position: 12.345
Interpolated values: ['BattU_u', 'Epm_nEng']
Available cards: ['BattU_u', 'Epm_nEng']
  ✓ Updated BattU_u: 12.34
  ✓ Updated Epm_nEng: 1801.23
Updated 2/2 cards
=== Live Values Update Complete ===
```

## Interpreting the Logs

### Status Indicators

- **✓ SUCCESS** - PID interpolated successfully and card updated
- **✗ SKIPPED** - PID has all NaN values (no data to interpolate)
- **⚠ FAILED** - PID has data but interpolation failed
- **✗ NO CARD** - Interpolation worked but no card exists
- **⚠ NO VALUE** - Card exists but no interpolated value

### Error Logging

Actual errors are now logged with **ERROR** level (red color in most log consoles):
- **Data type errors**: Non-numeric data that can't be interpolated
- **Interpolation failures**: Invalid results (NaN, infinity)
- **Missing cards**: Interpolation succeeded but no display card exists
- **Missing values**: Card exists but no interpolated value available

These errors will appear prominently in red in the log console, making them easy to spot when debugging object vs. float PID issues.

### Common Issues

1. **All NaN Values**: PID column contains no valid data
2. **Data Type Issues**: Non-numeric data that can't be interpolated
3. **Missing Cards**: Card creation failed or PID not in chart config
4. **Out of Range**: Slider position outside data bounds

### Object vs. Float PIDs

Many PIDs in automotive data are stored as objects (strings, mixed types) instead of floats. The system handles this automatically:

#### Automatic Data Cleaning
- **Chart Creation**: Object columns are converted to numeric with `errors='coerce'`
- **Non-numeric values**: Become NaN and are skipped during interpolation
- **Mixed data**: Valid numbers are preserved, invalid values become NaN

#### Error Detection
When object PIDs cause issues, you'll see:
```
ERROR: PID interpolation error for Epm_nEng: Cannot cast array data from dtype('O') to dtype('float64') according to the rule 'safe' at position 12.345
```

#### Debugging Object PIDs
1. **Enable debug logging** to see data types and sample values
2. **Check the "Data type" field** in interpolation logs
3. **Look for "Sample values"** to understand the actual data format
4. **Monitor ERROR messages** for problematic conversions

## Configuration Options

### Adjusting Rate Limiting

For more frequent logging (during debugging):
```python
LOG_INTERVAL_SECONDS = 0.5  # Log every 0.5 seconds
POSITION_CHANGE_THRESHOLD = 0.005  # More sensitive to movement
```

For less frequent logging (production):
```python
LOG_INTERVAL_SECONDS = 2.0  # Log every 2 seconds
LOG_ON_STOP = False  # Don't log when slider stops
```

### Disabling Stop Detection

If you only want time-based logging:
```python
LOG_ON_STOP = False  # Don't log when slider stops
```

## Log Files

The debug output is captured by the application's logging system and appears in:
- The in-app log console
- The main application log file (if file logging is enabled)

## Performance Impact

The debug logging has minimal performance impact when disabled. When enabled with rate limiting, the overhead is negligible even for frequent slider movements.

## Troubleshooting

### PIDs Not Updating

1. Check if the PID appears in the interpolation logs
2. Verify the PID has valid (non-NaN) data
3. Ensure the PID card was created successfully
4. Check for data type conversion errors

### Too Many Logs

1. Increase `LOG_INTERVAL_SECONDS` to reduce frequency
2. Set `LOG_ON_STOP = False` to disable stop detection
3. Increase `POSITION_CHANGE_THRESHOLD` to be less sensitive

### Too Few Logs

1. Decrease `LOG_INTERVAL_SECONDS` to increase frequency
2. Ensure `LOG_ON_STOP = True` to capture final positions
3. Decrease `POSITION_CHANGE_THRESHOLD` to be more sensitive

## Production Use

For production deployment, set `ENABLE_PID_DEBUG_LOGGING = False` in `pid_debug_config.py` to eliminate all PID debug logging overhead.
