"""
Expandable panel widget with custom title bar and collapse functionality.

Provides a container widget that can expand/collapse with a button in the title bar,
similar to dock widgets but for regular panels.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStyle, QFrame
from PySide6.QtCore import Qt, QSize, Signal, Property
from PySide6.QtGui import QFont


class ExpandablePanel(QWidget):
    """
    Expandable panel widget with custom title bar and collapse functionality.
    
    Features an expand/collapse button in the title bar and smooth transitions
    between expanded and collapsed states.
    """
    
    # Signal emitted when expansion state changes
    expansion_changed = Signal(bool)
    
    def __init__(self, title: str = "Panel", parent=None):
        super().__init__(parent)
        
        # Properties
        self._title = title
        self._is_expanded = True
        self._collapsed_height = 30
        self._expanded_height = 400
        self._content_widget: Optional[QWidget] = None
        
        # Setup UI
        self._setup_ui()
        self._update_state()
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Title bar
        self._setup_title_bar()
        
        # Content frame
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.StyledPanel)
        self.content_layout = QVBoxLayout(self.content_frame)
        self.content_layout.setContentsMargins(4, 4, 4, 4)
        
        self.main_layout.addWidget(self.title_bar)
        self.main_layout.addWidget(self.content_frame)
    
    def _setup_title_bar(self):
        """Setup the custom title bar with expand/collapse button."""
        self.title_bar = QFrame()
        self.title_bar.setFrameStyle(QFrame.StyledPanel)
        self.title_bar.setFixedHeight(self._collapsed_height)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(5, 2, 5, 2)
        title_layout.setSpacing(5)
        
        # Expand/collapse button
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
        
        # Title label
        self.title_label = QLabel(self._title)
        title_font = self.title_label.font()
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        
        # Add to layout
        title_layout.addWidget(self.expand_btn)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()
    
    def set_content_widget(self, widget: QWidget):
        """Set the content widget to be displayed when expanded."""
        # Clear existing content
        if self._content_widget:
            self.content_layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)
        
        # Add new content
        self._content_widget = widget
        if widget:
            self.content_layout.addWidget(widget)
    
    def toggle_expand(self):
        """Toggle between expanded and collapsed states."""
        if self._is_expanded:
            self.collapse()
        else:
            self.expand()
    
    def expand(self):
        """Expand the panel to show full content."""
        self._is_expanded = True
        self._update_state()
        self.expansion_changed.emit(True)
    
    def collapse(self):
        """Collapse the panel to show only title bar."""
        self._is_expanded = False
        self._update_state()
        self.expansion_changed.emit(False)
    
    def _update_state(self):
        """Update the visual state based on expansion."""
        # Update content visibility
        self.content_frame.setVisible(self._is_expanded)
        
        # Update button icon
        self._update_expand_button_icon()
        
        # Update panel size
        if self._is_expanded:
            self.setMaximumSize(16777215, 16777215)  # No max size limit
        else:
            self.setFixedHeight(self._collapsed_height)
    
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
        """Check if the panel is expanded."""
        return self._is_expanded
    
    def set_expanded(self, expanded: bool):
        """Set the expansion state."""
        if expanded != self._is_expanded:
            if expanded:
                self.expand()
            else:
                self.collapse()
    
    def set_title(self, title: str):
        """Set the panel title."""
        self._title = title
        self.title_label.setText(title)
    
    def get_title(self) -> str:
        """Get the panel title."""
        return self._title
    
    def set_collapsed_height(self, height: int):
        """Set the height when collapsed."""
        self._collapsed_height = height
        self.title_bar.setFixedHeight(height)
        if not self._is_expanded:
            self.setFixedHeight(height)
    
    def get_collapsed_height(self) -> int:
        """Get the height when collapsed."""
        return self._collapsed_height
    
    def get_content_widget(self) -> Optional[QWidget]:
        """Get the current content widget."""
        return self._content_widget


# Import QLabel for the title label
from PySide6.QtWidgets import QLabel
