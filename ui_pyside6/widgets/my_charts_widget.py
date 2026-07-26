"""
My Charts row: user-saved chart templates as a single row of buttons inside the
chart panel, led by a pinned ＋ tile.

There is no CRUD toolbar — the row is ~26px tall and a four-button toolbar
would crowd out the charts themselves. Management lives on a right-click menu
(Edit / Duplicate / Delete) on each chart button, and the ＋ tile saves whatever
is currently on the canvas. The row keeps its height in every state, including
"no charts yet", so nothing below it shifts as charts come and go.
"""

import copy
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QMessageBox, QButtonGroup, QMenu
)
from PySide6.QtCore import Signal, Qt

from domain.snaptypes import SnapType
from domain.snapshot import Snapshot
from domain.user_charts import UserChartDef, UserChartStore
from domain.chart_usage import ChartUsageStore

from .chart_button_row import ChartButtonRow, make_chart_button, BUTTON_HEIGHT

_ADD_BTN_STYLE = """
    QPushButton {
        background-color: #E8F5E9;
        border: 2px solid #43A047;
        border-radius: 4px;
        font-weight: bold;
        font-size: 12px;
    }
    QPushButton:hover:enabled {
        background-color: #C8E6C9;
    }
    QPushButton:disabled {
        background-color: #F0F0F0;
        border: 2px solid #C0C0C0;
        color: #888888;
    }
"""

_CHART_BTN_STYLE = """
    QPushButton {
        background-color: #EDE7F6;
        border: 2px solid #7E57C2;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
    }
    QPushButton:hover:enabled {
        background-color: #D1C4E9;
    }
    QPushButton:checked {
        background-color: #B39DDB;
        border: 2px solid #4527A0;
    }
    QPushButton:disabled {
        background-color: #F0F0F0;
        border: 2px solid #C0C0C0;
        color: #888888;
    }
"""

_CHART_BTN_TOOLTIP = "Click to load · Right-click to edit, duplicate or delete"


