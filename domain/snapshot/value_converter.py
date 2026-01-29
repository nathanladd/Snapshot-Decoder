"""
Value conversion logic for specific PIDs.

Handles type-specific conversions like millivolts to volts,
and PID-specific unit updates.
"""

from typing import Dict
import pandas as pd

from domain.snaptypes import SnapType


def apply_type_specific_conversions(
    df: pd.DataFrame,
    snapshot_type: SnapType,
    pid_info: Dict[str, Dict[str, str]]
) -> pd.DataFrame:
    """
    Apply snapshot-type-specific value conversions.
    
    Args:
        df: Cleaned snapshot DataFrame
        snapshot_type: Type of snapshot
        pid_info: PID metadata dictionary (may be modified)
        
    Returns:
        DataFrame with conversions applied
    """
    if snapshot_type == SnapType.ECU_V1:
        _update_v1_engine_state_unit(pid_info)
    
    if snapshot_type == SnapType.ECU_V2:
        df = _convert_v2_battery_voltage(df, pid_info)
    
    return df


def _update_v1_engine_state_unit(pid_info: Dict[str, Dict[str, str]]) -> None:
    """Update the SMC_ENGINE_STATE PID unit for V1 snapshots."""
    if "SMC_ENGINE_STATE" in pid_info:
        pid_info["SMC_ENGINE_STATE"]["Unit"] = "[0]Off   [1]Cranking   [2]Running   [3]Stalling"


def _convert_v2_battery_voltage(
    df: pd.DataFrame, 
    pid_info: Dict[str, Dict[str, str]]
) -> pd.DataFrame:
    """Convert BattU_u from millivolts to volts for V2 snapshots."""
    if "BattU_u" in df.columns:
        df["BattU_u"] = pd.to_numeric(df["BattU_u"], errors="coerce")
        df["BattU_u"] = df["BattU_u"] / 1000
        if "BattU_u" in pid_info:
            pid_info["BattU_u"]["Unit"] = "Volts"
    
    return df
