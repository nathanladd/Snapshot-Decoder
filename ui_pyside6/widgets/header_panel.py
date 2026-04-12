"""
Header panel widget displaying snapshot metadata with toolbar.
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox, QToolBar, QToolButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon

from domain.snapshot import Snapshot
from utils import resource_path


class HeaderPanel(QWidget):
    """Panel displaying snapshot header information with toolbar."""
    
    # Signals for toolbar actions
    open_requested = Signal()
    close_requested = Signal()
    raw_data_requested = Signal()
    clean_table_requested = Signal()
    chart_table_requested = Signal()
    help_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add toolbar
        self._setup_toolbar()
        layout.addWidget(self._toolbar)
        
        # Group box for header info
        self._group = QGroupBox("Header Info")
        self._group.setStyleSheet("QGroupBox { font-weight: bold; }")
        self._group_layout = QGridLayout(self._group)
        self._group_layout.setSpacing(4)
        
        # Container for dynamic header labels
        self._header_labels = []
        
        layout.addWidget(self._group)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot data."""
        # Clear existing header labels
        self._clear_header_labels()
        
        if snapshot is None:
            return
        
        # Add file name as first entry
        self._add_header_row("File:", snapshot.file_name)
        
        # Add snapshot type as second entry
        self._add_header_row("Type:", snapshot.snapshot_type.description)
        
        # Add all parsed header information
        if snapshot.header_list:
            for label, value in snapshot.header_list:
                self._add_header_row(f"{label}:", value)
        
        # Add derived values if available
        if snapshot.hours is not None:
            self._add_header_row("Engine Hours:", f"{snapshot.hours:.1f}")
        if snapshot.idle_time is not None and snapshot.idle_time > 0:
            self._add_header_row("Idle Time:", f"{snapshot.idle_time:.1f}")
    
    def clear(self):
        """Clear all displayed data."""
        self._clear_header_labels()
    
    def _clear_header_labels(self):
        """Clear all dynamic header labels."""
        # Remove all widgets from the layout
        while self._group_layout.count():
            child = self._group_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Clear the header labels list
        self._header_labels.clear()
    
    def _add_header_row(self, label_text: str, value_text: str):
        """Add a new header row to the layout."""
        row = self._group_layout.rowCount()
        
        label = QLabel(label_text)
        # Use QFont for bold instead of stylesheet to preserve palette colors
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        
        value_label = QLabel(value_text or "-")
        value_label.setWordWrap(True)
        
        self._group_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self._group_layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignTop)
        
        # Store references to the labels
        self._header_labels.append((label, value_label))
        
        # Ensure the value column stretches
        self._group_layout.setColumnStretch(1, 1)
    
    def _setup_toolbar(self):
        """Set up the toolbar with common actions."""
        self._toolbar = QToolBar()
        self._toolbar.setOrientation(Qt.Horizontal)
        self._toolbar.setMovable(False)
        
        # Apply consistent styling matching existing chart toolbar
        self._toolbar.setStyleSheet("""
            QToolButton {
                border: 1px solid #C0C0C0;
                border-radius: 3px;
                padding: 4px;
                background-color: #F0F0F0;
            }
            QToolButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #0078d4;
            }
            QToolButton:pressed {
                background-color: #D0D0D0;
            }
        """)
        
        # Open action
        open_btn = QToolButton()
        open_btn.setIcon(QIcon(resource_path("data/images/folder-open.png")))
        open_btn.setToolTip("Open snapshot file (Ctrl+O)")
        open_btn.clicked.connect(self.open_requested.emit)
        self._toolbar.addWidget(open_btn)
        
        # Close action
        close_btn = QToolButton()
        close_btn.setIcon(QIcon(resource_path("data/images/folder-close.png")))
        close_btn.setToolTip("Close snapshot")
        close_btn.clicked.connect(self.close_requested.emit)
        self._toolbar.addWidget(close_btn)
        
        # Raw Data action
        raw_data_btn = QToolButton()
        raw_data_btn.setIcon(QIcon(resource_path("data/images/raw-table.png")))
        raw_data_btn.setToolTip("Show raw data table")
        raw_data_btn.clicked.connect(self.raw_data_requested.emit)
        self._toolbar.addWidget(raw_data_btn)
        
        # Clean Table action
        clean_table_btn = QToolButton()
        clean_table_btn.setIcon(QIcon(resource_path("data/images/data-cleaning.png")))
        clean_table_btn.setToolTip("Show clean data table")
        clean_table_btn.clicked.connect(self.clean_table_requested.emit)
        self._toolbar.addWidget(clean_table_btn)
        
        # Chart Table action
        chart_table_btn = QToolButton()
        chart_table_btn.setIcon(QIcon(resource_path("data/images/chart-table.png")))
        chart_table_btn.setToolTip("Show chart data table")
        chart_table_btn.clicked.connect(self.chart_table_requested.emit)
        self._toolbar.addWidget(chart_table_btn)
        
        # Help action
        help_btn = QToolButton()
        help_btn.setIcon(QIcon(resource_path("data/images/information.png")))
        help_btn.setToolTip("Show help documentation (F1)")
        help_btn.clicked.connect(self.help_requested.emit)
        self._toolbar.addWidget(help_btn)
