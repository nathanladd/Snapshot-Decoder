"""
Snapshot type detection logic.

Identifies the type of snapshot (ECU_V1, ECU_V2, etc.) based on
column headers and known PID patterns.
"""

import pandas as pd

from domain.snaptypes import SnapType
from domain.constants import PID_KEY


def find_header_row(df: pd.DataFrame, max_scan_rows: int = 10) -> int:
    """
    Find the row index containing column headers (PID names).
    
    Args:
        df: Raw DataFrame loaded from file
        max_scan_rows: Maximum rows to scan for header
        
    Returns:
        Row index of the header row
        
    Raises:
        ValueError: If header row cannot be found
    """
    for i in range(min(len(df), max_scan_rows)):
        row_values = df.iloc[i].astype(str).str.strip().str.lower().tolist()
        
        for pattern in PID_KEY.keys():
            if any(v == pattern for v in row_values):
                return i
    
    raise ValueError("[Find Header Row] Couldn't locate header row containing useful information.")


def detect_snapshot_type(df: pd.DataFrame, header_row_idx: int) -> SnapType:
    """
    Identify the snapshot type based on the header row contents.
    
    Args:
        df: Raw DataFrame loaded from file
        header_row_idx: Index of the header row
        
    Returns:
        SnapType enum value indicating the snapshot type
    """
    row_values = df.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist()

    for pattern, snap_type in PID_KEY.items():
        if any(v == pattern for v in row_values):
            return snap_type
    
    return SnapType.EMPTY
