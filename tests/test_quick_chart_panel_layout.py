"""
Layout guards for the two-row chart panel.

The whole point of folding Quick Charts into a single row and hosting My Charts
below it is that the panel does not get taller than the old 2-row grid. These
tests are the cheap guard against a later stylesheet tweak quietly undoing that.
"""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from domain.chart_usage import ChartUsageStore
from domain.snaptypes import SnapType
from domain.user_charts import UserChartStore
from ui_pyside6.widgets.chart_button_row import ROW_HEIGHT
from ui_pyside6.widgets.quick_chart_panel import QuickChartPanel

# The pre-rework panel: QGroupBox title + 4px margins + a 90px scroll area.
PRE_REWORK_HEIGHT = 112


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def panel(qapp, tmp_path, monkeypatch):
    """A panel backed by empty tmp stores, so tests never touch real user data."""
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    UserChartStore._instance = None
    ChartUsageStore._instance = None
    widget = QuickChartPanel()
    yield widget
    widget.deleteLater()
    UserChartStore._instance = None
    ChartUsageStore._instance = None


def test_panel_is_no_taller_than_the_old_two_row_grid(panel):
    assert panel.sizeHint().height() <= PRE_REWORK_HEIGHT


def test_panel_height_is_stable_across_snapshot_types(panel):
    """Row 2 is reserved: the panel keeps its height whatever is loaded."""
    empty_height = panel.sizeHint().height()

    panel.set_snapshot_type(SnapType.ECU_V2)
    loaded_height = panel.sizeHint().height()

    panel.set_snapshot_type(None)
    cleared_height = panel.sizeHint().height()

    assert loaded_height == empty_height == cleared_height


def test_rows_are_fixed_height(panel):
    assert panel._quick_row.height() == ROW_HEIGHT
    assert panel.my_charts._row.height() == ROW_HEIGHT


def test_quick_row_holds_every_built_in_chart(panel):
    """All built-ins are present as items; the ▾ menu only hides them visually."""
    from domain.constants import BUTTONS_BY_TYPE

    panel.set_snapshot_type(SnapType.ECU_V2)
    action_ids = {btn.property("action_id") for btn in panel._quick_row.items()}

    assert action_ids == {aid for _, aid, _ in BUTTONS_BY_TYPE[SnapType.ECU_V2]}


def test_reference_button_is_pinned_not_an_item(panel):
    """Reference Charts leads row 1 and is outside the usage sort and overflow."""
    panel.set_snapshot_type(SnapType.ECU_V2)

    assert panel._reference_button is not None
    assert panel._reference_button in panel._quick_row._pinned
    assert panel._reference_button not in panel._quick_row.items()


def test_narrow_panel_folds_charts_into_the_overflow_menu(panel):
    """The row must shrink below its buttons' combined width, or the panel
    would force the window wider instead of folding into the ▾ menu."""
    panel.set_snapshot_type(SnapType.ECU_V2)
    row = panel._quick_row

    panel.resize(1150, 120)
    panel.show()
    QApplication.processEvents()
    assert not row._overflow_btn.isVisible()

    panel.resize(500, 120)
    QApplication.processEvents()
    assert row._overflow_btn.isVisible()
    assert len(row._overflow_btn.menu().actions()) > 0
    # Reference Charts is pinned: it never folds away.
    assert panel._reference_button.isVisible()

    panel.resize(1150, 120)
    QApplication.processEvents()
    assert not row._overflow_btn.isVisible()


def test_panel_does_not_force_a_wide_window(panel):
    panel.set_snapshot_type(SnapType.ECU_V2)
    assert panel.minimumSizeHint().width() < 200


def test_my_charts_row_shows_placeholder_when_empty(panel):
    panel.set_snapshot_type(SnapType.ECU_V2)

    assert panel.my_charts._row.items() == []
    assert panel.my_charts._row._placeholder is not None
    assert panel.my_charts._add_btn is not None
