"""
Time column processing logic.

Handles conversion of time values to proper formats and extraction
of time-based metrics like engine hours and idle time.
"""

from typing import Dict, Optional
import pandas as pd

from domain.snaptypes import SnapType
from domain.constants import ENGINE_HOURS_COLUMNS


def process_time_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the Time column to seconds (float).
    
    Args:
        df: DataFrame with a 'Time' column
        
    Returns:
        DataFrame with Time column converted to seconds
    """
    if "Time" not in df.columns:
        return df
    
    df["Time"] = pd.to_numeric(df["Time"], errors="coerce")
    df["Time"] = pd.to_timedelta(df["Time"], unit="s")
    df["Time"] = df["Time"].dt.total_seconds()
    
    return df


def find_engine_hours(
    df: pd.DataFrame, 
    snapshot_type: SnapType,
    pid_info: Dict[str, Dict[str, str]]
) -> float:
    """
    Find the engine hours from the snapshot.
    
    Reads the appropriate column based on snapshot type,
    gets value at Frame == 0, and converts from seconds to hours if needed.
    
    Args:
        df: Cleaned snapshot DataFrame
        snapshot_type: Type of snapshot (determines which column to read)
        pid_info: PID metadata for unit information
        
    Returns:
        Engine hours as float rounded to tenth of an hour, or 0.0 if not found
    """
    column_name = ENGINE_HOURS_COLUMNS.get(snapshot_type)
    if not column_name:
        return 0.0
    
    if column_name not in df.columns:
        return 0.0
    
    if "Frame" not in df.columns:
        return 0.0
    
    frame_zero_rows = df[df["Frame"] == 0]
    if frame_zero_rows.empty:
        return 0.0
    
    # Get unit to determine if conversion is needed
    unit = ""
    if column_name in pid_info:
        unit = pid_info[column_name].get("Unit", "").lower()
    
    if "second" in unit:
        try:
            seconds = float(frame_zero_rows[column_name].iloc[0])
            return round(seconds / 3600, 1)
        except (ValueError, IndexError, TypeError):
            return 0.0
    else:
        try:
            return round(float(frame_zero_rows[column_name].iloc[0]), 1)
        except (ValueError, IndexError, TypeError):
            return 0.0


def find_idle_time(
    df: pd.DataFrame,
    pid_info: Dict[str, Dict[str, str]]
) -> float:
    """
    Find the engine idle time from the EUD_Engine_idle_time_nvv column.
    
    Args:
        df: Cleaned snapshot DataFrame
        pid_info: PID metadata for unit information
        
    Returns:
        Idle time as float rounded to tenth, or 0.0 if not found
    """
    column_name = "EUD_Engine_idle_time_nvv"
    
    if column_name not in df.columns:
        return 0.0
    
    if "Frame" not in df.columns:
        return 0.0
    
    frame_zero_rows = df[df["Frame"] == 0]
    if frame_zero_rows.empty:
        return 0.0
    
    unit = ""
    if column_name in pid_info:
        unit = pid_info[column_name].get("Unit", "").lower()
    
    if "second" in unit:
        try:
            seconds = float(frame_zero_rows[column_name].iloc[0])
            return round(seconds / 3600, 1)
        except (ValueError, IndexError, TypeError):
            return 0.0
    else:
        try:
            return round(float(frame_zero_rows[column_name].iloc[0]), 1)
        except (ValueError, IndexError, TypeError):
            return 0.0


def calculate_mdp_success(df: pd.DataFrame) -> float:
    """
    Calculate the MDP success rate from success/failure counters.
    
    Args:
        df: Cleaned snapshot DataFrame
        
    Returns:
        MDP success rate as percentage (0-100), or 0.0 if not calculable
    """
    success_col = "I_C_Mdp_nb_update_success_nvv"
    failure_col = "I_C_Mdp_nb_update_failure_nvv"
    
    if not (success_col in df.columns and failure_col in df.columns):
        return 0.0
    
    if "Frame" not in df.columns:
        return 0.0
    
    frame_zero_row = df[df["Frame"] == 0]
    if frame_zero_row.empty:
        return 0.0
    
    try:
        mdp_success = int(frame_zero_row[success_col].iloc[0])
        mdp_failure = int(frame_zero_row[failure_col].iloc[0])
        
        total_updates = mdp_failure + mdp_success
        if total_updates == 0:
            return 0.0
            
        return round((mdp_success / total_updates) * 100, 1)
    except (ValueError, IndexError, TypeError):
        return 0.0
