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
        
        # Primary list with up/down buttons
        primary_list_row = QHBoxLayout()
        self._primary_list = QListWidget()
        self._primary_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        primary_list_row.addWidget(self._primary_list)
        
        # Up/down buttons for primary
        primary_btn_col = QVBoxLayout()
        primary_btn_col.setSpacing(2)
        self._primary_up_btn = QPushButton("▲")
        self._primary_up_btn.setFixedWidth(30)
        self._primary_up_btn.setToolTip("Move selected up")
        self._primary_up_btn.clicked.connect(self._on_primary_move_up)
        primary_btn_col.addWidget(self._primary_up_btn)
        
        self._primary_down_btn = QPushButton("▼")
        self._primary_down_btn.setFixedWidth(30)
        self._primary_down_btn.setToolTip("Move selected down")
        self._primary_down_btn.clicked.connect(self._on_primary_move_down)
        primary_btn_col.addWidget(self._primary_down_btn)
        primary_btn_col.addStretch()
        primary_list_row.addLayout(primary_btn_col)
        primary_layout.addLayout(primary_list_row)
        
        self._remove_primary_btn = QPushButton("Remove Selected")
        self._remove_primary_btn.clicked.connect(self._on_remove_from_primary)
        primary_layout.addWidget(self._remove_primary_btn)
        
        layout.addWidget(primary_group, stretch=1)
        
        # Secondary axis group
        secondary_group = QGroupBox("Secondary Axis (Right)")
        secondary_layout = QVBoxLayout(secondary_group)
        secondary_layout.setSpacing(4)
        
        # Secondary list with up/down buttons
        secondary_list_row = QHBoxLayout()
        self._secondary_list = QListWidget()
        self._secondary_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        secondary_list_row.addWidget(self._secondary_list)
        
        # Up/down buttons for secondary
        secondary_btn_col = QVBoxLayout()
        secondary_btn_col.setSpacing(2)
        self._secondary_up_btn = QPushButton("▲")
        self._secondary_up_btn.setFixedWidth(30)
        self._secondary_up_btn.setToolTip("Move selected up")
        self._secondary_up_btn.clicked.connect(self._on_secondary_move_up)
        secondary_btn_col.addWidget(self._secondary_up_btn)
        
        self._secondary_down_btn = QPushButton("▼")
        self._secondary_down_btn.setFixedWidth(30)
        self._secondary_down_btn.setToolTip("Move selected down")
        self._secondary_down_btn.clicked.connect(self._on_secondary_move_down)
        secondary_btn_col.addWidget(self._secondary_down_btn)
        secondary_btn_col.addStretch()
        secondary_list_row.addLayout(secondary_btn_col)
        secondary_layout.addLayout(secondary_list_row)
        
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
        added = False
        for item in self._available_list.selectedItems():
            pid = item.text()
            if pid not in self._primary_pids:
                self._primary_pids.append(pid)
                self._primary_list.addItem(pid)
                added = True
        if added:
            self.pids_changed.emit()
    
    def _on_add_to_secondary(self):
        """Add selected PIDs to secondary axis."""
        added = False
        for item in self._available_list.selectedItems():
            pid = item.text()
            if pid not in self._secondary_pids:
                self._secondary_pids.append(pid)
                self._secondary_list.addItem(pid)
                added = True
        if added:
            self.pids_changed.emit()
    
    def _on_remove_from_primary(self):
        """Remove selected PIDs from primary axis."""
        removed = False
        for item in self._primary_list.selectedItems():
            pid = item.text()
            if pid in self._primary_pids:
                self._primary_pids.remove(pid)
            self._primary_list.takeItem(self._primary_list.row(item))
            removed = True
        if removed:
            self.pids_changed.emit()
    
    def _on_remove_from_secondary(self):
        """Remove selected PIDs from secondary axis."""
        removed = False
        for item in self._secondary_list.selectedItems():
            pid = item.text()
            if pid in self._secondary_pids:
                self._secondary_pids.remove(pid)
            self._secondary_list.takeItem(self._secondary_list.row(item))
            removed = True
        if removed:
            self.pids_changed.emit()
    
    def _on_primary_move_up(self):
        """Move selected items up in primary list."""
        self._move_selected_up(self._primary_list, self._primary_pids)
    
    def _on_primary_move_down(self):
        """Move selected items down in primary list."""
        self._move_selected_down(self._primary_list, self._primary_pids)
    
    def _on_secondary_move_up(self):
        """Move selected items up in secondary list."""
        self._move_selected_up(self._secondary_list, self._secondary_pids)
    
    def _on_secondary_move_down(self):
        """Move selected items down in secondary list."""
        self._move_selected_down(self._secondary_list, self._secondary_pids)
    
    def _move_selected_up(self, list_widget: QListWidget, pid_list: List[str]):
        """Move selected items up in the list."""
        selected_rows = sorted([list_widget.row(item) for item in list_widget.selectedItems()])
        if not selected_rows or selected_rows[0] == 0:
            return
        
        for row in selected_rows:
            # Swap in pid_list
            pid_list[row], pid_list[row - 1] = pid_list[row - 1], pid_list[row]
            # Swap in list widget
            item = list_widget.takeItem(row)
            list_widget.insertItem(row - 1, item)
            item.setSelected(True)
        
        self.pids_changed.emit()
    
    def _move_selected_down(self, list_widget: QListWidget, pid_list: List[str]):
        """Move selected items down in the list."""
        selected_rows = sorted([list_widget.row(item) for item in list_widget.selectedItems()], reverse=True)
        if not selected_rows or selected_rows[0] == list_widget.count() - 1:
            return
        
        for row in selected_rows:
            # Swap in pid_list
            pid_list[row], pid_list[row + 1] = pid_list[row + 1], pid_list[row]
            # Swap in list widget
            item = list_widget.takeItem(row)
            list_widget.insertItem(row + 1, item)
            item.setSelected(True)
        
        self.pids_changed.emit()
    
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
    
    def set_pids(self, primary_pids: List[str], secondary_pids: List[str], emit_signal: bool = False):
        """Set the PIDs programmatically (e.g., from a quick chart)."""
        # Clear current selections
        self._primary_pids.clear()
        self._secondary_pids.clear()
        self._primary_list.clear()
        self._secondary_list.clear()
        
        # Add primary PIDs
        for pid in primary_pids:
            if pid in self._all_pids:
                self._primary_pids.append(pid)
                self._primary_list.addItem(pid)
        
        # Add secondary PIDs
        for pid in secondary_pids:
            if pid in self._all_pids:
                self._secondary_pids.append(pid)
                self._secondary_list.addItem(pid)
        
        if emit_signal:
            self.pids_changed.emit()
    
    def clear(self):
        """Clear the panel."""
        self.set_snapshot(None)
