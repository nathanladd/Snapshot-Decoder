"""
Quick chart buttons panel widget.
"""

from typing import Optional, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QGroupBox,
    QScrollArea, QSizePolicy, QToolButton, QMenu, QMessageBox
)
from PySide6.QtCore import Signal, Qt

from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE, REFERENCE_CHARTS_BY_TYPE
from domain.snapshot import Snapshot
from domain.user_charts import UserChartDef, UserChartStore

_MY_CHARTS_COLUMNS = 4

_USER_CHART_STYLE = """
    QPushButton {
        background-color: #EDE7F6;
        border: 2px solid #7E57C2;
        border-radius: 4px;
        padding: 4px 4px;
    }
    QPushButton:hover {
        background-color: #D1C4E9;
    }
    QPushButton:disabled {
        background-color: #F0F0F0;
        border: 2px solid #C0C0C0;
        color: #888888;
    }
"""

_SAVE_TILE_STYLE = """
    QPushButton {
        background-color: #E8F5E9;
        border: 2px solid #43A047;
        border-radius: 4px;
        font-weight: bold;
        padding: 4px 4px;
    }
    QPushButton:hover {
        background-color: #C8E6C9;
    }
    QPushButton:disabled {
        background-color: #F0F0F0;
        border: 2px solid #C0C0C0;
        color: #888888;
    }
"""


