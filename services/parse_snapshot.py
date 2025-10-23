from domain.snaptypes import SnapType
import pandas as pd
import math

# Define a mapping of header PIDs to SnapType enumerations
header_patterns = {
    "p_l_battery_raw": SnapType.ECU_V1,
    "battu_u": SnapType.ECU_V2,
    # Add more patterns as needed
}

def id_snapshot(snapshot: pd.DataFrame) -> SnapType:
        
    header_row_idx = None
    # Scan the first 10 rows
    for i in range(min(len(snapshot), 10)):
        # Clean and normalize each cell to lowercase strings
        row_values = snapshot.iloc[i].astype(str).str.strip().str.lower().tolist()

        # Check if any known header keyword appears in this row
        for pattern, snap_type in header_patterns.items():
            if any(v == pattern for v in row_values):
                header_row_idx = i
                return snap_type  # stop once a match is found
        else:
            # The 'else' on a for-loop runs only if the loop didn't break
            continue
        break  # Break outer loop after a successful match

    if header_row_idx is None:
        raise ValueError("Couldn't locate header row containing useful information.")

# ------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------- Find the header row --------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------       

def find_header_row(snapshot: pd.DataFrame) -> int:
    header_row_idx = None
    # Scan the first 10 rows
    for i in range(min(len(snapshot), 10)):
        # Clean and normalize each cell to lowercase strings
        row_values = snapshot.iloc[i].astype(str).str.strip().str.lower().tolist()

        # Check if any known header keyword appears in this row
        for pattern, snap_type in header_patterns.items():
            if any(v == pattern for v in row_values):
                return i  # stop once a match is found
        else:
            # The 'else' on a for-loop runs only if the loop didn't break
            continue
        break  # Break outer loop after a successful match

    if header_row_idx is None:
        raise ValueError("Couldn't locate header row containing useful information.")


 # ------------------------------------------------------------------------------------------------------------------------
 # ---------------------------------------------- Extract PID Descriptions ------------------------------------------------
 # ------------------------------------------------------------------------------------------------------------------------   

#Helper function for extract_pid_metadata
def _to_str(cell) -> str:
    """Convert any cell to a cleaned string, treating NaN/None as empty."""
    if cell is None:
        return ""
    if isinstance(cell, float) and math.isnan(cell):
        return ""
    s = str(cell).strip()
    return "" if s.lower() in ("nan", "none") else s

#Helper function for extract_pid_metadata
def _within(df: pd.DataFrame, r: int) -> bool:
    """True if r is a valid row index for df."""
    return 0 <= r < len(df)

#Extract the PID description and PID unit of measure for each PID
def extract_pid_metadata(df: pd.DataFrame, header_row_idx: int, start_col: int = 2) -> dict[str, dict[str, str]]:
    """
    Starting at start_col (default: 3rd col), read:
    - PID name from header_row_idx
    - Description from row above (header_row_idx - 1)
    - Unit from row below (header_row_idx + 1)
    Returns: { PID_name: {"Description": ..., "Unit": ...}, ... }
    """
    pid_info: dict[str, dict[str, str]] = {}

    # Row indices for description and unit (guard if out of bounds)
    desc_row = header_row_idx - 1 if _within(df, header_row_idx - 1) else None
    unit_row = header_row_idx + 1 if _within(df, header_row_idx + 1) else None

    for c in range(start_col, len(df.columns)):
        pid = _to_str(df.iat[header_row_idx, c])
        if not pid:
            continue

        description = _to_str(df.iat[desc_row, c]) if desc_row is not None else ""
        unit = _to_str(df.iat[unit_row, c]) if unit_row is not None else ""

        # Optional: collapse multi-line cells
        description = " ".join(part.strip() for part in description.splitlines() if part.strip())
        unit = " ".join(part.strip() for part in unit.splitlines() if part.strip())

        pid_info[pid] = {"Description": description, "Unit": unit}

    return pid_info
    