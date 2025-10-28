"""
Unit tests for ChartRenderer

Tests the chart rendering system with various configurations.
"""

import unittest
import pandas as pd
from matplotlib.figure import Figure

from domain.chart_config import ChartConfig, AxisConfig, SeriesStyle
from ui.chart_renderer import ChartRenderer


class TestChartRenderer(unittest.TestCase):
    """Test cases for ChartRenderer class."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = pd.DataFrame({
            'Time': range(50),
            'Temperature': [20 + i * 0.1 for i in range(50)],
            'Pressure': [100 + i * 0.5 for i in range(50)],
            'Flow': [50 + i * 0.2 for i in range(50)]
        })
    
    def test_basic_line_chart(self):
        """Test basic line chart creation."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature'])
        )
        
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        self.assertIsNotNone(fig)
        self.assertIsNotNone(ax_left)
    
    def test_dual_axis_chart(self):
        """Test chart with primary and secondary axes."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature']),
            secondary_axis=AxisConfig(series=['Pressure', 'Flow'])
        )
        
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        self.assertIsNotNone(ax_right)
    
    def test_bar_chart(self):
        """Test bar chart creation."""
        config = ChartConfig(
            data=self.test_data.iloc[::5],  # Sample every 5th point
            chart_type="bar",
            primary_axis=AxisConfig(series=['Temperature']),
            secondary_axis=AxisConfig(series=['Pressure'])
        )
        
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        self.assertIsNotNone(fig)
    
    def test_bubble_chart(self):
        """Test bubble chart creation."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="bubble",
            primary_axis=AxisConfig(series=['Temperature']),
            series_styles={
                'Temperature': SeriesStyle(markersize=10, alpha=0.6)
            }
        )
        
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        self.assertIsNotNone(fig)
    
    def test_axis_limits(self):
        """Test custom axis limits."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(
                series=['Temperature'],
                min_value=15,
                max_value=30,
                auto_scale=False
            )
        )
        
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        ylim = ax_left.get_ylim()
        self.assertAlmostEqual(ylim[0], 15, places=1)
        self.assertAlmostEqual(ylim[1], 30, places=1)
    
    def test_auto_x_detection(self):
        """Test automatic X-axis column detection."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature'])
        )
        
        x_col = config.get_x_column()
        self.assertEqual(x_col, 'Time')
    
    def test_pid_unit_labels(self):
        """Test automatic unit label detection from PID info."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature']),
            pid_info={
                'Temperature': {'Unit': '°C'},
                'Pressure': {'Unit': 'kPa'}
            }
        )
        
        label = config.get_axis_label(config.primary_axis)
        self.assertEqual(label, '°C')
    
    def test_custom_series_styling(self):
        """Test custom series styling."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature']),
            series_styles={
                'Temperature': SeriesStyle(
                    linestyle='--',
                    linewidth=2.5,
                    color='red'
                )
            }
        )
        
        style = config.get_series_style('Temperature')
        self.assertEqual(style.linestyle, '--')
        self.assertEqual(style.linewidth, 2.5)
        self.assertEqual(style.color, 'red')
    
    def test_render_on_existing_figure(self):
        """Test rendering on an existing figure."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['Temperature'])
        )
        
        fig = Figure(figsize=(8, 6))
        renderer = ChartRenderer(config)
        ax_left, ax_right = renderer.render(fig, canvas=None)
        
        self.assertIsNotNone(ax_left)
    
    def test_invalid_config_raises_error(self):
        """Test that invalid configuration raises error."""
        # Empty data
        with self.assertRaises(ValueError):
            config = ChartConfig(
                data=pd.DataFrame(),
                chart_type="line",
                primary_axis=AxisConfig(series=['Test'])
            )
            renderer = ChartRenderer(config)
        
        # No series specified
        with self.assertRaises(ValueError):
            config = ChartConfig(
                data=self.test_data,
                chart_type="line",
                primary_axis=AxisConfig(series=[]),
                secondary_axis=AxisConfig(series=[])
            )
            renderer = ChartRenderer(config)
    
    def test_missing_column_handling(self):
        """Test that missing columns are handled gracefully."""
        config = ChartConfig(
            data=self.test_data,
            chart_type="line",
            primary_axis=AxisConfig(series=['NonExistentColumn', 'Temperature'])
        )
        
        # Should not raise error, just skip missing column
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        self.assertIsNotNone(fig)


if __name__ == '__main__':
    unittest.main()
