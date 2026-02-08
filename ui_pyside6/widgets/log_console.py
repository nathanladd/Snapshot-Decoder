"""
Log console widget for displaying real-time log messages in the UI.

Provides a console-like view with color-coded messages by severity level,
support for overwritable progress lines, and real-time log streaming.
"""

import logging
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QComboBox, QLabel, QCheckBox
)
from PySide6.QtGui import QTextCursor, QColor, QTextCharFormat, QFont, QFontMetrics
from PySide6.QtCore import Qt, Slot, QTimer, QThread, Signal, QObject


class LogHandler(logging.Handler, QObject):
    """Custom logging handler that emits signals for Qt integration."""
    
    # Signal to emit log records
    log_record = Signal(logging.LogRecord)
    
    def __init__(self):
        logging.Handler.__init__(self)
        QObject.__init__(self)
        self.setLevel(logging.DEBUG)
    
    def emit(self, record: logging.LogRecord):
        """Emit a signal with the log record."""
        try:
            self.log_record.emit(record)
        except Exception:
            # Prevent logging errors from crashing the app
            pass


class LogConsole(QWidget):
    """
    Real-time log console widget with color-coded messages.
    
    Features:
    - Color-coded messages by severity level
    - Overwritable progress lines
    - Real-time log streaming
    - Level filtering
    - Auto-scroll toggle
    - Clear console
    """
    
    # Progress tracking for overwritable lines
    _progress_lines = {}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._setup_colors()
        self._setup_logging()
        
        # Auto-scroll enabled by default
        self._auto_scroll = True
        
        # Timer for updating UI
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._process_pending_logs)
        self._update_timer.start(50)  # Update every 50ms
        
        # Pending logs queue
        self._pending_logs = []
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        # Level filter
        self.level_label = QLabel("Level:")
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.setCurrentText("DEBUG")  # Show all by default
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        
        # Auto-scroll checkbox
        self.autoscroll_checkbox = QCheckBox("Auto-scroll")
        self.autoscroll_checkbox.setChecked(True)
        self.autoscroll_checkbox.toggled.connect(self._on_autoscroll_toggled)
        
        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_console)
        
        # Add to toolbar
        toolbar_layout.addWidget(self.level_label)
        toolbar_layout.addWidget(self.level_combo)
        toolbar_layout.addWidget(self.autoscroll_checkbox)
        toolbar_layout.addWidget(self.clear_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # Console text area
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(QFont("Consolas", 9))
        self.console.setMaximumBlockCount(1000)  # Limit to 1000 lines for performance
        
        layout.addWidget(self.console)
    
    def _setup_colors(self):
        """Setup color schemes for different log levels."""
        self.colors = {
            logging.DEBUG: QColor(128, 128, 128),      # Gray
            logging.INFO: QColor(0, 0, 0),              # Black
            logging.WARNING: QColor(255, 140, 0),       # Dark Orange
            logging.ERROR: QColor(255, 0, 0),           # Red
            logging.CRITICAL: QColor(139, 0, 0),        # Dark Red
        }
        
        # Background colors for emphasis
        self.background_colors = {
            logging.ERROR: QColor(255, 240, 240),      # Light Red
            logging.CRITICAL: QColor(139, 0, 0),       # Dark Red (text will be white)
        }
    
    def _setup_logging(self):
        """Setup the logging handler to capture log messages."""
        # Create custom handler
        self.log_handler = LogHandler()
        self.log_handler.log_record.connect(self._on_log_record)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
    
    def _get_level_filter(self) -> int:
        """Get the current logging level filter."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(self.level_combo.currentText(), logging.DEBUG)
    
    @Slot(logging.LogRecord)
    def _on_log_record(self, record: logging.LogRecord):
        """Handle incoming log records."""
        self._pending_logs.append(record)
    
    def _process_pending_logs(self):
        """Process pending log records and update the console."""
        if not self._pending_logs:
            return
        
        # Get current filter level
        filter_level = self._get_level_filter()
        
        # Process all pending logs
        while self._pending_logs:
            record = self._pending_logs.pop(0)
            
            # Filter by level
            if record.levelno < filter_level:
                continue
            
            # Check if this is a progress update
            if hasattr(record, 'progress_id'):
                self._update_progress_line(record)
            else:
                self._add_log_message(record)
    
    def _add_log_message(self, record: logging.LogRecord):
        """Add a regular log message to the console."""
        cursor = self.console.textCursor()
        
        # Move to end
        cursor.movePosition(QTextCursor.End)
        
        # Format the message
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        level_name = record.levelname.ljust(8)
        message = record.getMessage()
        
        # Get module/function info
        module = getattr(record, 'module', record.name)
        func_name = getattr(record, 'funcName', '')
        line_info = f"{module}:{func_name}" if func_name else module
        
        # Create formatted line
        #full_message = f"[{timestamp}] {level_name} {line_info}: {message}"
        full_message = f"[{timestamp}] {level_name}: {message}"
        
        # Apply formatting
        color = self.colors.get(record.levelno, QColor(0, 0, 0))
        bg_color = self.background_colors.get(record.levelno)
        
        # Set text color
        char_format = QTextCharFormat()
        char_format.setForeground(color)
        
        if bg_color:
            char_format.setBackground(bg_color)
            if record.levelno == logging.CRITICAL:
                char_format.setForeground(QColor(255, 255, 255))  # White text on dark red
        
        cursor.setCharFormat(char_format)
        cursor.insertText(full_message + "\n")
        
        # Auto-scroll if enabled
        if self._auto_scroll:
            self.console.ensureCursorVisible()
    
    def _update_progress_line(self, record: logging.LogRecord):
        """Update or create a progress line that can be overwritten."""
        progress_id = getattr(record, 'progress_id', 'default')
        message = record.getMessage()
        
        cursor = self.console.textCursor()
        
        if progress_id in self._progress_lines:
            # Update existing progress line
            line_num, old_length = self._progress_lines[progress_id]
            
            # Move to the line
            cursor.movePosition(QTextCursor.Start)
            for _ in range(line_num):
                cursor.movePosition(QTextCursor.Down)
            
            # Select and replace the line
            cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            
            # Insert new message
            char_format = QTextCharFormat()
            char_format.setForeground(QColor(0, 100, 0))  # Dark green for progress
            cursor.setCharFormat(char_format)
            cursor.insertText(message)
        else:
            # Create new progress line
            cursor.movePosition(QTextCursor.End)
            
            char_format = QTextCharFormat()
            char_format.setForeground(QColor(0, 100, 0))  # Dark green for progress
            cursor.setCharFormat(char_format)
            cursor.insertText(message + "\n")
            
            # Store line info
            line_num = cursor.blockNumber()
            self._progress_lines[progress_id] = (line_num, len(message))
        
        # Auto-scroll if enabled
        if self._auto_scroll:
            self.console.ensureCursorVisible()
    
    @Slot(str)
    def _on_level_changed(self, level: str):
        """Handle level filter change."""
        # Clear console and re-add filtered messages
        self._clear_console()
    
    @Slot(bool)
    def _on_autoscroll_toggled(self, enabled: bool):
        """Handle auto-scroll toggle."""
        self._auto_scroll = enabled
    
    @Slot()
    def _clear_console(self):
        """Clear the console."""
        self.console.clear()
        self._progress_lines.clear()
    
    def log_progress(self, progress_id: str, message: str):
        """Log a progress message that can be overwritten."""
        # Create a fake log record for progress
        record = logging.LogRecord(
            name="progress",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.progress_id = progress_id
        self._on_log_record(record)
    
    def closeEvent(self, event):
        """Clean up when widget is closed."""
        # Remove the log handler
        root_logger = logging.getLogger()
        if self.log_handler in root_logger.handlers:
            root_logger.removeHandler(self.log_handler)
        
        # Stop the timer
        self._update_timer.stop()
        
        super().closeEvent(event)
