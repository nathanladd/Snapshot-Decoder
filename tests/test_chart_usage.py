"""
Unit tests for ChartUsageStore and the row-overflow split rule.

Both back the two-row chart panel: usage decides button order (most-used
leftmost), the split rule decides which buttons stay visible and which fold
into the trailing "▾" menu.
"""

import json

import pytest

from domain.chart_usage import ChartUsageStore
from domain.constants import BUTTONS_BY_TYPE
from domain.snaptypes import SnapType
from ui_pyside6.widgets.chart_button_row import plan_row_split


@pytest.fixture
def fresh_usage(tmp_path, monkeypatch):
    """A clean ChartUsageStore singleton backed by a tmp AppData-style dir."""
    ChartUsageStore._instance = None
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    yield ChartUsageStore()
    ChartUsageStore._instance = None


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------

def test_missing_file_degrades_to_empty(fresh_usage):
    assert fresh_usage.count("V2_TURBO") == 0
    assert fresh_usage.last_used("V2_TURBO") == ""


def test_corrupt_file_degrades_to_empty(fresh_usage):
    with open(fresh_usage._file_path(), "w", encoding="utf-8") as f:
        f.write("{ not json at all")

    fresh_usage.load()
    assert fresh_usage.count("V2_TURBO") == 0


def test_record_increments_and_persists(fresh_usage):
    fresh_usage.record("V2_TURBO")
    fresh_usage.record("V2_TURBO")
    fresh_usage.record("USER_abc123")

    assert fresh_usage.count("V2_TURBO") == 2
    assert fresh_usage.count("USER_abc123") == 1
    assert fresh_usage.last_used("V2_TURBO") != ""

    with open(fresh_usage._file_path(), "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["counts"]["V2_TURBO"] == 2

    # A fresh instance reads the same counts back.
    ChartUsageStore._instance = None
    assert ChartUsageStore().count("V2_TURBO") == 2


def test_record_ignores_empty_action_id(fresh_usage):
    fresh_usage.record("")
    assert fresh_usage.count("") == 0


def test_forget_drops_history(fresh_usage):
    fresh_usage.record("USER_abc123")
    fresh_usage.forget("USER_abc123")
    assert fresh_usage.count("USER_abc123") == 0


# ----------------------------------------------------------------------
# Ordering
# ----------------------------------------------------------------------

def _ordered(usage, action_ids):
    return [
        aid for _, aid in sorted(
            ((i, aid) for i, aid in enumerate(action_ids)),
            key=lambda pair: usage.order_key(pair[1], pair[0]),
        )
    ]


def test_cold_start_preserves_declared_order(fresh_usage):
    """No history => the row renders in exactly BUTTONS_BY_TYPE order."""
    declared = [aid for _, aid, _ in BUTTONS_BY_TYPE[SnapType.ECU_V2]]
    assert _ordered(fresh_usage, declared) == declared


def test_most_used_sorts_leftmost(fresh_usage):
    declared = [aid for _, aid, _ in BUTTONS_BY_TYPE[SnapType.ECU_V2]]
    least_used = declared[-1]
    for _ in range(5):
        fresh_usage.record(least_used)

    assert _ordered(fresh_usage, declared)[0] == least_used


def test_ties_break_on_declared_index(fresh_usage):
    declared = ["A", "B", "C"]
    fresh_usage.record("B")
    fresh_usage.record("C")

    # B and C tie at 1 use, so declared order decides; A (unused) trails.
    assert _ordered(fresh_usage, declared) == ["B", "C", "A"]


def test_user_charts_sort_by_the_same_rule(fresh_usage):
    mixed = ["V2_TURBO", "USER_abc123"]
    for _ in range(3):
        fresh_usage.record("USER_abc123")

    assert _ordered(fresh_usage, mixed)[0] == "USER_abc123"


# ----------------------------------------------------------------------
# Overflow split
# ----------------------------------------------------------------------

def test_everything_fits_no_overflow():
    assert plan_row_split([50, 50, 50], available=200, overflow_width=28, spacing=4) == 3


def test_overflow_reserves_room_for_the_menu_button():
    # 3x50 + 2x4 spacing = 158 > 150, so the ▾ button must be budgeted for:
    # budget = 150 - 28 - 4 = 118 -> 50 + 54 = 104 fits, a third would be 158.
    assert plan_row_split([50, 50, 50], available=150, overflow_width=28, spacing=4) == 2


def test_pinned_items_never_overflow():
    """Reference Charts / the ＋ tile stay visible even in a too-narrow row."""
    visible = plan_row_split(
        [80, 80, 80], available=40, overflow_width=28, spacing=4, pinned=1
    )
    assert visible == 1


def test_empty_row_has_nothing_to_split():
    assert plan_row_split([], available=500, overflow_width=28, spacing=4) == 0


def test_row_too_narrow_for_anything_folds_everything():
    """Degenerate case: nothing fits, so the row is just the ▾ menu."""
    assert plan_row_split([500], available=100, overflow_width=28, spacing=4) == 0
