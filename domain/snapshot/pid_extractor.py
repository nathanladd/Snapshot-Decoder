"""
PID metadata extraction logic.

Extracts PID descriptions and units from snapshot files.
"""

import math
from typing import Dict
import pandas as pd

from domain.constants import UNIT_NORMALIZATION, PID_DESCRIPTION_OVERRIDES


def extract_pid_info(
    df: pd.DataFrame, 
    header_row_idx: int, 
    start_col: int = 2
) -> Dict[str, Dict[str, str]]:
    """
    Extract PID description and unit of measure for each PID column.
    
    For horizontal tables, the description is in the row above the header,
    and the unit is in the row below.
    
    Args:
        df: Raw DataFrame loaded from file
        header_row_idx: Index of the header row containing PID names
        start_col: Column index to start extraction (skip Frame, Time)
        
    Returns:
        Dictionary mapping PID names to their metadata:
        {pid_name: {"Description": str, "Unit": str}}
    """
    pid_info: Dict[str, Dict[str, str]] = {}

    # Row indices for description and unit (guard if out of bounds)
    desc_row = header_row_idx - 1 if _within(df, header_row_idx - 1) else None
    unit_row = header_row_idx + 1 if _within(df, header_row_idx + 1) else None

    for c in range(start_col, len(df.columns)):
        pid = _to_str(df.iat[header_row_idx, c])
        if not pid:
            continue

        description = _to_str(df.iat[desc_row, c]) if desc_row is not None else ""
        unit = _to_str(df.iat[unit_row, c]) if unit_row is not None else ""

        # Collapse multi-line cells
        description = " ".join(part.strip() for part in description.splitlines() if part.strip())
        unit = " ".join(part.strip() for part in unit.splitlines() if part.strip())

        # Override description for known PIDs (case-insensitive). The override
        # always wins over whatever the file provided.
        override = PID_DESCRIPTION_OVERRIDES.get(pid.strip().lower())
        if override is not None:
            description = override

        # Normalize unit if known
        if unit:
            normalized_unit = UNIT_NORMALIZATION.get(unit.strip().lower())
            if normalized_unit:
                unit = normalized_unit

        pid_info[pid] = {"Description": description, "Unit": unit}

    return pid_info


def update_pid_unit(pid_info: Dict[str, Dict[str, str]], pid_name: str, new_unit: str) -> None:
    """
    Update the unit for a specific PID in the pid_info dictionary.
    
    Args:
        pid_info: Dictionary of PID metadata
        pid_name: Name of the PID to update
        new_unit: New unit string to set
    """
    if pid_name in pid_info:
        pid_info[pid_name]["Unit"] = new_unit


def _to_str(cell) -> str:
    """Convert any cell to a cleaned string, treating NaN/None as empty."""
    if cell is None:
        return ""
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    s = str(cell).strip()
    return "" if s.lower() in ("nan", "none") else s


def _within(df: pd.DataFrame, r: int) -> bool:
    """True if r is a valid row index for df."""
    return 0 <= r < len(df)
