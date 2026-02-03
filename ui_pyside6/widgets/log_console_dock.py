"""
Dockable log console panel for the main window.

Provides a dockable widget that contains the log console with
proper integration into the main window's dock system.
"""

from PySide6.QtWidgets import QDockWidget
from PySide6.QtCore import Qt

from .log_console import LogConsole


class LogConsoleDock(QDockWidget):
    """
    Dockable log console widget.
    
    Can be docked to any side of the main window or floated as a separate window.
    """
    
    def __init__(self, parent=None):
        super().__init__("Log Console", parent)
        
        # Set dock widget properties
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Create the log console
        self.log_console = LogConsole(self)
        self.setWidget(self.log_console)
        
        # Default to bottom docking
        self.setFloating(False)
    
    def log_progress(self, progress_id: str, message: str):
        """Delegate progress logging to the embedded console."""
        self.log_console.log_progress(progress_id, message)
    
    def clear_console(self):
        """Clear the console."""
        self.log_console._clear_console()
    
    def set_level_filter(self, level: str):
        """Set the log level filter."""
        self.log_console.level_combo.setCurrentText(level)
    
    def set_autoscroll(self, enabled: bool):
        """Set auto-scroll behavior."""
        self.log_console.autoscroll_checkbox.setChecked(enabled)
