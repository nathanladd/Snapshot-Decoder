"""
PID selection panel widget.
"""

from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QGroupBox, QLineEdit, QLabel, QPushButton, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal

from domain.snapshot import Snapshot


class PidPanel(QWidget):
    """Panel for selecting PIDs to plot."""
    
    # Signal emitted when PID selection changes
    pids_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot: Optional[Snapshot] = None
        self._all_pids: List[str] = []
        self._primary_pids: List[str] = []
        self._secondary_pids: List[str] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Available PIDs section
        available_group = QGroupBox("Available PIDs")
        available_layout = QVBoxLayout(available_group)
        available_layout.setSpacing(4)
        
        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Filter:"))
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Type to filter PIDs...")
        self._search_box.textChanged.connect(self._on_filter_changed)
        search_layout.addWidget(self._search_box)
        available_layout.addLayout(search_layout)
        
        # Available PIDs list
        self._available_list = QListWidget()
        self._available_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        available_layout.addWidget(self._available_list)
        
        # Add buttons
        btn_layout = QHBoxLayout()
        self._add_primary_btn = QPushButton("Add to Primary ▶")
        self._add_primary_btn.clicked.connect(self._on_add_to_primary)
        btn_layout.addWidget(self._add_primary_btn)
        
        self._add_secondary_btn = QPushButton("Add to Secondary ▶")
        self._add_secondary_btn.clicked.connect(self._on_add_to_secondary)
        btn_layout.addWidget(self._add_secondary_btn)
        available_layout.addLayout(btn_layout)
        
        layout.addWidget(available_group, stretch=2)
        
        # Primary axis group
        primary_group = QGroupBox("Primary Axis (Left)")
        primary_layout = QVBoxLayout(primary_group)
        primary_layout.setSpacing(4)
        
        self._primary_list = QListWidget()
        self._primary_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        primary_layout.addWidget(self._primary_list)
        
        self._remove_primary_btn = QPushButton("Remove Selected")
        self._remove_primary_btn.clicked.connect(self._on_remove_from_primary)
        primary_layout.addWidget(self._remove_primary_btn)
        
        layout.addWidget(primary_group, stretch=1)
        
        # Secondary axis group
        secondary_group = QGroupBox("Secondary Axis (Right)")
        secondary_layout = QVBoxLayout(secondary_group)
        secondary_layout.setSpacing(4)
        
        self._secondary_list = QListWidget()
        self._secondary_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        secondary_layout.addWidget(self._secondary_list)
        
        self._remove_secondary_btn = QPushButton("Remove Selected")
        self._remove_secondary_btn.clicked.connect(self._on_remove_from_secondary)
        secondary_layout.addWidget(self._remove_secondary_btn)
        
        layout.addWidget(secondary_group, stretch=1)
        
        # Plot button
        self._plot_btn = QPushButton("Plot Selected PIDs")
        self._plot_btn.clicked.connect(self.pids_changed.emit)
        layout.addWidget(self._plot_btn)
        
        # Clear button
        self._clear_btn = QPushButton("Clear All")
        self._clear_btn.clicked.connect(self._on_clear_selections)
        layout.addWidget(self._clear_btn)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the panel with snapshot PIDs."""
        self._snapshot = snapshot
        self._primary_pids.clear()
        self._secondary_pids.clear()
        self._primary_list.clear()
        self._secondary_list.clear()
        
        if snapshot is None or snapshot.snapshot is None:
            self._all_pids = []
            self._available_list.clear()
            return
        
        # Get PIDs (exclude Frame and Time)
        self._all_pids = [
            col for col in snapshot.snapshot.columns
            if col not in ("Frame", "Time", "Time (MM:SS)")
        ]
        
        self._populate_available_list(self._all_pids)
    
    def _populate_available_list(self, pids: List[str]):
        """Populate the available PIDs list."""
        self._available_list.clear()
        for pid in sorted(pids):
            self._available_list.addItem(pid)
    
    def _on_filter_changed(self, text: str):
        """Handle filter text changes."""
        if not text:
            self._populate_available_list(self._all_pids)
            return
        
        filtered = [
            pid for pid in self._all_pids
            if text.lower() in pid.lower()
        ]
        self._populate_available_list(filtered)
    
    def _on_add_to_primary(self):
        """Add selected PIDs to primary axis."""
        for item in self._available_list.selectedItems():
            pid = item.text()
            if pid not in self._primary_pids:
                self._primary_pids.append(pid)
                self._primary_list.addItem(pid)
    
    def _on_add_to_secondary(self):
        """Add selected PIDs to secondary axis."""
        for item in self._available_list.selectedItems():
            pid = item.text()
            if pid not in self._secondary_pids:
                self._secondary_pids.append(pid)
                self._secondary_list.addItem(pid)
    
    def _on_remove_from_primary(self):
        """Remove selected PIDs from primary axis."""
        for item in self._primary_list.selectedItems():
            pid = item.text()
            if pid in self._primary_pids:
                self._primary_pids.remove(pid)
            self._primary_list.takeItem(self._primary_list.row(item))
    
    def _on_remove_from_secondary(self):
        """Remove selected PIDs from secondary axis."""
        for item in self._secondary_list.selectedItems():
            pid = item.text()
            if pid in self._secondary_pids:
                self._secondary_pids.remove(pid)
            self._secondary_list.takeItem(self._secondary_list.row(item))
    
    def _on_clear_selections(self):
        """Clear all selected PIDs and emit signal."""
        self._primary_pids.clear()
        self._secondary_pids.clear()
        self._primary_list.clear()
        self._secondary_list.clear()
        # Emit signal so chart can be updated
        self.pids_changed.emit()
    
    def get_primary_pids(self) -> List[str]:
        """Get the list of primary PIDs."""
        return self._primary_pids.copy()
    
    def get_secondary_pids(self) -> List[str]:
        """Get the list of secondary PIDs."""
        return self._secondary_pids.copy()
    
    def clear(self):
        """Clear the panel."""
        self.set_snapshot(None)
