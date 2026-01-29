"""
Quick chart buttons panel widget.
"""

from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, 
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import Signal, Qt

from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE


class QuickChartPanel(QWidget):
    """Panel with quick chart buttons based on snapshot type."""
    
    # Signal emitted when a quick chart is requested
    chart_requested = Signal(str)  # action_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: List[QPushButton] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Group box
        self._group = QGroupBox("Quick Charts")
        group_layout = QVBoxLayout(self._group)
        group_layout.setContentsMargins(4, 4, 4, 4)
        
        # Scroll area for buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setMaximumHeight(100)
        
        # Container for buttons - use horizontal flow
        self._button_container = QWidget()
        self._button_layout = QHBoxLayout(self._button_container)
        self._button_layout.setSpacing(4)
        self._button_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll.setWidget(self._button_container)
        group_layout.addWidget(scroll)
        
        layout.addWidget(self._group)
        
        # Show placeholder message
        self._show_placeholder()
    
    def _show_placeholder(self):
        """Show placeholder when no snapshot is loaded."""
        self._clear_buttons()
        placeholder = QPushButton("Load a snapshot to see quick charts")
        placeholder.setEnabled(False)
        self._button_layout.addWidget(placeholder)
        self._buttons.append(placeholder)
    
    def _clear_buttons(self):
        """Remove all buttons from the layout."""
        for btn in self._buttons:
            self._button_layout.removeWidget(btn)
            btn.deleteLater()
        self._buttons.clear()
    
    def set_snapshot_type(self, snapshot_type: Optional[SnapType]):
        """Update buttons based on snapshot type."""
        self._clear_buttons()
        
        if snapshot_type is None or snapshot_type == SnapType.EMPTY:
            self._show_placeholder()
            return
        
        # Get buttons for this snapshot type
        buttons_config = BUTTONS_BY_TYPE.get(snapshot_type, [])
        
        if not buttons_config:
            placeholder = QPushButton("No quick charts for this type")
            placeholder.setEnabled(False)
            self._button_layout.addWidget(placeholder)
            self._buttons.append(placeholder)
            return
        
        # Create compact buttons in horizontal row
        for i, (name, action_id, tooltip) in enumerate(buttons_config):
            btn = QPushButton(name)
            btn.setToolTip(tooltip)
            btn.setProperty("action_id", action_id)
            btn.clicked.connect(self._on_button_clicked)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            btn.setMaximumWidth(120)
            self._button_layout.addWidget(btn)
            self._buttons.append(btn)
        
        # Add stretch at end to keep buttons compact
        self._button_layout.addStretch()
    
    def _on_button_clicked(self):
        """Handle button click."""
        btn = self.sender()
        if btn:
            action_id = btn.property("action_id")
            if action_id:
                self.chart_requested.emit(action_id)
    
    def clear(self):
        """Clear the panel."""
        self.set_snapshot_type(None)
