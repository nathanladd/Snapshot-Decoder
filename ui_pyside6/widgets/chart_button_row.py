"""
One fixed-height row of chart buttons with a trailing overflow menu.

Used twice by the quick-chart panel: a "Quick" row of built-in charts and a
"Mine" row of My Charts. The row never scrolls and never changes height — a
scrollbar inside a ~34px row would eat the vertical space the two-row layout
exists to protect — so anything that doesn't fit folds into a trailing "▾"
menu instead. Leading pinned widgets (Reference Charts, the ＋ tile) are never
folded away.
"""

from typing import List, Optional, Sequence

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QToolButton, QMenu, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QSize
from PySide6.QtGui import QFontMetrics

LABEL_WIDTH = 48
ROW_HEIGHT = 34
BUTTON_HEIGHT = 26
BUTTON_MAX_WIDTH = 96
BUTTON_SPACING = 4
OVERFLOW_WIDTH = 28

_ROW_LABEL_STYLE = "color: #888; font-size: 9px; font-weight: bold;"
_PLACEHOLDER_STYLE = "color: #999; font-style: italic; font-size: 11px;"
_OVERFLOW_STYLE = """
    QToolButton {
        border: 1px solid #C0C0C0;
        border-radius: 3px;
        background-color: #F0F0F0;
        font-size: 11px;
        font-weight: bold;
    }
    QToolButton:hover { background-color: #E0E0E0; border: 1px solid #0078d4; }
    QToolButton::menu-indicator { image: none; width: 0px; }
"""


def plan_row_split(
    widths: Sequence[int],
    available: int,
    overflow_width: int = OVERFLOW_WIDTH,
    spacing: int = BUTTON_SPACING,
    pinned: int = 0,
) -> int:
    """How many leading items fit in `available` px; the rest go to the ▾ menu.

    Pure geometry, kept free of Qt so the reflow rule can be unit-tested.
    Returns the number of visible items. Pinned items lead the row and are
    always counted visible even if the row is too narrow for them.
    """
    count = len(widths)
    if count == 0:
        return 0

    total = sum(widths) + spacing * (count - 1)
    if total <= available:
        return count

    # Something overflows, so the ▾ button needs room of its own.
    budget = available - overflow_width - spacing
    used = 0
    visible = 0
    for i, width in enumerate(widths):
        needed = width if visible == 0 else width + spacing
        if i < pinned or used + needed <= budget:
            used += needed
            visible += 1
        else:
            break

    return max(visible, min(pinned, count))


def make_chart_button(
    text: str,
    action_id: str,
    tooltip: str = "",
    style: str = "",
    checkable: bool = False,
) -> QPushButton:
    """A row-sized chart button, text elided to the row's button width cap."""
    btn = QPushButton()
    btn.setProperty("action_id", action_id)
    btn.setProperty("full_text", text)
    btn.setFixedHeight(BUTTON_HEIGHT)
    btn.setMaximumWidth(BUTTON_MAX_WIDTH)
    btn.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
    btn.setCheckable(checkable)
    if style:
        btn.setStyleSheet(style)

    metrics = QFontMetrics(btn.font())
    elided = metrics.elidedText(text, Qt.TextElideMode.ElideRight, BUTTON_MAX_WIDTH - 20)
    btn.setText(elided)
    btn.setToolTip(tooltip or text)
    return btn


