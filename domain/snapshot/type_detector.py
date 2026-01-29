"""
Snapshot type detection logic.

Identifies the type of snapshot (ECU_V1, ECU_V2, etc.) based on
column headers and known PID patterns.
"""

import pandas as pd

from domain.snaptypes import SnapType
from domain.constants import SNAPSHOT_TYPE_PIDS


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
    # Collect all identifying PIDs from all snapshot types
    all_pids = set()
    for pids in SNAPSHOT_TYPE_PIDS.values():
        all_pids.update(pids)
    
    for i in range(min(len(df), max_scan_rows)):
        row_values = df.iloc[i].astype(str).str.strip().str.lower().tolist()
        
        if any(v in all_pids for v in row_values):
            return i
    
    raise ValueError("[Find Header Row] Couldn't locate header row containing useful information.")


def detect_snapshot_type(
    df: pd.DataFrame, 
    header_row_idx: int,
    match_threshold: float = 0.5
) -> SnapType:
    """
    Identify the snapshot type based on the header row contents.
    
    Calculates what percentage of identifying PIDs for each type are present
    in the header row and returns the type with the highest match percentage
    that meets the threshold.
    
    Args:
        df: Raw DataFrame loaded from file
        header_row_idx: Index of the header row
        match_threshold: Minimum percentage (0.0-1.0) of PIDs that must match.
                        Default 0.5 means at least 50% of listed PIDs must be found.
        
    Returns:
        SnapType enum value indicating the snapshot type
    """
    row_values = set(df.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist())

    best_match: SnapType = SnapType.EMPTY
    best_percentage: float = 0.0

    for snap_type, pids in SNAPSHOT_TYPE_PIDS.items():
        if not pids:
            continue
            
        # Count how many PIDs from this type are found in the row
        matched = sum(1 for pid in pids if pid in row_values)
        percentage = matched / len(pids)
        
        # Update best match if this type has higher percentage and meets threshold
        if percentage >= match_threshold and percentage > best_percentage:
            best_percentage = percentage
            best_match = snap_type
    
    return best_match


def get_match_percentages(df: pd.DataFrame, header_row_idx: int) -> dict[SnapType, float]:
    """
    Get the match percentage for each snapshot type.
    
    Useful for debugging or displaying match confidence.
    
    Args:
        df: Raw DataFrame loaded from file
        header_row_idx: Index of the header row
        
    Returns:
        Dictionary mapping SnapType to match percentage (0.0-1.0)
    """
    row_values = set(df.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist())
    
    percentages: dict[SnapType, float] = {}
    
    for snap_type, pids in SNAPSHOT_TYPE_PIDS.items():
        if not pids:
            percentages[snap_type] = 0.0
            continue
            
        matched = sum(1 for pid in pids if pid in row_values)
        percentages[snap_type] = matched / len(pids)
    
    return percentages
