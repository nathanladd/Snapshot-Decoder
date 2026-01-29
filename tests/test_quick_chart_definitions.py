"""
Unit tests for quick chart definitions.

Verifies that all chart definitions are valid and properly structured.
"""

import pytest
from domain.quick_charts import (
    QuickChartDef,
    BarChartDef,
    BubbleChartDef,
    V1_CHARTS,
    V2_CHARTS,
    EUD_CHARTS,
    QUICK_CHART_REGISTRY,
)
from domain.quick_charts.definitions import StatusChartDef


class TestQuickChartDef:
    """Tests for the base QuickChartDef dataclass."""

    def test_basic_definition(self):
        """Test creating a basic chart definition."""
        chart = QuickChartDef(
            action_id="TEST_CHART",
            title="Test Chart",
            primary_pids=["PID_A", "PID_B"],
        )
        assert chart.action_id == "TEST_CHART"
        assert chart.title == "Test Chart"
        assert chart.primary_pids == ["PID_A", "PID_B"]
        assert chart.chart_type == "line"
        assert chart.show_legend is True

    def test_definition_with_ranges(self):
        """Test definition with axis ranges."""
        chart = QuickChartDef(
            action_id="TEST_RANGES",
            title="Range Test",
            primary_pids=["PID_A"],
            primary_range=(0, 100),
            secondary_pids=["PID_B"],
            secondary_range=(-50, 50),
        )
        assert chart.primary_range == (0, 100)
        assert chart.secondary_range == (-50, 50)

    def test_definition_with_ticks(self):
        """Test definition with custom tick marks."""
        chart = QuickChartDef(
            action_id="TEST_TICKS",
            title="Tick Test",
            primary_pids=["PID_A"],
            primary_ticks=[0, 1, 2, 3],
            primary_tick_labels=["Off", "Low", "Med", "High"],
        )
        assert chart.primary_ticks == [0, 1, 2, 3]
        assert chart.primary_tick_labels == ["Off", "Low", "Med", "High"]


class TestBarChartDef:
    """Tests for BarChartDef dataclass."""

    def test_bar_chart_defaults(self):
        """Test bar chart has correct default chart_type."""
        chart = BarChartDef(
            action_id="TEST_BAR",
            title="Bar Test",
            primary_pids=[],
            source_columns=["COL_A", "COL_B"],
            bar_labels=["A", "B"],
        )
        assert chart.chart_type == "bar"
        assert chart.convert_seconds_to_hours is True

    def test_bar_chart_columns_match_labels(self):
        """Verify source_columns and bar_labels can be matched."""
        chart = BarChartDef(
            action_id="TEST_BAR",
            title="Bar Test",
            primary_pids=[],
            source_columns=["COL_A", "COL_B", "COL_C"],
            bar_labels=["A", "B", "C"],
        )
        assert len(chart.source_columns) == len(chart.bar_labels)


class TestBubbleChartDef:
    """Tests for BubbleChartDef dataclass."""

    def test_bubble_chart_defaults(self):
        """Test bubble chart has correct default chart_type."""
        chart = BubbleChartDef(
            action_id="TEST_BUBBLE",
            title="Bubble Test",
            primary_pids=[],
        )
        assert chart.chart_type == "bubble"

    def test_bubble_chart_index_maps(self):
        """Test bubble chart with index mappings."""
        chart = BubbleChartDef(
            action_id="TEST_BUBBLE",
            title="Bubble Test",
            primary_pids=[],
            x_index_map={0: 100, 1: 200},
            y_index_map={0: 10, 1: 20},
        )
        assert chart.x_index_map[0] == 100
        assert chart.y_index_map[1] == 20


class TestStatusChartDef:
    """Tests for StatusChartDef dataclass."""

    def test_status_chart_defaults(self):
        """Test status chart has correct default chart_type."""
        chart = StatusChartDef(
            action_id="TEST_STATUS",
            title="Status Test",
            primary_pids=["PID_A", "PID_B"],
        )
        assert chart.chart_type == "status"
        assert chart.show_legend is True

    def test_status_chart_with_digit_parsing(self):
        """Test status chart configured for digit parsing."""
        chart = StatusChartDef(
            action_id="TEST_STATUS",
            title="Status Test",
            primary_pids=[],
            source_column="STATUS_COL",
            digit_labels=["Bit0", "Bit1", "Bit2"],
            display_prefix="Status:",
        )
        assert chart.source_column == "STATUS_COL"
        assert len(chart.digit_labels) == 3


