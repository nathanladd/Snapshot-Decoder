"""
Unit tests for UserChartDef / UserChartStore (My Charts).
"""

import json
import os

import pytest

from domain.quick_charts import QUICK_CHART_REGISTRY, QuickChartDef, ChartConfigBuilder
from domain.snaptypes import SnapType
from domain.user_charts import UserChartDef, UserChartStore


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """A clean UserChartStore singleton backed by a tmp AppData-style dir."""
    UserChartStore._instance = None
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    yield UserChartStore()
    UserChartStore._instance = None


def make_chart(action_id="USER_abc123", title="My EGR + Boost", snapshot_type="ECU_V1"):
    return UserChartDef(
        action_id=action_id,
        title=title,
        primary_pids=["IN_Egr_position"],
        secondary_pids=["ACM_Boost_pressure"],
        primary_range=(0.0, 100.0),
        snapshot_type=snapshot_type,
        created="2026-07-14T09:00:00",
        modified="2026-07-14T09:00:00",
    )


class TestUserChartDefRoundTrip:
    def test_to_dict_from_dict_round_trips_tuples_as_lists(self):
        chart = make_chart()
        data = chart.to_dict()

        assert data["primary_range"] == [0.0, 100.0]
        assert data["secondary_range"] is None

        restored = UserChartDef.from_dict(data)
        assert restored.primary_range == (0.0, 100.0)
        assert restored.secondary_range is None
        assert restored == chart or restored.to_dict() == chart.to_dict()

    def test_to_quick_chart_def_produces_valid_definition(self):
        chart = make_chart()
        qcd = chart.to_quick_chart_def()

        assert isinstance(qcd, QuickChartDef)
        assert qcd.action_id == chart.action_id
        assert qcd.title == chart.title
        assert qcd.primary_pids == chart.primary_pids
        assert qcd.secondary_pids == chart.secondary_pids
        assert qcd.primary_range == chart.primary_range
        assert qcd.chart_type == "line"

    def test_user_chart_never_appears_in_registry(self):
        chart = make_chart(action_id="USER_never_registered")
        assert chart.action_id not in QUICK_CHART_REGISTRY


class TestUserChartStorePersistence:
    def test_missing_file_loads_empty(self, fresh_store):
        assert fresh_store.all() == []

    def test_corrupt_file_degrades_to_empty(self, fresh_store):
        path = fresh_store._file_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not valid json")

        fresh_store.load()

        assert fresh_store.all() == []

    def test_add_persists_and_reloads(self, fresh_store):
        chart = make_chart()
        fresh_store.add(chart)

        UserChartStore._instance = None
        reloaded = UserChartStore()
        reloaded.load()

        assert len(reloaded.all()) == 1
        assert reloaded.get(chart.action_id).title == chart.title

    def test_update_persists_changes(self, fresh_store):
        chart = make_chart()
        fresh_store.add(chart)

        chart.title = "Renamed"
        fresh_store.update(chart)

        UserChartStore._instance = None
        reloaded = UserChartStore()
        reloaded.load()

        assert reloaded.get(chart.action_id).title == "Renamed"

    def test_delete_persists(self, fresh_store):
        chart = make_chart()
        fresh_store.add(chart)
        fresh_store.delete(chart.action_id)

        UserChartStore._instance = None
        reloaded = UserChartStore()
        reloaded.load()

        assert reloaded.all() == []

    def test_json_shape_on_disk(self, fresh_store):
        chart = make_chart()
        fresh_store.add(chart)

        with open(fresh_store._file_path(), "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema_version"] == 1
        assert data["charts"][0]["action_id"] == chart.action_id


class TestTypeRouting:
    def test_for_type_returns_only_matching_snapshot_type(self, fresh_store):
        v1_chart = make_chart(action_id="USER_v1", snapshot_type="ECU_V1")
        v2_chart = make_chart(action_id="USER_v2", snapshot_type="ECU_V2")
        fresh_store.add(v1_chart)
        fresh_store.add(v2_chart)

        v1_results = fresh_store.for_type(SnapType.ECU_V1)
        assert [c.action_id for c in v1_results] == ["USER_v1"]

        v2_results = fresh_store.for_type(SnapType.ECU_V2)
        assert [c.action_id for c in v2_results] == ["USER_v2"]

        eud_results = fresh_store.for_type(SnapType.EUD_V1)
        assert eud_results == []


class TestTitleUniqueness:
    def test_rejects_title_matching_builtin_slug(self, fresh_store):
        # "EGR Flow" is a built-in chart title (V1_EGR_FLOW / V2_EGR_FLOW).
        assert not fresh_store.is_title_available("EGR Flow")
        assert not fresh_store.is_title_available("EGR   Flow")  # same slug, extra whitespace

    def test_rejects_title_matching_existing_user_chart(self, fresh_store):
        fresh_store.add(make_chart(action_id="USER_1", title="My Custom Chart"))
        assert not fresh_store.is_title_available("My Custom Chart")
        assert not fresh_store.is_title_available("My-Custom-Chart")

    def test_accepts_genuinely_new_title(self, fresh_store):
        assert fresh_store.is_title_available("A Totally New Chart Name")

    def test_exclude_id_allows_renaming_to_own_current_title(self, fresh_store):
        chart = make_chart(action_id="USER_1", title="My Custom Chart")
        fresh_store.add(chart)
        assert fresh_store.is_title_available("My Custom Chart", exclude_id="USER_1")

    def test_slug_matches_quick_iq_url_builder_exactly(self):
        from domain.quick_charts import slugify_chart_title

        # Mirrors MainWindow._build_quick_iq_url's historical inline logic.
        assert slugify_chart_title("EGR Flow") == "EGR-Flow"
        assert slugify_chart_title("Rail Pressure & Gap") == "Rail-Pressure-and-Gap"
        assert slugify_chart_title("A/B Test") == "A-B-Test"


class TestRegistryFallbackBuild:
    def test_user_chart_builds_chart_config_like_a_builtin(self):
        """A USER_ def resolves and builds a ChartConfig via the normal builder path."""
        from unittest.mock import MagicMock
        import pandas as pd

        chart = make_chart(action_id="USER_fallback_test")
        qcd = chart.to_quick_chart_def()

        mock_snapshot = MagicMock()
        mock_snapshot.snapshot = pd.DataFrame({
            "IN_Egr_position": [1.0, 2.0, 3.0],
            "ACM_Boost_pressure": [4.0, 5.0, 6.0],
            "Frame": [0, 1, 2],
        })
        mock_snapshot.pid_info = {}
        mock_snapshot.file_name = "test.xlsx"
        mock_snapshot.date_time = "2026-07-14"
        mock_snapshot.hours = 10.0
        mock_snapshot.snapshot_type = SnapType.ECU_V1

        config = ChartConfigBuilder.build(qcd, mock_snapshot)

        assert config.chart_type == "line"
        assert config.quick_chart_action_id == "USER_fallback_test"
        assert config.primary_axis.series == ["IN_Egr_position"]
        assert chart.action_id not in QUICK_CHART_REGISTRY
