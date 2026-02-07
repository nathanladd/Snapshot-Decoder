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


class HeaderPanel(QWidget):
    """Panel displaying snapshot header information with toolbar."""
    
    # Signals for toolbar actions
    open_requested = Signal()
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
        group = QGroupBox("Snapshot Info")
        group_layout = QGridLayout(group)
        group_layout.setSpacing(4)
        
        # Labels for header fields
        self._labels = {}
        fields = [
            ("file_name", "File:"),
            ("snapshot_type", "Type:"),
            ("date_time", "Date/Time:"),
            ("hours", "Engine Hours:"),
            ("idle_time", "Idle Time:"),
        ]
        
        for row, (key, label_text) in enumerate(fields):
            label = QLabel(label_text)
            # Use QFont for bold instead of stylesheet to preserve palette colors
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            value_label = QLabel("-")
            value_label.setWordWrap(True)
            
            group_layout.addWidget(label, row, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
            group_layout.addWidget(value_label, row, 1, Qt.AlignmentFlag.AlignTop)
            self._labels[key] = value_label
        
        group_layout.setColumnStretch(1, 1)
        layout.addWidget(group)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot data."""
        if snapshot is None:
            for label in self._labels.values():
                label.setText("-")
            return
        
        self._labels["file_name"].setText(snapshot.file_name)
        self._labels["snapshot_type"].setText(snapshot.snapshot_type.description)
        self._labels["date_time"].setText(snapshot.date_time or "-")
        self._labels["hours"].setText(f"{snapshot.hours:.1f}" if snapshot.hours else "-")
        self._labels["idle_time"].setText(f"{snapshot.idle_time:.1f}" if snapshot.idle_time else "-")
    
    def clear(self):
        """Clear all displayed data."""
        self.set_snapshot(None)
    
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
        open_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogOpenButton))
        open_btn.setToolTip("Open snapshot file (Ctrl+O)")
        open_btn.clicked.connect(self.open_requested.emit)
        self._toolbar.addWidget(open_btn)
        
        # Raw Data action
        raw_data_btn = QToolButton()
        raw_data_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView))
        raw_data_btn.setToolTip("Show raw data table")
        raw_data_btn.clicked.connect(self.raw_data_requested.emit)
        self._toolbar.addWidget(raw_data_btn)
        
        # Clean Table action
        clean_table_btn = QToolButton()
        clean_table_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogListView))
        clean_table_btn.setToolTip("Show clean data table")
        clean_table_btn.clicked.connect(self.clean_table_requested.emit)
        self._toolbar.addWidget(clean_table_btn)
        
        # Chart Table action
        chart_table_btn = QToolButton()
        chart_table_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon))
        chart_table_btn.setToolTip("Show chart data table")
        chart_table_btn.clicked.connect(self.chart_table_requested.emit)
        self._toolbar.addWidget(chart_table_btn)
        
        # Help action
        help_btn = QToolButton()
        help_btn.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_DialogHelpButton))
        help_btn.setToolTip("Show help documentation (F1)")
        help_btn.clicked.connect(self.help_requested.emit)
        self._toolbar.addWidget(help_btn)
