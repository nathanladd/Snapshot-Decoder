"""
Chart widget for displaying matplotlib plots in PySide6.
"""

from typing import Optional, List, Dict

import pandas as pd

from PySide6.QtWidgets import QWidget, QVBoxLayout, QToolBar
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter
import mplcursors

from domain.snapshot import Snapshot
from domain.chart_config import ChartConfig, AxisConfig
from domain.quick_charts import QUICK_CHART_REGISTRY, ChartConfigBuilder
from infrastructure import log_chart_generated, debug
from ui.color_manager import ColorManager
from ui.chart_renderer import ChartRenderer
from ui_pyside6.widgets.custom_toolbar import CustomNavigationToolbar
from ui_pyside6.widgets.live_values_widget import LiveValuesWidget
from ui_pyside6.widgets.expandable_panel import ExpandablePanel
from ui_pyside6.widgets.log_console_dock import LogConsoleDock
from ui_pyside6.widgets.chart_cart_dock import ChartCartDock
from ui_pyside6.widgets.help_browser_dock import HelpBrowserDock
from ui_pyside6.widgets.help_tooltip import HelpEventFilter
from ui_pyside6.widgets.debug_settings_dialog import DebugSettingsDialog
from ui_pyside6.widgets.enhanced_time_slider import EnhancedTimeSlider


def _format_time_mmss(seconds, pos):
    """Format seconds as MM:SS for x-axis labels."""
    if pd.isna(seconds):
        return ""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


