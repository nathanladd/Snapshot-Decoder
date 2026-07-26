"""
Chart buttons panel: a "Quick" row of built-in charts and a "Mine" row of
My Charts, in one fixed-height group box.

Both rows are single-line and never scroll — overflow folds into a trailing "▾"
menu (see ChartButtonRow) — so the panel keeps the same height it had as a
2-row grid of built-ins. Within each row, most-used charts sort leftmost
(ChartUsageStore), so the ▾ menu only ever holds charts this user ignores.
"""

from typing import Optional, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QToolButton, QMenu
)
from PySide6.QtCore import Signal, Qt

from domain.snaptypes import SnapType
from domain.constants import BUTTONS_BY_TYPE, REFERENCE_CHARTS_BY_TYPE
from domain.snapshot import Snapshot
from domain.chart_usage import ChartUsageStore

from .chart_button_row import ChartButtonRow, make_chart_button, BUTTON_HEIGHT
from .my_charts_widget import MyChartsWidget

_REFERENCE_STYLE = """
    QToolButton {
        background-color: #FFD700;
        border: 2px solid #FFA500;
        border-radius: 4px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: bold;
    }
    QToolButton::menu-indicator { image: none; width: 0px; }
"""


class QuickChartPanel(QWidget):
    """Two-row chart panel: built-in quick charts above, My Charts below."""

    # Emitted for any chart click in either row (built-in or USER_ id).
    chart_requested = Signal(str)  # action_id

    # Forwarded from the My Charts row's ＋ tile. MainWindow owns the PID panel
    # and axis controls needed to build the definition, so it handles the save.
    save_chart_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons: List[QWidget] = []
        self._reference_button: Optional[QToolButton] = None
        self._current_snapshot_type: Optional[SnapType] = None
        self._usage = ChartUsageStore()
        self._setup_ui()

    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._group = QGroupBox("Charts")
        group_layout = QVBoxLayout(self._group)
        group_layout.setContentsMargins(4, 4, 4, 4)
        group_layout.setSpacing(4)

        # Row 1 — built-in quick charts
        self._quick_row = ChartButtonRow("Quick")
        self._quick_row.overflow_activated.connect(self.chart_requested)
        group_layout.addWidget(self._quick_row)

        # Row 2 — My Charts (reserved: keeps its height even when empty)
        self.my_charts = MyChartsWidget()
        self.my_charts.chart_requested.connect(self.chart_requested)
        self.my_charts.save_chart_requested.connect(self.save_chart_requested)
        group_layout.addWidget(self.my_charts)

        layout.addWidget(self._group)

        self._show_placeholder()

    def _show_placeholder(self):
        """Show placeholder when no snapshot is loaded."""
        self._clear_buttons()
        self._quick_row.set_placeholder("Load a snapshot to see quick charts")
        self._quick_row.reflow()

    def _clear_buttons(self):
        """Remove all buttons from the quick row."""
        self._quick_row.clear()
        self._buttons.clear()
        self._reference_button = None

    def set_snapshot_type(self, snapshot_type: Optional[SnapType]):
        """Update both rows based on snapshot type."""
        self._build_quick_row(snapshot_type)
        self.my_charts.set_snapshot_type(snapshot_type)

    def _build_quick_row(self, snapshot_type: Optional[SnapType]):
        """Rebuild row 1 (built-in quick charts) for this snapshot type."""
        self._clear_buttons()
        self._current_snapshot_type = snapshot_type

        if snapshot_type is None or snapshot_type == SnapType.EMPTY:
            self._show_placeholder()
            return

        # Reference charts stay pinned leftmost, outside the usage sort.
        self._add_reference_button_if_available(snapshot_type)

        buttons_config = BUTTONS_BY_TYPE.get(snapshot_type, [])

        if not buttons_config:
            self._quick_row.set_placeholder("No quick charts for this type")
            self._quick_row.reflow()
            return

        # Most-used first; declared order breaks ties, so a user with no
        # history sees exactly the order defined in BUTTONS_BY_TYPE.
        ordered = sorted(
            enumerate(buttons_config),
            key=lambda pair: self._usage.order_key(pair[1][1], pair[0]),
        )

        for _, (name, action_id, tooltip) in ordered:
            btn = make_chart_button(name, action_id, tooltip)
            btn.clicked.connect(self._on_button_clicked)
            self._quick_row.add_item(btn)
            self._buttons.append(btn)

        self._quick_row.reflow()

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

        self._reference_button = QToolButton()
        self._reference_button.setText("Reference ▾")
        self._reference_button.setToolTip("Reference charts")
        self._reference_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._reference_button.setPopupMode(QToolButton.InstantPopup)
        self._reference_button.setStyleSheet(_REFERENCE_STYLE)
        self._reference_button.setFixedHeight(BUTTON_HEIGHT)

        reference_menu = QMenu(self._reference_button)
        for name, action_id, tooltip in REFERENCE_CHARTS_BY_TYPE[snapshot_type]:
            action = reference_menu.addAction(name)
            action.setToolTip(tooltip)
            action.triggered.connect(
                lambda checked, aid=action_id: self.chart_requested.emit(aid)
            )
        self._reference_button.setMenu(reference_menu)

        self._quick_row.add_pinned(self._reference_button)

    def set_snapshot(self, snapshot: Optional[Snapshot]):
        """Update both rows, disabling charts that require missing systems."""
        if snapshot is None:
            self._build_quick_row(None)
            self.my_charts.set_snapshot(None)
            return

        self._build_quick_row(snapshot.snapshot_type)

        # Disable buttons whose required systems are absent
        if not snapshot.has_air_throttle:
            self._set_button_enabled("V2_THROTTLE_VALVE", False)

        self.my_charts.set_snapshot(snapshot)

    def _set_button_enabled(self, action_id: str, enabled: bool):
        """Enable or disable a button by its action_id."""
        for btn in self._buttons:
            if btn.property("action_id") == action_id:
                btn.setEnabled(enabled)
                break

    def clear(self):
        """Clear the panel."""
        self._build_quick_row(None)
        self.my_charts.clear()
