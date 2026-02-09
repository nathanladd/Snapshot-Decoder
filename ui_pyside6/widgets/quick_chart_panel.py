"""
Quick chart buttons panel widget.
"""

from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox, 
    QScrollArea, QSizePolicy, QToolButton, QMenu
)
from PySide6.QtCore import Signal, Qt

from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE, REFERENCE_CHARTS_BY_TYPE


class QuickChartPanel(QWidget):
    """Panel with quick chart buttons based on snapshot type."""
    
    # Signal emitted when a quick chart is requested
    chart_requested = Signal(str)  # action_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: List[QPushButton] = []
        self._reference_button: Optional[QToolButton] = None
        self._current_snapshot_type: Optional[SnapType] = None
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
        scroll.setMaximumHeight(90)
        
        # Container for buttons - use grid layout for 2 rows
        self._button_container = QWidget()
        self._button_layout = QGridLayout(self._button_container)
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
        
        # Also clear reference button if it exists
        if self._reference_button:
            self._button_layout.removeWidget(self._reference_button)
            self._reference_button.deleteLater()
            self._reference_button = None
    
    def set_snapshot_type(self, snapshot_type: Optional[SnapType]):
        """Update buttons based on snapshot type."""
        self._clear_buttons()
        self._current_snapshot_type = snapshot_type
        
        if snapshot_type is None or snapshot_type == SnapType.EMPTY:
            self._show_placeholder()
            return
        
        # Add reference button if available for this snapshot type
        self._add_reference_button_if_available(snapshot_type)
        
        # Get buttons for this snapshot type
        buttons_config = BUTTONS_BY_TYPE.get(snapshot_type, [])
        
        if not buttons_config:
            placeholder = QPushButton("No quick charts for this type")
            placeholder.setEnabled(False)
            self._button_layout.addWidget(placeholder)
            self._buttons.append(placeholder)
            return
        
        # Create compact buttons in 2-row grid
        # Adjust column offset if reference button is present
        col_offset = 1 if self._reference_button else 0
        num_buttons = len(buttons_config)
        num_cols = (num_buttons + 1) // 2  # Calculate columns needed for 2 rows
        
        for i, (name, action_id, tooltip) in enumerate(buttons_config):
            btn = QPushButton(name)
            btn.setToolTip(tooltip)
            btn.setProperty("action_id", action_id)
            btn.clicked.connect(self._on_button_clicked)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            btn.setMaximumWidth(120)
            
            row = i % 2
            col = col_offset + (i // 2)
            self._button_layout.addWidget(btn, row, col)
            self._buttons.append(btn)
    
    def _on_button_clicked(self):
        """Handle button click."""
        btn = self.sender()
        if btn:
            action_id = btn.property("action_id")
            if action_id:
                self.chart_requested.emit(action_id)
    
    def _add_reference_button_if_available(self, snapshot_type: SnapType):
        """Add reference charts button if available for this snapshot type."""
        if snapshot_type not in REFERENCE_CHARTS_BY_TYPE:
            return
        
        # Create reference button
        self._reference_button = QToolButton()
        self._reference_button.setText("Reference\nCharts")
        self._reference_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._reference_button.setPopupMode(QToolButton.InstantPopup)
        self._reference_button.setStyleSheet("""
            QToolButton {
                background-color: #FFD700;
                border: 2px solid #FFA500;
                border-radius: 4px;
                padding: 4px 4px;
                font-weight: bold;
            }
            QToolButton::menu-indicator {
                width: 12px;
                height: 12px;
                subcontrol-position: bottom center;
            }
        """)
        self._reference_button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        
        # Create dropdown menu
        reference_menu = QMenu(self._reference_button)
        
        # Add individual chart options from constants
        reference_charts = REFERENCE_CHARTS_BY_TYPE[snapshot_type]
        for name, action_id, tooltip in reference_charts:
            action = reference_menu.addAction(name)
            action.setToolTip(tooltip)
            action.triggered.connect(
                lambda checked, aid=action_id: self.chart_requested.emit(aid)
            )
        
        self._reference_button.setMenu(reference_menu)
        
        # Span both rows so it matches the height of two button rows
        self._button_layout.addWidget(self._reference_button, 0, 0, 2, 1)
    
    def clear(self):
        """Clear the panel."""
        self.set_snapshot_type(None)
