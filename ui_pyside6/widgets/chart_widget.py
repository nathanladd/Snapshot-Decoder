"""
Chart widget for displaying matplotlib plots in PySide6.
"""

from typing import Optional, List, Dict

import pandas as pd

from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from domain.snapshot import Snapshot
from domain.chart_config import ChartConfig, AxisConfig
from domain.quick_charts import QUICK_CHART_REGISTRY, ChartConfigBuilder
from infrastructure import log_chart_generated, debug
from ui.color_manager import ColorManager
from ui.chart_renderer import ChartRenderer
from ui_pyside6.widgets.custom_toolbar import CustomNavigationToolbar


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
        self._current_config: Optional[ChartConfig] = None
        self._current_action_id: Optional[str] = None  # Track if showing a quick chart
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
        
        # Custom navigation toolbar with PDF export
        self._toolbar = CustomNavigationToolbar(self._canvas, self)
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
        self._current_config = None
        self._current_action_id = None
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
        secondary_pids: List[str],
        axis_settings: Optional[Dict] = None
    ):
        """Plot selected PIDs from the snapshot."""
        self._snapshot = snapshot
        df = snapshot.snapshot
        
        if df is None:
            return
        
        # Clear and recreate axes
        self._figure.clear()
        self._ax = self._figure.add_subplot(111)
        self._ax_secondary = None
        
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
        
        # Apply axis limits from settings
        if axis_settings:
            if not axis_settings.get('primary_auto', True):
                p_min = axis_settings.get('primary_min')
                p_max = axis_settings.get('primary_max')
                if p_min is not None or p_max is not None:
                    self._ax.set_ylim(bottom=p_min, top=p_max)
            
            if self._ax_secondary and not axis_settings.get('secondary_auto', True):
                s_min = axis_settings.get('secondary_min')
                s_max = axis_settings.get('secondary_max')
                if s_min is not None or s_max is not None:
                    self._ax_secondary.set_ylim(bottom=s_min, top=s_max)
        
        # Legends
        if primary_pids:
            self._ax.legend(loc='upper left')
        if secondary_pids and self._ax_secondary:
            self._ax_secondary.legend(loc='upper right')
        
        self._ax.grid(True, linestyle=':', alpha=0.7)
        self._figure.tight_layout()
        self._canvas.draw()
    
    def get_current_axis_limits(self) -> Optional[Dict]:
        """Get the current axis limits from the chart."""
        if self._ax is None:
            return None
        
        try:
            p_min, p_max = self._ax.get_ylim()
            result = {
                'primary_min': round(p_min, 4),
                'primary_max': round(p_max, 4),
                'secondary_min': None,
                'secondary_max': None,
            }
            
            if self._ax_secondary:
                s_min, s_max = self._ax_secondary.get_ylim()
                result['secondary_min'] = round(s_min, 4)
                result['secondary_max'] = round(s_max, 4)
            
            return result
        except Exception:
            return None
    
    def plot_quick_chart(self, snapshot: Snapshot, action_id: str):
        """Plot a quick chart by action ID."""
        self._snapshot = snapshot
        self._current_action_id = action_id
        
        debug(f"Plotting quick chart: {action_id}")
        
        # Get chart definition from registry
        definition = QUICK_CHART_REGISTRY.get(action_id)
        if not definition:
            debug(f"Unknown chart action ID: {action_id}")
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
        self._current_config = config
        
        # Log chart generation for audit trail
        all_pids = []
        if config.primary_axis.series:
            all_pids.extend(config.primary_axis.series)
        if config.secondary_axis.series:
            all_pids.extend(config.secondary_axis.series)
        
        log_chart_generated(
            chart_type=config.chart_type,
            pids=all_pids,
            snapshot_file=snapshot.file_name
        )
        
        debug(f"Generated {config.chart_type} chart with {len(all_pids)} PIDs")
        
        # Render based on chart type
        self._render_config(config)
    
    def get_current_config(self) -> Optional[ChartConfig]:
        """Get the current chart configuration."""
        return self._current_config
    
    def get_current_primary_pids(self) -> List[str]:
        """Get PIDs currently on primary axis."""
        if self._current_config:
            return list(self._current_config.primary_axis.series)
        return []
    
    def get_current_secondary_pids(self) -> List[str]:
        """Get PIDs currently on secondary axis."""
        if self._current_config:
            return list(self._current_config.secondary_axis.series)
        return []
    
    def update_chart(
        self,
        snapshot: Snapshot,
        primary_pids: List[str],
        secondary_pids: List[str],
        axis_settings: Optional[Dict] = None
    ):
        """Update the current chart with new PIDs and settings."""
        self._snapshot = snapshot
        df = snapshot.snapshot
        
        if df is None:
            return
        
        # Get relevant columns
        x_key = "Time" if "Time" in df.columns else ("Frame" if "Frame" in df.columns else None)
        relevant_columns = list(primary_pids) + list(secondary_pids)
        if x_key:
            relevant_columns.insert(0, x_key)
        
        # Filter to existing columns
        relevant_columns = [c for c in relevant_columns if c in df.columns]
        chart_data = df[relevant_columns].copy() if relevant_columns else pd.DataFrame()
        
        # Build axis configs
        primary_axis = AxisConfig(
            series=list(primary_pids),
            auto_scale=axis_settings.get('primary_auto', True) if axis_settings else True,
            min_value=axis_settings.get('primary_min') if axis_settings else None,
            max_value=axis_settings.get('primary_max') if axis_settings else None,
        )
        
        secondary_axis = AxisConfig(
            series=list(secondary_pids),
            auto_scale=axis_settings.get('secondary_auto', True) if axis_settings else True,
            min_value=axis_settings.get('secondary_min') if axis_settings else None,
            max_value=axis_settings.get('secondary_max') if axis_settings else None,
        )
        
        # Preserve title from current config if it exists, otherwise use default
        title = "Chart"
        if self._current_config and self._current_config.title:
            title = self._current_config.title
        
        # Create new config
        self._current_config = ChartConfig(
            data=chart_data,
            chart_type="line",
            primary_axis=primary_axis,
            secondary_axis=secondary_axis,
            title=title,
            x_column=x_key,
        )
        
        # Clear quick chart tracking since we're modifying
        self._current_action_id = None
        
        # Render the updated config
        self._render_config(self._current_config)
    
    def get_current_config(self) -> Optional[ChartConfig]:
        """Get the current chart configuration."""
        return self._current_config
    
    def _render_config(self, config: ChartConfig):
        """Render a ChartConfig using ChartRenderer."""
        # Update toolbar with current config for PDF export
        self._toolbar.set_chart_config(config)
        
        # Use ChartRenderer for consistent rendering with ColorManager
        renderer = ChartRenderer(config)
        ax_left, ax_right = renderer.render(self._figure, self._canvas)
        
        # Store the axes for reference
        self._ax = ax_left
        self._ax_secondary = ax_right
    
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
        
        # Apply axis limits
        if not config.primary_axis.auto_scale:
            if config.primary_axis.min_value is not None and config.primary_axis.max_value is not None:
                self._ax.set_ylim(config.primary_axis.min_value, config.primary_axis.max_value)
        
        if self._ax_secondary and not config.secondary_axis.auto_scale:
            if config.secondary_axis.min_value is not None and config.secondary_axis.max_value is not None:
                self._ax_secondary.set_ylim(config.secondary_axis.min_value, config.secondary_axis.max_value)
        
        # Legends
        if config.show_legend:
            if config.primary_axis.series:
                self._ax.legend(loc=config.primary_legend_loc)
            if config.secondary_axis.series and self._ax_secondary:
                self._ax_secondary.legend(loc=config.secondary_legend_loc)
    
    def _render_status_chart(self, config: ChartConfig, x_data):
        """Render a status chart with step-style lines for binary values."""
        df = config.data
        
        # Plot primary axis with step style for binary status values
        for pid in config.primary_axis.series:
            if pid in df.columns:
                y_data = pd.to_numeric(df[pid], errors='coerce')
                label = self._get_pid_label(self._snapshot, pid) if self._snapshot else pid
                self._ax.step(x_data, y_data, label=label, where='post')
        
        self._ax.set_ylabel(config.get_axis_label(config.primary_axis))
        
        # Set Y-axis for binary status (0/1) with padding
        if config.primary_axis.auto_scale:
            self._ax.set_ylim(-0.1, 1.1)
        else:
            if config.primary_axis.min_value is not None and config.primary_axis.max_value is not None:
                self._ax.set_ylim(config.primary_axis.min_value, config.primary_axis.max_value)
        
        # Apply custom ticks if specified
        if config.primary_axis.ticks is not None:
            self._ax.set_yticks(config.primary_axis.ticks)
            if config.primary_axis.tick_labels:
                self._ax.set_yticklabels(config.primary_axis.tick_labels)
        else:
            # Default to 0/1 ticks for status charts
            self._ax.set_yticks([0, 1])
            self._ax.set_yticklabels(["Off", "On"])
        
        # Legends
        if config.show_legend:
            self._ax.legend(loc=config.primary_legend_loc)
    
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
