"""
PID Debug Configuration

Thin wrapper that delegates to the AppSettings singleton so that
debug/logging preferences are persisted in settings.json.

The public API (get_*/set_* functions) is kept for backward compatibility.
"""

from domain.app_settings import app_settings


def get_pid_debug_setting() -> bool:
    """Get the current PID debug logging setting."""
    return app_settings.enable_pid_debug

def get_log_interval() -> float:
    """Get the log interval in seconds."""
    return app_settings.log_interval

def get_log_on_stop() -> bool:
    """Get whether to log when slider stops."""
    return app_settings.log_on_stop

def get_position_threshold() -> float:
    """Get the position change threshold."""
    return app_settings.position_threshold

def set_pid_debug_logging(enabled: bool):
    """Set PID debug logging on/off."""
    app_settings.enable_pid_debug = enabled
    app_settings.save()

def set_log_interval(seconds: float):
    """Set the log interval in seconds."""
    app_settings.log_interval = seconds
    app_settings.save()

def set_log_on_stop(enabled: bool):
    """Set whether to log when slider stops."""
    app_settings.log_on_stop = enabled
    app_settings.save()

def set_position_threshold(threshold: float):
    """Set the position change threshold."""
    app_settings.position_threshold = threshold
    app_settings.save()
