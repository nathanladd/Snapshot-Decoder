"""
Value conversion logic for specific PIDs.

Handles type-specific conversions (e.g. engine state labels)
and unit standardization (temperature, pressure, voltage).
"""

from typing import Dict
import pandas as pd

from domain.snaptypes import SnapType
from domain.constants import US_UNIT_CONVERSIONS
from infrastructure.logging_config import info, debug


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
    
    return df


def _update_v1_engine_state_unit(pid_info: Dict[str, Dict[str, str]]) -> None:
    """Update the SMC_ENGINE_STATE PID unit for V1 snapshots."""
    if "SMC_ENGINE_STATE" in pid_info:
        pid_info["SMC_ENGINE_STATE"]["Unit"] = "[0]Off   [1]Cranking   [2]Running   [3]Stalling"


def _apply_unit_conversion(
    df: pd.DataFrame,
    pid_info: Dict[str, Dict[str, str]],
    source_units: set[str],
    conversion_label: str,
) -> pd.DataFrame:
    """
    Convert all PID columns whose unit matches one of source_units.

    Uses US_UNIT_CONVERSIONS for the formula:
        result = (value + pre_offset) * factor + post_offset

    Args:
        df: Snapshot DataFrame
        pid_info: PID metadata dictionary (modified in place)
        source_units: Set of normalized unit strings to convert
        conversion_label: Human-readable label for log messages

    Returns:
        DataFrame with converted columns
    """
    if df is None or df.empty:
        return df

    col_lookup = {str(col).casefold(): str(col) for col in df.columns}
    converted = 0

    for pid_name, meta in list(pid_info.items()):
        unit = meta.get("Unit", "")
        if unit not in source_units:
            continue

        conv = US_UNIT_CONVERSIONS.get(unit)
        if conv is None:
            continue

        target_unit, factor, pre_offset, post_offset = conv
        resolved_col = col_lookup.get(pid_name.casefold())
        if not resolved_col or resolved_col not in df.columns:
            continue

        df[resolved_col] = pd.to_numeric(df[resolved_col], errors="coerce")
        df[resolved_col] = (df[resolved_col] + pre_offset) * factor + post_offset
        meta["Unit"] = target_unit
        converted += 1
        info(f"  Converted {resolved_col}: {unit} \u2192 {target_unit}")

    info(f"{conversion_label}: {converted} PID(s) converted")
    return df


def convert_temperature_to_us_units(
    df: pd.DataFrame,
    pid_info: Dict[str, Dict[str, str]],
) -> pd.DataFrame:
    """
    Convert all temperature PIDs to Fahrenheit.

    Handles Celsius and Kelvin source units.
    """
    info("Unit standardization: Temperature \u2192 Fahrenheit")
    return _apply_unit_conversion(
        df, pid_info,
        source_units={"Celsius", "Kelvin"},
        conversion_label="Temperature standardization",
    )


def convert_pressure_to_us_units(
    df: pd.DataFrame,
    pid_info: Dict[str, Dict[str, str]],
) -> pd.DataFrame:
    """
    Convert all pressure PIDs to PSI.

    Handles Kilopascals, Barometric Pressure (bar), and Hectopascals.
    """
    info("Unit standardization: Pressure \u2192 PSI")
    return _apply_unit_conversion(
        df, pid_info,
        source_units={"Kilopascals", "Barometric Pressure", "Hectopascals"},
        conversion_label="Pressure standardization",
    )


def convert_millivolts_to_volts(
    df: pd.DataFrame,
    pid_info: Dict[str, Dict[str, str]],
) -> pd.DataFrame:
    """
    Convert all millivolt PIDs to Volts.
    """
    info("Unit standardization: Millivolts \u2192 Volts")
    return _apply_unit_conversion(
        df, pid_info,
        source_units={"Millivolts"},
        conversion_label="Voltage standardization",
    )
