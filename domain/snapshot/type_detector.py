"""
Snapshot type detection logic.

Identifies the type of snapshot (ECU_V1, ECU_V2, etc.) based on
column headers and known PID patterns.
"""

import pandas as pd

from domain.snaptypes import SnapType
from domain.constants import SNAPSHOT_TYPE_PIDS
from infrastructure.logging_config import log_info, log_warning, log_error


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
        all_pids.update(p.lower() for p in pids)
    
    log_info(f"Scanning {max_scan_rows} rows for header containing known PIDs...")
    log_info(f"Looking for {len(all_pids)} known identifying PIDs")
    
    for i in range(min(len(df), max_scan_rows)):
        row_values = df.iloc[i].astype(str).str.strip().str.lower().tolist()
        
        # Count how many identifying PIDs are in this row
        found_pids = [v for v in row_values if v in all_pids]
        
        if found_pids:
            log_info(f"Header found at row {i} with {len(found_pids)} identifying PIDs")
            log_info(f"  Sample PIDs: {', '.join(found_pids[:5])}{'...' if len(found_pids) > 5 else ''}")
            return i
    
    raise ValueError("[Find Header Row] Couldn't locate header row containing useful information.")


def detect_snapshot_type(
    df: pd.DataFrame, 
    header_row_idx: int,
    match_threshold: float = 0.5
) -> tuple[SnapType, float]:
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
        Tuple of (SnapType, confidence) where confidence is the match percentage
    """
    row_values = set(df.iloc[header_row_idx].astype(str).str.strip().str.lower().tolist())

    best_match: SnapType = SnapType.EMPTY
    best_percentage: float = 0.0

    log_info("Starting snapshot type detection...")
    log_info(f"Found {len(row_values)} total PIDs in header row")
    
    for snap_type, pids in SNAPSHOT_TYPE_PIDS.items():
        if not pids:
            continue
            
        # Count how many PIDs from this type are found in the row
        matched = sum(1 for pid in pids if pid.lower() in row_values)
        percentage = matched / len(pids)
        
        # Log detailed information for this type
        found_pids = [pid for pid in pids if pid.lower() in row_values]
        missing_pids = [pid for pid in pids if pid.lower() not in row_values]
        
        log_info(f"TYPE {snap_type.name}: {percentage:.1%} confidence ({matched}/{len(pids)} PIDs)")
        if found_pids:
            log_info(f"  Found: {', '.join(found_pids[:5])}{'...' if len(found_pids) > 5 else ''}")
        if missing_pids:
            log_warning(f"  Missing: {', '.join(missing_pids[:5])}{'...' if len(missing_pids) > 5 else ''}")
        
        # Track the highest confidence match regardless of threshold
        if percentage > best_percentage:
            best_percentage = percentage
            best_match = snap_type
    
    if best_percentage >= match_threshold:
        log_info(f"Selected: {best_match.name} ({best_percentage:.1%} confidence)")
    else:
        log_error(f"No snapshot type met the minimum threshold (best: {best_match.name} at {best_percentage:.1%})")
        best_match = SnapType.EMPTY
    
    return best_match, best_percentage


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
            
        matched = sum(1 for pid in pids if pid.lower() in row_values)
        percentages[snap_type] = matched / len(pids)
    
    return percentages
