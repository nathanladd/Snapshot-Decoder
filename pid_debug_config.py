"""
PID Debug Configuration

Simple configuration file to control PID interpolation debug logging.
Set ENABLE_PID_DEBUG_LOGGING to False to disable verbose logging in production.
"""

# Set to False to disable verbose PID interpolation logging
# Set to True to enable detailed debugging for PID interpolation issues
ENABLE_PID_DEBUG_LOGGING = True

# Rate limiting configuration for debug logs
LOG_INTERVAL_SECONDS = 1.0  # Minimum time between log entries (seconds)
LOG_ON_STOP = True  # Log when slider stops moving (even if interval hasn't passed)
POSITION_CHANGE_THRESHOLD = 0.01  # Minimum position change to consider as "moving"

def get_pid_debug_setting() -> bool:
    """Get the current PID debug logging setting."""
    return ENABLE_PID_DEBUG_LOGGING

def get_log_interval() -> float:
    """Get the log interval in seconds."""
    return LOG_INTERVAL_SECONDS

def get_log_on_stop() -> bool:
    """Get whether to log when slider stops."""
    return LOG_ON_STOP

def get_position_threshold() -> float:
    """Get the position change threshold."""
    return POSITION_CHANGE_THRESHOLD

def set_pid_debug_logging(enabled: bool):
    """Set PID debug logging on/off (requires app restart)."""
    global ENABLE_PID_DEBUG_LOGGING
    ENABLE_PID_DEBUG_LOGGING = enabled

def set_log_interval(seconds: float):
    """Set the log interval in seconds."""
    global LOG_INTERVAL_SECONDS
    LOG_INTERVAL_SECONDS = seconds

def set_log_on_stop(enabled: bool):
    """Set whether to log when slider stops."""
    global LOG_ON_STOP
    LOG_ON_STOP = enabled

def set_position_threshold(threshold: float):
    """Set the position change threshold."""
    global POSITION_CHANGE_THRESHOLD
    POSITION_CHANGE_THRESHOLD = threshold
