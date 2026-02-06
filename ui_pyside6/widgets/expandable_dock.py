"""
Expandable dock widget with custom title bar and collapse functionality.

Provides a dockable widget that can expand/collapse with a button in the title bar,
similar to LogConsoleDock but for general content.
"""

from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStyle, QFrame, QLabel
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont


class ExpandableDock(QDockWidget):
    """
    Expandable dock widget with custom title bar and collapse functionality.
    
    Can be docked to any side of the main window or floated as a separate window.
    Features an expand/collapse button in the title bar.
    """
    
    # Signal emitted when expansion state changes
    expansion_changed = Signal(bool)
    
    def __init__(self, title: str = "Panel", parent=None):
        super().__init__(title, parent)
        
        # Track expansion state
        self._is_expanded = True
        self._collapsed_size = QSize(0, 30)  # Size when collapsed
        self._expanded_size = QSize(200, 400)  # Size when expanded
        self._content_widget: Optional[QWidget] = None
        
        # Set dock widget properties
        self.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea |
            Qt.DockWidgetArea.RightDockWidgetArea |
            Qt.DockWidgetArea.TopDockWidgetArea |
            Qt.DockWidgetArea.BottomDockWidgetArea
        )
        
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
            QDockWidget QWidget#contentWidget {
                padding-left: 8px;
            }
            QDockWidget QWidget#contentWidget QTreeWidget {
                margin-left: 0px;
            }
        """)
        
        # Create custom title bar with expand/collapse button
        self._setup_title_bar()
        
        # Default to not floating
        self.setFloating(False)
        
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
    
    def set_content_widget(self, widget: QWidget):
        """Set the content widget to be displayed when expanded."""
        # Clear existing content
        if self._content_widget:
            self.setWidget(None)
            self._content_widget.setParent(None)
        
        # Add new content
        self._content_widget = widget
        if widget:
            # Set object name for CSS targeting
            widget.setObjectName("contentWidget")
            # Force style update
            widget.setStyle(widget.style())
            self.setWidget(widget)
            widget.setVisible(self._is_expanded)
    
    def toggle_expand(self):
        """Toggle between expanded and collapsed states."""
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """Expand the dock widget to show full content."""
        self._is_expanded = True
        if self._content_widget:
            self._content_widget.setVisible(True)
        self.resize(self._expanded_size)
        self._update_expand_button_icon()
        self.expansion_changed.emit(True)
    
    def collapse(self):
        """Collapse the dock widget to show only title bar."""
        self._is_expanded = False
        if self._content_widget:
            self._content_widget.setVisible(False)
        self.resize(self._collapsed_size)
        self._update_expand_button_icon()
        self.expansion_changed.emit(False)
    
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
        if expanded != self._is_expanded:
            if expanded:
                self.expand()
            else:
                self.collapse()
    
    def set_collapsed_size(self, size: QSize):
        """Set the size when collapsed."""
        self._collapsed_size = size
        if not self._is_expanded:
            self.resize(size)
    
    def set_expanded_size(self, size: QSize):
        """Set the size when expanded."""
        self._expanded_size = size
        if self._is_expanded:
            self.resize(size)
    
    def get_collapsed_size(self) -> QSize:
        """Get the size when collapsed."""
        return self._collapsed_size
    
    def get_expanded_size(self) -> QSize:
        """Get the size when expanded."""
        return self._expanded_size
    
    def get_content_widget(self) -> Optional[QWidget]:
        """Get the current content widget."""
        return self._content_widget
