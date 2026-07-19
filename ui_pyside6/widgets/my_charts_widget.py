"""
My Charts panel content widget: user-saved chart templates with a CRUD
toolbar and a vertically stacked list of chart buttons.
"""

import copy
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea,
    QSizePolicy, QLabel, QMessageBox, QButtonGroup
)
from PySide6.QtCore import Signal, Qt

from domain.snaptypes import SnapType
from domain.snapshot import Snapshot
from domain.user_charts import UserChartDef, UserChartStore

_TOOLBAR_BTN_STYLE = """
    QPushButton {
        border: 1px solid #C0C0C0;
        border-radius: 3px;
        padding: 4px 4px;
        background-color: #F0F0F0;
        font-size: 11px;
    }
    QPushButton:hover:enabled {
        background-color: #E0E0E0;
        border: 1px solid #0078d4;
    }
    QPushButton:pressed:enabled {
        background-color: #D0D0D0;
    }
    QPushButton:disabled {
        color: #AAAAAA;
    }
"""

_ADD_BTN_STYLE = """
    QPushButton {
        background-color: #E8F5E9;
        border: 2px solid #43A047;
        border-radius: 4px;
        font-weight: bold;
        padding: 4px 4px;
        font-size: 11px;
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

_DELETE_BTN_STYLE = """
    QPushButton {
        border: 1px solid #C0C0C0;
        border-radius: 3px;
        padding: 4px 4px;
        background-color: #FFF0F0;
        font-size: 11px;
        color: #A40000;
    }
    QPushButton:hover:enabled {
        background-color: #FFD0D0;
        border: 1px solid #d40000;
    }
    QPushButton:pressed:enabled {
        background-color: #FFB8B8;
    }
    QPushButton:disabled {
        background-color: #F0F0F0;
        border: 1px solid #C0C0C0;
        color: #AAAAAA;
    }
