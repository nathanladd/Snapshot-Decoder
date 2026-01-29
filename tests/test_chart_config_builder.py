"""
Unit tests for ChartConfigBuilder.

Verifies that the builder correctly converts QuickChartDef definitions
into ChartConfig objects.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock

from domain.quick_charts import (
    QuickChartDef,
    BarChartDef,
    BubbleChartDef,
    StatusChartDef,
    ChartConfigBuilder,
    V1_CHARTS,
    V2_CHARTS,
    EUD_CHARTS,
)
from domain.chart_config import ChartConfig


def create_mock_snapshot(columns: list[str], data: dict = None) -> MagicMock:
    """Create a mock Snapshot object for testing."""
    mock = MagicMock()
    
    if data is None:
        # Create default test data
        data = {col: [1.0, 2.0, 3.0] for col in columns}
        data["Frame"] = [0, 1, 2]
        data["Time (MM:SS)"] = [0.0, 1.0, 2.0]
    
    mock.snapshot = pd.DataFrame(data)
    mock.pid_info = {col: {"Unit": "test_unit"} for col in columns}
    mock.file_name = "test_file.xlsx"
    mock.date_time = "2024-01-01 12:00:00"
    mock.hours = 100.0
    
    return mock


class TestLineChartBuilder:
    """Tests for building line chart configurations."""

    def test_build_basic_line_chart(self):
        """Test building a basic line chart."""
        definition = QuickChartDef(
            action_id="TEST_LINE",
            title="Test Line Chart",
            primary_pids=["PID_A", "PID_B"],
        )
        
        snapshot = create_mock_snapshot(["PID_A", "PID_B"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert isinstance(config, ChartConfig)
        assert config.chart_type == "line"
        assert config.title == "Test Line Chart"
        assert config.primary_axis.series == ["PID_A", "PID_B"]
        assert config.quick_chart_action_id == "TEST_LINE"

    def test_build_line_chart_with_ranges(self):
        """Test line chart with axis ranges."""
        definition = QuickChartDef(
            action_id="TEST_RANGES",
            title="Range Test",
            primary_pids=["PID_A"],
            primary_range=(0, 100),
            secondary_pids=["PID_B"],
            secondary_range=(-50, 50),
        )
        
        snapshot = create_mock_snapshot(["PID_A", "PID_B"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.primary_axis.auto_scale is False
        assert config.primary_axis.min_value == 0
        assert config.primary_axis.max_value == 100
        assert config.secondary_axis.auto_scale is False
        assert config.secondary_axis.min_value == -50
        assert config.secondary_axis.max_value == 50

    def test_filters_missing_pids(self):
        """Test that PIDs not in snapshot are filtered out."""
        definition = QuickChartDef(
            action_id="TEST_FILTER",
            title="Filter Test",
            primary_pids=["PID_A", "PID_MISSING", "PID_B"],
        )
        
        # Only PID_A and PID_B exist in snapshot
        snapshot = create_mock_snapshot(["PID_A", "PID_B"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert "PID_MISSING" not in config.primary_axis.series
        assert config.primary_axis.series == ["PID_A", "PID_B"]

    def test_dynamic_pids_filtering(self):
        """Test dynamic PID filtering (e.g., 3 vs 4 cylinder)."""
        definition = QuickChartDef(
            action_id="TEST_DYNAMIC",
            title="Dynamic PIDs",
            primary_pids=["CYL_0", "CYL_1", "CYL_2", "CYL_3"],
            dynamic_primary_pids=["CYL_0", "CYL_1", "CYL_2", "CYL_3"],
        )
        
        # 3-cylinder engine only has CYL_0, CYL_1, CYL_2
        snapshot = create_mock_snapshot(["CYL_0", "CYL_1", "CYL_2"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert len(config.primary_axis.series) == 3
        assert "CYL_3" not in config.primary_axis.series

    def test_metadata_copied(self):
        """Test that snapshot metadata is copied to config."""
        definition = QuickChartDef(
            action_id="TEST_META",
            title="Metadata Test",
            primary_pids=["PID_A"],
        )
        
        snapshot = create_mock_snapshot(["PID_A"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.file_name == "test_file.xlsx"
        assert config.date_time == "2024-01-01 12:00:00"
        assert config.engine_hours == 100.0


class TestStatusChartBuilder:
    """Tests for building status chart configurations."""

    def test_build_basic_status_chart(self):
        """Test building a basic status chart."""
        definition = StatusChartDef(
            action_id="TEST_STATUS",
            title="Status Test",
            primary_pids=["STATUS_A", "STATUS_B"],
        )
        
        snapshot = create_mock_snapshot(["STATUS_A", "STATUS_B"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "status"

    def test_build_parsed_status_chart(self):
        """Test status chart that parses digit columns."""
        definition = StatusChartDef(
            action_id="TEST_PARSED",
            title="Parsed Status",
            primary_pids=[],
            source_column="STATUS_COL",
            digit_labels=["Bit0", "Bit1", "Bit2"],
            display_prefix="Status",
        )
        
        # Create data with digit strings
        data = {
            "STATUS_COL": ["010", "101", "110"],
            "Frame": [0, 1, 2],
            "Time (MM:SS)": [0.0, 1.0, 2.0],
        }
        snapshot = create_mock_snapshot(["STATUS_COL"], data)
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "status"
        # Should have generated columns for each digit
        assert len(config.primary_axis.series) == 3
        assert "Status_Bit0" in config.primary_axis.series


class TestBarChartBuilder:
    """Tests for building bar chart configurations."""

    def test_build_bar_chart(self):
        """Test building a bar chart from column values."""
        definition = BarChartDef(
            action_id="TEST_BAR",
            title="Bar Test",
            primary_pids=[],
            source_columns=["COL_A", "COL_B", "COL_C"],
            bar_labels=["A", "B", "C"],
            x_label="Category",
            y_label="Hours",
            convert_seconds_to_hours=True,
        )
        
        # Create data with seconds values at Frame 0
        data = {
            "COL_A": [3600.0, 3600.0],  # 1 hour
            "COL_B": [7200.0, 7200.0],  # 2 hours
            "COL_C": [1800.0, 1800.0],  # 0.5 hours
            "Frame": [0, 1],
            "Time (MM:SS)": [0.0, 1.0],
        }
        snapshot = create_mock_snapshot(["COL_A", "COL_B", "COL_C"], data)
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "bar"
        assert len(config.data) == 3  # 3 bars
        # Values should be converted to hours
        assert config.data["Hours"].iloc[0] == 1.0
        assert config.data["Hours"].iloc[1] == 2.0
        assert config.data["Hours"].iloc[2] == 0.5

    def test_bar_chart_missing_columns(self):
        """Test bar chart handles missing columns gracefully."""
        definition = BarChartDef(
            action_id="TEST_BAR_MISSING",
            title="Missing Columns",
            primary_pids=[],
            source_columns=["COL_A", "COL_MISSING"],
            bar_labels=["A", "Missing"],
            convert_seconds_to_hours=False,
        )
        
        data = {
            "COL_A": [100.0],
            "Frame": [0],
            "Time (MM:SS)": [0.0],
        }
        snapshot = create_mock_snapshot(["COL_A"], data)
        config = ChartConfigBuilder.build(definition, snapshot)
        
        # Missing column should get 0.0 value
        assert config.data.iloc[1, 1] == 0.0


class TestBubbleChartBuilder:
    """Tests for building bubble chart configurations."""

    def test_build_bubble_chart(self):
        """Test building a bubble chart from column pattern."""
        definition = BubbleChartDef(
            action_id="TEST_BUBBLE",
            title="Bubble Test",
            primary_pids=[],
            column_pattern="DATA[{x},{y}]",
            x_label="X",
            y_label="Y",
            size_label="Size",
            x_index_map={0: 10, 1: 20},
            y_index_map={0: 100, 1: 200},
            total_reference_column="TOTAL",
        )
        
        data = {
            "DATA[0,0]": [50.0],
            "DATA[0,1]": [25.0],
            "DATA[1,0]": [25.0],
            "TOTAL": [100.0],
            "Frame": [0],
            "Time (MM:SS)": [0.0],
        }
        snapshot = create_mock_snapshot(["DATA[0,0]", "DATA[0,1]", "DATA[1,0]", "TOTAL"], data)
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "bubble"
        assert config.bubble_size_column == "Size"
        # Should have 3 data points
        assert len(config.data) == 3


class TestV1ChartBuilds:
    """Integration tests for V1 chart definitions."""

    def test_v1_battery_builds(self):
        """Test V1 battery chart builds correctly."""
        definition = V1_CHARTS["V1_BATTERY_TEST"]
        snapshot = create_mock_snapshot(["P_L_Battery_raw", "IN_Engine_cycle_speed"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "line"
        assert "P_L_Battery_raw" in config.primary_axis.series


class TestV2ChartBuilds:
    """Integration tests for V2 chart definitions."""

    def test_v2_battery_builds(self):
        """Test V2 battery chart builds correctly."""
        definition = V2_CHARTS["V2_BATTERY_TEST"]
        snapshot = create_mock_snapshot(["BattU_u", "Epm_nEng"])
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "line"
        assert "BattU_u" in config.primary_axis.series


class TestEUDChartBuilds:
    """Integration tests for EUD chart definitions."""

    def test_eud_speed_band_builds(self):
        """Test EUD speed band bar chart builds correctly."""
        definition = EUD_CHARTS["V1EUD_SPEED_BAND"]
        
        columns = [
            "EUD_Engine_run_time_spdbnd1_nvv",
            "EUD_Engine_run_time_spdbnd2_nvv",
            "EUD_Engine_run_time_spdbnd3_nvv",
            "EUD_Engine_run_time_spdbnd4_nvv",
            "EUD_Engine_run_time_spdbnd5_nvv",
        ]
        data = {col: [3600.0] for col in columns}
        data["Frame"] = [0]
        data["Time (MM:SS)"] = [0.0]
        
        snapshot = create_mock_snapshot(columns, data)
        config = ChartConfigBuilder.build(definition, snapshot)
        
        assert config.chart_type == "bar"
        assert len(config.data) == 5
