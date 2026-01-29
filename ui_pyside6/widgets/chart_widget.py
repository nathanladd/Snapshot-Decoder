"""
Chart widget for displaying matplotlib plots in PySide6.
"""

from typing import Optional, List

import pandas as pd

from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from domain.snapshot import Snapshot
from domain.chart_config import ChartConfig, AxisConfig
from domain.quick_charts import QUICK_CHART_REGISTRY, ChartConfigBuilder


def _format_time_mmss(seconds, pos):
    """Format seconds as MM:SS for x-axis labels."""
    if pd.isna(seconds):
        return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


class ChartWidget(QWidget):
    """Widget for displaying charts with matplotlib."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot: Optional[Snapshot] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create matplotlib figure and canvas
        self._figure = Figure(figsize=(10, 6), dpi=100)
        self._canvas = FigureCanvas(self._figure)
        
        # Create axes
        self._ax = self._figure.add_subplot(111)
        self._ax_secondary: Optional[object] = None
        
        # Navigation toolbar
        self._toolbar = NavigationToolbar(self._canvas, self)
        layout.addWidget(self._toolbar)
        
        # Canvas
        layout.addWidget(self._canvas, stretch=1)
        
        # Initial empty state
        self._show_welcome()
    
    def _show_welcome(self):
        """Show welcome message on empty chart."""
        self._ax.clear()
        self._ax.text(
            0.5, 0.5, "Load a snapshot and select PIDs to plot",
            ha='center', va='center', fontsize=14, color='gray',
            transform=self._ax.transAxes
        )
        self._ax.set_xticks([])
        self._ax.set_yticks([])
        self._canvas.draw()
    
    def clear(self):
        """Clear the chart."""
        self._figure.clear()
        self._ax = self._figure.add_subplot(111)
        self._ax_secondary = None
        self._show_welcome()
    
    def _get_pid_label(self, snapshot: Snapshot, pid: str) -> str:
        """Get the display label for a PID (description if available)."""
        if snapshot.pid_info and pid in snapshot.pid_info:
            desc = snapshot.pid_info[pid].get("description", pid)
            return desc if desc else pid
        return pid
    
    def plot_pids(
        self,
        snapshot: Snapshot,
        primary_pids: List[str],
        secondary_pids: List[str]
    ):
        """Plot selected PIDs from the snapshot."""
        self._snapshot = snapshot
        df = snapshot.snapshot
        
        if df is None:
            return
        
        # Clear and recreate axes
        self._figure.clear()
        self._ax = self._figure.add_subplot(111)
        
        # Determine x-axis
        use_time_format = False
        if "Time" in df.columns:
            x_col = "Time"
            self._ax.set_xlabel("Time (MM:SS)")
            use_time_format = True
        elif "Frame" in df.columns:
            x_col = "Frame"
            self._ax.set_xlabel("Frame")
        else:
            x_col = None
        
        x_data = df[x_col] if x_col else df.index
        
        # Apply mm:ss time formatting
        if use_time_format:
            self._ax.xaxis.set_major_formatter(FuncFormatter(_format_time_mmss))
        
        # Plot primary PIDs with description labels
        for pid in primary_pids:
            if pid in df.columns:
                label = self._get_pid_label(snapshot, pid)
                y_data = pd.to_numeric(df[pid], errors='coerce')
                self._ax.plot(x_data, y_data, label=label)
        
        self._ax.set_ylabel("Primary")
        
        # Plot secondary PIDs on secondary axis
        if secondary_pids:
            self._ax_secondary = self._ax.twinx()
            for pid in secondary_pids:
                if pid in df.columns:
                    label = self._get_pid_label(snapshot, pid)
                    y_data = pd.to_numeric(df[pid], errors='coerce')
                    self._ax_secondary.plot(
                        x_data, y_data, label=label, linestyle='--'
                    )
            self._ax_secondary.set_ylabel("Secondary")
        
        # Legends
        if primary_pids:
            self._ax.legend(loc='upper left')
        if secondary_pids and self._ax_secondary:
            self._ax_secondary.legend(loc='upper right')
        
        self._ax.grid(True, linestyle=':', alpha=0.7)
        self._figure.tight_layout()
        self._canvas.draw()
    
    def plot_quick_chart(self, snapshot: Snapshot, action_id: str):
        """Plot a quick chart by action ID."""
        self._snapshot = snapshot
        
        # Get chart definition from registry
        definition = QUICK_CHART_REGISTRY.get(action_id)
        if not definition:
            self._ax.clear()
            self._ax.text(
                0.5, 0.5, f"Unknown chart: {action_id}",
                ha='center', va='center', fontsize=12, color='red',
                transform=self._ax.transAxes
            )
            self._canvas.draw()
            return
        
        # Build chart config
        config = ChartConfigBuilder.build(definition, snapshot)
        
        # Render based on chart type
        self._render_config(config)
    
    def _render_config(self, config: ChartConfig):
        """Render a ChartConfig."""
        self._figure.clear()
        self._ax = self._figure.add_subplot(111)
        
        df = config.data
        x_col = config.get_x_column()
        if x_col and x_col in df.columns:
            x_data = pd.to_numeric(df[x_col], errors='coerce')
            # Apply mm:ss formatting if this is a time column
            if x_col == "Time":
                self._ax.xaxis.set_major_formatter(FuncFormatter(_format_time_mmss))
                self._ax.set_xlabel("Time (MM:SS)")
        else:
            x_data = df.index
        
        if config.chart_type == "line":
            self._render_line_chart(config, x_data)
        elif config.chart_type == "status":
            self._render_status_chart(config, x_data)
        elif config.chart_type == "bar":
            self._render_bar_chart(config)
        elif config.chart_type == "bubble":
            self._render_bubble_chart(config)
        else:
            self._render_line_chart(config, x_data)
        
        self._ax.set_title(config.title)
        self._ax.grid(config.grid, linestyle=config.grid_style, linewidth=config.grid_linewidth)
        self._figure.tight_layout()
        self._canvas.draw()
    
    def _render_line_chart(self, config: ChartConfig, x_data):
        """Render a line chart."""
        df = config.data
        
        # Primary axis
        for pid in config.primary_axis.series:
            if pid in df.columns:
                y_data = pd.to_numeric(df[pid], errors='coerce')
                label = self._get_pid_label(self._snapshot, pid) if self._snapshot else pid
                self._ax.plot(x_data, y_data, label=label)
        
        self._ax.set_ylabel(config.get_axis_label(config.primary_axis))
        
        # Secondary axis
        if config.secondary_axis.series:
            self._ax_secondary = self._ax.twinx()
            for pid in config.secondary_axis.series:
                if pid in df.columns:
                    y_data = pd.to_numeric(df[pid], errors='coerce')
                    label = self._get_pid_label(self._snapshot, pid) if self._snapshot else pid
                    self._ax_secondary.plot(x_data, y_data, label=label, linestyle='--')
            self._ax_secondary.set_ylabel(config.get_axis_label(config.secondary_axis))
        
        # Legends
        if config.show_legend:
            if config.primary_axis.series:
                self._ax.legend(loc=config.primary_legend_loc)
            if config.secondary_axis.series and self._ax_secondary:
                self._ax_secondary.legend(loc=config.secondary_legend_loc)
    
    def _render_status_chart(self, config: ChartConfig, x_data):
        """Render a status chart (similar to line but with tick labels)."""
        self._render_line_chart(config, x_data)
        
        # Apply custom ticks if specified
        if config.primary_axis.ticks is not None:
            self._ax.set_yticks(config.primary_axis.ticks)
            if config.primary_axis.tick_labels:
                self._ax.set_yticklabels(config.primary_axis.tick_labels)
    
    def _render_bar_chart(self, config: ChartConfig):
        """Render a bar chart."""
        df = config.data
        x_col = config.x_column or df.columns[0]
        y_col = config.primary_axis.series[0] if config.primary_axis.series else df.columns[1]
        
        if x_col in df.columns and y_col in df.columns:
            self._ax.bar(df[x_col], df[y_col])
            self._ax.set_xlabel(config.x_label or x_col)
            self._ax.set_ylabel(y_col)
    
    def _render_bubble_chart(self, config: ChartConfig):
        """Render a bubble chart."""
        df = config.data
        
        if df.empty:
            self._ax.text(0.5, 0.5, "No data for bubble chart",
                         ha='center', va='center', transform=self._ax.transAxes)
            return
        
        x_col = config.x_column or df.columns[0]
        y_col = config.primary_axis.series[0] if config.primary_axis.series else df.columns[1]
        size_col = config.bubble_size_column
        
        if all(c in df.columns for c in [x_col, y_col]) and size_col and size_col in df.columns:
            sizes = df[size_col] * config.bubble_size_scale
            self._ax.scatter(df[x_col], df[y_col], s=sizes, alpha=0.6)
            self._ax.set_xlabel(x_col)
            self._ax.set_ylabel(y_col)
