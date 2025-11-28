"""
Chart Configuration Data Classes

Defines data classes for configuring different types of charts (line, bar, bubble, status).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Literal
import pandas as pd

ChartType = Literal["line", "bar", "bubble", "status"]


@dataclass
class AxisConfig:
    """Configuration for a single axis (primary or secondary)."""
    series: List[str] = field(default_factory=list)
    label: str = ""
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    auto_scale: bool = True
    ticks: Optional[List[float]] = None
    tick_labels: Optional[List[str]] = None


@dataclass
class SeriesStyle:
    """Style configuration for a data series."""
    linestyle: str = "-"
    linewidth: float = 1.0
    marker: str = ""
    markersize: float = 6.0
    color: Optional[str] = None
    alpha: float = 1.0


@dataclass
class ChartConfig:
    """
    Configuration for creating charts with primary and secondary axes.
    
    This dataclass encapsulates all parameters needed to create different types
    of charts (line, status, bar, bubble) for use in various contexts (main window,
    separate window, or PDF export).
    """
    # Data
    data: pd.DataFrame
    
    # Chart type
    chart_type: ChartType = "line"
    
    # Axes configuration
    primary_axis: AxisConfig = field(default_factory=AxisConfig)
    secondary_axis: AxisConfig = field(default_factory=AxisConfig)
    
    # X-axis configuration
    x_column: Optional[str] = None  # If None, will auto-detect Time/Frame
    x_label: str = ""
    
    # Chart appearance
    title: str = "Chart"
    grid: bool = True
    grid_style: str = ":"
    grid_linewidth: float = 0.6
    
    # Legend
    show_legend: bool = True
    primary_legend_loc: str = "upper left"
    secondary_legend_loc: str = "upper right"
    
    # Series styles (optional per-series customization)
    series_styles: Dict[str, SeriesStyle] = field(default_factory=dict)
    
    # PID information (for unit labels)
    pid_info: Optional[Dict[str, Dict]] = None
    
    # Chain of custody metadata
    file_name: Optional[str] = None
    date_time: Optional[str] = None
    engine_hours: Optional[float] = None
    
    def get_x_column(self) -> Optional[str]:
        """Determine the X-axis column from data."""
        if self.x_column:
            return self.x_column
        
        # Auto-detect: prefer Time (MM:SS), then Time, then Frame
        if "Time (MM:SS)" in self.data.columns and pd.api.types.is_numeric_dtype(self.data["Time (MM:SS)"]):
            return "Time (MM:SS)"
        elif "Time" in self.data.columns and (pd.api.types.is_numeric_dtype(self.data["Time"]) or pd.api.types.is_datetime64_any_dtype(self.data["Time"]) or pd.api.types.is_timedelta64_dtype(self.data["Time"])):
            return "Time"
        elif "Frame" in self.data.columns and pd.api.types.is_numeric_dtype(self.data["Frame"]):
            return "Frame"
        
        return None
    
    def get_axis_label(self, axis_config: AxisConfig) -> str:
        """Get the label for an axis, using PID units if available."""
        if axis_config.label:
            return axis_config.label
        
        # Try to infer from PID info
        if self.pid_info:
            for pid_name in axis_config.series:
                info = self.pid_info.get(pid_name)
                unit = (info or {}).get("Unit") if info else None
                if unit:
                    return unit
        
        return "Value"
    
    def get_series_style(self, series_name: str, is_secondary: bool = False) -> SeriesStyle:
        """Get the style for a series, with defaults for secondary axis."""
        if series_name in self.series_styles:
            return self.series_styles[series_name]
        
        # Default styles
        if is_secondary:
            return SeriesStyle(linestyle="--")
        else:
            return SeriesStyle()