"""

_CHART_BTN_STYLE = """
    QPushButton {
        background-color: #EDE7F6;
        border: 2px solid #7E57C2;
        border-radius: 4px;
        padding: 5px 8px;
        text-align: left;
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


class MyChartsWidget(QWidget):
    """User-saved chart templates: CRUD toolbar + vertical chart list."""

    # Signal emitted when a My Chart is loaded onto the canvas
    chart_requested = Signal(str)  # action_id

    # Signal emitted when "＋ Add" is clicked to save the current canvas
    # selection as a My Chart. MainWindow owns the PID panel / axis controls
    # needed to build the definition, so it handles this end-to-end.
    save_chart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._store = UserChartStore()
        self._current_snapshot_type: Optional[SnapType] = None
        self._snapshot: Optional[Snapshot] = None
        self._chart_buttons: List[QPushButton] = []
        self._selected_action_id: Optional[str] = None
        self._placeholder: Optional[QLabel] = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # CRUD toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)

        self._add_btn = QPushButton("＋ Add")
        self._add_btn.setToolTip("Select PIDs to build a chart, then save it")
        self._add_btn.setStyleSheet(_ADD_BTN_STYLE)
        self._add_btn.setEnabled(False)
        self._add_btn.clicked.connect(self.save_chart_requested.emit)
        toolbar.addWidget(self._add_btn)

        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setToolTip("Load the selected My Chart")
        self._edit_btn.setStyleSheet(_TOOLBAR_BTN_STYLE)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        toolbar.addWidget(self._edit_btn)

        self._duplicate_btn = QPushButton("Duplicate")
        self._duplicate_btn.setToolTip("Duplicate the selected My Chart")
        self._duplicate_btn.setStyleSheet(_TOOLBAR_BTN_STYLE)
        self._duplicate_btn.clicked.connect(self._on_duplicate_clicked)
        toolbar.addWidget(self._duplicate_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setToolTip("Delete the selected My Chart")
        self._delete_btn.setStyleSheet(_DELETE_BTN_STYLE)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        toolbar.addWidget(self._delete_btn)

        layout.addLayout(toolbar)
        self._set_crud_enabled(False)

        # Scrollable vertical list of chart buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(3)
        self._list_layout.addStretch(1)

        scroll.setWidget(self._list_container)
        layout.addWidget(scroll, stretch=1)

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)
        self._button_group.buttonClicked.connect(self._on_chart_button_clicked)

        self._show_placeholder("Load a snapshot to see My Charts")

    # ------------------------------------------------------------------
    # Placeholder handling
    # ------------------------------------------------------------------

    def _show_placeholder(self, text: str):
        self._hide_placeholder()
        self._placeholder = QLabel(text)
        self._placeholder.setWordWrap(True)
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #999; font-style: italic; padding: 8px;")
        self._list_layout.insertWidget(0, self._placeholder)

    def _hide_placeholder(self):
        if self._placeholder:
            self._list_layout.removeWidget(self._placeholder)
            self._placeholder.deleteLater()
            self._placeholder = None

    # ------------------------------------------------------------------
    # Snapshot wiring
    # ------------------------------------------------------------------

    def set_snapshot_type(self, snapshot_type: Optional[SnapType]):
        """Update the chart list for the given snapshot type."""
        self._current_snapshot_type = snapshot_type
        self._render_user_charts()

    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update the chart list based on snapshot, disabling charts with no matching PIDs."""
        self._snapshot = snapshot
        self.set_snapshot_type(snapshot.snapshot_type if snapshot else None)

    def set_save_enabled(self, enabled: bool, tooltip: str = ""):
        """Enable/disable the ＋ Add button (no PIDs selected on the canvas => disabled)."""
        self._add_btn.setEnabled(enabled)
        self._add_btn.setToolTip(
            tooltip if tooltip else
            ("Save the current chart as a My Chart" if enabled
             else "Select PIDs to build a chart, then save it")
        )

    def reload_user_charts(self):
        """Re-fetch from the store and rebuild the chart list."""
        self._render_user_charts()

    def clear(self):
        """Clear the panel."""
        self._snapshot = None
        self.set_snapshot_type(None)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _clear_chart_buttons(self):
        for btn in self._chart_buttons:
            self._button_group.removeButton(btn)
            self._list_layout.removeWidget(btn)
            btn.deleteLater()
        self._chart_buttons.clear()
        self._selected_action_id = None
        self._set_crud_enabled(False)

    def _render_user_charts(self):
        """Rebuild the vertical list of My Charts buttons."""
        self._clear_chart_buttons()
        self._hide_placeholder()

        if self._current_snapshot_type is None or self._current_snapshot_type == SnapType.EMPTY:
            self._show_placeholder("Load a snapshot to see My Charts")
            return

        charts = self._store.for_type(self._current_snapshot_type)
        if not charts:
            self._show_placeholder("No My Charts yet.\nBuild a chart, then click “＋ Add”.")
            return

        for chart_def in charts:
            btn = QPushButton(chart_def.title)
            btn.setToolTip(chart_def.title)
            btn.setProperty("action_id", chart_def.action_id)
            btn.setStyleSheet(_CHART_BTN_STYLE)
            btn.setCheckable(True)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

            if not self._chart_has_any_pid(chart_def):
                btn.setEnabled(False)
                btn.setToolTip("No matching PIDs in this snapshot.")

            self._button_group.addButton(btn)
            self._list_layout.insertWidget(self._list_layout.count() - 1, btn)
            self._chart_buttons.append(btn)

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
    # Selection + CRUD toolbar
    # ------------------------------------------------------------------

    def _set_crud_enabled(self, enabled: bool):
        self._edit_btn.setEnabled(enabled)
        self._duplicate_btn.setEnabled(enabled)
        self._delete_btn.setEnabled(enabled)

    def _on_chart_button_clicked(self, btn: QPushButton):
        action_id = btn.property("action_id")
        if not action_id:
            return
        self._selected_action_id = action_id
        self._set_crud_enabled(True)
        self.chart_requested.emit(action_id)

    def _on_edit_clicked(self):
        if self._selected_action_id:
            self.chart_requested.emit(self._selected_action_id)

    def _on_duplicate_clicked(self):
        if not self._selected_action_id:
            return

        original = self._store.get(self._selected_action_id)
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

    def _on_delete_clicked(self):
        if not self._selected_action_id:
            return

        chart_def = self._store.get(self._selected_action_id)
        title = chart_def.title if chart_def else self._selected_action_id

        reply = QMessageBox.question(
            self,
            "Delete My Chart",
            f"Delete '{title}'? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._store.delete(self._selected_action_id)
        self.reload_user_charts()
