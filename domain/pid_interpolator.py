"""
PID Value Interpolator

Calculates PID values at any given time/frame position using linear interpolation.
Works with ChartConfig data to provide accurate values for the time slider.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
import time

from domain.chart_config import ChartConfig
from infrastructure import debug, error
from pid_debug_config import get_pid_debug_setting, get_log_interval, get_log_on_stop, get_position_threshold


class PIDInterpolator:
    """Interpolates PID values at specific positions in the data."""
    
    def __init__(self, enable_debug_logging: bool = None):
        self._cache = {}  # Cache for repeated positions
        self._cache_size_limit = 1000
        # Use config file setting if not explicitly specified
        if enable_debug_logging is None:
            self._debug_logging = get_pid_debug_setting()
        else:
            self._debug_logging = enable_debug_logging
        
        # Rate limiting for debug logs
        self._last_log_time = 0
        self._log_interval = get_log_interval()
        self._last_position = None
        self._log_on_stop = get_log_on_stop()
        self._position_threshold = get_position_threshold()
    
    def set_debug_logging(self, enabled: bool):
        """Enable or disable debug logging for PID interpolation."""
        self._debug_logging = enabled
    
    def _should_log(self, x_position: float) -> bool:
        """Check if we should log based on rate limiting and position changes."""
        if not self._debug_logging:
            return False
        
        current_time = time.time()
        
        # Always log if this is the first time or position changed significantly
        if self._last_position is None:
            self._last_position = x_position
            self._last_log_time = current_time
            return True
        
        # Check if position changed (slider is moving)
        position_changed = abs(x_position - self._last_position) > self._position_threshold
        self._last_position = x_position
        
        # Log if:
        # 1. Enough time has passed since last log, OR
        # 2. Position changed and we want to log on stop
        time_elapsed = current_time - self._last_log_time
        
        if time_elapsed >= self._log_interval:
            self._last_log_time = current_time
            return True
        
        # If slider stopped moving (no significant change), log the final value
        if not position_changed and self._log_on_stop and time_elapsed >= 0.1:
            self._last_log_time = current_time
            return True
        
        return False
    
    def interpolate_values(self, config: ChartConfig, x_position: float) -> Dict[str, float]:
        """
        Interpolate PID values at a specific X position.
        
        Args:
            config: ChartConfig containing data and axis information
            x_position: X position (time in seconds or frame number)
            
        Returns:
            Dictionary mapping PID names to interpolated values
        """
        if not config or config.data.empty:
            return {}
        
        # Check cache first
        cache_key = self._get_cache_key(config, x_position)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Get X column
        x_col = config.get_x_column()
        if not x_col or x_col not in config.data.columns:
            return {}
        
        # Prepare data
        df = config.data.copy()
        
        # Convert timedelta if necessary (matching ChartRenderer logic)
        if pd.api.types.is_timedelta64_dtype(df.get("Time")):
            df["Time"] = df["Time"].dt.total_seconds()
        elif pd.api.types.is_timedelta64_dtype(df.get("Time (MM:SS)")):
            df["Time (MM:SS)"] = df["Time (MM:SS)"].dt.total_seconds()
            # Update x_col if we converted Time (MM:SS)
            if x_col == "Time (MM:SS)":
                x_col = "Time"
        
        # Sort by X column for proper interpolation
        df_sorted = df.sort_values(x_col)
        x_data = df_sorted[x_col].values
        
        # Check if position is within data range
        if x_position < x_data[0] or x_position > x_data[-1]:
            return self._handle_out_of_bounds(df_sorted, x_col, x_position, config)
        
        # Get all PID columns (exclude X column)
        pid_columns = []
        pid_columns.extend(config.primary_axis.series)
        pid_columns.extend(config.secondary_axis.series)
        
        # Filter to only existing columns
        pid_columns = [col for col in pid_columns if col in df_sorted.columns]
        
        if not pid_columns:
            return {}
        
        # Interpolate values
        interpolated = {}
        should_log = self._should_log(x_position)
        
        if should_log:
            debug(f"=== PID Interpolation Debug at X={x_position:.3f} ===")
        
        for pid in pid_columns:
            try:
                y_data = df_sorted[pid].values
                nan_count = pd.isna(y_data).sum()
                valid_count = len(y_data) - nan_count
                
                if should_log:
                    debug(f"PID: {pid}")
                    debug(f"  - Data shape: {y_data.shape}")
                    debug(f"  - Valid values: {valid_count}/{len(y_data)} (NaN: {nan_count})")
                    debug(f"  - Data type: {y_data.dtype}")
                    debug(f"  - Sample values: {y_data[:5]}")
                
                # Skip if all NaN
                if pd.isna(y_data).all():
                    if should_log:
                        debug(f"  - SKIPPED: All NaN values")
                    continue
                
                # Linear interpolation
                value = np.interp(x_position, x_data, y_data)
                
                # Check if result is reasonable
                if not np.isnan(value) and not np.isinf(value):
                    interpolated[pid] = float(value)
                    if should_log:
                        debug(f"  - SUCCESS: Interpolated value = {value}")
                else:
                    if should_log:
                        debug(f"  - FAILED: Invalid result = {value}")
                    error(f"PID interpolation failed for {pid}: Invalid result {value} at position {x_position}")
            except Exception as e:
                # Skip problematic columns
                if should_log:
                    debug(f"  - ERROR: {e}")
                error(f"PID interpolation error for {pid}: {e} at position {x_position}")
                continue
        
        if should_log:
            debug(f"=== Interpolation Complete: {len(interpolated)}/{len(pid_columns)} PIDs successful ===")
            debug("")  # Empty line for spacing
        
        # Cache result
        self._cache_result(cache_key, interpolated)
        
        return interpolated
    
    def _get_cache_key(self, config: ChartConfig, x_position: float) -> str:
        """Generate cache key for interpolation result."""
        # Use hash of data shape and X position for simple caching
        data_hash = hash((config.data.shape, tuple(config.primary_axis.series), 
                         tuple(config.secondary_axis.series)))
        return f"{data_hash}_{x_position:.6f}"
    
    def _cache_result(self, cache_key: str, result: Dict[str, float]):
        """Cache interpolation result with size limit."""
        if len(self._cache) >= self._cache_size_limit:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._cache.keys())[:100]
            for key in keys_to_remove:
                del self._cache[key]
        
        self._cache[cache_key] = result
    
    def _handle_out_of_bounds(self, df: pd.DataFrame, x_col: str, x_position: float, 
                            config: ChartConfig) -> Dict[str, float]:
        """Handle positions outside the data range."""
        x_data = df[x_col].values
        
        # Get all PID columns
        pid_columns = []
        pid_columns.extend(config.primary_axis.series)
        pid_columns.extend(config.secondary_axis.series)
        pid_columns = [col for col in pid_columns if col in df.columns]
        
        result = {}
        
        if x_position < x_data[0]:
            # Use first row values (extrapolate backward)
            first_row = df.iloc[0]
            for pid in pid_columns:
                value = first_row[pid]
                if not pd.isna(value):
                    result[pid] = float(value)
        else:
            # Use last row values (extrapolate forward)
            last_row = df.iloc[-1]
            for pid in pid_columns:
                value = last_row[pid]
                if not pd.isna(value):
                    result[pid] = float(value)
        
        return result
    
    def clear_cache(self):
        """Clear the interpolation cache."""
        self._cache.clear()
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get information about cache usage."""
        return {
            "cache_size": len(self._cache),
            "cache_limit": self._cache_size_limit
        }
