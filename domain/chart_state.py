"""
Chart State Management.

Centralized state management for chart configurations with explicit reset
capability to prevent memory/state retention issues.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from domain.chart_config import ChartConfig


@dataclass
class ChartState:
    """
    Manages all transient chart state with explicit reset capability.
    
    This class centralizes chart state that was previously scattered across
    main_app attributes, ensuring proper cleanup when loading new files or
    switching chart types.
    """
    
    # Current chart configuration
    config: Optional[ChartConfig] = None
    
    # Axis series selections
    primary_series: List[str] = field(default_factory=list)
    secondary_series: List[str] = field(default_factory=list)
    
    # Axis range settings
    primary_auto: bool = True
    primary_min: Optional[float] = None
    primary_max: Optional[float] = None
    secondary_auto: bool = True
    secondary_min: Optional[float] = None
    secondary_max: Optional[float] = None
    
    # Custom ticks (for status charts, etc.)
    primary_ticks: Optional[List[float]] = None
    primary_tick_labels: Optional[List[str]] = None
    
    # Chart type
    chart_type: str = "line"
    show_legend: bool = True
    
    # Active quick chart (if any)
    active_quick_chart_id: Optional[str] = None
    
    def reset(self) -> None:
        """
        Reset ALL transient state for a fresh chart.
        
        Call this when:
        - Loading a new snapshot file
        - Clearing the current chart completely
        """
        self.config = None
        self.primary_series = []
        self.secondary_series = []
        self.primary_auto = True
        self.primary_min = None
        self.primary_max = None
        self.secondary_auto = True
        self.secondary_min = None
        self.secondary_max = None
        self.primary_ticks = None
        self.primary_tick_labels = None
        self.chart_type = "line"
        self.show_legend = True
        self.active_quick_chart_id = None
    
    def reset_for_chart_type_change(self) -> None:
        """
        Reset state that doesn't transfer between chart types.
        
        Call this when switching from one quick chart to another,
        preserving some settings while clearing chart-type-specific ones.
        """
        self.primary_ticks = None
        self.primary_tick_labels = None
    
    def has_series(self) -> bool:
        """Check if any series are selected for plotting."""
        return bool(self.primary_series or self.secondary_series)
    
    def get_all_series(self) -> List[str]:
        """Get combined list of all selected series."""
        return self.primary_series + self.secondary_series
    
    def set_primary_range(self, min_val: Optional[float], max_val: Optional[float]) -> None:
        """Set primary axis range, disabling auto-scale if values provided."""
        self.primary_min = min_val
        self.primary_max = max_val
        self.primary_auto = min_val is None and max_val is None
    
    def set_secondary_range(self, min_val: Optional[float], max_val: Optional[float]) -> None:
        """Set secondary axis range, disabling auto-scale if values provided."""
        self.secondary_min = min_val
        self.secondary_max = max_val
        self.secondary_auto = min_val is None and max_val is None
    
    def apply_to_config(self, config: ChartConfig) -> ChartConfig:
        """
        Apply current state settings to a ChartConfig.
        
        This allows state modifications (axis ranges, series changes)
        to be applied to an existing config for re-rendering.
        """
        # Update axis series
        if self.primary_series:
            config.primary_axis.series = self.primary_series.copy()
        if self.secondary_series:
            config.secondary_axis.series = self.secondary_series.copy()
        
        # Update primary axis range
        config.primary_axis.auto_scale = self.primary_auto
        if not self.primary_auto:
            config.primary_axis.min_value = self.primary_min
            config.primary_axis.max_value = self.primary_max
        
        # Update secondary axis range
        config.secondary_axis.auto_scale = self.secondary_auto
        if not self.secondary_auto:
            config.secondary_axis.min_value = self.secondary_min
            config.secondary_axis.max_value = self.secondary_max
        
        # Update custom ticks
        if self.primary_ticks is not None:
            config.primary_axis.ticks = self.primary_ticks
            config.primary_axis.tick_labels = self.primary_tick_labels
        
        # Update display settings
        config.chart_type = self.chart_type
        config.show_legend = self.show_legend
        
        return config
    
    def load_from_config(self, config: ChartConfig) -> None:
        """
        Load state from an existing ChartConfig.
        
        Used when a quick chart provides a config and we need to
        sync the state with it.
        """
        self.config = config
        self.primary_series = config.primary_axis.series.copy()
        self.secondary_series = config.secondary_axis.series.copy()
        
        self.primary_auto = config.primary_axis.auto_scale
        self.primary_min = config.primary_axis.min_value
        self.primary_max = config.primary_axis.max_value
        
        self.secondary_auto = config.secondary_axis.auto_scale
        self.secondary_min = config.secondary_axis.min_value
        self.secondary_max = config.secondary_axis.max_value
        
        self.primary_ticks = config.primary_axis.ticks
        self.primary_tick_labels = config.primary_axis.tick_labels
        
        self.chart_type = config.chart_type
        self.show_legend = config.show_legend
        self.active_quick_chart_id = config.quick_chart_action_id
