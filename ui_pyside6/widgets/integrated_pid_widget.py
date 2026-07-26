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
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QBrush

from domain.snapshot import Snapshot
from rendering.color_manager import ColorManager


class IntegratedPidWidget(QWidget):
    """Integrated PID selection widget with search and checkbox functionality."""
    
    # Signal emitted when PID selection changes
    pids_changed = Signal()

    _CHECKBOX_STYLE = """
        QCheckBox {
            spacing: 0px;
            margin: 0px;
            padding: 0px;
        }
        QCheckBox::indicator {
            width: 12px;
            height: 12px;
            border: 1px solid #333333;
            border-radius: 2px;
            background-color: white;
        }
        QCheckBox::indicator:hover {
            border: 1px solid #0078d4;
            background-color: #f0f8ff;
        }
        QCheckBox::indicator:checked {
            background-color: #28a745;
            border: 1px solid #28a745;
        }
        QCheckBox::indicator:checked:hover {
            background-color: #218838;
            border: 1px solid #218838;
        }
    """
    
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

        # Persistent separator row (created once per snapshot load)
        self._separator_item: Optional[QTreeWidgetItem] = None

        self._filter_timer = QTimer(self)
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(150)
        self._filter_timer.timeout.connect(self._filter_descriptions)
        
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
        pid_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        pid_layout = QVBoxLayout(pid_group)
        pid_layout.setSpacing(4)
        
        # Search box at the top
        search_frame = QWidget()
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(QLabel("Filter Descriptions:"))
        
        self.search_entry = QLineEdit()
        self.search_entry.textChanged.connect(self._schedule_filter)
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
        
        # Tree widget for PID info — column 5 is a hidden sort key
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Left", "Right", "Description", "PID Name", "Unit", "_sort"])
        
        # Configure tree columns
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)       # Primary checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)       # Secondary checkbox
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Description
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # PID name
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)  # Unit
        
        header.resizeSection(0, 40)   # Primary checkbox column (checkbox width + margins)
        header.resizeSection(1, 40)   # Secondary checkbox column (checkbox width + margins)
        header.resizeSection(2, 300)  # Description column
        header.resizeSection(3, 150)  # PID column
        header.resizeSection(4, 90)   # Unit column
        
        # Align checkbox columns to the left
        self.tree.header().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)

        # Hide the sort key column
        self.tree.setColumnHidden(5, True)
        
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
            self._separator_item = None
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
        self._separator_item = None
        
        if not hasattr(self, 'pid_info'):
            return
        
        for pid, data in self.pid_info.items():
            item = QTreeWidgetItem(self.tree)
            item.setText(3, pid)                    # PID Name (column 3)
            item.setText(2, data.get("Description", ""))  # Description (column 2)
            item.setText(4, data.get("Unit", ""))    # Unit (column 4)
            
            # Store the full PID data for later use
            item.setData(3, Qt.ItemDataRole.UserRole, pid)  # Store PID in column 3
            
            # Store item reference for color updates
            item.setData(2, Qt.ItemDataRole.UserRole, item)  # Store item itself for color updates
            
            # Create checkboxes — these persist for the lifetime of the tree
            primary_cb = self._create_checkbox(pid, is_primary=True)
            secondary_cb = self._create_checkbox(pid, is_primary=False)
            self.tree.setItemWidget(item, 0, primary_cb)
            self.tree.setItemWidget(item, 1, secondary_cb)

        # Create the persistent separator row (always exists, shown/hidden as needed)
        self._separator_item = QTreeWidgetItem(self.tree)
        self._separator_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self._separator_item.setText(2, "────────")
        self._separator_item.setHidden(True)

        # Apply initial filter + grouping
        self._filter_descriptions()

    def _create_checkbox(self, pid: str, is_primary: bool) -> QCheckBox:
        """Create a styled checkbox wired to the appropriate handler."""
        cb = QCheckBox()
        cb.setStyleSheet(self._CHECKBOX_STYLE)
        if is_primary:
            cb.stateChanged.connect(
                lambda state, p=pid: self._on_primary_checkbox_changed(state, p, cb)
            )
        else:
            cb.stateChanged.connect(
                lambda state, p=pid: self._on_secondary_checkbox_changed(state, p, cb)
            )
        return cb

    # ------------------------------------------------------------------
    # Grouping — uses a hidden sort column so items are reordered IN PLACE
    # by QTreeWidget.sortItems().  No items are removed/re-added, so
    # checkbox widgets are never destroyed.
    # ------------------------------------------------------------------

    def _get_group_rank(self, pid: str) -> int:
        """Return ordering group rank for a PID row."""
        if pid in self.current_primary_pids:
            return 0
        if pid in self.current_secondary_pids:
            return 1
        return 2

    def _apply_grouping(self):
        """Assign sort keys and re-sort items in place (no widget destruction)."""
        has_selected_visible = False
        has_unselected_visible = False

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is self._separator_item:
                continue
            pid = item.text(3)
            rank = self._get_group_rank(pid)
            item.setText(5, f"{rank}_{pid.lower()}")

            if not item.isHidden():
                if rank < 2:
                    has_selected_visible = True
                else:
                    has_unselected_visible = True

        # Place separator between selected (0_, 1_) and unselected (2_)
        if self._separator_item is not None:
            self._separator_item.setText(5, "1~")  # '~' sorts after all lowercase
            self._separator_item.setHidden(
                not (has_selected_visible and has_unselected_visible)
            )

        self.tree.sortItems(5, Qt.SortOrder.AscendingOrder)

    # ------------------------------------------------------------------
    # Search / filter
    # ------------------------------------------------------------------
    
    def _clear_search(self):
        """Clear the search input and show all PIDs."""
        self.search_entry.clear()

    def _schedule_filter(self):
        """Debounce interactive text filtering to keep the UI responsive."""
        self._filter_timer.start()
    
    def _filter_descriptions(self):
        """Filter tree items based on search text, then regroup."""
        search_term = self.search_entry.text().strip().lower()
        
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is self._separator_item:
                continue

            description = item.text(2).lower()
            pid_name = item.text(3)
            pid_name_lower = pid_name.lower()
            is_selected = (
                pid_name in self.current_primary_pids
                or pid_name in self.current_secondary_pids
            )
            matches_filter = search_term in description or search_term in pid_name_lower
            
            # Keep selected PIDs visible even when they do not match the filter.
            item.setHidden(not matches_filter and not is_selected)

        self._apply_grouping()

    # ------------------------------------------------------------------
    # Checkbox handlers
    # ------------------------------------------------------------------
    
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

        self._apply_grouping()
        
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

        self._apply_grouping()
        
        # Emit signal to update chart
        self.pids_changed.emit()
    
    def _get_primary_checkbox(self, pid: str) -> QCheckBox:
        """Get the primary checkbox for a PID."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is self._separator_item:
                continue
            if item.text(3) == pid:
                cb = self.tree.itemWidget(item, 0)
                return cb if isinstance(cb, QCheckBox) else None
        return None
    
    def _get_secondary_checkbox(self, pid: str) -> QCheckBox:
        """Get the secondary checkbox for a PID."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is self._separator_item:
                continue
            if item.text(3) == pid:
                cb = self.tree.itemWidget(item, 1)
                return cb if isinstance(cb, QCheckBox) else None
        return None
    
    def update_chart_pids(self, primary_pids: list, secondary_pids: list):
        """Update the current chart PID selections."""
        self.current_primary_pids = set(primary_pids)
        self.current_secondary_pids = set(secondary_pids)
        self._primary_pids = list(primary_pids)
        self._secondary_pids = list(secondary_pids)
        self._sync_checkboxes()
        self._apply_grouping()
    
    def _sync_checkboxes(self):
        """Sync checkboxes with current chart PIDs."""
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item is self._separator_item:
                continue
            pid = item.text(3)
            
            primary_cb = self.tree.itemWidget(item, 0)
            secondary_cb = self.tree.itemWidget(item, 1)
            
            if isinstance(primary_cb, QCheckBox) and isinstance(secondary_cb, QCheckBox):
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
        self._apply_grouping()
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
        self._apply_grouping()
        
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
            if item is self._separator_item:
                continue
            if item.text(3) == pid:  # Check PID name column (column 3)
                # Apply subtle background color to the description column
                bg_color = QColor(color)
                bg_color.setAlpha(30)  # Very subtle transparency (30/255)
                
                # Apply to description column (column 2) - main highlight
                item.setBackground(2, bg_color)
                
                # Also apply to PID name column (column 3) for consistency
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
            if item is self._separator_item:
                continue
            
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
        self.set_snapshot(None)
        self.search_entry.clear()