class ChartWidget(QWidget):
    """Widget for displaying charts with matplotlib."""
    
    # Signal emitted when user clicks "Add to Cart" on toolbar
    add_to_cart_requested = Signal()
    
    # Signal emitted when user clicks "Pop Out" on toolbar
    pop_out_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._snapshot: Optional[Snapshot] = None
        self._current_config: Optional[ChartConfig] = None
        self._current_action_id: Optional[str] = None  # Track if showing a quick chart
        
        # Value display state
        self._value_display_enabled = False
        self._mpl_cursor = None
        
        # Time slider state
        self._time_slider_enabled = False
        self._slider = None
        self._cursor_line = None
        
        # Live values display
        self._live_values_widget = None
        
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
        self._toolbar.add_to_cart_requested.connect(self.add_to_cart_requested.emit)
        self._toolbar.pop_out_requested.connect(self.pop_out_requested.emit)
        self._toolbar.value_display_changed.connect(self._on_value_display_changed)
        self._toolbar.time_slider_changed.connect(self._on_time_slider_changed)
        layout.addWidget(self._toolbar)
        
        # Canvas
        layout.addWidget(self._canvas, stretch=1)
        
        # Live values display (initially hidden)
        self._live_values_widget = LiveValuesWidget(self)
        layout.addWidget(self._live_values_widget)
        
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
    
    def get_current_axis_limits(self) -> Optional[Dict[str, float]]:
        """Get the current axis limits from the rendered chart."""
        if not self._ax:
            return None
        
        limits = {
            'primary_min': self._ax.get_ylim()[0],
            'primary_max': self._ax.get_ylim()[1],
        }
        
        if self._ax_secondary:
            limits.update({
                'secondary_min': self._ax_secondary.get_ylim()[0],
                'secondary_max': self._ax_secondary.get_ylim()[1],
            })
        
        return limits
    
    def _on_value_display_changed(self, enabled: bool):
        """Handle value display toggle change."""
        self._value_display_enabled = enabled
        if enabled:
            self._enable_value_display()
        else:
            self._disable_value_display()
    
    def _enable_value_display(self):
        """Enable hover value display on the chart."""
        if not self._current_config or self._current_config.data is None or self._current_config.data.empty:
            return
        
        # Clear existing cursor
        self._disable_value_display()
        
        # Collect all plot artists (lines, containers, collections)
        artists = []
        if self._ax:
            artists.extend(self._ax.lines)
            artists.extend(self._ax.containers)
            artists.extend(self._ax.collections)
        if self._ax_secondary:
            artists.extend(self._ax_secondary.lines)
            artists.extend(self._ax_secondary.containers)
            artists.extend(self._ax_secondary.collections)
        
        if artists:
            self._mpl_cursor = mplcursors.cursor(artists, hover=True)
            
            @self._mpl_cursor.connect("add")
            def on_add(sel):
                try:
                    # Get the data point
                    x, y = sel.target
                    label = sel.artist.get_label()
                    
                    # Format the display text
                    if self._current_config and self._current_config.x_column:
                        x_label = self._current_config.x_column
                    else:
                        x_label = "X"
                    
                    # Format based on chart type
                    if self._current_config and self._current_config.chart_type == "status":
                        # For status charts, show On/Off
                        y_text = "On" if y >= 0.5 else "Off"
                    else:
                        # For other charts, show numeric value
                        y_text = f"{y:.3f}"
                    
                    # Format x value (time if available)
                    if self._current_config and "Time" in str(x):
                        # Format as MM:SS if it looks like time
                        try:
                            mins = int(x // 60)
                            secs = int(x % 60)
                            x_text = f"{mins:02d}:{secs:02d}"
                        except:
                            x_text = f"{x:.2f}"
                    else:
                        x_text = f"{x:.2f}"
                    
                    sel.annotation.set_text(f"{label}\n{x_label}: {x_text}\nValue: {y_text}")
                    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
                    
                except Exception as e:
                    # Fallback to simple display
                    sel.annotation.set_text(f"{x:.2f}, {y:.3f}")
                    sel.annotation.get_bbox_patch().set(fc="white", alpha=0.9)
    
    def _disable_value_display(self):
        """Disable hover value display."""
        if self._mpl_cursor:
            try:
                self._mpl_cursor.remove()
            except Exception:
                pass
            self._mpl_cursor = None
    
    def _on_time_slider_changed(self, enabled: bool):
        """Handle time slider toggle change."""
        self._time_slider_enabled = enabled
        if enabled:
            self._enable_time_slider()
        else:
            self._disable_time_slider()
        
        # Show/hide live values display
        if self._live_values_widget:
            if enabled and self._current_config:
                self._live_values_widget.update_chart_config(self._current_config)
                self._live_values_widget.show_widget()
            else:
                self._live_values_widget.hide_widget()
    
    def _enable_time_slider(self):
        """Enable time slider and vertical cursor."""
        if not self._current_config or self._current_config.data is None or self._current_config.data.empty:
            return
        
        # Clear existing slider and cursor
        self._disable_time_slider()
        
        # Get the current x-axis limits from the chart
        if not self._ax:
            return
        
        # Get the actual x-axis range that's displayed on the chart
        xlim = self._ax.get_xlim()
        min_val = float(xlim[0])
        max_val = float(xlim[1])
        
        # Make room for slider
        try:
            self._figure.subplots_adjust(bottom=0.2)
        except Exception:
            pass
        
        # Create standard slider and enhance it
        from matplotlib.widgets import Slider
        ax_slider = self._figure.add_axes([0.15, 0.08, 0.7, 0.04])  # Slightly larger and better positioned
        self._slider = Slider(ax_slider, 'Time', min_val, max_val, valinit=min_val, color='lightgray')
        
        # Enhance the slider with better visual appearance (time display optional)
        from ui_pyside6.widgets.enhanced_time_slider import enhance_slider
        import numpy as np
        try:
            enhance_slider(self._slider, show_time_display=True)
        except Exception as e:
            print(f"Warning: Could not enhance slider: {e}")
            # At least try to enhance the appearance manually with aggressive styling
            if hasattr(self._slider, 'poly'):
                self._slider.poly.set_facecolor('red')
                self._slider.poly.set_edgecolor('darkred')
                self._slider.poly.set_linewidth(4)  # Thicker border
                self._slider.poly.set_alpha(1.0)    # Fully opaque
                # Try to make it larger
                try:
                    verts = self._slider.poly.get_xy()
                    if len(verts) > 0:
                        center_x = np.mean(verts[:, 0])
                        center_y = np.mean(verts[:, 1])
                        width = verts[:, 0].max() - verts[:, 0].min()
                        height = verts[:, 1].max() - verts[:, 1].min()
                        new_width = width * 3.0
                        new_height = height * 2.5
                        new_verts = [
                            [center_x - new_width/2, center_y - new_height/2],
                            [center_x + new_width/2, center_y - new_height/2],
                            [center_x + new_width/2, center_y + new_height/2],
                            [center_x - new_width/2, center_y + new_height/2]
                        ]
                        self._slider.poly.set_xy(new_verts)
                        self._slider.poly.set_zorder(10)
                except Exception:
                    pass
        
        # Create vertical cursor line
        self._cursor_line = self._ax.axvline(x=min_val, color='red', alpha=0.5, linestyle='--')
        
        # Update cursor position when slider changes
        def update(val):
            if self._cursor_line:
                self._cursor_line.set_xdata([val, val])
                
                # Update live values display
                if self._live_values_widget and self._live_values_widget.isVisible():
                    self._live_values_widget.update_values(val)
                
                self._canvas.draw_idle()
        
        self._slider.on_changed(update)
        self._canvas.draw()
    
    def _disable_time_slider(self):
        """Disable time slider and vertical cursor."""
        if self._slider:
            try:
                self._slider.ax.remove()
            except Exception:
                pass
            self._slider = None
        
        if self._cursor_line:
            try:
                self._cursor_line.remove()
            except Exception:
                pass
            self._cursor_line = None
        
        # Reset figure layout
        try:
            self._figure.subplots_adjust(bottom=0.1)
        except Exception:
            pass
        
        self._canvas.draw()
    
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
            pid_info=snapshot.pid_info,  # Add pid_info to config
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
        
        # Add "Reference: " prefix for reference charts
        title = config.title
        if config.quick_chart_action_id and config.quick_chart_action_id.startswith("REF_"):
            title = f"Reference: {title}"
        
        # Use ChartRenderer for consistent rendering with ColorManager
        renderer = ChartRenderer(config)
        ax_left, ax_right = renderer.render(self._figure, self._canvas)
        
        # Update title for reference charts
        if config.quick_chart_action_id and config.quick_chart_action_id.startswith("REF_"):
            ax_left.set_title(title)
        
        # Store the axes for reference
        self._ax = ax_left
        self._ax_secondary = ax_right
        
        # Update live values display when chart config changes
        if self._live_values_widget and self._time_slider_enabled:
            self._live_values_widget.update_chart_config(config)
        
        # Re-enable features if they were active
        if self._value_display_enabled:
            self._enable_value_display()
        if self._time_slider_enabled:
            self._enable_time_slider()
    
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
    
    def get_live_values_widget(self):
        """Get the live values widget for debug settings updates."""
        return self._live_values_widget
