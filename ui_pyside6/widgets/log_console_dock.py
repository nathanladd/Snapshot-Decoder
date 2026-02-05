"""
Dockable log console panel for the main window.

Provides a dockable widget that contains the log console with
proper integration into the main window's dock system.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QPushButton, QStyle, QLabel
from PySide6.QtCore import Qt, QSize

from .log_console import LogConsole


class LogConsoleDock(QDockWidget):
    """
    Dockable log console widget with expand/collapse functionality.
    
    Can be docked to any side of the main window or floated as a separate window.
    Features an expand/collapse button in the title bar.
    """
    
    def __init__(self, parent=None):
        super().__init__("Log Console", parent)
        
        # Track expansion state
        self._is_expanded = True
        self._collapsed_size = QSize(0, 30)  # Height when collapsed
        self._expanded_size = QSize(200, 300)  # Size when expanded
        
        # Set dock widget properties
        self.setAllowedAreas(
            Qt.DockWidgetArea.BottomDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea
        )
        
        # Create custom title bar with expand/collapse button
        self._setup_title_bar()
        
        # Create the log console
        self.log_console = LogConsole(self)
        self.setWidget(self.log_console)
        
        # Default to bottom docking
        self.setFloating(False)
        
        # Add padding around the dock widget
        self.setStyleSheet("""
            QDockWidget {
                border: 1px solid #C0C0C0;
                margin: 2px;
                background-color: #F8F8F8;
            }
            QDockWidget::title {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F0F0F0, stop:1 #E0E0E0);
                border-bottom: 1px solid #C0C0C0;
                padding: 2px;
            }
        """)
        
        # Set initial size
        self.resize(self._expanded_size)
    
    def _setup_title_bar(self):
        """Setup custom title bar with expand/collapse button and drag handle."""
        # Create title bar widget
        title_bar = QWidget()
        title_bar.setFixedHeight(25)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)
        title_layout.setSpacing(5)
        
        # Add drag handle indicator
        self.drag_handle = QLabel()
        self.drag_handle.setFixedHeight(16)
        self.drag_handle.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(120, 120, 120, 0.3), 
                    stop:0.5 rgba(120, 120, 120, 0.5), 
                    stop:1 rgba(120, 120, 120, 0.3));
                border: 1px solid rgba(120, 120, 120, 0.4);
                border-radius: 3px;
                margin: 2px;
            }
            QLabel:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(100, 100, 100, 0.4), 
                    stop:0.5 rgba(100, 100, 100, 0.6), 
                    stop:1 rgba(100, 100, 100, 0.4));
                border: 1px solid rgba(100, 100, 100, 0.6);
            }
        """)
        self.drag_handle.setToolTip("Drag to move panel")
        
        # Add expand/collapse button
        self.expand_btn = QPushButton()
        self.expand_btn.setFixedSize(16, 16)
        self.expand_btn.clicked.connect(self.toggle_expand)
        self._update_expand_button_icon()
        
        # Style the button
        self.expand_btn.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 0px;
                background: transparent;
            }
            QPushButton:hover {
                background: rgba(200, 200, 200, 100);
                border-radius: 2px;
            }
            QPushButton:pressed {
                background: rgba(150, 150, 150, 100);
            }
        """)
        
        # Add to layout
        title_layout.addWidget(self.drag_handle, 1)  # Stretch with width
        title_layout.addWidget(self.expand_btn)
        
        # Set custom title bar
        self.setTitleBarWidget(title_bar)
    
    def toggle_expand(self):
        """Toggle between expanded and collapsed states."""
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """Expand the dock widget to show full content."""
        self._is_expanded = True
        self.log_console.setVisible(True)
        self.resize(self._expanded_size)
        self._update_expand_button_icon()
    
    def collapse(self):
        """Collapse the dock widget to show only title bar."""
        self._is_expanded = False
        self.log_console.setVisible(False)
        self.resize(self._collapsed_size)
        self._update_expand_button_icon()
    
    def _update_expand_button_icon(self):
        """Update the expand/collapse button icon based on state."""
        if self._is_expanded:
            # Show collapse icon (down arrow)
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown)
            self.expand_btn.setIcon(icon)
            self.expand_btn.setToolTip("Collapse")
        else:
            # Show expand icon (up arrow)
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp)
            self.expand_btn.setIcon(icon)
            self.expand_btn.setToolTip("Expand")
    
    def is_expanded(self) -> bool:
        """Check if the dock widget is expanded."""
        return self._is_expanded
    
    def set_expanded(self, expanded: bool):
        """Set the expansion state."""
        if expanded:
            self.expand()
        else:
            self.collapse()
    
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
