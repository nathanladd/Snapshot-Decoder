"""
Unit tests for ChartState.

Verifies that state management and reset functionality work correctly.
"""

import pytest
import pandas as pd

from domain.chart_state import ChartState
from domain.chart_config import ChartConfig, AxisConfig


def create_test_config() -> ChartConfig:
    """Create a test ChartConfig for state tests."""
    return ChartConfig(
        data=pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]}),
        chart_type="line",
        primary_axis=AxisConfig(
            series=["A"],
            auto_scale=False,
            min_value=0,
            max_value=100,
            ticks=[0, 25, 50, 75, 100],
            tick_labels=["0", "25", "50", "75", "100"],
        ),
        secondary_axis=AxisConfig(
            series=["B"],
            auto_scale=False,
            min_value=-10,
            max_value=10,
        ),
        show_legend=False,
        quick_chart_action_id="TEST_CHART",
    )


class TestChartStateReset:
    """Tests for reset functionality."""

    def test_reset_clears_all_state(self):
        """Verify reset() clears all transient state."""
        state = ChartState()
        
        # Set various state values
        state.config = create_test_config()
        state.primary_series = ["PID_A", "PID_B"]
        state.secondary_series = ["PID_C"]
        state.primary_auto = False
        state.primary_min = 0
        state.primary_max = 100
        state.secondary_auto = False
        state.secondary_min = -50
        state.secondary_max = 50
        state.primary_ticks = [0, 50, 100]
        state.primary_tick_labels = ["Low", "Mid", "High"]
        state.chart_type = "status"
        state.show_legend = False
        state.active_quick_chart_id = "TEST_CHART"
        
        # Reset
        state.reset()
        
        # Verify all state is cleared
        assert state.config is None
        assert state.primary_series == []
        assert state.secondary_series == []
        assert state.primary_auto is True
        assert state.primary_min is None
        assert state.primary_max is None
        assert state.secondary_auto is True
        assert state.secondary_min is None
        assert state.secondary_max is None
        assert state.primary_ticks is None
        assert state.primary_tick_labels is None
        assert state.chart_type == "line"
        assert state.show_legend is True
        assert state.active_quick_chart_id is None

    def test_reset_for_chart_type_change(self):
        """Verify reset_for_chart_type_change clears only type-specific state."""
        state = ChartState()
        
        # Set state
        state.primary_series = ["PID_A"]
        state.primary_ticks = [0, 1, 2]
        state.primary_tick_labels = ["Off", "On", "Error"]
        state.chart_type = "status"
        
        # Reset for chart type change
        state.reset_for_chart_type_change()
        
        # Ticks should be cleared
        assert state.primary_ticks is None
        assert state.primary_tick_labels is None
        
        # Other state should be preserved
        assert state.primary_series == ["PID_A"]
        assert state.chart_type == "status"


class TestChartStateHelpers:
    """Tests for helper methods."""

    def test_has_series_empty(self):
        """Test has_series returns False when no series selected."""
        state = ChartState()
        assert state.has_series() is False

    def test_has_series_primary_only(self):
        """Test has_series with primary series only."""
        state = ChartState()
        state.primary_series = ["PID_A"]
        assert state.has_series() is True

    def test_has_series_secondary_only(self):
        """Test has_series with secondary series only."""
        state = ChartState()
        state.secondary_series = ["PID_B"]
        assert state.has_series() is True

    def test_get_all_series(self):
        """Test get_all_series combines both axes."""
        state = ChartState()
        state.primary_series = ["A", "B"]
        state.secondary_series = ["C"]
        
        all_series = state.get_all_series()
        assert all_series == ["A", "B", "C"]

    def test_set_primary_range_with_values(self):
        """Test set_primary_range disables auto-scale."""
        state = ChartState()
        state.set_primary_range(0, 100)
        
        assert state.primary_min == 0
        assert state.primary_max == 100
        assert state.primary_auto is False

    def test_set_primary_range_none_values(self):
        """Test set_primary_range enables auto-scale with None."""
        state = ChartState()
        state.primary_auto = False
        state.primary_min = 10
        state.primary_max = 90
        
        state.set_primary_range(None, None)
        
        assert state.primary_min is None
        assert state.primary_max is None
        assert state.primary_auto is True

    def test_set_secondary_range(self):
        """Test set_secondary_range works correctly."""
        state = ChartState()
        state.set_secondary_range(-50, 50)
        
        assert state.secondary_min == -50
        assert state.secondary_max == 50
        assert state.secondary_auto is False


class TestChartStateConfigInteraction:
    """Tests for config loading and applying."""

    def test_load_from_config(self):
        """Test loading state from a ChartConfig."""
        state = ChartState()
        config = create_test_config()
        
        state.load_from_config(config)
        
        assert state.config is config
        assert state.primary_series == ["A"]
        assert state.secondary_series == ["B"]
        assert state.primary_auto is False
        assert state.primary_min == 0
        assert state.primary_max == 100
        assert state.secondary_auto is False
        assert state.secondary_min == -10
        assert state.secondary_max == 10
        assert state.primary_ticks == [0, 25, 50, 75, 100]
        assert state.primary_tick_labels == ["0", "25", "50", "75", "100"]
        assert state.chart_type == "line"
        assert state.show_legend is False
        assert state.active_quick_chart_id == "TEST_CHART"

    def test_apply_to_config(self):
        """Test applying state to a ChartConfig."""
        state = ChartState()
        state.primary_series = ["X", "Y"]
        state.secondary_series = ["Z"]
        state.primary_auto = False
        state.primary_min = 10
        state.primary_max = 90
        state.chart_type = "status"
        state.show_legend = False
        
        config = ChartConfig(
            data=pd.DataFrame({"X": [1], "Y": [2], "Z": [3]}),
        )
        
        result = state.apply_to_config(config)
        
        assert result.primary_axis.series == ["X", "Y"]
        assert result.secondary_axis.series == ["Z"]
        assert result.primary_axis.auto_scale is False
        assert result.primary_axis.min_value == 10
        assert result.primary_axis.max_value == 90
        assert result.chart_type == "status"
        assert result.show_legend is False

    def test_apply_preserves_auto_scale(self):
        """Test that auto-scale is properly applied."""
        state = ChartState()
        state.primary_auto = True
        state.secondary_auto = True
        
        config = ChartConfig(
            data=pd.DataFrame({"A": [1]}),
            primary_axis=AxisConfig(auto_scale=False, min_value=0, max_value=100),
            secondary_axis=AxisConfig(auto_scale=False, min_value=-50, max_value=50),
        )
        
        result = state.apply_to_config(config)
        
        assert result.primary_axis.auto_scale is True
        assert result.secondary_axis.auto_scale is True


class TestChartStateDefaults:
    """Tests for default state values."""

    def test_default_values(self):
        """Test that default values are sensible."""
        state = ChartState()
        
        assert state.config is None
        assert state.primary_series == []
        assert state.secondary_series == []
        assert state.primary_auto is True
        assert state.secondary_auto is True
        assert state.chart_type == "line"
        assert state.show_legend is True
        assert state.active_quick_chart_id is None

    def test_fresh_state_has_no_series(self):
        """Test that fresh state reports no series."""
        state = ChartState()
        assert state.has_series() is False
        assert state.get_all_series() == []
