import unittest
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from domain.chart_config import ChartConfig, AxisConfig, SeriesStyle
from ui.chart_renderer import ChartRenderer

class TestStepChart(unittest.TestCase):
    def setUp(self):
        self.test_data = pd.DataFrame({
            'Time': range(10),
            'Value': [0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
        })

    def test_step_chart_rendering(self):
        config = ChartConfig(
            data=self.test_data,
            chart_type="step",
            primary_axis=AxisConfig(series=['Value'])
        )
        
        renderer = ChartRenderer(config)
        fig, ax_left, ax_right = renderer.create_and_render()
        
        # Verify that a line was plotted
        lines = ax_left.get_lines()
        self.assertTrue(len(lines) > 0, "No lines were plotted")
        
        # Verify it is a step plot
        # In matplotlib, step plots are Line2D objects with drawstyle starting with 'steps-'
        line = lines[0]
        drawstyle = line.get_drawstyle()
        print(f"DEBUG: Drawstyle is {drawstyle}")
        self.assertTrue(drawstyle.startswith('steps'), f"Expected drawstyle to start with 'steps', got '{drawstyle}'")
        self.assertEqual(drawstyle, 'steps-post')

if __name__ == '__main__':
    unittest.main()
