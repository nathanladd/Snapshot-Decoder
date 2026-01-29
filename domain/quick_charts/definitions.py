"""
Declarative quick chart definitions - no UI references.

These dataclasses define what a chart should contain,
without any knowledge of how it will be displayed.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any


@dataclass
class QuickChartDef:
    """
    Declarative definition of a quick chart - no UI references.
    
    This represents a standard line/status chart configuration.
    For specialized charts (bar, bubble), use the subclasses.
    """
    action_id: str
    title: str
    primary_pids: List[str]
    primary_range: Optional[Tuple[float, float]] = None
    secondary_pids: List[str] = field(default_factory=list)
    secondary_range: Optional[Tuple[float, float]] = None
    chart_type: str = "line"
    show_legend: bool = True
    primary_ticks: Optional[List[float]] = None
    primary_tick_labels: Optional[List[str]] = None
    
    # For dynamic PID filtering (e.g., 3-cylinder vs 4-cylinder engines)
    dynamic_primary_pids: Optional[List[str]] = None
    
    # For status charts that need data preprocessing
    preprocess_func: Optional[str] = None


@dataclass
class BarChartDef(QuickChartDef):
    """
    Definition for bar charts built from specific columns.
    
    Bar charts extract single values (typically from Frame 0)
    and display them as categorical bars.
    """
    chart_type: str = "bar"
    
    # Column names to extract values from
    source_columns: List[str] = field(default_factory=list)
    
    # Labels for each bar (must match length of source_columns)
    bar_labels: List[str] = field(default_factory=list)
    
    # X-axis configuration
    x_label: str = ""
    y_label: str = "Hours"
    
    # Value transformation
    convert_seconds_to_hours: bool = True


@dataclass
class BubbleChartDef(QuickChartDef):
    """
    Definition for bubble charts (scatter with sized markers).
    
    Bubble charts show relationships between three variables:
    x position, y position, and marker size.
    """
    chart_type: str = "bubble"
    
    # Column pattern for extracting data (e.g., "EUD_Spdload_blm_timer_nvv[{speed},{load}]")
    column_pattern: Optional[str] = None
    
    # Axis mappings
    x_label: str = "Speed"
    y_label: str = "Load"
    size_label: str = "Percent"
    
    # Index to value mappings
    x_index_map: Optional[Dict[int, float]] = None
    y_index_map: Optional[Dict[int, float]] = None
    
    # Reference column for percentage calculation
    total_reference_column: Optional[str] = None


@dataclass 
class StatusChartDef(QuickChartDef):
    """
    Definition for status charts showing binary/categorical state over time.
    
    Status charts display multiple PIDs as stacked horizontal bands,
    showing on/off or categorical states.
    """
    chart_type: str = "status"
    show_legend: bool = True
    
    # For charts that parse multi-digit status columns
    source_column: Optional[str] = None
    digit_labels: Optional[List[str]] = None
    display_prefix: Optional[str] = None
