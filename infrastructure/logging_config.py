"""
Logging configuration for Snapshot Decoder.

Provides centralized logging setup with:
- Chain of custody records for loaded snapshots
- Diagnostic logging for troubleshooting
- Toggleable verbose mode for detailed debugging
- Rotating log files in app data folder
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class SnapshotLogger:
    """Centralized logging configuration for the application."""
    
    def __init__(self, app_name: str = "SnapshotDecoder"):
        self.app_name = app_name
        self.logger = logging.getLogger(app_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Create logs directory
        self.logs_dir = self._get_logs_directory()
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup handlers
        self._setup_handlers()
        
        # Chain of custody tracking
        self.custody_log = self._setup_custody_logging()
    
    def _get_logs_directory(self) -> Path:
        """Get the appropriate logs directory based on platform."""
        if sys.platform == "win32":
            # Windows: %APPDATA%/SnapshotDecoder/logs
            app_data = os.environ.get("APPDATA", "")
            base_dir = Path(app_data) / self.app_name
        else:
            # macOS/Linux: ~/.local/share/SnapshotDecoder/logs
            home = Path.home()
            base_dir = home / ".local" / "share" / self.app_name
        
        logs_dir = base_dir / "logs"
        # Create parent directories if they don't exist
        base_dir.mkdir(parents=True, exist_ok=True)
        return logs_dir
    
    def _setup_handlers(self):
        """Setup file handlers only (no console output)."""
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler with rotation (10MB max, keep 5 files)
        log_file = self.logs_dir / f"{self.app_name.lower()}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        
        # Add file handler only
        self.logger.addHandler(file_handler)
    
    def _setup_custody_logging(self) -> logging.Logger:
        """Setup separate logger for chain of custody tracking."""
        custody_logger = logging.getLogger(f"{self.app_name}.custody")
        custody_logger.setLevel(logging.INFO)
        custody_logger.handlers.clear()
        
        # Separate custody log file
        custody_file = self.logs_dir / "custody.log"
        custody_handler = logging.handlers.RotatingFileHandler(
            custody_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        
        # Custody formatter (structured for easy parsing)
        custody_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        custody_handler.setFormatter(custody_formatter)
        custody_logger.addHandler(custody_handler)
        
        # Prevent propagation to root logger
        custody_logger.propagate = False
        
        return custody_logger
    
    def log_custody_event(self, event_type: str, details: str, level: str = "INFO"):
        """Log a chain of custody event."""
        message = f"{event_type} | {details}"
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        log_level = level_map.get(level.upper(), logging.INFO)
        self.custody_log.log(log_level, message)
    
    def log_file_loaded(self, file_path: str, file_size: int, snapshot_type: str, 
                       load_time: float, record_count: int):
        """Log successful file loading with chain of custody details."""
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
        details = f"File: {Path(file_path).name} | Error: {error}"
        self.log_custody_event("FILE_ERROR", details, "ERROR")
    
    def log_chart_generated(self, chart_type: str, pids: list, snapshot_file: str):
        """Log chart generation for audit trail."""
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
