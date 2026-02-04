"""
PID info window for PySide6.

Shows PID descriptions with search functionality and add-to-axis buttons.
"""

from typing import Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QApplication,
    QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class PidInfoWindow(QMainWindow):
    """PID info window with search and add-to-axis functionality."""
    
    # Signal emitted when a PID is added to an axis
    pid_added_to_primary = Signal(str)
    pid_added_to_secondary = Signal(str)
    
    def __init__(self, parent, pid_info: Dict[str, Dict[str, Any]], snapshot_path: str):
        super().__init__(parent)
        self.pid_info = pid_info
        self.snapshot_path = snapshot_path
        
        self._setup_ui()
        self._populate_tree()
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle(f"PID Descriptions: {self.snapshot_path}")
        self.setGeometry(100, 100, 800, 400)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        
        # Search box at the top
        search_frame = QWidget()
        search_layout = QHBoxLayout(search_frame)
        search_layout.addWidget(QLabel("Search Descriptions:"))
        
        self.search_entry = QLineEdit()
        self.search_entry.textChanged.connect(self._filter_descriptions)
        search_layout.addWidget(self.search_entry)
        
        layout.addWidget(search_frame)
        
        # Tree widget for PID info
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["PID Name", "Description", "Unit"])
        
        # Configure tree
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 180)  # PID column
        header.resizeSection(2, 90)   # Unit column
        
        # Make header bold
        font = header.font()
        font.setBold(True)
        header.setFont(font)
        
        layout.addWidget(self.tree)
        
        # Button frame at bottom
        button_frame = QWidget()
        button_layout = QHBoxLayout(button_frame)
        
        self.add_primary_btn = QPushButton("Add to Primary Axis")
        self.add_primary_btn.clicked.connect(self._add_to_primary)
        self.add_primary_btn.setEnabled(False)  # Disabled until selection
        
        self.add_secondary_btn = QPushButton("Add to Secondary Axis")
        self.add_secondary_btn.clicked.connect(self._add_to_secondary)
        self.add_secondary_btn.setEnabled(False)  # Disabled until selection
        
        button_layout.addWidget(self.add_primary_btn)
        button_layout.addWidget(self.add_secondary_btn)
        button_layout.addStretch()
        
        layout.addWidget(button_frame)
        
        # Connect selection change
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
    
    def _populate_tree(self):
        """Populate the tree with all PID information."""
        self.tree.clear()
        
        for pid, data in self.pid_info.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(0, pid)
            item.setText(1, data.get("Description", ""))
            item.setText(2, data.get("Unit", ""))
            
            # Store the full PID data for later use
            item.setData(0, Qt.ItemDataRole.UserRole, pid)
    
    def _filter_descriptions(self):
        """Filter tree items based on search text."""
        search_term = self.search_entry.text().strip().lower()
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            description = item.text(1).lower()
            
            # Show/hide based on search match
            item.setHidden(search_term not in description and search_term not in item.text(0).lower())
    
    def _on_selection_changed(self):
        """Handle tree selection changes."""
        selected_items = self.tree.selectedItems()
        has_selection = len(selected_items) > 0
        
        self.add_primary_btn.setEnabled(has_selection)
        self.add_secondary_btn.setEnabled(has_selection)
    
    def _add_to_primary(self):
        """Add selected PID to primary axis."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        
        pid = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
        self.pid_added_to_primary.emit(pid)
    
    def _add_to_secondary(self):
        """Add selected PID to secondary axis."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return
        
        pid = selected_items[0].data(0, Qt.ItemDataRole.UserRole)
        self.pid_added_to_secondary.emit(pid)
