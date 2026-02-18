"""
PID Value Interpolator

Calculates PID values at any given time/frame position using linear interpolation.
Works with ChartConfig data to provide accurate values for the time slider.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, List
import time

from domain.chart_config import ChartConfig
from infrastructure import debug, error
from domain.pid_debug_config import get_pid_debug_setting, get_log_interval, get_log_on_stop, get_position_threshold


class PIDInterpolator:
    """Interpolates PID values at specific positions in the data."""
    
    def __init__(self, enable_debug_logging: bool = None):
        self._cache = {}  # Cache for repeated positions
        self._cache_size_limit = 1000
        self._x_sort_cache: Dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        self._x_sort_cache_limit = 8
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
    
    def interpolate_values(
        self,
        config: ChartConfig,
        x_position: float,
        extra_pids: Optional[List[str]] = None,
    ) -> Dict[str, float]:
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
        
        pid_columns = self._get_pid_columns(config, extra_pids)

        if not pid_columns:
            return {}

        # Check cache first
        cache_key = self._get_cache_key(config, x_position, pid_columns)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Get prepared X-axis data (cached by config/data identity)
        prepared = self._get_prepared_x_data(config)
        if prepared is None:
            return {}
        x_sorted, sort_idx, x_valid_mask = prepared
        if x_sorted.size == 0:
            return {}
        x_valid = x_sorted[x_valid_mask]
        if x_valid.size == 0:
            return {}

        # Interpolate values
        interpolated = {}
        should_log = self._should_log(x_position)
        started = time.perf_counter()

        if should_log:
            debug(f"=== PID Interpolation Debug at X={x_position:.3f} ===")

        for pid in pid_columns:
            try:
                y_data = pd.to_numeric(config.data[pid], errors='coerce').to_numpy()
                y_sorted = y_data[sort_idx]
                valid_mask = x_valid_mask & (~np.isnan(y_sorted))
                valid_count = int(np.count_nonzero(valid_mask))
                nan_count = int(y_sorted.size - valid_count)

                if should_log:
                    debug(f"PID: {pid}")
                    debug(f"  - Data shape: {y_sorted.shape}")
                    debug(f"  - Valid values: {valid_count}/{len(y_sorted)} (NaN: {nan_count})")
                    debug(f"  - Data type: {y_sorted.dtype}")
                    debug(f"  - Sample values: {y_sorted[:5]}")

                if valid_count == 0:
                    if should_log:
                        debug(f"  - SKIPPED: All NaN values")
                    continue

                y_valid = y_sorted[valid_mask]
                x_valid_for_pid = x_sorted[valid_mask]

                # Linear interpolation
                value = np.interp(x_position, x_valid_for_pid, y_valid)

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

        elapsed_ms = (time.perf_counter() - started) * 1000.0
        if should_log:
            debug(f"=== Interpolation Complete: {len(interpolated)}/{len(pid_columns)} PIDs successful ===")
            debug(f"Interpolation elapsed: {elapsed_ms:.3f} ms")
            debug("")  # Empty line for spacing
        
        # Cache result
        self._cache_result(cache_key, interpolated)
        
        return interpolated
    
    def _get_pid_columns(self, config: ChartConfig, extra_pids: Optional[List[str]]) -> List[str]:
        """Return de-duplicated, in-order PID columns that exist in chart data."""
        pid_columns: List[str] = []
        pid_columns.extend(config.primary_axis.series)
        pid_columns.extend(config.secondary_axis.series)
        if extra_pids:
            pid_columns.extend(extra_pids)

        seen: set[str] = set()
        filtered: List[str] = []
        for col in pid_columns:
            if col in seen:
                continue
            if col not in config.data.columns:
                continue
            seen.add(col)
            filtered.append(col)
        return filtered

    def _get_prepared_x_data(self, config: ChartConfig) -> Optional[tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """Cache sorted X-axis arrays reused across slider events for same chart data."""
        x_col = config.get_x_column()
        if not x_col or x_col not in config.data.columns:
            return None

        cache_key = self._get_x_cache_key(config, x_col)
        cached = self._x_sort_cache.get(cache_key)
        if cached is not None:
            return cached

        x_series = config.data[x_col]
        if pd.api.types.is_timedelta64_dtype(x_series):
            x_numeric = x_series.dt.total_seconds()
        else:
            x_numeric = pd.to_numeric(x_series, errors="coerce")

        x_data = x_numeric.to_numpy()
        sort_idx = np.argsort(x_data, kind="mergesort")
        x_sorted = x_data[sort_idx]
        x_valid_mask = ~np.isnan(x_sorted)
        prepared = (x_sorted, sort_idx, x_valid_mask)

        if len(self._x_sort_cache) >= self._x_sort_cache_limit:
            oldest_keys = list(self._x_sort_cache.keys())[:2]
            for old_key in oldest_keys:
                self._x_sort_cache.pop(old_key, None)
        self._x_sort_cache[cache_key] = prepared
        return prepared

    def _get_x_cache_key(self, config: ChartConfig, x_col: str) -> str:
        return (
            f"{id(config.data)}|{x_col}|{config.data.shape}|"
            f"{hash(tuple(map(str, config.data.columns)))}"
        )

    def _get_cache_key(self, config: ChartConfig, x_position: float, pid_columns: List[str]) -> str:
        """Generate cache key for interpolation result."""
        data_hash = hash(
            (
                id(config.data),
                config.data.shape,
                tuple(config.primary_axis.series),
                tuple(config.secondary_axis.series),
                tuple(pid_columns),
            )
        )
        return f"{data_hash}_{x_position:.6f}"
    
    def _cache_result(self, cache_key: str, result: Dict[str, float]):
        """Cache interpolation result with size limit."""
        if len(self._cache) >= self._cache_size_limit:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._cache.keys())[:100]
            for key in keys_to_remove:
                del self._cache[key]
        
        self._cache[cache_key] = result
    
    def clear_cache(self):
        """Clear the interpolation cache."""
        self._cache.clear()
        self._x_sort_cache.clear()
    
    def get_cache_info(self) -> Dict[str, int]:
        """Get information about cache usage."""
        return {
            "cache_size": len(self._cache),
            "cache_limit": self._cache_size_limit
        }
