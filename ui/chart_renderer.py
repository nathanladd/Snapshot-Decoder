"""
Chart Renderer

A flexible chart rendering class that can create line, bar, and bubble charts
with primary and secondary axes. Can be used in various contexts: main window,
separate windows, or PDF export.
"""

from typing import Optional, Tuple
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.axes import Axes

from domain.chart_config import ChartConfig, ChartType


class ChartRenderer:
    """
    Renders charts based on ChartConfig.
    
    This class is designed to be flexible and work in different contexts:
    - Embedded in a tkinter window with FigureCanvasTkAgg
    - Standalone matplotlib windows
    - PDF export via matplotlib's PDF backend
    
    Examples:
        # Basic usage with existing figure
        renderer = ChartRenderer(config)
        renderer.render(figure, canvas)
        
        # Create new figure and render
        fig, axes = renderer.create_and_render()
    """
    
    def __init__(self, config: ChartConfig):
        """
        Initialize the chart renderer with a configuration.
        
        Args:
            config: ChartConfig instance with all chart parameters
        """
        self.config = config
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration."""
        if self.config.data is None or self.config.data.empty:
            raise ValueError("ChartConfig must have non-empty data")
        
        if not self.config.primary_axis.series and not self.config.secondary_axis.series:
            raise ValueError("At least one series must be specified in primary or secondary axis")
    
    def render(
        self, 
        figure: Figure, 
        canvas: Optional[object] = None,
        clear_figure: bool = True
    ) -> Tuple[Axes, Optional[Axes]]:
        """
        Render the chart on an existing figure.
        
        Args:
            figure: Matplotlib Figure object to render on
            canvas: Optional canvas object (e.g., FigureCanvasTkAgg) to refresh
            clear_figure: Whether to clear the figure before rendering
        
        Returns:
            Tuple of (primary_axis, secondary_axis)
        """
        if clear_figure:
            figure.clear()
        
        # Create axes
        ax_left = figure.add_subplot(111)
        ax_right = ax_left.twinx() if self.config.secondary_axis.series else None
        
        # Render based on chart type
        if self.config.chart_type == "line":
            self._render_line_chart(ax_left, ax_right)
        elif self.config.chart_type == "bar":
            self._render_bar_chart(ax_left, ax_right)
        elif self.config.chart_type == "bubble":
            self._render_bubble_chart(ax_left, ax_right)
        else:
            raise ValueError(f"Unsupported chart type: {self.config.chart_type}")
        
        # Apply common formatting
        self._apply_formatting(ax_left, ax_right)
        
        # Finalize
        figure.tight_layout()
        if canvas:
            canvas.draw_idle()
        
        return ax_left, ax_right
    
    def create_and_render(
        self, 
        figsize: Tuple[int, int] = (10, 6),
        dpi: int = 100
    ) -> Tuple[Figure, Axes, Optional[Axes]]:
        """
        Create a new figure and render the chart.
        
        Args:
            figsize: Figure size in inches (width, height)
            dpi: Dots per inch for the figure
        
        Returns:
            Tuple of (figure, primary_axis, secondary_axis)
        """
        fig = Figure(figsize=figsize, dpi=dpi)
        ax_left, ax_right = self.render(fig, canvas=None, clear_figure=False)
        return fig, ax_left, ax_right
    
    def _render_line_chart(self, ax_left: Axes, ax_right: Optional[Axes]):
        """Render a line chart."""
        df = self.config.data
        x_key = self.config.get_x_column()
        
        # Plot primary series
        if self.config.primary_axis.series:
            for series_name in self.config.primary_axis.series:
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=False)
                    
                    if x_key:
                        ax_left.plot(
                            df[x_key], y, 
                            label=series_name,
                            linestyle=style.linestyle,
                            linewidth=style.linewidth,
                            marker=style.marker,
                            markersize=style.markersize,
                            color=style.color,
                            alpha=style.alpha
                        )
                    else:
                        ax_left.plot(
                            y.index, y, 
                            label=series_name,
                            linestyle=style.linestyle,
                            linewidth=style.linewidth,
                            marker=style.marker,
                            markersize=style.markersize,
                            color=style.color,
                            alpha=style.alpha
                        )
        
        # Plot secondary series
        if ax_right and self.config.secondary_axis.series:
            for series_name in self.config.secondary_axis.series:
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=True)
                    
                    if x_key:
                        ax_right.plot(
                            df[x_key], y, 
                            label=series_name,
                            linestyle=style.linestyle,
                            linewidth=style.linewidth,
                            marker=style.marker,
                            markersize=style.markersize,
                            color=style.color,
                            alpha=style.alpha
                        )
                    else:
                        ax_right.plot(
                            y.index, y, 
                            label=series_name,
                            linestyle=style.linestyle,
                            linewidth=style.linewidth,
                            marker=style.marker,
                            markersize=style.markersize,
                            color=style.color,
                            alpha=style.alpha
                        )
    
    def _render_bar_chart(self, ax_left: Axes, ax_right: Optional[Axes]):
        """Render a bar chart."""
        df = self.config.data
        x_key = self.config.get_x_column()
        
        # Calculate bar width and positions
        num_primary = len(self.config.primary_axis.series)
        num_secondary = len(self.config.secondary_axis.series) if ax_right else 0
        total_bars = num_primary + num_secondary
        bar_width = 0.8 / max(total_bars, 1)
        
        # Plot primary series
        if self.config.primary_axis.series:
            for i, series_name in enumerate(self.config.primary_axis.series):
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=False)
                    
                    if x_key:
                        x = df[x_key]
                    else:
                        x = y.index
                    
                    offset = (i - num_primary / 2) * bar_width
                    ax_left.bar(
                        x + offset, y,
                        width=bar_width,
                        label=series_name,
                        color=style.color,
                        alpha=style.alpha
                    )
        
        # Plot secondary series
        if ax_right and self.config.secondary_axis.series:
            for i, series_name in enumerate(self.config.secondary_axis.series):
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=True)
                    
                    if x_key:
                        x = df[x_key]
                    else:
                        x = y.index
                    
                    offset = ((i + num_primary) - total_bars / 2) * bar_width
                    ax_right.bar(
                        x + offset, y,
                        width=bar_width,
                        label=series_name,
                        color=style.color,
                        alpha=style.alpha
                    )
    
    def _render_bubble_chart(self, ax_left: Axes, ax_right: Optional[Axes]):
        """Render a bubble chart (scatter plot with variable size)."""
        df = self.config.data
        x_key = self.config.get_x_column()
        
        # For bubble charts, we'll use scatter plots
        # The marker size can be controlled via series_styles
        
        # Plot primary series
        if self.config.primary_axis.series:
            for series_name in self.config.primary_axis.series:
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=False)
                    
                    if x_key:
                        x = df[x_key]
                    else:
                        x = y.index
                    
                    ax_left.scatter(
                        x, y,
                        label=series_name,
                        s=style.markersize ** 2,  # scatter uses area, not radius
                        marker='o' if not style.marker else style.marker,
                        color=style.color,
                        alpha=style.alpha
                    )
        
        # Plot secondary series
        if ax_right and self.config.secondary_axis.series:
            for series_name in self.config.secondary_axis.series:
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=True)
                    
                    if x_key:
                        x = df[x_key]
                    else:
                        x = y.index
                    
                    ax_right.scatter(
                        x, y,
                        label=series_name,
                        s=style.markersize ** 2,
                        marker='o' if not style.marker else style.marker,
                        color=style.color,
                        alpha=style.alpha
                    )
    
    def _apply_formatting(self, ax_left: Axes, ax_right: Optional[Axes]):
        """Apply formatting to the axes."""
        # Axis labels
        primary_label = self.config.get_axis_label(self.config.primary_axis)
        ax_left.set_ylabel(primary_label)
        
        if ax_right:
            secondary_label = self.config.get_axis_label(self.config.secondary_axis)
            ax_right.set_ylabel(secondary_label)
        
        # X-axis label
        x_key = self.config.get_x_column()
        x_label = self.config.x_label if self.config.x_label else (x_key if x_key else "Index")
        ax_left.set_xlabel(x_label)
        
        # Title
        ax_left.set_title(self.config.title)
        
        # Grid
        if self.config.grid:
            ax_left.grid(
                True, 
                linestyle=self.config.grid_style, 
                linewidth=self.config.grid_linewidth
            )
        
        # Legends
        if self.config.show_legend:
            if self.config.primary_axis.series:
                ax_left.legend(loc=self.config.primary_legend_loc)
            if ax_right and self.config.secondary_axis.series:
                ax_right.legend(loc=self.config.secondary_legend_loc)
        
        # Apply axis limits
        if not self.config.primary_axis.auto_scale:
            ymin = self.config.primary_axis.min_value
            ymax = self.config.primary_axis.max_value
            if ymin is not None or ymax is not None:
                ax_left.set_ylim(bottom=ymin, top=ymax)
        
        if ax_right and not self.config.secondary_axis.auto_scale:
            ymin = self.config.secondary_axis.min_value
            ymax = self.config.secondary_axis.max_value
            if ymin is not None or ymax is not None:
                ax_right.set_ylim(bottom=ymin, top=ymax)
