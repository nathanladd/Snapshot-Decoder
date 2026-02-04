"""
PID info window for PySide6.

Shows PID descriptions with search functionality and axis checkboxes.
"""

from typing import Dict, Any, Set
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QApplication,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class PidInfoWindow(QMainWindow):
    """PID info window with search and axis checkbox functionality."""
    
    def __init__(self, parent, pid_info: Dict[str, Dict[str, Any]], snapshot_path: str):
        super().__init__(parent)
        self.pid_info = pid_info
        self.snapshot_path = snapshot_path
        
        # Track current chart PIDs
        self.current_primary_pids: Set[str] = set()
        self.current_secondary_pids: Set[str] = set()
        
        self._setup_ui()
        self._populate_tree()
    
    def update_chart_pids(self, primary_pids: list, secondary_pids: list):
        """Update the current chart PID selections."""
        self.current_primary_pids = set(primary_pids)
        self.current_secondary_pids = set(secondary_pids)
        self._sync_checkboxes()
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle(f"PID Descriptions: {self.snapshot_path}")
        self.setGeometry(100, 100, 900, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Search box at the top
        search_frame = QWidget()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(QLabel("Search Descriptions:"))
        
        self.search_entry = QLineEdit()
        self.search_entry.textChanged.connect(self._filter_descriptions)
        search_layout.addWidget(self.search_entry)
        
        # Add clear button for search
        clear_search_btn = QPushButton("✕")
        clear_search_btn.setToolTip("Clear search")
        clear_search_btn.setFixedSize(24, 24)
        clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffe6e6;
                border: 1px solid #ffcccc;
                border-radius: 12px;
                font-weight: bold;
                color: #cc0000;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ffcccc;
                border: 1px solid #ff9999;
            }
            QPushButton:pressed {
                background-color: #ffb3b3;
                border: 1px solid #ff6666;
            }
        """)
        clear_search_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(clear_search_btn)
        
        layout.addWidget(search_frame)
        
        # Tree widget for PID info
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Primary", "Secondary", "PID Name", "Description", "Unit"])
        
        # Configure tree columns
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Primary checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Secondary checkbox
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # PID name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive) # Description
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Unit
        
        header.resizeSection(0, 80)   # Primary checkbox column
        header.resizeSection(1, 80)   # Secondary checkbox column
        header.resizeSection(2, 180)  # PID column
        header.resizeSection(4, 90)    # Unit column
        
        # Make header bold
        font = header.font()
        font.setBold(True)
        header.setFont(font)
        
        # Add checkbox headers (using header labels instead of setHeaderWidget)
        # Note: QTreeWidget doesn't have setHeaderWidget, so we'll use header labels
        # with checkbox indicators in the first two columns
        
        layout.addWidget(self.tree)
        
        # Button frame at bottom
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        
        refresh_btn = QPushButton("Sync with Chart")
        refresh_btn.setToolTip("Sync checkboxes with current chart PIDs")
        refresh_btn.clicked.connect(self._sync_with_chart)
        button_layout.addWidget(refresh_btn)
        
        clear_all_btn = QPushButton(" ✕ Clear All")
        clear_all_btn.setToolTip("Clear all axis selections")
        
        # Style with faint red background to match main window clear button
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffe6e6;
                border: 1px solid #ffcccc;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                color: #cc0000;
            }
            QPushButton:hover {
                background-color: #ffcccc;
                border: 1px solid #ff9999;
            }
            QPushButton:pressed {
                background-color: #ffb3b3;
                border: 1px solid #ff6666;
            }
        """)
        
        # Connect to parent's clear functionality instead of local method
        clear_all_btn.clicked.connect(self._on_clear_all_clicked)
        button_layout.addWidget(clear_all_btn)
        
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # Connect checkbox changes
        self.tree.itemChanged.connect(self._on_item_changed)
    
    def _populate_tree(self):
        """Populate the tree with all PID information."""
        self.tree.clear()
        
        for pid, data in self.pid_info.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(2, pid)
            item.setText(3, data.get("Description", ""))
            item.setText(4, data.get("Unit", ""))
            
            # Store the full PID data for later use
            item.setData(2, Qt.ItemDataRole.UserRole, pid)
            
            # Create checkboxes for primary and secondary axes
            primary_checkbox = QCheckBox()
            secondary_checkbox = QCheckBox()
            
            # Style checkboxes for better visibility on white background
            checkbox_style = """
                QCheckBox {
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                    border: 2px solid #333333;
                    border-radius: 3px;
                    background-color: white;
                }
                QCheckBox::indicator:hover {
                    border: 2px solid #0078d4;
                    background-color: #f0f8ff;
                }
                QCheckBox::indicator:checked {
                    background-color: #28a745;
                    border: 2px solid #28a745;
                }
                QCheckBox::indicator:checked:hover {
                    background-color: #218838;
                    border: 2px solid #218838;
                }
            """
            primary_checkbox.setStyleSheet(checkbox_style)
            secondary_checkbox.setStyleSheet(checkbox_style)
            
            # Set checkboxes as widget items
            self.tree.setItemWidget(item, 0, primary_checkbox)
            self.tree.setItemWidget(item, 1, secondary_checkbox)
            
            # Connect checkbox signals
            primary_checkbox.stateChanged.connect(
                lambda state, p=pid, cb=primary_checkbox: self._on_primary_checkbox_changed(state, p, cb)
            )
            secondary_checkbox.stateChanged.connect(
                lambda state, p=pid, cb=secondary_checkbox: self._on_secondary_checkbox_changed(state, p, cb)
            )
            
            # Store references to checkboxes
            item.setData(0, Qt.ItemDataRole.UserRole, primary_checkbox)
            item.setData(1, Qt.ItemDataRole.UserRole, secondary_checkbox)
    
    def _clear_search(self):
        """Clear the search input and show all PIDs."""
        self.search_entry.clear()
    
    def _filter_descriptions(self):
        """Filter tree items based on search text."""
        search_term = self.search_entry.text().strip().lower()
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            description = item.text(3).lower()
            pid_name = item.text(2).lower()
            
            # Show/hide based on search match
            item.setHidden(search_term not in description and search_term not in pid_name)
    
    def _on_primary_checkbox_changed(self, state: int, pid: str, checkbox: QCheckBox):
        """Handle primary axis checkbox change."""
        if state == Qt.CheckState.Checked.value:
            # Add to primary axis
            if pid not in self.current_primary_pids:
                self.current_primary_pids.add(pid)
                # Remove from secondary if it was there
                if pid in self.current_secondary_pids:
                    self.current_secondary_pids.remove(pid)
                    secondary_cb = self._get_secondary_checkbox(pid)
                    if secondary_cb:
                        secondary_cb.blockSignals(True)
                        secondary_cb.setChecked(False)
                        secondary_cb.blockSignals(False)
        else:
            # Remove from primary axis
            self.current_primary_pids.discard(pid)
        
        # Emit signal to update chart
        self._emit_chart_update()
    
    def _on_secondary_checkbox_changed(self, state: int, pid: str, checkbox: QCheckBox):
        """Handle secondary axis checkbox change."""
        if state == Qt.CheckState.Checked.value:
            # Add to secondary axis
            if pid not in self.current_secondary_pids:
                self.current_secondary_pids.add(pid)
                # Remove from primary if it was there
                if pid in self.current_primary_pids:
                    self.current_primary_pids.remove(pid)
                    primary_cb = self._get_primary_checkbox(pid)
                    if primary_cb:
                        primary_cb.blockSignals(True)
                        primary_cb.setChecked(False)
                        primary_cb.blockSignals(False)
        else:
            # Remove from secondary axis
            self.current_secondary_pids.discard(pid)
        
        # Emit signal to update chart
        self._emit_chart_update()
    
    def _get_primary_checkbox(self, pid: str) -> QCheckBox:
        """Get the primary checkbox for a PID."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(2) == pid:
                return item.data(0, Qt.ItemDataRole.UserRole)
        return None
    
    def _get_secondary_checkbox(self, pid: str) -> QCheckBox:
        """Get the secondary checkbox for a PID."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(2) == pid:
                return item.data(1, Qt.ItemDataRole.UserRole)
        return None
    
    def _emit_chart_update(self):
        """Emit signals to update the chart with current selections."""
        # Get parent main window and emit signals
        parent = self.parent()
        if hasattr(parent, 'pid_info_window_update_chart'):
            parent.pid_info_window_update_chart(
                list(self.current_primary_pids),
                list(self.current_secondary_pids)
            )
    
    def _sync_checkboxes(self):
        """Sync checkboxes with current chart PIDs."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            pid = item.text(2)
            
            primary_cb = self._get_primary_checkbox(pid)
            secondary_cb = self._get_secondary_checkbox(pid)
            
            if primary_cb and secondary_cb:
                primary_cb.blockSignals(True)
                secondary_cb.blockSignals(True)
                
                primary_cb.setChecked(pid in self.current_primary_pids)
                secondary_cb.setChecked(pid in self.current_secondary_pids)
                
                primary_cb.blockSignals(False)
                secondary_cb.blockSignals(False)
    
    def _on_primary_header_changed(self, state: int):
        """Handle primary header checkbox change (not implemented)."""
        # Header checkboxes not available in PySide6 QTreeWidget
        pass
    
    def _on_secondary_header_changed(self, state: int):
        """Handle secondary header checkbox change (not implemented)."""
        # Header checkboxes not available in PySide6 QTreeWidget
        pass
    
    def _sync_with_chart(self):
        """Sync checkboxes with current chart configuration."""
        # Get current chart PIDs from parent
        parent = self.parent()
        if hasattr(parent, 'get_current_chart_pids'):
            primary, secondary = parent.get_current_chart_pids()
            self.update_chart_pids(primary, secondary)
    
    def _on_clear_all_clicked(self):
        """Handle clear all button click - delegate to parent."""
        parent = self.parent()
        if hasattr(parent, '_on_clear_all'):
            # Call the main window's clear all method
            parent._on_clear_all()
        else:
            # Fallback to local clear if parent method not available
            self._clear_all_selections()
    
    def _clear_all_selections(self):
        """Clear all checkbox selections (fallback method)."""
        self.current_primary_pids.clear()
        self.current_secondary_pids.clear()
        self._sync_checkboxes()
        self._emit_chart_update()
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle tree item changes (not used for checkboxes)."""
        pass