class TestV1Charts:
    """Tests for V1 ECU chart definitions."""

    def test_all_v1_charts_have_action_id(self):
        """Verify all V1 charts have unique action IDs."""
        action_ids = [chart.action_id for chart in V1_CHARTS.values()]
        assert len(action_ids) == len(set(action_ids)), "Duplicate action IDs found"

    def test_all_v1_charts_have_title(self):
        """Verify all V1 charts have a title."""
        for action_id, chart in V1_CHARTS.items():
            assert chart.title, f"{action_id} missing title"

    def test_v1_battery_test_definition(self):
        """Test V1 battery chart is correctly defined."""
        chart = V1_CHARTS["V1_BATTERY_TEST"]
        assert chart.primary_pids == ["P_L_Battery_raw"]
        assert chart.primary_range == (0, 18)
        assert chart.secondary_pids == ["IN_Engine_cycle_speed"]

    def test_v1_cam_crank_is_status_chart(self):
        """Test V1 cam/crank chart is a status chart."""
        chart = V1_CHARTS["V1_CAM_CRANK"]
        assert chart.chart_type == "status"
        assert isinstance(chart, StatusChartDef)

    def test_v1_charts_count(self):
        """Verify expected number of V1 charts."""
        assert len(V1_CHARTS) == 13


class TestV2Charts:
    """Tests for V2 ECU chart definitions."""

    def test_all_v2_charts_have_action_id(self):
        """Verify all V2 charts have unique action IDs."""
        action_ids = [chart.action_id for chart in V2_CHARTS.values()]
        assert len(action_ids) == len(set(action_ids)), "Duplicate action IDs found"

    def test_v2_battery_test_definition(self):
        """Test V2 battery chart is correctly defined."""
        chart = V2_CHARTS["V2_BATTERY_TEST"]
        assert chart.primary_pids == ["BattU_u"]
        assert chart.primary_range == (0, 18)

    def test_v2_torque_limits_has_digit_labels(self):
        """Test V2 torque limits chart has digit labels for parsing."""
        chart = V2_CHARTS["V2_ENGINE_TORQUE_LIMITS"]
        assert chart.chart_type == "status"
        assert chart.source_column == "CoETS_stCurrLimActive"
        assert len(chart.digit_labels) == 15

    def test_v2_charts_count(self):
        """Verify expected number of V2 charts."""
        assert len(V2_CHARTS) == 10


class TestEUDCharts:
    """Tests for EUD chart definitions."""

    def test_all_eud_charts_have_action_id(self):
        """Verify all EUD charts have unique action IDs."""
        action_ids = [chart.action_id for chart in EUD_CHARTS.values()]
        assert len(action_ids) == len(set(action_ids)), "Duplicate action IDs found"

    def test_speed_v_load_is_bubble_chart(self):
        """Test speed vs load chart is a bubble chart."""
        chart = EUD_CHARTS["V1EUD_SPEED_V_LOAD"]
        assert chart.chart_type == "bubble"
        assert isinstance(chart, BubbleChartDef)
        assert chart.x_index_map is not None
        assert chart.y_index_map is not None

    def test_speed_band_is_bar_chart(self):
        """Test speed band chart is a bar chart."""
        chart = EUD_CHARTS["V1EUD_SPEED_BAND"]
        assert chart.chart_type == "bar"
        assert isinstance(chart, BarChartDef)
        assert len(chart.source_columns) == 5
        assert len(chart.bar_labels) == 5

    def test_elevation_bar_labels_match_columns(self):
        """Test elevation chart has matching columns and labels."""
        chart = EUD_CHARTS["V1EUD_ELEVATION"]
        assert len(chart.source_columns) == len(chart.bar_labels)

    def test_eud_charts_count(self):
        """Verify expected number of EUD charts."""
        assert len(EUD_CHARTS) == 4


class TestQuickChartRegistry:
    """Tests for the combined chart registry."""

    def test_registry_contains_all_charts(self):
        """Verify registry contains all charts from all categories."""
        expected_count = len(V1_CHARTS) + len(V2_CHARTS) + len(EUD_CHARTS)
        assert len(QUICK_CHART_REGISTRY) == expected_count

    def test_registry_keys_match_action_ids(self):
        """Verify registry keys match the chart action IDs."""
        for action_id, chart in QUICK_CHART_REGISTRY.items():
            assert action_id == chart.action_id

    def test_no_duplicate_action_ids_across_registries(self):
        """Verify no action ID appears in multiple registries."""
        all_action_ids = (
            list(V1_CHARTS.keys()) + 
            list(V2_CHARTS.keys()) + 
            list(EUD_CHARTS.keys())
        )
        assert len(all_action_ids) == len(set(all_action_ids)), \
            "Duplicate action IDs found across registries"

    def test_all_charts_are_valid_definitions(self):
        """Verify all registered charts are QuickChartDef instances."""
        for action_id, chart in QUICK_CHART_REGISTRY.items():
            assert isinstance(chart, QuickChartDef), \
                f"{action_id} is not a QuickChartDef instance"