class QuickChartPanel(QWidget):
    """Panel with quick chart buttons based on snapshot type."""

    # Signal emitted when a quick chart is requested
    chart_requested = Signal(str)  # action_id

    # Signal emitted when the "+" tile is clicked to save the current canvas
    # selection as a My Chart. MainWindow owns the PID panel / axis controls
    # needed to build the definition, so it handles this end-to-end.
    save_chart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: List[QPushButton] = []
        self._reference_button: Optional[QToolButton] = None
        self._current_snapshot_type: Optional[SnapType] = None
        self._snapshot: Optional[Snapshot] = None
        self._user_chart_buttons: List[QPushButton] = []
        self._save_tile: Optional[QPushButton] = None
        self._store = UserChartStore()
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

        # My Charts — user-saved templates. Own labeled group + scroll so it
        # can grow independently of the capped built-in grid.
        self._my_charts_group = QGroupBox("My Charts")
        my_charts_layout = QVBoxLayout(self._my_charts_group)
        my_charts_layout.setContentsMargins(4, 4, 4, 4)

        my_charts_scroll = QScrollArea()
        my_charts_scroll.setWidgetResizable(True)
        my_charts_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        my_charts_scroll.setMaximumHeight(110)

        self._my_charts_container = QWidget()
        self._my_charts_layout = QGridLayout(self._my_charts_container)
        self._my_charts_layout.setSpacing(4)
        self._my_charts_layout.setContentsMargins(0, 0, 0, 0)

        my_charts_scroll.setWidget(self._my_charts_container)
        my_charts_layout.addWidget(my_charts_scroll)

        layout.addWidget(self._my_charts_group)
        self._my_charts_group.setVisible(False)

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
            self._my_charts_group.setVisible(False)
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
        else:
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

        self._my_charts_group.setVisible(True)
        self._render_user_charts()

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

    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update buttons based on snapshot, disabling charts that require missing systems."""
        self._snapshot = snapshot
        if snapshot is None:
            self.set_snapshot_type(None)
            return

        self.set_snapshot_type(snapshot.snapshot_type)

        # Disable buttons whose required systems are absent
        if not snapshot.has_air_throttle:
            self._set_button_enabled("V2_THROTTLE_VALVE", False)

    def _set_button_enabled(self, action_id: str, enabled: bool):
        """Enable or disable a button by its action_id."""
        for btn in self._buttons:
            if btn.property("action_id") == action_id:
                btn.setEnabled(enabled)
                break

    # ------------------------------------------------------------------
    # My Charts — render, save tile, CRUD
    # ------------------------------------------------------------------

    def reload_user_charts(self):
        """Re-fetch from the store and rebuild the My Charts section."""
        self._render_user_charts()

    def _clear_user_chart_buttons(self):
        """Remove My Charts buttons and the save tile from the layout."""
        for btn in self._user_chart_buttons:
            self._my_charts_layout.removeWidget(btn)
            btn.deleteLater()
        self._user_chart_buttons.clear()

        if self._save_tile:
            self._my_charts_layout.removeWidget(self._save_tile)
            self._save_tile.deleteLater()
            self._save_tile = None

    def _render_user_charts(self):
        """Rebuild the My Charts row: the ＋ tile plus one button per matching chart."""
        self._clear_user_chart_buttons()

        if self._current_snapshot_type is None or self._current_snapshot_type == SnapType.EMPTY:
            return

        self._save_tile = QPushButton("＋")
        self._save_tile.setToolTip("Save the current chart as a My Chart")
        self._save_tile.setStyleSheet(_SAVE_TILE_STYLE)
        self._save_tile.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._save_tile.setFixedWidth(32)
        self._save_tile.setEnabled(False)
        self._save_tile.clicked.connect(self.save_chart_requested.emit)
        self._my_charts_layout.addWidget(self._save_tile, 0, 0)

        charts = self._store.for_type(self._current_snapshot_type)
        for i, chart_def in enumerate(charts):
            btn = QPushButton(chart_def.title)
            btn.setToolTip(chart_def.title)
            btn.setProperty("action_id", chart_def.action_id)
            btn.setStyleSheet(_USER_CHART_STYLE)
            btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            btn.setMaximumWidth(140)
            btn.clicked.connect(self._on_button_clicked)
            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, b=btn, aid=chart_def.action_id: self._show_user_chart_menu(b, pos, aid)
            )

            if not self._chart_has_any_pid(chart_def):
                btn.setEnabled(False)
                btn.setToolTip("No matching PIDs in this snapshot.")

            row = (i + 1) // _MY_CHARTS_COLUMNS
            col = (i + 1) % _MY_CHARTS_COLUMNS
            self._my_charts_layout.addWidget(btn, row, col)
            self._user_chart_buttons.append(btn)

    def _chart_has_any_pid(self, chart_def: UserChartDef) -> bool:
        """True if at least one of the chart's PIDs exists in the current snapshot."""
        if self._snapshot is None or self._snapshot.snapshot is None:
            return False
        columns_lower = {str(c).casefold() for c in self._snapshot.snapshot.columns}
        for pid in list(chart_def.primary_pids) + list(chart_def.secondary_pids):
            if str(pid).casefold() in columns_lower:
                return True
        return False

    def set_save_enabled(self, enabled: bool, tooltip: str = ""):
        """Enable/disable the ＋ tile (no PIDs selected on the canvas => disabled)."""
        if not self._save_tile:
            return
        self._save_tile.setEnabled(enabled)
        self._save_tile.setToolTip(
            tooltip if tooltip else
            ("Save the current chart as a My Chart" if enabled
             else "Select PIDs to build a chart, then save it")
        )

    def _show_user_chart_menu(self, btn: QPushButton, pos, action_id: str):
        """Right-click context menu: Edit / Duplicate / Delete."""
        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        duplicate_action = menu.addAction("Duplicate")
        delete_action = menu.addAction("Delete")

        chosen = menu.exec(btn.mapToGlobal(pos))
        if chosen is edit_action:
            self.chart_requested.emit(action_id)
        elif chosen is duplicate_action:
            self._duplicate_user_chart(action_id)
        elif chosen is delete_action:
            self._delete_user_chart(action_id)

    def _duplicate_user_chart(self, action_id: str):
        """Clone a My Chart with a new id and a disambiguated title."""
        import copy
        from datetime import datetime
        from uuid import uuid4

        original = self._store.get(action_id)
        if not original:
            return

        base_title = f"{original.title} copy"
        title = base_title
        suffix = 2
        while not self._store.is_title_available(title):
            title = f"{base_title} {suffix}"
            suffix += 1

        clone = copy.deepcopy(original)
        clone.action_id = "USER_" + uuid4().hex
        clone.title = title
        now = datetime.now().isoformat()
        clone.created = now
        clone.modified = now

        self._store.add(clone)
        self.reload_user_charts()

    def _delete_user_chart(self, action_id: str):
        """Confirm, then delete a My Chart and rebuild the panel."""
        chart_def = self._store.get(action_id)
        title = chart_def.title if chart_def else action_id

        reply = QMessageBox.question(
            self,
            "Delete My Chart",
            f"Delete '{title}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._store.delete(action_id)
        self.reload_user_charts()

    def clear(self):
        """Clear the panel."""
        self._snapshot = None
        self.set_snapshot_type(None)
