"""
Logging configuration for Snapshot Decoder.

Provides centralized logging setup with real-time console display only.
No file logging - all output goes to the in-app log console.
"""

import logging
from typing import Optional


class SnapshotLogger:
    """Centralized logging configuration for the application (console only)."""
    
    def __init__(self, app_name: str = "SnapshotDecoder"):
        self.app_name = app_name
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Setup console-only logging
        self._setup_console_logging()
    
    def _setup_console_logging(self):
        """Setup console-only logging (no files)."""
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Add a null handler to prevent "No handlers found" warnings
        # The actual console display is handled by the LogConsole widget
        null_handler = logging.NullHandler()
        self.logger.addHandler(null_handler)
    
    def log_custody_event(self, event_type: str, details: str, level: str = "INFO"):
        """Log a chain of custody event."""
        # This will be captured by the LogConsole widget
        message = f"{event_type} | {details}"
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        self.logger.log(log_level, message)
    
    def log_file_loaded(self, file_path: str, file_size: int, snapshot_type: str, 
                       load_time: float, record_count: int):
        """Log successful file loading with chain of custody details."""
        from pathlib import Path
        details = (
            f"File: {Path(file_path).name} | "
            f"Size: {file_size:,} bytes | "
            f"Type: {snapshot_type} | "
            f"Load Time: {load_time:.2f}s | "
            f"Records: {record_count:,}"
        )
        self.log_custody_event("FILE_LOADED", details)
    
    def log_file_error(self, file_path: str, error: str):
        """Log file loading error."""
        from pathlib import Path
        details = f"File: {Path(file_path).name} | Error: {error}"
        self.log_custody_event("FILE_ERROR", details, "ERROR")
    
    def log_chart_generated(self, chart_type: str, pids: list, snapshot_file: str):
        """Log chart generation for audit trail."""
        from pathlib import Path
        pid_list = ", ".join(pids[:5])  # Limit to first 5 PIDs
        if len(pids) > 5:
            pid_list += f" (+{len(pids)-5} more)"
        
        details = (
            f"Chart: {chart_type} | "
            f"PIDs: {pid_list} | "
            f"Source: {Path(snapshot_file).name}"
        )
        self.log_custody_event("CHART_GENERATED", details)
    
    def log_export(self, export_type: str, file_path: str, snapshot_source: str):
        """Log data export events."""
        from pathlib import Path
        details = (
            f"Export: {export_type} | "
            f"Output: {Path(file_path).name} | "
            f"Source: {Path(snapshot_source).name}"
        )
        self.log_custody_event("DATA_EXPORTED", details)


# Global logger instance
_global_logger: Optional[SnapshotLogger] = None


def get_logger() -> SnapshotLogger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = SnapshotLogger()
    return _global_logger


def log_custody(event_type: str, details: str, level: str = "INFO"):
    """Convenience function for custody logging."""
    logger = get_logger()
    logger.log_custody_event(event_type, details, level)


# Convenience functions for common events
def log_file_loaded(file_path: str, file_size: int, snapshot_type: str, 
                   load_time: float, record_count: int):
    """Log successful file loading."""
    logger = get_logger()
    logger.log_file_loaded(file_path, file_size, snapshot_type, load_time, record_count)


def log_file_error(file_path: str, error: str):
    """Log file loading error."""
    logger = get_logger()
    logger.log_file_error(file_path, error)


def log_chart_generated(chart_type: str, pids: list, snapshot_file: str):
    """Log chart generation."""
    logger = get_logger()
    logger.log_chart_generated(chart_type, pids, snapshot_file)


def log_export(export_type: str, file_path: str, snapshot_source: str):
    """Log data export."""
    logger = get_logger()
    logger.log_export(export_type, file_path, snapshot_source)


# Standard logging functions
def debug(message: str):
    """Log debug message."""
    logger = get_logger()
    logger.logger.debug(message)


def info(message: str):
    """Log info message."""
    logger = get_logger()
    logger.logger.info(message)


def warning(message: str):
    """Log warning message."""
    logger = get_logger()
    logger.logger.warning(message)


def error(message: str):
    """Log error message."""
    logger = get_logger()
    logger.logger.error(message)


def critical(message: str):
    """Log critical message."""
    logger = get_logger()
    logger.logger.critical(message)
