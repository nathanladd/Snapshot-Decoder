"""
Dockable log console panel for the main window.

Provides a dockable widget that contains the log console with
proper integration into the main window's dock system.
"""

from PySide6.QtWidgets import QDockWidget, QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QSize

from .log_console import LogConsole


class LogConsoleDock(QDockWidget):
    """
    Dockable log console widget.
    
    Can be docked to any side of the main window or floated as a separate window.
    Uses a custom title bar with a left-justified title label.
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
        
        # Create custom title bar
        self._setup_title_bar()
        self.topLevelChanged.connect(self._on_top_level_changed)
        
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
                    stop:0 #EAF4FF, stop:1 #D8E9FF);
                border-bottom: 1px solid #AFC8E8;
                padding: 2px;
            }
        """)
        
        # Set initial size
        self.resize(self._expanded_size)
        self._on_top_level_changed(self.isFloating())
    
    def _setup_title_bar(self):
        """Setup custom title bar with left-justified title."""
        title_bar = QWidget()
        title_bar.setFixedHeight(25)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #EAF4FF, stop:1 #D8E9FF);
                border-bottom: 1px solid #AFC8E8;
            }
        """)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)
        title_layout.setSpacing(5)

        self.title_label = QLabel("Log Console")
        self.title_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #333;")
        title_layout.addWidget(self.title_label)
        title_layout.addStretch(1)

        btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 2px;
                background-color: #F0F0F0;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
            }
        """

        close_btn_style = """
            QPushButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 2px;
                background-color: #FFF0F0;
                font-size: 11px;
                font-weight: bold;
                color: #A40000;
            }
            QPushButton:hover {
                background-color: #FFD0D0;
                border: 1px solid #d40000;
            }
            QPushButton:pressed {
                background-color: #FFB8B8;
            }
        """

        self.popout_btn = QPushButton("↗")
        self.popout_btn.setFixedSize(22, 22)
        self.popout_btn.setStyleSheet(btn_style)
        self.popout_btn.clicked.connect(self._on_toggle_floating)
        title_layout.addWidget(self.popout_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setStyleSheet(close_btn_style)
        self.close_btn.setToolTip("Close")
        self.close_btn.clicked.connect(self._on_close_requested)
        title_layout.addWidget(self.close_btn)
        
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
    
    def collapse(self):
        """Collapse the dock widget to show only title bar."""
        self._is_expanded = False
        self.log_console.setVisible(False)
        self.resize(self._collapsed_size)
    
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

    def _on_toggle_floating(self):
        self.setFloating(not self.isFloating())

    def _on_close_requested(self):
        self.close()

    def _on_top_level_changed(self, is_floating: bool):
        if is_floating:
            self.popout_btn.setText("⇲")
            self.popout_btn.setToolTip("Dock panel")
        else:
            self.popout_btn.setText("↗")
            self.popout_btn.setToolTip("Pop out panel")
