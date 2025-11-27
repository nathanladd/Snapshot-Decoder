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
from matplotlib.ticker import FuncFormatter
from matplotlib import dates as mdates

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
    
    def _get_legend_label(self, pid_name: str) -> str:
        """
        Get the legend label for a PID, using its description from pid_info if available.
        
        Args:
            pid_name: The PID column name
            
        Returns:
            The PID description if available, otherwise the PID name
        """
        if self.config.pid_info and pid_name in self.config.pid_info:
            description = self.config.pid_info[pid_name].get("Description", "")
            if description:
                return description
        return pid_name
    
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
        
        # Prepare data: convert Timedelta to seconds for plotting
        plot_data = self.config.data.copy()
        if pd.api.types.is_timedelta64_dtype(plot_data.get("Time")):
            plot_data["Time"] = plot_data["Time"].dt.total_seconds()
        elif pd.api.types.is_timedelta64_dtype(plot_data.get("Time (MM:SS)")):
            plot_data["Time (MM:SS)"] = plot_data["Time (MM:SS)"].dt.total_seconds()
        
        # Create axes
        ax_left = figure.add_subplot(111)
        ax_right = ax_left.twinx() if self.config.secondary_axis.series else None
        
        # Render based on chart type
        if self.config.chart_type == "line":
            self._render_line_chart(ax_left, ax_right, plot_data)
        elif self.config.chart_type == "bar":
            self._render_bar_chart(ax_left, ax_right, plot_data)
        elif self.config.chart_type == "bubble":
            self._render_bubble_chart(ax_left, ax_right, plot_data)
        elif self.config.chart_type == "status":
            self._render_status_chart(ax_left, ax_right, plot_data)
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
    
    def render_thumbnail(self, figsize=(4, 2), dpi=50):
        """Render a small thumbnail of the chart."""
        fig = Figure(figsize=figsize, dpi=dpi)
        
        # Create axes
        ax_left = fig.add_subplot(111)
        ax_right = None
        if self.config.secondary_axis.series:
            ax_right = ax_left.twinx()
        
        # Render the chart
        if self.config.chart_type == "line":
            self._render_line_chart(ax_left, ax_right, self.config.data)
        elif self.config.chart_type == "bar":
            self._render_bar_chart(ax_left, ax_right, self.config.data)
        elif self.config.chart_type == "bubble":
            self._render_bubble_chart(ax_left, ax_right, self.config.data)
        elif self.config.chart_type == "status":
            self._render_status_chart(ax_left, ax_right, self.config.data)
        
        # Apply formatting (limits, grid, etc.)
        self._apply_formatting(ax_left, ax_right)
        
        # Apply formatting without labels/titles/legends for thumbnail
        ax_left.set_title("")
        ax_left.set_xlabel("")
        ax_left.set_ylabel("")
        legend = ax_left.get_legend()
        if legend:
            legend.remove()
        
        if ax_right:
            ax_right.set_ylabel("")
            legend = ax_right.get_legend()
            if legend:
                legend.remove()
        
        fig.tight_layout()
        
        # Re-apply axis limits after tight_layout to ensure they're preserved
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
        
        return fig
    
    def _render_status_chart(self, ax_left: Axes, ax_right: Optional[Axes], plot_data: pd.DataFrame):
        """Render a status chart (Gantt-style strip)."""
        df = plot_data
        x_key = self.config.get_x_column()
        
        # We typically only support primary axis for status charts because they stack vertically
        # But we'll support secondary if requested (it will just overlay, which might be messy)
        
        axes = [(ax_left, self.config.primary_axis)]
        if ax_right:
            axes.append((ax_right, self.config.secondary_axis))
            
        current_offset = 0
        
        for ax, axis_config in axes:
            if not axis_config.series:
                continue
                
            for i, series_name in enumerate(axis_config.series):
                if series_name in df.columns:
                    y_vals = pd.to_numeric(df[series_name], errors="coerce").fillna(0)
                    style = self.config.get_series_style(series_name, is_secondary=(ax == ax_right))
                                       
                    # Stack index
                    y_center = i * 1.5 + 0.5
                    
                    if x_key:
                        x = df[x_key]
                        
                        # Draw "OFF" blocks (value <= 0.5) - smaller and lighter
                        # Height: 0.2 (vs 0.8 for ON)
                        # Color: Light gray or derived from main color but very light
                        ax.fill_between(
                            x, 
                            y_center - 0.1, 
                            y_center + 0.1, 
                            where=(y_vals <= 0.5),
                            step='post',
                            color='lightgray',
                            alpha=0.5,
                            linewidth=0
                        )
                        
                        # Draw "ON" blocks
                        # We use fill_between to create blocks where y_vals > 0.5 (assuming 0/1 input)
                        # Top of block: y_center + 0.4
                        # Bottom of block: y_center - 0.4
                        
                        ax.fill_between(
                            x, 
                            y_center - 0.4, 
                            y_center + 0.4, 
                            where=(y_vals > 0.5),
                            step='post',
                            color=style.color,
                            alpha=style.alpha,
                            linewidth=0 # No border for blocks usually looks cleaner
                        )
                    else:
                        x = y_vals.index
                        
                        # Draw "OFF" blocks
                        ax.fill_between(
                            x, 
                            y_center - 0.1, 
                            y_center + 0.1, 
                            where=(y_vals <= 0.5),
                            step='post',
                            color='lightgray',
                            alpha=0.5,
                            linewidth=0
                        )
                        
                        # Draw "ON" blocks
                        ax.fill_between(
                            x, 
                            y_center - 0.4, 
                            y_center + 0.4, 
                            where=(y_vals > 0.5),
                            step='post',
                            color=style.color,
                            alpha=style.alpha,
                            linewidth=0
                        )

    def _render_line_chart(self, ax_left: Axes, ax_right: Optional[Axes], plot_data: pd.DataFrame):
        """Render a line chart."""
        df = plot_data
        x_key = self.config.get_x_column()
        
        # Plot primary series
        if self.config.primary_axis.series:
            for series_name in self.config.primary_axis.series:
                if series_name in df.columns:
                    y = pd.to_numeric(df[series_name], errors="coerce")
                    style = self.config.get_series_style(series_name, is_secondary=False)
                    
                    legend_label = self._get_legend_label(series_name)
                    if x_key:
                        ax_left.plot(
                            df[x_key], y, 
                            label=legend_label,
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
                            label=legend_label,
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
                    
                    legend_label = self._get_legend_label(series_name)
                    if x_key:
                        ax_right.plot(
                            df[x_key], y, 
                            label=legend_label,
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
                            label=legend_label,
                            linestyle=style.linestyle,
                            linewidth=style.linewidth,
                            marker=style.marker,
                            markersize=style.markersize,
                            color=style.color,
                            alpha=style.alpha
                        )

    def _render_bar_chart(self, ax_left: Axes, ax_right: Optional[Axes], plot_data: pd.DataFrame):
        """Render a bar chart."""
        df = plot_data
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
                    legend_label = self._get_legend_label(series_name)
                    ax_left.bar(
                        x + offset, y,
                        width=bar_width,
                        label=legend_label,
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
                    legend_label = self._get_legend_label(series_name)
                    ax_right.bar(
                        x + offset, y,
                        width=bar_width,
                        label=legend_label,
                        color=style.color,
                        alpha=style.alpha
                    )
    
    def _render_bubble_chart(self, ax_left: Axes, ax_right: Optional[Axes], plot_data: pd.DataFrame):
        """Render a bubble chart (scatter plot with variable size)."""
        df = plot_data
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
                    
                    legend_label = self._get_legend_label(series_name)
                    ax_left.scatter(
                        x, y,
                        label=legend_label,
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
                    
                    legend_label = self._get_legend_label(series_name)
                    ax_right.scatter(
                        x, y,
                        label=legend_label,
                        s=style.markersize ** 2,
                        marker='o' if not style.marker else style.marker,
                        color=style.color,
                        alpha=style.alpha
                    )
    
    def _apply_formatting(self, ax_left: Axes, ax_right: Optional[Axes]):
        """Apply formatting to the axes."""
        
        # For status charts, auto-calculate Y-axis limits and tick positions
        # based on the number of series (using 1.5 spacing per series)
        if self.config.chart_type == "status":
            self._apply_status_chart_formatting(ax_left)
        
        # Axis labels
        primary_label = self.config.get_axis_label(self.config.primary_axis)
        
        # For status charts, we usually don't want the generic "Value" label on the Y-axis
        # as the tick labels themselves explain what the rows are.
        if self.config.chart_type == "status" and primary_label == "Value":
             primary_label = ""
             
        ax_left.set_ylabel(primary_label)
        
        if ax_right:
            secondary_label = self.config.get_axis_label(self.config.secondary_axis)
            if self.config.chart_type == "status" and secondary_label == "Value":
                secondary_label = ""
            ax_right.set_ylabel(secondary_label)
        
        # X-axis label
        x_key = self.config.get_x_column()
        if x_key == "Time":
            x_label = "Time (mm:ss)"
        else:
            x_label = self.config.x_label if self.config.x_label else (x_key if x_key else "Index")
        ax_left.set_xlabel(x_label)
        
        # X-axis formatter for Time
        if x_key in ["Time", "Time (MM:SS)"]:
            def format_time(x, pos):
                minutes = int(x // 60)
                seconds = int(x % 60)
                return f"{minutes:02d}:{seconds:02d}"
            ax_left.xaxis.set_major_formatter(FuncFormatter(format_time))
        
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

        # Apply custom ticks and labels
        if self.config.primary_axis.ticks:
            ax_left.set_yticks(self.config.primary_axis.ticks)
        if self.config.primary_axis.tick_labels:
            ax_left.set_yticklabels(self.config.primary_axis.tick_labels)
            
        if ax_right:
            if self.config.secondary_axis.ticks:
                ax_right.set_yticks(self.config.secondary_axis.ticks)
            if self.config.secondary_axis.tick_labels:
                ax_right.set_yticklabels(self.config.secondary_axis.tick_labels)
    
    def _apply_status_chart_formatting(self, ax: Axes):
        """
        Auto-calculate and apply Y-axis limits and tick positions for status charts.
        Uses 1.5 spacing per series, with ticks centered at each strip.
        """
        num_series = len(self.config.primary_axis.series)
        if num_series == 0:
            return
        
        offset_step = 1.5
        total_height = (num_series * offset_step) + 0.5
        
        # Set Y-axis limits
        ax.set_ylim(bottom=-0.5, top=total_height)
        
        # Calculate tick positions (centered on each strip)
        tick_positions = [(i * offset_step) + 0.5 for i in range(num_series)]
        ax.set_yticks(tick_positions)
        
        # Use series names as tick labels (strip prefix if present)
        tick_labels = []
        for name in self.config.primary_axis.series:
            # Remove category prefix (e.g., "Torque Limit:_" -> just the name after)
            if ":_" in name:
                label = name.split(":_", 1)[1]
            else:
                label = name
            tick_labels.append(label)
        
        ax.set_yticklabels(tick_labels)