class MyChartsWidget(QWidget):
    """User-saved chart templates as a single labelled row with a ＋ tile."""

    # Signal emitted when a My Chart is loaded onto the canvas
    chart_requested = Signal(str)  # action_id

    # Signal emitted when "＋" is clicked to save the current canvas selection
    # as a My Chart. MainWindow owns the PID panel / axis controls needed to
    # build the definition, so it handles this end-to-end.
    save_chart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._store = UserChartStore()
        self._usage = ChartUsageStore()
        self._current_snapshot_type: Optional[SnapType] = None
        self._snapshot: Optional[Snapshot] = None
        self._chart_buttons: List[QPushButton] = []
        self._add_btn: Optional[QPushButton] = None
        self._save_enabled = False
        self._save_tooltip = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._row = ChartButtonRow("Mine")
        self._row.overflow_activated.connect(self._on_overflow_activated)
        layout.addWidget(self._row)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self._on_chart_button_clicked)

        self._render_user_charts()

    # ------------------------------------------------------------------
    # Snapshot wiring
    # ------------------------------------------------------------------

    def set_snapshot_type(self, snapshot_type: Optional[SnapType]):
        """Update the chart row for the given snapshot type."""
        self._current_snapshot_type = snapshot_type
        self._render_user_charts()

    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the row based on snapshot, disabling charts with no matching PIDs."""
        self._snapshot = snapshot
        self.set_snapshot_type(snapshot.snapshot_type if snapshot else None)

    def set_save_enabled(self, enabled: bool, tooltip: str = ""):
        """Enable/disable the ＋ tile (no PIDs selected on the canvas => disabled)."""
        self._save_enabled = enabled
        self._save_tooltip = tooltip
        self._apply_save_state()

    def _apply_save_state(self):
        if self._add_btn is None:
            return
        self._add_btn.setEnabled(self._save_enabled)
        self._add_btn.setToolTip(
            self._save_tooltip if self._save_tooltip else
            ("Save the current chart as a My Chart" if self._save_enabled
             else "Select PIDs to build a chart, then save it")
        )

    def reload_user_charts(self):
        """Re-fetch from the store and rebuild the chart row."""
        self._render_user_charts()

    def clear(self):
        """Clear the row."""
        self._snapshot = None
        self.set_snapshot_type(None)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render_user_charts(self):
        """Rebuild the row: pinned ＋ tile, then chart buttons, most-used first."""
        for btn in self._chart_buttons:
            self._button_group.removeButton(btn)
        self._chart_buttons.clear()
        self._row.clear()

        self._add_btn = QPushButton("＋")
        self._add_btn.setFixedSize(30, BUTTON_HEIGHT)
        self._add_btn.setStyleSheet(_ADD_BTN_STYLE)
        self._add_btn.clicked.connect(self.save_chart_requested.emit)
        self._row.add_pinned(self._add_btn)
        self._apply_save_state()

        if self._current_snapshot_type is None or self._current_snapshot_type == SnapType.EMPTY:
            self._add_btn.setEnabled(False)
            self._row.set_placeholder("Load a snapshot to see My Charts")
            self._row.reflow()
            return

        charts = self._store.for_type(self._current_snapshot_type)
        if not charts:
            self._row.set_placeholder("Build a chart, then click ＋ to save it")
            self._row.reflow()
            return

        # Most-used first; creation order breaks ties.
        ordered = sorted(
            enumerate(charts),
            key=lambda pair: self._usage.order_key(pair[1].action_id, pair[0]),
        )

        for _, chart_def in ordered:
            btn = make_chart_button(
                chart_def.title,
                chart_def.action_id,
                tooltip=f"{chart_def.title}\n{_CHART_BTN_TOOLTIP}",
                style=_CHART_BTN_STYLE,
                checkable=True,
            )

            if not self._chart_has_any_pid(chart_def):
                btn.setEnabled(False)
                btn.setToolTip("No matching PIDs in this snapshot.")

            btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, b=btn: self._show_context_menu(b, pos)
            )

            self._button_group.addButton(btn)
            self._row.add_item(btn)
            self._chart_buttons.append(btn)

        self._row.reflow()

    def _chart_has_any_pid(self, chart_def: UserChartDef) -> bool:
        """True if at least one of the chart's PIDs exists in the current snapshot."""
        if self._snapshot is None or self._snapshot.snapshot is None:
            return False
        columns_lower = {str(c).casefold() for c in self._snapshot.snapshot.columns}
        for pid in list(chart_def.primary_pids) + list(chart_def.secondary_pids):
            if str(pid).casefold() in columns_lower:
                return True
        return False

    # ------------------------------------------------------------------
    # Selection + CRUD
    # ------------------------------------------------------------------

    def _on_chart_button_clicked(self, btn: QPushButton):
        action_id = btn.property("action_id")
        if action_id:
            self.chart_requested.emit(action_id)

    def _on_overflow_activated(self, action_id: str):
        """A chart picked from the row's ▾ menu."""
        if action_id:
            self.chart_requested.emit(action_id)

    def _show_context_menu(self, btn: QPushButton, pos):
        """Right-click menu on a My Chart button: Edit / Duplicate / Delete."""
        action_id = btn.property("action_id")
        if not action_id:
            return

        menu = QMenu(self)
        edit_action = menu.addAction("Edit")
        edit_action.setToolTip("Load this chart onto the canvas to modify it")
        duplicate_action = menu.addAction("Duplicate")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")

        chosen = menu.exec(btn.mapToGlobal(pos))
        if chosen is edit_action:
            self.chart_requested.emit(action_id)
        elif chosen is duplicate_action:
            self._duplicate_chart(action_id)
        elif chosen is delete_action:
            self._delete_chart(action_id)

    def _duplicate_chart(self, action_id: str):
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

    def _delete_chart(self, action_id: str):
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
        self._usage.forget(action_id)
        self.reload_user_charts()
