"""
Integrated PID selection widget combining PID info window functionality.

Replaces the separate PID panel and PID info window with a unified interface.
"""

from typing import Dict, Any, Set, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QLineEdit, QMessageBox, QApplication,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QCheckBox,
    QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QBrush

from domain.snapshot import Snapshot
from ui.color_manager import ColorManager


class IntegratedPidWidget(QWidget):
    """Integrated PID selection widget with search and checkbox functionality."""
    
    # Signal emitted when PID selection changes
    pids_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot: Optional[Snapshot] = None
        self._all_pids: List[str] = []
        self._primary_pids: List[str] = []
        self._secondary_pids: List[str] = []
        self._current_chart_config = None  # Store current chart config
        
        # Track current chart PIDs
        self.current_primary_pids: Set[str] = set()
        self.current_secondary_pids: Set[str] = set()
        
        self._setup_ui()
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect internal signals."""
        # Connect checkbox changes
        self.tree.itemChanged.connect(self._on_item_changed)
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # PID selection group
        pid_group = QGroupBox("PID Selection")
        pid_layout = QVBoxLayout(pid_group)
        pid_layout.setSpacing(4)
        
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
        
        pid_layout.addWidget(search_frame)
        
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
        
        pid_layout.addWidget(self.tree)
        
        # Button frame at bottom
        clear_all_btn = QPushButton(" ✕ Clear Chart")
        clear_all_btn.setToolTip("Clear all axis selections and reset chart")
        
        # Style with faint red background to match main window clear button
        clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffe6e6;
                border: 1px solid #ffcccc;
                border-radius: 4px;
                padding: 6px 8px;
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
        clear_all_btn.clicked.connect(self._clear_all_selections)
        
        pid_layout.addWidget(clear_all_btn)
        
        layout.addWidget(pid_group, stretch=1)
    
    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Set the snapshot and populate available PIDs."""
        self._snapshot = snapshot
        if not snapshot:
            self.tree.clear()
            self._all_pids.clear()
            self._primary_pids.clear()
            self._secondary_pids.clear()
            return
        
        # Get all available PIDs
        self._all_pids = [
            col for col in snapshot.snapshot.columns 
            if col not in ("Frame", "Time", "Time (MM:SS)")
        ]
        
        # Store PID info
        self.pid_info = snapshot.pid_info
        
        # Populate tree
        self._populate_tree()
    
    def _populate_tree(self):
        """Populate the tree with all PID information."""
        self.tree.clear()
        
        if not hasattr(self, 'pid_info'):
            return
        
        for pid, data in self.pid_info.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(2, pid)
            item.setText(3, data.get("Description", ""))
            item.setText(4, data.get("Unit", ""))
            
            # Store the full PID data for later use
            item.setData(2, Qt.ItemDataRole.UserRole, pid)
            
            # Store item reference for color updates
            item.setData(3, Qt.ItemDataRole.UserRole, item)  # Store item itself for color updates
            
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
        
        # Update internal PID lists
        self._primary_pids = list(self.current_primary_pids)
        self._secondary_pids = list(self.current_secondary_pids)
        
        # Emit signal to update chart
        self.pids_changed.emit()
    
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
        
        # Update internal PID lists
        self._primary_pids = list(self.current_primary_pids)
        self._secondary_pids = list(self.current_secondary_pids)
        
        # Emit signal to update chart
        self.pids_changed.emit()
    
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
    
    def update_chart_pids(self, primary_pids: list, secondary_pids: list):
        """Update the current chart PID selections."""
        self.current_primary_pids = set(primary_pids)
        self.current_secondary_pids = set(secondary_pids)
        self._primary_pids = list(primary_pids)
        self._secondary_pids = list(secondary_pids)
        self._sync_checkboxes()
    
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
    
    def _clear_all_selections(self):
        """Clear all checkbox selections."""
        self.current_primary_pids.clear()
        self.current_secondary_pids.clear()
        self._primary_pids.clear()
        self._secondary_pids.clear()
        self._sync_checkboxes()
        self.pids_changed.emit()
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """Handle tree item changes (not used for checkboxes)."""
        pass
    
    def get_primary_pids(self) -> List[str]:
        """Get the list of primary PIDs."""
        return self._primary_pids.copy()
    
    def get_secondary_pids(self) -> List[str]:
        """Get the list of secondary PIDs."""
        return self._secondary_pids.copy()
    
    def set_pids(self, primary_pids: List[str], secondary_pids: List[str], emit_signal: bool = True):
        """Set the primary and secondary PID lists."""
        self._primary_pids = primary_pids.copy()
        self._secondary_pids = secondary_pids.copy()
        self.current_primary_pids = set(primary_pids)
        self.current_secondary_pids = set(secondary_pids)
        
        # Update checkboxes
        self._sync_checkboxes()
        
        # Emit signal if requested
        if emit_signal:
            self.pids_changed.emit()
    
    def update_chart_colors(self, config):
        """Update PID colors based on chart configuration."""
        if not config or not hasattr(self, 'pid_info'):
            # Reset all items to default colors
            self._reset_all_item_colors()
            return
        
        # Reset all items first
        self._reset_all_item_colors()
        
        # Get color manager
        color_manager = ColorManager()
        
        # Apply colors to primary axis PIDs
        for i, pid in enumerate(config.primary_axis.series):
            if pid in self.pid_info:
                color = color_manager.get_series_color(pid, is_secondary=False, series_index=i)
                self._apply_item_color(pid, color, is_primary=True)
        
        # Apply colors to secondary axis PIDs
        for i, pid in enumerate(config.secondary_axis.series):
            if pid in self.pid_info:
                color = color_manager.get_series_color(pid, is_secondary=True, series_index=i)
                self._apply_item_color(pid, color, is_primary=False)
    
    def _apply_item_color(self, pid: str, color: str, is_primary: bool):
        """Apply color to a PID item while keeping it readable."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.text(2) == pid:
                # Apply subtle background color to the PID name column
                bg_color = QColor(color)
                bg_color.setAlpha(30)  # Very subtle transparency (30/255)
                
                # Apply to PID name column (column 2)
                item.setBackground(2, bg_color)
                
                # Also apply to description column (column 3) for consistency
                item.setBackground(3, bg_color)
                
                # Set text color to ensure readability
                text_color = QColor("#333333") if is_primary else QColor("#555555")
                item.setForeground(2, text_color)
                item.setForeground(3, text_color)
                
                # Make font slightly bold to indicate selection
                font = item.font(2)
                font.setBold(True)
                item.setFont(2, font)
                item.setFont(3, font)
                
                break
    
    def _reset_all_item_colors(self):
        """Reset all item colors to default."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            
            # Reset background for PID name and description columns
            item.setBackground(2, QBrush())
            item.setBackground(3, QBrush())
            
            # Reset text color to default
            item.setForeground(2, QBrush())
            item.setForeground(3, QBrush())
            
            # Reset font to normal
            font = item.font(2)
            font.setBold(False)
            item.setFont(2, font)
            item.setFont(3, font)
    
    def clear(self):
        """Reset all controls to default values."""
        self._clear_all_selections()