class ChartButtonRow(QWidget):
    """A labelled, fixed-height row of chart buttons that folds its overflow."""

    # Emitted when an overflowed chart is picked from the ▾ menu. Visible
    # buttons keep their own clicked wiring, owned by whoever created them.
    overflow_activated = Signal(str)  # action_id

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self._pinned: List[QWidget] = []
        self._items: List[QWidget] = []
        self._placeholder: Optional[QLabel] = None
        self._reflowing = False

        self.setFixedHeight(ROW_HEIGHT)
        # Take whatever width the panel gives. Without this the layout's
        # minimum width is the sum of every button, so the row can never get
        # narrower than its contents and the overflow menu would never engage.
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(BUTTON_SPACING)

        self._label = QLabel(label)
        self._label.setFixedWidth(LABEL_WIDTH)
        self._label.setStyleSheet(_ROW_LABEL_STYLE)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self._layout.addWidget(self._label)

        self._layout.addStretch(1)

        self._overflow_btn = QToolButton()
        self._overflow_btn.setText("▾")
        self._overflow_btn.setToolTip("More charts")
        self._overflow_btn.setFixedSize(OVERFLOW_WIDTH, BUTTON_HEIGHT)
        self._overflow_btn.setPopupMode(QToolButton.InstantPopup)
        self._overflow_btn.setStyleSheet(_OVERFLOW_STYLE)
        self._overflow_btn.setMenu(QMenu(self._overflow_btn))
        self._overflow_btn.hide()
        self._layout.addWidget(self._overflow_btn)

    # ------------------------------------------------------------------
    # Content
    # ------------------------------------------------------------------
    def clear(self):
        """Remove every pinned widget, item and placeholder."""
        for widget in self._pinned + self._items:
            self._layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
        self._pinned.clear()
        self._items.clear()
        self._clear_placeholder()
        self._overflow_btn.hide()

    def add_pinned(self, widget: QWidget):
        """Add a leading widget that is never folded into the ▾ menu."""
        widget.setParent(self)
        # Pinned widgets sit after the label, before any items.
        index = 1 + len(self._pinned)
        self._layout.insertWidget(index, widget)
        self._pinned.append(widget)

    def add_item(self, widget: QWidget):
        """Add a chart widget that may be folded into the ▾ menu when narrow."""
        widget.setParent(self)
        index = 1 + len(self._pinned) + len(self._items)
        self._layout.insertWidget(index, widget)
        self._items.append(widget)

    def set_placeholder(self, text: str):
        """Show grey italic text in place of chart buttons (row keeps its height)."""
        self._clear_placeholder()
        self._placeholder = QLabel(text)
        self._placeholder.setStyleSheet(_PLACEHOLDER_STYLE)
        self._layout.insertWidget(1 + len(self._pinned) + len(self._items), self._placeholder)

    def _clear_placeholder(self):
        if self._placeholder is not None:
            self._layout.removeWidget(self._placeholder)
            self._placeholder.setParent(None)
            self._placeholder.deleteLater()
            self._placeholder = None

    def items(self) -> List[QWidget]:
        return list(self._items)

    def minimumSizeHint(self) -> QSize:
        """Zero minimum width — the row folds its overflow instead of forcing
        the panel (and the window) wider than the user sized it."""
        return QSize(0, ROW_HEIGHT)

    def sizeHint(self) -> QSize:
        return QSize(0, ROW_HEIGHT)

    # ------------------------------------------------------------------
    # Reflow
    # ------------------------------------------------------------------
    def reflow(self):
        """Show as many items as fit; fold the rest into the ▾ menu."""
        if self._reflowing:
            return
        self._reflowing = True
        try:
            self._do_reflow()
        finally:
            self._reflowing = False

    def _do_reflow(self):
        widgets = self._pinned + self._items
        if not widgets:
            self._overflow_btn.hide()
            return

        placeholder_width = (
            self._placeholder.sizeHint().width() + BUTTON_SPACING
            if self._placeholder is not None else 0
        )
        available = self.width() - LABEL_WIDTH - BUTTON_SPACING - placeholder_width
        widths = [min(w.sizeHint().width(), w.maximumWidth()) for w in widgets]
        visible = plan_row_split(widths, available, pinned=len(self._pinned))

        for i, widget in enumerate(widgets):
            widget.setVisible(i < visible)

        hidden = widgets[visible:]
        menu = self._overflow_btn.menu()
        menu.clear()
        for widget in hidden:
            action_id = widget.property("action_id")
            text = widget.property("full_text") or widget.property("action_id") or ""
            action = menu.addAction(str(text))
            action.setToolTip(widget.toolTip())
            action.setEnabled(widget.isEnabled())
            action.triggered.connect(
                lambda checked=False, aid=action_id: self.overflow_activated.emit(str(aid))
            )

        self._overflow_btn.setVisible(bool(hidden))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.reflow()
